# P1-ENG-LOOP-002 — `K1K2K3K4` R3 冻结集返工稳定候选（Implementation；登记轮次 `R3返工`）

- 派发：Dispatch-Id `P1-ENG-LOOP-002-R3返工-20261007T190743Z-57c2`（`requested.round` = `R3返工`；Opus 子代理，单写者，supervisor 派发）。
- 机器：MacBook Air（Unity 主机）；系统 `python3` 跑 focused，仓库 `.venv-yoloe/bin/python` 只用作第 1.0 节探针里的 `$PY`（只读，不装包）。
- 合同：同名提案「R3冻结集裁定（2026-10-07，Acceptance）」§1–3（冻结集 {R3-1, R3-2, R3-3} 均范围内必修；AC-7 修订 4 选 (i)）；finding 原文见 `docs/reviews/P1-ENG-LOOP-002.md`「R3@K1K2K3K4」§3。
- 执行信封：零消耗。SSH、复制、板、Jetson、Unity/Play、5060、模型加载、下载、pip、runtime、全套测试本轮都是 0；N-1 全套 3/3 已用尽，本轮**没有跑全套**（engineering §6 窄修/定点路径，见 §6）。

## 0. 派生标识与完整候选 diff 解析式（运行时解析，不手抄）

```bash
PASSED=$(grep -oE 'passed_candidate: [0-9a-f]{40}' docs/reviews/P1-ENG-LOOP-002.md | tail -n 1 | awk '{print $2}')   # 上一通过候选（R2）= 全量基线
R3_ROUND=$(grep -oE 'round_candidate: [0-9a-f]{40}' docs/reviews/P1-ENG-LOOP-002.md | tail -n 1 | awk '{print $2}') # R3 §0 轮候选 = R4 修复触及行基线
DISPATCH=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 R3返工 supervisor 派发登记')   # 本轮派发 base
OPS=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 R3返工 操作单候选')               # 唯一 PLAY_GOVERNING 改动提交
CAND=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 R3返工 收工')                    # 本停点稳定候选（交 R4）
git diff "$PASSED".."$CAND"                       # 完整候选 diff（相对上一通过候选）
git diff --name-only "$PASSED".."$CAND"           # 路径闭集
git diff "$R3_ROUND".."$CAND" -- controller tools tests config Assets ProjectSettings Packages/packages-lock.json docs/evidence/P1-ENG-LOOP-002-play-ops.md   # PLAY_GOVERNING 增量 = 只有操作单
git diff "$DISPATCH".."$OPS"                      # 本轮全部操作单改动（只一个文件）
git diff --stat "$OPS".."$CAND"                   # 其后只有本证据与状态板
```

## 1. 状态与结论

- **本提交是 `K1K2K3K4` 的 R3 冻结集返工稳定候选**，按「R3冻结集裁定」§3 **直接交 Review `R4@K1K2K3K4`（终局），不经核对轮**。只记 `IMPLEMENTED`（未复核），不记 `DONE`；Gate board 门值不改（Overall `REVIEW_PASSED` 仍只限 R2 旧范围）。
- 本轮只改操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md` 的三处（加抬头修订记录与 G3 门的指针）：第 0.6 节（R3-1）、第 1.0 节（R3-3）、第 4 节启动块（R3-2）。`controller/`、`tools/`、`tests/`、`config/`、`Assets/` 零 diff（cmd: `git diff --stat "$R3_ROUND".."$CAND" -- controller tools tests config Assets` 为空）。
- 冻结件与其他运行时代码没动；自检工具（`tools/check_docs.py`）没动，第 1.0 节只是从固定发布引用 `$REL` 导出它的原文件、调用其中两个函数。

## 2. 稳定候选四条件自证（workflow §4.3.1；按 AC-n 附指针）

1. **实现范围与接口冻结：成立。** 改动闭集只有操作单一个 PLAY_GOVERNING 文件（cmd: `git diff --name-only "$DISPATCH".."$OPS"` = `docs/evidence/P1-ENG-LOOP-002-play-ops.md`）；三处都是「R3冻结集裁定」§1 表点名的位置。R3-1 按裁定 (i) 只改文本：`controller/language_selector.py` 与具名测试 `tests/test_llama_server_adapter.py::LongPollClientTests.test_wait_is_min_of_4s_and_both_remaining_deadlines_and_io_tracks_t_hard` 的名称与断言都没改，也没加测试。操作单里剩下的尖括号只是运行时取值，没有新占位。没有新的 AC、容差、额度或待裁定项。
2. **相称测试/验证通过：成立（窄修/定点路径，没跑全套）。** 改动只是操作单文本，不碰真实模型加载器、数据划分或对外指标路径，所以按 engineering §6 与裁定 §3 走窄修/定点：(a) 操作单 11 个 `bash` 块逐块 `bash -n` 都是 rc 0（只是语法检查）；(b) R3-2 三分支探针、R3-3 固定候选发布引用探针（§3）；(c) focused `python3 -m unittest tests.test_loop2_freeze` 跑了 3 个、OK（含 PLAY_GOVERNING 归属表外无 diff 的检查）。R3-1 没有代码修复，所以按裁定不构造修前红/修后绿。R3-2/R3-3 是 `NOT_MECHANIZABLE`（操作单文本），仓库里没有对应的可写断言，闭合由 R4 定点复看。
3. **已知 Unity 失败：不适用。** 本轮零 Unity、零 Play。
4. **复核范围、状态板、候选提交与未验证风险已更新：成立。** 本文件 §7 是复核范围，§8 是未验证项；状态板交接行（Owner Review，Progress 含 `R3返工`）、`$OPS` 与 `$CAND` 都已推送到 `origin/main`。

## 3. 冻结集逐条落点（finding → 操作单位置 → 证据）

| Finding / 依据 | 落点 | 证据（artifact:/cmd:） |
|---|---|---|
| R3-1 / `BC-7`（AC-7 修订 4） | 第 0.6 节标题加「修订 4」；长轮询条目把原「单次 I/O 截止 `min(5 s, T_hard 剩余)`…」挪进新的「截止与结果接纳（AC-7 修订 4…）」条目，原样收录提案「R3冻结集裁定」§2「修订3(c)现行逐字澄清文本」，再写清代码落点（`HttpAdapter._long_poll_result` 以 `remaining_hard()` 调 `_call`；`_call` 传给 opener 的 timeout 是 `min(HTTP_IO_DEADLINE_S, deadline_s)`）、具名测试名，以及裁定 (i) 的说明（不承诺在 T_ret 时刻立即返回、不承诺消除竞速）。G3 门加「R3冻结集裁定」§2。 | artifact: `docs/evidence/P1-ENG-LOOP-002-play-ops.md` 第 0.6 节；cmd: 逐字核对——在提案里用正则 `\*\*修订3\(c\)现行逐字澄清文本：\*\* (.*)` 取出 294 字符，确认它以 `  > <原文>\n` 的形式整段出现在操作单里（会话临时脚本，结果为 True）；代码出处 `controller/language_selector.py` 第 652 行 `min(HTTP_IO_DEADLINE_S, deadline_s)`、第 915 行 `remaining_hard()`（`git diff "$R3_ROUND".."$CAND" -- controller tests` 为空） |
| R3-2 / `BC-10`（AC-10） | 第 4 节启动块用四行替换原来那一行 `ss … \| grep … && {STOP}`：先 `SS=$(ss -ltn 2>&1); ss_rc=$?` 原样打印；`ss_rc≠0` 或输出为空就 `STOP S-PRECHECK ss_failed`、`exit 97`（停在 `pgrep` 和服务启动之前）；成功之后才用单个 `awk` 核端口，退出码三分：0 → `port_occupied` STOP，1 → `PORTS_FREE_OK`，其余 → `port_check_failed` STOP。不再用 `grep -q`，所以 `pipefail` 下不会出现 SIGPIPE 歧义。 | artifact: 操作单第 4 节；cmd: 探针（会话临时目录，不入仓）——从候选操作单抽出 `SS=` 行到 `pgrep` 判据行的片段，末尾加 `echo REACHED_SERVICE_START`，`PATH` 前置桩 `ss`/`pgrep`（`pgrep` 恒 rc 1），用 `bash --noprofile --norc -c 'set -o pipefail; . 片段'` 运行。新版：`ss` rc 1 且无输出 → rc 97、`ss_failed rc=1`、未到启动；`ss` rc 0 但输出为空 → rc 97、`ss_failed rc=0`；`ss` rc 2 只有报错文本 → rc 97、`ss_failed rc=2`；成功且 18082 被占 → rc 97、`port_occupied 100.100.100.100:18082`；成功且端口空闲（只有 22、46273）→ `PORTS_FREE_OK`，到了启动。修前对照（`$DISPATCH` 版同一片段）：三种 `ss` 失败都**到了启动**（rc 0，复现 R3-2），被占时 STOP |
| R3-3 / `BC-10`（AC-10 修订 1(b)） | 第 1.0 节重写放行门：(a) `round_candidate`/`passed_candidate` 只认行首（可带 `-`/`*` 列表记号和反引号）的「键: 40 位十六进制」，与复核文件的真实写法一致；取最后一条 round 行和最后一条 pass 行，缺有效 round 行、缺有效 pass 行、或最新一轮之后没有通过行（`PASS_LINE` ≤ `LAST_ROUND_LINE`）都 STOP，通过候选还须是 `$REL` 的祖先；(b) PG 差异先核 `git diff` 的退出码，非 0 就 STOP，不再把失败当成空差异；(c) 消耗性门：`git archive "$REL"` 导出 `docs/reviews`、`docs/implementation-status.md`、`tools/check_docs.py` 到 `$OUT` 下一个 `mktemp` 目录，调用 `$REL` 上 `check_docs.py` 的 `open_consuming_gate_blocks`（全部复核文件，按文件顺序配对，排除 README/预筛/围栏）与 `ledger_released_findings`（账本 `RELEASED_SCOPE_GAP`），再按 `check_consuming_gate_blocks` 的同一式子扣除；还有剩余就退出 4 → `consuming_gate_blocked` STOP，导出/读取/解析失败 → `consuming_gate_check_failed` STOP；(d) 所有 STOP 都置 `GATE=1`，只有 `GATE=0` 时末行才打印 `RELEASE_GATE_OK`，正文规定只有它出现、且整段没有 STOP 行才继续。第 1.5 步 `check_docs.py` 原样保留，正文写明它不能替代本步（它只在有未暂停 `Consuming=yes` 交接时才拒绝）。 | artifact: 操作单第 1.0 节；cmd: 探针（会话临时目录一次性 `git clone`，从被测提交的操作单抽出第 1.0 节块，只把 `git fetch origin` 换成空操作、`origin/main` 换成 `$PROBE_REL`；用 Air 的 `/bin/bash` 3.2 加 `pipefail` 运行，`$PY` = `.venv-yoloe/bin/python`）。**固定候选发布引用 `$REL` = `$OPS`**：`last_round_line=220`（非空）、`last_round_candidate` 等于 R3 §0 轮候选、`pass_line=166`、`passed_candidate` 等于 R2 通过候选 → `STOP latest_round_not_passed` 与 `STOP play_governing_changed_after_pass`（7 个 PG 路径，与 R3 §0 一致）；消耗性门配对输出 `consuming_gate_open_blocks_by_file_order={}`、`ledger_released_scope_gap={}`、`consuming_gate_unreleased={}` → `CONSUMING_GATE_OK`；末行 `STOP release_gate GATE=1`（正确：R3 未通过）。修前对照（`$DISPATCH` 版第 1.0 节，同一 `$REL`）：`last_round_line=` 为空、照样打印 `RELEASE_REF_OK`（复现 R3-3(a)），也没有任何门状态输出（R3-3(b)）。**允许路径（真实字节）**：`$REL` = R2 通过提交（`git log --format=%H --grep='^P1-ENG-LOOP-002 R2@K1K2K3K4 独立复核通过'`）→ `last_round_line=114 < pass_line=166`、`RELEASE_REF_OK`、`PG_DIFF_EMPTY_OK`、`CONSUMING_GATE_OK`、`RELEASE_GATE_OK`。**未 release 拒绝（真实字节）**：`$REL` = `P1-ENG-ACQ-001` R2 写 block 的提交（`git log --format=%H --grep='^P1-ENG-ACQ-001 R2@K1K2K3 PASS_WITH_NOTES'`）→ `consuming_gate_unreleased={"P1-ENG-ACQ-001.md": ["R2-1"]}`、`STOP consuming_gate_blocked`；**配对后允许**：`$REL` = 同项 R3 写 release 的提交（`--grep='^P1-ENG-ACQ-001 R3@K1K2K3 PASS_WITH_NOTES'`）→ 配对后 `{}`、`CONSUMING_GATE_OK`（这两个历史引用上本项复核文件还不存在，所以同时出现 `review_file_unreadable` 等 STOP 并 `GATE=1`，正是缺有效行时应有的结果）。账本 `RELEASED_SCOPE_GAP` 分支在仓库历史里没有真实行，本轮不手写账本造证；该分支用的就是 `check_docs.py` 自己的函数，回归在 `tests/test_check_docs.py::test_ledger_released_scope_gap_row_counts_as_release`（本轮未改、未跑） |

## 4. AC-n 证据指针（本候选；没改的 AC 结论随 R3 §2 携带）

| AC | 结论 | 证据指针 |
|---|---|---|
| AC-7（含修订 1/2/3/4） | 自证满足（文本对齐；代码与测试零 diff） | artifact: 操作单第 0.6 节；test: `tests/test_llama_server_adapter.py::LongPollClientTests.test_wait_is_min_of_4s_and_both_remaining_deadlines_and_io_tracks_t_hard`（未改，R3 focused 488 OK 随候选携带）；cmd: §3 R3-1 行 |
| AC-10（含修订 1） | 自证满足，待 R4 定点复看 | artifact: 操作单第 1.0 节、第 4 节；cmd: §3 R3-2/R3-3 行的探针 |
| AC-1…6、8、9、11…13、15（代码）、17 | 携带（R3 §2 成立；对应文件相对 `$R3_ROUND` 零 diff） | cmd: `git diff --stat "$R3_ROUND".."$CAND" -- controller tools tests config Assets` 为空；test: `tests.test_loop2_freeze` 3 OK |
| AC-14 / AC-18、AC-15 板端、AC-16 板端 | `NOT_RUN` | 阶段 B 运行未放行；不申请 `UNITY_NA` |

## 5. 改动文件闭集

- **本角色本轮**：`docs/evidence/P1-ENG-LOOP-002-play-ops.md`（PLAY_GOVERNING，`$OPS`）、本文件、`docs/current-status.md`（交接行、Gate board 本项实现列、Log 一条）。
- **`$R3_ROUND`..`$DISPATCH` 之间其他角色的提交**（按真实 diff，本表不豁免）：复核（`docs/reviews/P1-ENG-LOOP-002.md` R3 节）、接受（提案「R3冻结集裁定」与复判表、`-C4-K1K2K3K4.md`、`docs/implementation-status.md`、`docs/phase1-single-drone-design.md`）、supervisor（`docs/evidence/supervisor-dispatch.jsonl`）、状态板。
- 相对 `$PASSED` 的完整 diff 中，代码部分与 R3 §0 的 22 路径相同（本轮没加任何非 docs 路径）。

## 6. 验证用量与没跑的部分

- 停点全套：**没跑**（N-1 3/3 已用尽；本轮只改操作单文本，按 engineering §6 走窄修/定点路径；不记全套通过）。如果复核认为替代不够，须先回用户另签，本轮不假设新资源。
- focused：`python3 -m unittest tests.test_loop2_freeze` → `Ran 3 … OK`（输出写在会话临时目录，只回显了摘要）。
- 探针：都在会话临时目录（一次性 `git clone` 加桩目录），脚本和输出都不入仓；没写 `runtime/`，没有任何网络或板连接（第 1.0 节的 `git fetch` 已换成空操作）。
- consumed = none（零 ID/Play/API/GPU/下载/pip/SSH/板/复制/runtime/模型/回放）。

## 7. 复核范围（R4@K1K2K3K4，终局）

- 冻结集 + `RED_LINE` + 修复触及行上的 CLASS_1/2（「R3冻结集裁定」§3）：`git diff "$R3_ROUND".."$CAND" -- docs/evidence/P1-ENG-LOOP-002-play-ops.md` 的三处（抬头修订记录/G3、第 0.6 节、第 1.0 节、第 4 节启动块）。
- R3-1 定点：修订 4 文本 ↔ 操作单第 0.6 节 ↔ 具名测试 ↔ 真实 `_long_poll_result` → `_call`。
- R3-2 定点：第 4 节启动块的 ss 非 0/无输出、成功被占、成功空闲三个分支。
- R3-3 定点：第 1.0 节在一次性副本里以 `$REL` = 候选重跑，核 `LAST_ROUND_LINE` 非空、行序判据，以及 block/release 配对输出。

## 8. 未验证项与已知限制

- 第 4 节探针用的是 macOS `/bin/bash` 3.2 和 BSD `awk`；板端是 Ubuntu bash 与系统 `awk`（mawk/gawk），没在板上运行。`awk` 用到的 `$4 ~ /…/`、`END {exit f ? 0 : 1}` 是 POSIX awk 写法，但板端实际行为未验证。
- 第 1.0 节的行首匹配不排除复核文件里的围栏代码块（`check_docs.py` 的 block/release 扫描排除，round/pass 解析不排除）；本项复核文件目前没有围栏块。AGENTS 对这两行的规定只是「§0 写 `round_candidate: <40 位 SHA>`」「通过轮写 `passed_candidate`」，没有更多格式约定。
- 第 1.0 节不核「最新 pass 的候选等于最新 round 的候选」（只核行序与祖先关系），保持裁定 §1 的判据，不另加。
- 第 1.0 节会在 `$OUT/release/` 下每次留一个只读导出目录（`cg-tree.*`），不删（被忽略路径，不进 dirty 判据）。
- 其余未验证项照 `docs/evidence/P1-ENG-LOOP-002-stable-candidate.md` §9（板端长轮询、Tailscale、`llama-server` 实际行为、SSH 失败闭合回退等），本轮没有变化。

待裁定：**无**。
