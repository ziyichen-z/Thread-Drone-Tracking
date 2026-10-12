# P1-ENG-LOOP-001 — K1K2K3 候选（R-B8…11：机身跟随接入、一圈取样与操作单），交 C5@K1K2K3

Owner：实现角色（Claude Code `/implement`），2026-09-23。
输入：提案 Pending rulings **R-B8…11** 与追加的 AC-4 修订4、AC-19、AC-13 修订2、AC-12 修订6（冲突处以后者为准）；状态板交接行
「按提案 Pending rulings R-B8…11 … 交 C5@K1K2K3」；用户机身跟随原话已由接受角色入账（`docs/authorizations.md` 同日条目）。
零消耗：零 Play、零模型/5060 服务、零 ID、零下载、零传输；未写真实 `runtime/`。本文件是实现者自证，不是独立复核结论。

## 1. 候选与完整 diff

- 本候选 = 首次加入本文件的提交，运行时解析：`git log -1 --diff-filter=A --format=%H -- docs/evidence/P1-ENG-LOOP-001-K1K2K3-handoff.md`。
- 上一通过候选 = 复核文件最后一条 `passed_candidate`（R6）。完整候选 diff：`git diff <R6 passed_candidate> <本候选>`；其间另有接受角色
  的 R6 消费、R-B8…11 裁定与本实现角色的诊断 5 记录提交（只改状态板、提案、授权账本、implementation-status、prep 文件）。
- 本批改动（逐文件）：
  - `controller/gated_publisher.py`：机身通道（门控速度 / 无观测安全 hold / 写失败收据），收据闭集加 `WRITE_FAILED` 与 `body_safety_hold`。
  - `controller/language_loop.py`：`SessionConfig` 两个机身配置字段；`bind_body_runtime`（复用冻结 `_build_body_runtime` 校验并构造原型，
    不符即 `ConfigMismatch` 拒绝启动）；每段深拷贝独立规划器/估计器交给 `TrackLoop`；`run` 命令行总是带冻结配置；`session_started`
    日志与段运行日志抬头记规划器身份；`effective_scenario_document` 从 `read_scenario` 拆出；`FixtureFramePublisher` 相机姿态可设（测试用）。
  - `tests/test_language_loop.py`：新增 `BodyPlannerIntegrationTests` 10 项；收据闭集测试改为四值 outcome + 四值 channel。
  - 操作载体（PLAY_GOVERNING）：`-operations-c.md`（状态、额度、§1/§2 检查、§3 终端、§4 诊断 6/7、§5 一圈单次演示与冻结取样规则、§7）、
    `-operator.sh`（`lc_run` 显式传冻结配置、`lc_keep`、`lc_lap`、`lc_check` 查残留帧保存进程）、`-operator-watch.py`（一圈窗口行、
    机身位置/位移/命令模式）、`-build-stage-b-manifest.py`（传输集合加 `controller/gated_publisher.py`）、新增 `-frame-keeper.py`、`-lap-samples.py`。
  - 自测与证据：`-c2-carrier-selftest.py`（keeper/lap/watch-lap 三部分）、`-k1k2k3-carrier-selftest.log`、`-tests-k1k2k3.log`、本文件；状态板。
- 零改动（机检见 `-k1k2k3-carrier-selftest.log` §1）：`controller/body_planner.py`、`controller/track_loop.py`、`controller/language_bridge.py`、
  `config/`（含 `p1-m3-body-001.json` 与场景）、`Assets/`、`ProjectSettings/`、`Packages/`、`tools/`、5060 runner、操作页 `-operator-web.py`、
  Play 治理门三文件。

## 2. workflow §4.3.1 四项自证

1. **范围与接口冻结**：只做 R-B8…11 点名的接入、操作单与取样保全（§1）；规划器、配置、场景、Unity、控制包 schema、桥协议闭集、
   K 收据零改动。发布收据文件（Python 侧日志，非 Unity/控制包）闭集按 AC-19「区分命令意图和实际写入」各加一值。
2. **相称测试**：新增具名用例 10 项，其中 6 项在 R6 的发布门上红（`-k1k2k3-carrier-selftest.log` §4），关键回归「无观测帧的 hold 被判
   `catchup_stale` 杀段」有探针原样对照（§4.1）；载体自测 111/111（新增 12 项），旧 watch 与三个变异体各红对应检查（§3）；focused
   326 + 113 全绿（§5）；隔离副本停点全套 `Ran 1534`、failures 0，9 个 `ERROR:` 与 `-tests-r5-fix.log` 排序后逐名相同、skip 清单相同
   → 新增失败 0（`-tests-k1k2k3.log`；副本 `runtime/` 只有 README，`RealArchiveClosureTest` 仍 skip，不作归档闭合证据）。
3. **已知 Unity 失败**：本批不改 Unity；机身在真实 Unity 里的运动、首批追平与操作页只能在 C5/R7 通过后的获准诊断 6/7 里核实。
4. **状态板、候选提交、复核范围**：交接行转接受角色 C5@K1K2K3，只写本文件指针；复核范围见 §6。

## 3. 逐 AC 证据指针

| 编号 | 自证 | 证据 |
|---|---|---|
| AC-19 | 段构造复用冻结 `_build_body_runtime`（threshold、`config/p1-m3-body-001.json`、生效场景），不改规划器/配置/Unity/控制包 schema；场景与生效场景不一致、`capture_hz` 不符、`expires_after_s` ≠ 2/hz、校准/走廊哈希不符、地面高度与路线不符 → `ConfigMismatch` 拒绝启动（在会话锁与任何桥写入之前），无降级路径；初始化一次性 hold 照旧；`velocity_world` 只经冻结 `_body_step` → `GatedPublisher._derived`，与同帧 `WRITTEN` 观测绑定、写前重核五项；静音/无关联/拒收不写速度并抛 `BodyCommandNotWritten`，由冻结回退补一次显式 hold；无观测、规划器判停、规划器异常、写失败回退的 hold 走无观测安全通道（`body_safety_hold`，`frame_id` 为空，不冒充门控速度）；写失败记 `WRITE_FAILED`；回退再失败 → 冻结 `BODY_COMMAND_FAIL_CLOSED` 终止段；段 finalize 后两通道零写入零收据；日志 `body_planner.mode` 与 `published_mode` 分列意图与实际；在线路径只读传感器帧元数据（`PlatformState`、估计器），不读真值文件 | `tests.test_language_loop.BodyPlannerIntegrationTests`：`test_a_mismatched_planner_config_refuses_to_start`、`test_the_run_cli_always_binds_the_frozen_planner`、`test_seeding_keeps_the_one_time_hold_and_writes_no_image_derived_body_command`、`test_a_tilted_camera_moves_the_body_with_a_same_frame_gated_velocity`、`test_a_frame_without_an_observation_sends_a_safety_hold_and_keeps_the_segment`、`test_a_rejected_velocity_falls_back_to_a_safety_hold_and_ends_the_segment`、`test_a_planner_exception_publishes_a_safety_hold`、`test_a_failed_velocity_write_is_receipted_and_falls_back_to_a_hold`、`test_a_failed_fallback_hold_fails_closed`；冻结规划器回归 `tests.test_m3_body_tools`/`test_m3_body_policy`（§5 全绿，规划器零改动）；`-k1k2k3-carrier-selftest.log` §4 |
| AC-4 修订4 | 每个已确认段一个独立规划器与估计器（原型深拷贝，原型本身从不交给段）；未确认、初始化静音、退役段、终态不发由图像推出的机身命令；`raw_lost`/`raw_ok`、意外段终止（`BODY_COMMAND_FAIL_CLOSED` 走 AC-4 修订2 兜底：逐字记 `unexpected_segment_end` 并按 `metadata_invalid` 终止）、人工判丢/重指定/停止与单次 finalize 规则未改 | `test_each_segment_gets_its_own_planner_and_nothing_is_written_after_retirement`、`test_seeding_keeps_…`、`test_a_failed_fallback_hold_fails_closed`；会话日志 `session_started.body_planner` 与段运行日志抬头身份 |
| AC-13 修订2 | 取样规则、机械条件与判定按修订2 逐条写成可执行脚本并在操作单 §5 冻结（t0 = 首条 `WRITTEN` 观测帧的仿真时刻；九点 t0 + i·106.5/8；最近保存帧、偏差 ≤ 2 帧否则 `MISSING_FRAME`；无框 `NO_VALID_BOX`；窗口内无 LOST/REINIT/TERMINAL/退役/意外终止、无 `PUBLISH_REJECTED`、无身份更换、≥1 条门控速度、机身位移 ≥0.5 m）；脚本不宣告 `LAP_DEMO_PASSED`，须加用户九张逐张确认；源帧保全 = `lc_keep` 全程逐帧原字节保存，缺口如实记。Play 证据未到时点 | 载体自测 lap 五项 + keeper 四项 + watch-lap 两项（真实 `LanguageSession` + 冻结规划器驱动，一次全过、一次故意违反多项）；`-operations-c.md` §5；`-lap-samples.py`、`-frame-keeper.py` |
| AC-12 修订6 | 操作单与 runner 沿用既有标签与累计记账（不改 runner；诊断只余 `diag-loopb-6/7`，旧号 1…5 禁用）；顺序改为 K1K2K3 通过 → 诊断 6/7 → 正式 P1/P2；正式 P1 前两张具名样帧人眼保真（路径/确认人/结论）写入 §4 第 6 步；采集 checkout、主树、5060 导入源码逐项对应最后通过候选（§1：Python 改动须落在三文件传输集合内，清单脚本对阶段 A 副本机检漂移 = 传输集合） | `-operations-c.md` §0…§4、§7；`-build-stage-b-manifest.py`；`-k1k2k3-carrier-selftest.log` §6 |
| AC-18 等 | 操作页零改动；AC-1…17 其余条款运行时路径除上列外零改动 | §1 零改动机检 |
| AC-13…15 | 未到证据时点，正式 Play 0 | — |

## 4. 实现中的解读与请 C5 关注的点（不自行扩大；有异议请按合同退回）

1. **hold 不过发布门**：AC-19 写「无观测、规划器异常、命令写失败或发布门拒收时 … 显式安全 hold 可经无观测的安全通道发出」。实现把
   **所有** `hold` 模式命令（含规划器自身判停，如 `margin_above_release`）都走安全通道，理由：hold 不由图像推出运动，且若判停也过门，
   无观测帧会因沿用上一帧关联被判 `catchup_stale` 而杀段（§4.1 探针）。门控只管 `velocity_world`。
2. **段 finalize 时不补 hold**：人工判丢/释放/停止或到时结束时，最后一条速度命令在 `expires_after_s` = 0.4 s 后由接收器过期回落；
   实现未在 finalize 里补发 hold——冻结规划器合同第 3 条禁止 `_body_step` 以外的机身写入点，AC-4 亦要求 finalize 后零收据。若接受角色
   认为 finalize 应有显式 hold，须改冻结合同或另给写入点，请裁定。
3. **`BODY_COMMAND_FAIL_CLOSED` 的状态原因**：沿用 AC-4 修订2 兜底（`unexpected_segment_end` + `metadata_invalid`），未新增桥原因枚举；
   该原因词不贴切，但 AC-4 修订4 写明意外段终止规则不变。
4. **无机身配置的会话**：`SessionConfig` 两字段为空时不接规划器，只供离线回放演示（`language_demo`）与旧测试构造；Play 入口 `run`
   总是带冻结配置、没有关闭开关。
5. **取样的「对应观测」**：每个取样帧取段运行日志里该帧的跟踪框（批处理中间帧也有框，但观测只在批末写出）；报告另列该帧是否有
   `WRITTEN` 观测（`observation_written`），供核对。
6. **t0 只按首段**：一圈窗口按会话首条 `WRITTEN` 观测起算，后续段不重新起算（修订2「同一已人工确认的红车段」）；watch 对新段只提示
   「不重新起算」。
7. **诊断 6/7 不再单独做 10 s 失焦测试**：诊断 5 已观察到后台持续供帧，改为全程由 watch 的 `unfocused_frames`/「帧停滞」判定，
   以免占掉第 1 入画窗；若接受角色要求保留单独步骤，请退回。

## 5. 未验证项与已知限制

- 机身在真实 Unity 中的运动、走廊阻挡与系绳饱和、页面与 watch 的机身行，只有获准诊断能证实；自测的夹具没有物理（位移由测试写进帧元数据）。
- 冻结规划器只看云台余量与方位；BODY-001 臂 B 的整圈几何可见不等于本项一圈演示必然通过（遮挡、跟踪器冻结框仍可能出现）。
- 帧保存进程与会话进程独立，若机器过载导致落后超过 128 帧会出现缺口，按规则判该点 `MISSING_FRAME`，不补造。
- 5060 端：传输集合变为三个源文件（+ runner、清单），须 C5/R7 通过后重建清单、传输、`preflight`；runner 零改动。
- F3（`SCOPE_GAP`，账本 OPEN）未动。

## 6. 给核对与复核角色的范围（C5@K1K2K3 → 新鲜上下文 R7@K1K2K3）

- 完整 diff：`git diff <R6 passed_candidate> <本候选>`；K1（机身通道与发布门同帧关联、收据闭集）、K2（机身速度/安全 hold/写失败/fail-closed、
  段切换与退役后零写入）、K3（人工判丢/重指定/停止边界不变；一圈取样与用户逐张确认的判定边界）逐项覆盖。
- PLAY_GOVERNING 非空（操作单、operator.sh、watch、清单脚本与两个新载体）。
- 重跑：`.venv-language` focused（§5 两组）；`.venv-loop-client/bin/python docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.py`（系统 python3
  缺 Pillow 时渲染项显式 skip）；红跑用 `--watch/--keeper/--lap` 指向旧版或变异体；不需要 GPU、Unity、5060 或网络。

## 7. 用户在本会话的实现细节选择（`AskUserQuestion`，所选标签逐字；零消耗、在 AC-13 修订2 已接受范围内，不是新授权）

1. 问：「正式 P1 跑完后，9 张取样图要你逐张确认「红车可见、框在车上」。你想怎么看、怎么给结论？」选：「生成带框图，我在聊天里逐张
   回复（推荐）」（未选：「本地网页逐张点选」）。落实：`lc_lap` 生成九张带框图与九宫格总览，实现发给用户、逐字记录回复。
2. 另：用户要求本会话起汇报只用中文、不中英混合（沟通偏好，不影响合同）。
