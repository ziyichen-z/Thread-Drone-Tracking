# P1-ENG-FRAME-001 K2 候选交接（Implementation，Claude Opus 子代理，2026-09-30；K2补跑、C1@K2返工、R1@K2返工 2026-10-01）

工作项：`P1-ENG-FRAME-001`（`Workflow: engineering-v1`，D2 接受裁定生效；单候选停点 `K2`）。
合同：`docs/proposals/P1-ENG-FRAME-001-tracking-framing-and-body-follow-survey.md`（§2–§6、§9.1、「D2 接受裁定」）。
执行信封：`docs/authorizations.md` 2026-09-30「P1-ENG-FRAME-001 — 用户答复 §10 四条…并按申请签发 §5 预算信封」，
提案 §5「已签执行合同」实现至 K2 列。派发：Dispatch-Id `P1-ENG-FRAME-001-K2-20260930T235000Z-b5d6`；
`K2补跑` Dispatch-Id `P1-ENG-FRAME-001-K2补跑-20261001T155648Z-59ca`（本机卡死重启，记 `aborted(runner_gone)`，未提交）
→ 续接 `P1-ENG-FRAME-001-K2补跑-20261001T162718Z-3b82`（K2补跑 全部提交）；
`C1@K2返工` Dispatch-Id `P1-ENG-FRAME-001-C1@K2返工-20261001T165209Z-3fae`（见下「C1@K2返工」节）；
`R1@K2返工` Dispatch-Id `P1-ENG-FRAME-001-R1@K2返工-20261001T175900Z-f1e4`（见下「R1@K2返工」节）。

**派生标识一律运行时解析（不写死）：**

```bash
# K2 基线 = 本工作项实现角色开工提交的父提交
BASE=$(git rev-parse "$(git log --format=%H --grep='^P1-ENG-FRAME-001 K2 开工')^")
# 候选 = 本文件最后一次提交所在的 main 提交
CAND=$(git log -1 --format=%H -- docs/evidence/P1-ENG-FRAME-001-K2-handoff.md)
git diff --name-only "$BASE".."$CAND"      # 完整候选文件集（AC-25）
git diff "$BASE".."$CAND"                   # 完整候选 diff（C1@K2 输入）
# K2 首交候选（K2补跑 修复前）与 K2补跑 修复提交（Edit Mode 终跑所在 HEAD）
PREV=$(git log -1 --format=%H --grep='^P1-ENG-FRAME-001 K2 候选自证与交接')
FIX=$(git log -1 --format=%H --grep='^P1-ENG-FRAME-001 K2补跑 修复')
git diff "$PREV".."$FIX" -- Assets controller config tools tests docs/evidence/P1-ENG-FRAME-001-replay.json docs/evidence/P1-ENG-FRAME-001-replay.md   # K2补跑 修复增量
# C1@K2 核对时的候选（K2补跑 交接提交）与 C1@K2返工 修复提交（Edit Mode 终跑所在 HEAD）
C1CAND=$(git log -1 --format=%H --grep='^P1-ENG-FRAME-001 K2补跑 自证与交接')
RWFIX=$(git log -1 --format=%H --grep='^P1-ENG-FRAME-001 C1@K2返工 修复')
git diff "$C1CAND".."$CAND" -- Assets controller config tools tests   # C1@K2返工 代码增量（= "$C1CAND".."$RWFIX"）
# R1@K2 复核轮候选（复核文件「R1@K2」节机读行 round_candidate）与 R1@K2返工 修复提交
R1CAND=$(sed -n '/^## R1@K2/,/^## R[2-9]/p' docs/reviews/P1-ENG-FRAME-001.md | grep -m1 -oE 'round_candidate: [0-9a-f]{40}' | cut -d' ' -f2)
R1TEST=$(git log -1 --format=%H --grep='^P1-ENG-FRAME-001 R1@K2返工 回归用例')   # 只含 tests/ 的回归用例提交（先于修复）
R1FIX=$(git log -1 --format=%H --grep='^P1-ENG-FRAME-001 R1@K2返工 修复')        # 只含 controller/、tools/ 的修复提交
git diff "$R1CAND".."$R1FIX" -- Assets controller config tools tests   # R1@K2返工 代码与测试增量（R2 修复触及行基线）
```

**状态（R1@K2返工 后，现行）**：`R1@K2` `REWORK_REQUIRED` 的两条阻断 finding（R1-1 `BC-11`、R1-2 `IN_SCOPE_NO_BC`）与接受角色并入本次返工的
AC-22 修订 1（`CLARIFY`）已只在 §4.1 Part P 文件内修复（下节），各绑具名回归、修复前红、修复后绿；Python 全套 2061 项，失败集合与基线 13 项逐名相同、
新增失败 0；未改 C#（`$R1CAND..$R1FIX` 对 `Assets/` 零差异），Edit Mode 不重跑；回放 `--check` 逐字节一致，选参仍为 C3。直接交 `R2@K2`（不经核对轮）。
R1-3 已由接受角色记 `SCOPE_GAP`/OPEN，本轮未处理。以下「C1@K2返工」及其后各节为此前轮次原记录，受影响条目已就地标注「R1@K2返工」。

**状态（C1@K2返工 后）**：`C1@K2` 首退（AC-1 不满足，IR-10/IR-13 不采纳）的返工要点已在 §4.1 内落实（下节），
AC-1/AC-3/AC-27 重新自证；Edit Mode 全套终跑（代码 = `$RWFIX`）284/284 通过，Python 全套无新增失败；交 `C2@K2`
（本停点 C 退回额度已用 1/1，C2 不再退回、照交复核）。以下「K2补跑」及其后各节为 C1 所核候选的原记录，受影响条目已就地标注。

**状态（K2补跑 后，原记录）**：K2 候选自证齐全，交 `C1@K2`。Unity Edit Mode 全套已在 batchmode 执行：首跑（代码 = `$PREV`）
281 例 278 过 **3 败**——既有用例 `Scene006CandidateProbeEditModeTests.HappyPathBindsReviewedIdentity`、
`SceneAdjustmentConfigTests.CheckedInConfigsCarryTheSameStrictSceneAdjustment` 与本批 `TetheredDronePlantTests.Step_TetheredGoldenVectors`；
三条都归因于本候选、修复均在 §4.1 内，plant 代码与 AC 含义未改（下节）。终跑（代码 = `$FIX`）**282 例全过**（含新增回归用例 1 条）；
修复后 Python 全套无新增失败（§共用「测试」）。K2 首交时 Edit Mode 因用户编辑器占用工程未跑（当时 Status `IMPLEMENTED_AWAITING_EDITMODE`）。

## R1@K2返工：阻断 finding 与 AC-22 修订 1 逐条修复（交 `R2@K2`）

依据：`docs/reviews/P1-ENG-FRAME-001.md`「R1@K2」§3 R1-1、R1-2 与 §6；提案「待裁定」「AC-22 线索裁定」中 **AC-22 修订 1（`CLARIFY`）** 的 ①②③ 与证明闭集。
修改只在 §4.1 Part P 文件内（`git diff --name-only "$R1CAND".."$R1FIX"` 共 6 个路径：`controller/standoff_planner.py`、`controller/track_loop.py`
（只动 `_build_standoff_runtime`）、`tools/frame_follow_replay.py`、`tests/test_standoff_planner.py`、`tests/test_track_loop.py`、`tests/test_frame_follow_replay.py`）；
参数、预注册规则、回放选参（仍为 C3）、FRAME 配置、Play 信封与操作单、Part T 文件、冻结旧 `_build_body_runtime` 的 hold/threshold 路径均未动。
开工基线：派发开始时 HEAD 的 PLAY_GOVERNING 与 `$R1CAND` 零差异（`git diff --name-only "$R1CAND" <开工 HEAD> -- Assets controller config tools tests` 为空）。

| # | 依据 | 修改 | 具名回归（修复前 → 修复后） |
|---|---|---|---|
| R1-1 | 复核 R1-1（CLASS_2，`BC-11`，阻断）：AC-11「有限输入不抛异常」 | `controller/standoff_planner.py::_position_sigma`：2×2 最大特征值的半径项由 `math.sqrt((0.5*(a-d)) ** 2 + b*b)` 改为 `math.hypot(0.5*(a-d), b)`（数值稳定、不因中间平方超出 double 范围抛 `OverflowError`）；结果过大仍是有限大 σ、溢出为 `inf`/`nan` 时由其后既有的有限检查返回 `None`，二者都落入估计闸 `hold_estimate_uncertain`。估计闸阈值、`decide` 的异常处理与其余步骤不变，「有限输入不抛异常」未放宽 | `tests.test_standoff_planner.StandoffContractTests.test_large_finite_covariance_holds_without_raising`（新）：`build_standoff_planner` 生产构造，untethered / default / F-both 三场景 × 协方差 `diag(1e155,1,1,1)`、`diag(1e200,1,1,1)`、`diag(sys.float_info.max,1,1,1)`、对称非对角 1e200 共 12 个子用例，平台在锚点上方 25 m、云台离限位远（无兜底速度）、估计点 10 m 外；断言不抛、`mode = hold`、主标记 `hold_estimate_uncertain`、`vy = 0`、`expires_after_s = 0.4`。修复前 9 个对角子用例 `OverflowError: (34, 'Result too large')`（非对角 3 个修复前即走非有限分支而过，与复核探针一致）→ 修复后全过。`StandoffContractTests.test_finite_inputs_never_raise_and_keep_contract_fields`：方差候选集扩为 `{1e-6, 0.25, 4, 1e6, 1e200}`，x、z 独立抽取（`_estimate` 增可选参数 `variance_z`，缺省同旧）；修复前 `OverflowError` → 修复后过 |
| R1-2 | 复核 R1-2（CLASS_2，`IN_SCOPE_NO_BC`，阻断）：§3.11 入口 8「`--analyze-run` 读 run manifest 的场景 sha 与来源路径」 | `tools/frame_follow_replay.py::analyze_run`：先读 `manifest.json`，取 `body_planner` 的 `scenario_config_path`、`scenario_config_sha256`、`effective_scenario_path`、`effective_scenario_sha256`（缺 `body_planner` 或任一键 → `ValueError`）；`--scenario` 文件按字节算 sha256，须**同时**等于两个 manifest sha，否则 `ValueError`（消息含两侧 sha 与 manifest 的生效来源路径）；几何由同一份已核字节解析；输出新增 `scenario_binding`（所用路径与 sha、manifest 的两条来源路径）。来源路径的处理按复核建议修法：只读出并写入输出、不做字符串相等比对——manifest 记的是 Play 主机上的绝对路径，复核副本或他机重算时路径必然不同而字节相同，绑定由字节 sha 承担。`--scenario` 帮助文字与模块文档串同步一句；操作单命令（`--scenario config/scenario.untethered.json`）不变 | `tests.test_frame_follow_replay.AnalyzeRunTests.test_analyze_run_refuses_a_scenario_that_differs_from_the_manifest`（新）：manifest 身份 = `controller.track_loop._build_body_runtime(FRAME 配置, config/scenario.untethered.json, "standoff", scenario_id="deterministic-loop-untethered", ground_plane_y_m=0.2, runtime=<临时目录>)` 第 4 返回值，经 `controller.run_log.RunLogger(<临时目录>, run_id, manifest={…, "body_planner": identity})` 写出 `manifest.json`，帧记录经 `RunLogger.append` 写出（无手工 mkdir、无手写 manifest）；断言 `config/scenario.default.json` → `ValueError`（消息含 `sha256`），untethered → 通过且 `scenario_binding` 的 sha 等于 manifest 两 sha、两条来源路径等于 manifest；另以无 `body_planner` 的生产 manifest 断言拒绝。修复前 `AssertionError: ValueError not raised` → 修复后过。既有 `test_synthetic_run_produces_read_outs` 改用同一生产路径，读数断言逐字不变（修复前后均过）。评估器 truth 旁车由 Unity 写出、Python 侧无生产写盘函数，仍为合成数据（不是被测状态） |
| AC-22 修订 1 | 提案「待裁定」AC-22 修订 1（`CLARIFY`；解释 AC-22、设计 §3.5/§6，关联 AC-18） | ① `controller/track_loop.py::_build_standoff_runtime` 删除 `target.route_world_m` 的读取、遍历与「标定 = 路线高度」校验及其拒绝消息，docstring 改写为「整份场景文档只作配置同一性绑定，标定只来自显式参数」；本项新增的 `build_standoff_planner`、`_estimator_from_body_config` 原本不读路线（未改）。② 标定唯一来源为显式 `ground_plane_y_m`：`None`/bool → `ValueError`，非数值/非有限 → `ValueError`（消息均含 `ground_plane_y_m`），无缺省、不由路线或 home 高度代填；CLI 既有「缺 `--ground-plane-y-m` → `parser.error`」「非有限 → `parser.error`」未改。③ 原接线用例 `test_standoff_scenario_id_and_ground_plane_fail_closed` 的错误预期（有限 0.0 因与路线 0.2 不等被拒）改为「非有限 NaN 被拒」。场景逐值一致性（AC-18/29）、schema/`scenario_id`、SHA/来源身份保留。冻结 `_build_body_runtime` 的 hold/threshold 路径（含其旧路线高度检查）逐字未改：`git diff -U0 "$R1CAND".."$R1FIX" -- controller/track_loop.py` 的 3 个 hunk 全在 `_build_standoff_runtime` 内 | `tests.test_track_loop.StandoffWiringTests.test_standoff_ground_plane_is_explicit_finite_and_route_independent`（新）：真实 `_build_body_runtime(..., "standoff")`、既有 untethered 场景与 FRAME 配置、同一 `scenario_id`、临时 runtime 无覆盖：显式 0.2 与 0.0 均构造成功；直接构造 `None`、NaN、+Infinity、−Infinity 均 `ValueError`（消息含 `ground_plane_y_m`）；CLI 缺 `--ground-plane-y-m` 及 `=nan`/`=inf`/`=-inf` 均退出码 2、stderr 点名该参数；临时 runtime 前后为空。修复前：0.0 → `ValueError`（路线高度不符，**红**）、`None` → `TypeError`（红）、NaN → 未拒绝（红）；±Infinity 与 4 条 CLI 子用例修复前即拒绝 → 修复后全过。`tests.test_standoff_planner.TruthIsolationTests.test_standoff_construction_path_reads_no_route_or_evaluator_output`（新，静态）：只取 `_build_standoff_runtime`、`build_standoff_planner`、`_estimator_from_body_config` 三个函数源码，断言不含 `route`、`target`、`metrics.json`、`m3_body_truth`、`truth`、`evaluator`；不扫描旧模块全文、不迫使改冻结路径。修复前 `_build_standoff_runtime names 'route'`（红）→ 修复后过。原用例 `test_standoff_scenario_id_and_ground_plane_fail_closed`（改预期后）修复前 NaN 未拒绝（红）→ 修复后过 |

**红绿记录**（修复前 = 开工 HEAD 的 `controller/`、`tools/`（与 `$R1CAND` 相同）+ 本轮新测试的未提交工作树；修复后 = `$R1FIX`；
解释器同下「测试」，`-m unittest discover -s tests -p <模块>.py -k <名>`，输出写会话暂存、只回显摘要）：

| 选取 | 修复前 | 修复后 |
|---|---|---|
| `test_standoff_planner.py`，`-k` 上表 3 个方法 | `Ran 3`，`FAILED (failures=1, errors=10)`：9 个对角子用例与随机用例 `OverflowError`、静态检查 `route` | `Ran 3`，`OK` |
| `test_frame_follow_replay.py`，`-k AnalyzeRunTests` | `Ran 2`，`FAILED (failures=1)`：`ValueError not raised` | `Ran 2`，`OK` |
| `test_track_loop.py`，`-k StandoffWiringTests` | `Ran 5`，`FAILED (failures=2, errors=2)`：errors = 新用例 0.0 路线不符与 `None` `TypeError`；failures = NaN 未拒（新用例与改预期后的原用例各一） | `Ran 5`，`OK` |

**按复核协议复验**（一次性 worktree，detach 于 `$R1FIX`，跑后删除）：`git revert -n "$R1FIX"` 后同上三组选取依次为
`FAILED (failures=1, errors=10)`、`FAILED (failures=1)`、`FAILED (failures=2, errors=2)`（与上表修复前逐项相同）；`git checkout "$R1FIX" -- controller tools`
恢复后三组均 `OK`。提交拆分：回归用例 `$R1TEST`、修复 `$R1FIX`；`$R1FIX` 的树与全套测试所跑代码的树相同（拆分前后 `HEAD^{tree}` 相等）。

**修复后 focused（模块级）**：`test_standoff_planner` 34 OK（32 + 2 新）；`test_frame_follow_replay` 16 OK（15 + 1 新）；`test_track_loop` 27 项、1 败 =
基线既有 `test_cli_runs_pinned_csrt_to_a_versioned_summary`（本机 cv2 无 `TrackerCSRT_create`）；`test_frame_tether_switch` 18 OK；`test_track_experiment` 7 OK。

**回放（AC-19/AC-20）**：R1-1 改动经回放路径生效，故修复后执行 `.venv-yoloe/bin/python tools/frame_follow_replay.py --check`：`replay evidence matches`（墙钟 86 s）。
`docs/evidence/P1-ENG-FRAME-001-replay.{json,md}` 与 `config/p1-eng-frame-001-body.json` 在 `$R1CAND..$R1FIX` 零差异，**未重生成**，选中项仍为 C3、参数与证据 sha 不变；
R1-2 只改分析入口，不在回放网格内。

**Unity Edit Mode：本轮不重跑。** 理由：`git diff --name-only "$R1CAND".."$R1FIX" -- Assets ProjectSettings Packages` 为空，本轮未改任何 C#、场景或包配置；
`$R1CAND` 上的全套（284/284）既有实现者终跑（「C1@K2返工」节）亦有 R1@K2 复核副本独立重跑（复核文件 §0）。Unity Play 0、batchmode 0。

**Python 全套（AC-24，停点一次）**：`$R1FIX` 之后串行执行，AC-24 命令逐字（解释器同下「测试」），覆盖写 `docs/evidence/P1-ENG-FRAME-001-tests.log`：
`Ran 2061 tests`，`FAILED (failures=4, errors=9, skipped=19)`。失败集合与下「测试」所列基线 13 项**逐名相同**，**本批新增失败 0**；
新增 4 项（`test_standoff_planner` +2、`test_track_loop` +1、`test_frame_follow_replay` +1）全过。`runtime/`：全套前建参照文件，全套后
`find runtime -newer <参照>` 只命中 `runtime` 目录节点本身，目录内无文件变化（同前各轮现象）。

**已知限制与交复核关注（本轮新增）**

1. R1-2 的来源路径只记录不比对（理由见上表）；若复核认为 §3.11 入口 8 要求路径字符串相等，请在 R2 写 finding，本轮不自行扩张。
2. `hypot` 与旧式 `sqrt(x² + b²)` 在相关协方差（b ≠ 0）上可能有末位舍入差；回放 `--check` 全网格逐字节一致，未见决策变化。
3. AC-22 修订 1 的静态检查按证明闭集只钉三个新函数；`_build_body_runtime` 的 `standoff` 分派两行属旧函数，由真实调用的接线回归覆盖，不做静态扫描。

## C1@K2返工：返工要点逐条落实（交 `C2@K2`）

依据：提案「Contract conformance（核对表）」AC-1「不满足」理由、IR-10/IR-13「不采纳」与「返工要点」。修改只在 §4.1 内
（`git diff "$C1CAND".."$RWFIX"` 共 4 个路径：`ScenarioConfig.cs`、`TetheredTrackingEditModeTests.cs`、`controller/scenario_tether.py`
（仅模块文档串）、`tests/test_frame_tether_switch.py`）；参数、预注册规则、回放选参（仍为 C3）、Play 信封、plant 与 bootstrap 均未动。

| # | 返工要点（核对表原意） | 修改（`ScenarioConfig.cs`） | 回归用例 |
|---|---|---|---|
| 1 | 区分「缺键 / 序列化器实体化哨兵」与「显式非法围栏」：有缆模式显式非有限围栏不得静默取消，无缆继续 fail-closed | `DroneScenarioConfig.geofence_xz_m` 改 `[NonSerialized]`：JsonUtility 不能表示 null 成员，围栏不再交给它读写，原始 `JsonUtility.FromJson` 与 `ToJson` 往返都不再产生围栏对象，「实体化哨兵」这一类输入因此消失；`FromJsonStrict` 先调 `ReadTetherKeys` 读围栏：出现即须为对象、四界齐全、每界为有限 JSON 数值（`NaN`/`Infinity`/`-Infinity`/超出 float32 → `must be finite`；bool/字符串/null/对象/数组 → `must be a number`；缺界 → `is missing`）；`NormalizeGeofence` 删除全 NaN 哨兵分支（`IsUnsetGeofence` 已删），非空围栏一律校验有限、min < max、含 home，缺失且无缆 → `is required` | Edit Mode `ScenarioTetherSwitchTests.ExplicitTetherKeyValues_AreRefusedLikeThePythonParser`（17 个显式值夹具，含有缆/缺开关/无缆三种全 NaN）；`ScenarioTetherSwitchTests.SerializerPaths_NeverMaterialiseAGeofence` |
| 2 | `ApplyTetherKeyPresence` 键检测限定 `drone` 语境，真正缺字段始终开启 | 删除全文 `IndexOf` 判键与全文 `RequireJsonField("min_x"…)`；新增内部最小结构化读取器 `ScenarioConfig.JsonText`（字符串含转义、对象、数组、字面量；结构畸形即拒绝），只列根对象与 `drone` 对象的**直接成员**（同名键取最后一个，同 Python `json`）；`ApplyTetherKeyPresence(config, keys)`：缺 `tether_enabled` → `true`，缺 `geofence_xz_m` → `null`；开关须为 JSON `true`/`false` | Edit Mode `ScenarioTetherSwitchTests.TetherKeysOutsideTheDroneObject_MeanMissing`（4 个语境夹具：键在另一对象、嵌在 drone 子对象、在字符串内、无缆而围栏在另一对象） |
| 3 | 保留旧场景及 JsonUtility 往返回归 | — | `ExistingScenarioFiles_NormalizeBitwiseAsBeforeAndStayTethered`（17 个既有文件逐位）、既有 `Scene006CandidateProbeEditModeTests.HappyPathBindsReviewedIdentity`（ToJson 往返）、`SceneAdjustmentConfigTests.CheckedInConfigsCarryTheSameStrictSceneAdjustment`（原始解析）终跑均过；`SerializerPaths_NeverMaterialiseAGeofence` 钉住原始解析与 ToJson 往返均无围栏、无缆往返 fail-closed |
| 4 | Python 与 C# 逐名同表（AC-1） | `controller/scenario_tether.py` 逻辑原已只读 drone 直接成员并拒绝非 bool/非数值/非有限，本轮未改逻辑，只更新模块文档串（原「Python additionally rejects a non-bool」已不成立） | `tests/test_frame_tether_switch.py`：同名同插入文本的 `EXPLICIT_VALUE_FIXTURES`（17）与 `KEY_CONTEXT_FIXTURES`（4），`TetherSwitchParserTests.test_explicit_key_values_match_unity`、`test_keys_outside_the_drone_object_mean_missing`、`test_text_fixture_names_are_unique_and_disjoint_from_the_closed_set` |
| 5 | IR-10、IR-13 按裁定改写或撤回 | 两条均撤回，见「实现读法」表；不另立新读法 | 同上 |

K2补跑 回归用例 `SerializerMaterialisedGeofence_MeansAbsentButPartialFenceIsRefused`（编码已被否的 IR-13）由 `SerializerPaths_NeverMaterialiseAGeofence` 取代；
其「部分 NaN 拒绝」断言保留并加严为「全 NaN 亦拒绝」。闭集用例 `ClosedFixtureSet_VerdictsMatchThePythonParser` 与 Python 闭集未改。

**红绿**（红 = `$C1CAND` 的 `ScenarioConfig.cs` + 新测试文件，未提交工作树；绿 = `$RWFIX`）：

| 用例 | 修复前 | 修复后 |
|---|---|---|
| Edit Mode `ExplicitTetherKeyValues_AreRefusedLikeThePythonParser` | **败**，7 个夹具不一致：`fence-all-nan`、`true+fence-all-nan`、`true+fence-string-bound`、`true+fence-null-bound`、`switch-number+fence`、`switch-string+fence` 被接受；`true+fence-overflow` 以 `ArgumentException`（JsonUtility 解析失败）而非合同理由拒绝 | 过 |
| Edit Mode `TetherKeysOutsideTheDroneObject_MeanMissing` | **败**：`keys-in-another-object`、`keys-nested-in-drone` 被误拒（全文判键后 `missing required field 'min_x'`/`'max_x'`） | 过 |
| Edit Mode `SerializerPaths_NeverMaterialiseAGeofence` | **败**：原始 JsonUtility 解析实体化出围栏对象（首个断言） | 过 |
| Edit Mode 其余 3 条 `ScenarioTetherSwitchTests` | 过 | 过 |
| Python 上列 3 条 | 过（Python 解析器逻辑未改，红只在 C# 侧） | 过 |

**Unity Edit Mode**（开工及每次启动前 `pgrep -fl 'Unity.app/Contents/MacOS/Unity'` 无进程；batchmode、非 Play、零 ID；命令同下「Unity Edit Mode」小节，
仅 `-testResults`/`-logFile` 换文件名，红跑另加 `-testFilter TetheredTracking.Tests.ScenarioTetherSwitchTests`）：

| 次序 | 代码 | 结果（total / 过 / 败 / 跳过） | 产物（本机 `Logs/`，不入库） |
|---|---|---|---|
| 红跑（17:04Z） | 修复前 `ScenarioConfig.cs` + 新测试 | 6 / 3 / 3 / 0 | `P1-ENG-FRAME-001-rework-red.xml` sha256 `84bab9ced3b3310cfe25cab8e7fb971cffdad9e3ae50a75ac733db2701550c2d`、`…-rework-red-unity.log` |
| 中间跑（17:06Z） | 修复后未提交工作树，全套 | 284 / 284 / 0 / 0 | `P1-ENG-FRAME-001-rework-mid.xml` sha256 `a5b6c25066ee5f68270fccc3e15ff9c414ba271a54bcd383be38e87adc9ab96f` |
| **终跑（17:07Z）** | `$RWFIX`，`git status --porcelain -- Assets` 为空，全套 | **284 / 284 / 0 / 0** | `P1-ENG-FRAME-001-editmode-rework.xml` sha256 `662a58872840ce058c7e7173affa3a7f3503f0e82c2294ec425465d8265bf70c`、`…-editmode-rework-unity.log`（无 `error CS`） |

计数：284 = K2补跑 终跑 282 − 1（被取代的哨兵用例）+ 3（新用例）。既有用例全过（含上列两条既有用例）。三次运行后 `git status --porcelain`
只有本轮自改文件，Unity 未改写任何已跟踪文件，无需 `git restore`。修复前后各以 Unity 自带 Roslyn 离线编译 Runtime 与 EditModeTests 两程序集：
0 错误，改动的两个 C# 文件 0 警告（只证能编译）。

**Python 全套**（`$RWFIX` 之后、Edit Mode 终跑之后串行执行；AC-24 命令逐字，解释器同下「测试」）：`Ran 2057 tests`，
`FAILED (failures=4, errors=9, skipped=19)`；失败集合与「测试」所列基线 13 项逐名相同，**新增失败 0**；新增 3 项全过。
开发期 focused：`-m unittest discover -s tests -p test_frame_tether_switch.py` 18 项 OK。`runtime/`：全套前建参照文件，全套后
`find runtime -newer <参照>` 只命中 `runtime` 目录节点本身，目录内无文件变化。

**已知限制（本轮新增，交复核关注）**

1. `JsonUtility.ToJson(ScenarioConfig)` 不写出围栏（`[NonSerialized]` 的直接后果）：无缆配置往返重载按「无缆缺围栏」拒绝（fail-closed，
   用例钉住）；**有缆 + 围栏**配置往返会丢失围栏。仓库无此场景文件，运行时与 Editor 代码对 `ScenarioConfig` 无 `ToJson` 调用（只有测试
   以 `ToJson` 写无围栏候选），故当前无可达路径；如需该往返，须另立合同。
2. 不经 `FromJsonStrict` 的原始 `JsonUtility.FromJson<ScenarioConfig>` + `Normalize` 读无缆文件会因无围栏被拒（fail-closed）；仓库内此路径
   只读有缆文件（`SceneAdjustmentConfigTests`、`SceneCorridorEvidenceGenerator` 读旧缺省）。
3. 围栏界值超出 float32 范围（如 `1e39`）：Unity 按 `must be finite` 拒绝，Python 以 float64 视为有限并接受；闭集外、Unity 更严（fail-closed）。
   `1e999` 两侧均拒（同名夹具 `true+fence-overflow`）。
4. §3.1 两键之外的既有差异未改（C1 裁定「机体限值既有 Normalize 口径本轮不改」）：机体限值非正/非有限（Unity `Normalize` 回退缺省值、
   Python 拒绝），`drone` 缺失或非对象（Unity 回退有缆缺省、Python 拒绝）。不作为读法申请。
5. `FromJsonStrict` 现先做结构化读取：结构畸形的文本由该读取器以 `InvalidOperationException`（`malformed near character …`）拒绝，
   不再先到 JsonUtility；18 个 `config/scenario*.json` 与 ACQ 残留覆盖文件均为严格 JSON（只读核对），全部 Edit Mode 读取路径终跑通过。

## K2补跑：Edit Mode 失败归因与修复

| # | 失败（首跑） | 归因 | 修复（§4.1 内） | 为何不越界、不改 AC 含义 |
|---|---|---|---|---|
| E-1 | `Scene006CandidateProbeEditModeTests.HappyPathBindsReviewedIdentity`、`SceneAdjustmentConfigTests.CheckedInConfigsCarryTheSameStrictSceneAdjustment`（既有，非本批）：`drone.geofence_xz_m.min_x must be finite.`，栈顶为本批新增 `ScenarioConfig.NormalizeGeofence` | **本候选缺陷**。新增的 `GeofenceScenarioConfig` 以四个 NaN 初值作「未设」哨兵；Unity 序列化器不会让 `[Serializable]` 成员为 null，`JsonUtility.FromJson` 读不含该键的文件（SceneAdjustment 用例直接 `FromJson`+`Normalize` 读三份既有场景）或 `JsonUtility.ToJson` 往返（Scene006 夹具用 `ToJson` 写候选再 `FromJsonStrict` 读回，文本含该键与 NaN）都实体化出全 NaN 围栏；`FromJsonStrict` 的键存在判定只覆盖「文本无键」，`Normalize` 于是拒绝 | `ScenarioConfig.NormalizeGeofence`：四值**全为** NaN（哨兵）视同缺省并置 null；部分为 NaN 仍按「must be finite」拒绝；系留关 + 哨兵仍按「is required」拒绝。新增回归用例 `ScenarioTetherSwitchTests.SerializerMaterialisedGeofence_MeansAbsentButPartialFenceIsRefused`（四段：原始解析、往返、部分 NaN 拒绝、系留关缺失拒绝） | 文件属 §4.1（`ScenarioConfig.cs`，AC-1/3/27）；AC-1 闭集 7 个夹具裁决不变（终跑 `ClosedFixtureSet_VerdictsMatchThePythonParser` 过）；AC-3 逐位回归终跑过；只影响闭集外「显式写出全 NaN 围栏」的输入（Unity 视同缺省、Python 解析器拒绝非有限值），与 IR-10「闭集外 Python 更严」同类，记 IR-13；plant、bootstrap 与场景文件未改 |
| E-2 | `TetheredDronePlantTests.Step_TetheredGoldenVectors`（本批）：`GT4 step 800 x` 期望 13.6483994、实际 13.6484098（差 1.04e-5 > 1e-5） | **本候选缺陷（plant 镜像保真度）**。一次性诊断用例（未入库，跑后逐字节移除，测试文件 sha256 前后相同）导出真实 plant 在 9 条金标准序列上的逐步状态共 10,400 个（`Logs/P1-ENG-FRAME-001-plant-dump.txt`，sha256 `760590b861100bc03f9e2b5fe8f69f2ccf8c8dce103139cfa4e61fdf6c0b6a85`）：原镜像 4,020 个状态不逐位相等，最大偏差 1.91e-5（GT4 第 665 步），检查点最大 1.05e-5（GT4 第 800 步）。原因：Unity 的 Mono 运行时对 float 表达式中间量按 double 计算，只在存入 float 局部变量/字段/参数/返回值/构造参数时舍入为 float32（C# 规范允许）；原镜像逐运算舍入，误差在缆长球面滑移中累积 | `tools/frame_follow_replay.py` 镜像改为「存储时舍入」：平方和与模长、`ClampMagnitude` 比较、`MoveTowards` 末式、缆长内项、随机指令生成各按一次存储舍入。改后镜像与上述 10,400 个状态**逐位相等（0 不等）**。金标准字面值按改后镜像重生成（C# 与 Python 两处同值，31 行；即真实 plant 输出），容差仍 1e-5 | 交接文件既定处理「只重定字面值」在此不收敛：字面值取真实 plant 后 Python 侧 GT4@800 同样差 1.04e-5，故按派发「候选缺陷、修复落在 §4.1 内」处理；镜像与回放工具属 §4.1（AC-19/20/21）；plant 代码未改；AC-19 的 1e-5 不放宽。连带：回放证据重生成（见 §P AC-19/AC-20），选参所用 25 m/系留关/E1 三格与 `selection` 节逐字节不变，仍选中 C3、参数不变 |

C# 改动当时已用 Unity 自带 Roslyn 离线编译（零错误、改动文件零警告，见 §共用「离线编译」）；Edit Mode 结果以本节与 §共用 AC-24 为准。

## 实现读法（`C1@K2` 已裁：IR-1…9、IR-11、IR-12 采纳；IR-10、IR-13 不采纳，C1@K2返工 已撤回）

合同字面未写死或需要数值落地之处，取保守读法继续并逐条列出；未改动任何门值、候选参数与预注册规则。

| 编号 | 合同位置 | 字面 | 所取读法 | 理由 / 影响 |
|---|---|---|---|---|
| IR-1 | AC-14「系留开启时内嵌实例带冻结 BODY-001 走廊棱柱与半径 0.5 m」 | 「半径 0.5 m」 | 内嵌 `ThresholdBodyPlanner` 的 `corridor_radius_m` = `corridor_nominal_radius_m` 0.5 + `clearance_margin_m` 0.5 = 1.0，与现行 `_build_body_runtime` 阈值分支逐字同法 | §3.6 ③ 同写「膨胀 1.0 m = BODY-001 走廊半径 0.5 + 净空 0.5」，「半径 0.5」即名义半径；若取 0.5 则内嵌实例与生产阈值路径不等，违背「逐字复用冻结 BODY-001 值」。`build_standoff_planner` 另校验 `fixed.corridor_pad_m` 等于该和 |
| IR-2 | §3.6 第 5 步 ① | 只写「投影后残余速度 < 0.05 m/s → hold」 | 机身已在启用边界外超过 1 mm（经 plant 钳位不可达，只出现在 AC-15 F-on/F-off 夹具的界外采样）→ 直接 hold `+boundary_blocked`；投影后位移若超过 `v_max·0.4` 则截到 `v_max·0.4` | 界外机身投影到边界会要求超速；fail-closed。影响 AC-15 夹具的 hold 计数，不影响回放（机身恒在界内） |
| IR-3 | §3.6 第 5 步 ①、AC-15 (a)(b) | 「投影」「候选在围栏闭矩形内」 | 投影目标内缩 1e-9 m；输出前用消费者同一算式 `机身 + v·0.4` 复核：可达圆容差 1e-6 m（AC-15 (a) 同值）、围栏精确；不满足即 hold `+boundary_blocked` | 消除浮点舍入把候选推出闭矩形的可能 |
| IR-4 | §3.6 第 4/6 步 | 兜底速度「一律」经第 5 步；修饰按第 5 步顺序 | 采用兜底速度时，`reason` 只含本规划器第 5 步产生的修饰（内嵌阈值自身的 `+corridor_shortened` 不转写；③ 以同一 1.0 m 膨胀复核） | 闭集与顺序只定义第 5 步修饰 |
| IR-5 | §3.6 第 1 步、AC-11 | 三种契约 hold | 平台位置非有限 → `hold_no_platform`；内嵌阈值对畸形输入抛 `ValueError/TypeError/ArithmeticError` 时视为无兜底，第 1 步照常给契约 hold | 有限输入不抛异常的保守延伸 |
| IR-6 | §3.6 第 2/3 步 | 「位置 2×2 协方差最大特征值」「任一分量非有限」 | 取对称化 2×2（非对角取均值）；「任一分量」= 均值 4 项 + 协方差 16 项；估计闸 hold 时跟随锁存不变 | 不放宽闸门 |
| IR-7 | §3.9 回放模型 | 未写帧内步长、云台瞄点、框裁剪、E2 噪声作用对象、无缆格阈值是否带走廊、H3 判据细节、第二圈窗口 | plant 每帧 10 子步（0.02 s，float32 镜像；K2补跑 起为存储时舍入，见 IR-11）；帧 0 为初始化 hold（同 `track_loop` initialize）；云台理想指向车框中心（45° 钳、限位 + 0.1° 记饱和）；框为车体有向盒投影后裁剪；E2 姿态噪声加在**上报**相机基上、框由真实相机生成；无缆格阈值 (a) 不带走廊棱柱（同内嵌兜底）；H3「入膨胀棱柱」= 机身位置严格落入 2.1 m 膨胀棱柱，修饰占比分母 = 第二圈有 standoff 原因的决策帧；短边 = 2.0 m·fy / 到车框中心斜距；第二圈 = `[T, 2T)`；H4 停止态由窗口首样本初始化 | 全部写入 `replay.json`「model」；选参只在 25 m / 无缆 / E1 判 |
| IR-8 | AC-5「TetherAnchor 两模式都保留，OcclusionGeometry.Build 入参不变」 | Edit Mode bootstrap 用例 | 缆绳由新静态方法 `TetheredScenarioBootstrap.CreateTetherLine` 生成并做功能测试；锚点标记与遮挡几何入参因 `CreateAnchor` 用 `Destroy`（仅 Play 可用）改以源码文本断言钉住（`Awake` 无条件调用、`CreateAnchor`/`CreateEvaluationOcclusionGeometry` 不含系留开关） | 两处代码未改动，复核按 diff 核对 |
| IR-9 | AC-25 文件围栏 | 「候选 diff 文件集 ⊆ §4.1」 | 另含两类流程必写文件：`docs/current-status.md`（状态板）与 `docs/evidence/P1-ENG-FRAME-001-ledger.json`（派发信封要求的消耗记账）；均非代码/配置 | 见 §共用 AC-25 |
| IR-10 | AC-1 | 两侧对闭集夹具裁决一致 | **已撤回（`C1@K2` 不采纳；C1@K2返工）**。原读法「闭集外 Python 更严：机体限值、围栏数值为 bool 时 Unity 回退」不再使用：§3.1 两键现两侧同表——Unity 同样拒绝非 bool 开关与非数值/非有限围栏界值 | 证据：Edit Mode `ExplicitTetherKeyValues_AreRefusedLikeThePythonParser` 与 Python `test_explicit_key_values_match_unity` 同名同文本 17 夹具（含 `true+fence-all-bool`、`true+fence-string-bound`、`switch-number+fence` 等）。机体限值等既有 `Normalize` 口径按裁定本轮不改，见「C1@K2返工」已知限制 4，不作读法 |
| IR-11 | AC-19「金标准向量」 | 来源未写 | 金标准字面值由 Python float32 镜像生成，Edit Mode `Step_TetheredGoldenVectors`/`Step_UntetheredGoldenVectors` 对真实 plant 断言同一组字面值（≤ 1e-5）。**K2补跑 更新**：镜像改按 Unity 运行时「double 中间量、存储时舍入 float32」建模（E-2），与真实 plant 在 9 条序列全部 10,400 个状态逐位相等，故字面值即真实 plant 输出；Edit Mode 终跑与 Python 两侧对同一字面值均通过（实际偏差 0） | **已闭合**（首跑 GT4@800 差 1.04e-5 失败，修复后终跑通过；另：镜像仍复现两条既有 plant 测试字面值） |
| IR-12 | AC-15 夹具 | 状态是否独立 | 每个夹具用同一规划器实例按种子顺序连续调用（锁存与兜底滞回在样本间延续） | 避免每样本重建 779 棱柱索引 |
| IR-13 | §3.1「缺字段 = 无围栏」、AC-1（K2补跑 新增） | 未写序列化器实体化成员的情形 | **已撤回（`C1@K2` 不采纳；C1@K2返工）**。原读法「全 NaN 视同缺省」与 `IsUnsetGeofence` 已删除；现按 §3.1 字面「出现即校验」实现：围栏不经 JsonUtility（`[NonSerialized]`），由 `FromJsonStrict` 只读 `drone` 直接成员，显式全 NaN/非有限围栏在有缆、缺开关、无缆三种情形均拒绝 | 证据：`ExplicitTetherKeyValues_AreRefusedLikeThePythonParser`（`fence-all-nan`、`true+fence-all-nan`、`false+fence-all-nan`）与 `SerializerPaths_NeverMaterialiseAGeofence`；`[NonSerialized]` 的后果见「C1@K2返工」已知限制 1–2 |

## §T（Part T：AC-1…10、AC-27…29）

| AC | 证据指针 | 自证结果 |
|---|---|---|
| AC-1 | test: `tests/test_frame_tether_switch.py`（`TetherSwitchParserTests.test_closed_fixture_set_verdicts`、`test_non_bool_switch_is_rejected`、`test_malformed_fence_values_are_rejected`；C1@K2返工 新增 `test_explicit_key_values_match_unity`、`test_keys_outside_the_drone_object_mean_missing`、`test_text_fixture_names_are_unique_and_disjoint_from_the_closed_set`）；test: Edit Mode `ScenarioTetherSwitchTests.ClosedFixtureSet_VerdictsMatchThePythonParser`；C1@K2返工 新增 test: Edit Mode `ScenarioTetherSwitchTests.ExplicitTetherKeyValues_AreRefusedLikeThePythonParser`（显式非法值）、`ScenarioTetherSwitchTests.TetherKeysOutsideTheDroneObject_MeanMissing`（无键/语境）、`ScenarioTetherSwitchTests.SerializerPaths_NeverMaterialiseAGeofence`（序列化往返；取代 K2补跑 的 `SerializerMaterialisedGeofence_MeansAbsentButPartialFenceIsRefused`） | Python：7 个闭集夹具（缺字段/true/true+围栏/false+围栏/false+缺围栏/false+倒置/false+不含 home）裁决与 C# 用例逐名同表；非 bool 拒绝。**C1@K2返工**：闭集外 17 个显式值夹具与 4 个语境夹具两侧同名同文本、裁决一致（显式非有限/非数值围栏两模式均拒绝、非 bool 开关两侧均拒绝、`drone` 外同名键不改变「缺字段 = 有缆、无围栏」）；三条新 Edit Mode 用例修复前红、修复后绿（见「C1@K2返工」红绿表），Edit Mode 终跑 `Logs/P1-ENG-FRAME-001-editmode-rework.xml` 284/284 |
| AC-2 | test: Edit Mode `TetheredDronePlantTests.Step_TetherEnabledMatchesLegacyReferenceBitwise`（测试内 `LegacyPlantReference` = 基线 `Step` 逐字副本；序列：既有两例按原步长 4 条 + GT1 加速 / GT2 向外饱和 / GT3 高度上下限 / GT4 斜向滑移 / GT5 1,000 步种子随机 / 1,500 步种子随机真实锚点；每条分「字段缺省」与「显式 true」两路逐步逐位比对位置、`AppliedVelocity`、`TetherSaturated`） | Edit Mode 终跑过（`Logs/P1-ENG-FRAME-001-editmode.xml`，§共用 AC-24）（首跑亦过）。复核按基线 diff 核对 `LegacyPlantReference.Step` 与基线 `TetheredDronePlant.Step` 逐字相同（唯一改编：`transform` 为字段） |
| AC-3 | test: Edit Mode `ScenarioTetherSwitchTests.ExistingScenarioFiles_NormalizeBitwiseAsBeforeAndStayTethered`（17 个既有文件逐一列名于 `ExistingScenarioNames`，与测试内逐字保留的旧 `Normalize` 片段逐位比对 drone/gimbal/sensor）；cmd: `git diff --exit-code "$BASE" -- 'config/scenario*.json' ':!config/scenario.untethered.json'` | cmd 退出码 0（字节未变）；Edit Mode 终跑过（`Logs/P1-ENG-FRAME-001-editmode.xml`，§共用 AC-24）（首跑亦过）。**C1@K2返工**：围栏改由 `FromJsonStrict` 读取后同一用例终跑过（`Logs/P1-ENG-FRAME-001-editmode-rework.xml`），17 个既有文件仍逐位相等、有缆、无围栏；两条既有用例 `HappyPathBindsReviewedIdentity`、`CheckedInConfigsCarryTheSameStrictSceneAdjustment` 终跑过；cmd 重跑（`"$BASE"` 对工作树）退出码 0 |
| AC-4 | test: Edit Mode `TetheredDronePlantTests.Step_TetherOff_CanPassThirtyFiveMetresFromAnchor`、`Step_TetherOff_NeverReportsTetherSaturated`、`Step_TetherOff_AltitudeBandIsNotCappedByTetherLength`、`Step_TetherOff_SpeedAndAccelerationClampsUnchanged`、`Step_TetherOff_StaysInsideGeofence`（每条带「红」：同序列在系留开/无围栏下违反该断言） | Edit Mode 终跑过（`Logs/P1-ENG-FRAME-001-editmode.xml`，§共用 AC-24）：5 条首跑、终跑均过；同语义的 Python 镜像断言 test: `tests.test_frame_follow_replay.PlantMirrorGoldenTests.test_untethered_mode_differs_from_tethered_on_the_same_sequence` 通过 |
| AC-5 | test: Edit Mode `TetherBootstrapConstructionTests.TetherLine_IsCreatedOnlyWhenTetherEnabled_WithUnchangedParameters`、`AnchorMarkerAndOcclusionRoots_DoNotDependOnTheTetherSwitch`（IR-8） | Edit Mode 终跑过（`Logs/P1-ENG-FRAME-001-editmode.xml`，§共用 AC-24）（首跑亦过） |
| AC-6 | test: Edit Mode `FrameProtocolInvariantTests.SensorFrameMetadataV3_FieldSetIsUnchanged`；cmd: `git diff --exit-code "$BASE" -- controller/protocol.py controller/body_entry.py controller/gimbal_entry.py`；关闭模式 `tether_saturated` 恒 false 由 AC-4 `NeverReportsTetherSaturated` 覆盖（`SensorFrameWriter` 未改，直接写 `drone.TetherSaturated`） | cmd 退出码 0；`SensorFrameWriter.cs` 零改动；Edit Mode 终跑过（`Logs/P1-ENG-FRAME-001-editmode.xml`，§共用 AC-24）（首跑亦过） |
| AC-7 | cmd: `git diff --exit-code "$BASE" -- controller/body_planner.py config/p1-m3-body-001.json config/p1-m3-body-001-corridor-prisms.json config/scenario.default.json`；cmd: `python3 tools/build_m3_corridor.py --check`；test: `tests.test_m3_body_tools`、`tests.test_m3_body_policy` | diff 退出码 0；`corridor check OK: 779 prisms`；两模块 56 / 29 项全过（focused 与全套） |
| AC-8 | test: `tests.test_frame_tether_switch.ThresholdConstructorSwitchTests.test_tethered_identity_and_decisions_are_unchanged`（字段缺失与显式 true 两路：身份字典与字面期望相等、120 帧决策与按旧构造法建的独立 `ThresholdBodyPlanner` 逐条相等且含移动分支）、`test_tether_off_scenario_refuses_the_threshold_policy`、`test_hold_policy_is_unaffected_by_the_switch` | 通过 |
| AC-9 | test: `tests.test_frame_tether_switch.UntetheredScenarioDiffTests.test_difference_is_exactly_the_section_3_1_key_set` | 差异键恰为 `scenario_id`、`drone.tether_enabled`、`drone.geofence_xz_m` |
| AC-10 | test: `tests.test_frame_tether_switch.SafetyBoundsTests`（`test_untethered_bounds_equal_section_3_4`、`test_tethered_bounds_record_reach_circle_and_no_fence`、`test_standoff_manifest_identity_carries_the_bounds`、`test_replay_evidence_records_the_offline_clearance_check`）；artifact: `docs/evidence/P1-ENG-FRAME-001-replay.json`「safety_bounds」 | 围栏 [110,190]×[50,130]、高度 25 m / [8,32]、4 m/s、4 m/s²、膨胀 2.1、d_plaus 65、时效 0.4 写入 standoff 身份 `safety_bounds`；有缆场景身份记可达圆 √(35²−25²) 与无围栏。离线核对：围栏内相交棱柱 70 个、顶高最大 16.93 m，+2.1 < 25.2 m（25 m 档无冲突）；15 m 档如实列出冲突棱柱（顶高 16.93 m） |
| AC-27 | test: Edit Mode `ScenarioTetherSwitchTests.VersionedDefault_IsTheUntetheredScenarioAndLoadOrderIsUnchanged`（只读成员 `ScenarioConfig.VersionedDefaultPath`；不调 `Load()`；`FromJsonStrict` 读新旧两文件；`Load()` 覆盖优先行与 `CreateDefault()` 回退行以源码文本钉住） | Edit Mode 终跑过（`Logs/P1-ENG-FRAME-001-editmode.xml`，§共用 AC-24）（首跑亦过）。`Load()` diff 只改 `projectDefault` 一行。**C1@K2返工**：`Load()` 未改动（`"$C1CAND".."$RWFIX"` 对该方法零差异），同一用例终跑过（`Logs/P1-ENG-FRAME-001-editmode-rework.xml`）：新文件经 `FromJsonStrict` 读得 `tether_enabled = false`、围栏 = §3.4 值，旧文件有缆 |
| AC-28 | test: `tests.test_track_experiment.DefaultScenarioEntryTests`（缺省 `--print-only` 输出逐字等于期望：`deterministic-loop-untethered`、运行时 sha、`planned_duration_s` 272.97056274847716 与旧缺省相等；显式旧文件输出 JSON 逐字等于改动前字面；不透传 `--body-*`）；既有 3 条用例未改 | 通过；另以基线文件副本实跑比对：显式旧文件输出与改动前逐字节相同 |
| AC-29 | test: `tests.test_frame_tether_switch.EffectiveScenarioPathTests`（无覆盖 → 新文件；有覆盖 → 覆盖；AST 断言不导入/不调用 `language_loop`）；身份写入见 AC-10 / AC-18 用例 | 通过 |

**§T 四项条件自证（workflow §4.3.1）**

1. 范围与接口冻结：`tethered-scenario/v1` 只增两个可选键；帧包/命令包字段零改动（AC-6）；三处缺省入口按 §3.11 落地，`track_loop` 无场景缺省、覆盖文件不生成。
2. 相称测试：Python 侧 focused 与全套无新增失败（§共用 AC-24）；Unity Edit Mode 全套终跑 282/282 通过（K2补跑），AC-1(C#)/2/3/4/5/6(C#)/27 的 Edit Mode 用例全过。**C1@K2返工**：Edit Mode 全套终跑（`$RWFIX`）284/284，Python 全套 2057 项无新增失败；AC-1 新增三条 Edit Mode 用例修复前红、修复后绿。
3. 已知 Unity 失败：首跑 3 条（E-1 两条既有用例、E-2 金标准）已修复并终跑复测通过；无未修复的已知 Edit Mode 失败。**C1@K2返工**：红跑 3 败均为修复前候选在新用例上的预期红，修复后终跑全过；无未修复的已知 Edit Mode 失败。无缆新路径的 Unity Play 证据属 AC-21/AC-23，未授权前不跑。
4. 候选、状态板与未验证风险：已更新（本文件、状态板交接行）；Part T 未验证风险见 §共用「未验证项」。

## §P（Part P：AC-11…20）

| AC | 证据指针 | 自证结果 |
|---|---|---|
| AC-11 | test: `tests/test_standoff_planner.py` `StandoffContractTests`（`test_contract_holds`、`test_finite_inputs_never_raise_and_keep_contract_fields`、`test_ordered_replay_through_a_fresh_instance_reproduces_commands`、`test_decide_path_does_no_io_clock_or_truth`、`test_module_imports_only_contract_types_from_body_planner`） | 通过：三种契约 hold；4,500 个有限随机输入不抛异常、`vy = 0`、`expires_after_s = 0.4`、水平速度 ≤ 4；400 帧序列经新实例逐条复现；`decide` 路径无 I/O/时钟/真值字样；模块从 `controller/body_planner.py` 只导入 `CONTRACT_VERSION`/`BodyCommand`/`BodyPlanner`/`PlatformState`/`WorldEstimate`（兜底实例由构造方注入，IR-1）。**R1@K2返工**：R1-1 已修（`_position_sigma` 改 `math.hypot`）；新增 `StandoffContractTests.test_large_finite_covariance_holds_without_raising`（三场景 × 4 种有限大协方差，修复前 9 子用例 `OverflowError`、修复后全过），随机用例方差候选扩至 1e200 且 x/z 独立抽取（修复前红、修复后绿），见「R1@K2返工」节 |
| AC-12 | test: `tests.test_standoff_planner.DistanceBandTests`（远、v_max 钳、锁存滞回带、提前量与目标速度钳、近侧不后退、转角） | 通过 |
| AC-13 | test: `tests.test_standoff_planner.EstimateGateTests`（σ > w / σ ≤ w 红绿、相关协方差最大特征值、均值/协方差非有限、d̂ > / ≤ d_plaus 红绿、提前量计入） | 通过 |
| AC-14 | test: `tests.test_standoff_planner.FallbackTests`（每帧调用：两模式 500 帧逐帧等于独立阈值实例；系留关无走廊、输出不带 `+corridor`；系留开带 779 棱柱与 1.0 m（IR-1）并与独立实例相等；仅跟随分支 hold 时采用；`estimate is None` 不越过契约 hold） | 通过 |
| AC-15 | test: `tests.test_standoff_planner.SafetyPostprocessPropertyTests.test_tethered_reach_circle_and_corridor`、`…test_untethered_fence_without_reach_circle`、`…test_fence_stacks_on_tether`、`…test_obstacle_clearance_all_fixtures`（方法名逐字取合同；棱柱判据用冻结 `segment_intersects_prism` 作独立 oracle） | 通过。F-on 10,000、F-off 10,000、F-both 1,000 个种子固定状态；F-off 越出可达圆的非 hold 输出 ≥ 100（断言），各主标记与修饰计数打印在测试输出（`AC-15 fixture seed=…` 行，见 tests.log） |
| AC-16 | test: `tests.test_standoff_planner.ReasonClosedSetTests` | 通过：组合按固定顺序、闭集外拒绝；三场景 9,000 次输出全部可被 `split_reason` 解析 |
| AC-17 | test: `tests.test_standoff_planner.FrameConfigLoaderTests`（字段闭集、BODY-001 path+sha、估计器/标定/兜底/时效逐字复用、12 种篡改拒绝、CLI 无参数覆盖） | 通过 |
| AC-18 | test: `tests/test_track_loop.py` `StandoffWiringTests`（`--body-policy standoff` 接受、三参数无缺省、缺任一 `parser.error`（退出码 2、消息含 `--body-`）；红绿：无覆盖 + untethered 通过 / 覆盖为旧缺省副本 + untethered 拒绝 / 无覆盖 + 旧缺省拒绝；`runtime` 缺失拒绝；身份含 planner、FRAME sha、场景 sha、生效场景路径、选中候选）；cmd: `git diff --exit-code "$BASE" -- controller/language_loop.py` | 通过；diff 退出码 0；`hold`/`threshold` 既有测试不变且通过。**R1@K2返工**：AC-22 修订 1 后新增 `StandoffWiringTests.test_standoff_ground_plane_is_explicit_finite_and_route_independent`（显式 0.2 / 0.0 均构造成功；`None`/NaN/±Infinity 直接构造拒绝；CLI 缺参数与非有限拒绝）；原 `test_standoff_scenario_id_and_ground_plane_fail_closed` 的 0.0 拒绝预期改为 NaN 拒绝；场景逐值一致性三种红绿不变；`language_loop.py` diff 仍为空 |
| AC-19 | test: `tests/test_frame_follow_replay.py`（`PlantMirrorGoldenTests` 按模式对 AC-2/AC-4 金标准向量 ≤ 1e-5、复现既有 plant 测试字面值；`ReplayDeterminismTests`；`ReplayEvidenceTests` 60 格齐全、种子各异、输入 sha 为现行文件、选参按规则重算一致）；artifact: `docs/evidence/P1-ENG-FRAME-001-replay.json`、`docs/evidence/P1-ENG-FRAME-001-replay.md`；cmd: `.venv-yoloe/bin/python tools/frame_follow_replay.py --check`（全网格重跑逐字节比对，约 7–10 分钟） | 通过。**K2补跑**：镜像改存储时舍入后与真实 plant 10,400 个状态逐位相等（E-2、IR-11），金标准字面值重生成，Edit Mode 侧金标准断言终跑通过；回放证据随之重生成——60 格中 21 格的描述读数变化（全为系留开格与 E2 格，系留开格 `tether_saturated_frames` 变化较大，如 threshold/25 m/系留开/E0 全程 422→130：原镜像逐运算舍入把球面上的位置推出缆长、多计饱和），选参所用 25 m/系留关/E1 三格与 `selection` 节逐字节不变；`replay.md` 仅 1 行变化；`--check` 全网格重跑逐字节一致（本轮墙钟 84 s）。（K2 首交时另验过 struct 与 numpy 两种舍入实现证据逐字节相同，针对旧镜像，K2补跑 未复做）。**R1@K2返工**：R1-1 改动经回放路径生效，修复后 `--check` 全网格 `replay evidence matches`（86 s），回放证据与 FRAME 配置零差异、未重生成，选参仍为 C3 |
| AC-20 | test: `tests.test_frame_follow_replay.FrozenParametersTests`（配置 `params`/`selected_candidate`/`fixed` = 证据选中项；配置记证据 sha；操作单含 §3.11 入口清单）；artifact: `docs/evidence/P1-ENG-FRAME-001-play-ops.md`；artifact: `config/p1-eng-frame-001-body.json` | 通过。参数在任何 Play 之前冻结；K2补跑 只更新配置 `replay_evidence.sha256`（证据重生成），`params`/`selected_candidate`/`fixed` 不变 |

**回放选参结果（预注册规则，工具执行）**：25 m / 无缆 / E1 / 第二圈，C1、C2、C3 全过 H1–H5
（饱和 0；短边 p10 32.5 / 31.1 / 29.5 px；越界与入膨胀棱柱 0 帧、修饰占比 0；起停 3 / 4 / 4；静止比例 0.015 / 0.060 / 0.098）；
第二圈路程 192.5 / 183.4 / 171.2 m，C3 最短且与 C2 差 > 3%，**选中 C3**（d\* 12 m、w 4 m、T_lead 2.5 s、k_p 0.4 /s）。K2补跑 重生成后以上读数与选中项不变。
注意 C3 的 H5 = 0.098 贴近 0.10 上限；E2 条件下 C3 起停 24 次/圈、静止 0.115（描述量，不参与选择）。15 m 与系留开读数只作描述，见 `replay.md`。

**§P 四项条件自证（workflow §4.3.1）**

1. 范围与接口冻结：契约 `body-planner-contract/v1` 不变；新策略 `standoff-band-v1` 只经 `--body-policy standoff` 接入 `track_loop`；参数由回放证据冻结。
2. 相称测试：focused 通过、全套无新增失败（§共用 AC-24）；性质测试 21,000 状态；镜像与真实 plant 10,400 个状态逐位相等（E-2）。**R1@K2返工**：R1-1、R1-2、AC-22 修订 1 各有具名回归，修复前红、修复后绿；全套 2061 项无新增失败；回放 `--check` 一致。
3. 已知 Unity 失败：首跑金标准失败（E-2）已修复、终跑通过；Part P 的 Unity Play 证据属 AC-21/AC-23（未授权前不跑）。
4. 候选、状态板与未验证风险：已更新；未验证风险见 §共用。

## §共用（AC-21…26）

| AC | 证据指针 | 自证结果 |
|---|---|---|
| AC-21 | artifact: `docs/evidence/P1-ENG-FRAME-001-play.md`（未建）；artifact: `docs/unity-test-log.md` `UT-P1-ENG-FRAME-001-D1`（未建） | **NOT_RUN**：K2 候选不含 Play；操作单已写（§3.11 入口 5），读数工具 `--analyze-run` 已实现并有合成 run 测试。**R1@K2返工**：仍 **NOT_RUN**；`--analyze-run` 现按 run manifest 场景 sha 绑定（R1-2），错配或缺身份即拒绝 |
| AC-22 | test: `tests.test_standoff_planner.TruthIsolationTests`、`StandoffContractTests.test_decide_path_does_no_io_clock_or_truth`；cmd: `grep -nE 'metrics.json|m3_body_truth|route_world_m' controller/standoff_planner.py controller/scenario_tether.py` | 通过；grep 无命中（退出码 1）。真值只在 `tools/frame_follow_replay.py` 离线合成观测与读数中使用。**R1@K2返工**：AC-22 修订 1 已落实——`_build_standoff_runtime` 不再读取或校验路线，标定只来自显式 `ground_plane_y_m`；新增静态用例 `TruthIsolationTests.test_standoff_construction_path_reads_no_route_or_evaluator_output`（只钉三个新构造函数，修复前 `route` 命中、修复后过）与接线回归（见 AC-18）；本行 grep 重跑仍无命中（退出码 1） |
| AC-23 | artifact: `docs/evidence/P1-ENG-FRAME-001-play.md`「安全读数」§T / §P（未建） | **NOT_RUN**：同 AC-21。**R1@K2返工**：仍 **NOT_RUN**；读数工具的场景绑定缺口（复核 R1-2）已在 Play 前闭合，见「R1@K2返工」节 |
| AC-24 | cmd: `.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-FRAME-001-tests.log 2>&1; tail -n 3 docs/evidence/P1-ENG-FRAME-001-tests.log`；artifact: `Logs/P1-ENG-FRAME-001-editmode-rework.xml`（C1@K2返工 终跑，现行）、`Logs/P1-ENG-FRAME-001-editmode.xml`（K2补跑 终跑）、`Logs/P1-ENG-FRAME-001-editmode-run1.xml`（K2补跑 首跑）；命令见下「Unity Edit Mode」 | Python 全套见下「测试」。**Unity Edit Mode 全套**：首跑（代码 = `$PREV`）total 281 / passed 278 / failed 3 / skipped 0，XML sha256 `42e95916b04075143b8aa110afda0b03260962712fb1bbda00a92bf179e8cb25`；终跑（代码 = `$FIX`，`Assets/` 无未提交改动）total 282 / passed 282 / failed 0 / skipped 0，XML sha256 `524a88474adc36bebc1a3c5784daa840a8967245d76458e9ae0c555481bfd281`。`Logs/` 为 Unity 生成物目录、不入库，只在本机。**C1@K2返工（现行停点证据）**：Edit Mode 全套终跑（代码 = `$RWFIX`，`Assets/` 无未提交改动）total 284 / passed 284 / failed 0 / skipped 0，`Logs/P1-ENG-FRAME-001-editmode-rework.xml` sha256 `662a58872840ce058c7e7173affa3a7f3503f0e82c2294ec425465d8265bf70c`；Python 全套覆盖写 `docs/evidence/P1-ENG-FRAME-001-tests.log`：`Ran 2057 tests`、`FAILED (failures=4, errors=9, skipped=19)`，基线 13 项逐名相同，新增失败 0（「C1@K2返工」节）。**R1@K2返工（现行停点证据）**：Python 全套（代码 = `$R1FIX`）`Ran 2061 tests`、`FAILED (failures=4, errors=9, skipped=19)`，基线 13 项逐名相同，新增失败 0；未改 C#，Edit Mode 不重跑（`$R1CAND..$R1FIX` 对 `Assets/` 零差异；现行 Edit Mode 证据仍为 `Logs/P1-ENG-FRAME-001-editmode-rework.xml` 284/284 及复核副本独立重跑） |
| AC-25 | cmd: `git diff --name-only "$BASE".."$CAND"` 与提案 §4.1 归属表比对 | 见下「文件集」：§4.1 内 22 个路径 + 流程必写 2 个（IR-9）；K2补跑 改动 10 个路径均在其中、未新增路径；`$BASE..$CAND` 另含 supervisor 派发日志 `docs/evidence/supervisor-dispatch.jsonl`（supervisor 派发登记/核销提交写入，非实现角色改动，COORD-015 流程文件），合计 25 个路径；无 `*.unity`、prefab、`*.meta`、`language_loop.py`、ACQ 文件、`tools/check_*.py`、工作流文件；`PROJECT_BRIEF.md` 只改 §9.3 第 9 项所列的系留描述与缺省配置段。**C1@K2返工**：本轮实现改动 6 个路径（`ScenarioConfig.cs`、`TetheredTrackingEditModeTests.cs`、`controller/scenario_tether.py`、`tests/test_frame_tether_switch.py`、本文件、`-tests.log`）全在 §4.1，另改状态板（IR-9）；无新文件、无 `.meta`。`$BASE..$CAND` 现为 27 个路径，较 C1 时多出的 2 个均非实现角色写入：提案（接受角色 `C1@K2` 核对表提交）与 `docs/authorizations.md`（supervisor 全局代录提交），可用 `git log --format='%h %s' "$BASE".."$CAND" -- <路径>` 核对其提交归属。**R1@K2返工**：本轮实现改动 9 个路径——Part P 代码/测试 6 个（`controller/standoff_planner.py`、`controller/track_loop.py`（仅 `_build_standoff_runtime`）、`tools/frame_follow_replay.py`、`tests/test_standoff_planner.py`、`tests/test_track_loop.py`、`tests/test_frame_follow_replay.py`）+ 本文件、`-tests.log` + 状态板（IR-9）；无新文件、无 `.meta`、无 `Assets/`、无 Part T 文件。`$BASE..$CAND` 现为 32 个路径，较「C1@K2返工」交接时的 27 个多出的 5 个均非实现角色写入：复核文件、`docs/implementation-status.md`（接受角色 R1-3 记债）、`docs/roles/supervisor.md`、`docs/workflow-changelog.md`、`docs/evidence/COORD-015-codex-launch-form.md`（协调批次/supervisor），可用 `git log --format='%h %s' "$BASE".."$CAND" -- <路径>` 核对归属 |
| AC-26 | artifact: 本文件 §T / §P / §共用 | 本文件 |

### 测试（COORD-009：开发期 focused；停点全套一次，不带 `-v`）

- 解释器：`.venv-yoloe/bin/python`（3.12，lap 0.5.13 / numpy / cv2；只读使用，未装包）。本机没有 `~/TetheredDroneTracking-full`，
  故状态板「跟踪器相关测试用数据根」一条在本机无法照做，按派发指令用仓库 `.venv-yoloe`。该环境 site-packages 里有一个同名
  `tests` 包，`python -m unittest tests.test_x` 会解析错，focused 用 `-m unittest discover -s tests -p test_x.py`。
- 基线（开工前、未改任何文件时在主树同一解释器跑一次全套，输出留会话暂存、不入库）：`Ran 1984 tests`，
  `FAILED (failures=4, errors=9, skipped=19)`。
- 停点全套（`docs/evidence/P1-ENG-FRAME-001-tests.log`）：`Ran 2054 tests`，`FAILED (failures=4, errors=9, skipped=19)`。
  新增 70 项（`test_frame_tether_switch` 15、`test_frame_follow_replay` 15、`test_standoff_planner` 32、`test_track_loop` +4、
  `test_track_experiment` +4）全部通过。
- **失败集合与基线逐名相同（13 项），本批新增失败：0。** 基线既有：
  - errors 9：`test_ambiguous_manifest_hard_fails_without_parent_fallback`、`test_m3_armA_family_binds_via_run_snapshot`（`test_dist_data_round8`）；
    `test_archived_decision_a_recomputes_identically`（`test_rate3_protocol`）；`test_eng_sft_audit`、`test_eng_sft_build`、`test_eng_sft_cloud`、
    `test_eng_sft_evaluate`、`test_language_k_binding`（模块导入失败）；`test_pinned_opencv_csrt_initializes_and_updates`（`test_trackers`）。
  - failures 4：`test_arm_a_truth_patterns_cover_exactly_five_files`、`test_void_run_truth_pattern_matches_exactly_one_file`、
    `test_zero_unmatched_and_zero_multi_matched_jpg`（`test_dist_data_round4`，依赖主树 `runtime/` 现状）；
    `test_cli_runs_pinned_csrt_to_a_versioned_summary`（`test_track_loop`）。
- 日志末尾 3 行不是汇总行（测试打印与汇总交错写入），汇总行在 `Ran 2054 tests` 处；AC-15 各夹具计数行同在日志中。
- **K2补跑 停点全套**（代码 = `$FIX`，同一解释器，AC-24 命令逐字，覆盖写 `docs/evidence/P1-ENG-FRAME-001-tests.log`）：`Ran 2054 tests`，
  `FAILED (failures=4, errors=9, skipped=19)`；失败集合与上列基线 13 项逐名相同，**新增失败 0**；本轮未增删 Python 用例（`test_frame_follow_replay`
  15 项改了金标准字面值，全过）。开发期 focused：`-m unittest discover -s tests -p test_frame_follow_replay.py` 15 项 OK。
  （此前一次带 `/usr/bin/time` 包装的启动被即时中止并按原命令重跑；本机重启前未跑全套。）
- **R1@K2返工 停点全套**（代码 = `$R1FIX`，同一解释器，AC-24 命令逐字，覆盖写 `docs/evidence/P1-ENG-FRAME-001-tests.log`，**现行证据**）：`Ran 2061 tests`，
  `FAILED (failures=4, errors=9, skipped=19)`；失败集合与上列基线 13 项逐名相同，**新增失败 0**；新增 4 项（`test_standoff_planner` 32 → 34、
  `test_track_loop` 26 → 27、`test_frame_follow_replay` 15 → 16）全过。
- **C1@K2返工 停点全套**（代码 = `$RWFIX`，同一解释器，AC-24 命令逐字，覆盖写 `docs/evidence/P1-ENG-FRAME-001-tests.log`，已被 R1@K2返工 覆盖）：`Ran 2057 tests`，
  `FAILED (failures=4, errors=9, skipped=19)`；失败集合与上列基线 13 项逐名相同，**新增失败 0**；新增 3 项（`test_frame_tether_switch` 15 → 18）全过。
- `runtime/` 核对：全套前建参照文件，全套后 `find runtime -newer <参照>` 只命中 `runtime` 目录节点本身，目录内无文件变化（与 K2 首交时同一现象）；
  Edit Mode 与回放不触及 `runtime/`。

### Unity Edit Mode（`K2补跑` 已执行；C1@K2返工 三次运行见「C1@K2返工」节）

开工与每次启动前 `pgrep -fl 'Unity.app/Contents/MacOS/Unity'` 无编辑器进程；全部为 batchmode（非 Play、零 ID），结果与日志写 `Logs/`
（Unity 生成物目录、不入库），不写共享 `runtime/`。全套命令（首跑、终跑逐字相同）：

```bash
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  -batchmode -nographics -projectPath ~/TetheredDroneTracking \
  -runTests -testPlatform EditMode -testFilter TetheredTracking.Tests \
  -testResults ~/TetheredDroneTracking/Logs/P1-ENG-FRAME-001-editmode.xml \
  -logFile ~/TetheredDroneTracking/Logs/P1-ENG-FRAME-001-editmode-unity.log
```

| 次序 | 代码（运行时解析） | 结果 | 产物（本机 `Logs/`） |
|---|---|---|---|
| 首跑（2026-10-01 15:58Z） | `Assets/` 与 `$PREV` 逐字节相同（其后只有 supervisor 派发日志提交），工作树干净 | 281 / 278 过 / 3 败 / 0 跳过 | `P1-ENG-FRAME-001-editmode-run1.xml`（首跑后改名保存）、`…-run1-unity.log` |
| 诊断 ×2 | 首跑代码 + 一次性诊断用例 `ZZDiag_DumpGoldenTrajectories`（`-testFilter` 只跑它，导出逐步状态；跑后逐字节移除，测试文件 sha256 前后相同，未入库） | 均 1/1 过；第 1 次导出在暂存目录、因本机重启丢失，第 2 次（修复后代码，plant 未改）存 `Logs/` | `P1-ENG-FRAME-001-plant-dump.txt`（10,400 行，sha256 见 E-2） |
| 中间跑（16:17Z） | 修复后未提交工作树 | 282 / 282 过 | 已被终跑覆盖 |
| **终跑（16:36Z）** | `$FIX`（K2补跑 修复提交），`git status --porcelain -- Assets` 为空 | **282 / 282 过 / 0 败 / 0 跳过** | `P1-ENG-FRAME-001-editmode.xml`、`…-unity.log`（无 `error CS`） |

本批 Edit Mode 用例 15 个（全在 `TetheredTrackingEditModeTests.cs`，无新 C# 文件、无新 `.meta`）逐名结果（首跑 → 终跑）：

- `ScenarioTetherSwitchTests`：`ClosedFixtureSet_VerdictsMatchThePythonParser` 过 → 过；`ExistingScenarioFiles_NormalizeBitwiseAsBeforeAndStayTethered` 过 → 过；
  `VersionedDefault_IsTheUntetheredScenarioAndLoadOrderIsUnchanged` 过 → 过；`SerializerMaterialisedGeofence_MeansAbsentButPartialFenceIsRefused`（K2补跑 新增）— → 过。
- `TetheredDronePlantTests`：`Step_TetherEnabledMatchesLegacyReferenceBitwise` 过 → 过；`Step_TetheredGoldenVectors` **败** → 过；`Step_UntetheredGoldenVectors` 过 → 过；
  `Step_TetherOff_CanPassThirtyFiveMetresFromAnchor`、`Step_TetherOff_NeverReportsTetherSaturated`、`Step_TetherOff_AltitudeBandIsNotCappedByTetherLength`、
  `Step_TetherOff_SpeedAndAccelerationClampsUnchanged`、`Step_TetherOff_StaysInsideGeofence` 均 过 → 过。
- `TetherBootstrapConstructionTests`：`TetherLine_IsCreatedOnlyWhenTetherEnabled_WithUnchangedParameters`、`AnchorMarkerAndOcclusionRoots_DoNotDependOnTheTetherSwitch` 过 → 过。
- `FrameProtocolInvariantTests`：`SensorFrameMetadataV3_FieldSetIsUnchanged` 过 → 过。

既有用例：首跑败 2 条（E-1），终跑全过；`TetheredDronePlantTests` 既有 2 条两次均过。Unity 未改写任何已跟踪文件
（每次运行后 `git status --porcelain` 只有本轮自改文件；`ProjectSettings/`、`Packages/packages-lock.json` 无改动），无需 `git restore`。

### 离线编译（非测试证据）

用 Unity 自带 Roslyn（`…/Resources/Scripting/NetCoreRuntime/dotnet …/DotNetSdkRoslyn/csc.dll`）按 Unity 生成的
`Library/Bee/artifacts/200b0aE.dag/TetheredTracking.Runtime.rsp` 与 `TetheredTracking.EditModeTests.rsp`（输出改到会话暂存目录、
EditModeTests 引用新编 Runtime）编译：两程序集 **0 错误**，改动的 4 个 C# 文件 **0 警告**。只证明能编译，不证明行为。

### 文件集（AC-25）

§4.1 内：`Assets/TetheredTracking/Scripts/{ScenarioConfig,TetheredDronePlant,TetheredScenarioBootstrap}.cs`、
`Assets/TetheredTracking/Tests/EditMode/TetheredTrackingEditModeTests.cs`、`controller/{scenario_tether,standoff_planner,track_loop}.py`、
`config/{scenario.untethered,p1-eng-frame-001-body}.json`、`tools/{run_track_experiment,frame_follow_replay}.py`、
`tests/{test_track_experiment,test_track_loop,test_frame_tether_switch,test_standoff_planner,test_frame_follow_replay}.py`、
`docs/evidence/P1-ENG-FRAME-001-{play-ops.md,replay.json,replay.md,K2-handoff.md,tests.log}`、`PROJECT_BRIEF.md`。
流程必写（IR-9）：`docs/current-status.md`、`docs/evidence/P1-ENG-FRAME-001-ledger.json`。
supervisor 写入（不属实现角色）：`docs/evidence/supervisor-dispatch.jsonl`；`docs/current-status.md` 亦含 supervisor 检查点改动。
K2补跑（`$PREV..$CAND`，不计 supervisor 提交）：`Assets/TetheredTracking/Scripts/ScenarioConfig.cs`、`Assets/TetheredTracking/Tests/EditMode/TetheredTrackingEditModeTests.cs`、
`tools/frame_follow_replay.py`、`tests/test_frame_follow_replay.py`、`config/p1-eng-frame-001-body.json`、`docs/evidence/P1-ENG-FRAME-001-{replay.json,replay.md,K2-handoff.md,tests.log}`、`docs/current-status.md`；
无新 `*.meta`、无新文件。
**C1@K2返工**（`$C1CAND..$CAND` 中实现角色提交）：`Assets/TetheredTracking/Scripts/ScenarioConfig.cs`、`Assets/TetheredTracking/Tests/EditMode/TetheredTrackingEditModeTests.cs`、
`controller/scenario_tether.py`、`tests/test_frame_tether_switch.py`、`docs/evidence/P1-ENG-FRAME-001-{K2-handoff.md,tests.log}`、`docs/current-status.md`；无新 `*.meta`、无新文件。
同区间另有接受角色（提案核对表）与 supervisor（派发日志、`docs/authorizations.md` 全局代录）的提交，不属实现改动。
**R1@K2返工**（`$R1CAND..$CAND` 中实现角色提交）：`controller/standoff_planner.py`、`controller/track_loop.py`、`tools/frame_follow_replay.py`、
`tests/{test_standoff_planner,test_track_loop,test_frame_follow_replay}.py`、`docs/evidence/P1-ENG-FRAME-001-{K2-handoff.md,tests.log}`、`docs/current-status.md`；
全为 §4.1 Part P / 共用路径与状态板（IR-9），无 `Assets/`、无 Part T 文件、无新文件、无 `.meta`。同区间另有复核角色（复核文件）、接受角色（提案「待裁定」、
`docs/implementation-status.md` R1-3 记债）与 supervisor/协调批次（派发日志、`docs/authorizations.md`、`docs/roles/supervisor.md`、`docs/workflow-changelog.md`、
`docs/evidence/COORD-015-codex-launch-form.md`）的提交，不属实现改动。

### 复核范围（给 `R2@K2`：R1@K2返工 修复；不经核对轮）

- 修复触及行（`git diff "$R1CAND".."$R1FIX" -- Assets controller config tools tests`，6 个路径，全属 Part P）：
  `controller/standoff_planner.py::_position_sigma`（R1-1）、`tools/frame_follow_replay.py::_manifest_scenario_binding/analyze_run`（R1-2，含来源路径只记录不比对的处理，
  见「R1@K2返工」已知限制 1）、`controller/track_loop.py::_build_standoff_runtime`（AC-22 修订 1 ①②，冻结 `_build_body_runtime` hold/threshold 路径零改动）。
- 三条阻断/澄清的修前红/修后绿：`git revert -n "$R1FIX"` 后分别跑 `StandoffContractTests.test_large_finite_covariance_holds_without_raising`（R1-1）、
  `AnalyzeRunTests.test_analyze_run_refuses_a_scenario_that_differs_from_the_manifest`（R1-2）、
  `StandoffWiringTests.test_standoff_ground_plane_is_explicit_finite_and_route_independent` 与
  `TruthIsolationTests.test_standoff_construction_path_reads_no_route_or_evaluator_output`（AC-22 修订 1）。回归用例单独在 `$R1TEST`（先于修复），
  `$R1FIX` 只含 `controller/`、`tools/` 三个文件，故 `git revert -n "$R1FIX"` 只撤回代码、保留新测试。
- 回归夹具来源：R1-2 的 manifest 由 `_build_body_runtime` + `RunLogger` 生产路径产出；truth 旁车为合成（Unity 写出，无 Python 生产写盘函数）。
- 未变而须核对的：回放证据与 FRAME 配置零差异（`--check` 一致、选参 C3）；`$R1CAND..$R1FIX` 对 `Assets/` 零差异（Edit Mode 不重跑的依据）。

### 复核范围（给 `R1@K2`；按 Part 分节）

- §T：三个 Unity 脚本（`ScenarioConfig.Normalize` 有缆分支逐字、`ApplyTetherKeyPresence` 与 JsonUtility 缺字段行为、`TetheredDronePlant.Step` 有缆分支逐字 + 围栏叠加、bootstrap 只增两行赋值与 `CreateTetherLine`）、Edit Mode 新用例与 `LegacyPlantReference` 逐字性、`controller/scenario_tether.py`、`track_loop.py` 的 `threshold` 分支开关、`config/scenario.untethered.json` 差异闭集、`run_track_experiment.py` 常量。
- §P：`controller/standoff_planner.py`（第 1–6 步顺序、IR-1…6）、`track_loop.py` 的 `build_standoff_planner`/`_estimator_from_body_config`/`_build_standoff_runtime`/CLI、`tools/frame_follow_replay.py`（plant 镜像与 Unity 语义逐项对应、IR-7 模型选择、选参规则、`--analyze-run`）、`config/p1-eng-frame-001-body.json` 与证据 sha 绑定、操作单。
- §共用：真值隔离（AC-22）、文件围栏（AC-25）、`PROJECT_BRIEF.md` 措辞。
- K2补跑 增量（`$PREV..$FIX`）：`ScenarioConfig.NormalizeGeofence` 哨兵读法（IR-13、E-1）与新回归用例；`tools/frame_follow_replay.py` 镜像存储时舍入（E-2）逐式对照 Unity `Vector3.ClampMagnitude`/`MoveTowards`/`magnitude` 与 `TetheredDronePlant.Step`；金标准字面值 C#/Python 同值；回放证据重生成与配置 sha 绑定。
- C1@K2返工 增量（`$C1CAND..$RWFIX`）：`ScenarioConfig.FromJsonStrict`/`ReadTetherKeys`/`GeofenceBound`/`JsonText`（只读 `drone` 直接成员、字符串转义、同名键取最后一个、结构畸形拒绝、数值词法与 float32 溢出）、`[NonSerialized]` 对 JsonUtility 原始解析与 `ToJson` 往返的影响（「C1@K2返工」已知限制 1–2）、`NormalizeGeofence` 删除哨兵后的拒绝路径；C# 三条新用例与 Python 同名同文本夹具逐条一致；既有 17 场景逐位回归与两条既有用例。

### Unity 用例 / 观察点（`R1@K2` 通过且接受角色放行后；不在本轮）

`docs/evidence/P1-ENG-FRAME-001-play-ops.md`：Play 前移开 ACQ 残留 `runtime/scenario_config.json`（只移入 hold）；Console 须出现
`Loaded tethered scenario 'deterministic-loop-untethered' from …/config/scenario.untethered.json`；用户目检机身是否持续跟随、有无起停；
`--analyze-run` 产出 R-1…R-7 与 AC-23 安全读数。

### 未验证项与已知限制

1. Edit Mode 已跑（K2补跑 终跑 282/282；C1@K2返工 终跑 284/284；R1@K2返工 未改 C#、未重跑）；无缆新路径的 Unity Play 证据（AC-21/AC-23）未跑，待 `R2@K2` 通过与 §4.5 放行。Edit Mode XML、plant 逐步导出只在本机 `Logs/`（不入库），复核可按「Unity Edit Mode」小节命令重跑。
2. （原 K2 记录「`ApplyTetherKeyPresence` 以 JSON 文本判键存在」）**C1@K2返工 已修**：只读 `drone` 直接成员（`TetherKeysOutsideTheDroneObject_MeanMissing`）；本轮新增的已知限制见「C1@K2返工」节「已知限制」1–5。
3. 回放是运动学 + 合成观测：估计用框底中心地面交点，导致真实跟随距离比 d\* 偏大约 2 m（C3 第二圈 p50 14.1 m）；不含渲染、检测、跟踪器失败与遮挡；估计器先验未标定（提案 §6）。
4. 有缆模式下机身贴可达圆滑移时，若同帧发生避障/走廊缩短，float32 位置舍入可能触发 `+boundary_blocked` hold（IR-3 守卫）；只影响有缆对照读数。
5. 新 main 上 `language_loop` 的无覆盖回退仍指旧缺省，与 Unity 回退不一致（提案 §9.1 已披露，恢复 ACQ 时处理）；`runtime/scenario_config.json`（ACQ 残留）本轮未动。
6. 回放 `--check` 全网格重跑：K2 首交时约 7–10 分钟，K2补跑 实测 84 s（重生成 285 s，重启后后台负载不同）；冻结阈值规划器的走廊检查是主要耗时，未改冻结代码。
7. 镜像的「存储时舍入」模型由 9 条序列 10,400 个状态逐位核实，属对本机 Unity 6000.4.1f1（Mono、arm64）运行时的经验模型；换运行时（IL2CPP、其他架构）未验证，Edit Mode 金标准用例会在偏差 > 1e-5 时报警。

### 消耗对账（`docs/evidence/P1-ENG-FRAME-001-ledger.json`）

scenario ID 新建 1（`deterministic-loop-untethered`，随 `config/scenario.untethered.json`）；session/run ID 0；Unity Play 0；
权重加载 0；GPU·h / 付费 API / VLM 0；下载 / pip 安装 / 远端 0。本批代码与工具未写、未移、未删 `runtime/` 下任何文件（ACQ 残留 `runtime/scenario_config.json` 保持原样；本批新增测试与回放只用临时目录）。
核对：`find runtime -newer <派发开始时刻参照文件>` 只命中 `runtime` 目录节点本身（mtime 落在停点全套测试运行期间，即某个既有用例在
`runtime/` 下临时建删条目），目录内没有任何文件在派发后被修改；本批新增或改动的 5 个测试模块逐个单跑前后该目录 mtime 不变，
具体是哪条既有用例未定位。K2 首交时 Edit Mode batchmode 0 次。

**K2补跑**（两次派发合计）：Edit Mode batchmode 5 次（全套 3、诊断 2；非 Play、零 ID，不计信封）；scenario/session/run ID 新建 0；Unity Play 0；权重加载 0；
GPU·h / 付费 API / VLM 0；下载 / pip 安装 / 远端 0；`docs/evidence/P1-ENG-FRAME-001-ledger.json` 未改。未写、未移、未删 `runtime/` 下任何文件（Edit Mode 结果写 `Logs/`）；
核对见「测试」末条。

**C1@K2返工**：Edit Mode batchmode 3 次（红跑 1 次只跑 `ScenarioTetherSwitchTests`、全套 2 次；非 Play、零 ID，不计信封）；scenario/session/run ID 新建 0
（既建 `deterministic-loop-untethered` 复用）；Unity Play 0；权重加载 0；GPU·h / 付费 API / VLM 0；下载 / pip 安装 / 远端 0；
`docs/evidence/P1-ENG-FRAME-001-ledger.json` 未改。未写、未移、未删 `runtime/` 下任何文件（只读核对 ACQ 残留覆盖文件为严格 JSON）；
Python 全套前后 `find runtime -newer <参照>` 只命中目录节点本身。Unity batchmode 与 Python 全套串行执行，未并发。

**R1@K2返工**：Edit Mode batchmode 0 次；scenario/session/run ID 新建 0；Unity Play 0；权重加载 0；GPU·h / 付费 API / VLM 0；下载 / pip 安装 / 远端 0；
`docs/evidence/P1-ENG-FRAME-001-ledger.json` 未改。未写、未移、未删 `runtime/` 下任何文件（新回归只用临时目录）；回放 `--check` 与 Python 全套串行执行，
全套前后 `find runtime -newer <参照>` 只命中目录节点本身。
