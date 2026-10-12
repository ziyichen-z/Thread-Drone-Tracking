# COORD-015 A5/A7 夹具演练证据（2026-09-25 本地 / 2026-09-26 UTC，supervisor 协调批次）

**接受角色：Kimi Code / k3-256k，经 codex exec**（提供方 `kimi`，模型 `k3-256k`；每次 codex 日志头均为
`provider: kimi`、`model: k3-256k`）。构思/复核 = Claude Code 子代理 Fable，实现 = Opus，辅助 = Sonnet；
supervisor = 本会话（Claude Code `/supervisor`，Opus 5.5）。

**合成演练，不构成任何真实 D/C/R 轮次或门决定。** 夹具内的 `DRILL-001/002` 裁定、代拍、复核 verdict
与「用户处置/user_quote」都是合成的；标为「合成注入」的用户话语是演练脚本，不是用户原话。

授权：账本 2026-09-25「用户授权 A5/A7 夹具演练协调批次（含 A4 验收入库）」与同日「用户指示：五角色运行地改回本机」；
接受角色调用形态按同日「用户指示：A5/A7 演练接受角色改用 Kimi（k3-256k，经 codex exec）」（本批代录）。
未签任何信封、未启用 supervisor、未派发任何真实工作项、未触碰真实 `P1-*` 或暂停项。

## 0. 环境与方法

- 夹具：`python3 tools/make_supervisor_drill.py --dest <scratchpad>/drill`（会话临时目录，初始提交 `09a8941`），
  另建本地裸仓库 `<scratchpad>/drill-origin.git` 作 `origin`（F2 用 `git merge-base --is-ancestor <cand> refs/remotes/origin/main`）。
  演练结束时夹具 HEAD `b85d793`，共 40 个提交。夹具派发日志全文复制为 `docs/evidence/COORD-015-drill-dispatch.jsonl`
  （78 事件：requested 18 / started 16 / end_confirmed 17 / finished 12 / reconciled 3 / aborted 3 / duplicate_callback 9；
  每个 dispatch_id 终态事件恰 1 条）。它是合成日志，**不是**真实调度事实源 `docs/evidence/supervisor-dispatch.jsonl`（后者仍不存在）。
- 接受派发的固定形态：`source ~/.zshrc >/dev/null 2>&1; codex exec -c model_provider="kimi" -m "k3-256k" --sandbox danger-full-access -c approval_policy="never" "<提示>"`，
  cwd = 夹具；每次调用前 `[ -n "$KIMI_API_KEY" ]` 均通过。为取 pid，以子 shell 后台方式运行上述命令（⑥戊-2 故意不取 pid）。
- 子代理派发：Agent 工具，`run_in_background`，提示正文写入文件、sha256 入 `requested.prompt_sha256`，子代理先读该文件再执行。
- 夹具无 `check_role_writes.py`/`check_docs.py`：派发提示把两项自检改为「`git status --porcelain` 只含允许路径 + 状态板表格式完好」，
  尾注仍为 `Role-Check: <role> pass`。
- 核查脚本（会话临时目录，未入库）：从夹具派发日志取 `base_head`/`round`/`role`，按 `git log --all --grep=Dispatch-Id` 解析
  commits/candidate，逐项算 F1、F2、F3a 磁盘、F3b（两列 diff 按角色允许集）、F4 磁盘、F6 磁盘、F8 磁盘；F3a/F4/F5/F8 报告项、F5 与
  F9/F10 由 supervisor 对照被指文件逐条比对。
- 回调口径：Agent 子代理的 hand-back 消息 = `callback`；随后同一运行者的 task-notification 完成通知 = 第二次回调 → `duplicate_callback`。
  codex 以 `kill -0 <pid>` 失败取 `pid_gone`；退出码不作成败依据（五次 codex 均 exit 0），核销只看带内报告与磁盘凭据。

## 1. 逐段结果（核查项 pass / fail / N/A）

记号：F3a/F4/F5/F6/F8 写「磁盘+报告」表示两侧都比对；报告缺失时报告项记 N/A。

### ① 正常接力与 D1 代拍（DRILL-001）

| 派发 | 运行者 | 候选 | F1 | F2 | F3a | F3b | F4 | F5 | F6 | F8 | F9 | F10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 构思 D1 | Fable 子代理 | `436a3b5` | pass | pass | pass | pass（新增 PROPOSED+ACTIVE 行） | pass | N/A（构思无数字主张） | pass | pass | N/A | N/A |
| 接受 D1 | Kimi codex pid 74715 | `d2a5220` | pass | pass | pass | pass（→REVISION_REQUESTED_ROUND_1） | pass | pass（open_items 4 = AR1-1…4） | pass | pass | N/A | N/A |
| 构思 D2 | Fable 子代理 | `0dd6d20` | pass | pass | pass | pass（ROUND_1→PROPOSED_D2） | pass | N/A | pass | pass | N/A | N/A |
| 接受 D2 | Kimi codex pid 75572 | `e55b3ac` | pass | pass | pass（owner=supervisor） | pass（→ROUND_2） | pass | pass（open_items 2） | pass | pass | N/A | N/A |
| 构思 D3 | Fable 子代理 | `d2f7b62` | pass | pass | pass | pass（ROUND_2→PROPOSED_D3） | pass | N/A | pass | pass | N/A | N/A |
| 接受 D3 | Kimi codex pid 76404 | `913f153` | pass | pass | pass | pass（→ROUND_3） | pass | pass（open_items 2） | pass | pass | N/A | N/A |

- supervisor D1 代拍（D2 后）：Owner=supervisor 触发；r(2)=2 < r(1)=4、决策信封 D1 在效、supervisor 非作者、同轮首次。代拍前
  `git fetch` + `check_ledger.py --first-invalidation` → X none；主题提示无命中。条目暂存后 `check_ledger.py --root <夹具>`
  预提交视图 pass；`precheck_head` `bc75de9` = commit(E) `8f26024` 的首父；单独提交，随后另一提交把交接回构思 D3。**pass**
- D3 后：r(3)=2 ≥ r(2)=2 → §5.1 禁项（未严格递减）→ 不代拍，按 (a) 停下交用户。反证：临时暂存 round D3、now=2、prev=2 的 D1 条目，
  预提交视图拒绝「open_items 未严格递减（2 >= 2）」，随即撤回未提交。**pass**
- 停下前六次派发之间无用户介入（用户改接受提供方的指示发生在 ① 开始之前）。**① 适用项全 pass。**

### ② 重复派发

- chore-1（Sonnet）运行中尝试派发 DRILL-002 → 去重列出未终结派发 → 拒绝，未写 `requested`。**pass**
- chore-1 finished `eedcfc7`：F1/F2/F3a（磁盘+报告）/F3b/F4（磁盘+报告）/F6/F8（磁盘+报告）pass，F5 N/A（无数字主张）。
- 同一运行者随后的 task-notification = 第二次回调 → `duplicate_callback`，finished 仍 1 条。**pass**
  （同一机制在全部 9 个正常结束的子代理派发上都出现，均只核销一次。）

### ③ 报告丢失核销 → C 轮 → 复核（含 ⑥甲）

- impl-2（Opus）按脚本推送后 `sleep 60` 再回调、回调只写「结束」。⑥甲：02:52:08Z 轮询见提交 `559c2e7` 已在 origin，
  此时尚无结束凭据 → 等待、不核销、不派发；中途一次「等待自身后台任务」的中间状态通知不作凭据。**pass**
- hand-back 到达 → `end_confirmed(callback)`，报告缺失、有提交 → 无报告来源核查：F1 pass / F2 pass / F3a 磁盘 pass（报告 N/A）/
  F3b pass / F4 磁盘 pass（报告 N/A）/ F5 磁盘 pass（新 Log「Ran 6 tests」= 证据文件，报告 N/A）/ F6 磁盘 pass（报告 N/A）/
  F8 磁盘 pass（报告 N/A）/ F10 pass（AC-1/2/3 均带 test:/artifact:/cmd:）→ `reconciled(report_lost)`，
  candidate 按 §3.4 = `reconciled.candidate` `559c2e7`。**pass**
- 接受 C1@K4（Kimi codex pid 78004）finished `04a31a4`：F1/F2/F3a/F3b/F4/F5（核对表「Ran 6」= 证据）/F6/F8 pass；核对表候选 = `559c2e7`。
- 复核 R1@K4（Fable）：提示 = 夹具 `review.md` 正文 + 夹具机制 + 固定任务（work ID、候选、交接行原文），不含实现 claims。
  finished `5e01d41`：F1/F2/F3a/F3b（两列不变）/F4/F5/F6/F8 pass；**F9 pass**：`round_candidate` = `559c2e7` = 解析候选 ≠ 复核提交 `5e01d41`；
  verdict `REWORK_REQUIRED`，按规则无 `passed_candidate`。

### ④ 用户暂停（DRILL-002）

- chore-1（Sonnet，先 `sleep 240`）started 后合成注入「暂停 DRILL-002」→ stop_call 成功 → `end_confirmed(stop_call)` →
  `aborted(user_pause)`；无 DRILL-002 提交、无残留文件；之后 DRILL-002 不再派发。**pass**

### ⑤ 未知消耗与主题提示

- 未知消耗：chore-2（Sonnet）按脚本向夹具消耗账本追加事件、不提交、回调只写「结束」→ `end_confirmed(callback)`，无提交 →
  §3.4 第 3 支：工作树不干净、账本事件 `2026-09-26T02:50:32Z` 晚于 `started_at` `02:49:58Z` → 不重派、不记 `runner_gone`，停下（(h)）；
  停下期间派发 impl-2 被去重拒绝。合成用户处置后以 `aborted(runner_gone)` 终结（不重派）。**pass**
- 主题提示第一次尝试：生成器预置的 K4 执行信封，守卫得 X = `a399269`（① 布置时移除 DRILL-001 Gate 行 → §5.6 (ii) 永久到期）→
  拒绝 SUB 代拍。守卫行为正确；夹具观察见 §3。
- 主题提示正式：夹具布置合成执行信封 v2（S = `9577283`，预提交视图 pass）→ 提交 `4d4bcfc` 主题「DRILL-001 C1@K4 …」只改 Log →
  模拟 SUB 追加申请前守卫：X none；主题扫描 S..HEAD 命中 → 按 §3.6 (i) 停下，未写代拍条目、未产生 X（复跑仍 X none）。**pass**

### ⑥ 结束未确认不判终态

- (甲) 见 ③。**pass**
- (乙) chore-3（Sonnet）started 后宣布「模拟重启」，其回调视为不可见。对旧 id 的 stop_call：第 1 次返回成功（同会话仍可寻址，
  真实重启后不可得，**不采作凭据**，如实记录）；第 2 次返回 `not running (status: killed)` → 状态未知 → 停下、派发保持未闭
  （对账列出未终结，拒绝其他派发）。注入合成 user_quote → `end_confirmed(user_quote)` → 提交 `c13743a` 存在 → 无报告来源核查：
  F1/F2/F3a 磁盘/F3b/F4 磁盘/F6 磁盘/F8 磁盘 pass，报告项 N/A，F5 N/A → `reconciled(report_lost)`。**pass**
- (丙) 四次 codex 派发均以 `kill -0 <pid>` 失败取 `pid_gone` 后才写终态；pid 复用样例：借用存活 pid 73541，`kill -0` 成功但
  `ps -o lstart=`「Fri Sep 25 22:23:36 2026」≠ 记录的 runner_start「Fri Sep 25 22:33:05 2026」→ 判复用 → `pid_gone`
  （样例只做判定，不写日志）。**pass**
- (丁) chore-4 写 `requested` 后拉起、故意不写 `started`（模拟中断）→ 重启对账：只有 `requested`，基线 `requested_at`/`base_head`，
  无带该 Dispatch-Id 的提交、无晚于基线的消耗事件 → 不得记 `runner_gone` → 停下索取 user_quote；派发 DRILL-003 被去重拒绝。
  03:07:26Z 旧写者提交 `23b4b4f` 出现 → 仍须 `end_confirmed`；注入合成 user_quote → 无报告来源核查（同 ③）全 pass →
  `reconciled(report_lost)`，candidate 由 git 解析。**pass**
- (戊) 显式启动错误：以不存在的子代理类型启动 → 工具当场报「Agent type 'drill-nonexistent-role' not found…」、无 id →
  `aborted(launch_failed, proof=<错误原文>)`；零消耗重派 1 次（新 dispatch_id、沿用 `request_ids`）→ finished `a222279`，
  F1/F2/F3a/F3b/F4/F6/F8 pass，F5 N/A。启动无 id 且无错误：接受 disp-1 直接后台运行、不取 pid → `started(runner_id: unknown)`；
  期间派发 DRILL-003 被拒；后台任务完成通知内报告首行 dispatch_id 匹配 → `end_confirmed(callback)` → finished `35eb3fe`，
  F1/F2/F3a/F3b（接受改 Overall→REWORK_REQUIRED）/F4/F6/F8 pass，F5 N/A。**pass**

### A7 实现子代理合成派发

- 夹具布置：合成用户处置后直置 ACCEPTED、Implementation 列 `IMPLEMENTING`（非真实轮次）。
- impl-1（Opus）finished `522b631`：F1 pass / F2 pass / F3a pass（磁盘+报告）/ **F3b pass**（Implementation 列 IMPLEMENTING→IMPLEMENTED，
  Overall `ACCEPTED`、Lifecycle `ACTIVE` 不变）/ F4 pass（磁盘 3 路径 + 报告 6 指针）/ F5 pass（Log「Ran 5」= 证据「Ran 5 tests」= 报告）/
  F6 pass / F8 pass / F9 N/A（非复核轮）/ F10 pass（`## 自证`：AC-1 test:+artifact:，AC-2 cmd:）。
- 反例：以 `522b631` 为基造未推送提交 `361a392`，把本行 Lifecycle 改为 `PAUSED`，同一核查判 **F3b fail**「Lifecycle `ACTIVE`->`PAUSED`」（按预期失败）。
- 未触及真实 `P1-*` 与 infra。**A7 适用项全 pass。**

## 2. 额度读数

Claude 侧读数取自桌面应用用量接口（账户级整数百分比，含本 supervisor 会话自身消耗，无法按派发拆分）；子代理 tokens 取自
各派发 task-notification 的 `subagent_tokens`。codex 侧取自 `~/.codex/sessions` 当次 rollout 最后一个 `token_count` 事件的
`total_token_usage`；五次 rollout 的 `rate_limits` 各字段均为 null（Kimi 提供方不回传额度窗口）。

| 时刻（UTC） | 节点 | 5 小时窗口 | 周 · 全模型 | 周 · Fable |
|---|---|---|---|---|
| 02:24 | 开工 | 20% | 7% | 13% |
| 02:27 | ② chore-1 派发前 | 21% | 7% | 13% |
| 02:30 | ② 回调后 / ④ 派发前 | 22% | 7% | 13% |
| 02:31 | ① 构思 D1 派发前 | 22% | 7% | 13% |
| 02:36 | 接受 D1 后 / 构思 D2 前 | 24% | 7% | 13% |
| 02:42 | D1 代拍后 / 构思 D3 前 | 26% | 7% | 14% |
| 02:48 | ① 停下后 / A7 前 | 27% | 8% | 14% |
| 02:52 | ⑤ 后 / ③ impl-2 前 | 28% | 8% | 14% |
| 02:57 | C1@K4 后 / R1@K4 前 | 29% | 8% | 14% |
| 03:12 | 演练结束 | 33% | 8% | 14% |

子代理 tokens（task-notification）：chore-1 61,982；构思 D1 58,566；构思 D2 65,571；构思 D3 60,783；impl-1 60,100；
chore-2 61,867；impl-2 63,935；复核 R1@K4 73,466；chore-4 66,378；chore-5（重派）66,711；DRILL-002 chore-1 与 chore-3
被 stop_call 停止，通知未给 usage → N/A；launch_failed 那次未创建运行者 → 0。

| codex 派发 | 会话 id | token_count 事件数 | input | cached input | output | total | stdout「tokens used」 | rate_limits |
|---|---|---|---|---|---|---|---|---|
| 接受 D1 | 01a0db8f-23c0-… | 7 | 419,992 | 361,984 | 1,646 | 421,638 | 59,654 | 全 null |
| 接受 D2 | 01a0db94-fd1a-… | 8 | 489,882 | 482,304 | 2,220 | 492,102 | 9,798 | 全 null |
| 接受 D3 | 01a0db99-0018-… | 7 | 429,446 | 422,144 | 2,000 | 431,446 | 9,302 | 全 null |
| 接受 C1@K4 | 01a0dba2-02fe-… | 10 | 511,903 | 504,897 | 2,424 | 514,327 | 9,430 | 全 null |
| 接受 disp-1 | 01a0dbb1-1717-… | 6 | 369,460 | 361,472 | 1,835 | 371,295 | 9,823 | 全 null |

stdout「tokens used」= input − cached input + output（五次均吻合），首次调用缓存未热故明显偏高。

## 3. 观察与披露

1. **夹具设计冲突**（观察，非判定失败）：生成器让 DRILL-001 同时带「已接受」Gate 行与 K4 执行信封，而 ① 要从构思 D1 起步；
   为让构思 D1 合法新增 Gate 行（F3b 允许集），布置提交 `a399269` 移除了该行，按 §5.6 (ii) 使预置执行信封永久到期。
   ⑤ 因此另布置 v2 信封。建议后续夹具把 ① 与 ③/⑤ 放在不同 work ID，或布置顺序先演 ⑤ 再演 ①。
2. **合同来源不唯一**（合成内容）：① 停在 ROUND_3 后夹具直置 ACCEPTED，实现按派发提示的合成范围写码；复核 R1@K4 据提案 D1–D3 正文
   给 REWORK_REQUIRED（R1-1…6、CLARIFY-1/2）。复核正确识别了不一致，不影响核查判定。
3. **报告字段不可信的实例**：chore-4 报告里的「完整 SHA」`23b4b4f7b5a5…` 是编造的（真实 `23b4b4f4f880…`）；候选按 §3.2 由 supervisor 运行时从 git 解析，未采用报告值。
4. **被拉起角色改写已推送提交**：构思 D2 首次提交 `f46be89` 尾注顺序不合，子代理 amend 为 `0dd6d20` 后 `--force-with-lease` 重推；
   远端无分支含 `f46be89`，未造成候选歧义。现行规则未禁止此做法，记录供接受/复核参考。
5. **supervisor 操作失误**：写接受 D1 的 `finished` 时命令拼错，多追加 1 行无 candidate 的 `finished`（未提交），当场删除后重写；入库日志每个 dispatch_id 终态恰 1 条。
6. **超出核查方法的动作**：A7 核查时 supervisor 在夹具内多跑了一次 focused 测试（Ran 5 OK），不作为判据。
7. **会话卫生**：本协调批次（不在 §3 循环内）上下文约 29 万 token，超过细则「15 万 token 收工重开」阈值；如实披露。
8. **stop_call 在同会话可达**：⑥乙 第 1 次 stop_call 成功是同会话寻址所致，真实重启不可得；故以第 2 次失败走未确认分支。

## 4. 同批入库的其他证据

- A4：`docs/evidence/COORD-015-A4-grep.log`（六个入口 `.claude/commands/{fable,accept,implement,review,chore}.md` 与仓库外
  `~/.codex/prompts/codex.md` 的 `grep -c` 均为 3，报告必填字段 9/9）。
- 全套测试：`docs/evidence/COORD-015-tests.log`（`Ran 1640 tests`，本批 C1 退回项修复后重跑；落地批次为 1634，差 6 例为本批新增测试，`FAILED (failures=1, errors=9, skipped=27)`；10 项与落地批次
  同名同数，均为既有环境类失败——9 项 error 均为 `No module named 'cv2'`，1 项 fail 为主树 `runtime/frames/*.jpg` 残留使
  `test_dist_data_round4` 归档闭合用例失败；COORD-015 相关测试不在失败之列）。

## 5. 结论

A5 六段（①–⑥，含 ⑥甲–戊）与 A7 在本机运行地（子代理 + 本机 Kimi `codex exec`）下逐项完成，适用核查项全 pass，
预期失败的反例（A7 改 Lifecycle、D1 不递减条目）均判失败。A6 结论不变（未触发 `DEGRADED_MANUAL_ACCEPTANCE`），
A5 ① 为全自动通过。本文件只记录事实；A5/A7 是否满足验收、BC-1/2/4/7/9/10 的符合性，由接受角色与独立复核裁定。
两类信封首签、首次启用 supervisor 仍待用户授权。
