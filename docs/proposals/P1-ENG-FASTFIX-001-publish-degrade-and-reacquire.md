# P1-ENG-FASTFIX-001 — 快层一轮必要修正：发布门失败降级为丢帧、重建后自动重捕、门值重核、监控移出关键时序、逐阶段耗时

Status: ACCEPTED
Revision: D2
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（工程轨道 Opus 池，supervisor 派发子代理，MacBook Air；D1 Dispatch-Id `P1-ENG-FASTFIX-001-D1-20261010T222946Z-e09a`；D2 Dispatch-Id `P1-ENG-FASTFIX-001-D2-20261010T224619Z-a784`）
Created: 2026-10-10
Last updated: 2026-10-12

> **来历**：用户 2026-10-10 指示下一 supervisor 会话接续快层修复、以 CAPTURE 离线诊断为输入开新工作项（账本同日「全局 — 用户方向：下一 supervisor 会话继续快层修复…」，该条不授权代码、Play、模型或任何额度，不恢复 CAPTURE）；同日「全局 — 用户定重新构思待决『属性分类器是否允许』」作参考（本项不涉 VLM 与分类器，见 §2.3）。输入 = `docs/evidence/P1-ENG-CAPTURE-001-offline-diagnosis.md`（下称**诊断**）§1–§6 与 `docs/parked-status.md`「P1-ENG-CAPTURE-001 收口与保留义务（2026-10-10）」。D2 依据 = 本文「D1 接受裁定」AR1-1…7 与账本「2026-10-10 P1-ENG-FASTFIX-001 — 用户答 D1 退修转呈七题：全部按推荐，信封粗粒度」（下称**七题答复**；效力读法以账本为准，落实由接受角色核对）。
> **D2 已接受**：`Workflow: engineering-v1` 生效，字面合同含文末「D2 接受裁定」首次接受释义；§5 原申请与历史题面保留；阶段 A 主信封已依文末「A首签落实」生效，续修入口为「续做信封落实」，R1历史资源见「R1资源落实」及「R1简化计量落实」，候选4独立R2通过已由接受消费，现行阶段A收口与用户入口为「R2通过消费」；窄修/R2历史合同仍见「返工资源落实」；TX/B/C 仍未签即 0（七题答复本身不签额度）。本次接受审查不改代码、配置、测试、工具，不跑测试。

## 0. 只读事实（MacBook Air，D2 会话，零消耗；源码只 grep/sed 读文本、不导入；符号名为准）

| # | 事实 | 出处 |
|---|---|---|
| F1 | `_gate` **首命中即返回**，顺序：① 快照缺失 → `bundle_missing`；待发布帧 ≠ 最近加载帧 → `catchup_stale`（早于身份核验）；②③ 盘上 JPEG/元数据 → `bundle_missing`/`image_identity_changed`/`metadata_invalid`；④ `latest.json` 读失败/非法 → `bundle_missing`，`delta < 0` → `frame_rollback`，`delta > k_pub` → `catchup_stale`；⑤ `load_elapsed < 0` **或** `> t_pub_s` → `publish_expired`；`capture_unix_s` 缺 → `metadata_invalid`；`capture_age < 0` → `metadata_invalid`；`capture_age > t_stall_s` → `publish_expired` | `controller/gated_publisher.py::GatedPublisher._gate` |
| F2 | 观测/`predicted_look_at` 被拒记 `PUBLISH_REJECTED` 并 `_set_fatal`；观测每次尝试先清 `accepted_frame_id`；衍生通道（`look_at`、速度 `body_command`）无同帧关联 → `orphan_control` 致命，有关联则以该帧重跑 `_gate`，拒绝时「观测已 WRITTEN 的收据不回改」；速度未写出抛 `BodyCommandNotWritten`，由 `_body_step` 走一次显式 hold 回退；`hold` 走不过门的 `body_safety_hold` 安全通道；写失败记 `WRITE_FAILED` 后上抛 | 同文件 `observation`/`predicted_look_at`/`_derived`/`body_command`/`_safety_hold` |
| F3 | `load_monotonic_s` 在读字节、算 sha、写帧环副本**之后**、解码**之前**取值；门的 `load_elapsed` 起点即此刻 | `FrameSnapshotRing.image_loader` |
| F4 | 会话在 `process_available()` 后读 `publisher.fatal_reason` 作 `seg_end` → `_teardown_resident`：先 `_retire_pointer` → `target_manager.release_binding(reason)`（缺省 `cancel_task=True`，任务置 CANCELED），再 `publisher.finalize`、`on_teardown`；`resident_rebuilds += 1` → 有指针时 `REINIT_REQUIRED(seg_end)`；第 3 次需重建 → `stop("rebuild_limit")`；下一 tick 由会话模型缓存重建载体并记 `resident_loop_started(frame_id)`。`_advance_resident` 每 tick 运行，零新帧时也做 `frame_stall` 判定。**无任何自动重捕** | `controller/language_loop.py::_advance_resident`/`_teardown_resident`/`_retire_pointer`；`target_manager.py::release_binding` |
| F5 | `frame_gap`（TrackLoop 终止原因映射）、`frame_stall`（会话看门狗）**不是** `_gate` 返回值；`PUBLISH_REJECT_REASONS`、`PROTOCOL_ABORT_REASONS`、`STATE_REASONS`、`JOURNAL_KINDS` 为闭集，闭集外名字抛错 | `language_bridge.py`；`language_loop.py` 常量区 |
| F6 | `K_PUB = 2`、`T_STALL_S = 3.0` 为 AC-10 修订 1 冻结常数，5 Hz 下 `t_pub = 0.4 s`；捕获模式 `k_pub` 取 `K_PUB` | `language_loop.py` |
| F7 | 目标管理器闭集：`ORIGINS = (click, repair, lang_confirm, lang_acquire)`，`MODE_ORIGINS[capture] = {click, repair}`，`RELATIONS = (INITIAL, CONTINUITY_REPAIR, USER_RESELECT)`；`commit_binding` 是唯一设指针入口（预检 → 计划 → `follow` → 失败 `_rollback`）；`release_binding(cancel_task=False)` 使任务回 `ACQUIRING` 而不取消 | `controller/target_manager.py` |
| F8 | 修复门只用**原绑定键同帧库 prior**（`same_frame_prior`，phase 必为 `KF_PRIOR`）；`motion_size_gate`：S = P_pos + diag((σ_p w)², (σ_p h)²)，半径 √(g_motion·λmax S) ≤ r_gate_max，NIS ≤ g_motion，尺寸 log 比 ≤ g_size；竞争 = 各键连续证据累计 NIS，前二差 < m_nis → DISPUTED；提交用候选同帧 post；无库键检测永不可提交 | `target_manager.py::motion_size_gate`/`_repair_step` |
| F9 | `KfSnapshot` 只存 xywh、速度、2×2 位置协方差；库轨迹另有完整 8 维均值与 8×8 协方差；`apply_pose_center` 只移中心，速度与 8×8 协方差按雅可比 J 变换 | `resident_core.py::KfSnapshot`；`det_assoc_tracker.py::apply_pose_center` |
| F10 | 诊断 §3 表列 **7 行**致命拒绝（含第二 Play 背景 2 行），其汇总句称「全部 6 次」，二者冲突未消解；本提案不用该计数做任何推断。可用读数：已写出发布 load_elapsed p95 0.16–0.18 s、最大 0.33 s；第 647 帧单帧 0.545 s；载体 2 跟踪段处理滞后中位 0.457 s（持续积压） | 诊断 §2、§3 原表 |
| F11 | CAPTURE 冻结目标管理器参数在 `config/p1-eng-capture-001.json` | CAPTURE 提案 §3.7 |
| F12 | **真实模型加载路径闭集**（`grep -rnE "DetAssocTracker\(|_default_model_loader|YOLO\(|YOLOE\(" controller tools tests`）：运行时唯一真实构造 = `det_assoc_tracker.py::_default_model_loader`，会话经 `_SessionModelCache`（每会话 1 次，重建复用）、回放经 `tools/eng_capture/replay.py::CountingModel`（每次运行 1 次）；全套测试中真实构造只有 `tests/test_det_assoc_carrier.py` 两处（`CarrierSelfTest`，`_ready()` 不满足即 skip），其余构造注入替身；CAPTURE 候选 3 全套实测真实构造 2、墙钟 557.7 s。`reanchor_models.py`、`tools/eng_det`、`tools/eng_jet`、`tools/yoloe_dynamic_prompt_probe.py` 不在本项路径 | 源码 grep；`docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md`（全套记录） |
| F13 | CAPTURE 回放一次（加载 1、推理 3,962 帧）墙钟 137.7–146.2 s；缓存帧零推理（`CachedOrLiveModel`，缓存未命中且无 live 即报错） | `docs/evidence/P1-ENG-CAPTURE-001-replay.md`；`replay.py` |
| F14 | formal-redo 原件（Air，只读）：`unity-runtime/frames/` 约 76 MB；会话 `language-session.jsonl` 的 `frames_processed`（`at_monotonic_s`、`at_unix_s`、`frame_ids`、`raw_states`、`metadata_sha256`）与 `click_received`（`frame_id`、`k`、`point`、`image_sha256`）；`publish-receipts.jsonl`（`sequence`、`channel`、`outcome`、`frame_id`、`reason`、`at_monotonic_s`、`at_unix_s`、`detail.{load_elapsed_s, capture_age_s, frame_delta, latest_frame_id, snapshot_sha256}`）。红车点击 k = 584、提交 585，第 647 帧 `publish_expired`，新载体 `resident_loop_started` 于第 650 帧；会话 299.9 s | 本会话只读 ls/解析键名 |

## 1. 目的与价值

主线目标（逐字引用 `docs/project-background.md` §3）：

> 做一个边缘语义目标获取与跟随闭环，VLM 是主角：用户通过点击或语言指定目标，VLM 把语义要求映射到可见候选、承接持久任务，并对歧义与不存在显式报告；快层负责关联与状态估计，只做一轮必要修正，不做研究主张；系统在模型延迟和相机运动下完成捕获、换目标与短时重关联，对观测丢失和不可达显式反馈；部署目标是 VLM 与快层跑在 Jetson Orin Nano 8GB，Unity 留桌面机。

> 随之调整的四条旧约束（逐字同 `docs/evidence/COORD-RECHARTER-2026-10-09/recharter-draft-2026-10-08.md` §2）：
> 1. 「快层是非变量」→「快层只做一轮必要修正，额度一次 Play，不扩成跟踪研究」。用户动机：目标岗位是微调训练或 agent，快层只求能承接 VLM。检测加关联已是成熟件，缺的只是薄的目标管理层，没有现成库。
> 2. 「把 VLM 改为选候选 ID 一律退回」→ 允许作为探针里的对照接口 B，不是切换。含义：接口 A 是 VLM 自己输出框和 frame_id；接口 B 是检测器给编号候选框、VLM 回答第几号符合并报歧义或不存在。放宽理由：板上日志 decode 占一半以上，短输出接口单次约 0.9 s；能分开评估检测器漏检与 VLM 挑错；VLM 仍看全帧、仍做语义匹配。
> 3. 「不改 Unity 场景」→ 可以修正，多辆车运动是方向，具体稍后讨论。
> 4. 「VLM 是主角」→ 保持。含义落在三处：语言到候选的映射并显式报歧义与不存在（微调任务，有评估集与负例）；持久任务与目标管理器构成 agent 回路；量化部署到 Jetson 并用时延数据定接口。不包括两件结构上做不到的事：比点击更快地框已看见的车，逐帧维持实例身份。

本项是约束 1 那「一轮必要修正」在 CAPTURE 终止后的收尾补丁，不是第二轮快层研究。CAPTURE 正式重做的「拐角丢失」经诊断判为：一次处理超时（第 647 帧 0.545 s > 0.4 s）被当作协议错误，主动撤权且不会自动找回（诊断 E1/E2）。主线要求「在模型延迟下完成捕获与短时重关联，对观测丢失显式反馈」——VLM 第二轮会把延迟变得更大更抖，快层若一次尾部越线就丢目标，就承接不了 VLM。本项只做让快层**不因单次延迟主动丢目标、丢了能自动找回或显式报告**的最小改动，并补上定位尖峰来源所需的可观测性。不为快层做研究主张；所有读数只说明本仿真、本参数、本机的工程行为。**Play 次数**：七题答复 PLAY 选 (a)，即用户就本项给出约束 1「一次 Play」的例外——诊断冒烟 1 + 正式 1，仍须随 §5 信封签发后才可动用；CAPTURE 已超耗不抵偿本项额度。

## 2. 范围与不做的事

### 2.1 改动闭集（诊断 §6 五条 → G1–G5）

**只在捕获模式**（`run --language off`）启用 G1–G3；兼容模式（`--language on`）与 `P1-ENG-LOOP-002`/`P1-ENG-ACQ-001` 路径行为逐字不变（AC-12）。七题答复 ROUTE-K2：AR1-1…3 收束后准许捕获模式 G1/G2 安全范围走 engineering-v1，兼容/围栏/真值红线不变（是否生效仍由接受角色在 `ACCEPTED` 时裁定）。

- **G1 发布门失败分级降级**（诊断 §6-1）：捕获模式改用**全量求值**的分级门（§3.1）：完整性类任一命中即现行致命；仅当完整性全部通过、只有时序类命中时，**只丢弃本帧发布**（不置 `fatal_reason`、不拆载体、不动指针/历史/目标管理器），机身经现行路径写恰一次 hold。按最新帧一次结算的连续丢弃计数达 `N_drop` 才升级为现行致命路径。
- **G2 时序升级重建后自动重捕**（诊断 §6-2）：**只在**「时序类升级」导致拆载体且存在可用绑定时，以拆载体前取得的完整 KF 提示，在新载体就绪后的有界窗口内自动重捕（§3.3）；完整性类、`frame_gap`/`frame_stall` 及其他原因拆载体一律不自动重捕，显式报告并等人点击。`auto_reacquire=off` 为对照臂（现行行为）。
- **G3 门值参数化与重核**（诊断 §6-3）：捕获模式的 `t_pub_s`、`k_pub` 改由本项配置读取，首候选与现行常数逐值相同（0.4 s、2 帧，移植限值，不称本机最优）；冒烟后按 §3.4 预登记二选一，用户签值。`T_STALL_S`、`RESIDENT_REBUILD_LIMIT` 不改。
- **G4 采集监控移出关键时序**（诊断 §6-4）：仓库内计量工具（§3.6），停令检查与磁盘采样分离；本项 Play 只用它。
- **G5 逐阶段耗时日志**（诊断 §6-5）：同源时钟、相邻不重叠的分段耗时（§3.5），只进会话日志，不进桥文件。

**预计改动文件闭集**（实现可收窄，扩大须回接受角色）：`controller/gated_publisher.py`、`controller/track_loop.py`（捕获分支帧上下文与计时）、`controller/language_loop.py`（捕获会话、重捕窗口）、`controller/target_manager.py`（重捕状态机、闭集末尾追加）、`controller/language_bridge.py`（闭集末尾追加）、`controller/resident_core.py`（仅当需新增**只读**深复制访问器取完整 KF 状态；不回写库，K3 核对）、新 `config/p1-eng-fastfix-001.json`、新 `tools/eng_fastfix/`、新/扩 `tests/`。`controller/det_assoc_tracker.py` diff 为空（检测耗时由会话模型缓存返回对象的计时包装测得）。

### 2.2 与 CAPTURE 冻结项的关系（不反调；新口径写成新合同）

| CAPTURE 冻结项 | 本项处置 |
|---|---|
| 目标管理器参数与授权表、边界表 | 原值原样复用、`config/p1-eng-capture-001.json` diff 为空；G2 重捕门复用其 σ_p、g_motion、g_size、r_gate_max、m_nis、N_adopt 的**判据与原值**，本项只新增 §3.7 的 **2 个**设计参数（`N_drop`、`T_reacq`）与配置轴 `auto_reacquire`；D1 的 `ρ_reacq` 无算法用途，申请删除，接受侧准许收窄（见「D2 接受裁定」；七题答复未逐字签发删除） |
| AC-17/18/19 帧集、剧本、评分口径 | 不改、不重跑以「过门」；AC-7 是**新合同**：USER-4A 同批原始帧/位姿/CoverageEvaluator 真值经七题答复 SOURCE 限用途扩至本项 AC-7（落实由接受角色核对），新日志独立取证，不引用 CAPTURE 剧本、评分或结论 |
| 正式结果 `FAILED_INCOMPLETE`、AC-23…26 缺项、R1-4/R2-2 OPEN、旧资源偏差/UNKNOWN | 全部保持；本项任何结果不回写 CAPTURE、不销旧缺项、不改旧债状态 |
| 发布门「一次即致命」（LOOP-001 AC-3 修订 1 / AC-13 修订 1） | 仅捕获模式按 §3.1 改为分级；理由：诊断 E2/E3；兼容模式不变，`_gate` 函数体 diff 为空 |
| 原件保全 / 共享槽位 | play/formal/formal-redo 原件只读；AC-8 只取 §3.8 枚举的连续片段与字段，只读复制并核 sha，不移动/覆盖原件，不准入旧评分/旧结论，不读 `m3_body_truth.jsonl` |

### 2.3 明确不做

- VLM 职责、接口 A/B 探针、分辨率取舍（已移到聊天探讨，非决定）；属性分类器（账本 10-10 已定允许，归下一轮 VLM 工作项）；VLM 重训。
- 检测器重训、换权重、改 `conf`/`imgsz`/NMS；换关联器、改 BoT-SORT 冻结参数、加 ReID；推理加速或换框架；持续积压（处理慢于 5 Hz）的根治。
- Unity 脚本、`*.unity`、`config/scenario.*.json`；板端任何动作；K5。
- 兼容模式的任何新行为；`LanguageWorker`、`CandidatesBackend`、`tools/eng_loop2/`。
- 不改 CAPTURE/LOOP-002/ACQ-001 的提案、门值、Gate 行与 parked 记录；不声称尖峰根因已定案。

### 2.4 复用与承接

| 来源 | 判定 |
|---|---|
| CAPTURE `tools/eng_capture/ledger.py` | **不复用**：本项另写粗粒度账本 `tools/eng_fastfix/ledger.py`（§5.0），故 R1-4 **不触发**；若实现最终调用 `ledger.py` 任何函数 → 触发，补 AC-13 R1-4 具名回归 |
| CAPTURE `tools/eng_capture/replay.py` | 只导入 `CountingModel`、`CachedOrLiveModel`、帧读取与缓存键辅助；不调用 `ledger_balance`/`capture_ledger` |
| CAPTURE `tm_inputs.jsonl` 重放（R2-2） | G2 新增输入种类 `reacquire_hint` 与事件进 `tm_inputs` → **确定触发** R2-2 承接（AC-13） |
| LOOP-002 R1-5、ACQ K1K3-R1-1、FRAME-001 R1-3 | 不触发：相关文件 diff 为空（AC-12） |

## 3. 接口与数据契约

### 3.1 捕获模式分级门（G1；K1/K2；回应 AR1-1）

捕获模式新增 `GatedPublisher._gate_classified(frame_id)`；兼容模式继续调用 `_gate`（函数体 diff 为空，首命中语义不变）。`_gate_classified` **不首命中返回**：按下表逐项求值并收集全部命中（快照缺失、`latest.json` 不可读时后续项无法求值，即刻按完整性类结束），用同一次 `monotonic()`/`unix()` 读数：

| 步 | 检查 | 命中 → 原因名（沿用闭集，不新造） | 级别 |
|---|---|---|---|
| 1 | 快照缺失 | `bundle_missing` | 完整性（终止求值） |
| 2 | 待发布帧 ≠ 最近加载帧 | `catchup_stale`，`stale_by=not_latest_loaded` | 时序 |
| 3 | 盘上 JPEG/元数据（`verify_frame_identity`，**不因步 2 跳过**） | `bundle_missing`/`image_identity_changed`/`metadata_invalid` | 完整性 |
| 4a | `latest.json` 缺失/非法 | `bundle_missing` | 完整性（终止求值） |
| 4b | `delta < 0` | `frame_rollback` | 完整性 |
| 4c | `delta > k_pub` | `catchup_stale`，`stale_by=frame_delta` | 时序 |
| 5a | `load_elapsed < 0`（时钟异常） | `publish_expired`，`expired_by=negative_elapsed` | 完整性 |
| 5b | `load_elapsed > t_pub_s` | `publish_expired`，`expired_by=load_elapsed` | 时序 |
| 5c | `capture_unix_s` 缺失 | `metadata_invalid` | 完整性 |
| 5d | `capture_age < 0`（未来采集时刻） | `metadata_invalid`，`detail.capture_age_negative=true` | 完整性 |
| 5e | `capture_age > t_stall_s`（停帧） | `publish_expired`，`expired_by=capture_age` | 完整性 |

- **优先级**：完整性类任一命中 → `PUBLISH_REJECTED`，reason = 按上表顺序**第一个完整性命中**，`detail.hits` 列全部命中（含时序项），`_set_fatal`，与 streak 无关、不经降级；只有时序命中 → `PUBLISH_DROPPED`，reason = 第一个时序命中，`detail.hits` 同列；无命中 → 通过。
- 完整性异常**不能借降级恢复运动**：降级帧不写观测、云台、速度（§3.2），且完整性命中永远致命；兼容模式同一注入仍按 `_gate` 首命中、首拒即致命（AC-1、AC-3）。
- 安全拒绝保持：`body_safety_hold` 与显式 hold 照旧不过门；真实 `orphan_control`（本帧未尝试过观测或预测云台、也未被丢弃却出现速度命令）仍属完整性类致命。
- `frame_gap`、`frame_stall` 与 TrackLoop/会话层异常（`FrameIdentityChanged` 等）不经 `_gate`，行为不变；不属 G1 范围。

### 3.2 帧上下文、恰一次 HOLD 与按帧结算（G1；K1/K2；回应 AR1-2）

捕获分支在每个**本批最新帧**（B7）处理开始调用 `publisher.begin_frame(frame_id)`、末尾调用 `publisher.settle_frame(frame_id)`；旧帧不开上下文、不发命令、不计 streak。同帧通道按现行顺序：观测（OBSERVED 时）→ 云台（`look_at` 衍生或 `predicted_look_at`）→ `_body_step`。

| 路径 | 本帧收据 | 机身 | 帧结算 |
|---|---|---|---|
| 观测时序命中 | 观测 `PUBLISH_DROPPED`；其后同帧云台/速度不再求值、不写，记 `PUBLISH_DROPPED(dropped_with_frame)` | 速度未写 → `BodyCommandNotWritten` → 现行一次 hold 回退；或规划器本就判 hold → 安全通道一次 | DROPPED |
| 无观测帧 `predicted_look_at` 时序命中 | `predicted_look_at` `PUBLISH_DROPPED` | 预测窗口内授权本为 HOLD → 一次 | DROPPED |
| 观测 WRITTEN、其后云台或速度时序命中（同帧中途越线） | 观测收据保持 WRITTEN（**不回改、不撤销已写桥文件，不声称跨桥文件原子性**）；越线通道及其后通道 `PUBLISH_DROPPED`，`detail.partial_after_observation=true` | 一次 hold 回退 | DROPPED |
| 任一通道完整性命中 | `PUBLISH_REJECTED`，致命 | 现行 | FATAL（现行拆载体，不生成重捕提示） |
| 底层写失败 | `WRITE_FAILED` 后上抛（现行） | 现行 fail-closed | 不属时序类：不计 streak、不清零 |
| 无门控尝试（未尝试观测与云台） | — | 按授权 | NO_ATTEMPT |
| 全部门控通道 WRITTEN | WRITTEN | 按授权 | PUBLISHED |

- **恰一次 HOLD**：DROPPED 帧机身通道恰一条 `body_safety_hold` WRITTEN（来自规划器 hold 或回退 hold，二者不并存）；hold 自身写失败按现行 fail-closed。
- **streak 按最新帧一次结算**：DROPPED → +1；**只有 PUBLISHED 清零**（合格清零通道 = 同帧观测或 `predicted_look_at` WRITTEN 且本帧无 DROPPED）；NO_ATTEMPT 不变；`body_safety_hold`、显式 hold、`set_nadir`、`slew_look_at` 不清零也不计数。结算后 `streak ≥ N_drop` → 以本帧第一个时序原因名 `_set_fatal`，记 `publish_escalated`，走 F4 现行致命路径（原因名不变），并标记该拆载体为「时序升级」（G2 唯一入口）。
- **降级帧不改目标管理器**：连续性、观测状态、截止按 frame_id 照常推进；会话投影：管理器投影为 `TRACKING`/null 或 `TRACKING`/`predicting` 且本最新帧 DROPPED → `TRACKING`/`publish_degraded`；管理器其他原因优先；下一 PUBLISHED 帧恢复原投影。
- 新名字只在闭集**末尾追加**：收据 outcome `PUBLISH_DROPPED`、reason `dropped_with_frame`（收据层，非 `PUBLISH_REJECT_REASONS` 成员）；`JOURNAL_KINDS` 追加 `publish_dropped`、`publish_escalated`、`frame_timing`、`reacquire_started`、`reacquire_skipped`、`reacquire_canceled`、`reacquired_after_rebuild`、`reacquire_failed`；`STATE_REASONS` 追加 `publish_degraded`、`reacquiring`、`reacquire_failed`、`reacquire_ambiguous`、`rebuild_reacquired`。

### 3.3 时序升级重建后的自动重捕（G2；K3/K2；回应 AR1-3）

**提示生成**（拆载体前，旧载体仍在）：仅当拆载体原因为「时序升级」、`auto_reacquire=on`、存在绑定、当前连续性 ∉ {DISPUTED, BROKEN}、任务未 stopped 时生成；否则记 `reacquire_skipped(cause)` 并走现行路径（`operator_stop`、`duration_reached`、`binding_rollback_failed`、完整性类、`frame_gap`/`frame_stall`、无绑定均不生成）。提示内容：
- `f_last` = 管理器最后接受观测的帧，且须是经 `_gate_classified` 求值**无完整性命中**的最新帧（PUBLISHED 或 DROPPED）；不满足则回退到更早的满足帧，`f_last` 早于升级帧超过 `T_reacq` → `reacquire_skipped(hint_stale)`。
- 绑定键在 `f_last` 后验（posterior）的**完整 8 维均值与 8×8 协方差**深复制（单位：检测画幅像素、像素/帧）；任一分量非有限、协方差非对称或非半正定 → `reacquire_skipped(hint_invalid)`。
- `f_last` 帧传感器元数据中的位姿/内参（非真值，取自帧环快照）；绑定 TaskSpec、旧 episode_id、`seg_end`。
- 提示作为新输入种类 `reacquire_hint` 写入 `tm_inputs.jsonl`（含自身 sha），重放可复现（AC-13 R2-2）。
- 有提示时 `_retire_pointer` 以 `cancel_task=False` 调 `release_binding`：旧 episode 以 `seg_end` 关闭，任务回 `ACQUIRING`（TaskSpec、`intent_revision` 不变）；无提示时保持现行 `cancel_task=True`。

**窗口**（可观测且有界）：起点 = 新载体 `resident_loop_started` 事件，记 `f_ready`（该事件 frame_id）与 `m_ready`（同源 monotonic）。截止 = 处理帧 `frame_id > f_ready + T_reacq − 1`（缺帧照计）**或** `monotonic − m_ready > T_reacq / hz`（hz 为场景名义帧率，5 Hz 时 2.0 s，派生量非新参数），任一满足即到期；到期判定在 `_advance_resident` 每 tick 执行（零新帧亦然）。重建未完成即 `rebuild_limit` → 会话现行终止，提示作废。窗口内：零 `look_at`/`predicted_look_at`/速度命令，每个最新帧机身恰一次 hold（任务 ACQUIRING 无绑定的现行授权 HOLD 路径）；会话 `REINIT_REQUIRED`/`reacquiring`。

**同帧顺序**：① 非帧请求先于本帧（现行 ① 顺序）：stop > release > 点击；stop/release → 提示作废、任务取消，`reacquire_canceled(cause)`；点击 → 照现行点击提交，提示作废，`reacquire_canceled(user_click)`。② 本帧候选门。③ 满足提交条件即提交（截止帧当帧满足也提交）。④ 未提交且已到期 → `reacquire_failed`。歧义一经判定即锁存 → `reacquire_ambiguous`，窗口结束。失败/歧义/取消后任务置 CANCELED，不再自动尝试，等人点击/release/stop。

**合成先验**（每帧 f 现算，不入库、不回写）：n = f − f_last ≥ 1；对提示 8 维状态用**与库同一 KF 类与常数**的预测方程连推 n 步，再以 `pose_homography(meta_f_last, meta_f)` 做 pose-center 变换（中心按 H 映射，速度与 8×8 协方差按 J 变换，与 `apply_pose_center` 同式；与库「预测后、关联前」同序）；取位置块得 `KfSnapshot`，phase 记 `reacq_prior`（新常量，定义在 `target_manager.py`，不并入库 phase 闭集、不冒充 `KF_PRIOR`）。映射为 None、J 不可得、结果非有限或 S 不可逆 → 本帧无证据（`reacq_prior_invalid`），证据缓冲清零重计。**门只用合成先验**；不用候选自己的 prior/posterior 自证。

**候选门与竞争**：对新载体本帧 `TRACKED`/`UNCONFIRMED` 且有库键的轨迹逐个用 `reacquire_gate(prior_reacq, det, params)`——判据、常数与 `motion_size_gate` 逐式相同（S、半径门 r_gate_max、NIS ≤ g_motion、尺寸 ≤ g_size），只把 phase 校验换成 `reacq_prior`；`motion_size_gate` 对库 prior 的行为逐字不变。无库键检测只记诊断、永不可提交。证据按键连续帧累积（缺帧清零）；≥ 2 键且累计 NIS 前二差 < m_nis → 歧义；否则最小累计 NIS 键，连续 ≥ `N_adopt` 帧、提交帧状态 `TRACKED`、候选同帧 post 有效才提交（post 无效 → 本帧不提交，证据保留）。新载体无共存历史，**门 0 排除不可用**（§6 限制）。协方差随 n 增长使半径超 r_gate_max 时自然无候选，按到期失败处理。

**提交事务**：`commit_binding(origin="reacquire", ...)`；`ORIGINS` 末尾追加 `reacquire`，`MODE_ORIGINS[capture]` 加入；`RELATIONS` 末尾追加 `REBUILD_REACQUIRE`。预检：模式 capture、有效提示、窗口未到期、`runtime.phase == ACQUIRING`、未 stopped、看门狗 fresh、版本相符。计划：`episode_seq + 1`，`BindingRecord(relation=REBUILD_REACQUIRE, origin=reacquire)`，evidence = {`hint_line_sha256`、`f_last`、`reacquired_from_episode`、`seg_end`、证据帧、逐帧 NIS、状态、`tm_inputs_line_sha256`}；`TaskRuntime("TRACKING", capture, 新 episode)`；TaskSpec 与 `intent_revision` 不变；连续性以 BIND 边从 SUPPORTED 起。`follow` 失败 → 现行 `_rollback`；回滚失败 → `binding_rollback_failed`（现行 fail-closed，不再自动尝试）。提交后照 CAPTURE 授权表跟随；会话 `TRACKING`/`rebuild_reacquired`。重建计数与 `rebuild_limit` 不变，重捕不消耗额外重建。

### 3.4 门值重核规则（G3；预登记，K1；回应 AR1-7）

- 首候选 `t_pub_s = 0.4`、`k_pub = 2`：**合同继承的移植限值**（LOOP-001 AC-10 修订 1），不称本机最优；配置 sha 进每条降级/升级事件。
- 冒烟（§5.2）后实现角色按 §3.5 算「TRACKING 段最新帧门求值时刻 − `load_monotonic_s`」（与门同源同起点）的 n、p50、p95、p99、最大，及降级帧率（DROPPED 最新帧 ÷ 有门控尝试的最新帧）、升级次数、与计量采样区间重叠的越线帧数（区间交叠：帧 `[m_read0, m_end]` 与采样 `[start, end]` 同主机 monotonic 相交；另记 unix 对照）。
- 预登记分流（**建议线，不是验收 STOP**）：(a) 降级帧率 ≤ 1% 且升级 0 → 建议保持 0.4 s/2 帧；(b) 否则 p99 ≤ 0.6 s → 建议 0.6 s/3 帧（设计预算：多容一帧）；p99 > 0.6 s → 建议保持原值并如实报告持续积压（放宽无益）。只允许 `{0.4/2, 0.6/3}`，由用户签；未签保持原值。
- 冒烟先于任何正式门工件，门值只在此一次预登记二选一；正式 Play 后不得依其数字反调（workflow §4.3.2 反调参纪律）。门值改动是候选改动，须回代码停点（§7）后才进正式 Play。

### 3.5 逐阶段耗时（G5；K1；回应 AR1-7）

时钟：会话注入的同一 `monotonic`（与帧环、`GatedPublisher` 同源，不用 `perf_counter`）。每个被处理帧标记：`m_read0`（读字节前）→ `m_L`（= `load_monotonic_s`，F3）→ `m_dec`（解码完）→ `m_det`（模型 predict 返回；由会话模型缓存返回对象的计时包装测得）→ `m_assoc`（`tracker.update` 返回）→ `m_tm`（管理器 `on_frame` 返回）→ `m_end`（最新帧：最后一个通道收据落盘后；旧帧：= `m_tm`）。
- `frame_timing` 记：`frame_id`、`batch_position ∈ {newest, backlog}`、`read_s`、`decode_s`、`detect_s`、`associate_s`、`tm_s`、`publish_s`（旧帧 0 且 `publish_attempted=false`）、`total_s = m_end − m_read0`；相邻段首尾相接、不重叠，**各段之和 = total_s**（假时钟下逐值相等）。
- 每次门求值另记 `gate_eval_s = 门读 monotonic − m_L`（与门 `load_elapsed` 同值），供 §3.4。
- 本帧 `frame_timing` 自身写盘耗时无法记在本条：下一条记 `journal_prev_s` 与 `journal_prev_frame_id`，**单列、不计入任何帧的 total**。
- 失败帧（读/解码/检测异常、会话致命）：已过标记照记，未到达段 null 并附 `missing_reason`，不计入 §3.4 统计；DROPPED/REJECTED 最新帧照记全段。不进桥文件，不改 `compute_latency_ms` 原义。

### 3.6 计量工具（G4；`tools/eng_fastfix/meter.py`）

- 独立进程（`nice`），停令检查线程与采样线程分离：停令节拍 ≤ 0.5 s，任何采样进行中停令延迟 ≤ 1 s。
- 只遍历操作单声明的输出根（会话目录、本项输出目录、Unity runtime 帧目录），不全仓遍历；采样间隔可配，缺省 30 s；每次采样记 `start/end` 的 monotonic 与 unix。
- 输出：每次采样一行追加 JSONL（总量与根级小计），单文件上限 1 MB，超限停写并记 `meter_truncated`。
- 停令条件（墙钟、磁盘峰值）取自操作单，工具不内置合同数字；工具不读真值、不导入 `controller`。

### 3.7 参数（`config/p1-eng-fastfix-001.json`；类别按 v3.1 B9）

| 参数 | 类别 | 结构约束 | 值 | 依据 |
|---|---|---|---|---|
| `t_pub_s` | 合同继承 | = `k_pub`/hz | 0.4 s | LOOP-001 AC-10 修订 1；§3.4 二选一 |
| `k_pub` | 合同继承 | ≥ 1 | 2 帧 | 同上 |
| `N_drop` | 设计预算（占位，七题答复 VALUES 按占位进入） | 1 ≤ · ≤ T_report | 3 帧（0.6 s） | 纯发布中断不晚于 CAPTURE 报告时限升级 |
| `T_reacq` | 设计预算（占位，同上） | ≥ N_adopt + 1 | 10 帧（2 s） | 诊断：重建约 3 帧 |
| `auto_reacquire` | 配置轴 | {on, off} | on（off 为对照） | — |
| 其余目标管理器参数 | CAPTURE 冻结 | — | 读 `config/p1-eng-capture-001.json`，不复制 | F11 |

配置加载即校验结构约束，不满足拒绝启动。冒烟后只报读数，不改占位值。

### 3.8 离线证据合同（AC-7/AC-8/评分；K3/K4；回应 AR1-6）

**AC-7 输入**：USER-4A 同批原始帧/位姿（829 帧，`SHA256SUMS` 现算核对）与 CoverageEvaluator 真值（只进 `score_`）。**剧本**：实现角色只看原始帧登记红车绑定点击（帧号与像素点）与注入规则——注入帧 = 绑定提交帧 + {20, 40, 60, …}（步长 20，至多 12 次，越过末帧即止）；某注入帧系统状态（非真值：管理器 `TRACKING` 且本帧 OBSERVED）不满足 → 记 `not_applicable`，不挪帧。剧本运行前提交、sha 入证据。**运行**：每候选一次 live 推理建检测缓存（键含帧 sha、权重 sha、推理参数），注入运行全部从缓存取（`live=None`，未命中即报错，零推理）；每次注入调用与会话同一的提示生成/`release_binding`/`on_teardown` 路径，新建 `DetAssocTracker` resident 实例，跳过 3 帧模拟重建后从缓存续喂；两臂 `auto_reacquire = on/off`。**输出**（逐注入）：`committed | failed | ambiguous | canceled | skipped(cause) | not_applicable | invalid_input`、提交用时（帧）、证据帧、缺失证据项；离线 `score_` 记提交帧被跟实例与真值 IoU 及其后 10 帧 IoU ≥ 0.5 比例。

**AC-8 输入闭集**（仅 TX 签发后；用途按七题答复 SOURCE）：formal-redo `unity-runtime/frames/` 第 584–783 帧（200 帧，连续，含 k=584 点击、647 事件与约 650–700 转弯段，位于诊断 §1 可对应区间 142…1520 内）的 jpg/json；会话日志字段只取 F14 所列 `frames_processed`、`click_received`（第 584 帧那一条）、`publish-receipts` 字段；**不取** `m3_body_truth.jsonl`、`tm_inputs.jsonl`、任何评分产物或旧结论。完整性：逐帧 jpg sha 与收据 `snapshot_sha256`、元数据 sha 与 `frames_processed.metadata_sha256` 一致，缺任一帧或字段 → AC-8 `NOT_RUN`。**时钟模拟边界**：批次结构取 `frames_processed.frame_ids`；最新帧门求值时刻按收据 `load_elapsed_s` 注入假 monotonic，`latest.json` 帧号按收据 `latest_frame_id` 注入；无收据帧按批内顺序推进、不注入越线；检测为 mini 上本次推理（不复用旧检测）。这是**有限复演**：不称精确复演，不用局部源补 CAPTURE 读数。**判据（无真值）**：第 647 帧不拆载体（`resident_rebuilds = 0`），647 后至第 783 帧被跟键与管理器状态逐帧记录，丢失时在 CAPTURE 窗口内修复或准时报告；身份正确性不在 AC-8 判定。

**评分入口隔离**：真值读取者闭集 = `tools/eng_fastfix/score.py` 的 `score_*` 函数（AC-7、AC-16）；运行时入口（`controller/`、`tools/eng_fastfix/replay.py`、`meter.py`、`ledger.py`）不导入 `score.py`、不打开真值路径。动态证明：同一回放在真值文件替换为毒化副本时，运行时产物（事件、提交、`tm_inputs` 字节）逐字节相同；运行期间文件打开审计不含真值路径（AC-12）。

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | §3.1 逐行各一例（假时钟、假检测器）；交叉用例：步 2 + 步 3、步 4c + 步 5e、步 5b + 步 5d、步 5b + 步 3 → 完整性优先且致命、`detail.hits` 全列；负 `load_elapsed`、负 `capture_age`、缺 `capture_unix_s` → 完整性致命；仅时序命中 → `PUBLISH_DROPPED` 且 `fatal_reason` 为 None；同注入兼容模式 → `_gate` 首命中、首拒致命；`_gate` 函数体 diff 为空 | `test:tests/test_fastfix_publish.py::Classify*`、`::CompatGate*` | K1 | 2026-10-12（消费；现状见核对表） |
| AC-2 | §3.2 表逐路径：观测时序命中、预测云台时序命中、观测 WRITTEN 后云台越线、观测与云台 WRITTEN 后速度越线（复现第 647 帧 0.55 s 形态）→ 收据如表、观测 WRITTEN 不回改、每个 DROPPED 帧恰一条 `body_safety_hold`、无 `orphan_control`；指针、track_key、episode、管理器状态与未注入对照逐字段相同；下一帧 PUBLISHED、FOLLOW 恢复；`resident_rebuilds = 0` | `test:tests/test_capture_session.py::Degrade*` | K1K2 | 2026-10-12（消费；现状见核对表） |
| AC-3 | 连续 `N_drop` 个 DROPPED 最新帧恰在第 `N_drop` 帧结算时升级（原因名不变，拆载体、重建 +1）；`N_drop − 1` 后 PUBLISHED → 清零；hold/NO_ATTEMPT/旧帧不清零不计数；完整性命中在任意 streak 值都即刻致命且不被重置；写失败不计不清；兼容模式行为与修改前逐条相同 | `test:tests/test_capture_session.py::Escalate*`、`::CompatUnchanged*` | K1K2 | 2026-10-12（消费；现状见核对表） |
| AC-4 | 积压注入（10 帧 × 0.5 s）：只最新帧开上下文；streak 与升级时刻符合 §3.2；投影 `TRACKING/publish_degraded` 与恢复；管理器其他原因优先；新名字只在闭集末尾追加（静态检查） | `test:tests/test_capture_session.py::Backlog*`、`::Projection*` | K1 | 2026-10-12（消费；现状见核对表） |
| AC-5 | 重捕状态机（假检测器、假时钟）：提示生成/跳过各原因（含 `hint_stale`、`hint_invalid`、DISPUTED/BROKEN、完整性、`frame_stall`、`operator_stop`、`auto_reacquire=off`）；窗口起点 `resident_loop_started`、帧号与 monotonic 两截止（含零轨迹、缺帧、零新帧 tick）；截止帧当帧满足即提交；同帧 stop > release > 点击 > 自动；唯一候选 → `reacquire` 提交、新 episode、TaskSpec/`intent_revision` 不变、evidence 字段齐全；歧义锁存；follow 失败回滚、回滚失败 fail-closed；窗口内零 look_at/速度、每最新帧恰一次 hold；`tm_inputs` 重放事件逐条相同 | `test:tests/test_target_manager.py::Reacquire*`、`test:tests/test_capture_session.py::Reacquire*`；`artifact:docs/reviews/P1-ENG-FASTFIX-001.md` R2 §1–2（N-1已覆盖） | K3K2 | 2026-10-12（消费；现状见核对表） |
| AC-6 | 重捕负例：位置过门但尺寸不过、运动不过 → 不提交；提示车出画 → `reacquire_failed`；位姿大转（25°/帧滚转合成）经 pose-center 映射后仍按门判定；映射失败/非有限 → 本帧无证据；合成先验 phase 为 `reacq_prior`，`motion_size_gate` 对库 prior 输出与修改前逐值相同；门只用合成先验（以候选自身 prior 替换时结果不变的反证用例） | `test:tests/test_target_manager.py::ReacquireNegative*` | K3 | 2026-10-12（消费；现状见核对表） |
| AC-7 | 离线重捕回放（§3.8，Mac mini）：两臂逐注入输出齐全；`off` 臂零自动提交；判据：`on` 臂 **n_committed ≥ 1 且全部提交实例与真值 IoU ≥ 0.5**；n_committed = 0 → 记「无成功证据」、AC-7 不通过（不空真）；成功率、用时只作带 n 读数 | `artifact:docs/evidence/P1-ENG-FASTFIX-001-replay.md` §1–2 | K3K4 | 2026-10-12（消费；现状见核对表） |
| AC-8 | （可选；TX 未签或完整性不符 → `NOT_RUN`，不计）§3.8 有限复演：第 647 帧不拆载体，后续逐帧被跟键与管理器状态、修复/报告时点列表齐全；不判身份正确性 | `artifact:docs/evidence/P1-ENG-FASTFIX-001-replay.md` §3 | K1K3 | 2026-10-12（消费；现状见核对表） |
| AC-9 | 每个被处理帧恰一条 `frame_timing`，字段同 §3.5；假时钟下各段之和逐值等于 `total_s`，`gate_eval_s` 等于同次门 `load_elapsed`；`journal_prev_s` 单列不入 total；失败帧缺段带原因；桥文件无新字段 | `test:tests/test_capture_session.py::FrameTiming*`；`artifact:docs/evidence/P1-ENG-FASTFIX-001-r1-1-red.log`、`artifact:docs/evidence/P1-ENG-FASTFIX-001-r1-1-green.log`；`artifact:docs/reviews/P1-ENG-FASTFIX-001.md` R2 §0/§2–3（R1-1已闭） | K1 | 2026-10-12（消费；现状见核对表） |
| AC-10 | 捕获模式从 `config/p1-eng-fastfix-001.json` 读 §3.7 参数，违反约束拒绝启动；首候选 = 现行常数；无 `ρ_reacq`；兼容模式仍按 K 收据与 `K_PUB`；`K_PUB`、`T_STALL_S`、`RESIDENT_REBUILD_LIMIT` 常数 diff 为空 | `test:tests/test_fastfix_publish.py::Config*`；`cmd:git diff <base>.. -- controller/language_loop.py` | K1 | 2026-10-12（消费；现状见核对表） |
| AC-11 | 计量工具：假遍历器（15 万路径、单次采样 5 s）下停令延迟 ≤ 1 s；只遍历声明根；采样带 start/end；超 1 MB 停写记 `meter_truncated`；不读真值、不导入 controller | `test:tests/test_fastfix_meter.py` | K2 | 2026-10-12（消费；现状见核对表） |
| AC-12 | 隔离：§3.8 评分入口闭集外不读真值（静态导入图 + 毒化真值字节相同 + 打开审计）；diff 为空：`Assets/`、`*.unity`、`config/scenario.*.json`、`config/det-assoc-v1.models.json`、FAST-002 freeze、`config/p1-eng-capture-001.json`、`controller/det_assoc_tracker.py`、`LanguageWorker`、`CandidatesBackend`/`_validate_candidates_source`、围栏读取、`tools/eng_loop2/`、`tools/eng_capture/`；改动文件 ⊆ §2.1 闭集；兼容模式既有测试无新增失败 | `test:tests/test_capture_isolation.py`（扩展）；`cmd:git diff --stat <base>..`；`artifact:docs/reviews/P1-ENG-FASTFIX-001.md` R2 §0–2（N-2已覆盖） | K4 | 2026-10-12（消费；现状见核对表） |
| AC-13 | 承接回归：R2-2（行间链式引用/帧连续性、生产字节删行拒绝，含 `reacquire_hint` 行）修前红/修后绿；R1-4 仅在 §2.4 触发时补；不改旧债状态 | `test:` 具名回归（证据文件列名） | K4 | 2026-10-12（消费；现状见核对表） |
| AC-14 | 停点全套：每候选 Mac mini 数据根 `.venv-yoloe` 一次，写 `docs/evidence/P1-ENG-FASTFIX-001-tests.log`，分列基线已有与本批新增失败；新增 0；真实构造次数按 F12 闭集与 skip 状态如实记录，超出闭集即 S-LOADER | `cmd:<数据根>/.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-FASTFIX-001-tests.log 2>&1`；`artifact:docs/evidence/P1-ENG-FASTFIX-001-tests-c4-focused.log`、`artifact:docs/reviews/P1-ENG-FASTFIX-001.md` R2 §2（窄修替代附议，不记全套通过） | K1K2K3K4 | 2026-10-12（消费；现状见核对表） |
| AC-15 | 冒烟与正式操作单各一份：发令前 `git rev-parse HEAD`/`git status --porcelain`；Air 预检原始读数；计量配置与 sha；会话命令（`--language off --resident --body-policy standoff`）；剧本 S1 点静止车、S2 点红车跟随 ≥ 1 圈（含 CAPTURE 丢失拐角）、S3 点静止车再点回红车；§6 STOP 表；各一次、失败不重试 | `artifact:docs/evidence/P1-ENG-FASTFIX-001-play-ops.md` | K1K2K3K4 | 2026-10-12（消费；现状见核对表） |
| AC-16 | 正式 Play 连续性（离线 `score_`，逐项分母写明）：(a) 分母 = 全部 DROPPED 最新帧，每个归「下一帧恢复」或「N_drop 处升级」，**无单帧时序命中致拆载体**；(b) 分母 = 全部时序升级拆载体，每个归提交（真值 IoU ≥ 0.5）/失败/歧义/取消，误绑 0；(c) 分母 = 红车真值可见帧内每次失去已接受观测，每次在 CAPTURE 窗口内修复或在 T_report/T_repair 准时报告；(d) 被跟实例非红车帧数照记。任一分母所需日志或真值缺失、或未完成一圈 → 该项 `INCOMPLETE`，不判 PASS | `artifact:docs/evidence/P1-ENG-FASTFIX-001-play.md` §1–2 | PlayK2K3K4 | 2026-10-12（消费；现状见核对表） |
| AC-17 | 时延读数（描述，不设门）：§3.4 同口径分布、降级帧率、升级次数、采样重叠计数，带 n | `artifact:docs/evidence/P1-ENG-FASTFIX-001-play.md` §3 | PlayK2K3K4 | 2026-10-12（消费；现状见核对表） |
| AC-18 | 用户目检：拐角处跟住，或丢失/降级/重捕失败有可见报告；无「无报告的主动撤权悬停」；接受或辅助角色代录 | `artifact:docs/unity-test-log.md`（UT-P1-ENG-FASTFIX-001-…） | PlayK2K3K4 | 2026-10-12（消费；现状见核对表） |
| AC-19 | 粗粒度账本：每步启动前按 §5 剩余量拦截（余额不足拒启）；成功/失败/重试同账；尝试即记、失败不返还；计量缺失或账本损坏 → UNKNOWN → 拒启并停报；未列维度为 0 | `test:tests/test_fastfix_ledger.py` | K4 | 2026-10-12（消费；现状见核对表） |
| AC-20 | 冒烟报告（诊断，不作验收证据、不定 verdict）：§3.4 读数齐全、分流建议按预登记规则机械给出 | `artifact:docs/evidence/P1-ENG-FASTFIX-001-smoke.md` | — | 2026-10-12（消费；现状见核对表） |


## 5. 预算信封（申请草案；**用户逐字签发前各维度均为 0**；粗粒度；回应 AR1-4/AR1-5）

### 5.0 共同口径

- 七题答复 ENVELOPE-STOP：按阶段 A/B/C 分签；粗粒度 = 每阶段只列少数总量维度（墙钟、模型加载次数、Play 次数、传输总字节、磁盘峰值、ID），**不做逐候选/逐帧/逐 ID 细分上限**；未列维度为 0；耗尽即停；成功、失败、重试共账；尝试即记、失败不返还。
- 记账：`tools/eng_fastfix/ledger.py`（AC-19）每步启动前核剩余量，不足即拒；计量缺失或不可得 → UNKNOWN → 停报，不推余额。
- 复核/核对：核对轮零消耗；复核 focused 与红绿按设计全用替身（零模型）；复核若需真实模型重跑，计入所在阶段同一总量，不默认免费。
- 执行机：七题答复 MACHINE——离线阶段 Mac mini，Play 阶段 MacBook Air。
- 预检先行：§8.2 未核项先由零消耗只读预检核实（读数写 `docs/evidence/P1-ENG-FASTFIX-001-preflight.md`，执行者由 supervisor 派发）；依赖未核项的阶段在预检读数入仓前不呈签。
- **不细分的理由与例外**：推理帧不单列（受加载次数与墙钟双重约束，回放缓存零推理）；候选数 ≤ 3 写为结构上限（防以换候选号规避），不另设每候选额度。若接受角色认为某维必须细分才安全，请写明，构思角色不预设。

### 5.1 阶段 A（FASTFIX:A:1；离线，Mac mini）

| 维度 | 申请上限 | 数值出处 |
|---|---|---|
| 候选数（结构上限） | ≤ 3 | CAPTURE 同口径 |
| 真实模型加载（YOLO 构造，全阶段总量） | ≤ 14 | 每候选 AC-7 1 + AC-8 1 + 全套 ≤ 2（F12）= 4，×3 = 12，余 2 供崩溃重载/复核 |
| 计算墙钟（全套 + 回放 + 评分，总量） | ≤ 2 h | 全套约 10 min（F12）、回放约 3 min（F13），×3 候选并留余量 |
| Mac mini 新增磁盘峰值 | ≤ 2 GB（含 outputs、检测缓存、TX 副本、会话暂存、证据、git） | 设计预算 |
| TX（仅 AC-8，单独签） | 方向 Air → mini；1 次（重试共账）；≤ 200 帧（§3.8 片段）+ 两份日志字段抽取；总字节 ≤ 50 MB；Air 侧暂存峰值 ≤ 50 MB（传完即删暂存，不动原件） | 原件约 50 KB/帧（F14） |
| scenario/session/run ID | 0/0/0（回放输出目录不是 ID） | — |
| Unity/Play、API、云 GPU/训练、云、下载、安装、板端 | 0 | — |

### 5.2 阶段 B（FASTFIX:SMOKE:1；消耗性诊断冒烟，Air）

**不是** workflow §4.3.2 常设诊断通道：它真实运行会话、产生 ID，故作为**另行请求用户签发的消耗性诊断**（PLAY (a) 的「冒烟 1」）；产物只作 §3.4 门值读数，不进验收证据、不定 verdict。生效条件：代码停点 `K1K2K3K4` 首个通过轮已由接受角色消费放行（§7）。

| 维度 | 申请上限 | 数值出处 |
|---|---|---|
| Unity Play | 1 次（失败也占，不重试、不追加） | 七题答复 PLAY (a) |
| Play 段墙钟 | ≤ 300 s | formal-redo 会话 299.9 s（F14） |
| 阶段墙钟（预检到收尾提交） | ≤ 60 min | 设计预算 |
| 模型加载 | 1（会话缓存，重建复用） | F12 |
| scenario/session/run ID | 0/≤ 1/≤ 1（随该次 Play 产生） | — |
| Air 新增磁盘峰值 | ≤ 1 GB | formal-redo 约 217 MB 的约 4 倍 |
| 其他 | 0 | — |

### 5.3 阶段 C（FASTFIX:PLAY:1；正式，Air）

生效条件：冒烟后的候选（若有门值或修复改动）已回同一代码停点并经接受角色消费放行；§3.4 门值已由用户签或保持原值。

| 维度 | 申请上限 | 数值出处 |
|---|---|---|
| Unity Play | 1 次，失败不重试 | 七题答复 PLAY (a) |
| Play 段墙钟 | ≤ 300 s | 同上 |
| 阶段墙钟（预检、Play、离线评分、提交） | ≤ 90 min | 设计预算 |
| 模型加载 | 1 | F12 |
| scenario/session/run ID | 0/≤ 1/≤ 1 | — |
| Air 新增磁盘峰值 | ≤ 1 GB | 同上 |
| 其他 | 0 | — |

## 6. 限制、不承诺与 STOP 表

- 不声称尖峰根因（E4/E5）已定案；不声称门值最优；不声称跟随误差或进带指标（CAPTURE AC-25 口径不继承为门）；降级 hold 造成的跟随顿挫不优化。
- 重捕只覆盖「时序升级、拆载体前有可靠观测、重建短」的情形；新载体无门 0 排除，相似干扰车下误收养率无素材（同 CAPTURE A3），**不声称误重捕率**；AC-7/AC-16 误绑 0 只是样本观察，不推风险上界或板端能力。
- 持续积压不是本项能修的：只保证显式降级、升级与报告。

**STOP 表**（数值出处四类：信封＝用户签；合同继承；设计预算；实测）：

| 码 | 触发 | 数值出处 | 停什么 | 仍可做（零消耗安全收尾） | 耗用与 UNKNOWN |
|---|---|---|---|---|---|
| S-PRE | 预检不符（输入 sha、解释器/依赖、权重 sha、槽位/写者、runtime 残留） | 实测 | 本阶段全部消耗步骤不启动 | 记读数、提交预检证据 | 0；未读到即 UNKNOWN 视同不符 |
| S-BUDGET | 任一维启动前余额不足，或运行中将达上限 | 信封 | 拒启该步；运行中到限即停该步 | 保存已得产物、写资源记录与部分读数、提交 | 已耗如实入账，不返还 |
| S-UNKNOWN | 计量缺失、账本损坏、耗用不可得 | — | 本阶段一切后续消耗 | 同上 | 记 UNKNOWN，不推余额，回用户 |
| S-LOADER | 全套真实构造超出 F12 闭集 | 合同继承（F12） | 该次全套，AC-14 `NOT_RUN` | 保存日志、提交 | 已构造次数入账 |
| S-ORIG | 原件/准入集 sha 不符或异常 | 实测 | 依赖该输入的步骤（AC-7/AC-8） | 保留原件不动、记录差异 | 0 |
| S-TRUTH | 真值进入运行时迹象（隔离测试失败、打开审计命中） | 红线 | 全部运行与 Play | 保存证据，按 RED_LINE 报 | 已耗入账 |
| S-PLAY-WALL | Play 段到 300 s | 信封 | 操作员按停、会话 stop | 计量收尾、原件归档、离线评分（零模型） | Play 计 1 |
| S-DISK | 计量显示新增磁盘达上限 90% | 信封 | 立即停 Play/回放 | 同上，不删原件 | 记峰值 |
| S-METER | 计量工具崩溃或停令检查失联 | 设计预算 | 停 Play（磁盘失去监控） | 同上 | Play 计 1 |
| S-REBUILD | 会话 `rebuild_limit` 终止 | 合同继承 | 结束本次 Play，不重开 | 同上 | Play 计 1 |
| S-SAFETY | 操作员目视机身/系留异常 | — | 立即停 | 同上 | Play 计 1 |
| S-OPS | 误触、额外 Play 或未登记组件启动 | — | 立即停，不补跑 | 同上并如实登记 | 实际次数入账，超出部分回用户 |

所有 STOP 不重试、不追加；处置随信封交用户确认，未确认的处置不生效、照旧停报。

## 7. 必经停点与顺序（回应 AR1-5）

| 停点 | 触发 |
|---|---|
| `K1` | 分级门与 `PUBLISH_DROPPED` 语义、帧结算、计时、新日志/原因名 |
| `K2` | 降级帧恰一次 hold、重捕窗口内命令、计量停令 |
| `K3` | 重捕身份提交（新 origin/relation）、合成先验、episode 关系 |
| `K4` | 离线评分与真值隔离、账本、Play 读数口径 |

顺序（engineering-workflow §4「不可重跑消耗步骤先过停点」）：阶段 A 候选 → `C<n>@K1K2K3K4` → `R<n>@K1K2K3K4` → 接受角色消费放行 → **阶段 B 冒烟（一次性）** → 冒烟报告 → 若门值改签或冒烟暴露缺陷：具名窄修回同一停点（复核开轮按 workflow §4.4），再经消费放行；无改动则沿用已放行候选 → **阶段 C 正式 Play** → `PlayK2K3K4` 证据停点（AC-16…18）。冒烟失败只回具名返工，不隐含追加冒烟；冒烟不能代替独立复核。不触发 K5。

## 8. 只读试读

### 8.1 Air 已核（D1 + D2 会话）

- `controller/` 与派发基线一致；F1–F14 符号、路径与日志键名存在（grep/sed/解析键名，未导入）。
- `outputs/eng-capture/formal-redo/` 存在；会话日志与收据键名如 F14；帧目录约 76 MB。
- 仓库 `.venv-yoloe` 目录存在（未运行）。

### 8.2 未核（假设；依赖维度在预检读数入仓前不呈签）

- Mac mini：USER-4A 准入原件（829 帧、`SHA256SUMS`）在且未变；数据根 `.venv-yoloe` 含 `lap`、可构造跟踪器；权重 sha；磁盘余量（阶段 A 依赖）。
- Air：运行时槽位与写者、`runtime/` 残留、磁盘余量（阶段 B/C 依赖）。
- formal-redo 第 584–783 帧逐帧 sha 与收据/日志一致（AC-8 与 TX 依赖）。
- 同主机 monotonic 跨进程可比（计量采样重叠计法依赖；冒烟以 unix 对照核）。

## 9. 待用户

七题已由用户答「按推荐，信封粗粒度」（账本同日条），D2 已按其效力读法落实。**新增待用户事项无**；§5 三阶段信封与 STOP 处置在接受收束及预检后分阶段呈签（未签即 0）。

## 决策记录

- D1（2026-10-10，构思）：起草。G1–G5 一一对应诊断 §6 五条；只在捕获模式生效；门值首候选不改，重核走预登记二选一；正式 Play 前设独立代码停点。
- D2（2026-10-10，构思）：逐条回应 AR1-1…7 并落实七题答复：分级门改全量求值、按最新帧结算、重捕只接时序升级且窗口有界、删 ρ_reacq、冒烟改消耗性诊断并前移代码停点、信封改粗粒度分阶段、离线证据合同与评分隔离写实。见下「D2 逐条回应」。

### D1 接受裁定（2026-10-10，Acceptance）

**裁定：`REVISION_REQUESTED`，首次设计退修。** 已完整审阅 D1、现行工作流、授权两条、CAPTURE 离线诊断及收口义务，沿工程继承清单/缺陷账本读取相关合同与真实发布门。本轮为零消耗合同审查，不是候选核对、实现证据或独立复核；不跑测试，不写账本、代码、配置、工具或正式设计。

**轨道逐字裁定：本轮不准许 `Workflow: engineering-v1` 生效。** 新 ID 开项即有申请，工程定位与短任务合同形式适合本项；但尚未 `ACCEPTED`，依 engineering-workflow §0 fail-closed，不能按工程轨道启动实现。G1/G2 触及运行时安全与控制命令，依接受角色细则「轨道裁定」须先由用户确认该有界 K2 范围的换轨；现有零消耗构思方向授权不替代此决定，也不授权代码或任何额度。

#### 已核范围与保留边界

- §1 主线段落、四条约束及各条说明与 `docs/project-background.md` §3 现行正文逐字一致（仅引用排版不同）。属性分类器条明确是下一轮输入，不能据此改本项 VLM 职责或重训。
- G1–G5 对应诊断 §6 的五项建议，可保留为快层一轮必要修正的拟议闭集；§2.3 排除了 VLM、分辨率、检测器训练/权重/推理参数、场景、板端及兼容模式新行为。两次 Play 超出约束 1 的字面，必须由用户另定，不能解释成已获例外。
- 不反调 CAPTURE 参数、帧集、判据，不恢复或重跑旧门，不改其 ENDED/FAILED_INCOMPLETE、AC-23…26 缺项、OPEN 债或旧偏差/UNKNOWN；本项新重捕口径与旧读数分列。诊断 §3 表有七条拒绝记录，而汇总称六次，F10 不可把有冲突的汇总当已核精确计数。
- 正式 Play 前的 `K1K2K3K4` → C → 独立 R → 接受消费，以及单独 `PlayK2K3K4` 证据停点，设计方向成立。门值或代码后改须回代码停点，不能用冒烟通过代替独立复核。
- 指标上限保留：不以几何可见、一圈目检或样本误绑 0 推出跟踪改善、风险上界或板端能力；成功率与耗时仅带 n 的读数。Unity 真值仍只由 CoverageEvaluator 产生，离线评分可读其真值产物；不得通过 `score_` 名字把真值派生选择点、提示、候选键或 KF 输入送回感知/控制。
- §5 明确只是申请，未签/缺项即 0 是正确的；旧项余额不转用。下列矛盾修正前不呈为可首签信封。

#### 退修完成条件（同一 work ID 出 D2，逐条回应）

| ID | 位置与问题 | D2 必须明确的完成条件 |
|---|---|---|
| AR1-1 | §3.1 原因分级不覆盖真实 `_gate` 的 `load_elapsed_s < 0`；按首命中返回，处理超时可遮住同时发生的 capture_age 超限/未来采集时刻，not_latest_loaded 也早于身份核验。 | 枚举时序与完整性同时异常、负处理时间/负采集年龄的判定及优先级；完整性异常不得借时序降级恢复运动。明确如何保留完整性检查与安全拒绝，不以“现行顺序”代替新分级语义；AC-1 补这些交叉/边界用例，兼容模式保持旧行为。 |
| AR1-2 | §3.1“任一通道 WRITTEN 清零”可被每个降级帧必写的 body_safety_hold 清零；观测先 WRITTEN、后 look_at/速度才超时的路径，与 G1/AC-2 的全帧零 WRITTEN 不一致。真实 `_derived` 明确不回改先前观测收据。 | 按最新帧一次结算 streak，明确合格清零通道，安全 HOLD 与其他无帧安全通道不清零；写清观测先失败、预测通道失败、观测成功后衍生通道失败、写盘失败的各自效果/收据与恰一次 HOLD。不能声称撤销已写观测或跨桥文件原子性；补“同帧中途越线”、连续降级恰在 N_drop 升级、完整性失败不被重置的用例，AC-2/3/16 与接口一致。 |
| AR1-3 | §3.3 从“首个已激活轨迹帧”起算，始终无激活轨迹时无截止；ρ_reacq 在配置/AC-10 出现却无算法用途；多候选 NIS 差较大时“唯一过门”如何选不明。 | 从可观测且有界的新载体就绪事件起计窗口，列无轨迹/缺帧/到期同帧候选、点击/release/stop 优先级；明确提示有效性、位姿映射失败、KF phase/单位/协方差传播与有限性、竞争门及ρ用途（不用则提请删占位），不拿 posterior 自证创新。按新 origin 写 TaskSpec/intent/episode/association 计数与证据输入/事务回滚；完整性重建须先重核新信任根，BROKEN/DISPUTED 不复活；AC-5/6 覆盖这些路径，保持共享控制安全约束。 |
| AR1-4 | §5.1 引用不存在的 F12；“按清单”不是数值上限。每候选与整批加载、focused/全套/复核红绿、评分与 ID 耗用未闭合；磁盘只限 outputs 漏会话/临时副本/证据等。 | 先以零模型源码读取列真实 loader/回放路径闭集与次数，不导入执行；逐阶段写数值的每候选及整批上限、候选次数、推理帧、ID、墙钟/收尾、传输/磁盘峰值与附属路径、其他维度 0。共账成功/失败/重试、启动前拦截、未知即停报；复核所需消耗不得默认免费。TX 明确方向、次数、字节/帧/本机复制峰值；未核 mini/Air 假设先预检，依赖维度待核后申请。R1-4/R2-2 按实际复用触发承接，不改旧债状态。 |
| AR1-5 | §5.2 自称 workflow §4.3.2 诊断通道却申请 session/run 1/≤1，与该通道“不创建、不消耗 scenario/session/run ID”冲突。 | 若沿用该诊断通道，ID 三维均 0 且不进证据/门；若实际会话必需 ID，则明确这是另行请求用户授权的消耗性诊断，不能冒称常设例外。列其一次性不可重跑所依赖代码的停点安排，符合 engineering-workflow §4；失败只回具名返工，不隐含追加冒烟。§9 次数选择与 B/C/§7/AC-15 同步，不把用户选次数视为自动签全部维度。 |
| AR1-6 | AC-7 原件沿用 USER-4A，但账本准入“仅作本项”指 CAPTURE；零提交时“全部提交 IoU≥0.5”可空真。AC-8 缺精确输入闭集/时钟重放与判定分母；AC-12 对 tools/eng_fastfix 禁读评分产物又写真值只在 score_，隔离边界不明。 | USER-4A 不自动跨 work ID 生效；先按下文 SOURCE 提请，未准入不冻结相关证据合同。原图人工登记点击/注入剧本与非真值状态重建、检测缓存/两臂/无新推理身份绑定明确；逐注入输出成功/失败/歧义/截止及缺失证据，n_injected/n_committed=0 如实记无成功证据，不空真宣称重捕通过。AC-8 指明日志字段/连续片段完整性、可对应区间与处理时钟/最新指针模拟边界，不能称精确复演或用局部源补 CAPTURE。评分入口闭集与运行时入口隔离，动态证明真值不回流；AC-16 逐段分母、缺真值/缺日志/未完成一圈不得判 PASS。 |
| AR1-7 | §3.5 journal_prev_s 属上一帧，不能未经说明加入本帧 total 的加和；门值重核所需加载→发布耗时与处理计时起点未对齐。§3.7 新增“三个”占位却§2.2称两个；§6/AC-15 STOP 表未枚举，数值出处/条件不齐。 | 时间线明确同帧区间与不重叠段、上一帧写盘单列、失败/未发布帧的统计口径、与发布门同源时钟及采样重叠计法；用假时钟验证 AC-9，不能靠 null 免除可测段。所有门/STOP 数值列四类出处、运行条件与比较基线；0.4/2 是移植限值，不能称本机最优，1% 是建议分流线而非验收 STOP；候选值由用户签，新正式证据后不反调。占位计数/用途一致；逐码写停止哪些步骤、保留原件/零模型安全收尾、耗用计量和 UNKNOWN 处置，随信封交用户确认。F10 沿诊断原表保留七行与“六次”冲突，不改诊断原件、不借汇总推根因。 |

#### 待用户（§9 四项原样转呈；全部未答、未签）

以下题面与原推荐原样保留，接受角色不代选。前四题的决定只能在用户答复并逐字入账后落实；D2 可先零消耗修正文义与清单，未获用户逐字授权前不得开展消耗。

1. **Play 次数与约束 1**：(a) 冒烟 1 + 正式 1（推荐：用户偏好先诊断冒烟再查错；CAPTURE 正式 Play 直接被时序尖峰终结，冒烟可先暴露）；(b) 只正式 1（贴合约束 1 字面，但门值重核只能用旧数据）；(c) 本轮只做阶段 A，Play 另定。
2. **执行机**：离线 Mac mini、Play MacBook Air（推荐，沿用户 10-02 分工）。
3. **AC-8 TX 维度**（复制 formal-redo ≤ 200 帧片段到 mini）：签（推荐：这是唯一能复演真实第 647 帧事件的离线证据）或不签（AC-8 记 NOT_RUN，不影响其余）。
4. **占位值**：`N_drop = 3`、`T_reacq = 10`、`ρ_reacq = 1.5`（推荐按占位进入，冒烟后只报读数不改值）。

| 用户题 ID | 推荐与为何只能用户定 |
|---|---|
| PLAY | 保留原推荐 (a)，但先修 AR1-5、列精确信封与代码停点；它新增两次 Play 且改变主线“一次 Play”资源约束，只有用户能给该例外。既有 CAPTURE 超耗不抵偿新额度。 |
| MACHINE | 保留原推荐 mini 离线/Air Play；10-02 分工不能替新项签设备与执行权限，接受角色不能代定硬件/执行边界。 |
| TX | 保留原推荐有条件签，仅在连续片段与字段来源可核、TX 各维齐全后申请；第647事件只能作有限复演，原题“唯一能”不构成已证因果。新增跨机原件传输/磁盘额度与用途必须由用户签。 |
| VALUES | 保留原推荐三个占位，但先明确ρ用途与有界窗口；这些是报告/恢复时限及歧义风险设计预算，非已标定数字，改变控制安全边界不能由 D7 或接受角色代拍。 |
| ROUTE-K2 | 推荐在 AR1-1…3 收束后，准许捕获模式 G1/G2 安全范围走 engineering-v1，兼容/围栏/真值红线不变；角色细则明确运行时安全换轨先问用户，本轮不生效。 |
| SOURCE | 推荐把 USER-4A 同批原始帧/位姿/CoverageEvaluator 真值限用途扩至本项 AC-7，新日志独立取证；AC-8 另限 formal-redo 可对应连续片段与经枚举的非真值处理时序字段，不准入旧评分/旧结论。原例外限 CAPTURE，新项准入/额外诊断日志字段只能由用户扩大，TX 签字不替代用途准入。 |
| ENVELOPE-STOP | 推荐待 D2 收束及设备预检后，按阶段 A/B/C 分别确认精确逐维信封、STOP 码处置及所列代码/验证范围；新方向授权明确不授权代码/模型/Play/额度，首签与缺项解除只能由用户，不能签现在的 F12 占位清单或推定全部开放。 |

**交接：Ideation 零消耗修 D2；用户事项由 supervisor 原样转呈，之后由 Acceptance 核对实际入账答复。** 不启动实现/冒烟/回放/传输，不改旧项门或正式设计；用户待决不算已答，不把推荐当额度。上表 AR1-1…7 是本次具名残留，用户题依赖分别在相应条款列明。

open_items: AR1-1, AR1-2, AR1-3, AR1-4, AR1-5, AR1-6, AR1-7

### D2 逐条回应（2026-10-10，构思；Dispatch-Id `P1-ENG-FASTFIX-001-D2-20261010T224619Z-a784`）

| ID | 完成条件的落实 | 修改位置 |
|---|---|---|
| AR1-1 | 捕获模式改用全量求值 `_gate_classified`，逐项列出 11 个检查的原因名与级别；`load_elapsed < 0`、`capture_age < 0`、缺 `capture_unix_s` 归完整性；`not_latest_loaded` 不再遮住身份核验；完整性优先、`detail.hits` 全列；完整性命中永远致命、不经降级；兼容模式仍调 `_gate`（函数体 diff 为空）。AC-1 补四组交叉与三类负值/缺值用例及兼容对照 | F1、F5；§3.1；AC-1、AC-12 |
| AR1-2 | 引入 `begin_frame`/`settle_frame`，按最新帧一次结算；只有 PUBLISHED 清零，hold/安全通道/NO_ATTEMPT 不清零；表列观测先失败、预测云台失败、观测后云台或速度中途越线、完整性、写失败、无尝试七条路径的收据、机身与结算；恰一次 HOLD 的来源与互斥；明写已写观测不回改、不声称跨桥文件原子性；`orphan_control` 改判条件。AC-2/3/16 同步 | F2；§3.2；AC-2、AC-3、AC-16 |
| AR1-3 | G2 只接「时序升级」拆载体；窗口起点改为 `resident_loop_started`，帧号与 monotonic 双截止、每 tick 判定；零轨迹/缺帧/截止帧当帧/点击·release·stop 优先级逐条；提示有效性（`f_last` 须无完整性命中、`hint_stale`/`hint_invalid`）；合成先验 = 完整 8 维 KF 同库方程预测 + pose-center 雅可比变换，phase `reacq_prior`、单位、有限性与 S 可逆；门只用合成先验、不以候选自身自证；竞争沿 m_nis 累计 NIS；`ρ_reacq` 无用途已删。新 origin `reacquire`/relation `REBUILD_REACQUIRE` 闭集末尾追加，TaskSpec/intent/episode/evidence/回滚写清；完整性重建不重捕，BROKEN/DISPUTED 不复活 | F4、F7–F9；§3.3、§3.7；AC-5、AC-6 |
| AR1-4 | 删除 F12 占位引用，新 F12 以零模型源码 grep 列真实加载路径闭集与全套构造次数；§5 改为粗粒度：每阶段只列候选结构上限、模型加载总量、计算/阶段墙钟、磁盘峰值（含附属路径）、ID、TX（方向/次数/帧/字节/Air 暂存峰值），其余为 0；共账、启动前拦截、UNKNOWN 停报（AC-19）；复核消耗计入同账；mini/Air 未核项先预检、依赖维度预检后呈签；R1-4 不触发（另写账本）、R2-2 确定触发，不改旧债。按七题答复「信封粗粒度」不做逐候选/逐帧细分，推理帧不单列的理由写入 §5.0，交接受裁定 | F12–F13；§2.4、§5、§8.2；AC-13、AC-19 |
| AR1-5 | 冒烟改为另行请求签发的**消耗性诊断**（不冒称 §4.3.2 通道），ID 写 0/≤1/≤1；产物只作门值读数、不进证据；依 engineering-workflow §4 把代码停点前移到冒烟之前，冒烟后改动回同一停点再放行；失败只回具名返工、不追加冒烟；§9、§5、§7、AC-15/20 同步，用户选次数不视为签全部维度 | §5.2、§5.3、§7、§9；AC-15、AC-20 |
| AR1-6 | AC-7 输入用途依七题答复 SOURCE（待接受核对入账），剧本只看原始帧登记、运行前入 sha；注入复用与会话同一路径、检测缓存键与零推理、两臂；逐注入七类输出；n_committed = 0 记无成功证据、不空真。AC-8 列连续片段（584–783）、字段闭集、完整性核与时钟/最新指针模拟边界，判据去真值、称有限复演。评分入口闭集 `score.py::score_*` 与运行时入口隔离、毒化真值字节相同与打开审计；AC-16 逐项分母，缺日志/缺真值/未满一圈记 `INCOMPLETE` | §2.2、§3.8；AC-7、AC-8、AC-12、AC-16 |
| AR1-7 | 计时改同源 monotonic，七个标记首尾相接、各段之和 = total，上一帧写盘单列；失败/旧帧口径；`gate_eval_s` 与门同源同起点；重叠按区间交叠计。门值与 STOP 数值标出处四类；0.4/2 称移植限值；1% 改称建议分流线；新增参数计数统一为 2（ρ 删除）；STOP 表 12 码逐条写停什么、零消耗收尾与 UNKNOWN 处置，随信封呈用户确认；F10 按诊断原表保留 7 行与「6 次」冲突、不推根因 | F10；§3.4、§3.5、§3.7、§6；AC-9、AC-17 |

**七题答复落实**：PLAY (a) → §1、§5.2/5.3；MACHINE → §5.0；TX 有条件 → §3.8、§5.1 TX 行（单独签）；VALUES → §3.7（N_drop/T_reacq 按占位进入；ρ 删除另由下文接受裁定批准）；ROUTE-K2 → §2.1（裁定仍归接受角色）；SOURCE → §2.2、§3.8；ENVELOPE-STOP → §5、§6（分阶段、粗粒度、未签即 0）。

**自查残留**：无新增用户题。请接受角色重点核：(1) 粗粒度信封是否需在某维细分（§5.0）；(2) §3.3 合成先验用库 KF 方程离线外推是否满足 K3；(3) 若 `resident_core.py` 需新增只读访问器，是否接受列入改动闭集。


### D2 接受裁定（2026-10-10，Acceptance）

**裁定：`ACCEPTED`。逐字轨道裁定：准许本工作项 `Workflow: engineering-v1` 生效。** 新 ID 自起草即有申请；账本同日「用户答 D1 退修转呈七题」原话「按推荐，信封粗粒度」已给 ROUTE-K2 条件授权，本轮按下列首次接受释义收束 AR1-1…3。捕获模式 G1–G5、AC-1…20、代码停点 `K1K2K3K4` 与正式证据停点 `PlayK2K3K4` 成为本项合同；不触发 K5。本轮是零消耗 D 轮合同裁定，尚无实现候选，不填写 C 轮核对表、不签独立 verdict/UNITY_NA/DONE。

#### 七题效力与 AR1-1…7 核清

| 条目 | 接受结论与依据 |
|---|---|
| AR1-1 | 收束：§3.1 全量求值、完整性优先；未来采集时刻、负处理时间及 capture_age 超限都不经降级；AC-1 明列交叉/边界与旧 `_gate` 对照。无法求值的完整性检查按拒绝处理，不能把缺结果当通过。 |
| AR1-2 | 收束：§3.2 与 AC-2/3 按最新帧一次结算；安全 HOLD、无尝试与旧帧不能清零；观测已 WRITTEN 不回改，同帧后续越线仍结算 DROPPED，恰一次 HOLD；完整性失败独立致命。 |
| AR1-3 | 收束：§3.3 与 AC-5/6 从载体就绪计双截止，零轨迹/零新帧也有界；合成 prior、竞争、事务与提示落盘均已具名；截止与人工取消的字面歧义按下节解释。完整性重建不进入重捕；BROKEN/DISPUTED 不复活。 |
| AR1-4 | 按用户粗粒度要求收束：§0 F12 源码闭集与真实构造两处相符，§5 给总加载/执行墙钟/磁盘/TX/ID 上限，复核同账。无须增加逐候选、逐帧或逐 ID 额度；完整计量口径按下节补齐。设备、输入及路径预检仍未核，不把草案当可即时首签。 |
| AR1-5 | 收束：§5.2 已明确另请首签的消耗性诊断，§7 将 C/R/接受消费置于一次性冒烟之前；诊断不进验收门，失败不隐含重跑。 |
| AR1-6 | 收束：SOURCE 用途扩展已入账；§3.8 枚举输入、非真值剧本、缓存身份、有限时钟模拟及评分隔离；AC-7 排除零提交空真，AC-16 缺日志/真值/一圈记 INCOMPLETE。原件完整性未核时相关步骤仍 NOT_RUN/拒启，不冻结未实测的工件体积或新归档 schema。 |
| AR1-7 | 收束：§3.5 同源相邻段、上一帧日志单列；§3.4 是读数建议线，0.4/2 为移植值；§6 逐码处置随信封首签。失败/致命帧及安全收尾的统计、计量按下节解释。F10 七行/六次冲突保留，不改原诊断、不用该计数推断。 |

PLAY (a) 与 MACHINE 已答，分别落实冒烟 1 + 正式 1、mini 离线/Air Play；两次仍各待额度首签。TX 是有条件方向同意，不是传输许可；SOURCE 是用途准入，不是证据已通过。VALUES 的 `N_drop=3`、`T_reacq=10` 按占位冻结，冒烟后不改。**ρ 删除由本轮接受侧批准构思的无用途占位收窄**：D1 AR1-3 已要求不用则提请删除，D2 明确无算法用途；删除不放宽任何门、时限或安全行为，不把它冒称用户选了新的值或已签删除。七题账本仍按原文读，不重问。ENVELOPE-STOP 按分阶段、粗粒度执行，首签及 STOP 缺省处置仍待用户；本裁定不授权代码/模型/传输/Play 或任何额度。

#### 首次接受释义（本合同组成部分）

以下只明确既有 AC 的执行口径，不新增 AC；与正文发生歧义时按本节。

1. **AC-5 窗口与请求优先级**：最后允许帧为 `f_ready+T_reacq−1` 且提交时 monotonic 年龄必须 ≤ `T_reacq/hz`。等于边界可提交；任一维严格超过边界即先失效，不得因为先算候选、后记失败而提交过期证据。每 tick 检查，零帧照样到期。stop/release 取消原任务；人工点击仅取消重捕提示与缓冲，随后完整执行现行点击事务：成功保留新 TRACKING 任务，拒收按现行规则处理，**不得再用“取消后 CANCELED”覆盖新点击任务**。AC-5 的同帧与零帧用例逐字段检查任务/提示/绑定终态。
2. **AC-5/6 K3 与访问器**：准许 §3.3 用钉版库 KF 同类、同常数预测旧绑定的完整状态，再施加 pose-center 映射；这是拟实现算法的接受，尚非实测等价。提示需携带 sensor/library 帧、旧绑定键、posterior phase、检测画幅/单位与有效性；在各合格观测帧保存深复制状态，不能在拆载体时把当前状态冒充更早的 f_last。现有 `DetAssocTracker.associator` 可只读提供完整状态；`HistoryEntry`/`KfSnapshot` 已丢失完整协方差，不能靠只读 getter 恢复它。准许 `resident_core.py` 在 §2.1 闭集内新增只读深复制访问器/承载记录，完整状态须由获准会话或 TrackLoop 路径取得并输入；不得回写库、改变检测/关联、现有 binding 快照/回滚或兼容记录，`det_assoc_tracker.py` diff 仍为空。无法满足时在「待裁定」停报，不自行扩大闭集。AC-6 反证用例指**改变候选自身 prior 而保持合成 prior 与检测不变，结果不变**，不是把门的合成输入替换成候选 prior。另以同一完整输入对照钉版库预测方程及 pose-center 的均值/完整协方差，缺帧 n、映射失败、非有限与奇异 S 各有具名证据。
3. **AC-5/13 事务与重放**：新 episode 的 `association_revision=0`，episode_seq 加 1，成功提交 version 按现行一次递增；TaskSpec/intent_revision 保持。旧 episode 只在拆载体时关闭一次。失败不产生新 binding/episode 或成功提交计数，回滚失败沿 fail-closed。重捕起止、同源时钟、合成 prior/有效性及请求次序均作为非真值输入落盘；重放不依赖旧载体隐含内存，不凭未记录的在线时钟重判窗口，事件逐条相同。R2-2 的链式引用/连续性覆盖这些新增输入；兼容旧路径不因此改判。R1-4 如实际调用旧账本函数仍触发具名承接，两个旧 OPEN 债不在本轮关闭。
4. **AC-9/17 时间线**：有门控尝试的 DROPPED、REJECTED 与升级致命帧，凡已读出的同次门 load_elapsed/gate_eval 均入分布与对应分母；不能用“会话致命”排除超线尾部。未到达的段带 missing_reason，已到达可测段照记。七标记的相邻区间和是 total；假时钟使用可精确表达的数值验证，实时时钟的浮点舍入不作为新性能门。冷启动、积压批、实际运行 hz/分辨率、CPU/MPS 与采样重叠分列；1%/0.6 s 仅分流建议，不是停止下一步的性能 STOP。安全/身份硬拒与用户签发资源上限独立生效。
5. **AC-14/19 粗粒度计量**：阶段 A ≤3 候选、每候选停点全套至多一次（工程流程本有要求，非新增子额度），真实加载总量 ≤14；focused、复核红绿、崩溃重载、回放、评分、计量及验证收尾执行均共用 ≤2 h。墙钟总量按执行区间累计，重叠区间取并集，不扣失败执行、不算跨角色排队等待；不是仅统计模型 predict。B/C 的阶段墙钟从本次预检开始含归档、评分、提交/推送及收尾，Play 墙钟从实际按 Play 起算，到实际停下；会话 300 s 不替代按钮墙钟。GB/MB 按十进制 B。阶段新增磁盘峰值含 outputs、runtime、session、检测缓存、TX/解压/本地复制暂存、测试临时目录、证据、git 及可归属客户端/日志；启动前登记这些具名根与副作用计量办法，不能只用 §3.6 三类遍历根宣称完整峰值。无法计量的部分为 UNKNOWN，停报，不自行补 0 或申请豁免。仅共用总量与预算内收尾预留，无须细分额度；安全停止后不启动新消耗，保存/计量/提交也占原有墙钟和磁盘，留足余量；操作单提早发停令，实际停止超过上限仍记偏差，不把发令时刻当实际停止。耗尽时只做必要安全停令并报告偏差。
6. **AC-10/14/15/19 本机资源与 STOP**：冻结规格优先 MPS、不可用回 CPU，测试 CarrierSelfTest 明确 CPU；它们都是已选 Mac 的本机执行。草案原“GPU=0”若按所有加速器解释会与本路径冲突，故首签题面必须显式请求：**本机 CPU/MPS 只在所在阶段统一墙钟/加载上限内；云 GPU、训练、新加速设备及板端为 0**。此为未签草案的资源口径补齐，不是已获本机 MPS 许可；未获逐字首签不得推理。无需加独立 GPU·h 子上限或逐帧限额。计量日志截断不得变成无监控继续：若无法留下可核读数即 S-UNKNOWN；其余逐码按 §6，S-BUDGET/S-DISK 停后不得靠后续步骤越过总量/未知边界。所有处置仍由用户随阶段信封首签；未签时照旧停报。

#### 三阶段首签题面（原样转呈；均非已签）

先由 supervisor 安排 §8.2 **零消耗只读**设备/输入/槽位/路径预检，读数写具名 preflight 节；不导入或构造模型、不回放、不跑测试、不传输。依赖未核项不呈签；AC-8 核不齐则记 NOT_RUN，仍可呈签不含 TX 的 A。下列题面是本轮冻结的呈签草案，预检事实变化须先由 Acceptance 更新，不由 supervisor 默改或首签。首签含本节释义对应的代码、配置、工具与验证闭集；现阶段实现未获授权。

- **FASTFIX:A:1（含可选 TX，须分别明示）**：“预检满足后，是否签发阶段 A：Mac mini、§2.1 G1–G5 及 AC-1…20 所需代码/操作单准备，离线验证限 AC-1…15/19（AC-16…18/20 的现场执行留 B/C）；候选 ≤3，每候选停点全套至多一次，真实模型加载全阶段 ≤14，验证执行及收尾总墙钟 ≤2 h，新增磁盘总峰值 ≤2 GB；scenario/session/run ID=0/0/0，Unity/Play=0，API/云/云 GPU/训练/下载/安装/板端=0；本机 CPU/MPS 仅在上述统一总量内。AC-8 TX 单独选择签/不签：Air→mini 1 次（失败/重试共账）、第584–783帧≤200帧及两份枚举日志字段抽取、总传输≤50 MB、Air暂存峰值≤50 MB，mini副本计入2 GB；不签则TX=0、AC-8 NOT_RUN。确认§6适用STOP及本裁定收尾/UNKNOWN处置，不继承旧余额。” **推荐：预检齐全后签 A；TX 仅来源连续性/字段/体积可核时签，否则暂不签。为何只能用户定：代码执行、模型、跨机传输、资源首签与 STOP 处置不能由接受/supervisor 授权。**
- **FASTFIX:SMOKE:1**：“A代码停点独立复核通过并经接受消费、Air预检满足后，是否签发一次消耗性诊断冒烟：Air、本机CPU/MPS会话模型加载≤1，Unity Play=1（失败占用、不重试），实际Play墙钟≤300 s，预检到收尾提交/推送阶段墙钟≤60 min，scenario/session/run ID=0/≤1/≤1，新增磁盘总峰值≤1 GB；API/云/云 GPU/训练/下载/安装/传输/板端及其余未列维度=0；产物仅作门值读数、不进验收门。确认§6 STOP及本裁定收尾/UNKNOWN处置；失败只交具名返工，不隐含追加冒烟。” **推荐：前置齐全后签。为何只能用户定：PLAY方向答复未签任何额度，本次真实Play/ID、模型与资源首签及停止处置只能用户签发。**
- **FASTFIX:PLAY:1**：“冒烟报告已核、若改动已回代码停点复核并经接受消费、Air预检满足后，是否签发一次正式Play：Air、本机CPU/MPS模型加载≤1，Unity Play=1（失败不重试），实际Play墙钟≤300 s，预检/Play/离线评分/提交推送及收尾阶段墙钟≤90 min，scenario/session/run ID=0/≤1/≤1，新增磁盘总峰值≤1 GB；API/云/云 GPU/训练/下载/安装/传输/板端及其余未列维度=0。t_pub/k_pub保持0.4 s/2帧，或另按冒烟预登记建议由用户明确签0.6 s/3帧并回代码停点；N_drop=3、T_reacq=10不改；正式工件后不反调。确认§6 STOP及本裁定收尾/UNKNOWN处置；正式产物交PlayK2K3K4停点与用户AC-18目检。” **推荐：前置齐全后签，门值未另签保持原值。为何只能用户定：正式Play/ID/资源首签、控制门值改变与停止处置只能用户定，接受代码通过不能代签。**

上述本机资源与计量口径须进入最终首签原文，不能省略为“七题已按推荐，所以额度已签”。数值出处：阶段 A 14 的构造闭集与 CPU 全套旧读数、2 h 为实测基础上的设计余量；B/C 300 s 为本次资源申请（旧会话299.9 s仅背景）、60/90 min及2 GB/1 GB/50 MB为设计预算，未核投影不作目标条件通过线。S-DISK 90%是用户拟签资源上限的收尾预留，非模型性能门。正文门/停止条件没有厂商标称/异条件移植性能值导致的后续停跑；继承的身份/安全合同仍照守。

**交接：Supervisor 零消耗只读预检并准备分阶段原样首签转呈；预检后由 Acceptance 核清事实，再交用户首签。** 当前所有额度为0；不派发实现、模型、冒烟、正式Play或传输。首签落实后才按§7接力；旧CAPTURE失败、OPEN债及其他暂停项原样保留。本轮没有新增预算细分要求，也不提前放行消耗。

open_items: none

### D2预检核清（2026-10-10，Acceptance）

本轮只核清 `docs/evidence/P1-ENG-FASTFIX-001-preflight.md`「D2预检」及差异1–7，对照§8.2与「D2 接受裁定」；不复测设备、不跑测试、不签资源或独立verdict。`ACCEPTED`/`engineering-v1`保持；既有裁定原文保留，现行首签入口改为本节。原始读数只证明所读对象及当时状态，不证明完整运行、全部计量路径或可构造跟踪器已实测。

#### 1. 差异1–7逐条裁定

| 差异 | 裁定与执行读法 |
|---|---|
| 1 mini落后66提交 | 不把“代码/工具/测试/配置无差异”当开工版本一致。A首签后、任何改码/验证前，执行者在mini记录工作树与引用，fetch并仅fast-forward到本次实际派发基线，再核工作树干净、HEAD与基线一致；基线由派发/git运行时解析，不手抄SHA。不得merge、reset、覆盖本机改动或凭陈旧origin/main开工；无法快进/有新增差异即S-PRE停报。仓库同步明确列入A题面，时间与新增git字节共账；不授权模型/数据下载。当前尚未同步，不称开工条件全满足。 |
| 2 Air残留 | 无写者、帧槽/覆盖文件不存在只满足部分前置；8个旧桥文件与旧resident目录仍在活读取/归档路径，B/C当前S-PRE未解除。AC-15/19释义与拟议同卷保全范围见§2；旧CAPTURE的两对象迁移授权不继承到本项。本轮不挪、不删、不清槽。 |
| 3 解释器差异 | 不要求两机Python补丁版/numpy逐值相同，不安装或升级以追平。mini跟踪器相关测试与回放明确使用数据根`.venv-yoloe`，权重/数据根以绝对路径显式登记，不依赖未设的`ENG_DET_DATA_ROOT`。lap仅dist-info已核，构造能力仍未运行；实际构造列入签后A的既有加载/墙钟总量，失败停报，不能借此安装。Air按自己的已核venv登记，环境差异进入读数，不推跨机数值等价。 |
| 4 648–650无处理记录 | **AC-8 `NOT_RUN`，TX当前不可呈签。** 200帧jpg/json及归档sha保全成立，处理记录仅覆盖197帧；3帧缺`frames_processed`批次及metadata_sha对照。“无收据帧按批内顺序推进”限已有批次记录的帧，不能扩到未处理帧。不得用归档清单替代会话记录、补写批次、删3帧或缩换片段。恢复须找到并核实同一原会话已存、可认证的处理记录与完整字段，仍满足固定584–783片段；找不到就保持NOT_RUN，不为此重采集。若要改有限复演输入/判据，须另交用户定范围并先改合同，不凭TX签字放宽。A不含TX仍可呈签，AC-8不计。 |
| 5 647无capture_age_s | **AC-8 修订1（解释§3.8/F14字段要求）**：按现行首命中顺序，647的load_elapsed先拒，capture_age未计算；抽取保留字段缺失并标`not_computed_first_hit`，不得填0或事后推算。该情形本身不触发NOT_RUN；用于时钟注入的`load_elapsed_s`/`latest_frame_id`与该条身份、通道、时刻字段仍必需。其他缺字段不可援引本例外。此修订不解除差异4、不将旧首命中收据当全量门检查结果。 |
| 6 区间外缺号/latest异常 | 保留读数与原因UNKNOWN；不读取现存latest作为历史回放指针，不扩区间或推定全源完整。若未来AC-8具备准入，只按收据latest_frame_id模拟，仍是有限复演；当前NOT_RUN。该异常不影响独立USER-4A输入准入，不改CAPTURE原失败/缺项/主张。 |
| 7 实测体积较小 | 约39KB/帧、整片段及所列日志约8.0MB，是原件读数，未实际抽取/传输。50MB传输/Air暂存上限不改，不追加或返还额度；即使体积有余量，差异4仍阻断TX。最终派生产物须启动前核字节、来源与峰值。 |

§8.2逐项结论：mini输入1,669行sha全一致、权重/freeze一致、磁盘足、依赖静态存在；构造待签后验证。Air无写者/磁盘足，活路径残留未解。AC-8原件保全通过、处理来源不齐。跨进程时钟依据预检§4的系统读数与存档旁证接受为计量设计前置，未来冒烟仍须以unix交叠对照核，不声称本轮已实跑工具或验证采样重叠。

#### 2. AC-15/19与S-PRE释义：活路径残留、保全与计量

**AC-15 修订1（解释§6 S-PRE与操作单前置）**：S-PRE判据针对**本阶段实际读取、写入或归档的路径**，不是`runtime/`任何历史字节都必须不存在。A不读取Air活槽、不开Play，不因Air残留阻断不含TX的离线A。B/C操作单须在A准备时列闭集：帧桥/`latest.json`、`scenario_config.json`、8个桥文件（`body_command.json`、`gimbal_command.json`、`tracking_observation.json`、`metrics.json`、`tracker_state.json`、`language_request.json`、`road_scene_audit.json`、`route_corridor_audit.json`）、`runtime/runs/`及实际归档源、真值输出路径；执行前旧内容不得混入这些活路径。新阶段自己生成的配置/目录必须可归属新阶段，不算旧残留。

历史hold目录/文件仅在操作单已枚举且证明不被本阶段读取、覆盖或归档时可原地保留；不能仅凭mtime旧就排除。预检没给完整路径闭集，故当前不签“残留全无风险”。无法判明路径归属/是否有写者即S-PRE，无法核计量则S-UNKNOWN。首次Play前再核现场无Unity Play、会话/点击页/其他写者及锁冲突，不能沿用本次静态读数代现场确认。

拟议保全只限上述8个旧桥文件与`runtime/runs/`完整旧目录，源清单在操作单逐项登记；同卷rename到`outputs/eng-fastfix/preexisting-runtime/`当场排他创建的唯一目录，无覆盖、不删除、不改内容、不跨卷、不复制后删源，前后逐文件数量/字节/sha清单一致。其余历史对象原地保留且隔离；若再发现活路径残留，先停报、由接受核清题面，不自动扩大迁移范围。`outputs/eng-capture/`三组原件及原清单不动。B后的本项产物在C之前须按同样保全原则归档并核清活路径，具体新增源闭集在C首签前落实，不自动授权挪其他目录。

**AC-19 修订1（解释§5及D2首次接受释义5的归档计量）**：这项保全许可须由用户随B/C阶段题面明确签发；本节只是拟议执行范围，旧许可不转用。同卷移动既有字节不是新增6GB副本，原字节保留、基线登记不扣减；新目录/清单/git及客户端日志、保存本阶段产物的新增字节计入该阶段1GB峰值，全部核验/归档/收尾计入60/90min。不另设归档子额度；若只能复制、计量不全或剩余总量不足就停报，不能以清理释放空间解释为可执行。

#### 3. 三阶段首签题面现行原样版本（均非已签）

按账本2026-10-10「用户答 D1 退修转呈七题」的“信封粗粒度”：保持每阶段总量，不新增逐帧、逐候选、GPU·h或归档子额度；TX依用户原有条件单独明示。**当前只呈不含TX的A；TX/B/C下列全文是条件恢复后的原样入口，当前不得作为可立即执行的首签请求。** A的同步与签后真实构造不是追加预检额度，纳入A总量；未签时不执行。

- **FASTFIX:A:1（主信封）**：“是否签发阶段A：Mac mini、§2.1 G1–G5及AC-1…20所需代码/操作单准备，离线验证限AC-1…15/19（AC-16…18/20现场执行留B/C）；开工先在mini仅fast-forward同步至实际派发基线、核工作树干净与版本一致，同步时间/新增git字节计入A；跟踪器相关测试/回放用数据根`.venv-yoloe`，显式登记数据/权重绝对路径，签后构造失败即停报、不安装。候选≤3，每候选停点全套至多一次，真实模型加载全阶段≤14，验证执行及收尾总墙钟≤2h，新增磁盘总峰值≤2GB；scenario/session/run ID=0/0/0，Unity/Play=0，API/云/云GPU/训练/模型或数据下载/安装/板端=0；本机CPU/MPS仅在上述统一总量内。当前TX=0、AC-8 NOT_RUN；可选TX须按下一条另行明示签发，不签不阻断其余A。确认§6适用STOP及本节与D2接受释义的收尾/UNKNOWN处置，不继承旧余额。” **推荐：签A且不含TX。为何只能用户定：本项代码执行、模型、本机资源首签与STOP处置尚无账本授权，接受/supervisor不能代签。**
- **FASTFIX:A:1可选TX（独立明示选择签/不签，当前不可呈签）**：“仅在固定584–783片段及同一原会话处理记录完整性均已核齐后，是否另签AC-8 TX：Air→mini 1次（失败/重试共账）、≤200帧jpg/json及两份枚举日志字段抽取，总传输≤50MB、Air暂存峰值≤50MB，mini副本计入A的2GB与执行墙钟总量；不取真值、旧评分或旧结论，不动原件，传完仅删本项暂存；其余维度不追加，STOP与UNKNOWN处置同A。不签则TX=0、AC-8 NOT_RUN。” **推荐：本次不签，维持AC-8 NOT_RUN。为何只能用户定：来源齐全也不能替用户签跨机原件用途与传输/暂存资源；缺处理记录不能靠首签追认为合同满足。**
- **FASTFIX:SMOKE:1（当前不可呈签）**：“A代码停点独立复核通过并经接受消费、Air操作单路径闭集及计量办法已核、现场无写者后，是否签发一次消耗性诊断冒烟：Air、本机CPU/MPS会话模型加载≤1，Unity Play=1（失败占用、不重试），实际Play墙钟≤300s，预检到收尾提交/推送阶段墙钟≤60min，scenario/session/run ID=0/≤1/≤1，新增磁盘总峰值≤1GB；API/云/云GPU/训练/下载/安装/传输/板端及其余未列维度=0。明确允许本节§2列明8个旧桥文件及runtime/runs完整旧目录同卷无覆盖rename保全，前后数量/字节/sha一致、时间/新增字节共账；其他原件不动，迁后复核S-PRE满足才加载模型/按Play，异常停报、不追加额度。产物仅作门值读数、不进验收门。确认§6 STOP及本节与D2接受释义的收尾/UNKNOWN处置；失败只交具名返工，不隐含追加冒烟。” **推荐：完成前置后签，当前暂不呈签。为何只能用户定：PLAY方向答复不含额度；真实Play/ID、模型、保全迁移、资源首签与STOP只能用户签。**
- **FASTFIX:PLAY:1（当前不可呈签）**：“冒烟报告已核、若改动已回代码停点复核并经接受消费、Air操作单及现场预检满足后，是否签发一次正式Play：Air、本机CPU/MPS模型加载≤1，Unity Play=1（失败不重试），实际Play墙钟≤300s，预检/Play/离线评分/提交推送及收尾阶段墙钟≤90min，scenario/session/run ID=0/≤1/≤1，新增磁盘总峰值≤1GB；API/云/云GPU/训练/下载/安装/传输/板端及其余未列维度=0。允许已核C操作单闭集内的本项B产物同卷无覆盖rename保全、前后数量/字节/sha一致，归档与新增清单共用上述总量；源闭集未核不呈签、S-PRE未满足不启动模型/Play，不动其他原件。t_pub/k_pub保持0.4s/2帧，或另按冒烟预登记建议由用户明确签0.6s/3帧并回代码停点；N_drop=3、T_reacq=10不改；正式工件后不反调。确认§6 STOP及本节与D2接受释义的收尾/UNKNOWN处置；正式产物交PlayK2K3K4停点与用户AC-18目检。” **推荐：完成前置后签，门值未另签保持原值，当前暂不呈签。为何只能用户定：正式Play/ID、资源及保全迁移首签、控制门值改变和STOP不能由代码通过或接受/supervisor代签。**

不可呈签的缺项与恢复条件：TX缺3帧同源处理记录，按§1差异4恢复；B缺已消费代码通过轮、最终操作单/路径隔离计量闭集与现场无写者确认，齐后才呈含保全许可的B，签后先保全/复核再启动Play；C另缺冒烟报告与必要返工通过消费、B产物归档源闭集及C现场预检，齐后再呈C。未解决项不要求拆出新的微额度，不签等于0；未来读数若变化，接受先核清更新题面，supervisor不得默改。全部门值不变；本轮不作完成/通过裁定。

open_items: none


### A首签落实（2026-10-10，Acceptance）

#### 1. 账本核对与传输效力

依据 `docs/authorizations.md`「2026-10-10 P1-ENG-FASTFIX-001 — 用户首签 FASTFIX:A:1（阶段 A，Mac mini 离线）；TX 不由角色执行，所需文件由用户自行传输」；用户原话「签A，需要传输的文件我去传输」。本轮核对完整合同、首签条目与「D2预检核清」§3 主信封，裁定 **FASTFIX:A:1 主信封已签、生效**；`ACCEPTED`/`engineering-v1` 保持，尚未实施，不签实现通过、独立 verdict、UNITY_NA 或 DONE。

账本「授权范围/信封」与现行主信封**逐维实质一致，无冲突或扩大**：同为 Mac mini，G1–G5/AC-1…20 代码与操作单准备、离线验证 AC-1…15/19；仅 fast-forward 同步、显式路径、失败停报不安装；候选≤3、每候选全套至多一次、加载≤14、墙钟≤2h、峰值≤2GB；ID/Play/API/云/训练/下载/安装/板端与角色TX均0；CPU/MPS共用总量，STOP/UNKNOWN同源且不继承余额。措辞非逐字复制：账本以引用主信封原文涵盖“AC-16…18/20现场执行留B/C”，以“Unity/Play=否（0）”表述原文“=0”；其授权范围/效力段承载原文TX与AC-8限制，不另造额度。执行以「D2预检核清」§3主信封原文及用户原话为准，下节仅落实该原文。

接受 supervisor 对传输的读法：用户自行传输是用户设备操作，不计角色 TX、不构成可选 TX 首签；角色不得执行 Air↔mini 文件复制。用户传输不解除缺第648–650帧同源处理记录的来源缺口，AC-8仍 `NOT_RUN`，不计验收；不得补写处理记录、缩换片段或借文件到位变更判据。可选TX恢复仍按「D2预检核清」§1差异4与§3，须来源核齐并另行明示首签。

预检已核 USER-4A 原件在 mini、sha一致，代码另按获签的git同步；当前未识别出A另需用户传输的文件，**本轮 needs_user: none**。若实现发现实际缺文件，停下依赖该文件的步骤，将具体源/目的绝对路径、用途、缺失原因与推荐用户传输写入接力报告 needs_user；角色不代传、不下载。文件到位后先登记来源、计数/字节/sha并按已准入用途核验，才可在A总量内使用；新用途或越界不能由“用户传输”补授权，未知即停报。

#### 2. 生效信封与占轨判定

| 项 | 已签执行边界 |
|---|---|
| 阶段/执行机/范围 | A，Mac mini；§2.1闭集内G1–G5及AC-1…20所需代码/操作单准备，离线验证限AC-1…15/19；AC-8 NOT_RUN，AC-16…18/20现场执行留B/C |
| 候选与验证 | 候选≤3，每候选停点全套至多一次；全阶段真实YOLO构造≤14，含focused/全套/回放/崩溃重载/复核所需真实加载，成功失败重试共账、失败不返还 |
| 墙钟 | 验证执行及收尾总墙钟≤2h；首次接受释义5的执行区间并集累计口径保持，仓库同步也入账，不算跨角色排队；安全收尾/计量/提交留足原总量余量 |
| 磁盘 | 新增总峰值≤2GB（十进制）；outputs/runtime/session/缓存/本地暂存/测试临时目录/证据/git及可归属客户端日志等具名根与副作用均计量；同步新增git字节与用户传入后mini新增字节亦入峰值，不因角色TX=0豁免磁盘 |
| 本机计算 | CPU/MPS仅在统一加载/墙钟总量内；优先MPS、不可用回CPU，CarrierSelfTest用CPU；不另设或签GPU·h子额度 |
| 零维度 | scenario/session/run ID=0/0/0，Unity/Play=0，API/云/云GPU/训练/模型或数据下载/安装/板端=0，角色TX=0；其余缺项为0，旧余额不转用 |
| STOP/UNKNOWN | 用户首签确认§6适用STOP、「D2预检核清」及首次接受释义的收尾/UNKNOWN处置；启动前余额不足拒启，计量缺失/损坏/不可得停后续消耗并报UNKNOWN，不推余额、不重试追加、不靠收尾越界 |

**占轨：交接 Consuming=no。** AGENTS.md/协作工作流§7以创建或消耗scenario/session/run ID、Play配额、API预算为占消耗轨判据，A这些维度均0；真实模型加载与本机资源虽受信封计量，不自动改此闭集判据。全局仍0条消耗性、2条零消耗活跃交接，保持轨道上限与Gate-echo；本裁定不允许借A启动产生ID的真实会话或Play。

#### 3. 实现派发前提、顺序与交接

1. supervisor事实核查本轮已提交并推送、单写者与轨道成立后，派发 **Implementation（Mac mini）** 落实A；本轮未操作mini或其他设备，不声称同步或构造已完成。实现开工先读现行合同/本节与预检原始读数，记录mini工作树和引用，fetch后仅fast-forward到该次实际派发基线，再核干净与版本一致；基线由派发/git运行时解析、不手抄SHA。不得merge/reset/覆盖本机改动，无法快进或新差异即S-PRE停报；同步时间与新增git字节计入A。
2. 改码/验证前显式登记仓库、解释器（数据根`~/TetheredDroneTracking-full/.venv-yoloe`）、数据/权重/清单与输出/计量根的**绝对路径**，不依赖未设的`ENG_DET_DATA_ROOT`；核现行sha与阶段实际路径、写者和剩余量。跟踪器相关focused/全套/回放只用该数据根venv，不安装或升级。构造能力仍未实测，签后构造计入既有A总量，失败即停报，不修环境越界；计量未闭合先S-UNKNOWN停报。
3. 在§2.1改动闭集与首次接受释义内实现G1–G5、准备AC-15两份操作单及计量/隔离办法；A只准备Air操作单，不清槽、迁移runtime或执行B/C。按AC-13承接R2-2；旧R1-4仅实际复用触发时补回归，旧债/负结果保持。开发期focused，稳定候选停点全套每候选至多一次；日志写文件只回显摘要、不带-v，基线失败与新增失败分列，不把失败中间版交复核。
4. 按§7停在代码候选 **K1K2K3K4 → C → R → 接受消费**。实现者将workflow§4.3.1四项自证、逐AC证据与未验证风险写入`docs/evidence/P1-ENG-FASTFIX-001-K1K2K3K4-handoff.md`具名小节，AC-8明确NOT_RUN、B/C现场项明确未运行；列完整候选diff范围、实际命令/测试结果、加载/执行区间/峰值资源账与UNKNOWN、操作单指针，不手写可派生标识。同步状态板，提交并推送稳定候选，交接Owner Acceptance、请求`C1@K1K2K3K4`（首次候选）；交接行只指向具名自证小节。接受侧只读C后独立R，返工按现行规则直接回复核。
5. 到停点停止依赖后续实现。代码通过轮经接受消费仍不签B/C；冒烟、正式Play、保全迁移与门值改签分别按「D2预检核清」§3恢复条件和§7接力，当前均未签0。角色接力报告含实际耗用非零维度、checks、claims指针与needs_user，不把A首签或离线读数当Unity/硬件验收。

open_items: none

## Contract conformance（核对表）

### C1@K1K2K3K4（2026-10-11，首次候选核对）

owner = Acceptance；Dispatch-Id `P1-ENG-FASTFIX-001-C1@K1K2K3K4-20261011T003403Z-95de`。候选由本派发及上一实现派发 finished.candidate 解析；完整范围为该候选中首条「A实现 候选1代码」提交的父提交至派发候选，含三条实现提交、31路径全部diff（含证据）。已重读合同、首签、handoff §1–§R、逐AC证据及直接关联代码。只读核对，未跑实现测试、模型或回放；以下「满足」是合同忠实性核对主张，非独立verdict。

**结论：首次退回实现，R1未开。** C1-1…4仅要求执行原AC与首次接受释义，不新增或改写AC。本停点退回次数已用1/1；修后交C2，C2即使仍有未决项也照交独立R1。`ACCEPTED`/轨道、旧债与旧负结果保持，B/C/TX未签0，运行时功能不主张UNITY_NA/DONE。

C1逐AC核对表已由下方C2最新版替换；首次退回结论、IR裁定与C1-1…4合同要求保留，历史逐AC表从本节git历史读取。

#### IR-1…16 读法裁定

以下仅核对既有合同，不产生合同修订；不认可部分按原条款返工，无法在闭集满足则另列待裁定停报，不能自行扩大实现范围。

| IR | 裁定 |
|---|---|
| IR-1 | 部分不认可：m_read0为图像读字节前与§3.5相符（元数据前置段须明示不在total）；`step`返回不等于合同的`tracker.update`返回，历史组装耗时不能冒作纯关联段，见C1-1。 |
| IR-2 | 部分不认可：纯路径结算相符；混合DROPPED/WRITE_FAILED仍按AC-3写失败不计不清，不接受自定优先级，见C1-2。 |
| IR-3 | 认可：单次同源读数与现行读取位置不改变逐项优先级或时间原义。 |
| IR-4 | 认可：f_ready取启动事件帧、事件后才开窗且该帧计入截止；不因只从下一帧收证据延长双截止。 |
| IR-5 | 认可：无绑定时沿用既有授权HOLD/不发，未改授权函数；最终命令数量仍须由会话层证据核实。 |
| IR-6 | 部分不认可：旧token校验及人工优先相符；拒收点击后新增`release_binding(cancel_task=True)`不属现行零状态变化的拒收事务，见C1-3。 |
| IR-7 | 认可：合同逐次predict完整posterior，并未要求非Tracked的multi_predict置零；同库类/常数及完整协方差对照是所需证明。 |
| IR-8 | 认可：在线提示来自最新合格观测及PUBLISHED/DROPPED；无发布门回放只证明离线重捕，不证明在线门等价。 |
| IR-9 | 认可：unix同步推进触5e时必须致命；mono单推进仅是streak用例，不改捕获年龄完整性优先，也不冒称真实积压实测。 |
| IR-10 | 认可：预测器不可得时不伪造prior/提交，窗口有界失败；不扩写合同跳过原因闭集。 |
| IR-11 | 认可：捕获v2链与匹配配置重放；兼容及旧v1语义不回改，旧工件不因此获得v2完整性证明。 |
| IR-12 | 认可：忽略本项生成输出的git管理改动是准备工作的附属项；不是运行时闭集扩大或证据免提交。 |
| IR-13 | 认可限于具名捕获回放入口、原闭集前缀逐位不变及末尾追加；基础设施排除仅限另有用户授权的协调改动，不给未来新增路径普遍豁免。 |
| IR-14 | 认可：帧元数据时钟、模拟就绪及520–828缓存范围与剧本相符；829输入完整性核验与309推理帧是不同计数，有限回放不推真实重建时延。 |
| IR-15 | 部分认可：截断停令及客户端父目录保守纳入相符；不能据此认可完整峰值或采样失联处置，见C1-4。 |
| IR-16 | 认可该用例的停令出现至run返回口径；节拍/逐条检查不替代采样异常、工具失联与实际按钮停止时限的证明。 |

#### 定向退回与资源勘误

- **C1-1（AC-9，§3.5、首次接受释义4）**：`track_loop.py::_resident_frame/_capture_partial_timing/_capture_frame`须在闭集内取实际关联返回边界并保留已到达标记。当前step抛错直接将m_det置null，即使predict已返回；`on_frame`及发布阶段抛错亦可绕过计时。以检测成功后关联异常、管理器异常、发布异常的具名用例证明恰一行、已得段保留/未到达段带原因、旧检测标记不串帧；解码异常一例不足。冻结`det_assoc_tracker.py`不动，无法取边界则停报待裁定。
- **C1-2（AC-3，§3.2）**：`gated_publisher.py::settle_frame`的混合降级/写失败不可计streak或发时序升级。补实际降级后HOLD底层失败（含失败后安全回退）的生产路径交叉证据；原安全fail-closed不改，不靠直接手置上下文代替全部生产证明。
- **C1-3（AC-5，首次接受释义1）**：`language_loop.py::_action_click` finally中新加的取消任务动作与拒收零状态变化不符；`test_rejected_click_during_window_cancels_task`锁住了该偏离。点击只取消提示/缓冲，之后以现行事务决定任务终态；补拒收前后TaskSpec/runtime/version/绑定对照，成功新任务不得被覆盖，stop/release仍取消原任务。不扩成新自动恢复路径。
- **C1-4（AC-15/19、修订1，首次接受释义5–6）**：`meter.py::walk_sizes`吞PermissionError/条目OSError，`_sampler`仅捕SampleAborted，其他异常可杀采样线程而停令线程继续等待。无法核读的根/条目与采样/输出故障须可见UNKNOWN并拒启/停报，不写成0或存活计量；补具名故障证据。play-ops.md §4仅监视outputs/runtime，附属git/客户端只前后du不能证明峰值，TMP/测试临时/证据等须登记完整副作用办法或UNKNOWN；预检/rename早于meter启动却给完整3600/5400秒，计量又早于提交停止，均漏阶段边界。两份单须从预检起总计时、把保全/评分/提交推送共账并留收尾量；登记实际Play起止及提前发停令，300秒才发令不能保证实际停止≤300。保全前后清单须有数量/字节/sha，现有sha清单注释不能代替字节核验；C源闭集仍按原条件在首签前落实，当前不执行B/C。

A账本校验和与区间并集只读核对：used.wall_s为**1030.614 s**（含210 s收尾估计上界），不是handoff §R的820.6 s加“数秒”；本批勘误该摘要及旧A Log，保留估计标签，不重计或改账。候选已耗2/3、加载3/14（全套2按闭集推定）；磁盘入账20 MB依采样/估计，不将2秒采样读数冒称已证明所有瞬时峰值。实现先零消耗核清既有峰值覆盖/保守上界与剩余量，不能复原的部分依原S-UNKNOWN停报；核清后仅用A剩余信封整理至多一个候选，所有验证/收尾共账，无新增额度或用户授权追认。

#### 预复核关注项与接力

R1须用新鲜上下文核实上述核对主张、候选2窄修替代充分性、闭集计数及完整资源峰值证明；重点复查提示f_last深复制/合成完整协方差、双截止/同帧请求、回滚与生产输入删行链、完整性与时序交叉、异常帧时间线。完整复核范围仍为handoff §5加本轮定向修复增量，不给这些关注项finding分级，不签REVIEW_BLOCKED或独立通过。四项自证需由实现者对准修后候选重整；不得在停点前启动依赖后续或未签B/C。

needs_user: none（当前定向修复不申请范围/设备/预算变化；若资源无法核清、预算不足或闭集无法满足，停报后另列具名题面）。接手动作与状态token只见状态板Active handoffs。

open_items: C1-1,C1-2,C1-3,C1-4


### C2@K1K2K3K4（2026-10-11，候选3核对与R1交接）

owner = Acceptance；Dispatch-Id `P1-ENG-FASTFIX-001-C2@K1K2K3K4-20261011T062614Z-ab24`。本派发候选从上一实现派发 `P1-ENG-FASTFIX-001-续修C1-20261011T060317Z-d73d` 的 finished.candidate 解析；代码提交与补录提交按该事件 commits 顺序辨认，后者仅补录证据/账本。完整候选范围按handoff §2/候选3节，从「A实现 候选1代码」提交的父提交至派发候选解析：41路径全部diff，区分本项实现、接受裁定/授权与夹入的VLM/调度文档，不把他角色改动归给实现。本轮修复增量另读两笔实现提交及直接关联代码；合同包含D2各裁定、A首签、IR-1…16、C1-1…4、UNKNOWN处置与续做信封。逐AC证据、旧资产继承/缺陷及全局消耗性门已核读。只读核对，未跑实现测试/模型/回放、未改实现或账本JSON。

**结论：C2不再退回，候选3及本表未决主张交新鲜上下文独立R1。** C1退回仍1/1；C1-2/3修复对准原合同，C1-1/4有剩余未决项。独立R1尚未开轮，其一次性worktree/测试的磁盘资源不足以由现有授权覆盖，等待下方具名用户题面；不是接受侧独立verdict或REVIEW_BLOCKED。AC/接口/停点、ACCEPTED/engineering-v1及旧债不变，不签UNITY_NA/DONE。以下“满足”仅为待R1核实的合同忠实性主张。

本表于 **R2通过消费（2026-10-12）** 更新为候选4现状，取代候选3的逐AC表；不是新C轮，不重置C1退回1/1。满足项依据独立R1 §2与R2 §2–6；历史C2关注项原文保留，当前处置见「R2通过消费」§2–3。AC条款未新增或改写。

| AC | 核对 | 依据与限制 |
|---|---|---|
| AC-1 | 满足 | R1 §2成立；逐行/交叉/完整性优先与旧门对照，R2未改对应代码。 |
| AC-2 | 满足 | R1 §2、R2 §2成立；恰一次HOLD/已写观测不回改/恢复；R1-1修复仍原样上抛fail-closed。 |
| AC-3 | 满足 | R1 §2、R2 §2成立；结算零diff，写失败不计不清、只有PUBLISHED清零。 |
| AC-4 | 满足 | R1 §2成立；积压/投影具名测试；N-4/N-5限制见消费§3，不称状态投影持久锁存。 |
| AC-5 | 满足 | R1 §2、R2 §1–2成立；N-1深复制/完整8×8拒绝测试已补；双截止/人工优先/回滚及重放沿R1。 |
| AC-6 | 满足 | R1 §2成立；同库KF/几何及500例行为对照；N-3读法见消费§3。 |
| AC-7 | 满足 | 候选1有限离线回放沿用：on提交3，IoU 0.926/0.943/0.815；off自动0；9不适用。R1 §2核实、R2未改路径；非候选4新回放或在线等价。 |
| AC-8 | 证据缺失 | NOT_RUN，R1/R2附议；角色TX未签0且648–650缺同源处理记录，用户自行传输不补来源。 |
| AC-9 | 满足 | R2 §0/§2–3核实R1-1两例修前红/修后绿、生产路径保留门读数；真实BoT-SORT实例包装未实测、N-8限制见消费§2–3。 |
| AC-10 | 满足 | R1 §2成立；坏参数拒启/原常量与兼容路径保持，首门值0.4s/2帧。 |
| AC-11 | 满足 | R1 §2成立；具名假遍历停令及meter故障用例，不能外推整窗外部峰值完整。 |
| AC-12 | 满足 | R1 §2、R2 §0–2成立；N-2已把window_meter纳入静态图，毒化字节/打开审计实跑，冻结路径零diff、无RED_LINE。 |
| AC-13 | 满足 | R1 §2成立；v2链式生产输入删行/连续性回归已承接；旧R1-4函数零调用，不销旧OPEN债。 |
| AC-14 | 满足 | 工程§6窄修替代经R1/R2附议；候选4具名focused 23文件及R1-1红绿，新失败0、两既有失败保持；未跑候选4全套，不记全套通过。C2-P4经R1 §0/§4及C3-1补丁落实。 |
| AC-15 | 不满足 | 已有B/C操作单草案；R1 §2/§4与R2 §2/§6不签现场项。C2-P2及操作单t0/完整计量缺口仍待B前核清；三窗例外不扩到B/C。 |
| AC-16 | 证据缺失 | C未签0、NOT_RUN，R1/R2附议；有限回放不代正式连续性。 |
| AC-17 | 证据缺失 | C未签0、NOT_RUN，R1/R2附议；无现场同口径带n分布，不以假时钟补读数。 |
| AC-18 | 证据缺失 | 用户Unity目检NOT_RUN，无UNITY_NA申请或附议；候选通过不代现场验收。 |
| AC-19 | 不满足 | R1 §2代码侧成立，现场计量/拒启不判；C2-P2/P3及旧A/续做磁盘UNKNOWN不因校验和正确或R2通过而闭合。 |
| AC-20 | 证据缺失 | B未签0、NOT_RUN，R1/R2附议；不预填冒烟建议或提前选门值。 |

#### C2预复核关注项（待R1核实，不分级）

- **C2-P1（AC-9/17，首次接受释义4）**：`gated_publisher.py::_classified_verdict`已把本帧load_elapsed存入ctx.gate_evals，后续实际底层观测/命令写失败可上抛；`track_loop.py::_capture_frame`异常支路调用`_capture_partial_timing`，后者向`capture_timing_record`恒传settle=None，使已得到的gate_eval_s变空。具名`FrameTimingTests::test_publish_exception_emits_one_row_with_tm_segment`在整个observation入口抛错，未经过真实门，不能证明同次门读数保留。须核真实门后写失败、已发生DROPPED后HOLD失败等交叉及已有完整性致命尾部；未到达m_end可null，不等于已读门数据可丢。另核实例层懒建工厂包装在实际BoT-SORT对象上可赋值且不改变调用/返回；本轮没有真实加载证据。
- **C2-P2（AC-15/19、续做§4）**：`meter.py`的目录读错、采样线程失联与输出故障处理有具名测试；但操作单依赖的新`window_meter.py::main`为单循环，`fh.write/flush`、旗标写失败可未经UNKNOWN持久化直接退出，未见独立存活/末读时间戳看门狗。操作单§4每≤30s读旗标/末行U没有明确拒绝死亡或陈旧读数，不能由旧meter的线程测试替新进程自证。执行者PID只查联盟、未与t0启动身份比；外部身份从首读才建立。读取节拍声明≠失联安全证明。
- **C2-P3（AC-15/19、续做§3–4）**：play-ops §4命令先mkdir OUT再snapshot，t0已晚于该写入；snapshot顺序读多联盟后才写时间戳，未登记各自实际取样时刻/执行者启动身份，E/R从首读才设基线。续做实际t0→06:07:57Z约5min的联盟外其他进程仅凭执行者归Claude、两次pgrep/lsof及vlm新文件0排除，缺该时间段进程/后代闭集归属凭据或完整累计上界；两次瞬时读数和mtime不覆盖间歇退出/临时建删。dd退出/延迟与mmap实证支持具名联盟字段，不证明所有外部写者。容器净占用会受其他回收抵消且基线晚于t0，R自陈只是补充，不能补该缺口。因此不接受“全项可核→完整U上界”主张；整窗上界为UNKNOWN、资源符合性未证，保留已见组件数值。另核首版单联盟运行程序与最后多联盟/snapshot代码的差异：最终假读取器绿不证明运行进程版本；实际采样06:24:37Z结束早于06:25:14Z释放登记及推送，末尾补读只有C、E/R未同读，≤0.5s贯穿收尾未证。
- **C2-P4（AC-14、四项自证2）**：归档focused日志含710例（“约720”属近似）、两既有失败及一条frozen-paths新增红。实现报告称提交后单例已绿，但handoff“见下节”没有对应命令/输出落点，归档日志亦未补该次；具名修前红/修后绿目前由handoff表记录结果，原始运行输出未入仓。R1先核可取得原输出及当前候选稳定条件；接受侧未重跑，不因自陈或supervisor F10而签相称测试已全通过。全套未跑的预算拒启理由与具名窄修替代不视为全套绿；R1按工程§6核替代覆盖，不强行越界补跑。

C1既有预复核重点仍保留：提示深复制/双截止/同帧人工优先、完整KF协方差/几何、事务回滚、生产输入删行链与完整性/时序交叉。R1范围为handoff §5加候选3节增量与本表，不仅四项修复；四条件由R1判定，不是接受侧擅开轮。没有本项独立复核结论，也不改旧债或写blocks/release行。

#### C2资源核对与R1执行边界

1. **非磁盘账可核。** 两JSON的ledger_sha256用标准库按现有canonical定义独立重算一致；后继source的旧文件字节sha/账本sha/used一致，wall_s全部区间承接，carried_entries恰为原candidates/yolo_loads/wall_s子集（不含旧磁盘条目，符合§5，原文件未改）。区间并集=5,791.114s（含旧估计及本轮420s收尾估计，不改称精确实测）；原A上限7,200s，账面余1,408.886s，仍受遗漏核清而缩减。候选3/3用尽，加载3/14账面余11；本轮0真实构造依据F12文件闭集、非全局构造插桩。
2. **续做磁盘只核已报告组件。** 后继账记录推送前1,950,843,992B，报告终读1,955,230,808B；supervisor独立C读数与报告同量级，释放登记后C=1,213,185,977B。用旧E/R拼得约1,968,993,281B仅是近似组件合计，不能当同步终读或完整上界。上述已见合计低于2.7GB不证明整窗在限；C2-P3缺口依原§4–5按UNKNOWN停报，不改账本JSON、不抹读数、不追认旧A或续做合规。旧A UNKNOWN及用户已允许的历史偏差保留；这次新的续做上界缺口不自动由旧UNKNOWN答复覆盖。
3. **R1无可执行磁盘信封。** A首签的加载/墙钟包含复核，账面余额如上；旧A磁盘UNKNOWN锁定。用户10-11新增3GB只覆盖“仅续修原C1-1…4”，本窗口已由fast supervisor登记released；不能把余盘额/同一t0转给独立R1新worktree、临时输出、focused/全套/实际加载，也不能自行重开互斥。现阶段只移交材料，不派发会创建worktree/测试写入的R1，不以资源不足伪称复核通过/REVIEW_BLOCKED；B/C/TX、Play/正式ID/API/云/下载/安装/板端仍0。
4. **待签的可复核建议。** 见下方FASTFIX-R1-RESOURCE题面，未获用户逐字授权入账并由Acceptance落实前不生效。真正启动时两路supervisor重新核mini无在途写者，登记新具名FASTFIX-MINI-MUTEX窗口ready/start与固定t0，先于派发、同步、worktree/输出创建；执行者联盟及外部写者完整归属/上界、t0身份、所有根、≤0.5s持续采样/失联拒启、实际收尾/E/R同步终读及释放写入保守覆盖均须先核。不足或UNKNOWN即停报，不能利用本建议自行补代码/测试或换基线。模型加载/墙钟全部并入原A，候选计数不追加；R1只在一次性worktree读实现，不能修代码。

#### C2 needs_user（推荐题面，尚未授权）

- **FASTFIX-CONTINUATION-UNKNOWN**：推荐保留本次续做磁盘上界UNKNOWN及执行/计量偏差、保留组件读数和代码候选，允许材料继续交独立R1但不追认资源/STOP全合同符合；理由为C2-P3首读前外部覆盖与采样收尾缺口无法由现有材料补成整窗上界。当前停止新增本机执行消耗；不删除/覆盖旧原件、不返还额度。若用户要求补原件核清，须另定可用资源，不能自动补测或估成0。
- **FASTFIX-R1-RESOURCE**：推荐单独签Mac mini独立R1的新增磁盘≤3,000,000,000B、90%停止线2,700,000,000B及新的FASTFIX-MINI-MUTEX窗口；用途限候选3独立复核一次性worktree、focused一次及每条阻断finding红绿一次、证据/同步/提交推送与计量收尾。墙钟只用A核清后剩余（当前账面≤1,408.886s），加载只用A余11且总≤14，默认focused零真实加载、必要真实加载需先登记需求与预算检查；不增加候选（3/3用尽），全套/新回放默认不跑，不能省略复核必需验证来凑通过。其他维度仍0；启前按上一小节§4核完整计量与两路互斥，不能满足则继续停报。理由为现有续修3GB授权范围不含R1，旧A磁盘UNKNOWN且窗口已释放；3GB是供用户选择的资源上界，非已实测充分保证。用户也可选择继续等待，不借旧窗口余额启跑。

接手角色/下一动作的唯一当前落点为状态板Active handoffs；本节只记录核对与边界。未改AC、不签独立verdict，不触发新研究主张或里程碑证据变更。

open_items: C2-P1,C2-P2,C2-P3,C2-P4,FASTFIX-CONTINUATION-UNKNOWN,FASTFIX-R1-RESOURCE

## UNKNOWN处置落实（2026-10-11，Acceptance）

### 1. 答复效力与本轮结论

依据账本「2026-10-11 P1-ENG-FASTFIX-001 — 用户答 FASTFIX-A-DISK-UNKNOWN 选选项 1：A 既有磁盘峰值保持 UNKNOWN 记偏差，准许在 A 剩余量内续修 C1-1…4」、同名K1K2K3K4-handoff §C1R-1…4、ledger-A.json，以及「D2 接受裁定」首次接受释义5–6、「D2预检核清」§3、「A首签落实」和上方C1退回原文。用户已选1，不重问是否保留UNKNOWN或是否愿意继续修；旧峰值保持UNKNOWN、记偏差的处置已落实。**但题面不足以执行，S-UNKNOWN继续停报，不能派发续修。** 已签答复仅准许用A剩余量，明确不追加额度，并要求起算不足时回用户；它没有给出可核的磁盘余额，也没有签发续做从新基线独立计量的磁盘边界。

本轮为授权/资源题面核清，非C2、非再次退回；C1退回1/1保持，C1-1…4未修、候选3未开、R1未开。AC/接口/代码候选和验收门不变；本轮未跑实现测试、模型或回放，未改旧账及授权原文，不签独立verdict/UNITY_NA/DONE。

### 2. 已用量、剩余量与后继账本承接

只用标准库读取JSON并按账本源码的canonical规则校验，校验和相符；对全部wall_s区间独立排序合并重算为4127.220 s，候选/加载amount合计分别2和3，与used一致。未调用账本启动或写入函数。

| 维度 | 原上限 / 当前已用 | 可承接剩余与核清结论 |
|---|---|---|
| 候选 | 3 / 2 | 1；续修仍最多整理候选3，不另开免费候选 |
| 真实加载 | 14 / 3 | 11；全套2为F12闭集推定、回放1实测，原标签保留，失败不返还 |
| 墙钟 | 7200 / 4127.220 s | 3072.780 s；验证、计量、同步与收尾共账，不因换账本返还 |
| 磁盘 | 2,000,000,000 B / UNKNOWN | **余额UNKNOWN，不能相减；原20 MB失效，不可作为起算扣项** |

认可§C1R-1将3683.457 s会话全跨度保守入账、不扣其中等待的处置口径：它覆盖所列漏记执行并避免逐段补计重复；再加本轮核清/收尾区间的并集得4127.220 s。该认可针对保守记账，不把原5 s起点估计和240 s收尾估计冒作精确实测边界；若发现边界外执行须追加、不得退款。未来续修须从首个准备/同步动作至实际收尾留完整执行区间，启动前给收尾留量，实际超过预留照记偏差停报。

后继账本可以承接**已知维度**，不能解除未知维度锁：保留ledger-A.json不动，来源指向该文件及本节，完整承接候选2、加载3与原wall_s区间（不把4127.220 s伪造成新执行区间）；后续与原区间并集计账。新账若仅复制原envelope/used，disk仍UNKNOWN，`ledger.py::problems/check_launch`仍应拒启；把disk改0或20 MB并沿用旧2 GB会伪造余额。独立续做磁盘维须有用户明示的起点、上限、历史UNKNOWN隔离方式与停止条件后才可建账；本轮不建后继账本。

### 3. 计量与同机执行缺口

§C1R-4的“每次执行前后联盟差值+声明根采样”尚未规定贯穿多个执行的累计方式、准备/收尾覆盖、联盟更换/漏成员/计数回退与读取失败处置。每步差值取max会漏掉前步仍存的新增字节；逐次重新起零也会放大可用量。联盟累计写计数不能仅因数字可读就认定覆盖全部副作用：§C1R-3同时给了byteswritten与更大的逻辑延迟写读数，具体读取器、字段单位/语义、子进程归属与未纳入写者的办法还需零模型预检记录。声明根采样仍不能单独证明建删瞬时峰值；无法建立上界的部分仍UNKNOWN。

同机问题须进入用户题面。账本VLM-DIAG:B:1允许mini转换/呈现图并有mini磁盘6 GB；当前本道status「当前状态」已记准备因缺sentencepiece停报，不把“最近涉及BF16”冒作此刻仍在写。后续若恢复，同Claude.app联盟会纳入其写入；即使隔离仓库/输出根，联盟差值仍不能扣除VLM份额。原选项已说明会偏大，但没有用户在信封中明示的同执行机互斥安排（AGENTS.md「执行轨道纪律」）。接受角色不能自行停VLM或改用另一套排除计量；目前不改本道状态或其信封。

### 4. 待用户推荐题面（未签，不由“选1继续修”补授权）

**FASTFIX-A-DISK-REBASE，推荐明确签发独立续做磁盘边界**：

“旧A磁盘峰值及是否曾越过2 GB仍UNKNOWN、记偏差，不改旧账、不声称原A总峰值合规。准许仅续修原C1-1…4：Mac mini，最多再1候选、再11真实加载，A验证及收尾墙钟累计仍≤7200 s（当前已记4127.220 s；续做≤3072.780 s，后续补账只减余额）。为这次续做单独签发从准备/同步前基线t0至实际计量/提交/推送收尾的新增磁盘上界≤2,000,000,000 B；这是对未知历史的续做例外及新增磁盘授权，**不是**可证的原A磁盘余额、不追认旧A≤2 GB。旧存量登记基线并保全，不通过删除释放/返还计量额度；其他维度与范围不追加，TX/B/C/Play/ID/API/云/训练/下载/安装/板端仍0。”

建议2 GB数值仅沿用原设计预算作为续做上界，非续做真实峰值投影。若用户坚持“旧A+续做总峰值仍必须可证≤2 GB且不另签磁盘”，当前资料无可执行路径，继续停报；不把“选1”改读成用户选了结束。

**FASTFIX-MINI-MUTEX，推荐与上题一并签发续做独占窗口**：

“由两路supervisor在启动前共同核清mini已无VLM转换/图像生成/传输写入或在途子代理；未满足不派FASTFIX。随后从t0到FASTFIX实际安全收尾及终读完成，mini的fast续修与vlm本机执行互斥，本道不启动新的mini任务；窗口结束登记释放，再按VLM原信封恢复调度，不取消或扩大VLM额度。窗口内同Claude.app其他写入全部保守计入，不事后减去别路份额；锁/窗口冲突即拒启或停止并回报。”

**随上述两题呈签的计量/承接与STOP办法**（实现细节仍交Implementation；此处约束可核结果，不声称已经具备）：

1. 准备/同步前先零模型预检并登记读取器与只读命令、Claude.app PID/启动身份、资源联盟标识、子代理及其git/Python/计量后代归属、返回状态/结构长度、原始字节字段与单位、全部具名根及外部写者。完整继承子进程（含已退出子进程）写量、逻辑延迟写及临时/缓存副作用的覆盖无法核清即S-UNKNOWN，不开始改码/测试；不安装、提权或新增设备补接口。
2. 以同一联盟/写者闭集t0的原始累计计数为固定起点；每步前后及运行中连续采样并持久记录时间戳/原值。联盟读取节拍≤0.5 s，不能只在长步骤结束后判限；声明根采样并行且不阻塞停令。直到子进程静止和实际收尾终读都不重置t0、不扣失败或删文件。每次执行差值供核对，额度以整个续做窗口累计差值判定，不逐步取max充当累计量。
3. 以已核字段/写者的累计新增写量作为保守量，逻辑延迟写不能因较大被略去；另计联盟外可归属写者的完整上界与声明根新增峰值，允许重算重叠而偏大、不在缺证明时扣减。具体字段组合、根去重/基线和覆盖证明须在启动前写入具名证据；若只得到采样下界、漏成员/根、API拒读/计数回退/联盟更换、采样或输出截断/线程失联，立即UNKNOWN停报，不换新t0继续。若无法用原选项接口建立这一上界，先报具体缺口，不能用另一方法暗自豁免。
4. 后继账本保留原A来源/UNKNOWN偏差，并按§2承接非磁盘已用；仅用户新签的续做磁盘维按t0单独记账（不赋旧A为0），启动同时检查非磁盘原总量和续做磁盘累计上界。到磁盘90%（1,800,000,000 B）立即停止续修/验证，余量只供必要计量与收尾；不得启动新步，累计达2 GB或其他上限按S-BUDGET停报，实际越界如实记偏差。每步启动先核剩余及保守收尾量；任何维UNKNOWN按S-UNKNOWN停后续，保存已得结果，不重试/追加。后继写入办法须有具名验证，不能绕过现有UNKNOWN拒启函数。

### 5. 接力与保留义务

本次交回用户的仅为§4两项未签补充，已答的旧UNKNOWN处置/继续方向保留；下一owner/status只见状态板交接。两项明示入账且接受落实、计量预检可核后，才交Implementation（Mac mini）在原闭集续修C1-1…4；修后重整四项自证及逐AC证据，照C1原文交Acceptance `C2@K1K2K3K4`，再交独立R1（C2不再退回）。不改旧核对表、不另计退回、不新增AC；AC-8及B/C现场NOT_RUN、旧OPEN债与负结果保持。

needs_user: FASTFIX-A-DISK-REBASE（推荐§4独立续做磁盘上界；UNKNOWN无法推原余额，需明示新增授权）；FASTFIX-MINI-MUTEX（推荐§4独占mini续做窗口；同联盟VLM写入不可扣除，且同执行机互斥须用户在信封明示）。

## 续做信封落实（2026-10-11，Acceptance）

### 1. 授权核定与适用次序

依据 `docs/authorizations.md`「2026-10-11 P1-ENG-FASTFIX-001 — 用户签 FASTFIX-A-DISK-REBASE（改为续做独立新增磁盘上界 ≤ 3 GB）与 FASTFIX-MINI-MUTEX（mini 续做独占窗口）」；用户原话「题1改成3GB，题二同意签署」。已对照上节§4两题全文与随题办法1–4：**两题已签，唯一修改为独立续做磁盘上界2,000,000,000 B→3,000,000,000 B，其他范围、维度、承接和停止处置实质一致，无另行扩大。** GB沿首次接受释义5按十进制；90%是相对所签上界的收尾预留比例，旧括号1,800,000,000 B是旧2 GB的派生数，故核定supervisor同比例读法成立：现行S-DISK线为**2,700,000,000 B**，硬上界为**3,000,000,000 B**。不保留旧绝对停止值作为另一条线。

本节落实已签补充，解释AC-14/15/19既有计量与拒启条款，不新增/改写AC或实现范围。上节「未签」「不能派续修」及needs_user是补充签发前快照；现由本节替代其续做入口与磁盘数字，旧A峰值UNKNOWN/偏差及旧证据原文保留。**合同已可执行为有前置的接力：先由两路supervisor核清独占窗口，再交Implementation零模型计量预检，预检全项可核才续修。** 本轮没有核定计量接口已完整可用或窗口已空闲，不放行跳过预检；不是C2，不计第二次退回，C1退回1/1保持，候选3与R1仍未开。

### 2. 续做信封逐维表

| 维度 | 已签现行边界 / 承接 | 启动核对 |
|---|---|---|
| 阶段、设备与范围 | A续做，Mac mini；仅原C1-1…4，§2.1闭集与首次接受释义不变；离线验证AC-1…15/19，AC-8 NOT_RUN，现场执行留未签B/C | 不恢复旧项、不追加修复范围；具名计量/账本验证属C1-4原义务 |
| 候选 | A累计≤3，已用2，最多再1（候选3） | 尝试即记，失败不返还；不以换后继账本或小提交另开免费候选 |
| 真实YOLO加载 | A累计≤14，已用3，最多再11 | 原全套2按F12闭集推定的标签保留；focused/全套/回放/崩溃重载/复核真实加载共账 |
| 墙钟 | A累计≤7200 s，已记4127.220 s，续做最多3072.780 s；发现旧漏记只减余额 | 原区间与后续区间取并集；续做首个准备/预检/同步至实际计量、提交、推送收尾均覆盖，重叠不重复，不把旧累计数伪造为新区间 |
| 旧A磁盘 | 峰值及是否曾越过2 GB仍UNKNOWN、记偏差 | 原账只读保全，不补0、不沿用失效20 MB、不主张旧A或旧A+续做总峰值合规 |
| 独立续做磁盘 | t0起新增保守上界≤3,000,000,000 B；达2,700,000,000 B停止续修/验证，余量仅必要收尾 | 整窗累计，不逐步起零、不删存量返额度；预检、同步、git、测试暂存、证据、客户端副作用及终读均覆盖 |
| 本机计算与验证 | CPU/MPS仅在原墙钟/加载总量内；CarrierSelfTest用CPU；每候选停点全套至多一次 | 数据根`.venv-yoloe`只复用、不装包；全套/窄修替代按工程§6，不能虚报全套通过 |
| 同机互斥 | FASTFIX-MINI-MUTEX：从t0到实际安全收尾、子进程静止、终读完成，fast续修与vlm本机执行互斥 | 启动前两路共同核清；窗口内不派新的mini任务；同Claude.app其他写入全部保守纳入，不减别路份额 |
| 零维度 | TX/B/C/Unity/Play、scenario/session/run ID=0/0/0、API、云/云GPU、训练、模型/数据下载、安装、板端及其他未列维度均0 | git同步仍只按已签A方式执行，时间/新增git字节计入；不把同步解释为数据或模型传输许可 |

3 GB是用户选定的资源上界，非实测峰值投影或模型性能门；90%只作预算收尾预留。此信封不追加非磁盘维度，不改变AC通过线或§6其他STOP；成功、失败、工程重试同账。**返工归因：本次为C1指出的既有合同不符在原闭集内修复；磁盘UNKNOWN例外与独占窗口来源仅为上述用户补充授权。**

### 3. 独占窗口、t0与登记责任

登记由两路supervisor执行，Acceptance本轮不代写窗口开始或VLM状态。共同读最新 `docs/evidence/supervisor-dispatch.jsonl` 与VLM道 `docs/evidence/COORD-VLM-DIAG-2026-10-10/status.md`「当前状态」，并核实际进程/后代及写者：不能仅凭某事件finished或表称零模型判无mini写入。本轮所读「阶段1准备修订1」为requested+started，信封明确mini BF16转换、呈现准备及传输；未见结束凭据，**当前不能认定窗口可启动**。不抢占、终止或取消该道工作；等它实际收尾并由vlm supervisor确认mini无在途子代理/转换/图像生成/传输写入。实际读数有冲突或任一路未确认即不派FASTFIX。

登记位置与形式（复用已有事件格式，不新增派发事件种类）：两路各在自身实际新追加的派发事件`note`记录同一具名窗口`FASTFIX-MINI-MUTEX`与`state=ready/start/released`、UTC时间、实际执行机、确认角色/路、关联派发ID和对方确认凭据指针；fast路在续修requested的note记录两路ready及start/t0，vlm路在其在途派发实际结束时追加的end_confirmed/finished note记录ready、在窗口释放后的下一次requested note承接released。不改已有JSONL行，不重复终结事件；若派发已核销或尚无合适事件，先在各自现行状态板登记具名一句作为可核凭据，由下一实际事件引用，不为记锁虚造派发或finished；fast路为 `docs/current-status.md` 本项交接Progress，vlm路为本道「当前状态」。双方开始/释放各一句，均指向本节与实际凭据；互斥有效期间vlm不派mini任务，fast也不派本道新的mini任务。

**t0**：两路ready后、Implementation派发及首个准备/同步之前，由fast supervisor取得同一Claude.app资源联盟及已枚举外部写者的原始累计计数，记录PID、启动身份、联盟标识、monotonic/unix；该固定快照时刻即唯一t0。第一笔持久化及派发/预检日志写入在t0之后并纳入计量，不能先同步/准备/写输出后再挑基线。原始读取可先存内存再持久化；读取失败则不派实现。Implementation首步核读数有效性与覆盖，未核前仅做零模型只读预检，不改码、不跑测试；预检自身及其客户端/日志、后继账本建立成本也计入整窗，不是免费前缀。若无法在派发前取得并贯穿该起点，按S-UNKNOWN停报具体缺口，不能换t0抹去准备写入。

窗口从t0持续到安全停止、全部可归属子进程静止、计量/提交/推送实际收尾与终读完成。Implementation将实际起止、终读、资源账及停止原因写入同名handoff具名节交fast supervisor；fast核实后在finished note登记released，更新fast交接Progress一句并通知vlm supervisor，vlm在本道状态板登记同一释放凭据后才按原信封恢复调度。不得仅因实现交了报告、进程退出或发停令即释放；锁冲突拒启/停止回报，停止时仍持锁到实际静止/终读。读取失败可在静止已核后登记`released; measurement=UNKNOWN`及缺口，不把它当计量通过或重启许可；无法核静止则保持窗口并报障。释放登记最后一次写入本身须计入可核收尾预留/上界，不能先终读后留下未核副作用；本节不取消、转用或扩大VLM信封。

### 4. 联盟计量预检与整窗上界（落实上节§4办法1–3）

Implementation在 `docs/evidence/P1-ENG-FASTFIX-001-K1K2K3K4-handoff.md` 新增「续做计量预检」具名节，记录只读命令/读取器来源、执行机/解释器、API返回状态/结构长度、原始字段/单位/语义、PID与启动身份/联盟标识、成员和git/Python/计量后代归属（含退出子进程累计）、逻辑延迟写、外部写者及根闭集。不得由“能读到byteswritten”推完整覆盖；Claude.app以外的执行者/客户端必须明确归属或另有完整上界。不安装、提权或新增设备补接口；不能确认继承/退出累计/延迟写或临时副作用即S-UNKNOWN，预检到此停报。

根清单须逐项登记绝对路径及存在/不存在读数：仓库工作树（含未跟踪）、`.git`、本项outputs/runtime/session/检测缓存、本地暂存/测试TMPDIR、证据、会话scratchpad及客户端projects/file-history/backups/plugins、Claude应用支持/日志、系统用户缓存与`/private/tmp`等实际副作用位置；这是覆盖核清清单，不授权写这些位置或全盘遍历。读不到或有未枚举可归属根即UNKNOWN；外部写者的建删瞬时峰值不能仅以前后du/mtime或根采样补成完整上界。旧存量在t0登记、保全，不移动/删除原件释放额度。

在该节明确选择的已核字段组合与去重/基线规则：以固定t0的累计增量形成非递减联盟上界`C(t)`，逻辑延迟写须纳入，若字段有重叠而无扣减证明则保守相加；再加联盟外写者的完整新增上界`E(t)`和声明根新增峰值`R(t)`，整窗判限量为`U(t)=C(t)+E(t)+R(t)`，允许重复覆盖而偏大。`R(t)`为基线后声明根新增量的已见最大值，不因删除/缩小下降；取根并集去重，无法去重允许重算偏大。联盟/外部完整累计量负责覆盖采样间瞬时，R仅补充核对；覆盖不成立则U为UNKNOWN。启动前写清具体字段公式、外部上界来源与覆盖证明，Acceptance本轮不指定未经核实的macOS字段语义，不认可只有采样下界的公式。

全窗联盟读取节拍≤0.5 s，持久记录每步前后及运行中时间戳、原值、累计增量、U和停止原因；声明根采样并行、不阻塞停令。直到静止与实际收尾终读均沿同一t0，不逐执行取max代替累计、不扣失败/删除/别路字节。终读及持久化本身的上界与保守收尾量也预先登记；长步骤启动前须核当前累计量、该步保守需求及收尾预留，避免靠采样后停止越过硬界。漏成员/根、API拒读、计数回退/联盟更换、线程失联/输出截断或覆盖丢失即UNKNOWN并停止后续，不换读法或新t0继续；不把原接口不可用转成默认豁免。计量预检全项可核且双路窗口有效，才准许在原闭集改码/验证。

### 5. 后继账本与STOP（落实上节§4办法4）

Implementation另建具名 `docs/evidence/P1-ENG-FASTFIX-001-ledger-A-continuation.json`，不覆盖旧账、既有entries或授权。后继账本的authorization引用A首签、旧UNKNOWN选1和本次两题条目及本节；记录来源文件与运行时核得校验和、旧磁盘UNKNOWN/失效20 MB/偏差与原envelope/entries只读来源，**历史未知位于具名来源元数据，不伪装成新磁盘used=0或旧A通过**。完整承接候选2、加载3的来源entries、原wall_s全部区间及估计标签，独立重算并集，不新增虚拟4127.220 s区间；新发现旧漏记追加到后继承接记录，不动旧账、不退款。

后继执行信封仍为candidates=3、yolo_loads=14、wall_s=7200；后继`disk_peak_bytes`明确只指本次t0起U(t)，上限3,000,000,000 B，与来源旧A同名维度的UNKNOWN分域。它不是把旧used改0后沿用原2 GB；新维度初值必须由实际基线和已发生预检/派发写入计算，不得漏前缀。有效启动同时核来源完整/授权匹配、承接非磁盘总量、后继整窗磁盘与计量有效性。历史UNKNOWN只依本次用户明示例外保留为历史偏差；任何新维UNKNOWN仍拒一切后续。不得删除/跳过`ledger.py::problems/check_launch`的UNKNOWN拦截、手改校验和去漂白原账或仅靠口头表格放行。

具体后继创建/承接写入办法由Implementation在既有`tools/eng_fastfix/`闭集落实，附具名验证与证据：承接数/原区间一致、重复启动不清零、失败不返还、任一新UNKNOWN/损坏/越界拒启，旧账字节不变；不强制另造schema或扩大工具范围。现有peak型磁盘记录只能接收固定t0以来的**累计U(t)**再取历史max，不能录每步差值的max替代全窗累计；上限内仍须另检查90%停止线与保守收尾预留（`check_launch`自身不证明它们）。验证及建账自身在同一预算/监控内；若既有闭集无法安全落实，停报具名缺口交Acceptance，不隐含放宽。

| 触发 | 现行处置 |
|---|---|
| 窗口未ready/冲突、同步或输入前置不符 | S-PRE拒启；在运行中发现冲突即停止回报，不继续到长步骤结束；不夺占VLM |
| U(t)≥2,700,000,000 B | S-DISK立即停止续修/验证，不启动新步；剩余仅必要计量、安全收尾、提交/推送，仍受3 GB及原墙钟总量约束 |
| 任一维启动保守需求+收尾余量不足，或U(t)≥3,000,000,000 B/非磁盘达上限 | S-BUDGET拒启或停止；耗尽仅必要安全停令/报告，不靠“收尾”继续消耗；实际越界如实记偏差 |
| 新计量/账本/覆盖UNKNOWN或损坏 | S-UNKNOWN停止一切后续消耗，保存已有读数/结果与缺口，不推余额、不换t0、不重试追加；needs_user列推荐及理由 |

§6其他适用STOP仍照原文；监控故障不能成为S-METER后无计量继续。失败/STOP不返还候选、加载、墙钟或磁盘，旧A磁盘UNKNOWN不闭合。所需用户事项不得交互提问，写入接力报告；推荐优先保持停止并呈具名最小补充题面，而非泛请“继续”。

### 6. 接力与保留义务

交回Implementation（Mac mini）：两路supervisor按§3先核窗口，再先零模型计量预检与安全承接办法核清，全部可核才在原闭集续修C1-1…4；不可核则停报具体缺口，不借两题签发追认接口覆盖。修后重整workflow§4.3.1四项自证、逐AC具名证据、完整候选diff/修复增量/未验证风险、后继资源账与窗口终读，提交推送稳定候选并停依赖后续。照C1原文交Acceptance **C2@K1K2K3K4**；C2不再退回，核对表/未决关注项随候选交新鲜上下文独立R1。本轮未改旧核对表、不计核对退回、不跑实现测试、不建/改账本JSON，不签独立verdict/UNITY_NA/DONE；AC-8及B/C现场NOT_RUN、旧OPEN债与负结果保持。窗口等待是执行前置，不是新的用户授权缺口。

needs_user: none（两题已签且合同已落实；接口/后继办法预检若不可核，Implementation按§4–5停报具名缺口）。

open_items: C1-1,C1-2,C1-3,C1-4

## R1资源落实（2026-10-11，Acceptance）

> 本节保留原合同；用户后续选简化计量后的现行计量、记录与STOP按文末「R1简化计量落实」执行。其替代范围包括§4第1–3条、§5相关要求及§2/§3依赖它们的启动/收尾条件。

### 1. 两题逐维核定与效力

依据 `docs/authorizations.md`「2026-10-11 P1-ENG-FASTFIX-001 — 用户同意 FASTFIX-CONTINUATION-UNKNOWN、签 FASTFIX-R1-RESOURCE（R1 墙钟改为 1 小时）」；已逐字对照「C2 needs_user（推荐题面，尚未授权）」两题及上方「C2资源核对与R1执行边界」。账本的上文语境明确转呈两题，提示用户可另定R1墙钟；用户原话「题1同意2同意，墙钟1小时。更新一下状态版我会重开会话」。**核定supervisor读法成立：题1按推荐同意；题2唯一改动为R1独立墙钟≤3,600 s，不与A账面余额1,408.886 s相加，也不受A累计7,200 s约束。** 从新R1窗口t0到实际收尾终读，预检/派发、验证、计量、同步、提交推送及必要收尾共账，窗口内等待也不扣除；不是仅模型推理1小时。

| 核对维度 | 原题与账本对照 / 现行效力 |
|---|---|
| 题1：历史处置 | 同意保留续做整窗磁盘上界UNKNOWN、执行/计量偏差、组件读数与候选；允许交独立R1，不追认资源/STOP全合同符合，不删除/覆盖原件、不返还额度。旧A UNKNOWN亦保持；题1不是无限续做许可。 |
| 题2：用途/设备 | 均限Mac mini、候选3的独立R1一次性worktree、focused一次与每条阻断finding红绿一次，以及证据/同步/提交推送和计量收尾；不授权修实现。 |
| 磁盘/停止线/互斥 | 均为新R1窗口新增≤3,000,000,000 B、90%停止线2,700,000,000 B、新FASTFIX-MINI-MUTEX；不能复用已released的续修窗口/t0或其余额。 |
| 墙钟 | 用户改写原「墙钟只用A核清后剩余」；「C2资源核对与R1执行边界」第4条「模型加载/墙钟全部并入原A」中的墙钟部分同时失效。仅R1墙钟分域，模型加载部分继续有效；不是把A上限改成10,800 s。 |
| 加载/候选/测试/其他 | 加载仅A余11且总≤14；候选新增0（3/3用尽）；默认focused零真实加载，必要加载先登记需求/预算；全套/新回放默认不跑；其他维度0。无冲突或额外扩大。 |

原C2推荐题面、「R1无可执行磁盘信封」和「尚未授权」保留为签发前快照，当前由本节替代其资源入口；不回改原授权或两份账本JSON。只读独立重算两账canonical校验和相符、后继source原件字节校验相符，后继墙钟区间并集5,791.114 s、候选3/3、加载3/14与C2一致；估计标签保留。后继JSON中的磁盘数值只是已见组件，**续做整窗上界按C2仍UNKNOWN**，不能用其数值推历史余额。

本轮不是C轮，不计退回；C2不再退回、首退1/1保持。不新增/改写AC、接口、实现范围或独立verdict。合同可执行为**先核启动条件、再派R1**的有界接力；本轮未证明新互斥窗口或完整计量已就绪。

### 2. R1逐维执行信封

| 维度 | 已签上限 / 起算与承接 | 执行限制 |
|---|---|---|
| 设备、对象、用途 | Mac mini；候选3，R1@K1K2K3K4；范围由同名K1K2K3K4-handoff §5及候选3节、C2表/关注项与workflow§4.4确定 | 候选由派发日志的实现finished.candidate运行时解析；完整diff和独立复核职责不缩减，不能将资源落实提交当新代码候选 |
| 新增磁盘 | 固定R1 t0起整窗保守上界≤3,000,000,000 B；U≥2,700,000,000 B停止复核执行，余量仅必要安全收尾 | 准备/派发、同步、worktree、临时探针/输出、账本/证据、客户端/缓存、提交推送、删除副本与终读全部纳入；不扣删除/失败或同联盟其他写入 |
| 独立墙钟 | ≤3,600 s；t0起连续跨度到实际安全收尾终读，含同步/提交推送及释放登记的可核收尾覆盖 | monotonic判限、unix/UTC留证；启动每步先核需求+收尾余量；沿用操作单600 s收尾预留，最迟t0+3,000 s停止启动复核验证并进入收尾，不是额外600 s额度 |
| 真实模型加载 | 承接A已用3、总≤14，R1最多11；若核出旧漏记则相应缩减 | focused默认零真实加载；每次真实构造尝试前登记理由、次数/保守墙钟与字节需求、核余额，失败/重载照计；不为补真实包装主张自行跑新回放 |
| 候选 | A已用3/3，新增0 | 不修代码、不整理候选4、不以worktree/探针另开候选 |
| 验证 | focused一次；每条阻断finding的具名修前红/修后绿一次，在上述共同总量内 | 全套/新回放默认不跑；需超出该集合或资源不足则停报，不省略必要验证凑PASS；修后绿无修复候选时不得伪填 |
| 本机计算/环境 | CPU/MPS仅在已签本机统一总量内；CarrierSelfTest为CPU；数据根现有`.venv-yoloe`只读复用 | 不安装/下载；库导入与真实构造分列；不能把零模型改称零磁盘/墙钟 |
| 互斥 | 新FASTFIX-MINI-MUTEX窗口；t0到子进程静止、实际收尾/终读及释放覆盖完成 | 两路supervisor共同ready/start；mini上的fast与vlm执行互斥，个人实验也须核实际mini写者，非派发身份不自动排除 |
| 其余 | TX/B/C/Unity/Play、scenario/session/run ID=0/0/0、API、云/云GPU、训练、新设备、模型/数据下载、安装、板端及未列维度均0 | 只复用获签git同步方式；不授权数据/模型传输、原件清理或扩大用途 |

3 GB/1小时是用户签定的资源上界，90%/600 s为收尾预算，均非模型性能通过线；不改变其他适用STOP或旧负结果、OPEN债、AC-8及现场NOT_RUN。

### 3. 启动前窗口、t0与释放登记

两路supervisor按「续做信封落实」§3沿用调度日志实际事件note+两路状态各一句的形式登记新窗口，注明`phase=R1`、UTC、执行机、确认路/角色、关联派发ID与对方凭据；旧released事件不能充当本次ready。若无合适实际事件，先在fast交接Progress/vlm本道「当前状态」登记一句，由下一实际事件引用；不修改旧JSONL、不虚造finished。必须核最新两路日志/状态和实际进程、后代/写者；vlm最后finished仅是派发事实，不能推出mini无仓库外个人实验或后台写入。

**启动顺序**：先两路ready并核§4的不改代码计量/监督办法可用；fast supervisor在内存记录`t0_monotonic/t0_unix`，时间必须先于任何R1写入（包括mkdir、snapshot输出、派发提示/日志、fetch、worktree）。执行者与外部联盟原始读数、PID启动身份和容器基线可在t0前逐项只读取得，各记实际采样起止；使用不晚于t0的基线会保守多计前缀，不得采用t0之后读数回减写量。t0前纯只读核清不建目录、不落本项输出；若客户端记录成本不能与该前缀分离，起点提前到首个准备动作并核其完整上界，核不出则不建立可启动窗口。记录先存在内存，第一笔持久化在t0后并计入；派发、建账、worktree均在此后。

`window_meter.py snapshot`先读多联盟再取时间戳，**不得**以其`t0_*`作为本次墙钟起点，亦不得照play-ops §4先mkdir后snapshot。其原值只能在逐联盟实际取样时刻不晚于固定t0、身份/覆盖已核时作为保守基线；外部与R的首读晚于t0须补完整前缀上界，否则UNKNOWN。登记start同时明确固定t0、读数原件位置与采样/监督者身份；全部可核后才派Review，不得先派发再让复核者补起点。

R1报告交fast supervisor后，计量/独立监督继续贯穿副本移除、fetch/变基、提交推送、实际子进程静止及C/E/R同批终读（各带时刻、覆盖同步读期间写入）。最后持久化、计量退出及释放登记写量/时长必须有预先登记的保守尾量并验证在余量内，终读后的未覆盖尾部仍UNKNOWN；不能只补C或提前停采样。fast核实后登记released，vlm承接同一凭据才恢复原调度。静止已核而计量失败可登记`released; measurement=UNKNOWN`并留缺口；静止不可核则保持锁、报障。释放不意味着计量合规、复核通过或可再开免费窗口。

### 4. 不改代码的完整上界或停报办法（C2-P2/P3）

**现有工具单独运行不足以放行。** `window_meter.py::main`的write/flush/旗标失败可直接退出，无独立存活/陈旧看门狗；`snapshot`不核执行者t0启动身份，E/R首读才设基线。原meter线程用例不能证明新进程失联安全。R1不得修这些代码，亦不得把本节执行性兜底写成C2-P2/P3已修或AC-15/19通过。

可接受办法为supervisor侧独立只读计量与停令监督，使用已有macOS读取接口/现有命令及宿主进程监督能力，**不改任何仓库代码/配置/测试/工具，不安装或提权**；操作编排与原始日志在已计量scratch中。启前须给出实际命令、执行者/监督者PID与启动身份、读取器版本（运行时解析）、下面三组凭据；仅列计划、声称每30 s看旗标或让R1自己看同一工具均不满足。

1. **失联安全**：独立于被监控window_meter的宿主监督持续核进程存活+启动身份、完整末行的实际采样时间戳/读取成功/输出可读、采样间隔≤0.5 s及读数新鲜度≤0.5 s；缺行/半行、时间回退、陈旧、死亡、旗标无法持久化或监督自身失联都阻止新步并对已登记的本项测试/同步子进程组发安全停令。宿主须具有独立于采样进程的期限/退出约束与停令结果凭据，不能无限等待日志，也不能只看UNKNOWN旗标是否存在。每步事先限定最长执行期、最大新增写量和停令/收尾上界；即使采样间越线，累计写量也不能因延迟停令超3 GB。不接受无人看守的长命令或以普通工具timeout替磁盘上界；监督/终止能力或其自身故障覆盖不能证明则S-UNKNOWN，不派R1。
2. **起点与外部覆盖**：用已有`MacReader`只读接口核联盟四字段（byteswritten、logical_immediate_writes、logical_deferred_writes、logical_metadata_writes，重叠不扣）、API返回/结构长度/字节单位及退出成员、延迟/映射写覆盖。固定基线均不晚于t0，执行者PID及proc_start_abstime/lstart与t0身份对照；新子进程须证明继承已登记累计联盟，退出后仍保留累计量。supervisor/Review/客户端/git/Python/计量及停令后代、所有可归属外部写者从首个准备动作纳入，不能仅凭两次pgrep/lsof或mtime判不存在。外部联盟首读晚于t0时，可用其**完整联盟终身累计四字段**保守覆盖前缀（不得只取具名PID终身量排除其余成员）；新联盟也从完整终身量计，不晚取基线起零。须能持续覆盖联盟出现/退出/身份变更；观察遗漏的短命外部写者若无可核全区间上界，立即UNKNOWN，即使U小于停止线也不得执行。数字太大导致拒启照停，不事后扣别路字节。系统服务/缓存等可归属副作用没有累计覆盖时须另给完整上界，容器净占用不能替代。
3. **整窗和收尾**：根清单沿续做§4逐项现核绝对路径，补一次性worktree、R1 scratch/TMPDIR、主树与共享`.git`、复核报告及真实宿主客户端根；不把Claude.app作为唯一执行者假设。判限仍为固定起点的非递减`U=C+E+R`，未知任一组件则U=UNKNOWN；C/E完整累计负责临时建删瞬时，R仅作容器/根新增已见峰值补充，不凭净占用抵消峰值。独立监督须校验C/E/R各自基线时刻、身份、当前原值和贯穿提交推送的原始读数，而非只读取window_meter给的U。采样/监督输出上限、每步保守需求和实际终读/尾量预留均在本次3 GB/3,600 s内；输出截断、读错/回退、漏成员、未知根或收尾覆盖丢失均S-UNKNOWN。

以上是可接受的**外部执行办法及其拒启判据**，不是宣称当前宿主已提供这些能力。本轮只读材料尚无R1独立监督/全外部覆盖凭据，因此不得立刻创建worktree或跑focused。两路supervisor核清后若不能提供上述完整上界或失联安全，不拉起Review补工具，直接停报用户；推荐保持停止，另呈「补足具名外部计量能力的独立范围/资源」题面并列设备、可用接口、额度与缺口，当前缺项仍0，不默认申请无磁盘硬限或追认新UNKNOWN。

### 5. R1账本承接、复核步骤与STOP

Review只写同名复核文件及状态板；不改两份历史账本JSON、不写P1证据账本，不改实现工具。可在已计量R1临时目录使用现有`tools/eng_fastfix/ledger.py`的`create/read/record/check_launch/check_disk_window`（仅调用已有接口，不写新实现），在 `docs/reviews/P1-ENG-FASTFIX-001.md` 具名「R1资源账」节保全临时账本的完整JSON内容、运行时校验和、来源校验与原始计量日志指针。supervisor独立监控在仓库外计量scratch留原始日志，R1收工后按既有调度事件note/报告留最终尾量与释放凭据，不在复核运行期间代写状态板或P1账本。若现有接口或持久化不能满足本段则停报，不能手改校验和或扩大角色写权。

承接方式：先只读校验ledger-A.json及ledger-A-continuation.json原件/canonical/source关系，复核记录保全原envelope/used/entries/全部wall区间、估计标签、旧A及续做磁盘UNKNOWN裁定指针；由源码接口新建**R1分域**临时账，`envelope={candidates:3,yolo_loads:14,wall_s:3600,disk_peak_bytes:3000000000}`，authorization只引用已签账本条目与本节。用`record`将来源候选3与加载3作为具名历史承接各记一次（不是新增R1尝试），核完整来源entries合计；初始化未完成前严禁启动。磁盘首条记实际固定t0以来的累计U，墙钟首条记[t0,建账实际时刻]，不得填免费0前缀。**不调用create_continuation**：它会继承A的7200 s上限/旧区间，不能表达本次独立3600 s。历史A区间仅在来源记录保全、不进入R1 active wall_s，不把5791.114 s造为新执行区间或提高本次上限；加载全项共账与候选耗尽仍分别拦截。任何旧漏记加载追加历史承接，不退款。

每步先`read`校验全维/来源/授权与原件未变，核当前C/E/R、独立监督和窗口有效，再`check_launch`核需求、`check_disk_window`核整窗U+该步保守需求+必要尾量；并额外检查独立墙钟实际跨度+本步/收尾需求≤3600 s。新账的UNKNOWN/损坏仍拒启；历史UNKNOWN只在来源保全，例外来源是题1与本次新信封，不把历史重标KNOWN。磁盘条目记录固定t0累计U的历史max；wall条目是[t0,当前实际终点]并集（不断补长、不逐步骤起零）。成功/失败、真实加载尝试、同步/收尾均即时共账；超界如实记录并停止，不删entries或另建账重启。

给复核者的顺序（supervisor固定提示只引用本节名及已提交入口，不改写范围）：

1. 启动前由两路supervisor完成§3–4，ready/start/t0与独立监督凭据齐全后才派发新鲜Review；Review先核预算初始化与监控有效性，核候选绑定、完整diff和workflow§4.3.1四项自证/C2-P4原输出；稳定条件不成立按既有规则写REVIEW_BLOCKED，不以本节预定开轮。
2. 只在一次性候选worktree读实现、跑一次相称focused并记录测试树哈希；原始输出持久化，结果只作复核证据。核全量范围与C2-P1…4、具名生产失败路径、完整性/安全红线；默认零真实加载。必要加载先登记与检查，超测试闭集/额度或需全套/新回放则停报，不能静默少测。
3. finding只写同名复核文件，不能修任何controller/Assets/tools/tests/config，也不因计量外部兜底签AC-15/19已修。已有修复候选的阻断finding才按workflow§4.4做具名红绿；发现待修缺陷直接交实现，不在R1制造修复候选。机读round_candidate/passed_candidate、blocks/releases及新轮资格照旧，不能以资源落实代签verdict。
4. 清除一次性副本、核安全静止，更新复核文件/状态、两项角色自检后提交推送；所有动作继续监控计账，留实际终读与尾量交fast supervisor核释放。临时账/原始日志原件保全；复核文件内账截至具名时刻，随后提交推送/尾部用supervisor实际终读凭据承接，不以事前估计冒作终读。

| 触发 | STOP与缺省处置 |
|---|---|
| 双路未ready/start、身份/输入前置不符或锁冲突 | S-PRE拒启；运行中冲突停止本项执行、持锁至静止/终读；不抢占/终止别路 |
| U≥2,700,000,000 B，或预计本步+必要收尾将达到停止线 | S-DISK停止/拒新复核步，余量仅必要收尾，仍≤3 GB/3600 s |
| 墙钟到3000 s收尾线、保守需求+尾量不足、加载/候选耗尽或任一硬上限触及 | S-BUDGET拒新步/安全停止；3600 s为实际收尾硬界，超界照记偏差；耗尽只做必要安全停令/报告，不能强行提交或重跑 |
| 新计量/外部覆盖/监督/账本/尾量UNKNOWN，读错/输出截断或损坏 | S-UNKNOWN立即停全部后续消耗；保全已有材料与缺口，不估0/推余额、不换t0、不免费重开或修工具；needs_user逐条列推荐与理由 |

当前needs_user: none（题1/2已签，资源读法无未决；双路窗口/独立计量仍为启动前必须核清的前置，失败按§4停报用户）。交接owner/status/下一动作只见状态板；本轮未跑测试/模型/回放，未建R1账或窗口、不签独立复核/UNITY_NA/DONE。

open_items: C2-P1,C2-P2,C2-P3,C2-P4

## R1简化计量落实（2026-10-11，Acceptance）

### 1. 授权核定与替代范围

逐字核对账本「2026-10-11 P1-ENG-FASTFIX-001 — 用户选 R1 简化计量（替代提案「R1资源落实」§4 独立监督/全外部覆盖要求）」的上文语境、用户原话与效力。**supervisor读法成立**：用户选的是该摘要选项1，准许本项R1用磁盘剩余空间起止读数与一次性目录实测大小，取消独立监督/失联停令、全外部联盟覆盖与由该覆盖不确定引起的S-UNKNOWN；墙钟仍1小时。效力中的“及一次性目录实测大小”落实为另一个可见占用读数，**不与数据卷下降量相加**（二者可能重叠）；任一读数达到停止线即停止新复核执行。不是累计写字节或完整峰值证明。

本节替代「R1资源落实」§4第1–3条及其末段拒启办法、§5的独立监督/完整U/逐步check_disk_window和JSON建账要求；§2磁盘U口径、§3联盟基线/身份覆盖/独立监督/完整尾量证明等依赖要求同步由本节替代。R1不必运行window_meter或补监督工具，不要求≤0.5s采样、全联盟追踪、逐步骤保守写量证明。原文保留为被替代合同，不再用这些缺口拒启R1。

仅R1计量例外：新增磁盘≤3,000,000,000 B、停止线2,700,000,000 B、独立墙钟≤3,600 s（含同步/提交推送/收尾）、加载仅A余11且总≤14、候选新增0、focused一次及每条阻断finding红绿一次、全套/新回放默认不跑、新双路FASTFIX-MINI-MUTEX及其他维度0仍有效。AC表与实现验收不改；C2-P1…4待R1核实，不因取消外部监督要求而签C2-P2/P3已修或AC-15/19通过；旧A/续做UNKNOWN、偏差、原件及OPEN债保持。

### 2. 谁读、何时读、原件放哪里

fast supervisor负责窗口起止与墙钟，Review负责一次性worktree/临时目录大小；使用现有只读命令，不安装、不提权、不写新工具。起止的`df -k /System/Volumes/Data`取Available列×1024为可用字节F，每次已有读数的下降量D=max(0,F0−F)；目录用`du -sk <绝对路径>`首列×1024为占用字节。记录原始输出、实际读取UTC、命令及单位，不用`df -h`四舍五入值判线。

| 时点 | 责任与最小动作 |
|---|---|
| 启动前 | 两路supervisor核最新调度/实际mini任务，登记新窗口ready。fast在首个R1执行写入（派发、mkdir、fetch、worktree）前先取t0的monotonic/UTC，再只读取得F0，先存内存；随后登记start和起点读数才派Review。时间起点不晚于F0读数开始，准备/等待均共账。不能复用旧窗口或旧t0。 |
| 目录建好后 | Review记录一次性worktree和R1临时目录的绝对路径，用du各读一次实测大小；临时目录须是本轮新建，日志/TMPDIR放该目录。两目录不嵌套，若嵌套只计外层，避免重复相加；不覆盖已有目录/原件。 |
| 删除worktree前 | Review再读两目录大小，保留这两次读数中较大的合计S；目录测量包含测试输出/临时探针，删除不能抹掉已见读数。无须逐步骤check_disk_window；在自然步骤返回时可补df/du，已见超线照停。 |
| 实际收尾 | Review移除一次性worktree、保存报告/状态并自检、提交推送，将实际动作/加载次数及原始日志落点交fast。fast核本项子进程静止后读取F1及t1的monotonic/UTC，含上述收尾；计算墙钟t1−t0与D=max(0,F0−F1)，登记released及终读摘要，vlm承接该凭据后恢复。终读后的释放登记另带实际UTC，墙钟收尾取终读/释放较晚时刻；若该登记超过3600s如实记偏差，不藏尾部。 |

原始df/du/时间读数与测试输出保存在上述R1临时目录，收工保留该目录，不删除计量原件；其创建/写入也属于本次额度。supervisor起点原值在t0后写入该目录，并在实际调度事件note引用绝对路径及起点/终读摘要（无合适事件时沿用原§3状态一句登记再由下一实际事件引用，不虚造finished、不改旧JSONL）。Review在同名复核文件「R1资源记录」节写读数摘要与原件路径；最终F1/t1由supervisor调度note承接，不要求Review在提交前预填未来终读或提交后再循环改报告。

这套读数只反映已观察的卷净下降与目录占用；瞬时建删、系统回收抵消及客户端/外部写入归属不可得均记UNKNOWN，**不据此停止R1，也不称完整磁盘峰值或全合同资源符合**。已知别路在mini执行仍是互斥冲突，不能用“外部UNKNOWN不停”绕过窗口。

### 3. 最小资源记录替代R1 JSON账本

**不需要新建R1 JSON账本，不调用create/create_continuation、record或check_disk_window。** 替代记录就是同名复核文件「R1资源记录」加supervisor最终调度note；两份历史JSON只读校验/引用、不改已有条目。Review记录授权条目、本节指针、来源校验结果（运行时解析）、承接候选3/3与加载3/14、R1真实加载尝试数（默认0，成功/失败都计且不退款）、实际验证命令/起止/结果、F0/已得F/S/t0、STOP或未验证项及原件落点；supervisor补F1/t1/D与释放凭据。记录是短表或几行文字，不要求复制历史entries/墙钟区间或canonical校验和系统。

必要真实加载前Review核A来源与当前已用量，登记理由和次数，总量不得超过14；核出旧漏记即缩减可用11。R1墙钟单独从本次t0连续计，不并入旧A区间、不换t0、不另建记录重启额度。候选耗尽不阻止只读复核，但禁止修代码/新候选。外部写量UNKNOWN仅作限制栏，不令此最小记录失效；必要读数或加载承接本身缺失/损坏仍按下表停报。

### 4. 判停、复核与接力

| 触发 | 最小处置 |
|---|---|
| 两路未ready/start、F0/t0缺失、已知窗口冲突或输入不符 | S-PRE拒启；运行中冲突停止本项，持锁至静止，不抢占别路。 |
| 已见D或S≥2,700,000,000 B（含收尾读数） | S-DISK停止新复核/测试，余量仅必要安全收尾；不得删除原件、扣掉外部写量、换基线后继续。超过3 GB如实记偏差并回报，未到线也不证明完整峰值在限。 |
| t0后3000 s或余时不足以完成验证和收尾；加载余额不足/其他硬限触及 | S-BUDGET拒新验证并安全收尾；fast supervisor按3000 s转收尾、3600 s硬界管理宿主任务，启动长命令须留足收尾时间。600 s沿用原预留，不是新增额度；无法完成即报告部分结果，不能省验证凑PASS或强行提交。 |
| 必要df/du/墙钟读数失败、输入/来源或最小资源记录损坏 | S-UNKNOWN停止后续执行、保全材料并报具体缺口；不能估0。外部归属/瞬时峰值UNKNOWN不属此停报触发。 |

判停依赖上述少量读数和宿主墙钟管理，**不要求另设独立监督/实时磁盘看门狗**；两次卷读数不能发现期间所有峰值，这是本次用户选择的限制。原§5复核顺序2–3及workflow/engineering规则继续有效：Review在Mac mini新鲜上下文、自建一次性候选worktree，先核四项稳定条件/C2-P4原输出与完整diff，再做相称focused；稳定条件不成立仍REVIEW_BLOCKED不开轮。发现缺陷只写同名复核文件，红绿/机读行/边界/归因照旧，不能补工具或修实现。收尾按本节§2–3，不再要求原§5步骤1/4的独立监督和完整U账。

结论：本轮可执行合同已落实，交Review（R1@K1K2K3K4，Mac mini）；启动前两路supervisor仍须登记新FASTFIX-MINI-MUTEX窗口ready/start与起点读数。窗口就绪是前置，不是未签授权。本轮不是核对轮、不计退回、未跑测试/模型/回放、未建R1账或窗口，不签独立verdict/UNITY_NA/DONE。

needs_user: none

open_items: C2-P1,C2-P2,C2-P3,C2-P4

## 返工资源落实（2026-10-12，Acceptance）

### 1. 授权效力与窄修范围

逐字核对账本「2026-10-12 P1-ENG-FASTFIX-001 — 用户签 R1-1 窄修返工资源（第 4 个候选 + 实现/R2 两个简化计量窗口）」的上文选项1、原话「窄修返工」与效力：**按选项1签发的supervisor读法成立，无额度或范围扩大**。仅本次候选上限+1至总4，不重置旧3次；实现/R2各一独立窗口，不合并、借用旧余额或免费重开。新窗口可由用户当场确认代vlm侧ready，但账本10-11代确认仅限旧R1，不能沿用；未取得新凭据则由两路supervisor重新核清登记。

候选4必修仅R1-1：`controller/track_loop.py::_capture_partial_timing`保留本帧已读门读数；绑定同名复核R1 §3的生产路径回归 `tests/test_capture_session.py::FrameTimingTests::test_write_failure_after_real_gate_keeps_gate_eval`（可改名，证据列实际名）。真实分级门通过后令inner观测或云台写出器抛OSError，核恰一条frame_timing、gate_eval_s与本帧门读数同值、publish_failed原因及已到达段；不改settle_frame结算或fail-closed上抛。可选仅N-1深复制/完整协方差拒绝测试、N-2静态隔离集合补测及C3-1逐字文档补丁（同名复核R1 §3）；其余代码/配置/工具、接口和AC不改，不处理N-3…7新范围。归因：R1-1依据BC-9（AC-9）→实现错误，按用户一次性候选例外返工；不是验收放宽或复判。

### 2. 两窗口逐维合同与计量差异

| 维度 | 实现窗口 | R2窗口 |
|---|---|---|
| 设备/用途 | Mac mini；上述窄修、focused/红绿、证据/同步/提交推送及收尾 | Mac mini；候选4独立R2@K1K2K3K4、一次性worktree、focused一次/R1-1红绿一次、报告/同步/提交推送及收尾 |
| 候选 | 新增至多1，总≤4，尝试即记、失败不返还；本批提交共同绑定一个候选 | 新增0，不修代码或整理新候选 |
| 新增磁盘 | 独立t0起≤3,000,000,000 B；已见D或S≥2,700,000,000 B停 | 独立t0起≤3,000,000,000 B；同停止线 |
| 连续墙钟 | 独立≤3,600 s，t0+3,000 s转收尾，含准备/等待/提交推送/实际终读与释放 | 独立≤3,600 s，同起算与收尾线 |
| 真实模型加载 | 0，不动用A余11，已记3/14不变 | 0，同左 |
| 互斥/其余 | 各开一次新FASTFIX-MINI-MUTEX；TX/B/C/Unity/Play、scenario/session/run ID、API、云/GPU·h、训练、下载/安装、新设备、数据/模型传输及板端均0 | 同左，不能复用实现窗口；仅已签git同步方式 |

两窗口直接沿用「R1简化计量落实」§2–4的读数、单位、判停、最小记录与释放办法（D/S不相加；外部归属/瞬时峰值UNKNOWN不停，但必要读数失败或已知互斥冲突仍停；不证明完整峰值），**只作以下角色/记录差异**：

- 实现窗口由Implementation读本轮新建临时/输出目录du，S取建好/收尾前两次合计较大值，不重复计嵌套目录；主树不是新建复核副本，不把其存量当新增，主树/git写入由卷D观察。R2仍由Review读一次性worktree与新临时目录。
- fast supervisor分别取各窗t0/F0，t0后写入各自新临时目录；两路登记ready/start、起点读数及原件绝对路径后才派执行者。实现虽以当前Claude Code进程下的Opus子代理运行，不能沿用宿主旧起点；t0先于本窗准备/派发写入。两窗各到子进程静止、终读与released才解锁；原始日志保留。
- 实现最小资源记录写 `docs/evidence/P1-ENG-FASTFIX-001-K1K2K3K4-handoff.md`「R1-1窄修候选4自证」；R2写同名复核「R2资源记录」。各列授权/来源校验、候选本窗尝试数、真实加载0、命令/结果、t0/F0/已有F/S/STOP/原件指针；最终F1/t1/D与released由supervisor实际调度note承接。不新建JSON账本、不改两份旧JSON条目；新候选计次在上述记录承接3→4。

### 3. 实现停点自证与R2边界

候选4在同名handoff具名自证节按workflow §4.3.1四项逐条写短证据：①窄修文件清单/接口冻结及相对R1候选的diff；②覆盖改动文件的零真实加载focused、R1-1生产路径具名修前红/修后绿原始输出，分列基线已有/新增失败；③已知失败仅本次R1-1须先修绿，Unity/现场未执行保留NOT_RUN、无UNITY_NA；④证据、状态、实际候选提交与未验证风险已更新。按AC-9/12/14及实际补测AC列test:/artifact:/cmd:指针；候选标识运行时解析，不手抄SHA。本批相对上个停点全套候选的累积改动仍须符合工程§6窄修替代前提，列具名文件且不触及真实模型加载器、数据划分/对外指标路径；全套/新回放默认不跑，不记全套通过。替代不足或所需验证超授权即停报，不能省验证凑通过。

修绿、自证齐全后提交推送，直接交Review `R2@K1K2K3K4`，不经C轮；R1-1修复触及PLAY_GOVERNING，开轮资格按workflow §4.4核。R2重读R1与完整候选：修复触及行基线从R1 §0 round_candidate解析，全量diff按上一通过候选解析（当前无通过轮，沿R1 §0首轮基线）。全量diff仍必核范围/红绿，但本轮新阻断限修复触及行CLASS_1/2、旧finding闭合失败、RED_LINE及未改动行上轮漏检CLASS_1；未改动行漏检CLASS_2只阻断下个消耗性门，blocks/releases配对照旧。focused一次记测试树哈希，R1-1修前红/修后绿一次由Review在一次性副本核实；不得改实现。稳定条件不足仍REVIEW_BLOCKED不开轮，若R2再REWORK_REQUIRED即达到2/2，按规则冻结未闭集交接受裁定。

旧A/续做磁盘UNKNOWN、偏差、OPEN债与AC-8/现场NOT_RUN保持；不追认AC-15/19现场通过。本轮只落实资源，非核对轮、不计退回、不消费通过verdict、不签DONE；两新窗口尚未登记/动用，启动前置仍须核齐。

needs_user: none

open_items: R1-1


## R2通过消费（2026-10-12，Acceptance）

### 1. 通过轮绑定与阶段A代码收口

owner = Acceptance；requested.round = `R2通过消费`；Dispatch-Id `P1-ENG-FASTFIX-001-R2通过消费-20261012T022633Z-a104`。完整核读同名复核R1 §2–6与R2 §0–6、合同与自证「R1-1窄修候选4自证」；通过候选只从R2 §6 `passed_candidate`运行时解析，核其与R2 §0 `round_candidate`一致、为当前HEAD祖先，候选至本轮开工的controller/tools/tests/config/Assets/ProjectSettings/Packages无diff。复核提交是复核报告载体，不能拿它替代实现候选。修复增量从R1 §0机读行解析，仅track_loop与三测试文件，与自证及R2声明一致。

**消费R2@K1K2K3K4的独立 `REVIEW_PASSED`，Overall改为 `REVIEW_PASSED`，Lifecycle保持 `ACTIVE`，交用户决定后续。** 阶段A代码停点收口；本工作项完整验收仍未通过，不签DONE/UNITY_PASSED/UNITY_NA/CLOSED_*。本轮不是新的C/R，不运行实现测试/模型/回放，不改代码/配置/工具/测试、复核文件或历史JSON账本，不新增/改写AC。AC表仅补证据/日期，固定核对表为候选4最新读法；旧C2未决文字以本节处置为当前入口。

### 2. 证据、归因与未闭义务

- R1-1依据 `BC-9`（AC-9）→ **实现错误1**，R2在副本核实两例生产路径修前红/修后绿后闭合；N-1/N-2已补覆盖、C3-1逐字补丁已应用。无新CLASS_1/2、RED_LINE或blocks；不需要也不伪造release。C/R计数=2/2，C退回1、R返工1；候选4/4用尽，不重置计数。非阻断备注无依据列，不编造BC缺失或上游漏检归因。
- C2-P1的门读数缺口已按R1-1闭合；真实BoT-SORT对象update包装可赋值性仍未真实构造验证，不能从替身focused推出已实测。结算后异常的settle_outcome记录未新增具名测试；N-8另见§3。C2-P4由R1干净副本205 OK原始输出核实，C3-1已补正确指针，候选4亦205 OK。
- AC-7仅沿用候选1的有限离线读数：适用3次/全部12注入，on提交3且IoU均≥0.5，off提交0，9次not_applicable；不称候选4新实跑、在线门等价、误重捕率或板端能力。AC-14窄修替代经复核附议，focused新增失败0，两项既有失败保留；不称全套全绿。
- **AC-8保持NOT_RUN**：角色TX未签0，固定584–783片段仍缺648–650的同一原会话处理记录；自行传输不补来源，不删帧/缩换片段/补写记录，不为本项重采集。TX当前不可呈签；不签TX不阻断其余A或B前置准备。
- **B/C全部未签0**；AC-16/17/18/20 NOT_RUN，用户目检未完成且无UNITY_NA。AC-15操作单草案与AC-19代码侧成立不代表现场项通过。C2-P2的window_meter失联/输出故障及操作单t0先写目录、外部首读/整窗覆盖等缺口保持；仅R1/窄修/R2的简化计量例外不能转用于B/C。B须先核最终操作单、Air现场环境/活路径/保全闭集、计量与停令办法，再呈阶段信封及STOP；需要改工具/第五候选或新执行消耗先回用户签范围/额度，再走适用停点。C另须B报告、门值核定/必要返工消费、B产物归档闭集与C现场前置。
- 旧A及续做磁盘整窗上界UNKNOWN、执行/计量偏差原样保留，不改两JSON、不补0、不推历史磁盘余额、不追认全合同符合。真实加载累计仍3/14（全套2按F12闭集推定标签保持）；账面余量不授权新候选/回放。三个新增窗口已released，不借余额再开。完整瞬时峰值与外部归属UNKNOWN即使已见读数低于线也不变。
- **旧OPEN债保持**：CAPTURE R1-4/R2-2仍在implementation-status唯一账本；本项AC-13承接v2回归不追认旧v1任意删行检测、旧启动门零函数调用不销R1-4。LOOP-002 R1-5、ACQ K1K3-R1-1、FRAME R1-3等未触及债不销；CAPTURE FAILED_INCOMPLETE/来源缺项与既有暂停/研究门不变。

### 3. N-3…N-8非阻断备注的读法

本节消费复核备注，不复判分级、不补造finding或新增验收义务；原AC文字不覆盖或放宽，后续超出既有可达域的主张须另立合同。

| 备注 | 接受侧读法与限制 |
|---|---|
| N-3 | AC-6冻结的是对库prior的行为，不是函数体排版；共享_motion_size_core由R1的500例逐值基线对照及同库KF证明承接，不能冒称函数体零diff。 |
| N-4 | loop的published_observation=True是调用记录，不能作为WRITTEN成功计数；是否实际写出只读收据/桥文件与结算。它不改AC-2已写观测不回改，不据该布尔推发布成功或现场连续性。 |
| N-5 | R1已记投影按最新帧、本tick可回落且无害的备注；本轮只携带这一行为，不声称publish_degraded锁存到下一PUBLISHED，也不据此改streak清零或授权。AC-4的降级/下一发布恢复具名测试成立与零新帧/NO_ATTEMPT持久显示是两回事；现场报告仍待AC-18，不把此备注当用户已附议现场可见性或覆盖原§3.2措辞。 |
| N-6 | boxes_rows/library_boxes为同源框行转换辅助，按§2.4帧/缓存复用意图作现有纯转换读法；模块连带导入旧ledger但零函数调用，R1-4不触发。未来实际调用旧账本函数仍按原合同触发，不能用这条读法扩大用途或销债。 |
| N-7 | 提示键在tracked+lost缺席时预测器不可得→逐帧无证据→双截止到期失败，保持fail-closed，不引shared_kalman回退。非时序且无绑定不生成提示，原合同无必须生成该跳过事件的独立要求；无日志不推该路径已实测或发生重捕。 |
| N-8 | R2指出settle_frame首行清ctx后若内部抛错可能丢门读数，但当前纯内存运算无仓库内可达触发状态；按不分级备注携带，不声称所有任意注入异常都保留读数。未来扩大故障输入域须承接具名生产路径与相称验证，本次R1-1闭合不泛化到该域。 |

### 4. 三窗口资源事实核清

只读对照复核R1/R2 §5、自证末节及supervisor-dispatch对应finished.note：

| 窗口 | 实际墙钟（s，非取整摘要） | 已见D最大（B） | 已见S最大（B） | 真实加载 / 新候选 | released UTC |
|---|---|---|---|---|---|
| R1 | 903.28 | 341,381,120 | 82,165,760 | 0 / 0 | 2026-10-11T22:03:07Z |
| R1-1窄修实现 | 462.90 | 3,461,120 | 40,960 | 0 / 1（总4/4） | 2026-10-12T01:11:04Z |
| R2 | 826.38 | 94,281,728 | 82,329,600 | 0 / 0 | 2026-10-12T02:25:46Z |

三窗分域，不把墙钟相加对一窗上限或并入旧A；D/S不相加。已见量均低于各自2.7GB停止线、墙钟低于3600s，未记录STOP；这是用户选择的简化读数口径，不是完整峰值或所有资源/STOP符合性证明。R2复核§5的89,501,696B是当时已见最大，调度实际终读增至94,281,728B，按finished.note承接不改复核原文。实现窗非本窗PID 69550远程ssh/pip进程的本机外部写入归属UNKNOWN、终读前已结束，按合同不停；不将其记为本项安装授权或0外部写量。原始df/du/测试日志只沿复核、自证和finished.note绝对路径读取，原件保全。本次接受消费新增信封耗用为0。

### 5. needs_user（现行推荐题面，未授权）

- **FASTFIX-NEXT**：推荐选择“阶段A代码收口，继续准备B前置，暂不签B/C；先由supervisor在Air作零模型/零Play/零传输、无清槽迁移的只读事实核清，再交Acceptance核最终操作单、计量缺口和完整B题面”。理由：代码停点已通过消费，但AC-15/19未签，现有操作单不能直接执行；当前候选4/4及窗口已用完，若核清后需要改工具/新候选或新增消耗，必须另呈具体范围和资源，不能直接派实现或沿用R2简化计量。另一选择为暂停或终止本项；须用户明确选择后再按COORD-013移行，保留全部未闭义务，不把停止称验收通过。当前保持ACTIVE，仅等待该方向决定。

TX保持未签/AC-8 NOT_RUN，C待B及其他前置齐全才呈签；这两项由既有合同缺省直接保留，不要求用户重答传输方向、Play次数或门值。

接手owner/status唯一当前落点在状态板Active handoffs；以上是用户决策准备，不替用户作答或代写授权。

open_items: FASTFIX-NEXT
