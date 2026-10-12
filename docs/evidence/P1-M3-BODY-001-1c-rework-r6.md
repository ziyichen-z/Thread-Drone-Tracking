# P1-M3-BODY-001 1c 返工 round 6（Acceptance round 17 §B 六条 / Review F1+F2）

批次性质：消费独立 Review round 3 `REWORK_REQUIRED` 后的窄返工——只修
F1（测量窗来源未绑定）、F2（操作单流程被分析工具确定性误杀）与 N11
文字。**零正式 Play、零 trial/run ID、零运行指标、零配额。** 零 C#、零
config、零 scenario 改动；容差数值、H2、指标公式、compare 其余语义、
init/stage 绑定与 round 14/15 全部反例保留。

## 1. 六条 binding 要求落点

| round 17 §B | 落点 |
|---|---|
| 1 F1 硬门 | `analyze_trial` 在 scenario identity 检查之后、**使用测量窗之前**调用 `_require_pin_equal`：`sha256(run/margin.json)` 必须等于 `body_config.measurement_window.artifact_sha256`，`margin.visible_arc.sha256` 必须等于 `visible_arc_sha256`。新助手 `_sha256_hex` 要求两侧都是 64 位小写十六进制（缺失/类型错/大写/非法字符 → `sha256_not_hex64:<name>`），不等 → `margin_artifact_pin_mismatch:` / `visible_arc_pin_mismatch:`。receipt 仍写实际两哈希；`identity_keys` 由 13 键增至 15 键（加 `margin_artifact_sha256`、`visible_arc_sha256`）。`_collect_inputs` 的 create-once 行为未改——预置字节由 pin 拒绝，而不是靠收集逻辑 |
| 2 F1 反例 | `test_preseeded_margin_window_is_rejected`：run 目录预置 scenario identity 合法、窗口改 `[0,10]` 的 margin，首次分析报 `margin_artifact_pin_mismatch:` 且不生成 analysis。compare：`test_margin_artifact_sha_enters_compare_identity`（十份中仅 A4 的 `margin_artifact_sha256` 不同）与 `test_visible_arc_sha_enters_compare_identity`（仅 B3 的 `visible_arc_sha256` 不同）均必须失败。**happy 夹具带真 pin**：`TrialFixture._write_configs` 的 body config 现在像生产 config 一样写入两个真实 pin，未靠删 pin 规避 |
| 3 F2 分类 | `_counter` 强制 `backlog_count`/`skipped_count` 为非 bool 非负整数（否则 `frame_counter_invalid:`）。唯一 init 行两者必须为 0（`init_frame_counters_not_zero:`）。每条 update：`skipped_count=0` → **decision row**，必须有 `body_planner` mapping 且 `name` 等于期望 planner（`update_frame_planner_mismatch:`），`backlog_count` 可 0 可正；`skipped_count=1` → **catch-up row**，必须 `backlog_count>=1`（`catch_up_frame_backlog_invalid:`）且**无** planner（`catch_up_frame_carries_planner:`）；其他值 → `update_frame_skipped_count_invalid:`。全 run 至少一条 decision update（`no_decision_update_frame`）。`track_loop`、控制 cadence 与 planner 决策零改动 |
| 4 F2 反例与真实启动重放 | 夹具全帧补两个生产计数字段。(a) `test_two_frame_catch_up_batch_is_admissible`：frame 11 `backlog=1/skipped=1` 无 planner + frame 12 `backlog=1/skipped=0` 有 planner，分析成功且九个复算量节与基线**逐字段相等**；(b) `decision_update_without_planner` 失败；(c) `catch_up_without_backlog`（`skipped=1/backlog=0`）失败；(d) `catch_up_carries_planner` 失败。另补 `unknown_skipped_count`、`non_integer_counter`、`init_frame_counters_not_zero`、`every_update_is_catch_up` 四例。**真实启动重放**：650 帧生产重放集成测试改为复刻操作单的真实开跑形态——frame 0 为 init（计数为 0），frames 1–4 为一个补追批（全批 `backlog_count=3`，1–3 为 `skipped=1` 且无 planner，4 为 `skipped=0` 带 planner），其余为单帧批；该测试原有的窗口/H1/effort/truth 断言全部原值通过。round 14/15 的 planner 篡改与 init/stage 反例全部保留 |
| 5 N11 勘误 | `OFF_ROUTE_DERIVATION` 垂直情形改为 `d*L/sqrt(d^2+L^2) < d`；r3 证据 §1 表同处与 §4「dt 抖动只会使切点距离更小」改为「更贴近 0.5 m 下方，上界与 dt 无关」，两处均标注 round-17 §B.5 勘误。`OFF_ROUTE_TOL_M = 0.501` 与 650 帧重放结论不变。N12–N14 未实现（保持非阻断建议，不借机扩大范围） |
| 6 范围冻结 | 改动仅 `tools/analyze_m3_body.py`、`tests/test_analyze_m3_body.py`、操作单 revision 7、r3 证据勘误、本文件与状态板。零 C#/config/scenario；研究指标与阈值零变化 |

## 2. 改动清单（相对被 Review 退回的候选 `e030310`）

| 文件 | 内容 |
|---|---|
| `tools/analyze_m3_body.py` | `_sha256_hex`/`_require_pin_equal`/`_counter` 三个新助手；F1 pin 硬门；update 行 decision/catch-up 分类；`identity_keys` +2 键；N11 公式勘误 |
| `tests/test_analyze_m3_body.py` | 夹具带真 pin 与生产计数；+10 fail-closed 用例（共 34 个命名反例）与命名前缀断言；+3 独立测试（真实两帧补追、预置 margin、两个 compare 身份）；650 帧生产重放改为真实开跑形态。共 28 个测试 |
| `docs/evidence/P1-M3-BODY-001-1c-preflight.md` | 操作单 revision 7（F1 硬门、F2 分类、撤回 revision 6 的无条件读法、N11） |
| `docs/evidence/P1-M3-BODY-001-1c-rework-r3.md` | N11 两处勘误标注 |

## 3. 实际运行的命令与结果

```bash
.venv-track/bin/python -m unittest tests.test_analyze_m3_body   # 28/28 OK
.venv-track/bin/python -m unittest discover -s tests            # 452 ran / 1 既有失败
# Unity Edit Mode（batchmode，6000.4.1f1，本批次工作树）：
#   -runTests -testPlatform EditMode -testFilter TetheredTracking.Tests
#   -testResults runtime/test-results/p1-m3-body-001-1c-rework6-editmode.xml
#   testcasecount="267" result="Passed" failed="0"
```

- 全套 452/1：唯一失败仍是已登记的既有 infra 债务 `test_check_docs.py`
  （本批次未触碰 `tools/check_docs.py` 与 `tests/test_check_docs.py`）。
  条目数 448 → 452 = 本批次新增的四个独立测试。
- Edit Mode 267/267（本批零 C# 改动，回归确认）。

### 3.1 证伪运行（变异测试）

| 变异 | 结果 |
|---|---|
| 去掉 F1 pin 硬门 | 4 项失败：`margin_bytes_differ_from_pin`、`visible_arc_sha_differs_from_pin`、`margin_pin_missing`、`test_preseeded_margin_window_is_rejected` |
| 恢复 round-14「每条 update 必须有 planner」的无条件读法（= 修复前行为） | 7 项失败/错误，其中 **650 帧真实生产重放直接以 `AnalysisError: update_frame_planner_mismatch:1` 终止**——Review F2 的「每个正式 trial 都会被误杀」在真实冻结输入上端到端复现，本轮修复正是解除该误杀 |

（变异在临时副本上进行并已还原；证伪脚本留在会话 scratchpad，不入库。）

## 4. 生产语义对读（F2 分类的依据）

`controller/track_loop.py`：`backlog_count = max(0, len(processed) - 1)`
写满整批每一行；`skipped_count = 0 if is_latest else 1`；
`body_fields = self._body_step(bundle, result) if is_latest else None`。
因此一个 N 帧补追批产生 N−1 条 `backlog=N−1/skipped=1` 且无 `body_planner`
的行，加 1 条 `backlog=N−1/skipped=0` 带 planner 的行；INIT 路径写
`backlog_count=0, skipped_count=0`。本轮分类与该形态逐项对应，未新增任何
生产侧字段，也未放宽「隐藏 planner 身份」的空间：缺 planner 只在
`skipped=1 且 backlog>=1` 这一确切形态下合法。

## 5. 未验证项与已知限制

- N12（tracker 帧 `frame_id` 非 bool 整数检查）、N13（帧级 aspect 带子）、
  N14（`no_update_frame_with_expected_planner` 命名）按 round 17 §B.5
  保持未实现的非阻断建议。
- 本轮仍是离线分析工具与测试；十次 Play、正式 run ID 与指标未释放。

## 6. 给复核角色的复核范围

1. F1：pin 硬门位置是否早于任何测量窗使用；`_sha256_hex` 对大写/短串/
   非 hex/缺失/非字符串是否全部 fail closed；`identity_keys` 两个新键是否
   真的参与十 run 比较；预置/漂移 margin 无绕过路径。
2. F2：`_counter` 类型判定；decision/catch-up 判据是否与
   `process_available` 的真实字段逐项对应；缺 planner 是否**只**在
   `skipped=1 且 backlog>=1` 合法；`no_decision_update_frame` 是否可被绕过。
3. 650 帧真实重放的开跑形态是否与操作单 §3 步骤 2–3 一致，且窗口/H1/
   effort/estimator 复算量与 round 5 相同（stage 与计数不进指标计算）。
4. round 14/15 的全部既有反例是否仍在各自阶段失败；N11 勘误是否只改文字
   与推导表述、未改任何数值。
