# P1-ENG-LOOP-001 — 阶段 B 操作单 C（诊断、Play 剧本 P1/P2）

**本版状态（2026-09-23，R-B8…11 落实）**：会话每个已确认段接入冻结的 BODY-001 阈值规划器（机身跟随），正式 P1 改为
AC-13 修订2 的「一圈单次演示」，新增源帧保存（`lc_keep`）与一圈取样（`lc_lap`）；此前 R-B1…7、AC-18、AC-12 修订3/4/5、
R3@K1K3 的 F4/F5 与 R5@K1K3 的 F7 沿用。是 K1K2K3 候选的一部分（冻结操作单文件，属 PLAY_GOVERNING）。
**新候选经 C5@K1K2K3 核对并由新鲜上下文 R7@K1K2K3 独立复核通过之前，本单任何 Play（诊断或正式）都不得执行，5060 模型服务
也不得启动**；诊断 1…5 使用的旧版见 git 历史中本文件的先前版本。
Owner: Implementation（Claude Code `/implement`）

合同：D4、AC-13…15（含 AC-13 修订 1/2）、AC-18、AC-19、AC-4 修订3/4、AC-12 修订3/4/5/6 与既有修订。信封：`docs/authorizations.md`
2026-09-22「签发阶段 B（Play 证据）执行信封」、同日「单字段后台运行设置与追加两次诊断」与「本地按钮操作页与追加三次诊断」；
向 5060 传代码按同日「阶段 B 准备三项问答代录」第 2 项。本单是操作说明，不是证据；每次执行的实测写
`docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md`，Unity 证据只认接受/辅助角色代录的 `docs/unity-test-log.md`
条目。旧操作单 A/B（`P1-ENG-LOOP-001-operations.md`）的 A 信封命令一律不在本阶段执行。

**这一阶段验证什么（先对用户说明）**：验证「人看预览、人确认、人判丢与重新指定」这条人机闭环能在真实 Unity 里走通，
出错时按合同停下；新候选里机身由冻结的 BODY-001 阈值规划器跟随（云台接近 45° 限位时机身移动），正式 P1 是一圈按九个
预定点抽样的**单次演示**（AC-13 修订2）。**不**评估跟踪性能、恢复率、模型能力或 BODY-001 的效应量（AC-15；BODY-001
冻结措辞只许「threshold body allocation improves imaging quality」）。诊断 5（旧候选、机身 hold）已测到后台持续供帧与首批
追平；新候选的诊断只查前提（机身命令与运动、首批追平、操作页、两张具名样帧的人眼保真），不替代 AC-13…15 的正式证据。

## 0. 分工、额度与停止条件

| 角色 | 在本单里做什么 |
|---|---|
| 用户 | 关闭 5060 睡眠；打开 Unity、Play、退出 Play；**亲自**当操作者：在操作页看预览、点按钮（终端 `lc` 作后备）；确认、驳回、判丢、解除疑似、重新指定、停止都由用户决定；人眼保真检查 |
| 实现 | 发令前检查（§2）、槽位隔离、采集 worktree 对齐、5060 传输与服务启停（SSH）、起会话/watch/操作页、每次 Play 后收集与计数、如实报告；不替用户做任何确认类决定 |
| 接受/辅助 | 把用户反馈代录进 Unity 日志与账本；归因与关闭 |

| 额度（成功、失败、中止、零查询、`NOT_TRIGGERED` 都计） | 上限 | 记账处 |
|---|---|---|
| 正式 Play（= 正式 session，每个 session 一次 Play） | 8 | prep 文件 §5 Play 记账 |
| 诊断 Play：原信封 | 2（实际已用 3，含 1 次登记外，超用 1；不追认、不冲销，R-B2） | 同上 |
| 诊断 Play：第一次追加（AC-12 修订3） | 2（已用 2/2：`diag-loopb-3`、`diag-loopb-4`，已耗尽） | 同上 |
| 诊断 Play：第二次追加（AC-12 修订4） | 3（已用 1/3：`diag-loopb-5`，旧候选；余 `diag-loopb-6`、`diag-loopb-7`，K1K2K3 通过后才可用，不得新增标签） | 同上；5060 账本 `later_diag_amendments` |
| 每次 Play 仿真时间 / 段数（= 播种次数） | 300 s / 4 | 操作页与 watch 显示 `sim_t`（280 s 起告警）与 `track=<session>-t<k>` |
| 模型启动（5060 服务启动，含失败；正式与诊断合计） | 10（含已用，不追加） | F 盘 `receipts-b/stage-b-ledger.json` |
| 模型查询：每次 Play / 合计 | 40 / 400（含已用，不追加） | 同上（服务端先扣额再执行，超限拒绝且不调用模型）；操作页与 watch 在 query 序号 36 起告警 |

已用数以 prep §5 与 B 账本为准，本单不抄写。**Play 登记（prep §5）与服务端查询账本分列对账**：服务端只记有查询的会话，
零查询或中止的 Play 同样扣 Play 额度，只在 Play 登记里出现，不能用服务端会话数代替 Play 计数。5060 服务脚本 `amend`
一次性把 B 账本迁移到 AC-12 修订4：保留修订3 原记录、累计计数与事件，冻结此前已计费的全部诊断会话（从账本运行时枚举），
只接纳上表三个新标签，第 4 个新诊断会话拒绝；旧标签（含账本没有记录的零查询旧会话号）一律拒绝查询，不得续跑。
重复 `amend` 不再加额；账本缺少或改动了修订3 记录时迁移拒绝执行且不清账重建——这时停下报告，不手改账本。
账本文件本身不存在时（例如 `--root` 指错），runner 的任何动作都以 `STAGE_B_LEDGER_MISSING` 拒绝并退出，不创建目录或零计数账本。
其余上限与首次签发相同。

**硬停止（任一出现即停正式尝试，报告后按原返工渠道处理，不反复试到成功）**：诊断或正式 Play 中
发布门失败（`REINIT_REQUIRED` 且原因 ∈ {`publish_expired`,`catchup_stale`,`orphan_control`,
`image_identity_changed`,`bundle_missing`,`frame_rollback`}）或拿不到可核对的发布收据；操作者切换窗口时
watch 报「帧停滞」（后台运行设置未生效，R-B4：不以字段已改推定生效）；需要改 `controller/`、`tools/`、
`tests/`、`config/`、`Assets/`、`ProjectSettings/` 或本单冻结文件（PLAY_GOVERNING，回 K1K3）；
F3 实际触发（`backend_fatal` 且源于排队计时）——保留原失败，不以记债豁免；机身通道 fail-closed（会话日志
`unexpected_segment_end` 的 `event` = `BODY_COMMAND_FAIL_CLOSED`，或 `publish-receipts.jsonl` 出现 `WRITE_FAILED`）；任一额度耗尽。
不改 `T_pub`、K、场景、跟踪核心，也不靠暂停 Unity 供帧来「通过」。

## 1. 采集 checkout 与环境（新候选复核通过后、第一次新增诊断之前由实现做一次；每次 Play 前 `lc_check` 复核）

- **采集候选 = 复核文件最后一条 `passed_candidate`**（运行时解析，不手抄；R5 通过后即含操作页与 runner 迁移的新候选）。
  Python 客户端只从 detached worktree `~/TetheredDroneTracking-loop-b-capture` 运行：
  实现先 `git -C <worktree> checkout --detach <候选>`，其 HEAD 必须等于候选、`git status --porcelain
  --untracked-files=all` 为空（`runtime/models` 是指向主工作树模型目录的忽略链接）。操作者脚本也从该 worktree
  `source`，watch 与操作页从该 worktree 运行，因此执行的载体字节就是被复核的候选字节。
- **Unity 工程**仍从主工作树 `~/TetheredDroneTracking` 打开。`Assets config ProjectSettings Packages`
  与本单六个冻结文件（本文件、`P1-ENG-LOOP-001-operator.sh`、`-operator-watch.py`、`-operator-web.py`、
  `-5060-runner-b.py`、`-build-stage-b-manifest.py`）相对候选零差异，且同路径无未提交/未跟踪项（含 Unity 异常退出后生成的
  `Assets/_Recovery/`）；`ProjectSettings.asset` 为 `runInBackground: 1`。主工作树 HEAD 可以在候选之后（文档提交与
  COORD-013/014 工具/测试），这些差异不冒称白名单文档，由上述路径逐项核对处置（AC-12 修订3）。
- **客户端解释器** `.venv-loop-client`（用户 2026-09-22 选定，本地复制、零下载）：opencv-contrib-python
  5.0.0.93 + numpy 2.5.1 + Pillow 12.3.0；详见 prep 文件 §3。不改 `.venv-track`/`.venv-language`/`.venv-yoloe`。
  操作页只用 Python 标准库，由同一解释器运行，不新增依赖、不下载。
- **5060 服务**（代码传输授权见文首；只传代码与清单，不传权重/数据）：
  1. 核对 Python 改动只落在传输集合内：新旧两条 `passed_candidate`（复核文件最后两条）之间
     `git diff --name-only <旧> <新> -- controller tools/language_serve.py tools/eng_sft tools/requirements-language.txt`
     只能列出 `controller/gated_publisher.py`、`controller/language_bridge.py`、`controller/language_loop.py` 中的文件（K1K2K3 新候选
     改了 `gated_publisher.py` 与 `language_loop.py`；清单脚本另对阶段 A 副本机检漂移 = 传输集合，否则拒绝生成）；再核对主工作树的 runner 与新候选相同：
     `git diff --quiet <新> HEAD -- docs/evidence/P1-ENG-LOOP-001-5060-runner-b.py`。
  2. `python3 docs/evidence/P1-ENG-LOOP-001-build-stage-b-manifest.py <scratch 下新目录>` 重建清单（从新候选
     git 对象取源文件与 runner——工作树 runner 与候选不同即拒绝生成——并绑定 K 收据），把 staging 五个文件（三个源文件、
     runner、清单）传到 F 盘 `repo-b` 并逐文件比 sha256。
  3. 在 `repo-b` 依次运行（均不加载模型、不扣启动额度）：`operations_5060_b.py amend`（修订4 已于诊断 5 前记入；重复
     `amend` 不再加额，输出应仍是修订3 与修订4 两条原记录）→ `operations_5060_b.py preflight`（118 个文件、base/adapter、
     K 绑定、GPU 全过）。`serve` 未记修订4 时拒绝启动；`amend` 拒绝时停下报告。服务形态、端点、权重身份从 K 收据绑定，不得更换。
  4. 服务在 §2 其余检查通过后才启动（每次启动扣 1 次额度）；SSH 前台常驻（阶段 A 的分离进程曾无声消失），
     PowerShell 命令经 `-EncodedCommand` 传入。

## 2. 每次 Play 前的发令检查（实现执行，输出写 prep 文件；任一不过即不开 Play）

**顺序固定**：先由用户打开 Unity，再做检查（诊断 1 的 `_Recovery` 漏检就是因为检查早于 Unity 打开）。

1. 用户确认：5060 已接电源并关闭睡眠（电源选项「睡眠：从不」），Tailscale 在线；用户已在主工作树打开 Unity、
   载入场景 `Assets/SimplePoly City - Low Poly Assets/Demo/SimplePoly City - Low Poly Assets_Demo Scene.unity`，
   **没有按 Play**；Unity 窗口非全屏（操作页浏览器窗口要和 Unity 并排可见）。Unity 版本 `6000.4.1f1`。
2. `python3 tools/check_docs.py` 通过；Active handoffs 只有本项一条未暂停的 `Consuming=yes`；无未 release 的 `blocks_consuming_gate`。
3. 槽位隔离（**只移动、不删除**）：把 `runtime/frames/` 内容与 `metrics.json`、`tracking_observation.json`、
   `body_command.json`、`gimbal_command.json`、`language_request.json`、`language_result.json`、
   `tracker_state.json`、`m3_body_truth.jsonl` 中存在者移入 `runtime/hold-<本次标签>/`，记录移动前后
   sha256 与帧计数；`runtime/frames/` 留空目录。`runtime/scenario_config.json` 必须不存在（生效配置 =
   `config/scenario.default.json`，hz 5 / R 128，与 K 收据一致；否则会话以 `CONFIG_MISMATCH` 拒绝）。
4. `source <worktree>/docs/evidence/P1-ENG-LOOP-001-operator.sh <会话号>` 后运行 `lc_check`：除「5060 /status idle」
   外必须全部 `ok`（worktree HEAD = 候选且干净、主工作树冻结路径零差异且无未跟踪项、`runInBackground: 1`、
   Unity 已打开、槽位文件与锁不存在、`runtime/frames` 为空、无 track/language 进程、无残留操作页与帧保存进程）。
5. 启动 5060 服务（计 1 次启动），`/status` 为 `idle` 且身份与 K 收据一致；再运行一次 `lc_check`，须全部 `ok`。
   两次输出自动追加到 `<opdir>/precheck.log`，实现把最后一次原样抄入 prep 文件（即 §4.5 的两处 HEAD/status 与路径 diff）。
6. 首次正式 Play 之前：新候选下的机身命令与运动、首批追平、操作页，以及两张具名样帧的人眼保真（路径、确认人、结论）
   已在新增诊断中完成并记录（§4，AC-12 修订6）；一圈取样规则与源帧保存方法按 §5 冻结，不在 Play 之间改动。
7. 在 prep 文件 §5 先登记本次 Play（标签、会话号、类型），再开 Play；中止与零查询也照计。

## 3. 终端、操作页与命令

每个终端都执行 `source ~/TetheredDroneTracking-loop-b-capture/docs/evidence/P1-ENG-LOOP-001-operator.sh <会话号>`（同一个会话号）。
会话号：新增诊断 `diag-loopb-6`（`-7` 为余量），正式 P1 `loopb-p1-<n>`，正式 P2 `loopb-p2-<n>`，同号不复用；
旧诊断号 `diag-loopb-1…5` 一律不得再用（5060 服务拒绝已计费的旧号查询，零查询的旧号同样禁止）。

| 终端 | 命令 | 作用 |
|---|---|---|
| T1 | `lc_run` | 先自动跑 `lc_check`，不过则拒绝启动（退出码 2）；通过后起会话进程（http/c2-adapter/nanotrack-v2/follow/地面 0.2 m/300 s；诊断自动加 `--diagnostic`，产物在 `outputs/eng-loop/P1-ENG-LOOP-001/diagnostics/<会话号>/`；正式在 `outputs/eng-loop/P1-ENG-LOOP-001-play/sessions/<会话号>/`，段在 `runtime/runs/<会话号>-seg<k>/`）；输出同时写 `<opdir>/session-process.log` |
| T2 | `lc_watch` | 只读监视（页面模式，不再弹预览窗口）：状态变化、每个结果、`sim_t`、query 序号；每 10 s 的行另带机身位置 `body_pos`、相对首段首批写出帧的位移 `body_disp` 与桥上当前机身命令模式 `body_cmd`；首段首批写出时打印「一圈窗口：t0=… 至 …（九个取样时刻 …）」，窗口满时响铃打印「>>> 一圈窗口已满」（只供择时，判定只由 `lc_lap`）；候选出现或告警时响铃并发系统通知「看操作页」，打印可点击的 `file://` 路径；每段首次写出发布帧时打印 `PUBLISHED first track=… last_published=<帧号>`，之后每 10 s 的 `sim_t` 行带当前 `last_published`；告警行写明触发核验的 `query_id`；每秒记录最前台 App 的切换（`FOCUS` 行）、统计 Unity 不在最前台时到达的帧（`unfocused_frames`），最新帧 ≥2 s 不前进时报「帧停滞」，恢复时记停滞时长 |
| T3 | `lc_web` | 起本机操作页（只监听 `127.0.0.1:8771`，Python 标准库、页面内嵌、零下载）并用默认浏览器打开；终端打印每次点击的动作、request_id、退出码与回执；Ctrl-C 停止 |
| T4 | `lc_keep` | 源帧保存（AC-13 修订2 的保全方法）：只读跟随 `runtime/frames/latest.json`，把每个帧包（JPEG + JSON 原字节）复制到 `<会话目录>/source-frames/`，每帧一行写 `source-frames.jsonl`（帧号、仿真/采集时刻、两成员 sha256）；复制前已被淘汰的帧记为缺口，不补造；从不写 `runtime/`；每 10 s 打印 `KEEPER kept=… gaps=…`，Ctrl-C 后打印 `KEEPER stopped kept=… gaps=…` |
| T5（后备） | `lc ask "the red car"` / `lc confirm <k>` / `lc reject` / `lc respecify ["<指令>"]` / `lc verify` / `lc confirm-lost` / `lc dismiss` / `lc release` / `lc stop` / `lc status` | 操作页不可用时的 CLI 后备；令牌取 watch 已呈现的那一个（没呈现过就拒绝发送）；`lc confirm` 只收整数候选编号（不是 request_id）；每条命令的两路输出存 `<opdir>/operator-cli.log`。页面坏了需要 watch 弹预览时，T2 改用 `lc_watch_popup` |

**操作页**（浏览器窗口，和 Unity 并排放）：上方是当前预览大图（候选预览；告警时是**触发告警的那次核验**的预览，
告警期间其他核验在下方另列并标「不是告警触发帧」）、状态与确认倒计时；下方只出现当前状态下合法的按钮：

| 状态 | 按钮 |
|---|---|
| `IDLE` / `LOST` / `REINIT_REQUIRED` | 「指定：the red car」、组合指令（颜色 / 类别 / 左右关系下拉，只能拼出 §3.7 文法内的句子）、「重新指定（沿用上次指令）」（`IDLE` 下仅在本会话指定过后出现）、「停止会话…」 |
| `QUERYING` | 同上（再指定会替换在途查询） |
| `AWAITING_CONFIRMATION` | 每个候选一个「确认候选 k」、「驳回候选」、指定/重新指定、「停止会话…」 |
| `TRACKING` | 「立即核验」、「释放跟踪…」、「停止会话…」 |
| `SUSPECTED` | 「判丢（目标已丢）」、「解除疑似（误报）」、「重新指定（沿用上次指令）」、「立即核验」、「停止会话…」 |
| `backend_fatal` / `TERMINAL` | 只有「停止会话…」/ 没有按钮（须重启会话进程） |

- 每次点击 = 一次采集候选的 `controller.language_loop` CLI（与 `lc` 相同），令牌取**页面当时显示的**候选/疑似/段；
  页面过期（状态或令牌已变）时服务拒绝并提示重看，不会改用新令牌。「停止会话…」与「释放跟踪…」弹二次确认，其余一点即发。
- **候选图真正显示出来之后「确认候选」才可点**：图片加载中显示「预览加载中」，加载/解码失败或预览文件不是可显示的
  PNG 时写明原因并保持置灰（可驳回或重新指定）；换候选后要重新显示成功。
- 回执 `APPLIED` 只表示会话受理了请求，**不等于**播种或写出成功：播种看状态进入 `TRACKING`，写出看页首
  「已写出观测：本段首见 frame N · last_published M」。
- **数据新鲜度**：页首显示「读取 x s 前」、最新帧的采集时刻（超过 3 s 未前进标橙「帧未前进」）与 `last_published`
  最近一次变化。点击等待回执时页面照常刷新，并提示「请求在途」（这期间不能发下一个请求，停止也要等它结束，最长约 5 s）。
  本机服务读不到会话文件时页首红色横幅「页面数据过期」、确认停用；页面连不上本机服务时横幅「本机服务未响应」、
  整页变灰、按钮全部停用——改用终端 `lc` 后备（`lc status` 核对状态）。
- CLI 5 s 内没拿到回执（或 30 s 外层超时，或意外退出——写前拒绝与写者锁忙除外）时页面显示醒目的「结果未知」框和 request_id：
  动作可能稍后执行，先看状态变化；
  原按钮标「（结果未知）」并停用，需要重试只点该框里的「用同一 request_id 重试」（会话按原 id 去重）。可能同时有多条结果未知
  （例如核验与解除疑似都没回执），每条一个框、各自重试；会话日志里之后出现某条 id 的回执时，页面显示「迟到回执」并只解除那一条。
  重试前页面先读会话日志，原回执已到就不再重试、直接显示它；重试遇写者锁忙（例如终端 `lc` 正在写）、CLI 出错或再次无回执时，
  该框保留并注明「上次重试：…」，稍后再点；重试回「已处理过」时页面从会话日志取出原请求自己的回执再解除（R5@K1K3 F7）。
  同一时刻只处理一个点击，重复点击被拒。操作页重启后不再记得之前的「结果未知」，以 `operator-web.jsonl` 与 `lc status` 为准。
- 告警时下方另列的核验图都注明发起时刻：「告警前参考（旧核验，不是本次检查）」或「告警后核验（不是触发帧）」；
  `tracker_failure` 告警在点「立即核验」且结果回来之前，大图位置写「等待本次告警后的核验」，不把告警前的旧图当作本次判断依据。
- 每次点击、拒绝、重试与迟到回执（绑定的页面身份、命令行、退出码、两路输出、回执）追加到 `<opdir>/operator-web.jsonl`。

`<opdir>` = 会话根下的 `operator/<会话号>/`（`precheck.log`、`session-process.log`、`watch.log`、`operator-web.jsonl`、
`operator-cli.log`、`shown.json`）。指令只接受闭集文法（§3.7）：`the <class>` / `the <color> <class>` /
`the <class> to the viewer's left|right of the <class>`；页面下拉与 CLI 都拒绝文法外的句子，不发查询。
**顺序**：§2 通过 → T1 `lc_run` → T2 `lc_watch` → T3 `lc_web`（浏览器打开操作页）→ T4 `lc_keep` → 用户在 Unity 按 Play → 开始操作。
结束：操作页「停止会话…」（或 `lc stop`）→ 用户退出 Play → T2、T3、T4 各 Ctrl-C。Play 后在任一已 `source` 的终端运行 `lc_lap`
（按 §5 冻结规则取九张样图；诊断里只验证工具在真实帧上可用，不作证据）。

**确认时效（当前 K 收据：`K_ret`=30、`K_conf`=50 帧，5 Hz，`T_ret`=6 s、`T_conf`=10 s）**：确认要同时满足三道门——
结果首次呈现后 ≤10 s、查询发出起 ≤16 s、查询帧到最新帧的帧差 ≤80；**不是**「候选出现后还有 16 s」。操作页倒计时取前两道
截止中先到的一个（从会话写出的查询时刻与结果呈现时刻算，刷新、重开页面都不会重置），并同时显示帧差。页面计时到 0 只是提示：
确认按钮置灰并写明原因，不产生任何事件，也不会自动过期。**候选不确认就一直停在 `AWAITING_CONFIRMATION`**；只有合法的
`confirm` 才会触发时效检查，失败时按状态表落 `IDLE`（无过段）或 `REINIT_REQUIRED(candidate_expired)`（有过段），并记
`stale_rejected` 与失败原因；来不及就「驳回候选」或重新指定，不要赶。Play 中切到浏览器或终端是预期操作；Unity 应在后台
继续供帧，但这一点只有诊断能证实（§4 第 2 步）。

## 4. 新增诊断（`diag-loopb-6`，≤300 s；只查新候选的前提，不产生验收证据）

**目标入画时间（只供人择时）**：播种前相机固定朝下时，按 `config/scenario.default.json` 的路线/车速（环长 213 m、2.0 m/s、
一圈 106.5 s）与帧相机元数据推算，红车完整在画面内约为 `sim_t` 0–12 s、99–118 s、206–225 s。这是推算：第 2 窗有
`diag-loopb-4`/`-5` 的实帧支持，第 3 窗未经实帧验证；实际以用户在 Unity 画面里看到红车入画为准，播种后机身跟随，不沿用该预测。
推算只用于操作者择时，不进入控制器、感知输入、传感器元数据或任何自动触发。

1. 按 §2、§3 启动（含 T4 `lc_keep`）；用户在 Unity 按 Play，确认操作页与 T2 出现 `sim_t`。
2. **持续供帧**：全程看 T2——Unity 在后台时 `unfocused_frames` 增加且**没有**「帧停滞」（诊断 5 已在旧候选下观察到，不再单独
   占用入画窗）。出现「帧停滞」→「停止会话…」、退出 Play，停止本次诊断与后续正式 Play，实现整理原因上报。
3. 红车完整入画（第 1 窗能赶上就用第 1 窗，否则第 2 窗）就点「指定：the red car」；约 3–6 s 后大图出现候选，框在红车上 →
   「确认候选 <编号>」；否 →「驳回候选」，再按需重新指定。
4. 确认后看操作页与 T2：进入 `TRACKING`，页首出现「已写出观测」、T2 出现 `PUBLISHED first …` 与「一圈窗口」行（首批追平）。
   **机身**：云台接近限位时 T2 的 `body_cmd` 变为 `velocity_world`、`body_disp` 增长，Unity 里无人机应随红车移动；T4 `gaps` 应为 0。
   出现 `REINIT_REQUIRED` 且原因在 §0 硬停止集合，或机身通道 fail-closed →「停止会话…」、退出 Play，实现整理原因上报，**不进入正式 Play**。
5. 跟踪中至少等到 2 次核验结果；可点「立即核验」。能跟满一圈就等 T2「一圈窗口已满」再停；跟不满也照实停，不延长。
6. **两张具名样帧的人眼保真（workflow §4.3.2、AC-12 修订6，硬性）**：Play 后实现列出两张具名预览——本次指定候选
   `previews/<帧号>-<query_id>.png` 与一张核验预览——的完整路径发给用户；用户对照 Unity 画面逐张说明「车辆/颜色/朝向与运行时一致、
   跟踪框与 VLM 框画在对的位置」是否成立。实现把两张的路径、帧号、确认人与用户原话逐字记入 prep 文件；实现角色看图不能代替。
7. 「停止会话…」→ 退出 Play（≤300 s）→ T2、T3、T4 Ctrl-C。实现随后：从 `publish-receipts.jsonl` 取确认后第一批的
   `load_elapsed_s`/`frame_delta`/`capture_age_s` 与机身通道收据计数（`body_command` 的 `WRITTEN` 速度、`body_safety_hold`、
   `WRITE_FAILED`、`PUBLISH_REJECTED`）；从保存帧元数据算机身最大位移；跑一次 `lc_lap`（只验证取样工具在真实帧上可用，诊断的
   结果不作 AC-13 证据）；连同终态、watch 摘要与点击记录写 prep 文件，并与用户一起决定能否进入正式 P1。
8. `diag-loopb-7` 只作余量：仅当 `-6` 因环境或操作失误未取得第 4/6 步数据时使用，内容相同；诊断不得用于在正式运行之间「试数」，
   也不因数字不理想而改参数重试（workflow §4.3.2）。诊断标签、额度或设备不够时先回用户，不自行新增。

## 5. 正式 P1（`loopb-p1-<n>`，AC-13 修订2「一圈单次演示」；修订1 的离画事件照录）

**目的**：同一个已人工确认的红车段持续覆盖 106.5 s 仿真时间，机身按冻结规划器跟随，九个预定等距取样点由用户逐张确认
「红车可见且跟踪框落在该车上」。只证明一圈按九点抽样的人机闭环演示，**不**证明逐帧跟踪正确率或跨场景性能。

**冻结的取样规则（Play 前冻结，Play 之间不改；实现：`docs/evidence/P1-ENG-LOOP-001-lap-samples.py`，`lc_lap` 调用）**：
- t0 = `publish-receipts.jsonl` 里本会话首条 `WRITTEN` 观测所在帧的仿真时刻；该收据的 `track_id` 即一圈的段。
  窗口 = [t0, t0 + 106.5 s]。九个取样时刻 t_i = t0 + i·106.5/8 s（i = 0…8）只由 t0 决定。
- 每个 t_i 取 `source-frames/source-frames.jsonl` 中仿真时刻最近的已保存源帧（等距时取较早帧）；偏差超过两个采集帧（0.4 s）
  → `MISSING_FRAME`；该帧在段运行日志里无框或 `ok = false` → `NO_VALID_BOX`；该帧本身没有该段的 `WRITTEN` 观测收据
  → `NO_WRITTEN_OBSERVATION`（「对应观测」= 该取样帧自己的已写出观测，C5-1）；保存的 JPEG 与索引行 sha256 或该观测收据里
  跟踪器加载时的 `snapshot_sha256` 不符 → `KEPT_FRAME_IDENTITY_MISMATCH`（C5-3）。不许事后移窗、换帧。
- 窗口归属（C5）：带帧号的收据按该帧仿真时刻是否落在 [t0, t0 + 106.5 s]；不带帧号的记录（状态、退役、安全 hold、无关联拒收）
  从 t0 观测收据起、到第一次只处理窗口之后帧的 `frames_processed` 为止都算窗口内——窗口末帧晚处理时发生的失败照算；
  找不到这样一次处理（窗口没处理完）即 `window_not_fully_processed`，其后记录全部计入。
- 机械条件（任一不满足即列入失败，不豁免）：四个必需日志（发布收据、会话日志、保存帧索引、段运行日志）存在且逐行可解析，
  缺文件或坏行即失败；保存帧覆盖到窗口末，且窗口末 t0 + 106.5 s ≤ 220 s 仿真时间（P1 观察窗，C5-2，即 t0 ≤ 113.5 s）；
  窗口内无 `LOST`/`REINIT_REQUIRED`/`TERMINAL`、无该段退役、无 `unexpected_segment_end`；窗口内无 `PUBLISH_REJECTED`，
  窗口内写出的观测全部是该段 `track_id`；窗口内至少一条 `WRITTEN` 的 `body_command`（`velocity_world`）；保存帧元数据的
  机身位置相对 t0 位移 ≥ 0.5 m。
- 判定：机械条件全过**且**九张图用户逐张确认为「是」→ 本次正式 Play 记 `LAP_DEMO_PASSED`；否则逐项列出不满足的条件。
  修订1 的离画事件与 E1 结局仍照录，但 `E1_ACHIEVED` 不代替本次通过；未发生离画不记旧 `NOT_TRIGGERED` 失败。

**源帧保全方法**：T4 `lc_keep` 全程运行（§3），九张图从 `<会话目录>/source-frames/` 取；每帧复制后回读核对 sha256，
不符即删除并记缺口；保存帧缺口如实记录，取样点 ±0.4 s 内无保存帧即该点 `MISSING_FRAME`。

**操作**（观察窗 ≤220 s，整次 Play ≤300 s）：
1. 按 §2、§3 启动（含 T4）；Play 后红车完整可见时点「指定：the red car」→ 核对预览 →「确认候选 <k>」。**用第 1 窗**
   （约 `sim_t` 0–12 s）：一圈窗口须在 220 s 内结束（t0 ≤ 113.5 s），第 2 窗只有其前段（约 99–113 s）还来得及，更晚即判不通过。
2. 确认后不干预：页首出现「已写出观测」、T2 打印「一圈窗口」行，之后看 T2 的 `body_disp` 增长与机身跟随。窗口内**不要**
   判丢、释放、重新指定或停止——这些都会让本次一圈不通过。
3. 疑似告警（`SUSPECTED`）：看触发核验的预览——误报（红车在画面内且框在车上）点「解除疑似」，段不变、窗口继续；确实丢了/框已漂走
   → 如实点「判丢」，按修订1 记离画事件与后续「重新指定 → 新段」链路，本次一圈记为不通过。`tracker_failure` 先点「立即核验」再判断。
4. T2 打印「>>> 一圈窗口已满」后「停止会话…」→ 退出 Play → T2、T3、T4 Ctrl-C。
5. 实现运行 `lc_lap`：得到机械判定与九张带框图（`<会话目录>/lap-samples/lap-<i>-f<帧号>-t<仿真时刻>.png`）及九宫格总览，
   把九张图发给用户；用户在聊天里**逐张**回复「是/否」（红车可见、框在车上），实现逐字记录路径、帧号、时刻与原话，写入
   `docs/evidence/P1-ENG-LOOP-001-play-cases.md`，由接受/辅助角色代录 `UT-P1-ENG-LOOP-001-P1`。
6. 正式额度用尽仍无 `LAP_DEMO_PASSED` → AC-13 `NOT_MET`，工作项不能 DONE，交接受角色归因、回用户；不改场景、不改规则。

## 6. 正式 P2（`loopb-p2-<n>`，AC-14）

目的：静止同类多车时，`ambiguous` 是否被显式呈现并由人选定；其他结局如实报告。

1. Play 后在 Unity 画面（播种前相机朝下）找一个**画面内至少有 2 辆同类车**的类别，用组合指令选该类别、颜色与左右关系都留空
   （G3 同款 `the <class>`，例如 `the car`、`the suv`），点「发送组合指令」。画面里找不到任何同类 ≥2 的类别时，
   本次记为无法执行并停止，不改场景、不移相机。
2. 结局与适用检查：`ambiguous` → 预览里全部候选都有编号、每个候选一个确认按钮 → 选一辆点「确认候选 <k>」并确认播种成功；
   `unique` → 仍要确认（记「歧义未识别」）；`none`→`retry_exhausted`、`parse_failed`、`backend_error`、
   `stale_rejected`、`no_new_frame` → 如实记录，确认 N/A。
3. 播种后跟踪约 20 s 即可「停止会话…」；「歧义识别成功」只单列计数，不是通过条件。

## 7. 每次 Play 之后（实现）

1. 复制证据：会话 `language-session.jsonl`、`results.jsonl`、`publish-receipts.jsonl`、`previews/`、`lap-samples/`（P1）、
   `source-frames/source-frames.jsonl` 与九个取样帧的源帧（P1；其余保存帧留在原始路径并记清单 sha256）、
   `<opdir>/` 下六个文件、段运行目录清单 → `docs/evidence/P1-ENG-LOOP-001-play/<会话号>/`（诊断不复制进证据目录，只在 prep 文件记摘要与原始路径）。
2. 读 5060 B 账本（`operations_5060_b.py ledger`），与客户端 `results.jsonl` 的实际调用逐条核对；前置拒绝单列；
   Play 登记与服务端会话分列对账（零查询 Play 只在 Play 登记里）。
3. AC-15 描述性数字（查询次数、`frames_late`、端到端时延、重试、verdict 计数、疑似误报、处置延迟、重指定次数、终态；
   机身通道收据计数与最大位移、保存帧缺口数、`lc_lap` 机械判定与九张图的用户原话）写 play-cases，不写成跟踪性能主张。
4. 把本次 HEAD/status、操作与结果整理成给用户确认的 Unity 日志草稿，由接受/辅助角色代录 `UT-P1-ENG-LOOP-001-P1`/`-P2`。
5. 更新 prep 文件 §5 Play 记账；额度或硬停止触发即停。服务不用时经命令行核验后停止，检查残留进程与 8760 监听为 0；
   操作页、watch 与帧保存已 Ctrl-C（`lc_check` 会拒绝残留的操作页与帧保存进程）。

## 8. 复核注记的操作解读（沿用接受裁定，不改协议）

- 同一 `request_id` 重新写入可能先回 `IGNORED_DUPLICATE`（含 TERMINAL/外会话残留 id 被重用），不表示动作执行；
  新动作用新 id（操作页与 `lc` 每次自动新 id），结果未知的重试沿用原 id：操作页「用同一 request_id 重试」或
  `lc <动作> ... --request-id <原id>`。
- 已完成的 `inconclusive` 核验仍消耗配对帧；发起前跳过的日志可能每 tick 重复；无合法帧的指定重试可能在一个
  tick 内耗尽；`ILLEGAL_WRITER_SUSPECTED` 可能来自合法请求的迟到消费——都按原注记解释，不改查询/完成数口径。
- F3：排队时间计入 worker 硬限可能误报 `backend_fatal`；若 Play 中实际触发，保留原失败，按返工渠道处理。
