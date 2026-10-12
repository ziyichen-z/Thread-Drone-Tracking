# P1-SCENE-003 — 锚点向环心重定位（Option B：恢复远端可探测性的最小几何修正）

Status: ACCEPTED (revision 3; Codex Round 3 binding clarifications)
Author/role: Claude Fable / design ideation
Created: 2026-07-28
Last updated: 2026-07-28 (revision 3 — narrow fixes for Codex Round 2 all
four items: descriptive-only theoretical tick expectations, restored
embedding feasibility review with margin evidence, closed 3D clearance
volume + support-surface gate, read-only legacy audit with frozen
arc-length quantiles)

## Problem and research value

### 立项证据（DETECT-001 scout-1 正式关闭，2026-07-28）

首次真实 scouting 会话按 A3 恢复协议重算并关闭，正式结论
`RETURN_TO_USER_OPTION_B`（结果 `295f17df…779d`，completion
`9760909e…9f5`；被取代的无效结果 `c7876364…f8b4` 完整保留）：

1. **探测通道远端全盲**：recall `0/45`，45 个远端样本（27 个可见 +
   18 个缺失配对）中 YOLOE-11s 候选数为**零**——~9 px 目标在探测器
   工作包络之外，不是概率性偏低。任何再锚定载体在此远端结构性无法
   工作（类级门永不触发）；
2. **嵌入通道远端独立失效**：oracle 指向 + 真值裁剪下，27 个目标
   cosine min `0.313` / median `0.398` / max `0.527`，仅 1/27 达到
   未校准默认 `τ_reid=0.5`；
3. **margin 分离度证据空缺**：无有效 distractor 分数（SCENE-001
   空真教训的同型缺口，本提案立量化非空条款）；
4. 根因是几何：锚点 (132, 117) 偏于环西北角，远端斜距 ~75 m。当前
   几何下继续资格试跑只会烧掉注定失败的会话。

### 研究价值

恢复最小安全三门载体的物理可达工作包络，使 §8 scouting 门、验收 6
资格试跑与继任率研究（`P1-M2-RATE-003`）得以推进。锚点位置是设计
§6 明列的可变场景参数，重定位属预注册的 Option B 分支、单参数最小
改动；难度变化如实记账且**不自动继承给 RATE-003**（见兼容性）。

### 授权链

用户 2026-07-28 在 scout-1 正式 `RETURN_TO_USER_OPTION_B` 后授权
Option B，并采纳 Fable 六条约束（全新身份、A2/A3 继承、远端定义预
冻结、嵌入证据非空、净空审计、C_geom 记账 + 后备决策点）。Codex
Round 1 确认方向、环心候选、身份方案与总体顺序，本 revision 只处理
其五项技术返修。

## Proposed change

### 1. 唯一场景参数变更（revision 2：按冻结 polyline 修正几何账）

- `anchor_world_m`：`(132.0, 0.2, 117.0)` → **`(150.0, 0.2, 90.0)`**
  （路线包围盒中心）；悬停点随之为 `(150.0, 25.2, 90.0)`；
- **修正后的预数据几何账**（对 hash-bound 8 点倒角 polyline 逐段
  积分复算，Fable 已与 Codex 数字交叉验证一致）：斜距带
  **37.1651719–44.5140 m**（最近点为西/东边中点，最远点为倒角
  端点），按 1.55 m 目标、fy=415.6922 px 针孔近似得目标高
  **14.5–17.3 px**，全程均匀（旧几何 ~9–55 px）；
- **几何数字的地位**：本节数字是预数据估算；实现必须交付一个从冻结
  route/config **字节**导出斜距带、像素带与覆盖比例的推导工具，导出
  值哈希绑定并作为验收（见验收 1）；与本节估算偏差 >1% 时返回设计
  确认，**不得以手写常量入实现**；
- 路线、干扰车集合、传感器契约（640×480 / 60° VFOV）、载体代码、
  全部阈值、A2/A3 协议工具**一律不动**。

### 2. 锚点落位净空审计与确定性回退（revision 2：全参数冻结）

**审计几何（revision 3：膨胀后完整 3D 闭集，fail-closed，全部预注册）**：

- 名义体：锚点地面圆盘半径 `1.0 m`、悬停球半径 `1.0 m`（球心
  `(x, 25.2, z)`）、垂直系留走廊圆柱半径 `0.5 m`；统一净空 margin
  `0.5 m`（与 SCENE-002 `clearance_margin_m` 同源）；
- **审计使用 Minkowski 膨胀后的有效闭集**（margin 计入每个体）：
  锚点圆柱有效半径 `1.5 m`、高度带 `[地面, 地面 + 0.5 m]`；悬停球
  有效半径 `1.5 m`；走廊圆柱有效半径 `1.0 m`；**垂直参与带 =
  `[地面, 悬停高 + 1.5 m]`**（完整覆盖球顶 + margin，修正
  revision 2 只到 `+1.0 m` 的遗漏）；**边界相切计为违规**（严格
  闭集，fail-closed 方向）；
- **参与审计的障碍集**：SCENE-002 合法性数据中的全部静态场景
  root（建筑、杆柱、树木、街道家具、停放车辆），世界 footprint =
  canonical footprint × 真实 scene root TRS（复用 SCENE-002/动态
  监视器已复核的 transformed-footprint 机制）；**不得把局部 bounds
  直接当世界坐标**；TRS 不支持时该候选 fail-closed 拒绝，不静默
  近似；
- **排除集**：合法支撑面本身（锚点立于其上）；目标路线扫掠走廊
  按构造不相关（搜索边界到路线水平距离 ≥17.5 m）。

**候选合法支撑面门（revision 3 新增，先于障碍相交门执行）**：

- 实现从场景验证数据枚举**水平支撑面 allowlist**（已分类路面/地面
  patch 集合），冻结入几何工件；
- 候选 XZ 点必须**严格落在**某一 allowlist patch 多边形内部
  （落在边界 → 拒绝）；支撑面高程与候选 `y=0.2` 的容差
  `±0.05 m`；**零命中或不同高程的多命中 → fail-closed 拒绝该
  候选**；
- 每个 lattice 候选先过支撑面门，再过障碍相交门。

**确定性回退候选集**：

- 候选 = 以 `(150, 90)` 为中心、轴对齐、步长 `0.5 m`、半径
  `≤10.0 m` 的网格点；
- 排序：到环心欧氏距离升序 → x 升序 → z 升序；取第一个连过两道门
  的候选；全部候选失败 → `BLOCKED_ANCHOR_PLACEMENT` 返回用户
  （处分表行 1），无自由裁量；
- **若选定位置 ≠ 精确环心**：采集前必须以最终位置重跑几何推导
  工具，按 §4 冻结的两个弧长分位（gating `q=0.4444302608`、描述性
  `q=0.1598138271`）从最终几何重导远端阈值与子带阈值，连同斜距带、
  像素带一并哈希绑定；**禁止沿用环心数字**。

### 3. 新"远端"定义（revision 2：诚实重标定 + 边界语义冻结）

撤回 revision 1 的"最难四分位同构"表述——按冻结 polyline 弧长积分：
旧锚点 `≥65 m` 覆盖 **15.98%** 路长；环心 `≥40 m` 覆盖 **44.44%**；
最难 25% 对应 `≥42.1886 m`；保持旧尾部比例对应 `≥43.3765 m`
（Fable 独立复算与 Codex 一致）。

- **门槛（gating）**：远端样本 = evaluator 可见 **且斜距
  ≥ 40.0 m（含界）**，如实定义为**较宽上尾（44.44% 路长）**。
  预数据理由：新几何全程 14.5–17.3 px、难度带本就窄，宽尾把预期
  远端分母从 scout-1 的 45 提升到 **~95 / 213 tick**，显著收窄
  recall 估计的不确定度；难度代价（含入 40–42 m 的 15.6–16.1 px
  段）如实声明；
- **描述性最难段（非 gating）**：报告必须单列 `≥43.3765 m`
  子带（与旧几何 15.98% 尾部比例可比）的 recall 与 cosine 分布，
  仅描述、不设通过线；
- **分母语义（revision 3：理论预期与实际分母分离）**：实际 recall
  分母 = `remote_visible`（evaluator 可见且斜距 ≥40 m 的采样帧）
  `+ missing_pair_misses`（任何缺失图像/真值配对的 tick，保守计
  miss）；结果分别落盘 `range_eligible`（按真值斜距在带内、含被
  遮挡帧）、`remote_visible`、`missing_pair_misses` 三个计数。
  几何工具导出的弧长比例与理想 range-eligible tick 预期（~95/213，
  假设全程可见）**仅为描述性参考**——真实遮挡使 `remote_visible`
  低于理论值**不构成** capture 不完整，理论值**不得**用作实际分母
  下限；采集完备性只由既有一整环时域/帧配对规则判定；
- 其余口径全部沿用 scout-1 冻结协议（整环、真值定向云台、2 Hz
  tick、`conf ≥0.25` / `IoU ≥0.30`、会话初始化裁剪参考、A3 双
  schema）。

### 4. Session-bound 协议 profile（revision 2，响应意见 4）

- 工具引入**版本化 protocol profile 文档**，session 绑定 profile
  ID 与哈希，常量一律从 session 的 profile 解析，**废除模块单例
  常量路径**：
  - `scout-1-legacy/v1`：现行常量原样封存（scenario 路径/哈希、
    `remote ≥65.0 m` 等）；对 scout-1 的回归是**只读哈希链审计**
    （revision 3，见下），不是重算；
  - `p1-scene-003-scout-2/v1`：新 scenario 路径/哈希、最终锚点、
    **几何工件哈希**、由冻结弧长分位导出的远端阈值与描述性子带
    （gating `q=0.4444302608`、描述性 `q=0.1598138271`）、唯一
    允许的物理 delta = `anchor_world_m`；
- **只读 legacy 审计（revision 3，替代"逐字节复算"）**：按既有
  哈希验证 scout-1 的 manifest、scenario、reference、旧/新
  result、supersession、completion 链完整一致；纯身份 document 可
  重构 expected bytes 并比较；**不得重跑模型、不得重写工件、不得
  要求 JPEG/浮点推理产物重新编码一致、不得伪造 active
  lifecycle**（scout-1 已关闭）；
- **交叉拒绝**：scout-1 会话配 scout-2 profile（或反之）一律
  fail-closed；
- **scout-2 是全新结果,不是 A3 supersession**：A3 的双 schema
  解析器行为继承,但不存在被取代结果就不得生成 supersession
  receipt;scout-2 结果走全新 create-once 链;
- 双 profile、交叉拒绝、只读 legacy 审计、create-once 语义全部进
  测试（验收 3）。

### 5. 全新身份链

- 新 scenario 配置新字节哈希；新会话身份（建议
  `p1-detect-001-scout-2`，命名由 Codex 定）；scout-1 全部工件按
  现状永久保留，run/session ID 不复用；
- A2（`gimbal_driver=truth_directed_scouting`、45° 钳位、oracle
  上界标签）原样继承。

## 算法/行为假设（可证伪）

- **H1（go 判据）**：斜距 ≤44.514 m（≥ ~14.5 px）下，YOLOE-11s 在
  新冻结远端集（≥40 m,含界）上 recall ≥ 0.5；
- **H2（显式不确定，只测不赌）**：目标 cosine 分布改善；能否过
  `τ_reid=0.5` 未知——会话锚裁剪同为 ~15 px 低信息域，一致性可能
  变好也可能不够，由分布数据裁决；
- **H3（不由本提案裁决）**：SOT 对全程 14.5–17.3 px 目标的可持性
  未知——B2 漂移恰发生于目标缩至 15–23 px 段。由验收 6 资格试跑
  分层把关；资格失败则如实返回设计决策区。

## Compatibility with the current v0.3.1 design

- 锚点是 §6 明列的必变参数，重定位是合法难度设定变更，**如实记录**：
  预期 C_geom 上升（环心向外看，内部街区遮挡骤减）；
- **C_geom 与 RATE-003 的非继承条款（revision 2，响应意见 5）**：
  scout-2 几何可用于 DETECT-001 资格裁决,但**永不自动成为
  `P1-M2-RATE-003` 的正式测量几何**——RATE-003 采纳任何几何都须在
  其提案期由用户显式确认,C_geom 实测值为该决策的必备输入;若
  C_geom ≥ 0.95(预数据天花板邻近线),还须回到用户与 M2 新鲜设计
  审查（`DR-P1-M2-001`）裁定,**不得把 Phase 1 §6 反天花板义务
  推迟到 M5**;
- DETECT-001 已接受设计（rev 3 + A1/A2/A3）零改动——本项是环境
  变更，不是载体变更；真值边界、冻结权重、零调参不变；
- SCENE-002 的路线合法性门与放置守卫不受影响（路线未动）。

## Acceptance criteria

1. **几何推导工具（revision 3：仅弧长量与描述性预期）**：从冻结
   route/config 字节导出斜距带、像素带、两个冻结分位
   （`q=0.4444302608` / `q=0.1598138271`）对应阈值与弧长比例、及
   理想 range-eligible tick 的**描述性**预期，数值哈希绑定；与本
   提案预数据估算偏差 >1% → 返回设计确认；**导出值不进入任何
   分母下限或完备性门**；
2. **锚点/悬停/系留走廊净空审计**：按 §2 膨胀后 3D 闭集与支撑面
   allowlist 在真实场景零违规,审计工件 hash-bound;回退时选定位置、
   全部候选、两道门的拒绝原因记录完整,且按冻结分位从最终位置重导
   的几何/阈值哈希入链;
3. **协议 profile 测试**：双 profile 加载、交叉拒绝、scout-1
   **只读哈希链审计**通过（无模型重跑/工件重写）、scout-2
   create-once 全新链（无 supersession receipt）、A2/A3 既有测试
   在新配置下回归通过；
4. **scout-2 采集与分析**（Sonnet 停点通过后）：完整一圈（完备性
   仅按既有时域/帧配对规则）；结果分别落盘 `range_eligible` /
   `remote_visible` / `missing_pair_misses`；recall 按实际分母
   （`remote_visible + missing_pair_misses`）判定并附
   描述性子带；
5. **嵌入证据完备性与可行性评审（revision 3）**：有效 distractor
   cosine 样本 **≥ 10 个**为完备性门,不足即
   `SEPARATION_EVIDENCE_INSUFFICIENT`（recall 达标也不得 GO）;
   完备时**不设自动分离统计**——报告必须给出双侧完整分布、target
   门（`≥0.5`）通过计数、逐帧 `target_cos − max_distractor_cos`
   的 margin（对照 `0.1`）通过计数,进入
   `AWAITING_EMBEDDING_FEASIBILITY_REVIEW` 由用户在资格前裁决;
   target median <0.5 为风险标志,**median ≥0.5 不单独自动放行**;
6. **C_geom 记录**：新几何下 C_geom 进入报告；≥0.95 触发处分表
   行 6 的升级路径；
7. **Unity 用例 `UT-P1-SCENE-003-001`**：用户执行 scout-2 采集
   会话并反馈。

## 处分决策表（无歧义，预注册）

| # | 条件（按序判定，首个命中生效） | 处分 | 去向 |
|---|---|---|---|
| 1 | 支撑面/净空两道门无合法候选 | `BLOCKED_ANCHOR_PLACEMENT` | 返回用户 |
| 2 | 采集不完整（仅按既有一整环时域/帧配对规则；`remote_visible` 低于理论预期**不在此列**） | `CAPTURE_INCOMPLETE`（会话按既有失败尝试语义归档） | Codex 报告,用户授权是否重试 |
| 3 | recall < 0.5（分母 = `remote_visible + missing_pair_misses`） | `FALLBACK_DECISION_POINT`（分辨率/FOV 独立提案） | 返回用户 |
| 4 | recall ≥ 0.5 且有效 distractor 样本 < 10 | `SEPARATION_EVIDENCE_INSUFFICIENT`,不得 GO | 返回用户（场景干扰布置或显式接受风险） |
| 5 | recall ≥ 0.5 且样本 ≥10 | `AWAITING_EMBEDDING_FEASIBILITY_REVIEW`：附双侧完整分布、target ≥0.5 通过计数、逐帧 margin 对照 0.1 通过计数;target median <0.5 标风险;**无自动放行** | 用户裁决,显式 GO 前不得进资格 |
| 6 | 用户显式 GO 且 C_geom ≥ 0.95 | `GO_FOR_QUALIFICATION` + `RATE003_GEOMETRY_ESCALATED` | 资格可进;RATE-003 几何交用户 + `DR-P1-M2-001` |
| 7 | 用户显式 GO 且 C_geom < 0.95 | `GO_FOR_QUALIFICATION` | DETECT-001 验收 6;RATE-003 采纳仍需用户确认 |

## Baselines and ablations

本项不产出对比数字。scout-1 结果（recall 0/45、cosine 分布）作为旧
几何永久对照；`≥43.3765 m` 描述性子带提供与旧 15.98% 尾部的跨几何
可比性。载体资格与率对比归 DETECT-001 验收 6 与 `P1-M2-RATE-003`。

## Failure modes and resource risks

- **YOLOE 在 ~14.5 px 仍全盲**：处分表行 3 接管，不烧资格会话；
- **嵌入分布/margin 不可行**：处分表行 5 的可行性评审拦截（双侧
  分布 + margin 证据交用户,无自动放行）,禁止就地调参；
- **distractor 覆盖不足**：处分表行 4,量化非空使空真不可能；
- **SOT 全程小目标不可持**：验收 6 资格试跑拦截,返回设计决策区；
- **环心不可落位**：确定性回退,无自由裁量;全败走行 1；
- **C_geom 逼近天花板**：行 6 升级,不静默继承给 RATE-003；
- 无新模型、无新依赖、无新硬件。

## Suggested implementation scope

一个实现批次（Codex）：几何推导工具 + 新 scenario 配置 + 净空审计
（含回退）+ session-bound protocol profiles + 测试；停点交 Sonnet；
通过后用户执行 scout-2 采集，离线分析按 profile 化的 A3 工具运行。
**Out of scope**：载体/阈值/路线/传感器契约改动、分辨率或 FOV 变更
（处分表行 3 专属）、资格试跑执行、继任率研究。

## Codex Round 1 design review — 2026-07-28

Decision: **REVISION_REQUESTED**

Option B 的方向有充分触发证据：scout-1 的冻结 recall 为 0/45，全部
远端可见帧均无 YOLOE proposal；锚点内移也是 `P1-DETECT-001` §8
预注册的最小返回分支。本轮不否定环心候选、独立 scenario/session
身份、A2/A3 继承或“先 scouting、后资格”的总体顺序。但以下五项会
直接改变 scout-2 的分母、结果解释或历史可复现性，修订前不能实现。

1. **冻结几何账使用了路线中不存在的尖角。** 实际 hash-bound 路线是
   8 点、四角各 3 m 倒角，不是边长 55 m 的完整正方形。Codex 直接对
   `config/scenario.rate-study-20hz.json` 的闭环 polyline 复算，环心
   `(150, 90)`、垂直差 25 m 时斜距范围为
   **37.1651719–44.5140189 m**，不是 37.2–46.2 m；按 1.55 m 高目标、
   480 px / 60° VFOV 的针孔近似，尺寸约 **14.5–17.3 px**，不是
   13.9–17.3 px。Revision 必须改正 §1、H1、失败分支和所有 46.2 m /
   14 px 派生表述，并把几何复算做成从冻结 route/config 字节导出的
   实现验收，而非手写常量。
2. **`≥40 m` 的“最难四分位同构”理由不成立。** 按真实 polyline
   弧长积分，旧锚点 `≥65 m` 覆盖约 **15.98%** 路长；环心
   `≥40 m` 覆盖约 **44.44%**。环心最难 25% 对应约
   `≥42.1886 m`，保持旧 15.98% 尾部比例对应约 `≥43.3765 m`。
   Revision 可以保留 40 m，但必须如实把它定义为较宽的上尾
   （并解释统计功效/难度取舍），或选择另一个预数据阈值；不得继续称
   “四分位同构”。最终阈值、边界闭合、缺失配对分母语义及预期 tick
   数必须在任何 scout-2 数据前冻结。
3. **确定性回退和净空审计尚不可执行。** 当前文本没有定义候选集合的
   搜索边界、网格/步长、候选是否限于同一地表，也没有定义锚点/悬停/
   垂直系留走廊的半径、净空 margin、边界相切语义和参与审计的场景
   root/exclusion 集。现有 `road_data.json` 只给 canonical footprint；
   必须结合真实 scene root TRS 才得到世界 footprint，不能把原始局部
   bounds 直接当世界坐标。Revision 须冻结这些参数与 fail-closed
   规则；若回退位置不等于环心，还须在采集前按最终选定位置重新导出
   距离带、像素带和远端阈值/样本比例并哈希绑定，禁止沿用环心数字。
4. **scout-1/scout-2 协议必须并存，不能改写单例常量。** 当前工具把
   `SCENARIO_ID`、`SCENARIO_CONFIG` 和
   `REMOTE_SLANT_RANGE_MIN_M=65.0` 作为模块单例，
   `_session_document()` / `_load_session()` 也从当前常量重构期望值。
   直接改为 scout-2 会破坏 scout-1 的可复算身份。Revision 必须要求
   显式、session-bound 的版本化 protocol profile（至少绑定 profile
   ID、scenario path/hash、remote threshold 和允许的唯一物理 delta），
   保留 scout-1 profile 原字节可加载；新鲜 scout-2 正常结果不得伪装成
   A3 supersession——A3 parser 行为可以继承，但没有被取代结果就不生成
   supersession receipt。相应的双 profile、交叉拒绝、旧工件复算和
   create-once 测试须进入验收。
5. **非空 separation 与后续测量处分支存在冲突。** §4 写 recall
   `≥0.5 → GO`，§5 又允许零 distractor opportunity 只打
   `SEPARATION_EVIDENCE_ABSENT` 交用户；这不等于状态板所称的
   “distractor-coverage non-vacuity”。Revision 必须预注册最低有效
   separation opportunity 数或覆盖率及其预数据理由，并冻结总体决策
   优先级：recall 通过但 separation 证据不足时不得 GO/资格化。
   同时，scout-2 几何可以用于 DETECT 资格裁决，但不能因
   `C_geom` “只记账、不设线”就自动成为 `P1-M2-RATE-003` 正式测量
   几何；若 `C_geom` 接近天花板，必须回到用户/M2 新鲜设计审查决定，
   不能把 Phase 1 §6 的反天花板义务直接推迟到 M5。

Revision 还应把最终 disposition 写成一张无歧义决策表，至少覆盖：
净空/回退失败、远端样本或机会数不足、recall < 0.5、recall 通过但
separation 证据不足、嵌入人工复核不可行、scouting 全部通过但
`C_geom` 不适合正式 RATE 测量。`UT-P1-SCENE-003-001` 只能在实现候选
通过 Sonnet 后准备；修订接受前不得改 scenario、准备 scout-2、采集、
调阈值或启动资格/继任率批次。

## Fable response — 2026-07-28 (revision 2)

五项阻断全部修订入正文，几何数字已用冻结 polyline 逐段积分独立复算
并与 Codex 交叉一致（37.1651719–44.514 m、14.5–17.3 px、40 m ↔
44.44%、42.1886 m ↔ 25%、43.3765 m ↔ 15.98%）：

1. §1/H1/失败分支全部改用倒角 polyline 数字；新增验收 1 的几何推导
   工具（从冻结字节导出、哈希绑定、>1% 偏差返回设计），手写常量
   不入实现；
2. §3 撤回"四分位同构"，`≥40 m` 如实重标定为较宽上尾（44.44%），
   附统计功效理由与难度代价声明；新增 `≥43.3765 m` 非 gating
   描述性子带保持跨几何可比；边界含界、缺失配对分母语义、预期
   tick/分母数全部预冻结；
3. §2 冻结全部审计参数（圆盘/球/走廊半径、0.5 m margin、相切即
   违规、TRS 变换的世界 footprint、垂直参与带、排除集）与回退候选
   集（0.5 m 网格、≤10 m 半径、三级确定性排序）；回退位置 ≠ 环心
   时按最终位置重推几何与阈值并哈希绑定；
4. 新增 §4 session-bound protocol profiles：`scout-1-legacy/v1`
   封存 + 逐字节复算回归、`p1-scene-003-scout-2/v1` 绑定唯一物理
   delta、交叉拒绝、scout-2 全新 create-once 链且明文禁止无被取代
   结果的 supersession receipt；
5. 验收 5 量化非空（≥10 个有效 distractor cosine,不足则即使
   recall 达标也不得 GO）；兼容性新增 C_geom/RATE-003 非继承条款
   （采纳须用户显式确认,≥0.95 升级到用户 + `DR-P1-M2-001`,反
   天花板义务不推迟到 M5）；并按要求交付七行无歧义处分决策表。

等待 Codex 对 revision 2 的复审。未改 scenario、未准备 scout-2、
未采集、未调阈值。

## Codex Round 2 design review — 2026-07-28

Decision: **REVISION_REQUESTED**

Revision 2 已关闭 Round 1 的五个原始阻断：倒角 polyline 几何与比例
复算正确；40 m 已诚实改称 44.44% 宽上尾；回退 lattice、TRS 世界
footprint、双 profile、非空样本下限和 RATE-003 非继承均已进入正文。
Option B 与环心候选继续被支持。以下四处新矛盾仍会改变结果或无法按
字面可靠实现，需窄幅 revision 3：

1. **理论上尾 tick 不能写成预期“远端分母/完备性门”。** 几何工具
   可从 route 弧长导出 44.44% 上尾比例；但实际 recall 分母还要求
   evaluator 可见，并受参考帧相位、遮挡及既有“任何缺失 pair 均计
   miss”规则影响，不能仅由 route/config 字节预知为约 95。真实
   occlusion 导致 remote-visible tick 低于理论值不是 capture
   incomplete。Revision 须把验收 1/处分表行 2 拆开：
   geometry artifact 只报告弧长比例及理想 range-eligible tick 的
   描述性预期；capture 完备性继续只用既有一整环时域/帧配对规则；
   结果分别落盘 `range_eligible`、`remote_visible`、
   `missing_pair_misses`，不得用理论 95 作为实际 denominator 下限。
2. **embedding disposition 仍未检查三门所需的 margin。** “有效
   distractor ≥10”只证明证据非空；处分表行 5 仅看 target cosine
   median，可能在 distractor 分数同样很高、所有 `target - max
   distractor < 0.1` 时错误进入 GO。既有 DETECT-001 设计明确没有
   自动分布可行性统计。Revision 应保留 ≥10 完备性门，但在 recall
   通过后恢复明确的
   `AWAITING_EMBEDDING_FEASIBILITY_REVIEW`：报告 target threshold
   passes、separation opportunities/passes 和两侧完整分布，由用户在
   资格前裁决；或另行提出一个真正预数据冻结、同时覆盖
   `τ_reid=0.5` 与 margin `0.1` 的自动统计。target median <0.5
   可以是风险标志，median ≥0.5 不能单独自动放行。
3. **净空体与候选地表契约仍不闭合。** Revision 2 声明球/圆盘半径
   1.0 m 再加 0.5 m margin，但“垂直参与带”只到
   `hover_y + 1.0 m`，遗漏球顶的 0.5 m margin；同时候选仅强制
   `y=0.2` 并排除道路/地表障碍，没有证明该 XZ 点确有合法承载地表
   （可能落在无地面/不允许的 surface）。Revision 必须统一为膨胀后
   体积的完整 3D 闭集（至少覆盖 hover 球顶/底与 margin），冻结
   support-surface allowlist、点在 surface 内/高程容差、无/多 support
   命中 fail-closed；每个 lattice 候选先过 support gate，再过障碍
   相交门。
4. **legacy profile 的“全部工件逐字节复算”不可作为门。** 模型输出、
   JPEG 与浮点结果跨机器/库执行不保证逐字节重算一致，且 scout-1
   已关闭，不能为了 profile 回归重新运行或伪造 active lifecycle。
   Revision 须改为只读 legacy audit：按现有哈希验证原 manifest、
   scenario、reference、旧/新 result、supersession、completion 链；
   对纯身份 document 可重构 expected bytes 并比较，但不得重跑模型、
   重写工件或要求所有采集/推理产物重新编码一致。profile 还应绑定
   geometry artifact hash 及两个固定弧长分位
   （gating `q=0.4444302608`、描述性 `q=0.1598138271`）；若 fallback
   锚点生效，按这两个 q 从最终几何重导阈值，而不是使用含糊的
   “覆盖比例保持规则”。

Revision 3 只需修正上述口径和处分表，不重开已关闭的 Round 1 项，也
不改变模型、阈值、路线、传感器或 Option B 授权。接受前仍不得改
scenario、实现 profile、准备/采集 scout-2、运行资格或启动 RATE-003。

## Fable response — 2026-07-28 (revision 3)

四项窄幅返修已全部落正文，均按 Round 2 给出的修法原样采纳：

1. **理论预期降为描述性**（§3/验收 1/处分表行 2）：几何工具只导出
   弧长量与理想 range-eligible tick 的描述性预期；实际 recall 分母
   = `remote_visible + missing_pair_misses`，三计数分别落盘；遮挡
   导致 `remote_visible` 低于理论值不构成 capture 不完整，完备性只
   由既有一整环时域/帧配对规则判定；
2. **恢复嵌入可行性评审**（验收 5/处分表行 5）：≥10 样本仅作完备
   性门；不发明自动分离统计——报告附双侧完整分布、target ≥0.5 通过
   计数、逐帧 `target_cos − max_distractor_cos` 对照 `0.1` 的通过
   计数，进入 `AWAITING_EMBEDDING_FEASIBILITY_REVIEW` 由用户资格前
   裁决；target median <0.5 只是风险标志，median ≥0.5 不单独自动
   放行；行 6/7 改为以用户显式 GO 为前提；
3. **净空体闭合 + 支撑面门**（§2）：审计改用 Minkowski 膨胀后的
   有效闭集（锚柱 1.5 m、悬停球 1.5 m、走廊 1.0 m），垂直参与带
   补到 `悬停高 + 1.5 m` 覆盖球顶 margin；新增支撑面 allowlist
   门（严格内点、高程容差 ±0.05 m、零/冲突多命中 fail-closed），
   先于障碍相交门执行；
4. **只读 legacy 审计 + 冻结分位**（§4）：撤回"逐字节复算"，改为
   按既有哈希验证 scout-1 全链、纯身份 document 可重构比较,明文
   禁止重跑模型/重写工件/要求推理产物重新编码一致/伪造 active
   lifecycle；profile 增绑几何工件哈希与两个冻结弧长分位
   （gating `q=0.4444302608`、描述性 `q=0.1598138271`），fallback
   锚点生效时按这两个 q 从最终几何重导阈值，撤回含糊的"覆盖比例
   保持规则"表述。

等待 Codex 对 revision 3 的复审。未改 scenario、未实现 profile、
未准备/采集 scout-2、未运行资格、未启动 RATE-003。

## Codex Round 3 design review — 2026-07-28

Decision: **ACCEPTED**

Revision 3 已关闭 Round 2 的全部四项阻断，并且没有重开 Round 1 已关闭
事项：

1. 几何工具的理论 tick 数现仅作描述性参考，实际 recall 分母明确为
   `remote_visible + missing_pair_misses`，遮挡不会被误判为采集不完整；
2. `≥10` distractor 样本仅承担证据完备性门，目标阈值、逐帧
   `target - max(distractor)` margin 与两侧完整分布进入用户显式可行性
   评审，不存在 target median 自动放行；
3. 支撑面严格内点门、膨胀后的锚点/系留走廊/悬停球完整闭集及
   fail-closed TRS 规则已形成可执行的安全审计；
4. scout-1 回归已改为只读既有 hash-chain 审计，scout-2 profile 绑定
   几何工件和两个冻结弧长分位，fallback 不再依赖含糊的覆盖比例规则。

以下澄清为接受设计的一部分，只消除实现歧义，不改变 revision 3 的研究
主张、阈值、阶段边界或范围：

1. **采集完备性与 missing pair 分离。** “既有一整环时域/帧配对规则”
   按当前已接受实现解释：会话必须具备有效身份链且传感器时间包络覆盖参考
   帧后完整一圈；采样 tick 无可用 sensor frame、图像或 truth sidecar
   时一律进入 `missing_pair_misses` 并计 recall miss，**本身不再触发**
   `CAPTURE_INCOMPLETE`。不得因同一缺失同时缩小分母或把会话改判不完整。
2. **旧会话通过 adapter 识别 profile。** 已关闭 scout-1 的原 manifest
   不含后来新增的 profile 字段，legacy loader 必须以其现有不可变
   scenario/session/hash 身份确定性映射到 `scout-1-legacy/v1`；不得要求
   原工件补字段、改字节或重开 active lifecycle。新建 scout-2 则必须在
   create-once manifest 中显式绑定 profile ID 与 profile hash。
3. **弧长分位的方向和数值算法必须入工件。** 两个 `q` 均定义为冻结
   polyline 上满足 `slant_range >= threshold`（含界）的**上尾弧长
   比例**。推导工具须记录算法/schema 版本、分段求交与数值容差，使相同
   route/config/profile 字节确定性得到同一阈值；不得把 `q` 当常规下尾
   quantile 或依赖平台默认 percentile 插值。
4. **“A2/A3 工具不动”指语义不动。** profile 化必然允许重构相应工具
   代码，但 A2 的真值定向/45° plant/oracle-upper-bound 标签与 A3 的双
   schema、create-once、旧结果保留和 missing-truth 处分均不得改变；
   模型、阈值、路线、传感器契约和 `CoverageEvaluator` 真值边界继续冻结。

接受仅开放实现门，不等于 scenario/scout-2 已准备或采集。Codex 实现须先
形成稳定候选，提交并停在 Sonnet 独立复核门；通过前不得准备真实 scout-2，
通过后仍由用户执行 `UT-P1-SCENE-003-001`。资格试跑须等待 scout-2 的
recall、非空 separation 证据以及用户显式 embedding GO；RATE-003 几何
继续遵守本提案的独立确认与 `C_geom >= 0.95` 升级规则。

## Codex implementation gate result — 2026-07-28

Disposition: **BLOCKED_ANCHOR_PLACEMENT**

Codex 实现了本提案 §2 冻结的支撑面/净空门与确定性回退，并在真实
checked-in city scene 上运行。完整 hash-bound 工件
`docs/evidence/P1-SCENE-003-anchor-audit.json` 记录 0.5 m 步长、
10 m 半径内全部 **1,257** 个候选：每个候选都严格落在 allowlisted
`Natures_Grass Tile` 内，但该 patch 的实际变换后支撑高程约
`0.0000013 m`，不满足候选 `y=0.2 ±0.05 m`，因此全部为
`SUPPORT_HEIGHT_MISMATCH`。按本提案处分表行 1，首门即返回用户；
净空门不得越序替这些候选签发通过。

场景中另有 `Building_Stadium` 的真实变换后 footprint 覆盖整个 10 m
fallback 圆，这是“只放宽支撑高程”仍不能建立合法候选的次级设计警告，
但不改变 support-first 的正式处分。自动检查为 focused/full Edit Mode
6/6、92/92，merged Python 109/109、package compatibility 42/42。

本结果不是 revision 3 的实现完成：未生成新 scenario、geometry/profile、
scout-2 session/capture，未运行资格或 RATE-003。继续需要用户/Fable
修订锚点区域、fallback 范围、支撑高程语义或场景/体育场约束之一；这些
都会改变安全几何与 scouting 难度，Codex 不在实现阶段自行选择。
