# COORD-016 — 代拍放宽：D1 非递增判据与每提案上限、新增 D7 合同数值按推荐、启用 D2b

Status: ACCEPTED（D3，2026-09-26；研究轨道；BC-1…6 为 binding clarifications；用户对第二次退修选 (a)「再进行一次修改，闭合结果」，账本同日；仅接受设计，不授权协调落地或签封）
Author/role: 构思角色 / design ideation（Claude Code `/fable`，Fable 5.1）
Created: 2026-09-26
Last updated: 2026-09-26（D3 接受裁定；D1/D2 退修原文保留）
Track: 研究轨道（COORD 协调提案，与 COORD-015 同轨）
Inputs: `docs/evidence/authorization-ledger-stats-2026-09-25.{md,csv}`；`docs/authorizations.md` 2026-09-13…09-26 的退修/残留处置条目；
`docs/proposals/COORD-015-supervisor-role-record.md` §5.1/§5.4/§5.7/§13、BC-4/12/14；`docs/reviews/COORD-015.md` R1/R2；
`docs/evidence/COORD-015-drill.md` §1①；账本 2026-09-26「用户指示：起草 COORD-016，按三点放开代拍」与「用户裁定：允许 D7 作为有限例外」；文末「D1 接受裁定」AR1-1…4

> 本文是提案，不是授权。落地要改 `docs/roles/supervisor.md`、`docs/collaboration-workflow.md` §4.4、`docs/roles/review.md`、
> `tools/check_ledger.py`、`tests/test_check_ledger.py`、`tools/make_supervisor_drill.py` 与账本文件头，属工作流基础设施，只能由用户直接
> 授权的协调批次执行（workflow §7 规则 7）。本会话零测试、零代码、零消耗。COORD-015 已 `DONE`/`ENDED`，其 §5.1 不回改；本提案以
> 「替换句」形式给出新文本，落地时逐字覆盖对应句。

## 回应索引

| 轮 | 要求 | 落点 |
|---|---|---|
| AR1-1 | D7 与永不代拍「改 BC/AC/合同」相交 | 用户裁定「允许有限例外（推荐）」入账；§2.2 权限边界（数值种类闭集、排除项、接受角色保留合同写权、须新签含 D7 的信封）；§2.4 永不代拍闭集加逐字例外句 |
| AR1-2 | D7 可机检来源 | §2.2：触发限 `ACCEPTED` 之后；预注册来源 = BC/AC 内 `d7_range:` 机读行；快照读 `precheck_head`（历史）/暂存（pre-commit）；字段语法闭集；A2 具名反例 |
| AR1-3 | D2b 终局例外落点 | §2.3 列出九处「轮 3 终局」句的具名改法与 R4 终局语义；§3 纳入协调批次范围 |
| AR1-4 | A5 债务状态与 A3 命令 | §4 A5 改为修复→具名回归→复核闭合→`CLOSED`；A3 给出可执行命令与输出路径 |
| AR2-1 | D7 资格标记不合法 | §2.2：资格改为 `d7_range` 行内正向字段 `kind=` 闭集与 `bc=` 行绑定，不动复核项列；缺资格或不在闭集即不可代拍 |
| AR2-2 | D7 快照前后不等价 | §2.2：两视图都读已提交提案（pre-commit 读 `HEAD:`，历史读首父 = `precheck_head`），同批暂存的资格/推荐行不可见即拒绝；`Status: ACCEPTED` 快照前提；精确十进制比较；A2 加两例 |
| AR2-3 | D2b 轮 4 与开轮资格冲突 | §2.3：批准后分「有资格开 R4」与「无资格走回归通道」两条路径，失败终局都归用户；替换句与 A4 覆盖两路径 |
| AR2-4 | A3 不可执行 | §3/§4：具名脚本 `tools/check_route_text.py` + 规格文件，基线运行时解析，逐位置断言，缺失/重复即失败 |

## 1. 问题与证据（要素 1）

- **用户体感**（2026-09-26 原话）："我个人体感绝大部分时间都是赞同修改方案的，我觉得这方面相较于现在可以再放开一些"。
- **账本统计**（137 条，`authorization-ledger-stats-2026-09-25.csv`）：点头型（短确认 54 + 点选选项 40）94/137 = 69%；触发原因中
  「流程强制你拍板」17 条、「单次运行放行」15 条；推荐项采纳率 91%（stats.md）。
- **退修上限处置全样本**（账本标题含「第二次设计退修」或「审查残留」，2026-09-13…09-25）：SFT-002、LOOP-001（2 次）、FAST-001、
  COORD-015（4 次）共 8 次，用户 8/8 选 (a)/「A」/「选A」。COORD-015 §8 另有 2 条第二次退修选了删实验/拆项（ASSET-001、SFT-001），
  属范围变更，D1 禁项本就回用户，不受本提案影响。
- **残留数序列**（接受裁定具名条目数）：SFT-002 4→3；FAST-001 5→3；LOOP-001 6→6→4；COORD-015 8→4→4→2→1→0；FAST-002 6→3
  （2026-09-26 进行中）。现行 D1「严格递减」会把 LOOP-001 D1→D2 与 COORD-015 D2→D3 两处持平交回用户，而这两处用户实际都选了 (a)。
- **首次真实链的停点**（FAST-002，2026-09-26 supervisor 检查点摘要）：除 D1 处置外，摘要列出的待用户事项还有「阶段 1 各门的门值和
  最小样本量确认」「Unity 验证授权」「§5 执行信封」；其中门值/样本量是接受角色已给推荐值、且提案预注册了候选值的数字确认。
- **D2b 先例**：COORD-015 落地停点 R1→R2 就是"复核返工一次后通过"的路径；现行轮 3 终局回用户，D2b 类在 §13 U1 默认禁用。

## 2. 方案（要素 2、3；替换句逐字给出）

### 2.1 D1：严格递减改为非递增，加每提案上限

| 位置 | 现句（COORD-015 §5.1 D1 行 / `docs/roles/supervisor.md`「代拍类表」） | 新句 |
|---|---|---|
| 允许动作 | 仅当 r(n) < r(n−1) 时选 (a) … | 仅当 r(n) ≤ r(n−1) 且本提案已代拍次数 < 3 时选 (a) 保留范围并逐条列缺口（缺口 = 本轮 `open_items:`）；r(n) 定义、`open_items:` 落点（BC-14）与 D1 条目字段不变 |
| 禁项 | r(n) ≥ r(n−1)；… | r(n) > r(n−1)；本提案第 4 次；本轮或上一轮缺 `open_items:` 行或格式不合；同一轮第 2 次；其余禁项不变 |
| 计数键 | `<work_id>:D1:D<n>`（每裁定轮 1 次；严格递减故每提案总次数 ≤ r 首值） | `<work_id>:D1:D<n>`（每裁定轮 1 次）；另计 `<work_id>:D1` 累计 ≤ 3（机检按账本内同 work ID 的 D1 条目计数） |

机检（`tools/check_ledger.py` `_d1_errors()`）：`now > prev` 拒绝（现为 `now >= prev`）；新增同 work ID 的 D1 条目数 ≥ 3 时拒绝第 4 条。
不改 `open_items:` 解析与节绑定（BC-14）。持平代拍的语义：残留数未增即视为收敛中；原地打转由上限 3 与信封到期兜底。

### 2.2 新增 D7：预注册合同数值按接受角色推荐（用户 2026-09-26 裁定「允许有限例外（推荐）」）

**权限边界（AR1-1）**：D7 不是让 supervisor 改合同，而是把「用户在接受角色给出的推荐值上点头」这一步交给 supervisor；合同文本仍由接受角色写
（BC 行标 `CLARIFY`，引用 D7 条目标题）。覆盖的数值种类闭集：合格门门值、最小样本量、判定阈值、容差。排除（回用户）：阶段边界；安全约束
（速度/张力/geofence 等）；主指标定义（`C_track`、`C_cov` 等的计算方式或 IoU/身份门）；Unity/人眼/设备验证的通过条件；两种信封的任何维度
（次数、GPU·h、API 次数、Play、下载）；采样/数据划分。生效前提：用户为该 work ID 新签决策信封且 `classes` 逐字含 `D7`；已签信封不自动扩类。

| 项 | 内容 |
|---|---|
| 触发 | 仅在该 work ID `ACCEPTED` 之后（核对轮、待裁定答复或 BC `CLARIFY`），接受角色向用户申请确认某个已预注册的数值，并在提案文件裁定节末写机读行 `d7_recommend: <id> = <值>` |
| 预注册来源与资格（AR1-2、AR2-1） | `ACCEPTED` 时写入 BC 行（工程轨道写在 AC 行）的机读片段 `d7_range: <id> in [<lo>, <hi>] kind=<种类> bc=<BC-n｜AC-n>` 或 `… in {<v1>, <v2>, …} kind=… bc=…`；`kind` 取闭集 {门值, 最小样本量, 阈值, 容差}，是接受角色对「该数值属允许种类且不属排除项」的正向断言（语义责任在接受角色，机检只验结构）；`bc=` 必须等于该片段所在表格行首格的 BC/AC 编号（行绑定）；提案快照内该 `<id>` 恰好 1 行。不侵入「复核项」列 |
| 允许动作 | 当且仅当 `d7_recommend` 的值落在同 `<id>` 的 `d7_range` 内：按推荐值入账，一题一条目 |
| 禁项（回用户） | 值出区间/闭集；缺 `d7_range` 或 `d7_recommend` 行、或任一行多于 1 行；`kind` 缺失或不在闭集；`bc=` 与所在行编号不符或该行不在 BC/AC 表内；同一 `<id>` 第 2 次；快照处提案 `Status:` 行不以 `Status: ACCEPTED` 开头；信封 `classes` 不含 `D7` |
| 执行角色 | 接受角色按推荐值写 BC `CLARIFY` 行 |
| 计数键 | `<work_id>:D7:<id>`（每题 1 次） |
| 首版默认 | 启用（须信封显式列入 `D7`） |
| 条目字段 | 通用字段外必填 `question_id`（= `<id>`）、`decision`（逐字 = 推荐值字面）、`range`（逐字复制 `d7_range` 行）；`reason` 可省（同 D1） |

**语法闭集**：`<id>` 匹配 `[A-Za-z0-9_.-]+`；数值字面匹配 `-?[0-9]+(\.[0-9]+)?`（不带单位、不带指数，单位写在 AC/BC 正文）；区间 `[lo, hi]` 要求
`lo ≤ hi`，判定用精确十进制比较（`decimal.Decimal`），不得转二进制浮点；闭集 `{…}` 元素为字面，判定逐字相等；一行只含一个 `<id>`；`kind=`、`bc=` 各恰好 1 次。

**快照与前后一致（AR1-2、AR2-2）**：两视图读同一份已提交提案，与 D1/BC-14 同构：pre-commit 从 `HEAD:docs/proposals/<work_id>-*.md`
读 `d7_range`/`d7_recommend`/`Status:`，且待提交条目须 `precheck_head == HEAD`；历史条目从 `first_parent(commit(E))` 读，且须
`precheck_head == first_parent(commit(E))`（同 SUB 的首父谓词）。同一提交里暂存的新资格行或推荐行对两视图都不可见，因此「同批补行」在提交
前即被拒，提交后复判结论相同；提案后续编辑不改判历史条目。快照处提案 `Status:` 行须以 `Status: ACCEPTED` 开头，否则拒绝（`d7_range`
只在接受后写入 BC/AC 行，这一检查把「已 ACCEPTED 的提案版本」变成机检前提）。A2 反例：值出区间拒绝；`decision` ≠ 推荐字面拒绝；缺 `d7_range`
拒绝；`d7_recommend` 两行拒绝；信封无 `D7` 拒绝；同 `<id>` 第 2 条拒绝；同批暂存资格行 + 代拍条目 → pre-commit 拒绝、提交后复判亦拒绝；
`d7_range: g in [9007199254740992, 9007199254740992]` 对推荐值 `9007199254740993` 拒绝（精确十进制）；提交后改宽 `d7_range` 复判历史
条目结论不变；`kind` 缺失拒绝；`bc=` 不等于所在行编号拒绝；快照 `Status:` 非 `ACCEPTED` 拒绝。

### 2.3 启用 D2b（COORD-015 §13 U1 = B；AR1-3）

语义：同一停点第 2 次 `REWORK_REQUIRED` 后未闭集冻结，轮 3 终局改为「通过，或回用户；决策信封 D2b 在效时回 supervisor，supervisor 仅可
批准 1 次定向返工（限冻结集内具名 finding，`RED_LINE` 与 `blocks_consuming_gate` 未 release 的 finding 除外）；同停点第 2 次申请回用户」。
返工后按 workflow §4.4 开轮资格分两条路径（AR2-3）：**(i) 有资格**——修复批次在 PLAY_GOVERNING 上 diff 非空 → 开轮 4，轮 4 为新的终局：
通过，或回用户；**(ii) 无资格**——diff 为空（修复只触及规则/文档/测试）→ 不开新轮，冻结集内各 finding 按 §4.4「阻断 finding 的闭合」回归通道
逐条红绿核实，复核角色在同一复核文件写「回归核实」小节（不新编轮号），全部闭合 → 通过；任一未闭 → 回用户终局。两条路径下终局的
「回用户」都不可再代拍；冻结集、消耗性门 blocks/releases 配对不变；计数键 `<work_id>:<停点>:D2b`，两条路径同计 1 次。

九处常驻句的具名改法（落地时逐字）：

| 位置 | 现句片段 | 改法 |
|---|---|---|
| workflow §4.4 L393 | 轮 3 终局：通过，或回用户。 | 替换为上段引号内语义句，并紧接一句：「D2b 返工后按本节开轮资格分路：有资格开轮 4（终局：通过，或回用户）；无资格走本节阻断 finding 回归通道，任一未闭回用户」 |
| `docs/roles/review.md` L66 | 轮 3 终局（通过，或回用户） | 同上 |
| `docs/roles/review.md` L90；`AGENTS.md` L209、L277；`docs/roles/acceptance.md` L94；`.claude/commands/accept.md` L26；`.claude/commands/review.md` L17、L44 | 轮 3 终局 | 保留原句，句末加「（决策信封 D2b 在效时按 workflow §4.4 一次定向返工，轮 4 终局）」 |
| `docs/roles/supervisor.md` L60、L284 | 接 D2b（未启用）／首版默认 **禁用**（U1） | 改为「接 D2b（信封列入即生效）」／「启用（须信封显式列入）」 |

### 2.4 不变的部分与唯一的例外句

「永不代拍」闭集除下面一句外一字不改：`docs/roles/supervisor.md`「永不代拍」中「改 BC/AC/合同/采样」改为「改 BC/AC/合同/采样（例外：§2.2 D7
对已预注册 `d7_range` 数值选推荐值，合同文本仍由接受角色写）」。DIR/LIFE/ENV/FACT、Play、信封首签、范围变更、`DONE`/`CLOSED_*`、infra、
下载、D2a 均不动；否决窗口、撤销、`at:` 全序、S/X 到期机检、事实核查 F1–F10、单写者与停下条件不变。

## 3. 兼容性与受影响接口（要素 2、4）

| 文件 | 改动 |
|---|---|
| `docs/roles/supervisor.md` | 「代拍类表」D1 行按 §2.1 替换、D2b 行默认改启用、新增 D7 行；「两类引用与必填机读字段」加 D7 字段与失败关闭项 |
| `docs/collaboration-workflow.md` §4.4；`docs/roles/review.md`；`AGENTS.md`；`docs/roles/acceptance.md`；`.claude/commands/{accept,review}.md` | 九处「轮 3 终局」句按 §2.3 表逐字改 |
| `docs/roles/acceptance.md`；`.claude/commands/accept.md`；仓库外 `~/.codex/prompts/codex.md` | 加两句：`ACCEPTED` 时对可交 D7 的数值在 BC/AC 行写 `d7_range:`（排除项写 `D7_EXCLUDED`）；申请确认时在裁定节末写 `d7_recommend:`；D7 条目入账后写 BC `CLARIFY` 行引用该条目 |
| `tools/check_ledger.py`；`tests/test_check_ledger.py` | §2.1 判据与累计上限；`D7` 入闭集与 §2.2 校验；用例见 §4 A1/A2 |
| `tools/make_supervisor_drill.py`；`tests/test_supervisor_drill.py` | 夹具提案加 `d7_range:`/`d7_recommend:` 样例行；修 COORD-015 R2-1 债：`inject_open_items(proposal_path, items, round_no)` 插入 `### D<round_no>` 节末，具名回归 `tests.test_supervisor_drill.DrillFixtureTests.test_inject_open_items_targets_round_section`（修复前必失败） |
| `docs/authorizations.md` 文件头 | 代拍条目字段说明加 D7 三字段（`question_id`/`decision`/`range`） |
| `docs/roles/supervisor.md`「永不代拍」 | §2.4 例外句 |
| `tools/check_route_text.py`（新）；`tests/test_check_route_text.py`（新）；`docs/evidence/COORD-016-route-spec.json`（新） | A3 具名检查：读规格文件逐位置断言（文件、期望整句、期望出现次数、「不变」位置列表），基线用 `git log -1 --format=%H --grep='^COORD-016 协调落地'` 运行时解析后取其首父，「不变」位置与基线逐字比对；任一缺失、重复或改动即退出非零；输出写 `docs/evidence/COORD-016-route-check.log` |
| `docs/workflow-changelog.md` | 索引加行 |

已签信封：FAST-002 的决策信封 `classes: [D1, D4, D5, D6]` 不含 D7/D2b；要对本项启用需用户按 §5.5 另签（同名 `enabled: false` 撤销 +
新签，或新标题新签）。D1 判据放宽对已签信封立即生效（判据在工具，不在信封）。

## 4. 验收条件（要素 5）

| 编号 | 条件 | 证明方式 |
|---|---|---|
| A1 | D1：`now == prev` 通过、`now > prev` 拒绝；同 work ID 第 4 条 D1 拒绝、第 3 条通过；BC-14 节绑定用例保持通过 | test:`tests.test_check_ledger.D1Tests`（新增 ≥ 3 例，修复前必失败） |
| A2 | D7：合规条目通过（区间与闭集各一）；值出区间/闭集拒绝；`decision` ≠ 推荐字面拒绝；缺 `d7_range` 拒绝；`d7_recommend` 两行拒绝；信封 `classes` 不含 D7 拒绝；同 `<id>` 第 2 条拒绝；同批暂存资格行 + 条目 → pre-commit 拒绝且提交后复判拒绝；大整数精确比较例拒绝；提交后改宽 `d7_range` 复判不变；`kind` 缺失/`bc=` 不符/快照 `Status:` 非 ACCEPTED 各拒绝 | test:`tests.test_check_ledger.D7Tests`（≥ 13 例，修复前必失败） |
| A3 | §2.3 表九处新句各恰好 1 次命中、§2.4 例外句命中、supervisor.md 两处改句命中；「不变」位置（永不代拍闭集其余各句、D2a 行、AGENTS L59/L227 等 §2.4 所列）与基线逐字相同；规格文件缺一处或多一处均判失败 | cmd:`python3 tools/check_route_text.py --spec docs/evidence/COORD-016-route-spec.json > docs/evidence/COORD-016-route-check.log`；test:`tests.test_check_route_text`（缺失、重复、改动三例修复前必失败） |
| A4 | 夹具演练四段：持平残留 D1 代拍通过、第 4 次停下；D7 一题按推荐入账、一题值出区间停下交用户；D2b 路径 (i) 有资格开 R4 通过；D2b 路径 (ii) 无资格走回归通道、一条 finding 未闭 → 回用户 | artifact:`docs/evidence/COORD-016-drill.md` |
| A5 | 落地 diff 不改任何 `P1-*` 门值、verdict、授权原话（cmd:`git diff` 逐字比对）；COORD-015 R2-1 债走修复→具名回归（§3 `test_inject_open_items_targets_round_section` 修前红/修后绿）→本批独立复核核实→接受角色在 `docs/implementation-status.md` 改 `CLOSED`；复核核实前维持 `OPEN`，不以 `RELEASED_SCOPE_GAP` 冒充 | test:同 §3；artifact:`docs/reviews/COORD-016.md` |

## 5. 失败模式与资源风险（要素 6）

| 风险 | 缓解 |
|---|---|
| 持平代拍让不收敛提案多跑一两轮 | 每提案上限 3；信封 `expires_at`；每轮仍有接受角色具名残留可查 |
| D7 把不该由推荐值定的数字定了 | 只认提案预注册区间/闭集内的值；信封维度、Unity/人眼条件、主指标定义列为禁项；否决窗口 |
| 接受角色为触发 D7 把区间写得过宽 | 区间来自已 `ACCEPTED` 的提案文本，不是裁定节临时写；核对轮/复核照常核对 |
| D2b 一次定向返工被用来绕过轮 3 终局 | 仅冻结集内具名 finding、每停点 1 次、第 2 次回用户（COORD-015 原禁项不变） |
| 全程零消耗；落地约 1 个协调批次、2 次提交 | — |

## 6. 建议的实施范围与次序（要素 7，不强制）

1. 用户逐字授权本批（含 §13 选项）；2. 文档替换句（§3 前三行）；3. 工具与测试（A1/A2 修复前必失败）单独提交；
4. 夹具演练 A4 入库；5. 用户视需要为 FAST-002 重签含 D7/D2b 的信封。

## 7. 用户待决（有限选项，未选即按「未选时」执行）

1. U1 D1 每提案上限：A 3 次｜B 4 次。未选 = A。
2. U2 D7：**已裁定**（用户 2026-09-26「允许有限例外（推荐）」，账本同日）：作为永不代拍的有限例外启用，须信封显式列入。
3. U3 D2b：A 启用（信封显式列入才生效）｜B 维持禁用。未选 = A。
4. U4 D3（chore history 同意，COORD-015 §13 U2）：A 顺带启用｜B 不动。未选 = B。

## Binding clarifications (BC table)

| 编号 | 条款 | 复核项 | 证明方式 | 标签 | 依据 | 日期 |
|---|---|---|---|---|---|---|
| BC-1 | D1 只在 COORD-015 §5.1 原有身份、范围和行格式禁项均满足，`r(n) ≤ r(n−1)` 且同 work ID 历史 D1 代拍少于 3 条时可代选 (a)；同轮第二条、总第 4 条和 `r(n) > r(n−1)` 均拒绝。计数含已入账而后被否决的 D1 条目，不因撤销/否决返还。 | 行为/边界失败/测试覆盖 | test:tests.test_check_ledger.D1Tests | BASE | §2.1、A1；COORD-015 §5.1/BC-14 | 2026-09-26 |
| BC-2 | D7 只认 §2.2 的正向 `d7_range:` 资格：片段在已接受 BC/AC 表的条款/验收文本格，`kind=` 与 `bc=` 各恰好一次且绑定该行编号；接受角色负责排除安全、阶段、主指标、Unity/人眼/设备、信封和采样语义。§3「排除项写 `D7_EXCLUDED`」为 D2 遗留句，**不实施、不写入复核项列**；缺正向资格或结构/语义有疑义回用户。 | 行为/边界失败/文档一致 | test:tests.test_check_ledger.D7Tests | BASE | §2.2、AR2-1；workflow §4.2 复核项闭集 | 2026-09-26 |
| BC-3 | D7 的待提交与历史条目均只从提交前的已提交、`Status: ACCEPTED` 提案快照读取唯一 `d7_range`/`d7_recommend`；`precheck_head` 必等于首次入账提交的首父，暂存的新资格或推荐行不得参与。推荐行写在非 `### D<n>` 裁定节，保留各 D 轮 `open_items:` 节末约束；区间用精确十进制比较，闭集逐字比较；A2 的同批补行和大整数反例须修前红/修后绿。 | 几何时序/边界失败/测试覆盖 | test:tests.test_check_ledger.D7Tests | BASE | §2.2、AR2-2；COORD-015 §5.6/BC-14 | 2026-09-26 |
| BC-4 | D2b 须由新签且含 `D2b` 的决策信封启用，仅限 R3 未通过后的冻结集内一次定向返工。PLAY_GOVERNING diff 非空才可开 R4；为空不得编 R4，独立复核在原复核文件「回归核实」小节核实修前红/修后绿和冻结集，并写终局 verdict 与 `passed_candidate: <40 位 SHA>` 后方可称通过。任一未闭 finding、缺终局指针、未闭 `RED_LINE` 或未 release 的消耗性门阻断均不得通过，回用户；协调落地须同步明确 workflow §4.4「下一轮」闭合条件在无新轮回归通道的适用方式。 | 行为/边界失败/文档一致 | artifact:docs/evidence/COORD-016-drill.md | BASE | §2.3、A4、AR2-3；workflow §4.4 开轮资格与通过指针 | 2026-09-26 |
| BC-5 | A3 路由检查的基线是首个 `COORD-016 协调落地` 提交的首父，不取最后一个同前缀提交的首父；规格文件须有独立的预期位置闭集，漏列、重复、文本不符及 §2.4 不变句漂移均以非零退出并写证据，不能只搜索词。 | 测试覆盖/文档一致 | test:tests.test_check_route_text | BASE | §3/§4 A3、AR2-4 | 2026-09-26 |
| BC-6 | COORD-015 R2-1 保持缺陷账本 `OPEN`，直到修复的具名回归经独立复核核实；随后接受角色才改 `CLOSED`。本提案接受不关闭该债，不使用 `RELEASED_SCOPE_GAP`。 | 行为/文档一致 | artifact:docs/reviews/COORD-016.md | BASE | §3/§4 A5；COORD-015 R2@落地 R2-1 | 2026-09-26 |

复核项覆盖：行为 ✓ | 几何时序 ✓ | 边界失败 ✓ | 测试覆盖 ✓ | 文档一致 ✓

## Pending rulings（待裁定）

## Contract conformance（核对表）

### C1@落地（2026-09-27，Acceptance；第二次核对，交独立复核）

只读范围：首次核对已读 `2cbe3b2..b968e73` 的完整协调落地 diff 与补充同步 `b4b57d0`、`728a0fd`；本次核对候选 `8f0f708` 中 C1-1 修复 `04ccfc6` 的完整 diff、直接关联的 `tools/check_route_text.py`、`tests/test_check_route_text.py`、BC-5/A3 及 `docs/evidence/COORD-016-C1-1-red.log`、`-C1-1-tests.log`、`-route-check.log`。未运行测试，未改工具或实现，未签独立复核。

| 条款 | 结论 | 核对依据 |
|---|---|---|
| BC-1 / A1 | 满足 | `tools/check_ledger.py` 的 `_d1_errors` 拒绝 `now > prev`，`_cross_errors` 按 work ID 累计全部 D1 条目并拒绝第 4 条；`tests/test_check_ledger.py` D1Tests 覆盖持平、增加、第三/第四条与否决后计数，修前红摘要见 `docs/evidence/COORD-016-red.log`。 |
| BC-2 / A2 | 满足 | `_d7_errors` 从已提交提案解析 BC/AC 条款格、`kind` 闭集与 `bc` 行绑定；D7Tests 覆盖缺项、错格、错种类、错编号、出区间/闭集和重复题。语义排除项仍由接受角色在预注册时负责。 |
| BC-3 / A2 | 满足 | 待提交取 HEAD，历史取首次入账提交首父并校验 `precheck_head`；Decimal 精确比较及同批暂存资格不可见有具名用例。`d7_recommend` 的 D 轮节绑定按最近 1–3 级标题判断。 |
| BC-4 / A4 | 满足 | workflow §4.4 与角色/入口文本分有资格开 R4、无资格走原文件「回归核实」两路；`docs/evidence/COORD-016-drill.md` §1③④记录两个合成路径及回用户终局。真实 verdict 仍待独立复核。 |
| BC-5 / A3 | 满足 | `04ccfc6` 的 `in_place()` 先按行、再在改动块内按字符对齐基线原句，并校验全文计数；新增同行及跨行“原位置改写、别处补旧句”负例，以及删除、复制和邻近编辑正例。两项关键负例修前红见 `docs/evidence/COORD-016-C1-1-red.log`；修后全套日志无测试 failure、路由输出 69/69 exit 0 见 `docs/evidence/COORD-016-C1-1-tests.log`、`docs/evidence/COORD-016-route-check.log`。规格中的不变位置未在本修复批次改动。 |
| BC-6 / A5 | 满足 | `inject_open_items()` 已改为按 `### D<n>` 节末插入，具名 `test_inject_open_items_targets_round_section` 修前红、修后绿证据有记录；`docs/implementation-status.md` COORD-015/R2-1 仍为 `OPEN`，符合独立复核核实前不得关闭的条款；关闭仍待 R1@落地。 |

预复核关注项：`docs/evidence/COORD-016-C1-1-tests.log` 的全套为 1685 项、0 failure、9 errors、71 skipped；九个 errors 为 `cv2`/`numpy` 缺失，独立复核须核对基线同集及 C1-1 具名用例在其复核环境的结果。`in_place()` 对同一改动块内可解释为原句保留的文本按字符对齐判原位，工具文档已声明此判据边界；请独立复核核实其对 BC-5/A3 的适用性。本表为接受侧核对主张，不是独立复核 verdict；按 workflow §4.3.3 照交 R1@落地。

## Acceptance rulings（复判）

## Codex review decision

### D3 接受裁定（2026-09-26，Acceptance）

Decision: ACCEPTED（研究轨道；BC-1…6 为本项落地与复核的 binding clarifications）。用户按 workflow §4.2 (a) 保留范围的原话「再进行一次修改，闭合结果」已入账；D1/D2 两次退修计数不重置。AR2-1 的正向资格和行绑定、AR2-2 的同源已提交快照与精确十进制、AR2-3 的双路径、AR2-4 的具名路由检查均已给出可执行合同，见 §2.2–2.3、§3–4；D2 遗留文字与无新轮通过指针由 BC-2/4/5 按字面收束。

此接受仅冻结 COORD-016 的流程设计。`AGENTS.md`、角色/命令文件、工具、测试和账本头仍未改，D1 非递增、D2b、D7 规则均未生效；用户须另以逐字授权启动协调落地批次。`P1-ENG-FAST-002` 的既有决策信封不含 D2b/D7，不能自动扩类或消耗；COORD-015 R2-1 债仍 `OPEN`。本轮未跑测试、不签独立复核、不签任何信封。

Handoff: 用户裁定是否授权按本提案 §3–4 与 BC-1…6 执行零消耗协调落地；如授权，U1/U3/U4 按用户明选值或 §7 缺省值入账，再落地并交接受角色 C1@落地、独立复核 R1@落地。未授权前停在已接受设计。

open_items: none

### D2 接受裁定（2026-09-26，Acceptance）

Decision: REVISION_REQUESTED（第二次设计退修；研究轨道；提案仍未接受）。用户「允许有限例外（推荐）」已入 `docs/authorizations.md` 同日条目，仅解决 D7 权限方向，不授权基础设施落地、签封或运行。D1 AR1-1 的用户选择与排除范围已闭合；AR1-4 的 R2-1 债务闭合路线已修正；以下为仍阻止按字面落地的具名残留。

| 残留 | 依据与必须修订的合同 |
|---|---|
| AR2-1 — D7 资格标记不合法 | §2.2/§3 要求在 BC 行「复核项」列写 `D7_EXCLUDED`，但 workflow §4.2 与 `docs/roles/acceptance.md` 将该列闭集限定为「行为/几何时序/边界失败/测试覆盖/文档一致」。现案还把未写排除标记等同于可代拍，机检无法从自由文本证明该数值不属安全、阶段或主指标。改用不侵入复核项列的独立、明确、正向资格字段；规定它与具名 BC/AC 行、`d7_range`、排除项的绑定和失败关闭检查。仅有区间、缺资格或资格含糊时回用户。 |
| AR2-2 — D7 快照前后不等价 | §2.2 称历史从 `precheck_head` 读提案，pre-commit 却从暂存提案读；若同一提交暂存新 `d7_range`/`d7_recommend` 和 D7 代拍条目，提交前可通过，提交后按首父 `precheck_head` 复判则缺行。这与 COORD-015 §5.6 的 D1 预提交视图（读已提交 HEAD 提案）不同。固定同一不可变、已 `ACCEPTED` 的提案版本为两视图来源；校验 D7 条目 `precheck_head` 等于其首次入账提交首父，拒绝同批临时补资格/推荐行，并给出该反例的修前红/修后绿。区间数值若允许任意长度十进制字面，不得以二进制 float 比较：如 `[9007199254740992,9007199254740992]` 会误收 `9007199254740993`；须用精确十进制比较或限制可精确表示的闭集。 |
| AR2-3 — D2b 轮 4 与开轮资格冲突 | §2.3 同时写「返工后直接进入轮 4」和「PLAY_GOVERNING diff 非空的开轮资格不变」。workflow §4.4 明令 diff 为空时禁止开新轮；冻结 finding 的修复可以只触及规则文档，D2b 仍可能适用。明确 D2b 批准后有资格开 R4 与无资格开 R4 两条路径，后者按既有 finding 回归通道收束并规定失败时谁作终局决定；九处替换句与 A4 演练要覆盖两种路径，不能承诺无条件 R4。 |
| AR2-4 — A3 检查仍不可执行 | §4 A3 的 `cmd:` 含未解析的 `<落地前 SHA>`，且 `grep -n '轮 3 终局\|D7'` 只能列出现行字词，不能证明九处新句逐字命中或其余闭集未改。给出运行时解析基线的具体命令或具名检查脚本，逐位置断言预期文本、缺失/重复均失败，并保存可核对输出。 |

Disposition required by workflow §4.2 after two `REVISION_REQUESTED` rounds: (a) 保留当前提案范围，以 AR2-1…4 为已知缺口，交构思修正后再审（推荐；不等于 `ACCEPTED`）；(b) 关闭为负结果记录。`COORD-016` 无已签 D1 决策信封，且代拍权限本身属 supervisor 利害事项，故直接交用户；用户选择前不自行启动 D3。`P1-ENG-FAST-002` 的既有信封与交接保持原样，D7/D2b 均不生效。

open_items: AR2-1,AR2-2,AR2-3,AR2-4

### D1 接受裁定（2026-09-26，Acceptance）

Decision: REVISION_REQUESTED（首次设计退修；研究轨道；未接受，未授权落地、签封或启用任何代拍类）。

Rationale: §2.1 的 D1 非递增加累计上限方向与用户起草指示一致；§2.2、§2.3 和 A5 尚不能按现行权限与状态语义执行。用户在 `docs/authorizations.md` 同日仅授权起草，现有 `P1-ENG-FAST-002` 信封仍只含 D1/D4/D5/D6。本轮不写 BC、不改基础设施、不运行测试。

| 残留 | D2 必须给出的修订与核对依据 |
|---|---|
| AR1-1 — D7 权限界限 | §2.2 的「supervisor 选值→接受角色写入提案/BC」与 COORD-015 §5.2「改 BC/AC/合同」永不代拍项直接相交；用户 09-26 仅指示起草三点，未授权该例外或落地。先取得用户对**是否允许 D7 作为有限例外**的明确裁定；若维持禁令，删除 D7；若允许，逐字列明例外覆盖的数值种类、排除的阶段边界/安全/主指标/Unity/信封值、接受角色保留的合同写权及用户新签 D7 信封的前提。不能用 §2.4「永不代拍闭集一字不改」同时宣称 D7 可改合同。依据：`docs/roles/supervisor.md`「永不代拍」、`AGENTS.md`「角色边界」「共享状态更新」。 |
| AR1-2 — D7 可机检来源 | §2.2 同时允许设计轮触发和「已接受文本」预注册，前者在首次接受前无后者；§2.2/§4 A2 只查当前提案恰一行，未绑定被接受版本、推荐行与代拍前快照，后续编辑可改判历史条目。明确触发阶段、预注册来源及提交快照、`d7_recommend:`/账本字段语法（ID、数字与单位、区间端点、闭集、有限值、重复与多题），并规定 pre-commit 与历史复判同结论；A2 给出修前红/修后绿的具名反例。依据：COORD-015 §5.4–5.6 的 D1 快照/失败关闭合同及 `tools/check_ledger.py` 现行解析边界。 |
| AR1-3 — D2b 终局例外 | §2.3/§3 只改 workflow §4.4 和 review.md 一句，但 `AGENTS.md` 两处、`docs/roles/acceptance.md` 两处、`.claude/commands/accept.md` 与 `.claude/commands/review.md` 仍写「轮 3 终局」。给出这些常驻句与入口的具名替换/适用条件，并说清 R3 未通过后一次定向返工的后续复核轮、再失败的用户终局、冻结集和红线如何维持；将其列入需用户直接授权的协调批次范围。依据：COORD-015 §5.1 D2b 与 §5.7、现行 `AGENTS.md`「复核强制停点」。 |
| AR1-4 — A5 债务状态与证明 | COORD-015 R2-1 已在 `docs/implementation-status.md` 记为 `SCOPE_GAP`/`OPEN`；`RELEASED_SCOPE_GAP` 只用于接受角色改标并释放消耗性门，不能代表夹具已修。§3 既承诺修 `inject_open_items()`，A5 应按修复→具名回归→独立复核闭合的证据路线写 `CLOSED`；若不修则维持 `OPEN` 且不把它列为 A5 已完成。A3 的 `cmd:输出存 …` 也须改为可执行命令及输出路径。依据：COORD-015 R2@落地 R2-1、`docs/parked-status.md`「COORD-015 未闭义务」与缺陷账本状态定义。 |

Handoff: 构思角色按 AR1-1…4 修订后交 D2；D7 权限选择归用户，本接受裁定不代其选择。D2 前不动 `P1-ENG-FAST-002` 已签信封、暂停项或任何代码/额度。

open_items: AR1-1,AR1-2,AR1-3,AR1-4
