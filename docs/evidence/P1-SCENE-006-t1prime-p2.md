# P1-SCENE-006 — T1′(v2) 平价重定，实现阶段 T 证据

- Work ID：`P1-SCENE-006`
- 角色：实现（implementation，Claude Code `/implement` 备用入口）
- 日期：2026-08-04
- 上游合同：`docs/proposals/P1-SCENE-006-t1prime-parity-redirection.md`
  revision 2 正文 + §15 的 BC-P2-1–8（Acceptance round 3 接受，设计
  v0.3.15）；**§16 的 BC-P2-9–11**（Acceptance 对阶段 T 的
  `REVISION_REQUESTED`，2026-08-05，设计 v0.3.16）。
- 批次处分：**`T1P2_PROMPT_LAW_UNSATISFIABLE`（BC-P2-5 零额度终态）**。
- 轮次：第 1 轮（2026-08-04）实现 + 首次选择运行；第 2 轮（2026-08-05）
  按 BC-P2-9–11 有界返工并重跑全部证据。

## 0. 一句话结论

阶段 T 的代码、工件与测试全部落地，prompt 律 v2 选择工具在冻结几何上
跑出**空 `E`**：`|D| = 52` 全员 `OK`（无保真矛盾），但 warmup 池
`[0, 10]` 没有任何一帧同时满足不截断、尺度带与离轴带。按 BC-P2-5，
选择工件已生成并提交、`selected_tick: null`、**零执行额度、无诊断帧、
无稳定候选、无 Review、无正式执行**，工作项交回 Acceptance/Ideation。

BC-P2-9–11 的返工已完成（§6）：Unity EditMode **246/246 全绿**，
Python **339 项 / 仅既有 F3**，选择工件重新生成后可由严格 RFC 8259
解析器读取，且逐个数字与返工前完全一致。

## 1. 选择结果（`docs/evidence/P1-SCENE-006-prompt-selection-p2.json`）

`status` / `terminal` = `T1P2_PROMPT_LAW_UNSATISFIABLE`，
`selected_tick` = `null`，`diagnostic_tick`（k_diag）= `400`。

### 1.1 测量域 `D_V`（BC-P2-4 前置保真：通过）

| 项 | 值 |
|---|---|
| 测量 tick 数 | 106（`k = 15, 20, …, 540`，逐字未动） |
| `D_V = {k ∈ M : V(s_k) = 1}` | **52** |
| 全员 `target_box_status = OK` | **是**（`non_ok_members = []`） |
| 独立重数的分母断言 | 52 == 52，`denominator_assertion_ok = true` |

`|D| = 52` 与旧灰跑 `4/52` 的目标分母一致——分母域没有被本 amendment
改动，改的只有提示帧选取律。

### 1.2 域导出的两条 type-7 带（无手选端点）

| 带 | q05 | q95 |
|---|---|---|
| `min_side_px` | `48.67423629760742` | `106.98741378784179` |
| `applied_off_nadir_deg` | `43.78608341217041` | `45.0` |

域实测范围：`min_side` `25.088 – 107.791` px；离轴 `42.455 – 45.0`°
（52 个样本只有 6 个不同离轴值，绝大多数钉在 45° 钳位）。不可见 tick 的
`min_side_px` 与四边余量按 BC-P2-10 写作 JSON `null`（无投影框即无该
数值），不是有限哨兵。

### 1.3 warmup 池逐 k 的 `E` 全表

| k | V | status | `min_side_px` | applied 离轴 | 左余量 px | 首个不满足子句 |
|---|---|---|---|---|---|---|
| 0 | 0 | `TARGET_NOT_VISIBLE` | `null` | 42.543 | — | `a_visible` |
| 1 | 0 | `TARGET_NOT_VISIBLE` | `null` | 42.554 | — | `a_visible` |
| 2 | 1 | `OK` | 143.2294 | 42.587 | **0.0** | `c_untruncated` |
| 3 | 1 | `OK` | 123.4808 | 42.641 | 141.0 | `d_scale_band` |
| 4 | 1 | `OK` | 88.8857 | 42.716 | 253.8 | `e_off_nadir_band` |
| 5 | 1 | `OK` | 90.9934 | 42.812 | 253.1 | `e_off_nadir_band` |
| 6 | 1 | `OK` | 92.9862 | 42.929 | 252.6 | `e_off_nadir_band` |
| 7 | 1 | `OK` | 94.8588 | 43.066 | 252.1 | `e_off_nadir_band` |
| 8 | 1 | `OK` | 96.6044 | 43.223 | 251.7 | `e_off_nadir_band` |
| 9 | 1 | `OK` | 98.2188 | 43.398 | 251.3 | `e_off_nadir_band` |
| 10 | 1 | `OK` | 99.6988 | 43.591 | 251.1 | `e_off_nadir_band` |

三点事实供 Acceptance/Ideation 裁定时使用（**不是**修改协议的提议）：

1. **旧 `k* = 2` 被机械拒绝，方向与 F23 完全一致**：左边缘余量
   `0.0 px`（截断），`min_side 143.23 px` 高于域 q95 `106.99`。新律确实
   关掉了 F23 指出的两处失配。
2. **空集来自离轴带，且是近失**：k = 4…10 只差在离轴——k = 10 的
   `43.591°` 与 q05 `43.786°` 相距 `0.195°`。§6.2 预判的"warmup 结构性
   偏正 + D 钉在钳位角"确实发生了，量级比预期小。
3. **k = 3 同时越尺度上界**（123.48 > 106.99）；即使离轴带放宽，k=3 仍
   出带。E 空不是单一子句造成的。

### 1.4 `applied` 离轴的口径与其无关紧要性

正文 §3.2.3(e) 写"applied 离轴角"。工件按**云台律的 `applied` 值**
（`min(requested, 45°)`，`Scene006GimbalReplay.AppliedOffNadirDeg`，与
`Update` 共用同一处定义）落数，并同时记录**实际相机位姿离轴**
`camera_off_nadir_deg` 供核对。两者在 `k ≥ 4` 与整个 `D` 上逐位相同
（云台已收敛）；只在 k = 0/1/2/3 因 `RotateTowards` 迟滞而不同
（`0.000 / 11.637 / 23.052 / 33.940` vs 上表）。

**换用相机位姿口径不会改变任何结论**：k=0/1 仍在 (a) 失败，k=2 仍先在
(c) 失败，k=3 的 `33.940°` 同样出带且仍先在 (d) 失败，k≥4 数值相同。
`camera_off_nadir_deg` 在 k=2 的 `23.052°` 也复现了复核 F23 记录的
`23.1°`。因此本口径选择不构成需要 Acceptance 先行裁定的歧义；如
Acceptance 仍希望改口径，改一行常量后重跑即可（零额度）。

## 2. 实现内容与文件

| 文件 | 内容 |
|---|---|
| `Assets/TetheredTracking/Scripts/TargetVisualFactory.cs`（新） | §3.1 单一生产构造源：`BodyColor`/`RoofColor`、`readonly struct Build`（6 字段 + 显式构造器）、`AddTargetVisual(Transform)`；建两块 cube、显式覆写 local TRS、走冻结材质路径；不清理 collider、不设 `hideFlags` |
| `Assets/TetheredTracking/Scripts/TetheredScenarioBootstrap.cs` | `AddCarVisual` 改为纯委托＝工厂调用 + 两行 `Destroy`，再无构造语句 |
| `Assets/TetheredTracking/Editor/Scene006/Scene006SceneRig.cs` | `CreateTargetReplica` 改为工厂调用 + `DestroyImmediate` 两 collider + 两个 `DontSave` + `TargetRenderers = {Body, Roof}`；`AddReplicaCube` 删除 |
| `.../Scene006AppearanceContract.cs`（新） | `Describe`（读实物）与 `Expected`/`Verify`/`Compare`（Editor 侧冻结 oracle，不引用工厂常量）；RGBA 逐分量 `1e-6` 表示容差，其余字段精确 |
| `.../Scene006Json.cs`（新，第 2 轮） | BC-P2-10 序列化边界：把 `JsonUtility` 的裸 `NaN`/`Infinity` 值 token 改写为 JSON `null`（字符串字面量内不动）、反向还原、写盘前 fail-closed 复扫 |
| `.../Scene006PromptSelection.cs`（新） | prompt 律 v2 全部：重放、`D_V`、逐成员 `OK` fail-closed、type-7 带、`E` 五子句、`k*′`、`k_diag`、P3 逐位交叉核对、工件序列化（`selected_tick: null`）与 `Compare` |
| `.../Scene006ProbeRenderer.cs` | v3 manifest（`CandidateManifestP2`）＋`CandidateExtrasP2`；prompt 帧改由**已提交的 `k*′`** 指定；写盘前重算选择并逐行比对、读取 `target_appearance`、再校场景哈希 |
| `.../Scene006CandidateProbe.cs` | `ProbeIdP2`/`ProbeDirectoryP2`、`FrozenCandidateConfigSha256`、冻结路径集 v2（九条 + `Assets/TetheredTracking/Scripts`）、`ResolveToolCommit` 路径集重载、`CandidateIdentity.T6` |
| `.../Scene006GimbalReplay.cs` | 抽出 `AppliedOffNadirDeg`，`Update` 改用它（算术不变） |
| `.../Scene006EvidenceGenerator.cs` | `RunPromptSelection`（本批实际运行）、`RunCandidateProbeP2`（阶段 P 五项预检 + 阶段 X 额度边界，本批**未运行**） |
| `tools/run_scene006_probe.py` | v3 schema、`TARGET_APPEARANCE_CONTRACT` Python 冻结常量与比对、`prompt_eligibility` 校验、`|D|` 回验、F20 `capture_identity` 回显 |
| `Tests/EditMode/Scene006TargetParityEditModeTests.cs`（新）、`Scene006PromptSelectionEditModeTests.cs`（新）、`Scene006TestLog.cs`（新） | oracle 1/2、F21 真实配置钉、路径集 v2、prompt 律算术与 fail-closed；第 2 轮加颜色容差双向 mutation、严格 JSON 扫描器与工件往返、逐条 `LogAssert.Expect` |
| `tests/test_scene006_probe.py` | v3 happy path、外观失配、身份/资格违规 20 余例 |
| `docs/evidence/P1-SCENE-006-batch2-config.md` | F22 口径更正（仅 §3.4 一处 + 一段更正注记） |

**未触碰**：`config/`（零字节变化）、场景文件、`docs/proposals/`、
`docs/phase1-single-drone-design.md`、`docs/reviews/`、
`docs/unity-test-log.md`、`docs/authorizations.md`、M3′/DETECT/主指标
相关文件。旧 `runtime/p1-scene-006/probe-candidate-vfov40/` 与
`docs/evidence/P1-SCENE-006-probe-candidate-40deg.json` 只读未动。

> 退役路径提醒：`RunCandidateProbe`（v1 候选入口）本批**未做任何逻辑
> 修改**，但由于替身现在被上色，它的渲染已不再是灰色协议，**不得再
> 运行**；新旧目录永不合并（§3.5.1）。

## 3. 实际运行的命令与结果

### 3.1 Unity EditMode（6000.4.1f1，无头）

```bash
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  -batchmode -nographics -projectPath ~/TetheredDroneTracking \
  -runTests -testPlatform EditMode -testFilter TetheredTracking.Tests \
  -testResults runtime/test-results/p1-scene-006-editmode-p2t.xml \
  -logFile runtime/test-results/p1-scene-006-editmode-p2t.log
```

**246/246 全部通过**（225 既有 + 21 新增）。第 1 轮的 3 项失败由
BC-P2-9 关闭（§6）。

### 3.2 prompt 律 v2 选择（本批唯一一次工具运行）

```bash
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  -batchmode -nographics -projectPath ~/TetheredDroneTracking \
  -executeMethod TetheredTracking.Scene006.Scene006EvidenceGenerator.RunPromptSelection \
  -quit -logFile runtime/test-results/p1-scene-006-prompt-selection.log
```

退出码 0；日志末行
`[SCENE-006] prompt selection: status T1P2_PROMPT_LAW_UNSATISFIABLE,
|D| 52, k*' -1, k_diag 400`。零渲染、零 Play、零 session/run ID、零
ProbeDirectory、零检测器/嵌入器调用。

### 3.3 Python

`.venv-track/bin/python -m unittest discover -s tests` → **339 项，
1 失败 = 既有 F3**（`test_check_docs.test_compliant_minimal_status_passes`
基底破损，批次 1c 已归因协调批次 `902a72c`，与本批无关）。
`tests.test_scene006_probe` 单独 **26/26**。

### 3.4 角色写入自检

`python3 tools/check_role_writes.py --role implementation` 通过；
`python3 tools/check_docs.py` 通过。

## 4. 反调参与禁区自查

- 选择律的全部参数来源：`2.0 px` 截断余量（提案预注册的唯一手选常量）
  与 type-7 `[q05, q95]` 规则；两条带的端点由冻结几何确定性导出。
  **没有任何一个数来自 `4/52`、`16/99` 的命中、IoU、cosine 或 recall。**
- 旧工件在本批中只作历史引用（§1.3 第 1 条对照 F23），不进分母、不作
  同尺度基线、不参与任何阈值。
- 配置字节零变化：`config/scenario.p1-scene-006.json` 的 SHA-256 仍是
  `ec4154d1…c831`，由 `Scene006CandidateProbe.FrozenCandidateConfigSha256`
  在选择工具入口 fail-closed 绑定，并由 F21 测试用**独立硬编码字面量**
  单独钉住；测量帧集 `M`、样本下限 `40/40`、门值 `0.85/0.90`、
  `0.5/0.1` 字面量全部未动。
- E 空后**没有**扩池、没有改帧域、没有动场景/光学/锚点/路线/车辆/模型。

## 5. COORD-005 人眼保真记录

**尚未发生，且按 BC-P2-6 现在也不应发生**：诊断样帧只有在**非空**选择
工件提交之后才允许渲染，本批的工件是空 `E` 终态。故：

- 样帧路径：无（未渲染任何帧）。
- 确认人：无。
- 结论：**未进行**。

阶段 P 的机器可检标记常量定义在
`Scene006EvidenceGenerator.Coord005ConfirmationMarker`；本文件当前
**不含**该行，因此即便有人误启 `RunCandidateProbeP2`，也会在零额度的
`T1P2_PRECHECK_FAIL_COORD005_RECORD` 上停住。

## 6. BC-P2-9–11 返工（第 2 轮，2026-08-05）

Acceptance 对第 1 轮的裁定是 `REVISION_REQUESTED`（提案 §16），并逐条
指定了处理方式。三条全部按字面执行，范围不超出既有阶段 T。

### 6.1 BC-P2-9 — RGBA 表示容差（选项 B）

Acceptance 选了选项 B、拒绝选项 A。落实：

- **四份 oracle 的 expected 仍是作者合同**——`(0.9, 0.12, 0.1, 1)` 与
  `(0.65, 0.08, 0.07, 1)`，各自在自己的位置硬钉，没有任何一处改写成
  读回值。Python 侧连 TRS 也改回作者十进制（`1.2` 而不是
  `1.2000000476837158`），比较时先做单精度量化 `_float32`，**仍是精确
  相等**——可读性上升，严格度不变。
- **只有 RGBA 四分量**用逐分量绝对误差 `≤ 1e-6`：
  `Scene006AppearanceContract.ColorComponentTolerance`、
  测试内 `ColorComponentTolerance`、Python `COLOR_COMPONENT_TOLERANCE`
  三处各自独立声明。没有相对容差、没有舍入、没有复合范数、没有从
  actual 派生 expected。
- **mesh、shader、role、数量与全部 TRS 维持精确比对**，容差不外溢。

可证伪性证据（双向）：

| 证明 | 位置 | 结果 |
|---|---|---|
| 当前 Unity 往返误差在界内 | `Scene006TargetParityEditModeTests.ColorToleranceAdmitsRepresentationErrorAndNothingElse` | `0.12` 读回 `0.119999953`，误差 `≈4.4e-8 < 1e-6`；同时断言该往返**确实不精确**（若哪天变精确，测试会提示可以撤掉容差） |
| 界内偏差仍接受 | 同上 | `+5e-7` 通过 |
| 界外偏差必红 | 同上（C# 四分量逐个）+ `Scene006AppearanceToleranceTests.test_deviation_beyond_the_tolerance_is_caught_per_component`（Python 两块 × 四分量） | `+2e-6` 全部 `PROBE_FIDELITY_CONTRADICTION` / `AssertionException`，且只报告漂移的那一个分量 |
| 真实读回值走完整分析链 | `test_real_unity_round_trip_values_pass` | 把实测的 `0.119999953 / 0.09999997 / 0.07999996 / 0.06999998` 放进 manifest，`target_appearance_differences == []` |
| 几何不受容差影响 | `test_trs_stays_exact` | `local_scale.z` 改 `4.000001` 即失败 |

该数值只是 Unity sRGB/linear 表示边界的测试容差：样本下限 `40/40`、
recall 带 `0.85/0.90`、`0.5/0.1` 双门、T1–T6 阈值与主指标一字未动。

### 6.2 BC-P2-10 — 标准 JSON 边界

第 1 轮提交的选择工件含 **57 处裸 `NaN`**（`JsonUtility` 对非有限
float 的输出），严格 RFC 8259 解析器直接报错。这是实打实的缺陷：当时
用 Python `json.load` 验证，而它默认接受该方言，所以没被发现。

- 新增 `Scene006Json`：一个**扫描器**（不是文本替换），跟踪字符串字面量
  与转义，只把值位置的 `NaN`/`Infinity`/`-Infinity` 写成 `null`；反向把
  `null` 还原成 `NaN`，使工件往返不会把"不可用"悄悄读成 `0`。写盘前
  `ContainsNonFiniteToken` 再扫一遍，fail-closed。
- 应用于：选择工件与保真失败报告、v3 manifest、以及探针 truth 边车
  （truth 的 `target_min_side_px` 同样会是非有限值；边车文本与其
  `truth_sha256` 现在取自同一份字符串，顺带消掉了原先的重复表达式）。
- Python 侧：`read_strict_json` 用 `parse_constant` 拒绝三个方言常量；
  manifest 一律严格读，**v3** 捕获的边车也严格读；门工件用
  `json.dumps(..., allow_nan=False)` 写出。退役的 v1/v2 捕获目录里
  确实存在 43 个含 `NaN` 的边车，它们只读保留，因此非 v3 路径仍走宽松
  读取，preserved 工件不会因本次改动变得不可复算。
- 语义未变：不可用数值旁边的 `geometrically_visible` /
  `target_box_status` 本来就说明了原因，没有引入任何有限哨兵。
- 回归：`StrictJsonRewritesValueTokensAndLeavesStringsAlone`（含
  "字符串里写着 NaN/null 不许动"与未闭合字符串 fail-closed）、
  `SerializedArtifactIsStandardJsonAndKeepsUnavailableNumbers`（往返后
  `Compare` 逐行无差异）、Python `Scene006StrictJsonTests` 四项（含对
  **已提交工件本身**的严格解析回归）。

**重新生成后的工件逐数字未变**：`|D| = 52`、两条带端点、`k_diag = 400`、
11 行 `E` 表与逐 k `first_failed_clause` 全部与第 1 轮完全一致；变的只有
`NaN → null` 的表示。

### 6.3 BC-P2-11 — 不再整用例吞 error

`LogAssert.ignoreFailingMessages = true` 已删除。改为
`Scene006TestLog.ExpectMaterialInstantiation(cubeCount = 2)`：对每个
将要构建的 cube 逐条 `LogAssert.Expect(LogType.Error, <只匹配该条消息的
正则>)`。因此**任何额外 error 仍让测试失败**，而且**期望条数不足也会
失败**，连数量都被钉住。覆盖工厂合同、rig 入口、Editor 外观预检
（外观契约用例）、颜色容差用例，以及三个既有消费者用例
（`Scene006CandidateEditModeTests`、`Scene006FinalistEditModeTests`、
`Scene006EditModeTests`）。

### 6.4 返工中发现并修掉的一处真缺陷

`Scene006PromptSelection.Compare` 原先用值相等比较字符串字段。
`JsonUtility` 把 `null` 字符串写成 `""` 并读回 `""`，两者在已提交工件里
根本无法区分；于是"重算得到 `null`、工件里是 `""`"会被报成差异，让
**合法**的正式采集在写盘前中止。已改为 `CompareText`（`null` 与 `""`
等价，其余序数比较）。这是新加的严格往返测试暴露出来的。

## 7. 本批**没有**做的事（逐条对照 BC-P2-5/6/7）

- 没有渲染任何诊断样帧（BC-P2-6 要求非空工件在先）。
- 没有声明稳定候选、没有交 Acceptance 停点审计、没有交独立复核。
- 没有创建 `runtime/p1-scene-006/probe-candidate-vfov40-p2/`；正式执行
  额度**未消耗**（`RunCandidateProbeP2` 从未运行）。
- 没有扩 prompt 帧域，没有为避免空集调整任何阈值或口径。
- 没有推进 M3′、DETECT criterion 4、M1、BC-B2-8 目检。

## 8. 给复核角色的范围（若 Acceptance 决定先复核这一批）

1. `TargetVisualFactory` 是否为唯一生产构造字面量处；`AddCarVisual`
   是否为"工厂调用 + 两行 `Destroy`"纯委托；消费者差异是否不超出
   §3.1.2 穷举三类（A2）。
2. 四份 oracle 是否各自独立、是否都不从工厂/被测物/manifest/配置反读；
   `1e-6` 是否只作用于 RGBA、是否只是表示容差（§6.1）。
2b. 严格 JSON 边界是否覆盖全部写盘点，`Scene006Json` 扫描器是否会误伤
   字符串内容，往返是否不把"不可用"读成 `0`（§6.2）。
2c. `LogAssert.Expect` 是否逐条且计数精确、额外 error 是否仍会挂
   （§6.3）。
3. `Scene006PromptSelection` 是否可在一次性 worktree 独立重算并复现
   `|D| = 52`、两条带端点与 11 行 `E` 表（B1/B2）。
4. 选择工具是否确实不读旧采集目录、不读任何检测分数。
5. v3 manifest / 分析器的 fail-closed 面：`|D|` 双侧断言、
   `expected_k_star_p2`、`k*′` 最小性、F20 身份齐备性。
6. 阶段 P/X 的额度边界：正式目录创建之前的每一项检查都不消耗额度；
   目录已存在且非空时拒绝启动。
