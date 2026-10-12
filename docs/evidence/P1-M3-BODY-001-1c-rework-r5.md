# P1-M3-BODY-001 1c 返工 round 5（Acceptance round 15 §B 四条）

批次性质：round 15 `REVISION_REQUESTED_1C_REWORK_ROUND_5` 的窄返工——
只闭合 init/stage 唯一绑定与三个隔离反例。**零正式 Play、零 trial/run
ID、零运行指标、零配额。** round 14 及更早已成立的 capture 数值绑定、
ID/policy/planner 组合、compare、容差、H2、自包含复算、指标公式与 C#
载体未动（工具/测试/文档批次，零 C# 改动）。

## 1. 四条 binding 要求落点

| round 15 §B | 落点 |
|---|---|
| 1 init 身份与 stage 唯一绑定 | `_check_identity`：manifest `init.frame_id` 必须存在、类型恰为非 bool `int` 且 `>=0`，否则 `manifest_init_frame_id_invalid:<repr>`（不再允许流进 receipt 成 `null`）。`analyze_trial`：`compute_stage` 逐帧枚举为 `init`/`update`，其他取值或缺失即 `frame_compute_stage_invalid:<frame>:<stage>`；init 行数 ≠ 1 即 `init_frame_record_count:<n>`；唯一 init 行 `frame_id` ≠ manifest 值即 `init_frame_id_mismatch:<frame>!=<manifest>`；零条 update 仍为 `no_update_frame_with_expected_planner` |
| 2 在可信 stage 划分后核对 planner | planner 核对整体移到划分之后：唯一 init 行可缺 planner，存在则必须是 `Mapping` 且 `name` 等于期望 planner（`init_frame_planner_mismatch:<frame>`）；`update_records` 每条必须是 `Mapping` 且名称相等（`update_frame_planner_mismatch:<frame>`）。不再有「非 init 一律视作 update」的隐式分支——stage 枚举先于任何 planner 判断 |
| 3 三个隔离反例 | `update_frame_planner_mismatch` 改为只改 `compute_stage == "update"` 行（init 行原样保留），并断言错误前缀为 `update_frame_planner_mismatch:`；新增独立测试 `test_missing_manifest_init_frame_id_fails_closed`（删 manifest `init.frame_id`）与 `test_update_row_relabelled_init_fails_closed`（把原 update 帧 7/8 改标 init 并删 planner）。三者均断言 `AnalysisError` 且 `m3_body_analysis.json` 未生成；round-14 六个命名反例全部保留 |
| 4 范围冻结 | 改动仅 `tools/analyze_m3_body.py`（上述两项）、`tests/test_analyze_m3_body.py`、本文件与操作单/前一轮证据的声明。零 C# 改动；容差、H2、compare、指标公式、capture 绑定、ID/policy/planner 组合一字未改；未放宽 §B 任何字面条件 |

补充锁定（同属 §B.1 的字面条件，此前无测试覆盖）：`missing_compute_stage`、
`unknown_compute_stage`、`no_init_frame_record`、
`init_frame_id_differs_from_manifest` 四个 fail-closed 用例，均带命名
前缀断言。只增反例、不放宽任何条件。

## 2. 改动清单（相对被退回候选 `977a997`）

| 文件 | 内容 |
|---|---|
| `tools/analyze_m3_body.py` | manifest `init.frame_id` 类型/范围强制；`compute_stage` 枚举划分 + init 唯一性 + init ID 绑定；planner 核对后置到划分之后 |
| `tests/test_analyze_m3_body.py` | `_patch_frames` 只改指定 stage 的行；`EXPECTED_ERROR_PREFIX` 命名前缀断言；修正 `update_frame_planner_mismatch`；+2 独立测试、+4 fail-closed 用例（共 24 个测试）；生产重放夹具 frame 0 改为 init（与 manifest `init.frame_id=0` 和生产 `event="INIT"` 一致） |
| `docs/evidence/P1-M3-BODY-001-1c-preflight.md` | 操作单 revision 6（init/stage 唯一绑定；§3 步骤 5 补写划分顺序） |
| `docs/evidence/P1-M3-BODY-001-1c-rework-r4.md` | 顶部加 round-15 更正块（「缺 stage 按 update 处理更严」被证伪） |

## 3. 实际运行的命令与结果

```bash
.venv-track/bin/python -m unittest tests.test_analyze_m3_body   # 24/24 OK
.venv-track/bin/python -m unittest discover -s tests            # 448 ran / 1 既有失败
# Unity Edit Mode（batchmode，6000.4.1f1，本批次工作树）：
#   -runTests -testPlatform EditMode -testFilter TetheredTracking.Tests
#   -testResults runtime/test-results/p1-m3-body-001-1c-rework5-editmode.xml
#   testcasecount="267" result="Passed" failed="0"
```

- 全套 448/1：唯一失败仍是已登记的既有 infra 债务 `test_check_docs.py`
  （本批次未触碰 `tools/check_docs.py` 与 `tests/test_check_docs.py`）。
  条目数由 446 升到 448 = 本批次新增的两个独立测试。
- Edit Mode 267/267（本批零 C# 改动，回归确认）。

### 3.1 证伪运行（round 15 §A 原样复现 + 变异测试）

| 检查 | 结果 |
|---|---|
| §A.1 把 frame 0…44 全改标 `init` 并删 planner、只留 frame 45 为 update | `AnalysisError(init_frame_record_count:45)`，未生成 analysis |
| §A.1 删除 manifest `init.frame_id` | `AnalysisError(manifest_init_frame_id_invalid:None)`，未生成 analysis |
| §A.2 只改 update 行的 planner 名 | `AnalysisError(update_frame_planner_mismatch:1)`（不再先报 init 分支） |
| 变异：删除 update 分支的 planner 检查 | `update_frame_planner_mismatch` 用例失败（`AnalysisError not raised`）——该反例确实由 update 分支承载 |
| 变异：去掉 init 唯一性与 manifest ID 类型检查 | 三个新用例失败——两个新测试确实由本轮新增逻辑承载 |

（变异运行在临时副本上进行，运行后已还原；证伪脚本在会话 scratchpad，
不入库。）

## 4. 未验证项与已知限制

- 生产 `track_loop` 中 `event == "INIT"` 只在初始化路径出现一次
  （`controller/track_loop.py:375`），重锚定走 update 路径，因此「恰一条
  init」与生产一致；终态错误记录写 `compute_stage: null`，在新规则下
  fail closed——该类 run 本就是无效 trial，从严拒绝不构成合法路径损失。
- 本轮仍是离线分析工具与测试；十次 Play、正式 run ID 与指标未释放。

## 5. 给复核角色的复核范围

1. `_check_identity` 的 manifest `init.frame_id` 类型/范围判定是否无
   绕过路径（含 `True`/浮点/负数/缺字段）。
2. `analyze_trial` 的 stage 枚举划分：是否恰好一条 init、是否绑定
   manifest ID、其余是否强制 `update`，以及 planner 核对是否确实在划分
   之后发生（不存在「非 init 视作 update」的残留路径）。
3. 三个隔离反例是否真的在各自声明的分支失败（前缀断言），round-14 六个
   命名反例是否全部保留且仍在原阶段失败。
4. 生产重放夹具 frame 0 改为 init 后，H1/窗口/effort/estimator 复算量与
   round 4 是否一致（该夹具全程单一 `hold` 模式，`planner_switches`
   不受影响）。
