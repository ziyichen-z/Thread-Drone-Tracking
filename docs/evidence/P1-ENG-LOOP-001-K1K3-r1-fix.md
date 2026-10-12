# P1-ENG-LOOP-001 — R1@K1K3 返工（F1/F2）交付，直接交 R2@K1K3

Owner: Implementation（Claude Code `/implement` 备用入口）
Date: 2026-09-21
Status: `docs/reviews/P1-ENG-LOOP-001.md` R1@K1K3 `REWORK_REQUIRED` 的两条阻断 F1、F2 已修复并提交 →
Review R2@K1K3（按复核文件 §5 与 workflow §4.4，复核返工不经核对轮）。
本文件是实现者自证与复核入口，不是独立复核 verdict。合同、范围与信封不变。

## 1. 候选与复核范围

- 上轮候选 = 复核文件 §0 的 `round_candidate`。本轮候选 = 首次加入本文件的那个提交，运行时解析：
  `git log -1 --diff-filter=A --format=%H -- docs/evidence/P1-ENG-LOOP-001-K1K3-r1-fix.md`（不手写 SHA）。
- 修复 diff：`git diff <round_candidate> <本轮候选> -- controller tests`。两者之间另有 COORD-012 与
  R1 复核的提交，只改 `tools/check_*.py`、`tests/test_check_*.py` 与文档，与本项实现文件零重叠
  （`git diff --stat <round_candidate> <本轮候选> -- controller tests/test_language_*.py` 只列下面四个文件）。
- 触及文件（与状态板交接行声明一致）：`controller/language_bridge.py`、`controller/language_loop.py`、
  `tests/test_language_bridge.py`、`tests/test_language_loop.py`。
- 未触及：全部闭集常量（`ACTIONS`/`OUTCOMES`/…，`IGNORED_DUPLICATE` 原已在 `OUTCOMES` 内）、桥 schema 与
  文件名、`tools/`、Play 治理门文件（`tools/analyze_m3_body.py`、`tools/preflight_reanchor_env.py`、
  `controller/run_log.py`）、证据 JSON、冻结边界（`Assets/`、`config/`、`tools/eng_sft/`、
  `controller/{protocol,tracking_entry,track_loop}.py`、`ProjectSettings/`、`Packages/packages-lock.json`）、
  `controller/{gated_publisher,language_selector,language_demo}.py`。
- 按用户本会话指示只修 F1/F2；复核非阻断注记 1…9 与 F3（`SCOPE_GAP`，路由接受角色）均未动。

## 2. F1 — 死写者锁清理「并记日志」

**改动。** `bridge.acquire_writer_lock` 新增关键字参数 `on_dead_lock_cleared`：确认持有 pid 已死并
`unlink` 后，当场把被清理的持有者（`LockHolder`：pid、request_id、created_unix_s）交给回调；随后重建
即使输给并发写者（`WriterBusy`）也已回调过。返回类型不变，所以 `language_demo.py` 与测试夹具的现有调用
不用改。`send_request`（CLI 九个动作的唯一写入路径）传入回调：往 stderr 打一行
`已清理死写者锁：pid=… request_id=… created_unix_s=…`，并在返回字典里加
`replaced_writer_lock: {pid, request_id, created_unix_s}`（CLI `main` 原样把返回字典打印到 stdout，
回执到达与 5 s 超时两条返回都带）。没有接管时这个键不出现，stderr 也没有输出。

**具名回归（修前红）。** `tests.test_language_loop.RequestLifecycleTests.test_a_dead_writer_lock_is_reclaimed_and_reported_by_the_cli`
- fixture 走生产路径：起一个真实子进程，等它退出，拿它的 pid；再用
  `bridge.acquire_writer_lock(..., pid=<已死 pid>)` 建死锁，不手写锁文件。然后走 `send_request`，用缺省
  `is_alive`（`os.kill` 探测），会话由 `Harness` 真实 tick（fake sleep 驱动 tick）。
- 断言：回执 `APPLIED`；`replaced_writer_lock` 三个字段与死锁一致；stderr 里有 pid 与 request_id；
  等待期间锁由本次请求持有（本进程 pid、request_id `next`）；结束后锁已释放；会话 JSONL 里没有
  `ILLEGAL_WRITER_SUSPECTED`。
- 修前：`KeyError: 'replaced_writer_lock'`（接管静默发生，回执照常到达）。

**辅助用例。** `tests.test_language_bridge.WriterLockTests.test_acquire_takes_over_a_dead_lock`（回调拿到
(4242, "r1", 77.0)）、`WriterLockTests.test_second_writer_is_refused`（活锁 → `WriterBusy`，回调不触发）、
`tests.test_language_loop.RequestLifecycleTests.test_the_cli_reports_no_takeover_for_a_free_slot`（无锁 → 无该键、
stderr 为空）。前两条修前 `TypeError`（没有该参数）。

## 3. F2 — 同 id 重新写入回执 `IGNORED_DUPLICATE`

**改动。** `LanguageSession.consumed_requests` 从 `set[str]` 改为
`dict[request_id → (command_id, issued_unix_s)]`，记最近一次见到的写入身份。
`_consume_request` 遇到已消费的 id 时分三种情况：
- 写入身份与记录相同：这是槽内同一次写入的残留，会话每 20 ms 重读一次，照旧静默；
- 写入身份缺失 `(None, None)`：分不出残留还是重写，按残留处理；
- 写入身份变了：同 id 被重新写入（`protocol.packet` 每次写都铸新的 `command_id`）。更新记录，回执
  `IGNORED_DUPLICATE` 恰一次；不 dispatch，不改状态、epoch、候选，不起查询。

判定顺序与 R1 候选相同：去重先于 `ILLEGAL_WRITER_SUSPECTED` 检查、外会话、`TERMINAL` 与结构非法。
`bridge.read_request` 对可寻址的结构非法请求也带出 `command_id`/`issued_unix_s`（原先置 None），
让非法请求的同 id 重写同样能区分；七处非法分支改走一个局部 `invalid(reason)`，`invalid_reason`
取值不变。

**具名回归（修前红）。** `tests.test_language_loop.RequestLifecycleTests.test_a_rewritten_duplicate_id_gets_an_ignored_duplicate_receipt`
- fixture：A `ask` → `APPLIED`（到 `AWAITING_CONFIRMATION`）→ B `reject` → `APPLIED`（回 `IDLE`，
  `last_request` 变为 B）→ 持写者锁经 `bridge.write_request` 用同 id 重写 A（新 packet，不手写 JSON）。
- 断言：`last_request` 的 request_id/action/outcome = A/`ask`/`IGNORED_DUPLICATE`，`at_sequence` 大于 B；
  状态 `IDLE`、epoch、候选（`None`）、`worker.calls_started`、结果行数全部不变；再 tick 10 次后，
  A 在会话 JSONL 里的回执序列恰为 `[APPLIED, IGNORED_DUPLICATE]`，调用数仍不变。
- 修前：`last_request` 仍是 B 的回执，断言失败。

**钉住「残留重读不回执」。** `RequestLifecycleTests.test_exactly_once_and_duplicate_id` 按复核建议改写：
A 消费后请求文件留在槽里，连续 tick 10 次；epoch 与 `calls_started` 不变，`last_request` 仍是 `APPLIED`，
A 的回执序列恰为 `[APPLIED]`。修前修后都是绿，作用是钉住静默行为。原用例里「重写同 id」的那部分
在新合同下正确结果是 `IGNORED_DUPLICATE`，已移到上面的新用例。

**辅助用例。** `tests.test_language_bridge.RequestBridgeTests.test_unknown_action_reads_as_invalid_not_raise`
增断言：非法请求的 `command_id`/`issued_unix_s` 与文件头一致（修前 None）。

## 4. workflow §4.4 闭合四条

| 条 | F1 | F2 |
|---|---|---|
| (1) 生产路径 fixture | 已死子进程 pid + `bridge.acquire_writer_lock` 建锁 + `send_request` 默认探活 | `Harness.request` = 写者锁 + `bridge.write_request`，会话真实 tick |
| (2) 具名回归修前必红 | 修前 ERROR（`KeyError`） | 修前 FAIL（回执仍是 B） |
| (3) 不触 Play 治理门 | 三个治理门文件零改动 | 同左 |
| (4) 可机械断言 | 返回字典与 stderr 逐字段断言 | 回执字典、JSONL 回执序列、计数器逐项断言 |

## 5. 测试（开发期 focused；停点 focused 一次 + 全套一次；不带 `-v`）

- 修前红：`P1-ENG-LOOP-001-tests-r1-fix-before.log`。在一次性 worktree 里检出 `round_candidate` 的源码，
  配本批修后的两份测试文件，跑下列 7 个具名用例：`Ran 7`、`FAILED (failures=2, errors=3)`。红的 5 条
  = F1 回归、F2 回归、两条锁辅助、一条桥辅助；绿的 2 条 = 残留静默钉子、无接管。跑完 worktree 已删除。
- 修后绿：`P1-ENG-LOOP-001-tests-r1-fix-after.log`，同 7 条，`Ran 7`、`OK`。
- focused：`P1-ENG-LOOP-001-tests-r1-fix-focused.log`，
  `TMPDIR=/private/tmp .venv-language/bin/python -m unittest tests.test_language_bridge tests.test_language_selector tests.test_language_loop tests.test_language_k_binding`
  → `Ran 260`、`OK`，零 skip。257 + 本批新增 3，冻结资产两项与 Pillow 预览用例实际执行。
- 全套：`P1-ENG-LOOP-001-tests-r1-fix.log`，`TMPDIR=/private/tmp python3 -m unittest discover -s tests`
  → `Ran 1515`、`FAILED (errors=9, skipped=24)`。9 个 ERROR 与 K1K3 停点全套 `P1-ENG-LOOP-001-tests.log`
  逐名相同、原因相同（系统解释器缺 `cv2` 8 项、缺 `numpy` 1 项的测试模块导入失败），failures 0，
  **本批新增失败 0**。1515 − 1504 = 11 = 本批新增 3 + COORD-012 在候选之后新增的自检 8 项；skip 数不变。

## 6. workflow §4.3.1 四项自证

| 条件 | 自证 |
|---|---|
| 范围与接口冻结 | 只落实 R1 的 F1/F2；没有新增 AC、闭集成员、桥文件或 schema 字段，也没有扩预算。CLI 返回字典多了一个仅在接管时出现的诊断键，stderr 多一行，二者都不在桥协议内。 |
| 相称实现者验证 | 两条阻断各有一条具名回归，修前红、修后绿；focused 260 OK、零 skip；全套新增失败 0（§5）。 |
| 已知失败处理 / 未验证范围 | 没有待修失败；9 个既有环境 ERROR 与基线同名。阶段 A 零 Unity、零模型、零查询；AC-13…15 仍待阶段 B（未授权）。 |
| 状态、候选与风险可追溯 | 状态板交接行与本文同批更新；候选由 git 解析；风险见 §7。 |

## 7. 已知限制（不在本轮修复范围）

- F1 的「日志」落在 CLI 输出上（stderr 一行 + stdout 打印的返回字典），不写进会话 JSONL：CLI 和会话
  是两个进程，要持久化就得新增桥文件或日志文件，等于扩协议，本轮没做。阶段 B 操作单需要提示操作者
  保存 CLI 输出（留给阶段 B 信封与操作单处理，本轮不改 `operations.md`）。
- `language_demo.py` 的进程内请求仍用无回调的 `acquire_writer_lock`。它的 runtime 是新建的隔离目录，
  持有者就是本进程，不会碰到死锁；它也不是操作者 CLI 入口。
- 死锁回归用的是「已退出子进程的 pid」。理论上操作系统可能在测试的毫秒级窗口里把这个 pid 分配给别的
  进程，那样会误判为活锁、用例报 `WriterBusy`；这是测试环境的偶发风险，不影响生产逻辑。
- F3（`T_hard` 起算点，`SCOPE_GAP`）与复核注记 1…9 保持原样，交接受角色或阶段 B 决策。

## 8. 消耗

零：未启动模型、服务或 Play，没有下载，没有创建 scenario/session/run ID，也没有写真实 `runtime/`。
阶段 A 信封计数与 R1 核实值相同。
