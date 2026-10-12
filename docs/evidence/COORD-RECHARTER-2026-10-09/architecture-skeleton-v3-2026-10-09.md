# 架构骨架 v3（2026-10-09）

取代 v2。吸收 GPT 对 v2 的一致性审查（四处必改、三组契约、探针与模式口径），并按用户意见把**所有具体数字改为参数，由具名测试产生**。两处代码事实已核：`designate()` 在 BOUND/BOUND_COASTING 时会调 `follow()` 改指针并写 coasting，不是纯查询；128 帧历史每帧已存相机位置、旋转、内参、时间、全部轨迹行（含 lost 池预测行与状态）和已删 ID，缺未关联的原始检测。

## 0. 相对 v2 的变化

- 恢复窗口与三帧收养解耦：一个恢复截止 T_repair，云台预测追视截止 T_pred 与报告截止 T_report 各自不晚于它；N_adopt 与 T_repair 之间有结构约束。
- 连续性状态只能经转换函数改变；DISPUTED/BROKEN 在当前 episode 内不能被普通观测事件转回 SUPPORTED。
- 控制授权改为独立纯函数，组合表补全。
- designate 拆为纯解析 resolve 与写入 follow；follow 只在 commit_binding 内调用；三条绑定路径按来源分流。
- 在线可判定结果与离线真值归因分开命名。
- 历史材料契约与 KF 回放起点写明。
- TaskSpec 合法组合校验；首次捕获截止与 REARM 等待预算分开；尝试号不是 episode 号；九态外壳是投影。
- 事件日志加序号、接受/拒绝与效果序号；发布前复核版本与观测年龄；迟到效果不复活。
- 模式改为正交配置轴。
- 准入结果三态 PASS/FAIL/INCONCLUSIVE；wrong_unique 含选错物理实例。
- **数字全部进第 9 节参数表**，正文只写结构约束。

## 1. 不变量

1. 轨迹编号可以换，任务不能偷换：TaskSpec 只由操作者改，改即新 intent_revision。
2. 任何候选成为可执行目标前，必须经 commit_binding 说明：由谁选择、基于哪一帧、如何接到当前帧、是修复原实例还是开始新实例、当前证据授权哪些控制。
3. 预测可以继续，身份结论不因预测续期；恢复截止从最后一次可靠观测起算，不因结果返回、候选出现、弹窗刷新。
4. 新实例必须记作新 episode，不伪装成修复。
5. 「候选里没有」不等于「画面里没有」；「未知」不等于「已核实」；范围与时刻随结果一起记录。
6. 真值只进离线评分；在线结论的命名不得超出运行时能知道的内容。
7. 每条关键契约写明四件事：谁能写、依据什么写、何时失效、被拒绝后保证什么没变。

## 2. 五层职责

同 v2：操作者层呈现与采集带版本的选择；任务层推进阶段、决定问人/发查询/接受提案/授权控制；语义层对指定快照给判断；感知与估计层给观测、补偿、预测、诊断和门限数值；控制层执行获准的 AimIntent 并报告受限原因；平台层不动。控制接口为 `AimIntent(world_point, covariance, estimate_time, source, valid_until, task_revision, episode_id, association_revision)`。

## 3. 四条记录

```
TaskSpec（操作者批准，不可变）
  selector: 点击(x, y, frame_id, image_sha) | 谓词(闭集词表)
  binding_mode: INSTANCE | PREDICATE
  activation: NOW | WAIT_UNTIL_MATCH
  on_ambiguity: ASK
  on_loss: ASK | REARM_WITH_NEW_INSTANCE
  initial_capture_deadline        首次捕获截止
  rearm_wait_budget               仅 REARM 允许时存在，可为无限
  success_condition               在线可判定表述，见 §11

TaskRuntime（系统推进，reducer 唯一权威）
  phase: WAITING | ACQUIRING | TRACKING | PREDICTING | DISPUTED | LOST | DONE | CANCELED
  attempt_no                      捕获尝试号，不是 episode 号
  pending_request, pending_choice
  deadlines: 恢复截止、请求截止、提案有效期、看门狗、当前尝试截止

BindingRecord
  target_episode_id, track_key, association_revision
  relation: INITIAL | CONTINUITY_REPAIR | USER_RESELECT | ATTRIBUTE_REPLACE
  evidence_refs

TargetBelief
  mean, covariance（地面 [px, pz, vx, vz]）
  filter_snapshot_at_last_reliable   供修复回放
  last_accepted_observation
  observation_status: OBSERVED | PREDICTED | STALE
  continuity_status: SUPPORTED | TENTATIVE | DISPUTED | BROKEN
  semantic_status: SUPPORTED | UNKNOWN | CONTRADICTED
  geometry_valid, observation_age_frames, control_reachability
```

**合法组合**（构造时校验）：INSTANCE+ASK 合法；INSTANCE+REARM 非法；PREDICATE+ASK 合法；PREDICATE+REARM 合法。点击来源不得在无谓词时自动构造「等待符合描述的新实例」任务。谓词任务默认继续跟当前 episode，只有规定的丢失条件才触发新捕获，不逐帧换更近的匹配对象。

**截止**：initial_capture_deadline 只管首次捕获；每次合法 REARM 建立新尝试及其截止，取自 rearm_wait_budget；轮询、候选出现、弹窗不刷新；旧实例的身份恢复窗口不因此延长。

**九态外壳是投影**：现有九态与 `designation_id` 由 reducer 状态映射生成，映射表随实现冻结；不维护第二套推进逻辑。名称分类：WAITING_FOR_CHOICE 是阶段加 pending_choice 的派生呈现；CONTINUITY_REPAIR 是绑定事件；EXPIRED_NO_CAPTURE 是尝试结果；TRACKED_BUT_LIMITED 是跟踪阶段上的执行限制；MISSED_OPPORTUNITY 是一次机会的处理事件，不终止任务。

## 4. 状态转换与控制授权

**转换函数唯一改 continuity_status**，任何分支不得直接赋值。合法边：
- SUPPORTED → TENTATIVE（本帧原 ID 框不过门，或未匹配进入预测）
- TENTATIVE → SUPPORTED（原 ID 或暂定候选过门并经 commit）
- TENTATIVE/SUPPORTED → DISPUTED（出现无法消解的竞争）
- 任意 → BROKEN（超恢复截止）
- **DISPUTED/BROKEN → SUPPORTED 只能经操作者重选并建立新 episode**；普通观测事件不能转回，也不能更新当前 episode 的最后可靠观测时间、恢复截止或控制权限。
- 处理顺序：先判「该 episode 还允许自动恢复吗」，再判「这一个框合理吗」。

**授权函数** `derive_authorization(task, binding, belief, health, now) -> body_mode, gimbal_mode, valid_until, reason_codes`，纯函数，显示等级由它派生：

| 组合 | body | gimbal |
|---|---|---|
| OBSERVED + SUPPORTED + 无未解决竞争 + 语义非 CONTRADICTED | 过几何与执行约束后 FOLLOW | 观测估计 |
| OBSERVED + TENTATIVE | HOLD（显式写出） | 观测估计，限时 |
| PREDICTED + SUPPORTED/TENTATIVE，未超 T_pred，协方差未超上限 | HOLD | 预测估计，限时 |
| OBSERVED + DISPUTED/BROKEN | HOLD | 不朝未确认候选追 |
| 有效 CONTRADICTED 证据 | HOLD | 进入冲突处理 |
| UNKNOWN 且实例由点击确定 | 不因缺标签停止 | 同上行按其他状态 |
| STALE 或无新帧但旧状态为 OBSERVED | 按观测年龄重判，不保留旧权限 | 同左 |
| 控制到限位或被裁剪 | 记 CONTROL_LIMITED，不记丢失 | 同左 |

降级必须显式写 hold，因为旧速度命令还有过期期。

## 5. 回路

### 5.1 reducer 与事件日志

`reduce(state, event, frozen_config) -> (new_state, effects)`。感知运行与 VLM 运行只产生观测事件和结果事件；reducer 消费已确定的事件内容。每条事件记 `event_seq, event_type, event_time, payload | payload_ref, accepted|rejected 及原因, effect_seq`。被拒绝的迟到结果、停止前后排队的控制效果都要有事件，即使没有引起状态转换。可重放的定义：给定相同观测、模型返回、操作者事件、时间事件和配置，重现相同决策与效果序列；不承诺重跑推理得到相同数值。

处理顺序：停止/替换任务与到期事件 → 消费异步结果 → 新帧观测与关联诊断（先判 episode 可恢复性，再判框）→ 评估提案 → 原子 commit_binding → 生成 AimIntent 与授权、界面反馈 → 启动异步工具。无新帧时第 1、2、6 步照常。

### 5.2 发布前复核

每次实际写出前检查效果仍对应当前有效任务、episode、关联版本，并重新检查观测年龄与授权；已生成的效果不因晚写出而重获完整有效期；停止后写出 hold，之后到达的旧效果必须被丢弃。内部撤权时刻、hold 写出时刻、Unity 实际停止时刻是三个不同指标，分别记录。

### 5.3 异步结果接入

验证请求与任务版本 → 在原快照解析选择（纯）→ 建立从 k 到 N 的证据链（§7）→ 检查断证、竞争、未批准切换 → 检查当前新鲜观测与执行条件 → commit_binding。恢复截止不从返回时刻重算。人工确认引用 proposal_id，返回后重验到当前帧的连续性，失败则请求重选。

### 5.4 持久任务

默认解释与 v2 同。绑定条件：一次合格语义证据 + 候选到当前帧的连续性 + 若干帧真实检测稳定（参数 N_stable），再按确认策略绑定；准入线未过前保留一次点击确认。调度：新稳定候选触发加低频轮询兜底，只保留一条最新等待查询，合并限频。只监视当前视场。

## 6. 绑定提交与三条路径

- **resolve_designation(box, k)**：纯解析，返回六值闭集与候选，不改指针、不写 coasting。现有 `designate()` 的解析逻辑保留，副作用部分移出。
- **commit_binding(proposal, expected_versions, source_snapshot, evidence_chain, relation)**：唯一写入口。校验任务与绑定版本、阶段、截止、relation 合法性；同步提交快层指针（调 `follow()`）、BindingRecord、TargetBelief；产生绑定事件。拒绝时三者皆不变，不留半提交。
- 路径按来源分流：

| 情况 | 路径 |
|---|---|
| 尚未绑定，来源选择可连续追溯到当前 | assess_new_acquisition → INITIAL |
| 已有绑定，同 episode、恢复截止前 | assess_continuity_repair → CONTINUITY_REPAIR |
| 来源选择到当前的证据链已断 | 拒绝，要求当前帧重选；不靠旧世界点附近唯一候选补身份 |
| 谓词任务 REARM 取得新有效选择 | assess_new_acquisition → ATTRIBUTE_REPLACE，新 episode |
| 操作者重选 | assess_new_acquisition → USER_RESELECT，新 episode |

旧 acquire 通道保留的是入口与执行能力（世界点转向、到位判据），不保留「旧位置附近唯一即收养」的身份规则。

**assess_continuity_repair** 四门同 v2（马氏运动门加车辆运动上限、尺寸对数残差、语义三态、无竞争且无历史争议），外加预测协方差上限与时间上限；N_adopt 的定义：同一暂定候选在 N_adopt 个不同新观测帧过门、期间无竞争、提交不晚于恢复截止。**assess_new_acquisition** 不要求与旧实例空间连续；通过后重建 TargetBelief。

## 7. 证据链与 KF 回放

**历史材料契约**：每帧保存同帧位姿与内参、时间、全部轨迹行（含 lost 池预测行与状态）、已删 ID；若证据链需要，补未关联原始检测。VLM 返回后只对被选候选及其邻近竞争者做有界历史验证，不遍历一串相同 ID 就算证据。现有 128 帧深度是否够用由回放测试 R-5 给出。

**KF 回放**：暂定修复期间正式 KF 只预测不更新；TargetBelief 保留最后可靠状态的滤波快照；通过后从快照按各观测时间依次预测与更新，再推进到当前时刻，结果与绑定一起提交。不向当前状态倒灌旧测量。

## 8. 时限结构

| 时限 | 起点 | 结构约束 |
|---|---|---|
| T_repair 自动连续性修复截止 | 最后可靠观测 t0 | 唯一恢复截止 |
| T_pred 无观测时云台预测追视截止 | t0 | ≤ T_repair |
| T_report 明确报告「无新观测」 | t0 | ≤ T_repair |
| N_adopt 与 T_repair | | N_adopt × Δt + 一帧无候选容忍 + 处理与调度余量 ≤ T_repair，否则修复在结构上不可能完成 |
| 边界顺序 | | 到期事件先于同刻到达的证据处理；收养必须在截止前完成提交，第三份证据在到期事件之后处理即拒绝 |
| 看门狗 | 最近收到新帧 | 报 SENSOR_STALE |
| 前台语义请求 T_fg | 入队 | 迟到结果不执行 |
| 提案有效期 | 提案生成 | 不延长身份窗口 |
| 尝试截止 | 尝试开始 | 不被轮询刷新 |

时钟：本机单调时钟；不相减两机单调值；记录用名义帧时间还是接收时间；接收后处理延迟不冒充曝光到执行延迟。

## 9. 参数表：全部由测试产生

正文不写数值。每个参数给结构约束、产生它的测试、首次回放用的占位值（占位只为让测试能跑，不是默认）。

| 参数 | 结构约束 | 产生它的测试 | 占位 |
|---|---|---|---|
| Δt 帧间隔 | 传感器 5 Hz | 已知 | 0.2 s |
| T_pred | ≤ T_repair | R-1：回放中预测框与下一次真实观测 IoU ≥ iou_pred 的持续时长分布，取 p90 | 3 帧 |
| T_repair | ≥ N_adopt·Δt + 余量；≤ 目标出画时间的下界 | R-2：转向后原目标重新稳定出现的间隔分布，取覆盖 p90 可恢复间隔的值 | 5 帧 |
| T_report | ≤ T_repair | 与 T_repair 同测；用户可读性由演示反馈定 | = T_repair |
| N_adopt | ≥ 2 | R-3：有相似干扰车时误收养率对 N 的曲线，取误收养率低于 r_adopt_max 的最小 N；无干扰场景前只能占位 | 3 |
| N_stable 持久任务检测稳定帧数 | ≥ 1 | R-3 同源 | 2 |
| χ² 门 g_motion | 二维卡方分位 | R-4：真实延续的 NIS 覆盖率校准，覆盖率接近名义值才有效 | χ²₂(0.99) |
| 车辆运动上限 v_car_max | 场景车辆最大速度加余量 | 场景配置 | 由场景读 |
| 协方差上限 P_max | 使马氏门不退化 | R-3：误收养率随 P 的曲线 | 占位 = 带宽² |
| 尺寸残差门 g_size | 对数比值 | R-4：真实延续在转向中的分布 p99 | 占位 ±0.5 |
| iou_pred | | R-1 校准用 | 0.3 |
| R_floor 模型误差下限 | 非零 | R-4：框底中点对真值地面点的残差分布 | 占位 1 m² |
| 角步长上限 ω_step | 与帧率、框大小、预测误差匹配 | R-2：不同步长下关联断裂率 | 占位 3°/帧 |
| T_fg 前台语义请求 | ≥ 板上 p95 + 传输 | 板上 measure 收据 | p95 × 1.3 |
| 轮询周期 | ≥ 单次服务时间 | 板上 measure | 3 s |
| 准入线与比较线 | 见 §15 | 探针 | 测前固定 |

**产生数字的回放测试清单**（零 Play；R-1、R-2、R-4 可用 10-08 诊断根的 540 到 600 帧及其位姿与真值离线做，需加载一次 YOLO；R-3 需要有相似干扰车的新素材）：
- R-1 预测可用时长；R-2 转向后恢复间隔与角步长敏感度；R-3 误收养率对 N 与 P；R-4 NIS 覆盖率、尺寸残差、框底点残差；R-5 历史深度与字段是否足以重建证据链。
- 参数由测试产生后冻结进配置哈希，进日志。

## 10. 语义层接口与调度

同 v2，补三条：B 的范围声明同时约束 unique、ambiguous、none；on_ambiguity 的判断范围须与任务约定一致；结果带来源帧 k，是 k 帧范围内的判断，不是当前时刻全图保证。首版任务解释用界面模板生成 TaskSpec；自由语言生成持久任务另立接口与评估。

## 11. 在线结论与离线归因分开命名

| 在线可记录 | 离线评分才能确认 |
|---|---|
| 获准绑定的目标在规定证据条件下连续居中 t_center（success_condition 的在线表述） | 被跟物理实例确实正确 |
| EXPIRED_NO_CAPTURE，reason = NO_SUPPORTED_MATCH_OBSERVED | 目标始终未出现，还是出现过被漏掉 |
| 模型输出 NONE / 选了编号 j / 结果过期 / 来源不可追溯 | 模型选错、检测器漏检、候选生成丢掉正确目标 |
| 用户拒绝了提案 | 提案客观错误还是用户改主意 |

在线错误类型只保留：结果过期、版本失效、来源不可追溯、连续性不成立、超时、用户拒绝、系统错误。「模型语义错误」「候选覆盖失败」只在离线归因中出现。

## 12. 最低日志

v2 的逐帧、状态转换、语义请求三类保留，加 §5.1 的事件序号、接受/拒绝、效果序号；绑定变化记 old_track_key → new_track_key 与 relation；配置哈希进每条转换事件；命令写出记 command_written，不记 applied。

## 13. 配置轴

```
latency_profile      无注入 | 指定注入
confirmation_policy  显式实验配置
auto_repair          开 | 关
diagnostics          最低日志 | 扩展诊断
```

同一策略函数，配置冻结进日志。测量必须含无注入的真实基线；关闭 auto_repair 的对照可与任意其他轴组合。

## 14. 契约测试（零消耗，冻结前必过）

| 输入 | 必须结果 |
|---|---|
| 已锁存争议，下一帧原 ID 又匹配且创新很小 | 不清除争议，不恢复机身跟随 |
| 已超恢复截止，旧 ID 未被库删除并重新出现 | 不以原 episode 自动续跟 |
| 一帧无候选，随后 N_adopt 个新帧同一合格候选 | 配置允许且提交未超时则修复 |
| 第 N_adopt 份证据在到期事件之后处理 | 拒绝，不复活旧 episode |
| 首次选择的历史链已断，旧世界点附近出现唯一候选 | 不走修复，不自动接受 |
| 评估或提交被拒绝 | 指针、BindingRecord、TargetBelief 均不变 |
| 停止后到达旧 VLM 结果和旧控制效果 | 不绑定、不重发跟随；hold 不被覆盖 |
| 无新帧但异步事件持续到达 | 观测过期，不续发旧目标运动命令 |
| N_adopt 帧通过后提交 | KF 从快照回放，不向当前状态倒灌 |
| 同一事件流重放两次 | 状态转换、拒绝原因、绑定关系、效果序列一致 |
| INSTANCE + REARM 构造 | 拒绝 |
| 点击来源无谓词构造等待任务 | 拒绝 |

## 15. 探针口径

- 本轮用现有 609 行分组比较 A 与 B；三态各 160 是重跑生成器后的目标。
- 准入结果三态：PASS / FAIL / INCONCLUSIVE。零错误的单侧 95% 上界：48 行约 6.05%，100 行约 2.95%，160 行约 1.85%；相关场景片段不能按独立样本解释。本轮可以选出 A 或 B，同时把「取消确认」判为证据不足。
- wrong_unique 定义：输出 unique 且（画面真实语义状态不是 unique，或所选物理实例不是唯一匹配目标）。分组报错误率，另报自动提交中的错误绑定比例；不能靠多拒绝把风险做低。
- 评分链四项同 v2；比较线与准入线分开，测前固定。

## 16. 关口与待用户

已定八条：v2 七条加「designate 拆分、follow 只在 commit_binding 内」。仍待用户：主线文字入账；第一轮一次 Play 与一次 YOLO 离线回放额度（R-1/R-2/R-4/R-5 共用这次加载）；第二轮板上查询额度；R-3 所需相似干扰车素材即场景改动项；共驻未测前作品集对部署能力的表述。
