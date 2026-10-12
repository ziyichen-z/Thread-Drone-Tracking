# P1-M3-BODY-001 independent review

Status: ROUND_12_REWORK_REQUIRED (通过轮后接受续批复核债轮, candidate
`a5fc735`；续批的操作性内容全部核实成立——指针规则替换合格、排除清单操作
面全真、§6 N36 头一致、N34 依据复验为真——缺陷集中于来源自证文字：一条
CLASS_2 **F11**（§5 排除清单自证「账本 2026-08-14 逐字/不作增减」为假：
R10/R11、R12 不在批量 GO 条目的排除清单里）+ 两条 CLASS_3 **P8/P9**（提案
D′ 的「挂在闭合轮」与「RESIDUAL RISK 段」两处出处虚指）；P7 仍候 (c) 批次；
**B3 的 §2.0 (c) 在 F11 修正前不得发出**——修复是一句话的来源拆分)

Round history: round 1 `PASS_WITH_NOTES`（1a-α, `81202ab`）；round 2
`PASS_WITH_NOTES`（1a-β, `a234270`）；round 3 `REWORK_REQUIRED`
（1c, `e030310`，两个阻断缺陷 F1/F2）；round 4 `PASS_WITH_NOTES`
（1c round-6 返工, `e438b97`，F1/F2 关闭）；round 5 `REWORK_REQUIRED`
（preflight r8 + revision 11 累计, `7156f7e`，一个阻断缺陷 F3）；
round 6 `PASS_WITH_NOTES`（revision 11 round-4 返工, `6019f33`，F3 与
N19/N23 关闭）；round 7 `PASS_WITH_NOTES`（强制闭环轮, `07bb8a4`，
三笔复核债同轮清偿，N17 关闭，新增 N25–N28）；round 8
`REWORK_REQUIRED`（操作单 revisions 13–18 复核债, `13bf9dd`，三条
CLASS_2 缺陷 F4/F5/F6 + 三条 CLASS_3 补丁，新增 N29–N32；N25/N26/N27
验收关闭，N26 的缺陷延续为 F4）；round 9 `PASS_WITH_NOTES`（轮 8 返工
闭合轮, `408acd7`，F4/F5/F5b/F6/F6b + P1–P3 定点复看闭合，N29 关、
N31 以有理由不采纳结案，新增 N33）；round 10 `REWORK_REQUIRED`（操作单
revisions 19–22 + 轮 58 的 20 处复核债, `9cadebd`，四条 CLASS_2 缺陷
F7/F8/F9/F10 + 三条 CLASS_3 补丁 P4/P5/P6，新增 N34–N37）；round 11
`PASS_WITH_NOTES`（轮 10 返工闭合轮, `6e81bc2`，F7–F10 + P4/P5 定点复看
闭合，N34/N35/N36 经接受轮 64 裁定结案，新增 P7 与 N38/N39）；round 12
`REWORK_REQUIRED`（通过轮后接受续批 `a5fc735`，一条 CLASS_2 缺陷 F11 +
两条 CLASS_3 补丁 P8/P9，新增 N40–N42；F9 关闭判定在机制替换后经实测
维持）。轮次只追加，旧发现不删除。

Reviewer: review 角色（independent review, strongest pool; fresh context）

Implementation author: implementation 角色（Cursor）

## Round 1 — batch 1a-α（BC-M34-7 接口停点批次）

Date: 2026-08-07

- Accepted design: `docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md`
  round 2 `ACCEPTED_WITH_BINDING_CLARIFICATIONS`（BC-BODY1-1…10，设计
  v0.3.17）+ round 3 停点裁定（BC-BODY1-11…16）。
- Candidate: `81202ab`（SHA 补记提交 `a1fc9a1` 为纯文档）。Diff base:
  `4cf811a`（acceptance round 2 提交）。上一个复核通过候选：`d2db9f3`
  （P1-SCENE-006 round 8）。
- 复核范围 = 证据 §10 六条 + acceptance round 3 追加三项。范围主张按纪律
  视为待核实，不作为复核边界；候选与两个基线的全部变更逐文件核对。
- 复核副本：`git worktree add --detach .claude/worktrees/review-P1-M3-BODY-001
  81202ab`，收工已删除。主树实现文件零修改。

### 1. 变更完整性与中间区间定性

`git diff 4cf811a..81202ab --stat`：27 个路径，+23141/−20，与状态板声明
范围逐一对应（5 个新 C# + meta、1 个 EditMode 测试、4 个 Python 工具、
`controller/body_planner.py`、`tests/test_m3_body_tools.py`、3 个 config、
6 个 evidence 工件/文档、状态板与归档）。无 `.unity`、无
`track_loop.py`、无 `world_estimate.py`、无既有协议文件——BC-BODY1-3
「1a-α 零策略/估计器/track_loop」在 diff 层面成立。

中间区间 `d2db9f3..4cf811a` 除文档批次外含 SCENE-006 stage-T 的 Assets
变更（新增 `TargetVisualFactory.cs`、`TetheredScenarioBootstrap.AddCarVisual`
改为纯委托）。该批属 `P1-SCENE-006` 已终态关闭车道（BC-P2-5 在 Review 前
停止，用户授权关闭），本轮不追溯背书；本批次对它的**依赖**已单独核实：
工具 2 的 `TARGET_CUBES` 字面量与 `TargetVisualFactory.AddTargetVisual`
逐字段一致（body (0,0.5,0)/(2,1,4)，roof (0,1.2,−0.2)/(1.7,0.7,2)），
Bootstrap 委托保持局部 TRS 与颜色不变。

条件 5 审计本轮自跑复现：`check_role_writes.py --role implementation
--base 4cf811a` exit 0（27 路径全合规），与 round 3 记录一致。

### 2. 测试与工具全部自跑（不采信报告数字）

| 项 | 实现者声明 | 本轮独立复跑（副本内） |
|---|---|---|
| Unity EditMode `TetheredTracking.Tests` | 258/258 | **258/258 Passed**（结果 XML `testcasecount=258 failed=0`；含 P1M3Body 新测试） |
| 完整 Python 套件（.venv-track） | 394 / 1 失败 | **394 ran / 1 failure**，唯一失败 = `test_check_docs.test_compliant_minimal_status_passes` |
| `tests.test_m3_body_tools` | 55/55 | **55/55 OK** |
| 工具 1 `check_anchor_placement.py` | exit 0 `CLEAR` | **exit 0**：`CLEAR`，support `PASS` @ `0.20000043511390686`，误差 `−4.32e−07`，896 根 / 764 受审 / 0 阻挡 |
| 两个 Editor 生成器 | — | 副本内重跑，anchor-audit 与 scene-geometry 工件**字节零差异**；场景字节前后 SHA-256 均为 `dec58698…c9bf`（与证据 §1 声明逐位一致） |
| `build_m3_corridor.py --check` | 可复现 | **exit 0**：779 棱柱，sha256 `9e2956ad…c800` = config 钉住值 |
| 工具 2 `check_scene_body_margin.py` | 见证据 §3 | 重跑后工件**字节零差异**：`C_geom` 上界 `1.000000` / 下界 `0.565728`、臂B `0.584507`、可见弧 `[155.0, 275.5)` 跨接缝单段 `120.5 m`、窗 `[0, 62.5]`、两臂各 125 窗内样本、位移中位 `21.35` / 最大 `24.45 < 24.4949`、Stadium 2808 / 3069 |
| 工具 3 `calibrate_pixel_sigma.py` | `σ_px = 2.866112` | 2404 帧 NanoTrack 重放完整重跑，工件**字节零差异**：`2.866112`，中位 `2.7916` / p95 `7.8406` / 最大 `12.3742`，2404/2404 残差，0 丢失 |

**唯一 Python 失败项归因附议**：`tests/test_check_docs.py` 与
`tools/check_docs.py` 均不在本批 27 路径中（diff 内 0 命中），失败在候选
上原样复现——「既有失败、与本批无关、须协调批次修复」的归因成立。

**复现环境备注（供后续复核者）**：副本首跑全套曾出现 26F+4E，全部为
gitignored 权重缺失的环境性失败：`runtime/models/nanotrack-v2/` 与
`runtime/yoloe/yoloe-11s-seg.pt` 不入库；且 `run_scene006_probe.py` 的
「路径必须在项目内」防护会拒绝指向主树的符号链接，须用实体副本
（APFS clone）。补齐后即 394/1。σ_px 重放所需的 scout-4 帧/真值归档
（同样 gitignored）以只读符号链接接入即可。

### 3. 证据 §10 六条逐项核查

1. **BC-M34-4 (c) 锚点审计** — `CONFIRMED`。三个有效体积判据
   （anchor cylinder / corridor cylinder / hover sphere）与
   `P1Scene003AnchorAuditor.IntersectsEffectiveVolumes` 逐式相同（同
   epsilon、同区间语义）；support 判定链（`StrictlyInsideSurface` 严格
   内含、多支撑高程冲突、容差检查）逐行同构；原语全部经
   `P1Scene003AnchorAuditor` 引用复用，零重写。两处声明差异核实为真且
   不放宽判据：无点阵（单点裁定）、收集全部阻挡体（SCENE-003 首个即
   返回）——判定不变，任一阻挡即 FAIL；另加了 SCENE-003 没有的
   contract↔scenario 锚点一致性强检。合同五个安全值与
   `p1-scene-003`/`p1-scene-004` 逐字节相同（EditMode 测试锁定）。
   Python 检查器的独立性分工（道路面支撑与逐阻挡体域值独立复算；prefab
   支撑/场景 AABB 依赖 Editor 发布值做内部一致性检查）与其 docstring
   声明一致、诚实。`(132,117)` 的 `CLEAR` 成立。
   764 受审数与走廊 779 的差 = 合同 allowlist 命中的 15 块草地砖
   （896 − 117 道路面 − 15 草地 = 764），两个口径各自记录、互不矛盾。
2. **BC-M34-4 (a)(b) 15 点同构复算** — `CONFIRMED`。
   `bounds_corners`/`visibility_samples`（8 角+中心+6 轴向极值，分母
   恒 15）、in-frustum 判据（z>0 且 x,y∈[0,1]）、`ProjectBounds`
   （仅 8 角、z≤0 剔除、clamp、退化置 null、top-left 翻转）、面积/中心
   误差公式、`HasClearLineOfSight` 的 0.05 m 缩短、
   `TetheredGimbal.LateUpdate`（`max(0.1,−Δy)`、45° 钳位、45.1° 旗标、
   `Euler(90−applied, yaw, 0)`）——逐项与运行时源行对映核实；
   `camera_basis` 的 Ry·Rx 合成与 Unity Euler 语义一致（nadir/45° 两个
   极案手工验证）。目标包围盒按偏航旋转 AABB（`Renderer.bounds` 语义）
   正确。R1–R5 归约在 docstring 与工件 `pre_registered_reductions` 中
   运行前写死；两次重跑字节零差异，无事后调参痕迹。
   `scene_adjustments` 先于采集的修复彻底：两个 Editor 生成器均先
   `Apply` 再 `FindStaticRenderableRoots` 再审计（与
   `TetheredScenarioBootstrap` 同序），工件 `scene_adjustments_applied:
   true` + `relocated_vehicle_count: 6`，走廊构建器对该旗标 fail-closed。
3. **载体基准 779 自证** — `CONFIRMED`。`instance_count = 779 =
   road_audit_obstacle_count`（同一次遍历的 `RoadSceneAuditor.Audit`
   自证，builder 三值相等 fail-closed），未对 782 字面量断言；
   `runtime/road_scene_audit.json` 的 782 属 `p1-scene-004` 载体，
   不适用于本载体，工件以 `bc_body1_4_quoted_instance_count` /
   `bc_body1_4_count_conflict: true` 显式登记冲突。
4. **走廊工件唯一用途** — `CONFIRMED`（机械核对）。全库 grep：
   `corridor-prisms` 仅被 `build_m3_corridor.py`（构建/校验）与
   `config/p1-m3-body-001.json`（哈希钉住）引用；工具 2 只读
   scene-geometry 证据工件；批次 1 内运行时侧无任何消费者（策略属
   1a-β）。证据侧与 config 侧同源分身的设计使「唯一用途」可核对。
5. **接口契约完整性** — `CONFIRMED`。BC-M34-7 八项在契约文档 §1 逐项
   冻结且与既有代码行号核实相符（`packet()` 的 `command_id`、
   `BodyCommandReceiver.cs:77` 去重、`:99-103` 过期）；
   `controller/body_planner.py` 确为纯类型 + `ABC`，零策略、零走廊
   查询、零写入器（模块读毕核实；`body_entry.py` 仍是唯一发布者）；
   0.1° 死区在契约文档 §2 与 `limit_margin_deg` docstring 中正确表述为
   **非等价**，全部批次证据文本 grep 无「当且仅当」（唯一命中是引用
   禁令本身的句子）；waypoint 延后四条款（最迟批次 2 v2、v2 单独
   §4.3.1 停点、M4′ 不得预设、v2 只增不改）齐备；M4′ 三用例走查诚实
   （三处 ⚠️ 全部收敛到已延后的 waypoint）。`config/p1-m3-body-001.json`
   五个预注册值与提案 §3.5 逐字相同，`maximum_off_nadir_deg` 只记来源
   不复制，三个工件哈希与磁盘实测相符（测试锁定），estimator 节显式
   延后、未发明 `q_accel_mps2`。
6. **三处实质背离登记诚实性** — `CONFIRMED`。§3.2（窗 62.5 m/31.25 s
   非 ≈60 s）、§3.3（窗内中心误差中位对比 `0.82×` 远弱于整圈预扫
   `21×`，臂A 饱和占比 0.488 恰跨转折）、§5.2（779 vs 782）三处均以
   显著标记登记、附因果解释、声明「交接受角色裁定」且未淡化——数字
   本轮全部独立复现。三项已分别由 BC-BODY1-13/-14/-11 裁定，裁定内容
   与实测事实相符。

### 4. Acceptance round 3 追加三项

1. **BC-BODY1-12 的 R5 预注册文本缺陷登记** — `CONFIRMED`。
   `tools/check_scene_body_margin.py:47` 与 `:985-986` 确写
   「782 road-audit obstacle instances」，与同工件
   `identity.obstacle_instance_count: 779` 自相矛盾，位置与 round 3 所指
   逐行一致。核实其**不承重**：计算全部走 `geometry["instances"]`
   （779），R5 字符串仅为描述文本。修复划入 1a-β 且唯一准许改动为该
   计数描述——登记正确。另见 N2（同族字样还有一处）。
2. **BC-M34-4 (b) 的字面判据** — `CONFIRMED`。工件
   `c_geom.arm_b_lower_bound_with_box_occlusion = 0.5845070422535211`
   对 `0.565728`，增量 `+0.018779`（249/426 对 241/426），确为「期望
   可见性改变」的机械引用；`C_quality` 三分量在证据中保留为附加机制
   旁证，未被用作 (b) 判据。臂B 位移最大 `24.45 <
   sqrt(35²−25²) = 24.4949`（测试锁定）。
3. **「锚桅与缆绳不进遮挡几何」的代码层成立性** — `CONFIRMED`，但
   round 3 引用的机制不完整，结论不变：
   - 缆绳：`TetherLineVisual` 仅 `LineRenderer`（非 `MeshRenderer`、无
     `MeshFilter`、无碰撞体）→ 既不会被 `EvaluationOcclusionGeometry`
     建代理，也不可能被 `Physics.RaycastAll` 命中。round 3 的理由对
     缆绳完整成立。
   - 锚点标记：`TetherAnchor`（`TetheredScenarioBootstrap.CreateAnchor`,
     压扁圆柱）**本身带 `MeshRenderer`+`MeshFilter`**，「只从
     MeshRenderer 建代理」这条理由不足以排除它；实际保护机制是
     (i) 创建即 `Destroy(collider)`（raycast 不可命中），且
     (ii) 它是 `OcclusionGeometry.Build(anchorVisual, Drone, Target)`
     的显式排除根（不建代理）。结论「既不遮挡也不碰撞」在代码层
     双重成立；BC-BODY1-16 (c) 的披露文本引用机制时应以本条为准。

### 5. workflow §4.4 清单其余项

- **验收条件**：1a-α 交付物与 BC-BODY1-3 的 1a-α 清单一一对应；硬门 1
  先行且 fail-closed（工具 2 对非 `CLEAR` 锚点审计拒绝运行，测试锁定）。
- **坐标/单位/帧绑定**：全部世界系米/秒；`PlatformState` 仅承载 v3 帧
  已发布量（`SensorFrameWriter.cs` 字段核实）；`expires_after_s = 0.4 =
  2/capture_hz` 冻结入 config（测试锁定）。
- **边界与失败路径**：四个工具全部 fail-closed（身份哈希、schema、
  基准计数、锚门状态、TRS 不支持、无支撑/高程冲突路径均有测试或
  tamper 测试覆盖）。
- **真值泄漏**：本批新增运行时代码仅 `body_planner.py`（纯类型，无
  I/O）；`track_loop.py` 未触碰；工具 3 读归档真值属 BC-BODY1-7 明许的
  离线标定活动，入线形态仅 config 冻结标量。
- **消耗边界**：零 Play / 零 scenario/session/run ID / 零配额 / 零 API；
  两次 batchmode Editor 查询为 BC-BODY1-10 明许；场景字节前后同哈希
  （本轮重跑再次验证）。
- **文档一致性**：证据文件、契约文档、config、工件、状态板数字全部
  与本轮实测逐位一致。

### 6. Notes（PASS_WITH_NOTES 注记，须进入待办）

- **N1（1b/1c 前须处置）运行时相机 aspect 未被代码钉住，离线模型假定
  传感器 4:3。** `TetheredScenarioBootstrap` 只设 `fieldOfView`（垂直
  60°），从不设 `Camera.aspect`；`CoverageEvaluator.EvaluateVisibility`
  在 `OnFramePublished` 中运行，此时 `camera.targetTexture` 已被
  `SensorFrameWriter.Capture` 置回 null，故 `WorldToViewportPoint` 的
  aspect 跟随当时的 Game view/屏幕状态，而工具 2 按 `640/480` 建模。
  对 1a-α 门数**无影响**（本轮实测：426 样本视锥项全部 15/15，最坏
  视口坐标 x∈[0.4326, 0.5645]、y≤0.9407——束紧方向在俯仰，由 aspect
  无关的垂直 FOV 决定；遮挡项与 aspect 无关，故 (a) 缺口、(b) 增量、
  可见弧/测量窗全部稳健）。但 1c 的 `C_quality` 绝对值与
  `C_track|geom` 的 IoU 匹配都随运行时 aspect 缩放（这是 M0 冻结代码
  的既有属性，非本批引入）。**处置建议**：接受角色在 1b/1c 协议冻结前
  裁定——要么把用户 Play 时的 Game view aspect 固定为 640×480 并记入
  协议/证据，要么把钉住 `Camera.aspect` 列为经正规停点的后续代码变更；
  两臂同 aspect 故配对方向不受影响，但绝对量与离线投影对照须披露。
- **N2（1a-β 顺手项，扩权与否交接受角色）**：与 BC-BODY1-12 同族的
  「782」旧字样还有一处在 `tools/build_m3_corridor.py:8` 模块
  docstring（其 `:54-69` 注释与工件字段本身正确）。BC-BODY1-12 只授权
  改 `check_scene_body_margin.py` 的 R5 描述串；这一处是否并入同一
  勘误授权由接受角色裁定，本轮不扩大解释。
- **N3（1a-β 复核检查点）**：`PlatformState` 依 v3 帧承载
  `gimbal_saturated` 字段（诊断/run log 需要），而 BC-BODY1-6 禁止
  **策略**读旗标——契约 docstring 已写明该禁令，但机械上并未阻止实现
  读取。1a-β 复核须专项核对阈值策略实现零引用该字段。
- **N4（1c 分析工具设计约束）**：工具 2 的 `C_quality` 窗口切片按
  **各臂自身**的逐样本可见旗标过滤（本工件中两臂窗内恰好全可见，
  125=125，无实际影响）。1c 分析工具落地 BC-BODY1-2/-5 时须按里程
  配对并对可见性条件化做对称处理，避免两臂样本集不对称。
- **N5（措辞精度，非缺陷）**：遮挡归因中单个点样本可同时计入多个
  阻挡体（`blockers` 按 (点, 棱柱) 对计数），故「3069 中的 2808」应
  读作「2808 个被挡点样本的阻挡体清单含 Stadium」，逐实例计数之和
  （3493）大于被挡点总数属预期；工件字段名 `blocking_point_samples`
  本身准确。
- **N6（测试强度备忘）**：`test_module_exports_no_writer` 用固定名集
  等值判断（如 `write_command` 不会被捕获），实质属性本轮以通读模块
  核实成立；后续如在该模块加公共 API 请同步强化该测试。

### 7. UNITY_NA 立场

本批次未申领 `UNITY_NA`：Unity 列保持 `NOT_RUN`，验证义务由 1c 四门
（1a-α/1a-β 复核 PASS + 1b COORD-005 + 用户 Play）承接。**附议**：
这是正确分类——本批产物（审计/复算/标定/契约）最终服务于运行时行为，
不属"不影响 Unity 运行行为"的可豁免类，不申领即无须复核附议豁免。
证据 §12 交回的五项待裁均已由 acceptance round 3 裁定，裁定与本轮
实测无冲突。

### 8. Verdict

**Round 1: PASS_WITH_NOTES（candidate `81202ab`）。**

无阻断缺陷。BC-M34-4 (a)(b)(c) 的三个工具输出机械可复算性成立（本轮
全部字节级复现），接口契约完整，三处实质背离登记诚实，round 3 追加
三项全部核实（第 3 项机制表述以 §4.3 为准）。批次 1a-β 依 BC-BODY1-3
可以开工（含 BC-BODY1-12 修复）；N1 须在 1b/1c 协议冻结前由接受角色
处置；N3/N4 进入 1a-β/1c 的复核范围。

边界声明：本复核会话未修改任何实现文件；唯一写入为本文件、状态板交接
更新与轮换归档；复核副本已删除（`git worktree remove --force`）。

收工自检如实记录：`check_role_writes --role review`（工作区模式）报出
`docs/implementation-status.md` 与提案文件两个路径——经核实均为
**acceptance round 3 会话遗留的未提交批次**（本会话开始时的
`git status` 快照即含这四个文档改动，+29/+229 行为 round 3 停点裁定
记录本体），非本会话写入。按 AGENTS.md「不得覆盖/删减他人未归档内容」
不予恢复，留待接受角色自行提交；本角色只提交自己的三个白名单路径，
并以 `--base` 模式对本批提交单独复验通过。

---

## Round 2 — batch 1a-β（估计器 + 阈值策略 + 逐帧接线 + BC-BODY1-18…20 返工）

Date: 2026-08-07

- Accepted design: 提案 round 2 `ACCEPTED_WITH_BINDING_CLARIFICATIONS`
  （BC-BODY1-1…10）+ round 3 BC-BODY1-11…16 + round 4 BC-BODY1-17 +
  round 5 BC-BODY1-18…20（返工条款）+ round 6 §D release-to-review
  binding scope。绑定检查单 = 实现证据
  `docs/evidence/P1-M3-BODY-001-batch1a-beta.md` §10 十项 + round 6 §D 五点。
- Candidate: **`a234270`**（状态补记 `d9a0b11` 只改状态板/归档/证据 SHA，
  代码/config/tests/tools/Assets 零差异——本轮 diff 复核证实）。
  上一通过候选：`81202ab`（round 1）。实现增量按 `81202ab..a234270`
  逐文件核对；round 5 窄返工用 `db51792..a234270` 单独定位。
- 复核副本：`git worktree add --detach
  .claude/worktrees/review-P1-M3-BODY-001 a234270`，收工已删除。主树
  实现文件零修改。

### 1. 变更完整性与提交链归属

`git diff 81202ab..a234270 --stat`：17 路径，+3388/−99。逐提交归属本轮
自查：实现提交 `a1fc9a1`（1a-α SHA 补记）、`5340cf6`（1a-β 初版）、
`f8c3ea2`（候选补记）、`a234270`（返工）；穿插的 `6ef4e77`（Review
round 1）、`a67db45`（Acceptance rounds 3–4）、`db51792`（Acceptance
round 5）均只触碰各自角色的文档路径。实现侧 12 路径 =
`world_estimate.py`（新）、`body_planner.py`、`track_loop.py`、
`config/p1-m3-body-001.json`、两组测试、两个工具勘误、margin 工件重生成、
两份实现证据、契约文档、状态板。**零 `Assets/`、零 `.cs`、零
`config/scenario.*`、零协议文件**（`body_entry.py`/`protocol.py`/
`sensor_protocol.py`/`gimbal_entry.py` 不在 diff 中）——BC-BODY1-17 (b)
「不并入 `P1-EVAL-001`」与「零场景/协议字节」在 diff 层面成立。

条件 5 审计本轮复现：`--role implementation --base 81202ab` exit 1，
仅报提案与复核文件两路径（归属 Acceptance/Review，与 round 6 §B 一致）；
`--base db51792`（返工区间）exit 0，7 路径全部合规。

### 2. 测试与工具全部自跑（不采信报告数字）

| 项 | 实现者声明 | 本轮独立复跑（副本内） |
|---|---|---|
| `tests.test_m3_body_policy` | 29/29 | **29/29 OK** |
| `tests.test_m3_body_tools` | 56/56 | **56/56 OK** |
| 完整 Python 套件 | 424 / 1 失败 | **424 ran / 1 failure**，唯一失败 = `test_check_docs.test_compliant_minimal_status_passes` |
| 工具 2 `check_scene_body_margin.py` | exit 0，工件字节不变 | **exit 0**；重写出的工件 sha256 `c72c9407…9576d` = config 钉住值，`git status` 零改动 |
| `build_m3_corridor.py --check` | 779 棱柱，哈希不变 | **exit 0**：779 棱柱，sha256 `9e2956ad…c800` = config 钉住值 |
| Unity Edit Mode XML | 258/258 | **核验实文件**：`testcasecount=258 result=Passed failed=0`，2026-08-07 19:13:50Z |

- **唯一 Python 失败项归因附议**：`tests/test_check_docs.py` 与
  `tools/check_docs.py` 均不在 17 路径中（0 命中），失败与 round 1 在
  `81202ab` 上复现的同源——「既有失败、与本批无关、须用户授权协调批次
  修复」归因**成立**。
- **Unity XML 时间线如实定性**：XML 生成于 19:13:50Z，早于返工提交
  `a234270`（20:04Z）、晚于 1a-β 初版工作树成形——即它跑在返工**前**的
  实现树上。因 `81202ab..a234270` 全区间 C#/`Assets/` 字节逐位相同
  （diff 零命中），该结果对候选继续有效；证据 §8 的「返工零 C# 改动、
  结果继续有效」表述与此一致、诚实。
- 复现环境备注：round 1 的 26F+4E 环境性失败签名再现，本轮定位其完整
  资产集 = `runtime/models/`（含 **dinov2**，round 1 只记了 nanotrack）
  与 `runtime/yoloe/` 全目录；APFS 实体克隆补齐后 scene006 探针 26/26，
  全套即 424/1。

### 3. 证据 §10 十项逐条核查

1. **零真值/零可见性机械检查** — `CONFIRMED`，附一条强度备忘（N10）。
   本轮自跑 token 扫描：`CoverageEvaluator`/`WorldModelHandle`/
   `ground_truth`/`metrics.json`/`visible_arc`/`scene-body-margin`/
   `scene_geometry`/`road_data`/`EvaluationOcclusionGeometry` 在
   `world_estimate.py`、`body_planner.py` 及 `track_loop.py` 的
   `_platform_state`/`_body_step`/`_build_body_runtime` 全部零命中
   （仅禁令 docstring 自引）。`track_loop.py` 的 `metrics.json` 引用
   确属 qualification 收尾（`run_tracker` 内，非逐帧决策路径）——
   实质成立，但证据引用的行号已过时（见 N7）。
2. **§2 分支表逐字符合** — `CONFIRMED`。`initialize()` 未触碰（一次性
   `hold_body()` 仍在 `_rate_lifecycle is None` 分支内，init 记录无
   body 键，测试锁定）；rate/qualification 非空时 `_body_step` 先于任何
   副作用返回 `None`，且 `run_tracker` 与 `main()` 双层拒绝同用；无观测
   帧发布 `hold(no_observation)`；planner 返回值经 `RuntimePublisher.
   body_command` 唯一映射（`velocity` 实参顺序对 `body_entry.velocity
   (vx, vz, vy, expires)` 的非常规签名核实**正确**）；异常路径
   `hold(planner_exception)` 且 `planner_error` 入 run log 不吞。两道
   保险互不依赖：receiver 过期回落（C# 零改动）与本侧 fallback hold
   各自独立实现，互不引用。`_body_step` 只在 `is_latest` 帧运行，与
   云台发布同拍——与证据如实声明一致。
3. **走廊工件唯一用途与 fail-closed 加载** — `CONFIRMED`。全库 grep：
   `corridor-prisms` 仅 builder（构建/校验）、config（哈希钉住）、
   `body_planner.py`（schema 常量 + loader）；工具 2 零引用；运行时唯一
   查询 = `_corridor_blocked` 的线段 × 膨胀棱柱 slab 测试 + 0.05 m
   缩短/hold。`load_corridor_prisms` 的 schema/`instance_count` 相符/
   逐坐标有限/反向界四层校验齐备，无静默放宽；`_build_body_runtime`
   先验哈希再加载，半径 = `0.5 + 0.5 = 1.0 m` 由 config 两字段相加。
4. **N3：策略零引用 `gimbal_saturated`** — `CONFIRMED`。两个策略类源码
   零命中（机械测试 + 本轮 grep 复核）；文件内仅有的两处命中为
   `PlatformState` 字段声明与死区禁令 docstring——实质与证据一致，但
   证据行号 `:76/:92` 是返工前旧值，候选实为 `:85/:101`（N7）。
5. **BC-BODY1-12/N2 勘误未越界** — `CONFIRMED`。diff 恰为三处计数描述串
   （`check_scene_body_margin.py:47/:986`、`build_m3_corridor.py:8`）+
   工件重生成；`build_m3_corridor.py:54-69` 注释、
   `BC_BODY1_4_QUOTED_INSTANCE_COUNT = 782`、走廊工件的
   `bc_body1_4_quoted_instance_count: 782` / `bc_body1_4_count_conflict:
   true` 全部零改动。重生成工件与 `81202ab` 版逐字段独立比对：**唯一**
   差异 = `pre_registered_reductions.R5_occluders` 的 `782→779`，其余
   每个数值字段逐字节不变；哈希独立复算 `c72c9407…9576d` = config
   钉住值，`visible_arc_sha256` 不变。
6. **估计器** — `CONFIRMED`。量测射线重建与 `geolocate.box_ground_
   intersection` 逐项对映（同像素取点 = 框底边中心、同 `right·a −
   up·(v−cy)/fy + forward` 合成、同归一化、同 t 公式）；解析 Jacobian
   六列（两像素、三小转角 `n×w`、地高 `ray_x/ray_y`）数学本轮手工核
   对正确，数值微分交叉验证测试复跑通过；Joseph 形式
   `(I−KH)P(I−KH)ᵀ + KRKᵀ` 与 `K = P[:,:2]S⁻¹` 逐式核实；
   `Q = q²GGᵀ`、NIS、`dt<0` 即 `ValueError` fail-closed（测试锁定）。
   `del estimate` + 源码断言的「策略零读估计器」机械测试对当前 decide
   体量足够。四先验从 config 冻结值构造，`sigma_px` 走 calibration 节。
7. **BC-BODY1-18 措辞一致性** — `CONFIRMED`。config
   `priors_status`/四个 `*_derivation`、证据 §4、契约 §6 三处逐字对读：
   全部只称「事前未标定启发式先验」；`centripetal`/「向心」/「物理上界」
   全库扫描仅存于**撤回/否定句**内，无存活主张；
   `assertNotIn("centripetal", …)` 机械断言在测试中落地。derivation
   引用的事实抽查为真：`LoopTargetVehicle.cs:9` `turnRate = 240f`，
   `Step()` 平移 `position += direction·speed·dt`（即时换向），
   `turnRate` 仅入 `RotateTowards` 旋转朝向；`sigma_y_m` 引用的
   `0.05 m` 容差确在锚点合同文件（`support_height_tolerance_m`）。
8. **BC-BODY1-19 落地** — `CONFIRMED`。模块/类 docstring 与契约
   §1/§1.1 均按「有序输入历史 + 固定初态」表述，「arguments alone」
   旧句已废；迟滞确为单 `_moving` 布尔、构造时 `False`、每进程/trial
   新实例；`decide` 无 `open(`/`json.load`/`Path(`/`time.`/`input(`
   （机械测试 + 本轮通读）。全库发布点核查：`atomic_write
   ("body_command.json")` 仅在 `body_entry.py`；`body_entry.hold/
   velocity` 仅被 `RuntimePublisher` 两方法调用；后者仅被
   `initialize()` 一次性 hold 与 `_body_step` 唯一映射点调用——无第三
   发布点、无替代决策所有者（`body_entry` 自带的手动 CLI 为批前既有
   调试入口，不在任何 run 接线内）。
9. **BC-BODY1-20 fail-closed** — `CONFIRMED`。`_body_step` 发布块逐行
   对读：(a) 首错后**恰好一次** fallback hold（单层 try，无循环/重试）；
   原请求（`mode`/`reason`/`velocity_world_mps`）先记，发布结果分列
   （fallback 成功时 `published_mode: hold` + `published_reason:
   publish_failure_fallback`，原 velocity 不被记为已发布）。(b) 双错时
   `publish_error` + `fallback_error` 同帧保留，本帧记录先落盘，再追加
   `BODY_COMMAND_FAIL_CLOSED` 终态记录（`_record_terminal_error` 置
   `terminal`，`process_available` 永久返回 0，`run_tracker` 既有映射
   exit 2）。(c) 两个聚焦测试确实锁定命令槽终值（fallback hold /
   初始化 hold）、run-log 双错字段与进程继续/终止走向，故障注入为
   `OSError` 桩。(d) receiver 过期回落零触碰、零引用——两道保险互不
   依赖。
10. **run log 向后兼容** — `CONFIRMED`。`_append_record` 的 diff 仅
    新增可选参数与 `record.update(body_fields)`，既有键集**可证明**
    未变；`_record_terminal_error` 零触碰；新键都在 `world_estimate`/
    `body_planner` 两个新顶层键内；manifest `body_planner` 节仅在
    `--body-policy` 时出现（`body_identity is not None` 条件）；
    `test_no_body_wiring_keeps_records_unchanged` 锁定无接线运行零新键
    且唯一 body 发布仍是初始化 hold。

### 4. Round 6 §D 五点

均已在 §3 覆盖：(1) = §3.1/§3.4 + §3.6 的「策略零读估计器」；(2) =
§3.2/§3.8；(3) = §3.9；(4) = §3.5/§3.6/§3.7/§3.10；(5) = §2 全表。

### 5. workflow §4.4 清单其余项

- **坐标/单位/时间戳**：全部世界系米/秒；估计器与策略时间戳只走
  `capture_monotonic_s`（v3 校验器强制有限非负，见 N8）；
  `expires_after_s = 0.4 = 2/capture_hz` 冻结于 config 并由 builder
  校验为正。
- **边界与失败路径**：`_build_body_runtime` 对 schema/契约版本/
  scenario 身份/路线逐点地平面（`1e-9` 强检）/两个工件哈希全部
  fail-closed（tamper 测试覆盖）；`_platform_state` 任何字段缺失/非
  有限 → `None` → hold；`estimate is None` → hold（较严读法如实登记
  于证据 §9.5）。
- **真值泄漏**：零（§3.1）。
- **消耗边界**：零 Play / 零 scenario/session/run ID / 零配额 / 零
  API；本批零 Editor 侧查询（零 C# 改动）；Edit Mode 测试运行不产生
  ID。与证据 §1 一致。
- **文档一致性**：证据、契约、config、工件、状态板数字与本轮实测逐位
  一致，仅行号类小失准（N7）。

### 6. Notes（PASS_WITH_NOTES 注记，须进入待办；编号接 round 1）

- **N7（文档小失准，非缺陷）**：证据 §7/§10 引用的行号是返工前
  `5340cf6` 的旧值——`body_planner.py` 的 `gimbal_saturated` 两处合法
  命中实为 `:85/:101`（非 `:76/:92`），`track_loop.py` 的
  `metrics.json` 引用实为 `:1492/:1522`（非 `:1449/:1479`）。实质主张
  经本轮独立核实全部成立；后续引用请以内容而非行号定位。另：
  `world_estimate` 记录在 `GeometryRejected` 降级时会带
  `geo_reject_reason` 子键，证据 §6 的键清单未列（无兼容性影响）。
- **N8（防御性死路径备忘）**：`_body_step` 对 `capture_monotonic_s`
  取值失败的 `except ValueError: pass` 会把 `now_s` 留在 `0.0`；若该
  路径可达且估计器未初始化，会以 t=0.0 静默播种。经核实
  `FrameRepository.load` 的 v3 校验器强制该字段有限非负，故生产接线
  下不可达（已初始化情形也会因 `dt<0` 自报错）。任何未来改用非默认
  帧 schema 的接线必须重审此处。
- **N9（1c 观测建议，非义务）**：走廊缩短循环最坏 32 个候选 × 779
  棱柱线性扫描、无广相位，仅在持续被挡时发生；`_body_step` 自身延迟
  不单独入 run log。1c 若见帧延迟异常，此处是排查点之一。
- **N10（测试强度备忘，同 round 1 N6 性质）**：`MechanicalCheckTests`
  的禁令 token 扫描覆盖 `world_estimate.py` 与两个策略类源码，未覆盖
  `track_loop.py` 的 `_body_step`/`_platform_state`/`_build_body_
  runtime`（该部分本轮由复核 grep 补位核实为零命中）。批次 2 扩展
  决策路径时建议把这三个函数源码纳入同一机械扫描。

### 7. UNITY_NA 立场

本批次未申领 `UNITY_NA`，Unity 列保持 `NOT_RUN`。**附议**：分类正确——
估计器/策略/接线全部是运行时行为变更，验证义务由 1c 四门（1a-β 复核
PASS + `P1-EVAL-001` 复核 PASS + 1b COORD-005 + 用户 Play）承接，
不属可豁免类。证据 §12「无未决事项」与 round 5 裁定对读一致。

### 8. Verdict

**Round 2: PASS_WITH_NOTES（candidate `a234270`）。**

无阻断缺陷。BC-BODY1-18…20 三条返工条款逐条核实 FULFILLED；估计器
数学、§2 分支表、双保险独立性、发布失败 fail-closed、勘误边界与工件
字节不变性全部独立复现；测试与工具数字与声明逐位一致。N7–N10 为
非阻断注记：N7 属文档精度，N8/N9/N10 为后续批次备忘，均不构成返工
条件。候选可交 Acceptance 消费 verdict；按既定顺序 `P1-EVAL-001`
随后激活（自身停点），1b/1c/Play 在其后。

边界声明：本复核会话未修改任何实现文件；唯一写入为本文件、状态板
交接更新与轮换归档；复核副本已删除（`git worktree remove --force`），
副本内为复现测试临时补入的 gitignored 模型/归档克隆随副本一并删除。

---

## Round 3 — batch 1c（C# 真值载体 + 离线分析/证据链停点）

Date: 2026-08-08

- Accepted design: 提案 Acceptance round 11 §B、round 12 §B、round 13
  §B、round 14 §B、round 15 §B 五层 binding revisions + round 16
  `ACCEPTED — 1C_REWORK_R5_STOP_POINT_CONFIRMED`；操作单
  `docs/evidence/P1-M3-BODY-001-1c-preflight.md` revision 6。
- Candidate: **`e030310`**。上一独立复核通过的共享代码基线：`61ea20b`
  （P1-EVAL-001 round 1）。全区间 `61ea20b..e030310` 逐提交、逐文件
  核对；1c 实现提交 `1c26785`、`220a3af`、`a3c1f4e`、`977a997`、
  `e030310`。候选已推送（`origin/main` 含 `e030310`）。
- 复核副本：`git worktree add --detach
  .claude/worktrees/review-P1-M3-BODY-001 e030310`，收工已删除。主树
  实现文件零修改；全部读码/复跑/探针在副本内完成。

### 1. 变更完整性与提交链归属

`git diff 61ea20b..e030310 --stat`：24 路径，+4742/−108。逐提交归属
本轮自查：11 个非实现提交（`1b87c1d`/`6bde572`/`16a4da7`/`bd2db12`/
`bca5d84`/`3a40711`/`278b666`/`3ae4410`/`5888041` = Acceptance 决策与
状态记录；`d433eb0` = EVAL-001 推送授权代录；`df618cc` = 本角色
EVAL-001 round 1）只触碰各自角色文档路径；`a154982`（1b 证据 + 两帧
JPEG/JSON）与 `7e28ee4`（预检操作单 + `Scene006Visibility.cs`）属实现
文档/注释批次。实现实质代码 = `CoverageEvaluator.cs`（truth carrier，
`1c26785` 新增、`220a3af` 升 v2）、`M3BodyTruthEditModeTests.cs`(+meta)、
`tools/analyze_m3_body.py`、`tests/test_analyze_m3_body.py`。
`a3c1f4e`/`977a997`/`e030310` 零 `.cs` 路径——r3/r4/r5「零 C# 改动」在
提交层成立。零触碰：`controller/body_planner.py`、`world_estimate.py`、
`body_entry.py`、协议文件、`config/scenario.*`、`config/p1-m3-body-001*`。
`Scene006Visibility.cs` 恰 4 处 `///` 注释行号改符号定位，零代码语义，
与 round 10 §B.1/round 11 認定一致——运行时语义漂移为零。

条件 5 审计本轮复现：副本内 `check_role_writes --role implementation
--base 977a997` exit 1，唯一越权 = 提案文件（完整归因 Acceptance
`5888041`）；`--base 5888041` exit 0（7 路径全合规）。与 round 16 §A
条件 5 记录逐字一致。

### 2. 测试与工具全部自跑（不采信报告数字）

| 项 | 实现者声明 | 本轮独立复跑（副本内） |
|---|---|---|
| `tests.test_analyze_m3_body` | 24/24 | **24/24 OK** |
| 完整 Python 套件 | 448 / 1 既有失败 | **448 ran / 1 failure**（+1 环境性 skip：RATE-002 归档不在本机，历轮同类），唯一失败 = `test_check_docs.test_compliant_minimal_status_passes` |
| Unity Edit Mode | 267/267 | **本轮副本内重跑**：`testcasecount="267" result="Passed" failed="0"` |
| `build_m3_corridor.py --check` | 哈希不变 | **exit 0**：779 棱柱，sha256 `9e2956ad…c800` = config 钉住值 |

- **唯一 Python 失败项归因附议**：`tests/test_check_docs.py` 与
  `tools/check_docs.py` 在区间 diff 0 命中，失败与 round 1/2 同源——
  「既有失败、与本批无关、须用户授权协调批次修复」归因**成立**。
- **变异抽查（r5 证据 §3.1 声明核验）**：副本内禁用 init 唯一性检查后
  `test_update_row_relabelled_init_fails_closed` 立即失败——r5 新增
  测试确由新增逻辑承载；改动已还原，副本 diff 归零。
- 复现环境：APFS 克隆 `runtime/models`+`runtime/yoloe` 后全套即
  448/1（与 round 2 记录的资产集一致）。

### 3. C# truth carrier 独立核对（round 16 §B.2）

- **普通-run 门控** `CONFIRMED`：`M3BodyTruthAllowed` = 无 active
  experiment 且 `QualificationFrameDisposition.Ordinary`；调用点在
  qualification 门与 `EvaluateVisibility` 之后，RATE/qualification 帧
  零输出；Edit Mode 测试遍历全枚举锁定。
- **逐 Play 截断** `CONFIRMED`：writer 惰性创建 + `FileMode.Create` +
  随组件 `OnDestroy`/`OnApplicationQuit` 关闭——一 Play 一文件。
- **schema v2 字段** `CONFIRMED`：目标/机体世界坐标、
  `AppliedVelocity`（`TetheredDronePlant.AppliedVelocity`，
  `MoveTowards` 加速度限幅后的 plant 状态量，非 requested/published
  command）、可见性四元组、truth box/中心（−1 约定）、双饱和旗标、
  `capture_monotonic_s`+时钟 ID、逐帧生效评估 aspect；全部非有限值
  builder throw fail-closed（两个 Edit Mode 反例锁定）。
- **真值单向流出** `CONFIRMED`：全库 `m3_body_truth` 引用仅
  evaluator（写）+ 分析工具/测试（读）；`controller/` 0 命中（机械
  测试 + 本轮 grep）；v3 传感器元数据键零新增；planner/estimator 文件
  本区间零改动。

### 4. 离线分析链逐项核对（round 16 §B.3/§B.4）

以下全部经源码逐行对读 + 聚焦套件本轮复跑证实：生产
`tracking_iou_threshold` 键；容差推导（`OFF_ROUTE_TOL_M = 0.5+1e-3`
以生产 `LoopTargetVehicle.Step` `<0.5 m` 切点不吸附语义为前提，
`replay_loop_target` 与 `Step` 逐句等价，650 帧真实路线重放 + 超界
`+0.6 m` 反例）；里程投影/解卷绕/梯形权重边界补全（权重和=域长，首帧
与末段不丢）；窗 `[0,62.5]` 与整圈 `[0,P)` 两定义域分离，lap-2 帧不回
流；H1 三分支 `GEOMETRY_MODEL_REJECTED`/`WITHIN_RANGE`/
`SCENE_DEGENERATE` 与 BC-BODY1-15 逐字；`C_quality` 仅
`geometrically_visible ∧ truth_box_available` 窗内样本（遮挡带框帧
零进分母，反例锁定）；effort = Σ‖v_applied‖·Δt_sim（暂停 +300 s gap
指标逐节相等，requested 4 m/s vs applied 1 m/s 只认 applied）；H2 同
位置 0.5 m 网格配对差 + 改善为正号约定（中心误差 A−B）+ 第三分量冻结
指示量 `1[min_side≥20px]`（21→22 px 改善恰 0 反例）+ 逐 run-pair
中位数 5/5 同号 + naive「中位数之差」反例判 FAIL；十冻结 ID 顺序/
重复/错臂机械拒绝；三层 arm 身份（ID→期望臂→CLI policy→manifest
policy/planner→逐 update 帧 `body_planner.name`）；capture 逐帧非 bool
有限且与 truth ≤1e-9 绑定（缺字段反例）；manifest `init.frame_id`
非 bool 整数 `>=0`（`True`/浮点/负数/缺失全部落入判定式）；stage 枚举
恰一 init（ID 绑定 manifest）+ 其余全 update + 其他取值 fail-closed，
planner 核对确在划分之后（无「非 init 视作 update」残留）；三个隔离
反例 + 四个补充 stage 用例前缀断言、round-14 六反例全保留且在声明
阶段失败；compare `receipt.run_id==路径`、十哈希两两不同、
`init_frame_id` 入 identity_keys、`--output` create-once（无 output
即 exit 2）；`--verify` 删除全部外部依赖后仅从 run 目录逐字节复算。
生产侧对读：`track_loop._append_record` 恒写 `compute_stage`
（`"init" if event=="INIT" else "update"`，INIT 仅初始化路径一次）；
终态错误记录 `compute_stage: None` 且无 `record_kind`（按 frame 参与
分析）→ 新规则 fail-closed，r5 证据 §4 定性诚实；
`metrics.final.json` 由 `run_tracker` 收尾对普通 run 亦快照，
`evaluation_projection` aspect 核对满足 BC-BODY1-17 (d) 的 run 级
记录义务。r5 复核范围 §5 四项全部核毕；生产重放夹具 frame 0 改 init
不影响任何复算量（stage 不进指标计算，仅进身份链）——`CONFIRMED`。

### 5. 阻断缺陷（本轮新查出，返回实现角色）

**F1（阻断）：测量窗来源（margin 工件）在 1c 证据链内完全未绑定。**
六类 run-bound 输入中，`margin.json` 是唯一一个内容既不对冻结 pin
核对、也不进十-run compare 身份的输入——而它恰好定义主指标的测量域
`[0, 62.5 m]` 与可见弧。事实链：(i)
`config/p1-m3-body-001.json.measurement_window` 明确带
`artifact_sha256 = c72c9407…576d` 与 `visible_arc_sha256 =
4fe2eea5…df55` 两个 pin，且分析工具已加载同一份 run-bound body
config 读取 `route_sample_spacing_m`，却从不比对收集的 `margin.json`
哈希（receipt 的 `margin_artifact_sha256`/`visible_arc_sha256` 只
记录、无任何比较）；(ii) `compare_arms` 的 `identity_keys` 含
`scenario_sha256`/`body_config_sha256` 等 13 键，**不含** margin 两
键；(iii) `_collect_inputs` 对已存在的目标文件 `continue`——run 目录
被预置（或共享工件在十次分析之间漂移，该工件在 1a-β 已真实重生成过
一次）时，收集静默采用现存字节。副本内探针实证：预置
`measurement_window_m=[0,10]`、identity 匹配的 margin 后，分析成功且
窗口静默变为 `[0,10]`；两臂 margin 不同时 compare 仍会在缩小的公共
网格交集上"成功"。这与 round 14 §A.3/§A.4 被退回的 false-pass 同族：
逐 run 域可被无声改变而正式链无法察觉。修复方向（交实现角色）：
逐 run 强制 `sha256(margin.json) ==
body_config.measurement_window.artifact_sha256`（及 visible-arc 同
理），并把 margin 两键加入 compare `identity_keys`；配套预置/漂移
反例测试。

**F2（阻断）：操作单规定的开跑流程必然触发 `update_frame_planner_
mismatch`，每个正式 trial 都会被分析工具误杀。** 事实链：操作单
revision 6 §1「冻结初始框」行与 §3 步骤 2–3 规定——暂停于 `[2,10) s`，
以**保留的最低 frame_id** 初始化 tracker，恢复后「tracker 追平保留帧」。
生产代码 `track_loop.process_available` 以 `expected_ids =
range(last+1, latest+1)` 一次性补追全部保留帧（`:427-431`），批内仅
最后一帧 `is_latest`，`body_fields = self._body_step(...) if
is_latest else None`（`:564`），非 latest 帧照常 `_append_record`
（`:565-576`）——即批内前 `P−init−1` 条记录 `compute_stage="update"`
且**无 `body_planner` 键**（这是 round 2 复核已确认并接受的 1a-β
行为：「`_body_step` 只在 is_latest 帧运行」）。而
`analyze_m3_body.py:762-770` 对每条 update 记录强制 `body_planner`
mapping 且名称相等，缺键即 `update_frame_planner_mismatch:<frame>`。
按操作单执行的 trial 1 在暂停点前已发布 ~10–50 帧，初始化后第一次
poll 即产生该批次——**确定性失败，非小概率**；run 中任何 ≥0.2 s 的
控制器停顿（5 Hz 采集、`--poll-interval-s 0.02`，`backlog_count`/
`skipped_count` 本就是 run log 一等字段）同样触发。副本内探针实证：
在通过夹具上仅删除一条 update 行的 `body_planner` 键（= 生产补追行
的真实形态），整个 trial 被拒。后果：一次冻结的正式 Play 被消耗后
分析必然 fail-closed，且错误串与真实 planner 身份篡改**不可区分**。
根因是 round 14 §B.2 字面条款（「每条 update 帧必须有 body_planner
mapping」）与已复核接受的生产补追语义冲突——按 round 15 §B.4 纪律，
该冲突应退回 Acceptance 裁定而不是照字面落地。修复方向（表述权在
Acceptance）：让「planner 身份核对」只约束实际承载 body 决策的记录，
并用现有机械信号（`skipped_count`/批内非 latest 标记，或生产侧为补追
帧同样落 planner 身份字段）区分「未运行 planner 的合法补追帧」与
「身份被隐藏的 update 帧」，同时保留「至少一条合法 update」与相邻
反例。

两缺陷都在零 Play/零 ID/零指标状态下查出，无既有证据失效；候选退回
实现角色做窄返工后回到同一 §4.3.1 停点再交本角色。

### 6. Notes（非阻断注记，编号接 round 2）

- **N11（推导措辞精度，不影响容差值）**：`OFF_ROUTE_DERIVATION` 的
  垂直情形公式写 `d·L/(L+d)`，精确值应为 `d·L/√(d²+L²)`（仍严格
  `< d`，结论不变；真实路线 650 帧重放的实测上界是承重证据）。r3
  证据 §4「deltaTime 抖动只会使切点距离更小」方向说反（步长越细，
  切点距离越贴近 0.5 下方），但 `< 0.5` 上界与 dt 无关，容差有效。
- **N12（加固建议）**：分析侧对 tracker 帧记录的 `frame_id` 未做
  非 bool 整数类型检查（truth 侧有）；`True==1` 的字典别名不带来超出
  直接改写文件的新篡改能力，属一致性加固项，可与 F1/F2 返工顺手补。
- **N13（可选带子）**：truth 逐帧 `evaluation_aspect_width_over_
  height` 已记录但分析未与 sensor 宽高比对（run 级 metrics 快照已
  核对，BC-BODY1-17 (d) 义务已满足）；如需帧级带子可在返工时顺手加。
- **N14（命名备忘）**：`no_update_frame_with_expected_planner` 实际
  语义是「零条 update 记录」；名称略宽于行为，无功能影响。

### 7. UNITY_NA 立场

本批次未申领 `UNITY_NA`，Unity 列保持 `NOT_RUN` 等待 1c 四门后的用户
Play。**附议**：分类正确——truth carrier 是运行时行为、分析链服务正式
主指标，均不属可豁免类；formal Play/ID/指标在本 verdict 后继续冻结。

### 8. Verdict

**Round 3: REWORK_REQUIRED（candidate `e030310`）。**

F1（margin/测量窗未绑定）与 F2（操作单流程被分析工具确定性误杀）为
阻断缺陷，均属证据链 false-pass/false-kill 家族，必须在任何正式 Play
之前修复。其余复核范围全部 `CONFIRMED`：C# 载体、Scene006 注释清理、
容差/H2/自包含 verify/身份与 init/stage 绑定、全部既有证伪路径、测试
与工具数字逐位复现。round 1/2 的旧发现与已成立落点不受影响；arm A
trial 1、十次 Play、正式 run ID 与指标继续禁止。修复经 Acceptance
按 §4.3.1 回到同一停点后，本角色在新一轮复核 F1/F2 的闭合与反例。

边界声明：本复核会话未修改任何实现文件；唯一写入为本文件与状态板
交接更新（含轮换归档）；复核副本已删除（`git worktree remove
--force`），副本内探针与临时克隆的 gitignored 资产随副本一并删除；
探针造成的副本内改动在删除前已 `git checkout` 归零。本轮未推送任何
提交（无推送授权申领）。

---

## Round 4 — batch 1c round-6 返工（Review F1/F2 关闭核查）

Date: 2026-08-09

- Accepted design: Acceptance round 17 §B 六条（消费本角色 round 3
  `REWORK_REQUIRED`）+ round 18 `1C_REWORK_R6_STOP_POINT_CONFIRMED`；
  操作单 revision 7。复核范围按 round 18 §B：只复查 F1/F2 关闭、反例
  承重与 N15 定性，不重开 round 3 已确认的无关范围。
- Candidate: **`e438b97`**（已推送，`origin/main` 含之）。被退回候选
  `e030310`；上一独立复核通过共享代码基线仍为 `61ea20b`（其到
  `e030310` 的全量归因见 round 3，本轮维持）。
- 复核副本：`git worktree add --detach
  .claude/worktrees/review-P1-M3-BODY-001 e438b97`，收工已删除。主树
  实现文件零修改；全部读码/复跑/探针在副本内完成。

### 1. 变更完整性与提交链归属

`e030310..e438b97` 恰 4 个提交：`73890f7`（Acceptance round 16，4 文档
路径）、`51991a9`（本角色 round 3，3 白名单路径）、`419791b`
（Acceptance round 17，4 文档路径）、`e438b97`（实现 round-6，恰声明的
7 路径：分析工具、测试、操作单 r7、r3 证据勘误、r6 证据、状态板/归档）。
区间内 `Assets/**`、`*.cs`、`*.meta`、config、scenario **零命中**
（grep 0）；`docs/reviews/**` 仅本角色 `51991a9` 触碰。条件 5 审计副本
内复现：`--base e030310` exit 1 恰报提案与复核两路径（各归因
`73890f7`/`419791b` 与 `51991a9`）；`--base 419791b` exit 0（7 路径全
合规）——与 round 18 §A.5 逐字一致。

### 2. 测试与工具全部自跑（不采信报告数字）

| 项 | 实现者声明 | 本轮独立复跑（副本内） |
|---|---|---|
| `tests.test_analyze_m3_body` | 28/28 | **28/28 OK** |
| 完整 Python 套件 | 452 / 1 既有失败 | **452 ran / 1 failure**（+1 环境 skip），唯一失败 = 既有 `test_check_docs`（两文件区间 0 命中，归因附议不变） |
| Unity Edit Mode | 267/267 | **本轮副本内重跑**：`testcasecount="267" result="Passed" failed="0"`（本区间零 C#，回归确认） |
| 变异 A：移除 F1 pin 硬门 | 4 项失败 | **复现**：`test_preseeded_margin_window_is_rejected` + `margin_bytes_differ_from_pin`/`visible_arc_sha_differs_from_pin`/`margin_pin_missing` 三个 subtest 全部失败；还原后归零 |
| 变异 B：恢复 round-14 无条件 planner 读法 | 650 帧重放死于 `update_frame_planner_mismatch:1` | **复现**：真实重放以 `AnalysisError: update_frame_planner_mismatch:1` 终止——round 3 F2 的误杀在冻结输入上端到端重现，r6 分类正是解除项；还原后归零 |

### 3. F1 关闭核查 — `CONFIRMED`

- **门位**：`_require_pin_equal` 两调用位于 scenario identity 检查之后、
  `visible_arc`/`measurement_window_m` 首次取用之前——窗口的任何使用
  都在 pin 之后。
- **判定式**：`_sha256_hex` 要求 str + len 64 + 字符集 ⊆ 小写 hex——
  缺失（None 非 str）、类型错、大写、短串、非 hex 全部
  `sha256_not_hex64:<name>` fail-closed，且**两侧**（实际值与 pin）均
  过此检；不等 → `margin_artifact_pin_mismatch:` /
  `visible_arc_pin_mismatch:`。body config 缺 pin 键同样 fail-closed
  （`margin_pin_missing` 反例锁定）——happy 夹具因此必须携带真 pin，
  实测确带（`_write_configs` 写入实算哈希，未删 pin 规避）。
- **compare**：`identity_keys` 13→15，两个新键各有一条"十份中仅一份
  漂移"的失败测试（A4 margin / B3 visible-arc）承重。
- **round 3 攻击复演**：预置 identity 合法、窗口 `[0,10]` 的 margin
  现被 `margin_artifact_pin_mismatch:` 拒绝且不生成 analysis（专门
  测试 + 变异 A 证明该测试由 pin 门承载）。`_collect_inputs`
  create-once 行为保留，预置字节由 pin 拒绝——与 round 17 §B.1 字面
  一致。

### 4. F2 关闭核查 — `CONFIRMED`

- **分类与生产逐项对应**（副本内对读 `track_loop.py`）：
  `process_available` 对整批每行写 `backlog_count = len(processed)−1`、
  `skipped_count = 0 if is_latest else 1`，仅 latest 行运行
  `_body_step`；`initialize()` 的 INIT 行确写 `backlog_count=0,
  skipped_count=0`（本轮源码核实）。分析侧：`_counter` 强制非 bool
  非负整数；init 行 0/0；update 行 `skipped=0` → decision（必须带期望
  planner，backlog 可 0 可正——补追批的 latest 行形态被正确接纳）、
  `skipped=1 ∧ backlog≥1` → catch-up（`record.get("body_planner") is
  not None` 即拒，键缺失与值 null 同义，与 round 17 §B.3「键缺失或值
  为 null」一致）、其他 skipped 值 fail-closed；全 run 至少一条
  decision。
- **真实开跑重放**：650 帧集成测试改为 frame 0 init（0/0）+ frames
  1–4 单个补追批（全批 backlog=3，1–3 为 skipped=1 无 planner，4 为
  skipped=0 带 planner）+ 其余单帧批，窗口/H1/effort/truth 断言全部
  原值通过；两帧补追批测试锁定九个复算量节与基线逐字段相等（stage 与
  计数不进指标计算，round 3 判断维持）。
- **反例承重**：decision 缺 planner、catch-up 带 planner、
  `skipped=1/backlog=0`、未知 skipped、bool 计数、init 计数非零、全
  catch-up（`no_decision_update_frame`）七类全部前缀断言；round 14/15
  的 planner 篡改与 init/stage 反例全部保留且仍在原阶段失败（全套
  绿色）。变异 B 证明分类恰是解除 round 3 误杀的最小改动。

### 5. N15 定性与新注记（编号接 round 3）

- **N15（Acceptance round 18 披露，本轮核实定性：非阻断文字残留）**：
  模块顶层 docstring 仍写垂直情形 `d*L/(L+d)`，而 binding 的
  `OFF_ROUTE_DERIVATION` 常量（进入分析 JSON）、操作单 r7 与 r3 证据
  勘误均已改为 `d*L/sqrt(d^2+L^2)`。承重的是常量与工件，prose 不进任何
  判定；容差数值与行为无关。**定性：注记级**，与 N12–N14 同池，留待
  下一个实现批次顺手清理，本轮不扩大范围、不构成返工条件。
- **N16（新增，注记级加固项）**：分类只核逐行形态，不交叉核对批结构
  （生产不变量：同批行共享同一 backlog 值、catch-up 连跑长度 = 该
  backlog、紧随一条同 backlog 的 decision 行）。副本内探针：把一条真实
  decision 行改标 catch-up（skipped→1、backlog→1、删 planner）仍通过
  分析。裁量：该操作需要主动伪造 frames.jsonl，而同等伪造能力可直接
  改写 planner 名并同样通过逐行核对——receipt 哈希在首次分析才计算，
  预先的就地篡改本就在防伪边界之外（与 round 3 对 N12 的威胁模型
  一致）。**不构成新增绕过能力，非阻断**；如需加固可与 N12 同批实现
  批结构一致性检查。
- N11 已按字面落地（常量公式 + r3 证据两处带勘误标注、数值不变）；
  N12–N14 按 round 17 §B.5 保持未实现的非阻断建议——**附议**该边界
  纪律（未借机扩围）。

### 6. workflow §4.4 清单其余项

坐标/单位/时戳/帧绑定、真值单向流出、create-once/verify、消耗边界
（零 Play/ID/指标/配额）与 round 3 结论一致且本区间零相关改动；操作单
r7、r6 证据、r3 勘误、状态板数字与本轮实测逐位一致，r6 证据 §3.1 两项
变异声明均独立复现。

### 7. UNITY_NA 立场

本批次未申领 `UNITY_NA`，Unity 列保持 `NOT_RUN`。**附议**：分类正确
不变；分析链服务正式主指标，验证义务由 1c 四门与用户 Play 承接。

### 8. Verdict

**Round 4: PASS_WITH_NOTES（candidate `e438b97`）。**

无阻断缺陷。Round 3 的 F1/F2 两项阻断均已按 round 17 §B 字面关闭且
反例/变异承重；测试与工具数字逐位复现；范围冻结成立。N15/N16 与既有
N12–N14 为非阻断注记池，交下一实现批次顺手处理。候选可交 Acceptance
消费 verdict；消费后 1c 四门齐备侧的下一步（arm A trial 1 首跑退化门）
按操作单 r7 与 BC-BODY1-15 执行，Play 释放权在 Acceptance 与用户。

边界声明：本复核会话未修改任何实现文件；唯一写入为本文件与状态板
交接更新（含轮换归档）；复核副本已删除（`git worktree remove
--force`），副本内两次变异与探针在删除前已 `git checkout` 归零，临时
克隆的 gitignored 资产随副本删除。本轮未推送（无推送授权申领）。

---

## Round 5 — preflight r8 + revision 11 累计批次（`e438b97..7156f7e`）

Date: 2026-08-10

- Accepted design: Acceptance round 20 §B / round 21 §B / round 22 §C
  （re-anchor 环境预检 r8 三轮）+ round 29 §C（attempt-3 归因与 revision 11
  六条）+ round 30 §C（R11 round-2 六条）+ round 31 §C（R11 round-3 仅文档）
  + round 32 停点确认。操作单 = `docs/evidence/P1-M3-BODY-001-1c-preflight.md`
  revision 11。
- Candidate: **`7156f7e`**。上一个复核通过候选：`e438b97`（round 4
  `PASS_WITH_NOTES`）。复核区间按纪律取**累计** `e438b97..7156f7e`（29 个
  提交），不以实现者/接受角色声明的范围为边界。
- 复核副本：`git worktree add --detach
  .claude/worktrees/review-P1-M3-BODY-001 7156f7e`，收工已删除。主工作树
  实现文件零修改；全部读码、复跑、变异与探针在副本内完成。

### 1. 变更完整性与提交链归属

`git diff --stat e438b97 7156f7e`：**16 个路径，+4850/−149**。逐类核对：

| 类别 | 路径 | 核实 |
|---|---|---|
| 新普通工具 | `tools/preflight_reanchor_env.py`（+457） | round 21 §B.2 要求的新路径，非 `tools/check_*.py` |
| 工具修改 | `tools/analyze_m3_body.py`（+232） | ID 映射 + predecessor 门 + `--validate-completion` |
| 测试 | `tests/test_preflight_reanchor_env.py`（+626）、`tests/test_analyze_m3_body.py`（+401） | 对应两工具 |
| 协调批次 | `tests/test_check_docs.py`（±20） | `330bcf6`，见下 |
| 文档/证据/状态 | 其余 11 个 `docs/**` | 操作单、三份证据、状态板、归档、授权、提案、复核、Unity 日志 |

- **零 `controller/`、零 `Assets/**`、零 `*.cs`、零 `*.meta`、零 `config/`、
  零 scenario、零 models**（diff 层面 grep 0）。帧/控制协议、坐标与时间
  语义、主指标定义、阈值、planner、130 s watchdog 在本区间字节未动。
- **受保护基础设施零改动**：`git diff --stat e438b97 7156f7e -- 'tools/check_*.py'
  '.claude/**' 'docs/roles/**' AGENTS.md CLAUDE.md '.cursor/**'
  'tools/githooks/**' 'tools/rotate_docs.py'` 为空。
- **round 21 §B.1 恢复义务独立复核成立**：`tools/check_track_env.py` 在
  `34c1ec1` 与 `7156f7e` 上 SHA-256 同为
  `09e3b27e827eb319ac2c85a6468c07c89652900439c9bb14120c0d84bce73237`，
  `tests/test_check_track_env.py` 同样零净差；新工具内无该模块的代理、
  import 或兼容分支（读码核实）。中间候选 `8d5a923`/`78d8f91` 保留为
  可追溯的退修历史，未重写。
- **`tests/test_check_docs.py` 归因**：唯一改动来自 `330bcf6`
  「COORD-006: 修复 tests/test_check_docs.py 过时夹具（协调批次）」，提交
  信息逐字引用 `docs/authorizations.md`「2026-08-09 COORD-006」条目；本角色
  比对账本条目（授权范围＝只改夹具、不放宽检查项、不改 `tools/check_docs.py`）
  与实际 diff，**一致**，`tools/check_docs.py` 确实零改动。注意角色写入
  审计对 `tests/**` 放行，因此该路径不会被机械标出——本条归因是人工完成的。
  这也解释了 round 3/4 长期的「452/1 既有失败」在本轮清零。
- **条件 5 审计本轮自跑复现**（不采信接受角色数字）：
  `check_role_writes.py --role implementation --base e438b97` 原始非零，
  恰四条非实现路径；逐路径 `git log` 归因全部落在非实现批次——
  `docs/authorizations.md` → `78fdacb`/`09e1207`/`c55f4ad`；proposal →
  `fc08890`…`daefe35` 的 14 个 Acceptance 批次；`docs/reviews/**` → 仅
  独立复核 `9dac378`；`docs/unity-test-log.md` → `34c1ec1`/`9fb9b49`/
  `72916f6`/`6d293f5`/`e8c2ca0`/`68f35a2`/`c53a075`。精确区间
  `--base daefe35` exit 0（四文档路径）。**无实现角色越权写入**。

### 2. 测试与工具全部自跑（不采信报告数字）

副本内以主树 `.venv-track` / `.venv-yoloe` 解释器运行（副本自带 `PROJECT_ROOT`，
gitignored 权重以 APFS clone 补入）：

| 项 | 实现者/接受角色声明 | 本轮独立复跑 |
|---|---|---|
| `tests.test_analyze_m3_body`（`-m unittest` 入口） | 50/50 | **50/50 OK** |
| `tests/test_analyze_m3_body.py`（直接文件入口） | 50/50 | **50/50 OK**（B5 单一 main guard 成立） |
| `tests.test_preflight_reanchor_env`（两入口） | 36/36 | **各 36/36 OK（1 skip）** |
| 完整 Python 套件 | 510/510（1 skip） | **510 ran / 0 failure（2 skip）** |
| 真实 `.venv-yoloe` 预检 | `PASS`/0 | **exit 0**，stdout 恰一个可 `json.loads` 的对象，`status=PASS`，`side_effect_identity.unchanged=true`，四包 raw 版本 `cv2 5.0.0`/`torch 2.13.0`/`torchvision 0.28.0`/`ultralytics 8.4.104`，三构造器与双模型 SHA 齐全 |
| 真实 `.venv-track` 预检 | exit 1、stdout 0 字节 | **exit 1，stdout 0 字节**，stderr FAIL JSON 具名缺 torch |
| 真实 attempt-3 hold（主树只读核对） | 两文件 + 两 SHA | **恰 `frames.jsonl` + `manifest.json`**；SHA-256 `8f9f3551…16b5` / `e5caa982…8a65`，与工具常量逐字相等；`runtime/runs/p1-m3-body-001-arm-a-trial-1` 与 `-attempt-4` 均不存在；`runtime/frames/` 为空 |

**全套 510 的失败面独立定性**：副本首跑为 25F+4E，全部集中在
`tests/test_scene006_probe.py` 与 scouting 用例；探针取出真实
`fail_reason = FAIL_WEIGHT_HASH`，即 gitignored 权重缺失。补入
`runtime/models`、`runtime/yoloe` 后 **510 ran / OK**。故「环境性、与本批
无关」的定性成立，本轮**未**把它记为实现缺陷。skip 计数 2 vs 声明 1 属
解释器差异（互补 skip），非分歧。

### 3. 新增代码逐项核查

#### 3.1 attempt-4 采集 ID → canonical A1 映射 — `CONFIRMED`

`canonical_trial_id()` 三分支读码核实：attempt-4 → canonical A1；旧 A1 →
`run_id_void_consumed`（永久拒绝）；其余任何后缀/错臂/错序 →
`run_id_not_frozen_trial`。`_expected_policy()` 现在先过映射再定臂，
`expected_acquisition_ids()` 只在 A 臂首项替换。旧 A1 ID 在可执行路径
（模块 Usage、compare 示例、操作单 §3 step 5、§4 CLI）已全部消失，只作为
`A1_CANONICAL_TRIAL_ID` 常量与 receipt 字段存在——round 30 B1/B2 在
**这些**位置已闭合（§4 的例外见 F3）。A1 receipt 五字段实现且只对 A1 附加
（`test_receipt_carries_a1_binding_only_for_a1` 对 A2 断言零泄漏）。

#### 3.2 predecessor hold 真实字节门 — `CONFIRMED`

`_check_a1_predecessor_hold()` 位于 `analyze_trial` 内、**`_collect_inputs`
之前**（读码逐行确认门位），只枚举直接文件名并对原始字节取 SHA，不解析
void 内容、不算任何指标——**附议**「不违反禁止分析 void 工件」。四个具名
失败齐备；五条反例（缺目录/多文件/少文件/两种字节 mutation）每条都另断言
attempt-4 run 内零收集输入、零 `m3_body_analysis.json`；`test_shipped_
predecessor_constants_are_the_round29_values` 防止夹具 patch 掩盖出厂常量。
本角色另在主树只读复算了真实 hold 的两个 SHA，与常量逐位相等。

#### 3.3 完成握手 `--validate-completion` — `CONFIRMED`，并做了生产形态端到端实证

七个 AND 条件逐条与 round 30 §C.4 对映；PASS 只返回确认词，失败具名，
不调用 `finalize_run`、不写文件（`test_pass_path_returns_the_word_and_
writes_nothing` 以目录清单 + 逐文件 SHA 断言）。

测试夹具用的是**手写** `summary.json` 与 final JSON，因此本角色补做了
round 3 F2 同族的「按操作单跑会不会被自己的工具误杀」实证：

- 生产字段名对读：`track_loop.py:1536-1543` 的 final JSON 确有 `run_id` 与
  `summary` 两键；`run_log.py:387/491` 确产出 `actual_duration_s` 与
  `metrics_snapshot_present`。
- 语义对读：本 run 无 rate/qualification lifecycle，
  `measurement_elapsed_s = simulation_time_s − initial_simulation_time_s`
  （`track_loop.py:915-918`），而完成判据
  `elapsed_simulation_s = last_simulation_time_s − initial_simulation_time_s`
  （`:303-316`，`:588` 每帧更新）是**同一减法、同一操作数**，
  `actual_duration_s = max(measurement_elapsed)` 因单调而等于它。故
  `>= 130.0` 是**仿真时间**门，round 29 §C.4「墙钟不得替代仿真时间」成立，
  且不存在浮点误杀边缘。terminal 失败会令 `exit_code = 2`（`:1478`），
  由 exit-code 条件拒绝，方向 fail-closed。
- 端到端实证：用**真实** `controller.run_log.finalize_run` 生成 651 条
  5 Hz 生产形态记录的 `summary.json`（实测 `actual_duration_s = 130.0`、
  `metrics_snapshot_present = True`），以操作单 §3 步骤 4 的逐字命令形态
  （相对 `--runtime runtime`）跑真实 CLI：**exit 0，stdout 恰
  `TRACKER_AUTO_COMPLETE_CONFIRMED`**。绝对/相对路径两侧的 `.resolve()`
  口径一致，`summary` 路径比较不会误杀。**无 F2 同族误杀。**

#### 3.4 re-anchor 环境预检 — `CONFIRMED`

四包 raw `__version__` 直接比较、不规范化不剥 `+local`（`compare_raw_version`
读码 + suffix 反例）；cv2 pin 取 NanoTrack spec `opencv.tested_version` 的
披露读法与 round 22 §A.2 的 binding clarification 一致。round 22 §C.1 的
失败路径恒等成立：`before` 之后无论 `_construct` 正常返回还是普通异常失败，
`after` 都**恰执行一次**；有差异时错误同时具名 fingerprint delta 与原构造
异常，且不删除、不回写受污染现场。

#### 3.5 §5 终态分段（round 31 B6）— `CONFIRMED`

操作单 §5 现有两个并列段落与两张独立表：pre-tracker 表恰含
`TRIAL_VOID_PAUSE_WINDOW_VIOLATION` 与 `TRIAL_VOID_TRACKER_STARTUP_FAILURE`
并写明 run 目录未创建 / 采集 ID 未消耗；post-tracker 表恰含
`TRIAL_VOID_PROTOCOL_DEVIATION_POST_TRACKER_EARLY_EXIT` 并写明已创建 / 已
消耗 + 「不 `--finalize`、不分析、不重进」；另有三种各消耗一次 one-Play GO
的独立条目。终态名与触发条件字节未变。B6 逐字关闭。

#### 3.6 变异实证（哪些新门真的承重）

| 变异 | 结果 |
|---|---|
| 删除 `run_preflight` 失败路径的 after-fingerprint（回到 round-22 前行为） | `tests.test_preflight_reanchor_env` **4 项失败** → round 22 §C.1 承重 |
| 关闭 `--validate-completion` 的 `actual_duration_s >= 130.0` 门 | `tests.test_analyze_m3_body` **1 项失败** → 承重 |
| 删除 compare 侧 A1 五字段绑定核对 | **50/50 仍全绿** → **不承重**（见 N17） |
| 删除 `duplicate_canonical_trial_slot` 去重 | **50/50 仍全绿** → 该分支不可达（见 N18） |

四次变异后均 `git checkout` 归零，副本 `git status --porcelain` 为空。

### 4. 阻断缺陷

**F3（阻断）：冻结操作单 §2 的 Play 前隔离契约仍停留在 attempt-4 之前的
世界，既与 §1/§5 及已发布代码相互矛盾，又无法被逐字执行。**

事实链（全部以磁盘实测为准）：

1. **§2.2 的约束条与代码直接冲突。** §2.2 写「`runtime/runs/
   p1-m3-body-001-arm-a-trial-1/` 移动前后都必须**不存在**；冻结 ID 只能在
   新 GO 后由该次正式运行创建，这不是 ID 复用。」而 round 29 §C.2 之后，
   该 canonical ID 已被 attempt-3 void 现场永久消耗：同一份操作单 §1 的
   acquisition-IDs 行、§5 的 post-tracker 段，以及 `analyze_m3_body.py` 的
   `canonical_trial_id()`（对该串抛 `run_id_void_consumed`）三处都说它
   **不会**也**不许**再被创建。这正是 Acceptance round 30 B1 判为阻断的
   「冻结操作单会指向被拒 ID」同族，只是残留在 §2.2 而不是 §3 step 5。
2. **§2.2 自身已经执行完毕，却仍写成待执行。** §2.2 的开头是
   「返工期一律不执行本节移动。只有在用户新 GO 之后、新 Play 之前，先于
   §2 的六项隔离执行下列移动」，但它的三个目标
   `runtime/frames.arm-a-trial-1-void-attempt-1-hold/`、
   `runtime/m3_body_truth.arm-a-trial-1-void-attempt-1-hold.jsonl`、
   `runtime/metrics.arm-a-trial-1-void-attempt-1-hold.json` **在主树上都已
   存在**（attempt 2 之前就已执行，§2.3 自己也写「attempt-1 与 1b 的 hold
   逐项复核不变」）。§2.3、§2.4 都带「**已执行**」标记，唯独 §2.2 没有，
   因此它是 §2 里唯一被写成「下一次要做」的已完成动作。
3. **§2.1 的六项对 attempt 4 已不可执行。** 主树实测：`runtime/metrics.json`、
   `runtime/m3_body_truth.jsonl`、`runtime/scenario_config.json` 与三个
   publication 文件**全部不存在**（已在 attempt-1/2/3 保全中移走），而
   `runtime/frames.1b-diagnostic-hold`、`runtime/metrics.1b-diagnostic-hold.json`、
   `runtime/scenario_config.p1-scene-004.hold.json` 等目标**全部已存在**；
   `runtime/frames/` 为空目录。§2.1 结尾写「任一项与预期不符即停，回
   Acceptance，不得就地清理后继续」——逐字执行 §2 的操作者会在第 1 项就停住。
4. **§2.1 第 6 项核对的是错的目录。** 它要求核对「无
   `runtime/runs/p1-m3-body-001-arm-a-trial-1/`」，而 attempt 4 真正的
   create-once 前置是 `runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4/`
   不存在。该前置只在 §2.4（过去时的保全记录）里以「不得预建」出现，没有
   进入 §2 的 Play 前核对清单。（缓解项：`RunLogger` 用
   `mkdir(exist_ok=False)`，目录已存在会在 tracker 启动期炸掉；但那时
   run 目录已存在，与 §5 pre-tracker 段「run 目录未创建」的分类又冲突。）

后果与定级：操作单是这一次性、消耗 GO 的 Play 的逐字执行合同，本 work item
已经因协议偏差作废过三次 attempt。按 workflow §4.3.1 条件 1，实现范围与
**接口**必须冻结；§2 目前既不能执行、又与 §1/§5/代码给出相反的
「采集 ID 是否已消耗」结论，接口因此不成立。Acceptance 在 round 30 B1/B2 与
round 31 B6 对同一类残留文字均判停点不成立，本轮对 §2 采取同一标准。

修复方向（表述权在 Acceptance，本角色不代拟条文）：把 §2.1/§2.2 与
§2.3/§2.4 一样标注为已执行的历史记录，并另写一段**面向 attempt 4 的**
Play 前状态核对（预期：三个 publication 与 `metrics.json`/
`m3_body_truth.jsonl`/`scenario_config.json` 均不存在、`runtime/frames/`
为空、四组 hold 完好、`runtime/runs/…-attempt-4/` 不存在），并删除或改写
§2.2 中「冻结 ID 只能在新 GO 后由该次正式运行创建」这一与 §1/§5/代码
冲突的判定。

本缺陷在零 Play、零新采集 ID、零指标状态下查出，既有证据不失效。

### 5. Notes（非阻断，编号接 round 4）

- **N17（测试覆盖缺口）**：compare 侧的 A1 五字段绑定核对
  （`a1_attempt_binding_mismatch`）没有任何反例测试——变异删除整段后
  focused 仍 50/50。round 29 §C.6 点名要补反例的四类里，这一处是唯一
  只有正例的。功能上它与 `analyze_trial` 写入的常量同源，因而在合法链路上
  恒等成立，不构成新的绕过能力（与 round 3 对 N12、round 4 对 N16 的威胁
  模型一致），故非阻断；建议随 F3 返工顺手补一条「A1 receipt 五字段之一
  被改」的反例。
- **N18（不可达分支）**：`duplicate_canonical_trial_slot` 在
  `arm_a_ids`/`arm_b_ids` 已被逐字冻结序列拒绝之后才执行，集合大小恒为 10，
  分支不可达（变异删除后全绿）。语义上是无害的深度防御，但不应被证据文字
  当作承重门引用。
- **N19（文档与代码不符）**：`_check_a1_predecessor_hold` 在 `--verify`
  路径同样执行，因此 A1 的复核验证会读 run 目录**之外**的 void hold。
  副本内探针：删掉 hold 后 `--verify` 以 `a1_predecessor_hold_missing`
  失败。操作单 §3 步骤 5 仍写「复跑核验用 `--verify`：只读 run 目录，与
  存档逐字节一致」。只会 fail-closed、不产生错误指标，但 A1 的分析从此
  不能脱离 hold 独立复验，措辞应与实现对齐。
- **N20（夹具形态）**：`CompletionHandshakeTests` 用手写 summary/final JSON，
  没有一条走真实 `finalize_run`/`track_loop` 输出形态。本轮已由本角色端到端
  补证（§3.3），结论是通过；建议把那条生产形态回归固化进测试，避免下次
  生产字段改名时只有夹具跟着改。
- **N21（错误契约边缘）**：`run_preflight` 只把 `_construct` 内被显式包裹的
  异常转成 `PreflightError`；`config.raw["runtime"]`、
  `spec["opencv"]["tested_version"]`、`factory["name"]` 等取值抛出的
  `KeyError`/`TypeError` 会原样 `raise primary`，而 `main()` 只捕
  `PreflightError`，于是输出 traceback 而不是 `status=FAIL` 的 JSON。
  仍是非零退出 + stdout 0 字节，fail-closed 成立，属契约整齐度问题。
- **N22（macOS 现场脆性）**：`_check_a1_predecessor_hold` 要求 hold 的直接
  文件集合**恰为**两个文件。若 Finder 之类在 hold 目录落下 `.DS_Store`，
  attempt 4 的分析会在 Play 与 GO 都已消耗之后被
  `a1_predecessor_hold_file_set_mismatch` 挡死，而删除该文件又与「void 现场
  禁止删除」冲突。建议 Acceptance 事前写死这种情形的处置（例如允许忽略
  以 `.` 开头的非工件文件，或预先声明由 Acceptance 裁定）。
- **N23（残留文字）**：操作单 §6 的 revision-10 条目仍写
  「`p1-m3-body-001-arm-a-trial-1` 仍未创建」，而 attempt 3 已创建并已移入
  hold。该条是历史批次声明，但与 §2.4 直接矛盾，宜随 F3 一并更正。
- **N24（基线指针）**：§2.0 (b) 仍以 `git diff --name-only e438b97..H` 作为
  Play 前归因基线。本轮之后无论 verdict 如何，该基线都应更新为新的
  「上一个通过候选」，否则下一次 Play 前记录会对着过期基线做归因。
- **旧注记状态**：N11 已落地不变；**N15 仍在**（`analyze_m3_body.py` 模块
  docstring 第 50 行仍写 `d*L/(L+d)`，而 binding 常量已是
  `d*L/sqrt(d^2+L^2)`）；**N12 仍在**（分析侧 tracker 记录的 `frame_id`
  仍无非 bool 整数检查，truth 侧有）；N13/N14/N16 未实现。五项继续为
  非阻断注记池，**附议**实现角色未借本批次扩围。

### 6. workflow §4.4 清单其余项

- **坐标/单位/时间戳/帧绑定/过期语义**：本区间零 `controller/`、零 C#、
  零 config 改动，语义未被触碰；完成握手新增的时间判据经 §3.3 证实读的是
  仿真时间而非墙钟。
- **边界与失败路径**：预检的成功/失败双路径 fingerprint、分析器的四个
  predecessor 具名失败与七个完成握手具名失败均有反例；两处 fail-closed
  方向正确（宁可拒真，不放假）。
- **并发/原子性**：无新增并发面；预检显式证明零副作用（真实运行
  `unchanged=true`）。
- **真值泄漏**：无新增真值读者；predecessor 门只取字节 SHA，不解析 void
  内容，`test_no_controller_reads_m3_truth` 仍绿。
- **测试是否真的覆盖声明的行为**：四次变异给出了承重/不承重的机械结论，
  两处不承重已记为 N17/N18；其余声明逐项复现。
- **文档与代码相符**：这是本轮唯一失守的一项，见 F3 与 N19/N23/N24。

### 7. UNITY_NA 立场

本批次**未申领** `UNITY_NA`，Unity 列保持 `NOT_RUN`。**附议**该分类：
revision 11 改变的是正式 run 的绑定协议与完成判据，直接支配一次真实
Unity Play 的合法性，属于运行时行为，任何 `UNITY_NA` 主张都不成立；
预检 r8 虽是离线工具，但它是 Play 前置门的一部分，同样不单独申领豁免。
formal Play、采集 ID、分析与指标在本 verdict 后继续冻结。

### 8. Verdict

**Round 5: REWORK_REQUIRED（candidate `7156f7e`）。**

F3（冻结操作单 §2 与 §1/§5/代码相互矛盾且不可逐字执行）为阻断缺陷，
属证据链「按合同执行会走进相反分类或直接停摆」家族，必须在任何正式 Play
之前修复。除此之外本轮复核范围全部 `CONFIRMED`：累计 16 路径变更完整，
受保护基础设施与 `tools/check_track_env.py` 恒等成立，条件 5 四条非实现
路径全部独立归因，无实现角色越权；attempt-4→canonical 映射、predecessor
真实字节门、完成握手 AND 门与 re-anchor 预检四项新门逐条实现且（除 N17/N18
两处外）有承重反例；两入口 focused 50/50、36/36 与全套 510 全绿由本角色
自跑复现，`510` 的环境性失败面独立定性；完成握手经生产形态端到端实证
**不存在** round 3 F2 同族误杀。round 1–4 的旧发现与既有落点不受影响；
attempt 4、其余九次 Play、正式采集 ID、分析与指标继续禁止。

修复经 Acceptance 按 workflow §4.3.1 回到**同一停点**后，本角色在新一轮
复核 F3 的闭合，并复查 N17–N24 中被一并处理的项。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现文件。**
唯一写入为本文件与 `docs/current-status.md` 的交接更新。复核副本已删除
（`git worktree remove --force`）；副本内四次变异与全部探针在删除前已
`git checkout` 归零，`git status --porcelain` 为空；临时以 APFS clone 补入的
gitignored 权重随副本一并删除。主工作树在本轮全程只读（`git status
--porcelain` 在读码/复跑前后均为空），未运行任何会写入主树 `runtime/` 的
命令。本轮未推送任何提交（无推送授权申领）。

---

## Round 6 — revision 11 round-4（Review round 5 F3 返工闭合核查）

Date: 2026-08-10

- Accepted design: Acceptance round 33 §B 六条（消费本角色 round 5
  `REWORK_REQUIRED`）+ round 34 `R11_ROUND_4_STABLE_CANDIDATE /
  STOP_POINT_CONFIRMED`。操作单 = revision 11 round 4。
- Candidate: **`6019f33`**。被退回候选 `7156f7e`；上一个复核通过候选仍为
  `e438b97`，累计区间取 `e438b97..6019f33`（16 路径）。
- 复核副本：`git worktree add --detach
  .claude/worktrees/review-P1-M3-BODY-001-r6 6019f33`，收工已删除。主工作树
  实现文件零修改。
- **上下文披露（据实记录，交 Acceptance 判定）**：本轮与 round 5 在
  **同一会话**内进行，因此并非严格意义上的新鲜上下文。会话内不含实现或
  接受角色的任何转述，只有本角色自己 round 5 的读码与实测结果；为抑制锚定，
  本轮的全部结论均重新从磁盘读取、重新执行，未引用 round 5 的记忆结论。
  若 Acceptance 认为 §4.4/`docs/roles/review.md` 的新鲜上下文条款要求另开
  会话复核，本 verdict 应按其裁定处理。

### 1. 变更完整性

`git diff --stat 7156f7e 6019f33`：**7 个路径，全部 `docs/**`**。
`git diff --name-only 7156f7e 6019f33 -- tools/ tests/ controller/ Assets/
config/ '*.cs' '*.meta'` 为**空**；四个受关注实现文件逐一比对 SHA-256
（`tools/analyze_m3_body.py`、`tools/preflight_reanchor_env.py` 与两个测试
文件）在两个候选上**逐位相同**。故 round 5 §3 对四个新门的 `CONFIRMED`
在本候选上仍然成立，无需重开。

累计 `e438b97..6019f33` 仍为 16 路径，与 round 5 同一集合。

### 2. 测试与审计自跑

| 项 | 本轮独立复跑（副本内） |
|---|---|
| `tests.test_analyze_m3_body` 两入口 | **各 50/50 OK** |
| `tests.test_preflight_reanchor_env` 两入口 | **各 36/36 OK（1 skip）** |
| 完整 Python 套件 | **510 ran / 0 failure（2 skip）** |
| `check_role_writes --role implementation --base c923b9a` | **exit 0**（精确四路径） |
| `check_role_writes --role implementation --base e438b97` | 原始非零恰四条非实现路径，逐条自行归因：`docs/authorizations.md` → `78fdacb`/`09e1207`/`c55f4ad`；proposal → 16 个 Acceptance 批次；**`docs/reviews/**` 仅由 `9dac378`、`1a6e772` 两个独立 Review 批次写入**；Unity log → 7 个 Acceptance 批次。无实现角色越权 |
| `check_docs.py` / `git diff --check` | 均通过 |

### 3. F3 闭合核查 — `CONFIRMED`

round 5 F3 的四条事实链逐条复查：

1. **§2.2 与代码的冲突已消除。** §2.2 现以「时间边界」明确：旧 canonical
   `p1-m3-body-001-arm-a-trial-1` 在 attempt 1 保全**当时**尚未创建/消耗，
   原句「只能在新 GO 后由该次正式运行创建」只适用于当时；attempt 3 已创建
   并消耗该 ID 并移入 hold，**当前与未来一律不得再作为 acquisition ID 或
   run 目录被创建**，并逐字点名 `canonical_trial_id()` 的
   `run_id_void_consumed`。与 §1 acquisition-IDs 行、§5 post-tracker 段和
   已发布代码三方一致。
2. **§2.1/§2.2 已标注为历史。** 两节标题都加了「**已执行**」与日期，正文
   改为过去时并明写「本节不对未来任何 Play 发出指令」；「新 GO 后再执行
   这些移动」的现在时指令已删除。§2.1 原第 6 项的旧目录核对被降级为引用块
   并指向 §2.5。与 §2.3/§2.4 的标注方式现已统一。
3. **§2.1 六项不可执行的问题消失。** 它们不再是指令。
4. **create-once 前置改对了对象。** 新 §2.5 第 9 项要求
   `runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4/` 不存在，并显式
   禁止改用旧 canonical 目录作核对对象；还引用了 `RunLogger` 的
   `mkdir(exist_ok=False)`（`controller/run_log.py:508`）作为机械后盾——
   本角色 round 5 读码的同一行，复核无误。

**§2.5 九项状态核对由本角色在主工作树逐项独立执行**（只读，未写入任何
文件），全部与 §2.5 钉住值相符：

- 六个 shared 槽位（三发布 + `metrics.json` + `m3_body_truth.jsonl` +
  `scenario_config.json`）**全部 absent**；`runtime/frames/` 存在且 **0 项**。
- 四组 hold 计数 **257 / 93 / 109 / 257**，与 §2.5 逐一相等。
- attempt-1 truth **46 行** `64be7f85…39f2`、metrics `d31af400…2e7e`；
  attempt-2 truth **54 行** `7acd7a76…a64a`、metrics `f12ec093…2bbe`；
  attempt-3 truth **627 行** `6e273895…af50`、metrics `59085980…`、三发布
  hold `71fa8035…`/`372e6007…`/`b0dda5b0…`；1b 五个 hold 哈希齐全。全部
  与钉住前缀逐位一致，且这些哈希在实现证据 §B/§F.1/§H.1/§I.1 中确有对应
  出处（grep 命中）。
- attempt-3 run hold 恰两文件：`frames.jsonl` **755 行**
  `8f9f3551…16b5`、`manifest.json` **207 行** `e5caa982…8a65`。
- 四个 release/qualification 标记**全部 absent**。
- `…-attempt-4/` **不存在**；旧 canonical run 目录也不存在。

### 4. N19 / N23 闭合核查 — `CONFIRMED`

- **N19**：§1「真值载体」行与 §3 step 5 现都写明——`--verify` 对其余九个
  run 只读各自 run 目录，**对 A1 的 attempt-4 采集另读 run 目录之外的
  attempt-3 predecessor hold**，并注明该门只枚举文件名与取原始字节
  SHA-256、不解析 void 内容、不算 void 指标。与本角色 round 5 §5 的副本内
  探针结果（删掉 hold 后 `--verify` 以 `a1_predecessor_hold_missing` 失败）
  逐字相符。措辞与实现现已对齐。
- **N23**：§6 的 revision-10 条目已加时间边界，不再声称旧 A1 ID「仍未
  创建」；revision-8 条目也同步标注 §2.2 的移动已在 attempt 2 之前执行完毕。

### 5. 本轮 diff 的全量核对（不止 Acceptance 点名的部分）

操作单在本区间的**全部**改动为六处，逐处核实且无夹带：文件抬头新增
revision-11-round-4 说明；§1 真值载体行（N19）；§2.1、§2.2 改历史标注；
新增 §2.5；§3 step 5 `--verify` 说明（N19）；§6 两条历史句加时间边界
（N23）。其余 `docs/**` 为提案 round 33/34、实现证据 §L、状态板与机械归档。
**零现场移动/删除/覆盖/重算**——主树 runtime 的所有计数与哈希与 round 5
观测值逐位相同即为证。

### 6. Notes 状态

- **F3、N19、N23：关闭。**
- **N17（compare 侧 A1 五字段核对无反例）、N18（`duplicate_canonical_
  trial_slot` 不可达）、N20（完成握手夹具非生产形态）、N21（非
  `PreflightError` 异常绕过 FAIL JSON 契约）、N22（hold 目录混入隐藏文件
  会在 GO 消耗后挡死分析）**：本轮未处理。round 33 §C.2 明确本次文档返工
  不授权改测试、错误契约或 predecessor 两文件集合语义，**附议**该边界——
  在纯文档轮次里动这些反而会破坏「改动范围最小」的停点纪律。五项继续挂账，
  建议随下一个**代码**批次一并处理；其中 **N22 是唯一带操作时限的一条**，
  round 33 §C.2 已把它指派为「下一次 GO 前由 Acceptance 再做现场只读核对」，
  本角色**附议**并提请勿遗漏。
- **N24（基线指针）：仍开。** §2.0 (b) 目前仍写
  `git diff --name-only e438b97..H`。本 verdict 使新的「上一个通过候选」
  成为 **`6019f33`**，round 33 §C.3 所等的确切哈希现已存在；Acceptance 应在
  下一次 GO 前把该基线更新为 `6019f33`，否则 Play 前归因会对着过期基线执行。
- 旧注记 **N12、N15 仍在**（本区间零代码改动，如实登记）。

### 7. workflow §4.4 清单其余项

本区间零代码改动，坐标/单位/时间戳/帧绑定/过期语义、边界与失败路径、
并发/原子性、真值泄漏面与 round 5 结论一致且未被触碰；测试覆盖未变，
两入口与全套数字本轮重跑一致；文档与代码相符——round 5 唯一失守的这一项
现已闭合，且本轮另核实了操作单全文与磁盘现实的一致性（§2.5 九项）。

### 8. UNITY_NA 立场

本批次**未申领** `UNITY_NA`，Unity 列保持 `NOT_RUN`。**附议**：即便本轮是
纯文档批次，它修改的是支配一次真实 Unity Play 合法性的执行合同，不属可
豁免类；formal Play、采集 ID、分析与指标在本 verdict 后继续冻结。

### 9. Verdict

**Round 6: PASS_WITH_NOTES（candidate `6019f33`）。**

无阻断缺陷。round 5 的 F3 已按 round 33 §B 字面关闭：§2.1/§2.2 转为历史
记录并加时间边界、新增只读的 §2.5 状态门、create-once 前置改指
attempt-4 目录；N19/N23 同批关闭。§2.5 的九项由本角色在真实磁盘上逐项
独立执行，计数与哈希全部相符。代码与测试在本区间逐位未变，两入口 focused
50/50、preflight 36/36 与全套 510 由本角色重跑复现，两个写入审计的四条
例外全部独立归因。round 1–5 的旧发现与既有落点不受影响。

**本 verdict 不释放 Play。** 交 Acceptance 消费；按 round 34 §C.3，attempt 4
仍需：N24 基线指针更新为 `6019f33`、N22 的现场只读核对、以及用户另行逐字
授权的一次 one-Play GO。三者齐备前，attempt 4、其余九次 Play、分析与指标
全部保持冻结。

边界声明（逐字重申）：**本复核会话未修改任何实现文件。** 唯一写入为本文件
与 `docs/current-status.md` 的交接更新。§2.5 九项核对全程只读，未在主树
`runtime/` 创建、删除或改写任何字节（复核前后计数与哈希相同即为证）。
复核副本已删除（`git worktree remove --force`），临时以 APFS clone 补入的
gitignored 权重随副本一并删除。本轮未推送（无推送授权申领）。

---

## Round 7 — 强制闭环复核轮（loop-domain 修法 + A2 采集身份 + 操作单/COORD-007 复核债）

Date: 2026-08-13

- Accepted design: Acceptance round 42 `ACCEPTED_WITH_BINDING_CLARIFICATIONS`
  （BC-BODY1-23…31，授权 = 账本 2026-08-13「授权 G1 = F4+F2、G2 = (a)」条）
  + round 43 裁定（BC-BODY1-32/-33/-34、§B 七项、两门顺序写死、BC-25 更正）
  + round 44 §4.3.1 停点确认与 §D 复核范围。
- Candidate: **`07bb8a4`**。上一个复核通过候选 **`6019f33`**（round 6；该轮
  早于 COORD-007 R7，无 `passed_candidate` 机读行，属存量不回改，按交接与
  round 44 §C 的派生一致确认）。累计区间 `6019f33..07bb8a4` 共 **30 路径**，
  全部逐文件核对；实现者/接受角色声明的范围只作待核实主张。
- **开轮资格（§4.4 R1）本轮自验**：`git diff --name-only 6019f33..07bb8a4`
  在 PLAY_GOVERNING 上**非空，恰 9 条**——`tools/analyze_m3_body.py`、
  `tests/test_analyze_m3_body.py`、操作单
  `docs/evidence/P1-M3-BODY-001-1c-preflight.md`（round 40 裁定入集）、
  `tools/check_docs.py`、`tools/check_role_writes.py`、`tools/rotate_docs.py`
  （删除）与三个对应 `tests/test_*`。与 round 44 §C 声明逐字相符。本轮同时是
  §4.4 R3 条件 (3) 的**强制**闭环轮（修法触及 `analyze_m3_body.py`）。
- 复核副本：`git worktree add --detach
  .claude/worktrees/review-P1-M3-BODY-001-r7 07bb8a4`，收工已删除。按
  round 43 §B.7 把主树未跟踪的 A1 run 目录、attempt-3 hold 与
  `runtime/models`/`yoloe`/`p1-scene-006` **只读拷贝**入副本（cp 源侧零写入），
  使 `ArchivedRunLoopDomainTests` 与全套测试真跑而非 skip。主树实现文件
  零修改，全程 `git status --porcelain` 为空（复核前后各验一次）。

### 1. 测试与复算自跑（全部在副本内、BC-BODY1-34 钉住解释器）

| 项 | 本轮独立复跑 |
|---|---|
| focused `test_analyze_m3_body.py` | **67/67 OK**，`ArchivedRunLoopDomainTests` 四条真实字节用例**实跑非 skip** |
| A1 `--verify`（BC-BODY1-24 证明门） | **退出 0**，stdout 逐字 `{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}` |
| 全套 `discover -s tests` | **Ran 535，failures=1 + errors=1 + skipped=2**；两条不通过恰为既存 CSRT 对（`test_pinned_opencv_csrt_initializes_and_updates`、`test_cli_runs_pinned_csrt_to_a_versioned_summary`），与轮 39 §G/43 §D/44 §A.4 同一对；比主树多出的 1 条 skip 是 `test_rate3_protocol` 的 RATE-002 归档件缺失**显式 skip**（副本未拷该资产，环境差异非回归）。**零新增失败** |
| `test_check_docs.py` / `test_check_role_writes.py` | **13/13、14/14 OK**；候选树真实板 `check_docs.py` 退出 0 |
| 测试树哈希 | `07bb8a4:tests` = `4af739c2a4f1ff1a96259e4e80fd6b13dd95ccb4`；`test_analyze_m3_body.py` blob `cc83813f…`、SHA-256 `a3cf2681…f8f4f`；`analyze_m3_body.py` blob `c79a68ea…`、SHA-256 `e74350b9…2cb0d3` |

### 2. 变异探针（副本内执行，逐项 `git checkout` 恢复，收工 tracked 零残留）

1. **探针 A（BC-23/-25 承重）**：把整圈定义域段整体 revert 回
   `< P or >= 2P` 旧判据 → focused **恰 6 条具名测试红**（4 failures +
   3 errors，含 `ArchivedRunLoopDomainTests` 真实字节两条与
   `extra_laps` 两个 subtest），下界保留分支与其余 60 条全绿；恢复后
   67/67。与实现 §D 变体 B、接受轮 43 §A.2 互证，且本轮首次在**真实
   A1 字节**上复现（两者的副本当时无 `runtime/`）。
2. **探针 B（BC-32 承重）**：只删 `compare_arms` 新增的 18 行 A2 块 →
   **恰 12 条 `slot='a2'` subtest 红**（6 键 × wrong_value/missing），
   A1 侧 10 条 subtest、正向控制与其余全绿。与接受轮 44 §A.2 一致。
3. **探针 C（BC-27 承重）**：只删 `analyze_trial` 中
   `_check_a2_predecessor_hold` 调用 → **恰 6 条**
   `A2PredecessorHoldGateTests` subtest 红（缺目录/文件集偏差×2/三处
   字节篡改），其余全绿。
4. **探针 D（N12 落地承重）**：`tools/check_docs.py` revert 至
   `544cd18` → **恰** `test_milestone_rows_enter_echo_grammar` 红，
   其余 12 条绿；恢复复绿。`18a0aca` 提交信息按 R5 贴出的必失败输出
   与实测同名。

### 3. 债 1 — `analyze_m3_body.py` + 测试（BC 逐条核对，全部 `CONFIRMED`）

- **BC-BODY1-23**：`>= 2.0 * perimeter` 一支删除；下界与错误名
  `trial_invalid_no_single_loop` 逐字保留；两条具名域完整性门
  `loop_domain_sample_below_perimeter_after_closure:<idx>:<val>` 与
  `loop_domain_unwrapped_backward_step:<idx>:<prev>-><curr>` 落地，均对
  **整个序列**判定、硬 fail-closed、在任何写盘之前 raise（失败路径断言
  run 目录零输出）。
- **两门顺序（轮 43 §B.4 写死）本轮独立复推成立**：闭环后 `< P` 的样本
  与闭环样本之间必存在相邻回退步，故先判非递减会使闭环后门成为死代码；
  反之两样本均 `≥ P` 的回退只触发非递减门。两门可达性由探针 A 的
  6 条测试机械互证（`position_source={600: 520}` 同时构成回退步却报
  闭环后门名——顺序正确的直接证据）。
- **门为实义硬化而非死代码**：`_unwrap_mileage` 只在跳变超过 `P/2` 时调
  lap，半周长内的回退原样保留；超过 `P/2` 的前跳会被 `lap -= 1` 折为
  回退步——两个方向都被新门 fail-closed，方向正确（宁可拒真）。
- **`[0, P)` 域相互作用**：两门通过后，`unwrapped < P` 的样本集恰为闭环前
  前缀，故 H1 loop 域、window 域（`[0, 62.5]` ⊂ 首圈）与 `c_quality`
  series（取 window 域）都只依赖首圈前缀——`extra_laps` 两条测试断言的
  逐位不变有机械根据，轮 42 §A「第二圈不进 H1 也不再作废」成立。
- **BC-BODY1-24**：序列化仅 `a1_binding` 局部名改 `attempt_binding`
  （不进 JSON）；其余 run `**{}` 展开为零字段；输出 `sort_keys=True`；
  圈数不入 JSON（由既有 `domains` 字段派生）。`--verify` 逐字节门本轮
  自跑通过（§1）。
- **BC-BODY1-25（按轮 43 §B.1 更正后的口径）**：`two_loops` 改判为两条
  正向断言（合成 + 生产回放 1700 帧 > 3 圈）；`no_single_loop` 同步截断
  frames 后真正命中具名分支并钉住前缀；必失败测试 = 非递减 + 闭环后两条
  （探针 A 证实），下界为保留分支具名回归。反例 fixture 全部走
  `ProductionReplayRun`（真实 `config/scenario.default.json` + 冻结
  margin/body config + 行等价 Step 回放），**只重排回放坐标或截断**，
  零手造坐标；已归档通道 `copytree` 真实 A1 字节、真实 hold 常量不
  patch、缺资产显式 `skipUnless`。原 650 帧集成测试改用抽取类且断言保留
  （`ProductionReplayIntegrationTests` 逐条比对旧断言集，等价）。
- **BC-BODY1-26**：三常量逐字 = 轮 42 §B；`canonical_trial_id` 对两个
  已消耗 canonical ID 落 `run_id_void_consumed`（void 判定在 frozen 循环
  之前，旧 ID 不可能自映射）；其他 attempt 后缀落
  `run_id_not_frozen_trial`；`expected_acquisition_ids('a')[1]` = 新 ID、
  其余八个逐字不变、`TRIALS_PER_ARM = 5`——身份测试 + 探针 B/C 交叉锁住。
- **BC-BODY1-27**：`_check_a2_predecessor_hold` 只读、无指标（仅
  `is_dir`/`iterdir` 文件名/三个 `_sha256`），在 `_collect_inputs` 与一切
  写盘之前、仅 `run_id == A2_ACQUISITION_RUN_ID` 触发；十文件名集合与三个
  冻结 SHA 逐字 = 轮 42 §B 表（并被
  `test_shipped_a2_predecessor_constants_are_the_round42_values` 钉进测试）；
  A1 `--verify` 路径不受影响（§1 实测）；A1/A2 门互不依赖有测试。
- **BC-BODY1-32**：A2 逐键块在 A1 块之后、`arm_a_ids` 逐字序列校验
  （`analyze_m3_body.py:1520-1524`）**之后**执行，故 `arm_a[1]` 必为 A2；
  六键含 `predecessor_void_truth_sha256`，失败名
  `a2_attempt_binding_mismatch:<key>`（`.get` 使缺键同样命中）；
  **`identity_keys` 十五元组逐字未动**（diff 零触碰 + 正向控制测试断言
  其余八 run receipt 与六键交集为空、未篡改十 run 干净通过——该断言
  机械锁死"六键不进 identity_keys"）；**A1 分支逐字未动**（diff 中 A1 块
  零出现 + 探针 B 中 A1 侧 10 条保持绿）。
- **BC-BODY1-31**：区间零 `controller/`、零 `Assets/`、零
  `ProjectSettings/`、零 `config/`、零 C#/meta；主指标、`[0, P)` 域、
  `62.5 m` 窗、`130.0` watchdog、冻结初始框、CLI 其余参数在工具与操作单
  两侧逐字保留（§4 债 2 交叉核对）。
- **轮 43/44 对 §F/§F.8 的裁定逐条与落地相符**；A1 侧五键测试覆盖属
  round 5 **N17 请求的反例**，本轮判 **N17 关闭**（见 §7）。

### 4. 债 2 — 操作单 revision 12 + 轮 40/41/42 改动（`CONFIRMED`，两条新注记）

对 `docs/evidence/P1-M3-BODY-001-1c-preflight.md` 在 `6019f33..07bb8a4`
的**全部**改动逐 hunk 核对（含交接文字未点名的部分）：

1. **N24 闭合批次（`86c84bc`，round 35/36）**：§2.0 (b) 基线
   `e438b97` → `6019f33`，与 round 6 N24 的要求逐字对应。
2. **revision 12（round 39）**：§1 A2 钉住行、§2.5 转历史、§2.6 七项
   只读核对、§3 步骤 0′/门 1 记录型条款、§3 步骤 4/5 与 §4 CLI 的
   `--run-id` 轮换、§6 边界声明。**CLI 代码块 19 行恰 1 行不同
   （`--run-id`）本轮逐行复对成立**；暂停窗 `[2.000000, 10.000000)`、
   冻结初始框四分数、`212.9706`、`130.0`、`62.5/31.25`、全部 SHA 逐字
   保留；两条记录型条款只增停条件不放宽门，且 §4.1/§4.2 机器断言缺口
   （R10 未授权）在 §3/§6 双处逐字披露、未被记录型条款掩盖。
3. **round 40**：§2.0 (b) 计数更正为 7 条 + 第七条（操作单自身）单独
   定名 `RUNBOOK_DELTA_AUTHORED_UNDER_GO_NO_SEMANTIC_CHANGE_REVIEW_DEBT_
   REGISTERED`；BC-BODY1-21/-22 两条执行条款在 §2.0 落地。
4. **round 41**：§1 整圈定义域行两侧判据披露 + watchdog 行撤回「远低于
   两圈 213 s」；§5 新增具名终态行——其数字（`769.393 m` / `3.6127` 圈 /
   停留 `252.399 s` / 预算 `81.601 s`）用的是轮 41 §B **路线投影权威
   口径**，被禁止的弦长值 `83.197 s` 全文零出现（grep 验证）；四种终态
   各耗一次 GO；attempt-2 先例归属更正。
5. **round 42（`ed002f7`）**：§5 顶部**停用告示**（最高优先级）——
   revision 13 写出之前本操作单不得用于任何 Play，顺序 = BC-BODY1-28
   第 1–3 步之后才有 revision 13。
6. **本轮全套测试口径交叉验证**：操作单/证据引用的 focused 67、全套 535
   与两条 CSRT 失败由本轮自跑复现（§1）。

**残留失效文字全部有围栏、已被指派，不构成阻断**（详见 N25/N26）：
§1「本轮采集 ID」行、§2.6 第 7 项、§3 步骤 4/5、§4 CLI 仍写已被
BC-BODY1-26 永久拒绝的旧 ID `p1-m3-body-001-arm-a-trial-2`；§1 整圈
定义域行仍描述已撤下的 `>= 2P` 两侧判据（附过期行号 1034-1038，同类
过期行号另有 §1 的 :799 与 §2.6 的 1368-1373）。这些文字若被执行，
方向全部是**停**：§5 停用告示明令禁用，代码侧 `run_id_void_consumed`
拒旧 ID，`RunLogger` create-once 撞已存在目录，§2.6 第 7 项核对本身
不符即停。改写义务已由 BC-BODY1-28 第 4 步逐字指派给 revision 13。

### 5. 债 3 — COORD-007 R5 六条自检工具/测试路径（`CONFIRMED`）

- **覆盖边界确认**：`6019f33..544cd18` 段（`3d87524` R1–R9 落地、
  `c617a98` F4/F5 infra-fix、`538bdf1` F3 协调批次）已由 COORD-007
  复核轮 1–3 逐文件覆盖（轮 3 `passed_candidate:
  544cd18f425f6d0391d7d74368546c9eba527391`）；本轮对该段另做全量 diff
  扫描，`check_role_writes.py` 的 R2/R4/R5 落地（`--infra-fix` 模式、
  `tools/check_*.py` 通配、接受角色 `docs/evidence/*` 白名单、复核角色
  除外句）与已复核内容一致，`rotate_docs.py`/`test_rotate_docs.py` 删除
  （R9）后全仓仅剩两处历史提述，零活引用。
- **post-round-3 delta = `18a0aca` 一个提交**（本轮逐行复核）：
  `check_docs.py` 删除 `WORK_ID_RE` 形状前置，echo 执法判据改为
  Gate board token 表成员资格（含里程碑行），docstring 同步；
  `test_check_docs.py` 增 `test_milestone_rows_enter_echo_grammar`
  （夹具含 `M1` 里程碑 gate 行，裸引用拒/带 echo 过双向断言）。
  `WORK_ID_RE` 全仓零残留（grep 验证）。探针 D 证实必失败绑定；
  真实板通过且 13/13、14/14 绿（§1）。与接受轮 5 N12 裁定逐字一致。
- 措辞同步批次 `11a1b0b`（AGENTS.md + workflow，8+/5−）与账本
  2026-08-13 COORD-007 条目对应，非 tools/tests 路径，属协调批次凭据
  齐全。

### 6. 其余变更文件（30 路径全量归因）

- `docs/authorizations.md` **+201/−0 纯追加**：2026-08-13 的 trial-2 GO、
  「暂不决定」、G1=F4+F2/G2=(a)（含撤销关系与逐项授权范围）、COORD-007
  指令条逐字在账；BC-23…32 的授权链完整（账本 → 轮 42/43 → 落地）。
- `docs/reviews/P1-M3-BODY-001.md` 区间内 +160/−4：−4 全部是文件头
  Status 行随 round 6 更新，旧发现零删除（本角色自身批次，自归因）；
  `docs/reviews/COORD-007.md` 新增 = 该 ID 复核轮 1–3 记录。
- `docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md`（+106 纯追加，§N 现场
  事实）、`-arm-a-trial-2.md`（新增，§A–§I 结构完整：step (b) 报告含
  把 PLAY_GOVERNING 计数歧义**退回接受角色**的记录、§2.6 实测、解释器
  绑定落盘、三门、握手、fail-closed 分析、现场清点、§I.3 标注为诊断）、
  `-loop-domain-amendment.md`（新增，§A–§H 与代码逐条对映，本轮全文
  核对）；`docs/implementation-status.md`、`docs/unity-test-log.md`
  （+728，PRE_PLAY_RELEASED 事前记录 + 结果转录）均纯追加。
- `AGENTS.md`、workflow、`docs/roles/*`、`.claude/commands/*` 全部改动
  归因于三个带账本凭据的 COORD-007 批次（`3d87524`/`538bdf1`/`11a1b0b`），
  与 COORD-007 复核轮已确认的条文一致；`docs/roles/review.md` 的 R1/R4/R7
  新条款即本轮执行所依。状态板与归档：候选树真实板 `check_docs.py` 退出 0。
- **范围声明的一处小失准（记录，不构成缺陷）**：交接行与 round 44 §D.2
  把操作单债写作「轮 40/41/**43**」，git 实测区间内触碰操作单的接受轮为
  **35(N24)/39/40/41/42**（轮 43 未触碰）。声明的文件级范围（"全部改动"）
  覆盖正确，本轮按文件全量核对，不受该编号影响。

### 7. Notes（编号接 round 6；旧注记逐项过账）

- **N25（新，revision 13 改写清单——本轮验收其闭合）**：操作单在本候选
  上的失效文字（§4 已列：§1 A2 钉住行与整圈定义域行、§2.6 第 7 项、
  §3 步骤 4/5、§4 CLI 的旧 ID；三处过期行号 :799/1034-1038/1368-1373；
  watchdog 行的 `81.6 s` 论证在 F2 落地后已成历史背景）全部由 §5 停用
  告示围栏并已指派 revision 13（BC-BODY1-28 第 4 步：F4 条款、整圈
  定义域行改写、A2 采集 ID 钉住行、保全记录节）。**revision 13 的复核
  应逐项核对本清单清零。**
- **N26（新，基线指针，N24 同族）**：§2.0 (b) 仍手写基线 `6019f33`。
  本 verdict 落盘后「上一通过候选」由本文件首条 `passed_candidate` 机读
  行派生为 `07bb8a4`；revision 13 应把该行更新或改为按 R7 运行时派生，
  否则下一次 Play 前归因对着过期基线执行。
- **N27（新，N22 延伸到 A2）**：`_check_a2_predecessor_hold` 的十文件
  **精确**集合判等继承 A1 门的隐藏文件脆性——第 5 步保全移动创建 hold
  之后，Finder 等落下的 `.DS_Store` 会使 attempt-2 分析在 GO 已消耗后被
  `a2_predecessor_hold_file_set_mismatch` 挡死（fail-closed 方向正确，
  但代价高）；`iterdir` 只枚举常规文件，子目录不可见（与 round 30 已
  复核的 A1 形态一致）。建议接受角色在 revision 13 的保全记录节预先
  写死隐藏文件处置（N22 的既有请求扩展到 A2 hold）。
- **N28（新，Gate-echo 语义记录，非缺陷）**：echo 执法为**每行每 ID
  至少一次**（工具 docstring 与违规文案均写明「至少标注一次」）。本轮
  真实板探针：向已含正确 `M1` echo 的交接行追加裸 `M1` 引用**不**报违规
  （符合规格）；无 echo 的行裸引用被拒（`18a0aca` 的真实首抓即此形态，
  探针 D 复现）。属 COORD-007 轮 3 N13 同族的解析格式设计选择，如接受
  角色意图是逐处执法需另行立法。
- **N17：关闭。** compare 侧 A1 五键校验自轮 29 以来首次获得反例覆盖
  （`test_attempt_binding_mismatch_fails_closed` 的 10 条 A1 subtest，
  wrong_value/missing 双模式断言具名错误）；round 5 N17 所求即此。
  轮 44 §B.1 已裁定保留，本轮附议——零生产代码改动，纯测试加强。
- **N12、N15 仍在**（tracker 侧 `frame_id` 无非 bool 整数检查、模块
  docstring 第 58 行仍写 `d*L/(L+d)` 而 `OFF_ROUTE_DERIVATION` 常量为
  `d*L/sqrt(d^2+L^2)`——本区间未触碰对应行，如实登记）；**N18**
  （`duplicate_canonical_trial_slot` 不可达深度防御）**、N20**（完成
  握手夹具非生产形态）**、N21**（非 `PreflightError` 异常绕过 FAIL
  JSON 契约）**仍在**，本批未授权触碰，继续挂账；**N22 仍在**并由
  N27 延伸至 A2；**N24 已闭**（round 35/36），其后继形态即 N26。

### 8. workflow §4.4 清单其余项

- **坐标/单位/时间戳/帧绑定/过期语义**：新门只消费既有 `unwrapped`
  序列（米，路线投影），错误载荷 `.3f` 只进异常文本不进 JSON；帧绑定、
  时钟、过期语义零改动。
- **边界与失败路径**：两条新门与 A2 前驱门/身份门/compare 门共 15+ 个
  具名失败路径全部有反例（探针 A–C），失败时 run 目录零输出有断言；
  方向一律 fail-closed。
- **并发/原子性**：无新增并发面；create-once（run 目录、analysis、
  compare `--output`）语义逐字保留；门全部在写盘之前 raise。
- **真值泄漏**：无新增真值读者；A2 前驱门只取字节 SHA 不解析 void；
  `test_no_controller_reads_m3_truth` 本轮绿。
- **测试真实覆盖**：四路变异探针给出承重结论（§2）；`identity_keys`
  隔离由正向控制机械锁定。
- **文档一致性**：操作单失效文字全部有围栏且已指派（N25/N26），账本、
  证据、状态板与代码相符；round 44 §D 编号小失准已在 §6 记录。

### 9. UNITY_NA 立场

本批次**未申领** `UNITY_NA`，本轮**附议**该处置：候选零 `Assets/`、零
`ProjectSettings/`、零 `config/` 字节、无 C# 变更，不产生新的 Unity
回归面，这是"本批不产生 Unity 用例"（轮 43 §B.6/44 §C.3 的口径），
**不是** `UNITY_NA` 分类的适用情形，Unity 列既有状态不变。formal
Play、采集 ID、compare 与指标在本 verdict 后继续冻结。

### 10. Verdict

**Round 7: PASS_WITH_NOTES（candidate `07bb8a4`）。**

无阻断缺陷（CLASS_1/CLASS_2 零条）。三笔复核债同轮清偿：(1) loop-domain
修法与 A2 采集身份的全部 BC（23…27、31、32）逐条 `CONFIRMED`，四路变异
探针证实新门与新测试全部承重，BC-BODY1-24 零序列化扰动由本轮独立复跑的
A1 `--verify` 逐字节证实，两门顺序的可达性论证独立复推成立；(2) 操作单
revision 12 与轮 35/39/40/41/42 的全部改动逐 hunk 核对，冻结值零丢失、
被禁数字零出现、失效文字全部有停用告示围栏并已指派 revision 13
（N25/N26）；(3) COORD-007 R5 六路径的 post-round-3 delta（`18a0aca`）
逐行复核、必失败绑定复现，pre-544cd18 段与 COORD-007 轮 1–3 的既有
verdict 一致。focused 67/67（真实字节用例实跑）、全套 535 仅既存 CSRT
两条失败，由本轮在钉住解释器下自跑复现。round 1–6 的旧发现与既有落点
不受影响。

**本 verdict 不释放任何 Play。** 交 Acceptance 消费；按 BC-BODY1-28，
其后顺序为 revision 13（应闭合 N25/N26）→ 七项现场保全（含 BC-BODY1-33
排练；建议一并处置 N27）→ 用户新的逐字 GO（§G3 未答复）。候选未推送
（本地领先 origin），按 EVAL-001 先例待用户放行，与本 verdict 无关。

passed_candidate: 07bb8a47a9e41581c1450a7b0335e501ffdaaec9

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现
文件。** 主树唯一写入为本文件与 `docs/current-status.md` 的交接更新。
四路变异探针、`runtime/` 资产拷贝与全部测试运行都发生在一次性副本
`.claude/worktrees/review-P1-M3-BODY-001-r7` 内，探针逐项 `git checkout`
恢复并验证 tracked 零残留，副本收工 `git worktree remove --force` 删除
（未跟踪拷贝随副本消失）；主树 `runtime/` 未创建、删除或改写任何字节
（拷贝仅读源）。本轮未推送任何提交（无推送授权申领）。

---

## Round 8 — 操作单 revisions 13–18 复核债轮（轮 45…55 操作单改动逐文件核对）

Date: 2026-08-13

- 复核对象：状态板三处登记的复核债「revisions 13–18 与轮 45…55 的操作单
  改动欠一轮逐文件复核」（Current state Open obligations、交接行 Progress、
  Immediate next actions；各轮处置 `…REVIEW_DEBT_REGISTERED` 的登记不消灭）。
- Candidate: **`13bf9ddf9f0567b9a75fd9dce9a204feb084617e`**（HEAD，接受轮 55 +
  revision 18）。上一通过候选按 R7 由本文件最近一行 `passed_candidate` 派生
  = **`07bb8a47a9e41581c1450a7b0335e501ffdaaec9`**（round 7）。区间共
  **34 个提交、8 个路径，全部为文档**；测量侧（`controller/`、`Assets/`、
  `tools/`、`tests/`、`config/`、`ProjectSettings/`、
  `Packages/packages-lock.json`）diff **为空**——A1…A5 全部跑在 round 7 已
  复核的同一份代码上，本轮独立验证该声明成立。
- **开轮资格（§4.4 R1）本轮自验**：`git diff --name-only 07bb8a4..13bf9dd`
  在 PLAY_GOVERNING 上非空，**恰一条**——操作单
  `docs/evidence/P1-M3-BODY-001-1c-preflight.md`（round 40 裁定入集），
  +502/−28。触碰操作单的提交恰 8 个（`8149058` rev13 / `8dfadb4` 轮 46 勘误 /
  `ee40912` 轮 47 更正 / `70f788b` rev14 / `e867b0e` rev15 / `9816a5f` rev16 /
  `cd66f85` rev17 / `13bf9dd` rev18）；三个 (c) 轮（49/51/54）与全部实现
  执行批次对操作单**零字节**——与 BC-BODY1-21 的 Play 期冻结窗一致。
- 复核副本：`git worktree add --detach
  .claude/worktrees/review-P1-M3-BODY-001-r8 13bf9dd`，收工已删除。主树
  `runtime/runs`、`runtime/models` **只读拷贝**入副本（cp 源侧零写入）使
  归档字节用例与 `--verify` 真跑；主树实现文件零修改。

### 1. 测试与复算自跑（副本内、BC-BODY1-34 钉住解释器）

| 项 | 本轮独立复跑 |
|---|---|
| focused `test_analyze_m3_body.py` | **67/67 OK**（`discover -s tests -p`；dotted 模块名因 `tests/` 无 `__init__.py` 不可用，属调用方式非回归）；`ArchivedRunLoopDomainTests` 四条真实字节用例**实跑非 skip** |
| **五个 `--verify`（A1…A5）** | 全部退出 0 且**逐字复现各自冻结 receipt**：`0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` / `0.5783206310103214` / `0.5783243208518966`，均 `WITHIN_RANGE`、`window_c_track_given_geom = 1.0`——臂 A 5/5 的五个数字由本轮在副本内亲自复算，不转录任何角色报告 |
| F6 承重探针（副本拷贝内） | 移开 `…-arm-a-trial-2-void-attempt-1-hold/` → A2 `--verify` 立即 `ANALYSIS_FAIL_CLOSED:a2_predecessor_hold_missing:…`（退出 2）；恢复 → 退出 0 复现。机械证明 A2 的 `--verify` 读 run 目录**之外**的前驱 hold |
| §2.15 移动前钉住表（主树只读复算） | **八项全部相等**：destination `…-arm-a-trial-5-post-run/` 不存在；`frames/` 257 项聚合 `9dc67a7613201329b038ba6e425bc2e7aaa4ec7c9d196b09391c71624481a62b`（§B.3 口径亲自重算）；truth **731** 行 / 751891 字节 `a93ca5e0b2f67d164d8bfd079826ebef4d5328bb8e165e5362fe73f6c7bc80eb`；`metrics.json` 61/2101/`1804dd6f…`、`body_command` 10/208/`c98b0b75…`、`gimbal_command` 15/339/`02a3299a…`、`tracking_observation` 18/447/`215549ce…`；A5 run 目录**恰 11 份** |
| 树/blob 哈希 | `13bf9dd:tests` = `4af739c2a4f1ff1a96259e4e80fd6b13dd95ccb4`（与 round 7 记录逐字相同——代码零改动的独立旁证）；`analyze_m3_body.py` blob `c79a68ea…`（同 round 7）；操作单 blob `2761d00f8fdb4f3356601c2a6e9e1d90bd3035e7` |

### 2. revisions 13–18 逐 hunk 核对（含轮 46/47 两个更正批次）

对操作单在 `07bb8a4..13bf9dd` 的**全部** 8 个提交逐 hunk 核对；各修订抬头
声明与实际 diff 相符，未发现声明外的隐藏改动：

1. **revision 13（轮 45）**：槽位轮换到 BC-BODY1-26 冻结替代 ID；§1 整圈
   定义域行改写为只有下界 + 两条具名域完整性门（顺序按轮 43 §B.4，与代码
   `analyze_m3_body.py` 实序一致）；watchdog `81.6 s` 论证降历史背景；
   §2.0 (b) 基线改运行时派生（N26 闭合动作，**但例示命令有缺陷，见 F4**）；
   BC-BODY1-29/-30 落地（步骤 4 确认词后立即请退出、步骤 6 停留/圈数只记录
   不判定）；新增 §2.7（八项）/§2.8（七组保全 + 十文件精确集合 + 三钉 SHA +
   隐藏文件预写死 + BC-BODY1-33 排练）；revision 12 段加时间边界。
2. **轮 46 勘误**：BC-BODY1-33 只认直接调用 `_check_a2_predecessor_hold`，
   CLI 变体不合格——本轮对照代码独立证实：`missing_run_directory`
   （`analyze_trial` 起始）先于两个前驱门触发，勘误的事实主张**正确**。
3. **轮 47 更正**：§3 步骤 2 改为只要求报告「已暂停」，门 1 判据（保留帧
   机械导出）逐字不变——与轮 47 裁定一致，零门改动。
4. **revision 14/15（轮 48/50）**：同构轮换 A3/A4（canonical slot 即自身、
   无前驱门）；§2.9/§2.11 归档合同（A2 表：frames 257 聚合 `5af3b4d3…6882`、
   truth 773/796951/`79378d22…`；A3 表：257/`505b94df…5956`、751/774681/
   `3b38520f…`）；§2.10/§2.12 核对节；旧节转历史标注。
5. **revision 16（轮 52）**：**只**加 §2.13（A4 表：257 聚合 `281bb6d8…3b2c`、
   truth 1718/1755300/`f9c1a488…`），**不轮换槽位**（A5 当时无 GO）——
   保守方向正确。
6. **revision 17（轮 53）**：轮换 A5；新增 §2.14（七项，四个 `--verify` +
   四处归档聚合 SHA）；§2.8/§2.9/§2.11/§2.12/§2.13 五节失效标注就地更正 +
   §4 两处 revision 12 遗留括注更正，零参数改动（逐 hunk 证实）。
7. **revision 18（轮 55）**：**只**加 §2.15（A5 归档合同；钉住表与本轮主树
   实测**逐项相等**，见 §1）+ §2.14 转历史 + §5 执行前提改为「当前没有任何
   已授权的 Play」+ 臂 B 前置提示（`--body-policy threshold` 与
   `_expected_policy()` 复核）；**不轮换槽位**（臂 B 无 GO）。
8. **累计机械核对**：§4 CLI 块 19 行，`07bb8a4..HEAD` 累计恰 1 行不同
   （`--run-id`）；冻结值 token 多重集零丢失（`212.9706`、暂停窗、初始框
   四分数、`0.5645`、`130.0`、四种 void 终态名、两条域完整性门名、握手
   词等逐一比对，增量均可归因于定义域改写与修订抬头）；被禁弦长值
   `83.197` 全文**零出现**；唯一「待执行」节 = §2.15，与交接一致。
9. **N25/N26/N27 验收**：N25 清单逐项核对**关闭**——§1 A2 钉住行、整圈
   定义域行、§2.6 第 7 项、§3 步骤 4/5、§4 CLI 旧 ID 全部改写，`:799` 与
   `1034-1038` 两处行号去钉（**残留一处 §2.6 的 `1368-1373`，见 P3**，
   revision 13 抬头 F 的「三处」声明因此不精确为 2/3）；N26 手写基线已改
   运行时派生，**闭合成立但其机械化例示携带缺陷，延续为 F4**；N27 隐藏
   文件处置已预写死（§2.8 + §2.7 第 7 项，且前移到 GO 消耗之前）**关闭**。

### 3. 阻断 finding（编号续 round 3/5 的 F1–F3；与轮 41–42 修法选项名
F2/F4 无关）

- **F4（CLASS_2）—— §2.0 (b) 基线派生的例示命令取错方向。** 正文定义
  `<BASE>` =「`docs/reviews/P1-M3-BODY-001.md` 中**最新一行**
  `passed_candidate:` 的 40 位 SHA」（与 workflow §4.4 R7「最近一行」、
  `docs/roles/review.md` 一致），例示命令却是
  `grep -m1 '^passed_candidate:' …`——取**文件序第一个**匹配。复核轮次只
  追加（round 7 的该行在文件**末尾**），故文件一旦出现第二行
  `passed_candidate`，`grep -m1` 将永远返回**最旧**一行 `07bb8a4`，与规范
  句相反。当前恰一行、二者巧合一致；**下一个通过轮落盘之时即分歧**（本轮
  为 `REWORK_REQUIRED`、不写该行，分歧推迟到返工通过轮，但必然发生在下一次
  §2.0 (b) 执行之前）。**该例示是被实际执行的规程而非装饰**：A5 的 (c)
  记录（`docs/unity-test-log.md` PRE_PLAY_RELEASED 条）逐字记载
  「Baseline resolved at run time (N26): `grep -m1 …` → `07bb8a4…`」。失效
  方向：(b) 的路径归因对过期基线执行（diff 过含、证据锚点错误），不放宽门
  但违反 R7 派生契约。判据「操作员或工具的行为会不会因这段文字而不同」
  ——会。修复归接受角色（操作单作者）：例示改取最后一行（如
  `grep '^passed_candidate:' … | tail -1`），正文不动。仓库无处可写断言
  （`check_*.py` 属 infra、复核角色无 R5 例外）→ **`NOT_MECHANIZABLE`**，
  闭合 = 返工轮定点复看 §2.0 (b) 该段。
- **F5（CLASS_2）—— §1「acquisition IDs」行与 BC-BODY1-26 相悖。** 该行仍
  写「十个采集 ID：A1 = …-attempt-4（…）；**其余九个采集 ID 等于其
  canonical slot**」。自轮 42 冻结 A2 替代 ID
  `p1-m3-body-001-arm-a-trial-2-attempt-2` 起，「其余九个」对 A2 为**假**；
  revision 13 更新了「本轮采集 ID」行却漏掉本总表行，round 7 N25 清单亦未
  列它，遂存活至 HEAD。该行**无历史围栏、无改写指派**（revision 18 的臂 B
  修订清单不含它）。行为面：按此行推导 A2 采集 ID（如起草 compare 修订时）
  会得到被 `run_id_void_consumed` 永久拒绝的旧 ID——方向 fail-closed（机械
  停），但会误导 PLAY_GOVERNING 文档自身的后续起草。修复归接受角色：该行
  A2 处按 BC-BODY1-26 改写（A1、A2 双替代，其余八个等于 slot）。
  **`NOT_MECHANIZABLE`**，闭合 = 定点复看 §1 该行。
- **F6（CLASS_2，行为面为诊断路径）—— §1 真值载体行的 `--verify` 只读
  范围声明与 BC-BODY1-27 相悖。** 该行仍写「`--verify` 对**其余九个** run
  只读 run 目录；对 A1 的 attempt-4 采集另读…attempt-3 predecessor hold」。
  自 BC-BODY1-27 起 A2 的 `--verify` 同样读 run 目录之外的 attempt-1 void
  hold——本轮探针机械证实（§1：移开 hold → `a2_predecessor_hold_missing`
  退出 2）。§2.15 即将执行「复跑五个 `--verify`」，若 A2 失败，按此行会把
  病因误诊为 run 目录损坏而排除 hold——诊断行为因此文字而不同。修复归接受
  角色：该行改为「对 A1/A2 两个 attempt 采集各读其 predecessor hold，其余
  八个只读 run 目录」。同一过期声明存在于 `tools/analyze_m3_body.py` 模块
  docstring（本区间未触碰代码，登记为 N30 不入本 finding）。
  **`NOT_MECHANIZABLE`**，闭合 = 定点复看 §1 该行。

三条 finding 均为操作单文字与已接受 BC/常驻规则的相悖，**不质疑 A1–A5 的
有效性、轮 55 归因或任何冻结数值**（五个 `--verify` 由本轮亲自复现）；
**不阻塞 §2.15 的执行**（其合同文本与钉住表经本轮独立验证正确）。修复触及
PLAY_GOVERNING（操作单）→ 返工通过后按 §4.4 R1 开闭合轮资格自动成立；
操作单不属 R3 (3) 三个具名 Play 治理门文件，无强制闭环轮。**臂 B 修订不得
在未修正文本上起草。**

### 4. CLASS_3（闭集：时态/失效链接；接受角色独立复判后同轮应用，
不得改任何数字/哈希/run ID/disposition）

- **P1（§1「本轮采集 ID」行时态）**：行首「**本轮采集 ID（A5，revision 17）**」
  与行内「该 ID **从未被任何采集消耗**」为已执行步骤的时态残留（A5 已于
  2026-08-13 被有效消耗）。逐字替换：行首改
  「**上一采集 ID（A5，revision 17；已执行并于接受轮 55 判为有效）**」；
  「该 ID **从未被任何采集消耗**，**不需要**替代 ID」改「该 ID 发令前从未被
  任何采集消耗（现已被该次有效采集消耗，run 目录 create-once 已存在），
  当时**不需要**替代 ID」。已有围栏（§5 revision 18 执行前提「当前没有任何
  已授权的 Play」+ create-once），改写义务另已由 revision 18 抬头指派给
  臂 B 修订（「届时的修订必须同时改 §1 臂位行…」）——接受角色可择一时机。
- **P2（§4 抬头时态）**：「## 4. tracker CLI（本轮 = 臂 A trial 5，缺省值
  显式写出）」改「## 4. tracker CLI（最近完成轮 = 臂 A trial 5，已执行并判
  有效；当前无已授权 Play；缺省值显式写出）」；§4 尾注「**本轮 A5 =
  `p1-m3-body-001-arm-a-trial-5`，即其 canonical slot 本身**」改「**最近
  完成轮 A5 = `p1-m3-body-001-arm-a-trial-5`，即其 canonical slot 本身，
  已执行**」。围栏与指派同 P1。
- **P3（§2.6 残留行号钉，失效链接类）**：§2.6 第 4 项命令注
  「（`--verify` 在写盘前返回，`analyze_m3_body.py:1368-1373`，确为只读）」
  改「（`--verify` 在写盘前返回，确为只读；按模式名引用，不钉行号）」——
  与 §2.7/§2.10/§2.12/§2.14 同款注文一致；该行号在当前代码指向无关内容，
  revision 13 抬头 F「三处」去钉声明实际完成 2/3。§2.6 属已执行历史节，
  仅审计误导，无操作面。

### 5. 其余 7 路径（8 路径全量归因）

- `docs/authorizations.md` **+98/−0 纯追加**：§G3 答复（A2 attempt-2 一次
  Play）、「授权进行trail3」、「接受一下trail3并授权trail4」、「授权第五次
  trail」四条逐字在账，与各修订抬头引用一致。轮 52/55 引用的
  「trail4已经结束，归档」「trail5已经运行完成」**不在账**——二者只触发零
  消耗归档/判定动作，不属账本关键授权类，且修订抬头以「用户「…」」区别于
  「用户 GO「…」」，见 N31。
- `docs/unity-test-log.md` **+1249/−0 纯追加**：A2/A3/A4/A5 四条
  `PRE_PLAY_RELEASED` (c) 记录（各含发令时 HEAD、空 porcelain、8 路径 delta
  归因、预检退出码与 JSON、(d) 白名单断言）与四条结果转录；A5 (c) 记录的
  HEAD = `0c514f7`（轮 54 批次后、发令前），(c) 保持未提交贯穿 Play、事后
  由 `3f4d781` 零改动入库——提交序与 (d) 契约自洽。该 (c) 记录同时是 F4 的
  行为证据（`grep -m1` 被逐字执行）。**(c) 记录为冻结事前证据，返工不得
  触碰**（N29 的悬空引用修复只能走提案侧补记）。
- `docs/evidence/P1-M3-BODY-001-arm-a-trial-2.md` **+2458/−0 纯追加**
  （§K–§X）：§K 七组保全（含 BC-BODY1-33 直接调用排练）、§L/M/N（A2 三门/
  握手/绑定分析/BC-29 顺序）、§O–§Q（A3 链）、§R–§T（A4 链，F2 修法首例
  实弹：停留 `213.198013 s`/圈数 `3.243186` 零门触发）、§U（§2.13 归档）、
  §V（§2.14 77/77 + (b)）、§W/§X（A5 执行与现场清点）。抽查的钉住表
  （§2.9/§2.11/§2.13 移动前后相等、§2.15 前置）与操作单合同逐项相符。
- `docs/proposals/…-first-body-motion-closed-loop.md` **+819/−0 纯追加**：
  接受轮 44/45/46/47/48/49/50/52/53/54/55 各有节；**轮 51 无节**（其批次
  `36a9914` 只改状态板），而 trial-4 的 (c) 记录引用「rounds 50/51」——
  悬空引用，见 N29。
- `docs/implementation-status.md` **+81/−0 纯追加**：A2…A5 里程碑证据叙述，
  与 gate board/证据一致。
- `docs/reviews/P1-M3-BODY-001.md` +297/−3：−3 为文件头 Status/history 随
  round 7 的例行更新（`5d1fe0f`，本角色前轮自批次），旧发现零删除；
  `d099d5a`（轮 44）未触碰本文件——接受角色未预写 verdict，边界正确。
- `docs/current-status.md` 299+/317−：四个 chore 压缩批次（`c968f1c`/
  `0b08117`/`a069cdf`/`e4fc625`）按 COORD-007 R9 压缩旧 Log 叙述，指针/
  结论/未闭义务保留；各轮门 token 与交接更新（`d8762f6` 同批补漏更正）。
  终态一处失效文字：Immediate next actions 的轨道纪律段仍写「one released
  Play of `p1-m3-body-001-arm-a-trial-5`, not yet entered / one consuming
  row」——A5 已执行完毕，实际为 0 消耗 + 2 零消耗行（均在上限内），见
  N32（本轮状态板批次按「交接文字必须与现实一致」就地更正并在此记录）。

### 6. workflow §4.4 清单其余项

- **验收条件/坐标/单位/时间戳/帧绑定/过期语义**：区间零代码，冻结值 token
  多重集零丢失（§2.8），定义域改写与代码实序一致（轮 46 勘误对照
  `analyze_trial` 实序独立证实）。
- **边界与失败路径**：新增各节全部只增停条件（§2.7 第 7 项隐藏文件预检、
  §2.14 四 `--verify`、§2.15 五 `--verify`）；revision 16/18 在无 GO 时
  拒绝轮换槽位，方向正确。F4/F5/F6 均 fail-closed 方向，无门放宽。
- **并发/原子性/真值泄漏**：无新增面；(c)/(d) 时序契约在四条链上自洽。
- **测试真实覆盖**：focused 67/67 实跑（归档用例非 skip）；F6 探针承重。
- **文档一致性**：三条 CLASS_2 均属文字与已接受 BC/R7 相悖（§3）；其余
  修订声明与 diff 逐项相符；证据/账本/状态板互查一致（N29/N31/N32 除外）。

### 7. Notes（编号接 round 7）

- **N29（新）**：接受轮 51（A4 发令前置复算 + (c)）无提案节，其裁定只存
  于状态板 Log（已压缩）与 git；trial-4 (c) 记录「Rulings: proposal
  Acceptance rounds 50/51」为悬空引用。请接受角色在提案补记轮 51 节（内容
  归接受角色，本轮不代拟）；**不得**修改已冻结的 (c) 记录。
- **N30（新，N15 同族）**：`tools/analyze_m3_body.py` 模块 docstring 仍称
  「including `--verify`, is run-directory-only」——对 A1/A2 为假（两个
  predecessor hold 在 verify 路径同样强制，本轮探针证实）。本区间未触碰
  代码，如实登记，修复随下一个获授权的代码批次。
- **N31（新，信息性）**：轮 52/55 的触发话语「trail4已经结束，归档」
  「trail5已经运行完成」未入授权账本；二者只 gate 零消耗动作，修订抬头已
  用「用户「…」」与「用户 GO「…」」区分。如接受角色希望统一可追溯性，可
  考虑把此类触发话语一并入账；非缺陷。
- **N32（新，状态板失效文字，本轮已处置）**：见 §5 末条；本轮状态板批次
  就地更正，更正内容如实记于本条与状态板 Log。
- **N25：关闭**（残留 §2.6 行号钉一处 → P3）；**N26：关闭**（运行时派生
  已落地；例示缺陷延续为 F4，闭合以 F4 定点复看为准）；**N27：关闭**
  （隐藏文件处置预写死并前移到 GO 消耗之前，§2.7 第 7 项 + §2.8）。
- **N12、N15、N18、N20、N21、N22、N28 仍在**：区间零代码触碰，逐项过账
  不变；N22 的 A2 延伸（round 7 N27 注）已由 §2.8 隐藏文件条款吸收。

### 8. UNITY_NA 立场

本区间**未申领** `UNITY_NA`，本轮**附议**：四次 Play（A2…A5）均为用户真实
Unity 执行，三门/握手/Console 证据齐备并经 (c)/(d) 时序契约绑定；文档
修订自身不产生新的 Unity 回归面。Unity 列既有状态不变，无 `UNITY_NA`
分类适用情形。

### 9. Verdict

**Round 8: REWORK_REQUIRED（candidate `13bf9dd`）。**

三条 CLASS_2 阻断 finding（F4/F5/F6，均为操作单 PLAY_GOVERNING 文字与
BC-BODY1-26/-27 及 COORD-007 R7 的相悖，全部 `NOT_MECHANIZABLE`，闭合 =
返工轮定点复看具名段落）+ 三条 CLASS_3 逐字替换补丁（P1/P2/P3，交接受
角色独立复判分级后同轮应用）。**本 verdict 明确不推翻的事项**：A1…A5 的
有效性与轮 55 归因（五个 `--verify` 冻结 receipt 由本轮在副本内亲自逐字
复现）；revisions 13–18 的槽位轮换、归档合同与「零阈值/零门放宽」主张
（逐 hunk 证实）；§2.15 归档的可执行性（钉住表八项经主树只读复算逐项
相等，**§2.15 可照常执行，不因本 verdict 停摆**）。修复归接受角色（操作单
作者）；臂 B 修订不得在未修正文本上起草。复核债「revisions 13–18 + 轮
45…55」经本轮逐文件核对**清偿**，代之以上述三条具名 finding 的闭合义务。

按 R7，`REWORK_REQUIRED` 轮**不写** `passed_candidate` 行；「上一通过
候选」维持由 round 7 的机读行派生（`07bb8a4…`）。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现
文件。** 主树唯一写入为本文件与 `docs/current-status.md` 的交接更新（含
N32 的失效文字就地更正）。F6 探针与全部测试/`--verify` 运行都发生在一次性
副本 `.claude/worktrees/review-P1-M3-BODY-001-r8` 内（`runtime/` 资产为
只读拷贝，探针移动的是副本内拷贝并已恢复）；主树 `runtime/` 的 §2.15 表
复算全程只读（`ls`/`wc`/`shasum`），未创建、删除或改写任何字节。副本收工
`git worktree remove --force` 删除。本轮未推送任何提交（无推送授权申领）。

---

## Round 9 — 轮 8 返工闭合轮（F4/F5/F6 + P1–P3 定点复看；接受轮 56 批次）

Date: 2026-08-14

- 复核对象：接受轮 56 返工批次 **`408acd7`**（区间 `13bf9dd..408acd7` 恰一个
  提交、3 个路径：操作单 46+/15−、状态板 59+/51−、提案 +113/0；
  `docs/unity-test-log.md` **零字节**——冻结 (c) 记录保全，符合轮 8 N29 的
  禁改要求）。闭合方式按轮 8 verdict：全部 `NOT_MECHANIZABLE` → 本轮
  **定点复看具名段落**。
- Candidate: **`408acd7b39054e0a92eb3f0f9df5d4713b16f34a`**。上一通过候选仍由
  本文件最近一行 `passed_candidate` 派生 = `07bb8a4…`（轮 8 为
  `REWORK_REQUIRED`，未写该行）。**开轮资格（§4.4 R1）**：
  `07bb8a4..408acd7` 在 PLAY_GOVERNING 上非空（操作单）。
- **代码零接触，测试结论承接**：`408acd7:tests` =
  `4af739c2a4f1ff1a96259e4e80fd6b13dd95ccb4`、`analyze_m3_body.py` blob =
  `c79a68ea…`，与轮 7/8 记录逐字相同；累计 `07bb8a4..408acd7` 测量侧 diff
  **为空**（本轮实测）。轮 8（2026-08-13，本会话）在同一字节代码上的
  focused 67/67、五个 `--verify` 逐字复现与 F6 移开/恢复探针**继续有效**，
  本轮不重跑、不开副本（零实现代码接触；唯一探针用 scratchpad 合成文件）。

### 1. 定点复看（逐条闭合判定）

1. **F4 —— 关闭。** §2.0 (b) 例示改为
   `grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md | tail -1`，
   规范句「最新一行」逐字未动，缘由括注如实。行为探针（scratchpad 两行
   样例）：`-m1` 取旧行、`| tail -1` 取新行——修正方向正确。**自指验证**：
   本轮 verdict 的 `passed_candidate: 408acd7…` 落盘后，本文件出现第二行
   该标记，修正后命令在真实文件上返回**最新**行 `408acd7…`（提交前实测，
   见 verdict 块后记）；原 `-m1` 在同一文件上返回 `07bb8a4…`——缺陷若未修
   即在本轮成为实弹，修正恰在其生效前落地。
2. **F5 —— 关闭。** §1「acquisition IDs」行现为 A1（attempt-4）、A2
   （attempt-2，BC-BODY1-26 冻结、`run_id_void_consumed` 拒旧 ID）双替代 +
   「其余**八**个等于其 canonical slot」；依据列补轮 42/轮 56 标注。与
   BC-BODY1-26 及代码冻结表一致（轮 8 已对照 `expected_acquisition_ids`）。
3. **F5b（轮 56 自查，同类）—— 关闭。** §1「A1 采集 ID」行去「唯一替代」
   与「其余九个 ID 逐字不变」，改指 acquisition IDs 总表行并写明时间边界
   ——消除同一事实的第三处重复漂移源。
4. **F6 —— 关闭。** §1 真值载体行现为「`--verify` 对其余**八**个 run 只读
   run 目录；对 A1/A2 两个替代采集各另读 predecessor hold（A1 → attempt-3
   hold；A2 → attempt-1 void hold，BC-BODY1-27）」——与轮 8 探针实测的代码
   行为一致（hold 缺失 → `a2_predecessor_hold_missing` 退出 2）。
5. **F6b（轮 56 自查，同类）—— 关闭。** §3 步骤 5 同一声明同步改写：A1/A2
   双 hold 全路径（与真实目录名逐字相符）、两个门函数名并列、「其余八个」。
6. **P1/P2/P3 —— 关闭。** 三条 CLASS_3 补丁逐字应用（§1 A5 行「上一采集
   ID…已执行并于接受轮 55 判为有效/发令前从未被…现已被该次有效采集消耗」、
   §4 抬头与尾注「最近完成轮…已执行」、§2.6 注去行号钉改模式名引用）；
   CLI 19 行参数块一字未动（本轮 diff 复对）。接受轮 56 §B 逐条复判
   同意在案，符合 R4 通道。
7. **N29 —— 关闭。** 提案补记轮 51 节：补记声明写明一手来源（`36a9914`
   提交信息 + 状态板 Log）与「不改变任何当时裁定」；trial-4 (c) 记录的
   「rounds 50/51」引用自此可解析；冻结 (c) 记录零字节改动（numstat 证）。
8. **N31 —— 以有理由不采纳结案。** 接受轮 56 §C 依 AGENTS.md 账本范围
   （关键授权闭集）拒绝把零消耗触发话语入账，理由成立（稀释「账本没有 =
   未发生」边界）；「用户「…」/用户 GO「…」」的记载区分维持。本角色无异议；
   用户可随时改令。
9. **N32 —— 关闭。** 轮 8 已更正状态板轨道纪律段；轮 56 另更正 gate board
   Overall 格「await an archive contract」→「await the §2.15 archive
   execution (contract pinned by revision 18)」，与现实一致（合同已写就，
   待的是执行）。

### 2. 批次级核对

- **零冻结值改动**：返工 diff 全部改动行内 `212.9706`/`130.0`/初始框分数/
  暂停窗/`83.197` 命中 **0**；仅有的计数改动「九个→八个」即修正本体，与
  十 ID、双替代的现实一致（BC-BODY1-26 轮 42 原文即「其余八个」）。
- **新增 ID token 恰两个**且均为已冻结值：A2 替代 ID 与其 void hold 目录名
  （与 §2.7/§2.8/§2.9 既有冻结引用逐字一致）。
- **残留「其余九个/唯一替代」四处全部良性**：三处为历史修订块当时记录
  （revision 9 C2、revision 11 D、§5 revision 12 状态引文——轮 56 声明
  历史块不回改，本轮附议：回改历史批次记录反而伪造沿革）；一处
  「其余九个 trial」是另一含义（BC-BODY1-15 (c) 首跑门释放九个 trial 的
  协议合格状态，事实正确）。
- **revision 号不变**沿轮 46/47 先例；返工抬头具名处置
  `RUNBOOK_ROUND8_REWORK_TEXT_ALIGNMENT_TO_BC26_BC27_R7_NO_GATE_RELAXATION_
  CLOSURE_BY_TARGETED_REINSPECTION`，并逐字写明「本角色不给自己的修正签发
  通过」——闭合权留给本轮，边界正确。**§2.15 零触碰**（diff 证）。
- 状态板轮 56 批次：交接行把闭合轮点名交回复核角色
  （`AWAITING_A5_ARCHIVE_AND_REWORK_CLOSURE_REINSPECTION`）、Overall 格
  失效短语更正、Log 置顶条目；`check_docs` 于该批次提交时通过（钩子）。

### 3. Notes

- **N33（新，复核覆盖自省）**：F5b/F6b 与 F5/F6 同族（「唯一替代/其余
  九个」在 §1 A1 行与 §3 步骤 5 的另两处实例），轮 8 未点名，由接受角色
  独立核实时自查发现并披露修正。如实登记：轮 8 的操作单文字清扫在同族
  实例上非穷尽；本轮已对「其余九个/唯一替代/只读 run 目录」三个 pattern
  做全文残留清扫（§2 第 3 条），未再发现活性实例。
- **N30 仍在**：`analyze_m3_body.py` docstring 的 verify 只读范围声明过期，
  随下一个获授权代码批次修复（届时按 §4.4 R1 自动入复核范围）。
- **N12、N15、N18、N20、N21、N22、N28 仍在**：区间零代码触碰，逐项过账
  不变。**N25/N26/N27**：轮 8 已验收关闭；N26 随 F4 修正至此完全闭合。

### 4. UNITY_NA 立场

本批次纯文档、零 Unity 面，**未申领** `UNITY_NA`，本轮附议不适用；Unity
列既有状态不变。formal Play、采集 ID、compare 与指标继续冻结。

### 5. Verdict

**Round 9: PASS_WITH_NOTES（candidate `408acd7`）。**

轮 8 的三条 CLASS_2（F4/F5/F6）与接受角色自查的两条同类（F5b/F6b）全部
按处方修正并经本轮定点复看**关闭**；三条 CLASS_3（P1/P2/P3）经复判同意后
逐字应用**关闭**；N29 关闭、N31 有理由结案、N32 关闭、N26 完全闭合。零
冻结值/零门语义改动，历史修订块未被回改，冻结 (c) 记录零字节。操作单文本
自此与 BC-BODY1-26/-27 及 COORD-007 R7 对齐：**臂 B 修订可以在本候选文本
上起草**（其自身仍需按 revision 18 抬头轮换槽位与 `--body-policy` 并走
§2.0 四步）。§2.15 归档照旧归实现角色，本 verdict 不释放任何 Play、不
授权臂 B 任何一次采集。

passed_candidate: 408acd7b39054e0a92eb3f0f9df5d4713b16f34a

后记（F4 自指验证，提交前实测）：本 verdict 落盘后本文件含**两行**
`passed_candidate`；操作单修正后命令
`grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md | tail -1` 返回
`408acd7…`（最新，正确），原 `-m1` 形式返回 `07bb8a4…`（最旧，错误）——
F4 的修复在其缺陷首次可实弹化的同一时点生效。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现
文件。** 本轮零实现代码接触（测试树与工具 blob 哈希与轮 7/8 逐字相同，
测量侧累计 diff 为空，故未开复核副本、未重跑测试——轮 8 在同一字节上的
自跑结论承接）；唯一探针使用 scratchpad 合成文件与对已提交文档的只读
`grep`。主树唯一写入为本文件与 `docs/current-status.md` 的交接更新。

---

## Round 10 — 操作单 revisions 19–22 + 轮 58 的 20 处自查修复复核债轮

Date: 2026-08-14

- 复核对象：状态板三处登记的复核债「revisions 19/20/21/22 与接受轮 58 的
  20 处自查修复未被任何复核轮覆盖」（Current state Open obligations、
  Immediate next actions、Log 轮 61/63 条；B3 证据 §A.6 第 3 条同文登记）。
  Active handoffs 无单列复核行，按轮 8 先例以登记债开轮。
- Candidate: **`9cadebd05d4880b7703e46ee90e140f67b3b54fa`**（HEAD，B3 前置
  完毕 + 缺陷登记批次）。上一通过候选由本文件最近一行 `passed_candidate`
  派生 = **`408acd7…`**（round 9）。区间 **19 个提交、11 个路径，全部为
  文档**；测量侧（`controller/`、`Assets/`、`tools/`、`tests/`、`config/`、
  `ProjectSettings/`、`Packages/packages-lock.json`）diff **为空**（本轮
  实测）——A1…A5、B1、B2 与待跑的 B3 同在 round 9 已复核的代码字节上。
- **开轮资格（§4.4 R1）本轮自验**：`git diff --name-only 408acd7..9cadebd`
  在 PLAY_GOVERNING 上非空，**恰一条**——操作单
  `docs/evidence/P1-M3-BODY-001-1c-preflight.md`（round 40 裁定入集），
  +470/−48。触碰操作单的提交**恰 4 个**，全部为接受轮批次（`03cb2b5`
  rev19 / `4b76b64` rev20 / `41ff1bd` rev21 / `0af7344` rev22）；实现执行
  批次（`90f7b3b`/`eb6c96a`/`b6dcf86`/`5df2b99`/`29e903a`/`9cadebd`）对
  操作单、`docs/unity-test-log.md`、`docs/authorizations.md` **零字节**
  ——BC-BODY1-21/-22 与实现只读边界经逐提交 numstat 归因证实。
- 复核副本：`git worktree add --detach
  .claude/worktrees/review-P1-M3-BODY-001-r10 9cadebd…`，收工已删除。主树
  `runtime/runs`、`runtime/models` **只读拷贝**入副本（cp 源侧零写入）使
  focused 套件与七条 `--verify` 真跑；主树实现文件零修改，`runtime/` 只读。

### 1. 测试与复算自跑（副本内、BC-BODY1-34 钉住解释器）

| 项 | 本轮独立复跑 |
|---|---|
| focused `test_analyze_m3_body.py` | **67/67 OK**（副本内 `discover -s tests -p`）；`9cadebd:tests` = `4af739c2a4f1ff1a96259e4e80fd6b13dd95ccb4`、`analyze_m3_body.py` blob = `c79a68ea3042c2f96e33e7f7051b5786602c8304`——两哈希与轮 7/8/9 记录逐字相同，代码零漂移的独立旁证 |
| **七个 `--verify`（A1…A5 + B1 + B2）** | 全部退出 0 且**逐字复现各自冻结 receipt**：臂 A `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` / `0.5783206310103214` / `0.5783243208518966` 均 `WITHIN_RANGE`；**B1、B2 均 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`**——七个数字由本轮在副本内亲自复算，不转录任何角色报告 |
| B1/B2 运动量与直方图（副本内从 run 原始工件重算） | B1：effort `88.64522663177961` / 路径 `61.42306359956821` / 切换 **11**；decision 帧 **623** = `…+corridor_blocked` **324** + 滞回 116 + `below_trigger` 95 + `above_release` 82 + `…+corridor_shortened` 6；B2：`75.26945194958653` / `49.16248028068326` / **11**；**622** = **339**+109+93+75+6；两轮 `no_observation`/`no_platform_state`/`no_estimate`/`planner_exception` 与 `publish_failure_fallback` **全 0 帧**；`nees_median` `5.067625439804517` / `5.2993597343857255`；圈数 `1.618674694329237` / `1.5098613569575674`、B2 停留 `159.9828338623047 − 130.3805694580078 = 29.602264 s`——轮 60/63 与状态板引用的每个数字均与本轮自算相符 |
| 槽位机件探针（副本内直接调用） | `canonical_trial_id('…arm-b-trial-3')` 返回自身、`_expected_policy` = `threshold`、`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`、`ids('b')[2]` 逐字相等；`…-attempt-1/-attempt-2/-trial-6` 均 `run_id_not_frozen_trial`；**A1/A2 两个旧 canonical ID 仍 `run_id_void_consumed`**（见 N34） |
| §2.20 磁盘断言（主树只读复算） | 六个 shared 文件缺席、`runtime/frames/` 0 项、四处旧 hold **257/93/109/257**、attempt-3 run hold 恰 2 文件、void hold 恰 10 份零隐藏、**七个 run 目录各 11 份**、B3 run 目录不存在、四个 release 标记缺席、corridor 实测 = config pin = `9e2956ad…c800` 且工件实际 **779** 条；**七处归档各 6 项 / frames 各 257 项，七个聚合亲自重算**：`ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` / `9dc67a76…a62b` / `09f1ac61…524c` / **`71f65dca…0f85`**，B1/B2 十个单文件行数/字节/SHA 逐项等于 §2.17/§2.19 钉住表 |
| §4 CLI 两基准（三个 git 状态字节级 diff） | HEAD 对 `408acd7` **恰 2 行**（`--run-id`、`--body-policy`）、对 revision 21 状态 **恰 1 行**（`--run-id`），三者均 19 行——revision 21/22 抬头与 (b) 归因的两个基准数字实测成立 |

### 2. revisions 19–22 + 轮 58 的 20 处逐 hunk 核对

对操作单在 `408acd7..9cadebd` 的全部 4 个提交逐 hunk 核对；各修订抬头声明
与实际 diff 相符，未发现声明外的隐藏改动：

1. **revision 19（轮 58，首次跨臂轮换）**：§4 CLI 恰 2 行；§1 臂位行改写 +
   corridor 钉住行新增（磁盘验真）；新增 §2.16 九项（两项臂 B 专属）与
   **门 4**（只增停条件，零阈值）；两条披露（零作废容错、退化记录）；五处
   失效标注就地更正；BC-BODY1-15 (c) 不重新武装（G 点，与代码行为一致：
   分析器不据 `h1.disposition` 抛错、H1 只遍历臂 A——本轮读码确认）。
2. **轮 58 的 20 处自查修复**（提案 §D′ 全清单）：七处要害逐条与落地文本
   对勘——§5 void 行加注域完整性双门、pre/post-tracker 消耗区分、「整块
   19 行含两行」、§2.9/§2.11 指针改 §2.16、§2.16 恢复保全禁令、门 4、§5
   前提补 H2-CEILING 次序条件 (3)；其余 13 处（参数计数 16/17、「四种→
   三种」、`[0, P)` 口径、decision 帧措辞、void 保全命名取臂 B、`64be7f85…39f2`
   补全等）逐条在 diff 中找到对应落地。**注意**：其中「§2.9/§2.11 指针」与
   「void 保全命名」两处在 rev 21/22 后**再次过期**，见 F9/P5。
3. **revision 20（轮 60）**：只加 §2.17（B1 归档合同——钉住表六项经本轮
   主树实测逐项相等）、不轮换槽位（当时臂 B 2–5 无 GO，方向正确）。
4. **revision 21（轮 61）**：轮换 B2 恰 1 行 + 新增 §2.18 九项（§2.16 结构
   扩到六 run/六归档，`tether_corridor_check` 升机械断言）；抬头写死两基准
   区别（对已复核候选 2 行 / 对上一修订 1 行）——本轮字节级证实。
5. **revision 22（轮 63）**：新增 §2.19（B2 归档合同，**64 位全值钉住
   `71f65dca666cc37d91569a9b2b3893c0721e436a1b09756f5e644c0052a20f85`，
   与磁盘复算逐字相等**）+ 轮换 B3 恰 1 行 + 新增 §2.20（七 run/七归档）
   + §2.18 转历史。**§2.20 第 5 项的 B2 聚合缩写与本节全值矛盾，见 F7**；
   §2.17 未随批转已执行，见 P4。
6. **区间其余 10 路径全量归因**：`docs/authorizations.md` +68 纯追加（B1
   GO「1 + 3 合并执行，明确拒绝 2」与批量 GO「照跑 B2–B5，饱和作具名限制
   （推荐）」两条逐字在账，边界读法不扩权）；`docs/unity-test-log.md`
   +812 纯追加（B1/B2 各一条 `PRE_PLAY_RELEASED` (c) + 一条 `VALID_TRIAL`
   代录；两条 (c) 分别记 HEAD `f3a150b`/`ae140ce` + 空 porcelain，发令后由
   接受轮 60/63 批次零改动入库，区间零删改——冻结 (c) 契约成立）；三个
   臂 B 证据文件与 `…-arm-a-trial-2.md` §Y 纯追加，其载荷（§2.16 115、
   §2.17 24、§2.18 126、§2.19 24、§2.20 136、门 4 记录、握手、绑定分析）
   与本轮独立复算无一出入，B2 门 4 记录含 19 行命令原文 + 两条否定项自查；
   `docs/implementation-status.md` +53：两条预登记限制全文，H2-CEILING 反
   事实中位数算术本轮自验成立（116 zeros + 9 ones → median 0.0），且入账
   提交序（`03cb2b5` 早于 B1 Play、`41ff1bd` 早于 B2 Play）满足「预登记
   先于数据」；提案 +541（轮 57–63 七节，轮 63 携带**正确**64 位全值）；
   本文件 +133/−4（轮 9 verdict + 文件头例行更新，旧发现零删除）；状态板
   三个 chore 压缩批次抽查未见义务丢失，两处失效文字见 P6。

### 3. 阻断 finding（CLASS_2，编号续轮 8 的 F4–F6；修复归接受角色——
操作单作者；`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零触碰）

- **F7（CLASS_2）—— §2.20 第 5 项把 B2 归档聚合缩写成错值 `71f65dca…3a85`。**
  §2.19 的 64 位钉住值与本轮磁盘重算（§B.3 口径）均为
  `71f65dca666cc37d91569a9b2b3893c0721e436a1b09756f5e644c0052a20f85`，正确
  缩写 **`71f65dca…0f85`**；`3a85` 不对应本批次任何已钉工件的末四位。同一
  错值另出现在状态板轮 63 Log 条（「钉住值含 `frames/` 聚合 `71f65dca…3a85`」
  ——对 §2.19 实际钉住内容的错误转述）；提案轮 63 节携带的是正确全值。
  失效方向 fail-closed：照 §2.20 字面核对会在一个**完好**工件上判不符并
  触发停止（(c) 前的发令时刻复查即会撞上）。实现角色已在 B3 证据 §A.6
  第 1 条登记并按 §2.19 全值核对通过——本轮独立复算**裁决其登记属实**。
  修复：§2.20 第 5 项缩写改 `71f65dca…0f85`（或直接写 64 位全值）；状态板
  轮 63 Log 条同步更正。仓库无处可写断言（操作单属文档、复核角色无 R5
  例外）→ **`NOT_MECHANIZABLE`**，闭合 = 返工轮定点复看 §2.20 第 5 项与
  该 Log 条。
- **F8（CLASS_2）—— §4 抬头与散文停在 revision 19 的 B1 绑定，未随 rev
  21/22 轮换。** 四处实例（行号按候选）：抬头「**本轮 = 臂 B trial 1**」
  (L1444)；「**本轮有且仅有两处替换**（revision 19…）」（对 rev 22 为假：
  对上一修订恰 1 处）；「`--run-id` 用采集 ID（**本轮 B1 =
  `p1-m3-body-001-arm-b-trial-1`…**）」(L1472)；「包括**本轮新写**的
  `--run-id` 与 `--body-policy` 这两行」。同节 CLI 块、门 4 token、§1 槽位
  行均已在 trial-3——**同一活跃节内部自相矛盾**。行为面：操作员依散文把
  `--run-id` 写成 trial-1 → 门 4（token 正确）拦截强制停止；若门 4 执行
  松懈则撞 B1 run 目录 create-once → `TRIAL_VOID_TRACKER_STARTUP_FAILURE`
  ——烧一次 one-Play GO，且按批量授权条款**任何 void 终态立即中止授权**回
  用户。判据「操作员或工具的行为会不会因这段文字而不同」——会。修复：四处
  改为 B3 当轮绑定，或改为「本轮 = §1 采集 ID 行所指」的去实例化表述（见
  N37）。**`NOT_MECHANIZABLE`**，闭合 = 返工轮定点复看 §4 全节。
- **F9（CLASS_2）—— §3 活跃步骤的 B1 例示未随轮换更新（轮 58 修复 #4 族
  在 rev 21/22 后复发）。** 三处实例：步骤 0′ 第 1 步「记入本轮采集的证据
  文件（**B1 = `docs/evidence/P1-M3-BODY-001-arm-b-trial-1.md`**；…）」
  (L1259)——这是**启动 tracker 的硬前置**的落盘目的地，字面执行会把 B3 的
  解释器记录与门 1 导出写进 B1 的证据文件，正是 revision 19 E 点自己批评的
  「指错文件等于条款落空」；门 1 记录条款「（B1 = `…-arm-b-trial-1.md`；
  同上…）」(L1302) 同病；步骤 1 pause-window void 的保全命名「即
  `*.arm-b-trial-1-void-attempt-1-hold`」(L1291)——B3 真发生越界 void 时
  字面执行会以 B1 之名保全现场（B1 是有效 trial、无 void hold，伪造其作废
  外观并毁归因）。三处均涉 ID → 最低 CLASS_2。修复：三处例示改 B3 或去
  实例化（规则句「臂位取本轮采集 ID」本身正确）。**`NOT_MECHANIZABLE`**，
  闭合 = 返工轮定点复看 §3 步骤 0′/1/门 1 三段。
- **F10（CLASS_2）—— §5「最高优先级」执行前提槽未维护：rev 19 的已耗前提
  仍在位，其授权范围句与已入账批量 GO 相矛盾。** §5 现行首条前提仍是
  「revision 19 执行前提…本次授权只覆盖一次 Play、只覆盖
  `p1-m3-body-001-arm-b-trial-1`；**臂 B 余下四次与 `--compare` 仍需逐次
  逐字 GO**」(L1486-1496)，未按 rev 17/18 先例标「（历史，已放电）」；同页
  「**协议合格 ≠ 已获 GO**：本轮 GO 只覆盖 B1 一次 Play…其余 4 次仍需用户
  逐次点名授权」(L1548) 与 §6 rev 19 条「本轮已获授权的是且仅是
  `…-arm-b-trial-1` 的一次 Play」(L1610) 同族。自轮 61 批量 GO 入账起，
  B2–B5 的现行授权模型是「批量覆盖 + 每次完整 §2.0 (a)–(d) + 任何 void
  终态中止」——rev 21/22 只写进各自抬头，从未进 §5。操作员按「最高优先级」
  字面将拒发 B3 或另行索要已存在的 GO；授权判据文字 → CLASS_2。**注意**：
  该前提的第 (3) 条（H2-CEILING 预登记先于数据，附 `git log -S` 核对命令）
  对整个批次仍承重，修复不得连带删除，应由接受角色起草**现行前提块**（批量
  GO 边界 + 预登记次序条件）并将 rev 19 前提按先例转「历史，已放电」。
  **`NOT_MECHANIZABLE`**，闭合 = 返工轮定点复看 §5 前提区与 §6 相应条。

四条 finding 均为操作单 PLAY_GOVERNING 文字与当轮现实/已入账授权的相悖，
**全部 fail-closed 方向，无一放宽任何门**；**不质疑 A1–A5/B1/B2 的有效性、
轮 60/63 归因或任何冻结数值**（七条 `--verify` 与全部运动量/直方图由本轮
亲自复现）。**B3 的 (c) 与 Play 不得在未修正文本上发出**（与既有交接一致，
本 verdict 将其绑定为复核义务）。修复触及 PLAY_GOVERNING（操作单）→ 返工
通过后按 §4.4 R1 闭合轮资格自动成立；操作单不属 R3 (3) 三个具名 Play 治理
门文件，无强制闭环轮。

### 4. CLASS_3（闭集：时态/失效链接；接受角色独立复判后同轮应用，
不得改任何数字/哈希/run ID/disposition）

- **P4（§2.17 抬头时态 + §2.16 导航指针）**：`### 2.17 B1（有效 trial）的
  post-run 归档（revision 20，**待执行**）` 改
  `### 2.17 B1（有效 trial）的 post-run 归档（revision 20，**已执行**，2026-08-14）`，
  并沿 §2.15 先例在节首加一行历史记录（执行批次 `b6dcf86`，证据
  `…-arm-b-trial-2.md` §A；移动前后逐项相等，六条 `--verify` 逐字复现——
  本轮已在磁盘复验其钉住表）。§2.16 历史注「**本轮的待执行节是 §2.17**
  （B1 的 post-run 归档）」补时间边界：「（写于 revision 20 时属实；§2.17
  已于 2026-08-14 执行完毕）」。re-执行风险已被 destination-exists 守卫
  fail-closed 拦截（§2.19 误重复调用实证，见 N35），故不升级。
- **P5（三处「本轮（B1）的待执行核对是 §2.16」+ 文末「当前待执行的是臂 B
  trial 1」）**：§2.9 (L798)、§2.11 (L871)、§2.14 (L961) 三处导航指针逐字
  改「本文件当前待执行节以最新修订抬头为准（revision 22 起为 §2.19→§2.20；
  本注写于 revision 19（B1 轮）时指向 §2.16，当时属实）」；§6 末句
  「当前待执行的是臂 B trial 1」改「此后各轮以最新修订抬头为准」。若接受
  角色采 N37 的去实例化方案，可用其统一表述替代。
- **P6（状态板两处失效文字，本轮已按 AGENTS.md「交接文字必须与现实一致」
  就地更正并在此记录，轮 8 N32 先例）**：(i) Current state「**B2 executed
  2026-08-14 and awaits attribution**」——轮 63 已归因 `B2_VALID_TRIAL`，
  同一节 Open obligations 亦已写明，两句自相矛盾，更正为已归因表述；
  (ii) Gate board M3 行 Unity 格「“已退出，没有报错”, to be transcribed by
  Acceptance/Chore」——该代录已由轮 63 批次（`0af7344`）写入
  `docs/unity-test-log.md`（B2 `VALID_TRIAL` 条，本轮验证在案），更正为
  「transcribed by Acceptance round 63」。两处均为状态时效文字，零数字/
  零 verdict 改动；轮 63 Log 条的 `3a85` 错值**不在**本项内（属 F7，归
  接受角色随返工更正）。

### 5. workflow §4.4 清单其余项

- **验收条件/坐标/单位/时间戳/帧绑定/过期语义**：区间零代码；冻结值 token
  多重集逐项比对——`212.9706`(4→5)、`130.0`(6→7)、`0.5645`(4→5)、暂停窗
  两端(8→9)、初始框四分数(3→3)、四种 void 终态名、两条域完整性门名
  (各 1→2)、握手词(5→5)、被禁弦长 `83.197` 全文**零出现**；增量全部归因
  于新增臂 B 节/前提/披露；**唯一减少** `run_id_void_consumed`(5→4) 见
  N34（事实本轮探针复验仍真）。
- **边界与失败路径**：门 4、§2.16–§2.20 新增项全部只增停条件；rev 20/22
  在无 GO 或授权边界处拒绝扩张（rev 20 不轮换、rev 22 引批量 GO 不另立
  门）；F7–F10 均 fail-closed 方向，无门放宽。§2.19 误重复调用的失败路径
  见 N35。
- **并发/原子性/真值泄漏**：无新增面；两条 (c) 记录的「发令前落盘、Play 后
  零改动入库」时序在 git 层证实；归档 `os.rename` 逐项 destination-exists
  复查 + 移动前后逐项相等，本轮磁盘终态复算成立。
- **测试真实覆盖**：focused 67/67 副本实跑；七条 `--verify`、运动量、直方
  图、nees、圈数、停留全部从 run 原始工件亲自重算。
- **文档一致性**：四条 CLASS_2 均属操作单文字与当轮现实/授权账本的相悖；
  其余修订声明与 diff 逐项相符；证据/账本/日志/状态板互查一致（F7 的 Log
  错值、P6 两处除外）。

### 6. Notes（编号接轮 9）

- **N34（新）**：冻结 token 多重集唯一减少项——A5 槽位行模板中「A1/A2 两个
  旧 canonical ID 仍被 `run_id_void_consumed` 永久拒绝（本轮实跑复验）」的
  逐轮复验子句未被臂 B 槽位行模板继承（rev 19 起）。机械事实本轮探针复验
  **仍真**（两个旧 ID 均拒），名称在文内另 4 处存活，acquisition IDs 总表
  行仍作断言。建议接受角色择一：恢复该子句入臂 B 槽位行模板，或声明该
  断言由总表行 + focused 套件承载。非阻断。
- **N35（新）**：§2.19 误重复调用披露（`…-arm-b-trial-2.md` §D.3）本轮
  独立核证：主树七处归档唯一、34 个 run 目录、无 `…-arm-b-trial-3/`、
  `frames/` 0 项、六 shared 缺席、七条 `--verify` 逐字复现——**零副作用
  主张成立**；「先实测钉住值后移动」的守卫次序按设计生效，中止点在移动段
  之前。失败路径为未捕获 `FileNotFoundError` 而非有序退出——**附议实现
  角色的定性**（操作失误、零副作用、非合同/工具缺陷）；建议将来的 §2.x
  归档合同可加一句「执行脚本失败时以逐项不符报告有序退出」（零门改动，
  接受角色酌定）。
- **N36（新）**：§6「提交边界声明」自 revision 19 后未再延续（rev 20/21/22
  无条目），边界事实现全部在各修订抬头。平行索引停摆即漂移源（轮 9 F5b
  教训）。建议接受角色补记或在 §6 声明「revision 20 起边界声明并入修订
  抬头」。非阻断。
- **N37（新，F8/F9/F10 + P5 的系统根因）**：轮换同步清单（rev 21 A 点 /
  轮 63 C 点）只列 §1 采集 ID 行、§3 步骤 4/5、门 4 token、§4 `--run-id`，
  而 rev 19 在活跃文本播下的「本轮」绑定另有：§4 抬头与散文、§3 步骤
  0′/1 例示、§5 执行前提、§2.x 导航指针、§6 条目——**清单外绑定已在两次
  轮换中两次腐化**（轮 58 修复 #4 族复发即实证）。耐久修复二选一（接受
  角色裁定）：(a) 把上述全部位点固化进轮换修订模板的必改清单；(b) 活跃
  文本去实例化——凡「本轮 X」一律改指 §1 槽位行单一事实源，历史节才允许
  具名 ID。本轮 finding 按现状分级，不预设方案。
- **N30 仍在**：`analyze_m3_body.py` 模块 docstring 的 verify 只读范围声明
  过期；区间零代码触碰，随下一个获授权代码批次修复。
- **N12、N15、N18、N20、N21、N22、N28、N33 语境仍在**：区间零代码触碰，
  逐项过账不变。

### 7. UNITY_NA 立场

本区间**未申领** `UNITY_NA`，本轮**附议不申领**：B1/B2 是用户真实 Unity
Play，四门/握手/Console 证据齐备并经 (c)/(d) 时序契约绑定入库；B3 前置批次
（零 Play）在证据 §A.6 第 6 条明文不申领。Unity 列既有状态不变，无
`UNITY_NA` 适用情形。

### 8. Verdict

**Round 10: REWORK_REQUIRED（candidate `9cadebd`）。**

四条 CLASS_2 阻断 finding（F7 聚合缩写错值；F8/F9/F10 为 rev 21/22 轮换
未覆盖的 §4/§3/§5 活跃「本轮」绑定与批量 GO 失配，全部 `NOT_MECHANIZABLE`，
闭合 = 返工轮定点复看具名段落）+ 三条 CLASS_3 补丁（P4/P5 交接受角色独立
复判分级后同轮应用；P6 两处状态板失效文字本轮已按常驻规则就地更正并记录
在案）。**本 verdict 明确不推翻的事项**：A1…A5、B1、B2 的有效性与轮 60/63
归因（七条 `--verify` 冻结 receipt 由本轮在副本内亲自逐字复现，B1/B2 运动
量/直方图/nees/圈数/停留从原始工件重算相符）；revisions 19–22 的槽位轮换、
门 4、归档合同与「零阈值/零门放宽」主张（逐 hunk 证实，两基准 CLI 差异
字节级验证）；轮 58 的 20 处修复（逐条落地核对，其中两处随后再度过期已入
F9/P5）；两条预登记限制的内容与「先于数据」提交序；批量 GO 账本条目及其
边界读法。复核债「revisions 19–22 + 轮 58 的 20 处」经本轮逐文件核对
**清偿**，代之以上述具名 finding 的闭合义务。修复归接受角色（操作单与
状态板 Log 作者）；**B3 的 §2.0 (c) 与 Play 在 F7–F10 修正前不得发出**。

按 R7，`REWORK_REQUIRED` 轮**不写** `passed_candidate` 行；「上一通过
候选」维持由 round 9 的机读行派生（`408acd7…`）。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现
文件。** `controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零触碰；
操作单、提案、账本、Unity 日志、证据文件零触碰。全部测试、七条 `--verify`
与槽位/void-ID 探针都发生在一次性副本
`.claude/worktrees/review-P1-M3-BODY-001-r10` 内（`runtime/runs`、
`runtime/models` 为只读拷贝，cp 源侧零写入）；主树 `runtime/` 的 §2.20
断言与七个归档聚合复算全程只读（`ls`/`wc`/`shasum`/只读 Python），未创建、
删除或改写任何字节。主树唯一写入为本文件与 `docs/current-status.md` 的
交接更新（含 P6 两处失效文字的就地更正，均记录在案）。副本收工
`git worktree remove --force` 删除。本轮未推送任何提交（无推送授权申领）。

---

## Round 11 — 轮 10 返工闭合轮（F7–F10 + P4/P5 定点复看；接受轮 64 批次）

Date: 2026-08-14

- 复核对象：接受轮 64 返工批次 **`6e81bc2`**（区间 `9cadebd..6e81bc2` 恰一个
  提交、3 个路径：操作单 79+/45−、提案 +75/0、状态板 48+/84−；账本与
  `docs/unity-test-log.md` **零字节**——冻结 (c) 记录与账本保全）。闭合方式
  按轮 10 verdict：全部 `NOT_MECHANIZABLE` → 本轮**定点复看具名段落**。
- Candidate: **`6e81bc23fab417813e2761755b3b122b4d01c970`**。上一通过候选仍由
  本文件最近一行 `passed_candidate` 派生 = `408acd7…`（轮 10 为
  `REWORK_REQUIRED`，未写该行）。**开轮资格（§4.4 R1）**：`9cadebd..6e81bc2`
  在 PLAY_GOVERNING 上非空（恰一条 = 操作单）。
- **代码零接触，测试结论承接**：`6e81bc2:tests` =
  `4af739c2a4f1ff1a96259e4e80fd6b13dd95ccb4`、`analyze_m3_body.py` blob =
  `c79a68ea…`，与轮 7–10 记录逐字相同；测量侧 diff **为空**（本轮实测）。
  轮 10（同日，本会话）在同一字节代码上的 focused 67/67、七条 `--verify`
  逐字复现与全部原始工件重算**继续有效**，本轮不重跑、不开副本。

### 1. 定点复看（逐条闭合判定）

1. **F7 —— 关闭。** §2.20 第 5 项改为 **64 位全值**
   `71f65dca666cc37d91569a9b2b3893c0721e436a1b09756f5e644c0052a20f85`
   （与轮 10 磁盘重算逐字相等）并如实注明「revision 22 起草时把末四位误写成
   `3a85`」——取轮 10 处方的「直接写全值」分支，缩写歧义源根除。状态板侧：
   轮 63 Log 条经轮 64 按 R9 压缩入「B2 全链条」指针条目，错值不再被任何
   在盘文本**断言**（现存 `3a85` 全部是 finding 描述/登记中的引用），且指针
   条目如实注明「其缩写错值即 F7」。全文断言侧零残留（本轮 grep 清扫）。
2. **F8 —— 关闭。** §4 抬头改「本轮 = §1「本轮采集 ID」行所指的那一次」；
   散文改为「每轮替换的位点固定为两个」+ 双基准算术写死（对已复核候选
   `408acd7` 恰 2 行 / 对上一修订同臂恰 1 行，(b) 归因按 2 行——与轮 10 的
   字节级 diff 一致）；「本轮 B1 = …」句改为「唯一事实源是 §1 行，本节不
   复述具体 ID」；尾注「每次各需用户逐字 GO」改指 §5 现行前提（接受轮 64
   自查第 1 处）。**CLI 块本身 19 行字节不变**（本轮与候选逐字节比对），
   门 4 token 块未触碰仍指 trial-3。
3. **F9 —— 关闭。** §3 步骤 0′ 第 1 步与门 1 记录条款改为**机械导出规则**：
   文件名 = `docs/evidence/P1-M3-BODY-001-<本轮采集 ID 去 p1-m3-body-001-
   前缀>.md`——本轮对全部三个现存臂 B 文件逐一验证导出正确（b1/b2/b3），
   且在冻结合同下 §1 槽位行今后只可能持有 canonical B 槽 ID，规则域内无
   反例（历史 A1/A2 的 attempt 后缀 ID 不在其域内，见 N39）。步骤 1 void
   保全命名改为「臂位与序号一律取 §1 行」+ 双重否定告诫（不沿用 arm-a-*、
   不沿用任何前一轮 ID），并写明写死 B1 的归因毁伤后果。
4. **F10 —— 关闭。** §5 顶部新立**轮换不变的「现行执行前提（最高优先级）」**：
   批量 GO 授权模型（账本逐字引用）、每次完整 §2.0 (a)–(d)、任何 void 终态
   中止、`--compare` 排除；发令条件 (1) 泛化为「本修订抬头指定的核对节」、
   (3) 扩为**两条**预登记的次序探针——本轮实跑两条 `git log -S` 命令，
   分别返回 `03cb2b5`/`41ff1bd` 且均早于下一次 Play，探针可用。rev 19 前提
   按 rev 17/18 先例转「（历史，已放电）」，`--compare` 部分明示存续；
   「对 B1 继续逐字适用」改「对每一轮继续逐字适用」并纳入两次 `C_geom = 1.0`
   的反调参覆盖；§6 三条现在时逐次 GO 断言（rev 19/18/12 条）全部补时间
   边界。**本轮全文清扫**：活跃文本中 B1/trial-1 绑定零残留（仅存两处均在
   历史围栏内：rev 19 已放电前提的引用句、rev 17 原文块）。
5. **P4/P5 —— 关闭。** §2.17 抬头转已执行（历史注具名 `b6dcf86`）+ §2.16
   注补时间边界；§2.9/§2.11/§2.14 三处导航指针与文末句全部去实例化为
   「以最新修订抬头为准」。接受轮 64 §A 逐条复判在案（同意 CLASS_3、同轮
   应用、零数字/哈希/run ID/disposition 改动——本轮 diff 复对属实）。
6. **轮 64 自查的八处**（复核点名之外，含一处返工自造并披露）：逐处在
   diff 中定点核对，全部落地且方向一致（§2.19/§2.20 抬头转已执行并保留
   「发令时刻须复查」、§2.18 指针去实例化、§3 步骤 3 事实句改写、§2.17
   授权句时间边界等）；自造缺陷（P4 补记初稿硬编码节号）终稿已消除。
   披露诚实，无淡化。

### 2. 批次级核对

- **零冻结值改动**：对候选逐 token 比对——`212.9706`/`130.0`/`0.5645`/
  暂停窗两端/初始框四分数/四种 void 终态名/两条域完整性门名/握手词/
  `9e2956ad`/`run_id_void_consumed`/`run_id_not_frozen_trial` 计数全部不变，
  `83.197` 仍零出现；仅有的增量是 64 位全值 1→2（F7 修复本体）与
  `arm-b-trial-3` 10→11（§2.20 抬头改写），均可归因。
- **§4 CLI 块与门 4 token 块零字节改动**（本轮字节级比对）；§5 void 终态
  表、门 1/2/3 判据、完成握手零触碰。
- **角色边界**：批次恰 3 路径（操作单/提案/状态板，均接受角色所有），账本
  与 Unity 日志零字节；无越权。
- **状态板**：轮 64 更新了 Current state 与 Log（轮 61–63 压缩为指针条目，
  义务与预登记结论逐项保留，`3a85` 以「其缩写错值即 F7」如实标注）；
  **但 Active handoffs 行 1 未随返工落地更新**（仍写「fix F7–F10 before
  (c)」、Status `AWAITING_ROUND10_REWORK_THEN_C_RECORD`），见 N38——本轮
  按常驻规则在本批次就地更正并记录。

### 3. 新增 CLASS_3（接受角色独立复判后同轮应用）

- **P7（§2.19 补记的证据指针取错一手来源）**：§2.19 历史注写「（证据
  `…-arm-b-trial-3.md` §A）」，但「移动前后逐项相等（24/24）+ 七条
  `--verify` 逐字复现」的**一手执行报告**在
  `docs/evidence/P1-M3-BODY-001-arm-b-trial-2.md` **§D**（`29e903a` 批次）；
  trial-3 §A 是 §2.20 时点的**复验**（其 §A.1 第 2 项与 §A.2）。逐字替换：
  「（证据 `…-arm-b-trial-2.md` §D；§2.20 时点的复验见 `…-arm-b-trial-3.md`
  §A）」。纯引用精度，属失效链接族，不阻断、不影响任何门；随接受角色
  消费本 verdict 的批次应用即可。

### 4. Notes（编号接轮 10）

- **N38（新，状态板交接时效，本轮已处置）**：接受轮 64 落地返工后未把
  Active handoffs 行 1 的 Requested action/Status 从「待返工」翻到「待闭合
  复看」（其 Log 条目已写明「闭合仍待下一轮定点复看」，意图在案、行未同步）。
  本轮按「交接文字必须与现实一致」在状态板批次就地更正为 Round 11 后状态
  并在此记录（轮 8 N32 先例）。非 finding。
- **N39（新，信息性）**：§3 步骤 0′ 文件名导出规则在其适用域内正确——冻结
  合同下 §1 槽位行今后只能持有 canonical B 槽 ID（B3/B4/B5，均已验证导出
  与实名一致）；该规则**不**描述历史 A1/A2（attempt 后缀采集 ID 对应无后缀
  文件名），而该情形在无新的用户授权 + 代码 + 复核 + 停点之前不可再现，
  届时操作单必然另行修订。同理，步骤 1 保全名的 `-void-attempt-1` 序数
  字面对首次 void 正确；同槽第二次 void 需新 GO 与新修订，不在现行文本
  义务内。零动作。
- **N34/N35/N36 —— 结案**：接受轮 64 §D 逐条裁定（总表行 + focused 套件
  承载 void-ID 断言；附议 N35 定性并把「有序退出」条款指派给下一份归档
  合同；§6 停摆以「rev 20 起并入修订抬头」声明收束）。三条裁定理由成立，
  本轮无异议。
- **N30 仍在**：`analyze_m3_body.py` docstring 过期声明，区间零代码触碰，
  随下一个获授权代码批次修复。**N12/N15/N18/N20/N21/N22/N28/N33 仍在**：
  逐项过账不变。

### 5. UNITY_NA 立场

本批次纯文档、零 Unity 面，**未申领** `UNITY_NA`，本轮附议不适用；Unity
列既有状态不变。formal Play、采集 ID、`--compare` 与指标继续冻结。

### 6. Verdict

**Round 11: PASS_WITH_NOTES（candidate `6e81bc2`）。**

轮 10 的四条 CLASS_2（F7/F8/F9/F10）与两条 CLASS_3（P4/P5）全部按处方或
更优方案（N37 (b) 去实例化 + 「字面即机制」例外闭集）修正并经本轮定点复看
**关闭**；接受轮 64 自查的八处同族修复逐处核对落地；N34/N35/N36 经裁定
结案。零冻结值/零门语义改动，CLI 块与门 4 token 块零字节，历史围栏完好，
账本与冻结 (c) 记录零触碰。**操作单活跃文本自此以 §1「本轮采集 ID」行为
单一事实源，B3 的 §2.0 (c) 可以在本候选文本上起草**——(c) 仍须按 §2.20
抬头在发令时刻复查九项，并按 §2.0 在写入时点自取 HEAD/porcelain。新增
P7（CLASS_3 引用精度补丁）交接受角色随消费本 verdict 的批次复判应用，
不阻断 (c)。本 verdict 不释放任何 Play、不授权任何采集；B3–B5 的授权
仍完全由 2026-08-14 批量 GO 及其 void 中止条款约束。

passed_candidate: 6e81bc23fab417813e2761755b3b122b4d01c970

后记（R7 派生自指验证，提交前实测）：本 verdict 落盘后
`grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md | tail -1` 返回
`6e81bc2…`（最新，正确）；§2.0 (b) 的例示命令（round 9 F4 修正形）自动
前移到本候选，无需任何手写更新——R7 契约在第三行 `passed_candidate` 上
继续成立。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现
文件。** 本轮零实现代码接触（测试树与工具 blob 哈希与轮 7–10 逐字相同，
测量侧 diff 为空，故未开复核副本、未重跑测试——轮 10 同日在同一字节上的
自跑结论承接）；唯一探针是对已提交文档/git 对象的只读 `grep`/`git show`/
`git log -S` 与 scratchpad 内的 CLI 块字节比对。主树唯一写入为本文件与
`docs/current-status.md` 的交接更新（含 N38 的就地更正，记录在案）。
本轮未推送任何提交（无推送授权申领）。
本轮未推送任何提交（无推送授权申领）。

---

## Round 12 — 通过轮后接受续批复核债轮（接受轮 64 续批 `a5fc735`）

Date: 2026-08-15

- 复核对象：接受轮 64 **续批** `a5fc735`（2026-08-14 23:59:07 提交）。它落在
  复核轮 11 之后 **4 分 35 秒**（轮 11 提交 `1528288` 于 23:54:32，范围恰为
  `9cadebd..6e81bc2` 一个提交），故不在轮 11 覆盖内；其提交信息与提案 D′ 末段
  自述「本续批同样未经独立复核，与上批一并挂在闭合轮的定点复看范围内」——
  该覆盖预期在落地时已经落空（闭合轮已收官），见 P8/N41。Active handoffs
  无复核行、行 1 仍停在轮 11 后的「(c) 待发」状态，未登记本续批为复核债；
  按轮 8/轮 10 先例以**登记债**开轮（登记地 = 候选自身的提交信息与提案 D′
  末段），交接时效缺口本轮收工按常驻规则就地更正并在 N41 记录。
- Candidate: **`a5fc735a233e44cd824e5eff6cb5addaea4da94e`**（HEAD）。上一通过
  候选由本文件最近一行 `passed_candidate` 派生 = **`6e81bc2…`**（轮 11）。
- **开轮资格（§4.4 R1）本轮自验**：`git diff --name-only 6e81bc2..a5fc735` 在
  PLAY_GOVERNING 上非空，**恰一条**——操作单
  `docs/evidence/P1-M3-BODY-001-1c-preflight.md`（+19/−8）。区间恰两个提交、
  4 个路径：`1528288`（复核轮 11 自身：本文件 + 状态板，均本角色所有，与其
  边界声明一致）与 `a5fc735`（接受续批：操作单 + 提案 + 状态板，均接受角色
  所有）；测量侧（`controller/`、`Assets/`、`tools/`、`tests/`、`config/`、
  `ProjectSettings/`、`Packages/packages-lock.json`）diff **为空**（本轮实测）；
  `docs/authorizations.md` 与 `docs/unity-test-log.md` **零字节**。
- 复核副本：`git worktree add --detach
  .claude/worktrees/review-P1-M3-BODY-001-r12 a5fc735`，收工已删除；
  `runtime/runs`、`runtime/models` 只读拷贝入副本（cp 源侧零写入）。

### 1. 测试与复算自跑（副本内、BC-BODY1-34 钉住解释器）

| 项 | 本轮独立复跑 |
|---|---|
| focused `test_analyze_m3_body.py` | **67/67 OK**（副本内 `discover -s tests -p`）；`a5fc735:tests` = `4af739c2a4f1ff1a96259e4e80fd6b13dd95ccb4`、`analyze_m3_body.py` blob = `c79a68ea3042c2f96e33e7f7051b5786602c8304`——两哈希与轮 7–11 记录逐字相同，代码零漂移独立旁证 |
| **七个 `--verify`（A1…A5 + B1 + B2）** | 全部退出 0、`verified: true` 且**逐字复现各自冻结 receipt**：臂 A `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` / `0.5783206310103214` / `0.5783243208518966` 均 `WITHIN_RANGE`、窗口 `1.0`；**B1、B2 均 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`**——七个数字由本轮在副本内亲自复算 |
| 槽位机件探针（副本内直接调用） | `canonical_trial_id('…arm-b-trial-3')` 返回自身、`_expected_policy` = `threshold`、`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`、`expected_acquisition_ids('b')[2]` 逐字相等；`…-trial-3-attempt-1` 与 `…-arm-b-trial-6` 均 `run_id_not_frozen_trial`；**两个旧 canonical ID（`…arm-a-trial-1`/`…arm-a-trial-2`）均 `run_id_void_consumed`**——N34 裁定的机械事实本轮复验仍真 |
| §4 CLI 块（三个 git 状态字节级） | 19 行，`9cadebd`/`6e81bc2`/`a5fc735` 三个状态提取件同一 SHA-256（`fd832df1…`）——续批「对候选零差异（本批与上批均未触碰）」主张字节级证实；门 4 token 块不在续批任何 hunk 内（diff 构造上未触碰） |
| 冻结值 token 多重集（`6e81bc2` → `a5fc735`，操作单全文计数） | **零减少**：`212.9706`(5)、`130.0`(7)、`0.5645`(5)、暂停窗两端(9/9)、初始框四分数(3/4/3/3)、`(177,195,77,73)`(6)、四种 void 终态名(4/2/3/3)、两条域完整性门名(各 2)、握手词(5)、`9e2956ad`(6)、`run_id_void_consumed`(4)、`run_id_not_frozen_trial`(9)、`62.5`(5)/`31.25`(4)、B2 归档 64 位全值(2) 全部不变；被禁弦长 `83.197` **零出现**；64-hex 全值**无失无增**。仅有增量 `arm-b-trial-3` 11→12（步骤 0′ 例示句）与 `R10` 5→6、`R11`/`R12` 0→1（§5 排除清单），逐项可归因于续批两个 hunk |

### 2. 续批逐 hunk 核对（操作单 4 hunk + 提案 D′ + 状态板 bullet）

1. **§3 步骤 0′ 第 1 步 + 门 1 记录条款：导出规则撤回、换单一事实源指针——
   替换机制本轮验真，F9 保持关闭。** 撤回依据的三条磁盘事实逐一验真：A1 的
   采集 ID 确带 `-attempt-4` 后缀（§1 L433/L445，机械导出名磁盘不存在）、
   `docs/evidence/` 实测**恰五个** `…-arm-*` 证据文件、A3/A4/A5 无独立文件
   （与 A2 共用 `…-arm-a-trial-2.md`）。新指针链三环本轮实测齐全：revision 22
   抬头（L3–6）指定「§2.20（B3 的 Play 前核对）」→ §2.20 **节首**（L1214–1215）
   具名 `docs/evidence/P1-M3-BODY-001-arm-b-trial-3.md` → §5 发令条件 (1) 引用
   「本修订抬头指定的核对节」。例示句「例如 revision 22 的 §2.20 具名 …」是
   **轮换不变的历史真句**（revision 22 的 §2.20 已冻结，轮换后该句仍真，不同于
   F8/F9 那类「本轮 = B1」会变假的绑定）。渲染失真主张验真：旧文 L1274 单行
   4 个反引号构成嵌套断裂（`p1-m3-body-001-` 会被渲染成正文），新段 6 个反引号
   全部配对。**F9 的保护性质（落盘地绑定正确且不随轮换失效）由替换机制保持，
   F9 维持关闭**；轮 11 N39 的适用域分析随被分析规则的撤回失去对象，归档为
   历史（见 N42）。
2. **§5 排除清单补全：操作面逐项全真、无净授予——但来源自证为假，见 F11。**
   清单各项对真实授权现状逐项核对：`--compare` 需十次齐备并单独授权 ✓、任何
   重试/重进/调参被批量 GO 条目排除且另有 §3/§5 终态与 BC-BODY1-15 (d) 封堵 ✓、
   协议/指标/阈值/测量窗/载体/统计量变更被批量 GO 条目排除（统计量另有 B1 条目
   第 3 项 NO-GO）✓、R10/R11、R12 未授权未开工（COORD-007 账本 2026-08-12 +
   状态板在案）✓。方向纯收紧，无一项放宽、无一项把真授权拒之门外。发令条件
   (1)(2)(3) 与两条预登记探针原文未被触碰（hunk 外）。
3. **§6 N36 头：与裁定一致。** 头部声明「自 revision 20 起并入修订抬头，本节
   保留 revision 19 及更早」与 N36 裁定（轮 64 §D，轮 11 结案）逐字同向；实测
   §6 最新编号条目确为 revision 19，无 rev-20+ 条目。✓
4. **提案 D′（L5938–5967）**：第 1/3/5 项与实际 diff 相符、第 4 项的 N34 依据
   复核结论与本轮探针一致（其「逐字承载」措辞的精度问题见 N40）；第 2 项与
   操作单 §5 同病（F11 第二处）；**开头「其 RESIDUAL RISK 段点名」出处虚指**
   （见 P9）与**末段「挂在闭合轮的定点复看范围内」覆盖预期落空**（见 P8）。
   「九条 must-fix 已在上批全部落地」计数成立（F7 1 处 + F8 4 处 + F9 3 处 +
   F10 1 处 = 九处具名段落，轮 11 逐处闭合在案）。
5. **状态板 Log bullet（L302–306）**：撤回三事实、指针指向、N36/N34 落点均与
   磁盘一致；「§5 按账本逐字补全排除项」分句携带与 F11 同一失真，随 F11 一并
   更正（本角色不改他人 Log 条，轮 10 P6 先例）。**行 1 交接未登记本续批为
   复核债**，见 N41。
6. **P7 目标核对**：§2.19 补记（L1182–1184）本区间零改动，仍引 `…-arm-b-trial-3.md`
   §A——P7 维持原状，按轮 11 安排随 (c) 批次复判，不因本轮改变。

### 3. 阻断 finding（CLASS_2，编号续轮 10 的 F7–F10；修复归接受角色——
操作单/提案/该 Log 条作者；`controller/`、`Assets/`、`tools/`、`tests/`、
`config/` 零触碰）

- **F11（CLASS_2）—— §5「最高优先级」前提块把合并清单自证为「账本 2026-08-14
  逐字…本前提转录该清单不作增减」，对任一具名单源均不成立。** 账本当日有
  **两条**条目：**批量 GO 条**（「饱和决定」，L40–41）的排除清单为
  「`--compare`（需十次齐备并**单独授权**）、任何重试/重进/调参、任何协议/
  指标/阈值/测量窗/载体/统计量变更」——**不含 R10/R11、R12**；R10/R11、R12
  只出现在**已放电的 B1 单次 GO 条**（L80–81），而那份清单同时含「臂 B
  trial 2–5」（已被批量 GO 本身取代，未转录——不转录是对的）。故操作单
  §5（L1515–1517）「**批量 GO 明确未覆盖的（账本 2026-08-14 逐字）**：…
  R10/R11、R12。本前提转录该清单**不作增减**」把 B1 条目的排除项归到批量 GO
  条目名下：对批量 GO 条是**增**（R10/R11、R12），对 B1 条是**减**（臂 B
  trial 2–5），「逐字」对两者的措辞差异（「任何重试/重进/调参」被拆写、
  「…变更」被改写「修改…」）也不成立。提案 D′ 第 2 项（L5950–5953）
  「账本 2026-08-14 还**逐字**排除…已补，**不作增减**」同病；状态板 Log
  bullet「按账本逐字补全」分句同病。**操作面无净授予**（上文 2. 项逐项核实：
  清单各项今日均真不可为），失效方向 fail-closed——但这是发令前必读、标注
  最高优先级的**授权判据文字**，其自证邀请逐字审计：照字面对账本核对会在一份
  **完好**的授权上判出不符并触发停止（F7 同型）；且 (c) 起草者引用本前提即会
  把「批量 GO 逐字排除 R10/R11、R12」这一**账本没有的条文**写进冻结 (c) 记录
  ——在「账本没有的授权视为未发生」的项目里，给账本安上没说过的话是同一
  完整性的镜像破坏。按 R4「凡涉及判据的文字最低 CLASS_2」定级。修复处方
  （一句话来源拆分，不动任何门/数值）：批量 GO 逐字部分与站立排除分列，如
  「**批量 GO 明确未覆盖的（账本 2026-08-14『照跑 B2–B5』条逐字）**：
  `--compare`（需十次齐备并单独授权）、任何重试/重进/调参、任何协议/指标/
  阈值/测量窗/载体/统计量变更。**另按在案现状继续排除（非批量 GO 条文；
  COORD-007 账本 2026-08-12 未授权，B1 单次 GO 条 2026-08-14 曾逐字点名）**：
  R10/R11、R12」，并删除或限定「不作增减」句；提案 D′ 第 2 项与状态板 Log
  bullet 分句同批更正。仓库无处可写断言（纯文档）→ **`NOT_MECHANIZABLE`**，
  闭合 = 返工轮定点复看 §5 前提块、提案 D′ 第 2 项与该 Log bullet 分句。

四条以内、恰一条 CLASS_2；**fail-closed 方向，零门放宽**；**不质疑** A1…A5/
B1/B2 的有效性、轮 60/63 归因、批量 GO 及其边界读法、以及续批全部操作性
内容（指针规则替换、清单操作面、§6 头、N34 复验——均本轮核实成立）。
**B3 的 §2.0 (c) 与 Play 在 F11 修正前不得发出**（修复是一句话的来源拆分，
不阻塞其余 (c) 准备）。修复触及 PLAY_GOVERNING（操作单）→ 返工后按 §4.4 R1
闭合轮资格自动成立；操作单不属 R3 (3) 三个具名 Play 治理门文件，无强制
闭环轮。

### 4. CLASS_3（闭集：时态/失效链接；接受角色独立复判后同轮应用，
不得改任何数字/哈希/run ID/disposition）

- **P8（提案 D′ 末段的覆盖预期已落空——已执行轮次按未执行表述）**：
  L5966–5967「**本续批同样未经独立复核**，与上批一并挂在闭合轮的定点复看
  范围内。」中，「闭合轮」（= 复核轮 11）已于续批落地前 4 分 35 秒收官且其
  范围恰为 `9cadebd..6e81bc2` 一个提交，续批不在也不可能在其范围内。逐字
  替换：「**本续批同样未经独立复核**。（时间边界：落地时未知复核轮 11 已于
  同日 23:54 收官且其范围恰为 `9cadebd..6e81bc2` 一个提交；本续批的复核
  覆盖由复核轮 12 承担。）」
- **P9（提案 D′ 开头的出处虚指——失效引用）**：L5940「本续批处理其
  RESIDUAL RISK 段点名的非阻断项」——复核轮 10 **没有** RESIDUAL RISK 段
  （本轮 grep：该短语除此句外全仓零出现），且第 1 项处理的导出规则在轮 10
  时点**尚不存在**（上批才引入），轮 10 不可能点名。逐字替换：「本续批处理
  两类事项：上批落地后本角色自查仍留存的残项（第 1、2 项，认定与撤回均本
  角色自判），与 D 节只裁定、未写进操作单的两条（第 3、5 项）；第 4 项为
  N34 依据的实测复核」。状态板 Log bullet 首句「续批落地复核轮 10 的非阻断
  项」的同族措辞随本补丁一并更正（其中第 1、2 项并非轮 10 点名项）。

### 5. workflow §4.4 清单其余项

- **验收条件/坐标/单位/时间戳/帧绑定/过期语义**：区间零代码；冻结值 token
  多重集见上表（零减少，增量逐项归因）。
- **边界与失败路径**：续批只增禁止、只换指针，无门放宽；§5 发令三条件与两条
  预登记探针原文未触碰；步骤 0′ 第 2 步 fail-closed 语义原文未触碰；四种 void
  终态、门 1/2/3/4、握手全部零改动（token 计数 + hunk 定位双重证实）。
- **并发/原子性/真值泄漏**：无新增面；区间零 `runtime/` 触碰。
- **测试真实覆盖**：focused 67/67 副本实跑；七条 `--verify` 与槽位/void-ID
  探针亲自复算。
- **文档一致性**：F11/P8/P9 之外，操作单 4 hunk、提案 D′、状态板 bullet 与
  磁盘/账本/git 逐项相符；P7 目标零改动仍候 (c) 批次。

### 6. Notes（编号接轮 11）

- **N40（新，信息性）**：提案 D′ 第 4 项（L5956–5959）「总表行**确实逐字
  承载**两个旧 canonical ID 的 `run_id_void_consumed` 断言」——「逐字」对 A1
  侧过强：§1 总表行（L445）在 A2 侧逐字具名该 token，A1 侧写的是「原 A1 ID
  已被 attempt-3 void 现场消耗，永久拒绝」（语义同、token 无）。其括注如实
  引用了两侧原文，N34 裁定（断言由总表行 + focused 套件**共同**承载）不受
  影响，机械事实本轮探针复验两个 ID 均 `run_id_void_consumed`。零门影响；
  接受角色可随 F11 批次顺手把「逐字」限定到 A2 侧，不单独要求。
- **N41（新，过程事件与交接时效，本轮已处置登记）**：PLAY_GOVERNING 修改
  在通过轮收官 **4 分 35 秒后**落地，未在状态板登记复核债——行 1 仍写
  「Rework closed …next is B3's §2.0 (c)」，唯一的覆盖表述（提交信息与提案
  D′ 末段）指向一个已收官、范围已冻结的闭合轮。在本轮开轮之前的窗口里，
  状态板对 (c) 亮的是绿灯而操作单带着未复核 delta——若 (c) 在该窗口发出，
  B3 的 Play 将跑在未经复核的治理文本上。本轮以 git 派生发现并按登记债
  开轮，收工时按「交接文字必须与现实一致」把行 1 就地更正为轮 12 后状态
  （轮 8 N32 / 轮 11 N38 先例）。**建议**（接受角色采择，零门改动）：今后
  凡在通过轮之后触碰操作单，同批在 Active handoffs 行登记复核债（轮 8/10
  的登记债先例即为此用）。
- **N42（新，F9 承接判定）**：F9 的关闭在闭合机制被续批替换后**仍然成立**
  ——F9 要求的保护性质是「落盘地绑定正确且不随轮换失效」，不绑定某一具体
  机制；替换后的指针链本轮三环实测齐全（见 §2.1）。轮 11 N39 对旧导出规则的
  适用域分析随该规则撤回而失去对象，归档为历史，其「历史 A1/A2 不在规则域
  内」的事实陈述保持为真。零动作。
- **N30 仍在**：`analyze_m3_body.py` 模块 docstring 的 verify 只读范围声明
  过期；区间零代码触碰，随下一个获授权代码批次修复。
- **N12、N15、N18、N20、N21、N22、N28、N33 语境仍在**：区间零代码触碰，
  逐项过账不变。

### 7. UNITY_NA 立场

本区间**未申领** `UNITY_NA`，本轮**附议不申领**：区间纯文档、零 Unity 面、
零 Play/ID/`runtime/` 触碰；Unity 列既有状态不变。formal Play、采集 ID、
`--compare` 与指标继续冻结。

### 8. Verdict

**Round 12: REWORK_REQUIRED（candidate `a5fc735`）。**

一条 CLASS_2 阻断 finding（F11：§5 前提块把两条账本条目的排除项合并后自证
「批量 GO 逐字/不作增减」，对任一具名单源均不成立；操作面无净授予、方向
fail-closed，但属发令前必读的授权判据文字，且会把账本没有的条文带进 (c)
记录；`NOT_MECHANIZABLE`，闭合 = 返工轮定点复看三处具名位点）+ 两条 CLASS_3
补丁（P8/P9：提案 D′ 的覆盖预期与出处虚指，交接受角色独立复判后同轮应用）。
**本 verdict 明确不推翻的事项**：A1…A5、B1、B2 的有效性与轮 60/63 归因
（七条 `--verify` 冻结 receipt 由本轮在副本内亲自逐字复现）；批量 GO 账本
条目及其边界读法；续批的全部操作性内容——步骤 0′/门 1 的指针规则替换
（三环链实测齐全，F9 维持关闭）、§5 清单的操作面（逐项真禁止）、§6 N36 头、
N34 依据复验；轮 11 的全部闭合判定。P7 维持原状随 (c) 批次复判。复核债
「接受轮 64 续批未经复核」经本轮逐文件核对**清偿**，代之以 F11/P8/P9 的
闭合义务。修复归接受角色（操作单/提案/该 Log 条作者）；**B3 的 §2.0 (c) 与
Play 在 F11 修正前不得发出**——修复为一句话的来源拆分，其余 (c) 准备不受
阻塞。

按 R7，`REWORK_REQUIRED` 轮**不写** `passed_candidate` 行；「上一通过候选」
维持由 round 11 的机读行派生（`6e81bc2…`）。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现文件。**
`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零触碰；操作单、
提案、账本、Unity 日志、证据文件零触碰。全部测试、七条 `--verify` 与槽位/
void-ID 探针都发生在一次性副本 `.claude/worktrees/review-P1-M3-BODY-001-r12`
内（`runtime/runs`、`runtime/models` 为只读拷贝，cp 源侧零写入）；主树对
操作单/提案/账本的核对全程只读（`grep`/`git show`/`sed -n`/只读 Python），
CLI 块字节比对在 scratchpad 内完成。主树唯一写入为本文件与
`docs/current-status.md` 的交接更新（含行 1 交接时效的就地更正，N41 记录
在案）。副本收工 `git worktree remove --force` 删除。本轮未推送任何提交
（无推送授权申领）。

## Round 13 — 用户前置为 B4 放行条件的复核轮（四批复核债 + revision 23/24 对磁盘核对）

Date: 2026-08-20

- 复核对象：`6e81bc2..50e7d38` 全区间（**11 个提交、8 个路径**），即用户
  2026-08-20 逐字裁定「先复核再放行 B4」所指的那一轮。四批债一次清偿：
  F11 返工（接受轮 65）、轮 66 的写死候选归因修复、revision 23（轮 67）、
  revision 24（轮 68）。
- Candidate: **`50e7d387074aa280a6dfda26023d3781ff9cb1f5`**（HEAD）。上一通过候选
  由本文件最近一行 `passed_candidate` 派生 = **`6e81bc2…`**（轮 11；轮 12 为
  `REWORK_REQUIRED`，未写该行）。
- **开轮资格（§4.4 R1）本轮自验**：`git diff --name-only 6e81bc2..50e7d38` 在
  PLAY_GOVERNING 上**非空、恰一条** = 操作单
  `docs/evidence/P1-M3-BODY-001-1c-preflight.md`（+289/−9）。
  `controller/`、`Assets/`、`tools/`、`tests/`、`config/`、`ProjectSettings/`、
  `Packages/packages-lock.json` 的 tree 哈希在两端**逐项相同**（本轮实测：
  `tools` `ee6d522a…`、`tests` `4af739c2…`、`controller` `b43fd18e…`、
  `Assets` `b761fc8b…`、`config` `969c0ad4…`、`ProjectSettings` `35e21811…`、
  packages-lock blob `53259665…`），故本轮是**纯文档语义 + 磁盘实测**轮。
- 复核副本：`git worktree add --detach
  .claude/worktrees/review-P1-M3-BODY-001 50e7d38`，收工已删除。副本内以符号链接
  只读挂 `runtime/runs`；`runtime/` 全程**零写入**（收工 `git status --porcelain`
  主树为空，六项 shared 成员的 mtime/SHA 与开工时逐字相同）。
- **接受轮 68 明令的复核方式**：「verify the corrected §2.21/§2.22 against the disk
  rather than against the prose」。本轮照此执行——**并且正是磁盘实测推翻了
  revision 24 的 §2.21 A 组归属**（见 F12）。

### 1. 测试与复算自跑（副本内、BC-BODY1-34 钉住解释器）

| 项 | 本轮独立复跑 |
|---|---|
| focused `test_analyze_m3_body.py` | **67/67 OK，`skipped=0`**——`ArchivedRunLoopDomainTests` 四条真实字节用例**实跑非 skip**（副本内挂 `runtime/runs` 后复跑；未挂时为 `OK (skipped=4)`，本轮两次都记下）。`50e7d38:tests` = `4af739c2a4f1ff1a96259e4e80fd6b13dd95ccb4`、`analyze_m3_body.py` blob = `c79a68ea3042c2f96e33e7f7051b5786602c8304`——与轮 7–12 记录逐字相同 |
| **八条 `--verify`（A1…A5 + B1 + B2 + B3）** | 全部退出 0、`verified: true`、逐字复现各自冻结 receipt：臂 A `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` / `0.5783206310103214` / `0.5783243208518966` 均 `WITHIN_RANGE`；**B1/B2/B3 均 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`**。第八条（B3）为本轮首次由复核角色亲自复跑 |
| B3 绑定指标（副本内直接读 `m3_body_analysis.json`） | effort `91.174630127364`、path `64.4545385428812`、switches `11`、`nees_median` `5.196313303659595`、`loop_frame_count` `530`、`h2_grid_points` `125` 且 `min_side_ge20_share = 1.0`（即 125/125）、`body_policy = threshold` / `body_planner_name = threshold-corridor-v1` / `condition = follow` / `init_frame_id = 0`（臂身份三层）——与轮 67 §B 表、状态板、`implementation-status.md` 逐项相符 |
| B3 reason 直方图（副本内重算 `frames.jsonl`） | `corridor_blocked` **319**（+`margin_below_trigger`）、`within_hysteresis_band` 121、`margin_below_trigger` 95、`margin_above_release` 85、`corridor_shortened` 6，合计 **626** = `published_gimbal_commands`。轮 67「319」证实 |
| §2.22 第 3/4/5/6/9 项对磁盘 | 四处旧 hold **257 / 93 / 109 / 257** ✓；attempt-3 run hold **恰 2 文件** ✓；八个 run 目录**各恰 11 份** ✓；七处 post-run 归档**各恰 6 项**、`frames/` **各 257** ✓，七个聚合本轮按 `…-arm-a-trial-2.md` §B.3 口径重算，**7/7 逐字相符**（`ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` / `9dc67a76…a62b` / `09f1ac61…524c` / `71f65dca…0f85`——F7 的全 64 位改正值本轮再验）；attempt-1 void hold **恰 10 份、零隐藏项** ✓；四个 release pointer 均不存在 ✓；corridor 实测 SHA = config `artifact_sha256` = `9e2956ad93a4a81cf638a913b9c806e1a316616bf090b125641d3f5c0b7fc800`、`prisms` **779** = `instance_count`、`policy.tether_corridor_check = true` ✓ |
| B4 槽位机件探针（副本内直接调用） | `canonical_trial_id('…arm-b-trial-4')` 返回自身、`_expected_policy` = `threshold`、`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`、`expected_acquisition_ids('b')[3]` 逐字相等、`…-trial-4-attempt-1/-2` 与 `…-arm-b-trial-6` 均 `run_id_not_frozen_trial`、`runtime/runs/p1-m3-body-001-arm-b-trial-4/` 不存在——revision 23 §1 与 §2.22 第 9 项的机械主张**全部证实** |
| §4 CLI 块（四个 git 状态字节级） | 19 行整块提取另取 SHA：`8820678`（rev 23）与 `50e7d38`（rev 24）**同一 SHA `154b06a6…dee2f`**，证实 revision 24「§4 CLI 对 revision 23 一行不差」；对 `6e81bc2` **恰 1 行**（`--run-id`，同臂轮换）；`6e81bc2` 整块 SHA = `fd832df1b6a7a7b02cc00d25a1c3bdf5f25b39aecef551718668ad418dcd55dd`，证实接受轮 66 §B 的 `fd832df1…`；对 `408acd7` 恰 2 行（`--run-id` + `--body-policy`），历史陈述属实 |
| §2.21 四个 destination | `frames.unreleased-play-20260820-hold/`、`m3_body_truth.…-hold.jsonl`、`metrics.…-hold.json`、`test-results/…-shared-residue-3of6/` **均不存在** ✓（「移动前必须不存在」成立） |

### 2. 逐文件核对（8 个路径，实现者声明的范围只作待核实主张）

1. **操作单（PLAY_GOVERNING 唯一成员）**：revision 24/23 抬头 + §1 采集 ID 行轮换到
   B4（旧 B3 行降为「（历史）」）+ §2.19/§2.20 转历史 + **新增 §2.21/§2.22** +
   §3 步骤 0′/门 1/步骤 4/5 + 门 4 token 块 + §4 CLI + §5 前提块 + §6 N36 头。
   **轮换完整性本轮全文 sweep**：1230 行之后活跃指令中的 `arm-b-trial-3` 只余
   §2.22 第 4 项的第八条 `--verify`（正确）、§2.21 的 B 组来源说明（正确）与
   §3 步骤 0′ 的**历史例示**（「例如 revision 22 的 §2.20 具名…」，正确）；
   §3 步骤 4/5、门 4 token、§4 CLI 全部为 `-trial-4`。**F8/F9/F10 那类「轮换只改
   声明清单、活跃绑定留在上一轮」的失效本轮零发现。**
2. **`408acd7` 写死问题（轮 66 修复）验真**：操作单全文 `grep -c 408acd7` 在
   `1b3cbd1`/`67b2ac7`/`50e7d38` 三个状态**恒为 6**；本轮逐处判性质——L68/L91/L93
   （revision 22/21 抬头）、L1623（§4 散文）、L1815（§6 revision 19 条目）五处
   **全部已改为「历史事实 / 时间边界 + 一律实测」**，第 6 处 L533 是 §2.0 (b) 的
   历史例示段且自带「不得套用于 B1」告诫，**保留正确**。实现角色 §C.4 第 2 条
   自陈「漏列，实为 6 处」与接受轮 66「五处活跃全改到」两说**本轮均属实**。
3. **F11 闭合核查（定点复看，按轮 12 处方三处位点）**：账本两条 2026-08-14 条目
   本轮逐字对读——批量 GO 条排除清单原文「**不覆盖** `--compare`（需十次齐备并
   **单独授权**）、任何重试/重进/调参、任何协议/指标/阈值/测量窗/载体/统计量
   变更」与操作单 §5 现文**逐字相符**；R10/R11、R12 已移出该条，改列「另按在案
   现状继续排除（**非批量 GO 条文——不得记到该条名下**）」并注明依据是
   COORD-007 账本 2026-08-12 未授权 + B1 单次 GO 条曾点名；B1 条同时点名的
   「臂 B trial 2–5」明写「已被批量 GO 取代，不在此转录」；**「不作增减」的自证
   已删除**。提案 D′ 第 2 项与状态板同批更正。**F11 关闭。**
4. **P8/P9 闭合核查**：P9 —— D′ 开头已改为「上批落地后本角色自查仍留存的残项
   （第 1、2 项，认定与撤回均本角色自判）」并逐字记账「把自查结果记到独立复核
   名下属出处虚指」，**关闭**；P8 —— 已改为时间边界表述，本轮验其事实：轮 11 记录
   `1528288` 范围恰 `9cadebd..6e81bc2` 一个提交，而 `a5fc735^` = `1528288`，
   续批确不在也不可能在其范围内，**关闭**。**P7 维持随 (c) 批次复判**（本轮不动）。
5. **B3 的 (c) 记录（`docs/unity-test-log.md`）**：写入时 HEAD 自称
   `6b138ea1f2a5033f4c772b19f9c0db29c8d2c5e2`——本轮实测 `0d52e12^` **正是该 SHA**，
   即 (c) 之后确无提交先于 Play 落地，(d) 的实质判据成立；`6e81bc2..6b138ea`
   **恰 5 个路径全为文档**、测量侧（七类路径）diff **为空**——(b) 归因逐项证实。
   B3 与 A1…A5、B1、B2 跑在同一份已复核代码字节上。
6. **B3 四门与握手（轮 67 §A / 证据 §D）**：门 1 `reported_sim_t =
   4.980350971221924` ∈ `[2.000000, 10.000000)`，两侧余量 `2.980` / `5.020`
   （本轮算术复核相符）；门 2 最低帧 `0`；门 3 用户逐字「匹配」；门 4 两 token。
   dwell `76.803711 s` / laps `1.952997` 本轮独立交叉验证：`final_unwrapped_
   mileage_m 415.9308532790733` ÷ `route_perimeter_m 212.97056274847716` =
   `1.95299…` ✓；`2P − 415.93085` = `10.0103 m` ✓；且**保留帧末帧 `frame_1034` 的
   `capture_unix_s 1786939588.328` 减去 B3 末次发布 `issued_unix_s 1786939511.567`
   = `76.761 s`**，与 dwell 同量级同值——三条独立路径互证。
7. **`docs/authorizations.md` 新条**：三项选项为用户逐字原话，接受角色的读法与
   用户原话分栏、明写「不替用户扩权」；「§2.21 不在推迟之列」标注为接受角色判断
   并披露理由。**本轮未发现替用户扩权或把接受角色判断混记为用户授权。**
8. **`docs/implementation-status.md` / `docs/current-status.md`**：B3 第三次确认、
   n=2 方向性读法撤回、下界口径不变——与磁盘数字逐项相符。**但两者都转载了
   revision 24 的损失范围表述，故同受 F12 影响**（见下）。
9. **`docs/proposals/…`（接受轮 65/66/67/68）**：339 行纯新增，零删除；轮 68 §D.4
   自称「七个聚合缩写与源节全 64 位逐个比对 7/7 相符」，本轮**改按磁盘重算，同样
   7/7** ——该自查属实。轮 68 §D.1 自称「实测：仓库内无任何工具按 `post-run`
   检索」，本轮 grep 证实：`tools/`、`tests/`、`controller/`、`config/`、`Assets/`
   中唯一涉 `test-results` 的是 `tools/calibrate_pixel_sigma.py:62`，且是**写死的
   单一路径、不做任何 glob**；`preflight_reanchor_env.py` 的 `run_directories` 只枚举
   `runtime/runs` 直接子目录（`RUNS_ROOT = "runtime/runs"`），与 `test-results/` 无关。

### 3. 本轮 finding

#### F12 —— CLASS_1（阻断）：§2.21 A 组把 B3 的 256 份保留帧误归为 08-20 那次未放行 Play 的产物

**处置对象**：操作单 §2.21 A 组表首行、§2.21 背景段、§2.22 第 5 项注解与第 7 项、
B 组目录名 `…-shared-residue-3of6`，以及转载同一表述的提案轮 68 §B/§C、
`docs/implementation-status.md`、`docs/current-status.md`、`docs/unity-test-log.md`。

**磁盘实测（只读，四条独立证据链）**：`runtime/frames/` 的 **315 项不是同一次
Play 的产物**，而是两次 Play 的叠加——

| 组 | 项数 | frame id | mtime | 包内 `capture_unix_s` / `published_unix_s` |
|---|---|---|---|---|
| B3（2026-08-17） | **256**（128 帧 ×2） | **907…1034** | `2026-08-17 00:06:02` → `00:06:28` | `frame_1034` = `1786939588.328` → 2026-08-17 00:06:28 |
| 08-20 未放行 Play | **59**（29 帧 ×2 + `latest.json`） | **0…28** | `2026-08-20 14:30:07` → `14:30:13` | `frame_28` = `1787250613.018`；`latest.json` `frame_id 28` / `published_unix_s 1787250613.018` |

1. **逐文件 mtime**：256 / 59 的二分是干净的，无交叉。
2. **frame id 分段**：907…1034 与 0…28 不重叠；后者从 0 重新开始，正是新 Play 的
   计数复位。
3. **包内时戳**（与文件系统无关）：`frame_0000001034.json` 的
   `capture_unix_s = 1786939588.328`、`simulation_time_s = 206.9873046875`；
   `frame_0000000028.json` 的 `capture_unix_s = 1787250613.018`、
   `simulation_time_s = 5.784574508666992`。
4. **机制**：`Assets/TetheredTracking/Scripts/SensorFrameWriter.cs:212` 的
   `DeleteExpiredFrame(framesDirectory, publishedFrameId - retainedFrameCount)`
   （`retainedFrameCount = 128`，L106）**按 frame id 淘汰，不按 mtime**。新 Play 从
   id 0 起算，其淘汰窗口够不到上一次 Play 的高位 id，因此 B3 的 907…1034
   **原地幸存**。这条机制同时解释了「为什么正好是 128 帧」：七处 post-run 归档的
   `frames/` **恰 257 项** = 128×2 + `latest.json`，与本轮实测一致。

**算术闭合**：`1034 − 650 = 384` 帧，`384 / 5 Hz = 76.8 s`，与 B3 的 dwell
`76.803711 s` 相等——907…1034 正是 **B3 tracker 收尾后停留期的保留帧尾**，
归属无第二种解释。

**缺陷**：revision 24 §2.21 A 组把 `runtime/frames/` **整目录**（315 项、聚合
`274e9804…2d4c`，本轮按 §B.3 口径重算**相符**）移入
`runtime/frames.unreleased-play-20260820-hold/`。执行后，**B3 仅存的 256 份保留帧
将被装进一个名称断言「这是 08-20 那次未放行 Play 的产物」的 hold**——这正是
revision 24 抬头 C 条自己写下的、要用来否决 revision 23 的那条理由（「会给 B3
仅存的字节贴上错误标签，且那是最后一次能给它们贴正确标签的机会」）在同一节内
被违反。**移动前重测六项的 fail-closed 门挡不住它**：那六个钉住值本轮实测**全部
相符**（315 项 + `274e9804…`、29 行/30300 B/`7c6eb5f7…`、61 行/2020 B/
`c3bb6f6d…`、15 行/331 B/`f79bc73d…`、15 行/341 B/`6f9358d2…`、18 行/454 B/
`3c677ab6…`），所以门会全过、归属错误照样落地。该门防的是「现场又被写过」，
不防「归属判错」。

**连带的事实性错误（同一根因，四份文档）**：

- §2.21 背景段「**只覆盖了六项 shared 成员中的三项**（`frames/`、
  `m3_body_truth.jsonl`、`metrics.json`）」——对 `frames/` 不成立：该成员被覆盖的
  只有 `latest.json` **1 项**，B3 的 256 份帧文件字节完好。
- §2.22 第 5 项注解「其六项归档源中的三项（`frames/`、…）已被…覆盖而**永久不存在**」
  ——对 `frames/` 为假。
- 据实的损失范围应为：**两项全损**（`m3_body_truth.jsonl`、`metrics.json`）、
  **一项损失 257 之 1**（`frames/latest.json`）、**三项完好**（三个发布文件）。
  轮 67 记 6/6 是高估，轮 68 收窄到 3/6 **仍是高估**。
- 目录名 `…-shared-residue-**3of6**` 因此低报了 B3 实际幸存的份额；§2.22 第 10 项
  的「**恰 3 项**」同样需要随之重算。
- **结论层不翻案**：`m3_body_truth.jsonl` 与 `metrics.json` 确已永久覆盖，故
  **「B3 的完整 post-run 归档（六项）永久不可能」成立**，「归档 7 处 < 有效 run 8 次」
  成立，B3 的有效性与绑定证据（run 目录 create-once + 八条 `--verify`）**完全不受
  影响**。本 finding 改的是**归属与损失范围**，不是任何 disposition。

**根因**：轮 68 §B 的表格给 `runtime/frames/` 只记了**一个** mtime
（`2026-08-20 14:30:13`，即目录 mtime = 其最新条目的时间），未做逐文件 mtime /
frame id 分布核对，也未把 `SensorFrameWriter` 按 id 淘汰的机制纳入推理。这与轮 68
自己纠正轮 67 的方式同型——**轮 68 把「tracker 未启动 ⇒ 发布文件没被写过」推到位，
却没把「Unity 侧只追加、按 id 淘汰 ⇒ 上一次 Play 的高位帧不会被删」推到位**。

**紧迫性（与处置顺序直接相关）**：B3 的 256 份帧只在「后续任何 Play 发布到
frame id ≥ 1035」之前存活；B3 自己那次 Play 就跑到 1034，故一次时长相当的 B4
在其尾段就会开始逐帧删除它们。**这是加强而非削弱「§2.21 先行」的理由**——但必须
先按来源改正 A/B 两组的划分再执行；照现文执行会把最后一次正确标注的机会用掉。

**分级依据**：改数字（315 → 59 / 256 的归属拆分、`3of6`、§2.22 第 7 与第 10 项的
期望值）且改事实结论（损失范围），落在 CLASS_1；且 §2.21 是**不可重来的一次性
现场处置**。

**闭合方式**：`NOT_MECHANIZABLE`（对象是未纳入版本控制的 `runtime/` 字节与操作单
散文，仓库内无可写断言的生产路径 fixture）。闭合 = 下一轮**定点复看**改正后的
§2.21 两组表、§2.22 第 5/7/10 项、B 组目录名，以及四份转载文档的对应句；修复后
PLAY_GOVERNING diff 非空，按 §4.4 R1 开轮资格成立。**在闭合前 §2.21 不得执行、
不得进入 Play。**

#### F13 —— CLASS_2（阻断）：§2.21 是本轮唯一待执行且已放行的节，却没有具名落盘地

§2.20 与 §2.22 都在节内写明「结果落盘于 `docs/evidence/P1-M3-BODY-001-arm-b-trial-N.md`」，
§2.19 事后补了指针。**§2.21 全节无一句指定证据落盘地**（本轮 grep 该节：无
「落盘」「证据文件」「记入」「arm-b-trial-4」）。而 §3 步骤 0′ 的单一事实源规则
指向的是「**当轮 §2.x Play 前核对节**开头具名者」= §2.22 —— 但 §2.22 被本批次
明令**冻结在复核结论之后**，且其标题限定为「B4 的 Play 前状态核对」。于是现在
被单独放行去执行 §2.21 的实现角色，手上没有一条在效的落盘指令：把 §2.21 的
移动前后实测写进 `…-arm-b-trial-3.md`（本节讲的是 B3 的残留）与写进
`…-arm-b-trial-4.md`（本轮的证据文件）都说得通，而接受角色按交接要「rules §2.21's
six before/after equalities」时只会看其中一处。

本文件已经因同一族缺陷付出过代价（复核轮 10 **F9**：「指错文件等于条款落空」）。
按 §4.4 分级判据「操作员的行为会不会因这段文字而不同」——会。故 CLASS_2，
不入 CLASS_3 闭集。**危害有限**（两个候选落点都在仓库内、都可事后合并），但修复
只需一句话，且必须在 §2.21 执行**之前**落地。

**闭合方式**：`NOT_MECHANIZABLE`，闭合 = 下一轮定点复看 §2.21 节内新增的落盘地
指定句。

#### P10 —— CLASS_3（不阻断，逐字替换补丁，交接受角色独立复判）

§2.22 第 6 项丢了 §2.19（L1218）与 §2.20（L1290）都带着的出处指针，使「八个具名
标记」在 §2.22 内不可解析。属**失效/缺失链接**，在 CLASS_3 闭集内，不涉数值、
阈值、ID、判据、执行顺序或终态名。

- **文件**：`docs/evidence/P1-M3-BODY-001-1c-preflight.md`，§2.22 表格第 6 行
  （现行 L1377）。
- **原文（逐字）**：

  ```text
  | 6 | 活动标记 + attempt-1 void hold | 八个具名标记均不存在；void hold 仍**恰 10 份、零隐藏项**，三钉住 SHA 相等 |
  ```

- **替换为（逐字）**：

  ```text
  | 6 | 活动标记 + attempt-1 void hold | 八个具名标记（出处见 §2.16 第 6 项）均不存在；void hold 仍**恰 10 份、零隐藏项**，三钉住 SHA 相等 |
  ```

**本角色不亲手应用**；由接受角色独立复判分级后同轮应用，不得借此改动任何数值、
哈希、run ID 或 disposition。**P7 仍随 (c) 批次复判，本轮不动。**

### 4. 观察（登记，非 finding）

- **N42 —— B 组落点与既有保全惯例不一致。** 项目里既有的四处 shared 侧保全
  一律是 `runtime/<name>.<label>-hold.<ext>` 平铺（如
  `body_command.arm-a-trial-1-void-attempt-3-hold.json`、
  `frames.arm-a-trial-2-void-attempt-1-hold/`），而 revision 24 的 B 组新建在
  `runtime/test-results/` 下——**七处 post-run 归档正住在那里**。轮 68 已用目录名
  （含 `3of6`、不含 `post-run`）与 §2.22 第 10 项做了缓解，本轮也证实**无任何工具
  按 `post-run` 或 glob 检索该目录**，故当前无机械风险，不构成 finding。仅登记：
  F12 的返工本就要重划两组并改名，接受角色可在同一批次一并考虑落点是否回到既有
  惯例。
- **N43 —— 「移动前重测」门的能力边界，建议在返工时写明。** §2.21 的六项重测门
  只能证明「现场自钉住起未再被写过」，**不能**证明归属判定正确（F12 即是门全过而
  归属错）。返工若沿用该门，宜同时要求按 frame id 段 + 包内 `capture_unix_s` 做
  归属复核，而不只比对聚合值。

### 5. 复核债结算

`6e81bc2..50e7d38` 的四批债（F11 返工、轮 66 归因修复、revision 23、revision 24）
经本轮**逐文件核对清偿**，代之以 F12/F13 的闭合义务与 P10 的应用义务。COORD-007
`R5` 行本轮无新增动作。

### 6. UNITY_NA 立场

本区间**未申领** `UNITY_NA`，本轮**附议不申领**：B3 的 Play 与用户目检已发生并
经轮 67 归因，Unity 列由该次采集承载，不存在需要另判 `UNITY_NA` 的离线事项。
`--compare`、任何调参、任何协议/统计量变更继续无 GO。

### 7. Verdict

**Round 13: REWORK_REQUIRED（candidate `50e7d38`）。**

一条 **CLASS_1** 阻断 finding（**F12**：§2.21 A 组把 B3 的 256 份保留帧误归为
08-20 未放行 Play 的产物；四条独立证据链 + 写盘器按 id 淘汰的机制 + `1034 − 650 =
384 帧 = 76.8 s = dwell` 的算术闭合；连带「损失 3/6」在四份文档中仍属高估——实为
两项全损、`frames/` 只损 `latest.json`、三项完好）+ 一条 **CLASS_2** 阻断 finding
（**F13**：唯一已放行待执行的 §2.21 无具名落盘地）+ 一条 **CLASS_3** 逐字补丁
（**P10**：§2.22 第 6 项缺出处指针）。

**本 verdict 明确不推翻的事项**：A1…A5、B1、B2、**B3** 的有效性与轮 60/63/67 的
归因（八条 `--verify` 冻结 receipt 由本轮在副本内亲自逐字复现，B3 的四门、握手、
臂身份三层与全部运动指标独立重算相符）；「B3 的完整 post-run 归档永久不可能」与
「归档 7 处 < 有效 run 8 次」；轮 67 §C.3 的 GO 计数裁定及用户 2026-08-20 的维持
（B4/B5 各一次 Play 仍在）；批量 GO 的边界与两条预登记限制的下界口径；F11/P8/P9
的闭合；轮 66 五处写死候选的修复；revision 23/24 的槽位轮换、§4 CLI（对 rev 23
字节相同、对已复核候选恰 1 行）与 §2.22 第 3/4/5/6/9 项的全部期望值。

**处置顺序（本角色只给复核结论，取舍归接受角色与用户）**：F12 改的是一次性、
不可重来的现场处置的**归属划分**，而 B3 那 256 份帧只在下一次 Play 发布到
frame id ≥ 1035 之前存活。故本轮的结论是——**§2.21 仍应先行，但不得按现文执行**：
先由接受角色按 F12 改正 A/B 两组划分与目录名、按 F13 补落盘地（并复判 P10），
再执行保全。**在此之前不得进入 Play**；§2.22、§2.0 (b)/(c) 依用户 2026-08-20 的
放行条件继续等待。

按 R7，`REWORK_REQUIRED` 轮**不写** `passed_candidate` 行；「上一通过候选」维持由
round 11 的机读行派生（`6e81bc2…`）。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现文件。**
`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零触碰；操作单、提案、
账本、Unity 日志、证据文件零触碰；**`runtime/` 零写入**——全部实测为 `ls`/`stat`/
`shasum`/只读 `open()` 与 `--verify`（`analyze_m3_body.py:883` 跳过 `_collect_inputs`、
L1494 在 `write_text` 之前返回，本轮先读码确认再运行），收工 `git status
--porcelain` 主树为空且六项 shared 成员的 mtime/字节/SHA 与开工时逐字相同。
测试与探针全部发生在一次性副本 `.claude/worktrees/review-P1-M3-BODY-001` 内
（`runtime/runs` 以符号链接只读挂入，`ArchivedRunLoopDomainTests` 自身把归档字节
拷进临时目录后才分析）；CLI 块字节比对在会话 scratchpad 内完成。主树唯一写入为
本文件与 `docs/current-status.md` 的交接更新。副本收工 `git worktree remove
--force` 删除。本轮未推送任何提交（无推送授权申领）。

## Round 14 — 轮 13 返工闭合轮（F12/F13 定点复看 + §2.21 执行后的现场实测）

Date: 2026-08-20

- 复核对象：接受轮 69（`c776f8b`，revision 25）+ §2.21 执行批次（`fcb22a7`，实现角色）。
  闭合方式按轮 13 verdict：F12/F13 均 `NOT_MECHANIZABLE` → **定点复看具名文件**；
  但本轮的对象不只是散文——**§2.21 已经在磁盘上执行了**，故本轮把改正后的两张钉住表
  与执行结果**一并对磁盘实测**。
- Candidate: **`fcb22a75b3b7c83fb8b31e527683d1467df6cb1f`**（HEAD）。上一通过候选由本文件
  最近一行 `passed_candidate` 派生 = **`6e81bc2…`**（轮 11；轮 12/13 均
  `REWORK_REQUIRED`，未写该行）。
- **开轮资格（§4.4 R1）本轮自验**：`git diff --name-only 6e81bc2..fcb22a7` 在
  PLAY_GOVERNING 上非空、**恰一条** = 操作单（revision 25）。全区间 **14 个提交 /
  9 个路径**，`tools`/`tests`/`controller`/`Assets`/`config`/`ProjectSettings` 六棵树
  两端**逐项相同**；`docs/authorizations.md` 在 `50e7d38..fcb22a7` 上**零字节**
  （本批次未申领任何新授权）。
- 复核副本：`git worktree add --detach .claude/worktrees/review-P1-M3-BODY-001-r14
  fcb22a7`，收工已删除；副本内以符号链接只读挂 `runtime/runs`。**`runtime/` 零写入**
  （收工主树 `git status --porcelain` 为空；`find runtime -newermt "2026-08-20 15:00"`
  只返回 §2.21 那次移动本身影响的四个目录 inode，无新增文件）。

### 1. F12（CLASS_1）—— 关闭

改正后的 §2.21 两张表**逐项对磁盘实测相符**，且执行结果与表一致：

| 轮 13 处方 | revision 25 / 执行结果 | 本轮实测 |
|---|---|---|
| 按来源重划 A/B | B 组 = id **907…1034** 的 **256** 项；A 组 = id **0…28** 的 58 项 + `latest.json` = **59** 项 | `frames.arm-b-trial-3-shared-residue-hold/` **256** 项、id 段恰 `[907,1034]` 全 128 个、**无 `latest.json`**、mtime 全为 2026-08-17；`frames.unreleased-play-20260820-hold/` **59** 项、id 段恰 `[0,28]`、含 `latest.json`、mtime 全为 2026-08-20。**两段无交叉** |
| 两组聚合钉住值 | `568b6b98…a815` / `39698be4…9a7f`；`bytes_total` `5513679` / `939238` | 按 `…-arm-a-trial-2.md` §B.3 口径重算：**两个聚合、两个字节总数全部逐字相等** |
| 五个平铺 destination | 行数/字节/SHA-256 见 §2.21 两表 | 五项**全部等于本角色轮 13 亲自实测的原值**（`f79bc73d…`/`6f9358d2…`/`3c677ab6…`/`7c6eb5f7…`/`c3bb6f6d…`，行数字节同）——即移动**零字节改动** |
| **无损无串组的独立证明（本轮新增）** | —— | 把两个 hold 的 `shasum -a 256 *` 输出**合并后排序再取 SHA**，得 **`274e9804098c337d02245c64780c349c5c886c6633e4d8e7e1364d8da3e52d4c`**，与轮 13 记录的**移动前整目录聚合逐字相等**。315 = 256 + 59，**没有一份文件丢失、改名或被分错组** |
| 落点回既有惯例（N42） | 撤销 `test-results/…-3of6/`，改四处平铺 `runtime/<name>.arm-b-trial-3-shared-residue-hold.<ext>` | `runtime/test-results/` 下**无任何** `residue`/`3of6` 条目，只有七处 `*-post-run`；四处平铺 hold 与既有 void hold 同构。**`3of6` 已从所有名字里去掉** |
| 损失范围据实收窄 | 两项全损 + `frames/latest.json` 一项 + 三个发布文件与 256 帧完好 | 与实测一致；**结论层未翻案**——`m3_body_truth.jsonl`/`metrics.json` 确已永久覆盖，完整六项归档永久不可能，归档 7 处 < 有效 run 8 次 |
| 四份转载文档同批更正 | 提案轮 68 §D.1 加不可执行标注、`implementation-status.md`、`current-status.md`、`unity-test-log.md` | 四处**逐一复看，全部改正**；全仓 grep 后，`3of6` 与「3/6 / 六项中的三项」的**残留全部落在历史节（revision 24 抬头已加取代横幅、提案轮 68 为 append-only 历史记录）或本复核文件的 finding 描述内**，活跃指令区（操作单 1350 行之后）**零残留** |

**执行本身的承重核对本轮亲自复跑**：八条 `--verify`（A1…A5 + B1 + B2 + B3）全部退出 0
且逐字复现冻结 receipt；focused `test_analyze_m3_body.py` **67/67 OK 零 skip**；
七处 post-run 归档各恰 6 项 / `frames/` 各 257 项、七个聚合逐字相符；四处旧 hold
`257/93/109/257`、attempt-3 run hold 恰 2 文件、attempt-1 void hold 恰 10 份零隐藏项；
八个 run 目录各恰 11 份、B4 run 目录不存在；`runtime/frames/` **`ls -1a` 只有 `.` 与 `..`**
且目录本身保留；六个 shared 文件（含 `scenario_config.json`）全部不存在；
corridor `9e2956ad…c800` / **779** 棱柱 / `tether_corridor_check = true`。
另跑预检：退出 **0**、`status = PASS`、`side_effect_identity.unchanged = true`、
四个 guarded 文件均 `present = false`、`run_directories` **35**（含 B3、不含 B4——
历史记录的 34 是 B3 run 目录建立之前的数，本轮据实登记差异来源）。
`find runtime -type f -newermt 2026-08-18` 在 `test-results/` 与 `runs/` 下**零命中**
——七处归档与八个 run 目录**一个字节都没被碰过**。

**归属证据在移动后仍然在位**：`mv` 保留 mtime，故 B hold 全部仍是 2026-08-17、
A hold 全部仍是 2026-08-20；包内 `capture_unix_s` `1786939588.328` / `1787250613.018`
与 `latest.json` 的 `frame_id = 28` 三项本轮在**新位置**复读，逐字相符。**F12 关闭。**

接受轮 69 §A 独立复算了四条证据链并**照单接受**，§B 逐字写明自己的根因（只读目录
mtime、未把按 id 淘汰的机制推到位），并采纳 **N43** 把移动前的门由一项扩为两项
（新增归属复核）。实现角色执行时该门实跑 **38/38**（含七个 destination 移动前均不存在
7/7），移动后 **36/36**，且在八条 `--verify` **之后**又跑一遍仍 36/36——`--verify` 对
两个新 hold 零副作用是实测而非假定。上述计数本轮逐项复算相符。

### 2. F13（CLASS_2）—— 关闭

§2.21 现在节首明写「**结果落盘于 `docs/evidence/P1-M3-BODY-001-arm-b-trial-4.md`**
（F13 补；先例见 §2.19，与 §2.22 同一文件）」，与 §2.22 的落盘地**同一文件**，
轮 13 指出的两可性消除。实测：`docs/evidence/P1-M3-BODY-001-arm-b-trial-4.md` 存在，
§A 即 §2.21 的执行记录，接受角色要复算的「七项前后相等」与 §2.22 的十项落在一处。
**F13 关闭。**

### 3. P10（CLASS_3）—— 已按逐字补丁应用

§2.22 第 6 项现为「八个具名标记（出处见 §2.16 第 6 项）均不存在；…」——与轮 13 给出的
替换文本**逐字相同**，与 §2.19/§2.20 同款。接受轮 69 §C 独立复判后同意 CLASS_3，
**零数值/哈希/ID/disposition 改动**（本轮 token 多重集复算佐证，见下）。**P10 关闭。**
**P7 维持随 (c) 批次复判，本轮不动。**

### 4. 冻结值与非回归复算

- **冻结值 token 多重集（`50e7d38` → `fcb22a7`，操作单全文计数）零减少**：
  `212.9706`(5)、`130.0`(7)、`0.5645`(5)、暂停窗两端(9/9)、`(177,195,77,73)`(6)、
  `62.5`(5)/`31.25`(4)、`9e2956ad`(7)、`run_id_void_consumed`(4)、
  `run_id_not_frozen_trial`(10)、握手词(5)、四种 void 终态名、`SCENE_DEGENERATE`(8)、
  `threshold-corridor-v1`(9)、B2 归档 64 位全值(2) 全部不变；被禁弦长 `83.197`
  **零出现**。
- **64 位全值**：新增两个（`568b6b98…` / `39698be4…`），减少一个
  （`274e9804…2d4c`，即移动前整目录的聚合——它描述的状态已不存在）。**该值并未失去
  可核性**：本轮已证明两个新聚合的**并集重算恰好等于它**，且它逐字留存于轮 13 复核
  记录与 revision 24 的 git 历史。
- **§4 CLI 块**：`8820678`（rev 23）/ `50e7d38`（rev 24）/ `fcb22a7`（rev 25）三个状态
  提取件**同一 SHA-256 `154b06a6353249d5a192b5b8464aaaa8a0002b51cd7a948c69b89f3abf9dee2f`**
  ——revision 25「§4 CLI 对 revision 23/24 一行不差」字节级证实；对通过候选 `6e81bc2`
  仍恰 1 行（`--run-id`，同臂轮换）。
- **改动范围**：操作单 diff **恰两个 hunk**（抬头 + §2.21/§2.22），`@@ -1,4 +1,53 @@`
  与 `@@ -1301,84 +1350,101 @@`——「其余条款逐字不变」结构上成立；`fcb22a7` 只动
  状态板与新证据文件两个路径，实现角色「操作单本批次一字未改」属实。

### 5. 本轮 finding

#### P11 —— CLASS_3（不阻断，逐字替换补丁，交接受角色独立复判）

§2.21 已于 2026-08-20 执行完毕（本轮实测确证），但节标题仍写「**本轮第一步，待执行**」，
而同文件 §2.19/§2.20 的已执行节一律写「**已执行**」。属**已执行步骤的时态**，正在
§4.4 的 CLASS_3 闭集内，不涉数值、阈值、ID、判据、执行顺序或终态名。**方向 fail-closed**
（照字面重跑会在「每个 destination 移动前必须不存在」当场停住，源也已不存在），
实现角色亦已在证据 §A.7 主动登记「属修订级改动，由接受角色轮换，本角色不代劳」。

- **文件**：`docs/evidence/P1-M3-BODY-001-1c-preflight.md`，§2.21 节标题（现行 L1353）。
- **原文（逐字）**：

  ```text
  ### 2.21 现场按来源分离保全（revision 25，**本轮第一步，待执行**）
  ```

- **替换为（逐字）**：

  ```text
  ### 2.21 现场按来源分离保全（revision 25，**已执行**，2026-08-20）
  ```

补丁**只改时态**，不加计数；是否按 §2.20 的先例把 `38/38 + 36/36` 一并写进抬头，
属接受角色的编辑裁量，本角色不代拟。**本角色不亲手应用。**

### 6. 观察（登记，非 finding）

- **N44 —— 两个「六」不同集，建议下次修订顺带消歧。** §2.22 第 1 项的「**六个 shared
  文件**」= 五个发布/度量文件 + `scenario_config.json`（`frames/` 由第 2 项单列），
  而 §2.21 与 §2.22 第 5 项的「**六项 shared 成员**」= `frames/` + 五个文件。两者都叫
  「六」而集合不同。当前**无操作歧义**（第 1 项的括注点名 `scenario_config.json`，
  第 2 项单列目录），且是 §2.16 起的既有措辞，本批次未引入，故不构成 finding。
- **N45 —— 并集等式值得写进 §2.22 的出处。** 「两个 hold 的聚合并集 = 移动前整目录聚合
  `274e9804…2d4c`」是把移动前后**唯一**用哈希连起来的等式（§2.21 的门 2 用的是计数与
  id 段，不是哈希）。本轮已实测并记入本文件，可核性已永久锚定；接受角色若愿意，可在
  §2.22 第 7/10 项加一句出处，纯属加固。

### 7. UNITY_NA 立场

本区间**未申领** `UNITY_NA`，本轮**附议不申领**：§2.21 是磁盘保全动作，零 Play、
零采集 ID、零 Unity 面；B3 的 Unity 证据由轮 67 已归因的那次采集承载，不存在需要另判
`UNITY_NA` 的离线事项。`--compare`、任何调参、任何协议/统计量变更继续无 GO。

### 8. Verdict

**Round 14: PASS_WITH_NOTES（candidate `fcb22a7`）。**

**零 CLASS_1、零 CLASS_2。** 轮 13 的两条阻断 finding **全部关闭**：**F12** 由改正后的
§2.21 两表 + 执行结果对磁盘逐项实测关闭（并集聚合重算 `274e9804…2d4c` 证明 315 项
无丢失、无串组、无字节改动），**F13** 由 §2.21 节首具名落盘地关闭；CLASS_3 **P10**
已逐字应用。新增一条 CLASS_3 **P11**（§2.21 抬头时态仍写「待执行」，逐字补丁见 §5），
**P7** 维持随 (c) 批次复判。

**本轮明确不推翻的事项**：A1…A5、B1、B2、B3 的有效性与轮 60/63/67 归因（八条
`--verify` 本轮亲自逐字复现）；「B3 的完整六项 post-run 归档永久不可能、归档 7 处 <
有效 run 8 次」；轮 67 §C.3 的 GO 计数裁定与用户 2026-08-20 的维持（B4/B5 各一次
Play 仍在）；批量 GO 的边界、两条预登记限制的下界口径与 BC-BODY1-15 (d) 的反调参纪律；
全部冻结值与 §4 CLI 块。

**放行状态（复核只给结论，取舍归接受角色与用户）**：用户 2026-08-20 的放行条件是
「B4 的 Play 放行前必须有一轮独立复核结论」。轮 13 已给出结论并被完整返工，**本轮
`PASS_WITH_NOTES` 是该条件下的通过结论**；轮 13 附加的「§2.21 改正后方可执行」也已
满足并执行完毕。据本角色所见，**§2.22（十项）→ §2.0 (b) → (c)/(d) 的释放不再被任何
复核项阻断**；P11 是不阻断的时态补丁，可与 P7 同批应用。是否释放仍由接受角色按用户
条件裁定，本角色不代为放行。

按 R7，本通过轮写机读指针：

passed_candidate: fcb22a75b3b7c83fb8b31e527683d1467df6cb1f

此后「上一通过候选」由本行派生（`grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md
| tail -1`），无需任何手写更新。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现文件。**
`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零触碰；操作单、提案、账本、
Unity 日志、证据文件零触碰；**`runtime/` 零写入**——全部实测为 `ls`/`stat`/`find`/
`shasum`/只读 `open()`、`--verify`（`analyze_m3_body.py:883` 跳过 `_collect_inputs`、
L1494 在 `write_text` 之前返回）与 `preflight_reanchor_env.py`（自证
`side_effect_identity.unchanged = true`）；收工复测五个平铺 hold 与两个 hold 目录的
计数/字节/SHA 与本轮开工时逐字相同，`find runtime -newermt "2026-08-20 15:00"` 无新增
文件。测试与探针全部发生在一次性副本 `.claude/worktrees/review-P1-M3-BODY-001-r14` 内
（`runtime/runs` 以符号链接只读挂入）；聚合与 CLI 块比对在会话 scratchpad 内完成。
主树唯一写入为本文件与 `docs/current-status.md` 的交接更新。副本收工
`git worktree remove --force` 删除。本轮未推送任何提交（无推送授权申领）。

#### Round 14 收工补记（同角色续会话，2026-08-20）

**为什么有这一节**：写下 Round 14 的复核会话在**落盘之后、提交与副本清理之前意外
终止**（用户确认）。续会话（同为复核角色）接手收工。按「轮次只追加、不删除旧发现」，
上文 Round 14 的正文与 verdict **一字未改**；本节只补三件事——续会话的独立复算、
一处已失效的边界陈述更正、一条措辞范围的收窄。

**1. 续会话在自己的一次性副本里从头复算，Round 14 的承重结论逐项复现。**
副本 `.claude/worktrees/review-P1-M3-BODY-001-verify`（另起 `…-pf` 一个用于预检），
`runtime/runs`/`models`/`yoloe` 只读挂入或 `cp` 拷入，收工均已 `--force` 删除。

| 复算项 | 续会话实测 |
|---|---|
| B hold | **256** 项、id 恰 `[907,1034]` 全 **128** 个、**无 `latest.json`**、mtime 全 2026-08-17；聚合 `568b6b984376211b430ce1c016607e3cda3c3ba26c1ac43ef3ec4a1060d9a815`、`bytes_total` **5513679** |
| A hold | **59** 项、id 恰 `[0,28]` + `latest.json`、mtime 全 2026-08-20；聚合 `39698be45e69d7d0c8cb1632f58f39cdf8972f5b1085a0031b1a65f5244d9a7f`、`bytes_total` **939238** |
| 并集重算 | 两 hold 的 `shasum -a 256 *` 行合并排序再取 SHA = **`274e9804098c337d02245c64780c349c5c886c6633e4d8e7e1364d8da3e52d4c`** = 轮 13 亲测的移动前整目录聚合 |
| 五处平铺 hold | 行数/字节/SHA-256 与**轮 13 记录的原值**逐字相等，mtime 亦保持（`f79bc73d…`/`6f9358d2…`/`3c677ab6…` 仍 2026-08-17 00:05:11；`7c6eb5f7…`/`c3bb6f6d…` 仍 2026-08-20 14:30） |
| 现场 | 六个 shared 成员（含 `scenario_config.json`）全不存在；`runtime/frames/` `ls -1a` 只有 `.` 与 `..`；`test-results/` 下无 `residue`/`3of6`，仍恰七处 `*-post-run` |
| **纯移动的独立证明（续会话新增）** | `find runtime -type f -newermt "2026-08-20 15:00"` = **0**——轮 13 之后整个 `runtime/` **没有任何文件被写入**，只有 `frames/` 与两个新 hold 三个目录 inode 变化，正是纯 `mv` 的指纹 |
| 非回归 | focused `test_analyze_m3_body.py` **67/67 OK 零 skip**；**八条 `--verify`** 全退 0 且逐字复现；七处归档各 6 项 / `frames/` 各 257 项 / 七个聚合全中；四处旧 hold `257/93/109/257`、attempt-3 run hold 恰 2 文件、attempt-1 void hold 恰 10 份零隐藏；八个 run 目录各 11 份、B4 不存在；`runs/` 与 `test-results/` 下 08-18 之后**零文件被碰** |
| §4 CLI | `8820678`/`50e7d38`/`fcb22a7` 三态同一 SHA `154b06a6353249d5a192b5b8464aaaa8a0002b51cd7a948c69b89f3abf9dee2f`；对通过候选 `6e81bc2` 恰 1 行（`--run-id`） |
| 预检 | 退出 **0**、`status = PASS`、`side_effect_identity.unchanged = true`、四个 guarded 文件均 `present = false`、`run_directories` **35**（含 B3、不含 B4）。**复现方式登记**：副本内**必须 `cp` 实拷** `runtime/models`/`yoloe`——符号链接会被 `detector.path resolves outside the project` 守卫拒绝（续会话先踩后改，据实记下，供后轮省一次弯路） |
| 文档一致性 | 损失范围的第三次收窄已同步到四份转载文档；revision 24 抬头挂取代横幅、提案轮 68 §D.1 有失效标注；`3of6` 与「3/6」的残留全部落在历史节或 finding 描述内，活跃指令区零残留 |

**结论：续会话独立确认 Round 14 的 `PASS_WITH_NOTES` 成立，不改其 verdict，
也不另立轮次。** F12/F13 关闭、P10 已应用、P11 为唯一新增 CLASS_3，均照原文。

**2. 边界陈述更正（Round 14 落盘时尚未成真的一句）。** Round 14 的边界声明写
「副本收工 `git worktree remove --force` 删除」——该会话终止时**副本仍在**
（`.claude/worktrees/review-P1-M3-BODY-001-r14`，与主树同为 `fcb22a7`）。**副本由续会话
删除**，删除前核对其为 detached、无自有提交、`runtime/` 侧零写入。该句自本节起读作
「由续会话代为删除」。**其余边界事实经续会话复核属实**：`controller/`、`Assets/`、
`tools/`、`tests/`、`config/` 零触碰，操作单/提案/账本/Unity 日志/证据文件零触碰，
主树写入只有本文件与 `docs/current-status.md`。

**3. 措辞范围收窄（不推翻结论）。** Round 14 §1 把「没有一份文件丢失、改名或**被分错
组**」全部记在并集等式名下。**并集等式是分组无关的**——它只证明 (SHA, 文件名) 的多重集
不变，单独并不排除「两组之间互换文件」。**分组的正确性另有两条支撑，续会话已分别复算**：
(a) 两个**分组聚合**由接受轮 69 在**移动前**按预定划分实测、移动后逐项相等；
(b) id 段 / 逐文件 mtime / 包内 `capture_unix_s` 三重划分独立复现。三者合起来结论仍
完全成立，此处只把每条证据各自证明了什么分清楚。

**4. 本节不触碰 `passed_candidate`。** 上文 Round 14 verdict 块的机读行仍是文件中最近
一行（`grep '^passed_candidate:' … | tail -1` → `fcb22a7…`），续会话未新增、未修改该行。

## Round 15 — B4 全链条 + 接受轮 70/71 + revisions 26/27 + §2.23 + chore 压缩

Date: 2026-08-21

- 复核对象：`fcb22a7..HEAD` 全区间——接受轮 70（`62339fb`，revision 26）、§2.22 + §2.0
  (b) 批次（`667fbe2`）、B4 执行批次（`2fbdd00`）、接受轮 71（`45fe060`，revision 27）、
  chore 压缩（`6083ddf`）、§2.23 执行批次（`312b5cc`）、状态板交接（`1879db2`）与复核轮
  14 自身的落盘提交（`36b7e0d`）。交接声明的「三批 + §2.23」只是主张，本轮逐提交、
  逐文件核对了全部八个提交、九个路径。
- Candidate: **`1879db2a93047937220e946e0cb93a2dc5002c7c`**（HEAD）。上一通过候选由本文件
  最近一行 `passed_candidate` 派生 = `fcb22a7…`（轮 14）。
- **开轮资格（§4.4 R1）**：PLAY_GOVERNING 非空、**恰一条** = 操作单（revisions 26/27）。
  测量侧（`controller/ Assets/ config/ ProjectSettings/ Packages/packages-lock.json
  tools/ tests/`）对 `fcb22a7` **零路径**——B4 与全部前八次采集跑在同一份已复核测量字节
  上，本轮实测。区间实测 **8 提交 / 9 路径**；交接文字的「7 commits」是其自身提交入列前
  的测量（同 B3/B4 (b) 报告的一提交位移先例，文字本身声明运行时现取，登记不判缺陷）。
- 复核副本：`git worktree add --detach .claude/worktrees/review-P1-M3-BODY-001 1879db2`，
  收工已删除。副本无 `runtime/`（gitignored），以符号链接只读挂主树 `runtime/runs`
  （轮 14 同法；披露：挂载前 focused 套件 4 例因「archived A1 run 缺席」跳过，挂载后
  归零）。测试树哈希：`tests/test_analyze_m3_body.py` = `a3cf2681…f8f4f`、
  `tools/analyze_m3_body.py` = `e74350b9…2cb0d3`。**`runtime/` 零写入**：全部核对为
  `ls`/`stat`/只读 `open('rb')`/`shasum` 与 `--verify`（`analyze_m3_body.py:1494` 在
  `write_text` 之前返回，本轮先读码确认再运行）。

### 1. 承重复算（全部亲自重跑，不采信任何报告数字）

- **focused 套件 67/67 OK、零 skip**（钉住解释器 `.venv-yoloe/bin/python`，BC-BODY1-34）。
- **九条 `--verify` 全部退出 0 且逐字复现**（臂 A 五个 `WITHIN_RANGE` 冻结值、B1–B4 四个
  `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`）——含 B4 在其 shared 侧被 §2.23 归档之后。
- **§2.23 执行结果对钉住表逐项相符**：归档目录恰 6 项；`frames/` **257** 项、id 段恰
  `[724,851]` 全 128 个 ×2 + `latest.json`、聚合逐字 = `5ed64cf5…7ebf`；五个单文件行数/
  字节/SHA-256 逐项等于 revision 27 §2.23 表（truth 852/914667/`c6218bde…`、metrics
  61/2054/`43a5db7d…`、三发布件 328/342/459）。`runtime/frames/` 存在且恰 0 项；六个
  shared 槽位全空（含 `scenario_config.json`）；**未预建任何 run 目录**（B5 目录不存在）。
- **§2.21 两处保全 hold 未被触碰**：B hold 恰 256 项 / `bytes_total` 5513679 / 聚合逐字
  `568b6b98…a815`、id 段恰 `[907,1034]` 无 `latest.json`；A hold 恰 59 项 / 939238 /
  `39698be4…9a7f`、id 段恰 `[0,28]` 含 `latest.json`；五个平铺 hold 行数/字节相符；
  **并集等式亲自重算成立**（两目录 `shasum` 行合并排序取 SHA = `274e9804…2d4c`）。
- **归档 8 处 = 7 旧 + B4，逐处恰 6 项、`frames/` 各 257 项、八个聚合全部逐字命中**；
  有效 run 9 次，差额恒为 B3（附议：不是缺项）。四处旧 hold 257/93/109/257、attempt-3
  run hold 恰 2 文件、attempt-1 void hold 恰 10 份零隐藏项，抽样 SHA（attempt-1 truth/
  metrics hold）逐字相符。八个既有 run 目录各恰 11 份。
- **B4 run 目录 11 份**（含 `m3_body_analysis.json`/`summary.json`/`metrics.final.json`）；
  `summary.json` 的 `metrics_snapshot_present = true`、`actual_duration_s =
  130.0046690106392 >= 130.0`（握手 AND 门的可复核磁盘面）。receipt 臂身份三层逐项相符
  （`threshold` / `threshold-corridor-v1` / `follow` / `init_frame_id 0`），**receipt 键集
  中无任何 predecessor/attempt 键**；首末帧 0/851、`frame_record_count` 651、
  `truth_record_count` 852。
- **门 1 的值逐字复现**：`frames.jsonl` 中 frame 30 的 `simulation_time_s` =
  `6.184971809387207`，∈ `[2,10)`。**门 4 逐字节复现**：§4 bash 块在 `fcb22a7` /
  `667fbe2`（rev 26）/ HEAD（rev 27）三个状态提取件同为 19 行、同一 SHA-256
  `154b06a6…dee2f`（revision 26「一行不差」与 revision 27「§4 CLI 一行不动」双双字节级
  证实）；按 §C.4 规则重构命令（仅首行换绝对解释器路径）得 19 行、SHA-256 逐字 =
  `b764fc6c…2ded`；两条肯定项在、五条否定项全 False；42 个 token 中含 `hold` 子串者
  **仅 `threshold` 一个**，按 revision 27 规约判 **0 命中**——裸子串判法对臂 B 恒假阳性
  的披露属实，收编**只增停条件**（`fcb22a7` 时点门 4 原文实查只要求两条肯定项，轮 71
  裁定第 ① 层的前提成立）。
- **派生量全部重算**：B4 reason 直方图 **621 = 324/118/95/78/6**、无 planner 行 161、
  `frames.jsonl` 782 行；**同一段代码对 B1/B2/B3 复出 623 = 324/116/95/82/6、622 =
  339/109/93/75/6、626 = 319/121/95/85/6**，四轮圈数 `1.618675 / 1.509862 / 1.952997 /
  1.607742299284109` 逐项复现；五类失败 reason（`no_observation`/`no_platform_state`/
  `no_estimate`/`planner_exception`/`publish_failure_fallback`）**全 0 帧**；停留 =
  `170.38333129882812 − 130.185546875` = `40.197784423828125 s`；下界
  `342.4017822330673 >= 212.97056274847716` 成立；effort `88.72384065309268`、path
  `61.40687110469029`、`switch_count 11`、`nees_median 5.244988577303893`、
  `min_side_ge20_share 1.0` 及全部饱和/计数披露逐项等于 analysis（`--verify` 字节绑定）。
- **§2.0 (b) 两个时点均复现**：`fcb22a7..62339fb` = 5 路径 / 2 提交；`..667fbe2` = 6 路径
  / 3 提交；`2fbdd00` 的父提交恰为 `667fbe2`——「(c) 与发令之间零提交」属实。
- **revision 26 的四项逐项核实**：P11 时态与磁盘一致（§2.21 确已执行）；P7 的一手出处
  确在 trial-2 §D.1/§D.2（24/24 + 七条 `--verify`），trial-3 §A 为 §2.20 时点复验；
  N44 的两个「六」集合差异与 §2.16/§2.21/§2.23 实文一致；N45 出处注与本轮重算相符。
- **账本**：B4 放行条目在账本且读法未扩权（恰一次、void 中止条款不变、B5/重试/调参/
  `--compare` 明确未授权）。**角色写入边界逐提交核对全部合规**（实现角色两批未触碰
  unity-test-log/账本；(c) 条目随接受轮 71 批次入库，先例 B1/B2/B3）。chore 压缩只动
  `## Log` 旧条目，Gate board/交接/义务零改动，抽样删除值（`3.2432` 等）在证据/复核文件
  有落点；`python3 tools/check_docs.py` 在 HEAD 通过。

### 2. 本轮 finding

#### F14 —— CLASS_2（门 1 交叉验证叙述与磁盘不符；三处转载）

轮 71 §A 写「run 目录内 create-once 的 `frames.jsonl` 里 frame 30 的 `simulation_time_s`
与启动前落盘的 `6.184971809387207` 逐字相等，**frame 31 已无该字段**（暂停之后）」；
`docs/unity-test-log.md` B4 `VALID_TRIAL` 条目复算节写「且 **frame 31 已无
`simulation_time_s`**（暂停之后）」；`docs/current-status.md` 交接行 Scope 列英文写
「frame 31 **already has no sim-time**」。**磁盘实测：该说法为假。** B4 `frames.jsonl`
中 frame 31 的 update 行（文件第 35 行，`compute_stage = "update"`）**带有**
`simulation_time_s = 6.396984577178955`（frame 31 另有三条事件行该字段为 null）。

- **不受影响的部分（本轮明确不推翻）**：门 1 的判据与数值——frame 30 的值逐字复现、
  ∈ `[2,10)`，交叉验证的**承重半句成立**；B4 的有效性、轮 71 归因、四种 void 终态无一
  匹配、全部冻结值均不动。
- **为什么不是 CLASS_3**：该句是对具名证据文件中数值存在性的断言，不在 §4.4 CLASS_3
  闭集（拼写/格式/失效链接/时态）内；照字面复核会失败并诱导「现场被改」的误判——
  行为会因这段文字而不同。同型先例 F7（聚合缩写与磁盘不符）、F11（自证句失实而操作面
  全真）均为 CLASS_2。
- **磁盘上的真实边界标记（供返工措辞，本角色不代拟）**：暂停边界在 frame 30/31 之间
  体现于**墙钟**而非仿真时钟——`capture_unix_s` 间隙 `414.779 s`（仿真时间间隙仅
  `0.212 s`，暂停期间仿真时钟不走）；`frame_age_ms` 由 frame 30 的 `381239` 骤降至
  frame 31 的 `36`（前者为追平重放、后者为实时处理）。「启动前保留帧集为 0–30」本身
  已由门 2 的导出承载，无须借助 frames.jsonl 中不存在的缺字段现象。
- **闭合**：仓库内不存在可写断言的生产路径 fixture（对象是文档散文）→
  `NOT_MECHANIZABLE`，闭合为下一轮**定点复看**三处具名位置（提案轮 71 §A、
  `docs/unity-test-log.md` B4 `VALID_TRIAL` 条目、`docs/current-status.md` 交接行）。
  提案文件按 append-only 惯例由接受角色以追加更正处理；返工归**接受角色**
  （三处均为接受角色文字；先例：轮 8 的 F4/F5/F6 doc-text 返工径直交接受角色）。

### 3. 观察（登记，非 finding）

- **N46**：交接行与 Immediate next actions 的「7 commits」在本轮实测为 8（其自身提交
  入列）；路径集合仍恰 9、全文档。文字已声明 `<BASE>`/差异运行时现取，属已知的
  一提交位移现象，返工批次顺手更正即可，不单列 finding。
- **N47**：用户 2026-08-20「先复核再放行 B5」的指示**至本轮收工仍未转录进
  `docs/authorizations.md`**（账本最新条目仍为 B4 放行）。本轮的存在满足该指示的实质
  （B5 之前的独立复核轮已发生），但按 2026-07-30 规则，账本没有的授权视为未发生——
  转录义务仍在接受/辅助角色，B5 的放行条件引用该指示前必须先落账。

### 4. UNITY_NA 立场

本区间**未申领** `UNITY_NA`，本轮**附议不申领**：B4 是真实 Unity Play，其 Unity 证据由
用户反馈的代录条目承载；§2.23 归档与 chore 压缩是纯磁盘/文档动作，不构成需另判
`UNITY_NA` 的运行时功能面。

### 5. Verdict

**Round 15: REWORK_REQUIRED（candidate `1879db2`）。**

一条 **CLASS_2（F14）**：门 1 交叉验证的「frame 31 已无 `simulation_time_s`」与磁盘不符，
三处转载（提案轮 71 §A、Unity 日志 B4 条目、状态板交接行）。零 CLASS_1、零新 CLASS_3。

**本轮明确不推翻的事项**：B4 的有效性与轮 71 归因（四种 void 终态本轮逐条对照仍无一
匹配，门 1–4 的判据与数值全部亲自复现）；两条预登记限制的第四次确认与下界口径；
2026-08-14 批量 GO 不中止、B5 的一次 Play 仍在其覆盖内；§2.23 归档完整、§2.21 两处
hold 未触碰、归档 8 < 有效 run 9 恒为 B3；revisions 26/27 零门放宽（门 4 收编只增停
条件）；全部冻结值与 §4 CLI 块；chore 压缩无义务丢失。**F14 不触及任何 Play 治理门的
代码路径**，修复为纯文档更正，不触发 §4.4 R3 (3) 的闭环轮义务；B5 的槽位轮换与放行
决定归接受角色与用户（N47 的落账先行）。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现文件。**
`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零触碰；操作单、提案、账本、
Unity 日志、证据文件零触碰；**`runtime/` 零写入**（唯一写动作是复核副本内建
`runtime/runs` 符号链接，收工随副本整体删除，主树 `runtime/` 无任何变化）；主树写入
只有本文件与 `docs/current-status.md`。复核副本已 `git worktree remove --force` 删除。

## Round 16 — F14 定点闭合轮（轮 15 返工闭合：接受轮 72 批次）

Date: 2026-08-21

- 复核对象：接受轮 72 批次（`02c7c88`，`e8b8893..HEAD` 唯一提交）——F14 返工、N47 落账、
  N46 复查、Gate board 两处失效文字修正、B5 放行裁定。闭合方式按轮 15 verdict：F14
  `NOT_MECHANIZABLE` → **定点复看具名位置**（§4.4 R3 (4)，不重跑全套）。
- Candidate: **`02c7c888b5c217127a61590524c09966ae0c26c3`**（HEAD）。上一通过候选由本文件
  最近一行 `passed_candidate` 派生 = `fcb22a7…`（轮 14；轮 15 `REWORK_REQUIRED` 未写
  该行）。**开轮资格**：`fcb22a7..HEAD` 在 PLAY_GOVERNING 上仍恰一条（操作单
  revisions 26/27，轮 15 已覆盖）；轮 72 批次自身**零操作单、零代码、零 `runtime/` 改动**
  （四个路径全为 Acceptance 白名单文档；提案 diff 零删除行、纯追加一个 hunk；Unity 日志
  恰一行替换为加注更正；账本恰一个插入 hunk）。本轮为纯文档定点复看，未建复核副本，
  全部核对为主树只读读取与 `runtime/` 只读复算。

### 1. F14 四处转载的定点复看（全部落实）

| 位置 | 处置方式 | 本轮实测 |
|---|---|---|
| 提案接受轮 72 §A | append-only 追加更正；轮 71 §A 原文保留但明文作废（「以本节为准」） | 追加节存在且枚举准确；**轮 71 §A（L6455）原文未被回改**——与 F12 闭合同一标准：历史节残留可接受，作废声明由紧随其后的轮 72 §A 承担 |
| `docs/unity-test-log.md` B4 `VALID_TRIAL` 条目 | 就地加注更正（代录记录非 append-only） | 恰一行被替换；更正括注内**引用原句**留痕、指明根因（末条覆盖式聚合）、保留承重前半句；用户逐字反馈引文未被触碰 |
| 状态板交接行 | 轮 15 自身行重写时已取代 | 本轮 sweep 确认无残留 |
| 状态板接受轮 71 Log 条目（**轮 72 自查新发现的第四处**，轮 15 未列） | 就地加注作废 | 加注在位（〔本条原还写…已由接受轮 72 作废〕），保留原文引用与承重半句声明 |

**全仓独立 sweep**（`frame 31 已无` / `has no sim-time`）：除上述四处的更正/引用与轮 15/
本文件的 finding 描述外，唯一逐字原文即提案轮 71 §A 的 append-only 历史原文，活跃指令区
**零残留**。**F14 关闭。**

### 2. 轮 72 新主张的独立复算（全部逐字复现）

- **行号枚举**（1-indexed，对 `frames.jsonl` 逐行复算）：line **31** = frame 30 / update /
  `6.184971809387207`；line **35** = frame 31 / update / `6.396984577178955`；
  line **36/37/39** = frame 31 / stage None / sim None——与轮 72 §A 的枚举**逐项相等**
  （轮 15 用 0-indexed 测得同一组行，两套编号一致）。
- **四个数值**：墙钟间隙 `414.779000043869 s`（轮 72 记 `414.779` ✓）、仿真间隙
  `0.21201276779174805 s`（记 `0.212013` ✓）、`frame_age_ms` `381238.84296417236`
  （记 `381238.8` ✓）→ `36.353111267089844`（记 `36.4` ✓，就近取整）。
- **根因陈述与磁盘一致**：三条 null 事件行确在 update 行**之后**，末条覆盖式聚合
  （`found[fid]=st`）确会把 update 行盖掉——机制与轮 15 复核时的推测相同，轮 72 据实
  自认并收窄为「断言字段不存在必须按行枚举」的自律。**与 F12 同族**的归类恰当。
- **N47 账本条目**：在位；**明文标注为转述**（来源 = 实现角色 `1879db2` 提交信息，逐字
  引用）；用户本会话确认 **"就按这个意思做"** 逐字入账；落账时效句诚实（落盘后方可
  引用）。读法六点未扩权（B5 仍批量 GO 覆盖、`--compare`/调参仍无 GO、void 中止条款
  不变）。
- **N46**：交接行与 Immediate next actions 两处均已写 8 提交 / 9 路径（轮 15 所改，
  轮 72 复查属实）。
- **Gate board 两处失效文字修正核对**：Unity 列补记的 B4 行与轮 15 已核实的四门/握手/
  代录事实逐项相符；Overall 列叙述更新至轮 72 时点，无数值/verdict 改动。Overall token
  轮换为 `…F14_REWORK_APPLIED_AWAITING_CLOSURE`，三处行内 echo 同步（`check_docs`
  在其提交与本轮均通过）。
- **现场非回归抽查**：`runtime/frames/` 仍恰 0 项、B4 run 目录仍 11 份、B5 run 目录仍
  不存在（未预建）；轮 72 批次对 `runtime/` 零写入与声明相符。

### 3. 观察（登记，非 finding）

- **N48**：轮 72 的「B5 在 F14 闭合之后才放行」是接受角色在用户条件之上的自设裁定，
  其自身已声明用户可推翻。本轮闭合 F14 后该裁定的条件即满足；放行与槽位轮换归接受
  角色按用户决定执行，本角色不代为放行。

### 4. UNITY_NA 立场

轮 72 批次未申领 `UNITY_NA`，本轮**附议不申领**：纯文档更正与落账，无运行时功能面。

### 5. Verdict

**Round 16: PASS_WITH_NOTES（candidate `02c7c88`）。**

**零 CLASS_1、零 CLASS_2、零新 CLASS_3。** 轮 15 的唯一阻断 finding **F14 关闭**（四处
转载全部更正或按 append-only 惯例作废，活跃区零残留，根因据实入档）；**N47 落账核实**、
**N46 复查核实**。**本轮明确不推翻的事项**：B4 的有效性与轮 71 归因、两条预登记限制的
第四次确认、批量 GO 与 B5 的一次 Play 覆盖、全部冻结值、轮 15 的全部复现结论。
**B5 仍无轮换槽位与 Play 前核对，任何 Play 仍不得进入**；释放决定归接受角色与用户
（N48）。

按 R7，本通过轮写机读指针：

passed_candidate: 02c7c888b5c217127a61590524c09966ae0c26c3

此后「上一通过候选」由本行派生（`grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md
| tail -1`），无需任何手写更新。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现文件。**
`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零触碰；操作单、提案、账本、
Unity 日志、证据文件零触碰；**`runtime/` 零写入**（本轮全部为只读读取，未建复核副本、
未建任何符号链接）；主树写入只有本文件与 `docs/current-status.md`。

## Round 17 — B5 全链条 + 接受轮 73/74/75 + revisions 28/29 + §2.24/§2.25（用户裁定的 `--compare` 前置复核轮）

Date: 2026-08-21

- 复核对象：`02c7c88..HEAD` 全区间 **7 提交 / 8 路径**——接受轮 73（`c1c53d3`，revision
  28 + 轮换 B5）、§2.24 + §2.0 (b) 批次（`993520a`）、B5 执行批次（`99692f8`）、接受轮 74
  （`25a6c01`，`B5_VALID_TRIAL` + revision 29）、接受轮 75（`a7f9dd0`，`--compare` 次序
  入账）、§2.25 执行批次（`2916bc2`）与复核轮 16 自身的落盘提交（`dce7970`）。交接声明的
  「B5 执行 + 轮 74 + revision 29 + §2.25」只是主张，本轮逐提交、逐文件核对了全部七个提交。
  **本轮是用户 2026-08-21 裁定（账本逐字「归档 + 复核后再授权（推荐）」）的 `--compare`
  授权前置第二步。**
- Candidate: **`2916bc25180b72dec15ab50bc5b540d69c3ac0a8`**（HEAD）。上一通过候选由本文件
  最近一行 `passed_candidate` 派生 = `02c7c88…`（轮 16）。
- **开轮资格（§4.4 R1）**：PLAY_GOVERNING 非空、**恰一条** = 操作单（revisions 28/29）。
  测量侧（`controller/ Assets/ config/ ProjectSettings/ Packages/packages-lock.json tools/
  tests/`）对 `02c7c88` **零路径**——B5 与全部前九次采集跑在同一份已复核测量字节上，
  本轮实测；测试树哈希与轮 15 逐字相同（`a3cf2681…f8f4f` / `e74350b9…2cb0d3`）。
- 复核副本：`git worktree add --detach .claude/worktrees/review-P1-M3-BODY-001 2916bc2`，
  收工已删除；副本内以符号链接只读挂主树 `runtime/runs`（轮 14/15 同法）。**`runtime/`
  零写入**：全部核对为只读读取、`--verify`（`analyze_m3_body.py:1494` 在 `write_text`
  之前返回）与聚合/行级复算。

### 1. 承重复算（全部亲自重跑，不采信任何报告数字）

- **focused 套件 67/67 OK、零 skip**（钉住解释器，BC-BODY1-34）。
- **十条 `--verify` 全部退出 0 且逐字复现**（臂 A 五个 `WITHIN_RANGE` 冻结值、B1…B5 五个
  `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`）——含 B5 在其 shared 侧被 §2.25 归档之后。
- **§2.25 执行结果对钉住表逐项相符**（现场 53 项机检全过）：归档目录恰 6 项；`frames/`
  **257** 项、id 段恰 `[614,741]` 全 128 个 ×2 + `latest.json`、聚合逐字 =
  `dcabe43b…b814`；五个单文件行数/字节/SHA-256 逐项等于 revision 29 §2.25 表（truth
  742/806547/`6ea05d88…`、metrics 61/2057/`024acc13…`、三发布件 329/342/458）。
  `runtime/frames/` 存在且恰 0 项；六个 shared 槽位全空；**未预建任何 run 目录**
  （`…-trial-6` 不存在）。**九处 post-run 归档**各恰 6 项 / `frames/` 各 257 项、九个聚合
  全部逐字命中（七旧 + B4 `5ed64cf5…7ebf` + B5 `dcabe43b…b814`）；**归档 9 < 有效 run
  10，差额恒为 B3**（附议：不是缺项）。§2.21 两处 hold 未被触碰（256 / 5513679 /
  `568b6b98…a815`；59 / 939238 / `39698be4…9a7f`），**并集等式亲自重算成立**
  （`274e9804…2d4c`）；五个平铺 hold、四处旧 hold（257/93/109/257）、attempt-3 run hold
  恰 2 文件、attempt-1 void hold 恰 10 份零隐藏项全部相符。十个 run 目录各恰 11 份。
- **B5 执行链逐项复现**：门 1 的值**按行枚举**复现——`frames.jsonl` 第 **29** 行（1-indexed）
  = frame 28 update / `5.7835187911987305` ∈ `[2,10)`，相邻 frame 29/30/31/32 的 update 行
  依次 `5.9804863929748535` / `6.184908866882324` / `6.385033130645752` /
  `6.580019950866699`，**与轮 74 的枚举逐项相等**；两侧余量 `3.783519` / `4.216481` 复算
  相符。**双方均遵守 F14 后的自律**（证据 §C.1 明写「不重复 B4 的 F14 错误」，轮 74 亦
  不主张任何「某编号后已无该字段」）——轮 72 的收窄确实传导到位。**门 4 逐字节复现**：
  §4 bash 块在 `02c7c88` 为 19 行 SHA `154b06a6…dee2f`、在 HEAD 为 19 行 SHA
  `cfab3494…d149`，**恰 1 行不同且即 `--run-id`**（trial-4 → trial-5；`--body-policy
  threshold` 未动，同臂轮换与 revision 28 声明相符）；按 §C.4 规则重构命令得 19 行、
  SHA-256 逐字 = `df9a4aa0…4608`；42 个 token 中含 `hold` 子串者仅 `threshold`、规约判
  0 命中，五条否定项（含 `arm-b-trial-4`）全 False、两条肯定项在。
- **派生量全部重算**：B5 reason 直方图 **623 = 322/121/95/79/6**、无 planner 行 159、
  `frames.jsonl` 782 行；**同一段代码对 B1/B2/B3/B4 复出 623/622/626/621 的全部已发布
  分量**；五类失败 reason 全 0 帧（`publish_failure` 全文 0 次，字节级）；
  `published_observation:false` 计 27，落在五轮正常带 24–29 内（事件/追平行机制）。
  truth **742** 行、首末帧 0/741；停留 = `148.38572692871094 − 130.18399047851562` =
  `18.201736450195312 s`（五轮最短）；圈数 `298.19364929741283 / 212.97056274847716` =
  `1.4001636913998579`，下界成立。analysis 字段逐项相符：effort `90.18617697302953`、
  path `62.887483690312656`、`switch_count 11`（第五次）、`nees_median 4.762136507763351`
  （首次 <5，仍属注册发现 (a) 数据点）、`min_side_ge20_share 1.0`（第五次 125/125）、
  四项饱和、530/155；receipt 臂身份三层 + **无 predecessor/attempt 键**、
  `frame_record_count` 651；`summary.json` 的 `metrics_snapshot_present = true`、
  `actual_duration_s = 130.00008594989777 >= 130.0`（握手磁盘面）。
- **§2.0 (b) 两个时点均复现**：`02c7c88..c1c53d3` = 4 路径 / 2 提交；`..993520a` =
  5 路径 / 3 提交；`99692f8` 的父提交恰为 `993520a`——「(c) 与发令之间零提交」属实，
  Play 跑在 (c) 点名的 HEAD `993520a` 上。
- **revisions 28/29 与轮 73/74/75 逐项核实**：revision 28 的五处轮换 + §2.24 十一项结构
  （155 = 6+2+24+54+25+14+7+8+1+1+13，算术成立）+ §2.22 漏标自查补标（F8/F9/F10 同族，
  接受角色自查发现并修复，已登记轮换完整性教训）；revision 29 的 §2.25 合同 + §2.19
  落盘地先例终止句 + `--compare` C 条；轮 73 对 §2.24 的独立复算、轮 74 的四种 void 终态
  逐条对照（本轮亲自比对，无一匹配）、轮 75 的次序入账（**不是授权**，措辞与账本一致，
  三选项语境完整、约束先于提问披露）。**臂身份函数亲自复跑**：
  `expected_acquisition_ids('b')[4]` = trial-5、`canonical_trial_id` 返回自身、
  `_expected_policy` = `threshold`、`…-trial-5-attempt-1` 与 `…-trial-6` 在两个函数上均抛
  `run_id_not_frozen_trial`。**逐提交角色写入边界全部合规**（实现角色四批未触碰
  unity-log/账本；(c) + `VALID_TRIAL` 代录随轮 74 批次入库，先例 B1–B4）；
  `python3 tools/check_docs.py` 在 HEAD 通过。

### 2. 本轮 finding

**无。** 零 CLASS_1、零 CLASS_2、零 CLASS_3。

### 3. 观察（登记，非 finding）

- **N49**：状态板 Current state 的三处 B5 之前旧句（「B5 stays authorized / eight
  archives / nine `--verify`」「eight against nine」、Track discipline 的「B5 stays
  released but unrun / four unreviewed batches」）滞后于轮 74/§2.25，按 AGENTS.md 失效
  文字规则与轮 10/15 先例由本轮就地修正并记入 Log；不改任何门/verdict/数值。
- **N50**：`planner_switch_count` 五次恰 `11` 与 `nees_median` 首次 <5 均已按「只登记、
  不作机制主张」的口径处理（轮 74 §B、`implementation-status.md` 第五次确认段），
  与 BC-BODY1-15 (d) 一致；本轮附议该口径。

### 4. UNITY_NA 立场

本区间**未申领** `UNITY_NA`，本轮**附议不申领**：B5 是真实 Unity Play，其 Unity 证据由
用户反馈的代录条目（门 3「匹配」、Console「已退出，没有报错」）承载；§2.25 归档与
次序入账是纯磁盘/文档动作。

### 5. Verdict

**Round 17: PASS_WITH_NOTES（candidate `2916bc2`）。**

**零 finding。** B5 的执行链（四门 + 握手 + 绑定分析）、轮 74 的 `B5_VALID_TRIAL` 归因、
revisions 28/29 的零门放宽、§2.25 归档的零丢失与十条 `--verify` 逐字复现全部独立核实；
**臂 B 收于 5/5，十次采集全部有效，2026-08-14 批量授权完整履行完毕且中止条款从未触发**；
两条预登记限制第五次确认，效应量口径（**只报下界**、H2 上限
`THRESHOLD_ALLOCATION_PARTIAL`）不变。**用户裁定的 `--compare` 前置次序中，「独立复核」
一步随本轮完成**；下一步是**用户的另行逐字授权**（十次齐备与本轮通过都不构成授权——
批量 GO 原文排除 `--compare`，轮 75 的入账只是次序），授权后由接受角色落账并起草比较
合同。**M3′ batch 1 的关闭未被任何角色主张**，需另行判断加用户授权。本轮附议：
`--compare` 执行前的合同不得引入新指标/新阈值/新样本域（轮 75 §C 已写死）。

按 R7，本通过轮写机读指针：

passed_candidate: 2916bc25180b72dec15ab50bc5b540d69c3ac0a8

此后「上一通过候选」由本行派生（`grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md
| tail -1`），无需任何手写更新。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现文件。**
`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零触碰；操作单、提案、账本、
Unity 日志、证据文件零触碰；**`runtime/` 零写入**（唯一写动作是复核副本内建
`runtime/runs` 符号链接，收工随副本整体删除，主树 `runtime/` 无任何变化）；主树写入
只有本文件与 `docs/current-status.md`。复核副本已 `git worktree remove --force` 删除。

## Round 18 — `--compare` 全链条（合同 → 授权 → 执行 → 轮 78 归因）

Date: 2026-08-21

- 复核对象：`2916bc2..HEAD` 全区间 **5 提交 / 6 路径**——接受轮 76（`c62b2b1`，合同草案）、
  接受轮 77（`af7ba52`，用户授权入账）、`--compare` 执行批次（`7d08307`）、接受轮 78
  （`6bb2b3e`，归因 + 钉住 + 追认落盘地）与复核轮 17 自身的落盘提交（`7a5e8db`）。
  交接声明的范围只是主张，本轮逐提交、逐文件核对了全部五个提交。
- Candidate: **`6bb2b3e1e108609f289b2dea0af5c35fd18faa90`**（HEAD）。上一通过候选由本文件
  最近一行 `passed_candidate` 派生 = `2916bc2…`（轮 17）。
- **开轮依据（据实披露）**：本区间测量侧 **0 路径**、操作单**零改动**，故 §4.4 R1 的
  PLAY_GOVERNING diff **为空**——按其字面本轮不构成代码候选开轮条件。本轮开启的依据是：
  ① 用户在本会话的直接指示（「完成独立复核任务」，2026-08-21）；② 轮 78 交接行
  `AWAITING_REVIEW`；③ 本批含**一次消耗性、不可逆的执行**（`--compare` 恰一次授权已花掉）
  与承载研究主张措辞的归因——正是独立复核存在的对象。R1 的措辞未涵盖「零代码改动的
  消耗性执行批次」（runtime 不在 git diff 可见范围内），登记为 N51 交用户/协调批次酌定，
  本轮不自行修改任何工作流条文。
- 复核副本：`git worktree add --detach … 6bb2b3e`，收工已删除；副本内符号链接只读挂主树
  `runtime/runs`（轮 14/15/17 同法）。**`runtime/` 零写入**；**未运行 `--compare`**
  （授权恰一次已用尽；复算全部用本角色自写代码从十份 analysis 读出，工具的
  `compare_arms` 仅读码核实语义、未调用执行）。

### 1. 承重复算（全部亲自重跑/重算，不采信任何报告数字）

- **读码核实合同的四条语义主张**（`tools/analyze_m3_body.py`，测量侧字节与轮 15/17 逐字
  相同）：① `h1_arm_a_trials` 由 `arm_a` 构造——**H1 段只含臂 A** 属代码事实；② 分量
  `pass = summary > 0.0 AND 五个配对中位数全部 > 0.0`，verdict 映射全过 →
  `H2_SUPPORTED`、部分 → `THRESHOLD_ALLOCATION_PARTIAL`、全不过 → `…_INEFFECTIVE`；
  ③ 输出 create-once（`--output` 必填 + `compare_output_create_once`），**写盘在
  `compare_arms` 返回之后**——任何 `AnalysisError` 都不写输出（合同第 8 条属实）；
  ④ ID 序列/canonical 槽位/analysis 哈希去重/16 键跨 run 身份/A1、A2 绑定/两臂
  policy-planner 全部机械 `raise`。
- **钉住输出逐项核对**：`runtime/test-results/p1-m3-body-001-compare.json` 恰一个，
  **3413 字节 / 101 行**，SHA-256 逐字 =
  `4bd4a14f2176af3ad51ddecc49922e3dabacd9b467267111c1a6303c6c2a0607`，schema
  `p1-m3-body-compare/v3`，verdict `THRESHOLD_ALLOCATION_PARTIAL`，`passed_components` =
  `[area_median_px, center_error_px]`；`arm_a`/`arm_b` 序列 = 冻结顺序（A1 attempt-4、
  A2 attempt-2）；**十份 `analysis_sha256` 对各 run 目录内实测 SHA 逐一相符**；
  `h1_arm_a_trials` 恰五条、全为臂 A 冻结值（`0.578…` 系列 / `WITHIN_RANGE`）——
  **臂 B 的五次 `SCENE_DEGENERATE` 确不在该 JSON 内**，轮 76 §C.6 / 轮 78 §D.3 的
  披露义务有事实根据。
- **三分量十五个配对中位数 + 三个 summary 全部用自写代码逐位复现**（配对、共同里程
  格点交集、改善正向符号 B−A / A−B、格点中位数、五配对中位数的中位数）：
  `area_median_px` `632.4378616307513 / 513.9202581212885 / 663.310713669307 /
  558.6660874410882 / 585.4605541298952`，summary `585.4605541298952`，pass True；
  `center_error_px` `0.5305252075195312 / 0.7804527282714844 / 1.1124763488769531 /
  1.5641822814941406 / 1.1714401245117188`，summary `1.1124763488769531`，pass True；
  `min_side_ge20_share` **五个恰 `0.0`**，summary `0.0`，pass False。**与输出 JSON、
  证据 §C、轮 78 §B 三方逐位一致。**
- **天花板算术亲测坐实**：每对共同格点恰 **125** 个；配对 1 臂 A 的 min_side 指示为
  **116 个 `1.0` + 9 个 `0.0`**、臂 B **125 个 `1.0`**——B−A 差值 116 个 0 + 9 个 1，
  中位数恰 `0.0`，对严格 `> 0` 判据**永不通过** → `H2_SUPPORTED` 不可达、`PARTIAL`
  即天花板。**轮 78「达预登记天花板、非部分失败」的归因算术成立**；H2-CEILING 的
  预登记时序（2026-08-14，任何臂 B 数据之前）为既有已复核事实。
- **现场非回归**（执行后实测）：**十条 `--verify` 全部退出 0 且逐字复现**（`--compare`
  只读十份 analysis 的声明与实测一致）；十个 run 目录仍各 11 份；`runtime/frames/` 恰
  0 项；九处 post-run 归档；§2.21 两 hold 仍 256 / 59；`test-results/` 下 compare 相关
  文件**恰一个**；六个 shared 槽位仍空。focused 套件 **67/67 OK 零 skip**。
- **账本与角色边界**：轮 77 条目逐字（「认可，继续」）、读法未扩权（合同即授权范围、
  恰一次、重跑/变体/调参/关闭均明确不覆盖）、两条解读注意事项在授权前披露；四个提交
  的写入路径逐一在各角色白名单内（实现角色未触碰账本/Unity 日志）；
  `python3 tools/check_docs.py` 在 HEAD 通过。
- **两处披露复看**：① 实现角色 §A 的 zsh 分词误报（前置第 2 项误报 0/10）——当场识破、
  改用 Python 重做为 10/10，**未据误报停止也未据以放行**，错在核对脚本而非现场；处理
  与登记得当。② 轮 76 合同未具名落盘文件（F13 同族，F13 闭合后再犯）——实现角色把落盘
  地选择与理由摆上明面交追认，轮 78 照单追认并把「合同必须具名落盘文件」收窄为自律；
  **本轮附议该处理**：缺口已由责任角色自行登记并闭合，落盘地
  `docs/evidence/P1-M3-BODY-001-compare.md` 的批次级归档理由成立，不另立 finding。

### 2. 本轮 finding

**无。** 零 CLASS_1、零 CLASS_2、零 CLASS_3。

### 3. 观察（登记，非 finding）

- **N51**：§4.4 R1 的开轮资格以 git diff 为判据，未涵盖「零代码改动的消耗性执行批次」
  （`runtime/` 工件不在 diff 可见范围）。本轮以用户直接指示开启并如实记录；是否为此类
  批次增补开轮条款，属工作流基础设施，交用户决定（若修，须 COORD 协调批次）。
- **N52**：状态板 Current state 的「**`--compare` has never run**」句滞后于本批（已执行
  恰一次并归因），按失效文字规则由本轮就地修正；其后半句「no claim may rest on arm A
  alone」仍为有效常驻约束，保留。

### 4. UNITY_NA 立场

本区间**未申领** `UNITY_NA`，本轮**附议不申领**：`--compare` 是对十份已归档 analysis 的
离线只读比较，其 Unity 面由十次已代录的 Play 承载；本批不新增运行时功能。

### 5. Verdict

**Round 18: PASS_WITH_NOTES（candidate `6bb2b3e`）。**

**零 finding。** 合同 → 授权 → 执行 → 归因四环节逐项独立核实：十五个配对中位数与三个
summary 逐位复现，`THRESHOLD_ALLOCATION_PARTIAL` = **预登记天花板下的最高可达判定**这一
归因算术成立，H1 段只含臂 A 的披露义务有代码与字节双重根据，强制措辞五条（不可达性、
臂 B 饱和另行陈述、效应量只报下界、质量序列非主指标、零量级主张）与预登记限制一致。
**`--compare` 的恰一次授权已用尽**；任何重跑须用户另行逐字授权。**M3′ batch 1 的关闭仍
未被任何角色主张**——下一步是接受角色的关闭判断草案加用户授权，本角色不代为主张。

按 R7，本通过轮写机读指针：

passed_candidate: 6bb2b3e1e108609f289b2dea0af5c35fd18faa90

此后「上一通过候选」由本行派生（`grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md
| tail -1`），无需任何手写更新。

边界声明（对抗长上下文遗忘，逐字重申）：**本复核会话未修改任何实现文件。**
`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零触碰；操作单、提案、账本、
Unity 日志、证据文件零触碰；**`runtime/` 零写入、`--compare` 未运行**（唯一写动作是
复核副本内建 `runtime/runs` 符号链接，收工随副本整体删除）；主树写入只有本文件与
`docs/current-status.md`。复核副本已 `git worktree remove --force` 删除。
