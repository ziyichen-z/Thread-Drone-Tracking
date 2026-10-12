# P1-M3-BODY-001 批次 1a-α 实现证据

Work ID: `P1-M3-BODY-001`
Batch: **1a-α**（BC-BODY1-3 的 BC-M34-7 规划器接口独立停点批次）
Role: 实现（implementation）
Date: 2026-08-07
Gate: 稳定候选，待接受角色停点确认（BC-M34-4 (a)(b)(c) 归因 + workflow
§4.3.1 条件 5）→ 独立复核
**Stable candidate: `81202ab`**（本文件末尾的 SHA 引用与状态板补记在其后的
纯文档提交中；复核请对该候选做 `git worktree add --detach 81202ab`）

提案 §7 建议把证据拆成 `{anchor,margin,calib,run}.md`。该节自述"建议但不
强制"，BC-BODY1-3 只规定交付物不规定文件名；本批次改为一份带定位小节的
证据文件（§2 工具 1 / §3 工具 2 / §4 工具 3 / §5 走廊工件），接口契约另
成一份 [P1-M3-BODY-001-planner-contract.md](P1-M3-BODY-001-planner-contract.md)。
理由：四份文件共享同一批哈希与同一批载体事实，拆开必然漂移。

---

## 1. 消耗与边界声明

| 项 | 本批次 |
|---|---|
| Play 模式 | **零** |
| scenario / session / run ID | **零**（未创建、未消耗） |
| 配额 / API | **零** |
| Editor 侧查询 | 2 次 batchmode（BC-BODY1-10 明许） |
| 场景字节 | **未改动**，每次 Editor 运行前后 SHA-256 逐次比对 `dec58698773e8d96df300a996c0840d407d8a58d75ed5b7bd74fa1f402e2c9bf` |
| 策略 / 估计器 / `track_loop` 代码 | **零**（BC-BODY1-3：1a-α 不写） |
| 设计基线 / 提案决策 / 复核文件 / Unity 日志 / 授权账本 | 未触碰 |

---

## 2. 工具 1 — 主环线锚点支撑面/净空审计（硬门 1，BC-M34-4 (c)）

**结论：`CLEAR`。硬门通过，批次得以继续。**

| 项 | 值 |
|---|---|
| 被审锚点 | `(132.0, 0.2, 117.0)`，与 `config/scenario.default.json` `anchor_world_m` 逐位相同（审计器强制核对，不同即抛错） |
| 支撑 | 1 处，`Road Lane_01 (30)@140,120`，`surface_y_m = 0.20000043511390687` |
| 支撑高度误差 | `-4.3213367462158205e-07 m`，容差 `0.05 m` |
| 净空 | `PASS`，阻挡体 **0** |
| 场景根 / 受审障碍 | 896 / 764 |
| 工件 | `docs/evidence/P1-M3-BODY-001-anchor-audit.json`（sha256 `ebf931df…d2125`） |

### 2.1 合同参数来源

`config/p1-m3-body-001-anchor-placement.json` 的每个安全值与既有两份已接受
锚点合同**逐字节相同**（`p1-scene-003` / `p1-scene-004`）：悬停偏移 25.0、
支撑容差 0.05、锚点/悬停名义半径 1.0、走廊名义半径 0.5、净空余量 0.5。
走廊半径对 `0.5 + 0.5 = 1.0 m` 也与提案 §3.5 预注册一致。**本批次不提出
任何新安全值**，故 BC-BODY1-10「不请求用户授权」成立；`P1-SCENE-007` 悬而
未决的 `1.125 m` / `2.11 m` 争议属场景设计车道，未被本批次触碰或预判。

### 2.2 与 SCENE-003/004 的两处有意差异

1. **无点阵**。提案 §5.1 冻结锚点不动，所以这是对**一个**声明位置的裁定，
   不是寻找合法位置的搜索。迁移锚点属场景设计变更，不在本 work ID 范围。
2. **高程是被检项而非推导项**。SCENE-004 推导高程是因为它在**创作**新锚点；
   这里 scenario 字节已存在，审计的职责是判定它是否被支撑。

几何原语全部复用 `P1Scene003AnchorAuditor`（`TransformFootprint`、
`StrictlyInsideConvex`、`StrictlyInsideSurface`、`DistanceToConvex`、
`IntervalsOverlap`），不新造——提案 §5.2 的原话。唯一报告差异：SCENE-003
在**第一个**阻挡体上返回（它在给 1,257 个候选排序，只需第一个合法解），
本审计**收集全部**阻挡体（一次 FAIL 会停掉整批，归因必须完整）。判据不变，
任一阻挡体即 FAIL，没有放宽任何门。

### 2.3 已披露诊断（**不参与判定**）

锚点距冻结路线中心线 **0.5 m**，而路线走廊半宽是 `1.0 + 0.5 = 1.5 m`——
**锚点位于目标车辆的行车走廊之内**。

BC-M34-4 (c) 把该门冻结为「支撑/净空审计」，净空审计的对象是场景障碍实例，
而锚桅本身不是场景对象（`TetherLineVisual` 是纯 `LineRenderer`、零碰撞体），
所以现有判据不会看见这件事。实现角色**不自行增设新门**（那等于重新解释已
接受的 clarification，且该门大概率会 FAIL 并停掉整批）。数值已写入工件字段
`route_centerline_distance_m` / `route_corridor_half_width_m` 并配 EditMode
测试锁定其非门属性，**交接受角色裁定**。

---

## 3. 工具 2 — 15 点同构复算（BC-M34-4 (a)(b)、BC-BODY1-2）

工件：`docs/evidence/P1-M3-BODY-001-scene-body-margin.json`（sha256 `1f30d479…8e680`）

### 3.1 `C_geom`（整圈定义域，BC-BODY1-2）

| 量 | 本工具实测 | 提案 §3.1 预扫 |
|---|---|---|
| 上界（仅视锥） | **`1.000000`** | `1.0000` |
| 下界（+ 盒级遮挡） | **`0.565728`** | `0.5645` |
| 缺口 | **`0.434272`** | ≈`0.44` |
| 主遮挡体 | `Building_Stadium`，2808 / 3069 被挡点样本 | `Building_Stadium` |

**BC-M34-4 (a) 由此机械证成**：实义 `C_geom` 缺口 ≈ `0.43`，归因到单一可
指名建筑，设计 §6 的反天花板要求在本载体上满足。

其余归因：`Props_Street Light` 298、`Props_Traffic Signal_big` 233、
`Natures_Fir Tree` 153、`Props_Hydrant` 1。

### 3.2 可见弧与测量窗（BC-BODY1-2 冻结项）

| 项 | 值 |
|---|---|
| 可见弧 | **单段**，里程 `[155.0, 275.5)`（跨接缝回绕），长 **`120.5 m`** |
| `route[0]` 在弧内 | **是**（BC-BODY1-2 要求的核证项） |
| 测量窗 | `[0.0, 62.5) m` |
| 可见弧 SHA-256 | `4fe2eea5e831301be8fea76e4757e151113dcd0251941e88a2c21b1e1a6bdf55` |

可见弧长 `120.5 m` 与预扫 `120.2 m` 吻合，遮挡弧 `92.47 m` 与预扫 `92.8 m`
吻合，「简单双段」结构复现。

**⚠️ 实质背离 1：每 trial 的测量窗是 `62.5 m ≈ 31.25 s`，不是提案 §5.1 写的
「可见弧 ≈ 60 s」。** 原因是两条冻结条款的交互：§3.3 点 1 把起点钉死在
`route[0]`，点 4 规定目标进遮挡弧即结束 trial；而 `route[0]` 位于可见弧
**内部第 57.97 m 处**，不是弧首。所以每次 Play 只能测到该弧的剩余段。
这不改变任何门，但把每 trial 的有效测量时长减半，直接影响 §5.1「每臂 ≥5
个 trial」的样本量假设。**交接受角色裁定**（BC-BODY1-2：实质背离先回接受
角色再谈采集）。

### 3.3 `C_quality` 投影（测量窗内，各 125 个样本）

| 分量 | 臂A 云台-only | 臂B 阈值式 | B/A | 提案 §3.2 预扫 |
|---|---|---|---|---|
| 面积 px² 中位 | `1217.909011` | `2222.581504` | `1.82×` | `851.6 → 2153.8`（`2.53×`） |
| 面积 px² p10 | `705.167330` | `1995.564843` | `2.83×` | `588.1 → 1289.1`（`2.19×`） |
| **中心误差 px 中位** | `5.973297` | `4.913562` | `0.82×` | `130.3 → 6.2`（`21×`） |
| 中心误差 px 最大 | `132.301190` | `6.417680` | `0.05×` | — |
| 最小边 px 中位 | `28.041491` | `34.605346` | `1.23×` | `24.0 → 35.5` |
| 最小边 ≥20 px 占比 | `0.912` | **`1.000`** | — | `0.873 → 1.000` |
| 云台饱和占比（诊断） | `0.488` | **`0.000`** | — | `0.736 → 0.429` |

臂B 机身位移：中位 `21.35 m`、最大 `24.45 m`，全程在系留球
（`sqrt(35² − 25²) = 24.4949 m`）与走廊约束之内。

**BC-M34-4 (b) 由此机械证成**：系留/高度/净空约束内确实存在合法机身动作
（中位 21.35 m 水平位移），且它把最小边 ≥20 px 占比从 `0.912` 抬到 `1.000`、
把云台饱和从 `0.488` 压到 `0.000`、把中心误差最大值从 `132.3 px` 压到
`6.4 px`。

**⚠️ 实质背离 2：中位数口径下臂A/臂B 的对比远弱于预扫（中心误差 `0.82×` vs
预扫 `21×`）。** 原因是定义域不同，不是算法不同：BC-BODY1-2 规定
`C_quality` **只在测量窗内**算，而预扫显然按整圈算。测量窗 `[0, 62.5)` 覆盖
北直道近锚点半段，臂A 在其中只有 48.8% 的样本饱和，中位数恰好落在饱和转折
点上，因此中位数这个统计量在本窗内几乎没有区分度——但**尾部有**（最大值
`132.3 → 6.4 px`）。

BC-BODY1-1 把 `C_quality` 三分量预注册为「面积中位、中心误差中位、最小边
≥20 px 占比」，BC-BODY1-5 又把 H2 判定式定为三分量逐 run 配对差同号。按当
前测量窗，中心误差中位这一分量在臂A/臂B 之间方向为负（`4.91 < 5.97`，B 更
优，符号正确）但幅度极小，H2 的 (ii) 条「≥5 run 全同号」有实质失败风险。
**这属于「对判定式有异议须在采集前回接受角色」的情形（BC-BODY1-5），本批次
按原判定式如实登记，不作任何修改。**

### 3.4 预注册归约（R1–R5，工具运行前写死）

R1 路线域 = 冻结折线每 `0.5 m` 采样（§3.3 原步长），朝向取线段方向；
R2 云台瞄准目标地面点（`track_loop.py:615` 的零跟踪误差极限）；
R3 臂A 机体恒在锚点悬停点；
R4 臂B **准静态**：沿目标方位取使离轴角降到释放阈值（25°）的最小位移，
经系留球钳位后以 `0.05 m` 步长缩短至走廊无碰，仍不可行则 hold——**有意
忽略 4 m/s 机体动力学与 120°/s 云台转速**，那正是批次 1c 要实测的；
R5 离线遮挡体 = 779 个道路审计障碍实例的世界 AABB。

R5 的两处披露：AABB 相对运行时非凸 MeshCollider **高估阻挡**（这正是遮挡
结果作为 `C_geom` **下界**的来源）；道路面在离线侧不是遮挡体而运行时是
（自 25.2 m 向下、终点在路面上方 ≥0.2 m 且射线缩短 0.05 m 的射线打不到路
面，预期影响为零，但如实登记而非假设）。

### 3.5 中途发现并修复的真实缺陷（如实登记）

首版 Editor 查询在**未施加 `scene_adjustments`** 的原始场景上采集障碍实例。
`scenario.default.json` 会把 3 辆车移出路线、删除另外 3 辆，而这 6 辆里有
4 辆是环线上最重的遮挡体之一（`Vehicle_Container_color01` 403、
`Vehicle_Container_color02 (4)` 325、`Vehicle_Car_color03 (2)` 160、
`Vehicle_Taxi (2)` 133 个被挡点样本）。

首版结果因此是 `C_geom` 下界 `0.492958`、可见弧碎成 4 段。改为按
`TetheredScenarioBootstrap` 的原顺序「先 Apply、再 Find、再 Audit」之后，
下界变为 `0.565728`、可见弧回到单段，与预扫吻合。**预扫数字反过来成了发现
本缺陷的有效交叉验证**。工具 1 同样修正并重跑，`CLEAR` 结论不变。

---

## 4. 工具 3 — `σ_px` 离线重标定（BC-BODY1-7）

工件：`docs/evidence/P1-M3-BODY-001-sigma-px.json`（sha256 `824d77f5…3a7bb`）

| 项 | 值 |
|---|---|
| **`σ_px`** | **`2.866112` px** |
| 残差幅值 中位 / p95 / 最大 | `2.791571` / `7.840604` / `12.374182` px |
| 逐轴 | `mean_x -1.636743`、`stdev_x 2.672202`、`mean_y -0.312018`、`stdev_y 2.551911` |
| 初始化 | 帧 0 的 `VALID` 真值框，一次 |
| 样本 | 2404 / 2404 帧全部产出残差，`tracker_lost = 0`，真值缺口 0 |

**预注册聚合（运行前写死在工具与产物 schema 内）**：P1 首帧真值框初始化、
P2 逐帧框中心像素有符号偏移、P3 `σ_px` = 双轴有符号残差的**池化 RMS**、
P4 **不做任何截尾或剔除**（漂移抬高保守先验，方向安全）、P5 标为保守初值。

**两条外推风险逐字入档**：(a) 该归档 `manifest.gimbal_driver =
truth_directed_scouting`，是真值导向 scouting 扫描而非跟踪回路；(b)
SCENE-004 是近天底 benign 几何、斜距带很窄，而本批次载体是主环线最高约 70°
离轴，标定是跨该缺口外推的。

批次 1c 义务：回报载体上的实测残差分布与本值对照；需重标 Q/R 时回接受角色。

标定是离线工具活动，允许读归档真值；其产物进入在线侧的唯一形态是
`config/p1-m3-body-001.json` 里的冻结标量。

---

## 5. 系留走廊工件（BC-BODY1-4）

工件：`config/p1-m3-body-001-corridor-prisms.json`（sha256 `9e2956ad…c800`），
**779** 个世界系 AABB 棱柱，SHA-256 已记入 `config/p1-m3-body-001.json`。
`tools/build_m3_corridor.py --check` 重建并逐字节比对，可复现。

### 5.1 「唯一用途」如何做成可机械核对的

BC-BODY1-4 禁止批次 1 内任何可见性/遮挡预测、估计器或**测量窗**逻辑读取走廊
工件。工具 2 算的恰恰是遮挡与测量窗，因此**工具 2 不读走廊工件**：Editor 侧
一次遍历产出 `docs/evidence/P1-M3-BODY-001-scene-geometry.json`（证据侧），
走廊 config 由它离线派生（`tools/build_m3_corridor.py`），工具 2 只读证据侧。
两者同源但身份分离，于是「走廊工件只有一个用途」不是承诺而是可核对的事实。

### 5.2 ⚠️ 实质背离 3：BC-BODY1-4 的「782 实例集」在本载体上是 **779**

| 口径 | 计数 |
|---|---|
| `runtime/road_scene_audit.json`（`scenario_id: p1-scene-004`） | 782 |
| 未施加 `scene_adjustments` 的原始场景（预扫口径） | 782 |
| **`config/scenario.default.json` 自身的道路审计（本批次载体）** | **779** |

两个 782 是两个不同的量，恰好相等。本批次载体删掉 3 辆车，其自身道路审计
报 779（Editor 同一次遍历跑出，工件字段 `road_audit_obstacle_count`，状态
`CLEAR`）。用 782 那一版等于冻结一份「仿真永远不会运行的场景」的走廊工件。

实现角色**不自行重新解释** binding clarification：工件按实测 779 构建，基准
由道路审计**自证**而非对硬编码字面量断言，冲突以
`bc_body1_4_quoted_instance_count` / `bc_body1_4_count_conflict` 两个字段
显式登记，**交接受角色裁定**。builder 在两个计数不一致时 fail-closed。

---

## 6. 规划器接口契约 v1（BC-M34-7 停点主体）

见 [P1-M3-BODY-001-planner-contract.md](P1-M3-BODY-001-planner-contract.md)：
BC-M34-7 八项逐条冻结、触发量语义与 0.1° 死区、走廊工件唯一用途、
**waypoint 显式版本化延后至 contract v2**（v2 属控制协议变更，按 §4.3.1
单独停点）、**M4′ 三用例需求预审**（L2a/L2b/L4 全部功能够用，三处不便均
指向同一件缺失的 waypoint 且已显式延后）、config schema。

可执行半边 `controller/body_planner.py`：`PlatformState`、`WorldEstimate`、
`BodyCommand`、`BodyPlanner` 抽象。**零策略实现**——无阈值、无走廊查询、无
hold 实现，全部属批次 1a-β。模块**不导出任何写入器**（fail-safe (c)），
`controller/body_entry.py` 仍是唯一发布者。

---

## 7. 关键文件与协议

**新增**

- `config/p1-m3-body-001-anchor-placement.json`、`config/p1-m3-body-001.json`、
  `config/p1-m3-body-001-corridor-prisms.json`
- `Assets/TetheredTracking/Scripts/P1M3BodyAnchorAudit.cs`、
  `Assets/TetheredTracking/Scripts/P1M3BodySceneGeometry.cs`
- `Assets/TetheredTracking/Editor/P1M3BodyAnchorEvidenceGenerator.cs`、
  `Assets/TetheredTracking/Editor/P1M3BodySceneGeometryGenerator.cs`
- `Assets/TetheredTracking/Tests/EditMode/P1M3BodyAnchorAuditEditModeTests.cs`
- `tools/check_anchor_placement.py`、`tools/check_scene_body_margin.py`、
  `tools/calibrate_pixel_sigma.py`、`tools/build_m3_corridor.py`
- `controller/body_planner.py`（抽象）、`tests/test_m3_body_tools.py`
- `docs/evidence/P1-M3-BODY-001-{anchor-audit,scene-geometry,scene-body-margin,sigma-px}.json`
- `docs/evidence/P1-M3-BODY-001-{planner-contract,batch1a-alpha}.md`

**修改**：`docs/current-status.md`（交接与状态）。

**协议改动：零。** 帧/观测/控制协议字节、既有 config 字节、主指标定义均未
改动。运行时行为在本批次内**完全未变**（无策略、无 `track_loop` 接入）。

一处跨 work item 复用：Editor 侧写出用 `Scene006Json.ToStrictJson` +
`ContainsNonFiniteToken` fail-closed。`JsonUtility` 会打印裸 `NaN`，标准
解析器不接受，而 Python 检查器用 `json.load`；BC-P2-10 已为此建立过一个
经复核的严格 JSON 边界，复制一份只会制造漂移，故复用而非重写。

---

## 8. 实际运行的命令与结果

```
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity -batchmode -nographics -projectPath ~/TetheredDroneTracking -executeMethod TetheredTracking.Editor.P1M3BodyAnchorEvidenceGenerator.Generate -quit -logFile runtime/test-results/p1-m3-body-001-anchor-audit.log
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity -batchmode -nographics -projectPath ~/TetheredDroneTracking -executeMethod TetheredTracking.Editor.P1M3BodySceneGeometryGenerator.Generate -quit -logFile runtime/test-results/p1-m3-body-001-scene-geometry.log
python3 tools/check_anchor_placement.py
python3 tools/build_m3_corridor.py && python3 tools/build_m3_corridor.py --check
python3 tools/check_scene_body_margin.py
.venv-track/bin/python tools/calibrate_pixel_sigma.py
.venv-track/bin/python -m unittest discover -s tests
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity -batchmode -nographics -projectPath ~/TetheredDroneTracking -runTests -testPlatform EditMode -testFilter TetheredTracking.Tests -testResults runtime/test-results/p1-m3-body-001-editmode.xml -logFile runtime/test-results/p1-m3-body-001-editmode.log
```

| 检查 | 结果 |
|---|---|
| 工具 1 锚点审计 | `CLEAR`；Python 检查器 exit 0 |
| 走廊工件 build + `--check` | 779 棱柱，逐字节可复现 |
| 工具 2 | exit 0，`route[0]` 在可见弧内 |
| 工具 3 | `σ_px = 2.866112`，2404/2404 残差，0 丢失 |
| 新增 Python 模块 `tests.test_m3_body_tools` | **55/55 通过** |
| 完整 Python 套件 | **394 项，1 项失败**（见下） |
| Unity Edit Mode `TetheredTracking.Tests` | **258/258 通过**（新增 12 项） |
| 场景字节 | 每次 Editor 运行前后 SHA-256 相同 |

**唯一失败项是既有失败，与本批次无关**：
`tests/test_check_docs.py::CheckDocsTest::test_compliant_minimal_status_passes`
在 `git stash` 掉本批次全部改动后于 `HEAD` 上**同样失败**（fixture 缺
`## Current state` / `## Active handoffs` 两节，而 `tools/check_docs.py` 现在
要求它们）。两个文件都是工作流基础设施，对本角色只读，**未修改也不得修改**；
修复须走用户直接授权的协调批次。

---

## 9. 未验证项与已知限制

1. **工具 2 全部为几何投影，不是实测。** 臂B 是准静态归约（R4），忽略机体
   4 m/s 与云台 120°/s 动力学，也不含估计器误差。`C_track|geom` 的实际改善
   只能靠批次 1c 跑出来；本文件不预设其数值。措辞上限按 BC-BODY1-1 保持在
   「阈值式机身分配改善**成像质量**」。
2. **离线遮挡是 AABB**，相对运行时非凸 MeshCollider 高估阻挡；真实 `C_geom`
   落在 `[0.565728, 1.000000]`，精确值由批次 1c 实跑给出。
3. **目标朝向与转弯滞后未建模**：`LoopTargetVehicle.Step` 在距顶点 `<0.5 m`
   时只推进索引不移动，实际轨迹是切角的圆滑折线；转向 `240°/s` 使每个 45°
   倒角有约 `0.375 m` 行程的滞后。工具 2 用冻结折线与线段方向，两处偏差各
   ≤`0.5 m`，如实登记。
4. **`σ_px` 是跨几何外推的保守初值**，两条风险已逐字入档（§4）。
5. **锚点位于行车走廊内**（§2.3），已披露、未判定。
6. **走廊相交判据是 Minkowski 盒膨胀**而非真胶囊扫掠，在盒角处高估阻挡——
   安全检查的保守方向。
7. 本批次**未做**任何 Play、目检或渲染保真检查；COORD-005 的人眼保真检查
   属批次 1b，未到期。

---

## 10. 给复核角色的复核范围

BC-BODY1-3 的复核范围预告是「BC-M34-4 三条输出的机械可复算性与接口契约完整性
（含 waypoint 延后声明与 M4′ 三用例走查）」。逐条落点：

1. **BC-M34-4 (c)** — `P1M3BodyAnchorAudit.cs` 的判据是否与
   `P1Scene003AnchorAuditor` 原语一致、有无放宽；`tools/check_anchor_placement.py`
   是否真的独立复算（它只能独立复算道路面支撑与逐阻挡体域值，棱柱/prefab
   支撑要靠场景，这一分工是否被诚实声明）；`(132,117)` 的 `CLEAR` 是否成立。
2. **BC-M34-4 (a)(b)** — `tools/check_scene_body_margin.py` 的 15 点谓词、
   `BoundsCorners`/`VisibilitySamples`/`ProjectBounds`/`TetheredGimbal` 四处
   同构性；`Renderer.bounds` 用世界 AABB（而非局部盒）是否正确；R1–R5 归约
   是否在运行前写死、有无事后调参痕迹。
3. **载体基准** — 场景几何是否确实在 `scene_adjustments` 之后采集（§3.5 的
   缺陷是本批次自查发现并修复的，请独立确认修复彻底）；779 与道路审计自证
   是否一致。
4. **走廊工件唯一用途** — 工具 2 是否真的不读走廊 config；走廊工件是否只被
   声明的那一个查询使用（批次 1 内运行时侧尚无消费者）。
5. **接口契约完整性** — BC-M34-7 八项是否逐项冻结；`controller/body_planner.py`
   是否确实零策略、零写入器；0.1° 死区的非等价是否被正确表述（不得写「当且
   仅当」）；waypoint 延后声明与 M4′ 三用例走查是否完整。
6. **三处实质背离的登记是否诚实**（§3.2 测量窗 31.25 s、§3.3 中位数口径对比
   弱化、§5.2 的 779 vs 782），有无被淡化。

复核角色只在一次性 worktree 接触实现代码，发现缺陷只写 `docs/reviews/`，
不改一行。

---

## 11. 给用户的 Unity 观察点

**本批次不请求任何 Unity 操作。** 批次 1c 的每次 Play 由用户执行，且以
BC-BODY1-3 四门齐备为前提（1a-α 复核 PASS + 接受角色 BC-M34-4 归因、
1a-β 复核 PASS、1b 完成、用户 Play）。批次 1b 的 COORD-005 人眼保真检查
届时另行提出。

---

## 12. 交回接受角色的待裁事项

| # | 事项 | 位置 |
|---|---|---|
| 1 | BC-BODY1-4 的「782 实例集」在本载体上实为 779 | §5.2 |
| 2 | 每 trial 测量窗 `62.5 m ≈ 31.25 s`，非提案的 ≈60 s；影响 §5.1 的样本量假设 | §3.2 |
| 3 | 测量窗口径下 `C_quality` 中位数分量几乎无区分度，BC-BODY1-5 的 H2 判定式 (ii) 有实质失败风险；按 BC-BODY1-5 须在采集前提出 | §3.3 |
| 4 | 锚点位于行车走廊内（距中心线 0.5 m < 半宽 1.5 m），已披露未判定 | §2.3 |
| 5 | `tests/test_check_docs.py` 既有失败，属工作流基础设施，需协调批次修复 | §8 |
