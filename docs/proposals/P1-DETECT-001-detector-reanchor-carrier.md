# P1-DETECT-001 — 最小安全三门再锚定载体（周期 YOLOE 类级候选 + 独立外观嵌入门 + 世界系运动门）

Status: ACCEPTED_WITH_BINDING_CLARIFICATIONS (Codex round 2, 2026-07-28);
Amendment A1 (appearance-embedding model swap): REVISION 2 PROPOSED
(2026-07-28, responds to A1 Codex Round 1 all four blockers)
Author/role: Claude Fable / design ideation
Created: 2026-07-28
Last updated: 2026-07-28 (Fable files A1 revision 2: bicubic transform
contract, 40-hex commit pin with license hash, exact offline
construction/load/output contract, narrowed threshold and capability
claims)

## Problem and research value

### 立项证据（RATE-002 B2 Decision A，2026-07-28）

纯 SOT 载体（NanoTrack-v2 → LOS 云台伺服）在正式会话长度上被三个
admissible 复测一致证伪（`runtime/rate-study/P1-M2-RATE-002-B2/decision_a.json`）：

1. **失败机制**：release 后前 ~40 s 追踪真实正确（与 30 s pilot 逐帧一致，
   pilot `C_track|geom=0.9909`）；目标驶向远端路段（斜距 ~75 m、车高
   ~9 px、`C_geom=0.610`）后，SOT 把模板交接给地平线附近静态背景并锁死
   （后段框中心标准差 ~0.001），云台伺服将错误框稳定居中并饱和——**闭环
   把错误锁定变成稳定平衡点**，剩余 ~230 s 全部 incorrect；
2. **判定**：R1′ 触发（`C_track|geom` 中位数 0.24963 < 0.25，贴线）、
   R2′ 触发（incorrect/matched 中位数 0.8475，0.3/0.5/0.7 全触发）、
   R3′ 右删失未触发；预选 stop 分支生效，`M2_NOT_CLOSABLE`，正式
   5/20 Hz 对比义务转移至新载体/新批次；
3. **置信度信号实证失效**：背景锁定期间 NanoTrack 分数保持 0.83–0.94
   （中位 0.90），与正确期不可区分——证实 `P1-TRACK-002` §2 的预declared
   限制（上游无校准丢失语义），LOST 通路存在但恒不触发；
4. **协议教训**：30 s 资格 pilot 恰落在存活包络内、无预测力；R3′ 绑定
   追踪器自报 LOST，对无有效丢失信号的载体是空转规则。

### 研究价值

1. **载体可行性**：为继任率研究提供能在整环会话（环周期 106.485 s，
   会话 272.97 s）存活的测量流——这是 M2 正式关闭的前置；
2. **感知消融轴（归因标签按 round 1 意见 6 修正）**：本项交付的是
   **最小安全三门载体**（YOLOE 类级提议 + 独立外观嵌入门 + 世界系
   运动门），不是纯 `SOT+周期 YOLOE` 档。继任对比命名为
   `SOT-only → minimal triple-gated re-anchor`；**相对 SOT-only 的收益
   不得单独归因给 YOLOE**。若日后需分离 YOLOE/嵌入门/运动门的组件
   贡献，另行预注册安全的组件消融；完整 view-bank/模板管理仍在 M4。
   **B2 三复测只作历史探索性 SOT-only 底点**；正式 confirmatory 配对
   对比须由继任协议在相同冻结场景、时长与准入条件下**新采 SOT-only
   对照**（用户 2026-07-28 确认）；
3. **M4 基座**：本项的嵌入门与运动门就是 §3.3 三重打分的最小实现，
   显式 LOST/再锚定事件流是 §5 升级阶梯的入口信号；M4 在其上扩展
   （MHT、view bank、模板管理、搜索），不推倒重来。

### 授权链

- `P1-TRACK-002` §4（round 2 接受）把 YOLOE 检测通道预留给本 ID；
  Decision A stop 分支把对比义务交给新载体；
- 用户 2026-07-28 确认现状为纯 SOT 并选定方向 A；
- **用户 2026-07-28（Codex 强制决策点）选定选项 1**：授权把有界的周期
  YOLOE **类级候选通道**提前为 M2 载体前置，但保留 v0.3.1 的正确身份
  安全边界——**控制生效的自动重播种必须同时通过独立 ReID（外观嵌入）
  门和运动门**；仅类级证据的候选只能记录为 tentative，不得重播种；
- 用户同时确认 B2 数据定位（见研究价值 2）；
- Codex round 1 确认边界问题已关闭，本 revision 只处理其七项技术返修。

## Proposed behavior

### 1. 双通道最小形态（SOT 主通道不变）

- SOT 主通道：冻结的 NanoTrack-v2 插件原样保留（`P1-TRACK-002` 候选
  `46747d8` 的 verdict 不被继承或改动），逐帧驱动 LOS 伺服；
- 再检测通道：按固定节奏在已发布帧上异步运行（worker 语义见 §6），
  任何一轮推理不得阻塞 SOT/伺服循环；
- **节奏按秒定义而非按帧**（2.0 s/轮，见 §5 参数表），5 Hz 与 20 Hz
  细胞的再检测频率因此相同；**调度与所有时间戳一律使用同主机单调
  时钟**（帧侧采用 `tethered-sensor-frame/v2` 的 `capture_monotonic_s`，
  worker 侧采用同主机 monotonic 时钟），不用可回退 civil clock。

### 2. 模型与供应链身份（revision 3：提案层冻结，响应意见 2）

**检测器（类级提议者）**：

- 模型：仓库内 `runtime/yoloe/yoloe-11s-seg.pt`（`P1-YOLOE-001` 选定
  的动态视觉提示检查点），SHA-256
  `8e439445c87338b79d9ce21dec109f4621e26df67e94d26ea1a98c1e64dce3e3`；
- 运行时：pinned `ultralytics 8.4.104` + `torch 2.13.0`（现有
  `.venv-yoloe` 栈），入口 `ultralytics.YOLOE` +
  `ultralytics.models.yolo.yoloe.YOLOEVPSegPredictor`（首帧视觉提示，
  与 `tools/yoloe_dynamic_prompt_probe.py` 已验证的 API 相同）；
- **逐候选分数契约**：`Results.boxes.conf`（float，[0,1]，检测置信
  度）；候选框取 `Results.boxes.xyxy` 并按帧宽高归一化。**不使用、
  不宣称任何逐候选实例相似度输出**；
- YOLOE 输出仅为类级候选提议（v0.3.1 §3.2 语义）。

**外观嵌入门（承担 §3.3 ReID 角色的最小实现）**：

- 模型：`torchvision 0.28.0` `resnet18`，权重枚举
  `ResNet18_Weights.IMAGENET1K_V1`（不可变发布版本；下载 URL 与权重
  文件 SHA-256 在冻结时记录入 manifest）；许可证：torchvision
  BSD-3-Clause，权重为 ImageNet-1k 预训练；
- 契约：候选框裁剪 → 该权重枚举自带的官方预处理（224×224 +
  标准归一化）→ 去掉分类头后的全局平均池化 512 维特征 → 与会话锚
  嵌入的余弦相似度；
- **如实声明**：这是通用外观嵌入，非车辆 ReID 专用模型，且面对低多边
  形合成图像存在域差；可行性由 scouting 描述性分离度报告裁定（§8），
  不可行时返回设计决策区（可能指向专用车辆 ReID 选型，作为 M4 升级
  路径另案）；
- 会话身份锚 = 操作员确认初始框的裁剪嵌入（gallery-of-1），会话内
  冻结；不做模板更新/在线学习；
- **权重下载须先取得用户明确同意；接受本设计不等于授权下载**；
- 任一模型缺失/损坏/哈希不匹配、嵌入计算失败一律 fail-closed，不得
  静默降级为纯 SOT 运行。

**运行环境**：再检测通道与嵌入门在 track loop 进程内运行，需要
`.venv-yoloe` 栈（torch/torchvision/ultralytics）与 OpenCV（NanoTrack）
合并为一个记录在案的环境；合并后 `pip check` 与两模型加载冒烟为实现
期证据，无新增推理运行时。

### 3. 三重门、候选歧义与再锚定状态机（revision 3，响应意见 3/4）

每轮再检测绑定其**源帧** `frame_id`，在源帧上产生候选集。

**三道门（全部通过才是控制有效候选 D+）**：

1. **类级门**：`boxes.conf ≥ τ_det`；
2. **嵌入门**：候选裁剪嵌入与冻结会话锚的余弦 ≥ `τ_reid`；
3. **世界系运动门**：候选 LOS 与最近置信锚 LOS 的**世界系角距**
   ≤ `gate(Δt) = min(π, θ0 + ω_max · Δt)`。

**世界系 LOS 构造（意见 4）**：候选框中心像素经源帧
`intrinsics_px`（fx/fy/cx/cy）反投影为相机系射线，再用**该源帧**
`tethered-sensor-frame/v2` 元数据（`camera_rotation_xyzw` 及
`camera_forward/right/up_world` 正交基）旋转为世界系单位向量；角距 =
两单位向量夹角。**禁止比较随云台转动的图像坐标**。`Δt` = 候选源帧
`capture_monotonic_s` 减最近置信锚所在帧的 `capture_monotonic_s`
（帧侧单调时标，非 worker 完成时刻）。相机位姿元数据是已发布传感器
输出，不是 Unity 真值；真值边界不变。

**运动门参数来源（显式、有限、hash-bound 算法参数，意见 4）**：
`ω_max = v_max_target / r_min`。`v_max_target = 4.0 m/s`（通用城市
地面车辆速度上界，与 plant 自身 `maximum_speed_mps` 常数同值；独立
于目标路线真值）；`r_min = 8.0 m`（plant `minimum_altitude_m` 约束
给出的斜距下界）。得 `ω_max = 0.5 rad/s`，`θ0 = 0.1 rad`。controller
不得读取路线或逐帧 Unity 真值构造门。

**最近置信锚刷新规则（意见 4）**：release 时初始化为操作员初始框在
release 帧上的世界系 LOS；此后**仅**在 (a) AGREE 轮次与 (b) 重播种
完成（取 catch-up 头帧的 SOT 框 LOS）时刷新；AMBIGUOUS、DISAGREE、
tentative、no-candidate 轮次一律不刷新。

**候选排序与 tie-break（完全确定，意见 3）**：三门通过者按
(1) 嵌入余弦降序 → (2) 检测置信度降序 → (3) 与最近置信锚世界系角距
升序 → (4) 检测器输出索引升序。

**歧义 margin 规则（意见 3）**：若 ≥2 个候选通过三门且
`top1_cos − top2_cos < m_margin`，该轮判 **AMBIGUOUS**：只落盘
tentative，不产生 DISAGREE，且**重置**连续 DISAGREE 计数（保守）。

**状态机**：

- **AGREE**：D+ 与**同源帧** SOT 框 `IoU ≥ τ_agree` → 仅记录，刷新
  最近置信锚；
- **DISAGREE**：连续 `K` 轮存在无歧义 D+ 且与同源帧 SOT 框不一致，
  且相邻轮次获胜候选**轮间一致**（两轮获胜者世界系角距
  ≤ `ω_max · Δt_rounds + θ_cons`）→ 触发重播种（§4）；两次重播种
  之间最小间隔 `n_min` 轮；
- **tentative 记录**：仅过类级门（或类级+单门）或 AMBIGUOUS 的候选
  一律只落盘，**永不进入控制回路**；
- **无 D+ 的轮次是中性的**（合法 `NO_CANDIDATE`：推理成功且无候选过
  类级门）：仅记录，不累计 DISAGREE、不触发 LOST；**模型/worker/嵌入
  失败不得伪装成中性无候选**（见 §6）；
- **LOST 判定不变**：仍仅由既有框有效性规则触发（非有限/退化/越界）；
  LOST 期间云台保持最后指令（如实记录；几何搜索是 M4 L2a），再检测
  通道持续扫描，无歧义 D+ 直接进入重播种路径并置
  `recovered_from_lost`；
- 对 B2 失败形态的预期作用路径：背景锁定后目标回到近端时，无歧义 D+
  与锁死框持续不一致 → 重播种打破错误平衡；最坏 MTTR 以环周期为界。
  如实预期：远端 ~9 px 裁剪嵌入信息量低，正确再锚定集中在近端路段。

### 4. Frame-consistent 重播种：源帧初始化 + 顺序 replay/catch-up（revision 3，响应意见 1）

**禁止跨帧直接初始化**：检测候选框只在其**源帧**上有效；任何把源帧
框直接用于更晚帧 `init()` 的路径都被移除（revision 2 的"最新帧 + 有界
位移近似"作废）。

**帧历史环形缓冲**：controller 把已消费帧（图像 + `frame_id` +
`capture_monotonic_s` + 相机元数据）保留在内存环形缓冲中，保留时长
`t_buf = 6.0 s`（覆盖最大结果年龄 + catch-up 收敛；20 Hz 下 ≈ 120 帧
≈ 106 MiB @ 640×480×3，桌面可承受，作为显式资源成本记录）。

**重播种过程（全部在异步 worker 上执行，主循环不阻塞）**：

1. 冻结工厂按既有身份校验流程创建并验证**新的** NanoTrack-v2 实例；
2. 在**检测源帧**上以候选框 `init()`；
3. 按 `frame_id` 严格升序 `update()` 重放缓冲中源帧之后的全部帧，
   追到 catch-up 目标 = 主循环最近消费的帧；主循环在此期间继续用旧
   实例前进，重放以多次 pass 逼近（NanoTrack 单帧 p95 3.33 ms ≪ 帧
   周期，收敛有裕度）；
4. **原子替换仅当** 重放头帧 `frame_id` 与主循环最近消费帧 `frame_id`
   **精确相等**时，在两次主循环更新之间执行；替换耗时实测入预算；
5. **丢弃条件（任一即弃，旧实例继续）**：所需中间帧缺失于缓冲、
   重放中任一输出框无效（非有限/退化/越界）、catch-up 未在
   `t_catchup = 2.0 s` 墙钟内收敛、或主循环已越过缓冲保留窗；丢弃发
   `RESEED_DISCARDED_<reason>` 事件；
6. `init()`/重放异常或工厂验证失败 → `RESEED_FAILED` 事件；重播种的
   失败与丢弃进入**连续失败预算 `n_fail = 3`**，超限 fail-closed 终止
   会话并报错；
7. `REANCHOR` 事件记录新旧实例 id、源帧/催齐帧 `frame_id`、三门分数、
   margin、重放帧数与耗时；ready/manifest 增补两模型身份与工厂字段。

### 5. 冻结参数表（revision 3：提案层写死，接触任何新 scouting/资格数据前生效，响应意见 3）

| 参数 | 值 | 预数据理由 |
|---|---|---|
| 再检测节奏 | 2.0 s/轮 | 环周期 106.5 s 的 ~2%，纠错及时且远低于伺服带宽 |
| `τ_det` | 0.25 | ultralytics 库默认置信度阈值（外部库默认，非项目调参） |
| `τ_reid` | 0.5 | 余弦中点保守默认；**声明无外部校准来源** |
| `m_margin` | 0.1 | 保守歧义带；声明无外部校准来源 |
| `τ_agree` | 0.3 | 与 evaluator 跟踪 IoU 阈值同源 |
| `K` | 2 | 最小迟滞（防单轮误检直接重播种） |
| `θ_cons` | 0.05 rad | 轮间一致性残差带，叠加 `ω_max·Δt_rounds` |
| `θ0` / `ω_max` | 0.1 rad / 0.5 rad/s | §3 运动学推导（4.0 m/s ÷ 8.0 m） |
| 最大结果年龄 | 2.0 s（1 周期） | 超龄整轮丢弃 |
| `n_min`（重播种最小间隔） | 2 轮 | 防振荡 |
| `t_buf` | 6.0 s | 结果年龄 + catch-up 裕度 |
| `t_catchup` | 2.0 s | 重放收敛墙钟上限 |
| `n_fail`（连续失败预算） | 3 | 重播种与 worker 各自独立计数 |
| `t_timeout`（单轮推理超时） | 10.0 s | 5× 节奏；超时即失败 |
| 资格节奏达成率下限 | 0.8 | 实际完成轮次/计划轮次，进资格准入 |

全部参数以 strict 配置字段预注册并入哈希冻结链；敏感性（节奏
{1,2,4} s、`τ_agree` {0.2,0.3,0.4}、`τ_reid` 三点、`m_margin` 两点）
仅作描述性报告。**测量数据不得用于反向选参**；验收失败返回设计决策
区，不得调参重试至通过；scouting 分布只裁 go / 返回决策，不改参数。

### 6. 异步 worker 背压与失效语义（revision 3，响应意见 5）

- **至多一个 in-flight 轮次**（单 worker 线程，队列深度 0）；节奏到点
  而 worker 忙 → **丢弃该 tick**（`ROUND_SKIPPED_BUSY`），下一 tick 用
  最新帧重新开始；禁止无界排队；
- 单轮推理超时 `t_timeout` → 放弃该轮并计失败；worker 异常 → 计失败；
  worker 死亡 → 允许一次重启（计失败）；**连续 `n_fail` 次失败 →
  fail-closed 终止会话并报错**；
- **失败与中性严格区分**：合法 `NO_CANDIDATE`（推理成功、无候选过
  类级门）中性；模型加载/推理/嵌入/缓冲异常一律走失败计数，不得记
  为无候选；
- 进程退出：worker 带超时 join，无遗留后台线程、无未完成写入（验收
  直接测试）；
- 每轮实际启动/完成/丢弃时间戳与原因全部落盘；实际达成节奏统计进入
  资格准入（达成率 ≥ 0.8）。

### 7. 真值边界与证据流

- 检测通道与嵌入门输入只有已发布传感器帧（含其相机元数据）与冻结
  会话锚；无 Unity 真值、无 scenario 真值路线读取（沿用既有审计）；
- `frames.jsonl` 新增每轮记录（源帧、完成单调时间、时延、候选数、
  三门分数、margin、判定、事件、丢弃/失败原因）；观测协议状态机沿用
  既有 TRACKING/LOST + `recovered_from_lost`；
- 丢失次数、重播种/丢弃/失败计数、tentative 与 AMBIGUOUS 计数、错误
  重捕获率（evaluator 侧身份门事后判定）、分通道时延分布进入诊断
  指标（设计 §6）。

### 8. 远端召回 scouting 门（Option B 的决策闸）

冻结继任批次前，用验证会话捕获帧（非测量数据）离线量测 YOLOE 对远端
路段可见目标的召回率，并附嵌入分数分布（目标 vs 干扰车）描述性报告：

- 召回 ≥ 0.5（预注册下限，远端可见抽样帧计）→ 锚点几何冻结不变；
- 召回 < 0.5 或嵌入分离度不可行 → 载体在当前几何下不合格，**返回用户
  决策**：锚点向环心重定位（远端斜距 75→~46 m、目标 ~14 px）作为设计
  §6 本就要求变化的场景参数进入新批次，如实记录难度设定变更——
  **不自动改几何**。

### 9. 对继任率研究的协议约束（本项交付建议，另案执行）

- 资格 pilot 必须覆盖 ≥ 1 个环周期（106.485 s）或显式包含远端衰减段；
- 判定规则以 incorrect/matched 与再锚定事件流为连续性判据，不再绑定
  追踪器自报 LOST 的时序（修复 R3′ 空转）；
- **继任协议须包含相同冻结条件下的新采 SOT-only 对照 cell**，对比轴
  命名 `SOT-only → minimal triple-gated re-anchor`（意见 6）；
- 新批次新 run ID（建议 `P1-M2-RATE-003`），B2 编号不复用。

## Inputs, outputs, and affected interfaces

- 新代码（均在 Python 控制器侧）：YOLOE 类级候选通道模块 + 外观嵌入
  门（两模型加载/哈希校验/身份矩阵）、单 worker 异步调度器（单调时
  钟、帧绑定、过期/乱序/忙丢弃）、帧历史环形缓冲、三门/歧义/再锚定
  状态机接入 `track_loop`、冻结工厂 + 源帧初始化 + 顺序重放/催齐 +
  原子替换流程、strict 配置字段；
- 复用不改：帧桥与原子发布、观测/云台协议、`TrackerResult` 契约、
  NanoTrack 插件本体、`CoverageEvaluator` 与 Unity C#（预期零改动）;
- 环境：track loop 进程合并使用现有 `.venv-yoloe` 栈（torch 2.13.0 /
  torchvision 0.28.0 / ultralytics 8.4.104）+ OpenCV；合并环境
  `pip check` 为实现期证据；ResNet18 权重下载需用户先行同意；
- 资源成本显式化：帧缓冲 ≤ ~110 MiB（20 Hz × 6.0 s × 640×480×3）。

## Compatibility with the current v0.3.1 design

- 本项是**用户显式授权（2026-07-28）的有界 M4 子集提前**：保留 §3.2
  三重证据形态（YOLOE 类级提议 + 独立外观嵌入 + 运动似然）的最小单
  假设实现；MHT、view bank、模板在线更新、完整仲裁报告仍归 M4；
- §3.2 语义保持：YOLOE 为类级候选提议者，实例身份由独立外观嵌入门
  承担，正确身份主张（`C_track`）的定义不变；
- §5：显式 LOST/REANCHOR 事件即阶梯入口信号；L1–L4 行为不实现，LOST
  期云台保持最后指令如实记录为 pre-L1 占位；
- §7：对比轴 `SOT-only → minimal triple-gated re-anchor`；正式配对
  对比含新采 SOT-only 对照（继任协议执行）；收益不单独归因给 YOLOE；
- M2 语义保持：云台-only、无机身运动、无世界系 belief、无搜索；
- 真值边界、冻结权重、零微调约束全部不变。

## Acceptance criteria

1. **单元/集成测试（含意见 7 全部新增）**：
   - 异步不阻塞（通道开启时 20 Hz 主循环 compute p95 预算不劣化）；
     节奏按秒与单调时钟调度在 5/20 Hz 下不变性；
   - 三门逐门独立拒绝（类级/嵌入/运动各自不过即 tentative-only）；
     **双候选 margin/tie 确定性**（margin 不足 → AMBIGUOUS 且重置
     DISAGREE 计数；四级 tie-break 完全确定）；
   - **世界系 LOS 门在云台转动下的正确性**：合成相机位姿用例——图像
     坐标接近但世界系角距超门（拒绝），及图像坐标远离但世界系角距
     在门内（通过）；
   - **stale-box 禁止**：断言重播种路径的 `init()` 帧恒等于检测源帧，
     不存在跨帧直接初始化路径；
   - **重放/催齐**：成功路径（源帧 init → 顺序重放 → 头帧相等 → 原子
     替换），与缺帧、超龄、`t_catchup` 不收敛、重放框无效四类失败
     路径（各自 `RESEED_DISCARDED_<reason>`、旧实例继续）；
   - **worker 语义**：忙丢弃（`ROUND_SKIPPED_BUSY`、无排队）、超时、
     异常、死亡重启、连续 `n_fail` fail-closed；**失败 vs 合法
     `NO_CANDIDATE` 的区分**；退出时无后台线程与未完成写入；
   - K 迟滞与轮间一致性确定性；过期/乱序/缓冲缺帧丢弃路径；
     REANCHOR/RESEED_FAILED/RESEED_DISCARDED/LOST 事件完整性；两模型
     缺失/损坏/哈希不匹配 fail-closed；无真值读取审计；
2. **安装与身份冒烟**：YOLOE（`8e439445…dce3e3`）与 ResNet18 权重
   SHA-256/来源/许可证/版本 pin 记录；合并环境 `pip check` 通过；
3. **时延预算**：分通道 p95 实测——detector 轮、嵌入计算、catch-up
   重放、原子替换、主 SOT 循环；通道开启下主循环 p95 仍 < 50 ms
   （CPU/MPS，640×480）；**实际 detector 节奏达成率 ≥ 0.8 作为准入**；
4. **背景锁定打破测试（开发/资格证据，非独立泛化证据）**：冻结的 B2
   20 Hz follow 场景、覆盖 t≈40 s 交接点的 ≥150 s 窗口内：evaluator
   判 incorrect/matched < 0.5，且日志含 ≥1 次三门通过、经完整
   重放/催齐的 DISAGREE 重播种；失败 → 候选被拒、返回设计，不得调参
   重试；
5. **远端召回 scouting 报告**：按 §8 预注册下限给出 go / 返回决策闸
   的明确结论；附嵌入分数分布（目标 vs 干扰车）描述性报告；
6. **资格试跑**：修正场景、20 Hz follow、≥ 1 环周期连续会话：
   `C_track|geom ≥ 0.4`（高于 R1′ 停止线并留裕度）且
   incorrect/matched < 0.5、无 gap/reinit、节奏达成率 ≥ 0.8、错误
   重捕获计数如实报告；
   - **时长修正（`P1-SCENE-004` revision 2，2026-07-29，Codex Round 2
     接受时同步）**：在 SCENE-004 的 benign 短环线场景下，"≥ 1 环周期"
     退化为 ~36 s，低于 B2 实证的 ~40 s 背景锁定发生点，且本提案
     §"协议教训"已记录 30 s 级窗口无预测力。该场景的资格会话改为
     **墙钟 ≥ 150 s 且 ≥ 4 个完整环**（与验收 4 的 ≥150 s 窗口同级）；
     上述其余判据不变。困难场景下的"≥ 1 环周期"（106.485 s）原文保留；
     验收 4 的背景锁定打破测试仍绑定冻结的 B2 困难场景，不迁移到
     benign 场景。
7. **Unity 用例 `UT-P1-DETECT-001-001`**：用户观察资格试跑会话并反馈。

## Baselines and ablations

- **B2 三复测 = 历史探索性 SOT-only 底点**（`C_track|geom`
  0.2388/0.2499/0.2496、incorrect/matched ~0.85）：如实归档为触发本
  设计的正式负结果；**不作为**新协议下预注册 confirmatory 配对消融；
- 正式对比 `SOT-only → minimal triple-gated re-anchor` 由继任协议在
  相同冻结条件下新采 SOT-only 对照完成；**不把收益单独归因给
  YOLOE**；组件消融（YOLOE/嵌入门/运动门分离）如需另行预注册；
- 本项不产出 5/20 Hz 对比数字；率对比归继任研究（建议
  `P1-M2-RATE-003`）；
- 参数敏感性仅描述性；detector-only 基线不在本项。

## Failure modes and resource risks

- **远端小目标召回不足**：验收 5 的 scouting 门直接拦截并返回用户决策
  （锚点重定位 Option B），不烧正式会话；
- **通用嵌入在低多边形合成图像/微小裁剪上分离度不足**：验收 5 的描述
  性分布直接暴露；不可行 → 返回设计决策区（可能指向专用车辆 ReID
  选型或锚点几何），不得静默调参；
- **错误再锚定到干扰车辆**：三门 + margin 歧义带 + 场景显式
  `RateStudyDistractor` 集 + evaluator 错误重捕获率报告；风险如实
  计量，不宣称为零；
- **SOT/检测器振荡**：K 迟滞 + 轮间一致性 + `n_min` 最小间隔；
- **catch-up 不收敛**（推理/重放耗时超预期）：`t_catchup` 墙钟上限 +
  丢弃语义 + 失败预算，主循环永不被阻塞；
- **CPU/MPS 资源竞争与内存**：单 in-flight worker + 预算测试；帧缓冲
  ~110 MiB 显式记录；
- **供应链**：两模型来源/SHA-256/许可证记录，哈希不匹配 fail-closed；
  权重下载需用户先行同意；
- **范围蠕变到 M4**：out-of-scope 清单显式列出（见下）；
- 本项改变模型决策逻辑，属强制 Sonnet 停点。

## Suggested implementation scope

一个实现批次：候选通道 + 嵌入门 + 世界系运动门 + 单 worker 调度/帧
缓冲 + 源帧重放/催齐重播种 + 状态机接入 + strict 配置 + 测试 +
scouting/资格证据。**Out of scope**：MHT、view bank、模板在线更新、
L1–L4 行为（含几何搜索）、机身运动、VLM、锚点重定位的实施（仅决策
闸）、专用车辆 ReID 选型（M4 升级路径）、继任率研究执行、NanoTrack
插件与 CSRT 对照档改动、任何用测量数据选参。

## Codex review

### Pre-verdict scope hold — 2026-07-28

Status: **AWAITING_USER_SCOPE_DECISION**（尚未给出
`ACCEPTED` / `REVISION_REQUESTED` / `REJECTED`）

按仓库规则，本轮不能在未取得用户决定前替项目改写阶段边界和正确身份
主张。当前提案的方向有价值，但存在下列决定前阻塞：

1. **身份语义与正式设计直接冲突。** v0.3.1 §3.2 明确把 YOLOE 视觉提示
   定义为类级候选提议，不承担实例身份确认；自动重捕获必须同时具备
   YOLOE 提议、独立 ReID 和运动似然。提案却把首帧 YOLOE 视觉提示嵌入
   称为会话 `IdentityProfile`，把未定义的“提示相似度”作为身份门，并在
   明确排除 ReID/运动门的同时允许自动重播种。这会把错误候选直接送入
   控制回路，不能在不改正式研究边界的情况下接受。
2. **阶段边界发生提前。** v0.3.1 把 YOLOE 通道、§3.3 仲裁和错误重捕获
   报告放在 M4；本项拟在 M2 关闭前引入控制生效的检测/仲裁子集。用户已
   选择 detector re-anchor 方向，但仍需明确是否授权把一个有界的 M4
   子集提前为 M2 的载体前置条件，以及该子集是否必须保留现行的独立
   ReID + 运动门。
3. **当前本地 YOLOE 路径没有提案所依赖的分数契约。**
   `tools/yoloe_dynamic_prompt_probe.py` 只证明动态视觉提示推理与候选
   数量；它没有定义或验证逐候选“提示相似度”的 API、范围、校准或模型
   身份。修订必须给出真实输出字段、选择公式和预数据阈值来源，或把该
   信号诚实降级为 detector confidence，不能用名称制造实例身份能力。
4. **异步结果缺少帧绑定与过期语义。** 检测器在旧帧上完成时，SOT 已
   继续前进；当前提案没有规定 detector source frame、完成时单调时间、
   最大结果年龄、乱序结果丢弃、与当前 SOT 框的同帧比较方式，以及旧框
   如何传播到可重播种帧。直接用“最新 D+”会破坏现有 frame-bound
   observation 契约。`2.0 s` 挂钟还必须明确使用同主机单调时间，不能用
   可回退 civil clock。
5. **重播种不是现有插件上的无条件 `init()`。** 当前
   `NanoTrackV2Tracker` 持有一次初始化的后端实例；修订必须规定由冻结
   工厂创建并验证新实例、在确定帧上初始化成功后原子替换，失败时保留
   旧实例还是 fail-closed，以及该过程对 ready/manifest、延迟、事件和
   `recovered_from_lost` 的精确影响。
6. **B2 只能作历史探索性底点。** 三个 B2 run 是触发本设计的正式负结果，
   可如实归档为 SOT-only 历史基线，但不能事后变成同一新协议下预注册的
   confirmatory §7 配对消融。若后续论文主张正式的
   `SOT-only → SOT+周期 YOLOE` 增益，继任协议应在相同冻结场景、时长和
   准入条件下采集新的 SOT-only 对照。提案的背景锁定测试也属于基于已知
   B2 失败形态的开发/资格证据，不是独立泛化证据。

Codex 建议用户授权的边界是：**允许把有界的周期 YOLOE 候选通道提前为
M2 前置载体，但保留 v0.3.1 的正确身份安全边界；控制生效的自动重播种
必须加入独立 ReID + 运动门，否则本项只能记录 tentative 候选而不得重播种。**
同时把 B2 标为历史探索性 SOT-only 底点，正式 §7 比较另采同协议对照。
若用户反而授权 YOLOE-only 自动重播种，则这是对 §3.2/§3.3 的显式设计
改写，提案必须收窄正确身份主张并重新定义 ID-switch 风险与验收门后再审。

### Fable response — 2026-07-28 (revision 2)

用户已在决策点选定**选项 1**（有界 YOLOE 候选通道 + 独立 ReID/运动门）
并确认 B2 历史定位。Revision 2 已按六点阻塞项修订正文：

1. §2/§3 重写：YOLOE 降为类级候选提议者，"提示相似度"删除；实例身份
   由新增的冻结 ReID 嵌入门承担，运动门按 scenario 运动学界推导并随
   失联时长膨胀；三重门不齐只记 tentative，永不重播种；
2. 授权链记录用户对有界 M4 子集提前的显式授权与保留 ReID+运动门的
   边界；
3. 分数契约诚实化：detector confidence（类级）+ ReID 余弦（实例）,
   均有真实来源；ReID 下限声明无外部校准来源、保守预注册、描述性
   敏感性；
4. 新增 §4 异步帧绑定/过期语义：源帧绑定、同源帧比较、单调时钟、
   最大结果年龄 1 周期、乱序/缺帧丢弃、重播种帧确定性与有界位移
   近似的如实记录；
5. 新增 §4 重播种机制：冻结工厂新实例 + 确定帧初始化 + 原子替换 +
   失败保留旧实例 + 连续失败 fail-closed + ready/manifest/事件影响；
6. 基线章节重写：B2 = 历史探索性底点；正式 §7 配对对比由继任协议
   新采 SOT-only 对照；背景锁定测试改标为开发/资格证据。

等待 Codex 对 revision 2 的正式 verdict。

### Round 1 — 2026-07-28: REVISION_REQUESTED

Decision: **REVISION_REQUESTED**

Revision 2 正确落实了用户选定的边界：YOLOE 只作类级提议，任何控制生效
的重播种都必须通过独立 ReID 与运动门；它也删除了虚构的提示相似度，
补上同源帧比较、单调时钟、工厂新实例与 B2 历史探索性定位。这些方向性
问题已经关闭，不需要再次请求用户授权。

但 revision 2 仍不是可冻结实现的设计，原因是以下模型决策和时序语义仍
留给实现期自由选择，其中第一项会直接制造错误重播种：

1. **禁止把源帧候选框直接用于最新帧初始化。** §4 当前把最多 2 s 前的
   图像框原样用于最新帧；目标可移动约 4 m，云台也会在这段时间转动，
   因而“地面位移有界”不能保证归一化图像框仍覆盖目标。Revision 3 必须
   选择一个严格 frame-consistent 方案。建议在 detector 源帧上初始化新
   tracker，再按 `frame_id` 顺序重放所有保留的中间帧，追到一个冻结的
   catch-up frame 后才在两次主循环更新之间原子替换；任一帧缺失、追赶
   超龄、主流继续前进而无法收敛或 replay 结果无效都丢弃该次重播种。
   另一可接受方案是只在候选框与初始化框属于同一确切帧时替换，但不得
   用“最新帧近似”跨越该契约。
2. **在提案中选定具体模型与完整身份，而不是留到实现期。** Revision 3
   须指定一个确切的 ReID 模型/权重版本、不可变来源、许可证、输入尺寸、
   归一化、嵌入与余弦计算契约，以及现有 PyTorch YOLOE 的确切模型、
   predictor 和 detector-confidence 字段。下载仍须先取得用户同意；
   接受设计不等于授权下载。
3. **冻结全部控制有效参数与候选歧义规则。** 在接触新的 scouting/
   资格数据前写死 `τ_det`、`τ_reid`、第二候选/distractor margin、
   运动门公式和上限、候选排序与完全确定的 tie-break、K、轮间一致性
   公式/阈值、最小重播种间隔、结果年龄和失败预算。若多个候选同时过
   三门但身份 margin 不足，必须 tentative-only；不能由实现任意选择
   “获胜候选”。参数可声明无外部校准，但必须给出预数据理由。
4. **把运动门定义在明确的坐标与时间语义上。** 跨帧角距必须由各源帧
   相机元数据得到同一世界系单位 LOS，不能比较随云台转动的图像坐标；
   失联时长使用帧的 `capture_monotonic_s`，不是 worker 完成时刻。目标
   速度上界、最小斜距等只可作为显式、有限、hash-bound 的算法参数传入，
   并说明独立来源；controller 不得读取路线或逐帧 Unity 真值来构造门。
   同时精确定义“最近置信锚”何时刷新以及歧义时不刷新的规则。
5. **补齐异步 worker 的背压与失效语义。** 规定最多一个 in-flight
   round，周期到达但 worker 忙时是 coalesce 还是 drop、禁止无界排队；
   规定推理 timeout、异常、worker 死亡、取消和进程退出清理。合法的
   `NO_CANDIDATE` 可以中性，但模型/worker/嵌入失败不能伪装成中性无候选，
   必须进入有界失败计数并最终 fail-closed。实际启动/完成/丢弃节奏均
   落盘并进入资格准入。
6. **修正 §7 研究归因标签。** 本项包含 ReID 和运动门，因此不是纯
   `SOT+周期 YOLOE` 第二档，而是用户授权的“最小安全三门载体”。正式
   报告不能把相对 SOT-only 的收益单独归因给 YOLOE。Revision 3 应把
   本项及继任对比命名为 `SOT-only → minimal triple-gated re-anchor`；
   若以后要分离 YOLOE、ReID、运动门贡献，另行预注册安全的组件消融，
   完整 view-bank/模板管理仍留在 M4。
7. **把上述语义加入验收。** 测试至少覆盖 stale-box 不能跨帧直接
   init、源帧 replay/catch-up 成功与缺帧/追赶失败、云台转动下世界系
   LOS 门、双候选 margin/tie、worker 忙/超时/崩溃、错误与真实
   no-candidate 的区分、退出时无后台线程或未完成写入。时延报告必须同时
   给出 detector/ReID worker、catch-up replay 和主 SOT 循环，并验证
   20 Hz 主循环及实际 detector cadence 的准入门。

Revision 3 满足以上七项后可回到 Codex 正式复审。当前不得进入运行时代码、
下载 ReID 权重、创建继任率批次或使用新的 scouting/资格帧选参。

### Fable response — 2026-07-28 (revision 3)

Revision 3 已逐项响应 round 1 七项返修，全部落在正文：

1. **Frame-consistent 重播种（§4）**：跨帧直接初始化路径删除；采用
   Codex 建议方案——源帧 `init()` + 按 `frame_id` 顺序重放 + 头帧
   精确相等才原子替换；缺帧/超龄/不收敛/无效框四类丢弃语义 + 失败
   预算 fail-closed；新增 6.0 s 帧历史环形缓冲并显式记录内存成本；
2. **模型提案层冻结（§2）**：YOLOE = 仓库内 `yoloe-11s-seg.pt`
   （SHA-256 `8e439445…dce3e3`）+ ultralytics 8.4.104
   `YOLOEVPSegPredictor`，分数契约 `Results.boxes.conf`；嵌入门 =
   torchvision 0.28.0 `ResNet18_Weights.IMAGENET1K_V1` 512 维
   penultimate 特征 + 官方预处理 + 余弦；域差如实声明，下载须用户
   先行同意；
3. **参数与歧义规则冻结（§5 参数表 + §3）**：全部控制有效参数含预
   数据理由写死；四级确定性 tie-break；margin 不足 → AMBIGUOUS →
   tentative-only 且重置 DISAGREE 计数；
4. **运动门坐标/时间语义（§3）**：源帧相机元数据（v2 字段列名）反
   投影世界系单位 LOS；Δt 用 `capture_monotonic_s`；`v_max`/`r_min`
   为显式 hash-bound 参数并给出独立来源；置信锚刷新/不刷新规则
   精确化；
5. **worker 背压/失效（§6）**：单 in-flight、忙丢弃不排队、超时/
   异常/死亡重启/连续失败 fail-closed、失败与合法 NO_CANDIDATE 严格
   区分、退出清理、实际节奏落盘并进资格准入（≥ 0.8）；
6. **归因标签（标题/研究价值/§9/基线）**：全文改称"最小安全三门
   载体"，对比轴 `SOT-only → minimal triple-gated re-anchor`，收益
   不单独归因 YOLOE，组件消融另行预注册；
7. **验收补齐（验收 1/3）**：stale-box 禁止断言、重放成功/四类失败、
   云台转动下世界系门双向用例、双候选 margin/tie、worker 忙/超时/
   崩溃/退出、失败-中性区分、分通道时延与节奏达成率准入全部入测试。

等待 Codex 对 revision 3 的正式复审。未动运行时代码、未下载权重、
未启动 scouting。

### Round 2 — 2026-07-28: ACCEPTED_WITH_BINDING_CLARIFICATIONS

Decision: **ACCEPTED_WITH_BINDING_CLARIFICATIONS**

Revision 3 关闭了 Round 1 的全部七项阻断：重播种重新满足 exact-frame
契约；YOLOE/外观嵌入身份、分数契约和控制参数已预数据冻结；候选 margin、
世界系运动门、worker 背压/失败语义和测试义务均可证伪；研究标签也已诚实
改为 `minimal triple-gated re-anchor`。本项可以进入实现，但以下说明具有
绑定效力：

1. **交换检查必须原子。** “replay 头帧等于主循环最近消费帧”的读取、
   比较和 tracker 指针替换必须在同一个主循环更新边界/临界区完成；帧
   缓冲条目在发布给 worker 后不可变。先无锁检查、后延迟替换不满足
   exact-frame 契约。
2. **线程 timeout 不等于可强杀。** Python worker 仍存活时不得启动替代
   worker，任何时刻最多一个。超时后若 worker 不能在有界 join 内确认
   终止，主线程必须完成可完成的原子日志/终态写入并终止本次 tracker
   进程；不得继续以纯 SOT 测量，也不得声称线程已被取消。一次 restart
   只允许在旧 worker 已确认退出后发生；后台 worker 不直接写 JSONL，
   所有持久化由主线程串行完成。
3. **固定反投影与 release 锚语义。** top-left 图像坐标的相机射线固定为
   `normalize(((u-cx)/fx)*right_world - ((v-cy)/fy)*up_world +
   forward_world)`；元数据的 quaternion 与正交基必须有限、归一且相互
   一致，否则该轮 fail-closed。运动锚在 acknowledged release 帧上取
   **该帧当前 SOT 框**的 LOS；operator 初始框只生成冻结外观嵌入，不得
   被假装成 release 帧框。
4. **运动包络是预注册启发式，不是真值保证。** `4.0 m/s` 与 `8.0 m`
   保持冻结，但文档/实现不得把 `drone.maximum_speed_mps` 或最低飞行
   高度误称为目标速度/相机到目标框中心的严格物理界；它们是用户接受
   的显式保守算法参数。controller 仍不得读取目标路线或逐帧真值。
5. **供应链证据先于模型使用。** 获得用户下载许可后，首次加载
   `ResNet18_Weights.IMAGENET1K_V1` 前必须记录确切官方 URL、文件大小、
   完整 SHA-256 与覆盖权重 artifact 的肯定许可证证据；torchvision
   代码的 BSD-3-Clause 不能自动代替权重许可证。缺失或歧义时实现门
   fail-closed 并返回用户，不进入 scouting。
6. **计数器与准入分母必须确定。** worker/reseed 两个连续失败计数器
   分开；各自在本通道一次完整成功后归零，`NO_CANDIDATE` 不算失败但也
   不替另一通道清零。cadence 达成率分母为 acknowledged release 后所有
   计划 tick，忙跳过/超时/失败均留在分母，完成且未超龄的 round 才进
   分子。

正式设计仅同步以上接受边界；这不是实现或独立复核通过。该 work item
改变模型决策与帧时序，完成实现者测试后必须形成提交并停在 Sonnet 稳定
候选门。接受本设计不授权下载 ResNet18 权重；在用户明确允许前不得开始
模型获取、scouting 或依赖该模型的运行时实现。

## Amendment A1 — 外观嵌入模型更换：DINOv2 ViT-S/14（ACCEPTED）

Status: ACCEPTED (Codex Round 2, 2026-07-28)
Author: Claude Fable

### 触发与授权

- 绑定澄清 5 的供应链门对 `ResNet18_Weights.IMAGENET1K_V1` fail-closed：
  制品 `resnet18-f37072fd.pth` 已按授权下载并哈希（未加载），但
  torchvision 官方文档与仓库均只声明"预训练模型可能有自己的许可或源自
  训练数据集的条款，由使用者自行确认"，**不存在覆盖该权重制品的肯定
  授权**（`docs/evidence/P1-DETECT-001-resnet18-supply-chain-gate.md`）；
- **方向 1（提供 ResNet18 权重的权威许可依据）经查证不可得**：官方
  来源即是免责声明本身，Fable 不制造不存在的许可依据；
- 用户 2026-07-28 授权 Fable 准备模型选型修订（方向 2），本 amendment
  即该修订。

### 替换范围（最小改动）

仅替换已接受正文 §2"外观嵌入门"的模型与契约条款、验收 2/3 中对应的
模型身份行、以及 manifest 中的嵌入模型字段。**不变**：三门结构与状态
机（§3）、frame-consistent 重播种（§4）、参数表 §5（`τ_reid=0.5`、
`m_margin=0.1` 作为沿用的未校准保守默认，不主张跨模型分布或阈值
等价；敏感性仍仅描述性）、worker 语义（§6）、绑定澄清 1–4/6 全部
原文有效；澄清 5 的证据门语义不变，逐字适用于新制品。

### 新模型与供应链身份（revision 2：全部在提案层冻结，响应 A1 意见 1/2/3）

**模型与权重制品**：

- **模型**：DINOv2 `dinov2_vits14` —— **无 registers**、LVD-142M
  预训练的 ViT-S/14 backbone（~21M 参数，patch size 14，嵌入 384 维），
  Meta AI 官方发布；
- **权重制品**：
  `https://dl.fbaipublicfiles.com/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth`
  （backbone-only 检查点）；下载门记录确切文件大小与完整 SHA-256，
  **先于任何反序列化**（澄清 5 语义）。

**代码身份（提案层写死，意见 2）**：

- Pinned commit（完整 40 位）：
  **`7764ea0f912e53c92e82eb78a2a1631e92725fc8`**（`main`，2026-06-03，
  "Safely load weights from specified URLs (#598)"）；
- Commit-pinned 权威链接：
  - 仓库树：
    `https://github.com/facebookresearch/dinov2/tree/7764ea0f912e53c92e82eb78a2a1631e92725fc8`
  - README（含许可声明）：
    `https://github.com/facebookresearch/dinov2/blob/7764ea0f912e53c92e82eb78a2a1631e92725fc8/README.md`
  - LICENSE：
    `https://github.com/facebookresearch/dinov2/blob/7764ea0f912e53c92e82eb78a2a1631e92725fc8/LICENSE`
  - 官方变换源码：
    `https://github.com/facebookresearch/dinov2/blob/7764ea0f912e53c92e82eb78a2a1631e92725fc8/dinov2/data/transforms.py`
  - MODEL_CARD：
    `https://github.com/facebookresearch/dinov2/blob/7764ea0f912e53c92e82eb78a2a1631e92725fc8/MODEL_CARD.md`
- **许可证文件哈希（Fable 2026-07-28 对 commit-pinned raw LICENSE
  实测）**：11,359 字节，SHA-256
  `600cc67cc4cb2f5ea317dcfc687ad1c74dc4bec8782bbe9db0afd83513b935b7`
  （Apache License 2.0 全文）；
- **肯定许可证据**：该 commit README 明文 "DINOv2 code and model
  weights are released under the Apache License 2.0"；HF
  `facebook/dinov2-small` 模型卡 license 标签 `apache-2.0`。
  **证据快照须显式区分**：同仓库 XRay-DINO / Cell-DINO 专用权重为
  FAIR Noncommercial Research License，不在本选型内；
- 用户下载许可取得后：源码 archive/checkout 在**首次导入前**记录实际
  大小与完整 SHA-256；运行时只能从该本地副本离线导入。

**离线构造与加载契约（意见 3）**：

- 架构构造：从本地 pinned 副本导入，调用
  `dinov2/hub/backbones.py` 的 `dinov2_vits14` 入口并强制
  `pretrained=False`（仅构造无 registers 的 ViT-S/14 架构，全部构造
  kwargs 取该 commit 该入口的默认值，不触网）；**禁止
  `torch.hub.load` 及任何隐式网络路径**；
- 权重加载顺序：先对本地检查点做 size + 完整 SHA-256 校验（哈希
  先验），通过后 `torch.load(local_path, map_location="cpu",
  weights_only=True)`（当前 pinned torch 2.13.0），再
  `model.load_state_dict(state_dict, strict=True)`，最后
  `model.eval()`；任一步失败 fail-closed；
- **特征输出契约**：`torch.no_grad()` 下前向，嵌入 =
  `model.forward_features(x)["x_norm_clstoken"]` —— 最终 LayerNorm
  后的 CLS token，**384 维**（该 commit 下与 identity-head `model(x)`
  等价）；嵌入必须全有限且范数非零后才计算余弦，否则按 §6 失败路径
  计数（`EMBED_INVALID`），**不得伪装成中性无候选**。

**预处理契约（意见 1：与 pinned commit
`make_classification_eval_transform()` 默认值逐项一致）**：

- 输入构造：候选框先裁剪到帧边界；BGR 帧缓冲裁剪 → **显式 BGR→RGB
  转换** → PIL RGB uint8 图像；
- 变换管线：`Resize(256, interpolation=InterpolationMode.BICUBIC)` →
  `CenterCrop(224)` → ToTensor（uint8 [0,255] → float32 [0,1]）→
  `Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))`；
- **antialias 冻结**：官方变换未显式传 `antialias`；本契约冻结 PIL
  输入路径——torchvision 0.28.0 对 PIL 输入的 bicubic Resize 恒定
  抗锯齿，行为确定；实现不得改走 tensor-Resize 路径；
- **退化/空 crop fail-closed**：裁剪与帧边界交集为空、或整数化后
  宽 < 2 px 或高 < 2 px、或变换输出含非有限值 → 该候选以
  `CROP_INVALID` 从候选集确定性剔除（逐候选记录；不是 worker 失败；
  剔除后剩余候选照常走三门；若本轮曾有类级门通过者、但全因 crop
  无效被剔除，则记录 `TENTATIVE_CROP_INVALID`，不得伪装成仅适用于
  “无候选过类级门”的合法 `NO_CANDIDATE`）；
- **时延**：ViT-S/14 224² CPU/MPS 单次前向预计数十至百余 ms；异步
  2.0 s 节奏下可容，实测进验收 3，主循环预算与节奏达成率准入不变。

### 如实声明（revision 2：按 A1 意见 4 收窄）

- 仍非车辆 ReID 专用模型；官方 MODEL_CARD 将 nearest-neighbor image
  retrieval 列为已评估用途，**但这不构成其在本项目低多边形合成车辆
  实例上更强的证据**；本项不作任何跨模型能力比较主张，适用性与收益
  **唯一**由 scouting 分离度报告与资格证据裁定（§8/验收 5/6）；
- `τ_reid=0.5` 与 `m_margin=0.1` 保留，但定位为**沿用的未校准保守
  默认**：不主张 ResNet18 与 DINOv2 的分数分布或阈值语义跨模型等价；
  scouting 显示不可行时返回设计决策区，不得就地调参；
- 嵌入维度由 512 变为 384，仅影响 manifest 记录，不影响任何阈值语义。

### 被阻断制品的处置

`runtime/models/resnet18-f37072fd.pth` 保持未加载、路径 ignored；
阻断证据文件永久保留；实现批次首个动作删除该文件（或按 Codex 卫生
决定保留原样注记），任何加载路径不得触及它。

### 已考虑并排除的备选（避免重提死路）

- torchvision 任何 ImageNet 权重：官方明确不提供肯定授权——死路；
- `timm/resnet18.a1_in1k`（HF 卡片 apache-2.0 标签）：第三方维护者
  对 ImageNet 派生权重的卡片标签，授权强度弱于 Meta 对自有模型的
  明文声明，特征质量亦无优势——不选。

### 下载许可边界

Amendment 接受不等于授权下载。Codex 接受 A1 后，下载
`dinov2_vits14_pretrain.pth` 与 pinned hub 代码前，须再次取得用户
明确同意；ResNet18 的既有下载同意不迁移到新制品。

### Amendment A1 Codex Round 1 — 2026-07-28: REVISION_REQUESTED

Decision: **REVISION_REQUESTED**

DINOv2 标准 ViT-S/14 是可行替代方向。Meta 官方 README 明确说明
DINOv2 代码和模型权重以 Apache-2.0 发布，根 LICENSE 是 Apache-2.0；
官方 model card 同时确认 ViT-S 为 384 维、patch size 14，并列出
nearest-neighbor image retrieval 用途。A1 对 XRay-DINO/Cell-DINO
特殊非商业权重的排除也是必要且正确的。以下四项仍阻断接受：

1. **预处理契约写错插值算法。** A1 写 `resize 256 (bilinear)`，但
   DINOv2 官方 `make_classification_eval_transform()` 默认是
   `InterpolationMode.BICUBIC`，随后 center crop 224、ToTensor 和
   ImageNet mean/std。Revision 必须选择并冻结一个契约；若继续称
   “官方变换”，应改为 bicubic，并写明 torchvision 0.28.0 的
   antialias 行为、RGB 转换、像素缩放和退化/空 crop fail-closed。
2. **代码身份尚未冻结。** “实现时记录 pinned commit”仍让被接受设计
   指向会移动的 `main`。Revision 必须写入完整 40 位 Git commit SHA、
   commit-pinned repository/tree/README/LICENSE URL，以及许可证文件
   SHA-256。实现下载许可取得后，源码 archive/checkout 还须在首次导入
   前记录实际大小和完整 SHA-256；运行时只能从该本地副本离线加载。
3. **加载与特征输出契约不够精确。** Revision 必须固定无 registers 的
   `dinov2_vits14` LVD-142M backbone，构造参数及本地加载路径；不得让
   `torch.hub` 隐式联网。应明确权重先作 size/SHA-256 校验，再以
   `weights_only=True`（当前 pinned torch）反序列化并 strict
   `load_state_dict`；嵌入是 eval/no-grad 前向返回的最终 LayerNorm 后
   `x_norm_clstoken`/`model(x)` 384 维向量，须有限且非零后才计算余弦。
4. **阈值和能力主张须收窄。** 相同的余弦值域不代表 ResNet18 与
   DINOv2 的分数分布或 `0.5` 阈值语义相同。可以在接触项目数据前保留
   `τ_reid=0.5`，但必须标成“沿用的未校准保守默认”，明确不主张跨模型
   标定等价，失败仍返回设计决策。官方 model card 支持通用检索用途，
   但不足以证明本项目低多边形车辆实例上“公认更强”；删除该比较性结论
   或给出直接、适用的预数据依据，并保持收益由 scouting/资格证据裁定。

Revision 只需修正上述冻结与主张问题；三门、worker、replay、主指标、
阶段边界和 Round 2 bindings 1–4/6 不需重开。Round 2 binding 5 在 A1
接受后应改写为 DINOv2 的 commit-pinned 代码与标准权重制品证据门。
在 A1 复审接受且用户另行授权下载之前，不下载 DINOv2 源码/权重，不加载
任何新模型，不启动实现或 scouting。ResNet18 制品继续 ignored、未加载。

### Fable response — 2026-07-28 (A1 revision 2)

四项阻断已全部在 amendment 正文修订：

1. **预处理契约改为与 pinned commit 官方源码逐项一致**：bicubic
   插值（修正原 bilinear 笔误）、CenterCrop 224、ToTensor 像素缩放
   [0,255]→[0,1]、ImageNet mean/std；antialias 以冻结 PIL 输入路径
   确定化（torchvision 0.28.0 对 PIL bicubic 恒定抗锯齿），禁走
   tensor-Resize 路径；显式 BGR→RGB；空/退化 crop（交集空、宽或高
   < 2 px、非有限输出）以 `CROP_INVALID` 逐候选确定性剔除；
2. **代码身份提案层写死**：完整 commit
   `7764ea0f912e53c92e82eb78a2a1631e92725fc8`，commit-pinned
   tree/README/LICENSE/transforms/MODEL_CARD 五个链接，raw LICENSE
   实测 11,359 字节 / SHA-256 `600cc67c…35b7`（Apache-2.0 全文）；
   下载许可取得后源码副本首次导入前记录实际大小与完整 SHA-256，
   运行时仅离线导入本地副本；
3. **构造/加载/输出契约冻结**：本地副本 `dinov2_vits14` 入口
   `pretrained=False` 构造（无 registers、该 commit 默认 kwargs、
   禁 `torch.hub.load`）；哈希先验 → `weights_only=True` +
   `map_location="cpu"` → `strict=True` `load_state_dict` →
   `eval()`；嵌入 = no-grad `forward_features(x)["x_norm_clstoken"]`
   最终 LayerNorm 后 384 维，非有限/零范数走 `EMBED_INVALID` 失败
   计数，不伪装中性；
4. **主张收窄**：删除"公认更强"比较性结论，MODEL_CARD 的检索用途
   只作用途记录不作域内证据；`τ_reid=0.5`/`m_margin=0.1` 改标"沿用
   的未校准保守默认"，明确不主张跨模型标定等价，适用性唯一由
   scouting/资格证据裁定。

等待 Codex 对 A1 revision 2 的复审。未下载 DINOv2 源码/权重（许可
哈希来自对 commit-pinned raw LICENSE 文本的直接抓取核算，未入库、
未导入），未启动实现或 scouting；ResNet18 制品维持 ignored、未加载。

### Amendment A1 Codex Round 2 — 2026-07-28: ACCEPTED

Decision: **ACCEPTED**

Revision 2 关闭了 Round 1 的四项阻断：

1. commit-pinned 官方变换确认使用 bicubic，并已冻结 PIL/RGB、
   256→224、ToTensor、ImageNet normalization 与无效 crop 语义；
2. 官方代码身份冻结到完整 commit
   `7764ea0f912e53c92e82eb78a2a1631e92725fc8`。Codex 独立核验该 commit
   及标题，并对其 raw LICENSE 复算为 11,359 字节、SHA-256
   `600cc67cc4cb2f5ea317dcfc687ad1c74dc4bec8782bbe9db0afd83513b935b7`；
3. 无 registers 的 LVD-142M ViT-S/14 本地构造、hash-before-load、
   `weights_only=True`、strict load、eval/no-grad 与 384 维最终
   LayerNorm 后 CLS 输出均已可证伪；禁止 hub/隐式网络；
4. 跨模型能力与阈值等价主张已删除；两个数值只作为未校准的沿用默认，
   项目域适用性仍由预注册 scouting/资格证据裁定。

接受时同步确定一个既有状态机解释：合法 `NO_CANDIDATE` 仍只表示推理成功
且没有候选通过类级门。若已有类级候选但全部 `CROP_INVALID`，必须记录
`TENTATIVE_CROP_INVALID`，不计 worker 失败，但也不得记作
`NO_CANDIDATE`。这保持失败/中性诊断可区分，不改变三门控制语义。

Round 2 binding 5 自此替换为：用户另行授权后，首次导入 pinned DINOv2
源码或反序列化标准 `dinov2_vits14_pretrain.pth` 前，必须记录
commit-pinned 源码副本的大小/完整 SHA-256、权重官方 URL/大小/完整
SHA-256、上述 LICENSE identity 与 README 对标准 DINOv2 代码/权重的
Apache-2.0 肯定授权；证据须排除 XRay-DINO/Cell-DINO 特殊权重。任一
缺失/不匹配/歧义均 fail-closed。Bindings 1–4/6 原文继续有效。

这是设计接受，不是下载授权、实现完成或独立复核通过。下一步仍须用户明确
授权下载 pinned 源码与 DINOv2 标准权重；授权前不得获取新制品、开始依赖
实现或 scouting。实现形成稳定候选后仍必须提交并停在 Sonnet 复核门。

## Capture Amendment A2 — validation-only truth-directed follow

### Fable clarification and user authorization — 2026-07-28

§8 已冻结“20 Hz follow”验证会话，但 plain Unity Play 的云台默认为
nadir，原实现未绑定 follow 驱动源。使用历史 SOT 驱动会把已知漂移写入
远端可见样本集合，使用本项 re-anchor 驱动又会让待裁定系统生成自己的
可行性数据，二者都污染 scouting 的检测/嵌入可行性问题。用户授权
validation-only Unity truth-directed follow，并冻结四项约束：

1. 仅在有效的 `p1-detect-scouting`、`non_measurement=true` 会话身份下
   启用；路径留在 Unity 侧，controller 零引用审计扩展到新身份字段，
   其他身份或缺失字段 fail-closed；
2. 只能调用现有 `TetheredGimbal.LookAtWorld` 执行器，保留 45° off-nadir
   限位、slew 与 saturation，不得绕过物理可达视场；
3. manifest 与每帧 truth sidecar 固定记录
   `gimbal_driver=truth_directed_scouting`；外部
   `GimbalCommandReceiver` 必须不存在或被 Unity 侧显式禁用并记录；
4. scouting 结果把 recall 标为
   `ORACLE_POINTED_DETECTABILITY_UPPER_BOUND`，明确
   `closed_loop_recall_claimed=false`。闭环可行性仍只由验收 6 资格会话
   裁定，不得把本上界报告写成 closed-loop recall。

### Codex review — 2026-07-28: ACCEPTED

Decision: **ACCEPTED**

四项约束关闭了 follow 驱动源未绑定这一结果决定性缺口，同时保持 §7
controller 无真值、§8 recall 数值规则、锚点几何、模型与阈值全部不变。
truth 仅用于非测量验证会话的相机指向上界；检测器与嵌入器仍只读取发布的
传感器帧。实现必须覆盖错误/缺失 driver identity、外部云台命令屏蔽、
现有 45° plant 限位、manifest/sidecar 身份链、离线报告上界标签及
controller 零引用。该项改变采集控制协议，形成稳定候选后必须停给 Sonnet；
复核通过前不得准备或采集真实 scouting session。

## Recovery Amendment A3 — versioned bbox-schema reanalysis

### Fable recommendation and user authorization — 2026-07-28

首个真实 `analyze` 结果暴露跨语言 schema 缺陷：Unity truth sidecar 把
非空框序列化为 `{x,y,width,height}` 对象，而 Python 离线端把它直接传给
只接受四元素序列的验证器，导致 27 个远距 target crop 全部被误记为
`CROP_INVALID`，结果 SHA-256 `c7876364…f8b4` 缺少必须的嵌入分布。用户
授权以下窄恢复路径：

1. 原无效结果不得覆盖、删除或冒充完成结果；以明确 hash 和原因永久保留；
2. parser 只接受两种 schema：键集合**恰为**
   `{x,y,width,height}` 且四值均为有限 JSON number 的对象，或四元素有限
   number 序列；其他形态 fail-closed；
3. 修复同时覆盖 IoU 与 target/distractor embedding，补对象、序列、
   缺键、多键、非数值、bool、退化/越界和 `null` 路径测试；
4. 重分析使用新的版本化 identity；create-once supersession receipt 必须
   同时绑定原结果 hash、新结果 hash、reason 与 reanalysis plan hash；
5. 至少一个 fixture 必须从真实保留 capture 的 sidecar **byte-for-byte**
   提取并锁定 SHA-256，避免再次以手写双端 fixture 掩盖契约断裂；
6. 只重算同一不可变 capture；不重采、不回填缺失 sidecar、不改阈值、
   几何、采样或自动 go/no-go 语义；形成候选后停给 Sonnet。

用户随后提供的 Unity Console 截图显示恰好 63 次
`invalid_scouting_distractor_truth`，与 capture 恰好缺 63 个 truth
sidecar 一一对应。writer 允许 `null`，而缺失段两侧合法 distractor 框都
贴图像边界，因此根因是 `ProjectBounds` clamp 后的 float 算术偶发让
`x+width`/`y+height` 仅以舍入量越过 1，随后被无容差验证拒绝。A3 同时
纳入写入侧防御：只规范化不超过 `1e-5` 的右/下边界舍入越界，任何更大
越界、非有限、负值或退化框继续 fail-closed。既有 63 个缺失 sidecar
仍按预注册规则计 recall miss，不据此授权重采或真值回填。

### Codex review — 2026-07-28: ACCEPTED_WITH_BINDING_CLARIFICATIONS

Decision: **ACCEPTED_WITH_BINDING_CLARIFICATIONS**

该 amendment 修复实现契约而不改变核心研究主张、主指标、几何、阈值或
阶段边界。Codex 接受 Fable 的版本化 identity、supersession receipt 和
真实 fixture 三项证据门，并增加两条实现绑定：

1. 原 `scouting-result.json` 保持字节不变；A3 结果、plan、receipt 均使用
   独立 create-once 路径，A3 close 必须验证两代结果及 receipt hash 链，
   不允许旧 close 路径把无效结果签成 A3 completion；
2. Unity 容差只适用于 `[0,1]` 内合法 origin/正尺寸框的右/下端点舍入，
   最大修正 `1e-5` normalized（640 px 下小于 0.0064 px），并用“微小越界
   接受规范化 / 实质越界仍拒绝”的直接 Edit Mode 回归锁定。

这是实现授权，不是恢复结果或独立复核通过。Codex 必须先完成 Python 与
Unity 测试、提交稳定候选并停给 Sonnet；Sonnet 通过前不得运行真实
`reanalyze-a3`、不得 close、不得重采。

## Clock Amendment A4 — shared-host monotonic frame protocol

### Codex diagnosis and user authorization — 2026-07-29

首次 benign qualification `p1-detect-001-qual-1` 在 0 s fail-closed：
普通 `tethered-sensor-frame/v1` 没有 `capture_monotonic_s`。RATE-002
专用 v2 也不能复用，因为 Unity 的 `Time.realtimeSinceStartupAsDouble`
是 Editor 进程相对时钟，而重锚 worker 的 Python `time.monotonic()` 是
主机系统单调时钟；结果年龄路径直接相减会把所有结果误判为 stale。用户在
退出 Play 后明确授权修复时钟协议。

修复绑定如下：

1. 普通传感器帧升级为 `tethered-sensor-frame/v3`，同时发布有限非负
   `capture_monotonic_s` 和精确身份
   `capture_monotonic_clock_id=system-stopwatch/v1`。Unity 值取自
   `System.Diagnostics.Stopwatch.GetTimestamp()/Frequency`；当前冻结的
   macOS/Unity Mono 环境已用跨进程探针确认其与 Python
   `time.monotonic()` 共用 `mach_absolute_time()` 主机 epoch。
2. RATE-002 专用 v2 和 `Time.realtimeSinceStartupAsDouble` 语义保持
   不变；`--rate2-session` 与 `--reanchor-config` 显式互斥。任何 v1、
   v2、缺字段、非有限值、负值或错误 clock ID 在重锚路径 fail-closed。
3. 初始化帧 schema、clock、frame ID 和 scenario ID 必须在创建 tracker、
   加载 detector/embedder、分配 run ID 或创建 run 目录之前通过。运行时
   重锚入口再做一次相同校验，防止绕过 CLI。
4. 离线 scouting 只读端继续接受历史 v1，并接受经过完整 clock 校验的
   v3；Gate 0 的冻结旧字节探针继续只读 v1。不得重写历史 capture。
5. 模型/权重、三门阈值、stale 上限、主指标、真值边界、场景几何、
   RATE-002 历史和资格门全部不变。失败的 qual-1 ID 永久消耗，不得复用。

### Codex review — 2026-07-29: ACCEPTED

Decision: **ACCEPTED**

A4 修正的是原接受设计中未真正绑定同一 epoch 的跨进程时间接口。v3 的
schema + clock identity 让结果年龄比较可证伪，前置与运行时双重门避免再次
在模型加载和运行目录创建后才发现协议错误；v2 隔离保留了已关闭 RATE-002
证据语义。该修复不改变研究主张、阶段边界、主指标、硬件目标、模型身份或
任何决策阈值。由于它触及帧/时间与模型决策语义，实现形成稳定候选后必须
停止并交 Sonnet 新一轮独立复核；通过前不得准备或运行新的 qualification。

## Release Boundary Amendment A5 — non-RATE qualification barrier

### Codex diagnosis and user authorization — 2026-07-29

`p1-detect-001-qual-2` 验证了 A4 的跨进程时钟，但暴露资格流程仍无
non-RATE release 边界：tracker 在 Unity 暂停期间消费的 retained frames
进入了测量相位，operator confirmation gap 被重锚 cadence 记为 977 个
planned ticks，且最终 tracker window 只有 149.415 s 新鲜 post-resume
capture。该 run 永久保留为
`PROTOCOL_INVALID_RELEASE_BOUNDARY`，不得用描述性通过项追认。

Codex 明确说明该修复触及 phase、duration/cadence 与主资格门，必须在实现
后形成新的 Sonnet 停点；用户随后以“好的继续下一步吧”明确授权以下窄
修复，不授权准备或运行 qual-3：

1. 新协议仅用于 `P1-DETECT-001`、`p1-scene-004`、follow、
   NanoTrack-v2 + 已接受 re-anchor 的 non-RATE 资格会话；run ID 必须为
   `p1-detect-001-qual-N`，并与 RATE-002/v2 严格互斥。
2. tracker 在初始化帧、模型和 re-anchor 初始化成功后发布 create-once
   ready。Unity 暂停期间由独立 `--release-qualification RUN_ID` 命令生成
   create-once release command；command 必须晚于 ready 的 Unix 与共享
   host-monotonic 时间，并通过 manifest/ready/command SHA-256 链绑定。
3. command 的
   `not_before_capture_monotonic_s` 之前的初始化/retained/backlog 帧全部
   标为 `hold`：允许 SOT 顺序追上 retained stream，但不发布 observation
   或 gimbal command，不释放 re-anchor，不进入资格 duration、cadence、
   event denominator 或最终 evaluator 指标。
4. 第一个满足
   `capture_monotonic_s >= not_before_capture_monotonic_s` 的普通 v3
   live frame 是唯一 release origin。该同一帧原子确定 tracker ack、
   simulation elapsed、host-monotonic wall elapsed、re-anchor released
   phase、control/observation publication 和 Unity evaluator origin。
5. Unity 只在 `CoverageEvaluator` 内读取 hash-bound active marker 和
   command；首次 release 时清空所有 pre-release truth aggregation，再从
   同一 release frame 记主指标。`metrics.json` 必须写入 run/command/
   marker hash、release frame 与两项 origin；Python 只接受与 ack 完全
   相符且 evaluator duration 达标的 snapshot。真值仍不得进入 controller。
6. 完成同时要求 release-origin simulation span 与共享 host-monotonic
   wall span均 ≥150 s；summary 的 wall duration 以 monotonic span 为主，
   Unix span只保留审计。缺失/篡改/跨 run/短时 metrics、重复协议、释放后
   replay 或不同 active marker 均 fail-closed。
7. active marker 仅在 provenance、达标 metrics snapshot 与 summary
   成功后清理；run-local ready/command/active/ack/provenance 永久保留。
   qual-1/qual-2 继续已消耗，A5 通过 Sonnet 前不得准备 qual-3。

模型、权重、三门阈值、stale 上限、主指标公式、场景几何、硬件目标和
acceptance 6 的数值门均不改变。

### Codex review — 2026-07-29: ACCEPTED

Decision: **ACCEPTED**

A5 只修复资格会话缺失的运行相位边界，并把 Python 控制/重锚日志与
`CoverageEvaluator` 主指标锁到同一 v3 首帧；它没有用 qual-2 的描述性
结果修改任何性能阈值或主指标公式。create-once hash 链、双时长门、
metrics-origin 反向校验和失败后保留 active marker，使漏标、跨 run、
旧 metrics 或操作暂停都不能静默成为有效资格证据。Unity truth 仍只在
`CoverageEvaluator` 内计算。

由于 A5 改变帧/控制 phase 和主资格 duration/cadence gate，实现候选必须
提交并推送后停给 Sonnet 独立复核；Codex 不给自己的实现签发独立通过，
复核前不得准备或运行 `p1-detect-001-qual-3`。

### Round 7 B2 implementation binding — stale marker session scope

Round 7 confirmed A5's intended release chain but found that its retained
top-level active marker was being evaluated by every later
`CoverageEvaluator` session. A failed attempt intentionally retains that
marker, so a different scene could throw and an ordinary new SCENE-004
session could silently adopt the old run identity.

The accepted A5 meaning is clarified without changing its clean-session
release semantics:

1. each `QualificationReleaseGate` records the current Unity evaluator
   session's Unix and shared host-monotonic start times;
2. it may arm only when the referenced release command was issued strictly
   after **both** starts and the marker scenario matches the current exact
   `p1-scene-004` session;
3. a foreign-scene, malformed, missing-chain or older marker is inert for that
   Unity session: disposition remains `Ordinary`, observations remain allowed,
   aggregation is not reset and no qualification identity enters metrics;
4. once a marker passes session freshness and scenario ownership, the original
   full command/hash/manifest/ready validation remains fail-closed; no clean
   A5 chain, duration, threshold or metric rule changes;
5. a retained failed-attempt pointer still blocks creation of a different
   qualification release transaction until explicitly preserved/cleared. It
   cannot block or relabel unrelated Unity work.

Direct regressions must cover both Round 7 reproductions: no exception in a
different scenario and no reset/foreign metrics identity in a later ordinary
SCENE-004 session. The fixed candidate returns to the same Sonnet stop; qual-3
remains unprepared.
