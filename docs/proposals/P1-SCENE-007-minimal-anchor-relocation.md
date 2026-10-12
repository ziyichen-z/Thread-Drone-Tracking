# P1-SCENE-007 — 最小锚点重定位：把系留锚点移出目标车道走廊，选点不看任何可见性

Status: REVISION_REQUESTED
Author/role: 构思角色（ideation，历史名 Claude Fable）
Created: 2026-08-06
Last updated: 2026-08-06
Revision: 1（回应 Acceptance round 1 的 5 条必修项；逐条回应见 §12）

本 work item 由 `P1-SCENE-005` Acceptance round 2 §14 必修项 5 直接
派生："Revision 2 应把 Stage 2a 改为独立的先行提案/裁定：仅按最小位移、
实测支撑与净空的确定性排序选点，不读任何可见性结果；不放宽安全合同。"

**授权状态（逐字核对 `docs/authorizations.md`）**：2026-08-05 "开始吧，
接受"与 2026-08-06 "可以，按 A 起草…"都记为**方向确认 + 起草授权，
非最终变更**。本提案**不携带任何执行授权**：实际移动锚点、写入新
scenario 配置字节、执行 Edit Mode/Play、消耗任何 ID，都需要用户另行
明确授权 + 本 ID 自己的 Acceptance 裁定与两轮独立复核。

**与 `P1-SCENE-003` 的关系**：SCENE-003 是"把锚点移到环线中心"的
Option B，已 `BLOCKED_ANCHOR_PLACEMENT`（1,257/1,257 候选全部违反支撑
合约）。本 ID **不是**它的重启：目标不同（移出走廊，不是移到中心）、
判据不同（最小位移优先，不是几何居中），但**必须继承它的教训**（§3 H2）。
SCENE-003 的证据与终态原样保留，不因本 ID 改动。**其安全合同参数被本
稿完整继承，不作任何收缩**（§2.2，round 1 必修项 1）。

---

## 0. 修订索引（Acceptance round 1 → 本稿位置）

| round 1 必修项 | 本稿落点 | 实质变化 |
|---|---|---|
| 1 恢复 `1.5 m` 安全包络、相切违规、同一半径贯穿三类判据 | §2.2、§2.4 | 撤销 `0.6 + 0.3 = 0.9 m`，恢复合同的 `anchor_nominal 1.0 + clearance_margin 0.5 = 1.5 m`；缆绳柱按选项 A 一并恢复为 `0.5 + 0.5 = 1.0 m`；闭集相切计违规 |
| 2 冻结 exact support allowlist 与豁免边界 | §2.3、§2.5 | allowlist 逐字冻结为 `Natures_Grass Tile` / `Natures_Grass Tile Small`；只有本候选**具名、实测、高度一致**的选中支撑实例可获合同豁免，道路/其他支撑/未分类 root 全部 fail closed |
| 3 拆成两个稳定候选、两次停点、两次独立复核 | §2.7 | 候选工具与 `a*` 工件为第一停点；用户 GO 后写入的 exact 配置 + self-diff + 哈希为第二停点；第二轮 Review 通过前不得 Unity 目检、不得交 SCENE-005 |
| 4 冻结全部参数、删除实现前再解释空间、`Δy` 给数值容差 | §2.2、§2.6、§10 | 六个参数与 allowlist 全部写进唯一冻结配置；`\|Δy − 0.2\| ≤ 0.05 m` 数值容差、超界 fail closed；OQ-1–3 撤销 |
| 5 删除重复"输入"行、补路线合法性复现验收条件 | §4、§6 条 9 | §4 输入行去重；新增"新 scenario 下 427/779/101/0/0 与哈希必须复现"验收条件 |

**另一处本轮自行更正（用户 2026-08-06 选定方向 A）**：缆绳净空半径。
初稿在 §2.3 判据 6 写"垂直缆绳段以 `0.375 m` 膨胀"，那是从
`Scene006PathCertificate.TetherRadiusM` 继承的值，而已接受合同的缆绳柱
有效半径是 `1.0 m`——比锚点盘那处更大的收缩（`0.625 m`）。本稿恢复
为 `1.0 m`。

---

## 1. Problem and research value

### 1.1 由冻结字节确定的缺陷

`config/scenario.default.json`
（`sha256=f9c9205249aacf7487579ca42f727c766800cc329d0523ec82a96140564a2ce3`）
与 `TetheredScenarioBootstrap` 的字面量共同确定：

| 事实 | 数值 | 来源 |
|---|---|---|
| 锚点 | `(132.0, 0.2, 117.0)` | `anchor_world_m` |
| 北段路线中心线 | `z = 117.5` | `target.route_world_m[0..1]` |
| 锚点到中心线垂距 | `0.500000 m` | 上两行 |
| 走廊半宽 | `1.0 + 0.5 = 1.500000 m` | `route_corridor.target_half_width_m + clearance_margin_m` |
| 锚点视觉占据 | `z ∈ [116.4, 117.6]`、`y ∈ [0.0, 0.4]` | `CreateAnchor`：Cylinder，`localScale = (1.2, 0.2, 1.2)` |
| 目标车体占据（沿北段） | `z ∈ [116.5, 118.5]`、`y ∈ [0.2, 1.75]` | `TargetVisualFactory` body/roof |

⇒ **锚点在走廊内 1.000000 m，且目标车每圈从锚点标记里穿过去**
（水平重叠 1.1 m、垂直重叠 0.2 m）。

按已接受的锚点合同（§2.2）判，冲突比上表更严重：合同的锚点有效半径是
`1.5 m`，锚点中心距路线中心线只有 `0.5 m`，即锚点的**合同包络整体**
落在走廊内部。

现有审计结构上发现不了：`RouteCorridorAuditor` / `RoadSceneAuditor` 只
审计场景静态 root，而锚点视觉、无人机与目标是 bootstrap 显式排除的
runtime actor；锚点的 collider 也被 `Destroy`，所以它既不挡射线也不
触发净空审计。

### 1.2 为什么必须先做，而不是并行或事后

1. **它阻断 BC-M34-4(c)。** 章程要求"支撑/净空审计通过"，锚点在目标
   车道内部不满足。`P1-SCENE-005` 的处分表因此把它列为预检门（处分 2），
   在现字节上必然命中。
2. **在非法几何上扫场是浪费。** SCENE-005 Stage B 的主扫描是
   `1,040 × 540 × 15 = 8,424,000` 条射线；锚点一动，`p_hover` 与整个
   站点格的世界坐标全部平移，结果作废。
3. **它是场景合法性缺陷，不是指标问题。** `P1-SCENE-001` 因 taxi/
   street-light 重叠被判 Unity FAIL 是同一类；论文里一个立在行车道上、
   还被车反复穿过的地面锚点会被直接质疑。

### 1.3 研究价值边界（诚实说明）

本 work item **不产生任何研究主张**。它是一次场景合法性修复，价值在于
让下游的 `C_geom` 缺口归因不被一个显而易见的建模缺陷污染。它同时产生
一项**代价**：几何变了，旧 M2 曲线不再直接可比（§5）。

---

## 2. Proposed behavior

### 2.1 硬性边界：选点不得看任何可见性量

**这是本提案的第一条约束，也是它能先行的唯一理由。** 候选排序与判定
只用几何与实测支撑，**不读** `C_geom`、`C_frustum`、`C*`、`U_occ`、
遮挡计数或 `P1-SCENE-005` 的任何工件。该约束机械可查：

- 选点工具的程序集**不得**引用任何可见性/评估模块
  （`CoverageEvaluator`、`Scene006Visibility`、`Scene006Evaluation`、
  `P1Scene005*` 的可见性部分）；
- 工件里记录该工具读取的**全部输入文件路径与哈希**，复核核对其中不含
  任何可见性工件；
- 依赖图检查与输入清单审计写进本 ID 的复核范围。

违反即 `SELECTION_CONTAMINATED_BY_VISIBILITY`，整批作废重做。

### 2.2 继承的安全包络（round 1 必修项 1 + 4：逐字冻结，不得收缩）

全部取自已接受的 `config/p1-scene-003-anchor-placement.json` 与
`config/p1-scene-004-anchor-placement.json`（两份同值），语义取自
`Assets/TetheredTracking/Scripts/P1Scene004AnchorAudit.cs:63-68, 745-775`：

| 实体 | 名义半径 | 净空裕度 | **有效半径** | 竖直范围 |
|---|---|---|---|---|
| 锚点柱 | `anchor_nominal_radius_m = 1.0` | `clearance_margin_m = 0.5` | **`1.5 m`** | `[groundY, groundY + 0.5]` |
| 缆绳柱 | `corridor_nominal_radius_m = 0.5` | `0.5` | **`1.0 m`** | `[groundY, hoverY]` |
| 悬停球 | `hover_nominal_radius_m = 1.0` | `0.5` | **`1.5 m`** | 以 `p_hover` 为心 |

- **闭集判定**：`distance <= radius + 1e-5` 即违规，**相切计违规**
  （与 `P1Scene004AnchorAudit` 的 `GeometryEpsilon` 约定一致）。
- **同一锚点半径贯穿三类判据**：支撑面 strict-interior、道路/走廊
  间距、障碍净空全部用 `1.5 m`，不得对不同判据用不同尺度。
- 初稿的 `0.6 + 0.3 = 0.9 m` **已撤销**。本稿不请求任何安全合同放宽。

**冻结参数（全部写进唯一配置 `config/p1-scene-007-relocation.json`，
实现前无再解释空间）**

| 参数 | 冻结值 | 来源/依据 |
|---|---|---|
| `anchor_nominal_radius_m` | `1.0` | 继承 SCENE-003/004 |
| `hover_nominal_radius_m` | `1.0` | 继承 |
| `corridor_nominal_radius_m` | `0.5` | 继承 |
| `clearance_margin_m` | `0.5` | 继承 |
| `support_height_tolerance_m` | `0.05` | 继承 |
| `support_surface_allowlist` | `["Natures_Grass Tile", "Natures_Grass Tile Small"]` | 继承，逐字 |
| `lattice_step_m` | `0.5` | 继承（= SCENE-003/004 的 `lattice_step_m`） |
| `search_radius_m` | `12.0` | 本 ID 新值；SCENE-003/004 为 `10.0`。**这是搜索域扩大，不是安全参数放宽**——它只让更多候选被**审**，每个候选仍按同一包络判 |
| `standoff_m` | `0.2` | `a_y := supportY + standoff`，等于现锚点相对其名义地面的抬升 |
| `delta_y_tolerance_m` | `0.05`，即 `\|Δy − 0.2\| ≤ 0.05` | round 1 必修项 4；数值容差，超界 fail closed |
| `flatness_tol_m` | `0.05` | 盘内高程起伏上限 |
| `corridor_standoff_m` | `0.5` | 锚点有效盘与走廊棱柱的额外水平间距 |

### 2.3 支撑豁免的精确边界（round 1 必修项 2）

障碍集合按 SCENE-006 的做法取**完整实例集**（含路面与支撑），因此需要
一条明确的豁免条款，且该条款必须窄：

- **只有**本候选**具名的、实测的、高度一致的**选中支撑实例，可以在
  缆绳柱的头段 `[0, d_trim]` 内被忽略；
- **道路面、其他支撑实例、未分类 root 全部 fail closed**，全段查询，
  无任何豁免；
- 被绑定的支撑实例若不在障碍集合中，直接抛错（不得静默豁免一个不存在
  的实例）；
- 工件必须记录该实例在被豁免区段内**穿入缆绳柱的最大深度**，使复核者
  看得见豁免掉的究竟是什么。

**`d_trim` 的闭式导出（垂直缆绳情形）**：SCENE-007 只判 `p_hover`，
机体静止，缆绳竖直（仰角 `90°`）。设 `Δy = a_y − supportY`，充分条件为
`Δy + d_trim · sin(90°) ≥ corridor 有效半径`，即

```
d_trim ≥ corridor_effective_radius − Δy = 1.0 − Δy
```

在 `Δy ∈ [0.15, 0.25]` 的冻结容差内，右端 ≤ `0.85 m`。预注册
`d_trim_m = 1.00`，并要求工件用**实测** `Δy` 复算该不等式；不成立即
`TRIM_PROOF_FAILED`。（`P1-SCENE-005` 的机体会移动、缆绳倾斜，其
`d_trim` 由该 work item 按带下界另行导出，见其 §2 S1b。）

> **与 SCENE-003/004 的机制差异（须写明，避免被误读成放宽）**：
> SCENE-003/004 的障碍集合是 `RoadObstacleFootprint`，**不含**支撑面，
> 所以它们不需要豁免条款。本 ID 与 SCENE-005/006 一样使用完整实例集
> （更 fail-closed），代价是必须显式豁免锚点脚下那一个实例。两者的
> 净空半径相同，**本 ID 的障碍集合是更大的那个**。

### 2.4 候选集合与逐候选判据（按序，命中即拒，记录首个拒绝原因）

```
A_cand = { (a_x + s·i, ·, a_z + s·j) : i, j ∈ Z,
           0 < sqrt((s·i)² + (s·j)²) ≤ search_radius_m }
```

`a = (132.0, ·, 117.0)`；候选的 **y 不是自由变量**：
`a_y := supportY(候选) + standoff_m`。这直接对应 SCENE-003 的失败根因
——那一轮把 `0.2` 当成**假设**，而草地瓦片实测支撑面是 `0.0000013 m`，
`|0.2 − 0.0000013| = 0.2 > 0.05`，1,257 个候选全灭。本轮 `a_y` 由
**实测**导出，不是假设。

| # | 判据（全部用 §2.2 的有效半径，闭集相切违规） | 拒绝码 |
|---|---|---|
| 1 | **实测支撑**：候选 XZ 处存在支撑面；`supportY` 由实测取得（非估计）；支撑实例可具名且在冻结 allowlist 内 | `NO_MEASURED_SUPPORT` |
| 2 | **支撑面片完整性**：锚点有效盘（**`1.5 m`**）在支撑面片内部（strict interior），且面片在盘内高程起伏 ≤ `flatness_tol_m` | `SUPPORT_PATCH_INSUFFICIENT` |
| 3 | **`Δy` 容差**：`\|Δy − 0.2\| ≤ 0.05 m`，`Δy = a_y − supportY ≥ 0` | `DELTA_Y_OUT_OF_TOLERANCE` |
| 4 | **走廊排除**：锚点有效盘（`1.5 m`）与冻结路线走廊棱柱（半宽 `1.5 m`、`target_bottom_offset_m = 0.0`、`target_height_m = 1.55`、`vertical_clearance_margin_m = 0.5`）的水平间距 ≥ `corridor_standoff_m = 0.5` ⇒ 锚点中心距路线中心线 ≥ `1.5 + 0.5 + 1.5 = 3.5 m` | `CORRIDOR_CONFLICT` |
| 5 | **道路间距**：锚点有效盘不落在沥青带上，且与沥青边界间距 ≥ `corridor_standoff_m`——锚点不得立在车道上 | `ON_ROAD_SURFACE` |
| 6 | **障碍净空**：锚点有效盘（`1.5 m`）与全部场景障碍（沿用 SCENE-002 的 779 障碍 / 101 车辆审计集合）不相交 | `ANCHOR_CLEARANCE` |
| 7 | **缆绳柱净空**：`[groundY, hoverY]` 的 **`1.0 m`** 有效半径柱与完整实例集不相交，仅按 §2.3 豁免具名实测支撑实例的头段 | `TETHER_CLEARANCE` |
| 8 | **悬停球净空**：`p_hover = (a_x, a_y + 25.0, a_z)` 处 **`1.5 m`** 有效半径球与完整实例集不相交 | `HOVER_ILLEGAL` |
| 9 | **路线可达性（纯几何，非可见性）**：`min_s dist_xz(s, a) ≤ sqrt(35² − 8²) = 34.073450 m`。**这只排除"机体连一点路线都够不到"的退化锚点，不是覆盖率判据** | `ROUTE_UNREACHABLE` |

> **`hover_nominal_radius_m = 1.0` 的一处报告（不自行处置）**：运行时
> 机体可见体的外接半径是 `sqrt(1.6² + 0.06²) = 1.601125 m`
> （`AddDroneVisual` 四条臂 `localPosition = direction*0.8` + 半长 `0.8`），
> 大于合同的名义半径 `1.0`，也大于有效半径 `1.5` 吗——否，`1.5 > 1.601`
> 不成立：**有效半径 `1.5 m` 小于机体自身的外接半径 `1.601125 m`**。
> 即已接受合同的悬停球装不下它要保护的对象。本 ID **沿用合同值不自行
> 加严**（加严同样是改合同），只把该发现登记给接受角色；
> `P1-SCENE-005` 因为要审的是运动中的机体，已按导出值取
> `1.61 + 0.5 + 0.125 = 2.235 m`（**大于**合同值，属加严方向，见其
> §2 S1a）。两者的差异及其理由必须在两份文档中同时可见。

### 2.5 确定性排序与选择

全部通过 1–9 的候选按

```
(位移 sqrt((s·i)² + (s·j)²) 升序, 然后 (x, z) 字典序)
```

排序，取**第一个**为 `a*`。位移相同时由字典序唯一定序，无随机、无人工
挑选。工件写出**全部**通过候选（不只 `a*`），以及每个被拒候选的首个
拒绝码，使选择可被独立复算。

### 2.6 处分表（预注册，按序）

| # | 条件 | 处分 | 去向 |
|---|---|---|---|
| 0 | 输入哈希不符，或工具读取了任何可见性工件 | `SELECTION_CONTAMINATED_BY_VISIBILITY` / `BLOCKED_INPUT_IDENTITY` | 实现角色 |
| 1 | 通过候选为空 | `BLOCKED_ANCHOR_RELOCATION_V2` | 构思角色（重新设计；**不得**通过放宽 §2.2 任一半径或容差来制造通过） |
| 2 | 通过候选非空 | `ANCHOR_CANDIDATE_SELECTED`（**工具态止于此**） | 第一停点 + 独立 Review → 用户 GO |

处分由确定性函数从工件计算，不允许人工填写 verdict。

### 2.7 两个稳定候选、两次停点、两次独立复核（round 1 必修项 3）

```
批次 1  工具 + 候选工件（零配置字节写入）
        → Acceptance 按 workflow §4.3.1 做实现写入归因并确认停点 1
        → 独立 Review（worktree）
        → 通过后才向用户展示 a* 并请求 GO
用户 GO → 写入 config/scenario.p1-scene-007.json
批次 2  exact 配置 + one-file self-diff + 哈希 + 消费方绑定
        → Acceptance 停点 2
        → 独立 Review
        → 通过后才允许 UT-P1-SCENE-007-001 与 SCENE-005 Stage B
```

**"GO 后写入"的字节不得绕过复核**：最终被 Stage B 消费的正是批次 2 的
配置字节，它必须自己经过一次完整的独立复核。第二轮 Review 通过之前，
不得做 Unity 目检，也不得把配置交给 SCENE-005。

### 2.8 字节与命名边界

- **不覆盖任何既有配置字节。** 新锚点写入**新文件**
  `config/scenario.p1-scene-007.json`（新 `scenario_id`），
  `config/scenario.default.json` 与 `scenario.scene-validation.json`
  原样保留，其哈希链与所有引用它们的档案证据不受影响。
- 新配置除 `scenario_id` 与 `anchor_world_m` 外，与
  `scenario.default.json` **逐键相同**（路线、光学、目标、
  `scene_adjustments`、`evaluation` 全部不动），并由一份 one-file
  self-diff 工件证明这一点。

---

## 3. 算法/行为假设（可证伪）

- **H1（存在合法候选）**：`search_radius_m = 12`、`lattice_step_m = 0.5`
  的候选集合内存在通过 1–9 的点。**证伪**：全候选被拒 → 处分 1。
  **本轮的诚实提醒**：把锚点盘从 `0.9` 恢复到 `1.5 m`、并新增判据 5/7/8
  之后，通过率必然低于初稿，H1 的风险随之上升。这是恢复安全包络的
  代价，不构成放宽包络的理由。
- **H2（实测支撑是可得的，且不重蹈 SCENE-003）**：SCENE-003 的
  1,257/1,257 全灭源于把 `a_y = 0.2` 当作**假设**去和实测支撑高度比。
  本轮把 `a_y` 定义为 `supportY + standoff`，所以该比较在构造上恒成立，
  失败只可能来自"该 XZ 处根本没有可具名的 allowlist 支撑面"或"面片
  不够平/不够大装下 `1.5 m` 盘"。**证伪**：大量候选报
  `NO_MEASURED_SUPPORT` 或 `SUPPORT_PATCH_INSUFFICIENT` → 说明支撑
  实测机制在该区域不适用，回构思角色而不是放宽容差。
- **H3（最小位移足以解决问题）**：判据 4 要求锚点中心距路线中心线
  ≥ `3.5 m`，现锚点是 `0.5 m`，故最小位移至少 `3.0 m`。**证伪**：`a*`
  的位移接近 `search_radius_m`，说明近邻区域整体不合法，须重新考虑是改
  锚点还是改路线。
- **H4（不看可见性不会选出退化锚点）**：判据 9 只排除"够不到任何路线
  点"的退化情形。**已知的诚实局限**：本 ID **不保证**新锚点在覆盖率
  意义上不劣于旧锚点——那需要看可见性，而看可见性正是本 ID 被禁止做的
  事。若 `P1-SCENE-005` Stage B 在新锚点上判出处分 5/6，处置走
  SCENE-005 的 Stage C，**不得**回头按可见性重选锚点（那会把整条链
  变成按结果调场）。

---

## 4. Inputs, outputs, and affected interfaces

**输入**：`config/scenario.default.json`（`f9c92052…2ce3`）、
`config/road_data.json`（`111e0759…1894`）、城市场景资产、
SCENE-003/004 已实现的支撑面实测与 strict-interior 机制、SCENE-002 的
走廊/障碍/车辆审计集合、新增冻结配置
`config/p1-scene-007-relocation.json`。**不含任何可见性工件。**

**输出**（新目录 `runtime/p1-scene-007/`）

| 工件 | schema | 内容 | 批次 |
|---|---|---|---|
| `candidates.json` | `p1-scene-007-candidates/v1` | 全候选、逐候选 9 项判定与首个拒绝码、实测 `supportY`/分类/面片、排序与 `a*` | 1 |
| `selection.json` | `p1-scene-007-selection/v1` | `a*`、位移、`Δy`、`d_trim` 不等式两端与豁免区最大穿入深度、`p_hover` 证书、输入文件清单与哈希 | 1 |
| `config/scenario.p1-scene-007.json` | `tethered-scenario/v1` | **仅在用户 GO 之后**写入 | 2 |
| `config-selfdiff.json` | `p1-scene-007-selfdiff/v1` | 与 `scenario.default.json` 的逐键 diff（应只有 `scenario_id` 与 `anchor_world_m`）+ 双方哈希 | 2 |
| `route-legality-recheck.json` | `p1-scene-007-route-recheck/v1` | 新 scenario 下重跑的路线合法性审计计数与哈希 | 2 |
| `docs/evidence/P1-SCENE-007-relocation.md` | — | 命令、退出码、工件哈希、耗时、处分 | 1+2 |

**受影响接口：运行时代码零改动。** 不改帧包/控制协议、坐标或时间语义、
主指标定义、安全约束或模型决策逻辑。改的是**场景几何配置**，因此需要
两轮独立复核与一次用户 Unity 验证（`UT-P1-SCENE-007-001`：Edit Mode
生成 + 非 Play 目检新锚点落点与场景合理性，沿用 SCENE-006 BC-B2-8 的
目检形式；**只在批次 2 的 Review 通过之后**）。

---

## 5. Compatibility with the current v0.3.16 design

- 四指标定义、三条消融轴、里程碑表全部零改动。
- §6 "已接受的场景合法性门（`P1-SCENE-001`）"与"道路合法路线门
  （`P1-SCENE-002`）"不放宽：本 ID 只移动锚点，路线字节与全部既有
  合法性判据原样保留并须在新 scenario 下复现（§6 条 9）。
- **安全包络零收缩**：§2.2 的三组半径、容差与 allowlist 全部逐字继承
  SCENE-003/004 的已接受合同。本 ID 不请求任何放宽。
- **可比性后果（硬性披露）**：移动锚点改变几何，**旧 M2 曲线保留为旧
  几何下的历史证据，但不再与新几何直接可比**；M3′ 须在新几何上重新
  建立云台-only baseline。该句必须同时出现在本 ID 的证据文档、
  `P1-SCENE-005` §5、M3′ 实现提案与论文叙述中。
- 受影响的既有档案证据（**只登记，不重开**）：`UT-P1-SCENE-002-001`
  attempt 3 的 `C_geom = 0.219562724`、RATE-002 的三次 r20-follow、
  `P1-M3M4-SCOPE-002` 的 `0.7353`/`0.0000`/`70.113398°`——它们都以旧
  锚点为基准，新几何上须重算，旧值作为旧几何的历史记录保留。
  `P1-DETECT-001` qual-3 与 `P1-SCENE-004` benign 载体在**另一个场景**
  上，不受本 ID 影响。
- CLAUDE.md 阶段边界规则：本 ID 不改研究主张、阶段边界、主指标或硬件
  目标；它是 `P1-M3M4-SCOPE-001` BC-M34-4(c) 的前置修复。

---

## 6. Acceptance criteria（逐条可证伪）

1. **安全包络逐字继承**：冻结配置的
   `anchor_nominal_radius_m/hover_nominal_radius_m/corridor_nominal_radius_m/
   clearance_margin_m/support_height_tolerance_m/support_surface_allowlist`
   与 `p1-scene-004-anchor-placement.json` 逐字相同；闭集相切计违规有
   构造性测试。
2. **选点不含可见性**：工具程序集依赖图不含任何可见性/评估模块；
   `selection.json` 的输入文件清单不含任何可见性工件；复核逐条核对。
3. **参数先于测量冻结、无再解释空间**：§2.2 表中十二项全部入库，提案与
   配置逐字一致；文中不存在"由接受角色以后再选"的开放口径。
4. **支撑是实测的**：每个候选的 `supportY` 与分类来自实测，工件记录
   具名支撑实例；**不存在任何以假设高度参与判定的路径**。
5. **`a_y` 与 `Δy`**：`a_y = supportY(a*) + 0.2` 可逐位复算；
   `|Δy − 0.2| ≤ 0.05` 成立，超界 fail closed。
6. **豁免边界**：只有本候选具名、实测、高度一致的选中支撑实例在
   `[0, d_trim]` 内被忽略；道路、其他支撑、未分类 root 全段 fail closed；
   工件记录豁免区内的最大穿入深度；`d_trim ≥ 1.0 − Δy` 用实测 `Δy`
   复算成立。
7. **九项判据齐备**：`a*` 的锚点盘、缆绳柱、悬停球三项净空证书，以及
   走廊/道路间距、支撑 strict-interior、`Δy`、路线可达性判定全部入工件。
8. **确定性可复算**：给定工件字节，排序与 `a*` 复跑一致；全候选与逐条
   拒绝码齐备；处分由确定性函数产出。
9. **新 scenario 下路线合法性复现**：批次 2 在新配置上重跑既有审计，
   `route_sample_count = 427`、`audited_obstacle_count = 779`、
   车辆 `101`、违规 `0/0` 与 `road_data` 哈希必须复现；任一不符即
   fail closed。
10. **字节边界**：既有 `config/*.json` 字节与哈希零改动；新配置为新文件
    新 `scenario_id`，且除 `scenario_id` 与 `anchor_world_m` 外与
    `scenario.default.json` 逐键相同（self-diff 工件证明）。
11. **两停点两复核**：批次 1 与批次 2 各自形成稳定候选、各自经 Acceptance
    停点与独立 Review；`UT-P1-SCENE-007-001` 与 SCENE-005 Stage B 只在
    批次 2 的 Review 通过之后开始。
12. **用户 GO 门**：工具态止于 `ANCHOR_CANDIDATE_SELECTED`；未获用户
    逐字授权前不写入新 scenario 字节。
13. **可比性披露在场**：§5 的可比性句逐字出现在证据文档中。
14. **不越权**：不改设计文档、不关闭任何里程碑、不宣称任何用户授权、
    不启动 `P1-SCENE-005` Stage B、不放宽 §2.2 任一参数。

---

## 7. Baselines and ablations

本 work item 不产生研究主张，因此没有基线与消融。它唯一的"对照"是
**旧锚点**：工件必须并列记录旧锚点与 `a*` 的位移、`supportY`、分类、
走廊间距、三项净空证书结果，使"改了什么、改了多少"一目了然。

`P1-SCENE-003` 的 `BLOCKED_ANCHOR_PLACEMENT` 与其 1,257/1,257 拒绝
证据保留为**负结果对照**：它证明"按几何居中 + 假设高度"的选法在本场景
行不通，本 ID 的两处改动（最小位移优先、`a_y` 由实测导出）正是对它的
直接回应——而**不是**通过放宽合同来制造通过。

---

## 8. Failure modes and resource risks

- **处分 1（全候选被拒）**：SCENE-003 的先例说明这不是假想风险，且本轮
  恢复 `1.5 m` 包络后风险更高（§3 H1）。处置是回构思角色重新设计，
  **不是**放宽 `flatness_tol`、`corridor_standoff` 或任一半径。
- **可比性损失**：确定发生，不是风险而是代价。缓解是显式披露 + 旧曲线
  完整保留 + M3′ 在新几何上重建 baseline。
- **锚点搬到不合理的位置**：判据 5（不得立在沥青带上）与判据 9（路线
  可达性）是仅有的两道"合理性"约束，且都是纯几何的。**残余风险由用户
  的非 Play 目检兜底**（验收条件 11），这正是 COORD-005 人眼保真检查
  存在的理由。
- **"GO 后写入"的字节绕过复核**：初稿的真实缺口。缓解是 §2.7 的双停点。
- **按可见性调场的诱惑**：最危险的科学风险。缓解是 §2.1 的机械可查
  约束 + §3 H4 的显式禁令。
- **资源**：候选规模上界 `π·12²/0.5² ≈ 1,810` 个格点，逐候选是几何与
  少量射线。零 Play 测量、零 session/run ID、零采集预算；两轮 Review
  之后一次用户 Edit Mode + 非 Play 目检。

---

## 9. Suggested implementation scope（建议，不强制）

1. `Assets/TetheredTracking/Editor/P1Scene007AnchorRelocation.cs`：候选
   生成、实测支撑、9 项判据、排序与工件落盘（复用
   `P1Scene003AnchorAudit` / `P1Scene004AnchorAudit` 已实现的支撑面
   实测、strict-interior 与三实体净空原语，不复制）；
2. `controller/scene007_relocation.py`：确定性处分函数与报告合成
   （形态参照 `controller/rate3_decision.py`）；
3. `tests/test_scene007_relocation.py` + EditMode 测试：9 项判据各自的
   构造性正反例、**闭集相切必须违规**、排序确定性、处分表 0–2 全覆盖、
   **依赖图/输入清单不含可见性**的机械检查、`d_trim` 不等式与豁免深度、
   `Δy` 容差边界、self-diff 正确性、新 scenario 路线复现计数；
4. `config/p1-scene-007-relocation.json` 冻结参数（§2.2 十二项）；
5. `docs/evidence/P1-SCENE-007-relocation.md`。

批次划分见 §2.7：批次 1 零字节写入，批次 2 才写配置。

---

## 10. Open questions

初稿的 OQ-1–3（`R_max`/`s` 取值、`standoff` 是否保持、allowlist 是否
沿用）按 round 1 必修项 4 **全部撤销**——它们已在 §2.2 冻结，实现前
没有再解释空间。

- **OQ-1（保留，原 OQ-4）**：若 `a*` 的位移使锚点跨到路线**外侧**
  （环线之外），是否可接受。构思角色认为可以——判据 9 已保证路线可达，
  而"锚点必须在环内"从未是任何已接受合同的要求；但这会明显改变几何，
  建议由用户在批次 2 的目检时一并确认。
- **OQ-2（保留，原 OQ-5）**：本 ID 与 `P1-SCENE-003` 是否应合并记账。
  构思角色建议**不合并**：SCENE-003 的终态与证据保留原样，本 ID 是
  独立的、目标不同的 work item，合并会让 SCENE-003 的负结果记录失真。
  Acceptance round 1 Disposition 已确认不合并。
- **OQ-3（新）**：`hover_nominal_radius_m = 1.0`（有效 `1.5 m`）小于
  运行时机体外接半径 `1.601125 m`，见 §2.4 的报告框。本 ID 沿用合同值
  不自行加严；是否要修订该合同参数，属接受角色与用户的裁量。

---

## 11. Acceptance review decision

### Acceptance round 1 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

独立先行、按最小位移排序且禁止读取可见性结果的方向成立；实测支撑导出
`a_y` 也正确吸收了 SCENE-003 的负结果。但 `0.6 + 0.3 = 0.9 m` 的锚点
膨胀盘小于 SCENE-003/004 已接受的 `1.0 + 0.5 = 1.5 m`，构成未经授权的
安全包络收缩。候选工件 Review 通过后再由用户 GO 写配置的流程，也没有
覆盖 GO 后新增配置字节的独立复核。

Required revisions:

1. 沿用至少 `1.0 + 0.5 = 1.5 m` 的闭集有效半径并让相切违规；同一半径
   用于 support strict-interior、走廊/道路间距和障碍净空。若要用
   `0.9 m`，先请求用户单独授权安全合同放宽。
2. 冻结 exact support allowlist；只允许具名、实测、高度一致的选中支撑
   实例获得合同规定的豁免，其他支撑、道路、未分类 root 全部 fail closed。
3. 把交付拆成两个稳定候选：工具 + `a*` 工件先停点/Review；用户 GO 后的
   exact scenario 配置 + self-diff + 哈希绑定再停点/Review。第二轮 Review
   通过前不得 Unity 目检，也不得交给 SCENE-005。
4. 冻结 `s=0.5 m`、`R_max=12 m`、`standoff=0.2 m`、
   `flatness_tol=0.05 m`、`corridor_standoff=0.5 m` 和 exact allowlist，
   删除 OQ-1–3 的实现前再解释空间；给 `Δy` 冻结数值容差并 fail closed。
5. 删除 §4 重复的“输入”行；补一条新 scenario 下既有路线合法性审计
   `CLEAR` 计数/哈希必须复现的验收条件。

Disposition:

- 不合并回 SCENE-003；其 `BLOCKED_ANCHOR_PLACEMENT` 终态保持不变；
- 不授权工具实现、候选评估、Edit Mode/Play、新配置字节或锚点移动；
- revision 1 与 SCENE-005 revision 3 一并返回 Acceptance round 4。

---

## 12. Revision 1 逐条回应（构思角色，2026-08-06）

**1 — 恢复既有锚点安全包络。** 已恢复，且承认初稿的
`0.6 + 0.3 = 0.9 m` 是按**视觉体**建模，把"物体多大"和"承诺按多大审"
搞混了。§2.2 逐字继承 `p1-scene-004-anchor-placement.json` 的
`anchor_nominal 1.0 + clearance_margin 0.5 = 1.5 m`，并按
`P1Scene004AnchorAudit.cs:745-775` 的语义补齐另外两个实体：缆绳柱
`0.5 + 0.5 = 1.0 m`、悬停球 `1.0 + 0.5 = 1.5 m`；闭集相切计违规
（`<= r + 1e-5`），并有构造性测试。同一 `1.5 m` 锚点半径贯穿支撑
strict-interior、道路/走廊间距与障碍净空三类判据。本稿**不请求任何
安全合同放宽**。

**顺带修正一处 round 1 未指出、但同类且更大的收缩（用户 2026-08-06
选定方向 A）**：初稿判据 6 写"垂直缆绳段以 `0.375 m` 膨胀"，那是从
`Scene006PathCertificate.TetherRadiusM` 继承的值，而合同的缆绳柱有效
半径是 `1.0 m`——收缩 `0.625 m`，比锚点盘那处更大。本稿恢复为 `1.0 m`
（§2.2、§2.4 判据 7）。该方向是**收紧**（只会多拒候选，不会多放行）。
`Scene006PathCertificate` 既有常量的归因属接受角色裁量，本稿不预取。

**2 — 冻结 exact support allowlist 与豁免边界。** allowlist 逐字冻结为
`["Natures_Grass Tile", "Natures_Grass Tile Small"]`（§2.2）。§2.3 把
豁免收窄到只有**本候选具名的、实测的、高度一致的**选中支撑实例，且只
在缆绳柱头段 `[0, d_trim]` 内；道路面、其他支撑实例、未分类 root 全部
全段 fail closed；被绑定实例不在障碍集合中直接抛错。新增一条本轮自加的
可审计要求：工件必须记录该实例在豁免区内**穿入缆绳柱的最大深度**，让
复核者看得见豁免掉的是什么。`d_trim` 改为闭式 `d_trim ≥ 1.0 − Δy`
（垂直缆绳，`sin 90° = 1`），预注册 `1.00 m`，用实测 `Δy` 复算。
另在 §2.3 写明与 SCENE-003/004 的机制差异：那两轮的障碍集合不含支撑面
所以不需要豁免条款，本 ID 用完整实例集（更 fail-closed），豁免是这个
更强集合的必要配套，**不是**净空半径的放宽。

**3 — 拆成两个稳定候选、两次停点、两次独立复核。** 已拆（§2.7）。
批次 1 = 工具 + 候选工件（零配置字节写入）→ Acceptance 按 §4.3.1 做
实现写入归因并确认停点 1 → 独立 Review → 通过后才向用户展示 `a*` 请求
GO。用户 GO → 写入配置。批次 2 = exact 配置 + one-file self-diff + 哈希
+ 消费方绑定 → 停点 2 → 独立 Review。**`UT-P1-SCENE-007-001` 与
SCENE-005 Stage B 只在批次 2 的 Review 通过之后开始**，"GO 后写入"的
字节不再绕过复核（验收条件 11、12）。

**4 — 冻结全部参数、删除实现前再解释空间、`Δy` 给数值容差。** §2.2 的
十二项参数全部写进唯一冻结配置 `config/p1-scene-007-relocation.json`：
三组名义半径与 `clearance_margin_m`、`support_height_tolerance_m`、
exact allowlist、`lattice_step_m = 0.5`、`search_radius_m = 12.0`、
`standoff_m = 0.2`、`delta_y_tolerance_m = 0.05`、
`flatness_tol_m = 0.05`、`corridor_standoff_m = 0.5`。`Δy` 容差改为
数值形式 `|Δy − 0.2| ≤ 0.05 m`，超界 `DELTA_Y_OUT_OF_TOLERANCE`
fail closed（§2.4 判据 3）。初稿的 OQ-1–3 全部撤销（§10）。
`search_radius_m = 12.0` 与 SCENE-003/004 的 `lattice_radius_m = 10.0`
不同，§2.2 表内注明**这是搜索域扩大、不是安全参数放宽**——它只让更多
候选被审，每个候选仍按同一包络判。

**5 — 删除重复"输入"行、补路线合法性复现验收条件。** §4 的输入行已
去重并补齐哈希。新增验收条件 9：批次 2 必须在新 scenario 上重跑既有
路线合法性审计并复现 `route_sample_count = 427`、
`audited_obstacle_count = 779`、车辆 `101`、违规 `0/0` 与 `road_data`
哈希，任一不符即 fail closed；对应新工件
`route-legality-recheck.json`。

**一处主动上报、不自行处置的发现**：合同的 `hover_nominal_radius_m = 1.0`
（有效 `1.5 m`）**小于**运行时机体可见体的外接半径
`sqrt(1.6² + 0.06²) = 1.601125 m`（`AddDroneVisual` 四条臂
`localPosition = direction*0.8`、半长 `0.8`）。即已接受合同的悬停球
装不下它要保护的对象。本 ID **沿用合同值、不自行加严**（加严同样是
改合同），只登记给接受角色（§2.4 报告框、§10 OQ-3）；`P1-SCENE-005`
因为审的是运动中的机体，已按导出值取 `2.235 m`（大于合同值，属加严
方向），两者的差异在两份文档中同时可见。

**授权与边界**：本稿据 2026-08-06 账本条目"缆绳净空半径按选项 A 恢复
既有包络"撰写，该条记为**方向确认 + 起草授权，非最终变更**。本稿不
主张任何执行授权：不实现、不跑 Edit Mode/Play、不消耗 ID、不移动锚点、
不写 scenario 字节、不启动 SCENE-005 Stage B。提交后与
`P1-SCENE-005` revision 3 一并返回 Acceptance round 4。

---

## 13. Acceptance review decision — round 2

### Acceptance round 2 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

Revision 1 已关闭上一轮的 `1.5 m` 锚点盘、exact allowlist、窄支撑豁免、
参数冻结、路线合法性复现和双停点问题。但 §2.4 同时证明有效 `1.5 m`
悬停球小于真实机体外接半径 `1.601125 m`，却仍让该球决定候选是否通过。
已知欠包络不能只作为 OQ-3 披露：它会签发名不副实的悬停净空证书，并把
候选选择与下游 SCENE-005 的 `2.235 m` 机体门故意做成不一致。

Required revisions:

1. 新增并冻结 `body_nominal_radius_m = 1.61`、
   `body_clearance_margin_m = 0.5`、静态有效半径 `2.11 m`；候选判据 8、
   全部工件、失败统计与构造性测试统一使用 `2.11 m`。旧
   `hover_nominal_radius_m = 1.0` 只保留为历史合同来源，不得继续签发
   本 ID 的悬停通过。该安全加严标为待用户明确授权。
2. 把“十二项全部逐字继承”改成逐项来源表：锚点盘 `1.5 m` 与静态垂直
   系留走廊 `1.0 m` 继承 SCENE-003/004；机体球 `2.11 m` 是本 ID 因真实
   外接半径新提出的加严。验收条件 1 与 §5 的“安全包络零收缩”按此改写，
   不得同时声称悬停球逐字继承又使用新值。
3. 批次 1 统一写成“零 scenario 几何字节、零 `anchor_world_m` 写入”，
   而非“零配置字节”；`config/p1-scene-007-relocation.json`、工具和候选
   工件一起进入停点 1 与第一轮独立复核。

Disposition:

- revision 1 已关闭的锚点盘、allowlist/豁免边界、十二项确定性选择参数、
  路线复现与双停点顺序不重开；
- 不授权实现、Edit Mode/Play、候选评估、场景字节、锚点移动、ID 或配额；
- 与 SCENE-005 round 4 的动态系留来源及 `A0.3` 两项一起返回构思角色，
  revision 2 与 SCENE-005 revision 4 一并进入 Acceptance round 5。
