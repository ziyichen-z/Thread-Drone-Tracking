# P1-M2-RATE-003 — 继任帧率研究（时钟统一 + 难度阶梯 + 配对相位）

Status: ACCEPTED (acceptance round 3, 2026-07-30)
Amendment DR-B (B1/B2/B3, 2026-07-30): **ACCEPTED**（acceptance
round 4, 2026-07-31；BC-DRB-1..7）；见文末 "Acceptance round 4"。
Acceptance criterion 0c: **AUTHORIZED**（2026-07-31；用户原话
"同意授权"；`docs/authorizations.md`）。
Author/role: 构思角色（ideation，历史名 Claude Fable）
Created: 2026-07-30
Last updated: 2026-07-31

Revision 2 闭合 acceptance round 1 的 1–7；revision 3 闭合 acceptance
round 2 的 1–5。两张对照表见文末"Round 1 revision map"与"Round 2
revision map"。两轮审查原文均保留在文件末尾，不删改。

Revision 3 的主要新增：冻结的正式时域与完成门（§10）、时钟校验的启动期/
运行期分层次序与专用 clock-smoke 身份（§1）、探针 admissibility 前置与
6 m/s 分支收敛（§5）、decision 工件字段的完全确定（§6）、可运动数据源上
的实测环周期工件（§11）。

Acceptance round 3 接受 revision 3，并以文末 BC-R3-1/BC-R3-2 裁定两个
工程数值：`planned_duration_s = 150.0` 保持不变；全批次累计 invalid
attempt **达到 4 次**即暂停。文末 binding clarifications 对正文中此前的
“超过 6 次”提议具有覆盖效力。

## Problem and research value

设计 §11 的 M2 验收要求"云台-only 在新指标下的基线曲线"，其冻结 5/20 Hz
对比义务至今未履行：`P1-M2-RATE-001` 以 `CLOSED_PROTOCOL_INVALID` 关闭，
`P1-M2-RATE-002` 在判定点 A 冻结为 `TERMINATED_AT_DECISION_A /
M2_NOT_CLOSABLE`。设计 §11 指定"由新 ID 继任协议完成冻结 5/20 Hz 对比"，
本提案承接该义务。

本提案不是 RATE-002 的重跑。RATE-002 的协议机制（HOLD/release 事务、
心跳、溯源链、S1′–S3）是有效资产并原样继承；需要正面解决的是四个问题，
其中三个已在仓库中预登记或可由现有工件证实，第四个是本轮核查新发现的
阻断事实。

### 1. 阻断事实：当前载体与当前 RATE 路径在代码中被显式互斥

RATE-003 的测量对象必然是 `P1-DETECT-001` 的三门再锚载体（设计 §11 M2
明写"先资格化最小安全三门载体，再由新 ID 继任"）。但该载体与 RATE-002
的会话机制**当前无法组合**，且这不是推断——是已接受、已通过复核的代码
里一道有意写下的守卫：

```python
# controller/track_loop.py:795-799
if args.rate2_session and args.reanchor_config is not None:
    raise ValueError(
        "detector re-anchor is incompatible with the RATE-002 v2 "
        "process-relative monotonic clock"
    )
```

根因链（均为只读核查所得）：

- `Assets/TetheredTracking/Scripts/SensorFrameWriter.cs:183-187`：当
  `ExperimentController.IsActive` 为真（即 RATE 会话）时写
  `tethered-sensor-frame/v2`，`capture_monotonic_s` 取
  `Time.realtimeSinceStartupAsDouble`（Unity 进程相对 epoch，无 clock id）；
  否则写 v3 + `HostMonotonicSeconds()` + `system-stopwatch/v1`；
- `Assets/TetheredTracking/Scripts/SensorFrameWriter.cs:300-301`：
  `HostMonotonicSeconds()` = `Stopwatch.GetTimestamp() / Stopwatch.Frequency`；
- `controller/sensor_protocol.py:13-43`：`validate_system_monotonic_frame`
  对非 v3 或 `capture_monotonic_clock_id != "system-stopwatch/v1"` 直接抛错；
- `controller/reanchor_runtime.py:130`：`after_frame` **无条件**调用该校验，
  即三门载体逐帧硬要求 v3；
- `controller/track_loop.py:811-815`：`FrameRepository` 的期望 schema 由
  `--rate2-session` 参数化（v2/v3 二选一），line 111 的单调时钟校验只在
  v3 分支执行——所以裸 NanoTrack 载体在 v2 下可跑（RATE-002 正是如此），
  三门载体不行；
- `controller/rate2_protocol.py:21`：`SENSOR_SCHEMA = "tethered-sensor-frame/v2"`。

结论：Clock A4 把 ordinary 路径迁到了带身份的共享主机时钟，**没有迁 RATE
路径**，并用一道守卫把不安全的组合挡住。这是负责任的处置，但它把债留给了
RATE-003：不解决它，本研究的第一次测量会话在启动时即抛错。qual-1 已经为
同一类时钟 epoch 问题烧掉一个资格化 ID；这次它在提案阶段就可见，不应再用
Unity 会话去发现。

### 2. 预登记债务：benign 几何下的区分度

`P1-SCENE-004` 提案（第 161、279、312 行）与设计 §3.4（第 283 行）已把
"benign 几何下 5/20 Hz 可能同近天花板"的风险显式指派给本提案正面处理
（"可用速度、瞬时遮挡等温和难度旋钮"），并明确"不留给 `DR-P1-M2-001`
事后发现"。

### 3. 载体 × 场景混杂

可比数字只有两组，且两个变量同时变化：

| 来源 | 场景/几何 | 载体 | `C_track|geom` | `incorrect/matched` |
|---|---|---|---|---|
| RATE-002 B2 判定点 A（20 Hz follow，N=3 中位数） | 困难 SCENE-002 | 裸 NanoTrack-v2 | 0.2496313750743866 | 0.8475073313782991 |
| qual-2 描述性（20 Hz，协议无效但数值可读） | benign SCENE-004 | DETECT-001 三门 | 0.890283 | 172/2985 = 0.0576 |

任何"三门载体带来数倍提升"的表述当前都不成立——场景与载体同时改变。
论文若要对三门载体做感知轴归因（设计 §7 感知轴第 1→2 段），必须有固定
场景下的对照。Round 1 已裁定该对照（原 O1）属范围扩大，不入本提案；
本提案因此**不主张**任何载体归因，并把该缺口显式登记为 M5 候选。

### 4. 复现件不是样本

RATE-002 的三个 `rs2-r20-follow-*` run（`decision_a.json` 原文）：

| run | `C_track|geom` | `incorrect/matched` | `matched` |
|---|---|---|---|
| 1 | 0.238801 | 0.853659 | 5453 |
| 2 | 0.249914 | 0.847296 | 5455 |
| 3 | 0.249631 | 0.847507 | 5456 |

`matched` 计数三次相差 3（0.05%），三个 run 的首次 LOST 全部右删失于同一
`planned_duration_s`。scenario `random_seed = 0`、路线为确定性折线、`s*`
冻结——N=3 "replicate" 测的是数值与时序抖动，不是任何科学意义上的方差。
在其上报设计 §7 要求的"均值与 95% CI"会构成统计学误导。附带说明：R1′
以 0.2496 对阈值 0.25 触发，绝对余量 0.00037，小于 run 间抖动幅度
（run 1 与 run 2 相差 0.011）；R2′ 在 {0.3, 0.5, 0.7} 三档敏感性下均触发，
是该批次真正稳健的结论——载体保持住了框，但 85% 的匹配是错的。

**研究价值**：本提案把 M2 的率对比从"再跑一次同样的矩阵"改造成一个能
产出可复算处分的设计——难度阶梯上的配对率对比，且零效应是预注册的有效
结论之一。

## Proposed behavior

### 1. 单一时钟契约（前置强制停点，先于一切测量）

Round 1 阻断项正确：原稿只点了 `SensorFrameWriter` 一个写入点，却断言
"统一后内部一致性不变"。核实确认该断言是错的——
`RateStudyExperimentController.cs:150` 把
`Time.realtimeSinceStartupAsDouble` 传入 release 路径并在 line 324 写成
`release_ack.release_monotonic_s`，而 `controller/rate2_protocol.py:602`
直接拿它与帧的 `capture_monotonic_s` 比较来切测量相位。只改帧写入点会把
跨 epoch 比较**重新引入 release 边界**，即 qual-2 同类失效。

本节改为逐字段的单一时钟契约。**RATE-003 会话内一切单调值必须来自
`system-stopwatch/v1`**，定义为：Unity 侧 `Stopwatch.GetTimestamp() /
Stopwatch.Frequency`，Python 侧 `time.monotonic()`；同主机同 boot epoch，
其可比性由 A4 已完成的跨进程夹逼实测（5/5）背书，本提案不重新论证。

| # | 生产者 | 当前取值 | 当前 epoch | 要求 | 主要消费者 / 比较点 |
|---|---|---|---|---|---|
| P1 | 帧 `capture_monotonic_s`（RATE 分支） | `Time.realtimeSinceStartupAsDouble` | Unity 进程 | 改为 `HostMonotonicSeconds()` | `rate2_protocol.frame_phase()`、S1′ |
| P2 | 帧 `capture_monotonic_s`（ordinary 分支） | `HostMonotonicSeconds()` | 共享主机 | 不变 | `track_loop`、`reanchor_runtime` |
| P3 | `release_ack.release_monotonic_s` | `Time.realtimeSinceStartupAsDouble`（`RateStudyExperimentController.cs:150`→`324`） | Unity 进程 | **改为 `HostMonotonicSeconds()`** | `rate2_protocol.py:579,602`、`run_log.py:320`、S1′ cohort |
| P4 | tracker-ready `publisher_monotonic_s` | Python `time.monotonic()` | 共享主机 | 不变，补 clock ID | Unity `RateStudyExperimentController.cs:345-346`（现仅查有限/非负）、协调器新鲜度 |
| P5 | `ReanchorRuntime` 内部 `self.monotonic()` | Python `time.monotonic()` | 共享主机 | 不变，补契约声明 | 与帧 `capture_monotonic_s` 相减做陈旧门（`reanchor_runtime.py:86,201,330`） |

必须被显式校验的跨进程比较点（逐一写测试）：

- C1 `rate2_protocol.py:602`：帧 capture vs `release_monotonic_s`；
- C2 `run_log.py:320`：`monotonic_capture_times[0]` vs `release_monotonic_s`；
- C3 `reanchor_runtime.py`：Python monotonic vs 帧 capture（陈旧门）；
- C4 `RateStudyExperimentController.cs:345-346`：ready `publisher_monotonic_s`
  与 ack/帧的关系——现在只查有限与非负，须升级为带 ID 的同源校验。

**契约条款**：

1. 每个跨进程单调字段要么自带 `*_clock_id`，要么由版本化 schema 明文
   钉死其 clock ID；两者必居其一，不允许"约定俗成"；
2. C1–C4 每个比较点在读取前校验两侧 ID 相等，不等即
   `INVALID_CLOCK_IDENTITY`；
3. 本契约的实现是**独立强制停点**（改时间语义，见 `AGENTS.md`）。

#### 1.1 校验次序：分层的可执行契约（Round 2 要求 2）

Round 2 指出 revision 2 的"所有错钟都在任何副作用之前 fail-closed"对
**运行中出现的坏帧**不可能按字面成立——此前的帧已经产生了副作用。该表述
过宽，现按阶段拆成两层，各自有确切的"之前"：

**(a) 启动期一次性校验（pre-model / pre-run / pre-release 副作用之前）**

| 检查对象 | 必须早于 |
|---|---|
| CLI/会话文件的 study 与 schema 版本、声明 clock ID | 构造模型、创建 run ID、创建 `RunLogger`、写任何 run 目录 |
| init 帧的 schema 与 `capture_monotonic_clock_id` | 同上（沿 A4 已实现并经 round 6 复核的 `run_tracker` 前飞检查次序） |
| ready 心跳的 `publisher_clock_id` | 发布 ready（Python 侧）、接受 release 命令（Unity 侧） |
| release 命令与 ack 的 `release_clock_id` | Unity 的 RELEASED 原子转换、写 ack、任何目标运动/evaluator 累计/指令施加 |

任一失败 → 进程以非零码退出或 Unity 拒绝并保持 HOLD；**不创建 run 目录、
不发布 ready、不发生 release**。

**(b) 运行期逐帧校验（该帧自身副作用之前）**

对 release 之后的每一帧，clock ID 与单调性校验必须早于该帧的：
(i) 观测发布、(ii) 云台/机身指令发布、(iii) re-anchor 门/锚状态更新、
(iv) 进入 evaluator 聚合与 run 记录。失败 → 该帧不产生上述任何一项，
且 run **以 `INVALID_CLOCK` 终止并 fail-closed 归档**，不得跳过坏帧继续。
先前已合法处理的帧保持其既有副作用，这正是 (a)/(b) 必须分层的原因。

**C4 的确切谓词**（Round 2 点名）。Unity 在 release 事务的同一 Update 内：

- `ready.publisher_clock_id == "system-stopwatch/v1"`，否则拒绝，保持 HOLD；
- 取 `now = SensorFrameWriter.HostMonotonicSeconds()`，在**同一 Update
  周期内**采样（RATE-002 §1 已要求校验与转换同周期，故无竞态窗口）；
- 新鲜度与未来性合一：`0 ≤ now − ready.publisher_monotonic_s ≤ 2 ×
  heartbeat_interval_s`，`heartbeat_interval_s = 1.0`（RATE-002 §2 声明
  上限），即窗口 `[0, 2.0] s`。下界 0 即拒绝"来自未来"的 ready——同主机
  同时钟，不留任何 slack；
- 该谓词与既有的 schema/身份/`0 ≤ backlog ≤ 1` 终验并列，全部通过才转换。

**P5 的身份绑定**（Round 2 点名）。`ReanchorRuntime` 的 `self.monotonic`
是**进程内时钟依赖**，不是输出字段，因此不能靠"字段带 ID"绑定。改由三件
事共同绑定：(i) 构造时断言注入的 `monotonic` callable 即声明为
`system-stopwatch/v1` 的系统单调源，非默认注入必须显式声明；(ii) 它每次
与帧 `capture_monotonic_s` 相减前，该帧已由
`validate_system_monotonic_frame` 校验过 `capture_monotonic_clock_id`
（现有实现已满足）；(iii) 运行时把所假定的 clock ID 写入 run manifest，
使溯源可审计。

#### 1.2 专用非测量 clock-smoke 身份（Round 2 要求 2）

Round 2 正确指出 revision 2 的验收 1 自相矛盾：它既要求"用**真实**
RATE-003 会话证明载体逐帧通过校验"，又禁止在该验收通过前启动任何
RATE-003 会话。解法是给验证循环一个不消耗研究身份的专用身份：

- 身份 `P1-M2-RATE-003-CLOCKSMOKE`，会话 ID `rs3-clock-smoke`；
- 与 scouting / calibration / probe / formal 四类 ID 空间**互斥**，编排器
  对其互串 fail-closed；
- 写入隔离的 runtime 槽位，工件归档在非测量路径下；
- **不产出任何 cell 的 `C_track|geom`**，不得被任何处分、判定或论文数字
  引用；
- 无 attempt 上限（不消耗测量身份），可按复核需要反复执行。

据此，本提案所有"不得启动"的措辞统一收窄为**不得启动任何研究数据会话
（scouting / calibration / probe / formal）**；clock-smoke 明确允许，
它正是验收 1 的验证载体。

方案 Q（改用 A5 资格化 release 链）经 Round 1 裁定不采纳，理由记录在案：
它会丢掉 RATE-001 之后建立的启动污染防线（HOLD 冻结目标 + 事务内
`0 ≤ backlog ≤ 1`）。本提案不再保留该备选。

### 2. RATE-003 使用新版本协议，不原地改写 RATE-002 语义

Round 1 要求 2 的落实。**禁止**把 `rate2_protocol.py:21` 的单个
`SENSOR_SCHEMA` 常量从 v2 改成 v3——那会让所有历史 reader 一起漂移。

- **归档读路径（冻结）**：RATE-001/RATE-002 工件继续以
  `tethered-sensor-frame/v2` 与 `p1-rate2-*` 全套 schema 解析，语义一字
  不改，只读；
- **活跃写/读路径（新增）**：RATE-003 使用
  - 传感器帧：复用已存在的 `tethered-sensor-frame/v3`（不新增帧 schema）；
  - 会话：`p1-rate3-session/v1`；
  - 心跳：`p1-rate3-tracker-ready/v1`（含 `publisher_clock_id`）；
  - release 命令/回执/溯源：`p1-rate3-release-{command,ack,provenance}/v1`
    （ack 含 `release_clock_id`）；
  - 判定：`p1-rate3-decision/v1`；
- **路由规则**：版本选择由**会话文件声明的 study/schema 版本**决定，不由
  全局常量决定。需要显式改造并回归的调用点至少包括
  `controller/rate2_protocol.py:21`、`controller/track_loop.py:27,813`、
  `tools/run_rate2_study.py:16,346`；
- **回归要求**：(a) 用真实归档的 RATE-002 工件证明 v2 复算结果与历史值
  逐字节/逐值一致；(b) 用 RATE-003 会话证明走 v3 路径；(c) 交叉喂入
  （v2 工件进 v3 reader、v3 工件进 v2 reader）必须 fail-closed，不得静默
  降级或升级。

模块组织（新建 `rate3_protocol` 还是在现模块内做版本路由）属实现选择，
只要满足上述契约与回归即可，本提案不指定。

### 3. 难度旋钮：目标速度，且只用目标速度

选择 `target.speed_mps` 的理由：

- 它是冻结 scenario schema 里**已有的标量**，零新机制、零新依赖、不动
  场景几何，走既有配置字节 SHA-256 冻结链；
- 它是**唯一同时经两条机制作用于帧率**的旋钮：(a) 追踪器帧间像素位移，
  (b) 云台指令下发节拍——指令节拍等于帧率，5 Hz 时指向更新少 4 倍。
  两条机制同向，正是 M2"反射层闭环"的核心叙事；
- 它近似正交于 `C_geom`：离轴角上限 35.82° 远低于 45° 限位，提速不改变
  几何天花板，只改变"跟不跟得上"。这正是设计 §6 要求的 `C_track` 与
  `C_geom` 分离。

**明确排除瞬时遮挡**：遮挡会触发丢失升级阶梯（设计 §5 的 L1/L2a），属
M4 范围，会把帧率效应与重捕获策略效应混在一起，破坏本提案的归因。

#### 预注册的位移模型（可证伪）

几何取自已实现并经证据确认的
`docs/evidence/P1-SCENE-004-geometry.json`（权威值，取代 revision 1 中我
按顶点自算的区间——顶点采样漏掉了腿中段的最近点）：

- 周长 `62.14213562373095 m`；**标称**环周期 `31.071067811865476 s`
  （= 周长 / 2.0 m/s；实际行驶周期见 §8 限制，短于标称值）；
- 斜距 `26.058397207859084 .. 30.586599435742414 m`；
  离轴 `17.878695710658132° .. 35.82459571162962°`；
- `f = (480/2)/tan(30°) = 415.6922 px`；切向像素位移 = `f/R` 每米，
  即 `13.5907 px/m`（远端）到 `15.9523 px/m`（近端）；
- 参考框取 qual-1/qual-2 用户确认的 `(353, 82, 72, 43)` px，min-side 43 px。

| 速度 | 标称环周期 | 20 Hz 帧间位移 | 5 Hz 帧间位移 |
|---|---|---|---|
| 2.0 m/s（D1，现行） | 31.07 s | 1.36–1.60 px（3.2–3.7% min-side） | 5.44–6.38 px（12.6–14.8%） |
| 4.0 m/s | 15.54 s | 2.72–3.19 px（6.3–7.4%） | 10.87–12.76 px（25.3–29.7%） |
| 6.0 m/s（下调档） | 10.36 s | 4.08–4.79 px（9.5–11.1%） | 16.31–19.14 px（37.9–44.5%） |
| 8.0 m/s（D2 候选） | 7.77 s | 5.44–6.38 px（12.6–14.8%） | 21.75–25.52 px（50.6–59.4%） |

**选点与内部标定点**：`D1 = 2.0 m/s`，`D2 候选 = 8.0 m/s`。选 8.0 的依据是
一个**精确**（非近似）的对称性：`8.0/20 = 2.0/5 = 0.4 m/帧`，因此
**D2@20 Hz 与 D1@5 Hz 的每帧位移完全相同**（5.44–6.38 px）。这给阶梯一个
自带的标定点，并产生一条不额外消耗任何会话的模型检验：

- **H2（描述性，不参与处分）**：若帧间位移是主导因果变量，则
  `C_track|geom(D2, 20 Hz) ≈ C_track|geom(D1, 5 Hz)`。背离的判据由 §6 的
  `H2_DIVERGENCE_FLAG` 精确定义为 `|C_20(D2) − C_5(D1)| > 2θ = 0.10`；
  背离即说明除位移外还有速度相关机制在起作用（§8 列出的偏航滞后是首要
  嫌疑）。该检验只写入报告与判定工件的诊断栏，**不改变任何
  `final_action`**。两个 cell 的 `planned_duration_s` 相同（§10），故可比。

### 4. 配对释放相位与冻结执行顺序

沿用 RATE-002 §3 的确定性侦察机制，预注册**三个**弧长相位
{s*₁, s*₂, s*₃}：在 RATE-002 §3 的资格判据（边距 ≥0.15、最近干扰
IoU = 0 且中心距 ≥1.0 倍目标框宽）下合格的候选中，在 `{0, P/3, 2P/3}`
三个理想相位各自沿弧长**向前**搜索的第一个合格候选，全程无操作者裁量；
任一相位无合格候选则 `INVALID_SCOUTING` fail-closed。

**用词更正（Round 1 要求 4）**：三个相位是**确定性 matched design
points**，不是随机种子，也不构成"成对随机种子"的实现。设计 §7 的成对
原则在此以固定设计点的形式体现，统计解释相应受限：不做总体推断，不报
95% CI，不称统计等效。

主分析量为逐相位配对差
`Δ_i = C_track|geom(20 Hz, s*_i) − C_track|geom(5 Hz, s*_i)`，i = 1,2,3。

**数据产生前冻结的 12 次正式 run 顺序**（槽位编号即执行顺序）：

| 槽 | run ID | 槽 | run ID |
|---|---|---|---|
| 1 | `rs3-d1-p1-r20` | 7 | `rs3-d2-p1-r20` |
| 2 | `rs3-d1-p1-r5` | 8 | `rs3-d2-p1-r5` |
| 3 | `rs3-d1-p2-r5` | 9 | `rs3-d2-p2-r5` |
| 4 | `rs3-d1-p2-r20` | 10 | `rs3-d2-p2-r20` |
| 5 | `rs3-d1-p3-r20` | 11 | `rs3-d2-p3-r20` |
| 6 | `rs3-d1-p3-r5` | 12 | `rs3-d2-p3-r5` |

设计意图：同一相位的两个帧率**紧邻执行**，使配对差这一被估量受系统漂移
的污染最小；相位 2 内部把两个帧率的先后次序翻转，平衡 run 内顺序效应。
难度整体上 D1 先于 D2，该时间混杂**不可消除**，按下述方式处置。

**补跑与防挑选规则**：

- 失败 run 在**原槽位原地重跑**，`attempt` 递增；槽位顺序永不改变；
- **attempt 上限的统一口径（Round 2 要求 3）**：每个槽位（含 §5 探针槽位）
  `max_attempts = 3` **总数**，即 1 次初跑 + 最多 2 次补跑（此即 RATE-002
  "补跑上限 2 次"的等价表述，本提案统一按总数计以消除歧义）。超限即该
  难度 `BLOCKED_INCOMPLETE_CELL`，探针超限即 `BLOCKED_PROBE`；
- **资源边界的显式披露**：已授权的"约 16 次会话"是**成功路径**的名义值。
  补跑是协议内的异常处理，不是计划会话。最坏情况为 13 个槽位 × 3 =
  39 次，这一上界在此显式登记，不隐藏在授权之下。建议的护栏（交接受角色
  Round 3 裁决见 BC-R3-2）：**全批次累计 invalid attempt 达到 4 次即暂停
  并回到接受角色归因及用户重新授权**，而不是静默跑到 39；
- 不可变 manifest 与 `p1-rate3-decision/v1` 必须逐 run 记录：槽位号、
  计划顺序位、实际 attempt 号、release 墙钟时刻与主机单调时刻；
- **操作者不得在看到任何已完成 run 的结果后选择下一个 rate/phase**——
  顺序由上表决定，编排器对越序启动 fail-closed。

### 5. D2 探针（一次；数据不入任何正式 cell）

探针职责收窄为两件事：**校验位移模型**与**触底筛查**。revision 1 的
"明显低于"这一未定义比较已删除。

- **会话**：`rs3-probe-d2`，`5 Hz / D2 候选 / s*₁`，`planned_duration_s`
  与正式 run 同为 **150.0 s**（数值与完成门见 §10——revision 2 的"与正式
  run 同时长"是两个未定义量互相引用，Round 2 要求 1 已据此退修）；
- **位移测量的确切定义**：`d_k = ||c_k − c_{k−1}||₂`（像素），`c_k` 取
  **评测域投影真值框中心**（与 RATE-002 §3 资格表同源同边界——真值只进
  评测/离线链，不进追踪输入）；样本集合 = 测量跨度内**相邻已发布传感器
  帧对**且两侧真值中心均存在、目标物理可见者；汇总量 = 中位数，另报
  p05/p95（分位数算法见 §6 末，type-7 线性插值）；
- **允许区间**：预测 5 Hz@8.0 m/s 为 21.75–25.52 px，容差 ±25%，即实测
  中位数须落在 **[16.3, 31.9] px**；
- **触底判据**：`C_track|geom(probe) ≥ 0.15`。

**分支：admissibility 先判，然后才判模型与触底（Round 2 要求 3）**

Round 2 正确指出 revision 2 的分支表会把"无相邻合格帧对/统计非有限/主
端点缺失"错误地读成"位移模型被证伪"。因此新增前置判据 A0，且它**优先于
B1–B3**：

| 序 | 分支 | 条件 | 处分 | 去向 |
|---|---|---|---|---|
| 0 | **A0** | 下列任一成立：会话协议无效（时钟契约/release 链/S1′–S3/溯源失败）；主端点 `C_track\|geom` 缺失；合格相邻帧对数 < 1；任一汇总统计非有限 | `PROBE_ATTEMPT_INVALID` | 归档，原槽位重跑（§4 统一口径：总 attempt ≤ 3）；超限 `BLOCKED_PROBE` |
| 1 | B1 | A0 不成立 且 位移中位数在 [16.3, 31.9] px 之外 | `PROBE_MODEL_INVALID` | 位移模型（D2 选点的全部依据）被证伪，停止，返回构思/接受，**不下调、不测量** |
| 2 | B2 | A0 不成立 且 位移合格 且 `C_track\|geom ≥ 0.15` | `PROBE_CONFIRMS_D2` | D2 冻结为 8.0 m/s，进入正式矩阵 |
| 3 | B3 | A0 不成立 且 位移合格 且 `C_track\|geom < 0.15` | `PROBE_TRIGGERS_DOWNSHIFT` | D2 := 6.0 m/s，须完成验收 0b 后方可正式测量 |

四个分支互斥且穷尽：A0 覆盖一切"数据不足以判读"的情形，B1–B3 只在数据
可判读时才被求值。

**6 m/s 分支的收敛（Round 2 要求 3）**。revision 2 一面说 B3 后不再重跑
探针、一面又留了 `BLOCKED_D2_UNSELECTABLE`，二者矛盾。本轮**二选一：不新增
第二次探针**（新增会增加会话并需另取用户授权），并因此**删除
`BLOCKED_D2_UNSELECTABLE`**。

- B3 触发 → 下调只发生一次，D2 := 6.0 m/s → 完成 0b → 直接进入正式矩阵；
- 若 6.0 m/s 在**正式 D2 cell** 中仍触底，由 §6 既有路径收束：难度层
  `FLOOR(D2)` → 研究层 `H1_FALSIFIED_FLOOR_AT_D2`。不再有独立的探针级
  终止码，与 §6 完全对齐。

**下调的完整授权链（Round 1 要求 5）**：B3 触发后，在任何正式测量之前
必须依次完成——(i) 生成 6.0 m/s 的新 scenario 配置并取得其字节 SHA-256；
(ii) 重跑 SCENE-002/004 已接受的路线合法性与包络审计并留证；(iii) 取得
**用户对 6.0 m/s 实档的显式确认**（验收 0b）。三者缺一不得测量。

### 6. 判定：写成总定义函数

Round 1 要求 3 的落实。`0.05` 更名为**预注册实际意义阈值**
`θ = 0.05`（绝对覆盖率），**不是**统计等效界，也不证明 equivalence。

**难度层的 cell 汇总量**（对每个难度 D ∈ {D1, D2}，输入为 3 相位 × 2 帧率
共 6 个 admissible run）：

- `C_20(D) = median_i C_track|geom(20 Hz, s*_i)`；
- `C_5(D)  = median_i C_track|geom(5 Hz,  s*_i)`；
- `Δ_i(D)  = C_track|geom(20 Hz, s*_i) − C_track|geom(5 Hz, s*_i)`；
- **`Δ(D) = median{Δ_1, Δ_2, Δ_3}`**（三个值取中位数，奇数个、无插值、
  唯一确定）。同时报 `C_20 − C_5` 作为次要量，并明示两者一般不相等。

**难度层处分（按序判定，首个命中即终止；对任一 admissible 输入唯一）**：

| 序 | 条件 | 处分 |
|---|---|---|
| 1 | 6 个 run 未在 §4 的 attempt 上限（每槽总数 3）内全部 admissible（含 §10 完成门），或任一汇总量非有限 | `BLOCKED_INCOMPLETE_CELL(D)` |
| 2 | `C_20 < 0.30` 且 `C_5 < 0.30` | `FLOOR(D)`——两档均不可用，率对比不可解释 |
| 3 | `C_20 ≥ 0.80` 且 `C_5 ≥ 0.80` 且 `\|Δ\| ≤ θ` | `CEILING(D)` |
| 4 | `Δ > θ` | `RATE_EFFECT_POSITIVE(D)` |
| 5 | `Δ < −θ` | `RATE_EFFECT_INVERTED(D)` |
| 6 | 其余（`\|Δ\| ≤ θ` 且非上述天花板/触底） | `NO_EFFECT_DETECTED_MIDBAND(D)` |

序 2 先于序 3–6，因此"floor 与 rate effect 同时成立"不再是歧义输入：
触底时率对比不可解释，处分为 `FLOOR`，`Δ` 仅作诊断记录。

**诊断旗标（可并存，不改变处分；全部为独立布尔字段）**：

| 字段 | 确切定义 |
|---|---|
| `CEILING_FLAG` | `C_20(D) ≥ 0.80` 且 `C_5(D) ≥ 0.80` |
| `FLOOR_FLAG` | `C_20(D) < 0.30` 且 `C_5(D) < 0.30` |
| `DISPERSION_FLAG` | `max{Δ_i} − min{Δ_i} > 2θ = 0.10` |
| `SIGN_INCONSISTENT_FLAG` | 三个 `Δ_i` 的符号不全相同（`0` 计为与两侧均不同号） |
| `H2_DIVERGENCE_FLAG` | **`\|C_20(D2) − C_5(D1)\| > 2θ = 0.10`**（研究层字段，非难度层） |

`H2_DIVERGENCE_FLAG` 的确切输入即 §3 内部标定点的两个 cell 汇总量：
`C_20(D2)` 与 `C_5(D1)`——这两个 cell 的每帧位移精确相同（0.4 m/帧），
故可比。revision 2 的"显著背离"是未定义措辞，现以上式取代。仅当两个 cell
均完整时可计算；否则该字段为 `null` 并附 `h2_unavailable_reason`。它
**永不改变** `final_action`。

**研究层 `final_action`（唯一）**：

| 序 | 条件 | `final_action` |
|---|---|---|
| 1 | D1 或 D2 为 `BLOCKED_INCOMPLETE_CELL` | `BLOCKED_INCOMPLETE` → 接受角色归因 |
| 2 | D2 = `RATE_EFFECT_POSITIVE` | `M2_RATE_CONTRAST_ESTABLISHED` |
| 3 | D2 = `RATE_EFFECT_INVERTED` | `INVERTED_EFFECT_REPORTED` → 如实报告并交 `DR-P1-M2-001` |
| 4 | D2 = `CEILING` | `H1_FALSIFIED_CEILING_AT_D2` → 返回设计；**不得在本提案内继续加难度** |
| 5 | D2 = `FLOOR` | `H1_FALSIFIED_FLOOR_AT_D2` → 返回设计 |
| 6 | D2 = `NO_EFFECT_DETECTED_MIDBAND` | `NO_EFFECT_DETECTED_AT_D2` → 如实报告，返回设计/DR |

**D1 的处置（Round 2 要求 4：改为独立字段，不动 enum）**。revision 2 的
"追加后缀"会改变 `final_action` 的 schema 枚举，本轮取消该做法：

- `final_action` **恒为上表六值之一**，枚举封闭，不带任何后缀；
- 新增独立布尔字段 `ladder_premise_violated := disposition(D1) != CEILING`；
- 新增独立布尔字段 `dr_referral_required`，在
  `ladder_premise_violated` 为真、或 `final_action ∈
  {INVERTED_EFFECT_REPORTED, NO_EFFECT_DETECTED_AT_D2}`、或下述异质性
  限定成立时置真。

D1 仍不改变 `final_action` 的选择——阶梯低端的意外结果是需要解释的科学
信息，不是 D2 结论的否决权。

**异质性限定（Round 2 要求 4）**。若 `final_action ∈
{M2_RATE_CONTRAST_ESTABLISHED, INVERTED_EFFECT_REPORTED}` 且
（`DISPERSION_FLAG` 或 `SIGN_INCONSISTENT_FLAG` 为真），则：

- 工件必须置 `heterogeneity_qualified = true`，并写入非空
  `qualifier_text`，内容至少列出三个 `Δ_i` 原值与其极差；
- `dr_referral_required := true`；
- 报告与论文**不得**出现不带异质性说明的笼统 "contrast established"；
  规范表述为"在三个注册设计点上中位配对差超过 θ，但各点间不一致
  （附 `Δ_i` 原值）"。

**零效应的表述限定**：处分 3/6 及 `CEILING` 的结论只能写成"**在三个注册
设计点上，未检出超过预注册实际意义阈值 θ = 0.05 的效应**"，不得写成
总体等效、不得声称"帧率无影响"。敏感性描述档位 `{0.03, 0.05, 0.10}`
与主判定一并给出，仅供读者判读，不产生第二套处分。

**分位数算法（Round 2 要求 4）**：全提案所有 p05/p95（含 §5 探针位移、
§11 环周期、次端点分布）一律使用 **type-7 线性插值**
（`h = (n−1)p + 1`，即 `numpy.percentile(..., method="linear")` 的默认
行为）。实现须有一条直接测试断言其与该参考实现逐值一致，保证跨实现复算
一致。中位数即 `p50`，同法计算。

全部输入值、逐规则结果、旗标与 `final_action` 写入不可变
`p1-rate3-decision/v1` 工件，绑定 12 个 run 的 manifest 与
release-provenance SHA-256、规则版本与生成时刻。

### 7. 矩阵与会话预算

- **主矩阵**：{D1, D2} × {5, 20} Hz × {s*₁, s*₂, s*₃}，**follow 条件**
  = 12 次测量会话（顺序见 §4）；
- **nadir 不进主矩阵**。M2 验收要的"云台-only 基线曲线"中承载控制回路的
  是 follow；nadir 下云台不动，提速会让 `C_geom` 快速塌陷，测到的是
  "目标飞出画面"而非帧率效应。nadir 全矩阵登记为 M5 候选；
- **每次正式 run 与探针的 `planned_duration_s` 均为 150.0 s**（§10 冻结）；
- 前置：§1 时钟停点 → 独立复核 → `rs3-clock-smoke` 聚焦 Unity（§1.2，
  非测量身份，不计入下述 16 次）→ 侦察 1 次（相位资格表 + 三个 `s*`
  冻结）→ 每档难度标定 1 次 = 2 次 → D2 探针 1 次；
- **合计约 16 次研究数据会话**（成功路径名义值），与 RATE-002 的计划
  规模相当；补跑与 clock-smoke 是协议内的异常/验证路径，其边界与护栏
  见 §4。

批次身份 `P1-M2-RATE-003-B1`，run ID 见 §4 表，标定 `rs3-d{1|2}-calib`，
探针 `rs3-probe-d2`。

### 8. D2 的物理主张收窄与已知运动学限制

Round 1 要求 6 的落实。**D2 只能表述为 synthetic kinematic
speed-stress condition**（合成运动学速度压力条件）。删除 revision 1 的
"城市道路合理车速"表述；`8.0 m/s = 28.8 km/h` 仅为单位换算，**不构成**
任何道路车辆动力学真实性主张。

只读核查 `Assets/TetheredTracking/Scripts/LoopTargetVehicle.cs` 后，
以下限制必须写入论文与证据文档：

1. `Step()`（line 65-81）沿"指向当前航点的直线方向"按恒定速度积分位置，
   **无加减速、无横向力上限、无轮胎/悬架/载荷模型**；
2. 路径航向在每个航点**近似瞬时**改变（四个顶点 45°、两个顶点 90°），
   仅由 0.5 m 航点接受半径（line 72）平滑；
3. 该接受半径使实际行驶路径**短于**标称 62.1421 m 多边形，因此
   `31.0711 s` 是**标称**环周期。实际行驶周期必须**实测并报告**，不得
   由标称值断言；"≥4 完整环"的核对以实测周期为准；
4. 航点切换时 `return`（line 75）会**跳过该次 Update 的位移**；
5. **偏航与路径解耦且速度相关（本轮新查）**：`turnRate = 240 °/s`
   （line 9），朝向经 `RotateTowards` 限速跟随，而位置立即沿新方向移动。
   在两个 90° 顶点，偏航需 `0.375 s` 才转到位，其间车辆行驶
   **D1 为 0.75 m，D2 为 3.00 m**——即高速档下车辆有明显更长的"横向
   蟹行"渲染区段。这是一个**速度相关的外观混杂**，与"位移压力"部分纠缠；
   必须按 §6 的 `H2_DIVERGENCE_FLAG` 与逐 run 诊断记录，并在报告中列为
   已知混杂，不得把全部 D2 效应归因于帧间位移。

本提案**不含任何路线几何改动**。圆角化或引入车辆动力学须另立提案并取得
用户范围授权。

### 9. 原样继承 RATE-002 的已接受机制

状态机与 HOLD 语义、release 原子事务与 `0 ≤ backlog ≤ 1` 事务内检查、
tracker-ready 心跳与一致读算法、溯源哈希链、释放前控制冻结、S1′–S3 逐
run 采信门、混批次/混载体拒绝、真值只进 `CoverageEvaluator` 的边界——
语义原样继承（承载它们的 schema 按 §2 升版），本提案不重新设计。

### 10. 正式时域与完成门（冻结；Round 2 要求 1）

Round 2 的判断正确：revision 2 从未给出 `planned_duration_s`，"探针与正式
run 同时长"只是两个未定义量互相引用。本节冻结该值。

**冻结值：`planned_duration_s = 150.0 s`，对全部 12 个正式 run、D2 探针、
两个难度、两个帧率、以及 8→6 m/s 分支后的配置，取值完全相同。**

**为什么必须跨 rate 与 difficulty 保持同值**：

1. 主端点 `C_track|geom` 是时间加权比值，漂移随暴露时长累积。同一难度内
   两个帧率若时域不同，配对差 `Δ_i` 就同时含帧率效应与暴露差，被估量不
   再是帧率；
2. §3 的内部标定点 H2 要比较 `C_20(D2)` 与 `C_5(D1)`——跨难度的两个 cell。
   只有时域相同，该比较才可解释；
3. 以**秒**而非"完整环数"冻结时域，可使完成门独立于 §8 已识别的行驶路径
   不确定性（0.5 m 接受半径使实际路径短于标称多边形）。若改用环数，就必须
   先冻结 lap 定义与取整才能定时域，而 lap 只能在目标运动的会话里测得——
   那正是 Round 2 要求 5 指出的循环。本提案因此**不设 lap 门**。

**为什么是 150.0**：

- D1 标称环周期 31.0711 s → 150 s 含 **4.83 环**（角点切割只会缩短实际
  环周期，即实际环数更多，方向安全），全路线几何、六个顶点与远/近斜距段
  均被完整覆盖；D2@8.0 含 19.3 环，D2@6.0 含 14.5 环；
- 样本量：5 Hz 给 750 个测量帧，20 Hz 给 3000 个，对比值型端点充裕；
- **不构成已授权资源的实质扩大**（Round 2 明确要求核对）：RATE-002 的正式
  run 是 272.97056274847716 s，本提案 150.0 s **更短**；12 × 150 s = 30 min
  纯 Play。故沿用 0a 授权，**无需新授权**；
- 与 SCENE-004/DETECT-001 已实测的 ~150 s 量级同级，该时长的 Unity 稳定性
  与操作体验已有实证（qual-2 约 150 s 新鲜采集、scout-4 120 s 无 Console
  报错），不引入未知运行风险。

**完成门的四个时间量及其关系**（全部以 release 为原点，沿 RATE-002 §4）：

| 量 | 定义 | 门 |
|---|---|---|
| simulation duration | 已采信帧累计的仿真时长 | `≥ 150.0` |
| shared-host monotonic wall duration | 末个已采信帧 `capture_monotonic_s` − `release_monotonic_s`（同 `system-stopwatch/v1`） | `≥ 150.0` |
| evaluator cutoff | `metrics.final.json` 绑定同一 release identity 的 elapsed | `≥ 150.0` 且与 simulation duration 之差 `≤ 0.5 s` |
| right-censored LOST | 无 LOST 事件的 run 贡献的删失值 | 恒 `= 150.0`（即 `planned_duration_s`） |

0.5 s 容差的依据：RATE-002 B2 smoke 实测 evaluator cutoff delta 为
0.037748 s，0.5 s 留约 13 倍余量，既能吸收单帧级抖动，又不足以掩盖真实的
边界错位（qual-2 的错位是数十秒量级）。

**采信条件**：run 为 admissible 当且仅当——四个时间量全部满足上表、
S1′–S3 通过、溯源链完整、§1 时钟契约逐帧通过。任一不满足 → 按 §4 原槽位
重跑（总 attempt ≤ 3）。

`planned_duration_s = 150.0` 及其 tolerance 进入
`p1-rate3-session/v1`、run manifest、`p1-rate3-release-provenance/v1` 与
`p1-rate3-decision/v1` 的哈希链，数据产生前冻结，事后不可改。

### 11. 实测环周期工件（Round 2 要求 5）

Round 2 正确指出 revision 2 的"标定会话顺带读取过顶点时刻"不可执行：
RATE 标定处于 HOLD、目标不动；且 0.5 m 接受半径意味着车辆通常并不精确
经过顶点。本节改用可运动的数据源与有方向的起始截面。

- **数据源**：正式 run 与探针**已释放测量段**的评测域真值位置流（目标在
  此段确实运动）。与 §5 位移测量同源同边界——真值只进评测/离线链，不进
  追踪输入。不新增任何 Unity 会话；
- **lap 边界（有方向的起始截面）**：过 `route[0] = (128.0, 116.0)`、法向
  取 `route[0] → route[1]` 方向（即 `+x`）的竖直平面。设 `d(t)` 为目标
  位置到该平面的有符号距离。一次 crossing 计数当且仅当相邻两个真值样本
  满足 `d(t_k) < 0 ≤ d(t_{k+1})`（**仅 − → + 单向**，消除抖动双计），
  且交点处沿平面的横向偏移 `≤ 1.5 m`（容纳角点切割导致的路径内移）；
- **时间基**：crossing 时刻由两个夹逼样本对 `d` 线性插值求得，以
  **release 原点的仿真秒**为主（与 §10 的 simulation duration 同基），
  并同时记录 `system-stopwatch/v1` 单调秒；
- **环周期**：相邻 crossing 时刻之差；报中位数、min、max、n（分位数按
  §6 末的 type-7）；
- **最少完整 lap 数**：D1 在 150 s 窗口内须有 ≥4 次 crossing（即 ≥3 个
  完整 lap 区间）方可报告；D2 远高于此；
- **异常/漏 crossing 处分**：若真值流的缺口跨越了一次预期 crossing，该
  lap 区间**丢弃**并计入 `dropped_lap_intervals`；若丢弃比例 > 20%，该
  run 的环周期结果记为 `LAP_MEASUREMENT_INSUFFICIENT`。这**不会**使 run
  失效——因为环周期是报告项而非门；
- **工件归属**：写入该 run 的不可变分析输出，并按难度汇总进
  `p1-rate3-decision/v1` 的诊断区 `measured_lap_period_s`（跨 run 中位
  数），哈希绑定各 run manifest。

**是否参与门：否，仅报告。** 它不决定 `planned_duration_s`（已由 §10
冻结为 150.0 s），RATE-003 也不设"≥N 环"门。这从结构上排除了 Round 2
担心的"从正式结果事后反改时域"。

唯一附带诊断：若 D1 的实测环周期中位数与标称 `31.0711 s` 偏差 > 5%，置
`LAP_PERIOD_DEVIATION_FLAG` 并披露。预期方向为**更短**（角点切割），
若观察到更长则说明存在未建模的行为，须在报告中解释。

## Inputs, outputs, and affected interfaces

- **C# 变更**：`SensorFrameWriter` RATE 分支改用 `HostMonotonicSeconds()`
  并写 v3；`RateStudyExperimentController.cs:150` 的 ack 时钟源改为同一
  `HostMonotonicSeconds()`，line 345-346 的 ready 校验升级为带 ID 校验；
  侦察工具输出三相位资格表；D1/D2 双 scenario 绑定；
- **Python 变更**：v2 归档路径冻结、v3 活跃路径新增与版本路由
  （`rate2_protocol.py:21`、`track_loop.py:27,813`、
  `run_rate2_study.py:16,346`）；C1–C4 四个比较点的 clock-ID 校验；
  `track_loop.py:795` 互斥守卫在 §1 契约真正成立后解除（不是单纯删断言）；
  难度/相位/槽位编排、配对差分析、`p1-rate3-decision/v1` 生成；
- **配置**：新增 `config/scenario.p1-scene-004-d2.json`，与现行
  `scenario.p1-scene-004.json` 的差异**仅限** `scenario_id` 与
  `target.speed_mps`；走既有字节 SHA-256 冻结链，并重跑路线合法性与包络
  审计留证（几何未变，预期零违规）；
- **协议影响**：RATE 活跃路径的传感器元数据与 release/ready/provenance
  全部升版（时间语义变更，强制停点）。观测协议、云台协议、
  `metrics.json` 指标定义均不变。

## Compatibility with the current v0.3 design

- 主指标定义、模型与阈值、`IdentityProfile`、硬件目标、阶段边界均不变；
  本提案不改变核心研究主张，不扩大 Phase 1 范围；
- **几何非继承条款的落实**：`P1-SCENE-003` 提案第 187–189 行与
  `P1-SCENE-004` 处分表行 7 都要求"RATE-003 采纳任何几何仍需其提案期用户
  确认"。D2 改变 `target.speed_mps`，属测量难度的实质变更，故列为验收
  0a/0b；
- `DR-P1-M2-001` 仍外置于本提案。按 workflow §4.7，它因 RATE-002 的
  `M2_NOT_CLOSABLE`（仍产生进入论文的研究主张）**已经到期**，不因本提案
  而顺延；本提案不得被用作推迟该审查的理由；
- RATE-001/RATE-002 全部归档只读、按原 schema 可复算、run ID 永不复用、
  不并入本批汇总；
- **运行依赖门（Round 1 要求 7）**：`P1-DETECT-001` qual-3 必须先取得用户
  Unity `PASS` 并由接受角色完成归因，RATE-003 的侦察/标定/探针/测量方可
  启动。§1 的时钟停点代码工作可独立排程，但不得越过该运行门；
- 依赖序：§1 停点全过（复核 + 聚焦 Unity）→ qual-3 PASS 与归因 → 侦察 →
  标定 → D2 探针 → 12 次正式测量 → 判定工件 →（`DR-P1-M2-001` 之后）
  M2 关闭议题。

## Acceptance criteria

0. **范围与几何授权（两段，消除 revision 1 的循环）**：
   - **0a（侦察之前）**：用户逐字确认 `D1 = 2.0 m/s`、`D2 候选 =
     8.0 m/s`、§5 的一次性下调**规则**（B3 触发时降至 6.0 m/s）、约 16 次
     主矩阵会话预算，以及 O1 推迟至 M5。授权逐字记入
     `docs/authorizations.md`；账本无条目视为未授权；
   - **0b（仅当 B3 触发，正式测量之前）**：用户确认已实现的 6.0 m/s
     配置及其重新审计后的哈希。
1. **单一时钟契约停点**：P1–P5 五个生产者全部输出 `system-stopwatch/v1`
   并带 ID 或由 schema 钉死（P5 按 §1.1 三重绑定）；C1–C4 四个比较点在
   读取前校验 ID 相等；**启动期检查按 §1.1(a) 在 pre-model/pre-run/
   pre-release 副作用之前，运行期检查按 §1.1(b) 在该帧自身副作用之前且
   失败即以 `INVALID_CLOCK` 终止 run**；C4 按 §1.1 的确切谓词实现
   （clock ID + `[0, 2.0] s` 新鲜度窗口 + 同 Update 采样）；三门载体在
   **真实** RATE-003 会话中逐帧通过 `validate_system_monotonic_frame`；
   `track_loop.py:795` 的互斥前提被真正解除；§2 的 v2/v3 双向交叉喂入
   回归 fail-closed，且真实 RATE-002 归档复算值与历史一致；Edit + Play
   Mode 与 Python 全绿 → 稳定候选 → 独立复核 → 聚焦 Unity 验证。
   该聚焦验证使用 §1.2 的 `rs3-clock-smoke` 专用非测量身份。
   **在此之前不得启动任何研究数据会话（scouting / calibration / probe /
   formal）**；clock-smoke 明确允许，它正是本条的验证载体。
2. 侦察一次产出全量相位资格表（含不合格候选，杜绝樱桃挑选），按 §4
   确定性规则选定 {s*₁, s*₂, s*₃} 并先于全部测量冻结入库。
3. D2 探针按 §5 执行；**A0 admissibility 先于 B1–B3 求值**；位移测量的
   来源/样本集/汇总量/区间逐项可复算；四个分支唯一命中；工件可证探针
   数据未进入任何正式 cell、未用于调参、未反改任何阈值；若触发下调，
   0b 链条完整，且不新增第二次探针。
4. 12 次正式测量按 §4 冻结槽位顺序完成；逐 run 通过 §10 的四个时间量
   完成门、S1′–S3 与完整溯源链，否则按既有处置归档并原地补跑
   （**总 attempt ≤ 3**），**不得以帧率解释协议失败**，不得越序或按已见
   结果选择下一个 run。累计 invalid attempt 达到 4 次即暂停并回到接受
   角色归因及用户重新授权（精确定义见 BC-R3-2）。
5. §6 判定函数按字面执行：任一 admissible 输入产出唯一 `final_action`
   （六值封闭枚举，无后缀）；`ladder_premise_violated`、
   `dr_referral_required`、`heterogeneity_qualified` 与 `qualifier_text`
   为独立字段；逐相位 `Δ_i`、`Δ(D)`、`C_20`、`C_5`、全部旗标（含按
   `|C_20(D2) − C_5(D1)| > 0.10` 定义的 `H2_DIVERGENCE_FLAG`）、敏感性
   档位与全部次端点写入不可变 `p1-rate3-decision/v1`；全部分位数用
   type-7 并有直接测试断言。
5b. **时域与环周期**：`planned_duration_s = 150.0` 在数据前冻结并进入
   session/manifest/provenance/decision 哈希链；§11 的实测环周期按有向
   起始截面在已释放测量段上产出，仅作报告、不参与任何门。
6. 边界审计：追踪进程无真值与 scenario 配置读取；侦察与探针的真值产物
   不进入追踪输入路径（代码审计可证）。
7. **混杂与限制如实披露**（缺一即验收不通过）：载体×场景混杂——RATE-002
   数字不得作为配对基线，本提案不主张载体归因；D1 先于 D2 的时间混杂并
   逐 run 记录；三相位为确定性设计点而非随机样本，不报 95% CI、不称统计
   等效；§8 的五项运动学限制（含偏航滞后的速度相关外观混杂）全部列出；
   实际行驶环周期以实测报告，不用标称值断言。
8. Unity 用例 `UT-P1-M2-RATE-003-001`：用户按会话清单执行并反馈。

载体表现好坏不构成实现门失败；实现门只看协议忠实执行与证据完整性。

## Baselines and ablations

- **主对比**：帧率单变量，D1 与 D2 各自内部配对（§4 槽位顺序）；
- **内部标定点 H2**：`C_track|geom(D2, 20 Hz)` 与 `C_track|geom(D1, 5 Hz)`
  的比较，每帧位移精确相同（0.4 m/帧），零额外会话，描述性；
- **不在本提案范围**：SOT-only 感知轴对照（原 O1，+3 会话）经 Round 1
  裁定属范围扩大，**登记为 M5 候选**。后果如实记录：缺此对照，
  0.2496 → 0.890283 的差异无法归因给三门载体，只能表述为"载体与场景
  同时改变"；
- **不在本提案范围**：nadir 全矩阵（+12 会话），M5 候选；
- CSRT 对照行只引用 `P1-TRACK-001` 归档数字，显式标注为不同载体、不同
  场景、非配对。

## Failure modes and resource risks

- **§1/§2 停点失败** → 全部 RATE-003 会话不启动。这正是本提案要在会话
  之前暴露的风险；
- **探针 B1（位移模型被证伪）** → D2 选点的全部依据失效，停止并返回，
  不得改用"试几个速度看看"的方式继续；
- **D2 触底或仍天花板** → §6 研究层处分 4/5 直接给出返回设计的分支，
  禁止就地调参或在本提案内追加难度；
- **偏航滞后混杂（§8 第 5 项）**：D2 的 3.00 m 蟹行区段可能贡献部分效应。
  无法在不改路线的前提下消除，只能记录与披露；若复核认为该混杂足以
  推翻率归因，正确处置是另立圆角/动力学提案，而不是在本提案内改几何；
- **提速改变 `C_geom`**：预期基本不变（离轴 ≤35.82° 远低于 45° 限位）。
  若实测显著下降，说明云台跟随在高速下失效，属次端点诊断信息，须与主
  端点分开报告，不得混入率效应；
- **会话预算**：约 16 次。历次采集报废率高（RATE-001 整批、scout-3、
  qual-1、qual-2 均因协议报废），§1/§2 的提前修复正是为降低报废；
- 零新模型、零新依赖、零传感器硬件变更、零路线几何变更。

## Suggested implementation scope

两个实现批次：

1. **单一时钟契约 + v2/v3 版本路由 + 回归**（独立强制停点，先于一切
   RATE-003 会话）；
2. **D2 配置 + 三相位侦察 + 槽位编排 + 探针 + 判定函数工件**。

**Out of scope**：三门载体本体与其阈值、遮挡与丢失升级阶梯（M4）、机身
运动与词典序分配（M3）、SOT-only 对照（M5）、nadir 全矩阵（M5）、圆角
路线或车辆动力学、随机化路线（M5）、M2 关闭宣告本身（须先过
`DR-P1-M2-001`）。

## Open questions

1. **θ = 0.05 的取值**。目前无先验方差估计：RATE-002 的 run 间抖动约
   0.011 仅是确定性重跑的数值抖动下界，不能估计跨相位变异。本轮把它
   定义为预注册实际意义阈值而非统计界，已消除表述问题；若接受角色仍要
   更严阈值，需要额外的相位间变异数据，那会改变 §5 探针"不入正式对比"
   的定位，须一并裁决。
2. **`Δ` 用配对差中位数**（本稿选择）**还是三个 `Δ_i` 全一致才算效应**
   （更保守的 all-or-none 规则）。前者对单相位异常稳健，后者更严格但会
   在 `DISPERSION_FLAG` 情形下频繁落入无处分。本稿用中位数 + 离散度
   旗标，请接受角色确认是否接受该取舍。
3. **补跑护栏的数值（Round 3 已决）**：本轮把"约 16 次"明确为成功路径
   名义值，并登记最坏 39 次的上界。原提议为累计 invalid attempt > 6；
   acceptance round 3 改为**累计达到 4 次即暂停**，精确定义和理由见
   BC-R3-2。
4. **`planned_duration_s = 150.0`（Round 3 已决）**：150 s 满足 D1 的
   4.83 环与 5 Hz 的约 750 帧，且短于 RATE-002 的 272.97 s，故无资源扩大。
   acceptance round 3 保留该值，不上调至 200–270 s；理由见 BC-R3-1。

## Round 2 revision map（要求 → 落点）

| Round 2 要求 | 落点 |
|---|---|
| 1 冻结正式时域与完成门 | **§10 新增**：`planned_duration_s = 150.0 s`，跨 rate/difficulty/探针/降档分支同值，附科学理由；四个时间量（simulation / 共享主机墙钟 / evaluator cutoff 含 0.5 s 容差 / 右删失值）与采信条件；显式核对不构成资源扩大（RATE-002 为 272.97 s，本提案更短），沿用 0a 授权；不设 lap 门。验收 5b |
| 2 时钟校验次序写成可执行契约 | **§1.1 新增**：(a) 启动期 pre-model/pre-run/pre-release 表、(b) 运行期逐帧"该帧副作用之前"并以 `INVALID_CLOCK` 终止；C4 确切谓词（clock ID + `[0,2.0] s` 窗口 + 同 Update 采样 + 拒未来）；P5 三重身份绑定。**§1.2 新增** `rs3-clock-smoke` 专用非测量身份，并把"不得启动"收窄为"不得启动任何研究数据会话"，解掉验收 1 的自相矛盾 |
| 3 闭合探针与 6 m/s 分支 | **§5 重写**：新增 A0 admissibility 前置（协议无效/主端点缺失/无合格帧对/统计非有限），优先于 B1–B3，不再把数据不足误读为模型证伪；attempt 上限统一为**总数 3**（§4 同步）；选定"不新增第二次探针"，**删除 `BLOCKED_D2_UNSELECTABLE`**，由正式 D2 cell 的 `FLOOR(D2)` → `H1_FALSIFIED_FLOOR_AT_D2` 收束 |
| 4 decision 工件字段完全确定 | **§6 重写**：旗标改为定义表，`H2_DIVERGENCE_FLAG := \|C_20(D2) − C_5(D1)\| > 0.10`（两 cell 每帧位移精确相同故可比，不完整时为 `null`）；`ladder_premise_violated` / `dr_referral_required` / `heterogeneity_qualified` / `qualifier_text` 改为独立字段，`final_action` 保持六值封闭枚举；异质性成立时禁止笼统 "contrast established" 并强制 DR；分位数钉死 type-7 并要求直接测试 |
| 5 定义实测环周期工件 | **§11 新增**：数据源改为**已释放测量段**的评测域真值流（HOLD 标定确实测不到）；有向起始截面（过 `route[0]`、法向 `+x`、单向 −→+、横向容差 1.5 m）取代"过顶点"；插值求 crossing 时刻，release 原点仿真秒为主；D1 需 ≥4 次 crossing；漏 crossing 丢弃并在 >20% 时记 `LAP_MEASUREMENT_INSUFFICIENT`；**仅报告、不参与任何门**，从结构上排除事后反改时域 |

## Round 1 revision map（要求 → 落点）

| Round 1 要求 | 落点 |
|---|---|
| 1 闭合单一时钟契约 | §1 全节重写：P1–P5 生产者表、C1–C4 比较点、四条契约条款；验收 1 |
| 2 新版本协议，不原地改写 v2 | §2 全新一节：归档 v2 冻结 / 活跃 v3 路由、调用点清单、双向交叉喂入回归；验收 1 |
| 3 判定写成总定义函数 | §6 全节重写：cell 汇总量、`Δ` 定义、难度层 6 序处分、研究层 6 序 `final_action`、D1 旗标、θ 更名与结论限定 |
| 4 准确描述配对与执行顺序 | §4：用词更正为确定性 matched design points、12 槽冻结顺序表、原地补跑、防挑选与逐 run 记录；验收 4、7 |
| 5 闭合 D2 探针 | §5 全节重写：位移定义/样本集/汇总量/[16.3, 31.9] px 区间、B1–B4 四分支、下调授权链；验收 0b、3 |
| 6 收窄 D2 物理主张 | §8 新增：synthetic kinematic speed-stress、五项运动学限制（含新查出的偏航滞后速度相关混杂）、标称 vs 实测环周期、不改路线几何 |
| 7 闭合依赖与范围授权 | Compatibility 的运行依赖门（qual-3 PASS 先行）、验收 0a/0b、Baselines 中 O1 移出并登记 M5 |
| Accepted design-document change | §3 采用权威工件值 `62.14213562373095 m / 31.071067811865476 s`（标称），并按 §8 第 3 项要求实测周期 |

## Codex review decision

### Acceptance round 1 — 2026-07-30

Decision: **REVISION_REQUESTED**

Rationale:

继任新 ID、保留 RATE 的 HOLD/release/backlog 事务、把 RATE 帧迁到带身份
的共享主机时钟、只用目标速度制造两级难度、用三个预注册相位替代伪随机
复现件，以及“不作总体推断、不报 95% CI”的方向均可保留。方案 Q 会丢掉
RATE-001 后已经建立的启动污染防线，本轮不采纳；方案 R 是正确方向。

但现稿尚不能按字面实现，也不能产生唯一可复算的研究处分。最直接的阻断
在真实代码中：`SensorFrameWriter` 若按方案 R 改用
`HostMonotonicSeconds()`，`RateStudyExperimentController.PollControl()`
仍把 `Time.realtimeSinceStartupAsDouble` 写进
`release_ack.release_monotonic_s`；而
`controller/rate2_protocol.py:frame_phase()` 会直接比较这两个值。现稿
所谓“统一后内部一致性不变”因此不成立，而是把不同 epoch 的比较重新引入
release 边界。

此外，正文定义了三个 `Δ_i`，判定表却使用未定义的单个 `Δ`；“两档均
≥0.80/<0.30”也未说明逐相位还是聚合判定。D1 非预期结果、D2 中间带和
rate-effect 与 floor 同时成立等输入没有唯一处分。`0.05` 在没有随机样本
与方差模型时只能是预注册的实际意义阈值，不能称为统计等效界或证明
equivalence。

Required revisions:

1. **闭合单一时钟契约。** RATE-003 的 frame capture、tracker-ready
   publisher、Unity release ack、Python release/frame-phase 比较和
   provenance 必须逐字段写清同一 `system-stopwatch/v1` 身份；Unity ack
   必须改用与 `SensorFrameWriter.HostMonotonicSeconds()` 相同的时钟源，
   不能继续使用 `Time.realtimeSinceStartupAsDouble`。所有跨进程单调值
   都要携带或由版本化 schema 明确绑定 clock ID，错 ID/缺 ID/混 epoch
   在副作用前 fail-closed。
2. **RATE-003 使用新版本协议，不原地改写 RATE-002 语义。** session、
   ready、release ack/provenance 与 active study identity 要有 RATE-003
   版本；现有 `rate2_protocol.py` 的单个 `SENSOR_SCHEMA` 常量不能简单从
   v2 改为 v3 后让历史 reader 漂移。列出 active-v3 与 archived-v2 的
   明确路由、调用点和回归；RATE-001/002 工件保持只读且仍能按原 schema
   复算。时钟批次继续作为独立强制停点，复核与聚焦 Unity 通过前不得启动
   RATE-003 侦察、标定、探针或测量。
3. **把判定写成总定义函数。** 明确定义每个难度的 cell 汇总量、单个
   `Δ` 如何由 `{Δ_1,Δ_2,Δ_3}` 得到，以及 ceiling/floor 是互斥处分还是
   可并存诊断旗标。覆盖 D1 的所有非预期输入、D2 的全部中间带、正/负
   rate effect 与 floor/ceiling 同时成立、cell 不完整和非有限值；任一
   admissible 输入必须得到唯一 `final_action`。把 `0.05` 改称
   “预注册实际意义阈值”，零效应结论限定为“在三个注册设计点未检出超过
   阈值的效应”，不得写成总体等效。
4. **准确描述配对与执行顺序。** 三个相位是确定性 matched design
   points，不是随机种子，也不“直接落实成对随机种子”。在数据前冻结
   12 次正式 run 的确切顺序、合法补跑插入位置和配对规则；固定顺序造成
   的时间混杂不仅要披露，还必须由不可变 manifest/decision 工件逐 run
   记录，禁止操作者按已见结果选择下一个 rate/phase。
5. **闭合 D2 探针。** 定义帧间位移的来源、样本集合、汇总量、允许区间/
   容差和每个失败分支；删除未定义的“明显低于”。若 8.0 m/s 探针触发
   一次性下调，6.0 m/s 的新配置哈希、路线/包络审计与用户确认必须在
   正式测量前完成；不得把 acceptance criterion 0 写成既要求侦察前确认
   下调值、又只能在侦察后的探针中产生下调值。已实现几何工件给出的权威
   周长/周期为 `62.1421 m / 31.0711 s`；SCENE-004 提案期的“~36 s”只是
   旧估计，不再作为门值。
6. **收窄 D2 物理主张。** 当前六段倒角折线路径与
   `LoopTargetVehicle.Step()` 仍是分段运动学载体，不能凭
   `8.0 m/s = 28.8 km/h` 宣称道路车辆动力学真实。修订要么保持几何不变
   并把 D2 明标为 synthetic kinematic speed-stress condition、把拐点
   瞬时方向变化列为限制；要么另立圆角/动力学提案并取得用户范围授权。
   本轮不授权在 RATE-003 内顺手改路线几何。
7. **闭合依赖和范围授权。** `P1-DETECT-001` qual-3 必须先取得用户 Unity
   PASS 并由接受角色完成归因，才可启动 RATE-003 测量；时钟停点代码工作
   可独立排程，但不能越过该运行门。主矩阵约 16 次 Unity 会话以及 D1
   2.0 / D2 8.0 m/s（或经规则下调后的 6.0）都需要用户逐字确认。O1 的
   +3 次 SOT-only 感知轴对照属于范围扩大，本轮不纳入主提案；若用户希望
   现在做，须作为显式 amendment 授权，否则登记为 M5 候选。

Re-review entry conditions:

- 构思角色提交 revision 2，逐条闭合上述 1–7；
- 用户明确选择是否授权 16 次主矩阵与 D1/D2 synthetic speed-stress
  几何，并选择 O1 现在扩入或推迟；
- 在 revision 2 获得接受前，不得开始实现、侦察、标定、探针或测量。

Accepted design-document changes:

无 RATE-003 设计变更获接受。仅把 SCENE-004 已实现并经证据确认的环周期
账目更正为 `31.0711 s`；这不接受 D2、不改变 A5 或任何测量门。

### Acceptance round 2 — 2026-07-30

Decision: **REVISION_REQUESTED**

Rationale:

Revision 2 已实质闭合 Round 1 的 1–7：P1–P5/C1–C4 把漏掉的 release ack
纳入共享主机时钟；RATE-003 使用新 schema 且双向拒绝 v2/v3 串喂；三相位
判定、冻结槽位顺序、探针四分支、synthetic D2 标签、qual-3 运行门与 O1
移出范围均已落到正文。用户对 0a 推荐范围的授权也已存在于
`docs/authorizations.md`，不再是未决项。`Δ(D)=median{Δ_i}` 配合离散度/
符号旗标可以作为三个确定性设计点的稳健工程汇总；`θ=0.05` 已正确收窄为
实际意义阈值而非统计等效界，这两个选择本轮不再退修。

但现稿仍有五组会让实现角色必须自行补设计的阻断歧义。最重要的是，12 个
正式 run 和 D2 探针的 `planned_duration_s` 完全没有数值或推导规则；“探针
与正式 run 同时长”只是两个未定义量互相引用。测量时域决定样本量、漂移暴露、
环数与用户资源，不能从 DETECT 资格门或 RATE-002 历史值猜。

Required revisions:

1. **冻结正式时域与完成门。** 对 D1/D2、5/20 Hz、8→6 m/s 分支以及探针，
   明写 release-origin `planned_duration_s` 的唯一数值或数据前推导公式，
   是否跨 rate/difficulty 保持相同，及其科学理由。分别写清 simulation
   duration、shared-host monotonic wall duration、evaluator cutoff、
   right-censored LOST 与完成采信的关系；该值进入 session/manifest/
   provenance/decision 哈希链。若用“完整环数”决定时长，必须在任何结果
   前冻结 lap 定义和取整；若所选时域实质扩大已授权的用户资源，先补用户
   授权账本。
2. **把时钟停点的验证次序写成可执行契约。** 当前“所有错钟都在任何副作用
   前失败”对运行中后续坏帧不可能按字面成立：修订须区分
   (a) launch/session/init/ready/release 的 pre-model/pre-run 或
   pre-release 副作用检查，与 (b) 后续逐帧在 observation/control/
   evaluator/re-anchor 更新前的 runtime fail-closed。C4 要给出确切谓词：
   ready 的 clock ID 与谁比较、是否检查 future/staleness、使用哪个当前
   时刻。P5 是进程内时钟依赖而非输出字段，须说明其 identity 如何由代码/
   schema 绑定。另为独立复核后的聚焦 Unity 定义专用、非测量的 clock-smoke
   身份；它不占用 scouting/calibration/probe/formal ID。把验收 1 的“在此
   之前任何 RATE-003 会话不得启动”收窄为“任何研究数据会话”，否则它与
   验收 1 自己要求的真实 RATE-003 聚焦验证循环矛盾。
3. **闭合探针与 6 m/s 分支。** 先判协议/数据 admissibility，再判 B1–B3；
   无相邻合格帧对、非有限统计或缺失主端点必须落入明确 invalid 分支，不能
   被当成位移模型证伪。把“上限 2 次”写成总 attempt 数还是补跑数，并与
   正式槽位统一。现稿一面说 B3 后不再重跑探针、直接进入 6 m/s 正式矩阵，
   一面又写“6.0 再次触底 → `BLOCKED_D2_UNSELECTABLE`”；必须二选一并与
   §6 的 D2 `FLOOR` final action 对齐。若新增 6 m/s 第二探针，会增加会话，
   须另取用户授权；若不新增，则删除 `BLOCKED_D2_UNSELECTABLE`，由正式
   D2 cell 的 `H1_FALSIFIED_FLOOR_AT_D2` 收束。
4. **使 decision 工件字段完全确定。** `H2_DIVERGENCE_FLAG` 目前使用未定义
   的“显著背离”；写出确切输入（应明确是否为 `C_20(D2)` 与 `C_5(D1)`）、
   比较式与阈值。`LADDER_PREMISE_VIOLATED` 必须是独立布尔/枚举字段，不能
   “追加后缀”改变六值 `final_action` 的 schema 枚举。若
   `DISPERSION_FLAG` 或 `SIGN_INCONSISTENT_FLAG` 为真而中位数仍触发 rate
   effect，decision/report 必须自动附带限定语并进入
   `DR-P1-M2-001`，不得输出不带异质性说明的笼统“contrast established”。
   非 gating 的 p05/p95 也要钉死分位数算法，保证跨实现复算一致。
5. **定义实际环周期工件。** “标定会话顺带读取过顶点时刻”不可按字面执行：
   RATE 标定在 HOLD，目标不跑；且 0.5 m 接受半径意味着车辆通常不经过精确
   顶点。修订须指定可运动的数据来源、lap 边界（例如有方向的起始截面）、
   所用 simulation/monotonic 时间、最少完整 lap 数、异常/漏 crossing
   处分和不可变工件归属。说明该实测周期仅报告，还是参与 `planned_duration`
   或“≥4 环”门；若参与门，必须在门使用前产生并冻结，不能从正式结果事后
   反改时域。

Re-review entry conditions:

- 构思角色提交 revision 3，逐条闭合上述 1–5；
- 0a 账本授权继续有效，无需重复；只有新增会话、采用 6.0 m/s 实档（0b）
  或 materially 扩大单次时域时才需新授权；
- revision 3 获接受前，不得开始 RATE-003 实现或任何 RATE-003 Unity 会话。
  `P1-DETECT-001` qual-3 仍按既有独立交接执行，不受本退修阻断。

Accepted design-document changes:

无。Round 1 已记账的 SCENE-004 标称周期修正不受影响；RATE-003 仍未进入
正式设计基线。

### Acceptance round 3 — 2026-07-30

Decision: **ACCEPTED**

Rationale:

Revision 3 已逐项闭合 round 2 的五个阻断项。`planned_duration_s` 现在对
探针、12 个正式槽、D1/D2、5/20 Hz 及 8→6 m/s 分支唯一冻结，并通过
simulation / shared-host monotonic wall / evaluator cutoff / LOST 右删失
四量门进入同一哈希链。时钟检查已按启动期与运行期分层，C4 谓词、P5 身份
绑定和不占研究 ID 的 `rs3-clock-smoke` 消除了原先的副作用次序及验证循环。
A0 先于探针 B1–B3，6 m/s 不再有第二探针；decision 的六值枚举、独立限定
字段、H2 公式和 type-7 分位数均已确定；环周期也改为已释放运动段上的有向
截面工件且只报告、不反改时域。实现角色无需再自行补设计。

两个工程数值的裁决如下。`150.0 s` 保留：它给最慢的 D1/5 Hz 条件约
4.83 个标称环和约 750 帧，超过本载体已冻结的 150 s/4 环资格尺度，也远长于
既有约 40 s 背景锁定失效点；更重要的是，本研究的独立设计点仍只有三个
预注册相位，把单次 run 拉长到 200–270 s 只增加相关时间样本和用户 Play
成本，不增加独立相位样本量。各 cell 等时还保持 `Δ_i` 与 H2 的暴露可比性。

原“累计 invalid attempt > 6”不采纳，改为达到 4 次即暂停。按原写法要到
第 7 次无效尝试后才停，相当于名义 16 次成功路径的 43.75%，且对 150 s
探针/正式 run 最多已额外消耗 17.5 min 测量时间；对本仓库既有整批协议报废
历史过松。单槽第 3 次无效本来就会触发局部阻断；4 是严格高于单槽上限
3 的最小全局阈值，若被触发必已出现跨槽分散失效；同时在无效消耗达到
名义预算 25% 时要求重新归因和授权。

Binding clarifications（按字面执行；与前文冲突时以下条款优先）：

1. **BC-R3-1 — 冻结 150.0 s。** `planned_duration_s` 精确为 `150.0`，
   适用于 D2 探针、全部 12 个正式 run、D1/D2、5/20 Hz 和获 0b 后的
   6.0 m/s 分支。不得按实测环周期、rate、difficulty 或已见结果伸缩。
   §10 四量完成门、`0.5 s` evaluator/simulation 差值容差和 §11
   report-only lap 语义原样执行。该值落在 0a 已授权范围内，不需要新授权。
2. **BC-R3-2 — 全局无效尝试护栏为 4。** `batch_invalid_attempt_count`
   是批次内单调不减的整数；scouting、calibration、probe、formal 四类
   研究数据身份中，每生成一份不可变的 invalid/non-admissible attempt
   receipt 就加 1，不因后来成功、换槽或换难度清零。`rs3-clock-smoke`
   及在创建研究 attempt identity/receipt 之前被 preflight 拒绝的操作不计。
   每次先归档无效 receipt 并递增计数，再求值：若
   `batch_invalid_attempt_count >= 4`，则在准备或授权下一研究数据会话前
   fail-closed 暂停，返回接受角色做失效归因，并取得用户对继续消耗会话的
   新显式授权。每槽总 attempt ≤ 3 的局部门独立存在；任一门先触发即停止，
   不得以另一门尚未触发为由继续。

Accepted design-document changes:

- `docs/phase1-single-drone-design.md` 升至 v0.3.9，纳入 RATE-003 的 v3
  共享时钟、难度/相位矩阵、150.0 s 等时完成门、总定义处分及 BC-R3-2
  全局无效尝试护栏。
- 0a 授权继续有效；O1/nadir/路线动力学仍在本提案范围外，6.0 m/s 实档仍须
  0b。`P1-DETECT-001` qual-3 PASS + 接受归因仍是研究数据会话运行门。
- 时钟/schema 批次改变时间语义，构成独立强制停点。稳定候选只能在接受角色
  完成 workflow §4.3.1（含 implementation write audit）后交独立复核；复核
  和 `rs3-clock-smoke` Unity 门通过前不得启动研究数据会话。

---

## Amendment DR-B — DR-P1-M2-001 round 1 预数据修订（B1/B2/B3）

Status: **PROPOSED**（awaiting acceptance round 4）
Author/role: 构思角色（ideation）
Created: 2026-07-30
Trigger: `docs/design-reviews/DR-P1-M2-001.md` round 1
`DESIGN_REVISION_REQUIRED`——三项阻断发现 B1/B2/B3 均为数据产生前的
有界设计缺口，必须在 RATE-003 batch 2 实现之前由接受角色裁定接受。

### 范围守卫（本修订的不变量）

本修订**不触碰**：`planned_duration_s = 150.0`（BC-R3-1）、θ = 0.05、
12 槽冻结顺序、BC-R3-2 全局无效尝试护栏、§1/§2 已实现并经复核的时钟/
schema 代码（batch 1，候选 `57f2561`）、`rs3-clock-smoke` 已通过的
Unity 证据、qual-3 交接、任何已归档 RATE-001/002 工件。全部修订落点是
batch 2 尚未实现的工件与编排（decision 工件、D2 配置审计、标定编排），
以及数据产生前的 binding 条款。

### B1 — 决策工件的无条件字段与 `CGEOM_DIVERGENCE_FLAG`

**缺口（DR B1）**：主端点 `C_track|geom` 的分母（几何可见时长）经
"帧率→追踪→云台→视锥"闭环依赖处理变量。5 Hz 档指向失败时分母坍缩会
抬高 `C_5`：掩盖真实效应（假 `NO_EFFECT` / 假 `CEILING(D2)`，后者直接
误诊 `H1_FALSIFIED_CEILING_AT_D2`）、并在正效应成立路径上让论文主数字
系统低估效应而无任何旗标。现行唯一防线"`C_geom` 显著下降→分开报告"是
未定义比较。

#### B1.1 逐 run 无条件字段（恒记录，不依赖旗标）

`p1-rate3-decision/v1` 的逐 run 记录区（12 个正式 run）新增：

- `c_geom`：无条件几何可见覆盖率 = 几何可见时长 / release-origin 测量
  时长（`CoverageEvaluator` 的 geometric duration / elapsed）；
- `c_track`：无条件追踪覆盖率 = 追踪成立时长 / release-origin 测量时长；
- 两者**逐值等于**该 run `metrics.final.json` 的对应权威量（同一 release
  identity 截止），decision 生成时复制并绑定该 run manifest SHA-256；
  不一致即 decision 生成 fail-closed。

探针 run 的同名量由 §5 探针工件自行承载，不进入 decision 的正式 cell 区。

#### B1.2 背离量、配对差与旗标（恒计算）

对每个难度 D ∈ {D1, D2}、相位 i ∈ {1,2,3}：

- `δ_geom_i(D) := c_geom(20 Hz, D, s*_i) − c_geom(5 Hz, D, s*_i)`；
- `Δ_i^track(D) := c_track(20 Hz, D, s*_i) − c_track(5 Hz, D, s*_i)`；
- `Δ^track(D) := median{Δ_1^track, Δ_2^track, Δ_3^track}`（与 §6 的
  `Δ(D)` 同法：三值中位数，无插值）；
- **`CGEOM_DIVERGENCE_FLAG(D) := ∃ i, |δ_geom_i(D)| > θ_geom`**；
- 研究层 **`CGEOM_DIVERGENCE_FLAG := CGEOM_DIVERGENCE_FLAG(D1) ∨
  CGEOM_DIVERGENCE_FLAG(D2)`**；
- **`θ_geom` 建议 0.05**（绝对覆盖率，与 θ 同级；数值由接受角色本轮
  裁定并数据产生前冻结，进入哈希链）；
- null 语义（镜像 §6 H2）：某难度 6 run 未全部 admissible 时该难度旗标
  为 `null` 并附 `cgeom_flag_unavailable_reason`；任一输入为 null 时
  研究层旗标为 `null`。此情形下研究层 `final_action` 必为
  `BLOCKED_INCOMPLETE`（§6 序 1），不会有未设防的主张路径。

#### B1.3 解释与引用规则（binding）

1. 旗标是诊断字段，**永不改变** `final_action` 的选择（与 §6 既有旗标
   架构一致）；
2. 研究层 `CGEOM_DIVERGENCE_FLAG = true` 时：
   - `dr_referral_required := true`（并入 §6 该字段的置真条件清单）；
   - decision 工件必须置 `cgeom_divergence_qualified = true` 并写入
     非空 `cgeom_qualifier_text`，内容至少含逐相位的
     `(c_geom(20), c_geom(5))` 原值对、`δ_geom_i`、条件化 `Δ(D)` 与
     无条件 `Δ^track(D)`；
   - **任何率效应/零效应/天花板结论**（研究层 `final_action` 序 2–6 及
     其依赖的难度层处分 3–6）在报告与论文中必须**同时**给出条件化
     `Δ(D)` 与无条件 `Δ^track(D)`，且不得把条件化 Δ 单独作为效应量；
     规范表述为"条件化配对差 X / 无条件配对差 Y；两者之差主要由几何
     可见性背离（δ_geom）承载，云台指向失败是候选机制"；
   - 伪天花板防线：`disposition(D2) = CEILING` 且
     `CGEOM_DIVERGENCE_FLAG(D2) = true` 时，
     `H1_FALSIFIED_CEILING_AT_D2` 的"返回设计"叙述必须标注该天花板
     可能是分母坍缩伪象，不得据此单独否定 H1；
3. 旗标为 false 时无条件字段仍全部在工件中（透明可复算）；论文可以
   条件化 Δ 为主效应量，并引用旗标 false 作为分母稳定性的证据。

#### B1.4 schema 与哈希链

`p1-rate3-decision/v1` 属 batch 2 尚未实现的工件，本修订在实现前扩充
其 v1 字段定义，不构成已实现 schema 的追改。B1.1–B1.3 全部字段
（逐 run `c_geom`/`c_track`、`δ_geom_i`、`Δ_i^track`、`Δ^track`、
两级旗标、`θ_geom`、null 原因、`cgeom_divergence_qualified`/
`cgeom_qualifier_text`）与旗标定义式进入 decision schema 及其哈希链，
数据产生前冻结。

### B2 — 难度配置的包络审计分治（供接受角色径直以 BC 裁定）

**缺口（DR B2）**：`tools/build_scene004_geometry.py` 的五个门中，
`loop_period_s`（gate [30,45] s）与 `distractor_opportunities`
（tick 预算 = `floor(loop_period × HZ)`）由配置速度导出。D2=8.0 m/s 的
环周期 `62.14213562373095 / 8.0 = 7.7678 s`、6.0 m/s 为 `10.357 s`，
必然 `ENVELOPE_OUT_OF_BOUNDS`；工具还把 `SCENARIO_PATH` 钉死为 D1 配置。
Inputs 节"预期零违规"因此不可满足，审计范围未定义。

#### B2.1 分治表（对 `scenario.p1-scene-004-d2.json` 及 0b 后的 6.0 配置）

| 门 | 类别 | 难度配置处置 |
|---|---|---|
| `max_slant_range_m` | 速度无关（几何/位姿导出） | **必须重跑并通过**；且数值必须与 D1 基线工件逐值一致（容差见 B2.3），不一致即 `ENVELOPE_OUT_OF_BOUNDS` |
| `max_off_nadir_deg` | 速度无关 | 同上 |
| `predicted_min_side_p05_px` | 速度无关（仅依赖斜距与已实测乘积常数） | 同上 |
| 路线合法性审计（SCENE-002 已接受工具） | 速度无关 | **必须重跑并通过**，逐值一致同上 |
| `loop_period_s` ∈ [30,45] s | 速度导出 | **记录性重算**：记录难度配置实际值、D1 基线值与差值；不参与 pass/fail |
| `distractor_opportunities` ≥ 10 | 速度导出（tick 预算随环周期缩水） | 同上记录性重算（含逐干扰车 `fully_in_frame_ticks` 与 `tick_count`） |

#### B2.2 为什么是"记录性重算"而非静默豁免

- `[30,45] s` 环周期门编码的是 SCENE-004 开发载体在 2.0 m/s 下的侦察
  节奏假设，是 D1 资格化语境的门，不是 RATE-003 的安全或有效性性质；
  D2 按构造不可能满足它，强行沿用等于禁止难度阶梯本身；
- 干扰机会 tick 预算按"每环"定义，随速度机械缩水；而单位时间的干扰
  暴露不变（每环 tick 数 × 每 150 s 环数 ≈ 150 × 采样 Hz，与速度无关，
  仅受 floor 取整影响）。该门守的是 SCENE-004 侦察资格化，其结论已在
  D1 消费完毕；RATE-003 的侦察资格表基于 hold 相机投影，本就与速度
  无关（一次侦察覆盖两难度）；
- 记录性重算保留全部数值透明度：审计工件里 D2 实际值、D1 基线与差值
  俱在，论文与后续 DR 轮可直接引用，无信息损失。

**逐值一致检查的理由**：声明的配置差异仅限 `scenario_id` 与
`target.speed_mps`（Inputs 节），故一切几何/位姿导出量必须与 D1 基线
完全相同；任何漂移都证明配置差异超出声明，应 fail-closed 而非放行。

#### B2.3 工件语义与被取代的表述

- 难度配置的审计工件必须含：分治模式声明字段、必须通过门的结果与
  对 D1 基线工件（以 SHA-256 引用）的逐值一致检查、记录性门的
  {难度值, D1 基线值, 差值} 三元组、以及**仅在必须通过门集合上计算**的
  overall status（沿用 `ENVELOPE_OK` / `ENVELOPE_OUT_OF_BOUNDS` 值域）；
- 一致性容差：**建议逐值位相同（bit-equal），退而求其次
  `|diff| ≤ 1e-9`**；数值由接受角色裁定并冻结；
- `SCENARIO_PATH` 的参数化属 batch 2 实现细节，语义以本节为准；
  D1 基线工件不重跑、不追改；
- **接受后取代**：Inputs 节"重跑路线合法性与包络审计留证（几何未变，
  预期零违规）"与 §5 下调授权链 (ii) 中的同类表述，一律按本分治解读——
  "预期零违规"仅指必须通过门集合。

### B3 — 标定机制、会话预算与配对初始化锚点

**缺口（DR B3）**：HOLD 机制每会话只在一个声明 `s*` 生成目标；§7 的
"每档难度标定 1 次 = 2 次"至多产出 2 个相位框，覆盖不了 3 相位 × 2 难度
= 6 个初始化点。且"同一 (difficulty, phase) 两率共享字节相同冻结框"
这一配对公平锚点未成文。

#### B3.1 机制裁定（推荐方案 B：六次标定会话）

- 标定会话 ID：**`rs3-d{1|2}-p{1|2|3}-calib`**（取代 §7 的
  `rs3-d{1|2}-calib`），共 6 个标定槽位；
- 每会话严格沿 RATE-002 §3 已经 Unity 实证的语义执行：在该难度的冻结
  scenario 配置下声明单一 `s*_i` → HOLD → 冻结 hold 参考帧 + 操作者
  标注框 + 全部 SHA-256 入库。**零新机制**：不引入 HOLD 内目标重定位，
  不引入逐 run 现场冻结；
- **全部 6 份冻结产物先于 D2 探针入库**——保持"一切操作者裁量输入先于
  任何测量数据"的不变量；执行序更新为：侦察 1 → 标定 6 → D2 探针 →
  12 正式测量；
- 标定与侦察槽位纳入 §4 的统一 attempt 口径：每槽位总 attempt ≤ 3
  （补全 §4 未明写的部分）；标定/侦察无效尝试本就按 BC-R3-2 计入全局
  计数器（其收据语义已覆盖 scouting/calibration 身份，BC-R3-2 无需
  修改）。

#### B3.2 备选与被拒绝方案（记录在案，供接受角色裁定）

- **方案 A（多相位单会话标定）——不推荐**：需要新的 Unity 侧 HOLD 内
  重定位机制与多份冻结包语义，为省 4 次短会话引入新实现与新复核面，
  且改变已实证的冻结语义，代价不相称；
- **方案 C（逐 run HOLD 现场冻结）——拒绝**：D2 各相位的框将在全部 D1
  结果可见之后才标注，破坏"操作者裁量先于一切测量结果"的预注册边界；
  且字节相同锚点只能靠"首 run 冻结、次 run 复用"维持，等于把冻结点
  搬进批次中段；
- **方案 D（跨难度共享的每相位标定，3 次会话，名义 17 次）——语义
  成立但不推荐**：HOLD 中目标静止，hold 帧内容与 `target.speed_mps`
  无关，故 (D1, s*_i) 与 (D2, s*_i) 的 hold 帧物理同一，3 份产物可
  跨难度共享（附带消除 H2 跨难度比较中的标注方差）。代价是 init 帧
  身份链需要一个跨 `scenario_id` 的显式豁免（run 的 scenario 哈希 ≠
  init 帧捕获时的 scenario 哈希），削弱既有混批次/混载体 fail-closed
  边界。鉴于本仓库该边界屡次拦下真实缺陷，本稿推荐 B；若接受角色
  优先会话预算而选 D，必须以 binding clarification 写明身份豁免的
  精确谓词（豁免仅限标定产物、仅限声明差异字段、哈希链仍逐份绑定）。

#### B3.3 会话预算重算（新验收 0c）

- 名义成功路径：侦察 1 + 标定 6 + 探针 1 + 正式 12 = **20 次研究数据
  会话**，超出 0a 的"约 16 次"名义值；按 DR-P1-M2-001 与 0a 条款，
  **须用户重新确认**——新增验收 **0c**：用户逐字确认 20 次名义预算，
  记入 `docs/authorizations.md`；账本无条目视为未授权，任何研究数据
  会话不得启动；
- 最坏上界更新：20 个槽位 × 3 = **60**（显式登记，取代 §4 登记的 39）。
  BC-R3-2 的全局护栏独立存在：累计 invalid attempt 达 4 即暂停归因并
  重新授权，会远早于该上界触发；两门任一先触发即停止；
- 供用户决策参考：标定会话为 HOLD-only、无 150 s 测量段，单次时长与
  操作负担显著低于正式 run（RATE-002 标定已有实证），+4 次的实际
  Play 成本有限。

#### B3.4 配对初始化锚点（binding）

1. **同一 (difficulty, phase) 的 5 Hz 与 20 Hz 两个正式 run 必须从
   同一份 SHA-256 绑定的冻结标定产物初始化**：同一 hold 参考帧文件
   （字节相同，SHA-256 相等）与同一操作者标注框（逐字段相等）；
2. 启动期前飞检查（沿 §1.1(a) 次序）：run 声明的 (difficulty, phase)
   与所加载标定产物的身份及 SHA-256 不匹配 → 在构造模型/创建 run 目录
   之前拒绝，fail-closed，无副作用；
3. 纵深防线：run manifest 与 `p1-rate3-release-provenance/v1` 记录
   所用标定产物 SHA-256；`p1-rate3-decision/v1` 逐 run 记录该哈希并在
   判定生成时校验每对 run 哈希相等——不等即该 run 视为非 admissible，
   经 §6 难度层序 1 落入 `BLOCKED_INCOMPLETE_CELL(D)`，交接受角色归因；
4. 探针 run `rs3-probe-d2`（5 Hz / D2 / s*₁）同样必须从 (D2, s*₁) 的
   冻结标定产物初始化，接受同样的前飞检查与哈希记录。

#### B3.5 接受后取代的表述

§7 的"每档难度标定 1 次 = 2 次"、"合计约 16 次研究数据会话"与标定 ID
`rs3-d{1|2}-calib`；§4 的"最坏情况为 13 个槽位 × 3 = 39 次"；
Compatibility 依赖序中的"标定"（更新为"标定 ×6，全部先于探针冻结"）。
其余条款（含 BC-R3-1/R3-2）不变。

### 七要素映射（workflow §4.1）

| 要素 | 落点 |
|---|---|
| 1 问题与研究价值 | 三项预数据缺口的闭合使 batch 2 可按字面实现、M2 主张可辩护：B1 堵死分母坍缩伪结论路径，B2 使难度配置审计可执行，B3 使配对差 `Δ_i` 的公平锚点可审计 |
| 2 输入/输出/接口 | `p1-rate3-decision/v1` 字段扩充（B1.1/B1.2）；难度配置审计工件分治语义（B2.3）；标定会话 ID 与冻结产物哈希绑定（B3.1/B3.4）。帧/控制/观测协议、时钟契约、`metrics.json` 定义零变更 |
| 3 算法/行为假设 | `δ_geom` 捕获"指向失败"通道（RATE-002 实测 c_geom≈0.61 证实通道存在）；hold 帧内容与速度无关（B3.2 方案 D 依据）；单位时间干扰暴露与速度无关（B2.2） |
| 4 与 v0.3 兼容 | 主端点仍为 `C_track|geom`，无条件量为伴随诊断，不改指标定义；不改阶段边界与硬件目标；唯一资源变化是 +4 次标定会话，经 0c 用户确认 |
| 5 可证伪验收条件 | 见下节"验收条件增补" |
| 6 基线/消融/失败模式/资源 | 见下节"失败模式与资源风险（增量）" |
| 7 建议实现范围 | 全部落在 batch 2（decision 生成器、审计工具参数化与分治、标定编排与前飞检查）；batch 1 零返工；batch 2 仍按既有裁定构成复核停点 |

### 验收条件增补（接受后并入正文验收清单的确切落点）

- **0c（新增）**：用户逐字确认 20 次名义研究数据会话预算并记入
  `docs/authorizations.md`；无条目不得启动任何研究数据会话；
- **验收 2 增补**：6 个标定槽位按 `rs3-d{1|2}-p{1|2|3}-calib` 完成且
  全部冻结产物（帧 + 框 + SHA-256）先于探针入库；标定/侦察槽位总
  attempt ≤ 3；
- **验收 3 增补**：探针从 (D2, s*₁) 冻结标定产物初始化，前飞检查与
  哈希记录可证；
- **验收 4 增补**：逐对 run 的标定产物 SHA-256 相等经 decision 校验；
  启动期前飞拒绝错配标定产物且无副作用（有测试）；
- **验收 5 增补**：decision 工件含 B1.1/B1.2 全部字段与两级
  `CGEOM_DIVERGENCE_FLAG`（θ_geom 冻结值）、`cgeom_divergence_qualified`
  与 `cgeom_qualifier_text` 的置位逻辑、B1.3 引用规则的表述模板；旗标
  不改变 `final_action` 有测试断言；
- **验收 5c（新增）**：难度配置审计工件按 B2.1 分治——必须通过门全过
  且与 D1 基线逐值一致（冻结容差），速度导出门记录三元组，overall
  status 仅在必须通过门上计算。

### 失败模式与资源风险（增量）

- **θ_geom 过紧**：旗标频繁为真 → 频繁 DR referral。0.05 与 θ 同级、
  且远小于 RATE-002 实测背离幅度（1.0 − 0.61 ≈ 0.39），误报风险可控；
  若接受角色改值，须同样数据前冻结；
- **逐值一致检查误报**：若 D1 基线工件与难度重算在不同浮点环境产生，
  bit-equal 可能失败——比较必须针对**已归档的 D1 基线工件数值**，
  且工具在同机同实现运行；退化容差 1e-9 由接受角色裁定；
- **INVALID_PAIRING 路径**：标定产物错配在启动期即被拒（无副作用、
  不消耗 attempt 之外的会话）；判定期兜底校验若触发，说明前飞检查
  存在缺陷，须作为缺陷归因而不仅是 run 报废；
- **预算被拒**：用户若不确认 20 次（0c），方案 D（17 次）是记录在案的
  退路，但须补身份豁免 BC；不存在"回到 2 次标定"的合法路径——那正是
  B3 认定不可执行的起点；
- 零新模型、零新依赖、零几何变更、零已实现代码返工。

### 待接受角色裁定的数值与选项清单（round 4）

1. `θ_geom`（建议 0.05）；
2. B2.3 逐值一致容差（建议 bit-equal，退化 `1e-9`）；
3. 标定机制：方案 B（推荐，6 会话）或方案 D（3 会话 + 身份豁免 BC）；
4. 0c 预算确认路径（20 次；若选 D 则 17 次）；
5. 标定/侦察槽位总 attempt ≤ 3 的口径补全。

### Acceptance round 4 — 2026-07-31

Decision: **ACCEPTED**

Rationale:

Amendment DR-B 对 `DR-P1-M2-001` round 1 的 B1/B2/B3 给出数据产生前、
可按字面实现且可复算的闭合：无条件 `c_geom`/`c_track` 与数值旗标堵住
条件化分母坍缩的伪结论路径；难度配置审计分治保留速度无关安全/几何门，
同时把按构造必变的速度导出量改为透明记录；六个既有 HOLD 语义的标定槽位
既覆盖 3 相位 × 2 难度，也维持操作者裁量先于探针和正式数据的边界。
独立设计审查 round 2 已逐项确认技术充分。本轮采用审查优先值与方案 B，
不开放跨 `scenario_id` 的方案 D 身份豁免。

Binding clarifications（按字面执行；与 Amendment DR-B 或此前接受文本冲突时
以下条款优先）：

1. **BC-DRB-1 — `theta_geom` 冻结为 `0.05`。**
   `CGEOM_DIVERGENCE_FLAG(D) := exists i,
   abs(delta_geom_i(D)) > 0.05`；它及研究层 OR/null 语义、无条件字段、
   限定语和引用规则按 B1.1–B1.4 原样实现。该旗标永不改变
   `final_action`。
2. **BC-DRB-2 — D1 数值一致语义。** 比较对象必须是审计工件引用的、
   已归档 D1 基线工件值。能保留相同数值类型与序列化表示时要求
   bit-equal；若工具链重算只能提供有限浮点数，则唯一退化规则为
   `abs(difficulty_value - archived_d1_value) <= 1e-9`。整数、布尔、
   字符串、枚举、数组长度、键集合和 canonical order 必须精确相等，
   不适用浮点退化。任何非有限值或缺字段均失败关闭。
3. **BC-DRB-3 — 路线合法性逐值相等字段集。** 除允许不同的
   `scenario_id` 外，D2/获 0b 后 6.0 配置的
   `p1-scene-road-audit/v1` 必须与已归档 D1 报告逐字段比较：
   `schema_version`、`status`、`route_sample_count`、
   `road_violation_count`、`audited_obstacle_count`、
   `overhead_exemption_count`、`obstacle_violation_count`、
   `vehicle_violation_count`、`prop_violation_count`、
   `nature_violation_count`、`building_violation_count`、
   `other_violation_count`、`road_violations` 和
   `obstacle_violations`。计数、状态、数组长度/次序和每项字符串/整数
   字段精确相等；两类 violation 项中的有限几何浮点字段
   （`route_s_m`、坐标、距离与高度）按 BC-DRB-2。必须同时满足
   `status == "CLEAR"`、全部 violation count 为 0、两 violation 数组
   为空；字段相等本身不能替代通过门。
4. **BC-DRB-4 — 采用标定方案 B。** 必须使用六个
   `rs3-d{1|2}-p{1|2|3}-calib` 独立槽位；全部六份冻结产物先于探针
   入库。不得采用方案 D，不得跨 `scenario_id` 复用标定身份。scouting
   的一个槽位和每个 calibration 槽位均为**总 attempt <= 3**（初次
   attempt 计入三次），并继续受 BC-R3-2 的批次无效尝试计数器约束。
5. **BC-DRB-5 — 配对错配按对失败。** 判定期若同一
   `(difficulty, phase)` 的 5 Hz/20 Hz 两 run 所绑定标定产物 SHA-256
   不等，则该配对的**两个 run 均**标记 non-admissible，并经 §6 序 1
   落入 `BLOCKED_INCOMPLETE_CELL(D)`；同时按实现缺陷归因，不得只报废
   任意一侧后继续解释配对差。
6. **BC-DRB-6 — 探针归因读取无条件量。** 探针工件必须记录并哈希绑定
   同一 release identity 的 `c_geom`、`c_track` 和
   `C_track|geom`。A0/B1–B3 的冻结谓词及判序不变；任何探针分支归因
   必须同时读取并报告这三个量，禁止只看条件化量解释触底或不降档。
7. **BC-DRB-7 — 0c 是运行授权门，不是设计默认值。** 方案 B 的成功路径
   名义预算为 20 个研究数据会话，最坏槽位上界为 60；BC-R3-2 在累计
   invalid attempt 达到 4 时仍更早暂停。用户对 20 次名义预算的逐字确认
   必须先写入 `docs/authorizations.md`；账本无 0c 条目时，任何
   scouting/calibration/probe/formal 会话均不得启动。接受本 amendment
   本身不构成 0c 授权。

Accepted design-document changes:

- `docs/phase1-single-drone-design.md` 升至 v0.3.10，纳入 B1 decision
  字段/旗标与引用规则、B2 must-pass/record-only 分治及 D1 值相等语义、
  方案 B 的标定 ×6/配对哈希锚、名义 20 次预算与 0c 运行门。
- M2 关闭检查单登记 `DR-P1-M2-001` 的 N1/N2/N3/N5：R1' 阈值边缘性、
  R2' 错误匹配的可见性分解、N=3 伪复现件/固定顺序限制、benign 载体
  标签与困难场景义务；未逐项披露前不得关闭 M2。
- Batch 1、BC-R3-1、BC-R3-2、0a、0b、qual-3 运行门、O1/nadir/路线
  动力学的范围边界均不变。Batch 2 只能实现本轮接受范围；研究数据会话
  仍同时受 0c、qual-3 PASS + 接受归因及其他既有前置门约束。

0c fulfillment:

- 2026-07-31，用户对接受角色所述“侦察 1 + 标定 6 + 探针 1 + 正式 12，
  共 20 次名义研究数据会话；最坏槽位上界 60，但累计第 4 次无效尝试仍
  强制暂停”的问题原话回复："同意授权"。逐字账本见
  `docs/authorizations.md`。
- 0c 只解除预算授权门；`DR-P1-M2-001` round 3、qual-3 PASS + 接受归因、
  0b 条件门及全部协议/admissibility 门不因本授权自动满足。

### Acceptance batch-2 clarification / stop-point round — 2026-07-31

Clarification decision: **ACCEPTED_WITH_BINDING_CLARIFICATIONS**

Stop-point decision: **NOT_CONFIRMED_REWORK_REQUIRED**

实现候选 `6417dc3` 提出的 CQ-1/CQ-2 均是把已接受语义补成可执行输入，
不改变测量矩阵、指标、冻结数值、阶段边界或研究主张，因而无需重开
`DR-P1-M2-001`。但 CQ-2 的两份路线审计报告尚未生成，当前 difficulty
audit 正确失败关闭为 `ENVELOPE_OUT_OF_BOUNDS`；候选还不是可交独立复核的
稳定版本。

Binding clarifications（按字面执行）：

1. **BC-B2-CQ1 — 四份 rate × difficulty 配置。** 允许并要求四份冻结
   配置：D1/20 Hz 复用 `scenario.p1-scene-004.json`，另有 D1/5 Hz、
   D2/20 Hz、D2/5 Hz 三份版本化文件。同一 difficulty 的两率配置必须
   共用同一 `scenario_id`，且只能在 `sensor.capture_hz`、
   `sensor.retained_frame_count`、
   `evaluation.maximum_pending_frame_count` 三字段不同；同一 rate 的
   D1/D2 只能在 `scenario_id` 与 `target.speed_mps` 不同。启动前的
   `check_scenario_configs()` 必须逐字段失败关闭并把四份配置 SHA-256
   绑定进 campaign/session 溯源；不得用 `scenario_id` 编码 rate。
2. **BC-B2-CQ2 — 先建立、后冻结 D1 路线审计基线。** 接受新增的同一
   `RoadSceneAuditor` Editor generator，按 D1 后 D2 的固定次序从冻结场景
   字节生成 `P1-M2-RATE-003-d1-road-audit.json` 与
   `P1-M2-RATE-003-d2-road-audit.json`。两份报告必须各自 `CLEAR`、零违规，
   D1 文件在本批稳定候选中首次提交后即成为只读 archived baseline；D2
   按 BC-DRB-2/3 对其逐字段比较。生成器、两报告、报告 SHA-256 和最终
   `p1-rate3-difficulty-audit/v1` 工件必须属于同一实现证据链。
3. **BC-B2-CQ2 完成门。** 在确认停点前，实现在无研究数据会话的 Unity
   Editor 证据运行中生成并提交两报告，随后以可从仓库根目录复现的命令
   （模块调用且显式给出 `--output`）重跑 difficulty audit；最终状态必须
   为 `ENVELOPE_OK`，所有 must-pass 项通过且 record-only 项仍不参与
   overall status。当前两报告缺失所得 `ENVELOPE_OUT_OF_BOUNDS` 只证明
   fail-closed 正常，不是通过证据。
4. **证据命令修正。** 实现证据不得继续把缺少模块路径/`--output` 的
   `tools/build_rate3_difficulty_audit.py --scenario ...` 记为已运行命令；
   必须写入实际可复现命令、退出码和输出工件 SHA-256。Unity clone 运行的
   162/162 Edit + 3/3 Play 可保留为实现者证据，独立复核仍须在一次性
   worktree/无项目锁环境复现相称测试。

Write-audit attribution（本轮候选，尚非最终停点）：

- `python3 tools/check_role_writes.py --role implementation --base 57f2561`
  标出 6 路径，均可归因到非实现批次：`docs/reviews/P1-M2-RATE-003.md`
  属 `3c91b52` 代码复核；`docs/authorizations.md` 与
  `docs/unity-test-log.md` 属 `33fe919` 接受代录；
  `docs/design-reviews/DR-P1-M2-001.md` 属 `0f84f07`、`513f20b`、
  `27c1d70` 独立设计审查；RATE-003 proposal 属 `75c8daa` 构思与
  `38cc95f` 接受；正式设计属 `38cc95f` 接受。实现提交 `6417dc3` 未写
  这 6 路径。归因成立，但实现补证形成新候选后仍须以同一 base 重跑审计。

Re-entry conditions:

- 提交两份路线审计报告与最终 difficulty-audit 工件；
- 可复现命令返回 `ENVELOPE_OK`，实现证据改正命令与结果；
- 自动检查继续通过，工作树干净，形成新的候选 commit；
- 返回接受角色重跑 implementation write audit 并确认停点，之后才能交
  独立复核。任何 scouting/calibration/probe/formal 会话仍禁止。

### Acceptance batch-2 stop-point round 2 — 2026-07-31

Stop-point decision: **CONFIRMED**

Stable candidate: `dea5111` (review baseline: `57f2561`)

Rationale:

- BC-B2-CQ2 的两份路线审计报告已由同一 Editor 证据运行按 D1 后 D2
  生成并提交；两者均为 `CLEAR`、126 个路线样本、782 个受审计障碍物、
  全部违规计数为 0 且违规数组为空。除唯一豁免的 `scenario_id` 外，两份
  JSON 逐字段相同；SHA-256 分别为 `9dddecaa…1775` 与
  `492d3d1f…8636`。
- 从仓库根目录按证据记录的模块命令重建 difficulty audit，返回码为 0，
  状态为 `ENVELOPE_OK`、`failures=[]`；除 provenance 字段
  `generated_unix_s` 外，重建结果与已提交工件逐字段相同。已提交工件
  SHA-256 为 `dd931be2…acb2`，must-pass 项全部通过，record-only 项未进入
  overall status。
- 四份冻结配置的 SHA-256 与 campaign 证据一致；接受角色重跑
  `.venv-track/bin/python -m unittest discover -s tests` 得 279/279 通过，
  工作树保持干净。Unity Edit 162/162 与 Play 3/3 属实现者停点证据，仍待
  独立复核在一次性 worktree 复现相称检查。

Write-audit attribution（最终停点）：

- 已按 workflow §4.3.1 对 `dea5111` 以
  `python3 tools/check_role_writes.py --role implementation --base 57f2561`
  重跑。工具仍列出同一 6 个跨角色路径：review 文件来自 `3c91b52`；
  authorization 与 Unity log 来自 `33fe919`；design-review 来自
  `0f84f07`、`513f20b`、`27c1d70`；proposal 来自 `75c8daa`、
  `38cc95f`、`3bea810`；正式设计来自 `38cc95f`；实现返工提交
  `dea5111` 未修改这 6 个路径。告警全部完成非实现归因，未发现实现角色
  越权写入。

Handoff and freeze:

- `dea5111` 是 batch 2 稳定候选，现交独立复核角色按 evidence 的 Review
  scope 审查。本结论只确认停点成立，不构成独立代码复核通过。
- 在独立复核 verdict 前，不得启动依赖本结果的后续实现，也不得准备或
  启动 scouting、calibration、probe 或 formal 研究数据会话；后者仍受
  qual-3 `PASS` 加接受归因以及全部既有运行门约束。

### Acceptance batch-2 review closure attribution — 2026-07-31

Review disposition: **ACCEPTED (`PASS_WITH_NOTES`)**

Reviewed candidate: `ab8ae73`; review record: round 4 in
`docs/reviews/P1-M2-RATE-003.md`.

Closure attribution:

- Round 3 的两个阻塞项归因于 batch-2 orchestration 实现，而非已接受设计：
  A0 首次裁决过早冻结 campaign 级 `probe.json`，切断 §5 同槽重跑；HOLD-only
  calibration 没有生产可达的失败收据路径，导致 BC-DRB-4/BC-R3-2 计数
  fail-open。实现提交 `ab8ae73` 在同一停点内修复两项，并补了真实生产路径
  回归；没有改动 C#、配置、controller 或已提交审计工件。
- 独立复核 round 4 在一次性 worktree 中逐项确认修复，复跑原始复现并得到
  `.venv-track` 287/287、focused rate3 43/43；`.venv-yoloe` 285/287 的两项
  失败仍是未安装 contrib CSRT 的既有环境差异。verdict 为
  `PASS_WITH_NOTES`，无剩余阻塞 finding，代码复核门关闭。

Live non-blocking notes（进入批次台账，不改变本轮 verdict）：

1. 若第三次无效 probe 在调用裁决前先归档，campaign 级
   `BLOCKED_PROBE` 工件不会生成，但 per-slot cap 与缺失 terminal probe
   仍会阻止 formal 授权。运行手册在 probe 开始前必须明确“先裁决、后归档”
   的顺序；后续可补 backfill，但不阻塞本轮 Unity 套件复跑。
2. `metrics.final.json` 当前由本 run 的 create-once 目录、场景身份和 cutoff
   delta 间接绑定；若以后新增 verify-style 重查路径，应同时加入显式
   release-identity 字段校验。本轮没有该重查路径，因此记技术债而不返工。
3. evaluator truth stream 的记录形状、门控与 stale-slot 清理有 Edit/Python
   覆盖，但仍未由真实 live Play session 端到端证明；该项保留在 Unity/
   首次合法运行一侧，不能用当前代码复核替代。

Resulting gate:

- Batch 2 不是 `DONE`：下一步由用户在 `ab8ae73` 的代码等价树上原地复跑
  Edit Mode 162/162 与 Play Mode 3/3。复跑前须按 workflow §4.5 记录实际
  HEAD、干净状态及相对 `ab8ae73` 的仅文档差异。
- 在用户 Unity verdict 进入日志前，不推进依赖 batch 2 的实现；无论套件
  结果如何，scouting/calibration/probe/formal 研究会话仍须等待
  P1-DETECT-001 qual-3 `PASS` 加接受归因、run-gate record 与所有既有门。
