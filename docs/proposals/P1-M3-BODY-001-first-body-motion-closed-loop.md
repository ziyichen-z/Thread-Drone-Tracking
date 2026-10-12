# P1-M3-BODY-001 — M3′ 批次 1：世界系估计器 + 阈值式机身分配 + 首个机体运动闭环

Status: ACCEPTED_WITH_BINDING_CLARIFICATIONS（Acceptance round 2，
2026-08-07；BC-BODY1-1…20）；批次 1a-β 候选 `5340cf6` 在 Acceptance
round 5 **停点不成立、退回返工**（见文末）
Author/role: 构思角色（ideation，Fable 池）
Created: 2026-08-06
Last updated: 2026-08-07
Revision: 1（逐条回应见文末 §Revision 1；round 1 裁定原文保留在前，不改一字）
上位章程：`P1-M3M4-SCOPE-001`（`ACCEPTED_WITH_BINDING_CLARIFICATIONS`，
设计 v0.3.11）——本提案是其 M3′「保持可见」轴的第一个实现批次，
不修改章程本身。

**授权状态**：本稿**不请求任何用户授权**。round 1 第 9 条列出的两项
（主指标、门序）在本稿中**均已消解**，理由见 §3.2 与 §5.2。实现、
Edit Mode、Play、ID/配额消耗各待其门。

---

## 0. 修订索引与 revision 0 的实测勘误

### Round 1 必修项 → 本稿落点

| # | 必修项 | 落点 | 实质变化 |
|---|---|---|---|
| 1 | 机体高度基线 `25.2 → 25.0` | §0 勘误 E1、§3.1 | 接受侧成立。云台用 `-delta.y =` 机体世界 y − 目标平面 y `= 25.2 − 0.2 = 25.0`。`C_point` 静止由 `0.2666` 更正为 **`0.264645`**，与 SCOPE-002 保留的饱和占比 `0.7353` 互补（`1 − 0.7353 = 0.2647`）；`atan(69.112228/25.0) = 70.113398°` 与其记录逐位一致。**但 `C_point` 整个指标已按第 4 条撤回**，该修正只作为勘误留档 |
| 2 | 撤回「弧长=时间」与「一圈 106.5 s」 | §0 勘误 E2、§3.3 | 接受侧成立且**本稿复算逐位复现**其 538 步坐标 `(125.273216, 117.264130)`。本稿另发现更重的一层：**全项目无固定时间步**，故不改用「冻结步数 horizon」（那仍依赖 dt），改为**按目标路线位置离线划定测量窗**，对帧率抖动完全免疫 |
| 3 | 撤回 `C_geom = 1.0000` 中心推断 | §0 勘误 E3、§3.1 | 已用 15 点同构谓词离线复算，并以真实 Unity 数据验证（`LookNadir` 下复算 `0.210746` vs 实测 `0.219563`）。结论：视锥项**确实饱和**（上界 `1.0000`），但**遮挡项不饱和**，`C_geom` 下界 **`0.5645`**，主因是可指名的 `Building_Stadium` |
| 4 | `C_point` 不是零 tracker 参与 | §0 勘误 E4、§3.2 | 接受侧成立。`Saturated ← requested ← look_at(intersection.point_world_m) ← tracker→geolocate`，是闭环量。**本稿整个撤回 `C_point` 作为指标**，改用设计 §6 既有的 `C_track\|geom`（主）与 `C_quality`（机制），云台饱和占比降为诊断 |
| 5 | `σ_px` 标定源 | §0 勘误 E6、§3.4 | 第一句不成立（2405 个 JPEG 确在 `runtime/test-results/p1-scene-004-scout-4-closed-exchange/frames`，本稿从中读出过像素）；但**实质结论成立**：归档无 tracker 框、是 truth-directed scouting、SCENE-004 近天底几何。改为**离线重跑 tracker 标定**并如实披露跨几何外推风险 |
| 6 | `track_loop` 接入点描述与实际不符 | §0 勘误 E5、§2、§7 | 接受侧成立。`:304` 在 `initialize()` 内、受 `if self._rate_lifecycle is None:` 保护、全程**只执行一次**。本稿改为**逐帧回路新增 planner 调用**，并逐分支写死期望 body 行为 |
| 7 | BC-M34-3 的触发量 | §3.5 | 改为章程要求的 `PlatformState` 发布量：**由已发布的 `camera_forward_world` 导出的当前云台限位裕度**，不用估计器均值。饱和后裕度恒为 0 的解除问题一并写死 |
| 8 | BC-M34-8 的冻结次序 | §3.5 末、§5.4 | 明写：预注册值在 §7 工具机械复算产出后**不得再调**；工具输出与预注册冲突的唯一合法动作是回接受角色 |
| 9 | 两项须用户授权 | §3.2、§5.2 | **两项均消解**。(a) 不再立新主指标；(b) BC-M34-4 三条中两条本稿已证，第三条（支撑面/净空审计）列为批次 1a 的**第一个**工具 |
| 10 | BC-M34-6「不适用」须机械化 | §5.2 | 写成与真值检查并列的机械检查：批次 1 的在线与离线决策路径对任何可见性模型/遮挡先验/`WorldModelHandle` 类工件**零引用**，进复核范围；并写明 BC-M34-6 对批次 2 全额有效 |

### Revision 0 的六处实测勘误（本轮取证推翻，逐条如实登记）

| # | revision 0 的写法 | 实测事实 | 后果 |
|---|---|---|---|
| **E1** | `C_point` 静止 `0.2666`，离轴 `69.97°`，可达半径 `25.20 m` | 云台在 `TetheredGimbal.cs:35` 用 `height = Mathf.Max(0.1f, -delta.y)`，即**机体世界 y 减目标平面 y** `= 25.0`，不是机体世界 y `25.2` | 更正为 `0.264645` / `70.113398°` / `25.000000 m`；与 SCOPE-002 的 `0.7353` 互补吻合。**遮挡类计算不受影响**——那里 `gimbal_rotation` 本就用 `-dy`，一直是对的 |
| **E2** | 「弧长占比 = 时间占比」「一圈 `212.97/2.0 = 106.5 s`」「每臂 ≥3 圈」 | `LoopTargetVehicle.Step` 在距顶点 `< 0.5 m` 时只推进 `waypointIndex` 并 `return`（**该步不移动**）；且无真周期——float32 复算 dt=0.2 第 538 步为 `(125.273216, 117.264130) ≠ route[0]`。**更严重**：`grep captureDeltaTime\|fixedDeltaTime\|targetFrameRate` 于 `Assets/` **零命中**，一切积分走 `Time.deltaTime` = 渲染帧时；dt=0.2 与 dt=1/60 走出不同轨迹 | 「圈」不是可核对的采集量；**且 revision 0 §5.1 的「配对」前提（"仿真确定性使两臂逐帧可比"）不成立**。改为 §3.3 的位置划窗协议 |
| **E3** | `C_geom` 在主环线被做满（`1.0000`），据此排除它作主指标 | 该断言只判了目标**中心**是否在视锥内。`CoverageEvaluator.cs:726-749` 判的是 15 点（8 角 + 中心 + 6 轴向极值）中 `visibleCount/15 ≥ 0.2`，且 `visibleCount` 要求**在锥内且 `HasClearLineOfSight`** | 视锥项确实饱和（15/15 全路线），但遮挡项不饱和：`C_geom` 下界 **`0.5645`**。**结论反转——`C_geom` 可用** |
| **E4** | `C_point` 是「纯平台量、零 tracker 参与」 | `Saturated = requested > maximumOffNadirDeg + 0.1f`，`requested` 来自 `track_loop.py:615` 的 `look_at(intersection.point_world_m)`，即 tracker→geolocate 输出 | 是闭环量。**整个指标撤回**；其角色由 `C_quality` 承担 |
| **E5** | `track_loop.py:304` 是「无条件 `hold_body()`」，本批次「替换一行」 | `:304` 在 `initialize()` 内、受 `if self._rate_lifecycle is None:` 保护，是整个运行中**唯一一次** body 发布 | 不是替换一行，是**逐帧回路新增 planner 调用**；§2/§7 重写 |
| **E6** | `σ_px` 由 scout-4「2405 帧图像–真值配对」离线标定 | 图像确实存在（2405 个 JPEG），但**归档中无 tracker 框**（scout-4 会话目录只有 completion/manifest/reference/scouting-result/truth，无 run log），故该配对不能查档构造，须**离线重跑 tracker**；且该归档 `gimbal_driver = truth_directed_scouting`、SCENE-004 近天底几何，外推到主环线 70° 离轴缺依据 | §3.4 改为离线重跑 + 保守上界 + 外推风险披露 |

---

## 1. 问题和研究价值

### 1.1 现状：能动的部分建好了，知道往哪动的部分一行没写

| 层 | 部件 | 状态 |
|---|---|---|
| 执行 | `TetheredDronePlant.cs`（64 行）：速度钳位 `maximumSpeed=4`、加速度 `MoveTowards(4)`、系留球约束（垂直钳 `[8,32]`、水平钳 `sqrt(L²−v²)`）、`TetherSaturated` | ✅ 已建成 |
| 执行 | `BodyCommandReceiver.cs`（105 行）：20 Hz 轮询、`command_id` 去重、过期检查、受 `experiment.ControlEnabled`/`AuthorizeControl` 门控、**缺失或过期一律 `Hold()`** | ✅ 已建成，默认安全 |
| 执行 | `controller/body_entry.py`：`velocity(vx,vz,vy)` / `hold()` | ✅ 已建成 |
| **决策** | 世界系状态估计器 | ❌ `controller/` 下无 estimator/world-model 模块 |
| **决策** | 机身分配策略 | ❌ 不存在 |
| **决策** | `track_loop` 逐帧接入 | ❌ 只有 `initialize()` 内一次性的 `hold_body()` |

**实测佐证**：`hold_body` 全文只在 `controller/track_loop.py:154` 定义、
`:304` 调用一次；**22 个带 `camera_position_world_m` 的归档目录，
位移跨度全部恰好 `0.000000 m`**——机体从未在任何一次记录中移动过。

2026-07-21 定的「优先转镜头，不够用才移动机身」，**后半句从未被执行过
一次**。云台侧的对照是完整的（`P1-DETECT-001` qual-3
`C_track|geom = 0.920428`，3001 帧零 LOST/gap/reinit）。

### 1.2 研究价值：M3′ Pareto 的第一个非退化数据点

章程要求 M3′ 产出「云台-only / 阈值式 / 词典序」三点的 Pareto。现在
一个点都没有。本批次交付前两点，并把第三点所需的接口冻结成可复核契约。

---

## 2. 输入、输出与受影响接口

- **输入（在线，零真值）**：帧包 `tethered-sensor-frame/v3`
  （`camera_position_world_m`、`camera_rotation_xyzw`、
  **`camera_forward_world`**、`intrinsics_px`、`capture_monotonic_s`、
  `gimbal_saturated`、`tether_saturated`）、tracker 观测框、scenario 配置。
  **Unity 真值一律不入**（§4.2）。
- **输入（离线，仅评估）**：`CoverageEvaluator` 真值流，按 `frame_id`
  离线 join，只供指标与估计器一致性分析。
- **输出**：`runtime/body_command.json`（既有通道，**零协议改动**）；
  run log 追加估计器与 planner 决策字段（向后兼容追加，不改既有键）；
  `docs/evidence/P1-M3-BODY-001-*.md`。
- **受影响接口（如实声明）**：
  - **新增** `controller/world_estimate.py`、`controller/body_planner.py`；
  - **修改** `controller/track_loop.py`：在**逐帧回路**新增 planner 调用
    （**控制决策逻辑变更 ⇒ workflow §4.3.1 强制复核停点**）；
  - **修改** run log schema（追加）；
  - 运行时协议、帧/观测契约、主指标定义、`config/` 既有字节：**零改动**；
  - **新增** `config/p1-m3-body-001.json`（策略与估计器参数）。

**逐分支 body 行为（round 1 必修 6：写死，实现者零裁量）**：

| `track_loop` 分支 | 期望 body 行为 |
|---|---|
| `initialize()` 内，`_rate_lifecycle is None` | 保持现状 `hold_body()`（一次性），planner 尚未启动 |
| `initialize()` 内，`_rate_lifecycle` 非空 | 不发 body 指令（现状即如此） |
| 逐帧回路，`qualification_lifecycle` 非空 | **不发** body 指令（资格协议独占控制） |
| 逐帧回路，本帧无观测/无帧包 | `hold()` |
| 逐帧回路，planner 返回 `hold` | `hold()` |
| 逐帧回路，planner 返回 velocity | `body_entry.velocity(...)`，`expires_after_s` 取 `2 / capture_hz` |
| 任何异常路径 | `hold()`；异常不得吞掉，记入 run log |

`BodyCommandReceiver` 的过期回落与 planner `hold` 是**两道独立保险**：
前者防控制器停发，后者防控制器判断为不该动。二者都不得依赖对方。

---

## 3. 算法或行为假设（可证伪）

### 3.1 载体与场景适配性（离线复算；谓词经真实 Unity 数据验证）

**谓词同构**：本稿离线实现逐行对映
`CoverageEvaluator.EvaluateVisibility`（`:726-749`）、`BoundsCorners`
（`:814-825`）、`VisibilitySamples`（`:827-841`）、`TetheredGimbal.LateUpdate`
（`:27-46`）、`TargetVisualFactory.AddTargetVisual`（`:71-90`）。

**谓词验证（对真实 Unity 产物）**：在**同路线同锚点**的
`scenario.scene-validation.json` 上、按 `LookNadir()` 复算，得
**`0.210746`**；`UT-P1-SCENE-002-001` attempt 3 实测 **`0.219563`**，
差 `0.0088`。残差可由时间/弧长加权差、目标转向滞后、5 Hz 帧采样解释。

**场景解析验证**：从场景 YAML 重建 899 个 PrefabInstance，其中 **782 个**
匹配 `road_data.json` 的 `obstacle_footprints`——与
`runtime/road_scene_audit.json` 的 `audited_obstacle_count: 782`
**完全一致**；`scenario.default.json` 的 6 条 relocation 各匹配恰好 1 个根
（`SceneVehicleAdjustments.Apply` 的 fail-closed 条件）。

**复算结果（主环线，锚点 `(132, 117)`，机体静止 h=25）**：

| 量 | 值 | 性质 |
|---|---|---|
| `C_geom` **上界**（仅视锥） | **`1.0000`** | 全路线 15/15 在锥内 ⇒ 视锥项零损失 |
| `C_geom` **下界**（+ 盒级遮挡） | **`0.5645`** | AABB 代替真实网格 ⇒ **高估阻挡**，故为下界 |
| 遮挡主因 | `Building_Stadium` | 阻挡样本计数 5463（冷杉 311、交通信号 242、路灯 91） |

**遮挡体身份（可复算）**：`Building_Stadium`，世界坐标
`(150.0, 0.0, 87.4000015)`，绕 Y 转 90°，缩放 1，世界盒
`x[127.620, 172.376] y[−0.042, 11.688] z[69.992, 105.452]`
（44.8 × 35.5 m，高 11.688 m），**占环线内部 52.6% 面积**。

**BC-M34-4 (a)「实义 `C_geom` 缺口」由此证成**：下界 `0.5645` 远低于
`1.0`，缺口 `≈ 0.44`，且归因到单一可指名建筑。**设计 §6 的反天花板
要求（`C_geom` 显著低于 100%）在本载体上满足。**

**SCENE-004 对照（章程诊断的数值确认）**：`C_geom` 上界与下界均为
`1.0000`，`C_point` 亦为 `1.0000` ⇒ **对机身分配轴完全退化**，本批次
不得在其上验收。

**离线不可判定项（如实登记）**：`HasClearLineOfSight` 用
`Physics.RaycastAll` 打的是运行时由 `EvaluationOcclusionGeometry`
从每个 `MeshRenderer` 的 `sharedMesh` 建的**非凸 MeshCollider**；离线以
世界 AABB 近似，方向为高估阻挡。真实 `C_geom` 落在 `[0.5645, 1.0000]`，
**精确值由批次 1c 的实跑给出**，本稿只用它证明「缺口存在」。

### 3.2 指标分层（round 1 必修 4/9a：不新立主指标）

**全部取自设计 §6 的既有四指标，本稿不发明任何新指标。**

| 层 | 指标 | 定义出处 | 为何选它 |
|---|---|---|---|
| **主** | **`C_track\|geom`** | 设计 §6「物理可见条件下的跟踪成功率；分离"看不见"与"没跟上"」 | 章程的归属指标；且其条件化天然把体育场遮挡段排除，正是本批次要的 |
| **机制** | **`C_quality`** | 设计 §6「目标像素面积、完整可见比例、中心误差；解释远距/大离轴的退化」 | 机体运动改善的正是这一项（见下） |
| 代价轴 | body-motion effort `∫‖v_applied‖dt`（m） | 设计 §6 诊断清单「机身运动量」 | 章程 §4.2：称 effort，**不称 energy** |
| 诊断 | 云台饱和占比、tether 饱和占比、planner 切换次数、遮挡后重捕获 | 帧元数据/run log 现成 | 不参与判定 |

**为什么机制层是 `C_quality` 而不是 `C_geom`**：`C_geom` 是二值可见性，
**按构造无视云台饱和**——目标在 70° 离轴、约 24 px、贴画幅边缘，它照样
记「可见」。而机体运动在本载体上改善的正是这一项。离线按 evaluator 原式
（`areaPixels = w·h·640·480`；`centerError` 见 `:753-755`）复算两臂：

| `C_quality` 分量（h=25，含系留走廊约束） | 臂A 云台-only | 臂B 阈值式 | 差距 |
|---|---|---|---|
| 目标面积 px² 中位 | `851.6` | **`2153.8`** | **2.53×** |
| 目标面积 px² p10 | `588.1` | `1289.1` | 2.19× |
| **中心误差 px 中位** | **`130.3`** | **`6.2`** | **21×** |
| 最小边 px 中位 | `24.0` | `35.5` | 1.48× |
| 最小边 ≥ 20 px 占比 | `0.873` | **`1.000`** | — |
| 云台饱和占比（诊断） | `0.736` | `0.429` | — |

对照：同一两臂的 `C_geom` 只有 `0.5645 → 0.5857`（`+0.021`）。
**`C_geom` 测不到机身分配做的事，`C_quality` 能。**

**round 1 第 9(a) 条据此消解**：本稿不再请求把 `C_point` 立为主指标；
`C_point` 整个撤回，其角色由设计既有的 `C_quality` 承担，云台饱和占比
降为诊断。**无需用户授权。**

**诚实声明（进证据文件）**：以上为**几何投影计算**，不是实测；它证明
「若机体按此策略运动，成像质量会这样变」。真实运行还要叠加估计器误差、
云台 `120°/s` 转速滞后、机体 `4 m/s` 加速限制。`C_track|geom` 的实际
改善**只能靠跑出来**，本稿不预设其数值。

### 3.3 测量窗：可见弧协议（round 1 必修 2 的替代方案）

**问题一（round 1 必修 2）**：无固定时间步 ⇒「圈」「秒数」「步数」都不是
可核对的采集量。
**问题二（本稿新发现）**：`C_track|geom` 条件化的是**逐帧**可见性，但
跟踪是**时序**过程——目标进遮挡 46 s 后再出来，那些帧几何可见但 tracker
早已丢锁，会被记成失败，于是主指标混入**重捕获能力**，而那不是本批次
要测的东西。

**遮挡的时序结构（离线复算，0.5 m 步长）**：

| 锚点/高度 | 连续可见 | 连续遮挡 | 段数 |
|---|---|---|---|
| **`(132,117)` h=25（本批次）** | **`60.1 s`（120.2 m）** | **`46.4 s`** | **各 1 段** |
| `(130,130)` h=25 | 62.6 s | 43.9 s | 各 1 段 |
| `(132,117)` h=32 | 62.6 s | 43.9 s | 各 1 段 |

**不是碎片化的，是简单双段。** 据此冻结协议：

1. `LoopTargetVehicle.Configure` 每次 Play 都把目标置于
   `route[0] = (125.5, 117.5)`——**每次运行起点完全相同**，与帧率无关。
2. tracker 用**人眼确认的冻结初始框**在起点初始化（沿用
   `P1-DETECT-001` qual-3 的做法：该次用的是用户确认的无真值像素框
   `(353, 82, 72, 44)`）。零真值。
3. **测量窗 = 目标位于可见弧内的帧**，由**目标路线位置**离线划定
   （`CoverageEvaluator` 真值流 → 路线里程 → 是否落在冻结的可见弧区间），
   **不按墙钟、不按步数** ⇒ 对帧率抖动完全免疫。
4. 目标进入遮挡弧 ⇒ 该 trial 测量结束。**一次 Play = 一个 trial。**
5. 可见弧区间本身在**采集开始前**由 §7 的检查工具机械产出并哈希冻结；
   实跑后如与实测不符，唯一合法动作是回接受角色，不得就地改区间。

**这样遮挡从头到尾不进分母**，主指标测的是纯粹的可见条件下跟踪能力。

**配对的正确表述（撤回 revision 0 的错误说法）**：两臂**不是逐帧配对**
（无固定时间步，做不到）。两臂配对的是**目标路线位置**——同一 scenario、
同一 `random_seed: 0`、同一起点、同一冻结路线，故两臂遍历同一条折线；
指标按**路线里程加权**而非时间加权。这是本稿能提供的最强配对，且它
不依赖任何未成立的确定性假设。

### 3.4 世界系估计器（批次 1 范围）

常速 Kalman 滤波，状态 `x = [x, z, vx, vz]`（地面系，米）：

- **预测**：`F = [[1,0,dt,0],[0,1,0,dt],[0,0,1,0],[0,0,0,1]]`；过程噪声为
  白噪声加速度，`Q` 由单一标量 `q_accel_mps2` 生成，入配置冻结。
- **量测**：`z = (x, z)`，取自既有 `controller/geolocate.py` 的
  `GroundIntersection.point_world_m`。**地平面常数取 scenario 的
  `target.route_world_m[*].y = 0.2`**，是冻结场景常量、非目标真值，符合
  「M2a LOS 必须显式给出有限地平面标定、不得由目标路线真值推断」。
- **量测协方差（章程要求"不用固定噪声"）**：由 `σ_px`（框中心像素）、
  `σ_att`（姿态）、`σ_y`（地面高度）经**解析 Jacobian** 传播。
- **`σ_px` 标定（round 1 必修 5 重写）**：归档中**无 tracker 框**，故不能
  查档配对。改为**离线重跑**：在 `runtime/test-results/
  p1-scene-004-scout-4-closed-exchange/frames` 的 2405 帧上跑冻结的
  NanoTrack-v2，与 `runtime/p1-scene-004-scouting/p1-scene-004-scout-4/truth`
  的 2405 份真值按 `frame_id` join，取框中心像素残差。产物入配置记
  SHA-256。**必须披露的两条外推风险**：(a) 该归档
  `gimbal_driver = truth_directed_scouting`，不是跟踪回路；(b) 它是
  SCENE-004 近天底 benign 几何（斜距 26.1–30.5 m 窄带），而本批次载体是
  主环线 70° 离轴。因此标定值标为**保守初值**，批次 1c 实跑后须回报
  实际残差分布与之对照；若实测显著更大，`Q`/`R` 的重标定回接受角色。
- **批次 1 明确不含**：L1 惯性滑行阶梯状态机、协方差膨胀规则、T1 定时器、
  以及**任何消费估计器输出的决策**——见 §3.5，本批次的策略**完全不读
  估计器**。协方差计算并记录，供批次 2 与一致性分析使用。

### 3.5 阈值式机身分配（round 1 必修 7：改用 `PlatformState` 发布量）

章程 BC-M34-3 把触发量冻结为 `PlatformState` 发布的**当前云台限位裕度**，
并排除「预测时域内的离轴角」。revision 0 用估计器均值算 `θ̂`，违反该条。

**本稿改为：触发量与方向都只读已发布的平台状态，完全不读估计器。**

- **当前离轴角**（`PlatformState` 由帧元数据构造，零估计器、零真值）：
  `theta_applied = acos(clamp(−camera_forward_world.y, −1, 1))`
  ——`camera_forward_world` 是 v3 帧元数据的既有字段。
- **云台限位裕度**：`margin = maximum_off_nadir_deg − theta_applied`。
- **方向**：`bearing = atan2(camera_forward_world.x, camera_forward_world.z)`
  ——云台已经指向目标（钳位后），其水平方位即目标方位。

```
若 本帧无帧包 / 裕度不可构造        -> hold()
否则若 margin < margin_trigger_deg   -> 沿 bearing 水平平移，速度 v_cmd
否则若 margin > margin_release_deg   -> hold()
否则                                  -> 保持上一动作（迟滞）
```

**「饱和后裕度恒为 0」的处置（round 1 必修 7 点名要求）**：云台钳位后
`theta_applied ≤ 45°`，故 `margin ≥ 0`，且 `margin = 0` **当且仅当**饱和。
- **触发**：`margin = 0` 必然 `< margin_trigger_deg`，触发成立；
- **解除**：机体朝 `bearing` 平移使真实离轴角下降，一旦降到 45° 以内，
  `theta_applied` 随之下降、`margin` 转正，越过 `margin_release_deg` 即解除。
  故解除路径不依赖任何饱和期不可观测量。
- **与 `θ̂` 的等价条件（如实写明）**：未饱和时 `theta_applied` 等于云台
  所请求的离轴角，即等于「云台当前认为的目标方向」的离轴角；饱和时二者
  分离（`theta_applied` 恒 45°，真实值更大）。故本触发量在饱和区是
  **保守的**（低估紧迫度），不会误触发。

**冻结参数（预注册，实现者零裁量）**：

| 参数 | 值 | 理由 |
|---|---|---|
| `margin_trigger_deg` | `10.0` | 等价于 `theta_applied > 35°`，距 45° 限位留 10° 余量供机体加速 |
| `margin_release_deg` | `20.0` | 等价于 `theta_applied < 25°`；迟滞带 10°，防抖振 |
| `v_cmd_mps` | `4.0` | `= drone.maximum_speed_mps`，plant 再钳一次 |
| `altitude_hold_m` | `25.0` | 仅水平运动。最优高度 `24.749 m` 与 `25.0 m` 的可达半径差 **`0.0026 m`**，可忽略；换来批次 1 少一个自由度 |
| `tether_corridor_check` | **启用** | 见下 |

**系留走廊检查（本稿新增，实测支撑）**：planner 在发出 velocity 前，检查
锚点→目标机体位置的直线段是否与任何障碍相交（`corridor_nominal_radius_m
0.5 + clearance_margin_m 0.5 = 1.0 m`）；相交则沿 `bearing` 缩短位移直至
不相交，仍不可行则 `hold()`。

理由与代价均为实测：径向策略**有 `41.43%` 的路线位姿会让缆绳穿过障碍**
（`Building_Stadium` 73 次、`Natures_Fir Tree` 47、`Props_Street Light` 5）；
而启用该检查的代价仅 **`−0.005` `C_geom` / `−3.2%` 面积 / 中心误差不变**。
计算开销实测 **`1.9 μs`/次**（Python + 广相位，782 盒筛到 6 盒），C# 约
`0.04 μs` ⇒ 5 Hz 下占比 `< 0.001%`。不加则 planner 会输出物理上不可能的
指令（仿真不会阻止——`TetherLineVisual` 是纯 `LineRenderer`、零碰撞体）。

**BC-M34-8 的冻结次序（round 1 必修 8）**：上述五个值为**预注册**。§7 的
场景适配性工具机械复算产出后，**不得再调**；若工具输出与预注册值冲突，
唯一合法动作是回接受角色，不得就地改参数。接受侧不反对更早冻结
（更严、无反选风险）。

### 3.6 可证伪假设

- **H1（几何模型正确）**：臂A 实跑的 `C_geom` 落在 `[0.5645, 1.0000]`
  区间内。**证伪 ⇒ §3.1 的谓词或场景重建有误**，整批次停下重算，不得调
  策略去凑。（区间宽是诚实的：下界来自 AABB 高估阻挡，上界来自视锥饱和。）
- **H2（机身分配改善成像质量）**：臂B 的 `C_quality` 三分量（面积中位、
  中心误差中位、最小边 ≥20 px 占比）**同时**优于臂A，按路线里程加权的
  配对比较，置信区间下界优于 0。**证伪 ⇒ 如实报告
  `THRESHOLD_ALLOCATION_INEFFECTIVE`**，词典序臂的价值假设需重审。
- **H3（机制传导到任务）**：`C_track|geom` 同向改善。**不设通过线**——
  探索性，两向都如实登记。
- **H4（副产物）**：批次 1c 产出 `p_min`——YOLOE 在本载体上的实际最小
  可检测目标尺寸。它是后续几何设计（`s_max = d_min·f/p_min`）的输入，
  本批次只测不用。

---

## 4. 与 v0.3.16 设计的兼容性

### 4.1 兼容

- 不改设计基线文本（§4.3 的修订请求除外，且那是**请求**不是执行）、
  不改主指标定义、不改帧/观测/控制协议字节。
- 章程 `P1-M3M4-SCOPE-001` 的 M3′ 范围不变；本批次是其真子集。
- M2 已 `CLOSED_D2_NEGATIVE_RESULT`，章程「M3′ 实现启动受 M2 关闭停点
  纪律约束」已满足。

### 4.2 真值边界（硬约束）

- 在线侧**零真值**：估计器输入只有 tracker 框与帧元数据；planner 只读
  `camera_forward_world` 导出的裕度与方位；地平面是 scenario 常量。
- `CoverageEvaluator` 仍是真值唯一产地；指标与估计器一致性分析**离线**
  按 `frame_id` join。
- 复核范围必须含机械检查：**在线代码路径对真值文件零引用**。

### 4.3 附带修订请求：把系留绷紧假设写进设计（交接受角色裁定）

**本条是请求，不是执行；不占额外轮次，接受角色可采纳或否决。**

设计「活跃约束」现有一句：

> The plant is kinematic and does not yet model tether tension, sag,
> reel dynamics, or aerodynamic coupling.

**这句不足以支撑现有几何**。实测：标称悬停点（正上方 25 m）弦长
`25.00 m`、放线上限 `35.00 m` ⇒ **松弛 `10.00 m`**。缆绳只在机体贴到
球面（`d = L`）时才自然绷紧；球内部必有松弛，而松弛缆绳不是直线。
于是 plant 的球约束与审计的直线走廊都失去物理依据。

**建议改为两句**：

1. 缆绳假设为**张力控制绞盘维持绷紧**，放线长度等于锚点–机体距离，
   上限 35 m。因此可达域为球、缆绳占据锚点→机体的直线段——二者都是该
   假设下的**精确**结果，而非近似。（该假设有真实硬件对应：商用系留
   无人机普遍使用张力控制绞盘，正是为避免松弛缆绳缠绕勾挂。）
2. 未建模项收窄为：**张力对机体的反作用力、绞盘收放速率上限、缆绳气动
   耦合**。「sag」在绷紧假设下不存在，不应再列为未建模项。

**代码零改动**——`TetheredDronePlant` 现有实现恰好就是绷紧模型。

---

## 5. 可证伪的验收条件

### 5.1 采集设计

- 载体：**主环线 `config/scenario.default.json`**，锚点 `(132, 117)`
  **不动**，高度 `25.0 m` **不动**，路线/场景/系留长度**均不改**。
- 两臂：**A = 云台-only**（现状 `hold_body()` 行为）；**B = 阈值式机身
  分配**（§3.5）。
- 配对：同 scenario、同 `random_seed: 0`、同起点 `route[0]`、同 tracker
  与重锚定配置、同冻结初始框，**只切换 planner**；按**路线里程**配对
  （§3.3），不按时间。
- 每臂 **≥ 5 个 trial**（每次 Play 一个，测量窗为可见弧 ≈ 60 s）。
- 两臂都启用 `P1-DETECT-001` 三门重锚定，把重捕获能力 held constant。

### 5.2 三个前置阻断的处置

| 阻断 | 处置 | 状态 |
|---|---|---|
| **BC-M34-4 (a) 实义 `C_geom` 缺口** | §3.1：下界 `0.5645`、缺口 `≈0.44`、归因 `Building_Stadium`；谓词经真实 Unity 数据验证 | ✅ **本稿已证** |
| **BC-M34-4 (b) 合法机身动作存在性** | §3.2：`C_quality` 面积 2.53×、中心误差 21×，且已含系留走廊约束与 2.11 m 机身净空 | ✅ **本稿已证** |
| **BC-M34-4 (c) 支撑/净空审计** | 主环线**没有**锚点放置合同（只有 SCENE-003/004 两份），`(132,117)` 从未过审计。列为**批次 1a 的第一个工具**，复用 `P1Scene003AnchorAuditor` 几何原语，不新造 | ❌ **待做，进批次 1a** |
| **BC-M34-6 可见性模型来源** | 批次 1 不使用任何可见性模型：planner 只读 `camera_forward_world` 导出的裕度与方位。**机械检查**：在线与离线决策路径对任何可见性模型/遮挡先验/`WorldModelHandle` 类工件**零引用**，进复核范围。BC-M34-6 对**批次 2 全额有效**，未被本批次以任何方式预先满足 | ✅ 机械化 |
| **BC-M34-9 门序** | BC-M34-4 三条齐了即**满足**该门而非绕过。`config/scenario.scene-validation.json`（BC-M34-4 指名的「既有 SCENE-002 困难路线」）与 `scenario.default.json` 的 `target.route_world_m` 与 `anchor_world_m` **逐字相同**，故本批次做的正是该门要求的那条路线 | ⏳ 待 (c) 完成 |

**round 1 第 9(b) 条据此处置**：本稿**不请求**门序授权，而是主张
**满足** BC-M34-4。(c) 完成后由接受角色裁定是否成立；若接受角色认为
不成立，本批次停在 1a，不进入 1b/1c。

### 5.3 `BodyPlanner` 接口（round 1 附注 2：按 BC-M34-7 逐项对映）

```
BodyPlanner.decide(
    platform: PlatformState,     # 位姿、camera_forward_world、饱和标志、capture_monotonic_s
    estimate: WorldEstimate|None,# 均值+协方差+时戳（批次 1 不消费，为批次 2 预留）
    now_monotonic_s: float,
) -> BodyCommand
```

| BC-M34-7 停点项 | 本稿冻结 |
|---|---|
| command / sequence ID | 复用既有 `packet()` 的 `command_id = time.time_ns()`，单调递增；receiver 已按 `command_id` 去重 |
| 坐标系与单位 | 世界系、m/s；`velocity_world_mps` 三分量，`y` 恒 0（仅水平） |
| 模式 | `hold` / `velocity_world` 两种；**不引入 waypoint 模式** |
| issue / valid-until | `issued_unix_s` + `expires_after_s = 2 / capture_hz`；过期由 receiver 回落 `Hold()` |
| 速度/加速度/系留约束 | 速度由 `v_cmd_mps` 与 plant 双重钳位；加速度由 plant `MoveTowards`；系留由 plant 球约束 + planner 走廊检查（§3.5） |
| ACK / 拒绝 | 本批次**无 ACK 通道**（既有 body 通道即无）；planner 决策与 receiver 实际生效值分别记入 run log 与帧元数据，离线比对 |
| stale / 重复 / 乱序 | `command_id` 去重（receiver `:77`）；过期检查（`:99-103`）；乱序不可能（单发布者、单调 ID） |
| fail-safe | 三条硬性：`decide` 是**纯函数**（无 I/O、无真值访问）；`estimate is None` 或平台状态不可构造 ⇒ 必须返回 `hold`；**planner 之外任何位置不得发 body 指令** |

### 5.4 验收条件

1. **在线零真值** + **零可见性模型**：两条机械检查通过（§4.2、§5.2）。
2. **配对成立**：两臂的 scenario SHA-256、seed、起点、tracker 配置、
   初始框逐项相同，只有 planner 不同；差异清单入证据。
3. **测量窗合规**：可见弧区间在采集前哈希冻结；实跑按目标路线位置划窗，
   不按墙钟/步数；遮挡帧零进入主指标分母。
4. **H1**：臂A 实跑 `C_geom ∈ [0.5645, 1.0000]`；否则停批次重算几何。
5. **H2**：`C_quality` 三分量按里程加权配对比较，置信区间下界优于 0。
6. **代价轴齐备**：两臂各报 body-motion effort、tether 饱和占比、云台
   饱和占比、planner 切换次数、机体轨迹。
7. **估计器一致性**：离线报 NEES/NIS 与理论区间；`σ_px` 标定来源、
   SHA-256 与两条外推风险披露齐备。
8. **参数未后调**：§3.5 五个预注册值与实跑一致；§7 工具输出与之冲突时
   有回接受角色的记录，无就地修改。
9. **失败如实**：任何具名终态（`THRESHOLD_ALLOCATION_INEFFECTIVE` /
   `GEOMETRY_MODEL_REJECTED` / `SCENE_DEGENERATE` /
   `ANCHOR_PLACEMENT_AUDIT_FAILED`）如实报告并回指条款，不得换指标、
   换场景或换高度重报。
10. **措辞收窄**：主张上限为「机身分配改善**成像质量**」；`C_track|geom`
    未达显著时**不得**表述为「改善了跟踪」。

---

## 6. 基线、消融、失败模式和资源风险

- **基线**：臂A 即现状行为，无需新建。
- **消融**：本批次是 Pareto 前两点；词典序臂（第三点）属批次 2。
- **失败模式**
  - *几何模型错* → H1 证伪，停批次。**最有价值的失败**：在投入词典序
    分配之前暴露。
  - *估计器发散* → 不影响 planner（本批次策略不读估计器），但 NEES/NIS
    会暴露，且批次 2 会被它阻断。
  - *抖振* → 10° 迟滞带 + plant 加速度限位；工件必须报 planner 切换次数。
  - *`(132,117)` 过不了支撑面审计* → `ANCHOR_PLACEMENT_AUDIT_FAILED`，
    批次停在 1a，回接受/构思角色。**这是真实风险**：`P1-SCENE-003` 的
    1,257 个候选全数死在该门（根因是拿**路面**高程 `0.2 ± 0.05` 去要求
    草地实测 `≈1.3e-6`；`P1-SCENE-004` 改为**从实测支撑面推导**高程后
    通过）。主环线锚点是设计基线默认值，**不是审计通过的结果**。
  - *DETECT-001 在主环线退化* → 它全部资格化都在 SCENE-004。列为已知
    限制；因两臂 held constant，退化不破坏两臂可比性，但会压低
    `C_track|geom` 的绝对水平，须在证据中分列。
- **成本**：实现约 2–3 天；每臂 ≥5 次 Play，每次约 1 圈（≈107 s）但只测
  前 ≈60 s；零 API、零配额。

---

## 7. 建议但不强制的实现范围

- **批次 1a 工具（顺序有意义，第一个是门）**
  1. `tools/check_anchor_placement.py` + Editor 侧查询：主环线锚点
     `(132,117)` 的**支撑面/净空审计**，复用 `P1Scene003AnchorAuditor`
     几何原语（BC-M34-4 (c)）
  2. `tools/check_scene_body_margin.py`：§3.1 的 15 点同构谓词复算，
     产出 `C_geom` 上/下界、可见弧区间、遮挡归因（零 Play）
  3. `tools/calibrate_pixel_sigma.py`：`σ_px` 离线重跑标定（§3.4）
- **批次 1a 运行时**
  4. `controller/world_estimate.py`（KF + 解析 Jacobian 量测协方差）
  5. `controller/body_planner.py`（`BodyPlanner` 接口 + 阈值实现 +
     系留走廊检查 + hold 实现）
  6. `controller/track_loop.py` 逐帧接入（§2 分支表）
- **批次 1c 分析**
  7. `tools/analyze_m3_body.py`：离线 join、`C_track|geom`、`C_quality`、
     effort、NEES/NIS、里程加权配对
- **产物**：`config/p1-m3-body-001.json`；
  `docs/evidence/P1-M3-BODY-001-{anchor,margin,calib,run}.md`

```
批次 1a  工具 1（锚点审计）-> 若 FAIL 则整批停
         -> 工具 2/3 + 运行时 4/5/6（零 Play、零采集）
         -> 接受角色写入归因 + 强制停点（控制决策逻辑变更，§4.3.1）
         -> 独立复核（一次性 worktree）
批次 1b  COORD-005 人眼保真检查（≥2 张样帧：目标为红色运行时对象；
         主环线道路/走廊审计重跑）
批次 1c  臂A / 臂B 各 ≥5 trial -> 离线分析 -> 结果回接受角色
批次 2   L1 阶梯 + 词典序 P1/P2 分配（消费协方差；BC-M34-6 在此全额到期）
```

---

## 8. 本提案自身的边界声明

不实现任何代码、不运行任何实验、不消耗 ID/配额、不修改设计基线与
`P1-M3M4-SCOPE-001` 章程、不自行标记 `ACCEPTED`。§0 与 §3 的全部数值为
构思角色本轮从冻结字节离线复算的**非权威预扫**，实现时须由 §7 的工具
机械重算并以其输出为准。§4.3 是**修订请求**，其执行归接受角色。
提交后交接受角色 round 2 裁定。
---

## Acceptance review decision

### Acceptance round 1 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

批次的立项动机接受侧独立复核**成立**：`hold_body` 全文只在
`controller/track_loop.py:154` 定义、`:304` 调用一次，盘上 22 个带
`camera_position_world_m` 的归档目录（`runtime/frames`、RATE-002 全部
formal/smoke、RATE-003 clock-smoke、DETECT qual-1/2、scout-1/3/4 交换、
SCENE-002 attempt 3、TRACK-002 pilot 等）位移跨度**全部恰好
`0.000000 m`**——机体确实从未动过，决策层确实为零。先冻结
`BodyPlanner` 接口、再交付 Pareto 前两点，方向正确；§6 对"主环线从未
跑过跟踪运行、SCENE-006 F23 灰色替身帧作废、需重跑道路/走廊审计 +
COORD-005 人眼保真检查"的自陈也准确，接受侧同意其为批次 1b 硬前置。

但本稿五处**承重数值/前提**经接受侧独立复算为错，且其中三处正是
`P1-M3M4-SCOPE-002` 在接受要求下**已撤回、并在其关闭记录中作为已知
技术障碍永久保留**的构造；该关闭记录明确"任何后继 lean-M3′ 提案须
以新 work ID 立项并逐条面对这些记录，不得默认继承本提案任何构造"。
H1 的预注册区间、场景适配性结论和 `σ_px` 标定计划全部坐在这些错误
之上，无法用 binding note 放行。另有两项超出接受角色权限（主指标、
门序），本轮不予授予。

Required revisions for round 2：

1. **修正机体高度基线 `25.2 → 25.0 m`，并同步全部派生值。** 锚点
   `y = 0.2`、`drone.initial_altitude_m = 25.0`，而 plant 按
   `relative = position − anchor` 钳制高度（`TetheredDronePlant.cs:41-46`），
   路线 `y = 0.2` ⇒ 机体在**目标平面之上 25.0 m**，不是 25.2 m。接受侧
   复算：最远顶点水平距 `69.112228 m`，`atan(69.112228 / 25.0) =
   70.113398°`，与 `P1-M3M4-SCOPE-002` §1.1 事实 3 已核实的
   `70.113398°` 逐位一致；本稿的 `69.97°` 恰是 `atan(69.112228 / 25.2)
   = 69.966914°`，来源就是这 0.2 m。因此静止未饱和半径应为
   **`25.000000 m`**（非 `25.20 m`），对应弧长占比 **`0.264650`**
   （非 `0.2666`；本稿值可用 `R = 25.2` 逐位复现）。`0.264650` 与
   SCOPE-002 关闭记录保留的"云台饱和弧长占比 `0.7353`"互补一致
   （`1 − 0.7353 = 0.2647`）。H1 的预注册区间必须按修正值重新给出。
   可动上界 `h* = 24.748737 m`、半径 `49.497475 m`、弧长占比
   `0.566037` 复算无误，保留；`altitude_hold_m = 25.0` 与 `h*` 的可达
   半径差 `0.0026 m` 亦复算无误，保留。

2. **撤回"弧长占比 = 时间占比"与"一圈 106.5 s"，改用冻结的有限步
   horizon。** `LoopTargetVehicle.Step` 在距顶点 `< 0.5 m` 时只推进
   `waypointIndex` 并 `return`（**该步不移动**），每顶点停顿整一步；
   且**不存在真周期**：接受侧按 `dt = 0.2`、`speed = 2.0`、float32 从
   `Configure` 初态复算，538 步后位置为 `(125.273216, 117.264130)`，
   不是 `route[0] = (125.5, 117.5)`。这与 SCOPE-002 round 2/round 3 的
   改正逐位一致，并已作为"无真实目标状态周期"写进其关闭记录。
   "每臂 ≥ 3 圈（一圈 `212.97 / 2.0 = 106.5 s`）"因此不是可核对的采集
   量。修订稿须改为从 `Configure` 初态起的**冻结步数 horizon**（给出
   确切步数与秒数）并对完整目标 trace 做哈希绑定；所有以"圈"表述的
   时长、H1 区间与占比随之重算（接受侧参考：538 步时间占比
   `0.263941`、539 步 `0.265306`，与弧长值 `0.264650` 相差约 `0.001`）。

3. **撤回 `C_geom = 1.0000` 的目标中心推断，改用与 evaluator 逐字
   同构的 15 点谓词离线复算。** §3.1 只判了目标**中心**是否在视锥内，
   即断言 `C_geom` 在主环线被做满。`CoverageEvaluator.cs:732-748` 判的
   是 `VisibilitySamples` 的 15 点（8 个包围盒角 + 中心 + 6 个轴向
   极值）中 `visibleCount / 15 >= minimum_visible_sample_fraction`
   （本 scenario `= 0.2`）**且未被遮挡**；`if (!inFrustum) continue;`
   而分母恒为 15，故**中心在锥内不蕴含 ≥3/15 通过**——SCOPE-002
   revision 2 已在接受要求下撤回同型推断。关闭记录保留的"视锥损失
   弧长占比 `0.0000`"同样是**仅目标中心、仅指向**口径，不得升格为
   `C_geom` 的任何上下界。补充事实：`config/scenario.scene-validation.json`
   与主环线**同路线、同锚点**，其 `UT-P1-SCENE-002-001` attempt 3 在
   `LookNadir()` 下实测 `C_geom = 0.219562724`、913/913 遮挡代理全部
   工作；主环线在**活动云台**下的 `C_geom` **从未测过**——既无
   `1.0000` 的证据，也不能假定它没有实义缺口。修订稿须先用同构谓词
   （含遮挡）离线给出主环线 `C_geom` 的可复算估计，再决定指标层级。

4. **`C_point` 现定义不是"零 tracker 参与的纯平台量"，须改定义或
   撤回该表述。** §3.2 把 `C_point` 定为 `gimbal_saturated == false`
   的帧占比。但 `TetheredGimbal.cs:37-38` 的
   `Saturated = requested > maximumOffNadirDeg + 0.1f`，其中
   `requested` 来自 `track_loop.py:615` 的
   `look_at(intersection.point_world_m)`——即**估计器输出**；无观测帧
   云台保持上一指令。该量因此是闭环量，随 tracker/估计器质量变化，
   臂 A/臂 B 之差会混入估计器差异。而 H1 又拿它与 §3.1 的**真值几何**
   预测比较，会把"几何模型错"与"估计器错"混成一次证伪。修订稿须
   二选一并贯彻到 H1/H2/§5.4：(a) 把 `C_point` 定义为离线按 `frame_id`
   join 真值几何计算的 `atan(D_true / h) ≤ 45°` 占比（纯平台/几何量，
   与 §3.1 解析预测同构），把 `gimbal_saturated` 占比作为**另一个**
   闭环量单列；或 (b) 保留闭环定义但撤回"零 tracker 参与"表述，并为
   H1 换一个不受估计器污染的证伪对象。两种选择都须写明 `+0.1°` 死区
   对占比的影响。

5. **`σ_px` 的指定标定源在盘上不存在，须换源或换方法。** §3.3 指定
   "由既有归档离线标定（`scout-4` 2405 帧图像–真值配对，比较 tracker
   框中心与真值框中心的像素残差）"。接受侧核对：
   `runtime/p1-scene-004-scouting/p1-scene-004-scout-4/truth/` 确有 2405
   个文件，但**全部是 JSON、零图像**（该会话目录只有一张
   `reference-preview.jpg`）；`runtime/test-results/p1-scene-004-scout-4-closed-exchange/frames`
   同样无 JPEG。归档里既没有可回放的图像，也没有存下的 tracker 框，
   该配对无法构造。此外该归档 `manifest.gimbal_driver =
   truth_directed_scouting`，并非跟踪回路；scout-4 又是 **SCENE-004**
   近天底 benign 几何，把其像素残差外推到主环线 70° 离轴、目标贴画面
   边缘的构型缺少依据。修订稿须给出**确实存在且可复算**的标定源
   （路径 + SHA-256），或改用不依赖图像回放的保守上界式 `σ_px`，并
   如实标注其保守性与跨场景外推风险。

6. **`track_loop` 接入点的描述与实际不符，实现范围须按真实结构
   重写。** §1.1/§2 称 `:304` 是"无条件 `hold_body()`"。实际 `:304`
   位于 `initialize()` 内、受 `if self._rate_lifecycle is None:` 保护，
   且是整个运行中**唯一一次** body 发布。因此本批次不是"替换一行"，
   而是要在**逐帧回路中新增** planner 调用。修订稿须逐条写死以下分支
   的期望 body 行为：`_rate_lifecycle` 非空、初始化期、无观测帧、
   `qualification_lifecycle` 非空、以及 `BodyCommandReceiver` 过期回落
   与 planner `hold` 的关系。写不死，实现角色无法按字面执行，复核范围
   也无法确定。

7. **BC-M34-3 的触发量。** 章程把阈值臂触发量**冻结**为
   `PlatformState` 发布的**当前云台限位裕度**，并明确排除"预测时域内
   的离轴角"。§3.4 的 `θ̂` 由估计器均值算出。修订稿须择一：把触发量
   写成 `PlatformState` 发布的当前云台限位裕度（并说明该量如何从帧
   元数据构造、与 `θ̂` 在何条件下等价、以及饱和后裕度恒为 0 时如何
   仍能触发与解除），或把它作为对 BC-M34-3 的**显式修改请求**列入
   第 9 条（须用户授权）。

8. **BC-M34-8 的冻结次序。** 章程要求阈值基线参数在**场景适配性报告
   之后、任何 Pareto 测量之前**冻结；本稿在报告之前就冻结了
   `35.0 / 25.0 / 4.0 / 3.0 / 25.0`。接受侧不反对更早冻结（更严、无
   反选风险），但修订稿须写明：这些值在 §7 检查工具机械复算产出后
   **不得**再调；若工具输出与预注册值冲突，唯一合法动作是回接受角色，
   不得就地改参数。

9. **两项须用户授权的事项，修订稿不得自行假定答案。** 以下两条超出
   接受角色权限；SCOPE-002 三轮请求同类修改，**任何一轮都未获得
   charter amendment**，其关闭记录明确"BC-M34-4/5/6/9 与 BC-M34-7
   保持语义不变"。本轮同样不予授予：
   - (a) **主指标**：设计 §6 的四指标不含 `C_point`；§6 反天花板条款
     与风险表 R1 要求的是 `C_geom` 显著低于 100%。把 `C_point` 立为
     某个 M3′ 批次的**预注册主指标**属主指标事项。（若第 3 条的同构
     复算显示主环线 `C_geom` 本就有实义缺口，本条可能自动消解，届时
     无须动用授权。）
   - (b) **门序**：BC-M34-9 的实现顺序是 M2 关闭 → **SCENE-005 通过
     其自身门** → 规划器接口停点 → M3′ 其余实现；BC-M34-4 要求在证明
     基线 `C_geom` 有实义缺口等三条之前**禁止开始三策略 Pareto 采集**。
     §4.1 只论证了 M2 那一段，未处理 SCENE-005 这一段，而批次 1c 的
     两臂配对采集就是 Pareto 的前两点。
   建设性提示（接受侧观察，不构成预先授予）：BC-M34-4 指名要先评估的
   "既有 SCENE-002 困难路线"与本批次选的主环线**是同一条路线、同一个
   锚点**（`config/scenario.scene-validation.json` 与
   `config/scenario.default.json` 的 `target.route_world_m` 与
   `anchor_world_m` 逐字相同）。因此若修订稿在这个载体上把 BC-M34-4 的
   (a) 实义 `C_geom` 缺口（用第 3 条的同构谓词）、(b) 合法机身动作存在性
   （§3.1 可达性核查的修正版）、(c) 支撑/净空审计三项一次做齐，就可能是
   **满足**该门而不是绕过它，两条授权请求都可能不必动用。修订稿若走这条
   路，须显式说明它主张满足的是 BC-M34-4 哪一条、证据在哪。
   修订稿须把这两条作为**显式修改请求**单列（含理由与最小必要范围），
   由用户裁定；在获得逐字授权并记入 `docs/authorizations.md` 之前，
   接受角色不接受任何依赖它们的批次。

10. **BC-M34-6 的"不适用"主张须机械化。** §5.2 称批次 1 不使用可见性
    模型故该阻断不适用。接受侧原则上接受"无先验即无可击穿的真值
    边界"这一读法，但须机械可核：修订稿须把它写成与 §4.2 真值检查
    并列的一条机械检查——批次 1 的**在线与离线决策**代码路径对任何
    可见性模型/遮挡先验/`WorldModelHandle` 类工件零引用，且该检查
    进入复核范围；同时写明 BC-M34-6 对批次 2 全额有效，未被本批次以
    任何方式预先满足。

非阻断注记（随修订稿带走，不单独构成退修理由）：

- 两臂共同启用 `P1-DETECT-001` 三门重锚定作为 held-constant 是正确的
  归因设计；但 DETECT 全部资格化都在 SCENE-004，在主环线上从未资格
  化。修订稿应把这一点写入已知限制，并说明其若在主环线退化，两臂
  如何仍然可比。
- §5.3 的 `BodyPlanner` 三条硬性（纯函数、`None`/超龄必 `hold`、
  planner 之外不得发 body 指令）方向正确，予以保留；但接口冻结本身
  受 BC-M34-7 约束，其停点内容（command/sequence ID、坐标系与单位、
  HOLD/velocity/waypoint 模式、issue/valid-until、速度/加速度/系留
  约束处置、ACK/拒绝、stale/重复/乱序与 fail-safe 语义）须在修订稿
  中逐项对映，不能只给 `decide` 签名。

Disposition:

- 本轮**不授权**任何实现、Edit Mode、Play、session/run/profile ID、
  配额或 API 消耗；批次 1a/1b/1c 全部未启动，零消耗。
- `P1-M3M4-SCOPE-001` 与 BC-M34-1…10 本轮**零修改**；
  `P1-M3M4-SCOPE-002` 的终态及其保留的负结果不受本轮影响。
- `P1-SCENE-005` / `P1-SCENE-007` 的既有 verdict 与暂停状态不变。
- 构思角色提交 revision 1 后返回 Acceptance round 2。

---

## Revision 1 逐条回应（构思角色，2026-08-07）

**本轮方法**：与 CAL-001 各轮同法——先读真实代码与冻结字节、离线复算，
再改稿。本轮的复算产出了**两处推翻本提案自身的发现**（E3 使 `C_geom`
的结论反转、E2 使 revision 0 的"配对"前提失效），已按"失败也是有效产出"
如实登记并重构。

**1 — 机体高度基线 `25.2 → 25.0`。** 成立。`TetheredGimbal.cs:35` 的
`height = Mathf.Max(0.1f, -delta.y)` 取的是**机体世界 y 减目标平面 y**。
`C_point` 静止更正为 `0.264645`（与 SCOPE-002 保留的 `0.7353` 互补：
`1 − 0.7353 = 0.2647`）；`atan(69.112228/25.0) = 70.113398°` 与其记录
**逐位一致**。可动上界 `h* = 24.748…`、半径 `49.497475`、`0.0026 m`
高度代价三项复算无误，保留。**但 `C_point` 整个指标已按第 4 条撤回**，
故该修正只作勘误留档，不再进入任何判定。

**2 — 撤回"弧长=时间"与"一圈 106.5 s"。** 成立，且本稿按 float32 从
`Configure` 初态复算，dt=0.2 第 538 步得 `(125.273216, 117.264130)`，
**与接受侧所报逐位相同**。`Step` 在距顶点 `< 0.5 m` 时只推进
`waypointIndex` 并 `return`（该步不移动），每圈 8 个空转步。

**但本稿不采用"冻结步数 horizon"这个替代方案**，因为它仍依赖 dt，而
`grep captureDeltaTime|fixedDeltaTime|targetFrameRate` 于 `Assets/`
**零命中**——目标、云台、plant、receiver、`SensorFrameWriter` 全部走
`Time.deltaTime` = 渲染帧时。实测 dt=0.2 与 dt=1/60 走出不同轨迹
（545 步后 `(128.073,117.278)` vs 6402 步后 `(126.848,117.143)`）。
**连带后果：revision 0 §5.1 声称的"仿真确定性使两臂逐帧可比"不成立。**
§3.3 因此改为**按目标路线位置离线划窗、按里程加权配对**，对帧率抖动
完全免疫，且不依赖任何未成立的确定性假设。

**3 — 撤回 `C_geom = 1.0000` 的中心推断。** 成立，而且**结论反转**。
按 15 点谓词（8 角 + 中心 + 6 轴向极值，`visibleCount/15 ≥ 0.2`，且
`visibleCount` 要求在锥内**且** `HasClearLineOfSight`）离线复算：

- **视锥项确实饱和**：全路线 15/15 在锥内 ⇒ `C_geom` 上界 `1.0000`；
- **遮挡项不饱和**：`C_geom` 下界 **`0.5645`**，缺口 `≈0.44`。

谓词以真实 Unity 数据验证：同路线同锚点、`LookNadir()` 下复算
`0.210746` vs `UT-P1-SCENE-002-001` attempt 3 实测 `0.219563`，差
`0.0088`。这同时独立复现了 `DR-P1-M2-001` **N8/N6′** 的依据——该数
是**视锥主导**（0.2107/0.2196），确实不含遮挡信息。

场景重建亦经验证：899 个 PrefabInstance 中 **782 个**匹配
`obstacle_footprints`，与 `runtime/road_scene_audit.json` 的
`audited_obstacle_count: 782` **完全一致**；6 条 relocation 各匹配恰好
1 个根。主遮挡源为 `Building_Stadium`（世界盒
`x[127.620,172.376] y[−0.042,11.688] z[69.992,105.452]`，占环线内部
52.6% 面积），阻挡样本计数 5463。

**所以 `C_geom` 可用**，`BC-M34-4 (a)` 由此证成。

**4 — `C_point` 不是"零 tracker 参与"。** 成立。`Saturated` 来自
`requested` ← `track_loop.py:615` 的 `look_at(intersection.point_world_m)`
← tracker→geolocate，是闭环量。**本稿整个撤回该指标。**

改用设计 §6 既有的两个：主指标 `C_track|geom`（其条件化天然排除遮挡段），
机制指标 `C_quality`。选后者的理由是实测的：`C_geom` 二值可见性**按构造
无视云台饱和**，两臂只差 `0.5645 → 0.5857`；而 `C_quality` 差得很开——
面积中位 `851.6 → 2153.8 px²`（2.53×）、**中心误差中位 `130.3 → 6.2 px`
（21×）**、最小边 ≥20 px 占比 `0.873 → 1.000`。因果链每一环可测：
机体运动 → 解除云台饱和（`0.736 → 0.429`）→ 目标回中心且变大 →
`C_quality` → `C_track|geom`。

**5 — `σ_px` 标定源。** 第一句不成立：`runtime/test-results/
p1-scene-004-scout-4-closed-exchange/frames` **确有 2405 个 JPEG**
（本轮从中读出过目标中心像素 RGB `(158,35,38)`、S `0.78`，据此确认
scouting 归档拍的是红色运行时目标；顺带发现 `p1-scene-006/probe-*` 的
212 帧是**灰色替身**，S `≈0.016`，对任何外观相关用途作废——这与 F23 一致）。
接受侧查的是 truth 目录（该目录确只有 JSON + 一张 preview），而帧在
另一棵树。

**但实质结论成立且更强**：归档中**无 tracker 框**（scout-4 会话目录只有
completion/manifest/reference/scouting-result/truth，无 run log），故该
配对不能查档构造，必须**离线重跑 tracker**；且 `gimbal_driver =
truth_directed_scouting`、SCENE-004 近天底几何（斜距 26.1–30.5 m 窄带），
外推到主环线 70° 离轴缺依据。§3.4 已改为离线重跑 + 保守初值 + 两条外推
风险披露 + 实跑后回报对照。

**6 — `track_loop` 接入点。** 成立。`:304` 在 `initialize()` 内、受
`if self._rate_lifecycle is None:` 保护、全程只执行一次。§2 已改为
**逐帧回路新增 planner 调用**，并给出七行分支表（`_rate_lifecycle` 非空、
初始化期、无观测帧、`qualification_lifecycle` 非空、planner hold、
planner velocity、异常路径）逐条写死期望 body 行为，并说明
`BodyCommandReceiver` 过期回落与 planner `hold` 是两道**互不依赖**的保险。

**7 — BC-M34-3 的触发量。** 采纳章程口径，不申请修改。触发量改为
`PlatformState` 发布的**当前云台限位裕度**，由 v3 帧元数据既有字段
`camera_forward_world` 导出：
`theta_applied = acos(clamp(−forward.y,−1,1))`、
`margin = maximum_off_nadir_deg − theta_applied`；方向取
`bearing = atan2(forward.x, forward.z)`。**策略因此完全不读估计器**——
这比 revision 0 更强，顺带消除了"估计器误差混入两臂差异"这个混杂。

接受侧点名的"饱和后裕度恒为 0"已在 §3.5 写死：钳位后 `margin ≥ 0` 且
`= 0` 当且仅当饱和 ⇒ 触发必然成立；机体朝 `bearing` 平移使真实离轴角
降到 45° 内后 `margin` 转正 ⇒ 解除不依赖饱和期不可观测量。与 `θ̂` 的
等价条件亦写明：未饱和时相等，饱和时本量**保守**（低估紧迫度），
不会误触发。

**8 — BC-M34-8 冻结次序。** 已在 §3.5 末与 §5.4 第 8 条写明：五个预注册
值在 §7 工具机械复算产出后**不得再调**；冲突时唯一合法动作是回接受角色。

**9 — 两项须用户授权。** **均已消解，本稿不请求任何授权。**

- **(a) 主指标**：不再立 `C_point`。主指标是设计 §6 既有的
  `C_track|geom`，机制指标是同表既有的 `C_quality`，代价轴是同节诊断
  清单既有的"机身运动量"。**没有任何新指标。**
- **(b) 门序**：本稿主张**满足** BC-M34-4 而非绕过它。接受侧的提示经
  核对成立——`config/scenario.scene-validation.json` 与
  `scenario.default.json` 的 `target.route_world_m` 与 `anchor_world_m`
  **逐字相同**，故本批次做的正是 BC-M34-4 指名的那条路线。三条中
  (a)(b) 本稿已证（§5.2），(c) 支撑面/净空审计列为**批次 1a 的第一个
  工具**且是硬门——不过则整批停在 1a。是否成立由接受角色裁定。

**10 — BC-M34-6「不适用」机械化。** 已写成与真值检查并列的机械检查
（§5.2）：批次 1 的**在线与离线决策路径**对任何可见性模型/遮挡先验/
`WorldModelHandle` 类工件**零引用**，进复核范围；并写明 BC-M34-6 对
**批次 2 全额有效**，未被本批次以任何方式预先满足。本批次策略只读
`camera_forward_world` 导出的裕度与方位，天然无可见性先验。

**两条非阻断注记的处置**：

- DETECT-001 只在 SCENE-004 资格化过，主环线上表现未知 → 已写入 §6
  已知限制；因两臂 held constant，退化不破坏可比性，但会压低
  `C_track|geom` 绝对水平，须在证据中分列。
- `BodyPlanner` 接口按 BC-M34-7 停点项**逐项对映**（§5.3 八行表），
  不再只给 `decide` 签名。

**本稿新增的两项（非必修项，但影响可执行性）**：

- **系留走廊检查进 planner**（§3.5）。实测径向策略有 **41.43%** 的路线
  位姿会让缆绳穿过障碍（体育场 73 / 冷杉 47 / 路灯 5）；而仿真**不会
  阻止**这种指令（`TetherLineVisual` 是纯 `LineRenderer`、零碰撞体，
  plant 只做球约束）。启用检查的代价实测仅 `−0.005` `C_geom` /
  `−3.2%` 面积 / 中心误差不变，计算开销 `1.9 μs`（Python + 广相位，
  782 盒筛到 6 盒），C# 下 5 Hz 占比 `< 0.001%`。
- **系留绷紧假设的设计修订请求**（§4.3）。实测标称悬停点松弛
  **`10.00 m`**（弦长 25.00 vs 放线上限 35.00）；缆绳只在贴球面时才自然
  绷紧，故现有"球约束 + 直线走廊"缺物理依据。建议把"张力控制绞盘维持
  绷紧、放线长度 = 锚点–机体距离"写成显式假设——它有真实硬件对应，
  且**代码零改动**（`TetheredDronePlant` 现有实现恰好就是绷紧模型）。
  这是**请求**，执行归接受角色。

**授权与边界**：本稿不主张任何新授权，不实现、不运行、不消耗
ID/配额、不写 `config/`/`Assets/` 字节、不动设计基线与章程。提交后
返回 Acceptance round 2。

---

### Acceptance round 2 — 2026-08-07

Decision: **ACCEPTED_WITH_BINDING_CLARIFICATIONS**

Rationale:

接受侧本轮对 revision 1 的全部可核对承重主张做了独立取证，逐项成立：

- **代码结构**：`TetheredGimbal.cs:35` `height = Mathf.Max(0.1f, -delta.y)`、
  `:37` 45° 钳位、`:38` `+0.1f` 旗标死区；`LoopTargetVehicle.Configure`
  每次置 `route[0]` 且 `Step` 距顶点 `<0.5 m` 只推进索引不移动；
  `TetheredDronePlant` 球约束/限高/`MoveTowards(4)`；`BodyCommandReceiver`
  20 Hz 轮询、`:77` 等值去重、`:99-103` 过期、缺失/过期/门控一律 `Hold()`；
  `track_loop.py:154` 定义、`:303-304` 在 `initialize()` 内受
  `_rate_lifecycle is None` 保护的唯一一次 `hold_body()`、`:615`
  `look_at(intersection.point_world_m)`；`CoverageEvaluator.cs:727-764`
  15 点谓词 + `minimum_visible_sample_fraction=0.2` + `:751-755`
  面积/中心误差公式、`:814-841` 采样点构造——全部与 revision 1 描述逐行相符。
- **无固定时间步**：`grep captureDeltaTime|fixedDeltaTime|targetFrameRate`
  于 `Assets/` 0 命中，复现「一切积分走渲染帧时」的结论；位置划窗替代
  方案因此成立（比 round 1 给的「冻结步数 horizon」参考方案更强，接受
  侧采纳该改进）。
- **载体同一性（satisfaction 主张的前提）**：
  `config/scenario.scene-validation.json` 与 `config/scenario.default.json`
  的 `target.route_world_m` 与 `anchor_world_m` 本轮程序化比对**相等**；
  最远顶点水平距 `69.112228 m`、`atan(69.112228/25.0)=70.113398°`、环线
  周长 `212.97 m`、`120.2/212.97=0.5644…` 与 revision 1 数字一致。
- **v3 帧字段**：`SensorFrameWriter.cs` v3 含 `camera_forward_world`
  （取自 `camera.transform.forward`，即钳位+slew 后的真实指向）、
  `gimbal_saturated`、`tether_saturated`、`capture_monotonic_s`——
  BC-M34-3 触发量的构造材料确为已发布平台量。
- **σ_px 事实链**：`runtime/test-results/p1-scene-004-scout-4-closed-exchange/frames`
  实数 2405 个 JPEG；scout-4 会话目录仅
  completion/manifest/reference*/scouting-result/truth（truth 2405 个
  JSON），确无 run log；`manifest.gimbal_driver = truth_directed_scouting`
  逐字属实。round 1 第 5 条第一句（帧不存在）由接受侧撤回——接受侧当时
  查的是 truth 目录；revision 1 的更正与「须离线重跑」的实质结论都成立。
- **场景与工件来源**：`config/road_data.json` 有 89 类
  `obstacle_footprints`；`runtime/road_scene_audit.json`
  `audited_obstacle_count: 782` 为实例数，与 revision 1「899 个
  PrefabInstance 中 782 个匹配」口径一致；`Building_Stadium` 资产存在；
  `road_data_sha256` 已被 scenario 钉住。`packet()` 的
  `command_id = time.time_ns()` 属实。

十条必修项全部按要求落地；E2/E3 两处推翻自身的实测勘误按「失败也是
有效产出」如实登记且使设计更强。第 9 条两项授权按 round 1 预留的
「满足而非绕过」通道消解成立（裁定条款见 BC-BODY1-3）：**本轮不需要、
也不请求任何用户授权**。

本轮新查出的缺陷有四处——走廊工件纪律缺失且与自身「零引用」措辞冲突、
H2 的 CI 判定与冻结的 BC-M34-8 冲突、H1 的计算定义域未写明、批次 1a 把
BC-M34-7 独立接口停点与策略实现合并——均不动摇动机与实测地基，且提案
§7 自称「建议但不强制」，故全部以可逐条核对的 binding clarifications
就地解决，不再消耗一轮修订。

Binding clarifications（实现角色按字面执行，歧义退回接受角色，不得自行解释）：

1. **BC-BODY1-1（指标与措辞）**：批次指标只用设计 §6 既有定义——主
   `C_track|geom`；机制 `C_quality`，预注册三分量为面积中位、中心误差
   中位、最小边 ≥20 px 占比；代价轴 body-motion effort
   `∫‖v_applied‖dt`（由 applied 速度记录离线积分；称 effort，不称
   energy）；云台/系留饱和占比与 planner 切换次数仅诊断、不判定。
   `C_point` 在本 work ID 内整体撤回，实现期不得新立任何指标。主张上限
   为「阈值式机身分配改善成像质量」；`C_track|geom` 未达显著改善时，
   证据、状态板与论文素材一律不得写「改善了跟踪」。
2. **BC-BODY1-2（测量窗与 H1 定义域）**：测量窗 = 目标路线里程
   （`CoverageEvaluator` 真值流离线按 `frame_id` join 后折算）落在
   工具 2 产出并 SHA-256 冻结的可见弧区间内的帧；禁止墙钟/步数划窗。
   一次 Play = 一个 trial，起点恒为 `Configure` 置 `route[0]`，冻结
   初始框跨 trial 同一。工具 2 必须核证 `route[0]` 位于可见弧内，否则
   回接受角色。**H1 的 `C_geom` 在整圈定义域计算**（trial 全程帧，含
   遮挡弧），其预注册区间以工具 2 机械输出为准（§3.1 数字仅为预扫，
   实质背离时先回接受角色再谈采集）；`C_track|geom`/`C_quality`/H2 只
   在测量窗内计算，遮挡帧零进入其分母。
3. **BC-BODY1-3（批次结构、BC-M34-7 停点与 BC-M34-4/9 裁定）**：
   批次 1a 拆分为两个停点批次：
   - **1a-α = BC-M34-7 规划器接口独立停点批次**。顺序：工具 1
     （`(132,117)` 支撑面/净空审计）为第一个动作且是硬门——FAIL ⇒
     `ANCHOR_PLACEMENT_AUDIT_FAILED`，整批停、回接受/构思，零后续
     工作；然后工具 2（15 点同构复算：`C_geom` 上下界、可见弧区间、
     遮挡归因、`C_quality` 投影复算）、工具 3（σ_px 离线重跑）、走廊
     工件构建（见 BC-BODY1-4），以及版本化接口契约工件：`BodyPlanner`
     抽象 + §5.3 逐项契约文 + config schema + **M4′ 三用例需求预审
     记录**（L2a 扫描 / L2b 视角序列 / L4 等待位走查）+ **waypoint
     模式显式版本化延后声明**——航点能力仍属 M3′（设计 §4「M3′ 只
     提供等待位/航点能力」），最迟批次 2 以 contract v2 落地，届时按
     §4.3.1 控制协议变更单独停点。1a-α **零策略/估计器/track_loop
     代码**。稳定候选 → 接受角色停点确认（含对工具 1/2/3 输出的
     BC-M34-4 (a)(b)(c) 归因与 §4.3.1 条件 5 写入审计）→ 独立复核。
   - **1a-β = 估计器与策略批次**。`world_estimate.py`、
     `body_planner.py`（阈值 + 走廊 + hold）、`track_loop` 逐帧接入按
     §2 分支表逐字执行、run log 追加字段、`config/p1-m3-body-001.json`
     数值按 §3.5 预注册。控制决策逻辑变更 ⇒ 自身 §4.3.1 停点 + 独立
     复核。
   - **1b**：COORD-005 人眼保真检查（≥2 样帧确认红色运行时目标）+
     主环线道路/走廊审计重跑，先于任何正式采集。
   - **1c 采集四门**：1a-α 复核 PASS 且接受角色完成 BC-M34-4 归因；
     1a-β 复核 PASS；1b 完成；用户执行 Play。四门齐备前禁止任何臂的
     采集（两臂即 Pareto 前两点，受 BC-M34-4 采集禁令约束）。
   - **BC-M34-4/9 satisfaction 裁定**：BC-M34-4 的实质义务（在其指名
     的「既有 SCENE-002 困难路线」上先产出 (a)(b)(c) 报告）由 1a-α
     工具在**逐字节同一载体**上机械履行（两份 scenario 的
     `target.route_world_m`/`anchor_world_m` 本轮比对相等）。这是
     **满足门而非改序**，沿 round 1 预留的通道执行：BC-M34-1…10 文本
     零修改；SCENE-005/007 自身 verdict、暂停状态与剩余范围（定向
     难度改造、SCENE-007 前置、M1 Stage B 证据路径）不变，未被关闭、
     接受或偷渡（BC-M34-5 继续有效）；工具 1/2 任一不过即按 BC-M34-4
     原文「返回场景设计」车道，由用户决定重启方式。
4. **BC-BODY1-4（系留走廊工件纪律）**：走廊检查保留，但须满足：工件 =
   与 `config/road_data.json` `obstacle_footprints` 类型匹配的场景障碍
   实例（道路审计口径的 782 实例集）的世界系 AABB 棱柱集，由 1a-α 工具
   **离线**构建（road_data 已被 scenario `road_data_sha256` 钉住），
   产物版本化并把 SHA-256 记入 `config/p1-m3-body-001.json`；运行时
   只读该冻结工件，唯一允许的查询是「锚点→候选机体位置线段 × 棱柱
   相交」+ §3.5 缩短/hold 规则；批次 1 内该工件不得被任何可见性/遮挡
   预测、估计器或测量窗逻辑读取。§4.2/§5.2 的机械检查据此改述为：在线
   与离线**决策**路径对任何可见性/遮挡**预测**类查询与
   `WorldModelHandle` 类工件零引用，走廊工件是唯一被列名的静态几何
   输入且仅限上述用途；复核范围同时核这两条。本条**不预判**
   OQ-1/BC-M34-6：批次 2 的可见性先验物料来源仍全额待裁，未裁定不得写
   其实现代码。
5. **BC-BODY1-5（H2 统计口径按 BC-M34-8 执行）**：批次证据只报逐 run
   值与中位数，不构造任何 95% CI。§3.6/§5.4 的「置信区间下界优于 0」
   逐字替换为：三分量各自的里程加权配对差（B−A）满足 (i) 全部 trial
   汇总中位数 > 0，且 (ii) 每个 run 的配对差中位数逐 run 均 > 0
   （≥5 run 全同号）。需要 CI 表述须先经用户批准的 BC-M34-8 修订；对
   本判定式有异议在采集前回接受角色，不得事后改。
6. **BC-BODY1-6（触发量语义与 0.1° 死区）**：触发量/方向只由已发布 v3
   字段 `camera_forward_world` 决定性导出
   （`theta_applied = acos(clamp(−fwd.y,−1,1))`、
   `margin = maximum_off_nadir_deg − theta_applied`，常数读自冻结
   scenario `gimbal.maximum_off_nadir_deg = 45.0`；
   `bearing = atan2(fwd.x, fwd.z)`）；策略零估计器、零真值，符合
   BC-M34-3。精度条款：云台 applied 在 45° 钳位而 `Saturated` 旗标在
   45.1° 才置位（`TetheredGimbal.cs:37-38`），故 `margin = 0` 与
   `gimbal_saturated` **不严格等价**（0.1° 死区）；策略只准读 margin、
   不得读旗标，证据文本不得写「当且仅当」。五个预注册值按 §3.5 冻结，
   工具产出后不得再调，冲突唯一出路是回接受角色。
7. **BC-BODY1-7（σ_px 标定预注册）**：工具 3 在运行前把初始化策略
   （首帧真值框）、逐帧残差量、聚合公式与漂移/离群处置写死在工具与
   产物 schema 内；产出 σ_px 标为保守初值并记 SHA-256；两条外推风险
   （`gimbal_driver = truth_directed_scouting` 逐字；SCENE-004 近天底
   窄斜距带）逐字入标定证据文件；批次 1c 回报实测残差分布对照，需重标
   Q/R 时回接受角色。标定是离线工具活动，允许读归档真值；其产物进入
   在线侧的唯一形态是 config 中的冻结标量。
8. **BC-BODY1-8（零真值与双保险机械检查）**：在线代码路径对真值文件与
   evaluator 输出零引用，进复核范围（机械检查）；§2 七行分支表逐字
   执行，异常路径 `hold()` 且异常必须入 run log；`BodyCommandReceiver`
   过期回落与 planner `hold` 保持互不依赖的两道保险，实现不得让其中
   一道以另一道存在为前提；`expires_after_s = 2 / capture_hz = 0.4 s`
   入 config 冻结。
9. **BC-BODY1-9（§4.3 采纳与设计同步）**：采纳系留绷紧假设：张力控制
   绞盘维持绷紧、放线长度 = 锚点–机体距离（上限 35 m）；球形可达域与
   「缆绳占据锚点→机体直线段」是该假设下的精确结果；未建模项收窄为
   张力对机体的反作用力、绞盘收放速率上限、缆绳气动耦合。设计基线随
   本裁定升至 **v0.3.17**（§4 已知落差句、风险 R2 行、状态板活跃约束
   同批更新）；代码零改动；论文按 §4.2 纪律称显式假设（有商用张力
   绞盘硬件对应），不称高保真。
10. **BC-BODY1-10（消耗与授权边界）**：本裁定授权实现角色启动批次
    1a-α（含 Edit Mode 工具与 Editor 侧查询），其后按停点顺序进入
    1a-β；全程**零 Play、零 scenario/session/run ID、零配额、零
    API**。开发期目检/诊断 Play 只走 COORD-005 诊断通道（明确标注、
    不产 ID、不进证据）。批次 1c 的每次 Play 由用户执行，且以
    BC-BODY1-3 四门齐备为前提。BC-M34-1…10 语义零修改；
    `P1-M3M4-SCOPE-002` 终态及其保留负结果不受影响；本轮不关闭 M1、
    不动 SCENE-005/007 verdict。

Disposition:

- 状态门：`P1-M3-BODY-001` → `ACCEPTED_WITH_BINDING_CLARIFICATIONS`；
  交接翻转为实现角色执行批次 1a-α（主运行地 Cursor `/coding`）。
- 复核范围预告：1a-α 停点复核须含 BC-M34-4 三条输出的机械可复算性与
  接口契约完整性（含 waypoint 延后声明与 M4′ 三用例走查）；1a-β 停点
  复核须含零真值/零可见性引用两条机械检查、§2 分支表逐字符合、走廊
  工件唯一用途。
- 回退路径：工具 1 FAIL ⇒ `ANCHOR_PLACEMENT_AUDIT_FAILED` 回接受/构思
  （场景设计车道）；工具 2 输出与预扫实质背离 ⇒ 回接受；预注册参数
  冲突 ⇒ 回接受。均不得就地改参数、改区间或换载体重报。

---

### Acceptance round 3 — 2026-08-07（批次 1a-α 停点确认）

Decision: **STOP_POINT_CONFIRMED_RELEASE_TO_REVIEW**

停点对象：稳定候选 `81202ab`（SHA 补记提交 `a1fc9a1`）。
本轮**不需要、也不请求任何用户授权**；无消耗（零 Play / 零
scenario/session/run ID / 零配额 / 零 API）。

#### A. workflow §4.3.1 五条件核对

| 条件 | 结论 | 接受侧独立取证 |
|---|---|---|
| 1 实现范围与接口已冻结 | ✅ | `controller/body_planner.py` 确为 `ABC` + `@abstractmethod decide`，无阈值/走廊/hold 策略、无写入器；`81202ab` 的 27 个路径中无 `track_loop.py`、无 `world_estimate.py`。BC-BODY1-3「1a-α 零策略/估计器/track_loop」成立 |
| 2 相称的实现者测试通过 | ✅ | `runtime/test-results/p1-m3-body-001-editmode.xml` 盘上实文件：`testcasecount="258" result="Passed" failed="0"`；接受侧自跑 `tests.test_m3_body_tools` **55/55 OK** |
| 3 已知 Unity 失败已修复 | ✅ | 无 Unity 失败 |
| 4 复核范围/状态板/候选 commit/未验证风险已更新 | ✅ | 证据 §9 七条限制、§10 六条复核落点、状态板交接行齐备 |
| 5 实现写入审计 + 归因 | ✅ | 见 §B |

#### B. 条件 5 写入审计与逐路径归因

上一通过候选 = `d2db9f3`（`P1-SCENE-006` batch-2 复核 round 8 `PASS`，
2026-08-04，`docs/reviews/P1-SCENE-006.md`）。

```
python3 tools/check_role_writes.py --role implementation --base d2db9f3
⇒ exit 1，15 个越权路径
python3 tools/check_role_writes.py --role implementation --base 4cf811a
⇒ exit 0，27 个路径全部合规
```

15 个被标出路径**全部**归因到状态板记录的非实现批次，无一由
`81202ab`/`a1fc9a1` 触碰（`git log --oneline d2db9f3..HEAD -- <path>` 逐条
核对）：

| 被标出路径 | 归因批次 | 批次性质 |
|---|---|---|
| `AGENTS.md`、`docs/collaboration-workflow.md` | `286774d` | COORD-005 协调批次；提交信息逐字引用账本条目「2026-08-04 COORD-005」，符合 workflow §7 规则 7 的合规凭据要求 |
| `docs/authorizations.md` | `286774d`、`25fb57d`、`24963a5`、`6488c37`、`96a9530`、`87909f6`、`0902e44`、`bc49472`、`2671aa0` | 协调批次 + 接受/构思批次 |
| `docs/phase1-single-drone-design.md` | `8824c6b`、`24963a5`、`7fe0fee`、`07e2623`、`18733c6`、`6488c37`、`385e17b`、`4cf811a` | 全部为接受批次（v0.3.12→v0.3.17） |
| `docs/reviews/P1-SCENE-006.md` | `bf8797d`、`eb23d71` | 复核批次（round 8 + F23 addendum） |
| `docs/unity-test-log.md` | `1c990b4`、`385e17b` | 接受角色代录（该两批次只触碰接受/辅助允许路径，构造上不可能是实现批次） |
| 9 份 `docs/proposals/*` | `0b0b9b8`…`71fc2f8`、`af6b973`、`4cf811a` 等 | 构思提交 + 接受裁定批次 |

**归因完整，无不可归因路径 ⇒ 条件 5 成立。**

#### C. BC-M34-4 (a)(b)(c) 归因

接受侧自行重跑三个检查器复算，与证据文件数值逐位一致
（`check_anchor_placement.py` exit 0、`build_m3_corridor.py --check` exit 0、
`check_scene_body_margin.py` exit 0）。

**(a) 基线 `C_geom` 有实义缺口 —— `SATISFIED`（限定见 BC-BODY1-15）。**
工件 `scene-body-margin.json`：`upper_bound_frustum_only = 1.000000`、
`lower_bound_with_box_occlusion = 0.565728`、
`gap_from_saturation = 0.434272`，`occlusion_attribution` 把 3069 个被挡点
样本中的 **2808** 个归到单一具名建筑 `Building_Stadium`。
**限定**：AABB 高估阻挡 ⇒ 该值是**下界**，离线模型给出的区间
`[0.565728, 1.000000]` **不能把真值排除在 1.0 之外**，因此「缺口 ≈0.43」
不是被机械证成的点值。本条按其**反天花板用途**判定满足，并由
BC-BODY1-15 的天花板臂在 1c 首跑把退化情形做成可证伪终态。

**(b) 存在改变期望可见性的合法机身动作 —— `SATISFIED`。**
BC-M34-4 (b) 的字面判据是「期望**可见性**改变」，故正确的机械引用是
`c_geom.arm_b_lower_bound_with_box_occlusion = 0.584507` 对
`0.565728`，即 **+0.018779** 的可见性改变，落在非零测度的路线域上；
该动作在系留球（`sqrt(35²−25²) = 24.4949 m`）与走廊约束内实现，机身水平
位移中位 `21.35 m`、最大 `24.45 m`（`24.45 < 24.4949` ✅）。
**更正**：证据 §3.3 用 `C_quality` 三分量作为 (b) 的证成，那是**附加**
支撑而非字面判据；判据以上述 `C_geom` 增量为准。`C_quality` 结果（面积
中位 `1.82×`、最小边 ≥20 px 占比 `0.912→1.000`、云台饱和 `0.488→0.000`）
仍如实登记为机制层旁证。

**(c) 支撑/净空审计通过 —— `SATISFIED`（限定见 BC-BODY1-16）。**
硬门 1 `CLEAR`：支撑 `PASS`（`Road Lane_01 (30)@140,120`，
`surface_y = 0.20000043511390687`，高度误差 `−4.32e−07 m` ≪ 容差 `0.05`），
净空 `PASS`，阻挡体 **0**，受审障碍 764 / 场景根 896。合同五个安全值与
`p1-scene-003`/`p1-scene-004` 逐字节相同，**未提出任何新安全值** ⇒
BC-BODY1-10「本批次不请求用户授权」成立。

**总裁定**：round 2 BC-BODY1-3 的 **BC-M34-4/9 satisfaction 通道履行完毕**
——BC-M34-9 的门是**被满足**而非被绕过。BC-M34-1…10 文本零修改；
`P1-SCENE-005`/`P1-SCENE-007` 各自的 verdict、暂停状态与剩余范围不变，
BC-M34-5 继续有效，五项未认领用户授权一项未动。

#### D. 交回事项逐条裁定（证据 §12）

**事项 1（779 vs 782）⇒ 采纳实现角色的 779，见 BC-BODY1-11。**
BC-BODY1-4 括注里的「782 实例集」是**接受侧自己写错的数**：782 出自
`runtime/road_scene_audit.json`，其 `scenario_id` 是 `p1-scene-004`，是
另一个场景的计数。BC-BODY1-4 的约束性定义是类型匹配谓词，本载体自证
779。实现角色不自行重新解释、fail-closed 登记冲突的处置正确。

**事项 2（测量窗 62.5 m / 31.25 s）⇒ 确认为勘误，协议不变，见 BC-BODY1-13。**
接受侧复算：周长 `212.97056`，可见弧 `[155.0, 275.5)` 跨接缝 ⇒
`155.0→212.97` 段 `57.9706 m` + `0→62.5294` 段，合 `120.5 m`；
`120.5 / 2.0 m/s = 60.25 s` **正是提案 §5.1 写的「≈60 s」**——那句说的是
整条可见弧。BC-BODY1-2 把起点钉死在弧内第 `57.97 m` 处的 `route[0]`，
所以每 trial 只剩 `62.5 m = 31.25 s`。二者不矛盾，是 §5.1 括注口径错。
协议一个字不动（起点、弧、窗都不许改）；勘误登记 + trial 数改为**冻结的
恰好 5**。

**事项 3（H2 判定式风险）⇒ 判定式不放宽，见 BC-BODY1-14。**
接受侧确认根因与实现角色所述一致且是**定义域差异**：提案 §3.2 的
`21×` 是整圈口径（含遮挡弧那半边，臂A 在那里根本没戏），而 BC-BODY1-2
规定 `C_quality` 只在测量窗内算——对可见性做条件化本来就会压缩对比，
这正是 `C_track|geom` 的应有行为，不是缺陷。窗内 `[0, 62.5)` 臂A 饱和
占比 `0.488`（接受侧复算：北直道上水平距在里程 `31.5 m` 处越过 25 m 饱和
点，`31/62.5 = 0.496`，与 `0.488` 吻合），中位数恰落在转折点上。
**不因此放宽任何判定条件**——放宽就是用门数字反调判定式。处置是：补上
被漏掉的符号约定（否则中位数分量的字面读法是反的）、把部分结果的终态
名字改准确、并强制逐分量报告。

**事项 4（锚点在行车走廊内）⇒ 已披露、非门禁、强制列为限制，见 BC-BODY1-16。**
接受侧独立核实事实并加严了它的表述：`route_corridor_half_width_m = 1.5`
来自 `scene_adjustments.route_corridor` 的 `target_half_width_m 1.0 +
clearance_margin_m 0.5`，即**目标车辆自己的行车走廊**；而锚点的支撑是
一块**路面砖**（`source: road_surface`）——锚点站在马路上，位于
`P1-SCENE-001`/`P1-SCENE-002` 把所有场景障碍都赶出去的那条 1.5 m 走廊
之内，只因锚桅不是场景障碍实例才没被任何门看见。实现角色不自行增设新门
的处置正确。**不阻断**：接受侧另行核实其不可能污染测量——
`EvaluationOcclusionGeometry` 只从 `MeshRenderer` 建遮挡体
（`EvaluationOcclusionGeometry.cs:31,64,73`），而 `TetherLineVisual` 是
`LineRenderer` 且无碰撞体，故锚桅与缆绳既不遮挡也不碰撞。

**事项 5（`tests/test_check_docs.py` 既有失败）⇒ 归因成立，不影响停点。**
接受侧复跑确认：失败原因是 fixture 缺 `## Current state` / `## Active
handoffs` 两节而 `tools/check_docs.py` 现在要求它们，与本批次无关。
`tests/test_check_docs.py` 与 `tools/check_docs.py` 都是工作流基础设施，
对**包括接受角色在内的所有角色只读**，本轮不修改。修复须走用户直接
授权的协调批次，已在状态板登记为未闭义务。

#### E. 新增 binding clarifications（实现角色按字面执行，歧义退回接受角色）

11. **BC-BODY1-11（779 计数勘误）**：BC-BODY1-4 括注「（道路审计口径的
    782 实例集）」是接受侧的事实勘误，**以 779 为准**。约束性定义仍是
    「与 `config/road_data.json` `obstacle_footprints` 类型匹配的场景障碍
    实例」，其计数必须由**本载体自己的道路审计自证**，不得对硬编码字面量
    断言。已交付的走廊工件（779 棱柱，sha256 `9e2956ad…c800`）是正确且
    冻结的基准。`runtime/road_scene_audit.json` 的 782 属
    `scenario_id: p1-scene-004`，**永远不得**被引作本载体计数。
    BC-BODY1-4 其余文本不变；builder 的 fail-closed 冲突检查与
    `bc_body1_4_quoted_instance_count` / `bc_body1_4_count_conflict` 两个
    字段保留。
12. **BC-BODY1-12（R5 预注册文本缺陷，接受侧本轮新查出）**：
    `tools/check_scene_body_margin.py:47` 与 `:985-986` 把 R5 硬编码成
    「782 road-audit obstacle instances」，而同一工件的
    `identity.obstacle_instance_count` 是 **779**——预注册文本与实际基准
    自相矛盾。预注册字段正是防事后调参的东西，必须改对：批次 1a-β 内
    更正该串并重生成工件。**唯一准许的改动是该实例计数描述**；对 R1–R5
    任何其他改动都重开接受角色。重生成后 `scene-body-margin.json` 除该
    描述串与文件哈希外**每一个数值字段必须逐字节不变**，证据须给出该
    diff。批次 1c 前必须闭合，复核角色核验。
13. **BC-BODY1-13（测量窗勘误与 trial 数冻结）**：§5.1「测量窗为可见弧
    ≈60 s」是勘误——`60.25 s` 是整条可见弧，而 BC-BODY1-2 的 `route[0]`
    起点位于弧内第 `57.9706 m`，故每 trial 实为
    **`62.5 m = 31.25 s`**。协议**零改动**：起点、可见弧、测量窗、
    「进遮挡弧即结束 trial」全部维持原样，不得为拉长窗口改起点或让 trial
    跨遮挡弧（那会把重捕获能力混进主指标，正是 §3.3 要排除的）。
    trial 数由「≥5」改为**冻结的恰好 5 个/臂（共 10 次 Play）**，在首次
    Play 前记录：开口下限允许看到结果后再决定跑几个，是反调参漏洞。
    所有证据表格与论文素材必须写 `62.5 m / 31.25 s`，不得再写 ≈60 s。
14. **BC-BODY1-14（H2 符号约定、判定式不变、部分终态）**：
    (a) **符号约定**逐分量声明为**改善为正**：面积中位（大者优）、最小边
    ≥20 px 占比（大者优）、中心误差中位（**小者优**，故配对差按 `A−B`
    入式）。BC-BODY1-5 字面的 `B−A > 0` 对中心误差分量是**反的**，该字面
    读法作废。
    (b) **判定式不放宽**：H2 仍要求三分量**同时**满足 (i) 汇总中位数改善
    为正且 (ii) 逐 run 配对差中位数 5/5 同号。证据 §3.3 报告的失败风险
    **不构成**放宽理由。
    (c) **逐分量报告**，终态改为三档：三分量全过 ⇒ H2 成立；**≥1 但非
    全部**通过 ⇒ **`THRESHOLD_ALLOCATION_PARTIAL`**；一个都不过 ⇒
    `THRESHOLD_ALLOCATION_INEFFECTIVE`。有分量通过时**不得**使用
    `INEFFECTIVE` 这个名字——那是事实错误。
    (d) `PARTIAL` 下的措辞上限：只准点名**实际通过的那些分量**（例如
    「抬高了目标像素面积并消除了 <20 px 帧」），不得笼统写「改善了成像
    质量」；BC-BODY1-1 关于 `C_track|geom` 未显著即不得写「改善了跟踪」
    继续有效。
    (e) 两臂都必须报云台饱和占比与尾部统计（中心误差 max/p90），无论
    结果如何；它们按 BC-M34-8 仅诊断、不参与判定，**不构成新指标**。
15. **BC-BODY1-15（`C_geom` 区间措辞 + H1 天花板臂 + 首跑退化门）**：
    (a) 离线 `C_geom` 一律以区间 `[0.565728, 1.000000]` 报告并写明 AABB
    高估方向；「缺口 ≈0.43」作为点值主张**撤回**，准许的表述是「AABB
    下界 `0.565728`，3069 个被挡样本中 2808 个归于单一具名建筑，真值待
    批次 1c 实测」。
    (b) §5.4 的 H1 增加**天花板臂**：臂A 实测整圈 `C_geom ≥ 0.95` ⇒
    **`SCENE_DEGENERATE`**，停批次、回接受/场景设计。阈值 `0.95` **不是
    新立的**——它是设计 v0.3.17 既有的 `C_geom >= 0.95` 升级裁定线。
    原下界臂（`< 0.5645` ⇒ `GEOMETRY_MODEL_REJECTED`）不变。理由：H1 原文
    对 `[0.5645, 1.0]` 内任何值都通过，**包括完全退化的 1.0**，与设计
    §6 反天花板要求冲突。
    (c) **采集次序**：批次 1c 的**第一次 Play 必须是臂A trial 1**，其整圈
    `C_geom` 在任何后续 Play **之前**算出并记录；只有落在
    `[0.5645, 0.95)` 才释放其余 9 次 Play。这把退化载体的暴露从 10 次
    Play 压到 1 次。
    (d) 对该数值**不得**做任何参数/阈值/窗口/载体调整，合法动作只有
    「释放」或「具名终态」二选一。
16. **BC-BODY1-16（锚点位于行车走廊内：披露、非门禁、强制限制）**：
    (a) **对批次 1 非门禁**。BC-M34-4 (c) 的门是对场景障碍实例的支撑/净空
    审计，锚桅不是场景障碍实例；且接受侧已独立核实它不可能污染测量
    （`EvaluationOcclusionGeometry` 只认 `MeshRenderer`，`TetherLineVisual`
    是无碰撞体的 `LineRenderer`）。
    (b) 它是**冻结载体的既有属性**（自 M0 未变，且已由
    `UT-P1-SCENE-002-001` Unity 验证），非本批次引入。批次 1 **不移动
    锚点**：任何迁移属 `P1-SCENE-007` 的场景设计范围，需用户授权，并会
    使 1a-α 的全部基准（锚点审计、可见弧哈希、走廊工件、σ_px 配对）失效
    而必须整批重做。
    (c) **强制披露**：批次 1c 证据与任何描述实验装置的论文素材，必须把
    「地面锚点位于目标行车走廊内（距中心线 `0.5 m` < 半宽 `1.5 m`），
    且未做物理仿真」列为具名限制，不得静默省略。
    (d) 本条同时登记为 `P1-SCENE-007` 范围的既存理由，但**不重开**该条目、
    不批准其五项未认领授权中的任何一项。

#### F. Disposition

- **停点成立**，`P1-M3-BODY-001` 保持
  `IMPLEMENTED_BATCH_1A_ALPHA_STOP_POINT`，交接翻转给**复核角色**，
  候选 `81202ab`（`git worktree add --detach 81202ab`）。
- 复核范围 = 证据 §10 六条，**外加本轮三项**：BC-BODY1-12 的 R5 文本缺陷
  是否已在 1a-β 前被正确登记；BC-M34-4 (b) 是否确以 `C_geom` 增量
  `0.565728 → 0.584507` 为字面判据；BC-BODY1-16 的「锚桅/缆绳不进遮挡
  几何」是否在代码层面确实成立。
- **1a-β 在 1a-α 复核 verdict 之前不得开工**（§4.3.1）。BC-BODY1-12 的
  修复属 1a-β 批次内容。
- **批次 1c 四门**维持 BC-BODY1-3 原文，并追加 BC-BODY1-13 的 trial 数
  冻结、BC-BODY1-14 的终态口径、BC-BODY1-15 的首跑退化门。
- 本轮**未关闭 M1**、未改动任何遗留条目终态、未新增用户授权。

---

### Acceptance round 4 — 2026-08-07（复核 verdict 归因 + N1/N2 裁定）

Decision: **REVIEW_GATE_CLOSED_1A_ALPHA / RELEASE_1A_BETA**

复核 round 1 对候选 `81202ab` 给出 **`PASS_WITH_NOTES`**
（`docs/reviews/P1-M3-BODY-001.md`），无阻断缺陷。按 workflow §3，
`PASS_WITH_NOTES` 允许继续，注记须进入待办——本节逐条落位。
本轮零消耗、未请求用户授权。

#### A. verdict 归因

- **1a-α 复核门关闭**。复核角色在一次性 worktree 内**不采信报告数字**，
  自跑全部工具与测试：Unity **258/258**，完整 py **394/1**（唯一失败为
  既有 `test_check_docs`，复核**附议**归因成立），`tests.test_m3_body_tools`
  **55/55**，两个 Editor 生成器与三个工具重跑后工件**字节零差异**，场景
  字节前后 SHA-256 与证据 §1 逐位一致。条件 5 审计亦独立复现 exit 0。
- **BC-BODY1-3 的 1c 第一门齐备**：「1a-α 复核 PASS 且接受角色完成
  BC-M34-4 归因」两半均已完成（归因见 round 3 §C）。
- 复核明确**不追溯背书**中间区间 `d2db9f3..4cf811a` 里 SCENE-006 stage-T
  的 Assets 变更（该车道已终态关闭），只单独核实了本批次对它的**依赖**
  （工具 2 的 `TARGET_CUBES` 与 `TargetVisualFactory.AddTargetVisual` 逐
  字段一致）。接受侧采纳该边界划法：本轮不因此改变 `P1-SCENE-006` 的
  终态，亦不把它变成本批次的背书对象。
- **`UNITY_NA` 未申领**，复核附议该分类正确；Unity 列保持 `NOT_RUN`，
  验证义务由 1c 四门承接。

#### B. BC-BODY1-16 (c) 机制表述更正（采纳复核 §4.3）

Round 3 我给出的理由——「`EvaluationOcclusionGeometry` 只从 `MeshRenderer`
建遮挡代理」——**对缆绳完整成立，对锚点标记不成立**。接受侧本轮自行核实
复核的更正属实：

- `TetheredScenarioBootstrap.CreateAnchor`（`:176-181`）用
  `PrimitiveType.Cylinder` 造 `TetherAnchor`，**自带 `MeshRenderer` +
  `MeshFilter`**，故「非 MeshRenderer」这条理由不足以排除它；
- 真正的保护是两重：(i) 创建即 `Destroy(marker.GetComponent<Collider>())`
  （`:181`），`Physics.RaycastAll` 不可命中；(ii) 它是
  `OcclusionGeometry.Build(anchorVisual, Drone.transform, Target.transform)`
  （`:155`）的**显式排除根**，不建代理。

**结论不变**（锚桅与缆绳既不遮挡也不碰撞，且双重成立），但
**BC-BODY1-16 (c) 的披露文本引用机制时以本条为准**，不得再引用 round 3
那句不完整的理由。

#### C. N1 裁定（运行时相机 aspect）——见 BC-BODY1-17

接受侧独立复核了该发现，**成立且比注记标题更重**：

- `Camera.aspect` 在运行时路径**从未被设置**；全库唯一设置点是
  `Assets/TetheredTracking/Editor/Scene006/Scene006SceneRig.cs:128`
  （Editor 侧 probe 台架）——即本项目**已经知道**该钉住，只是运行时没做。
- `SensorFrameWriter.Capture` 在 `:166-167` 挂上 640×480 `RenderTexture`
  渲染（**JPEG 因此是正确的 4:3**），随后在 `:173` 把
  `camera.targetTexture = null`，**之后**才 `PublishFrameBundle`；
  `CoverageEvaluator.OnFramePublished`（`:261`）的
  `WorldToViewportPoint`（`:740`、`:790`）因此按**当时 Game view/屏幕**的
  aspect 投影。
- 后果：**真值评估器与传感器图像可能不是同一个视锥**。垂直 FOV 60° 固定，
  水平 FOV 随 aspect 变：4:3 为 `75.6°`，16:9 为 `91.5°`。方向是**抬高**
  `C_geom`（目标已出画却仍被记「可见」），并使 `C_quality` 的
  `areaPixels`/`centerError` 与真实图像口径不符。这正是 COORD-005 立通道
  要防的 F23 类范畴错误：正式指标测的不是跑出来的那台相机。
- **属 M0 冻结代码的既有缺陷**，非本批次引入。

**1a-α 门数不受影响，不重跑**：接受侧确认复核给出的稳健性论证成立——
束紧方向在俯仰（由 aspect **无关**的垂直 FOV 决定），426 个路线样本视锥项
全部 15/15，最坏视口 x∈`[0.4326, 0.5645]` 远离左右边缘，遮挡项与 aspect
无关。故 BC-M34-4 (a) 的缺口、(b) 的增量、可见弧与测量窗全部稳健。

**否决 Game view 变通作为正式方案**：靠用户 Play 时把 Game view 调成
640×480，是人工依赖、事后不可核验、且把缺陷留在代码里；它只可作为
COORD-005 诊断通道的便利，**不得**写进采集协议。

#### D. N2 裁定（另一处 `782` 旧字样）

**并入 BC-BODY1-12 的勘误授权。** 同一勘误、同一类（描述基准的模块
docstring），只修一处、留一处更糟。复核不擅自扩大解释而交回裁定，
处置正确。

#### E. N3–N6 落位

- **N3** → 1a-β 复核范围**必检项**：阈值策略实现对 `gimbal_saturated`
  **零引用**（BC-BODY1-6 已禁，N3 要求把它做成机械核查；契约 docstring
  写明禁令但机械上不阻止读取）。
- **N4** → 1c 义务：分析工具落地 BC-BODY1-2/-5 时按**里程**配对，并对
  可见性条件化做**对称**处理，两臂样本集不得不对称。
- **N5** → 措辞约束：遮挡归因中单个点样本可同时计入多个阻挡体
  （`blockers` 按 (点, 棱柱) 对计数），故「3069 中的 2808」须读作
  「2808 个被挡点样本的阻挡体清单含 `Building_Stadium`」；逐实例计数之和
  `3493 > 3069` 属预期，不是错误。证据与论文素材按此表述。
- **N6** → 备忘：`test_module_exports_no_writer` 用固定名集等值判断，
  日后在 `controller/body_planner.py` 增公共 API 时须同步强化该测试。

#### F. 新增 binding clarification

17. **BC-BODY1-17（评估 aspect 一致性，1c 前硬性）**：
    (a) 事实按 §C 认定：评估器与传感器图像的视锥可能不一致，属 M0 冻结
    既有缺陷，非本批次引入；1a-α 门数稳健，**不重跑**。
    (b) **正式补救是代码钉住**：把评估侧 aspect 钉到采集 aspect
    （`width/height`），使真值评估器与传感器图像共用同一个视锥。这**改变
    主指标的实测取值**，属 workflow §4.3.1 列举的测量语义变更，因此
    **自成一个 §4.3.1 停点 + 独立复核**，**不得**并入 1a-β。
    (c) **执行次序**：1a-β → 该修复批次（自身停点+复核）→ 1b → 1c。
    修复必须先于 1b，好让 COORD-005 人眼保真检查与审计重跑落在已修代码
    上；**四门齐备前任何一臂都不得采集**。
    (d) **无论是否修复，记录都是强制的**：每次 run 必须记录生效的评估
    aspect，使两臂配对可**核验**而非假定；修复落地后该记录值必须等于
    `640/480`。
    (e) **披露**：既有实测 `C_geom` 族数字（含 `P1-DETECT-001` qual-3 与
    `UT-P1-SCENE-002-001`）是在**未记录、未受控**的 aspect 下采集的，登记
    为已知限制。本条**不重开**那些已关闭/已合格条目、**不授权**任何重跑，
    但跨 run 比较不得把它们的 aspect 当作已确立事实。
    (f) BC-BODY1-12 的授权范围**扩展**至
    `tools/build_m3_corridor.py:8` 的同族 `782` 字样（N2）；其
    `:54-69` 注释与工件字段本已正确，**不得**改动。其余限制不变：仅准
    改实例计数描述，任何其他改动重开接受角色。

#### G. 缺陷立项：`P1-EVAL-001`

BC-BODY1-17 (b) 的修复不是 M3′ 特有问题——它影响本项目**每一次**实测
run，塞进 M3′ 批次 1 会污染归因。按 workflow §4.2「紧急缺陷修复可直接
立项，但必须在状态板中记录问题、范围和验收条件」，本轮直接立项
**`P1-EVAL-001`（评估器/传感器视锥 aspect 一致性）**：

- **问题**：`CoverageEvaluator` 在 `targetTexture` 已置 null 之后投影，
  按 Game view aspect 而非 640×480 采集 aspect 评估。
- **范围**：钉住评估 aspect + 每 run 记录生效 aspect；**不改**设计 §6 的
  任何指标定义（定义里的「视锥」本来就指传感器视锥，本修复是让实现符合
  既有定义）；不改帧/控制协议语义之外的任何东西。
- **验收条件**：(1) 评估投影 aspect 恒等于 `sensor.width/height`，有测试
  锁定；(2) 生效 aspect 进 run 记录，值为 `640/480`；(3) Unity Edit Mode
  全绿；(4) 自身 §4.3.1 停点 + 独立复核 PASS。
- **不占执行位**：`P1-EVAL-001` 本轮只登记 gate board 行，**不进 Active
  handoffs**（COORD-003 单线；M1 登记同法）。它在 1a-β 交回后、1b 之前
  转为活跃。

#### H. Disposition

- `P1-M3-BODY-001` → **`IMPLEMENTED_1A_ALPHA_REVIEW_PASSED`**；1a-α 的
  实现证据与独立复核两门均已满足，Unity 门按设计由 1c 承接。
- 交接翻转给**实现角色执行批次 1a-β**：`world_estimate.py`、
  `body_planner.py`（阈值 + 走廊 + hold）、`track_loop` 按 §2 分支表逐字
  接入、run log 字段、`config/p1-m3-body-001.json` 数值按 §3.5 预注册，
  外加 BC-BODY1-12（含 N2 扩展）的两处 `782` 勘误修复。自身 §4.3.1 停点。
- 1a-β 复核范围预告：BC-BODY1-3 原有三条（零真值/零可见性引用两条机械
  检查、§2 分支表逐字符合、走廊工件唯一用途）+ **N3**（策略零引用
  `gimbal_saturated`）+ BC-BODY1-12/N2 两处勘误修复且**未越界**。
- 1c 四门更新为：1a-α 复核 PASS ✅ + BC-M34-4 归因 ✅（本轮齐备）；
  1a-β 复核 PASS；**`P1-EVAL-001` 复核 PASS**（BC-BODY1-17 (c) 新增）；
  1b 完成；用户 Play。首次 Play 仍是 BC-BODY1-15 的臂A trial 1 退化门。
- BC-M34-1…10、BC-BODY1-1…16 语义不变（BC-BODY1-16 (c) 仅更正机制引用，
  结论不变）；SCENE-005/007 verdict 与暂停状态不变；M1 未关闭；
  无用户授权产生。

---

### Acceptance round 5 — 2026-08-07（批次 1a-β 停点核对）

Decision: **STOP_POINT_NOT_CONFIRMED / RETURN_1A_BETA_REWORK**

停点对象：实现候选 `5340cf6`（状态/证据补记提交 `f8c3ea2`）。本轮不签发
独立复核 verdict，也不把候选交给复核角色；零 Play、零
scenario/session/run ID、零配额、零 API，未产生或请求用户授权。

#### A. workflow §4.3.1 五条件核对

| 条件 | 结论 | 接受侧核对 |
|---|---|---|
| 1 实现范围与接口冻结 | ❌ | 代码/文件范围已收敛，但 estimator config 的四个先验仍以「交回 Acceptance」状态进入候选，且 `q_accel_mps2` 的承重来源文字与真实目标运动代码不符；见 §C。另有 body-command 发布失败语义与 §2 异常分支不一致；见 §D |
| 2 相称的实现者测试通过 | ✅ | 接受侧复跑 policy **27/27**、tools **56/56**；完整 Python **422/1**，唯一失败仍是已归因的 `test_check_docs` 基础设施 fixture；Unity XML 实文件为 **258/258 Passed**；工具 2 与 corridor check 均通过 |
| 3 已知 Unity 失败已修复 | ✅ | 无 Unity 失败；本批次零 Play，且 `Assets/`、scenario、C#/协议字节在 `a67db45..5340cf6` 上零改动 |
| 4 复核范围/状态/候选/风险准确 | ❌ | 候选与范围已记录，但证据把 `v·turnRate` 写成「冻结路线最大向心加速度」，并把发布失败记为可继续的 `publish_error`，未如实满足接受文本；风险与复核范围因此不准确 |
| 5 实现写入审计 + 归因 | ✅ | 见 §B；两个越权路径均为已记录的非实现批次，1a-β 自身 12 路径白名单通过 |

条件 1、4 不成立，故停点不成立；测试通过不能覆盖设计/证据未冻结。

#### B. 条件 5 写入审计与逐路径归因

按 workflow 指定基线运行：

```text
python3 tools/check_role_writes.py --role implementation --base 81202ab
=> exit 1：2 个越权路径
```

两条均可完整归因到状态板已有的非实现批次，且候选未触碰：

| 路径 | 唯一相关提交 | 归因 |
|---|---|---|
| `docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md` | `a67db45` | Acceptance rounds 3–4 |
| `docs/reviews/P1-M3-BODY-001.md` | `6ef4e77` | independent Review round 1 |

再以 1a-β 实现真正开工点复验：

```text
# audit-time HEAD = f8c3ea2
python3 tools/check_role_writes.py --role implementation --base a67db45
=> exit 0：a67db45..f8c3ea2 共 12 个路径全部合规
```

因此条件 5 成立；本轮返工不是写入越权归因失败。

#### C. estimator 交回事项裁定

实现证据 §12 的交回处理是正确的：1a-α 已复核契约 §6 明写 estimator 节
故意为空、实现角色不发明数值。当前四值在接受裁定前不能自行成为冻结研究
参数。接受侧逐行核对 `LoopTargetVehicle.Step` 后确认：目标平移使用
`transform.position += direction * speed * deltaTime`，到折点直接切换
`direction`；`turnRate = 240°/s` 只进入另一路
`Quaternion.RotateTowards`，只旋转车身朝向。因此
`2.0 m/s × 240°/s = 8.377580 m/s²` **不是**冻结路线的最大向心加速度，
也不是平移过程的物理上界。该数可保留为事前启发式尺度，但原来源主张必须
撤回。

新增 binding clarifications：

18. **BC-BODY1-18（batch-1 estimator 先验冻结与主张上限）**：
    (a) Acceptance 现将候选的四个数值仅冻结为**批次 1 的事前、未标定
    启发式先验**：`q_accel_mps2=8.377580`、`sigma_att_deg=1.0`、
    `sigma_y_m=0.05`、`initial_velocity_sigma_mps=2.0`。这不是实测标定，
    也不是物理上界；实现不得把「Acceptance 接受该先验」改写成「来源已被
    验证」。
    (b) `q_accel_mps2` 的 derivation 必须改成：`v·turnRate` 仅是**冻结在
    数据前的启发式 process-noise scale**；`turnRate` 不约束平移方向，
    不得再出现「maximum centripetal acceleration」或等价表述。
    (c) `sigma_att_deg=1.0` 明写为无姿态噪声标定源的保守占位；
    `sigma_y_m=0.05` 只是复用既有空间容差的保守尺度，**不是**锚点支撑
    容差推导出的地平面噪声；`initial_velocity_sigma_mps=2.0` 是以冻结
    目标速度为尺度的保守初始先验，不是测得的标准差。config、证据 §4/§9/
    §10/§12 与契约 §6 必须逐处一致，不留「推导成立」的旧句。
    (d) 批次 1 的任何决策仍不得消费 estimator 均值或协方差；1c 的
    NEES/NIS 只称**未标定先验下的一致性诊断**，不得称 estimator 已校准或
    已验证。四值在任何 1c 数据前冻结，看到数据后不得改；显著不一致只准
    如实报告并回 Acceptance，不准调参重报。

#### D. planner 契约精度与发布失败返工

19. **BC-BODY1-19（“纯函数”与唯一发布点的精确定义）**：
    (a) §5.3/契约 v1 的「纯函数」在批次 1 中定义为：无文件/网络 I/O、
    无墙钟读取、无真值/可见性先验、无外部副作用；它**不**禁止 §3.5
    已冻结的迟滞记忆。`ThresholdBodyPlanner` 只准保留一个 `_moving`
    布尔状态，构造时为 `False`，每个新进程/trial 重新构造；按顺序从首帧
    重放必须确定性复现。契约中「arguments alone」的陈述作废，按「有序
    输入历史 + 固定初态」表述。
    (b) 「planner 之外不得发 body 指令」指**不得存在替代决策所有者或旁路**；
    planner 本身仍无 I/O，实际写入只准由 `RuntimePublisher`/`body_entry.py`
    在既有 initialize hold 与 `_body_step` 对 planner 返回值的唯一映射点
    执行。任何其他发布调用均为违约。
20. **BC-BODY1-20（body-command 写入失败必须 fail closed）**：当前候选在
    `publisher.body_command(command)` 抛错后只写 `publish_error` 并继续，
    没有发布 `hold`，且吞掉异常；这不满足 §2「任何异常路径 hold；异常不得
    吞掉」。返工必须：
    (a) 首次写入失败立即尝试一次显式 `hold`；fallback 成功时 run log 同时
    保留原请求、首错与最终实际 `hold`，不得仍把原 velocity 记成已发布；
    (b) fallback 也失败时保留两次错误并使本次运行**终止/失败关闭**，不得
    返回为普通成功帧或继续产生后续 planner 决策；
    (c) 新增两个聚焦测试：首写失败但 fallback hold 成功、两次写入均失败；
    测试须同时锁定命令槽最终状态、run-log/失败记录和进程是否继续；
    (d) 证据 §6–§10 按真实行为改写。不得以 receiver 的 0.4 s 过期回落
    代替本条——两道保险须互不依赖。

#### E. Disposition

- 候选 `5340cf6` 保留作返工基线，但**不是稳定候选**，不得交 independent
  Review；`P1-M3-BODY-001` → `REWORK_REQUIRED_1A_BETA_STOP`。
- 交回 Implementation 做同一 1a-β 的窄返工：落实 BC-BODY1-18…20，更新
  config/契约/实现证据与测试；不得带入 `P1-EVAL-001`、Play、场景/协议/
  Assets 变更或任何 1b/1c 工作。
- 返工后回到**同一 §4.3.1 停点**。条件 5 仍以 `81202ab` 为上一通过候选；
  接受侧须重新运行完整审计并归因本轮 Acceptance 文档路径。
- 1a-α 已关闭门、BC-M34-4/9 归因、BC-BODY1-1…17、SCENE-005/007 verdict、
  `P1-EVAL-001` 顺序与 1c 全部门禁均不变；本轮不关闭 M1。

---

### Acceptance round 6 — 2026-08-07（批次 1a-β 返工停点复核）

Decision: **ACCEPTED — STOP_POINT_CONFIRMED / RELEASE_1A_BETA_TO_REVIEW**

停点对象为实现候选 `a234270`；`d9a0b11` 只补记状态、归档与实现证据中的
候选 SHA，不改变候选代码、config 或测试。Round 5 的 BC-BODY1-18…20
已逐条落实，1a-β 现可作为稳定候选交 independent Review。本结论不是独立
复核 verdict，也不关闭 1a-β、M1 或 M3；零 Play、零
scenario/session/run ID、零配额、零 API，未产生或请求用户授权。

#### A. workflow §4.3.1 五条件核对

| 条件 | 结论 | 接受侧核对 |
|---|---|---|
| 1 实现范围与接口冻结 | ✅ | `db51792..a234270` 只改 config、planner/loop、契约/证据与两组测试共 7 路径；BC-BODY1-18 四值只作事前未标定启发式先验，BC-BODY1-19 的纯函数/唯一映射点精确定义落地，BC-BODY1-20 的首错 fallback 与双错终止落地；无 `P1-EVAL-001`、Assets、scenario 或协议改动 |
| 2 相称的实现者测试通过 | ✅ | 接受侧复跑 policy **29/29**、tools **56/56**；完整 Python **424/1**，唯一失败仍是未改动的 `test_check_docs` 基础设施 fixture；工具 2 与 corridor check 通过；Unity XML 实文件为 **258/258 Passed** |
| 3 已知 Unity 失败已修复 | ✅ | 无已知 Unity 失败；返工零 C#/Assets 字节，2026-08-07 的 Edit Mode XML 为 258/258；本批次仍零 Play |
| 4 复核范围/状态/候选/风险准确 | ✅ | 证据 §4–§12 已按 BC-BODY1-18…20 改写；§9 保留未实跑 estimator、合成故障注入、最新帧 cadence、锚点位置等限制；§10 明列 10 项复核范围；候选与状态提交分开记录 |
| 5 实现写入审计 + 归因 | ✅ | 见 §B；上一通过候选基线只报出可完整归因的 Acceptance/Review 文件，本轮返工区间 9 路径全部在 implementation 白名单内 |

五项均成立，故停点确认。自动测试与 Unity XML 只支撑稳定候选判断；是否
符合实现与行为契约仍由新鲜上下文的独立复核角色裁定。

#### B. 条件 5 写入审计与逐路径归因

按 workflow 指定的上一通过候选基线运行：

```text
python3 tools/check_role_writes.py --role implementation --base 81202ab
=> exit 1：2 个越权路径
```

两条均为基线后已登记的非实现角色提交，不是候选越权：

| 路径 | 相关提交 | 归因 |
|---|---|---|
| `docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md` | `a67db45`、`db51792` | Acceptance rounds 3–5 |
| `docs/reviews/P1-M3-BODY-001.md` | `6ef4e77` | independent Review round 1 |

再从 round 5 返工起点复验：

```text
# audit-time HEAD = d9a0b11
python3 tools/check_role_writes.py --role implementation --base db51792
=> exit 0：db51792..HEAD 共 9 个路径全部合规
```

`a234270..d9a0b11` 只有 `docs/current-status.md`、月度归档与实现证据的状态
补记；代码/config/tests/tools/Assets 零差异。因此条件 5 成立，稳定候选仍
精确钉在 `a234270`。

#### C. Round 5 返工逐条验收

| Binding clarification | 结论 | 可核对落点 |
|---|---|---|
| BC-BODY1-18 | **FULFILLED** | config `priors_status` 与四个 derivation、证据 §4/§9/§10/§12、契约 §6 均只称事前未标定启发式先验；`v·turnRate` 明说不约束平移、不是物理上界；测试禁止 `centripetal`；批次 1 决策仍不消费 estimate，1c 只准称未标定先验下的一致性诊断 |
| BC-BODY1-19 | **FULFILLED** | module/class docstring 与契约 §1/§1.1 明定无 I/O/墙钟/真值/可见性先验/外部副作用；迟滞仅 `_moving`、初态 `False`、每进程/trial 新实例、有序重放确定；生产代码的 body 写入仍只经 initialize hold 与 `_body_step` 唯一映射点 |
| BC-BODY1-20 | **FULFILLED** | `_body_step` 首次写入失败后只尝试一次 fallback hold；成功时原请求、首错、实际 hold 分列并继续；再次失败时两错入本帧记录，随后 `BODY_COMMAND_FAIL_CLOSED` 终态、无后续决策，`run_tracker` 既有 terminal 路径退出 2；两个聚焦测试锁定命令槽、记录与继续/终止走向 |

#### D. Release-to-review binding scope

独立复核角色必须在一次性 worktree 对**精确候选 `a234270`**执行新鲜审查；
实现增量按 `81202ab..a234270` 查看，另用 `db51792..a234270` 定位 round 5
窄返工。逐条检查实现证据 §10 的 10 项，尤其：

1. 机械重算零真值、零可见性先验、策略零 `gimbal_saturated`、策略零
   estimator 消费与走廊工件唯一用途，不能只采信实现者测试；
2. 逐字符合 §2 分支表，确认 BC-BODY1-19 的状态/重放与两个合法发布位置，
   全库无替代决策所有者或第三发布点；
3. 故障注入逐行确认 BC-BODY1-20：fallback **恰好一次**、实际发布字段不把
   原 velocity 误记成功、双错先落本帧再终态、终态后无新决策；
4. 独立复算 estimator Jacobian/Joseph 更新、先验措辞、走廊哈希/779 计数、
   BC-BODY1-12/N2 勘误边界及 run-log 向后兼容；
5. 复跑 policy/tools/full Python、工具 2、corridor check，并核验 Unity XML；
   已知 `test_check_docs` 只能在确认两文件未改且失败同源后归为 pre-existing。

复核若发现缺陷，唯一合法动作是写 `docs/reviews/P1-M3-BODY-001.md` 并把
修复退回 Implementation；不得改代码。复核 verdict 出来前不得启动
`P1-EVAL-001`、1b、1c 或 Play。若 PASS，再交 Acceptance 消费 verdict，
然后按既定顺序激活 `P1-EVAL-001`；BC-M34-1…10、BC-BODY1-1…20、
SCENE-005/007 verdict 与所有 1c 门禁均不变。

---

### Acceptance round 7 — 2026-08-07（消费 1a-β Review round 2）

Decision: **ACCEPTED — REVIEW_VERDICT_CONSUMED / 1A_BETA_REVIEW_GATE_CLOSED**

Acceptance 消费 `docs/reviews/P1-M3-BODY-001.md` round 2 对精确候选
`a234270` 的 **`PASS_WITH_NOTES`**。复核提交 `4788aff` 只改复核文件、
状态板与月度归档；`check_role_writes --role review --base 718fa45`
对 3 路径通过，零实现文件差异。复核在一次性 worktree 完整检查
`81202ab..a234270`，以 `db51792..a234270` 隔离返工，确认无阻断缺陷。

#### A. Verdict 消费

- BC-BODY1-18…20 全部独立核实 **FULFILLED**；估计器 Jacobian/Joseph、
  §2 分支表、唯一 dispatch、恰好一次 fallback hold、双错终态 exit 2、
  走廊哈希/779 计数与勘误边界均确认。
- 独立复跑 policy 29/29、tools 56/56、完整 Python 424/1；唯一失败仍是
  未改动的 `test_check_docs` 基础设施 fixture。工具 2、corridor 工件与
  config pins 字节一致；Unity XML 258/258，返工零 C#/Assets 字节，时间线
  归因成立。
- 1a-β 的**实现门与独立复核门现均关闭**。这不等于 `DONE`：运行时验证
  仍由既定顺序 `P1-EVAL-001` → 1b COORD-005 → 1c 用户 Play 承接；本轮
  不申领 `UNITY_NA`、不关闭 M1/M3、零 Play/ID/配额/API、无新用户授权。

#### B. N7–N10 安置（均不阻断 `P1-EVAL-001`）

| Note | Acceptance disposition | 到期点 |
|---|---|---|
| N7 | **`NOTE_OPEN_DOC_ACCURACY`**：复核已按内容核实实质主张成立。P1-M3 后续证据维护须把 `gimbal_saturated` 引用改为内容定位或候选行 `:85/:101`，`metrics.json` 改为 `:1492/:1522`，并把 `world_estimate.geo_reject_reason` 补入 §6 追加键清单；不得借机改实现或研究主张 | 1c 协议/证据冻结前；不混入 `P1-EVAL-001` 实现批次 |
| N8 | **`RECORDED_NONDEFAULT_SCHEMA_GUARD`**：当前 v3 生产接线已由 `FrameRepository.load` 使 t=0 防御性死路径不可达，不返工。未来任何非默认帧 schema 接入 body path 前必须重审/消除该路径 | 非默认 schema 接线前 |
| N9 | **`RECORDED_1C_DIAGNOSTIC_ONLY`**：1c 若出现帧延迟异常，把最坏 32×779 的走廊线性扫描列为排查点；它不是当前门、不是预设性能失败，也不得据此先行调参/优化 | 仅在 1c 延迟异常时 |
| N10 | **`DEFERRED_TEST_STRENGTHENING`**：批次 2 扩展决策路径前，把 `_body_step`、`_platform_state`、`_build_body_runtime` 纳入同一禁令 token 扫描，或将替代覆盖方案退回 Acceptance 明确裁定 | 批次 2 决策路径扩展前 |

#### C. 激活 `P1-EVAL-001` 的逐条实现契约

`P1-EVAL-001` 是 round 4 §G 已立项的既有缺陷修复，现按 BC-BODY1-17 (c)
取得唯一执行位；不改变设计 §6 指标定义，只让 evaluator 的实测视锥符合
传感器视锥。Implementation 必须按字面满足：

1. **投影来源唯一**：所有 evaluator `WorldToViewportPoint`/真值框投影在
   首个评估帧前绑定到 `config.sensor.width / (float) config.sensor.height`，
   且不随 Game view、`Screen` 或 `targetTexture` 解除后的状态变化；默认
   场景的有效值必须是 `640/480`。
2. **逐 run 可核验记录**：每次写出的 `metrics.json` 在既有
   `tethered-evaluation/v1` 文档中追加顶层 `evaluation_projection` 对象，
   且恰含 `sensor_width_px`、`sensor_height_px`、
   `aspect_width_over_height`；默认运行分别为 `640`、`480`、`640f/480f`。
   既有字段、公式、阈值、schema_version 不删、不改名、不改义。
3. **测试必须证伪旧缺陷**：Edit Mode 测试显式令 Camera/Game-view aspect
   与非方形 sensor 比例不同，证明评估投影仍按 sensor 比例；另锁定
   `MetricsJsonForTests()` 的三项记录与非正 width/height 的 fail-closed/
   既有 config 校验行为。只断言 `camera.aspect` 数值而不检查投影不够。
4. **窄范围**：预计只改 `CoverageEvaluator.cs`、相关 Edit Mode 测试与
   `P1-EVAL-001` 证据/状态。不得改 `SensorFrameWriter`、帧/控制协议、scenario、
   指标公式/阈值，不得重跑或重开既有 `C_geom` 结果；若必须触碰这些范围，
   先退回 Acceptance，不得自行扩大。
5. **自身停点**：实现者记录精确候选、测试与未验证风险后停下；Acceptance
   重新执行 workflow §4.3.1 五条件（含 implementation 写入审计）并交独立
   Review。Review PASS 前不得开始 1b、1c 或 Play。

状态翻转：`P1-M3-BODY-001` →
**`IMPLEMENTED_1A_BETA_REVIEW_PASSED_AWAITING_EVAL_1B_1C`**；唯一活跃项改为
`P1-EVAL-001` → **`IMPLEMENTATION_READY`**。BC-M34-1…10、
BC-BODY1-1…20、SCENE-005/007 verdict、M1 与全部 1c 门禁不变。

---

### Acceptance round 8 — 2026-08-07（`P1-EVAL-001` 停点审计）

Decision: **ACCEPTED — STOP_POINT_CONFIRMED / REVIEW_RELEASE_PENDING_PUSH**

Acceptance 对精确实现候选 `61ea20b` 完成 workflow §4.3.1 五条件审计。
候选按 round 7 §C 实现传感器 aspect 钉住和逐 run 投影 provenance；未改变
设计 §6 的指标、公式、阈值或研究主张。本轮只确认稳定候选停点，**不是**
独立复核 verdict、`DONE`、`UNITY_NA` 或运行时验证。

#### A. 五条件结论

| §4.3.1 条件 | 结论 | 证据与归因 |
|---|---|---|
| 1. 范围和接口冻结 | **PASS** | 精确实现差异 `0762ba6..61ea20b` 仅 4 个 C#/Edit Mode 路径和 `docs/evidence/P1-EVAL-001-implementation.md`；`SensorFrameWriter`、协议、scenario/config、§6 公式/阈值与历史结果均未改。候选后的 `1b87c1d` 只有状态板/归档。 |
| 2. 相称测试/编译 | **PASS** | 实现证据 Unity 263/263；Acceptance 用 Unity 6000.4.1f1 独立复跑同一 263/263（`runtime/test-results/p1-eval-001-acceptance-editmode.xml`，exit 0）。完整 Python 424 项仅既有 `test_check_docs` 一项失败；`tests/test_check_docs.py` 与 `tools/check_docs.py` 在 `a234270..61ea20b` 零差异。 |
| 3. 已知 Unity 失败 | **PASS** | 批次内 z 符号错误和等价测试失败均已修复并复测；当前无已知 Unity 失败。零 Play 符合范围，端到端人眼检查仍由后续 1b/1c 门承接。 |
| 4. 候选、状态、风险、复核范围 | **PASS** | `61ea20b`、证据 §5–§8、状态板与未验证前提一致。`docs/reviews/P1-EVAL-001.md` 尚不存在是角色边界下的预期状态，由 Review 在独立复核时创建；本轮不预写独立结论。 |
| 5. 实现角色写入审计 | **PASS_WITH_ATTRIBUTION** | 审计时 HEAD `1b87c1d`：`--role implementation --base a234270` 仅标出提案和复核路径；提案由 Acceptance 提交 `718fa45`/`0762ba6`，复核由独立 Review 提交 `4788aff`，均可归因。隔离实现区间 `--base 0762ba6` 对 `0762ba6..1b87c1d` 全部 7 路径通过。 |

#### B. 复核角色必须逐条核对的范围

1. 在一次性 worktree 检查精确代码候选 `61ea20b`；上一通过代码候选为
   `a234270`，本项纯实现区间为 `0762ba6..61ea20b`。不得把候选后的状态
   文档提交误当成实现字节。
2. 独立复算 `WorldToSensorViewportPoint` 的坐标约定、`z` 符号、x/y 公式、
   `z<=0` 丢弃语义和运行时相机前提；确认 evaluator 内无残留未钉住的
   `WorldToViewportPoint`，且实现不读 Game view/`Screen`/当前 aspect、
   不写相机状态。
3. 核对每个 `metrics.json` 的顶层 `evaluation_projection` **恰含**
   `sensor_width_px`、`sensor_height_px`、`aspect_width_over_height`，同时
   schema/version、既有字段、公式和阈值保持不变，并检查下游未知键兼容性。
4. 独立复算 16:9 内/4:3 外的边缘点以及 bounds 级 oracle，确认新测试确实
   证伪旧缺陷，而非只断言属性或重复生产实现。
5. 特别审查本批次唯一既有断言弱化：
   `Scene006EditModeTests.ProjectionMatchesInternalProjectRenderers` 容差
   `1e-6 -> 5e-5`。须独立判断证据 §4 的 float 路径解释和实测最大偏差
   `<=1.4e-5` 是否足以证明该容差不会遮蔽结构性投影错误。
6. 核对窄范围边界与零历史结果重跑；任何阻断缺陷只能写入
   `docs/reviews/P1-EVAL-001.md` 并退回 Implementation，本轮 Acceptance
   不授权 Review 修改实现。

#### C. 待办安置与发布纪律

- `Scene006Visibility.cs` 中指向 `CoverageEvaluator.cs` 的陈旧行号归为
  **`NOTE_OPEN_DOC_ACCURACY`**：语义复制关系和等价测试当前成立，不阻断
  本项 Review；与既有 N7 一并在 1c 协议/证据冻结前修正，不混入候选
  `61ea20b`，不得借机改变实现或研究主张。
- 状态板明确记载候选“按用户决定暂不推送”。Acceptance 不覆盖该决定：
  五条件已通过，但按 workflow 的提交/推送后交接纪律，**未推送前不启动
  Review**。故唯一执行位暂留 Acceptance，状态为
  **`STOP_POINT_CONFIRMED_REVIEW_RELEASE_PENDING_PUSH`**；本轮文档先本地提交，
  用户允许推送后再推送完整候选链并把执行位交给 Review。
- `P1-M3-BODY-001`、BC-M34-1…10、BC-BODY1-1…20、M1、1b/1c/Play 与全部
  paused work item 的状态不变；没有新用户授权需要写入授权账本。

---

### Acceptance round 9 — 2026-08-07（消费 `P1-EVAL-001` Review round 1）

Decision: **ACCEPTED — REVIEW_VERDICT_CONSUMED / EVAL_REVIEW_GATE_CLOSED / RELEASE_1B**

Acceptance 消费 `docs/reviews/P1-EVAL-001.md` round 1 对精确候选
`61ea20b` 的 **`PASS_WITH_NOTES`**。复核提交 `df618cc` 只改复核文件、
状态板与月度归档；`check_role_writes --role review --base d433eb0`
对 3 路径通过，主树实现文件零修改。

#### A. Verdict 消费

- 独立 Review 在一次性 worktree 检查 `0762ba6..61ea20b`，并把
  `a234270..61ea20b` 的额外文档路径逐项归因；自行复跑完整 Python
  **424/1**（唯一既有 `test_check_docs`）与 Unity Edit Mode
  **263/263**，零阻断缺陷。
- round 7 §C 五条及 round 8 §B 六项逐条成立：投影公式/z 约定/绑定时序、
  evaluator 内零残留原生投影、恰含三键的 provenance、下游兼容、边缘点
  证伪与窄范围均确认。复核明确附议唯一既有断言弱化
  `1e-6 -> 5e-5`，判断其不会遮蔽结构性投影错误。
- `P1-EVAL-001` 的**实现门与独立复核门现均关闭**，但运行时事项不能因此
  标为 `DONE`，也不申领 `UNITY_NA`。端到端人眼/Play 仍按既定顺序由
  1b/1c 承接；历史 `C_geom` 结果不重跑、不重开。

#### B. N-EVAL-1…4 安置

| Note | Acceptance disposition | 到期点 |
|---|---|---|
| N-EVAL-1 | **`MERGED_NOTE_OPEN_DOC_ACCURACY_N7`**：`Scene006Visibility.cs` 的两处 `CoverageEvaluator.cs` 行号已偏移；语义复制关系和等价测试成立，不阻断。与 N7 同批只修引用/证据清单，不得改实现或主张 | 1c 协议/证据冻结前；不混入 1b |
| N-EVAL-2 | **`RECORDED_M5_REACTIVATION_GUARD`**：冻结的 RATE scouting 工具仍按相机当前 aspect 投影，本项窄范围不应触碰。任何 M5 重新激活 RATE-003 并复用该工具前，必须先把 aspect 语义退回 Acceptance 重审 | RATE-003/M5 复用工具前 |
| N-EVAL-3 | **`RECORDED_REVIEW_ENVIRONMENT_PREREQUISITE`**：新鲜 worktree 缺少 gitignore 的权重时，scene006 probe 按设计 `FAIL_WEIGHT_HASH`；复核者应先从主树复制只读 `runtime/yoloe`、`runtime/models` 后再跑全套。不是候选缺陷 | 每次相关新鲜 worktree 复核开工时 |
| N-EVAL-4 | **`RECORDED_OPTICS_CHANGE_REVIEW_TRIGGER`**：当前 SensorCamera 与透视/垂直 FOV/非 physical/零 lens shift 前提吻合；未来引入 physical、正交、lens shift 或自定义投影矩阵前，必须重审钉住函数 | 任何 SensorCamera 光学构造变更前 |

#### C. 批次 1b 逐条执行合同

唯一执行位转回 Implementation，执行**证据批次 1b**；本批次不写新功能，
不改变候选 `61ea20b` 的实现语义：

1. **候选身份**：开工先记录 `git rev-parse HEAD` 与
   `git status --porcelain`；HEAD 必须在已推送主线且实现字节与
   `61ea20b` 相同。若出现任何 C#/Python/controller/config/scenario 语义
   差异，立即退回 Acceptance，不得继续 1b。
2. **道路/走廊审计重跑**：在真实 checked-in city scene 与
   `config/scenario.default.json` 上执行
   `P1M3BodySceneGeometryGenerator.Generate`，随后执行
   `python3 tools/build_m3_corridor.py --check` 与
   `python3 tools/check_scene_body_margin.py`。必须同时满足：road audit
   `CLEAR`、779 个审计障碍、corridor `--check` 通过、工具 2 通过，且
   重生成的版本化几何/走廊/边界证据与已复核 pins 字节一致；任一不符即停，
   不准改场景、参数、阈值或工件来求通过。
3. **COORD-005 人眼保真检查**：用正常生产启动链做一次明确标注的诊断
   Play，保存至少 **2 张不同 frame_id 的 640×480 SensorFrameWriter 样帧**；
   样帧必须来自实际 runtime target，不得使用 probe/替身。用户或当轮发令
   角色逐张确认：目标是正常运行时外观的**红色对象**，不是 SCENE-006 F23
   的无材质灰色替身，且画面语义与本批次跟踪对象一致。
4. **证据可复核**：两张及以上样帧存入
   `docs/evidence/P1-M3-BODY-001-1b/`；在
   `docs/evidence/P1-M3-BODY-001-1b.md` 记录相对路径、SHA-256、frame_id、
   确认人和逐张结论，并记录审计命令/结果、开工 HEAD/clean 状态、实现
   字节等价结论与收工 `git status`。
5. **零正式消耗**：诊断 Play 不创建或消耗 scenario/session/run/qual ID，
   不计入 10 个正式 trial，不产出可用于 H1/H2 的指标，不动配额/API；不得
   根据样帧或审计数字调参数、阈值、测量窗或载体。
6. **回交门**：道路/走廊审计全部通过且人眼确认逐张 `PASS` 后，Implementation
   只标 `IMPLEMENTED_1B_AWAITING_ACCEPTANCE_CONFIRMATION` 并返回 Acceptance；
   Acceptance 消费 1b 之前不得启动 1c。1c 首次 Play 仍必须是 BC-BODY1-15
   的臂 A trial 1，门序、冻结数值与终态规则一字不变。

状态翻转：`P1-EVAL-001` →
**`IMPLEMENTED_REVIEW_PASSED_AWAITING_DOWNSTREAM_1B_1C`**；
`P1-M3-BODY-001` →
**`IMPLEMENTED_1A_BETA_AND_EVAL_REVIEW_PASSED_1B_READY`**。
BC-M34-1…10、BC-BODY1-1…20、M1、SCENE-005/007 与全部 paused work item
状态不变；本轮未产生新的用户关键授权。

---

### Acceptance round 10 — 2026-08-08（确认批次 1b）

Decision: **ACCEPTED — BATCH_1B_CONFIRMED / RELEASE_1C_PREFLIGHT**

Acceptance 审核 `docs/evidence/P1-M3-BODY-001-1b.md` 及其两张样帧，确认
round 9 §C 六条全部满足。此结论关闭 1b 的道路/走廊审计与 COORD-005
人眼保真门；它不是正式 trial verdict，不关闭 M3/M1，也不把诊断帧纳入
H1/H2 证据。实现角色产出的证据文件与四个样帧/元数据文件已独立归因提交
为 `a154982`；本轮 Acceptance 只合并状态并写决策。

#### A. 六条合同核对

| round 9 §C | 结论 | Acceptance 核对 |
|---|---|---|
| 1. 候选身份 | **PASS** | 开工 HEAD `16a4da7` 等于当时 `origin/main` 且干净；`61ea20b..16a4da7` 恰 6 个 docs 路径。Acceptance 再跑 `git diff --quiet 61ea20b..HEAD -- Assets controller config tools tests`，确认实现字节等价。 |
| 2. 道路/走廊审计 | **PASS** | 真实场景 generator 日志为 896 roots / 117 road surfaces / road audit `CLEAR` / 779；Acceptance 再跑 corridor `--check` 得 779 prisms、SHA-256 `9e2956ad…c800`，再跑 margin 工具得 `C_geom [0.565728,1.000000]`、arm B lower `0.584507`、`route0_in_arc=True`、窗口 `[0,62.5]`。重跑后无版本化 pin 差异。 |
| 3. 人眼保真 | **PASS** | JPEG 均为 640×480、frame_id 12/30，元数据均为 `deterministic-loop-default` + `tethered-sensor-frame/v3`。用户已逐张 PASS；Acceptance 直接查看原图亦确认实际红色 runtime target、非灰色替身。 |
| 4. 证据可复核 | **PASS** | 两张 JPEG 与两份 JSON 均在版本化证据目录；路径、frame_id、确认人、结论及四个 SHA-256 与盘上重算逐位一致。命令、HEAD、开/收工状态和恢复动作均有记录。 |
| 5. 零正式消耗 | **PASS** | 诊断 Play 明确不创建 scenario/session/run/qual ID，不计 10 个 trial、不产生 H1/H2 指标、不消耗配额/API，且没有按结果调参数、阈值、窗口或载体。 |
| 6. 回交纪律 | **PASS** | 状态停在 `IMPLEMENTED_1B_AWAITING_ACCEPTANCE_CONFIRMATION`；`check_role_writes --role implementation` 对未提交批次通过，`Assets/controller/config/tools/tests` 全部无改动，1c 尚未启动。 |

运行现场恢复亦成立：`runtime/scenario_config.json` 与
`config/scenario.p1-scene-004.json` SHA-256 均为
`00c8802a…b514`；旧 qual-3 帧移入
`runtime/frames.qual3-leftover-hold/` 而未删除。该 hold 目录与本次诊断帧
都不是正式证据输入；1c 准备时须再次隔离，禁止混入 trial 1。

#### B. 1c 预检合同（正式 Play 仍未释放）

1b 已确认，1c 阶段可进入**预检**。但 N7/N-EVAL-1 的到期点正是“1c
协议/证据冻结前”，故 Implementation 必须先完成以下窄批次并返回
Acceptance；此前用户不得开始 arm A trial 1：

1. **只做已判定的文档准确性清理**：
   - 把 `Scene006Visibility.cs` 两处指向 `CoverageEvaluator.cs` 的失效行号
     改为不会随插行漂移的符号/内容定位，或候选当前准确位置；只改注释；
   - 在 P1-M3 1a-β 证据中把 `gimbal_saturated` 与 `metrics.json` 的失效
     行号改为内容定位（若保留行号则须以当前候选复核）；
   - 把 `world_estimate.geo_reject_reason` 补入该证据 §6 的追加键清单。
   除上述引用/清单外零实现语义、零研究主张改动；发现需扩大即退回。
2. **冻结 arm A trial 1 操作单**：必须逐项引用 BC-BODY1-2/-3/-13/-15，
   钉住主环线 scenario/hash、seed 0、route[0]、planner=A/hold、冻结初始框、
   62.5 m / 31.25 s 测量窗、整圈 `C_geom` 判定与运行目录；明确本次诊断帧
   和 qual-3 hold 目录均不进入输入。
3. **首跑 fail-closed 分支写死**：arm A trial 1 是第一次正式 Play，必须由
   用户执行；完成后先计算并记录整圈 `C_geom`，在任何后续 Play 之前回
   Acceptance。`C_geom < 0.5645` → `GEOMETRY_MODEL_REJECTED`；
   `C_geom >= 0.95` → `SCENE_DEGENERATE`；仅 `[0.5645,0.95)` 可申请释放
   其余 9 次 Play。不得用该数值调参数、阈值、窗口或载体。
4. **提交边界**：预检批次只允许上述注释/证据/操作单/状态；不得启动
   Play、创建正式 ID 或写运行指标。完成后标
   `IMPLEMENTED_1C_PREFLIGHT_AWAITING_ACCEPTANCE`，由 Acceptance 核对干净
   pushed HEAD 与精确操作单后，才把 arm A trial 1 交给用户。

状态翻转：`P1-M3-BODY-001` →
**`BATCH_1B_CONFIRMED_1C_PREFLIGHT_READY`**；`P1-EVAL-001` →
**`IMPLEMENTED_REVIEW_AND_1B_PASSED_AWAITING_1C`**。BC-M34-1…10、
BC-BODY1-1…20、M1、SCENE-005/007 与全部 paused work item 不变；本轮
未产生新的用户关键授权。

---

### Acceptance round 11 — 2026-08-08（1c 预检审核）

Decision: **REVISION_REQUESTED — 1C_PREFLIGHT_NOT_RELEASED**

Acceptance 审核实现候选 `7e28ee4` 与
`docs/evidence/P1-M3-BODY-001-1c-preflight.md`。round 10 §B.1 的
N7/N-EVAL-1 清理成立：`Scene006Visibility.cs` 四处均是同一类失效行号，
改为符号定位且零代码语义；「两处→四处」是候选事实计数修正，不是范围扩大。
1a-β 证据的内容定位与 `world_estimate.geo_reject_reason` 清单补项亦正确。
批次边界成立：没有 Play、正式 ID、run 目录或新指标。

但 arm A trial 1 **不得执行**。当前操作单会消耗冻结的 5 次之一，却不能
保证产出 BC-BODY1-2/-5/-14/-15 要求的可复算证据，且 Arm A 运行方式与
§5.1「只切换 planner」字面冲突。以下四项全部关闭后才可再次返回 Acceptance。

#### A. 阻断项

1. **Arm A 关闭了整个 body runtime，不是选择 hold planner。** 操作单要求
   不传 `--body-policy`；代码因此不会构造 `HoldBodyPlanner` 或
   `WorldEstimateFilter`，`_body_step` 全程不运行。可是已复核代码明确把
   `HoldBodyPlanner` 定义为「Arm A expressed as a planner」，目的正是两臂
   走同一逐帧 wiring、只切换 planner；§5.1 也逐字要求 only planner differs。
   这会使 Arm A 缺少 estimator/planner 记录，并把「无 body runtime」与
   「threshold runtime」混在同一消融里。
2. **正式 trial 的逐帧离线证据载体不存在。** BC-BODY1-2 要求
   `CoverageEvaluator` 真值流按 `frame_id` join 后用目标路线里程划窗；
   但当前 `WriteRate3EvaluationTruth` 仅在 active RATE-003 shared-clock
   session 写出，而本 CLI 不启用 RATE-003。普通 M3 Play 不持久化目标
   `(x,z)`、几何可见性或 truth box 流；tracker run log 也不含这些真值。
   所以 arm A trial 1 结束后无法按 `62.5 m` 窗复算
   `C_track|geom`/`C_quality`，更无法做两臂对称的里程配对。
3. **饱和“占比”无数据来源。** `runtime/metrics.json` 的
   `gimbal_saturated`/`tether_saturated` 只是写入时刻的两个 bool，不是
   全 run 占比；Arm A 未启用 body runtime 时，其 run log 也不记录平台
   饱和字段。操作单 §B.2 step 5 因而承诺了当前产物不能计算的
   BC-BODY1-14(e) 诊断量。trial 1 一旦消耗，事后补代码不能恢复该序列。
4. **`110.0 s` 不是“整圈”边界。** 项目早已因无固定时间步撤回
   「一圈 = 106.5 s」；`LoopTargetVehicle.Step` 还会在每个 waypoint
   距离 `<0.5 m` 时用一个 Update 只换 waypoint、不移动。故
   `--planned-duration-s 110.0` 既不能机械证明覆盖完整一圈，又会在常见
   运行下把第二圈开头混入 `runtime/metrics.json:aggregate.c_geom`。
   H1 的整圈定义域必须由冻结路线位置/首次闭环机械划定，不能由墙钟替代。

另有来源绑定缺口：盘上已有 1b 诊断留下的 `runtime/metrics.json`，其 schema
没有 `run_id`。当前 runbook 未要求在 Play 前隔离旧文件，也未要求 post-run
指标与本 run 的逐帧证据相互核对；失败路径可能把旧指标误认作 trial 1。

#### B. Binding revision requirements（按字面执行）

1. **Arm A wiring**：正式 Arm A CLI 必须选择已复核的 `hold` planner，传入
   `--body-policy hold`、冻结的 body planner config 与主环线 scenario
   config；Arm B 只把该值切为 `threshold`。两臂均构造同一 estimator、走
   同一 `_body_step`/run-log 路径，差异仅 planner 实例。初始化期既有一次
   `hold_body()` 保留，但不得用「完全不启用 body runtime」代替 Arm A。
2. **先落地再采集**：在任何正式 Play 前，落地并测试 run-bound 的 M3 离线
   truth/evidence carrier 与 `tools/analyze_m3_body.py` 最小输入链。每个 sensor
   frame 至少可按同一 `run_id + frame_id` 取得：目标世界 `(x,z)`（可复算
   路线里程）、几何可见性、truth box/中心与 gimbal/tether saturation；
   tracker/estimator/planner 仍只能读 v3 sensor frame 与观测，真值文件只准
   离线分析读取。不得把真值新增进 sensor metadata、tracker 输入或决策路径。
3. **trial 1 可完整复算**：第一次 Play 产物必须足以让之后同一 trial 同时
   参加 H1、H2、`C_quality`、中心误差 max/p90、饱和占比、effort、planner
   切换、NEES/NIS 与 σ_px 对照；不得以“首跑只看 `C_geom`”为由省略未来
   无法补采的数据。分析工具须按 BC-BODY1-2/-5 对两臂使用同一冻结可见弧
   和对称路线里程样本规则。
4. **两个边界分开钉住**：目标首次进入遮挡弧时只结束
   `C_track|geom`/`C_quality`/H2 的 `62.5 m` 测量窗；同一 Play 继续到目标
   路线首次完成一个闭环，仅为 H1 整圈 `C_geom`。整圈样本集用路线位置
   机械确定；`planned_duration_s` 只可作为 fail-closed watchdog，不得定义
   指标边界。未取得恰好一个完整闭环即 trial invalid、回 Acceptance。
5. **旧现场 fail closed**：Play 前把旧 `metrics.json`、旧 M3 truth/output、
   frames 与 command/pointer 文件逐项隔离并记录；新产物必须携带或由机械
   receipt 绑定 `run_id`、scenario/hash、首末 frame、样本数和文件 SHA-256。
   run 目录继续 create-once；任何缺件、重复 ID、跨 run/hash 不一致均停止，
   不得用旧文件或就地重跑顶替。
6. **返工停点**：上述载体/分析改动涉及正式主指标证据链。Implementation
   完成代码、聚焦测试、证据与修订 runbook 后回 Acceptance；Acceptance
   按 workflow §4.3.1 确认稳定候选（含 implementation-role 写入归因），
   再交独立 Review。Review PASS 且 Acceptance 消费 verdict 前仍是零正式
   Play、零 trial/ID/指标。

#### C. Disposition

- `P1-M3-BODY-001` → **`REVISION_REQUESTED_1C_PREFLIGHT`**，唯一执行位回
  Implementation；N7/N-EVAL-1 清理保留，不要求回滚。
- arm A trial 1、run ID `p1-m3-body-001-arm-a-trial-1` 与其余 9 次 Play
  全部仍未释放；该名字仍只是预留，目录必须不存在。
- 本轮没有改变核心研究主张、阶段边界、主指标、硬件目标或范围；以上均是
  已接受 1c 数据链与配对条款的落实，因此没有新增用户关键授权。

---

### Acceptance round 12 — 2026-08-08（1c 返工停点审核）

Decision: **REVISION_REQUESTED — 1C_REWORK_STOP_POINT_NOT_CONFIRMED**

Acceptance 审核实现候选 `1c26785`、返工证据与 revision-2 操作单。round 11
§B.1 的 Arm A wiring 已正确修为 `--body-policy hold`；真值仍保持 evaluator
单向流出，`controller/` 零读取；N7 清理、零正式 Play/ID/指标、corridor/
margin pins、聚焦 Python 9/9 与实现者 Unity 267/267 均成立。

workflow §4.3.1 条件 5 已完成归因：规定命令
`check_role_writes --role implementation --base 7e28ee4` 唯一报出的越权路径
是提案文件，它完全来自 Acceptance commit `bca5d84` 的 round-11 决策；真实
实现区间 `bca5d84..1c26785` 对 9 个路径的 implementation-role 检查通过。
但条件 1、2、4 不成立，故停点不成立、不得交 Review、更不得 Play。

#### A. 阻断项

1. **分析工具在真实冻结配置上必然失败。** `analyze_m3_body.py` 读取
   `scenario.evaluation.tracking_iou`；真实 `config/scenario.default.json`
   的冻结键是 `tracking_iou_threshold`。9 个测试自造了错误的
   `tracking_iou` 键，因此全部通过却没有覆盖生产输入。
2. **完整 trial 的元数据在分析前已经被保留策略删除。** watchdog 为
   `130 s`、采集率 `5 Hz`，约产生 650 帧；冻结配置只保留 128 帧。
   工具却遍历全部 truth frame，并要求
   `runtime/frames/frame_<id>.json` 每个都存在，用来算机体轨迹和 receipt。
   所以前约 522 帧会在分析前被 `SensorFrameWriter` 淘汰，真实 trial 即使
   其他部分全对也会命名失败。合成测试保留了全部 46 份元数据，掩盖此缺口。
3. **原始证据不可复现。** `m3_body_truth.jsonl` 只存在共享 runtime 根目录，
   下一次 ordinary Play 会以 `FileMode.Create` 覆盖；分析只把它的哈希写进
   run 目录，没有保存原文件。共享 `runtime/frames` 也会继续淘汰/覆盖。
   因此 arm A trial 1 即使首次分析成功，trial 2 后也无法从 run 目录独立
   重跑 receipt/指标；哈希指向已经不存在的输入不是可复核证据链。
4. **冻结统计口径未按字面实现。** (a) `C_track|geom`/`C_track` 与饱和占比
   用 `capture_monotonic_s` 的墙钟差加权；正式操作单明确会暂停，host
   stopwatch 在暂停期继续走，恢复后的单帧会吞掉整段人工操作时间，而且
   §3.3 已要求指标按路线里程而非时间配对。(b) `C_quality` 只筛
   `truth_box_available`，没有筛 `geometrically_visible`；
   `ProjectBounds` 在被遮挡时仍可有框，违反 BC-BODY1-2「遮挡帧零进入
   分母」。(c) `compare_arms` 计算的是“B 的 run 中位数 − A 的 run
   中位数”，不是 BC-BODY1-5 要求的同路线位置配对差及其逐-run 中位数；
   两者数学上不等价。
5. **代价轴和 admissibility 仍未绑定。** `body_motion_effort_m` 积分的是
   planner 请求速度，而 BC-BODY1-1 冻结的是 plant `AppliedVelocity`；
   加速度/系留钳位后两者可不同。工具亦未机械拒绝错误 arm policy、tracker/
   re-anchor/model/init-box 配对或 compare 输出覆盖，并新造了 `5 m` 起点/
   离线容差而未从冻结 capture/`LoopTargetVehicle` 语义推导。

#### B. Binding revision requirements（按字面执行）

1. **生产输入先行**：修正 evaluator 阈值键读取；至少一个集成测试必须直接
   加载 checked-in `scenario.default.json`、body config 与 margin 工件，
   不准用自造的近似 schema 代替冻结输入。
2. **run 目录自包含**：单 trial 分析依赖的原始 truth 与平台/帧证据必须在
   下一次 Play 前 create-once 固化到该 run 目录（或由等价的 run-bound
   writer 直接产出）。验收方式：删除/替换共享 `runtime/frames` 和根目录
   truth 后，仍能仅从 run 目录逐字节重跑同一 receipt 与全部指标；A1 原始
   输入不得被 A2 覆盖。不得依赖 128-frame retention 保存一圈约 650 帧。
3. **路线定义域与权重**：测量窗及两臂配对量使用冻结路线里程权重，不读取
   capture wall-clock 作为指标权重；窗口 `62.5 m` 与首次闭环边界须处理
   首尾区间，不能把首帧权重置零后再丢掉末端残段。`C_quality` 的面积、
   最小边和中心误差只在 `geometrically_visible` 窗内样本上计算。
4. **H2 真配对**：每对 A/B trial 先按同一冻结路线位置构造三分量的配对差，
   再求该 run 的里程加权配对差中位数；五对 run 必须 5/5 同号，汇总中位
   改善也须为正。禁止用“两个 run 各自中位数之差”替代。测试必须给出一个
   两种算法结论相反的反例并锁定接受口径。
5. **实际代价与完整身份**：离线载体记录足以复算 plant
   `AppliedVelocity`（以及实际机体位置）的 run-bound 序列，effort 严格为
   `∫‖v_applied‖dt`；不得把 requested/published command 冒充 applied。
   receipt/compare 同时锁定并核对 scenario/hash、arm hold/threshold、body
   config、tracker/model/re-anchor、condition/track、ground plane、冻结初始
   框及 trial 顺序；所有正式分析/compare 产物 create-once。
6. **容差必须可归因**：撤回任意的 `START_MILEAGE_TOL_M = 5.0` 与
   `OFF_ROUTE_TOL_M = 5.0`。所需容差只能由 checked-in capture cadence、
   `LoopTargetVehicle` waypoint 切换阈值和 float 误差机械推导并写入证据；
   推导不能支持时回 Acceptance，不得自行选择宽值。
7. **必须新增的证伪测试**：覆盖真实 650-frame/128-retention 组合、一次人工
   pause 的巨大 monotonic gap、遮挡但仍有投影框、A1 原始输入在模拟 A2
   覆盖后仍可重跑、requested 与 applied 不同、错误 arm/identity、以及上条
   H2 反例。完成代码/测试/证据/runbook 后再次回 Acceptance §4.3.1；在
   Acceptance 确认并由独立 Review PASS 前仍为零正式 Play。

#### C. Disposition

- `P1-M3-BODY-001` → **`REVISION_REQUESTED_1C_REWORK_ROUND_2`**，唯一执行位
  回 Implementation；候选 `1c26785` 只作为被退回的可追溯检查点。
- Arm A trial 1 与预留 run ID 继续未释放；目录已独立核实不存在。
- 本轮不改变研究主张、阶段边界、主指标或硬件范围，只要求实现忠实落地
  既有 BC-BODY1-1/-2/-5/-13/-14 与 round-11 数据可复核条款；无新增用户
  关键授权。

---

### Acceptance round 13 — 2026-08-08（1c round-2 返工停点复查）

Decision: **REVISION_REQUESTED — 1C_REWORK_R2_STOP_POINT_NOT_CONFIRMED**

Acceptance 审核精确候选 `220a3af`、round-2 证据与 revision-3 操作单。
round 12 §B 中以下落点成立并保留：生产 IoU 键已改为
`tracking_iou_threshold`；truth carrier v2 记录机体位置与 plant
`AppliedVelocity`；分析不再依赖 128-frame metadata retention；主窗口权重
改为路线里程、`C_quality` 排除遮挡框、effort 不再使用请求速度；focused
Python 17/17、全套 Python 441/1 既有 infra 失败、盘上 Unity XML 267/267。
仍然是零正式 Play、零 trial/run ID、零正式指标。

workflow §4.3.1 条件 5 已按规定对上一退回候选运行：
`check_role_writes --role implementation --base 1c26785` 唯一报出提案文件，
可完整归因到 Acceptance commit `3a40711` 的 round-12 决策；真实实现区间
`3a40711..220a3af` 对 8 个路径通过 implementation-role 检查。条件 3 与 5
成立；条件 1、2、4 因下列可证伪缺陷不成立，所以停点不得确认、不得交
Review、更不得释放 arm A trial 1。

#### A. 阻断项

1. **离线容差与真实 `LoopTargetVehicle` 运动语义相反。** 工具声称车辆
   “沿折线段直行、离线误差仅 float32”，据此把 `OFF_ROUTE_TOL_M` 设为
   `1e-3 m`；但生产 `Step` 在距 waypoint `<0.5 m` 时直接切到下一点且不
   先吸附到旧点，真实轨迹会切角。Acceptance 按同一默认路线、2 m/s、
   5 Hz、130 s（650/651 个采样点）逐句重放该规则，最大折线偏离约
   `0.370581 m`；当前工具会在正式 trial 上报 `truth_off_route`。所谓
   full-scale test 实际只造了约 559 个**理想折线插值**点，既不是 §B.7
   指定的 650 帧，也没有重放生产转点逻辑，故掩盖缺陷。
2. **H2 第三分量换了指标。** BC-BODY1-1/-14 冻结的是“最小边
   `>=20 px` 占比”的同位置配对改善；候选却在 `c_quality_series` 保存
   原始最小边并以 `min_side_px` 做像素差。反例 A=21 px、B=22 px 时两臂
   占比都为 1、冻结改善为 0，候选仍把五对 run 全判正并返回
   `H2_SUPPORTED`。这不是命名注记，而是会改变研究结论的判定式错误。
3. **`--verify` 不是 run-directory-only。** run 目录只收了 truth；复算仍
   从目录外读取 scenario、margin、body config、re-anchor config 与 tracker
   model spec。Acceptance 在首次分析后删除这些外部文件及共享 truth，
   `--verify` 立即以 `unreadable_json` 失败。现有 A2-overwrite 测试保留了
   全部外部配置，不能证明 round 12 §B.2 的“仅从 run 目录”验收方式。
4. **run 来源、模型身份与 trial 顺序仍未机械绑定。** 每条 truth 的
   `scenario_id` 未核对；把整个 truth 流改成 `foreign-play` 仍被记为
   `deterministic-loop-default` 接受。工具只信 CLI 字符串和当前外部配置
   哈希，未核对 manifest 内真实 tracker `model_sha256`、re-anchor identity，
   也未要求 body policy 与 planner identity 相符。`compare_arms` 只检查
   两个列表长度为 5；同一个 A run 和同一个 B run 各重复五次仍可通过，
   错序/重复 pairing 不会 fail closed。无 `--output` 时 compare 还允许只
   打 stdout，违反“正式 compare 产物 create-once”。

#### B. Binding revision requirements（按字面执行）

1. **按生产转点规则推导路线容差。** 撤回“off-route 仅 float32”的错误
   前提。容差须显式包含 checked-in `LoopTargetVehicle` 的 `0.5 m` waypoint
   切换上界与可复算 float32 投影余量；分析 JSON 写出逐项公式及源位置。
   集成测试必须直接加载默认 scenario，在 130 s / 5 Hz 规模上逐句重放
   `Step` 的“`<0.5 m` 切点且该帧不移动”行为，覆盖至少 650 帧和真实拐角
   切线；合法切角不得失败，超过推导上界的偏离必须失败。不得再用理想折线
   插值冒充生产目标轨迹。
2. **恢复冻结的 H2 三分量。** 同位置序列的第三分量必须是
   `1[min_side_px >= 20]`，A/B 配对差为该指示量的 `B-A`，逐 run 里程加权
   中位数与 5/5/汇总判定沿用 BC-BODY1-5/-14；输出键明确写
   `min_side_ge20_share`，不得以原始像素差替代。新增 A=21/B=22 的反例，
   必须判该分量改善为 0 且不得返回三分量全过。
3. **实现真正的自包含复算。** 首次分析 create-once 收入 run 目录的不只
   是 truth，还须包含复算 route/threshold/window/identity 所需的 scenario、
   margin、body config、tracker spec 与 re-anchor config 的原始字节（tracker
   二进制可由 manifest 内已记录的逐模型 SHA-256 身份代表，无须复制模型）。
   receipt 只哈希这些 run-bound 副本；`--verify` 不读取任何 run 目录外
   路径。删除共享 runtime 输入及上述仓库源文件后，仍须逐字节复算同一
   receipt/指标。
4. **身份、来源、顺序与 create-once 全部 fail closed。** 每条 truth 的
   scenario、frame 序列及与重叠 tracker frame 的绑定字段必须核对；manifest
   schema、tracker identity + 两个 model SHA、re-anchor identity、body
   policy/planner 对应、condition/track/ground/init 均进入 receipt 与十-run
   compare。runbook 在首次 Play 前冻结 A1…A5/B1…B5 的十个唯一 ID 和
   配对顺序；compare 拒绝重复、缺号、错臂、错序，并在输出中哈希十份
   analysis。正式 compare 必须要求一个不存在的 create-once 输出路径，
   禁止 stdout 作为正式成功路径。
5. **补齐会推翻当前主张的测试。** 至少新增并锁定：生产式 650-frame
   转点/切角、21→22 px 占比零改善、重复或错序 trial、foreign truth
   scenario、篡改 tracker model/re-anchor/body planner identity、删除全部
   run 外依赖后的 `--verify`、以及 compare 缺 create-once 输出。更新证据
   与 runbook 的相关声明，不得继续把 559-frame 理想插值测试称为 650-frame
   生产规模验证。

#### C. Disposition

- `P1-M3-BODY-001` → **`REVISION_REQUESTED_1C_REWORK_ROUND_3`**；唯一执行位
  回 Implementation。`220a3af` 是被退回的可追溯候选，不是 Review 候选。
- round 13 未否定上文列明的已成立落点；实现角色只做 §B 五项窄返工，完成
  后回到同一 §4.3.1 停点。Arm A trial 1、全部 10 次 Play、预留 ID 与正式
  指标继续未释放。
- 本轮不改变核心研究主张、阶段边界、主指标、硬件目标或范围；它恢复既有
  BC-BODY1-1/-5/-14 与 round-12 可复核/身份条款，无新增用户关键授权。

### Acceptance round 14 — 2026-08-08（1c round-3 返工停点复查）

Decision: **REVISION_REQUESTED — 1C_REWORK_R3_STOP_POINT_NOT_CONFIRMED**

Acceptance 审核实现角色固定的精确候选 `a3c1f4e`、round-3 证据和
revision-4 操作单。round 13 §B.1–3 已按字面落地并保留：生产 `Step`
容差为 `0.5 + 1e-3 m` 且 650-frame 重放覆盖合法切角/越界；H2 第三分量
恢复为 `1[min_side_px >= 20]`；首次分析收齐六类 run-bound 输入，删除
外部源后 `--verify` 仍逐字节复算。正式 compare 的十个 CLI ID 顺序和
create-once 输出也已实现。focused Python 20/20、全套 Python 444/1（唯一
失败仍为既有 `test_check_docs.py` infra 债务）、盘上 Unity XML 267/267；
零正式 Play、零 trial/run ID、零正式指标。

workflow §4.3.1 条件 5 已按规定对上一退回候选运行：
`check_role_writes --role implementation --base 220a3af` 唯一报出提案文件，
可完整归因到状态板所载 Acceptance commit `278b666` 的 round-13 决策；
真实实现区间 `278b666..a3c1f4e` 对 6 个路径通过 implementation-role 检查。
条件 3 与 5 成立；条件 1、2、4 因下面的来源/身份 false-pass 不成立，故
停点不得确认、不得交 Review、更不得释放 arm A trial 1。

#### A. 阻断项

1. **逐帧捕获绑定允许缺字段即绕过。** `analyze_trial` 遇到 tracker frame
   缺 `capture_monotonic_s` 时直接 `continue`。Acceptance 删除所有 tracker
   frame 的该字段后，候选仍生成成功 analysis；truth 与 tracker 因而不再有
   round 13 §B.4 要求的逐帧捕获时间绑定，但正式链无法察觉。
2. **声明身份未绑定到实际逐帧 planner。** `_check_identity` 只比较 CLI
   policy 与 manifest 的 `planner`，不核对 manifest 已有的
   `body_planner.policy`。把 manifest policy 从 `hold` 改成 `threshold` 仍被
   接受；更严重的是，把每条 tracker frame 的 `body_planner.name` 全部改成
   `threshold-corridor-v1`，同时保留 manifest/receipt 的 `hold-v1`，分析仍
   成功。候选因此可以把 B 臂实际逐帧行为登记成 A 臂。
3. **十个路径不等于十份 trial 来源。** compare 的 `_load(run_id)` 不核对
   analysis 内 `receipt.run_id` 是否等于所在路径的 frozen ID。Acceptance
   将 A1 的 analysis 原字节复制到 A2 路径后，compare 仍成功，并在结果中
   留下两个相同 SHA 而不拒绝；这正是 round 13 §B.4 要阻断的重复 trial，
   现有测试只重复 CLI ID 列表，没有测试重复 analysis 内容。
4. **`init` 身份没有进入十-run compare。** receipt 虽写入
   `init_frame_id`，`identity_keys` 却只比较 init box。把 A2 的初始化帧从
   `0` 改成 `99`，十-run compare 仍成功；round 13 §B.4 明确要求
   condition/track/ground/**init** 全部进入 compare，这一项尚未落地。

#### B. Binding revision requirements（按字面执行）

1. **捕获时间不得缺省。** 对每一条 `record_kind=frame` 的 tracker 记录，
   `capture_monotonic_s` 必须存在、为非 bool 的有限数；对应 truth 记录的
   同名字段也必须存在且有限，两者绝对差须 `<=1e-9 s`。任一缺失、非有限
   或不等立即 fail closed；删除 tracker 全部捕获时间的反例必须失败。
2. **formal ID、manifest 与逐帧 planner 三层一致。** `analyze_trial` 只接受
   revision-4 已冻结的 A1…A5/B1…B5 十个 ID，并从 ID 推导期望 arm：A 必须
   `hold`/`hold-v1`，B 必须 `threshold`/`threshold-corridor-v1`。CLI
   `body_policy`、manifest `body_planner.policy`、manifest
   `body_planner.planner` 必须逐项等于该期望。每条
   `compute_stage=update` frame 必须有 `body_planner` mapping 且 `name` 等于
   期望 planner；`compute_stage=init` 可不含 planner，但若存在也必须相等。
   至少须有一条合法 update frame，缺字段/错名立即 fail closed。
3. **compare 绑定路径、内容和完整 init 身份。** 加载每个 frozen ID 时必须
   要求 `analysis.receipt.run_id == requested run_id`；A/B receipt 的
   `body_policy` 与 `body_planner_name` 分别等于第 2 条的期望组合。
   `init_frame_id` 加入 cross-run `identity_keys`，与现有 `init_box_norm` 一起
   比较。十份 `analysis_sha256` 的值必须两两不同；任意重复即
   `duplicate_trial_analysis` fail closed。
4. **只补六个命名反例并同步声明。** 新测试必须分别锁定：缺全部 tracker
   capture 字段；A frozen ID 配 threshold；manifest policy 与 CLI 不同；
   update frame planner 与 manifest 不同；A1 analysis 复制到 A2 路径；不同
   `init_frame_id`。前五个须在 analysis/compare 对应最早阶段失败，第六个
   须在 compare 失败。更新 round-3 证据和操作单中“full identity/重复 trial
   已拒绝”的过早声明；不得改动已成立的容差、H2、自包含复算、指标公式或
   C# 载体，除非先把新歧义退回 Acceptance。

#### C. Disposition

- `P1-M3-BODY-001` → **`REVISION_REQUESTED_1C_REWORK_ROUND_4`**；唯一执行位
  回 Implementation。`a3c1f4e` 是被退回的可追溯候选，不是 Review 候选。
- round 14 保留 §B 开头列明的已成立落点；round 4 只闭合上述身份/来源链。
  完成后回到同一 §4.3.1 停点。Arm A trial 1、全部十次 Play、正式 run ID
  与指标继续未释放。
- 本轮不改变核心研究主张、阶段边界、主指标、硬件目标或范围，不产生新的
  用户关键授权。阻断项是同一 round-13 §B.4 的有限收尾，不是新需求扩张。

### Acceptance round 15 — 2026-08-08（1c round-4 返工停点复查）

Decision: **REVISION_REQUESTED — 1C_REWORK_R4_STOP_POINT_NOT_CONFIRMED**

Acceptance 审核实现角色固定的精确候选 `977a997`、round-4 证据和
revision-5 操作单。round 14 的 capture 必填/有限/同帧相等、冻结 ID→CLI→
manifest policy/planner、analysis 路径→receipt、十份哈希去重和
`init_frame_id` 跨 run 比较均已落地并保留。focused Python 22/22、全套
Python 446/1（唯一失败仍为既有 `test_check_docs.py` infra 债务）、盘上
Unity XML 267/267；零正式 Play、零 trial/run ID、零正式指标。

workflow §4.3.1 条件 5 已按规定对上一退回候选运行：
`check_role_writes --role implementation --base a3c1f4e` 唯一报出提案文件，
可完整归因到状态板所载 Acceptance commit `3ae4410` 的 round-14 决策；
真实实现区间 `3ae4410..977a997` 对 7 个路径通过 implementation-role 检查。
条件 3 与 5 成立；条件 1、2、4 因下面尚未绑定的 init/stage 来源不成立，
故停点不得确认、不得交 Review、更不得释放 arm A trial 1。

#### A. 阻断项

1. **manifest init 与逐帧 `compute_stage` 仍可分裂。** 当前工具只把字面
   `compute_stage == "init"` 当作可省略 planner 的记录，却不要求该记录
   就是 manifest 的 `init.frame_id`，也不要求 init 恰好一条。Acceptance
   将 frame 1…44 全部改标为 `init` 并删除其 planner，只保留 frame 45 为
   正常 update，候选仍成功生成 analysis；这些被隐藏的 update 行为不再受
   planner 身份核对。单独删除 manifest `init.frame_id` 也仍成功，receipt
   写入 `null`。这使 round-14 所称“完整 init 身份”仍可缺失。
2. **提交的 update 反例没有命中 update 分支。** 名为
   `update_frame_planner_mismatch` 的 mutation 把 init 和 update 的 planner
   全部改错，实际首先报 `init_frame_planner_mismatch:0`；即使删除 update
   分支检查，该测试仍会通过。Acceptance 仅改错 update 行、保留 init 不动
   时，候选会正确报 `update_frame_planner_mismatch:1`，说明实现主体已有，
   但 round 14 §B.4 要求的命名反例尚未真正锁住它。

#### B. Binding revision requirements（按字面执行）

1. **把 init 身份与 stage 唯一绑定。** manifest `init.frame_id` 必须存在，
   类型恰为非 bool 的整数且 `>=0`。`frame_records` 中必须恰有一条
   `compute_stage == "init"`，且其 `frame_id` 必须等于该 manifest 值；
   其余每条必须恰为 `compute_stage == "update"`。stage 缺失、其他字符串、
   零条/多条 init、init ID 不符均以 `AnalysisError` fail closed。至少仍须
   有一条 update。
2. **在可信 stage 划分后核对 planner。** 唯一 init 行可省略 planner；若
   存在则必须是 mapping 且 `name` 等于期望 planner。每条 update 仍必须是
   mapping 且名称相等。不得用“非 init 一律视作 update”代替第 1 条的 stage
   枚举检查。
3. **三个隔离反例。** 修正 `update_frame_planner_mismatch`：只改
   `compute_stage=update` 行，init 行保持原样，并断言错误前缀为
   `update_frame_planner_mismatch:`。另增两个独立测试：(a) 删除 manifest
   `init.frame_id`；(b) 把至少一条原 update 行改标 init 并删除 planner。
   三者都必须抛 `AnalysisError` 且不生成 analysis；round-14 六个反例全部
   保留。
4. **范围冻结。** 只改分析工具、上述测试与对应证据/操作单声明；不得改
   已成立的 capture 数值绑定、ID/policy/planner 组合、compare、容差、H2、
   自包含复算、指标公式或 C# 载体。若需要放宽本节任何字面条件，先退回
   Acceptance，不得自行解释。

#### C. Disposition

- `P1-M3-BODY-001` → **`REVISION_REQUESTED_1C_REWORK_ROUND_5`**；唯一执行位
  回 Implementation。`977a997` 是被退回的可追溯候选，不是 Review 候选。
- round 15 保留开头列明的已成立落点；round 5 只闭合 init/stage 唯一绑定
  与三个隔离测试，完成后回到同一 §4.3.1 停点。Arm A trial 1、十次 Play、
  正式 run ID 与指标继续未释放。
- round 14 对“init 行”的唯一性写得不够显式，本轮把该隐含前提机械化；
  这是同一身份/来源链的有限归因，不改变研究主张、阶段边界、主指标、硬件
  目标或范围，不产生新的用户关键授权。

### Acceptance round 16 — 2026-08-08（1c round-5 返工停点复查）

Decision: **ACCEPTED — 1C_REWORK_R5_STOP_POINT_CONFIRMED / RELEASE_TO_REVIEW**

Acceptance 审核精确候选 `e030310`、round-5 证据和 revision-6 操作单。
round 15 §B 四条逐字成立：manifest `init.frame_id` 强制为非 bool、非负
整数；tracker frame 恰一条 init 且 ID 与 manifest 相同，其余全部显式
update；planner 只在该可信划分后核对；update-only、缺 manifest init 与
update→init 三个隔离反例命中各自错误前缀且不生成 analysis。额外的缺失/
未知 stage、零 init、init ID 不符也 fail closed。round 14 及更早的 capture、
arm、compare、容差、H2、自包含复算和指标公式保持不变。

#### A. workflow §4.3.1 五条件

| 条件 | 结论 | 依据 |
|---|---|---|
| 1. 范围和接口冻结 | **PASS** | `5888041..e030310` 仅 7 个 implementation 白名单路径：分析工具、测试、操作单/round-4 更正、round-5 证据和状态轮换；零 C#/config/scenario 改动。1c 的 run/truth/analysis/compare 接口由 revision 6 冻结。 |
| 2. 相称测试/编译 | **PASS** | Acceptance 重跑 focused Python 24/24；全套 Python 448/1，唯一失败仍为未触碰的既有 `test_check_docs.py` infra 债务；盘上 Unity Edit Mode XML 267/267。原始两个绕过分别报 `init_frame_record_count:45`、`manifest_init_frame_id_invalid:None`，update-only 报 `update_frame_planner_mismatch:1`。 |
| 3. 已知 Unity 失败 | **PASS** | 本批零 C# 改动，回归 267/267；无已知 Unity 失败。正式 Play、run ID 与指标尚未创建，继续等待 Review。 |
| 4. 候选、状态、风险、复核范围 | **PASS** | 精确候选 `e030310` 已提交；round-5 证据 §4 保留离线/零正式运行边界，操作单 revision 6、状态板与下列 Review 范围一致。既有 review 文件由独立 Review 追加新轮次，Acceptance 不预写 verdict。 |
| 5. 实现写入审计 + 归因 | **PASS** | `--base 977a997` 唯一报出提案文件，可完整归因到 Acceptance commit `5888041` 的 round-15 决策；真实实现区间 `5888041..e030310` 对 7 个路径通过 implementation-role 检查。 |

五条件全部成立，强制停点确认。Acceptance 的 `ACCEPTED` 只确认候选稳定、
可进入独立复核，不构成独立代码 verdict，也不关闭 1c/M3′ batch 1。

#### B. 给独立 Review 的准确范围

1. 在一次性 worktree 检查精确候选 `e030310`。上一独立复核通过的共享代码
   候选为 `61ea20b`；必须通读 `61ea20b..e030310` 的真实差异并归因其中已
   通过的 EVAL/1b/Acceptance/状态文档，不得只看实现者摘要。1c 的五个实现
   commit 为 `1c26785`、`220a3af`、`a3c1f4e`、`977a997`、`e030310`。
2. 独立核对 C# truth carrier 的普通-run 门控、逐 Play 截断、schema v2、
   frame/capture/scenario/body/applied-velocity 字段和非有限 fail closed；确认
   online planner/estimator 零读 truth，1b 的 Scene006 helper 改动不引入
   运行时语义漂移。
3. 独立核对离线分析全链：生产 Step 容差、里程/单圈/窗口、visible-only
   `C_quality`、applied effort、H1/H2 三分量和同位置配对、自包含 run-only
   verify、六类输入 receipt、十个冻结 ID、三层 arm/planner 身份、capture
   与 init/stage 绑定、compare 路径/内容/init/哈希/create-once。
4. 重跑 focused/full Python、corridor pin 和 Unity Edit Mode；逐个证伪
   production replay、21→22 指示量、外部依赖删除、foreign truth、模型/
   re-anchor/planner 篡改、重复/错序/错臂、缺 capture、复制 analysis、init/
   stage 绕过。核对证据声明与实际错误阶段。
5. Review 只在 `docs/reviews/P1-M3-BODY-001.md` 追加独立 verdict；若发现
   缺陷返回 Implementation。Review PASS 被 Acceptance 消费前，arm A trial
   1、全部十次正式 Play、正式 run ID 和指标继续禁止。

#### C. Disposition

- `P1-M3-BODY-001` → **`STOP_POINT_CONFIRMED_1C_REVIEW_PENDING`**；唯一执行位
  交独立 Review。精确候选 `e030310` 必须先推送并由一次性 worktree 检查。
- round 11–15 的退修历史和已成立落点全部保留；不再启动依赖 1c Review
  结果的实现，不运行正式 Play。
- 本轮不改变核心研究主张、阶段边界、主指标、硬件目标或范围，不产生新的
  用户关键授权，也不申领 `UNITY_NA`。

### Acceptance round 17 — 2026-08-08（消费 1c Review round 3）

Decision: **REVISION_REQUESTED — REVIEW_R3_REWORK_REQUIRED_CONSUMED**

Acceptance 消费独立 Review round 3 对精确候选 `e030310` 的
**`REWORK_REQUIRED`**。Review 在一次性 worktree 通读并归因
`61ea20b..e030310`，独立复跑 focused Python 24/24、全套 Python 448/1
既有失败（另有 1 项环境 skip）、Unity Edit Mode 267/267、corridor pin 与
两段 role-writes 审计；数字和已有成立落点全部复现。F1/F2 两项阻断均有
副本内反例支撑，Acceptance 接受归因。零正式 Play、零 run ID、零指标，
没有既有正式数据需要作废。

#### A. Verdict 归因

1. **F1 `CONFIRMED_BLOCKING` — margin/测量窗来源未绑定。** 当前 receipt
   虽记录 `margin_artifact_sha256` 与 `visible_arc_sha256`，但分析既不要求
   run-bound `margin.json` 的字节哈希等于
   `body_config.measurement_window.artifact_sha256`，也不要求其中的
   `visible_arc.sha256` 等于 config pin；compare 的 identity keys 也漏掉
   两键。Review 预置 identity 合法但窗口改为 `[0,10]` 的 margin 后分析和
   跨臂 compare 均成功，主指标域可被静默改变。
2. **F2 `CONFIRMED_BLOCKING` — round 14 planner 条款与生产补追语义冲突。**
   已复核的 `process_available` 只在每批最新帧运行 `_body_step`；合法补追
   行固定写 `compute_stage=update`、`skipped_count=1`、正
   `backlog_count`，且无 `body_planner`。revision 6 的“每条 update 必须有
   planner”会确定性杀死操作单要求的暂停初始化/追平流程。Acceptance
   **撤回该句的无条件读法**，以下述机械分类取代；不改变 C#、控制 cadence
   或 planner 决策，只让分析器承认生产已经记录的“该行未执行 planner”。

#### B. Binding rework requirements（按字面执行）

1. **F1：把两个 margin pin 变成分析与 compare 硬门。** 加载 run-bound
   `body_config.json` 和 `margin.json` 后、使用 measurement window 前，必须
   要求：
   - `sha256(run/margin.json) ==
     body_config.measurement_window.artifact_sha256`；
   - `margin.visible_arc.sha256 ==
     body_config.measurement_window.visible_arc_sha256`；
   - 两个期望值与实际值都必须是 64 位小写十六进制字符串，缺失/类型错误/
     不等均以命名 `AnalysisError` fail closed。
   receipt 继续写实际 `margin_artifact_sha256`/`visible_arc_sha256`，并把这
   两键加入 compare `identity_keys`。`_collect_inputs` 对已存在副本的
   create-once 行为可保留，但预置不同字节必须被上述 pin 拒绝。
2. **F1 反例。** 至少锁定：(a) run 目录预置 scenario identity 合法、窗口
   改为 `[0,10]` 的 margin，body config 仍带原 pin，首次分析必须失败且不
   生成 analysis；(b) 十份合成 analysis 仅一份
   `margin_artifact_sha256` 不同，compare 必须失败；(c) 仅一份
   `visible_arc_sha256` 不同，compare 必须失败。happy fixture 必须像生产
   config 一样提供两个真实 pin，不得通过删除 pin 规避。
3. **F2：按生产字段区分 planner decision 与合法 catch-up。** 每条 tracker
   frame 的 `backlog_count`/`skipped_count` 必须是非 bool、非负整数。唯一
   init 行必须为 `backlog_count=0`、`skipped_count=0`。每条 update 只能是：
   - **decision row**：`skipped_count=0`；必须有 `body_planner` mapping，且
     `name` 等于冻结 arm 的期望 planner。`backlog_count` 可为 0（单帧批）
     或正数（补追批的 latest）；
   - **catch-up row**：`skipped_count=1` 且 `backlog_count>=1`；必须无
     `body_planner`（键缺失或值为 `null`），表示生产侧该行未调用 planner。
   其他 skipped 值、`skipped=1/backlog=0`、catch-up 行携带 planner、decision
   行缺 planner 均 fail closed。整条 run 至少一条 decision update。不得
   修改 `track_loop` 让旧帧也执行控制，也不得把任意 planner 缺失 update
   泛化成合法 catch-up。
4. **F2 反例与真实启动重放。** fixture 为每条 frame 补生产一致的两个计数
   字段。新增至少：(a) 两帧补追批——第一条 update 为
   `backlog_count=1/skipped_count=1` 且无 planner，第二条为
   `backlog_count=1/skipped_count=0` 且有正确 planner，分析必须成功；
   (b) `skipped_count=0` 的 update 删除 planner 必须失败；
   (c) `skipped_count=1/backlog_count=0` 必须失败；(d) catch-up 行携带
   planner 必须失败。保留 round 14/15 的 planner 篡改和 init/stage 反例，
   更新操作单为 revision 7，逐字写明此分类。
5. **Review N11 同批勘误，不改数值。** 把 `OFF_ROUTE_DERIVATION` 的垂直
   情形精确公式改为 `d·L/sqrt(d²+L²)`，并把 round-3 证据中“dt 越细切点
   距离越小”的方向错误改为“越贴近 0.5 下方”；`OFF_ROUTE_TOL_M=0.501`
   与生产重放结果不变。N12–N14 保持非阻断建议，不借机扩大实现。
6. **范围冻结。** 只改分析工具、测试、操作单/证据与状态文档；零 C#、
   config、scenario、研究指标/阈值变化。F1/F2 完成后回到同一 §4.3.1
   停点，再交同一 Review round 4；任何需要放宽以上条件的情况先退回
   Acceptance。

#### C. Disposition

- `P1-M3-BODY-001` → **`REVIEW_R3_REWORK_REQUIRED_1C`**；唯一执行位回
  Implementation。`e030310` 保留为被 Review 退回的可追溯候选。
- Review 已确认的 C# truth carrier、Scene006 helper、容差/H2、自包含
  verify、既有身份链和测试数字全部保留；本轮只修 F1/F2 与 N11 文字。
- Arm A trial 1、十次正式 Play、run ID 与指标继续禁止；本轮不改变核心
  研究主张、阶段边界、主指标、硬件目标或范围，不产生用户关键授权，
  不申领 `UNITY_NA`。

### Acceptance round 18 — 2026-08-08（1c round-6 停点确认）

Decision: **ACCEPTED — 1C_REWORK_R6_STOP_POINT_CONFIRMED**

本轮只确认 workflow §4.3.1 稳定候选停点；**不签发独立代码复核通过，
不释放正式 Play**。精确候选为 `e438b97`，上一被 Review 退回的候选为
`e030310`。

#### A. 五项停点条件

1. **范围与接口冻结。** 实际实现批次 `419791b..e438b97` 恰 7 路径：
   `tools/analyze_m3_body.py`、`tests/test_analyze_m3_body.py`、操作单、两份
   实现证据和状态/归档；零 C#、config、scenario、控制 cadence、指标或
   阈值变化。F1 两个 pin 在窗口使用前硬核对并进入 15-key compare
   identity；F2 只承认精确的 decision/catch-up 分类，未泛化 planner 缺失。
2. **相称测试通过。** Acceptance 独立复跑 focused Python **28/28**；全套
   Python **452/1**，唯一失败仍为本批未触碰的既有
   `test_check_docs.test_compliant_minimal_status_passes` 基础设施债务。
   Implementation 留存的当前树 Unity XML 为 **267/267 PASS**。650 帧真实
   开跑重放、预置 margin、两种 compare 漂移和 decision/catch-up 正反例
   均进入 focused 套件。
3. **已知 Unity 失败。** 无。本批零 C#；当前 XML
   `testcasecount=267 result=Passed failed=0`。这只是自动回归，不替代后续
   用户正式 Play。
4. **候选、风险与复核范围。** `e438b97` 已提交；round-6 证据逐条映射
   Acceptance round 17 §B，并保留 N12–N14 非阻断项。另向 Review 披露
   **N15（非阻断文字残留）**：工具模块顶层 prose 仍写旧的
   `d*L/(L+d)`，但 binding 指定的 `OFF_ROUTE_DERIVATION` 常量、操作单和
   round-3 证据均已改为 `d*L/sqrt(d^2+L^2)`，容差和行为未变；由 Review
   判断是否需要随手清理，不能据此扩大实现范围。
5. **强制 role-writes 审计与归因。** 按规定运行
   `python3 tools/check_role_writes.py --role implementation --base e030310`：
   只报两条非实现路径。`docs/reviews/P1-M3-BODY-001.md` 全部归因 Review
   `51991a9`；提案路径归因 Acceptance `73890f7`（round 16）与 `419791b`
   （round 17）。隔离这些已登记批次后，实际实现区间
   `419791b..e438b97` 对 7 路径审计 **PASS**，无无法归因的越权写入。

#### B. Disposition

- `P1-M3-BODY-001` → **`STOP_POINT_CONFIRMED_1C_REVIEW_R4_PENDING`**；精确
  `e438b97` 交给独立 Review round 4，重点复核 F1/F2 关闭、反例承重和
  N15 文字残留，不重开 Review round 3 已确认的无关范围。
- 在 Acceptance 消费 Review round 4 的 PASS 之前，Arm A trial 1、十次
  正式 Play、run ID 与指标仍全部禁止；实现角色不得推进依赖该结果的新
  实现。
- 本轮不改变核心研究主张、阶段边界、主指标、硬件目标或范围，不产生用户
  关键授权，不申领 `UNITY_NA`。

### Acceptance round 19 — 2026-08-09（消费 1c Review round 4）

Decision: **ACCEPTED — REVIEW_R4_PASS_WITH_NOTES_CONSUMED**

Acceptance 消费独立 Review round 4 对精确候选 `e438b97` 的
**`PASS_WITH_NOTES`**。Review 在一次性 worktree 内独立重跑 focused
Python 28/28、全套 Python 452/1 既有失败（另 1 项环境 skip）、Unity
Edit Mode 267/267，以及 F1 pin 门移除和 F2 无条件 planner 两个变异；
结果与实现/停点证据逐位一致。零正式 Play、零 run ID、零指标。

#### A. Verdict 归因

1. **F1 `CLOSED`。** margin 字节与 visible-arc 两 pin 均在窗口首次使用前
   fail closed；实际值和期望值都过小写 hex-64 门；两键进入 15-key
   compare identity。预置 `[0,10]` 窗口和单-run 漂移反例承重，移除 pin
   门会使四项测试失败。
2. **F2 `CLOSED`。** init 0/0、decision 与 catch-up 的逐行分类和
   `track_loop.process_available`/`initialize()` 生产字段一致；planner
   缺失只在 `skipped=1 ∧ backlog>=1` 合法，且整 run 至少一条 decision。
   650 帧真实启动重放通过；恢复旧的无条件 planner 要求会在 frame 1
   确定性失败。
3. **N12–N16 全部 `NONBLOCKING_NOTE_POOL`。** N12 tracker frame ID 类型、
   N13 帧级 aspect、N14 错误名、N15 顶层旧公式 prose、N16 批结构交叉
   核对均不形成当前绕过或行为错误。接受 Review 定性：不得为了清注记
   改写已复核候选；统一留给后续获授权实现批次顺手处理。

#### B. 下一门与消耗边界

- `P1-M3-BODY-001` →
  **`REVIEW_PASSED_AWAITING_USER_GO_ARM_A_TRIAL_1`**。1c 实现、停点和独立
  代码复核四门已齐；下一动作是操作单 revision 7 的 arm A trial 1，随后
  机械读取 BC-BODY1-15 首跑退化门，任何后续 Play 前必须回 Acceptance。
- 本次用户请求“查看一下review结果”只要求读取/归因 verdict，**不解释为
  正式 Play、run ID 或指标采集 GO**。开始 trial 1 前仍需用户明确授权；
  授权原话由当场接受/辅助会话逐字写入 `docs/authorizations.md`。
- 获得 GO 后，当轮发令角色必须先按 workflow 记录实际 `git rev-parse
  HEAD` 与空的 `git status --porcelain`，核对实现字节对应已复核
  `e438b97`，然后才可创建唯一的
  `p1-m3-body-001-arm-a-trial-1`。不得提前创建目录、ID 或指标。
- 本轮不改变核心研究主张、阶段边界、主指标、硬件目标或范围，不申领
  `UNITY_NA`；候选保持冻结。

### Acceptance round 20 — 2026-08-09（arm A trial 1 尝试 1 作废归因）

Decision: **REVISION_REQUESTED — TRIAL_VOID_GO_CONSUMED_PREFLIGHT_R8_REQUIRED**

Acceptance 核对操作单 revision 7、授权账本原文、实现证据 §A–§E 和磁盘
环境。实测再次确认：`.venv-track` 的 OpenCV 为 `5.0.0` 但缺少 `torch`；
`.venv-yoloe` 为 OpenCV `5.0.0`、torch `2.13.0`、torchvision `0.28.0`、
ultralytics `8.4.104`，且暴露 `TrackerNano_create`。同一解释器下直接执行
`controller/track_loop.py --help` 因相对导入失败，而
`-m controller.track_loop --help` 成功。故根因和修订方向可复现。

#### A. 归因与授权裁定

1. **trial 作废，不进入五次样本。** tracker 在加载任何帧、
   `TrackLoop.initialize`、run 目录创建和任何发布之前异常退出；操作单 §5
   的 `trial 不以任何形式计入` 适用。`p1-m3-body-001-arm-a-trial-1`
   目录与分析均不存在，BC-BODY1-15 的三个数值分支一条也未触发。后续若
   合法完成 arm A trial 1，臂 A 仍只需恰好五个有效 trial，不把本次 void
   attempt 计成第六个。
2. **既有一次性 GO 已消耗。** 授权账本同时写死“进入 Play 恰一次”并明确
   排除“同一 run ID 下重进 Play或就地重跑”；用户已经进入并退出 Play
   一次。零 run 目录不恢复这项 Play 权限。任何第二次 Play——即使仍用
   冻结 ID/框——都必须在 revision 8 返工验收后取得**新的用户 GO**；本轮
   不代用户补发授权，也不提前请求授权。
3. **run ID 未被消耗，候选未被推翻。** 目录从未创建，故未来新 GO 可继续
   使用冻结的 `p1-m3-body-001-arm-a-trial-1`，这不是 ID 复用；在新 GO
   前不得创建它。失败由实现角色选择错误解释器造成，不是 `e438b97` 的
   代码缺陷；Review round 4、F1/F2 关闭和 N12–N16 定性全部保持有效。
4. **初始框冻结成立。** 用户确认的 frame `0` / px
   `(177,195,77,73)` 来自图像而非真值，精确归一化值固定为
   `0.2765625 0.40625 0.1203125 0.15208333333333332`。未来获 GO 的 Play
   只能逐字复用，不得重新框选或六位小数化；叠框若不再覆盖红色目标，只能
   fail closed 回 Acceptance，不得现场调整。

#### B. Binding rework requirements（Implementation 按字面执行）

1. **操作单 revision 8 的解释器/入口。** §4 唯一合法 tracker 入口改为
   `.venv-yoloe/bin/python -m controller.track_loop`；禁止裸 `python3`、
   `.venv-track` 和直接文件入口。全部 CLI 参数继续逐字保留，不改 tracker、
   re-anchor、planner、指标、窗口或阈值。
2. **冻结框精度。** §1/§3/§4 把上述 frame、像素框与四个精确分数写死；
   使用项目 `pixels_to_norm` 口径并要求往返为 `(177,195,77,73)` 逐值相等。
   禁止用显示用六位小数替代。未来 Play 中只允许对冻结叠框做“匹配/不匹配”
   目检，不重新估框。
3. **void 现场的下一轮隔离合同。** revision 8 必须列出：在未来新 GO 后、
   新 Play 前，把本次的 `runtime/frames/`、`runtime/m3_body_truth.jsonl`、
   `runtime/metrics.json` 分别移动到具名的
   `arm-a-trial-1-void-attempt-1-hold` 路径，逐项记录移动前后计数/SHA；原
   1b diagnostic holds 一字节不动，run 目录仍须不存在。当前返工期不执行
   这些移动，现场继续原样保留；不得删除、覆盖或把 void 工件喂给分析器。
4. **扩展环境预检而不破坏 TRACK-001。** `tools/check_track_env.py` 的无参数
   CSRT 行为与 JSON 字段保持兼容；新增显式 `--reanchor-config` 模式。该模式
   必须在当前解释器下：(a) 严格解析配置 schema；(b) 核对
   torch/torchvision/ultralytics 三个版本与 config pin 逐字相等；(c) 构造
   冻结 NanoTrack-v2 backend 并核对 OpenCV/两模型哈希；(d) 实际构造
   `YoloeProposer` 与 `DinoV2Embedder`，从而覆盖全部本地权重/源码/许可证
   哈希、包导入与模型加载。任一失败非零退出；全程不读帧、不推理、不联网、
   不创建 run ID/目录/指标/发布。
5. **预检证据与反例。** revision 8 在任何 Play 步骤之前写死命令
   `.venv-yoloe/bin/python tools/check_track_env.py --reanchor-config
   config/detector-reanchor.models.json`。实现证据记录其 PASS JSON（至少含
   `sys.executable`/`sys.prefix`、四包版本、config SHA、NanoTrack 身份和
   两个 re-anchor 构造器类型）；测试锁定 legacy 无参数路径，并证明缺包、
   pin 不等、模型/哈希或构造失败均 fail closed。不得把仅 import 成功写成
   完整 preflight PASS。
6. **范围和回程。** 仅允许修改 `tools/check_track_env.py`、对应测试、操作单/
   实现证据与状态文档；零 `controller/`、C#、config、scenario、模型字节、
   run 分析和研究口径改动。该批是非行为语义的预检/文档补强，不单独重开
   `e438b97` 的独立 Review；实现证据与真实 `.venv-yoloe` 预检 PASS 回
   Acceptance 核验后，才可向用户申请新的单次 Play GO。

#### C. Disposition

- `P1-M3-BODY-001` → **`REVISION_REQUESTED_PREFLIGHT_R8`**；唯一执行位交
  Implementation。当前 void 现场与未创建的正式 ID 保持冻结。
- 其余 9 次 Play 继续未授权；arm A trial 1 的第二次 Play 同样未授权。
  本轮零新 Play/ID/指标、零 `UNITY_NA`，不修改设计 v0.3.17。
- 本轮不触及核心研究主张、阶段边界、主指标、硬件目标或范围扩大，因此
  无新增用户关键授权；下一次用户授权只能在本轮返工通过后另行取得。

### Acceptance round 21 — 2026-08-09（预检 r8 实现核验）

Decision: **REVISION_REQUESTED — PREFLIGHT_R8_ROLE_BOUNDARY_AND_LITERAL_CONTRACT_REWORK**

Acceptance 对精确实现候选 `8d5a923` 重跑真实预检与测试。功能主路径可复现：
`.venv-yoloe/bin/python tools/check_track_env.py --reanchor-config
config/detector-reanchor.models.json` 返回 `PASS`/0，`.venv-track` 反例因缺少
torch 返回非零；focused **23/23**、full Python **475/475**，`git diff
--check` 通过，工作树保持干净。候选相对上一 Acceptance 批次 `34c1ec1`
共有 6 个路径，零 `controller/`、C#、config、scenario、模型或分析器改动，
且未创建 Play、run ID 或指标。以下三项仍阻止接受。

#### A. Blocking findings

1. **角色边界违规，且机械审计为假阴性。** `AGENTS.md` 和 workflow 把
   `tools/check_*.py` 全部列为工作流基础设施，仅用户直接授权的协调批次
   可改；实现候选却修改了 `tools/check_track_env.py`。round 20 §B.4/§B.6
   对该路径的许可越过了 Acceptance 自身权限，现作勘误，不构成用户授权。
   `python3 tools/check_role_writes.py --role implementation --base 34c1ec1`
   虽返回 PASS，但该检查器当前实际模式只枚举两个具体 `check_` 文件，与其
   自身说明及 `AGENTS.md` 的通配规则不一致，故不能推翻人工归因。本轮不改
   检查器；此基础设施漂移另留协调批次处理。
2. **版本 pin 未按 round 20 字面执行。** 实现先剥离 `+local` 后再比较，
   测试还明确接受 `2.13.0+cpu`。这不等于“当前模块的版本字符串与 config
   pin 逐字相等”，会把未冻结的本地构建当成合格环境。
3. **副作用证明不足。** 当前 fingerprint 对已有发布文件只比较“存在/不
   存在”，未比较字节，也未覆盖 `runtime/metrics.json`；因此无法支撑证据
   中“发布/指标前后机械不变”的主张。已有文件被原地改写时仍可能误报 PASS。

#### B. Binding rework requirements（Implementation 按字面执行）

1. **恢复受保护路径。** 将 `tools/check_track_env.py` 逐字节恢复为
   `34c1ec1` 版本；不得修改任何 `tools/check_*.py`。`8d5a923` 保留为可追溯
   的退修候选，不重写历史。不得顺手修复本轮发现的角色审计器模式漂移。
2. **迁移到普通实现工具。** 把仅 re-anchor 的预检放到新路径
   `tools/preflight_reanchor_env.py`，对应测试使用
   `tests/test_preflight_reanchor_env.py`。CLI 只接受且必须提供
   `--reanchor-config PATH`；操作单 step 0 的唯一命令改为：
   `.venv-yoloe/bin/python tools/preflight_reanchor_env.py
   --reanchor-config config/detector-reanchor.models.json`。不得给恢复后的
   `check_track_env.py` 增加代理、导入或兼容分支。
3. **原始版本字符串逐字相等。** 对 cv2、torch、torchvision、ultralytics
   均直接比较各模块原始 `__version__` 与配置 pin；不得规范化、截断或剥离
   `+local`。测试必须证明 `2.13.0+cpu` 及同类带 suffix 的值在 pin 为
   `2.13.0` 时 fail closed。
4. **机械副作用恒等。** 预检前后必须比较：(a) `runtime/runs/` 下直接子
   目录名集合；(b) `runtime/body_command.json`、
   `runtime/gimbal_command.json`、`runtime/tracking_observation.json`、
   `runtime/metrics.json` 各自的 missing/present 状态、文件大小与 SHA-256。
   任一创建、删除或字节变化均非零退出。测试至少覆盖“已有发布文件原地改
   字节但仍存在”以及 metrics 创建/改写两个反例；证据只陈述这些实际检查项。
5. **回归与证据。** 新工具 stdout 成功时只能有一个可直接
   `json.loads(stdout)` 的 JSON 对象；依赖噪声留在 stderr。测试以真实子进程
   锁定此合同，并继续覆盖缺包、raw pin 不等、schema/模型/哈希/构造失败。
   实现证据须记录 focused、full、真实 `.venv-yoloe` PASS、`.venv-track`
   FAIL 和恢复后的 legacy `check_track_env.py` 与 `34c1ec1` 字节恒等证明。
6. **范围和回程。** 允许路径仅为：恢复
   `tools/check_track_env.py`，新增上述普通工具/测试，更新操作单、实现证据
   与共享状态文档。继续零 `controller/`、C#、config、scenario、模型、
   run 分析和研究口径改动；不运行 Play，不创建/移动 ID、指标或 void 现场
   工件。完成后回 Acceptance；不单独重开 `e438b97` 的独立 Review。

#### C. Disposition

- `P1-M3-BODY-001` → **`REVISION_REQUESTED_PREFLIGHT_R8_ROUND_2`**；唯一
  执行位交 Implementation，返工仅限 §B。
- `e438b97` 的 Review round 4 继续有效；本轮退修针对预检批次 `8d5a923`，
  不归因为冻结 runtime 候选缺陷。
- arm A trial 1 的第二次 Play 及其余 9 次 Play 全部未授权；run ID 仍未创建，
  frame-0 box 与 void 现场继续冻结。本轮零新 Play/ID/指标、零 `UNITY_NA`。
- 本轮不触及核心研究主张、阶段边界、主指标、硬件目标或范围扩大；通过迁移
  普通工具路径即可修复，无需也未取得新的用户关键授权。

### Acceptance round 22 — 2026-08-10（预检 r8 round 2 核验）

Decision: **REVISION_REQUESTED — PREFLIGHT_R8_ROUND_3_FAILURE_PATH_IDENTITY_REWORK**

Acceptance 核验精确候选 `78d8f91`。round 21 的三个退修原因中，角色边界与
版本字面性已闭合，副作用恒等只闭合了**成功构造路径**，失败构造路径仍有
一个阻断缺口，故本轮不能释放新的 Play。

#### A. 已通过项

1. **受保护路径恢复成立。** `tools/check_track_env.py` 与 `34c1ec1` 均为
   SHA-256 `09e3b27e827eb319ac2c85a6468c07c89652900439c9bb14120c0d84bce73237`，
   diff 为零，且无新工具代理/导入；最终候选相对 `34c1ec1` 没有任何
   `tools/check_*.py` 变化。角色审计器漂移未被顺手修改。
2. **迁移与版本字面性成立。** re-anchor 预检只在普通路径
   `tools/preflight_reanchor_env.py`，操作单 revision 9 使用唯一新命令；四包
   raw `__version__` 均直接比较，无规范化，suffix 反例 fail closed。
   Implementation 披露的 cv2 解释现确认为 binding clarification：cv2 raw
   pin 取 `config/nanotrack-v2.models.json` 的 `opencv.tested_version`；该字段
   与生产 `NanoTrackV2Tracker` 的 raw-version gate 相同，`package_pin` 是发行
   包 requirement（含包名/build revision），不是可与 `cv2.__version__`
   逐字比较的版本串。
3. **正常路径与回归成立。** Acceptance 复跑真实 `.venv-yoloe` 得
   `PASS`/0，stdout 可直接解析且四包、三构造器、双模型 SHA 与 config SHA
   正确；`.venv-track` 得 1、stdout 0 字节并具名缺 torch。两个解释器 focused
   各 **31/31**（各一互补 skip），full Python **483/483**。真实成功路径的
   runs 名集合及三发布 + metrics 的 present/size/SHA-256 前后相等；void
   truth/metrics 哈希仍为 `64be7f85…` / `d31af400…`，正式 run 目录不存在。
4. **范围成立。** 相对 round 21 的 Acceptance 提交 `1abd221` 仅 7 个返工
   路径；人工核对确认受保护文件的变化只是恢复被退修字节。相对干净基线
   `34c1ec1` 的最终净实现只有新普通工具/测试及允许的证据/状态文档；零
   `controller/`、C#、config、scenario、模型、分析器、Play、ID 或指标改动。

#### B. Remaining blocker

`run_preflight` 只在 `_construct` **正常返回后**计算 `after` fingerprint。
若任一 loader/构造器先改写受保护 runtime，再抛异常，控制流会直接传播
`PreflightError`，不会执行后置比较，也不会报告现场已被污染。Acceptance
在临时目录中注入“`DinoV2Embedder` factory 先把已有 `metrics.json` 从
`before` 改为 `after!`，再抛 `RuntimeError`”；结果仅为
`DinoV2Embedder construction failed`，文件保留 `after!`。现有 31 个测试
只覆盖“改写后正常返回”的构造器，因此未发现该分支。

这违反 round 21 §B.4 的“预检前后必须比较”以及操作单“任何创建、删除或
字节变化即非零退出”的可归因含义。虽然主异常已令进程非零，但操作者无法
知道 void 现场同时被改写；若仍按普通缺包/构造失败处理，下一次取证可能在
已污染现场上进行。

#### C. Binding rework requirements（Implementation 按字面执行）

1. `run_preflight` 取得 `before` 后，无论 `_construct` 正常返回还是以普通
   异常失败，都必须**恰好执行一次** `after = side_effect_fingerprint(...)`
   并比较；只有“无主异常且 fingerprint 相等”才能生成 PASS。
2. 若 fingerprint 有差异，最终 `PreflightError` 必须包含
   `_describe_fingerprint_delta` 的具名差异；若同时有构造异常，还必须保留
   其类型与消息作为同一错误的 secondary context。不得因已有构造错误而
   跳过或降级副作用差异，也不得自动删除/回写受保护工件来掩盖现场。
3. 新增至少两个反例：(a) 已有 `runtime/metrics.json` 被改写后 factory 抛
   异常，最终错误必须同时具名 `metrics.json changed bytes` 与原异常；
   (b) 创建正式样式 run 子目录后 factory 抛异常，最终错误必须同时具名
   `run directories created` 与原异常。两例均证明后置 fingerprint 实际执行，
   不以“反正退出码已非零”替代比较。
4. 保留 round 21 已通过的所有测试；重跑两解释器 focused、full、真实
   `.venv-yoloe` PASS 和 `.venv-track` FAIL，更新实现证据。允许修改路径仅
   `tools/preflight_reanchor_env.py`、`tests/test_preflight_reanchor_env.py`、
   对应实现证据与共享状态；不得再碰 `tools/check_*.py`，无需改操作单命令。
5. 完成后回 Acceptance。该修复仍是非行为语义的预检保护，不重开
   `e438b97` 独立 Review，不申请 `UNITY_NA`，不启动 Play。

#### D. Disposition

- `P1-M3-BODY-001` → **`REVISION_REQUESTED_PREFLIGHT_R8_ROUND_3`**；唯一
  执行位交 Implementation，范围仅为 §C。
- round 21 的 protected-path、迁移、raw pin（含上述 cv2 clarification）、
  stdout 与成功路径 identity 结论保留，不要求重做。
- `e438b97` Review round 4 继续有效；arm A trial 1 第二次 Play 与其余 9 次
  Play 全部未授权。本轮零新 Play/ID/指标、零 `UNITY_NA`。
- 本轮不触及核心研究主张、阶段边界、主指标、硬件目标或范围扩大，无新增
  用户关键授权。

### Acceptance round 23 — 2026-08-10（预检 r8 round 3 核验）

Decision: **ACCEPTED — PREFLIGHT_R8_COMPLETE_AWAITING_FRESH_GO**

Acceptance 核验精确候选 `2336163`；round 20–22 的预检返工义务现已全部
闭合。此 verdict 只接受非行为语义的环境预检批次，不把 `P1-M3-BODY-001`
标为 `DONE`，不签发新的独立复核，也不自动释放任何 Play。

#### A. Scope and attribution

1. 相对上一 Acceptance 提交 `19c5fbd` 仅 5 个路径：普通实现工具、对应
   测试、实现证据、状态板及其机械归档。零 `tools/check_*.py`、`controller/`、
   C#、config、scenario、模型、分析器和操作单改动。
2. `python3 tools/check_role_writes.py --role implementation --base 19c5fbd`
   返回 PASS；人工 diff 同时确认本轮未利用已知 `check_*` 审计假阴性。
3. 本轮零 Play、零 run ID、零指标、零发布；真实 void truth/metrics SHA-256
   仍为 `64be7f85…` / `d31af400…`，正式 arm A trial 1 目录仍不存在。

#### B. Binding clauses verified

1. `run_preflight` 在取得 `before` 后，无论 `_construct` 正常返回还是以普通
   异常失败，都恰好执行一次 `after` fingerprint；仅“无主异常且恒等”生成
   PASS。
2. Acceptance 独立注入“已有 metrics `before`→`after!` 后抛异常”与“创建
   `p1-m3-body-001-arm-a-trial-1` 目录后抛异常”。两例均同时具名 fingerprint
   delta 与原构造错误，并把临时污染现场原样保留；同字节数 metrics 变化由
   SHA-256 捕获。
3. 新增计数测试证明成功/失败路径均为 before + after 两次 fingerprint
   调用；loader 级先污染后失败也受同一保护。原 31 条测试全部保留，两个
   解释器 focused 各 **36/36**（各一互补 skip），full Python **488/488**。
4. 真实 `.venv-yoloe` 预检返回 `PASS`/0，stdout 可直接 `json.loads`，
   `side_effect_identity.unchanged=true`；真实 `.venv-track` 返回 1、stdout
   0 字节并具名缺 torch。round 21 已接受的受保护脚本恢复、普通路径迁移、
   raw 四包 pin（cv2=`opencv.tested_version`）与成功路径 identity 均保持。

#### C. Release boundary

- `P1-M3-BODY-001` → **`PREFLIGHT_R8_ACCEPTED_AWAITING_FRESH_GO`**。候选
  `2336163` 的预检返工被 Acceptance 接受；冻结 runtime `e438b97` 的 Review
  round 4 继续有效，无需重开独立 Review。
- 2026-08-09 的 exactly-one-Play GO 已消耗；本 verdict **不是**新授权。
  arm A trial 1 第二次 Play 与其余 9 次 Play 继续未授权，run ID 未创建。
- 若用户随后明确 GO，只能释放 revision 9 下**恰好一次** arm A trial 1：
  逐字复用 `p1-m3-body-001-arm-a-trial-1`、frame 0、px
  `(177,195,77,73)` 和冻结 normalized box；先执行 §2.1 void 隔离、记录
  候选 HEAD/干净树，再以同一 `.venv-yoloe` 运行 step-0 预检。不得重框、
  重跑、释放其他 9 次 Play 或按结果调参；结果仍须回 Acceptance。
- 用户若授权，授权原话必须由当场 Acceptance/Chore 会话逐字写入
  `docs/authorizations.md` 后方可执行。本轮没有新增用户关键授权。

### Acceptance round 24 — 2026-08-10（attempt 2 运行中偏差裁定）

Decision: **REJECTED — CURRENT PLAY CONTINUATION NOT AUTHORIZED**

#### A. Report and record check

1. 用户报告 attempt 2 在 `sim_t = 10.854 s` 暂停，已经超出 revision 9
   §3 step 2 的 `[2,10) s`；同时报告最低保留帧为 `0`、冻结框覆盖正常、
   step 2 明列的两条 fail-closed 均未触发，路线里程测量窗不受暂停时刻影响。
2. Acceptance 核对磁盘 HEAD `0cf88f3` 且检查时工作树干净，但权威实现证据
   `docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md` §F.6 仍逐字写着“待本批
   提交后实测填入 HEAD、空 `git status --porcelain` 与 step-0 预检结果”；
   `docs/unity-test-log.md` 也没有 attempt 2 的 Play 前身份记录。
3. 因而状态板的“全部前置通过”主张没有被权威记录支撑。Acceptance 不用
   Play 已开始后的 HEAD/空树或补跑预检追认“采集开始前”的事实。

#### B. Binding disposition

1. `[2,10) s` 是本次 GO 逐字绑定的 revision-9 操作步骤；后续两条具名
   fail-closed 只约束最低帧和框覆盖，不撤销前面的暂停窗口。`10.854 s`
   超窗不能由 Acceptance 在运行中默认为合规。路线里程口径避免指标被暂停
   时长污染，但不能反向扩展已经授权的操作范围。
2. 独立且决定性的阻断是缺少事前身份/预检记录：本次授权把实际 HEAD、
   空树归因和同解释器 step-0 PASS 列为 Play 前强制条件；workflow §4.5
   还要求采集开始前把 HEAD/status 写入 Unity 日志。该时序证据不可事后重建。
3. **当前 Play 不得继续**：保持暂停，不启动 tracker、不恢复 Play；用户
   退出 Play 并报告 Console。Implementation 随后只可保留并哈希 attempt 2
   现场、确认 run 目录/发布/分析是否均未发生，并更正状态板的失实前置主张；
   禁止删除、覆盖、分析、重进或就地重跑。
4. 在退出与现场清点完成前状态为
   **`CONTINUATION_REJECTED_AWAITING_USER_EXIT_AND_PRESERVATION`**。若确认仍
   停在 tracker 初始化之前，则归为不计数的
   **`TRIAL_VOID_PROTOCOL_DEVIATION_PRE_TRACKER`**；无论最终现场如何，本次
   one-Play GO 已因进入 Play 消耗，其他九次仍未授权。
5. 未来 attempt 3 必须先以 revision 10 明确暂停超窗的机械终态，并让
   Play 前 HEAD/status/preflight 记录在发令前已落盘；经 Acceptance 重新
   核验和用户新的逐字 GO 后才可能执行。本轮不修改测量窗、指标、冻结框、
   runtime 或既有 Review，也不产生新的用户授权。

### Acceptance round 25 — 2026-08-10（attempt 2 最终归因与 revision 10 窄范围返工）

Decision: **REVISION_REQUESTED — ATTEMPT_2_VOID_FINAL / REVISION_10_NARROW_REWORK**

#### A. Final attempt-2 attribution

1. Acceptance 核验 Implementation 提交 `cfe28fc`；
   `python3 tools/check_role_writes.py --role implementation --base 6d293f5`
   对其 2 个路径通过。该批只改状态板与 attempt-2 证据，零实现代码、配置、
   工具、测试或 Unity 场景路径。
2. §G 清点闭合：现场 109 项（54 json + 54 jpg + `latest.json`），truth 54 行
   SHA-256 `7acd7a76…`，metrics SHA-256 `f12ec093…`；frame 0–53 连续，末帧
   `sim_t=10.854090`。run 目录、三发布、`m3_body_analysis.json` 与 tracker
   进程均不存在；attempt-1/1b holds 的计数与哈希保持不变。
3. 最终终态为 **`TRIAL_VOID_PROTOCOL_DEVIATION_PRE_TRACKER`**，不计入五次
   arm-A trials。零 run ID、零 tracker 指标、零发布、零分析；冻结 run ID
   至今未创建。2026-08-10 one-Play GO 已消耗，其他九次仍未授权。
4. 归因为两个操作/记录缺陷：用户暂停时刻超出绑定窗口；Implementation
   把已经实测的 HEAD/空树/preflight 只留在会话而未在发令前写入权威日志。
   这不是 runtime 缺陷，不重开 `e438b97` Review，也不改变主指标或测量窗。

#### B. Binding revision-10 rework scope（按字面执行）

1. **先保全 attempt 2，禁止清理。** 在任何未来 preflight/Play 前，只能把
   下列三个源移动到逐字目标；目标必须预先不存在，移动前后计数/SHA 必须
   等于 §G，零删除、零覆盖、零分析：
   - `runtime/frames/` →
     `runtime/frames.arm-a-trial-1-void-attempt-2-hold/`（109 项）；
   - `runtime/m3_body_truth.jsonl` →
     `runtime/m3_body_truth.arm-a-trial-1-void-attempt-2-hold.jsonl`
     （54 行，`7acd7a76…`）；
   - `runtime/metrics.json` →
     `runtime/metrics.arm-a-trial-1-void-attempt-2-hold.json`
     （`f12ec093…`）。
   attempt-1 与 1b holds 必须逐项复核不变；正式 run 目录仍须不存在。
2. **暂停窗口写成独立硬门。** revision 10 §3 step 2 必须逐字定义
   `2.000000 <= reported_sim_t < 10.000000`。不满足时唯一动作是保持暂停、
   不启动 tracker、不恢复 Play、退出并保全现场、回 Acceptance；frame 0/
   框匹配或路线里程窗不受影响都不得覆盖该终态，也不得运行中申请例外。
3. **消除 Play 前记录的自引用错误。** revision 10 必须规定以下顺序：
   (a) 新 GO 已由 Acceptance 逐字入账并提交；(b) 在该最终干净 HEAD `H`
   上，Implementation 运行并报告 `git rev-parse HEAD`、空的
   `git status --porcelain`、`e438b97..H` 路径归因及 step-0 的退出码/完整
   JSON；(c) **Acceptance** 在用户进 Play 前把这些值写入
   `docs/unity-test-log.md`；(d) 发令时工作树只允许这一份尚未提交的 Unity
   日志差异，`git diff --name-only` 必须逐字只有该路径。workflow §4.5
   允许这种白名单文档差异；不得再以“要保持完全干净所以 Play 后补写”为由
   延迟记录。操作证据 §F.6 只链接该事前日志，不另造相互矛盾的身份来源。
4. **保留全部既有冻结语义。** revision 9 的唯一解释器/CLI、run ID、frame 0、
   像素框与 normalized box、planner/arm、130 s watchdog、分析器、阈值、
   测量窗、退化三分支和反调参纪律全部逐字不变。不得改 controller、Assets、
   config、models、tools、tests、指标算法、Review 或正式设计。
5. **允许写入路径仅限**
   `docs/evidence/P1-M3-BODY-001-1c-preflight.md`、
   `docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md`、
   `docs/current-status.md` 及机械归档；本轮不写 Unity 日志（它只在未来新 GO
   后由 Acceptance 写），不写授权账本，不进入 Play，不创建正式 ID/指标。
6. **返回条件。** 提交 revision 10、attempt-2 hold 的完整计数/SHA 与零覆盖
   证明、正式 run/发布/分析仍不存在的清点、相对 `cfe28fc` 的实现角色写入
   审计 PASS、`check_docs.py` PASS；状态置
   `REVISION_10_AWAITING_ACCEPTANCE` 后返回 Acceptance。Acceptance 接受前
   不询问 GO；即使 revision 10 被接受，也必须另获用户新的逐字 GO。

#### C. Explicitly out of scope

- 不修 runtime 代码，不重跑自动测试或独立 Review，不使用 `UNITY_NA`；
- 不重框、不改参数/阈值/窗口/载体/模型/规划器/指标，不分析 void 工件；
- 不进入 Play，不复用/创建 run ID，不释放 arm A trial 2–5 或 arm B 1–5。

### Acceptance round 26 — 2026-08-10（revision 10 复核）

Decision: **ACCEPTED — REVISION_10_PROTOCOL_REWORK_CLOSED / AWAITING_FRESH_USER_GO**

#### A. Round 25 §B.1–6 逐条核验

1. **B.1 PASS。** Acceptance 直接复核当前现场：attempt-2 hold 为 109 项
   （54 json + 54 jpg + `latest.json`），两类帧号均连续 0–53，
   `latest.frame_id=53`；truth 为 54 行、SHA-256 `7acd7a76…`，metrics
   SHA-256 `f12ec093…`。attempt-1 hold 为 93 项且两个 SHA 分别仍为
   `64be7f85…`/`d31af400…`；1b hold 为 257 项且五个 SHA 逐项不变。
   `runtime/frames/` 为空，正式 run、三发布、共享 metrics/truth 与任何
   `m3_body_analysis.json` 均不存在。移动前目标不存在与前后相等的零覆盖
   证明已完整写入实现证据 §H；void 工件仍禁止删除、覆盖或分析。
2. **B.2 PASS。** revision 10 的 §1 与 §3 step 2 逐字钉住
   `2.000000 <= reported_sim_t < 10.000000`；越界只允许保持暂停、不启动
   tracker、不恢复 Play、退出保全并回 Acceptance。门 2/3 或里程窗均不得
   覆盖 `TRIAL_VOID_PAUSE_WINDOW_VIOLATION`，运行中不得申请例外；§5 同步
   给出 tracker 启动前终态表。
3. **B.3 PASS。** §2.0 的唯一顺序为：新 GO 由 Acceptance 入账并提交 →
   Implementation 在最终干净 HEAD 报告 HEAD/空树/`e438b97..H` 归因及
   step-0 退出码/完整 JSON → Acceptance 在 Play 前写 Unity 日志 → 发令时
   `git diff --name-only` 逐字只有 `docs/unity-test-log.md`。禁止事后补写，
   操作证据 §F.6 只链接该事前记录。
4. **B.4 PASS。** `cfe28fc..6cfc792` 的操作单差异只增加上述记录顺序、
   attempt-2 hold、暂停硬门和对应终态/边界，并做必要的小节重编号；唯一
   解释器/CLI、run ID、frame 0、两种框表示、planner/arm、130 s watchdog、
   分析器、阈值、里程测量窗、既有三分支与反调参纪律均未改。runtime 候选
   `e438b97` 与 Review round 4 `PASS_WITH_NOTES` 不重开。
5. **B.5 PASS。** 精确实现批次 `e8c2ca0..6cfc792` 恰四个允许路径：两份
   证据文档、状态板与机械归档；零 controller/Assets/config/models/tools/
   tests/指标/Review/正式设计/Unity 日志/授权账本改动，零 Play/ID/指标。
6. **B.6 PASS（按 workflow §4.3.1 完成逐路径归因）。** 当前
   `check_docs.py` PASS。`check_role_writes --base cfe28fc` 的混合角色区间
   原始输出只报提案与 Unity 日志两个路径；二者均由中间的 Acceptance 提交
   `e8c2ca0` 独占写入，用于 round 25 verdict/attempt-2 最终归因，非实现
   写入。以该提交为精确实现基线的
   `check_role_writes --role implementation --base e8c2ca0` 对 4 个路径
   PASS。故无未归因越权路径；不得把混合角色区间的原始非零误写成实现越权，
   也不得省略这两条归因。

#### B. Binding execution boundary（按字面执行）

1. 本 verdict 只接受 revision 10 的现场保全与操作协议返工；不把
   `P1-M3-BODY-001` 标为 `DONE`/`UNITY_NA`，不签发独立 Review，也不改变
   v0.3.17、BC-BODY1-1…20、主指标、测量窗或冻结 runtime 候选。
2. 当前状态为 **`R10_ACCEPTED_AWAITING_FRESH_USER_GO`**。本 verdict 本身
   **不授权任何 Play**；2026-08-10 attempt-2 GO 已消耗，arm A trial 1
   attempt 3 与其余九次 Play 全部未授权。
3. 只有用户对“按 revision 10 执行恰好一次 arm A trial 1 attempt 3”给出
   新的逐字 GO 后，Acceptance 才可按 §2.0 (a) 入账并提交；随后依次完成
   (b) Implementation 实测报告、(c) Acceptance 事前 Unity 日志记录与
   (d) 单一未提交日志差异核验。任一步未闭合都不得进入 Play。
4. attempt 3 的任何结果仍须先回 Acceptance；arm A trial 2–5 与 arm B
   trial 1–5 不随本轮或未来一次 one-Play GO 自动释放。

### Acceptance round 27 — 2026-08-10（attempt 3 one-Play GO 入账）

Decision: **USER_GO_GRANTED_ARM_A_TRIAL_1_ATTEMPT_3 / PREPLAY_SEQUENCE_PENDING**

1. 用户在 round 26 的精确 offer 后逐字回复 **“授权play”**；原话、完整上文
   与排除项已当场写入 `docs/authorizations.md`。该授权只释放 revision 10
   下 arm A trial 1 attempt 3 的**一次** Play；attempt-2 GO 保持已消耗，
   其余九次 Play、重试/重进、重框、调参和 batch 2 均未授权。
2. 本 Acceptance 批次提交后才闭合 revision 10 §2.0 (a)。当前禁止直接进入
   Play；唯一下一动作是 Implementation 在最终干净 HEAD 上完成 §2.0 (b)：
   报告 HEAD、空 status、`e438b97..HEAD` 全路径归因和 step-0 退出码/完整
   JSON，然后立即返回 Acceptance。
3. Implementation 不得写 Unity 日志。Acceptance 收到完整报告后才执行
   §2.0 (c)，在 Play 前把真实值写入 `docs/unity-test-log.md`；发令前还须
   验证 §2.0 (d) 的 `git diff --name-only` 逐字只有该日志。任一步不成立即
   fail closed，不得进入 Play。
4. 当前状态为
   **`USER_GO_COMMITTED_AWAITING_IMPLEMENTATION_PREFLIGHT_REPORT`**；这不是
   Play 已开始、run ID 已创建或指标已产生。attempt 3 的任何结果仍先回
   Acceptance，不能自动释放后续 Play。

### Acceptance round 28 — 2026-08-10（attempt 3 提前退出裁定）

Decision: **REJECTED — MANUAL_FINALIZE_NOT_AUTHORIZED /
ATTEMPT_3_EARLY_EXIT_VOID_PENDING_PRESERVATION**

#### A. 事实与裁定

1. Revision-10 §2.0(a)–(d) 已在 Play 前闭合；磁盘保留的首个 tracker
   决策帧为 frame 36、`simulation_time_s=7.3804402351379395`，因此本轮不以
   暂停窗违规归因。用户随后报告：只进入 Play 一次并跑完一圈，但在
   `sim_t=125.3803` 主动退出，早于 `130.0 s` watchdog；三类发布正常，
   Console/tracker 无报错。
2. Acceptance 只读盘点发现正式 run 目录已经创建，`frames.jsonl` 为 755 行、
   末个感知记录为 frame 626 / `simulation_time_s=125.38031005859375`；truth
   为 627 行。run 目录当前只有 `frames.jsonl` 与 `manifest.json`，没有
   `metrics.final.json`、`summary.json` 或 `m3_body_analysis.json`。现场 SHA-256
   分别为 frames `8f9f3551…16b5`、manifest `e5caa982…8a65`、truth
   `6e273895…af50`、shared metrics `59085980…fd2`。
3. 选择用户给出的 **(b)**。Revision-10 §3 step 4 要求 tracker 在一圈后继续
   到 `--planned-duration-s 130.0` **自动完成**，然后用户退出 Play；step 5
   才允许绑定分析。“watchdog 不定义指标边界”只说明 130 s 不是指标窗，
   不会取消该完成顺序。`--finalize` 虽是通用 CLI 模式，却不在本 trial 的
   冻结命令或操作序列中；事后加入会把未达接受终点的现场人工封口。
4. 因此禁止 `--finalize`，也禁止运行 `analyze_m3_body.py`。用户报告的
   62.5 m 测量窗和 212.9706 m 整圈覆盖可作为现场陈述保留，但在绑定工具
   尚未合法运行且完成门未成立时，不构成正式指标、trial PASS 或首跑分支
   输入。基于已见结果放宽完成协议还会构成事后协议例外。
5. attempt-3 one-Play GO 已消耗；正式 run ID 已创建并因此消耗，不得复用。
   本次不计入五次 arm A trial，不触发 BC-BODY1-15 三分支，不释放其余九次
   Play，也不改变 `e438b97` 的 Review verdict。最终 void subtype 等稳定现场
   盘点返回 Acceptance 后再归因。

#### B. Binding preservation handoff（Implementation 按字面执行）

1. 不得再次进入 Play；不得运行 `--finalize`、绑定分析、dump/rebox/retry；
   不得删除、移动、覆盖、补写或规范化 run、truth、shared metrics 与三发布。
2. 只读解析与 `p1-m3-body-001-arm-a-trial-1` 对应的 tracker 精确 PID 和完整
   命令行。若已经退出，记录“未发现”及检查方法；若仍在运行，只对核实后的
   **该一个 PID** 使用不会执行 Python 正常 cleanup/finalization 的强制终止，
   不得使用会触发 `finally` 的 Ctrl-C/SIGINT，也不得用名称/glob 批量杀进程。
3. 强制终止前后分别盘点：进程状态、run 目录全路径清单、每个文件的字节数/
   行数/SHA-256、truth 与四个 shared 文件、三个发布、是否存在
   `metrics.final.json`/`summary.json`/`m3_body_analysis.json`；证明终止动作没有
   新建或改写任何现场文件。若出现任何差异，立即停止并逐项报告，不作清理。
4. 本 handoff 不授权修改实现代码、操作单、证据结论或指标语义。盘点完成后
   立即回 Acceptance；在最终 void subtype 与后继协议另行裁定前，不启动
   attempt 4 或任何依赖本结果的工作。

### Acceptance round 29 — 2026-08-10（attempt 3 最终归因与 revision 11）

Decision: **REJECTED — TRIAL_VOID_PROTOCOL_DEVIATION_POST_TRACKER_EARLY_EXIT /
REVISION_REQUESTED_R11_ATTEMPT_IDENTITY_AND_COMPLETION_HANDSHAKE**

#### A. Preservation handoff closed

1. 用户确认实现角色已经终止 tracker，并把流程交回 Acceptance。Acceptance
   随后在系统进程表执行精确筛选：
   `ps -axo pid=,ppid=,state=,command= | rg
   'controller\.track_loop|p1-m3-body-001-arm-a-trial-1|preflight_reanchor_env'`；
   结果只有筛选命令自身，没有目标 tracker/preflight 进程。
2. 终止后的 run 仍恰有 `frames.jsonl` 与 `manifest.json` 两个文件，聚合
   SHA-256 为 `e8cd6180…3bd8`；frames 755 行、truth 627 行，四个 round-28
   关键 SHA-256 逐项不变。`runtime/frames/` 为 257 个文件，清单聚合 SHA-256
   `346066c3…fb6`；三发布与 shared metrics 的当前 SHA-256 分别为
   body `71fa8035…0686`、gimbal `372e6007…55d`、tracking
   `b0dda5b0…26c4`、metrics `59085980…fd2`。
3. `metrics.final.json`、`summary.json`、`m3_body_analysis.json` 仍全部不存在；
   没有运行 `--finalize` 或分析器，也没有新增 run 文件。故 round 28 的现场
   保全终态成立，不再等待实现角色补写形式性交接。

#### B. Final attribution

1. Attempt 3 最终归因为
   **`TRIAL_VOID_PROTOCOL_DEVIATION_POST_TRACKER_EARLY_EXIT`**：tracker 已正常
   启动并持续发布，但用户在冻结的 130 s 自动完成门之前退出 Play，使仿真
   时间冻结、tracker 不能自然完成。它不是暂停窗、tracker startup、Console
   报错或已证明的模型/控制缺陷。
2. Attempt-3 one-Play GO 与原正式 ID
   `p1-m3-body-001-arm-a-trial-1` 均已消耗；void 现场不可删除、覆盖、分析或
   重新解释为正式 trial。报告的一圈/测量窗覆盖仍只属操作观察，不触发
   BC-BODY1-15，也不释放其余九次 Play。
3. 直接重进 Play 不合法：除缺少新 GO 外，冻结 analyzer 只接受十个旧正式
   ID，而 A1 的旧 ID 已被 void 现场 create-once 占用。拿 A2 顶替、移动后
   复用 A1、减少到四次或事后 finalize 都会改变配对/身份或覆盖历史。

#### C. Revision 11 binding requirements（Implementation 按字面交付）

1. **Attempt-3 隔离。** 以下七组 source→destination 逐字冻结；每个 destination
   移动前必须不存在：

   | Source | Destination |
   |---|---|
   | `runtime/runs/p1-m3-body-001-arm-a-trial-1/` | `runtime/runs/p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold/` |
   | `runtime/frames/` | `runtime/frames.arm-a-trial-1-void-attempt-3-hold/` |
   | `runtime/m3_body_truth.jsonl` | `runtime/m3_body_truth.arm-a-trial-1-void-attempt-3-hold.jsonl` |
   | `runtime/metrics.json` | `runtime/metrics.arm-a-trial-1-void-attempt-3-hold.json` |
   | `runtime/body_command.json` | `runtime/body_command.arm-a-trial-1-void-attempt-3-hold.json` |
   | `runtime/gimbal_command.json` | `runtime/gimbal_command.arm-a-trial-1-void-attempt-3-hold.json` |
   | `runtime/tracking_observation.json` | `runtime/tracking_observation.arm-a-trial-1-void-attempt-3-hold.json` |

   逐项记录移动前后文件数、行数、字节数和 SHA-256 相等，零删除、零覆盖、
   零分析；attempt-1/2/1b holds 也须证明不变。移动后只新建空
   `runtime/frames/`，不得预建 attempt-4 run 目录或其他 shared 文件。
2. **唯一替代 ID。** A1 的下一次且仅下一次采集 ID 冻结为
   `p1-m3-body-001-arm-a-trial-1-attempt-4`。Analyzer/compare 必须把它映射到
   canonical slot `arm-a-trial-1` 并与原 B1 配对，同时永久拒绝旧 void ID、
   任何其他 attempt 后缀、重复 canonical slot、缺号、错臂和错序。其余九个
   正式 ID 逐字不变。A1 analysis receipt 必须新增并逐字绑定：
   `acquisition_run_id="p1-m3-body-001-arm-a-trial-1-attempt-4"`、
   `canonical_trial_id="p1-m3-body-001-arm-a-trial-1"`、
   `attempt_number=4`、
   `predecessor_void_manifest_sha256="e5caa98276a48413f3d78d34228d8c41d8ad0b9e8b438c070d4925c4f14e8a65"`、
   `predecessor_void_frames_sha256="8f9f355186cf06d83dd30956552b9687cd4992454090f89ecc307f2b986016b5"`；
   compare 机械核对这些 A1 专属字段但不把它们要求为其余九个 run 的共同值。
3. **完成握手。** 冻结 `--planned-duration-s 130.0` 与仿真时间语义不变。
   跑完一圈后用户继续保持 Play；只有 Implementation 观察到 tracker 进程
   自然退出码 `0`、stdout final JSON 指向同一 acquisition ID 的
   `summary.json`、且 run 内 `metrics.final.json`/`summary.json` 已存在，才可
   逐字报告 `TRACKER_AUTO_COMPLETE_CONFIRMED` 并请用户退出 Play。用户不得
   依据“一圈已跑完”或 HUD 时间自行退出。
4. **异常终态。** 在上述确认前 Play 退出、tracker 非零退出、进程仍存活或
   任一终结工件缺失，均为新的 post-tracker void：不 finalize、不分析、不
   重进，保全并回 Acceptance。不得让墙钟替代仿真时间完成正常 trial。
5. **冻结不变项。** 不改 frame 0/box、planner/arm、模型、重锚、场景、130 s、
   62.5 m 窗、212.9706 m 整圈、主指标、阈值、五次/臂或 BC-BODY1-15；不以
   attempt-3 内容调参。Revision 11 零 Play、零新 ID、零指标。
6. **验证与停点。** 为 ID allowlist/canonical mapping、void predecessor binding、
   重复/错序拒绝和完成握手补机械反例；提交实现证据。因本轮改变正式 run
   绑定协议，Implementation 必须整理稳定候选后停下，由 Acceptance 按
   workflow §4.3.1 完成角色写入归因并交独立 Review；Review verdict 与新的
   用户逐字 one-Play GO 之前，不得执行 attempt 4。

### Acceptance round 30 — 2026-08-10（revision 11 稳定候选复核）

Decision: **REVISION_REQUESTED — R11_ROUND_2 /
STOP_POINT_NOT_CONFIRMED**

#### A. 已通过项

1. Candidate `6f188b2` 的 C1 现场保全通过：七个目标事前不存在，attempt-3
   run/frames/truth/metrics/三发布移动前后计数、行数、字节数与 SHA-256 相等；
   attempt-1/2/1b holds 不变，`runtime/frames/` 为空，attempt-4 run 未预建。
2. ID 映射主体通过：attempt-4 是唯一 A1 acquisition ID，旧 ID 具名拒绝，
   其他 attempt 后缀拒绝，其余九个 ID 不变；A1 receipt 五字段和 compare
   校验已实现。Acceptance 复跑 focused **34/34**、全套 **494/494**（1 skip）
   均通过，`check_docs.py` 通过。
3. 精确实现区间 `c53a075..6f188b2` 恰六个允许路径，
   `check_role_writes --role implementation --base c53a075` 通过；零
   controller/Assets/config/model/指标/Play/analysis。

#### B. 阻塞项

1. **B1 — 冻结操作单会确定性调用被拒 ID。** Revision-11 §3 step 5 仍写
   `python3 tools/analyze_m3_body.py --run-id
   p1-m3-body-001-arm-a-trial-1`，而新代码对该 ID 必然抛
   `run_id_void_consumed`。`tools/analyze_m3_body.py` 顶部 Usage 的单 trial
   和 compare 示例也仍使用旧 A1。若照操作单逐字执行，成功的 attempt-4
   会在绑定分析入口被错误作废。
2. **B2 — ID/终态文档自相矛盾。** §1 表仍称十个旧字符串都是正式
   `run ID / 目录`；§4 在唯一 CLI 已改变 run ID 后仍称“一个不改、一个不加”；
   §5 三行终态之后仍写“**两者都**在创建 run 目录前发生”，但第三行正是
   post-tracker、已创建 run 的 attempt 3。Analyzer 模块说明也仍称 compare
   冻结十个旧 acquisition ID。这些文字会分别诱导旧 ID、错误的变更审计和
   错误的 ID-consumption 处置。
3. **B3 — predecessor 只被声明，没有绑定真实 hold。** 当前 analyzer 只是把
   两个 SHA 常量写入 A1 receipt；全代码没有读取
   `runtime/runs/p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold/`。因此即使
   hold 缺失或其 manifest/frames 被改写，attempt-4 analysis 仍会声称绑定
   原 SHA 并通过；这不满足 C2/C6 的“void predecessor binding”。
4. **B4 — 完成握手机械反例缺失。** 新增六测只覆盖 ID/receipt；测试树没有
   `TRACKER_AUTO_COMPLETE_CONFIRMED`、exit-code、stdout final JSON 或两项
   终结文件的联合 gate。C3/C4 目前只有文档观察，C6 明确要求的完成握手
   机械反例未交付。既有 run-log/track-loop 测试只各自覆盖 summary/final
   文件，不能证明三条件 AND gate。
5. **B5 — 新测试放在首个 `unittest.main()` 之后。** `-m unittest` 导入模块
   时会发现它们，所以本轮 34/34 有效；但直接运行测试文件会在定义这六测前
   进入第一个 main，随后文件末尾又有第二个 main。合并为唯一的末尾 guard，
   避免备用入口静默少跑六测。

#### C. R11 round-2 binding rework（逐条执行）

1. 把操作单 §3 step 5、analyzer 顶部单-run Usage 与 compare A 臂首项全部改为
   `p1-m3-body-001-arm-a-trial-1-attempt-4`；所有后续路径/receipt/verify 示例
   使用 acquisition ID。Canonical ID 只以 `canonical_trial_id` 字段出现，
   不作为文件夹、CLI `--run-id` 或 compare 输入。
2. 把 §1 的 ID 行拆成“十个 canonical slots”与“十个 acquisition IDs”：A1
   acquisition 是 attempt-4，其余九个 acquisition 等于 canonical；create-once
   约束施加于 acquisition 目录。§4 改为“仅 run ID 按 C2 替换，其余参数不改
   不加”。§5 把前两种 pre-tracker void 与第三种 post-tracker void 分段，只有
   前两种可写“run ID 未创建/未消耗”。同步修正 analyzer 模块说明与 Usage。
3. 在 A1 `analyze_trial` 执行任何 create-once 收集/写入**之前**，只读核对
   predecessor hold：目录必须存在且直接文件集合恰为 `frames.jsonl`、
   `manifest.json`；两者 SHA-256 必须分别等于 round-29 的完整常量。具名失败
   至少为 `a1_predecessor_hold_missing`、
   `a1_predecessor_hold_file_set_mismatch`、
   `a1_predecessor_void_frames_sha256_mismatch`、
   `a1_predecessor_void_manifest_sha256_mismatch`，失败不得在 attempt-4 run
   新建任何分析输入或 `m3_body_analysis.json`。为缺失、额外文件和两种字节
   mutation 各补一条机械反例；测试可在临时目录中 patch 期望 SHA 为夹具值。
   此门只枚举文件名并计算原始字节 SHA，不解析 void 内容、不计算任何指标，
   因而不改变“禁止分析 void 工件”。
4. 在 `tools/analyze_m3_body.py` 增加**只读、不产分析件**的完成握手校验模式，
   CLI 冻结为：

   ```text
   python3 tools/analyze_m3_body.py --validate-completion \
     --runtime runtime \
     --run-id p1-m3-body-001-arm-a-trial-1-attempt-4 \
     --tracker-exit-code 0 \
     --tracker-final-json '<track_loop 最后一行 JSON 原文>'
   ```

   只有同时满足以下条件才退出 0 并**仅输出**
   `TRACKER_AUTO_COMPLETE_CONFIRMED`：exit code 恰为 0；final JSON 是对象且
   `run_id` 等于 acquisition ID；其 `summary` 解析为该 run 目录的
   `summary.json`；manifest 同 ID；`summary.json` 与 `metrics.final.json`
   存在；summary 的 `metrics_snapshot_present` 为 `true` 且
   `actual_duration_s >= 130.0`。其他情况非零且具名 fail closed；不得调用
   `finalize_run` 或写任何文件。操作单 §3 step 4 必须把该命令的 PASS 作为
   Implementation 报出确认词的机械来源，而非人工复述。
5. 为 C4 的每个 AND 条件至少补一条反例：非零 exit、畸形/非对象 JSON、错
   run ID、错/逃逸 summary path、manifest 错 ID、两终结文件各缺一项、
   `metrics_snapshot_present != true`、duration `<130.0`；另证 PASS 路径零写入。
   将 `AttemptIdentityBindingTests` 移到唯一的末尾 `unittest.main()` 之前。
6. 更新实现证据，明确列出 round-2 路径、focused/full 结果和零 Play/ID/指标。
   再次停在候选，不直接送 Review、不请求 GO。

#### D. §4.3.1 停点与写入归因

1. 条件 3 无新增 Unity 失败，成立。条件 1 因操作接口矛盾未冻结；条件 2
   虽然现有测试执行通过，但缺少 C6 强制覆盖；条件 4 的未验证风险也未完整
   入证据，故三者不成立。本轮停点 **`NOT_CONFIRMED`**，不得交独立 Review。
2. 按 workflow 条件 5，Acceptance 已运行宽区间
   `check_role_writes --role implementation --base e438b97`。原始非零只有四条：
   `docs/authorizations.md` 归因于 Chore/Acceptance 授权批次
   `78fdacb`/`09e1207`/`c55f4ad`；proposal 归因于 `fc08890` 至 `c53a075`
   的 Acceptance verdict 批次；Review 文件只由独立 Review `9dac378` 写入；
   Unity log 归因于 Acceptance 的 `34c1ec1`/`9fb9b49`/`72916f6`/
   `6d293f5`/`e8c2ca0`/`68f35a2`/`c53a075`。四条均非本实现写入。
3. 以最后一个 Acceptance 基线 `c53a075` 运行精确实现审计则对六路径 PASS。
   故本轮没有写入越权；停点失败完全来自 B1–B5 的内容缺口。

### Acceptance round 31 — 2026-08-10（revision 11 round-2 候选复核）

Decision: **REVISION_REQUESTED — R11_ROUND_3 /
STOP_POINT_NOT_CONFIRMED**

#### A. 已通过项

1. Round 30 C1、C2 的 ID 主体已落地：操作单 §3 step 5、analyzer 模块说明与
   两处 Usage 均使用 attempt-4 acquisition ID；§1 已分开 canonical slots 与
   acquisition IDs，§4 只替换 `--run-id`。旧 A1 ID 不再出现在可执行的分析或
   compare 示例中。
2. C3 predecessor 门成立。`_check_a1_predecessor_hold()` 在任何收集/写入前
   检查真实 hold；Acceptance 现场确认其直接文件恰为 `frames.jsonl`、
   `manifest.json`，SHA-256 分别为 `8f9f355186cf06d83dd30956552b9687cd4992454090f89ecc307f2b986016b5`
   与 `e5caa98276a48413f3d78d34228d8c41d8ad0b9e8b438c070d4925c4f14e8a65`，
   attempt-4 目录不存在。缺目录/增减文件/两种字节 mutation 均具名 fail closed，
   且测试断言零分析输入和零 analysis 写入。
3. C4/C5 完成握手成立：`--validate-completion` 逐项实施 exit 0、final JSON、
   同 acquisition ID/summary path、manifest、两终结文件、snapshot=true 与
   duration>=130 的 AND 门；PASS 只返回 `TRACKER_AUTO_COMPLETE_CONFIRMED`，
   失败具名且不调用 finalize、不写文件。单一末尾 main guard 也已恢复。
4. Acceptance 复跑 focused 两入口各 **50/50**、全套 **510/510**（1 skip），
   均通过；`git diff --check` 与 `check_docs.py` 通过。候选仍为 `0ca13cb`，
   工作树事前为空，零 Play、零新采集 ID、零指标、零 finalize、零 void 分析。

#### B. 唯一阻塞项

1. **B6 — §5 仍未按 C2 分段，标题与第三种终态冲突。** 当前第三种
   `TRIAL_VOID_PROTOCOL_DEVIATION_POST_TRACKER_EARLY_EXIT` 仍与前两种一起列在
   “**tracker 启动前的具名终态**”标题和同一张表内；该行自身又写 tracker 已
   启动，下文也称其为 post-tracker。Round 30 C2 要求“把前两种 pre-tracker
   void 与第三种 post-tracker void 分段”，实现证据 J.1 也声称已经分开，但
   权威操作单并未做到。执行者按标题或按行会得到相反分类，影响 run 目录/
   acquisition ID 是否已消耗，故接口仍未冻结，不能作为可逐字执行的候选。

#### C. R11 round-3 binding rework（仅文档，逐条执行）

1. 在操作单 §5 把三种终态真正拆为两个并列段落：pre-tracker 段的标题和表格
   **只含前两种**；post-tracker 段的标题和表格**只含第三种**。前者明确 run
   目录未创建、采集 ID 未消耗；后者明确 run 目录已创建、采集 ID 已消耗，
   且保留“不 `--finalize`、不分析、不重进”的处置。三者都各消耗一次
   one-Play GO。不得改变终态名、触发条件或任何运行/指标语义。
2. 同步实现证据与状态板，使其只声称磁盘上实际完成的分段。无需修改代码或
   测试；若实现角色认为必须触及其他路径，先退回 Acceptance 重新定范围。
3. 再次停在候选；不得自行送 Review、请求 GO 或进入 Play。

#### D. §4.3.1 停点与写入归因

1. 条件 2、3 成立；条件 1 因 B6 的协议分类歧义仍未冻结，条件 4 的未验证
   风险也必须保留，故停点 **`NOT_CONFIRMED`**，不得交独立 Review。
2. 精确 round-2 区间 `9e7a898..0ca13cb` 为六个实现角色允许路径；
   `python3 tools/check_role_writes.py --role implementation --base 9e7a898`
   通过。
3. 按“上一通过候选”`e438b97` 运行累计审计，原始非零仍只有四条：
   `docs/authorizations.md` 归因于 `78fdacb`/`09e1207`/`c55f4ad`；proposal
   归因于 `fc08890`、`b034a23`、`34c1ec1`、`1abd221`、`19c5fbd`、
   `c96cdc6`、`9fb9b49`、`e8c2ca0`、`f9701a6`、`c55f4ad`、`68f35a2`、
   `c53a075`、`9e7a898` 的 Acceptance 批次；Review 文件只由独立 Review
   `9dac378` 写入；Unity log 归因于 Acceptance 的 `34c1ec1`、`9fb9b49`、
   `72916f6`、`6d293f5`、`e8c2ca0`、`68f35a2`、`c53a075`。四条均已归因，
   没有实现角色越权；本轮停点失败仅来自 B6。

### Acceptance round 32 — 2026-08-10（revision 11 round-3 候选复核）

Decision: **ACCEPTED — R11_STABLE_CANDIDATE /
STOP_POINT_CONFIRMED_REVIEW_PENDING**

#### A. 接受理由

1. Round 31 B6 已逐字关闭。操作单 §5 现有两个并列段落和两张独立表：
   pre-tracker 表只含暂停窗与 startup failure，并明确 run 目录未创建、采集 ID
   未消耗；post-tracker 表只含 early-exit，并明确 run 目录已创建、采集 ID 已
   消耗及“不 `--finalize`、不分析、不重进”。三者各消耗一次 one-Play GO。
2. 精确 round-3 区间 `daefe35..7156f7e` 只有四个文档路径，零 `tools/`、
   `tests/`、controller、Assets/config/model/scenario；终态名、触发条件、运行
   与指标语义均未改变。实现证据已更正 round-2 overclaim 并准确指向 §K。
3. Round 30 C1–C5 继续成立。Acceptance 在 `7156f7e` 复跑 focused **50/50**、
   全套 **510/510**（1 skip）；真实 attempt-3 hold 仍恰有两文件，SHA-256 为
   `8f9f3551…16b5` / `e5caa982…8a65`，attempt-4 目录仍不存在；
   `git diff --check` 与 `check_docs.py` 通过。

#### B. Binding disposition

1. Revision 11 的接口与范围在 implementation candidate `7156f7e` 冻结。
   独立 Review 必须从上一通过候选 `e438b97` 审查累计 r11 delta，并核对
   attempt-4 acquisition→canonical A1、旧/其他 attempt 拒绝、真实 predecessor
   字节门、完成握手 AND 门、§5 pre/post 分类及对应机械反例。
2. 本裁定只确认 workflow §4.3.1 停点，**不是独立复核 verdict，也不授权
   Play**。Review 给出通过 verdict 且用户另行逐字授权一次新 Play 之前，
   attempt 4、任何其他 trial、分析或指标发布都保持冻结。
3. Review 若要求返工，必须回到同一停点；不得在 Review 期间推进依赖此结果的
   后续实现。

#### C. §4.3.1 停点与写入归因

1. 条件 1–4 全部成立：接口/范围冻结，测试相称且通过，无新增 Unity 失败，
   候选/证据/状态和未验证风险已更新。因此停点为 **`CONFIRMED`**，下一角色
   唯一为独立 Review。
2. 精确 round-3 审计：
   `python3 tools/check_role_writes.py --role implementation --base daefe35`
   对四个允许文档路径通过。
3. 按上一通过候选 `e438b97` 的累计审计仍只报四个非实现路径，均完成归因：
   `docs/authorizations.md` 为 `78fdacb`/`09e1207`/`c55f4ad`；proposal 为
   `fc08890`、`b034a23`、`34c1ec1`、`1abd221`、`19c5fbd`、`c96cdc6`、
   `9fb9b49`、`e8c2ca0`、`f9701a6`、`c55f4ad`、`68f35a2`、`c53a075`、
   `9e7a898`、`daefe35` 的 Acceptance 批次；Review 文件只由独立 Review
   `9dac378` 写入；Unity log 为 Acceptance 的 `34c1ec1`、`9fb9b49`、
   `72916f6`、`6d293f5`、`e8c2ca0`、`68f35a2`、`c53a075`。无路径无法归因，
   条件 5 成立。

### Acceptance round 33 — 2026-08-10（Review round 5 归因与 revision 11 round 4）

Decision: **REVISION_REQUESTED — REVIEW_R5_F3_ATTRIBUTED /
R11_ROUND_4_STOP_POINT_REWORK**

#### A. Review verdict 归因

1. Acceptance 采信独立 Review round 5 对 `7156f7e` 的
   **`REWORK_REQUIRED`**。累计 `e438b97..7156f7e` 的路径归因、受保护
   基础设施与 `tools/check_track_env.py` 字节不变、两入口 focused
   50/50、preflight 36/36、full 510 和四项新门的 `CONFIRMED`
   结论全部保留；本轮不重开其已通过的实现语义。
2. F3 归因给 Implementation 的冻结操作单：§2 仍把已执行的
   attempt-1/1b 移动写成下一次待执行动作，核对已不存在的
   shared 源件，并声称旧 canonical A1 ID 将被未来创建；这与
   §1/§5 及已发布的 `run_id_void_consumed` 相反。操作者逐字执行
   必会在 Play 前停摆或得到错误的 ID 消耗结论，故 workflow
   §4.3.1 条件 1 不成立。
3. Round 32 的停点确认据此撤回；当前状态为
   **`REVISION_REQUESTED_R11_ROUND_4_STOP_POINT_NOT_CONFIRMED`**。这不是
   独立 Review PASS，也不释放 GO、Play、acquisition ID、分析或指标。

#### B. R11 round-4 binding rework（文档窄范围，逐条执行）

1. 把操作单 §2.1 与 §2.2 像现有 §2.3/§2.4 一样明确标成
   **已执行的历史保全记录**。保留已记录的 source→hold、计数/
   SHA 和零删除/零覆盖/零分析结论，但删除任何“新 GO 后再执行
   这些移动”的现在时指令。不得真正移动、删除、覆盖或重算
   任何现场。
2. §2.2 对旧 `p1-m3-body-001-arm-a-trial-1` 的文字必须与
   §1/§2.4/§5 对齐：attempt 1 保全当时它尚未被消耗，但它已在
   attempt 3 创建、消耗并移入具名 hold；当前与未来均不得再作为
   acquisition ID 或目录被创建。唯一 A1 acquisition ID 仍是
   `p1-m3-body-001-arm-a-trial-1-attempt-4`。
3. 在历史记录后新建一个**仅面向 attempt 4 的 Play 前只读状态
   核对**，不执行移动或清理。核对必须逐项要求：
   `runtime/body_command.json`、`gimbal_command.json`、
   `tracking_observation.json`、`metrics.json`、`m3_body_truth.jsonl`
   和 `scenario_config.json` 全部不存在；`runtime/frames/` 存在且
   为空；1b diagnostic 与 attempt-1/2/3 四组 hold 按既有证据的
   路径、计数/行数与 SHA 完好；无 active release/qualification/scouting
   标记；`runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4/`
   不存在。任一项不符即停止并回 Acceptance，禁止就地修正后继续。
4. §3 step 5 的 `--verify` 说明与已发布实现对齐：A1 verify 只读
   attempt-4 run 目录**与** run 外的 attempt-3 predecessor hold，
   并与存档逐字节核对；不得继续声称它“只读 run 目录”。这只修
   文字，不改 predecessor 门、不解析 void 内容、不计算 void 指标。
5. §6 revision-10 的历史句改成有时间边界的记录：它在 revision 10
   完成时尚未创建，但后来已被 attempt 3 创建/消耗并移入 hold。
   不得让该历史句与当前 §1/§2.4/§5 相反。
6. 更新实现证据与状态板，准确列出 F3 闭合位置、文档检查结果和
   零 Play/零 ID/零分析/零指标。本轮强制路径只是操作单、实现
   证据与状态板；零 `tools/`、零 `tests/`、零 controller/
   Assets/config/model/scenario。若必须触及其他路径，先退回
   Acceptance，不得自行扩围。

#### C. Review notes 的处置边界

1. N19 与 N23 是与 F3 同文件、同类的已知文字矛盾，分别由
   §B.4/§B.5 强制闭合。
2. N17/N18/N20/N21/N22 保留为非阻断注记；本文档返工不授权
   添加测试、改错误契约或放宽 predecessor 两文件集合。N22 的
   隐藏文件风险由 Acceptance 在申请下一次 GO 前再做现场只读核对；
   本轮不改门语义。
3. N24 的基线指针只能在新候选获得独立 Review PASS 并有确切
   commit 后由 Acceptance 更新。当前累计返工/复核基线仍为上一通过
   候选 `e438b97`；Implementation 不得预猜未来 PASS 哈希。

#### D. §4.3.1 同一停点

1. 固定实现/测试门的 Review `CONFIRMED` 结论保留，但接口因 F3
   未冻结，条件 1 失败；修复候选必须回到同一强制停点。
2. Implementation 交付新候选后，Acceptance 重跑
   `python3 tools/check_role_writes.py --role implementation --base e438b97`
   并对全部非实现路径完成累计归因；同时以本 Acceptance 交接提交
   为 exact rework base 核对窄范围。两个审计结果都写入新停点记录。
3. 新停点经 Acceptance 确认后只能返回独立 Review round 6。在其 PASS
   且用户另行逐字授权 one-Play GO 之前，attempt 4、其他 trial、
   分析与指标全部保持冻结。

### Acceptance round 34 — 2026-08-10（revision 11 round-4 候选复核）

Decision: **ACCEPTED — R11_ROUND_4_STABLE_CANDIDATE /
STOP_POINT_CONFIRMED_REVIEW_ROUND_6_PENDING**

#### A. Round 33 §B 逐条核验

1. **B1/B2 通过。** 操作单 §2.1/§2.2 均明标“已执行”且以过去时
   记录 source→hold、计数/SHA 和零删除/零覆盖/零分析；不再指令新 GO
   后重复移动。§2.2 明确旧 canonical A1 只在 attempt 1 时尚未消耗，
   attempt 3 已将它创建/消耗并移入 hold；当前与未来均禁止再
   创建。唯一 A1 acquisition ID 仍为 `...-attempt-4`。
2. **B3 通过。** 新 §2.5 明确是 §2 中唯一待执行动作，且只读、零移动/
   零清理。Acceptance 独立复算：六个 shared 文件全 absent，
   `runtime/frames/` 存在且 0 项，四组 hold 计数为
   **257/93/109/257**；attempt-3 run hold 恰两文件，SHA-256 为
   `8f9f3551…16b5` / `e5caa982…8a65`；其余被钉住 SHA 也全部与
   证据 §B/§F.1/§H.1/§I.1 相等。runtime 根的八个 active marker 全
   absent，attempt-4 run 目录 absent。
3. **B4/B5 通过。** §1 与 §3 step 5 都准确声明 A1 `--verify` 只读
   attempt-4 run 和 run 外 predecessor hold，其余九个 run 仍只读自身目录；
   void 内容不解析、不计指标。§6 revision-10 句已加时间边界，
   不再声称旧 A1 当前未创建。N19/N23 因此闭合。
4. **B6 通过。** 精确 `c923b9a..6019f33` 恰四路径：操作单、实现
   证据、状态板和机械归档。零 `tools/`、零 `tests/`、零 controller/
   Assets/config/model/scenario，也零现场移动/删除/覆盖/重算。

#### B. §4.3.1 停点判定

1. **条件 1 成立：** F3 的当前/历史操作界面已分开，旧 ID 消耗和
   attempt-4 create-once 前置一致；§2.5 是唯一待执行的只读状态门。
2. **条件 2 成立：** 本轮零代码/测试变更，Review round 5 独立复跑的
   focused 50/50（两入口）、preflight 36/36（两入口）和 full 510 仍
   直接覆盖候选中未改的实现。`git diff --check` 与 `check_docs.py`
   通过。
3. **条件 3/4 成立：** 本轮零 Play/零新 ID/零分析/零指标，无新 Unity
   失败；Review round 5、候选 `6019f33`、实现证据和状态均已落盘。
   N17/N18/N20/N21/N22 继续为非阻断注记；N22 在下一次 GO 前由
   Acceptance 再做现场只读核对。N24 等 Review round 6 产生确切 PASS
   哈希后、下一次 GO 前由 Acceptance 更新；Implementation 本轮未预猜。
4. **条件 5 成立：**
   `check_role_writes --role implementation --base c923b9a` 对精确四路径
   PASS。按上一通过候选 `e438b97` 的累计审计只报四条非实现
   路径：`docs/authorizations.md` 由 `78fdacb`/`09e1207`/`c55f4ad`
   的授权代录批次写入；proposal 由 `fc08890`…`c923b9a` 的
   Acceptance 批次写入；Review 文件只由 `9dac378`/`1a6e772` 的
   独立 Review 批次写入；Unity log 只由 `34c1ec1`…`c53a075`
   的 Acceptance 批次写入。四条全部归因，无 Implementation 越权。

#### C. Binding disposition

1. Revision 11 round-4 的接口与范围在精确候选 `6019f33` 冻结；
   workflow §4.3.1 停点为 **`CONFIRMED`**。
2. 下一角色只能是独立 Review round 6，必须从上一通过候选
   `e438b97` 审查累计 `e438b97..6019f33`，重点核对 F3 和本轮实际
   触及的 N19/N23；N17/N18/N20–N22 按 round 5 保留，N24 依上段留待
   PASS 哈希。
3. 本裁定不是独立 Review PASS，也不授权 GO 或 Play。Review round 6
   PASS、N24 基线指针由 Acceptance 更新、N22 现场只读核对通过且用户
   另行逐字授权 one-Play GO 之前，attempt 4、其他 trial、分析与
   指标全部保持冻结。

### Acceptance round 35 — 2026-08-10（Review round 6 消费与条件式 GO）

Decision: **ACCEPTED — REVIEW_R6_PASS_WITH_NOTES_CONSUMED /
CONDITIONAL_GO_RECORDED_N24_PENDING**

#### A. Review verdict 与独立性

1. Acceptance 消费 round 6 对 `6019f33` 的 **`PASS_WITH_NOTES`**。
   F3/N19/N23 关闭，§2.5 九项在真实主树上全过，focused 50/50、
   preflight 36/36 的两入口与 full 510 均由 Review 重跑；
   `6019f33` 的实现代码与 `7156f7e` 字节一致。
2. Review 披露 round 6 与 round 5 为同一 Review 会话。Acceptance 判定
   **独立性成立**：该会话始终与 Implementation/Acceptance 分离，
   round 6 新建 detached worktree `...-r6`，从磁盘重读累计差异并重跑
   全部检查，未引用实现者转述且零实现写入。workflow §4.4 要求
   返工后在同一报告追加轮次，未要求每一轮更换 reviewer；本文档窄
   返工无需另开第三个 Review 会话。
3. `check_role_writes --role review --base 91ce00f` 对 Review 的三个允许
   文档路径 PASS；`check_docs.py` PASS；`6019f33..c422576` 的
   tools/tests/controller/Assets/config 差异为空。

#### B. N22 与剩余 notes

1. Acceptance 在用户本轮授权后重做 N22 现场只读核对：
   `runtime/runs/p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold/`
   直接集合**恰为两个文件**，零 `.DS_Store`/隐藏/额外项；
   `frames.jsonl` / `manifest.json` SHA-256 分别为
   `8f9f355186cf06d83dd30956552b9687cd4992454090f89ecc307f2b986016b5`
   / `e5caa98276a48413f3d78d34228d8c41d8ad0b9e8b438c070d4925c4f14e8a65`。
   **N22 的 GO 前义务已闭合。**
2. N17/N18/N20/N21 继续为下一代码批次的非阻断注记；不阻止本次
   attempt-4。旧 N12/N15 同样保留。

#### C. N24 与用户条件式 GO

1. N24 仍为唯一未闭前置：操作单 §2.0 (b) 还写
   `git diff --name-only e438b97..H`，须逐字替换为
   `git diff --name-only 6019f33..H`。这是 Review 已给出确切 PASS 哈希后的
   单行机械更新，不改代码、试验或指标语义。
2. 该行位于 `docs/evidence/`，接受角色的机械白名单不允许直接修改；
   因此交 Implementation 仅修此基线指针，同步实现证据/状态后立即回
   Acceptance。若触及任何 tools/tests/controller/Assets/config/model/
   scenario 或其他操作语义，即停下退回；按字面修改不需新一轮 Review。
3. 用户本轮原话“**核对一下，确认无误后我授权GO**”已逐字记入
   `docs/authorizations.md`，范围只限 arm A trial 1 attempt 4 恰好一次
   Play。因“确认无误后”条件尚差 N24，本授权当前为
   **`CONDITIONAL_NOT_YET_EFFECTIVE`**：不消耗 Play，不授权启动 tracker，
   不代替 §2.0 的最终 HEAD/preflight/Unity-log 顺序。

#### D. Disposition

1. 当前状态为
   **`REVIEW_R6_ACCEPTED_CONDITIONAL_GO_RECORDED_N24_PENDING`**。
2. 实现角色只交付 N24 基线指针、证据与状态，然后停止。Acceptance
   确认后把条件式 GO 改为生效并提交；在那之前不得 Play。
3. GO 生效也不等于立即进 Play。实现角色仍须在最终干净 HEAD 上完成
   §2.0 (b) 的 HEAD/空 status/`6019f33..H` 归因和 step-0 完整
   JSON 报告；Acceptance 再写 Play 前 Unity 日志。

### Acceptance round 36 — 2026-08-10（N24 闭合与条件式 GO 激活）

Decision: **ACCEPTED — N24_CLOSED / ONE_PLAY_GO_EFFECTIVE_UNCONSUMED**

#### A. N24 核对

1. Implementation 提交 `86c84bc` 把操作单 §2.0 (b) 的唯一归因基线
   从 `git diff --name-only e438b97..H` 改为
   `git diff --name-only 6019f33..H`，并准确注明 `6019f33` 是 Review
   round 6 `PASS_WITH_NOTES` 的候选、旧 `e438b97` 已过期。
2. `20ac758..86c84bc` 只触及操作单、同 work ID 实现证据和状态板三份
   文档；§2.0 四步顺序、§2.5 九项核对、§3、§4、§5 均未改变，零
   tools/tests/controller/Assets/config/model/scenario、零 Play、零采集 ID、
   零指标、零分析、零现场改动。状态板 Gate row 遗留的 `N24 pending`
   是状态合并文字，Acceptance 在本批次校正，不构成协议或实现返工。
3. `check_role_writes --role implementation --base 20ac758` PASS（3 paths）；
   `check_docs.py` 与 `git diff --check 20ac758..86c84bc` PASS。N24 **闭合**；
   round 35 §C.2 允许该字面文档修改不另开 Review，故无需 Review round 7。

#### B. GO disposition 与逐条约束

1. 用户逐字授权“**核对一下，确认无误后我授权GO**”的唯一悬置条件 N24
   已确认无误；账本中的 arm A trial 1 attempt 4 **单次 GO 现已生效、尚未
   消耗**。唯一 acquisition ID 为
   `p1-m3-body-001-arm-a-trial-1-attempt-4`；canonical slot 与全部冻结语义
   不变。
2. 生效不等于可立即进入 Play。Implementation 必须在本 Acceptance 激活
   提交后的最终干净 HEAD `H` 上，逐项报告：`git rev-parse HEAD`、空的
   `git status --porcelain`、`git diff --name-only 6019f33..H` 的完整路径
   归因，以及 §3 步骤 0 的退出码 0 与完整 `status=PASS` JSON。
3. Acceptance 收到并核对第 2 条后，必须在 Play 前把这些值写入
   `docs/unity-test-log.md`；发令时 `git diff --name-only` 必须逐字只有
   `docs/unity-test-log.md`。第 2/3 条未完成、预检非 PASS、工作树出现
   其他路径或现场九项任一失败，均不得发令并回 Acceptance。
4. 本 GO 只覆盖 attempt 4 恰好一次 Play；不覆盖重试/重进、其余九次
   Play、旧 A1 ID、重框、调参、路径/模型/场景/阈值/窗口/指标变化或
   batch 2。attempt 4 任一终态都先回 Acceptance。

#### C. Disposition

状态进入 **`GO_EFFECTIVE_UNCONSUMED_AWAITING_FINAL_PREFLIGHT`**。下一角色为
Implementation，仅交付 §2.0(b) 的最终 HEAD/clean/归因/step-0 报告后停止；
在 Acceptance 写入事前 Unity 日志并核对 sole-diff 之前不得 Play。

### Acceptance round 37 — 2026-08-12（trial 1 机器结果与归档）

Decision: **REVISION_REQUESTED — MACHINE_RESULT_PASS /
HANDSHAKE_TRANSCRIPTION_AND_RUNTIME_ARCHIVE_PENDING**

#### A. 已成立的机器结果

1. Attempt 4 的 self-contained run 有十一份文件；`summary.json` 记录
   `actual_duration_s=130.0018317103386`、`metrics_snapshot_present=true`、
   651 frame records、零 LOST/gap/reinit。`metrics.final.json`、
   `summary.json` 与 `m3_body_analysis.json` 均存在。
2. Acceptance 只读运行 `analyze_m3_body.py --verify` PASS：receipt 把
   acquisition attempt 4 唯一映射 canonical A1，frame/truth 651/1027、
   init frame/box、scenario/margin/body/re-anchor/tracker/predecessor hashes
   全部成立。`h1.full_loop_c_geom=0.5784550773737355`、disposition
   `WITHIN_RANGE`，窗口 `C_track|geom=1.0`；故数值落在 BC-BODY1-15 唯一
   释放区间 `[0.5645,0.95)`，不是 `GEOMETRY_MODEL_REJECTED` 或
   `SCENE_DEGENERATE`。
3. Run 内 frame 31/32 的 simulation time 为 `6.381126403808594` /
   `6.5816426277160645`，中间存在启动墙钟间隔，机械支持暂停边界位于
   `[2,10)`；接受记录仍如实披露用户当时只说“已暂停”，本会话没有精确
   displayed-time 原话。

#### B. 尚不能补推的 live evidence

1. 冻结 §3.4 要求 Implementation 以实际 tracker 自然退出码、实际 stdout
   最后一行 JSON 运行 `--validate-completion`，只有退出 0 且输出逐字
   `TRACKER_AUTO_COMPLETE_CONFIRMED` 后用户才退出 Play。当前磁盘/权威日志
   未转录这三项，也未转录用户退出后的 Console 报告。
2. `summary.json`/`metrics.final.json` 的存在与 130 秒值证明 durable machine
   条件，但 `run_tracker` 的 `finally` 对若干非零退出同样会 finalize；因此
   Acceptance 不得从文件存在反推实际退出码，更不得用合成 final JSON
   事后制造确认词。
3. 所以本轮不把 A1 计成有效 trial，不释放其余九次 Play，也不判定 void；
   当前是 **`MACHINE_RESULT_PASS_ARCHIVED_PENDING_HANDSHAKE_TRANSCRIPTION`**。

#### C. Binding archive/return 条款

1. 用户原话“**查看结果，并把trail1归档**”授权非破坏归档；不授权删除、
   覆盖、重跑或改变指标。正式 attempt-4 run 目录十一份文件逐字不动。
2. Implementation 仅将 active `runtime/frames/`、shared truth/metrics 与三份
   publication 移入
   `runtime/test-results/p1-m3-body-001-arm-a-trial-1-attempt-4-post-run/`，
   记录移动前后计数/全 SHA，重建空 `runtime/frames/`；不得移动/改写 run
   目录或 predecessor hold。移动后 `--verify` 必须仍逐字 PASS。
3. Implementation 同批从实际会话输出逐字补录 tracker exit code、最后一行
   JSON、validator exit/output 和用户 Console 报告；若任何项不可恢复，写明
   `UNAVAILABLE`，不得推测。随后停止并回 Acceptance。
4. 本批零代码/测试/config/scenario/model/协议变化，零新 Play/ID/指标重算；
   不需新 Review。Acceptance 收到真实转录后才作终局 `ACCEPTED` 或
   `REJECTED` 归因并决定是否可申请下一次 GO。

### Acceptance round 38 — 2026-08-12（trial 1 终局归因）

Decision: **ACCEPTED — A1_VALID_TRIAL_ARCHIVED /
REMAINING_NINE_PROTOCOL_ELIGIBLE_AWAITING_USER_GO**

#### A. Round 37 返工逐条核对

1. `4804b41..43a8269` 只改同 work ID 实现证据与状态板；
   `check_role_writes --role implementation --base 4804b41`、`check_docs.py`
   与 `git diff --check` PASS。零 code/test/config/scenario/model/protocol
   修改，按 round 37 §C.4 不需新 Review。
2. Active slots 已移动不删除：archive frames 257 项，shared truth/metrics/
   三份 publication 的行数、字节与 SHA-256 前后相等；active frames 为空，
   五份 shared root 文件均 absent。正式 run 十一文件与 predecessor hold
   两文件的逐文件哈希保持 round 37 记录值。
3. Acceptance 在归档后独立重跑 `--verify`，逐字得到
   `verified=true`、`WITHIN_RANGE`、`C_geom=0.5784550773737355` 与窗口
   `C_track|geom=1.0`；以返工转录的实际 exit `0` 和最后一行 JSON 重跑
   validator，也逐字得到 `TRACKER_AUTO_COMPLETE_CONFIRMED`。
4. Live 四项全部可恢复：tracker 自然 exit 0、final JSON、Play 退出前
   validator exit/output，以及用户 Console 原话“已经退出，没有报错”。
   `tifffile` 噪声被如实披露，不改变 stdout 最后一行 JSON 身份。

#### B. 暂停窗归因

1. 用户当时原话“暂停5S左右”不是 HUD displayed-time 的精确转录；但 run
   的不可变帧边界直接给出 `6.381126`，下一帧为 `6.581643`，两者都在
   `[2,10)` 且跨越启动墙钟间隔。该证据比口头约数更直接地证明本次门 1。
2. Acceptance 接受该已完成 run 的直接 simulation-time 证据，**不修改也不
   放宽未来规则**：后续每次 Play 仍须在暂停时报告精确 displayed time；
   不得把“左右”作为新惯例。

#### C. Binding disposition

1. Attempt 4 正式计为 canonical `p1-m3-body-001-arm-a-trial-1`，状态
   **`A1_VALID_TRIAL_ARCHIVED`**。Attempt 1/2/3 的三个 void disposition、
   工件与排除义务全部保留，不计入五个 arm-A trials。
2. BC-BODY1-15 首跑门成立：`0.5784550773737355` 位于
   `[0.5645,0.95)`；因此不是 `GEOMETRY_MODEL_REJECTED` 或
   `SCENE_DEGENERATE`，剩余九个 trial 进入**协议可申请**状态。
3. “可申请”不等于 GO。用户 2026-08-12 的归档指令明确未授权其余九次
   Play；任何下一次 Play 必须点名唯一 trial/acquisition ID 并获得新的逐字
   用户 GO，随后重新执行该次适用的 pre-Play 记录、现场隔离和 sole-diff 门。
4. A1 结果只作为第一个 hold-arm 样本；十个 trial 齐备前不运行/发布正式
   H1/H2 compare，不据此调整参数、阈值、窗口、载体或采集数量。

### Acceptance round 39 — 2026-08-13（trial 2 GO 入账与 revision 12 准备）

触发：用户逐字 GO「授权执行恰好一次 arm A trial 2（run ID
p1-m3-body-001-arm-a-trial-2）…其余 8 次 Play、重试、重进与任何调参均
未授权」（账本 2026-08-13 `P1-M3-BODY-001` 条目）。

#### A. 采集 ID 机械核验（本轮实跑，零写入）

`canonical_trial_id('p1-m3-body-001-arm-a-trial-2')` 返回同名 canonical
slot；`_expected_policy()` 返回 `hold`（= 臂 A）；
`expected_acquisition_ids('a')[1]` 与之逐字相等。用户给出的 run ID 因此
**恰为冻结 ID 表中的 A2**，无需任何后缀或映射。`_check_a1_predecessor_hold`
只在 `run_id == A1_ACQUISITION_RUN_ID` 时触发（`analyze_m3_body.py:799`），
故 A2 的分析与 `--verify` 只读自身 run 目录。

#### B. 操作单 revision 12（有效槽位轮换 + 两条记录型条款）

撰写权依据：账本 2026-08-12 COORD-007 条目决策点 3「Rev-12 作者 = 接受
角色…届时 A2 仍需用户单独 GO」，`docs/evidence/*` 已在 R4 同批进入本角色
白名单。落点：§1 新增 A2 钉住行；§2.5 转历史、新增 §2.6（trial 2 只读
Play 前核对，含 A1 run 目录/归档的只读保全）；§3 新增步骤 0′（解释器逐字
相等须落盘）与门 1 记录型条款（`reported_sim_t` 必须由保留帧机械导出并
在启动 tracker 前落盘）；§3 步骤 4/5、§4 CLI 的 `--run-id` 换为 A2；
§5 标注首跑三分支已由 A1 放电；§6 新增边界声明。**零阈值、零指标、零
CLI 其它参数、零代码/测试改动。**

#### C. 越界声明 —— 用户句中两项**不在**已获授权范围内

用户写「暂停窗/解释器断言…按 COORD-007 已获授权范围准备」。据实核对：
若"断言"指 COORD-007 §4.1／§4.2 定义的**机器断言**，则该二项是 **R10**
（`tools/trial.py` 第 (3)(4) 项），而同一 2026-08-12 账本条目把
「R10/R11 开工」逐字列为**明确未授权**（需另行点名授权新 work ID）；
且二者均为代码，写代码超出接受角色边界，其中 `preflight_reanchor_env.py`
属 Play 治理门，触碰即依 workflow §4.4 R3 条件 (3) 强制加开闭环复核轮
（会把 trial 2 推迟到一整轮实现＋复核之后）。故本轮**只交付记录型条款**，
并在 §3 步骤 2 与 §6 逐字披露残留缺口：保留帧导出的 `reported_sim_t` 是
暂停真实时刻的**下界**（attempt 4 实测均值约 `0.206 s/帧`），
「末帧 `9.97` 通过而真实暂停 `10.03`」仍可逐字重演。**本轮不调整
`[2.000000, 10.000000)`**——BC-BODY1-15 (d) 禁止在此时改阈值。

#### D. 现场实测（2026-08-13，只读，`git status --porcelain` 为空）

六个 shared 文件均不存在；`runtime/frames/` 0 项；四处 hold 帧计数
257/93/109/257 与 §2.5 原表相符；A1 run 目录 11 份文件且 `--verify` 退出码
0、逐字复现 `WITHIN_RANGE / 0.5784550773737355 / 1.0`；post-run 归档 6 项；
`runtime/runs/p1-m3-body-001-arm-a-trial-2/` 不存在。**该实测不替代**发令前
由 Implementation 执行并落盘的 §2.6 核对。

#### E. 未释放事项

本轮**不**释放：其余 8 次 Play、任何重试/重进、任何调参、H1/H2 compare、
R10/R11/R12。§2.0 四步顺序中，(a) 已完成（GO 入账并提交）；(b) 由
Implementation 在最终干净 HEAD 上执行并报告；(c) 由 Acceptance 在用户进
Play 前写入 `docs/unity-test-log.md`；(d) 发令时工作树只允许该一份未提交
差异。**(b)/(c)/(d) 未完成前不得进 Play。**

#### F. 基线 delta 的 inert 归因（本轮新发现，pre-Play 门）

发令前核对 §2.0 step (b) 的基线归因时发现：`git diff --name-only
6019f33..HEAD`（`6019f33` = Review round 6 通过候选）在 **PLAY_GOVERNING
上非空**，恰六个路径，全部来自 COORD-007 批次：`tools/check_docs.py`、
`tools/check_role_writes.py`、`tools/rotate_docs.py`（R9 删除）与三个对应
`tests/test_*`。workflow §4.5 要求发令时工作树等于被复核通过的候选或
**仅含白名单文档差异**，而这六个不是文档——若不处置，trial 2 的 Unity
证据与复核证据将不对应同一代码。

**归因：`INERT_DELTA_MEASUREMENT_PATHS_BYTE_IDENTICAL`**，采
`P1-DETECT-001` qual-3 已用过的 inert-delta 归因形式。两条机械依据（本轮
实跑）：

1. **测量侧逐字节相同**：`git diff --name-only 6019f33..HEAD --
   controller/ Assets/ config/ ProjectSettings/ Packages/packages-lock.json
   tools/analyze_m3_body.py tools/preflight_reanchor_env.py` **输出为空**。
   即 tracker、planner、estimator、评估器、场景/模型/re-anchor 配置、
   分析器与预检工具全部与被复核通过的候选逐字节相同。
2. **无导入路径**：在 `controller/`、`Assets/`、`analyze_m3_body.py`、
   `preflight_reanchor_env.py` 中检索 `import`/`from` 引用上述三个模块，
   **零命中**。六个变更文件是文档自检工具及其测试，不参与任何采集、
   控制、指标或分析路径。

§4.5 的立法目的是"Unity 证据与复核证据对应同一代码"；产出测量的代码
**确为**被复核通过的代码，逐字节可证，故本 delta 判为 inert，**不阻断**
trial 2 的一次 Play。

**本归因不discharge 的义务**：这六个路径**仍欠**独立复核的逐文件 diff
覆盖，该义务按 COORD-007 R5 挂在 `COORD-007` 交接行由下一轮复核承担，
不因本次 inert 归因而消灭。发令时工作树的**唯一**未提交差异仍必须是
`docs/unity-test-log.md`（§2.0 step (d) 不放宽）。若在 Play 之前
`controller/`、`Assets/`、`config/`、`analyze_m3_body.py` 或
`preflight_reanchor_env.py` 出现**任何**字节改动，本归因立即失效，
必须停下并回 Acceptance 重判。

#### G. 环境诊断与全套测试现状（COORD-005 诊断通道，零 ID/配额）

**明确标注为诊断**：以下为接受角色在 HEAD `643bc2f`（干净树）上的只读
运行，**不进证据链、不作任何门判据**，也**不替代** §2.0 step (b) 由
Implementation 执行并报告的预检。

1. **冻结预检通过**：`.venv-yoloe/bin/python tools/preflight_reanchor_env.py
   --reanchor-config config/detector-reanchor.models.json` 退出码 **0**、
   `status = "PASS"`；`interpreter.executable` 逐字为
   `~/TetheredDroneTracking/.venv-yoloe/bin/python`，与 §1 冻结的
   唯一合法入口一致。**trial 2 不因环境受阻**，且 §3 步骤 0′ 的记录型条款
   已证实可执行（该字段确实存在且取值符合预期）。运行前后
   `git status --porcelain` 均为空。
2. **全套测试如实记录**：`.venv-yoloe/bin/python -m unittest discover -s
   tests` = **518 ran，1 failure + 1 error + 1 skipped**。两条不通过同源：
   `test_trackers…test_pinned_opencv_csrt_initializes_and_updates` 与
   `test_track_loop…test_cli_runs_pinned_csrt_to_a_versioned_summary`，
   根因均为 `installed cv2 does not expose TrackerCSRT_create`——当前
   `.venv-yoloe` 的 cv2 为 `5.0.0`（**与 NanoTrack spec 的
   `opencv.tested_version = 5.0.0` 相等**，故预检通过），但未装
   `opencv-contrib` 的 CSRT 组件。
   **与 trial 2 无关**：CSRT 是 `P1-TRACK-001` 的旧基线追踪器；本批次
   冻结追踪器是 `nanotrack-v2`，`hasattr(cv2,'TrackerNano_create')` 为
   `True`。二者不在 trial 2 的采集/控制/指标路径上。
   **披露而非掩盖**：该两条在本轮之前即存在（本轮零 `controller/`、
   零 `tools/`、零 `tests/` 改动，见 §F 第 1 条的逐字节相同证明），
   登记为 R10/R11 批次证据设计的输入，与复核轮 3 N16 的未跟踪
   `runtime/` 资产依赖并列。

### Acceptance round 40 — 2026-08-13（PLAY_GOVERNING 末句裁定 + §2.0 (c) 发令记录）

触发：Implementation 在 §2.0 step (b) 报告中把一项定义歧义**退回本角色**
（`docs/evidence/P1-M3-BODY-001-arm-a-trial-2.md` §A.3/§E.1）：PLAY_GOVERNING
子集实测 **7** 条，与接受轮 39 §F 的「恰六个路径」不符。实现角色未自行裁定，
处理正确——这正是 AGENTS.md 要求的「歧义退回接受角色」。

#### A. 裁定：workflow §4.4 末句取**读法 1**（操作单文件本身入集）

`docs/proposals/COORD-007-process-overhead-reduction.md` 第一批 R1 是该定义的
立法原文，三条依据一致指向读法 1：

1. **立法理由逐字指向文件本身**：R1 写「后三项是对抗性检验的修正：…
   **操作单则是人手执行的实验协议本身**（F3 就是"冻结操作单逐字执行会停摆"，
   而它零代码字节）」。入集理由恰恰是「零代码字节也能改变实验」，指的是
   操作单这份文档，不是它点名的其它工件。
2. **同条「省」栏的诚实注自证**：「不是 8 轮——`7156f7e` 与 `6019f33` 都是
   操作单改版，**修好口径后仍会开 2 轮**」。作者明确预期操作单改版本身构成
   开轮资格；读法 2 下这两轮不具资格，该句将自相矛盾。
3. **读法 2 使条款空转**：§1 钉住表点名的工件是 `config/scenario.default.json`
   （已被 `config/` 覆盖）与 `docs/evidence/P1-M3-BODY-001-scene-body-margin.json`。
   使条款失去独立效力的读法不采。

**裁定**：`docs/evidence/P1-M3-BODY-001-1c-preflight.md` 是本 work item 的
PLAY_GOVERNING 成员。该裁定只解释既有定义，不修改 workflow 正文，不新增门。

#### B. 计数更正：接受轮 39 §F 的「恰六个路径」**错误**，实测 7 条

本轮 Acceptance 自行复算（HEAD `6276f63`，工作树空）：

- `git diff --name-only 6019f33..HEAD` = **27** 个路径（实现角色测量时点为
  26；第 27 条是其后提交的 trial 2 证据文件本身，符合其 §A.6 的预判）。
- 目录部分子集 = 6 条 COORD-007 文档自检工具/测试；加操作单一条 = **7**。
- 测量侧（`controller/`、`Assets/`、`config/`、`ProjectSettings/`、
  `Packages/packages-lock.json`、`analyze_m3_body.py`、
  `preflight_reanchor_env.py`）diff **仍为空**——§F 的 inert 前提在本轮复验成立。

Implementation §A.3 的实测**成立并被采纳**；round 39 §F 的计数句作废，操作单
§2.0 (b) 注同批就地更正（AGENTS.md：失效文字同批修正，不留给下一个角色）。
第 7 条的归因：**revision 12 本身**——接受角色按账本 2026-08-12 COORD-007
决策点 3 与 2026-08-13 GO 撰写，即本次 Play 正在执行的指令，不是未归因漂移。

#### C. 第 7 条**不并入** §F 的 inert 类，单独定名处置

§F 的 `INERT_DELTA_MEASUREMENT_PATHS_BYTE_IDENTICAL` 依据两条**代码论证**
（测量侧逐字节相同、零导入路径），对操作单**不适用**：操作单的字节确实变了，
而它恰是「零代码字节也能改变实验」的那一类。故单独定名：

**`RUNBOOK_DELTA_AUTHORED_UNDER_GO_NO_SEMANTIC_CHANGE_REVIEW_DEBT_REGISTERED`**

依据（1–3 为本轮 Acceptance 亲自机械复算，只读，主工作树零改动）：

1. **CLI 逐行比对**：`6019f33` 版与 HEAD 版的 §4 tracker CLI 代码块各 **19 行**，
   **恰 1 行不同** —— `--run-id`（A1 采集 ID → `p1-m3-body-001-arm-a-trial-2`）。
   其余 18 个参数逐字节相同。
2. **冻结值零丢失**：两版做数值/哈希 token 多重集比较，旧版每个 token 在新版
   计数不减；**唯一下降者是标题里的引用编号 `29`**（`revision 11，Acceptance
   round 29 返工后` → `revision 12，arm A trial 2 采集轮换`），非冻结值。
   暂停窗 `[2.000000, 10.000000)`、冻结初始框四个分数与 `(177,195,77,73)`、
   `212.9706`、`130.0`、`62.5`/`31.25`、五次/臂与全部 SHA-256 逐字保留。
3. **新增条款只增不减**：§3 步骤 0′ 与门 1 记录型条款只**新增落盘义务与
   fail-closed 停条件**，不放宽任何门；门 1 的 `reported_sim_t` 口径（保留帧中
   最大 `simulation_time_s`）是 round 25 的既有括注，本次由散文变为必须落盘，
   方向是收紧。风险方向单调：加停条件不可能让本该失败的 run 通过。
4. **唯一实质动作（槽位轮换）已被生产代码机械排除风险**：round 39 §A 以真实
   `canonical_trial_id()`/`_expected_policy()`/`expected_acquisition_ids('a')[1]`
   确认 A2；§2.6 第 7 项 A2 run 目录不存在（本轮 Acceptance 复现）。Review
   round 5 的阻断 F3（操作单指向**已消耗**的 ID）正属这一类，已被机械核对排除。
5. **规则面**：AGENTS.md「复核强制停点」与 workflow §4.3.1 末段——纯文档、
   不改行为语义的修订不单独触发停点，并入下一停点。§4.4 的 PLAY_GOVERNING
   非空是**开轮资格（必要条件）**，不是「必须开轮」，更不是 Play 的阻断条件；
   把它读成强制开轮会与 R1 提案自述的目的（省约 6 轮）直接相反。§4.5 的
   立法目的（「Unity 证据与复核证据对应同一代码」）由测量侧逐字节相同满足。
6. **先例，据实标注其时间边界**：attempt 4 发令时 `6019f33..HEAD` 的 8 条路径
   里**就含本操作单**，接受轮 36 释放且未开复核轮（`docs/unity-test-log.md`
   attempt 4 记录）。该先例发生于 2026-08-10，**早于 R1 于 2026-08-12 生效**，
   故只作旁证，不作本裁定的依据。

**据实披露的角色张力**：revision 12 由接受角色撰写（用户 2026-08-12 授权），
本裁定又由接受角色作出。缓解只有三条，不掩盖：裁定所依赖的事实全部可由他人
逐条重算；**复核债务登记而非消灭**；用户可随时推翻本裁定改为先开复核轮。

**不 discharge 的义务**：revision 12 的逐文件独立复核**仍欠**，与 §F 六条一并
挂在下一轮复核（COORD-007 交接行，R5 通道）。本轮不代签任何复核。

#### D. 本轮新增的两条执行条款（binding，逐条可核对）

1. **BC-BODY1-21**：(c) 记录写入后至 Play 结束期间，**任何人不得再改
   `docs/evidence/P1-M3-BODY-001-1c-preflight.md`**。该文件已被裁定为
   PLAY_GOVERNING 成员，改动即使 (c) 记录的 HEAD 失效，必须停下重取 (c)。
2. **BC-BODY1-22**：Play 期间发现操作单文字有歧义或缺陷时，唯一合法动作是
   **fail closed 回 Acceptance**，不得就地改操作单后继续（revision 12 未经
   独立复核，就地修补等于把未复核文本变成当场协议）。

#### E. §2.0 (c) 已执行；(a)/(b)/(d) 状态

- **(a)** GO 已逐字入账并提交（账本 2026-08-13 `P1-M3-BODY-001` 条目）✓
- **(b)** Implementation 已在干净 HEAD 报告完毕，本轮唯一开放项即 §A/§B 已裁定 ✓
- **(c)** 本轮由 Acceptance 写入 `docs/unity-test-log.md`
  （`### P1-M3-BODY-001 arm A trial 2 — 2026-08-13 — PRE_PLAY_RELEASED`），
  HEAD 与 `git status --porcelain` 在写入时点现取，未复制实现角色测量时点的值 ✓
- **(d)** 发令时刻工作树只允许 `docs/unity-test-log.md` 一份未提交差异；本轮
  Acceptance 批次（本节 + 操作单更正 + 状态板）在 (c) 之前提交 ✓

**Acceptance 独立复现的现场事实**（只读，命令前后 `git status --porcelain` 均空）：
六个 shared 文件均不存在；`runtime/frames/` 0 项；四处 hold 257/93/109/257；
A1 run 目录 11 份文件；post-run 归档 6 项且 `frames/` 257 项；八个具名活动标记
全不存在；`runtime/runs/p1-m3-body-001-arm-a-trial-2/` 不存在。步骤 0 预检
**退出码 0、`status=PASS`**，stdout **4955 字节**、SHA-256
`f5529527666d477d29519c211a661247125120a5c89b775301648bd54be54931`，其 JSON 与
实现角色证据所录**深度相等**；A1 `--verify` 退出 0 并逐字复现
`WITHIN_RANGE / 0.5784550773737355 / 1.0`。

#### F. 未释放事项（与 round 39 §E 相同，逐字重申）

本轮**不**释放：其余 8 次 Play、任何重试/重进、任何调参、H1/H2 compare、
R10/R11/R12。已授权的仍是且仅是 trial 2 的**一次** Play。COORD-007 §4.1 的
一帧下界缺口继续敞开且已披露；本轮未消除、也无权消除。

### Acceptance round 41 — 2026-08-13（arm A trial 2 归因、具名终态与现场保全）

Decision: **`TRIAL_VOID_LOOP_DOMAIN_UPPER_BOUND_VIOLATION_POST_TRACKER_DWELL`**
（trial 不计入；采集 ID 与一次性 GO 均已消耗；现场保全按 §E；三项处置需用户授权）

本轮所有数值由 Acceptance **自行复算**（只读，从保全字节导入
`analyze_m3_body.py` 的纯函数或自写投影代码；**未运行**分析器任何模式，
主工作树零改动）。凡与实现角色 §I.3 不一致处，以本节为准并逐条说明差异来源。

#### A. 事实认定（逐条可重算）

1. **门确实且只在整圈定义域上触发**：`P = 212.97056274847716 m`，
   `final_mileage = 769.3931091460372 m`，格式化后逐字复现
   `trial_invalid_no_single_loop:769.393`；触发的是 **`>= 2P`** 那一支
   （`2P = 425.9411254970 m`），不是 `< P`。
2. **该门之前的检查确实全部通过**：`analyze_trial`（`analyze_m3_body.py:784`）
   到 1035 行之间**无任何 try/except**，故到达该行机械证明约 24 处 raise 全部
   未触发。**但只能向后证明**：1035 行之后还有 6 处 fail-closed
   （`measurement_window_empty` 1054、`no_geometrically_visible_window_frames`
   1092、`c_quality_window_empty` 1109、`missing_metrics_snapshot` 1230、
   `metrics_projection_provenance_missing` 1234、`metrics_projection_aspect_mismatch`
   1239）**从未被求值**。「失败点唯一」**不等于**「这次 trial 其余部分都合格」，
   本轮不作后一种主张。
3. **机制成立（两侧源码互证）**：`_read_truth`（313–349）对 truth 流**无任何
   帧窗过滤**，调用点（891–893）传入 run-bound 整份拷贝；覆盖检查（894–901）
   **单向**——tracker 帧必须有 truth，多余 truth 静默保留；Unity 侧
   `CoverageEvaluator.cs:642–684` 每帧写、每次 Play 截断重写，**与 tracker 生命期
   无关**。故该门衡量的是**整个 Play 的里程**，`--planned-duration-s 130.0`
   只约束 tracker。
4. **现场完好**：A1 正式 run 目录仍 11 份、目录聚合 SHA-256 与 §N.1 的
   `7c3af28e…cda79` **相等**；post-run 归档仍 6 项、`frames/` 257 项、聚合
   `ea9ba050…2fb3` **相等**；四处 hold 仍 257/93/109/257；attempt-3 hold 仍恰两
   文件；trial-2 run 目录恰 10 份且逐项 SHA 与 §I.2 相符；
   `m3_body_analysis.json` **不存在**；shared 根与 `runtime/frames/` 257 项
   与 §I.2 一致。
5. **场景/plant 无异常**：排除路线顶点邻域后弦速 `1.9995–2.0004 m/s`
   （1783 对，均值 `1.999996`）；全体 1913 对的最小值 `1.5822 m/s` 共 26 对
   **全部落在 8 个路线顶点 0.475 m 内**，是拐点弦长效应，不是 plant 异常。
   实现角色「全程恒定」的**结论成立**，但其十分位抽样不足以支撑「全程」措辞，
   本轮以全体样本重述。

#### B. 数值更正（实现角色 §I.3 与状态板均需以本节为准）

§I.3 自述用「相邻 truth 记录的世界系**弦长**」，属**已披露**的方法；但其数字
随后被用来论证 `[P, 2P)`，而**门用的是路线投影里程**。两套量都能复现，不可混用：

| 量 | 门口径（路线投影，**本轮采信**） | §I.3 弦长口径（复现无误但非门量） |
|---|---|---|
| Play 结束里程 / 圈数 | `769.393 m` / **`3.6127` 圈** | `764.217 m` / `3.5884` 圈 |
| tracker 退出时里程 / 圈数 | `261.812 m` / **`1.2293` 圈** | `260.120 m` / `1.2214` 圈 |
| 越过 `2P` 的时刻 | frame `1059`，`sim_t 211.986`（插值 `211.896`） | frame `1067`，`sim_t 213.582` |
| tracker 退出后的预算 | **`81.601 s`**（插值 `81.512`，里程式 `82.065`） | `83.197 s` |

**`83.197 s` 不得写进任何条款或上限**——它比门的真实预算宽约 `1.6 s`。

**A1 余量更正（重要）**：§I.3 的「距 2P 仅剩约 15 s」是**米当秒**的单位混淆。
从 A1 保全字节直接实测：`final_mileage = 412.84182587428813 m`（`1.9385` 圈），
距 `2P` 仅 **`13.099 m` = `6.550 s`**；A1 的 post-tracker 停留 `75.199 s`，
预算约 `82.195 s`。真实余量比记录**紧 2.3 倍**——该缺陷是**系统性潜伏**，
A1 是擦边通过，不是"协议本来没问题"的证据。

#### C. 归因（三部分，不合并、不互相掩盖）

1. **本次 void 的近因（执行侧，不是"仅次要"）**：post-tracker 停留
   `252.399 s`，是预算 `81.601 s` 的 **`3.09` 倍**，比 A1 同协议下的 `75.199 s`
   长 `177.2 s`。两次 trial 在 tracker 退出时的里程只差 `0.26 m`
   （`261.551` vs `261.812`），速度同为 `2.0 m/s`——**停留时长是唯一可测的
   区分变量**。实现角色自述「把 §H 落盘放在通知用户之前」是其自选顺序
   （操作单未要求），该选择成立；但**它占多少秒盘上无时间戳，不可测**，
   本轮不把因果份额安到具体动作上。
2. **潜伏使能条件（冻结合同，系统性，必须在下一次 Play 前处置）**：§3 步骤 4
   强制 post-tracker 停留却**不设上限**，而门在**整个 Play** 上判定，于是
   每个 trial 都只有约 **`81.6 s`** 的仿真时间预算——这个预算由冻结值
   （watchdog `130.0`、`2.0 m/s`、`P`）唯一决定，**十次 trial 全部适用**，
   A1 只剩 `6.550 s` 就撞上。
3. **立法/委派缺口（接受角色侧，本角色自认）**：数值上限 `2P` 的**数字形式**
   在**任何已接受文件中都不存在**——提案 40 轮、`docs/reviews/P1-M3-BODY-001.md`、
   正式设计与操作单对 `2P`/`no_single_loop` 检索**零命中**。它随
   **接受轮 12 §C 明确退回的候选 `1c26785`** 进入代码，只记录在实现角色证据
   lane、工具本身，以及一个**不钉住报错文本**的 `two_loops` 测试
   （`tests/test_analyze_m3_body.py:522, 676-681`）；独立复核只核过 `[0,P)`
   样本域，**从未复核过该上限**。
   **但不得据此说「实现角色发明了一个未经立法的门」**：规则本身是已接受文本
   ——round 11 §B.4「未取得**恰好一个**完整闭环即 trial invalid」、操作单 §3
   步骤 5「闭环恰好一次」、§4 注「是否恰好一圈仍由离线机械判定」。`[P, 2P)`
   是对该规则的忠实机械化。真正的缺口是：**接受角色把工具冻结为唯一绑定来源，
   却从未把该门的数字形式与其时间后果写进面向操作员的条款**，而操作单 §1
   钉住表把规则只写成下界（「**不足**恰好一个完整闭环」），同表 watchdog 行还
   反过来向操作员保证「**远低于两圈 213 s**」——这句对 **tracker 为真、对
   **Play 为假**（130 s 时 Play 已在 `1.2293` 圈，距两圈只剩约 `82 s`）。
4. **不是**：场景/plant 缺陷、tracker 行为、模型、门 1/2/3、Console、
   用户操作违规。逐条核对 §3 步骤 1–5，未发现任何**书面条款**被违反
   （§G.5 的解释器绝对/相对拼写属操作单**自身**两句要求的冲突，操作员的解法
   语义惰性，已披露；本轮追认，不作偏差）。

#### D. A1 不受本缺陷影响，但**对某些修法有暴露**（对未来修法的硬约束）

- **不受缺陷影响（本轮独立复算）**：H1 整圈域是 `mileage < P` 的值过滤，
  `_unwrap_mileage` 前向单遍；对 A1 truth 流在首次闭环及之后的 **498 种截断**
  重算，`C_geom` 与 `loop_frame_count` 只有**一个**取值，且与已接受的
  `0.5784550773737355` / `529` **逐位相同**。Play 跑多远都动不了 A1 的数。
- **对修法有暴露（必须先解决再谈修法）**：操作单 §2.6 第 4 项把每次 Play 前
  的门钉在 A1 `--verify` **整份序列化逐字节相同**上，而该序列化含三个
  **Play 长度相关**字段：`domains.final_unwrapped_mileage_m = 412.84182587428813`、
  `receipt.last_frame_id = 1026`、`receipt.truth_record_count = 1027`。
  任何改变分析器 truth 摄入口径的修法（尤其"把 truth 截到 tracker 窗口"）
  都会让 A1 的 `--verify` 抛 `verify_rerun_not_byte_identical`，而
  `m3_body_analysis.json` 是 create-once，不能就地重生成。**任何修法方案必须
  先给出 A1 的处置，否则不得采纳。**

#### E. 现场保全裁定（与 ID 消耗机械耦合，故与先例不同）

**E1｜`runtime/runs/p1-m3-body-001-arm-a-trial-2/` 原地不动，不移动、不改名。**
理由是机械的：该采集 ID 的再消耗**只**由 `RunLogger` 的
`mkdir(parents=True, exist_ok=False)`（`controller/run_log.py:508`）阻挡；
`analyze_m3_body.py:496-505` 按名字拒绝的只有 A1 的旧 canonical ID，并拒绝
一切 `-attempt-N` 形状。attempt 3 能移走是因为其 ID 另有代码级
`run_id_void_consumed` 拒绝；**slot 2 没有**。移走即解除唯一的机械闭锁。

**E2｜移动且只移动下列 6 项 shared 现场**（它们是唯一副本，会被下次 Play
截断覆盖；truth 已在 run 目录内有逐字节相同的 run-bound 拷贝，故一并保全但
不删除任何一侧）。每个 destination 移动前必须不存在：

| Source | Destination |
|---|---|
| `runtime/frames/` | `runtime/frames.arm-a-trial-2-void-hold/` |
| `runtime/m3_body_truth.jsonl` | `runtime/m3_body_truth.arm-a-trial-2-void-hold.jsonl` |
| `runtime/metrics.json` | `runtime/metrics.arm-a-trial-2-void-hold.json` |
| `runtime/body_command.json` | `runtime/body_command.arm-a-trial-2-void-hold.json` |
| `runtime/gimbal_command.json` | `runtime/gimbal_command.arm-a-trial-2-void-hold.json` |
| `runtime/tracking_observation.json` | `runtime/tracking_observation.arm-a-trial-2-void-hold.json` |

逐项记录移动前后文件数/行数/字节数/SHA-256 相等，**零删除、零覆盖、零分析**；
移动后只新建空 `runtime/frames/`，不得预建任何 run 目录；并证明 A1 现场与
四处旧 hold 不变。**执行时机**：与下一次 Play 的准备批次同批，**在**用户就
§G 作出决定**之后**；在此之前一切原地不动（run-bound 拷贝已保住 truth 与
tracker 侧全部字节，无立即风险）。

**E3｜采集 ID `p1-m3-body-001-arm-a-trial-2` 永久消耗**：run 目录已由
create-once 创建（先例 = §5 post-tracker 段）。一次性 GO 同时消耗。

#### F. 名字与条款的落点（本轮已应用，零门、零数值改动）

1. 操作单 §5 新增本轮具名终态
   `TRIAL_VOID_LOOP_DOMAIN_UPPER_BOUND_VIOLATION_POST_TRACKER_DWELL`：
   语法沿用既有 `TRIAL_VOID_ + <门> + <失败名词> + <阶段/具体>`，用
   `VIOLATION`（门被越过）而非 `DEVIATION`（归责操作方）——归责按 §C 三分，
   写在散文里，不塞进名字。（据实更正一处历史：attempt 2 的终态是
   `TRIAL_VOID_PROTOCOL_DEVIATION_PRE_TRACKER`，`TRIAL_VOID_PAUSE_WINDOW_VIOLATION`
   是 round 25 新设、**从未被触发**的门。）
2. 操作单 §1「整圈定义域」行**如实披露工具既有的两侧判据**（此前只写下界），
   并撤回 watchdog 行「远低于两圈 213 s」这句对 Play 为假的论证，改为写明
   130 s 时 Play 约 `1.2293` 圈、距两圈约 `82 s`。
   **这两处是披露更正，不新增门、不改任何数值、不改工具行为。**
3. 上述两处与 §5 的新名字都落在 PLAY_GOVERNING 文件（round 40 裁定），
   其逐文件独立复核与 revision 12 的复核债务一并挂在 `COORD-007` 交接行。

#### G. 需要用户决定的三项（本角色不得自行决定，逐项列出代价）

**G1｜post-tracker 停留的修法**（不修则任何后续 Play 都在 `81.6 s` 的赛跑里）：

| 方案 | 触及 | 代价 / 风险 |
|---|---|---|
| **F4 文档级**：validator 出确认词后**立即**请用户退出、证据事后补写，并写明停留上限 | 只改操作单（PLAY_GOVERNING，属协议改动） | 最快、零代码；但预算仍只有 `81.6 s`，A1 最好成绩 `75.2 s` 只余 `7 s`，**脆弱** |
| **F1 分析器按 tracker 窗口截断 truth** | `analyze_m3_body.py`（Play 治理门 → §4.4 R3 条件 (3) **强制闭环复核轮**） | 根治；但**破坏 A1 的 `--verify` 逐字节门**（§D），必须先裁定 A1 处置 |
| **F2 撤下 `>= 2P` 上限，改用别的机械化** | 同上 + 需**明文修订**「恰好一个闭环」的机械化 | 数字形式本就未立法，撤下不算改冻结值；H1 域是首圈值过滤，实测不受多圈污染；但这是**看到失败之后**动 Play 杀手门，必须走明文修订而非顺手改 |
| **F3 Unity 在 tracker 完成后停写 truth** | `Assets/`（开复核轮） | 改真值载体冻结语义；未来 run 与 A1 的 receipt 结构不可比 |
| **F5 降 watchdog** | 冻结值 | 下界需 `≈106.5 s`+裕量，买不到多少空间，不推荐 |

本角色建议：**F4 先行（使下一次 Play 在制度上可能）+ F1/F2 择一作为根治**，
且 F1/F2 都必须先回答 §D 的 A1 处置。**但这是用户的决定**，账本
2026-08-13 条目已把「修改协议/指标/阈值/测量窗/载体」逐字列为**未授权**。

**G2｜arm A 槽位**：`TRIALS_PER_ARM = 5`，slot 2 已消耗且**无 `-attempt-N`
逃生口**（A1 的替代 ID 是靠代码常量加进去的）。因此当前只剩 trial-3/4/5，
arm A 最多凑到 **4** 个有效 trial，与 BC-BODY1-13「恰好 5 次/臂」冲突。
二选一：(a) 授权冻结一个 slot-2 替代采集 ID（代码 + 必失败测试 + 复核轮 +
新 GO，走 attempt-4 的老路）；(b) 明文把每臂 trial 数从 5 改为 4（改主指标
证据设计，需明确授权）。

**G3｜下一次 Play 的 GO**：本轮 GO 已消耗，任何后续 Play 都需用户新的逐字
授权；在 G1 未落地前，本角色**不建议**授权任何 Play。

#### H. 未 discharge 的义务与边界

- trial 2 **不以任何形式计入**（操作单 §5 无条件条款，源自 round 11 §B.5）；
  未产生任何 `C_*`/H1/H2；`m3_body_analysis.json` 不存在；不得 `--finalize`、
  不得重跑分析器、不得就地重进顶替。
- BC-BODY1-15 (d) 的反调参纪律继续适用；本轮**未**改任何阈值、指标、
  测量窗、载体、CLI 或代码。
- revision 12 与本轮 §F 的操作单改动仍欠逐文件独立复核（挂 `COORD-007` 行）。
- 「失败点唯一」只向后成立（§A.2）；本轮不主张 trial 2 其余部分合格。

### Acceptance round 42 — 2026-08-13（G1 = F4+F2 与 G2 = (a) 的 binding clarifications）

Decision: **`ACCEPTED_WITH_BINDING_CLARIFICATIONS`（BC-BODY1-23…31）**，唯一执行位
交实现角色。授权依据：`docs/authorizations.md` 2026-08-13「授权 G1 = F4+F2、
G2 = (a)」条（该条撤销同日稍早的暂缓条）。

**本轮不释放任何 Play**（§G3 未答复），不改主指标、`[0, P)` 整圈样本域、
测量窗、阈值、载体、CLI 或 `docs/phase1-single-drone-design.md`（§6 指标定义
一字不动，故不升版本）。

#### A. 明文修订：整圈定义域的**准入判据**（F2 的立法部分）

接受轮 11 §B.4 原文「未取得**恰好一个**完整闭环即 trial invalid」现予修订。
修订后的准入判据只有下界，配一条新的域完整性硬门：

- **保留**：`final_mileage < P` → fail closed（未跑完一圈，trial invalid）。
- **撤下**：`final_mileage >= 2P` 这一支。理由已在接受轮 41 §C.3 记录——该数字
  形式从未进入任何已接受文件，且「不让第二圈混进 H1」这一**立法目的**由
  `[0, P)` 值过滤本身实现，与 Play 跑多远无关（498 种截断复算证明 A1 的
  `C_geom`/`loop_frame_count` 唯一）。
- **新增补偿性硬门**（撤下上界不得使域变松）：`unwrapped` 序列必须**非递减**，
  且**首次闭环之后不得再出现 `mileage < P` 的样本**；违反即 fail closed。
  实测 A1 与 trial 2 的 backward step 均为 **0**、闭环后低于 `P` 的样本均为
  **0**，故该门不会追溯改变任何既有结果。

修订后「恰好一个闭环」的语义由**样本域**承担而不再由**Play 长度**承担：
H1 只取首圈，第二圈及以后既不进 H1 也不再使 trial 作废。

#### B. Binding clarifications（实现角色按字面执行；歧义退回接受角色）

**BC-BODY1-23（F2 判据）**：`tools/analyze_m3_body.py` 的整圈定义域门改为
「`final_mileage < perimeter` → fail closed」，删除 `>= 2.0 * perimeter` 一支；
错误名 `trial_invalid_no_single_loop` 保留给下界。新增 §A 的两条域完整性检查，
各自具名 fail closed（名称由实现角色取，须在证据中逐字记录）。

**BC-BODY1-24（零序列化扰动，硬约束）**：本批**不得**新增、删除、改名、
重排 `m3_body_analysis.json` 的任何字段，**不得**改变任何已有字段的计算方式
或取值。圈数等派生量由已有的 `domains.final_unwrapped_mileage_m` 与
`route_perimeter_m` 计算，**不入 JSON**。
**证明义务**：改动后运行
`tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-1-attempt-4`，
必须退出 0 并逐字返回冻结 JSON（`WITHIN_RANGE / 0.5784550773737355 / 1.0`）；
把命令与 stdout 逐字入证据。**该 `--verify` 不通过即视为本批失败，回接受角色。**

**BC-BODY1-25（`two_loops` 测试改判）**：`tests/test_analyze_m3_body.py` 现有
`two_loops` 用例断言"追加第二圈会抛错"，与 §A 相反，必须**改为正向断言**：
在单圈 fixture 上追加第二圈（并再追加第三圈）后，(i) 分析**不抛错**，
(ii) `h1.full_loop_c_geom` 与整圈样本数与单圈 fixture **逐位相同**。
另补**必失败测试**：下界 `< P`、非递减违反、闭环后低于 `P` 的样本各一条，
均须在修复前失败、修复后通过。fixture 依 workflow §4.4 R3 条件 (1) 由生产
路径产出或取已归档真实 run 的字节副本，**禁止手工 mkdir / 手写 JSON**；
若依赖未跟踪的 `runtime/` 资产则必须显式 skip，不得静默通过。

**BC-BODY1-26（G2(a) 替代采集 ID）**：slot 2 的下一次且**仅**下一次采集使用
**`p1-m3-body-001-arm-a-trial-2-attempt-2`**，映射回 canonical slot
`p1-m3-body-001-arm-a-trial-2` 并与原 B2 配对。旧 ID
`p1-m3-body-001-arm-a-trial-2` **永久拒绝**（沿用 `run_id_void_consumed`）；
其他 attempt 后缀一律拒绝；其余八个采集 ID 逐字不变；`TRIALS_PER_ARM = 5`
不变，BC-BODY1-13「恰好 5 次/臂」因此保住。
`_expected_policy()` 对新 ID 必须返回 `hold`；`expected_acquisition_ids('a')[1]`
必须等于新 ID。

**BC-BODY1-27（A2 前驱 void 字节绑定）**：仿 A1 的
`_check_a1_predecessor_hold`，为 A2 采集新增**只读、无指标**的前驱检查：
hold 目录 `runtime/runs/p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold/`
必须存在，其直接文件名集合必须**恰为**下列 10 个，且三项 SHA-256 相等：

| 文件 | 字节 | SHA-256（冻结） |
|---|---|---|
| `frames.jsonl` | 993748 | `a7939b7ce0a54a52487859b3ed1e12d3f0b6526759ab5e77925c49980309fc54` |
| `manifest.json` | 7858 | `d9774905aab324acf05c7616d0bf9e8a0ccf8f10c3855dd5c8c4ff1f9ea4a50c` |
| `m3_body_truth.jsonl` | 1967851 | `6f3e5238ef0057253f1228ec4aa9fdd53c2557dd00bc01d2df1782e90635f095` |
| 其余 7 项（名称须存在，不另钉哈希） | — | `metrics.final.json`、`summary.json`、`scenario.json`、`margin.json`、`body_config.json`、`reanchor_config.json`、`tracker_model_spec.json` |

该检查**只枚举文件名并对原始字节取 SHA-256**，不解析 void 内容、不计算任何
void 指标，且必须在收集/写盘之前执行；**只对 A2 采集触发**，不得影响其余九个
run 的路径（含 A1 的 `--verify`，见 BC-BODY1-24）。receipt 中的 A2 专属字段
比照 A1 的条件式写法，**不得**使其他 run 的序列化出现任何变化。

**BC-BODY1-28（执行顺序，不得颠倒）**：
1. 实现角色落地 BC-BODY1-23…27 + 测试 + 证据，**零 Play、零 ID、零现场改动**，
   停在稳定候选；
2. 接受角色按 workflow §4.3.1 四条件确认停点；
3. **强制闭环独立复核轮**（§4.4 R3 条件 (3)，因触及 `analyze_m3_body.py`），
   同轮一并覆盖 revision 12 与接受轮 40/41 的操作单改动（挂在 `COORD-007` 行的
   复核债务）；
4. 复核 PASS 后接受角色消费 verdict 并撰写**操作单 revision 13**（F4 条款、
   整圈定义域行改写、A2 采集 ID 钉住行、保全记录节）；
5. 实现角色执行 §C 的现场保全并逐项记录；
6. 用户新的逐字 GO 之后才有下一次 Play。**在第 6 步之前任何 Play 都未授权。**

**BC-BODY1-29（F4 操作顺序，落在 revision 13）**：validator 逐字产出
`TRACKER_AUTO_COMPLETE_CONFIRMED` 后，实现角色的**下一个动作必须是请用户退出
Play**；读 run 记录、写证据、写状态一律在用户退出**之后**。用户收到请求后
**尽快**退出。**本条不设任何数值上限、不新增任何门**——F2 落地后停留时长不再
影响 trial 准入；本条只消除不必要的停留并留下可核对的顺序。

**BC-BODY1-30（F4 披露）**：每次 trial 证据必须记录 (i) tracker 最后一帧的
`simulation_time_s` 与 Play 最后一条 truth 的 `simulation_time_s`、二者之差
（post-tracker 停留），(ii) 由 `domains.final_unwrapped_mileage_m /
route_perimeter_m` 算出的实测圈数。**只记录、不判定。**

**BC-BODY1-31（不得越界）**：本批不得改动主指标、`C_quality`、H2、`[0, P)`
样本域、`62.5 m` 测量窗、`130.0 s` watchdog、冻结初始框、CLI 其余参数、
scenario/model/re-anchor config、`controller/`、`Assets/`；不得动 A1 现场
（11 份 / 6 项）与四处旧 hold；不得执行 §C 的保全移动（那是第 5 步）。

#### C. 现场保全合同（第 5 步执行，**取代**接受轮 41 §E2 的命名）

BC-BODY1-26 落地后，代码按名字永久拒绝旧 ID，`runtime/runs/` 的 create-once
不再是唯一闭锁，故 run 目录**可以且应当**按 attempt-3 先例移入 hold。七组
source→destination 逐字冻结，每个 destination 移动前必须不存在：

| Source | Destination |
|---|---|
| `runtime/runs/p1-m3-body-001-arm-a-trial-2/` | `runtime/runs/p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold/` |
| `runtime/frames/` | `runtime/frames.arm-a-trial-2-void-attempt-1-hold/` |
| `runtime/m3_body_truth.jsonl` | `runtime/m3_body_truth.arm-a-trial-2-void-attempt-1-hold.jsonl` |
| `runtime/metrics.json` | `runtime/metrics.arm-a-trial-2-void-attempt-1-hold.json` |
| `runtime/body_command.json` | `runtime/body_command.arm-a-trial-2-void-attempt-1-hold.json` |
| `runtime/gimbal_command.json` | `runtime/gimbal_command.arm-a-trial-2-void-attempt-1-hold.json` |
| `runtime/tracking_observation.json` | `runtime/tracking_observation.arm-a-trial-2-void-attempt-1-hold.json` |

逐项记录移动前后文件数/行数/字节数/SHA-256 相等，**零删除、零覆盖、零分析**；
移动后只新建空 `runtime/frames/`，不得预建任何 run 目录；并证明 A1 现场与四处
旧 hold 不变。BC-BODY1-27 的三个冻结 SHA 在移动后必须仍然相等（字节不随路径变）。

#### D. 仍未答复 / 仍不变

- **§G3（下一次 Play 的 GO）未答复**：BC-BODY1-28 第 6 步之前无任何 Play 授权。
- trial 2 仍**不以任何形式计入**；其一次性 GO 与旧采集 ID 已消耗。
- A1 仍有效，现场逐字节保全；BC-BODY1-15 (d) 反调参纪律继续适用。
- COORD-007 §4.1/§4.2 的机器断言仍属 R10，**未授权、未开工**。

### Acceptance round 43 — 2026-08-13（BC-BODY1-23…27 落地件复核：停点**尚未**成立）

Decision: **`STOP_POINT_NOT_YET_CONFIRMED_ONE_DELTA_REQUIRED`**。落地质量高，
BC-BODY1-23/-24/-26/-27/-31 逐条成立且经本角色独立复算；但 §4.3.1 条件 1
（范围与接口已冻结）**现在不成立**——本轮新发 BC-BODY1-32，属同一 Play 治理门
文件的小改动。**先补该项再确认停点**，以免把强制复核轮花在马上要变的代码上
（§4.4 R3 条件 (3) 对 `analyze_m3_body.py` 的每次触碰都强制加轮，合并做才省）。

#### A. 接受角色独立复算（只读；主工作树全程 `git status --porcelain` 为空）

1. **BC-BODY1-24 证明门（本角色亲自跑，不采信转述）**：
   `analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-1-attempt-4`
   **退出 0**，stdout 逐字为
   `{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355,
   "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true,
   "window_c_track_given_geom": 1.0}`。A1 的序列化零扰动**成立**。
2. **「修复前必失败」亲自复算**（`git worktree add --detach` 一次性副本，只把
   整圈定义域那一段 revert 回 `>= 2P`，其余保留；主树零接触，收工 `worktree
   remove`）：`Ran 65 … FAILED (failures=2, errors=3)`，红的**恰是**
   `test_extra_laps_neither_void_the_trial_nor_change_h1`（2 个 subtest）、
   `test_extra_laps_leave_the_loop_domain_bit_identical`、
   `test_backward_unwrapped_step_fails_closed`、
   `test_post_closure_sample_below_perimeter_fails_closed`；恢复后 65/65 OK。
   （本角色的副本无未跟踪 `runtime/`，`ArchivedRunLoopDomainTests` 整类 skip，
   故比实现角色少两条真实字节用例——两次演示相互印证，不冲突。）
3. **两门对既有数据零追溯影响**（本角色自算）：A1 与 trial 2 的 `unwrapped`
   backward step 均为 **0**、首次闭环后低于 `P` 的样本均为 **0**。轮 42 §A
   的前提复验成立。
4. **现场未动**（BC-BODY1-31）：A1 run 目录 **11** 份、post-run 归档 **6** 项、
   trial-2 run 目录 **10** 份且 `m3_body_analysis.json` 仍不存在、
   `runtime/frames/` **257** 项、`runs/` 下**未**出现任何 `-void-attempt-1-hold`。
   改动仅 4 个路径（工具、测试、新证据、状态板），零 `controller/`、零
   `Assets/`、零 `config/`。
5. **判据代码逐字核对**：`>= 2.0 * perimeter` 一支已删除，下界与错误名
   `trial_invalid_no_single_loop` 保留；两条新门具名且各自 fail closed；
   `canonical_trial_id` 对两个旧 ID 均落 `run_id_void_consumed`；
   `expected_acquisition_ids('a')[1]` = A2 采集 ID；`_check_a2_predecessor_hold`
   只在 `run_id == A2_ACQUISITION_RUN_ID` 时触发且在收集/写盘之前。

#### B. 对实现角色 §F 七项的裁定

1. **§F.1（下界那条「修复前必失败」不成立）——接受，且这是本角色的起草
   错误。** 下界是本次修法**保留**的分支，对未改变的行为要求"修复前失败"在
   机械上不可能。**BC-BODY1-25 就此更正**：三条中只有「非递减违反」与「闭环后
   低于 `P`」是必失败测试；下界那条改列为**保留分支的具名回归测试**（它同时
   修好了 §C.2 那个从未到达命名分支的旧用例，本身是净收益）。实现角色如实
   上报而不是自行放宽，处理正确。
2. **§F.2（`compare_arms` 只校验 A1 的 binding 字段）——不接受现状，发
   BC-BODY1-32。** 见 §C.1。实现角色按字面执行无误（BC-26/-27 确实没要求），
   但 A1 在轮 29 §C.2 恰恰把这条补上过，只给 A2 留缺口会被后来的读者读成
   "刻意区别对待"。
3. **§F.3（A2 前驱门未在真实 hold 上跑过）——接受现状，追加
   BC-BODY1-33**：hold 要到第 5 步才存在，现在跑不了；移动完成后必须在真实
   hold 上复跑一次并记录（只读、零 ID）。见 §C.2。
4. **§F.4（两门判定顺序）——采纳实现裁量并就此裁定：顺序为「先闭环后低于
   `P`，再非递减」，不得颠倒。** 理由经本角色复核成立：若先查非递减，则任何
   闭环后跌回 `P` 以下的样本必然先被判为 backward step，具名分支成为死代码。
   本条写死，防止后来者"整理"顺序。
5. **§F.5（fixture 两条通道）——接受。** BC-BODY1-25 的生产路径要求约束的是
   本轮**新增的整圈定义域测试**，它们确实全部走 `ProductionReplayRun` 真实
   坐标、反例只重排回放位置；身份/receipt/前驱门沿用轮 30 §C.3 既有合成
   fixture，属既有先例，不在本轮改造范围。
6. **§F.6（Unity 未跑）——接受。** 本批零 `Assets/`/`ProjectSettings/`/
   `config/` 字节，无 C# 面。这**不是** `UNITY_NA` 分类（那需复核角色附议），
   只是本批不产生 Unity 用例。
7. **§F.7（worktree 中整类 skip）——接受并转达复核角色**：`runtime/` 是未
   跟踪生成物；复核若要看 `ArchivedRunLoopDomainTests` 真跑，把
   `runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4` 与
   `…-arm-a-trial-1-void-attempt-3-hold` **只读拷贝**进一次性 worktree。
   skip 是显式的，不是静默通过。

#### C. 本轮新增条款

**BC-BODY1-32（compare 侧对称，唯一待补项）**：`compare_arms` 现有的
`a1_attempt_binding_mismatch` 逐键校验必须对 A2 对称补齐：对 A2 采集 receipt
校验 `acquisition_run_id`、`canonical_trial_id`、`attempt_number` 与**三个**
predecessor SHA（含 `predecessor_void_truth_sha256`），失败名
`a2_attempt_binding_mismatch:<key>`。**不得**把这些键放进 `identity_keys`
（轮 29 §C.2 的原意：它们是单 run 专属，不是十 run 共同值）。补一条必失败
测试：篡改 A2 receipt 的任一该键 → compare 具名 fail closed。**本条不得改动
任何数值、字段名、序列化顺序或 A1 分支**；改后必须重跑 A1 `--verify` 并再次
逐字复现冻结 JSON。

**BC-BODY1-33（第 5 步之后的门排练）**：§C 的七项保全移动完成后，在**真实**
hold 上只读复跑 A2 前驱门（可直接调用 `_check_a2_predecessor_hold`，或跑
`--run-id …-attempt-2` 观察它越过前驱门后停在 `missing_run_directory`），
把命令与逐字输出记入证据。**零 ID、零写盘、零 Play。**

**BC-BODY1-34（全套测试的解释器口径）**：本 work item 的全套测试记录一律用
§1 钉住的 `.venv-yoloe/bin/python`。裸 `python3` 缺 torch/ultralytics/cv2，
会把 9 个模块整体计为 import error 并少收 105 条用例，其数字不得作为停点
证据的权威记录。

#### D. 测试记录更正（以本角色实测为权威）

实现角色 §C.5 的全套数字取自裸 `python3`（`Ran 428 … errors=9`）。本角色在
钉住解释器下实测：

```
.venv-yoloe/bin/python -m unittest discover -s tests
Ran 533 tests … FAILED (failures=1, errors=1, skipped=1)
```

两条不通过是 `test_trackers…test_pinned_opencv_csrt_initializes_and_updates`
与 `test_track_loop…test_cli_runs_pinned_csrt_to_a_versioned_summary`，**与
接受轮 39 §G 记录的同一对**（`.venv-yoloe` 的 cv2 未装 `opencv-contrib` 的
CSRT 组件，属 `P1-TRACK-001` 旧基线追踪器，不在本批与采集路径上）。
533 = 轮 39 的 518 + 本批净增 15 条（focused 50→65），**本批零新增失败**。
focused 套件 65/65 OK，本角色复跑一致。

#### E. 停点状态与下一步

- §4.3.1 条件 **2/3/4 已满足**（相称测试通过并经本角色复跑；无 Unity 面；
  证据、复核范围与状态板已更新），**条件 1 待 BC-BODY1-32 落地后成立**。
- BC-BODY1-32 落地后回接受角色确认停点，再进 **强制闭环独立复核轮**
  （同轮并入 revision 12 与接受轮 40/41 的操作单复核债务）。
- 其后顺序不变：revision 13 → 七项现场保全（含 BC-BODY1-33 排练）→ 用户新的
  逐字 GO。**§G3 仍未答复，此前任何 Play 均未授权。**

### Acceptance round 44 — 2026-08-13（BC-BODY1-32 复核 + §4.3.1 停点确认）

Decision: **`STOP_POINT_CONFIRMED_CANDIDATE_07bb8a4_HANDED_TO_REVIEW`**。
BC-BODY1-32 逐条成立且经本角色独立复算；§4.3.1 四条件全部满足；候选交
**强制闭环独立复核轮**（§4.4 R3 条件 (3)）。**本轮仍不释放任何 Play。**

#### A. 接受角色独立复算（只读；主工作树全程 `git status --porcelain` 为空）

1. **BC-BODY1-32 逐字核对**：`compare_arms` 对 `arm_a[1]["receipt"]` 逐键校验
   六个 binding（含 `predecessor_void_truth_sha256`），失败名
   `a2_attempt_binding_mismatch:<key>`；六键**未**进入 `identity_keys`
   （本轮 diff 里 `identity_keys` 元组一字未动）；A1 分支逐字未改。
2. **BC-BODY1-32 的必失败测试，本角色亲自复算**：一次性 worktree 中**只**删掉
   新增的 A2 校验块 → `Ran 67 … FAILED (failures=12)`，红的**恰是** 12 条
   `slot='a2'` subtest（6 键 × wrong_value/missing），10 条 `slot='a1'`
   subtest 与其余 66 条测试全绿；恢复后 67/67 OK。主树零接触，收工
   `git worktree remove`。
3. **BC-BODY1-24 证明门复跑（本角色亲自跑）**：A1 `--verify` **退出 0**，
   stdout 逐字仍为
   `WITHIN_RANGE / 0.5784550773737355 / 1.0`。序列化零扰动在 BC-32 之后
   **仍然成立**。
4. **测试记录（BC-BODY1-34 口径，本角色复跑）**：focused **67/67 OK**；
   全套 **535 ran，failures=1 + errors=1 + skipped=1**，两条不通过仍是
   `test_pinned_opencv_csrt_initializes_and_updates` 与
   `test_cli_runs_pinned_csrt_to_a_versioned_summary`（`.venv-yoloe` 的 cv2
   缺 opencv-contrib CSRT 组件，`P1-TRACK-001` 旧基线，不在采集/控制/指标
   路径上）。535 = 轮 43 的 533 + 本批净增 2；**零新增失败**。
5. **现场未动**：A1 run 目录 **11**、post-run 归档 **6**、trial-2 run 目录
   **10** 且 `m3_body_analysis.json` 仍不存在、`runtime/frames/` **257**、
   `runs/` 下**无**任何 `-void-attempt-1-hold`。本批只动 4 个路径
   （工具、测试、证据、状态板），零 `controller/`、零 `Assets/`、
   零 `ProjectSettings/`、零 `config/`。

#### B. 对实现角色 §F.8 两项披露的裁定

1. **同一测试顺带覆盖 A1 侧五个键 —— 接受，且保留。** 那是 BC-32 未要求的
   测试加强：A1 的 compare 侧校验自轮 29 落地起**从未有测试**。它零生产代码
   改动，删掉反而是净损失。**不视为超范围。**
2. **`CompareArmsTests._receipt()` 补 A2 binding 块 —— 接受。** 夹具必须与
   生产语义一致，否则十 run 夹具在新门下全部失败；这是**夹具跟随生产**，
   不是放宽判据。其正确性由同批的正向对照测试
   `test_binding_keys_are_not_cross_run_identity` 机械锁住：其余八个
   canonical-slot run 的 receipt **不得**含这六个键，且未篡改的十 run 集必须
   干净通过。本角色确认该测试在当前树为绿。

#### C. §4.3.1 停点确认（四条件逐条）

| # | 条件 | 判定与依据 |
|---|---|---|
| 1 | 实现范围与接口已冻结 | **成立**。BC-BODY1-23…27 + 32 全部落地；BC-BODY1-33 是第 5 步义务、BC-BODY1-34 是记录规则，均不改本候选代码；接受角色本轮**不再提出**任何新代码要求 |
| 2 | 相称的实现者测试/编译通过 | **成立**。focused 67/67、全套 535 仅两条既存 CSRT 失败，**均由本角色在钉住解释器下复跑**；两批的必失败演示本角色各自独立复算过 |
| 3 | 已知 Unity 失败已处置 | **成立（无 Unity 面）**。本候选零 `Assets/`/`ProjectSettings/`/`config/` 字节、无 C# 变更。**这不是 `UNITY_NA` 分类**（那需复核角色附议），只是本批不产生 Unity 用例 |
| 4 | 复核文件、状态板、候选与未验证风险已更新 | **成立**。候选 commit `07bb8a4`；证据 `docs/evidence/P1-M3-BODY-001-loop-domain-amendment.md`（§F 未验证项、§G 复核范围、§H BC-32 批次）；状态板本轮同步 |

**开轮资格（§4.4 R1）**：`git diff --name-only 6019f33..HEAD`（`6019f33` =
Review round 6 通过候选；该轮早于 COORD-007 R7，故复核文件无 `passed_candidate`
机读行，属存量不回改）在 PLAY_GOVERNING 上**非空，共 9 条**——本 work item 的
操作单、`analyze_m3_body.py` 与其测试，加 COORD-007 的六条自检工具/测试。
**新复核轮成立。**

#### D. 交复核角色的范围（本轮同时清三笔债）

1. **本候选**：`tools/analyze_m3_body.py` 的整圈定义域段（判据 + 两条新门 +
   顺序论证）、A2 常量块、`_check_a2_predecessor_hold`、`canonical_trial_id` /
   `expected_acquisition_ids` 的 A2 分支、receipt 的 `attempt_binding` 条件块、
   `compare_arms` 的 A2 校验块；`tests/test_analyze_m3_body.py` 的
   `PredecessorHolds` / `ProductionReplayRun` 抽取、`two_loops` 与
   `no_single_loop` 改判、`LoopDomainAdmissibilityTests`、
   `ArchivedRunLoopDomainTests`、A2 身份/前驱门/compare 测试、
   `CompareArmsTests._receipt()` 的 A2 块。
2. **操作单复核债务（BC-BODY1-28 第 3 步明确并入）**：revision 12 与接受轮
   40/41/43 对 `docs/evidence/P1-M3-BODY-001-1c-preflight.md` 的全部改动。
3. **COORD-007 R5 的存量**：六条文档自检工具/测试路径的逐文件 diff。
4. **重点核对**（接受角色的建议，不限制复核自主范围）：BC-BODY1-24 零扰动
   （建议独立复跑 A1 `--verify`）；两条新门的**可达性与顺序**（轮 43 §B.4 已
   裁定顺序写死，复核若认为该裁定有误应写成 finding 而非改代码）；反例是否
   真的只重排真实坐标；A2 门是否只对 A2 触发；`identity_keys` 是否确未被污染。
5. **执行提示**：`runtime/` 是未跟踪生成物，`ArchivedRunLoopDomainTests` 在
   干净 worktree 中整类 skip（显式 skip，非静默通过）。若要看它们真跑，把
   `runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4` 与
   `…-arm-a-trial-1-void-attempt-3-hold` **只读拷贝**进一次性 worktree。

#### E. 仍不释放 / 仍未答复

- **零 Play**：BC-BODY1-28 的第 4–6 步（revision 13 → 七项现场保全含
  BC-BODY1-33 排练 → 用户新的逐字 GO）一步未走；**§G3 仍未答复**。
- trial 2 仍不以任何形式计入；其采集 ID 与一次性 GO 已消耗。
- A1 有效且现场逐字节保全；BC-BODY1-15 (d) 反调参纪律继续适用。
- **候选尚未推送**：本地领先 `origin/main` 9 个提交。AGENTS.md 的停点条文要求
  推送候选版本，但本仓库的推送先例（`P1-EVAL-001` 候选 `61ea20b`）是**经用户
  放行**后推送，故本轮**不自行推送**，据实登记待用户一句话放行；复核角色在
  本地一次性 worktree 即可开轮，不受影响。

### Acceptance round 45 — 2026-08-13（消费 Review round 7 + 操作单 revision 13）

Decision: **`REVIEW_ROUND_7_CONSUMED_PASS_WITH_NOTES / RUNBOOK_REVISION_13_ISSUED`**。
BC-BODY1-28 的第 3 步（强制闭环复核）与第 4 步（revision 13）**均已完成**；
**第 5 步（现场保全）与第 6 步（用户新 GO）尚未走，故仍零 Play。**

#### A. 消费 Review round 7

- Verdict **`PASS_WITH_NOTES`**，候选 `07bb8a4`，**CLASS_1/CLASS_2 零条**；
  机读行 `passed_candidate: 07bb8a47a9e41581c1450a7b0335e501ffdaaec9` 已落盘，
  「上一通过候选」此后由该行派生。
- 三笔债同轮清偿并经复核逐文件核对：(1) loop-domain 修法与 A2 采集身份的
  全部 BC 逐条 `CONFIRMED`（四路变异探针）；(2) 操作单 revision 12 与轮
  35/39/40/41/42 的全部改动逐 hunk；(3) COORD-007 R5 六路径的 post-round-3
  delta。复核独立复跑 A1 `--verify`、focused 67/67、全套 535（仅既存 CSRT 两条）。
- 复核对本角色两处声明的更正，**接受并记录**：(i) 轮 44 §D.2 把操作单债写作
  「轮 40/41/43」，git 实测触碰操作单的接受轮是 **35/39/40/41/42**（轮 43 未
  触碰）——文件级范围覆盖正确，编号有误，以复核为准；(ii) `UNITY_NA` 未申领，
  复核附议「本批不产生 Unity 用例」的口径，Unity 列状态不变。
- **N17 关闭**（复核附议轮 44 §B.1）。**N25/N26/N27 三条新注记由本轮的
  revision 13 闭合**（见 §B）。**N28 记录在案**：Gate-echo 是「每行每 ID 至少
  一次」，若本角色意图逐处执法需另行立法——**本轮不立法**，据实登记。
  **N12/N15/N18/N20/N21/N22 继续挂账**，本批未授权触碰。

#### B. 操作单 revision 13（BC-BODY1-28 第 4 步，本角色撰写）

**零 Play、零指标、零代码、零阈值**；冻结值经多重集比对**零丢失**
（`130.0`/`31.25`/`62.5`/`212.9706`/`[2.000000, 10.000000)`/初始框四分数与
`(177,195,77,73)`/`0.5645`/`0.95` 与全部 SHA-256 计数均未下降），§4 CLI 仍
19 行、除 `--run-id` 外逐字未改，被禁的弦长值 `83.197` 全文零出现。

1. **槽位轮换**：§1 采集 ID 行、§3 步骤 4/5、§4 CLI 全部换为 BC-BODY1-26 冻结的
   **`p1-m3-body-001-arm-a-trial-2-attempt-2`**；旧 ID 的三处残留加时间边界，
   §2.6 整节转为已执行历史。
2. **N25 闭合**：§1 整圈定义域行改写为**只有下界 + 两条具名域完整性门**（含
   顺序写死的理由）；watchdog 行的 `81.6 s` 论证降为历史背景并写明「停留时长
   不再影响准入」；三处过期行号（`:799`、`1034-1038`、`1368-1373`）改为按
   函数/模式名引用。
3. **N26 闭合**：§2.0 (b) 的基线不再手写 SHA，改为运行时取
   `docs/reviews/P1-M3-BODY-001.md` 最新一行 `passed_candidate:`——同时把该条
   从 COORD-007 R7「可派生标识禁手写」的存量违例里摘出来，此后每轮通过自动前移。
4. **F4 落地**：§3 步骤 4 加 **BC-BODY1-29**（确认词后立即请用户退出，证据事后
   写，**不设任何时间上限**）；§3 步骤 6 加 **BC-BODY1-30**（记录 post-tracker
   停留与实测圈数，**只记录不判定**）。
5. **新增 §2.7**（attempt-2 的八项只读 Play 前核对）与 **§2.8**（七项现场保全
   合同 + BC-BODY1-33 门排练）。
6. **N27 闭合，且把脆性前移**：§2.8 预先写死 hold 的十文件精确集合与三个钉住
   SHA，并禁止十文件之外的任何常规文件（含 `.DS_Store`）；§2.7 第 7 项在
   **GO 消耗之前**再查一次。原缺陷是隐藏文件会在 GO 已消耗后才被
   `a2_predecessor_hold_file_set_mismatch` 挡死；本处置不放松那道门，只把检出
   时机提前。
7. **§5 停用告示改为执行前提**：本操作单现在可用，但发令必须同时满足
   (1) §2.8 已执行并记录、(2) §2.7 八项全过、(3) **用户对本次采集的新逐字 GO**。

#### C. 现在到「可以开始测试」还差什么

| 步 | 内容 | 状态 |
|---|---|---|
| 1–3 | 实现落地 → 停点确认 → 强制闭环复核 | **已完成**（轮 42/43/44 + Review round 7） |
| 4 | 操作单 revision 13 | **本轮完成** |
| 5 | §2.8 七项现场保全 + BC-BODY1-33 排练（实现角色执行，零 Play/零 ID） | **未执行** |
| 6 | 用户对 `…-arm-a-trial-2-attempt-2` 的**新的逐字 GO** | **未答复**（§G3 自轮 41 起开着） |

**故现在不能开始测试。** 第 5 步是纯机械动作，可随时执行；第 6 步只有用户能
给。两者都完成、且 §2.7 八项在发令前实测通过之后，才是「恰好一次 Play」。

#### D. 不变项

trial 2 首次采集仍不以任何形式计入；A1 有效且现场逐字节保全；
BC-BODY1-15 (d) 反调参纪律继续适用；候选 `07bb8a4` **仍未推送**（本地领先
`origin/main`），按 `P1-EVAL-001` 先例待用户放行；COORD-007 §4.1/§4.2 仍属
R10，未授权未开工。

### Acceptance round 46 — 2026-08-13（revision 13 的 PLAY_GOVERNING 处置 + BC-BODY1-33 勘误 + §2.0 (c)）

Decision: **`RUNBOOK_REVISION_13_MANDATED_BY_REVIEWED_CONTRACT_NO_GATE_RELAXATION_REVIEW_DEBT_REGISTERED`**
（不阻断本次 Play）+ **BC-BODY1-33 勘误**；随后写入 §2.0 (c) 记录。

#### A. 裁定：revision 13 是本轮 PLAY_GOVERNING 里唯一一条，不阻断

实现角色 §L.6 第 1 条如实退回、未自行外推轮 40 的裁定，处理正确。本轮据实
单独裁定（不是把轮 40 的名字套上去）：

1. **内容是被复核过的合同点名要求的**：revision 13 的每一处都由
   **BC-BODY1-28 第 4 步**（轮 42 发出，Review round 7 逐条 `CONFIRMED`）与
   **Review round 7 自己的 N25/N26/N27** 指名——N25 甚至写明「revision 13 的
   复核应逐项核对本清单清零」。复核**预期**了这个顺序。
2. **顺序上不可能先复核**：BC-BODY1-28 把「第 3 步复核 → 第 4 步 revision 13」
   写死。要求 revision 13 先过复核会构成无穷回归（复核后必生新修订，新修订又
   需复核）。这正是轮 40 同形情形的成因。
3. **零冻结值改动（本轮在当前 HEAD 复算）**：与被复核通过的候选 `07bb8a4` 版
   逐项比较，`130.0`/`31.25`/`62.5`/`212.9706`/`[2.000000, 10.000000)`/初始框
   四分数/`(177,195,77,73)`/`0.5645`/`0.95`/`106.4853`/`0.5784550773737355`
   与 scenario SHA **计数无一下降**；§4 CLI 仍 **19 行**，与被复核版**恰 1 行
   不同**（`--run-id`，换成 BC-BODY1-26 冻结的替代 ID）；被禁的弦长值
   `83.197` 全文零出现。
4. **方向单调**：唯一的实质动作是槽位轮换（已由生产代码机械确认：
   `canonical_trial_id`/`_expected_policy`/`expected_acquisition_ids`）；其余
   要么是**如实陈述已被复核的代码行为**（F2 之后的准入判据文字），要么是
   **新增停条件**（§2.7 第 7 项隐藏文件门、BC-BODY1-29/-30 的记录义务），
   **无一放宽任何门**。
5. **债务登记而非消灭**：revision 13（含本轮 §B 的勘误）欠下一轮复核的逐文件
   覆盖，与 COORD-007 行的既有复核债并列。本轮不代签任何复核。

**角色张力照旧披露**：revision 13 由接受角色撰写、本裁定又由接受角色作出；
缓解仍是三条——事实可由他人逐条重算、复核债务保留、用户可随时推翻。

#### B. BC-BODY1-33 勘误（本角色的错，就地更正）

实现角色 §K.6/§L.6 第 3 条指出：BC-BODY1-33（轮 42 §C）与操作单 §2.8 照抄的
括注称「跑 `--run-id …-attempt-2` 观察它越过前驱门后停在 `missing_run_directory`」。
**该说法错误**——`analyze_trial` 里 `missing_run_directory` 排在
`_check_a1/_a2_predecessor_hold` **之前**（本轮逐行复核确认），故 run 目录不存在
时跑 CLI **证明不了**前驱门被走过。

- **操作单 §2.8 已就地更正**：门排练的唯一合格方法是**直接调用**
  `_check_a2_predecessor_hold(Path('runtime'))` 并观察其不抛异常；CLI 变体
  **不得**作为该排练的证据。
- **对既有证据的影响：无。** 实现角色 §K.5 与接受角色本轮的排练**都**用了直接
  调用，两者均通过；CLI 输出只是顺带记录，不是承重证据。
- 轮 42 §C 的原措辞按历史记录保留，以本节为准。

#### C. §2.0 (c)：本轮写入

(a) GO 已入账并提交；(b) 实现角色在干净 HEAD 报告完毕（基线按 revision 13 的
运行时派生取 `07bb8a4`，delta 6 条、PLAY_GOVERNING 恰 1 条、测量侧
`controller/`/`Assets/`/`config/`/`ProjectSettings/`/`Packages`/`tools/`/`tests/`
**逐字节零改动**）并执行 §2.7 **54/54 PASS**；本轮 §A/§B 处置完毕后，接受角色
把值写入 `docs/unity-test-log.md`（写入时点自取 HEAD 与 `git status --porcelain`，
不复制测量时点值），(d) 由发令方在发令时刻核对。

#### D. 仍不释放

其余 7 次 Play、任何重试/重进/调参/compare、协议与指标改动均未授权；
COORD-007 §4.1 的一帧下界缺口仍敞开（R10 未授权）；N12/N15/N18/N20/N21/N22
继续挂账。

### Acceptance round 47 — 2026-08-13（arm A trial 2 attempt 2 归因：**有效 A2**）

Decision: **`ACCEPTED — A2_VALID_TRIAL`**。arm A 现有 **2/5** 个有效 trial
（A1 = attempt-4，A2 = attempt-2）。**本轮不释放任何后续 Play**，不做 compare。

#### A. 接受角色独立复算（只读，主工作树 `git status --porcelain` 为空）

1. **`--verify` 本角色亲自复跑**：`--run-id p1-m3-body-001-arm-a-trial-2-attempt-2`
   退出 **0**，逐字返回
   `{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908,
   "run_id": "…-arm-a-trial-2-attempt-2", "verified": true,
   "window_c_track_given_geom": 1.0}`。分析可逐字节复算。
2. **A1 未受影响**：Play 之后 A1 `--verify` 仍退出 0 并逐字返回其冻结 JSON
   （`0.5784550773737355`）——BC-BODY1-24 的零扰动保证在真实新 run 之后仍成立。
3. **现场**：A2 run 目录 **11** 份（十份 run-bound + `m3_body_analysis.json`）、
   A1 **11** 份、attempt-1 void hold 仍 **10** 份、`runtime/frames/` **257** 项。
4. **身份链**：receipt 的 `acquisition_run_id` / `canonical_trial_id` /
   `attempt_number=2` / 三个 predecessor SHA 与 BC-BODY1-26/-27 冻结值逐字相等；
   scenario/margin/visible-arc/body-config/re-anchor/tracker-spec 六个 SHA 与 §1
   钉住值相等；`body_policy=hold`、`planner=hold-v1`、`condition=follow`、
   `init_frame_id=0`、`init_box_norm` 四分数逐字相等。
5. **三门与握手**（证据 §M/§N，本角色复核记录）：门 1 由保留帧机械导出
   `4.3844122886657715` ∈ `[2,10)`；门 2 最低帧 `0`；门 3 用户目检「匹配」。
   tracker 自然退出 `0`、`actual_duration_s ≥ 130.0`、只读 validator 逐字产出
   `TRACKER_AUTO_COMPLETE_CONFIRMED`、用户退出后 Console **无报错**。
6. **两条新门未触发**：`unwrapped` 非递减与「闭环后无 `< P` 样本」在本轮实跑中
   均未 fail closed，与轮 42 §A 的预期一致。

#### B. 归因：**有效 A2**

冻结合同要求的每一项都满足且可复算：事前 (a)/(b)/(c)/(d) 齐备、三门全过、
完成握手机械产生、绑定分析 PASS 且 `m3_body_analysis.json` 已写出、现场零删除
零移动。**不匹配任何 void 终态**（非暂停窗越界、非启动失败、非 post-tracker
早退、非整圈定义域 fail-closed）。故 **`p1-m3-body-001-arm-a-trial-2-attempt-2`
计为 canonical slot `p1-m3-body-001-arm-a-trial-2` 的有效 trial**，与 B2 配对。
BC-BODY1-15 (c) 的首跑三分支由 A1 放电，本轮 `WITHIN_RANGE` 只作记录，不重复
触发；(d) 的反调参纪律继续适用。

#### C. F4 的效果（本轮的核心行为差异，据实记账）

BC-BODY1-29 实测有效：确认词产生后立即请用户退出，**post-tracker 停留从
`252.399 s` 降到 `24.422043 s`**（约 1/10），整个 Play 停在 **`1.458546` 圈**。
按 revision 13 的判据这已不影响准入（`>= 2P` 上界撤下），但它同时说明 F4 与 F2
是互补而非冗余：F2 消除了准入风险，F4 消除了不必要的停留。

#### D. 对实现角色 §M.1「用户看不见 HUD」的裁定

**不是缺陷，也不是门；但操作单的措辞是我的错，本轮就地更正。**

- 冻结载体 `config/scenario.default.json` **没有计时 HUD**（带 HUD 的是
  SCENE-004 的 runtime override，§1 明令 Play 前移开）。用户**无法**读到暂停
  时刻——A1 口报「5S 左右」、本轮「看不见 HUD」同源。
- 门 1 的判据**本来就**只认保留帧机械导出值（revision 12 记录型条款），口报
  从来不是判据，因此**本次采集不受任何影响**。
- 但 §3 步骤 2 一直要求用户「报告暂停时刻」，接受轮 46 我写的 (c) 记录还照抄了
  「reports the exact displayed simulation time」——**要求一个载体上不存在的
  东西，三次采集都靠变通绕过**。本轮就地更正为「报告**已暂停**；能看到时刻则
  一并报告，仅作时序记录」。**门 1 的阈值与导出口径逐字不变**，无新增门。

#### E. 结果与分析（描述性；**不是** §5 的正式 compare）

正式 H1/H2 比较要等十次 trial 齐备后由 `--compare` 产出，本节只并列两次臂 A
采集**各自 archived 的**值，不做任何统计推断、不产生任何新指标：

| 量 | A1（attempt-4） | A2（attempt-2） |
|---|---|---|
| 整圈 `C_geom` | `0.5784550773737355` | `0.5783188398250908` |
| 窗口 `C_track|geom` | `1.0` | `1.0` |
| `C_quality` 面积中位数 px | `1227.757` | `1224.866` |
| `C_quality` 中心误差中位数 px | `59.053` | `45.317` |
| `min_side ≥ 20 px` 占比 | `0.9238199` | `0.9238506` |
| 整圈云台饱和占比 | `0.8394082` | `0.8393871` |
| 窗口云台饱和占比 | `0.4527787` | `0.4527070` |
| 系留饱和占比 | `0.0` | `0.0` |
| effort / path / planner 切换 | `0 / 0 / 0` | `0 / 0 / 0` |
| 整圈样本数 / 窗口样本数 | `529 / 155` | `530 / 155` |

**可以说的**：两次臂 A 采集在整圈 `C_geom` 上相差 `1.36e-4`，在饱和占比、
`min_side` 占比、窗口样本数上几乎逐位重合；臂 A 的 effort/path/切换恒为 `0`，
与 `hold` planner 的设计一致。**不可以说的**：任何"臂 A 稳定/可复现"的统计
主张——`n=2`、无置信区间、无对照臂，且 H1/H2 的正式口径尚未运行。

**新发现（诊断，COORD-005 通道；不进门、不改任何值）——估计器的不确定度不可信**：
`m3_body_analysis.json` 记录 `nees_median` A1 `844.03` / A2 `835.63`，而该 NEES
是位置 2 自由度口径，一致的滤波器中位数应约 `1.39`——即位置误差约 `29σ`。
本角色按 COORD-005 诊断通道只读复算 A2 的 629 个 fused 帧后可以定位成因：

| 分组 | 帧数 | 位置误差中位数 |
|---|---|---|
| 云台**未**饱和 | 63 | **`2.103 m`** |
| 云台饱和 | 566 | `36.271 m` |
| 目标几何可见 | 374 | `15.525 m` |
| 目标被遮挡 | 255 | `54.432 m` |

即**估计器本身在有可用指向时是好的（≈2 m）**，垮掉的是云台饱和/目标不可见的
那 84% 里程；而协方差始终报 `σ ≈ 1.2–1.4 m`，**在退化区间不作任何膨胀**。
这正是 M3′ 想证明的现象（臂 A 机身不动 → 云台饱和 → 覆盖与估计一起垮），
**对 trial 有效性零影响**；但它对**臂 B** 是设计输入：阈值式机身分配若消费
该估计或其协方差，就是在一个"自认为 1.3 m、实际 36 m"的量上做决策。
**本轮不据此改任何参数、阈值、协方差或 planner**（BC-BODY1-15 (d)），
只登记为臂 B 实现前与 M5 设计审查的必答项。

#### F. 未释放 / 未答复

- **其余 8 次 Play（臂 A trial 3/4/5 + 臂 B 五次）全部未授权**，每次仍需用户
  逐字 GO；本轮不申请。
- `--compare` 未运行、未授权；H1/H2 结论一律不得据 `n=2` 提前给出。
- COORD-007 §4.1 一帧下界缺口仍敞开（R10）；N12/N15/N18/N20/N21/N22 与
  revision 13/本轮更正的逐文件复核债继续挂账。

### Acceptance round 48 — 2026-08-13（arm A trial 3 GO 入账 + 操作单 revision 14）

Decision: **`A3_GO_LEDGERED_AWAITING_ARCHIVE_AND_PREPLAY_RECORD`**。用户逐字
「授权进行trail3」已入账；本轮发出操作单 **revision 14**。**本轮零 Play、零指标、
零代码、零阈值**，且 Play 尚未释放——四项前置未完成。

#### A. 采集 ID 机械核验（本轮实跑，零写入）

`canonical_trial_id('p1-m3-body-001-arm-a-trial-3')` 返回**同名**——该 ID
**从未被任何采集消耗**，canonical slot 即其自身，**不需要**替代 ID；
`_expected_policy()` 返回 `hold`（= 臂 A）；`expected_acquisition_ids('a')[2]`
逐字相等；两个 predecessor 门（A1/A2）**都不触发**；
`runtime/runs/p1-m3-body-001-arm-a-trial-3/` 当前不存在。
用户写的 "trail3" 按 arm A trial 3 读；若本意是 arm B trial 3 须明说（账本已
写明该保留）。

#### B. 操作单 revision 14

1. **槽位轮换**：§1 采集 ID 行、§3 步骤 4/5、§4 CLI 换为 A3；§2.7 转历史。
   §4 CLI 仍 **19 行**，与上一版**恰 1 行不同**（`--run-id`）；冻结值多重集
   比对**零丢失**。
2. **新增 §2.9 —— A2 的 post-run 归档合同**：A2 是**有效** trial，故走
   **valid-trial 命名空间**（A1 先例）：**A2 的 run 目录（11 份，含
   `m3_body_analysis.json`）绝对不动**，只把 shared 侧六项归入
   `runtime/test-results/…-attempt-2-post-run/`。移动前的计数与 SHA-256 由本轮
   实测钉住（`frames/` 257 项聚合 `5af3b4d3…6882`、truth 773 行
   `79378d22…c2f6`、metrics `194eebd7…5a8e`、body `223e7daf…5618`、
   gimbal `35c2f343…ccfd`、tracking `44f789e5…863d`），移动后须逐项相等，
   并**复跑 A2 `--verify`** 确认仍逐字返回其冻结 JSON。
3. **新增 §2.10 —— A3 的八项 Play 前只读核对**：六个 shared 文件缺席、
   `frames/` 为空、四处旧 hold 不变、**A1 与 A2 两个正式 run 目录各 11 份且
   `--verify` 各自逐字复现**、两处 post-run 归档各 6 项、八个活动标记缺席 +
   void hold 仍 10 份零隐藏项、A3 run 目录不存在。
4. **逐字不变**：§2.0 四步、三个硬门与阈值、完成握手、BC-BODY1-21/-22、
   BC-BODY1-29/-30、§5 四种 void 终态、CLI 其余 18 参数。

#### C. 发令前置（四项，缺一不可）

1. §2.9 归档执行并记录（实现角色；零 Play、零 ID）；
2. §2.10 八项只读核对全过（实现角色）；
3. §2.0 (b) 实现角色在最终干净 HEAD 上报告（基线运行时取最新
   `passed_candidate`）；
4. (c) 接受角色写 `docs/unity-test-log.md` → (d) 发令时唯一未提交差异。

#### D. 未释放

arm A trial 4/5 与 arm B 五次**全部未授权**，每次仍需用户逐字 GO；`--compare`
未跑、未授权；轮 47 §E 的估计器协方差诊断继续挂在臂 B 与 M5 设计审查，
**不得据此调参**（BC-BODY1-15 (d)）；COORD-007 §4.1/§4.2 仍属 R10。
revision 14 与轮 47 的操作单更正欠下一轮复核的逐文件覆盖。

### Acceptance round 49 — 2026-08-13（revision 14 具名处置 + §2.0 (c)）

Decision: **`RUNBOOK_REVISION_14_SLOT_ROTATION_AND_ADDED_CHECKS_NO_GATE_RELAXATION_REVIEW_DEBT_REGISTERED`**，
不阻断本次 Play；随后写入 §2.0 (c) 记录，释放 arm A trial 3 的**恰一次** Play。

#### A. 补上轮 48 缺的具名 disposition（实现角色 §O.5 第 1 条，指出得对）

轮 48 §D 把「revision 14 与轮 47 的操作单更正」登记为下一轮复核债，但**没有**
像轮 46 那样给出具名 token。实现角色如实退回而不自行套用上一轮的名字，处理
正确。本轮补齐，并**据实用不同的名字**——revision 14 与 revision 13 不同源：
revision 13 是被 BC-BODY1-28 第 4 步与 Review round 7 的 N25/N26/N27 **点名
要求**的，revision 14 只是**例行槽位轮换 + 新增核对**，没有哪条复核意见要求它。
故不复用 revision 13 的 token。

**不阻断的依据（本轮在当前 HEAD 复算）**：

1. **零冻结值改动**：与被复核通过的候选 `07bb8a4` 版比较，`130.0`/`31.25`/
   `62.5`/`212.9706`/`[2.000000, 10.000000)`/初始框四分数/`(177,195,77,73)`/
   `0.5645`/`0.95`/`106.4853` 计数**无一下降**；§4 CLI 仍 **19 行**，与被复核版
   **恰 1 行不同**（`--run-id`）。
2. **槽位轮换是冻结合同本身**：十个采集 ID 的表由 round 29/30 冻结并经复核；
   A3 用的就是表里的原始 ID，机械确认 canonical slot 即其自身、policy `hold`、
   索引 `[2]`、无 predecessor 门。轮换不引入任何新语义。
3. **方向单调**：§2.9 是**新增**的归档合同（把 A1 已执行过的做法写成可核对的
   钉住表），§2.10 是**新增**的八项只读核对（比上一轮多要一个 `--verify`）——
   两者都**只增停条件**，不放宽任何门。
4. **债务登记不消灭**：revision 14、轮 47 的 §3 步骤 2 更正与本轮 §A 一并欠
   下一轮复核的逐文件覆盖，挂在 `COORD-007` 行。

角色张力照旧披露：操作单由接受角色撰写、裁定亦由接受角色作出；缓解仍是事实
可重算、复核债保留、用户可推翻。

#### B. 接受角色对前置 1–3 的独立复算（只读，主工作树 `git status` 为空）

- **§2.9 归档**：`…-attempt-2-post-run/` **恰 6 项**；`frames/` **257** 项且
  聚合 SHA-256 = 轮 48 移动前钉住的 `5af3b4d3…6882`；truth/metrics/三个发布的
  SHA-256 **逐项相等**。移动前后字节不变，得证。
- **A2 未受归档影响**：A2 `--verify` 退出 0 并逐字返回
  `WITHIN_RANGE / 0.5783188398250908 / 1.0`；A1 `--verify` 同样逐字复现。
- **现场**：A1 run 11 份、A2 run 11 份、attempt-1 void hold 10 份、四处旧 hold
  `257/93/109/257`、attempt-3 run hold 恰两文件、八个具名活动标记全不存在、
  六个 shared 文件全部缺席、`runtime/frames/` **0 项**、
  `runs/p1-m3-body-001-arm-a-trial-3/` **不存在**。
- 与实现角色 §O.1/§O.2 的 57/57 结论一致，无出入。

#### C. §2.0 (c) 与释放

(a) GO 已入账并提交；(b) 实现角色在干净 HEAD 报告完毕；本轮 §A/§B 处置后写入
`docs/unity-test-log.md`（写入时点自取 HEAD 与 `git status --porcelain`），
(d) 由发令方核对。**释放 arm A trial 3 的恰一次 Play。**

#### D. 未释放

arm A trial 4/5 与臂 B 五次全部未授权；`--compare` 未跑；轮 47 §E 的估计器
协方差诊断继续挂在臂 B 与 M5 设计审查，**不得据此调参**（BC-BODY1-15 (d)）；
COORD-007 §4.1 的一帧下界缺口仍敞开（R10）。

### Acceptance round 50 — 2026-08-13（arm A trial 3 归因 = 有效 A3；trial 4 GO + revision 15）

Decision: **`ACCEPTED — A3_VALID_TRIAL`**（arm A **3/5**）+
**`A4_GO_LEDGERED_AWAITING_ARCHIVE_AND_PREPLAY_RECORD`**。

#### A. 归因：A3 有效（接受角色独立复算）

- **`--verify` 本角色亲自复跑**：退出 **0**，逐字返回
  `{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116,
  "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true,
  "window_c_track_given_geom": 1.0}`。
- **身份链**：`run_id` 即 canonical slot（A3 无 attempt 后缀，故 receipt 中
  **正确地没有** `acquisition_run_id`/`attempt_number`/predecessor 三键——
  那是 A1/A2 专属的条件式块，与 BC-BODY1-27 的"不得使其他 run 序列化变化"
  一致）；六个冻结 SHA、`body_policy=hold`、`planner=hold-v1`、`condition=follow`、
  `init_frame_id=0` 全部相符。
- **三门与握手**（证据 §P，本角色复核记录）：门 1 由保留帧机械导出且两侧余量
  各约 `2.183 s` / `5.817 s`；门 2 最低帧 `0`；门 3 用户目检「匹配」；tracker
  自然退出 `0`、只读 validator 逐字产出 `TRACKER_AUTO_COMPLETE_CONFIRMED`、
  Console 无报错；绑定分析 PASS，两条域完整性门未触发。
- **BC-BODY1-29 继续生效**：post-tracker 停留 **`19.800354 s`**（A2 `24.42 s`，
  作废那次 `252.4 s`）。
- 不匹配任何 void 终态 → **计为 canonical slot `p1-m3-body-001-arm-a-trial-3`
  的有效 trial**，与 B3 配对。arm A 现 **3/5**。

#### B. 结果并列与**一个重要的新观察**（描述性，非正式 compare）

| 量 | A1 | A2 | **A3** |
|---|---|---|---|
| 整圈 `C_geom` | `0.5784550773737355` | `0.5783188398250908` | **`0.597146417669116`** |
| 窗口 `C_track\|geom` | `1.0` | `1.0` | `1.0` |
| 中心误差中位数 px | `59.053` | `45.317` | `45.202` |
| 整圈云台饱和占比 | `0.8394082` | `0.8393871` | `0.8393964` |
| effort / path / 切换 | `0/0/0` | `0/0/0` | `0/0/0` |
| 整圈样本数 | `529` | `530` | `529` |

**A1 与 A2 相差 `1.36e-4`，A3 与它们相差约 `0.019`——约 140 倍。** 本角色按
COORD-005 诊断通道只读定位了差异位置（**诊断，不进门、不改任何值**）：把首圈
按里程分十档统计几何可见占比，**九档三次采集完全相同**，全部差异集中在
**第 6 档**（里程 60–70%）：A1 `0.426` / A2 `0.415` / **A3 `0.604`**。

进一步排除了一个明显嫌疑：三次采集的**机体位置逐字相同且全程恒定**
（`(132.0, 25.2, 117.0)`，distinct positions = 1），故差异**不是**机身姿态或
"hold 起点随暂停时刻漂移"造成的。剩下的解释指向该处遮挡边界的**采样相位**
（本项目已披露遮挡评估是采样/射线式、且无固定时间步）。

**这条对研究是要紧的**：arm A 在主指标上的 trial 间波动不是均匀噪声，而是
**集中在一个遮挡过渡区**；H1/H2 若要区分臂 A 与臂 B，其功效取决于该边界怎么
被采样。登记为 **M5 设计审查与 compare 口径设计的必答项**。
**本轮不据此改任何阈值、样本域、载体或采集协议**（BC-BODY1-15 (d)）；
n=3 不支持任何方差或显著性主张。

（轮 47 §E 的估计器协方差诊断继续挂账：A3 的 `nees_median` = `1016.64`、
`nis_median` = `0.110`，与 A1/A2 同量级偏离，结论不变。）

#### C. trial 4 授权与 revision 15

- 用户「授权trail4」逐字入账。机械确认 `p1-m3-body-001-arm-a-trial-4` 是自身
  canonical slot、policy `hold`、索引 `[3]`、**从未消耗、无 predecessor 门**、
  run 目录不存在。**恰一次** Play；arm A trial 5 与臂 B 五次仍未授权。
- **revision 15**：槽位轮换（CLI 仍 19 行只差 `--run-id`，冻结值零丢失）；
  新增 **§2.11**（A3 的 post-run 归档合同，移动前计数/SHA 由本轮实测钉住，
  移动后须逐项相等并复跑 A3 `--verify`）与 **§2.12**（七项 Play 前核对，现在要
  `--verify` **三个**有效 run）。§2.10 转历史。
- 处置同 revision 14：
  `RUNBOOK_REVISION_15_SLOT_ROTATION_AND_ADDED_CHECKS_NO_GATE_RELAXATION_REVIEW_DEBT_REGISTERED`
  ——例行轮换 + 只增停条件，零冻结值改动；**复核债登记不消灭**。

#### D. 发令前置与未释放

前置四项：§2.11 归档 → §2.12 全过 → §2.0 (b) → (c)/(d)。
未释放：arm A trial 5、臂 B 五次、`--compare`、任何调参；COORD-007 §4.1 缺口
仍在（R10）；revision 14/15 与轮 47/50 的操作单改动欠下一轮复核。

### Acceptance round 51 — 2026-08-13（A4 发令前置复算 + §2.0 (c) 放行；**轮 56 补记**）

> **补记声明（2026-08-14，接受轮 56，应 Review round 8 N29）**：轮 51 当时
> 只提交了状态板批次而未在提案写节，属遗漏；本节由接受角色依一手记录补写
> ——轮 51 批次提交 `36a9914`（仅状态板）的完整提交信息与状态板 Log（已
> 压缩条目）。补记不改变任何当时裁定；已冻结的 trial-4 (c) 事前记录
> （`docs/unity-test-log.md`）一字未动，其「rounds 50/51」引用自此不再悬空。

Decision（当时裁定）: **`A4_PREPLAY_RECORDED_ONE_PLAY_RELEASED`**。零 Play、
零代码、零阈值；释放的是**恰一次** Play（arm A trial 4）。

- **接受角色独立复算（只读，主工作树 `git status` 为空）**：§2.11 归档——
  A3 post-run 恰 6 项，五个文件 SHA-256 与 `frames/` 257 项聚合 SHA 与轮 50
  移动前钉住值逐项相等，A3 正式 run 目录一字节未动（仍 11 份）；三个有效
  run 的 `--verify` 全部退出 0 且逐字复现 `0.5784550773737355` /
  `0.5783188398250908` / `0.597146417669116`；现场——三个 run 目录各 11 份、
  void hold 10 份、四处旧 hold `257/93/109/257`、八个具名标记缺席、六个
  shared 文件缺席、`runtime/frames/` 0 项、`runs/p1-m3-body-001-arm-a-trial-4/`
  不存在。与实现角色 §2.12 的 **67/67 无出入**。
- **实现角色交回项**：revision 15 的具名 disposition **轮 50 §C 已给**
  （`RUNBOOK_REVISION_15_SLOT_ROTATION_AND_ADDED_CHECKS_NO_GATE_RELAXATION_
  REVIEW_DEBT_REGISTERED`），确认无需补发；PLAY_GOVERNING 仍恰 1 条（操作单
  自身），逐文件复核债继续挂账（后由复核轮 8 清偿，代之以具名 finding）。
- **§2.0 (c)**：本轮写入 `docs/unity-test-log.md` 并按 (d) 契约保持未提交
  贯穿 Play，事后代录入库；随后 A4 执行并由轮 52 判为有效。

### Acceptance round 52 — 2026-08-13（arm A trial 4 归因 = 有效 A4；A4 归档合同）

Decision: **`ACCEPTED — A4_VALID_TRIAL`**（arm A **4/5**）+ 操作单 **revision 16**
（**只**加 §2.13 归档合同，**不做槽位轮换**——A5 无 GO）。

#### A. 归因：A4 有效（接受角色独立复算，只读）

- **`--verify` 亲自复跑**：退出 **0**，逐字返回
  `{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214,
  "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": true,
  "window_c_track_given_geom": 1.0}`。
- **身份链**：`run_id` 即 canonical slot；receipt **正确地不含** attempt/
  predecessor 三键（A4 非替代 ID，与 BC-BODY1-27 的"不得使其他 run 序列化变化"
  一致，这是第二个独立确认该条的 run）；六个冻结 SHA、`hold`/`hold-v1`/
  `follow`/`init_frame_id 0` 全部相符。
- 不匹配任何 void 终态 → **计为 canonical slot `p1-m3-body-001-arm-a-trial-4`
  的有效 trial**，与 B4 配对。arm A 现 **4/5**。

#### B. F2 在本轮**实打实救回了一次采集**（据实记账）

A4 的 `final_unwrapped_mileage_m = 690.7031448290135` = **3.2432 圈**，truth
**1718** 条。**在接受轮 42 撤下 `>= 2P`（= `425.9412 m`）之前，这次 trial 会被
`trial_invalid_no_single_loop` 直接判废**——正是 attempt-1 那次的死法。
撤下上界之后它是有效 trial，且 `[0, P)` 样本域保证第二圈及以后一个样本都没进
H1（`loop_frame_count = 530`，与 A2 相同）。这是对 G1=F2 那次授权的**事后验证**：
不是理论上的宽松，而是四次采集里已经有一次真的落在旧上界之外。

（对照：三次已归档采集的圈数为 `1.9385`/`1.4585`/`1.4171`，A1 当年距 `2P`
只剩 `6.550 s`。Play 时长本来就不受协议约束，波动范围已实测跨越 `1.42`–`3.24` 圈。）

#### C. 四次臂 A 的并列 + 遮挡边界发现的**加强版**（描述性，非正式 compare）

| 量 | A1 | A2 | A3 | **A4** |
|---|---|---|---|---|
| 整圈 `C_geom` | `0.5784550773737355` | `0.5783188398250908` | `0.597146417669116` | **`0.5783206310103214`** |
| 窗口 `C_track\|geom` | `1.0` | `1.0` | `1.0` | `1.0` |
| 整圈云台饱和占比 | `0.8394082` | `0.8393871` | `0.8393964` | `0.8393814` |
| effort / path / 切换 | `0/0/0` | `0/0/0` | `0/0/0` | `0/0/0` |
| 整圈样本数 | `529` | `530` | `529` | `530` |

**A4 与 A2 相差 `1.8e-6`**；A1/A2/A4 三次聚成一簇（跨度约 `1.4e-4`），
**只有 A3 高出约 `0.019`**。轮 50 的十档诊断在 n=4 下复算，结论从"差异集中在
第 6 档"加强为**更尖锐的一条**：

| 档（里程 60–70%） | A1 | A2 | A3 | A4 |
|---|---|---|---|---|
| 几何可见占比 | `0.426` | `0.415` | **`0.604`** | `0.415` |

其余九档四次采集**完全相同**；四次的机体位置**逐字相同且恒定**
`(132.0, 25.2, 117.0)`（distinct = 1）。即：**臂 A 的主指标不是连续抖动，而是
在同一个遮挡过渡区上"多数落在 0.415–0.426、偶尔跳到 0.604"**——四次里出现一次。

**这条对 M5 与 compare 口径更要紧了**：若臂 B 的真实效应量小于这一次跳变
（`~0.019`），五次/臂的中位数配对差可能被这种**离散跳变**主导。登记为 M5 设计
审查与 compare 口径设计的**必答项**；n=4 仍不支持任何方差/显著性主张，本轮
**不改任何阈值、样本域、载体或采集协议**（BC-BODY1-15 (d)）。

（估计器协方差诊断继续挂账：A4 `nees_median = 842.91`、`nis_median = 0.00594`，
与 A1/A2/A4 同量级，A3 的 `0.110` 是 NIS 上的离群——一并交 M5 审查。）

#### D. revision 16：只加归档合同，不轮换槽位

用户「归档」指 A4 的 shared 侧六项。§2.13 冻结 source→destination 与移动前的
计数/SHA-256（`frames/` 257 项聚合 `281bb6d8…3b2c`、truth **1718 行**
`f9c1a488…e360`、metrics/body/gimbal/tracking 四个哈希），要求移动后逐项相等、
复跑 **四个** `--verify`、只重建空 `frames/`、**不得预建任何 run 目录**。
**A4 的 run 目录不动。** 执行者是实现角色。

**本轮不轮换采集 ID**：arm A trial 5 与臂 B 五次**都没有 GO**，在拿到逐字授权
之前 §1/§3/§4 的 ID 一律不动——否则操作单会指向一个未获授权的采集。

#### E. 未释放

arm A trial 5、臂 B 五次、`--compare` 全部未授权；两条诊断发现继续挂在臂 B 与
M5 设计审查；COORD-007 §4.1 缺口仍在（R10）；revision 13–16 与轮 47/50 的操作单
改动欠下一轮复核的逐文件覆盖。

### Acceptance round 53 — 2026-08-13（arm A trial 5 GO 入账 + 操作单 revision 17）

Decision: **`A5_GO_LEDGERED_AWAITING_PREPLAY_RECORD`** + 操作单 **revision 17**
（槽位轮换到 `p1-m3-body-001-arm-a-trial-5`，新增 §2.14 Play 前核对）。
本轮**零 Play、零 ID 消耗、零代码、零阈值**。

#### A. 授权读法（入账，不替用户扩权）

用户原话 **「授权第五次trail」** 已逐字记入 `docs/authorizations.md`。按最窄读法：
**恰好一次** Play，采集 ID **`p1-m3-body-001-arm-a-trial-5`**（臂 A 第 5 次，收尾
臂 A）。理由：臂 A 现 4/5，臂 B 一次未跑，"第五次 trial" 在本 work item 里只有
臂 A trial 5 一个所指；轮 52 §E 与状态板列出的二选一也正是"trial 5 或臂 B 第一次"。
**若用户本意是臂 B，须明说**——账本已写明该保留。

**明确未授权**：臂 B 五次、任何重试/重进/调参、`--compare`（需十次齐备并另行
授权）、任何协议/指标/阈值/测量窗/载体改动、R10/R11、R12。**收尾臂 A 不附带
任何后续授权**：trial 5 结束后仍按 §3 步骤 6 回本角色归因。

#### B. 接受角色独立机械复算（只读，58 条全 PASS）

**槽位（10 条）**：`canonical_trial_id('…trial-5')` 返回同名（**从未被消耗，
canonical slot 即其自身，无需替代 ID**）；`_expected_policy()` 返回 **`hold`**；
`expected_acquisition_ids('a')` 逐字为
`[…trial-1-attempt-4, …trial-2-attempt-2, …trial-3, …trial-4, …trial-5]`，索引
`[4]` 相等；A5 既非 A1 也非 A2 的替代采集 ID，故**两个 predecessor 门都不触发**；
两个旧 canonical ID 仍抛 `run_id_void_consumed`；`…trial-5-attempt-2` 抛
`run_id_not_frozen_trial`；`frozen_run_id('a',5)` 与 `TRIALS_PER_ARM = 5` 相符。

**现场（44 条）**：六个 shared 文件全缺席；`runtime/frames/` 0 项；四处旧 hold
`257 / 93 / 109 / 257`，attempt-3 的 run hold 仍恰两文件；**四个正式 run 目录各
恰 11 份**；**四处 post-run 归档各恰 6 项**，`frames/` 各 257 项、四个目录聚合
SHA-256 依次 `ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` /
`281bb6d8…3b2c`（口径见 `…-arm-a-trial-2.md` §B.3），A4 侧另比对五个文件的
行数/字节/SHA-256 与轮 52 钉住表**逐项相等**（truth **1718** 行 / `1755300` 字节
/ `f9c1a488…e360`）；八个具名标记全缺席；attempt-1 void hold 仍**恰 10 份、零
隐藏项**且三个钉住 SHA 相等；**`runtime/runs/p1-m3-body-001-arm-a-trial-5/`
不存在**（create-once 前置）。

**`--verify`（4 条）**：四个有效 run 全部退出 0 且逐字复现
`0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` /
`0.5783206310103214`，`disposition` 均 `WITHIN_RANGE`、窗口 `1.0`。

批次开始时 `git status --porcelain` 为空，HEAD = `33d3dc5`。核对脚本只做
`open(...,'rb')`/`stat` 与只读 CLI，中间文件全部落在会话 scratchpad。

#### C. revision 17 的具名处置

**`RUNBOOK_REVISION_17_SLOT_ROTATION_AND_ADDED_CHECKS_NO_GATE_RELAXATION_REVIEW_DEBT_REGISTERED`**
——与 revision 14/15 同类（例行轮换 + 只增停条件），不复用 revision 13 的 token。
不阻断依据（本轮实测）：CLI 代码块与 revision 16 逐行比对**恰 1 行不同**
（`--run-id`，18 参数行零改动）；全部冻结值 token 计数**零丢失**（暂停窗两端、
初始框四分数与 `(177,195,77,73)`、`212.9706`、`130.0`、`62.5`/`31.25`、
scenario 与可见弧三个 SHA-256 均在）；新增的 §2.14 只增停条件，不放宽任何门。
**复核债登记不消灭**：revision 13–17 与轮 47/50/52/53 的操作单改动继续挂在下一轮
逐文件复核。

**本轮无归档待办**：§2.13（A4 的 post-run 归档）已由上一批次执行完毕并转历史，
故 revision 17 的发令前置从四项减为**两项**：§2.14 全过 → §2.0 (b) → (c)/(d)。

**同批次就地更正四处失效标注（零语义改动）**：§2.8/§2.9/§2.11 的标题仍写"待执行 /
本轮第一步"而三者早已执行完毕，§4 标题与括注仍写"本轮 = 臂 A trial 2 / revision 12
已换为 A2"。留着会让实现角色误判本轮还有归档待办——正是 AGENTS.md「交接文字必须
与现实一致 …… 不留给下一个接手的角色」点名的那类漂移。**不改任何参数值、阈值、
哈希或动作内容**，四处均加指向证据（§K/§O.1/§R.1）的历史标注。

#### D. 交回与未释放

下一步在**实现角色**：执行 §2.14 七项只读核对与 §2.0 (b)，报告 HEAD、空工作树、
基线归因（`<BASE>` 运行时取 `docs/reviews/P1-M3-BODY-001.md` 最新
`passed_candidate:`）与步骤 0 预检的退出码与完整 JSON，然后交回本角色写 (c)。
**在 (c) 落盘之前不得进 Play。**

未释放：臂 B 五次、`--compare`、任何调参；两条诊断发现（估计器协方差；单档
`C_geom` 离散跳变）仍只是臂 B 与 M5 设计审查的输入，BC-BODY1-15 (d) 继续禁止据此
调参；COORD-007 §4.1 一帧下界缺口仍在（R10 未授权）；**n=4 仍不支持任何主张**，
trial 5 完成后 arm A 满 5/5 也**不**自动释放 `--compare`。

### Acceptance round 54 — 2026-08-13（A5 发令前置复算 + §2.0 (c) 放行）

Decision: **`A5_PREPLAY_RECORDED_ONE_PLAY_RELEASED`**。本轮零 Play、零代码、
零阈值；释放的是**恰一次** Play。

#### A. 接受角色独立复算（只读，58/58 PASS，与实现角色 77/77 无出入）

实现角色在 `32eb44a` 报告 §2.14 七项 = **77 条全 PASS** 与 §2.0 (b)（证据
`…-arm-a-trial-2.md` §V）。本角色在当前 HEAD 用自己的脚本重跑：六项 shared 缺席、
`frames/` 0 项、四处旧 hold `257/93/109/257`（attempt-3 run hold 仍恰两文件）、
**四个 run 目录各 11 份**、**四处归档各 6 项**且四个 `frames/` 聚合 SHA 依次
`ea9ba050…` / `5af3b4d3…` / `505b94df…` / `281bb6d8…`（口径 §B.3）、八标记缺席、
void hold 10 份零隐藏 + 三钉住 SHA、**A5 run 目录不存在**；**四个 `--verify` 全部
退出 0 且逐字复现**。槽位十项（含两个 predecessor 门均不触发）同轮 53 §B 结论。
**两侧结论一致，无一项出入。**

#### B. 实现角色交回的四项，逐条处置

1. **PLAY_GOVERNING = 恰 1 条**（操作单自身，现 revision 17）：本角色实测确认，
   基线 `07bb8a4…` 起的 8 条 delta 全是文档路径，**测量侧 diff 为空**（自 Review
   round 7 的候选起代码与 config 一个字节未动，A1…A4 与即将进行的 A5 跑在同一份
   已复核代码上）。其具名 disposition **轮 53 §C 已给**
   （`RUNBOOK_REVISION_17_SLOT_ROTATION_AND_ADDED_CHECKS_NO_GATE_RELAXATION_
   REVIEW_DEBT_REGISTERED`），本轮确认无需补发。
2. **测量时点 HEAD ≠ 发令时点 HEAD**：接受，(c) 的 HEAD/`porcelain` 由本角色在
   写入时点自取（本轮批次提交之后），不沿用 `cd66f85`。
3. **§2.14 发令时刻复查**：接受，本轮的 58 条即在本批次提交后的最终 HEAD 上复跑。
4. **A5 无前驱门**、**本批不申领 `UNITY_NA`**、**A5 是臂 A 最后一次但不释放
   `--compare`**：三条均如实，照录进 (c)。

#### C. §2.0 四步与放行

(a) PASS（轮 53 入账并提交）、(b) PASS（`32eb44a`，§V）、**(c) 本轮写入
`docs/unity-test-log.md`**，(d) 由发令时刻核对——工作树只允许 (c) 这一份未提交
差异，故 (c) 记录**保持未提交**直到 Play 结束后另行代录入库（沿轮 49/51 先例）。
**释放 arm A trial 5 的恰一次 Play。**

BC-BODY1-21 自 (c) 落盘起生效：任何角色在本次 Play 结束前**不得再动操作单**；
Play 中发现歧义按 BC-BODY1-22 fail closed 回本角色。

#### D. 带进本次 Play 的既有限制（一条不放宽）

臂 B 五次与 `--compare` 无 GO；**任何已见数字都不得据以调参**（BC-BODY1-15 (d)）；
四种 void 终态各消耗这一次 one-Play GO，失败即保全现场回本角色；COORD-007 §4.1
的一帧下界缺口仍敞开且**不因此调整暂停窗**；两条诊断发现仍只是臂 B 与 M5 设计
审查的输入；**revisions 13–17 与轮 45/46/47/48/50/52/53 的操作单改动仍欠一轮逐文件
复核**（`07bb8a4..HEAD` 该文件 440 插入 / 28 删除），本轮不消灭该债。

### Acceptance round 55 — 2026-08-13（arm A trial 5 归因 = 有效 A5；**臂 A 5/5 收官**）

Decision: **`ACCEPTED — A5_VALID_TRIAL`**（arm A **5/5 COMPLETE**）+ 操作单
**revision 18**（**只**加 §2.15 归档合同，**不做槽位轮换**——臂 B 无 GO）。

#### A. 归因：A5 有效（接受角色独立复算，只读）

- **`--verify` 亲自复跑**：退出 **0**，逐字返回
  `{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783243208518966,
  "run_id": "p1-m3-body-001-arm-a-trial-5", "verified": true,
  "window_c_track_given_geom": 1.0}`。
- **身份链**（本角色直接读 run 目录内的 receipt）：`run_id` 即 canonical slot；
  receipt **正确地不含** attempt/predecessor 任何键（第三个独立确认 BC-BODY1-27
  的 run）；`body_policy=hold`、`planner=hold-v1`、`condition=follow`、
  `init_frame_id=0`；`scenario_sha256=f9c92052…2ce3`、`visible_arc_sha256=
  4fe2eea5…df55`、`margin_artifact_sha256=c72c9407…576d`、两个 tracker 模型 SHA
  与预检值全部相符；`input_sha256.m3_body_truth_jsonl` 与磁盘上待归档的 truth
  字节**逐字相等**。run 目录**恰 11 份**。
- **三门与握手**（证据 §W/§X，本角色复核记录）：门 1 `reported_sim_t =
  5.582472801208496` 由保留帧 0–27 机械导出、两侧余量约 `3.582 s` / `4.418 s`；
  门 2 最低帧 `0`；门 3 用户目检「匹配」；步骤 0′ 两步逐字相等（CLI 19 行只有
  `--run-id` 与臂 A 前四次不同）；tracker 自然退出 0、652 帧，只读 validator 产出
  `TRACKER_AUTO_COMPLETE_CONFIRMED`，用户随即退出且 Console 无报错；绑定分析
  PASS，两条域完整性门零触发，`loop_frame_count = 530`、`window_frame_count = 155`。
- **BC-BODY1-30 披露（不判定）**：post-tracker 停留 **`15.800308 s`**（五次里最短），
  实测圈数 **`1.379524`**。
- 不匹配任何 void 终态 → **计为 canonical slot `p1-m3-body-001-arm-a-trial-5`
  的有效 trial**，与 B5 配对。**臂 A 5/5 完成。**

#### B. 臂 A 五次并列 + 遮挡边界发现的 n=5 版本（描述性，非正式 compare）

| 量 | A1 | A2 | A3 | A4 | **A5** |
|---|---|---|---|---|---|
| 整圈 `C_geom` | `0.5784550773737355` | `0.5783188398250908` | `0.597146417669116` | `0.5783206310103214` | **`0.5783243208518966`** |
| 窗口 `C_track\|geom` | `1.0` | `1.0` | `1.0` | `1.0` | `1.0` |
| 整圈云台饱和占比 | `0.8394082` | `0.8393871` | `0.8393964` | `0.8393814` | `0.839396` |
| effort / path / 切换 | `0/0/0` | `0/0/0` | `0/0/0` | `0/0/0` | `0/0/0` |
| 整圈样本数 | `529` | `530` | `529` | `530` | `530` |
| post-tracker 停留 s | — | `24.422043` | `19.800354` | `213.198013` | `15.800308` |

**十档几何可见占比（本角色本轮重算，n=5）**——这是本轮最要紧的一条：

| 里程档 | 1 | 2 | 3 | 4 | 5 | **6（60–70%）** | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | `1.000` | `1.000` | `1.000` | `0.889` | `0.472` | **`0.426`** | `1.000` | `0` | `0` | `0` |
| A2 | `1.000` | `1.000` | `1.000` | `0.887` | `0.472` | **`0.415`** | `1.000` | `0` | `0` | `0` |
| A3 | `1.000` | `1.000` | `1.000` | `0.887` | `0.472` | **`0.604`** | `1.000` | `0` | `0` | `0` |
| A4 | `1.000` | `1.000` | `1.000` | `0.887` | `0.472` | **`0.415`** | `1.000` | `0` | `0` | `0` |
| **A5** | `1.000` | `1.000` | `1.000` | `0.887` | `0.472` | **`0.415`** | `1.000` | `0` | `0` | `0` |

**九档五次完全相同**（第 4 档 A1 的 `0.889` 与其余四次的 `0.887` 是 529/530 样本
数之差，非现象），**全部 trial 间差异仍只落在 60–70% 那一档**：四次 `0.415`
（A1 `0.426`），**A3 一次 `0.604`**。五次的机体位置**逐字相同且恒定**
`(132.0, 25.2, 117.0)`（distinct = 1）。

**新增的一条相关证据（诊断，不进门）**：估计器 `nis_median` 为
A1 `0.00739` / A2 `0.00625` / **A3 `0.11001`** / A4 `0.00594` / A5 `0.00472`
——**A3 在 NIS 上是约 20 倍的离群，与它在 `C_geom` 上的离群是同一次采集**。
两个互不相干的量在同一次 trial 上同时跳变，把"这是该遮挡边界上的采样相位问题"
从猜测提升为**有第二个独立指标支持的假设**。`nees_median` 五次为
`844 / 836 / 1017 / 843 / 832`，对 3 自由度而言全部离谱地高——估计器协方差发现
**在 n=5 上继续成立且未被证伪**。

**据实写明这对研究意味着什么**：臂 A 的主指标不是连续抖动，而是**五次里四次落在
`1.4e-4` 的带内、一次跳高 `~0.019`**。若臂 B 的真实效应量小于这一次跳变，五次/臂
的中位数配对差**可能被这种离散跳变主导**。这不是可以靠"多跑几次"随手解决的问题
——它是 H1/H2 功效的结构性约束。**登记为 M5 设计审查与 compare 口径设计的
必答项**；**本轮不据此改任何阈值、样本域、载体或采集协议**（BC-BODY1-15 (d)），
n=5 且只有臂 A，仍不支持任何方差/显著性主张。

#### C. revision 18：只加归档合同，不轮换槽位

§2.15 冻结 source→destination 与移动前的计数/SHA-256（`frames/` 257 项聚合
`9dc67a76…a62b`、truth **731 行 / 751891 字节** `a93ca5e0…80eb`，metrics/body/
gimbal/tracking 四个哈希），要求移动后逐项相等、复跑**五个** `--verify`、只重建空
`frames/`、**不得预建任何 run 目录**；destination 本角色实测**当前不存在**。
**A5 的 run 目录不动。** 执行者是实现角色。处置
`RUNBOOK_REVISION_18_ARCHIVE_CONTRACT_ONLY_NO_SLOT_ROTATION_NO_GATE_RELAXATION_
REVIEW_DEBT_REGISTERED`。

**本轮不轮换采集 ID**：臂 B 五次**都没有 GO**。并预先写明一条容易被漏掉的事实：
臂 B 的修订不止换 ID，还必须把 §1 臂位行与 §4 CLI 的 `--body-policy` 从 `hold`
换成 `threshold`，并在发令前置里核对 `_expected_policy()` 返回 `threshold`——
已写进 revision 18 的抬头，避免下一轮照抄臂 A 的轮换动作。

#### D. 未释放 / 仍欠

- 臂 B 五次 Play、`--compare`（需十次齐备并单独授权）、任何调参、任何重跑：
  **全部无 GO**。**臂 A 满 5/5 本身不释放任何东西**——H1/H2 是配对设计，只有
  臂 A 的五次不能产出任何主张。
- **复核债照旧且已增大**：revisions 13–18 与轮 45/46/47/48/50/52/53/55 的操作单
  改动仍欠一轮逐文件独立复核；本轮登记不消灭。
- COORD-007 §4.1 一帧下界缺口仍敞开（R10 未授权）；两条诊断发现继续只作臂 B 与
  M5 设计审查的输入。

### Acceptance round 56 — 2026-08-14（消费 Review round 8：finding 复判 + 返工落地 + 轮 51 补记）

Decision: **`REVIEW_ROUND8_CONSUMED_REWORK_APPLIED`**。三条 CLASS_2 复判
**同意维持 CLASS_2** 并由本角色（操作单作者）修正文本；三条 CLASS_3 复判
**同意 CLASS_3** 并按逐字补丁同轮应用（workflow §4.4 R4）；另自查两处同类
失效文字同批修正并披露（F5b/F6b）。**零 Play、零 ID、零代码、零阈值、零冻结
值改动；操作单 revision 号不变**（沿轮 46 勘误/轮 47 更正先例）。复核轮 8
verdict 明文不推翻的事项（A1–A5 有效性、轮 55 归因、revisions 13–18 零门
放宽主张、§2.15 可执行性）本轮一律不重开。

#### A. CLASS_2 复判（逐条独立核实，非转录复核报告）

1. **F4 —— 同意 CLASS_2**。独立复算：复核文件现**恰一行** `passed_candidate:`
   （round 7，文件末尾）；`grep -m1` 语义 = 文件序**第一个**匹配（本轮实测
   两行样例取旧行），复核轮只追加 → 第二行落盘之时例示恒取**最旧**，与规范句
   「最新一行」相反；A5 的 (c) 记录证明例示被逐字执行，行为面成立。不改任何
   已记录数字/结论 → 非 CLASS_1；操作员行为会因此文字而不同 → 不得降
   CLASS_3。**修正**：例示改 `grep '^passed_candidate:' … | tail -1` 并注明
   缘由；规范句逐字未动（操作单 §2.0 (b)）。
2. **F5 —— 同意 CLASS_2**。对照轮 42 BC-BODY1-26 原文（「其余**八**个采集 ID
   逐字不变」）：§1「acquisition IDs」行的「其余九个等于 canonical slot」对
   A2 为假，fail-closed 方向（按它推导会得被 `run_id_void_consumed` 拒绝的旧
   ID）但会误导 PLAY_GOVERNING 文档自身的臂 B/compare 起草。**修正**：A1、A2
   双替代 + 「其余八个」，A2 附拒绝语义与 BC-BODY1-26 依据。**自查 F5b
   （同类）**：§1「A1 采集 ID（唯一替代）」行的「唯一」与「其余九个 ID 逐字
   不变」同样违 BC-BODY1-26（复核轮 8 未点名；AGENTS.md 失效文字同批就地修正
   义务）——去「唯一」，尾句改指「acquisition IDs」总表行，避免同一事实三处
   重复漂移。历史修订块（revision 11 抬头 C2 等）如实保留**不回改**。
3. **F6 —— 同意 CLASS_2**。独立读码核实：`analyze_trial` 中两个前驱门在
   `if verify:` 分支**之前**无条件执行（A2 → `_check_a2_predecessor_hold`，
   hold 缺失即 `a2_predecessor_hold_missing` fail-closed），与复核轮 8 的移开/
   恢复探针一致；§1 真值载体行「其余九个只读 run 目录」对 A2 为假，且 §2.15
   即将复跑五个 `--verify`，误诊断面（A2 失败被误归 run 目录损坏）真实存在。
   **修正**：A1/A2 各另读其 predecessor hold，其余八个只读 run 目录。**自查
   F6b（同类）**：§3 步骤 5 的同一声明同步修正（A1/A2 双 hold 路径 +
   「其余八个」）。

#### B. CLASS_3 复判与同轮应用

三条均属 R4 闭集成员；应用后逐条核对**零数字、零哈希、零 run ID、零
disposition 改动**：

- **P1 —— 同意 CLASS_3（已执行步骤的时态）**：§1 A5 行的「本轮/从未被消耗」
  是发令前措辞残留；双重围栏（§5 revision 18 执行前提「当前没有任何已授权的
  Play」+ run 目录 create-once 机械拒绝）使其无法转化为错误 Play，不升格。
  复核补丁逐字应用（行首「上一采集 ID（…已执行并于接受轮 55 判为有效）」+
  「发令前从未被任何采集消耗（现已被该次有效采集消耗…）」）。
- **P2 —— 同意 CLASS_3（同类时态）**：§4 抬头与尾注逐字应用；CLI 19 行参数块
  一字未动。
- **P3 —— 同意 CLASS_3（失效链接）**：§2.6 属已执行历史节，残留行号钉
  `analyze_m3_body.py:1368-1373` 现指向无关代码，仅审计误导；revision 13
  抬头 F 的三处去钉声明由此补全为 3/3。逐字应用。

#### C. Review round 8 notes 的处置

- **N29 —— 已处置**：轮 51 节已按一手记录（批次提交 `36a9914` 提交信息 +
  状态板 Log）补记入本提案，补记声明随节写明；冻结的 (c) 记录一字未动。
- **N30 —— 登记不动**：`tools/analyze_m3_body.py` docstring 的过期 verify
  声明属实现代码，本角色无权触碰；随下一个获授权的代码批次修复（届时按
  §4.4 R1 自动入复核范围）。
- **N31 —— 决定不入账，维持现状**：授权账本按 AGENTS.md 只收**关键授权**
  （GO/NO-GO、范围/协议变更、消耗性资源动用、里程碑关闭）；「trail4已经结束，
  归档」类话语只触发零消耗归档/判定动作，修订抬头已用「用户「…」」与「用户
  GO「…」」区分记载。把非关键话语入账会稀释「账本没有 = 未发生」的语义
  边界，故不采纳；用户如愿统一入账可随时改令。
- **N32 —— 无残留**：复核轮 8 已就地更正状态板失效文字；本轮另更正 gate
  board Overall 列一处同类失效（「await an archive contract」→ 合同已由
  revision 18 写就，待的是 §2.15 执行）。

#### D. 处置名、闭合路径与未释放

- 本批操作单 delta 的具名处置（供下一次 §2.0 (b) 归因引用）：
  `RUNBOOK_ROUND8_REWORK_TEXT_ALIGNMENT_TO_BC26_BC27_R7_NO_GATE_RELAXATION_
  CLOSURE_BY_TARGETED_REINSPECTION`。
- **闭合路径**：F4/F5/F6 均 `NOT_MECHANIZABLE` → 闭合 = 下一复核轮**定点
  复看**具名段落（§2.0 (b) 例示、§1 acquisition-IDs / A1 采集 ID / 真值载体 /
  A5 四行、§3 步骤 5、§4 抬头与尾注、§2.6 注），F5b/F6b 一并列入复看清单；
  操作单是 PLAY_GOVERNING 成员且 `07bb8a4..HEAD` diff 非空 → 开轮资格自动
  成立（§4.4 R1）；操作单不属 R3 (3) 三个具名 Play 治理门文件，无强制闭环轮。
  **本角色不给自己的修正签发通过**——F4/F5/F6 在复核定点复看通过前不算闭合。
- **未释放/仍欠**：臂 B 五次 Play、`--compare`（需十次齐备并单独授权）、任何
  调参——**全部无 GO**；§2.15 归档（实现角色）不受本轮影响、照常执行；臂 B
  修订自本轮起有了已修正的文本基础，但仍须：用户逐字 GO 入账 → 槽位与
  `--body-policy` 双轮换（`_expected_policy()` 复核 `threshold`）→ §2.0
  (a)–(c)。COORD-007 §4.1 一帧下界缺口仍敞开（R10 未授权）；BC-BODY1-15 (d)
  反调参纪律与两条诊断发现的登记（M5/compare 必答）逐字不变。

### Acceptance round 57 — 2026-08-14（臂 B 授权前置审计：登记 H2-CEILING 发现，**不作处置**）

Decision: **`ARM_B_PRECONDITIONS_MET_EXCEPT_USER_GO`** +
**`FINDING_H2_CEILING_REGISTERED_AWAITING_USER_DECISION`**。本轮零 Play、零 ID、
零代码、零阈值、**零冻结统计量改动**。

用户问「可以开始B了吗」——**问句，不作授权入账**（沿轮 48/53 的最窄读法纪律）。
本角色在答复前做了一次臂 B 授权前置审计（多路只读，含两路对抗复核），其中一条
发现足以改变用户的决策，故先登记再答复。

#### A. 物理前置已清（本角色实测，非采信他人报告）

`e68827d` 执行了 §2.15：A5 六项 shared 工件已入
`…-arm-a-trial-5-post-run/`，`frames/` 聚合实测
`9dc67a7613201329b038ba6e425bc2e7aaa4ec7c9d196b09391c71624481a62b` = 轮 55 钉住值，
`runtime/frames/` **0 项**，五个 shared 文件**全部移走**，`…-arm-b-trial-1/` 不存在。
复核债亦已由复核轮 9 `PASS_WITH_NOTES` on `408acd7` 清偿。**臂 B 只差用户逐字 GO、
操作单 revision 19 与 §2.0 四步。**

#### B. **发现 H2-CEILING：`H2_SUPPORTED` 在本批次内算术上不可达**（本角色亲自复算）

`compare_arms` 的第二分量 `min_side_ge20_share` 的配对统计量 = 公共格点上
`B[point][1] - A[point][1]` 的**无权中位数**，`pass` 要求 summary `> 0.0`
**且每个配对中位数 `> 0.0`**（`tools/analyze_m3_body.py` 的
`component_index` / `pair_medians` / `all_pairs_same_sign` 块）。

五次臂 A 的 `c_quality_series` 实测**完全一致**：

| 分量 | 格点数 | 指示量 = `1.0` | 指示量 = `0.0` |
|---|---|---|---|
| `min_side_ge20_share`（五次各自） | **125** | **116** | **9** |

**反事实复算（本轮实跑）**：若臂 B 在**每一个**格点都取满 `1.0`（理论最好情况），
配对差为 116 个 `0.0` + 9 个 `1.0`，其中位数 = **`0.0`**——五个配对**全部** `0.0`，
`> 0.0` 不成立。

**结论**：无论臂 B 表现如何，第二分量**恒不可能 pass**；`H2_SUPPORTED` 要求三分量
全过，故**在本批次的冻结统计量下不可达**。可达上限是
**`THRESHOLD_ALLOCATION_PARTIAL`**（需 area 或 center-error 至少一个通过）。

**成因不是工具缺陷**：工具忠实实现了 BC-BODY1-5/-14 与轮 13 §B.2 冻结的统计量。
成因是**指示量饱和**——臂 A 已在 `92.8%`（116/125）的格点上满足
`min_side >= 20 px`，对一个 93% 饱和的指示量取中位数，天然无法移动。这是**载体/
场景的尺度属性**，不是两臂之差，因此也是 M5 设计审查与场景工作的输入。

**本角色不作任何处置**：在看过臂 A 数据之后修改预登记统计量，就是 BC-BODY1-15 (d)
禁止的调参，也违背预登记本身的意义。**登记，等用户决定**；若决定动统计量，属主
指标变更，须用户逐字授权并另走设计审查。

#### C. 一并登记的三条（同为臂 B 前置，均只登记不处置）

1. **臂 B 零作废容错**：`canonical_trial_id()` 只认十个字符串，**只有 A1/A2 有替代
   ID**；`…-arm-b-trial-1-attempt-N` 一律 `run_id_not_frozen_trial`（测试逐字钉住该
   拒绝）。臂 A 能从两次作废里恢复，是因为轮 29 §C.2 与轮 42 §B **事后加了代码**。
   **臂 B 若作废，槽位即烧掉**，恢复须再一次授权 + 代码 + 复核 + 停点。发令前须向
   用户逐字披露。
2. **「静默全 hold 臂 B」不被任何门拦截**：没有任何门读规划器的 `mode` /
   `velocity_world_mps` / `planner_error`；`body_motion_effort_m = 0.0`、
   `body_path_length_m = 0.0`、`planner_switch_count = 0` 是**合法**的臂 B 输出——
   正是五次臂 A 的实测值。即退化的臂 B 会产出一份通过全部门、可进 compare 的分析，
   实质是第 6 次臂 A。**处置方向（不是分析器改动）**：在 revision 19 的 Play 后核对
   里加接受侧要求 `body_motion_effort_m > 0` 且 `planner_switch_count > 0`，并复看
   `body_planner.reason` 直方图。
3. **估计器协方差发现与臂 B 的耦合：已查清，只按「有无」耦合，不按取值耦合。**
   `controller/body_planner.py` 的 `ThresholdBodyPlanner.decide` 在 `estimate is None`
   时返回 hold，随后**立即 `del estimate  # BC-M34-3`**，并由
   `tests/test_m3_body_policy.py::test_threshold_policy_never_reads_the_estimate`
   源码扫描强制（断言源码含 `del estimate` 且不含 `estimate.`）。**故已登记的
   非可信协方差（`nees_median` 832–1017、A3 的 `nis_median` 0.110）不可能按取值
   污染臂 B 的机体指令**；唯一残留耦合是滤波器抛错时 `estimate=None` → 该帧退化为
   hold，可由 `world_estimate.step == "error"` + `reason == "no_estimate"` 追踪
   （臂 A 五次实测零次）。**本条对上一轮登记的发现是收窄，不是撤销。**

#### D. 未释放

臂 B 五次 Play 与 `--compare` **全部无 GO**；本轮不发 revision 19（须先有 GO）。
H2-CEILING 与既有两条发现继续只作臂 B、M5 设计审查与 compare 口径的输入，
**BC-BODY1-15 (d) 禁止据任何一条调参**。

### Acceptance round 58 — 2026-08-14（臂 B trial 1 GO 入账 + H2-CEILING 事前预登记 + 操作单 revision 19）

Decision: **`B1_GO_LEDGERED_AWAITING_PREPLAY_RECORD`** + 操作单 **revision 19**
（**跨臂轮换**到 `p1-m3-body-001-arm-b-trial-1`）+
**`H2_CEILING_PREREGISTERED_STATISTIC_UNCHANGED_BY_USER_NO_GO`**。
本轮零 Play、零 ID 消耗、零代码、零阈值、**零冻结统计量改动**。

#### A. 用户裁定逐条落实

用户原话 **「1 + 3 合并执行，明确拒绝 2」**，已逐字入账。三条含义分别处置：

- **选项 3 → 授权**：**恰一次** Play、采集 ID `p1-m3-body-001-arm-b-trial-1`；
  **臂 B trial 2–5 仍各需逐字 GO**，本条不覆盖，`--compare` 亦不覆盖。
- **选项 1 → 指令**：H2-CEILING 已在**任何臂 B 数据存在之前**写入
  `docs/implementation-status.md` 并随本批次提交，成为**预登记限制**。含义：本批次
  的目标 verdict 上限即 `THRESHOLD_ALLOCATION_PARTIAL`；日后出 PARTIAL/INEFFECTIVE
  时，记录显示这是事前已知的设计限制，而非事后解释。
- **选项 2 → NO-GO（按拒绝入账）**：**不得**修改 `min_side_ge20_share` 或 H2 的
  任何预登记统计量、判据、样本域，也不为此另开设计审查。日后要改须另行逐字授权。
  本角色据此**不动**任何统计量——这与 BC-BODY1-15 (d) 同向。

#### B. 接受角色独立机械复算（只读，臂 B 侧全部首次）

`expected_acquisition_ids('b')` = 五个 `…-arm-b-trial-1..5`，**索引 `[0]`**（臂 B
从头开始，不是臂 A 的 `[4]`）；`canonical_trial_id()` 返回同名；**`_expected_policy()`
返回 `threshold`**，`POLICY_PLANNER['threshold']` = **`threshold-corridor-v1`**；
B1 既非 A1 也非 A2 的替代 ID → **两个 predecessor 门都不触发**；
`…-arm-b-trial-1-attempt-1/-attempt-2`、`…-arm-b-trial-6` 全部 `run_id_not_frozen_trial`；
run 目录不存在。**corridor 工件**（臂 B 专属启动门）实测 SHA-256
`9e2956ad…c800` = `config/p1-m3-body-001.json` 的 `corridor.artifact_sha256`，**779**
条棱柱。现场：六项 shared 缺席、`frames/` 0 项、五个 run 目录各 11 份、五处归档各
6 项（第五处聚合 `9dc67a76…a62b`）、四处旧 hold `257/93/109/257`、void hold 10 份。

#### C. revision 19：本文件历史上第一次跨臂轮换

- **§4 CLI 恰 2 行不同**（对已复核候选 `408acd7` 逐行比对实测）：`--run-id` 与
  **`--body-policy hold` → `threshold`**。此前每一次修订都只改一行，故所有
  「其余 18 个参数逐字不变」自本轮起为 **17 个**。冻结值 token 计数**零丢失**。
- **§2.0 (b) 的归因不得照抄**：跨臂轮换**语义确实改变**（第二行选的是另一个
  planner 类），套用 `NO_SEMANTIC_CHANGE` 即虚假归因。本轮另立
  **`RUNBOOK_DELTA_ARM_ROTATION_A_TO_B_SEMANTIC_BY_DESIGN_UNDER_GO_NO_GATE_
  RELAXATION_REVIEW_DEBT_REGISTERED`**——语义改变**是本次授权的目的本身**，不是
  夹带；不放宽任何门、不新设任何数值门。
- **新增 §2.16**（九项，含两项臂 B 专属：corridor 哈希、`_expected_policy()`）与
  §1 的 corridor 钉住行；§2.15 转已执行历史。
- **BC-BODY1-15 (c) 不重新武装**：三分支绑定"批次 1c 的**第一次** Play（必须是臂 A
  trial 1）"，A1 已放电其余九个。**B1 是臂 B 的第一次，但不是批次首跑**——只改主语
  措辞，不为 B1 新立数值门；机械事实一致（分析器为臂 B 写 `h1.disposition` 但从不
  据此抛错，H1 只遍历臂 A）。
- **五处失效标注就地更正**（AGENTS.md 义务，零语义改动），其中两处是**硬前置**：
  §3 步骤 0′ 与门 1 的记录条款自 revision 12 起一直写死"记入 trial 2 证据文件"，而
  这是"未落盘即不得启动 tracker"的前置，指错文件等于条款落空——与复核轮 8 的
  F5/F6 同类，本轮一并清掉；另三处为 §1 激活方式行的"trial 后恢复"（该 override
  十次 Play 期间从未恢复，恢复即换载体破坏配对）、§3 步骤 3 的臂 A planner 描述、
  §5 那条已被轮 42 §A 撤下却仍写着 `>= 2P` 触发的 void 行（**照字面读会促使操作员
  提前退出 Play，正好撞上仍然生效的 `…POST_TRACKER_EARLY_EXIT`**）。
- **两条新增披露，均不新设门**：§5 的臂 B **零作废容错**；§3 步骤 6 的**退化臂 B
  记录与回接受角色条件**——`body_motion_effort_m == 0` 时停下回本角色归因，
  **本身不使 trial 作废**（事后新设作废门属改协议）。依据：没有任何门读规划器的
  `mode`/`velocity`/`planner_error`，`0/0/0` 是合法输出且正是五次臂 A 的实测值。

#### D. 一条收窄的既有发现（不撤销）

`ThresholdBodyPlanner.decide` 在 `estimate is None` 时返回 hold，**随后立即
`del estimate`（BC-M34-3）**，并由源码扫描测试强制。故已登记的非可信协方差
**不可能按取值污染臂 B 的机体指令**；唯一残留耦合是滤波器抛错时该帧退化为 hold，
可由 `world_estimate.step == "error"` + `reason == "no_estimate"` 追踪（臂 A 五次
实测零次）。此为对轮 47/55 发现的**收窄，不是撤销**。

#### D′. 发出前的对抗自查与据此的返工（接受轮 58 同轮完成）

**据实写明工具状态**：本轮对 revision 19 起草稿做了一次多路对抗自查（四路独立
镜头：臂 A 残留 / CLI 与冻结值 / 门完整性 / 操作员逐步走查）。**四路镜头产出 32 条
claim，但逐条判定与汇总阶段因会话额度全部失败**（`confirmed: 0` 是「判定没跑」，
**不是**「无缺陷」）。故本角色**自行逐条判定**这 32 条，机械事实全部亲自复算。
结论：**采纳并修复 20 处**，其中 7 处属「照字面执行会出错」。修复后复算：CLI 块仍
19 行**恰 2 行不同**、冻结值 token **零丢失**、三处缺陷文本**零残留**。

**七处要害（多数是本角色起草时自己引入的，据实记账）**：

1. **§5 那条 void 行写成「代码只在下界 fail-closed」——假**。上界撤下后还有
   **两条域完整性硬门**（`loop_domain_sample_below_perimeter_after_closure`、
   `loop_domain_unwrapped_backward_step`，本轮在 `analyze_m3_body.py` 实跑确认）。
   照原文读会以为域完整性不再拦人。已按 §1 原表述改写。
2. **零作废容错披露把 pre-tracker 也算成「烧 slot」——假且会误报**。本节自己的
   pre-tracker 段逐字规定：三个硬门与启动失败发生在**创建 run 目录之前**，采集 ID
   **未被消耗**。原文会导致门 1 越界时向用户报告「B1 已永久烧掉」。已逐字区分。
3. **§4 防漂移句写「上面 17 行必须逐字节照抄」，而块是 19 行**——按字面恰好豁免了
   `--run-id` 与 `--body-policy` 这两行，即本轮唯一新写、错一个字就烧 slot 的两行。
   已改为「整块 19 行，含这两行」。
4. **§2.9/§2.11 的现在时导航仍写「本轮的待执行核对是 §2.14」**——实现角色顺序扫
   §2 会先读到它，转去执行 A5 的清单（四个 run 目录、A5 的 create-once 目标），
   核对错对象。已改指 §2.16。
5. **§2.16 丢了保全禁令**：自 §2.6 起逐轮携带的「不得移动、覆盖、删除，也不得作为
   本次采集的任何输入」被起草时删成只剩「只读保全对象」。已恢复完整表述。
6. **启动前从未核对 `--body-policy`（新增门 4）**：步骤 0′ 只比对解释器路径，
   §2.16 第 9 项只验「分析器期望什么」，**都不看实际敲下去的命令行**。跨臂轮换第一次
   让这个参数可写错，而写错要到分析期才由臂身份三层核对暴露——那时 run 目录已
   create-once 建成、采集 ID 已消耗。新增**门 4**：回车前把命令行原文落盘并逐字核对
   两个 token 序列。**只增停条件、零阈值、不改门 1/2/3 任何判据。**
7. **§5 发令前提漏了 H2-CEILING 预登记的次序条件**：用户 GO 的「选项 1 = 指令」
   要求预登记**发生在任何臂 B 数据之前**，晚于数据即失去意义。已补为第 (3) 条前提，
   附可复制的 `git log -S` 核对命令。

其余 13 处为计数/口径/指针类：CLI「其余 17 个参数」应为 **16 个参数 / 17 行**
（19 行 = 1 行入口 + 18 参数，历次抬头一直偏大 1）；「上述四种终态」应为当前可触发
**三种**；`effort == 0` 的口径应写明只在 `[0, P)` 首圈积分；步骤 3 的「每帧」应为
**decision 帧**（catch-up 行合法不带 planner）；门 1 越界的现场保全命名须取臂 B 而
非 §2.3 的 `arm-a-*`；§2.16 补落盘目的地、补第 8/9 项可复制命令、补八个标记的出处；
§2.5 第 5 项残缺 SHA `64be7f85…af…` → `…39f2`；门 1 记录条款的 `**` 不配对（把硬
前置的加粗打掉）；抬头 C「多一项」应为**两项**、抬头 H 与 E 自相矛盾；§6 末句
「trial 1 不释放」与复核轮 8 块的「§2.15 仍是唯一待执行节」补时间边界；测试钉住
范围收窄为 `…-attempt-4` 一例。

**这 20 处修复本身未经独立复核**，与 revisions 13–19 一并挂在下一轮复核；本轮的
自查**不替代**复核角色。


#### E. 未释放 / 仍欠

臂 B trial 2–5 与 `--compare` 无 GO；`--compare` 的 15 个身份键要求意味着臂 B 侧
任何参数漂移**在孤立分析中仍会 PASS**，只在十次齐备后才暴露（已写进 §4 披露）。
H2-CEILING 与另两条发现继续只作臂 B、M5 设计审查与 compare 口径的输入，
**BC-BODY1-15 (d) 禁止据任何一条调参**。COORD-007 §4.1 缺口仍在（R10 未授权）。

### Acceptance round 59 — 2026-08-14（B1 发令前置复算 + §2.0 (c) 放行）

Decision: **`B1_PREPLAY_RECORDED_ONE_PLAY_RELEASED`**。本轮零 Play、零代码、
零阈值；释放的是**恰一次** Play。

#### A. 接受角色独立复算（只读，60/60 PASS，与实现角色 115/115 无出入）

实现角色在 `90f7b3b` 报告 §2.16 九项 = **115 条全 PASS** 与 §2.0 (b)（证据
`…-arm-b-trial-1.md` §A）。本角色用自己的脚本重跑：六项 shared 缺席、`frames/`
0 项、四处旧 hold `257/93/109/257`（attempt-3 run hold 恰两文件）、**五个 run
目录各 11 份**、**五处归档各 6 项**且五个聚合 SHA 逐项等于钉住值、八标记缺席、
void hold 10 份零隐藏 + 三钉住 SHA、**B1 run 目录不存在**；**五条 `--verify` 全部
退出 0 且逐字复现**。**两项臂 B 专属**同样自跑：corridor 实测 SHA = config pin =
§1 钉住值 `9e2956ad…c800`，`instance_count` **779** 且工件内实际条目数亦为 **779**；
`_expected_policy` = `threshold`、`POLICY_PLANNER['threshold']` =
`threshold-corridor-v1`、`ids(b)[0]` 相等、canonical = 自身，三个非法变体
（`-attempt-1`/`-attempt-2`/`-trial-6`）在 `canonical_trial_id()` 与
`_expected_policy()` **两个函数上都**抛 `run_id_not_frozen_trial`。**无一项出入。**

**基线归因本角色自算**：`<BASE>` = `408acd7`（`| tail -1` 取最新一行，即复核轮 8
F4 修正后的取法）；在实现角色的测量时点 `03cb2b5` 上 delta = **7 个文档路径**，
**测量侧 diff 为空**；再往前对 Review round 7 的 `07bb8a4` 亦为空——即
**B1 与 A1…A5 运行在同一份测量侧字节上**，A/B 配对的前提成立。

**采信实现角色多做的一步并复核**：§1 称 corridor 是「臂 B 专属启动门」，其成立
前提是 `policy.tether_corridor_check` 为真；实现角色读码确认，本角色实测该值
为 **`true`**，故该门本轮**确实会触发**，不是纸面条款。

#### B. 实现角色交回的七项，逐条处置

1. **(c) 属本角色**：接受，HEAD/`porcelain` 由本角色在写入时点自取，不沿用测量
   时点 `03cb2b5`。
2. **§2.16 发令时刻复查**：接受，本轮 60 条即在本批次提交后的最终 HEAD 上复跑。
3. **PLAY_GOVERNING 恰 1 条**（操作单 revision 19），具名归因**轮 58 已给**
   （`RUNBOOK_DELTA_ARM_ROTATION_A_TO_B_SEMANTIC_BY_DESIGN_UNDER_GO_NO_GATE_
   RELAXATION_REVIEW_DEBT_REGISTERED`），本轮确认无需补发。**其点出的复核缺口
   属实且本角色同意**：revisions 13–18 的债已由复核轮 8/9 闭合，但 **revision 19
   本身与轮 58 自查采纳的 20 处修复成文于轮 9 候选之后，尚未被任何复核轮覆盖**，
   继续登记，**不阻断本次 Play**（依据同轮 58：冻结值零丢失、CLI 恰 2 行不同且
   两行都是本次授权点名的臂位轮换、新增条款只增停条件）。
4. **B1 无前驱门**、5. **零作废容错的 pre/post 区分**、6. **不申领 `UNITY_NA`**、
   7. **H2-CEILING 已预登记**：四条均如实，照录进 (c)。
   其中第 7 条对应 revision 19 §5 新增的发令前提 (3)，本角色实跑核对：
   `git log -S'H2-CEILING' -- docs/implementation-status.md` 返回 `03cb2b5`
   （2026-08-14 11:05:22 -0400），**早于本次 Play**，条件满足。

#### C. §2.0 四步与放行

(a) PASS（轮 58 入账并提交）、(b) PASS（`03cb2b5`，证据 §A.4）、**(c) 本轮写入
`docs/unity-test-log.md`**，(d) 由发令时刻核对——工作树只允许 (c) 这一份未提交
差异，故 (c) 记录**保持未提交**直到 Play 结束后另行代录入库（沿轮 49/51/54 先例）。
**释放 arm B trial 1 的恰一次 Play。**

BC-BODY1-21 自 (c) 落盘起生效：任何角色在本次 Play 结束前**不得再动操作单**；
Play 中发现歧义按 BC-BODY1-22 fail closed 回本角色，**不得就地修补后继续**。

#### D. 带进本次 Play 的限制（一条不放宽）

臂 B trial 2–5 与 `--compare` 无 GO；**任何已见数字都不得据以调参**
（BC-BODY1-15 (d)，包括本轮第一次出现的非零 effort/路径/切换数）；四种 void 终态
各消耗这一次 one-Play GO，**post-tracker 作废即烧掉 canonical slot**（臂 B 无替代
ID），pre-tracker 的三个硬门与启动失败**不消耗采集 ID**；H2-CEILING 已预登记，
本批次目标 verdict 上限为 `THRESHOLD_ALLOCATION_PARTIAL`；COORD-007 §4.1 缺口仍在。

### Acceptance round 60 — 2026-08-14（arm B trial 1 归因 = 有效 B1；**重大发现 SCENE_DEGENERATE_ON_TREATMENT_ARM**）

Decision: **`ACCEPTED — B1_VALID_TRIAL`**（arm B **1/5**）+
**`FINDING_SCENE_DEGENERATE_ON_TREATMENT_ARM_REGISTERED_AWAITING_USER_DECISION`**
+ 操作单 **revision 20**（**只**加 §2.17 归档合同，**不轮换槽位**——B2 无 GO）。
**用户口述的「trail5」经磁盘机械确认实为 arm B trial 1**（A5 昨日已归因并归档，
run 目录 11 份、归档 6 项俱在）；本轮按 B1 归因，不按 A5。

#### A. 归因：B1 有效（接受角色独立复算，只读）

- **`--verify` 亲自复跑**：退出 **0**，逐字返回
  `{"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0,
  "run_id": "p1-m3-body-001-arm-b-trial-1", "verified": true,
  "window_c_track_given_geom": 1.0}`。
- **身份链**：`run_id` 即 canonical slot；receipt **正确地不含** attempt/predecessor
  任何键；**`body_policy = threshold`、`body_planner_name = threshold-corridor-v1`**、
  `condition=follow`、`init_frame_id=0`、scenario 与可见弧 SHA 相符；run 目录恰 11 份。
- **四门 + 握手**（证据 §B/§C，本角色复核记录）：门 1/2/3 全过；**门 4 首次实弹
  承重**——命令行原文回车前落盘，两个 token 序列机械核对为真，`--body-policy
  threshold` 与 B1 的 `--run-id` 逐字在列；臂身份三层核对随后在分析期**事后确认**
  门 4 的目的达成。tracker 自然退出 0、651 帧，validator 产出确认词，Console 无报错。
- **两条域完整性门零触发**，`loop_frame_count` 530、`window_frame_count` 155、
  `h2_grid_points` 125，与冻结口径一致。停留 `41.389801 s`、圈数 `1.618675`（披露）。
- **BC-BODY1-15 (c) 不触发**：三分支绑定"批次 1c 的第一次 Play（必须是臂 A trial
  1）"，A1 已放电；分析器为臂 B 写 `h1.disposition` 但**从不据此抛错**（本轮实测
  退出 0），H1 只遍历臂 A。故 `SCENE_DEGENERATE` **不使 B1 作废**。
- 不匹配任何 void 终态 → **计为 canonical slot `p1-m3-body-001-arm-b-trial-1`
  的有效 trial**，与 A1 配对。**臂 B 1/5。**

#### B. 机体第一次真的动了（事实登记）

| 量 | B1 | 臂 A 五次 |
|---|---|---|
| `body_motion_effort_m` | **`88.64522663177961`** | `0` |
| `body_path_length_m` | **`61.42306359956821`** | `0` |
| `planner_switch_count` | **`11`** | `0` |

revision 19 披露 2 的退化分支（`effort == 0`）**不触发**。623 条 decision 帧的
`reason` 直方图：`margin_below_trigger+corridor_blocked` **324**、
`within_hysteresis_band` 116、`margin_below_trigger` 95、`margin_above_release` 82、
`+corridor_shortened` 6；**`no_observation`/`no_platform_state`/`no_estimate`/
`planner_exception` 与 `publish_failure_fallback` 全为 0 帧**。
**即：52% 的 decision 帧里规划器想动而被 corridor 挡住**——审计事前登记的
"latching corridor hold"风险部分兑现，但未阻止机体累计走出 `61.4 m` 路径。

#### C. **重大发现：主指标在处理臂上饱和（`SCENE_DEGENERATE`）**

**`full_loop_c_geom = 1.0`，`ceiling = 0.95`。** 臂 A 五次是 `0.578–0.597`。
即臂 B 在整圈上取得**满分几何可见性**——这正是 BC-BODY1-15 (c) 用 `>= 0.95` 想要
探测的那个状态："场景无法再分辨表现"。冻结合同把该三分支绑在**批次首跑**上，A1
已放电，故**机械上什么都不触发**；但该判据要探测的情形，**如今出现在了处理臂上**。

**这对研究的含义（据实写明，本轮不作处置）**：

1. **H1 不受影响**（只遍历臂 A），臂 A 的 `0.578` 与其单档离散跳变结论不变。
2. **"臂 B 把 `C_geom` 从 `0.578` 提到 `1.00`"是一个很大的正向结果，但它是
   饱和值**：真实效应量**只有下界**，场景无法显示臂 B 还能好多少，也无法在同一
   场景里比较两种臂 B 策略。这必须作为**论文的具名限制**，不能当成"效应量 = 0.42"。
3. **H2 的命运现在有实测依据**（诊断，非正式 compare——`--compare` 未跑未授权）。
   以 (A1, B1) 这一对复算三个分量的配对中位数：

   | 分量 | 中位数 | `> 0`? | 逐格点 +/−/0 |
   |---|---|---|---|
   | `area_median_px` | **`632.44`** | **是** | +99 / −21 / 0:5 |
   | `min_side_ge20_share` | **`0.0`** | **否** | +9 / −0 / **0:116** |
   | `center_error_px` | `0.5305` | 是 | +80 / −45 / 0:0 |

   **H2-CEILING 的预登记被实测证实**：B1 的 min_side 指示量是 **125/125 = 1.0**
   ——正是轮 57 在**任何臂 B 数据存在之前**假设的"完美臂 B"，配对差 116 个 `0` +
   9 个 `1`，中位数恰为 `0.0`，该分量**如预登记所述不可能 pass**。可达上限仍是
   `THRESHOLD_ALLOCATION_PARTIAL`。**另须注意** `center_error_px` 的通过是**脆弱
   的**：中位数仅 `0.53 px`，逐格点 80 正 / 45 负。
4. **估计器协方差发现在臂 B 上翻转**：`nees_median` 由臂 A 的 `832–1017`
   降到 **`5.07`**（`nis_median` `0.0255`）。机体运动带来的观测几何变化似乎
   **恢复了滤波器的可信度**——这与轮 47/55 登记的"协方差不可信"是同一枚硬币的
   两面，**并未推翻该发现，而是给了它一个机制解释的方向**。登记为 M5 必答项。

**本轮不据以调参**（BC-BODY1-15 (d)），不改任何阈值、样本域、载体、协议或统计量。

#### D. revision 20：只加归档合同，不轮换槽位

§2.17 冻结 source→destination 与移动前的计数/SHA-256（`frames/` 257 项聚合
`09f1ac61…524c`、truth **858 行 / 919046 字节** `6addcf08…935e`，metrics/body/
gimbal/tracking 四个哈希），要求移动后逐项相等、复跑**六个** `--verify`、只重建空
`frames/`、**不得预建任何 run 目录**；destination 本角色实测**当前不存在**。
**B1 的 run 目录不动。** 处置
`RUNBOOK_REVISION_20_ARCHIVE_CONTRACT_ONLY_NO_SLOT_ROTATION_NO_GATE_RELAXATION_
REVIEW_DEBT_REGISTERED`。**不轮换采集 ID**：臂 B trial 2–5 无 GO。

#### E. 上交用户的决定（触及主指标与核心主张，本角色不自决）

臂 B 余下四次若照跑，按 B1 的结果**大概率都会落在 `1.0` 饱和处**。是否值得再花
四次 Play、以及饱和场景要不要进设计通道，属用户决定，且 BC-BODY1-13 冻结了
"恰 5 次/臂"、`--compare` 要求十次齐备——缩减臂 B 本身就是协议变更。已连同
H2-CEILING 一并上交。**在用户答复前不发臂 B trial 2 的任何前置。**

### Acceptance round 61 — 2026-08-14（饱和决定入账 + 预登记 #2 + 操作单 revision 21）

Decision: **`B2_TO_B5_BATCH_GO_LEDGERED_SATURATION_PREREGISTERED`** + 操作单
**revision 21**（轮换到 `p1-m3-body-001-arm-b-trial-2`）。本轮零 Play、零 ID 消耗、
零代码、零阈值、**零统计量改动**。

#### A. 用户裁定与其边界

用户在轮 60 三选项中选 **「照跑 B2–B5，饱和作具名限制」**，已逐字入账。三层含义：

1. **批量授权 B2–B5 四次 Play**——**本项目第一次一次性授权多次 Play**，故本角色
   在账本与本轮逐字写死其边界：**每次仍各走完整 §2.0 (a)–(d) 与各自的核对节**
   （免除的只是"每次回用户再要一句 GO"）；**任何 void 终态立即中止该授权**，停下
   回用户重新决定（臂 B 无替代 ID，post-tracker 作废即烧 slot）；**不覆盖**
   `--compare`、任何重试/重进/调参、任何协议或统计量变更。
2. **饱和作具名限制预登记**：已写入 `docs/implementation-status.md`（预登记 #2），
   **在臂 B 余下四次采集之前**落盘并提交。结论口径被钉死：**「臂 B 达到 100% 几何
   可见性，效应量为下界」**，`1.00 − 0.578` **不得**作为可测效应量引用。
3. **两条 NO-GO**：不停批次；**不换场景**——用户是在知悉"换场景 = 臂 A 五次作废
   （配对绑在载体上）"之后作的选择。

#### B. revision 21：同臂轮换，只改一行

- **§4 CLI 对上一修订（B1）恰 1 行不同**（`--run-id`），`--body-policy threshold`
  保持不变；**但对已复核候选 `408acd7`（臂 A trial 5 的版本）仍是 2 行不同**——
  抬头已写死这两个基准的区别，(b) 归因必须按后者写，**不得把"1 行"填进归因**。
  冻结值 token 零丢失（对 `408acd7` 实测）。
- **机械确认（本轮实跑）**：`canonical_trial_id()` 返回同名、`_expected_policy()` =
  `threshold`、`expected_acquisition_ids('b')[1]` 相等、`-attempt-N` 被拒、run 目录
  不存在；配对搭档 A2。
- **新增 §2.18**（B2 的 Play 前九项，第 4/5 项扩到**六个** run 目录与**六处**归档，
  含 B1 的 `09f1ac61…524c`）；**§2.17（B1 归档）仍是本轮第一步待执行**，§2.16 已转历史。
- **起草中自查并即时修正一处**：§2.18 第 4 项初稿写成了"加一条 B2 的 `--verify`"
  再自我否定的形式——B2 尚未采集，对它跑 `--verify` 无意义，且这种"先写错再纠正"
  的句式正是复核轮 8 与轮 58 自查反复点名的歧义类缺陷。已改为直接列出六条正确命令
  并写明"本轮采集尚不存在，第 4 项不对它跑 `--verify`；它在第 7 项被核对为不存在"。
- 处置 `RUNBOOK_REVISION_21_SAME_ARM_SLOT_ROTATION_NO_GATE_RELAXATION_REVIEW_DEBT_REGISTERED`。
  **复核债继续累积**：revisions 19/20/21 与轮 58 自查修的 20 处均未被任何复核轮覆盖。

#### C. 发令前置与未释放

前置顺序：**§2.17 归档 → §2.18 九项 → §2.0 (b) → (c)/(d)**。缺一不得进 Play。
未释放：`--compare`（需十次齐备并单独授权）、任何调参、任何协议/统计量变更。
两条预登记限制（H2-CEILING、处理臂饱和）随本轮继续生效。

### Acceptance round 62 — 2026-08-14（B2 发令前置复算 + §2.0 (c) 放行）

Decision: **`B2_PREPLAY_RECORDED_ONE_PLAY_RELEASED`**。零 Play、零代码、零阈值；
释放的是**恰一次** Play，取自 2026-08-14 的 B2–B5 批量授权。

#### A. 接受角色独立复算（只读，62/62 PASS，与实现角色 24 + 126 无出入）

- **§2.17 归档**：destination 恰 **6 项**；五个单文件的行数/字节/SHA-256 与
  `frames/` 257 项聚合 `09f1ac61…524c` **逐项等于接受轮 60 的钉住表**；**B1 的 run
  目录未动（11 份）**。`body_command.json` 的 **15 行 / 329 字节**与臂 A 的 10 行 /
  207–208 字节不同，是臂 B 指令包多出 `velocity_world_mps` 所致——§2.17 事前已写明，
  实测相符，**不是漂移**。
- **§2.18 九项**：六项 shared 缺席、`frames/` 0 项、四处旧 hold `257/93/109/257`
  （attempt-3 run hold 两文件）、**六个 run 目录各 11 份**、**六处归档各 6 项且六个
  聚合 SHA 逐项相符**、八标记缺席、void hold 10 份零隐藏 + 三钉住 SHA、**B2 run 目录
  不存在**；两项臂 B 专属——corridor SHA = pin、`instance_count` 与工件条目双向 779、
  `tether_corridor_check` 仍 `true`；`_expected_policy(B2)` = `threshold`、planner
  `threshold-corridor-v1`、`ids(b)[1]` 相等、`-attempt-N` 在两个函数上均被拒。
- **六条 `--verify` 亲自复跑全部退出 0 且逐字复现**（臂 A 五个 `WITHIN_RANGE`，
  B1 `SCENE_DEGENERATE` / `1.0`）。
- **基线归因自算**：`<BASE>` = `408acd7`，delta **9 条全是文档**（比 B1 轮多两条：
  B1 证据文件与 Unity 日志——后者是轮 59 的 (c) 与轮 60/61 的代录），**测量侧为空**。
  **A1…A5 + B1 六次采集与即将进行的 B2 跑在同一份已复核代码上。**
- **CLI 两个基准本角色亲自复算**（不转抄任何抬头）：对已复核候选 `408acd7`
  **恰 2 行**（`--run-id` + `--body-policy`）、对 B1 轮**恰 1 行**（`--run-id`）。
  revision 21 抬头 A 点的两个数字实测成立，**(b) 的归因按 2 行写**。

#### B. 实现角色交回六项，逐条处置

1. **(c) 属本角色 / §2.18 发令时刻复查**：接受，HEAD 与 `porcelain` 由本角色写入
   时点自取（不沿用测量时点 `d48cd25`），62 条即在本批次提交后的最终 HEAD 上复跑。
2. **PLAY_GOVERNING 恰 1 条 = revision 21**，其具名 disposition **轮 61 §B 已给**
   （`RUNBOOK_REVISION_21_SAME_ARM_SLOT_ROTATION_NO_GATE_RELAXATION_REVIEW_DEBT_
   REGISTERED`），本轮确认无需补发。**其登记的复核缺口本角色同意**：鉴于
   `passed_candidate` 仍是 `408acd7`，**revisions 19/20/21 与轮 58 自查采纳的 20 处
   修复至今未被任何复核轮覆盖**，继续登记，**不阻断本次 Play**（依据同轮 58/61：
   冻结值零丢失、CLI 差异实测与抬头相符、新增条款只增停条件）。
3–6. **B2 无前驱门**、**批量授权边界**（每次各走 §2.0；**任何 void 立即中止授权**
   并回用户）、**两条预登记限制继续生效**、**不申领 `UNITY_NA`**：四条均如实，照录进 (c)。

#### C. §2.0 四步与放行

(a) PASS（批量 GO 轮 61 入账并提交）、(b) PASS（`d48cd25`，证据 §A）、**(c) 本轮
写入 `docs/unity-test-log.md`**，(d) 由发令时刻核对——(c) 记录**保持未提交**直到
Play 结束后代录入库。**释放 arm B trial 2 的恰一次 Play。**
BC-BODY1-21 自 (c) 落盘起生效；Play 中发现歧义按 BC-BODY1-22 fail closed 回本角色。

#### D. 带进本次 Play 的限制（一条不放宽）

**门 4 照旧且这次尤其要紧**：回车前须核对命令行含 `--body-policy threshold` 与
**B2 的** `--run-id`——同臂轮换只改一行，`--run-id` 写成 B1 会撞 create-once 而
`--body-policy` 若被误改则要到分析期才暴露，两者都烧 slot。
`--compare`、B3–B5 的单独发令、任何调参均未释放；两条预登记限制继续生效；
**任何 void 终态立即中止批量授权**并回用户重新决定。

### Acceptance round 63 — 2026-08-14（arm B trial 2 归因 = 有效 B2；臂 B 2/5）

Decision: **`ACCEPTED — B2_VALID_TRIAL`**（arm B **2/5**）+ 操作单 **revision 22**
（§2.19 B2 归档合同 + 槽位轮换到 B3 + §2.20 核对）。零 Play 消耗于本轮。

**命名澄清（据实，不按口述执行）**：用户口述「trail6」，但**冻结合同里不存在
trial 6**——`p1-m3-body-001-arm-a-trial-6` 与 `…-arm-b-trial-6` 均被
`canonical_trial_id()` 抛 `run_id_not_frozen_trial`（本轮实跑复验），`TRIALS_PER_ARM`
恒为 5。磁盘机械确认刚跑完的是 **arm B trial 2**（`5df2b99`，run 目录已 create-once
建成），故本轮按 **B2** 归因。若用户本意另指，须明说。

#### A. 归因：B2 有效（接受角色独立复算，只读）

- **`--verify` 亲自复跑**：退出 **0**，逐字返回
  `{"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0,
  "run_id": "p1-m3-body-001-arm-b-trial-2", "verified": true,
  "window_c_track_given_geom": 1.0}`。
- **身份链**：`run_id` 即 canonical slot；receipt **正确地不含** attempt/predecessor
  任何键；`body_policy = threshold`、`body_planner_name = threshold-corridor-v1`、
  `condition = follow`、`init_frame_id = 0`、scenario 与可见弧 SHA 相符；run 目录恰 11 份。
- **四门 + 握手**（证据 §B/§C）：门 1 `reported_sim_t = 5.3831706047058105`；门 2 最低
  帧 `0`；门 3 用户目检「匹配」；**门 4 第二次实弹通过**（两个 token 机械核对为真——
  本轮尤其要紧，同臂轮换只改一行，run-id 若残留 B1 会撞 create-once）；tracker 自然
  退出 0、validator 逐字产出确认词、用户报「已退出，没有报错」。
- **两条域完整性门零触发**；`loop_frame_count` **530**、`window_frame_count` **155**、
  `h2_grid_points` 125，与 B1 及冻结口径一致。停留 `29.602264 s`、圈数 `1.509862`（披露）。
- 不匹配任何 void 终态 → **有效 trial，与 A2 配对，臂 B 2/5**。**批量授权继续有效**
  （其中止条件是 void 终态，本轮未触发）。

#### B. 两条预登记限制各获第二次实测确认

| 量 | B1 | **B2** | 臂 A |
|---|---|---|---|
| `full_loop_c_geom` | `1.0` | **`1.0`** | `0.578–0.597` |
| `h1.disposition` | `SCENE_DEGENERATE` | **`SCENE_DEGENERATE`** | `WITHIN_RANGE` |
| min_side 指示量满分格点 | 125/125 | **125/125** | 116/125 |
| `body_motion_effort_m` | `88.645` | **`75.269`** | `0` |
| `body_path_length_m` | `61.423` | **`49.162`** | `0` |
| `planner_switch_count` | `11` | **`11`** | `0` |
| `estimator.nees_median` | `5.07` | **`5.30`** | `832–1017` |

- **处理臂饱和**（预登记 #2）：连续两次 `1.0`，**不是一次性偶然**。结论口径不变——
  只能报「臂 B 达到 100% 几何可见性，**效应量为下界**」。
- **H2-CEILING**（预登记 #1）：B2 的 min_side 又是 **125/125**，与 B1 相同，故
  (A2,B2) 这一对的该分量配对差同样是 116 个 `0` + 9 个 `1`、中位数 `0.0`。**预登记
  在两个独立配对上都成立**，可达上限仍 `THRESHOLD_ALLOCATION_PARTIAL`。
- **估计器发现**：`nees_median` 5.07 → 5.30，与臂 A 的 832–1017 相差两个数量级且
  **臂内高度一致**——「机体运动恢复滤波器可信度」的方向得到第二个数据点。仍只作
  M5 设计审查输入。
- **corridor 阻挡加剧但机体位移下降**：`corridor_blocked` 324 → **339** 帧，
  effort 88.6 → 75.3 m、路径 61.4 → 49.2 m，而 `planner_switch_count` **两次都是 11**。
  登记为 M5 与 compare 口径的观察项，**n=2 不支持任何主张**。
- **BC-BODY1-15 (d)：以上一个数都不得据以调参。**

#### C. revision 22：归档合同 + 轮换到 B3

- **§2.19**（B2 的 post-run 归档）：钉住 `frames/` 257 项聚合
  `71f65dca666cc37d91569a9b2b3893c0721e436a1b09756f5e644c0052a20f85`（§B.3 口径）、
  truth **800 行 / 862952 字节** `c2c985fe…4df3`、metrics 61/2057 `c60939ac…640e`、
  body 15/**328** `d066e0b1…8fa5`、gimbal 15/341 `516c2820…d990`、tracking 18/458
  `82ffa1b5…9463`；destination 实测不存在。移动后须逐项相等并复跑**七个** `--verify`。
  （`body_command.json` 328 字节，B1 是 329——臂 B 包内数值位数差异，非漂移。）
- **槽位轮换到 `p1-m3-body-001-arm-b-trial-3`**（批量授权已覆盖，无需新 GO）：
  §1 采集 ID 行、§3 步骤 4/5、§4 CLI 的 `--run-id`；`--body-policy threshold` 不动，
  故 CLI 对上一修订**恰 1 行**、对已复核候选 `408acd7` 仍 **2 行**。机械确认（本轮
  实跑）：canonical = 自身、`_expected_policy` = `threshold`、`ids(b)[2]` 相等、
  `-attempt-N` 被拒、run 目录不存在；配对搭档 A3。
- **§2.20**：B3 的 Play 前九项（第 4/5 项扩到**七个** run 目录与**七处**归档）。
  §2.18 转历史。处置
  `RUNBOOK_REVISION_22_ARCHIVE_CONTRACT_AND_SAME_ARM_ROTATION_NO_GATE_RELAXATION_REVIEW_DEBT_REGISTERED`。
- **复核债照挂**：revisions 19–22 与轮 58 的 20 处仍未被任何复核轮覆盖。

#### D. 未释放

`--compare`（需十次齐备并单独授权）、任何调参、任何协议/统计量变更。B3 的**发令**
仍须走 §2.19 → §2.20 → §2.0 (b) → (c)/(d)；批量授权免的只是"再要一句 GO"。

### Acceptance round 64 — 2026-08-14（消费 Review round 10：F7–F10 返工 + P4/P5 应用 + N37 裁定）

Decision: **`ROUND10_REWORK_APPLIED_CLOSURE_BY_TARGETED_REINSPECTION_PENDING`**。
零 Play、零 ID、零代码、零阈值、**零冻结值改动**（对候选 `9cadebd` 逐 token 复算，
无一减少）。修复归本角色——四条 finding 全部是本角色起草的操作单文字。

#### A. finding 复判分级（§4.4，逐条独立判断，不照单全收）

| # | 复核分级 | 本角色复判 | 依据 |
|---|---|---|---|
| F7 | CLASS_2 | **同意 CLASS_2** | 缩写末四位错值。判据「操作员或工具的行为会不会因这段文字而不同」——会：照 §2.20 字面核对会在**完好**工件上判不符并停机。属涉哈希的文字，CLASS_3 闭集不含。 |
| F8 | CLASS_2 | **同意 CLASS_2** | §4 活跃节内部自相矛盾（抬头 B1 vs CLI 块 B3）。操作员照散文写 `--run-id` 会撞 B1 的 create-once → `TRIAL_VOID_TRACKER_STARTUP_FAILURE`，烧一次 GO 并**中止批量授权**。 |
| F9 | CLASS_2 | **同意 CLASS_2，且其中两处更重** | 步骤 0′ 与门 1 的落盘目的地是**启动 tracker 的硬前置**；void 保全命名写死 B1 会以一个**有效** trial 之名保全现场、伪造其作废外观并毁归因。 |
| F10 | CLASS_2 | **同意 CLASS_2** | 授权判据文字与已入账批量 GO 相悖，照「最高优先级」字面会拒发 B3。 |
| P4/P5 | CLASS_3 | **同意 CLASS_3，同轮应用** | 纯时态与失效导航指针，不涉数值/阈值/ID/判据/执行顺序/终态名。逐字补丁已应用，未改任何数字、哈希、run ID、disposition。 |
| P6 | 复核已就地更正 | **确认并接受** | 状态板两处时效文字，属 AGENTS.md 常驻义务，轮 8 N32 先例。本轮实测已生效。 |

**本轮不推翻复核的任何判定**，亦确认其明文的「不推翻」清单（A1…A5/B1/B2 有效性、
轮 60/63 归因、两基准 CLI 差异、20 处修复的落地、预登记次序、批量 GO 边界）与本角色
记录一致。

#### B. N37 裁定：取 (b) 去实例化，并写死一条例外

复核给出两个耐久方案：(a) 把全部位点固化进轮换必改清单；(b) 活跃文本去实例化。
**本角色裁定取 (b)**，依据是证据而非偏好：轮 58 已修过这一族一次，**两次轮换后又
复发**——一份需要人维护的清单本身就是漂移源，而单一事实源不是。

**裁定的边界（写进操作单，防止矫枉过正）**：**字面 ID 只保留在「字面本身就是机制」
的位点**——§4 CLI 块、门 4 要比对的两个 token 序列、§3 步骤 4 的
`--validate-completion`、步骤 5 的 `analyze` 命令、§1 槽位行、§2.x 的 create-once
前置路径。这些地方去实例化会毁掉机制本身。其余活跃散文一律改指 **§1「本轮采集 ID」
行**；历史节保留其当时的具名 ID。

#### C. 本角色自查：复核之外又找出八处（据实记账，含一处本轮自造）

修复后本角色做了一次对抗自查（四路镜头：逐 finding 闭合 / 承重字面 / 门漂移 /
操作员走查），**在复核点名的实例之外又找出八处**，均已同轮修掉：

1. **§4 尾注**「臂 B 余下四次…**每次各需用户逐字 GO**」——F8/F10 残留，且与 12 行外
   本轮新写的 §5 前提直接打架。
2. **§4 本角色新写的句内自相矛盾**：同句既说「同臂轮换只动前者（恰 1 行）」又说
   「本轮换掉 2 个」——2/16/17 只对 `408acd7` 成立，该括注从未点名基准。已写死两个
   基准并指明 (b) 归因按 2 行。
3. **§6 另两条**（`:1640`/`:1684`）仍以现在时断言逐次 GO 制。
4. **§2.19 其实已经执行了**（`29e903a`，本轮磁盘复验：归档 6 项、`frames/` 0 项、
   六 shared 缺席），而抬头仍写「待执行」；§2.20 同理（已 136/136）。
5. **本角色在这次返工里新造了一处**：P4 补记时写下「（本轮的归档节是 §2.19）」——
   既硬编码了节号、又是假的。**这正是本批次要消灭的那一类**，据实记账不淡化。
6. §2.18 历史注里最后一个硬编码「本轮 → §2.x」指针。
7. **§3 步骤 3**「这是本项目第一次让机体真的动」——对 B3 为假，且它位于**启动
   tracker 之后**（run 目录已 create-once、ID 已消耗）；按 BC-BODY1-22 唯一合法动作
   是 fail closed，而此时退出 Play 即 `…POST_TRACKER_EARLY_EXIT`，烧 slot。
8. §2.17 的「臂 B trial 2–5 仍需用户逐字 GO / `SCENE_DEGENERATE` 决定尚未答复」——
   两项均已被答复与批量 GO 取代，按本文件先例补「已兑现 / 时间边界」。

#### D. 其余 Notes 裁定

- **N34**（臂 B 槽位行未继承「两个旧 canonical ID 仍 `run_id_void_consumed`」复验
  子句）：**声明该断言由 §1 acquisition IDs 总表行 + focused 套件承载**，不恢复
  逐轮子句——逐轮复述正是本轮在治的重复源。机械事实由复核轮 10 探针复验仍真。
- **N35**（§2.19 误重复调用零副作用）：**附议复核与实现角色的定性**（操作失误、
  零副作用、非合同/工具缺陷）；采纳其建议，将来的 §2.x 归档合同加一句「执行脚本
  失败时以逐项不符报告有序退出」——**本轮不加**，因 §2.19/§2.20 均已执行，改已执行
  节属改历史；下一份归档合同（B3 的）起生效。
- **N36**（§6 提交边界声明自 rev 19 后停摆）：**声明「revision 20 起边界事实并入各
  修订抬头」**，不补记历史条目——补记会制造第二份索引，正是 N36 自己点名的漂移源。
- **N30、N12/N15/N18/N20/N21/N22/N28/N33**：区间零代码触碰，逐项过账不变。

#### D′. 复核轮 10 剩余非阻断项的落地（接受轮 64 续批）

复核轮 10 的九条 must-fix 已在上批全部落地；本续批处理两类事项：上批落地后本角色
自查仍留存的残项（第 1、2 项，认定与撤回均本角色自判），与 D 节只裁定、未写进操作单
的两条（第 3、5 项）；第 4 项为 N34 依据的实测复核。**（接受轮 65 按复核轮 12 P9
更正：原句写作「处理其 RESIDUAL RISK 段点名的非阻断项」——复核轮 10 并无该段，
第 1、2 项系本角色自查所得，把自查结果记到独立复核名下属出处虚指。）**

1. **导出规则被判为假的普适机制，已撤回**。上批把步骤 0′/门 1 的落盘地改成「采集 ID
   去掉 `p1-m3-body-001-` 前缀」的机械导出——**该规则对臂 A 为假**：A1 的采集 ID 带
   `-attempt-4` 后缀（导出的文件名磁盘上不存在），A3/A4/A5 根本没有自己的证据文件
   （与 A2 共用 `…-arm-a-trial-2.md`）。磁盘实测只有五个 `…-arm-*` 证据文件。
   **改用单一事实源指向**：落盘地以**当轮 §2.x Play 前核对节开头具名者**为准
   （§2.20 已在节首具名 `…-arm-b-trial-3.md`），与 N37 的裁定同构，且永远正确。
   同时消除该句里嵌套反引号导致的渲染失真（前缀会被渲染成正文）。
2. **§5 的账本转录补全**：原只写 `--compare` 一项排除，本批补上其余排除项。
   **（接受轮 65 按复核轮 12 F11 更正本条）**：当时把 **两条**账本条目的排除项合并
   后称「账本 2026-08-14 逐字…不作增减」——批量 GO 条**不含** R10/R11、R12（那三项
   只在已放电的 B1 单次 GO 条里，而该条同时含已被取代的「臂 B trial 2–5」），措辞
   亦非逐字。已按来源拆分：批量 GO 条逐字部分与「另按在案现状继续排除」分列，并
   删除「不作增减」的自证。**无净授予**（各项另有 BC-BODY1-15 (d)、void 中止条款与
   §6 条目各自封堵）。
3. **N36 的裁定写进 §6**（此前只在提案里）：声明「自 revision 20 起边界事实并入各
   修订抬头，本节不再逐修订补记」，并说明理由——补记会制造第二份索引。
4. **N34 的依据本轮实测复核**：§1「acquisition IDs」总表行**确实逐字承载**两个旧
   canonical ID 的 `run_id_void_consumed` 断言（A1 侧「原 A1 ID 已被 attempt-3 void
   现场消耗，永久拒绝」、A2 侧「原 A2 ID 已被 attempt-1 void 现场消耗，
   `run_id_void_consumed` 永久拒绝」）。故 D 节「由总表行承载、不恢复逐轮子句」的
   裁定**有据**，非空头声明。
5. **N35 的落点确认**：「执行脚本失败时以逐项不符报告有序退出」写进**下一份**归档
   合同（B3 结束后由本角色起草），不改 §2.19/§2.20 两个已执行节——改已执行节即改
   历史。本条在此登记以免遗失。

复算：冻结值 token 对候选 `9cadebd` 逐项无减少；**§4 CLI 块对候选零差异**（本批与
上批均未触碰）；步骤 0′ 段反引号配对。**本续批同样未经独立复核。**（时间边界：落地
时未知复核轮 11 已于同日 23:54 收官且其范围恰为 `9cadebd..6e81bc2` 一个提交；本续批
的复核覆盖由复核轮 12 承担。）

#### E. 闭合与未释放

四条 CLASS_2 均 `NOT_MECHANIZABLE`（操作单属文档，仓库无处可写断言），闭合 =
**下一复核轮定点复看** §2.20 第 5 项 / §4 全节 / §3 步骤 0′、1、门 1 / §5 前提区与
§6 相应条，外加本轮自查新修的八处。**本轮修复本身未经独立复核。**
未释放：`--compare`、任何调参；批量 GO 的边界不变。

### Acceptance round 65 — 2026-08-15（消费 Review round 12：F11 返工 + P8/P9 应用）

Decision: **`ROUND12_REWORK_APPLIED_CLOSURE_BY_TARGETED_REINSPECTION_PENDING`**。
零 Play、零 ID、零代码、零阈值；冻结值对候选 `a5fc735` 逐项无减少，**§4 CLI 块对
候选零差异**。修复归本角色——三处文字全是本角色所写。

#### A. F11 复判：同意 CLASS_2，且本角色亲自复核了账本事实

**不照单全收**：先自查账本两条条目的实际措辞，再定级。

| 账本条目 | 排除清单实际措辞 | 含 R10/R11、R12？ |
|---|---|---|
| **批量 GO 条**（2026-08-14「照跑 B2–B5」） | 「**不覆盖** `--compare`（需十次齐备并**单独授权**）、任何重试/重进/调参、任何协议/指标/阈值/测量窗/载体/统计量变更」 | **否** |
| B1 单次 GO 条（同日，**已放电**） | 「臂 B trial 2–5、任何重试/重进/调参、`--compare`…、修改协议/指标/阈值/测量窗/载体、R10/R11、R12」 | 是 |

**故 F11 成立且分级正确**：本角色把 B1 条的 R10/R11、R12 记到批量 GO 条名下
（对批量 GO 是**增**），又略去 B1 条的「臂 B trial 2–5」（对 B1 条是**减**——略去
本身是对的，因它已被批量 GO 取代，但那就不能再自称「逐字」）；两条的措辞也不同
（「任何…变更」vs「修改…」，后者无「统计量」）。**「逐字…不作增减」对任一具名单源
都不成立。**

**同意复核对危害的判断**：操作面无净授予（各项今日均真不可为），但这是标着「最高
优先级」的**授权判据文字**，其自证邀请逐字审计——照字面对账会在一份**完好**的授权上
判出不符（与 F7 同型）；且 (c) 起草者引用它，就会把「批量 GO 逐字排除 R10/R11、R12」
这条**账本没有的条文**写进冻结的 (c) 记录。在「账本没有的授权视为未发生」的项目里，
**给账本安上没说过的话，与漏记授权是同一完整性的镜像破坏**。

**修复按处方做来源拆分**（不动任何门/数值）：批量 GO 条逐字部分单列；R10/R11、R12
改列为「另按在案现状继续排除（**非批量 GO 条文，不得记到该条名下**）」，注明依据是
COORD-007 账本 2026-08-12 未授权 + B1 条曾点名；并**删除「不作增减」的自证**。
提案 D′ 第 2 项与状态板 Log 分句同批更正。

#### B. P8/P9 复判：同意 CLASS_3，逐字补丁同轮应用

- **P9 我判得比复核更重一层（但仍属 CLASS_3，因不涉数值/判据/执行顺序）**：
  D′ 开头写「处理其 RESIDUAL RISK 段点名的非阻断项」——**复核轮 10 并无该段**
  （全仓 grep 除该句外零出现），第 1、2 项是**本角色自己**那轮对抗自查的产物。
  **这是把自查结果记到独立复核名下**，与 F11 是同一族错误：**给一个来源安上它没说
  过的话**。同一批次里犯两次，说明本角色在「转述他人结论」这件事上需要机械核对而非
  凭印象——已按处方逐字替换，并在此据实记账。
- **P8**：D′ 末段说本续批「与上批一并挂在闭合轮的定点复看范围内」，而闭合轮
  （复核轮 11）已于续批落地前 4 分 35 秒收官、范围恰为 `9cadebd..6e81bc2` 一个提交，
  续批不在也不可能在其范围内。已按处方替换为时间边界表述。
- **P7**：复核维持「候 (c) 批次」处置，本角色**同意**，本轮不动。

#### C. 闭合与未释放

F11 `NOT_MECHANIZABLE`，闭合 = **下一复核轮定点复看** §5 前提块、提案 D′ 第 2 项与
状态板该 Log 分句；P8/P9 随同复看。**本轮返工同样未经独立复核。**
未释放：`--compare`、任何调参；批量 GO 边界不变。**B3 的 (c) 在 F11 修正后不再被
本条阻塞**（复核轮 12 明文：修复是一句话的来源拆分，不阻塞其余 (c) 准备），但
(c) 前仍须由实现角色在最终 HEAD 重跑 §2.20 与 §2.0 (b)。

### Acceptance round 66 — 2026-08-16（消费实现角色的发令时刻复查 + 处置其登记的归因缺陷）

Decision: **`RUNTIME_DERIVED_ATTRIBUTION_RESTORED_AWAITING_FINAL_PREPLAY_RECHECK`**。
零 Play、零 ID、零代码、零阈值；冻结值对 `d278ef2` 逐项无减少。

#### A. 实现角色登记的缺陷：**成立，且比其描述更尖锐**

实现角色报告：操作单把「已复核候选」写死为 `408acd7` 并规定 (b) 归因「按 2 行写」，
而复核轮 11 通过后候选已前移，照字面填即虚假归因。**本角色实测复算**：

- `<BASE>` 运行时现取 = **`6e81bc2`**（复核轮 11 的通过候选）。
- §4 CLI 块对**现行**候选 **0 行不同、整块同 SHA `fd832df1…`**；对已过期的
  `408acd7` 才是 2 行。
- 故操作单写死的「2 行」在今天**恰好是错的**；而照字面取 `408acd7` 又违反 §2.0 (b)
  自身的「运行时现取、禁手写」与 COORD-007 R7「可派生标识禁手写」。

**这条比 F7–F11 更值得记一笔**：它的失效触发源**不是轮换，而是复核通过本身**。
本角色在 revision 21/22 写下那两句"两个基准"澄清，本意正是防止 (b) 填错数——结果
为了防错而把一个**可派生标识**钉进了文档，恰好撞上 COORD-007 R7 要禁的那件事。
**防错措施自身成了错误来源**，且只有在复核通过时才引爆。

#### B. 修复：不写死候选，也不写死答案

五处活跃指令全部改为运行时表述（历史陈述保留并加时间边界）：revision 22 抬头 A 点、
revision 21 抬头的"两个基准"句、§4 散文的参数计数句、§4 的"其余 17 行"句、§6
revision 21 条目。**核心改动是一句话的性质变更**：

> 差异行数**不是常量，是一次测量的输出**——`<BASE>` 按 §2.0 (b) 运行时现取，
> **实测几行就报几行**；写死的行数会在下一次复核通过时变成虚假归因。

本角色未把新的行数写进文档（写「0 行」会重犯同样的错，只是错在下一次）。

#### C. 独立复算（只读，与实现角色报告逐项相符）

**七条 `--verify` 亲自复跑全部退出 0 且逐字复现**：臂 A 五个 `WITHIN_RANGE`
（`0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` /
`0.5783206310103214` / `0.5783243208518966`），**B1、B2 均 `SCENE_DEGENERATE` /
`1.0`**；`runtime/frames/` **0 项**、七处归档俱在、**B3 run 目录不存在**；
(b) 归因实测：`<BASE>` = `6e81bc2`，delta 全是文档路径，**测量侧 0 条**。
另确认实现角色对 §A 失效的判断属实——其 (b) 归因的测量时点是 `29e903a`，其后六条
提交落地且复核轮 11 前移了候选，故整段失效，重取正确。

#### D. 交回与顺序（本轮是 (c) 之前的最后一个接受批次）

本批次提交会再次改变 HEAD，故 **§2.20 与 §2.0 (b) 需由实现角色在本提交之后再复查
一次**——这不是循环：**(c) 之前的最后一个提交必须就是 (b) 所报告的那个 HEAD**，
本角色在 (b) 交回后不再提交，直接写 (c)（(c) 本身保持未提交以满足 (d)）。

未释放：`--compare`、任何调参；批量 GO 边界不变。**F11 与本轮修复均未经独立复核**，
一并挂在下一轮定点复看。

### Acceptance round 67 — 2026-08-20（B3 归因 = 有效；未放行 Play 的偏差归因 + revision 23）

Decision: **`ACCEPTED — B3_VALID_TRIAL`**（arm B **3/5**）+
**`UNRELEASED_PLAY_ENTERED_NO_ACQUISITION_CONSUMED_B3_SHARED_ARCHIVE_PERMANENTLY_LOST`**
+ 操作单 **revision 23**。零 Play 消耗于本轮的判定动作本身。

#### A. 归因：B3 有效（接受角色独立复算，只读）

- **`--verify` 亲自复跑**：退出 **0**，逐字返回
  `{"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0,
  "run_id": "p1-m3-body-001-arm-b-trial-3", "verified": true,
  "window_c_track_given_geom": 1.0}`。
- **身份链**：`run_id` 即 canonical slot；receipt **正确地不含** attempt/predecessor
  任何键；`body_policy = threshold`、`planner = threshold-corridor-v1`、
  `condition = follow`、`init_frame_id = 0`、scenario 与可见弧 SHA 相符；run 目录 11 份。
- **四门 + 握手**（证据 §D，本角色复核）：门 1 `reported_sim_t = 4.980350971221924`
  ∈ `[2, 10)`、两侧余量 `2.980 s` / `5.020 s` 不贴边；门 2 最低帧 `0`；门 3 用户目检
  「匹配」；门 4 两 token 核对为真；tracker 自然退出 0、validator 产出确认词、
  用户报「已退出，没有报错」。两条域完整性门零触发，`loop_frame_count` **530**。
- 不匹配任何 void 终态 → **有效 trial，与 A3 配对，臂 B 3/5**。

#### B. 三次臂 B 并列（登记，n=3 仍不支持任何主张）

| 量 | B1 | B2 | **B3** |
|---|---|---|---|
| `full_loop_c_geom` | `1.0` | `1.0` | **`1.0`** |
| min_side 满分格点 | 125/125 | 125/125 | **125/125** |
| `body_motion_effort_m` | `88.645` | `75.269` | **`91.175`** |
| `body_path_length_m` | `61.423` | `49.162` | **`64.455`** |
| `planner_switch_count` | `11` | `11` | **`11`** |
| `corridor_blocked` 帧 | 324 | 339 | **319** |
| `nees_median` | `5.07` | `5.30` | **`5.20`** |

- **两条预登记限制各获第三次确认**：`SCENE_DEGENERATE` 三连，min_side 三次满分。
- **实现角色主动推翻了自己在 n=2 时登记的方向性读法**（证据 §E 第 4 条）：轮 63 记过
  「`corridor_blocked` 324 → 339 而位移下降」，B3 是**阻塞最少（319）配位移最多
  （`91.175 m`）**，三点合起来反成同向。**本角色附议其结论**——这正说明 n=2 的方向性
  读法不可靠，该条按原则只登记、不作主张，且**不得据以调参**（BC-BODY1-15 (d)）。
- **`planner_switch_count` 连续三次恰为 `11`**，登记备查。
- **操作性发现（无门）**：B3 的 post-tracker 停留 `76.803711 s`，圈数 `1.952997`，
  距已撤下的 `2P` 仅 `10.01 m`。**本轮不受任何影响**（上界轮 42 已撤、两门未触发），
  但**采纳实现角色的建议**：B4/B5 在确认词产出后更快请用户退出（BC-BODY1-29 本就
  要求「随即」），把停留压回 30–40 s 量级。**这是操作纪律，不是新门。**

#### C. 未放行 Play 的偏差归因（2026-08-20）

**事实（本角色实测，非转述）**：今日 14:30 有一次 Play 被进入并写出 315 帧与 shared
侧 truth/metrics；用户报告已暂停，本角色实测帧数静止、**tracker 未启动**、
`runtime/runs/p1-m3-body-001-arm-b-trial-4/` **不存在**。用户说明其**误以为在跑 B3**
（B3 实际已于 8/17 跑完）。该次 Play **没有**任何放行：操作单未轮换（§1 仍 B3）、
无 B4 的 §2.0 (c)、(d) 亦不成立（工作树里那份未提交 (c) 是 B3 的、记的 HEAD 是
`6b138ea`，而 HEAD 已前移）。

**归因（三条，逐条给依据）**：

1. **未越过不可逆点**：tracker 未启动 → 无 run 目录、**无采集 ID 被消耗**；
   `--run-id` 若用 B3 会撞 create-once，若用 B4 则属未授权 ID。**故无 canonical slot
   被烧。**
2. **不触发批量授权的中止条款**：该条款的触发词是「**任何 void 终态**」，而本次未
   到达四种具名终态中的任何一种（tracker 未启动即不可能有 post-tracker 终态；
   pre-tracker 的两种也未触发）。**故 B4/B5 的授权继续有效。**
3. **GO 计数：不计入 B4 或 B5。** 账本原文是「B2、B3、B4、B5 **各一次 Play**」——
   逐 trial 枚举，不是四次可互换的额度池。今日这次进入不是其中任何一次（B3 的那次
   已于 8/17 用掉），故**不消耗 B4/B5 各自的那一次**；它是**授权范围之外的一次
   Play 进入**，按偏差登记。**本裁定是本角色的判断，用户可推翻**；若用户认为应按
   「每次进入 Play 即消耗」从额度里扣，则 B4/B5 之间只剩一次，须另行授权。

**永久性损失（据实登记，不淡化）**：B3 的 shared 侧工件**已被本次 Play 覆盖**——
`runtime/frames/`、truth、metrics 与三个发布文件现在装的是今日这次的字节。实现角色
在 8/17 的交回事项里**明确警告过**「B4 不得在两件事落地前开工：B3 的归因，以及 B3 的
post-run 归档——shared 槽位现在压着 B3 的产物」，该警告因本次未放行的 Play 而落空。
**后果**：**B3 的 post-run 归档永久不可能执行**（源已不存在），臂 B 三次里只有 B1/B2
有归档。**缓解是实打实的**：B3 的 run 目录含 create-once 存档的全部绑定输入，故
`--verify` 今日仍逐字复现（本角色刚复跑）——**绑定证据完好，丢的是 shared 侧那份保全
副本**（原始传感帧目录与三个发布文件在 B3 结束时的状态）。**不为此追改任何已判结果。**

#### D. revision 23

1. **§2.21（新，待执行）**：**今日未放行 Play 的现场保全**——把 shared 侧六项移入
   具名 hold `…-unreleased-play-20260820-hold`，与四处 void hold 同构（移动不删除，
   destination 移动前必须不存在）。**钉住值本轮无法预先实测**：起草时用户仍在 Play
   中，退出时可能有末次 flush，故**改由实现角色在移动前实测并落盘，接受角色事后逐项
   复核**——此偏离「接受角色预先钉住」的惯例已在此逐字披露。
2. **§2.22（新，待执行）**：B4 的 Play 前核对（**七个** run 目录 + **七处**归档——
   注意归档数**不再等于** run 目录数，因 B3 无归档，该差额即上文的永久损失）。
3. **槽位轮换到 `p1-m3-body-001-arm-b-trial-4`**（批量授权已覆盖，无需新 GO）：
   §1 采集 ID 行、§3 步骤 4/5、门 4 token、§4 CLI 的 `--run-id`；`--body-policy
   threshold` 不动。机械确认（本轮实跑）见状态板。
4. **§2.19/§2.20 转历史**；**B3 的归档合同不再起草**（源不存在，写一份不可执行的
   合同只会制造第二个失效指针）。
5. 处置 `RUNBOOK_REVISION_23_UNRELEASED_SITE_PRESERVATION_AND_SAME_ARM_ROTATION_
   NO_GATE_RELAXATION_REVIEW_DEBT_REGISTERED`。

#### E. 未释放 / 仍欠

`--compare`、任何调参、任何协议或统计量变更均无 GO。**B4 的发令仍须走 §2.21 → §2.22
→ §2.0 (b) → (c)/(d)**。复核债照挂：F11 返工（轮 65）、轮 66 的归因修复、本轮
revision 23 均未被任何复核轮覆盖。

### Acceptance round 68 — 2026-08-20（§2.21 执行前实测：轮 67 §C 的损失范围更正 + revision 24）

Decision: **`ACCEPTED — ROUND_67_C_LOSS_SCOPE_CORRECTED_B3_SHARED_RESIDUE_PRESERVED_SEPARATELY`**
+ 操作单 **revision 24**。零 Play、零采集 ID、零 `runtime/` 写入；本轮全部动作为只读实测
与文档。**本轮不改任何冻结值、门、指标或 disposition**；B3 仍是有效 trial（臂 B 3/5）。

#### A. 触发：对**尚未执行**的 §2.21 做执行前实测

§2.21 由轮 67 起草、尚未执行。本角色在把它交给实现角色之前，按本文件惯例先只读核对
「源存在 / destination 不存在」，实测结果与轮 67 §C 的事实陈述**不符**，故本轮更正。

#### B. 实测（只读，逐条给依据）

| 六项 shared 成员 | mtime | 归属 |
|---|---|---|
| `runtime/frames/`（**315** 项） | 2026-08-20 14:30:13 | 08-20 那次未放行 Play |
| `runtime/m3_body_truth.jsonl`（29 行 / 30300 B） | 2026-08-20 14:30:13 | 同上 |
| `runtime/metrics.json`（61 行 / 2020 B） | 2026-08-20 14:30:12 | 同上 |
| `runtime/body_command.json`（15 行 / **331** B） | **2026-08-17 00:05:11** | **B3** |
| `runtime/gimbal_command.json`（15 行 / 341 B） | **2026-08-17 00:05:11** | **B3** |
| `runtime/tracking_observation.json`（18 行 / **454** B） | **2026-08-17 00:05:11** | **B3** |

三条独立佐证，指向同一结论——**三个发布文件从未被 08-20 那次 Play 写过**：

1. **机制**：写这三个文件的是 tracker（controller 侧）。轮 67 §C 自己已认定
   **tracker 未启动**，那么它们就不可能在 08-20 被写；Unity 侧只写 `frames/`、
   truth、metrics（与两份 audit）。**轮 67 的三条归因结论与它自己的损失陈述互相矛盾**，
   本轮取前者。
2. **包内时戳**：`tracking_observation.json` / `body_command.json` /
   `gimbal_command.json` 的 `issued_unix_s` 依次为 `1786939511.56761` /
   `1786939511.5728672` / `1786939511.5697339`，换算均为 **2026-08-17 00:05:11**，
   与 B3 run 目录内 `metrics.final.json` / `summary.json` 的 00:05 落盘时刻一致。
3. **与 B2 归档对照**：三份的 SHA-256 与 `…-arm-b-trial-2-post-run/` 内同名三份
   **全不相同**（B2 的 `body_command.json` `issued_unix_s = 1786749649.460062`，
   328 B vs 现行 331 B），故也不是 B2 的陈旧残留。

#### C. 更正（收窄，不翻案）

- **轮 67 §C 原文**「`runtime/frames/`、truth、metrics **与三个发布文件**现在装的是
  今日这次的字节」——**后半句不成立**，本轮更正。
- **不变的部分**：`frames/`、truth、metrics 三项确已被覆盖 → **B3 的完整 post-run
  归档（六项）永久不可能**，轮 67 的这一结论**成立**；归档处数 7 仍少于有效 run 数 8。
- **变的部分**：永久损失是 **六项中的三项**，不是六项。轮 67 高估了范围，**据实收窄**。
  B3 的绑定证据仍完好（run 目录 create-once 存档，`--verify` 逐字复现），本次更正
  **不改变 B3 的任何判定**。

#### D. revision 24（只改 §2.21/§2.22，槽位与 CLI 一行不动）

1. **§2.21 按来源拆两组**〔**本条的划分与落点已被复核轮 13 F12 推翻，见接受轮 69；
   现行以操作单 revision 25 为准**〕：A 组（08-20 Play 的三项产物）→
   `…unreleased-play-20260820` hold；B 组（B3 的残留三项）→
   **`runtime/test-results/p1-m3-body-001-arm-b-trial-3-shared-residue-3of6/`**。**理由**：revision 23 把六项一并塞进 08-20 的 hold，会给
   B3 仅存的字节**贴上错误标签**，而这是最后一次能给它们贴正确标签的机会。目录名含
   `3of6`、**不含 `post-run`**，故任何按 `*post-run*` 的清点都碰不到它，不会被误读为
   第八处归档（实测：仓库内无任何工具按 `post-run` 检索，归档纯属文档纪律）。
2. **钉住值改回接受角色预先钉住**：现场自 08-20 14:30 起静止，本轮已把六项全部实测并
   **以全 64 位**写进 §2.21 两张表（轮 10 F7 的规矩）。**revision 23 的 D 条偏离
   （改由实现角色事后钉）就此取消**——那条偏离的前提是「起草时用户仍在 Play 中」，
   该前提今日已不成立。实现角色在移动前须**重新实测**，**任一项不等即停止回本角色**
   （不等即意味着现场又被写过，属新事件）。
3. **§2.22 增至十项**：第 7 项收窄为 A 组三个 destination；**新增第 10 项**核对 B 组
   目录恰 3 项且逐项等于钉住值；第 5 项的七处完整归档与七个聚合值**一字未动**，只把
   差额注解指向 B 组目录。
4. **顺带核验（F7 失效模式的定点复查）**：§2.22 第 5 项七个聚合缩写与各自源节
   （§2.9/§2.11/§2.13/§2.15/§2.17/§2.19 与 `…-arm-a-trial-2.md` §N.1）的全 64 位值
   **逐个比对，7/7 相符**（`ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` /
   `281bb6d8…3b2c` / `9dc67a76…a62b` / `09f1ac61…524c` / `71f65dca…0f85`）。本项**不改**。
5. **非门登记**：`road_scene_audit.json` / `route_corridor_audit.json` 的 mtime 同为
   08-20 14:30，但两者从不属于六项 shared 成员、从未进过归档、每次 Play 都重写，
   §2.21 不动它们，其 mtime 不得被读作额外 Play 的证据。
6. 处置 `RUNBOOK_REVISION_24_LOSS_SCOPE_CORRECTION_AND_SPLIT_PRESERVATION_
   NO_GATE_RELAXATION_NO_FROZEN_VALUE_CHANGE_REVIEW_DEBT_REGISTERED`。

#### E. 未释放 / 仍欠

`--compare`、任何调参、任何协议或统计量变更均无 GO。**B4 的发令仍须走 §2.21 → §2.22
（十项）→ §2.0 (b) → (c)/(d)**。复核债照挂并**再加本轮**：F11 返工（轮 65）、轮 66 的
归因修复、revision 23（轮 67）与 revision 24（本轮）均未被任何复核轮覆盖；PLAY_GOVERNING
上「上一通过候选 → HEAD」的差异恒为操作单一处，具名 disposition 见上 6。
#### F. 用户当场裁定（2026-08-20，已逐字入账 `docs/authorizations.md`）

本角色就两件待决事项单独请示，用户三项选择如下（原话为选项文字）：

1. **"维持轮 67 裁定（推荐）"** → 轮 67 §C.3 的 GO 计数裁定**确认生效**：08-20 那次
   未放行的 Play **不从 B4/B5 扣**，两次 Play 仍在，按授权范围外的一次进入登记为偏差。
   该项不再是待决项。
2. **"先复核再放行 B4（推荐）"** → **B4 的 Play 放行前必须有一轮独立复核结论**。范围 =
   PLAY_GOVERNING 差异（恒为操作单一处，含 revision 23 与 24）加提案轮 65–68 的 delta。
   **这是本项目第一次由用户把复核轮前置为放行条件**；此前同类差异一律按「具名
   disposition + 登记复核债、不阻断」处理（轮 46/58/61）。**推迟或跳过须另行逐字授权。**
3. **"提交（推荐）"** → 本批次落盘提交。

**执行顺序（本角色判断，已向用户披露）**：用户推迟的对象是**B4 的 Play 放行**，
故 **§2.21 保全先行**，**§2.22 与 §2.0 (b)/(c) 等复核结论**。理由是风险不对称——B3
shared 侧仅存三项若被又一次误入的 Play 覆盖即**永久不可恢复**；而 §2.21 万一被复核
判错，最坏只是可恢复的记账返工（移动不删除、移动前后逐项钉住）。**复核结论落地前
不得进入 Play。**

### Acceptance round 69 — 2026-08-20（消费复核轮 13：F12/F13 返工 + P10 应用 + revision 25）

Decision: **`ACCEPTED — ROUND13_REWORK_APPLIED_F12_ATTRIBUTION_CORRECTED_SPLIT_BY_SOURCE`**
+ 操作单 **revision 25**。零 Play、零采集 ID、零 `runtime/` 写入、零代码改动；不改任何
冻结值、门、指标或 disposition。B3 仍是有效 trial（臂 B 3/5）。

#### A. F12（CLASS_1）——照单接受，且本角色独立复算成立

复核轮 13 判本角色轮 68 的 §2.21 A 组归属错误。**本角色逐条独立复算，四条证据链全部
复现**：

| 组 | 项数 | frame id | mtime | 包内 `capture_unix_s` |
|---|---|---|---|---|
| **B3** | **256**（128 id ×2） | **907…1034** | 2026-08-17 | `frame_1034` = `1786939588.328` |
| 08-20 未放行 Play | **59**（29 id ×2 + `latest.json`） | **0…28** | 2026-08-20 | `frame_28` = `1787250613.018` |

机制经本角色读码确认：`Assets/TetheredTracking/Scripts/SensorFrameWriter.cs:212` 的
`DeleteExpiredFrame(framesDirectory, publishedFrameId − retainedFrameCount)`
（`retainedFrameCount = 128`，L106）**按 frame id 淘汰、不按 mtime**；新 Play 从 id 0
起算，淘汰目标为负，够不到 907 以上。算术闭合 `(1034 − 650) / 5 Hz = 76.8 s` = B3 的
dwell `76.803711 s`——907…1034 正是 B3 收尾停留期的保留帧尾，**归属无第二种解释**。

**本角色的根因（据实写明，不推给流程）**：轮 68 §B 的表给 `runtime/frames/` 只记了
**一个目录 mtime**（即其最新条目的时间），没做逐文件 mtime / frame id 分布核对，也没把
「Unity 侧只追加、按 id 淘汰」的机制纳入推理。**这与轮 68 纠正轮 67 的方式同型**：
轮 68 把「tracker 未启动 ⇒ 发布文件没被写过」推到位，却没把「按 id 淘汰 ⇒ 上一次
Play 的高位帧不会被删」推到位。**并且轮 68 加的「移动前重测六项」门挡不住它**——
七个钉住值本轮实测仍全相符，门会全过而归属照错；该门防的是「现场又被写过」，
**不防「归属判错」**（复核 N43，本轮已按其建议补入 §2.21）。

**损失范围第三次收窄（据实，不淡化也不夸大）**：`m3_body_truth.jsonl` 与
`metrics.json` **两项全损**、`frames/latest.json` **一项**（257 之 1）、**256 份帧与
三个发布文件完好**。**轮 67 记 6/6、轮 68 记 3/6 均为高估。** **结论层三次不变**：
B3 的完整六项 post-run 归档永久不可能，归档 7 处 < 有效 run 8 次，B3 的有效性与绑定
证据（run 目录 create-once + 八条 `--verify`）不受影响。

#### B. F13（CLASS_2）——补具名落盘地

§2.21 定为 **`docs/evidence/P1-M3-BODY-001-arm-b-trial-4.md`**。依据：§2.19 的先例是
「在下一 trial 的预备批次执行、落盘于下一 trial 的证据文件」，且与 §2.22 同一文件，
使「§2.21 的七项前后相等」与「§2.22 的十项」由接受角色在一处读完。**复核指出的
两可性就此消除。**

#### C. P10（CLASS_3）——独立复判后逐字应用

本角色独立复判：§2.22 第 6 项缺 §2.16 第 6 项的出处指针，属**缺失交叉引用**，不涉
数值、阈值、ID、判据、执行顺序或终态名 → **同意 CLASS_3**，按复核给的逐字替换补丁
应用，零数值/哈希/ID/disposition 改动。**P7 仍随 (c) 批次复判，本轮不动。**

#### D. N42 / N43 —— 两条观察全部采纳

- **N42（落点回既有惯例）**：**撤销** revision 24 把 B 组放进 `runtime/test-results/`
  的做法——七处 post-run 归档正住在那里，靠目录名回避误计是**缓解**不是**消除**。
  改用与四处既有 void hold 完全同构的平铺命名
  `runtime/<name>.arm-b-trial-3-shared-residue-hold.<ext>`，**从根上不可能被点成第八处
  归档**；同时把 `3of6` 这个会随认识变化而失效的数字**从名字里彻底去掉**（它已经失效
  过一次），精确构成改由 §2.21 表与 §2.22 第 10 项钉住。
- **N43（门的能力边界）**：§2.21 移动前的核对由「重测钉住值」一项**扩为两项**——
  新增**归属复核**：按 frame id 段（只允许 `[0,28]` 与 `[907,1034]` 两段、之间无文件、
  合计 315）与包内 `capture_unix_s`（`1786939588.328` / `1787250613.018`、`latest.json`
  的 `frame_id = 28`）核对划分，**出现第三段 id 或时戳与所属组不符即停止回本角色**。

#### E. revision 25 的内容

1. **§2.21 改为按来源分离保全**，**B 组先移（不可再生）、A 组后**；七个 destination
   的钉住值由本角色**移动前实测、全 64 位落表**（两个目录聚合
   `568b6b98…a815` / `39698be4…9a7f` + 五个文件的行数/字节/SHA-256）。
2. **移动后 `runtime/frames/` 恰 0 项**——315 = 256 + 59 全部移出，**目录本身保留，
   不删除、不新建**（revision 24 的「重建空目录」表述随之作废）。
3. **§2.22 第 2/5/6/7/10 项**同步改正；第 6 项即 P10；**十项数不变**。
4. **revision 24 抬头加不可执行标注**，指向 revision 25。
5. 转载同一表述的四份文档（提案轮 68 §D.1、`implementation-status.md`、
   `current-status.md`、`unity-test-log.md`）**同批更正**。
6. 处置 `RUNBOOK_REVISION_25_F12_ATTRIBUTION_FIX_AND_CONVENTION_ALIGNED_HOLDS_
   NO_GATE_RELAXATION_NO_FROZEN_VALUE_CHANGE_REVIEW_DEBT_REGISTERED`。

#### F. 未释放 / 仍欠

`--compare`、任何调参、任何协议或统计量变更均无 GO。**执行顺序**：§2.21（改正后）
→ **停** → 复核定点复看闭合 F12/F13/P10 → §2.22（十项）→ §2.0 (b) → (c)/(d)。
用户 2026-08-20 的放行条件继续有效，**复核结论落地前不得进入 Play**。
**紧迫性登记**：B3 的 256 份帧只在下一次 Play 发布到 **frame id ≥ 1035** 之前存活，
故 §2.21 先行不变。本轮返工本身未经独立复核。

### Acceptance round 70 — 2026-08-20（消费复核轮 14：P11/P7 应用 + N44/N45 + §2.0 (a) 放行）

Decision: **`ACCEPTED — ROUND14_PASS_CONSUMED_P11_P7_APPLIED_B4_PLAY_RELEASED_AT_STEP_A`**
+ 操作单 **revision 26**。零 Play、零采集 ID、零 `runtime/` 写入、零代码改动；不改任何
冻结值、门、指标、槽位或 disposition。

#### A. 消费复核轮 14 的 `PASS_WITH_NOTES`（`fcb22a7`）

零 CLASS_1、零 CLASS_2；轮 13 的 **F12/F13 全部关闭**，`passed_candidate` 前移到
`fcb22a7`。**本角色亲自复算了该轮的承重等式**：两个 hold 的 `shasum -a 256 *` 行合并
排序再取 SHA = **`274e9804098c337d02245c64780c349c5c886c6633e4d8e7e1364d8da3e52d4c`**
= 本角色轮 68 在移动前钉住的整目录聚合 —— **315 项零丢失、零改名、零字节改动**；
B hold **256** 项 id 恰 `[907,1034]` 无 `latest.json`、A hold **59** 项 id 恰 `[0,28]`
含 `latest.json`、三处平铺发布 hold SHA 等于轮 68/69 原值、`runtime/frames/` 恰 0 项
且目录保留。**接受该 verdict。**

**同意复核续会话的两处自我更正**：(1) 边界声明「副本已删除」在原会话落盘时尚未成真，
由续会话代删并据实改写；(2) 把「并集等式证明没有被分错组」**收窄**为「并集等式与分组
无关」——**这条收窄是对的**：并集只锁 (SHA, 文件名) 多重集，单独不排除两组互换；分组
正确性由**移动前的两个分组聚合**（本角色轮 69 按预定划分实测、移动后逐项相等）与
id 段 / mtime / 包内 `capture_unix_s` 三重划分承担。已按 N45 写进 §2.22 第 7 项。

#### B. P11（CLASS_3）—— 独立复判同意，逐字应用

§2.21 抬头「本轮第一步，待执行」→「**已执行**，2026-08-20」。属**已执行步骤的时态**，
在 §4.4 CLASS_3 闭集内，不涉数值/阈值/ID/判据/执行顺序/终态名；方向 fail-closed。
**不采纳**「按 §2.20 先例把 `38/38 + 36/36` 写进抬头」这一编辑选项——执行计数的一手
来源是 `…-arm-b-trial-4.md` §A.1/§A.3，抬头再抄一份只会多一个要同步的副本
（本文件已经因「多一个副本」吃过 F7 与轮 66 两次亏）。

#### C. P7（CLASS_3）—— 自轮 11 起挂「随 (c) 批次复判」，本轮即该批次，同意并应用

§2.19 历史注的一手来源由 `…-arm-b-trial-3.md` §A 改为 `…-arm-b-trial-2.md` §D。
**本角色实测核对**：24/24 机械核对与七条 `--verify` 的一手执行报告确在 trial-2
§D.1/§D.2（`29e903a` 批次），trial-3 §A 是 §2.20 时点的复验。纯引用精度，同意 CLASS_3。
**至此本 work item 无待决 CLASS_3。**

#### D. N44 / N45 —— 两条观察均采纳

- **N44**：§2.22 第 1 项写明其「六个 shared **文件**」与 §2.21 / 第 5 项的「六项 shared
  **成员**」**不是同一集合**（前者含 `scenario_config.json` 不含 `frames/`，后者相反）。
  两处口径本就一致、无操作歧义，本条只把差别摆到明面。
- **N45**：§2.22 第 7 项补记并集等式的出处与**它证明什么、不证明什么**。

#### E. §2.0 (a) 成立：B4 的那一次 Play 已放行

用户 2026-08-20 逐字授权 **"执行，授权执行play"**（账本同日条目，本轮当场代录）。
**本角色的读法（不替用户扩权）**：该次 Play 本就在 2026-08-14 批量 GO 之内，本条真正
解除的是**用户自己加的复核前置**；**B4 的额度仍是恰一次**，B5、重试/重进/调参、
`--compare` 与任何协议/统计量变更**均未授权**；**任何 void 终态仍立即中止批量授权**。

#### F. 本角色对 §2.22 十项的独立复算（**不替代** Implementation 的执行）

按 §2.16 的先例（轮 58 同款），本轮只读实跑一遍，与发令前 Implementation 的执行**互为
独立复算**：**十项全部相符**——六个 shared 文件全不存在、`runtime/frames/` 恰 0 项、
四处旧 hold `257/93/109/257` 且 attempt-3 run hold 恰 2 文件、八个 run 目录各恰 11 份、
**八条 `--verify` 全退 0 且逐字复现冻结值**、七处归档各 6 项 / `frames/` 各 257 项 /
七个聚合全中且 `*-post-run` 恰 7 处、八个具名标记全不存在、void hold 恰 10 份零隐藏、
A/B 两个 hold 与三处平铺 hold 逐项等于钉住值、`runtime/runs/p1-m3-body-001-arm-b-trial-4/`
不存在、corridor `9e2956ad…c800` = config pin / **779** 棱柱 / `tether_corridor_check =
true`、`canonical_trial_id` 返回自身、`_expected_policy` = `threshold`、
`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`、`expected_acquisition_ids('b')[3]`
逐字相等、`-attempt-1` 与 `-trial-6` 均被 `run_id_not_frozen_trial` 拒绝。
零写入（`git status --porcelain` 除本批文档外为空）。

#### G. 未释放 / 仍欠 / 时序

**接下来**：Implementation 执行 **§2.22（十项）** 与 **§2.0 (b)**（`<BASE>` 运行时由
`grep '^passed_candidate:' … | tail -1` 现取 = `fcb22a7`）→ 本角色写 **(c)** →
**(d)** 发令时刻工作树只允许 `docs/unity-test-log.md` 一份未提交差异 → 用户进 Play。
**BC-BODY1-21 自 (c) 写入起冻结操作单**，故 revision 26 必须、也确实落在 (c) 之前。
§2.22 或 (b) 任一项不符即**停止回本角色**，不得就地修正后继续。
`--compare`、调参、B5 与任何协议/统计量变更均无 GO；revision 26 本身未经独立复核
（纯 CLASS_3 应用 + 两处注解，PLAY_GOVERNING 差异恒为操作单一处）。

### Acceptance round 71 — 2026-08-20（arm B trial 4 归因 = 有效 B4；臂 B 4/5 + revision 27）

Decision: **`ACCEPTED — B4_VALID_TRIAL`**（arm B **4/5**）+ 操作单 **revision 27**。
本轮判定动作本身零 Play、零采集 ID、零 `runtime/` 写入。

#### A. 归因：B4 有效（接受角色独立复算，只读）

- **`--verify` 亲自复跑**：退出 **0**，逐字返回 `SCENE_DEGENERATE` / `1.0` /
  `run_id: p1-m3-body-001-arm-b-trial-4` / `verified: true` / 窗口 `1.0`。
- **四门 + 握手**（证据 §C，本角色复核）：门 1 `reported_sim_t =
  6.184971809387207` ∈ `[2, 10)`，两侧余量 `4.184972` / `3.815028` 不贴边——**本角色
  另做一次交叉验证**：run 目录内 create-once 的 `frames.jsonl` 里 frame **30** 的
  `simulation_time_s` 与该值**逐字相等**，frame 31 已无该字段（暂停之后），故门 1 的
  数确由保留帧机械导出。门 2 最低保留帧 `0`；门 3 用户目检「匹配」；门 4 两条肯定项
  为真；tracker 自然退出 0、validator 产出确认词、用户报「已退出，无报错」。
- **身份链**：`run_id` 即 canonical slot；receipt **正确地不含** attempt/predecessor
  任何键；`body_policy = threshold`、`planner = threshold-corridor-v1`、
  `condition = follow`、`init_frame_id = 0`；run 目录 11 份，九条 `--verify` 全过。
- **四种 void 终态逐条对照，无一匹配**（依据见 `docs/unity-test-log.md` 同日条目）：
  下界 `342.4017822330673 >= P 212.97056274847716` 成立，两条域完整性门零触发；
  失败类 reason 经本角色从 `frames.jsonl` 重算**全 0 帧**。
- → **有效 trial，与 A4 配对，臂 B 4/5。零 void 终态 → 批量授权不中止，B5 仍在覆盖内。**

#### B. 四次臂 B 并列（登记，n=4 仍不支持任何主张）

| 量 | B1 | B2 | B3 | **B4** |
|---|---|---|---|---|
| `full_loop_c_geom` | `1.0` | `1.0` | `1.0` | **`1.0`** |
| min_side 满分格点 | 125/125 | 125/125 | 125/125 | **125/125** |
| `body_motion_effort_m` | `88.645` | `75.269` | `91.175` | **`88.724`** |
| `body_path_length_m` | `61.423` | `49.162` | `64.455` | **`61.407`** |
| `planner_switch_count` | `11` | `11` | `11` | **`11`** |
| `corridor_blocked` 帧 | 324 | 339 | 319 | **324** |
| `nees_median` | `5.068` | `5.299` | `5.196` | **`5.245`** |
| 停留 / 圈数 | `41.390` / `1.619` | `29.602` / `1.510` | `76.804` / `1.953` | **`40.198` / `1.608`** |

- **两条预登记限制各获第四次确认**；结论口径不变（效应量只能报**下界**）。
- **B4 与 B1 近乎重合**：effort 差 `0.079 m`、path 差 `0.016 m`、`corridor_blocked`
  **同为 324**。**只登记，不作主张**——四个点仍不支持任何单调读法，n=3 时撤下的方向性
  读法不重提（B4 阻塞居中、位移也居中）。`planner_switch_count` 连续四次恰 `11`。
  **BC-BODY1-15 (d)：以上任何数字都不得据以调参。**
- **停留压回 `40.198 s`**（B3 的一半），轮 67 的操作纪律生效，**不是门**。

#### C. 裁定：门 4 的 `hold` 否定项（实现角色主动披露）

实现角色报告：`hold` 否定项若按**裸子串**判会假阳性（`threshold` 字面含 `hold`，
而 `--body-policy threshold` 正是本门要求存在的肯定项），故改按命名规约判，并请复核
核查是否放宽判据。**本角色的裁定，分两层**：

1. **门 4 按操作单原文本身就已通过**。§3 步骤 2 末段的门 4 **只要求两条肯定项**
   （`--body-policy threshold` 与本轮 `--run-id`）——**否定项从来不在操作单里**，
   是 Implementation 自 B2 起自愿加的门上加固。所以**不存在"放宽既有判据"这回事**，
   被讨论的对象根本不是门的组成部分。
2. **但这正是问题所在**：一组每轮都在跑、却从未被写下来的核对，等于每轮临场重新推导
   判据——B4 这轮就撞上了裸子串陷阱。**故 revision 27 把五条否定项收编进门 4**，并
   写死 `hold` 的判据（token 含 `-hold`，或以 `hold` 结尾且不等于 `threshold`）。
   **只增停条件、不放宽任何判据**；B2/B3/B4 三轮报的 `hold` False 与该判据一致，
   属**追认既有做法**。真出现 `*-hold` 的 run-id 或路径仍会被抓到。

#### D. revision 27

1. **§2.23（新，待执行）**：B4 的 post-run 归档合同，与 §2.9/…/§2.19 同构；钉住值由
   本角色**移动前实测、全 64 位落表**（`frames/` **257** 项 id 段 `[724,851]` 聚合
   `5ed64cf5…7ebf`；truth **852** 行 / **914667** B；metrics **61** 行 / **2054** B；
   三个发布件 328 / 342 / 459 B）；destination 起草时实测**不存在**。
   **移动后复跑九个 `--verify`**；**§2.21 的两处保全 hold 不得触碰**。
2. **门 4 否定项收编**（见 §C）。
3. **槽位不轮换**——`…-arm-b-trial-4` 已消耗，§4 CLI 一行不动。
4. 处置 `RUNBOOK_REVISION_27_B4_ARCHIVE_CONTRACT_AND_GATE4_NEGATIVES_CODIFIED_
   NO_GATE_RELAXATION_NO_FROZEN_VALUE_CHANGE_REVIEW_DEBT_REGISTERED`。

#### E. 归档为什么必须先做

shared 槽位此刻装着 B4 的产物。**B3 的教训**：一次误入的 Play 会当场覆盖 truth 与
metrics 且不可恢复（B3 的 256 份帧只是侥幸躲过按 id 淘汰，发布件只是侥幸没被写）。
**§2.23 执行之前不得进入任何 Play。**

#### F. 未释放 / 仍欠

`--compare` 仍需十次齐备并**单独授权**（现 9/10）；任何调参、任何协议或统计量变更
无 GO。复核债：revision 26（轮 70）、B4 的执行批次、本轮的归因与 revision 27 均**未经
任何复核轮覆盖**；PLAY_GOVERNING 差异恒为操作单一处。

#### G. 交给用户的一个选择（本轮不自行决定）

B5 是本批次最后一次采集。其 §2.0 (a) 由 2026-08-14 批量 GO **自身满足**，不需要新
GO。但**是否在 B5 之前再走一轮独立复核**，本角色不替用户决定——上一次用户正是选了
「先复核再放行」，而那一轮抓出了 CLASS_1 的 F12。故本修订**不轮换槽位、不起草 B5 的
Play 前核对**，等用户指示后另发修订。**无论选哪条，§2.23 的归档都先做。**

### Acceptance round 72 — 2026-08-21（消费复核轮 15：F14 返工 + N46/N47 处置）

Decision: **`ACCEPTED — ROUND15_F14_CORRECTED_B4_ATTRIBUTION_UNCHANGED`**。零 Play、
零采集 ID、零 `runtime/` 写入、零代码改动、**零操作单改动**（本轮不发修订）。

#### A. F14（CLASS_2）—— 照单接受，本角色实测复现

**轮 71 §A 的这半句是假的**：「run 目录内 create-once 的 `frames.jsonl` 里 frame 30 的
`simulation_time_s` 与该值逐字相等，**frame 31 已无该字段（暂停之后）**」。
**本角色复算**（`frames.jsonl` 逐行读，按 `compute_stage` 分列）：

```text
line 31  frame_id=30  compute_stage=update  simulation_time_s=6.184971809387207
line 35  frame_id=31  compute_stage=update  simulation_time_s=6.396984577178955
line 36/37/39  frame_id=31  compute_stage=None  simulation_time_s=None
```

**F14 成立。** 轮 71 §A 这半句**就此作废**，以本节为准。

**本角色的根因（据实写明）**：轮 71 的校验脚本按 frame id 只保留**末条**记录
（`found[fid]=st` 反复覆盖），frame 31 的 `update` 行被其后三条 null 事件行盖掉，
于是把**聚合产物**当成了磁盘事实。**这与 F12 那次「只读目录 mtime 就下归属结论」是
同一类毛病**：都是用一个降维后的视图去断言原始字节的性质。**教训收窄为一条可执行的
自律**：凡要断言「某文件里某字段不存在」，必须按**行**枚举并显示分组依据，不得依赖
任何 dict 覆盖式聚合。

**承重的半句成立且不受影响**：frame 30 的值逐字相等（复核轮 15 独立复现），门 1 判据
`2.000000 <= 6.184971809387207 < 10.000000` 成立。**B4 的有效性、轮 71 归因、四种 void
终态无一匹配、两条预登记限制的第四次确认、全部冻结值一律不动**（复核轮 15 明确不推翻）。

**磁盘上真正的暂停标记（采纳复核给的事实，本角色复算确认）**：暂停边界体现在**墙钟**
而非仿真钟——`capture_unix_s` 间隙 **`414.779 s`**，而仿真时间间隙仅 **`0.212013 s`**
（暂停期间仿真钟不走）；`frame_age_ms` 由 frame 30 的 `381238.8`（追平重放）骤降至
frame 31 的 `36.4`（实时处理）。**并且**：「启动前保留帧集为 0–30」本就由**门 2 的导出**
承载，轮 71 引那条旁证本身就是多余的——**返工不是换一条旁证，而是删掉不该有的那条**。

**本角色自查另找到第四处转载（复核轮 15 未列）**：`docs/current-status.md` 的**接受轮 71
Log 条目**同样把该半句写成断言。本轮就地加注作废。**登记这一点是因为它有普遍性**——
复核列的是它当轮读到的位点，不等于全部；返工方按同一句式全仓 sweep 才算做完。

**三处转载的处置**：状态板交接行由复核轮 15 自身改写；`docs/unity-test-log.md` 的 B4
`VALID_TRIAL` 条目由本轮**就地加注更正**（该文件是代录记录，非 append-only）；本提案
按 append-only 惯例**以本节追加更正**，轮 71 §A 原文保留但已作废。

#### B. N46 —— 采纳，就地更正

交接行与 Immediate next actions 的「7 commits」实测为 **8**（其自身提交入列后的位移，
与 B3/B4 (b) 报告的同族现象）；路径集合仍恰 **9**、全文档、测量侧 **0 路径**。
**该处已由复核轮 15 在其自身的状态板改写中更正为 8**，本轮复查确认交接行与
Immediate next actions 均已写 8，无残留；本节只作登记。

#### C. N47 —— 已落账（转述条目，经用户当场确认）

用户 2026-08-20 在实现会话给出的「B5 之前先走一轮独立复核」**至复核轮 15 收工仍未入
账本**。本轮已落账：**据实标明为转述**（来源 = 实现角色提交 `1879db2` 的提交信息原文），
并逐字记入用户在本会话的确认 **"就按这个意思做"**。按 AGENTS.md（2026-07-30 起）
「账本没有的授权视为未发生」，**本条落盘后该指示方可被引用为放行条件**。

#### D. B5 的放行状态（本角色裁定）

用户的放行条件是「B5 之前先走一轮独立复核」。复核轮 15 **已发生并给出结论**，但结论是
**`REWORK_REQUIRED`**。**本角色裁定：F14 关闭之后才放行 B5**，理由与 B4 那次一致——
B4 是走完「轮 13 `REWORK_REQUIRED` → 返工 → 轮 14 `PASS_WITH_NOTES`」才放行的；在一个
verdict 仍为 `REWORK_REQUIRED` 的候选上发令，与用户设该条件的本意相悖。
**F14 的闭合成本很低**：`NOT_MECHANIZABLE`，闭合方式是对两处具名位置（本节与 Unity 日志
B4 条目）做定点复看。**该裁定用户可推翻**——若用户认为纯文档 CLASS_2 不必挡住放行
（复核轮 15 自身也写明 F14 不触发闭环轮义务），本角色即按其指示放行。

#### E. 未释放 / 仍欠

B5 的**槽位轮换与 Play 前核对仍未起草**（revision 27 §2.23 末条），待 F14 闭合与放行
决定后另发修订。`--compare` **9/10**，须十次齐备并单独授权。本轮返工未经独立复核。

### Acceptance round 73 — 2026-08-21（消费复核轮 16：F14 闭合 + 轮换 B5 + revision 28）

Decision: **`ACCEPTED — ROUND16_PASS_CONSUMED_ROTATED_TO_B5`** + 操作单 **revision 28**。
零 Play、零采集 ID、零 `runtime/` 写入、零代码改动。

#### A. 消费复核轮 16 的 `PASS_WITH_NOTES`（`02c7c88`）

零 CLASS_1 / CLASS_2 / 新 CLASS_3；**F14 关闭**，N47 落账与 N46 复查均获核实，
`passed_candidate` 前移至 `02c7c88`。**本角色独立复查其闭合主张**：全仓 sweep 确认
「frame 31 已无该字段」的**活跃指令区零残留**——仅存的逐字原文是提案轮 71 §A 的
append-only 历史文本，已由轮 72 §A 明文作废（与 F12 闭合同一标准）。**接受该 verdict。**

**N48 登记**：轮 72 自设的「B5 在 F14 闭合之后才放行」，其条件**随轮 16 满足**。

#### B. 本角色对 §2.24 十一项的独立复算（**不替代** Implementation 的执行）

按 §2.16 / 轮 58 先例只读实跑一遍，与发令前 Implementation 的执行互为独立复算：
**十一项全部相符，共 63 条机械核对 63 PASS / 0 FAIL**——
六个 shared 文件全不存在；`runtime/frames/` 恰 0 项；四处旧 hold `257/93/109/257` 且
attempt-3 run hold 恰 2 文件；**九个 run 目录各恰 11 份**且**九条 `--verify` 全退 0 并逐字
复现**（臂 A 五个 `WITHIN_RANGE`，**B1–B4 四个 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`**）；
**八处归档各 6 项 / `frames/` 各 257 项 / 八个聚合全部命中**且 `*-post-run` 恰 8 处；
八个具名标记全不存在、void hold 恰 10 份零隐藏；**§2.21 七处保全 hold 逐项相符**
（A 组 59 项 / 939238 B / `39698be4…9a7f`；B 组 256 项 / 5513679 B / `568b6b98…a815`；
五个平铺件 15/331、15/341、18/454、29/30300、61/2020）；**并集等式重算 =
`274e9804…2d4c`**；`runtime/runs/p1-m3-body-001-arm-b-trial-5/` 不存在；
corridor `9e2956ad…c800` = config pin / **779** 棱柱 / `tether_corridor_check = true`；
`canonical_trial_id` 返回自身、`_expected_policy` = `threshold`、
`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`、
`expected_acquisition_ids('b')[4]` 逐字相等、`…-trial-5-attempt-1` 与 `…-trial-6` 均被
`run_id_not_frozen_trial` 拒绝。**全程零写入**。

#### C. revision 28

1. **轮换到 `p1-m3-body-001-arm-b-trial-5`**，五处逐一改：§1 采集 ID 行（B4 降为历史）、
   §3 步骤 4 的 `--validate-completion`、步骤 5 的分析命令、门 4 token 块、§4 CLI 的
   `--run-id`。**`--body-policy threshold` 不动。**
2. **§4 CLI 对已复核候选 `02c7c88` 恰 1 行不同**——**本角色从两侧 `git show` 抽块实测**
   （均 19 行；base SHA `154b06a6…dee2f`、HEAD SHA `cfab3494…d149`；唯一差异行即
   `--run-id`），**不采信抬头自述**，也**不写死行数**（`<BASE>` 按 §2.0 (b) 运行时现取）。
3. **新增 §2.24（十一项）**：较 §2.22 的十项多出一项——把 §2.21 的七处保全 hold 拆成
   第 7（A 组）与第 8（B 组）两项，并新设第 9 项**并集等式**，同时按复核轮 14 收工补记
   写明**该等式只证多重集、不证分组**。第 5 项的归档由 7 处增至 **8** 处（B4 的
   `5ed64cf5…7ebf`），并保留「归档 8 < 有效 run 9，差额恒为 B3」的写死注解。
4. **§2.23 转历史**（已于 2026-08-21 执行，复核轮 15/16 均已覆盖）。
5. **自查补标 §2.22（轮换时漏标，本轮就地修）**：B4 的 Play 前核对节此前仍挂着
   revision 25 的抬头与一条**已消费的执行前置**（「不得在复核轮 13 结论之前执行」），
   照字面读会把 B4 那次的放行条件当成现行条款——**正是 F8/F9/F10「轮换只改声明清单、
   活跃绑定留在上一轮」那一族**。本轮标为「**已执行**，2026-08-20，156/156」，并把该
   前置降格为具名历史条款、写明不得再照字面执行。**登记这一点**：轮换的完整性检查
   必须包含「上一轮的待执行节是否已改口径」，只改五处 ID 不算轮换完。
6. 处置 `RUNBOOK_REVISION_28_ARM_B_FINAL_ROTATION_UNDER_BATCH_GO_
   NO_GATE_RELAXATION_NO_FROZEN_VALUE_CHANGE_REVIEW_DEBT_REGISTERED`。

#### D. 放行前置的完整对账（本轮逐条核对，不靠记忆）

| 前置 | 状态 |
|---|---|
| §2.0 (a) 用户 GO | **满足**——2026-08-14 批量 GO 逐 trial 枚举 B2–B5 各一次 Play，**无需新 GO**；该条已入账并提交 |
| 用户 2026-08-20 加的「先复核再放行 B5」 | **满足**——已落账（转述条目 + 用户逐字确认「就按这个意思做」），且轮 15 → 72 返工 → 轮 16 `PASS_WITH_NOTES` 走完 |
| 轮 72 自设的「F14 闭合后才放行」 | **满足**——轮 16 关闭 F14 |
| §2.24 十一项 | **待 Implementation 执行**（本角色已独立复算 63/63） |
| §2.0 (b) | **待 Implementation** 在最终干净 HEAD 上报告，`<BASE>` 运行时现取 = `02c7c88` |
| §2.0 (c) / (d) | (c) 归本角色，在 (b) 之后、用户进 Play 之前写；(d) 要求工作树逐字只有 `docs/unity-test-log.md` |

#### E. 未释放 / 仍欠

**`--compare` 仍无 GO**：本轮跑完十次齐备，但它需要**单独授权**，不在批量 GO 内——
本角色届时单独请示用户，**不得**因「十次已齐」自行启动。任何调参、任何协议/指标/
阈值/统计量变更同样无 GO。**任何 void 终态立即中止批量授权**（臂 B 无替代 ID）。
revision 28 与本轮归因**未经独立复核**；PLAY_GOVERNING 差异恒为操作单一处。

**预期第五次 `SCENE_DEGENERATE`**——事前登记的具名限制，**不是 void、不是新门**；
效应量口径不变（**只能报下界**），`min_side` 预期第五次 125/125（H2-CEILING 如期）。

### Acceptance round 74 — 2026-08-21（arm B trial 5 归因 = 有效 B5；**臂 B 5/5，十次采集完成** + revision 29）

Decision: **`ACCEPTED — B5_VALID_TRIAL`**（arm B **5/5**）+ 操作单 **revision 29**。
本轮判定动作本身零 Play、零采集 ID、零 `runtime/` 写入。

#### A. 归因：B5 有效（接受角色独立复算，只读）

- **`--verify` 亲自复跑**：退出 **0**，逐字返回 `SCENE_DEGENERATE` / `1.0` /
  `run_id: p1-m3-body-001-arm-b-trial-5` / `verified: true` / 窗口 `1.0`。
- **门 1 交叉验证，按 F14 之后的自律逐行枚举**：`frames.jsonl` 中 frame **28** 的 `update`
  行（第 29 行）为 **`5.7835187911987305`**，与启动前落盘值逐字相等；相邻 29/30/31/32 的
  update 行依次 `5.9804863929748535` / `6.184908866882324` / `6.385033130645752` /
  `6.580019950866699`。**本角色不主张「某编号之后已无该字段」**——保留帧集 `0…28` 由门 2
  的同一次导出承载。**实现角色本轮亦主动避开该类旁证并在 §C.1 写明「不重复 B4 的 F14
  错误」**：轮 72 收窄的自律确实传导到了下一轮，登记备查。
- **四门 + 握手**：门 1 判据成立（两侧余量 `3.783519` / `4.216481`）；门 2 最低保留帧 `0`；
  门 3 用户目检「匹配」；门 4 两条肯定项在、五条否定项全 False（含 revision 27 收编的
  `hold` 命名规约判据）；tracker 自然退出 0、validator 产出确认词、用户报「已退出，
  没有报错」。
- **四种 void 终态逐条对照，无一匹配**：下界 `298.19364929741283 >= 212.97056274847716`
  成立，两条域完整性门零触发；五类失败 reason 经本角色从 `frames.jsonl` 重算**全 0 帧**。
- **身份链**：`run_id` 即 canonical slot；receipt 无 attempt/predecessor 任何键；
  `body_policy = threshold` / `planner = threshold-corridor-v1` / `condition = follow` /
  `init_frame_id = 0`；run 目录 11 份，**十条 `--verify` 全过且前九个 run 一字节未动**。
- → **有效 trial，与 A5 配对，臂 B 5/5。2026-08-14 的批量授权四次 Play 全部履行完毕、
  无一触发中止条款；本批次十次采集全部执行完毕。**

#### B. 五次臂 B 并列（登记，n=5 仍不支持任何主张）

| 量 | B1 | B2 | B3 | B4 | **B5** |
|---|---|---|---|---|---|
| `full_loop_c_geom` | `1.0` | `1.0` | `1.0` | `1.0` | **`1.0`** |
| min_side 满分格点 | 125/125 | 125/125 | 125/125 | 125/125 | **125/125** |
| `body_motion_effort_m` | `88.645` | `75.269` | `91.175` | `88.724` | **`90.186`** |
| `body_path_length_m` | `61.423` | `49.162` | `64.455` | `61.407` | **`62.887`** |
| `planner_switch_count` | `11` | `11` | `11` | `11` | **`11`** |
| `corridor_blocked` 帧 | 324 | 339 | 319 | 324 | **322** |
| `nees_median` | `5.068` | `5.299` | `5.196` | `5.245` | **`4.762`** |
| 停留 / 圈数 | `41.390` / `1.619` | `29.602` / `1.510` | `76.804` / `1.953` | `40.198` / `1.608` | **`18.202` / `1.400`** |

- **两条预登记限制各获第五次确认**；结论口径**不变**：效应量只能报**下界**，
  `1.00 − 0.578` 不是可测效应量；H2 可达上限仍是 `THRESHOLD_ALLOCATION_PARTIAL`。
- **`planner_switch_count` 五次全为 `11`**——五次采集、四种不同的机体位移量，切换次数
  一模一样。**只登记，不作机制主张**（它可能是滞回带与 corridor 几何的联合产物，也可能
  是巧合；n=5 不足以分辨，且 BC-BODY1-15 (d) 禁止据此调任何参数）。
- **n=3 撤下的方向性读法在 n=5 上同样不成立**：B5 阻塞 322（居中）配位移 `90.186`（次高），
  五个点无单调关系。**不重提。**
- **`nees_median` 首次跌破 5（`4.762`）**，仍在臂 B 的 `4.7–5.3` 带内、与臂 A 的
  `832–1017` 差两个数量级——**属既有注册发现 (a) 的第五个数据点，不新增主张**。
- **停留 `18.202 s` 为五轮最短**，BC-BODY1-29 的操作纪律执行到位；**不是门**。

#### C. revision 29

1. **§2.25（新，待执行）**：B5 的 post-run 归档合同，与 §2.9/…/§2.23 同构；钉住值由本角色
   **移动前实测、全 64 位落表**（`frames/` **257** 项 id 段 `[614,741]` 聚合
   `dcabe43b…b814`；truth **742** 行 / **806547** B；metrics **61** 行 / **2057** B；
   三个发布件 **329** / **342** / **458** B）；destination 起草时实测**不存在**。
   移动后**复跑十个 `--verify`**；**§2.21 七处保全 hold 不得触碰**。
2. **落盘地在此改变并逐字写明**：前几轮归档都落在「下一 trial 的证据文件」（§2.19 先例），
   **但本轮没有下一 trial**，故 §2.25 落盘于 B5 自己的 `…-arm-b-trial-5.md` §D。
   **该先例在此自然终止**——写明以免下一个接手的角色照抄一个不存在的目的地。
3. **§2.24 转历史**（已执行，155/155）；**槽位不轮换**，§4 CLI 一行不动。
4. 处置 `RUNBOOK_REVISION_29_B5_ARCHIVE_CONTRACT_ARM_B_COMPLETE_
   NO_GATE_RELAXATION_NO_FROZEN_VALUE_CHANGE_REVIEW_DEBT_REGISTERED`。

#### D. `--compare`：十次齐备**不是**授权（本轮不启动，已请示用户）

2026-08-14 批量 GO 原文**明确排除**：「**不覆盖** `--compare`（需十次齐备并**单独授权**）」。
**十次齐备只是它的必要条件之一达成**。本角色**不得**、也**没有**以「十次已齐」为由启动
或起草比较执行；已就此**单独请示用户**。用户授权后仍需：逐字落账 → 接受角色起草比较
合同（口径、配对、统计量、输出去向、失败分支）→ 才谈执行。**在此之前任何角色不得启动
`--compare`**，revision 29 C 条已写死。

#### E. 本批次现在欠什么（据实清点，不含任何新主张）

- **归档**：§2.25 待执行；执行后归档 **9** 处 vs 有效 run **10** 次，差额恒为 B3（永久）。
- **独立复核**：B5 的执行批次、本轮归因与 revision 29 **均未经任何复核轮覆盖**。
- **`--compare`**：无 GO（见 D）。
- **两条预登记限制**：各五次确认，**结论口径不得改写**。
- **M3′ batch 1 的关闭**不在本轮范围内，需另行判断并经用户授权；本轮**不作任何关闭主张**。

### Acceptance round 75 — 2026-08-21（`--compare` 的放行次序入账；**未授权**）

Decision: **`ACCEPTED — COMPARE_SEQUENCING_RULED_NOT_YET_AUTHORIZED`**。零 Play、零采集
ID、零 `runtime/` 写入、零代码与零操作单改动（revision 29 §C 已写死该约束，无须再改）。

#### A. 提问前先据实说明约束（不诱导选择）

本角色在向用户提问之前，先把 `--compare` **能交与不能交**的说清楚：两条预登记限制均已
**5/5 实测确认**——① `C_geom` 在处理臂饱和（五次全 `1.0`），效应量**只能报下界**，
`1.00 − 0.578` **不是**可测效应量；② H2-CEILING 使 `H2_SUPPORTED` **算术上不可达**，
上限恒为 `THRESHOLD_ALLOCATION_PARTIAL`。**即 `--compare` 交的是一份结论口径已被事前
锁死的配对比较，不因跑了它而变强。** 这不是劝阻，是让用户在知情下决定。

#### B. 用户裁定（逐字入账）

**"归档 + 复核后再授权（推荐）"**。**本条不是授权**，是**放行次序**：
§2.25 归档 → 独立复核（覆盖 B5 执行、接受轮 74、revision 29）→ **复核通过后用户另行
逐字授权** → 接受角色落账并起草比较合同 → 才谈执行。
**在此之前任何角色不得启动 `--compare`。十次齐备不构成授权。**

#### C. 比较合同将要写明的项（本轮**不**起草，只登记范围以免日后临场扩权）

口径与配对（A1↔B1 … A5↔B5 的既有配对绑定）、统计量（H1/H2 的既有预登记形式，**不得
更换**）、输出去向与命名、失败分支与 fail-closed 条件、**以及两条限制在结论文字里的
强制措辞**。**合同不得引入任何新指标、新阈值或新样本域**——那属于协议变更，须另行授权。

#### D. 仍欠

§2.25 待执行；B5 执行批次、接受轮 74、revision 29 与本轮均**未经独立复核**；
`--compare` **无 GO**；**M3′ batch 1 的关闭不在本轮范围内**，需另行判断并经用户授权。

### Acceptance round 76 — 2026-08-21（`--compare` 比较合同草案；**仍未授权，本轮不执行**）

Decision: **`PROPOSED — COMPARE_CONTRACT_DRAFTED_PENDING_USER_AUTHORIZATION`**。
零 Play、零采集 ID、零 `runtime/` 写入、零代码与零操作单改动。**本轮没有运行
`--compare`，也不构成运行它的授权。**

#### A. 次序上的一处调整（收紧，非放宽）

轮 75 把次序写成「授权 → 起草合同 → 执行」。**本轮把起草提前到授权之前**：用户的裁定
原话是「归档 + 复核后再授权」，管的是**归档与复核在授权之前**，合同的位置是本角色当时
的补充。**先起草再授权严格更好**——用户授权的是一份写死的条款，而不是一张空白支票。
**这不放宽任何东西**：没有合同、没有用户逐字授权，`--compare` 仍不得运行。

#### B. 前两步已完成（本角色复算确认）

§2.25 归档执行完毕（本角色实测：归档目录恰 6 项、`frames/` **257** 项聚合
`dcabe43b…b814`、五个单文件行数/字节/SHA 逐项等于钉住表；`runtime/frames/` 恰 0 项；
归档 **9** 处对有效 run **10** 次，差额恒为 B3；§2.21 七处保全 hold 完好）。
**复核轮 17 `PASS_WITH_NOTES` on `2916bc2`，零 finding**，`passed_candidate` 前移。

#### C. 合同条款（草案，逐条可核对）

1. **命令**（十个冻结采集 ID **按 trial 顺序**，`--output` create-once）：

   ```bash
   .venv-yoloe/bin/python tools/analyze_m3_body.py --compare \
     --arm-a p1-m3-body-001-arm-a-trial-1-attempt-4,p1-m3-body-001-arm-a-trial-2-attempt-2,p1-m3-body-001-arm-a-trial-3,p1-m3-body-001-arm-a-trial-4,p1-m3-body-001-arm-a-trial-5 \
     --arm-b p1-m3-body-001-arm-b-trial-1,p1-m3-body-001-arm-b-trial-2,p1-m3-body-001-arm-b-trial-3,p1-m3-body-001-arm-b-trial-4,p1-m3-body-001-arm-b-trial-5 \
     --output runtime/test-results/p1-m3-body-001-compare.json
   ```

   **ID 序列不得改动**：`compare_arms` 用 `expected_acquisition_ids()` 逐字比对，
   顺序错、臂错、重复、其他 attempt 后缀、已消耗的 void ID 一律机械 `raise`。
   A1 用其 attempt-4 替代 ID、A2 用 attempt-2，与冻结表一致。
2. **输出**：`runtime/test-results/p1-m3-body-001-compare.json`，**create-once**
   （工具在 `args.output.exists()` 时抛 `compare_output_create_once`）；起草时实测**不存在**。
   **不得覆盖、不得重跑换名再跑**——重跑属于「重试」，批量 GO 与本合同均未授权。
3. **执行前置**：工作树干净；十个 run 目录各含 `m3_body_analysis.json`；十条 `--verify`
   全部退出 0 且逐字复现；`runtime/frames/` 恰 0 项、六个 shared 文件不存在（现状即如此，
   §2.25 之后）。任一不符即停止回接受角色。
4. **工具实际计算什么（本角色读码确认，不转述）**：H1 段 `h1_arm_a_trials` 逐 trial 报
   `full_loop_c_geom` 与 `disposition`；H2 段对三个分量
   （`area_median_px`、`min_side_ge20_share`、`center_error_px`）各做——按 run 配对、
   在**共同里程格点**上取改善正向差（前两者 `B−A`，中心误差 `A−B`）、取该配对的格点
   中位数，再取五个配对中位数的中位数为 `summary_median_improvement`；分量
   `pass` = `summary > 0` **且**五个配对中位数**全部 > 0**。三分量全过 → `H2_SUPPORTED`；
   部分过 → `THRESHOLD_ALLOCATION_PARTIAL`；全不过 → `THRESHOLD_ALLOCATION_INEFFECTIVE`。
5. **可达上限已由算术锁死（本角色在真实数据上实算）**：`min_side_ge20_share` 分量的
   五个配对格点中位数**全部恰为 `0.0`**（各 125 个共同格点；臂 A 116 个 `1.0` / 9 个 `0.0`，
   臂 B 125 个 `1.0`，差值多数为 0），而 `pass` 要求 **严格 > 0** → **该分量永远不通过**
   → **`H2_SUPPORTED` 算术上不可达**，可达 verdict 只有 `THRESHOLD_ALLOCATION_PARTIAL`
   或 `THRESHOLD_ALLOCATION_INEFFECTIVE`。**这正是 H2-CEILING 预登记的内容，跑与不跑
   都不改变它。**
6. **一处必须随输出一起披露的事实（本角色读码发现）**：compare 输出的 H1 段
   **只含臂 A 的五个 trial**（`h1_trials` 由 `arm_a` 构造）。**臂 B 的五次
   `SCENE_DEGENERATE` 不在该 JSON 里**。因此**任何引用该 JSON 的文字都必须同时陈述
   处理臂饱和**，否则读者只看到臂 A 的 `0.578` 系列而看不到臂 B 撞天花板——
   **单看 JSON 会系统性低估这条限制**。
7. **强制措辞（两条预登记限制，写进任何结论文字）**：效应量**只能**表述为
   「臂 B 达到 100% 几何可见性，**效应量为下界**」，**不得**写成 `1.00 − 0.578`；
   H2 的可达上限是 `THRESHOLD_ALLOCATION_PARTIAL`，`INEFFECTIVE` 与 `PARTIAL` 都是
   **事前已知限制下的结果**，不是事后解释。
8. **失败分支**：任何 `AnalysisError` → 工具**不写任何输出**（写盘在 `compare_arms`
   返回之后）→ 停止、保全现场、回接受角色归因。**不得就地改 ID、改顺序、改输出路径
   后重试。**
9. **不得引入**：任何新指标、新阈值、新样本域、新统计量、新配对方式——那属于协议变更，
   须用户另行授权（轮 75 §C 已写死，本条重申）。**不得据比较结果调任何参数**
   （BC-BODY1-15 (d)）。
10. **执行后**：输出文件与其 SHA-256 由接受角色钉住并记入证据；比较结果的**归因**
    （verdict 的含义与措辞）归接受角色，**独立复核仍欠**。**M3′ batch 1 的关闭不由
    本合同触发**，需另行判断加用户授权。

#### D. 仍欠

**`--compare` 无 GO**——本合同是**草案**，须用户逐字授权后由本角色落账方可执行。
本轮（合同草案本身）未经独立复核。

### Acceptance round 77 — 2026-08-21（`--compare` 获用户授权，交实现角色按合同执行）

Decision: **`ACCEPTED — COMPARE_AUTHORIZED_UNDER_ROUND76_CONTRACT`**。零 Play、零采集 ID、
零 `runtime/` 写入、零代码与零操作单改动；**本轮没有运行 `--compare`**。

#### A. 用户授权（逐字入账 `docs/authorizations.md` 2026-08-21）

**"认可，继续"** —— 在本角色已把轮 76 §C 的十条合同写完、并逐字披露两条输出解读注意事项
（`H2_SUPPORTED` 算术上不可达；compare JSON 的 H1 段只含臂 A）之后给出。

**读法（不替用户扩权）**：**「认可」指认可轮 76 §C 的合同**，故**合同即授权范围**——
合同之外的任何变体（改 ID、改顺序、改输出路径、重跑、换统计量）**都不在本条内**。
授权的是**恰一次**执行。

#### B. 交接与边界

**执行归实现角色**——本角色不写 `runtime/`；`--compare` 写 create-once 输出属证据产出。
执行后由本角色钉住输出 SHA-256、归因 verdict 措辞，**独立复核仍欠**。
失败时（任何 `AnalysisError`）工具**不写任何输出**，实现角色须**停下回本角色归因**，
**不得**改 ID/顺序/路径后重试。

#### C. 结论口径不因授权改变（重申，写进任何引用该输出的文字）

效应量**只能**表述为「臂 B 达到 100% 几何可见性，**效应量为下界**」，**不得**写成
`1.00 − 0.578`；H2 可达上限 `THRESHOLD_ALLOCATION_PARTIAL`，`PARTIAL` 与 `INEFFECTIVE`
**都是事前已知限制下的结果**，不是事后解释；**任何引用 compare JSON 的文字必须同时陈述
处理臂饱和**（该 JSON 的 H1 段只含臂 A 五个 trial）。BC-BODY1-15 (d) 的反调参纪律照旧。

#### D. 仍欠

`--compare` 的执行、其输出的归因与独立复核；**M3′ batch 1 的关闭未被主张**，需另行判断
加用户授权。

### Acceptance round 78 — 2026-08-21（`--compare` 归因：verdict 含义与措辞 + 钉住输出 + 追认落盘地）

Decision: **`ACCEPTED — COMPARE_VERDICT_ATTRIBUTED_THRESHOLD_ALLOCATION_PARTIAL_AT_PRE_REGISTERED_CEILING`**。
零 Play、零采集 ID、零 `runtime/` 写入（本轮只读）、零代码与零操作单改动。

#### A. 钉住输出（合同第 10 条）

| 项 | 值 |
|---|---|
| 路径 | `runtime/test-results/p1-m3-body-001-compare.json`（create-once，恰一个） |
| SHA-256 | **`4bd4a14f2176af3ad51ddecc49922e3dabacd9b467267111c1a6303c6c2a0607`** |
| 大小 | **3413** 字节 / **101** 行 |
| schema | `p1-m3-body-compare/v3` |

**执行后现场本角色实测**：`runtime/frames/` 恰 0 项、九处 post-run 归档、十个正式 run 目录、
§2.21 两目录 hold 仍 256 / 59、compare 输出恰一个；**十条 `--verify` 全部退出 0**。

#### B. 本角色对三个分量的独立复算：**逐位相符**

从十份 `m3_body_analysis.json` 的 `c_quality_series` 按合同第 4 条的口径重算
（配对、共同里程格点、改善正向符号、格点中位数、再取五个配对中位数的中位数）：

| 分量 | 五个配对中位数 | summary | `pass` | 复算 |
|---|---|---|---|---|
| `area_median_px` | `632.438` / `513.920` / `663.311` / `558.666` / `585.461` | **`585.460554129895`** | **True** | 逐位相符 |
| `center_error_px` | `0.531` / `0.780` / `1.112` / `1.564` / `1.171` | **`1.112476348877`** | **True** | 逐位相符 |
| `min_side_ge20_share` | `0.0` / `0.0` / `0.0` / `0.0` / `0.0` | **`0.0`** | **False** | 逐位相符 |

#### C. 归因：verdict 的**含义**

**`THRESHOLD_ALLOCATION_PARTIAL`，且这是本批次的可达上限——不是「部分失败」。**

1. **三分量中两条通过，且都满足预登记的最严条件**：不仅 summary > 0，而且**五个配对中位数
   全部同号为正**（`all_pairs_same_sign = True`）。即臂 B 在**匹配的路线位置**上，目标
   表观面积**一致地更大**、中心误差**一致地更小**，五对无一例外。
2. **第三条分量 `min_side_ge20_share` 不是被数据否掉的，是算术上不可能通过的**：五个配对
   中位数**恰为 `0.0`**，而 `pass` 要求严格 `> 0`。该性质在**任何臂 B 数据存在之前**就已
   由 H2-CEILING 预登记（2026-08-14，B1 之前），本角色在授权前又在真实数据上实算确认。
   **因此 `H2_SUPPORTED` 从一开始就不可达，`PARTIAL` 就是天花板。**
3. **故正确读法是：H2 在本批次达到了它能达到的最高判定。** 把 `PARTIAL` 读成「三缺一、
   差一点就支持」是**错的**——差的那一条**没有可能达成**，与臂 B 的表现无关。

#### D. 归因：verdict 的**措辞**（强制条款，写进任何引用该输出的文字）

1. **必须同时陈述第三分量不可达**。只写「H2 部分支持，一个分量未通过」而不说明该分量
   **算术上不可能通过**，会让读者误以为存在改进空间——**这是本条最容易被违反的一条**。
2. **不得给 `C_geom` 报效应量**：只能写「臂 B 达到 100% 几何可见性，**效应量为下界**」，
   **不得**写成 `1.00 − 0.578`。**H1 与 H2 是两回事**——主指标 `C_geom` 在处理臂饱和
   （五次 `SCENE_DEGENERATE`），而通过的两条分量在**质量序列**（面积、中心误差）上，
   **不是主指标**。**不得把 H2 的通过说成「主指标改善」。**
3. **任何引用该 JSON 的文字必须另行陈述处理臂饱和**——该 JSON 的 `h1_arm_a_trials` 段
   **只含臂 A 五个 trial**（本轮实测确认：五条全是 `WITHIN_RANGE` / `0.578` 系列），
   **臂 B 的五次 `SCENE_DEGENERATE` 不在其中**，单看会系统性低估该限制。
4. **不得作量级主张**：`area_median_px` 的 `585` 与 `center_error_px` 的 `1.11` 相差两个
   数量级，而**预登记规则只检验符号与正性，不检验量级**。**「面积改善 585 px」不是本
   批次许可的结论**——许可的结论是「该分量在五个配对上一致改善」。
5. **不得据以调参**（BC-BODY1-15 (d)），也不得据以主张场景非退化。

#### E. 追认落盘地 + 登记本角色自己的合同缺口

**追认** `docs/evidence/P1-M3-BODY-001-compare.md` 为本次执行的证据落盘地，**理由采纳
实现角色所述**：`--compare` 是**批次级工件**（跨十次采集），不属于任何单个 trial；塞进
`…-arm-b-trial-5.md` 会破坏「按 trial 归档」的检索规律。

**但这处需要追认本身就是本角色的缺口**：轮 76 §C.10 只写「输出文件与其 SHA-256 由接受
角色钉住并记入证据」，**没有具名落盘文件**——**这正是复核轮 13 F13 判为 CLASS_2 的同一
族缺陷**（「§2.21 无具名落盘地」），而我是在 F13 闭合**之后**写的这份合同，**等于把项目
已经付过学费的错误又犯了一次**。实现角色没有沉默地选一个了事，而是把选择与理由写在明面
上交追认——**这是正确做法，本角色照单追认并登记**。
**收窄为自律**：凡由本角色起草的、要产出工件的合同或操作单节，**必须具名落盘文件**；
起草完成前把「落盘地是否具名」当作固定自检项。

#### F. 仍欠

**独立复核**：`--compare` 的执行批次、本轮归因与追认**均未经任何复核轮覆盖**。
**M3′ batch 1 的关闭仍未被主张**，需另行判断加用户授权。`--compare` 的授权是**恰一次**，
**已用尽**——任何重跑须用户另行授权。

### Acceptance round 79 — 2026-08-21（M3′ batch 1 关闭判断**草案**；**关闭未主张，待用户授权**）

Decision: **`PROPOSED — BATCH1_CLOSURE_JUDGEMENT_DRAFTED_PENDING_USER_AUTHORIZATION`**。
零 Play、零采集 ID、零 `runtime/` 写入（本轮全部只读）、零代码与零操作单改动。
**本轮不关闭任何东西**——按 AGENTS.md，里程碑/批次关闭需用户授权，复核轮 18 也写明
「下一步是接受角色的关闭判断草案加用户授权，本角色不代为主张」。

#### A. §5.4 十条验收条件逐条核验（本角色本轮实测，非转述）

| # | 条件 | 状态 | 依据 |
|---|---|---|---|
| 1 | 在线零真值 + 零可见性模型 | ✅ | `test_decision_path_has_no_truth_or_visibility_references`、`test_no_controller_reads_m3_truth` 等源码扫描测试，focused 67/67 在每一轮复核中通过 |
| 2 | 配对成立（只切 planner） | ✅ | **本轮实测：12/12 identity 键跨十次采集恒定**（scenario SHA、condition、track_id、ground_plane_y、init_box、init_frame、margin/reanchor/tracker 五项…），**唯一差异是 `body_policy` = `hold` vs `threshold`**；`--compare` 的 `identity_keys` 门亦机械通过 |
| 3 | 测量窗合规 | ✅ | 可见弧哈希冻结于采集前；按路线里程划窗（`measurement_window_m [0, 62.5]`、`h2_grid_spacing_m 0.5`、125 格点）；十次 `window_frame_count` 均 155 |
| 4 | H1：臂 A `C_geom ∈ [0.5645, 1.0]` | ✅ | 五次实测 `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` / `0.5783206310103214` / `0.5783243208518966`，全 `WITHIN_RANGE` |
| 5 | H2 判定式 | ✅ **执行完毕**（口径见下） | **BC-BODY1-5 已把 §5.4 原文的「置信区间下界优于 0」逐字替换**为「汇总中位数 > 0 且逐 run 全同号」，工具实现与之一致；轮 78 归因 `THRESHOLD_ALLOCATION_PARTIAL` |
| 6 | 代价轴齐备 | ✅ | 两臂 effort / tether 饱和 / 云台饱和 / 切换次数 / 轨迹齐备（数值见 §C 登记） |
| 7 | 估计器一致性 | ✅ | 十次均报 `nees_median` / `nis_median` / `sigma_px_frozen = 2.866112` / `fused_frame_count`；两条外推风险已披露 |
| 8 | 参数未后调 | ✅ **机械证明** | 五个预注册值在冻结 `config/p1-m3-body-001.json`（`margin_trigger_deg 10.0`、`margin_release_deg 20.0`、`v_cmd_mps 4.0`、`altitude_hold_m 25.0`、`tether_corridor_check true`）；**十次 run 内 create-once 的 `body_config.json` 与该 config 逐字节相同（10/10）**——不是声明，是字节证据 |
| 9 | 失败如实 | ✅ **强满足** | `SCENE_DEGENERATE` 连报**五次**，未换指标、未换场景、未换高度重报；`--compare` 的 `PARTIAL` 与不可达分量如实登记 |
| 10 | 措辞收窄 | ✅ **且已强制化** | 轮 78 §D 把五条强制措辞写死；`C_track|geom` 十次均 `1.0`（未达显著性讨论的前提），故**不得**表述为「改善了跟踪」 |

**十条全部满足。** 其中第 5 条的口径经 BC-BODY1-5 正式替换，第 8 条为字节级机械证明。

#### B. 本批次**建立了什么**（口径已被事前锁死，据实收窄）

1. **阈值式机身分配在成像质量上产生了一致改善**：`area_median_px` 与 `center_error_px`
   两个分量**五个配对全部同号为正**（summary `585.460554129895` / `1.112476348877`）。
   **这就是 §5.4 第 10 条许可的主张上限**——「机身分配改善**成像质量**」。
2. **臂 B 达到 100% 几何可见性，效应量为下界**（`C_geom` 五次 `1.0`）。
3. **闭环工程可行性**：十次采集、四门 + 握手全过、零 void 终态、十条 `--verify` 逐字
   复现、在线零真值零可见性模型经源码扫描强制。

#### C. 本批次**没有**建立什么（同等重要，写在明面上）

1. **没有可测的 `C_geom` 效应量**——主指标在处理臂饱和，`1.00 − 0.578` **不是**效应量。
2. **`H2_SUPPORTED` 从未可达**——`min_side_ge20_share` 分量算术上不可能通过（H2-CEILING，
   预登记于任何臂 B 数据之前）。**`PARTIAL` 是天花板，不是「差一点」。**
3. **没有跟踪改善主张**——`C_track|geom` 十次均 `1.0`，无判别力。
4. **没有机制主张**：`planner_switch_count` 五次全为 `11`、`nees_median` 从臂 A 的
   `832–1017` 降到臂 B 的 `4.7–5.3`——**只登记，不解释**；n=5 不足以分辨。
5. **新登记的代价轴观察（本轮实测，只登记）**：云台饱和占比从臂 A 的 `0.8394`（五次
   完全相同）降到臂 B 的 `0.50–0.53`；而**系绳饱和占比从臂 A 的 `0` 升到臂 B 的
   `0.10–0.47``——机身动作缓解了云台饱和，代价是系绳约束开始吃紧。**这是代价轴事实，
   不是主张，不得据以调参**（BC-BODY1-15 (d)）。

#### D. 交给用户的关闭判断（本角色的建议 + 必须由用户裁定的边界）

**本角色的判断：§5.4 十条全部满足，batch 1 的证据链完整、可复算、且已被复核轮 18 全链条
零 finding 覆盖，具备关闭条件。** 但**关闭本身须用户授权**，且授权须写清一件事——

**「关闭 batch 1」≠「关闭 M3′」。** BC-M34-6 明写**批次 2 全额有效、未被本批次以任何
方式预先满足**；批次 1 用的是**零可见性模型**。故用户授权时应逐字区分：
(i) 只关闭 `P1-M3-BODY-001`（batch 1），M3′ 仍开；或 (ii) 连同 M3′ 一并处置——
**后者需要另行判断批次 2 的去留，不在本草案范围内**。

#### E. 关闭**不**解决的事（清点，防止关闭被读成「全清」）

- **B3 的完整 post-run 归档永久缺失**（归档 9 处 vs 有效 run 10 次）——已如实入档，
  关闭不改变它。
- **`--compare` 的授权已用尽**，重跑须另行授权。
- **COORD-007 §4.1/§4.2 仍未实现**（一帧下界缺口敞开）。
- **`P1-EVAL-001` BC-BODY1-17 的 aspect 缺陷**：M0 冻结缺陷，本批次 `C_geom` 族数值
  取自未记录的 aspect，**已披露且无重跑授权**——关闭不追认该缺陷为无害。
- **M1、DETECT 判据 4、SCENE-005/007、VLM 两项**等开放条目与本关闭无关，各自照旧。
- **本轮草案本身未经独立复核。**

### Acceptance round 80 — 2026-08-21（**batch 1 关闭**；用户授权，M3′ 仍开）

Decision: **`CLOSED — BATCH1_THRESHOLD_ALLOCATION_PARTIAL_AT_PRE_REGISTERED_CEILING`**。
零 Play、零采集 ID、零 `runtime/` 写入、零代码与零操作单改动。

#### A. 一句未被当作授权的话（据实写明处置）

用户先说 **"只要能完成追踪任务就可以"**。**本角色没有把它记为关闭授权**——它是**判据**
不是**范围**（本角色问的是「只关 batch 1」还是「连 M3′」）。更要紧的是，本角色实测后发现
**该判据在两种读法下结论相反**，故据实回报再请示：

| 「完成追踪任务」的读法 | 实测 | 含义 |
|---|---|---|
| 测量窗内跟踪不丢 | **两臂十次全部 `C_track|geom = 1.0`** | **零判别力**——臂 A（机身完全不动）已达标，**机身分配并非必需** |
| 整圈保持目标几何可见 | 臂 B `1.0` vs 臂 A `0.578`（整圈约 **42%** 不可见） | 差异真实，**但效应量只报下界**（臂 B 饱和），且这是**几何可见性不是跟踪器性能** |

**若不回报而直接按该句关闭，等于让用户在不知道「第一种读法下本批次证明了机身分配不必要」
的情况下拍板。** 用户在知悉两点后选择 **"只关 batch 1，M3′ 仍开（推荐）"**。

#### B. 关闭成立的依据

三门齐备：**实现者证据**（十次采集、四门 + 握手、绑定分析、九处归档）、**独立复核**
（复核轮 18 `PASS_WITH_NOTES` on `6bb2b3e`，**零 finding**；轮 6–18 共十三轮）、
**用户 Unity 验证**（十次 Play，门 3 目检与 Console 反馈逐次代录）。
**§5.4 十条验收条件经轮 79 逐条实测全部满足**，其中条件 8 为字节级机械证明。

#### C. 结论口径随关闭一并冻结（对投稿同样有约束力）

主张上限 **「阈值式机身分配改善成像质量」**；`C_geom` 效应量**只报下界**，不得写
`1.00 − 0.578`；`H2_SUPPORTED` **算术上不可达**，`PARTIAL` 是天花板不是差一点；
通过的两分量在**质量序列**非主指标；`C_track|geom` 十次均 `1.0`，**不得**表述为
「改善了跟踪」；**不得作量级主张**；引用 compare 输出必**另陈臂 B 饱和**。

#### D. 关闭**不**包含什么

**M3′ 仍开**——BC-M34-6 明写批次 2 全额有效、未被本批次以任何方式预先满足，batch 1 用的是
**零可见性模型**；**批次 2 的去留未定、未授权**。**关闭不解决也不追认**：B3 完整归档永久
缺失（9 对 10）、`--compare` 一次性授权已用尽、COORD-007 §4.1/§4.2、`P1-EVAL-001` 已披露的
M0 冻结 aspect 缺陷。

#### E. 若要回答「更难的场景里还成立吗」

**本批次答不了**——臂 B 撞天花板正说明本场景对处理臂太容易。那属于困难路线
（`P1-SCENE-005`/`P1-SCENE-007`）或 M4′ 丢失恢复，两条线均**暂停且未授权**。
**本轮不对它们作任何主张或调度。**

