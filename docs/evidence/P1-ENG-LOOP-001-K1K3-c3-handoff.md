# P1-ENG-LOOP-001 — K1K3 停点候选交接（R-B5…7 落实：本地按钮操作页、runner 诊断额度迁移、操作单 C；C3 后修 C3-1…3，交 C4）

Owner：Implementation（Claude Code `/implement`），2026-09-22。输入 = 提案 Pending rulings R-B5…7（AC-18、AC-12 修订4/5）与
`docs/authorizations.md` 同日「本地按钮操作页与追加三次诊断」；**替换候选**另依据提案「用户指定网页功能审查」节（接受角色，
UI-1…6）与用户本会话选择（§6 第 5 条）：在 C3 开始前先修 UI-1…4，UI-5/6 不在本批。**C3@K1K3 之后**，按提案
`## Contract conformance（核对表）` 的预复核关注项 C3-1…3 与用户选择（§6 第 6 条）再修一次，交接受角色 C4@K1K3 后再交 R5。本批零消耗：零 Play、零模型加载/查询、零 5060 传输或服务启动、
零正式 ID；没有写 `runtime/`，没有改 `controller/`、`Assets/`、`config/`、`ProjectSettings/`、`tools/`、`tests/`、K 收据或协议。

## 1. 候选与完整 diff

- **候选** = 最后一次修改本文件的提交：`git log -1 --format=%H -- docs/evidence/P1-ENG-LOOP-001-K1K3-c3-handoff.md`
  （运行时解析，本文不手写 SHA）。已推送 `origin/main`。**被替换的第一个 C3 候选** = 首次加入本文件的提交
  （`git log --diff-filter=A --format=%H -- <本文件>`），C3 未对它开始；两者之差只在 `-operator-web.py`、自测、操作单 C 与证据文件。
  **C3 所核对的候选** = C3 提交（主题 `P1-ENG-LOOP-001 C3@K1K3 check candidate and hand off open items`）之前最后修改本文件的提交；
  它与本候选之差只在 `-5060-runner-b.py`（C3-1）、`-operator-web.py`（C3-2/3）、自测、操作单 C 与证据文件。
- **基线**：上一通过候选 = `docs/reviews/P1-ENG-LOOP-001.md` 最后一条 `passed_candidate`（R4）；上一复核候选 = 该文件最后一条
  `round_candidate`。完整 diff：`git diff <R4 passed_candidate> <候选>`。
- **完整 diff 分类**（相对 R4 通过候选）：
  - PLAY_GOVERNING 的代码路径 `controller/ Assets/ tools/ tests/ config/ ProjectSettings/ Packages/packages-lock.json`：**零差异**
    （`-c3-carrier-selftest.log` §1 逐路径 `git diff --quiet` 退出码 0）。
  - 本项冻结操作单集合（R-B5 点名，属 PLAY_GOVERNING，本批改动）：`P1-ENG-LOOP-001-operations-c.md`、`-operator.sh`、
    `-operator-watch.py`、`-operator-web.py`（新）、`-5060-runner-b.py`、`-build-stage-b-manifest.py`。
  - 本批测试/证据：`-c2-carrier-selftest.py`（按合同沿用该文件名，补 C3 检查）、`-c3-carrier-selftest.log`、`-tests-c3.log`、
    本文件、`-stage-b-prep.md` §9。
  - R4 之后、本批之前由其他角色/批次提交的文档（状态板、授权账本、提案、复核文件、implementation-status、设计文档、
    Unity 日志、prep §8、`-service-5060-b.log`、`-transfer-manifest-5060-stage-b.json`）在同一 diff 范围内但**不属本批实现**，
    如实列出，不冒称白名单文档；其中 `-transfer-manifest-5060-stage-b.json` 是诊断 3 前按 R4 候选重建的执行清单，本批未改。

## 2. workflow §4.3.1 四项自证

1. **范围与接口冻结**：AC-18 的操作页（`-operator-web.py`）、页面模式 watch、`lc_web`/`lc_watch`/`lc_watch_popup` 与 `lc_check`
   新增的残留操作页检查；AC-12 修订4 的 runner 一次性迁移（`AC-12-rev4`：+3、标签 `diag-loopb-5…7`、冻结已计费诊断会话）与清单
   脚本从候选 git 对象取 runner；AC-12 修订5 的操作单 C 全部文字。倒计时与身份绑定只用现有只读数据（结果信封 `issued_unix_s`、
   结果 `query_unix_s`/`frame_id`、`latest.json`、K 收据、会话 `results.jsonl` 与 `previews/`），**不缺字段，未回 Pending rulings、
   未扩核心改动**。控制器、协议、K、门、跟踪核心与模型决策零改动。本批无新的合同歧义。
2. **相称测试通过**：`python3 docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.py` 90/90 ok（`-c3-carrier-selftest.log` §2，含
   两次真实 CLI 子进程往返与一次真实外层超时；夹具预览为真实可解码 PNG，结果与会话日志行用会话自己的追加写函数产生）。
   **修前红**：同一套检查对 C3 所核对候选的 runner 红 1（C3-1）、页面红 4（C3-2 两项、日志连带一项、C3-3）（同日志 §3 前两节）。
   **反证**：对 R4 旧 runner/旧 watch、第一个 C3 页面与十个各改坏一处的页面变体全部变红（同日志 §3 其余各节：
   10/3/3/2/4/1/1/1/2/2/3/3/1，其中七个变体对应 UI-1…4 与 C3-3），证明检查不空转；清单脚本在工作树 runner 与通过候选不同时
   拒绝生成且不动已入库清单（同日志 §4）。
   浏览器行为另由实现角色在应用内浏览器用 scratchpad 假会话目检（§4 第 1 条，非证据）。停点全套
   `docs/evidence/P1-ENG-LOOP-001-tests-c3.log`：沿用接受裁定认可的运行位置——隔离 worktree（HEAD + 本批 `docs/evidence`
   改动，`runtime/` 只有 README、无 `outputs/`），系统 `python3`、不带 `-v`：`Ran 1524`，failures 0，errors 9，skipped 68；
   9 个 ERROR 与 R3 返工隔离全套（`-tests-r3-fix.log`）排序后**逐名相同**（8 × `No module named 'cv2'`、1 × numpy），68 个 skip
   **逐项相同**，**新增失败 0**。被测代码树（`tests`/`controller`/`tools`）与 R4 通过候选相同，树哈希见日志首行。
   `RealArchiveClosureTest` 5 项仍以「真实归档不在本工作副本中」skip，未执行，不作归档闭合证据（接受裁定原文）。
   全套跑在本批 runner、页面、自测与操作单改动之后；随后只改了本文件与 prep §9，二者不被任何测试读取。
3. **已知 Unity 失败**：本批不触及 Unity；诊断 3/4 没有测到首批追平，接受侧已作执行归因（流程/时机，非代码缺陷），本批不据此改代码。
   真实浏览器呈现与点击、首批追平、人眼保真仍待 R5 通过后的获准诊断。
4. **复核文件、状态板、候选 commit、未验证风险**：状态板交接行转接受角色 C4@K1K3（本文件为指针）；复核文件由复核角色写 R5，
   实现不写；候选已提交推送；风险见 §4。

## 3. 逐 AC 证据指针（本批新增/修订的三行；其余 AC 与 R4 相同，本批代码路径零差异）

| AC | 条款要点 | 证据指针 |
|---|---|---|
| AC-18 | 仅 127.0.0.1、标准库、内嵌页面、无下载 | artifact:`-operator-web.py`（`HOST`、`PAGE`、只 import 标准库）；cmd:自测「listens on 127.0.0.1…」 |
| AC-18 | 状态、绑定 query_id/源帧的候选与核验预览、确认剩余时间 | cmd:自测「deadline = earlier of…」「verify-raised alert shows the triggering query's preview (F5)」；artifact:`-operator-web.py` `Monitor.preview_name` |
| AC-18 | 动作闭集、按 §3.4/AC-17 修订1 只呈现合法动作、backend_fatal 只许 stop | cmd:自测「buttons follow the §3.4 table…」「backend_fatal offers stop only」「TERMINAL has no buttons」「an action not legal…」 |
| AC-18 | 只调用采集候选 CLI、不手写桥文件、无自动动作 | artifact:`CliRunner.argv`（`python -m controller.language_loop`，cwd = `--worktree`）；cmd:自测「every argv parses with the real language_loop CLI」「real CLI round trip…」「the page wrote nothing into the runtime」 |
| AC-18 | 身份绑定、旧页面不换绑令牌 | cmd:自测「a stale page (older candidate/epoch) is refused…」「an old alert page cannot dismiss a newer alert」「confirm runs the CLI once with the shown result_id and index」「confirm-lost carries the shown suspect_id」 |
| AC-18 | 预览缺失/身份不符不提供确认 | cmd:自测「missing or mismatched preview -> not confirmable, confirm not sent」 |
| AC-18 | F5 读序绑定、后到核验不替代告警帧 | cmd:自测「a later verify never replaces the alert frame…」「alert seen before its result waits…」「verdict/kind mismatch…」 |
| AC-18 | 两个截止取早者 + 帧差门；可信原始时刻；刷新/重启不续期；取不到即明示不可确认；页面计时结束无事件 | cmd:自测「deadline = earlier of query+T_ret+T_conf…」「when the query started early the query deadline wins…」「polling, reload and restart never renew the deadline」「past the frame-difference gate…」「without a readable latest frame…」「past the deadline confirm is disabled and not sent (no event, state unchanged)」 |
| AC-18 | 防重复提交；未知/超时不自动换 request_id；同 id 重试 | cmd:自测「a click while another is running is refused」「an identical click right after is refused as duplicate」「unknown receipt (exit 5)… nothing is resent」「operator retry reuses the same argv, request_id and token」「real CLI without a receipt -> result unknown…」 |
| AC-18 | 点击/身份/stdout/stderr/回执记入 opdir；APPLIED 不冒称播种/发布 | cmd:自测「every click/refusal is logged…」「APPLIED is reported as accepted…」；artifact:`<opdir>/operator-web.jsonl` |
| AC-18 | F4 发布显示 | cmd:自测「published display (F4)…」 |
| AC-18（UI-1） | 预览要真正显示成功才可确认：服务端校验 PNG 头；页面只在 `<img>` 加载且解码（`naturalWidth>0`）并仍是本次候选后才启用确认，确认请求须带该图片名，服务端不符即拒绝；加载中/失败/换候选明示原因 | cmd:自测「confirm without the name of the preview the page displayed is refused (UI-1)」「a preview file that is not a displayable PNG…」「web page source: … confirm gated on the loaded image…」；反证：变体 ui1-no-preview-seen、ui1-no-png-check |
| AC-18（UI-2） | 点击等回执期间照常刷新；显示读取时刻、帧采集时刻（>3 s 标「帧未前进」）与 `last_published` 变化；读不到会话文件 → 标过期并停用确认，点击时读失败 → 拒绝不发送；连不上本机服务 → 横幅、整页变灰、按钮全停 | cmd:自测「stale (>1 s old) or unreadable data disables confirmation…」「a click is refused (nothing sent) when the fresh read fails…」「shows when last_published last moved…」「shows when the latest frame last moved…」「web page source: keeps polling while a click waits…」；反证：变体 ui2-never-stale |
| AC-18（UI-3） | 结果未知时同一视图的同一动作被拒（原按钮标「结果未知」停用），突出同 id 重试；会话日志中该 request_id 的迟到回执自动关联并显示 | cmd:自测「while a result is unknown the same action on the same view is refused…」「a late receipt in the session journal resolves the unknown request…」；反证：变体 ui3-no-unknown-guard、ui3-no-late-receipt |
| AC-18（UI-4） | 告警期间其他核验按发起时刻标「告警前参考」/「告警后核验」；`tracker_failure` 在告警后核验回来前不以旧图为依据；显示在途核验 | cmd:自测「under tracker_failure the old verify is labelled a pre-alert reference…」「the operator's verify after a tracker_failure alert is shown as after-alert evidence…」；反证：变体 ui4-no-relation |
| AC-18（C3-2） | 多条「结果未知」按 request_id 逐条保留：各自守卫同视图的同一动作、各自同 id 重试、迟到回执只解除对应一条；页面每条一个框 | cmd:自测「two different unknown actions are both kept…(C3-2)」「a late receipt… resolves only its own unknown request…」「the other unknown request keeps its own same-id retry (C3-2)」；修前红：C3 所核对页面；反证：变体 ui3-no-unknown-guard、ui3-no-late-receipt |
| AC-18（C3-3） | 外层超时截获的字节输出先解码，且先记「结果未知」再写点击日志；日志序列化对字节兜底 | cmd:自测「an outer CLI timeout with partial output is kept as unknown and logged as text (C3-3)」（真实子进程、真实超时）；修前红：C3 所核对页面；反证：变体 c3-3-no-decode |
| AC-18 | 页面模式 watch 不弹独立预览，CLI 后备保留 | cmd:自测「watch page mode: …」；artifact:`-operator.sh`（`lc_watch --page`、`lc_watch_popup`、`lc` 不变） |
| AC-18 | fixture 调用生产写盘函数 | artifact:自测 `Fixture`（`tracker_state_payload`/`write_tracker_state`、`result_payload`/`write_result`；`results.jsonl` 与 `language-session.jsonl` 行由 `LanguageSession._append_result_line`/`_journal` 追加；预览为真实可解码 PNG；时钟经 `controller.protocol` 受控） |
| AC-12 修订4 | 迁移保留修订3 记录/累计/事件、幂等、旧标签拒绝、新 3 个、第 4 个拒绝、总额不增、迁移失败不清账重建 | cmd:自测 runner 19 项（`-c3-carrier-selftest.log` §2）；反证 §3（R4 runner 红 9） |
| AC-12 修订4（C3-1） | 账本文件不存在时 runner 的任何动作在写盘前拒绝（exit 2），不建目录、不建零计数账本；入口代码到读账本为止无写盘调用 | cmd:自测「runner: missing ledger file is refused before anything is written (C3-1)」；修前红：C3 所核对 runner |
| AC-12 修订4 | 重建候选传输清单、runner 按候选核对 | artifact:`-build-stage-b-manifest.py`（runner 取自候选 git 对象，工作树不同即拒绝）；cmd:`-c3-carrier-selftest.log` §4 |
| AC-12 修订4/5 | Play 登记含零查询/中止、与服务端账本分列；标签 `diag-loopb-5…7`；R5 前禁止 Play/服务 | artifact:`-operations-c.md` §0/§3/§4/§7 |
| AC-12 修订5 | 先供帧后 ask、不抢第一窗；时间窗标为推算（第 2 窗有诊断 4 目视支持、第 3 窗未验证、播种后不沿用）；删除「让它过期」；三门同时满足、不称「候选出现后还有 16 s」；对用户说明阶段 B 目的 | artifact:`-operations-c.md` 文首「这一阶段验证什么」、§3「确认时效」、§4 文首与第 2/3 步；artifact:`-operator-watch.py` 候选行文字（自测「candidate line states the three gates…」） |

## 4. 未验证项与已知限制

1. **没有真实 Unity 会话下的浏览器点击证据**。本会话在应用内浏览器用 scratchpad 假会话（真实 `LanguageSession` + 回放桩 +
   评估集静态帧，零消耗）给用户试看过第一版页面，用户确认布局后才冻结（§6）；替换候选后实现角色又用同一假会话目检了
   UI-1…4：候选图加载后才出现倒计时与可点的确认；保留 PNG 头、改坏图片数据再刷新，页面显示「预览没有显示成功（加载或解码
   失败）」且确认置灰（当时帧差 20/80、未过截止）；杀掉会话进程后点「立即核验」，5 s 等待期间页首「读取 0.0 s 前」持续刷新、
   帧采集时刻持续变旧、提示「请求在途」，之后出现「结果未知」框、原按钮标「（结果未知）」停用；停掉本机服务后出现红色横幅、
   整页变灰、按钮全停。这些目检**不是证据**，不进 AC 与门判定。R5 通过后，新增诊断须在真实 Unity 下核实页面呈现/点击、
   持续供帧、首批追平与至少两张样帧的人眼保真（AC-12 修订4）。
2. **时钟域**：会话截止用单调时钟，桥文件只暴露墙钟；页面在同一台 Mac 上用墙钟算。结果呈现锚点 `issued_unix_s` 早于会话的
   呈现时刻（保守）；查询锚点 `query_unix_s` 比会话的单调提交时刻晚微秒级（不保守，量级可忽略）。系统时钟在 16 s 窗内被
   NTP 跳变时页面倒计时会偏，会话检查不受影响。页面计时归零后确认按钮置灰、服务端也不发送——这只是提示，不产生事件；
   若时钟偏差恰使页面早于会话判过期，操作者可驳回或重新指定，不会写出任何控制。
3. 点击到会话受理约需 CLI 启动加 20 ms 轮询（本机约 0.3–0.5 s），倒计时剩余 < 1 s 时的点击可能被会话按截止拒绝（结果落
   `stale_rejected`，按状态表处理）。页面倒计时 < 3 s 变红。
4. 「本段首见 frame」与 `last_published` 的「变化于」都是页面首次看到的时刻；页面若在播种后才启动，它不是首批帧。操作单要求
   `lc_web` 在 Play 前启动。帧的新鲜度优先用帧元数据 `capture_unix_s`（Unity v3 帧包有该字段），缺失时退回页面首见时刻并标明。
   「结果未知」只记在页面内存里：操作页重启后不再显示，以 `operator-web.jsonl` 与 `lc status` 为准（操作单 C §3 已写）。
   浏览器内的图片加载门与刷新/断连行为不在自动自测里（只做了页面源码层面的断言），由复核读码与获准诊断核实。
   C3-2/C3-3 的修复没有重做浏览器目检（页面只是把单个「结果未知」框改为逐条列出，交互与样式沿用 UI-3 版本）。
5. F5 绑定沿用 watch 的做法：页面在告警期间重启时，绑定到当时 `verification.last_query_id`，与 R4 的 watch 限制相同。
6. `IDLE` 下「重新指定（沿用上次指令）」只在本会话 `results.jsonl` 出现过 designate 后才呈现（会话才有可沿用指令）。
7. runner 修订4 在「+3」上限之外另用 `new_session_labels` 白名单，机械实现「禁止用旧标签续跑」（含账本从未见过的零查询旧号
   `diag-loopb-1`）；第 4 个新会话因不在白名单而拒绝（`session_label:diag`）。修订4 迁移尚未在 F 盘账本执行（R5 通过后按
   操作单 §1 执行，账本缺少/改动修订3 时拒绝且不重建）。
8. 本机服务额外做了 Host 头、Origin 与每次启动随机 nonce 校验，挡住其他网页对 127.0.0.1 的跨站请求；端口固定 8771，
   被占用时拒绝启动。
9. R4 注记与既有限制（F3 OPEN、归档 skip 不作闭合证据、IGNORED_DUPLICATE 优先级等）不变。
10. runner 从此不再能在 F 盘新建 B 账本：账本缺失即拒绝（有意为之，C3-1）；真实账本已存在，迁移仍按操作单 §1 在 R5 通过后执行。
    超时输出在三处转为文本（捕获处、点击处理、日志序列化兜底），只去掉其中一处不会复现 C3-3。

## 5. 给复核角色的范围（R5@K1K3）

- **开轮资格**：`git diff <R4 passed_candidate> <候选>` 在本项冻结操作单集合（PLAY_GOVERNING）上非空 → 开 R5；非返工轮，
  接受裁定要求先 C3 再 R5，R4 的同会话例外**不**延伸到 R5（须新鲜上下文）。C/R 计数、冻结集处置与终局限制按提案原文。
- **须逐文件读**：六个冻结文件全文与 `-c2-carrier-selftest.py` 的本批改动；对照 AC-18、AC-12 修订4/5、§3.4 状态表、AC-1 修订1、
  AC-2 修订1、AC-5 修订1、AC-17 修订1 与 R3 F4/F5。重点：页面的身份绑定与合法动作是否与 `controller/language_loop.py` 的
  `_action_*` 守卫一致；截止锚点与会话 `_check_confirmation` 的对应；`_read_results_log` 的增量读取；runner 迁移在真实账本形状
  （`diag_amendment` 已有修订3）下的行为与「迁移失败不重建」；清单脚本的 runner 取源；本机 HTTP 服务的访问面。
- **focused 重跑**：`python3 docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.py`（约 20 s，含 5 s 真实 CLI 超时一例）；
  反证可按 `-c3-carrier-selftest.log` §3 用 `--runner/--watch/--web` 指向旧版本或变体。
- **次序**：先 C4@K1K3（接受角色对本候选的核对，C3 表中的 C3-1…3 应逐条对应本文件 §3 的三行），再由新鲜上下文复核角色
  核实 §4.3.1 资格后开 R5。C/R 计数、终局限制与「R4 上下文例外不延伸」均按提案原文。
- 替换候选的 UI-1…4 对照提案「用户指定网页功能审查」节逐条核实（该节本身不是 finding/verdict，也不自动成为新验收义务；
  UI-5/6 不在本批，是否及如何处理由接受角色按现行规则定）。
- 不需要 GPU、Unity、5060 或网络；自测只写临时目录。

## 6. 用户在本会话的实现细节选择（`AskUserQuestion`，所选标签逐字；均在 AC-18 已接受范围内，不是新授权）

1. 问：网页上的「指定目标（ask）」怎么输入？选：「预设按钮 + 下拉组合（推荐）」（未选：「预设按钮 + 文本框」「预设按钮 + 一排类别快捷键」）。
2. 问：点「确认候选 k」时一点就发还是二次确认？选：「确认一点即发，停止要二次确认（推荐）」（选项说明含「释放跟踪」同样二次确认；
   未选：「全部一点即发」「确认也要二次确认」）。
3. 问：冻结候选前要不要先用假数据看一眼？选：「先试看再冻结（推荐）」。试看后问是否按此冻结，选：「可以，按这个冻结」。
4. 问：Play 时页面在哪里打开？选：「系统默认浏览器自动打开（推荐）」（未选：「Claude 应用内浏览器面板」「只打印地址，我自己开」）。
5. 第一个 C3 候选提交后、C3 开始前，用户在会话里贴出接受角色网页审查的摘要（三项优先：图片显示成功后才能确认、发送期间继续刷新、
   区分告警前后的核验图片；三项随后建议：未知回执突出同一请求重试、疑似状态允许直接改指令重新指定并显示实际沿用的指令、增加
   执行进度与失败原因）。问：「接受角色审查提的这几条，现在怎么处理？」选：「现在修 UI-1～4，替换候选再交 C3（推荐）」（未选：
   「六条都现在做」「不改，原样走 C3→R5」）。该选择改变的是尚未核对的候选内容，范围仍在 AC-18 之内；是否需要记入授权账本
   请接受/辅助角色判断（实现角色对账本只读）。C3 已判定该五项选择无需另入关键授权账本。
6. C3@K1K3 完成后，用户说「查看accept的结果」。实现角色汇报 C3 结论与三项待核实主张属实后问：「C3 附的三项问题都属实，现在怎么走？」
   选：「先修 C3-1～3，再走 C4→R5（推荐）」（未选：「原样交 R5」「先不动，我再想想」）。
