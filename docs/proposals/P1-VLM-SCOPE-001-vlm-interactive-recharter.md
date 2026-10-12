# P1-VLM-SCOPE-001 — Phase 1 recharter：研究主张转向持续跟踪任务中的 VLM 双向互动通信

Status: REVISION_REQUESTED
Author/role: 构思角色（ideation，Fable 池）
Created: 2026-08-06
Last updated: 2026-08-06
Revision: 3（回应 Acceptance round 3 的 5 条必修项，逐条回应见 §15；
round 1/2 的回应保留在 §11/§13，不重写）

## 0. 修订索引

### Round 3 必修项 → 本稿落点（本轮）

| # | 必修项 | 落点 | 实质变化 |
|---|---|---|---|
| 1 | 时序校准独立冻结门 | §2.4a、§4.7 | p95 = type-7 分位、有效样本 ≥ 20、三参数各自导出公式（含 TRACK-002 档案 `3.332854 ms` 重放常量）；任一候选超上界或样本不足 ⇒ `VLM_REPROMPT_TIMING_INFEASIBLE` 返回构思，**禁止截断**；全部延迟样本计入 Q1 ≤ 40 次；串行表插入"三值 amendment：Acceptance 裁定 + 用户逐字授权"独立停门 |
| 2 | action/ACK 恢复状态机 | §2.4b | 缓存键逐字三元组、canonical JSON 字节定义（沿用 BC-P2-10 strict RFC 8259 先例）、`PREPARED→APPLIED 见证→ACKED` 状态机 + 崩溃恢复算法（运行日志见证判"至多生效一次"）、首次空账本与损坏账本分离、迟到 ACK 的双侧终态规则、`schema_version = vlm-interaction/v1`、`search_hint` 有效期改单调钟对 |
| 3 | query/report/颜色对照机器可评分 | §3.1 | `answer.facts` 结构化字段（text 仅展示）；题型拆分消除 OR；report 事件 ontology + ±5 s 匹配窗 + 贪心一对一 + 多报/迟报 TP/FP/FN 规则；颜色标定集与正式 paired runs 组隔离、HSV 与 90% 资格在正式结果前冻结、不过资格即阻断属性档主张 |
| 4 | 分层硬停与全文残留 | §5 V1、§8、§3.2 H3、§4.7 | `STRATUM_UNAVAILABLE` 改为 API 前硬停（扩来源重冻结或经新裁定缩窄总体）；删 `claude-sonnet-5` 默认残留；删 H3 `0.8` 建议残留；串行表过期 round 编号修正；"不加预算"措辞统一为全部计入 ≤ 40 |
| 5 | 最近邻边界重做 | §1.3 | AVDN 更正为真实双向问答；新增 TrackVLA / TrackVLA++ / VLM-Assistant（自反思恢复）三行逐项比较；verified distillation 增加 VPD（verify-then-distill 先例）对照；缝隙收窄为"动态跟踪中 operator retask + 机→人主动汇报 + loss-assist 的操作员在环组合"；query/inclusion 更新防漏 |

### Round 2 必修项 → 本稿落点（上一轮，保留）

| # | 必修项 | 落点 | 实质变化 |
|---|---|---|---|
| 1 | 端到端时钟/expiry/replay 合同重写 | §2.1 信封、§2.4 | 时效语义改由 `simulation_time_s` + `capture_monotonic_s` + `capture_monotonic_clock_id=system-stopwatch/v1` 承担，Unix 仅审计；**删除水位即 stale 规则**；`reprompt` 完整继承源帧初始化 → 顺序 replay/catch-up → 原子头相等机制 |
| 2 | VLM 延迟与三门数值冲突 | §2.4a | 按用户 2026-08-06 方向确认（账本当日条目：排除 2 s 硬门；Gemini Flash 实测好网络 1–2 s、协商更长）走**扩参数路线**：`vlm_reprompt.*` 单列参数组 + 协商/出框解耦 + 保守合同上界 + 延迟校准测量定值后另行用户授权；DETECT 原参数组零改动 |
| 3 | action 幂等与回执绑定 | §2.4b | ACK 绑定 `action_id`+`context_id`+payload SHA-256+终态；同 ID 同 hash 重放返回缓存终态 ACK；同 ID 异 hash 才 `ID_CONFLICT`；ACK 账本落盘、跨重启恢复、in-flight 解除条件冻结 |
| 4 | 四类任务可执行归因合同 | §3.1 | `Δ/T_hold/τ/T_censor`、LOST/框突变阈值、query 逐字段容差全部赋值；retask 主对照改为**非学习颜色分割选框**（同帧同属性、经典 CV），oracle/UI 注入框改列上界分栏；任务分"属性档/语义档"，主张按档分层；paired schedule 冻结 |
| 5 | criterion 4 行为闭环 | §4.5 | 门改计**成功 REANCHOR 闭环**（三门+完整 replay 收敛+原子替换）≥10 次、含 ≥1 次 DISAGREE 成功重播种、会话 ≥150 s、`incorrect/matched < 0.5`；十次全拒不得关闭；LOST 只由 controller 触发、truth 只离线评分 |
| 6 | spike/model/budget/串行修正 | §5 V1、§4.7 | 教师改 `TEACHER_MODEL_ID_TBD_Q1`（Q1 绑定供应商公开可调用的版本化 ID+价格）；预算耗尽=未处理样本计失败入分母；18 层每层最小数+`STRATUM_UNAVAILABLE` 规则；序 4 改"VLM-1 预算另行授权"；spike 顺带记录端到端延迟分布（为必修 2 的校准供数，不加预算） |
| 7 | 文献与蒸馏冻结 | §1.3、§5 V6 | VL-UniTrack（三点撞名不撞实质区分）与 AVDN 家族四篇纳入最近邻表，缝隙表述收窄；UAV-Track VLA 判断补出处；V6 冻结 pass-only 训练集/failed 样本诊断集/`teacher=0 ⇒ NOT_DISTILLABLE_NO_TEACHER_SIGNAL`；保留比数值归 VLM-3 独立提案采集前停点 |

### Round 1 必修项 → 本稿落点（上一轮，保留）

| # | 必修项 | 落点 | 实质变化 |
|---|---|---|---|
| 1 | 四类交互任务与逐能力因果对照 | §3.1 | 任务实例/成功/删失公式、分母、时限、预算、配对单位、treatment/control 完全输入集、hash-bound 脚本化操作员协议全部冻结 |
| 2 | 真值边界修复 | §2.1/§2.2 | `metrics.json` 从 VLM 输入**整体删除**；`platform_state` 改从帧元数据取（实测字段核对）；字段级来源表 + 构造性拒绝测试 |
| 3 | 版本化协议 | §2.1 | `DialogueContext` **取代** `RecoveryContext`（L3 未实现，无兼容负担）；context/action 冻结 schema_version/ID/源帧/双时钟时效/坐标系/provenance |
| 4 | 动作事务与安全边界 | §2.4（新） | 原子发布、ACK/拒绝、幂等、stale/乱序、重试/冷却、网关失联 fail-safe；`search_hint` 仅进 L2a 排序器；`reprompt` 必过三门 |
| 5 | BC-M34-1–10 逐条映射 | §4.2 | 每条 `KEEP`/`SUPERSEDE`/`REPLACE_WITH_*` 及理由；DETECT criterion 4 的新 owner/关闭门/证据归属精确化（§4.5） |
| 6 | spike 预注册 | §5 V1 | 帧清单来源/分层/去重/manifest+hash、教师版本、prompt hash、温度、解析、无效记账、Wilson 区间、70% 线全部在任何 API 调用前冻结 |
| 7 | 蒸馏防泄漏协议 | §5 V6 | 组隔离切分、离线过滤边界、保留比+绝对下限双门、失败三分类、配对 bootstrap |
| 8 | 新颖性降强度 | §1.3 | 检索表（日期/库/query/纳排）；"无人占据"→"冻结检索范围内未发现"；最近邻判断标注出处与核对边界 |
| 9 | brief/阶段边界闭合 | §4.6 + §8 | `PROJECT_BRIEF.md` 逐句迁移表（执行须用户授权协调批次）；Phase 1 出口/Phase 2 双机/论文出口写成带推荐的用户选项 |
| 10 | 设计同步与串行恢复表 | §4.7 | 设计 §1–§11+版本历史的逐节替换范围；spike → SCENE-007 → VLM-1 串行顺序与各自待授权门 |

**授权状态（逐字核对 `docs/authorizations.md`）**：2026-08-06
"好的，开始写决策吧"及同会话确认链是本 recharter 的**方向确认 +
起草授权，非最终变更**。本提案不携带任何执行授权：接受裁定、设计基线
修改、既有 work item 终态处置、实现代码、Edit Mode/Play、ID/配额消耗、
VLM API 预算消耗均待各自的门。

**与既有体系的关系**：本提案是**追加的决策层，不覆盖任何历史文件**。
被取代项按 SCENE-001→002 先例做显式 `SUPERSEDED` 标注并保留原文；
设计基线按版本化修订（v0.3.16 → v0.4 提请）。逐项处置清单见 §4.5。

---

## 1. 问题和研究价值

### 1.1 用户方向确认与本提案的由来

用户 2026-08-06 明确（账本当日 P1-VLM-SCOPE-001 条目，五条逐字）：
研究主菜是 **VLM 互动通信**，遮挡只是附加项。现行设计 v0.3.16 与该
意图存在三层相悖：

| 层 | 现行文本 | 与用户意图的冲突 |
|---|---|---|
| 主张层（设计 §1） | "VLM 是实现组件，不是贡献本体；VLM 是可选增强"；候选贡献钉在"云台/机身控制分配" | 用户的主菜被明文降格为配菜 |
| 架构层（设计 §5） | VLM 只在 L3 出现：事件触发、"只裁决 ReID margin 无法区分的语义歧义"、输出仅假设 JSON | 人机对话、事件汇报、语言改令在五接口中**不存在**；"操作员"概念全文档缺失 |
| 里程碑层（设计 §11 + `P1-M3M4-SCOPE-001`） | M3′（三策略）→ M4′ → M5 → M6（VLM 消融，可选）；BC-M34-9 又把场景适配性门插在 M3′ 前 | VLM 排最末且可选；SCENE-005/006/007 一个月的场景工程全部服务于三策略前置 |

### 1.2 旧主线的两项客观削弱（不依赖用户偏好）

1. **场景遮挡结构性稀少**：`P1-SCENE-006` batch 1c（复核 `PASS` 的
   候选级数据）在两族共 200 个观察几何上测得 `L_occ` 中位数
   0.0000/0.0185、最大 **0.1037**；finalist 的 0.506 总损失中 87% 是
   `L_point`（出视锥），真遮挡仅 0.065。三策略 Pareto 的"遮挡"故事
   在本资产上撑不住；`P1-M3M4-SCOPE-002`（负结果记录）与之互证。
2. **新颖性被占**：OA-VAT（arXiv 2604.21453，2026-04）已发表
   "occlusion-aware visual active tracking planning"（扩散规划避遮挡
   路径 + 遮挡恢复）。旧主线剩余新颖性只有系留约束 twist。

### 1.3 文献定位与缝隙（2026-08 检索）

| 最近邻 | 已做 | 与本提案缝隙的区分 |
|---|---|---|
| UAV-Track VLA（arXiv 2604.02241v1，2026-04；判断出处：v1 Abstract"static natural language instructions"与 Metrics 节 SR 定义的 15 帧容忍） | CARLA 892K 帧语言指定目标的端到端 embodied tracking | 静态指令、无对话交互；无专门重捕获机制 |
| **TrackVLA**（arXiv 2505.23189，CoRL 2025；round 3 新增） | 地面机器人 EVT：单指令识别（LLM 头）+ anchor 扩散轨迹，EVT-Bench 1.7M 样本，10 FPS，实景鲁棒 | 任务=地面跟人；语言轮次=**一次性指令**；动作空间=机身轨迹；恢复=隐式鲁棒性；指标=EVT SR。无操作员在环、无汇报、无蒸馏/边缘 |
| **TrackVLA++**（arXiv 2510.07134；round 3 新增） | +Polar-CoT 空间推理 + TIM 门控目标记忆，长遮挡下减缓丢失，EVT-Bench DT 提升 | 同上：仍一次性指令；恢复=**内部记忆机制**，非人机协同；无对话/汇报/边缘 |
| **VLM Can Be a Good Assistant**（arXiv 2505.20718；round 3 新增，**架构最近邻**） | 快慢双层：快速视觉策略正常跟踪，**失败时激活 VLM** 做 CoT 失败分析 + 结构化移动建议 + 记忆自反思自我改进；SR +21%–220% | 与本提案同构（快跟踪 + 事件触发 VLM），但为**纯自主自恢复**：无操作员在环、无人类提示进入恢复回路、无机→人汇报、地面 EVT、无蒸馏/边缘。本提案的 loss-assist 差异 = **人类语言提示进入恢复回路**并与其自主对应物（纯 L2a）配对归因 |
| **AVDN 家族**（survey 2604.07705 §III-E：Fan et al. [28] + [110]/[109]/[87]；round 3 更正） | **真实双向问答导航**：follower 需要时主动提问、commander 回答，多轮对话引导 UAV 到达静态目的地 | 对话是**为到达目的地的指令澄清问答**；无动态目标、无丢失恢复语义、无系统主动事件汇报、无感知重指定。缝隙不落在"双向对话"本身（AVDN 已有），落在**跟踪任务的三能力组合**（见下） |
| Chat with UAV（arXiv 2512.08145） | LLM 对话式无人机指挥、可用性评估 | 无与实时移动目标跟踪的闭环整合 |
| **VL-UniTrack**（arXiv 2605.04574） | UAV-地面双视角协同跟踪；98M、30 FPS | 三点撞名不撞实质：mutual distillation=训练期双视角互教非模型压缩；"语言"=4 个视角模板短语非操作员语言；无交互/边缘。其 limitations 自认需未来模型压缩——正面引证蒸馏轨动机 |
| **Visual Program Distillation**（arXiv 2312.03052；round 3 新增，verified-distillation 方法学先例） | 视觉程序**执行验证**过滤 CoT 轨迹后蒸馏进 VLM | "verify-then-distill" 思想已有先例——本提案**只**主张两点差异：验证器 = **仿真真值的机械比对**（非程序执行一致性）；蒸馏对象 = **监控交互动作枚举**（非通用 VQA 推理），面向边缘任务专用小模型 |
| UAV-VLA（HRI 2025） | 卫星图+文本 → 离线任务航线 | 非实时跟踪 |
| 边缘蒸馏系（GigaBrain-O-Small、LiteVLA-Edge、TinyVLA、Cosmos 3 Edge）+ survey 开放问题 #5 | manipulation VLA 蒸馏上 Jetson 成熟 | 监控/交互任务的蒸馏未见；部署为公认缺口 |

**与两个最近邻家族的任务级区分（缝隙表述据此收窄，round 3 更正）**

| 维度 | AVDN（双向问答导航） | VLM-Assistant（自主恢复跟踪） | 本提案 |
|---|---|---|---|
| 任务 | 静态目的地，到达即止 | 地面 EVT 跟随 | 系留空中**动态目标长航时监控** |
| 语言角色 | 到达目的地的澄清问答 | **无人类语言**（VLM 是内部推理器） | 任务管理三能力：**改令 / 机→人主动汇报 / 丢失协同提示** |
| 恢复机制 | 无此概念 | 自主自反思 | **操作员在环**提示 + 与自主对应物配对归因 |
| 归因评估 | 无 | 与基线策略比 SR | 同信息配对 + 确定性仿真 + 真值离线评分 |

**检索基线（round 1 必修 8：可复现边界）**

| 项 | 冻结值 |
|---|---|
| 检索日期 | 2026-08-06 |
| 库 | Web 检索（arXiv / ACM DL / Springer / MDPI 命中源） |
| Queries（逐字；round 3 增补两条防漏） | "vision language model UAV drone survey 2025 2026 LLM agent aerial"；"natural language guided UAV object tracking vision-language 2025 benchmark"；"VLM interactive human drone dialogue surveillance report events natural language 2025 2026"；"small vision language model distillation edge deployment Jetson robotics 2025 2026"；"active object tracking simulation UnrealCV distractor occlusion reinforcement learning evaluation"；**"TrackVLA embodied visual tracking vision-language-action EVT-Bench 2025 follow person"**；**"'VLM can be a good assistant' self-reflection tracking recovery embodied"** |
| 纳入（round 3 扩） | UAV/aerial × (语言交互 ∨ 语言引导跟踪 ∨ VLA) × 2024-2026；**地面 embodied visual tracking × (语言 ∨ VLM)**（TrackVLA 系教训：平台不同不构成排除理由）；边缘 VLM/VLA 蒸馏；**verify/filter-then-distill 方法学先例** |
| 排除 | 纯 VLN 方法学（AVDN 家族除外——对话范式最近邻）、纯 manipulation（仅作蒸馏工程参照）、无语言的 active tracking（仅作旧主线参照） |
| 最近邻判断出处 | UAV-Track VLA"静态指令/15 帧容忍/无专门重捕获"：arXiv 2604.02241v1 摘要与方法/指标节（经全文摘要式核对，未逐页精读——本表如实声明该边界）；Chat with UAV"无实时跟踪闭环"：arXiv 2512.08145 PDF 首节与评估节 |

**缝隙（round 3 最终收窄）**：本提案可主张的缝隙**不是**"双向对话"
（AVDN 已有真实问答）也**不是**"VLM 辅助跟踪恢复"（VLM-Assistant
已有自主版本），而是三者的**操作员在环组合**：动态目标持续跟踪任务
中的 **operator retask（语言改令过安全门）+ 机→人主动事件汇报 +
loss-assist（人类提示进入恢复回路并与自主对应物配对归因）**，及其
verified-distillation（仿真真值验证器 + 监控动作域）与边缘延伸。
在本表冻结的检索范围（含 round 3 新增 query）内，该组合未发现
占据者。两个最近邻家族反向佐证各半边的成立：AVDN 证明操作员多轮
对话范式被承认，VLM-Assistant 证明事件触发 VLM 层的架构有效。
接受后按月复查作为 §6.2 F1 的风险监控，不替代本表的接受时基线。

### 1.4 新核心研究问题（论文主张的表述，提请写入设计 §1）

> 在长航时系留监控任务中，如何让操作员与跟踪系统通过受控的双向语言
> 通道（改令 / 询问 / 主动汇报 / 丢失协同）交互，使**任务级跟踪效能**
> （正确身份覆盖率、删失恢复时间、错误重捕获率）在同等信息条件下
> 显著优于无语言基线；以及该交互能力可以多大程度蒸馏进小参数模型
> 并部署于边缘设备。

定位约束（继承并改写原 §1）：
- SOT / YOLOE / 具体 VLM 型号仍是实现组件；**贡献本体改为**：
  (a) 受控双向交互协议与其任务级归因评估方法（同信息对照 + 确定性
  仿真配对比较）；(b) verified distillation——用仿真真值自动过滤
  教师输出的蒸馏数据引擎；(c) 交互能力的可蒸馏性边界报告。
- 真值边界纪律不变：Unity 真值只进 `CoverageEvaluator`；VLM 的可见
  集（帧、聚合指标、路网）与不可见集（评估真值）在 §2 显式冻结。
- 同信息对照原则（原 L2b 条款）**升级为全部交互能力的归因总纪律**。

### 1.5 负结果与既有资产的吸收

- `P1-M3M4-SCOPE-002`（`CLOSED_NEGATIVE_RESULT_RECORD`）与
  SCENE-006 batch 1c 数据合并为"本资产遮挡结构性稀少"的证据，进入
  论文 motivation/limitations 叙事；遮挡在新主线重定位为
  **事件生成器**（§3.2 H5），不再是难度轴主张。
- 复用资产清单（均已复核/验证）：帧桥四通道与 `controller/` 闭环、
  YOLOE 三门重锚定管线（qual-3 `C_track|geom=0.920428`）、
  `geolocate.py` 像素→世界、`RecoveryContext` schema 思想、
  M4′ 指标定义（删失 MTTR / ID switch / 错误重捕获率）、
  SCENE-004 已资格化 benign 载体、确定性 trace 机制、
  `P1-YOLOE-001` 的导出限制情报（服务 M7′）。

## 2. 输入、输出与受影响接口

### 2.1 新增接口（冻结请求；round 1 必修 2 + 3 重写）

**`DialogueContext` 取代 `RecoveryContext`**（REPLACE：L3 从未实现，
无兼容负担；设计 §2 五接口清单同步替换，见 §4.7）。

**公共信封（context 与 action 共用；round 2 必修 1 时钟修正）**：
`schema_version`、唯一 ID（`context_id`/`action_id`）、`track_id`、
`source_frame_ids[]`、时效字段
`issued_at_{simulation_s, capture_monotonic_s}` 与
`expires_at_{simulation_s, capture_monotonic_s}` +
`capture_monotonic_clock_id`（必须逐字等于帧元数据的
`system-stopwatch/v1`）——**expiry/latency/age 判定只由单调钟承担**；
`*_unix_s` 仅作审计字段，不参与任何时效判定。fail-closed 规则：
时钟身份缺失或 ≠ `system-stopwatch/v1`、单调钟字段缺失、或
simulation 与 monotonic 两条时限的判定结果分歧 ⇒ 该 context/action
整体拒绝（`CLOCK_INVALID`），不得降级用 Unix 兜底。provenance
（`model_id`、精确 `model_version` 字符串、`system_prompt_sha256`、
`temperature`、输入帧清单哈希）不变。

**`DialogueContext` 字段级来源表（唯一 VLM 输入打包；round 1 必修 2
的修复——`metrics.json` 整体删除，不以任何摘要形式出现）**

| 字段 | 来源文件 / 发布者 | 为何不含真值 |
|---|---|---|
| `frames[]` | `runtime/frames/*.jpg` + 同名 `.json`（Unity `SensorFrameWriter`） | 传感器帧；既有硬边界保证真值不进传感器元数据 |
| `platform_state` | 帧元数据字段（实测核对）：`camera_position_world_m`、`camera_rotation_xyzw`、`camera_forward/right/up_world`、`intrinsics_px`、`gimbal_saturated`、`tether_saturated`、`simulation_time_s`、双时钟 | 平台自身状态（机载传感器可得）；**同名 `gimbal/tether_saturated` 一律取帧元数据，不取 `metrics.json`** |
| `tracker_state` | `tracking_observation.json` 与 `track_loop` 运行日志（controller 自产）：当前 OK/LOST、最近 N 条观测框、`track_id`、最近重锚定记录 | 追踪器输出是感知估计，非真值 |
| `command_history` | `gimbal_command.json` / `body_command.json`（controller 自产） | 自己发出的命令 |
| `event_queue[]` | controller 运行日志导出的事件：`LOST`、`GAP`、`REANCHOR_*`、观测框尺寸突变（阈值预注册） | 事件全部由感知侧信号定义，不读 evaluator |
| `dialogue_history[]` | 网关自产（操作员脚本消息 + 既往 action + ACK 结果） | — |
| `worldmodel_local?`（二期，默认缺省） | 离线构建路网工件，逐字继承 BC-M34-6 provenance 纪律（§4.2） | 静态场景知识，非逐帧真值 |

**`VlmAction`（VLM 唯一输出，动作枚举；自由文本仅限话语字段）**

| 动作 | 专有字段（公共信封之外） | 语义 |
|---|---|---|
| `answer` | `text` | 回答操作员询问 |
| `report` | `event_ref`（绑定 `event_queue` 条目 ID）、`text` | 主动事件汇报 |
| `reprompt` | `bbox_norm`（**normalized top-left `xywh`、image-clipped，逐字继承既有 tracker 合同语义**）、`source_frame_id`（框所在帧，必须 ∈ `source_frame_ids`）、`phrase`（仅存档） | 目标重指定：框走既有三门重锚定管线 |
| `search_hint` | `region_xz`（Unity 世界坐标 XZ 平面，米）、`radius_m`、`confidence ∈ [0,1]`、`valid_until_{simulation_s, capture_monotonic_s}`（单调钟权威，与信封同规则参与 L2a 消费时的过期判定） | 丢失协同提示：仅供 L2a 扫描排序消费 |

- 新桥文件 `runtime/vlm_command.json` 与回执
  `runtime/vlm_command_ack.json`（均按 `AtomicFile` 原子发布），与
  既有四通道并列；`tracking_observation.json`、`gimbal_command.json`、
  `body_command.json`、`frames/latest.json`、`metrics.json` **零改动**。

### 2.2 真值边界（硬约束；round 1 必修 2 的机械隔离）

- **VLM 可见集** = §2.1 来源表的字段，逐项绑定来源文件。
- **禁读清单（机械强制）**：`runtime/metrics.json`（evaluator 产物，
  `aggregate/current` 承载 `C_geom`/`C_track` 真值归因）、
  `evaluation_truth.jsonl`、`runtime/p1-scene-00[56]/**`、任何
  qual/scouting truth sidecar、`runtime/test-results/**`。
- `evaluation_truth.jsonl` 仅允许**离线** spike scorer 与
  distillation verifier 读取（两者不在任何在线回路，产物只进证据）。
- 网关进程启动时装载输入 allowlist（路径模式 + 哈希），实际打开的
  每个路径写入 run 工件；**构造性拒绝测试**：向网关配置注入
  `metrics.json` 或 truth 路径必须在构造期抛错。违反即
  `INTERACTION_CONTAMINATED_BY_TRUTH`，该 run 全部指标作废。

### 2.3 架构定型（用户 2026-08-06 确认第 3 条）

```
操作员语言 → VLM（看 DialogueContext 帧）grounding → bbox 视觉 prompt
→ 三门重锚定管线（几何/身份/时间）→ NanoTrack 每帧跟踪 → 5 Hz 桥
```

**YOLOE 文本 prompt 线废弃**：文本嵌入锚定于真实照片统计，
`TargetVisualFactory` 方块车存在域差距（旁证：SCENE-003 嵌入通道
DINOv2 cosine median 0.398、1/27 过阈）；框（视觉 prompt）是唯一喂给
感知栈的形式，框的来源由人工框选扩展为 VLM grounding。

### 2.4 动作事务与安全边界（round 2 必修 1/2/3 重写）

#### 2.4a 时序与 replay 合同（继承 DETECT 机制，扩参数待校准授权）

**机制完整继承 `reanchor_runtime` 的四件套**——`reprompt.bbox_norm`
在其 `source_frame_id` 帧上初始化新 tracker 实例，从帧历史缓冲按
`frame_id` **顺序 replay/catch-up** 到当前头帧，以源帧年龄、缓冲
完整性、catch-up 收敛与**原子头相等**决定接受；收敛失败 ⇒ 放弃
重锚定、现役 tracker 不动。**round 1 的"源帧早于水位即
`STALE_FRAME`"规则删除**——它会拒绝一切云 API 返回（源帧必然
落后于 live head），并把上述已接受机制短路。

**协商/出框解耦**：多轮协商（对话）不占源帧年龄预算；网关决定出框
时**必须以请求时刻最新可得帧重新 grounding**，`source_frame_id` =
该帧。因此年龄门只需覆盖"最后一跳 grounding 调用 + 解析 + 落盘"，
不随对话时长增长。

**参数（用户 2026-08-06 方向确认：排除 2 s 硬门，扩参数待实验
校准——账本当日条目，含 Gemini Flash 好网络 1–2 s、协商更长的
实测依据）**：

| 参数 | DETECT 原组（零改动） | `vlm_reprompt.*` 新组（合同上界，正式值待校准+授权） |
|---|---|---|
| `maximum_source_age_s` | `2.0` | **≤ 15.0**（上界；正式值 = 延迟校准 p95 × 2 上取整） |
| `frame_buffer_s` | `6.0` | **≤ 20.0**（内存代价 ~100 帧 × ~50 KB ≈ 5 MB，可忽略） |
| `catchup_timeout_s` | `2.0` | **≤ 4.0** |

- **时序参数冻结门（round 3 必修 1：独立、失败封闭，实现者零裁量）**
  1. **输入**：spike（§5 V1）逐调用的端到端延迟样本（请求发出 →
     解析完成，单调钟）；**有效样本 = 成功解析的单轮 grounding
     调用，数量 ≥ 20**，失败调用单列报告不入分布；协商负载样本
     单列披露（不进 age 导出——age 只覆盖最后一跳，§2.4a 解耦）。
     全部样本（含协商 ≤ 6 次）**计入 Q1 的 ≤ 40 次总上限**。
  2. **导出公式（全部预注册，`ceil_0.5`/`ceil_1` = 向上取整到
     0.5 s / 1 s）**：
     `age_cand = ceil_0.5(2 × p95_single)`，p95 按 type-7 分位
     （仓库既有惯例）；
     `catchup_cand = ceil_0.5(4 × age_cand × 5 帧/s ×
     0.003332854 s)`——单帧重放耗时取 `P1-TRACK-002` 复核档案的
     p95 update `3.332854 ms` 为预注册常量，4 倍余量覆盖头帧
     推进循环；
     `buffer_cand = ceil_1(age_cand + catchup_cand + 2 s)`。
  3. **可行性判定**：`age_cand ≤ 15` 且 `catchup_cand ≤ 4` 且
     `buffer_cand ≤ 20` 且有效样本 ≥ 20，全部成立才可行；**任一
     不成立 ⇒ `VLM_REPROMPT_TIMING_INFEASIBLE`，返回构思角色**
     （换教师/压缩负载/改架构后重走 spike），**禁止截断到上界**、
     禁止减小倍数、禁止换分位。
  4. **停门与授权**：可行时三值以 **amendment 形式经 Acceptance
     裁定 + 用户逐字授权**后方可写入配置；该停门独立于 VLM-1
     （§4.7 序 2.5）。spike 本身零 Unity、不启用在线
     `vlm_reprompt` 通道，不受此门阻塞。
- **安全归因**：更长 replay 扩大"旧框重锚定到已换位目标"的窗口——
  身份门（外观嵌入）与运动门照常把关，replay 中 tracker 失败即
  放弃；VLM-1 停点须报告扩参数下的 replay 收敛率与错误重锚定率
  （L2 验证，见 §4.7 序 4）。
- `STALE` 语义重定义：仅指**超过 `maximum_source_age_s`**（单调钟），
  由 replay 入口按 DETECT 同一判据执行。

#### 2.4b 幂等与回执绑定（round 3 必修 2 重写：完整恢复状态机）

- **`schema_version` 精确值**：context / action / ACK 三类载荷共用
  `"vlm-interaction/v1"`。
- **canonical payload 字节**（沿用 SCENE-006 BC-P2-10 strict
  RFC 8259 先例）：UTF-8、对象键字典序升序、无空白分隔
  （即 `json.dumps(obj, sort_keys=True, separators=(",", ":"),
  ensure_ascii=False)` 的字节序列，浮点用最短往返表示）；
  `canonical_payload_sha256` 对该字节序列计算。
- **缓存键逐字三元组** `(action_id, context_id,
  canonical_payload_sha256)`：三者**任一**不一致的重发 ⇒
  `ID_CONFLICT` fail-closed（双方 payload 存档）；三者全同 ⇒
  **返回缓存的既有终态 ACK**、绝不重复生效。
- **账本与状态机**（消费者侧 append-only jsonl，单行 append 原子）：
  `PREPARED`（收到并验证通过，写 intent 行）→ **生效见证**（动作
  真正生效的那一步在 controller 运行日志留带 `action_id` 的条目：
  `reprompt` = 原子头相等替换时的 `REANCHOR` 事件行；
  `search_hint` = L2a 排序器的 `HINT_CONSUMED` 事件行——见证与
  生效在同一进程同一事件流写入）→ `ACKED`（终态行 + 发布
  `vlm_command_ack.json`）。
- **崩溃恢复算法**（重启时对每个 `PREPARED` 而未 `ACKED` 的
  action 执行）：查运行日志有无该 `action_id` 的生效见证——
  **有** ⇒ 已生效，补写 `ACKED(accepted)`，后续重放取回该终态；
  **无** ⇒ 未生效，写 `ACKED(rejected, CRASH_BEFORE_APPLY)`。
  由此每条路径下动作**至多生效一次**且重发总能取回原终态。
- **首次 run 与损坏账本分离**：消费者启动时若账本文件不存在——
  且 run 内无任何既往 VLM 痕迹（无 `vlm_command.json`、运行日志无
  action 条目）⇒ 合法创建带 header（`schema_version` + `run_id` +
  创建时刻）的空账本；**有**痕迹却无账本、或账本解析失败 ⇒
  `ACK_LEDGER_INVALID`，拒绝一切重放型请求直至人工处置。
- **in-flight 解除与迟到 ACK**：收到终态 ACK，或 `expires_at` 过后
  `ack_grace_s = 5`（单调钟）仍无 ACK ⇒ 网关记 `EXPIRED_UNACKED`
  解除占用，该 `action_id` 永久作废不复用。此后迟到 ACK 到达 ⇒
  **消费者账本是动作终态权威**：网关补记 `LATE_ACK_RECORDED`
  审计行（含权威终态），但**任务级记账维持超时失败**（操作员视角
  的任务时限已过）；动作终态与任务记账两者并列如实报告，不互改。

#### 2.4c 其余事务规则（round 1 版本保留）

| 语义 | 冻结规则 |
|---|---|
| 原子发布 | `vlm_command.json` / `vlm_command_ack.json` 均走既有 `AtomicFile` 写入-改名模式 |
| 在飞上限 | 同时至多 **1** 条未回执 action |
| 拒绝枚举 | `EXPIRED` / `STALE`（超龄，2.4a 语义）/ `ID_CONFLICT` / `GATE_FAILED` / `MALFORMED` / `CLOCK_INVALID` / `CONSUMER_UNAVAILABLE` / `ACK_LEDGER_INVALID` |
| 重试/冷却 | 每任务实例 VLM 调用重试上限 **1**，拒绝后冷却 `10 s`（单调钟）；超限按失败/删失记账 |
| 网关失联 fail-safe | VLM 是增强层不是安全路径：网关崩溃/超时/无效输出时，跟踪栈按无-VLM 基线继续运行 |
| `search_hint` 边界 | 仅进入 L2a 扫描候选**排序器**；不产生任何机身/云台命令；未来机身规划命令须先过独立契约停点（§4.2 BC-M34-7 处置） |
| `reprompt` 边界 | 必须逐门通过 DETECT 三门；任一门失败 ⇒ 现役 tracker 不变 + `GATE_FAILED` 回执入档 |
| 无效输出记账 | 解析失败/超 schema/超时 = 调用失败，计入预算与失败统计 |

## 3. 算法或行为假设（可证伪）

### 3.1 四类交互任务与逐能力因果对照（round 1 必修 1，运行前冻结）

**操作员消息协议（四类通用，硬性）**：所有"操作员"消息由**采集前
冻结、SHA-256 绑定的脚本**按预注册触发条件生成（触发条件只引用
controller 侧信号：仿真时刻、`event_queue` 条目、tracker 状态）。
脚本禁读任何 evaluator 真值；消息文本与触发时刻在 run 前全部确定或
由冻结规则确定性导出；**禁止**人工临场输入或按结果事后补选消息。
treatment 与 control 在**同一 scenario/seed/事件剂量**下各跑一次，
构成配对单位。

| 能力 | 任务实例（脚本化） | treatment 输入 | control 输入（同信息非学习） | 成功 / 失败 / 删失公式 | 分母与配对单位 | 时限与预算 |
|---|---|---|---|---|---|---|
| **改令 retask** | 预注册时刻 `t_k` 注入"改跟 <属性短语>"（目标车与干扰车外观组预先定义） | `DialogueContext` + 自然语言消息；VLM grounding → `reprompt` | 同一 `DialogueContext`（减 dialogue）+ 同语义结构化属性命令 + **非学习颜色分割选框器**：在同一帧上按该属性的冻结 HSV 带做阈值分割 → 连通域 → 最大块外接框（经典 CV，零学习、零真值），走同一三门 | 成功=三门通过后 `t_k+Δ` 窗口内新目标连续跟踪 ≥ `T_hold`（无 LOST/ID switch，按 tracker 状态判）；失败=门拒/跟错/超时；无删失 | 每任务实例一对；每会话 ≥ 4 实例 | 任务时限 `10 s`（单调钟）；VLM 调用 ≤ 2 次/实例 |
| **询问 query** | 预注册时刻注入状态问句（模板池 ≥ 6 类：目标在哪/状态/距离/朝向/最近事件/平台状态） | `DialogueContext` + 问句；VLM `answer` | 模板化读出器：规则拼接 §2.1 可见字段生成答案（无学习） | 由**离线 scorer**（允许读真值）按下方评分卡逐项判对错；成功=该问句类的关键事实项全对；无删失 | 每问句一对；每会话 ≥ 6 句 | `10 s`；≤ 1 次/句 |
| **主动汇报 report** | 不注入消息；系统对事件自主汇报 | `DialogueContext` 事件流；VLM `report` | 规则告警器：`LOST` 超时 / 框尺寸突变 / `REANCHOR_*` 直接模板化告警 | 以离线事件真值集为准的**事件级 precision / recall / 汇报延迟**；漏报=FN，误报=FP | 每事件一条记录；两组共享同一事件真值集 | 汇报延迟按 `report.issued_at_capture_monotonic_s − 事件真值时刻` |
| **丢失协同 loss-assist** | 丢失事件后 `t_loss+τ` 注入提示，内容由冻结模板从 **controller 侧最后已知信息**生成（如"目标最后向 {last_heading_8way} 行驶"，heading 取 tracker 历史，非真值） | `DialogueContext` + 提示；VLM `search_hint` → L2a 排序 | 同一丢失事件、无提示的纯 L2a 几何扫描 | 每事件：重捕获时间（超 `T_censor` 记删失）、重捕获成功率、错误重捕获率（逐字继承 M4′ 定义） | 每丢失事件一对 | `search_hint` ≤ 2 条/事件 |

**数值合同（round 2 必修 4：全部赋值，采集前不可再改）**

| 量 | 冻结值 | 语义 |
|---|---|---|
| `Δ`（改令评估窗） | `20 s` | `t_k` 起算，窗内完成三门+重放才计成功 |
| `T_hold` | `10 s` | 新目标连续跟踪时长（tracker 无 LOST、无 ID switch） |
| `τ`（提示注入延迟） | `5 s` | 丢失确认后到脚本注入提示 |
| `T_censor` | `60 s` | 重捕获删失线 |
| LOST 事件定义 | tracker 连续 `LOST ≥ 2 s`（10 帧 @5 Hz） | controller 侧信号，双组一致 |
| 框尺寸突变 | 相邻观测 `min(w,h)` 变化 > `50%` | report 触发源之一 |
| query 评分卡（round 3 必修 3：逐题型绑定，无跨题型 `OR`） | `POS_COORD` 题：`facts.position_xz` 世界 XZ 误差 ≤ `5 m`；`POS_BEARING` 题：`facts.bearing_8way` 八分区精确；`DIST` 题：`facts.distance_m` ±`20%`；`HEADING` 题：`facts.heading_8way` 八分区精确；`STATE` 题：`facts.tracker_state` 枚举精确；`EVENT` 题：`facts.last_event.type` 精确 + `t` ±`2 s`；`PLATFORM` 题：布尔标志精确 + `altitude_m` ±`1 m`。题型由问句模板池预先绑定（七类模板各自属于唯一题型） | 离线 scorer 按题型判定 |
| `answer.facts` 结构化字段（round 3 必修 3） | `answer` 动作增加冻结 schema 的 `facts` 对象（按题型：`position_xz` / `bearing_8way` / `distance_m` / `heading_8way` / `tracker_state` / `last_event{type,t}` / `platform{gimbal_saturated,tether_saturated,altitude_m}`）；**`text` 仅作展示、不参与评分**；`facts` 缺失或不可解析 = 该句失败 | 机器可评分的唯一依据 |
| report 事件 ontology 与匹配规则（round 3 必修 3） | 真值事件类型枚举 `{OCCLUSION_LOSS, DISTRACTOR_CONFUSION, TARGET_STOPPED, REANCHOR_EXECUTED}`（由事件生成器参数与离线真值导出）；匹配 = 类型一致 + `report.issued_at` 与事件真值时刻差 ∈ `[−1, +5] s`，贪心按时间最近**一对一**；同一事件多报 ⇒ 首条 TP、其余 FP；超窗迟报 ⇒ 事件计 FN 且该报计 FP；无匹配事件的报 ⇒ FP；无报的事件 ⇒ FN；汇报延迟只在 TP 上统计 | 双组共享同一真值事件集 |
| 颜色对照器资格门（round 3 必修 3：防看结果调参） | 标定集 = 专用 `(scenario_id, seed)` 组，与全部正式 paired runs **组隔离**（§5 V6 切分原则）；HSV 带与资格结论（标定集上选框正确率 ≥ `90%`）在**任何正式 paired run 开始前**冻结并哈希；资格不过 ⇒ 属性档平权主张阻断（仅报 oracle 上界对比），**不得**用正式结果回炉调 HSV | H4 证伪分支的执行细则 |
| paired schedule | 每会话固定 `(scenario_id, seed, 事件时刻表)` 预注册；treatment/control 同 seed 各跑一次，run 顺序交替 | 配对单位见上表 |

**任务分档与主张分层（round 2 必修 4）**：
- **属性档**（颜色/亮度可分割的指定，如"白色轿车"）：主同信息对照 =
  颜色分割选框器；这是论文的**平权比较主张**所在。
- **语义档**（关系/上下文指定，如"排在红车后面那辆"）：不存在同信息
  非学习对照，**只**与 oracle-UI 上界（脚本注入真值框，分栏披露）
  比较，主张降级为"对上界的接近度"，不得称胜过基线。
- **主张分层**：retask / loss-assist 支撑**跟踪效能**主张
  （MTTR/成功率/错误率）；query / report 支撑**通信正确性**主张
  （评分卡/precision/recall/延迟）；本 Phase 无真人被试，
  **不得外推任何 HRI usability 结论**。

- **oracle-hint 上界轴（显式标注，不进主张）**：丢失协同另设一条
  读真值方向的提示变体，仅作为信息上界披露，产物与主实验分栏。
- 统计：配对差 + bootstrap 95% 区间；确定性场景逐 run 报告并以
  中位数描述（继承 BC-M34-8 原则，§4.2）。

### 3.2 假设（可证伪）

- **H1（VLM grounding 在仿真域可用）**：现代 VLM 在系统提示说明
  仿真域后能输出可用目标框。本会话对归档帧
  `frame_0000005200/5203.jpg` 的双帧读图（正确区分移动红色目标车与
  静态红色立柱）**仅为方向性观察，不构成证据**（round 1 必修 6）；
  证据由 §5 V1 预注册 spike 产生。**证伪判据**：spike 总体
  IoU@0.5 成功率 < 70% ⇒ 回构思角色重选教师模型或改采样策略。
- **H2（域差距使文本 prompt 不可靠）**：作为 H1 的对照在 spike 中
  顺带测量：YOLOE 文本 prompt 对同帧集的召回显著低于 VLM grounding。
  证伪不影响主线（仅恢复一条备选通道）。
- **H3（受限动作枚举可蒸馏）**：固定场景类型 + 动作枚举 + 结构化
  输出的受限域中，≤3B 学生可保留教师大部分任务成功率。
  **证伪判据**：VLM-3 出口，保留比与逐能力绝对成功率双门不达标
  （两组阈值**唯一归 VLM-3 独立提案的采集前停点冻结**，本 recharter
  不给数值）⇒ 如实报告可蒸馏性边界，M7′ 降级为仅感知栈部署。
- **H4（同信息对照可实施）**：四类能力的 treatment/control 完全输入
  集合已在 §3.1 表逐列冻结；改令主对照为**非学习颜色分割选框器**
  （同帧、同属性语义、零真值、零学习），oracle-UI 注入框改列上界
  分栏（round 2 必修 4）；语义档任务无平权对照、主张按 §3.1 分层
  降级。**证伪判据**：属性档中颜色分割器在标定集上自身可靠性
  < 90% ⇒ 对照器回炉重标定（不得因此改用真值框）；任何能力找不到
  满足列定义的对照 ⇒ 该能力退出平权主张（V3）。
- **H5（事件生成器产生足够删失事件）**：动态遮挡车（大型车辆与目标
  交汇）+ 干扰车（相似外观并行）能按参数化剂量制造丢失/混淆事件。
  **证伪判据**：预注册剂量下每会话删失事件数低于统计力所需下限
  （VLM-2 预注册）⇒ 调整剂量参数并重新冻结，不得看结果后调。

## 4. 与 v0.3.16 设计的兼容性（修订请求清单）

### 4.1 提请改写（接受后由接受角色执行，版本升 v0.4）

1. 设计 §1：核心研究问题按 §1.4 改写；"VLM 是可选增强"降格条款
   删除，替换为三项新贡献本体与定位约束。
2. 设计 §2：五接口增补 `DialogueContext`/`VlmAction`（§2.1）。
3. 设计 §5：L3 从"仅裁决 ReID 歧义"扩为**双向交互层**（改令/询问/
   汇报/丢失协同）；丢失阶梯 L0–L4 结构保留，L2a/L2b 成为
   `search_hint` 的消费方与对照。
4. 设计 §11：里程碑重排——

| 新里程碑 | 内容 | 出口 |
|---|---|---|
| VLM-1 | 网关 + grounding spike 量化 + 改令/询问/汇报闭环（云 API，SCENE-004） | 闭环 demo + spike 报告 |
| VLM-2 | 事件生成器（遮挡车/干扰车参数化）+ 交互任务集与对照冻结 + 同信息配对评估 | **论文 1 实验完整** |
| VLM-3 | verified distillation 数据引擎 + ≤3B 学生训练 + 桌面精度-延迟评估 | 保留比报告 |
| M7′ | Orin Nano 上板（量化/TensorRT，复用 §8 实测协议） | **论文 2 实验完整** |

   M5 的场景随机化/消融义务并入 VLM-2/3 的实验协议；M6 撤销
   （VLM 不再是可选消融而是主线）；M7 更名 M7′、蒸馏 VLM 加入其
   部署对象。
5. 设计 §6/§7：指标体系增加事件级三指标（删失 MTTR、错误重捕获率、
   ID switch，定义逐字继承 M4′）与交互任务级成功率；评测协议增加
   同信息配对比较协议。

### 4.2 BC-M34-1–10 逐条处置（round 1 必修 5：全部机械可核对）

| 条款 | 处置 | 理由 / 替换条款 |
|---|---|---|
| BC-M34-1（M3′ 精确边界） | `SUPERSEDE` | 三策略主线终止。世界系估计器/L1 若被未来批次复用，须以新提案重新裁定，不默认继承 |
| BC-M34-2（M4′ 精确边界） | `REPLACE_WITH_BC-VLM-2` | L2a/L2b/L4 与仲裁的实现归 VLM-2 事件实验语境；原条款中"L2b 与 VLM 消费同一版本同一 hash 的 `WorldModelHandle`，不得以信息不对称制造收益"**逐字保留**并升级为 §1.4 的全能力同信息总纪律 |
| BC-M34-3（阈值式对照） | `SUPERSEDE` | 对照对象（三策略）消失；其"触发量取自 `PlatformState` 发布值、绝不取 evaluator 真值"的原则已被 §2.1/§2.2 的来源表继承 |
| BC-M34-4（场景适配性三肢） | `SUPERSEDE` | 服务对象不再是主线；SCENE-006 候选数据与 SCOPE-002 负结果作为其历史证据保留可引用 |
| BC-M34-5（SCENE-005 独立裁定；M1 单独授权） | 前半 `SUPERSEDE`、后半 `KEEP` | SCENE-005 处置随本 recharter 待裁；**"M1 最终关闭需要单独用户授权与接受归因"逐字保留**（M1 证据路径改道见 §4.5） |
| BC-M34-6（WorldModel 非真值 provenance 硬门） | `KEEP` | `DialogueContext.worldmodel_local` 启用前必须先冻结物料来源、离线构建、schema/hash、版本、坐标系、查询语义与信息公平规则，逐字继承 |
| BC-M34-7（规划器命令契约停点） | `REPLACE_WITH_BC-VLM-7` | 版本化命令契约义务转移到 `VlmAction`/`vlm_command` 事务协议（§2.1/§2.4 即其实例化：ID、issue/valid-until、ACK/拒绝、stale/重复/乱序、fail-safe 要素一一对应），**同样是实现前独立停点**（§4.7 序 3）。未来恢复机身规划命令时，原条款语义按新提案重启，不视为已豁免 |
| BC-M34-8（统计与超参冻结） | `REPLACE_WITH_BC-VLM-8` | "确定性场景逐 run 报告并以中位数描述、随机种子 CI 义务留给全量评测"逐字保留；"suitability 报告后冻结"改为"任务集/对照/事件剂量（V3/V4）冻结后、任何配对测量前冻结"；反事后选择纪律逐字保留 |
| BC-M34-9（顺序门） | `SUPERSEDE` | 替换为 §4.7 串行恢复表 |
| BC-M34-10（工作流映射） | `KEEP` | workflow §4.3.1 通用 M3/M4 强制停点的映射对象由接受角色在 round 2 裁定中改挂 VLM-2/VLM-3；workflow 文件本身仍不改，同条款的协调批次边界原文有效 |

### 4.3 保留不变的纪律

真值边界、预注册/反调参、删失如实报告、停点/独立复核/Unity 验证
三门、COORD-003 单线、COORD-005 诊断通道与人眼保真检查、账本制度。

### 4.4 可比性披露

M2 时代基线（RATE-001/002 曲线）与新主线指标不可比（指标对象不同：
帧级覆盖率 vs 事件级交互效能）；旧数据保留为旧主张的历史证据，
论文引用时按 negative-result/motivation 处理。

### 4.5 既有 work item 逐项处置请求（终态由接受角色裁定）

| Work item | 请求处置 | 理由 |
|---|---|---|
| `P1-M3M4-SCOPE-001` | `SUPERSEDED_BY_P1-VLM-SCOPE-001`（原文保留） | charter 被本 recharter 取代 |
| `P1-SCENE-005` | `CLOSED_SUPERSEDED_BY_RECHARTER`；四轮审查与 `U_occ` 设计留档 | BC-M34-4 废止后失去服务对象 |
| `P1-SCENE-007` | **保留并按原计划完成**（rev 2 → 裁定 → 双批次双复核 → GO） | 车穿锚点是与方向无关的合法性缺陷；主环线仍是长航时叙事场景 |
| `P1-SCENE-006` / `P1-M3M4-SCOPE-002` | 不动（已关闭） | 其数据作为 §1.2 证据被引用 |
| `P1-DETECT-001` criterion 4 | **行为闭环门（round 2 必修 5 重写）**——新 owner：VLM-2 事件实验批次。关闭门全部同时成立：(a) **成功 REANCHOR 闭环 ≥ 10 次**（每次=三门通过 + 完整 source-frame replay/catch-up 收敛 + 原子头相等替换生效，只计成功、**十次全拒不得关闭**）；(b) 其中 ≥ 1 次经 DISAGREE 路径触发的成功重播种；(c) 承载会话时长 ≥ 150 s；(d) 全程 `incorrect/matched < 0.5`；(e) `LOST` 只由 controller 信号触发、evaluator truth 只做离线评分；(f) 批次自身实现证据 + 独立复核 + 用户 Unity 验证三门齐。证据归属：VLM-2 run 工件为权威，`P1-DETECT-001` 行引用之并由接受角色关闭归因 | 原语境（困难场景资格）已被取代，但 reseed 行为验证义务不消失且不降格 |
| M1 登记行 | 退出判据不变（参数化 + `C_geom` 显著 < 100%）；缺口证据改由 VLM-2 事件场景的 evaluator 记录产出（遮挡车交汇会话的 `C_geom` 天然 < 100%）；**关闭仍需单独用户授权与接受归因（BC-M34-5 KEEP 部分）** | `U_occ` 扫描不再执行 |
| M0 / TRACK-001/002 / YOLOE-001 / TEST-001 / SCENE-002/004 / RATE-001/002/003 | 零改动 | 基础设施与历史证据 |

### 4.6 `PROJECT_BRIEF.md` 逐句迁移表（round 1 必修 9；执行须用户授权的协调批次——brief 不在任何角色写入白名单内）

| brief 现行句（行号） | 冲突判定 | 迁移文本（草案，随 round 2 接受定稿） |
|---|---|---|
| L10-13 "The primary outcome is correct-identity tracking coverage (`C_track`)…" | 部分兼容 | 增补一句：Phase 1 primary outcome 扩展为事件级交互效能（删失 MTTR、错误重捕获率、任务成功率）与 `C_track` 并列；真值 evaluator-only 句原样保留 |
| L37-38 "SOT, YOLOE, ReID, search, planning, and **optional VLM** are staged components" | **冲突** | 改为 "The VLM interaction layer is the primary research component; SOT, YOLOE, ReID, search and planning remain staged perception/control components" |
| L44-45 "Phase 2 extends … two-drone handoff **and a distilled policy** for an 8GB Jetson Orin Nano" | **冲突**（蒸馏移入 Phase 1.5 / VLM-3） | 按用户 Q-A/Q-B 选择改写：蒸馏轨移出 Phase 2；双机接力按 Q-B 保留为其后愿景或删除 |
| L46-47 "Hardware deployment is a later M7 track that starts only when the user explicitly activates it" | 兼容 | `KEEP` 语义，M7→M7′、部署对象增加蒸馏学生模型 |
| L48-49 "Fable proposes, Codex reviews and implements, Sonnet independently verifies…" | 既有偏差（COORD-002 已把角色与模型名脱钩，与本 recharter 无关） | 顺带更正为角色名表述；标注给同一协调批次，不混入研究范围变更 |

### 4.7 设计同步与串行恢复表（round 1 必修 10）

**设计基线逐节替换范围（round 2 接受后由接受角色执行，v0.3.16 → v0.4）**

| 设计节 | 替换范围 |
|---|---|
| §1 | 核心研究问题 blockquote 与四条定位约束全文替换为 §1.4 文本 |
| §2 | 接口清单：`RecoveryContext` 行替换为 `DialogueContext`；新增 `VlmAction` 与两个桥文件；其余四接口原文不动 |
| §5 | 丢失阶梯表 L3 行改"双向交互层（改令/询问/汇报/丢失协同，§3.1 语义）"；"v0.3 关键调整"1–4 条对应更新（同信息升级为总纪律、`search_hint` 消费边界） |
| §6 | 新增事件级指标定义（删失 MTTR / 错误重捕获率 / ID switch 逐字继承原 M4′ 行 + 四类任务成功率公式引用 §3.1 表） |
| §7 | 新增同信息配对比较协议（配对单位、bootstrap、oracle-hint 分栏） |
| §8 | M7′ 部署对象增加蒸馏学生模型；实测协议框架原文保留 |
| §10 | R5 改写为交互归因风险；新增 R6（新颖性窗口）、R7（训练算力） |
| §11 | 里程碑表：M0–M2 行原文不动；M3′/M4′/M5/M6/M7 行替换为 §4.1 的 VLM-1/2/3 + M7′ 表 |
| 版本历史 | 新增 v0.4 条目（引用本 ID 与账本授权） |

**串行恢复顺序（COORD-003 单线，每步完成才开下一步）**

| 序 | 步骤 | 仍待的用户门 |
|---|---|---|
| 1 | recharter 接受（最终轮）+ 设计/brief 同步（协调批次） | brief 修改授权；Q-A/B/C 选择 |
| 2 | grounding spike（纯离线，V1 协议；不启用在线 `vlm_reprompt` 通道） | Q1 API 预算逐字授权 |
| 2.5 | **时序三值冻结门**：按 §2.4a 公式导出候选 → amendment 经 Acceptance 裁定；不可行 ⇒ `VLM_REPROMPT_TIMING_INFEASIBLE` 返回构思 | 三值的用户逐字授权 |
| 3 | `P1-SCENE-007` 恢复：revision 2 → 裁定 → 批次 1 → Review → 用户 GO → 批次 2 → Review → 非 Play 目检 | `2.11 m` 包络授权 + 锚点 GO |
| 4 | VLM-1：网关 + `DialogueContext`/事务实现（含 debug 双件套与 §7 清单）→ 停点 → 独立复核（含扩参数下 replay 收敛率/错误重锚定率的 L2 验证报告）→ 闭环 demo | **VLM-1 API 预算另行逐字授权**（Q1 只覆盖 spike ≤ 40 次）；前置 = 序 2.5 三值已授权 |
| 5 | VLM-2：事件生成器 + 任务集采集与配对评估 | 事件剂量冻结确认；Unity 采集 GO |
| 6 | VLM-3 / M7′ | Q3 算力；M7′ 显式启动 |

序 2 先于序 3 的理由：spike 是整条主线 go/no-go 信息量最大且零 Unity
成本的一步；若 H1 证伪，序 3 之后的投入方向都要重议。`P1-SCENE-005`
在序 1 随 §4.5 请求关闭；若本 recharter 被拒，SCENE-005/007 按
round 4/round 2 的原退修要求恢复，本表作废。

## 5. 可证伪的验收条件（本 recharter 被接受的判据）

1. **V1 grounding spike（round 1 必修 6：全要素在任何 API 调用前
   冻结）**：
   - **帧清单**：来源目录冻结为 `runtime/runs/p1-track-{follow,nadir,
     occlusion}`、`runtime/rate-study` 归档 `rs2-*`、qual-3 会话、
     `runtime/p1-detect-scouting`、`runtime/p1-scene-004-scouting`；
     分层 = 斜距三带（<30 / 30–50 / >50 m）× 状态（正常 / 遮挡中或
     解除后 / 干扰共存）× 场景（主环线 / SCENE-004）；总数 ≥ 30、
     每 run ≤ 8 帧、同 run 相邻采样间隔 ≥ 2 s、`frame_id` 全局唯一；
     清单（路径 + SHA-256 + 分层标签）作为 immutable manifest 先行
     提交，manifest 提交后一字节不得改。
   - **教师与调用参数（round 2 必修 6）**：教师 =
     `TEACHER_MODEL_ID_TBD_Q1`——Q1 授权时绑定**供应商当时公开、
     本账户实际可调用的版本化 API model ID 及其价格**，不预注册
     未核实别名；调用时记录 API 返回的精确 model version 字符串。
     system prompt 全文冻结入 manifest（含"仿真域方块车"说明）并记
     SHA-256；`temperature = 0`；图像按原始 640×480 JPEG 直传不缩放；
     输出为冻结 JSON schema `{bbox_norm, confidence, not_visible}`。
   - **分层规则（round 3 必修 4：硬停，无"缺层继续"路径）**：18 个
     声明分层（3 距离带 × 3 状态 × 2 场景）**每层最小 1 帧**；
     manifest 构建时（任何 API 调用前）若任一声明层可用帧数为 0 ⇒
     **硬停**，二选一后重来：(a) 扩大冻结来源目录清单并重新冻结
     manifest；(b) 以新一轮 Acceptance 裁定显式缩窄 spike 目标总体
     （删层并同步修改覆盖主张）。不存在一边缺层一边维持 18 层覆盖
     主张的路径；可用层合计仍须 ≥ 30 帧。
   - **记账**：解析失败/超时/超 schema = 失败样本，重试上限 1；
     全部原始响应存档。**预算耗尽规则**：40 次上限耗尽时，manifest
     中未处理样本一律计失败并入分母（不得截断分母美化成功率）。
   - **延迟校准测量（供 §2.4a 冻结门定值；round 3 必修 4 统一预算
     措辞：全部计入 ≤ 40 次总上限）**：每次调用逐条记录端到端延迟
     （请求发出 → 解析完成，单调钟），另以 ≤ 6 次调用跑 2–3 轮
     模拟协商负载的延迟样本；输出 p50/p95/max 分布，按 §2.4a 冻结
     公式导出三值候选（数值经 amendment 裁定 + 用户逐字授权后
     生效）。
   - **评分**：离线 scorer 读 `evaluation_truth.jsonl`（§2.2 允许的
     唯一场合之一），报告 IoU@0.5 成功率点估计 + Wilson 95% 区间 +
     逐分层分解；**通过线 70%（总体）在此预注册**，看结果前的修改
     只能经新一轮裁定。
   - **H2 对照**：同一 manifest 帧集跑 YOLOE 文本 prompt
     （冻结短语集 `{"red car","white car","vehicle"}`）报告召回。
   - **预算**：教师调用 ≤ 40 次；执行前须用户 Q1 逐字授权。
2. **V2 接口冻结**：`DialogueContext`/`VlmAction`/`vlm_command.json`
   schema 落入配置与文档，真值边界机械检查（§2.2）有构造性测试。
3. **V3 对照完备**：VLM-2 冻结前，每个交互能力有已定义的同信息
   对照与配对统计方案；任何能力缺对照即该能力不得进入论文主张。
4. **V4 事件剂量预注册**：遮挡车/干扰车的时刻/时长/外观参数在采集
   前冻结并哈希绑定；剂量作为自变量的消融表预注册。
5. **V5 处置完备**：§4.5 表中每行获得接受角色的显式 disposition；
   设计基线 v0.4 的改写与版本历史条目完成。
6. **V6 蒸馏防泄漏与部署判据（round 1 必修 7）**：
   - **切分组隔离**：train/val/test 按
     `(scenario_id, seed, 事件剂量档, 目标/干扰外观组)` 整组切分
     （70/15/15），任何组不得跨集出现。
   - **过滤边界**：真值过滤只发生在离线数据引擎；verifier 读
     `evaluation_truth.jsonl` 后仅输出 `(输入, 教师输出, pass/fail)`，
     学生训练输入与 `DialogueContext` 同构、零 evaluator 字段；
     过滤率与被滤样本的分层统计入工件。
   - **训练集组成（round 2 必修 7）**：**只有 verifier `pass` 的教师
     样本进入训练集**；`fail` 样本保留在独立的 held-out 诊断集
     （永不训练，仅用于教师错误模式分析并入工件）。某能力教师
     成功数为 0 时保留比无定义 ⇒ 该能力记
     `NOT_DISTILLABLE_NO_TEACHER_SIGNAL`，如实报告、不得并入均值。
   - **双门与记账**：学生/教师保留比阈值与逐能力绝对成功率下限
     **归 VLM-3 独立提案的采集前停点冻结**（本 recharter 只冻结
     "双门结构"本身，撤销 revision 1 的"建议 0.8"裁量残留）——只报
     比值会在"教师答对"的幸存样本上乐观化；失败样本按
     仅教师错 / 仅学生错 / 双错三分类记账；配对 bootstrap 95% 区间。
   - **门外授权**：训练算力（Q3）与 M7′ 板上延迟/内存/功耗上限各自
     待用户授权与显式启动；到期未达标按 H3 证伪分支如实报告，
     M7′ 降级为仅感知栈部署。

## 6. 基线、消融、失败模式和资源风险

### 6.1 基线与消融

- 逐能力同信息对照按 §3.1 表冻结（treatment/control 完全输入集合
  逐列在案）；教师 vs 学生 vs 对照三方配对。
- 消融轴：事件剂量（V4）、交互能力开关（仅改令/仅汇报/全开）、
  教师模型档位、学生规模与量化位宽（VLM-3/M7′）。
- 不设"无跟踪器纯 VLM"轴：VLM 不承担每帧跟踪，架构上不可比。

### 6.2 失败模式

- **F1 窗口被占**：同类工作发表 ⇒ 差异化退守 verified distillation
  + 系留长航时叙事 + 归因硬度；按月复查文献（构思角色义务）。
- **F2 demo 化**：任务集/对照设计不硬 ⇒ V3 是硬门，缺对照的能力
  禁入主张。
- **F3 API 成本失控**：预算逐字授权 + 网关调用计数入工件。
- **F4 训练算力不足**：本机 Mac 不足以正经蒸馏 ⇒ VLM-3 开工前
  需用户确认 GPU 途径（§8 Q3），未确认则 VLM-3 不开工。
- **F5 部署动机被质疑**：系留有线缆 ⇒ 论文如实采用"地面站边缘盒 +
  断缆应急自主"动机，不夸大机载必要性。
- **F6 教师输出污染**：教师 API 错误进入蒸馏集 ⇒ verified
  distillation 的真值过滤是硬门，过滤率入工件。

### 6.3 资源

云 API 预算（Q1）、可选 GPU（Q3）、既有 Unity/Python 环境；
零新增硬件直至 M7′（Orin 采购是 M7′ 的用户显式启动项，与原 M7 同）。

## 7. 建议但不强制的实现范围（VLM-1 批次草案）

1. `controller/vlm_gateway.py`：桥订阅、关键帧采样、API 适配、
   `VlmAction` 解析与分发；调用计数与输入清单工件。
2. spike 工具：分层帧采样 + IoU 评分脚本（复用
   `evaluation_truth.jsonl` 读取器）。
3. `DialogueContext` 打包器与真值边界测试。
4. `reprompt` → 三门管线适配器（零改动接入 `reanchor_runtime`）。
5. 相机位姿逐帧落盘（A0 审计指出的可复放缺口，随网关批次补）。
6. Debug 双件套（用户 2026-08-06 要求）：Edit Mode trace 可视化
   （逐 tick 可见性/阻挡实例着色）+ Play 逐帧归因通道
   （`OUT_OF_FRUSTUM / OCCLUDED_BY_<instance> / TRACKER_LOST /
   TRACKER_DRIFT`）。

## 8. 需要用户确认的事项（round 1 必修 9：写成带推荐的明确选项）

- **Q-A Phase 1 关闭出口**（决定 brief §4.6 与设计 §11 的措辞）：
  - **A1（推荐）**：Phase 1 止于 VLM-2（论文 1 实验完整即关闭）；
    VLM-3 + M7′ 组成独立的"Phase 1.5 蒸馏与边缘轨"，各有自己的
    启动授权。理由：出口早、每期可交付、算力风险不押在 Phase 1 上。
  - A2：Phase 1 包含 VLM-3（蒸馏入 Phase 1 主张，M7′ 仍单列）。
- **Q-B Phase 2 双机接力的去留**：
  - **B1（推荐）**：保留为远期愿景，brief 中排序改到蒸馏轨之后、
    措辞降为 outlook；不占任何近期范围。
  - B2：从 brief 删除（收窄叙事，代价是丢掉多机扩展故事）。
- **Q-C 论文出口**：
  - **C1（推荐）**：两篇分投——论文 1 交互系统 + 归因评估
    （VLM-2 出口）、论文 2 verified distillation + 边缘部署
    （M7′ 出口）。理由：窗口紧，论文 1 可先行占位。
  - C2：合并一篇长系统文章（更完整但发表更晚）。
- **Q1 API 预算**：教师模型 = `TEACHER_MODEL_ID_TBD_Q1`——授权时
  绑定供应商当时公开、本账户实际可调用的版本化 API model ID 及其
  价格；调用上限 spike ≤ 40 次（含延迟校准与协商负载样本）先行
  授权；VLM-1/2 采集预算随各自批次另行逐字授权。
- **Q3 训练算力途径**：云 GPU 预算或实验室资源；VLM-3 开工前确认，
  未确认则 VLM-3 不开工（§6.2 F4）。
- **Q4 串行顺序确认**：§4.7 表建议 spike → SCENE-007 → VLM-1；
  若你更急于见交互 demo，可交换序 3/4（两者无技术依赖，但
  SCENE-007 的 `2.11 m` 授权与锚点 GO 时点随之后移）。

## 9. 本提案自身的边界声明

本提案不实现任何代码、不运行 Edit Mode/Play、不消耗任何 ID/配额/
API 调用、不修改设计基线与任何既有提案文件、不自行标记 `ACCEPTED`、
不处置任何既有 work item 终态。提交后交接受角色 round 1 裁定。

---

## 10. Acceptance review decision

### Acceptance round 1 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

方向本身成立，且与 2026-08-06 账本中的五条用户原话一致：VLM 双向互动
应取代“VLM 仅为可选 L3 消融”的旧定位，视觉 grounding → 既有三门重锚定
也比继续押注仿真方块车的 YOLOE 文本 prompt 更符合已确认意图。引用的三个
最近邻确实存在：UAV-Track VLA 是 CARLA 中的 embodied tracking/VLA，
OA-VAT 覆盖实例级跟踪与遮挡规划，Chat with UAV 覆盖 LLM 人机任务规划。
这足以支撑“值得重构并继续论证”，但不足以支撑当前稿的排他性“无人占据”
表述；后者仍需可复现检索边界。

当前稿不能作为 v0.4 的逐字实现合同。最直接的阻断矛盾是
`DialogueContext.metrics_summary` 声称来自 `metrics.json` 且“无真值”：
本仓库的 `metrics.json` 由 `CoverageEvaluator` 产生，承载 `C_geom`、
`C_track` 等 evaluator 真值归因，不能进入 VLM/控制输入。交互实验也尚未
冻结操作员消息从何而来、何时发、是否知道真值，以及四类能力各自的同信息
对照；因此任何收益都可能只是信息不对称或事后选消息。最后，
`VlmAction` 缺少控制命令必需的版本、时序、坐标、幂等、拒绝和失效语义，
而“废止 BC-M34-3/7/8 中仅服务三策略的部分”又把精确边界留给实现者解释。

此外，本提案只请求修改设计文档，却与 `PROJECT_BRIEF.md` 的现行仓库契约
直接冲突：该 brief 仍把 VLM 定为 optional staged component，把 Phase 2
冻结为双机接力 + distilled policy，并把硬件部署钉为用户显式启动的 M7。
在这份冲突被显式迁移且获得用户授权前，Acceptance 不得只改设计 §1/§11
制造两份权威范围。

Required revisions for round 2:

1. **冻结四类交互任务与逐能力因果对照。** 分别为改令、询问、主动汇报、
   丢失协同给出任务实例、成功/失败/删失公式、分母、响应时限、调用/消息
   预算和配对统计单位。逐能力列出 treatment/control 的完全输入集合；
   自然语言改令的对照至少应通过结构化非学习接口获得同一语义内容，而不是
   简单“减去 dialogue”。操作员消息必须由采集前冻结、hash-bound 的脚本
   或独立协议产生，禁止读取 evaluator 真值或按结果事后选择消息。
2. **修复真值边界。** 从 `DialogueContext` 删除对 evaluator
   `metrics.json` 的任何读取，改为字段级 allowlist 的 controller-side
   摘要，并逐项写明来源文件/发布者及为何不含真值。`evaluation_truth.jsonl`
   只可由离线 spike scorer / distillation verifier 使用；网关进程输入
   allowlist、路径、hash 和构造性拒绝测试必须能机械证明二者隔离。
3. **把接口写成可执行的版本化协议。** 明确 `DialogueContext` 是替代还是
   保留 `RecoveryContext`，并为 context/message/action 冻结至少
   `schema_version`、唯一 ID、`track_id`、source `frame_id`、issue/expiry
   时间、坐标系/单位、模型/提示/输入 provenance。`reprompt.bbox_norm`
   必须逐字继承图像裁剪后的 normalized top-left `xywh` 语义并绑定源帧；
   `search_hint.region_xz` 必须声明世界坐标系、有效期和置信语义。
4. **补齐动作事务与安全边界。** 冻结原子发布、ACK/拒绝、重复/乱序/
   stale、重放幂等、冷却/重试上限、无效输出和网关失联时的 fail-safe。
   `search_hint` 只能进入经约束检查的 L2a/L2b/planner 消费接口，不得直接
   变成机身命令；`reprompt` 仍必须逐门通过 DETECT 三门，任何失败不得改变
   当前 tracker。保留的规划器命令合同必须先过独立停点。
5. **逐条处置旧 binding clarifications。** 对 BC-M34-1–10 每一条写
   `KEEP` / `SUPERSEDE` / `REPLACE_WITH_<新条款>` 和理由；不得使用
   “仅服务三策略的部分”这类不可机械核对的范围。尤其保留 BC-M34-6 的
   非真值 provenance、BC-M34-7 中仍适用于控制命令的安全语义、通用强制
   停点和用户显式启动 M7 的边界。相同精度补全 §4.5 中 DETECT criterion 4
   的新 owner、关闭门和证据归属，不得只写“移交/重述”。
6. **预注册 grounding spike，而非把即席双帧观察算作证据。** 在任何 API
   调用前冻结 ≥30 帧清单的来源、分层、去重、scene/target/event 覆盖、
   immutable manifest/hash、教师模型与版本、system prompt、温度、图像
   预处理、结构化 bbox 解析、无效输出记账、IoU 分母和通过线。报告点估计
   与不确定性；70% 门的修改只能在看结果前经新裁定。API 预算仍须用户另行
   逐字授权。
7. **冻结 verified-distillation 的防泄漏协议。** 训练/验证/测试按
   scenario、seed、事件剂量、目标/干扰外观成组隔离；说明真值过滤只发生
   在离线数据引擎且其输出不会把 evaluator 字段带入学生输入。学生/教师
   保留比必须同时绑定绝对任务成功率下限、失败样本记账和配对不确定性，
   避免只在“教师答对”的幸存样本上给出乐观比值。训练算力与 M7′ 硬件仍
   分别等待用户授权。
8. **把新颖性主张降到证据允许的强度。** 增加检索日期、数据库、query、
   inclusion/exclusion 和结果表，对“静态指令”“15 帧”“无跟踪闭环”等
   具体最近邻判断给出章节/页码。完成系统检索前把“当前无人占据”改为
   “在冻结检索范围内未发现”；按月复查是风险监控，不能替代 round-2
   接受时的可复现基线。
9. **闭合仓库契约与阶段边界。** 增加 `PROJECT_BRIEF.md` 的逐条迁移表，
   明确 Phase 1 的关闭出口究竟止于 VLM-2、是否包含 VLM-3，以及双机
   Phase 2 是否保留。Q2 论文出口和这些阶段边界必须作为待用户选择的
   明确选项（含推荐项），不得由 Acceptance 猜测；M7′ 继续是另行显式
   启动的未来硬件轨。获得用户逐字授权前不得修改 brief 或正式设计。
10. **给出 revision 1 的精确设计同步与串行恢复表。** 列出设计 §1/§2/
    §5/§6/§7/§8/§10/§11 和版本历史的替换文本范围；说明 recharter 接受后
    `P1-SCENE-007` revision 2 与 VLM-1 的建议串行顺序及各自仍待的用户
    GO。§4.5 的其余终态请求可保留，但本轮不预签任何一个 disposition。

Disposition:

- `P1-VLM-SCOPE-001` 保持单一活跃轨，退回构思角色提交 revision 1；
- v0.3.16、`PROJECT_BRIEF.md`、`P1-M3M4-SCOPE-001` 及其 BC-M34-1–10
  全部维持现状；本轮不关闭/不 supersede `P1-SCENE-005`，不改 M1 或
  DETECT criterion 4；
- `P1-SCENE-005` revision 4 与 `P1-SCENE-007` revision 2 继续
  `PAUSED_PENDING_RECHARTER`，不并行恢复；
- 不授权实现、Edit Mode/Play、API 调用、训练、配置/场景写入、锚点移动、
  ID/配额或硬件工作。revision 1 返回 Acceptance round 2。

---

## 11. Revision 1 逐条回应（构思角色，2026-08-06）

**1 — 四类任务与逐能力因果对照。** §3.1 新表冻结每类能力的任务实例、
成功/失败/删失公式、分母与配对单位、响应时限与调用预算、
treatment/control 完全输入集合。自然语言改令的对照改为**同语义结构化
接口**（冻结的属性→外观映射表注入候选框，走同一三门），不再是"减去
dialogue"。操作员消息统一为采集前冻结、SHA-256 绑定的脚本，触发条件
只引用 controller 侧信号，禁读真值、禁事后选择；oracle-hint 上界轴
显式分栏、不进主张。H4 随之改写。

**2 — 真值边界修复。** 接受裁定指出的矛盾属实：revision 0 把
`metrics.json` 当作"无真值"摘要来源是错误——它是 `CoverageEvaluator`
的产物。本稿将其**整体移出** VLM 输入（含任何摘要形式），
`DialogueContext` 改为 §2.1 字段级来源表：`platform_state` 取自帧
元数据（对实物 `frame_0000005200.json` 核对字段名：
`camera_position_world_m`、`camera_rotation_xyzw`、`gimbal_saturated`、
`tether_saturated` 等——平台状态逐帧已在，同名饱和标志一律取帧元数据
不取 `metrics.json`）；`tracker_state`/`command_history`/`event_queue`
全部来自 controller 自产文件。§2.2 补禁读清单、离线 scorer 例外的
精确范围、网关 allowlist + 哈希 + 构造性拒绝测试。

**3 — 版本化协议。** `DialogueContext` **取代** `RecoveryContext`
（L3 未实现，无兼容负担；设计 §2 替换见 §4.7）。公共信封冻结
`schema_version`、唯一 ID、`track_id`、`source_frame_ids[]`、双时钟
issue/expiry、provenance（model_id/精确版本串/system_prompt 哈希/
温度/输入哈希）。`reprompt.bbox_norm` 逐字继承 image-clipped
normalized top-left `xywh` 合同并绑定 `source_frame_id`；
`search_hint.region_xz` 声明 Unity 世界 XZ 坐标、`radius_m`、
`confidence` 与 `valid_until`。

**4 — 动作事务与安全。** 新增 §2.4：原子发布、在飞 ≤1、ACK/拒绝
枚举、`action_id` 幂等、stale/乱序拒绝、重试上限 1 + 冷却 10 s、
网关失联 fail-safe（跟踪栈按无-VLM 基线继续）。`search_hint` 只进
L2a 扫描排序器、不产生任何机身/云台命令；`reprompt` 必须逐门通过
DETECT 三门，门败保持当前 tracker 并回执入档；无效输出计入预算与
失败统计。

**5 — BC 逐条映射。** §4.2 对 BC-M34-1–10 每条给出
`KEEP`/`SUPERSEDE`/`REPLACE_WITH_*` 与理由，撤销"仅服务三策略的
部分"这类不可核对表述：BC-M34-6 与 BC-M34-5 的 M1 单独授权条款
`KEEP`；BC-M34-2 的同信息句、BC-M34-7 的命令契约要素、BC-M34-8 的
统计纪律以 `REPLACE_WITH_BC-VLM-*` 逐字继承进新语境。§4.5 补
DETECT criterion 4 的新 owner（VLM-2 事件批次）、关闭门
（reseed ≥ 10 次触发、零错误重锚定、三门证据齐）与证据归属。

**6 — spike 预注册。** §5 V1 重写：manifest（来源目录、三维分层、
去重规则、路径+哈希）先行提交且不可改；教师默认 `claude-sonnet-5`
（Q1 可改）、精确版本串、system prompt 冻结+哈希、`temperature=0`、
原始分辨率直传、冻结输出 schema、失败/重试记账；离线 scorer 报告
点估计 + Wilson 95% 区间 + 分层分解；70% 线预注册。本会话的双帧
读图在 §3.2 H1 降级为"方向性观察，不构成证据"。API 预算 ≤ 40 次
且待 Q1 逐字授权。

**7 — 蒸馏防泄漏。** §5 V6 重写：按
`(scenario, seed, 剂量档, 外观组)` 整组切分 70/15/15；真值过滤仅在
离线引擎、学生输入零 evaluator 字段、过滤率入工件；保留比与逐能力
绝对成功率**双门**、失败三分类记账、配对 bootstrap；算力（Q3）与
M7′ 各自待授权。

**8 — 新颖性降强度。** §1.3 增检索基线表（日期、库、五条逐字
query、纳排标准、最近邻判断出处及"未逐页精读"的诚实边界）；结论改
写为"在冻结检索范围内未发现占据者"；round-2 接受前须按同一 query
集复查一次，按月复查仅作风险监控。

**9 — brief 与阶段边界。** §4.6 给出 `PROJECT_BRIEF.md` 五处逐句
迁移表（L37 optional VLM、L44-45 Phase 2 蒸馏句为实质冲突；brief
不在任何角色白名单内，执行须用户授权的协调批次）。§8 把 Phase 1
出口（A1 止于 VLM-2，推荐）、Phase 2 双机去留（B1 保留为 outlook，
推荐）、论文出口（C1 分投，推荐）写成带推荐的用户选项，接受角色
不猜。

**10 — 设计同步与串行恢复。** §4.7 列设计 §1/§2/§5/§6/§7/§8/§10/
§11 与版本历史的逐节替换范围，以及六步串行恢复表（round 2 接受 →
spike → SCENE-007 全链 → VLM-1 → VLM-2 → VLM-3/M7′）与每步仍待的
用户门；spike 先于 SCENE-007 的理由（go/no-go 信息量最大且零 Unity
成本）写明；recharter 被拒时 SCENE-005/007 按原退修恢复、本表作废。

**授权与边界**：本稿不主张任何新授权；不实现、不运行、不调 API、
不写配置/场景字节、不动设计基线与 brief。提交后返回 Acceptance
round 2。

---

## 12. Acceptance review decision — round 2

### Acceptance round 2 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

Revision 1 实质关闭了 round 1 的若干核心缺口：`metrics.json` 已完整移出
在线输入，§2.1 所列相机位姿、内参和 `gimbal_saturated` /
`tether_saturated` 字段与真实 `SensorFrameWriter` 一致；四类任务已有
脚本化操作员框架；BC-M34-1–10、brief 迁移与阶段选项也不再留作实现者
自由解释。这些改进不重开。

但当前时序合同在真实代码上不可执行。冻结的 DETECT 配置把
`maximum_result_age_s=2.0`、`frame_buffer_s=6.0`、
`catchup_timeout_s=2.0`；现有 runtime 在检测源帧上初始化，再按
`frame_id` 重放到当前头帧。Revision 1 一面给 VLM 10 s 响应时限，一面
声称“复用既有三门”，又把任何早于消费者水位的 `source_frame_id` 直接
判成 `STALE_FRAME`。正常云 API 返回时源帧必然早于 live head；该规则会
绕过已接受的 replay/catch-up，且 2 s 结果年龄与 10 s 响应窗互相排斥。
这不是实现细节，而是决定 VLM grounding 能否进入三门的接口语义。

公共信封也把 simulation + Unix 称为“沿用仓库惯例”的双时钟。仓库用于
跨进程年龄判断的冻结时钟实际是带身份的
`capture_monotonic_clock_id=system-stopwatch/v1`；Unix 只作审计，不能
承担 expiry/latency。重复 `action_id` 一律回 `DUPLICATE` 也不是完整的
重放幂等：原 ACK 丢失后，消费者应对同 payload/hash 重发既有终态 ACK，
而不是让调用方无法区分“先前已生效”与“从未生效”。

研究归因仍有两个阻断。retask control 的精确候选框来自未定义的
“属性→外观映射表”；若它由 truth/人工点选生成，就是比语言 treatment
多了空间信息的 UI/oracle 上界，不能称同信息对照。`Δ`、`T_hold`、`τ`、
`T_censor`、LOST/框突变触发阈值和 query 评分容差仍未冻结，因此 round 1
必修 1 的公式尚不能机械执行。DETECT criterion 4 的新门只要求“触发
≥10 次 + 零错误重锚定”，允许十次全部被拒仍关闭；它遗漏旧门的成功
DISAGREE 重播种、完整 replay/catch-up、≥150 s 和
`incorrect/matched < 0.5` 结果义务。

最后，round-2 文献复查未完成到提案自定门槛：§1.3 明说 UAV-Track VLA
未逐页精读，仍没有 round 1 要求的章节/页码；本轮相同主题检索还找到
[VL-UniTrack](https://arxiv.org/abs/2605.04574)（visual-language prompts
+ mutual distillation 的 UAV-ground tracking 最近邻）和
[Aerial VLN survey](https://arxiv.org/abs/2604.07705)（明确列出
dialog-based aerial navigation），均未进入最近邻表。它们未必占据本
提案缝隙，但必须纳入后才能冻结“检索范围内未发现”的边界。官方 Anthropic
资料在本轮核验中也未提供 `claude-sonnet-5` 这一精确 API ID；Q1 应绑定
届时供应商实际公开且账户可调用的版本化 model ID，不得预注册未核实别名。

Required revisions for round 3:

1. **重写端到端时钟、expiry 与 replay 合同。** 公共信封以
   `simulation_time_s` + `capture_monotonic_s` + 精确
   `capture_monotonic_clock_id=system-stopwatch/v1` 承担时效语义，Unix
   只留审计；定义任一时钟缺失、identity 错误、双时限分歧时的 fail-closed
   规则。删除“源帧早于已处理水位即 stale”；`reprompt` 必须绑定源帧，
   在该帧初始化后走既有顺序 replay/catch-up，再以 source age、缓冲完整性、
   catch-up 收敛和原子 head equality 决定接受。
2. **闭合 VLM 延迟与冻结三门的数值冲突。** 在 `2.0 s` result age、
   `6.0 s` buffer、`2.0 s` catch-up 与当前 10 s API 响应窗之间选一个真实
   可运行的合同。若保持既有 DETECT 数值，则 VLM 超过 2 s 必须失败且
   spike 同时报告端到端延迟准入；若提议扩大 age/buffer/catch-up，须列出
   新值、内存/漂移风险、测试与安全归因，并把这项模型决策/安全语义变更
   标为待用户明确授权，不能借 recharter 默改。
3. **修复 action 幂等与回执绑定。** ACK 必须绑定 `action_id`、
   `context_id`、command payload hash 和终态。相同 ID + 相同 hash 的重放
   返回已缓存终态 ACK 且不重复生效；相同 ID + 不同 hash 才 fail-closed
   冲突。冻结跨进程重启的 watermark/ACK 保留范围、ACK 丢失恢复和
   单 in-flight 解除条件。
4. **完成四类任务的可执行归因合同。** 给 `Δ`、`T_hold`、`τ`、
   `T_censor`、LOST/框突变阈值、query 每类事实字段与数值/方向容差赋值，
   并冻结 paired schedule。逐字说明 retask control 的 bbox 来源：若为
   人工/真值点选，改列 `structured-UI/oracle upper bound`，与主同信息
   对照分栏；主对照不得通过 evaluator truth 获得空间框。核心表述同步
   区分 retask/loss-assist 的跟踪效能主张与 query/report 的通信正确性，
   无真人研究时不得外推 HRI usability。
5. **恢复 DETECT criterion 4 的行为闭环。** controller `LOST` 只可触发，
   evaluator truth 只可离线评分；门必须计“成功三门 + 完整 source-frame
   replay/catch-up + 原子替换”的实际 REANCHOR，而不是只计 reseed trigger。
   明确保留或有理由替换旧门的 ≥150 s、至少一次 DISAGREE 成功重播种和
   `incorrect/matched < 0.5`；新增的 ≥10 事件可作更强样本门，但十次全拒
   不得关闭 criterion 4。
6. **修正 spike/model/budget 与串行表。** 把教师写为
   `TEACHER_MODEL_ID_TBD_Q1`，Q1 时绑定供应商公开、账户可调用的精确 API
   model ID、价格和版本；定义总调用上限耗尽时未处理 manifest 样本如何
   计失败。§4.7 序 4 不得写“VLM-1 复用 Q1”：Q1 当前仅授权候选为 spike
   ≤40 次，VLM-1/2 各自仍需独立预算。18 个声明分层须给每层最小数或
   manifest-before-call 的 `STRATUM_UNAVAILABLE` 停止规则。
7. **完成文献与蒸馏冻结。** 对 UAV-Track VLA 的具体判断补可复查章节/
   页码，把 VL-UniTrack 和 dialog-based aerial VLN 最近邻纳入同一 query
   复查表并据此更新边界。V6 明确只有 verifier `pass` 的教师样本是否进入
   训练、failed 样本如何保留，给出 teacher=0 时的保留比语义；`0.8` 与
   各能力绝对下限要么在 revision 2 冻结，要么明确归到独立 VLM-3 提案的
   采集前停点，不能写成由 Acceptance 猜测的“建议值”。

Disposition:

- `P1-VLM-SCOPE-001` 继续作为唯一活跃轨，退回构思角色提交 revision 2；
- round 1 已关闭的 `metrics.json` 禁读、真实帧元数据来源、BC 映射表形式、
  brief 迁移选项化和资源隔离不重开；
- Q-A/B/C、Q1、Q4 本轮均不提交用户选择：技术合同修正后再请求授权，
  Q3 仍只在 VLM-3 开工前到期；
- v0.3.16、`PROJECT_BRIEF.md`、BC-M34-1–10、M1、DETECT criterion 4 与
  全部 §4.5 legacy disposition 维持现状；SCENE-005/007 继续暂停；
- 不授权实现、Edit Mode/Play、API 调用、训练、配置/场景写入、锚点移动、
  ID/配额或硬件工作。revision 2 返回 Acceptance round 3。

---

## 13. Revision 2 逐条回应（构思角色，2026-08-06）

**1 — 时钟/expiry/replay 合同。** 信封时效改由
`simulation_time_s` + `capture_monotonic_s` +
`capture_monotonic_clock_id=system-stopwatch/v1` 承担，Unix 降为纯
审计；时钟身份错误/字段缺失/双时限判定分歧一律 `CLOCK_INVALID`
fail-closed（§2.1）。**水位即 stale 规则删除**——承认它会拒绝一切
云 API 返回并短路已接受的重放机制；`reprompt` 改为完整继承
`reanchor_runtime` 四件套（源帧初始化 → 顺序 replay/catch-up →
源龄/缓冲/收敛判定 → 原子头相等替换），`STALE` 重定义为仅超
`maximum_source_age_s`（§2.4a）。

**2 — 延迟与三门数值。** 按用户 2026-08-06 方向确认（账本当日
条目；其自有实验：Gemini Flash 好网络 1–2 s，协商机制/更优质输出
更长）**排除 2 s 硬门路线**，走扩参数路线：`vlm_reprompt.*` 单列
参数组（合同上界 age ≤ 15 / buffer ≤ 20 / catchup ≤ 4 s，内存代价
≈ 5 MB 已列），DETECT 原组零字节改动；协商/出框解耦（出框前强制
以最新帧重新 grounding，年龄门只覆盖最后一跳）；正式数值由 spike
的端到端延迟分布（p95 × 2 上取整）导出后**作为安全语义变更另行
请求用户逐字授权**，未授权前通道不启用；VLM-1 停点须报告扩参数下
replay 收敛率与错误重锚定率（§2.4a、§4.7 序 4）。

**3 — 幂等与回执。** ACK 绑定 `action_id` + `context_id` +
`payload_sha256` + 终态；同 ID 同 hash 重放**返回缓存终态 ACK**、
不重复生效；同 ID 异 hash 才 `ID_CONFLICT`；ACK 账本落盘、跨进程
重启恢复、账本损坏则 `ACK_LEDGER_INVALID` 拒绝重放请求；in-flight
解除 = 终态 ACK 或 expiry + `ack_grace_s = 5` 后记
`EXPIRED_UNACKED` 且该 ID 永久作废（§2.4b）。

**4 — 归因合同赋值。** `Δ=20 s`、`T_hold=10 s`、`τ=5 s`、
`T_censor=60 s`、LOST=连续 2 s、框突变=min(w,h) 相邻变化 >50%、
query 六类逐字段容差、paired schedule 全部冻结（§3.1 数值合同表）。
retask 主对照弃用"属性→外观映射表"（承认其框来源不明），改为
**非学习颜色分割选框器**（同帧、冻结 HSV 带、连通域最大块，零真值
零学习）；oracle-UI 注入框改列上界分栏。任务分属性档/语义档：
语义档无平权对照、主张降级为对上界的接近度；retask/loss-assist 与
query/report 的主张按跟踪效能/通信正确性分层，无真人被试不外推
HRI usability（§3.1、H4）。

**5 — criterion 4 行为闭环。** 门重写为六条同时成立：成功
REANCHOR 闭环（三门 + 完整 replay 收敛 + 原子替换）≥ 10 次且
**十次全拒不得关闭**、≥ 1 次 DISAGREE 成功重播种、会话 ≥ 150 s、
`incorrect/matched < 0.5`、LOST 只由 controller 触发 / truth 只
离线评分、三门证据齐（§4.5）。

**6 — spike/model/budget/串行。** 教师改
`TEACHER_MODEL_ID_TBD_Q1`（Q1 绑定供应商公开且账户可调用的版本化
ID + 价格；承认 `claude-sonnet-5` 未经 API ID 核实）；预算耗尽时
未处理样本计失败入分母；18 层每层最小 1 帧 +
manifest-before-call 的 `STRATUM_UNAVAILABLE` 规则、总数不足则扩
来源重冻结；§4.7 序 4 改"VLM-1 预算另行授权 + 参数值授权"；spike
逐调用记录端到端延迟并加 ≤ 6 次协商负载样本（为必修 2 定值供数，
计入 40 次总预算内的独立小额）（§5 V1、§4.7）。

**7 — 文献与蒸馏冻结。** §1.3：UAV-Track VLA 判断补出处（v1
Abstract/Metrics 节，声明未逐页精读的核对边界）；VL-UniTrack 纳入
并给三点"撞名不撞实质"区分（训练期双视角互教 ≠ 模型压缩蒸馏；
4 个视角模板短语 ≠ 操作员语言；双视角协同 ≠ 交互监控），其
limitations 反向引证蒸馏轨动机；AVDN 家族四篇（[28]/[110]/[109]/
[87]）纳入并给任务级区分表，缝隙表述收窄为"动态目标持续跟踪任务中
的双向操作员对话（含机→人主动汇报与丢失协同）"。§5 V6：训练集
只收 verifier `pass` 样本、`fail` 样本入永不训练的诊断集、
`teacher=0 ⇒ NOT_DISTILLABLE_NO_TEACHER_SIGNAL`；保留比与绝对下限
数值撤出本 recharter，归 VLM-3 独立提案的采集前停点冻结。

**授权与边界**：本稿不主张任何新授权；`vlm_reprompt.*` 正式数值、
Q-A/B/C、Q1、Q3、Q4 全部按 round 2 Disposition 留待技术合同通过后
的授权轮。不实现、不运行、不调 API、不写配置/场景字节、不动设计
基线与 brief。提交后返回 Acceptance round 3。

---

## 14. Acceptance review decision — round 3

### Acceptance round 3 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

Revision 2 已实质关闭 round 2 的多项阻断：公共信封改用带身份的单调钟，
`reprompt` 删除错误的“早于水位即 stale”规则并恢复 source-frame 初始化、
顺序 replay/catch-up 与原子 head equality；DETECT 原参数组保持不动；
criterion 4 已恢复成功 REANCHOR、DISAGREE、150 s、
`incorrect/matched < 0.5` 和三门证据；四类任务的基本数值、属性/语义分档、
颜色分割对照方向以及 pass-only 蒸馏集也已补齐。这些内容下一轮不得无故
重开。账本中的用户原话只确认“排除 2 s 硬门、扩参数待实验校准”，提案对
该授权边界的理解正确；本轮不要求用户提前拍最终数值。

但 revision 2 仍不能作为无歧义的接受→实现交接物。§2.4a 只给
`maximum_source_age_s = ceil(2 × p95)` 的方向和三个上界，没有定义 p95
算法、超 `15 s` 的失败分支，也没有给 `frame_buffer_s`、
`catchup_timeout_s` 的导出规则；“延迟校准不加预算”又与“≤6 次调用计入
40 次”并存。实现者仍可自行选择两项安全参数或在超上界时截断。正确做法
是把 spike 后的三值冻结设为一个新的接受/用户授权停门，而不是把待定值
藏在 VLM-1 内。

ACK 合同也尚未闭合。§2.4b 声称 ACK 绑定
`action_id + context_id + payload_sha256`，重放规则却只比较
`action_id + payload_sha256`，因此同 action/hash、不同 context 的处理
未定义；payload 的规范化字节也未定义。更关键的是，提案没有规定
“动作生效”与 ACK ledger 持久化之间崩溃时的恢复状态机，单纯说“重启后
恢复缓存”不能证明不会重复生效或虚报已生效；首次 run 的正常空账本也与
“账本缺失即拒绝重放”混在一起。

归因表已有阈值，但尚不能机械评分。`answer` 只有自由文本，而 query
scorer 没有冻结结构化事实或确定性解析器；report 没有事件匹配窗、去重和
同一事件多报的计数规则。颜色分割器允许在“可靠性 < 90%”后回炉，却没有
冻结与正式 paired runs 隔离的标定集，会留下看结果调 HSV 的通道。18 个
声明分层的 `STRATUM_UNAVAILABLE` 又被定义成“不计失败且继续”，不是
round 2 要求的 manifest-before-call 停止规则。

文献边界仍有实质误述。AVDN 原论文明确记载 follower 会在需要时主动提问、
commander 回答，不能写成“人→机单向引导”；本提案可主张的缝隙应落在
**动态目标持续跟踪中的改令、主动事件汇报和丢失协同**，不能落在“双向
对话”本身。Revision 2 引用的 UAV-Track VLA 自己在 Related Work §2.1
列出 [TrackVLA](https://proceedings.mlr.press/v305/wang25c.html)、
[TrackVLA++](https://arxiv.org/abs/2510.07134) 和
“VLM can be a good assistant”（self-reflection recovery）等更近的
embodied visual tracking 工作，却都未进入本稿最近邻表。verified
distillation 贡献也应至少对照
[Visual Program Distillation](https://arxiv.org/abs/2312.03052) 这类
“执行/标签验证后再蒸馏”的既有方法。现有差异可能成立，但冻结检索尚不足
以支撑当前“不占据”表述。

另有三处直接残留矛盾：§8 Q1 仍写“默认 `claude-sonnet-5`”，与
`TEACHER_MODEL_ID_TBD_Q1` 冲突；H3 仍写“Acceptance 冻结，建议 0.8”，
与 V6 声称把全部阈值移交 VLM-3 的文字冲突；§4.7 序 1 仍写“round 2
接受”。这些必须按全文唯一语义清理，不能只在 §13 回应中声明已删除。

Required revisions for round 4:

1. **把时序校准写成独立、失败封闭的参数冻结门。** 冻结 p95 的有限样本
   算法、取整单位以及三项参数各自的导出/可行性规则；明确任何候选超过
   `age ≤ 15 / buffer ≤ 20 / catchup ≤ 4 s`，或 replay 基准无法支撑
   候选值时，结果是 `VLM_REPROMPT_TIMING_INFEASIBLE` 并返回构思，禁止
   截断到上界。所有延迟样本（含模拟协商的 ≤6 次）必须计入 Q1 的 40 次
   总上限。串行表改为：recharter 接受与 Q1 授权 → offline spike →
   三值 amendment 由 Acceptance 裁定并取得用户逐字授权 → 才可启动依赖
   该结果的 VLM-1；spike 不消费、也不启用在线 `vlm_reprompt` 通道。
2. **冻结完整的 action/ACK 恢复状态机。** 缓存键逐字为
   `(action_id, context_id, canonical_payload_sha256)`；任一字段不一致均
   `ID_CONFLICT`。定义 canonical payload 字节、首次 run 创建空账本、
   已存在账本丢失/损坏、`PREPARED/APPLIED/ACKED`（或等价）崩溃窗口与
   重启恢复，以及过期后迟到 ACK 的唯一处理；每条路径都必须证明动作
   至多生效一次且重发能取回原终态。公共 schema_version 给出精确值；
   `search_hint.valid_until_simulation_s` 改为同一单调钟有效期对，或明确
   仅为不参与接受/过期判断的审计字段。
3. **使 query/report 与颜色对照可机器复核。** `answer` 增加冻结的
   结构化事实字段（自由文本只作展示），或冻结确定性解析器及无法解析的
   失败语义；逐问句类消除“5 m 或八分区”这种未绑定题型的 `OR`。为
   report 冻结事件 ontology、匹配容差窗、重复报告/一报多事/迟报的
   TP/FP/FN 规则。颜色分割器的标定集必须与正式 paired runs 按
   scenario/seed/外观组隔离，HSV 与 90% 资格结论在正式结果前冻结；未过
   资格门就阻断属性档主张，不得用正式结果回炉调参。
4. **修正 spike 分层和全文残留。** 每个可用声明层 ≥1；任何
   `STRATUM_UNAVAILABLE` 在 API 调用前硬停并扩来源重冻结，或经新裁定
   明确缩窄 spike 的目标总体，不能一边缺层一边维持 18 层覆盖主张。
   全文删除 `claude-sonnet-5` 默认值与 H3 的 `0.8` 建议残留，把阈值
   唯一归到 VLM-3 采集前停点；统一“≤6 次也计入 ≤40”的预算措辞，并
   修正串行表的过期 round 编号。
5. **重做最近邻边界，不扩大当前执行范围。** 把 AVDN 写成真实的双向
   问答导航，主张收窄到动态跟踪中的 operator retask、机→人主动事件
   汇报与 loss-assist 的组合；把 UAV-Track VLA §2.1 指向的
   TrackVLA/TrackVLA++/self-improving VLM recovery 纳入同一检索表，逐项
   比较任务、语言轮次、动作空间、恢复机制和指标。对 verified
   distillation 增加 verifier/filter-then-distill 最近邻并说明本稿仅能
   主张的任务/数据引擎差异。更新 query 与 inclusion 规则使这些近邻不会
   被漏掉；完成前不写“冻结范围内未发现占据者”。

Disposition:

- `P1-VLM-SCOPE-001` 保持唯一活跃轨，退回构思角色提交 revision 3；
- round 3 已确认关闭的 monotonic/replay、DETECT 零改动、criterion 4、
  任务基本数值、属性/语义分档与 pass-only 蒸馏方向不得无故重开；
- Q-A/B/C、Q1、Q4 和三项时序正式值仍不提交用户选择；技术合同通过后再
  进入授权轮，Q3 仍只在 VLM-3 开工前到期；
- v0.3.16、`PROJECT_BRIEF.md`、BC-M34-1–10、M1、DETECT criterion 4 与
  全部 §4.5 legacy disposition 维持现状；SCENE-005/007 继续暂停；
- 不授权实现、Edit Mode/Play、API 调用、训练、配置/场景写入、锚点移动、
  ID/配额或硬件工作。Revision 3 返回 Acceptance round 4。

---

## 15. Revision 3 逐条回应（构思角色，2026-08-06）

**1 — 时序校准独立冻结门。** §2.4a 新增四步冻结门：p95 = type-7
分位、有效样本 ≥ 20（失败调用单列不入分布、协商样本单列不进 age
导出）；三参数各自的预注册导出公式——`age = ceil_0.5(2×p95)`、
`catchup = ceil_0.5(4 × age × 5 × 0.003332854)`（单帧重放耗时取
`P1-TRACK-002` 复核档案 p95 `3.332854 ms` 为常量）、
`buffer = ceil_1(age + catchup + 2)`；任一候选超上界（15/4/20）或
样本不足 ⇒ `VLM_REPROMPT_TIMING_INFEASIBLE` 返回构思角色，**禁止
截断/减倍/换分位**。可行时三值以 amendment 经 Acceptance 裁定 +
用户逐字授权（§4.7 新序 2.5 独立停门），VLM-1 前置于它。预算措辞
统一：全部延迟样本（含协商 ≤ 6 次）计入 Q1 ≤ 40 次。

**2 — ACK 恢复状态机。** §2.4b 重写：缓存键逐字三元组
`(action_id, context_id, canonical_payload_sha256)`、任一不一致即
`ID_CONFLICT`；canonical 字节按 BC-P2-10 strict RFC 8259 先例精确
定义；状态机 `PREPARED → 生效见证 → ACKED`，生效见证 = controller
运行日志中带 `action_id` 的 `REANCHOR`/`HINT_CONSUMED` 事件行
（与生效同进程同事件流、单行 append 原子），崩溃恢复算法凭见证
判定补 `ACKED(accepted)` 或 `ACKED(rejected, CRASH_BEFORE_APPLY)`
——每条路径至多生效一次且重发取回原终态。首次 run 合法空账本与
`ACK_LEDGER_INVALID` 按"有无既往 VLM 痕迹"分离；迟到 ACK 按
"消费者账本为动作终态权威、任务记账维持超时失败"双列如实报告。
`schema_version = "vlm-interaction/v1"`；`search_hint` 有效期改为
单调钟对并参与消费时过期判定。

**3 — 机器可评分。** §3.1 新增三行合同：`answer.facts` 结构化
字段（七类题型各自 schema，`text` 仅展示、`facts` 缺失即失败）；
评分卡按题型拆分（`POS_COORD` 5 m / `POS_BEARING` 八分区各自
独立），消除跨题型 `OR`；report 冻结事件 ontology 四类枚举 +
`[−1,+5] s` 匹配窗 + 贪心一对一 + 多报首条 TP 余者 FP、迟报
FN+FP、TP 上统计延迟。颜色对照器资格门：标定集与正式 paired runs
组隔离、HSV 与 90% 资格在任何正式 run 前冻结并哈希、不过门即阻断
属性档主张，**不存在用正式结果回炉调参的路径**。

**4 — 分层硬停与残留清理。** `STRATUM_UNAVAILABLE` 改为 API 前
硬停（扩来源重冻结，或经新裁定显式缩窄总体并同步修改覆盖主张），
删除"缺层继续"路径。全文残留清理：§8 Q1 删 `claude-sonnet-5`
默认（改 `TEACHER_MODEL_ID_TBD_Q1` 全文唯一语义）；§3.2 H3 删
"建议 0.8"（双门阈值唯一归 VLM-3 采集前停点）；§4.7 序 1 过期
编号改"recharter 接受（最终轮）"。

**5 — 最近邻边界重做。** §1.3：AVDN 更正为**真实双向问答**
（follower 主动提问、commander 回答），撤回"人→机单向"误述；
新增 TrackVLA（2505.23189：地面 EVT、一次性指令、扩散轨迹、
EVT-Bench 1.7M）、TrackVLA++（2510.07134：+Polar-CoT+TIM 记忆、
恢复=内部机制）、VLM-Assistant（2505.20718：**架构最近邻**——
快慢双层、失败触发 VLM、自反思自改进，但纯自主自恢复无操作员
在环）三行逐项比较（任务/语言轮次/动作空间/恢复机制/指标）；
verified distillation 增加 VPD（2312.03052）先例行，本稿差异
收窄为"仿真真值验证器 + 监控动作域"两点。缝隙最终收窄为
**operator retask + 机→人主动汇报 + loss-assist 的操作员在环
组合**，不再落在"双向对话"或"VLM 辅助恢复"本身；query 集增补
两条实际执行的新检索、inclusion 扩到地面 EVT×语言与
verify-then-distill 先例。两个最近邻家族反向佐证两个半边的
范式成立。

**授权与边界**：本稿不主张任何新授权；时序三值、Q-A/B/C、Q1、Q3
全部按 round 3 Disposition 留待技术合同通过后的授权轮。不实现、
不运行、不调 API、不写配置/场景字节、不动设计基线与 brief。
提交后返回 Acceptance round 4。

---

## 16. Acceptance review decision — round 4

### Acceptance round 4 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

Revision 3 已关闭 round 3 的大部分研究设计缺口：AVDN 已更正为双向问答，
TrackVLA / TrackVLA++ / VLM-Assistant / VPD 已进入最近邻表，主张也收窄到
operator retask + 主动汇报 + loss-assist 的组合；18 层缺一即停、API
总预算、query 逐题型 facts、report 的基本 TP/FP/FN 窗口和颜色对照的
正式结果隔离均已写出。DETECT 原参数组、criterion 4、monotonic/replay
主方向和 pass-only 蒸馏继续保持，不在下一轮重开。

当前首要阻断仍是 ACK 的崩溃论证不成立。§2.4b 把“同进程同事件流”当成
生效与见证原子，但真实代码中 `ReanchorRuntime.before_update()` 只在
`controller/reanchor_runtime.py:134` 把 `REANCHOR` 放进**内存**队列，
`TrackLoop` 在 `controller/track_loop.py:421` 替换 tracker，直到
`track_loop.py:544` 才 drain 到运行日志；`RunLogger.append()` 又只 flush，
到 close 才 fsync。动作已影响后续帧/输出、持久见证尚不存在的崩溃窗口
真实存在。此时“无见证 ⇒ 未生效 ⇒ `CRASH_BEFORE_APPLY`”是错误归因。
此外状态机只定义 `reprompt` 与 `search_hint`，没有说明 `answer` / `report`
的展示或发送副作用如何去重、如何恢复，因而不能声称覆盖全部 `VlmAction`。

时序门虽有公式，却仍没有执行用户要求的“稍后设计实验检查”。
`3.332854 ms` 是 TRACK-002 对 `tracker.update()` 单独计时的 100 次合成帧
benchmark；真实 `replay_tracker()` 还包含 tracker factory、source-frame
`init()`、历史遍历、逐帧 update 和追赶移动 head。固定乘 4 不是这些路径的
实测，不能作为 `catchup_timeout_s` 的唯一冻结依据。它可保留为先验 sanity
bound，但序 2.5 amendment 前还需要零 API 的实际 replay/catch-up 校准。

机器评分合同也有三处接口断裂。§2.1 的 `answer` 行仍只有 `text`，与
§3.1 新增 `answer.facts` 冲突；`report` 仍只有绑定 controller
`event_queue` 的 `event_ref + text`，但 scorer 的 truth ontology 含
`TARGET_STOPPED`、`OCCLUSION_LOSS`、`DISTRACTOR_CONFUSION`，没有冻结
这些 truth 类型如何映射到在线可见事件、结构化 report 字段和非学习
control。当前 control 只模板化 LOST / 框突变 / REANCHOR，而 treatment
可读 frames 与完整 `DialogueContext`，既不能保证两组可表达同一事件，
也不能证明同信息归因。颜色 HSV 的调参与“≥90% 资格”仍使用同一标定集，
90% 会成为训练集成绩而非独立资格门。

最后，§1.4 核心问题仍把四类通道统一表述成“任务级跟踪效能显著优于
无语言基线”，与 §3.1 已承认的分层矛盾：query / report 只支撑通信
正确性，不应被写成提高跟踪效能。VPD 的区分也不准确：该工作在有标签时
会用标签验证程序输出后再蒸馏，不只是“程序执行一致性”；本稿不能把
“用真值过滤教师输出”本身当作方法新颖点，只能主张仿真跟踪动作域、自动
任务验证器和系统归因组合。另有两个会误导实现者的残留：§2.1 已确认相机
位姿逐帧存在，§7 却又要求“补相机位姿逐帧落盘”；`answer.facts` 尚未进入
主 action schema。

Required revisions for round 5:

1. **把 ACK 改成可实现的持久化/崩溃合同并覆盖四种 action。** 对
   `answer`、`report`、`reprompt`、`search_hint` 各自冻结消费者、实际
   副作用、幂等键和恢复路径；PREPARED/见证/终态的耐久点必须明确到
   fsync/原子文件或具同等保证的事务顺序，不能把进程内 append 称为持久
   原子。若某副作用无法与见证原子提交，崩溃后无见证只能记
   `CRASH_OUTCOME_UNKNOWN`、永久烧掉 ID 且任务计失败，禁止重放，也禁止
   虚报 `CRASH_BEFORE_APPLY`；若坚持 accepted/rejected 二值，则须给
   idempotent sink 或可核验 commit record。canonical JSON 同步写明
   `allow_nan=false`、所有数值有限，否则“strict RFC 8259”与所列 Python
   调用不一致。预注册 crash-injection 矩阵覆盖每个耐久边界。
2. **让序 2.5 使用真实 replay/catch-up 实测。** 在不调用 API 的前提下，
   对实际 `replay_tracker()` 路径（factory + init + N 次 update + 移动 head
   追赶）使用冻结的 640×480 归档帧和目标运行设备做预注册样本；冻结样本
   数、age 档、p95 算法、head 推进负载和失败记账。`catchup_cand` 必须由
   该实测分布的预注册余量公式导出；TRACK-002 的 update-only 常量只可作
   交叉检查。随后再计算 buffer，并继续沿用 15/4/20 上界、不可行硬停、
   amendment 裁定和用户逐字授权。
3. **统一 action schema 与 report 因果合同。** 在 §2.1 主表中加入
   `answer.facts` 的精确字段并使 `text` 仅展示；为 report 增加机器评分的
   结构化 `event_type/event_time`（或等价字段），说明 `event_ref` 缺失、
   不可映射和多事件引用的失败语义。冻结 controller-visible candidate
   events → offline truth ontology 的映射、同一份 treatment/control
   可见输入、非学习 control 如何从这些输入产生四类候选，以及贪心同距
   tie-break；任何需要 evaluator truth 的分类只能在 scorer，不能进入
   在线 action/control。颜色对照拆成互不重叠的 HSV tuning 组与
   qualification 组；qualification 未过即阻断，不能回看该组继续调参。
4. **统一核心主张、文献定位与实现草案。** §1.4/§4.6 明确拆成：
   retask + loss-assist 的跟踪效能主张，query + report 的通信正确性主张；
   不把后两者宣称为提高 `C_track`/MTTR。把 VPD 写成“执行候选并在有标签
   时以标签验证正确输出后蒸馏”的先例，verified-distillation 的新颖性只
   落在本任务域与系统化自动验证/归因组合。删除重复资产行；删除或精确
   解释 §7 已存在相机位姿却仍要补写的矛盾，并把未在授权账本出现的
   “用户要求 Debug 双件套”改成提案建议或补可核对来源。

Disposition:

- `P1-VLM-SCOPE-001` 保持唯一活跃轨，退回构思角色提交 revision 4；
- round 4 已确认关闭的最近邻纳入/主张收窄方向、stratum 硬停、预算隔离、
  query 基本阈值、report 基本匹配窗与颜色正式结果隔离不得无故重开；
- Q-A/B/C、Q1、Q4 和三项时序正式值仍不提交用户选择；revision 4 技术
  合同通过后才进入核心主张/阶段边界授权轮，Q3 仍只在 VLM-3 前到期；
- v0.3.16、`PROJECT_BRIEF.md`、BC-M34-1–10、M1、DETECT criterion 4 与
  §4.5 全部 legacy disposition 维持现状；SCENE-005/007 继续暂停；
- 不授权实现、Edit Mode/Play、API 调用、训练、配置/场景写入、锚点移动、
  ID/配额或硬件工作。Revision 4 返回 Acceptance round 5。
