# P1-ENG-LOOP-001 — R3@K1K3 返工（F4/F5 + F6 补丁）交付，直接交 R4@K1K3（终局）

Owner: Implementation（Claude Code `/implement`），2026-09-22。
输入：`docs/reviews/P1-ENG-LOOP-001.md` R3@K1K3 `REWORK_REQUIRED`（§3 F4/F5 阻断、F6 CLASS_3 补丁，§5 [实现] 条款）。
按 workflow §4.3.1/§4.4：复核返工不经核对轮，直接回复核；R4 为终局（冻结集 + `RED_LINE` + 修复触及行上的 CLASS_1/2）。
冻结集的「范围内必修 / SCOPE_GAP」裁定由接受角色并行进行（状态板第二条交接），本批按复核 §5 把 F4/F5 当必修处理。
零消耗：零 Play、零模型、零 ID、零 5060 传输。本文件是实现者自证，不是独立复核 verdict。

## 1. 候选与复核范围

- 上轮候选 = 复核文件 R3 §0 的 `round_candidate`。本轮候选 = 首次加入本文件的提交，运行时解析：
  `git log -1 --diff-filter=A --format=%H -- docs/evidence/P1-ENG-LOOP-001-K1K3-r3-fix.md`（不手写 SHA）。
- 修复触及行：`git diff <round_candidate> <本轮候选>`。两者之间另有接受角色 C2 核对提交与 R3 复核提交（只改状态板、提案、
  implementation-status、正式设计、复核文件），与下列触及文件零重叠。
- 触及文件（复核 §5 [实现] 允许的范围内）：
  - `docs/evidence/P1-ENG-LOOP-001-operator-watch.py`（F4/F5，冻结操作单，PLAY_GOVERNING）
  - `docs/evidence/P1-ENG-LOOP-001-operations-c.md`（F4/F5 同步文字；状态行改为「新候选复核通过（R4）之前不开 Play」，冻结操作单）
  - `docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.py`（F4/F5 具名回归 7 项；`--runner`/`--watch` 参数与分部异常捕获，使修前红可由已提交脚本复现——即 F6 的根因）
  - `docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.log`（F6 逐字替换补丁，未改其他行）
  - 新证据：本文件、`-tests-r3-fix-before.log`、`-tests-r3-fix-after.log`、`-tests-r3-fix.log`；状态板
- 未触及：`-operator.sh`、`-5060-runner-b.py`、`controller/`、`tools/`、`tests/`、`config/`、`Assets/`、`ProjectSettings/`、`Packages/`、
  Play 治理门三文件。`git diff --stat <round_candidate> <本轮候选> -- controller tools tests config Assets ProjectSettings Packages` 为空。
- 复核注记（R3 §4 注记 1…7）、F3（`SCOPE_GAP` OPEN）未动；注记 5（`lc_run` 管道退出码被 `tee` 掩盖）属 `operator.sh`，本批不改。

## 2. F4 — watch 看不到发布帧号

**改动。** `Watch.on_published`（每次读到本会话状态都调用，与 STATE 去重键无关）：某段 `track_id` 的
`last_published_frame_id` 首次非空时打印一行 `PUBLISHED first track=<track_id> last_published=<帧号>（首批已写出）`（每段一次）；
10 s 一行的 `sim_t` 行加 `last_published=<当前值>`，用于看增长。STATE 去重键不变（避免 5 Hz 刷屏）。
操作单 §3 T2 行、§4 第 4 步、§5 第 2 步同步：首批判据改为出现 `PUBLISHED first` 行；写明播种瞬间 STATE 行的
`last_published=None` 是初始化发布被静音的正常值；增长看 `sim_t` 行，或 T3 `lc status` 的 `last_published_frame_id`。

**具名回归。** `-c2-carrier-selftest.py` → `test_watch_bridge` → `watch: last_published change is printed (F4)`：
fixture 由 `controller.language_bridge.tracker_state_payload` + `write_tracker_state` 写两份同键 `TRACKING` 状态
（`last_published_frame_id` `None` → 57），两次 tick 后 `watch.log` 含 `PUBLISHED first track=diag-selftest-t1 last_published=57`。

## 3. F5 — 告警预览未按 `query_id` 绑定

**改动。** 去掉悬挂标志 `open_next_verify`：
- `on_result` 把每条核验结果按 `query_id` 存入 `verify_results`（先于任何告警）。
- `on_state` 在首次见到新 `suspect_id` 时建立告警：`lost`/`drift`/`ambiguous` 绑定该状态的 `verification.last_query_id`
  （会话先写触发结果、后写 SUSPECTED 状态，`_handle_verify_outcome` 在写两者之前已把 `last_verify_query_id` 置为触发查询）；
  告警行打印触发 `query_id`。`tracker_failure` 无触发核验，不绑定任何旧核验，告警行提示先 `lc verify`。
- `open_alert_preview`：绑定的 `query_id` 一旦在 `verify_results` 中（无论先于还是晚于状态读到）即打开**该**结果的预览并打印
  `告警触发核验 q=… frame=… verdict=…` 与 `预览文件：file://…`；若其 verdict 与告警类别不符（lost↔none、drift↔drift、
  ambiguous↔ambiguous）则不打开、告警提示用 `lc status` 核对。每个告警至多打开一次。
- 告警期间其他核验结果（如操作者 `lc verify`）打印「该核验不是告警触发帧（告警 q=…），不自动打开；预览：file://…」。
- 离开 `SUSPECTED` 即清除告警。
操作单 §3 T2 行、§5 第 3 步同步（按告警行的 `query_id` 看预览；`tracker_failure` 先 `lc verify` 再点打印路径；标「不是告警触发帧」的
结果不作本告警依据）。

**具名回归。** `test_watch_bridge`，fixture 由 `language_bridge.result_payload` + `write_result` 与 `tracker_state_payload` +
`write_tracker_state` 按生产顺序（先结果、后状态）写盘；`open` 经替换模块内 `subprocess` 记录、不真正执行：
- `watch: straddled alert opens the triggering query's preview (F5)`：tick₁ 读到旧 `TRACKING` + 新核验结果 Q；tick₂ 读到 `SUSPECTED`
  （`last_query_id = Q`）→ 只打开 Q 的预览，日志含 `触发核验 q=Q` 与 Q 的 `预览文件：file://…`。
- `watch: a later verify result is not opened as the alert preview (F5)`：随后核验 R 不被打开，日志标「不是告警触发帧」。
- 另三项加固：告警先于结果读到（watch 重启）时结果到达即打开；`tracker_failure` 不打开任何旧核验且提示 `lc verify`；
  verdict 与类别不符不打开。以及 fixture 目录只有两个桥文件。

## 4. 修前红 / 修后绿

- 修前：`docs/evidence/P1-ENG-LOOP-001-tests-r3-fix-before.log`——已提交的本批自测脚本加 `--watch` 指向 R3 `round_candidate` 的 watch
  （`git show` 到 scratchpad）：F4/F5 相关 6 项 `FAIL`，其余 22 项 `ok`，`FAILED: 6 failed`，退出码 1。
- 修后：`docs/evidence/P1-ENG-LOOP-001-tests-r3-fix-after.log`——默认载体 28 项全 `ok`，`OK: 0 failed`，退出码 0。

## 5. 停点全套（隔离副本，复核 §5 要求）

`docs/evidence/P1-ENG-LOOP-001-tests-r3-fix.log`：在 scratchpad 下 `git worktree add --detach` 的副本（HEAD = R3 复核提交，拷入本批
`docs/evidence` 改动；副本 `runtime/` 只有 `README.md`、无 `outputs/`，即无任何诊断残留），系统 `python3` 跑一次，不带 `-v`，
末尾按名列出全部 skip：`Ran 1524`，`FAILED (errors=9, skipped=68)`，failures 0。
- 9 个 ERROR 与 K1K3 R1 修复批基线（`-tests-r1-fix.log`）排序后逐名相同（8 × `No module named 'cv2'`，1 × `numpy`），**新增失败 0**。
- skip 68（主工作树基线 24）：副本不含未入库资产目录，冻结资产类测试跳过（与 COORD-013 隔离全套先例同数）；其中
  `test_dist_data_round4.RealArchiveClosureTest` 5 项全部以「真实归档不在本工作副本中」skip（日志 `## skipped tests` 节逐项列出），
  所以该测试在本副本里**未执行**，不构成对归档闭合的正向证据。
- 被测代码树哈希与主树 HEAD 相同（`tests`/`controller`/`tools`，见日志首行）；本批改动都在 `docs/evidence/`，不在被测树内。
  副本运行后 `git status` 只有拷入的本批改动，随后已删除。

## 6. workflow §4.3.1 四项自证

1. **范围冻结**：只动复核 §5 [实现] 允许的文件（§1）；合同、K 收据、协议、跟踪核心、模型决策、Unity 设置不变。
2. **相称测试**：修前红/修后绿（§4）；隔离副本全套新增失败 0（§5）。
3. **已知 Unity 失败**：无新增；`runInBackground` 效果、首批追平、人眼保真仍待 R4 通过后的新增诊断，未推定生效。
4. **状态板、候选提交、未验证风险**：交接行转 Review（R4@K1K3），只写本文件指针；风险见 §7。

## 7. 未验证项与已知限制

- 真实 Play 中 watch 的读取时序、`open` 与通知的可见性只有诊断能证实；自测用记录代替真实 `open`。
- 告警绑定依赖会话「先写触发结果、后写 SUSPECTED 状态、两者之间不改 `last_verify_query_id`」的现有顺序（`controller/language_loop.py`
  `_handle_verify_outcome`，候选与 R2 同字节）；若操作者在 watch 首次读到新告警之前已完成另一次 `lc verify`（需在 250 ms 轮询内完成
  一次约 5 s 的查询，实际不可达），verdict 核对会拒绝错配、不打开。
- 冻结集裁定（F4/F5/F6/F3）由接受角色给出；若裁定与本批处理不同，以裁定为准回到实现。
- 复核 §4 注记 2（归档闭合测试对 `runtime/` 残留敏感）的处置归接受角色；主树 `runtime/` 残留本批未动。
