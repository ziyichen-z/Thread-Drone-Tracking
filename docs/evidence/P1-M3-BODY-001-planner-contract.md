# P1-M3-BODY-001 — 规划器接口契约 v1（BC-M34-7 独立停点）

Work ID: `P1-M3-BODY-001`
Batch: 1a-α（BC-BODY1-3 的 BC-M34-7 规划器接口独立停点批次）
Contract version: `body-planner-contract/v1`
Executable half: [controller/body_planner.py](../../controller/body_planner.py)
Config: [config/p1-m3-body-001.json](../../config/p1-m3-body-001.json)

BC-M34-7 要求在 M3′ 策略实现和任何 M4′ 依赖实现之前先冻结版本化命令
契约。本文件是该契约的散文半边；可执行半边是 `controller/body_planner.py`
的类型与抽象。**本批次零策略代码**：阈值策略、走廊查询、估计器和
`track_loop` 逐帧接入都属批次 1a-β，各自另有停点与独立复核。

契约版本号在任何字段、单位、模式或时序规则变化时递增。v1 **不含**
waypoint 模式，延后规则见 §4。

---

## 1. BC-M34-7 八项逐条冻结

对映提案 §5.3。左列是 BC-M34-7 原文要求的停点项，右列是 v1 的冻结内容。

| BC-M34-7 停点项 | v1 冻结内容 |
|---|---|
| command / sequence ID | 复用既有 `controller/protocol.py` 的 `packet()`：`command_id = time.time_ns()`，单调递增。接收器按 `command_id` 等值去重（`BodyCommandReceiver.cs:77`）。规划器不生成 ID——它返回 `BodyCommand`，发布由 `body_entry.py` 完成 |
| 坐标系与单位 | 世界系、米、米/秒、秒。`velocity_world_mps` 三分量；批次 1 内 `y` 恒 `0.0`（仅水平运动，提案 §3.5），该零值写在 `config/p1-m3-body-001.json` 的 `command.velocity_y_mps` |
| 模式 | 恰好两种：`hold`、`velocity_world`。二者 `body_entry.py` 已实现，**运行时协议零字节改动**。`waypoint` 见 §4 |
| issue / valid-until | `issued_unix_s`（`packet()` 写入）+ `expires_after_s = 2 / capture_hz = 0.4 s`，冻结在 config `command.expires_after_s`。过期由接收器回落 `Hold()`（`BodyCommandReceiver.cs:99-103`） |
| 速度/加速度/系留约束处置 | 速度：`v_cmd_mps = 4.0` 与 plant 双重钳位；加速度：plant `MoveTowards(maximum_acceleration_mps2)`；系留：plant 球约束（垂直钳 `[8,32]`、水平钳 `sqrt(L²−v²)`）+ 规划器侧走廊检查（§3）。**规划器不得假设自己的钳位生效**——plant 的钳位是权威 |
| ACK / 拒绝 | 本批次**无 ACK 通道**（既有 body 通道即无）。规划器决策记入 run log，接收器实际生效值记入帧元数据，离线按 `frame_id` 比对。v1 不新增回传通道 |
| stale / 重复 / 乱序 | 重复：`command_id` 等值去重；stale：`expires_after_s` 过期检查；乱序：单发布者 + 单调 ID，结构上不可能。三条都由既有接收器承担，规划器不重复实现 |
| fail-safe | 三条硬性，属契约而非某个策略：(a) `decide` 在 **BC-BODY1-19 (a)** 的精确定义下纯：无文件/网络 I/O、无墙钟读取、无真值/可见性先验访问、无外部副作用；该条**不**禁止 §3.5 已冻结的迟滞记忆——策略是「**有序输入历史 + 固定初态**」的确定性函数（`arguments alone` 的旧表述作废），按序从首帧重放经新实例确定性复现；(b) `platform is None` 或限位裕度不可构造 ⇒ **必须**返回 `hold`；(c) **不得存在替代决策所有者或旁路**（BC-BODY1-19 (b) 的精确定义） |

### 1.1 fail-safe (c) 的实现后果

`controller/body_planner.py` 因此**不导出任何写入器**，规划器自身零 I/O。
实际写入只准发生在 `controller/body_entry.py` 的两处：既有的
`initialize()` 一次性 hold，以及 `TrackLoop._body_step` 把 planner 返回值
（或其 fail-closed fallback hold）映射为数据包的**唯一映射点**
（BC-BODY1-19 (b)）。任何其他发布调用均为违约。

BC-BODY1-8 另要求：接收器的过期回落与规划器的 `hold` 是**两道互不依赖的
保险**。实现不得让其中一道以另一道存在为前提——即规划器不得因为"反正
接收器会过期回落"而省略 `hold`，接收器也不得因为"反正规划器会发 hold"
而放松过期检查。同一原则适用于 BC-BODY1-20：写入失败时的即时 fallback
`hold` 是本侧的 fail-closed 义务，不得以接收器的 0.4 s 过期回落代替。

---

## 2. 触发量语义（BC-M34-3 / BC-BODY1-6）

触发量与方向**只由已发布的 v3 帧字段 `camera_forward_world` 决定性导出**，
零估计器、零真值：

```
theta_applied = degrees(acos(clamp(-forward.y, -1, 1)))
margin        = maximum_off_nadir_deg - theta_applied
bearing       = degrees(atan2(forward.x, forward.z))
```

`maximum_off_nadir_deg` **读自冻结 scenario**（`gimbal.maximum_off_nadir_deg
= 45.0`），本 work ID 的 config 不复制该常量，只记录其来源路径。

**0.1° 死区（BC-BODY1-6 精度条款）**：`TetheredGimbal.cs:37-38` 在 45° 钳
位 applied 角，但 `Saturated` 旗标要到 `45 + 0.1` 才置位。因此
`margin = 0` 与 `gimbal_saturated` **不严格等价**。策略只准读 margin，
**不得读旗标**；证据文本不得写「当且仅当」。契约把这条写进
`PlatformState.limit_margin_deg` 的 docstring，使其随代码走。

`PlatformState` 只承载帧包已发布量。估计器输出与真值都不得进入该类型；
BC-BODY1-8 的「在线路径零真值引用」是机械复核项。

---

## 3. 走廊工件的唯一用途（BC-BODY1-4）

| 项 | 冻结内容 |
|---|---|
| 工件 | `config/p1-m3-body-001-corridor-prisms.json`，schema `p1-m3-body-001-corridor-prisms/v1` |
| 内容 | 与 `config/road_data.json` `obstacle_footprints` 类型匹配的场景障碍实例的**世界系 AABB 棱柱集** |
| 基准 | `config/scenario.default.json` 的道路审计口径（见 §3.1 的计数勘误） |
| 构建 | 由 1a-α 工具**离线**构建：Editor 侧一次遍历 → `docs/evidence/P1-M3-BODY-001-scene-geometry.json` → `tools/build_m3_corridor.py` |
| 冻结 | SHA-256 记入 `config/p1-m3-body-001.json` 的 `corridor.artifact_sha256` |
| 运行时 | **只读该冻结工件**；唯一允许的查询是「锚点→候选机体位置线段 × 棱柱相交」+ 提案 §3.5 的缩短/hold 规则 |
| 禁止 | 批次 1 内不得被任何可见性/遮挡**预测**、估计器或**测量窗**逻辑读取 |

因此工具 2（`tools/check_scene_body_margin.py`）**不读**走廊工件——它要
算的正是遮挡与测量窗——而是直接读场景几何证据工件。二者同源同一次遍历，
但身份分离，使「走廊工件只有一个用途」可被机械核对。

本条**不预判** OQ-1/BC-M34-6：批次 2 的可见性先验物料来源仍全额待裁，
未裁定不得写其实现代码。

### 3.1 计数勘误：BC-BODY1-4 的「782 实例集」在本载体上是 779

BC-BODY1-4 把工件基准写为「道路审计口径的 **782** 实例集」。实测：

| 口径 | 计数 |
|---|---|
| `runtime/road_scene_audit.json`（`scenario_id: p1-scene-004`）`audited_obstacle_count` | 782 |
| 未施加 `scene_adjustments` 的原始场景（构思角色预扫口径） | 782 |
| **`config/scenario.default.json` 自身的道路审计（本批次载体）** | **779** |

`scenario.default.json` 把 3 辆车移出路线、删除另外 3 辆。用 782 那一版
就等于冻结一份「仿真永远不会运行的场景」的走廊工件，而这三辆被删/被移的
车恰是环线上最重的遮挡体之一（见 `P1-M3-BODY-001-margin.md` §3）。

实现角色**不自行重新解释** binding clarification：工件按实测的 779 构建，
基准由 Editor 同一次遍历跑出的 `RoadSceneAuditor.Audit` **自证**（
`road_audit_obstacle_count`），而不是对硬编码字面量断言；`782` 与冲突标志
一并写进工件字段 `bc_body1_4_quoted_instance_count` /
`bc_body1_4_count_conflict`，交接受角色裁定。

---

## 4. waypoint 模式：显式版本化延后声明

**航点能力仍属 M3′。** 设计 §4.3 明写「M3′ 只提供等待位/航点能力；L4
状态与转移仍由 M4′ 实现」，BC-M34-1 同样把「提供 L4 可消费的
waypoint/HOLD 能力」划在 M3′ 内。

v1 **不实现** `waypoint` 模式，理由是范围而非能力：批次 1 的阈值式分配
只需要 `velocity_world` 与 `hold`，而航点模式会引入 v1 无从冻结的语义
（到达判据、航点序列所有权、抢占规则、到达后的保持行为）。

冻结的延后条款：

1. `waypoint` **最迟在批次 2 以 contract v2 落地**；
2. contract v2 属**控制协议变更**，按 workflow §4.3.1 **单独形成停点**并
   经独立复核，不并入任何策略批次；
3. v2 之前，任何 M4′ 实现**不得**假设 waypoint 可用；`CONTRACT_VERSION`
   是该假设的机械检查点；
4. v1 的两个模式在 v2 中语义不变——v2 只增不改，否则版本号跳到 v3。

---

## 5. M4′ 三用例需求预审（BC-BODY1-3）

BC-M34-7 的目的是让 M4′ 能消费 M3′ 冻结的接口而不必反向绕过停点。以下
逐用例走查 v1 是否够用，**不实现任何 M4′ 状态机**（BC-M34-2）。

### 5.1 L2a 几何搜索（预测轨迹扫描 → 扇形/螺旋扩展）

| 需求 | v1 能否承担 | 结论 |
|---|---|---|
| 沿扫描图案移动机身 | `velocity_world` 逐帧重发即可走出任意曲线（0.4 s 过期，5 Hz 重发） | ✅ 够用 |
| 云台扫描视角 | 走 `gimbal_command.json`，与 body 通道正交 | ✅ 不涉及本契约 |
| 扫描期间保持系留合法 | plant 球约束 + 走廊检查 | ✅ 够用 |
| 扫描图案的"到达下一站位"判据 | v1 无 waypoint，需 M4′ 自行按位置误差闭环 | ⚠️ 可行但笨拙；**v2 waypoint 的首要动机** |

### 5.2 L2b 路网 belief 搜索（按后验概率排序的视角序列）

| 需求 | v1 能否承担 | 结论 |
|---|---|---|
| 逐个前往排序后的观测位 | 同 5.1：速度指令可达，但"序列"要 M4′ 自己维护 | ⚠️ 同上，v2 收口 |
| 观测位的 belief 来源 | `WorldEstimate` 已冻结形状；belief/路网物料来源归 BC-M34-6，**本批次不裁定** | ✅ 形状够用；来源另门 |
| 与 VLM 的信息公平 | 二者必须消费同版本同 hash 的 `WorldModelHandle`（BC-M34-2）。v1 不引入任何 handle，**不制造信息不对称** | ✅ 无预判 |

### 5.3 L4 哨兵等待位

| 需求 | v1 能否承担 | 结论 |
|---|---|---|
| 移动到等待位并停住 | `velocity_world` 到位后转 `hold` | ✅ 够用 |
| 长时间保持等待位 | `hold` + 0.4 s 过期 ⇒ 需 5 Hz 续发；停发即接收器回落 `Hold()`，行为一致 | ✅ 够用，且失效方向安全 |
| "等待位"作为一个可声明的目标 | v1 只有速度语义，等待位是 M4′ 的内部概念 | ⚠️ v2 waypoint 的第二动机 |

**预审结论**：v1 对三个用例都**功能上够用**，无一需要反向修改 M3′ 已冻结
语义；三处 ⚠️ 全部指向同一件事——缺 waypoint 模式，而它已按 §4 显式版本化
延后到 contract v2。M4′ 不因本契约被阻塞，也不获得任何未裁定的能力。

---

## 6. config schema（`p1-m3-body-001/v1`）

| 节 | 键 | 冻结值 | 来源 |
|---|---|---|---|
| `policy` | `margin_trigger_deg` | `10.0` | 提案 §3.5 预注册 |
| `policy` | `margin_release_deg` | `20.0` | 提案 §3.5 预注册 |
| `policy` | `v_cmd_mps` | `4.0` | 提案 §3.5 预注册 |
| `policy` | `altitude_hold_m` | `25.0` | 提案 §3.5 预注册 |
| `policy` | `tether_corridor_check` | `true` | 提案 §3.5 预注册 |
| `policy` | `maximum_off_nadir_deg_source` | scenario 路径 | BC-BODY1-6：常量读自 scenario，不复制 |
| `command` | `contract_version` | `body-planner-contract/v1` | 本文件 |
| `command` | `expires_after_s` | `0.4` | BC-BODY1-8：`2 / capture_hz` |
| `corridor` | `artifact_sha256` | 见 config | BC-BODY1-4 |
| `calibration` | `sigma_px` | `2.866112` | 工具 3 实测（保守初值） |
| `measurement_window` | `visible_arc_sha256` | 见 config | BC-BODY1-2 冻结可见弧 |
| `estimator` | 四个先验值 | 见 config | BC-BODY1-18（见下） |

**五个预注册值在工具产出后不得再调**（BC-BODY1-6）。本批次先于工具运行
即冻结，属接受侧明许的"更早冻结"（提案 §3.5 末：更严、无反选风险）；
工具输出与预注册值冲突时唯一合法动作是回接受角色。

`estimator` 节的历史与现状：1a-α 时该节**故意为空**——`q_accel_mps2`
在已接受提案中没有预注册值，实现角色不发明数值，只把义务登记在 config
里。1a-β 填入四值并在 Acceptance round 5 被裁定为**措辞越界**
（`v·turnRate` 不是平移物理上界，`turnRate` 只旋转车身朝向），由
**BC-BODY1-18** 收束：四值（`q_accel_mps2=8.377580`、`sigma_att_deg=1.0`、
`sigma_y_m=0.05`、`initial_velocity_sigma_mps=2.0`）仅冻结为**批次 1 的
事前、未标定启发式先验**——不是实测标定，也不是物理上界；在任何 1c
数据前冻结，看到数据后不得改，显著不一致只准如实报告并回接受角色。
批次 1 的任何决策仍不得消费估计器均值或协方差；1c 的 NEES/NIS 只称
**未标定先验下的一致性诊断**，不得称估计器已校准或已验证。

---

## 7. 本契约不做的事

- 不实现任何策略（阈值、词典序、hold 实现）——批次 1a-β 与批次 2。
- 不实现估计器，不引入 `WorldModelHandle` 或任何可见性先验（BC-M34-6 全额
  待裁）。
- 不改运行时协议字节、不改帧/观测契约、不改主指标定义。
- 不新增 ACK 通道，不新增 waypoint 模式。
- 不消耗 Play / scenario / session / run ID / 配额 / API。
