# P1-VLM-DATA-002 — 面向 grounding 的场景内巡览采集批（多锚点、目标停放、S0 supersession）

Status: ACCEPTED_WITH_BINDING_CLARIFICATIONS（Acceptance round 3，2026-09-03；revision 2
回应 round 2 AR2-1…6；BC-SURVEY-1…16 及解释它们的 BC-SURVEY-17/18 按字面优先于正文
冲突处；2026-09-05 终局 `R3@stageA` 已通过并消费，授权 #2 已执行 B–D；2026-09-07 接受侧确认批次产出不足，待用户 §2.4 选择）
Author/role: 构思角色（ideation，Fable 池）
Created: 2026-09-03
Last updated: 2026-09-07
上位章程：`P1-VLM-DIST-001`（`ACCEPTED_WITH_BINDING_CLARIFICATIONS` round 3，设计 v0.3.18）
上位批次：`P1-VLM-DATA-001`（`ACCEPTED_WITH_BINDING_CLARIFICATIONS`；正式 S0–S5 attempt-1
create-once 不可变；supersession 已由本批授权 #2 信封吸收）
起草依据：`docs/authorizations.md` 2026-09-03 条目（用户逐字选择「A 场景内补采集」与
「6–10 次 (Recommended)」；**仅授权起草，不授权任何执行**）；用户同日确认训练目标沿
`P1-VLM-DIST-001` 不动，并逐字选「按此写」批准 revision 2 的闭合方案。
硬预算：本文 ≤ 600 行（COORD-008 S3）；后续只追加 BC 表行与「待裁定」问答
执行授权：§6 #1 阶段 A 于 2026-09-03 签发；§6 #2 阶段 B–D 于 2026-09-05 以「授权继续」签发入账

> 本文已由 Acceptance round 3 接受为带 BC 的设计，但**接受不等于执行授权**。阶段 A 已过
> COORD-005 保真并生成七对正式 plan/config；终局 `R3@stageA` 通过已消费，授权 #2 已交实现角色。
> B–D 已执行，阶段 D 工件核验见 `docs/implementation-status.md`；批次为 `SURVEY_FLOORS_UNREACHABLE`，
> 等待用户 §2.4 选择；Unity 逐会话机器结果已代录，事前工作树/Console 证据待补；§8 仍只作规划。

## 0. 修订索引

**revision 2 ↔ AR2-1…6**

| AR 项 | 落点 | 实质变化 |
|---|---|---|
| AR2-1 逐帧有效性 / 证人顺序 | §2.1(c)(e) | `VALID_SURVEY` 逐帧判定（驻留窗 ∧ 位置 ≤ 1 m ∧ 朝向 ≤ 3°）；视角达成 = 窗内有效帧 ≥ 3（证人 ≥ 10）；15 个位置 / 227 个视角计数改准；位置内视角顺序、C14/C26 追加证人视角、W26 的离散 θ 与 tie-break 写死 |
| AR2-2 停放目标朝向 / y | §2.1(f) | 停放段冻结为世界 +z 方向 1.0 m（出生旋转 = 单位四元数，`LookRotation(+z)` 零转动，代码核实）；`P_k.y` = 所在 patch `surface_y_m`；`drive` 前置零违规 `road_scene_audit.json`，报告随会话归档，S2 缺失/非零即整族 `INVALID` |
| AR2-3 候选身份 / 零帧 / 恢复 | §2.1(a)(h) | 每个停放候选独立 scenario/plan/config/session 身份；零帧会话专用 `close` 路径与终态；`tree.json` 成员域写死；completion 后重入只删逐字核验的残留、其余移入 create-once hold 后解锁 |
| AR2-4 swept-path 边界 | §2.1(d) | 扩展框闭集、线段/AABB 精确相交（不采样）；绕行高度 `max_y + 4`（正余量 1 m），> 30 m 即具名不可达；系留/高度极值在端点的机械断言 |
| AR2-5 COORD-005 顺序 / attempt 语义 | §2.3、§2.2 第 5 条 | 顺序改为授权 #1 → 候选 → 诊断 Play 保真 → 停点自证 → 复核 → 授权 #2 → pilot → 采集 → attempt-2；诊断前置条件与现场恢复；attempt-3 = 从首个未发布阶段起重跑、逐件 supersede 最新已发布前身；BC-SURVEY-3/4 再冻结零-ID 诊断与混合 attempt 的实际输入 refs |
| AR2-6 授权措辞 | §6、§Compatibility | 区分「新增专用 config」「不改 Unity scene asset」「不改 default config」；如实承认继承 default 已冻结 6 条 relocation/removal；attempt 身份与诊断 Play 次数入原话 |

**revision 1 ↔ AR1-1…6（保留索引）**：AR1-1 不可变 session id + 两阶段 `close`；AR1-2
逐帧 selection + 本地停放证人；AR1-3 H 相对锚点 y、33 m 余量、冻结顺序与转场检查；
AR1-4 逐工件 supersession + S0 会话表/allowlist + S5 精确 refs；AR1-5 阶段门与信封；
AR1-6 pilot 闭集状态机。round 2 认可其中 AR1-4/AR1-6 主干与 AR1-1/2/3 方向。

## Problem and research value

**事实**：`P1-VLM-DATA-001` 正式 S0–S5 的审计前上界报告
（`docs/evidence/P1-VLM-DATA-001-S0-S5-pre-audit-upper-bound.md`，非门 verdict）
显示现有归档在**结构上**达不到 BC-DATA-1 冻结的下限，人工审计与 supersession
都不能改变它：

| 下限 | 冻结值 | 乐观上界 | 结构原因 |
|---|---|---|---|
| F1 双验证对象 | ≥ 60 / 101，≥ 6 类 | 9（结构上限 16） | 85 辆目录车从未以 `OK` 状态出现在任何 BOUND 帧 |
| F3 属性唯一单元 train∪dev / test | ≥ 60 / ≥ 25 | 25 / 20 | 候选外延只含 7 个对象 |
| F4 统计簇 train∪dev / test | ≥ 25 / ≥ 10 | 4 / 7 | 全库只有 3 个原子 |
| train split | 非空 | **空** | 3 原子经冻结规则全部落入 dev/test |
| `TARGET_UNBOUNDED` 帧 | — | 16,472 / 23,549（70.0%） | 动态目标在画面内却无逐帧真值的族整帧出局 |

现有全部归档都是沿默认路线附近采集的追踪实验副产物：相机只看过城区一角，且动态
目标几乎总在画面里。按 `P1-VLM-DIST-001` §3.1 与 `P1-VLM-DATA-001` §1/§7，章程内
只有两条路：以 `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA` 收束，或**另立用户授权的
消耗性采集批**。用户 2026-09-03 选择后者，并把 Play 预算定为 6–10 次、系留 35 m
不动（账本当日条目）。

**研究价值**：本仿真的独特资产是**完备且机械可验证的符号真值**（章程 §0.3 的
LLaVA 同构前提：教师读符号不读像素）。补采集保住这一前提，不改研究问题、T-G1、
BC-DIST-1…4、F1–F4 定义与下限、切分与审计协议；它只补「相机看过哪些车、从哪些
站位看」这一块。**本批不产生任何研究主张**。

## Proposed behavior

### 2.1 巡览采集协议（纯 Python 驱动，零 C# 改动）

**(a) 身份（AR1-1 / AR2-3）**。三级身份，全部不可变、只增不改：

- **计划身份** `p1-vlm-survey-a<k>-p<v>-c<j>`：k = 锚点序号 1–10，v = 计划版本 1 或 2
  （§2.4），j = 该锚点该版本下的停放候选序号（从 1 起，按 (f) 的冻结排序）。每个计划
  身份对应**恰一份** `config/scenario.p1-vlm-survey-a<k>-p<v>-c<j>.json`（`scenario_id`
  同名）与恰一份 `plan.json`，均 create-once；换候选 = 新身份，永不改写旧文件。
- **会话身份** `<计划身份>-s<n>`：同一计划身份下第 n 次 Play。逐字用于
  `runtime/p1-vlm-survey/<session>/`（manifest、drive log、completion）、归档根
  `runtime/test-results/p1-vlm-survey/<session>/`、manifest `session_id`、S1 的 family
  与 source unit、Unity 日志条目 `UT-P1-VLM-DATA-002-<session>`。
- **每个会话恰一次 Play**（含零帧会话）；每次 Play 计入信封；任何会话的归档永不删除。

**(b) 巡览专用场景配置**。从 `config/scenario.default.json` 派生，**只允许改动**下表
五个字段，其余字节逐字相同（`scene_adjustments` 含 default 已冻结的 6 条
relocation/removal 原样继承，bootstrap 照常搬移 3 辆、移除 3 辆；`road_data_sha256`、
`sensor` 的分辨率/视场/帧率、`drone`、`gimbal`、`evaluation` 全部不变；布局类仍为
`default`）：

| 字段 | 值 | 理由 |
|---|---|---|
| `scenario_id` | 计划身份 | 会话身份 |
| `anchor_world_m` | 锚点表 A_k（§8 表 2；y = 0.2） | 覆盖城区 |
| `target.route_world_m` | `[P_k, P_k + (0, 0, +1.0)]`（(f) 定义） | 本地证人；零转动 |
| `target.speed_mps` | 0 | 目标停放（`ScenarioConfig` 允许 0） |
| `sensor.retained_frame_count` | 10000 | 一次 Play ≈ 2,400 帧不被环形缓冲丢弃 |

**(c) 位置、视角与顺序（AR1-3 / AR2-1）**。全部几何以归档场景字节的 `anchor_world_m`
为原点：H 是相对 `anchor_world_m.y` 的垂直分量，位置 = 锚点 + (r·cos θ, H, r·sin θ)。

- **巡览位置 14 个**：H ∈ {14, 26} m；每高度 = 中心 C_H（r = 0）+ 圆环 R_H,θ
  （θ = 0°,60°,…,300°），圆环半径 `r(H) = 0.75·√(33² − H²)`（14 m → 22.4 m，26 m →
  15.2 m；33 m = 35 m 系留减 2 m 控制余量）。
- **证人位置 1 个**：W26 = (r(26), θ_W)，θ_W = 锚点到 P_k 的方位角取整到最近的 15°
  倍数，正好落在两倍数中点时取较小者；与某个 R26,θ 重合时仍是独立的一次访问（复访）。
- **视角**：每个巡览位置 16 个巡览视角 = 离天底角 20° 下方位角 0°,45°,…,315°，再离
  天底角 44° 下同序；look-at 地面点 = 位置 xz + `H·tan(离天底角)`·(cos az, sin az)，
  y = 0.2。C14、C26 在其 16 个巡览视角之后各追加 1 个证人视角（look-at P_k）；W26 只有
  1 个证人视角。合计 **15 个位置、224 个巡览视角 + 3 个证人视角 = 227 个视角**。
- **访问顺序（冻结）**：出生点（锚点正上方 25 m）→ C14 → R14 按 θ 升序 → C26 →
  R26 按 θ 升序 → W26 → 结束悬停。位置内按上条视角顺序执行。
- **位置净空与系留**：障碍 = `docs/evidence/P1-M3-BODY-001-scene-geometry.json`（S0 已
  钉死哈希）全部非车辆实例 AABB 的**闭集扩展框** `B' = [min_x−3, max_x+3] × [min_y,
  max_y+3] × [min_z−3, max_z+3]`。位置点必须在所有 B' 之外（严格）；违规则 H 以 2 m
  步长上调至多 30 m，**每步重算** `r' = min(r, √(33² − H'²))`、保持 θ，逐步重测；仍
  违规则丢弃该位置（`PLAN_POSITION_DROPPED`）。每个保留位置断言 `√(r² + H²) ≤ 33` 且
  H ∈ [8, 30]。计划有效条件：保留巡览位置 ≥ 10、证人视角 ≥ 3；否则 `plan` 拒绝。

**(d) 全路径净空（AR2-4）**。相邻位置间为直线转场段；每段对每个 B' 做**线段/AABB
精确相交测试**（slab 法，闭集边界），不采样。段与某些 B' 相交 → 绕行：令
`safe_world_y = max(起点 world y, 终点 world y, max(相交 B'.max_y) + 1)`，再令
`H_safe = safe_world_y - anchor_world_m.y`；即原障碍 `max_y + 3` 的闭扩展顶面外再留 1 m，
不是对已扩展顶面再加 4 m。起点垂直到 `safe_world_y`，水平移到终点正上方，再垂直到
终点；三段各自重新对全部 B' 做相交测试。`H_safe ∉ [8,30]`、任一绕行端点系留距离
`> 33 m` 或绕行段仍相交 → 丢弃终点位置（`PLAN_POSITION_UNREACHABLE`），从上一位置直连
下一位置重测，**不做侧向绕行**。到锚点的距离沿线段是凸函数、高度沿线段线性，极值都在
端点，故每段两端点的 `≤ 33 m` 与 `[8,30]` 断言足够（写入 plan 并配测试）。
plan.json（位置、视角、转场航点、每段相交测试结果）create-once，SHA 入 manifest。

**(e) 逐帧有效性与达成（AR2-1）**。每视角：发 `look_at_world` 后等 0.5 s 稳定，再停留
1.2 s（证人视角 4 s）；驱动器记录停留窗 = 稳定结束后到停留结束间从 `frames/latest.json`
观察到的 frame_id 闭区间。**每帧独立判定**：帧 f 为 `VALID_SURVEY` ⇔ f 属于某视角的
停留窗 ∧ 该帧 sidecar `camera_position_world_m` 与计划位置距离 ≤ 1.0 m ∧
`camera_forward_world` 与计划视线夹角 ≤ 3°（相机与机身同位，`SensorCamera` 局部位置
为零）；其余帧（起飞、转场、稳定等待、窗内不达标）为 `PROTOCOL_INVALID`。**视角
达成** ⇔ 其窗内 `VALID_SURVEY` 帧 ≥ 3（证人视角 ≥ 10）。**会话达成率** = 达成巡览
视角数 / 计划巡览视角数（证人视角另按 (f) 分母计）；< 90% → 整会话全部帧
`PROTOCOL_INVALID`。`close` 写 create-once `selection.json`：归档中每个 frame_id 恰一行
`{frame_id, view_id|null, class, reason}`；S0 attempt-2 钉住其 SHA，S1 断言归档 jpg
集合与清单逐 id 一一对应（多、少、类不在闭集即硬错误）。`PROTOCOL_INVALID` 沿既有
语义只作 train/dev 扩增，永不计 F 下限、永不进 test。

**(f) 停放目标证人（AR1-2 / AR2-2）**。

- **停放点**：候选 = 以 world (0,0) 为原点、`x,z ∈ ℤ` 的 1 m 网格上满足：(i) 按
  `check_anchor_placement.strictly_inside_surface` 同判据严格落入某路面 patch 且向内缩
  1.5 m，(ii) 到锚点平面距离 d ∈ [4, 26] m，(iii) 到由冻结基础几何按 default 六条调整
  派生的任一实际目录车辆 AABB 中心 ≥ 8 m，(iv) 在任一障碍 AABB 扩 4 m 之外，(v)
  `P_k + (0, 0, 1)` 同样满足 (i)–(iv) 且与 P_k 落在同一 patch。若两个端点同时落入多个
  patch，取「两端到四条 patch 边界的最小局部余量」最大者，仍平手按 UTF-8 `surface.id`
  升序；每个 (x,z) 只形成一个候选。再按 `(|d − 8|, x, z)` 升序编号 j = 1, 2, …。
  **`P_k.y` 唯一来源** = 该规范 patch 的 `surface_y_m`（取自与场景 `road_data_sha256`
  哈希相等的 `road_data.json` 字节）。
- **零转动证明**：目标由 `new GameObject` 生成，旋转 = 单位四元数（前向 = 世界 +z），
  `LoopTargetVehicle.Configure` 只设位置；`Step` 在 `speed = 0` 时位置不变、旋转按
  `RotateTowards(…, LookRotation(direction))` 转向 route[1]。停放段方向恰为世界 +z
  ⇒ `LookRotation(+z)` = 单位四元数 ⇒ **从第 0 帧起旋转恒为单位四元数**；段长 1.0 m
  ⇒ `delta.magnitude = 1.0 ≥ 0.5`，航点索引永不翻转。因此停放位姿 = (P_k, 前向 +z)
  对每一帧精确成立，`blocking(f)` 无过渡帧。plan 以测试断言方向向量逐位等于 (0, 0, 1)。
- **合法性门**：Unity bootstrap 的路线合法性审计以 `runtime/road_scene_audit.json`
  为权威；真实顺序是审计先于 `SensorFrameWriter` 创建。`drive` 观察到首帧后、发任何控制
  指令前必须读到该文件、其 `status` 为零违规且对应本会话场景，否则拒绝驱动并按 (h)
  关闭；bootstrap 因审计抛错时不会产生帧。`close` 把该报告复制入 `session/`；S2 对无该报告
  或报告非零违规的会话判整族 `INVALID`（审计失败场景下渲染的帧整体退出，**不作**
  `PROTOCOL_INVALID`）。工具的 (i)–(v) 预检只是减少无效 Play，不冒充审计。
- **证人视角与分母**：C14→P、C26→P、W26→P 各停留 4 s。`plan` 用
  `tools/dist_data/project_boxes` 与冻结构造 AABB（目标局部 x ∈ [−1, 1]、y ∈ [0, 1.55]、
  z ∈ [−2, 2]，前向 +z，置于 (P_k, surface_y)）预测每个证人视角离天底角 ≤ 40° 且
  visible 框短边 ≥ 16 px，不满足者丢弃；预测证人帧（每视角 20）< 60 → 换下一候选。
  **样本分母** = 三个证人视角窗内 `VALID_SURVEY` 帧中投影 visible 框短边 ≥ 12 px 者，
  须 ≥ 50，否则 `INSUFFICIENT_WITNESS_FRAMES`。
- **判定**：对分母内每帧，取像素落在 S0 red 色相带 [345°,15°) 且 S ≥ 0.5、V ≥ 0.35 的
  连通分量中与投影框相交且面积最大者，比较其外接框与投影 visible 框：中心命中
  ≥ 90% 且 IoU 中位数 ≥ 0.5（§2.3 既有阈值）→ `WITNESS_PASS`，否则 `WITNESS_FAIL`。
  `close` 以同一函数算**临时**结论写入 completion，S2 重算为**权威**，两者不等即硬错误。
- **与 `blocking(f)`**：停放目标按 (P_k, +z) 投影的框是该会话每一帧的图像面阻断体，与
  m3 真值框同处理；`class=car`/`color=red` 沿 BC-DATA-9 的版本化构造源继承（manifest
  记录 git HEAD 与构造 oracle 哈希）；`referable=false`，不入目录、不入 F1 分母；巡览帧
  `target_unbounded` 恒 false。

**(g) 驱动器**（`tools/run_grounding_survey.py`；只用既有桥：`velocity_world`/`hold`、
`look_at_world`、`frames/latest.json`、`tethered-sensor-frame/v3`）：

| 子命令 | 行为 | 拒绝 / 终态 |
|---|---|---|
| `plan --anchor k --plan-version v --candidate j` | 生成计划身份的场景配置与 plan.json（create-once，重跑字节幂等） | 锚点不在冻结表；位置 < 10；证人视角 < 3；候选不存在 |
| `prepare --session <id>` | 安装场景到 `runtime/scenario_config.json`；写 manifest（scenario/plan/几何 SHA、git HEAD、构造 oracle 哈希、信封序号 = 已用 Play 数 + 1）；写活动标记 | `runtime/frames/` 非空；已有 override/活动标记/率研究或 scouting 状态；信封用尽（拒绝即不计次） |
| `drive --session <id>` | 等首帧并核对 `scenario_id` 与零违规审计报告；每 0.2 s 发 `velocity_world`（v = clamp(1.0·Δ, 3 m/s)，`expires_after_s = 1.0` 续租，驱动器一死指令即过期、机身 hold；机身 4 m/s² 限幅由 plant 施加）；到达 = 距离 ≤ 0.3 m 且指令速度 ≤ 0.3 m/s 后 `hold` 并稳定 0.5 s；逐视角执行 (e)；写 drive_log.jsonl | 审计缺失/非零 → `DRIVE_REFUSED_AUDIT`；航点 30 s 未收敛 → `UNREACHABLE_RUNTIME` 跳过；视角 5 s 未稳定 → 跳过；10 s 无新帧 → `ABORTED_NO_FRAMES`；总 15 min → `ABORTED_TIMEOUT`；正常 → `DRIVE_COMPLETE`/`DRIVE_COMPLETE_WITH_SKIPS` |
| `close --session <id>` | (h) | (h) |
| `verify --session <id>` | 只读重算归档树 SHA、selection 一致性、清单闭集 | 任何不一致 |
| `diagnostic --anchor k` | COORD-005 诊断模式（§2.3 步 2） | 非空 `runtime/frames/`、已有 override 或活动标记 |

**(h) 无损归档与恢复（AR1-1 / AR2-3）**。`close` 两阶段：(1) 从 drive log 与 sidecar
生成 selection（(e)）、临时证人结论（(f)）、`tree.json`；(2) 在归档根同一文件系统建
`…/p1-vlm-survey/.staging-<session>/`，逐文件复制成员并**复制后重读比对 SHA**；(3) 整体
原子 `rename` 到 `…/p1-vlm-survey/<session>/`；(4) 在 `runtime/p1-vlm-survey/<session>/
completion.json` create-once 写逻辑树 SHA 与终态；(5) 仅当 (4) 成功才删除
`runtime/frames/` 中已核验成员、卸载 override、清活动标记。

- **`tree.json` 成员域**：归档根下除 `tree.json` 自身外的全部常规文件（`frames/*.jpg`、
  `frames/*.json`、`metrics.json`（如有）、`drive_log.jsonl`（如有）、`selection.json`、
  `session/scenario_config.json`、`session/manifest.json`、`session/road_scene_audit.json`
  （如有））；`completion.json` 在归档外记树 SHA，不属成员域。
- **零帧会话**（bootstrap 抛错、`drive` 因审计拒绝、或用户在首帧前退出）：`close`
  发现 `runtime/frames/` 为空，且 drive log 缺席或只含**发任何控制指令前**的拒绝/无帧终态
  时走零帧路径——只归档 `session/`（manifest、场景字节副本、审计报告如有、操作员
  Console 记录和该终态 log 如有），终态 `CLOSED_ZERO_FRAMES`，计
  Play、清标记；S0 会话表记 `frame_count = 0`，S1 断言该 unit 零 jpg。
- **重入**：存在 `.staging-<session>` 而无最终目录 → 逐成员对照源重验后从 (3) 继续；
  最终目录存在而 completion 缺失 → 重验树后写 completion；completion 已写而源未删净 →
  对源目录每个剩余文件：相对名在 `tree.json` 且 SHA 相等 → 删除；否则移入 create-once
  `runtime/frames.<session>-foreign-residue-hold/`（附录 A.3 新增 pattern →
  `DIAGNOSTIC_HOLD`，仅 inventory）；处理完即清标记解锁。树验证失败 →
  `CLOSE_TREE_MISMATCH`：归档保留、会话记 `PROTOCOL_INVALID`、不删任何文件、标记保留待
  人工对账（唯一不自动解锁的终态，需用户知情）。
- 终态闭集：`CLOSED_OK`、`CLOSED_PROTOCOL_INVALID`（达成率 < 90%）、`CLOSED_ZERO_FRAMES`、
  `CLOSE_INCOMPLETE_STAGING`（可重入）、`CLOSE_RESIDUE_RECOVERED`（重入后解锁）、
  `CLOSE_TREE_MISMATCH`。

**用户每会话动作**：`plan`（首次）→ `prepare` → 进入 Play（Game 视图活跃、Error
Pause 开）→ 另一终端 `drive` → 看到终态后退出 Play → `close`。Console 异常照实
报告，由接受/辅助角色代录 `docs/unity-test-log.md`（条目 id = 会话 id）。

### 2.2 `P1-VLM-DATA-001` 合同增量（逐工件 supersession；AR1-4 / AR2-5）

1. **附录 A / `tools/dist_data/roots.py`**：新增 A.1 行 `<RT>/p1-vlm-survey/*/frames/
   frame_*.jpg`（用途类 **`VALID_SURVEY`**，新增闭集值，加入 `FLOOR_USAGE_CLASSES`）；
   新增 A.3 行 `runtime/frames.p1-vlm-survey-diagnostic-*/frame_*.jpg` 与
   `runtime/frames.p1-vlm-survey-*-foreign-residue-hold/frame_*.jpg`（均 `DIAGNOSTIC_HOLD`）。
   family = source unit 目录名（会话 id）：条目 family 字段写占位 `<unit>`，
   `_family_of_unit` 对该占位返回 unit 末段。用途类先按 pattern 取 `VALID_SURVEY`，再按
   `selection.json` 逐帧降级为 `PROTOCOL_INVALID`（只降不升）。
2. **S2 绑定**：manifest `scenario_config_sha256` → 族内归档快照 `session/scenario_config.json`
   （已在 `SCENARIO_BYTE_PROVIDERS` 内）；partition = `(会话 id, sha)`。族级失效条件
   （任一 → `INVALID`，帧全部退出）：`session/road_scene_audit.json` 缺失或非零违规；
   `WITNESS_FAIL` / `INSUFFICIENT_WITNESS_FRAMES`；事后净空——任一 `VALID_SURVEY` 帧的
   `camera_position_world_m` 到归档锚点距离 > 35 m 或落入任一 B'。
3. **动态目标 schema 闭集新增 `target_parked`**（§2.1(f)：位姿 (P_k, +z) 由归档场景
   字节的 `route_world_m` 派生）；既有三种 schema 逐字不变。
4. **逐工件 supersession 与 S0 会话表**：S0–S5 attempt-2 各自 `supersedes: attempt-1`、
   `supersession_reason: "P1-VLM-DATA-002 survey roots"`；attempt-1 六件原样保留。S0
   attempt-2 新增 `survey_sessions` 表：每会话 `{session_id, plan_identity, archive_root,
   tree_sha256, selection_sha256, manifest_sha256, scenario_sha256, plan_sha256, frame_count,
   close_terminal}`；S1 断言实际枚举的会话集合与该表逐项相等（多、少、哈希不符均硬错误）。
   **顶层键 allowlist**：与 attempt-1 canonical bytes 允许不同的顶层键恰为 {`attempt`,
   `supersedes`, `supersession_reason`, 根清单键, 用途类闭集键, 目标 schema 闭集键,
   `survey_sessions`}（键名以 `contract.json` 实际顶层键为准，实现逐字列出）；测试断言
   其余顶层键字节相同，并单独断言 `FLOORS`、θ_occ 与投影常量、站位分箱、pHash 与切分
   seed、审计配额、颜色判定带六组逐字相同。
5. **attempt-3 工程重试的真实身份（AR2-5）**：attempt-2 = 首次正式执行。若某阶段在
   attempt-2 发布前失败（含 `IncompleteCompositeArtifactError` 残留），从**首个未发布
   阶段**起以 attempt-3 重跑。attempt-3 每次读直接依赖时按 `attempt-3` 已发布者优先、否则
   读 `attempt-2`，并把实际 ref 传到消费者；S2 读 inventory，S3 读 inventory+layout，S4
   读 frames_catalog，S5 读 frames_catalog+layout，缺任一即 fail-closed，禁止按 driver 的
   写入 attempt 事后合成 ref。每个 attempt-3 工件 `supersedes` 该阶段**最新已发布前身**
   （attempt-2 若已发布，否则 attempt-1），并写原因；attempt-3 再失败 → 回用户。为此
   **受影响接口**如实包括：`tools/dist_data/artifacts.py`
   （`write_composite` 新增 `supersedes`/`supersession_reason` 参数与 envelope 写入，
   现为写死 `null`）、`run_pipeline.py` 与 `contract.py` 的六个 S0–S5 写点（`contract`、
   `inventory`、`layout`、`frames_catalog`、`splits`、`field_catalog`）、`supersession_chain`
   读取；配生产回归覆盖普通工件链与组合工件链各一条（真实写盘函数产出 fixture）。
6. **S5 lineage 精确合同**（AR1-4 原文）：生产 `stage5_field_catalog()` 从本次实际读取
   取得 `frames_catalog` composite ref 与 `layout` ref，以固定顺序 `[frames_catalog_ref,
   layout_ref]` 写入 S5 envelope `inputs`；ref 恰含 `{artifact, attempt, sha256}`；生产回归
   须证明不是事后按路径合成，且任一 ref 错配 fail-closed。是否升格为 BC 由接受轮决定。
7. 既有全部归档族**原样保留**在根清单（并集）；`FLOORS`、θ_occ、站位分箱、pHash、切分
   规则、审计协议、S6–S9 一字不动。attempt-2 在全部会话 `close` 后 create-once 执行，
   并按轮 20/28 同格式产出新的审计前上界报告（`NOT_EVALUATED_PRE_AUDIT`）。

### 2.3 阶段、授权与门的顺序（AR1-5 / AR2-5）

| 步 | 内容 | 授权 / 门 | 消耗 |
|---|---|---|---|
| 0 | 接受轮 3 裁定本修订 | 接受角色 | 零 |
| 1 | **用户授权 #1**（§6 原话）：阶段 A 实现 + 至多 3 次 COORD-005 诊断 Play；保真 PASS 后创建首选正式 plan/scenario 身份 | 用户逐字 | 诊断 Play ≤ 3；正式 plan/scenario ID ≤ 10 |
| 2 | 阶段 A 实现候选 → **COORD-005 人眼保真检查**：`diagnostic --anchor 1` 生成只在 `runtime/` 生存的临时配置，`scenario_id` 逐字沿用 `config/scenario.default.json` 的既有值；不建正式 plan/config、session/run、标记或归档。前置 `runtime/frames/` 为空且无 override；用户进入 Play 约 30 s、不跑驱动器；退出后实现角色把 `runtime/frames/` 整体移入 create-once `runtime/frames.p1-vlm-survey-diagnostic-<d>-hold/`（d 是 hold 序号，不是 scenario/session/run ID）、卸载 override 恢复现场；选 2 张样帧（停放目标同框 1 张、≥ 3 辆目录车同框 1 张）由用户逐张确认，样帧路径、SHA、确认人、结论记入证据文件。不通过 → 修复 → 重新诊断（每次计诊断次数） | 用户目检；未完成 = 协议缺口 | 诊断 Play ≤ 3 次；零新 ID |
| 3 | 保真通过后才生成并纳入候选的首选正式 plan/config（每锚点至多一个，共 ≤ 10 个 plan/scenario ID）→ §4.3.1 四项自证 → 独立复核（PLAY_GOVERNING diff 非空，必开轮）→ `passed_candidate` | 复核角色 | plan/scenario ID ≤ 10 |
| 4 | **用户授权 #2**（§6 原话）：章程放宽 + 阶段 B–D 信封 | 用户逐字 | 零 |
| 5 | 阶段 B：锚点 1 试采会话（正式 Play #1）→ `close` → pilot 判定（§2.4）；后续任何 p2/候选 plan/config 都须先形成新的 PLAY_GOVERNING 停点并经复核通过 | 状态机 | 1 次 Play |
| 6 | 阶段 C：其余锚点按 §8 表 2 顺序各开会话；重试与零帧会话计信封 | 每会话 `close` 即停点 | ≤ 9 次 Play |
| 7 | 阶段 D：在已通过候选上执行 S0–S5 attempt-2 + 上界报告；无 PLAY_GOVERNING diff 不开复核轮，由接受角色核验正式工件并归因消费；失败按 §2.2 第 5 条 attempt-3；若 B/C/D 暴露代码修复 → 回停点，按 §4.4 开轮资格决定是否复核，再回本步 | 接受角色 | attempt 身份 ≤ 2 |
| 8 | 用户决定是否授权 S6 审计（`P1-VLM-DATA-001` 既有协议） | 用户 | — |

### 2.4 pilot 状态机与批次成败（AR1-6）

- **状态**：`PILOT_PENDING` →(close)→ `PILOT_CLOSED` →(只读分析)→ `PILOT_PASS` |
  `PILOT_FAIL_TOOL` | `PILOT_FAIL_SCENE`。分析是**正式 pilot 判定**，不是 COORD-005 诊断
  通道；由实现角色用工具从 pilot 归档 + layout attempt-1 + `project_boxes` 计算，不写
  正式工件。
- **预注册量**：达成率；`VALID_SURVEY` 帧数；证人分母与结论；事后净空结论；锚点 55 m 内
  每辆目录车的状态直方图与最佳短边；被降级 `PROTOCOL_INVALID` 的视角清单。
- **判定**：`PILOT_PASS` ⇔ 达成率 ≥ 90% ∧ 55 m 内车辆 ≥ 60% 在 ≥ 1 个 `VALID_SURVEY` 帧
  取得 `OK` ∧ `WITNESS_PASS` ∧ 净空通过。达成率 < 90% 或证人/净空失败 →
  `PILOT_FAIL_TOOL`（修复 → 停点 → 按 §4.4 资格复核 → 再试采，计信封）；达成率合格但
  `OK` 车辆 < 60% → `PILOT_FAIL_SCENE`（回用户，不自动改锚点）。
- **唯一一次修订**：仅在 `PILOT_PASS` 后、阶段 C 首个 `prepare` 前，实现角色可在「待
  裁定」节以预注册量为依据提出**至多一次**修订，可调集 = {H 集合（各值 ∈ [10, 30]）,
  巡览停留 s ∈ [1.0, 2.0], 圆环系数 ∈ [0.6, 0.85], 证人停留 s ∈ [3, 6]}；接受角色答复即
  BC 行 → 计划版本 v = 2 → 新计划身份（`-p2-c1`）；pilot 会话保持 v = 1 身份留在归档。
  **永不可调**：锚点表与顺序（只允许因不可达丢弃）、离天底角集、方位角集、帧率、保留
  数、达成容差、净空边距、证人阈值与分母、S0 全部常量。无修订请求则 v = 1 继续。
- **终态分立**：`PROTOCOL_INVALID`（转场/未达成/低达成率，图像与位姿真值未被否定）
  → 仅 train-aug；审计缺失或非零、`WITNESS_FAIL`、`INSUFFICIENT_WITNESS_FRAMES`、事后
  净空违规 → S2 `INVALID` → 整会话退出母集与全部计数。
- **批次成败**：阶段 D 后 `SURVEY_FLOORS_REACHABLE`（§5 第 5 条五项全过）或
  `SURVEY_FLOORS_UNREACHABLE`；后者只回用户二选一：另授权第二信封（新提案或 BC 行）或
  按章程走 `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA`；**不自动续批**。

## Inputs, outputs, and affected interfaces

- **新增**：`tools/run_grounding_survey.py`；`config/scenario.p1-vlm-survey-a<k>-p<v>-c<j>.json`
  与 `config/p1-vlm-survey-plans/<计划身份>/plan.json`（工具生成、create-once 并纳入版本
  控制）；`runtime/p1-vlm-survey/<session>/`（manifest、drive_log、
  completion；无 jpg）；`<RT>/p1-vlm-survey/<session>/{frames,session,selection.json,
  tree.json,metrics.json,drive_log.jsonl}`；`runtime/frames.p1-vlm-survey-diagnostic-*-hold/`
  与 `runtime/frames.p1-vlm-survey-*-foreign-residue-hold/`。
- **修改**：`tools/dist_data/{roots,contract,build_inventory,bind_layout,build_catalog,
  artifacts,run_pipeline}.py` 与对应测试（用途类、目标 schema、占位 family、逐帧
  selection、审计/证人/净空核验、S5 refs、S0 allowlist 与会话表、`write_composite`
  supersession 与六个写点）。
- **不动**：`Assets/**`（零 C#）、`config/scenario.default.json` 与全部既有冻结配置、
  `PROJECT_BRIEF.md`、既有归档与正式 attempt-1、`FLOORS`、θ_occ、站位分箱、pHash、
  切分规则、S6–S9、`P1-VLM-DIST-001` 的四臂/T-G1/BC-DIST-1…4。
- **消费的接口**：`tethered-drone-control/v1` 机身 `velocity_world`/`hold` 与云台
  `look_at_world`、`tethered-frame-manifest/v1`、`tethered-sensor-frame/v3`、
  `runtime/road_scene_audit.json`（`p1-scene-road-audit/v1`）、
  `check_anchor_placement.strictly_inside_surface`、`tools/dist_data/project_boxes`。

## Compatibility with the current v0.3 design

- **章程修订（推荐原话见 §6；按阶段向用户索取）**：`P1-VLM-DIST-001` §3.1「不得为
  补数据修改场景、加车、移动车辆或启动 Play」与 §7「不补采」对**本批**放宽为：允许一个
  用户授权、带信封的采集批，在新增的专用场景配置里改 `scenario_id`、`anchor_world_m`、
  两点停放段 `target.route_world_m`、`target.speed_mps = 0` 与
  `sensor.retained_frame_count`；专用配置**原样继承** default 已冻结的 6 条
  relocation/removal（bootstrap 照常搬移 3 辆、移除 3 辆），本批不新增或改变这 6 条，
  不再额外加车、移车或删车；不改 Unity scene asset，不改 `config/scenario.default.json`。
  既有 work item 与冻结场景不受影响；设计基线 M6 行由接受角色同步。
- **`P1-VLM-DATA-001` 的 BC 不变**：BC-DATA-1（下限不回调）、BC-DATA-9（目标字段权威）、
  BC-DATA-13（partition 绑定）、BC-DATA-23/24（交叉验证域）、BC-DATA-25/26（有界表示）
  全部沿用；§2.2 supersession 协议按设计逐工件使用，组合工件补齐同一协议。
- **吸收待决事项**：接受轮 31 待用户决定的有界 supersession 路径被 attempt-2 吸收；
  S5 lineage 债按 §2.2 第 6 条在本批闭合。若本提案被拒，该待决事项原状恢复。
- **不是调参**：本批不看任何 G0/确认性结果改阈值；pilot 唯一一次修订只涉及采集几何，
  可调集与不可调集在 §2.4 写死。

## Acceptance criteria

1. **工具机械性**：`plan` 重跑字节幂等；`prepare`/`close`/completion create-once；下列
   各配修复前必失败测试（fixture 由生产路径产出）：帧目录非空、活动会话冲突、信封用尽、
   位置落入 B'、线段/AABB 相交未绕行、`H_safe > 30` 未判不可达、系留 > 33 m 位置、
   端点极值断言、停放段方向非 (0, 0, 1)、审计缺失/非零时 `drive` 拒绝、逐帧有效性
   （窗内早期帧朝向 > 3° 被降级）、selection 与归档 jpg 集合不一致、零帧 `close`、
   `close` 三种重入（staging 残留、completion 缺失、completion 后残留含 foreign 文件）、
   零帧且只有 pre-command refusal log 的 `close`、
   `CLOSE_TREE_MISMATCH` 不删文件。
2. **每会话**：达成率 ≥ 90%（否则整会话 `PROTOCOL_INVALID`）；`selection.json` 覆盖全部帧；
   归档树 SHA 与 completion 一致；`runtime/frames/` 清空、override 卸载、标记清除；Unity
   日志条目 `UT-P1-VLM-DATA-002-<session>`（含 Console 结果与零帧原因）。
3. **绑定与证人**：全部 `VALID_SURVEY` 会话 S2 `BOUND`；归档审计报告零违规；证人分母
   ≥ 50、`WITNESS_PASS`；事后净空通过；`close` 临时结论与 S2 权威结论逐会话相等；巡览帧
   `target_unbounded` 恒 false。
4. **S0–S5 attempt-2/3**：每件各自 `supersedes` 最新已发布前身、create-once、字节幂等，
   attempt-1 原样保留；S0 顶层键 allowlist 与六组常量逐字相同断言通过；`survey_sessions`
   与 S1 枚举一致；`write_composite` 的 supersession envelope 与 `supersession_chain` 配
   普通链/组合链生产回归；失败落在 S2/S3/S4/S5 的具名回归逐一证明 attempt-3 的每个直接
   依赖 ref 来自实际读取的最新已发布 attempt-2/3 工件；S5 `inputs` 精确合同配具名回归
   `test_stage5_inputs_are_actual_read_refs`。
5. **预注册产出线（批次成败，不是 G0 verdict）**：上界报告满足 `U_F1 ≥ 60` 且 ≥ 6 类、
   `U_F3` train∪dev ≥ 60 / test ≥ 25、`U_F4` train∪dev ≥ 25 / test ≥ 10、train split
   非空。任一不达 → `SURVEY_FLOORS_UNREACHABLE`，后续只按 §2.4 回用户；**下限永不移动**。
6. **门**：COORD-005 保真证据（样帧、SHA、确认人、结论、诊断 hold 路径）先于正式
   plan/config 生成、停点自证与复核存在；诊断配置沿用 default 的既有 scenario id，零新
   scenario/session/run ID。阶段 A 一次稳定候选 + 独立复核；此后任何新 p2/候选 config 都
   是 PLAY_GOVERNING diff，须在用于 Play 前再过停点与复核；阶段 D 无该 diff 不开复核轮；
   Unity 列 = 用户 Play 采集记录，不申请 `UNITY_NA`。

## Baselines and ablations

不适用（数据批次）。本批不产生研究结论；四臂、δ、seed 归 D2。

## Failure modes and resource risks

| 风险 | 处置 |
|---|---|
| 机身/相机进入建筑包围盒 → 投影标签错 | 位置 + 线段/AABB 精确净空（§2.1(c)(d)）；事后净空核验 → 整会话 `INVALID` |
| nature/prop 过包围 AABB 在斜视角把车判 `EXCLUDED_OCCLUDED`（少算） | 20° 离天底视角减轻；方向保守；不调 θ_occ；损失入上界报告 |
| 颜色结构上限：出租车 13 辆已 `GROUP_INCONSISTENT`，警车 5、公交 6 无主色 → 可双验证上限 ≈ 77 | F1 ≥ 60 需皮卡/SUV/轿车/货柜/卡车/救护车各组一致；近距离 20° 视角提高主色占比；不达即 `SURVEY_FLOORS_UNREACHABLE` |
| 停放目标与某目录车同框冲突 `car`/`red car` 唯一性 | 设计使然，仅影响该帧该程序；P_k 离目录车 ≥ 8 m |
| Unity 路线合法性审计抛错（bootstrap 在 `SensorFrameWriter` 创建前抛错，故零帧） | `drive` 不发控制；会话按 (h) 的零帧路径归档并计 Play；换下一候选 = 新计划身份，且新 config 先过 PLAY_GOVERNING 复核 |
| 停放目标转向 | 已证明 +z 段零转动（§2.1(f)）；plan 测试断言方向向量 |
| 跨会话 pHash 并簇吞掉原子 | 锚点间距 ≥ 40 m，预期不并；同锚点重试会话预期并簇，按 §2.5 如实发生 |
| `close` 中途崩溃 / completion 后残留 | §2.1(h) 两阶段发布、三种重入、foreign 残留 hold；唯一不自动解锁的是 `CLOSE_TREE_MISMATCH` |
| 驱动器崩溃 / Play 提前退出 | 指令续租 1.0 s 过期即 hold；已落盘帧照常 `close`，逐帧有效性与达成率决定用途类 |
| S4 全对 pHash 比较随帧数平方增长 | 帧数 ≈ 2×，比较 ≈ 3.9×（§8）；manifest 已有界；只披露不改代码 |
| 磁盘 | 归档 ≈ 10 × 2,400 × 50 KB ≈ 1.2 GB；S3 shard 压缩 +≈ 0.9 GB |
| 资源 | 正式 Play ≤ 10（信封）+ 诊断 Play ≤ 3；零 API/GPU/模型/下载；用户时间 ≈ 8 会话 × 12 min ≈ 1.6 h + 诊断约 10 min；S6 审计另行授权 |

## Real-data dry run

构思侧只读扫描（2026-09-03，零写入、零 Play；未经复核，只作规划）。

**表 1 归档尺度与内存投影**

| 量 | 实测 | 本批投影 |
|---|---|---|
| S2 layout attempt-1 | 779 实例：nature 318 / prop 290 / vehicle 101 / building 70；车辆 x −3.6…244.0，z −13.6…209.3；非车辆高度 p50/p95/max = 6.1/16.9/27.0 m | 净空以 27 m 为最坏高度；`H_safe` 上限 30 m 意味着最高障碍（27 m）上方不可穿越，该类转场判不可达 |
| 每帧字节（scout-4 归档） | 121 MB / 2,405 帧 ≈ 50 KB（jpg ≈ 28–50 KB + sidecar ≈ 1 KB） | 10 会话 ≈ 24,000 帧 ≈ 1.2 GB |
| S3 行流 attempt-1 | 5,515,458,884 B 未压缩 / 932,548,072 B 压缩 ÷ 23,549 帧 ≈ 234 KB / 39.6 KB 每帧；S3 peak RSS ≈ 401 MiB（流式） | +24,000 帧 → +5.6 GB / +0.95 GB；RSS 不随帧数增长 |
| S4 pHash 全对比较 | C(23,549, 2) ≈ 2.77×10⁸，wall 297.5 s | C(47,549, 2) ≈ 1.13×10⁹ ≈ 4.1×，wall ≈ 20 min；manifest 已有界 |
| S2 绑定率 attempt-1 | 9 / 9 partition `BOUND`；两 scouting partition 交叉验证 centre 1.0 / IoU 0.999995 | 巡览族按归档副本绑定，预期 100%；**首次 Play 前无法实测**（如实披露） |
| S5 颜色（attempt-1 域内 16 辆） | 出租车 ×3 `GROUP_INCONSISTENT`；警车、公交 ×2 无主色；SUV_color01 1/2 验证；轿车/货柜/卡车/救护车已验证 | F1 可达上限 ≈ 77 |

**表 2 锚点表（只冻结坐标与顺序；候选数、覆盖数和生成叙述是未经复核的规划估计，
按 BC-SURVEY-9 不作门，诊断复算不等不得阻断）**

| 序 | 锚点 (x, z) | 新覆盖车辆 | 35 m 内车辆 | 30 m 内 > 8 m 障碍数（最高） |
|---|---|---|---|---|
| 1 | (206, 55) | 20 | 5 | 1（19.0 m） |
| 2 | (41, 58) | 19 | 3 | 7（27.0 m） |
| 3 | (194, 163) | 18 | 6 | 1（9.1 m） |
| 4 | (38, 163) | 17 | 5 | 1（9.1 m） |
| 5 | (95, −2) | 9 | 4 | 11（24.8 m） |
| 6 | (113, 163) | 9 | 5 | 1（9.0 m） |
| 7 | (182, 25) | 5 | 6 | 3（19.0 m） |
| 8 | (−10, −2) | 2 | 3 | 4（24.9 m） |
| 备 9 | (62, 79) | 1 | 7 | — |
| 备 10 | (191, 193) | 1 | 6 | — |

前 8 个锚点累计覆盖 99 / 101 辆（未覆盖：`Vehicle_Container_color02 (3)`、
`Vehicle_SUV_color01 (4)`），21 个（prefab, 皮肤）组全部有成员被覆盖；车辆最近邻
距离 p10/p50/p90 = 9.0/14.1/23.1 m。备用锚点只在信封仍有余量且前 8 个全部 `close`
后使用。半径 55 m 的依据：H = 26 m 时圆环半径 15.2 m + 44° 离天底角地面偏移 25 m
+ 半视场 ≈ 12 m；短边 12 px 对应斜距 ≈ 50–65 m。

**表 3 停放证人可行性（同一扫描：`road_data.json` 91 块路面、内缩 1.5 m、
离目录车 ≥ 8 m、离障碍 ≥ 4 m；候选按 (f) 排序后取 d ≈ 8 m 者）**

| 锚点 | 35 m 内合法停放候选数 | 最近候选距锚点 | 证人几何（d ≈ 8 m；C26→P 与 W26→P） |
|---|---|---|---|
| 1 (206, 55) | 243 | 8.9 m | C26 离天底 17°、深度 27 m、短边 ≈ 30 px；W26 离天底 ≤ 26°、短边 ≈ 28 px |
| 2 (41, 58) | 354 | 1.4 m（取 d ≥ 4 的次候选） | 同上量级 |
| 3 (194, 163) | 157 | 0.0 m（取次候选） | 同上量级 |
| 4 (38, 163) | 186 | 0.0 m（取次候选） | 同上量级 |
| 5 (95, −2) | 292 | 5.0 m | 同上量级 |
| 6 (113, 163) | 430 | 8.0 m | C26 离天底 17°、短边 ≈ 30 px |
| 7 (182, 25) | 250 | 3.6 m（取次候选） | 同上量级 |
| 8 (−10, −2) | 193 | 2.2 m（取次候选） | 同上量级 |

C14→P 视角在 d ≤ 14 m 时离天底角 ≤ 45°、深度 ≤ 20 m、短边 ≥ 40 px；三个证人视角各
20 帧，预测证人帧 60 ≥ 50 的分母要求。+z 方向 1 m 段在内缩 1.5 m 的 patch 内必然
合法，与 patch 的 yaw 无关。

## Suggested implementation scope

按序：(1) `contract.py`/`roots.py`/`build_inventory.py` 闭集增量、占位 family、逐帧
selection、S0 `survey_sessions` 与 allowlist 断言测试；(2) `artifacts.py`
`write_composite` supersession + 六个写点 + `supersession_chain` 回归；(3) `bind_layout.py`
`target_parked` 绑定、审计报告/证人/净空权威判定；`build_catalog.py` 停放目标阻断体；
(4) S5 精确 refs 与具名回归；(5) `tools/run_grounding_survey.py` 六个子命令 + §5 第 1 条
全部拒绝回归（fixture 由生产路径产出）；(6) 诊断 Play 保真 → 停点自证。阶段 B–D 不含
新代码，除非 pilot/采集暴露缺陷（回停点，复核按 §4.4 资格）。

## Open questions（收敛为一份推荐案；接受后分阶段向用户索取）

授权 #1 已于 2026-09-03 签发入账；用户 2026-09-05 以「授权继续」确认下列授权 #2，
章程限域放宽及阶段 B–D 信封已入账（`docs/authorizations.md`）。两条授权文字保留如下：

1. **授权 #1（阶段 A；已签发）**：「授权 P1-VLM-DATA-002 阶段 A：实现巡览工具、DATA-001 合同
   增量（含 artifacts.py 组合工件 supersession）与测试；允许至多 3 次 COORD-005 诊断
   Play，诊断临时配置沿用 config/scenario.default.json 的既有 scenario_id，不创建或消耗
   新 scenario/session/run ID，帧移入诊断 hold；保真 PASS 后允许创建至多 10 个首选正式
   plan/scenario ID 及对应版本化专用 plan/config，供稳定候选复核。零正式采集 Play、零
   session/run ID、零 API、零 GPU；不改 Unity scene asset、config/scenario.default.json
   或其他既有配置；不执行正式 S0–S5/supersession」。
2. **授权 #2（章程放宽 + 信封；已签发）**：「对 P1-VLM-DATA-002 放宽 P1-VLM-DIST-001 §3.1 与 §7：
   允许本批在专用配置里改 scenario_id、anchor_world_m、两点停放段 route_world_m、
   speed_mps = 0 与 retained_frame_count；专用配置原样继承 default 已冻结的 6 条
   relocation/removal，本批不新增或改变这 6 条，不再额外加车、移车或删车；不改 Unity
   scene asset。信封：阶段 = B–D；正式 Play 次数上限 = 10（含试采、重试与零帧会话）；
   新增 plan/scenario ID 上限 = 10，session ID 上限 = 10；attempt 身份上限 = 2
   （attempt-2 首次执行 + attempt-3 工程重试）；GPU·h 上限 = 0；API 次数上限 = 0；
   Unity/Play = 是，仅 p1-vlm-survey-* 场景；任何新增 p2/候选 plan/config 在 Play 前先过
   PLAY_GOVERNING 停点与复核」。

其余项（停放点、候选顺序、锚点顺序、pilot 修订机制）均已机械化，不需要用户选择。

## Binding clarifications (BC table)

| 编号 | 条款 | 依据 | 日期 |
|---|---|---|---|
| BC-SURVEY-1 | `B'` 已含原障碍顶面 +3 m；绕行安全世界高度只能再加 1 m，并换算成相对锚点的 `H_safe`。三段闭集相交、`H_safe ∈ [8,30]` 和每端点系留 `≤33 m` 任一不满足均为 `PLAN_POSITION_UNREACHABLE`；不得把 `B'.max_y` 再加 4 m。 | AR2-4；世界/相对坐标唯一化 | 2026-09-03 |
| BC-SURVEY-2 | Bootstrap 的两项路线/道路审计均早于 `SensorFrameWriter`；`drive` 只能在观察首帧后、发任何控制前核对本次场景零违规报告。审计抛错按零帧处理；zero-frame `close` 接受无 drive log 或仅含 pre-command refusal/no-frame terminal 的 log。 | 真实 `TetheredScenarioBootstrap.Awake` 调用序 | 2026-09-03 |
| BC-SURVEY-3 | COORD-005 诊断不得创建/消耗新 ID：临时 runtime 配置沿用 default 既有 `scenario_id`，诊断序号只命名 hold，不是 ID；不生成正式 plan/config/session。保真 PASS 后才可按授权 #1 创建至多 10 个首选正式 plan/scenario ID。 | workflow §4.3.2；轨道/授权真实性 | 2026-09-03 |
| BC-SURVEY-4 | attempt-3 从首个未发布阶段续跑时，每条直接依赖按「已发布 attempt-3 优先，否则 attempt-2」实际读取并携带 ref；S2=inventory，S3=inventory+layout，S4=frames_catalog，S5=frames_catalog+layout。缺失即失败；写入 attempt 与读取 attempt 不得强绑或事后伪造。 | 生产 driver 当前把读写都绑到 `self.attempt` | 2026-09-03 |
| BC-SURVEY-5 | 正式 plan 存于 `config/p1-vlm-survey-plans/<identity>/plan.json`，与同身份 scenario config 一并 create-once、纳入版本控制。初始文件在保真后进入首个稳定候选；pilot p2 或候选切换产生的新文件属于 PLAY_GOVERNING diff，必须在下一次 Play 前重走停点和独立复核。 | §4.3.1/§4.4；配置不可脱离通过候选 | 2026-09-03 |
| BC-SURVEY-6 | §6 两条修订后原话是唯一可请求的执行授权：#1 仅阶段 A、≤3 诊断 Play、保真后 ≤10 首选 plan/scenario ID；#2 仅 B–D、≤10 正式 Play、≤10 新 plan/scenario ID、≤10 session ID、attempt-2/3。缺项仍按 0；任何越界回用户。 | COORD-008 S4；AR2-6 | 2026-09-03 |
| BC-SURVEY-7 | S0 attempt-2/3 的 `contract` payload 必须新增顶层 `root_manifest`，并列入 supersession allowlist；它按运行时顺序逐字投影 `ENUMERATION_ROOTS`、`ROOT_EXCLUDED_PREFIXES`、`MUST_BE_EMPTY_DIRS` 与 `ROOT_TABLE` 的操作字段 `{pattern, kind, usage_class, family, layout_class}`，不含说明性 `note` 或编译后 regex。S1 在枚举前须把当前操作表与其实际读取的 S0 `root_manifest` 比较，不等即失败。既有 attempt-1 字节保持不动；allowlist 回归必须以存量正式 attempt-1 payload（或其逐字 bytes fixture）对比 attempt-2，并断言差异键**恰为** `{root_manifest, usage_classes, dynamic_target, survey_sessions}`，不得用当前 `contract_document()` 同时生成“前后”两侧。不得以 `usage_classes` 代替根 pattern/映射的哈希冻结。 | §2.2 第 4 条确实点名根清单键；当前 `contract_document()` 没有该键，且现测试用当前函数生成两侧，均不足以证明真实 supersession 边界 | 2026-09-03 |
| BC-SURVEY-8 | §2.1(f)(iv) 的“障碍 AABB 扩 4 m”是 x/y/z 三轴各向外 4 m 的闭集扩张；停放点 `(x, surface_y, z)` 同时落入三个扩张轴区间才被拒绝。不得把该选择另称为比纯水平判据更保守；它只是本合同的唯一三维语义。 | 实现期请求 2；冻结边界与措辞 | 2026-09-03 |
| BC-SURVEY-9 | §8 表 2 只冻结十个锚点的坐标、序号与使用顺序；`2,684`、逐锚点覆盖数、`99/101` 与候选生成叙述均是规划估计，不是门或可引用证据。`recompute_anchor_candidates` 只能输出诊断差异，任何不等不得使 `plan`/pipeline 失败，也不得改写锚点表。锚点常量不豁免 §2.1(c)–(f) 的位置、转场、停放候选、系留与道路审计硬门；正式可达性只由这些门和 §2.4/§5 的预注册终态决定。 | §8 自述“未经复核、不进证据链”；实现复算 2,393 且锚点 8/10 不满足该规划生成叙述 | 2026-09-03 |
| BC-SURVEY-10 | 既有“无逐帧目标真值、使用全路线扫掠代理”的第三个动态目标分支，其唯一 schema 名称为 `sweep_proxy`；attempt-2/3 的闭集顺序为 `m3, scouting, sweep_proxy, target_parked`。命名不得改变既有代理判定、字段或历史工件。 | 实现期请求 4；给既有匿名分支稳定名称 | 2026-09-03 |
| BC-SURVEY-11 | `VALID_SURVEY` 在 `USAGE_CLASSES` 中唯一插入于 `VALID_PARENT_HOLD` 之后、`PROTOCOL_INVALID` 之前；表序仍是 lineage primary 优先级，且全部既有用途类之间的相对顺序逐字不变。 | 实现期请求 5；避免复制 lineage 的优先级漂移 | 2026-09-03 |
| BC-SURVEY-12 | 证人红色分量必须扫描整幅图，以 4-邻接形成分量并输出右/下开像素框；只保留与投影 visible 框相交的分量，按 `(area, box)` 取最大（面积同值时取字典序较大的 box）。不得改为 8-邻接或投影框裁窗。真实巡览帧尚未存在，因此本条只冻结预数据算法，不声称像素门已通过。 | 实现证据 §6 的结果驱动自由度；正式数据前消除实现者自选参数 | 2026-09-03 |
| BC-SURVEY-13 | `selection.view_id` 的合法值必须来自该会话 manifest 所钉、字节哈希相符的已复核 plan：巡览为 `s/<position_id>/<00..15>`，证人为且仅为 `w/C14`、`w/C26`、`w/W26`；窗外帧为 `null`。S1/S2 对非 `null` 值须做完整语法和 plan 成员校验，未知/畸形/仅前缀匹配一律失败，禁止用 `startswith("w/")` 决定证人资格。 | 实现证据 §6 的 schema 自由度；当前 S2 仅前缀识别，可让未绑定 plan 的标签进入证人分母 | 2026-09-03 |
| BC-SURVEY-14 | S0 attempt-2/3 的 `contract` payload 新增顶层 `survey_acquisition`；本条仅在差异集合上取代 BC-SURVEY-7：相对不可变 attempt-1 的 payload 差异键必须恰为 `{root_manifest, usage_classes, dynamic_target, survey_sessions, survey_acquisition}`。该块须是完整采集协议的 canonical JSON 投影：全部公开 `SURVEY_*` 协议常量、BC-SURVEY-12 的连通性，以及驱动器内会影响身份、资源信封、安全、计划、逐帧分类或证人/S2 判定的锚点表与顺序、出生高度、schema/protocol id 和数值常量均须显式收口，不得留下由当前模块字面量静默决定正式结果的旁路。`plan.json` 与会话 manifest 均须携带该 canonical bytes 的 SHA-256；`prepare`、`drive`、`close`（含重入）、`verify`、S1、S2 在发布、发指令、释放现场、枚举或判定前分别核对 plan/manifest/S0/当前运行投影，任一漂移即失败。回归至少证明：attempt-1 fixture 的差异恰为五键；新增一个受管常量但漏投影会失败；任一钉子或当前投影变异会使上述各生产入口 fail-closed。 | 实现证据 §9 主动披露：会改变达成、净空与证人结论的采集常量不在 S0 哈希面；选项 (a) 能同时保住 DATA-001 的自描述合同与 Play 前已复核计划 | 2026-09-03 |
| BC-SURVEY-15 | BC-SURVEY-12 的“右/下开”适用于该分量框的全部消费者；中心命中只能用 `x0 ≤ cx < x1 ∧ y0 ≤ cy < y1`。当前 `evaluate_parked_witness()` 对 `x1/y1` 使用 `≤`，必须改为半开判断，并以中心恰落右边界、下边界和左/上边界的三组具名回归证明方向。 | Acceptance round 4 代码核查；当前实现把已冻结的半开框重新当成闭框 | 2026-09-03 |
| BC-SURVEY-16 | 十个锚点的坐标与顺序仍冻结；按该顺序对每个锚点的**全部**停放候选依冻结次序只读求 plan，取首个过 §2.1(c)–(f) 硬门者。无合法候选或全部 plan 无效即记该锚点 `PLAN_POSITION_UNREACHABLE`，不得创建 plan/scenario/session ID 或消耗 Play；备 9/10 在前八项分别已 `close` 或到达该不可达终态后才依序启用。当前可达序列为 1/2/3/4/6/7/9；5/8/10 丢弃，规划性的 `99/101` 不作下调后的新承诺。F1–F4、pilot 与 §5 五项批次门均不变；七锚点若最终不能过门，仍只能落 `SURVEY_FLOORS_UNREACHABLE` 回用户，不得换坐标、放宽阈值或自动续批。回归须穷举当下 5/8 的全部实际候选并证明均无效、10 无候选，同时证明七个可达锚点各自首个合法候选与冻结顺序。 | 实现证据 §9 的新待裁定；Acceptance 只读实跑补足“前六个候选”不足，5/8 的全部 135/128 个实际候选均无有效 plan，10 无候选；§2.4 已允许因不可达丢弃 | 2026-09-03 |

### Accepted 后的解释行（COORD-009）

| 编号 | 条款 | 复核项 | 证明方式 | 标签 | 依据 | 日期 |
|---|---|---|---|---|---|---|
| BC-SURVEY-17 | **解释 BC-SURVEY-14，不新增义务。** 该条的 `survey_acquisition` 顶层键闭集恰为 `{schema_version, work_id, constants}`；其中 `constants` 键闭集恰为以下 89 项：`SURVEY_ACQUISITION_VERSION`, `SURVEY_ACTIVE_MARKER_FILENAME`, `SURVEY_ACTIVE_MARKER_SCHEMA`, `SURVEY_ANCHOR_CANDIDATE_GRID_M`, `SURVEY_ANCHOR_COVERAGE_RADIUS_M`, `SURVEY_ANCHOR_TABLE`, `SURVEY_ANCHOR_Y_M`, `SURVEY_ARRIVAL_DISTANCE_M`, `SURVEY_ARRIVAL_SPEED_MPS`, `SURVEY_BEARING_TOLERANCE_DEG`, `SURVEY_BIRTH_HEIGHT_M`, `SURVEY_CLOSE_TERMINALS`, `SURVEY_COMMAND_LEASE_S`, `SURVEY_COMPLETION_SCHEMA`, `SURVEY_CONTROL_PROTOCOL`, `SURVEY_DEFAULT_SCENARIO_PATH`, `SURVEY_DETOUR_EXTRA_M`, `SURVEY_DRIVE_GAIN`, `SURVEY_DRIVE_LOG_SCHEMA`, `SURVEY_DRIVE_MAX_SPEED_MPS`, `SURVEY_DRIVE_TERMINALS`, `SURVEY_DRIVE_TICK_S`, `SURVEY_DWELL_S`, `SURVEY_FRAME_CLASSES`, `SURVEY_FRAME_MANIFEST_SCHEMA`, `SURVEY_GROUND_LOOK_AT_Y_M`, `SURVEY_HEIGHTS_M`, `SURVEY_HEIGHT_STEP_M`, `SURVEY_MANIFEST_SCHEMA`, `SURVEY_MAX_DIAGNOSTIC_PLAY`, `SURVEY_MAX_FORMAL_PLAY`, `SURVEY_MAX_HEIGHT_M`, `SURVEY_MAX_PLAN_IDENTITIES`, `SURVEY_MAX_TETHER_RADIUS_M`, `SURVEY_MIN_ACHIEVEMENT_RATE`, `SURVEY_MIN_HEIGHT_M`, `SURVEY_MIN_KEPT_SURVEY_POSITIONS`, `SURVEY_MIN_VALID_FRAMES_PER_VIEW`, `SURVEY_MIN_VALID_FRAMES_PER_WITNESS_VIEW`, `SURVEY_MIN_WITNESS_VIEWS`, `SURVEY_MUTABLE_SCENARIO_FIELDS`, `SURVEY_NO_FRAME_TIMEOUT_S`, `SURVEY_OBSTACLE_EXPANSION_TOP_M`, `SURVEY_OBSTACLE_EXPANSION_XZ_M`, `SURVEY_OFF_NADIR_DEG`, `SURVEY_PARKED_ANCHOR_DISTANCE_M`, `SURVEY_PARKED_MIN_CATALOG_VEHICLE_M`, `SURVEY_PARKED_OBSTACLE_MARGIN_M`, `SURVEY_PARKED_SEGMENT_M`, `SURVEY_PARKED_SURFACE_INSET_M`, `SURVEY_PLAN_DIRECTORY`, `SURVEY_PLAN_DROP_REASONS`, `SURVEY_PLAN_SCHEMA`, `SURVEY_POSITION_TOLERANCE_M`, `SURVEY_RETAINED_FRAME_COUNT`, `SURVEY_RING_AZIMUTHS_DEG`, `SURVEY_RING_COEFFICIENT`, `SURVEY_ROAD_AUDIT_CLEAR_STATUS`, `SURVEY_ROAD_AUDIT_SCHEMA`, `SURVEY_RUNTIME_OVERRIDE_FILENAME`, `SURVEY_SELECTION_SCHEMA`, `SURVEY_SENSOR_FRAME_SCHEMA`, `SURVEY_SESSION_ROW_KEYS`, `SURVEY_SESSION_TIMEOUT_S`, `SURVEY_SETTLE_S`, `SURVEY_TETHER_CONTROL_MARGIN_M`, `SURVEY_TETHER_LENGTH_M`, `SURVEY_TREE_EXCLUDED_NAMES`, `SURVEY_TREE_SCHEMA`, `SURVEY_VIEW_AZIMUTHS_DEG`, `SURVEY_VIEW_ID_SURVEY_PREFIX`, `SURVEY_VIEW_ID_WITNESS_PREFIX`, `SURVEY_VIEW_INDEX_MAX`, `SURVEY_VIEW_SETTLE_TIMEOUT_S`, `SURVEY_WAYPOINT_TIMEOUT_S`, `SURVEY_WITNESS_AZIMUTH_QUANTUM_DEG`, `SURVEY_WITNESS_CONNECTIVITY`, `SURVEY_WITNESS_DWELL_S`, `SURVEY_WITNESS_MIN_DENOMINATOR`, `SURVEY_WITNESS_MIN_SIDE_PX`, `SURVEY_WITNESS_POSITION_IDS`, `SURVEY_WITNESS_PREDICT_FRAMES_PER_VIEW`, `SURVEY_WITNESS_PREDICT_MAX_OFF_NADIR_DEG`, `SURVEY_WITNESS_PREDICT_MIN_FRAMES`, `SURVEY_WITNESS_PREDICT_MIN_SIDE_PX`, `SURVEY_WITNESS_SATURATION_MIN`, `SURVEY_WITNESS_VALUE_MIN`, `SURVEY_WITNESS_VERDICTS`, `SURVEY_WORK_ID`。BC-SURVEY-14 的“全部/任一”只在此闭集及其已点名六入口、四侧钉子、五差异键上判定；未列成员不得借该全称量词扩张本条，后续缺口只由复核按可达性判 `IN_SCOPE_NO_BC` 或 `SCOPE_GAP`。 | 行为/几何时序/边界失败/测试覆盖/文档一致 | test:`tests/test_dist_data_survey.py::SurveyAcquisitionProjectionTest`（顶层三键、`constants` 精确 89 键及 canonical pin） | CLARIFY | COORD-009 §7 T9；解释 BC-SURVEY-14 | 2026-09-03 |
| BC-SURVEY-18 | **解释 BC-SURVEY-16，不新增义务。** “每个锚点的全部停放候选”闭集是冻结锚点表逐行调用 `tools/run_grounding_survey.py::parked_candidates` 的有序输出；回归以该输出的连续 `candidate_index` 枚举计数为准：锚点 `1: 1..53`、`2: 1..209`、`3: 1..60`、`4: 1..74`、`5: 1..135`、`6: 1..248`、`7: 1..62`、`8: 1..128`、`9: 1..217`、`10: ∅`。BC-SURVEY-16 的“全部/均”只在这十个已枚举集合上判定；5/8 须分别对 135/128 个成员逐一求 plan 且全无效，10 须保持空集，1/2/3/4/6/7/9 须保持候选 1 为首个合法 plan；集合外的缺口只由复核按可达性判 `IN_SCOPE_NO_BC` 或 `SCOPE_GAP`。 | 行为/几何时序/边界失败/测试覆盖/文档一致 | test:`tests/test_survey_tool.py::AnchorTableReachabilityTest`（十锚点枚举计数、5/8 全量无效、10 空集、七锚点首个合法） | CLARIFY | COORD-009 §7 T9；解释 BC-SURVEY-16 | 2026-09-03 |
| BC-SURVEY-19 | **解释 BC-SURVEY-6/16 与 §2.4，不新增义务或状态。** 本次 `p1-vlm-survey-a1-p1-c1-s1` 达成率 0、证人不足，归 `PILOT_FAIL_TOOL`，不得置于状态机外或改成零帧会话；drive/close/S2 分别保留 `ABORTED_NO_FRAMES` / `CLOSED_PROTOCOL_INVALID` / `INVALID`。依据实现证据 §19.2，根因为 Editor 失焦的环境阻塞，纠正操作顺序后的同计划 s2 是授权 #2 内工程重试；两次 Play 与两会话身份均计数，不重置额度。此次未产生代码/计划修复，manifest 所记提交与终局通过候选的 PLAY_GOVERNING 差异为空，沿用已通过停点，依 §4.4 不开空 diff 复核轮；这不豁免新代码/计划的停点，也不把尚缺的采集前工作树记录补认成存在。s1 的 19 帧依证人不足由 S2 排除，s2 的 pilot 判定另记。 | 行为/边界失败/文档一致 | artifact:runtime/dist-data/layout/attempt-2/layout.json；artifact:docs/evidence/P1-VLM-DATA-002-stage-a-implementation.md（§19.2–19.3） | CLARIFY | 解释 BC-SURVEY-6/16、§2.4；实现待裁定 §19.2；COORD-008 S4 | 2026-09-07 |

复核项覆盖：行为 ✓；几何时序 ✓；边界失败 ✓；测试覆盖 ✓；文档一致 ✓。

## Pending rulings（待裁定）

2026-09-03：实现证据 §9 的 acquisition 请求由 BC-SURVEY-14 选择选项 (a)，半开边界由
BC-SURVEY-15 收束；新锚点请求由 BC-SURVEY-16 接受七个可达锚点，但不降低任何冻结门。
BC-SURVEY-17/18 已收束闭集；实现证据 §19.2 的 s1 归类由 BC-SURVEY-19 答复。
2026-09-07：阶段 D 消费结论为 `SURVEY_FLOORS_UNREACHABLE`（S5 双验证 37 < 60）；不是 G0 verdict。
用户待选 §2.4 第二信封或章程数据不足终态；正式 Unity 事前工作树与 Console 记录待补，详见 Unity 日志。

## Acceptance rulings（复判）

| 复核文件 / 轮次 / finding | 裁定 | 日期 |
|---|---|---|
| `docs/reviews/P1-VLM-DATA-002.md` / `R2@stageA` / F5 | **范围内必修，不改标 `SCOPE_GAP`。** 生产入口可达，`--through` 是既有执行停止界；越界发布 create-once 工件会不可逆消耗 attempt 身份。修复须在运行任一阶段前拒绝“停止点已被续跑跳过”的请求，并以生产 `run_stages` 具名回归证明修前会写、修后零写。 | 2026-09-05 |
| `docs/reviews/P1-VLM-DATA-002.md` / `R2@stageA` / F6 | **范围内必修，不改标 `SCOPE_GAP`。** 不合式 attempt 可由生产 CLI 直接触发并绕过已接受的谱系与两身份信封。生产入口须只接受 `attempt-<正整数>`，拒绝时零写；具名回归须证明修前写出无谱系树、修后 fail-closed，且 `attempt-1` 行为不变。 | 2026-09-05 |
| `docs/reviews/P1-VLM-DATA-002.md` / `R2@stageA` / F3 | **范围内、非阻断 CLASS_3；逐字补丁已应用。** 只校正设计版本状态行与 M6 时态，不改数字、ID、门或 disposition；不进 SCOPE_GAP 账本。 | 2026-09-05 |

实现证据 §17 的自查项记为 **I17，范围内必修**：它是 F2 的续跑修复自身引入的回归，且生产默认
`--through g0_report` 会消费该路径；其义务已由 BC-SURVEY-4 的“实际读取 attempt 与写入 attempt
不得强绑”和 §2.3 阶段 D 的 S0–S5 + 上界报告覆盖，**不新增 BC/`NEW_OBLIGATION`，也不改动冻结集**。
实现须用生产默认停止点证明：一致 lineage 可完成；不一致时在发布新的 attempt 工件前失败。最终分级与
闭合已由终局 `R3@stageA` 核实（2026-09-05 `PASS_WITH_NOTES`）；接受角色已消费并收尾阶段 A
复核门。归因、四项度量及非阻断待办见 `docs/implementation-status.md` 的 stage-A 收尾记录。
阶段 A 当时无正式 Unity；B–D 后续结果见 `docs/implementation-status.md`，工作项仍未 `DONE`。

## Contract conformance（核对表）

`C1@stageA`（2026-09-04）只读核对候选 `bc83728` 的完整声明范围、直接关联代码、
BC-SURVEY-1…18 与实现证据 §10/§11；本轮未运行测试、未修改实现、未新增 BC，也不签发
独立复核 verdict。结论：14 项满足、4 项不满足、0 项证据缺失；按 COORD-009 对本停点的
既定处置，本轮无退回权，全部不满足项与关注项随候选交 `R1@stageA` 核实。

| 编号 | 结论 | 理由 |
|---|---|---|
| BC-SURVEY-1 | 满足 | `transition_waypoints()` 以相交 `B'.max_y + 1 m` 求 `H_safe`，并逐段复核闭集相交、`[8,30]` 与 33 m 端点系留；实现证据 §2 的具名几何回归对准条款。 |
| BC-SURVEY-2 | 不满足 | 首帧后的审计前置已落地，但零帧 `close` 只读取 drive-log 首行终态：`_drive_windows()` 丢弃其余事件，`close_session()` 对任意 `ABORTED_NO_FRAMES` 都放行，不能证明日志“仅含” pre-command refusal/no-frame terminal；证据只覆盖 `DRIVE_COMPLETE` 这一种 post-command 反例。 |
| BC-SURVEY-3 | 满足 | `install_diagnostic()` 沿用 default `scenario_id`，不建 plan/config/session/marker；§11 记录诊断 Play 1/3、零新 ID、hold 路径与用户逐帧确认，截断车辆仍是同框目录车且条款未要求完整框。 |
| BC-SURVEY-4 | 不满足 | `PipelineDriver._read_ref()`、`_catalog_stream()` 与 S2 仍只读 `self.attempt`，`run_stages()` 也总从 S0 开始；没有“attempt-3 优先、否则 attempt-2”的逐依赖解析。`Attempt3ReadRefTest` 两条仅测写侧 supersession 参数与同-attempt refs，没有构造任何混合 attempt。 |
| BC-SURVEY-5 | 满足 | `write_plan()` 将同身份 plan/config 写入冻结路径并经 `_create_once_json()` 发布；7 对正式文件在保真后进入候选，证据 §10 记录重跑字节幂等与 PLAY_GOVERNING 范围。 |
| BC-SURVEY-6 | 满足 | 三个信封上限均来自合同投影；`prepare_session()`、`write_plan()`、`install_diagnostic()` 在越界前拒绝，证据 §2 有三条具名边界回归；授权 #2 仍关闭。 |
| BC-SURVEY-7 | 满足 | `root_manifest()` 逐字投影四个成员与五个操作字段，S1 枚举前 canonical 对账；冻结 attempt-1 bytes fixture 和 allowlist 回归均在证据 §2 点名。 |
| BC-SURVEY-8 | 满足 | `_clear_of_obstacles()` 对 x/y/z 三轴各扩 4 m 且按闭区间拒绝；三条边界回归与代码判据一致。 |
| BC-SURVEY-9 | 满足 | 锚点坐标/顺序由合同常量冻结，`recompute_anchor_candidates()` 仅报告差异；plan/diagnostic 仍走全部位置、转场、停放与系留硬门。 |
| BC-SURVEY-10 | 满足 | schema 闭集顺序为 `m3, scouting, sweep_proxy, target_parked`；既有无 schema 分支仍单独走 sweep proxy，测试同时拒绝把 `sweep_proxy` 当成可传入真值 schema。 |
| BC-SURVEY-11 | 满足 | `VALID_SURVEY` 唯一插在 `VALID_PARENT_HOLD` 与 `PROTOCOL_INVALID` 之间，旧闭集相对顺序和 lineage priority 回归均保持。 |
| BC-SURVEY-12 | 满足 | `red_components()` 实际强制 4-邻接并扫描经真实尺寸核对的整帧，输出右/下开框；`select_witness_component()` 按 `(area, box)` 最大选择相交分量。 |
| BC-SURVEY-13 | 满足 | plan 路径/字节/身份钉子与完整 view-id 语法均 fail-closed；S1、S2、drive、close、verify 使用 plan 成员闭集，前缀分类函数已删除。 |
| BC-SURVEY-14 | 不满足 | 89 项投影与六入口钉子主体已落地，但 `stage0_contract()` 在零归档时传 `sessions or None` 并省略 `survey_sessions`；`ContractAllowlistTest.test_the_shape_the_driver_would_actually_publish_today` 还明确接受四键差异，违反本条冻结的“差异键恰为五键”。 |
| BC-SURVEY-15 | 满足 | `evaluate_parked_witness()` 的中心命中逐字使用 `x0 ≤ cx < x1`、`y0 ≤ cy < y1`，右/下边界回归对准生产表达式。 |
| BC-SURVEY-16 | 不满足 | 全候选穷举、不可达零身份与七锚点首个合法候选已落实；但 `prepare_session()` 没有检查前八项的 close/不可达状态，也没有限制备 9/10 依序启用，现有回归只验证只读可达序列。 |
| BC-SURVEY-17 | 满足 | `survey_acquisition` 顶层恰三键，自动投影与解释行逐字冻结的 89 个名称双向一致；证据 §2 指向具名闭集回归。 |
| BC-SURVEY-18 | 满足 | `AnchorTableReachabilityTest` 对十锚点连续候选索引和 `53/209/60/74/135/248/62/128/217/0` 逐项断言，5/8 全集拒绝、10 空集。 |

**预复核关注项（非 BC finding，分级与依据留给复核角色）：**

1. `tools/run_grounding_survey.py:1502-1531` 以实际完成的 `windows` 计算
   `planned_survey_views`；被跳过的位置或未稳定视角不进分母，可把提案 §2.1(e) 的
   “达成巡览视角数 / 计划巡览视角数”抬高。
2. `tools/dist_data/bind_layout.py:1746-1764` 重算权威 witness 后不读取或比较
   `completion.json.tentative_witness`；现有测试只在 happy path 事后做相等断言，未实现
   §2.1(f)/验收条件 3 的“不等即硬错误”。
3. `tools/dist_data/build_inventory.py:417-438` 先把两侧会话表转成以 `session_id` 为键的
   dict，重复行会被覆盖，故不能保证 §2.2 第 4 条要求的表与实际枚举逐项精确相等。
4. 实现证据 §10 的 BC 指针表混用中文 `工件:`/`命令:`，不符合 COORD-009 冻结的
   `artifact:`/`cmd:` ASCII 前缀；各行仍有合法 `test:` 指针，因此本轮不记证据缺失。

## Codex review decision

Decision: **ACCEPTED_WITH_BINDING_CLARIFICATIONS**（Acceptance round 3，2026-09-03）

Rationale:

Revision 2 已闭合 AR2-1…6 的主体：逐帧 `VALID_SURVEY` 与唯一视角顺序；目标从第 0 帧 保持 +z 朝向；候选/会话/归档身份和零帧恢复；连续线段/AABB 净空；COORD-005 先于稳定 候选；attempt-2/3、组合工件 supersession 与准确的场景调整措辞。只读真数据扫描也提供了 归档规模、内存投影、绑定率、锚点覆盖与候选数，满足 COORD-008 S5。

余下问题都能在不改语言→框主张、不放宽 F1–F4、不增加 Play/API/GPU 上限的前提下唯一化： 正文把已扩展 `B'` 顶面又多加了 3 m；把 bootstrap/FrameWriter 顺序写反；诊断使用了新 scenario id，违反 COORD-005；当前 driver 又把输入读取绑死到写入 attempt；正式 config 若在通过候选后生成会逃出复核范围。BC-SURVEY-1…6 逐字覆盖这些冲突，实施者不得自行另选 解释。接受仍不授权实现、配置/ID 创建、Play、正式 S0–S5、supersession、S6、API 或 GPU。

Accepted design-document changes: `docs/phase1-single-drone-design.md` → v0.3.30，M6 加入本批
已接受但待两条用户授权的采集合同；`docs/implementation-status.md` 只登记设计门，零实现
证据。用户随后已逐字签发 §6 授权 #1；阶段 A 保真、停点与独立复核现已通过，接受角色已消费
终局 verdict（2026-09-05）。用户随后以「授权继续」签发授权 #2，账本已录；未新增 BC。

2026-09-07 执行消费：既有设计接受结论不变；阶段 D 归档/谱系核验完成，接受 `SURVEY_FLOORS_UNREACHABLE` 的机械派生。无新增 D/C/R 轮，不授予第二信封、S6 或里程碑关闭；完整理由与核验范围见 `docs/implementation-status.md`。

## COORD-010 disposition（2026-09-07）

Overall: `CLOSED_INSUFFICIENT_DATA_WITH_PROVENANCE_GAPS`。旧巡览采集目标终止；保留 SURVEY_FLOORS_UNREACHABLE（37 < 60）及来源记录缺口，不签正式 G0 verdict、UNITY_PASSED 或 DONE。第二信封不启动，原授权剩余额度不再动用。
依据：`docs/authorizations.md` 当日 COORD-010「批准 §10 A+B+C 整体落地」条目，
规则批 `R2@batch1` 已通过；本节由接受角色执行 §7 状态迁移，不新增 D/C/R 轮或 BC。
本节是当前处置入口；上方设计决定、历史执行安排及复核轮次原样保留，不再构成继续执行指令。
工程继承唯一清单见 `docs/implementation-status.md`「COORD-010 — 工程继承清单」；
来源缺口唯一收口记录见 `docs/unity-test-log.md`「COORD-010 — DATA-002 来源缺口收口」。
原图、目录、划分与归档不改写；后续加工、模型推理或训练须独立工作项及授权。
