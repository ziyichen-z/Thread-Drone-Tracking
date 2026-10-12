# P1-M2-RATE-002 — 继任帧率研究（机器起跑屏障 + 单调时钟 + NanoTrack-v2 载体）

Status: ACCEPTED_WITH_BINDING_CLARIFICATIONS (round 3 — 2026-07-24)；修订 A1
round 2（T-停止预注册 + decision_a 工件 + 执行门）Codex
`ACCEPTED_WITH_BINDING_CLARIFICATIONS`（2026-07-25）
Author/role: Claude Fable / design ideation
Created: 2026-07-24
Last updated: 2026-07-25

## Problem and research value

`P1-M2-RATE-001` 已以 `CLOSED_PROTOCOL_INVALID` 关闭，正式 M2 的 5/20 Hz
对比义务由本项承接。本项结构性修复批次 1 的四个缺陷：陈旧初始化、人工
计时不可复现、民用时钟可回退、同追踪器谱系断裂。继承有效资产：2×2×3
矩阵与时间等效派生量表、双时钟语义、诊断性分析定位与混杂披露、
`metrics.final.json` 权威快照语义、evaluator 聚合测试（已 DONE）、
`DR-P1-M2-001` 门外置。

## Proposed behavior

### 1. 实验状态机（round 3：Unity 拥有状态；ARMED 折叠进单一 release 事务）

```
HOLD ──(携 ready 证据载荷的 release 命令，Unity 事务内终验通过，恰好一次)──► RELEASED
  │
  └──(显式 abort 命令 / Unity 检出致命身份不一致)──► ABORTED（终态，本次尝试 INVALID）
```

- **状态属主是 Unity**：协调器只发送命令与收集证据，无权直接改变实验状态。按 Codex 第二轮提供的折叠选项，**取消独立 ARMED 态**——其职责并入 release 事务本身，消除"外部验证后、命令到达前"的陈旧窗口；
- **HOLD**：目标车以冻结姿态在弧长 `s*`（§3）生成、速度 0；传感器**继续正常发布帧**；evaluator 不累计任何时长/计数；Unity 对运行时云台/机身指令一律不施加（拒绝并计数入日志）；
- **release 事务（原子）**：命令载荷 = 协调器最后一次一致读取得的 tracker-ready 心跳快照（§2）+ study/run/command 身份。Unity 在处理该命令的**同一 Update 周期内做权威终验**：载荷 schema、TRACKING 状态、完整 tracker/model/init 身份及哈希与当前场景/run 自洽，且 `0 ≤ 当前已发布 frame_id − 载荷.last_processed_frame_id ≤ 1`（未来帧证据同样拒绝；积压边界在事务内检查，检查与转换之间不存在竞态窗口）。通过 → 单次原子转换（目标运动、evaluator 累计、指令施加、测量时间基同时启用）并写出 release-ack（§5）；不通过 → 拒绝、持久化拒绝记录、状态保持 HOLD；
- **重复/迟到的 release**（RELEASED 之后到达）：**唯一语义 = 拒绝 + 持久化拒绝记录，状态保持 RELEASED**——明确不是 ABORT（消除 round 2 中"重复拒绝"与"非法转换即中止"的矛盾）；
- **ABORTED 的触发恰好两种**：①显式版本化 `abort` 命令；②Unity 在事务终验中检出与当前场景/run 身份冲突的致命不一致。其余一切无效命令（格式错误、过期、乱序、错误通道、HOLD 期的重复 release 尝试）一律拒绝 + 持久化 + 状态不变。

### 2. tracker-ready 实时心跳与无竞态终验（round 3：取代一次性记录）

- `tracker_ready.json` 由一次性记录改为**原子心跳**（schema `p1-rate2-tracker-ready/v2`）：追踪进程**每处理一帧后重发布**，且间隔不超过声明上限 1 s；字段在 round 2 基础上新增单调递增 `seq` 与追踪进程自身通过 `time.monotonic_ns()`（或同等系统单调时钟）取得的 `publisher_monotonic_s`。协调器与追踪进程必须位于同一主机，只有该同源单调时钟可用于心跳新鲜度比较；Unity 单调时钟属于独立 epoch，只用于 release/capture 边界；
- **操作者目视确认前置**（消除"验证后无界人工停顿"）：核对静态叠加框在 HOLD 期进行、时长不限（心跳持续刷新）；确认完成后协调器才进入终验-释放，**两步之间无人工停顿**；
- **协调器一致读算法**：读 `frames/latest.json` → 读心跳 → 校验 `seq` 较上次读取前进、心跳新鲜（`publisher_monotonic_s` 滞后 ≤ 2× 声明心跳间隔）、`0 ≤ latest.frame_id − last_processed_frame_id ≤ 1` → 全部满足则**立即**把该心跳文件的确切字节及 SHA-256 绑定进 release 命令并发送；任一不满足则有限次重试后放弃并记录；
- 协调器侧检查仅为预筛；**权威积压边界检查在 Unity 的 release 事务内**（§1），check-to-release 竞态由此闭合；
- 测试覆盖两个方向：健康移动指针（HOLD 帧持续发布、心跳跟进 → release 接受）与故意延迟追踪进程（心跳陈旧或事务内积压 >1 → 拒绝）。

### 3. 初始状态的确定性侦察（修订 6）

- **`s*` 定义**：沿 `route_world_m` 折线自 `route[0]` 起的弧长（米），路点间线性插值；候选网格为**精确集合** `{k·0.5 m | k = 0, 1, …; k·0.5 < P}`（P = 路线周长；不含 s = P 的回绕重复点，s=0 与环路终点不重复计入）；
- **资格判据（精确式）**：对候选点的 hold 相机（锚点上方 nadir 声明位姿）投影目标框 `[x,y,w,h]`（归一化 top-left）：
  - 边距：`min(x, y, 1−(x+w), 1−(y+h)) ≥ 0.15`；
  - 干扰分离：**"最近干扰"= 场景内全部活动干扰车投影框上的逐一最小值**；对该最小者要求 `IoU = 0` 且中心欧氏距离（像素）`≥ 1.0 × 目标框宽（像素）`；
- **确定性选择规则**：满足全部判据的**最小弧长** `s*`（无操作者裁量）；若候选集合为空则以 `INVALID_SCOUTING` fail-closed，禁止进入标定或试跑；
- **资格表整体归档**：侦察工具输出全部候选点的判据数值表（含不合格者），杜绝樱桃挑选；
- **真值边界说明**：资格表由 Unity 侧侦察工具生成，使用评测域的投影真值框——该产物属实验设计/评测域，**只用于选 `s*` 与归档**；追踪进程收到的仍是操作者在选定 hold 帧上人工标注的冻结参考框，真值不进入追踪输入；
- 冻结产物（`s*`、hold 参考帧、操作者标注框、全部 SHA-256）在任何测量前入库；两档共用同一 `s*`。

### 4. 测量时间基：一切从 release 起算（修订 3）

- `TrackLoop` 新增显式 release 基线：**等待 `release_ack.json` 出现，验证**其 study/run/command 身份与自身 run 身份及 init 哈希一致、三时戳有限且与后续帧单调相容，**验证通过后**才把记录切换为 `phase="measurement"` 并取用 `measurement_start_simulation_s` / `measurement_start_monotonic_s`；验证失败 → 本次尝试 fail-closed（`INVALID_RELEASE`）；
- **planned duration、`actual_duration_s`、`time_to_first_LOST`、evaluator 累计时长、`metrics.final.json` 权威截止**全部以 release 为原点；HOLD 期的追踪记录在 `frames.jsonl` 标 `phase="hold"`，仅作诊断，**排除在一切结局、时延、积压聚合与 R1′–R3′ 输入之外**；
- **长保持测试**：故意保持 ≥ 60 s 的 HOLD 后释放，证明时长判定与全部结局与短保持运行一致。

### 5. release 证据与不可变 manifest 的溯源链（round 3：选定"不可变初始 manifest + 独立溯源工件"方案）

- release 命令（schema `p1-rate2-release-command/v1`）包含 ready 心跳的确切字节（可逆编码）及 SHA-256、study/run/command、tracker/model/init 身份及哈希；Unity 在 RELEASED 转换时原子写出 `runtime/release_ack.json`（schema `p1-rate2-release-ack/v1`），除 `{command_id, study_id, run_id, release_frame_id, release_unix_s, release_monotonic_s, release_simulation_s}` 外，必须回显 release-command SHA-256、ready SHA-256、init frame ID/SHA-256、tracker/model 身份哈希，以及终验采用的 current/last-processed frame ID 与 backlog；
- **溯源方案（回应"manifest 先于 release 创建"）**：`RunLogger` 的初始 `manifest.json` **创建后保持不可变**，不做任何事后追改；release 后把收到的 release-command 和 Unity 产生的 release-ack 的**确切字节**分别归档为 run 目录内不可变文件，再由编排器一次性原子写出 `release_provenance.json`（schema `p1-rate2-release-provenance/v1`），记录两者 SHA-256、初始 `manifest.json` SHA-256 及 study/run/command/tracker 身份链；写出后同样不可变；
- summary/finalize、`TrackLoop` 与 S1′ 计算器验证整条链：manifest 哈希 ↔ provenance ↔ command 原文哈希 ↔ ready 原文哈希 ↔ ack 原文哈希 ↔ 命令 ID ↔ run/追踪器/init 身份；**S1′ 直接使用链内的 `release_monotonic_s`**；链上任何缺失/失配/非有限/epoch 错误（如 ack 单调时戳大于其后帧的单调时戳）/非递增 → **fail-closed**（`INVALID_RELEASE` 或 `INVALID_CLOCK`，按不可变尝试 ID 归档补跑）。

### 6. 释放前控制冻结（修订 4）

- 追踪进程在 HOLD 期可内部计算并记录 init 观测与 look-at（诊断），但**不发布**云台/机身指令；Unity 侧同时门控（双保险，§1 HOLD 语义）；
- release 边界上 follow 与 nadir 从**同一声明 nadir 相机/平台状态**出发，release 后 follow 才施加其首条指令；
- **Play Mode 断言**：release 前两条件的平台/相机位姿逐分量一致。

### 7. 单调采集时钟（沿 round 1，修订 6/9 补充回归范围）

- `SensorFrameWriter` 新增 `capture_monotonic_s`，schema 升版 `tethered-sensor-frame/v2`，保留 `capture_unix_s` 作跨进程关联；epoch = Unity 进程启动，仅会话内可比；
- S1′ cohort = `capture_monotonic_s ≥ release_monotonic_s`；`INVALID_CLOCK` 适用于单调数据缺失/非有限/非递增，不可变尝试 ID + 同 cell 补跑上限 2 次；
- **按真实调用链修订的迁移清单（round 3，取代 round 2 的错误清单）**：
  - **schema 强制点**（实际校验传感器元数据 schema 的位置）：`controller/track_loop.py::FrameRepository` 与 `tools/run_rate_study.py::_frame_candidates()`——在这两处测试 v2 的显式接受，以及本研究上下文中读到 v1 帧的明确拒绝（fail-closed，不静默降级）；
  - `geolocate`：消费**已解析映射**，不做 schema 校验——测试其字段契约（必需位姿/内参字段不变；新增 `capture_monotonic_s` 被容忍）；
  - run 记录构建与 summary：测试 monotonic 字段的往返与 S1′ 计算取数路径；
  - C# 侧：`SensorFrameWriter` 写出新字段、`SensorFrameInfo` 结构及其消费者（`CoverageEvaluator` 的 FramePublished 处理）——Edit Mode 测试覆盖；
  - **单独记录**：`controller.protocol.latest_frame_bundle()` 只校验 `tethered-frame-manifest/v1`（帧清单 schema，本次**不**升版），不属于传感器元数据迁移范围——不得对其测试不存在的 v2 行为。

### 8. 实验矩阵、批次身份与判定规则

- 矩阵/不变量/派生量表沿 round 1（{5,20} Hz × {follow,nadir} × N=3；`retained_frame_count`、`maximum_pending_frame_count` 时间等效缩放）；载体 = `P1-TRACK-002` 的 `nanotrack-v2` 插件，manifest 身份 fail-closed；
- 批次身份：`study_id="P1-M2-RATE-002-B1"`，run ID `rs2-r{5|20}-{follow|nadir}-{1..3}`、标定 `rs2-r{5|20}-calib`；混批次/混载体防护测试沿 round 1；
- **预注册判定规则（修订 8：边界闭合）**——作用于 20 Hz follow cell，全部输入仅取 release 后样本，触发去向 = 起草 `P1-DETECT-001` 且 M3 挂起：
  - **R1′**：`C_track_given_geom` 的 cell 中位数 < 25%；当某 run 几何可见时长为 0 或 `matched = 0` 时，该 run 的 `C_track_given_geom := 0`（确定性触发路径）；
  - **R2′**：**逐 run 比值** `incorrect/matched` 的 cell 中位数 ≥ 0.5；某 run `matched = 0` 时该 run 比值 **:= 1.0**（保守：零匹配即不可用测量流）；
  - **R3′（右删失闭合）**：每个 run **恰贡献一个值**——存在 LOST 事件则取 release 起算的首次 LOST 时刻；无 LOST 则取 release 基线的 planned duration 作为**右删失值**计入。中位数恒在固定的三值总体上计算，不随哪些 run 恰好报 LOST 而改变总体；中位数 < 1 个环路周期 → 触发；
  - 敏感性描述性报告：R1′ {15,25,35}%、R2′ {0.3,0.5,0.7}；数据产出后规则冻结。

### 9. 资格门（修订 7：与已接受的 TRACK-002 验收 4 同一次试跑，判据精确化）

**试跑调用冻结（round 3）**：资格试跑 = **20 Hz、follow 条件**，单次。pre-release warm-up 规则开跑前冻结为固定就绪条件：追踪进程须已在 HOLD 期处理 ≥ 20 帧且心跳 `seq ≥ 20`，方可进入操作者确认；**任何试跑结果不得反改该规则**。**单一固定的 30.0 s 窗口自 release-ack 确认基线起算**（试跑 planned duration = 30.0 s），必须全部满足：

1. S1′–S3 在窗口内通过（S1′ 基于 release-ack 单调时戳）；
2. 无 LOST / GAP / reinit 事件；
3. `C_track_given_geom ≥ 0.25`；
4. `matched_tracking_observations > 0`；
5. `incorrect_tracking_observations / matched_tracking_observations < 0.5`。

失败 → 冻结候选返回设计，不消耗 2+12 会话，不得用试跑数据调参。（"漂移主导发生"的模糊表述已废除，以上第 5 条为其精确替代。）

### 10. 会话流程概要

侦察 1 次（资格表 + `s*` 冻结）→ 每档标定 1 次（hold 帧 + 操作者框冻结）→ 资格试跑 1 次（§9，30 s）→ 测量 12 次。每次测量 run：prepare（配置/身份校验，并清除或断言不存在旧的 `tracker_ready.json`、`experiment_control.json`、`release_ack.json` 及同尝试残留槽位）→ Play 进入 HOLD → 追踪进程启动、静态帧 init、心跳开始 → **操作者核对静态叠加框（HOLD 内，不限时）** → 协调器一致读终验（与下一步之间**无人工停顿**）→ 携 ready 载荷的 release 命令 → Unity 事务内终验 → RELEASED + release-ack → 确切 command/ack 与 `release_provenance.json` 哈希链归档 → 运行至 release + planned duration → `metrics.final.json` → 停 Play → 归档。

### 修订 A1（round 2，2026-07-25，已并入 Codex 全部 6 条修订）：测量执行顺序与判定点 A（T-停止预注册）

**动机（表述已按修订 4 收窄）**：§8 判定规则 R1′/R2′/R3′ 的输入全部来自
20 Hz follow 单一 cell（3 个 run）。把该 cell 置于测量顺序之首，判定所需
数据在第 3 次测量后即告完整——**"当前 NanoTrack-v2 载体在冻结的 20 Hz
follow 条件下是否足以承载本次 M2 测量"**这一预注册判定从第 12 次提前到
第 3 次。这是成组序贯式的顺序重排，不是中途偷看：规则、阈值、统计量、
敏感性档位零修改。资格试跑（§9）与判定点 A 的关系（修订 4）：前者是
30 s 的**启动准入门**，后者是三个完整正式 run 上的**预注册载体判定**；
两者叙述分开、数据不复用（试跑 run 不进入判定点 A 的输入）。

**A. 执行顺序钉死（改 §10）**：

```
侦察 → rs2-r20-calib → 资格试跑（20 Hz follow，30 s）
  → rs2-r20-follow-r1..r3 ──► 判定点 A（离线，非 Unity 会话）
  → rs2-r20-nadir-r1..r3
  → rs2-r5-calib → rs2-r5-follow-r1..r3 → rs2-r5-nadir-r1..r3
```

**B. 唯一预注册分支（修订 1：数据产生前冻结，无判定点裁量）**：

- `trigger_branch = "stop"`（**用户 2026-07-25 选定**）——写入本提案、
  批次 manifest 与编排配置三处；**资格试跑一旦开始即不可修改**；判定点 A
  没有任何人工选择步骤，触发即自动执行 T-停止；
- **T-停止后果（修订 5）**：跳过剩余 9 次测量**与尚未执行的 5 Hz 标定**，
  campaign 标 `TERMINATED_AT_DECISION_A`，本批明确标记
  **`M2_NOT_CLOSABLE`**——正式 5/20 Hz 对比义务由新载体/新批次承接；已
  采信 run 与判定工件全部保留归档；随即起草 `P1-DETECT-001`，M3 保持挂起。

**C. 判定点 A 语义（修订 2：布尔与异常语义闭合）**：

- **时点**：20 Hz follow cell 的 3 个 run 全部按既有 per-run 采信规则
  （S1′–S3、溯源链）完成采信之后、第 4 次测量会话开始之前；纯离线步骤，
  不新增 Unity 会话；
- **判定式**：`triggered := R1′ OR R2′ OR R3′`，三个规则的输入值与
  各自结果**逐一记录**；
- **齐全性前提**：仅当三个 admissible run 齐全时才可判定；若该 cell 在
  既有补跑上限内仍凑不足三次，状态 = **`BLOCKED_INVALID_CELL`**——既不是
  触发、不是未触发、也不是 `TERMINATED_AT_DECISION_A`，按环境/实现阻塞
  返回 Codex 归因；
- 判定为**最终**，不得因后续任何数据覆盖或翻案；未触发 → 按顺序继续，
  "未触发"判定同样入档。

**D. 不可变判定工件与执行门（修订 3）**：

- Python 编排器原子生成版本化 `decision_a.json`
  （schema `p1-rate2-decision-a/v1`），至少绑定：三个已采信 run ID 及其
  manifest 与 release-provenance SHA-256、规则版本、逐规则输入/输出、
  阈值敏感性表、`trigger_branch`、最终动作、生成时间；写出后不可变；
- **执行门**：第 4 次测量会话与 5 Hz 标定必须在 `decision_a.json` 存在
  且通过校验（哈希绑定完整、`triggered=false`）后方可启动；编排器对此
  fail-closed。

**E. 时间混杂披露（修订 6）**：固定顺序使全部 20 Hz follow run 先于 5 Hz
run 执行。既有 S1′–S3 门保留；`decision_a.json` 与批次汇总工件记录**真实
执行顺序与各会话时间**；正式 5/20 Hz 对比的解释必须披露该固定顺序与系统
负载漂移风险，**不得把未受控的时间效应归因于帧率**。

**F. 不变式声明**：per-run 采信检查、资格试跑门、批次身份、混批防护、
真值边界全部不变；5 Hz 数据从来不参与载体判定（§8 原文即如此）；本修订
无 C# 变更、无协议变更，仅编排器排程、判定工件生成与执行门（Python 小改）。

#### Codex review — 2026-07-25: REVISION_REQUESTED

Decision: **REVISION_REQUESTED**

Rationale:

把完整的 20 Hz follow cell 放在最前面是合理的资源调度修订。判定统计量仍取
冻结的三次完整 run，规则、阈值和样本量不变，因此这不是在 cell 内逐次偷看；
把 5 Hz 标定推迟到判定点之后也不会污染该 cell。该方向可以保留。

当前 A1 仍有一个阻断性的预注册缺陷：它允许在判定点 A 已经看到触发结果后，
再由用户选择 `T-停止` 或 `T-继续`。分支只有两个并不能消除数据依赖裁量；
停止规则必须在资格试跑和任何正式测量结果产生前冻结。若目标是节省无效会话，
Codex 建议预先固定 **T-停止**；代价是触发时本批只能标记
`TERMINATED_AT_DECISION_A`，不能完成或关闭正式 M2 的 5/20 Hz 对比。若必须由
本批完成该对比，则应预先固定 **T-继续**，但 Decision A 只会提前启动
`P1-DETECT-001`，不会节省后续测量。

Required revisions:

1. **在数据产生前冻结唯一分支。** 删除“由用户在判定点二选一”，在提案、
   批次 manifest 和编排配置中预先记录 `trigger_branch = stop|continue`。
   资格试跑或正式测量一旦开始，该字段不可修改；本轮建议由用户现在选择，
   Fable 据此只保留一个触发路径。
2. **闭合 Decision A 的布尔与异常语义。** 明写
   `triggered := R1′ OR R2′ OR R3′`，分别记录三个规则值与结果。只有三个
   admissible run 齐全时才能判定；若某 cell 在既有补跑上限内仍不足三次，
   状态应为 `BLOCKED_INVALID_CELL`，不得把它解释成触发、未触发或
   `TERMINATED_AT_DECISION_A`。
3. **定义不可变判定工件和执行门。** Python 编排器原子生成版本化
   `decision_a.json`，至少绑定三个已采信 run ID、各自 manifest 与 release
   provenance 哈希、规则版本、逐规则输入/输出、敏感性表、
   `trigger_branch`、最终动作和生成时间。第 4 次测量及 5 Hz 标定必须在该
   工件通过校验后才可启动；已生成的判定不得被后续数据覆盖或重写。
4. **收窄研究表述。** 将“载体是否可用”改为“当前 NanoTrack-v2 载体在冻结
   20 Hz follow 条件下是否足以承载本次 M2 测量”。资格试跑是 30 s 的启动
   准入门，Decision A 是三个完整正式 run 的预注册载体判定；两者不得合并
   叙述或重复使用同一数据。
5. **写清会话与里程碑后果。** 若预注册为 T-停止且触发，除剩余九次测量外
   也跳过尚未执行的 5 Hz 标定，并明确本批 `M2_NOT_CLOSABLE`、由新载体/新
   批次承接正式对比；若 T-继续，明确触发后仍禁止据后续数据翻案。
6. **披露固定顺序的时间混杂。** A1 会把所有 20 Hz follow 运行放在 5 Hz
   运行之前。保留既有 S1′–S3 门，并在判定/汇总工件中记录真实执行顺序与
   会话时间；正式 5/20 Hz 解释必须说明该固定顺序及系统负载漂移风险，不得
   把未控制的时间效应归因于帧率。

Accepted design-document changes:

None in this amendment round. 原 round 3 已接受设计及 Batch A/当前 Unity
基础设施验证不受影响；在 A1 修订并获 Codex 接受前，Batch B 不实现新的排程
或 Decision A 逻辑。

#### Codex re-review — 2026-07-25: ACCEPTED_WITH_BINDING_CLARIFICATIONS

Decision: **ACCEPTED_WITH_BINDING_CLARIFICATIONS**

Rationale:

A1 round 2 已闭合前一轮全部六项要求。`trigger_branch="stop"` 在资格试跑和
正式测量数据产生前冻结，Decision A 现在是数据驱动的确定映射：
`R1′ OR R2′ OR R3′` 为真即自动停止，为假才允许继续。三个 admissible run
不足时独立进入 `BLOCKED_INVALID_CELL`，不会被误记为性能触发。资格试跑与
正式三-run 判定的数据和主张边界分离；提前执行 20 Hz follow、延后 5 Hz
标定不会改变冻结统计量。不可变判定工件、后续启动门、M2 未关闭后果和固定
顺序混杂披露均足以授权实现。

Binding clarifications:

1. `decision_a.json` 的规范位置固定为
   `runtime/rate-study/P1-M2-RATE-002-B1/decision_a.json`；实现和测试可对
   runtime 根做依赖注入，但生产路径不得另选或搜索多个候选文件。
2. `final_action` 仅允许
   `CONTINUE_REMAINING_CELLS`、`TERMINATED_AT_DECISION_A` 或
   `BLOCKED_INVALID_CELL`。`triggered=true` 必须对应
   `TERMINATED_AT_DECISION_A`；`triggered=false` 必须对应
   `CONTINUE_REMAINING_CELLS`；不完整 cell 的 `triggered` 必须为 JSON
   `null`，不得伪造布尔结论。
3. 工件使用 create-once 语义：目标已存在时，字节完全相同可作为幂等读取，
   任何不同内容一律 fail-closed，禁止覆盖。第 4 次测量和 5 Hz 标定的
   prepare 路径必须共同调用同一个校验函数。
4. 该 Python 排程/判定工件改变实验决策语义，完成后形成独立稳定候选并停在
   Sonnet 强制复核点；不得仅以单元测试通过直接授权资格试跑或正式测量。

Accepted design-document changes:

接受 A1 round 2 的 20 Hz follow-first 顺序、预注册自动 T-停止、
`decision_a.json` 证据与执行门、`BLOCKED_INVALID_CELL` 路径以及固定顺序
混杂披露。以上四条 binding clarifications 同为正式要求。

## Inputs, outputs, and affected interfaces

- **C# 变更（完整停点先于一切测量）**：实验状态机（HOLD/RELEASED/ABORTED + 指令门控 + evaluator 门控）、`experiment_control.json` 接收器（含拒绝持久化）、release-ack 写出、`SensorFrameWriter` 单调时钟 + schema v2、侦察工具（评测域）；Edit/Play Mode 测试见验收 1；
- **Python 变更**：tracker-ready 发布、release 协调器、release 基线时间语义（`TrackLoop`）、`rs2-*` 批次过滤、S1′/判定/敏感性工具；
- 协议影响：帧元数据 v2；新增 `experiment_control` / `tracker_ready` / `release_ack` 三个版本化文件契约；观测/云台协议不变。

## Compatibility with the current v0.3.1 design

沿 round 1（承接 §3.6 义务、主指标不变、诊断性定位、`DR-P1-M2-001` 门外置）。依赖序：C# 基础设施停点全过 → 侦察/标定 → 资格试跑（=TRACK-002 验收 4）→ 2+12 测量。

## Acceptance criteria

1. **基础设施停点**：状态机/心跳/事务/溯源/时钟/门控的 Edit+Play Mode 测试全绿——含**长 HOLD（≥60 s）结果不变性、心跳健康推进与故意延迟双向用例、RELEASED 后重放 release 的唯一拒绝语义（非 abort）、事务内 `0 ≤ backlog ≤ 1`（检查与转换同一 Update 周期）、完整 tracker/model/init/schema/state 身份终验、旧 runtime 槽位清理、释放前指令抑制断言（两条件平台位姿逐分量一致）、溯源链（manifest↔provenance↔command↔ready↔ack↔命令 ID）任一环失配 fail-closed、时钟 epoch 失配 fail-closed、真实强制点上的 v1/v2 显式行为（§7 清单）、混批次/混载体拒绝、汇总排除全部 pre-release 样本**；随后稳定候选 → Sonnet 复核 → 聚焦 Unity 验证；
2. 侦察资格表全量归档 + `s*` 按最小弧长规则选定 + 冻结产物入库，先于全部测量；
3. 资格试跑按 §9 五项判据通过后才授权 2+12 会话；
4. 2 标定 + 12 测量按批次身份完成；
5. 20 Hz cell 逐 run 过 S1′–S3 或如实 `RATE_UNSUSTAINABLE`/`INVALID_CLOCK`/`INVALID_RELEASE` 处置（补跑上限内），不顶替帧率；
6. 完整指标集逐 run + cell 中位数/极差报告（全部 release 后样本；含 R2′ 逐 run 比值与 R3′ 时序）；
7. §8 规则逐字引用并判定，敏感性表一并给出，结论入证据文档与状态板；
8. 边界审计：追踪进程无真值/scenario config 读取；侦察真值产物不进入追踪输入路径（代码审计可证）；
9. Unity 用例 `UT-P1-M2-RATE-002-001`：用户按 §10 清单执行并反馈。

载体表现好坏不构成实现门失败；实现门只看协议忠实执行与证据完整性。

## Baselines and ablations

沿 round 1：帧率单变量对比（新载体）；CSRT 对照行 = M2a 归档数字；RATE-001 批次 1 永久排除于汇总。

## Failure modes and resource risks

- 资格试跑失败 → 候选拒绝、campaign 不启动、直接进入 `P1-DETECT-001` 讨论（设计意图）；
- 状态机/时钟基础设施回归 → 专属停点拦截；
- release 时积压超界 → 拒绝释放、会话重开（比污染数据便宜）；
- 操作负担：侦察 1 + 标定 2 + 试跑 1 + 测量 12 ≈ 16 次会话；HOLD 期无时间压力，单次失败率显著低于批次 1。

## Suggested implementation scope

两个实现批次：①C# 状态机/握手/ack/时钟/侦察工具 + 测试（独立停点）；②Python 编排/时间基/判定工具。**Out of scope**：`P1-TRACK-002` 插件本体、`P1-DETECT-001`、L1–L4、M3、正式 M2 关闭宣告。

## Open questions

无——侦察常数（0.5 m 网格 / 0.15 边距 / 1.0 框宽分离）与 release 积压边界（`0 ≤ backlog ≤ 1`）已由 Codex 裁决明示接受并冻结；本轮无未决问题。

## Codex review decision

### Round 1 — 2026-07-24: REVISION_REQUESTED

Decision: **REVISION_REQUESTED**

Rationale:

The successor split is correct and most of the scientific design is now
clean: it has a new study identity, monotonic S1 clock, non-circular
detector-escalation rules, immutable anti-mixing boundaries, a frozen
non-edge initialization criterion, and explicit infrastructure stop points.
These changes resolve the lineage, civil-clock, and operator-timing defects
from RATE-001.

The proposed start barrier is not yet closed over the actual runtime. Current
`TrackLoop` measures planned duration from the initialization frame's
`simulation_time_s`; therefore time spent waiting behind the barrier would
shorten the measured run unless the duration origin is explicitly moved to
release. `TrackLoop.initialize()` also immediately publishes the first follow
observation/gimbal command. Freezing only the vehicle lets the gimbal move
during operator confirmation, so follow and nadir would no longer share the
declared initial camera state.

Finally, static sensor publication does not by itself guarantee zero backlog.
The coordinator needs an authoritative tracker-ready handshake before release,
and the release timestamp/epoch must be archived in a machine-readable record.
Without these pieces the successor can reproduce a smaller version of the same
startup contamination it is intended to eliminate.

Required revisions:

1. **Specify one atomic experiment state machine.** Define at least
   `HOLD -> ARMED -> RELEASED` (plus terminal/error). During HOLD, target
   motion, evaluator accumulation, and application of tracker-generated
   gimbal/body commands are gated. ARMED means the exact tracker/model/init
   identity is ready. RELEASED atomically enables target motion, evaluator
   accumulation, controller actuation, and the measurement horizon exactly
   once. Persist rejected duplicate/expired/out-of-order commands.
2. **Add an authoritative tracker-ready handshake.** The tracker or launcher
   must publish an atomic readiness record containing study/run ID, tracker
   identity, init frame/hash, last processed frame, state, and backlog. The
   release coordinator verifies it against the current frame pointer and
   refuses release on stale identity, error/LOST, or backlog above the
   predeclared bound. State whether pre-release sensor frames continue or are
   quiesced; in either case define and test the release-time backlog bound
   rather than claiming it is structurally zero.
3. **Move all measurement time origins to release.** Add an explicit
   `measurement_start_simulation_s`/release baseline to `TrackLoop`; planned
   duration, `actual_duration_s`, first-LOST time, evaluator elapsed time, and
   authoritative metrics cutoff all start at release, not init. Pre-release
   tracker records remain diagnostic and are excluded from outcome and
   latency/backlog aggregates. Test a deliberately long HOLD to prove results
   and duration admission are unchanged.
4. **Freeze initial controller semantics.** The init observation may be
   recorded internally, but follow look-at and other runtime commands must not
   move the gimbal/body before RELEASED. At the release boundary both
   conditions start from the same declared nadir camera/platform state; then
   follow may apply its initialized command. Add a Play Mode assertion for
   identical pre-release platform/camera state.
5. **Make release evidence explicit.** Define a versioned atomic release-ack
   artifact containing command ID, study/run ID, frame ID, and unix/monotonic/
   simulation timestamps. Archive its hash in the manifest. S1′ uses this
   exact `release_monotonic_s`; missing, mismatched, non-finite, wrong-epoch,
   or non-increasing evidence fails closed. Do not rely on timestamps being
   merely "deducible" from later metadata.
6. **Make scouting deterministic.** Define `s*` units and route interpolation,
   the exact normalized border-margin equations, and a deterministic
   tie-breaker (for example, the smallest route arc length satisfying every
   predeclared criterion). Archive all inspected candidates or the generated
   eligibility table so the selected start cannot be cherry-picked.
7. **Synchronize the qualification gate with accepted TRACK-002 semantics.**
   Use one fixed 30 s post-release window and require S1′–S3, no
   LOST/GAP/reinit, `C_track_given_geom >= 0.25`,
   `matched_tracking_observations > 0`, and
   `incorrect_tracking_observations / matched_tracking_observations < 0.5`.
   Remove the undefined event "drift dominance occurs."
8. **Close rule edge cases.** State that R2′ is the median of per-run ratios,
   define division-by-zero behavior, and ensure R1′ still deterministically
   triggers when geometric visibility or matched observations are zero.
   Pre-release observations and evaluator state must be excluded from all
   R1′–R3′ inputs.
9. **Expand compatibility and regression coverage.** Enumerate every v1 frame
   consumer and test its explicit v2 acceptance/rejection behavior. Add tests
   for long HOLD, stale/wrong tracker-ready records, duplicate release,
   pre-release command suppression, release-ack/manifest mismatch, clock epoch
   mismatch, batch/tracker mixing, and summary exclusion of all pre-release
   samples.

Accepted design-document changes:

None in this round. The new work ID, NanoTrack-v2 vehicle, monotonic-clock
direction, and start-barrier concept are sound but remain proposed until the
release transaction and measurement-time semantics are fully specified.

### Round 2 — 2026-07-24: REVISION_REQUESTED

Decision: **REVISION_REQUESTED**

Rationale:

Round 2 substantively addresses all nine first-round requests: the desired
states, release-based outcome window, explicit release evidence, deterministic
scouting, exact qualification inequalities, zero-denominator rules, and a
much stronger regression list are now present. The proposed numeric scouting
values (0.5 m grid, 0.15 border margin, one target-box-width distractor
separation) and the release-time backlog bound of one frame are accepted for
the next revision; they do not need another design choice.

The remaining blockers appear only when the proposed contracts are traced
through the current runtime. First, the document gives the external
coordinator authority to validate readiness but never defines a command or
acknowledgement that actually causes Unity's authoritative state to move from
HOLD to ARMED. Sending `release` after an external-only state change cannot
satisfy Unity's rule that release is valid only in ARMED. The operator
confirmation is also currently placed after readiness validation, so an
unbounded human pause can invalidate the very ready snapshot the coordinator
just checked.

Second, `tracker_ready.json` is described as a one-shot publication after
initialization while HOLD deliberately continues producing frames. Its
`last_processed_frame_id` therefore becomes stale immediately even if the
tracker continues consuming correctly. A live readiness heartbeat and an
explicit race-free final validation are required; otherwise the one-frame
bound is either permanently rejected or checked against non-authoritative
state.

Two evidence contracts also remain underspecified. The current `RunLogger`
creates `manifest.json` before tracking and release, so a later release-ack
hash cannot simply appear in that already-created manifest without a declared
one-time amendment or separate hash-chained provenance artifact. And the
listed v1 consumers do not match the current code: `FrameRepository` in
`controller/track_loop.py` and `_frame_candidates()` in
`tools/run_rate_study.py` enforce the sensor metadata schema;
`controller.protocol.latest_frame_bundle()` reads only the frame-manifest
schema, while `geolocate` consumes an already-parsed mapping. The migration
inventory must follow the real call graph so v2 does not silently break a
consumer that was omitted or test a component that never parsed the schema.

Required revisions:

1. **Close the authoritative ARM transaction.** State explicitly that Unity
   owns the experiment state. Define either a versioned `arm` command plus
   atomic `armed_ack`, followed by release, or collapse ARMED into a single
   coordinator-to-Unity release transaction whose payload contains the
   validated ready evidence. If ARMED remains, specify command/ack schemas,
   identity binding, expiry, idempotency, rejection persistence, and exactly
   which invalid commands transition to ABORTED. In particular, resolve the
   current contradiction between "duplicate release is rejected" and "any
   illegal transition aborts": a replay after a valid RELEASED transition
   must have one unambiguous state/evidence outcome.
2. **Make readiness live and race-bounded.** Republish
   `tracker_ready.json` atomically as a monotonic heartbeat after processed
   frames (or at a fixed declared maximum interval), adding a sequence and
   tracker-process monotonic publication time. Put visual confirmation before
   the final readiness acquisition. Define the coordinator's consistent-read
   algorithm and require the final ready/latest validation immediately before
   ARM/release, with no human pause between them. State how the `<=1` frame
   bound remains true across this check-to-release race and test both a healthy
   moving pointer and deliberate tracker delay.
3. **Define post-release provenance without mutating history implicitly.**
   Choose and specify one auditable design: a two-phase/hash-chained manifest
   finalization, or an immutable initial manifest plus a separate atomic
   release-provenance artifact. The exact `release_ack.json` bytes must be
   copied into the run directory, bound to run/study/command/tracker identity,
   and hashed by the chosen final provenance record. Specify what TrackLoop
   waits for and validates before it switches records to
   `phase="measurement"`.
4. **Freeze the shared pilot invocation.** State explicitly that the single
   qualification run is **20 Hz follow**, define the pre-release NanoTrack
   warm-up rule (fixed count or fixed readiness condition chosen before the
   run), and confirm that the 30.0 s window begins at the acknowledged release
   baseline. No pilot result may change that warm-up rule.
5. **Close remaining deterministic statistics.** Define the scouting grid as
   an exact set over route perimeter (including endpoint/wrap behavior) and
   define "nearest distractor" as the minimum over all active distractor
   projections. For R3′, state whether no-LOST runs contribute the fixed
   release-based planned duration as right-censored values to the three-run
   median; do not leave the median population dependent on which runs happened
   to report LOST.
6. **Replace the schema-migration inventory with the real consumer list.**
   Cover at minimum `FrameRepository`, rate-study frame discovery/scouting,
   `geolocate`'s metadata-field contract, run-record construction/summary, and
   all C# `SensorFrameInfo` consumers affected by the added monotonic field.
   Record separately that `protocol.latest_frame_bundle()` validates
   `tethered-frame-manifest/v1`, not the sensor metadata schema. Test explicit
   v2 behavior and deliberate v1 rejection at the actual enforcing
   boundaries.

Accepted design-document changes:

None in this round. The first-round scientific choices and the numeric
scouting/backlog constants above are accepted inputs to the focused third
revision, but the protocol/time-semantics change does not enter the formal
design until the ARM/readiness/provenance transaction is executable end to
end.

### Round 3 — 2026-07-24: ACCEPTED_WITH_BINDING_CLARIFICATIONS

Decision: **ACCEPTED_WITH_BINDING_CLARIFICATIONS**

Rationale:

Round 3 closes all six blocking defects from round 2. Folding ARMED into the
Unity-owned release transaction is the cleaner option: readiness validation
and state transition now occur in one authoritative Update-cycle transaction,
while replay and ABORT semantics are unambiguous. The live heartbeat, immutable
post-release provenance, frozen 20 Hz follow pilot, deterministic scouting and
right-censoring rules, and code-accurate schema consumer list are sufficient to
authorize implementation.

Binding clarifications:

1. There is no ARMED runtime state. The only states are HOLD, RELEASED, and
   terminal ABORTED, with transitions and replay behavior exactly as specified
   in §1.
2. Both coordinator and Unity enforce `0 <= current_frame_id -
   last_processed_frame_id <= 1`. Unity additionally validates the ready
   schema/state and complete tracker/model/init identity in the same
   transaction; a future-frame record cannot pass.
3. The release command binds the exact ready bytes and hash. The ack binds the
   command, ready, init, tracker identity, accepted frame pair, and backlog.
   Exact command and ack bytes are archived; provenance hashes those files and
   the immutable initial manifest. A narrative copy without byte-verifiable
   binding is insufficient.
4. Heartbeat freshness uses a same-host process monotonic clock
   (`time.monotonic_ns()` or equivalent). Unity's monotonic epoch remains
   separate and is used only for release/capture measurement boundaries.
5. Every prepare clears or rejects stale ready/control/ack slots. The
   infrastructure tests must cover this hygiene together with healthy,
   delayed, replayed, forged-future-frame, and long-HOLD cases.

Required revisions:

None before implementation. The clarifications above are binding acceptance
requirements and have been merged into the proposal text.

Accepted design-document changes:

The formal design now adopts RATE-002's Unity-owned release transaction,
heartbeat, monotonic capture schema, immutable release evidence chain, frozen
20 Hz follow pilot, deterministic scouting rules, and fixed three-run
statistics. No Unity measurement is authorized until the infrastructure
candidate passes its mandatory Sonnet stop and focused Unity validation.

## Round 3 revision map（第二轮修订 → 落点）

| Codex 第二轮修订 | 落点 |
|---|---|
| 1 权威 ARM 事务 | §1（Unity 属主；ARMED 折叠进单一 release 事务；重放后唯一拒绝语义；ABORT 触发恰好两种） |
| 2 心跳与竞态闭合 | §2（v2 心跳 + seq + 发布方单调时间；确认前置；一致读算法；事务内权威终验；健康/延迟双向测试） |
| 3 溯源不改历史 | §5（不可变初始 manifest + `release_provenance.json` 哈希链，ack 逐字节副本）；§4（TrackLoop 等待并验证 ack 后才切 `phase="measurement"`） |
| 4 试跑调用冻结 | §9（20 Hz follow；warm-up = HOLD 期 ≥20 帧且 seq≥20，结果不得反改；30.0 s 自 ack 基线起算） |
| 5 统计确定性 | §3（网格精确集合与回绕排除；最近干扰 = 全体活动干扰的最小值）；§8（R3′ 右删失：无 LOST run 以 planned duration 计入固定三值总体） |
| 6 真实消费方清单 | §7（强制点 = `FrameRepository` 与 `_frame_candidates()`；`geolocate` 字段契约；run 记录/summary；C# `SensorFrameInfo` 消费者；`latest_frame_bundle()` 单独记录为帧清单 schema、不升版） |

## Round 2 revision map（修订 → 落点）

| Codex 修订 | 落点 |
|---|---|
| 1 原子状态机 | §1（HOLD/ARMED/RELEASED/ABORTED、门控清单、拒绝持久化） |
| 2 tracker-ready 握手 | §2（版本化 ready 记录、协调器校验、积压边界 ≤1 帧 + 测试，帧不静默） |
| 3 时间基移到 release | §4（release 基线、hold 期记录仅诊断、长 HOLD 不变性测试） |
| 4 释放前控制冻结 | §6（双侧抑制、共享 nadir 初态、Play Mode 位姿断言） |
| 5 release-ack 证据 | §5（版本化原子 ack + manifest 哈希、S1′ 直接取用、fail-closed 清单） |
| 6 确定性侦察 | §3（弧长/插值/网格、边距与分离精确式、最小弧长 tie-breaker、资格表全量归档、真值边界说明） |
| 7 资格门精确化 | §9（固定 30 s 窗口五判据，废除"漂移主导发生"措辞） |
| 8 规则边界 | §8（R2′ 逐 run 比值中位数、matched=0 → 比值:=1.0、R1′ 零可见/零匹配 → :=0、pre-release 样本排除） |
| 9 兼容与回归 | §7（v1 消费方枚举 + 显式行为）；验收 1（修订 9 全测试清单） |
