# COORD-015 — supervisor 角色：接力调度、事实核查、有界代拍与池重分配

Status: ACCEPTED（D6，2026-09-25；研究轨道；接受后修订 1 已确认（BC-12）；修订 2/3 由用户指示修订 4 撤销、运行地恢复 D6 原文（Opus），见「回应索引」修订 4 行；§9.2 已落地、CLI 下载/A6 完成；2026-09-26 `R2@落地` 通过轮最终处置 `DONE`（见「Acceptance rulings（复判）」）；信封首签与首次启用仍归用户、不属 `DONE` 前置；设计退修累计 2）
Author/role: 构思角色 / design ideation（Claude Code `/fable`）
Created: 2026-09-25
Last updated: 2026-09-26（`R2@落地` 最终处置 `DONE`；BC-14/BC-15 `CLARIFY`）；2026-09-25（接受后修订 4，用户指示撤销修订 2/3、恢复 supervisor=Opus；接受后修订 3，用户指示不指定任何模型以及 CLI；接受后修订 2，用户指示 supervisor 运行地/模型不绑定；接受后修订 1，用户指示 D1 收敛判据；D6 `c258c01`、接受 D6 `abb2fda`；D5 `a4b01c1`、接受 D5 裁定 `f5e8d5d`；D4 `71d817a`、接受 D4 裁定 `911678a`；D3 `da33e70`、接受 D3 裁定 `ed0a4f1`；D2 `960da97`、接受 D2 裁定 `fec3088`、用户选 A `f2bb4de`；D1 重写版 `2a154cd`、首版 `4c5287c`）
Track: 研究轨道（接受 D1 裁定）
Inputs: `docs/evidence/authorization-ledger-stats-2026-09-25.{md,csv}`；账本 2026-09-25 十三条 COORD-015 相关条目；本会话只读核实的
运行地与切换事实（§1、附录 A）；接受 D1–D5 裁定 AR1-1…8、AR2-1…4、AD3-1…4、AD4-1/2、AD5-1 与 D6 ACCEPTED（文末「Codex review decision」）；用户「改成第二种」指示（账本同日「用户指示 D1 收敛判据」）；用户「改成本机跑supervisor，不要指定模型名称，因为我可能会换模型。上传已有的工作状态，我会重新开一个kimi会话来构思」指示（账本同日「用户指示修订 2」及构思会话补充代录）；用户「accept已经接受，最后稍微修改一下，不指定任何模型以及cli」指示（账本同日「用户指示修订 3」）；用户「算了恢复到最初的那一档吧，就是用opus来做supervisor。」与「不用重写，把那一版本找回来就行了」指示（账本同日「用户指示修订 4」）

> 本文是提案，不是授权，也不是角色细则。落地要改 `AGENTS.md`、`CLAUDE.md`、两份 workflow、`docs/roles/`、`.claude/commands/`、`tools/`（含 `githooks/pre-commit`）、`tests/`，
> 并安装一个 CLI，属工作流基础设施与下载，只能由用户直接授权的协调批次执行（workflow §7 规则 7）。本会话零测试、零代码、零下载、零消耗；示例日期、额度、次数均为**示例**，
> 不构成默认授权。设计退修累计 2（D1、D2），本 D6 为用户对 D5 残留选 (a) 后的修正，接受后修订 1 为用户对 D1 计数的指示修订，接受后修订 2/3 为运行地指示修订（已被修订 4 撤销），接受后修订 4 为用户对撤销修订 2/3、恢复 D6 原文的指示修订，均不重置计数。**本提案正文预算 ≤ 522 行，含 BC 表、不含从「Codex review decision」起的接受裁定原文**（修订 3 审核时裁定为 551；修订 4 恢复 D6 文句后回降，相对修订 1 确认版 +2 行 = 回应索引修订 4 行与 BC-13 撤销注记；不修改 workflow 的 600 行信号或状态板上限）。

## 回应索引

| 轮 | 要求 | 落点 |
|---|---|---|
| AR1-1…8、AR2-1…4（D1/D2） | 见 D2/D3 落点，均保留（接受 D2/D3 裁定逐项表） | §3–§13、附录 A（已闭合部分不改） |
| AD3-1…4（D3） | 见 D4 落点，均保留（接受 D4 裁定逐项表） | §3.2–3.6、§4、§5.6、§8、§10、附录 A |
| AD4-1 | 去重键扩到未终结 `requested`；`launch_failed` 只认当场的未创建证明；无 id/超时/裸 `requested` 统一未确认，基线 `requested_at`/`base_head`，不凭干净树释放 | §3.2–3.5、§10 A5 ⑥(丁)(戊) |
| AD4-2 | 解析器在 S 处先做初态检查（X 可 = S）、新旧信封各自边界；预提交视图（待提交条目首父 = HEAD、暂存状态板作虚拟提交、与提交后谓词等价） | §5.6、§10 A2 |
| AD5-1 | 到期事实源唯一：只有状态板事件产生 X，原 (ii) 提交主题条件撤出到期事实、降为派发守卫的停下提示；预提交视图对 (i)(ii) 完全可判且与提交后等价，同一提交到期即拒绝；不新增 commit-msg 钩子 | §5.6、§3.6 (i)、§9.2、§10 A2/A5 ⑤ |
| 接受后修订 1（用户 2026-09-25「改成第二种」，账本同日） | D1 由「每提案 1 次」改为残留数严格递减：接受裁定节 `open_items:` 机读行定义 r(n)、计数键 `<work_id>:D1:D<n>`、D1 条目机检字段；§8 样本按新判据以裁定具名条目数代算（D1 仍 3：#28 出、#27 进）；A2 加四例、A5 ① 加代拍与不递减停下；已由接受角色确认，见 BC-12 | §5.1、§5.4、§5.7、§8、§9.2/9.3、§10 A2/A5 ①、§13 |
| 接受后修订 2（用户 2026-09-25「改成本机跑supervisor，不要指定模型名称，因为我可能会换模型。上传已有的工作状态，我会重新开一个kimi会话来构思」，账本同日「用户指示修订 2」及补充代录） | supervisor 运行地由「Opus / Claude Code `/supervisor`」改为本机（用户当前工作机）Kimi Code CLI 会话、不绑定模型名称（模型由用户当轮选择、可更换，规则文件不写死任何模型名；「本机」非特定硬件绑定）；A9 模型升降改交用户；U4 模型部分改判、其余部分维持缺省；已落地文件的对应句按 §7 末清单在接受确认后由协调批次逐字同步；D6 接受结论与设计退修累计 2 不变，不新增 D 轮；已确认，见「接受后修订 2 审核」与 BC-13 | §2.1、§7、§0.2、§0.3、§8、§13 |
| 接受后修订 3（用户 2026-09-25「accept已经接受，最后稍微修改一下，不指定任何模型以及cli」，账本同日「用户指示修订 3」） | 修订 2 的「本机 Kimi Code CLI 会话」去 CLI 绑定：运行地为本机（用户当前工作机）CLI 会话，不指定任何 CLI 与模型名称，均由用户当轮选择、可更换，规则文件不写死；§7 末落地对应句目标文本同步去 CLI 名（对应句尚未同步，协调批次直接按修订 3 文本一次落地）；BC-13 随本次确认同步；D6 结论与退修累计 2 不变，不新增 D 轮；已确认，见「接受后修订 3 审核」 | §2.1、§7、§0.2、§0.3、§8、§13 |
| 接受后修订 4（用户 2026-09-25「算了恢复到最初的那一档吧，就是用opus来做supervisor。」「不用重写，把那一版本找回来就行了」，账本同日「用户指示修订 4」） | 撤销修订 2/3：supervisor 运行地恢复 D6 原文（Opus 池、Claude Code `/supervisor`、U4=A、A9 升 Fable 原句恢复）；§7 末「接受后修订 2/3 落地对应句」清单废除（对应句已由协调批次恢复至 c2cea6b 之前版本）；BC-13 加撤销注记；修订 1 保留；D6 结论与退修累计 2 不变，不新增 D 轮 | §2.1、§7、§0.2、§0.3、§8、§13 |
| C1@落地 退回项 BC-1（接受 2026-09-25，文本侧） | §3.2 尾注形态由 `Role-Check: check_role_writes --role <r> pass` 统一为 `Role-Check: <role> pass`，与 §3.8、五个角色细则/入口、`docs/roles/supervisor.md` 及仓库外 `codex.md` 一致；工具侧 `tools/make_supervisor_drill.py` `commit_trailers()` 与 `tests/test_supervisor_drill.py` 的同步归协调批次；不改 BC | §3.2 |
| 接受后修订 5（用户 2026-09-28「工程轨道构思改 Opus，复核不变」，账本同日「全局 — 用户指示：工程轨道构思改用 Opus 池，复核不变」） | 工程轨道（`Workflow: engineering-v1`）构思改由 Opus 子代理运行，研究轨道构思、复核仍 Fable；用户直接指示、不经构思/接受轮，D6 结论与退修累计不变；落地文件对应句由同一协调批次同步 | §0.2、§2.4、§7 |
| 接受后修订 6（用户 2026-09-28「我觉得可以调到25-30万，重开时间我同意」「好的，起草」，账本同日「全局 — 用户指示：supervisor 会话卫生阈值改 25/30 万 token、按节读取细则」） | §3.10 会话卫生：删「每处理 20 次交接」；上下文超 25 万 token 后在当前派发核销与核查完成时收工重开、不在派发中途重开，超 30 万 token 即写检查点摘要收工，未完成派发由下一会话按 §3.5 重启后对账接上；细则按节读取（开工只读职责/白名单/边界/重启后对账，其余节到对应步骤再读，代拍各节只在信封或子额度块在效时读）；用户直接指示、不经构思/接受轮，D6 结论与退修累计不变；落地文件对应句由同一协调批次同步 | §3.10 |

## 0. 目标、摘要与用户定局

### 0.1 目标（用户原话，2026-09-25）

"我想要的就是supervisor agent能帮我完成重复性的切换agent工作以及代替我做一些简单的事实核查这样我能隔两个小时左右检查一次"

### 0.2 摘要

| 发现 | 提议 | 目标（§8；落地后实测） |
|---|---|---|
| 用户是会话之间的人肉中继：09-08…09-24（17 天）交接提交 140 次、用户开会话 76 次（§1 F1） | **S0 接力调度**：常驻循环按状态板拉起下一角色，全局同一时刻只跑 1 个写仓库角色；派发日志登记/核销/对账；只在需要用户处停 | 自动接力成功的链段内用户开会话 0 次 |
| 用户每次检查时做的核对无角色承担 | **S1 事实核查**：角色提交前自跑自检并把凭据写进提交尾注；supervisor 提交后只核验凭据与磁盘事实（F1–F10，非权威） | 用户只看差异 |
| 点头型决定：退修二选一、放行次序、杂事、既有维度内的小额追加 | **S2/S3 有界代拍**：决策信封（默认类 D1/D4/D6）+ 执行信封子额度块；两类引用分开机检；可撤销、可否决 | 逐条证明 5/137，附子额度块 7/137（5%）；启用 D2a/D2b 9/137；上界 13，不计收益（§8） |
| 流程规则修改 30 条几乎全由监督会话发起 | **T 节流**：5 天窗口 ≤ 1 个 COORD 批次、打包、无数据不提、emergency 例外 | 30 → 7–14 |
| 实现（Cursor）与接受（Codex 桌面应用）无法无人值守拉起 | **P 池重分配**：构思 Fable（工程轨道 Opus，修订 5）、实现 Opus、接受 Codex CLI、复核 Fable、辅助 Sonnet、supervisor Opus | 五角色可无人值守 |

### 0.3 用户定局（逐字，账本同日条目）

1. 代拍边界："我唯一会修改截图里 option 1 的地方，是 “≤20% 余量”不要写死成 supervisor 自己天然拥有的权力。最好是你每次签 envelope 时顺便写：supervisor_subdelegation: enabled: true / max_increment: $X / max_total: $Y / expires_at: K4 这样 supervisor 不是因为“规则默认允许”就能花钱，而是你在这次信封里提前授权了一个子额度。"（换行已压平）
2. 节流："默认 5天窗口最多 1 个 COORD 批次；同一窗口内发现的问题必须打包。如果没有数据支撑就不提。紧急 correctness / 权限 / deadlock 问题可以立即提 emergency COORD。"
3. 路由："只接代拍类，其余直达（推荐）"。
4. 池分布："改一下分布，构思用fable，实现用opus，接受用codex，审查用fable，归档用sonnet。另外supervisor你觉得应该用什么模型？"（构思建议 Opus，用户未反对）
5. Codex 拉起："装 Codex CLI，全自动（推荐）"。
6–8. 路径："怎么交接给接受角色？状态版有更新吗"（按字面取接受轮）；第二次退修处置："A"；D3 残留处置："(a) 修正 AD3-1…4 出 D4（推荐）"
（AskUserQuestion 选项标签）；D4 残留处置："选A"；D5 残留处置："(a) 修正 AD5-1 出 D6（推荐）"（同前）。四次处置都只保留范围与已有效修正，不等于 ACCEPTED，不授权落地。9. D1 计数（D6 接受后修订 1）："改成第二种"（两种改法原文见账本同日「用户指示 D1 收敛判据」条目）。10. supervisor 运行地与模型（D6 接受后修订 2）："改成本机跑supervisor，不要指定模型名称，因为我可能会换模型。上传已有的工作状态，我会重新开一个kimi会话来构思"（账本同日「用户指示修订 2」；改动范围细化见构思会话补充代录）。11. CLI 亦不指定（D6 接受后修订 3）："accept已经接受，最后稍微修改一下，不指定任何模型以及cli"（账本同日「用户指示修订 3」）。12. 恢复 Opus（接受后修订 4）："算了恢复到最初的那一档吧，就是用opus来做supervisor。"、"不用重写，把那一版本找回来就行了"（账本同日「用户指示修订 4」；撤销 10/11 两项指示，运行地恢复 D6 原文）。

## 1. 问题与证据（要素 1）

- **F1 切换负担（可复算；脚本与本会话复算输出见附录 A，落地时随 A9 入库）**。窗口 2026-09-08…09-24（17 天）。
  口径 A「交接提交」：`docs/current-status.md` 共 147 次提交，其中 diff 触及「## Active handoffs」节者 140 次。口径 B「用户开会话」：
  Claude 顶层会话（首条时间戳落在窗口内）65 个 + Codex 会话 11 个 = 76 次，约 4.5 次/天（逐日分布见附录 A 输出）；Cursor 会话无本地
  可数记录未计；Claude 会话含用户直接指挥的会话未剔除。
- **F2 负担结构**（账本 137 条）：需要用户判断 28%、流程自身产生 34%、放行与额度 27%、杂事 10%；点头型 69%，推荐项采纳 91%。
- **F3 按 §5.1 允许动作/禁项/次数键逐条重判的可代拍样本**（AR2-4；逐条见 §8）：D1 3、D4 0（#85/#88 只含可代拍的次序部分）、D5 0、D6 2（#101 自发指令不计）、
  SUB 2（需子额度块）；D2a/D2b 各 1 仅在用户启用时计入；D3 0（#13/#14 混合）。
- **F4 改规则负担**：META 30 条在 14 个日期、17 个批次组，五组两两相隔 ≤ 5 天。**F5 角色缺位**：监督会话代录 8 条 COORD 授权，无细则、
  无白名单，写入借用 `--role acceptance`。
- **F6 运行地事实**（只读核实）：登录 shell 与常见安装目录均无 `claude`、`codex`、`cursor-agent`、`agent`；`~/.codex/sessions/2026` 54 个会话与 `~/.codex/computer-use/`
  桌面应用，即接受角色一直经 Codex 桌面应用运行；`Cursor.app` 只带 `cursor` 命令；本 Claude 桌面版无新开会话工具，有子代理（可选档位、完成回调、可停止）、自定节奏唤醒、后台监视与推送通知。
- **F7 红线**：授权与信封只能来自用户原话并逐字入账（`AGENTS.md`）；代拍必须说明兼容性（§5.8）。

## 2. 角色定义（要素 2、7）

### 2.1 名称、运行地、模型、作者边界

- 角色名 `supervisor`；Claude Code 命令 `/supervisor`；`check_role_writes.py` 角色键 `supervisor`。
- 模型 **Opus**（U4）：机械调度与清单核查为主，代拍有默认值兜底；长期驻留，Opus 输出单价为 Fable 的 0.4 倍；核查不是复核，
  不受「复核档位不低于实现者」约束。A9 报告出现代拍被否决或核查漏检即升 Fable。
- 作者边界：supervisor **是** COORD 提案的作者（S5）；对自己起草的 COORD 提案，D 类代拍一律不适用、回用户；委托子代理起草
  不改变作者归属（派发提示与委托记录在调度日志）。自身利害事项（本角色细则、白名单、模型、节流、两种信封、调度日志格式）
  的任何决定回用户。它不是任何 `P1-*` 提案的作者、任何候选的实现者或复核者，且不在自己的上下文里做任何角色的工作。

### 2.2 职责闭集

| 编号 | 职责 | 产出 |
|---|---|---|
| S0 | 接力调度（§3）：登记、拉起、等待、核销、对账、停下 | `docs/evidence/supervisor-dispatch.jsonl` |
| S1 | 事实核查（§4）：提交后核验凭据与磁盘事实，非权威 | 不一致时状态板 Log 一条 + 退回交接 |
| S2 | 代拍：决策信封在效类内替用户决定，逐条入账（§5） | 账本代拍条目 |
| S3 | 子额度审批：执行信封子额度块内批准追加（§5.3） | 账本代拍条目 |
| S4 | 检查点摘要：待决（各带推荐项与「为何只能用户定」）、已代拍可否决、核查差异、链路进度 | 对话消息 |
| S5 | 起草 COORD 提案（§6 节流）；按用户逐字授权执行协调批次 | `docs/proposals/COORD-*.md`；infra（仅协调批次） |
| S6/S7 | 代录：用户在 supervisor 会话给出的授权与反馈当场入账；流程健康度统计 | 账本、`docs/unity-test-log.md`；`docs/evidence/COORD-*` |

不做：不写运行时代码、配置、测试、工具（§2.3）；不写 `docs/reviews/`、`docs/design-reviews/`；不签发 `ACCEPTED`/verdict/`DONE`/
`CLOSED_*`；不写 BC/AC/核对表；不首签任何信封；不做 §5.2 决定；不运行 Unity、不做人眼保真；运行中的角色收工前不写状态板与账本。

### 2.3 写入白名单与协调批次例外

allow：`docs/proposals/COORD-*.md`、`docs/current-status.md`、`docs/authorizations.md`、`docs/unity-test-log.md`、`docs/evidence/COORD-*`、
`docs/evidence/supervisor-dispatch.jsonl`、`docs/project-background.md`、`docs/workflow-changelog.md`；`docs/parked-status.md` 仅在
U7 选 A 时加入（仅机械搬运）。deny（显式）：`docs/reviews/*`、`docs/design-reviews/*`、`docs/implementation-status.md`、
`docs/phase1-single-drone-design.md`、`docs/status-history.md`；`P1-*` 提案与代码不在 allow 内即拒绝；`INFRA_PATTERNS` 照旧优先。
**常规写权不含 `tools/`、`tests/`**；§12 的测试与工具改动全部发生在用户逐字授权的协调批次内（现行规则：协调批次不跑角色检查、
凭据为提交信息引用的账本条目）。

### 2.4 与各角色和用户的边界

| 对方 | supervisor 做 | 不做 | 对方的变化 |
|---|---|---|---|
| 构思（子代理：研究轨道 Fable、工程轨道 Opus） | 拉起、核查、接 D1 | 不写 `P1-*`；不裁定自己的 COORD | 需要用户的问题回报 supervisor |
| 接受（Codex CLI） | 拉起 `codex exec`、核查、接 D1/D4/D5 | 不写 BC/AC、不裁定 `ACCEPTED`、不签独立复核 | 「上交用户」句按 §9.3 具名映射 |
| 实现（Opus 子代理） | 拉起（信封在效）、核查、接 SUB | 不改实现、不解释 BC/AC | 主运行地 Cursor → Claude `/implement`；追加申请写报告 `needs_user` |
| 复核（Fable 子代理） | 按 §3.7 拉起、核查、接 D2b（若启用） | 不进 worktree、不改 verdict | 轮 3 终局句按 U1 |
| 辅助（Sonnet 子代理） | 拉起压缩/预筛/检索；接 D3（若启用） | 不接管压缩标准 | 「交用户同意」句按 U2 |
| 用户 | 检查点摘要；停下时推送；信封内代拍并接受否决 | 不做 DIR/LIFE/ENV/FACT；不放宽红线；不跑 Unity | 一次签决策信封；执行信封可附子额度块；Unity/人眼/设备节点仍由用户执行 |

### 2.5 直达用户的事项不加审批

对 §5.2 不可代拍事项，supervisor 只做三件事：原样展示（含负责角色的推荐项与理由）、当场逐字代录、交回负责角色；不加审批、不改推荐项、不延迟、不因「打包」扣留任一事项。

## 3. 接力调度协议（要素 3；AR1-1、AR2-1）

假设：Active handoffs 已完整定义交接，各角色入口已是完整开工指令；一个只按表拉起、只核验磁盘事实的调度者可以替代用户的中继
动作而不改变门语义。

### 3.1 唯一执行

首版**全局同一时刻最多运行 1 个写仓库的角色**；supervisor 在该角色收工前对仓库只读。协调批次、`--infra-fix` 提交与 DR-* 审查不在循环内。

### 3.2 派发事实源、身份与字段

`docs/evidence/supervisor-dispatch.jsonl` 是派发状态的唯一事实源，追加式，每行一个事件。事件闭集与字段：
`requested`（dispatch_id、work_id、role、round、runtime、model、base_head、requested_at、prompt_sha256、request_ids[]）、`started`（runner_id：
子代理 id 或 `codex exec` 的 pid，启动调用无返回时 `unknown`；runner_start：pid 的 `ps -o lstart=` 或子代理 id 的返回时刻；started_at）、
`end_confirmed`（source ∈ {callback, stop_call, pid_gone, user_quote}，`user_quote` 附原话）、`finished`（report 全文、commits[]、candidate、reachable_remote）、
`reconciled`（reason ∈ {report_lost, runner_gone}、commits[]、candidate、credentials）、`aborted`（reason ∈ {launch_failed, runner_gone, user_pause}；`launch_failed` 必带 `proof`）、`duplicate_callback`。
`dispatch_id = <work_id>-<round>-<UTC 时间戳>-<4 hex>`；角色收工提交信息末尾必须带尾注 `Dispatch-Id: <id>` 与
`Role-Check: <role> pass`（提交前自跑 `check_role_writes --role <role>` 与 `check_docs` 两项自检的持久凭据，§4 F1；与 §3.8、各角色入口及细则同一形态，C1@落地 BC-1 同步）。`candidate` = 该派发全部带同一 `Dispatch-Id` 的提交
按 `git log --reverse` 顺序的最后一个，由 supervisor 运行时解析写入，不手写。

### 3.3 启动前登记与全局去重

派发前：(i) 读日志，若**任一** work_id 存在未终结的 `requested`（有无 `started` 都算；终态 = `finished/reconciled/aborted`）→ 不派发，先按 §3.5
对账，不明则停（与 §3.1 一致）；(ii) 写 `requested`（含 `requested_at`、`base_head`）；(iii) 启动；(iv) 启动调用返回后立即写 `started`（runner_id、
runner_start）。启动结果三分：**已证明未创建运行者**（子代理工具返回显式错误，或 `codex exec` 在 fork 前失败、无 pid）→ `aborted(launch_failed,
proof=<错误原文>)`，零消耗角色允许重派 1 次（新 dispatch_id、沿用 `request_ids`），消耗性停下；**返回 id** → `started`；**其余**（超时、无 id 且无显式
错误、返回值不可解析）→ `started(runner_id: unknown)`，走 §3.4 未确认分支，禁止记 `launch_failed`。未创建证明只能在启动调用当场取得，事后不可补。
完成回调按 dispatch_id 只核销一次，重复回调记 `duplicate_callback` 并忽略。

### 3.4 完成核销、报告丢失、运行者消失

终态事件（`finished`/`reconciled`/`aborted(runner_gone)`）只能写在同一 dispatch_id 的 `end_confirmed` 之后（`launch_failed`、`user_pause` 例外）。
**结束凭据闭集**（`end_confirmed.source`）：`callback`（该子代理的完成/失败回调；runner_id 未知时以回调报告内的 dispatch_id 匹配）；`stop_call`（对
已知子代理 id 的停止调用返回成功）；`pid_gone`（`codex exec`：`kill -0 <pid>` 失败，或 pid 存活但 `ps -o lstart=` ≠ `runner_start`，即 pid 已复用）；
`user_quote`（用户逐字确认该运行者已结束，原话写入事件）。runner_id 未知或只有 `requested` 时凭据只剩 `callback` 与 `user_quote`；「本会话重启」
「暂时无提交且工作树干净」「宽限已过」都不是凭据。**基线时刻** = `started_at`，缺失时 = `requested_at`；基线提交 = `base_head`。

1. 收到报告（回调即 `end_confirmed(callback)`）→ §4 核查（磁盘项 + 报告项）→ 写 `finished`（含 `candidate`）。
2. 报告缺失但存在带该 `Dispatch-Id` 的提交 → 先取得 `end_confirmed`；未取得则等待：每 5 分钟看 `git status --porcelain`、
   `git log --grep` 与凭据来源，宽限 30 分钟（零消耗与消耗性相同），到期仍未确认 → §3.6 (h) 停下，派发保持未闭、单写者不释放。
   确认后按 §4「无报告时的来源」核查（报告项记 N/A）→ 写 `reconciled(report_lost)`，`candidate` 按 §3.2 规则解析；磁盘项缺任一 → 停下。
3. 无提交 → 同样先取得 `end_confirmed`（等待规则同上）。确认后：工作树干净且角色零消耗 → `aborted(runner_gone)`，允许重派 1 次
   （新 dispatch_id，`request_ids` 沿用）；工作树不干净、该 work_id 的 `docs/evidence/*-ledger.json` 出现晚于基线时刻的事件、
   或角色为消耗性 → 不重派，停下等用户。

候选解析顺序（唯一）：(1) 该派发 `finished.candidate`；(2) 否则 `reconciled.candidate`；(3) 都没有 → **无可证明候选，停下**，禁止退取
更早派发的候选。

### 3.5 重启后对账

supervisor 启动时先对账：逐条处理未终结派发（含只有 `requested` 的），先按 §3.4 取得 `end_confirmed`——`codex exec` 用 `pid_gone`；上一会话的子代理
收不到回调，只能尝试 `stop_call`，失败即状态未知。只有 `requested` 的派发视同 `runner_id: unknown`：以 `requested_at`/`base_head` 为基线，`git fetch`
后核对 `git log --grep='Dispatch-Id: <id>'`（含远端）与消耗账本晚于基线时刻的事件——有提交 → 转 §3.4-2（仍须 `end_confirmed`）；无提交 → 不得记
`runner_gone`，停下并向用户索取 `user_quote`。其余核对同前：`git status --porcelain`、各消耗账本 `events[].at` 与基线时刻先后、远端是否有本地缺失的
提交。任何不明先停并写检查点摘要；不盲目重跑。

### 3.6 停下条件、重试、用户暂停

停下 = 不再拉起、写检查点摘要、等用户：(a) 交接 Owner 为用户且不在启用的代拍类；(b) 下一步需要 Unity Play、人眼保真或用户
设备操作；(c) 越出信封（含子额度耗尽）；(d) 同一角色核查连续 2 次不一致；(e) 异常退出——零消耗角色允许自动重试 1 次（按 §3.4-3
先确认结束），第 2 次停下；消耗性角色不重试；(f) 机检在角色提交后仍失败；(g) 红线；(h) 状态不明、结束未确认或无可证明候选；(i) 派发守卫的主题提示命中而 X 不存在（§5.6）。推送通知只在
(b)–(i) 与「有待决问题」时发一次。用户暂停：该项不再派发；运行中的零消耗角色停止并记 `aborted(user_pause)`；运行中的消耗性
角色让其收工，用户明示立即中止时才停止，随后按 §3.5 对账。

### 3.7 复核派发：候选绑定与独立性

复核派发不使用子代理的 worktree 隔离；复核子代理按 `review.md` 自建 `.claude/worktrees/review-<work-id>` 读码，复核文件写主树
并自行提交推送。派发提示 = 固定模板：`review.md` 正文 + work ID + 候选 SHA（按 §3.4 解析顺序取上一实现派发的 `candidate`）+
交接行原文；**不含**实现报告的 `claims`。提示 sha256 入日志。独立性依据 = 新鲜上下文 + 提示内容可审计。

### 3.8 角色接力报告与持久凭据

报告在带内返回（子代理结果 / `codex exec` 标准输出末段），supervisor 把全文写入 `finished.report`，自己只保留 ≤ 600 B 摘要。必填：`work_id`、
`this_round`（本次执行的轮次，如 `D1`）、`commits[]`（多于 3 个时写首、末与计数）、`handoff`（角色写入交接行的 `owner` 与 `status` token）、`next_owner`、
`needs_user`（每条一行，带推荐项与理由）、`consumed`（仅非零维度）、`checks`（两项自检通过行）。`claims` 只放指针（`路径#小节`）。总长 > 2 KB 时 `claims` 与
`needs_user` 详情改指向该角色本轮已提交的证据/交接文件，必填字段不可省。**持久凭据**与报告并行存在于提交尾注（`Dispatch-Id`、`Role-Check`）与 git（提交存在、
远端可达），因此报告丢失时 §4 的磁盘项仍可核验，报告项记 N/A。子代理不得代写用户原话的账本条目。报告格式写进各角色入口末尾「被 supervisor 拉起时」一段。

### 3.9 并发与消耗纪律；3.10 会话卫生

轨道上限、Gate-echo、共享槽位互斥不变；消耗由被拉起的实现子代理按现行规则使用与记账。supervisor 每次唤醒只读结构节与本项
Gate 行；唤醒间隔 ≥ 20 分钟；上下文超 25 万 token 后在当前派发核销与核查完成时收工重开、不在派发中途重开，超 30 万 token 即写检查点摘要收工（修订 6，原「每处理 20 次交接或上下文超 15 万 token 时收工重开」）；细则按节读取（修订 6）。

## 4. 事实核查（S1；AR1-2、AR2-3）

原则：**提交前检查由角色自跑（现行）并把凭据写进提交尾注；supervisor 提交后只核验凭据与磁盘事实，不对已提交批次做写入归因**
（保留 workflow §7 规则 7）。提交后按路径白名单审计与 `--base <commit>^` 诊断复跑整体列为用户待选变更 U9，未选即不存在。
批次 = 一次派发从 `started` 到带同一 `Dispatch-Id` 的最后一次提交；协调批次与 `--infra-fix` 不适用本节。

| 编号 | 核查 | 方法 |
|---|---|---|
| F1 | 凭据：每个派发提交带 `Role-Check: … pass` 尾注（角色提交前自跑），且提交存在（pre-commit 已跑 `check_docs`）；报告 `checks` 为辅 | 缺尾注 = 失败 |
| F2 | 远端可达：`git fetch -q origin main && git merge-base --is-ancestor <candidate> refs/remotes/origin/main` | 这是唯一凭据；报告收据不作依据 |
| F3a | 磁盘项：本 work ID 交接行存在、Status 非空，且 Status 或 Progress 含 `requested.round` 字面；报告项：Owner/Status 与报告 `handoff` 逐字一致 | 比对下一交接身份，不与本次轮次比 |
| F3b | Gate board 两列写权（其余列不是本项对象）：`Lifecycle` 只在接受派发的批次变化；`Overall` 的接受决定 token（`ACCEPTED`/`REVISION_REQUESTED*`/`REJECTED`/`REWORK_REQUIRED`/`REVIEW_PASSED`/`UNITY_*`/`BLOCKED*`/`DEFERRED_*`/`DONE`/`CLOSED_*`）只在接受派发的批次变化；构思派发只可新增本 work ID 行（`PROPOSED` + `ACTIVE`）或把本行 `Overall` 由 `REVISION_REQUESTED*` 改为 `PROPOSED_D<n>`（workflow §4.1）；实现派发只可把本行改为 `IMPLEMENTING`/`IMPLEMENTED`（workflow §4.3；写在 Overall 或 Implementation 列均可）；复核/辅助派发两列不得变 | 两列 diff 按派发角色落在允许集内，否则失败；非本 work ID 行的两列任何变化即失败 |
| F4 | 磁盘项：交接行与本批新 Log 条目内的路径/小节存在；报告项：`claims` 指针 | `test -e` + 标题 grep |
| F5 | 磁盘项：交接行与新 Log 条目的数字 = 被指文件具名行；报告项：报告数字 | 逐一比对 |
| F6 | 磁盘项：`git diff <base_head>..<candidate> -- docs/authorizations.md` 无新增 `## ` 条目；报告项：报告声称写了即失败；supervisor 自己代录的条目与本会话用户消息逐字一致 | 有新增条目即失败 |
| F7 | （U9 未选时不存在）U9 选 A 时：`check_role_writes.py --role <r> --base <commit>^` 与路径白名单比对，非门诊断 | 结果只进 A9 报告，不退回 |
| F8 | 磁盘项：每个带 `Dispatch-Id` 的提交主题以 `<work_id> ` 开头且含 `requested.round` 字面；报告项：`this_round` = `requested.round` | 不与交接行的下一轮次比 |
| F9 | 复核轮：复核文件 `round_candidate:` = §3.4 解析的候选 SHA，≠ 复核提交自身；通过轮才有 `passed_candidate:` 且相等 | 双 SHA 分别比对 |
| F10 | 实现停点：证据文件具名自证小节存在，每条 AC/BC 有 `test:`/`artifact:`/`cmd:` 指针 | grep |

**无报告时的来源（AD3-1）**：每项核查分磁盘项（必做）与报告项（有报告时的交叉核对）；报告缺失时报告项记 N/A、磁盘项照常，一项核查读同一
行两遍不算交叉核对；F1/F2/F9/F10 本就只有磁盘项；`requested.round` 来自派发日志，不来自报告。

通过例（正常换角色/换轮次）：接受角色派发 `this_round = D1`，提交主题 `COORD-015 D1 …`（F8 ✓）；它把交接行写成 Owner=Ideation、
Status=`AWAITING_IDEATION_D2` 且报告 `handoff` 相同（F3a ✓）；Gate 行 Overall 改为 `REVISION_REQUESTED_ROUND_1` 且派发角色是接受（F3b ✓）；
实现派发把 Implementation 列 `IMPLEMENTING`→`IMPLEMENTED`、Overall/Lifecycle 不变（F3b ✓）；构思派发把本行 Overall `REVISION_REQUESTED_ROUND_2`→`PROPOSED_D3`（F3b ✓）。

适用矩阵（✓ 适用；N/A 附理由；证据缺失 = 失败；**N/A 记为 N/A，不记为通过**）：

| | 构思 D 轮 | 接受 D 轮 | 接受 C 轮 | 实现停点 | 复核 R 轮 | 辅助 |
|---|---|---|---|---|---|---|
| F1 F2 F3a F4 F6 F8 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| F3b | ✓（允许集见表） | ✓ | ✓ | ✓（允许集见表） | ✓（两列不得变） | ✓（两列不得变） |
| F5 | N/A（无数字主张时） | ✓ | ✓ | ✓ | ✓ | ✓ |
| F7 | 仅 U9 选 A 时对全部角色适用 | | | | | |
| F9 | N/A | N/A | N/A | N/A | ✓ | N/A |
| F10 | N/A | N/A | N/A（核对表由接受写） | ✓ | N/A | N/A |

处置：不一致时 supervisor 不改内容，状态板 Log 写一条 `supervisor 核查：<编号> 不一致 + 指针`（≤ 600 B），交接行退回同一角色并
写明差异；第 2 次仍不一致即 §3.6 (d) 停下。核查通过不写 Log。演练与 A9 报告逐项记 {pass, fail, N/A(理由)}，「全过」= 适用项全 pass。

反例（夹具，均须判失败）：候选不在 `origin/main`（F2）；Log 写 `Ran 12` 而证据文件 `Ran 11`（F5）；复核文件 `round_candidate` 等于
复核提交自身（F9）；构思派发的批次里本行 Overall 由 `REVISION_REQUESTED_ROUND_2` 变为 `ACCEPTED`（F3b）；实现派发的批次里本行 `Lifecycle` 变为 `PAUSED`（F3b）；提交缺 `Role-Check` 尾注（F1）；子代理报告称已写账本用户原话
（F6）；交接行 Status 与报告 `handoff.status` 不符（F3a）；提交主题 `D2` 而报告 `this_round: D1`（F8）。

## 5. 有界代拍（S2/S3；AR1-3、AR1-4、AR2-2）

### 5.1 代拍类逐类定义

| 类 | 触发 | 允许动作（闭集） | 禁项（触发即回用户，优先于允许） | 执行角色 | 计数键 | 首版默认 |
|---|---|---|---|---|---|---|
| D1 | 接受角色第 2 次 `REVISION_REQUESTED` 后，及此后每一轮仍有具名残留的裁定，把交接 Owner 设为 supervisor | 仅当 r(n) < r(n−1) 时选 (a) 保留范围并逐条列缺口（缺口 = 本轮 `open_items:`）。r(n) = 接受角色第 n 轮裁定节末机读行 `open_items: <具名条目 ID，逗号分隔｜none>` 的 ID 数；supervisor 与 check_ledger 只从提案文件读，不从报告取；r(n−1) 读上一轮同名行；D1 条目写 `round: D<n>`、`open_items_now`、`open_items_prev` | (b) 关闭负结果；任何缩小/拆分范围；supervisor 为作者；r(n) ≥ r(n−1)；本轮或上一轮缺 `open_items:` 行或格式不合；同一轮第 2 次。均回用户，用户处置不受判据约束；存量提案不回填 | 接受角色按 (a) 继续 | `<work_id>:D1:D<n>`（每裁定轮 1 次；严格递减故每提案总次数 ≤ r 首值） | 启用 |
| D2a | 复核角色申请沿用上一轮会话上下文 | 授予该停点 1 次例外 | 不得替代 verdict、不得解除 `blocks_consuming_gate`、不得跳过开轮资格；第 2 次 | 复核角色 | `<work_id>:<停点>:D2a` | **禁用**（U1） |
| D2b | 同停点第 2 次 `REWORK_REQUIRED` 后轮 3 终局回用户 | 批准 1 次定向返工（限冻结集内具名 finding） | 同上；冻结集外；第 2 次 | 实现→复核 | `<work_id>:<停点>:D2b` | **禁用**（U1） |
| D3 | chore 按 work item 组提交 history 移入同意 | 逐组同意 | 组内含活跃项或未闭义务 | chore | `<work_id>:D3` | **禁用**（U2） |
| D4 | 角色列出已签信封内步骤的次序选项 | 在已列步骤内排序（先复核再跑、归档后再放行、提交时机） | 新增额度/步骤；含计数或合同裁定的混合题；含 Play 的步骤仍需用户在场 | 对应角色 | `<work_id>:D4:<n>` | 启用 |
| D5 | 接受/核对轮把选项集交 supervisor，且每个选项都不改合同/BC/AC、不改信封、不改数据/采样、不改 Lifecycle、不触发 D3 | 选推荐项（无推荐则首项） | 选项集含任一改动即整题回用户（含「暂缓」答复） | 接受/实现 | `<work_id>:D5:<n>` | 启用 |
| D6 | 角色发问：推送已提交候选、按既有操作单归档、预列位置中选存储、已授权步骤排序 | 上述四种 | 删除、新传输渠道、新设备、改 Lifecycle；用户自发指令只代录 | 对应角色 | `<work_id>:D6:<n>` | 启用 |
| SUB | 实现子代理报告 `needs_user` 中的追加申请（`request_id`、维度、数量、理由） | 在执行信封子额度块内批准 | 维度不在块内、信封值为 0 的维度、下载、Play、新设备、合同例外 | 实现角色 | `request_id` | 随信封块 |

### 5.2 永不代拍（闭集）

DIR、LIFE（含 D1 的 (b)、暂停/恢复/关闭、`CLOSED_*`）、ENV（首签两种信封、新信封）、FACT；`AGENTS.md`「触及核心研究主张、阶段
边界、主指标、硬件目标或范围扩大」；红线放宽；infra 修改授权；新设备、新消耗类别、新传输渠道、Jetson 探测；`NEW_OBLIGATION`
超配额；改 BC/AC/合同/采样；`DONE`/`CLOSED_*`；任何下载安装；supervisor 自身利害事项。

### 5.3 两种信封块

```text
supervisor_decision_envelope:          # 一次性，用户逐字签，随账本条目
  enabled: true
  classes: [D1, D4, D5, D6]            # 闭集 {D1, D2a, D2b, D3, D4, D5, D6}，可删不可加；D2a/D2b/D3 须用户显式列入
  expires_at: <YYYY-MM-DD>             # 必填，日期型
  veto_window_days: <n>                # 必填；只对 D 类代拍生效
supervisor_subdelegation:              # 随每份执行信封，用户逐字签（用户定局 §0.3-1）
  enabled: true
  max_increment: {<维度>: <n>}         # 单次追加上限；键 ⊆ 本信封值 > 0 的维度
  max_total: {<维度>: <n>}             # 累计追加上限
  expires_at: K4 | <YYYY-MM-DD>        # 停点短名或日期，可同时给，先到者生效
```

SUB 代拍**没有否决窗口**：用户已在块内预授权，增量一经批准即可消耗；用户的控制手段是块的上限、到期与撤销（§5.5）。
因此 SUB 条目不写 `veto_until`，也不借用决策信封的窗口。

### 5.4 两类引用、字段闭集、失败关闭

代拍条目 `## YYYY-MM-DD <work-id> — supervisor 代拍：<一句话>`，机读行：`at: <ISO 8601 UTC>`（必填）、`delegated_class`（闭集
{D1,D2a,D2b,D3,D4,D5,D6,SUB}）、`cites_decision_envelope: <标题>`（D 类必填）或 `cites_execution_envelope: <标题>`（SUB 必填，且该
信封的 work ID = 条目 work ID）、`decision`、`reason`（D1 之外必填）、`increment: {<维度>: <n>}` 与 `request_id`（SUB 必填）、
`counter_key`、`dispatch_id`（有派发时）、`precheck_head: <40 位 SHA>`、`veto_until`（仅 D 类）、`round: D<n>` 与 `open_items_now`/`open_items_prev`（仅 D1，§5.1）、代录会话。信封、撤销条目同样必填 `at:`。
失败关闭（任一即拒绝提交）：未知键；负数、非整数或非有限值；缺必填字段；同标题重复条目；D 类引用执行信封或 SUB 引用决策信封；
串用他工作项信封；类不在被引信封 `classes`；SUB 维度不在块内或 `increment` 超 `max_increment`；同一 `request_id` 已有条目；
`counter_key` 超该类次数上限；两种信封块缺 `expires_at`；D 类缺 `veto_until` 或 SUB 出现 `veto_until`；D1 条目缺 `round`/`open_items_now`/`open_items_prev`、与提案文件该轮及上一轮 `open_items:` 行不符、或 now ≥ prev（§5.1）。

### 5.5 事件全序、历史合法性、撤销

- **事件全序**（签发、代拍、撤销统一使用）：按 `at:` 时间戳排序；`at:` 相同或缺失（存量条目）时按条目日期，再按文件位置
  （同日靠上者更新）。机检以此全序比较，不再单独比较日期。
- 代拍条目 E 引用信封 V **历史合法** iff：V 在全序中先于 E；V 在 E 的 `at:` 时刻未过期（日期型 `expires_at` ≥ E 日期）；不存在
  在全序中先于 E 的对 V 的撤销。后来的到期或撤销不追溯改判旧条目。
  反例 1（须通过）：同日 09:00 代拍 E，15:00 撤销 R → R 后于 E，E 仍合法；R 之后的新条目被拒。
  反例 2（须拒绝）：同日 09:00 代拍 E，11:00 才签发 V → V 后于 E，E 不合法（同日不能靠日期比较放过）。
- **当前可执行**由 supervisor 在每次代拍与每次消耗性派发前按全序与当前状态板重新判定，并把当时 `HEAD` 写入 `precheck_head`。
- 撤销：用户写条目 `## <日期> <work-id|全局> — 用户撤回信封：<标题>`，机读行 `supervisor_envelope_revoke: <标题>` 与 `at:`；新签
  `enabled: false` 的同名块等价于撤销。撤销自其 `at:` 起生效。

### 5.6 事件型到期、快照先于代拍、申请身份、否决

- **到期事实源唯一（AD5-1）**：事件型到期只由 `docs/current-status.md` 的内容判定；提交主题、提交信息与其他文件都不是到期事实。解析器（`tools/check_ledger.py --first-invalidation <work_id> --envelope <标题>`，机检与 supervisor 共用）：
  S = 首次把该信封标题写入 `docs/authorizations.md` 的提交；**先在 S 处做初态检查**，再沿 `git log --reverse --first-parent S..HEAD -- docs/current-status.md`（恰是能改变该事实的全部一线提交，无遗漏）逐提交读该提交的状态板，
  X = 从 S 起第一个满足任一条件的提交：(i) 该 work ID 交接行 Status 匹配 `AWAITING_C\d+_(AT_)?<停点>`；(ii) 该 work ID 的 Gate 行 `Lifecycle` ∈ {PAUSED, ENDED} 或该行已不在 Gate board（移入 parked）。
  原「提交主题匹配 `^<work_id> [CR]\d+@<停点>`」不再是到期条件，只作派发守卫的提示（见下）。签发时已满足即 X = S（信封生来已到期，引用它的条目一律拒绝）。每份信封只用自己的 S；同一 work ID 恢复后由用户另签的新信封
  从其新 S 起算并同样先做初态检查，旧信封的 X 不转移也不清除。日期型到期不用解析器。X 一旦存在即永久生效：恢复、进入后续轮次或 token 消失都不使旧信封复活。
- **历史合法性（机检）**：`commit(E)` = 首次写入条目 E 标题的提交。SUB 条目 E 合法还须：`precheck_head` 是 `commit(E)` 的祖先（`git merge-base --is-ancestor`）且等于 `commit(E)` 的首父（快照即代拍前实际最新状态，其后无迁移可漏）；
  X 不存在，或 X 既不等于也不是 `commit(E)` 的祖先。反例（A2）：线性历史 `P → X → E`、`precheck_head` = P → 拒绝（X 是 `commit(E)` 祖先）；E0 的提交先于 X → 通过；`precheck_head` 非首父 → 拒绝；到期 → 恢复 → 再申请 → X 仍是祖先，拒绝。
- **预提交视图（pre-commit，AD4-2/AD5-1）**：待提交条目 = 暂存区 `git show :docs/authorizations.md` 中有、HEAD 中无其标题的条目；其 `commit(E)` 尚不存在，首父即当前 HEAD，谓词等价地改为 `precheck_head == HEAD`；
  X 在 `S..HEAD` 上解析，并把暂存的 `docs/current-status.md` 当作紧随 HEAD 的虚拟提交检查 (i)(ii)（两条件只读状态板，预提交完全可判；虚拟提交命中即 X = 本次提交 → 拒绝）；待提交信封的 S 尚不存在时，初态检查用暂存状态板。
  未暂存的工作树差异不参与判定。等价性：提交后 `commit(E)` 的首父就是当时的 HEAD、其状态板就是当时暂存的状态板，而到期事实只来自状态板，故两视图对同一条目结论相同；状态板未暂存时该提交事后也不被枚举，同样一致。
  `--no-verify` 绕过的提交由派发守卫下次运行时按提交后视图补判。
- **当前派发守卫（运行时）**：每次代拍与每次消耗性派发前 `git fetch`，在当前 HEAD 重跑解析器，X 存在即拒绝；把当时 HEAD 写入 `precheck_head` 并立即单独提交（不与状态板改动同批），提交前 HEAD 已移动则重判。
  **主题提示（非权威）**：同时扫描 `git log --first-parent --format=%s S..HEAD`（不限路径），主题匹配 `^<work_id> [CR]\d+@<停点>` 而 X 不存在 → 按 §3.6 (i) 停下，交用户核对状态板；提示不产生 X，也不改变任何已入账条目的合法性。
- 申请身份：`request_id = <work_id>:<信封标题 sha 前 8 位>:SUB:<n>` 由实现子代理在 `needs_user` 中给出、跨重派稳定；重派（新
  `dispatch_id`）复用同一 `request_id`，不重复批准；新增追加须新 `request_id` 与新条目。
- 累计 = 引用同一执行信封的全部 SUB 条目 `increment` 之和；SUB 无否决，不存在返还。
- D 类否决：窗口内用户写 `## <日期> <work-id> — 用户否决代拍：<标题>` 条目；只能停止未执行动作（未派发、未提交），对已执行的
  D 类决定 = 该决定重开交用户，工作产物保留；可撤回与不可逆两类在检查点摘要中分列。

### 5.7 被替换的常驻规则与用户选项

| 类 | 被替换句子 | 替换后 | 未选时 |
|---|---|---|---|
| D1 | workflow §4.2 L201–203「必须上交用户二选一」；engineering §3 L67；acceptance L19；ideation L11/L28；accept.md L21/L43；README L18 | 「决策信封 D1 在效且残留数严格递减（§5.1 `open_items:`）时上交 supervisor，supervisor 仅可选 (a)，否则上交用户」 | 原句不变 |
| D2a / D2b | review.md L19「本会话必须是新鲜上下文」的例外授予人（现由用户逐次授权）／ workflow §4.4 L389「轮 3 终局：通过，或回用户」、review.md L66 | 「信封 D2a 在效时 supervisor 可授每停点 1 次例外」／「…或回 supervisor（信封 D2b 在效时仅可批准 1 次冻结集内定向返工）」 | 原句不变 |
| D3 | chore.md L47–52「须先经用户同意」 | 「…或 supervisor（信封 D3 在效）」 | 原句不变 |
| D4–D6 | 无常驻句（接受角色惯例问用户） | 细则新增 | 惯例不变 |
| SUB | AGENTS「任何越界回到用户」（L59/L227）等 | 「子额度块内的追加由 supervisor 批准并入账；块外仍回用户」 | 原句不变 |
| F7 | workflow §7 规则 7「已提交批次的写入归因不做机械检查」 | U9 选 A 时加「supervisor 可对派发提交做非门诊断复跑」 | 原句不变，F7 不存在 |

### 5.8 红线兼容

授权来源仍是用户原话（两种信封）；代拍是对已签信封的行使，结构同「信封内工程性重试不需要新授权」；每次行使单独入账并被机检绑定到
信封，引用缺失、不合法或字段不闭合即拒绝提交而非默认允许；撤销与否决路径使用户随时可收回。

## 6. 协调批次节流（T；用户定局 §0.3-2）

supervisor 提出的 COORD 批次两两间隔 ≥ 5 个自然日（以上一批用户授权条目日期起算），每窗口 ≤ 1 个；同窗口发现的问题打包进下一批；无数据不提（数据 =
账本频率、成本实测、`check_*` 拒绝记录、复核 finding/轮次统计、字节或行数、调度日志），提案须有取证口径节。emergency COORD 仅限 correctness、权限、deadlock：
可立即提、不占窗口、标题带 `(emergency)`、贴触发失败输出、diff 最小，仍须用户授权（或落入 `--infra-fix` 例外）；窗口计法按 U5。

## 7. 池重分配与 Codex CLI（P；用户定局 §0.3-4/5）

| 角色 | 现行 | 提议 |
|---|---|---|
| 构思 | Fable | Fable（修订 5：工程轨道 Opus） |
| 接受 | Codex 桌面应用 `/prompts:codex` | Codex CLI 非交互 `codex exec`；交互式入口保留给用户手动使用 |
| 实现 | Cursor `/coding` | Claude **Opus**，`/implement` 改为主入口；`.cursor/` 入口按 U8 |
| 复核 | Fable | Fable |
| 辅助 | Sonnet | Sonnet |
| supervisor | 无 | Opus（U4） |

档位规则仍成立：复核（Fable）不低于实现（Opus）；判断密集节点不在最便宜池。Codex CLI：`npm install -g @openai/codex`（npm 全局前缀
`/opt/homebrew`），与桌面应用共用 `~/.codex/auth.json` 与 `config.toml`；非交互模式的审批策略、沙箱、退出码**装后实测**（A6）；不达标则
接受角色回退为「用户检查时手点」，记为 `DEGRADED_MANUAL_ACCEPTANCE`，A5 的「全自动」不算通过。安装须落地批次逐字授权。Cursor 相关
句子闭集：AGENTS L106；workflow §1.1 L57、§4.3.3 L313；implementation.md L3–6；review.md L7；codex.md L2/L12；implement.md L2/L6–7。


## 8. 减负估算（要素 6；AR1-7、AR2-4）

- **切换**：基线 = 交接提交 140 次 / 17 天、用户开会话 76 次 / 17 天（§1 F1，附录 A）。目标限定为：**在自动接力成功的链段内**每次交接
  不再需要用户开会话；扣除每日重开 supervisor、Unity/人眼/设备节点、信封首签、DIR/LIFE/FACT 决定、A6 回退时的接受轮、核查两次失败与
  状态不明的停下。不预测整体数字，落地后按 A9 用同一口径实测。
- **账本样本逐条重判**（按 §5.1 允许动作、禁项、次数键逐条给证明；统计原件与历史授权不改写；「潜在」= 混合条目中可代拍的部分，
  只列上界、不计收益）：

| 序号 | 条目 | 判定 | 证明 |
|---|---|---|---|
| 39、1 | SFT-002 / FAST-001 第二次退修选 (a) | D1 ✓ | 原话即 (a)，未附范围变更；存量无 `open_items:` 行，以裁定具名条目数代算：AR1→AR2 为 4→3、5→3，严格递减 |
| 51、46 | ASSET-001 / SFT-001 第二次退修 | ✗ 用户 | 删除重放实验 / 拆项 = 范围变更 |
| 28 / 27 | LOOP-001 第二次退修选 A / D3 残留继续修正 | ✗ 用户 / D1 ✓ | 代算 AR1→AR2 为 6→6 不递减 / AR2→AD3 为 6→4 递减，同轮首次（接受后修订 1 前分别为 ✓ / ✗） |
| 85 | BODY-001 `--compare` 放行次序 | ✗ 用户（潜在 D4） | 选项 2「归档后直接授权、不等复核」减一道步骤且含授权；条目自注 compare 仍须另签 |
| 86 | BODY-001「B5 前先复核」 | ✗ 用户 | 用户自发；新增放行前置 = 新增步骤 |
| 88 | BODY-001 GO 计数 + B4 前复核 + 提交 | ✗ 用户（潜在 D4：「提交」项） | 含计数裁定与新增前置 |
| 96、95 | BODY-001 G1/G2 暂缓 / 协议与准入判据、替代 ID | ✗ 用户 | 选项集含合同改动，整题回用户 |
| 35 | SFT-002 C2-4「先修代码，不重抽」 | ✗ 用户 | 「重抽」选项改数据/采样 |
| 72、107 | DATA-001 推送第 5 候选 / EVAL-001 释放推送并启动复核 | D6 ✓ | 角色发问；推送已提交候选、已授权步骤排序 |
| 101 | BODY-001「查看并归档 arm A trial 1」 | ✗ 只代录 | 用户自发指令 |
| 36、34 | SFT-002 入口/预检追加、F1 返工追加 | SUB ✓（需块） | 既有维度、信封值 > 0；#34 在循环内由实现派发的 `needs_user` 提出 |
| 7、5 | LOOP-001 R4 同会话例外 / R5-F7 一次定向返工 | D2a/D2b ✓（仅启用） | 各停点首次 |
| 14 | COORD-012 8 组 history 同意 | ✗ 用户（潜在 D3：无未闭义务的组） | 申请含带未闭义务的组，混合 |
| 13 | COORD-012 推送 + 整组移入 + 关闭 | ✗ 用户 | 用户自发；含 LIFE（`CLOSED_BY_USER`/`ENDED`） |

  逐条证明可消除的打断：默认类 **5/137**（D1 3 + D6 2）；附子额度块 **7/137（5%）**；启用 D2a/D2b 再 +2 → 9/137（7%）；D3 0。
  潜在上界（#85、#88、#14、#13 的次序/提交/合规组/推送部分）+4 → ≤ 13，不计为收益。撤回 D3 版「默认 9–10、全启用 13–14」口径。
  此数字只说明「可少打断多少条」，不是分钟数。
- **META**：30 → 按 5 天窗口聚簇同期问题 7 批 → 7–14 条。
- **异地转录**：只限「发生在 supervisor 会话内的授权不再需要异地转录」；实现子代理不与用户对话，用户在其他会话说的话仍需转录。
- 新增成本：supervisor 会话（Opus）、代拍与调度日志写入；A9 计量。

## 9. 兼容性与受影响接口（要素 2、4；AR1-5、AR2-3）

### 9.1 与 v0.3 设计及现行机制

不触及 `docs/phase1-single-drone-design.md`、运行时代码、协议、指标、冻结项；不新增状态门或通过态；`CLOSED_*`、`DONE` 三证据、核对轮/复核轮
规则（除 §5.7 用户勾选启用的替换句外）、执行轨道纪律与 Gate-echo、Log 可压池与字节上限、「已提交批次不做机械检查」（除 U9）不变。
调度不改变写权限：每个角色仍以自己的白名单提交。§4.1 第 8 要素：不冻结数据合同。

### 9.2 落地要改的文件（闭集）

| 文件 | 改动 |
|---|---|
| `AGENTS.md` | 「角色边界」加 supervisor 条、改实现条（L106）；「共享状态更新」加两种信封块、代拍/撤销/否决条目、`at:`、提交尾注、调度日志；红线句加「决策信封与子额度块同样只能由用户逐字签发」 |
| `CLAUDE.md` | 角色分工一句同步 |
| `docs/collaboration-workflow.md` | §1 表加行；§1.1 池表（L57）；§4.2 L201–203、§4.4 L389 按 §5.7/U1；§4.3.3 L313 措辞；§6 表加 `docs/roles/supervisor.md`、调度日志；§7 规则 7 协调批次执行会话与 U9 |
| `docs/engineering-workflow.md` | §3 L67 同句；§8 并发段引用 §3.1 |
| `docs/roles/supervisor.md`（新） | §2–§6 全文 |
| `docs/roles/{acceptance,implementation,review,ideation,chore}.md` | 运行地/池（implementation L3–6、review L7）；§5.7 句子；末尾「被 supervisor 拉起时」报告段与提交尾注要求；acceptance 加「第 2 次退修起每轮裁定节末写 `open_items:` 机读行」（§5.1 D1） |
| `.claude/commands/supervisor.md`（新）；`fable/implement/review/chore/accept/codex.md`；`.cursor/commands/coding.md`、`.cursor/rules/implementation-role.mdc` | 入口；报告段与尾注；`implement.md` L2/L6–7 去「备用」；`codex.md` L2/L12 池同步；`.cursor/` 按 U8 |
| `tools/check_role_writes.py`；`tests/test_check_role_writes.py` | `ROLE_RULES["supervisor"]`；A1 用例 |
| `tools/check_ledger.py`（新）；`tests/test_check_ledger.py`（新） | §5.4–5.6 机检；A2 用例 |
| `tools/githooks/pre-commit` | 先运行 `tools/check_ledger.py`（失败即退出非零）再 `exec` check_docs；不新增 `commit-msg` 钩子（到期事实不含提交主题，AD5-1） |
| `tools/make_supervisor_drill.py`（新）；`tests/test_supervisor_drill.py`（新） | 生成夹具到临时目录（§10）；五段演练的机械部分 |
| `docs/proposals/README.md` L18；`docs/authorizations.md` 文件头；`docs/workflow-changelog.md` | §5.7 句与 COORD 作者缺省 supervisor；格式段加两种信封块、代拍/撤销/否决条目、`at:`；批次索引 COORD-015 行 |
| 仓库外 `~/.codex/prompts/codex.md` | 报告段、尾注、`open_items:` 行与 §5.7 D1/D5 句；用户手动同步，须在首次无人值守拉起前验收（A4） |

### 9.3 A3 的具名映射（不做全局替换）

| 位置 | 现句 | 新句 |
|---|---|---|
| workflow §4.2 L201–203；engineering §3 L67；acceptance L19；ideation L11/L28；accept.md L21/L43；README L18 | 上交用户二选一 | 决策信封 D1 在效且残留数严格递减则上交 supervisor（仅 (a)），否则上交用户二选一 |
| workflow §4.4 L389；review.md L66 ／ chore.md L47–52 | 轮 3 终局：通过，或回用户 ／ 须先经用户同意 | U1 含 D2b 时加「或回 supervisor（1 次定向返工）」／ U2 选 A 时加「或 supervisor（信封 D3 在效）」，否则不改 |
| workflow §7 规则 7；AGENTS「共享状态更新」同句 | 已提交批次的写入归因不做机械审计 | U9 选 A 时加非门诊断复跑一句，否则不改 |
| AGENTS L59/L227；workflow L184/L635；engineering L60/L140；acceptance L94；README L152 | 越界回用户 / 超出回用户 | **不改** |

## 10. 验收条件（要素 5；AR1-6、AR2-1…3）

演练夹具：`tools/make_supervisor_drill.py` 在临时目录生成 git 仓库副本（精简状态板、账本、角色入口、消耗账本样例），合成 work item `DRILL-001`；演练只在夹具内运行，
结果标注「合成演练，不构成任何真实 D/C/R 轮次或门决定」，不触碰真实状态板、账本或暂停项；夹具内子代理与 `codex exec` 的 cwd 为夹具目录；每项核查逐条记 {pass, fail, N/A(理由)}。

| 编号 | 条件 | 证明方式 |
|---|---|---|
| A1 | 白名单：`docs/proposals/P1-X.md`、`docs/reviews/x.md`、`tests/x.py`、`AGENTS.md` 各被拒；`docs/proposals/COORD-016-x.md` + `docs/authorizations.md` + `docs/evidence/supervisor-dispatch.jsonl` 通过 | test:`tests.test_check_role_writes` 新增 6 例，修复前必失败 |
| A2 | 机检：§5.4 失败关闭清单每项一例；§5.5 反例 1 通过、反例 2 拒绝；撤销后新条目拒绝、撤销前条目通过；到期后的旧条目通过；§5.6 快照非祖先拒绝、`precheck_head` 非首父拒绝、旧快照例 `P→X→E` 拒绝、X 之前的旧代拍通过、到期→恢复→再申请拒绝；同一 `request_id` 第二条拒绝；累计超限拒绝；SUB 带 `veto_until` 拒绝；真实 pre-commit 路径：合法首次入账通过（含首次签发信封）、`precheck_head` ≠ HEAD 的首次入账拒绝、签发时已在停点的信封（X = S）被引用即拒绝、历史条目复判与提交后结果一致；AD5-1 三例：提交主题匹配 `^<work_id> C1@K4` 但状态板未到期（该提交只改 Log）的 SUB 条目 → 提交前通过、提交后复判通过；主题匹配却不改状态板的提交 X′ 之后写入的 SUB 条目 → 通过（X′ 不被枚举、不是 X），两视图一致；同一提交既写 SUB 条目又把状态板改到停点 → 提交前拒绝（虚拟提交命中）、提交后拒绝（X = commit(E)）；D1 四例：`open_items_now` < `open_items_prev` 且与提案文件两轮 `open_items:` 行一致 → 通过；相等 → 拒绝；提案缺该轮或上一轮 `open_items:` 行 → 拒绝；同一轮第二条 D1 → 拒绝；合规样例通过 | test:`tests.test_check_ledger` ≥ 29 例；cmd:`python3 tools/check_ledger.py` |
| A3 | §9.3 每处位置含对应新句，末行位置逐字不变；§4 反例 9 例逐一判失败、通过例 3 例判通过（含实现合法推进与构思 `PROPOSED_D<n>`） | cmd:输出存 `docs/evidence/COORD-015-route-check.log` |
| A4 | 六个角色入口（含仓库外 `codex.md`）末尾报告段与尾注要求与 §3.8 一致；首次无人值守拉起前完成 | cmd:`grep -c` 输出入库 |
| A5 | 夹具演练六段：①正常接力与 D1 代拍（构思 D1 → 接受 D1 退修 `open_items:` 4 项 → 构思 D2 → 接受 D2 第 2 次退修 `open_items:` 2 项 → supervisor 按 §5.1 D1 代选 (a) 并入账 → 构思 D3 → 接受 D3 `open_items:` 2 项，不递减 → 停下交用户；停下前六次派发无人介入，适用项全 pass）；②重复派发（第二次回调记 `duplicate_callback`，无重复核销；另一 work_id 有未闭派发时拒绝派发）；③实现提交后报告丢失 → `end_confirmed(callback)` → 无报告来源核查（报告项 N/A、磁盘项全 pass）→ `reconciled(report_lost)`，候选按 §3.4 解析 → 接受 C 轮 → 复核派发绑定该候选，F9 pass；④用户暂停（运行中零消耗角色停止并 `aborted(user_pause)`，之后不再派发）；⑤未知消耗与主题提示（夹具消耗账本出现晚于 `started_at` 的事件 → 停下，不重派；提交主题匹配 `DRILL-001 C1@K4` 而状态板未到期 → 派发守卫按 §3.6 (i) 停下，不代拍、不产生 X）；⑥结束未确认不判终态：(甲) 提交已出现但无凭据 → 等待，宽限内回调到达 → 转 ③；(乙) 模拟重启、旧运行者为子代理且 `stop_call` 失败 → 停下并保持未闭，注入 `user_quote` 后才 `reconciled`；(丙) `codex exec` 用 `pid_gone`（含 pid 复用样例）；(丁) 只有 `requested`（启动后、写 `started` 前中断）而旧写者仍活跃 → 重启后不派发另一 work ID，停下索取 `user_quote`，旧写者随后提交 → 转 ③；(戊) 启动无 id 且无显式错误 → `started(unknown)` 阻止其他派发；显式启动错误 → `launch_failed` 重派 1 次 | artifact:`docs/evidence/COORD-015-drill.md` + 夹具内 `supervisor-dispatch.jsonl` |
| A6 | Codex CLI 装后实测：`codex exec` 能读夹具仓库、写 `docs/`、不弹审批、退出码可判、按提示完成一次合成接受轮；任一不达标即 `DEGRADED_MANUAL_ACCEPTANCE` 且 A5 ① 不算全自动通过 | artifact:`docs/evidence/COORD-015-codex-exec.md` |
| A7 | 实现子代理（Opus）在夹具内按合成的已接受范围完成一次 focused 实现提交，适用项全 pass（含 Implementation 列 `IMPLEMENTING`→`IMPLEMENTED`、Overall/Lifecycle 不变的 F3b pass，与改 `Lifecycle` 的反例 fail）；不触及真实 `P1-*` 与 infra | artifact:同 A5 |
| A8a | 本批 diff 不改任何既有工作项的门值、verdict、未闭义务、授权原话；不触及活跃 `P1-*` 行 | cmd:`git diff` 逐字比对 |
| A8b | 本项自身状态推进按现行规则正常，不被 A8a 误拦 | 状态板 Gate 行与 Log |
| A9 | 落地后 30 天报告（不设门）：附录 A 口径的交接提交与开会话次数、检查点数、代拍/否决数、核查逐项 pass/fail/N/A 计数、各类账本条目 vs §8、supervisor 会话费用；附录 A 脚本与原始输出入库 | artifact:`docs/evidence/COORD-015-after-30d.md` |
| A10 | supervisor 发起的 COORD 授权日期两两间隔 ≥ 5 天，emergency 除外 | cmd:账本标题扫描，写入 A9 |

复核项映射（供接受角色在 `ACCEPTED` 时写 BC，本轮不预填）：行为 ← A5/A6/A7；边界失败 ← A2 失败分支、A5 ②–⑥、A3 反例；测试覆盖 ← A1/A2 修复前必失败；文档一致 ← A3/A4/A8。本轮不签任何 `UNITY_NA` 关闭结论。

## 11. 失败模式与资源风险（要素 6）

| 风险 | 缓解 |
|---|---|
| 把声称当进度、退取旧候选、重复派发、回调丢失、运行者未结束即重派 | 凭据在提交尾注与 git，缺证据 = 失败；§3.4 解析顺序唯一、第 3 步停下；两次不一致停下；§3.2–3.5 登记/核销/对账、全局去重、结束凭据闭集与等待、未确认即停；消耗性不自动重派 |
| supervisor 成为第二授权来源；同日撤销次序；到期后 token 消失使信封复活 | 两类引用、`at:` 全序与两反例、撤销、否决、`request_id`；首次失效提交 X（含签发时初态）永久生效；到期事实只来自状态板（主题仅提示），预提交视图与提交后谓词等价 |
| supervisor 自己动手；复核独立性被父会话污染 | §2.2 硬边界与白名单；§3.7 固定模板、不含 claims、提示 sha256 |
| 演练污染真实状态；Codex CLI 非交互行为不符；实现改 Opus 后 Claude 侧账单上升；Unity/人眼/设备节点 | 只在夹具、结果标注合成、A8a；A6 实测与显式降级；A9 计量，可改回一行入口；停下条件 (b) |

## 12. 建议的实施范围与依赖次序（要素 7，不强制）

1. 用户在账本逐字授权本批（含 Codex CLI 一次下载与 U1–U9 的选择）；2. 规则/角色/命令/报告段与尾注要求（§9.2 文档类文件）；
3. 测试与工具（A1/A2 修复前必失败 → `check_role_writes.py`、`check_ledger.py`、`pre-commit`；`make_supervisor_drill.py`），单独提交；
4. 仓库外 `~/.codex/prompts/codex.md` 同步并验收（A4）；5. 安装 Codex CLI，跑 A6，不达标按 §7 降级；6. 生成夹具 → A5 六段 + A7，
证据入库，全套测试按 COORD-009 纪律跑一次；7. 用户签第一份决策信封（独立账本条目）并写「启用 supervisor 无人值守」账本条目；
8. 首次真实派发限零消耗工作项，随后按 §3 循环。预计 2 个 supervisor 会话、4–5 次提交。

## 13. 用户待决（有限选项，未选即按「未选时」执行）

0. 路径、退修与残留处置（D2–D5）、D1 计数：已解决（接受轮；用户选 A/(a)；D1 改残留数严格递减，用户「改成第二种」）。U4 经修订 2/3 改判后由修订 4 撤销，恢复原选项与缺省（见下）。
1. U1 D2a/D2b：A 启用 D2a｜B 启用 D2b｜C 都启用｜D 都不。未选 = D。
2. U2 D3：A 启用｜B 不启用。未选 = B。
3. U3 否决窗口天数：由用户在决策信封 `veto_window_days` 填写；只对 D 类；否决不承诺回滚实耗。未签信封 = 代拍整体不启用。
4. U4 supervisor 模型：A Opus｜B Fable。未选 = A。检查节奏约 2 h、通知只在停下时发：A 可以｜B 改为 ___。未选 = A。
5. U5 窗口计法：A 仅 supervisor 发起的批次计入｜B 全部批次计入。未选 = B。
6. U6 首封 `expires_at`：A 30 天｜B 60 天｜C 用户写日期。未选 = 信封未签，代拍不启用。
7. U7 parked 写权：A 给（仅机械搬运）｜B 不给。未选 = B。
8. U8 `.cursor/` 入口：A 保留为遗留｜B 删除。未选 = A。
9. U9 提交后路径审计与诊断复跑（F7）：A 启用｜B 不启用。未选 = B（F7 不存在，workflow §7 规则 7 原句不变）。

## 附录 A. 切换基线脚本与 2026-09-25 复算输出（只读；落地时随 A9 入库）

```python
# A-1 交接提交：diff 触及「## Active handoffs」节的 docs/current-status.md 提交数（按日）
import subprocess, re, collections
sh = lambda *a: subprocess.run(a, capture_output=True, text=True).stdout
tot, hit = collections.Counter(), collections.Counter()
for sha, day in [l.split() for l in sh('git','log','--since=2026-09-08','--until=2026-09-25','--format=%H %ad','--date=short','--','docs/current-status.md').split('\n') if l]:
    if day > '2026-09-24': continue  # D4：`--until` 含当日提交，显式截到 09-24
    tot[day] += 1; txt = sh('git','show',sha+':docs/current-status.md').split('\n')
    s = next((i for i,l in enumerate(txt) if l.startswith('## Active handoffs')), None)
    if s is None: continue
    e = next((i for i in range(s+1,len(txt)) if txt[i].startswith('## ')), len(txt))
    diff = sh('git','show','-U0','--format=',sha,'--','docs/current-status.md')
    if any(int(m.group(1))-1 < e and int(m.group(1))-1+max(int(m.group(2) or 1),1) > s
           for m in re.finditer(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', diff, re.M)): hit[day] += 1
print(sum(tot.values()), sum(hit.values()), dict(sorted(hit.items())))
# 2026-09-25 本会话只读复算输出：147 140 {'2026-09-08': 9, '2026-09-09': 2, '2026-09-11': 9, '2026-09-14': 8, '2026-09-15': 4, '2026-09-16': 3, '2026-09-17': 2, '2026-09-18': 13, '2026-09-19': 10, '2026-09-20': 22, '2026-09-21': 3, '2026-09-22': 21, '2026-09-23': 25, '2026-09-24': 9}
```

```python
# A-2 开会话：Claude 顶层会话（首条时间戳）与 Codex 会话目录（按日）
import os, json, glob, collections
c, x = collections.Counter(), collections.Counter()
for f in glob.glob(os.path.expanduser('~/.claude/projects/-Users-zc-TetheredDroneTracking/*.jsonl')):
    for line in open(f, encoding='utf-8'):
        try: ts = json.loads(line).get('timestamp')
        except Exception: continue
        if ts: (c.__setitem__(ts[:10], c[ts[:10]] + 1) if '2026-09-08' <= ts[:10] <= '2026-09-24' else None); break
for root, _, files in os.walk(os.path.expanduser('~/.codex/sessions/2026')):
    p = root.split(os.sep); d = '%s-%s-%s' % (p[-3], p[-2].zfill(2), p[-1].zfill(2)) if len(p) >= 3 and p[-3] == '2026' else ''
    if '2026-09-08' <= d <= '2026-09-24': x[d] += len(files)
print(sum(c.values()), dict(sorted(c.items())), sum(x.values()), dict(sorted(x.items())))
# 2026-09-25 本会话只读复算输出：65 {'2026-09-08': 5, '2026-09-09': 2, '2026-09-11': 5, '2026-09-12': 2, '2026-09-13': 1, '2026-09-14': 3, '2026-09-17': 4, '2026-09-18': 7, '2026-09-19': 5, '2026-09-20': 3, '2026-09-21': 7, '2026-09-22': 8, '2026-09-23': 11, '2026-09-24': 2} 11 {'2026-09-20': 4, '2026-09-22': 1, '2026-09-23': 3, '2026-09-24': 3}（无会话的日期省略）
```

## Binding clarifications (BC table)

| 编号 | 条款 | 复核项 | 证明方式 | 标签 | 依据 | 日期 |
|---|---|---|---|---|---|---|
| BC-1 | S0 严守 §3.1–3.5 的全局单写者：未终结 requested、未知运行者、报告丢失和结束未确认时不得派发下一写者；仅凭 §3.4 的结束凭据核销，未知消耗不得自动重派。 | 行为/边界失败 | artifact:docs/evidence/COORD-015-drill.md | BASE | §3.1–3.6；A5②③⑤⑥ | 2026-09-25 |
| BC-2 | 派发候选只按 §3.4 的 finished.candidate、reconciled.candidate 顺序解析；缺可证明候选即停，复核派发按 §3.7 绑定该候选并使用不含实现 claims 的固定提示。 | 行为/文档一致 | artifact:docs/evidence/COORD-015-drill.md | BASE | §3.4/3.7；A5③ | 2026-09-25 |
| BC-3 | S1 对 §4 F1–F10 按适用矩阵核查：报告缺失时报告项记 N/A、磁盘项照核，正常换角色/构思 PROPOSED_Dn/实现 IMPLEMENTED 不得误退，§4 所列越权与缺凭据反例须失败。 | 行为/边界失败/测试覆盖 | artifact:docs/evidence/COORD-015-route-check.log | BASE | §4；A3/A7 | 2026-09-25 |
| BC-4 | S2/S3 只执行 §5.1 的 D1、D2a、D2b、D3、D4、D5、D6、SUB 类及各行禁项/次数键；D2a、D2b、D3 仅在用户选启用后生效，§5.2 的禁项直达用户，信封必须由用户逐字签发入账。 | 行为/边界失败 | artifact:docs/evidence/COORD-015-drill.md | BASE | §5.1–5.3、§13；A5 | 2026-09-25 |
| BC-5 | §5.4/5.5 的签发、代拍、撤销共用 at 全序；机检拒绝该节闭集列出的字段、引用、额度、次数和重复申请错误，旧合法条目不因后来的撤销或到期被追溯拒绝。 | 几何时序/边界失败/测试覆盖 | cmd:python3 -m unittest discover -s tests -p test_check_ledger.py | BASE | §5.4/5.5；A2 | 2026-09-25 |
| BC-6 | §5.6 的 X 仅来自该 work ID 状态板的交接到期状态或 Gate Lifecycle 失效；S 初态、暂存虚拟提交及提交后历史判定一致。同一提交新增 SUB 且状态板到期须在 pre-commit 拒绝；提交主题不产生 X。 | 几何时序/边界失败/测试覆盖 | cmd:python3 -m unittest discover -s tests -p test_check_ledger.py | BASE | §5.6；A2 AD5-1 三例 | 2026-09-25 |
| BC-7 | 当前派发守卫在每次代拍和消耗性派发前重算 X；§5.6 主题提示命中而 X 不存在时按 §3.6(i) 停下，不代拍、不修改历史合法性。 | 行为/边界失败 | artifact:docs/evidence/COORD-015-drill.md | BASE | §3.6(i)/§5.6；A5⑤ | 2026-09-25 |
| BC-8 | supervisor 常规写入仅限 §2.3 allow 路径，deny/INFRA_PATTERNS 优先；协调批次 infra 仅凭用户单独授权执行，提交前角色检查与状态板/Gate-echo 自检保留。 | 边界失败/测试覆盖/文档一致 | cmd:python3 -m unittest discover -s tests -p test_check_role_writes.py | BASE | §2.3/§9.2；A1/A8 | 2026-09-25 |
| BC-9 | 首次无人值守拉起前，A4 所指六个角色入口（含仓库外 codex.md）符合 §3.8 报告/提交尾注；Codex CLI 的读写、审批与退出码按 A6 实测，不达标进入 DEGRADED_MANUAL_ACCEPTANCE。 | 行为/文档一致 | artifact:docs/evidence/COORD-015-codex-exec.md | BASE | §3.8/§7；A4/A6 | 2026-09-25 |
| BC-10 | A5 六段合成演练与 A7 实现派发仅在隔离夹具进行，结果明确标为合成；§12 的首次真实派发要在用户授权协调落地、CLI 验收和启用入账之后。 | 行为/边界失败/文档一致 | artifact:docs/evidence/COORD-015-drill.md | BASE | §10/§12；A5/A7/A8 | 2026-09-25 |
| BC-11 | supervisor 发起 COORD 批次时执行 §6 的五天窗口、同窗打包、数据依据与 emergency 例外；按 A10 核对授权日期。 | 行为/文档一致 | artifact:docs/authorizations.md | BASE | §6；A10 | 2026-09-25 |
| BC-12 | 解释 BC-4 的用户指示 D1 修订：新工作项从首次 `REVISION_REQUESTED` 裁定（D1）起，每轮裁定节末由接受角色写 `open_items:`；值为互异、非空的具名 ID 逗号分隔，或单独 `none`。第二次及后续裁定仅在本轮数 < 上一轮数、决策信封 D1 在效且无 §5.1 禁项时每轮代选 (a) 至多一次；缺任一轮行、重复/空 ID、未递减即回用户。D1 条目的 `round`、`open_items_now`、`open_items_prev` 与两轮行须一致；新条目在 pre-commit 读当时 HEAD 的已提交提案，历史条目按其首次入账提交的首父提案复判，后续编辑不追溯改变旧结论。§9.2 的“第 2 次退修起写行”由本行改为“首次退修起写行”，A5① 的 D1 基线才可执行。 | 行为/几何时序/边界失败/测试覆盖/文档一致 | cmd:python3 -m unittest discover -s tests -p test_check_ledger.py | CLARIFY | BC-4；用户 2026-09-25「改成第二种」；§5.1/§5.4/§9.2；A2/A5① | 2026-09-25 |
| BC-13 | 解释 BC-9/10 所引 §7/§12 的用户指示修订 2/3：supervisor 在本机（用户当前工作机）CLI 会话运行，CLI 与模型由用户当轮选择、可更换，不固定名称或自动升档；§13 U4 旧模型选项失效，其余角色池与 U4 检查节奏不变。§7 清单只同步 supervisor 对应句，保留提示文件路径不证明所选 CLI 自动发现或可执行该入口；A4/A5/A7 仍须验证实际选定运行地的入口、接力及实现派发，A6 与降级规则保持，不能以原 Claude 会话能力或机械夹具通过替代。（修订 4 撤销：本行的运行地解释作废，恢复 D6 原文 Opus/U4=A；本行保留作历史记录。） | 行为/文档一致 | artifact:docs/evidence/COORD-015-drill.md | CLARIFY | BC-9/10；账本 2026-09-25「用户指示修订 2」及补充代录、「用户指示修订 3」；§2.1/§7/§13；A4/A5/A6/A7 | 2026-09-25 |
| BC-14 | 解释 BC-12「每轮裁定节末写 `open_items:`」的机读落点（`docs/reviews/COORD-015.md` R1@落地 R1-1）：(1) 第 n 轮裁定节 = 提案文件中唯一一行匹配 `^### D<n>(?![0-9A-Za-z])` 的三级标题起，至其后第一行匹配 `^#{1,3} ` 的标题（不含）或文件尾止；`####` 及更深标题属于该节，接受角色把逐条残留子节写成 `####`。(2) 第 n 轮的行 = 该节内匹配 `tools/check_ledger.py` 现行 `OPEN_ITEMS_RE` 的行，须恰好 1 行且为该节最后一个非空行，取值按 BC-12 解析。(3) 失败关闭（D1 条目拒绝）：第 n 或 n−1 轮标题为 0 行或 ≥ 2 行；节内匹配行为 0 行或 ≥ 2 行；匹配行不是节内最后一个非空行；取值格式不合。(4) 与文件序无关：各 `### D<n>` 节在文件中的先后不影响取值；不在任一 `### D<n>` 节内的 `open_items:` 行（如「接受后修订 N 审核」、核对表、复判节）不参与计数。提案快照规则按 BC-12 不变。 | 行为/边界失败/测试覆盖 | test:tests.test_check_ledger.D1Tests.test_d1_newest_first_layout_legal_passes；test:tests.test_check_ledger.D1Tests.test_d1_newest_first_layout_increase_rejected | CLARIFY | BC-12；复核 R1-1；§5.1/§5.4 | 2026-09-26 |
| BC-15 | 解释 BC-5 所引 §5.4「信封、撤销条目同样必填 `at:`」的相邻条款（`docs/reviews/COORD-015.md` R1@落地 R1-4）：`## <日期> <work-id> — 用户否决代拍：<标题>` 条目同属 §5.5 全序事件，`at:` 必填（与 `AGENTS.md`「共享状态更新」及账本文件头「代拍、撤销与否决条目带 `at:`」一致）；缺 `at:` 即失败关闭拒绝提交，不得跳过 §5.6 否决窗口判定。 | 边界失败/测试覆盖 | test:tests.test_check_ledger.StructuralTests.test_veto_missing_at_rejected | CLARIFY | BC-5；复核 R1-4（IN_SCOPE_NO_BC）；§5.4/§5.5/§5.6 | 2026-09-26 |

复核项覆盖：行为 ✓ | 几何时序 ✓ | 边界失败 ✓ | 测试覆盖 ✓ | 文档一致 ✓。

## Pending rulings（待裁定）

## Contract conformance（核对表）

### C2@落地（2026-09-26；同停点最终核对；BC-5/BC-12 两行按 `R2@落地` 通过轮更新）

候选范围为落地授权提交至本轮交接前的 `C1@落地 退回项修复` 提交，共 45 个变更文件，包含协调修订、授权、入口、工具、测试与演练证据；提交边界由 git 历史运行时解析，已按文件清单重读。研究轨道；本轮未跑测试、未改实现、未签独立复核。C1 退回的尾注格式、A3、稳定聚焦输出、A1 红绿、A8a 与四项自证均已有候选内指针。**C2 时 BC-5 不满足，按 §4.3.3 的 C 轮上限照交 `R1@落地`；R1 `REWORK_REQUIRED` 后修复经 `R2@落地` `PASS_WITH_NOTES`（复核 R2 §5 `passed_candidate`，运行时解析），BC-5、BC-12 两行已按 R2 改写，其余行为 C2 结论不变。**“满足”只表示接受侧合同核对，不表示复核通过或真实启用通过。

| BC | 结论 | 依据与待核实内容 |
|---|---|---|
| BC-1 | 满足 | 提案 §3.2、`docs/roles/supervisor.md`「派发登记」、各角色入口及 `tools/make_supervisor_drill.py` `commit_trailers()` 均为 `Role-Check: <role> pass`；`tests/test_supervisor_drill.py` 作整串断言。§3.2 为 C1 退回后的格式纠正，BC 表未改。 |
| BC-2 | 满足 | 提案 §3.4/3.7 与 `docs/roles/supervisor.md`「完成核销」「复核派发」给出候选解析顺序和固定提示；`docs/evidence/COORD-015-drill.md` §1③及合成日志记 `reconciled.candidate`、C/R 绑定与 F9。 |
| BC-3 | 满足 | `docs/evidence/COORD-015-route-check.log` (a) 26/26、(b) 九个反例及三个通过例 12/12；脚本全文在日志末尾，可与提案 §4/§9.3 逐项比对。F4/F5 扫描范围有限，列入关注项。 |
| BC-4 | 满足 | 提案 §5.1–5.3、`docs/roles/supervisor.md`「代拍类表」「永不代拍」一致；`docs/evidence/COORD-015-drill.md` §1①只在合成信封中演示递减代拍与持平停下。 |
| BC-5 | 满足 | `R2@落地` `PASS_WITH_NOTES`（`docs/reviews/COORD-015.md` R2 §5 `passed_candidate`，运行时解析；闭合见 R2 §1）：C2 所指 SUB 引用 `全局` 执行信封分支已去除（R1-2），同 `at:` 平局靠上者更新（R1-3），否决条目 `at:` 必填按 BC-15（R1-4）；三条具名测试副本内修前红/修后绿，focused 88 OK，真实账本机检通过。 |
| BC-6 | 满足 | `tools/check_ledger.py` `board_expired()`/`resolve_x()`/`check_precommit()` 与 `tests/test_check_ledger.py` `PrecommitViewTests`、`BoardExpiredFailClosedTests` 覆盖 S 初态、虚拟提交、提交后复判及 C1 指出的缺表头失败关闭；聚焦结果见 `COORD-015-focused-tests.log`。 |
| BC-7 | 满足 | 提案 §3.6(i)/§5.6 与 `docs/roles/supervisor.md`「事件型到期」一致；`docs/evidence/COORD-015-drill.md` §1⑤记录 X 不存在但主题命中时停下，未写代拍。 |
| BC-8 | 满足 | `tools/check_role_writes.py` supervisor allow/deny、`tests/test_check_role_writes.py` 六例；`docs/evidence/COORD-015-A1-redgreen.log` 红绿与 `COORD-015-A8a.log` 10/10 给出写权和非本项行/授权原话比对。 |
| BC-9 | 满足 | `docs/evidence/COORD-015-A4-grep.log` 六入口 3/3、字段 9/9；`COORD-015-codex-exec.md` A6 五项逐列记录。提交须用 `--sandbox danger-full-access`，退出码不反映带内任务成败，真实启用仍须按报告与磁盘核销。 |
| BC-10 | 满足 | `docs/evidence/COORD-015-drill.md` 与 `COORD-015-drill-dispatch.jsonl` 明示 A5/A7 仅夹具合成；`docs/authorizations.md` 无真实信封首签/启用条目。 |
| BC-11 | 满足 | `docs/roles/supervisor.md`「COORD 节流」列五天窗口、打包、数据与 emergency；A10 需要运行期授权日期，当前没有可扫描的真实 supervisor 提案序列。 |
| BC-12 | 满足 | R1 改判不满足（R1-1：按文件序取 `open_items:`）；`R2@落地` `PASS_WITH_NOTES`（复核 R2 §5 `passed_candidate`，运行时解析；闭合见 R2 §1）核实 `_d1_errors()` 按 BC-14 绑定 `### D<n>` 节、与文件序无关，两条具名测试（最新在上布局）修前红/修后绿。夹具生成器 `inject_open_items()` 与 BC-14 落点不一致（R2-1，失败关闭、不可达生产入口）记债，见 `docs/implementation-status.md` 缺陷账本。 |
| BC-13 | 满足 | 提案「回应索引」修订 4、BC-13 撤销注记、`docs/phase1-single-drone-design.md` §1 均指回 D6 Opus/U4=A。 |

**停点自证：**`docs/evidence/COORD-015-self-attestation.md`「§4.3.1 四项自证」逐条列范围冻结、相称 focused 通过、Unity N/A、状态板与风险；其「BC-1…13 逐条指针」覆盖全部 BC。全套日志 `docs/evidence/COORD-015-tests.log` 为 1640 例、1 FAIL/9 ERROR/27 skipped；自证「全套测试 10 项失败的归因」把错误指向缺 `numpy`/`cv2` 和旧 `runtime/frames` 残留。复核须判断这份归因是否足以满足稳定候选条件；本轮不代其签发资格或 verdict。A9 是 30 天非门报告，A10 运行期扫描仍未闭。

**预复核关注项（待核实主张，不定 finding 分级/依据值）：**(1) BC-5 的 SUB 全局信封分支，见 `tools/check_ledger.py` 第 421–422 行与提案 §5.4。(2) A3 脚本 `docs/evidence/COORD-015-route-check.log`「附：脚本源码」的 `f4()` 只找反引号 `docs/` 路径、`f5()` 只找 `Ran N`；对照提案 §4 F4/F5 的「路径/小节存在」「数字逐一比对」，核实合成测试的证明边界。(3) `COORD-015-tests.log` 的 10 项失败及自证归因，核实复核停点资格。另 `COORD-015-A8a.log` (a) 对 AGENTS 原句采用句级保留、行尾追加，核实 §9.3「不改」要求。

交接（2026-09-26 更新）：关注项 (1) 由 R1-2 闭合，(2)(3) 由复核 R1 §0/§3 核实（证明边界如实披露、全套失败归因成立）；本停点已由「Acceptance rulings（复判）」`R2@落地` 最终处置关闭。真实信封首签与首次启用仍须用户另行授权。

## Acceptance rulings（复判）

### R2@落地 最终处置（2026-09-26；接受角色，Claude Code `/accept` 备用运行地，用户直接指挥，零消耗）

消费 `docs/reviews/COORD-015.md` R2 §5 `PASS_WITH_NOTES`（`passed_candidate` 以复核文件 R2 §5 机读行运行时解析，不在此手写）。归因按依据列机械派生（workflow §4.6）：

| Finding | 分级 | 依据 | 归因 | 状态 |
|---|---|---|---|---|
| R1-1 | CLASS_1 | `BC-12` | 实现错误 | 闭合（R2 §1 红绿核实） |
| R1-2、R1-3 | CLASS_2 | `BC-5` | 实现错误 | 闭合（同上） |
| R1-4 | CLASS_2 | `IN_SCOPE_NO_BC` | BC 缺失（阻断；BC-15 补覆盖） | 闭合（同上） |
| R1-5 | CLASS_3 | `上游漏检` | 核对轮（C2 未查出演练记录的全套计数陈旧） | 闭合（补丁已应用） |
| R2-1 | CLASS_2 | `SCOPE_GAP` | BC 缺失（非阻断） | 记债 `OPEN`，`docs/implementation-status.md`「范围外已知缺陷」 |

复核 R2 §5 叙述称均为实现/证据侧错误；本表按依据列机械派生，R1-4、R1-5 分入 BC 缺失与核对轮。`上轮漏检`、`RED_LINE` 均 0。度量：C 退回 1（C1：BC-1 不满足、BC-3 证据缺失）、C2 照交 1；落地停点复核 2 轮（返工 1）；BC 缺失类 `IN_SCOPE_NO_BC` 1、`SCOPE_GAP` 1；`ACCEPTED` 后新增 BC 行 `CLARIFY` 4（BC-12…15）、`NEW_OBLIGATION` 0；设计退修累计 2。

**Overall `DONE`；Lifecycle 应为 `ENDED`，暂留 `ACTIVE`。** 三证据齐：实现证据（自证文件与 focused/全套日志、R1 返工红绿）、独立复核 `PASS_WITH_NOTES`、`UNITY_NA`（复核 R1 §4、R2 §4 两轮附议）。§10 A1–A8 有证据并经 R1/R2 核实；A9 原文「不设门」，A10 为运行期扫描、「写入 A9」，二者均不能在落地时发生，不是 `DONE` 前置。信封首签、首次启用与真实派发亦非前置：§10 验收表无此项；§12 标注「不强制」，第 7–8 步是用户签发与启用动作；§13 U3/U6 规定「未签信封 = 代拍整体不启用」，即不启用是落地后的合法状态；BC-4/9/10 写的是签发来源与首次拉起/派发前提，约束未来事件，不要求其发生。用户可永不启用，本项不应为等用户动作保持未关闭。暂留 `ACTIVE` 的唯一原因是机械阻塞：整行移入 `docs/parked-status.md` 后本项约 40 条 Log（161 行）按无关联计入可压池，池由 147 行升至 308 行，超 300 行上限被 `tools/check_docs.py` 拒绝；压缩须把叙述移入 `docs/status-history.md`，该文件只有 chore 可写、写入前须用户按 work item 同意，且本项未 `ENDED` 前其条目不可压。故交用户处置（状态板交接行）。选项：(a) 推荐——一次同意把 `COORD-015` 整组 Log 条目移入 `docs/status-history.md`，并授权一个用户直接指挥的零消耗协调批次在同一提交内完成压缩、Gate 行移入「已终止（ENDED）」与交接行移除；理由：chore 不能写 `docs/parked-status.md`、接受角色不能写 history、本项未 `ENDED` 前条目不可压，分角色分步会互锁，且本组是池内最大来源。(b) 同意压缩池内某个已有组（如 `COORD-011` 13 行条目）至少 8 行，chore 执行后接受角色单独移行；不需协调批次，但本组 161 行随即进池、池贴近上限，下次关闭会再触发。(c) 暂不处置：本项保持 `DONE`/`ACTIVE`，占 1 条零消耗轨道。

`DONE` 时未闭条目（移行前列于状态板 Current state，移行时随行移入 `docs/parked-status.md`「已终止（ENDED）」表下注）：A9 30 天报告与 A10 扫描（不设门）；两类信封首签与「启用 supervisor 无人值守」条目（用户）；R2-1 记债；复核注记 R1 §3、R2 §3（首次真实启用前裁定被拉起角色能否 amend 并 `--force-with-lease`；信封块避免 ASCII 键非机读行；A5① 若重跑按 BC-14 写节；`D10 is not D1` 子用例断言收紧）。本轮未跑测试、未改实现、未写 `docs/reviews/*`。

### R1@落地 复判（2026-09-26；接受角色，Claude Code `/accept` 备用运行地，用户直接指挥，零消耗）

- `docs/reviews/COORD-015.md` / R1@落地 / R1-1（CLASS_1，依据 `BC-12`）：维持 CLASS_1，**范围内必修**（非 `SCOPE_GAP`：合同点名、可达且改结论）；归因 = 实现错误（依据列 `BC-12` 机械派生）；2026-09-26。BC-12 未写明节绑定，落点由 BC-14（`CLARIFY`）固定，协调批次逐字实现。两条具名回归测试的 fixture 与真实提案同布局：`### D<n>` 最新在上，其上另有一个含 `open_items: none` 的非 D 节（如 `### 接受后修订 1 审核`）；increase_rejected 以 r(1)=2、r(2)=4、条目按文件序 now=2/prev=4 构造。相对复核建议的调整：「取节内最后一条」与「多于一条即失败关闭」合并为「恰好 1 行且为节末」；节止于下一 `#{1,3}` 标题，残留子节须写 `####`（本提案 D1/D2 裁定节的同级 `### AR…` 写法会截断节末，存量不回填）；标题匹配加非字母数字边界，防 `D1`/`D10` 混淆。
- R1-2、R1-3（CLASS_2，`BC-5`）与 R1-5（CLASS_3）：不逐条复判（COORD-008 S2），由协调批次按复核文件修复，直接回 `R2@落地`；2026-09-26。
- R1-4（CLASS_2，`IN_SCOPE_NO_BC`）：同上路由，不逐条复判；为使 R2 有可核条款加 BC-15（`CLARIFY`，引用 BC-5 与 §5.4 相邻条款）。不是 `NEW_OBLIGATION`：来源为复核 `IN_SCOPE_NO_BC`，不是实现「待裁定」或 `SCOPE_GAP`（acceptance.md 来源限制），且该义务已写在落地的 `AGENTS.md`「共享状态更新」与账本文件头；本 work ID `NEW_OBLIGATION` 计数仍为 0。最终归因在通过轮按依据列机械派生；2026-09-26。
- 本轮未跑测试、未改实现、未写 `docs/reviews/*`。

## Codex review decision

### 接受后修订 3 审核（2026-09-25；不新增 D 轮）

Decision: CONFIRMED_WITH_BC-13。保持 D6 `ACCEPTED`、研究轨道与设计退修累计 2；本轮是用户指示的 CLI 去绑定确认，C/R 未开。
账本同日「用户指示修订 3」逐字要求不指定任何模型及 CLI；「提案记录移至新文件」要求正式设计和角色细则的合同指针改指新路径。已核对修订 3 相对修订 2 的提案 diff、§2.1/§7/§13、BC-9/10/13 与 §7 对应句清单。

| 核对项 | 裁定与依据 |
|---|---|
| 运行地与合同 | 确认本机（用户当前工作机）CLI 会话，CLI 与模型由用户当轮选择、可更换；BC-13 就地解释 BC-9/10，保留 A4/A5/A7 对实际选定入口、接力及派发的实测要求。 |
| 落地边界 | §7 清单只改 supervisor 对应句及角色细则设计指针；其他角色池、U4 检查节奏与 U1–U9 其余选择不变。CLI 下载/A6、两类信封及首次启用仍待单独授权。 |
| 正文预算 | 「Codex review decision」前实测 551 行，比修订 2 的 550 行多一条回应索引；接受自报预算 551 行，未触及 workflow 的 600 行提示线。 |

Handoff: 用户直接指挥的协调批次按 §7 清单及账本修订 3 同步基础设施对应句与 changelog 索引；本接受批次仅同步提案、正式设计和状态板。无测试、代码、下载或消耗；不恢复暂停项。
open_items: none

### 接受后修订 2 审核（2026-09-25；不新增 D 轮）

Decision: CONFIRMED_WITH_BC-13。保持 D6 `ACCEPTED`、研究轨道与设计退修累计 2；本轮是用户指示修订的合同确认，C/R 未开。
依据为账本同日「用户指示修订 2」及「用户指示修订 2 补充」原话；已读取本次提案 diff、§2/§3/§7/§9–13、BC-1…12 和直接受影响的角色/入口句。

| 核对项 | 裁定与依据 |
|---|---|
| 运行地与模型 | 确认 §2.1/§7 的本机 Kimi Code CLI、当轮选模型且可更换；不绑定硬件。§13 U4 第 4 项旧模型二选一与第 0 项冲突，按用户原话就地同步，BC-13 明示旧选项失效。 |
| 权限与其余角色 | §2.3 写权、§3 单写者/核销、BC-1…12、其余角色池与 U1–U9 其余选择保持；A9 模型调整交用户，符合 §2.1 自身利害事项直达用户。 |
| 落地范围与可执行性 | §7 四份规则/入口文件对应句及 changelog 索引可交协调批次同步。运行地决定不证明接力可用：入口路径只是提示工件，实际发令端仍须按 A4/A5/A7 取证，A6 保持；BC-13 仅解释 BC-9/10，不新增验收项或消耗额度。 |
| 正文预算 | 实测修订前「Codex review decision」之前为 549 行；525 是 BC 标题行号，不能作为正文行数。计入 BC-13 后 550 行，本提案自报预算由 520 调为 550；保留裁定原文，不改工作流基础设施或状态板上限。 |

§9.2 首批文档与工具已按同日协调授权落地，不再笼统写“落地待授权”；本次修订对应句尚待协调批次同步。CLI 下载/A6、两类信封首签、首次启用与真实派发仍未授权；现有工具未在本轮做候选核对或独立复核，A4–A10 的已有未闭义务保持，A9 仍不设门。
Handoff: 用户直接指挥的协调会话按账本修订 2 及补充范围同步 §7 对应句，提交引用授权条目；本接受会话只改提案、正式设计边界和状态板。无测试、代码、下载或消耗；不恢复暂停项。
open_items: none

### 接受后修订 1 审核（2026-09-25；不新增 D 轮）

Decision: CONFIRMED_WITH_BC-12。原 D6 `ACCEPTED` 不重签，设计退修仍累计 2，C/R 未开。
用户逐字「改成第二种」的授权见账本同日「用户指示 D1 收敛判据」；本次只确认该已接受设计的指示修订，不授权协调落地或签封。

§5.1/§5.4 已把 D1 改为相邻裁定轮残留数严格递减、每轮一次及缺行/持平回用户；§5.7、§8、§9.3、A2/A5①也随之调整。
审核发现 §9.2 写“第 2 次退修起”才记录 `open_items:`，但 D2 首次可代拍时必须读取 D1 基线；A5①已按 D1 写行演练。BC-12 字面澄清为首次退修起写，且固定互异 ID 与代拍时的已提交提案快照，使计数可机检、旧条目不被后续编辑改判。
BC-4 原行保留；BC-12 标 `CLARIFY` 并引用 BC-4，不把此次用户指示误记为实现期自查产生的 `NEW_OBLIGATION`。
未来实现须按 A2/A5① 和 BC-12 覆盖首次 D1 基线、缺行、重复 ID、持平、同轮第二条与后续提案编辑后的历史复判。本轮仅作合同判断，未运行测试或修改基础设施。
Handoff: 用户决定是否另行授权 §9.2/§12 协调落地与 Codex CLI 下载/安装；§13 U1–U9、两类信封与首次启用仍需各自用户原话。现行流程继续生效。

### D6 接受侧裁定（2026-09-25）

Decision: ACCEPTED。Track: 研究轨道（头部无 `Workflow: engineering-v1`）；设计退修累计 2，C/R 未开。
用户对 D5 残留选择 (a) 的原话见账本同日「用户处置 D5 审查残留 AD5-1」；本轮只作设计接受，不把该授权扩大为落地、下载安装或信封签发。

AD5-1 已闭合：§5.6 删除提交主题作为 X 的独立条件，X 只看状态板 (i)(ii)；带路径过滤的首父历史查询遂覆盖全部到期事实。
预提交使用 HEAD 和暂存状态板模拟本次提交，同一提交到期即拒绝；A2 增三例分别覆盖主题命中但状态未到期、纯主题提交、同提交 SUB 与到期。
主题只在运行时守卫作异常提示，§3.6(i)/A5⑤明确停下，不改变旧账本条目的合法性；§9.2 不需 commit-msg hook。
已核对 D6 相对 D5 的提案、账本及状态板改动；D1–D5 的已闭合裁定保持，其他 §3–§13 条款继续受 BC-1…11 约束。

Accepted design-document changes: 该提案只调整协作设施，不改运行时协议、指标或里程碑；正式设计 §1 同步“已接受但未落地”的边界。
未运行测试、未签独立复核，§10 A1–A10 与 BC 的证明方式留给获授权后的实现候选。`UNITY_NA` 仍须独立复核附议，不能由本轮设计接受替代。
A9 是落地后 30 天报告且明确不设门，不作为本次 BC 或启用/DONE 前置。
Handoff: 用户另行决定是否授权 COORD-015 协调落地、Codex CLI 下载/安装及 §13 U1–U9；如获授权，由授权会话逐字入账后按 §12 执行，首次启用和两类信封各需单独用户原话。现行角色/工具规则继续生效。

### D5 接受侧裁定（2026-09-25）

**尚不能 `ACCEPTED`；仅 AD5-1 残留，交用户处置，不签发第三次 `REVISION_REQUESTED`。**
Owner: Acceptance / Codex。Track: 研究轨道；设计退修累计 2，C/R 未开。
账本同日「用户处置 D4 审查残留 AD4-1/2」已执行为 D5 修订与本轮审查，不延伸为下一设计轮或落地授权。
本轮读取 D5 正文、验收、附录、D1–D4 裁定及 D5 修改，核对现行角色/工作流、正式设计 §1 与相关授权。
这是提案决策；不运行测试、不复算历史统计、不签独立复核。以下判断是条款推演，不声称已运行未来的 A2/A5。

| D4 残留 | D5 审查结论 | 依据与保留范围 |
|---|---|---|
| AD4-1 | 具名启动缺口已闭合 | §3.3 全局去重覆盖未终结 requested；launch_failed 受“已证明未创建运行者”的前提约束，不能把一般报错当证明。§3.4/3.5 为裸 requested/unknown 定义结束凭据及 requested_at/base_head 基线；A5⑥丁/戊覆盖旧写者仍活跃与启动结果未知。 |
| AD4-2 | 签发初态与暂存首父已补齐，判定等价仍未闭合 | §5.6 已检查 S、分开新旧信封、用 HEAD/暂存树解释待提交条目；但提交主题条件 (ii) 与预提交视图及历史查询集合不一致，见 AD5-1。 |

AD3-3/4 在 D4 闭合的具名问题保持闭合；收益仍是有条件的历史样本分类，不是已实测节省次数。

#### AD5-1 — 事件型到期的提交集合与提交前后判定不一致（承接 AD4-2）

§5.6 将“提交主题匹配 `^<work_id> [CR]\d+@<停点>`”列为独立到期条件 (ii)，却在预提交视图明确“不查 (ii)”，随后断言两视图相同。
首父与暂存状态板相同只能证明 (i)(iii) 相同，不能证明未检查的提交主题条件相同。两条具体路径：

1. 现有信封未到期，待提交 E 新增 SUB 条目、precheck_head = HEAD，并改状态板的非到期内容（如 Log）；状态仍 ACTIVE，交接不匹配 (i)。
   若该提交主题匹配 (ii)，pre-commit 按现文通过；提交后 E 会进入带状态板路径过滤的历史查询，X = commit(E)，历史谓词却拒绝。
   这没有绕过 hook，不能归入 `--no-verify` 后补判；也不符合 §5.4 的非法新条目拒绝提交与 A2 的前后等价要求。
2. 信封签发后出现主题匹配 (ii)、但不修改状态板的提交 X。现文的 `git log ... -- docs/current-status.md` 不枚举 X，
   后续 E 与派发守卫都可能继续得到“X 不存在”；仅增加 S 初态检查不能覆盖这个签发后的路径。

修正只限 §5.6、与之相连的 §9.2 hook 清单及 A2：统一到期事实源和被枚举的提交集合，使每个声明有效的到期条件都能在拒绝提交前判定。
可将 (ii) 改为非权威提示、以明确的状态板事件为准；若保留主题作为独立到期事实，则须定义提交消息可得的提交前检查和不漏主题事件的历史枚举。
由构思角色选择并同步正文与验收，不由实现临场补协议。A2 覆盖上述“主题命中、状态未到期”及“主题命中、不改状态板”两例，
明确按所选语义应通过还是拒绝，并验证提交前后结论一致；原有合法首次入账、S 初态拒绝、旧合法条目不追溯失效与到期不复活继续保留。
这是一处既有到期机检的未闭语义，不新增代拍类别、资源范围或 BC，也不重开已闭合的启动设计。

Accepted design-document changes: 无；未接受，不修改正式设计或里程碑证据，不提前冻结 BC。
全局 check_docs 通过（完整轨道/Gate-echo/blocks/releases 来源）；当前 0 条消耗性、1 条零消耗活跃交接。
Handoff: 用户按 workflow §4.2 选择 (a) 保留范围与已闭合修正，仅交构思修正 AD5-1 后再审（推荐），或 (b) 关闭为负结果记录。
用户答复前不派发下一设计轮；U1–U9、落地/下载、签封与启用仍归用户，暂停项不恢复。

User disposition（2026-09-25）：用户逐字选 "(a) 修正 AD5-1 出 D6（推荐）"（本构思会话 AskUserQuestion 选项标签；构思开工时先只读分析 AD5-1 并给出修正方向），已记入账本同日「用户处置 D5 审查残留 AD5-1」条目；构思据此修正后提交 D6 交接受角色再审。退修累计 2 不重置；尚未 ACCEPTED，U1–U9、落地/下载与信封仍未授权。

### D4 接受侧裁定（2026-09-25）

**尚不能 `ACCEPTED`；残留收敛为 AD4-1/2，交用户处置，不签发第三次 `REVISION_REQUESTED`。**
Owner: Acceptance / Codex。Track: 研究轨道；设计退修累计 2，C/R 未开。
用户对 D3 残留的 (a) 已执行为 D4 修订与本轮审查，不代表落地或继续下一设计轮的授权。
本轮完整读取 D4 正文、验收与附录，沿用未变的 D1–D3 裁定、角色/工作流及正式设计 §1；新增授权已核对。
这是提案决策，不是候选核对或独立复核；未运行测试、未复跑附录 A，未写实现或 infra。

| D3 残留 | D4 审查结论 | 依据与保留范围 |
|---|---|---|
| AD3-1 | 报告来源已闭合，启动恢复尚有残留 | §4 已分磁盘项与报告项，无报告时 N/A 不再冒充核验；§3.4 普通结束路径已有凭据。§3.3 的启动缺口仍可释放未知写者，见 AD4-1。 |
| AD3-2 | 历史旧快照反例已修，提交前语义未闭合 | §5.6 的首父绑定可拒绝 P→X→E 旧快照；但拟挂 pre-commit 的检查依赖尚不存在的 commit(E)，签发边界也漏查 S 本身，见 AD4-2。 |
| AD3-3 | 前轮具名矛盾已解决 | §4 F3b、适用矩阵和 A3/A7 同步列入构思/实现合法推进与越权 Lifecycle 反例；保留其现行角色边界，不据此签发任何实际候选通过。 |
| AD3-4 | 前轮具名混合样本问题已解决 | §8 已将 #85/#86/#13/#14 移出确定收益，撤回 9–10/13–14，附录 A 补输出。5/7/9 只按所列未来启用前提作历史样本分类，不作为已实测节省次数；本轮不作统计复算认证。 |

以下仅为原启动恢复与到期机检的未闭路径，不追加新的工作范围或 BC。

#### AD4-1 — 启动登记缺口与 launch_failed 不能释放未知写者（承接 AD3-1）

§3.3 的顺序是 requested→启动→started，但全局去重只拦已有 started 的派发。若启动已经发生、supervisor 在写 started 前退出，
磁盘只有 requested；§3.5 虽要求逐条对账，却未定义这种没有 runner_id/started_at 的请求怎样保持占用，不能直接套 pid_gone 或已知子代理 id 的 stop_call。
更直接的冲突是“调用报错或未返回 id”进入 aborted(launch_failed)，而“调用超时或结果不明”进入 unknown；未返回 id 本身不能区分启动失败与启动结果丢失。
当前 launch_failed 豁免 end_confirmed，加上干净树、无提交、零消耗即可重派，仍可能在旧角色尚未写文件时启动第二写者。

修正落点限 §3.2–3.5/A5：未终结的 requested 也阻止新派发；只有可证明未创建运行者的启动拒绝才可记 launch_failed 并重试。
未返回身份、超时、启动后登记前中断统一保留为未确认状态；无法取得结束或未启动证明就停下，不能凭干净树释放。
明确该分支用何种请求时刻/基线核对提交和消耗，不能引用不存在的 started_at。A5 补“只有 requested、旧写者仍活跃”和“无 id 但启动结果未知”，
两者都应阻止另一 work ID 的派发；已证实未启动的零消耗失败仍可保留一次重试。

#### AD4-2 — 账本检查需区分待提交状态与历史提交（承接 AD3-2）

§9.2 要在 pre-commit 运行 check_ledger，§5.4 又要求不合法新条目拒绝提交；但 §5.6 只定义了已提交条目的 commit(E) 和信封首次提交 S。
首次提交合法 SUB 条目时，hook 运行期间 commit(E) 尚不存在，无法按字面解析其首父或祖先关系；首次写入信封时 S 同样不存在。
若缺失就拒绝，合法条目无法首次入账；若跳过未提交条目，则本次最需要阻止的错误反而没有受检。仅对提交后的合成历史做 A2 不能证明 hook 可用。

应明确：历史条目用其首次提交；待提交条目用当前 HEAD 与暂存树作为预提交视图，定义与提交后首父谓词等价的判定，
同时覆盖本次暂存的账本与状态板，区分未暂存差异；不能为取得 commit(E) 先放行提交。A2 增加真实 pre-commit 路径的合法首次入账通过与非法首次入账拒绝。

另，解析器只遍历 S..HEAD，未检查 S 时的状态：若签发当时已在到期停点或 PAUSED，随后仅追加 E 而没有状态板提交，X 仍可为空。
应定义签发时的初始状态检查及新旧信封各自的搜索边界；不能以“签发后无状态板变化”证明尚未到期。该反例沿 A2 验证，
仍保留“真实 E 先于 X 的旧条目不因后来到期而失效”和“同一信封到期后不复活”。

Accepted design-document changes: 无；不修改运行时设计或里程碑证据，不提前冻结 BC。
全局 check_docs 通过（完整轨道/Gate-echo/blocks/releases 来源）；当前 0 条消耗性、1 条零消耗活跃交接。
Handoff: 用户按 workflow §4.2 选择 (a) 保留范围与已闭合修正，仅交构思修正 AD4-1/2 后再审（推荐），或 (b) 关闭为负结果记录。
用户答复前不派发下一设计轮；U1–U9、落地/下载、签封与启用仍归用户，暂停项不恢复。

User disposition（2026-09-25）：用户逐字答复“选A”（构思会话纯文本消息；用户先要求「查看一下accept的D4，先分析一下」，构思只读分析后建议 (a)），已记入账本同日「用户处置 D4 审查残留 AD4-1/2」条目；构思据此修正后提交 D5 交接受角色再审。退修累计 2 不重置；尚未 ACCEPTED，U1–U9、落地/下载与信封仍未授权。

### D3 接受侧裁定（2026-09-25）

**尚不能 `ACCEPTED`，上交用户处置；不签发第三次 `REVISION_REQUESTED`。**
Owner: Acceptance / Codex。Track: 研究轨道（未申请 engineering-v1）。设计退修累计仍为 2，C/R 未开。
账本同日「用户处置第二次设计退修」的 A 已执行为构思修正并提交 D3；不将其解释为自动接受或无限次继续修订。
本轮完整读 D3、D1/D2 裁定、现行角色/工作流与正式设计 §1，并回查 §8 候选样本的授权原条目；不跑测试、不作独立复核。

| D2 要求 | D3 审查结论 | 保留的修正与残留 |
|---|---|---|
| AR2-1 | 部分闭合 | 提交尾注、远端可达、reconciled.candidate、无候选即停与全局未闭派发检查可保留；报告丢失核查与启动/退出确认仍未闭合，见 AD3-1。 |
| AR2-2 | 部分闭合 | 同日签发/代拍/撤销用同一顺序、独立 request_id、SUB 无否决窗口已明确；事件失效来源和快照时效仍可放过过期申请，见 AD3-2。 |
| AR2-3 | 部分闭合 | F7/U9 默认禁用、F3a/F8 分离两类身份、N/A 分列、报告指针化及具名夹具路径可保留；F3b 的权限与矩阵矛盾仍阻断正常推进，见 AD3-3。 |
| AR2-4 | 部分闭合 | 已剔除前轮点名的范围变更、重复 D1 与合同选项；成功链段目标也已限定。但 9–10/13–14 仍非逐条证明的可消除打断数，见 AD3-4；附录 A 只有脚本、无原始输出，本轮未复算切换基线。 |

下列是用户处置的具名残留，不是新 BC、独立复核 finding 或已授权的第三次退修。

#### AD3-1 — 报告丢失核查与运行者生命周期仍缺可执行来源（AR2-1/3）

§3.4-2 要在报告缺失时完成 §4；F3a、F8 却仍必须比较报告的 handoff/this_round，F4 也引用报告 claims。
§3.2 的持久字段只有派发 round 与提交尾注，没有最终报告这些字段或缺报告时的替代取值规则；适用矩阵又把这些项列为必查、缺证据即失败。
因此 A5③ 仍会停在核查，不能走到声称的 reconciled→C→R；仅把 F1/F2 改为持久凭据未闭合整条链。
应逐项点明无报告时 F3a/F4/F5/F6/F8 的独立来源与比较对象，或把不可重建的部分明确记 N/A 并保留必要事实核验，不能以读取同一行两遍代替核验。

§3.3 要先写含 runner_id 的 started 再启动，未说明启动前无法取得子代理 id/pid 时怎样登记；§3.5 又以「本会话重启」作为旧子代理已结束的证明。
除非运行地保证并可核验重启必终止旧子代理，否则这不足以排除旧写者仍在运行。§3.4-2 对“已有提交但运行者尚未确认结束”也未设等待条件。
应明确 requested 后启动失败/身份未回写的恢复分支，以及 finished/reconciled/aborted 前的结束凭据；无法确认就保持未闭并停下，不能释放全局单写者。
沿 A5③/⑥ 覆盖“提交已出现但进程仍活跃”和“重启后旧运行者状态未知”，不另建通用并发平台。

#### AD3-2 — 首次失效查询和祖先条件不能证明代拍时仍有效（AR2-2）

§5.6 给出的 `git log --reverse -S'<work_id>…C1@K4'` 搜索的是含省略号的连续字面串，不能据此解析状态板中分处不同单元格的 work ID 与停点；
到期值允许停点短名，查询却固定 C1@K4，也未把首次事件的搜索区间绑定到被引信封的签发。文字说明“同样检查 Lifecycle”尚未定义相应行的状态迁移取法。
应按该 work ID、信封签发边界及 expires_at 指定事件解析历史状态迁移，明确首次失效提交的选择；不能以未命中字面串推出从未到期。

即使已正确得到失效提交 X，现条件也会放过线性历史 `P → X → E`：取旧 P 为 precheck_head，P 是记录 E 的祖先且不是 X 的后代，
两个条件都满足，但到 E 时失效已发生。每次口头要求“重新判定”不能弥补 A2 机检谓词的这个反例。
需把快照绑定到本次代拍前的实际最新状态，并检查其后至 E 的相关迁移；历史合法性与当前派发守卫分别明确。
A2 应拒绝上述旧快照例，仍通过真正发生在 X 之前的旧代拍；到期→恢复→再申请不得复活同一信封。

#### AD3-3 — F3b 同时存在误退和漏检（AR2-3）

§4 F3b 规定 Overall/Lifecycle 变化只能来自接受角色，矩阵却把构思/实现/复核标 N/A（“无权改 Gate”），反例又要求构思改 Overall 必失败。
按矩阵执行会跳过该反例；按正文执行则会误退 workflow §4.1/§4.3 与 implementation.md「职责」明确允许的 PROPOSED、IMPLEMENTING、IMPLEMENTED 状态推进。
AGENTS 将 Lifecycle 交接受角色或用户维护，不等于把每个角色在现行流程下记录的全部状态事实也收归接受。
应分开 Lifecycle 与各角色可记录的状态字段/迁移，按现行规则列出核验对象，并统一矩阵与反例；不得借非权威核查暗改角色门权限。
A3/A7 同时给出实现合法推进与越权改 Lifecycle 的相反例；F3a 已修好的正常换角色例继续保留。

#### AD3-4 — 收益计数仍混合“可代拍部分”和“整条无需用户”（AR2-4）

§8 的 #13（账本 2026-09-20 COORD-012「用户指示推送全部提交，并同意把 COORD-012 整组 Log 条目移入 status-history」）
明确包含 CLOSED_BY_USER、Lifecycle=ENDED 和停止 N4；其原话为用户自发指令。即使其中归档或推送部分可交现有角色执行，整条仍含 LIFE，
不能计入“全启用即可少打断”的 D3/D6 样本。#14（同日「同意 chore 把 Log 可压池 8 个 work item 组…」）的原文还明确包含未闭义务、
部分获同意组最终未移入；不能把整组申请算作符合 §5.1 D3“组内含未闭义务即回用户”的样本。

默认 9 条中的 #85（2026-08-21 BODY「--compare 的放行次序」）明确尚未授权 compare，之后仍须用户另签；#86（2026-08-20「B5 之前先走一轮独立复核」）
明确是新增一道放行前置。二者不能仅凭“排序”标签证明符合 D4“已签信封内、已列步骤、不新增步骤”，需区分可代拍的次序部分与仍需用户的授权/前置改变。
这些是授权文本分类，未重审任何历史运行结论。保留原统计文件和历史授权；将未证明样本排除或仅列潜在上界，别以默认 9–10、全启用 13–14 冒充合规净收益。
主价值仍是接力调度；本项无需承诺具体收益才可继续，但须撤回不成立的已证明口径。附录 A 原始输出待落地实测的限制保留。

Accepted design-document changes: 无；本项尚未接受，不修改运行时设计或里程碑证据。
全局机检覆盖完整复核 blocks/releases 与账本 release 来源，当前通过；0 条消耗性、1 条零消耗活跃交接，暂停项不恢复。
Handoff: 用户按 workflow §4.2 选择 (a) 保留范围与已有效修正，以 AD3-1…4 为具名残留交构思继续修正后再审（推荐）；
或 (b) 关闭为负结果记录（不是 DONE）。用户答复前不派发下一设计轮；U1–U9、落地/下载、两种信封与启用仍待原有授权路径。

User disposition（2026-09-25）：用户逐字答复“(a) 修正 AD3-1…4 出 D4（推荐）”（构思会话 AskUserQuestion 选项标签），已记入账本同日「用户处置 D3 审查残留 AD3-1…4」条目；构思据此修正后提交 D4 交接受角色再审。退修累计 2 不重置；尚未 ACCEPTED，U1–U9、落地/下载与信封仍未授权。

### D2 历史裁定（保留原文；当前交接以上述 D3 裁定为准）

Decision: REVISION_REQUESTED
Round: D2（2026-09-25，Acceptance / Codex；设计退修累计 2，C/R 均未开）
Track: 研究轨道；本轮只作提案决策，不签独立复核、BC 或落地授权。

Rationale: 调度与事实核查方向保留；D2 的分类、隔离演练和用户选项已有改善，但恢复链、授权时序、核查适用及收益依据仍不能按字面执行。以下 AR2-1…4 为具名残留，不是已生效合同或复核 finding。

| D1 要求 | D2 审查结论 | 依据与剩余范围 |
|---|---|---|
| AR1-1 | 部分解决 | 全局串行、登记与去重已写；报告丢失与候选恢复未闭合，见 AR2-1。 |
| AR1-2 | 部分解决 | F2 已绑定远端可达性，F9 已区分两类 SHA；凭据丢失、F3/F7/F8 仍冲突，见 AR2-1/3。 |
| AR1-3 | 部分解决 | D/SUB 引用分开、累计含否决已有定义；同日撤销、事件到期与重试未闭合，见 AR2-2。 |
| AR1-4 | 已解决设计边界 | §2.1/2.5/5.1/5.2 已约束作者、D1(b)、禁项优先及直达；D2a/b、D3 仍须用户明选。 |
| AR1-5 | 部分解决 | hook、测试与外部入口已补；§12 第 6 步的夹具生成脚本仍无 §9.2 具名路径，F7/U9 边界见 AR2-3。 |
| AR1-6 | 部分解决 | A5/A7 改合成夹具、A8 拆分、安装回退和签封次序已明确；A5 报告丢失段与核查接口见 AR2-1/3。 |
| AR1-7 | 未闭合 | 已收窄预测并去掉下载/Play 样本，但 17/137 仍包含不可代拍项，见 AR2-4；切换统计脚本/原始输出尚未入库，不视为已复算证据。 |
| AR1-8 | 已解决选项形态 | §13 给有限选项与未选分支；不据此代替用户签封、授权落地或批准例外。 |

### AR2-1 — 报告丢失与复核候选的恢复链（§3.2–3.7、§4 F1/F2/F9、A5）

§3.4 要报告丢失时做 §4 后写 `reconciled`，但 F1/F2 又把报告中的 `checks`/`push_receipt` 缺失判失败，A5 因而不能按现文成功恢复；`reconciled` 只列原因，§3.7/F9 却只从 `finished.commits[-1]` 取候选，恢复成功的实现派发没有该来源。需定义可持久核验的替代凭据、恢复核销的候选字段与唯一解析顺序；无可证明候选时停下，不能退取更早实现。给出“实现提交后报告丢失→核对→复核”的完整合成例。重启对账还须先确认旧子任务/进程已结束，不能把“暂时无提交且工作树干净”当成零消耗角色已退出而重派；§3.3 的去重检查应覆盖全局未闭派发，与 §3.1 一致。

### AR2-2 — 授权时间与到期必须使用同一可复算顺序（§5.4–5.6、A2）

§5.5 虽定义同日位置顺序，历史合法公式却用“不存在日期 ≤ E 的撤销”：上午合法代拍、下午撤销会使上午条目也失败；同日先代拍后签封也未被日期比较排除。需统一按事件全序比较签发、代拍、撤销，并给这两种反例。§5.6 定义“首次出现 C1@K4/暂停/终止即失效”，却只看当前或 `precheck_head` 单个状态板快照；恢复后或进入后续轮次可不再有该 token，旧信封不能因此复活。需可追溯的首次失效来源，验证引用快照确为代拍前状态；补到期→恢复→再次申请仍拒绝。§3.4/3.6 重派用新 dispatch_id，§5.6 却按同一 dispatch_id 复用，需独立稳定的申请/追加身份；SUB 必填 `veto_until` 的来源也须定义（执行信封块没有否决窗口），不得借用未引用的决策信封。

### AR2-3 — 默认核查不能误退合法交接或暗改写入审计（§3.8、§4、§9.2、A3/A4/A5）

F7 逐提交做路径白名单归因并以失败退回，实质仍是默认强制的提交后写入检查；称“只读、非归因”不能消除与 workflow §7.7 的冲突，U9 未选也不关闭 F7。需保留提交前凭据核验，或将此机制完整列入用户待选变更。F3 要逐字段比较 Owner/Status/Progress，但报告未定义后两者；F8 要提交轮次与交接行一致，正常“接受 D1 提交→构思 D2 下一动作”本就不同。需分开本次派发身份与下一交接身份，补正常换角色/换轮次通过例；A5/A7 按适用矩阵验收，不能把 N/A 当作实际核验通过。§3.8 还需给必填内容超过 600 B 的指针化规则；§9.2 补夹具生成脚本具名路径。以上是已有核查与演练要求的可执行化，不扩成通用调度平台。

### AR2-4 — 17/137 不能继续称合规代拍子集（§1 F3、§8）

按 CSV 的“序号”列回查原账本：#51（2026-09-08 ASSET）主动删除重放实验，#46（2026-09-12 SFT-001）拆成两项，都是明确范围变更，超出 D1；#27 是 LOOP 同项在 #28 之后再次选择继续，超过每提案 D1 一次；#95（2026-08-13 BODY G1/G2）授权协议/准入判据与替代 ID，#96 是同一含合同改动选项集的暂缓答复，按 D5 禁项应整题回用户。仅剔除这五条，原 17 条至多余 12 条，尚非其余样本全数合规认证。需按允许动作、禁项和次数键逐条重算，混合条目保留必要用户介入，不为维持预测放宽权限；统计原件与历史授权不改写。

Accepted design-document changes: 无；已读正式设计 §1，本轮不改运行时设计或里程碑证据。全局未发现有效未配对的消耗性 block；当前 0 条消耗性、1 条零消耗活跃交接，暂停项不恢复。
Handoff: 交用户按 workflow §4.2 二选一：(a) 接受保留当前提案范围，并以 AR2-1…4 为已知缺口交构思修正后再审（推荐；不等于 ACCEPTED 或授权落地）；(b) 关闭为负结果记录。未答前不自行启动第三次设计退修；U1–U9、落地/下载与两种信封仍未获本轮授权。

User disposition（2026-09-25）：用户逐字答复“A”，已记入账本同日「用户处置第二次设计退修」条目；上条待用户交接已完成，当前交构思修正 AR2-1…4 后提交 D3。退修累计 2 不重置；尚未 ACCEPTED，U1–U9、落地/下载与信封仍未授权。

### D1 历史裁定（保留原文；下述交接已由 D2 取代）

Decision: REVISION_REQUESTED
Round: D1（2026-09-25，Acceptance / Codex；首次设计退修，未开 C/R 轮）
Track: 研究轨道（头部无 `Workflow: engineering-v1`；不因题材为流程工程而换轨）。

Rationale: 接力调度与事实核查符合账本同日用户目标，池重分配和有界代拍可以继续设计；但当前协议仍有重复派发、
授权判定与验收自相矛盾，不能按字面交付。此次为提案决策，不是候选核对或独立复核；下列为设计修订要求，
不是复核 finding 或已生效 BC。落地授权、决策信封、子额度均未签发；现行流程继续有效。

Required revisions（AR1-1…8；构思角色逐项回应后交 D2）：

### AR1-1 — 补齐调度的唯一执行与中断恢复语义（§3）

§3.1 在每次唤醒扫描未暂停行，§3.3 报告只有完成结果；未定义运行中登记、重复回调去重、退出前已提交/已消耗的恢复。
按 work ID 串行也不能隔离不同工作项共同修改的状态板、账本和 Git index；§3.5 的“异常 2 次”未说明重试可否重复消耗。
D2 明定派发身份与运行状态的事实源、启动前登记、完成核销、重启后对账及用户暂停后的处置；状态不明先停，不能盲目重跑。
首版可选全局一次只运行一个写仓库的角色，不必建设通用并发系统；若保留并发须说明共享文件与提交互斥。
复核要明确新鲜上下文及候选绑定：§3.2 的 Agent worktree 与 `review.md` 自建候选副本如何衔接、报告如何回主树、由谁提交，不能仅靠同一父会话下“不同子代理”推定独立。
补派发重复、提交后报告丢失、用户暂停、未知消耗四种演练及预期结果；禁止恢复现有暂停项作演练。

### AR1-2 — F1–F10 要核查确定对象，不能误判或暗改机制（§4）

F1 重新对已提交批次做强制写入归因，与 workflow §4.3.1/§7.7“已提交批次不做机械检查”相反；
`tools/check_role_writes.py::changed_paths_from_base` 实际查 `<base>..HEAD`，若 base 取被查提交本身则该提交不在范围。
明确保留提交前检查、提交后仅核验凭据，或把恢复提交后归因列为待授权机制变更；定义批次起止与协调批次/infra-fix 适用分支。
F2 的本地 HEAD=origin/main 不证明报告 commit 已上远端（远端跟踪引用可旧）；需绑定报告提交并给出推送收据或远端可达性依据。
F9 区分被复核候选与复核报告提交，不能把二者的 SHA 混用。给 F1–F10 按角色/轮次的适用与 N/A 理由矩阵，
证据缺失不得当通过；说明 ≤2 KB 报告超长时如何保留必要字段与工件指针。以具体反例代替只有 grep 存在性的验收。

### AR1-3 — 信封机检缺少可执行的时间、撤销与 SUB 规则（§5.1/5.2/5.4）

§5.4 要每条代拍的类属于被引信封 `classes`，但执行信封子额度块没有 `classes`，决策信封闭集也没有 SUB。
须分开定义两类引用、work item/阶段/停点绑定与必填字段；未知键、负数、非有限值、缺字段、重复条目及串用他项信封均失败关闭。
补“历史合法性”与“现在还能否执行”的区别：全账本不能因后来到期而把合法旧记录判错，也不能让后来 `enabled: false`
失去效力。定义事件排序、撤销引用、累计口径、否决后实耗不返还、重试不重复批准与执行前再检查。
`expires_at: K4` 仅交核对轮事后核验无法保护之后的新派发；明确哪个 work item 的哪一停点事件使其失效及执行前检查来源。
否决可以停止未执行动作，但不能回滚已花费用、已用查询或已发生的外部效果；分别写清可撤回动作与不可逆实耗的处理。
A2 增补上述失败分支的样例，区分机检与人工/接受侧职责，不要求本轮实现工具。

### AR1-4 — 代拍闭集与权限声明须消除重叠（§2/§5/§9.1）

D1 选 (b) 是关闭负结果，与 §5.3 LIFE/CLOSED_* 永不代拍冲突；D2 同会话例外及超限返工本就改变现行独立性/轮次规则，
不能同时声称 §9.1“核对轮/复核轮规则不变”。D5 的暂缓、不重抽与 D6 的归档也可能触及暂停、合同或 D3。
逐类写触发、允许动作、禁项优先级、执行角色与计数键；D2 两种例外如保留须分别限定条件、不得替代 verdict 或解除 block。
列出明确被替换的常驻规则及对应待用户批准选项；未选择的例外按禁用处理。解释 supervisor 起草 COORD 与
§2.1“不是任何提案作者”的矛盾；自己的提案和自身利害事项不能靠委托子代理绕过回用户的边界。
“其余直达用户”可经 supervisor 原样展示和代录，但不应增加一层实质审批；在协议中明确这一点。

### AR1-5 — 落地文件闭集不完整（§9.2、A1/A3/A4）

§5.4 声明 pre-commit 并列运行新机检，但 §9.2 漏 `tools/githooks/pre-commit`；现文件以 `exec python3 tools/check_docs.py` 结束，
不能在其后简单追加。A1 需要新增 `tests/test_check_role_writes.py` 用例，该文件也未入闭集；
`.claude/commands/codex.md` 仍写实现主地 Cursor/Claude 备用，池同步表未包括它。
按现文件补齐清单；A3 改成具名条款到新语义的映射，避免全局替换“上交用户”而误放宽禁项。厘清新 supervisor 常规写权限与
获授权协调批次写工具/测试的例外（§2.2 当前绝对禁测试，§12 又要求其写测试）。仓库外入口同步要在首次无人值守拉起之前验收。

### AR1-6 — A5/A7 演练与激活顺序不可按现文执行（§10/§12/§13-1）

本次 D1 已经由用户手动调起，且 supervisor 未落地，不能回填成 A5 的无人介入首段；真实接受轮是否退修也不能为凑
“构思→接受→构思 D2→接受”而预设。A7 未指定已接受实现范围；用本项则涉及需另行授权的 infra，用暂停 P1 项则越界。
将固定分支演练放入隔离夹具/副本，与真实门决定分开；具名演练范围、资源口径和负责角色，合成结果不得写成真实 D/C/R 通过。
按准备规则和入口→验证 CLI/交接→演练→用户签封/启用的依赖次序重排；A6 手点回退必须明确为降级结果，不能仍算 A5 全自动通过。
A8 区分现有工作项门与本项正常状态推进；补失败/暂停分支验收。未来若走研究轨道接受，BC 须覆盖行为、边界失败、测试和文档一致，
不能沿用当前一概 N/A；本轮不提前冻结 BC，也不签 `UNITY_NA` 关闭结论。

### AR1-7 — 减负估算包含本提案禁止代拍的样本（§1/§8）

CSV SUB 集含 #37（账本 2026-09-14 安装 tokenizers）、#8/#6（2026-09-22 追加 2/3 次诊断 Play，且伴随合同例外），
与 §5.2/5.3 排除下载、Play、合同变更相冲突；不能计为整条授权不再打断。请按原账本拆分混合条目、重新给出合规子集与上限，
保留统计输入原件不改写。87 次提交角色变化不是 87 次用户操作的直接证据（§1 自述 76 条无角色标记），补可复算口径与原始输出，
把“切换→0”“异地转录结构性归零”限定为成功自动接力的目标，扣除每日重开、CLI 回退及必要人工节点；不需要新增运行数据来证明预测。

### AR1-8 — 收束用户待决与已定事项（§13）

§13-1 已由账本同日“用户定路径”及本轮具名任务确定为接受轮，改为已解决；其余七项保留用户裁定，不把沉默算批准。
建议 D3 首版不启用、否决不承诺实耗可回滚、parked 搬运首版仍交现有有权角色、Cursor 保留遗留；仅为建议。
Opus/约 2 h 节奏可按起草方向继续细化，窗口计法与首封期限须保留明确待选值；示例日期和额度不得成为默认授权。
上述修订不必等用户先答七题才开始；D2 应给能逐项签字的有限选项及未选时禁用分支，避免把落地设计再次交用户补写。

Accepted design-document changes: 无。已读正式设计 §1；本提案不修改运行时设计或里程碑证据。
Handoff: 构思角色修改本提案并逐项回应 AR1-1…8 后交接受 D2；首次退修计 1，适用 workflow §4.2 两次上限。
本批仅提案与状态板，未运行测试、安装 CLI、修改 infra、创建调度任务或消耗实验额度。
