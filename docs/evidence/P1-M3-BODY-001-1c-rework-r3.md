# P1-M3-BODY-001 1c 返工 round 3（Acceptance round 13 §B 五条）

> **round 14 更正（2026-08-08）**：本文件 §1 第 4 行与 §5 第 4 条曾把
> 身份/顺序链写成已闭合。Acceptance round 14 证明四处 false-pass：
> tracker 帧缺 `capture_monotonic_s` 被跳过、manifest
> `body_planner.policy` 与逐帧 `body_planner.name` 未核对、compare 未
> 核对 analysis 内容归属路径（A1 字节复制到 A2 仍过）、`init_frame_id`
> 未进 compare。这些声明以 round-4 返工后的
> `docs/evidence/P1-M3-BODY-001-1c-rework-r4.md` 为准；容差、H2 指示量、
> 自包含复算三项在 round 14 被判成立，不受影响。

批次性质：round 13 `REVISION_REQUESTED_1C_REWORK_ROUND_3` 的窄返工。
**零正式 Play、零 trial/run ID、零运行指标、零配额。** round 11/12 被判
成立的落点未动；本批只改 `tools/analyze_m3_body.py`、
`tests/test_analyze_m3_body.py` 与操作单/证据（C# 零改动——round 13
未对载体提缺陷，Edit Mode 复跑仅为回归确认）。

## 1. 五条 binding 要求落点

| round 13 §B | 落点 |
|---|---|
| 1 按生产转点规则推导容差 | 撤回「离线仅 float32」前提。`OFF_ROUTE_TOL_M = 0.5 + 1e-3`：生产 `LoopTargetVehicle.Step`（`LoopTargetVehicle.cs:65-81`，`:72` 为 <0.5 m 切点且不吸附）切角弦与理想折线的最大偏离严格小于切换距离（垂直情形 `d·L/sqrt(d²+L²) < d`；round-17 §B.5 勘误，原文误写为 `d·L/(L+d)`，结论与数值不变），+1e-3 m float32 投影余量（|坐标|≤256 m 处 1 ulp ≈ 3.05e-5 m，约 30 ulp）；推导与源位置写入工具 docstring 和分析 JSON `tolerances` 节。集成测试用**逐句等价的 Step Python 重放**（`replay_loop_target`，切点帧不移动），在真实默认路线、130 s/5 Hz、**650 帧**规模上跑通；合法切角（实测最大偏离 >0.01 m 存在且 <0.501 m）不失败，超界注入（+0.6 m）必报 `truth_off_route` |
| 2 恢复冻结 H2 第三分量 | `c_quality_series` 第三分量改为指示量 `1[min_side ≥ 20 px]`，compare 组件键 `min_side_ge20_share`，配对差为指示量 B−A；反例测试：A=21/B=22 px（指示量 1→1）判改善恰为 0、分量不通过、verdict 不得 `H2_SUPPORTED` |
| 3 真自包含复算 | 首次分析 create-once 收进 run 目录：truth 流 + scenario/margin/body config/re-anchor/tracker model spec 五类原始字节（tracker 二进制以 manifest 双模型 SHA-256 代表并与收集 spec 对核）；之后所有读取（含 `--verify`）只碰 run 目录；receipt 只哈希 run-bound 副本。验收测试 `test_verify_is_run_directory_only`：删除全部外部配置与共享 truth 后 `--verify` 逐字节一致 |
| 4 身份/来源/顺序/create-once | truth 逐条 `scenario_id` 核对（foreign-play 即失败）；truth↔tracker 逐帧 `capture_monotonic_s` 绑定核对；manifest schema、tracker 身份+双模型 SHA、re-anchor `config_sha256`、policy↔planner 对应（hold↔hold-v1、threshold↔threshold-corridor-v1）、condition/track/地平面/init 框全部进 receipt 与十-run compare；十个正式 ID 冻结为 `p1-m3-body-001-arm-a-trial-1..5`/`-arm-b-trial-1..5`，compare 机械拒绝重复/错序/错臂；compare 输出含十份 analysis 的 SHA-256；`--compare` 必须 `--output` 到不存在的新路径（stdout 不再是正式成功路径） |
| 5 证伪测试 | 20 个测试，新增/锁定：650 帧生产转点重放、21→22 px 零改善、重复/错序/错臂 trial、foreign truth scenario、篡改 tracker 模型 SHA/re-anchor/body planner 身份、capture 绑定错位、删除全部 run 外依赖后的 `--verify`、compare 缺 create-once 输出/输出已存在；证据与 runbook 措辞同步（不再把理想插值测试称为生产规模验证） |

## 2. 改动清单（相对被退回候选 `220a3af`）

| 文件 | 内容 |
|---|---|
| `tools/analyze_m3_body.py` | 上述五项；analysis/compare schema 升 v3（series 第三分量语义变化 + receipt 扩展 + compare 输出含哈希） |
| `tests/test_analyze_m3_body.py` | 重写为 20 个测试（§B.5 清单全覆盖 + 生产 Step 重放器 `replay_loop_target`） |
| `docs/evidence/P1-M3-BODY-001-1c-preflight.md` | 操作单 revision 4（十 ID 冻结、六类 run-bound 输入、compare create-once 输出、容差与指示量口径） |

C# 零改动；`CoverageEvaluator` 载体 v2 与 Edit Mode 4 测试在 round 13
未被指缺陷，回归确认通过。

## 3. 实际运行的命令与结果

```bash
.venv-track/bin/python -m unittest tests.test_analyze_m3_body   # 20/20 OK
.venv-track/bin/python -m unittest discover -s tests            # 444 ran / 1 既有失败
# Unity Edit Mode（batchmode，6000.4.1f1，本批次工作树）：
#   runtime/test-results/p1-m3-body-001-1c-rework3-editmode.xml
#   testcasecount="267" result="Passed" failed="0"
```

- 全套 444/1：唯一失败仍是已登记的既有 infra 债务 `test_check_docs.py`
  （本批次未触碰该两文件）。
- Edit Mode 267/267（本批零 C# 改动，回归确认）。

## 4. 未验证项与已知限制

- `replay_loop_target` 是生产 `Step` 的逐句等价 Python 移植（平移/切点/
  不移动分支），用于测试夹具；它不替代真实 Play——trial 1 的真值由
  载体记录并由工具机械核验。
- 转点重放的固定 dt=0.2 s 是采集节奏等价重放；真实 Play 的
  `Time.deltaTime` 抖动使切点距离 **更贴近 0.5 m 的下方**（步长越细，
  越可能在刚跨过阈值时就切换），严格 `< 0.5 m` 的上界与 dt 无关，容差
  不受影响。〔round-17 §B.5 勘误：原文写作「只会使切点距离更小」，方向
  说反；`OFF_ROUTE_TOL_M = 0.501` 与实测结论不变。〕
- compare 的十 ID 冻结在操作单 revision 4；trial 1 证据将记录实际
  init 框并供 compare 跨 run 核对。

## 5. 给复核角色的复核范围

1. 容差推导：弦偏离 < 切换距离的几何论证与 `LoopTargetVehicle.cs:72`
   语义；`replay_loop_target` 与生产 `Step` 的逐句对读。
2. 指示量恢复：`c_quality_series` 第三分量语义、compare 组件键与
   BC-BODY1-1/-5/-14 逐字对读；21→22 px 反例。
3. 自包含：六类 run-bound 输入的 create-once 收集与 `--verify` 的
   run-directory-only 性质；receipt 哈希覆盖完整性。
4. 身份/顺序：receipt 与 compare 的身份键清单是否覆盖 round 13 §B.4
   逐项；十 ID 冻结与错序/重复拒绝。
5. 测试是否真实覆盖 §B.5 清单且数值独立可复算。
