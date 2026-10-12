# P1-M3-BODY-001 批次 1a-β 实现证据

Work ID: `P1-M3-BODY-001`
Batch: **1a-β**（BC-BODY1-3：估计器与策略批次——控制决策逻辑变更，自带
workflow §4.3.1 停点）
Role: 实现（implementation）
Date: 2026-08-07
Gate: 稳定候选，待接受角色停点确认（§4.3.1 五条件 + 条件 5 写入审计）→
独立复核。**Stable candidate: `a234270`**（复核请对该候选做
`git worktree add --detach a234270`；返工前候选 `5340cf6` 经
Acceptance round 5 判定 `STOP_POINT_NOT_CONFIRMED`，保留为返工基线，
未交复核）

**返工记录（2026-08-07，Acceptance round 5 / BC-BODY1-18…20）**：候选
`5340cf6` 的条件 1/4 不成立——估计器先验的来源措辞越界
（`v·turnRate` 被误述为「冻结路线最大向心加速度」，但 `turnRate` 只经
`Quaternion.RotateTowards` 旋转车身朝向、不约束平移）且 body 指令发布
失败路径未 fail-closed。本文件已按 BC-BODY1-18…20 就地改写：§4（先验
措辞）、§5（「纯函数」与唯一发布点的精确定义）、§6（发布失败语义）、
§7–§10（检查、结果、限制、复核范围）、§12（交回事项处置）。

交付物（Acceptance round 4 §H 逐项 + round 5 返工）：
`controller/world_estimate.py`（新）、`controller/body_planner.py`（阈值 +
走廊 + hold 两个 v1 策略）、`controller/track_loop.py`（§2 分支表逐字逐帧
接入 + run log 追加字段 + CLI）、`config/p1-m3-body-001.json`（§3.5 预注册
值维持不变 + 估计器节，见 §4）、**BC-BODY1-12（含 round 4 §F/N2 扩展）的
两处 `782` 勘误修复 + 重生成 margin 工件**（§2）。

---

## 1. 消耗与边界声明

| 项 | 本批次 |
|---|---|
| Play 模式 | **零** |
| scenario / session / run ID | **零**（未创建、未消耗） |
| 配额 / API | **零** |
| Editor 侧查询 | **零**（本批次无 C#/Assets 改动，无需 Editor 遍历） |
| 场景字节 / `Assets/` 字节 | **未改动**（`git diff HEAD --stat -- Assets/` 为 0 行） |
| 运行时协议、帧/观测契约、主指标定义 | **零改动**；run log 为向后兼容追加（不改既有键、不加版本号），manifest 追加 `body_planner` 身份节 |
| `P1-EVAL-001` aspect 修复 | **未并入**（BC-BODY1-17 (b)：独立停点，本批次零触碰） |
| 设计基线 / 提案决策 / 复核文件 / Unity 日志 / 授权账本 | 未触碰 |

Unity Edit Mode **已复跑通过**：`runtime/test-results/p1-m3-body-001-1a-beta-editmode.xml`
`testcasecount="258" result="Passed" failed="0"`（2026-08-07，本批次工作树上
运行）。本批次 `Assets/` 零字节改动（diff 可核），该结果同时复核了 1a-α 的
C# 侧在当批树上无回归。

---

## 2. BC-BODY1-12（含 N2 扩展）勘误修复与工件重生成

**授权边界（round 3 BC-BODY1-12 + round 4 §F (f)）**：唯一准许的改动是实例
计数描述串；`tools/build_m3_corridor.py:54-69` 注释与工件字段不得改动；
重生成后 `scene-body-margin.json` 除描述串与文件哈希外每个数值字段逐字节
不变；证据须给出 diff。

实际改动（`git diff HEAD` 可核，共 4 处字符串、0 处数值）：

| 位置 | 改动 |
|---|---|
| `tools/check_scene_body_margin.py:47` | docstring R5「the **782** road-audit obstacle instances」→「**779**」 |
| `tools/check_scene_body_margin.py:986` | 工件字段 `R5_occluders` 同串 782 → 779 |
| `tools/build_m3_corridor.py:8` | 模块 docstring「the road-audit basis, **782** instances」→「**779**」 |
| `docs/evidence/P1-M3-BODY-001-scene-body-margin.json` | 由修复后的工具 2 机械重生成 |

未触碰核对：`build_m3_corridor.py:54-69` 注释、
`BC_BODY1_4_QUOTED_INSTANCE_COUNT = 782`（BC-BODY1-11 保留的引用值）、
`bc_body1_4_quoted_instance_count` / `bc_body1_4_count_conflict` 工件字段、
R1–R4 与其余全部 R5 文字——全部零改动。

**重生成 diff（BC-BODY1-12 要求的逐字节证明）**：对修复前工件（HEAD 版，
sha256 `1f30d479…8e680`）与重生成工件（sha256 `c72c9407…9576d`）的
`git diff` 只有**一行**——`R5_occluders` 描述串 `782 → 779`；其余每个
字段（含 `identity.obstacle_instance_count: 779`、`c_geom` 各值、可见弧、
测量窗、`C_quality` 投影）逐字节不变。`config/p1-m3-body-001.json` 的
`measurement_window.artifact_sha256` 同步更新为 `c72c9407…9576d`，
`visible_arc_sha256` 不变（`4fe2eea5…df55`）。

复跑验证（本批执行）：

```
python3 tools/check_scene_body_margin.py   # exit 0；重写出工件与盘上逐字节相同
shasum -a 256 docs/evidence/P1-M3-BODY-001-scene-body-margin.json
# c72c940736da9bb1d2924e0d8349f8cfeb08cfb06013e656b72793155f89576d = config 钉住值
python3 tools/build_m3_corridor.py --check
# corridor check OK: 779 prisms, sha256=9e2956ad…c800（不变）
```

---

## 3. 估计器（`controller/world_estimate.py`，提案 §3.4）

常速 Kalman 滤波，状态 `[x, z, vx, vz]`（地面系、米、米/秒），时间戳全部走
共享的 `capture_monotonic_s`（倒退即 fail-closed）：

- **预测**：`F` 常速转移；`Q = q² G Gᵀ` 白噪声加速度模型，`G` 按
  `dt²/2 / dt` 标准式；`q = q_accel_mps2` 单一标量，入 config 冻结。
- **量测**：`z = (x, z)` 取自既有 `geolocate.box_ground_intersection` 的
  `GroundIntersection.point_world_m`；地平面 `0.2` 由
  `--ground-plane-y-m` 传入并由 `_build_body_runtime` 对冻结 scenario 的
  `target.route_world_m[*].y` 逐点强检（不一致 fail-closed）——显式有限
  地平面标定，非目标真值推断。
- **量测协方差**：`σ_px` / `σ_att` / `σ_y` 三源经**解析 Jacobian** 传播
  （像素两轴 + 绕相机 right/up/forward 三轴小转角 + 地面高度），射线数学
  与 `geolocate.py` 逐项对映。测试以中心差分数值微分交叉验证
  （`test_analytic_covariance_matches_numerical_differentiation`，
  6 列 Jacobian 全对，delta `1e-6`）。
- **更新**：Joseph 形式协方差更新，记录 NIS（`last_nis`）供 1c 离线
  NEES/NIS 一致性分析；无观测帧 `advance()` 纯预测。
- **批次 1 范围边界**：无 L1 惯性滑行阶梯、无协方差膨胀规则、无 T1 定时
  器；**没有任何决策消费该估计**（BC-M34-3），协方差只为批次 2 与一致性
  分析记录。

## 4. config 估计器节取值（BC-BODY1-18：事前未标定启发式先验）

1a-α 契约文档 §6 把估计器节留空并登记「`q_accel_mps2` 在已接受提案中没有
预注册值……实现角色不发明数值」。1a-β 初版填入四值，Acceptance round 5
裁定来源措辞越界并以 **BC-BODY1-18** 收束：四值仅冻结为**批次 1 的事前、
未标定启发式先验**——不是实测标定，也不是物理上界；在任何 1c 数据前
冻结，看到数据后不得改，显著不一致只准如实报告并回接受角色。逐值
provenance（写死在 config 的 `*_derivation` 与 `priors_status` 字段并由
测试锁定，含「禁出现 centripetal 表述」的机械断言）：

| 键 | 值 | provenance（BC-BODY1-18 措辞） |
|---|---|---|
| `q_accel_mps2` | `8.377580` | 数据前冻结的启发式 process-noise **尺度**：`2.0 m/s`（冻结 scenario 速度）× `240°/s` 弧度（`LoopTargetVehicle.cs:9`）。`turnRate` 只旋转车身朝向、**不约束平移**，该乘积只是量级尺度，**不是**目标平移的物理上界（round 5 撤回了初版「最大向心加速度」的错误表述） |
| `sigma_att_deg` | `1.0` | 全项目无姿态噪声标定源；`1.0°` 是保守占位，仅此而已 |
| `sigma_y_m` | `0.05` | 仅作保守尺度复用既有 `0.05 m` 空间容差（锚点合同文件）；**不是**由锚点支撑容差推导的地平面噪声 |
| `initial_velocity_sigma_mps` | `2.0` | 以冻结目标速度为尺度的保守初始先验；**不是**测得的标准差 |

**BC-BODY1-18 (d)**：批次 1 的任何决策仍不得消费估计器均值或协方差；
1c 的 NEES/NIS 只称**未标定先验下的一致性诊断**，不得称估计器已校准或
已验证。

§3.5 五个预注册值（`10.0 / 20.0 / 4.0 / 25.0 / true`）与
`command.expires_after_s = 0.4` 维持 1a-α 冻结值，**零改动**；
`maximum_off_nadir_deg` 仍只记来源、运行时从 scenario 读取。

## 5. 策略（`controller/body_planner.py` 下半）

- **`HoldBodyPlanner`（臂A）**：每帧 `hold`，把「现状 `hold_body()` 行为」
  显式化为策略，使两臂走同一逐帧接线、只差 planner（§5.1 配对条款）。
- **`ThresholdBodyPlanner`（臂B）**：§3.5 逐字——触发量与方向只由已发布
  `camera_forward_world` 决定性导出（`theta_applied` / `margin` /
  `bearing`，`maximum_off_nadir_deg` 从冻结 scenario 读入）；`margin <
  trigger` 沿 bearing 以 `v_cmd` 平移，`margin > release` 保持，带内保持
  上一动作（迟滞，单布尔 `_moving`，重放 run log 可逐帧复现）；velocity
  前做系留走廊检查（BC-BODY1-4）：锚点→候选机体位置线段 × 膨胀棱柱
  slab 测试，相交则以 `0.05 m` 步长缩短，仍不可行则 `hold`。
- **失效安全**（§5.3 三条硬性 + 契约 + BC-BODY1-19 精确定义）：`decide`
  无文件/网络 I/O、无墙钟读取、无真值/可见性先验、无外部副作用（机械
  测试逐 token 核对）——该「纯」**不**禁止 §3.5 已冻结的迟滞记忆：策略
  是「有序输入历史 + 固定初态」的确定性函数（`_moving` 构造时 `False`，
  每进程/trial 新实例，按序重放确定性复现）；`platform is None` / 裕度
  不可构造 / `estimate is None` ⇒ `hold`（提案 §5.3 的较严读法与契约 (b)
  同时满足，安全方向）；模块零写入器，无替代决策所有者或旁路——实际
  写入只发生在 `body_entry.py` 的既有 initialize hold 与 `_body_step` 的
  唯一映射点（N6 强化后的子串扫描测试锁定）。
- **BC-BODY1-6 / N3**：策略只读 margin，**零引用 `gimbal_saturated`**
  （机械测试 `test_policies_never_reference_the_saturation_flag`）；
  `margin = 0` 与旗标不等价（0.1° 死区），证据文本不写「当且仅当」。

## 6. `track_loop` 逐帧接入（§2 分支表逐字）

| §2 分支 | 实现 | 锁定测试 |
|---|---|---|
| `initialize()` 内一次性 `hold_body()` | **未触碰**；planner 不在初始化期启动 | `test_threshold_arm_publishes_velocity_and_logs_decision`（init 记录无 `body_planner` 键） |
| `_rate_lifecycle` 非空 | 逐帧回路直接返回，**不发** body 指令；CLI 同时拒绝 `--body-policy` 与 rate2/rate3 同用 | `run_tracker` 前置校验 + `_body_step` 内双保险 |
| `qualification_lifecycle` 非空 | 同上，**不发**（资格协议独占控制） | `test_qualification_lifecycle_owns_body_control` |
| 本帧无观测/无帧包 | `hold()`（reason `no_observation`）；估计器纯预测并记录 | `test_lost_frame_publishes_hold` |
| planner 返回 hold | `hold()` |  hysteresis 测试组 |
| planner 返回 velocity | `body_entry.velocity(...)`，`expires_after_s = 2 / capture_hz = 0.4` | wiring 测试组 |
| 任何异常路径 | `hold()`，异常记入 run log（`planner_error`），不吞 | `test_planner_exception_holds_and_is_recorded` |
| 指令发布失败（round 5 新增行为，BC-BODY1-20 (a)） | 立即尝试**恰好一次**显式 fallback `hold`；成功则 run log 分列原请求（`mode`/`reason`/`velocity_world_mps`）、首错（`publish_error`）与实际发布（`published_mode: hold`、`published_reason: publish_failure_fallback`），运行继续 | `test_first_publish_failure_falls_back_to_hold` |
| fallback 也失败（BC-BODY1-20 (b)） | 保留两次错误（`publish_error` + `fallback_error`），本帧记录落盘后追加终态记录（`BODY_COMMAND_FAIL_CLOSED`），`terminal` 置位、**运行失败关闭**，不再产生后续 planner 决策；进程以既有的 terminal 路径退出（exit 2） | `test_double_publish_failure_terminates_fail_closed` |

接线细节（如实声明）：`_body_step` 只在**最新帧**运行，与云台发布同拍
（`is_latest`），过期堆积帧不重放决策；`PlatformState` 由 v3 帧元数据构造，
任何字段缺失/非有限 ⇒ `None` ⇒ planner `hold`（fail-safe (b)）。发布失败
的两档处置见上表末两行——receiver 的 0.4 s 过期回落是**独立的另一道
保险**，本侧不得以它代替即时 fallback hold（BC-BODY1-20 (d)，两道保险
互不依赖）。CLI 新增 `--body-policy {hold,threshold}` +
`--body-planner-config` + `--body-scenario-config`，缺配或与 rate/qualification
协议同用即拒绝；未传 `--body-policy` 的既有运行**零行为变化**
（`test_no_body_wiring_keeps_records_unchanged`：记录无新键、唯一 body
发布仍是初始化 hold）。

**run log 追加字段**（向后兼容，不改既有键）：`world_estimate`（step /
mean / covariance / valid_at / nis / error / geo_reject_reason）、
`body_planner`（name /
mode / reason / velocity_world_mps / published / published_mode /
published_reason / planner_error / publish_error / fallback_error）；
manifest 追加 `body_planner` 身份节（policy、contract 版本、config 与
scenario 的 SHA-256、expires）。接收器实际生效值仍在帧元数据侧，离线按
`frame_id` 比对（契约 §1 ACK 行）。

## 7. 机械检查（进复核范围，全部可执行）

| 检查 | 结果 |
|---|---|
| 零真值（BC-BODY1-8）：决策路径（`world_estimate.py`、两个策略、`_body_step`/`_platform_state`/`_build_body_runtime`）对真值文件/evaluator 输出零引用 | `MechanicalCheckTests` 逐 token 核对 + grep 复核：新代码零命中（`track_loop.py` 仅有的 `metrics.json` 引用在 `run_tracker()` 的既有 qualification 收尾段——读取运行时 `metrics.json` 及其缺失报错两处，非本批决策路径） |
| 零可见性/遮挡预测引用（BC-BODY1-4） | 同上：`visible_arc` / `scene-body-margin` / `scene_geometry` / `road_data` / `WorldModelHandle` 等 token 在决策路径零命中 |
| N3：策略零引用 `gimbal_saturated` | `body_planner.py` 仅 `PlatformState` 的 `gimbal_saturated: bool` 字段声明（run log 诊断需要）与「The margin is *not* equivalent to ``gimbal_saturated``」死区 docstring 两命中，两个策略类零命中 |
| 走廊工件唯一用途 | 全库 grep：`corridor-prisms` 仅被 `build_m3_corridor.py`（构建/校验）、`config/p1-m3-body-001.json`（哈希钉住）、`body_planner.py`（loader）、`track_loop.py`（构建期加载）、测试引用；工具 2 不读；运行时唯一查询 = 声明的「线段 × 棱柱相交 + 缩短/hold」 |
| `decide` 纯函数（BC-BODY1-19 (a) 精确定义） | 机械测试：`open(` / `json.load` / `Path(` / `time.` / `input(` 零命中；迟滞记忆为冻结例外（单 `_moving` 布尔，固定初态，有序重放复现） |
| 两道保险互不依赖 + BC-BODY1-20 | receiver 过期回落（C# 既有，未触碰）与 planner `hold` 各自独立；发布失败的即时 fallback hold 是**本侧** fail-closed 义务，不以 receiver 过期回落代替；双写失败即终态退出（exit 2 路径），两个聚焦测试锁定命令槽终态、run-log 记录与进程是否继续 |

## 8. 实际运行的命令与结果

```
.venv-track/bin/python -m unittest tests.test_m3_body_policy   # 29/29 OK
.venv-track/bin/python -m unittest tests.test_m3_body_tools    # 56/56 OK
.venv-track/bin/python -m unittest discover -s tests           # 424 ran / 1 failure
python3 tools/check_scene_body_margin.py                        # exit 0，工件字节不变
python3 tools/build_m3_corridor.py --check                      # exit 0，779 棱柱哈希不变
# Unity Edit Mode（batchmode，本批次工作树）：
#   -runTests -testPlatform EditMode -testFilter TetheredTracking.Tests
#   -testResults runtime/test-results/p1-m3-body-001-1a-beta-editmode.xml
```

| 检查 | 结果 |
|---|---|
| 新增/修改 Python 测试 | **85/85 通过**（policy 29 + tools 56；round 5 返工新增 BC-BODY1-20 (c) 两个聚焦测试） |
| 完整 Python 套件 | **424 项，1 项失败**——`tests/test_check_docs.py` 既有失败，与本批次无关（两文件零触碰；1a-α §8 / round 3 §D 事项 5 同一归因，仍待用户授权的协调批次修复） |
| Unity Edit Mode | **258/258 通过**（`runtime/test-results/p1-m3-body-001-1a-beta-editmode.xml`，2026-08-07 本批次工作树；round 5 返工零 C# 改动，该结果继续有效） |
| 场景 / config 既有字节 | 除 `p1-m3-body-001.json` 自身的 `batch` 字段、margin 工件哈希与估计器节外，零改动 |

## 9. 未验证项与已知限制

1. **估计器从未实跑**：KF/Jacobian 只有合成元数据上的单元测试；四个先验
   是 BC-BODY1-18 冻结的**事前未标定启发式值**（§4），载体上的实测残差
   分布、NEES/NIS（只称未标定先验下的一致性诊断）属 1c 义务；显著不一致
   如实报告并回接受角色，不调参重报。`σ_px` 的两条外推风险
   （`truth_directed_scouting`、SCENE-004 近天底窄斜距带）按 1a-α 原文
   继续有效。
2. **策略效果零运行时证据**：阈值/走廊/迟滞全部只有单元测试与 1a-α 的
   准静态投影；机体 4 m/s 与云台 120°/s 动力学下的真实行为由 1c 实测。
3. `_body_step` 只在最新帧运行（与云台同拍）；积压帧不重放决策——5 Hz
   帧率与 20 Hz receiver 轮询下，`expires_after_s = 0.4 s` 提供约 2 帧
   冗余，如实登记。
4. **发布失败路径只有合成故障注入测试**（`OSError` 桩），未在真实运行
   中触发过；双写失败的终态退出复用既有 `terminal` 机制（exit 2），
   其行为本身有既有测试覆盖。
5. `estimate is None ⇒ hold` 采用提案 §5.3 的较严读法：估计器初始化前
   （首个可用量测之前）臂B 恒 hold——安全方向，但这意味着**估计器 config
   缺失时整个 body 运行时被 fail-closed**。
6. 锚点位于行车走廊内（BC-BODY1-16 (c)）继续作为 1c 证据与论文素材的
   具名限制，机制表述以 round 4 §B 为准（双重保护：collider 即毁 +
   遮挡构建显式排除根）。
7. 本批次**未做**任何 Play / 目检；1b COORD-005 人眼保真检查未到期，且其
   前置现在还包括 `P1-EVAL-001` 复核 PASS（BC-BODY1-17 (c)）。

## 10. 给复核角色的复核范围

按 round 4 §H 预告逐项落点：

1. **零真值 / 零可见性引用两条机械检查**——§7 的 token 清单与测试是否
   真的覆盖**全部**新代码路径；`track_loop.py` 既有 `metrics.json` 引用
   （`run_tracker()` 的 qualification 收尾段两处）确属 qualification
   收尾而非本批决策路径。
2. **§2 分支表逐字符合**——逐行对读 `_body_step` / `initialize()` /
   `run_tracker` 前置校验与 §2 七行表；两道保险是否仍互不依赖。
3. **走廊工件唯一用途**——grep 复核 §7 第四行；`load_corridor_prisms`
   的 fail-closed 校验（schema/计数/逐坐标有限性/反向界）有无静默放宽。
4. **N3**——两个策略类对 `gimbal_saturated` 零引用（注意两处合法命中
   是 `PlatformState` 字段声明与禁令 docstring）。
5. **BC-BODY1-12/N2 勘误未越界**——diff 只有计数描述串；`:54-69` 注释、
   `BC_BODY1_4_QUOTED_INSTANCE_COUNT`、工件字段零改动；重生成工件除
   R5 串外逐字节不变（本文件 §2 给了 diff，请独立复算哈希）。
6. **估计器**——解析 Jacobian 与 `geolocate.py` 的逐项对映；Joseph 形式
   更新；`del estimate` 与「策略零读估计器」的机械测试是否足够；
   `capture_monotonic_s` 倒退 fail-closed。
7. **BC-BODY1-18 措辞一致性**——config `*_derivation` / `priors_status`、
   本文件 §4、契约文档 §6 三处逐字对读：四值只称「事前未标定启发式
   先验」，无「向心加速度/物理上界/实测标定」残留表述（测试含
   `assertNotIn("centripetal", ...)` 机械断言）。
8. **BC-BODY1-19 精确定义落地**——模块/类 docstring 与契约 §1/§1.1 的
   「纯函数」「唯一映射点」表述；迟滞是否确为单 `_moving` 布尔、固定初态、
   有序重放可复现；全库是否真的没有第三个 body 发布点。
9. **BC-BODY1-20 fail-closed**——`_body_step` 发布块逐行对读：(a) 首错后
   恰好一次 fallback hold、原请求与首错和实际发布是否分列（原 velocity
   不得被记成已发布）；(b) 双错后两错保留、本帧记录落盘、终态记录
   `BODY_COMMAND_FAIL_CLOSED`、`terminal` 置位不再产生后续决策；(c) 两个
   聚焦测试是否真的锁定命令槽终态 / run-log / 进程继续与否；(d) 未以
   receiver 过期回落代替本侧义务。
10. **run log 追加的向后兼容性**——既有键零改动（测试只锁定
   `published_gimbal_command` / `capture_monotonic_s` 两个代表键，请抽查
   全键集）；manifest 新节只在 `--body-policy` 运行时出现；新增键
   `published_mode` / `published_reason` / `fallback_error` 均为追加。

复核角色只在一次性 worktree 接触实现代码，发现缺陷只写 `docs/reviews/`，
不改一行。

## 11. 给用户的 Unity 观察点

**本批次不请求任何 Unity 操作。** 1c 采集的四门现为：1a-α 复核 PASS ✅ +
BC-M34-4 归因 ✅、**1a-β 复核 PASS（本停点）**、**`P1-EVAL-001` 复核
PASS**（BC-BODY1-17 (c) 新增）、1b COORD-005 人眼保真检查、用户 Play；
首次 Play 仍是 BC-BODY1-15 的臂A trial 1 退化门（整圈 `C_geom ∈
[0.5645, 0.95)` 才释放其余 9 次 Play）。

## 12. 交回接受角色的待裁事项

**无未决事项。** 初版的唯一交回事项（估计器取值处置，原 §12 事项 1）已由
Acceptance round 5 裁定：`q_accel_mps2` 的「最大向心加速度」来源主张撤回，
四值按 BC-BODY1-18 冻结为事前未标定启发式先验，config / 本文件 §4 / 契约
§6 三处措辞已逐处对齐（§10 第 7 条请复核角色核验一致性）。
