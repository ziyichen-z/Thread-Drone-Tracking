# P1-ENG-LOOP-001 — R5@K1K3 F7 定向返工交付，直接交新鲜上下文 R6@K1K3

Owner: Implementation（Claude Code `/implement`），2026-09-23。
输入：`docs/reviews/P1-ENG-LOOP-001.md` R5@K1K3 `REWORK_REQUIRED`（§3 F7 阻断与闭合要求，§4 注记 1）；提案 Acceptance rulings
R5/F7 两行；`docs/authorizations.md` 2026-09-23「R5/F7 一次定向超限返工」（用户原话「授权一次定向返工」：额外一次、仅闭合 F7、
不经 C5、直接交新鲜上下文 R6；R6 不通过回用户，不自动授予 R7）。
零消耗：零 Play、零模型/5060 服务、零 ID、零下载、零传输、零账本迁移；未触碰真实 `runtime/`。本文件是实现者自证，不是独立复核 verdict。

## 1. 候选与复核范围

- 上轮候选 = 复核文件 R5 §0 的 `round_candidate`。本轮候选 = 首次加入本文件的提交，运行时解析：
  `git log -1 --diff-filter=A --format=%H -- docs/evidence/P1-ENG-LOOP-001-K1K3-r5-fix.md`（不手写 SHA）。
- 修复触及行：`git diff <round_candidate> <本轮候选>`。两者之间另有 C4 核对、R5 复核、R5/F7 接受裁定与授权入账四笔提交，只改
  `docs/{authorizations,current-status,implementation-status}.md`、提案与复核文件，与下列触及文件零重叠。
- 触及文件（R5 §3 允许的范围）：
  - `docs/evidence/P1-ENG-LOOP-001-operator-web.py`（F7、注记 1、§3 用户选择 2；冻结操作单，PLAY_GOVERNING）
  - `docs/evidence/P1-ENG-LOOP-001-operations-c.md`（§3「结果未知」段两句同步；首段状态行改为「R6@K1K3 通过前不开 Play」；冻结操作单）
  - `docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.py`（具名回归 9 项；`StubCli` 允许按调用执行的夹具动作）
  - 新证据：本文件、`-r5-fix-carrier-selftest.log`、`-tests-r5-fix.log`；状态板
- 未触及：`-operator.sh`、`-operator-watch.py`、`-5060-runner-b.py`、`-build-stage-b-manifest.py`、`controller/`、`tools/`、`tests/`、
  `config/`、`Assets/`、`ProjectSettings/`、`Packages/`、Play 治理门三文件。`-r5-fix-carrier-selftest.log` §1 逐目录 `git diff --quiet`
  相对 `round_candidate` 退出码均为 0。
- F3（`SCOPE_GAP`，账本 `OPEN`）与 R5 注记 2…9 未动。

## 2. F7 — 同 id 重试写不进去时删除「结果未知」条目

**改动（`App._run`，只对 `retry_same_request_id`）。** 同 id 重试从不新增、也不因「本次没写进去」删除条目：只有拿到能回答原请求的回执
（`IGNORED_DUPLICATE` 以外的任何回执）才移除；`WRITER_BUSY`（4）、CLI 出错（1 或其他退出码）、超时、再次无回执（0/5）一律保留原条目
（原 argv、页面身份、令牌、`since_unix_s` 不变），并在条目上记 `last_retry = {exit, timeout, message, at_unix_s}`，返回文案追加
「原请求结果仍未知，保留在「结果未知」框」。同视图同动作守卫（`_click` 的 `same`）与迟到回执关联（`resolve_late_receipts` 按 id 查会话
JSONL）因条目仍在而继续生效。重试等待期间该条目被迟到回执解决时不再被重试「复活」，返回文案带上那条迟到回执（`late_messages`）。
页面「结果未知」框显示「上次重试：…（x s 前）」，渲染键包含 `last_retry.at_unix_s`，所以同一条目的重试结果变化会重画。

## 3. 用户在本会话的选择（`AskUserQuestion`，所选标签逐字；零消耗、不改合同，不是新的关键授权）

1. 问：修 F7 时，要不要顺带处理复核注记 1（同一条路径上的毫秒级竞态）？选：「一并处理（推荐）」（未选：「只按复核点名的写」
   「只修 F7 最小面」）。落实：
   - `App._retry` 先 `monitor.poll()` 读会话日志再 `resolve_late_receipts()`：原回执已到则**不发**重试，拒绝文案「不再重试，原请求已有
     回执——迟到回执（同一 request_id）：…」；对已解决条目的过期重试按钮同样给出其回执（原为「没有这个结果未知的请求可重试」）。
     读取失败按 `_click` 同样处理：不发、提示读取失败、条目保留。
   - 重试回 `IGNORED_DUPLICATE`（原请求在页面读日志之后、重试写入之前被消费）时条目保留，随即重读日志，用原请求**自己的**回执解除，
     返回文案「同一 request_id 已处理过…；迟到回执（同一 request_id）：<原回执含义>」。
   - `Monitor._read_logs`：同一 `request_id` 已有回执时，后到的 `IGNORED_DUPLICATE` 不覆盖它（它只是重试的回声）。其余回执仍按原样
     后写覆盖（`PENDING_QUEUED` → `SUPERSEDED` 的更新不受影响）。
2. 问：新点击（不是重试）的 CLI 以退出码 1 等「意外退出」结束时，要不要也保留为「结果未知」？（背景：`send_request` 写入请求后
   读状态文件遇系统错误、或 `finally` 释放写者锁出错都会以 1 结束，此时请求可能已写入；该判定行本批已触及。）选：「一并按结果未知处理
   （推荐）」（未选：「不改，记为已知限制」）。落实：新常量 `NOT_WRITTEN_EXITS = {2, 4}`（`language_loop.main`：2 = 写前的参数/守卫
   拒绝，4 = `WRITER_BUSY`）；新点击无回执时只有这两个退出码不留条目，0/5/超时/其余退出一律留作「结果未知」、只可同 id 重试；
   `interpret` 对其余退出码的文案改为「CLI 退出码 N：结果未知（请求可能已写入），不会自动重发」。

两项都在 AC-18 / AC-1 修订 1 已接受语义（未知结果不自动换 id、同 id 重试由会话去重）之内，是否需另入授权账本请接受/辅助角色判断
（实现角色对账本只读）。

## 4. 具名回归（`-c2-carrier-selftest.py` → `test_web`）

fixture：桥与状态由 `language_bridge.tracker_state_payload` + `write_tracker_state` 写，迟到回执由 `LanguageSession._journal`（会话自己的
写者，经 `Fixture.receipt`）写入会话 JSONL；CLI 为 `StubCli`（exit 4 / 1 / 5 / 2，或在调用中执行夹具动作以复现竞态）。

| 检查名（逐字） | 对应 |
|---|---|
| `web: a same-id retry refused by WRITER_BUSY keeps the unknown entry, its guard and its late-receipt match (F7)` | R5 §3 闭合要求 (2)：重试 exit 4 后条目仍是 `[A]`、`last_retry.exit == 4`，同视图同动作被拒且不调 CLI，A 的迟到回执到达后被关联（`APPLIED`） |
| `web: a same-id retry that exits 1 (CLI error) keeps the unknown entry and its guard (F7)` | R5 §3 闭合要求 (1)「另补 exit 1 一例」 |
| `web: a retry whose request is resolved by its late receipt while the CLI runs is not re-added and keeps that receipt in view (F7)` | §2 重试期间被解决不复活 |
| `web: a retry whose original receipt is already in the session journal is not sent; that receipt is shown (R5 note 1)` | §3 选择 1 |
| `web: a retry answered IGNORED_DUPLICATE shows the original request's own receipt from the journal (R5 note 1)` | §3 选择 1（竞态：会话先记 `REQUEST_INVALID`、再记 `IGNORED_DUPLICATE`） |
| `web: a retry clicked on an already resolved request is not sent and names its receipt (R5 note 1)` | §3 选择 1（过期按钮） |
| `web: a fresh click whose CLI exits 1 (request may be written) is kept unknown for a same-id retry (F7 rework, user choice)` | §3 选择 2 |
| `web: exits 2 (refused before writing) and 4 (WRITER_BUSY) prove nothing was written: not kept unknown` | §3 选择 2 的反向边界（新旧页面都应绿） |
| `web page source: each unknown box shows its last retry's outcome and keeps its same-id retry button (F7)` | 页面源码断言（未开真实浏览器） |

原有「WRITER_BUSY is reported as not written (not unknown)」（新点击 exit 4）、「operator retry reuses the same argv, request_id and token」、
C3-2 多条未知与 C3-3 外层超时各项不变且仍绿。

## 5. 修前红 / 修后绿（`docs/evidence/P1-ENG-LOOP-001-r5-fix-carrier-selftest.log`）

- §2 修后：默认载体 99 项全 `ok`（R5 候选 90 + 本批 9），`OK: 0 failed`，退出码 0。
- §3.1 修前：已提交的本批自测加 `--web` 指向 `round_candidate` 的按钮页（`git show` 到 scratchpad）：8 项 `FAIL`（上表除 exit 2/4 反向
  边界外全部），其余 `ok`，退出码 1。
- §3.2 非空性：只删 `Monitor._read_logs` 的两行「不覆盖」→ 只红「IGNORED_DUPLICATE shows the original…」1 项。
- §3.3 非空性：只把 `_run` 的删除规则还原成 `round_candidate` 的写法 → 红 6 项（两项 F7、重试期间复活、新点击 exit 1、IGNORED_DUPLICATE；
  「receipt already in the journal」连带红，因为旧规则让前一步的 exit-1 重试删掉了它要重试的条目）。
- §4 页面内嵌脚本 `node --check` 语法通过。

## 6. 停点全套（隔离副本）

`docs/evidence/P1-ENG-LOOP-001-tests-r5-fix.log`：scratchpad 下 `git worktree add --detach` 的副本（HEAD = 授权入账提交，拷入本批
`docs/evidence` 最终改动；副本 `runtime/` 只有 `README.md`、无 `outputs/`），系统 `python3` 跑一次，不带 `-v`，末尾按名列出全部 skip。
结果与 C3 后候选的 `-tests-c3.log` 相同：`Ran 1524`、failures 0、9 个 `ERROR:` 排序后逐名相同（8 × `No module named 'cv2'`、1 × `numpy`）、
skip 清单排序后逐项相同（68；`RealArchiveClosureTest` 5 项在副本内 skip，不作归档闭合证据）→ **新增失败 0**。被测树 `tests`/`controller`/
`tools` 与 `round_candidate` 相同（日志首行树哈希），本批改动都在 `docs/evidence/`，`tests/`、`tools/`、`controller/` 不引用这三个文件。
如实说明：§3 选择 2 落实之前，曾以同样方式对中间内容跑过一次全套（结果与上述逐名相同）；为使日志严格对应最终候选内容，选择 2 与本文件
写完后重跑一次，本日志是这一次，覆盖前者。

## 7. workflow §4.3.1 四项自证（按 AC 编号）

1. **范围冻结**：只动 R5 §3 允许的文件（§1）；合同、K 收据、桥协议与闭集、会话状态机、Unity 设置零改动（`-r5-fix-carrier-selftest.log` §1）。
2. **相称测试**：AC-18 / AC-1 修订 1 的未知结果处理由 §4 九项具名回归覆盖，修前红/修后绿与两个变异体见 §5；停点全套新增失败 0（§6）。
3. **已知 Unity 失败**：本批不触及 Unity；首批追平、后台供帧与人眼检查仍按裁定留待 R6 通过后的获准诊断。
4. **状态板、候选提交、复核范围**：交接行转 Review（R6@K1K3），只写本文件指针；复核范围见 §9。

逐 AC 指针：AC-18（未知/超时遵循 AC-1 修订 1、不自动换 id、同 id 重试、迟到回执关联、记录点击/回执）→ §2、§3、§4；AC-1 修订 1
（`WRITER_BUSY` 与同 id 重试去重）→ §2 与 `controller/language_loop.py` `main`/`send_request`/`_consume_request`（零改动）；其余 AC 沿用 R5 §1。

## 8. 未验证项与已知限制

- 「上次重试」一行与重画只有页面源码断言和 `node --check`，未在真实浏览器点击；按合同留获准诊断。
- `unknowns` 与 `late_messages` 只在操作页进程内存中，操作页重启后不再记得（操作单 §3 原有提示不变，以 `operator-web.jsonl` 与 `lc status` 为准）。
- 新点击退出码 1 等若发生在**写入之前**（例如取写者锁时的系统错误），页面也会显示「结果未知」；这是选择 2 的保守代价，同 id 重试由会话去重，
  不会双执行。
- `IGNORED_DUPLICATE` 之后若会话日志里始终读不到原回执（现行会话每次消费都记回执，未见此路径），条目保留、显示「上次重试：同一 request_id
  已处理过…」，不冒称未执行。

## 9. 给复核角色的范围（R6@K1K3）

按授权：只查 F7 闭合红绿 + 修复触及行（`git diff <round_candidate> <本轮候选>`，三个触及文件）上的 CLASS_1/2 与 `RED_LINE`。§3 两项用户选择
都在触及行内，请一并按同一标准核查。PLAY_GOVERNING 非空（按钮页与操作单）。不需要 GPU、Unity、5060 或网络；自测只写临时目录，
帧目录参数可用主树 `runtime/frames.1b-diagnostic-hold` 只读传入（与 R5 相同）。
