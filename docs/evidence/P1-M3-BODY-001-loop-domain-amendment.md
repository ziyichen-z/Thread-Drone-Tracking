# P1-M3-BODY-001 整圈定义域修法落地证据（BC-BODY1-23…31，接受轮 42）

角色：实现（implementation）。批次性质：**零 Play、零采集 ID、零现场改动**。
授权链：`docs/authorizations.md` 2026-08-13「授权 G1 = F4+F2、G2 = (a)」→ 提案
`docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md` Acceptance
round 42 §A/§B → 本批次。

改动文件恰两个：`tools/analyze_m3_body.py`、`tests/test_analyze_m3_body.py`
（外加本证据文件与状态板）。`controller/`、`Assets/`、`config/`、
`ProjectSettings/`、`runtime/`、操作单 `docs/evidence/P1-M3-BODY-001-1c-preflight.md`
一个字节未动。

## A. 代码改动与 BC 逐条对映

### A.1 BC-BODY1-23：准入判据改判 + 两条补偿性域完整性门

`analyze_trial` 中原判据

```python
if final_mileage < perimeter or final_mileage >= 2.0 * perimeter:
    raise AnalysisError(f"trial_invalid_no_single_loop:{final_mileage:.3f}")
```

改为只保留下界，`>= 2.0 * perimeter` 一支删除，错误名 `trial_invalid_no_single_loop`
仍归下界。新增两条具名 fail-closed 门，**名称逐字**如下：

| 门 | 具名错误（前缀） | 判据 | 消息载荷 |
|---|---|---|---|
| 闭环后不得低于 `P` | `loop_domain_sample_below_perimeter_after_closure` | 首个 `unwrapped >= P` 的样本之后，不得再出现 `unwrapped < P` 的样本 | `:<样本下标>:<unwrapped 值 .3f>` |
| `unwrapped` 非递减 | `loop_domain_unwrapped_backward_step` | 相邻样本不得 `unwrapped[i] < unwrapped[i-1]` | `:<样本下标>:<前值>-><后值>`（均 .3f） |

**两门的判定顺序（实现裁量，理由入证据）**：先判「闭环后低于 `P`」，再判非递减。
原因是机械可达性——闭环后出现 `< P` 的样本必然同时是一次回退，若先判非递减，
则「闭环后低于 `P`」分支永远不可达（成为死代码，也就无法为它写必失败测试）。
反向不成立：两样本都 `>= P` 的回退（或闭环前的回退）只触发非递减门，两门因此
都可达且各有独立必失败测试（§D）。两门都是硬 fail-closed，顺序只决定同时违反
时报出的名字。

`final_mileage = max(unwrapped)` 与 `[0, P)` 样本过滤 (`mileage < perimeter`)
一行未动。

### A.2 BC-BODY1-24：零序列化扰动

`m3_body_analysis.json` 未新增/删除/改名/重排任何字段，也未改变任何已有字段的
计算方式或取值。圈数**不入 JSON**：由已有的 `domains.final_unwrapped_mileage_m /
domains.route_perimeter_m` 派生（§E.3 给出 A1 的派生值）。唯一涉及序列化的编辑
是把局部变量 `a1_binding` 改名为 `attempt_binding`（Python 局部名，不进 JSON；
且输出走 `sort_keys=True`）。证明门见 §B。

### A.3 BC-BODY1-26：A2 替代采集 ID

```python
A2_CANONICAL_TRIAL_ID  = "p1-m3-body-001-arm-a-trial-2"
A2_ACQUISITION_RUN_ID  = "p1-m3-body-001-arm-a-trial-2-attempt-2"
A2_ATTEMPT_NUMBER      = 2
```

- `canonical_trial_id()`：新 ID → canonical slot；旧 ID `p1-m3-body-001-arm-a-trial-2`
  与 A1 旧 ID 一并落 `run_id_void_consumed`（void 判定置于 frozen 循环之前，
  所以旧 ID 不可能再被当成自身 canonical 返回）；其他 attempt 后缀仍落
  `run_id_not_frozen_trial`。
- `_expected_policy("p1-m3-body-001-arm-a-trial-2-attempt-2")` → `hold`（实测）。
- `expected_acquisition_ids("a")[1]` → 新 ID（实测）；`TRIALS_PER_ARM` 仍为 5，
  其余八个采集 ID 逐字未变。

### A.4 BC-BODY1-27：A2 前驱 void 字节绑定

新增只读、无指标的 `_check_a2_predecessor_hold(runtime)`，仿 `_check_a1_predecessor_hold`，
在 `analyze_trial` 中**收集/写盘之前**、仅当 `run_id == A2_ACQUISITION_RUN_ID`
时触发。检查：hold 目录 `runtime/runs/p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold/`
存在；其直接文件名集合**恰为**冻结的 10 个；三项 SHA-256 相等。具名错误：
`a2_predecessor_hold_missing`、`a2_predecessor_hold_file_set_mismatch`、
`a2_predecessor_void_frames_sha256_mismatch`、
`a2_predecessor_void_manifest_sha256_mismatch`、
`a2_predecessor_void_truth_sha256_mismatch`。只枚举文件名并对原始字节取
SHA-256，不解析 void 内容、不计算任何 void 指标。

receipt 侧比照 A1 的条件式写法，新增 A2 专属块（`acquisition_run_id`、
`canonical_trial_id`、`attempt_number`、三个 `predecessor_void_*_sha256`）；
A1 与其余八个 run 的序列化零变化（§B 证明门 + `test_receipt_carries_attempt_binding_only_for_a1_and_a2`）。

三个冻结 SHA 与现场实测**逐位相同**（只读，`shasum -a 256`，未移动任何文件）：

```
a7939b7ce0a54a52487859b3ed1e12d3f0b6526759ab5e77925c49980309fc54  runtime/runs/p1-m3-body-001-arm-a-trial-2/frames.jsonl
d9774905aab324acf05c7616d0bf9e8a0ccf8f10c3855dd5c8c4ff1f9ea4a50c  runtime/runs/p1-m3-body-001-arm-a-trial-2/manifest.json
6f3e5238ef0057253f1228ec4aa9fdd53c2557dd00bc01d2df1782e90635f095  runtime/runs/p1-m3-body-001-arm-a-trial-2/m3_body_truth.jsonl
```

现场文件名集合实测也恰为冻结表的 10 个：`body_config.json frames.jsonl
m3_body_truth.jsonl manifest.json margin.json metrics.final.json
reanchor_config.json scenario.json summary.json tracker_model_spec.json`。

### A.5 BC-BODY1-28/-29/-30/-31

- **-28**：本批只做第 1 步（落地 + 测试 + 证据，停在稳定候选）。第 2–6 步
  （停点确认 → 强制闭环复核 → revision 13 → 现场保全 → 新 GO）未开始。
- **-29/-30**：条款落在操作单 revision 13（接受角色第 4 步）与其后的 trial
  证据，本批无 trial，故无对应记录义务；§E.3 先行给出 A1 的两项派生量作参考。
- **-31**：主指标、`C_quality`、H2、`[0, P)` 样本域、`62.5 m` 窗、`130.0 s`
  watchdog、冻结初始框、其余 CLI 参数、scenario/model/re-anchor config、
  `controller/`、`Assets/` 均未改动；A1 现场（11 份）与四处旧 hold 未动；
  §C 的七项保全移动**未执行**。

## B. BC-BODY1-24 证明门（硬约束）

命令与逐字 stdout（退出码 0）：

```
$ python3 tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
EXIT=0
```

`--verify` 分支逐字节比较整份序列化（不同即 `verify_rerun_not_byte_identical`），
故退出 0 即证明 `m3_body_analysis.json` **零扰动**，且 A1 的真实样本序列同时
通过两条新门（新门在序列化之前执行）。该命令在改动前后各跑一次，输出相同。

## C. 测试改动与结果

### C.1 `two_loops` 改判（BC-BODY1-25 (i)(ii)）

原 `test_fail_closed_cases` 的 `two_loops` 用例（断言追加第二圈抛错）已从
fail-closed 列表与 `_break` 分支中删除，改为两条正向测试：

- `AnalyzeTrialTests.test_extra_laps_neither_void_the_trial_nor_change_h1`：
  单圈 fixture 追加第二圈、再追加第三圈，(i) 不抛错，(ii) `h1`
  （含 `full_loop_c_geom`）与 `domains.loop_frame_count` 与单圈**逐位相同**，
  只有 `final_unwrapped_mileage_m` 增大。
- `LoopDomainAdmissibilityTests.test_extra_laps_leave_the_loop_domain_bit_identical`：
  同一断言跑在**生产回放**上——540 帧（刚闭环）对 1700 帧（> 3 圈，即真实
  trial 2 的形状），`full_loop_c_geom`、`disposition`、`loop_frame_count`、
  `c_quality_series` 全部逐位相同。

### C.2 `no_single_loop` 用例改为名副其实

原用例只截断 truth，实测先撞 `truth_coverage_gap:[30, 31, 32, 33, 34]`，从未
到达它命名的分支。现同步截断 `frames.jsonl`，并在 `EXPECTED_ERROR_PREFIX` 钉住
`trial_invalid_no_single_loop:`。

### C.3 三条必失败测试（各两套 fixture）

fixture 走 workflow §4.4 R3 条件 (1) 的两条通道，反例只做**截断**或把某条真实
记录的坐标**替换为同一条真实轨迹上另一条记录的坐标**，不臆造任何坐标：

| 门 | 生产回放 fixture（`ProductionReplayRun`，始终运行） | 已归档真实 run 字节副本（`ArchivedRunLoopDomainTests`，缺资产则显式 skip） |
|---|---|---|
| 下界 `< P` | `test_below_one_loop_fails_closed`（400 帧 = 158.456 m） | `test_truncated_below_one_loop_fails_closed`（A1 真实流截断到闭环前） |
| 闭环后低于 `P` | `test_post_closure_sample_below_perimeter_fails_closed`（第 600 帧回放第 520 帧位置） | `test_post_closure_sample_below_perimeter_on_real_bytes` |
| `unwrapped` 非递减 | `test_backward_unwrapped_step_fails_closed`（第 600 帧回放第 590 帧位置） | `test_backward_step_on_real_bytes_fails_closed` |

- 生产回放 = `config/scenario.default.json` + 冻结 margin 工件 + 冻结 body config
  + 与生产 `LoopTargetVehicle.Step` 行等价的回放（含切角），即已被轮 13 §B.1/§B.5
  接受的同一条通道；本批把原先写死在单个测试里的构造抽成
  `ProductionReplayRun`，原 650 帧集成测试改用它并保留全部断言。
- 已归档通道直接 `copytree` 真实 A1 run 与真实前驱 hold 到临时目录（真实 hold
  的字节即冻结常量，**无需 patch**），对副本操作；真实现场只读。缺
  `runtime/` 资产时整类 `skipUnless` 跳过，不静默通过。
- 另加 `ArchivedRunLoopDomainTests.test_real_run_reproduces_and_is_domain_intact`：
  真实 A1 序列的回退步数 **0**、闭环后低于 `P` 的样本数 **0**，且重算得
  `full_loop_c_geom = 0.5784550773737355`。这机械支撑了轮 42 §A「不追溯改变任何
  既有结果」的前提。

### C.4 A2 身份与前驱门测试

新增/改判：`test_a2_acquisition_id_maps_to_canonical_slot`、
`test_consumed_void_id_is_permanently_rejected`（改为覆盖两个被消耗 ID）、
`test_other_eight_ids_are_unchanged`、
`test_expected_sequence_uses_acquisition_ids_at_a1_and_a2`、
`test_receipt_carries_attempt_binding_only_for_a1_and_a2`（A1 五字段 / A2 六字段 /
A3 零字段）、`test_shipped_a2_predecessor_constants_are_the_round42_values`
（把轮 42 §B 的目录名、10 个文件名与 3 个 SHA 逐字钉进测试）、新类
`A2PredecessorHoldGateTests`（缺目录、多一文件、少一文件、三处字节篡改各自
具名 fail-closed，且失败时 run 目录不得出现任何收集件或分析件；A1 hold 与 A2
门互不依赖）。原 `test_gate_does_not_apply_to_the_other_nine` 改名为
`..._the_other_eight` 并改用 A3（A2 现在**有**前驱门）。

### C.5 命令与结果

```
$ python3 -m unittest tests.test_analyze_m3_body
Ran 65 tests in 0.825s
OK                                    # 改动前为 50 tests OK
```

```
$ python3 -m unittest discover -s tests
Ran 428 tests in 3.124s
FAILED (errors=9, skipped=6)
```

那 9 条 error 是**预先存在的环境缺库导入失败**，与本批无关：在同一 HEAD 的
一次性 worktree 上跑同一命令得到**同一组 9 条**（`Ran 413 tests … FAILED
(errors=9, skipped=7)`；worktree 少一条 skip 是因为它没有未跟踪的 `runtime/`
资产，与本批无关）。逐条名单：`test_benchmark_reanchor`、
`test_detector_scouting`、`test_rate2_protocol`、`test_rate3_difficulty_audit`、
`test_rate3_reanchor_clock_mismatch_raises_defensively`、`test_rate_study`、
`test_scene004_gate0_probe`、`test_scene004_scouting`、`test_scene006_probe`。

> **接受轮 43 §D + BC-BODY1-34 更正**：上面这组裸 `python3` 数字**不作为停点
> 证据的权威记录**——该解释器缺 torch/ultralytics/cv2，把 9 个模块整体计为
> import error 并少收 105 条用例。本 work item 的权威口径是 §1 钉住的
> `.venv-yoloe/bin/python`；接受角色在该解释器下实测 `Ran 533 … FAILED
> (failures=1, errors=1, skipped=1)`，两条不通过是 `.venv-yoloe` 的 cv2 未装
> opencv-contrib 的 CSRT 组件所致的既有失败（与接受轮 39 §G 同一对），本批零
> 新增失败。BC-BODY1-32 之后的权威数字见 §H.4。

**Unity 未运行**：本批 `Assets/`、`ProjectSettings/`、`config/` 零字节改动，
无 C# 变更，故不产生 Unity 侧回归面；上一轮 Edit Mode 证据不受影响。

## D. 「修复前必失败」的机械演示

两个一次性副本，主工作树零接触（副本在会话 scratchpad 内）：

- **变体 A**：整份 `tools/analyze_m3_body.py` 还原为 HEAD（`ed002f7`）字节，
  测试用新版。结果：新测试整体无法通过——多数用例在 fixture 构造阶段就
  `AttributeError: module 'tools.analyze_m3_body' has no attribute
  'A2_PREDECESSOR_HOLD_DIR_NAME'`（旧工具没有 A2 常量）。
- **变体 B（隔离演示，更干净）**：只把**整圈定义域那一段** revert 回
  `final_mileage < perimeter or final_mileage >= 2.0 * perimeter`，其余改动
  （A2 常量与门）保留。逐条结果：

| 测试 | 变体 B（修复前） | 修复后 |
|---|---|---|
| `ArchivedRunLoopDomainTests.test_backward_step_on_real_bytes_fails_closed` | **FAILED** `AnalysisError not raised` | OK |
| `ArchivedRunLoopDomainTests.test_post_closure_sample_below_perimeter_on_real_bytes` | **FAILED** `AnalysisError not raised` | OK |
| `LoopDomainAdmissibilityTests.test_backward_unwrapped_step_fails_closed` | **FAILED** `AnalysisError not raised` | OK |
| `LoopDomainAdmissibilityTests.test_post_closure_sample_below_perimeter_fails_closed` | **FAILED** `AnalysisError not raised` | OK |
| `LoopDomainAdmissibilityTests.test_extra_laps_leave_the_loop_domain_bit_identical` | **ERROR** `trial_invalid_no_single_loop:672.202` | OK |
| `AnalyzeTrialTests.test_extra_laps_neither_void_the_trial_nor_change_h1` | **ERROR** `trial_invalid_no_single_loop:84.000` | OK |
| `ArchivedRunLoopDomainTests.test_truncated_below_one_loop_fails_closed` | OK | OK |
| `LoopDomainAdmissibilityTests.test_below_one_loop_fails_closed` | OK | OK |
| 其余 57 条 | 全绿 | 全绿 |

变体 B 全套：`Ran 65 tests … FAILED (failures=4, errors=3)`——**恰好**上表六条
具名测试红（其中一条含 2 个 subtest error），其余全绿。

**与 BC-BODY1-25 文字的一处偏差（交接受角色裁定，见 §F.1）**：下界 `< P` 的那
一条**在修复前后都通过**。下界分支是本次修法**保留**的分支，字面与行为都未变，
因此「修复前失败」对它在机械上不可能成立；它仍是一条真实的具名回归测试（并且
修好了 §C.2 那个从未到达命名分支的旧用例）。

## E. 只读现场核对（零改动）

### E.1 旧 ID 永久拒绝 / 新 ID 今日仍无现场

```
$ python3 tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-a-trial-2
ANALYSIS_FAIL_CLOSED:run_id_void_consumed:p1-m3-body-001-arm-a-trial-2
EXIT=2

$ python3 tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-a-trial-2-attempt-2
ANALYSIS_FAIL_CLOSED:missing_run_directory:~/TetheredDroneTracking/runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2
EXIT=2
```

两次调用都在任何写盘之前 fail closed；`runtime/runs/` 未新建任何目录
（`ls runtime/runs/ | grep trial-2` 仍只有 `p1-m3-body-001-arm-a-trial-2`）。

### E.2 现场字节

- trial-2 run 目录 10 个文件的 SHA-256 在本批全部操作前后**逐行相同**
  （`shasum -a 256 … | sort` 前后 `diff` 为空）。
- A1 现场 11 份文件 mtime 全部停在 `Aug 10`/`Aug 12`，本日无写入；六项 shared
  现场（`frames/`、`m3_body_truth.jsonl`、`metrics.json`、`body_command.json`、
  `gimbal_command.json`、`tracking_observation.json`）mtime 全部停在
  `Aug 13 01:48–01:52`（trial 2 那次 Play 留下的），本批未触碰。
- §C 的七项保全移动**未执行**（BC-BODY1-31）。

### E.3 圈数与停留披露（BC-BODY1-30 口径，只读，只记录不判定）

A1（`p1-m3-body-001-arm-a-trial-1-attempt-4`，已归档、已接受）：

- tracker 最后一帧 `simulation_time_s = 130.182861`；Play 最后一条 truth
  `simulation_time_s = 205.382004`；**post-tracker 停留 = 75.199142 s**。
- `domains.final_unwrapped_mileage_m = 412.841826` ÷
  `domains.route_perimeter_m = 212.970563` = **1.938492 圈**。

两项均与接受轮 41 的独立计算一致（A1 同协议停留 `75.199 s`；余量
`2P − 412.842 = 13.099 m`）。

## F. 未验证项、已知限制与交回接受角色的事项

> 接受轮 43 §B 已逐条裁定，裁定结果附在每项之后（**接受角色语**，不是实现
> 角色的自我判定）。

1. **BC-BODY1-25 的「三条均须修复前失败」在下界一条上不成立**（§D 末段）。
   实现角色不自行放宽验收条件：现状如实列出，是否接受该条为「保留分支的
   具名回归测试」由接受角色裁定。
   → **轮 43 §B.1：接受，并认属接受角色的起草错误。** BC-BODY1-25 更正为
   只有「非递减违反」与「闭环后低于 `P`」是必失败测试；下界那条改列**保留
   分支的具名回归测试**。
2. **`compare_arms` 只校验 A1 的 binding 字段，未对称校验 A2**。BC-BODY1-26/-27
   未要求，故按字面未做；`identity_keys` 同样不含这些字段（轮 29 §C.2 原意）。
   若接受角色认为该对称性属必须，需另发 clarification。
   → **轮 43 §B.2/§C.1：不接受现状，发 BC-BODY1-32。** 已于本文件 §H 落地。
3. **A2 前驱门尚未在真实 hold 上跑过**：hold 目录要到 BC-BODY1-28 第 5 步才
   存在。当前证据 = (a) 三个冻结 SHA 与现有 trial-2 现场逐位相同（§A.4，只读）、
   (b) 文件名集合恰为 10 个、(c) stand-in hold 上的六条具名 fail-closed 测试。
   保全移动完成后应在真实 hold 上复跑一次该门。
   → **轮 43 §B.3：接受现状，追加 BC-BODY1-33**（第 5 步之后的只读门排练，
   零 ID、零写盘、零 Play）。**本批不执行**，属第 5 步义务。
4. **两门判定顺序是实现裁量**（§A.1），BC 未指定；若接受角色要求另一顺序，
   「闭环后低于 `P`」将成为不可达分支，其必失败测试须一并改判。
   → **轮 43 §B.4：采纳并写死为「先闭环后低于 `P`，再非递减」，不得颠倒。**
5. **fixture 通道的解释**：BC-BODY1-25 的「生产路径产出或已归档真实 run 字节
   副本」被实现为两条并行通道（§C.3）。合成 `TrialFixture` 仍保留给身份/
   receipt/前驱门类测试（轮 30 §C.3 既有先例），未按本条改造。
   → **轮 43 §B.5：接受。**
6. **Unity 未跑**（§C.5 理由）。本批不产生 Unity 用例，也不解锁任何 Play。
   → **轮 43 §B.6：接受；且明确这不是 `UNITY_NA` 分类。**
7. `runtime/` 是未跟踪生成物，`ArchivedRunLoopDomainTests` 在干净 clone /
   一次性 worktree 中会整类 skip；复核角色若要看它们真跑，需把
   `runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4` 与
   `…-arm-a-trial-1-void-attempt-3-hold` 拷进 worktree（只读拷贝即可）。
   → **轮 43 §B.7：接受并已转达复核角色。**

### F.8 本次（BC-BODY1-32 批）新增的披露

- `test_attempt_binding_mismatch_fails_closed` 同时覆盖了 **A1 侧**的五个键。
  BC-BODY1-32 只要求 A2 侧；A1 分支自轮 29 落地以来从未有测试，顺手补上属
  测试加强，**未改动 A1 分支的任何一行代码**。若接受角色认为超范围，删掉
  cases 元组里 `slot=0` 的五行即可，A2 侧不受影响。
- `CompareArmsTests._receipt()` 必须同步补 A2 binding 块，否则十 run 夹具在
  新门下全部 fail——这是夹具跟随生产语义，不是放宽判据。

## G. 给复核角色的范围

- `tools/analyze_m3_body.py`：整圈定义域段（判据 + 两门 + 顺序论证）、
  A2 常量块、`_check_a2_predecessor_hold`、`canonical_trial_id` /
  `expected_acquisition_ids` 的 A2 分支、receipt 的 `attempt_binding`
  条件块、模块 docstring 两处。
- `tests/test_analyze_m3_body.py`：`PredecessorHolds` 抽取、`TrialFixture`
  改用它、`no_single_loop` 与 `two_loops` 改判、`ProductionReplayRun` 抽取
  （原 650 帧测试改用它，断言集是否等价）、`LoopDomainAdmissibilityTests`、
  `ArchivedRunLoopDomainTests`、A2 身份/前驱门测试。
- 重点核对：BC-BODY1-24 的零扰动（建议独立复跑 A1 `--verify`）、两门的可达性
  与顺序论证是否成立、反例是否真的只用了真实坐标、A2 门是否真的只对 A2 触发、
  §F 的七项。
- **BC-BODY1-32 增量**（§H）：`compare_arms` 的 A2 逐键块、`_receipt()` 的 A2
  夹具块、`test_attempt_binding_mismatch_fails_closed`、
  `test_binding_keys_are_not_cross_run_identity`；核对 A1 分支是否**逐字未动**、
  六个键是否**未**进 `identity_keys`。
- 同轮还欠 `COORD-007` 行登记的操作单 revision 12 与接受轮 40/41 改动的逐文件
  复核（BC-BODY1-28 第 3 步明确并入本轮）。

## H. BC-BODY1-32 落地（接受轮 43 §C.1，本文件第二批）

### H.1 代码改动（仅 `compare_arms`，A1 分支逐字未动）

在既有 `a1_attempt_binding_mismatch` 逐键块**之后**新增对称块，取
`arm_a[1]["receipt"]`（`arm_a_ids` 已在本函数开头逐字比对过
`expected_acquisition_ids("a")`，故下标 1 必然是 A2 采集），逐键校验六项：
`acquisition_run_id`、`canonical_trial_id`、`attempt_number`、
`predecessor_void_manifest_sha256`、`predecessor_void_frames_sha256`、
`predecessor_void_truth_sha256`；不等即
`AnalysisError("a2_attempt_binding_mismatch:<key>")`。

- **A1 分支零改动**：其注释、键序、错误名一个字符未动（`git diff` 中 A1 块
  不出现）。
- **六个键未进 `identity_keys`**（BC-BODY1-32 明令），由
  `test_binding_keys_are_not_cross_run_identity` 机械锁住：未篡改的十 run
  compare 正常返回，且其余八个 run 的 receipt 与这六个键交集为空。
- 数值、字段名、序列化顺序、`m3_body_analysis.json` 与 compare 输出的 schema
  均未改动。

### H.2 测试

- `CompareArmsTests._receipt()` 补 A2 binding 块（夹具跟随生产语义，见 §F.8）。
- **必失败测试** `test_attempt_binding_mismatch_fails_closed`：对 A2 的六个键
  × {改错值, 删除} 共 12 个 subtest，断言异常字符串**恰为**
  `a2_attempt_binding_mismatch:<key>`；另附 A1 侧五键 × 2 = 10 个 subtest
  （超出 BC 的测试加强，见 §F.8）。
- `test_binding_keys_are_not_cross_run_identity`：正向控制 + `identity_keys`
  隔离断言。

### H.3 「修复前必失败」的隔离演示

一次性副本（scratchpad，主工作树零接触），**只**删掉 §H.1 那 18 行 A2 块，
其余全保留：

```
$ .venv-yoloe/bin/python -m unittest discover -s tests -p "test_analyze_m3_body.py"
Ran 67 tests … FAILED (failures=12)
```

12 条红**恰为** `slot='a2'` 的 12 个 subtest（六键 × 两种篡改），逐条
`AssertionError: AnalysisError not raised`；A1 侧 10 个 subtest、正向控制与
其余 66 条测试**全绿**。恢复该块后 67/67 OK。

### H.4 BC-BODY1-24 证明门复跑 + 权威全套数字（BC-BODY1-34 口径）

```
$ .venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
EXIT=0
```

```
$ .venv-yoloe/bin/python -m unittest discover -s tests -p "test_analyze_m3_body.py"
Ran 67 tests in 0.730s
OK

$ .venv-yoloe/bin/python -m unittest discover -s tests
Ran 535 tests in 16.709s
FAILED (failures=1, errors=1, skipped=1)
```

535 = 接受轮 43 §D 的 533 + 本批净增 2 条；两条不通过仍是
`test_pinned_opencv_csrt_initializes_and_updates` 与
`test_cli_runs_pinned_csrt_to_a_versioned_summary`（`.venv-yoloe` 的 cv2 缺
opencv-contrib CSRT 组件，属 `P1-TRACK-001` 旧基线，不在本批与采集路径上）。
**本批零新增失败。**

### H.5 现场与边界

零 Play、零采集 ID、零 `runtime/` 写入；`Assets/`、`ProjectSettings/`、
`config/`、`controller/` 零字节；§C 的七项保全移动仍未执行（第 5 步）；
BC-BODY1-33 属第 5 步义务，本批不执行。
