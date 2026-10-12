# P1-VLM-DATA-002 — S0–S5 attempt-2 审计前上界（**审计前上界、非门 verdict**）

Work ID: `P1-VLM-DATA-002`
Role: 实现角色（implementation）
Date: 2026-09-06
授权：用户 2026-09-05 逐字「授权继续」签发提案 §6 授权 #2（阶段 B–D；账本
`docs/authorizations.md` 同日条目）。本文件是 §2.2 第 7 条与 §2.3 步 7 指定的
上界报告，格式对齐 `P1-VLM-DATA-001` 轮 20/28 的同名交付
（`docs/evidence/P1-VLM-DATA-001-S0-S5-pre-audit-upper-bound.md`）。
执行收据与采集细节见 `docs/evidence/P1-VLM-DATA-002-stage-a-implementation.md` §19/§20。

## 0. 摘要（**审计前上界、非门 verdict**）

S0–S5 六类工件已以 **attempt-2** create-once 落盘，六个写点各自 supersede
attempt-1，`--through field_catalog` 在 S5 精确停住（未触及 S6–S9）。`U_F1`…`U_F4`
从**同一份未 supersede 的 S0–S5 工件只读、在内存中**计算，状态一律
`NOT_EVALUATED_PRE_AUDIT`。唯一的乐观假设是被授权的那个：A1/A2/A3 零降级、零拒绝、
零修复，且 S0–S5 不发生 supersession。**本表不是 G0 门结论**，不得读作 `OPEN` /
`CLOSED` / `PASS` / `FAIL` / `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA`；未写 audit、
未调 `stage7_gate()` / `build_g0_report()`，未产生 `mother_candidates` / `g0_report` /
S8 / S9。

## 1. 上界表（**审计前上界、非门 verdict**）

| 量 | 乐观上界 | 状态 | 冻结 floor 参考 | 诊断差额（上界 − floor） |
|---|---|---|---|---|
| `U_F1` 双验证对象数 / 101 | **37**（bus、car、container truck、pickup truck、police car、suv、truck 共 **7** 类） | `NOT_EVALUATED_PRE_AUDIT` | ≥ 60，且 ≥ 6 类各有 ≥ 1 | 对象 **−23**；类 **+1** |
| `U_F2` 站位簇（floor-eligible） | 全局 **1,543**；train 198 / dev 477 / test **868** / d3 0 | `NOT_EVALUATED_PRE_AUDIT` | 全局 ≥ 40；test ≥ 8 | 全局 **+1,503**；test **+860** |
| `U_F3` 属性唯一单元 (对象, 站位簇) | train∪dev **494**；test **633**；test 留出单元 **280**；类覆盖 train∪dev 与 test 各 **9** 类（ambulance/bus/car/container truck/pickup truck/police car/suv/taxi/truck） | `NOT_EVALUATED_PRE_AUDIT` | train∪dev ≥ 60；test ≥ 25；test 留出 ≥ 8；类 train ≥ 5 / test ≥ 4 | **+434**；**+608**；**+272**；train 类 **+4** / test 类 **+5** |
| `U_F4` 统计簇 (atom_id, 对象) | train∪dev **49**；test **55** | `NOT_EVALUATED_PRE_AUDIT` | train∪dev ≥ 25；test ≥ 10 | **+24**；**+45** |

差额为负只表示「乐观上界相对 floor 的诊断差额」，差额为正也**不是**达标结论。

### 与 `P1-VLM-DATA-001` attempt-1 的对照（同口径）

| 量 | attempt-1 | attempt-2 | 变化 |
|---|---|---|---|
| `U_F1` 对象 / 类 | 9 / 5 类 | **37 / 7 类** | +28 / +2（**类下限首次达成**） |
| `U_F2` 全局 / test | 46 / 22 | **1,543 / 868** | ×33 / ×39 |
| `U_F3` train∪dev / test | 25 / 20 | **494 / 633** | ×20 / ×32 |
| `U_F4` train∪dev / test | 4 / 7 | **49 / 55** | ×12 / ×8 |
| train split 帧数 | **0**（空） | **2,523** | 首次非空 |

### 预注册产出线（§5 第 5 条；机械派生，待接受角色核验）

| 条件 | 要求 | 实测 | 达成 |
|---|---|---|---|
| `U_F1` 对象 | ≥ 60 | 37 | **否** |
| `U_F1` 类 | ≥ 6 类 | 7 类 | 是 |
| `U_F3` train∪dev / test | ≥ 60 / ≥ 25 | 494 / 633 | 是 |
| `U_F4` train∪dev / test | ≥ 25 / ≥ 10 | 49 / 55 | 是 |
| train split 非空 | 非空 | 2,523 帧 | 是 |

**五项中四项达成，`U_F1` 对象数未达。** 按 §5 第 5 条「任一不达 →
`SURVEY_FLOORS_UNREACHABLE`，后续只按 §2.4 回用户；**下限永不移动**」，本批的机械
结论是 **`SURVEY_FLOORS_UNREACHABLE`**。实现角色只作机械派生并如实记录，verdict 的
消费与归因属接受角色。

## 2. `U_F1` 未达的结构定位（观察，非裁定）

S5 对象域共 **690** 个对象，其中 `Vehicle_*` **93** 个。93 个车辆对象
**class 全部 `class_verified = true`（93/93）**，卡点完全在颜色一侧：

| 颜色状态 | 数量 | 含义 |
|---|---|---|
| `VERIFIED` | **37** | 即 `U_F1` 的双验证对象 |
| `UNVERIFIED` / `GROUP_INCONSISTENT` | **37** | 同一颜色组内成员的解析色不一致，整组降级 |
| `UNVERIFIED` / 无降级原因 | **19** | 主色带占比未达 `COLOR_MAIN_BAND_MIN_SHARE = 0.5`，颜色始终未解析 |

88 个颜色组中 **28 组不一致**。已验证色词表 = {blue, gray, green, purple, red, yellow}。

**与上一批的关键差别**：attempt-1 的报告记录「class 可验证的目录车辆只有 16 个 ⇒
`U_F1` 不可能超过 16」——那时 60 的下限在结构上**不可达**。attempt-2 的结构上限已升到
**93**（≥ 60），下限因此**首次在结构上可达**；未达的原因转移为颜色验证：37 组内不一致
+ 19 个主色带不足。这一条只陈述事实，不构成任何调参、放宽或补采的提议——`FLOORS`、
`COLOR_MAIN_BAND_MIN_SHARE`、θ_occ 与切分规则均为冻结常量，本批一字未动。

## 3. S0–S5 attempt-2 实测摘要

| 阶段 | 工件 | 字节 | 产出与核验 |
|---|---|---|---|
| S0 | `contract` | 25,062 | `survey_sessions` **8**；supersedes attempt-1 |
| S1 | `inventory` | 50,676,725 | records **50,115**（attempt-1 为 29,923）；只读 preflight 复现 `match_audit` zero/multi 均 **0**、INCLUDED 图像 **43,711** |
| S2 | `layout` | 4,178,273 | partition **17**，**BOUND 16**；`p1-vlm-survey-a1-p1-c1-s1` 判 **INVALID**（该会话 `close` 时证人为 `INSUFFICIENT_WITNESS_FRAMES`，§2.4 终态分立要求整会话退出母集与全部计数——合同自动生效，非人工干预） |
| S3 | `frames_catalog` | manifest 63,141；**151** shard（约 1.56 GiB 压缩） | frames **43,535**；`skipped_invalid_frames` **19**（即 a1-s1）、`skipped_unbound_frames` **157** |
| S4 | `splits` | manifest 4,010,544；**7** shard（约 7.2 MiB 压缩） | 无 terminal；atoms **4**；`frame_counts` train **2,523** / dev **13,144** / test **8,450** / d3 0；dropped **19,418** |
| S5 | `field_catalog` | 638,069 | objects **690**（Vehicle_* 93）；双验证 **37** |

对象状态直方图（S3 全量行流）：`OK` **392,301** / `NOT_IN_VIEW` 32,207,415 /
`EXCLUDED_OCCLUDED` 745,495 / `TOO_SMALL` 285,550 / `TRUNCATED` 283,004 /
`PHANTOM` 52,329。referable 对象-帧 **57,430**；冻结候选外延 **27,074** 条。

### supersession 谱系（逐件实测）

```
contract        supersedes=attempt-1  inputs=[]
inventory       supersedes=attempt-1  inputs=[contract@attempt-2]
layout          supersedes=attempt-1  inputs=[]
frames_catalog  supersedes=attempt-1  inputs=[inventory@attempt-2, layout@attempt-2]
splits          supersedes=attempt-1  inputs=[frames_catalog@attempt-2]
field_catalog   supersedes=attempt-1  inputs=[frames_catalog@attempt-2, layout@attempt-2]
```

六件各自 supersede attempt-1、无一断链（`R1@stageA` F1 修复在真实归档上的首次检验）。
本次自 S0 连续跑到 S5，**未触发** BC-SURVEY-4 的跨代回退路径（F2/I17 所修），该路径在
真实归档上仍只有测试夹具证据——如实记录，不作已验证声明。

## 4. 执行如实记录

| 步骤 | 耗时 | 峰值内存 |
|---|---|---|
| 只读 preflight（S1+S2，零写出） | 831.9 s | 240 MB |
| S0–S5 attempt-2 `--run --through field_catalog` | 2,364.9 s（39.4 min） | 727 MB |
| 上界计算（只读，S7 取数链止于 compute_f1..f4） | 1,620.9 s（27.0 min） | **7.17 GB** |

- 首次 preflight 曾以 `SurveyContractError: 归档树摘要不符` fail-closed：
  `p1-vlm-survey-a1-p1-c1-s2/` 内出现一个 macOS Finder 生成的 `.DS_Store`（6,148 B，
  `Sep 6 02:13`）。该文件**移出隔离而非删除**，移出后 `verify` 重算
  `tree_sha256 = a0edc431…b415`，与 `close` 记录逐字一致，归档内容未变。八个会话中
  只有该目录被污染。**观察（供接受角色参考，非提议）**：树摘要把目录内任何文件都算作
  成员，故 OS 生成物会直接阻断阶段 D；是否为此类文件开白名单会改动树计算，属合同问题。
- 上界计算的 7.17 GB 峰值来自对 S3 行流的多遍消费；`SplitDecoratedStream` 之外还
  多次 `list(stream)`。该脚本是一次性只读诊断，不在仓库内，不影响任何工件。

## 5. 未授权与未执行（如实声明）

未写 `audit`；未调 `stage7_gate()` / `build_g0_report()` / `freeze` 之外的任何写点；
未产生 `mother_candidates` / `g0_report` / `mother_set` / `stop_point`；未训练、未下载、
未用 API/GPU。attempt-3 未创建（身份仍剩 1 个）。S6 人工审计与 S7–S9/G0/D0 仍须用户
另行授权。
