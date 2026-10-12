# P1-ENG-FRAME-001 独立复核（机身跟随 c-组合 + 系留可关闭，engineering-v1，停点 `K2`）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-FRAME-001-R1@K2-20261001T173044Z-681c`，`requested.round = R1@K2`）。
轨道：提案抬头逐字 `Workflow: engineering-v1`，接受角色在「D2 接受裁定」`ACCEPTED` 时逐字裁定生效 → 按 `docs/engineering-workflow.md` 复核；依据列仍写 `BC-n`，读作任务合同第 n 条验收项 `AC-n`。复核文件按提案 §7 分 §T / §P / §共用核对，finding 标所属 Part。
零消耗：零 scenario/session/run ID、零 Unity Play、零付费 API/GPU/VLM、零下载/安装/远端。只在一次性副本内读码、重跑 focused、重跑回放 `--check`、以本机 Unity 6000.4.1f1 batchmode 重跑 Edit Mode 全套（非 Play、零 ID；副本自带 `Library/` 副本，主树未被 Unity 触碰）、跑三个只读探针（脚本在会话暂存目录，不入库）。

## R1@K2（2026-10-01）

### §0 候选、基线与开轮资格

- `round_candidate: c715886bd09c0a54704267ad0a5f22311cf2a196`（= 上一实现派发 `C1@K2返工` 的 `finished.candidate`；主树 HEAD 4ecfccc 相对候选只多 supervisor 派发日志、接受角色 C2 核对表、`docs/roles/supervisor.md` 与 changelog 等文档提交，`Assets/ controller/ config/ tools/ tests/` 零差异）。
- 全量 diff 基线：本文件此前不存在，无 `passed_candidate`；基线按交接文件解析块运行时解析 `$BASE` = `9417656`（`K2 开工` 提交的父提交）。`git diff --name-status $BASE..c715886` 共 27 路径，已逐文件核对：实现文件 `Assets/TetheredTracking/Scripts/{ScenarioConfig,TetheredDronePlant,TetheredScenarioBootstrap}.cs`、`Assets/TetheredTracking/Tests/EditMode/TetheredTrackingEditModeTests.cs`、`controller/{scenario_tether,standoff_planner,track_loop}.py`、`config/{scenario.untethered,p1-eng-frame-001-body}.json`、`tools/{frame_follow_replay,run_track_experiment}.py`、`tests/{test_frame_tether_switch,test_standoff_planner,test_frame_follow_replay,test_track_loop,test_track_experiment}.py`、`PROJECT_BRIEF.md`；其余为证据（`docs/evidence/P1-ENG-FRAME-001-*` 6 件）、状态板、消耗账本、提案核对表（接受角色提交 c41d4e0）、`docs/authorizations.md`（supervisor 代录 0a69064）与派发日志（supervisor 提交）。无 `*.meta`/`*.unity`/prefab、无 `controller/language_loop.py`、无 ACQ 文件、无 `tools/check_*.py`、无工作流文件（AC-25 成立，IR-9 的两类流程文件如实披露）。
- 开轮资格：PLAY_GOVERNING（`controller/`、`Assets/`、`tools/`、`tests/`、`config/`）diff 非空 → 开轮。首个复核轮，无上一复核轮候选、无修前红/修后绿义务。
- 停点自证（`docs/evidence/P1-ENG-FRAME-001-K2-handoff.md` §T / §P「四项条件自证」）四项成立：接口冻结（帧包/命令包零改动，AC-6 cmd 空）、全套与 Edit Mode 已跑（新增失败 0、284/284）、无未修复 Unity 失败、候选已提交推送且状态板/证据已更新；不判 `REVIEW_BLOCKED`。
- 复核副本 `.claude/worktrees/review-P1-ENG-FRAME-001`（detach 于候选），测试树哈希 `HEAD:tests = 956fc5c791ce0c70d07b156470f2cd26dd6e93bc`。解释器 `.venv-yoloe/bin/python`（3.12；按派发附注，本机无 `~/TetheredDroneTracking-full`）。
- focused 重跑（`-m unittest discover -s tests -p <x>.py`，输出写会话暂存目录，只回显摘要）：`test_frame_tether_switch` 18 OK；`test_standoff_planner` 32 OK（21.7 s）；`test_frame_follow_replay` 15 OK；`test_track_experiment` 7 OK；`test_track_loop` 26 → 1 败 = 基线既有 `test_cli_runs_pinned_csrt_to_a_versioned_summary`（本机 cv2 无 `TrackerCSRT_create`，与交接基线 13 项逐名相同，非本候选）；AC-7 的 `test_m3_body_tools` 56 OK、`test_m3_body_policy` 29 OK、`tools/build_m3_corridor.py --check` → `corridor check OK: 779 prisms`。
- 证据复算：`tools/frame_follow_replay.py --check` 在副本内全网格重跑，`replay evidence matches`（82 s）；`docs/evidence/P1-ENG-FRAME-001-tests.log` 的 13 条 FAIL/ERROR 逐名等于交接列出的基线集合；`config/p1-eng-frame-001-body.json` 所钉 BODY-001 sha `3d1c4b…` 与回放证据 sha `8e35ca…` 均与现行文件实算相等；本机 `Logs/P1-ENG-FRAME-001-editmode-rework.xml` sha256 `662a58…`、284/284，`-rework-red.xml` sha256 `84bab9…`、6/3/3，与交接所记一致。
- **Unity Edit Mode 独立重跑**（副本内，`cp -R` 主树 `Library/` 后以交接「Unity Edit Mode」小节同一命令、`-testFilter TetheredTracking.Tests`；启动前后 `pgrep` 无编辑器进程；主树未被触碰）：`Logs/R1K2-editmode.xml` **total 284 / passed 284 / failed 0 / skipped 0**，日志无 `error CS`，`Test run completed. Exiting with code 0 (Ok)`；本批 15 条用例与两条既有用例（`HappyPathBindsReviewedIdentity`、`CheckedInConfigsCarryTheSameStrictSceneAdjustment`）逐名 `Passed`；跑后副本 `git status --porcelain` 为空（`ProjectSettings/`、`Packages/packages-lock.json` 未变）。产物只在副本 `Logs/`，随副本删除。
- cmd 核对：AC-3 `git diff --exit-code $BASE -- 'config/scenario*.json' ':!config/scenario.untethered.json'` 退出 0；AC-6 `… -- controller/protocol.py controller/body_entry.py controller/gimbal_entry.py` 与 `SensorFrameWriter.cs` 退出 0；AC-7 四份冻结资产 diff 退出 0；AC-18 `controller/language_loop.py` diff 退出 0；AC-22 `grep -nE 'metrics.json|m3_body_truth|route_world_m' controller/standoff_planner.py controller/scenario_tether.py` 无命中；AC-9 两份场景 JSON 规范化 diff 恰为 `scenario_id`、`drone.tether_enabled`、`drone.geofence_xz_m`。

### §1 逐文件核对摘要

| Part | 文件 | 结论 |
|---|---|---|
| T | `Assets/TetheredTracking/Scripts/TetheredDronePlant.cs` | `Step` 有缆分支逐字 = 基线（只是缩进进 `if (tetherEnabled)`），其后追加 `geofenceEnabled` 钳位；无缆分支：`TetherSaturated = false`、高度 `Clamp(min, max)`、不做球面钳；`ConfigureGeofence(null)` = 无围栏。与 §3.2 一致。 |
| T | `Assets/TetheredTracking/Tests/EditMode/TetheredTrackingEditModeTests.cs` | `LegacyPlantReference` 的字段、`SetVelocity`、`Hold`、`Step` 经脚本逐行（去缩进）与 `$BASE` 文件比对**完全相同**（唯一改编 `transform` 为字段，如交接所述）；`Step_TetherEnabledMatchesLegacyReferenceBitwise` 10 条序列 × 缺省/显式 true 两路逐位比对；五条 `Step_TetherOff_*` 各带有缆对照红；`ClosedFixtureSet`/`ExplicitValueFixtures`（17）/`KeyContextFixtures`（4）与 Python 同名同插入文本；`SerializerPaths_NeverMaterialiseAGeofence` 钉住原始解析与 `ToJson` 往返；`AnchorMarkerAndOcclusionRoots` 以源码文本钉 `Awake`/`CreateAnchor`/`OcclusionGeometry.Build`（IR-8，经本人 diff 核对两处代码未改）；`FrameProtocolInvariantTests` 以反射钉 v3 字段集。 |
| T | `Assets/TetheredTracking/Scripts/ScenarioConfig.cs` | `Load()` 只改 `projectDefault = VersionedDefaultPath`，覆盖优先与 `CreateDefault()` 回退逐字不变（AC-27）；`FromJsonStrict` 先 `ReadTetherKeys`（结构化读取器只列根与 `drone` 直接成员，同名键取最后一个，`tether_enabled` 只认 `true`/`false`，围栏四界经 `JsonNumber` 正则 + `double.TryParse` + float32 溢出检查）再 `JsonUtility.FromJson`、`ApplyTetherKeyPresence`；`Normalize` 有缆分支高度钳逐字同基线，无缆分支 `Max(0.1, min)`/`Max(min, max)`；`NormalizeGeofence` 出现即校验（有限、`min < max`、含 home），无缆缺围栏拒绝。`[NonSerialized] geofence_xz_m` 的后果见 §5。 |
| T | `Assets/TetheredTracking/Scripts/TetheredScenarioBootstrap.cs` | 只增 `Drone.tetherEnabled`/`ConfigureGeofence` 两行赋值与 `CreateTetherLine`（有缆才建，参数逐字同旧：名 `TetherLine`、`drone`、`anchor`）；`CreateAnchor`、`CreateEvaluationOcclusionGeometry` 无改动。SensorCamera `localPosition = Vector3.zero`（供 §5 判断）。 |
| T | `controller/scenario_tether.py` | §3.1 规则：非 bool 开关拒绝、围栏对象/四界/有限/`min<max`/含 home、无缆缺围栏拒绝；高度规范化两模式与 C# 同式；`effective_scenario_path` 覆盖优先、否则 `config/scenario.untethered.json`（AC-29）；`safety_bounds` 按模式记可达圆/围栏（AC-10）。只读运行时配置，无真值引用。 |
| T | `controller/track_loop.py`（`threshold` 分支） | 仅在 `elif policy_name == "threshold":` 首部加 `parse_tether_settings(scenario).tether_enabled` 否则 `ValueError`；有缆路径逐字不变（AC-8 用例以旧构造法独立实例 120 帧逐条相等）。 |
| T | `config/scenario.untethered.json`、`tools/run_track_experiment.py`、`tests/test_track_experiment.py` | 差异键闭集成立（AC-9）；常量一行改动（AC-28），`DefaultScenarioEntryTests` 以逐字期望 JSON 比对缺省与显式旧文件输出、不透传 `--body-*`。 |
| P | `controller/standoff_planner.py` | 第 1–6 步顺序与 §3.6 一致：兜底每帧先 `decide`（畸形输入异常 → 无兜底）；契约 hold 三种（含平台位置非有限、裕度不可构造/非有限，IR-5）；估计闸 σ（对称化 2×2 最大特征值，IR-6）> w / 非有限 / d̂ > d_plaus；锁存 `> d*+w` 置位、`≤ d*` 复位、近侧不后退；兜底仅在 2/3 步结论 hold 时采用；第 5 步 ①(a) 可达圆仅有缆、①(b) 围栏配置出现即启用、先 (a) 后 (b)、残余 < 0.05 m/s → `+boundary_blocked`、位移截到 `v_max·0.4`（IR-2）、② 机身线段避障两模式、③ 走廊仅有缆、末端以消费者同式复核（IR-3）；闭集 `compose_reason`/`split_reason`。`PrismIndex` 格预选为纯加速（精确超集），`segment_hits_prism` 与冻结 `segment_intersects_prism` 逐项同式。**见 R1-1。** |
| P | `controller/track_loop.py`（`standoff`） | `build_standoff_planner` 从冻结 BODY-001 配置逐字取 `policy`/`command.expires_after_s`/走廊工件（sha 校验），`fixed.corridor_pad_m` 必须等于 0.5 + 0.5（IR-1）；无缆时兜底与新策略均不带走廊；`_build_standoff_runtime` 校验 FRAME 配置（及其两个 sha）、`scenario_id`、路线地面高、生效场景逐值相等（`effective_document != scenario` 拒绝）；身份含 planner/FRAME sha/场景 sha/生效路径与 sha/候选/参数/`safety_bounds`；CLI `choices` 加 `standoff`，三参数无缺省。 |
| P | `tools/frame_follow_replay.py` | `UnityPlantMirror` 逐式对照 Unity `Vector3.MoveTowards`/`ClampMagnitude`/`magnitude`/`Vector2.normalized`（`kEpsilon` 1e-5）与 `TetheredDronePlant.Step` 两模式：每个 C# 存储点一次 `r32`，一致；回放网格、噪声 E0/E1/E2、H1–H5 与选择规则（3% 平手 → 起停 → 编号）与 §3.9 逐条一致；`_clearance_check` 产出 AC-10 离线核对；真值只在本工具内合成观测与读数。`analyze_run` **见 R1-2、§5。** |
| P | `config/p1-eng-frame-001-body.json` | `selected_candidate = C3`、`params` = 回放 `selection.selected_params`、`fixed` = §3.7 值；两处 sha 实算相等（AC-17/AC-20）。 |
| P | `tests/test_standoff_planner.py`、`tests/test_frame_follow_replay.py`、`tests/test_track_loop.py` | 具名用例对准 AC-11…AC-20/AC-22；AC-15 四个方法名逐字取合同，F-on/F-off/F-both 10,000/10,000/1,000 状态、F-off 越圆 ≥ 100 断言取自非 hold 速度输出（D2 裁定）；AC-18 三种覆盖/无覆盖红绿。AC-11「有限输入不抛异常」用例只覆盖对角方差 ≤ 1e6 → 未覆盖 R1-1。 |
| 共用 | `PROJECT_BRIEF.md`、`docs/evidence/P1-ENG-FRAME-001-play-ops.md` | 措辞限 §9.3 第 9 项（有缆历史/无缆新缺省、三处入口、「实现至 K2 候选；复核与 Unity 待完成」）；操作单含 §3.11 入口清单、覆盖缺席核对与 hold 步骤、source_path 核对句、三个 body 参数逐字。 |

### §2 AC 逐项与 C2 关注项（依据列 `BC-n` 读作 AC-n）

| AC | 结论 | 依据 |
|---|---|---|
| AC-1 | 成立 | 7 闭集 + 17 显式值 + 4 语境夹具两侧同名同文本，Python 18 例与 Edit Mode 6 例均在本轮独立重跑中通过。闭集外 float32/float64 差异见 R1-3（`SCOPE_GAP`）。 |
| AC-2 / AC-3 / AC-27 | 成立 | 参考副本逐行等于基线（§1）；17 个既有文件字节不变（cmd）且逐位回归通过；`Load()` 只改一行。 |
| AC-4 / AC-5 / AC-6 | 成立 | Edit Mode 重跑通过；帧写入器与协议文件零改动；关闭模式恒 false 由 `NeverReportsTetherSaturated` 覆盖。 |
| AC-7 / AC-8 / AC-9 / AC-10 / AC-28 / AC-29 | 成立 | §0 cmd 与 focused 重跑；AC-10 回放证据 `obstacle_clearance`：围栏内 70 棱柱、顶高 16.93 + 2.1 < 25.2，15 m 档如实列冲突。 |
| AC-11 | **不成立** | 见 R1-1（有限协方差 `OverflowError`）。其余子项（纯度、三种 hold、重放、`vy = 0`、0.4 s、只 import 契约类型）成立。 |
| AC-12 / AC-13 / AC-14 / AC-15 / AC-16 / AC-17 | 成立 | 读码 + focused 重跑；AC-14 的 IR-1（0.5 + 0.5 = 1.0）与生产阈值分支同法，`build_standoff_planner` 另作等式校验。 |
| AC-18 / AC-20 | 成立 | `StandoffWiringTests` 红绿；配置 = 回放选中项、sha 实算相等；操作单含入口清单。 |
| AC-19 | 成立 | 镜像两模式对 AC-2/AC-4 金标准（≤ 1e-5）通过；`--check` 全网格逐字节一致；选参复算 = C3。镜像「存储时舍入」对真实 plant 逐位相等的主张（10,400 状态）依赖实现者本机导出，本轮以 Edit Mode 金标准用例（≤ 1e-5）独立通过为据，不外推逐位结论。 |
| AC-21 / AC-23 | `NOT_RUN`（如实） | Unity 阶段；但读数工具的场景绑定缺口见 R1-2，须在 Play 前闭合。 |
| AC-22 / AC-24 / AC-25 / AC-26 | 成立 | §0 cmd；全套 2057、新增失败 0、13 项与基线逐名相同；27 路径归属已核；交接分节自证齐全。 |

C2 关注项核实：**T-1**（`[NonSerialized]` 与调用可达性）→ 无可达缺陷，见 §5；**T-2**（结构读取器）→ 逐函数读码，闭集内一致，闭集外差异不构成缺陷，见 §5；**T-3**（数值接受域）→ 探针证实差异存在，列 R1-3 `SCOPE_GAP`；**P-1**（有限协方差）→ 探针证实，列 R1-1 阻断；**P-2**（后处理与回归参照）→ `PrismIndex.blocked`/`_post_process`/`_shorten`/末端守卫读码成立，`LegacyPlantReference` 逐行相等；**P-3**（Play 分析绑定与量源）→ 绑定缺口列 R1-2 阻断，量源见 §5。

### §3 Findings

| ID | Part | 分级 | 依据 | 阻断 | 摘要 |
|---|---|---|---|---|---|
| R1-1 | P | CLASS_2 | `BC-11` | 是 | `_position_sigma` 对有限大方差抛 `OverflowError`，违反 AC-11「有限输入不抛异常」 |
| R1-2 | P | CLASS_2 | `IN_SCOPE_NO_BC` | 是 | `analyze_run` 不按 §3.11 入口 8 绑定 run manifest 的场景 sha/来源路径，错场景静默接受 |
| R1-3 | T | CLASS_2 | `SCOPE_GAP` | 否（路由接受角色） | AC-1 闭集外围栏界值的 float32/float64 接受域两侧不同 |

#### R1-1 有限协方差使 `decide` 抛异常（`controller/standoff_planner.py::_position_sigma`，Part P）

- 合同：AC-11「`StandoffBodyPlanner` 实现契约 v1：… 有限输入不抛异常」。
- 实现：`largest = 0.5 * (a + d) + math.sqrt((0.5 * (a - d)) ** 2 + b * b)`。Python 浮点 `**` 在结果超出 double 范围时抛 `OverflowError`（乘法只会给 `inf`），而非有限检查 `isfinite(largest)` 在其后；`decide` 只对兜底 `self._fallback.decide` 捕获 `ArithmeticError`，对 `_follow_branch` 未捕获。
- 探针（副本内，`build_standoff_planner` 生产构造，untethered 与 default 两场景，平台在锚点上方 25 m、估计点 10 m 外）：协方差 `diag(1e200,1,1,1)`、`diag(1e155,1,1,1)`、`diag(float_max,1,1,1)` 三例均 `decide` → `OverflowError: (34, 'Result too large')`；对照 `b = 1e200` 非对角 → `hold_estimate_uncertain`（`b*b = inf` 走非有限分支），`diag(1e6)` → `hold_estimate_uncertain`，均值/速度/平台取 `1e308` → 分别 `hold_estimate_implausible` / `follow_move`（速度钳 4）/ `hold_estimate_implausible`，不抛。
- 影响：`track_loop._body_step` 对 `decide` 的任何异常发布 hold 并记 `planner_error`、reason `planner_exception`（行表第 7 行），故运行时不崩溃、不发速度；但 AC-11 字面不成立，且该帧 run log 的 reason 落在 §3.6 闭集之外。既有用例 `test_finite_inputs_never_raise_and_keep_contract_fields` 只取对角方差 `{1e-6, 0.25, 4, 1e6}`，未覆盖。
- 范围判据：AC-11 点名「有限输入」→ 可达；依据 `BC-11`，阻断。
- 闭合回归（修前必红）：`tests.test_standoff_planner.StandoffContractTests.test_large_finite_covariance_holds_without_raising`（新）——以 `build_standoff_planner`（生产构造）在 untethered、default、F-both 三场景上，对协方差 `diag(1e155,1,1,1)`、`diag(1e200,1,1,1)`、`diag(sys.float_info.max,1,1,1)` 与非对角 `1e200`（对称）各断言 `decide` 不抛、`mode == "hold"`、主标记 `hold_estimate_uncertain`、`vy = 0`、`expires_after_s = 0.4`；并把随机用例的方差候选集扩到含 `1e200`。修法由实现角色定（例如 `math.hypot(0.5 * (a - d), b)` 不会溢出，或在 `_position_sigma` 内捕获 `OverflowError` 返回 `None`）；R2 以 `git revert -n <fix>` 做修前红/修后绿。

#### R1-2 Play 读数工具不绑定 run manifest 的场景（`tools/frame_follow_replay.py::analyze_run`，Part P）

- 合同：§3.11 入口 8「回放工具 `tools/frame_follow_replay.py`：无缺省；网格两个场景路径写死；**`--analyze-run` 读 run manifest 的场景 sha 与来源路径**」；§3.8 run manifest `body_planner` 身份含「场景 sha、生效场景来源路径」正是为此绑定而写入；AC-23 的 T 行（围栏内、高度、`tether_saturated`、越 35 m 帧数）全部依赖所用场景几何。
- 实现：`analyze_run(run_directory, truth_path, metrics_path, scenario_path)` 读 `manifest.json` 后只转写 `run_id` 与 `body_planner`，几何（围栏、锚点、路线、初始高度、内参）全部来自 CLI 显式 `--scenario`，与 manifest 的 `scenario_config_sha256` / `effective_scenario_sha256` / `effective_scenario_path` 不作任何比对；输出也不记录所用场景文件的 sha。
- 探针（副本内，manifest `body_planner` 形如 `_build_standoff_runtime` 身份、钉 `config/scenario.untethered.json` 的 sha；truth 1 帧机身 x = 100）：`--scenario config/scenario.untethered.json` → `T_fence_violation_frames = 1`；改传 `config/scenario.default.json` → **静默接受**，`scenario_id = deterministic-loop-default`、`T_fence_violation_frames = None`（无围栏），manifest 仍写着 untethered 的 sha。即 AC-23 的 T 行读数可被错传的场景文件改写而无任何拒绝或告警。
- 范围判据：Play 收集步骤（操作单 §5）直接调用该入口，可达；§3.11 入口 8 为合同正文但无 `AC-n` 逐字覆盖 → `IN_SCOPE_NO_BC`，阻断（须在 AC-21/AC-23 的 Play 之前闭合，否则 Play 证据的几何来源不可核）。
- 闭合回归（修前必红，fixture 走生产路径）：`tests.test_frame_follow_replay.AnalyzeRunTests.test_analyze_run_refuses_a_scenario_that_differs_from_the_manifest`（新）——manifest 由生产写盘函数产出：身份取 `controller.track_loop._build_body_runtime(FRAME_CONFIG, UNTETHERED, "standoff", scenario_id=…, ground_plane_y_m=0.2, runtime=<临时 runtime>)` 的第 4 个返回值，经 `controller.run_log.RunLogger(..., manifest={"body_planner": identity, …})` 写出 `manifest.json`（`track_loop.py:1377` 同一路径），禁止手写 JSON 造 manifest；断言 `analyze_run(run, truth, None, DEFAULT_SCENARIO_PATH)` 抛 `ValueError`（消息点名 sha 不符），`analyze_run(run, truth, None, UNTETHERED_PATH)` 通过且输出含所用场景的 sha 与 manifest 的 `effective_scenario_path`。修法由实现角色定；建议比对 `sha256(scenario_path)` 与 `body_planner.scenario_config_sha256` 及 `effective_scenario_sha256`，并把两者写入分析 JSON。既有 `test_synthetic_run_produces_read_outs` 的手写 manifest 可随之改用同一生产路径。

#### R1-3 闭集外围栏界值的 float32/float64 接受域（`ScenarioConfig.cs::GeofenceBound/NormalizeGeofence` 与 `scenario_tether.py::_number/parse_geofence`，Part T）

- 事实（Python 探针 + C# 读码）：`max_x = 1e39` → Python（float64）接受、Unity（`(float)` 溢出 → `must be finite`）拒绝；`min_x = 132.000001`（home x = 132）→ Python 拒绝「不含 home」、Unity float32 舍入为 `132.0` 后接受；`132.00001` 两侧均拒绝。交接「已知限制 3」只披露前者。
- 两个方向都不产生不安全运行：Python 拒绝 → `standoff` 构造器拒绝、无 run；Unity 拒绝 → 无 Play。AC-1 只约束闭集夹具（已成立）；仓库内无此类文件，提案未点名该触发状态，生产入口不能从已归档工件产生 → 不可达边界，`SCOPE_GAP`，非阻断，路由接受角色（记债或裁定不记）。若日后要求两侧同表，可在 Python 侧按 float32 舍入后再做 `min<max`/含 home 判定并拒绝 `|v| > float32 max`。

### §4 UNITY_NA

本项不申请 `UNITY_NA`（提案 §7：两部分都改变运行时行为）；复核**附议「不适用 `UNITY_NA`」**。AC-21/AC-23 维持 `NOT_RUN`，本轮不给 Unity verdict；`R1@K2` 通过前不得放行 Play。

### §5 非 finding 观察（不阻断）

- **T-1 / 已知限制 1–2**：`[NonSerialized] geofence_xz_m` 使 `JsonUtility.ToJson(ScenarioConfig)` 不写围栏。grep `Assets/` 全部 `ToJson` 调用均为其他文档类型；`TetheredScenarioBootstrap.Config` 是 `{ get; private set; }` 属性（Unity 不序列化）；原始 `JsonUtility.FromJson<ScenarioConfig>` 的非测试调用只有 `Editor/SceneCorridorEvidenceGenerator.cs`（读旧缺省，有缆无围栏）。无可达路径，不列 finding；若将来出现「有缆 + 围栏」配置的往返需求，须另立合同（同交接披露）。
- **T-2**：`JsonText` 读取器与 Python `json` 在闭集内一致；闭集外差异（未转义控制字符不拒绝、`﻿` 视作空白、非 §3.1 键的字面量不做词法判定）要么随后被 `JsonUtility` 处理、要么不影响 §3.1 两键裁决，不构成缺陷。
- **P-3 量源**：`analyze_run` 的 T 行读数取评估器 sidecar `m3_body_truth.jsonl`（`body_world_*`、`applied_velocity_*`、`gimbal_saturated`、`tether_saturated`），而 AC-23 写「已发布平台量」。核实：SensorCamera `localPosition = Vector3.zero` → 帧元数据 `camera_position_world_m` 与 sidecar `body_world_*` 同源同值；两处 `tether_saturated`/`gimbal_saturated` 读同一 `Drone`/`Gimbal` 对象；run log `frames.jsonl` 不记平台位置，保留帧只有 128，sidecar 是全程唯一来源；`M3BodyTruthAllowed` 不限场景，untethered Play 会写出。接受角色在 AC-23 核对时宜在 play.md 注明该来源并抽查保留帧元数据与 sidecar 同帧一致；不改变读数。
- R1-1 的运行时表现：`_body_step` 行表第 7 行把异常转为 hold `planner_exception`，安全上 fail-closed；修复后该帧应回到 `hold_estimate_uncertain`。
- 回放 C3 的 H5 = 0.0977 贴近 0.10 上限、E2 下 24 次起停/圈，交接已如实披露；选择规则预注册、工具执行，不是 finding。
- IR-1…IR-9、IR-11、IR-12 逐条与代码核对一致（IR-2 `BODY_OUTSIDE_TOLERANCE_M = 1e-3`、IR-3 `BOUNDARY_INSET_M = 1e-9`/`REACH_TOLERANCE_M = 1e-6`、IR-4 兜底修饰只来自第 5 步、IR-7 `PLANT_SUBSTEPS_PER_FRAME = 10`/帧 0 hold/`GIMBAL_SATURATION_DEADBAND_DEG = 0.1`、IR-12 同实例连续调用）；IR-10/IR-13 已撤回且代码中无残留（`IsUnsetGeofence` 不存在）。

### §6 Verdict

Verdict: REWORK_REQUIRED

`R1@K2` 第 1 次 `REWORK_REQUIRED`（未触发 COORD-009 (c) 冻结）。阻断：R1-1（CLASS_2，`BC-11`）、R1-2（CLASS_2，`IN_SCOPE_NO_BC`），直接交回实现角色；返工只回 Part P 文件（`controller/standoff_planner.py`、`tools/frame_follow_replay.py` 与对应测试），Part T 本轮无阻断。修复后**直接回复核 `R2@K2`，不经核对轮**；R2 对两条阻断 finding 以 `git revert -n <fix>` 做修前红/修后绿。R1-3 `SCOPE_GAP` 非阻断，路由接受角色。无 `RED_LINE`；本轮无 `上轮漏检`，不写 `blocks_consuming_gate`。参数、预注册规则、回放选参（C3）、信封与 Play 操作单不因本轮改动；`passed_candidate` 写出前 Play 不得放行。Overall 与 Lifecycle 由接受角色维护。

边界自查：本会话未修改任何实现文件；主工作树只写本文件与状态板。副本内只写 `Logs/`（Unity 产物）与 `Library/` 副本（生成物），`git status --porcelain` 为空，副本收工删除。

## R2@K2（2026-10-01）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-FRAME-001-R2@K2-20261001T190210Z-8c28`，`requested.round = R2@K2`）。增量轮：先读 R1@K2 全部轮次；新阻断只来自修复触及行上的 CLASS_1/2、旧 finding 闭合失败、`RED_LINE`、未改动行上标 `上轮漏检` 的 CLASS_1。零消耗：零 scenario/session/run ID、零 Unity Play、零 batchmode、零付费 API/GPU/VLM、零下载/安装/远端。

### §0 候选、基线与开轮资格

- `round_candidate: ce7568e3447bb5f16a016f3b5c83b8f8737169a3`（= 上一实现派发 `R1@K2返工` 的 `finished.candidate`；主树 HEAD 23ec1f4 相对候选只多 supervisor 派发登记提交，`Assets/ controller/ config/ tools/ tests/` 零差异）。
- **修复触及行**（`git diff c715886..ce7568e`，上一复核轮 §0 `round_candidate`）：17 路径。PLAY_GOVERNING 6 路径全属 §4.1 Part P：`controller/standoff_planner.py`（+4/−1，只 `_position_sigma`）、`controller/track_loop.py`（`-U0` 三个 hunk 1520/1527/1541 全在 `_build_standoff_runtime` 内）、`tools/frame_follow_replay.py`、`tests/{test_standoff_planner,test_track_loop,test_frame_follow_replay}.py`；`Assets/ ProjectSettings/ Packages/ config/` 零差异；`docs/evidence/P1-ENG-FRAME-001-replay.{json,md}`、`config/p1-eng-frame-001-body.json`、操作单、消耗账本零差异。其余 11 路径为文档：本文件（R1）、提案「待裁定」（接受角色）、`docs/implementation-status.md` R1-3 账本行（接受角色）、交接与测试日志、状态板、`docs/authorizations.md`、派发日志、`docs/roles/supervisor.md`、`docs/workflow-changelog.md`、`docs/evidence/COORD-015-codex-launch-form.md`（supervisor/协调批次），非实现角色改动。
- **全量 diff**（相对上一通过候选：本文件此前无 `passed_candidate`，基线仍为交接文件解析块的 `$BASE` = `9417656`）：32 路径 = R1 的 27 + 上述 5 份文档；实现文件集合与 R1 相同，仍 ⊆ §4.1（AC-25 成立）。
- 提交拆分核实：回归用例 `67d3da9` 只含 3 个 `tests/` 文件，先于修复 `2da7cf2`（只含 `controller/standoff_planner.py`、`controller/track_loop.py`、`tools/frame_follow_replay.py`）；`git revert -n 2da7cf2` 只撤代码、保留新测试。
- 开轮资格：PLAY_GOVERNING 非空 → 开轮。停点自证四项成立：帧/命令协议文件不在 diff 内；全套已跑并提交（`docs/evidence/P1-ENG-FRAME-001-tests.log`：`Ran 2061 tests`、`FAILED (failures=4, errors=9, skipped=19)`，13 条 FAIL/ERROR 逐名等于 R1 §0 所列基线集合）；无未修复 Unity 失败（本轮未改 C#，Edit Mode 不重跑的依据成立）；候选已提交推送、状态板与交接已更新。不判 `REVIEW_BLOCKED`。
- 副本 `.claude/worktrees/review-P1-ENG-FRAME-001`（detach 于候选），测试树哈希 `HEAD:tests = b6badad8f97946df65106157225060124a57d1b0`；解释器 `.venv-yoloe/bin/python`（3.12，只读）。
- focused 重跑（副本内，`-m unittest discover -s tests -p <x>.py`，输出写会话暂存目录，只回显摘要）：`test_standoff_planner` 34 OK（22.0 s）；`test_frame_follow_replay` 16 OK；`test_track_loop` 27 → 1 败 = 基线既有 `test_cli_runs_pinned_csrt_to_a_versioned_summary`（本机 cv2 无 `TrackerCSRT_create`）+ 1 skipped；`test_frame_tether_switch` 18 OK；`test_track_experiment` 7 OK。与交接「修复后 focused」逐项相同。
- 回放复算：`tools/frame_follow_replay.py --check` 副本内全网格重跑 → `replay evidence matches`（82 s）。R1-1 的 `hypot` 改动未改变任何回放决策；选中项仍 C3，证据与配置 sha 不变（AC-19/AC-20 维持）。

### §1 旧 finding 闭合（修前红/修后绿）

副本内 `git revert -n 2da7cf2`（撤回三个代码文件）→ 跑具名回归 → `git checkout ce7568e -- controller tools` 恢复（`git status --porcelain` 为空）→ 重跑：

| Finding | 具名回归（`-k` 选取） | 修前（revert） | 修后 | 结论 |
|---|---|---|---|---|
| R1-1（CLASS_2，`BC-11`） | `StandoffContractTests.test_large_finite_covariance_holds_without_raising`（新）+ 扩域 `test_finite_inputs_never_raise_and_keep_contract_fields` | `Ran 3`（同组含 AC-22 静态用例）`FAILED (failures=1, errors=10)`：10 处 `OverflowError: (34, 'Result too large')`（9 个对角子用例 + 随机用例） | `Ran 3` OK | **闭合** |
| R1-2（CLASS_2，`IN_SCOPE_NO_BC`） | `AnalyzeRunTests.test_analyze_run_refuses_a_scenario_that_differs_from_the_manifest`（新） | `Ran 2` `FAILED (failures=1)`：`ValueError not raised` | `Ran 2` OK | **闭合** |
| AC-22 修订 1（接受角色 `CLARIFY`） | `StandoffWiringTests.test_standoff_ground_plane_is_explicit_finite_and_route_independent`（新）+ 改预期的 `test_standoff_scenario_id_and_ground_plane_fail_closed` + `TruthIsolationTests.test_standoff_construction_path_reads_no_route_or_evaluator_output`（新，静态） | `Ran 5` `FAILED (failures=2, errors=2)`：0.0 → `ValueError: ground_plane_y_m does not match the frozen scenario route height (route_world_m[0].y = 0.2)`、`None` → `TypeError`、NaN 两处 `ValueError not raised`；静态用例 `_build_standoff_runtime names 'route'` | `Ran 5` OK；静态用例过 | **成立** |

workflow §4.4 四条闭合条件：(1) R1-2 夹具由生产路径产出——manifest 身份为 `controller.track_loop._build_body_runtime(FRAME, UNTETHERED, "standoff", scenario_id=…, ground_plane_y_m=0.2, runtime=<临时>)` 第 4 返回值，经 `controller.run_log.RunLogger(runtime, run_id, manifest=…)` 写出（`run_directory = runtime/runs/<run_id>`、`_atomic_json(manifest.json)`、`append` 写 `frames.jsonl`，与 `track_loop.py:1928` 同一写盘类；`manifest["body_planner"] = dict(body_identity)` 在 `_manifest()` 第 1377 行，键位与 `analyze_run` 读取处一致）；truth 旁车合成（Unity 写出、Python 无生产写盘函数，非被测状态）——成立。(2) 本轮红绿核实——成立。(3) 修复未触及 Play 治理门文件（`analyze_m3_body.py`、`preflight_reanchor_env.py`、`controller/run_log.py` 不在 diff 内）。(4) 无 `NOT_MECHANIZABLE`。

### §2 修复触及行逐文件核对

| 文件 | 核对 |
|---|---|
| `controller/standoff_planner.py::_position_sigma` | 唯一改动：`math.sqrt((0.5(a−d))² + b²)` → `math.hypot(0.5(a−d), b)`；前置有限检查、`isfinite(largest)` → `None`、`sqrt(max(0, largest))` 不变。`math.hypot` 溢出返回 `inf` 不抛（副本探针：`hypot(fm, fm) = inf`、`hypot(0.5·fm, 0.9·fm) = inf`，`fm = sys.float_info.max`），`inf` 经既有有限检查 → `None` → `hold_estimate_uncertain`。生产 `build_standoff_planner` 三场景（untethered / default / F-both）× 8 个极端协方差探针（`a=fm,d=1,b=0.9fm` 使 hypot 溢出；`fm/fm`、`fm/−fm`、`1e308/−1e308/1e308`、`0.6fm` 全满、`5e-324`、`1e155`、`−fm`）全部 `decide` 不抛、`mode = hold`、`vy = 0`、`expires = 0.4`，有效大方差全为 `hold_estimate_uncertain`。估计闸阈值（`sigma > band_w_m`）、`decide` 的异常处理与其余步骤未改。 |
| `controller/track_loop.py::_build_standoff_runtime` | ① 路线读取/遍历/高度校验及其拒绝消息整段删除（hunk 3）；② 新增 `None`/bool 拒绝 + `_finite()` 包装（`TypeError`/`ValueError` 统一转 `ValueError`，消息含 `ground_plane_y_m`）；docstring 改为「整份场景文档只作配置同一性绑定、标定只来自显式参数」。场景 schema、`scenario_id`、`effective_document != scenario` 逐值一致性、`sha256_file` 两份身份、`safety_bounds` 均保留（AC-18/AC-29 不受影响）。`_build_body_runtime` 的 `standoff` 分派两行与冻结 hold/threshold 路径（含旧路线检查，现行 1673–1682 行）零改动。CLI 既有校验（`required` 含 `ground_plane_y_m` → `parser.error`；`_finite(args.ground_plane_y_m)` 非有限 → `parser.error`）未改，新用例 4 条 CLI 子用例退出码 2 独立通过。`_finite` 对数值字符串（如 `"0.2"`）会接受：只在直接构造可达，CLI `type=float` 已转数值，且修订 1 ② 的拒绝闭集为缺失/非有限，不构成 finding。 |
| `tools/frame_follow_replay.py` | `MANIFEST_SCENARIO_KEYS` 四键 = `_build_standoff_runtime` 身份的四键（`scenario_config_path/sha256`、`effective_scenario_path/sha256`）；`_manifest_scenario_binding` 对缺 `body_planner`、非 Mapping、任一键缺失或空串 fail-closed；`analyze_run` 先读 manifest，`--scenario` 按字节算 sha256，须同时等于两个 manifest sha，几何从同一份已核字节解析（不二次读盘）；输出新增 `scenario_binding`（所用路径、sha、manifest 两条来源路径）。来源路径只记录不比对：§3.11 入口 8 要求「读」sha 与来源路径，字节 sha 已承担绑定，manifest 记的是 Play 主机绝对路径、跨机必然不同——**附议**交接「已知限制 1」，不列 finding。`hashlib`/`Mapping` 为既有导入；`--scenario` 帮助文字与模块文档串同步。 |
| `tests/test_standoff_planner.py` | `_estimate` 增 `variance_z`（缺省同旧）、`_position_covariance` helper；新用例 3 场景 × 4 协方差 = 12 子用例；随机用例方差集含 1e200、x/z 独立抽取；静态用例以 `inspect.getsource` 只取 `_build_standoff_runtime`/`build_standoff_planner`/`_estimator_from_body_config` 钉 `route`/`target`/`metrics.json`/`m3_body_truth`/`truth`/`evaluator` 六个 token，不扫旧模块（符合裁定「不迫使修改冻结路径」）。 |
| `tests/test_track_loop.py` | 原用例预期 0.0 → NaN（注释说明理由）；新用例以真实 `_build_body_runtime` 对 0.2/0.0 构造成功（`planner.name`、`expires = 0.4`、`identity["effective_scenario_path"]`），对 `None`/NaN/±inf `assertRaisesRegex(ValueError, "ground_plane_y_m")`，CLI 缺参/`=nan`/`=inf`/`=-inf` 退出码 2 且 stderr 点名参数，临时 runtime 前后为空。`io`/`redirect_stderr`/`tempfile`/`main` 为既有导入。 |
| `tests/test_frame_follow_replay.py` | `AnalyzeRunTests` 改为生产路径夹具（§1 (1)）；`test_synthetic_run_produces_read_outs` 读数断言逐字不变（抽为 `_assert_read_outs`）；无 `body_planner` 的生产 manifest 拒绝子断言。 |

修复触及行上无新 CLASS_1/2，无 `RED_LINE`；本轮无 `上轮漏检`，不写 `blocks_consuming_gate`。

### §3 AC 更新（只列本轮有变化或被触及的条目，其余维持 R1 §2 结论）

| AC | 结论 | 依据 |
|---|---|---|
| AC-11 | **成立**（R1 不成立 → 本轮闭合） | R1-1 红绿 + §2 探针；纯度/三种 hold/重放/`vy = 0`/0.4 s/只 import 契约类型维持 |
| AC-22（含修订 1） | **成立** | 三条红绿；副本重跑 `grep -nE 'metrics.json|m3_body_truth|route_world_m' controller/standoff_planner.py controller/scenario_tether.py` 无命中；新构造路径静态用例过；冻结旧路径未动（裁定「旧路径边界」） |
| AC-18 / AC-29 | 维持成立 | 场景逐值一致性与身份四键保留；`StandoffWiringTests` 5 项 OK |
| AC-19 / AC-20 | 维持成立 | `--check` 一致；回放证据与 FRAME 配置零差异、选参 C3 |
| AC-24 | 成立 | `-tests.log` 2061 项、13 项逐名 = 基线、新增失败 0；Edit Mode 不重跑依据成立（`Assets/ ProjectSettings/ Packages/` 零差异，现行 284/284 证据含 R1 副本独立重跑） |
| AC-25 | 成立 | 32 路径，实现文件集合同 R1，均在 §4.1 |
| AC-21 / AC-23 | `NOT_RUN`（如实） | Unity 阶段；R1-2 已闭合，不再是 Play 前的读数工具缺口 |

### §4 UNITY_NA

同 R1：本项不申请 `UNITY_NA`（两部分都改变运行时行为）；复核**附议「不适用 `UNITY_NA`」**。AC-21/AC-23 维持 `NOT_RUN`，本轮不给 Unity verdict；Play 放行由接受角色按 workflow §4.5 另决，本轮不放行。

### §5 非 finding 观察（不阻断）

- `analyze_run` 要求 `--scenario` 的 sha **同时**等于 manifest 的 `scenario_config_sha256` 与 `effective_scenario_sha256`。若 Play 时存在与 body 场景逐值相等但字节不同的 `runtime/scenario_config.json` 覆盖，构造器接受（逐值比对）而两 sha 不等，分析对任何文件都拒绝（fail-closed，消息列出两 sha 与来源路径，无错读数）。AC-23 与操作单要求 Play 期间覆盖缺席；当前 ACQ 残留覆盖为旧缺省副本（逐值不等 → 构造拒绝、无 run）→ 不可达，不列 finding。接受角色核 AC-23 时沿用「覆盖缺席」核对即可。
- 负（无效）方差（如 `a = −fm`）经 `max(0, largest)` 得 σ = 0，不触发估计闸（探针 `in_band_hold`）：既有行为、本轮未触及；AC-11 只约束不抛异常，契约 v1 未定义无效协方差语义；不列 finding。
- `hypot` 与旧式在 b ≠ 0 时可能有末位舍入差（交接「已知限制 2」）：回放全网格 `--check` 逐字节一致，决策无变化。
- R1-3 `SCOPE_GAP` 已由接受角色记入 `docs/implementation-status.md`「范围外已知缺陷」（`OPEN`），路由完成；本轮不重开、不签 release（原无 block）。

### §6 Verdict

Verdict: PASS_WITH_NOTES

passed_candidate: ce7568e3447bb5f16a016f3b5c83b8f8737169a3

R1-1、R1-2 闭合，AC-22 修订 1 成立；修复触及行无 CLASS_1/2，无 `RED_LINE`，无 `blocks_consuming_gate`，`REWORK_REQUIRED` 计数停在 1/2。`K2` 停点独立复核通过，交接受角色消费（维护 Overall/Lifecycle、决定 AC-21/AC-23 的 Play 放行）；本轮不放行 Play、零消耗。R1-3 `SCOPE_GAP`/`OPEN` 债不变；参数、预注册规则、回放选参（C3）、信封与操作单不因本轮改动。

边界自查：本会话未修改任何实现文件；主工作树只写本文件与状态板。副本内只做 `git revert -n` 后立即 `git checkout` 恢复（收工前 `git status --porcelain` 为空），探针脚本与测试输出在会话暂存目录、不入库；副本已删除。

## R3@K2（2026-10-02，R7字段路径窄修）

角色：独立 review，新鲜上下文子代理；依据账本 2026-10-01「用户允许开始三项补测前置准备」调用，不是 supervisor 派发，无 Dispatch-Id。只在一次性 detached worktree 阅读实现和运行无模型 focused；主树只写本复核文件与状态板。接受侧 C3 是待核实主张，不代替本轮判断。

### §0 候选、完整范围与开轮资格

round_candidate: 7d69a1b0f797cb551ac9a367a27d1b2030931f19

最近通过候选及上一复核轮候选均从本文件 R2 的机读行解析为 `ce7568e3447bb5f16a016f3b5c83b8f8737169a3`。两个基线相同；完整 diff 共 **44 路径**（C3 记录产生前是43，新增 C3-inspection.json），先读文件清单再分块逐文件读完整 diff。新大 JSON 逐字段全部阅读，机器日志含完整栈；未把协调变更或原 Unity 记录排除。候选开工已提交/推送，主树干净。PLAY_GOVERNING 的工具、测试和操作单差异非空，具备开轮资格；本轮不是因轮号3就触发冻结终局，此前 REWORK_REQUIRED 只有1次。

完整文件清单（相对最近通过候选）：

- `.agents/skills/chore/SKILL.md`
- `.agents/skills/chore/agents/openai.yaml`
- `.agents/skills/fable/SKILL.md`
- `.agents/skills/fable/agents/openai.yaml`
- `.agents/skills/implement/SKILL.md`
- `.agents/skills/implement/agents/openai.yaml`
- `.agents/skills/review/SKILL.md`
- `.agents/skills/review/agents/openai.yaml`
- `.agents/skills/supervisor/SKILL.md`
- `.agents/skills/supervisor/agents/openai.yaml`
- `docs/authorizations.md`
- `docs/current-status.md`
- `docs/evidence/P1-ENG-FRAME-001-C3-inspection.json`
- `docs/evidence/P1-ENG-FRAME-001-R7-acceptance-inspection.json`
- `docs/evidence/P1-ENG-FRAME-001-R7-acceptance-inspection.md`
- `docs/evidence/P1-ENG-FRAME-001-R7-environment.log`
- `docs/evidence/P1-ENG-FRAME-001-R7-full-preflight.json`
- `docs/evidence/P1-ENG-FRAME-001-R7-full-suite-handoff.md`
- `docs/evidence/P1-ENG-FRAME-001-R7-full-suite-preparation.md`
- `docs/evidence/P1-ENG-FRAME-001-R7-full-suite-result.json`
- `docs/evidence/P1-ENG-FRAME-001-R7-full-suite.log`
- `docs/evidence/P1-ENG-FRAME-001-R7-green-tests.log`
- `docs/evidence/P1-ENG-FRAME-001-R7-implementation.md`
- `docs/evidence/P1-ENG-FRAME-001-R7-recompute.json`
- `docs/evidence/P1-ENG-FRAME-001-R7-red-tests.log`
- `docs/evidence/P1-ENG-FRAME-001-play-ops.md`
- `docs/evidence/P1-ENG-FRAME-001-play-result.json`
- `docs/evidence/P1-ENG-FRAME-001-play.md`
- `docs/evidence/P1-ENG-FRAME-001-play2-paused.json`
- `docs/evidence/P1-ENG-FRAME-001-preflight.json`
- `docs/evidence/P1-ENG-FRAME-001-retry-preflight.json`
- `docs/evidence/P1-ENG-FRAME-001-supplement-ops.md`
- `docs/evidence/P1-ENG-FRAME-001-supplement-preparation.json`
- `docs/evidence/P1-ENG-FRAME-001-unpaused-play.json`
- `docs/evidence/supervisor-dispatch.jsonl`
- `docs/implementation-status.md`
- `docs/phase1-single-drone-design.md`
- `docs/proposals/P1-ENG-FRAME-001-tracking-framing-and-body-follow-survey.md`
- `docs/reviews/P1-ENG-FRAME-001.md`
- `docs/unity-test-log.md`
- `docs/workflow-changelog.md`
- `tests/fixtures/frame_follow_metrics_unity.json`
- `tests/test_frame_follow_replay.py`
- `tools/frame_follow_replay.py`

另完整读取 R1/R2 两轮、已接受提案全29 AC及 C3、旧 K2-handoff 全文、工程继承清单与范围外账本、设计相关协议/控制/标定/指标章节，以及新旧证据直接指向的代码。未触及旧代码不开展新的泛化复核。

**workflow §4.3.1 四项稳定条件独立判断：成立，准予 R3，不判 REVIEW_BLOCKED。**

1. 范围/接口冻结：运行工具仅 `analyze_run` 增加3行 aggregate 回退；controller、Assets、config、ProjectSettings、Packages、帧/命令协议与回放选参均零 diff。允许的必要回归随同旧数据量源，不增加运行行为或参数。
2. 相称测试成立但绝非全绿：具名一次全套原日志为2064项、4 FAIL/21 ERROR/19 skip。独立解析旧/新日志，旧13逐名保留，新增12、解决0；两日志 hash 匹配 result。逐条原栈及直接 HTTP server/test setup 显示新增12均在 `server_bind/socket.bind` 抛 `PermissionError: [Errno 1] Operation not permitted`，未到 HTTP 行为断言。它们是未改动 `test_eng_acq_operator_web.HttpBoundaryTests` 3项及 `test_language_selector.HttpAdapterTests` 9项；相关服务不调用本次 R7 分支。AC-24 要求执行一次全套并分列既有/新增，本次做到了；新增12只能记环境限制/行为未验证。窄修真实量源和兼容路径由一次独立 focused19项全过及双端点复算直接覆盖，故不要求无关受限 HTTP 行为再跑后才开轮。
3. 无已知未修复的本候选 Unity 自动失败：Assets/Unity设置零 diff；直接核旧终跑 XML 为284/284且 sha 与原 K2交接吻合（`662a58872840ce058c7e7173affa3a7f3503f0e82c2294ec425465d8265bf70c`），未机械重跑 Unity。原 Play 的 R7 缺口已由下述原件复算验证修复；用户机身目检与完整按钮墙钟仍缺证，是尚未放行的后续补测义务，不能声称 Unity PASS。
4. 候选/交接/风险齐：R7-full-suite-handoff 的四项具名自证已逐项核实，模型成功构造数未知、测试按授权上界记账、12项限制、旧原件/端点及目检/墙钟未闭均披露，C3交接清楚；本轮更新状态板交接受消费。

测试副本 `/private/tmp/review-frame-r3`，detach 于本轮候选。测试树 `HEAD:tests = c2bde857843da0badbed4c73ec878adabbf5820f`。独立核全套记录的93个测试文件与6个受保护路径全部 sha 匹配候选；工作副本测试前后无跟踪改动。

### §1 独立验证与修复触及行

focused仅一次，在副本以主树既有解释器只读执行：

```text
PYTHONPATH=tests ~/TetheredDroneTracking/.venv-yoloe/bin/python -m unittest discover -s tests -p test_frame_follow_replay.py
Ran 19 tests in 0.644s
OK
```

完整输出写会话临时文件，sha256 `accf85a9709562f08e7504501dca73ac465dde162adfc4aa2401909f44cecd1e`。未重跑全套、12条HTTP、Unity或模型预检；无阻断 finding 要求新增红绿。实现者既有 R7 红1败/绿5项原日志已全文读取，本轮19项包含该5项。

| 触及路径 / C3关注项 | 独立结论 |
|---|---|
| tools/frame_follow_replay.py / F-1 | 先保留顶层、summary的键存在优先级（含null/zero），仅两层均缺键时取 aggregate.c_track；未取 given_geom、未推断 metrics.final；未传metrics仍null。`_rounded`六位口径不变，读取仅在离线工具；无控制真值泄漏、帧/坐标/时间/原子写入或并发语义变化。完整函数和 CLI 输出路径已读。 |
| tests/test_frame_follow_replay.py及真实fixture / F-1 | 新真实schema用例、9种兼容分支和显式不传metrics用例有效。manifest/frames经 `_build_body_runtime`/`RunLogger` 生产写盘路径生成，直接相关代码已读；truth仍合成，只有metrics字节是真实，不能称整份真实run fixture。Unity `CoverageEvaluator.BuildMetricsDocument` 的 aggregate.c_track分母为safeTotal，given_geom为safeGeometric，两个指标不能互换。 |
| R7-recompute及原play-result / F-2 | 独立校验原run清单138/138文件的size/hash，复算前后都相等；fixture逐字节等于原退出metrics.json。副本代码读取主树保存原件，输出仅写临时目录，两个输出SHA与实现证据逐字相同；原analysis未覆盖。见下表。 |
| 全套/自证 / F-3 | §0给出相称性判断；12项行为未验证，旧13项仍失败，不以本轮通过洗掉这些负结果。资源原记录区分静态上界与未知实际成功次数；不推断模型全成功或外网流量为零。 |
| 全候选/协调 / F-4 | 44路径全部核读并按git历史与真实账本归属。完整集合按§4.1机械比较并非子集，此事实保留；已采纳IR-9的流程文件读法不等于自动豁免任意代码。10-01两条直接协调授权覆盖技能迁移及相应流程记录，窄修授权明确含必要focused回归，真实metrics fixture恰服务已授权R7回归；未发现未经授权的实现扩范围。C3误把迁移归到COORD-016，记R3-1纠正文档出处；不把既有授权撤销或擅自改AC。 |
| 操作单/Unity / F-5 | play-ops及supplement-ops、完整Unity增量与前置机器记录相符，三body参数、冻结配置、覆盖缺席保持。历史首轮/第二次放行不等于新工具补测放行。额外Play1/加载1/run1未消费，补测480s授权只本次；465.024116s首末帧跨度不是完整按钮墙钟。用户“consle无错误，但是我看不见无人机啊”不构成跟随/起停目检通过。 |

| 独立复算端点 | R7 | 输出 sha256 | 与原退出analysis比较 |
|---|---|---|---|
| 明确传入原退出 metrics.json | 0.91899 | 368aadbc773618075737e253d4039ffd469bf654f1726ab677c390528193ac01 | 仅 R7_c_track 改变 |
| 明确传入 metrics.final.json（tracker自然结束快照） | 0.99495 | 3aa1989c6bfd636229d7e49116011f186d1a8ab5bccb8505fdd25f7738e0a19b | 仅 R7_c_track 改变；其余读数仍使用相同原旁车窗口，不冒充结束时截短全套读数 |

旧原件、冻结配置、回放证据和两端点窗口均未混写；这些复算不是新Play或新正式ID。

### §2 全29项AC及旧finding承接

| AC | 本轮判断 |
|---|---|
| AC-1…10、27…29（§T共13项） | 维持R2已通过范围：对应Unity/Python实现、冻结配置与协议均未动；沿完整旧K2 §T/原XML/R1/R2证据，不声称新跑。R1-3闭集外数值差异仍 SCOPE_GAP/OPEN。 |
| AC-11…20（§P共10项） | 维持R2：规划器/估计闸/后处理/接线零diff；R1-1闭合有效。离线镜像、60格选参及FRAME参数未变，本轮focused包含镜像/冻结证据检查；不重新执行全网格。操作单的授权/前置更新不改参数或控制协议。 |
| AC-21 | R7输出缺口闭合于工具与旧数据复算；整体仍未闭，人眼跟随/起停及完整按钮墙钟不由本轮代签。 |
| AC-22 | 新三行仅离线分析，控制器零diff，原修订1及R2证明有效。 |
| AC-23 | 原Play已接受的安全/来源证据保留；本轮复算安全读数逐值不变，原128组同帧平台记录全部已读。不新增Unity verdict。 |
| AC-24 | 一次全套与逐名差异记录成立；明确保留13旧失败和12新增环境ERROR。相称性理由见§0。 |
| AC-25 | 完整集合字面非§4.1子集；逐项授权/必要流程归属核查未发现越权实现，不能将协调文件从全量审查中删除，也不把文字改为字面成立。消费时按本轮§1与R3-1准确说明。 |
| AC-26 | 旧/新逐AC自证与稳定条件具名来源齐全，独立核实后可开轮。 |

R1-1、R1-2已由R2红绿闭合；本轮未重开、不伪造新闭合。R1-3仍由原范围外账本承接，不修不关；无未改动行上的新CLASS_2，故无新增 blocks_consuming_gate 或 releases_consuming_gate。

### §3 Finding（非阻断）

| ID | 级别 | 依据 | 位置与影响 | 处置 |
|---|---|---|---|---|
| R3-1 | CLASS_3 | 上游漏检 | 提案 Contract conformance C3 的AC-25行把十个技能/映射的授权写成“账本COORD-016迁移授权”。实际为账本10-01两条用户直接协调授权，两个迁移提交各自提交信息也引用该条目；错误出处降低审计可追溯性，但授权本身存在、实现范围未因此扩大。 | 不阻断。由拥有提案写权限的接受角色在下一提交按下列逐字替换，不回交实现改提案。 |

逐字替换补丁（只在提案C3 AC-25行匹配一次；复核不改提案）：

```diff
-协调路径可沿账本COORD-016迁移授权及git归属
+协调路径可沿账本2026-10-01「全局 — 用户指示：复制 Claude 的 supervisor、implement、review、chore 到 Codex」及「全局 — 用户指示：复制 Claude 构思角色到 Codex」两条直接协调授权与git归属
```

迁移归属：git动态核得四角色迁移与构思迁移各独立提交，仅新增10个技能/映射及授权/状态/变更记录；对应提交信息明确引用上述授权。review/implement入口保留独立性与角色边界，没有更改全局模型池/无人值守派发规则。其他授权/dispatch变更为旧R2核销、接受消费和后续Play/补测逐次授权记录；不是当前R3派发。

### §4 UNITY_NA、verdict与交接

本项不适用 UNITY_NA，复核继续附议“不适用”；不签整体Unity PASS或DONE。

Verdict: PASS_WITH_NOTES

passed_candidate: 7d69a1b0f797cb551ac9a367a27d1b2030931f19

本轮R7实现无新CLASS_1/2、无RED_LINE；R3-1文档出处按CLASS_3随下一提交修正。REWORK_REQUIRED计数仍1，C核对退回仍1/1，不混计。本轮通过限K2候选复核，交Acceptance消费并按workflow §4.5核主机/候选差异与预算后裁定补测；未放行Play。Overall/Lifecycle维持已有值，由接受角色维护。

资源：一次无模型focused19项、只读原件hash/双端点分析；正式scenario/session/run ID、Unity/Play/batchmode、Nano/YOLO/DINO/CSRT加载、GPU/API、下载/安装均0。没有重新请求/执行全套提权或HTTP探测。本轮测试输出及探针仅在临时目录，不入证据树；一次性副本收工删除，主树只改本文件与状态板。
