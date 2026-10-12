# COORD-015 独立复核（supervisor 接力调度、事实核查与有界代拍：研究轨道落地停点）

角色：复核（review，Fable 池，Claude Code 子代理，新鲜上下文）。拉起方式：用户直接指挥、构思会话代为派发（账本 2026-09-26「用户指示：完成 COORD-015，由构思会话拉起 Fable 复核子代理做 `R1@落地`」）；非 supervisor §3 派发，无 `Dispatch-Id`。零消耗：不启动模型服务、不跑 Unity/Play、不下载、不生成正式 ID、不签信封、不启用 supervisor、不真实派发任何角色。

## R1@落地（2026-09-26）

### §0 候选、基线与开轮资格

- `round_candidate: 2028832b96f1a5454fb63aad992559e873f988cc`
- 全量 diff 基线 = 落地授权入账提交 `bcc2c68e67d0ea51c6ea3d9a8510f2851529d8ba`（本文件此前不存在，无 `passed_candidate`，基线按派发字段取）；`git diff bcc2c68..2028832` 共 45 个变更文件，已逐文件核对。另核对本批 C2 文档提交 `4044aaf3892ff5d9e013411f788aa66526967b81`（只改状态板与提案「Contract conformance」，无实现改动）。
- 开轮资格（review.md 第 0 条 / workflow §4.4）：PLAY_GOVERNING 集合上 diff 非空（`tools/check_ledger.py`、`tools/check_role_writes.py`、`tools/githooks/pre-commit`、`tools/make_supervisor_drill.py`、`tests/test_check_ledger.py`、`tests/test_check_role_writes.py`、`tests/test_supervisor_drill.py`）→ 开轮。
- 停点自证（workflow §4.3.1 四项，`docs/evidence/COORD-015-self-attestation.md`）核实：(1) 范围冻结成立（§9.2 闭集文件均在候选内，本批只改两处工具函数与测试/证据）；(2) 相称测试：本人重跑 focused 82 例 OK（见下）；全套 10 项失败归因本人复核成立——副本内 `import numpy`/`import cv2` 均 `ModuleNotFoundError`（9 个 ERROR 全是 loader 导入失败），`test_dist_data_round4.RealArchiveClosureTest.test_zero_unmatched_and_zero_multi_matched_jpg` 在副本内 `OK (skipped=1)`（主树 `runtime/frames/` 残留所致，属环境）；失败名单不含本项任何测试，也不导入本项改动文件；(3) Unity 不适用；(4) 状态板、候选与风险已更新。自证条件成立，不判 `REVIEW_BLOCKED`。
- 复核副本：`.claude/worktrees/review-COORD-015`（detach 于候选）；测试树哈希 `HEAD:tests` = `f384c948ef976b221c492f3aca7e00d485edd7e5`，`HEAD:tools` = `d7b034e80a0f7ffc5acbf9b67932facd2b4d4d53`。
- 重跑（副本内，输出写文件只回显摘要）：`python3 -m unittest tests.test_check_ledger tests.test_check_role_writes tests.test_supervisor_drill` → `Ran 82 tests … OK`（与 `docs/evidence/COORD-015-focused-tests.log` 一致）；`python3 tools/check_ledger.py --root <副本>` 对真实账本 → 「账本机检通过」。本轮为首轮，无修前红/修后绿义务；下文每条阻断 finding 均附本人在副本内以候选代码复现的探针结果（探针脚本在会话临时目录，未入库、未改任何实现文件）。

### §1 逐文件核对摘要（45 文件）

| 组 | 文件 | 结论 |
|---|---|---|
| 规则/入口 | `AGENTS.md`、`CLAUDE.md`、`docs/collaboration-workflow.md`、`docs/engineering-workflow.md`、`docs/proposals/README.md`、`docs/workflow-changelog.md`、`docs/phase1-single-drone-design.md`、`docs/roles/{supervisor,acceptance,implementation,review,ideation,chore}.md`、`.claude/commands/{supervisor,accept,chore,codex,fable,implement,review}.md`、`.cursor/commands/coding.md`、`.cursor/rules/implementation-role.mdc` | 与提案 §2–§7、§9.2/§9.3 一致；U1=D/U2=B/U9=B 位置原句逐字保留；AGENTS L227 原句「视为 0；任何越界回到用户。」逐字保留、行尾追加为 §9.2 明文授权的红线句，本人裁定符合 §9.3「不改」（句未改）。`docs/roles/supervisor.md` 全文与提案 §2–§6 逐节对照无偏差（尾注形态已统一为 `Role-Check: <role> pass`）。 |
| 工具 | `tools/check_role_writes.py`（supervisor allow/deny，U7=B）、`tools/githooks/pre-commit`（先 `check_ledger.py` 再 `exec check_docs.py`，不新增 commit-msg 钩子）、`tools/make_supervisor_drill.py`（夹具生成、事件闭集、尾注生成器） | 与 §2.3、§9.2 一致。 |
| 工具 | `tools/check_ledger.py` | §5.4 字段闭集、§5.5 撤销/日期到期、§5.6 S 初态/虚拟提交/首父/X 永久化、BC-12 D1 字段均已实现；**四处与合同不符**，见 §2 finding R1-1…R1-4。 |
| 测试 | `tests/test_check_ledger.py`（41 例，真实临时 git 仓库）、`tests/test_check_role_writes.py`（+6 例）、`tests/test_supervisor_drill.py`（9 例） | A1 六例、A2 清单绝大多数各有一例、AD5-1 三例、D1 四例、失败关闭五例均对准条款；覆盖缺口见 §3。 |
| 账本 | `docs/authorizations.md` | 仅新增文件头格式段与 10 条 COORD-015 用户指示/授权条目，无删改行；无任何信封块条目（BC-10 成立：未首签、未启用）。 |
| 状态板/提案 | `docs/current-status.md`、`docs/proposals/COORD-015-supervisor-role-record.md`（含改名） | 非本项 Gate 行/交接行/Log 零改动（本人以 diff 复核，与 `COORD-015-A8a.log` 一致）；提案改动限回应索引、§0.3、§3.2 尾注、BC-13 与核对表。 |
| 证据 | `COORD-015-{self-attestation.md,focused-tests.log,tests.log,A1-redgreen.log,A4-grep.log,A8a.log,route-check.log,drill.md,drill-dispatch.jsonl,codex-exec.md}`、`a6-codex-exec-{run1,run2,neg}.log` | 指针可达、数字与文件一致（例外：R1-5）；A3(b)/A5/A7 为合成夹具结果并已如实标注；`~/.codex/prompts/codex.md` 本人只读核对：三要素 3、`Role-Check: acceptance pass` 存在。 |

### §2 Findings

| 编号 | 分级 | 依据列 | 位置 | 内容 | 闭合绑定 |
|---|---|---|---|---|---|
| R1-1 | CLASS_1 | `BC-12` | `tools/check_ledger.py` `_d1_errors()`（`rounds[round_no - 1]` / `rounds[round_no - 2]`） | D1 判据把提案文件中**第 n 个** `open_items:` 行当作「第 n 轮裁定」，即假定裁定节按 D1→Dn 自旧到新排列。仓库实际约定是**最新在上**（本提案「Codex review decision」下 D6→D1 自上而下；候选内已存在的两行 `open_items: none` 亦是「修订 3 审核」在「修订 2 审核」之上，`docs/proposals/COORD-015-supervisor-role-record.md:590,606`），BC-12/§5.1 定义的 r(n) 是「第 n 轮裁定节末」的行，不是文件序第 n 行。探针（副本内，按仓库约定最新在上布置 D1/D2 裁定节）：合法 r(1)=4→r(2)=2、条目 now=2/prev=4 → 被拒「与提案第 2 轮 open_items 行（4 项）不符」「未严格递减（4 >= 2）」；**非法** r(1)=2→r(2)=4、条目按工具的文件序写 now=2/prev=4 → **通过**（假接受）。结论随布局翻转，属改结论。`tests/test_check_ledger.py` `proposal()` 与 `tools/make_supervisor_drill.py` `inject_open_items()`（追加到文件末尾）都只构造自旧到新布局，故 A2/A5① 未暴露。 | 修复须把 `open_items:` 行绑定到 `round: D<n>` 对应的裁定节（如 `### D<n> …` 标题起至下一 `###`），与文件序无关；回归测试（生产路径 fixture = 与真实提案同布局的提案文本 + 临时 git 仓库）：`tests.test_check_ledger.D1Tests.test_d1_newest_first_layout_legal_passes` 与 `…test_d1_newest_first_layout_increase_rejected`，修复前必失败。分级为 CLASS_1，交接受角色复判（含裁定节标题/`open_items:` 落点的机读约定），修复归协调批次。 |
| R1-2 | CLASS_2 | `BC-5` | `tools/check_ledger.py` `_cross_errors()`（`env.work_id != entry.work_id and env.work_id != "全局"`） | 与 C2 关注项 (1) 一致：SUB 条目引用 `work_id=全局` 的执行信封不被拒绝。提案 §5.4 / `docs/roles/supervisor.md`「两类引用」要求 SUB 引用的执行信封 work ID **等于**条目 work ID（「串用他工作项信封」失败关闭项）。探针：`全局` 执行信封 + `W-001` SUB 条目 → 无错误。可达：账本为用户手写，`全局` 已是撤销条目合法的 work-id 取值。 | 回归测试 `tests.test_check_ledger.StructuralTests.test_sub_citing_global_envelope_rejected`，修复前必失败。 |
| R1-3 | CLASS_2 | `BC-5` | `tools/check_ledger.py` `order_key()`（返回 `(moment, date, pos)`） | §5.5 事件全序：`at:` 相同时按日期，再按**文件位置（同日靠上者更新）**。账本是最新在前（第 47 行 2026-09-25，第 3281 行 2026-07-30），故位置靠上 = 更新；工具以 `pos` 升序为更旧，与合同相反。探针：同一 `at:`、信封在条目**之上**（按合同信封更新 → 应拒「签发不先于代拍」）→ 工具**通过**；信封在下 → 工具拒绝。撤销同理反向。只在 `at:` 完全相同时触发，但为合同点名的判定规则。 | 回归测试 `tests.test_check_ledger.StructuralTests.test_same_at_upper_entry_is_newer`，修复前必失败。 |
| R1-4 | CLASS_2 | `IN_SCOPE_NO_BC` | `tools/check_ledger.py` `_entry_errors()`（`at:` 只对 delegated/revoke/envelope 必填） | 否决条目（`用户否决代拍：`）缺 `at:` 不报错，§5.6 否决窗口判定（`veto_at > veto_until`）被静默跳过——失败开放。`AGENTS.md`「共享状态更新」与账本文件头均写明「代拍、撤销与否决条目带 `at:` 等机读字段，由 `tools/check_ledger.py` 机检」。探针：`veto_until` 2026-09-22、否决条目日期 2026-09-30 且无 `at:` → 无错误。BC-5 只点名签发/代拍/撤销，故依据列记 `IN_SCOPE_NO_BC`（可达、范围内、无 BC 覆盖，阻断）。 | 回归测试 `tests.test_check_ledger.StructuralTests.test_veto_missing_at_rejected`，修复前必失败。 |
| R1-5 | CLASS_3 | `上游漏检` | `docs/evidence/COORD-015-drill.md` §4 | 叙述「`docs/evidence/COORD-015-tests.log`（`Ran 1634 tests` …）」与候选内该文件（`Ran 1640 tests`，本批重跑）不符；自证文件已说明差 6 例为本批新增测试，不驱动任何工具或操作员动作。 | 不阻断。逐字替换补丁（由 `docs/evidence/COORD-*` 写权角色下一次提交应用）：`- 全套测试：\`docs/evidence/COORD-015-tests.log\`（\`Ran 1634 tests\`，` → `- 全套测试：\`docs/evidence/COORD-015-tests.log\`（\`Ran 1640 tests\`，本批 C1 退回项修复后重跑；落地批次为 1634，差 6 例为本批新增测试，` |

### §3 非阻断观察（不计 finding，供修复与后续轮参考）

- 测试覆盖缺口（A2 清单）：决策信封块缺 `expires_at` 无用例（只测子额度块）；D1「与提案该轮/上一轮行不符」（now≠行内 ID 数）无直接用例；`test_stale_snapshot_p_x_e_rejected` 只断言非空错误列表。R1-1 的回归测试落地后前两项自然补齐。
- `_find_proposal()` 要求 `docs/proposals/<work_id>-*.md` 唯一；仓库现有 `P1-SCENE-006` 两个同前缀文件，D1 对此类工作项将失败关闭（可接受，但供接受角色知悉）。
- `MACHINE_RE` 对信封类条目把任何 `- <ASCII 键>: 值` 行当机读键（如 `- Play: 否`）报「未知机读键」，失败关闭；用户首签执行信封时须避免此类行，建议写入账本文件头提示（非本轮义务）。
- `first_commit_adding()` 以 `git log -S <标题>` 取 S/commit(E)：若信封标题是更早某条目标题的子串，S 会提前；失败关闭方向，注意标题唯一性。
- A3(b) 的 F 核查脚本只入库为证据附件，仓库无 F1–F10 运行时工具；F4 仅查反引号 `docs/` 路径、F5 仅查 `Ran N`，证明边界已由自证与 C2 如实披露，本人认可其作为 BC-3「可判、有区分力」的合成证据，但不构成运行时保证。
- `docs/evidence/COORD-015-drill.md` §3-4 记录被拉起角色 amend 并 `--force-with-lease` 改写已推送提交；现行规则未禁止，建议接受角色在首次真实启用前裁定是否禁止（否则 `candidate` 解析可能遇到远端历史改写）。

### §4 `UNITY_NA` 附议

本工作项为工作流基础设施（规则文件、账本机检工具、夹具生成器与测试），不触及 `controller/`、`Assets/`、`config/` 或任何运行时协议/指标；Gate board Unity 列 `N/A`（设计已接受）与自证第 3 项「Unity 不适用」本人**附议**。此附议仅覆盖 Unity 维度，不构成 `DONE` 结论。

### §5 Verdict

**`REWORK_REQUIRED`**（本停点第 1 次）。阻断：R1-1（CLASS_1，交接受角色复判并裁定 `open_items:` 落点的机读约定）、R1-2/R1-3/R1-4（CLASS_2）。修复路径：`tools/check_ledger.py` 与 `tests/test_check_ledger.py` 属工作流基础设施，须由用户授权的协调批次（或按 AGENTS「共享状态更新」的 `--infra-fix` 例外，单独提交并贴失败输出）执行，修复后直接回本角色 `R2@落地`，不经核对轮；R2 只核修复触及行、四条 finding 修前红/修后绿与 `RED_LINE`。C2 核对表 BC-5「不满足」结论本人确认；BC-12 由 R1-1 改判为不满足；其余 BC 的接受侧结论未见反证。本轮未修改任何实现文件；主树只写本文件与 `docs/current-status.md`。

## R2@落地（2026-09-26）

增量轮（本停点第 2 轮）。拉起方式同 R1：用户直接指挥、构思会话代为派发（账本 2026-09-26「用户授权 R1 返工协调批次（含接受复判 R1-1 与 `R2@落地`，构思会话代录）」第 (3) 项）；非 supervisor §3 派发，无 `Dispatch-Id`。零消耗（不启动模型服务、不跑 Unity/Play、不下载、不生成正式 ID、不签信封、不启用 supervisor、不真实派发）。

### §0 候选、基线与重跑

- `round_candidate: 91e05904a5127bcbf59f5f6d8151ca65668bf099`
- 修复触及行 = `git diff 2028832..91e0590`：9 文件（`tools/check_ledger.py` +41/−10、`tests/test_check_ledger.py` +84/−0、`docs/evidence/COORD-015-R1-redgreen.log`、`COORD-015-R1-focused-tests.log`、`COORD-015-drill.md`、`docs/proposals/COORD-015-supervisor-role-record.md`（BC-14/BC-15、C2 核对表、R1@落地 复判节）、`docs/authorizations.md`（仅新增 2 条用户指示/授权条目，无删改）、`docs/current-status.md`、`docs/reviews/COORD-015.md`（R1 轮本身））。全量 diff 相对 `bcc2c68` 共 48 文件，只用于核实声明范围：新增的 3 文件全是本批证据/授权/复核，无范围外实现改动。
- 复核副本 `.claude/worktrees/review-COORD-015`（detach 于候选）；测试树哈希 `HEAD:tests` = `8f24a0e65ec3d9383580a0bb33d8e99fb1e2e700`，`HEAD:tools` = `70bfc02b1502d73710f8516f4be7230fde30ea6c`。
- focused 重跑（副本内，输出写文件只回显摘要）：`python3 -m unittest tests.test_check_ledger tests.test_check_role_writes tests.test_supervisor_drill` → `Ran 88 tests … OK`（与 `docs/evidence/COORD-015-R1-focused-tests.log` 一致）；`python3 tools/check_ledger.py --root <副本>` 对真实账本 → 「账本机检通过」，退出码 0。
- 修前红/修后绿（本人在副本内 `git show 2028832:tools/check_ledger.py > tools/check_ledger.py` 后逐条单跑，再 `git checkout -- tools/check_ledger.py` 恢复，副本工作树复核后干净；不信日志数字）：

| 具名测试 | 修前（2028832 工具） | 修后（候选） |
|---|---|---|
| `D1Tests.test_d1_newest_first_layout_legal_passes` | FAILED（误拒：按文件序把「接受后修订 1 审核」的 `none` 当第 1 轮） | OK |
| `D1Tests.test_d1_newest_first_layout_increase_rejected` | FAILED（读数错：报「与第 2 轮行（4 项）不符」而非「未严格递减（4 >= 2）」） | OK |
| `StructuralTests.test_sub_citing_global_envelope_rejected` | FAILED | OK |
| `StructuralTests.test_same_at_upper_entry_is_newer` | FAILED（failures=2，两个子用例方向全反） | OK |
| `StructuralTests.test_veto_missing_at_rejected` | FAILED | OK |
| `D1Tests.test_d1_section_binding_fail_closed`（附加，BC-14 (3)） | FAILED（仅子用例 `no D2 heading` 失败，其余 4 个子用例修前也通过） | OK |

与 `docs/evidence/COORD-015-R1-redgreen.log` 结论一致。

### §1 R1 finding 闭合核实

| 编号 | 闭合结论 | 核实内容 |
|---|---|---|
| R1-1 | **已闭合** | `tools/check_ledger.py` 新增 `_round_open_items()` 与 `SECTION_END_RE`，`_d1_errors()` 改为按节取第 n/n−1 轮：标题 `^### D<n>(?![0-9A-Za-z])` 须恰好 1 行；节止于下一 `^#{1,3} ` 标题或文件尾（`####` 属本节）；节内 `OPEN_ITEMS_RE` 匹配行须恰好 1 行且为最后一个非空行；任一不成立即返回失败关闭错误；与文件序无关；非 `### D<n>` 节内的 `open_items:` 不参与计数。逐条对照 BC-14 (1)–(4) 无偏差；`round_no < 2` 仍先拒绝，`round_no − 1 ≥ 1` 成立。两条具名测试 fixture 与接受复判要求一致（`proposal_newest_first()`：最新在上、其上有含 `open_items: none` 的非 D 节、D2 内含 `####` 子节；increase_rejected 以 r(1)=2、r(2)=4、条目 now=2/prev=4 构造），走真实临时 git 仓库 + `check_precommit()` 生产路径。BC-12 结论由「不满足」改回满足（以 BC-14 落点）。 |
| R1-2 | **已闭合** | `_cross_errors()` 去掉 `and env.work_id != "全局"` 分支，SUB/D 类引用信封的 work ID 必须等于条目 work ID；具名测试用 `work_id="全局"` 的执行信封 + `W-001` SUB 条目，断言「串用他工作项信封」。C2 核对表 BC-5「不满足」的唯一依据由此消除。 |
| R1-3 | **已闭合** | `order_key()` 返回 `(moment, entry.date, -entry.pos)`，同 `at:`、同日期时靠上者键更大（更新），与 §5.5 一致；本人核对 `order_key` 的全部消费点（信封先于代拍 L426–427、撤销先于代拍 L442、`delegated` 排序 L385、撤销列表 L382/384）均为同一键的 `<` 比较，方向一致，无其它直接读 `pos` 做先后比较的位置（`pos` 另只用于 `_label` 行号）。具名测试两个子用例：信封在上（更新）→ 拒「签发不先于代拍」；信封在下 → 通过。 |
| R1-4 | **已闭合** | `_entry_errors()` 的 `at:` 必填集合加入 `"veto"`（`VETO_KEYS` 本已含 `at`）；缺 `at:` 报「缺必填 at:」失败关闭，否决窗口判定不再被静默跳过。与 BC-15 一致。 |
| R1-5 | **已闭合** | `docs/evidence/COORD-015-drill.md` §4 已逐字应用 R1 给出的替换补丁（`Ran 1640 tests`，本批 C1 退回项修复后重跑；落地批次为 1634，差 6 例为本批新增测试）。 |

### §2 Findings（本轮）

修复触及行上未发现 CLASS_1/2；无 `RED_LINE`（本项不触及 `controller/`、`Assets/`、`config/`，无真值路径）。以下一条在未改动行上，由修复落定的 BC-14 语义暴露，非阻断：

| 编号 | 分级 | 依据列 | 位置 | 内容 | 处置 |
|---|---|---|---|---|---|
| R2-1 | CLASS_2 | `SCOPE_GAP` | `tools/make_supervisor_drill.py` `inject_open_items()`（L74–76，未改动行）与 `_proposal()`（L135–143） | 夹具生成器把 `open_items:` 行**追加到提案文件末尾**，而 `_proposal()` 的 `### D1`/`### D2` 节自旧到新排列，追加行全部落在最后一节：探针（副本内）注入 r(1)=4 项、r(2)=2 项后，`_round_open_items()` 报「`### D2` 内 open_items: 机读行有 2 行」「`### D1` 内 0 行」——即该 helper 生成的夹具在 BC-14 语义下对 D1 代拍**失败关闭**（不会假通过）。范围判据：`inject_open_items()` 的唯一调用方是其自身单元测试 `tests/test_supervisor_drill.py::test_open_items_injection_matches_ledger_checker`（只断言行格式）；`docs/evidence/COORD-015-drill.md` §1 ① 的 `open_items:` 行由夹具内接受角色（Kimi）自行写入、非此 helper 生成；真实账本的 pre-commit 与派发守卫从不调用本生成器。故不可达于生产入口与已归档 A5 证据，标 `SCOPE_GAP`，路由接受角色记债（`docs/implementation-status.md`「范围外已知缺陷」）。修复方向（供后续批次）：`inject_open_items(proposal_path, items, round_no)` 把行插到 `### D<round_no>` 节末，并同步其单元测试。 |

### §3 非阻断观察（不计 finding）

- `test_d1_section_binding_fail_closed` 的 5 个子用例中只有 `no D2 heading` 在修前失败；`D10 is not D1` 子用例的断言（`"open_items" in e or "### D" in e`）过宽——即使标题正则缺 `(?![0-9A-Za-z])` 边界，`### D10` 被当作 D1 时也会因 `open_items_prev=3 与提案第 1 轮行（2 项）不符` 而含 `open_items` 通过断言，故该子用例不能区分边界正则。本人另以探针确认候选正则对 `### D10 裁定` 不匹配、对 `### D1 裁定` 匹配，实现正确；建议后续把该子用例断言收紧为「`### D1` 有 0 行」。此测试为附加项，BC-14 绑定的两条具名测试不受影响。
- `docs/evidence/COORD-015-drill.md` §1 ① 的 D1 代拍证据产生于 BC-14 之前（工具当时按文件序取行），夹具未归档，无法复核 Kimi 写入的 `open_items:` 行是否满足 BC-14 的节内落点；A5 ① 若在首次真实启用前重跑，须按 BC-14 (1) 写节（残留子节用 `####`）。此为证据时效提示，不改变 BC-4/BC-12 的接受侧结论。
- 本提案自身的 `### D1 历史裁定`…`### D6 接受侧裁定` 节后紧跟同级 `### AR…` 子节且节内无 `open_items:` 行（接受复判已声明存量不回填）；当前真实账本无 COORD-015 的 D1 条目，机检通过；若未来对本 work ID 写 D1 条目将失败关闭，符合 BC-14 (3)。
- R1 §3 的其余观察（`_find_proposal()` 唯一性、`MACHINE_RE` 对信封块内 ASCII 键、`git log -S` 标题子串、A3 脚本边界、夹具内 `--force-with-lease`）本轮未变，仍供接受角色在首次真实启用前知悉。
- `docs/current-status.md` 角色表在 `4044aaf`（C2 文档提交）把实现角色改为 Claude Opus 并新增 Supervisor 行，与提案 §7 池重分配一致，非实现改动。

### §4 `UNITY_NA` 附议

本轮再次明确：本工作项为工作流基础设施（账本机检工具、测试与证据），不触及 `controller/`、`Assets/`、`config/` 或任何运行时协议/指标；Gate board Unity 列 `N/A` 与自证「Unity 不适用」本人**附议**。此附议仅覆盖 Unity 维度，不构成 `DONE` 结论。

### §5 Verdict

Verdict: PASS_WITH_NOTES
passed_candidate: 91e05904a5127bcbf59f5f6d8151ca65668bf099

R1-1…R1-5 全部闭合（四条阻断各以具名回归测试修前红/修后绿在副本内核实；R1-5 补丁逐字应用）；focused 88 OK；真实账本机检通过；修复触及行无新 CLASS_1/2，无 `RED_LINE`。Notes：R2-1（CLASS_2/`SCOPE_GAP`，非阻断，交接受角色记债）与 §3 观察。归因按依据列机械派生：R1-1 `BC-12`、R1-2/R1-3 `BC-5`、R1-4 `IN_SCOPE_NO_BC`（BC-15 补覆盖）、R1-5 `上游漏检`，均为实现/证据侧错误，非合同缺口。本轮未修改任何实现文件；主树只写本文件与 `docs/current-status.md`；副本已删除。交接受角色做最终通过轮处置（`AWAITING_ACCEPTANCE_FINAL_R2_LANDING`）；A9 非门报告、A10 运行期扫描、两类信封首签与首次启用仍未闭、仍归用户。
