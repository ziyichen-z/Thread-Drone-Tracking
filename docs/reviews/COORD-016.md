# COORD-016 独立复核（代拍放宽：D1 非递增+每提案上限 3、D7 预注册数值按推荐、启用 D2b：研究轨道落地停点）

角色：复核（review，Claude Code 子代理，Opus 5.5，新鲜上下文；档位不低于落地批次执行者 Opus 5.5）。拉起方式：supervisor 按 COORD-015 §3.7 派发，
`Dispatch-Id: COORD-016-R1@落地-20260927T192023Z-48fe`，`requested.round: R1@落地`。轨道：提案抬头无 `Workflow: engineering-v1`，
D3 接受裁定写明研究轨道 → 按 `docs/collaboration-workflow.md`。零消耗：不启动模型服务、不跑 Unity/Play、不下载、不签信封、不启用任何代拍类。

## R1@落地（2026-09-27）

### §0 候选、基线与开轮资格

- `round_candidate: 8f0f708c283a8f7969f793efa041e32a41c3e71b`
- 全量 diff 基线 = D3 接受提交 `2cbe3b2a76f0465c77a5f581b8e1c999554e0289`（本文件此前不存在，无 `passed_candidate`；与 C1@落地 首次核对所读范围起点一致）。
  `git diff 2cbe3b2..8f0f708` 共 31 个变更文件，已逐文件核对；其中 `docs/phase1-single-drone-design.md` 与
  `docs/proposals/P1-ENG-FAST-002-*.md` 只由 `P1-ENG-FAST-002` D2 接受提交 e118e72 改动，不属本项，核对其未被 COORD-016 提交触及。
  COORD-016 自身提交：落地三笔 8c08220/41371b2/b968e73、补充同步 b4b57d0/728a0fd、C1-1 修复 04ccfc6/8f0f708。
- 开轮资格（workflow §4.4）：PLAY_GOVERNING 上 diff 非空（`tools/check_ledger.py`、`tools/check_route_text.py`、
  `tools/make_supervisor_drill.py`、`tests/test_check_ledger.py`、`tests/test_check_route_text.py`、`tests/test_supervisor_drill.py`）→ 开轮。
- 停点自证（workflow §4.3.1）：本批没有 `docs/evidence/` 下的具名自证小节（见 §3 观察 1）；本人按四项直接核实：(1) 范围冻结——
  改动文件恰为提案 §3 表所列加两批用户授权的补充同步与 C1-1 修复，无范围外文件；(2) 相称测试——本人重跑 focused 全绿（下）；
  (3) Unity 不适用；(4) 状态板、候选与未决风险（C1@落地「预复核关注项」）已更新。条件实质成立，不给 `REVIEW_BLOCKED`。
- 复核副本：`.claude/worktrees/review-COORD-016`（detach 于候选）；测试树哈希 `HEAD:tests` = `120989375b480052065aa336aa755266ffc240a5`，
  `HEAD:tools` = `6fa604e50fe638e5cfade2fa648256683d189d53`。
- 重跑（副本内，输出写会话临时文件、只回显摘要；Python 3.9.6）：
  - focused：`python3 -m unittest tests.test_check_ledger tests.test_check_route_text tests.test_supervisor_drill` → `Ran 101 tests … OK`。
  - A3：`python3 tools/check_route_text.py --spec docs/evidence/COORD-016-route-spec.json` → exit 0，69/69；首行基线
    `43aba45f05543fe003041c6458a0a8c42d2735e5` = 首个 `COORD-016 协调落地` 提交 8c08220 的首父（BC-5 成立，不是末个同前缀提交 b968e73 的首父）；
    除首行外与 `docs/evidence/COORD-016-route-check.log` 逐行相同。
  - 真实账本：`python3 tools/check_ledger.py --root <副本>` → 「账本机检通过」。
  - BC-6 / R2-1 修前红/修后绿：把 `tools/make_supervisor_drill.py` 换回 2cbe3b2 版本跑
    `tests.test_supervisor_drill.DrillFixtureTests.test_inject_open_items_targets_round_section` → 红，但红因是签名 `TypeError`（旧函数无 `round_no`
    参数），不能证明行为；本人另以探针把 `inject_open_items` 替换为旧「追加到文件尾」语义并接受第三参数 → 仍红（`_round_open_items(lines, 1)`
    报 `### D1` 节内 0 行），行为性红成立；恢复候选版本 → 绿。
  - C1-1（BC-5）修前红/修后绿：`tools/check_route_text.py` 换回 04ccfc6 首父版本跑 `tests.test_check_route_text` → 2 failures
    （`test_rewritten_in_place_but_copied_elsewhere_fails`、`test_cross_line_sentence_rewritten_in_place_but_copied_elsewhere_fails`），恢复 → 绿，
    与 `docs/evidence/COORD-016-C1-1-red.log` 一致。
  - 全套九个 errors 的基线同集（C1 关注项）：`COORD-016-tests.log`（落地）与 `COORD-016-C1-1-tests.log`（C1-1 后）列出的九个 `ERROR:` 完全相同；
    本副本 `import cv2`、`import numpy` 均 `ModuleNotFoundError`；九个模块（`test_benchmark_reanchor`、`test_detector_scouting`、
    `test_rate2_protocol`、`test_rate3_difficulty_audit`、`test_rate3_protocol`、`test_rate_study`、`test_scene004_gate0_probe`、
    `test_scene004_scouting`、`test_scene006_probe`）不在候选 diff 内，且不导入本批三个工具。**环境错误、基线同集，核实成立。**
    落地日志另有 1 failure（`test_dist_data_round4` 读主树 `runtime/frames` 残留），C1-1 日志已无，同属环境、与本批无关。

### §1 逐文件核对摘要

| 组 | 文件 | 结论 |
|---|---|---|
| 终局句（§2.3 九处 + BC-4） | workflow §4.4 两处（轮 3 终局句、阻断 finding 闭合段「回归核实」句）；`docs/roles/review.md` L66/L90；`AGENTS.md` L209/L277；`docs/roles/acceptance.md` L95；`.claude/commands/accept.md` L26；`.claude/commands/review.md` L17/L44 | 逐字与 §2.3 表一致；review.md L66 把「本节」改写为「workflow §4.4」属必要的指代调整。BC-4 要求的「下一轮」在无新轮回归通道的适用方式已写入 workflow 闭合段。 |
| D1 句（§2.1 + 补充同步两批） | workflow §4.2、`docs/engineering-workflow.md` §3、`docs/proposals/README.md`、`docs/roles/{acceptance,ideation}.md`、`.claude/commands/{accept,supervisor}.md`、`docs/roles/supervisor.md` D1 行与判据段 | 与 §2.1 与 BC-1 一致；仓库内已无「残留数严格递减」旧句；仓库外 `~/.codex/prompts/codex.md` 只读核对含 D1 新句与 D7 两句。 |
| supervisor 细则 | `docs/roles/supervisor.md`：D1/D2b/D7 行、D7 预注册判据段、永不代拍例外句、信封注释、必填字段与失败关闭、边界表复核行 | 与 §2.2–2.4 一致；§2.4 所列不变部分（D2a–D6、SUB 行，永不代拍其余各句，否决窗口、撤销、`at:` 全序、F1–F10、单写者段）在 diff 中未被触及。边界表复核行「对方的变化」格残留旧叙述，见 R1-2。 |
| 账本 | `docs/authorizations.md` | 唯一删改行是文件头 D1 字段句的续写（加 D7 三字段）；其余为 COORD-016 新增授权条目，未改任何既有用户原话（A5 成立）。 |
| 工具 | `tools/check_ledger.py` | D1 `now > prev` 拒绝、按 work ID 累计 >3 拒绝（含后被否决条目）；D7 同源快照（待提交读 HEAD、历史读 commit(E) 首父且 `precheck_head` 须相等）、`Status: ACCEPTED`、唯一 `d7_range`/`d7_recommend`、条款格与 `bc=` 行绑定、`kind` 闭集、非 D 轮节、`decision`/`range` 逐字、Decimal 区间比较均已实现；**闭集元素与闭集推荐值未校验数值字面**，见 R1-1。 |
| 工具 | `tools/check_route_text.py` | 规格闭集（expected 计数 + closure 标记 + unchanged 原位）与 BC-5 一致；原位判据边界的适用性见 §3 观察 2。 |
| 工具 | `tools/make_supervisor_drill.py` | `inject_open_items(proposal, items, round_no)` 按唯一 `### D<n>` 节末插入、标题缺失或重复 `ValueError`；夹具提案加 D7 样例行。R2-1 修复成立（§0 红绿）。 |
| 测试 | `tests/test_check_ledger.py`（D1Tests 10 例、D7Tests 21 例）、`tests/test_check_route_text.py`（13 例）、`tests/test_supervisor_drill.py`（+2 例、1 例改写） | 均在真实临时 git 仓库上走 `check_precommit`/`check` 生产入口；删除的只有旧「严格递减」两例，由持平/增加用例替代；A2 所列反例各有具名用例。缺闭集语法反例（R1-1）。 |
| 证据 | `COORD-016-{red.log,tests.log,route-spec.json,route-check.log,drill.md,C1-1-red.log,C1-1-tests.log}` | 指针可达，数字与本人重跑一致；`drill.md` 是合成演练叙述，驱动脚本未入库，作 A4 artifact 接受（见 §3 观察 4）。 |
| 状态板/提案/调度日志/changelog | `docs/current-status.md`、提案「Contract conformance」、`docs/evidence/supervisor-dispatch.jsonl`、`docs/workflow-changelog.md` | COORD-016 提交未改任何 `P1-*` Gate 行、交接行门值或 verdict（逐提交 diff 核对）；changelog 三行与落地内容一致。 |

### §2 Findings

| 编号 | 分级 | 依据列 | 位置 | 内容 | 闭合绑定 |
|---|---|---|---|---|---|
| R1-1 | CLASS_2 | `BC-2` | `tools/check_ledger.py` `_d7_parse_set()`（闭集分支只查空项/空格/重复）与 `_d7_errors()`（数值字面只在区间分支校验推荐值） | 提案 §2.2「语法闭集」规定数值字面匹配 `-?[0-9]+(\.[0-9]+)?`（不带单位、不带指数，单位写在 BC/AC 正文），`docs/roles/supervisor.md` 落地句同写「区间端点与值匹配 …」；D7 只覆盖门值/最小样本量/阈值/容差四种数值。工具对闭集形式不校验元素与推荐值是否为数值字面，失败开放。探针（副本内以 `tests.test_check_ledger` 的 `d7_proposal`/`d7_entry` 夹具走 `check_precommit`）：`d7_range: n1 in {200帧, 400帧} kind=最小样本量 bc=BC-3` + `d7_recommend: n1 = 400帧` → 错误列表为空（通过）；`{2e2, 4e2}` + `4e2` → 通过；同样带单位的区间 `[200帧, 400帧]` → 正确拒绝「片段语法不合」。可达：触发状态是提案 §2.2 点名的语法闭集，生产入口（pre-commit / 历史复判）读任何已接受提案都会走到；BC-2「结构有疑义回用户」要求拒绝。 | 具名回归 `tests.test_check_ledger.D7Tests.test_d7_closed_set_non_numeric_rejected`（修复前必失败）：真实临时仓库、`check_precommit` 入口，断言闭集元素带单位（`{200帧, 400帧}`/推荐 `400帧`）与带指数（`{2e2, 4e2}`/推荐 `4e2`）各被拒绝，且合法数值闭集 `{200, 400}` 仍通过。修复限 `_d7_parse_set`/`_d7_errors` 对闭集元素与闭集推荐值加 `D7_NUMBER_RE` 全匹配；如同步澄清 `docs/roles/supervisor.md` 语法句（「区间端点、闭集元素与推荐值均匹配 …」），须在同一授权批次内。 |
| R1-2 | CLASS_3 | `BC-4` | `docs/roles/supervisor.md` L60 边界表「复核」行「对方的变化」格 | 该格仍写「轮 3 终局句按 U1（=D，原句不变）」，而本批已按 §2.3 改写复核侧九处终局句、D2b 改为信封列入即生效，同一行「做」格已写「接 D2b（信封列入即生效）」；属已执行步骤的时态残留，不驱动工具，操作员以代拍类表 D2b 行为准，行为不因此不同。提案 §2.3 表对 L60 只点名改「做」格，实现按字面执行，非实现越界。 | 不阻断。逐字替换补丁（`docs/roles/supervisor.md` 属工作流基础设施，由下一次用户授权的协调批次应用）：把 `轮 3 终局句按 U1（=D，原句不变）` 替换为 `轮 3 终局句按 COORD-016 §2.3 改写（决策信封 D2b 在效时一次定向返工，轮 4 终局）`。应用时须同步 `docs/evidence/COORD-016-route-spec.json` 的 S01 预期或 closure（该格改后含「轮 4 终局」，否则 closure「轮 4 终局」会计数不符）。 |

### §3 非阻断观察（不计 finding）

1. **自证小节缺失**：COORD-015 落地停点有 `docs/evidence/COORD-015-self-attestation.md`，本批没有对应的 §4.3.1 具名小节，交接行只指向证据文件。
   本人已在 §0 直接核实四项条件；建议后续协调批次到停点时照 AGENTS「复核强制停点」补具名小节。
2. **`in_place()` 原位判据边界（C1 关注项）**：本人探针（副本内直接调用 `in_place`）——原位改写 + 文件尾补旧句 → 判非原位（正确）；改写后移到下一节
   （标题行未变）→ 判非原位（正确）；原行改写、邻近另一改动块补句 → 判非原位（正确）；同一改动块内紧邻新行补旧句、同行内挪到行尾、
   四行整块改写中句子从首行挪到末行 → 均判原位。后三种情形结果文件都可解释为「不变句逐字未动、只改了其前后文字」，且句子仍在同一对未改锚行
   （标题/未改行）之间，只看结果文件的检查无法区分；§2.4 不变句本身的逐字漂移、删除、复制与跨锚移位都会非零退出。本人认为该边界满足 BC-5
   「不变句漂移以非零退出」的字义，**附议其适用性**。
3. **规格闭集覆盖**：closure「残留数非递增」只列四个文件，不含补充同步第 2 批的 `docs/engineering-workflow.md` 与 `docs/proposals/README.md`
   （这两处由 S08/S09 的 expected 计数单独约束，别处新增同句不会被闭集捕获）；§2.4 所列「否决窗口、撤销、`at:` 全序、F1–F10、单写者」等段
   未进 unchanged 规格。本人已用候选 diff 直接核对这些段本批未改（§1），A3 在本候选成立；规格作为日后回归检查的覆盖面有限，供接受角色知悉。
4. **A4 演练**：`COORD-016-drill.md` 的驱动脚本与夹具仓库在会话临时目录、未入库，四段结论不可由第三方原样复跑；D2b 的开轮资格与回归核实判定
   无专用机检，计数只靠 `counter_key` 逐字重复拒绝（写法不同的计数键不会被拦）。二者均已在该文件如实披露，符合 BC-4 的 artifact 证明方式。
5. **落地全套日志路径**：`COORD-016-tests.log` 内路径为 `~/TetheredDroneTracking/…`，与本机主树 `~/…` 不同；该日志已被
   C1-1 日志取代，不影响本轮结论，仅记录。
6. **BC-6 / R2-1**：修复与具名回归经本轮修前红（行为性）/修后绿核实成立。R1-1 的修复不应触及 `tools/make_supervisor_drill.py`；
   按 BC-6，账本 `docs/implementation-status.md` COORD-015/R2-1 由接受角色改 `CLOSED`，建议在本停点复核通过后一并处理，以免返工回归。

### §4 `UNITY_NA` 附议

本工作项只改工作流规则文件、账本机检/路由检查/夹具工具与其测试和证据，不触及 `controller/`、`Assets/`、`config/`、运行时协议或指标；
Gate board Unity 列 `N/A`（流程提案）本人**附议**。此附议只覆盖 Unity 维度，不构成 `DONE` 结论。

### §5 Verdict

**`REWORK_REQUIRED`**（本停点第 1 次）。阻断：R1-1（CLASS_2，`BC-2`）。R1-2 为 CLASS_3，附补丁，不阻断。
BC 逐条：BC-1 满足；BC-2 不满足（R1-1）；BC-3 满足；BC-4 满足（R1-2 为文档残留，不影响）；BC-5 满足（§3 观察 2 附议边界）；BC-6 核实成立（§3 观察 6）。
路由：CLASS_2 直接交实现角色，无需接受角色复判。`tools/check_ledger.py` 与 `tests/test_check_ledger.py` 属工作流基础设施，修复须走
AGENTS「共享状态更新」的 `--infra-fix` 例外（非复核角色，只改 `tools/check_*.py` 与 `tests/test_check_*.py` 的单独提交，贴出本文件 R1-1 的探针输出作失败证据）
或用户授权的协调批次；修复直接回复核 `R2@落地`，不经核对轮，R2 以 R1-1 具名回归修前红/修后绿核实闭合。
本轮无未改动行上的 `上轮漏检`，不写 `blocks_consuming_gate`。

边界自查：本会话只写本文件与 `docs/current-status.md`；复核副本内的临时替换已 `git checkout` 恢复，副本收工删除；未修改任何实现文件。

## R2@落地（2026-09-27）

增量轮（本停点第 2 轮）。拉起方式：supervisor 按 COORD-015 §3.7 派发，`Dispatch-Id: COORD-016-R2@落地-20260927T212715Z-044f`，`requested.round: R2@落地`；
角色同 R1（复核，Claude Code 子代理，Opus 5.5，新鲜上下文；档位不低于 R1-1 修复执行者 Opus 5.5）。轨道仍为研究轨道。零消耗。

### §0 候选、修复触及行与重跑

- `round_candidate: 41004363eccd4de0eeda354049ce6ea359876a05`
- 上一复核轮候选 = R1 `round_candidate` `8f0f708`；本文件此前无 `passed_candidate`，全量基线仍为 `2cbe3b2`。
- `git diff 8f0f708..4100436` 共 7 文件，逐文件核对：
  - 实现改动只有 R1-1 修复提交 `6981959`（`--infra-fix`）：`tools/check_ledger.py` +11/−7、`tests/test_check_ledger.py` +28/−0，恰为 AGENTS「共享状态更新」例外允许的两类路径，
    提交单独、不含证据产出，提交信息贴有修前失败输出；用户授权见账本 09-27「COORD-016 — 用户选 R1-1 修复路径 A…」（`13190eb`）。
  - 其余为非实现文件：`docs/current-status.md`（`4100436` 交接）、`docs/evidence/supervisor-dispatch.jsonl`（派发登记）、`docs/authorizations.md`（`13190eb` 本项路径 A 代录与 `b146aed`
    `P1-ENG-FAST-002` 代录，均为新增条目，未改既有原话）、`docs/proposals/COORD-016-delegation-loosening.md`（`00b79f9` 接受角色 C1 第二次核对表，非实现）、本文件 R1 轮。
- 开轮资格：PLAY_GOVERNING 上 diff 非空（`tools/check_ledger.py`、`tests/test_check_ledger.py`）→ 开轮。
- 复核副本 `.claude/worktrees/review-COORD-016`（detach 于候选）；`HEAD:tests` = `3b7df94865292ae35d2c37acbb73f566a422774a`，`HEAD:tools` = `07cceb56ce973d8681630faf3e74ca020033b1a2`；Python 3.9.6。
- focused：`python3 -m unittest tests.test_check_ledger tests.test_check_route_text tests.test_supervisor_drill` → `Ran 102 tests … OK`（R1 为 101，+1 为本具名回归）。
- 真实账本：`python3 tools/check_ledger.py --root <副本>` → 「账本机检通过」，exit 0。
- R1-1 修前红/修后绿（副本内 `git show 8f0f708:tools/check_ledger.py > tools/check_ledger.py` 单跑具名回归，再 `git checkout --` 恢复，副本复核后干净）：
  修前 `FAILED (failures=3)`——子例 `{200帧, 400帧}`/`400帧` 与 `{2e2, 4e2}`/`4e2` 错误列表为空（**行为性红**，即 R1 探针所示失败开放）；子例 `{200, 400}`/`400帧` 修前已被
  「推荐值不在闭集」拒绝，只因断言特定原因文本而红（文本性红，不作闭合依据）；修后 `OK`，合法 `{200, 400}`/`400` 子例断言错误列表为空。

### §1 修复触及行核对

| 位置 | 结论 |
|---|---|
| `_d7_parse_set()` 闭集分支 | 新增元素全匹配 `D7_NUMBER_RE`（`-?[0-9]+(?:\.[0-9]+)?`，str 模式下 `[0-9]` 只匹配 ASCII），不合即 `None` → 「片段语法不合」。在空项/空格检查之后、重复检查之前，区间分支不变。本人直接探针：`{-1, 0.5, 2}`、`{400}`、`{200 , 400}`、`{200,400}` 通过；`{+1, 2}`、`{1., 2}`、`{1e3}`、全角数字、`{}`、`{200, 200}` 拒绝——与提案 §2.2 语法闭集一致，无过度拒绝。 |
| `_d7_errors()` 推荐值 | 数值字面检查从区间分支提到分支前，区间与闭集同查；非数值推荐值报「推荐值不是数值字面」并跳过成员判定，数值推荐值再按 Decimal 区间 / 逐字闭集判定。与修前相比只多拒、不少拒（`parsed is None` 时非数值推荐值现在也多报一条）。 |
| 模块 docstring | 同步写明「区间端点、闭集元素与推荐值均须为数值字面（R1-1）」，与代码一致。 |
| 具名回归 | 走真实临时 git 仓库与 `check_precommit` 生产入口（`init_d7`/`stage_d7`/`precommit_errors`），覆盖 R1 闭合绑定要求的带单位、带指数两类拒绝与合法数值闭集通过，另加数值闭集 + 带单位推荐值。 |

修复触及行上无新 CLASS_1/2，无 `RED_LINE`；未改动行上无 `上轮漏检` CLASS_1/2，不写 `blocks_consuming_gate`。

### §2 Findings

| 编号 | 状态 | 说明 |
|---|---|---|
| R1-1 | **闭合** | 具名回归 `tests.test_check_ledger.D7Tests.test_d7_closed_set_non_numeric_rejected` 修前行为性红 / 修后绿经本人副本内核实；BC-2 转为满足。 |
| R1-2 | 未变（CLASS_3，不阻断） | `docs/roles/supervisor.md` L60 残留与 R1 所附逐字补丁仍待下一次用户授权的协调批次应用（须同步 route-spec S01）；本轮不改分级。 |

本轮无新 finding。

### §3 非阻断观察（不计 finding）

1. R1 闭合绑定中「如同步澄清 `docs/roles/supervisor.md` 语法句」为可选项，本修复未做（`--infra-fix` 不得改 `docs/roles/`）。该句现写「区间端点与值匹配 …」，
   工具比该句字面更严但与提案 §2.2（语法闭集）一致；可与 R1-2 在同一协调批次一并澄清为「区间端点、闭集元素与推荐值均匹配 …」。
2. 闭集按字面判重，`{0.70, 0.7}` 作为两个不同元素通过语法（数值等价的字面各算一个）；这与「闭集逐字比较」「decision 逐字 = 推荐值字面」的既定语义一致，
   不影响成员判定正确性，只供接受角色预注册时知悉。
3. R1 §3 观察 1–5 本轮未变，仍供接受角色知悉；BC-6 / COORD-015 R2-1 的账本状态按派发范围不在本轮，由接受角色处置。

### §4 `UNITY_NA` 附议

本轮修复只动账本机检工具与其测试，不触及 `controller/`、`Assets/`、`config/`、运行时协议或指标；Gate board Unity 列 `N/A` 本人**再次附议**。此附议只覆盖 Unity 维度，不构成 `DONE` 结论。

### §5 Verdict

Verdict: PASS_WITH_NOTES
passed_candidate: 41004363eccd4de0eeda354049ce6ea359876a05

R1-1 闭合（具名回归修前行为性红/修后绿，副本内核实）；focused 102 OK；真实账本机检通过；修复触及行无新 CLASS_1/2，无 `RED_LINE`。BC-1…6 全部满足（BC-5 边界附议见 R1 §3 观察 2，BC-6 红绿见 R1 §0）。
Notes：R1-2（CLASS_3 补丁待协调批次）、§3 观察 1–3。归因按依据列机械派生：R1-1 `BC-2`，实现侧错误，非合同缺口。
交接受角色做最终处置（COORD-015 R2-1 账本按 BC-6 改 `CLOSED`、R1-2 补丁去向、`DONE` 判定），轮次由 supervisor 调度。

边界自查：本会话只写本文件与 `docs/current-status.md`；副本内对 `tools/check_ledger.py` 的临时替换已 `git checkout` 恢复，副本收工删除；未修改任何实现文件。
