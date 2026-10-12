# COORD-007 — independent verification

Reviewer/role: 复核角色（review，独立复核，新鲜上下文会话）
Round: 1
Date: 2026-08-12
Candidate: `84b078773af4f4b51ca3328568ed2b7add00e5b5`
（`docs/proposals/COORD-007-process-overhead-reduction.md` 提案正文与
Acceptance round 1 同一提交落盘）
复核对象来源：状态板无待复核停点交接，复核目标由用户当场指定
（"核对现在对于流程改进的提案"）。

## 范围与方法

- 一次性副本 `.claude/worktrees/review-COORD-007`（detached `84b0787`），
  主树对实现文件只读；收工已删除。
- Diff 基线：`b6fdff3..84b0787` 仅 3 个文档路径（提案、状态板、轮换归
  档），状态板变更逐行核对（两条 COORD-007 记录 + 合规轮换，零新交接
  行，零授权账本条目——与"零执行授权"一致）。另自行 diffstat 证实
  `6019f33..84b0787`（上一通过候选，BODY-001 round 6）全部为文档路径，
  零 `controller/ Assets/ tools/ tests/ config/` 字节。
- 不采信提案 §1.1 或 Acceptance §A 的任何数字：全部机械声称在副本内按
  原始口径重测；git 历史类声称以 `b6fdff3` 为端点复算。
- 未重跑 Python/Unity 全套测试。理由（自证，非转述）：上一条 diffstat
  为本轮亲测，全部代码字节与 round 6 独立重跑（focused 50/50、
  preflight 36/36、全套 510 绿）所验树逐字节相同；本轮对象是提案文档。
  `tools/check_docs.py` 在候选树内自跑通过。

## 独立复现结果

### Acceptance §A 15 项 —— 全部成立

1. `tools/githooks/pre-commit` 仅 `exec python3 tools/check_docs.py`。
2. `grep -rn "2\.000000" tools controller Assets` 零命中；判据文本唯一
   存在于 `docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md`（门 1 定义
   块），变量逐字 `reported_sim_t`。
3. `tools/preflight_reanchor_env.py` 457 行；`sys.executable` 仅
   :379/:442 写入输出 JSON。`controller/`、`tools/` 中无任何把该值绑定
   到 tracker 启动解释器的机制（`run_rate*`/`run_track_experiment` 的
   `--python` 参数属 RATE/TRACK 通道，不覆盖 M3′ 人工操作单路径）。
4. `.gitignore` 为 `/runtime/*` + `!/runtime/README.md`；
   `git ls-files runtime/` 仅 README。
5. `ROLE_RULES['acceptance']['allow']` 共七项，无 `docs/evidence/*`。
6. `INFRA_PATTERNS` 仅点名 `check_docs.py`/`check_role_writes.py`/
   `rotate_docs.py`；`check_anchor_placement.py`、
   `check_scene_body_margin.py`、`check_track_env.py` 存在且不受保护。
7. `check_docs.py` docstring 写 "≤28 行 / Active handoffs ≤40"，代码为
   `MAX_ENTRY_LINES = 8`（:49）、`"Active handoffs": 70`（:57）。
8. `ProjectSettings/TimeManager.asset` 受追踪且逐字含
   `Fixed Timestep: 0.02`、`Maximum Allowed Timestep: 0.33333334`；
   `Packages/packages-lock.json` 受追踪。
9. `git diff --stat 7156f7e..b6fdff3 -- controller Assets tools tests
   config` 为空；`0ca13cb..b6fdff3` 恰 14 次提交；最后一次触代码路径的
   提交即 `0ca13cb`。
10. `git rev-list --count b6fdff3` = 415；触 `docs/archive/` 的提交 213
    （51.3%）。
11. `docs/current-status.md` 累计 +10,499/−10,119 行；`b6fdff3` 版本
    373 行。
12. BODY-001 匹配提交 74，其中 59 次零代码路径字节（逐提交 diff-tree
    重测，两数逐字复现）。
13. 最大提案 3,709 行（BODY-001）；五个 `NOT_STARTED` 提案
    1661+608+1015+1317+2236 = 6,837 行。
14. `61ea20b` 提交于 2026-08-07。
15. `analyze_m3_body.py`：`raise AnalysisError` 恰 110 处；
    `canonical_trial_id` def :486，冻结十 ID，canonical A1 旧 ID 抛
    `run_id_void_consumed`，其余抛 `run_id_not_frozen_trial`；
    predecessor SHA 字面量 :127-131；`metrics_projection_aspect_mismatch`
    :1239；`arm_a_trial_ids_not_frozen_sequence` :1396。

### §3.1 拦截记录 —— 七行全部锚定

- DETECT R1 B1 引文 "silently, with no exception and no failed test"：
  `docs/reviews/P1-DETECT-001.md:192`。
- EVAL-001 升格链：BODY 复核 round 1 N1（`docs/reviews/
  P1-M3-BODY-001.md:190`）→ 提案 §C N1 裁定（:1312）→ BC-BODY1-17
  （:1363）→ 状态板 `P1-EVAL-001` 行与 BC-BODY1-17 约束 bullet。
- DR-P1-M2-001 B1（分母为受处理变量）：`docs/design-reviews/
  DR-P1-M2-001.md:46,:63`。
- RATE-002：backlog 不变量 `0 <= current_frame_id -
  last_processed_frame_id <= 1`（评审 :42/:880 + 两份证据）；metrics
  cutoff 三数在 `docs/evidence/P1-M2-RATE-002-metrics-cutoff-fix.md`
  :17-20（5.040644030118151 − 4.3017754554748535 = 0.738868575… >
  0.050001，与提案舍入一致）。
- SCENE-006 F16（:1444 起，BLOCKING）与 F23 渲染范畴错误
  （`CreateTargetReplica`/`AddCarVisual`，:2106-2112）。
- 账本硬语义：`docs/authorizations.md:139` 逐字「"查看一下review结果"
  已明确不解释为 GO」；:80/:107 "独立的新授权，不追溯恢复旧授权"；
  round 20 §B.4/§B.6 勘误撤销原文在 BODY 提案 :2644-2649（"现作勘误，
  不构成用户授权"）。
- 用户 Play 拦截（RATE-002 R3/R6/R7、SCENE-002 attempts）在对应评审与
  Unity 日志有记录锚点。

### §3.2 削减对象 —— 结构与抽样支持

- 条件 5 "0 真阳性"：抽样约 20 条在案审计结果（`implementation-status.md`
  6 条、BODY 提案/复核 10+ 条、RATE-003/SCENE-006 复核若干），全部
  clean 或可完整归因；唯一真实 infra 越权（round 21，改
  `tools/check_track_env.py`）恰为该工具 PASS 假阴性——BODY 提案
  :2644-2649 逐字，且假阴性根因与上文 §A6 的 `INFRA_PATTERNS` 字面名
  漂移互相印证。（"50 次"精确总数未逐一重数，见 N6。）
- 多线汇报模板 `AGENTS.md` 33-49 行恰 17 行；`MAX_ACTIVE_HANDOFFS = 1`
  在 `check_docs.py:68`——"结构上不可触发"论证成立。
- "12 轮纯闭环复核 0 新阻断"：抽样 BODY rounds 4/6，两轮均无新阻断，
  一致；全量 12 未重数（N6）。

### §4 三处必须先修的事实 —— 全部成立（同 §A 2/3/4）

### 其余锚点

- 44 裁定轮 = 38 接受轮（`^#+ Acceptance round` 计 38）+ 6 复核轮；
  18+16+5+3+2 = 44 算术成立（分类本身作者自证，N6）。
- 距上次新增 DONE：`1cea988`（2026-07-27 "close TRACK-002"）→
  2026-08-12 = 16 天。
- A1 全精度 `0.5784550773737355` 与 `130.0018317103386 s`：
  `implementation-status.md:634/:636`、`unity-test-log.md:3416/:3425`。
- BC-C7-8 追溯计数（SCENE-005 4 轮 / SCENE-007 2 轮 / VLM-SCOPE-001
  4 轮 / VLM-CAL-001 4 轮）与状态板逐一一致。
- BC-C7-13 预算：决策块前恰 395 行 ≤ 400（另见 N3）。
- R6 引句 "zero-ID E5-A diagnostics cannot issue binding gate evidence
  under COORD-005" 在状态板逐字存在；`captureDeltaTime` 在
  `Assets/ controller/ tools/` 零命中。
- runtime 磁盘现场与 §4.3 描述一致：三次作废现场（attempt 1/2/3 hold
  文件与 `…-void-attempt-3-hold` 目录）全部只存在于未追踪 `runtime/`；
  `…-attempt-4/` 运行目录在盘。

## Findings（本轮均非阻断）

**F1 — 提案头部 Status 未随接受更新。** `COORD-007-process-overhead-
reduction.md:3` 仍为 `Status: PROPOSED`，与同文件 Codex review decision
块（`ACCEPTED_WITH_BINDING_CLARIFICATIONS`）、状态板两条记录及仓库惯例
（SCENE-004、M3M4-SCOPE-001、TRACK-002、M2-SCOPE-001 四例头部均随接受
改写）不一致。修复归接受角色。

**F2 — BC-C7-4 重述位置清单漏 `docs/current-status.md` 自身散文；须在
对应批次授权前补入清单。** 实测两处活规则重述不在清单：
(a) 状态板表头（:5 "Archive: `docs/archive/` (monthly files hold
rolled-off entries)"、:8-11 "rotation runs via `python3
tools/rotate_docs.py`" 及滚动上限句）重述滚动/归档机械，属 R9 清单；
(b) Active handoffs 节首（:165-167 "Single-track discipline
(COORD-003): exactly one row may be active…enforces the cap"）重述单线
纪律，属 R8 清单。BC-C7-4 自设标准是"漏改任一处即 R5 类漂移，批次不合
格"，而按现清单逐字执行恰会留下失效散文，与 R5(b)（同文件内 docstring
漂移）同型；按提案自身 R4 判据（"操作员或工具的行为会不会因这段文字而
不同"——该表头是所有角色开工必读文本）不属可豁免的 CLASS_3 闭集。修复
是接受角色对 BC-C7-4 的追加条目，零代码。

## Notes（不构成缺陷，留档）

- N1：§1.1 总括句"全部数字于 2026-08-12 在 main（`b6fdff3`）上实测复
  现"对两行不按字面成立：78.6%（326）行——按"不触五代码路径"口径本轮
  实测 333/415（Acceptance 测 332，±1 属根提交/工具处理差异），按"仅
  docs/"口径 395；"此后 271 次提交"行——`1cea988..b6fdff3` 实测 273，
  271 恰对应起草时 HEAD `43a8269`。两行方向均成立且实测更极端，其一
  Acceptance 已作口径披露；不改变任何裁定。
- N2：§9 步骤 3 "（含那 30 条补追行）"在受追踪文档与 attempt-4 收据键
  中均无锚点（盘上 `frames.jsonl` 计 784 行；receipt 仅
  `catchup_timeout_s` 配置键）。非承载性旁注；建议 R10/R11 批次证据中
  给出该数的机器出处或删去。
- N3：BC-C7-13 括注"（§1–§10，实测 395 行）"的 395 实为"决策块之前全部
  行"（含标题与导语；纯 §1–§10 为 379 行）。两种口径均在 ≤400 预算内。
- N4：`canonical_trial_id` 行号 §9 写 :485-505、§A15 写 :486-505，def
  实测 :486；文内自不一致，无行为影响。
- N5（可追溯性）：提案草稿与接受决策同一提交落盘，草稿在接受前无独立
  提交，接受过程是否改动 §1–§10 无法以 diff 证伪。起草身份披露在案且
  本轮零执行授权，风险有限；建议后续提案在决策前先行落盘。
- N6（作者自证项划界，附议 Acceptance §A 的处理）：44 裁定轮
  18/16/5/3/2 成因分类、条件 5 "50 次运行"精确计数、"12 轮纯闭环复核"
  全量——未逐一重数；抽样均与主张一致（见上）。三者只作动机统计，不
  承载任何门槛。

## UNITY_NA 处置

本工作项未声称 `UNITY_NA`，也不产生运行时行为，无附议/反对对象。零执
行授权结构（BC-C7-1/-6：每批开工需 `docs/authorizations.md` 用户逐字
条目；R10/R11 新开 work ID 走完整六步 + 强制停点）与 workflow §7 规则
7 一致，本复核予以确认。

## Verdict

**Round 1: PASS_WITH_NOTES（candidate `84b0787`）。**

Acceptance round 1 的全部机械依据独立复现成立；两条非阻断缺陷交回接受
角色——F1（头部状态）随时可修，F2（BC-C7-4 清单缺口）须在首批/R9 对应
批次授权前闭合；N1–N6 留档。本 verdict 不构成任何批次的执行授权，六个
用户决策点（round 1 §D）不受影响。

passed_candidate: 84b078773af4f4b51ca3328568ed2b7add00e5b5

（说明：机读 `passed_candidate` 行按已接受、尚未开工的 BC-C7-9 格式
自愿提前采用；存量轮次不回改。）

## 边界自查

本会话未修改任何实现文件；主树写入仅本复核文件与状态板（含机械轮换
产生的归档）。复核副本 `.claude/worktrees/review-COORD-007` 已按收工
纪律删除。

---

# Round 2 — 第一批 R1–R9 协调批次落地件（PLAY_GOVERNING 半边）

Reviewer/role: 复核角色（同一复核会话续轮）
Round: 2
Date: 2026-08-12
Candidate: `3d875242d3e7a573456abf8a7b05ab363766ef15`
Diff basis: `84b0787..3d87524`，起点按 R7 从本文件最近一行
`passed_candidate` 运行时派生，终点为唯一匹配
`git log --grep="^COORD-007: 协调批次落地第一批"` 的提交。开轮资格
（R1）：区间在 PLAY_GOVERNING 上非空（6 条 tools/tests 路径）。
测试树哈希：`3d87524:tests` = `c6a7cbb91d4d03380265748f91553c682e7be216`，
`3d87524:tools` = `8b26fa22db999c93b674dc6126403e3029fd3b57`。

## 范围核对（区间全部 20 路径逐一归因）

- 批次本体 17 路径（`3d87524`，账本凭据见下）：AGENTS.md、workflow、
  current-status、提案（接受轮 2 + F1 头部修复 + BC-C7-4 F2 追加）、
  五份角色细则、`/accept`、`/chore`、`check_docs.py`、
  `check_role_writes.py`、两测试文件、`rotate_docs.py` 与其测试删除。
  零 `controller/ Assets/ config/`、零设计文档、零 Unity 日志——未越出
  R1–R9 授权。
- 区间其余 3 提交路径：`074f1b2` 为本复核轮 1 批次（4 路径，自归因）；
  `239f985` 为账本代录（接受角色白名单路径）。
- **授权链（BC-C7-1）**：`docs/authorizations.md` "2026-08-12 COORD-007"
  条目逐字含用户原话与三个结构化选择（第一批+R9 / R2 取 (b) 明写移除 /
  rev-12 归接受角色），并逐条列明未授权项；账本提交（`239f985`）先于
  批次（`3d87524`），批次提交信息引用该条目。仓库外
  `~/.codex/prompts/codex.md` 由用户手动同步已记一句。

## 独立复现与探针（全部在一次性副本 `review-COORD-007-r2` 内）

**文本落地逐条核对**：R1/R3/R4/R7 落 workflow §4.4（PLAY_GOVERNING
唯一定义含 `ProjectSettings/`、`Packages/packages-lock.json`、冻结集
点名操作单；AGENTS.md 与 review.md 仅引用名字不复抄——BC-C7-2 成立）；
R2(b) 的"已提交批次的写入归因不再机械检查"明文落 §4.3.1 与 §7 规则 7，
轮 1 清单四处重述全部同批改写，全仓清扫零残留（`--base` 在
`check_role_writes.py` 按批次声明降级为诊断保留）；R3 四条件含 BC-C7-5
隔离逐字落地；R4 分级闭集逐字 + 接受角色复判/升格 + 应用约束 +
白名单 `docs/evidence/*`；R5 两处漂移实测已修（三个 `check_*` 工具
现受通配保护——实况探针见下；docstring 28/40 残句已消）；R6 落 §4.2 +
ideation/accept 细则，BC-C7-8 追溯句在；R8 的 AGENTS 文本、17 行模板
删除、`MAX_CONSUMING_ACTIVE=1`/`MAX_ZERO_CONSUMPTION_ACTIVE=2`、
Consuming 列、Gate-echo 检查与测试同一提交（BC-C7-10 同批契约成立）；
R9 四节并 `## Log` 零条目丢失（旧 12 条中 11 条在 Log，1 条为轮 1 批次
按旧规则轮换进只读归档；§C 风险 6 闭合）、`rotate_docs.py` 删除后活
文件零悬挂引用、零代码路径触碰 `docs/archive/`（风险 5 闭合）。轮 1
F1/F2 确认闭合：头部 Status 已改，BC-C7-4 已补状态板自身两处重述且
两处改写与清单修正同批落地。

**测试自重跑**：focused `tests.test_check_docs` +
`tests.test_check_role_writes` = 22/22 OK（副本内）。全套
`.venv-track discover -s tests`：副本首跑 FAILED（25 失败/4 错误全部
集中于 `test_scene006_probe`，另 skipped=4）；将主树未跟踪
`runtime/yoloe`、`runtime/p1-scene-006`、`runtime/models` 复制进副本后
该模块 26/26 OK，全套 **Ran 513, OK (skipped=2)**——两个 skip 均为
环境条件（`.venv-track` 无 re-anchor 栈；RATE-002 归档工件未复制，
主树存在故其运行时 skipped=1）。结论：批次与接受轮 3 的
"513 绿（skipped=1）"声称在主树环境为真；失败纯系测试对未跟踪
`runtime/` 资产的耦合（见 N7）。新增回归测试的"修复前必失败"性质
已验：旧 `check_role_writes.py` 上新测试模块直接失败（import 级——旧版
无 `violations_for_infra_fix`；通配断言在旧清单下也必失败）。

**行为探针**：候选板 `check_docs.py` 基线通过；干净第二条消耗行 →
响亮拒绝（轨道上限阳性对照）；改 `check_track_env.py` 后
`--role implementation` 报越权、同状态 `--infra-fix` 通过（R5 例外
闭集双向实证，`controller/` 路径被 `--infra-fix` 拒绝有单测覆盖）。

## Findings（Round 2）

**F3 — CLASS_2（NOT_MECHANIZABLE）：R5 例外的"任何角色"与复核角色
绝对禁令互相矛盾。** `AGENTS.md`（共享状态更新节）与 workflow §7
规则 7 均写"**任何角色**可在……单独提交里修复自检工具"；而同批
`docs/roles/review.md` 写 `tools/`、`tests/` "**一行也不许改**"（无
例外注记），未动的 `CLAUDE.md` 保留同义绝对句，且提案红线 A（接受轮 1
§E 声明全部保留）要求复核五路径禁令绝对。两份必读规则对"复核角色可否
用 `--infra-fix`"给出相反答案；按 §4.4 判据（操作员行为会否因文字而
不同）最低 CLASS_2。修复：在 AGENTS.md 与 workflow §7 的例外句排除
复核角色（或明写角色细则优先），`CLAUDE.md` 同批对齐——三处均为
infra 文档，超出 `--infra-fix` 路径闭集，需用户授权的协调批次。闭合：
`NOT_MECHANIZABLE`，定点复看上述三文件的例外句。

**F4 — CLASS_2（活缺陷）：Gate-echo 对单元格含竖线的 gate 行静默
免检——当前恰好豁免唯一消耗性轨道。** `check_docs.py` 的
`split_table_row` 按裸 `|` 切列，不识别反引号内的字面竖线；gate board
`P1-M3-BODY-001` 行与 `P1-DETECT-001` 行的单元格文本含主指标名
`C_track|geom`，切列右移后 Overall 列（index 6）落在无反引号单元格，
`gate_overall_tokens` 的 `if id_match and overall_match` 静默丢弃该
行。后果：这两个 ID 从不进入 echo 执法。副本实测：把交接表 User 行的
echo 篡改为 `` `P1-M3-BODY-001`@STALE_TOKEN `` 后 `check_docs.py`
**通过**（应拒绝）。R8 的两个机械载体之一对当前活跃工作项形同虚设，
即接受轮 3 §A 预警的"漂移落在新代码里"。现有 echo 测试夹具无竖线，
"asserts the claim in name only"（RATE-003 R3 同型教训）。闭合绑定：
修复前必失败的具名回归测试（建议
`test_gate_echo_enforced_when_gate_cells_contain_pipes`），fixture 须
含真实形状的 `C_track|geom` gate 行 + 错误 echo，断言违规非空；修复
不触及 §4.4 点名的三个 Play 治理门文件，可走 R5 `--infra-fix` 单独
提交（鉴于 F3 未决，执行者应为非复核角色）或协调批次。

**F5 — CLASS_2（潜在缺陷）：轨道纪律检查静默跳过畸形交接行。**
`check_track_discipline` 对 `len(cells) <= max(work_col, status_col,
consuming_col)` 的行直接 `continue`：副本实测一条六单元格的活跃
消耗形交接行 **SILENT-PASS**——同时逃出两个轨道上限与"Consuming 列
必填"校验。畸形行应响亮拒绝（fail-closed），不应静默豁免。闭合绑定：
修复前必失败的具名回归测试（建议
`test_malformed_handoff_row_is_rejected`）。与 F4 同根因（裸竖线切列
+ 静默跳过），建议一并以"反引号感知切列 + 畸形行显式违规"结构性修复；
交接行内含裸竖线当前是响亮误读（见 N8），方向可接受。

CLASS_3：无。

## 对接受轮 3 §C 六项风险的逐项答复

1. `check_track_discipline`：**会**静默漏计——见 F5（短行）；行内
   竖线错位是响亮失败（可接受，N8）；`PAUSED` 前缀的反引号/大小写
   处理正确；分隔行跳过正确。
2. `check_handoff_gate_echo`：反引号引用限定与"Gate board 无行的 ID
   不触发"（含 `COORD-007` 自身）属 BC-C7-10 授权批次定义解析格式的
   范围，本轮**附议为设计选择**（N9）；但竖线致 token 表丢行是事故
   不是选择——见 F4。
3. `--infra-fix` 路径闭集成立（实况 + 单测双向验证）；但"谁可调用"
   的文本矛盾见 F3。
4. 接受白名单 `docs/evidence/*` 未越出授权：账本选项 3 逐字批准该
   放开，`docs/roles/acceptance.md` 以 CLASS_3 应用约束与 rev-12 职责
   限定用法；配套单测在。
5. `rotate_docs.py` 删除干净：活文件零悬挂引用、零失效导入；
   `docs/archive/` 无任何代码路径触碰，只读性成立。
6. `## Log` 合并零丢失：旧四节 12 条 = Log 内 11 条 + 只读归档 1 条
   （轮 1 批次旧规则轮换），新增 2 条有序置顶。

## Notes（续轮 1 编号）

- N7：全套测试的副本可复现性依赖主树未跟踪 `runtime/` 资产
  （`test_scene006_probe` 26 用例读盘上探针工件与权重路径；
  RATE-002 归档工件决定一个 skip）。这是提案 §4.3 诊断的"未跟踪
  收据对复核副本不可见"在测试层的同型表现，应作为 R10/R11 批次证据
  设计的输入；非本批次引入，不阻断。
- N8：交接行单元格含裸竖线时列错位为**响亮**失败（Consuming 校验
  报错），fail-closed 方向可接受；F4/F5 修复落地前，状态板作者应避免
  在表格单元格使用裸 `|`。
- N9：echo 解析的两项限定（仅反引号引用、无 gate 行不触发）已附议；
  若未来 Gate board 出现 `COORD-*` 行或 Overall 失去反引号包裹，
  `gate_overall_tokens` 的静默丢行行为将扩大免检面——F4 修复时应一并
  改为"丢行即违规"。
- N10：批次由接受会话以协调批次执行并由另一接受会话（轮 3）确认停点；
  协调批次免角色写入检查的凭据链完整。执行者与停点确认者分离在案。

## UNITY_NA 处置（Round 2）

接受轮 3 §B 条件 3 明确本批零运行时行为、不申请 `UNITY_NA`；本轮
附议：无 Unity 门适用，未签发任何 `UNITY_NA`。

## Verdict（Round 2）

**Round 2: REWORK_REQUIRED（candidate `3d87524`）。**

三条 CLASS_2：F3（规则文本矛盾，NOT_MECHANIZABLE）、F4（Gate-echo
竖线免检，活缺陷，含篡改探针实证）、F5（畸形交接行静默豁免，潜在
缺陷）。其余全部核对项通过：授权链、范围、BC-C7-1…13 落地、轮 1
F1/F2 闭合、focused 22/22 与全套 513 自重跑、R5 探针、文本清扫、Log
零丢失。修复通道：F4/F5 走 R5 `--infra-fix` 单独提交（非复核角色
执行）或协调批次，各绑定修复前必失败的具名回归测试；F3 需用户授权的
协调批次。修复批次触及 `tools/`/`tests/`，按 R1 开轮资格下一复核轮
成立。上一通过候选维持本文件既有 `passed_candidate` 行（`84b0787`）
不变；本轮按 BC-C7-9 不写该行。

## 边界自查（Round 2）

本会话未修改任何实现文件；变异探针与运行时资产复制全部发生在一次性
副本 `review-COORD-007-r2` 内，随副本删除。主树写入仅本复核文件与
状态板。

---

# Round 3 — 复核轮 2 返工修复（F3/F4/F5 + 自查第四洞）

Reviewer/role: 复核角色（新鲜上下文会话，非前两轮会话）
Round: 3
Date: 2026-08-12
Candidate: `544cd18f425f6d0391d7d74368546c9eba527391`
Diff basis: `84b0787..544cd18`。起点按 R7 由本文件最近一行
`passed_candidate` 运行时派生（`84b078773af4f4b51ca3328568ed2b7add00e5b5`），
非轮 2 的 `REWORK_REQUIRED` 候选。开轮资格（R1）：区间在 PLAY_GOVERNING
上非空（累计 6 条 `tools/`/`tests/` 路径；轮 2 候选之后的新增量 3 条）。
测试树哈希：`544cd18:tests` = `8601c2c0f77a4d4de76148ab67c7cfa929e30af3`，
`544cd18:tools` = `dd87ca0c7dd7088180fe0d95ec8cc7f0c6a2e024`。
一次性副本 `.claude/worktrees/review-COORD-007-r3`（detached `544cd18`），
收工已删除；主树对实现文件全程只读。

## 范围核对（区间 9 提交、20 路径逐一归因）

- `3d87524` 经 `git merge-base --is-ancestor` 实测是 `544cd18` 的祖先，
  轮 2 已逐文件复核的区间未被改写；本轮新增量 = `3d87524..544cd18`
  的 9 个路径，其中 PLAY_GOVERNING 恰 3 条：`tools/check_docs.py`、
  `tests/test_check_docs.py`、`tools/check_role_writes.py`。
- `c617a98`（R5 `--infra-fix`）实测恰 2 路径
  （`tools/check_docs.py`、`tests/test_check_docs.py`）；用候选树自身的
  `violations_for_infra_fix()` 复算返回空列表——路径闭集成立，且未与
  证据产出混提交。提交信息按 R5 贴出了四条触发失败输出。
- `538bdf1`（协调批次）3 路径（`AGENTS.md`、workflow、
  `check_role_writes.py` docstring），提交信息逐字引用账本
  「修复复核轮 2 三条流程漏洞」条目；账本提交 `4fbfb2f` 在其之前落盘，
  账本 diff 为纯追加（零删除行）。授权链（BC-C7-1）成立。
- `cf2c655` 为本复核文件轮 2 批次（自归因）；`544cd18` 为接受轮 4 的
  状态板 + 提案，提案侧实测为纯追加（零删除行），本文件自 `cf2c655`
  之后零字节改动。
- 零 `controller/`、零 `Assets/`、零 `config/`、零设计文档、零 Unity
  日志；未越出账本授权的三条 finding 修复范围。

## 独立复现（全部在一次性副本内）

**自重跑测试。** focused `tests.test_check_docs` +
`tests.test_check_role_writes` = **26/26 OK**（与接受轮 4 声称一致；
26 = 12 + 14，"26/26 + 14/14"系合并跑与单模块跑并列，非两组不同数字）。
全套 `.venv-track discover -s tests`：副本首跑 517 中 25 失败 / 4 错误，
**全部集中在 `test_scene006_probe`**；按轮 2 同法复制主树未跟踪
`runtime/yoloe`、`runtime/p1-scene-006`、`runtime/models` 后
**Ran 517, OK (skipped=2)**。517 = 轮 2 的 513 + 本批新增 4 条回归测试，
计数自洽；零附带破坏（实测仅这两个测试模块 import 被改工具）。

**修复前必失败（revert-rerun，副本内 `git checkout c617a98^ --
tools/check_docs.py`）。** `tests.test_check_docs` 12 条中恰 4 条失败，
逐名与提交信息一致：`test_gate_echo_enforced_when_gate_cells_contain_pipes`、
`test_gate_row_with_unparsable_overall_is_flagged`、
`test_malformed_handoff_row_is_rejected`、
`test_gate_echo_matches_multi_segment_work_ids`；其余 8 条仍绿（新测试
不是靠改动既有断言换来的）。恢复后 26/26 复绿。轮 2 对 F4/F5 绑定的
两个建议测试名逐字落地，F4 夹具确含真实形状的反引号内 `C_track|geom`
gate 行 + 错误 echo。

**真实板行为（本轮亲测，不采信任何转述）。**

- 候选树 `python3 tools/check_docs.py` 通过（exit 0）。
- 解析诊断：Gate board **25/25 行**全部切出 7 单元格并产出 Overall
  token（修复前 `P1-M3-BODY-001`、`P1-DETECT-001` 因 `C_track|geom`
  错位被静默丢弃）；Active handoffs 5/5 行全部 8 单元格；
  `gate_overall_tokens` 违规列表为空。
- 篡改探针 11 路（沙箱在副本内，随副本删除）：候选代码下 **11/11 按
  预期**（基线通过；6 个真实 echo 逐一改 `@STALE_TOKEN` 全部被拒；
  删 echo 被拒；畸形短行被拒；Overall 去反引号被拒；第二条消耗行被拒）。
  同一组探针在**修复前**代码上只有 4/11 符合预期——`P1-M3-BODY-001`、
  `P1-M3M4-SCOPE-002`、`P1-VLM-CAL-001`、`P1-VLM-SCOPE-001` 四路
  `@STALE_TOKEN` 篡改、删 echo、畸形短行、Overall 去反引号共 7 路
  **静默通过**。接受轮 4 声称的"四路探针"我实测为 6 路 echo 全被拒
  （其中 4 路是修复前逃逸的），声称成立且偏保守。
- 引用侧覆盖枚举：5 条交接行内被引用且有 gate 行的 work ID 现已全部
  进入执法；唯一 `matched-no-gate` 是 `COORD-007` 自身（无 gate 行，
  轮 2 N9 已附议为设计选择）。

**对抗性解析探针（本轮新增，超出实现者自查范围）。** 未平衡反引号
吞掉竖线 → 行长不足 → **响亮拒绝**；Consuming 列之前多一根裸竖线 →
Consuming 校验**响亮报错**；之后多一根 → 列索引不受影响，轨道上限
照常执法（第二条消耗行被抓）。方向全部 fail-closed，未发现新的静默
免检路径（唯一例外见 N15，非承载性）。

## F3/F4/F5 闭合的独立核验

- **F3（NOT_MECHANIZABLE，定点复看三文件）——闭合成立。**
  `AGENTS.md:109-115` 与 workflow §7 规则 7（:378-385）例外句均改为
  「**唯一例外（COORD-007 R5，复核角色除外）**：非复核角色可在……」，
  并各自加了"红线 A 五路径绝对禁令优先、复核发现自检工具缺陷时只写
  复核文件"的明写句；`CLAUDE.md:28-29` 的复核绝对句保持不变且不含任何
  例外句，经此排除后无矛盾。账本额外要求的
  `tools/check_role_writes.py:18-21` docstring 已同批对齐。全仓
  `git grep` 复核：`--infra-fix` / `COORD-007 R5` 的活规则重述位置只有
  这三处 + 工具自身，`docs/roles/`、`.claude/commands/` 无残留反例，
  "任何角色"授予例外的措辞在活规则文件中零命中（提案正文残留见 N11）。
  说明：该排除仍是**文字**约束——`--infra-fix` 模式不读 `--role`，
  工具层面不阻止复核会话调用；轮 2 将其定级 `NOT_MECHANIZABLE` 正是
  此意，本轮附议此定级，不另提要求。
- **F4（活缺陷）——闭合成立。** 根因 `split_table_row` 改为反引号感知
  切列；`gate_overall_tokens` 行长不足 / Overall 无 token 由静默 `continue`
  改为产出违规（轮 2 N9 建议的"丢行即违规"一并落地），返回值改
  `(tokens, violations)` 并在 `check_handoff_gate_echo` 合流。真实板与
  夹具双向实证见上。
- **F5（潜在缺陷）——闭合成立。** `check_track_discipline` 的短行分支
  从 `continue` 改为先记违规再 `continue`，副本实测六单元格活跃消耗行
  由 SILENT-PASS 变为响亮拒绝。
- **自查第四洞（多段 `WORK_ID_RE`）——独立复现成立。** 修复前
  `^(?:P1-[A-Z0-9]+-\d{3}|COORD-\d{3})$` 使 `P1-M3-BODY-001`、
  `P1-VLM-CAL-001`、`P1-VLM-SCOPE-001`、`P1-M3M4-SCOPE-002` 等多段
  AREA 的 ID 在引用侧永不执法；改 `P1(?:-[A-Z0-9]+)+-\d{3}` 后四路
  篡改全部被拒（上文探针）。这是与 F4 同类的静默免检，接受角色自查
  发现并同批修复、同批配必失败测试，处置得当。
- §4.4 R3 闭合四条件：条件 (3) 不触发——本批零触碰 `analyze_m3_body.py`、
  `preflight_reanchor_env.py`、`controller/run_log.py`。条件 (1) 讨论
  见 N14。条件 (2)（接受角色亲自 revert 复算）是接受角色的动作，本轮
  的 revert-rerun 是复核侧独立验证，不替代之；**F3/F4/F5 的正式闭合
  仍由接受角色按 §4.4 作出**。

## Findings（Round 3）

**F6 — CLASS_3：状态板 `Immediate next actions` 的轨道占用句仍写
"review round 2"。** `docs/current-status.md:213-216` 的 Track
discipline 段写 "the COORD-007 review round 2 takes one zero-consumption
slot"，而同文件交接行已改判 `REWORK_FIXES_LANDED_AWAITING_REVIEW_ROUND_3`、
上方 COORD-007 段亦写"**等复核轮 3**"。分级理由：轨道会计本身（1 消耗
+ 1 零消耗 + 1 空位）实测正确，未涉及数值/阈值/ID/判据/终态名，权威
待办在交接行与同节段落中无歧义，故属 R4 闭集中"已执行步骤的时态"，
不阻断。逐字替换补丁（同行数，不破坏折行）：

```text
--- 原 213-216
**Track discipline (COORD-003, amended by COORD-007 R8).** Only the
`P1-M3-BODY-001` user GO decision occupies the consuming slot; the
COORD-007 review round 2 takes one zero-consumption slot and the second
stays open with nothing authorized to fill it.
--- 改为
**Track discipline (COORD-003, amended by COORD-007 R8).** Only the
`P1-M3-BODY-001` user GO decision occupies the consuming slot; the
COORD-007 row (now with Acceptance for the §4.4 closure) takes one
zero-consumption slot and the second stays open with nothing to fill it.
```

**处置披露（须接受角色复判）**：本轮的状态板更新本身就改变了该句
陈述的事实（零消耗槽位由复核转交接受），按 AGENTS.md「交接文字必须与
现实一致……在同一批次就地修正」我在收工的状态板更新中**已就地应用
上述补丁**，而非留给下一个接手的角色。这与 R4「CLASS_3 由接受角色
复判后应用」存在边界重叠：该句不在 `controller/ Assets/ tools/ tests/
config/` 五路径内，且 `docs/current-status.md` 属复核角色写入白名单与
法定收工动作。若接受角色判定该应用越界，请直接回退该四行并按 R4 流程
重走；本条已完整披露，不构成隐藏改动。

CLASS_1：无。CLASS_2：无。

## Notes（续轮 2 编号）

- N11：提案 `COORD-007-…-reduction.md:184` 的 §5 R5 正文仍写"允许
  **任何角色**在只改……的单独提交里修复"。核为**提案原文**，与 R2 的
  两分支写法同例（分支选择记在接受轮与账本，不回改正文），接受轮 4 §A
  已逐字记录改法，活规则文件三处均已排除复核角色，故不作为缺陷。仅
  提示：单独阅读 §5 R5 会得到 F3 前的答案。
- N12（潜在，非本批引入）：Gate board 的 `M1`（milestone）行会被
  `gate_overall_tokens` 正常收进 token 表
  （`OPEN_AWAITING_SCENE005_STAGE_B`），但 `WORK_ID_RE` 匹配不到 `M1`，
  因此**任何交接行引用 `M1` 都不会被要求 echo**。与刚修的第四洞同类，
  但按 workflow §2 的 ID 文法 `M1` 不是 work ID，规则文本只约束
  "work ID"，故本轮不定级为缺陷。M1 的 Overall 是活门（closure 待
  用户授权），建议接受角色显式裁定：要么把里程碑行纳入 echo 文法，
  要么在 BC-C7-10 的解析契约里写明里程碑行不在 echo 范围。
- N13：轮 2 N9 的第二肢（"无 gate 行不触发"）保留；另实测把 work ID
  写进更长的反引号跨度（如 `` `docs/reviews/P1-EVAL-001.md` ``）或写成
  裸文本同样不触发 echo。均属 BC-C7-10 定义的解析格式，本轮继续附议为
  设计选择，不作缺陷。
- N14（R3 条件 (1) 的适用性）：本批四条回归测试的夹具是 `tempfile` 里
  手写的合成状态板（5 列），不是真实 `docs/current-status.md`（gate 7
  列 / 交接 8 列）的字节副本。`check_docs.py` 的"生产写盘函数"不存在，
  轮 2 的闭合绑定要求的是"真实**形状**的 `C_track|geom` gate 行"，该
  要求已满足，故不判违反条件 (1)。但值得记录的事实是：**第四洞是接受
  角色跑未提交的真实板探针发现的，不是套件抓到的**；套件全绿与真实板
  静默逃逸可以并存正是 F4 的失效模式。建议后续批次（R10/R11 输入）加
  一条消费仓库真实状态板的冒烟断言（如"每条 gate 行都产出 token、每条
  交接行单元格数等于表头"），把这一类漂移变成机器可抓。
- N15：全空单元格行与全 `-` 行仍被 `is_separator_row` 在 F5 的 fail-closed
  之前静默跳过（副本实测 8 单元格全空行 SILENT-PASS）。该类行不携带
  work ID / Status / Consuming，无法夹带活跃交接或过期 echo，且为修复前
  既有行为，非本批引入，不作缺陷。
- N16：轮 2 N7 复现——全套测试在新副本内仍依赖主树未跟踪 `runtime/`
  资产（`test_scene006_probe` 29 项失败/错误全由此产生，复制后 517 全绿）。
  仍应作为 R10/R11 批次证据设计的输入。

## UNITY_NA 处置（Round 3）

本批（`--infra-fix` 提交 + 协调批次 + 文档记录）零运行时行为、零 Unity
门适用，接受轮 4 未声称 `UNITY_NA`；本轮**附议**其未声称的处置，未签发
任何 `UNITY_NA`。区间内亦无任何 Play/采集 ID/配额/API 消耗，
`P1-M3-BODY-001` 的 GO 轨道未被本批触动——实测状态板消耗性活跃交接
仍恰为 BODY-001 一条。

## Verdict（Round 3）

**Round 3: PASS_WITH_NOTES（candidate `544cd18`）。**

轮 2 的三条 CLASS_2 全部在一次性副本内独立验证为真实闭合：F3 三文件
定点复看一致（附议 `NOT_MECHANIZABLE` 定级）、F4 与 F5 的绑定回归测试
逐名落地且 revert 后确实必失败、真实板篡改探针由修复前 7 路静默通过
变为 11/11 响亮拒绝；接受角色自查发现的第四洞（多段 `WORK_ID_RE`）
同批修复并配必失败测试，独立复现成立。授权链、`--infra-fix` 路径闭集、
协调批次账本凭据、区间 20 路径归因、focused 26/26 与全套 517 绿全部
通过。本轮唯一 finding 为 CLASS_3（F6，已披露就地应用），不阻断。
本 verdict 不构成任何执行授权，也不代替接受角色按 §4.4 四条件（含其
亲自 revert 复算）对 F3/F4/F5 作出的正式闭合；R10/R11、R12 仍未授权。

passed_candidate: 544cd18f425f6d0391d7d74368546c9eba527391

## 边界自查（Round 3）

本会话未修改任何实现文件——`controller/`、`Assets/`、`tools/`、
`tests/`、`config/` 主树零字节改动。revert-rerun、篡改探针沙箱与未跟踪
`runtime/` 资产复制全部发生在一次性副本
`.claude/worktrees/review-COORD-007-r3` 内，副本已按收工纪律
`git worktree remove --force` 删除。主树写入仅本复核文件与
`docs/current-status.md`；`python3 tools/check_role_writes.py --role
review` 通过。

过程披露：本轮记录初稿因 shell 工作目录停留在一次性副本内，先写进了
副本的同名文件并随副本删除，主树当时 `git status --porcelain` 为空
（零主树写入）；本节文字为在主树重写的同一内容。这反过来实证了副本
隔离纪律有效：所有副本内动作（含误写）都随副本消失，未污染主树。
