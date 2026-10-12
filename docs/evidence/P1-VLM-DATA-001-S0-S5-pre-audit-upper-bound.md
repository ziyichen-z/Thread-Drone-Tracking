# P1-VLM-DATA-001 — S0–S5 审计前上界诊断（**审计前上界、非门 verdict**）

授权：提案 §32（接受轮 20，`FORMAL_S0_S5_AUTHORIZED /
PREAUDIT_UPPER_BOUND_DIAGNOSTIC_ONLY`，用户逐字授权见
`docs/authorizations.md` 2026-08-28 条目）与提案 §40（接受轮 28，
`FORMAL_S3_S5_CONTINUATION_AUTHORIZED / PREAUDIT_UPPER_BOUND_DIAGNOSTIC_ONLY`，
用户逐字「授权，继续」见账本 2026-09-01 条目）。本文件是 §32.2 / §40.3 指定的
**唯一**诊断交付；执行收据与核验细节见实现证据
`docs/evidence/P1-VLM-DATA-001-implementation.md` §22。

## 0. 摘要（**审计前上界、非门 verdict**）

**S0–S5 六类正式工件现已全部 create-once 落盘且逐件核验完整。** S0/S1/S2 来自
2026-08-28 的轮 20 执行；S3 `frames_catalog`、S4 `splits`、S5 `field_catalog` 来自
2026-09-01 的轮 28 continuation——以既有 S0–S2 为只读输入、同一 attempt、依次调用
已复核生产入口 `stage3_frames_catalog()` → `stage4_splits()` →
`stage5_field_catalog()`，未走 `--run`，S4 未返回 terminal，S0–S2 字节前后相等，
零 `.staging/`、零重试、零代码改动。

按 §32.2 / §40.3，`U_F1`…`U_F4` 已从**同一份未 supersede 的 S0–S5 工件只读、
在内存中**计算，状态一律 `NOT_EVALUATED_PRE_AUDIT`。唯一的乐观假设是被授权的那
一个：A1/A2/A3 零降级、零拒绝、零修复，且 S0–S5 不发生 supersession。**本表不是
G0 门结论**，不得读作 `OPEN` / `CLOSED` / `PASS` / `FAIL` /
`INSUFFICIENT_SYMBOLIC_GROUNDING_DATA`；未写 audit，未调 `stage7_gate()` /
`build_g0_report()`，未产生 `mother_candidates` / `g0_report` / S8 / S9。

读数（只陈述乐观上界相对冻结 floor 的**诊断差额**，不签发任何 verdict）：
`U_F1` 双验证对象 **9 / 101**（floor 60，差额 −51；覆盖 5 类，floor 6 类，差额 −1）；
`U_F2` 站位簇全局 **46**（floor 40，差额 +6）、test 侧 **22**（floor 8，差额 +14）；
`U_F3` 属性唯一单元 train∪dev **25**（floor 60，差额 −35）、test **20**（floor 25，
差额 −5）、test 留出单元 **9**（floor 8，差额 +1）、类覆盖 train 4（floor 5，
差额 −1）/ test 4（floor 4，差额 0）；`U_F4` 统计簇 train∪dev **4**（floor 25，
差额 −21）、test **7**（floor 10，差额 −3）。

一条与审计无关的结构事实（观察，非裁定）：S5 对象域里 **class 可验证的目录车辆
只有 16 个**——101 个目录车辆中只有这 16 个在任一 BOUND 帧上取得过 `OK` 状态与
visible 框，其余 85 个从未进入 S5 域。因此在本份归档上，无论人工审计结果如何，
`U_F1` 的双验证对象数都不可能超过 16。

## 1. 上界表（**审计前上界、非门 verdict**）

| 量 | 乐观上界 | 状态 | 冻结 floor 参考 | 诊断差额（上界 − floor） |
|---|---|---|---|---|
| `U_F1` 双验证对象数 / 101 | **9**（ambulance、car、container truck、suv、truck 共 5 类） | `NOT_EVALUATED_PRE_AUDIT` | ≥ 60，且 ≥ 6 类各有 ≥ 1 | 对象 **−51**；类 **−1** |
| `U_F2` 站位簇（floor-eligible） | 全局 **46**；dev 24 / test **22** / train 0 / d3 0 | `NOT_EVALUATED_PRE_AUDIT` | 全局 ≥ 40；test ≥ 8 | 全局 **+6**；test **+14** |
| `U_F3` 属性唯一单元 (对象, 站位簇) | train∪dev **25**；test **20**；test 留出单元 **9**；类覆盖 train {car, container truck, suv, taxi} / test {bus, container truck, suv, taxi} | `NOT_EVALUATED_PRE_AUDIT` | train∪dev ≥ 60；test ≥ 25；test 留出 ≥ 8；类 train ≥ 5 / test ≥ 4 | **−35**；**−5**；**+1**；train 类 **−1** / test 类 **0** |
| `U_F4` 统计簇 (atom_id, 对象) | train∪dev **4**；test **7** | `NOT_EVALUATED_PRE_AUDIT` | train∪dev ≥ 25；test ≥ 10 | **−21**；**−3** |

四项均为**同一份未 supersede 的 S0–S5 工件**上的乐观上界。差额为负只表示
「乐观上界相对 floor 的诊断差额」，差额为正也**不是**达标结论。

## 2. 上界算法与假设（只读、内存；复用既有纯函数）

算法就是 S7 `stage7_gate()` 里冻结的那条链，但**不写任何工件、不产生门 token**：

1. 以 S7 的读取权限（`requesting_stage=7`）经 `ArtifactStore` 只读取 S2 `layout`、
   S3 `frames_catalog` 行流（`CatalogStream`，每遍重新逐 shard 校验）、S4 `splits`
   manifest 与 S5 `field_catalog`。
2. **假设 A1 零降级**：`build_catalog.apply_audit_downgrades(field_catalog, [])`
   （空降级表；断言 `dual_verified_object_ids`、`verified_color_vocabulary` 与 S5 载荷
   相同）。**假设 A2/A3 零拒绝**：`compute_f1`…`compute_f4` 与
   `freeze_mother_candidates` 本就不读取 A2/A3 结果，它们只能经 supersession 改变
   工件，而本报告的前提是不发生 supersession。
3. `split_of_frame` 由 S4 `frames` 派生并以 `SplitDecoratedStream` 装饰行流（复核轮 6
   F20 的生产路径）；`atom_of_frame` 由 S4 `atoms` 派生；留出对象取 S4
   `held_out_objects`；`station_of_frame` 由每帧 `station_bin.key` 派生。
4. 候选外延 = 对每帧每个 `referable` 对象调用 `build_catalog.frame_world` +
   `prospective_mother_eligible`（§2.4 具名谓词，与 S7 相同的胶水），再经
   `g0_report.freeze_mother_candidates(..., dropped_frames=S4.dropped_frames)` 冻结
   （只在内存）。
5. `U_F1 = compute_f1(降级后目录)`、`U_F2 = compute_f2(带 split 的行流)`、
   `U_F3 = compute_f3(冻结外延, station_of_frame)`、`U_F4 = compute_f4(冻结外延)`；
   分母 = `g0_report.stratified_denominators`。四个函数返回的 `passed` 布尔量**被
   丢弃**，`build_g0_report()` 与 `stage7_gate()` 均未调用，故不存在 gate 字段。
6. 自检：F2 在「每帧轻量投影（除 `objects` 外全部顶层字段 + split）」与「装饰行流」
   上各算一遍，逐字段相等；计算前后正式根 92 个文件逐路径 SHA 相同（零写入）。

「上界」的成立条件与 §32.2 相同：只对同一份未 supersede 的 S0–S5 工件成立；A1
可降级颜色组、A2/A3 可拒绝样本，只会让正式 S7 的值不高于本表。

## 3. S0–S5 实测摘要（**审计前上界、非门 verdict**）

attempt 由 `ArtifactStore` 运行时枚举后选定（S0–S2 共有的唯一 attempt）；按
COORD-007 R7 不在本文件手写 attempt 名与工件 SHA。

| 阶段 | 工件 | 字节 | 完整性核验 |
|---|---|---|---|
| S0 | `contract` | 5,014 | 可解析、结尾换行、信封身份正确；`floors` 与 `contract.FLOORS` 相等 |
| S1 | `inventory` | 28,574,739 | `record_count` **29,923**（image 24,154 / truth 5,769），`match_audit` zero/multi 均 **0**；INCLUDED 图像 **23,706**；5,769 条 INCLUDED 真值记录重算 SHA 未变 |
| S2 | `layout` | 2,220,725 | 9 partition 全 `BOUND`、9 条 `cross_validation`（与轮 20 及只读 preflight 逐项吻合）；`inputs` 引用 inventory 的运行时 SHA；BOUND 帧 **23,549** |
| S3 | `frames_catalog` | manifest 35,034；83 shard 压缩 932,548,072（未压缩 5,515,458,884） | 经生产 `read_composite_rows` 全量迭代 **23,549** 行 = `frame_count` = `row_count`，帧 id 严格升序；`skipped_unbound_frames` **157**、`skipped_invalid_frames` **0**；`inputs` = 本次读取的 inventory + layout ref |
| S4 | `splits` | manifest **515,074,557**；3 shard 压缩 3,204,731（未压缩 183,337,279） | **无 terminal**；atoms **3**；`frame_counts` train **0** / dev **7,060** / test **3,045** / d3 **0**，dropped **13,444**（合计 23,549）；角色行 **1,032,602** = `exposure_matrix.sample_count`，`(frame_id, object_id)` 严格升序；泄漏断言 6 对两两不交；`inputs` = 本次读取的 S3 manifest ref |
| S5 | `field_catalog` | 94,325 | objects **106**（class 可验证 **16**，其余 90 为取得 `OK` 状态的非车辆对象）；color `VERIFIED` 54 / `UNVERIFIED` 52；35 个颜色组中 5 组不一致 → 41 个 `GROUP_INCONSISTENT` 降级；**双验证 9**；`inputs` 为空（见实现证据 §22.3） |

S3 行流的其他实测：`target_unbounded` 帧 **16,472 / 23,549**（70.0%）；
`pre_split_floor_eligible` 帧 **4,390**；referable 对象-帧 **27,870**（每帧最多 5）；
站位簇键 54 个；对象状态合计 OK 213,182 / NOT_IN_VIEW 17,399,521 / TOO_SMALL 155,304 /
TRUNCATED 153,262 / EXCLUDED_OCCLUDED 423,402 / PHANTOM 52,329。

S4 指派（冻结规则的机械结果，原样报告）：dev = {detect-scout1, m3-armA, rate,
scene-val}，test = {s004-qual, s004-scout, s004-smoke} ∪ {m3-armB}，train = ∅，
d3 = ∅（`d3_holdout_empty` 为真）。3 个 atom 中 test 按全枚举目标向量取 2 个，无
D3 可选原子，剩下的唯一原子按 `split_dev` 的 15% 前缀规则整体落入 dev，train 因此
为空——这是 §2.5 规则在本归档上的结果，不是可调参数。

## 4. 分母（**审计前上界、非门 verdict**；`stratified_denominators` 与冻结外延）

| 分母 | 值 |
|---|---|
| `frames_by_split` | dev 7,060 · test 3,045 · 无 split（dropped）13,444 |
| `frames_by_usage_class` | CALIBRATION 286 · PROTOCOL_INVALID 8,126 · SMOKE 3,762 · VALID_FORMAL 3,722 · VALID_PARENT_HOLD 4,224 · VALID_SCOUTING_CLOSED 3,173 · VOID_TRIAL_HOLD 256 |
| `frames_by_layout_class` | default 7,700 · scene-004 15,849 |
| 冻结候选外延 | **5,398** 条，全部 `attribute` 程序；floor-eligible **2,837**；train_augment_only 2,561 |
| `candidates_by_split` | dev 309 · test 2,528 · dropped 2,561 |
| `candidates_by_usage_class` | PROTOCOL_INVALID 2,561 · VALID_FORMAL 12 · VALID_SCOUTING_CLOSED 2,825 |
| `candidates_by_layout_class` | default 321 · scene-004 5,077 |
| `candidates_by_object` | 仅 **7** 个对象：Vehicle_SUV_color01 (1) 2,519 · Vehicle_Container_color02 (2) 1,590 · Vehicle_Taxi (2) 736 · Vehicle_Container_color01 256 · Vehicle_Bus_color03 (1) 240 · Vehicle_Container_color03 45 · Vehicle_Car_color01 12 |
| 留出 | 候选中留出对象 2,098 条；留出对象作 ref 的候选 0 条；候选覆盖 3,560 个不同帧 |

## 5. 执行时间线（如实记录）

**轮 20（2026-08-28）**：

1. 首次调用按 §32.1 (3) 逐阶段调用 S0→S5（**未走** `--run`）。S0/S1/S2 写盘成功后，
   进程在 S3 期间被实现会话工具的 10 分钟墙钟上限 SIGTERM 中断——非阶段异常。
2. 因 `ArtifactStore.write` 使用非原子 `write_bytes`，对已落盘三件逐件核验可解析性、
   结尾换行与信封身份，并与 preflight 对账，确认完整。
3. 续跑只调 S3–S5，S0–S2 经 store 只读消费。S3 被 OS SIGKILL（`exit=137`，内存
   耗尽：整表 entry 累积 ≈ 5.4 GiB JSON 的数倍驻留），S3/S4/S5 均未产生；按
   §32.1 (4) 未修补、未重试、未删目录、未 supersede，返回接受角色。接受轮 21 以
   BC-DATA-25 裁定有界流式存储，经复核轮 6/7 与接受轮 22–27 闭合。

**轮 28 continuation（2026-09-01）**：

4. 执行前 §40.1 硬门 32 项全过（实现证据 §22.1）。
5. S3：wall 226.1 s，进程外 peak RSS 420,282,368 B（≈ 401 MiB）——同一 S3 在
   有界流式存储下不再驻留全集；立即核验 13/13（34.4 s）。
6. S4：wall 297.5 s，peak RSS 3,129,065,472 B（≈ 2.91 GiB，见 §6）；无 terminal；
   立即核验 13/13（3.7 s）。
7. S5：wall 64.3 s，peak RSS 674,250,752 B（≈ 643 MiB）；立即核验 11/11。
8. 上界计算：只读 100.9 s，peak RSS 2,957,262,848 B（同样由解析 S4 manifest 主导）；
   正式根前后 92 个文件 SHA 相同。

## 6. 性能观察（§40.2 (4)：只披露，不据此改代码、K、样本、split、阈值或对象域）

1. **S5 双遍解压**（复核轮 7 note 2 / 接受轮 27 列为监控项）：S5 对 83 个 shard
   （5.5 GB 未压缩）完整解压两遍，wall 64.3 s，即每遍约 30 s；驻留 ≈ 643 MiB，
   与 `O(对象数 × K)` 的选择器上界相容。成本存在但有限。
2. **S4 manifest 515,074,557 B 与 peak RSS ≈ 2.91 GiB**：manifest 的 512,888,211 B
   来自 `atoms.near_duplicate_pairs`——`merge_atoms` 对 C(23,549, 2) ≈ 2.77×10⁸ 个
   跨帧 pHash 对做 Hamming 比较（S4 的主要 wall time 来源），并把 **2,663,282** 对
   跨族近重复帧对整份写入 manifest。BC-DATA-25 (4) 把「小型摘要」留在 manifest，
   而该成员在归档尺度上并不小；随后每个解析 S4 manifest 的消费者（S4 核验进程
   3.61 GiB、上界进程 2.96 GiB）都为此付出约 2.5–3.6 GiB 驻留。这是已复核代码的
   既有行为，本批未改，交接受角色裁定。
3. **S3 有界如设计**：写出 5.5 GB 未压缩行流时 peak RSS ≈ 401 MiB。

## 7. 边界自查

- `runtime/dist-data/` 下恰有 `contract`/`inventory`/`layout`/`frames_catalog`/
  `splits`/`field_catalog` 六类，各恰一个 attempt；`audit`、`mother_candidates`、
  `g0_report`、`mother_set`、`template_expressions`、`stop_point` **均不存在**（实测）；
  全根零 `.staging/`、零 `*.publishing`、无无 manifest 的 `shards/`。
- 未写合成 `audit`，未调 `stage7_gate()` / `build_g0_report()`，未写 S6–S9，未
  supersede，未删除任何目录，未重试任何阶段，未走 `--run`。
- 本批未修改任何生产代码、测试、合同或依赖（实测 `git status` 仅本报告、实现证据
  与状态板）；未添加 instrumentation code，wall time / RSS 全部来自进程外
  `/usr/bin/time -l`。
- 零 Unity/Edit Mode/Play、零 scenario/session/run ID、零 API/GPU/模型下载。

## 8. 保留的既有风险与纪律（原样转录）

- **`m3-armB` 贴线**：复核轮 5 与接受轮 19 记录的 `141/153 = 0.9216` 对
  `0.9` 仅余约 **3.3 个样本**裕量。正式运行须原样报告，**禁止为过门调参**。
  本次 S2 未重跑，该 partition 的交叉验证结果与轮 20 相同。
- 上界只对**同一份未 supersede 的 S0–S5 工件**成立；A1 可降级颜色组、
  A2/A3 可拒绝样本。若审计发现工具/数据缺陷并触发未来 supersession，本报告
  自动失效，不约束新 attempt 的值。
- 本报告的任何数字都不得被用来修改参数、帧集、阈值或测量对象。

## 9. 返回接受角色的观察（实现角色不自行裁定）

1. **F1 的结构上限是 16**（S5 域内 class 可验证车辆数），与审计无关；其中双验证 9。
   85 个目录车辆从未在任何 BOUND 帧取得 `OK` 状态——属于归档覆盖事实，不是本批
   可处理的实现问题。
2. **`target_unbounded` 帧占 70.0%**，直接压低 floor-eligible 帧（4,390）与候选
   外延（5,398 条、7 个对象）。
3. **S4 train split 为空**是冻结规则在 3 个 atom 上的机械结果（§3）。
4. **S4 manifest 尺度**（§6 第 2 条）与 **S5 信封 `inputs` 为空**（实现证据 §22.3）
   均为已复核代码的既有行为，本批只披露。
5. 上表的每个负差额都只是「乐观上界相对 floor 的诊断差额」；是否投入人工审计、
   是否另立采集补数 work item，由用户与接受角色决定，本报告不签发 G0 verdict。
