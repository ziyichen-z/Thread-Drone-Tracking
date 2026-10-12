# P1-SCENE-006 batch 1c — 工具阶段证据（`C_tool′`，无 P3 工件）

Work ID: `P1-SCENE-006`（amendment 1 revision 5，batch 1c 工具阶段）
日期: 2026-08-03
角色: 实现（implementation）
依据: `docs/proposals/P1-SCENE-006-post-v2-anchor-route-amendment.md` §25
BC-B1C-1–5（Acceptance disposition of independent review round 2）

## 1. 零 diff 判定（BC-B1C-3 的第一问）

冻结工具路径集（batch-1b 停点记录声明）在 `fe37ad2..HEAD` 上零 diff
（已核实：`git diff fe37ad2..HEAD --stat -- <工具路径>` 为空）。
但 P3 的四个组成部分在冻结工具集中**不存在**：

1. §5.4 决赛选择函数（margin/score/tie-break/排序表）无实现；
2. BC-B1C-2 的支撑语义 fail-closed 核对无实现；
3. 候选模式 T4（§5.4.4 字面证书 + 站点枚举）与 T6（采集扫描）无实现
   ——`Scene006CandidateEvaluation.RunCell` 按设计只算 T1/T2/T3；
4. checker 无 P3 工件校验能力。

**结论：P3 不能在冻结工具路径集零 diff 下按字面执行 → 按 BC-B1C-3 形成
`C_tool′`。本批次不运行、不写出任何 P3 工件**；P3 采集待 `C_tool′`
经 Acceptance 写入审计与独立复核通过后，在 `capture_commit =
tool_commit = C_tool′` 上执行（§5.6 ④）。

## 2. C_tool′ 内容（全部落在工具/测试路径，不触碰任何 P1/P2/P3 工件）

### 2.1 新增

- `Assets/TetheredTracking/Editor/Scene006/Scene006FinalistSelection.cs` —
  §5.4 冻结评分：四个输入逐个 finite 检查（`SCORE_INPUT_NOT_FINITE`，
  先于一切 margin 运算，+Inf 不会经 `min(…,1.0)` 洗入）、binary64
  margin/score、score 相等用 `==` 语义（`+0.0 == −0.0` 为真，不用
  `CompareTo`）、tie-break 链（score 降序 → vfov 升序 → 高度升序 →
  族名字典序 → §5.5 候选格 rank 升序，`AnchorRank` 按
  （距离², x, z）复现冻结格序）。
- `Assets/TetheredTracking/Editor/Scene006/Scene006FinalistGenerator.cs` —
  `RunBatch1c` 入口与 P3 工件（`p1-scene-006-p3/v1`）：输入工件按内容
  SHA-256 绑定；BC-B1C-2 `VerifySupportBinding`（逐入带格核对 P1 记录：
  `legal=true`、支撑实例恰好一个、规范名属于两个草地 allowlist、
  P1/P2 合格高度一致；任一不符 → `SUPPORT_SEMANTICS_MISMATCH` 并停止，
  不产门值）；T5 复核性重跑 `ModeReportsEqual`（逐候选全字段逐项比对，
  不同即 `T5_RECHECK_DIVERGENCE` fail closed）；候选模式 T4
  （`RunCandidateT4`：字面 §5.4.4 证书绑定唯一支撑实例，`C_hold` 直接
  取 P2 格 `c_geom`，绝不重算覆盖 P2 值）；候选模式 T6
  （`RunCandidateT6`：k=0..10 扫描，中位数取 P2 格
  `t1_min_side_median_px`）。trace 重新生成并与 P2 格 `trace_sha256`
  比对，不符即 `TRACE_BINDING_MISMATCH`。
- `Assets/TetheredTracking/Tests/EditMode/Scene006FinalistEditModeTests.cs`
  — 8 项测试：三个已复核入带格上的手算选择（决赛点
  `(197,30), h=16, vfov=40`，score 0.0847/0.0423/0.0 排序与逐位
  margin）、有限性终态（NaN/+Inf 拦截）、tie-break 全链、格序 rank、
  支撑绑定五类失配、T5 对账器、合成场景 T4/T6（含 `C_hold` 取自 P2 与
  绑定实例缺席 fail-closed）。

### 2.2 修改

- `tools/scene006_candidate_check.py` — 新增 `check_p3`：输入工件哈希
  绑定、§5.4 排序逐格重算（1e-9 容差，见 §4.2）、支撑记录对 P1 复算、
  trace/合同哈希绑定、T4/T6 门算术、状态一致性；dispatch 与 CLI
  增加 `--p1-path/--p2-path`；并并入两项 F8 清理：(b) 真实工件测试接
  通 `p1_path` 交叉检查，(c) `check_p1` 补 clearance 拒绝对账（语义同
  C#：`support PASS ∧ clearance != PASS`）。F8(a)（direct-script 包装）
  按 BC-B1C-4 非必改项保留未动。
- `tests/test_scene006_candidate_check.py` — 6 项 P3 校验测试（合法
  P3_OK、margin 篡改、错误决赛点、支撑记录失真、状态不一致、dispatch
  缺参 fail-closed）；既有 P1 fixture 的 `clearance_status` 按审计器
  真实语义补齐（非合法候选记 `FAIL`），与新增 clearance 对账一致。

## 3. 实际运行的命令与结果

- Unity EditMode（6000.4.1f1，无头）：**214/214 通过**
  （206 既有 + 8 新增）。`runtime/test-results/p1-scene-006-editmode-b1c.xml`。
  实现过程记录：首轮 213/214，失败项是我测试里 `(195,32)` 与
  `(197,30)` 等距（dist² 均 4）时按 x 升序的期望写反——测试期望错误，
  非工具缺陷，已修正并补该 tie 断言。
- Python：`.venv-track/bin/python -m unittest discover -s tests`
  **321 项，1 失败 = 既有 F3**（`test_check_docs` 基底破损，复核已归因
  协调批次 `902a72c`，与本批无关）；`test_scene006_candidate_check`
  18/18（含 6 项新 P3 测试），`.venv-yoloe` 下 PYTHONPATH 直跑同绿。
- **未运行** `RunBatch1c`、未生成任何 P3 工件（BC-B1C-3）。

## 4. 实现语义解释记录（交复核核对，非门变更）

1. **T4 的 `C_hold` 与 T6 的中位数取自 P2 工件值**（§5.3 门分工：
   T1/T2/T3 权威在 P2，P3 不重算不覆盖）；`c_hold_source` 字段写明
   `p2_cell_c_geom`。
2. **margin/score 序列化**：`ScoredCell` 用 double 字段；checker 以
   1e-9 绝对容差对账 margin/score（容忍 JSON 序列化的末位差异），输入
   四值按工件所存 float32 值（读入即 binary64 精确）逐格重算。
3. **新增具名 fail-closed 终态**（提案未列名，属实现侧防御）：
   `TRACE_BINDING_MISMATCH`（重生成 trace 与 P2 绑定不符）、
   `T5_RECHECK_DIVERGENCE`（§5.3"逐项相同，不同即 fail closed"的
   落名）。两者出现即停止并返回 Acceptance。
4. **checker 的锚点排序键**用族格心距离² + x + z 元组复现
   `AnchorRank` 的全格排序——对 tie-break 等价格序（仅在 score/vfov/
   高度/族全同的并列时生效）。
5. **pre-scene 终态豁免 `scene_state_sha256`**：
   `BLOCKED_GEOMETRY_INFEASIBLE` / `SUPPORT_SEMANTICS_MISMATCH` 在不开
   场景前产出，checker 只对到达场景阶段的终态强制该字段非空。
6. **F6 未追认语义在工具侧的体现**：BC-B1C-2 把"支撑实例规范名 ∈
   {Natures_Grass Tile, Natures_Grass Tile Small}"作为硬条件；road_data
   铺装面支撑（如 `Road Tile@210,30`）会命中失配并终止 P3。

## 5. 未验证项与已知限制

- P3 采集（决赛点 T4/T6/T5 复核）未执行——等 `C_tool′` 复核门。
  选择函数对三个已复核入带格的预测性结果（仅测试级）：
  `(197,30), h=16, vfov=40` 第一；这不是 P3 结论。
- `RunBatch1c` 的真实场景路径只有合成测试覆盖；复核角色可在一次性
  worktree 里运行它（其产物在 worktree 内，属复核行为）。
- F8(a) 仍未做（`python3 tools/scene006_candidate_check.py` 直跑入口；
  规范入口为 `python3 -m tools.scene006_candidate_check`）。

## 6. 复核范围（精确文件清单）

新增：`Scene006FinalistSelection.cs`、`Scene006FinalistGenerator.cs`、
`Scene006FinalistEditModeTests.cs`、本文件。
修改：`tools/scene006_candidate_check.py`（check_p3 + F8(b)(c)）、
`tests/test_scene006_candidate_check.py`（+6 测试 + fixture 修正）。
零改动：`config/`、`Scripts/`、全部既有工件（含 batch-1/1b 工件）、
既有 Editor 工具文件。

重点复核项：§5.4 评分/tie-break 与提案逐字一致性；BC-B1C-2 五类失配
的 fail-closed 覆盖；T4 `C_hold` 与 T6 中位数的 P2 来源纪律；两个新增
具名终态；checker 对账的容差与排序键等价性。

## 7. Unity 用例

工具阶段全部为 Edit Mode 离线执行与离线 Python，零 Play、零采集：
无用户 Unity 运行用例。复现：重跑 §3 的命令。

---

## 8. 返工轮次（2026-08-03）：复核 round 3 F10–F13

复核 round 3 对 `C_tool′ 06bbf86` 判 `REWORK_REQUIRED`
（`docs/reviews/P1-SCENE-006.md`）。本轮回合全部修复如下，仍严格在冻结
工具路径集内；**P3 工件依旧未运行、未写出**。

- **F10（阻断）— NaN 感知逐项相等**：`ModeReportsEqual` 全部 float 字段
  改经 `SameFloat`（`left == right || both NaN`）——`SupportAt` 对
  `SUPPORT_NOT_FOUND` 候选合法记录 `support_surface_y_m = NaN`（族 B
  每高度 288 个），IEEE `!=` 使自比对也发散。修复后字节一致重跑必相等，
  NaN 与有限值的真分歧仍被检出。分歧详情同步富化（F14(a)）：逐字段记
  字段名与两侧值。回归测试
  `T5RecheckComparatorTreatsBothNaNAsSame`（含 NaN 的 fixture：
  相等通过、NaN↔finite 发散）。
- **F11 — checker pre-scene 终态豁免落实**：`_check_capture` 增加
  `require_scene_state` 形参；`check_p3` 按终态分支传值——两个
  pre-scene 终态（`BLOCKED_GEOMETRY_INFEASIBLE` /
  `SUPPORT_SEMANTICS_MISMATCH`）必须空、场景阶段终态必须非空。
  回归测试覆盖三种组合（空通过、pre-scene 带值拒绝、场景阶段空值
  拒绝）。
- **F12 — 排序表保留终态标签**：`Select` 新增 `Table`（排名格在前、
  终态格随后、rank −1），工件 `ranking` 改序列化 `Table`；checker
  校验终态行的成员身份、重算标签与 rank −1。回归测试
  `SelectionTableKeepsTerminalLabels` 与 checker 侧
  `test_ranking_keeps_terminal_labels`。
- **F13 — checker 的 T6 门模型补 `PROBE_FIDELITY_CONTRADICTION`**：
  k* ≥ 0 且 prompt min-side 非有限时按具名保真矛盾门对账，状态落到
  `BLOCKED_FINALIST_AUDIT_FAILED`。回归测试
  `test_t6_fidelity_contradiction_gate`。

结果：Unity Edit Mode **216/216**（214 + 2 新增；
`runtime/test-results/p1-scene-006-editmode-b1c2.xml`）；Python 全套
324 项仅余既有 F3；`test_scene006_candidate_check` 21/21。
复核端点：`77595c8..<新 C_tool′>`（§5.6 ④）。
