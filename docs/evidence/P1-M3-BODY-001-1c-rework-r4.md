# P1-M3-BODY-001 1c 返工 round 4（Acceptance round 14 §B 四条）

> **round-15 更正块（2026-08-08）**：本文件 §1 表第 2 行与 §4 第 1 条
> 声称「`compute_stage` 缺失的帧按 update 处理（更严方向）」。Acceptance
> round 15 §A.1 证伪：把 update 行改标 `init` 并删除 planner，即可让这些
> 行完全跳过 planner 核对；删掉 manifest `init.frame_id` 也仍能生成
> analysis（receipt 写 `null`）。该「更严」判断不成立。round 5 起
> `compute_stage` 改为枚举划分（恰一条 init 且绑定 manifest ID，其余全部
> update，其他取值 fail closed），以
> `docs/evidence/P1-M3-BODY-001-1c-rework-r5.md` 为准。本文件其余落点
> （capture 绑定、三层 arm 身份、compare 路径/内容绑定、六个命名反例）
> 未被推翻。

批次性质：round 14 `REVISION_REQUESTED_1C_REWORK_ROUND_4` 的窄返工——
只闭合身份/来源链。**零正式 Play、零 trial/run ID、零运行指标、零配额。**
已成立的容差、H2 指示量、自包含复算、指标公式与 C# 载体未动
（工具/测试/文档批次，零 C# 改动）。

## 1. 四条 binding 要求落点

| round 14 §B | 落点 |
|---|---|
| 1 捕获时间不得缺省 | 每条 `record_kind=frame` 的 tracker 记录必须携带非 bool 有限 `capture_monotonic_s`，且与同帧 truth 记录同名字段绝对差 ≤1e-9 s；缺失/非有限/不等即命名 fail closed（`tracker_capture_missing` / `truth_frame_binding_mismatch`）。反例：删除全部 tracker capture 字段必失败 |
| 2 三层 arm 身份一致 | `analyze_trial` 只接受十个冻结 ID（`_expected_policy` 从 ID 推导期望臂，A=hold、B=threshold）；CLI `body_policy`、manifest `body_planner.policy`、manifest `body_planner.planner` 逐项等于期望；每条 `compute_stage=update` 帧必须有 `body_planner` mapping 且 `name` 等于期望 planner（init 帧可缺但存在也必须相等）；至少一条合法 update 帧，否则 fail closed |
| 3 compare 绑定路径/内容/完整 init | `_load` 强制 `analysis.receipt.run_id == 请求路径 ID`（A1 字节复制到 A2 路径即 `analysis_run_id_path_mismatch`）；A/B receipt 的 `body_policy` 与 `body_planner_name` 分别等于期望组合；`init_frame_id` 加入 `identity_keys`；十份 `analysis_sha256` 两两不同，任一重复即 `duplicate_trial_analysis` |
| 4 六个命名反例 + 声明同步 | 新增测试锁定：缺全部 tracker capture、A ID 配 threshold policy、manifest policy ≠ CLI、update 帧 planner 错名（以上在 analysis 对应最早阶段失败）、A1 analysis 复制到 A2 路径、不同 `init_frame_id`（后两个在 compare 失败）。round-3 证据顶部加 round-14 更正块；操作单升 revision 5 并修正「compare 机械拒绝重复」的过早措辞 |

## 2. 改动清单（相对被退回候选 `a3c1f4e`）

| 文件 | 内容 |
|---|---|
| `tools/analyze_m3_body.py` | 上述四项；compare schema 保持 v3（键集合不变，语义收紧为满足 round 14 的既有声明） |
| `tests/test_analyze_m3_body.py` | +6 命名反例（共 22 个）；fixture 补 `compute_stage` 与 receipt `init_frame_id`/`body_planner_name` |
| `docs/evidence/P1-M3-BODY-001-1c-preflight.md` | 操作单 revision 5（三层 arm 身份、捕获绑定、compare 内容绑定） |
| `docs/evidence/P1-M3-BODY-001-1c-rework-r3.md` | 顶部加 round-14 更正块（过早声明以本文件为准） |

## 3. 实际运行的命令与结果

```bash
.venv-track/bin/python -m unittest tests.test_analyze_m3_body   # 22/22 OK
.venv-track/bin/python -m unittest discover -s tests            # 446 ran / 1 既有失败
# Unity Edit Mode（batchmode，6000.4.1f1，本批次工作树）：
#   runtime/test-results/p1-m3-body-001-1c-rework4-editmode.xml
#   testcasecount="267" result="Passed" failed="0"
```

- 全套 446/1：唯一失败仍是已登记的既有 infra 债务 `test_check_docs.py`
  （本批次未触碰该两文件）。
- Edit Mode 267/267（本批零 C# 改动，回归确认）。

## 4. 未验证项与已知限制

- `compute_stage` 缺失的帧按 update 处理（更严方向）：生产
  `track_loop._append_record` 恒写该键，缺失即异常输入，从严拒绝不
  构成合法路径损失。
- compare 的重复哈希检查在内容层兜底；路径归属检查（receipt.run_id）
  在加载期先行失败，两者共同覆盖 §A.3 的复制情形。

## 5. 给复核角色的复核范围

1. `_expected_policy` 的 ID→臂映射与三层相等检查是否覆盖 round 14
   §B.2 逐字（含 init/update 帧分支与至少一条 update 帧要求）。
2. 捕获绑定的字段存在性/有限性/≤1e-9 判定无绕过路径。
3. compare：`_load` 路径归属、`identity_keys` 完整性、重复哈希拒绝、
   期望 planner 组合核对。
4. 六个命名反例是否真的在声明的阶段失败。
