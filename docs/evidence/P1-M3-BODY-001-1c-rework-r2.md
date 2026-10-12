# P1-M3-BODY-001 1c 返工 round 2（Acceptance round 12 §B 七条）

批次性质：round 12 `REVISION_REQUESTED_1C_REWORK_ROUND_2` 的返工。
**零正式 Play、零 trial/run ID、零运行指标、零配额。**

## 1. 七条 binding 要求落点

| round 12 §B | 落点 |
|---|---|
| 1 生产输入先行 | 阈值读取改 `evaluation.tracking_iou_threshold`；新增 `FrozenConfigIntegrationTests`：直接加载 checked-in `scenario.default.json` / `p1-m3-body-001.json` / margin 工件，在真实路线（周长 212.9706 m 复核一致）与真实 ~559 帧规模（>128 保留窗、零元数据文件）下跑通并 `--verify` 逐字节一致 |
| 2 run 目录自包含 | 载体 v2 逐帧自带机体位置/AppliedVelocity/饱和，分析**零依赖** `runtime/frames` 元数据（128 帧保留不再能截断分析）；`analyze_trial` 先把共享 truth 流 create-once 复制进 run 目录再分析，`--verify` 仅从 run 目录重算并与存档逐字节比对；测试 `test_verify_reruns_byte_identical_after_shared_input_replaced` 模拟 A2 覆盖共享 truth 后 A1 仍可重跑 |
| 3 路线定义域与权重 | 全部指标权重为里程梯形权重 `trapezoidal_weights`（首帧保留 `[0, m_0]`、末帧保留 `[m_n, 域端]`，权重和恰为域长；单测锁定）；capture 墙钟不再是任何权重；`C_quality`/分母只取 `geometrically_visible` 且 `truth_box_available` 的窗内样本（证伪测试：遮挡但有框的两帧不进任何分母） |
| 4 H2 真配对 | `compare_arms` 按冻结 0.5 m 网格取同位置配对差（面积/最小边 B−A、中心误差 A−B），逐 run-pair 取配对差中位数，要求 5/5 run-pair 中位数同号为正且汇总中位改善为正；`test_true_pairing_rejects_naive_median_difference` 锁定反例 A=[1,2,3] vs B=[0.5,2.5,2.5]：naive 中位差 +0.5 会误判通过，真配对中位数 −0.5 判失败 |
| 5 实际代价与完整身份 | 载体 v2 记录 `body_world_*_m` 与 `applied_velocity_*_mps`（plant `AppliedVelocity`，钳位后真值）；effort = Σ‖v_applied‖·Δt_sim（仿真时间差，暂停安全；测试锁定 requested 4 m/s vs applied 1 m/s 时 effort 只认 applied）；receipt 锁定并核对 scenario/hash、arm policy∈{hold,threshold}、body config、tracker、condition、track_id、地平面、冻结初始框；compare 逐项核对十 run 跨 run 身份；分析与 compare 产物均 create-once |
| 6 容差可归因 | `START_MILEAGE_TOL_M = 0.5`：1/5 Hz × 2.0 m/s = 0.4 m 首帧里程上界 + 帧定时/float 裕量，钉在冻结 waypoint 切换粒度 0.5 m；`OFF_ROUTE_TOL_M = 1e-3`：车辆沿折线直线行驶，离线距离纯 float32 误差，|坐标|≤256 m 处 1 ulp ≈ 3.05e-5 m，1e-3 ≈ 30 ulp；推导同时写入工具 docstring 与分析 JSON `tolerances` 节 |
| 7 证伪测试 | 17 个测试覆盖：真实规模/零元数据（集成）、暂停 +300 s 单调钟 gap（指标逐节相等）、遮挡但有框、A2 覆盖后 A1 `--verify` 逐字节重跑、requested≠applied、错误 arm policy/tracker/地平面/缺 init 框、跨 run 身份不符、H2 反例、无单圈/两圈/真值缺口/起点偏移/既有 fail-closed 组 |

## 2. 改动清单（相对被退回候选 `1c26785`）

| 文件 | 内容 |
|---|---|
| `Assets/TetheredTracking/Scripts/CoverageEvaluator.cs` | `M3BodyTruthRecord` 升 `p1-m3-body-truth/v2`：+`body_world_x/y/z_m`、`applied_velocity_x/y/z_mps`（取自 `scenario.Drone.transform.position` 与 `Drone.AppliedVelocity`）；builder 签名与 fail-closed 非有限 guard 同步扩展 |
| `Assets/TetheredTracking/Tests/EditMode/M3BodyTruthEditModeTests.cs` | 三处调用改 v2 签名；新增 applied-velocity 非有限用例与字段断言 |
| `tools/analyze_m3_body.py` | 按 §1 全面重写（run 目录自包含 + `--verify`、里程梯形权重、真配对 H2、完整身份核对、可归因容差、阈值键修正） |
| `tests/test_analyze_m3_body.py` | 重写为 17 个测试（含 §B.7 全部证伪用例与真实冻结配置集成测试） |
| `docs/evidence/P1-M3-BODY-001-1c-preflight.md` | 操作单 revision 3（载体 v2、自包含收集/`--verify`、口径节） |

真值单向流动不变：`controller/` 零引用 `m3_body_truth`（机械测试）；
v3 元数据键零新增；RATE/qualification 协议产物路径零改动。

## 3. 实际运行的命令与结果

```bash
.venv-track/bin/python -m unittest tests.test_analyze_m3_body   # 17/17 OK
.venv-track/bin/python -m unittest discover -s tests            # 441 ran / 1 既有失败
# Unity Edit Mode（batchmode，6000.4.1f1，本批次工作树）：
#   runtime/test-results/p1-m3-body-001-1c-rework2-editmode.xml
#   testcasecount="267" result="Passed" failed="0"
```

- 全套 441/1：唯一失败仍是已登记的既有 infra 债务 `test_check_docs.py`
  （本批次未触碰该两文件）。
- Edit Mode 267/267（含载体 v2 的 4 个聚焦测试）。

## 4. 未验证项与已知限制

- 载体 v2 的 Play 行为仍由单测/复核覆盖；首次真实 Play 产物由 trial 1
  绑定工具机械核验（receipt + `--verify` 设计即为此）。
- `--compare` 的 H1 仍只逐 trial 报告臂 A 值（设计未冻结跨 trial 聚合）；
  H2 网格取 `body_config.measurement_window.route_sample_spacing_m`
  （0.5 m，冻结值），格心配对容差半格（机械规则，已写入工具 docstring）。
- `START_MILEAGE_TOL_M` 的推导覆盖正常启动 cadence；若真实首帧因场景
  加载延迟超过 0.5 m 里程，工具 fail-closed 报
  `trial_not_started_at_route_zero` 而非静默通过——此时按纪律回
  Acceptance，不就地放宽。

## 5. 给复核角色的复核范围

1. v2 载体字段与 plant/evaluator 语义逐键对映；`AppliedVelocity` 确为
   钳位后值；截断/门控/guard 不回退。
2. `analyze_m3_body.py`：梯形权重边界补全数学；`[P, 2P)` 恰好一圈；
   窗/整圈域构造；`_per_position_series` 最近点规则；H2 判定式与
   BC-BODY1-5/-14 逐字对读；身份核对覆盖 round 12 §B.5 清单。
3. 自包含性：收集 create-once、`--verify` 真只读 run 目录、字节一致
   比较无时间戳类不确定字段。
4. 测试是否真实覆盖 §B.7 清单（特别是 650 帧规模、暂停 gap、反例）。
5. 容差推导是否如声明只可归因于冻结量。
