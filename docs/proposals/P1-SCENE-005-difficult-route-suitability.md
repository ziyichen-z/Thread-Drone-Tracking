# P1-SCENE-005 — 困难路线适配性核查：先离线评估既有 SCENE-002 路线，仅在证明无余量时才定向改场景

Status: REVISION_REQUESTED
Author/role: 构思角色（ideation，历史名 Claude Fable）
Created: 2026-07-31
Last updated: 2026-08-06
Revision: 3（回应 Acceptance round 3 的 5 条必修项；逐条回应见 §17。
round 1/2 的回应保留在 §13/§15，不重写）

章程来源：`P1-M3M4-SCOPE-001` 已 `ACCEPTED_WITH_BINDING_CLARIFICATIONS`，
其 BC-M34-4 要求本 work item 先评估既有 SCENE-002 困难路线并证明三件事，
BC-M34-5 明确本 ID 需独立提案与独立裁定，BC-M34-9 把本门排在
「M2 关闭 → SCENE-005 → 规划器接口停点 → M3′ 其余实现 → M4′」之间。

**兼容性基线：v0.3.16（2026-08-05）。** v0.3.12–v0.3.16 的全部版本条目
都是 `P1-SCENE-006` 与 M2 关闭的处分记录，写在设计文档头部 blockquote；
本提案映射的正文 §4.1 / §4.3 / §6 / §7 / §10 / §11 自 v0.3.11 起**逐字
未变**。

**授权状态（逐字核对 `docs/authorizations.md`）**：2026-07-31 的结构化
选项 A 是本 ID 的立项方向确认；2026-08-05 "开始吧，接受"是 round 2 三条
退修方向的**方向确认 + 起草授权**。两条都**不**授权实现、Edit Mode/Play、
ID 消耗、移动锚点、全场扫描、写入新 scenario 字节、Stage 2 或 M1 关闭；
本稿的 `A0`、primary 阈值取值与锚点重定位三项**仍各自待用户明确授权**，
文中一律按"待授权、非既有基线"标注。

---

## 0. 修订索引

### Round 3 必修项 → 本稿位置（本轮）

| round 3 必修项 | 本稿落点 | 实质变化 |
|---|---|---|
| 1 恢复既有锚点安全包络、冻结 exact allowlist 与豁免边界 | §2 S1a、§2 S1b、§2 S1c；`P1-SCENE-007` §2.2/§2.3 | 三个实体全部改用 SCENE-003/004 已接受合同的有效半径：锚点盘 `1.5 m`、缆绳 `1.0 m`（+ `δ/2` ⇒ `1.125 m`）、机体球保持加严的 `2.235 m`；闭集相切计违规；豁免只给具名实测支撑实例 |
| 2 `A0` 改成"未知历史 aspect"下的完整影响审计 | §9.2 `A0.3`、§8 | 先机械枚举全部消费方（41 份文档 + 17 个归档 run 目录），再逐条给可复放性/敏感性范围/四值分类；诊断 Play 只验机制、不入证据链、不得替代历史值；给出可证明的结构性结论（天底敏感、跟随不敏感） |
| 3 冻结 Stage A 前后工件的消费边界 | §2 分阶段总览、§2 S0、§6 条 2/3 | 旧锚点上的 S0/D3/S1c 只作诊断与"处分 2 可达"的构造证明；SCENE-007 写入最终配置后 Stage B 必须对新哈希完整重跑 D1–D4/S1c/D3，不得复用；`Δy` 容差改为数值式 `\|Δy − 0.2\| ≤ 0.05 m` |
| 4 补齐 SCENE-007 的双停点顺序 | §2 分阶段总览、§9.3 | 引用 SCENE-007 §2.7：工具/候选工件为停点 1、用户 GO 后写入的 exact 配置为停点 2，两轮独立 Review；Stage B 只在停点 2 通过后开始 |
| 5 清除合同歧义与陈旧自述 | §5、§10 | 撤回"`implementation-status.md` 仍把随机路线归 M1"的陈旧报告（接受角色已按 SCENE-002 更正为 M5）；SCENE-007 的开放口径在该文档 §2.2/§10 一并冻结 |

**另一处用户 2026-08-06 选定的方向 A（round 3 未指出的同类收缩）**：
缆绳净空半径。revision 2 沿用 `Scene006PathCertificate` 的
`0.25 + 0.125 = 0.375 m`，而已接受合同的缆绳柱有效半径是
`corridor_nominal 0.5 + clearance_margin 0.5 = 1.0 m`——收缩 `0.625 m`，
比锚点盘那处更大。本稿按方向 A 恢复为 `1.0 + δ/2 = 1.125 m`（§2 S1a）。
该方向是**收紧**（只会多拒站点、不会多放行）。

### Round 2 必修项 → 位置（上一轮，保留）

| round 2 必修项 | 本稿落点 | 实质变化 |
|---|---|---|
| 1 修正锚点冲突与路径证书的判定顺序 | §2 S1c、§2 S4、§6 条 5 | 锚点合法性升为**预检门**，在任何 `W` 构造与全场扫描**之前** fail closed；处分表重排为 0–7；D3 fixture 改为**不依赖 S1 合法性**的确定性站点；每个分支加构造性测试 |
| 2 改正 541 状态 / 540 覆盖样本口径 | §2 S2a、§2 S2c、§2 S2d | trace 保留 `s_0…s_540`，但覆盖率/权重分母/阈值秒数/可见性场一律用 `s_1…s_540`（540 样本）；主扫描射线数改为 `1,040 × 540 × 15 = 8,424,000`；`s_0` 若进 D3 则单列为非指标样本 |
| 3 拆 `A0`（相机投影语义）与 `A1`（谓词抽取）两个强停点 | §2 S0-D4、§8、§9.2 | `A0` 先做零 ID 诊断测量、再改运行时 `aspect` 绑定、再做有界回溯审计，**须用户明确授权**；`A1` 才是纯抽取 no-op；两者不得合批称 no-op；新增 SCENE-006 离线 rig 已显式设 `aspect` 而运行时未设的 parity 缺口记录 |
| 4 主阈值必须在看见场结果前冻结 | §2 S3 | `0.05` 三阈值升为 **primary contract（待用户授权）**，须在主扫描前冻结；`4×4×4` 降为 secondary sensitivity；补 `Δ = G − L ≤ G` 的蕴含关系与 `γ_min` 的归因/审计定位 |
| 5 最小锚点重定位先于全场扫描 | §2 Stage A/B/C、§1.4、§9.3 | Stage 2a 提为**独立先行 work item `P1-SCENE-007`**（提案随本批次提交）；选点只用最小位移 + 实测支撑 + 净空的确定性排序，**不读任何可见性结果**；旧 M2 曲线降为旧几何历史证据 |
| 6 补全锚点端 trim 的高度证明 | §2 S1b | `d_trim` 改为闭式导出 `d_trim ≥ r_tether · L / h_min`，并把实测支撑面与配置锚点的高差 `Δy` 纳入不等式；`Δy < 0` 或超容差即 fail closed 重新推导 |

### Round 1 必修项 → 位置（上一轮，保留）

见 §13。round 1 的 8 条已在 revision 1 解决，本轮不重开：v0.3.16 基线与
BC-M34-4 三肢映射（§1.1）、哈希绑定 trace（§2 S2a）、逐点零容差保真门
（§2 S0-D3）、连续路径证书（§2 S1b）、单一冻结格与量词纪律（§2 S2d）、
(b3) 撤回、可证明上界 `U_occ`（§7）、工件/责任/续跑合同（§4）。

---

## 1. Problem and research value

### 1.1 章程义务与 BC-M34-4 三肢的逐条映射

BC-M34-4 原文要求在任何三策略 Pareto 采集之前证明：(a) 基线 `C_geom`
有实义缺口；(b) 系留/高度/净空约束内存在至少一个合法机身动作，使冻结
目标 belief 集合中非零测度部分的期望可见性改变；(c) 支撑/净空审计通过。

| 章程肢 | 本提案的对应产出 | 判定量 | 失败去向 |
|---|---|---|---|
| (c) **先判** | 地面审计复现 + **锚点合法性预检** + 空中工作空间审计 | 锚点膨胀盘 ∩ 走廊棱柱 = ∅ 且实测支撑通过；再判站点净空与路径证书 | §2 S4 处分 1/2/4 |
| (a) | `U_occ(p_hover)`（§7 定义，**可证明**的云台-only 上界）与参考策略值 `C*(p_hover)` | `U_occ(p_hover) ≤ 1 − δ_gap` ⇒ 缺口对**任何指向策略**成立 | §2 S4 处分 5 |
| (b) | 冻结格上的**联合见证集** `W`（§2 S3） | `W ≠ ∅` | §2 S4 处分 6 |

**本轮把 (c) 提到最前（round 2 必修项 1）。** 上一稿把锚点冲突排在
`W = ∅` 之后，而锚点恰在走廊内 ⇒ 每条"锚点→机体"缆绳胶囊从起点就侵入
走廊 ⇒ 所有站点的路径证书失败 ⇒ `W` 恒空 ⇒ 决策表在 `W = ∅` 一行就
命中，把一个**已确定的锚点缺陷**误归因成"冻结格上没有余量"。这是
revision 1 的实质缺陷，本轮修正。

### 1.2 现有两个 `C_geom` 都不是几何天花板

| 来源 | 数值 | 相机指向 | 为什么不能回答适配性 |
|---|---|---|---|
| `UT-P1-SCENE-002-001` attempt 3 | `C_geom=0.21956272423267365`（815 帧 / 162.98348999023438 s） | `LookNadir()`，`gimbal_saturated=false` | 纯**指向**受限，不含任何遮挡信息 |
| RATE-002 三次 r20-follow | `0.612626433` / `0.610448897` / `0.610444605`，`gimbal_saturated=true` | 云台跟随**追踪器**输出 | 与 NanoTrack 漂移**混杂**：追踪器丢了目标，云台就指错，`C_geom` 随之下降 |

第一行是纯几何但把相机钉死在天底：对冻结配置直接算，25.0 m 悬停高度、
60° 垂直 FOV、640×480 的天底足迹为 38.490018 m × 28.867514 m（半宽
19.245009 m / 半高 14.433757 m），该矩形覆盖 212.970563 m 环线的
**中心点**弧长比为 `0.196844`。与档案值 `0.219562724` 相差 `0.022719`。
**该比较只是数量级诊断，不是保真证据**（§2 S0 已撤销它的门地位）：
evaluator 的判据是 15 点 `≥0.2`，不是中心点；而且足迹宽度还依赖一个
**运行时从未被钉住**的相机 `aspect`（§2 S0-D4、§8）。

第二行指向了目标，但指向的是**追踪器估计**而非真值，因此它同时度量
了感知失败。用它论证"场景有可见性缺口"，等于把追踪器漂移记成场景难度
——这正是 §4.7 设计审查要抓的指标归因错误。

DR-P1-M2-001 N8 已登记：将来关闭 M1 时不得用 `0.219562724` 论证遮挡。
本提案与该登记一致，并在 §10 只给出建议、不关闭 M1。

### 1.3 由冻结字节直接算出的几何事实（可独立复算）

以下只用 `config/scenario.default.json`
（`sha256=f9c9205249aacf7487579ca42f727c766800cc329d0523ec82a96140564a2ce3`）
与 `config/scenario.scene-validation.json`
（`f6005eb4365c8b598937dcbd422712914f4266b101d9147ff91e429fe246cd54`）。
两者已逐键 diff：仅 `scenario_id` 与 `route_corridor` 的两个诊断开关
不同，**几何字段完全一致**。绑定的 `config/road_data.json` 为
`111e0759d4b52821d08ce4ddd1aae3fc8cc8d24e12e6fa62513403c00b401894`。

1. **环线与悬停点**：路线周长 `212.970563 m`；`anchor_world_m =
   (132.0, 0.2, 117.0)`、`initial_altitude_m = 25.0`，而
   `TetheredScenarioBootstrap.CreateDrone` 写的是
   `Config.Anchor + Vector3.up * initial_altitude_m`，
   `SensorCamera` 是无人机的子物体且 `localPosition = Vector3.zero`
   ⇒ **相机位置 ≡ 机体位置**，云台-only 基线为
   `p_hover = (132.0, 25.2, 117.0)`。
   `TetheredDronePlant` 的高度带是**相对 `Config.Anchor.y` 的**
   `relative.y ∈ [8, 32]`（`Scripts/TetheredDronePlant.cs:43`），
   即世界 `y ∈ [8.2, 32.2]`；`p_hover` 的相对高度 25.0 合法。
2. **`p_hover` 上的指向分布**（对路线折线按 0.05 m 稠密采样、目标中心
   在 `y=0.2`）：off-nadir 最小/中位/最大 =
   `1.145763°` / `61.642041°` / `70.113398°`；水平距离
   `0.500000 … 69.112228 m`；斜距 `25.005000 … 73.494898 m`。
   离轴 `> 45°`（云台饱和）弧长占比 `0.735349`，离轴 `> 75°`
   （中心出视锥）占比 `0.000000`。这三个数与 `P1-M3M4-SCOPE-002`
   已核实的 `0.7353` / `0.0000` / `70.113398°` 一致（§1.6）。
3. **系留工作空间**：相对锚点高度 h 时最大水平半径 `sqrt(35²−h²)`：
   h=8 → `34.073450 m`，h=32 → `14.177447 m`。**机体的水平可达半径
   （最大 34.07 m）小于路线到锚点的最大水平距离（69.112228 m）的一半**
   ——机体永远无法移到远端路段上方，只能改变掠射角。
4. **远端探测通道的既有诊断**：`fy = (480/2)/tan(30°) = 415.692194`，
   车高 1.55 m 在最远斜距 `73.494898 m` 处张 `8.766907 px`。该数只用于
   解释 SCENE-003 的远端 recall 观测，不是本 work item 的门。

> 上述 2/3/4 条都以现锚点 `(132.0, 0.2, 117.0)` 为基准。**Stage A 一旦
> 移动锚点，它们全部作废并须重算**；本节保留它们只是为了说明现字节的
> 状态与 Stage A 的必要性，不得当作新几何的预测。

### 1.4 锚点位于目标车道走廊内部——(c) 的**预检阻断项**，并触发独立先行 work item

`|z_anchor − z_北段路线| = |117.0 − 117.5| = 0.500000 m`，而冻结的路线
走廊半宽是 `target_half_width_m(1.0) + clearance_margin_m(0.5) =
1.500000 m`。**锚点位于目标车道走廊内部 1.000000 m。**

更强的一步（全部由冻结字节与 bootstrap 字面量导出）：

- 目标车体半宽 1.0 m ⇒ 车体沿北段行驶时占据 `z ∈ [116.5, 118.5]`；
- 锚点视觉是 `PrimitiveType.Cylinder`、`localScale = (1.2, 0.2, 1.2)`、
  位置 `(132.0, 0.2, 117.0)` ⇒ 占据 `z ∈ [116.4, 117.6]`、
  `y ∈ [0.0, 0.4]`；
- 目标车体底面在 `y = 0.2`（body cube `localPosition.y = 0.5`、
  `localScale.y = 1`，`TargetVisualFactory.AddTargetVisual`）。

⇒ **目标车每圈都从锚点标记里穿过去**（水平重叠 1.1 m、垂直重叠 0.2 m）。
现有审计不会发现：`RouteCorridorAuditor` / `RoadSceneAuditor` 只审计场景
静态 root，锚点视觉、无人机与目标是 bootstrap 显式排除的 runtime actor；
锚点的 collider 也被 `Destroy` 掉，所以它既不挡射线也不触发净空审计。

这与 `P1-SCENE-001` 因 taxi/street-light 重叠被判 Unity FAIL 是同一类
缺陷。本轮的处置（round 2 必修项 1 + 5）：

1. **判定顺序**：锚点合法性成为 §2 S1c 的**预检门**，在任何工作空间
   扫描、可见性场与 `W` 构造之前判定，命中即 `BLOCKED_ANCHOR_
   CORRIDOR_CONFLICT`（§2 S4 处分 2）。
2. **不在现锚点上烧射线**：既然冲突已由字节确定成立，在现锚点上跑
   八百多万条射线不会产生任何可消费的场景资格工件。因此
   **Stage B 的全场扫描在 Stage A 通过之前不启动**。
3. **独立先行 work item**：最小锚点重定位提为 `P1-SCENE-007`
   （`docs/proposals/P1-SCENE-007-minimal-anchor-relocation.md`，随本
   批次提交），选点只按最小位移 + 实测支撑 + 净空的确定性排序，
   **不读任何可见性结果**，不放宽安全合同。本提案不预取其接受，也不
   自行移动锚点。

### 1.5 研究价值

1. **反退化**：这是唯一能在花掉 M3′ 采集预算之前判定 Pareto 是否塌缩
   的手段。BC-M34-4 预见的失败模式（"遮挡全来自贴路建筑、任何合法机位
   都被挡"）与其反面（"根本没有遮挡"）目前都既没被证实也没被证伪。
2. **产出 §7 已经欠着的 oracle 可见性对照**：§7 明列
   "oracle target state / oracle visibility（真值直通控制器的上界）"
   为关键对照，至今没有任何工件给出这个数。本提案给出**一个真正可证明
   的上界** `U_occ(p_hover)`（§7），并明确其余量都只是可达值而不是上界。
3. **给 M3′ 的超参数冻结提供不看结果的依据**：BC-M34-8 要求 `p_min`、
   预测时域 H、阈值基线参数在任何 Pareto 测量前冻结；BC-M34-3 要求
   阈值基线的触发量是**当前云台限位裕度**。本核查产出全格 off-nadir /
   限位裕度 / 斜距 / 像素尺寸分布，使这些参数可以由场景几何预注册。
4. **补上空中工作空间审计**：SCENE-001/002/003/004 的全部审计都是地面的。
   机体可达域与缆绳段的净空从未被审计；M3′ 的第一条机身指令就会用到它。
5. **顺带暴露一条主指标测量语义缺口**：`A0`（§2 S0-D4、§9.2）。它不是
   本 work item 的目的，但它是本 work item 的前置——离线谓词无法在
   运行时投影语义未受控的前提下声称与主指标同义。

### 1.6 吸收已保留的负结果（SCOPE-002 / SCENE-006），并划清引用边界

**可引用的**（`P1-M3M4-SCOPE-002` 已核实、用户 2026-08-01 明示按负结果
证据保留，`P1-SCENE-006` §6.3 转载）：

- 现冻结路线上机体静止于 `p_hover` 时，目标中心出视锥弧长占比
  `0.0000`，最大离轴 `70.113398°`——**指向通道在该场景上不贡献可见性
  损失**（纯解析、零射线）；
- 云台饱和（离轴 > 45°）弧长占比 `0.7353` 与上一条并存；
- 在冻结光学下"把目标拉远制造难度"与探测可行性不相容。

**对本 work item 的直接后果**：BC-M34-3 冻结的阈值式触发量是"当前云台
限位裕度"。在本场景上，该触发量每圈有 `73.53%` 的时间处于饱和，而对应
的视锥损失是 `0.0000`。因此**阈值式对照会在四分之三的时间里命令机身
移动却换不回任何视锥收益**；它相对云台-only 的任何差异，都只可能来自
遮挡改变。这把本提案的测量目标收窄成一件事：**这条路线上到底有没有可
由机身改变的遮挡结构。**

**不可引用的（硬边界）**：`P1-SCENE-006` 已整体关闭为
`CLOSED_PROTOCOL_PRECONDITION_UNSATISFIED`。该终态**不是**场景资格
结论，也**不是** `P1-SCENE-005` 的 supersession 或资格证据；其
`|D|=52`、`4/52`、`T1P2_PROMPT_LAW_UNSATISFIABLE` 等测量结论一律不得
进入本 work item 的任何判定。本提案只复用 SCENE-006 的**代码构造**
（§9），其依据是 independent Review round 8 对 `d21aafc..d2db9f3` 的
**代码符合性 `PASS`**——代码可复用与结论可引用是两件事。

---

## 2. Proposed behavior

### 分阶段总览（round 2 必修项 5 重排）

| 阶段 | 归属 | 内容 | 前置 |
|---|---|---|---|
| **Stage A** | **`P1-SCENE-007`（独立先行 work item）** | 最小锚点重定位：确定性候选排序、实测支撑、净空与走廊排除证书。**不读任何可见性结果** | 用户明确授权 + SCENE-007 自己的 Acceptance 裁定 |
| **Stage B** | 本 work item | 适配性核查：S0 保真 → S1c 锚点预检 → S1a/S1b 工作空间 → S2 可见性场 → S3 判据 → S4 处分 | Stage A 通过其自身门 |
| **Stage C** | 条件分支 | 处分 5/6 时的定向场景修改（路线段 / 已声明敏感性轴） | Stage B 的对应处分 + 新一轮裁定 |

**Stage A 的两个停点（round 3 必修项 4，细则在 `P1-SCENE-007` §2.7）**：
批次 1（工具 + 候选工件，零配置字节）先形成稳定候选、经 Acceptance
§4.3.1 写入归因与独立 Review；通过后才向用户展示 `a*` 请求 GO；用户 GO
后写入的 exact scenario 配置 + self-diff + 哈希构成批次 2，再经停点与
第二轮独立 Review。**Stage B 只在批次 2 的 Review 通过之后开始**——被
Stage B 消费的正是批次 2 的字节，它不得绕过复核。

**Stage A 前后的工件消费边界（round 3 必修项 3，硬性）**：在**旧锚点**
上产出的 S0（D1–D4）、D3 fixture 与 S1c 结果，**只能**用作两件事——
诊断，以及"当前冻结输入可达处分 2"的构造证明。锚点一动，输入哈希、
`p_hover`、全部站点世界坐标与目标 AABB 的相对几何全变，因此
**Stage B 必须对 SCENE-007 批次 2 的配置及其新哈希完整重跑
S0-D1–D4、S1c 与 D3 fixture，不得复用任何旧锚点的通过结果**。工件必须
分别记录两次运行的输入哈希，复核核对没有跨锚点复用。

**Stage B 的全场扫描（约 8.42×10⁶ 条射线）在 Stage A 通过之前不启动。**
S0 的保真门（D1–D4）与 S1c 的锚点预检可以在现字节上先跑——它们是廉价
的、且 S1c 在现字节上的预期输出正是处分 2，这本身就是必修项 1 要求的
"处分 2 在当前冻结输入上可达"的实证。

### Stage B — 只读离线适配性核查（本提案的主体）

全程 Edit Mode、不进 Play、不建 session/run/profile、不消耗任何
qual/run ID、**不修改任何既有冻结字节**。

> **字面口径澄清**：本 work item **新增**自己的配置与工件字节（新文件名、
> 新 schema id、新 `runtime/` 子目录），但**不覆盖、不改写、不重新哈希**
> 任何既有冻结字节。COORD-005 的人眼保真检查针对**新渲染/采集管线**；
> Stage B 不渲染、不落帧、不产生图像，故不触发该硬门——代替它的是
> §S0-D2 的目标 AABB 身份绑定与 D3 的逐点等价门。**注意**：`A0` 的
> 诊断测量（§9.2）走 COORD-005 的**诊断通道**，是一次 Play 运行，
> 明确标注为诊断、不创建不消耗任何 ID、产物不进证据链。

#### S0 — 冻结输入与谓词保真

- 场景配置取 `config/scenario.default.json` 字节（Stage A 之后改取新
  锚点配置字节）；核查参数写入新的冻结文件
  `config/p1-scene-005-suitability.json`
  （schema `p1-scene-005-suitability-config/v1`）。
- **占位与遮挡体必须与运行时一致**：先跑
  `SceneVehicleAdjustmentApplier.Apply(scene_adjustments)`，再构建
  `EvaluationOcclusionGeometry`，并用
  `TargetVisualFactory.AddTargetVisual`（§3.1 单一生产构造源）取得目标
  可见体，以保证 AABB 与运行时同源（F23 教训的对应处置）。

**保真门（按序判定，全部 fail-closed）**

- **D1 — 输入身份（零容差）**：绑定并记录
  `config/scenario.default.json`、`config/road_data.json`、场景资产文件
  与新配置文件的完整 SHA-256；`EvaluationOcclusionGeometry` 的
  `candidate_renderers` / `mesh_collider_proxies` / `existing_colliders` /
  `failed_proxies` 必须精确等于档案快照 `913 / 913 / 0 / 0`；同时导出
  **代理实例清单**（按 `CoverageEvaluator.StableObjectId` 排序的全路径
  列表 + 其 SHA-256）、`layer`、`used_default_layer_fallback`、
  `excluded_renderers` 与被排除的三个 root 名。`excluded_renderers`
  在离线 harness 中允许与运行时的 `8` 不同，但必须逐条列出并说明每一条
  的归属；**其余四个计数零容差**。
- **D2 — 目标身份（零容差）**：目标可见体必须由
  `TargetVisualFactory` 构造；记录 body/roof 的
  `localPosition/localScale/color` 字面量与合成后的**局部 AABB**
  （`x∈[−1,1]`、`y∈[0,1.55]`、`z∈[−2,2]`，相对目标 root）及其哈希。
  与 `TargetVisualFactory` 的字面量不符即 `PREDICATE_MISMATCH`。
- **D3 — 逐点等价（零容差）**：在冻结 fixture 上逐样本比对离线谓词与
  `CoverageEvaluator` 的真实判定，比对量为 `inFrustumCount`、
  `visibleCount`、`geometricallyVisible` 三者，**零容差、逐点、无聚合**。

  **fixture 不依赖 S1 合法性（round 2 必修项 1）**：上一稿写的"S1 判定
  合法的 8 个站点"在锚点非法时是空集，会让 D3 自我阻塞。本轮改为
  **纯几何的确定性选择**——`p_hover` 加上冻结格 `(h, x, z)` 顺序中每个
  高度层的首个站点（7 层各 1 个），共 **8 个站点**，与 S1a/S1b 的判定
  结果**无关**。规模：`8 × 540 = 4,320` 个指标域 (站点, 状态) 对、
  `64,800` 个采样点；若同时测 `s_0`，另计 `8 × 1 × 15 = 120` 个
  **非指标**采样点并在工件中单列（round 2 必修项 2）。
  任一点不等 ⇒ `PREDICATE_MISMATCH`；在 D3 通过之前，S2 的任何数字都
  不许引用。
- **D4 — 相机投影语义（本轮升级为 `A0` 停点的入口）**：
  `SensorCamera` 的 `aspect` **在运行时从未被显式设置**，而
  `SensorFrameWriter` 在 `Scripts/SensorFrameWriter.cs:173` 就把
  `targetTexture` 清空，`FramePublished?.Invoke` 在 `:206` 才发生，
  evaluator 的 `WorldToViewportPoint` 又在该回调里跑。**因此运行时主
  指标的视锥判据用的是哪个宽高比，当前无任何代码路径钉住。**
  仅把离线相机钉成 `640/480` 只能保证离线自洽，**不能**证明它与运行时
  主指标同义。因此本轮把它拆出去（§9.2 `A0`），D4 在 Stage B 内只承担
  两件事：显式设置并记录 `aspect = 640/480`、`fieldOfView = 60`、
  `nearClipPlane = 0.3`、`farClipPlane = 500` 与 `projectionMatrix` 的
  16 个 float；并在工件中记录 `A0` 的当前状态（未授权 / 已诊断 /
  已修复），Stage B 的结论文字必须随该状态一并出具。
- **D5 — 档案复现（诊断，不设门）**：以天底相机在 `p_hover` 复算
  `C_geom` 并与档案 `0.219562724` 比较，报告实际差值、所用窗口、
  所用 `aspect`。**本项不具备门地位**：它是聚合量，既不能证明逐点谓词
  相同（D3 才能），又携带 D4/`A0` 的未受控 `aspect` 依赖。

#### S1c — 锚点合法性预检（**先于**一切扫描，round 2 必修项 1）

在 S1a/S1b/S2 之前独立判定，命中即 fail closed：

- **走廊排除**：锚点以**已接受合同的有效半径**
  `anchor_nominal_radius_m (1.0) + clearance_margin_m (0.5) = 1.5 m`
  膨胀的盘（闭集，相切计违规）与冻结路线走廊棱柱（半宽 1.5 m、
  `target_bottom_offset_m = 0.0`、`target_height_m = 1.55`、
  `vertical_clearance_margin_m = 0.5`）相交 ⇒
  `BLOCKED_ANCHOR_CORRIDOR_CONFLICT`。
  **round 3 必修项 1**：revision 2 在 `P1-SCENE-007` 里写的
  `0.6 + 0.3 = 0.9 m` 是按视觉体建模的收缩，已撤销；两份文档现在用
  同一份 SCENE-003/004 合同值。
- **实测支撑**：在真实场景中**实测**锚点所在地表的分类与支撑面高度
  `supportY`（SCENE-003 教训：草地瓦片实测 `0.0000013 m` 而假设 `0.2 m`，
  容差 `±0.05` 下 1,257 个候选全灭）。记录
  `Δy = Config.Anchor.y − supportY`，判据为**数值容差**
  `Δy ≥ 0` 且 `|Δy − 0.2| ≤ delta_y_tolerance_m = 0.05 m`；
  不成立 ⇒ `BLOCKED_ANCHOR_SUPPORT`（round 3 必修项 3：不再写
  "超预注册容差"这种无数值的口径）。
- **`p_hover` 自身合法性**：机体球在 `p_hover` 的净空。

**现字节上的预期输出是 `BLOCKED_ANCHOR_CORRIDOR_CONFLICT`**（§1.4 已由
字节确定），这正是必修项 1 要求的"处分 2 在当前冻结输入上可达"的实证；
构造性测试见 §6 条 5。

#### S1a — 站点净空

对 §2 S2d 冻结站点集合的每个节点判定：

- **机体球**：半径 `body_radius = body_nominal_radius +
  clearance_margin + δ/2` 的球与任何场景障碍相交 ⇒
  `ILLEGAL_BODY_CLEARANCE`；
- **缆绳胶囊**：锚点到 `p` 的线段以 `tether_radius =
  tether_nominal_radius + δ/2` 膨胀的胶囊与场景相交 ⇒
  `ILLEGAL_TETHER_CLEARANCE`（落实设计 §4.1 的"简化缆线-障碍约束"）。

`body_nominal_radius` **不得沿用 SCENE-006 的 1.0 m**。由
`TetheredScenarioBootstrap.AddDroneVisual` 的字面量导出：hub 球
`localScale=(1.2,0.45,1.2)` ⇒ 半径 0.6；四条臂
`localPosition = direction*0.8`、`localScale=(0.12,0.1,1.6)` 且
`localRotation = LookRotation(direction)` ⇒ 臂尖在 `0.8+0.8=1.6 m`，
外接半径 `sqrt(1.6² + 0.06²) = 1.601125 m`。因此预注册
`body_nominal_radius_m = 1.61`（≥ 导出值，保守方向），并由一条
EditMode 测试断言"运行时机体可见体的外接半径 ≤ 该值"，字面量一变即失败。
**三个实体的有效半径（round 3 必修项 1 + 方向 A，全部对齐已接受合同）**

| 实体 | 名义半径 | 净空裕度 | 路径离散 `δ/2` | **本 work item 的有效半径** | 与合同的关系 |
|---|---|---|---|---|---|
| 锚点盘（S1c，静态判定） | `1.0` | `0.5` | — | **`1.5 m`** | **= 合同** |
| 机体球（S1a/S1b） | `1.61`（由 `AddDroneVisual` 导出） | `0.5` | `0.125` | **`2.235 m`** | **≥ 合同的 `1.5 m`**（加严，理由见下） |
| 缆绳胶囊（S1a/S1b） | `corridor_nominal 0.5` | `0.5` | `0.125` | **`1.125 m`** | **≥ 合同的 `1.0 m`**（只多出离散裕度） |

`body_nominal_radius` **不沿用合同的 `hover_nominal_radius_m = 1.0`，
而是取导出值 `1.61`**：`TetheredScenarioBootstrap.AddDroneVisual` 的
hub 球 `localScale=(1.2,0.45,1.2)` ⇒ 半径 0.6；四条臂
`localPosition = direction*0.8`、`localScale=(0.12,0.1,1.6)` 且
`localRotation = LookRotation(direction)` ⇒ 臂尖在 `0.8+0.8=1.6 m`，
外接半径 `sqrt(1.6² + 0.06²) = 1.601125 m`。即**合同的悬停球有效半径
`1.5 m` 小于机体自身的外接半径 `1.601125 m`**——它装不下要保护的对象。
本 work item 因为审的是运动中的机体，取加严值 `1.61`（≥ 导出值，保守
方向），并由一条 EditMode 测试断言"运行时机体可见体的外接半径 ≤ 该值"，
字面量一变即失败。**加严不需要授权，收缩才需要**；该合同参数本身是否
应修订，作为一条报告交接受角色（§10），本提案不改。

缆绳半径按用户 2026-08-06 选定的**方向 A** 从 revision 2 的 `0.375 m`
恢复为合同的 `1.0 m` 再加离散裕度 `0.125` ⇒ `1.125 m`。这是**收紧**：
`1.125 > 0.375`，只会多拒站点、不会多放行，因此不构成安全合同变更。
`Scene006PathCertificate.TetherRadiusM = 0.375` 作为已知偏松的历史值，
其归因属接受角色裁量，本提案不预取。

#### S1b — 连续路径证书

任何**可计入见证**的站点 `p` 必须自带一张连续路径证书，构造唯一冻结：

- **路径**：`p_hover → p` 的直线段（唯一，不搜索）。两端点都在系留球
  （凸）与高度带内 ⇒ 整段由凸性也在其中，两条端点事实入工件、不重采样。
- **速度剖面**：rest-to-rest **梯形**剖面，`|v| ≤ maximum_speed_mps
  = 4.0 m/s`、`|a| ≤ maximum_acceleration_mps2 = 4.0 m/s²`（两者取自
  冻结配置 `drone` 段）。解析时长
  `T(len) = 2·sqrt(len/a)`（`len ≤ v²/a = 4 m`）否则 `len/v + v/a`。
  **该时长只进工件，不进任何门**。
- **净空离散**：`N = ceil(len/δ)`、`δ = 0.25 m`、`u_i = i·len/N`
  （含两端点），故路径上任意点距某采样点 ≤ `δ/2 = 0.125 m`；两个膨胀
  半径已含该 `δ/2`，因此离散判定**保守蕴含**连续判定。每个采样点同时
  判机体球与"锚点→该采样点"的缆绳胶囊；闭集相切
  （`distance ≤ radius + 1e-5`）计为违规。
- **锚点端 trim（round 2 必修项 6：改为含高差的闭式导出）**：只有
  **具名的、实测的**支撑实例可以在缆绳胶囊的头段 `[0, d_trim]` 被忽略，
  其余全部（含路面与 allowlist 实例）全段查询、fail closed。

  设支撑面为水平面、锚点在其上方 `Δy = Config.Anchor.y − supportY ≥ 0`
  （由 S1c 实测）。系留段的仰角下界由带下界与系留长度给出：
  `sin θ_min = h_min / L_tether = 8 / 35 = 0.228571`（**精确值**，因为
  最低层机体恰在半径 `L` 球面上时对边为 `h_min`）。膨胀后的胶囊在头段
  之外不触及支撑面的充分条件是

  ```
  Δy + d_trim · (h_min / L_tether) ≥ tether_radius
  ⇒  d_trim ≥ (tether_radius − Δy) · L_tether / h_min
  ```

  代入方向 A 的 `tether_radius = 1.125 m` 与 S1c 冻结的
  `Δy ∈ [0.15, 0.25]`：最坏 `Δy = 0.15` 时
  `d_trim ≥ (1.125 − 0.15) × 35 / 8 = 0.975 × 4.375 = 4.265625 m`。
  预注册 **`d_trim = 4.30 m`**，并要求工件用**实测** `Δy` 复算该不等式；
  不成立即 `TRIM_PROOF_FAILED`。（`Δy = 0` 时需 `4.921875 m`，故
  `4.30 m` 的成立依赖 S1c 的 `Δy` 数值容差先通过——两条判据的耦合必须
  在工件中显式记录。）
  **须一并披露的代价**：半径从 `0.375` 提到 `1.125` 使 `d_trim` 从
  `1.70 m` 增至 `4.30 m`，即被豁免的头段变长。豁免仍是**逐实例**的
  （只豁免那一个具名实测支撑实例），其余实例全段查询不变；但为了让
  复核者看得见豁免掉的是什么，工件必须额外记录该实例在
  `[0, d_trim]` 内**穿入缆绳胶囊的最大深度**。所用 `Δy`、`θ_min`、
  不等式两端、余量与该穿入深度全部入工件。
- **走廊冲突不可豁免**：若机体球或缆绳胶囊在任何采样点侵入冻结路线
  走廊棱柱，该站点的证书直接失败。**不存在"论文披露"豁免路径。**
  注：锚点合法时该条只淘汰个别站点；锚点非法时它会淘汰**全部**站点，
  这正是 S1c 必须前置的原因。

输出 `runtime/p1-scene-005/workspace.json`
（schema `p1-scene-005-workspace/v1`），含各处分计数、合法节点集合、
被拒节点的首个拒绝原因与阻挡实例 ID，哈希绑定。

#### S2 — 冻结评估域与指向-oracle 可见性场

**S2a — 唯一冻结目标域**

`LoopTargetVehicle.Step` 有 0.5 m 的路点暂停规则
（`delta.magnitude < 0.5f` 时**只推进索引、当帧不移动**），因此运行时
轨迹既不等于折线弧长参数化，也没有精确周期。冻结**唯一的有限 trace**：

| 项 | 冻结值 | 依据 |
|---|---|---|
| 生成律 | `LoopTargetVehicle.Step(Δt)` 的字面复现（含暂停语义、`delta.y=0` 水平投影、`RotateTowards` 240°/s） | `Scripts/LoopTargetVehicle.cs:65-81`；已有实现 `Scene006Trace.Generate` |
| `Δt` | `0.2 s`（= `1/capture_hz`，与 evaluator 的 `weight = deltaSimulationSeconds` 同尺度） | `sensor.capture_hz = 5.0` |
| 状态 | `541` 个状态 `s_0…s_540` | `Scene006Trace.HorizonSteps = 540` |
| **指标域** | **`s_1…s_540`，共 540 个样本、等权** | `Scene006Evaluation` 既有合同（该文件 §5.2 注释与 `for (int k = 1; …)`、`/ 540f`） |
| `s_0` | **只作初始化与可选保真 fixture，不进任何覆盖率分母** | 同上 |
| 窗口 | `540 × 0.2 = 108.0 s`（`108.0/106.485281 = 1.0142` 圈） | — |
| `s_init` | `0.0`，采用 `PlaceAtRouteDistance` 的朝向语义 | 见下方披露 |
| 绑定 | 全 541 状态的 SHA-256（每状态 int32 步号 + position xyz + rotation xyzw 的 float32 位模式） | `Scene006Trace.HashStates` |

> **round 2 必修项 2 的更正**：revision 1 把 `s_0` 计入了覆盖率分母
> （写作"541 状态"），与所复用的 `Scene006Evaluation` 合同冲突。本轮
> 更正为 **540 个指标样本**；所有阈值的秒数换算、权重分母、可见性场与
> 射线预算一律按 540 重算。`s_0` 仍保留在 trace 与哈希里（它是初始化
> 状态，删掉会改变哈希语义），但**不是指标样本**；若 D3 另测 `s_0`，
> 工件必须把那 `8 × 15 = 120` 个采样点单列为非指标样本并单独计数。

**必须披露的两处口径差**：

1. 运行时 `Configure(route)` 之后机体朝向保持 identity，而
   `PlaceAtRouteDistance` 语义会立刻置为
   `LookRotation(route[1]−route[0])`。本 trace 采用后者。差异只影响
   前约 2 个状态（240°/s × 0.2 s = 48°/步，90° 差需 2 步收敛），
   工件必须同时报告"两种起始朝向下的 `C_frustum`/`C_geom`"作为诊断。
   注意该差异全部落在 `s_0…s_2`，而 `s_0` 已不在指标域内。
2. 运行时 `Update()` 按 `Time.deltaTime` 步进，不是固定 0.2 s。因此
   本 trace 是一个**声明的评估域**，不是运行时轨迹的复现；所有 `C*`
   都是"该冻结窗口上的均值"。所有站点用**同一个**窗口，因此站点间
   比较是公平的。

**S2b — 逐样本必须绑定的量**

目标位置、目标朝向四元数、目标 scale、世界 AABB 的 `center/extents`、
evaluator 的 **15 个采样点世界坐标**、相机位置与姿态四元数、云台
`requested/applied` 离轴角与 `Saturated`、斜距、权重、以及该样本是否
属于指标域（`s_0` 标 `false`）。

**S2c — 三个可见性量（分别输出，不合并；分母恒为 540）**

```
LOS_i(p, s)     = CoverageEvaluator 的射线判据（RaycastAll、~0、
                  IgnoreTriggers、distance − 0.05、跳过目标子树）
inFrustum_i(p,s)= 云台按 TetheredGimbal 稳态律指向真值目标位置
                  （yaw 精确，tilt 在 maximum_off_nadir_deg 处 clamp）
                  时的视口矩形判据（z>0 且 x,y ∈ [0,1]）
C_frustum(p)    = |{ s ∈ s_1..s_540 : |{i : inFrustum_i}| / 15 ≥ 0.2 }| / 540
C*(p)           = |{ s ∈ s_1..s_540 : |{i : inFrustum_i ∧ LOS_i}| / 15 ≥ 0.2 }| / 540
U_occ(p)        = |{ s ∈ s_1..s_540 : |{i : LOS_i}| / 15 ≥ 0.2 }| / 540
L_point(p)      = 1 − C_frustum(p)      （指向损失）
L_occ(p)        = C_frustum(p) − C*(p)  （遮挡损失）
```

恒等式 `1 − C*(p) = L_point(p) + L_occ(p)` 必须由工件逐站点自检
（禁双重计数），与 SCENE-006 §5.1 的分解口径一致。

**关键的实现性质**：`LOS_i` 只依赖相机位置与采样点，**与指向无关**。
evaluator 因为 `if (!inFrustum) continue;` 只对入视锥样本发射射线，但
射线是纯函数，因此"先算全部 15 个 `LOS_i`、再与 `inFrustum_i` 取交"与
evaluator 的短路写法**结果恒等**。于是主扫描的射线总数是
`1,040 站点 × 540 状态 × 15 采样 = 8,424,000` 条，
`C*` 与 `U_occ` 由同一遍射线产出。

**S2d — 冻结站点集合**

**单一冻结全格**，不做粗扫/精扫，不做 top-K 精化：

```
P_frozen = { (anchor_x + 4i, anchor_y + h, anchor_z + 4j)
             : i,j ∈ Z, h ∈ {8,12,16,20,24,28,32},
               (4i)² + (4j)² ≤ 35² − h² }  ∪  { p_hover }
```

节点数：h=8→225、12→213、16→185、20→161、24→129、28→89、32→37，
合计 `1,039`；`p_hover`（h=25.0，不在任何层）另计 ⇒ **`1,040` 个站点**。
确定性顺序为 `(h, x, z)` 字典序，取最大值时并列取该序中的第一个。
该构造与 `Scene006StationSet.Build` 逐字相同，实现时必须断言
`TetherLengthM/LatticeStepM/HeightsM` 等于本场景冻结配置的对应值。
（节点数是格构造的函数，与锚点位置无关，故 Stage A 之后不变；但每个
节点的**世界坐标**随锚点平移。）

**量词纪律（硬性）**：全文只允许写 `max_{p ∈ P_frozen}`，**禁止**写
`max_p` 或"工作空间内最优"。工件与证据文档必须逐字包含：

> 冻结格是连续合法域的有限子集。射线场在障碍边界处不连续，格点之间
> 可能存在格上看不见的见证；**格上未找到见证只证明"冻结格未找到"，
> 不证明连续域无余量。**

**预算与可续跑**：预注册 `max_audit_seconds`（建议 `7200`）。工具每
完成一个站点即向 `runtime/p1-scene-005/checkpoint.jsonl` 追加该站点的
完整结果与其输入哈希；超预算 ⇒ 处分 `AUDIT_BUDGET_EXCEEDED`，写出
已完成站点集合与续跑指针，**不得静默截断后当成完整场使用**；续跑必须
校验输入哈希一致，不一致即整批作废重跑。

#### S3 — 判据与阈值（round 2 必修项 4：primary 先冻结）

**联合见证集（同一个 `p` 上联合判定）**

```
Δ(p) = C*(p) − C*(p_hover)
G(p) = |{ s ∈ s_1..s_540 : V*(p,s)=1 ∧ V*(p_hover,s)=0 }| / 540
L(p) = |{ s ∈ s_1..s_540 : V*(p,s)=0 ∧ V*(p_hover,s)=1 }| / 540
W(δ_body, γ_min) = { p ∈ P_frozen :
                     Δ(p) ≥ δ_body  ∧  G(p) ≥ γ_min
                   ∧ S1a 通过  ∧ S1b 连续路径证书通过 }
```

工件必须输出完整的 `W`（而非单个 `p*`），以及 `W` 内按
`(Δ 降序, (h,x,z) 字典序)` 的确定性代表 `p_w`。

| 编号 | 判据 | 判定量 |
|---|---|---|
| (a) | `U_occ(p_hover) ≤ 1 − δ_gap` | 对**任何指向策略**成立的缺口（§7 证明） |
| (b) | `W(δ_body, γ_min) ≠ ∅` | 增益 + 非零测度 + 连续路径，同站点 |
| (c) | S1c 预检通过；S1a/S1b 出具；同批次地面审计复现 `CLEAR`（427 路线采样 / 779 障碍 / 101 车辆 / 0 / 0） | 精确等值 |
| (d) | S0 的 D1+D2+D3+D4 | 见 S0 |

**Primary contract（待用户授权，须在主扫描前冻结）**

```
δ_gap = δ_body = γ_min = 0.05
```

按 540 个指标样本，`0.05` ⇒ **27 tick / 5.4 s**（`0.05 × 540 = 27`）。
语义锚点：`1 − U_occ(p_hover)` 是云台-only 在**任何指向策略**下都拿不
回来的覆盖率损失，`0.05` 以下与 evaluator 的 15 点 `≥0.2` 阈值抖动同
量级、Pareto 上不可分辨；`δ_body = 0.05` 是三条 Pareto 曲线在同一张图
上可分辨所需的净覆盖增益。

**`γ_min` 在同值下不是独立的数学筛选门（必修项 4，须写明）**：由
`C*(p) = μ{两者皆 1} + G(p)`、`C*(p_hover) = μ{两者皆 1} + L(p)` 得
`Δ = G − L`，而 `L ≥ 0` ⇒ **`Δ ≤ G`**。因此当 `δ_body = γ_min = 0.05`
时，`Δ ≥ 0.05` 已蕴含 `G ≥ 0.05`。保留 `γ_min` 的理由有二，都不是
"再筛一遍"：

1. **归因/审计条款**：它强制工件逐站点报告 `G` 与 `L`，使"非零测度"
   （BC-M34-4(b) 的原文）可被逐条核对，并让"`Δ` 大但 `G` 集中在单个
   建筑边缘"这类脆弱见证在工件里可见；
2. 若接受角色将来冻结 `γ_min > δ_body`，它才成为独立的绑定门。

**Secondary sensitivity（不得用来选 primary）**：主扫描完成后，对
`δ_gap, δ_body, γ_min ∈ {0.02, 0.05, 0.10, 0.20}` 的 `4×4×4 = 64` 组合
各输出一行处分，作为敏感性表写进工件。**判定次序是"先冻结 primary →
主扫描 → 出 primary 处分 → 再算 secondary 表"**；工件必须记录 primary
冻结的提交时间早于主扫描开始时间，复核核对该次序。任何"先看 64 行
映射再选 primary"都是本 work item 的科学失效。

#### S4 — 处分决策表（预注册，按序判定，命中即止）

| # | 条件 | 处分 | 工件 | 去向 |
|---|---|---|---|---|
| 0 | D1/D2/D3/D4 任一不过 | `PREDICATE_MISMATCH` | `fidelity.json` + 首个不等点的完整上下文 | 实现角色 |
| 1 | 地面审计非 `CLEAR`，或任一冻结哈希不符 | `BLOCKED_ROUTE_LEGALITY` | `workspace.json` | 实现角色 |
| **2** | **S1c 预检不过**（锚点盘 ∩ 走廊 ≠ ∅，或实测支撑失败） | **`BLOCKED_ANCHOR_CORRIDOR_CONFLICT` / `BLOCKED_ANCHOR_SUPPORT`** | `workspace.json` §S1c | **用户 + 接受角色：`P1-SCENE-007` 先行。不启动主扫描** |
| 3 | 超 `max_audit_seconds` | `AUDIT_BUDGET_EXCEEDED` | `checkpoint.jsonl` + 续跑指针 | 接受角色（调预算或续跑） |
| 4 | S1a 合法节点为空，或 `p_hover` 自身非法 | `WORKSPACE_AUDIT_FAILED` | `workspace.json` | 用户 + 接受角色（设计决策区） |
| 5 | (a) 不成立 | `SCENE_GEOMETRICALLY_BENIGN` | `visibility-field.json` | 返回场景设计（Stage C） |
| 6 | (a) 成立、`W = ∅` | `NO_WITNESS_ON_FROZEN_LATTICE`——**在锚点已合法的前提下**，冻结格上无见证 | `visibility-field.json` + 全站点 `Δ/G/L` 分布 | 返回场景设计（Stage C） |
| 7 | (a)(b)(c)(d) 全成立 | `SUITABLE_EXISTING_ROUTE` | 全部工件 | M3′ 实现提案可消费冻结的适配性工件 |

**顺序的语义（round 2 必修项 1）**：处分 2 在处分 6 **之前**。因此
处分 6 的含义被收紧为"**排除锚点冲突之后**冻结格上没有见证"，不再
可能由锚点缺陷伪造。§6 条 5 要求为每个分支各写一条构造性测试，其中
两条是硬性的：

- 用**当前冻结输入**喂处分函数 ⇒ 必须得到 `BLOCKED_ANCHOR_CORRIDOR_
  CONFLICT`（证明处分 2 可达）；
- 用一个合成的合法锚点 + 空 `W` 喂处分函数 ⇒ 必须得到
  `NO_WITNESS_ON_FROZEN_LATTICE`（证明处分 6 只在锚点合法时可达）。

处分由确定性函数从工件计算，实现形态参照 `controller/rate3_decision.py`
的既有先例，不允许人工填写 verdict。工件字节相同 ⇒ 处分复跑相同。

**诊断量（明确不参与放行）**：改善弧的连续区间、其 `dwell = arclen/2.0`、
以及 `p_hover → p` 的 rest-to-rest 梯形解析时长 `T(len)`，全部作为诊断
写进工件，供 M3′ 自己在预注册超参数时使用。

### Stage C — 定向修改阶梯（条件分支，只在处分 5/6 触发时启动）

- **C1 路线定向修改**：把环线的一段改到天空暴露更好的街道，重跑
  SCENE-002 全部合法性门（沥青带、三维扫掠包络、放置守卫）。
- **C2 已声明的敏感性轴**：缆长、FOV、车速、锚点——§6 明列这四项为
  正式实验必须变化的参数，因此调整它们是合法的系统参数选择，但**改的
  是平台不是场景**，须作为 M3′ 冻结场景参数显式声明并与 M2 基线的
  可比性一起披露；本级需用户裁定。
- **C3 删改遮挡物**：**显式拒绝**。为让指标好看而移除建筑属于研究
  诚信风险，本提案不提供该路径。

（原 Stage 2a"锚点最小重定位"已提为 Stage A / `P1-SCENE-007`，不再是
Stage C 的一级。）Stage C 的任何一级都要以本提案的修订轮或独立 work ID
重新走接受裁定，本提案不预取其接受。

### 真值边界（硬约束）

- 适配性工件是**评估域**产物：它由场景几何 + 冻结真值 trace 导出，与
  `CoverageEvaluator` 同源。它**永不得**被控制器、追踪器、感知输入、
  对外传感器元数据读取。
- 特别地：它**不是**且不得成为 BC-M34-6 的控制器侧 `WorldModelHandle`
  遮挡先验的物料来源。M3′ 的先验必须由其自己被接受的离线管线从场景
  资产独立构建；共享场景资产允许，共享**工件**不允许。
- 建议实现把 schema id `p1-scene-005-*` 列入运行时禁读清单，并把
  "信息来源审计"写进本 work item 的复核范围。
- **Stage A 的反向边界（必修项 5）**：`P1-SCENE-007` 的选点工具**不得
  读取任何可见性量**——不链接可见性模块、不读本 work item 的任何工件。
  该约束是机械可查的（依赖图 + 工件读取审计），写进 SCENE-007 的复核
  范围。

---

## 3. 算法/行为假设（可证伪）

- **H1（`p_hover` 上指向不是瓶颈）**：在真值指向 + 45° clamp 下，
  `p_hover` 处**全部 15 个采样点**在指标域的每个状态都位于视锥内，
  因此 `C_frustum(p_hover) = 1` 且 `1 − C*(p_hover) = L_occ(p_hover)`。

  解析包络（双精度、对**全部目标朝向**取最坏、对折线外扩 ±0.5 m 的
  轨迹管取最坏、逐 15 点而非仅中心点）：相对光轴的最大**竖直**偏角
  `27.096191°` < 垂直半视场 `30°`（余量 `2.903809°`）；最大**水平**
  偏角 `7.290070°` < 水平半视场 `37.589089°`（余量 `30.299020°`）。
  水平方向只需 `aspect ≥ 0.221576` 即成立，故 **H1 对 `A0` 的 `aspect`
  不确定性不敏感**（而 D5 的档案复现对它敏感——两者的地位差别正来源
  于此）。
  **证伪**：S2 输出中存在 `inFrustumCount < 15` 的 (p_hover, 指标状态)
  对。出现即记 `H1_ENVELOPE_VIOLATED` 并交接受角色归因，**不得**因
  "解析上应该成立"而放行。
  **注**：该包络以现锚点为基准，Stage A 移动锚点后须重算。

- **H1′（其他站点上指向会重新成为瓶颈）**：对冻结格的解析预筛：
  `1,040` 个站点里有 `649`（`62.4%`）存在中心离轴 `> 75°` 的状态，
  只有 `391` 个全程无中心出锥；最好指向站点是
  `(144.0, 28.20, 101.0)`（h=28，最大离轴 `60.3140°`），优于
  `p_hover` 的 `70.113398°`。因此机身移动**可能同时改善遮挡而恶化
  指向**，`C_frustum`/`C*` 必须逐站点分开报告。

- **H2（遮挡主导且各向异性）**：`1 − U_occ(p_hover)` 显著大于 0，且
  `C*` 在冻结格上不是常数。**证伪**：`U_occ(p_hover) > 1 − δ_gap`
  （→ 处分 5）或 `W = ∅`（→ 处分 6）。
  **诚实的先验**：SCENE-006 §1.2 已记录本场景的路线走廊是被**主动清空**
  的（3 辆整车删除、2 辆移到 6 m 外、`expected_distractor_count = 1`），
  且净空审计在结构上禁止任何物体靠近路线。因此处分 5 是一个**真实可能
  且概率不低**的结局。反方向的机制同样存在：`p_hover` 高度只有 25 m，
  远端视线以 `70°` 离轴掠过 73.5 m 城市街区，任何 12 m 以上的建筑都
  可能切断视线。

- **H3（离线谓词忠实）**：Edit Mode 的几何/相机与 Play 一致到可忽略。
  **证伪**：D3 逐点不等（→ 处分 0）。
  **本轮收窄**：H3 现在只声称"离线 harness 与 evaluator 在**同一投影
  参数**下逐点一致"。"离线 harness 与**运行时主指标**同义"是一个更强的
  命题，它依赖 `A0`（§9.2）；在 `A0` 完成之前，Stage B 的结论必须带
  `A0` 状态标注出具，不得省略。

- **H4（Stage A 存在合法锚点）**：在预注册搜索半径内存在满足实测支撑 +
  净空 + 走廊排除的锚点候选。**证伪**：SCENE-007 全候选被拒（SCENE-003
  的 1,257/1,257 先例）→ `BLOCKED_ANCHOR_RELOCATION_V2` 回构思角色。
  该假设归 `P1-SCENE-007`，本提案只记录它是 Stage B 的前置。

---

## 4. Inputs, outputs, and affected interfaces

**输入**

- `config/scenario.default.json`（`f9c92052…2ce3`）与其绑定的
  `config/road_data.json`（`111e0759…1894`）；**Stage A 通过后改取
  SCENE-007 产出的新锚点配置字节**；
- 城市场景与既有 `EvaluationOcclusionGeometry` / `RoadSceneAuditor` /
  `RouteCorridorAuditor` / `SceneVehicleAdjustmentApplier`；
- `CoverageEvaluator` 可见性谓词、`TetheredGimbal` clamp 律、
  `TetheredDronePlant` 系留裁剪律、`TargetVisualFactory` 目标构造源
  （四者语义均不改；`A0` 只改投影参数绑定，见 §9.2）；
- 档案证据 `runtime/test-results/ut-p1-scene-002-001-attempt3-pass/
  metrics.json`——**仅用于 D5 诊断**；
- 新增冻结配置 `config/p1-scene-005-suitability.json`。

**输出**（各带 schema 版本与 SHA-256；全部在新目录
`runtime/p1-scene-005/`，不覆盖任何既有路径）

| 工件 | schema | 内容 |
|---|---|---|
| `fidelity.json` | `p1-scene-005-fidelity/v1` | D1–D5 的全部绑定量、代理清单哈希、`projectionMatrix`、逐点等价结果、`A0` 状态 |
| `trace.json` | `p1-scene-005-trace/v1` | 541 状态的位姿、AABB、15 采样点、指标域标志与全 trace 哈希 |
| `workspace.json` | `p1-scene-005-workspace/v1` | S1c 预检；1,040 站点的 S1a/S1b 判定、拒绝原因与阻挡实例；`Δy`/`θ_min`/`d_trim` 不等式两端 |
| `visibility-field.json` | `p1-scene-005-visibility-field/v1` | 逐站点 `C_frustum`/`C*`/`U_occ`/`L_point`/`L_occ`/`Δ`/`G`/`L` 与恒等式自检 |
| `suitability-report.json` | `p1-scene-005-suitability/v1` | primary 处分（含冻结时间戳）、`W` 全集、secondary 64 行敏感性表、诊断量 |
| `checkpoint.jsonl` | `p1-scene-005-checkpoint/v1` | 逐站点续跑记录 |
| `docs/evidence/P1-SCENE-005-suitability.md` | — | 命令、退出码、工件哈希、实际耗时、处分 |

**受影响接口：`A1` 零语义改动；`A0` 改变主指标的投影参数绑定。**
本提案不改帧包/控制协议、坐标或时间语义、主指标**定义**、安全约束或
模型决策逻辑；但 `A0` 改变主指标的**测量语义**（视锥判据实际使用的
宽高比），因此它是独立的强制停点、须用户明确授权，且**不得**与 `A1`
的纯抽取合批称 no-op（§9.2）。本 work item 另需自己的独立代码复核与
一次用户 Unity Edit Mode 执行（`UT-P1-SCENE-005-001`）。

---

## 5. Compatibility with the current v0.3.16 design

- §6 四指标**定义**零改动；`C*` 是 `C_geom` 在"机体站点 × oracle 指向"
  上的离线取值，不是新指标，报告时必须写成 `C_geom*`（oracle-pointing）
  并与闭环 `C_geom` 严格区分标注。`C_frustum`/`L_point`/`L_occ` 沿用
  SCENE-006 §5.1 已冻结的分解口径。
- **`A0` 是唯一触及主指标测量语义的项**，因此单列停点与用户授权；它不
  改四指标的定义文字，改的是"视锥判据实际用哪个宽高比"这一实现事实。
- §6 "场景反天花板"条款要求"加入遮挡与干扰车辆——保证 `C_geom` 显著
  低于 100%"。本 work item 是该条款的**检验**，不是其实施。
- §7 三条消融轴文本零改动；本工件服务于"机身分配是否有效"轴的对照与
  上界，不新增轴、不改对照序列。
- §11 M3′ 行的"预登记场景适配性核查先于 Pareto 测量"前置句由本提案
  落实，符合 `P1-M3M4-SCOPE-001` 验收条件 2。
- §2 `WorldModelHandle` 的括号约束由 §2 的真值边界条款正面承接；
  BC-M34-6 的硬门不因本工件存在而被绕过。
- BC-M34-3/4/5/7/8/9 与 BC-M34-4 的原文全部保持不变；本稿不请求任何
  章程修改。
- **Stage A 的可比性后果（必修项 5，须显式披露）**：移动锚点会改变
  几何，**旧 M2 曲线保留为旧几何下的历史证据，但不再与新几何直接可比**；
  M3′ 须在新几何上重新建立云台-only baseline。该披露必须同时进入
  SCENE-007 的提案、M3′ 的实现提案与论文叙述。
- CLAUDE.md 阶段边界规则：本提案在已接受的 M3′ 章程内，不改研究主张、
  阶段边界、主指标定义或硬件目标。
- **一处需接受角色注意的陈旧正文（只报告，不修改）**：设计 §6 写着
  "现有 `CoverageEvaluator` 只判断真值中心点是否落在视口矩形内，无遮挡"
  ——该句描述的是 M0 之前的 evaluator。**revision 2 报告的另一处
  （`implementation-status.md` 把随机路线归 M1）已由接受角色按 SCENE-002
  更正为 M5，本稿撤回该报告**（round 3 必修项 5）。

---

## 6. Acceptance criteria（逐条可证伪）

1. **冻结先于测量**：`config/p1-scene-005-suitability.json` 在任何
   Stage B 运行前入库，含全部格参数、trace 参数、Minkowski 半径、
   `max_audit_seconds`，以及**经用户授权后冻结的 primary 三阈值**；
   提案与配置的取值逐字一致；复核核对"primary 冻结提交时间 < 主扫描
   开始时间"，以及 secondary 64 行在 primary 处分之后生成。
2. **保真门通过**：D1 精确复现 `913/913/0/0` 并给出代理清单哈希；
   D2 目标字面量与局部 AABB 相符；**D3 在 `8 × 540 = 4,320` 个指标域
   (站点, 状态) 对、`64,800` 个采样点上逐点零容差相等**，fixture 的
   站点选择不依赖 S1 合法性；若另测 `s_0`，其 `120` 个采样点单列为
   非指标样本；D4 记录 `aspect/fov/near/far/projectionMatrix` 与 `A0`
   状态；D5 只作诊断报告。
3. **锚点预检先行**：`workspace.json` 的 S1c 段在任何站点扫描结果之前
   写出，含走廊排除判定、**实测**支撑面分类与高度、`Δy` 及其容差判定；
   S1c 不过时工件中**不得**存在可见性场结果。
4. **工作空间审计出具**：1,040 站点的合法/各类非法计数与首个拒绝原因；
   `p_hover` 的合法性显式列出；每个计入 `W` 的站点都带 S1b 连续路径
   证书（采样数、`Δy`、`θ_min`、`d_trim` 不等式两端与余量、被绑定的
   具名实测支撑实例、阻挡实例）。
5. **处分由确定性函数产出，且每个分支有构造性测试**：给定工件字节，
   处分函数复跑得到同一处分；决策表 0–7 每一条都有直接测试覆盖，其中
   必含两条硬性用例——**当前冻结输入 ⇒ 处分 2 可达**；**合成合法锚点
   + 空 `W` ⇒ 处分 6**（证明处分 6 不会被锚点缺陷伪造）。
6. **可见性场出具**：逐站点五个量齐备，恒等式 `1 − C* = L_point + L_occ`
   逐站点自检通过；`U_occ(p_hover)`、`C*(p_hover)`、`Δ/G/L` 全分布、
   `W` 全集齐备；分母恒为 540；量词披露句逐字在场。
7. **可复现性**：证据文档记录完整命令、退出码、工件 SHA-256 与实际
   耗时；复核者在自己的 worktree 用仓库相对路径能复算出同一数值（浮点
   比较规则沿用 BC-DRB-2 的 typed equality）。
8. **真值边界审计**：复核范围显式包含信息来源审计——确认无任何运行时
   控制/感知/传感器路径导入本 work item 的模块或读取其工件；并确认
   `P1-SCENE-007` 的选点工具不链接、不读取任何可见性模块或工件。
9. **量词与上界纪律**：全文与全部工件中不出现 `max_p`、"工作空间内
   最优"、以及 `[C*(p_hover), max_p C*(p)]` 形式的区间自洽检查；
   `U_occ` 的上界性质有 §7 的证明与一条构造性测试。
10. **`A0`/`A1` 分离**：`A1` 的候选 diff 不含任何投影参数改动，并附
    抽取前后逐点 bit-equal 的 no-op 证明；`A0` 单独成批、附诊断测量
    记录与有界回溯审计表，且**不得**在证据文档中被称为 no-op。
11. **Unity 用例 `UT-P1-SCENE-005-001`**：用户在 Unity 编辑器执行一次
    Edit Mode 生成命令并反馈退出码、Console 错误与工件是否生成；**不进
    Play、不创建 session/run、不消耗任何保留 ID**。（`A0` 的诊断测量
    是另一次、明确标注为诊断的 Play 运行，不消耗 ID、不进证据链。）
12. **不越权**：本 work item 不修改 `docs/phase1-single-drone-design.md`、
    不关闭 M1、不宣称任何用户授权、不启动 Stage C、不移动锚点、不改
    任何既有冻结字节。

---

## 7. Baselines and ablations

### 7.1 唯一可证明的上界：`U_occ(p_hover)`

**命题**：对固定机体站点 `p`，任何指向策略（含任意云台限位、任意
slew、甚至瞬时指向）产生的 `C_geom` 都满足 `C_geom ≤ U_occ(p)`。

**证明**：evaluator 的逐帧布尔是 `visibleCount/15 ≥ 0.2`，其中
`visibleCount = |{i : inFrustum_i ∧ LOS_i}|`。对任意指向，
`{i : inFrustum_i ∧ LOS_i} ⊆ {i : LOS_i}`，故
`visibleCount ≤ |{i : LOS_i}|`；阈值判据对计数单调，所以逐状态
`V*(p,s) ≤ V_occ(p,s)`，在同一指标域上加权后即得。∎

**推论**：`U_occ(p_hover)` 是**云台-only 策略**的 `C_geom` 上界，与
指向律、slew、belief 质量都无关。`1 − U_occ(p_hover)` 因此是
BC-M34-4(a) 意义上"实义缺口"的**下界**——这是本 work item 唯一有资格
叫"上界/天花板"的量。

由于 `C_track` 的成功条件包含 `record.GeometricallyVisible`
（`CoverageEvaluator.RecordObservation`），有 `C_track ≤ C_geom`，
因此上述上界对 `C_track` 同样适用。`C_track|geom` 是条件量，本 work
item **不产生**它的任何界。

### 7.2 不是上界的量（改名并标注）

| 量 | 性质 |
|---|---|
| `C*_static-best(P_frozen) = max_{p ∈ P_frozen} C*(p)` | **可达值**：冻结格内最佳**静态站点**在冻结指向律下的取值。它是"连续域最佳静态站点"的**下界**，**不是**任何动态策略的上界。 |
| `C̄_switch(P_frozen) = |{s : max_{p∈P_frozen} V*(p,s) = 1}| / 540` | **允许逐相位瞬移**的松弛值。它比 `C*_static-best` 大，但仍**不是**动态策略的上界：真上界需要在**连续**合法域上取 sup，而 `max_{格} ≤ max_{连续}`。只作为"格上换站潜力"的诊断。 |
| ~~`[C*(p_hover), max_p C*(p)]` 区间自洽检查~~ | **已删除**：数学上不成立，会把正确的动态测量误判为归因错误。 |

**本 work item 不产生任何动态机身策略的上界，也不承诺产生。**

### 7.3 对照与消融

- **对照的本体**：`C*(p_hover)` 是"云台-only + oracle 指向 + oracle
  belief"这一条**具名参考策略**的取值（不是 sup，因为有限 slew 与
  clamp 意味着真实闭环可能低于它，而某些偏置指向理论上可能高于它）。
  `U_occ(p_hover)` 才是该策略族的上界。
- **消融**：本提案自身不做消融；但它把 M3′ 的机身分配轴从"三条曲线"
  升级为"三条曲线 + 一个可证明的几何上界 + 一个可达的静态最佳值"。
- **与 benign 载体的关系**：SCENE-004 的 `C_geom=1.0` 属设计预期
  （DR-P1-M2-001 N5）。本 work item 不改 benign 载体，也不把困难场景
  的结论回填给 benign 场景。

---

## 8. Failure modes and resource risks

- **处分 2（锚点预检不过）**：§1.4 已由冻结字节确定成立，因此这是现
  字节上**必然**的首个结局。代价是 `P1-SCENE-007` 的先行成本与 M2
  曲线的可比性损失；收益是不在一个已知非法的几何上烧掉 8.42×10⁶ 条
  射线，也不把锚点缺陷伪装成"格上无余量"。
- **处分 5（场景其实是良性的）**：概率不低（§3 H2）。代价是 Stage C
  的场景返工，但这正是把核查前置的理由。
- **处分 6（冻结格上无见证）**：**必须按"锚点合法前提下、格上未找到"
  措辞**，不得写成"连续域无余量"。
- **处分 0（离线谓词不忠实）**：缓解是 D1–D4 四道门 + §9.2 `A1` 的
  "共用同一代码路径"。
- **`A0`：运行时投影语义未受控（本轮升级为主指标风险）**：
  `SensorFrameWriter.cs:173` 在 `:206` 的 `FramePublished?.Invoke`
  **之前**清空 `targetTexture`，而 evaluator 的 `WorldToViewportPoint`
  在该回调内执行。因此**历史与当前的 `C_geom`、真值框、IoU、
  `C_quality` 都可能依赖 Game View 宽高比**。附带发现：
  `Scene006SceneRig.cs:128` 的离线评估相机**显式**设了
  `aspect = imageWidth/imageHeight`，而运行时没有——两者之间因此存在
  一条此前未被记录的 parity 缺口。处置见 §9.2 `A0`；**在诊断测量完成
  之前，本提案不对影响方向或量级下任何结论**。
- **计算预算失控**：主扫描射线总数 `1,040 × 540 × 15 = 8,424,000` 条。
  缓解是单遍复用 + 预注册时限 + 逐站点 checkpoint。
- **阈值被事后调整**：缓解是 primary 先冻结 + 时间戳次序可复核 +
  secondary 表只在 primary 处分之后生成。
- **量词滑坡**：缓解是 §6 条 9 的机械检查。
- **Stage A 全候选被拒**：SCENE-003 的 1,257/1,257 先例。归
  `P1-SCENE-007` 的失败模式，届时回构思角色重新设计。
- **退化 belief 被误读为完整 belief**：报告与论文必须写明 `C*` 是
  oracle belief + oracle 指向下的**参考值**。
- **资源**：Stage B = 0 个 Play 会话、0 个研究 run ID、0 次采集预算
  动用、0 个 qual ID，仅一次用户 Edit Mode 执行。`A0` 的诊断测量是一次
  诊断 Play 运行（COORD-005 通道，零 ID、不进证据链）。RATE-003 的 20
  次会话预算不受影响（0c 仍为 0/20）。

---

## 9. Suggested implementation scope（建议，不强制）

### 9.1 复用已通过代码符合性复核的 SCENE-006 构造

| 模块 | 用途 | 复用条件 |
|---|---|---|
| `Scene006Trace` | 生成 + 哈希绑定 541 状态 trace | 断言 `StepSeconds=0.2`、`TurnRateDegPerSecond=240`、`WaypointPauseDistanceM=0.5` 与运行时字面量一致 |
| `Scene006Visibility` | 15 点谓词、`C_frustum`/`C_geom` 分离、`OccludingRoots` 归因 | 断言 `VisibleFractionThreshold == evaluation.minimum_visible_sample_fraction` |
| `Scene006Evaluation` 的域合同 | `s_1…s_540` 分母 | 本提案与其一致（必修项 2） |
| `Scene006StationSet` | 冻结格构造与确定性排序 | 断言 `TetherLengthM/LatticeStepM/HeightsM` 等于本场景配置；`supportY` 传 `Config.Anchor.y`（运行时高度带以锚点 y 为基准） |
| `Scene006RouteGeometry` | 周长/弧长采样/SHA-256 | 无 |

`Scene006PathCertificate` **不能直接复用**：其 `BodyRadiusM = 1.625`
是 SCENE-006 的冻结常量，而本场景由机体可见体导出的是 `2.235`（§2 S1a），
且本轮的 `d_trim` 改为含 `Δy` 的闭式。因此新增
`P1Scene005PathCertificate`，构造与 SCENE-006 §5.4 逐字相同但半径、
`Δy` 与 `d_trim` 由本场景配置注入，并**用一条 EditMode 测试证明：喂入
SCENE-006 的常量与 `Δy = 0` 时它复现 `Scene006PathCertificate` 的输出**
——以等价性换取复用，而不触碰已冻结的文件。

### 9.2 两个**分离**的强停点（round 2 必修项 3）

> **`A0` 与 `A1` 不得合批，也不得整体称为 no-op。**

**`A0` — 运行时相机投影语义修复（主指标测量语义变化，须用户明确授权）**

1. **`A0.1` 诊断测量先行（零 ID）**：走 COORD-005 诊断通道，在一次明确
   标注为诊断的 Play 运行中记录 `SensorCamera.aspect` 与
   `projectionMatrix` 在**两个时刻**的取值——`Render()` 期间（有
   `targetTexture`）与 `FramePublished` 回调内（已清空）——并记录当时
   的 Game View 分辨率。**在该测量出来之前，不对影响方向或量级下结论。**
2. **`A0.2` 修复**：`SensorCamera.aspect = sensor.width / sensor.height`
   在构造时显式绑定（并保证此后无 `ResetAspect()`）；新增测试断言
   渲染时刻与评估时刻的 `projectionMatrix` 一致，且与帧包发布的
   `intrinsics_px` 元数据一致。
3. **`A0.3` 完整影响审计（round 3 必修项 2 重做）**。revision 2 的
   七行选摘被明确判为不完整；本稿改为**机械枚举 + 逐条判定**，并接受
   "历史 aspect 不可恢复"这一前提。

   **第一步 — 机械枚举消费方（不得手工选摘）**：对
   `docs/current-status.md`、`docs/implementation-status.md`、
   `docs/unity-test-log.md`、`docs/evidence/**`、`docs/reviews/**`、
   `docs/design-reviews/**`、`docs/archive/**` 与
   `runtime/test-results/**` 全量检索
   `C_geom` / `c_geom` / `C_track` / `c_track` / `C_track|geom` /
   `truth_box` / `IoU` / `iou` / `visible_sample_fraction` /
   `target_bbox_area_px` / `target_center_error_px` / scouting truth，
   把命中清单连同其 SHA-256 写进工件。**构思角色的预扫（非权威、供
   规模参考）**：`docs/evidence/`、`docs/reviews/`、
   `docs/unity-test-log.md` 命中 **41 份**文档，`runtime/test-results/`
   下有 **17 个**归档 run 目录。revision 2 漏掉的 RATE-001、
   TRACK-001/002、M0-001、TEST-001、SCENE-001 等都在其中。

   **第二步 — 逐条判定三件事**：

   | 字段 | 含义 |
   |---|---|
   | 可复放性 | 归档的原始输入是否足以做 4:3 反事实重放。需要**逐帧相机位姿 + 目标位姿/朝向**；`metrics.json` 只有聚合量，`evaluation_truth.jsonl` 只有目标世界 xz 与真值框，**都不含相机位姿**——因此多数 run 预期为"不可复放" |
   | 敏感性范围 | 在 `aspect ∈ [1.0, 21:9]` 上可证明的取值区间 |
   | 分类 | `UNCHANGED` / `LIMITATION_ONLY` / `REATTRIBUTION_REQUIRED` / `UNRESOLVABLE` |

   **第三步 — 用可证明的结构性结论收窄工作量**（构思角色已算出，实现
   者须复算并逐 run 核验其前提）：

   - **天底指向的 run 高度敏感。** 垂直半视场 `30°` 与 aspect 无关，
     水平半视场随 aspect 变。以中心点判据算 SCENE-002 环线的弧长占比：
     `1:1 → 0.174258`、`4:3 → 0.196844`、`16:10 → 0.214923`、
     `16:9 → 0.226991`、`21:9 → 0.264604`。**注意档案值
     `0.219562724` 落在 16:10 与 16:9 之间**——但这**不能**据以推断
     当时的 aspect：evaluator 用的是 15 点 `≥0.2` 判据，它比中心点
     判据更宽松，4:3 下本来就会高于 `0.196844`。两种解释（更宽的
     Game View / 更宽松的判据）**从 `metrics.json` 单独无法分离**，
     这正是 round 3 所说"诊断 Play 不能支撑历史主张"的具体形态。
   - **指向目标的 run 结构性不敏感。** 云台 yaw 精确指向目标时，目标
     位于图像竖直中线上，15 个 AABB 采样点的最大**横向**离轴角在
     `p_hover` 上只有 `7.290070°`（§3 H1 的包络）。保持全部采样点横向
     在锥内所需的最小 aspect 是 **`0.221576`**——远低于任何真实窗口
     形状。故这类 run 的 `C_geom` 对 aspect **不敏感**，可判
     `UNCHANGED`，**但该结论有前提**：指向必须确实落在目标附近。
     追踪器驱动指向（RATE-002 follow、DETECT qual-3）的 yaw 误差要
     逐 run 用归档观测量界定；界不住即降为 `UNRESOLVABLE`，不得默认
     `UNCHANGED`。

   **第四步 — 硬性纪律**：历史 aspect 不可恢复时**记为未知并保守
   归因**，**不得**用新诊断运行时的 Game View 代替。诊断 Play 的产物
   与正式审计证据**分栏存放**（诊断进 `runtime/p1-scene-005/diagnostic/`
   并标注不入证据链，审计表进 `fidelity.json` 的独立段）。历史证据
   **不自动重开**；审计只判定"哪些主张需要重新归因"，重开与否由接受
   角色按 §4.6 裁定。

**`A1` — 谓词抽取（纯 no-op，独立停点）**

把 `CoverageEvaluator.EvaluateVisibility` 的纯几何内核抽成
`internal static`（输入 camera/bounds/corners/target/阈值，输出
`inFrustumCount`/`visibleCount`/box），运行时与离线 harness **调用同一
函数**。谓词保真从"测试"变成"构造恒等"，D3 退化为回归证明。
**候选 diff 不得包含任何投影参数改动**；附抽取前后逐点 bit-equal 的
no-op 证明。

**退路 `R`**：若接受角色不批 `A1` 的运行时触碰，则用
`Scene006Visibility` 复制体 + D3 逐点零容差比对，代价是仍需一个
`internal` 测试入口，且复制体长期存在漂移风险。

### 9.3 批次与文件

| 批次 | 内容 | 前置 |
|---|---|---|
| **Stage A** | `P1-SCENE-007` 的选点工具、候选工件、支撑/净空/走廊证书 | 用户授权 + SCENE-007 Acceptance |
| `A0` | 诊断测量 → 运行时 `aspect` 绑定 → 回溯审计 | **用户明确授权**；独立强制停点 + 独立复核 |
| `A1` | 谓词内核抽取 + no-op 证明 + D1–D4 保真工具 | 独立强制停点 + 独立复核 |
| `B1` | `P1Scene005PathCertificate` + `Editor/P1Scene005SuitabilityGenerator.cs`（场景修正应用、代理构建、S1c 预检、站点审计、工件落盘与哈希） | `A1` 通过 |
| `B2` | 可见性场扫描 + checkpoint + `controller/scene005_suitability.py`（确定性处分函数）+ `tests/test_scene005_suitability.py` + EditMode 测试（决策表 0–7 全覆盖含两条硬性构造用例、typed equality、预算超限、锚点预检、缆绳胶囊/走廊侵入、量词措辞机械检查） | Stage A 与 `B1` 通过；primary 阈值已冻结 |

另加 `config/p1-scene-005-suitability.json` 与
`docs/evidence/P1-SCENE-005-suitability.md`。

---

## 10. 悬账记账建议（仅建议路径，本提案不关闭任何门）

1. **M1 验收**：参数化由 SCENE-001/002/004 证明；`C_geom` 显著 <100%
   目前只有 `0.219562724`，而 DR-P1-M2-001 N8 已禁止用它论证遮挡。
   建议接受角色等 Stage B 的 `U_occ(p_hover)` 落地后再补门板并归因关闭。
   **本提案不关闭 M1。** 附加提醒：若 `A0` 判定该数字受宽高比影响，
   M1 的候选证据需连同 `A0` 的回溯审计一起归因。
2. **N5 指向更新**：建议接受角色在 M2 关闭检查单里同步"困难场景义务
   实际落在 M3′/M4′ 并以本 work item 为前置"。
3. **陈旧行**：设计 §6 的陈旧 evaluator 描述。
   （`implementation-status.md` 的 "randomized route generation belongs
   to M1" 已由接受角色更正为 M5，本稿撤回该条报告。）
4. **相机 `aspect` 未受控**：`A0`，见 §8/§9.2。
5. **SCENE-006 离线 rig 与运行时的 `aspect` parity 缺口**：只登记，
   不重开 SCENE-006 的终态。

以上五条都只是报告，本提案不改任何一份文件。

---

## 11. Open questions

- **OQ-1（改写）**：primary 三阈值 `0.05` 的最终取值须由用户授权后由
  接受角色冻结，且必须在主扫描前完成。构思角色的推荐依据见 §2 S3；
  secondary 64 行只在 primary 处分之后生成，不得倒过来用。
- **OQ-2（已解决，保留记录）**：(b3) 阶段门已在 revision 1 撤回；
  dwell/transit 为诊断量，采用 rest-to-rest 梯形剖面。
- **OQ-3（改写）**：`P1-SCENE-007` 的搜索半径与最小位移的确定性排序
  细则由该提案给出；本提案只要求它不读任何可见性结果。若 SCENE-007
  全候选被拒，回构思角色重新设计，而**不是**放宽本 work item 的安全
  合同。
- **OQ-4**：可见性场是否需要覆盖 `maximum_off_nadir_deg` 之外的假想
  云台。建议本轮**不做**。
- **OQ-5**：格步长 4 m 是否够密。建议先跑 4 m 格；只有在 `Δ` 分布显示
  余量集中在格边界附近时才加密，且加密必须是新的一轮预注册。
- **OQ-6（新）**：`A0` 的回溯审计若判定某条档案主张实质改变，是否触发
  该 work item 的重开，属接受角色按 §4.6 的归因裁量，本提案不预判。

---

## 12. Acceptance review decision

### Acceptance round 1 — 2026-08-05

Decision: **REVISION_REQUESTED**

Rationale:

提案正确拒绝把 `0.219562724` 当作遮挡证据，也正确保留评估真值与
`WorldModelHandle` 的硬隔离；先用零 Play 的离线门检查既有路线，方向与
BC-M34-4/5/9 一致。但当前稿不能按字面交给实现角色：它只用 `p_hover` 到
目标中心的 `70.113398° < 75°` 支撑 H1，未覆盖 evaluator 的 15 个 AABB
样点、目标姿态和其他合法机位；粗扫 top-3 后精扫不能证明全文使用的
`max_p`；节点净空也不能证明连续机身/系留路径合法。更关键的是，
`max_p C*(p)` 只是最佳**静态站点**均值，不是动态机身策略的上界，动态
策略可随目标相位换位并超过该量。把它作为 M3′ Pareto 的分母/自洽上界会
形成错误研究归因。

本稿还把 (b3) 明说成“章程之上的加强项”，却让它直接决定 Stage 1 是否
放行；这实质强化了已接受的阶段门。2026-07-31 的用户授权只支持
BC-M34-4 原文，没有授权这一新增关闭条件。本轮因此不接受任何实现、运行
或范围变化，也不新增授权账本条目。

Required revisions for round 2:

1. **以最新基线重写问题陈述和 BC-M34-4 对映。** 兼容性基线从陈旧的
   v0.3.11 更新到当前 v0.3.16；逐条映射 (a)/(b)/(c)，并吸收已保留的
   SCOPE-002/SCENE-006 负结果：现场景 `L_frustum=0.0000`、云台饱和占比
   `0.7353`，所以“当前限位裕度”阈值式对照会触发却没有对应的视锥损失。
   不得把 SCENE-006 的协议终态写成 SCENE-005 的 supersession 或资格证据。
2. **冻结唯一的目标/评估域，并覆盖真实 15 点谓词。** 明确选择哈希绑定的
   有限 `LoopTargetVehicle` trace，或真正周期的弧长相位律；不得再把
   `212.97/2` 当作运行时代码的状态周期。逐样本必须绑定目标位置、朝向、
   scale、AABB 15 点、相机姿态和权重，并分别输出 `C_frustum`、`C_geom`
   及其差。H1 只能按实际逐点结果成立，不能由目标中心角度外推。
3. **把保真门改成逐点等价门。** 仅有 913/913/0 计数和 nadir 聚合值的
   `0.03/0.05` 容差不足以证明谓词相同。冻结具名 fixture（至少
   `p_hover ×` 全 trace，另含多个合法机位），逐点比对
   `inFrustumCount`、`visibleCount`、boolean，零容差；同时绑定完整
   SHA-256、proxy 对象清单、layer/mask、排除集合及目标 prefab 身份。
4. **给每个可计入见证的机位出具连续合法路径证书。** 冻结唯一路径和
   rest-to-rest 速度/加速度律；用带半步 Minkowski 膨胀的保守离散或同等
   连续证明，覆盖机体球与沿途每个系留胶囊。锚点端只可忽略具名、实测的
   支撑实例，其他 collider 一律 fail closed。锚点/目标走廊冲突在现有
   安全合同下不能靠“论文披露”变成 `SUITABLE`；若要放宽，须另取用户授权。
5. **改正搜索与存在量词。** 若保留两段网格，只能报告
   `max_{p∈P_frozen_grid}`，并说明 top-K 精扫可能漏掉非连续射线场中的
   见证；不得称全工作空间 `max_p`。处分必须在同一个合法见证 `p` 上同时
   检查增益、非零测度和路径证书，而不是先选仅使 `Δ` 最大的 `p*` 再检查
   其他条件。网格未找到见证只能证明“冻结网格未找到”，不能证明连续域无余量。
6. **撤回未经授权的 (b3) 阶段门，或先取得用户明确授权。** 为保持现有
   BC-M34-4，round 2 默认把 dwell/transit 降为诊断量。若构思角色仍要把
   它作为放行条件，须先提出可选择的范围变更并取得用户授权；同时必须冻结
   真实 trace 上的改善区间、触发时刻、唯一运动剖面和解析 transit，不能写
   “一阶速度模型（4 m/s、4 m/s²）”这种把速度模型与加速度约束混在一起的口径。
7. **改正 oracle 上界和 Pareto 自洽关系。** 将 `max_p C*(p)` 改名为最佳
   静态站点量；它不能上界动态策略。若需要真正的宽松上界，可另定义
   `Σ_s w_s max_{p∈P_legal} V(p,s)/Σ_s w_s` 并明确它允许逐相位瞬移，或给出
   有限机身/云台动力学的合法动态 oracle。分别写清哪些不等式适用于
   `C_geom`、`C_track`，删除 `[C*(p_hover), max_p C*(p)]` 的错误区间检查。
8. **重做阈值、处分和交接合同。** 给 `δ_gap/δ_body/γ_min` 各自提供与
   “实义缺口/非零测度”对应的选择依据和阈值敏感性；在用户尚未选择新的
   阶段门前，不得把任意数值伪装成已授权基线。用完整工件路径/hash、失败
   责任人和可续跑语义消除分支歧义，并把“零 Play、不改既有冻结输入”与
   “会新建冻结配置/输出工件”的字面矛盾改清楚。

Disposition:

- BC-M34-4/5/6/9、BC-M34-7 和当前正式设计均不改变；
- `P1-SCENE-005` 未被 supersede，两个既有 `C_geom` 归因与 `0.500000 m`
  锚点冲突发现保留，但均不是场景资格证据；
- 不授权实现代码、Unity/Edit Mode 执行、session/run/profile/qual ID、
  Stage 2、M1 关闭或任何资源消耗；
- 构思角色提交 revision 1 后返回 Acceptance round 2。

---

## 13. Revision 1 逐条回应（构思角色，2026-08-05）

**1 — 基线改 v0.3.16、逐条映射 (a)(b)(c)、吸收负结果。** 已改。
兼容性基线整体挂 v0.3.16，并在文首给出核对依据（v0.3.12–v0.3.16 只改
设计文档头部 blockquote，本提案映射的 §4.1/§4.3/§6/§7/§10/§11 正文自
v0.3.11 起逐字未变）。BC-M34-4 三肢映射表在 §1.1。SCOPE-002 的
`0.0000` / `0.7353` / `70.113398°` 进入 §1.3 与 §1.6，并给出本轮新增
推论：BC-M34-3 的触发量在本场景上每圈空转 `73.53%`，因此阈值式与
云台-only 的任何差异都只可能来自遮挡改变。§1.6 末段写明 SCENE-006 的
终态与全部测量结论**不得**用作本 ID 的 supersession 或资格证据，只复用
其代码构造（依据是 round 8 的代码符合性 `PASS`）。

**2 — 冻结唯一评估域、覆盖真实 15 点谓词。** 已改。选择"哈希绑定的
有限 trace"分支（§2 S2a）：541 状态、`Δt = 0.2 s`、等权、`s_init = 0`、
全 trace SHA-256 绑定，生成律是 `LoopTargetVehicle.Step` 的字面复现。
撤回"`212.97/2` 是周期"与"弧长均匀 belief"两处表述，并披露两处口径差
（起始朝向语义、`Time.deltaTime` vs 固定步长）。逐样本绑定量见 S2b；
`C_frustum`/`C*`/`U_occ`/`L_point`/`L_occ` 分别输出并逐站点自检恒等式
（S2c）。H1 改为"解析包络（逐 15 点、全朝向最坏、±0.5 m 轨迹管）+
实测判定"，并新增 H1′ 记录 `62.4%` 的站点会重新出现指向损失——正是
必须分离两个量的证据。

**3 — 保真门改逐点等价门。** 已改。旧 D2 的 `0.03/0.05` 聚合容差**撤销
门地位**、降为诊断 D5；新 D3 在 `9 × 541 = 4,869` 个 (站点, 状态) 对、
`73,035` 个采样点上逐点零容差比对 `inFrustumCount`/`visibleCount`/
boolean。D1 绑定完整 SHA-256、代理实例清单哈希、layer/mask、排除集合；
D2 绑定目标 prefab 身份（`TargetVisualFactory` 字面量 + 局部 AABB）。
另外新增 D4：本轮发现 `SensorCamera.aspect` 在运行时从未被显式设置，
因此必须显式绑定并记录 `projectionMatrix`；该发现同时作为一条独立风险
交接（§8、§10）。§9.2 给出更强的方案 P——让运行时与离线共用同一函数，
把 D3 从测试变成构造恒等。

**4 — 连续路径证书。** 已改（§2 S1b）。唯一冻结路径 `p_hover → p` 直线
段；rest-to-rest 梯形剖面 `v ≤ 4 m/s`、`a ≤ 4 m/s²`（取自冻结配置），
解析时长入工件不入门；`δ = 0.25 m` 离散 + `δ/2 = 0.125 m` Minkowski
膨胀，因此离散判定保守蕴含连续判定；机体球与沿途每个系留胶囊逐采样点
判定，闭集相切计违规。锚点端只有**具名的实测支撑实例**可在 `[0, d_trim]`
被忽略，`d_trim = 1.70 m` 由本场景 `θ_min = 13.212980°` 重新导出；其余
collider 全段 fail closed。本轮同时把 `body_nominal_radius` 从
SCENE-006 的 `1.0` 更正为由 `AddDroneVisual` 字面量导出的 `1.61`
（外接半径 `1.601125`），机体球半径变为 `2.235 m`。锚点/走廊冲突改为
**不可豁免**：§2 S4 处分 6 是 `BLOCKED_ANCHOR_CORRIDOR_CONFLICT`，
不是 `SUITABLE`，且本稿明确指出该冲突在现字节上已确定成立，因此处分 7
在用户另行裁定前不可达。

**5 — 改正搜索与存在量词。** 已改。撤销两段式网格与 top-K 精扫，改为
**单一冻结全格 1,040 站点**（构造与节点数在 §2 S2d 可独立复算）。全文
只写 `max_{p ∈ P_frozen}`；§2 S2d 载入逐字披露句（格是连续域的有限
子集、射线场在障碍边界不连续、格上未找到只证"格上未找到"）；§6 验收
条件 8 把禁用措辞变成机械检查。见证改为**联合见证集** `W`——增益、
非零测度、S1a、S1b 在同一个 `p` 上联合判定，输出全集而非单个 `p*`。

**6 — 撤回 (b3) 阶段门。** 已撤回，且**不请求**任何替代授权。
dwell/transit 降为诊断量（§2 S4 末段），不参与放行；旧 H3 一并撤回。
运动剖面口径改写为 rest-to-rest 梯形（`v_max`/`a_max` 分列，解析时长
公式给出），不再使用"一阶速度模型（4 m/s、4 m/s²）"的混合措辞。
处分表由 9 行减为 8 行（0–7），原处分 6 `MARGIN_UNREACHABLE_IN_TIME`
随阶段门一并删除。

**7 — 改正 oracle 上界与 Pareto 自洽。** 已改（§7）。`max_p C*(p)`
改名 `C*_static-best(P_frozen)` 并标注为**可达值**、是连续域最佳静态
站点的下界、**不上界任何动态策略**。新增 `C̄_switch(P_frozen)` 并明确
它允许逐相位瞬移、且因 `max_{格} ≤ max_{连续}` 仍**不是**动态上界。
删除 `[C*(p_hover), max_p C*(p)]` 区间自洽检查。新增本 work item 唯一
**可证明**的上界 `U_occ(p_hover)`（去掉视锥判据、只留射线）并给出证明：
`{inFrustum ∧ LOS} ⊆ {LOS}` + 阈值判据对计数单调。由
`C_track ≤ C_geom`（`RecordObservation` 要求 `GeometricallyVisible`）
说明该上界同样适用于 `C_track`，而 `C_track|geom` 本 work item 不产生
任何界。本稿并**不承诺**产生动态策略上界，明说那是另一个最优控制问题。

**8 — 重做阈值、处分与交接合同。** 已改。三个阈值改为**预注册 4×4×4
网格 + 全映射工件**（§2 S3），并给出每个阈值的语义锚点与冻结窗口
`108.0 s` 上的秒数换算；全部标注为"构思角色推荐、未获授权、非基线"，
接受角色可在看到 64 行映射后冻结。处分表补齐每个分支的工件路径与责任
去向（§2 S4），续跑语义写在 §2 S2d（逐站点 `checkpoint.jsonl` +
输入哈希校验，不一致即整批作废）。工件路径/schema/哈希表在 §4。
字面矛盾在 §2 Stage 1 的 blockquote 中改清：不覆盖任何既有冻结字节，
但新增本 work item 自己的新文件与新 schema id；同处说明 COORD-005
人眼保真硬门因"不渲染、不落帧"而不触发，代之以 D2/D3。

**本轮不主张的事项**：不主张任何新的用户授权；不主张 supersession；
不主张实现、Unity/Edit Mode 执行、session/run/profile/qual ID 消耗、
Stage 2 或 M1 关闭。提交后返回 Acceptance round 2。

---

## 14. Acceptance review decision — round 2

### Acceptance round 2 — 2026-08-05

Decision: **REVISION_REQUESTED**

Rationale:

Revision 1 已实质解决 round 1 的大部分问题：它改挂当前 v0.3.16 基线，
冻结单一格与逐点保真域，撤回未经授权的 (b3)，补入连续路径证书，并把
静态最佳值与真正上界分开。这些改动保留。但当前文本仍不能按字面实现：
锚点在走廊内意味着每条“锚点→机体”的缆绳胶囊从起点就侵入走廊，故
S1b 对所有站点失败、`W` 恒为空；决策表又先判 `W = ∅`，导致已经确定的
`BLOCKED_ANCHOR_CORRIDOR_CONFLICT` 分支不可达。trace 也把仅用于初始化的
`s_0` 错计入覆盖率分母，与所复用的 SCENE-006 实现合同不一致。

另外，`SensorCamera.aspect` 不是单纯的离线 harness 风险：采集器在发布
帧前已经清空 `targetTexture`，而 evaluator 在 `FramePublished` 回调中才
调用 `WorldToViewportPoint`。因此历史和当前 `C_geom`、真值框、IoU 与
`C_quality` 可能依赖 Game View 宽高比。只把离线相机钉成 4:3 不能证明
它与运行时主指标同义。修复运行时宽高比会改变测量语义，不能与“纯函数
抽取的 no-op”合并，也不能在没有用户明确授权时由本轮自行接受。

Required revisions for round 3:

1. **修正锚点冲突与路径证书的判定顺序。** 当前字节的锚点走廊冲突必须
   在构造 `W` 之前 fail closed 为 `BLOCKED_ANCHOR_CORRIDOR_CONFLICT`；不得
   先让每条 S1b 因同一锚点起点失败，再误归因为
   `NO_WITNESS_ON_FROZEN_LATTICE`。D3 的多站点 fixture 也不得以“存在
   S1-合法站点”为前提。给决策表每个分支补一条构造性测试，证明处分 6
   在当前冻结输入上可达、处分 5 只表示排除锚点冲突后的冻结格无见证。
2. **改正 541 状态与 540 个覆盖样本的口径。** 保留 trace
   `s_0…s_540`，但与 `Scene006Evaluation` 的既有合同一致：`s_0` 只作
   初始化/可选保真 fixture，全部覆盖率、权重分母、阈值秒数和可见性场
   使用 `s_1…s_540` 共 540 个样本。全场主扫描射线数相应为
   `1,040 × 540 × 15 = 8,424,000`；若 D3 另测 `s_0`，须把它明确列为
   非指标样本并单独计数。
3. **把相机投影语义修复与谓词抽取拆成两个强停点。** 修订稿应提出
   `A0`：运行时 `SensorCamera.aspect = sensor.width / sensor.height`
   的显式绑定、元数据/投影矩阵一致性测试及历史影响审计；这是主指标
   测量语义变化，须在接受前取得用户明确授权。历史证据不自动重开，
   但必须做有界回溯审计；若受影响主张发生实质变化，再单独归因，不能
   预先承诺“全部沿用”。`A1` 才是方案 P 的纯谓词抽取，并以抽取前后
   bit-equal 证明 no-op。不得把 A0+A1 整批称为 no-op。
4. **主阈值必须在看见场结果前冻结。** 推荐把
   `δ_gap = δ_body = γ_min = 0.05` 作为待用户授权的 primary contract，
   并在任何主扫描/完整映射前冻结；`4×4×4` 的 64 行只作 secondary
   sensitivity，不得先看映射再选主门。按 540 个覆盖样本，`0.05` 是
   27 tick / 5.4 s。还须写明：当 `δ_body = γ_min` 时，由
   `Δ = G − L ≤ G` 可知 `Δ ≥ 0.05` 已蕴含 `G ≥ 0.05`，所以同值的
   `γ_min` 是显式归因/审计条款，不是独立的数学筛选门。本项改变阶段门
   数值，仍需用户明确授权后才能接受。
5. **把最小锚点重定位放在全场扫描之前，且禁止按可见性调场。** 当前
   锚点已确定不合法，在它上面先跑八百余万条射线不会产生可消费的场景
   资格工件。Revision 2 应把 Stage 2a 改为独立的先行提案/裁定：仅按
   最小位移、实测支撑与净空的确定性排序选点，不读任何可见性结果；
   不放宽安全合同。旧 M2 曲线保留为旧几何下的历史证据但不再直接可比，
   M3′ 在新几何上建立新的 cloud-only baseline。未经用户授权与新一轮
   Acceptance，不得搬锚点或执行全场扫描。
6. **补全锚点端 trim 的高度证明。** `d_trim = 1.70 m` 的推导不能只用
   相对高度带角度，同时又把 `Config.Anchor.y − supportY` 仅作报告。
   修订稿必须把实测支撑面与配置锚点的高度差纳入最坏角度/包络证明；
   若差值超出预注册容差则 fail closed 并重新推导，不得沿用 1.70 m。

Disposition:

- 接受角色推荐方案 P，但只对 `A1` 的共享纯谓词内核成立；`A0` 是另一个
  主指标语义停点，二者均尚未获实现许可；
- 接受角色推荐 primary 三阈值先冻结为 `0.05`、64 组合降为敏感性表，
  以及“最小锚点重定位而非放宽安全合同”；这些是退修方向，不是已经发生
  的用户范围/指标/安全授权；
- BC-M34-4/5/6/9、BC-M34-7、正式设计 v0.3.16 与历史证据终态均不改变；
- 不授权实现代码、Edit Mode/Play、session/run/profile/qual ID、Stage 2、
  M1 关闭、锚点移动、主阈值采用或任何资源消耗；
- 构思角色提交 revision 2 后返回 Acceptance round 3。用户本轮原话
  “好的，把这些意见写回给fable”要求执行本次退修交接；该句不扩张解释
  为上述主指标或安全语义变更已经获批。

---

## 15. Revision 2 逐条回应（构思角色，2026-08-06）

**1 — 修正锚点冲突与路径证书的判定顺序。** 已改，且承认这是 revision 1
的实质缺陷：锚点在走廊内 ⇒ 每条"锚点→机体"缆绳胶囊在 `u=0` 就侵入走廊
⇒ 全部 1,040 站点的 S1b 失败 ⇒ `W` 恒空 ⇒ 旧表在 `W = ∅` 一行命中，把
已确定的锚点缺陷误归因成"格上无余量"。本轮把锚点合法性提为 **§2 S1c
预检门**，位置在处分表第 **2** 行、在任何工作空间扫描、可见性场与 `W`
构造之前；`NO_WITNESS_ON_FROZEN_LATTICE` 降到第 6 行并把语义收紧为
"**锚点已合法的前提下**冻结格上无见证"。D3 的 fixture 改为**不依赖
S1 合法性**的纯几何确定性选择（`p_hover` + 冻结格每个高度层的首个站点，
共 8 个），避免锚点非法时 D3 自我阻塞。§6 条 5 要求每个分支各一条
构造性测试，其中两条硬性：当前冻结输入 ⇒ 处分 2 可达；合成合法锚点 +
空 `W` ⇒ 处分 6。

**2 — 改正 541 状态与 540 覆盖样本的口径。** 已改。trace 仍是
`s_0…s_540`（`s_0` 删掉会改变哈希语义），但**指标域收为 `s_1…s_540`
共 540 个等权样本**，与 `Scene006Evaluation` 的既有合同一致（该文件的
§5.2 注释与 `for (int k = 1; …)`、`/ 540f` 已核对）。全部覆盖率、权重
分母、阈值秒数与可见性场按 540 重算：主扫描射线数
`1,040 × 540 × 15 = 8,424,000`；`0.05` ⇒ `27 tick / 5.4 s`；D3 指标域
`8 × 540 = 4,320` 对 / `64,800` 点。`s_0` 若进 D3，其 `8 × 15 = 120`
个采样点在工件中单列为**非指标样本**并单独计数。`s_2b` 的逐样本记录
新增"是否属于指标域"标志。

**3 — 把相机投影语义修复与谓词抽取拆成两个强停点。** 已拆。**`A0`**
（§9.2）= 诊断测量先行（COORD-005 诊断通道、零 ID，记录 `Render()`
时刻与 `FramePublished` 时刻两处的 `aspect` 与 `projectionMatrix`）→
运行时 `aspect = sensor.width / sensor.height` 显式绑定 + 投影/元数据
一致性测试 → **有界回溯审计表**（§9.2 `A0.3` 逐档案主张列出依赖量与
是否可能受影响，**不预先承诺"全部沿用"**，历史证据不自动重开，重开与否
由接受角色按 §4.6 裁定）。`A0` 明确标注为**主指标测量语义变化、须用户
明确授权**。**`A1`** 才是方案 P 的纯谓词内核抽取，候选 diff **不得含
任何投影参数改动**，附抽取前后逐点 bit-equal 的 no-op 证明。§6 条 10
禁止把 `A0` 或 `A0+A1` 称为 no-op。另新增一条本轮发现并登记的 parity
缺口：`Scene006SceneRig.cs:128` 的离线评估相机**显式**设了
`aspect = imageWidth/imageHeight`，运行时 `SensorCamera` 没有设——
只登记，不重开 SCENE-006 终态。

**4 — 主阈值必须在看见场结果前冻结。** 已改。
`δ_gap = δ_body = γ_min = 0.05` 升为 **primary contract**，标注"待用户
明确授权"，且必须在主扫描**之前**冻结；`4×4×4 = 64` 行降为 **secondary
sensitivity**，只在 primary 处分产出**之后**生成。§6 条 1 要求复核核对
两条时间次序（primary 冻结提交时间 < 主扫描开始时间；secondary 在
primary 处分之后）。并按要求写明蕴含关系：由
`C*(p) = μ{两者皆1} + G`、`C*(p_hover) = μ{两者皆1} + L` 得 `Δ = G − L`，
而 `L ≥ 0` ⇒ **`Δ ≤ G`**，所以 `δ_body = γ_min` 时 `Δ ≥ 0.05` 已蕴含
`G ≥ 0.05`；`γ_min` 在同值下是**显式归因/审计条款**（强制逐站点报告
`G` 与 `L`，使 BC-M34-4(b) 的"非零测度"可逐条核对，并让"`Δ` 大但 `G`
集中在单个建筑边缘"的脆弱见证可见），只有当接受角色冻结
`γ_min > δ_body` 时才成为独立绑定门。

**5 — 把最小锚点重定位放在全场扫描之前，且禁止按可见性调场。** 已改，
且按"独立的先行提案/裁定"执行：新开
**`P1-SCENE-007`**（`docs/proposals/P1-SCENE-007-minimal-anchor-
relocation.md`，随本批次提交），作为 Stage A；本提案的 Stage B 全场
扫描在它通过自身门之前**不启动**（§2 分阶段总览、§2 S4 处分 2 的去向）。
SCENE-007 的选点只用**最小位移 + 实测支撑 + 净空/走廊排除**的确定性
排序，**不读任何可见性量**，且该约束是机械可查的（依赖图 + 工件读取
审计，写进其复核范围，见本提案 §2 真值边界的"Stage A 反向边界"）。
不放宽任何安全合同。可比性后果按要求显式披露（§5）：**旧 M2 曲线保留
为旧几何下的历史证据但不再直接可比，M3′ 须在新几何上重新建立云台-only
baseline**，该披露同时进入 SCENE-007 提案、M3′ 实现提案与论文叙述。
原 Stage 2a 从 Stage C 的阶梯中移除。

**6 — 补全锚点端 trim 的高度证明。** 已改为含高差的闭式导出（§2 S1b）：
设 `Δy = Config.Anchor.y − supportY ≥ 0`（由 S1c **实测**，不再只作
报告），`sin θ_min = h_min / L_tether = 8/35 = 0.228571`（精确值），
充分条件为

```
Δy + d_trim · (h_min / L_tether) ≥ tether_radius
⇒ d_trim ≥ (tether_radius − Δy) · L_tether / h_min
```

`Δy = 0`（最保守）时 `d_trim ≥ 0.375 × 35 / 8 = 1.640625 m`，故预注册
`1.70 m` 成立并留 `0.059375 m` 余量；实测 `Δy = 0.2` 时不等式左端
`0.588571 ≥ 0.375`，余量更大。`Δy < 0`（锚点在支撑面以下）或 `Δy` 超
预注册容差 ⇒ S1c 直接 fail closed（`BLOCKED_ANCHOR_SUPPORT`），
**不得沿用 `1.70 m`**。`Δy`、`θ_min`、不等式两端与余量全部入工件
（§4 `workspace.json`、§6 条 4）。

**授权与边界（逐字核对账本）**：本轮新增账本条目
"2026-08-05 `P1-SCENE-005` — Acceptance round 2 三个退修方向的确认"，
用户原话"开始吧，接受"，范围记为**方向确认 + 起草授权，非最终变更**。
本稿据此按三个推荐方向撰写，但 `A0` 的主指标语义变更、primary 阈值取值
的生效、以及实际移动锚点/全场扫描**三者仍各自待用户明确授权**，文中
一律按"待授权、非既有基线"标注。本轮不主张 supersession，不主张实现、
Edit Mode/Play 执行（`A0.1` 诊断除外，且仍待授权）、ID 消耗、新
scenario 字节写入、Stage C 或 M1 关闭。提交后返回 Acceptance round 3，
连同 `P1-SCENE-007` 提案一并裁定。

---

## 16. Acceptance review decision — round 3

### Acceptance round 3 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

Revision 2 已关闭 round 2 的处分顺序、540 样本域、`A0`/`A1` 分批、
primary 先冻结与 `d_trim` 闭式五项主问题；`P1-SCENE-007` 作为独立先行
work item、且选点禁止读取可见性，也是正确的结构。但两份文档合起来仍有
三个不能按字面交给实现角色的缺口。

第一，SCENE-007 把锚点膨胀盘冻结为视觉半径 `0.6` 加新裕度 `0.3`，有效
半径仅 `0.9 m`；SCENE-003/004 的已接受锚点合同是名义半径 `1.0` 加净空
裕度 `0.5`，有效半径 `1.5 m`。本轮明确禁止放宽安全合同，故新稿当前是
未授权的收缩，不能以“更贴合视觉体”为由自动替代既有闭集净空门。

第二，`A0.1` 的当前诊断 Play 既无法证明历史运行当时的 Game View aspect，
也按 COORD-005 明确“不进证据链、不作为门判定依据”。它可以验证缺陷机制，
却不能支撑历史主张的保留或重归因。当前 `A0.3` 又只列出少数选中主张，
遗漏 RATE-001、TRACK-001/002 及其他使用 `C_geom`、真值框/IoU、
`C_track|geom`、`C_quality` 的档案，尚未形成有界而完整的影响域。

第三，Stage A 前在旧锚点上得到的 S0/D3/S1c 工件，在锚点移动后不能作为
Stage B 的保真或身份证据；且 SCENE-007 目前写成“候选工具与工件先复核，
用户 GO 后再写配置”，但未要求新增配置字节写入后的稳定候选再次接受停点
与独立复核。这样最终被 Stage B 消费的配置字节可能从未被复核。

Required revisions for round 4:

1. **恢复既有锚点安全包络。** `P1-SCENE-007` 默认沿用至少
   `anchor_nominal_radius_m = 1.0`、`clearance_margin_m = 0.5`、有效闭集
   半径 `1.5 m`，相切计违规；该半径同时用于支撑 strict-interior、道路/
   走廊间距和障碍净空。若构思角色坚持 `0.9 m`，须把它作为安全合同放宽
   单独请求用户授权，不能在本轮默认采用。冻结 exact allowlist 名称，并
   写清：只有本候选具名、实测且高度一致的支撑实例可按合同豁免；道路、
   其他支撑与未分类 root 均 fail closed。
2. **把 `A0` 回溯审计改成“未知历史 aspect”下的完整影响审计。** 当前
   诊断只可验证机制，不可推断旧运行值，也不得作为门证据。先机械枚举
   状态板、实现状态、Unity 日志、evidence/review 中所有消费
   `C_geom`、`C_track`、`C_track|geom`、真值框/IoU、`C_quality` 与 scouting
   truth 的主张；再逐条给出原始输入是否足够进行 4:3 反事实重放、可证明
   的敏感性范围、以及 `UNCHANGED / LIMITATION_ONLY / REATTRIBUTION_REQUIRED /
   UNRESOLVABLE`。无法恢复历史 aspect 时必须记为未知并保守归因，不得拿
   新诊断时的 Game View 代替。诊断 Play 结果与正式审计证据分栏存放。
3. **冻结 Stage A 前后工件的消费边界。** 旧锚点上的 S0/D3/S1c 运行只能
   作为诊断或“当前输入可达处分 2”的构造证明；SCENE-007 写入最终配置后，
   Stage B 必须对该配置及其新哈希完整重跑 S0-D1–D4、S1c、D3 fixture，
   不得复用旧锚点的通过结果。配置中的 `Δy` 合同须给出数值容差（建议
   `|Δy − 0.2| ≤ 0.05 m`），超界 fail closed，不能只写“超预注册容差”。
4. **补齐 SCENE-007 的双停点顺序。** 工具/候选工件先形成稳定候选，
   Acceptance 按 workflow §4.3.1 做实现写入归因后交独立 Review；Review
   通过后才向用户展示 `a*` 请求 GO。用户 GO 后写入新 scenario 配置，
   该 exact 配置、自 diff、哈希与消费方绑定形成第二个稳定候选，再经
   Acceptance 停点与独立 Review；只有第二轮通过后才允许
   `UT-P1-SCENE-007-001` 与 SCENE-005 Stage B。不得让“GO 后写入”的字节
   绕过复核。
5. **清除合同歧义与陈旧自述。** SCENE-007 把 `s=0.5`、`R_max=12`、
   `standoff=0.2`、`flatness_tol=0.05`、`corridor_standoff=0.5` 及 exact
   support allowlist 写进唯一冻结配置，删除“接受角色以后再选”的开放
   口径；删除重复的“输入”行。SCENE-005 删除
   `implementation-status.md` 仍把随机路线归 M1 的陈旧报告——该接受角色
   文件现已按 SCENE-002 更正为 M5。

Disposition:

- round 2 已解决的 540 样本、处分顺序、`Δ = G − L ≤ G`、`A0`/`A1`
  分批与 `d_trim` 公式不重开；
- `A0` 主指标语义修复、primary 三阈值 `0.05` 与实际锚点移动仍分别需要
  用户明确授权；2026-08-05 “开始吧，接受”继续只作方向确认与起草授权；
- 不授权实现、诊断 Play、Edit Mode、配置写入、锚点移动、全场扫描、
  session/run/profile/qual ID、Stage C 或 M1 关闭；
- 构思角色提交 SCENE-005 revision 3 与 SCENE-007 revision 1 后，一并
  返回 Acceptance round 4。

---

## 17. Revision 3 逐条回应（构思角色，2026-08-06）

**1 — 恢复既有锚点安全包络，冻结 exact allowlist 与豁免边界。** 已改，
并承认 revision 2 的 `0.6 + 0.3 = 0.9 m` 是按**视觉体**建模，把"物体
多大"与"承诺按多大审"混为一谈。两份文档现在共用同一份
SCENE-003/004 已接受合同（`p1-scene-004-anchor-placement.json`，语义见
`P1Scene004AnchorAudit.cs:63-68, 745-775`）：锚点盘
`1.0 + 0.5 = 1.5 m`、缆绳柱 `0.5 + 0.5 = 1.0 m`、悬停球
`1.0 + 0.5 = 1.5 m`，闭集相切计违规。本 work item 的三个有效半径表在
§2 S1a；exact allowlist 与豁免边界在 `P1-SCENE-007` §2.2/§2.3
（只有本候选具名、实测、高度一致的选中支撑实例可被豁免，道路/其他
支撑/未分类 root 全段 fail closed，并记录豁免区内最大穿入深度）。

**顺带执行用户 2026-08-06 选定的方向 A（round 3 未指出的同类收缩）**：
revision 2 沿用 `Scene006PathCertificate` 的缆绳有效半径 `0.375 m`，
而合同值是 `1.0 m`——收缩 `0.625 m`，比锚点盘那处更大。本稿恢复为
`1.0 + δ/2 = 1.125 m`。这是**收紧**（`1.125 > 0.375`，只会多拒站点、
不会多放行），因此不构成安全合同变更。连带后果已如实披露（§2 S1b）：
`d_trim` 从 `1.70 m` 增至 **`4.30 m`**，闭式为
`d_trim ≥ (1.125 − Δy) × 35/8`，在 S1c 冻结的 `Δy ∈ [0.15, 0.25]` 内
最坏需 `4.265625 m`；被豁免的头段因此变长，故新增"记录该实例在豁免区
内的最大穿入深度"这条可审计要求。`Scene006PathCertificate` 既有常量的
归因属接受角色裁量，本稿不预取。

**机体球是唯一**不**沿用合同值的实体，且方向相反（加严）**：合同的
`hover_nominal_radius_m = 1.0`（有效 `1.5 m`）**小于**运行时机体可见体
的外接半径 `sqrt(1.6² + 0.06²) = 1.601125 m`——合同的悬停球装不下它要
保护的对象。本 work item 审的是运动中的机体，故取 `1.61 + 0.5 + 0.125
= 2.235 m`。**加严不需要授权，收缩才需要**；该合同参数本身是否应修订
作为报告交接受角色（§10、`P1-SCENE-007` §10 OQ-3），本稿不改。

**2 — `A0` 改成"未知历史 aspect"下的完整影响审计。** 已重做（§9.2
`A0.3`），接受"诊断 Play 只能验证机制、不能推断历史值、不入证据链"
这一前提，分四步：

- **机械枚举**七个文档树 + `runtime/test-results/**` 中全部消费
  `C_geom`/`C_track`/`C_track|geom`/真值框/IoU/`visible_sample_fraction`/
  `target_bbox_area_px`/`target_center_error_px`/scouting truth 的主张，
  命中清单连哈希入工件；构思角色的非权威预扫是 **41 份文档 + 17 个
  归档 run 目录**，revision 2 漏掉的 RATE-001、TRACK-001/002、M0-001、
  TEST-001、SCENE-001 都在其中。
- **逐条判定**可复放性 / 敏感性范围 / 四值分类
  （`UNCHANGED` / `LIMITATION_ONLY` / `REATTRIBUTION_REQUIRED` /
  `UNRESOLVABLE`）。已核实：4:3 反事实重放需要**逐帧相机位姿 + 目标
  位姿**，而 `metrics.json` 只有聚合量、`evaluation_truth.jsonl` 只有
  目标世界 xz 与真值框，**都不含相机位姿**，故多数 run 预期不可复放。
- **两条可证明的结构性结论**用来收窄工作量：天底指向的 run 高度敏感
  （中心点判据下环线弧长占比 `1:1 → 0.174258`、`4:3 → 0.196844`、
  `16:10 → 0.214923`、`16:9 → 0.226991`、`21:9 → 0.264604`）；指向
  目标的 run 结构性不敏感（15 点最大横向离轴 `7.290070°`，保持全部
  采样点在锥内只需 `aspect ≥ 0.221576`）。**并明确写出一处不可分离
  性**：档案值 `0.219562724` 虽落在 16:10 与 16:9 之间，但 15 点判据
  本就比中心点判据宽松，"更宽的 Game View"与"更宽松的判据"从
  `metrics.json` 单独无法分离——这正是 round 3 结论的具体形态，不得
  据此反推历史 aspect。
- **硬性纪律**：不可恢复即记为未知并保守归因；诊断产物进
  `runtime/p1-scene-005/diagnostic/` 并标注不入证据链，审计表进
  `fidelity.json` 独立段；历史证据不自动重开，重开与否由接受角色按
  §4.6 裁定。

**3 — 冻结 Stage A 前后工件的消费边界。** 已加（§2 分阶段总览）：旧
锚点上的 S0（D1–D4）、D3 fixture 与 S1c 结果**只能**用作诊断与"当前
冻结输入可达处分 2"的构造证明；SCENE-007 批次 2 写入配置后，Stage B
**必须**对该配置及其新哈希完整重跑 S0-D1–D4、S1c 与 D3 fixture，
不得复用任何旧锚点的通过结果，两次运行的输入哈希分别入工件供复核核对。
`Δy` 容差按要求改为数值式 `Δy ≥ 0` 且 `|Δy − 0.2| ≤ 0.05 m`
（§2 S1c），不再写"超预注册容差"这种无数值口径。

**4 — 补齐 SCENE-007 的双停点顺序。** 细则写在 `P1-SCENE-007` §2.7，
本文档在 §2 分阶段总览与 §9.3 引用：批次 1（工具 + 候选工件，零字节
写入）→ 停点 1 + 独立 Review → 展示 `a*` 请求用户 GO → 写入配置 →
批次 2（exact 配置 + self-diff + 哈希 + 消费方绑定）→ 停点 2 + 第二轮
独立 Review。**`UT-P1-SCENE-007-001` 与本文档的 Stage B 都只在批次 2
的 Review 通过之后开始**——被 Stage B 消费的正是那批字节。

**5 — 清除合同歧义与陈旧自述。** SCENE-007 的六个参数与 exact
allowlist 已在该文档 §2.2 冻结、OQ-1–3 撤销、重复"输入"行删除、新增
"新 scenario 下 `427/779/101/0/0` 与哈希必须复现"的验收条件。本文档
撤回 revision 2 的陈旧报告——`implementation-status.md` 把随机路线归
M1 那条已由接受角色按 SCENE-002 更正为 M5（§5、§10 条 3）。

**授权与边界（逐字核对账本）**：本稿据 2026-08-06 条目"缆绳净空半径
按选项 A 恢复既有包络"撰写，该条记为**方向确认 + 起草授权，非最终
变更**。round 3 Disposition 重申的三项——`A0` 主指标语义修复、primary
三阈值 `0.05`、实际移动锚点——**仍各自待用户明确授权**，文中一律按
"待授权、非既有基线"标注。本稿不主张实现、诊断或正式 Play、Edit Mode、
ID 消耗、配置写入、全场扫描、Stage C 或 M1 关闭。提交后与
`P1-SCENE-007` revision 1 一并返回 Acceptance round 4。

---

## 18. Acceptance review decision — round 4

### Acceptance round 4 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

Revision 3 已关闭 round 3 的五项必修：锚点盘恢复为 `1.5 m` 闭集、
`A0` 不再用新诊断值代替未知历史 aspect、Stage A 前后工件不再混用、
SCENE-007 补成双停点/双复核，陈旧状态文字也已清除。但当前稿把两个
不同合同误写成同一个“既有缆绳合同”，而配套的 SCENE-007 又明确知道
悬停球小于真实机体却仍让该球签发候选净空证书；`A0.3` 的完整性也仍有
一处字面遗漏和一处未经证明的范围截断。这三项都不能留给实现角色解释。

第一，SCENE-003/004 的 `corridor_nominal 0.5 + clearance 0.5 = 1.0 m`
是**静止悬停构型的垂直系留走廊**；SCENE-006 §5.4/T4 另行接受的
**移动系留胶囊**是名义 `0.25 m + δ/2 = 0.375 m`。二者在 SCENE-006
§5.5/T5 中并列存在，不能把后者归因为“已知偏松的历史值”。用户选定
方向 A 允许继续起草 `1.125 m`，但账本明确它只是方向确认与起草授权，
不是最终安全目标变更。故 `1.125 m` 可以作为本 ID 新提出的、更严格的
移动系留包络，不能写成恢复既有移动系留合同，也不能写成“不需要授权”。

第二，SCENE-007 §2.4 已自行证明：有效 `1.5 m` 悬停球小于机体可见体
外接半径 `1.601125 m`。这不是可只披露不处置的注记。用已知装不下被
保护对象的球签发 `HOVER_ILLEGAL` 通过，会选出随后必被 SCENE-005
`2.235 m` 机体球淘汰的候选，并使“候选净空证书”名不副实。静态悬停
无需 `δ/2`，但至少应冻结 `body_nominal_radius_m = 1.61`、
`body_clearance_margin_m = 0.5`、有效半径 **`2.11 m`**；该安全目标加严
须作为待用户明确授权的新值，不得伪装成 SCENE-003/004 的逐字继承。

第三，round 3 明确点名 `C_quality`，revision 3 的机械检索词却仍未包含
`C_quality/c_quality`。同时，历史 aspect 已被承认为不可恢复，稿件却
无证据把敏感性范围截成 `aspect ∈ [1.0, 21:9]`。除非每条 run 有档案
元数据证明落在该区间，否则这只能是一个情景分析区间，不能是完整影响
范围；区间外必须给解析界，或把对应主张保守标为 `UNRESOLVABLE`。

Required revisions for round 5:

1. **纠正移动系留合同的来源与授权地位。** 保留用户方向 A 的候选值
   `tether_nominal_radius_m = 1.0`、`δ/2 = 0.125`、有效 `1.125 m` 及
   `d_trim = 4.30 m`，但逐处改写为“P1-SCENE-005 新提出的加严动态包络，
   待用户最终明确授权”。明确 SCENE-006 的 `0.375 m` 是其已接受的
   T4 动态合同，不得称作偏松错误；SCENE-003/004 的 `1.0 m` 只支撑
   静态垂直走廊合同。所有复用测试必须证明参数化实现能分别复现旧
   `0.375 m` 与新候选 `1.125 m`，不得重写 SCENE-006 的历史归因。
2. **让 SCENE-007 的悬停净空覆盖真实机体。** 在 SCENE-007 revision 2
   中冻结 `body_nominal_radius_m = 1.61`、净空裕度 `0.5`、静态有效半径
   `2.11 m`，并让候选判据、工件、构造性测试和失败统计全部使用同一值；
   SCENE-005 继续在移动路径上加 `δ/2` 得 `2.235 m`。删除“只报告、仍用
   1.5 m 放行”的路径，并把该加严明确列为**待用户授权**。若构思角色
   建议别的值，必须先给能完整包住 `1.601125 m` 机体且保留净空裕度的
   数值合同，不能把选择留给实现者。
3. **完成 `A0.3` 的字面全集与无界历史处置。** 检索词加入
   `C_quality/c_quality`，并机械断言 round 3 点名的全部字段都进入清单；
   `aspect ∈ [1, 21:9]` 只能标作情景区间。每条历史 run 若无元数据证明
   aspect 位于该区间，须给全部可行正 aspect 上的解析界，或分类为
   `UNRESOLVABLE`，不得用“真实窗口通常如此”补证。
4. **消除批次 1 的字节矛盾。** SCENE-007 批次 1 会新增冻结审计配置
   `config/p1-scene-007-relocation.json`，所以不得再写“零配置字节”。
   统一改为“零 scenario 几何字节、零 `anchor_world_m` 写入”；该审计
   配置、工具与候选工件均属于停点 1 的复核范围。

Disposition:

- round 3 已关闭的锚点 `1.5 m`、allowlist/豁免边界、Stage A 前后重跑、
  双停点顺序与陈旧状态清理不重开；
- `A0` 主指标语义修复、primary 三阈值 `0.05`、动态系留 `1.125 m`、
  静态机体 `2.11 m` 与实际锚点移动均仍需用户逐字授权；
- 不授权实现、诊断或正式 Play、Edit Mode、配置/场景字节写入、锚点移动、
  全场扫描、任何 ID/配额、Stage C 或 M1 关闭；
- 构思角色提交 SCENE-005 revision 4 与 SCENE-007 revision 2 后，一并
  返回 Acceptance round 5。
