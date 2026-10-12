# P1-SCENE-001 — 场景车辆去冲突与路线走廊净空审计

Status: ACCEPTED_WITH_BINDING_CLARIFICATIONS
Author/role: Claude Fable / design ideation
Created: 2026-07-27
Last updated: 2026-07-27

用户 2026-07-27 直接指派：目标车在运行中与场景车辆碰撞穿模，导致结果
不正确；要求先修场景，并系统梳理其他场景设计问题。

## Problem and research value

### 1.1 实测缺陷：目标路线穿过三辆停放车辆

对 city demo 场景 104 个 `Vehicle_*` 预制件实例的序列化位置与
`route_world_m`（闭合周长 ≈ 208.97 m）做几何相交解析（离线场景文件
解析，Codex 实现时需在 Unity 内复核）：

| 场景车辆 | XZ 位置 | 距路线中心线 | 沿路线里程 s | 2 m/s 到达时刻 |
|---|---|---|---|---|
| `Vehicle_Taxi`（黄色出租车） | (138.9, 116.4) | **0.60 m** | ≈6.9 m | ≈3.45 s |
| `Vehicle_Container_color01`（集装箱卡车） | (168.3, 117.1) | **0.15 m** | ≈36.3 m | ≈18.2 s |
| `Vehicle_Police Car`（警车） | (183.9, 89.1) | **0.85 m** | ≈77.1 m | ≈38.6 s |

目标车视觉体宽 2 m（半宽 1 m），场景车辆半宽约 1.0–1.2 m；三处
中心线距离全部小于两半宽之和，即目标车**每圈都从这三辆车的车体内
穿过**。场景全程无碰撞体（M0 已证实 city 场景无序列化 3D Collider）、
无任何运动脚本，唯一运动方是 `LoopTargetVehicle` 的纯运动学步进，
所以穿模是路线与静态摆放的几何冲突，不是物理参数问题。

### 1.2 对结果正确性的具体污染路径

1. **外观污染发生在最敏感窗口**：RATE-002 冻结标定把目标放置在
   s≈0（相机 (132, 25.2, 117) 正下方），释放后约 1.3–5.6 s 目标车体
   与出租车重叠。初始模板刚建立就注入未受控的外观扰动，直接落在
   5/20 Hz 主对比的早期关键段。
2. **遮挡评估的归因错误**：停放车辆是活动 `MeshRenderer`，全部拥有
   评估器遮挡代理。目标从卡车体内穿过时，相机—目标采样射线被卡车
   网格阻挡，`visible_sample_fraction` 下降、`C_geom` 翻假——本应
   是"场景缺陷帧"却被记为"合法物理不可见"，从 `C_track` 分母中
   删失；而穿出后追踪器若已漂移到卡车/出租车（同尺度车辆外观），
   又会被记为追踪失败。两个方向的归因都错。
3. **历史诊断的可疑巧合（假设，不作因果主张）**：RATE-001 诊断中
   follow 首次 LOST 出现在 `3.45044 s`，与旧协议下目标到达出租车的
   时刻（6.9 m ÷ 2 m/s = 3.45 s）几乎一致；RATE-001 标定窗口
   frames 15–19 的目标/干扰车重叠也发生在同一路段。该项已按协议
   无效关闭，此处仅说明：同一几何冲突已至少两次干扰实验流程。
4. **30 s 正式会话覆盖 s∈[0,60]**：出租车（s≈6.9）与集装箱卡车
   （s≈36.3）都落在每个正式 RATE-002 会话内；警车（s≈77.1）落在
   更长的自由会话与未来 M4/M5 实验内。

### 1.3 连带发现：干扰分离门当前空转

RATE-002 已接受协议要求"最近干扰 = 全部活动干扰车投影框的逐一
最小值，IoU=0 且中心距 ≥ 1 倍目标框宽"。但 `RateStudyDistractor`
标记组件在场景文件中出现次数为 **0**（按脚本 GUID 检索）——
`FindObjectsByType<RateStudyDistractor>` 恒返回空集，
`active_distractor_count=0`，分离门对所有候选**空真通过**。标定中
实际造成歧义的黄色出租车从未被标记为干扰车。协议文字与场景标注
脱节，这是信息完整性缺口，须与穿模一并修复。

### 1.4 研究价值

M1 里程碑（场景视觉验证 + 场景参数化）与设计 §7"场景反天花板"
要求场景难点是**受控设计**而非意外缺陷。本项把"路线走廊净空"和
"干扰车显式标注"变成机械可检查的场景合法性条件，为 M2 正式测量、
M4 遮挡/ID-switch 实验和 M5 场景随机化提供可复用的审计基础。

## Proposed behavior

### 2.1 配置驱动的确定性场景修正（不改动第三方场景文件）

在 scenario config 增加**可选** `scene_adjustments` 块（缺省不存在时
行为与现状完全一致）：

```json
"scene_adjustments": {
  "vehicle_relocations": [
    {
      "prefab_name": "Vehicle_Taxi",
      "original_xz_m": { "x": 138.9, "z": 116.4 },
      "match_tolerance_m": 0.5,
      "new_position_m": { "x": 138.9, "y": 0.0, "z": 112.5 },
      "mark_as_distractor": true
    }
  ],
  "expected_distractor_count": 1,
  "route_corridor": {
    "target_half_width_m": 1.0,
    "clearance_margin_m": 0.5
  }
}
```

- Bootstrap 在 `CreateTarget` 之后、`CreateEvaluationOcclusionGeometry`
  **之前**应用修正，保证遮挡代理按修正后的位置构建。
- 车辆解析键 = 预制件名 + 原始 XZ 位置（容差内唯一匹配）。找不到、
  匹配多于一个、或修正后仍违反走廊净空 → **fail-closed**：抛异常
  终止会话构建，不得静默跳过。
- `mark_as_distractor: true` 的对象在运行时挂 `RateStudyDistractor`
  标记，使分离门非空转；scouting 增加校验
  `active_distractor_count == expected_distractor_count`，不等则报告
  `INVALID_SCOUTING`。
- 修正块随 scenario config 一起进入既有的 SHA-256 冻结链：任何场景
  修正的启用/变更自动改变 config 哈希，旧冻结战役无法在新场景下
  被误用——治理性质与现有协议一致，无需新增哈希机制。

### 2.2 路线走廊净空审计（新增机械检查）

新增 `RouteCorridorAuditor`（Edit Mode 可调用 + 运行时可选逐帧核查）：

1. **静态审计**：对场景内全部车辆 renderer 包围盒计算与路线折线的
   XZ 距离，`距离 < target_half_width + vehicle_half_extent +
   clearance_margin` 记为违规；输出 JSON 报告（车辆名、位置、距离、
   沿线里程）。当前场景应恰好报告 §1.1 的三处违规。
2. **动态核查（仅验证会话使用）**：Play 中逐帧检测目标 renderer
   XZ 包围盒与其他车辆包围盒的相交，计数写入报告；修正后跑完整一圈
   应为 0。该组件默认关闭，不参与正式测量会话。

### 2.3 建议的具体修正值（Codex 可在等效净空内调整）

| 车辆 | 修正 | 理由 |
|---|---|---|
| 出租车 | 沿 -z 平移至 z≈112.5（横向净距 4.5 m），`mark_as_distractor: true` | 保留在 20 Hz 标定帧脚印（x∈[112.6,151.4], z∈[102.5,131.6]）内，继续充当释放窗口的显式受标记干扰车，但不再与目标车体相交 |
| 集装箱卡车 | 移出路线走廊 ≥5 m（如就近路侧泊位） | 在标定帧脚印外，移动不影响冻结参考帧字节 |
| 警车 | 移出路线走廊 ≥5 m | 同上；主要影响长会话与 M4/M5 |

### 2.4 显式非目标

- 不引入物理引擎、碰撞体或避让控制——修复是静态摆放级去冲突；
- 不改 `route_world_m`、不改任何指标公式/协议语义；
- 移动干扰车系统（受控动态干扰）属未来 M4/M5 独立提案；
- `LoopTargetVehicle` 的航点微停顿/切角问题（见 §8）不在本项范围。

## Inputs, outputs, and affected interfaces

- 新代码：`ScenarioConfig` 可选 `scene_adjustments` 解析与校验；
  bootstrap 的修正应用步骤；`RouteCorridorAuditor`；scouting 的
  干扰车计数校验。
- 修改配置：`config/scenario.default.json` 与 RATE-002 会话配置增加
  修正块（后者仅在新战役中生效，见 §6 时序）。
- 不改：帧/观测/控制协议、评估器公式、`p1-rate2-*` 统计规则、
  第三方场景与预制件文件、追踪器代码。
- 输出工件：走廊审计报告 JSON（修正前/后各一份，入证据目录）。

## Compatibility with the current v0.3 design

- 落实设计 §7"场景反天花板"对受控难点的要求，并为 M1 的"遮挡布置
  参数化"提供机械验收工具；
- Unity 真值边界不变：审计器只服务场景合法性检查与证据报告，不向
  控制器、感知输入或传感器元数据输出任何真值；
- 与 RATE-002 冻结协议的关系是**时序问题而非语义冲突**，见 §6。

## Acceptance criteria

1. **审计器再现已知缺陷**：对未修正场景 + 现行路线，静态审计恰好
   报告 §1.1 三处违规，距离值与独立几何计算一致（±0.1 m）。
2. **修正后零违规、零相交**：启用修正块后静态审计 0 违规；动态核查
   跑完整一圈（≥105 s）目标与其他车辆包围盒相交帧数为 0。
3. **fail-closed 路径有测试**：解析键失配（找不到/多匹配）、修正后
   仍违规、`expected_distractor_count` 不符 → 会话构建或 scouting
   分别以显式错误终止/报告 `INVALID_SCOUTING`，各有直接测试。
4. **遮挡代理一致性**：修正启用时，被移动车辆的评估代理位于新位置
   （代理总数不变），有 Edit Mode 测试覆盖。
5. **缺省无扰动**：不含修正块的既有配置下，全部现有 Unity/Python
   测试通过，行为与现状逐字节一致（config 哈希不变）。
6. **反天花板保持**：修正场景中一次 follow 整圈参考会话的 `C_geom`
   仍显著 < 100%（建筑/树木遮挡保留），作为 Unity 观察项记录。

## Baselines and ablations

本项是场景合法性修复，不设算法消融。证据对比 = 修正前后两份审计
报告 + 动态相交计数 + 同一参考会话的 `C_geom`/`C_track` 前后对照
（后者仅作描述性记录，不用于任何率结论）。

## Failure modes and resource risks

- **冻结战役失效（最大风险，见 §6）**：出租车在 20 Hz 标定帧脚印内，
  移动它必然改变冻结参考帧字节，B1 战役标定随之失效。处置：时序上
  先完成待办集成重跑，再以新战役重新冻结；B1 按 fail-closed 惯例
  保留工件、标记被取代，不复用 run-ID。
- **解析键脆弱性**：场景有 129 个同名出租车实例级引用；仅凭名字
  定位必然歧义。已用"名字 + 原始 XZ + 容差"复合键并 fail-closed。
- **过度清场**：把所有路侧车辆推离路线会削弱视觉密度与干扰难度。
  本项只动三辆相交车辆，且出租车保留在标定脚印内并显式标记。
- **资源**：纯桌面改动，无新依赖、无网络、无硬件需求。

## Suggested implementation scope

建议（不强制）：`ScenarioConfig.cs` 扩展 + bootstrap 修正步骤 +
`RouteCorridorAuditor.cs` + scouting 计数校验 + Edit/Play Mode 测试
+ 修正前后审计报告入 `docs/evidence/P1-SCENE-001-corridor-audit.md`。
替代方案（直接编辑 vendor 场景文件）被不推荐：不可 diff 审查、资产
升级易被覆盖、且无法进入 config 哈希链。

## Sequencing with P1-M2-RATE-002 (decision area)

**S1（推荐）**：
1. 先让已授权的 `UT-P1-M2-RATE-002-002` 集成重跑在**未改动**场景上
   完成（它验证的是 metrics-cutoff 基础设施，消耗的是已恢复的
   字节级 B1 会话；场景改动会使其失效）；
2. 重跑通过后本项进入实现与停点复核；
3. 修正落地后，B1 战役标记 `SUPERSEDED_SCENE_DEFECT`（工件原样
   保留，无 run-ID 复用——B1 至今**没有任何正式测量会话**，损失
   仅为重做 scouting 与标定确认，估计用户操作 10–20 分钟）；
4. 以修正后场景创建新战役（B2）重新冻结 scouting/标定，再走资格
   试点与正式测量。

**S2（最小改动，不推荐）**：只移标定脚印外的卡车与警车，保留出租车
穿模与 B1 战役。被不推荐原因：外观污染恰好落在释放后模板关键窗口，
且用户报告的可见穿模仍在。

**S3（改路线避车，不推荐）**：路线变更破坏 config 哈希、周长、
scouting 表与全部里程语义，影响面大于移三辆车且无额外收益。

采用 S1/S2/S3 与 B1 处置属于协议级决策，需 Codex 审查并经用户确认。

## Other scene-design issues catalogued (non-scope, for future items)

1. **锚点视觉标记**：黄色圆柱正好在路线 s=0，目标每圈从其中穿过且
   出生时压在其上（标定框正下方）；黄色与出租车同色系。建议随 B2
   重冻结一并改为扁平深色薄片（纯视觉，锚点物理位置不动）。
2. **`LoopTargetVehicle` 航点微停顿**：到达航点 0.5 m 阈值内的那一帧
   直接 return，产生每航点一帧的速度毛刺与最多 0.5 m 切角；建议
   未来单独立项改为沿闭合路线弧长连续步进（与
   `PlaceAtRouteDistance` 同一参数化），属运动真值语义变更，须走
   独立停点。
3. **全部干扰均为静态**：M4 的 ID-switch/错误重捕获实验需要受控
   移动干扰车（确定性时刻表、显式标记、与走廊审计兼容），建议届时
   以 `P1-SCENE-002` 级别提案引入。
4. **第三方 demo 场景直用**：实验场景是资产包演示场景，项目级
   摆放意图（哪些车是干扰、哪些区域必须净空）此前无处落地；§2.1 的
   配置块即为该意图的版本化载体，后续场景随机化（M5）应复用同一
   机制而非手改场景。

## Open questions

1. 出租车新位置 z≈112.5 是否与路侧建筑/树木代理冲突，需 Codex 在
   Unity 内确认（审计器本身会兜底）。
2. `expected_distractor_count` 是否应按会话条件（follow/nadir）分别
   配置，还是战役级单值即可。
3. B1 取代后的战役命名（沿用 `P1-M2-RATE-002-B2` 还是其他），以及
   取代记录写入 `docs/evidence/` 还是战役目录内，由 Codex 定。

## Codex review decision

Decision: ACCEPTED_WITH_BINDING_CLARIFICATIONS

Rationale:

- 三处路线冲突与空真的干扰分离门会同时污染 tracker 外观与 evaluator
  的遮挡归因，属于正式测量前必须 fail-closed 修复的场景合法性缺陷。
- 配置驱动的运行时修正保留第三方资产原样，并自动进入现有配置哈希链；
  相比改路线或引入物理避让，它是影响面最小且可审计的修复。
- 审计和动态相交计数只写场景验证工件，不进入传感器元数据、tracker
  输入、控制器或 `CoverageEvaluator` 指标，因此不越过真值边界。
- 用户已在 2026-07-27 明确否决 S1 的“先重跑”步骤并批准 scene-first；
  该决定是本次接受的前置条件，不再重复请求确认。

Binding clarifications:

1. `prefab_name` 表示规范化预制件根名。实现只检查场景根对象，并允许
   Unity 的纯数字实例后缀 ` (N)`；随后以 `original_xz_m` 和容差要求
   **恰好一个**匹配。零匹配、多匹配、重复配置键均终止场景构建。
2. 修正块一旦存在，其所有数值和引用必须严格有限/有效，不使用普通场景
   配置的容错回退。静态净空审计在车辆修正后、遮挡代理构建前强制运行；
   任一剩余违规会终止构建。未修正场景的三处基线违规由 Edit Mode
   场景审计工件记录。
3. `expected_distractor_count` 是场景级精确值，而不是 follow/nadir
   条件级值：当前标记集合和 renderer 激活状态不随相机条件变化。
   scouting 必须同时报告期望值、实测值和失配原因，并以
   `INVALID_SCOUTING` 返回。
4. 建议坐标只是候选。提交稳定候选前须以真实 Unity renderer 包围盒和
   路线审计证明三处修正后为零违规；建筑/树木的视觉合理性与整圈动态
   零相交仍保留为用户 Unity 验证项。
5. B1 立即 fail-closed 归档且永不复用；修正后的继任战役 ID 固定为
   `P1-M2-RATE-002-B2`。历史 B1 工件不改字节，首个 B2 campaign smoke
   承接已停止 rerun 的 metrics-cutoff 集成目标。
6. 动态相交监视默认关闭，只可由显式配置用于验证会话；正式 RATE-002
   测量配置保持关闭，且该诊断不得写入 `CoverageEvaluator`。

Required revisions: None before implementation; the binding clarifications
above are normative.

Accepted design-document changes:

- `docs/phase1-single-drone-design.md` records config-hash-bound vehicle
  relocations, fail-closed route-corridor legality, a non-vacuous distractor
  cardinality gate, and the B1 → B2 campaign boundary.
