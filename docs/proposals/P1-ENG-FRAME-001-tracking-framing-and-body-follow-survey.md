# P1-ENG-FRAME-001 — 机身跟随策略 c-组合（距离保持带 + 比例速度 + 预测提前量，阈值兜底）与系留可关闭、主线缺省关闭（D1 任务合同）

Status: ACCEPTED（D2；R3@K2 PASS_WITH_NOTES 已消费；10-04墙钟收尾落实：UNITY_PASSED，DONE/ACTIVE；按钮墙钟已追认的可能超额仍未知，R1-3 OPEN保留）
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（工程轨道 Opus 池；supervisor 派发子代理：D0 Dispatch-Id `P1-ENG-FRAME-001-D0-20260930T201238Z-dd5c`，D1 Dispatch-Id `P1-ENG-FRAME-001-D1-20260930T215248Z-634e`，D2 Dispatch-Id `P1-ENG-FRAME-001-D2-20260930T225515Z-97c9`，D2 按账本 09-30「全局 — 用户指示：本 supervisor 对话中构思派发可调用 Fable」以 Fable 子代理运行）
Created: 2026-09-30
Last updated: 2026-10-04

> **性质**：D1 完整任务合同 + D2 退修答复（U1/R1/R2；修订条款原位标注）。接受角色 D2 已裁定 **`Workflow: engineering-v1` 生效**，理由、限制与未完成证据门见文末「D2 接受裁定」。
>
> **依据**：`docs/authorizations.md` 2026-09-30「P1-ENG-FRAME-001 — 用户决定：方向选 c-组合，系留改为可关闭并缺省关闭并入 D1，两部分测试/证据归属分列」（下称「账本 09-30 决定」），用户原话："选 c-组合，系留改为可关闭并缺省关闭并入D1.合并后 FRAME-001 D1 的 diff 会同时含规划器新策略和 plant 变更，复核范围变大，D1 提案里就把两部分的测试/证据归属分开列"。同日另三条（用户意见「系留作为约束对目前这个项目没有意义」、背景补充「低空作业；系留是旧双机设定」、方向补充「不能等目标很小快丢才动」）为语境。账本授权范围：只写 D1、零消耗；高度未定（保留 25 m 缺省，离线对比 15/25 m）。
>
> **两部分**（用户要求分列，全文一致使用）：**Part T — 系留开关**（系留约束可关闭、主线缺省关闭，及关闭后的通用安全边界）；**Part P — 跟随策略**（c-组合新策略类，`ThresholdBodyPlanner` 保留为对照与兜底）。
>
> **本轮消耗**（D1、D2 同）：ID/Play/GPU/付费 API/下载均为 0；只读仓库，估算脚本放会话暂存目录、不入库；未改任何代码、配置、测试、工具或 Unity 资产。

## 1. 目的与价值

主线目标（逐字引用 `docs/project-background.md` §3）：

> 做一个闭环系统：语言指定目标，快层跟上并保持居中，换目标时能迁移并跟上新目标，丢失与歧义显式报告。VLM 是主角（接口 A：输出框 + 所在 frame_id）；快层是非变量，但必须能换目标。部署目标是 VLM 与快层跑在 Jetson Orin Nano 8GB（headless），Unity 留桌面机。项目的难点是「发现目标 → 跟上」，不是保持跟踪。验证只看四类数字：陈旧指定解析成功率随延迟、转向存活率、捕获时间与成功率按偏角/距离分桶、误锁率与显式报告比例。不作为目标：单目标稳态保持率不设资格门；不做 ReID、SAM 2 在线、更大模型、INT8、SAHI、Unity 场景改动；不为快层做研究主张；VLM 剪枝等优化只在闭环跑通且曲线证明延迟重要之后。

本项落实主线中的「跟上并保持居中」的机身侧：画面居中仍由云台负责（现状不变，附录 A F3）；机身从「云台快到限位才起停式追赶」（F1/F2）改为「按目标地面估计保持跟随距离、带外连续比例追随」，并去掉已无意义的系留约束（用户意见），代之以通用安全边界。价值：消除 attempt 2「只要在视线内就不动」的观感与系留边界卡死（F4），让后续快层/VLM 在更稳定的距离与视角下工作。**不设资格门、不为规划器做研究主张**；新增读数一律是描述量；主指标 `C_track` 与主线四类数字口径不变。

## 2. 范围与不做的事

### 2.1 Part T — 系留开关（可关闭、主线缺省关闭）

- **T1 显式开关**：场景配置 `drone` 下新增可选字段 `tether_enabled`（bool）与 `geofence_xz_m`（矩形）。**缺字段 = 系留开启（逐字等于现行行为）**，保证全部既有场景文件、冻结工件与历史证据可复现。
- **T2 主线缺省关闭（D2 修订）**：新增版本化场景 `config/scenario.untethered.json`（= `config/scenario.default.json` 逐值复制，只改 §3.1 列明的三个键），作为本项及后续新工作项的**缺省场景**。「缺省」的含义收窄为 §3.11 闭集内的**三处缺省入口**：Unity `ScenarioConfig.Load()` 无覆盖时的版本化回退、`tools/run_track_experiment.py::DEFAULT_SCENARIO`、Python 侧生效场景解析器 `controller/scenario_tether.py::effective_scenario_path`；`controller/track_loop.py` 与回放工具**没有场景缺省**、一律显式传参；`runtime/scenario_config.json` 覆盖文件**不由本项生成**（入口转缺省后无需覆盖，本项 Play 要求它不存在）；ACQ/BODY-001 冻结消费者（§3.11 第 7 行）不转。`config/scenario.default.json` **字节不动**：它的 sha 被 BODY-001 冻结工件与两个基础设施检查工具绑定（§8.3）；落点已由用户答复 §10 第 1 条选 T2（账本 09-30「用户答复 §10 四条…」），接受角色 D1 裁定 (c) 同意。
- **T3 plant**：`TetheredDronePlant` 增加 `tetherEnabled` 与围栏；关闭时不做球面钳位、`TetherSaturated` 恒 false、水平位置钳到围栏矩形（plant 侧硬围栏，作规划器侧围栏之外的第二道保险 [推断：类同常见飞控的 geofence 功能]）；开启时代码路径逐字不变。
- **T4 加载与可视**：`ScenarioConfig` 解析新字段并在关闭模式下 fail-closed 校验围栏；`TetheredScenarioBootstrap` 传入开关，关闭时不创建 `TetherLine` 缆绳可视（锚点标记保留，作 home 标记）。
- **T5 规划器侧开关**：阈值构造器在系留关闭场景下拒绝构造（冻结 BODY-001 配置假定有缆）；新策略的「锚点→机身缆绳线段 × 障碍棱柱」检查与可达圆投影只在系留开启时启用（语义属 T，代码在 P 的类中，AC 分别登记）。
- **T6 通用安全边界**（关闭后的替代）：围栏、高度、速度、加速度、机身位置避障，数值与来源见 §3.4。

### 2.2 Part P — 跟随策略（c-组合）

- **P1 新策略类** `StandoffBodyPlanner`（新模块 `controller/standoff_planner.py`，只 import `controller/body_planner.py` 的契约类型，不改该文件）：云台画面居中不变 + 机身距离保持带（设定点 d\*、带宽 w）+ 带外比例速度（k_p）+ 基于估计器速度的预测提前量（T_lead）+ 现行云台余量触发作兜底（内部组合一份未改代码的 `ThresholdBodyPlanner`）+ 活动范围边界处理与显式状态（§3.6）。契约 `body-planner-contract/v1` 不变。
- **P2 配置** `config/p1-eng-frame-001-body.json`（新 schema），估计器、标定、走廊工件与兜底参数逐字引用冻结 BODY-001 配置（path + sha）。
- **P3 离线运动学回放与参数冻结** `tools/frame_follow_replay.py`：零消耗，用真实策略类与真实估计器按预注册规则选参（§3.9）；同一工具的分析模式产出 Play 描述读数（同一套度量代码）。
- **P4 接线**：`controller/track_loop.py` 的 `--body-policy` 增 `standoff`；Play 线束沿用 BODY-001 臂 B 的 `tools/run_track_experiment.py`（NanoTrack-v2、冻结初始框）。

### 2.3 实现顺序与内部检查点

1. **Part T 先落地并回归**（AC-1…AC-10、AC-27…AC-29）：解析器（含生效场景解析器）→ `ScenarioConfig`/plant/bootstrap（含无覆盖回退改指新文件）→ 阈值构造器开关 → `config/scenario.untethered.json` → `run_track_experiment.py` 缺省常量 → focused Python + Edit Mode focused 全绿；写停点证据 §T 草稿。这是实现者**内部检查点**，不开核对/复核轮。（D2 修订：括号内新增三条 AC 与两处入口。）
2. **Part P 在其上**：策略类与单测（AC-11…AC-16）→ 回放工具与 Python plant 镜像（对 Part T 的 Edit Mode 金标准向量，AC-19）→ 按规则选参、写配置（AC-17/AC-20）→ 接线（AC-18）。
3. **合并为一个 K2 候选**（§7）：全套测试（AC-24）、范围围栏（AC-25）、分节自证（AC-26）→ `C1@K2` → `R1@K2`，复核文件按 §T / §P 分节。
4. **Unity**：`R1@K2` 通过后，接受角色按 workflow §4.5 核对 HEAD 与通过候选及操作单，用户在信封内做 1 次正式 Play（AC-21/AC-23）。

### 2.4 明确不做

不改 `controller/body_planner.py`、`config/p1-m3-body-001.json`、`config/p1-m3-body-001-corridor-prisms.json`、`config/scenario.default.json` 与其余既有场景文件；不删系留代码；不改 `controller/language_loop.py`（主线接入另定，§9.1；其旧缺省回退也不改）；不给 `controller/track_loop.py` 新增场景文件缺省、不给 `run_track_experiment.py` 新增 body 参数透传；不生成 `runtime/scenario_config.json`（D2 修订，§3.11）；不改 `P1-ENG-ACQ-001` 暂停状态、合同、操作单与冻结规划器；不新增帧/控制协议字段；不做高度/垂直策略（高度恒定于初始高度，`vy = 0`）、变焦、机身偏航策略、MPC、多边形围栏；不改 `*.unity`/prefab/材质/手工 `*.meta`；不改 `tools/check_*.py` 与工作流文件；`docs/phase1-single-drone-design.md` 由接受角色处理，Implementation 只按 D2 接受裁定同步 `PROJECT_BRIEF.md`（§9.3）；不设资格门、不做研究主张、不为快层/规划器做主张；不碰 `P1-ENG-JET-001`；零 GPU/付费 API/下载/远端。

## 3. 接口与数据契约

### 3.1 场景配置新增字段（Part T；schema 仍为 `tethered-scenario/v1`，只增可选字段）

| 键 | 类型 | 缺省（字段缺失） | 规则 |
|---|---|---|---|
| `drone.tether_enabled` | bool | `true`（逐字旧行为） | Python 对非 bool 拒绝；Unity 侧必须保证缺字段 = 开启（若 `JsonUtility` 对嵌套对象不保留字段初值 `true`，改用可判缺失的表示，以 AC-1「缺字段」夹具为准） |
| `drone.geofence_xz_m` | `{min_x, max_x, min_z, max_z}`（Unity 世界系，米） | 无围栏 | 出现即校验：有限、`min < max`、包含 home（`anchor_world_m` 的 xz）；`tether_enabled = false` 时**必填**，缺失或非法 → Unity 加载抛错拒绝开场、Python 构造拒绝 |

`config/scenario.untethered.json` 相对 `config/scenario.default.json` 的**差异键闭集**：`scenario_id` → `deterministic-loop-untethered`；`drone.tether_enabled` → `false`；`drone.geofence_xz_m` → §3.4 值。其余子树（`road_data_sha256`、`anchor_world_m`、`scene_adjustments`、`target`、`sensor`、`gimbal`、`evaluation`、其余 `drone` 键）逐值相等，使 BODY-001 走廊棱柱工件的场景基准仍适用。高度仍相对 home（= `anchor_world_m`）高度，与现行 plant 一致。

### 3.2 plant 语义（Part T）

- 开启（字段缺失或 `true`）：`Step` 与现行实现逐字相同（球面钳位、`vertical = min(vertical, tetherLength)`、`TetherSaturated` 判定）；`ScenarioConfig.Normalize` 的缆长相关高度钳位逐字相同。
- 关闭：速度钳 `maximumSpeed`、加速度 `MoveTowards` 不变；高度钳 `[minimumAltitude, maximumAltitude]`（不再被缆长截断）；水平位置越出围栏矩形即投影回矩形；`TetherSaturated` 恒 false；不创建 `TetherLine`。plant 的钳位是权威（契约 v1「规划器不得假设自己的钳位生效」照旧）。
- 围栏在开启模式下若出现也生效（两者叠加）；既有文件均无该字段，回归不受影响。

### 3.3 帧/控制协议（K1 判断，Part T）

帧包 `tethered-sensor-frame/v3` 的字段集、类型、单位、坐标系与时间语义不变；body/gimbal 命令包零字节改动。`tether_saturated` 的定义（本步 plant 是否被缆长钳位）不变，关闭模式下恒 false 是该定义在无缆模式的直接结果，不新增 `geofence_saturated` 之类帧字段（围栏状态由规划器按已发布机身位置自算并记 run log）。场景配置不属帧/控制协议。据此本角色判断**不触发 K1**；若接受角色认为「恒 false」属语义扩展，则并为 `K1K2` 单候选，AC 不变。（D2 修订）R1 的三处缺省入口改动（§3.11：Unity 无覆盖回退文件、线束常量、Python 生效场景解析器）不改帧包与命令包的任何字段、类型、单位、坐标系或时间语义；本项 Play 的帧元数据 `scenario_id` 取值 `deterministic-loop-untethered` 是该字段既有的按场景取值（SCENE-004 等历史场景已如此），不是 schema 变化。故 D2 维持 **`K2` 单候选**、不改判 `K1K2`。

### 3.4 通用安全边界与数值来源（Part T 定义；Part P 规划器侧同值执行）

| 边界 | 值 | 执行点 | 来源 |
|---|---|---|---|
| 水平围栏 | 矩形 x ∈ [110, 190]，z ∈ [50, 130]（m） | plant 硬钳 + 规划器投影 | 操作者声明的作业区：默认场景内环街区（路线外接框 [122.5, 177.5] × [62.5, 117.5]）各向外扩 12.5 m。设计期由场景地图一次确定，**运行时只读这四个数，不读目标路线**（信息公平，提请 §7 (f)）。圆形「离起飞点最大距离」被否决：路线最远点距 home 69.1 m，而 24.8–24.95 m 高楼位于 home 西侧 49.6–52.7 m（§8.2），圆无法同时覆盖路线与避开高楼 |
| 高度 | 恒定于初始高度 25 m（相对 home）；plant 钳 [8, 32] m | plant（现行）+ 规划器 `vy = 0` | 现行 `config/scenario.default.json` `drone`；低空作业（用户背景）。高度改动留用户（§10 第 2 条） |
| 速度 | ≤ 4.0 m/s | plant 钳 + 规划器 v_max | 现行 `drone.maximum_speed_mps`；BODY-001 `v_cmd_mps` |
| 加速度 | ≤ 4.0 m/s² | plant | 现行 `drone.maximum_acceleration_mps2` |
| 机身位置避障 | 机身线段（当前→候选）× 障碍棱柱，膨胀 2.1 m，0.05 m 步长缩短，无正位移即 hold | 规划器 | 棱柱 = 冻结工件 `config/p1-m3-body-001-corridor-prisms.json`（字节不变，新增第二种查询，提请 §7 (d)）；膨胀 = 机体可视臂展 1.6 m（`TetheredScenarioBootstrap.AddDroneVisual` 臂长 1.6 m）+ BODY-001 净空 0.5 m。25 m 下围栏内最高棱柱 16.93 m，余量约 8.3 m（§8.2） |
| 估计合理性 | 预测点水平距离 ≤ d_plaus = 65 m | 规划器 | 车宽 2.0 m（`TargetVisualFactory` 车身 2 × 1 × 4 m）、`fy = 415.692`、12 px 口径（`MIN_VISIBLE_SIDE_PX`）→ 斜距 69.3 m，25 m 高度下水平约 64.6 m，取 65 m |
| 命令时效 | `expires_after_s = 0.4 s` | 规划器 + 接收器 | 冻结 BODY-001 `command.expires_after_s`（2 / capture_hz） |

（D2 修订）**各行生效模式**：水平围栏 = 配置出现时（无缆模式必填；有缆模式可选，出现即与可达圆叠加）；缆长可达圆（§3.6 第 5 步 ①，半径 √(L² − h²)）= **仅有缆模式**，无缆模式不检查；锚点走廊（§3.6 第 5 步 ③）= 仅有缆模式；机身位置避障、高度、速度、加速度、估计合理性、命令时效 = 两模式相同。AC-15 按此逐模式断言。

### 3.5 阈值规划器与构造器（Part T）

`ThresholdBodyPlanner` 与 `config/p1-m3-body-001.json` 不改。`controller/track_loop.py::_build_body_runtime` 的 `threshold` 分支：场景系留开启（含字段缺失）时行为与身份字典逐字不变；系留关闭时抛 `ValueError`（`language_loop.bind_body_runtime` 已有映射为 `CONFIG_MISMATCH`，该文件不改）。共享解析器 `controller/scenario_tether.py` 负责 §3.1 规则，供构造器、新策略与回放工具共用。

### 3.6 `StandoffBodyPlanner`（Part P；`name = "standoff-band-v1"`）

输入仍是契约 v1 的 `decide(platform, estimate, now)`；内部状态 = 跟随锁存布尔 + 内嵌阈值实例的滞回布尔（固定初态，按序重放确定性复现）。每帧：

1. **契约 fail-safe**：`platform is None` → `hold_no_platform`；限位裕度不可构造 → `hold_margin_unconstructible`；`estimate is None` → `hold_no_estimate`（契约 (b)，兜底不得越过）。
2. **估计闸**：位置 2×2 协方差最大特征值开方 > w、任一分量非有限 → `hold_estimate_uncertain`；预测点水平距离 > d_plaus → `hold_estimate_implausible`。
3. **跟随分支**：v̂ = 估计速度按模长钳到 v_max；预测点 p̂ = (x, z) + T_lead·v̂；d̂ = ‖p̂ − 机身 xz‖。锁存：d̂ > d\* + w 置位，d̂ ≤ d\* 复位。置位时速度 = min(v_max, k_p·(d̂ − d\*)) 沿 (p̂ − 机身) 方向 → `follow_move`；否则 `in_band_hold`。**近侧不后退**（目标驶近或从下方穿过时只 hold，减少无谓运动）。设计注记：取 T_lead·k_p = 1 时稳态比例滞后被提前量抵消，真实跟随距离 ≈ d\*（§8.4 估算印证）。
4. **兜底**：内嵌 `ThresholdBodyPlanner`（冻结 BODY-001 `policy` 值 10°/20°/4 m/s，经 sha 校验读取；系留关闭时不传走廊棱柱）每帧调用以保持滞回；**仅当第 2/3 步结论为 hold** 且它给出速度时采用 → `fallback_margin`。覆盖「估计失效但云台已近限位」与「估计与云台指向矛盾」。
5. **安全后处理**（跟随与兜底速度一律，固定顺序；D2 修订：按模式逐项写明启用条件）：① 候选 = 机身 + v·0.4 s，**边界投影按实际启用的约束**——(a) 缆长可达圆（半径 √(L² − h²)，h = 机身相对 home 高度）**仅在系留开启时启用**，投影记 `+tether_limited`；(b) 围栏矩形**仅在场景配置出现 `geofence_xz_m` 时启用**（无缆模式必填故必启用；有缆模式可选，出现即与 (a) 叠加、先 (a) 后 (b)），投影记 `+geofence_limited`；无缆模式**不检查**可达圆、机身可越过锚点 35 m；任一投影后残余速度 < 0.05 m/s → hold 并记 `+boundary_blocked`；② 机身线段避障（§3.4）**两模式均启用**，记 `+obstacle_shortened` / `+obstacle_blocked`；③ **仅系留开启**：锚点→候选线段 × 棱柱（膨胀 1.0 m = BODY-001 走廊半径 0.5 + 净空 0.5，步长 0.05 m），记 `+corridor_shortened` / `+corridor_blocked`；无缆模式该步不执行、修饰不得出现。
6. **显式状态**：`reason` = 主标记（闭集 `follow_move`、`in_band_hold`、`fallback_margin`、`hold_no_platform`、`hold_margin_unconstructible`、`hold_no_estimate`、`hold_estimate_uncertain`、`hold_estimate_implausible`）+ 零或多个修饰（闭集，按上列顺序拼接）。`reason` 只进 run log，不上线路（契约 v1 已如此）；不新增对操作者的会话状态。

### 3.7 配置 `config/p1-eng-frame-001-body.json`（Part P；schema `p1-eng-frame-001-body/v1`）

字段：`work_id`；`planner` = `standoff-band-v1`；`selected_candidate`（C1/C2/C3）与 `params {d_star_m, band_w_m, t_lead_s, k_p_per_s}`（= AC-19 工具选出的候选）；`fixed {v_max_mps: 4.0, target_velocity_clamp_mps: 4.0, d_plaus_m: 65.0, obstacle_pad_m: 2.1, corridor_pad_m: 1.0, shorten_step_m: 0.05, min_residual_speed_mps: 0.05}`；`body_001_config {path, sha256}`（估计器先验、`sigma_px` 标定、走廊工件 path/sha、兜底 `policy`、`command.expires_after_s` 全部从这里读，逐字复用）；`replay_evidence {path, sha256}`。无 CLI 覆盖；缺字段、非有限、sha 不符、schema 不符一律拒绝。

### 3.8 接线与 Play 线束（Part P）

`track_loop --body-policy standoff --body-planner-config config/p1-eng-frame-001-body.json --body-scenario-config config/scenario.untethered.json`（三个参数**均显式、无缺省**，与现行 `threshold` 同规则）。（D2 修订）构造器另校验：body 场景与 **Python 侧生效场景**逐值相等，否则拒绝；生效场景由 `controller/scenario_tether.py::effective_scenario_path(runtime)` 解析，规则与 Unity `ScenarioConfig.Load()` 同序——`runtime/scenario_config.json` 存在即整份取它，否则取版本化缺省 `config/scenario.untethered.json`（§3.11 入口 1/6）；因此 ACQ §2.6 产物（旧缺省的覆盖副本）残留时 standoff 构造器因 `scenario_id`/`tether_enabled` 不等而拒绝，fail-closed。run manifest 的 `body_planner` 身份含 planner 名、FRAME 配置 sha、场景 sha、生效场景来源路径、选中候选。`hold`/`threshold` 路径与既有测试不变。Play 线束 = `tools/run_track_experiment.py`（BODY-001 臂 B 同款：`nanotrack-v2`、冻结初始框 `0.2765625 0.40625 0.1203125 0.15208333333333332` @ frame 0、`planned_duration_s` = 两圈 + 60 s ≈ 273 s）：操作单以其**缺省场景**（D2 后 = `config/scenario.untethered.json`，§3.11 入口 2）运行 `--print-only` 取得 `scenario_id`、`planned_duration_s` 与基础命令，再按操作单逐字追加上述三个 body 参数（线束不透传 body 参数，与 BODY-001 臂 B 操作单 §4 同法）。**不生成 `runtime/scenario_config.json`**：入口 1 转缺省后 Unity 无覆盖即加载 untethered 文件；Play 前该文件须不存在（ACQ 残留按 §9.1 移入 `runtime/hold-<标签>/`，不删除、不覆盖），Unity 日志须出现 `Loaded tethered scenario 'deterministic-loop-untethered' from <项目根>/config/scenario.untethered.json`（AC-23 T 行）；保留帧数取缺省 128。D1 原句「覆盖由 untethered 逐字复制生成」撤回。选 track_loop 而非 language_loop 的理由：隔离暂停中的 ACQ 链路、复用已复核线束与冻结初始框、零 VLM/候选收据成本（§7 (i)）。

### 3.9 离线运动学回放与预注册选参（Part P；零消耗）

- **模型**：默认路线（周长 212.97 m，2 m/s，两圈）；Python plant 镜像 `TetheredDronePlant.Step`，**按模式镜像**（D2 修订）：系留开（`config/scenario.default.json`）= 速度/加速度钳 + 缆长球面钳 + 缆长高度截断、无围栏，与 AC-2 金标准向量一致；系留关（`config/scenario.untethered.json`）= 速度/加速度钳 + 高度钳 [8, 32] + 围栏矩形投影、无球面钳，与 AC-4 金标准向量一致（均 ≤ 1e-5 m）；回放工具**没有场景缺省**，两个场景文件路径写死在预注册网格表中（§3.11 入口 8）；5 Hz 决策、0.4 s 时效；云台理想指向目标（45° 限位钳位）；框 = 红车 AABB（2.0 × 1.55 × 4.0 m，朝向沿路线）经帧元数据同一针孔模型投影；估计 = 真实 `WorldEstimateFilter`（冻结先验）。真值只在本离线工具内用于合成观测，不进入运行时路径。
- **噪声条件（预注册）**：E0 无噪声；E1 框中心加 σ_px = 2.866112 px（冻结 `calibration.sigma_px`）高斯噪声；E2 = 2σ_px 且相机姿态加 1°（冻结 `sigma_att_deg`）噪声。种子固定。
- **网格**：{C1, C2, C3, 阈值 (a), hold} × {25 m, 15 m} × {系留关（untethered）, 系留开（default）} × {E0, E1, E2}。
- **候选（预注册）**：

| 候选 | d\* (m) | w (m) | T_lead (s) | k_p (1/s) | 稳态离底角 @25 m |
|---|---|---|---|---|---|
| C1 | 6 | 3 | 2.0 | 0.5 | ≈ 13.5° |
| C2 | 9 | 3 | 2.0 | 0.5 | ≈ 19.8° |
| C3 | 12 | 4 | 2.5 | 0.4 | ≈ 25.6° |

  兜底阈值（10°/20°/4 m/s）不作候选变量：逐字复用冻结 BODY-001 值。
- **选择规则（预注册；由工具执行，不由人挑）**：只在 25 m / 系留关 / E1、第二圈（稳态）上判：H1 云台饱和时间比例 ≤ 0.5%；H2 目标短边估算像素 p10 ≥ 24 px（2.0 m 车宽）；H3 出围栏/入膨胀棱柱 0 帧，且触边/避障修饰占比 ≤ 1%；H4 起停次数（机身速度先 < 0.2 m/s 后 > 1.0 m/s 记 1 次）≤ 5 / 圈；H5 目标运动时机身静止（< 0.2 m/s）时间比例 ≤ 10%。全过者中取第二圈机身路程最短者（设计 §4.1「机身最小化运动」精神）；路程差 ≤ 3% 视为平手，依次比起停次数少、候选编号小。**全不过 → 不进 Play**，回接受角色（预注册失败模式，§6）。选定后写入配置，Play 前冻结；Play 后不得据结果改参（改参 = 新 D 轮）。
- **15 m 与系留开的读数只作描述**，不参与选择；高度是否改动留用户。

### 3.10 描述读数（共用；不设门）与对 `C_track` 的可能影响

回放与 Play 用同一套度量代码：R-1 画面中心误差 p50/p90 与 ≤ 64 px 时间比例（Play 取评估器 `target_center_error_px`，仅离线；回放由饱和角换算）；R-2 云台饱和时间比例（帧 `gimbal_saturated`）；R-3 水平跟随距离 p50/p90/max（机身取帧 `camera_position_world_m`，目标取评估器真值，仅离线）；R-4 机身路程、起停次数、静止时间比例（H4/H5 定义）；R-5 斜距与目标短边像素 p10/p50（Play 另报评估器真值框短边）；R-6 状态标记占比（`fallback_margin`、`hold_estimate_*`、边界/避障修饰）；R-7 `C_track`（评估器原样，口径不变，不与 BODY-001 臂 B 直接比较：系留与策略同时变化）；R-8 系留开/关对照（仅回放，取代 D0「按系留可达/不可达分层」）。

对 `C_track` 的可能影响 [推断，不设门]：机身持续平移使背景每帧位移约 v·Δt·fy/R ≈ 0.4 × 415.7 / 30 ≈ 5.5 px（F11 的纯旋转补偿不含平移，若日后接入 ACQ 快层须评估其关联门）；目标更近、更居中、短边约 30 px（阈值起停时 27–31 px 起伏）对跟踪器有利；稳态离底角 13–26° 比 BODY-001 臂 B 与训练帧常见的斜视更俯视，外观域偏移可能影响检测/VLM。

### 3.11 缺省入口闭集（T2 落实；D2 新增，答复 R1）

「谁、何时选择 `config/scenario.untethered.json`」逐入口列明；现状为 2026-09-30 只读核实（`ScenarioConfig.cs:142–163`、`run_track_experiment.py:19/165`、`track_loop.py:1842/1882–1901`、`language_loop.py:304–318/818/3457`）。红线：`config/scenario.default.json` 字节不动；ACQ 暂停合同、操作单（含 §2.6 由旧缺省 `sed` 生成覆盖）与冻结规划器不改；AC-2/AC-3/AC-7/AC-8 不变。

| # | 入口 | 现状 | D2 取舍与理由 | 谁、何时选择新场景 | 可改文件 / AC | 系留开启配置如何复现 |
|---|---|---|---|---|---|---|
| 1 | Unity `ScenarioConfig.Load()` | `runtime/scenario_config.json` 存在→整份用；否则 `config/scenario.default.json`；两者都缺→内置 `CreateDefault()` | **(i) 转**：无覆盖时的版本化回退改指 `config/scenario.untethered.json`；覆盖优先分支与内置回退逐字不变。理由：plant 是系留物理所在，用户「缺省关闭」若只靠操作单生成覆盖则 Unity 直接 Play 仍有缆，与决定不符；改动为一处路径字符串，文件已在 §4.1 集内 | Unity 启动时 `Load()` 自动选择；操作者只须保证覆盖文件不存在（§3.8） | M `ScenarioConfig.cs`（已在集）/ AC-27；AC-3 守旧文件 | 生成覆盖（ACQ §2.6 路径不变，覆盖优先）或显式加载旧文件（AC-3 逐位回归）；无覆盖时 Unity 日志 source_path 可核对 |
| 2 | `tools/run_track_experiment.py::DEFAULT_SCENARIO` | 指旧缺省；只用于 `scenario_id`、两圈时长与命令打印，不透传 body 参数 | **(i) 转**：常量改指新文件。理由：这是 T2 所称「CLI 缺省」的唯一实体；一行改动 + 测试，旧文件经显式参数逐字可达 | 操作者按操作单不传 `--scenario-config` 运行 `--print-only`（§3.8） | M `tools/run_track_experiment.py`、M `tests/test_track_experiment.py`（D2 新增入 §4.1）/ AC-28 | 显式 `--scenario-config config/scenario.default.json`，输出 JSON 与改动前逐字相等（AC-28 红绿） |
| 3 | `controller/track_loop.py` CLI | 无场景文件缺省：`--scenario-id` 必填；`--body-scenario-config` 随 `--body-policy` 必填、无 `default` | **(ii) 不转**（无缺省可转，也不新增缺省，保持显式 fail-closed）。理由：与现行 `threshold` 规则一致；缺省会让 body 场景与生效场景的一致性校验失去意义 | 操作者在命令行逐字给 `--scenario-id deterministic-loop-untethered --body-scenario-config config/scenario.untethered.json`；构造器按 §3.8 校验，不等即拒绝 | M `track_loop.py`（已在集）/ AC-18（D2 修订） | `--body-policy threshold` + 旧文件路径逐字回归（AC-8） |
| 4 | `runtime/scenario_config.json` 覆盖生成 | 仓库内无生成工具；只由操作单生成（ACQ §2.6 自旧缺省 `sed`；LOOP-001 `operator.sh` 已收口） | **(ii) 不生成**：入口 1 转缺省后无需覆盖；本项 Play 要求该文件不存在。理由：覆盖是整份副本，是与版本化文件漂移的来源；ACQ 残留副本又恰是系留开启配置 | 接受角色 Play 核对（workflow §4.5）确认文件不存在、ACQ 残留已按 §9.1 移入 hold | N `play-ops.md`（已在集）/ AC-20、AC-23 | ACQ §2.6 路径不受影响：其覆盖仍是系留开启配置，Unity 覆盖优先 |
| 5 | Play 操作单 `docs/evidence/P1-ENG-FRAME-001-play-ops.md` | 新文件 | **(i)**：逐字给出完整 track_loop 命令（入口 2 打印 + 三个 body 参数）、覆盖文件缺席核对、Unity 日志 source_path 核对、ACQ 残留 hold 步骤 | 操作者 Play 前执行；接受角色核对 | N `play-ops.md`（已在集）/ AC-20（D2 修订） | — |
| 6 | Python 侧生效场景解析（standoff 构造器、回放 `--analyze-run`） | 现行 `language_loop.effective_scenario_document` 回退旧缺省（文件冻结不改，AC-18） | **(i) 新增** `controller/scenario_tether.py::effective_scenario_path(runtime)`，与 Unity 同序（覆盖→`config/scenario.untethered.json`）。理由：standoff 一致性校验必须与 Unity 实际加载的文件比对 | standoff 构造时自动 | N `scenario_tether.py`（已在集）/ AC-29 | `language_loop` 回退不变；无覆盖时其与 Unity 回退不一致，由帧元数据 `scenario_id` 绑定 fail-closed（§9.1） |
| 7 | 不转的既有消费者 | `controller/language_loop.py`（3 处旧缺省）、`tools/eng_acq/candidates_preflight.py`、`tools/check_anchor_placement.py`、`tools/check_scene_body_margin.py`、`tools/build_m3_corridor.py`、`tools/analyze_m3_body.py`、`tools/dist_data/roots.py`、Edit Mode 审计测试（直接读旧文件） | **(ii) 不转**，字节不变。理由：ACQ 冻结、基础设施工具、BODY-001 冻结证据链（§8.3） | — | AC-7 / AC-18 / AC-25 守门 | 它们读的就是旧文件本身 |
| 8 | 回放工具 `tools/frame_follow_replay.py` | 新文件 | **无缺省**：网格两个场景路径写死（§3.9）；`--analyze-run` 读 run manifest 的场景 sha 与来源路径 | 工具内预注册 | N（已在集）/ AC-19 | 网格「系留开」格即旧文件 |

**后果如实披露**：入口 1 转缺省后，凡依赖「覆盖缺席 = 系留开启缺省」的**历史**操作单（BODY-001 1c/臂 A/B 的 `runtime/scenario_config.json` 缺席核对项）在本项落地后的 main 上不再成立；这些工作项已关闭、不重跑，旧证据按当时规则解读（§9.2）。唯一暂停中的 `P1-ENG-ACQ-001` 走覆盖路径（§2.6），不受影响；恢复方式由用户另定（§10 第 3 条）。

## 4. 验收项（AC 表）

| 编号 | Part | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|---|
| AC-1 | T | Unity `ScenarioConfig` 与 Python `controller/scenario_tether.py` 对同一闭集夹具（缺字段；`true`；`true`+合法围栏；`false`+合法围栏；`false`+缺围栏；`false`+围栏倒置；`false`+围栏不含 home）给出相同裁决：缺字段 = 开启；`false` 缺/非法围栏 → Unity 加载抛错、Python 拒绝；Python 对非 bool 取值拒绝。任一夹具裁决不一致即不满足 | test: `tests/test_frame_tether_switch.py`；test: Edit Mode `ScenarioTetherSwitchTests` | K2 | |
| AC-2 | T | 系留开启逐字回归（plant）：字段缺失或 `true`、无围栏时，`Step` 对预注册指令序列（既有两例 + ≥ 3 条覆盖加速、向外饱和、高度上下限、斜向滑移、≥ 1,000 步种子随机序列）输出的位置、`AppliedVelocity`、`TetherSaturated` 与测试内逐字保留的改动前 `Step` 参考副本逐位相等；复核按基线 diff 核对参考副本逐字等于改动前代码 | test: Edit Mode `TetheredDronePlantTests`（新增回归用例） | K2 | |
| AC-3 | T | 系留开启逐字回归（加载）：全部既有 `config/scenario*.json`（证据逐一列名，不含新增 untethered）经 `Normalize` 后 `drone`/`gimbal`/`sensor` 值与改动前逐位相等；这些文件字节不变 | test: Edit Mode `ScenarioTetherSwitchTests`；cmd: `git diff --exit-code <K2 基线> -- 'config/scenario*.json' ':!config/scenario.untethered.json'`（基线运行时解析） | K2 | |
| AC-4 | T | 系留关闭 plant：可越过锚点 35 m；`TetherSaturated` 全程 false；高度钳 [8, 32] 不被缆长截断；速度/加速度钳不变；水平位置恒在围栏内（越界投影）。每条红绿 | test: Edit Mode `TetheredDronePlantTests`（关闭模式用例） | K2 | |
| AC-5 | T | 关闭时不创建 `TetherLine`；开启时创建且参数逐字不变；`TetherAnchor` 两模式都保留，`OcclusionGeometry.Build` 入参不变 | test: Edit Mode（bootstrap 构造用例） | K2 | |
| AC-6 | T | 帧协议不变：`SensorFrameWriter` 元数据字段集、类型、单位不变；body/gimbal 命令包零字节改动；关闭模式 `tether_saturated` 恒 false | test: Edit Mode 元数据字段集断言；cmd: `git diff <K2 基线> -- controller/protocol.py controller/body_entry.py controller/gimbal_entry.py` 为空 | K2 | |
| AC-7 | T | 冻结资产不动：`controller/body_planner.py`、`config/p1-m3-body-001.json`、`config/p1-m3-body-001-corridor-prisms.json`、`config/scenario.default.json` 字节不变；`tools/build_m3_corridor.py --check` 通过；`tests.test_m3_body_tools`、`tests.test_m3_body_policy` 通过 | cmd: `git diff --exit-code <K2 基线> -- controller/body_planner.py config/p1-m3-body-001.json config/p1-m3-body-001-corridor-prisms.json config/scenario.default.json`；cmd: `python3 tools/build_m3_corridor.py --check`；test: `tests.test_m3_body_tools`、`tests.test_m3_body_policy` | K2 | |
| AC-8 | T | 阈值构造器开关：系留开启场景下 `_build_body_runtime(..., "threshold")` 的身份字典与对同一输入序列的决策与改动前逐条相等；系留关闭场景下抛 `ValueError`；`hold` 不受影响 | test: `tests/test_frame_tether_switch.py`（构造器用例） | K2 | |
| AC-9 | T | `config/scenario.untethered.json` 相对 `config/scenario.default.json` 只有 §3.1 差异键闭集，其余子树逐值相等 | test: `tests/test_frame_tether_switch.py`（差异闭集用例） | K2 | |
| AC-10 | T | 安全边界生效值与 §3.4 表逐值相等并写入 run manifest 身份；离线核对「围栏矩形内障碍棱柱顶高最大值 + 膨胀 < 25 m 机身世界高度」（15 m 档如实报告冲突棱柱）。（D2 修订）本条针对 `config/scenario.untethered.json`；对系留开启场景，manifest 身份记 `tether_enabled = true`、可达圆半径 √(L² − h₀²)、无围栏，不断言围栏值 | test: `tests/test_frame_tether_switch.py`；artifact: `docs/evidence/P1-ENG-FRAME-001-replay.json`「safety_bounds」 | K2 | |
| AC-11 | P | `StandoffBodyPlanner` 实现契约 v1：`decide` 纯（无 I/O、墙钟、真值）、按序重放经新实例逐条复现；§3.6 第 1 步三种 hold；有限输入不抛异常；`vy = 0`；`expires_after_s` = 0.4 s；模块只 import 契约类型 | test: `tests/test_standoff_planner.py` | K2 | |
| AC-12 | P | 距离保持带：锁存阈值 d\*+w / d\*、比例速度与 v_max 钳、提前量与目标速度钳、近侧不后退；合成状态红绿（远、近、带内、转角、速度超限） | test: `tests/test_standoff_planner.py` | K2 | |
| AC-13 | P | 估计闸：σ > w、非有限、d̂ > d_plaus 各有红绿用例，主标记分别为 `hold_estimate_uncertain` / `hold_estimate_implausible` | test: `tests/test_standoff_planner.py` | K2 | |
| AC-14 | P | 兜底：内嵌阈值实例每帧调用；仅在跟随分支为 hold 时采用其速度（`fallback_margin`），方向与速度与独立 `ThresholdBodyPlanner` 同输入输出相等；`estimate is None` 时不越过契约 hold；（D2 修订，两模式分写）系留关闭时内嵌实例**无**走廊棱柱、其输出不得带 `+corridor_*`；系留开启时内嵌实例带冻结 BODY-001 走廊棱柱与半径 0.5 m，其输出与独立 `ThresholdBodyPlanner(corridor_prisms=…)` 同输入逐字相等 | test: `tests/test_standoff_planner.py` | K2 | |
| AC-15 | P | （D2 修订，答复 R2）安全后处理（§3.6 第 5 步）顺序与记号正确，**按实际启用的约束逐模式断言**。三个种子固定夹具：F-on = `config/scenario.default.json` 几何（锚点 (132, 0.2, 117)、L = 35 m、无围栏），≥ 10,000 个随机状态，机身 xz 在以锚点为心 0–60 m 圆盘采样（含可达圆外）、高度 8–32 m、估计点 0–80 m 环内；F-off = `config/scenario.untethered.json` 几何（围栏 [110, 190] × [50, 130]、无缆），≥ 10,000 个状态，机身 xz 在围栏各向外扩 20 m 的矩形采样（含围栏外与距锚点 > 35 m）；F-both = 合成场景（默认几何 + `tether_enabled = true` + §3.4 围栏，仅证叠加），≥ 1,000 个状态。对每个速度输出取候选 = 机身 + v·0.4 s：(a) F-on：候选与锚点水平距离 ≤ √(L² − h²) + 1e-6；`+geofence_limited` 出现 0 次；锚点→候选线段与膨胀 1.0 m 棱柱相交 0 次；(b) F-off：候选在围栏闭矩形内；`+tether_limited` 与 `+corridor_*` 出现 0 次；**且至少 100 个输出候选与锚点水平距离 > √(L² − h²)**（证明可达圆未启用；不足 100 即夹具无效、本条不满足）；(c) F-both：(a) 的可达圆与走廊断言、(b) 的围栏断言同时成立，`+tether_limited`/`+geofence_limited` 均可出现；(d) 三夹具：机身→候选线段与膨胀 2.1 m 棱柱相交 0 次，或输出为 hold 且带 `+obstacle_blocked`；(e) hold 输出不作候选断言，但各主标记与修饰计数写入测试输出。任一断言失败即不满足 | test: `tests.test_standoff_planner.SafetyPostprocessPropertyTests.test_tethered_reach_circle_and_corridor`；test: `tests.test_standoff_planner.SafetyPostprocessPropertyTests.test_untethered_fence_without_reach_circle`；test: `tests.test_standoff_planner.SafetyPostprocessPropertyTests.test_fence_stacks_on_tether`；test: `tests.test_standoff_planner.SafetyPostprocessPropertyTests.test_obstacle_clearance_all_fixtures`（方法名为合同名，实现逐字采用） | K2 | |
| AC-16 | P | 所有输出 `reason` 属 §3.6 第 6 步闭集且修饰顺序固定；闭集外即不满足 | test: `tests/test_standoff_planner.py` | K2 | |
| AC-17 | P | FRAME 配置含 §3.7 全部字段；引用 BODY-001 配置 path + sha 并逐字复用其估计器/标定/走廊/兜底/时效；篡改（sha、缺字段、非有限、schema）即拒绝；无 CLI 参数覆盖 | test: `tests/test_standoff_planner.py`（配置加载用例） | K2 | |
| AC-18 | P | `--body-policy standoff` 接线与 §3.8 校验（场景一致、身份字段）；`hold`/`threshold` 既有测试不变；`controller/language_loop.py` 字节不变。（D2 修订）三个 body 参数均无 `default`，缺任一即 `parser.error`；一致性校验用 AC-29 的生效场景解析器：红绿用例 = 无覆盖 + body 场景 untethered → 通过；覆盖为旧缺省副本（ACQ §2.6 产物）+ body 场景 untethered → 拒绝；无覆盖 + body 场景旧缺省 → 拒绝 | test: `tests/test_track_loop.py`（standoff 接线用例）；cmd: `git diff --exit-code <K2 基线> -- controller/language_loop.py` | K2 | |
| AC-19 | P | 回放工具按 §3.9 跑满网格；（D2 修订）Python plant 镜像**按模式**与金标准向量一致（≤ 1e-5 m）：系留开镜像对 AC-2 向量、系留关镜像对 AC-4 向量；同一种子重跑输出逐字节相同；按预注册规则选参并写证据 | test: `tests/test_frame_follow_replay.py`；artifact: `docs/evidence/P1-ENG-FRAME-001-replay.json`、`docs/evidence/P1-ENG-FRAME-001-replay.md` | K2 | |
| AC-20 | P | 参数冻结先于 Play：K2 候选中 FRAME 配置 `params` 与 `selected_candidate` = 回放证据的选中项（测试读取证据比对）；配置记回放证据 sha；Play 操作单按运行时解析引用配置 sha。（D2 修订）操作单另含 §3.11 入口清单：入口 2 `--print-only` 命令与追加的三个 body 参数逐字、`runtime/scenario_config.json` 缺席核对与 ACQ 残留 hold 步骤（§9.1）、Unity 日志 source_path 核对句 | test: `tests/test_frame_follow_replay.py`（冻结一致用例）；artifact: `docs/evidence/P1-ENG-FRAME-001-play-ops.md` | K2 | |
| AC-21 | P（Unity） | 信封内 1 次正式 Play 在 untethered 场景完成两圈；`tools/frame_follow_replay.py --analyze-run` 以同一度量代码产出 §3.10 R-1…R-7（不设门）；用户目检（机身是否持续跟随、有无起停）入 Unity 日志 | artifact: `docs/evidence/P1-ENG-FRAME-001-play.md`；artifact: `docs/unity-test-log.md` `UT-P1-ENG-FRAME-001-D1` | Unity | |
| AC-22 | 共用 | 真值隔离：新增/改动的运行时模块不读评估器输出、`metrics.json`、`m3_body_truth.jsonl` 或路线真值；回放工具的真值只用于离线合成与离线读数 | test: `tests/test_standoff_planner.py`（导入/读取面静态断言）；cmd: `grep -nE 'metrics.json|m3_body_truth|route_world_m' controller/standoff_planner.py controller/scenario_tether.py` 无命中 | K2 | |
| AC-23 | 共用（T：plant 钳；P：命令） | 同一 Play 的已发布平台量：机身水平位置全程在围栏内（T）；高度恒定于初始高度 ± 0.05 m（T）；`tether_saturated` 全帧 false（T）；命令速度 ≤ 4.0 m/s、`vy = 0`（P）；修饰计数如实报告（P）。（D2 修订）Play 为无缆模式：**不断言** 35 m 可达圆，机身越过锚点 35 m 的帧数如实报告（T）；Play 期间 `runtime/scenario_config.json` 不存在、Unity 日志含 `Loaded tethered scenario 'deterministic-loop-untethered' from …/config/scenario.untethered.json`、帧元数据 `scenario_id = deterministic-loop-untethered`（T，§3.11 入口 1/4） | artifact: `docs/evidence/P1-ENG-FRAME-001-play.md`「安全读数」§T / §P | Unity | |
| AC-24 | 共用 | 停点全套 Python 一次（基线已有失败与本批新增失败分列）+ Unity Edit Mode 全套 batchmode 一次 | cmd: `python3 -m unittest discover -s tests > docs/evidence/P1-ENG-FRAME-001-tests.log 2>&1; tail -n 3 docs/evidence/P1-ENG-FRAME-001-tests.log`；artifact: Edit Mode XML 路径记入 `docs/evidence/P1-ENG-FRAME-001-K2-handoff.md` | K2 | |
| AC-25 | 共用 | 范围围栏：候选 diff 文件集 ⊆ §4.1 归属表；`PROJECT_BRIEF.md` 只按 D2 接受裁定末段同步 §9.3 第 9 项，不扩大合同；不含 `*.unity`、prefab、手工 `*.meta`（新 C# 文件的 `.meta` 仅由 Unity 生成并逐个列名）、`controller/language_loop.py`、ACQ 文件、`tools/check_*.py`、工作流文件 | cmd: `git diff --name-only <K2 基线>..<候选>` 与归属表比对 | K2 | |
| AC-26 | 共用 | 停点证据 `docs/evidence/P1-ENG-FRAME-001-K2-handoff.md` 分 §T（AC-1…10、AC-27…29）与 §P（AC-11…20）两个具名小节逐条自证，AC-22/24/25 列于 §共用；交接行只写指针（D2 修订：§T 括号内加 AC-27…29） | artifact: `docs/evidence/P1-ENG-FRAME-001-K2-handoff.md` | K2 | |
| AC-27 | T（D2 新增） | Unity 缺省入口（§3.11 入口 1）：`ScenarioConfig` 暴露只读成员给出无覆盖时的版本化回退路径，测试断言其以 `config/scenario.untethered.json` 结尾且文件存在；`Load()` 的覆盖优先分支（`File.Exists(runtimeOverride) ? runtimeOverride : projectDefault`）与内置 `CreateDefault()` 回退逐字不变（复核按 diff 核对）；测试不调用 `Load()`（不触碰共享 `runtime/`），改以 `FromJsonStrict` + `Normalize` 读两个文件断言：新文件 → `scenario_id = deterministic-loop-untethered`、`tether_enabled = false`、围栏 = §3.4 值；旧文件 → 与改动前逐位相等（AC-3 闭集之一） | test: Edit Mode `ScenarioTetherSwitchTests`（缺省入口用例） | K2 | |
| AC-28 | T（D2 新增） | 线束缺省入口（§3.11 入口 2）：`tools/run_track_experiment.py::DEFAULT_SCENARIO` 指 `config/scenario.untethered.json`；不传 `--scenario-config` 的 `--print-only` 输出 `scenario_id = deterministic-loop-untethered`、`scenario_config_sha256` = 该文件运行时 sha、`planned_duration_s` 与旧缺省相等（同路线）；显式 `--scenario-config config/scenario.default.json` 的输出 JSON 与改动前逐字相等（`scenario_id = deterministic-loop-default`、sha = 旧文件运行时 sha、同一命令 token 序列）；线束不新增 body 参数透传；`tests/test_track_experiment.py` 既有用例不变 | test: `tests/test_track_experiment.py`（缺省入口与旧缺省回归用例） | K2 | |
| AC-29 | T（D2 新增） | Python 生效场景解析器（§3.11 入口 6）：`controller/scenario_tether.py::effective_scenario_path(runtime)` 在 `runtime/scenario_config.json` 存在时返回它、否则返回 `config/scenario.untethered.json`，与 Unity `Load()` 同序；返回值连同 sha 写入 run manifest 身份；不读取、不改动 `controller/language_loop.py::effective_scenario_document`（其旧缺省回退保持，AC-18） | test: `tests/test_frame_tether_switch.py`（解析器红绿：有覆盖/无覆盖两用例） | K2 | |

### 4.1 归属表（Part × 文件路径 × AC × 测试/证据；复核按 Part 分开核对范围）

| Part | 文件路径（新增 N / 修改 M） | AC | 测试 / 证据 |
|---|---|---|---|
| T | M `Assets/TetheredTracking/Scripts/ScenarioConfig.cs`（含无覆盖回退路径改指新文件，D2） | AC-1, AC-3, AC-27 | Edit Mode `ScenarioTetherSwitchTests` |
| T | M `Assets/TetheredTracking/Scripts/TetheredDronePlant.cs` | AC-2, AC-4 | Edit Mode `TetheredDronePlantTests` |
| T | M `Assets/TetheredTracking/Scripts/TetheredScenarioBootstrap.cs` | AC-5 | Edit Mode bootstrap 用例 |
| T | M `Assets/TetheredTracking/Tests/EditMode/TetheredTrackingEditModeTests.cs`（或 N 同目录新测试文件 + Unity 生成 `.meta`） | AC-1…AC-6 | Edit Mode XML |
| T | N `controller/scenario_tether.py`（含 `effective_scenario_path`，D2） | AC-1, AC-8, AC-10, AC-29 | `tests/test_frame_tether_switch.py` |
| T | M `controller/track_loop.py`（仅 `_build_body_runtime` 的 `threshold` 分支开关） | AC-8 | `tests/test_frame_tether_switch.py` |
| T | N `config/scenario.untethered.json` | AC-9, AC-10 | `tests/test_frame_tether_switch.py` |
| T | M `tools/run_track_experiment.py`（仅 `DEFAULT_SCENARIO` 常量，D2 新增入集）；M `tests/test_track_experiment.py`（新增用例，D2 新增入集） | AC-28 | `tests/test_track_experiment.py` |
| T | N `tests/test_frame_tether_switch.py` | AC-1, AC-8, AC-9, AC-10, AC-29 | 测试日志 |
| T | 不变（守门） `controller/body_planner.py`、`config/p1-m3-body-001*.json`、`config/scenario.default.json` 等既有场景、`controller/protocol.py`、`controller/body_entry.py`、`controller/gimbal_entry.py` | AC-3, AC-6, AC-7 | `git diff` 空 |
| P | N `controller/standoff_planner.py` | AC-11…AC-17 | `tests/test_standoff_planner.py` |
| P | N `config/p1-eng-frame-001-body.json` | AC-17, AC-20 | 同上；回放证据 |
| P | M `controller/track_loop.py`（`--body-policy standoff` 与构造分派） | AC-18 | `tests/test_track_loop.py` |
| P | N `tools/frame_follow_replay.py` | AC-19, AC-20, AC-21 | `tests/test_frame_follow_replay.py`；`docs/evidence/P1-ENG-FRAME-001-replay.{json,md}` |
| P | N `tests/test_standoff_planner.py`、`tests/test_frame_follow_replay.py`；M `tests/test_track_loop.py`（新增用例） | AC-11…AC-20 | 测试日志 |
| P | N `docs/evidence/P1-ENG-FRAME-001-play-ops.md`、`docs/evidence/P1-ENG-FRAME-001-play.md` | AC-20, AC-21, AC-23 | Unity 日志 |
| 共用 | N `docs/evidence/P1-ENG-FRAME-001-K2-handoff.md`、`docs/evidence/P1-ENG-FRAME-001-tests.log` | AC-22, AC-24…AC-26 | — |
| 共用 | M `PROJECT_BRIEF.md`（仅 §9.3 第 9 项；D2 接受裁定限定措辞） | AC-25, AC-26 | `C1@K2` 文档一致性核对 |

`controller/track_loop.py` 是唯一两部分共改的文件：T 只动 `threshold` 分支开关，P 只动 CLI 选项与 `standoff` 分派；复核按函数/段落分归 §T / §P。（D2）`tools/run_track_experiment.py` 只由 T 改一个常量，P 沿用不改。

## 5. 预算信封

下表为构思 D1 的**申请值**，不是授权来源。用户已在 `docs/authorizations.md` 2026-09-30「P1-ENG-FRAME-001 — 用户答复 §10 四条：缺省关闭落点取 T2、高度保留 25 m、ACQ-001 恢复时再定，并按申请签发 §5 预算信封」逐字签发；本任务合同实际执行额度以下方「已签执行合同」为准，不由申请表自行签发或扩额。

| 项目 | 实现至 K2 候选 | Unity 证据（AC-21/AC-23） |
|---|---|---|
| Consuming | no（若接受角色认定新建 scenario_id 属消耗，则实现交接为 yes，§7 (h)） | yes |
| scenario ID | 新建 1 个：`deterministic-loop-untethered`（随 `config/scenario.untethered.json` 创建） | 0（复用） |
| session ID | 0 | 0 |
| run ID | 0 | ≤ 2（正式 1 + 环境性失败重试 1；作废 ID 保留、不复用） |
| Unity Play | 0 | ≤ 2 次，单次墙钟 ≤ 330 s（线束 `planned_duration_s` ≈ 273 s）；重试只限首个机身命令之前的环境性失败（初始化失败、崩溃、配置拒绝），两次之间不得改参数或代码 |
| Unity Edit Mode（batchmode） | 自动测试，非 Play、零 ID，不计入信封（接受角色可另设上限） | — |
| 权重加载 | 0 | NanoTrack-v2 每次尝试 1 次（≤ 2）；YOLO/VLM 0 |
| GPU·h / 付费 API / VLM 查询 | 0 | 0 |
| 下载 / pip 安装 / 远端（5060、Jetson） | 0 | 0（模型文件本机已有，§8.1） |
| 本地磁盘 | 代码、测试、证据；回放为本机 CPU 分钟级 | run 目录 + 缺省 128 保留帧，约 10 MB 量级 |

### 已签执行合同（D2 接受转写；授权来源为上述账本条目）

| 维度 | 实现至 `K2` 候选 | Unity 证据（AC-21/AC-23；仅 `R1@K2` 通过且接受角色按 workflow §4.5 放行后） |
|---|---|---|
| Consuming | **yes**：创建 scenario ID 占唯一消耗性轨道（D1 裁定 (h)） | yes |
| scenario ID | 新建 1 个 `deterministic-loop-untethered` | 0，新 ID 不得创建，复用前段 |
| session ID / run ID | 0 / 0 | 0 / ≤ 2（正式 1 + 环境性失败重试 1；作废 ID 不复用） |
| Unity Play | 0 | ≤ 2 次，每次墙钟 ≤ 330 s；仅首个机身命令之前的环境性失败（初始化失败、崩溃、配置拒绝）可重试，且两次之间代码和参数不变 |
| 权重加载 | 0 | NanoTrack-v2 每次尝试 1 次、总计 ≤ 2；YOLO/VLM 0 |
| GPU·h / 付费 API / VLM 查询 | 0 / 0 / 0 | 0 / 0 / 0 |
| 下载 / pip 安装 / 远端（5060、Jetson） | 0 / 0 / 0 | 0 / 0 / 0 |

成功、失败与重试同计上述上限，任何越界回用户。Unity Edit Mode 是自动测试、非 Play、零 ID；本地磁盘是估算，二者均非可转用的信封额度。执行信封子额度块未签，不启用。

## 6. 限制、不承诺与失败模式

- **不承诺**：任何 `C_track` 改善、保持率、主线四类数字变化或 Jetson 结论；回放是运动学 + 合成观测，不含渲染、检测与跟踪器失败，只支持「策略在几何上的行为」陈述。
- **估计器先验未标定**（附录 A F10）：回放 E1/E2 的噪声只是预注册扰动，不代表在线真实噪声；Play 中估计闸与兜底的占比如实报告。
- **预注册失败模式**：(i) 回放全不过 H1–H5 → 不进 Play，回接受角色；(ii) Play 中 `fallback_margin` 或 `hold_estimate_*` 占比高 → 如实报告，不改参；(iii) 触边/避障修饰出现 → 如实报告，AC-23 只要求位置不越界；(iv) NanoTrack 在第 0 帧初始化失败 → 计环境性失败，按信封重试一次，仍失败回接受角色；(v) 系留开启回归（AC-2/AC-3/AC-8）任一不等 → Part T 不成立，返工。
- **系留开启模式下新策略**：可达域仍是 35 m 缆长球，约四成路线云台必然饱和（§8.4），读数只作 R-8 对照，不是本项目标。
- 高度保持 25 m；15 m 读数只作描述。

## 7. 必经停点与提请裁定

- **`K2` 单候选**（engineering §4「相互关联的触发可合并」）：Part T = 安全约束（系留工作空间 → 围栏/避障，plant 钳位）；Part P = 控制命令生成（新策略、兜底、安全后处理）。一次 `C1@K2` → 新鲜上下文 `R1@K2`；核对表与复核文件按 **§T / §P / §共用** 分节，finding 标所属 Part，返工只回对应 Part 的文件；每停点计数照旧（核对轮 ≤ 1 次退回，`REWORK_REQUIRED` ≤ 2）。不采用「T、P 各一次 K2」：同名停点两轮会共用计数，且用户已预期合并 diff。
- **K1**：按 §3.3 判断不触发；接受角色若不同意，改为 `K1K2` 单候选，AC 不变。（D2）R1 的缺省入口改动不触及协议语义（§3.3 末段），本角色不改判 `K1K2`，维持 `K2`。**K3** 不触发（机身策略不涉模型决策、目标身份与重播种）。**K4** 不触发（R-1…R-8 为内部描述读数，不新增划分、标签或对外指标；若日后对外发布再按 K4/K5 另议）。**K5** 不触发。
- **不申请 `UNITY_NA`**：两部分都改变运行时行为。`R1@K2` 通过后 Overall 最高记 `IMPLEMENTED_REVIEWED_AWAITING_UNITY`；`DONE` 须 AC-21/AC-23 的 Unity 证据与接受角色收口。系留开启路径不另做 Play，其 Unity 侧证据为 AC-2/AC-3 的 Edit Mode 逐位回归（提请 (g)）。
- **提请接受角色在 `ACCEPTED` 时裁定**：(a) `Workflow: engineering-v1` 申请；(b) 停点 `K2`（或 `K1K2`）；(c) 「缺省关闭」按 T2 落点（新版本化缺省场景、`config/scenario.default.json` 字节不动），以用户对 §10 第 1 条的答复为准；(d) 冻结走廊棱柱工件新增「机身线段避障」第二种查询（工件字节与 BODY-001 契约不变，本项合同内登记新用途）；(e) 场景 schema 保持 `tethered-scenario/v1`、只增可选字段；(f) 围栏矩形作为操作者声明作业区的信息公平读法（设计期定值、运行时不读路线）；(g) 系留开启回归以 Edit Mode 逐位回归作为 Unity 侧证据；(h) 新建 scenario_id 是否计消耗（决定实现交接 `Consuming` 列）；(i) Play 线束用 track_loop（BODY-001 臂 B 同款）而非 language_loop；(j) §9.3 设计基线改写清单在接受时处理。
- **推进方式**：轮次由 supervisor 派发；§5 信封首签、Play 与 §10 各项归用户。

## 8. 只读试读与试运行数字（2026-09-30 本会话只读；估算脚本在会话暂存目录，不入库；**全部为估算，权威数字以 AC-19 工具为准**）

### 8.1 路线、目标与资源

- 默认路线周长 212.97 m（一圈 106.5 s @ 2 m/s），路线点距 home（锚点 xz）最远 69.1 m；锚点 (132, 0.2, 117)。
- 红车 2.0 × 1.55 × 4.0 m（`TargetVisualFactory` 车身 2 × 1 × 4 m + 车顶 1.7 × 0.7 × 2 m @ y 1.2）；短边像素 ≈ 831 / 斜距（fy 415.692），12 px ↔ 斜距约 69 m（修正附录 A F7 的 1.8 m 估计）。
- 机体可视臂展 1.6 m；NanoTrack-v2 模型文件本机 `runtime/models/nanotrack-v2/` 已有（backbone/head onnx）。

### 8.2 障碍与围栏（冻结棱柱工件 779 个实例只读统计）

- 围栏矩形 [110, 190] × [50, 130] 内相交棱柱 70 个，顶高最大 16.93 m（`Building Sky_small_color03`，仅在 x 110.0–111.3 边缘相交），其次场地中央体育馆 11.69 m。25 m 机身（世界高 25.2 m）余量约 8.3 m；15 m 机身（世界高 15.2 m）低于 16.93 m，避障检查会在围栏西缘生效，对体育馆余量 3.5 m（> 膨胀 2.1 m）。
- home 西侧 49.6–52.7 m 有 24.8–24.95 m 高楼与楼顶停机坪（x ≤ 97），位于围栏外；这是否决「以 home 为心的圆形围栏」的原因（需 ≥ 69 m 半径才覆盖路线）。

### 8.3 为什么不改 `config/scenario.default.json` 字节（Part T 爆炸半径实测）

其 sha 被以下对象按字节绑定：冻结工件 `config/p1-m3-body-001-corridor-prisms.json`（`source_scenario_sha256`，而该工件 sha 又钉在冻结配置 `config/p1-m3-body-001.json`）；证据 `docs/evidence/P1-M3-BODY-001-{scene-geometry,anchor-audit,scene-body-margin}.json`；校验工具 `tools/build_m3_corridor.py`、`tools/check_anchor_placement.py`、`tools/check_scene_body_margin.py`（后两者属 `tools/check_*.py` 基础设施，任何角色不可改）；测试 `tests/test_m3_body_tools.py`（如 `test_checked_in_corridor_artifact_is_reproducible`）；`tools/dist_data/roots.py` 的 `SCENARIO_BYTE_PROVIDERS` 按 sha 匹配历史帧的场景字节；另有 LOOP-001/SCENE-006 等 30 余份证据文件记录该 sha。改字节会使 BODY-001 冻结证据链校验失败，且修复需改基础设施工具或重建冻结工件（违反「不改冻结配置」）。`P1-ENG-ACQ-001` 操作单 §2.6 以 `sed` 从该文件生成运行时覆盖，T2 落点下 ACQ 恢复时仍得到系留开启配置。

### 8.4 运动学回放估算（第二圈稳态；25 m；E1 类扰动为脚本内简化噪声，非 AC-19 的真实估计器口径）

| 场景 | 策略 | 跟随距离 p50 / max (m) | 云台饱和 | 短边 p10 (px) | 起停 / 圈 | 静止比例 | 路程 (m) | 触边比例 |
|---|---|---|---|---|---|---|---|---|
| 系留关 | hold | 46.4 / 69.1 | 74% | 12 | 0 | 100% | 0 | 0 |
| 系留关 | 阈值 (a) | 14.3 / 18.4 | 0 | 27 | 12 | 46% | 353 | 0 |
| 系留关 | C1 | 5.9 / 6.7 | 0 | 32 | 1 | 0% | 389 | 0 |
| 系留关 | C2 | 8.9 / 9.7 | 0 | 31 | 3 | 1% | 370 | 0 |
| 系留关 | C3 | 11.8 / 12.8 | 0 | 30 | 5 | 4% | 347 | 0 |
| 系留开 | 阈值 (a) | 22.0 / 44.8 | 44% | 18 | 5 | 26% | 175 | 61% |
| 系留开 | C1–C3 | 21.9 / 44.6 | 43% | 18 | 3–4 | 12–19% | 173–189 | 60–67% |

- （D2 修订）「触边比例」列按模式读：系留关各行 = 候选被围栏投影的帧比例；系留开各行 = 候选被缆长可达圆投影的帧比例（该模式无围栏）；两者不可跨模式比较。
- 读法：系留开启时饱和由缆长决定、策略几乎无差别（D0 F4/F5 的定量复核）；**仅关闭系留，阈值策略在本路线已不饱和**，但仍每圈约 12 次起停、近一半时间静止——即用户所见「看得见就不动」的观感；c-组合把起停降到 1–5 次/圈、跟随距离稳定在 d\* 附近。
- 按 §3.9 规则的估算结果：C1–C3 均过 H1–H5（C3 的 H4 = 5 恰在上限），路程 C3 < C2 < C1 且差 > 3%，**估算会选 C3**；以工具在真实估计器下的结果为准。E2 类扰动下 C1–C3 起停升至 8–9 次/圈、最大跟随距离比 E1 增加约 1 m。
- 15 m、系留关：阈值 18 次起停/圈、短边 45 px；C1/C2/C3 短边 51/47/43 px、起停 1/3/5 次/圈（描述，不参与选择）。

## 9. 交叉影响

### 9.1 `P1-ENG-ACQ-001`（暂停中）

- 本项不改其暂停状态、合同、操作单与冻结规划器；T2 落点下 `config/scenario.default.json` 与阈值路径逐字不变（AC-7/AC-8），ACQ 操作单 §2.6 生成的仍是系留开启配置。
- 但本项修改 `controller/track_loop.py` 与三个 Unity 脚本，ACQ 操作单 §3「实现代码与通过候选一致」在本项落地后的 main 上**必然不成立**。恢复时须用户另定（§10 第 3 条）：推荐 (i) 若按原合同恢复，在 ACQ 通过候选的检出上运行（代码完全一致，本项改动不在场）；(ii) 若希望 ACQ 采用新跟随策略，另由接受角色写 ACQ 修订并窄复核（language_loop 接入属该修订，不在本项）。
- 暂停时的 Play D1 `runtime/scenario_config.json` 仍在共享 `runtime/`：本项 Play 前操作单须先按 ACQ 操作单 §2.6 末段处置意图把它移入 `runtime/hold-<标签>/`（不删除）或另行裁定，**不覆盖**；此动作由接受角色在 Play 核对时确认。（D2）若未移开，三道 fail-closed 各自独立生效：Unity 覆盖优先会加载它（系留开启、`deterministic-loop-default`），`track_loop._validate_frame_scenario` 因帧 `scenario_id` 与 `--scenario-id deterministic-loop-untethered` 不等而拒绝首帧，standoff 构造器因生效场景与 body 场景不等而拒绝（AC-18）。
- （D2）`controller/language_loop.py` 的 Python 侧回退（`effective_scenario_document`、`--body-scenario-config` 缺省、读场景缺省三处）仍指 `config/scenario.default.json`，本项不改（AC-18）；本项落地后 main 上「无覆盖」时它与 Unity 的回退不再一致——ACQ 操作单 §2.6 总是生成覆盖，故 ACQ 恢复按原合同在通过候选检出上运行时无此问题；若用户选在新 main 上恢复，该不一致须由 ACQ 修订处理（§10 第 3 条，用户已答「恢复时再定」），本项不代为决定。

### 9.2 旧证据

BODY-001、ACQ attempt 1/2、SCENE-* 等按当时规则解读，不回溯改判；字段缺失 = 系留开启、`config/scenario.default.json` 字节不动、阈值路径逐字回归（AC-2/AC-3/AC-7/AC-8）共同保证系留开启配置可复现。BODY-001 臂 B 读数与本项 Play 读数不做直接比较（系留与策略同时变化，R-7）。

### 9.3 设计基线 v0.3 需改写的条目清单（由接受角色在接受时改写；本角色只列清单）

1. 文件头版本注记 v0.3.17「采纳系留绷紧假设」→ 注明系留为可选场景模式，主线缺省场景无系留，绷紧假设仅在开启时适用。
2. §1「保留的系统研究问题」（固定锚点、有限缆长）与「系留物理在 Phase 1 明确简化为球面工作空间约束」→ 标为系留开启模式/研究副线。
3. §2 `PlatformState`「系留裕度」→ 可选（开启时）。
4. §4.1 P1「机身最小化运动（含悬停）」→ 工程缺省改为「距离保持带跟随」，hold 与阈值策略保留为对照/兜底；P2 约束 `‖p_k − anchor‖ ≤ 35` 改为「系留开启时」，并加围栏与机身避障约束（`‖v_k‖ ≤ 4`、`8 ≤ h_k ≤ 32` 不变）。
5. §4.2「系留的真实含义…」→ 系留开启模式下适用。
6. §4.3「保留两个系留特有模式」与「已知落差：…张力控制绞盘维持绷紧」→ 限定为开启模式，补无缆模式 plant 语义（围栏钳位、`tether_saturated` 恒 false）。
7. §6「场景反天花板：必须变化锚点位置、系留长度…」与 §7 消融「忽略系留约束的规划器」→ 研究轨道条目，工程轨道不适用。
8. §10 风险 R2 行 → 限定为开启模式。
9. `PROJECT_BRIEF.md` 第 5–7、28、42 行的系留描述，与 `docs/current-status.md`「Active constraints and decisions」的绷紧假设条 → 同步措辞。

### 9.4 Unity 改动与 `docs/project-background.md` §3「不做 Unity 场景改动」

本项改 3 个 C# 运行时脚本（`ScenarioConfig.cs`、`TetheredDronePlant.cs`、`TetheredScenarioBootstrap.cs`）与 Edit Mode 测试，并新增 1 个 JSON 场景配置；**不改** `*.unity` 场景文件、prefab、材质、第三方资产或手工 `*.meta`。脚本/配置改动不等于场景改动；唯一的渲染差异是系留关闭时不再绘制缆绳线（运行时生成对象，场景文件无此物）。系留开启时渲染逐字不变。若用户把运行时可视对象也算作「场景」，则改为关闭时仍绘制缆绳（AC-5 相应改写），请接受角色确认读法。

## 10. 待用户（每条附推荐与理由；答复前按推荐缺省不执行，只影响接受/签发时点）

1. **「缺省关闭」的落点**：推荐 T2——新增版本化缺省场景 `config/scenario.untethered.json` 作主线缺省，`config/scenario.default.json` 字节不动；理由：后者 sha 被 BODY-001 冻结工件与两个 `tools/check_*.py` 基础设施工具绑定（§8.3），字面改写须用户另授权协调批次，范围远超本项。
2. **高度**：推荐保留 25 m 缺省；理由：15 m 下目标像素更大（估算 43–51 px 对 30–32 px），但围栏西缘出现高于机身的楼宇、避障开始生效，且更俯视的视角离训练帧更远；待 AC-19 的 15/25 m 读数出来后再定。
3. **`P1-ENG-ACQ-001` 恢复与主线接入**：推荐恢复时由用户另定——按原合同恢复则在其通过候选的检出上运行；若要新跟随策略进入主线闭环，另由接受角色写 ACQ 修订（含 language_loop 接入）；理由：本项改动使 ACQ「代码与通过候选一致」必然不成立，且接入会改变 ACQ 已复核的冻结规划器前提。
4. **§5 预算信封**：推荐按申请签发（新 scenario_id 1、Play ≤ 2 次 × ≤ 330 s、run ID ≤ 2、NanoTrack 加载 ≤ 2，其余 0）；理由：1 次两圈 Play 即覆盖 Part P 读数与 Part T 在 Unity 的无缆安全读数，重试只限环境性失败。

## 附录 A. D0 调研与现状事实（压缩；编号保留可引用；D0 全文见本文件 git 历史中主题为「P1-ENG-FRAME-001 D0 调研与选项…」的提交）

| # | 事实 | 出处 |
|---|---|---|
| F1 | 冻结规划器 `ThresholdBodyPlanner`（`threshold-corridor-v1`）只读云台离底角余量 `margin = 45° − 离底角`：< 10° 置「移动」，> 20° 置「停」，其间保持；移动时沿云台方位以固定 4 m/s 水平飞，锚点→候选位置线段碰走廊棱柱则缩短或 hold；不读估计器、真值与饱和标志 | `controller/body_planner.py`；`config/p1-m3-body-001.json` `policy` |
| F2 | 25 m 高度、云台未饱和时 d = 25·tanθ：35° ↔ 17.5 m 开始飞，25° ↔ 11.7 m 停——现行规划器是一条 11.7–17.5 m 的距离带，以 4 m/s 起停式执行 | D0 计算 |
| F3 | 「画面居中」由云台负责：ACQ §3.8 每处理帧对指针 track 发 `look_at`，限速 30°/s；机身规划器输入不变 | ACQ 提案 §3.8、AC-15 修订 1 |
| F4 | attempt 2：机身约 frame 650–700 飞到 (156.1, 112.8) 后停住，约 frame 750 起云台持续饱和；该点距锚点约 24.5 m，已达 35 m 缆长在约 25 m 高度的水平可达半径约 24.3 m——停住主因是系留边界 | `docs/unity-test-log.md` attempt 2 supervisor 核对；D0 计算 |
| F5 | 系留开启时「可让云台不饱和对准」的最远水平距离约 49.5 m，路线约 43% 超出；机身不动时目标全程在画面内（离底角最大约 70°） | D0 计算；§8.4 复核（饱和 43–44%） |
| F6 | 系留开启时可居中半径 √(35² − h²) + h 在 h ≈ 24.7 m 取最大 49.5 m，现行 25 m 已最优 | D0 计算 |
| F7 | 尺寸：`fy = 415.7 px`；D0 按车宽 1.8 m 估短边 ≈ 748/R；**D1 核实红车宽 2.0 m，修正为 ≈ 831/R**（R = 25 m 约 33 px、50 m 约 17 px，12 px ↔ 约 69 m）；「太小」口径短边 < 12 px（`MIN_VISIBLE_SIDE_PX`） | ACQ §0 事实 9；`tools/dist_data/contract.py`；`TargetVisualFactory` |
| F8 | 系留开启、机身按最佳位置跟随时路线最远斜距约 51 m；机身不动时约 73 m | D0 计算 |
| F9 | 设计 §4.1 P1「可见概率满足 → 机身最小化运动（含悬停）」，P2 才滚动优化；阈值规划器是其简化实现 | 设计 §4.1/§4.3 |
| F10 | 地面系估计器输出 `WorldEstimate`（x, z, vx, vz + 协方差），契约 v1 已传给 `decide()`；先验为「未标定启发式」 | `controller/body_planner.py`；`controller/track_loop.py` `_body_step`；BODY-001 配置 `estimator.priors_status` |
| F11 | 快层全局运动补偿按纯旋转单应（H = K·R_Δ·K⁻¹），v1 忽略机身平移 | ACQ 提案 §3.4 |
| F12 | 已有指标：`C_track`（主，IoU + 身份）、`C_geom`、`C_track\|geom`、`C_quality`（含中心误差、像素面积）；ACQ 描述读数 time-to-center（< 64 px 连续 5 帧） | 设计 §6；ACQ 提案 §3.10 |

**D0 调研结论（保留原结论，出处见下）**：(1) 「目标在画面里」不是好的成功定义，公开工作要么加距离/分辨率条件（Luo 2018 的 d、Quintero 2014 的「足够分辨率」），要么加中心偏差（DAT、COPA）；(2) 「居中」几乎都由云台或机头朝向负责，机身负责距离/相对位置（PX4 Follow Me、ArduPilot Follow、DJI Trace、COPA）；机身不动只靠云台是另一合法模式（DJI Spotlight、PTZ、系留 ISR 产品）；(3) 机身触发多为连续设定点而非阈值起停，「超距放弃」（ArduPilot `FOLL_DIST_MAX`）才是阈值，画面中心死区只见于 PTZ 云台防抖；(4) 按尺寸触发平台移动只见于玩具级项目，且为连续控制；(5) 现行规划器在距离上并非「快丢才动」，观感来自宽滞回 + 起停式执行与系留边界（F2/F4）。常用指标：画面内时间比例、到画面中心像素距离、距离保持误差、累计奖励/任务长度、跟踪器 IoU/中心误差——本项只作描述量。

**D0 选项与推荐（保留）**：(a) 维持阈值规划器——不推荐作最终方向，保留为对照；(b) 机身跟到目标正上方（d\* ≈ 0）——可行不作首选；(c1) 画面中心死区触发机身——退化为 (a)，不推荐；(c2) 距离保持带；(c3) 基于速度的提前量；(c4) 按目标尺寸触发——噪声与可用区间太窄，不推荐作主触发；**(c-组合) = 云台居中 + (c2) + (c3) + 阈值兜底 + 边界处理与显式状态——推荐，用户已选**（账本 09-30 决定）。D0 §6 各问的去向：方向与「居中指什么」已由用户选定；d\*/带宽 → §3.9 候选与规则；系留不可达段 → 系留缺省关闭后不再存在，开启时按 R-8 对照；ACQ 关系 → §9.1；设计 §4.1 → §9.3。

## 出处（D0 调研，保留）

- PX4 Follow-Me Mode：https://docs.px4.io/main/en/flight_modes_mc/follow_me.html ；ArduPilot Copter Follow Mode：https://ardupilot.org/copter/docs/follow-mode.html
- DJI Support, Using the Tracking Function with Drones：https://support.dji.com/help/content?customId=en-us03400006832&spaceId=34&re=US&lang=en&documentType=artical&paperDocType=paper ；DJI Store, Film Like a Pro with ActiveTrack：https://store.dji.com/guides/film-like-a-pro-with-activetrack/
- Skydio Autonomy：https://www.skydio.com/skydio-autonomy ；Elistair：https://elistair.com/applications/defense-surveillance-drone/ ；Hoverfly SPECTRE：https://hoverflytech.com/tethered-drones-uas/spectre/
- Frigate Camera Autotracking：https://docs.frigate.video/configuration/autotracking/ ；Telycam：https://telycam.com/auto-tracking-ptz-cameras-how-they-work.html
- Luo et al., ICML 2018：https://proceedings.mlr.press/v80/luo18a/luo18a.pdf ；DAT（NeurIPS 2025）：https://arxiv.org/abs/2412.00744
- Chaumette & Hutchinson 2006：https://faculty.cc.gatech.edu/~seth/ResPages/pdfs/ChaHut06.pdf ；COPA（arXiv 2026）：https://arxiv.org/abs/2609.25898 ；PAMPC（IROS 2018）：https://rpg.ifi.uzh.ch/docs/IROS18_Falanga.pdf
- Quintero & Hespanha 2014：https://www.sciencedirect.com/science/article/abs/pii/S0967066114001774
- Joubert et al. 2016：https://arxiv.org/abs/1610.01691 ；Nägeli et al., ACM TOG 2017（仅据检索摘要）；Bonatti et al., JFR 2020：https://arxiv.org/abs/1910.06988 ；Karakostas et al., ICIP 2018：https://aiia.csd.auth.gr/wp-content/uploads/papers/PUBLISHED/CONFERENCE/pdf/2018/Karakostas_ICIP_2018.pdf
- UAV123（ECCV 2016）：https://link.springer.com/chapter/10.1007/978-3-319-46448-0_27 ；Xiao, Dufek, Murphy 2020：https://arxiv.org/abs/2001.06347 ；CBF-QP for tethered UAVs 2025：https://arxiv.org/abs/2502.08129
- 玩具级参照：https://github.com/fvilmos/tello_object_tracking ；https://github.com/Matthewjsiv/Person-Tracking-Tello-Drone

## 待裁定

### AC-22 线索裁定（2026-10-01，接受角色）

**问题与来源**：用户要求的模型主观评测中，一次只读影子核对报出新 standoff 构造路径读取 `target.route_world_m[*].y` 核对显式地面高度的线索；影子核对不是任何角色的正式产出，也不是门证据。用户经账本 2026-10-01「P1-ENG-FRAME-001 — 用户决定：R1@K2 返工前先交接受角色裁定 AC-22 线索」要求本角色裁定；supervisor 只核实新旧两处磁盘事实，未给合同结论。`C2@K2` 与 `R1@K2` 均未处理这条线索，本节不把影子结论改作复核 finding。

**只读核实**：候选从 `docs/reviews/P1-ENG-FRAME-001.md`「R1@K2 §0」的 `round_candidate` 解析，K2 基线按交接文件文首 `$BASE` 解析。候选 `controller/track_loop.py::_build_standoff_runtime` 第 1541–1550 行逐点读取路线 y，缺路线或高度不等即拒绝；基线 `_build_body_runtime` 第 1431–1440 行确为逐字相同的检查。当前主树与该候选在实现路径无差异。`TruthIsolationTests.test_runtime_modules_name_no_truth_source` 只扫 `standoff_planner.py` 和 `scenario_tether.py`，未覆盖新构造路径；`StandoffWiringTests.test_standoff_scenario_id_and_ground_plane_fail_closed` 还把有限标定 0.0 与路线 0.2 不等时拒绝写成预期。

**答复：新路径不符合 AC-22。** AC-22 禁的是本项运行时读取路线真值，并不限于把真值喂给 `decide`。这里虽未用路线 y 自动填参数，却用它验证操作者标定、决定控制器能否构造，并在拒绝消息中输出真值；fail-closed 不消除这条信息依赖。设计 §3.5 的显式、有限、无缺省地面标定要求继续适用，不能把「不得推断」缩成「不自动赋值」，也不能把设计 §6「Unity 真值只进 evaluator」放宽成允许构造阶段读取。AC-11 的 planner 纯度不能替代 AC-22 的接线隔离。

**旧路径边界**：旧 `P1-M3-BODY-001` 提案 §3.4 明列该高度为冻结场景常量，其历史合同、verdict 与证据按当时规则解读，不据本项 AC-22 回溯改判；这也不构成新路径照搬的许可。本项 §3.5、AC-7/8/18 冻结旧 `hold`/`threshold` 行为。新构造器及其兜底组装 `build_standoff_planner` 不调用旧 `_build_body_runtime` 的路线检查，可独立修复；本轮不要求改旧路径，不扩大范围。若之后要求修旧构造路径，须先回用户另定范围，不能借本次返工改动。

| 条款解释 | 裁定与可逐条核对的修复要求 | 证明方式 | 日期 |
|---|---|---|---|
| AC-22 修订 1（`CLARIFY`；解释 AC-22、设计 §3.5/§6，关联 AC-18） | ① 新 `_build_standoff_runtime` 及其本项新增调用链不得提取、遍历或按路线坐标/高度校验标定，移除该检查及相应 docstring；② 标定唯一来源仍为显式 `ground_plane_y_m`，直接构造与 CLI 均拒绝缺失/非有限值，不新增缺省、不由路线或 home 高度代填；③ 更新原接线测试的错误预期，并按下述红绿与静态检查证明。只改 §4.1 Part P 的 `controller/track_loop.py`、`tests/test_track_loop.py`、`tests/test_standoff_planner.py` 及原停点证据；参数、选参、信封和冻结旧路径不动。 | test: `tests.test_track_loop.StandoffWiringTests.test_standoff_ground_plane_is_explicit_finite_and_route_independent`（新增，调用真实 `_build_body_runtime(..., "standoff")`）；test: `tests.test_standoff_planner.TruthIsolationTests`（增补新构造路径/新增 helper 的读取面检查）；artifact: `docs/evidence/P1-ENG-FRAME-001-K2-handoff.md`（本次 R1 返工的 AC-22 自证） | 2026-10-01 |

证明闭集：上述具名接线回归使用既有 untethered 场景与 FRAME 配置、同一 `scenario_id`、临时 runtime 无覆盖，显式标定分别为 0.2 与 0.0 时均应成功构造（后一项修前必红）；直接构造对 `None`、NaN、正/负 Infinity 均拒绝，CLI 缺参数与非有限值继续拒绝。静态检查只钉新构造函数及本项新增 helper 的路线/评估器读取面，不能用扫描整个旧模块而迫使修改冻结路径。实现者保留修前红/修后绿证据，交复核角色在 `R2@K2` 核实，接受角色本轮未跑测试。有限值可被显式声明不表示已证明实际地面标定正确；本项正式 Play 仍用原操作单的标定值，不改标定或选参。

AC-18/29 的场景一致性校验、schema/scenario_id 与 SHA/来源身份仍须保留：整份场景文档仅作配置同一性绑定，不得从其中的 target 子树取控制/标定量。本修订不允许为回归绕过配置绑定、不新增字段或标定工件、不触及离线工具的真值合成/读数用途。原 AC 表不覆盖、不删改、不新增 AC；这是用户转来的既有合同解释，并入本次 `R1@K2` 返工，修复后直接交 `R2@K2`，不增核对轮、不改独立 verdict、不放行 Play。C2 表的 AC-22「满足」及其计数仅是当轮未处理此处的记录，本节补充裁定使该处在修复前不得作为 AC-22 满足依据。

### R1-3 SCOPE_GAP 记债裁定（2026-10-01，接受角色）

**裁定：记债，`SCOPE_GAP` / `OPEN`，非阻断，不并入本次返工。** 来源为 `docs/reviews/P1-ENG-FRAME-001.md`「R1@K2 §3 R1-3、§6」。只读核对 `ScenarioConfig.cs::GeofenceBound/NormalizeGeofence` 与 `scenario_tether.py::_number/parse_geofence`，Unity 先转 float32 后判定，Python 用 float64；`max_x = 1e39` 与 home.x = 132、`min_x = 132.000001` 分别产生相反方向的接受域差异。任一侧拒绝即无共同运行，不能一概称 Unity 更严。接受复核所列当前闭集/归档域不可达判据，维持 AC-1 已限定的夹具域，不增 AC、不改 Part T。记债理由：数值域扩展后配置一致性可能失效，未来复用此解析器接受超 float32 或 home/界值舍入邻域输入前，须在后续获批合同中明确两侧数值口径并验证两个方向；唯一债务入口为 `docs/implementation-status.md`「范围外已知缺陷」本项 R1-3 行。本条不签 release（原无 block），也不宣称已修复。

本次两项裁定均在已接受范围与角色权限内，`needs_user: none`；实现接手 CLARIFY 与既有 R1-1/R1-2，独立复核仍待 `R2@K2`。

open_items: none

## R2@K2 通过轮消费（2026-10-01，接受角色）

消费 `docs/reviews/P1-ENG-FRAME-001.md`「R2@K2」§0–§6 的 `PASS_WITH_NOTES`；通过候选仅从同轮 §6 `passed_candidate` 运行时解析。R1-1/R1-2 已经复核修前红/修后绿闭合，AC-22 修订 1 成立，无新的阻断或消耗性 block。K2 代码停点通过；Overall 为 `IMPLEMENTED_REVIEWED_AWAITING_UNITY`、Lifecycle 为 `ACTIVE`。AC-21/AC-23 仍 `NOT_RUN`，不适用 `UNITY_NA`，不得 `DONE`。本轮只消费既有证据，不重做 C 核对、不跑测试、不签独立 verdict。证据与机械归因汇总见 `docs/implementation-status.md` 同名节。

**现行合同解释（不增 AC）**：§2.3/§5/§7 与操作单原写「R1@K2 通过」是首次计划的 K2 独立复核前置；按 workflow §4.4 的同停点返工及 §4.6「最终通过轮消费」，现在由同一 K2 的 R2 通过轮承接此条件，不追认 R1 为 PASS。账本 09-30「用户答复 §10 四条…」的「明确未授权」仍禁止在独立复核通过及接受侧 §4.5 放行前开 Play；预算、重试条件与候选范围不变，复核通过不等于本轮已放行。

R2 §5 的覆盖观察沿用 AC-23 的**全程覆盖缺席**要求，操作单 §2 增补发令前与结束后核对、期间不得恢复覆盖；不得以「逐值相等」代替缺席。负方差的拒绝语义未由现行契约定义，本轮不扩张 AC-11/13 或新增义务；`hypot` 末位差有既有全网格 `--check` 一致证据，不改参数、选参 C3 或阈值。R1-3 `SCOPE_GAP`/`OPEN` 不变，唯一债务入口仍在 `docs/implementation-status.md` 的对应行。R1 §5 的平台量来源按 AC-23 解释：离线从评估器旁车取同源平台字段，操作单 §5 记录同帧元数据交叉核对；不把目标真值送入控制器，也不改读数算法或门值。

**Play 决定：尚未放行。** 已签 Unity 信封与 K2 复核前置成立；尚缺 Unity 主机的候选/工作树、解释器与本地模型文件、覆盖缺席、槽位及打印命令预检。本机只读见通过候选至开工 HEAD 仅状态板/复核文件/派发日志差异、工作树干净，但本机残留覆盖仍在，且本机事实不能替代 Unity 主机核对。用户先按操作单 §0–§3 做零消耗预检并回传原始输出（不 Play、不载权重、不建 ID）；接受角色再按 workflow §4.5 记录主机 HEAD/status 到 `UT-P1-ENG-FRAME-001-D1`、核实白名单文档差异与预算余额，全部就绪后才放行并把交接改 `Consuming=yes`。当轮发令/ tracker 操作由接受角色在 Unity 主机完成，用户执行 Unity Play；supervisor 只转交与调度，不替代接受裁定。预检失败先回接受角色，不安装、下载或使用远端补齐。

open_items: WORKFLOW_4_5_PREFLIGHT, AC-21_UNITY_VERDICT, AC-23_UNITY_VERDICT, R1-3

## Unity 主机预检与 Play 放行（2026-10-01，接受角色）

用户本轮指定本机执行 Unity（账本同日「用户指定本机 Unity 预检与放行」）。操作单 §0–§3 预检与 workflow §4.5 对应关系核对通过，接受侧放行首轮正式 Play；逐项核对、候选差异文档白名单、原始 HEAD/status、覆盖保留与职责见 `docs/unity-test-log.md`「UT-P1-ENG-FRAME-001-D1」，机器记录与完整命令见 `docs/evidence/P1-ENG-FRAME-001-preflight.json` / `-play.md`。先前 R2 消费时「尚未放行」为当轮历史结论，以本节与该日志的现行裁定为准。

本批零 Play/权重/run 消耗，不改 AC、冻结参数、信封或 R1-3 债；AC-21/AC-23 `NOT_RUN`，Overall/Lifecycle 不变。下一接手为用户执行 Play 并尽早暂停，之后接受角色按操作单核帧0与 source_path、经用户冻结框目检后启动 tracker；不能据预检宣称 DONE。

open_items: AC-21_UNITY_VERDICT, AC-23_UNITY_VERDICT, R1-3

## Unity Play 首次短运行处置（2026-10-01，接受角色）

首轮已执行但未暂停/提前退出、未启动 tracker，原件已保留；计 Unity Play 1、加载/run/session 0。现行裁定及用户原话见 `docs/unity-test-log.md`「UT-P1-ENG-FRAME-001-D1 / 首次短运行处置」，机器凭据见 `docs/evidence/P1-ENG-FRAME-001-unpaused-play.json`。操作失误不在 §6 环境性重试闭集内，故既有首轮放行不延伸为重开许可；“覆盖一下”的含义及是否在原总额度内允许再开一次已向用户澄清，未答前停在零消耗交接。AC、代码/参数、信封与 R1-3 债不改；AC-21/AC-23 NOT_RUN，无 Unity verdict。

open_items: USER_RETRY_DECISION, AC-21_UNITY_VERDICT, AC-23_UNITY_VERDICT, R1-3

## Unity Play 操作失误重试授权与第二次放行（2026-10-01，接受角色）

用户“再开一次”已逐字入账同日「用户授权操作失误后再开一次 Play」：只允许本次未暂停提前退出后的重试一次，不追加原 Play≤2 / 单次≤330 s 总上限，不改 AC、代码/参数/模型。首轮原件保留，共享残留仅保留式移动；正式 run 均未创建，不复用已产生 ID。原 §6 环境性重试闭集仅本次按用户例外处理，第二次之后不得第三次 Play。

本机 §0–§3 与 workflow §4.5 重核通过，第二次 Play 放行但尚未执行；原始 HEAD/status、候选逐路径白名单、模型/配置/命令、共享槽位/覆盖/额度与交接见 `docs/unity-test-log.md`「UT-P1-ENG-FRAME-001-D1 / 操作失误重试授权与第二次放行」及 `docs/evidence/P1-ENG-FRAME-001-retry-preflight.json`。当前累计 Play1、加载/run/session0，无新增消耗。AC-21/AC-23 NOT_RUN，无 Unity verdict；R1-3 债及 Overall/Lifecycle 不变。

open_items: AC-21_UNITY_VERDICT, AC-23_UNITY_VERDICT, R1-3

## Unity 第二次采集与接受裁定（2026-10-01，接受角色）

用户本次“已暂停”“匹配”“已恢复”以及“仅本次延长至420秒”“仅本次延长至480秒”均直接在本会话发生，墙钟两次例外逐字入账且在越界前生效，仅替换当前第二次Play总墙钟上限；代码/冻结参数/约273秒计划/模型及其他预算维度不改，不追加第三次Play。tracker自然结束0、1366条记录/273.009458s，Unity已退出；累计Play2/加载1/run1。完整按钮墙钟未独立取得，465.024116s仅为全旁车capture跨度，不补造精确在限结论。

按原AC-21/AC-23核对，结果见 `docs/evidence/P1-ENG-FRAME-001-play.md`「接受裁定与未闭项」及机器结果同名 `-play-result.json`：两圈及AC-23安全/身份/128组同帧平台量核对满足；AC-21工具R7_c_track=null（读取顶层/summary而实际metrics为aggregate.c_track）不满足，用户原话“consle无错误，但是我看不见无人机啊”使机身跟随/起停目检仍缺证。整体未通过、不记DONE；不改R2历史通过轮，不签独立finding/复核文件，不新增AC/阈值，不用数字替代人眼条件。

归因：R7缺口属于既有AC-21实现输出不忠实，交实现按原合同离线窄修并用保存run零消耗重分析，禁止新Play/权重/ID；不占C核对退回额度或R独立复核轮数。用户目检未闭与墙钟未独立核实留待接受/用户，R1-3范围外债不变；Overall/Lifecycle保持IMPLEMENTED_REVIEWED_AWAITING_UNITY/ACTIVE。

open_items: AC-21_R7_SCHEMA_PATH, AC-21_USER_FOLLOW_OBSERVATION, PLAY_WALL_TIME_UNVERIFIED, R1-3

## Unity 补测准备（2026-10-01，接受角色）

用户“可以，开始补测吧”已逐字入账「用户同意开始一次补测」：新增Play1（累计最多3）、原剩余加载/run各1用于具名补测，两项总上限仍各2；原场景/参数/約273秒仿真计划/其他额度不变、不再重试。新补测墙钟沿原330秒；此前480秒仅适用已结束第二次，建议新补测设480秒待用户明确。R7尚未修，不提前放行或进入Play；实现调用授权待用户，接受不改实现或跑测试。

具体窄修交接与计时/目检准备见 `docs/evidence/P1-ENG-FRAME-001-supplement-ops.md`，源码/旧run完整性与未用run核对见同名 `-supplement-preparation.json`。现有AC-21只沿原义务修复与补证，不新增AC/性能门，不回写旧原件、R2历史verdict或R1-3债。整体门/Lifecycle不变。

open_items: AC-21_R7_SCHEMA_PATH, IMPLEMENTATION_DELEGATION, SUPPLEMENT_WALL_LIMIT, AC-21_USER_FOLLOW_OBSERVATION, PLAY_WALL_TIME_UNVERIFIED, R1-3

## 补测准备授权落实（2026-10-01，接受角色）

用户直接答复“允许实现子代理先修R-7”“本次补测上限480秒”，已逐字入账同日「用户授权实现子代理与本次补测480秒上限」。一个实现子代理获准执行现有AC-21字段路径窄修、必要focused回归及旧数据复算；零Play/模型/run消耗。仅本次补测总墙钟480秒；新增Play1与原剩余加载/run各1的边界不变、不再重试。具体交接见 `docs/evidence/P1-ENG-FRAME-001-supplement-ops.md`。修复与适用候选凭据接受核验之前不放行Play，门/Lifecycle与原合同不变。

open_items: AC-21_R7_SCHEMA_PATH, AC-21_USER_FOLLOW_OBSERVATION, PLAY_WALL_TIME_UNVERIFIED, R1-3

## R7实现结果核验与补测前置（2026-10-01，接受角色）

R7窄修、focused红绿与旧run复算已完成；接受重读本批9路径完整diff/原AC/证据及直接关联代码，逐条核验见 `docs/evidence/P1-ENG-FRAME-001-R7-acceptance-inspection.md` / 同名json。138原件不变，新旧analysis仅R7变化；AC-21整体仍未闭。新全套资源、独立复核子代理与仅此次同源接受核对例外已形成具体选项待用户。不是正式C轮，不重写下方历史C2表/旧R2、不消耗退回次数；480s补测未动，未放行Play。

open_items: R7_FULL_SUITE_RESOURCE_AUTHORIZATION, R7_INDEPENDENT_REVIEW, R7_CROSS_MODEL_DISPOSITION, AC-21_USER_FOLLOW_OBSERVATION, PLAY_WALL_TIME_UNVERIFIED, R1-3

## R7全套前置静态预检裁定（2026-10-01，接受角色代录）

用户“可以开始做准备工作了”已逐字入账，同意具名三项前置与仅此次同源核对例外；本轮全树预检另发现两条re-anchor真实子进程，Nano4/YOLOE2/DINO2超过已签Nano2/YOLO-DINO0，按越界即停未启动全套。原始版本/文件hash/93测试路径清单与闭集loader来源见 `docs/evidence/P1-ENG-FRAME-001-R7-full-preflight.json`；具体选项与接受代录见同名 `-full-suite-preparation.md`「接受侧收工代录与当前裁定」。一次本地CPU全套的数量调整待用户；此前复核/同源许可保留，C3/R3未开、不放行Play，不改下方历史核对表/合同/R2或R1-3债，实际模型/Play/新ID消耗0。库导入可能初始化DNS、无当时流量证据，不声称外部DNS零；后续执行方案列安全离线环境与禁止自动安装。

open_items: R7_EXPANDED_TEST_RESOURCE_AUTHORIZATION, R7_FULL_SUITE_EVIDENCE, R7_INDEPENDENT_REVIEW, AC-21_USER_FOLLOW_OBSERVATION, PLAY_WALL_TIME_UNVERIFIED, R1-3

## R7一次全套数量调整落实（2026-10-01，接受角色）

用户“继续吧，你来调用子进程”在已明确一次本地CPU全套Nano4/YOLOE2/DINOv2 2/CSRT2的上下文中确认继续；逐字入账同日「用户确认一次完整测试的具名模型额度并调用原子代理」。仅替代本次测试的具名数量上限，原实现子代理执行一次并补停点自证；完整测试尚未执行，后续C3/R3未开、不放行Play。具体交接见 `docs/evidence/P1-ENG-FRAME-001-supplement-ops.md`「当前前置与下一角色」，其他合同/额度、人眼/墙钟及R1-3债不变。

open_items: R7_FULL_SUITE_EVIDENCE, R7_INDEPENDENT_REVIEW, AC-21_USER_FOLLOW_OBSERVATION, PLAY_WALL_TIME_UNVERIFIED, R1-3

## R3@K2 通过轮消费与补测预检（2026-10-02，接受角色）

消费同名复核文件「R3@K2」§0–§4 的 PASS_WITH_NOTES；通过候选从同节 passed_candidate 动态解析，不沿旧R2放行新工具。独立19项focused通过、138原件前后hash相同、两个明确端点复算对应原量源，R7工具缺口闭合；全套旧13失败与新增12项loopback环境ERROR保留，未测HTTP行为不改称通过。四项停点条件由独立复核认可，本接受轮不跑测试/签独立verdict。

R3-1 CLASS_3/上游漏检按复核§3逐字补丁已在本批应用：C3技能迁移出处改为10-01两条用户直接协调授权。机械归因新增核对轮错误1（文档出处，不阻断），不转嫁实现；复核文件原finding/补丁保留，本角色不改复核记录。AC-25完整集合字面非§4.1子集的事实保留；按R3§1/§2逐文件授权/必要流程归属核查，无越权实现，不据此改AC、撤销协调授权或裁切候选。R1-3 SCOPE_GAP/OPEN不变。

本机workflow§4.5零消耗预检已就绪，原始HEAD/status、最新通过候选至HEAD的两项白名单文档差异、既有解释器/API、两个模型完整hash、冻结配置与逐token命令、全局blocks/release及共享槽位在同名supplement-preflight.json。Unity6000.4.1f1正确场景非Play；覆盖缺席、旧覆盖保留。358份共享残留移入新hold、移动前后hash一致，138份正式旧run原件不变；未删除、不建新run或载权重。直接脚本print-only因导入路径失败的预检事实保留，模块形式成功产出相同冻结command，不修代码或安装。

**放行本次已授权补测，等待用户准备好观察后再发计时/Play指令。** 额外Play1、原剩余Nano加载1/run1、本次完整按钮墙钟≤480秒、约273秒冻结仿真、无再重试及其他额度0不变。用户负责Play/暂停/恢复/退出和机身跟随/起停目检；接受核暂停帧0/source/冻结框后起后台。计时独立于帧跨度/后台时长：发令前非Play时刻至退出后观测形成完整按钮墙钟的保守上界，精确按钮时刻未知时如实报范围/上界，不冒称精确测量；保守上界480秒前停止，绝不默认延期。开跑前再次记录HEAD/status与槽位/覆盖/代码身份；变化即回预检。

K2复核3轮、REWORK_REQUIRED仍1次，核对退回1/1不变，不因轮号3误判冻结终局；不适用UNITY_NA。Overall/Lifecycle维持IMPLEMENTED_REVIEWED_AWAITING_UNITY/ACTIVE，AC-21人眼与完整按钮墙钟未闭；无新Unity PASS/DONE。预算已获用户授权，本批不再请求同一额度。

open_items: AC-21_USER_FOLLOW_OBSERVATION, SUPPLEMENT_PLAY_WALL_TIME, SUPPLEMENT_COLLECTION, R1-3

## Contract conformance（核对表）

`C3@K2`（2026-10-02）接受侧只读核对，替换旧 C2 表。**照交新鲜上下文独立 R3@K2**；C1 已消费本停点唯一退回额度，本表不是独立 verdict，不直接放行 Play。仅此次 R7 接受同源核对例外依据账本 10-01「用户允许开始三项补测前置准备」，不虚称 Codex/Claude 异源。本轮不跑测试、不写实现、不新增或改写 AC、合同或额度。

候选和最近通过基线由 git/复核 `passed_candidate` 动态解析，机器身份、完整 43 路径及完整 patch 的 hash 见 `docs/evidence/P1-ENG-FRAME-001-C3-inspection.json`。已先读清单，再完整分块读取全部候选 diff：含十个技能/映射文件、协调授权/派发/状态、旧 Play 原始机器证据及 R7 新证据，不自行排除混入的协调变更；补读实现最后一批全部五路径增量。已完整重读 AC-1…29、§2–6/§4.1/D2 裁定、R7代码与测试、Unity评估器直接量源和证据指针。相对旧通过候选 controller/Assets/config/ProjectSettings/Packages 零 diff；未触及项沿读旧 K2-handoff 与 R2 的真实证据，不冒称新运行。

独立只读校验：138份旧run原件 hash不变、真实fixture逐字节等于旧退出端点metrics.json、六个冻结/三路径身份对应一次全套所测代码。R7两端点复算证据无混用；12条新增ERROR的原日志逐条完整栈均在 server_bind/socket.bind 抛 EPERM，尚未到 HTTP 行为断言。机器比对不替代独立复核或用户Unity目检。

### §T

| AC | 结论 | 核对理由与指针 |
|---|---|---|
| AC-1 | 满足 | 解析器/测试未触及；旧K2-handoff「§T」、R2 §T对七个闭集与直接成员判键已有证据，本次完整全套无此项新增失败。R1-3范围外数值债仍OPEN，未外推闭集。 |
| AC-2 | 满足 | plant与EditMode参考副本零diff；旧K2-handoff §T和R2逐字回归核验保留，本次未重跑Unity。 |
| AC-3 | 满足 | 既有场景与加载实现零diff；沿旧K2-handoff §T的17文件逐位证据及R2，不回改旧证据。 |
| AC-4 | 满足 | 无缆plant和金标准未改；旧K2-handoff §T的五个关闭模式用例/284项XML及R2可沿读。 |
| AC-5 | 满足 | bootstrap零diff；旧K2-handoff §T和R2的TetherLine/anchor/遮挡调用链证据未失效。 |
| AC-6 | 满足 | 帧写入器与body/gimbal协议零diff；旧元数据字段集XML/R2仍适用。 |
| AC-7 | 满足 | 冻结BODY资产、旧场景与language_loop零diff；旧K2-handoff §T的走廊check及BODY用例、R2保留。 |
| AC-8 | 满足 | _build_body_runtime阈值分支与ThresholdConstructorSwitchTests零diff；旧§T身份/120帧/拒绝证据与R2保留。 |
| AC-9 | 满足 | 两场景零diff；旧UntetheredScenarioDiffTests、K2-handoff §T及R2的三键闭集证据保留。 |
| AC-10 | 满足 | 场景/安全函数零diff；冻结replay.json hash匹配，旧§T与replay的safety_bounds证据保留，15m冲突不改称通过。 |
| AC-27 | 满足 | ScenarioConfig.Load/VersionedDefaultPath零diff；旧§T XML和R2的无覆盖回退/覆盖优先证据保留。 |
| AC-28 | 满足 | DEFAULT_SCENARIO/线束零diff；旧DefaultScenarioEntryTests、K2-handoff §T和本轮全套无新增该项失败，未新增body透传。 |
| AC-29 | 满足 | effective_scenario_path及构造身份零diff；旧EffectiveScenarioPathTests、K2-handoff §T与R2保留，ACQ暂停不恢复。 |

### §P

| AC | 结论 | 核对理由与指针 |
|---|---|---|
| AC-11 | 满足 | R1旧有限协方差异常已由R2核实修复；planner零diff，旧K2返工证据/R2和本次全套均无该项新增失败，不继续沿旧C2的不满足结论。 |
| AC-12 | 满足 | 距离带/预测/锁存代码与DistanceBandTests零diff；旧K2-handoff §P、R2与本次全套无相关新增失败。 |
| AC-13 | 满足 | EstimateGateTests及估计闸零diff；旧K2-handoff §P与R2保留。 |
| AC-14 | 满足 | 兜底构造与FallbackTests零diff；旧§P/R2对应两模式走廊处理，无缆语义未改。 |
| AC-15 | 满足 | 后处理与四个具名性质用例零diff；本轮full-suite.log末段三种夹具计数与旧§P/R2对应，新增12条不在该套件。 |
| AC-16 | 满足 | reason闭集与ReasonClosedSetTests零diff；旧§P/R2及本次全套证据保留。 |
| AC-17 | 满足 | 配置/loader未改、运行时hash与全套记录对应；旧FrameConfigLoaderTests、§P/R2不变。 |
| AC-18 | 满足 | track_loop接线、参数、场景身份和language_loop零diff；旧StandoffWiringTests/§P/R2保留。新的HTTP ERROR属于未改动的ACQ/operator及language_selector假adapter服务，行为本轮未测，交关注项F-3。 |
| AC-19 | 满足 | 修改仅analyze_run的R7读数分支；plant镜像/网格/选参未动，replay.json hash匹配。旧§P/R2的60格、金标准及同种复现继续适用。 |
| AC-20 | 满足 | FRAME params/selected_candidate/replay hash不变；完整读取play-ops与supplement-ops增量，三body参数/覆盖缺席/来源句保留，补测冻结时长未改。操作单失效时态由本批更新，非协议变更。 |

### §共用与后续 Unity

| AC | 结论 | 核对理由与指针 |
|---|---|---|
| AC-21 | 证据缺失 | 旧play.md/Unity日志已有完整tracker运行，R7窄修用真实退出metrics字节补读aggregate.c_track。CoverageEvaluator::BuildMetricsDocument的c_track=trackingDuration/safeTotal，独立于c_track_given_geom；analyze_run先保留top-level/summary的键存在、null/zero，再补aggregate，_rounded仍六位。真实schema/兼容九分支/不推断metrics.final三个新用例与红1败→绿5/5证据在R7-implementation。旧退出R7=0.91899，显式自然结束端点=0.99495分别保留；缺用户持续跟随/起停目检及完整按钮墙钟，补测尚未运行。 |
| AC-22 | 满足 | 新R7读取限定既有离线analyze_run，运行时/控制模块零diff；旧TruthIsolationTests、§共用/R2保留，无真值进入tracker的新路径。 |
| AC-23 | 满足 | 旧play.md「安全读数」与play-result.json的已发布平台/旁车一致、位置/高度/饱和/速度/vy、修饰及来源均已接受核对；138原件保留。本次R7不更换安全量源，不把旧安全读数代替新补测或人眼。 |
| AC-24 | 满足 | 具名一次全套已执行：2064项/4败21错19跳，full-suite-result逐名分列旧13保留/新增12/解决0；全原日志已读，12条均loopback bind EPERM、相关HTTP行为未验证，绝非全绿。Assets/config零diff，旧K2-handoff引用284/284 XML身份对应，依工程§6不机械重跑未触及Unity。相称测试/环境限制是否允许开轮交独立复核判断，不把AC-24改写为全绿。 |
| AC-25 | 不满足 | 若按“完整候选集⊆§4.1”字面机械比较，43路径含十个技能/映射、协调账本/派发/工作流变更、后续证据和真实JSON fixture，非字面子集。全部已核读，协调路径可沿账本2026-10-01「全局 — 用户指示：复制 Claude 的 supervisor、implement、review、chore 到 Codex」及「全局 — 用户指示：复制 Claude 构思角色到 Codex」两条直接协调授权与git归属，R7必要回归见10-01窄修授权；运行实现仅analyze_run三行、test文件及fixture，无新增Assets/controller/config改动。此为范围读法待复核主张，不自行排除协调文件或增改AC豁免，也不据此撤销独立协调授权。 |
| AC-26 | 满足 | 原K2-handoff §T/§P/§共用逐AC与四项自证仍在；新R7-full-suite-handoff「四项稳定自证」补齐窄修增量、一次全套/逐栈归因/未测行为/资源未知、43路径和停止交接。自证存在不等于独立认可，重点交复核判条件2。 |

计数：满足27、不满足1（AC-25完整集合字面读法）、证据缺失1（AC-21后续Unity义务）。本停点退回额度1/1已用，不签REWORK_REQUIRED、不追加合同义务；核对表随候选照交复核。R1-3 SCOPE_GAP/OPEN保持原账本，不修不闭。

### 预复核关注项（给 R3@K2）

- **F-1 字段优先级/真量源**：tools/frame_follow_replay.py::analyze_run新三行，tests/test_frame_follow_replay.py::AnalyzeRunTests和真实fixture。核Unity原aggregate.c_track量源、top-level/summary同时存在、显式null/zero、缺键与不传metrics；不得回退到given_geom或默选metrics.final，不改变六位存储口径。真实fixture仅metrics字节是真实原件，其余manifest/frames由生产RunLogger路径生成的合成夹具，不能称整份真实run回放。
- **F-2 原件与两端点**：R7-recompute的before/after/explicit_tracker_finish_analysis、play-result完整138文件hash和C3-inspection核验。核原退出analysis只R7改变、自然结束与退出的统计窗口区别、原件无覆盖；旧Play按钮墙钟未知，465秒帧跨度不能替代总墙钟，新补测480秒授权仍只本次。
- **F-3 相称自证/12项环境限制**：R7-full-suite.log的12个具名server_bind栈及result逐名比较，关联未改动tests/test_eng_acq_operator_web.py、tests/test_language_selector.py与controller对应build_server。12项均未到HTTP断言，不称通过；请独立判断其与三路径窄修的关联和§4.3.1条件2。旧13项失败保持，模型成功数未知，按全次上界记账，不授权再跑全套、安装或模型加载。
- **F-4 完整集范围与协调混入**：机器43路径，尤其十个.agents技能/映射、workflow-changelog/authorizations/supervisor-dispatch及test fixture。必须逐文件核所有变更与来源，不从实现摘要裁切；AC-25的完整集字面问题交独立裁判，既有协调批次授权/已提交归属不由此核对改写。旧R2已通过的无改动finding按增量轮规则，R1-3债仍OPEN。
- **F-5 操作单/原Unity限制**：supplement-ops、play-ops及Unity日志完整增量；新工具未独立通过、准备状态与旧放行历史分清。正式额外Play1/加载1/run1未消费，完整按钮墙钟/用户视点及目检不得凭后台退出0代替。不开Unity、不提前清共享槽、不重建已用ID。

**交接结论**：四项增量自证有具名来源，接受侧保留测试环境限制与范围字面未决；照交独立复核判断开轮资格/稳定条件及R7行为。通过后仍须接受消费与workflow §4.5主机预检；本表不等于Play放行。

## 决策记录

- 2026-09-30 D0：调研与选项，推荐 c-组合（提交主题「P1-ENG-FRAME-001 D0 调研与选项…」）。
- 2026-09-30 用户决定（账本 09-30 决定）：方向 c-组合；系留可关闭、缺省关闭并入 D1；两部分 AC/测试/证据分列。
- 2026-09-30 D1（本稿，构思）：DR-1「缺省关闭」落点取 T2（新版本化缺省场景，旧缺省字节不动；§8.3，待用户确认 §10 第 1 条）；DR-2 显式 `tether_enabled` 字段而非超大缆长（避免魔数、缆绳仍被绘制、`tether_saturated` 口径混淆与规划器第二开关）；DR-3 新策略放新模块、组合未改的 `ThresholdBodyPlanner` 作兜底，`controller/body_planner.py` 字节不动；DR-4 系留关闭场景下阈值构造器拒绝构造；DR-5 围栏取矩形作业区而非 home 圆（§8.2）；DR-6 Play 线束用 track_loop；DR-7 单一 `K2` 候选、按 Part 分节复核；DR-8 近侧不后退、T_lead·k_p = 1 抵消比例滞后；DR-9 参数由预注册规则经工具选定并在 Play 前冻结。
- 2026-09-30 D1 接受裁定（bbbdb10）：`REVISION_REQUESTED`，退修项 U1/R1/R2；(b)–(j) 裁定见「D1 接受裁定」表。
- 2026-09-30 D2（本稿，构思，Fable 子代理）：DR-10 U1 已由用户答复（账本 09-30「P1-ENG-FRAME-001 — 用户答复 U1：同意本项走 engineering-v1 工程轨道」），本稿只记指针，轨道生效待接受角色 `ACCEPTED` 裁定；DR-11 R1 缺省入口闭集（§3.11）：Unity 无覆盖回退、线束常量、Python 生效场景解析器三处转新缺省，`track_loop` 与回放工具无缺省显式传参，覆盖文件不生成、Play 要求缺席，`language_loop`/ACQ/基础设施工具/BODY-001 冻结消费者不转；新增 AC-27/28/29，`tools/run_track_experiment.py` 与 `tests/test_track_experiment.py` 入 §4.1 集（Part T）；理由：plant 才是「缺省关闭」的物理落点，覆盖副本是漂移源，旧缺省经显式路径与覆盖路径逐字可达（AC-3/AC-8/AC-28）；DR-12 R2 AC-15 改为三夹具逐模式断言（有缆查可达圆 + 走廊、配置有围栏查围栏、无缆不查可达圆且须有 ≥ 100 个越圆样本证明未启用、避障两模式），同一原则修正 AC-10/AC-14/AC-19/AC-23 与 §3.4/§3.6/§3.9/§8.4 的两模式表述；DR-13 R1 改动不触及帧/命令协议语义，维持 `K2`、不改判 `K1K2`（§3.3）。
- 2026-09-30 D2 接受裁定：DR-14 **`ACCEPTED`，`Workflow: engineering-v1` 生效**；U1/R1/R2 已闭合，§7 (a)–(j) 按下节裁定，单候选 `K2`，§5 已签额度以账本转写的「已签执行合同」为准。旧证据不回溯；实现、独立复核与 Unity 证据仍待完成。

## D1 接受裁定（2026-09-30）

Decision: **REVISION_REQUESTED**。D1 任务合同尚不能进入实现。用户 09-30「用户决定：方向选 c-组合…」已授权构思 Part T/Part P 方向；同日「用户答复 §10 四条…」已答 T2、25 m、ACQ 恢复时再定并签发 §5 信封。接受角色不把这些答复扩大为对 `engineering-v1` 轨道的明示批准；本项改变运行时安全边界，按 `docs/roles/acceptance.md`「工程轨道」须先问用户。轨道未获裁定前按研究轨道 fail-closed，任何实现、ID 创建和 Play 均不得开始。§5 仍是提案中的申请表；用户已签额度见账本，待 `ACCEPTED` 时才按其逐字转写为执行合同。

| §7 提请 | D1 裁定 | 依据与边界 |
|---|---|---|
| (a) `engineering-v1` | **待用户明示，未生效** | 本项解除系留钳位并引入围栏，触及运行时安全；接受角色细则要求入工程轨道前问用户。推荐同意工程轨道，以 `K2` 保留异源核对和独立复核；若不同意，构思须按研究轨道重写合同，不得凭申请行实施。见 U1。 |
| (b) `K2` / `K1K2` | **有条件取单候选 `K2`** | §3.3 保留现有帧/命令字段、单位、时间和 `tether_saturated`「本步是否被缆长钳位」定义；关闭时恒 false 是该定义的无缆实例，当前不触发 K1。若 D2 改变上述协议语义，则改为 `K1K2` 并重审。工程轨道获用户同意后才生效。 |
| (c) T2 | **同意** | 用户 §10 第 1 条自填「缺省关闭落点（推荐 T2，证据充分）」，账本已记录 supervisor 读作同意 T2；本轮据此取新增 `config/scenario.untethered.json`、旧 `config/scenario.default.json` 字节不动。落点的实际缺省入口仍须按 R1 修齐。 |
| (d) 冻结棱柱工件第二种查询 | **同意，限只读新用途** | 工件字节、原 BODY-001 走廊查询和原合同均不改；新增机身线段避障由本项 AC-15 与 K2 核对/复核覆盖。 |
| (e) 场景 schema v1 可选字段 | **同意，限 §3.1 的增量** | 缺字段仍开启；关闭时围栏缺失/非法须拒绝。原文件与旧场景回归由 AC-1…4、AC-9 守门。 |
| (f) 矩形围栏信息公平 | **同意，限本默认路线的设计期常数** | §3.4 的 4 个数可作为操作者声明的作业区配置；运行时不得读取目标路线真值或评估器输出，变更作业区须重审安全合同。 |
| (g) 系留开启回归 | **同意 Edit Mode 逐位回归作为该旧路径的 Unity 侧证据** | AC-2/3 与独立 K2 复核共同核实；无缆新路径仍须 AC-21/23 正式 Unity 证据，不能用 Edit Mode 代替。 |
| (h) scenario ID 消耗 | **计消耗** | 创建 `deterministic-loop-untethered` 属 AGENTS.md「执行轨道纪律」的创建 scenario ID；未来实现交接必须 `Consuming=yes`，占唯一消耗性轨道。本轮退修只改文档，`Consuming=no`；额度仅限账本已签的 1 个 ID。 |
| (i) track_loop 线束 | **同意，限本项隔离验证** | 复用 BODY-001 臂 B 线束、冻结初始框；不声称已经接入语言闭环或满足 ACQ 的 Unity 验收。实际场景缺省入口与操作单须按 R1 对齐。 |
| (j) §9.3 基线清单 | **内容方向同意，暂不改写基线** | 设计头、§1/2/4/6/7/10、`PROJECT_BRIEF.md` 与状态板当前绷紧假设须在接受时按 1–9 项同步限定为有缆模式；用户主线目标 §3 原文不改，旧证据不回溯。当前未 `ACCEPTED`，不能把拟议无缆设计写成已生效基线。 |

### 退修要求（下一轮逐条答复）

- **U1 — 用户轨道选择**：请用户明确是否同意这个触及运行时安全的工作项走 `engineering-v1`。推荐同意，理由是 K2 合并候选仍保留 C/R 与 Unity 门，且合同按 Part T/P 分列；若不同意，D2 按研究轨道重新编排 BC/停点。用户原话须由授权发生会话入账，构思/接受角色不得代造。
- **R1 — T2 缺省入口与文件闭集**：§2.1 T2 声称 CLI 缺省、操作单、`runtime/scenario_config.json` 均由新场景生成；但现有 `ScenarioConfig.Load()` 与 `tools/run_track_experiment.py::DEFAULT_SCENARIO` 指向旧 `config/scenario.default.json`，后者不在 §4.1 可改文件集。D2 须逐入口列明何时、由谁选择新场景，以及相应允许修改的文件、AC 测试与旧场景回归；若某入口不转新缺省，须收窄 T2 声称并说明如何满足用户「主线缺省关闭」。不得改旧缺省文件、ACQ 暂停合同或冻结规划器。
- **R2 — AC-15 有效边界**：AC-15 当前对两种系留模式都要求「出围栏、出可达圆…次数均为 0」，却在 §3.2/§3.6 明定无缆模式可越过 35 m、仅有缆模式投影可达圆。D2 须按实际启用的约束逐模式写可证伪断言：有缆检查可达圆、配置有围栏时检查围栏、无缆不检查缆长可达圆；障碍安全两模式均检查。相应修正性质测试夹具和证据指针。
- **接受侧后续动作（不计退修项）**：D2 若可 `ACCEPTED`，接受角色须把 §5 的申请状态与账本签发状态区分，按账本 09-30「用户答复 §10 四条…」逐项转写实现/Unity 两阶段的额度、重试条件和零维度，并把 (h) 的实现 `Consuming=yes` 写入交接；`Unity Edit Mode` 与磁盘估算仅作非信封说明。未接受、未放行 K2 前不使用信封。

open_items: U1,R1,R2

## D2 退修答复（2026-09-30）

构思角色（Fable 子代理，Dispatch-Id `P1-ENG-FRAME-001-D2-20260930T225515Z-97c9`）逐条答复「退修要求」；本轮零消耗，只改本提案与状态板。被改条款在正文原位标 `（D2 修订）`；D1 接受裁定节原文不动。

- **U1 — 用户轨道选择**：已答复。账本 `docs/authorizations.md` 2026-09-30「P1-ENG-FRAME-001 — 用户答复 U1：同意本项走 engineering-v1 工程轨道（supervisor 会话代录）」，`at: 2026-09-30T22:54:33Z`，所选选项 "同意走 engineering-v1 (Recommended)"。本稿只记指针（头部「性质」注、决策记录 DR-10）；头部 `Workflow: engineering-v1` 仍是申请行，是否生效由接受角色在 `ACCEPTED` 时逐字裁定并写进本提案（§7 (a)），本角色未写「已生效」。
- **R1 — T2 缺省入口与文件闭集**：新增 §3.11 逐入口列明现状、取舍、理由、谁/何时选择新场景、可改文件与旧场景复现方式。结论：入口 1 Unity `ScenarioConfig.Load()` 无覆盖回退、入口 2 `run_track_experiment.py::DEFAULT_SCENARIO`、入口 6 Python 生效场景解析器 **(i) 转新缺省**；入口 3 `track_loop` CLI **(ii) 无缺省可转、不新增缺省**（显式传参 + §3.8 一致性校验）；入口 4 覆盖文件 **(ii) 不生成**、Play 要求缺席（撤回 D1 §3.8「由新文件复制生成覆盖」）；入口 7 `language_loop`/ACQ 预检/基础设施工具/BODY-001 冻结消费者 **(ii) 不转**。相应修订：§2.1 T2（声称收窄为三处缺省入口）、§2.3、§2.4、§3.8、§3.9、§4.1 归属表（新增 `tools/run_track_experiment.py`、`tests/test_track_experiment.py`，Part T）、AC-18/AC-20/AC-23/AC-26 修订、AC-27/28/29 新增、§9.1 两条披露。红线核对：`config/scenario.default.json` 字节不动（AC-7）；`P1-ENG-ACQ-001` 暂停合同、操作单与冻结规划器不改；ACQ 操作单 §2.6 由旧缺省 `sed` 生成系留开启覆盖的路径不受影响（Unity 覆盖优先分支逐字不变，AC-27）；AC-2/AC-3/AC-7/AC-8 原文不变。§7 (b)：R1 改动不触及帧/命令协议语义，**不改判 `K1K2`**，维持 `K2`（§3.3 末段、DR-13）。
- **R2 — AC-15 有效边界**：AC-15 改写为三夹具逐模式可证伪断言（F-on 有缆：可达圆 + 走廊，不查围栏；F-off 无缆：围栏，不查可达圆与走廊，并要求 ≥ 100 个越出可达圆的输出候选证明该约束未启用；F-both 合成叠加；障碍安全三夹具均查），证据指针改为四个具名测试方法。同一原则修正：§3.4 表下新增各行生效模式；§3.6 第 5 步按模式写明启用条件；§3.9 plant 镜像按模式对 AC-2/AC-4 向量；AC-10（针对 untethered 文件，有缆场景 manifest 记可达圆、无围栏）；AC-14（两模式内嵌实例各自断言）；AC-19（按模式镜像）；AC-23（无缆 Play 不断言可达圆，越 35 m 帧数如实报告）；§8.4「触边比例」列按模式读。AC 表其余行无两模式同一断言问题（AC-2/AC-3/AC-8 只有缆，AC-4/AC-9/AC-21 只无缆，其余与模式无关）。
- **§5**：保持申请表原样；账本 09-30「用户答复 §10 四条…」已签发，转写为执行合同归接受角色在 `ACCEPTED` 时办理；(h) 已裁「计消耗」，未来实现交接 `Consuming = yes`。
- **接受角色本轮需裁定**：§7 (a)（轨道生效）、(b)（维持 `K2`）、§3.11 各入口取舍、AC-15 三夹具与 AC-27…29 新增、§5 转写。
- **needs_user**：无新的用户层面待决项；§10 四条已答，本轮未产生新的目标、硬件或资源边界变化。

## D2 接受裁定（2026-09-30）

Decision: **ACCEPTED**。头部 `Workflow: engineering-v1` 原为申请；依据账本 2026-09-30「P1-ENG-FRAME-001 — 用户答复 U1：同意本项走 engineering-v1 工程轨道」，接受角色现逐字裁定：**`P1-ENG-FRAME-001` 走 `Workflow: engineering-v1`，自本次 `ACCEPTED` 起生效。** 只接受本任务合同的 Part T/P 范围，不表示实现、复核或 Unity 已通过；§5「已签执行合同」仅转写用户同日「用户答复 §10 四条…」的额度。

| D1 未闭项 | D2 核对结论 | 可证伪点与边界 |
|---|---|---|
| U1 | **闭合** | 账本已有用户明示；本节执行 §7 (a) 生效裁定，工程轨道保留 `C1@K2`、`R1@K2` 与 Unity 门。 |
| R1 | **闭合** | §3.11 的八入口逐项定去留：Unity 无覆盖回退、线束常量、Python 新解析器转新场景；track_loop/回放显式，覆盖不生成；language_loop、ACQ 与冻结消费者不转。新改文件 `tools/run_track_experiment.py`、`tests/test_track_experiment.py` 已进 §4.1；AC-27/28/29 检查新缺省及旧文件显式路径，AC-3/7/8 守旧行为，AC-18/20/23 检查一致性与 Play 来源。`config/scenario.default.json` 字节不动。§9.1 对旧无覆盖操作单和新 main 上 language_loop 回退差异作了披露；恢复 ACQ 仍按用户已答的「恢复时再定」，本项不得代改其暂停合同、操作单、冻结规划器。 |
| R2 | **闭合** | AC-15 三夹具的可达圆/走廊、围栏、机身避障按启用模式分别断言；F-off ≥100 个实际输出候选越可达圆，少于 100 即不满足，足以检出把无缆模式误套可达圆的实现。各模式有效输出才作位置断言，hold 则核 reason 与修饰计数；实现和复核应确保越圆计数来自**非 hold 的有效速度输出**，避免把无命令状态计入证明。§3.4/3.6/3.9、AC-10/14/19/23、§8.4 的模式限定与之相符。 |

§7 (b) 裁定维持 **`K2` 单候选**：三处缺省入口与 `scenario_id` 的场景取值变化不改变帧/控制包字段、单位、坐标或时间语义；`tether_saturated` 仍指本步缆长钳位，无缆时恒 false。§7 (c)–(j) 维持 D1 表内已裁边界；(h) 创建 scenario ID 计消耗，实现交接 `Consuming=yes`。§9.3 的设计基线清单由本轮接受角色同步进 `docs/phase1-single-drone-design.md` 和状态板；其中历史 v0.3.17 与旧研究条款只作适用模式说明，旧证据不改判。`PROJECT_BRIEF.md` 不在 acceptance 的写入白名单，留给具有该文件写权限的 Implementation 在本项 K2 候选中按 §9.3 第 9 项同步：研究起点区分有缆历史与无缆新模式，缺省配置区分三处转新入口和旧文件显式路径，系留球面与绷紧假设限有缆模式，注明实现/复核/Unity 进度；接受核对轮检查该项文档一致性，不在本轮越权改写。

对 §9.1 两项披露，用户已在 §10 第 3 条决定 ACQ 恢复时再定，故本轮 **needs_user: none**。本项实施后，旧 BODY-001 无覆盖操作单在新 main 上不可照旧执行；新 main 上无覆盖的 language_loop 与 Unity 缺省不一致，均作为已知边界在未来恢复/重跑前处理，不在本项偷偷扩大接线。实现者须按 AC-1…29、§4.1 文件围栏及 §5 已签信封推进，并同步上一段限定的 `PROJECT_BRIEF.md` 文字；先写 `docs/evidence/P1-ENG-FRAME-001-K2-handoff.md` 的 §T/§P/§共用逐项自证，再交 `C1@K2`；核对后才交独立复核，Play 仍待复核通过与 workflow §4.5 放行。

open_items: none

## 2026-10-04 补测收集裁定（既有合同，无新D/C/R）

本节保留追认前历史；现行结论见下节「墙钟收尾落实」。

接受按既有AC-21/23核对补测：运行完成两圈+60s，同度量工具R1…R7完整、用户可见机身且记录跟随/起停，安全与来源满足。用户认为启停不是问题；轻微抖动/拐角停止记录，不自动判为缺陷或新性能门。完整按钮墙钟缺证，用户未额外计时、仅估计8分钟内；保守区间跨480s，不能证明预算合规或实际超限。整体不签Unity PASS/DONE；正式Play3/加载2/run2已耗尽、无重试，消耗性交接释放。详细证据与唯一收尾入口见 `docs/evidence/P1-ENG-FRAME-001-supplement-play-20261004.md`「接受裁定与下一动作」及Unity日志「补测收集与接受裁定」。R3既有通过、R1-3范围外OPEN债及测试局限保持，不改AC/参数/信封或研究里程碑。

## 2026-10-04 墙钟收尾落实（既有合同，无新D/C/R）

落实账本同日「用户追认补测按钮墙钟可能超出 480 秒额度、不补测，按 AC-21/23 行为结论收尾…」授权范围(1)–(4)：完整按钮墙钟记「已追认的可能超额：未知、≤532.672385 s 保守上界、可能超过480 s」，不补造按钮实测或在限结论；正式余额各0、不补测。该条仅解除本项墙钟缺证的收尾阻断，不代签验收、不改AC或全局门。

接受角色据实现者证据、最终R3@K2 PASS_WITH_NOTES与同一补测AC-21/23行为/安全/用户目检裁定 `UNITY_PASSED`、Overall `DONE`；Lifecycle在墙钟收尾轮暂留 `ACTIVE`，本轮收口按账本10-04旧Log迁移授权(2)改为 `ENDED`（工作树待协调合并提交）；三证据逐项、AC-25字面非子集的非阻断承接、完整局限/归因及交接见 `docs/evidence/P1-ENG-FRAME-001-supplement-play-20261004.md`「墙钟收尾落实」。R1-3 SCOPE_GAP/OPEN、旧失败/环境ERROR与R3未测HTTP照旧；不关闭研究里程碑、无新增AC/修订，本轮零消耗；旧Log历史迁移同意已入账，当前needs_user为none；本轮不动旧Log、不提交，具体协调接手与最终迁移核对见同一证据「收口与协调批次交接」。

open_items: FRAME_LOG_MIGRATION_COORDINATION, R1-3
