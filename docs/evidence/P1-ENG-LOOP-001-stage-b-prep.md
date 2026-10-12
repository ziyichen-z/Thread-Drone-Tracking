# P1-ENG-LOOP-001 — 阶段 B 准备记录（操作单 C、客户端环境、采集候选、5060 服务）

Owner: Implementation（Claude Code `/implement`，2026-09-22）
合同：D4、AC-1…17 及既有修订；阶段 B 信封见 `docs/authorizations.md` 2026-09-22
「签发阶段 B（Play 证据）执行信封」与提案「阶段 B 信封申请与注记处置」。
本文件只记准备过程与实测；操作步骤见 `docs/evidence/P1-ENG-LOOP-001-operations-c.md`。
本文件不是 Unity 证据，也不代写 Unity 日志。

**接受侧处置已落盘（2026-09-22）**：§6 问答已逐字入账，R-B1…4 见同名提案 Pending rulings。
下文原计数/待裁请求按发生时保留；当前旧诊断3/2（登记外1次，超用1）、新增诊断0/2，
正式0/8、启动2/10、查询1/400。先改设置及操作单，经C2→R3后再诊断；本记录不发令。

**实现会话更新（2026-09-22 晚，§8）**：新增诊断 2/2 已用（`diag-loopb-3`/`-4`，均持续供帧通过、未播种），额度耗尽即停；
正式 0/8、启动 3/10、查询 3/400，5060 服务已停。用户新要求（按钮操作页、追加 3 次诊断）与待裁定见 §8.6。

## 1. 授权代录请求（实现角色对账本只读，请接受/辅助角色逐字入账）

实现会话中，用户对三个问题的回答如下（`AskUserQuestion`，问题与选项原文逐字；
用户原话 = 所选选项标签）。第 2 项影响信封「下载/资产传输=否」的读法，入账前
实现角色不执行任何向 5060 的传输。

1. 问（逐字）："Mac 端会话进程要在同一个 Python 里同时用到三样东西：冻结版 NanoTrack-v2
   需要的 cv2（opencv-contrib 5.0.0.93）、候选预览图需要的 Pillow、以及 HTTP 客户端。现有环境
   都不全：.venv-track 有 cv2 没有 Pillow；.venv-language 有 Pillow 没有 cv2；.venv-yoloe 的 cv2
   是另一个包（opencv-python），和冻结规格不符。签发的信封规定「下载=否」，接受角色也写明改绑定
   环境要先报告。之所以问您，是因为客户端必须先定下一个环境，操作单 C 才能写。选哪种做法？"
   用户先追问（逐字）："一共要占用多少存储空间？"；实现角色答约 210 MB（cv2 138 MB + numpy
   24 MB + Pillow 40 MB + pip/骨架约 9 MB，放内置盘，剩余 35 GB）后再问
   "知道占用后，Mac 客户端环境选哪种做法？"，用户选（逐字）："本地复制新建（推荐，约210MB）"。
   该选项说明（逐字）："在内置盘新建 .venv-loop-client，约 210 MB：从 .venv-track 复制 cv2 和
   numpy，从 .venv-language 复制 Pillow。不下载，不动现有环境，Play 时不需要 T7。"
2. 问（逐字）："阶段 B 要往 5060 传一点代码：复核通过版本的两个文件，加一个按 B 信封记账的服务
   脚本，合计约 130 KB，不含权重和数据。是否允许？5060 端由谁操作？"
   用户选（逐字）："允许，我经 SSH 操作（推荐）"。该选项说明（逐字）："只传代码、不传权重和数据，
   记录逐文件哈希清单。您开好 5060 和 Tailscale 后，由我经 SSH 启动和停止服务，账本记在 F 盘。"
3. 问（逐字）："本地准备做完以后，这个会话接下来怎么安排？……"
   用户选（逐字）："准备完接着做诊断 1"。该选项说明（逐字）："我做本地准备的同时，您另开 /chore
   把代码传输授权记入账本，并打开 5060。账本记好后，我传代码、启动服务，您按操作单 C 跑 Unity，
   并亲自敲操作者命令。"

**实现角色更正（2026-09-22，问第 2 题时的估算有误）**：实际传输包 179,286 B（约 179 KB，
不是约 130 KB）：候选 `controller/language_bridge.py` 45,535 B、`controller/language_loop.py`
111,756 B、B 服务脚本 7,488 B、哈希清单 14,507 B；类别与问题所述相同（只有代码与清单，无权重/
数据）。已在本会话向用户说明。

范围说明（实现角色的理解，入账时请逐字保留上面原话，下述只作语境）：第 2 项只放行**代码**
传输（阶段 B 服务脚本与复核通过候选的源文件），不放行权重、数据、下载或新增模型/查询额度；
5060 服务启动与查询仍计入已签发的 ≤10 / ≤400 / 每次 Play ≤40。

## 2. 采集候选对应性（2026-09-22 实测；候选从复核文件运行时解析，不手抄）

- 解析：`grep -o 'passed_candidate: …' docs/reviews/P1-ENG-LOOP-001.md | tail -1`；该候选是当前 HEAD 的祖先。
- 采集 checkout：`git worktree add --detach ~/TetheredDroneTracking-loop-b-capture <候选>`；
  worktree `rev-parse HEAD` = 候选，`status --porcelain` 空（0 行）；`runtime/models` →
  `~/TetheredDroneTracking/runtime/models` 为被忽略的链接（NanoTrack 模型目录按
  `PROJECT_ROOT/runtime/models` 解析）。worktree 内 K 收据与两份测量报告 sha 与 K 收据 `source_reports` 一致。
- 主工作树（Unity 工程）：`git diff --stat <候选> HEAD -- Assets config ProjectSettings Packages` 0 行、
  同路径 `status --porcelain` 0 行。候选之后的非 `docs/` 差异只有 `.claude/commands/{chore,implement}.md`、
  `.cursor/commands/coding.md`、`AGENTS.md`、`tools/check_{docs,role_writes}.py`、
  `tests/test_check_{docs,role_writes}.py`（COORD-013/014 协调批次）；`controller/`、`tools/language_*`、
  `tools/eng_sft/`、`tools/requirements-language.txt` 差异 0 行。按接受裁定这些不冒称白名单文档；
  处置方式是 Python 客户端只从候选 worktree 运行，Unity 只读逐字相同的 Assets/config。
- 5060 端：阶段 A 绑定传输清单与候选逐文件比对，推理相关代码（`controller/language_selector.py`、
  `tools/language_serve.py`、`tools/eng_sft/*` 等）一致；`controller/language_{bridge,loop}.py` 为 R1 返工前版本
  （服务进程加载前者），`tools/check_{docs,role_writes}.py` 亦旧但服务不导入。B 阶段在 F 盘建 `repo-b` 并覆盖
  候选的两个源文件；清单 `docs/evidence/P1-ENG-LOOP-001-transfer-manifest-5060-stage-b.json`（118 个文件核哈希，
  两个 check 工具列入 `not_verified`）由 `P1-ENG-LOOP-001-build-stage-b-manifest.py` 生成。

## 3. Mac 客户端环境 `.venv-loop-client`（用户选「本地复制新建」；零下载，未改既有环境）

- 基础解释器与 `.venv-track`/`.venv-language` 相同：uv CPython 3.12.13（macOS arm64）；`python -m venv` 的 pip 来自
  ensurepip 自带轮子（25.0.1，无网络）。
- 复制（`rsync -a`，排除 `._*` 与 `__pycache__`）：`.venv-track` 的 `cv2/`、`opencv_contrib_python-5.0.0.93.dist-info/`、
  `numpy/`、`numpy-2.5.1.dist-info/`；`.venv-language`（T7 site-packages）的 `PIL/`、`pillow-12.3.0.dist-info/`。
  逐文件 sha256 与源相同：1,277 个文件、0 个包不一致，树摘要 `821723903f6a001d…`；占用 185 MB（内置盘）。
- `pip check`：No broken requirements found；`pip freeze`：numpy==2.5.1、opencv-contrib-python==5.0.0.93、pillow==12.3.0。
- 自检（候选 worktree 内运行）：cv2 5.0.0（有 `TrackerNano`）、numpy 2.5.1、Pillow 12.3.0；导入
  `controller.language_loop`/`language_selector`（`HttpAdapter`）/`gated_publisher` 成功；`NanoTrackV2Tracker()`
  通过 OpenCV 版本与模型哈希校验（backbone `530bdd0c…`、neckhead `0d8c0637…`），在
  `runtime/frames.1b-diagnostic-hold` 样帧上 init 成功、5 次 update 2.8–3.7 ms；Pillow 画框成功。
  OpenCV 打印两行 `setPreferableTarget … new graph engine` WARN（与 `.venv-track` 同一轮子）。
- focused：`docs/evidence/P1-ENG-LOOP-001-tests-client-env.log`（候选 worktree，语言四模块 260 项 OK，
  2 skip = `FrozenReplayAssetTests`/`ReplayDemoTests`，worktree 无 `outputs/` 冻结回放资产，Play 不用回放）。
- 另在 scratchpad 用本解释器跑 `replay-demo`（零模型、零 ID，退出码 0），供操作脚本自测：`operator-watch.py --once`
  正确解析真实桥文件（终态 TERMINAL/operator_stop、designate 候选与编号、SUSPECTED 告警），`shown.json` 只记已呈现的
  `result_id`/`suspect_id`；`lc`（zsh）无已呈现令牌时拒绝发送（退出码 2），有令牌时 `--token` 与序号正确传给 CLI、
  两路输出写入 `operator-cli.log`（该次无会话进程，按设计返回「结果未知」退出码 5）。上述自测只写 scratchpad。

## 4. 5060 传输与服务、诊断 1 发令检查（2026-09-22）

**传输（入账后执行；账本 2026-09-22「阶段 B 准备三项问答代录」）**：F 盘 `repo` 本地 robocopy 为 `repo-b`
（150/150 文件）；Mac 打包 `stage-b-transfer.tar`（sha256 `4a07c32f…2583`，4 个文件，内容与已提交的
`P1-ENG-LOOP-001-5060-runner-b.py`、传输清单逐字节相同，两个源文件与候选 git 对象相同）经 `scp` 传到
F 盘并解到 `repo-b`；两端逐文件 sha256 相同：`language_bridge.py` `38de0d51…`、`language_loop.py`
`37528823…`、`operations_5060_b.py` `f11b741b…`、`transfer-manifest-stage-b.json` `4ed2faa7…`。未传权重/数据。

**preflight（零模型加载、零扣额）**：118 个文件哈希、base `7de1838c…`、adapter `4044dd4f…`、K 绑定
（c2-adapter/http/端点 `http://100.100.100.100:8760`）、RTX 5060 Laptop GPU 全部通过，退出码 0。
PowerShell 命令经 `-EncodedCommand` 传入（首次直传因引号解析失败未执行任何命令，未扣额）。

**服务启动 1/10**：沿用阶段 A 的教训（`Start-Process` 分离进程曾无声消失），SSH 前台常驻；服务 pid 17740，
`GET /status` = idle，身份（权重/prompt/词表 sha、revision、cuda）与 K 收据一致；B 账本 `model_loads=1`、
`query_rows=0`。服务日志原始副本在 scratchpad，停止服务时并入证据。

**诊断 1 发令检查（2026-09-22T15:15-0400）**：`check_docs.py` 通过（含消耗性门 blocks 机检）；Active handoffs
只有本项一条未暂停 `Consuming=yes`；`language_session.lock`/`language_request.lock`/`scenario_config.json`
不存在；无 `track_loop`/`language_loop` 进程；`runtime/frames/` 0 项。槽位隔离：`body_command.json`、
`gimbal_command.json`、`m3_body_truth.jsonl` 移入 `runtime/hold-diag-loopb-1/`，移动前后 sha256 相同
（`02d40dbd…`、`ec79e047…`、`f25d912d…`），未删除任何文件。§4.5 身份：采集 worktree HEAD = 候选、
status 0 行；主工作树 HEAD `08d6cc2`（辅助角色代录提交）、status 0 行；候选→HEAD 在
`Assets config ProjectSettings Packages` 上 diff 0 行、status 0 行。

### 4.2 诊断 2 发令检查（2026-09-22T15:59-0400，Unity 已打开原场景、未 Play）

`check_docs.py` 通过；锁/`scenario_config.json` 不存在；无 track/language/watch 进程；槽位已隔离（见 4.1 末条）；
采集 worktree HEAD = 候选、status 0 行；主工作树 status 0 行，候选→HEAD 在 Unity 路径 diff 0、status 0；
5060 `/status` idle（服务第 2 次启动）。诊断 2 会话号 `diag-loopb-2`。

### 4.3 诊断 2（`diag-loopb-2`）结局：未确认、未播种；发现 Unity 失焦即停帧（环境/流程阻塞）

- 15:58:03 会话启动（pid 77385，诊断根；启动时 K 绑定与 5060 实时身份握手通过）；15:59:31 进入 Play（`sim_t=0.2s`）。
- 15:59:37 `lc ask "the red car"`（回执 `APPLIED`）→ 15:59:41 结果 `diag-loopb-2-q1`：`unique`、查询帧 9、
  返回时 `frames_late=13`（≤ `K_ret` 30）、`latency_ms=3851`、`wall_elapsed_s=4.13`、`finish_reason=stop`、
  候选 0 = xywh `[0.374,0.442,0.12,0.075]`，预览 `…/diag-loopb-2/previews/9-diag-loopb-2-q1.png` 已生成，watch 调 `open`。
  用户原话：「做完了，至于预览我没有看到」。
- 16:00:20 用户输入 `lc confirm diag-loopb-2-req-8c16d530`（把 `ask` 输出的 request_id 当作候选编号），CLI 参数校验
  拒绝（`argument index: invalid int value`，退出码 2），**未写入任何请求**；此时距查询 43 s，已超 `T_ret+T_conf`=16 s。
  会话停在 `AWAITING_CONFIRMATION`，未 `initialize`、未建段、发布收据为空，首批追平**未测到**。
- 16:05:28 `lc stop`（回执 `APPLIED`，TERMINAL/`operator_stop`），Play 最高 `sim_t=291.2s`（≤300 s）。模型查询 1 行
  （B 账本：启动 2、查询 1、会话 `diag-loopb-2`=1、拒绝 0），与客户端 `results.jsonl` 1 行一致；零正式 ID。
- **帧停顿与根因**：`sim_t` 在 15:59:42–16:00:32 停在 5.0 s（帧 24）、16:05:26 后停在 291.2 s，与操作者切到终端/预览窗口、
  再切回 Unity 的时刻吻合；诊断 1 在 15:26:21 的停帧（用户离开去处理 5060）与 15:54–15:55 的续跑（回到 Unity）同样吻合。
  `ProjectSettings/ProjectSettings.asset` 第 85 行 `runInBackground: 0`：Unity 编辑器失去焦点即暂停 Play 的帧循环。
  本闭环的操作者动作（终端命令、查看预览）必然让 Unity 失焦，因此在当前工程设置下，任何 Play 都会在操作者操作时停帧
  （跟踪中会触发 `frame_stall`，确认窗口按墙钟被耗掉）。这是 Play 流程/环境阻塞，不是候选代码缺陷；M3 各次 Play
  无需 Play 中交互，故此前未暴露。人眼保真检查未完成（用户未看到预览）。
- 诊断额度：2/2 已用（另有 §4.1 的登记外 Play 待接受角色裁定）。按信封「先用诊断确认首批追平再进正式」，该前提未满足；
  实现角色停止，不启动任何正式 Play。

### 4.1 诊断 1（`diag-loopb-1`）结局：环境中断，未取得首批追平数据

- 15:16:39 会话进程启动（`.venv-loop-client`、候选 worktree；启动时 K 绑定与 5060 实时身份握手通过；
  `--diagnostic`，产物在 `outputs/eng-loop/P1-ENG-LOOP-001/diagnostics/diag-loopb-1/`，`runtime/runs/` 未建）；
  watch 与操作者终端就绪。用户约 15:23:59 进入 Play（watch：`sim_t=0.2s`）。
- 约 15:25 5060 整机失联：挂服务的前台 SSH 以 `Connection reset by peer` 断开（退出码 255），SSH 22 端口与
  `/status` 均超时；用户随后唤醒 5060（用户原话「已经恢复」）。复查时原服务 pid 17740 仍在监听且 idle，但其控制台管道
  已断，按用户指示（原话「已经唤醒了，重启服务」）核对命令行后停止 17740 及其启动器 3404，服务重启 **2/10**
  （pid 见 `receipts-b/server-startup-b-2.json`，身份同 K 收据，查询 0）。
- Unity 帧在约 15:26:21 停在 `sim_t=136.6s`，其后一度到 138.6 s（帧 692）后静止；用户手动重启了 Unity
  （用户原话「已经退出play，是我手动重启无报错」）。实现角色于 15:45:24 经 `lc` 代发 `stop`
  （回执 `APPLIED`，会话 TERMINAL/`operator_stop`），会话进程退出、会话锁释放、watch 停止。
- 本次零查询（`max_query_seq=0`；B 账本 `query_rows=0`）、零正式 ID；会话 JSONL 3 行（启动、stop 回执、TERMINAL）；
  桥上 `tracking_observation.json`/`gimbal_command.json`/`body_command.json` 未被写出（空闲会话零发布）。
  没有 `ask`/`confirm`，首批追平、确认延迟、人眼保真检查**均未取得**。按信封「中止也计」，诊断 1 计 1 次，
  原因 = 环境（5060 休眠/断网 + Unity 手动重启），不是候选缺陷。
- **Unity 恢复目录（发令检查漏项，如实补记）**：15:23 打开 Unity 时生成未跟踪的 `Assets/_Recovery/0.unity`
  （1,772,456 B，与已跟踪演示场景逐字节相同）与 `Assets/_Recovery.meta`；15:15 的发令检查在 Unity 打开前执行，
  未覆盖到，所以诊断 1 的 Play 期间 `Assets/` 实际有这两项未跟踪差异（已跟踪文件零改动）。诊断 2 发令检查
  （15:47）发现后停下，用户选择在 Unity 内自行删除并确认打开原场景；以后每次发令检查在 Unity 打开之后、按
  Play 之前执行。用户删除文件夹后（原话「已经删了，重新打开场景了还没有play」）复查仍剩孤儿
  `Assets/_Recovery.meta`（172 B，sha256 `4b3b58ed…`），实现角色按用户删除意图将其**移动**到
  `runtime/hold-diag-loopb-2b/unity-recovery/`（未删除）。
- **第二段登记外帧（同交接受角色归因）**：15:47 隔离后，`runtime/frames/` 又出现帧 309–436（保留窗 128 帧；
  `sim_t` 62.0→87.4 s，采集于 15:55:04–15:55:30）及新 `metrics.json`/`m3_body_truth.jsonl`，即 Unity 约 15:54–15:55:30
  处于 Play（可能是 15:45 那次暂停后继续），未挂会话、零查询；15:57 复查已停止写帧。已整体移入
  `runtime/hold-diag-loopb-2b/`（257 项，树摘要移动前后相同）。
- **登记外 Play（交接受角色归因）**：Unity 重启后又进入过一次 Play（帧 0–19、`sim_t≈4.0s`，约 15:45），
  未挂语言会话、零查询、零 ID；用户已退出。它不是按操作单登记的诊断/正式 Play，实现角色不自行判定其是否计入
  「诊断 Play ≤2」，如实列入 §5 供接受角色裁定。

## 5. Play 记账（开 Play 前登记，结束后结算；中止也计）

| # | 标签/会话号 | 类型 | 登记时间 | 结局 | 模型启动累计 | 查询（本次/累计） |
|---|---|---|---|---|---:|---|
| 1 | `diag-loopb-1` | 诊断（≤300 s，正式 ID 0） | 2026-09-22T15:16-0400 登记 | 中止（环境：5060 失联 + Unity 手动重启；零查询，见 §4.1） | 2（重启 1 次） | 0 / 0 |
| — | （无会话） | 登记外 Play：Unity 重启后进入，帧 0–19，后续帧至 436（`sim_t` 87.4 s） | 约 15:45–15:55:30 | 零会话/零查询/零 ID；是否计入诊断额度交接受角色 | 2 | 0 / 0 |
| 2 | `diag-loopb-2` | 诊断（≤300 s，正式 ID 0；最后一次诊断额度） | 2026-09-22T15:59-0400 登记 | 未确认/未播种（CLI 参数错 + 超窗；Unity 失焦停帧，见 §4.3）；max `sim_t` 291.2 s | 2 | 1 / 1 |
| 3 | `diag-loopb-3` | 新增诊断 1/2（AC-12 修订3；≤300 s、≤4 段、正式 ID 0） | 2026-09-22T21:15-0400 登记 | 持续供帧通过；未确认/未播种（查询时红车不在画面，候选落在非目标小物体上，操作者未确认），首批追平与人眼检查未取得，见 §8.3；max `sim_t` 150.2 s | 3 | 1 / 2 |
| 4 | `diag-loopb-4` | 新增诊断 2/2（余量，§4 第 8 步：诊断 3 因步骤顺序与红车经过时间窗冲突未取得第 4/6 步数据） | 2026-09-22T21:34-0400 登记 | 持续供帧通过；候选正确但确认超窗（`stale_rejected`/`frames_late_exceeded`），未播种，首批追平与人眼检查未取得，见 §8.5；max `sim_t` 293.6 s；新增诊断额度耗尽 | 3 | 1 / 3 |
| 5 | `diag-loopb-5` | 新增诊断 1/3（AC-12 修订4，R6 通过候选；≤300 s、≤4 段、正式 ID 0） | 2026-09-23T15:20-0400 登记 | 持续供帧通过；确认 4.1 s 内成功、播种、首批追平写出（见 §11）；drift 告警→操作者判丢→停止；人眼检查用户原话见 §11.2；max `sim_t` ≈ 287 s | 4 | 6 / 9 |
| 6 | `diag-loopb-6` | 新增诊断 2/3（AC-12 修订4/6，R7 通过候选 K1K2K3；≤300 s、≤4 段、正式 ID 0） | 2026-09-23T18:19-0400 登记 | **硬停止**：段1播种、首批追平写出、机身跟随 20.6 m，后跟踪漂移经核验告警→判丢；段2/3/4 均 `catchup_stale`（§0 硬停止集合），见 §13.3；两张具名样帧人眼确认已完成；max `sim_t` ≈ 210 s | 5 | 11 / 20 |

## 6. 交接受角色：待裁定与代录请求（2026-09-22，实现角色停在此处）

实现角色对 `docs/proposals/` 与账本无写权限，以下请求写在本节，由接受角色裁定/代录后落到提案与账本。

**6.1 用户新回答（请逐字代录入账；`AskUserQuestion` 问题与选项原文）**

1. 问（逐字）："Unity 失焦就停帧（runInBackground: 0），而操作者必须切到终端敲命令、看预览。您倾向哪条路？不论选哪条，
   都还需要您另外授权诊断额度，并由接受角色裁定后才能再 Play。" 用户选（逐字）："勾选 Run In Background（推荐）"。
   该选项说明（逐字）："把 ProjectSettings.asset 里的 runInBackground 从 0 改成 1，只改这一项。这样操作者在 Mac 上照常用
   终端即可，最简单。但它属于改 Unity 工程设置（PLAY_GOVERNING），需要接受角色裁定合同里的「Unity 零改动」是否放行，以及
   要不要开复核轮。" 未选的两项：「不改 Unity，第二台设备当操作台」「先停下，交接受角色」。
2. 问（逐字）："诊断额度 2/2 已用完。改好 Run In Background 后，需要重新用诊断 Play 检查首批追平和预览画面。您要追加几次？
   每次仍不超过 300 秒、不占正式 ID，模型启动和查询仍在原来的 ≤10 / ≤400 总额内计数，这两项不追加。"
   用户选（逐字）："追加 2 次（推荐）"。该选项说明（逐字）："1 次用来验证首批追平和人眼保真检查，再留 1 次余量，应对环境
   意外或操作失误。"
3. 其余本批用户原话（语境，逐字）：「已经恢复」「已经唤醒了，重启服务」「说一下，unity重启了」
   「已经退出play，是我手动重启无报错」「已经删了，重新打开场景了还没有play」「做完了，至于预览我没有看到」。

**6.2 待裁定（请接受角色答复；实现角色不自行解释）**

- **R-B1 Unity 失焦停帧的处置**：`ProjectSettings/ProjectSettings.asset` `runInBackground: 0 → 1`（单字段）。该路径属
  PLAY_GOVERNING（workflow §4.4），合同 §2.2 写「不改 Unity（`Assets/`、`config/` 零字节）」而未点名 `ProjectSettings/`，
  AC-4 的零改动机检只列 `Assets/ config/ tools/eng_sft/`。请裁定：(a) 是否允许、由谁改（实现角色提交该一行）；
  (b) 是否构成 `K1K3` 候选变化并按 §4.4 开 R 轮（`git diff <通过候选>..<新候选>` 于 PLAY_GOVERNING 非空）；
  (c) 采集候选对应性（Python 客户端仍从原通过候选运行、Unity 工程多一行设置）与 Unity 日志的写法。
- **R-B2 登记外 Play**：§4.1 末条（Unity 重启后进入、帧 0–19 并在 15:54–15:55 续跑至 `sim_t` 87.4 s；零会话/零查询/零 ID）
  是否计入「诊断 Play ≤2」或另计。
- **R-B3 诊断 1/2 的归因**：诊断 1 = 环境中断（5060 休眠 + Unity 失焦停帧，零查询）；诊断 2 = 未确认/未播种（操作者把
  request_id 填进 `confirm` + 超窗；Unity 失焦停帧），查询 1 行。实现角色建议均归「环境/流程」，非候选缺陷；由接受角色机械归因。
- **R-B4 首批追平门仍未测**：授权要求「先用诊断确认首批追平再进正式」，该前提未满足；在追加诊断入账且 R-B1 落地前，实现角色
  不开任何 Play。

**6.3 本批的操作工具修正（`docs/evidence/`，非 PLAY_GOVERNING，已自测）**：`lc confirm` 先校验候选编号为整数且在已呈现
范围内，否则提示用法、不发请求；watch 在候选出现时逐个打印可照抄的 `lc confirm <k>`。5060 服务已按命令行核验停止
（残留 0、8760 监听 0；B 账本 启动 2/10、查询 1/400、拒绝 0）；两次启动的前台输出原样存
`docs/evidence/P1-ENG-LOOP-001-service-5060-b.log`。`runtime/hold-diag-loopb-{1,2,2b}/` 保留隔离物，未删除。

## 7. R-B1…4 落实：单字段设置核对（C2@K1K3 候选，2026-09-22，零消耗）

- 用户先退出 Unity（避免编辑器开着时改盘上设置被覆盖/不生效），实现角色只改 `ProjectSettings/ProjectSettings.asset`
  第 85 行 `runInBackground: 0` → `1`；相对 R2 `passed_candidate`：该文件 `--numstat` = `1 1`，`Assets/`、`config/`、
  `Packages/`、`tools/eng_sft/`、`controller/` 零差异。退出 Unity 时工作树保持干净（Unity 未写回任何文件）。
- **效果未验证**：失焦后是否持续供帧、首批追平、人眼保真检查都要等 R3@K1K3 通过后的新增诊断（`diag-loopb-3`，
  操作单 C §4）；本记录不发令，未开 Play、未启动模型、未向 5060 传输。
- 操作单 C 与三个执行载体的修订、逐 AC 证据与全量 diff 分类见 `docs/evidence/P1-ENG-LOOP-001-K1K3-c2-handoff.md`。

## 8. R4 候选对齐与新增诊断 `diag-loopb-3`（2026-09-22 晚，Implementation / Claude Code）

用户在本会话选定（`AskUserQuestion`，所选标签逐字）：「准备完接着做诊断3（推荐）」「已接电、睡眠=从不」
「我在 Claude 终端面板开（推荐）」（后者 = 实现在 Claude 应用终端面板开 T1/T2/T3，T1 `lc_run`、T2 `lc_watch`，用户在 T3 敲 `lc` 命令）。

### 8.1 操作单 C §1 对齐（零 Play、零模型加载、零扣额）

- 采集候选 = 复核文件最后一条 `passed_candidate`（运行时解析）；§1.1：倒数第二条与最后一条之间
  `git diff --quiet … -- controller tools/language_serve.py tools/eng_sft tools/requirements-language.txt` 退出码 0；
  `git diff --quiet <候选> HEAD -- docs/evidence/P1-ENG-LOOP-001-5060-runner-b.py` 退出码 0。
- 采集 worktree `git checkout --detach <候选>`：HEAD = 候选，`status --porcelain --untracked-files=all` 0 行；
  `runtime/models` 仍为指向主工作树模型目录的忽略链接；worktree 内 `runInBackground: 1`。
- §1.2 重建清单：`P1-ENG-LOOP-001-build-stage-b-manifest.py` 输出 `files_verified` 118、清单 sha256 `b3893f72…`、
  staging 181,360 B；清单相对上一版只变 `passed_candidate` 与 `operations_5060_b.py` 两行。传输前 5060 `repo-b`
  四个文件哈希与上一版清单一致（`38de0d51…`/`37528823…`/`f11b741b…`/`4ed2faa7…`），服务进程 0、8760 监听 0。
  `stage-b-transfer-r4.tar`（189,440 B，sha256 `25f21056…`）经 `scp` 到 F 盘、`tar.exe -xf` 解到 `repo-b`，两端逐文件
  sha256 相同：`language_bridge.py` `38de0d51…`、`language_loop.py` `37528823…`（两源文件与上次传输相同）、
  `operations_5060_b.py` `3120e516…`、`transfer-manifest-stage-b.json` `b3893f72…`。未传权重/数据。
- §1.3：`amend` 退出码 0，B 账本记 `diag_amendment` = `AC-12-rev3`、`diag_sessions_added` 2、`diag_sessions_before`
  = [`diag-loopb-2`]（`diag-loopb-1` 零查询，服务端账本从未有该会话）；`preflight` 退出码 0（候选 = 最新
  `passed_candidate`、runner `3120e516…`、K 收据 `b511ad6c…`、base `7de1838c…`、adapter `4044dd4f…`、c2-adapter、
  端点 `http://100.100.100.100:8760`、RTX 5060 Laptop GPU）。账本前后：启动 2/10、查询 1/400、拒绝 0。

### 8.2 `diag-loopb-3` 发令检查（2026-09-22T21:14–21:15-0400，Unity 已在主工作树打开场景、未 Play）

- §2.1：用户确认 5060 接电、睡眠=从不（见 §8 首段）；Tailscale 显示 5060 在线；Unity 6000.4.1f1 已以主工作树为
  `-projectpath` 运行（用户原话「已打开，未play」）。
- §2.2：`check_docs.py` 通过；Active handoffs 仅本项一条未暂停 `Consuming=yes`；复核文件无机读 `blocks_consuming_gate:` 行。
- §2.3 槽位隔离（只移动）：诊断 2 残留移入 `runtime/hold-diag-loopb-3/`：`frames/` 257 项（帧 1328–1455 + `latest.json`，
  树摘要移动前后 `0066f522f4bc4c20`）、`metrics.json` `5cb9ec43…`、`language_request.json` `cb454163…`、
  `language_result.json` `301d2a86…`、`tracker_state.json` `13cc3520…`、`m3_body_truth.jsonl` `ffb909ea…`（移动前后相同）；
  `runtime/frames/` 为空目录；`scenario_config.json` 不存在。
- §2.4 第一次 `lc_check`（21:14:29）：除「5060 /status」（服务未启动）外全部 `ok`。
- §2.5 服务启动 **3/10**：SSH 前台常驻（`-EncodedCommand`），`LISTENING` pid 22356，`model_loads` 3、`query_rows_before` 1，
  候选/清单 `b3893f72…`/runner `3120e516…`/K 收据 `b511ad6c…`；`/status` idle，权重 `4044dd4f…`、prompt `b28d2eb5…`、
  词表 `65c59418…`、revision `89644892…` 与 K 收据一致。第二次 `lc_check`（21:15:11）原样：

```
passed_candidate=737527964a62f7098cbf483ce808458fe0ba1e57 capture_worktree_HEAD=737527964a62f7098cbf483ce808458fe0ba1e57 main_HEAD=b66b55700fe01fe11562852a991a7a12d99519ca
ok   capture worktree HEAD = passed_candidate
ok   capture worktree status empty
ok   main tree = passed_candidate on Assets/config/ProjectSettings/Packages + operation files
ok   main tree status empty on the same paths (incl. untracked, e.g. _Recovery)
ok   ProjectSettings runInBackground: 1
ok   Unity is open on ~/TetheredDroneTracking (checks run after Unity opened)
ok   runtime/frames empty; slot files absent unless listed above
ok   no track_loop/language_loop process
ok   5060 /status idle
lc_check passed
```

### 8.3 `diag-loopb-3` 结局：持续供帧通过；未确认、未播种（首批追平与人眼检查未取得）

- 21:15:35 `lc_run`（启动前 `lc_check` 全 `ok`，pid 3081，K 绑定与 5060 实时身份握手通过；`--diagnostic`）；T2 watch 21:15:52 起；
  用户 21:17:35 进入 Play（`sim_t=0.2s`）。
- **第 2 步 持续供帧（R-B4）通过**：21:17:35–21:17:59 用户在 Claude 终端面板（`FOCUS Unity -> Claude`），之后多次在 Unity、Claude、
  预览之间切换；`sim_t` 持续增长，至 21:20:04 `unfocused_frames`=624，`max_stall_s`=0.0，无「帧停滞」。
- 21:18:25 `lc ask "the red car"`（回执 `APPLIED`）→ 21:18:29 结果 `diag-loopb-3-q1`：`unique`、查询帧 246（`sim_t`≈49 s）、
  `frames_late`=21（≤ `K_ret` 30）、`latency_ms`=3405、`wall_elapsed_s`=3.74；候选 0 = xywh `[0.375,0.064,0.02,0.048]`，
  预览 `…/diag-loopb-3/previews/246-diag-loopb-3-q1.png`（watch 打开，用户 21:18:30–38 在预览前台）。预览中红车不在画面内，
  框落在画面顶边一个红色小物体上；用户未确认（未发 `confirm`/`reject`）。
- 候选停在 `AWAITING_CONFIRMATION` 直至停止（约 112 s）：按合同状态表与 `_check_confirmation`，时效只在合法 `confirm` 时检查，
  没有自动过期；操作单 C §3「来不及就让它过期（会记 `candidate_expired`）」与此不符（仅记录，冻结文件未改；供接受角色注记）。
- 21:20:05 最后一帧 750（`sim_t` 150.2 s）写出时 Unity 在最前台（21:20:04–07），watch 21:20:07 的「帧停滞」对应用户退出 Play，
  不是后台停帧；21:20:21 `lc stop`（回执 `APPLIED`，TERMINAL/`operator_stop`），会话进程退出、锁释放；watch 经 SIGINT 停止。
  用户原话：「你现在unity一直在跑，按你的做法红车已经走了。只能结束」「已停止退出play。另外先确认一下本次测试的目的是什么」。
- 计数：B 账本 启动 3/10、查询 2/400（`diag-loopb-3`=1）、拒绝 0，与客户端 `results.jsonl` 1 行一致；零正式 ID；新增诊断 1/2。
- **原因（实现角色的事实整理，归因由接受角色机械派生）**：播种前相机固定朝下，按 `config/scenario.default.json` 的目标路线
  （环长 213 m、2.0 m/s、一圈 106.5 s）与帧元数据（相机 (132, 25.2, 117) 正下视、HFOV 75.2°/VFOV 60°）推算，红车完整在画面内的
  时间窗约为 `sim_t` 0–12 s、99–118 s、206–225 s（已有帧 t=0.2/2/4 s 有红车，t=49、62–87、125–150、266–291 s 无红车，一致；
  第 2、3 窗未经帧直接验证）。操作单 C §4 要求第 2 步（约 10 s 切窗）先于 ask，第 1 窗因此不可用；本次在两窗之间提问。
  该推算只用于操作者择时，不进入控制器、感知输入或传感器元数据。
- 用户随后原话：「先不着急做诊断4，先想一下整个流程能怎么优化一下」；实现角色列出档 0（不改文件：第 2 步照做后等第 2 窗、
  提前敲好 ask、并排布局、框不对立即 reject）、档 1（接受角色注记：上述「过期」表述与时间窗表）、档 2（操作工具改动，PLAY_GOVERNING，
  须 K1K3 核对轮+复核轮，暂不建议）。用户原话：「按档0来一次」。

### 8.4 `diag-loopb-4` 发令检查（Unity 仍在主工作树打开、未 Play；服务沿用启动 3，不新增启动）

- 槽位隔离（只移动）：诊断 3 残留移入 `runtime/hold-diag-loopb-4/`：`frames/` 257 项（帧 623–750 + `latest.json`，树摘要移动前后
  `45a6a5c0fb57eb76`）、`metrics.json` `f55ad4d0…`、`language_request.json` `1cea6eb8…`、`language_result.json` `15b0a2fc…`、
  `tracker_state.json` `ab56d6e5…`、`m3_body_truth.jsonl` `e4796c2c…`（前后相同）；`runtime/frames/` 空；`scenario_config.json` 不存在。
- `check_docs.py` 通过；`lc_check`（会话号 `diag-loopb-4`）全部 `ok`：候选 = 最新 `passed_candidate` = 采集 worktree HEAD、worktree 干净、
  主工作树冻结路径零差异且无未跟踪项、`runInBackground: 1`、Unity 已打开、槽位与锁不存在、无 track/language 进程、5060 `/status` idle。
- 执行按档 0：第 2 步照做（Play 开始即切到 T3 约 10 s）；随后等待第 2 窗，`sim_t`≈95 s 预先敲好 `lc ask "the red car"`，
  见红车从画面左下沿左侧竖路驶入再回车；错过则等第 3 窗；框不对立即 `lc reject` 后重问。操作单 C 冻结文本未改。

### 8.5 `diag-loopb-4` 结局：持续供帧通过；候选正确，但确认超出 16 s 窗被拒（未播种）

- 21:34:49 `lc_run`（启动前 `lc_check` 全 `ok`，pid 6321，握手通过；`--diagnostic`）；watch 21:35:15 起；用户约 21:36:22 进入 Play。
  第 2 步照做（21:36:28 起在 Claude 终端面板），此后 `unfocused_frames` 持续增长至 1398，`max_stall_s`=0.0，无「帧停滞」。
- 21:38:06 `lc ask "the red car"`（`APPLIED`，与第 2 窗预测一致地在红车驶入时提问）→ 21:38:10 结果 `diag-loopb-4-q1`：`unique`、
  查询帧 500（`sim_t`≈100 s）、`frames_late`=19、`latency_ms`=2963、`wall_elapsed_s`=3.30；候选 0 = xywh `[0.206,0.776,0.08,0.159]`，
  预览 `…/diag-loopb-4/previews/500-diag-loopb-4-q1.png`：框落在从画面左下驶入的红车上（实现角色看图；用户未另作人眼结论）。
  用户 21:38:11–17 在预览前台。
- 21:38:30 `lc confirm 0`（回执 `APPLIED`，距 ask 24.0 s、距候选呈现 20.2 s）→ 确认检查点 `frames_late_exceeded`
  （最新帧 − 500 > `K_ret`+`K_conf` = 80）：结果 `stale_rejected`，候选作废，无既往段 → `IDLE`（合同状态表第 248 行）；未 `initialize`、
  未建段、发布收据为空，首批追平**未测到**。21:40:36 `lc verify` → `REQUEST_INVALID`（`verify_in_IDLE`，无跟踪段时按设计拒绝）。
  第 3 窗（约 206–225 s）未再提问。21:41:18 `lc stop`（`APPLIED`，TERMINAL/`operator_stop`）；21:41:20 最后一帧 1467（`sim_t` 293.6 s）
  后用户退出 Play（≤300 s）。watch 经 SIGINT 停止。
- 用户原话（逐字）：「昨晚，但是手动输入verify无响应」（附两张终端截图：T3 的 ask/confirm/verify 回执与 T2 的 `sim_t` 行）。
  实现角色问确认耗时卡在哪（`AskUserQuestion`，多选），用户选（逐字）：「打字/核对命令慢」「看预览、对照 Unity 花了时间」；
  未选「切回终端麻烦」「不知道有 16 秒限制」。
- 计数：B 账本 启动 3/10、查询 3/400（`diag-loopb-4`=1）、拒绝 0，与客户端 `results.jsonl`（1 查询行 + 1 `stale_rejected` 行）一致；零正式 ID；
  **新增诊断 2/2 耗尽 → 操作单 C §0 硬停止**。5060 服务经命令行核验停止（remaining=0、listen8760=0）；启动 3 的前台输出原样并入
  `docs/evidence/P1-ENG-LOOP-001-service-5060-b.log`。`runtime/hold-diag-loopb-{3,4}/` 保留隔离物，未删除；`runtime/frames/` 现有本次
  末段 128 帧（下次发令前隔离）。
- 原因（事实整理，归因由接受角色派生）：两次新增诊断都没有到达播种。诊断 3：第 2 步先于 ask，与红车第 1 窗冲突，
  提问时目标不在画面；诊断 4：提问时机与候选均正确，确认链「看预览 → 核对 → 切回终端打字」约 20 s，超出设计给人的
  `T_ret+T_conf`=16 s（诊断 2 同一环节 43 s）。门按设计 fail-closed，无协议违规、无 `REINIT_REQUIRED`、F3 未触发。

### 8.6 交接受角色：用户新要求与待裁定（实现角色对账本/提案只读，请代录与裁定）

**用户原话（逐字；`AskUserQuestion` 问题与所选标签原文）**

1. 实现角色问（逐字）："诊断额度已用完，正式 Play 不能开。下一步怎么走？（这是需要你授权的决定，我会逐字记录，交接受角色入账和
   裁定；模型启动 3/10、查询 3/400 还充裕。）" 用户未选四个选项（「追加诊断+最小改动（推荐）」「追加诊断+加一键确认」「跳过诊断直接正式」
   「先停，交接受归因」），以「其他」回答（逐字）："测试想要什么？模型的跟踪能力吗"。实现角色答：阶段 B 不测跟踪能力（AC-15
   「报告不含跟踪性能/恢复率主张」），测人机闭环链路在真实 Unity 里能否走通及出错时安全停下；诊断查三项前提。
2. 用户（逐字）：「我在想，后面人确认其实不用很长时间，如果要是有一个交互按钮点一下就解决了」
3. 问（逐字）："按钮要管哪些操作？（问这个是因为：正式 P1 里不只是首次确认要抢时间，车丢了以后还要「判丢 → 重新指定 → 再确认」，
   同样有 16 秒窗；但按钮覆盖的动作越多，复核范围越大、成本越高。）" 用户选（逐字）："全部操作者动作（推荐）"。该选项说明（逐字）：
   "按当前状态只显示合法的按钮：指定红车、确认候选 k（每个候选一个按钮）、驳回、核验、判丢、解除疑似、重新指定、停止。P1/P2 全程基本不用打字。"
   未选：「只管确认和驳回」「确认/驳回 + 判丢/重新指定」。
4. 问（逐字）："按钮放在哪种界面里？（问这个是因为它决定你 Play 时的屏幕布局，也影响实现难度和安全性；三种都不下载新东西，按钮背后都
   调用同一个已复核的命令行，不手写桥文件。）" 用户选（逐字）："本地网页（推荐）"。该选项说明（逐字）："浏览器开一个本机页面：上方是当前
   预览大图（候选/核验自动刷新）、状态和确认倒计时，下方是按当前状态出现的按钮。和 Unity 并排放，预览不再弹独立窗口抢焦点。"
   未选：「终端快捷键」「原生小窗口」。
5. 问（逐字）："按钮版做好并复核通过后，要追加几次诊断 Play？（问这个是因为诊断额度只能由你授权、逐字入账，服务脚本也要按这个数改；
   每次仍 ≤300 秒、不占正式 ID，模型启动和查询仍在原来 ≤10 / ≤400 总额内计数，这两项不追加。）" 用户选（逐字）："追加 3 次"。
   未选：「追加 2 次（推荐）」「追加 1 次」。
6. 同批其余用户原话（语境，逐字）：「已打开，未play」「你现在unity一直在跑，按你的做法红车已经走了。只能结束」
   「已停止退出play。另外先确认一下本次测试的目的是什么」「先不着急做诊断4，先想一下整个流程能怎么优化一下」「按档0来一次」
   「昨晚，但是手动输入verify无响应」。

**待裁定（实现角色不自行解释，不开工）**

- **R-B5 操作者按钮页**：用户要求的本地网页操作台（无新依赖，Python 标准库本机服务，仅监听 127.0.0.1）：显示当前候选/核验预览、状态与
  确认剩余时间；按状态只呈现合法动作按钮（ask 预设 `the red car` 并可输入闭集文法指令、每个候选一个 `confirm k`、`reject`、`verify`、
  `confirm-lost`、`dismiss`、`respecify`、`release`、`stop`）；每个按钮只调用采集候选中已复核的 `controller.language_loop` CLI（同 `lc`，令牌取
  watch 已呈现者，不手写桥文件），每次点击与两路输出记入 `<opdir>`；终端 `lc` 保留作后备；页面使用时 watch 不再以 `open` 弹预览。
  请裁定：是否在已接受范围内（操作者工具，不改协议/K/门/控制）、载体文件路径、AC 归属与证明方式（载体自测 + 复核），以及它作为
  PLAY_GOVERNING 变化按 §4.4 开 K1K3 候选（核对轮 + 复核轮）。
- **R-B6 追加 3 次诊断**：用户选「追加 3 次」（入账后生效）；5060 runner 的 `DIAG_AMENDMENT`（`AC-12-rev3`，+2）是写死的服务端上限，
  须改为新修订（冻结已计费的 `diag-loopb-2/3/4`，新增 3 个会话，建议会话号 `diag-loopb-5…7`）并重建传输清单；操作单 C §0/§3/§4 同步。
- **R-B7 操作单文字修正（同一候选内）**：写入播种前红车在画面内的时间窗（由 `config/scenario.default.json` 路线/车速与帧相机元数据推算，
  约 `sim_t` 0–12、99–118、206–225 s；第 2 窗已由 `diag-loopb-4` 查询帧 500 目视印证；只用于操作者择时，不进控制器/感知/传感器元数据）
  及第 2 步切窗与第 1 窗的顺序安排；改正 §3「让它过期（会记 `candidate_expired`）」（时效只在合法 `confirm` 时检查）。
- **归因请求**：`diag-loopb-3/4` 按 R-B3 口径机械归因（实现建议：流程/操作时序，非候选缺陷）；16 s 确认窗未要求修改，作为可用性事实
  供 AC-15 描述（不改 `T_conf`/K 收据）。在 R-B5…7 裁定、授权入账、新候选复核通过之前，实现角色不开任何 Play、不启动 5060 服务。

## 9. R-B5…7 落实（C3@K1K3 候选，2026-09-22 晚，零消耗）

- 按提案 Pending rulings R-B5…7 交付本地操作页 `P1-ENG-LOOP-001-operator-web.py`（`lc_web`）、页面模式 watch、runner 修订4 迁移与
  清单脚本改动、操作单 C 修订；四项自证、逐 AC 指针、限制与 R5 范围见 `docs/evidence/P1-ENG-LOOP-001-K1K3-c3-handoff.md`。
- 本批零 Play、零 5060 连接/传输/服务启动、零模型查询；B 账本仍是 §8.5 末的 启动 3/10、查询 3/400，**修订4 迁移尚未在 F 盘执行**
  （R5 通过后按操作单 C §1 执行 `amend`）。新增诊断标签分配为 `diag-loopb-5`（`-6`、`-7` 余量），本批未创建任何目录或身份。
- 页面布局由用户在应用内浏览器用 scratchpad 假会话（真实会话代码 + 回放桩 + 评估集静态帧）试看后确认冻结；试看不是诊断 Play，
  不计诊断额度，也不作任何证据。`runtime/frames/` 里诊断 4 的末段 128 帧仍在（下次发令前按 §2.3 隔离），`runtime/hold-diag-loopb-{3,4}/` 保留。
- **C3 候选替换（同晚）**：第一个 C3 候选提交后、C3 开始前，用户选择先按提案「用户指定网页功能审查」修 UI-1…4（选项原文见
  `-K1K3-c3-handoff.md` §6 第 5 条）；替换候选只改操作页、自测、操作单 C 与证据，仍零 Play、零 5060、零模型查询。页面目检用的
  scratchpad 假会话同样不计诊断额度、不作证据。
- **C3 后再替换（2026-09-23）**：C3@K1K3 附三项待核实主张（C3-1 账本缺失先写零账本、C3-2 未知回执单槽覆盖、C3-3 超时字节输出致日志失败），
  实现角色核实均属实，用户选择先修再走 C4→R5（原文见 `-K1K3-c3-handoff.md` §6 第 6 条）。只改 runner、操作页、自测、操作单 C 与证据，
  仍零 Play、零 5060、零模型查询。

## 10. R6 通过候选对齐（2026-09-23，Implementation / Claude Code；零 Play、零模型加载、零扣额）

用户在本会话选定（`AskUserQuestion`，所选标签逐字）：「准备完接着做诊断 5（推荐）」；随后 5060 离线，再选「现在弄不了，改天」。

- 操作单 C §1.1：采集候选 = 复核文件最后一条 `passed_candidate`（运行时解析，R6）；倒数第二条（R4）与最后一条之间
  `git diff --quiet … -- controller tools/language_serve.py tools/eng_sft tools/requirements-language.txt` 退出码 0；
  `git diff --quiet <候选> HEAD -- docs/evidence/P1-ENG-LOOP-001-5060-runner-b.py` 退出码 0；候选→HEAD 在
  `Assets config ProjectSettings Packages` 与六个冻结操作文件上 `git diff --quiet` 退出码 0。
- 采集 worktree `git checkout --detach <候选>`（此前在 R4 通过候选）：HEAD = 候选，`status --porcelain --untracked-files=all` 0 行；
  `runtime/models` 仍为指向主工作树模型目录的忽略链接；worktree 与主工作树 `runInBackground: 1`。
- §1.2 重建清单：`P1-ENG-LOOP-001-build-stage-b-manifest.py` 输出 `files_verified` 118、清单 sha256 `1efc65b9…`、staging 183,145 B；
  已提交的 `-transfer-manifest-5060-stage-b.json` 相对上一版只变 `passed_candidate` 与 `operations_5060_b.py`（`3120e516…` → `d691f84d…`）两行。
  staging 在会话 scratchpad，未传输；清单脚本确定性重建，下次可原样重做。
- **停在传输之前**：5060（Tailscale 名 `laptop`，`100.100.100.100`）离线（`tailscale status`：last seen 5h ago），SSH 22 端口连接超时，
  零命令执行。F 盘 `repo-b` 仍是 R4 候选的四个文件，B 账本仍为 §8.5 末的 启动 3/10、查询 3/400，**修订4 `amend` 与 `preflight` 未执行**。
  `diag-loopb-5` 未登记、未开 Play。`runtime/frames/`（257 项）与既有 `runtime/hold-diag-loopb-*` 未动（下次发令前按 §2.3 隔离）。
- 下次续做（顺序不变）：用户确认 5060 接电、睡眠=从不、Tailscale 在线 → 重跑 §1.1/§1.2（候选未变则结果应相同）→ 传输四个文件并逐文件比
  sha256 → `amend` → `preflight` → 用户打开 Unity（不 Play）→ §2 发令检查 → 起服务（计 1 次启动）→ `diag-loopb-5`。

## 11. `diag-loopb-5`（2026-09-23 下午，Implementation / Claude Code；新增诊断 1/3）

承 §10：用户先选「现在弄不了，改天」，同一会话随后原话「5060已经开了，继续」「一连上，继续」；Unity 就绪时选（`AskUserQuestion`，
标签逐字）「已打开并载入场景，未 Play」。

### 11.1 §1 续做与 §2 发令检查（零模型加载至启动前）

- 传输：`stage-b-transfer-r6.tar`（191,488 B，sha256 `eaf92a80…`，四文件）经 `scp` 到 F 盘 `tmp`，`tar.exe -xf` 解到 `repo-b`；两端逐文件
  sha256 相同：`language_bridge.py` `38de0d51…`、`language_loop.py` `37528823…`（两源文件与上次相同）、`operations_5060_b.py` `d691f84d…`、
  `transfer-manifest-stage-b.json` `1efc65b9…`。传输前 `repo-b` 为 R4 候选四文件（哈希与 §8.1 一致），服务进程 0、8760 监听 0。未传权重/数据。
- `amend` 退出码 0：`AC-12-rev3` 原记录保留，`later_diag_amendments` 追加 `AC-12-rev4`（`diag_sessions_added` 3，`diag_sessions_before`
  = [`diag-loopb-2`,`-3`,`-4`]，`new_session_labels` = [`diag-loopb-5`,`-6`,`-7`]）；前后计数不变（启动 3/10、查询 3/400、拒绝 0）。
- `preflight` 退出码 0：候选 = R6 `passed_candidate`、清单 `1efc65b9…`、runner `d691f84d…`、K 收据 `b511ad6c…`、base `7de1838c…`（revision
  `89644892…`）、adapter `4044dd4f…`、c2-adapter、端点 `http://100.100.100.100:8760`、RTX 5060 Laptop GPU。
- 5060 电源：交流供电（`BatteryStatus` 2），`STANDBYIDLE` 交流 `0x7ffffda7`、直流 `0`（均为不睡眠）。
- §2.2 `check_docs.py` 通过；Active handoffs 仅本项一条未暂停 `Consuming=yes`。§2.3 槽位隔离（只移动）：`metrics.json`、`language_request.json`、
  `language_result.json`、`tracker_state.json`、`m3_body_truth.jsonl` 与 `runtime/frames/` 257 帧移入 `runtime/hold-diag-loopb-5/`，移动前后
  262 个 sha256 逐一相同；`scenario_config.json` 与两把锁不存在。
- §2.4 第一次 `lc_check`：除「5060 /status idle」外全 `ok`。§2.5 服务启动 **4/10**（后台 SSH 前台常驻，约 20 s 后 `/status` idle），
  身份六项（backend/model_form/base revision/weights/prompt/vocab sha）与 K 收据逐项一致；第二次 `lc_check` 全部 `ok`（两次输出在
  `outputs/eng-loop/P1-ENG-LOOP-001/diagnostics/operator/diag-loopb-5/precheck.log`）。§2.7 Play 登记见 §5 第 5 行。
- 终端：Claude 应用终端面板 T1 `lc_run`、T2 `lc_watch`、T3 `lc_web`（操作页由默认浏览器 Chrome 打开）；用户在页面操作。

### 11.2 结局（原始路径 `outputs/eng-loop/P1-ENG-LOOP-001/diagnostics/diag-loopb-5/` 与同名 `operator/` 目录；诊断不复制进证据目录）

- **持续供帧（第 2 步）**：整次 Play Unity 基本在后台（最前台为 Claude/Chrome），`unfocused_frames` 1285、`max_stall_s` 0.0，无「帧停滞」。
- **指定与确认（第 3 步）**：`sim_t` ≈ 101 s 点「指定」；`q1` 查询帧 507、时延 3.98 s、唯一候选；结果呈现（`AWAITING_CONFIRMATION`
  于 unix `…460.02`）后 4.1 s 点「确认候选 0」（查询起 8.5 s），回执 `APPLIED`，`segment_seeded` 帧 507。
- **首批追平（第 4 步）**：播种后 0.5 s 首批 `WRITTEN`：观测与 `look_at` 均为帧 555，`load_elapsed_s` 0.240、`frame_delta` 2、
  `capture_age_s` 0.52；下一批帧 557 `frame_delta` 0、`load_elapsed_s` 0.011；T2 打印 `PUBLISHED first track=diag-loopb-5-t1
  last_published=555`。全段发布收据 702 条：`WRITTEN` 700、`MUTED_DROPPED` 2（播种瞬间初始化发布被静音，符合设计）；无硬停止原因。
- **核验（第 5 步）**：`q2`/`q3`/`q4`（帧 605/650/717）`consistent`，IoU 0.86/0.89/0.66；`q5`/`q6`（帧 782/849）`drift`，IoU 0.0，
  第 2 次后 `SUSPECTED(drift)`（`suspect_id` `diag-loopb-5-s1`，触发核验 `q6`）；操作者点「判丢」→ `LOST(verify_drift)`，段退役；
  随后「停止会话」→ `TERMINAL(operator_stop)`。页面五次点击（ask/confirm/verify/confirm-lost/stop）全部退出码 0、回执 `APPLIED`。
- **计数**：本次查询 6，B 账本 `model_loads` 4、`query_rows` 9、`diag-loopb-5` 6、`refused` 0，与客户端 `results.jsonl` 六行一一对应。
  服务在用户决定不进入正式 Play 后经命令行核验停止（两个 `operations_5060_b.py serve` 进程：venv 启动器与其子进程），剩余 0、8760 监听 0。
- **机身未动（用户观察）**：按合同 AC-13「机身沿用一次性 hold；`--condition follow`」，会话播种时只写一次 `body_command` `mode: hold`，
  机身全程在锚点上方 `(132.0, 25.2, 117.0)`；云台由正下方转向目标，约 `sim_t` 150 s 起达到 `config/scenario.default.json`
  `gimbal.maximum_off_nadir_deg` 45°（帧元数据 `gimbal_saturated: true`，相机前向离底角 45.0°）；此后跟踪框冻结在画面上方
  （中心 0.5, 0.16，置信度约 0.94），核验 `q5`/`q6` 报 drift。实现角色看过 `650-q3`（两框同在红车上）与 `849-q6`（两框都不在红车上），
  这不代替用户人眼检查。
- **人眼保真（第 6 步）**：实现角色请用户对照 Unity 画面看候选图 `507-q1` 与核验图（如 `650-q3`）并说明判丢时所见，用户原话（逐字）：
  「最开始是能看见的，前几章图片都是画框正确，但是后续飞到死角被运动场挡住然后由于无人机不移动红车彻底离开视线发现可能性归0然后就暂停了」。
  是否满足 workflow §4.3.2 与操作单 §4 第 6 步（至少 1 张候选 + 1 张核验）由接受角色判断；实现角色不代为认定。
- 用户在人眼检查前另提出机身必须移动（原话见 §12）。

## 12. 交接受角色：用户要求机身跟随、改在本工作项内（2026-09-23，实现角色停在此处；零代码、零 Play）

**用户原话（逐字，本实现会话；实现角色对账本只读，请接受/辅助角色入账）：**

1. 诊断 5 结束后用户问：「已退出，我感觉这个无人机是不是没有运动？你能读到结果吗」。实现角色答：按 AC-13 机身一次性 hold、只有云台跟随，
   云台到 45° 限位后目标离画（§11.2）。用户（逐字）：「无人机如果不移动的话是不能跟踪完成一圈的追踪任务的。必须要修改」。
2. 实现角色问（`AskUserQuestion`）：「你说的「完成一圈的追踪任务」，指的是哪种？」（选项：「整圈把红车保持在画面里」「允许丢，但能接回来跟完一圈」
   「两者都要，先评估可行性」）。用户未选选项，以「其他」回答（逐字）：「这不是开始的提案已经完成了吗？查一下history，里面应该有详细的记录」。
3. 实现角色检索历史后汇报（下节事实），问：「机身跟随改在哪里做？（我按你选的写成交接给接受角色裁定，原话逐字转交入账；在裁定前不写代码、
   不开 Play。）」用户选（逐字）：「改在 LOOP-001 里（推荐）」。该选项说明（逐字）：「请接受角色裁定：语言闭环的段复用 BODY-001 的阈值规划器
   让机身跟随，AC-13 与正式 P1 随之修订；正式 Play 在新候选通过前暂停。」未选：「另立新工作项」「先让接受角色建议归属」。

**历史事实（只读检索，指针供核对）：**

- `P1-M3-BODY-001`（M3′ batch 1，2026-08-21 关闭，`THRESHOLD_ALLOCATION_PARTIAL`，复核 Round 18 `PASS_WITH_NOTES`）已在真实 Unity 中让机身运动：
  `controller/body_planner.py` `ThresholdBodyPlanner`（`threshold-corridor-v1`，云台余量 <10° 起动、>20° 停、4 m/s、系绳走廊校验，
  `config/p1-m3-body-001.json`）。臂 B（阈值规划 + follow 云台）5/5 次整圈几何可见 `C_geom` = 1.0，臂 A（hold）0.578–0.597；云台饱和
  0.84 → 0.50–0.53，系绳饱和 0 → 0.10–0.47；`C_track|geom` 只在前 62.5 m 窗口计、十次均 1.0。冻结主张上限：「threshold body allocation improves
  imaging quality」，不得写成改进跟踪（`docs/parked-status.md` 冻结措辞节；提案 `docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md`
  第 7050–7084 行附近；`docs/evidence/P1-M3-BODY-001-compare.md`）。
- 规划器唯一入口是 `python -m controller.track_loop … --body-policy threshold --body-planner-config config/p1-m3-body-001.json
  --body-scenario-config config/scenario.default.json`（`controller/track_loop.py` 参数与互斥检查；实例命令见
  `docs/evidence/P1-M3-BODY-001-arm-b-trial-4.md`）。`controller/language_loop.py` 建 `TrackLoop` 不装规划器、无机身参数；本提案 AC-13 写
  「机身沿用一次性 hold」，待裁定 8 写「本项的段从不装 … body planner」。
- 几何限制：锚点 `(132, 0.2, 117)`、悬停 25 m、系绳 35 m（水平可达约 24.5 m）、云台 45°；BODY-001 记臂 A 的缺失主要来自建筑遮挡
  （`Building_Stadium`），与本次用户所见「被运动场挡住」一致。锚点迁移项 `P1-SCENE-003`/`-007` 暂停，不在本请求内。

**请接受角色裁定（实现角色不自行解释，裁定前不写代码、不开 Play）：**

- **R-B8 合同修订**：是否及如何修订 AC-13（及待裁定 8 / AC-4 修订 2 的「段从不装 body planner」）为：语言会话的每段 `TrackLoop` 复用冻结的
  BODY-001 阈值规划器与其配置；`hold_body`/`set_nadir` 静音透传与发布门对 `body_command` 的同帧关联（§3.3）如何适用；是否构成 K2 停点
  （机身控制命令由语言会话的段发出），停点与复核范围如何划分。
- **R-B9 正式 P1 的目标**：机身跟随后目标可能整圈可见，AC-13 的「离画事件 / E1」可能不再发生；P1 改测什么（例如整圈跟随下的核验提醒与
  误报、或仍需离画链路时如何诱发），与 AC-15「不评估跟踪性能」及 BODY-001 冻结措辞的关系。
- **R-B10 额度**：阶段 B 余量 = 诊断 2 次（`diag-loopb-6`/`-7`）、正式 8 次、模型启动 6 次、查询 391 次（B 账本：启动 4/10、查询 9/400）；
  新候选下诊断是否沿用余量；runner 的诊断标签写死，若需新标签即 PLAY_GOVERNING 改动。新候选通过后须按操作单 §1 重建清单、重新传输与 `preflight`。
- **R-B11 诊断 5 归因**：持续供帧与首批追平已测到（§11.2）；人眼检查用户原话见 §11.2；这些结果在修订后的合同下是否仍作为前提记录。

**现状：** 5060 服务已停（剩余进程 0、8760 监听 0）；`runtime/` 留有诊断 5 会话写出的桥文件与帧（下次发令前按 §2.3 隔离），
`runtime/hold-diag-loopb-5/` 保留移入的旧槽位文件；采集 worktree 仍在 R6 通过候选。F3 债与 AC-13…15 `NOT_RUN` 不变。

## 13. R7 通过候选对齐与第三源码传输授权（2026-09-23 晚，Implementation / Claude Code；零 Play、零模型加载、零扣额、零传输）

**用户原话（本实现会话 `AskUserQuestion`，逐字，依提问顺序；实现角色对账本只读，请辅助/接受角色逐字入账）：**

1. 问（逐字）："是否允许把第三个源文件 controller/gated_publisher.py（25,367 字节，只有代码，不含权重和数据）加入传给 5060 的代码包？
   问这个的原因：它是本次机身跟随改动的文件，不在你 9-22 授权的两个源文件里，接受角色裁定必须你另行点头才能传。5060 的服务本身不运行机身通道，
   传它只是为了让 language_loop 能正常导入、哈希和候选一致。整包 5 个文件约 213 KB（三个源文件、B 记账脚本、哈希清单），仍由我经 SSH 传输并
   逐文件比对 sha256；不增加任何 Play、启动或查询额度。"
   用户选（逐字）："允许传第三个文件（推荐）"。该选项说明（逐字）："同意 gated_publisher.py 加入传输包。你的原话我逐字记入 prep 文件，还需要另开
   /chore 或接受会话记进授权账本；账本记好之前我只做本地对齐和清单重建，不传输。" 未选：「不允许」「先只做本地准备」。
2. 问（逐字）："本地准备做完之后，这个会话怎么安排？问这个的原因：如果接着做诊断 6，我要把交接改成消耗性，并扣 1 次模型启动（当前 4/10）和 1 次
   诊断额度（这批剩余 2 次：diag-loopb-6、-7），你需要在 Unity 前当操作者并做两张样帧的人眼检查；如果今天不做，我就停在零消耗的位置。诊断 6 要查的是：
   新候选下机身有没有收到命令并移动、首批追平、操作页、两张具名样帧。"
   用户选（逐字）："准备完接着做诊断 6（推荐）"。该选项说明（逐字）："我先做本地对齐和清单重建；你另开 /chore 把传输授权记入账本。账本记好后我传
   5 个文件、amend、preflight；你打开 Unity（不按 Play）后我做发令检查、启动服务，再由你按操作单 C 跑诊断 6。" 未选：「传输和 preflight 后停」
   「本地准备完就停」。

第 1 项是新的执行授权请求（在 2026-09-22「阶段 B 准备三项问答代录」第 2 项的两个源文件之外增加 `controller/gated_publisher.py`；类别仍只有代码与
清单，无权重/数据/下载）；第 2 项是会话执行顺序确认，不新增额度。**入账前不向 5060 传输任何文件。**

**操作单 C §1.1（零消耗，已完成）：**

- 采集候选 = 复核文件最后一条 `passed_candidate`（运行时解析，R7）；候选是 HEAD 的祖先；倒数第二条（R6）→最后一条之间
  `git diff --name-only … -- controller tools/language_serve.py tools/eng_sft tools/requirements-language.txt` 只列
  `controller/gated_publisher.py`、`controller/language_loop.py`（属传输集合）；`git diff --quiet <候选> HEAD -- docs/evidence/P1-ENG-LOOP-001-5060-runner-b.py`
  退出码 0。
- 候选→HEAD 在 `Assets config ProjectSettings Packages` 与六个冻结操作文件上 `git diff --quiet` 退出码 0；主工作树同路径相对 HEAD 零改动、
  `status --porcelain --untracked-files=all` 0 行；候选→HEAD 全部差异只有四个文档文件（状态板、implementation-status、本项提案、复核文件）。
  主工作树与采集 worktree 均 `runInBackground: 1`。
- 采集 worktree `git checkout --detach <候选>`（此前在 R6 通过候选）：HEAD = 候选，`status --porcelain --untracked-files=all` 0 行；
  `runtime/models` 仍为指向主工作树模型目录的忽略链接。

**§1.2 重建清单（零消耗，已完成；未传输）：** `P1-ENG-LOOP-001-build-stage-b-manifest.py <scratchpad>/stage-b-staging-r7` 输出
`files_verified` 118、清单 sha256 `5714d37a…`、staging 213,590 B（五个文件）。三个源文件的 staging sha256 与候选 git blob 逐一相同
（`gated_publisher.py` `0dbbd03c…`、`language_bridge.py` `38de0d51…`、`language_loop.py` `e70aedc2…`）；runner `operations_5060_b.py`
`d691f84d…` 与上一版相同。已提交的 `-transfer-manifest-5060-stage-b.json` 相对上一版只变四处：`gated_publisher.py`、`language_loop.py`
两行哈希，`passed_candidate`，`transferred` 增加 `controller/gated_publisher.py`；staging 内清单与证据文件逐字节相同。staging 在会话
scratchpad，清单脚本确定性重建，入账后可原样重做再传。

**续做顺序（入账后，不变）：** 5060 在线（本次 `tailscale status`：`laptop` idle）且用户确认接电、睡眠=从不 → 传五个文件到 F 盘 `repo-b`
并逐文件比 sha256 → `amend`（幂等，应仍只有修订3/修订4 两条原记录）→ `preflight` → 用户打开 Unity（不 Play）→ §2 发令检查 →
交接改 `Consuming=yes` → 起服务（计 1 次启动）→ 登记并执行 `diag-loopb-6`（操作单 C §4）。

### 13.1 入账后传输、`amend`、`preflight`（零模型加载、零扣额）

用户原话（逐字）：「已入账，5060已经准备好」。账本条目 `docs/authorizations.md` 2026-09-23「第三源码传输（gated_publisher.py）与诊断 6 会话顺序
（实现会话代录）」已在磁盘上（辅助角色写入，本实现角色只读核对）。

- 传输前 5060（`laptop`，SSH `devuser`）：`operations_5060` 进程 0、8760 监听 0；`repo-b` 为 R6 候选五文件（`gated_publisher.py` `3c9724b1…`、
  `language_bridge.py` `38de0d51…`、`language_loop.py` `37528823…`、`operations_5060_b.py` `d691f84d…`、清单 `1efc65b9…`）。电源：交流
  （`BatteryStatus` 2），`STANDBYIDLE` 交流 `0`（从不睡眠）。
- `stage-b-transfer-r7.tar`（218,624 B，sha256 `7e4ab1f5…`，五文件）经 `scp` 到 F 盘 `tmp`，`tar.exe -xf` 解到 `repo-b`（退出码 0）；两端逐文件
  sha256 相同：`gated_publisher.py` `0dbbd03c…`、`language_bridge.py` `38de0d51…`、`language_loop.py` `e70aedc2…`、`operations_5060_b.py`
  `d691f84d…`、`transfer-manifest-stage-b.json` `5714d37a…`。未传权重/数据。
- `amend` 退出码 0：仍只有 `AC-12-rev3` 与 `AC-12-rev4` 两条原记录（`new_session_labels` = [`diag-loopb-5`,`-6`,`-7`]），未另加额。
- `preflight` 退出码 0：候选 = R7 `passed_candidate`、清单 `5714d37a…`、runner `d691f84d…`、K 收据 `b511ad6c…`、base `7de1838c…`（revision
  `89644892…`）、adapter `4044dd4f…`、c2-adapter、端点 `http://100.100.100.100:8760`、RTX 5060 Laptop GPU。
- B 账本（`ledger`）：启动 4/10、查询 9/400、拒绝 0；会话 `diag-loopb-2…5` = 1/1/1/6 行。
- Unity：用户选（`AskUserQuestion`，标签逐字）「已打开并载入场景，未 Play」。辅助角色的账本条目当时未提交、其交接行未删；用户选「我先让 chore 收尾（推荐）」，
  发令检查（§2）待其提交后再做。

### 13.2 `diag-loopb-6` 发令检查（2026-09-23T18:17–18:19-0400，Unity 已在主工作树打开场景、未 Play）

- §2.2 `check_docs.py` 通过；Active handoffs 仅本项一条未暂停 `Consuming=yes`（提交 `4a1649a…` 的状态板）；无未 release 的 blocks。
- §2.3 槽位隔离（只移动）：`metrics.json`、`tracking_observation.json`、`body_command.json`、`gimbal_command.json`、`language_request.json`、
  `language_result.json`、`tracker_state.json`、`m3_body_truth.jsonl` 与 `runtime/frames/` 257 个文件移入 `runtime/hold-diag-loopb-6/`，移动前后
  265 个 sha256 逐一相同；`runtime/frames/` 为空目录；`scenario_config.json` 不存在。
- §2.4 第一次 `lc_check`（18:17:38）：除「5060 /status not idle」外全 `ok`。§2.5 服务启动 **5/10**（后台 SSH 前台常驻），`/status` idle，
  身份六项（backend/model_form/base revision/weights/prompt/vocab sha）与 K 收据逐项一致；第二次 `lc_check`（18:18:12）全部 `ok`、`lc_check passed`
  （两次输出在 `outputs/eng-loop/P1-ENG-LOOP-001/diagnostics/operator/diag-loopb-6/precheck.log`）。§2.7 Play 登记见 §5 第 6 行。

### 13.3 `diag-loopb-6` 结局（原始路径 `outputs/eng-loop/P1-ENG-LOOP-001/diagnostics/diag-loopb-6/` 与同名 `operator/` 目录；诊断不复制进证据目录，不作 AC-13…15 证据）

**时间线（watch/会话日志）：** Play 18:20:15（`sim_t` 0.4 s）。用户点「指定」→ `q2`（帧 22，3.06 s）唯一候选 → 确认 → 段 1 `t1` 播种、
首批写出帧 64（`PUBLISHED first`），一圈窗口 t0 = 13.0 s。随后核验 `q3`（帧 64，IoU 0.46）与 `q4`（帧 81，IoU 0.0）均 `drift`，
进入 `SUSPECTED`；用户「解除疑似」→ 核验 `q5`/`q6` 仍 `drift` → 用户「判丢」，段 1 `verify_drift` 退役（帧 222）。之后用户三次指定并确认
（`q7` 帧 274 → 段 2；`q8` 帧 382 → 段 3；`q11` 帧 850 → 段 4），**三段都在首批写出前以 `catchup_stale` 退役**（`REINIT_REQUIRED`）；
另有 `q9`（帧 461）、`q10`（帧 545）两次候选被用户驳回（`operator_reject`，未播种）。用户「停止会话」（`TERMINAL`/`operator_stop`，
`sim_t` ≈ 193 s）后退出 Play（最后帧 1049，`sim_t` 210.3 s）。实现角色在段 2 触发后即告知用户属 §0 硬停止、建议停止；是否继续由用户决定。

**§4 各步：**
- 第 2 步持续供帧：`unfocused_frames` 1047、`max_stall_s` 0.0，全程无「帧停滞」（退出 Play 后的停滞除外）；`lc_keep` `kept=1050 gaps=0`。
- 第 4 步首批追平与机身：段 1 首批 `WRITTEN`（`load_elapsed_s` 0.191、`frame_delta` 2、`capture_age_s` 0.473）。机身通道段 1：`body_command`
  `WRITTEN` `velocity_world` 110 条、`body_safety_hold` `WRITTEN` 48 条；全会话 `WRITE_FAILED` 0、`BODY_COMMAND_FAIL_CLOSED` 0。保存帧
  `camera_position_world_m` 相对帧 64 最大水平位移 **20.6 m**（帧 173），末位置约 (134.0, 97.6)；`tether_saturated` 0 帧，`gimbal_saturated`
  980/1050 帧（帧 100 起基本持续饱和）。段 2/3/4 各只写 1 条 `body_safety_hold`（原因 `margin_below_trigger+corridor_blocked`），look_at
  `PUBLISH_REJECTED`（`orphan_control`）。
- **硬停止（§0）：** 段 2/3/4 首批 `observation` `PUBLISH_REJECTED`、原因 `catchup_stale`（`controller/gated_publisher.py` `_gate` ④：发布时
  `latest.json` 帧差 > `K_pub` = 2），帧差分别为 5 / 3 / 8。
- 第 5 步核验结果：≥2 次（`q3`…`q6`）。第 6 步人眼保真：见下。第 7 步 `lc_lap` 在真实帧上运行成功（退出码 0）：九点中 #0–#2
  `READY_FOR_USER`、#3–#8 `NO_VALID_BOX`（段 1 于帧 222 退役），`body_max_displacement_m` 20.60、`velocity_written_in_window` 110；产物在
  `lap-samples/`（含拼图）。诊断结果不作 AC-13 证据。
- 计数：本次 Play 查询 11 行（`q1`…`q11`；`q1` 帧 4 的指定被用户再次指定替换，结果 `IGNORED_STALE_EPOCH`）；B 账本停服后 启动 **5/10**、查询 **20/400**、拒绝 0、`diag-loopb-6` 11 行。
  5060 服务已停（剩余进程 0、8760 监听 0）。新增诊断（修订4）已用 2/3，余 `diag-loopb-7`；正式 0/8。

**首批追平量化（段首批 = 播种后第一个 `frames_processed` 批）：**

| 段 | 播种帧 | 批帧数 | 批耗时 | 每帧 | 跟踪 `compute_latency_ms` 中位（首批） | 发布时帧差 | 结果 |
|---|---:|---:|---:|---:|---:|---:|---|
| t1 | 22 | 42 | 0.397 s | 9.5 ms | 4.3 | 2 | `WRITTEN` |
| t2 | 274 | 44 | 0.910 s | 20.7 ms | 8.6 | 5 | `catchup_stale` |
| t3 | 382 | 32 | 0.608 s | 19.0 ms | 7.1 | 3 | `catchup_stale` |
| t4 | 850 | 44 | 1.733 s | 39.4 ms | 12.6（最大 88.9） | 8 | `catchup_stale` |

读法（事实，不作归因结论）：`_body_step` 只在批末最新帧执行（冻结 `track_loop.py` 文档串「runs on latest frames only」），批内每帧耗时 =
跟踪更新 + 读帧/日志等开销，两部分在段 2–4 同时变慢（相对段 1 约 2–4 倍），与会话内时间先后单调相关；原因（本机负载/降频或其他）未测。
积压 ≈ 模型时延约 3 s + 确认时间，5 Hz 下约 32–44 帧；K_pub = 2 要求批处理在约 2 帧间隔（0.4 s）内完成，即每帧 ≲ 9 ms——段 1 的 9.5 ms
恰在边界（帧差 = 2）。R1 §4 注记 6 与阶段 B 注记处置已预告此风险（「现有模型 p95 不能证明该门可过」）。

**跟踪漂移（段 1，事实）：** 播种时（帧 22→64 的约 8.4 s 内相机固定朝下）红车已行至画面右缘；帧 64 两框都在车上（IoU 0.46）；帧 81 起
云台饱和，跟踪框落到体育场红色看台上（`q4` 预览：VLM 框在红车上），帧 163 跟踪框在一辆黄色出租车上。机身在此期间按跟踪框移动 20.6 m。

**两张具名样帧人眼保真（workflow §4.3.2、AC-12 修订6；确认人 = 用户，本实现会话 `AskUserQuestion`，所选标签逐字）：**

1. `outputs/eng-loop/P1-ENG-LOOP-001/diagnostics/diag-loopb-6/previews/22-diag-loopb-6-q2.png`（帧 22，本次指定候选 `q2`）：
   问（逐字）："第 1 张（第 22 帧，指定候选 q2）：对照你在 Unity 里看到的画面，车辆、颜色、朝向是否一致？红框是否画在对的位置（框住目标红车）？
   问这个的原因：正式 P1 之前必须有两张具名样帧的人眼确认（工作流 §4.3.2、AC-12 修订 6），实现角色看图不能代替你。"
   用户选（逐字）："一致，框在红车上"。
2. `outputs/eng-loop/P1-ENG-LOOP-001/diagnostics/diag-loopb-6/previews/64-diag-loopb-6-q3.png`（帧 64，核验 `q3`）：
   问（逐字）："第 2 张（第 64 帧，核验 q3）：车辆、颜色、朝向是否与运行时一致？绿框（跟踪器）和红框（VLM）是否画在对的位置？（红车正在画面右边缘
   往外开，两个框都压在它身上，这张被核验判成漂移是因为两框重叠度只有 0.46。）"
   用户选（逐字）："一致，两框都在红车上"。

### 13.4 交接受角色：`diag-loopb-6` 硬停止（实现角色停在此处；不改代码、不开 Play、不启动服务）

按操作单 C §0/§4 第 4 步，`catchup_stale` 属硬停止：**不进入正式 P1**，报告后按原返工渠道处理。实现角色不自行解释合同、不改 `T_pub`/K/
场景/跟踪核心，也不以 `diag-loopb-7` 在正式运行之间「试数」。请接受角色裁定：

- **R-B12 归因与处置**：段 2–4 的 `catchup_stale` 是按合同 fail-closed 的正确拒收；但在当前积压（约 32–44 帧）与本机逐帧耗时（9.5–39.4 ms）下，
  首批追平门在正式 P1 中基本无法稳定通过（段 1 擦线）。是否归入实现缺陷回 K1K2K3（例如批内处理提速）、合同/参数问题（需改 K、`T_pub` 或积压
  来源，须用户），或环境问题；以及 `diag-loopb-7` 是否及何时可用。
- **R-B13 播种时刻目标已近离画**：固定朝下相机 + 约 3 s 模型时延 + 人工确认时间，使播种时红车已到画面边缘，段 1 在云台饱和后约 3 s 漂移。
  这对正式 P1「一圈单次演示」的可行性有影响，请一并裁定是否需要合同层处理（实现角色不提方案）。
- 两张具名样帧人眼确认已完成（上节），AC-12 修订6 的该前提在本候选下有记录；首批追平前提仅段 1 满足。AC-13…15 仍 `NOT_RUN`；F3/F8 不变。

**现状：** 5060 服务已停；`runtime/` 留有诊断 6 会话写出的桥文件与帧（下次发令前按 §2.3 隔离），`runtime/hold-diag-loopb-6/` 保留移入的
诊断 5 残留槽位文件；采集 worktree 在 R7 通过候选；会话、watch、操作页、保存器进程均已退出。
