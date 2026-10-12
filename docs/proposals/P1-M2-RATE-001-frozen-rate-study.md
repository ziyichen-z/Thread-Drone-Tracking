# P1-M2-RATE-001 — 冻结协议下的 5/20 Hz 帧率对比（M2 rate study）

Status: CLOSED_PROTOCOL_INVALID（修订 11 round 2 经 Codex 接受，
2026-07-24）；批次 1 永久保留，不产生新测量；正式 5/20 Hz 义务转交
`P1-M2-RATE-002`
Author/role: Claude Fable / design ideation
Created: 2026-07-24
Last updated: 2026-07-24

## Problem and research value

M2a（`P1-TRACK-001`，已 DONE）给出了 5 Hz 基线：follow `C_track≈0.30%`、nadir `≈3.11%`，follow 比 nadir 差一个量级。可能的解释包括采样节奏效应（5 Hz 采样间相机位姿最多变化 24°，CSRT 无自运动补偿；Unity 执行本身连续）与外观困难（低多边形车体 + JPEG85 + 小目标；nadir 也仅 3.11%）。

本项在**除帧率外全部冻结**的协议下做 2×2 对比（{5, 20} Hz × {follow, nadir}），交付两件事：正式 M2 的 5/20 Hz 对比要求（v0.3.1 §3.6），以及深度 SOT 插件是否立项的**预注册判定证据**。

**分析定位（修订 5）**：本闭环实验**不构成 H1/H2 的因果识别**——在 follow 条件下提高 `capture_hz` 同时改变追踪器输入节奏与云台指令更新节奏，且 `C_track_given_geom` 的条件分母本身可被 follow 控制器改变。follow/nadir × 5/20 交互只做**描述性诊断**呈现，并在证据文档中明确披露上述混杂。

## Proposed behavior

### 1. 实验单元、不变量与派生量

2 × 2 = 4 个 cell：{5 Hz, 20 Hz} × {follow, nadir}，每 cell 固定 N=3。**唯一自变量及其时间等效派生量**：

| 项 | 5 Hz cell | 20 Hz cell | 理由 |
|---|---|---|---|
| `sensor.capture_hz` | 5 | 20 | 自变量 |
| `sensor.retained_frame_count` | 128 | 512 | 保留窗口**时长**不变（25.6 s） |
| `evaluation.maximum_pending_frame_count` | 512 | 2048 | evaluator 待决窗口**时长**不变（102.4 s）（修订 4） |
| `scenario_id` | `rate-study-5hz` | `rate-study-20hz` | 证据标注 |
| init `frame_id` | 派生 | 派生 | init 仿真时间窗相同，见 §2 |

其余一切逐字节相同：路线、车速、云台限位/转速、分辨率/FOV/JPEG 质量、tracker 及 pin 版本、`.venv-track`、`--ground-plane-y-m`（显式提供，入 manifest）、planned_duration 公式（`2×周长/车速+60 s`）。两档条件通过两份**入库**的 scenario 覆盖文件实现（安装时记录 SHA-256），不改 C# 运行时行为。

**两个时钟的用途（修订 4；Unity 修订 10）**：证据同时记录①**仿真时间采样节奏**（相邻帧 `simulation_time_s` 间隔）与②**墙钟采集节奏**（现有协议使用相邻帧 `capture_unix_s` 间隔；若未来新增并版本化 `published_unix_s`，则另行报告发布完成吞吐）。可持续性判据 S1 用②，S2/S3 用追踪进程自身测量；评测积分权重天然基于①。全体帧的墙钟 cadence 继续作为 raw 诊断保留；S1 cadence 只使用 `capture_unix_s >= manifest.created_unix_s` 的 post-launch 帧。该 cutoff 在 tracker launch 开始、用户解除暂停之前冻结，因此排除的是 staging 后人工确认停顿，cutoff 之后的任何真实运行中卡顿仍计入 S1。

### 2. 初始化策略（修订 1；Unity 修订 9：按帧率档冻结，不跨图像复用框）

- **每个帧率档一次标定会话**（不计入 N=3）：全新 Play，等待声明窗口 `simulation_time_s ∈ [7.0, 8.0)` 内首个已发布帧，dump 并冻结为该档**参考帧**——记录其精确 `simulation_time_s`、`frame_id`、图像 SHA-256；在该参考帧上标注该档**参考框**。标定后该会话作废，不作测量用。
- follow 与 nadir 共用**同一档的**冻结参考帧/框（两种模式初始相机态同为锚点上方 nadir，初始图像同分布）；同档全部 6 个测量 run 复用，不再逐 run 标注。
- 测量 run 内，init 帧取**本 run** 声明窗口内首个已发布帧，配冻结参考框启动；开跑前操作者 dump 该 init 帧目视确认框仍落在目标车上。**确认失败只能作废并重开本次会话（排查原因后重试），不得改标任何已测 cell、不得移用其他档的框**。

**Unity 修订 9（2026-07-24）**：第一次真实 5 Hz 标定证明原
`[3.0,4.0)` 窗口内的红色目标与黄色干扰车持续重叠（frames 15–19，
`3.180–3.982 s`），无法产生可由操作者确认的无歧义紧框；到 frame 35
（`7.181 s`）两车已有清晰间隔。用户据此批准在任何标定或测量数据产生前，
把两档共同的确定性窗口改冻为 `[7.0,8.0)`。该修订不改变帧率、路线、车速、
相机、评测、N、持续时长或判定规则；5/20 Hz 仍使用完全相同的仿真时间窗口。
所有拟用框必须以**实际矩形叠加图**交给操作者确认，不能只报告数值坐标。

### 3. 重复与汇总规则（修订 2：固定 N，预声明稳健汇总）

- 每 cell 固定 **N=3** 次全新 Play 会话，共 12 次测量会话（+2 次标定会话）；无条件补跑规则；
- 报告形式：**逐 run 全量数字 + cell 中位数 + 极差**；
- **判定统计量预声明为 cell 中位数**——阈值附近的混合结果由中位数唯一裁决，单个 run 无否决权；该规则在数据采集前冻结。

### 4. 20 Hz 可持续性判据与失败语义（修订 3：不可替代）

高帧率 cell 每个 run 须满足：

- **S1** 实测墙钟采集帧率 ≥ 19 Hz（名义 95%）；
- **S2** tracker 计算时延 p95 < 50 ms；
- **S3** backlog p95 ≤ 1 帧且无 `ERROR_REINIT_REQUIRED`。

任一不满足 → 该 run 标 `RATE_UNSUSTAINABLE`、证据保留。**20 Hz 是本项验收与正式 M2 关闭不可替代的高帧率档**：若 20 Hz 反复不可持续，本工作项以环境/实现阻塞状态**返回 Codex**归因（或由用户显式启动设计变更），不得以其他帧率顶替。10 Hz 仅可作为**明确标注的补充诊断**加跑，不计入验收，不进入判定规则。

**Unity 修订 10（2026-07-24）**：真实 r1/r2 证明原 whole-span S1
把暂停等待框确认的 `99.031/74.757 s` 计入分母，而对应仿真只前进
`0.055/0.067 s`。raw whole-span cadence 因此仍报告但不作 S1 判定。
post-launch cohort 必须记录 cutoff、首个 eligible frame、eligible/excluded
样本数和 cadence；cutoff 缺失、非有限或 eligible 样本不足 2 个时 S1
fail-closed。既有原始时间戳足以确定性重算，无须重跑 r1/r2。

### 5. 预注册判定规则（修订 6：地板 + 连续性双条件）

主结局为 `C_track`（协议主指标）；判定规则作用于诊断量。**触发 `P1-TRACK-002`（深度 SOT 插件提案）当且仅当满足任一**（均按 §3 的 cell 中位数，作用于 20 Hz follow cell）：

- **R1 精度地板**：`C_track_given_geom` 中位数 **< 25%**；
- **R2 连续性**：`time_to_first_LOST`（init 帧至首个 `LOST` 事件的仿真时长；整程无 LOST 记为 ≥ 实际时长）中位数 **< 一个环路周期**（`路线周长/车速`，由运行脚本写入 manifest）。理由：只在前段正确、随后长期丢失的追踪器，无论均值多高，都不是 M3 滤波可用的测量流——**不允许用 Kalman 掩盖永久丢失的测量源**。

配套要求：

- **阈值敏感性报告**：在 {15%, 25%, 35%} 三档地板下分别给出 R1 判定是否翻转；翻转发生时如实标注结论脆弱性（不改变按 25% 预注册值做出的正式判定）；
- 两条规则触发的都是**提案**，仍走 Codex 接受门；CSRT 永久保留为经典对照档；
- 阈值与规则仅可在本提案接受时协商修改，数据产出后冻结。

### 6. 前置条件：evaluator 聚合与状态机的直接测试（修订 7）

任何对比 run 被采信前，需合入并通过覆盖以下内容的 Edit Mode 直接测试（作用于 `CoverageEvaluator` 本体，非其数学助手）：

1. 时长加权聚合：可见/不可见 × 成功/失败帧序列，含 `DeltaSimulationSeconds` 缺失时 `1/capture_hz` 回退权重路径（20 Hz 下权重缩 4 倍）；
2. **承重状态转移**：matched / incorrect / duplicate（同帧第二观测被忽略）/ unmatched（未知 frame_id）各自的计数与时长归属；
3. **pending 修剪**：在时间等效的 5/20 Hz 设置（512 vs 2048）下，修剪不影响任何已采信观测的归属；
4. 数值容差：聚合比值断言相对误差 ≤ 1e-5，时长累计绝对误差 ≤ 1e-4 s。

### 7. 持久证据

- 复用 `p1-track-run/v1` run 目录 schema（`time_to_first_LOST` 由 frames.jsonl 推导，无 schema 变更）；12 个测量 run + 2 个标定会话全部归档；追踪进程须在 planned duration 结束、用户停 Play 之前生成权威 `metrics.final.json`，后续步骤只校验和归档，不得以仍在增长分母的 `runtime/metrics.json` 覆盖；
- 汇总证据文档 `docs/evidence/P1-M2-RATE-001.md`：逐 run 表、cell 中位数/极差表、两时钟记录、可持续性判据核对、判定规则逐字引用与判定、阈值敏感性表、混杂披露段、覆盖文件与参考帧哈希。

### 8. 可执行会话协议（修订 8：12+2 次会话的逐步清单）

**Run ID 规则**：`rate{5|20}-{follow|nadir}-r{1|2|3}`；标定会话 `rate{5|20}-calib`。每次尝试的 ID 均不可变且不可复用；无效尝试使用 `-invalid-a` 等唯一后缀并保留目录、标 `INVALID`（附原因），补跑成功后才占用对应的规范 `-r1/-r2/-r3` 身份，不删除证据。

每档先执行标定会话（步骤 A），再执行 6 个测量 run（步骤 B）：

**A. 标定会话（每档一次）**
1. 安装该档覆盖文件至 `runtime/scenario_config.json`，记录 SHA-256；
2. 清理运行时槽位：`tracking_observation.json`、`gimbal_command.json`、`body_command.json`、`frames/`、`metrics.json`（`runs/` 归档不动）；
3. 全新 Unity Play；等待声明窗口内首个已发布帧；
4. dump 该帧，记录 `frame_id`/`simulation_time_s`/SHA-256，标注该档参考框；
5. 停 Play，会话记录归档为 `rate{X}-calib`，不计入 N。

**B. 测量 run（每档 × {follow, nadir} × 3）**
1. 确认覆盖文件仍为该档（复核 SHA-256）；清理运行时槽位（同 A2）；
2. 全新 Unity Play；
3. 运行脚本以冻结参考框 + 本 run 声明窗口首帧启动追踪进程（follow 或 nadir 模式；`--ground-plane-y-m` 显式传入），并把周长/车速/planned_duration/loop_duration 写入 manifest；
4. dump 本 run 的 init 帧，目视确认框落在目标车上；失败 → 本会话作废（标 `INVALID`），排查后重开；
5. 运行至 `planned_duration_s` 结束；追踪进程收尾（或 `--finalize`）；
6. 确认追踪进程已在 planned duration 结束时、停 Play 前生成场景匹配的 `metrics.final.json`；停 Play 后仅校验并归档该快照，不得用后续 `runtime/metrics.json` 覆盖；缺失或场景不匹配则标记本次尝试 `INVALID`；
7. 按 Run ID 规则归档 run 目录，登记进证据文档草稿行。

S1 的 measurement cohort 从步骤 3 写入的 `manifest.created_unix_s`
开始；步骤 4 之前已捕获的 retained/staged 帧不进入 S1，但仍保留在 raw
cadence、tracker 记录和初始化证据中。

### 修订 11（round 2，2026-07-24，已并入 Codex 审查全部 8 条）：批次 1 处置与本研究关闭

范围收窄声明：round 1 中的起跑屏障、载体更换、时钟前置与新 campaign 全部
移出本修订，进入独立继任提案 `P1-M2-RATE-002`（Codex 修订 5）。本修订只
处置批次 1 与关闭本研究。

**A. 批次 1 处置（修订 1：事实修正）。** 全部 12 个测量 run + 2 个标定
会话永久保留，原 per-run 文件与其历史 `COMPLETE` 采信结果不可变；批次级
状态标注 `BATCH1_PROTOCOL_INVALID`（科学判定无效）。准确事实：**11 个
run 各有 1 条发布观测（init 时发出），但 evaluator 匹配为 0**——发布与
匹配是两件不同的事实，不得合并表述。无效性归因于**陈旧初始化 + 突发积压
消化 + 仅最新发布**协议缺陷（init 帧在追踪器启动时已 67–302 s 旧，初始
backlog 28–201 帧，CSRT 在所选仿真帧后约 3.4 s 报 LOST）；目标在固定
nadir 视角下驶出视野是**预期几何条件**，右缘初始化属于**低功效初始化选择
**，两者本身不是协议缺陷。`rate20-follow-r3` 为 spurious-`ok` 漂移分叉
（数千条多数错误的发布）。

**B. 判定规则关闭（修订 5 前半）。** R1/R2 随本研究关闭，判定结果 =
`UNDETERMINED_INVALID_INPUT`：规则未被触发，也不移植到任何新载体——继任
研究必须重新预注册自己的规则（含针对不自报丢失追踪器的连续性等价判据）。
原验收标准 7（5 Hz 与 CSRT M2a 基线量级一致性）随关闭作废，其不一致已由
A 段归因解释并归档。

**C. 本研究关闭形态。** `P1-M2-RATE-001` 保留为 **CSRT 协议失败研究**：
批次 1 是协议缺陷机制与 CSRT 随机失败模式（如实报失败 vs spurious-ok
漂移二态）的证据档案。本研究不再产生任何新测量；正式 M2 的 5/20 Hz 对比
义务由 `P1-M2-RATE-002` 承接。时钟完整性交接（`rate20-nadir-r3`）随本
研究关闭归档：该 run 保持 fail-closed 判定不翻案，单调时钟作为继任研究的
**前置基础设施**（非缓议项）在 `P1-M2-RATE-002` 中定义。

## Inputs, outputs, and affected interfaces

- 新增：`config/` 两份入库覆盖文件；运行脚本扩展（cell 编排、manifest 增记 loop_duration、汇总表与敏感性表生成、`time_to_first_LOST` 推导）；C# Edit Mode 聚合/状态机测试（前置条件，测试代码，不改运行时行为）。
- 复用不改：帧包/观测/云台协议、`p1-track-run/v1`、`.venv-track`、追踪进程本体。
- 边界不变：追踪进程不读 scenario config 与任何真值；实验编排（含时长/周长计算）在运行脚本层。

## Compatibility with the current v0.3.1 design

- 落实 §3.6 的"5/20 Hz 两档分别报告"与执行拆分段（与 `P1-TRACK-001` 共同构成正式 M2 关闭候选）；20 Hz 不可替代性与该节的正式要求一致；
- 不触碰 §3.3/§4/§5；主结局用 §6 的主指标 `C_track`，不改任何指标定义；
- M2 正式关闭仍需 `DR-P1-M2-001` 新鲜上下文设计审查，本项验收不包含也不替代该门。

## Acceptance criteria

1. **前置**：§6 测试先行合入并全绿（Unity Edit Mode + 既有 Python 测试），此后产生的 run 方可采信；
2. 2 次标定会话 + 12 次测量 run 按 §8 协议完成；manifest/证据含全部要求的哈希与时钟记录；`INVALID` 会话保留并补跑；
3. 20 Hz cell 逐 run 通过 S1–S3，或如实记录 `RATE_UNSUSTAINABLE` 并把工作项按环境/实现阻塞返回 Codex（此时不做判定、不顶替帧率）；
4. 报告逐 run + cell 中位数/极差的完整指标集：`C_track`（主）、`C_geom`、`C_track_given_geom`、matched/incorrect/unmatched 计数、`time_to_first_LOST`、质量诊断、LOST/GAP/GEO_REJECT、compute p50/p95、frame age p50/p95、两时钟实测节奏；
5. §5 判定规则（R1+R2）被逐字引用并按 cell 中位数判定；阈值敏感性表一并给出；结论写入证据文档与状态板；
6. 交互呈现为描述性诊断，证据文档含混杂披露段（指令节奏与条件分母均随 follow 改变）；
7. 5 Hz cell 与 `P1-TRACK-001` 基线量级一致性检查，显著偏离需解释；
8. 边界审计不变；
9. Unity 用例 `UT-P1-M2-RATE-001-001`：用户按 §8 清单执行并反馈。

CSRT 在任何 cell 的表现好坏不构成实现门失败；实现门只看协议忠实执行与证据完整性。

## Baselines and ablations

本项即"帧率"单变量受控对比；5 Hz cell 同时复现检验 `P1-TRACK-001`。10 Hz 如加跑仅为标注明确的补充诊断。

## Failure modes and resource risks

- **20 Hz 不可持续** → `RATE_UNSUSTAINABLE`，按 §4 返回 Codex 归因，不顶替；
- **两档都趴地板** → R1 触发 `P1-TRACK-002`，本项仍算判定成功；
- **cell 内极差大**（Unity 时序抖动）→ N=3 中位数裁决 + 如实报告极差与可比性限制；
- **标定框跨会话失配**（初始像面位置漂移超预期）→ 按 §2 作废重开；若反复失配，说明"跨会话初始条件近似不变"假设不成立，如实上报并申请协议修订（显式流程，非静默处理）；
- 磁盘/IO 与操作负担：20 Hz ~1 MB/s、保留窗 ~25 MB 无压力；14 次会话是用户门的已知劳动量，已在 §8 内最小化单次成本。

## Suggested implementation scope

两份覆盖文件 + 运行脚本扩展 + C# Edit Mode 测试 + 证据文档；一个实现批次。**Out of scope**：深度 SOT 插件本体、M3 预测、任何运行时 C# 行为变更、正式 M2 关闭宣告（还差 `DR-P1-M2-001`）。

## Open questions

无。R1 阈值 25% 与 R2 连续性窗口（1 个环路周期）仅可在本轮接受时协商，数据产出后冻结。

## Codex review decision

### Round 1 — 2026-07-24: REVISION_REQUESTED

Decision: **REVISION_REQUESTED**

Rationale:

The proposal correctly preserves CSRT as a frozen classical baseline, turns
the required 5/20 Hz comparison into a reproducible work item, places direct
duration-weighted evaluator coverage before comparative use of `C_track`, and
keeps the M2 fresh-context design audit separate. The 2×2 follow/nadir
structure is useful: nadir measures a stationary-camera rate effect while
follow measures the complete rate-sensitive closed loop.

It is not implementation-ready yet. The current initialization rule asks
non-identical 5/20 Hz images to share one normalized box but also permits
conditional relabeling, which both weakens correctness and reintroduces
operator variance. The adaptive N=2 rule is circular because the decision to
add a replicate depends on the cross-rate difference being estimated from
those same runs. A 10 Hz fallback cannot satisfy the canonical M2 requirement
for a 5/20 Hz comparison. The invariants table also holds the evaluator's
pending-frame *count* fixed, making its pending time window four times shorter
at 20 Hz.

Finally, this closed-loop experiment cannot by itself causally identify
"sampling" versus "camera self-motion": raising `capture_hz` in follow changes
both tracker input cadence and gimbal-command update cadence, and
`C_track_given_geom` conditions on a denominator that the follow controller
can itself change. The interaction remains a valuable diagnostic, but it must
not be described as proof that H1 or H2 is dominant. The SOT go/no-go rule also
needs a continuity criterion; accepting a tracker that is correct for only
25% of geometrically visible time and then remains permanently `LOST` would
provide an unsuitable measurement stream for M3.

Required revisions:

1. **Make the initialization policy deterministic without applying one box to
   different images.** Select the first frame in a declared simulation-time
   window at each rate, record its exact `simulation_time_s` and image SHA-256,
   and annotate one rate-specific reference box before any measured run.
   Because follow and nadir both start from the same nadir camera state, they
   must share that rate's frozen reference frame/box. All repetitions reuse
   it. A pre-run visual check may invalidate and restart a session, but must
   not silently relabel a measured cell.
2. **Use a fixed replicate count.** Set every cell to N=3 and report all runs
   plus median and range (or another predeclared robust summary). Remove the
   circular conditional-third-run rule. Define how mixed results around a
   decision threshold are resolved before data collection.
3. **Keep 20 Hz as the required high-rate condition.** A 10 Hz run may be
   retained as an explicitly supplementary diagnostic, but it cannot replace
   20 Hz for this work item's acceptance or formal M2 closure. If 20 Hz is
   unsustainable, record `RATE_UNSUSTAINABLE` and return the work item as an
   environment/implementation blocker or request an explicit design change.
4. **Freeze time semantics, not only frame counts.** Add
   `evaluation.maximum_pending_frame_count` to the derived-rate variables so
   its pending duration is equal across rates, or demonstrate and test why it
   cannot affect any admitted observation. Record both simulation-time sensor
   cadence and wall-clock publication throughput; state exactly which one each
   sustainability threshold uses.
5. **Reframe the analysis as diagnostic, not causal identification.** Report
   `C_track` as the primary outcome alongside `C_geom`,
   `C_track_given_geom`, matched/incorrect counts, and time to first `LOST`.
   Present the follow/nadir rate interaction descriptively and disclose that
   follow changes the closed-loop command cadence and the conditional
   denominator. Correct "24°/帧跳变" to "up to 24° camera-pose change between
   5 Hz captured samples"; Unity actuation itself still updates continuously.
6. **Strengthen the SOT-upgrade decision.** Retain a pre-registered
   `C_track_given_geom` floor only with a clear robust cell-summary rule and
   threshold sensitivity report. Add a continuity requirement tied to the
   downstream use: if the high-rate follow condition cannot maintain valid
   tracking until at least one deterministic route-loop duration (using the
   predeclared N=3 summary rule), it must also trigger `P1-TRACK-002`.
   Kalman/M3 must not be used to disguise a permanently lost measurement
   source.
7. **Make the aggregation precondition cover the load-bearing state
   transitions.** In addition to weighted visible/success/failure frames and
   the `1/capture_hz` fallback, directly test matched, incorrect, duplicate,
   unmatched, and pending-frame pruning behavior at time-equivalent 5/20 Hz
   settings. Specify numeric tolerances.
8. **Add an executable session protocol.** Define config installation,
   runtime-slot cleanup, fresh Play start/pause, reference-frame selection,
   tracker launch, completion/finalization, invalid-run handling, run IDs, and
   artifact/config hashing. This may be implemented by helpers later, but the
   proposal must first make the 12 user sessions unambiguous.

Accepted design-document changes:

None in this round. The canonical requirement for a frozen-protocol 5/20 Hz
comparison remains valid; its detailed protocol will be synchronized only
after a revised proposal is accepted.

### Round 2 — 2026-07-24: ACCEPTED

Decision: **ACCEPTED**

Rationale:

Round 2 closes all eight Round 1 requirements. Initialization is now frozen
per rate on hashed reference images and shared correctly across the two
initially-nadir controller conditions; replication is fixed at N=3 with a
predeclared median/range summary; 20 Hz is no longer replaceable by a more
convenient rate; both retained and evaluator-pending windows preserve duration
rather than frame count; wall and simulation clocks have separate roles; the
interaction is explicitly diagnostic rather than causal; the SOT decision has
both conditional-coverage and one-loop continuity gates; the evaluator tests
cover the load-bearing state transitions; and the 12+2 session protocol is
operationally bounded.

The design is therefore reproducible and falsifiable enough to implement.
CSRT performance itself remains an experimental result, not an implementation
success criterion. A triggered `P1-TRACK-002` still enters as a proposal and
does not silently broaden this work item.

Binding implementation clarifications:

1. **S1 clock calculation (amended by user after Unity diagnosis).** Unless an
   explicit per-frame `published_unix_s` is added and versioned, S1 uses the
   existing finite `capture_unix_s` values in `frames.jsonl` and is named
   **post-launch wall-clock capture cadence**. Select
   `capture_unix_s >= manifest.created_unix_s`, then calculate
   `(N-1)/(last-first)` over that cohort. Report cutoff, first eligible frame,
   eligible/excluded counts, and interval p50/p95. Preserve the former
   whole-span cadence separately as raw diagnostic evidence. Do not label
   `capture_unix_s` as a publication-completion timestamp. Missing/invalid
   cutoff or fewer than two eligible samples fails S1 closed.
2. **Metrics cutoff.** The authoritative `metrics.final.json` is the existing
   tracker-finalization snapshot taken immediately when the planned run ends,
   before the user stops Play. Session step B6 verifies and archives that
   snapshot; it must not overwrite it with a later `runtime/metrics.json`
   whose denominator continued growing after tracker completion. A missing or
   scenario-mismatched final snapshot makes the run `INVALID`.
3. **Invalid-attempt identity.** Every attempt has a unique immutable run ID.
   Invalid attempts use a suffix such as `-invalid-a`; the replacement that
   fills a cell replicate receives the canonical `-r1/-r2/-r3` identity (or an
   explicit attempt field in the evidence table). Existing run directories are
   never deleted or reused.
4. **Metric semantics stay frozen.** The new direct evaluator tests may expose
   a defect, but no change to `C_geom`, `C_track`, or
   `C_track_given_geom` semantics may be folded silently into this rate study.
   Any semantic correction requires an explicit design decision and invalidates
   older comparison runs that used the prior definition.
5. **Review sequencing.** Codex forms a stable code/tooling candidate after
   the two configs, orchestration/summary helpers, and expanded Edit Mode tests
   pass. Sonnet reviews that candidate before the user starts the 12 measured
   Unity sessions. After accepted runs complete, formal M2 closure still
   requires the separately recorded `DR-P1-M2-001` fresh-context design audit.
6. **Initialization-window amendment.** Before any calibration artifact or
   measured run existed, Unity validation rejected `[3.0,4.0)` because the
   target and distractor overlap. The user accepted `[7.0,8.0)` based on clean
   retained evidence. Both rates use this same half-open simulation-time
   window, and every proposed reference box is shown as a rectangle overlay
   before capture. This amendment requires a focused Sonnet re-review.

Required revisions:

None.

Accepted design-document changes:

- Record the fixed N=3 `{5,20} Hz × {follow,nadir}` diagnostic protocol,
  time-equivalent retention/pending windows, dual-clock sustainability
  semantics, and the non-substitutable 20 Hz condition.
- Record that `P1-TRACK-002` is triggered by either the pre-registered 25%
  conditional-coverage floor or failure of the 20 Hz follow median to remain
  valid for one route-loop duration.
- Record the evaluator aggregation/state-machine tests as an admissibility
  precondition and retain `DR-P1-M2-001` as a separate M2 closure gate.

## Round 2 revision map（修订 → 落点）

| Codex 修订 | 落点 |
|---|---|
| 1 初始化确定性 | §2（按档标定会话冻结参考帧/框 + SHA-256，follow/nadir 共用，失败只作废不改标）；§8-A |
| 2 固定 N=3 | §3（12 次测量会话，中位数+极差，中位数为唯一判定统计量）；§8 |
| 3 20 Hz 不可替代 | §4（`RATE_UNSUSTAINABLE` → 阻塞返回；10 Hz 仅补充诊断）；Acceptance 3 |
| 4 时间语义冻结 | §1（`maximum_pending_frame_count` 512→2048；两时钟定义与各判据归属） |
| 5 诊断性改述 | Problem 段（混杂披露、24° 表述修正）；§5 主结局改 `C_track`；Acceptance 4/6 |
| 6 判定规则强化 | §5（R1 地板 + R2 连续性双触发、阈值敏感性表、不许用 M3 掩盖丢失） |
| 7 聚合测试扩栏 | §6（matched/incorrect/duplicate/unmatched/pending 修剪 + 数值容差） |
| 8 可执行协议 | §8（A/B 步骤清单、Run ID、INVALID 处理、哈希记录） |
| 9 Unity 初始化窗口修订 | §2（`[3,4)` 因目标/干扰车重叠作废；两档统一改为 `[7,8)`；冻结前必须展示矩形叠加图） |

### Amendment 11 review — 2026-07-24: REVISION_REQUESTED

Decision: **REVISION_REQUESTED**

Rationale:

The first batch must not support a formal rate or R1/R2 conclusion. Direct
artifact inspection confirms that the initialization frame was already
`67–302 s` old in wall time when the tracker started, initial
`backlog_count` reached `28–201`, and 11 runs produced only the initialization
publication before CSRT reported LOST about `3.4 s` after the selected
simulation frame. The exceptional `rate20-follow-r3` instead stayed
spuriously `ok` and published thousands of mostly incorrect boxes. Preserving
the batch as protocol-failure evidence is therefore correct.

Amendment 11 is not yet safe to accept. Part A says those 11 runs had "zero
publication"; their raw logs actually contain one published observation each,
while evaluator `matched=0`. Those are different facts and must not be
collapsed. Target FOV exit under fixed nadir is also an expected geometric
condition, not by itself a protocol defect; the decisive defect is stale
initialization plus burst processing and latest-only publication.

Part B still depends on a human pausing "immediately" inside a one-second
window. That is neither deterministic nor automatable, and it can reproduce
the same stale-frame failure. Part C then changes the frozen tracker while
retaining the old work ID and its rules. This destroys the original
same-tracker lineage, makes the 5 Hz consistency check against CSRT invalid,
and creates a circular rule in which `P1-TRACK-002` is both the triggered
upgrade and the object to which the trigger is reapplied. Part D knowingly
starts another 14-session campaign on an adjustable civil clock even though a
clock regression has already occurred.

Required revisions:

1. **Correct the batch-1 disposition.** Use a status such as
   `BATCH1_PROTOCOL_INVALID`/`SCIENTIFIC_DECISION_INVALID`, while preserving
   the original per-run files and their historical `COMPLETE` admission
   result. State accurately that 11 runs each have one publication but zero
   evaluator matches. Attribute invalidity to the stale-init/backlog protocol;
   treat right-edge/FOV exit as a low-power initialization choice, not the
   sole defect.
2. **Define evidence-preserving batch identities.** The existing canonical
   `rate*-r*` directories are immutable and occupied. A replacement campaign
   needs a versioned study/batch ID and unique run IDs, selection rules that
   exclude batch 1, and tests proving summaries cannot mix batches or tracker
   identities.
3. **Replace manual immediate pause with a machine-enforced start barrier.**
   Unity must publish a deterministic initialization frame/state, hold target
   motion and evaluation time, allow box confirmation and tracker
   initialization, then release on an explicit command. Define the sensor,
   simulation clock, evaluator, and S1 cutoff behavior across this barrier.
   Add Edit Mode/Play Mode tests for zero stale backlog and the release
   transition. A human timing instruction is not sufficient.
4. **Freeze a viable initialization state before measurement.** The target
   must be separated from distractors and have a predeclared image-border
   margin. Establish this with a non-measured scouting/calibration artifact,
   then freeze the state/box before any accepted batch-2 run. Do not select a
   better start from measured outcomes.
5. **Separate the new algorithm campaign.** Keep `P1-M2-RATE-001` as the
   preserved CSRT protocol-failure study and create a versioned successor
   (recommended `P1-M2-RATE-002`) for the corrected protocol plus the accepted
   `P1-TRACK-002` vehicle. Remove the now-invalid "5 Hz must match CSRT
   baseline magnitude" criterion. Replace the circular R1/R2 destination with
   an explicitly named downstream decision (for example, detector/arbiter
   escalation) or close those rules with the original invalid batch and use a
   newly predeclared qualification gate.
6. **Fix the known clock defect before recollection.** Make the proposed
   versioned monotonic capture timestamp a prerequisite, not a deferred
   suggestion. Preserve Unix time for cross-process correlation, use the
   monotonic field for S1 cadence, define reset/epoch semantics, and pass the
   required protocol/time-semantics Sonnet stop point before Unity runs.
   `INVALID_CLOCK` remains useful for missing/non-finite/non-increasing
   monotonic data, with immutable attempt IDs and a bounded retry rule.
7. **Add a short qualification gate before 2+12 sessions.** The selected
   frozen tracker must pass the corrected live start barrier, 20 Hz
   sustainability, and a predeclared non-floor correctness/continuity smoke.
   A failed candidate returns to design without consuming the full user
   campaign and without tuning on the pilot.
8. **Update scope honestly.** The revised work necessarily changes Unity/C#
   experiment-start behavior, time/frame semantics, Python orchestration,
   run identity, and tracker selection. It therefore requires implementer
   tests, a stable candidate, Sonnet review, and focused Unity validation
   before the new measured batch.

Accepted design-document changes:

None in this round. Batch 1 remains preserved and no additional Unity
measurement is authorized until the successor protocol and tracker proposal
are accepted and pass their respective stop points.

### Amendment 11 round 2 review — 2026-07-24: ACCEPTED

Decision: **ACCEPTED**

Rationale:

The revised amendment accurately separates publication from evaluator
matching, identifies stale initialization/backlog/latest-only publication as
the decisive protocol defect, treats nadir FOV exit as expected geometry and
the right-edge start as a low-power choice, and preserves every original
artifact and historical per-run admission result. It closes R1/R2 as
`UNDETERMINED_INVALID_INPUT` rather than retroactively claiming that they
triggered, and moves every structural change and new tracker campaign into a
distinct successor work ID.

This work item is therefore closed as `CLOSED_PROTOCOL_INVALID`, not `DONE` and
not a successful rate comparison. Existing Round 1–4 Sonnet verdicts remain
valid only for the tooling candidates they reviewed; they do not turn batch 1
into scientifically admissible evidence. No additional
`P1-M2-RATE-001` measurement or canonical run-ID reuse is permitted.

Binding closure clarifications:

1. `BATCH1_PROTOCOL_INVALID` is a batch-level scientific disposition. It does
   not rewrite immutable run files that recorded `COMPLETE` artifact/duration
   admission.
2. The generated fail-closed clock result for final r3 remains archived and is
   not reinterpreted.
3. The superseding amendment controls over the now-historical acceptance
   criteria, baseline, failure-mode, and implementation-scope sections above;
   none authorizes more RATE-001 execution.

Required revisions:

None.

Accepted design-document changes:

- Record RATE-001 as the preserved CSRT protocol-failure study with no formal
  frame-rate or R1/R2 conclusion.
- Transfer the still-open formal M2 5/20 Hz obligation to
  `P1-M2-RATE-002`.
