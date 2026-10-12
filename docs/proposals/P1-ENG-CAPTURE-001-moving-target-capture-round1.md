# P1-ENG-CAPTURE-001 — 第一轮：VLM 旁路下的移动目标捕获（点击入口、目标管理器、只移中心的位姿补偿、丢失后收养）

Status: ACCEPTED
Revision: D2
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（工程轨道 Opus 池，supervisor 派发子代理，Mac mini；D1 Dispatch-Id `P1-ENG-CAPTURE-001-D1-20261009T221610Z-e026`，D2 Dispatch-Id `P1-ENG-CAPTURE-001-D2-20261009T223928Z-5adc`）
Created: 2026-10-09
Last updated: 2026-10-10

> **来历**：用户 2026-10-09 同意开本工作项（账本同日「P1-ENG-CAPTURE-001 — 用户同意开新工作项…」）；范围来源 = 重新构思草案 §5「第一轮」（`docs/evidence/COORD-RECHARTER-2026-10-09/recharter-draft-2026-10-08.md`）；快层方向 = 账本同日「COORD-RECHARTER-2026-10-09 — 用户方向：快层修正方向＝补偿只移中心、宽高不变，第一轮一并做丢失后收养」；设计基线 = 同目录骨架 v3 + v3.1 修订清单（冲突以 v3.1 为准）。D1 首退见文末「D1 接受裁定」；用户对其上交四项的答复见账本同日「P1-ENG-CAPTURE-001 — 用户答 D1 接受裁定上交的四项…」（下称 **USER-4A**）。
> **本提案只是申请**：`Workflow: engineering-v1` 是否生效由接受角色裁定；§5 额度只起草、未签即 0；不改代码、配置、测试、工具。D2 逐条回应见 §10。

## 0. 只读事实（D1+D2，Mac mini，零消耗；符号名为准，行号以开工 HEAD 重定位）

| # | 事实 | 出处 |
|---|---|---|
| F1 | 常驻关联器缺省 `gmc_source="pose"`；补偿把预测框四角经单应映射后取外接框（AABB）定中心与宽高，中心雅可比转速度与位置/速度协方差块；H 为 None 时不补偿 | `controller/det_assoc_tracker.py::apply_pose_warp`、`make_resident_associator`、`DetAssocTracker.__init__`；`controller/pose_gmc.py::warp_box_xyxy` |
| F2 | 10-08 现场即 F1 路径；红车在 559–562 帧图像每帧滚转 18–24°，AABB 预测框膨胀，561 起 LOST、592 删除 | 回放设计 §1.1–1.2（诊断，只作设计依据） |
| F3 | 检测 `model.predict(conf=0.25, iou=0.7)` 按类别 NMS，类别闭集 {0 vehicle, 1 target}；输出 `Boxes` 原样进 `tracker.update` | `det_assoc_tracker.py::_detect`/`_step`；`config/det-assoc-v1.models.json` |
| F4 | `designate()` 在 BOUND/BOUND_COASTING 时调 `follow(j)` 并写 coasting，第二级收养也 `follow`；`select_track` 是纯函数；`follow` 换指针时清 coasting | `controller/resident_core.py::designate`/`_level2`/`follow` |
| F5 | `.follow(` 调用点：`resident_core.py` designate/_level2、`language_loop.py::_new_pointer_epoch`、`det_assoc_tracker.py::follow`（转发）、`tools/eng_acq/e1.py`（离线线束）；`.designate(` 调用点：`language_loop.py::_designate_resident`、`e1.py` | grep |
| F6 | 历史每帧存位姿、内参、时间、tracked 行与 lost 池预测行、removed_ids；**不存**原始检测、未确认轨迹、KF 均值/协方差、补偿矩阵；退化或出画的 lost 框被丢弃，指针因此被判 REMOVED | `resident_core.py::record`、`rows_from_library`/`_norm_box` |
| F7 | 指针丢失现行处理：lost 池 → `bound_track_unmatched`，不发观测、不发 look_at、机身 hold；库删 ID（30 帧）后才 `_raise_suspect("tracker_failure")` | `language_loop.py::_advance_resident`；`track_loop.py::_publish_resident` |
| F8 | look_at 点 = 框底中点射线 ∩ 地面平面，经 `servo_clamp` 限相邻视线角 ≤ 30°/s ÷ hz；机身估计器取同一观测 | `track_loop.py::_publish_resident`、`servo_clamp` |
| F9 | 会话动作闭集 `ACTIONS`、`STATE_REASONS` 追加不重排；会话启动强制读 K 收据并据其建适配器；`JOURNAL_KINDS` 闭集 | `controller/language_bridge.py`；`language_loop.py::_run_session`、`JOURNAL_KINDS` |
| F10 | 现有本机操作网页 W1–W5（127.0.0.1、`Submitter` 单在途提交与 seal、`OpsLog`、CLI 子进程执行动作）；无图像点击入口 | `tools/eng_loop2/operator_web.py` 文首 docstring |
| F11 | 场景：目标 2.0 m/s 绕 213 m 回环；无人机初始高度 25 m、v_max 4 m/s；机身带 `d_star` 12 m、`band_w` 4 m；`target_height_m` 1.55 | `config/scenario.untethered.json`、`config/p1-eng-frame-001-body.json` |
| F12 | 全套真实 YOLO 构造只读清单：`tests/test_det_assoc_carrier.py` 120、173（`CarrierSelfTest`，`_ready()` 不满足即 skip）；其余 `DetAssocTracker(` 构造（同文件 380；`tests/test_det_assoc_tracker.py` 162/211/399/621）均注入 `model_loader` 替身；`YOLO(`/`_default_model_loader` 无其他真实构造 | grep（D2 只读全量） |
| F13 | 库 KF（BoT-SORT `KalmanFilterXYWH`）状态 8 维 (xc,yc,w,h,vx,vy,vw,vh)，单位为检测输入画幅像素与「每帧」；`update()` 内 `multi_predict(strack_pool)` 先于 `_pre_first_associate`（补偿），未确认轨迹只补偿不预测；`project()` 量测噪声 std = (w/20, h/20, w/20, h/20)；库内 `update`/`re_activate` 不传置信度缩放 | `.venv-yoloe` 内 ultralytics 8.4.104 `trackers/utils/kalman_filter.py`（`_std_weight_position = 1/20`）、`trackers/byte_tracker.py::update` |
| F14 | 未匹配高分检测（≥ `new_track_thresh` 0.25）建轨即分配 ID，`is_activated=False`（未确认）；次帧匹配才激活并进输出，未匹配即 removed；输出只含已激活行 | `byte_tracker.py::_init_new_tracks`/`_unconfirmed_association`/`_format_output` |
| F15 | 指针清除路径：`_retire_pointer(clear_core=True)` 经 `getattr(tracker, "follow")` 动态调 `follow(None)`；`ResidentCore.clear()` 直接置空指针与 coasting；`e1.py` 每次解析后 `follow(None)` | `language_loop.py::_retire_pointer`；`resident_core.py::clear` |
| F16 | 语言路径：确认 → `designate`；BOUND/BOUND_COASTING → `_new_pointer_epoch`（先 `_retire_pointer(clear_core=False)` 再 `follow`）；TRACK_ENDED 或 coasting 超时 → `_begin_acquiring`（`_retire_pointer` 清指针）→ 到位后 `_adoption_candidate` 连续 `n_adopt` 帧 → `_acquire_adopted` → `_new_pointer_epoch` | `language_loop.py::_designate_resident`/`_begin_acquiring`/`_acquire_step`/`_acquire_adopted` |
| F17 | `CliRunner.argv` 只接 token/index/instruction/intent/delay_s，`CLI_ACTIONS` 无 click；`Submitter.submit` 参数同；`on_reply` 抛异常只 `log.write("record_reply_failed")`，不 seal、不记 UNKNOWN；CLI 写请求等回执的函数是 `language_loop.send_request` | `operator_web.py::CliRunner`/`Submitter.submit`；`language_loop.py::send_request` |
| F18 | `git diff c4973d0 HEAD -- controller/` 为空（c4973d0 = 回放设计 §1 记载的 10-08 Play 代码）；即当前 `controller/` 与 10-08 现场代码相同 | 本会话只读 git |

## 1. 目的与价值

主线目标（逐字引用 `docs/project-background.md` §3）：

> 做一个边缘语义目标获取与跟随闭环，VLM 是主角：用户通过点击或语言指定目标，VLM 把语义要求映射到可见候选、承接持久任务，并对歧义与不存在显式报告；快层负责关联与状态估计，只做一轮必要修正，不做研究主张；系统在模型延迟和相机运动下完成捕获、换目标与短时重关联，对观测丢失和不可达显式反馈；部署目标是 VLM 与快层跑在 Jetson Orin Nano 8GB，Unity 留桌面机。

同节约束 1（逐字）：「快层是非变量」→「快层只做一轮必要修正，额度一次 Play，不扩成跟踪研究」。

本项就是那「一轮必要修正」。VLM 旁路（零 VLM 查询），只解决 10-08 暴露的问题：移动目标一被指定、云台一转就丢，丢了 31 帧不报。让快层在相机运动下完成**点击捕获、换目标与短时重关联**，对观测丢失**显式反馈**，并把「谁能改目标」收进一个有证据的提交入口（第二轮 VLM 承接持久任务要接的地方）。本项不让 VLM 担任何新角色，不为快层做研究主张；所有读数只说明本仿真、本参数下的工程行为。

## 2. 范围与不做的事

### 2.1 改动闭集（草案 §5 第一轮：目标管理器、位姿补偿、跟踪中丢失的收养触发、预测窗口发 look_at、点击入口、报告时延）

**两种会话模式**（D2 新增，回应 (g)/AR1-3）：`run --language off`（新，**捕获模式**）启用本节全部新行为；`run --language on`（现行，**兼容模式**）行为保持现状，唯一变化是指针写入改经 `commit_binding`/`release_binding`（准入与副作用逐条等同现行，§3.5）。Play 只用捕获模式。

- **C1 检测类别策略**：`DetAssocTracker` 新增 `class_policy ∈ {per_class, unify_vehicle}`；`unify_vehicle` = `predict(..., agnostic_nms=True)` 且进关联器前 cls 置 0。**构造器缺省不变**（`per_class`），SOT 第二级、`tools/eng_acq/e1.py`、compat 模式与其他离线工厂不传新值；只有捕获模式会话入口与 `tools/eng_capture/replay.py` 新臂显式传 `unify_vehicle`。权重、`conf`、`imgsz`、`nms_iou`、规格与 freeze 文件不改；per_class 的既往验证不外推到 unify_vehicle（新臂独立取证，AC-17）。
- **C2 位姿补偿只移中心**（用户方向）：新增 `gmc_source="pose-center"`；**构造器缺省仍为 `pose`**（作为 `pose-aabb` 别名，旧日志可解析），兼容模式不变；只有捕获模式会话与回放新臂显式传 `pose-center`。中心经 H 映射；宽高与宽高速度不变；位置/速度及其协方差块经 H 在中心处的雅可比转换。`optflow`/`none` 不改。
- **C3 历史契约补列**（v3.1 A8；AR1-2）：每帧另存原始检测、未确认轨迹行、`matched_det_index`、每行只读 KF 快照（§3.1）；出画或退化的 lost 框不再丢弃，改带 `out_of_frame`；深度 128 不变。这些字段**只在进程内与会话日志**，不进任何桥文件。
- **C4 目标管理器**（新文件 `controller/target_manager.py`，纯 Python，无 ultralytics、无真值）：一个 reducer 管 TaskSpec、BindingRecord、连续性与观测状态、按帧计的截止、修复证据缓冲、授权函数与事件日志（§3.2–3.4）；会话每帧喂历史，按其效果发布，并把状态投影到九态外壳（§3.6）。兼容模式下只承担单写者与日志，连续性修复、预测 look_at、新报告均关闭。
- **C5 designate 拆分**：`ResidentCore.resolve_designation(box, k)` 纯解析（不改指针、coasting、designation 计数）；`TargetManager.commit_binding(...)` 为唯一设指针入口，`TargetManager.release_binding(reason)` 为唯一会话内清指针入口（§3.5 路径表）。`ResidentCore.designate` 原样保留只作 `e1.py` 兼容外壳，会话不调用。
- **C6 预测窗口发 look_at 与瞄准点**（捕获模式）：授权表行 7 条件全满足时（§3.4），云台按原绑定轨迹的内部未裁剪预测中心发 look_at；机身显式 HOLD。云台瞄准点改用框中心射线 ∩ 平面 y = `ground_plane_y_m` + h_c（P_center）；机身估计器量测点（框底中点）不改。
- **C7 点击入口**（捕获模式）：动作闭集追加 `click`（x_px、y_px、frame_id、image_sha256）；会话在 k 帧历史解析「包含点的框」，逐帧验证 k→当前证据链后经 commit_binding 绑定；不调 VLM、无二次确认；再次点击即换目标、新 episode。兼容模式收到 click → `REQUEST_INVALID`（`click_unavailable`）。本机点击页 `tools/eng_capture/click_web.py` 进程内调 `send_request` 提交（§3.5；最小 diff 闭集见 §2.5）。
- **C8 报告时延**（捕获模式）：最后可靠观测 t0 后第 T_report 帧报告「无新观测」，第 T_repair 帧报告连续性中断；竞争锁存报告身份争议（§3.3 边界表）。
- **C9 语言关闭模式**：`run --language off` 不建适配器与 worker、不读 K 收据，`k_pub` 取常量 `K_PUB`；ask/respecify/verify/confirm 一律 `REQUEST_INVALID`（`language_disabled`）。
- **C10 证据工具**：`tools/eng_capture/replay.py`（离线回放、故障注入、合成滚转；基线臂见 AC-17）、`tools/eng_capture/baseline_runner.py`（只在基线源导出目录上运行）、`tools/eng_capture/analyze_play.py`（Play 读数，真值只进 `score_` 函数）；`config/p1-eng-capture-001.json` 存参数（逐值带 §3.7 类别），其 sha 进每条转换事件；操作单 `docs/evidence/P1-ENG-CAPTURE-001-play-ops.md`。

### 2.2 骨架 v3 取舍

| v3 节 | 本轮处置 | 理由 |
|---|---|---|
| §1 不变量 1–4、6、7 | 采纳 | 换 ID 不换任务、改目标必经提交、截止不续期、新实例记新 episode |
| §1 不变量 5 | 部分 | 只用于点击：`NO_TRACK_AT_K` 记作「k 帧候选里没有」；VLM 侧随第二轮 |
| §2 AimIntent | 部分 | 内部记录 world_point、source、valid_until（帧）、episode_id、association_revision 并进日志；接口层不改 |
| §3 四条记录 | 部分 | TaskSpec 实现点击子集与语言兼容投影；phase 只用 {ACQUIRING, TRACKING, CANCELED}；BindingRecord 全量；TargetBelief 只用像面预测与三状态，`filter_snapshot_at_last_reliable` 延后 |
| §4 转换函数与授权函数 | 采纳（按 A10/A11） | §3.3–3.4 |
| §5.1 reducer 与事件日志 | 采纳 | AC-15（从落盘输入重放） |
| §5.2 发布前复核 | 采纳（按 A12） | AC-11 |
| §5.3 异步结果、§5.4 持久任务 | 延后 | 本轮无 VLM |
| §6 resolve/commit 与路径 | 采纳 INITIAL、CONTINUITY_REPAIR、USER_RESELECT；语言两条兼容路径；ATTRIBUTE_REPLACE 延后 | §3.5 |
| §6 旧 acquire 身份规则 | 不在本轮修 | 兼容模式原样保留 `_adoption_candidate`，只改为经 commit_binding 写指针；捕获模式不可达；记为已知偏差，第二轮处理 |
| §7 历史契约 | 采纳（A8） | C3 |
| §7 KF 快照回放 | 延后 | 只读 KF 快照进历史（§3.1），但不做「回到最后可靠帧重放滤波」；提交后丢掉 N_adopt−1 个证据帧的量测，写入 §6 |
| §8 时限 | 采纳结构约束、边界顺序、看门狗（沿用 `T_STALL_S`）；T_fg、提案有效期不适用 | §3.3 |
| §9 参数表 | 采纳形式 | §3.7 |
| §10 语义层、§15 探针 | 不适用 | 第二轮 |
| §11 在线/离线命名 | 采纳 | 在线事件只用运行时可知的词 |
| §12 最低日志 | 采纳 | §3.8 |
| §13 配置轴 | 采纳 `auto_repair` 开/关；`latency_profile`、`confirmation_policy` 不适用 | `auto_repair=off` 作故障注入对照臂 |
| §14 契约测试 | 采纳 #1–#8、#10–#12；#9 延后 | AC-4…AC-11、AC-15 |

### 2.3 v3.1 修订清单逐条处置

| # | 处置 | 落点 |
|---|---|---|
| A1 门 0、NIS 裕度、DISPUTED 定义 | 采纳 | §3.3、AC-6 |
| A2 原 ID 1 帧回 SUPPORTED、新 ID 需 N_adopt | 采纳；误 TENTATIVE 率只报读数 | AC-5、AC-17 |
| A3 R-3 配对口径 | 延后（无相似干扰车素材）；按 USER-4A 第一轮不声称误收养率 | §6 |
| A4 两种量测点、瞄准点 | 部分：云台瞄准改 P_center；机身估计器量测点不改 | C6、AC-9 |
| A5 semantic_status 契约 | 本轮恒 UNKNOWN；授权表保留 CONTRADICTED 行（不可达） | §3.4 |
| A6 持久任务拒绝记忆 | 不适用 | — |
| A7 证据资格按 frame_id | 采纳；`vlm_busy` 延后 | §3.3、AC-10 |
| A8 原始检测进历史 | 采纳 | C3、AC-3 |
| A9 新捕获 belief 初始化回放 | 延后 | §6 |
| A10 未提交候选不驱动云台；OBSERVED 定义 | 采纳 | AC-8 |
| A11 授权全函数与优先级 | 采纳 | §3.4、AC-8 |
| A12 单写者、STOP 串行、follow() 回滚 | 采纳 | AC-7、AC-11 |
| A13 T_pred 生存界 | 采纳为读数口径；配置值仍为占位 | AC-17、§3.7 |
| B1 phase 只留生命周期 | 采纳 | §3.2 |
| B2 TaskSpec 合法性 | 采纳点击子集与语言兼容投影 | AC-4 |
| B3 措辞统一 | 采纳 | §3.2 |
| B4 来源快照选择语义 | 用于点击：在帧 k 选择，逐帧验证连续到当前 | AC-12 |
| B5 点击即批准 | 采纳 | AC-12 |
| B6 前台语义延迟 | 不适用 | — |
| B7 三种时间、积压旧帧不算新鲜 | 采纳（§3.3 批内规则） | AC-10 |
| B8 P_max 与 R 独立性 | 像面版：`r_gate_max`；地面版延后 | §3.1 |
| B9 数字三类 | 采纳；设计预算已由 USER-4A 给占位 | §3.7、§4.1 |
| C1 暂定值带样本量 | 采纳 | §3.7 |
| C2 合成转向帧 | 采纳为非劣化回归（评分口径冻结见 AC-19） | AC-19、AC-27 |
| C3 回放不能替代闭环 | 部分：保留 30°/s 视线限速；Play 逐帧记图像滚转读数 | AC-23 |
| C4 T_repair 按剩余机制定 | 采纳 | §3.7 |
| C5 机身首次闭环 | 采纳 | AC-25 |
| C6 A/B 探针 | 不适用 | — |
| C7 正向契约用例 | 部分：点击直接捕获、窗口内真正修复 | AC-6、AC-12 |
| D 回放导出 | 采纳子集；`vlm_busy` 延后 | AC-17 |

### 2.4 明确不做

- 第二轮：VLM 接口探针、板上查询、语言分支任何新行为（兼容模式不加修复/预测/新报告）、`LanguageWorker` 改动。
- 第三轮：演示四幕、Unity 场景改动（相似干扰车、第二辆车运动）。
- 属性分类器；VLM 重训；检测器重训或换权重。
- 快层多轮研究：不换关联器、不加 ReID、不调 BoT-SORT 冻结参数、不做按图像滚转率限速的转向控制、不调规划器或 FRAME-001 机身参数。
- 板上快层框架选择与任何板上动作。
- Unity 脚本、`*.unity`、`config/scenario.*.json`；`P1-ENG-LOOP-002` 提案、`docs/parked-status.md` 及其 Gate 行；K5。

### 2.5 复用与承接（`P1-ENG-LOOP-002` 暂停中，只引用、不改其提案与门）

| 来源 | 本项用法 | 判定 |
|---|---|---|
| LOOP-002 A1 `--body-policy standoff`、§3.1 覆盖文件（`retained_frame_count` 1500）、`T_sess` 帧起点式 | Play 原样复用 | 复用 |
| LOOP-002 A3 显式 hold 收据、`JOURNAL_KINDS` 闭集；A5 会话单次权重加载；A6 `frames_processed.metadata_sha256`；A7 `geometry_rejected` | 原样复用；新事件名只追加 | 复用 |
| LOOP-002 §3.4 闭集表（指针 raw LOST → 不发 look_at）与 AC-4 | 本项**仅在捕获模式**改为预测窗口内发云台 look_at；兼容模式不变。按 (f) **不向 LOOP-002 提案追加任何内容**；差异只在本提案登记，LOOP-002 旧 verdict 只绑旧候选，恢复与基线归用户 | 改语义（本提案内登记） |
| LOOP-002 `Submitter`/`OpsLog` | 点击页导入复用。`operator_web.py` **diff 闭集恰两处**：① `Submitter.submit` 增仅关键字参数 `extra_argv: Mapping[str, Any] \| None = None`，为 None 时原样调用 `argv_builder.argv`（既有动作 argv 逐字节不变）；② R1-5 `on_reply` 失败路径（下行）。`CliRunner`、`CLI_ACTIONS`、`App`、`Monitor`、`Handler`、W1–W5 零 diff | 复用 + 窄修 |
| LOOP-002 R1-5（`implementation-status` 账本 OPEN） | 新 click 故障域**触发** on_reply 子路径：on_reply 抛异常 → 先在同一把锁内于内存 seal 该会话、写 `unknown[request_id]`（保留 request_id 与「已发送」事实），再尝试写日志；记录器自身再抛也不影响已完成的内存 seal，回复带 `sealed`/`unknown`。具名回归 `test_click_on_reply_failure_seals`、`test_on_reply_and_log_failure_still_seals`。R1-5 的 CLI kill/quiesce 收尾子路径**不销账**、本项不复用计划收尾器，原债保持 OPEN | 触发（窄） |
| LOOP-001 F8（复用可变归档前承接哈希/时刻一致性） | 回放只用 USER-4A 准入原件：**触发**；开跑前对准入文件现算 sha256 清单入证据并与 `replay-transfer/SHA256SUMS` 对应行比对，帧旁车 `frame_id`/`simulation_time_s` 与真值行一致，不符即停（S-A-INPUT） | 触发 |
| LOOP-001 F3（触及 `LanguageWorker`） | 不触发：`LanguageWorker` 类 diff 为空（AC-13） | 不触发 |
| ACQ K1K3-R1-1（`CandidatesBackend`/预检） | 不触发：diff 为空（AC-16） | 不触发 |
| FRAME-001 R1-3（围栏数值域） | 不触发：围栏代码 diff 为空 | 不触发 |
| FAST-001 R1-2（空窗 `KEPT`） | 不触发：不复用 `replay.py:window_outcome()` | 不触发 |
| LOOP-002「红车居中一次后不跟随」与 REPAIR:DIRECTION | 不代答 LOOP-002 的题 | §9 已定事项 |

## 3. 接口与数据契约

### 3.1 检测、关联与只读 KF 快照（C1–C3；K1/K3）

- `DetAssocTracker(class_policy=..., gmc_source=...)`；`manifest_identity()` 增 `class_policy`、`agnostic_nms`；`gmc_source` 闭集扩为 `{pose, pose-center, pose-aabb, optflow, none}`（`pose` ≡ `pose-aabb`）。检测缓存键 = (权重 sha, `class_policy`, `agnostic_nms`, imgsz, conf, nms_iou, 帧字节 sha)；补偿源另记在运行 manifest。
- `apply_pose_center(tracks, H)`：(xc, yc) ← H(xc, yc)；J = ∂H/∂(u,v)|(xc,yc)；(vx, vy) ← J·(vx, vy)；8×8 变换在位置块与速度块放 J、其余单位；P ← T P Tᵀ。宽高与宽高速度不变；`map_point` 返回 None 或雅可比不可得时该轨迹不改。
- **只读 KF 快照**（AR1-2）：`DetAssocTracker.step` 在 `tracker.update` 返回后，对 `tracked_stracks`（含未确认）与 `lost_stracks` 每条复制（不回写）`KfSnapshot{xywh_px, vel_px_per_frame(vx,vy), pos_cov_px2 = covariance[0:2,0:2], phase}`。`phase = posterior`：本帧已用检测更新；`phase = prior`：本帧未更新（lost，或未确认未匹配），即库「预测 → 本帧补偿」后的状态（F13 顺序）。单位：检测输入画幅像素（640×480）、像素²、每帧。任一分量非有限、w/h ≤ 0、协方差非对称或最小特征值 < −1e-9 → `kf = None` 并记 `kf_invalid_reason`；消费方一律 fail-closed（运动门不过、授权落行 8）。
- **运动门的 S**（明列假设）：候选在帧 f 的检测中心 z（模型输出原始框，未裁剪）对原轨迹 o 在 f 的 prior 中心 μ：d = z − μ；S = P_pos + diag((w_o/20)², (h_o/20)²)，即库 `project()` 的位置块（厂商常数 1/20，F13；本项未标定，世界系 R-4 NIS 不替代）；NIS = dᵀS⁻¹d；另要求 √(g_motion·λmax(S)) ≤ `r_gate_max`。o 的 prior 在 o 被库删除（30 帧）前每帧都有，T_repair ≪ 30。
- **内部与对外分开**：预测框、`out_of_frame` 行、KF 快照只在进程内与会话日志；PREDICTED 帧不发 tracking observation（与现行 lost 一致），对外桥文件只出现 OBSERVED 帧的画幅裁剪框；预测只以云台 look_at 世界点出现。
- 历史行：`TrackRow` 增 `state ∈ {tracked, lost, unconfirmed}`、`matched_det_index`（无则 −1）、`out_of_frame`、`kf`；`HistoryEntry` 增 `raw_detections`（det_index、未裁剪 box_px、conf、策略后 cls）、`silently_dropped_ids`（非有限框仍丢弃时）。`pointer_result` 语义不变：未确认行与 out_of_frame 行都不算 ok。

### 3.2 目标管理器记录（C4；K3）

```
TaskSpec（不可变）
  selector = Click(x_px, y_px, frame_id, image_sha256) | LanguageCompat(designation_id, box_k, k)
  binding_mode = INSTANCE; activation = NOW; on_ambiguity = ASK; on_loss = ASK
  intent_revision                  每次被接受的提交 +1（被拒请求不变）
TaskRuntime
  phase ∈ {ACQUIRING, TRACKING, CANCELED}; mode ∈ {capture, compat}
  episode_id, deadlines（以 frame_id 计）
BindingRecord
  target_episode_id, track_key, association_revision
  relation ∈ {INITIAL, CONTINUITY_REPAIR, USER_RESELECT}; origin ∈ {click, repair, lang_confirm, lang_acquire}
  evidence_refs（帧号、行键、门限值、tm_inputs 行 sha、配置 sha）
TargetBelief（本轮子集）
  t0 = 最后已接受观测的 frame_id; last_accepted_observation（frame_id、box、track_key）
  predicted（内部未裁剪中心与宽高、pos_cov_px2，取自 §3.1 快照）
  observation_status ∈ {OBSERVED, PREDICTED, STALE}; continuity_status ∈ {SUPPORTED, TENTATIVE, DISPUTED, BROKEN}
  semantic_status ≡ UNKNOWN; geometry_valid; age = 当前帧 − t0
RepairBuffer（有界）：候选键、各证据帧引用、各门结果、累计 NIS、版本、截止
```

- **OBSERVED** 只在 belief 被已接受观测更新时成立（A10）：原绑定轨迹本帧 tracked 且过运动门与尺寸门，或修复刚提交。
- **合法构造**：Click → 只能 INSTANCE+NOW+ASK；LanguageCompat 只能由兼容模式的语言确认/收养路径构造；INSTANCE+REARM、无谓词 WAIT 构造即拒（v3 §14 #11/#12）。
- 旧 episode 一旦 DISPUTED/BROKEN 不再恢复 SUPPORTED；只有新点击（USER_RESELECT）建新 episode；旧 episode 关闭记事件与原因（B3），且**只在新绑定成功提交后**关闭。

### 3.3 连续性、时间边界与收养（C4/C8；K1/K3）

**唯一写 `continuity_status` 的是 `transition(belief, event)`**。合法边：SUPPORTED→TENTATIVE（原轨迹本帧未匹配或不过门）；TENTATIVE→SUPPORTED（原轨迹在窗口内重新过门且无竞争，1 帧即回；或修复提交）；SUPPORTED/TENTATIVE→DISPUTED（无法消解的竞争）；SUPPORTED/TENTATIVE→BROKEN（到期）。DISPUTED/BROKEN 是当前 episode 的终点。

**结构约束**（配置加载即校验，不满足拒绝启动；AR1-1）：N_adopt ≥ 2；1 ≤ T_report ≤ T_repair − 1；1 ≤ T_pred ≤ T_repair − 1；1（无候选容忍）+ N_adopt + 1（处理余量）≤ T_repair − 1。占位 N_adopt 2、T_report 3、T_pred **4**（D1 的 5 违反新约束）、T_repair 5。

**到期规则**：age ≥ T_repair 即到期，到期先于同帧任何证据处理；修复提交只允许 age ≤ T_repair − 1（严格早于到期帧）；T_pred ≤ T_repair − 1 使「预测 look_at」与「到期撤权」永不同帧。

**同帧顺序**（每个被处理帧 f）：① 停止/替换任务请求 → ② 到期判定（age ≥ T_repair → BROKEN，清 RepairBuffer，本帧证据与原 ID 重现都不再用于本 episode）→ ③ 原轨迹重匹配（过门且无竞争 → OBSERVED/SUPPORTED，t0 = f）→ ④ 修复证据入缓冲与提交判定（仅 age ≤ T_repair − 1）→ ⑤ 授权与效果。

**批内规则**（B7）：一个 tick 追平多帧时，各帧按 frame_id 依次走 ①–④（截止、证据都按 frame_id）；⑤ 只对本批最新帧求值并产生命令，旧帧不发命令、不单独刷新新鲜度。STALE 只由看门狗（无新帧 > `T_STALL_S`）给出。

**边界逐列表**（占位值，假设无恢复、几何有效、协方差未超限；t0 = 最后已接受观测帧）：

| age | 0 | 1–2 | 3 = T_report | 4 = T_pred = T_repair−1 | 5 = T_repair | ≥ 6 |
|---|---|---|---|---|---|---|
| continuity / observation | SUPPORTED / OBSERVED | TENTATIVE / PREDICTED | TENTATIVE / PREDICTED | TENTATIVE / PREDICTED | BROKEN | BROKEN |
| state / reason | TRACKING / null | TRACKING / `predicting` | TRACKING / `no_new_observation`（本帧恰发一次事件） | 同左（不重复事件） | SUSPECTED / `continuity_broken` | 同左 |
| gimbal / body | 观测 P_center / FOLLOW | 预测 P_center / HOLD | 预测 / HOLD | 预测（最后一帧）/ HOLD | 不发 / HOLD | 不发 / HOLD |
| 修复提交 | — | age ≥ N_adopt 起可（最早 age 2） | 可 | 可（最后机会） | 否（先到期） | 否 |

一般式：预测 look_at 只在 1 ≤ age ≤ T_pred 且授权行 7 全部条件成立；T_pred < age < T_repair 落行 8；age ≥ T_repair 必为 BROKEN。提前可靠恢复（③）、DISPUTED、几何拒绝、协方差超限或 `kf=None` 的帧不发预测 look_at，测试不得强制。

**assess_continuity_repair**（新 ID 接管原目标，仅捕获模式且 `auto_repair=on`）：
- **门 0 排除**（A1）：[绑定帧, t0] 内与原轨迹同帧 tracked、且自身中心无大于 `r_jump` 跳变的轨迹，从候选与竞争者中一并排除。
- **候选与证据单位**：证据 = (帧 f, 库轨迹键 c, c 在 f 的状态 ∈ {unconfirmed, tracked})；与任何库轨迹无关的原始检测只记诊断，不计证据、永不可提交。
- **运动门**（§3.1 的 S）NIS ≤ `g_motion`；**尺寸门** |log(√(w′h′)/√(wh))| ≤ `g_size`；语义门本轮不阻断。
- **竞争**：过门候选 ≥ 2 时比较证据帧累计 NIS，最优与次优之差 < `m_nis` 即锁 DISPUTED（不得简化为「候选数 > 1」）。
- **可提交的活跃库键**：c 在提交帧为 **tracked 且已激活**（F14），不在 ended/removed 集；证据帧须为 c 的 N_adopt 个**连续** frame_id（中间缺帧即清零重计）；提交帧 age ≤ T_repair − 1 → `commit_binding(relation=CONTINUITY_REPAIR)`，同 episode、association_revision +1。

### 3.4 授权函数（C4/C6；K2）

`derive_authorization(task, binding, belief, now_frame) -> (body_mode, gimbal_mode, valid_until_frame, reason_codes)`，纯函数、全函数，**按行序第一条命中即定**（兼容模式不调用本函数，沿用现行发布逻辑）：

| 序 | 条件 | body | gimbal |
|---|---|---|---|
| 1 | 无有效任务 / CANCELED / 已停止 | HOLD | 不发 |
| 2 | STALE | HOLD | 不发 |
| 3 | continuity ∈ {DISPUTED, BROKEN} | HOLD | 不发 |
| 4 | semantic = CONTRADICTED（本轮不可达） | HOLD | 不发 |
| 5 | geometry_valid = false | HOLD | 不发（`GEO_REJECT`） |
| 6 | OBSERVED + SUPPORTED + age = 0 | FOLLOW（经规划器与现行约束） | look_at 观测 P_center |
| 7 | PREDICTED + {SUPPORTED, TENTATIVE} + 1 ≤ age ≤ T_pred + kf 有效 + 门半径 ≤ r_gate_max | HOLD（显式写出） | look_at 预测 P_center，valid_until = t0 + T_pred |
| 8 | 其余 | HOLD | 不发（保持当前指向） |

**有限枚举域**（AC-8）：task {none, ACTIVE, CANCELED, stopped} × watchdog {fresh, stale} × continuity {S, T, D, B} × semantic {UNKNOWN, CONTRADICTED} × geometry {valid, invalid} × observation {OBSERVED, PREDICTED} × age 带 {0, [1,T_pred], (T_pred,T_repair), ≥T_repair} × 协方差 {within, exceeds, kf_invalid} = 3,072 格；另用一组 T_pred=2、T_repair=5 的测试配置使 (T_pred,T_repair) 带非空。**授权偏序**：body FOLLOW > HOLD；gimbal 观测 > 预测 > 不发；授权 (b,g) ≤ (b′,g′) 当且仅当两分量都不高。**各轴「变差」一步**：task ACTIVE→其余；fresh→stale；S→T→D→B；UNKNOWN→CONTRADICTED；valid→invalid；OBSERVED→PREDICTED；age 带递增；within→exceeds→kf_invalid。到限位或被裁剪只记 `CONTROL_LIMITED`。修复期间候选观测只进 RepairBuffer，永不产生 look_at。

### 3.5 提交与清除路径（C5/C7；K1/K3；AR1-3）

| 路径（origin） | 模式 | 准入 | 任务投影 / episode | 指针与 coasting 副作用 |
|---|---|---|---|---|
| 点击首绑 INITIAL（click） | 捕获 | k ∈ 历史；帧字节 sha 符；`resolve_click` 恰得 j；**逐帧证据链**：对 [k, 提交帧] 每个历史帧，j 为 tracked（已激活）、不在 removed/ended，缺任一历史帧即拒 | 新 Click TaskSpec、intent_revision +1、新 episode | `follow(j)`；不设 coasting |
| 点击换目标 USER_RESELECT（click） | 捕获 | 同上 | 同上；旧 episode 在新绑定成功后以 `superseded_by_click` 关闭 | 同上 |
| 连续性修复 CONTINUITY_REPAIR（repair） | 捕获 | §3.3 收养条件 | 同 episode、association_revision +1 | `follow(c)`；不设 coasting |
| 语言确认（lang_confirm） | 兼容 | `resolve_designation(box_k, k)` 结果 BOUND 或 BOUND_COASTING（判据逐字同现行 `designate`） | LanguageCompat TaskSpec；designation_id 在提交成功时分配 | `follow(j)`；BOUND_COASTING 时按现行设 coasting（同一 designation_id、步数 0） |
| 语言转向收养（lang_acquire） | 兼容 | 现行 `_acquire_step`/`_adoption_candidate` 判据原样（不套点击证据链） | 沿用当前 designation | `follow(j)`；不设 coasting |
| 释放 `release_binding(reason)` | 两者 | 会话内一切清指针（`_retire_pointer(clear_core=True)` 改调此入口） | 当前 episode 以 reason 关闭 | `follow(None)` |
| 拆除 | 两者 | `_teardown_resident` → `ResidentCore.clear()`（直接置空，保留） | 管理器收到 `resident_teardown` 关闭 episode | 无 follow 调用 |

- `resolve_click(x, y, k)`：纯；在 k 帧 **tracked** 行里找包含点的框：0 → `NO_TRACK_AT_K`；1 → j；≥ 2 → 取框中心离点最近者，次近/最近距离比 < ρ_click 则 `AMBIGUOUS`。`resolve_designation` 纯：判据逐字同现行 designate 两级（第二级 SOT 照旧注入 runner）。
- `commit_binding(proposal, expected_versions, source_frame, evidence, origin)`：先校验版本、阶段、截止与 origin 合法性 → 在不改任何状态的前提下算出新记录 → 调 `follow(new)`。`follow` 抛异常 → 调 `follow(old)` 复原并读回 `pointer()` 核对；复原成功则任务、episode、BindingRecord、TargetBelief、coasting、designation 计数与版本全部保持调用前值，事件记 `rejected/follow_failed`；复原也失败或读回不符 → fail-closed：`release_binding`、HOLD、`REINIT_REQUIRED`/`binding_rollback_failed`。仅 `follow` 成功后才写新记录、关闭旧 episode、设 coasting。被拒（任何准入不过）同样零状态变化；**换目标被拒时继续跟旧目标**。
- **`follow` 调用点闭集**（AC-7 静态检查）：`controller/target_manager.py`（commit/release）；`resident_core.py` 的 `def follow` 与 `designate`/`_level2` 内部（只供 e1 兼容外壳）；`det_assoc_tracker.py::follow`（转发例外）。`language_loop.py` 内零直接或经 `getattr(..., "follow")` 的调用；会话不调 `designate`。
- `click` 请求：字段 `x_px`、`y_px`（`[0,width)×[0,height)`）、`frame_id`、`image_sha256`。k 不在历史 → `FRAME_NOT_IN_HISTORY`；`runtime/frames/frame_<k>.jpg` 当刻字节 sha ≠ 请求值 → `REQUEST_INVALID`（`image_mismatch`）；解析与提交在消费该请求的同一 tick 完成。
- **点击页**（`tools/eng_capture/click_web.py`）：只监听 127.0.0.1、nonce + Host/Origin 校验；按 `latest.json` 显示帧，提交浏览器实际解码字节的 sha 与该帧 frame_id；收到点击时先在服务端记 `click_received_unix_s` 与当刻 `latest.json` frame_id（e2e 起点）。提交经复用的 `Submitter`，其 `cli` 为本文件的 `InProcessSend`：在进程内调 `controller.language_loop.send_request(..., click=...)`，按 CLI 同一退出码语义（0 回执 / 2 拒绝 / 4 WRITER_BUSY / 5 无回执）返回，避免子进程启动开销计入 e2e；`argv_builder` 为子类 `ClickArgv(CliRunner)`，只为 `click`/`stop` 组 argv 供记录。另有「停止会话」按钮；无确认、无自由文本、无语言按钮。

### 3.6 状态投影与报告（C8；K1/K2）

| 目标管理器（捕获模式） | 会话 state / reason |
|---|---|
| 无绑定 | `IDLE`（或现行 LOST(*)） |
| OBSERVED + SUPPORTED | `TRACKING` / null |
| PREDICTED，age < T_report | `TRACKING` / `predicting` |
| PREDICTED，T_report ≤ age ≤ T_repair − 1 | `TRACKING` / `no_new_observation` |
| 修复提交当帧 | `TRACKING` / `continuity_repaired` |
| BROKEN | `SUSPECTED` / `continuity_broken`（人：再点击、release 或 stop） |
| DISPUTED | `SUSPECTED` / `continuity_disputed` |

`STATE_REASONS` 末尾只追加：`predicting`、`no_new_observation`、`continuity_repaired`、`continuity_broken`、`continuity_disputed`、`language_disabled`、`image_mismatch`、`superseded_by_click`、`click_unavailable`、`binding_rollback_failed`。捕获模式下「库删 ID 后才报 `tracker_failure`」不再触发（BROKEN 先报）；兼容模式不变。所有年龄与截止以 **sensor frame_id 之差**计。

### 3.7 参数（`config/p1-eng-capture-001.json`；类别按 v3.1 B9，出处四类见 §4.1）

| 参数 | 类别 | 结构约束 | 值 | 依据 |
|---|---|---|---|---|
| Δt | 已知约束 | 5 Hz | 0.2 s | 场景 |
| T_report | 设计预算（用户占位，USER-4A） | 1 ≤ · ≤ T_repair−1 | 3 帧 | 草案「≤ 5 帧」 |
| N_adopt | 设计预算（用户占位，USER-4A；非 R-3 标定） | ≥ 2 | 2 | v3 下限 |
| ρ_click | 设计预算（用户占位，USER-4A） | > 1 | 1.5 | 占位 |
| T_pred | 待标定 | 1 ≤ · ≤ T_repair−1 | 4 帧 | 草案「3 到 5 帧」；R-1 诊断 pose-center 6–12 帧（不作依据） |
| T_repair | 待标定 | ≥ N_adopt + 3 | 5 帧 | v3 占位；补偿修正后剩余机制未测 |
| g_motion | 待标定 | χ²₂ 分位 | 9.21（0.99） | 像面 NIS 未标定，回放只报读数 |
| g_size | 待标定 | 面积平方根 log 比 | 0.5 | v3 占位 |
| r_gate_max | 待标定 | 像面像素 | 80 px | 占位 |
| m_nis | 待标定 | > 0 | 4.6 | 占位 |
| r_jump | 待标定 | > 0 | 0.5 框对角线 | 占位 |
| σ_p | 厂商 | — | 1/20 | F13（库常数，本项不改） |
| h_c | 已知约束 | 车高一半 | 0.775 m（相对 `ground_plane_y_m`） | `target_height_m`/2 |
| 机身进带时限 N | 由公式定 | 测前固定 | ⌈(d₀−14)/(4−2)⌉ + 2.5 + 2 s | v_max 4、目标 2 m/s、`t_lead_s` 2.5 |

「待标定」值只是让代码可运行的占位，不是默认值、不声称最优；依赖它们的读数一律标「暂定（n=…）」。

### 3.8 日志与可重放输入（AR1-2）

- **落盘 reducer 输入** `tm_inputs.jsonl`（会话目录，追加写）：每个被处理帧一行 = frame_id、`simulation_time_s`、`capture_monotonic_s`、处理墙钟、批内位置（newest/backlog）、reducer 读到的历史子集（全部行：键、state、未裁剪框、`matched_det_index`、`out_of_frame`、`kf`；原始检测；removed_ids），以及本 tick 消费的请求原文（request_id、动作、字段）与配置 sha；每行带自身 sha256。
- **事件**（进 `JOURNAL_KINDS`）：`tm_event`（event_seq、type、frame_id、accepted/rejected + 原因、effect_seq、config_sha256、所引 `tm_inputs` 行 sha）、`tm_transition`（old→new、原因）、`binding_committed`（old/new track_key、relation、origin、episode、证据引用）、`authorization`（逐帧 body/gimbal 与 reason_codes）、`click_received`（request_id、k、点、sha、消费时历史头、页面侧 e2e 起点）。逐帧另记补偿源与由位姿算的图像滚转读数（不读真值）。命令只记 `command_written`。

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | `unify_vehicle` 下同一车不再出现两类两框（注入两类重叠框的假模型 → 关联器只收 1 框、cls=0）；构造器缺省仍 `per_class`/`pose`，SOT、e1、compat 构造不传新值；权重/conf/imgsz/nms_iou/规格与 freeze sha 不变；`controller/` 无代码以 cls==1 作决策；manifest 与检测缓存键含 `class_policy`、`agnostic_nms` | `test:tests/test_det_assoc_tracker.py`（类别策略与缺省用例）；`cmd:git diff --stat <base>.. -- config/det-assoc-v1.models.json docs/evidence/P1-ENG-FAST-002-freeze.json` 为空 | K3 | |
| AC-2 | `pose-center` 对合成纯旋转单应（含 25°/帧绕光轴）：中心等于 H(中心)（≤ 1e-6 px）；w、h、vw、vh 不变；速度与位置/速度协方差块等于 J 变换；H=None 不改；`pose-aabb`/`pose` 输出与修改前 `apply_pose_warp` 逐元素一致 | `test:tests/test_pose_center.py` | K1 | |
| AC-3 | 历史每帧含原始检测、未确认行、`matched_det_index`、`silently_dropped_ids`、KF 快照（phase、单位、非有限/非 PSD → `kf=None`）；出画 lost 行保留并带 `out_of_frame`，指针此时判 UNMATCHED；`pointer_result` 对既有用例不变；桥文件（tracking_observation、tracker state）中不出现未裁剪框、`out_of_frame` 或 KF 字段 | `test:tests/test_resident_core.py`（历史契约）；`test:tests/test_det_assoc_tracker.py::KfSnapshot*` | K1 | |
| AC-4 | TaskSpec 不可变；Click 只能 INSTANCE+NOW+ASK，LanguageCompat 只能由兼容路径构造；INSTANCE+REARM 与无谓词 WAIT 被拒；被接受的提交 intent_revision 与 episode_id 递增，被拒请求两者不变 | `test:tests/test_target_manager.py::TaskSpec*` | K3 | |
| AC-5 | 只有 `transition` 写 `continuity_status`（静态检查 + 用例）；已锁存争议后原 ID 又以小创新匹配 → 不清争议、不恢复 FOLLOW（#1）；age ≥ T_repair 后原 ID 重现 → 不续跟（#2）；原 ID 在窗口内重新过门且无竞争 → 1 帧回 SUPPORTED | `test:tests/test_target_manager.py::Continuity*`；`cmd:` 静态检查列全部赋值点 | K3 | |
| AC-6 | 收养：一帧无候选后同一合格候选在 N_adopt 个连续新帧过门、提交帧已激活 → 修复（#3）；第 N_adopt 份证据落在 age = T_repair 帧 → 先到期、拒绝（#4）；只有原始检测无库键 → 永不提交；未确认帧计入证据但不可在该帧提交；门 0 排除；两候选 NIS 差 < m_nis → DISPUTED；违反 §3.3 结构约束（含 T_pred = T_repair）的配置拒绝加载 | `test:tests/test_target_manager.py::Repair*` | K3 | |
| AC-7 | `resolve_*` 前后指针、coasting、designation 计数不变；commit 被拒 → 任务/episode/BindingRecord/TargetBelief/coasting/designation/版本全不变，**换目标被拒继续跟旧目标**；`follow` 抛异常（含「先改指针再抛」的半改替身）→ 复原并读回一致，复原失败 → `binding_rollback_failed` fail-closed；BOUND_COASTING 经 commit 后 coasting 记账与修改前一致；首次点击证据链中间一帧断 → 拒绝，旧点附近唯一候选不补身份（#5）；`follow(` 调用点与 §3.5 闭集一致 | `test:tests/test_target_manager.py::Commit*`；`cmd:grep -rn -e "follow" -e ".designate(" controller/` 与证据文件所列一致 | K3 | |
| AC-8 | §3.4 枚举域 3,072 格（另加非空带配置）：每格命中的行条件成立且所有更前行不成立；所有单轴「变差」一步对，授权不升级；候选观测从不产生 look_at；无 OBSERVED+SUPPORTED 的帧无 WRITTEN 速度型 `body_command` | `test:tests/test_target_manager.py::Authorization*` | K2 | |
| AC-9 | 预测：在授权行 7 条件全成立的帧上，云台 look_at 指向内部预测中心的 P_center 且经现行 `servo_clamp`，机身每帧显式 HOLD 收据；age > T_pred、提前恢复、DISPUTED、几何拒绝、协方差超限、`kf=None` 各一例均无预测 look_at；OBSERVED 帧瞄 P_center；机身估计器量测仍取框底中点（与修改前逐帧一致） | `test:tests/test_capture_session.py::Prediction*`（假检测器驱动） | K2 | |
| AC-10 | §3.3 边界表逐列：age = T_report 恰一次 `no_new_observation`；age = T_repair 恰为 `SUSPECTED/continuity_broken` 且同帧证据被拒；截止以 frame_id 计，墙钟延迟注入不改结果；批内旧帧不发命令（B7）；新原因追加在 `STATE_REASONS` 末尾 | `test:tests/test_capture_session.py::Report*` | K1 | |
| AC-11 | 停止后先写 hold，之后到达的旧控制效果被丢弃，无 FOLLOW 速度命令（#7）；无新帧 → STALE，不续发运动命令（#8）；授权检查、命令写出、STOP 在同一单写者内串行 | `test:tests/test_capture_session.py::Stop*` | K2 | |
| AC-12 | 点击：sha 不符 → `image_mismatch`；k 不在历史 → `FRAME_NOT_IN_HISTORY`；0/1/≥2 包含框 → NO_TRACK_AT_K / 绑定 / AMBIGUOUS（按 ρ_click）；j 在 [k, 当前] 任一帧不 tracked → 拒绝；已有绑定再点 → USER_RESELECT、新 episode、旧 episode 在成功后关闭；兼容模式 click → `click_unavailable`；零适配器调用、零确认步骤；**受理子段**：提交帧历史头 − 消费时历史头 ≤ 1 | `test:tests/test_capture_session.py::Click*` | K1 | |
| AC-13 | `--language off`：不读 K 收据、不建适配器与 worker；ask/respecify/verify/confirm → `language_disabled`；`LanguageWorker` 类 diff 为空；兼容模式：语言路径既有测试相对基线无新增失败，另加语言确认（BOUND/BOUND_COASTING）、coasting 超时转 acquire、acquire 收养三条用例，经 commit/release 后的指针、纪元、coasting、状态与原因序列与修改前代码在同一脚本输入上逐条一致 | `test:tests/test_capture_session.py::LanguageOff*`、`::LanguageCompat*`；`cmd:git diff <base>.. -- controller/language_loop.py` 中 `class LanguageWorker` 区段为空 | K1 | |
| AC-14 | 点击页：只监听 127.0.0.1、nonce 与 Host/Origin 校验；提交 frame_id 与 sha 来自浏览器实际解码字节；`InProcessSend` 退出码语义与 CLI 一致（四种结局各一例）；R1-5 两条具名回归（§2.5）；`operator_web.py` diff 恰为 §2.5 两处，既有动作 argv 逐字节不变、既有 operator_web 测试无新增失败 | `test:tests/test_capture_click_web.py`；`cmd:git diff <base>.. -- tools/eng_loop2/operator_web.py` | K1 | |
| AC-15 | 事件日志每条带 event_seq、accepted/rejected 与原因、effect_seq、config_sha256、所引 `tm_inputs` 行 sha；**只读落盘的 `tm_inputs.jsonl` 与配置文件**重放 reducer，转换、拒绝原因、绑定与效果序列逐条相同（#10）；篡改任一输入行 → 行 sha 校验失败、重放拒绝 | `test:tests/test_target_manager.py::Replay*` | K3 | |
| AC-16 | 真值隔离：`controller/`、`click_web.py` 不读 `m3_body_truth`、评分产物或 `CoverageEvaluator` 输出；真值只进 `analyze_play.py` 与 `replay.py` 的 `score_` 函数（静态检查）；以下 diff 为空：`Assets/`、`*.unity`、`config/scenario.*.json`、`CandidatesBackend`/`_validate_candidates_source`、围栏读取、`tools/eng_loop2/`（除 AC-14 两处）、LOOP-002 提案 | `test:tests/test_capture_isolation.py`；`cmd:git diff --stat <base>..` | K4 | |
| AC-17 | 离线回放（Mac mini，每候选 YOLO 1 次加载）。**输入只限 USER-4A 准入原件**（帧 jpg/json 与位姿字段；真值只进 `score_`）；不读旧会话日志、`frames.jsonl`、RECHARTER 导出或其读数。开跑前 S-A-INPUT 核（§2.5 F8 承接）。**点击剧本**：运行前由人只看准入原始帧预登记 (frame_id, x_px, y_px)（含 557 帧点红车、此前点一辆静止车各一次），剧本 sha 入证据，不读真值。**基线臂**：`baseline_runner.py` 在基线源导出（本提案 `ACCEPTED` 裁定提交上的 `controller/`，运行时由 git 解析并核其与 F18 等价，不手写）上运行，`per_class`+`pose`，以点击点在 k 帧包含框作 `designate` 输入，检测来自本次 per_class 缓存（替身 `model_loader`，零加载）；**现象门**：红车点击后在 559–565 帧内至少一帧指针非 ok 且真值可见，否则 S-A-REPRO。**新臂**（`unify_vehicle`+`pose-center`+目标管理器，同一剧本）：判据 = 557–600 每个真值可见帧上要么 OBSERVED 且绑定框与真值 IoU ≥ 0.5，要么处于 age ≤ T_repair − 1 的 TENTATIVE 窗口；无 BROKEN、误绑帧 0。PASS/FAIL 按此逐帧；另报暂定读数（R-1 生存下界、两种量测点残差、误 TENTATIVE 次数，均带 n） | `artifact:docs/evidence/P1-ENG-CAPTURE-001-replay.md` §1–3；`cmd:python -m tools.eng_capture.replay run …` | K3 | |
| AC-18 | 故障注入（新臂检测缓存，零推理）：红车 561 起删检测 m∈{1,2,4,6} 帧，另强制对目标开新轨迹。每种注入：授权行 7 成立帧都有预测 look_at；**IoU 判定**：下一次真实观测 = 缺口后首个与真值 IoU ≥ 0.5 的检测；预测框与其 IoU ≥ 0.3 → PASS，< 0.3 → FAIL，缺口后 T_repair 帧内无真实观测 → NOT_EVALUABLE（不计通过）；窗口内修复或在 T_report/T_repair 准时报告；age ≥ T_repair 后原 ID 重现不续跟；`auto_repair=off` 对照只报告不修复 | `artifact:docs/evidence/P1-ENG-CAPTURE-001-replay.md` §4 | K2 | |
| AC-19 | 合成滚转（同一次加载；真值基 6 个 × ω∈{15,20,25}°/帧 × Θ∈{60°,120°} × 正负 = 72 序列，每序列热身 8 帧复用原始检测 + 变换 16 帧，两臂各 1,152 推理帧）。**评分口径冻结**：真值中心 = H(真值框中心)，真值多边形 = 四角经 H；在画内面积 < 50% 的帧为删失；「在目标上」= 观测框中心落在真值多边形内；**断轨** = 未删失帧上连续 ≥ T_repair 帧无有效观测（基线臂指针非 ok / 新臂非 OBSERVED）或任一有效观测帧不在目标上（误跟单列并计入）；序列末不足 T_repair 帧的缺口记右删失单列；每格分母 = 热身与旋转首帧均未删失的序列数。判据：新臂每格断轨率 ≤ 基线臂，带 Wilson 95% 区间与 n，只作非劣化，不声称阈值；RECHARTER 诊断的 3D 投影真值等口径不继承 | `artifact:docs/evidence/P1-ENG-CAPTURE-001-replay.md` §5 | K4 | |
| AC-20 | 停点全套：每候选在 Mac mini 以 `.venv-yoloe/bin/python` 跑一次，写 `docs/evidence/P1-ENG-CAPTURE-001-tests.log`，分列基线已有失败与本批新增失败；新增失败为 0；新测试一律注入替身；真实 YOLO 构造次数按 F12 清单与 skip 状态如实记录，超出清单即 S-A-LOADER | `cmd:.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-CAPTURE-001-tests.log 2>&1` | K1K2K3K4 | |
| AC-21 | 操作单：Air 发令前记录 `git rev-parse HEAD` 与 `git status --porcelain`；§8.2 Air 预检原始读数；覆盖文件（`retained_frame_count` 1500）生成与 sha；`T_sess` ≤ min(290 s, (1490−f₀)/5)；会话命令（`--language off --resident --body-policy standoff`）；点击剧本 S1 点一辆静止车；S2 红车入画、操作者判断其远于静止车时点红车；S3 跟随红车 ≥ 1 圈；S4 点静止车再点回红车；§6 STOP 表；按钮墙钟 ≤ 420 s；一次 Play、失败不重试 | `artifact:docs/evidence/P1-ENG-CAPTURE-001-play-ops.md` | K1K2K3K4 | |
| AC-22 | Play 点击时延（USER-4A 第 2 项）：**分母 = 全部发出的点击**（含被拒、超时、UNKNOWN、未绑定）。每次记 e2e = 提交帧历史头 − 页面收到点击时 `latest.json` 的 frame_id，及子段「受理后」= 提交帧历史头 − 消费时历史头，另记墙钟（描述）。e2e ≤ 1 帧为该次 PASS，未绑定或 > 1 为 FAIL；AC-22 PASS 当且仅当全部 PASS；受理子段 ≤ 1 单独报，不替代 e2e | `artifact:docs/evidence/P1-ENG-CAPTURE-001-play.md` §1 | PlayK2K4 | |
| AC-23 | Play（离线评分，真值可见帧）：红车 ≥ 1 圈内每次失去已接受观测，都在窗口内修复，或在 age = T_report/T_repair 准时报告；**确认跟踪（SUPPORTED）期间被跟实例不是红车的帧数**照记，=0 只是本次样本观察、不作风险上界（USER-4A 第 4 项）；S4 两次换目标的 e2e 计入 AC-22，换回红车后转向不丢，或在窗口内修复/报告；逐帧图像滚转读数照记 | `artifact:docs/evidence/P1-ENG-CAPTURE-001-play.md` §2 | PlayK2K4 | |
| AC-24 | Play 预测窗口：授权行 7 成立帧都有 look_at WRITTEN 收据；每个窗口按 AC-18 同一口径判 PASS/FAIL/NOT_EVALUABLE；AC-24 PASS 当且仅当可评窗口 ≥ 1 且全部 PASS；可评 0 → NOT_EVALUABLE；逐窗列 IoU 原值与 n | `artifact:docs/evidence/P1-ENG-CAPTURE-001-play.md` §3 | PlayK2K4 | |
| AC-25 | Play 机身（USER-4A 第 3 项）：S2 提交时真值水平距离 d₀；d₀ < 10 m → 进带项 NOT_EVALUABLE；N 按 §3.7 公式测前固定（d₀ ≤ 14 m 时 N 取常数项）。**进带**：N 内进入 [10, 14] m；**保持**：进带后至 S4 首次点击前、授权 FOLLOW 的全部帧都在带内。两项都成立为 PASS；另报带内比例、全部越界帧原值与非 FOLLOW 帧数；非 OBSERVED+SUPPORTED 帧无 WRITTEN 速度命令 | `artifact:docs/evidence/P1-ENG-CAPTURE-001-play.md` §4 | PlayK2K4 | |
| AC-26 | 用户目检（Play 中或回看录像）：点击捕获、转向跟住、丢失报告可见；由接受或辅助角色代录进 `docs/unity-test-log.md` | `artifact:docs/unity-test-log.md`（UT-P1-ENG-CAPTURE-001-…） | PlayK2K4 | |
| AC-27 | 人眼保真（workflow §4.3.2）：正式回放运行前，合成滚转管线 ≥ 2 张样帧（含 ω=25 转向中一帧、Θ=120° 保持一帧，叠真值多边形，零推理）；点击页以归档准入帧在保真模式 ≥ 2 张（点击处标记落在所点车上、像素坐标无缩放偏移）；由用户或当轮发令角色确认，样帧路径、确认人、结论入候选证据文件；未完成即 S-A-FIDELITY；不据此申请第二次 Play | `artifact:docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` §保真 | K1K2K3K4 | |

### 4.1 草案验收落点与数值出处（AR1-5）

草案 §5 第一轮验收落点：「点击到绑定 ≤ 1 帧」→ AC-22 端到端（USER-4A 第 2 项保留原目标；「受理后 ≤ 1 帧」只作 AC-12/22 子段）；「离线复现 540–600」→ AC-17（按 USER-4A 只用准入原件，复现门改为现象门）；「≤ 2 帧内由收养恢复」→ AC-6/17（N_adopt=2 时等价）；「3 到 5 帧继续发 look_at、IoU ≥ 0.3」→ AC-9/18/24；「报告无新观测 ≤ 5 帧」→ AC-10/23（T_report = 3）；「机身 N 秒进带并保持」→ AC-25（USER-4A 第 3 项保留 12±2 m）；「红车一圈不丢或窗口内恢复/报告」→ AC-23。

| 数值 | 出处类别 | 用途 | 合同条件 |
|---|---|---|---|
| 5 Hz、640×480、fx=fy=415.692 | 合同/物理（场景与帧元数据） | 全部帧计时、像素单位 | 本场景 |
| e2e ≤ 1 帧；12±2 m 进带并保持 | 用户目标（USER-4A） | AC-22、AC-25 门 | 5 Hz Play |
| T_report 3、N_adopt 2、ρ_click 1.5 | 用户同意的占位设计预算（USER-4A） | §3.7；AC-6/10/12 | 非 R-3 标定 |
| IoU ≥ 0.3（预测 vs 下一观测） | 合同（草案原文） | AC-18/24 门 | 同上 |
| IoU ≥ 0.5（被跟实例是真值车） | 本提案评分口径 | AC-17/18/23 判定 | 离线评分 |
| σ_p = 1/20 | 厂商（ultralytics 8.4.104） | 运动门 S | 未标定 |
| T_pred、T_repair、g_motion、g_size、r_gate_max、m_nis、r_jump | 待标定占位（不作门值来源） | 仅运行参数 | 暂定 |
| 30°/s 视线限速、v_max 4 m/s、`t_lead_s` 2.5 | 合同（现行代码/配置） | C6、N 公式 | 不改 |
| 420 s、290 s、1490 帧、run ≤ 3 | 异条件移植（LOOP-002 运行约束） | 只作运行上限，不作验收线 | — |
| FRAME-001 p50 14.03 / max 22.17 m | 异条件移植（另一候选描述读数） | 只作对照描述，不作门（(h)） | — |

## 5. 预算信封（申请草案；**用户逐字签发前各维度均为 0**；成功、失败、重试共账，耗尽即停）

### 5.1 阶段 A（CAPTURE:A:1）

| 维度 | 上限 |
|---|---|
| 执行机 / 解释器 | Mac mini；`.venv-yoloe/bin/python`（§8.1 读数；不装包；`ENG_DET_DATA_ROOT` 不设）；进程设 `YOLO_OFFLINE=True`、`YOLO_AUTOINSTALL=False` |
| 候选总数 | ≤ 3（首候选 + 至多 2 个返工候选） |
| 停点全套 | 每候选 1 次；每次全套内真实 YOLO 构造 ≤ 2（F12 清单）；整批 ≤ 3 次全套、≤ 6 次构造；每次墙钟 ≤ 30 min |
| 离线回放 YOLO 加载 | 每候选正常 1 + 崩溃重载 1 **共账 ≤ 2**；整批 ≤ 6 |
| 离线回放推理帧 | 每候选 ≤ 5,500（原始 829 × 2 策略 = 1,658 + 合成 2 × 1,152 = 2,304，余量供崩溃重跑，共账）；整批 ≤ 16,500；故障注入 0 推理 |
| 开发期 focused 真实权重加载 | 整批 ≤ 20 |
| 墙钟 / 磁盘 | 每次回放 ≤ 30 min；mini 新增 ≤ 3 GB（`outputs/eng-capture/`，不入仓） |
| scenario / session / run ID | 0 / 0 / 0（会话测试只写临时目录，不写共享 `runtime/`） |
| Unity/Play、板上、VLM/API、云 GPU | 0 |
| 下载 / 安装 | 0（mini 上 lap 0.5.13 来自 RECHARTER 单项下载例外，本信封不继承任何下载例外；数据根缺省规则另按 §8.1） |

### 5.2 阶段 B（CAPTURE:PLAY:1；生效条件 = `K1K2K3K4` 最终有效通过轮被接受角色消费放行 **且** §8.2 Air 预检全部核过）

| 维度 | 上限 |
|---|---|
| 执行机 | MacBook Air（Unity + 会话 + 快层）；分析零模型加载，在 Air 或 mini（局域网拷贝不计下载） |
| Unity Play | 正式 1 次；诊断 Play 0；失败不重试 |
| scenario / session / run ID | 0（复用现有场景配置，不新建）/ 1 / ≤ 3（常驻段 1 + 现行重建上限 2） |
| 会话 YOLO 加载 | ≤ 1（会话缓存，重建复用） |
| 墙钟 | 按钮墙钟 ≤ 420 s；`T_sess` ≤ min(290 s, (1490 − f₀)/5) |
| 磁盘 | Air 新增 ≤ 1 GB |
| 板上、VLM/API、云 GPU、下载/安装 | 0 |

依赖 Air 未核环境的维度在 §8.2 核清前不申请签发（工程轨道 §9 同理，按缺项为 0）。

### 5.3 账本签发格式草案（照 RECHARTER:REPLAY:1 条）

```text
## 2026-10-?? P1-ENG-CAPTURE-001 — 用户签发第一轮阶段 A 额度 CAPTURE:A:1（代录会话：…）
- 用户原话（逐字）："…"
- 授权范围：按 docs/proposals/P1-ENG-CAPTURE-001-moving-target-capture-round1.md §2–§6 实现并取阶段 A 证据；
  不授权 Play、第二/三轮、场景改动、板上动作；STOP 码与处置按提案 §6 表（用户随本条确认）。
- 信封 CAPTURE:A:1（阶段 A，Consuming no，执行机 Mac mini，解释器 .venv-yoloe/bin/python，不装包）：
  - 候选 ≤ 3；停点全套每候选 1 次（整批 ≤ 3），每次全套真实 YOLO 构造 ≤ 2（整批 ≤ 6），每次 ≤ 30 min
  - 离线回放每候选 YOLO 加载正常 1 + 崩溃重载 1 共账 ≤ 2（整批 ≤ 6）；推理帧每候选 ≤ 5,500 共账（整批 ≤ 16,500）
    （outputs/eng-det/runs/run-1/weights/last.pt，sha256 d6a0d6a9…）
  - 开发期 focused 真实权重加载整批 ≤ 20；故障注入 0 推理
  - scenario/session/run ID = 0/0/0；Unity/Play = 0；板上 = 0；VLM/API = 0；云 GPU = 0；下载/安装 = 0
  - 每次回放墙钟 ≤ 30 min；mini 新增磁盘 ≤ 3 GB（outputs/eng-capture/，不入仓）
- 越界任一维即停，报回用户；剩余额度不转用。
```

CAPTURE:PLAY:1 用同一格式另条签发，逐字含 §5.2 各维与生效条件；不与 A 同条。

## 6. 限制、不承诺与停止规则

- **主张上限**：只说明本仿真、5 Hz、现行检测器与 BoT-SORT 冻结参数、本组占位参数下的工程行为。不声称误收养率（USER-4A：第一轮有限口径；R-3 未做）、不声称参数最优、不声称板上性能。Play 只有 1 次，结果是单次读数，不是统计结论。
- **已知偏差**：KF 快照回放与新捕获 belief 回放延后（A9），修复提交后丢掉 N_adopt−1 个证据帧的量测；兼容模式的语言旧收养规则未改；`vlm_busy` 列延后；按图像滚转率限速延后；机身估计器量测点不改；AC-17 复现门因准入范围改为现象门。
- **输入性质（USER-4A 第 1 项）**：AC-17/18/19 只用准入原件（原始帧、位姿、真值）作本项新离线回归夹具，以新代码、新日志独立取证；RECHARTER:REPLAY:1 的导出、读数与 10-08 Play 结论仍为诊断，不进本项证据链、不追认任何旧门；workflow §4.3.2 对其他诊断产物不变。
- **对 `P1-ENG-LOOP-002` 的影响**：本项改动其通过候选覆盖的文件；其 verdict 只绑定它自己的通过候选，本项不改其门、不回写其复核、不向其提案追加内容。

**STOP 表**（交用户随信封确认；停止不等于读数通过，已停步骤的 AC 记 `NOT_RUN` 或 FAIL，不补跑、不以部分读数宣称通过）：

| 码 | 触发 | 停止的后续 | 仍可执行（零消耗安全收尾） |
|---|---|---|---|
| S-A-BUDGET | 阶段 A 任一维将越界 | 该维相关的一切后续消耗 | 写证据与交接；回用户 |
| S-A-INPUT | 准入文件 sha、帧旁车与真值 `frame_id`/`simulation_time_s` 不符 | 本候选全部回放（AC-17/18/19 `NOT_RUN`） | 全套与零模型测试；回用户 |
| S-A-FIDELITY | AC-27 未确认或不一致 | 正式回放运行 | 修管线后重做保真（零消耗） |
| S-A-REPRO | 基线臂现象门不过 | 新臂评分与 AC-17/18/19 读数作废 | 写证据；回接受角色与用户 |
| S-A-CRASH | 回放第 2 次崩溃（共账用尽） | 本候选回放，不第 3 次加载 | 保存已得缓存与日志 |
| S-A-LOADER | 全套真实构造超出 F12 清单 | 本次全套不重跑，AC-20 `NOT_RUN` | 报回用户裁定 |
| S-B-PRE | Air 预检、HEAD/porcelain、覆盖文件 sha 任一不符 | 不进 Play（无消耗） | 回用户 |
| S-B-UNITY | Unity 未进 Play | 本次 Play（计已用，不重试） | 停会话、归档、哈希清单、零模型分析 |
| S-B-TERM | 会话 TERMINAL 于非 `operator_stop`/`duration_reached` | 剩余剧本 | 同上 |
| S-B-WALL | 按钮墙钟到 420 s 仍未静止 | 剩余剧本 | 同上 |
| S-B-UNSAFE | 非 OBSERVED+SUPPORTED 帧出现 WRITTEN 速度命令 | 操作者立即按「停止会话」，剩余剧本 | 同上；AC-25 记 FAIL |
| S-B-BUDGET | 阶段 B 任一维将越界 | 该维相关的一切后续 | 同上 |

## 7. 必经停点与提请接受裁定

- **停点 1 `K1K2K3K4`**（按 (b) 合并，先于唯一一次 Play）：K1 点击协议、补偿坐标语义、帧计截止、状态原因闭集；K2 预测 look_at 与授权函数；K3 目标管理器、收养、resolve/commit；K4 回放与 Play 评分口径。AC-1…AC-21、AC-27 在此自证，`docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` 按 AC 逐条附指针 → 核对轮 → 新鲜上下文复核。Play 放行取该停点**最终有效通过轮**（不锁 R1），并经接受角色按 workflow §4.5 消费放行；签额不跳过本停点。
- **停点 2 `PlayK2K4`**：AC-22…AC-26 另过核对与复核。`DONE` 需实现者证据、独立复核与用户 Unity 目检三样齐全；不申请 `UNITY_NA`。
- **D1 (a)–(h) 落实**：(a) 申请保留，待本轮裁定；(b) §7 上条；(c) 按 USER-4A 落实（§6、AC-17）；(d) §2.5 R1-5 行；(e) C1/C2；(f) 不向 LOOP-002 追加（§2.5）；(g) 兼容模式 + §3.5；(h) 按 USER-4A 保留 12±2 m（AC-25）。
- **D2 新提请**：(i) 兼容模式保持语言路径全部现行行为（含 per_class+pose-aabb），新行为只在 `--language off`，是否可接受；(j) 点击页进程内 `send_request` 替代 CLI 子进程，及 `operator_web.py` 两处 diff 闭集；(k) 基线臂用接受提交上的 `controller/` 导出 + 缓存检测，复现门改为现象门（因准入不含旧会话日志）；(l) T_pred 占位 5→4（AR1-1 结构约束）；(m) §6 STOP 表措辞是否足以交用户确认。

## 8. 只读试读（Mac mini，D2 本会话；零消耗）

### 8.1 mini 已核

- 解释器 `.venv-yoloe/bin/python` = Python 3.12.14；`importlib.metadata` 只读：ultralytics 8.4.104、torch 2.13.0、opencv-python 5.0.0.93、lap 0.5.13、numpy 2.5.3。系统 `python3` = 3.9.6，不用于全套与回放。
- 权重 `outputs/eng-det/runs/run-1/weights/last.pt` 5,458,330 B，sha256 前缀 d6a0d6a9cdee06a0，与 `config/det-assoc-v1.models.json` 一致。
- 准入输入根 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261008T213653Z/`（40 MB）：`play/diag-loop2-214005/frames/` 829 jpg + 829 json；`m3_body_truth.jsonl` 829 行；`replay-transfer/SHA256SUMS` 1,669 行（完整性参照）。
- 数据根：`ENG_DET_DATA_ROOT` 未设，缺省 `~/TetheredDroneTracking-full` 存在（含 scout-1 帧目录），故 F12 两处真实构造可能不 skip，按 ≤ 2 申请。
- 现成入口：会话 `python -m controller.language_loop run|<动作>`（`--resident`、`--ground-plane-y-m` 等已有）；`tools/eng_capture/` 不存在（新建）；RECHARTER 回放脚本不入仓、不复用。mini 磁盘可用约 118 GiB。

### 8.2 Air 未核（阶段 B 签发前置；mini 上不可见，不臆测）

Air 上只读核清并留原始读数：`git rev-parse HEAD` 与 `git status --porcelain`；`.venv-yoloe/bin/python --version` 与 ultralytics/torch/lap/numpy 版本（须与 §8.1 一致或逐项说明）；权重 sha256；可用磁盘 ≥ 1 GB；Unity 6000.4.1f1 能打开工程；`runtime/scenario_config.json` 覆盖文件可生成；点击页端口空闲；Air→mini 局域网拷贝路径可用。另有未核假设：会话 tick 间隔 ≤ 1 帧（AC-22 e2e 前提，K1 证据实测）、`send_request` 进程内往返时延。

## 9. 待用户

**已答，不再询问**（账本为准）：USER-4A 四项（诊断原件限用途准入；点击到绑定 ≤ 1 帧端到端；12±2 m 进带并保持；第一轮有限口径与 N_adopt=2 / T_report=3 / ρ_click=1.5 占位）；机器分工（mini 回放/全套，Air 承载 Unity 与会话）；`P1-ENG-LOOP-002` 保持暂停、本项不代答其题。

| 题 | 内容 | 推荐 | 为何只能用户定 |
|---|---|---|---|
| U-1 | 签发阶段 A 信封 CAPTURE:A:1（§5.1、§5.3） | 待接受角色对 D2 裁定 `ACCEPTED` 后按 §5.1 签；缺此信封停点全套与回放无法运行（工程轨道 §6） | 信封只能由用户签发入账 |
| U-2 | 签发 CAPTURE:PLAY:1（§5.2） | 等 `K1K2K3K4` 最终有效通过轮被消费放行、§8.2 预检核清后再签；不增加重试 | Play 是不可重跑的消耗性资源 |
| U-3 | Air 只读预检（§8.2）的执行时机与执行者 | 阶段 B 准备时由用户或 Air 上的会话执行，零消耗，读数入操作单 | Air 是用户设备，动用时机属用户的机器分工 |
| U-4 | §6 STOP 表与「仍可执行」列 | 随 U-1/U-2 信封一并确认 | 停止后哪些收尾可继续涉及额度处置，按 AR1-6 交用户 |

## 10. D2 回应表（AR1-1…7）

| AR | 改在哪 | 完成条件如何满足 |
|---|---|---|
| AR1-1 | §3.3 结构约束、到期规则、同帧顺序、边界逐列表；§3.4 行 7；§3.6；§3.7 T_pred 5→4；AC-6/9/10/18/24 | 到期取 age ≥ T_repair 先到、修复提交严格 ≤ T_repair−1；T_pred ≤ T_repair−1 使预测与撤权永不同帧；逐列给 T_report/T_pred/T_repair 前、当、后结果；预测测试只在行 7 全条件成立时要求 look_at，并对提前恢复/DISPUTED/几何/协方差/kf 无效各列反例 |
| AR1-2 | §3.1 只读 KF 快照、S 组成、内外分开；§3.8 `tm_inputs.jsonl`；AC-3/8/15 | 在线接口 = `step` 后复制库 KF（phase、单位、F13 同帧阶段、非有限/非 PSD 退化）；S = 库位置协方差 + 厂商像面噪声（明列未标定，不用 R-4）；未裁剪预测与 `out_of_frame` 只在内部，桥文件有用例拦截；日志落盘输入原文、版本与三种时间，AC-15 从落盘输入重放；AC-8 列具体轴值、年龄分带与偏序 |
| AR1-2 附 | KF 快照全量回放 | 仍延后（§2.2、§6），未扩成地面滤波重写 |
| AR1-3 | §2.1 两种模式；§3.2 TaskSpec 投影与 origin；§3.3 证据单位与可提交库键；§3.5 路径表、原子提交与回滚、`follow` 闭集；AC-4/7/12/13 | INITIAL/USER_RESELECT/CONTINUITY_REPAIR/语言两条兼容路径分别定准入、投影、coasting 与副作用；原始检测只作诊断、未确认帧只作证据、提交须已激活；点击逐帧证据链；语言旧收养只在兼容路径；清指针路径与转发例外枚举；被拒/异常全状态不变、成功后才关旧 episode；补语言/coasting、拒绝重选保留旧目标、半改后抛异常用例 |
| AR1-4 | §2.5 `operator_web.py` 两处 diff 闭集；§3.5 点击页 `InProcessSend`/`ClickArgv`；AC-14/16；AC-17 基线源导出 + `baseline_runner.py`；AC-19 评分口径；AC-27 保真 | 新 click 提交所在文件与最小 diff 写清，原「除记录路径外零 diff」改为恰两处；既有动作 argv 逐字节不变；旧臂在导出的旧代码上运行、不复用新管理器；合成真值映射、删失、断轨与每格分母冻结，RECHARTER 3D 投影等偏差不继承；合成与点击呈现各 ≥ 2 张保真样帧先于正式运行；不据此申请第二次 Play；准入按 USER-4A |
| AR1-5 | AC-22（端到端 + 子段、失败计分母）；AC-17/18/23/24/25 判定；§4.1 出处表 | 按 USER-4A 保留原目标，受理后 ≤ 1 只作子合同；每条数值列四类出处与合同条件（5 Hz/640×480）；PASS/FAIL/NOT_EVALUABLE 与缺观测分母写明，无下一观测不判通过；AC-25 按用户保留 12±2 m 进带并保持，另报带内比例与越界原值；FRAME-001 读数只作描述 |
| AR1-6 | §5.1–5.3 信封；§6 STOP 表；§8.1/8.2；F12 | 每候选正常/崩溃共账、候选 ≤ 3 与整批封顶、真实 loader 只读清单；scenario/session/run 各维入草案；解释器/数据根/权重/入口 mini 已核，下载例外不继承；Air 未核项列为阶段 B 前置、依赖其的维度暂不申请；12 个具名 STOP 码各写停什么与可继续的零消耗收尾，交用户随信封确认（U-4） |
| AR1-7 | §6 输入性质；§3.7 类别列；§9 | 诊断原件准入与设计预算均已由 USER-4A 答复并逐字落实（不由构思/接受角色解除常设限制）；N_adopt=2 标为用户占位、非 R-3 标定；剩余 U-1…U-4 带推荐与理由，不重问已答项 |

## Contract conformance（核对表）

### 诊断核读与ENDED（2026-10-10，Acceptance）

owner=Acceptance；范围仅为诊断报告的范围/资源/解释边界核读与 ENDED 文档迁移，状态为本轮收尾完成。依据账本 2026-10-10「用户定后续范围」「用户签发离线诊断额度 CAPTURE:DIAG:1，并同意本项旧 Log 叙述移入 status-history」、本提案「收口与诊断落实」§1–3、「诊断信封落实」§1–3。后两节原“未执行/待搬移/ACTIVE”保留为当轮快照，由本节承接现状。本轮不是 C/R 轮，不签新 verdict、AC 证据、验收 PASS、DONE 或 UNITY_NA；未运行诊断、测试、模型、Unity/Play、评分或重放，不改报告、原件、授权账本或 status-history。

#### 1. 诊断合同核读与解释上限

核读对象为 `docs/evidence/P1-ENG-CAPTURE-001-offline-diagnosis.md` 全文及 `docs/evidence/supervisor-dispatch.jsonl` 中本项「离线诊断」的 finished.report；原输入入口沿 play.md §0、formal-play.md §0、formal-redo.md §0–1。只核报告及既有记录，不重复运行流式哈希/诊断或展开新的原件分析。

| 核读项 | 结论与边界 |
|---|---|
| 输入闭集 | 报告 §1–3 所用三组 Air 已保全 play/formal/formal-redo 日志、非真值旁车、原 RGB、配置/启动/清单及仓内源码属于合同 §2；第二 Play 仅背景。身份按入口运行时解析，报告未新建 ID。报告逐件哈希只证明保全一致；重做缺失/冲突/可对应分列，不把关键时刻可对应扩成正式源完整。 |
| 真值 / 禁止闭集 | 报告 §1/§8 声明真值仅流式字节身份、未解析内容；分析限时间差、日志计数、有限三张原图及源码文本。禁止闭集逐项有未执行声明；未见报告披露模型/测试/Play/评分/reducer/KF/跟踪器运行、导入生产包、原件改写/复制/导帧、其他设备或传输。此为报告范围核读，不冒称独立执行审计或新行为证据。 |
| 已证时序与解释 | §2/§4 的第 647 帧发布拒绝→撤权→重建后无绑定/HOLD，作为日志时序及原图支持的诊断解释保留。用户“第一个拐角”的精确帧与物理身份仍 UNKNOWN；报告“不是检测丢失”“排除感知丢失”只读作该段日志未记录感知丢失、撤权先于原图转弯，不推广为检测器无缺陷或所有丢失均由此导致。 |
| 假设 / 计数限制 | §4 E3 为可支持解释，E4/E5 的争用、监控及重建变慢根因未定案，不能把同现当因果。§3 逐行表含第二 Play 2 行、formal 3 行、重做 2 行，与段末/E3 的“6 次”汇总未一致；本轮不采该总数、不改原报告，也不为此续分析。逐行时序不由汇总计数替代。 |
| 建议去向 | §6 的发布失败降级、自动重捕、门值重核、监控与耗时日志五项只交未来快层修正的构思/接受角色作输入，未接受为新合同。涉及 K1/K2/K3、指标或采集改动时由后续获批工作项设相称停点与独立复核；不反调本项参数/帧集/判据，不解除 AC-23…26 缺项，不产生研究或板端主张。 |

#### 2. CAPTURE:DIAG:1 实耗核读（不追认完整符合）

一次诊断已用 1/1，完成与证据不足均不返还。报告 §7 的提交前墙钟 313 s 与 finished.report 的推送后约 332 s 分列；按后者核已报告共账值低于 1,800 s。另保留起点一致性缺口：§7 起始 UTC 文本为 21:44:48Z，但所列 unix 对应 21:44:42Z，差 6 s；文本至推送完成 21:50:14Z 为 326 s，约 332 s 对应 unix 起点。两种现有读法均低于上限，不据此签精确起点/全流程时钟一致或重填原数字。

报告 §7 与 finished.report 的可观测可归属新增分配块保守峰值约 2.9 MB，低于 100,000,000 B；计入报告、transcript/meta/tool-results、git 对象预留、状态板瞬时改写及临时余量，不按 df/净增计、不将删除返还。`~/.claude` 外客户端日志/缓存仍 UNKNOWN，完整客户端峰值未证；新 UNKNOWN 的发现与停止分析时刻未给可配对记录，不能签“新 UNKNOWN 即停”流程全部符合。旧历史 UNKNOWN 例外不继承，未知不补零、不凭观测部分推完整余额。本轮接受已停止的一次诊断报告及限制，按「诊断信封落实」§3(3) 将缺口随收尾保留，不追认完整资源或执行合同符合，不续诊断/追加计量或额度。CAPTURE:DIAG:1 未用墙钟/磁盘余额随此收尾作废、不转用。

#### 3. ENDED 迁移与承接

chore 已完成本项旧 Log 45 条/180 行整段搬移（来源为派发日志本项「Log搬移」finished.report），状态板汇总条保持原文；history 不作为门值、义务或证据来源。本轮依既定顺序完成诊断核读后，置 Lifecycle=`ENDED`，完整 Gate 行仅改 Lifecycle 后整行迁入 `docs/parked-status.md`「已终止（ENDED）」表，移除本项 Active handoffs；Overall 保持 `CLOSED_DESCRIPTIVE_RESULT_WITH_KNOWN_FAILURES`。Current state 留一行结论/指针，Immediate next actions 同步活跃数量与入口，不搬回旧 Log、不扩大搬移或处理其他项。

本项停点与保留义务事实源为 `docs/parked-status.md`「P1-ENG-CAPTURE-001 收口与保留义务（2026-10-10）」；承接「收口与诊断落实」§1 的完整义务及本节新增核读限制。阶段 A 原通过消费与候选 2 回放仅按原范围保留；正式结果 FAILED_INCOMPLETE、R1-4/R2-2 OPEN、旧失败/超时/UNKNOWN/晚停/源混存、原件留 Air 和暂停项不变。原实现/验收范围不恢复，PlayK2K4 自证仍未齐，不补成功停点。下一 Owner=用户（仅另定后续工作项范围/逐维信封时；无已签执行动作），本项不再挂活跃交接。

needs_user：无（诊断与 Log 收尾授权已足；解释/资源缺口允许照记后终止，无需为本项续诊断或追认）。consumed={}（本轮不消耗执行信封；上节为既有诊断实耗核读）。

open_items: R1-4, R2-2, PLAY-AC23-26, RESOURCE-UNKNOWN, B-WALL-OVERRUN, FORMAL-REDO-SOURCE, FORMAL-REDO-LATE-STOP, DIAG-TIME-ORIGIN, DIAG-COUNT-SUMMARY, DIAG-UNKNOWN-STOP

### 诊断信封落实（2026-10-10，Acceptance）

owner=Acceptance；范围为 CAPTURE:DIAG:1 逐维落实与后续文档收尾交接；状态为已签资源落实、诊断未执行。唯一授权来源为 `docs/authorizations.md` 2026-10-10「P1-ENG-CAPTURE-001 — 用户签发离线诊断额度 CAPTURE:DIAG:1，并同意本项旧 Log 叙述移入 status-history（supervisor 会话代录）」。本节只转写该条已签边界，不追加额度、不代写用户原话；下方「收口与诊断落实」§2/§3 的“资源未签／暂不执行／Log 待同意”是签发前快照，其资源效力与下一 Owner 由本节承接，原文保留。

#### 1. CAPTURE:DIAG:1 逐维核对与生效边界

账本选定项、授权范围与「收口与诊断落实」§2/§3 逐项一致；CAPTURE-DIAG-WALL、CAPTURE-DIAG-AIR-DISK 均已签。**交 Air Implementation 的唯一诊断合同仍为「收口与诊断落实」§2**；本节只落实资源和接力，不另立分析合同、不恢复原实现/验收范围。

| 维度 | 已签效力与执行边界 |
|---|---|
| 设备 / 执行者 / 次数 | 仅 MacBook Air / Air Implementation，一次只读离线诊断；失败、到限或证据不足也占这一次，不重试、不借旧信封余额重开。 |
| 输入 / 分析 / 产出 | 严格按原 §2 的三组 Air 已保全输入闭集、真值字节身份口径、禁止闭集及中文诊断报告执行；不语义读真值、不跑评分/reducer/KF/跟踪器。报告建议路径仍为 `docs/evidence/P1-ENG-CAPTURE-001-offline-diagnosis.md`，注明“诊断，不进验收证据”。 |
| 共账墙钟 | ≤ 1,800 s（30 分钟），从诊断执行准备起至资源记录、机检、报告提交推送结束；全部准备/只读核对/有限原图查看/报告/收尾同账，失败照计。建议预留最后 300 s 收尾，余量不足即停止深入分析；无到点后的提交宽限。 |
| Air 新增磁盘峰值 | ≤ 100,000,000 B（100 MB，非 MiB）；含报告/短记录及本次可归属客户端日志、缓存、暂存、git 与收尾。原 §3 的报告目标 ≤10 MB、附属预留 ≤90 MB 仍仅为同一总额内的安排，不能相加扩额。不复制原件、不导帧。 |
| 计量 / 余额 | Implementation 执行前现场记录新基线、计量方法及产出/收尾预留，计可归属新增分配块与峰值并查重；删除不返还历史峰值，不以 df/净增替代峰值。未发生用量不预填 0；新用量/峰值不可核即停报 UNKNOWN，不继承旧历史 UNKNOWN 例外或据旧快照推新余额。 |
| Unity/Play / 模型与推理 | Unity/Play=否（0，含诊断 Play）；模型加载/推理=0，不运行测试或可能启动模型的生产入口。 |
| scenario/session/run ID / API / GPU | 0/0/0；API=0，GPU=0，不创建或消耗正式 ID，不云端或板端执行。 |
| 下载 / 安装 / 原件传输 / 其他设备 | 全部 0；不装包、不传输原件、不动 mini/Jetson/其他设备；缺项视为 0。 |

墙钟与磁盘各自封顶，不相互抵偿、不转用原 A/B 剩余或下一轮额度。本轮仅文档落实，未启动诊断准备计量或诊断次数，不把本轮检查写成诊断实耗/报告核清。

#### 2. STOP 与到限处置

用户已随本条确认原 §3 的停止边界：**到限/将越界、输入漂移/哈希不符、新 UNKNOWN 或出现任何禁止操作需求，即结束分析**；仅在已留且仍可核的墙钟/磁盘余量内记报告、实际用量、停止原因和限制，交回 Acceptance；需追加资源或扩范围时回用户，不自动扩大、不重试。收尾也在 1,800 s/100,000,000 B 内，不以安全收尾或提交推送另获宽限；实际超限/计量失败如实记偏差，不能补零或追认符合。

定位不到根因，或混存/缺记录不能配对，就在同一次内提交“不确定/证据不足”；已有混存及旧 UNKNOWN 作为原 §2 的已知输入限制保留，不由其推断新计量符合。新输入异常/新 UNKNOWN 仍立即停，不筛最佳段补正式结果、不临场扩读真值或运行评分。报告建议仅作下一轮修正输入，原失败、AC-23…26 缺项、R1-4/R2-2 OPEN 和全部旧资源偏差仍按「收口与诊断落实」§1 保留。

#### 3. CAPTURE-LOG-SINK 已获同意与后续顺序（本轮不执行）

CAPTURE-LOG-SINK 已获上述账本用户同意：仅本 work item、仅此一次，将本项旧 Log 叙述整段移入 `docs/status-history.md`，保留原标题/原文，移动而非复制，状态板保留结论/权威指针；history 不是事实源，不作为义务或证据来源。仅 chore 有该文件写权，本轮 Acceptance 不搬 Log、不写 history/parked，不置 ENDED。

后续按本次交接指定顺序，保持单写者接力：

1. **Air Implementation 执行一次诊断**：按原 §2 与本节已签边界交报告及实际资源/限制，提交推送后停止；完成或 STOP 均不得自行续诊断、改代码/参数、Play 或签验收。
2. **chore 搬移本项旧 Log**：引用上述一次用户同意，只整理本项旧叙述，结论/限定语/负结果/未闭义务留在摘要或明确权威指针；不动其他工作项或本批新条目，不改门值/Lifecycle。此顺序依据本项用户直接授权及本轮交接，限定本项旧 Log 搬移，不推广为对其他 ACTIVE 项的整理许可；按 chore 细则核对并运行自检。状态板交接仍为唯一接手动作入口。
3. **Acceptance 只读核清并收尾迁移**：重读诊断报告、实际资源及限制，只核范围/资源/解释边界，不跑诊断/测试/评分，不产新 verdict/AC 证据。核清诊断或 STOP 报告及 chore 整理后，在同一收尾提交置 Lifecycle=`ENDED`、把完整 Gate 行迁入 `docs/parked-status.md`「已终止（ENDED）」并写保留义务节，Overall 仍为 `CLOSED_DESCRIPTIVE_RESULT_WITH_KNOWN_FAILURES`；同批核 Log 可压池上限和文档自检。解释/资源缺口照记，不因迁移追认符合或销债；需额外动作只列 needs_user，不扩大原信封。

诊断先于 Log 搬移，可让 chore 一次整理已形成的诊断交接叙述，避免先迁 ENDED 后仍留执行交接。Log 整理先于接受侧迁移，可防 ENDED 移行使旧 Log 失去保护后再超可压池上限；不改 300 行上限。收尾保留义务承接原 §1 全表，并补诊断报告与资源实际/UNKNOWN/解释限制的权威指针；不以 history 承载权威门值、未闭义务或正式证据。

当前 Owner=Air Implementation，Status=`READY_AIR_OFFLINE_DIAG`，Return to=Acceptance。Consuming=no：AGENTS 判据是 scenario/session/run ID、Play 配额或 API 预算，此诊断三类均为 0；墙钟/磁盘已签不改变该列判据。Overall/Lifecycle 保持描述性关闭/ACTIVE，仅留诊断与迁移承接，不签 verdict/DONE/UNITY_NA。needs_user：无（本轮授权无歧义，三项已答不重问）；consumed={}（本轮未执行诊断）。

open_items: R1-4, R2-2, PLAY-AC23-26, RESOURCE-UNKNOWN, B-WALL-OVERRUN, FORMAL-REDO-SOURCE, FORMAL-REDO-LATE-STOP, CAPTURE-DIAG-REPORT, CAPTURE-LOG-MOVE, CAPTURE-ENDED-MIGRATION

### 收口与诊断落实（2026-10-10，Acceptance）

owner=Acceptance；范围仅为用户已选描述性收口、未闭义务承接及一次离线诊断合同准备。唯一授权来源为 `docs/authorizations.md` 2026-10-10「P1-ENG-CAPTURE-001 — 用户定后续范围：本轮按描述性结果收口，并做一次零消耗离线诊断查拐角丢失（supervisor 会话代录；不追加额度）」；用户体感来源为 `docs/unity-test-log.md` FORMAL2「用户阶段 B 总评」。本节承接下方旧“后续范围待定／REVIEW_PASSED/ACTIVE”快照；不改原 AC、阈值、STOP、原件或复核文件，不开 C/R，不签独立 verdict、验收 PASS、DONE 或 UNITY_NA。本轮未运行 Unity/Play、模型、测试、评分或重放，不写授权账本、runtime/、outputs/。

#### 1. 描述性收口裁定

依用户选择及 engineering-workflow §11、collaboration-workflow §3/§4.6，本项原实现与正式验收范围停止：Overall = `CLOSED_DESCRIPTIVE_RESULT_WITH_KNOWN_FAILURES`。这属于终止处置，不是新的通过态，不产生跟踪优越性、参数标定、统计风险界或板端/研究主张。用户已明确选择“收口”，不重问该决定；但本轮尝试 Lifecycle=`ENDED` 并移行后，check_docs.py 实报 Log 可压池 467 行 > 300 行。AGENTS「共享状态更新」及 workflow §6 要求移出的旧叙述经用户按 work item 同意后整段移入 status-history；本轮无此授权、也不得删减他人未沉淀内容。因此不擅自迁移，Lifecycle 暂留 `ACTIVE`，仅承载诊断资源签发与收尾迁移待决，ENDED/parked 移行延至 §3 的 CAPTURE-LOG-SINK 获准并完成合规整理后同批落实。原代码/验收范围已停止，不因保留 ACTIVE 恢复。一次诊断是收口留下的分析义务，报告不进本项验收证据；保留义务唯一详表在下文，不先复制到 parked。

| 结果 | 本次收口读法 | 直接来源与限制 |
|---|---|---|
| 点击切换 | 按用户选择记为达成的描述性结果 | FORMAL2 体感 + formal-redo.md §1 局部 AC-22：4/4 绑定，e2e 原值 [0,0,−1,0]，受理子段均 0；未独立复核，不称负物理时延、不签 AC/Unity PASS。第二 Play 12 点击/11 绑定与第三 Play 5 点击/4 绑定、AC-22 FAIL 原样并列，不概括为历次全部通过。 |
| 跟随连续性 | 已知失败 | formal-play.md §0 的 publish_expired/catchup_stale 两次重建及 rebuild_limit 提前终止；formal-redo.md §0–2 的过期重建、用户第一个拐角丢失。一圈跟随与换回段未实证，不预断两类现象的因果关系。 |
| AC-23…26 | 正式验收缺项保留 | AC-23/24/25 为 NOT_RUN(SOURCE_PROVENANCE_UNRESOLVED)，第二 Play 的 EVIDENCE_MISSING 及第三 Play 剧本/身份缺项不改；AC-26 仅部分体感/捆绑回复，转向跟住及丢失报告逐项目检未齐。正式结果仍 FAILED_INCOMPLETE。 |

阶段 A `K1K2K3K4` 通过消费、原核对/复核及候选 2 回放读数按其原范围保留；全套既有失败与合同预期失败不改称全绿。`PlayK2K4` 稳定自证未齐，不补开成功停点。原信封停止使用，剩余额度不转给诊断或下一轮；失败/误触不返还次数。最终资源只沿 formal-redo.md §3 指向的 `outputs/eng-capture/formal-redo/control/execution-close.json` 读取，本轮仅只读核该机器封口已存在，未新增计量或据检查点推最终完整符合。

| 保留义务 | 承接去向与边界 |
|---|---|
| R1-4、R2-2 SCOPE_GAP/OPEN | 唯一债入口仍为 `docs/implementation-status.md`「范围外已知缺陷」本项两行；不修、不关、不写 release。未来扩大账本输入域/复用启动门前承接全维上限拒绝回归；扩大重放输入域/人工编辑或声称任意删行可检出前承接链式完整性/帧连续性拒绝回归，由后续获批合同及独立复核负责。 |
| 连续性失败、AC-23…26 缺项 | 本节 §2 仅查原因，报告交下一轮快层修正的构思/接受角色；修代码、再次 Play 或正式验收必须另定范围与逐维信封。旧缺项不会因诊断“查明”而闭合。 |
| 旧失败/超时/执行偏差及 UNKNOWN | 第二 Play 单 attempt 超时、后封口/客户端附属峰值未知；阶段 A 旧资源核账偏差/UNKNOWN；第三 Play 身份不一致与提前停止；第四 Play 晚停、源混存、额外误触启动类别/次数及采样峰值限制，均保持。源见第二Play核清、正式提前终止与正式重做核清节及各原证据；后续引用必须携带限制，无追认、补零、删样本或余额抵偿。 |
| 原件保全/共享槽位 | 三组原件及哈希清单留 Air，无删除/移动/覆盖许可；下一获批采集者先独立核槽位与源归属，诊断不腾槽、不回填正式真值、不把混合源拼成完整正式源。LOOP-002/ACQ 暂停、其他旧债及延期研究门不动。 |

#### 2. 一次零消耗离线诊断合同（资源未签，暂不执行）

**目的/次数/责任：** 交 MacBook Air Implementation，一次只读分析，查正式重做红车第一个拐角丢失，以及正式测评/重做中 publish_expired、catchup_stale 触发驻留重建的原因。可对第二 Play 同类现象作背景对照，不能扩成新实验。用户已选诊断方向与 Air 原件输入，未签的墙钟/新增磁盘维度仍为 0；目前不得派发执行诊断。

**输入闭集：** 只读 Air 已保全的 `outputs/eng-capture/play/`、`outputs/eng-capture/formal/`、`outputs/eng-capture/formal-redo/`，包括既有控制/点击/会话/驻留历史、tm_inputs、帧图像/非真值旁车、配置与启动记录、原哈希清单。入口见 play.md §0、formal-play.md §0、formal-redo.md §0–1；可读本仓代码/配置及上述证据。session、run 路径/候选/工件身份从 launch、manifest、同名复核机读行及 git 现场解析，报告只写来源指针，不手抄派生 SHA/目录名。只在此闭集内核来源及逐件哈希，异常照报、不修原件、不扩大盘点到旧保全目录、其他设备或共享 runtime。formal-redo 的混合源只作诊断，按 capture 时刻/帧号/日志对应分别标可对应、冲突、缺失或 UNKNOWN；哈希一致只证保全一致，不能证明单轮正式源完整，不筛出“最佳段”冒充整轮。

**分析与真值口径：** 默认且本合同无需语义读取真值。按既有日志形成点击绑定→最后可靠观测→未匹配/运动尺寸门/竞争/几何或 KF 退化→预测/报告/撤权→驻留终止/重建的时序，区分 sensor frame_id、simulation_time、capture 与处理/发布墙钟及 valid_until；只按存量数据重算简单时间差/日志计数，不跑 reducer、KF、跟踪器或模型。结合原 RGB 与非真值旁车定位用户拐角现象，身份或首丢失时刻不能对应时明确不确定；分别核 publish_expired/catchup_stale 的代码触发条件、积压/处理时延/发布年龄与重建前后记录，区分日志已证原因、可支持解释和待验证假设，不把同现当因果。真值文件只允许作为既有保全清单的字节身份对象，不解析其内容、不从真值生成选择点/轨迹键/感知或控制输入。项目红线仍为真值只能进入离线评估/诊断分析，永不进入控制器/感知器；若没有真值就无法区分遮挡与身份丢失，本次报告证据不足，额外真值语义分析须先明确只读分析口径交接受角色/用户另定，不临场扩读或启动 score_。

**禁止闭集：** 不加载/推理任何模型，不 Unity/Play（含诊断 Play），不创建/消耗 scenario/session/run ID，不 API/云/板端/其他设备，不下载安装或传输原件；不改代码/配置/测试，不运行测试、正式评分、analyze_play.main/score_*、replay 或执行导入后可能启动模型的生产入口；不改动原件/原清单、runtime/、outputs/，不复制整份原日志/图像到临时目录，不全量导帧/生成录像/新缓存。可用系统已有标准库作只读流式解析，不导入 controller 或模型包，不保存可复用新分析工具；内存中比较既有记录，输出限下述报告及必要的短资源记录。

**产出/结束条件：** 建议唯一报告 `docs/evidence/P1-ENG-CAPTURE-001-offline-diagnosis.md`，中文、标题注明“诊断，不进验收证据”。报告列输入来源/哈希核对及混存限制、两类现象分开的事件时间线、各解释的支持/反证指针、无法核定项、下一轮最小修正建议及需新验证项；另记实际墙钟、Air 新增磁盘峰值/计量方法与 UNKNOWN，原失败/OPEN 债和禁止动作未执行声明。定位不到原因也在同一次内交“不确定/证据不足”，不得自行重试、修代码或加实验。完成后交 Acceptance 只读核范围/资源/解释边界，不产本项新 verdict/AC 证据；建议仅为下一轮输入，不能反调本项冻结参数/帧集/判据。

#### 3. needs_user：诊断新增资源维度（推荐，未生效）

依据 engineering-workflow §8/AGENTS「缺项视为 0」，上述账本只选诊断方向、未给墙钟/磁盘数字；这两项必须由用户在发生授权的会话逐字签发入账，不由接受角色或 supervisor 代拍。无需再问是否收口或是否想诊断，也不追加旧 Play 信封；下列为仅此一次诊断的新维度申请。

| needs_user | 推荐上限与理由 | 生效/停止边界 |
|---|---|---|
| CAPTURE-DIAG-WALL | 一次共账墙钟 ≤ 1,800 s（30 分钟）；三组既有日志的流式核对/读码/有限原图查看、报告及收尾留出保守窗口，未做试跑、不承诺此内查明根因 | 用户签发前 0。从诊断执行准备开始至资源记录/机检/证据提交推送结束全区间计时，失败也占一次；建议至少预留最后 300 s 作报告/收尾，余量不足停止深入分析，按已得事实交接，不隐含宽限/重开。 |
| CAPTURE-DIAG-AIR-DISK | Air 新增峰值 ≤ 100,000,000 B（100 MB，非 MiB）；报告和短记录目标 ≤ 10 MB，另留 ≤ 90 MB 给本次可归属客户端日志/缓存/暂存/git 与收尾，不复制原件或导帧 | 用户签发前 0。执行前记录新基线并预留产出/收尾，计本次所有可归属新增分配块/峰值，重叠查重、删除不返还历史峰值，不用 df 或净增代峰值；新用量/峰值不可核即停报 UNKNOWN，不从旧未知例外获得放行。 |

新增 needs_user **CAPTURE-LOG-SINK**：推荐用户仅按本 work item 一次同意将其旧 Log 叙述整段移入 `docs/status-history.md`（非事实源），状态板保留结论/权威指针，由后续获准的文档整理批次执行，再同批置 ENDED、完整 Gate 行迁 parked 并写保留义务。本轮不动任何旧 Log/status-history/parked。理由：ENDED 移行会使本项旧 Log 失去非终止保护而触发上限；现行用户授权未包含搬移旧叙述，Acceptance 不自行扩大。此题只为迁移合规，不要求再次批准描述性收口，也不放宽 300 行上限。

两项诊断资源须一并签发并由 Acceptance 落实后才交 Air Implementation；仅签一维时另一维仍 0，不执行依赖两维的诊断。其余维度一律 0，Unity/Play=否、模型/推理=0、scenario/session/run ID=0/0/0、API/GPU/下载/安装/其他设备=0；只允许本节 §2 输入与报告，不追加验收或代码范围。到限/将越界、输入漂移/哈希不符、新 UNKNOWN 或任何禁止操作需求即结束分析、在已留余量内报告已得与限制，回用户，不自动扩大信封。当前下一 Owner=用户，Status=`AWAITING_CAPTURE_DIAG_RESOURCE_SIGNATURE`，Consuming=no；当前只可答复诊断资源及旧 Log 搬移建议，不派发诊断。

open_items: R1-4, R2-2, PLAY-AC23-26, RESOURCE-UNKNOWN, B-WALL-OVERRUN, FORMAL-REDO-SOURCE, FORMAL-REDO-LATE-STOP, CAPTURE-DIAG-WALL, CAPTURE-DIAG-AIR-DISK, CAPTURE-LOG-SINK

### 正式重做失败及源归属核清（2026-10-10，Acceptance）

owner=Acceptance；仅根交回终场反馈/用量/入口核清，不重跑评分/测试/模型、不语义读真值、不改实现/独立复核，未开C/R。用户两句逐字已录账本及Unity日志FORMAL2：捆绑确认但明确第一个拐角跟丢，停止后误触要求不用理会。此反馈不扩成逐项PASS、源完整/额外额度或旧结果追认。

本轮正式Play1、缓存加载1/session1/run3已用，额外误触Play或采集组件启动类别/次数UNKNOWN；不能证明完整Play次数符合或返还。首次有效operator_stop退休事件距launch304.059822291 s，较原采集290 s上限迟14.059822291 s；根监控全量采样阻塞停止检查属执行偏差，不以计划采样间隔或覆盖后的stop.json洗白。发布过期/追赶过旧及用户拐角丢失事实保留，不作未经验证因果归属。

**评分入口仍阻断：** 停止后新0/1/2非真值旁车时刻在stop后、旧142…1641留，真值仅stat/hash3147 B未语义读取；静止与无写者只证已停，不能证属于单一正式源。当前混合源3009文件/71,686,913 B逐件哈希保全不等于正式源完整；不筛帧/拼接/补真值/扩读或补跑。AC-23/24/25两次标准main均NOT_RUN(SOURCE_PROVENANCE_UNRESOLVED)，replay0，不替换为NOT_EVALUABLE或局部PASS。S-B-TERM已得文件零模型闭集内，允许且只执行既有click_latency一次全原点击/会话日志配对：分母4、4绑定、e2e[0,0,−1,0]、受理子段0、局部AC-22读数PASS；未签独立复核，不改分母、阈值或把−1称负物理延迟，不解除跟随/源完整/用户目检缺项。

资源检查点681.995 s/保守325,279,744 B来自根最近转交，非最终；本批代录/核清/自检/提交继续共账本900s/新增1GB，根余下仅补机器计量/封口及首检查点指针。最终值引用 `outputs/eng-capture/formal-redo/control/execution-close.json`（本批时待写），close-meter可被后续采样覆盖，不把早586.677 s/305,942,528 B误称当前值或最后值。短暂附属峰值未证仍UNKNOWN，不声称完整历史/本轮峰值符合，不把核清耗时填0、不给宽限或自动新授权。

当前正式结果FAILED_INCOMPLETE，四项稳定停点自证未齐，不开C/独立R/新实现，不签验收PASS/DONE/UNITY_NA。仅剩本窗口安全封口；无再次Play/模型/session/run或额外评分授权，下一范围需用户另定。阶段AOverall/Lifecycle仍REVIEW_PASSED/ACTIVE、R1-4/R2-2 OPEN及全部旧失败/超时/UNKNOWN保持；源污染与晚停不因点击局部读数通过而覆盖。

open_items: R1-4, R2-2, PLAY-AC23-26, RESOURCE-UNKNOWN, B-WALL-OVERRUN, FORMAL-REDO-SOURCE, FORMAL-REDO-LATE-STOP

### 正式测评提前终止与新一次重做落实（2026-10-10，Acceptance）

仅本次反馈/资源核清和新用户直接授权落实，不开C/R、不签PASS/DONE/UNITY_NA，不改正式AC/STOP/代码。原话完整录Unity日志FORMAL1；第三PlayS-B-TERM/rebuild_limit安全结束，控制717帧2–723，Unity1332帧0–1331后续无控制帧不能延长跟随段；归档2667文件/71,011,567 B逐件哈希全等。加载1/session1/run3/Play1实际用尽，原结果不因重做返还。

S1后4原点击与用户红车额外2次报告不一致，S2身份/首次序号UNKNOWN；原误填index2追加纠正、不删原记录。按S-B-TERM已得文件零模型分析闭集，仅既有click_latency调用一次：5原点击/4绑定，未发送malformed0，AC-22合同分母5/FAIL；未读真值或调用main/replay。S3一圈/S4/换回缺项，AC-23/25正式证据缺失、不通过，AC-24 NOT_RUN，不猜参数评分/放宽分母或用局部结果放行。实现自证条件未齐，不申请新候选独立通过。已知封口577.723 s/保守218,193,920 B，随后附属代录/核清/git用量照记，未核齐UNKNOWN，不声明最终完整用量合规；旧两次超时/UNKNOWN/OPEN债保持。

用户另逐字「授权重新进行一次正式测试」并对完整题面答「同意，按相同单次额度重做」，已另条入账，正式第四次Play许可1。仅Air，本次独立新增Play1/诊断0/失败不重开，加载≤1/session1/run≤3/scenario0、新基线新增磁盘≤1GB、准备至归档/两次原评分/原重放核一致性/证据提交共账≤900s；T_sess原min290与新鲜f₀1490门、足额收尾预留保持，其他设备/板端/API/云/下载安装0，不新增测试/模型回放。旧未知仅不单独阻断本新计量额度，不追认旧符合，新UNKNOWN仍停；维度不抵偿/转用、不返还旧耗用。本批新基线/覆盖/模型/Play未启动。

用户自行完整四点击/一圈、陪同仅开始/结束/异常停止，原四次意图静止/更远红/静止/红与一圈预登记；最终实际完成回复及提交/绑定日志对应后才核身份与满一圈，不拿预登记替真实动作、不丢失败分母。其余现场前置/旧件隔离/动态独立ID/原评分/真值隔离/停止义务沿上一「第三次正式测评新信封落实」。新FORMAL2一次采集前HEAD/空porcelain对应已复核候选，根提交后最终HEAD写ops机器证据、不递归日志；未齐不得发令。Overall/Lifecycle仍REVIEW_PASSED/ACTIVE，旧债与负结果不关闭。

open_items: R1-4, R2-2, PLAY-AC22-26, RESOURCE-UNKNOWN, B-WALL-OVERRUN, FORMAL-REDO-PRE

### 第三次正式测评新信封落实（2026-10-10，Acceptance）

用户逐字「可以开一次正式验收，先告诉我步骤」「授权开始一次正式测评」，随后对完整题面答「同意上述本轮额度，继续正式测评」，均已录账本同日「用户授权一次正式测评并签发本轮新资源信封」。本项新增正式Play1已签（此前已用2次保持；本次累计第三次许可），不是对旧结果/超时的追认。owner=Acceptance；仅落实授权与现行合同，不改AC、阈值、实现或复核，不开C/R或签PASS/DONE/UNITY_NA。

**本轮新增信封：** 仅Air，Play正式1/诊断0且失败不重开；YOLO加载≤1、session1、run≤3（驻留1+现行重建≤2），scenario新增0；新计量基线起新增磁盘≤1,000,000,000 B，准备/等待/起停/采集/归档/哈希/两次零模型评分/原ops重放核一致性/证据提交全部共账≤900 s，采集T_sess仍≤min(290 s, (1490−本次新鲜f₀)/5)且扣足实际剩余收尾预留。其他设备/板端/VLM/API/云/下载/安装0，不新增全套/构造测试/正式模型回放。旧额度不返还、不自动转用或相互抵偿；旧单次438.978 s超时、后封口耗用及全部UNKNOWN保留，仅不单独阻断本次新信封，不追认旧符合。新基线后用量/峰值不可核仍停报，不扩旧UNKNOWN例外、不假记0或给900s外提交宽限。

**发令准备与身份：** 最新passed_candidate运行时解析，当前祖先检查exit0、其后PLAY_GOVERNING diff空；既有通过候选可承接，无代码改动不重复开核对/复核轮。发令角色仍现场复取最终HEAD/空porcelain及候选对应、全局门/共享槽位、Unity本工程非Play、冻结身份、容量与预留，新计量基线从执行准备前建立并持续核用量。旧两次帧/真值/日志原件保全隔离，不混入本轮输入/评分；新输出/session/run由运行时独立生成并记机器证据，不手写派生ID、不覆盖旧对象。允许按本新信封把原ops硬编码旧SID/OUT替换为现场独立SID/OUT，仅命令路径绑定，不改工具/配置/正式接口。覆盖源若有残留/冲突、写者漂移、预留不够即停，未授权删除或扩大迁移范围。

**唯一顺序和合同不变：** 完成现场前置/新基线及预留→生成原1500帧覆盖并核身份→最终采集前HEAD/porcelain由接受侧一次代录Unity日志（NOT_STARTED）→根发令用户进入唯一新Play→取得本次新鲜图像/元数据/身份后取f₀/T_sess，才分配session/run/加载模型并启动点击页。正式S1静止车一次→S2更远红车一次→保持红车≥1圈→S4静止车一次再红车一次；现场回复与绑定日志核真实序号/物理身份，异常先报告不补点。全部失败发出点击保留AC-22分母；ops§7原两次评分/两段AC-23同时取读、AC-25仅S2→S4原窗及真值隔离不变。先安全停会话、用户停Unity再归档/评分/原重放核一致性，所有耗用共账新900s/1GB，原STOP/撤权与失败不重开保持。

采集前代录采用现场快照HEAD对应已复核实现，日志/操作单后续仅白名单文档提交；根复取日志提交后的最终HEAD记操作单/机器证据，不递归改日志HEAD。任意PLAY_GOVERNING漂移即回接受侧，未完成凭据不得Play。实现证据/相称验收仍须稳定停点自证→接受核对→独立复核与用户Unity目检；授权不等于结果已通过。Overall/Lifecycle仍REVIEW_PASSED/ACTIVE，旧缺项/OPEN债保持。本批未运行测试/模型/Play/评分/重放，无采集开始或资源实测0声明。

open_items: R1-4, R2-2, PLAY-AC22-26, RESOURCE-UNKNOWN, B-WALL-OVERRUN, FORMAL-PRE

### 第二Play执行核清与描述性结果处置（2026-10-10，Acceptance）

owner = Acceptance；范围仅为根会话交回的执行资源、Unity原话及合同缺项处置。只读原日志与直接相关缓存代码，不跑测试/模型/Play/正式评分/重放/新真值分析，不改实现；不是C轮或独立复核，不签AC/Unity PASS、DONE、UNITY_NA或终止范围。原信封、历史UNKNOWN窄例外及OPEN债保持，先前待执行/NOT_RUN为历史快照。

#### 1. 实际资源及偏差

原件来源为 `outputs/eng-capture/play/attempt-2-control/` 的prelaunch/process-end/close-meter/execution-close、attempt-2-archive及会话language-session.jsonl。Play首轮1+第二轮1=2/2，session1/1；原日志3个distinct resident_loop_started，初始驻留+两次publish_expired后重建，run **3/3已用**，不能凭session目录没有run-*子目录报0。YOLO加载 **1/1**：累计model_requests1→2→3、model_loads始终1，直接相关 `_SessionModelCache` 及重建代码支持同一会话缓存复用，三个累计1不相加为3；不扩为全机独立构造审计。scenario/板端/VLM/API/云/下载/安装新增0，正式评分/重放调用0。

第二attempt同一准备基线unix1791664586.568991：进程结束347.196 s、归档结束365.980 s、close-meter404.587 s、execution-close438.978 s。**已知单attempt超420 s约18.978 s**，归档后至封口72.997 s仍属核验/证据收尾，不改记闲置或给宽限。首轮已核209.723 s保持；根另以旧轮准备93 s+基线至归档全跨度保守计360 s，到第二封口共798.978 s，仅是当时读数，不是最终全B墙钟。封口后的根文档/机检/git与接受代录附属耗用未可靠核齐，保持UNKNOWN、不假记0，不追认最终≤840 s；总上限840亦不豁免单attempt超时。现已停报，无继续采集/评分许可。

close-meter保守已知磁盘291,059,456 B，两轮共账，含移动路径重复计量；该采样不能证明所有短命峰值。封口后文档/git/工具附属增量及未测峰值仍UNKNOWN，旧具名历史附属例外不扩到新UNKNOWN，不声称最终B≤1 GB符合，不为核齐扩大审计/收尾。

执行偏差保留：首轮私有陪同25 s窗口过短；本轮首stop缺共享runtime参数被零写拒绝，补齐后一次有效stop/APPLIED且session/page退出0；监控读取不存在language_state造成null显示，实际tracker_state/会话正常，不记真实状态0。旧请求ILLEGAL_WRITER_SUSPECTED不删。用户自由切换偏离原剧本；已知超时归于执行/证据收尾，无用户额外宽限或追认。

#### 2. 描述性结果及正式缺项

两段用户原话已逐字录Unity日志「UT-P1-ENG-CAPTURE-001-PLAY1 / 第二Play现场反馈与结果代录」。用户报告基本能够跟随/切换、自由切换不同车辆、本人手动结束及2–3次“不灵名”；“测试没有问题”属宽泛体验反馈，不明确丢失报告可见，不扩为合同变更/AC-26完整PASS。903帧/12已发点击保全，11次绑定；第8条请求在原tm_event为NO_TRACK_AT_K。失败保留全点击分母，APPLIED仅受理；至少一条未绑定，不能称AC-22全部绑定/通过，未运行逐点击e2e或正式评分，不作完整时延结论。未把日志事件与用户2–3次反馈无证配对因果。

S2/S4现场序号及物理目标身份、红车完整一圈与换回段未核：AC-23/25为EVIDENCE_MISSING，AC-24评分NOT_RUN，AC-26完整目检未核。ops§7两次评分不得猜序号/物理身份或选最佳段补齐，不能把未评分缺项改成NOT_EVALUABLE。原预测日志保留，不新增分析或判通过。

#### 3. 当前处置与用户入口

推荐保留此次自由切换下基本跟随/切换的**描述性运行结果**与完整原件，并列留正式剧本/评分/验收缺项、执行超时与UNKNOWN；推荐尚未替用户采纳新验收标准或关闭work。四项稳定停点自证未齐，不以本次开新C/R或申请复核通过，阶段A既有通过与R1-4/R2-2 OPEN保持。

当前已签操作停止；Play/session/run及会话加载额度已用尽，不第三次Play、不再模型/会话/run、不猜参数评分、不追加设备/额度。进一步采集、恢复执行或放宽正式合同须用户另定具体范围/逐维预算，不自动重试或补授权。Overall/Lifecycle保持REVIEW_PASSED/ACTIVE；交用户决定下一范围，本轮代录/核清提交后停止。

open_items: R1-4, R2-2, PLAY-AC22-26, RESOURCE-UNKNOWN, B-WALL-OVERRUN

### 用户本人一次重开落实（2026-10-10，Acceptance）

来源为账本同日「用户本人授权一次重开 Play」；原话「不用，直接重开，本人授权」，前句反馈「已进入 Play，现在已退出」。**新正式Play1次已获准，本批累计≤2；不重问是否允许Play。** 该具名授权覆盖原失败不重试及S-B-UNITY的“无再次进入”，不是模型/ID/磁盘/墙钟的新信封；停止安全义务和其余STOP保持。首Play已实际用1，模型/session/run均0，AC-22…26NOT_RUN；私有编排25 s提前停止与晚到新帧如实保留，不能把用户已进退出改写成Unity始终未进入。

执行前先保全旧帧0–67/真值，完整性核验并隔离旧输入/评分，不覆盖、不混旧f₀；按现行操作单现场候选/槽位/覆盖/新帧核清，新的鲜明身份/时间证据出现后取f₀。新session/model/run仅沿原未用上限（1/≤1/≤3），scenario0，不另开代码核对轮或扩大AC。新采集前Unity凭据由Implementation重取后Acceptance一次追加代录，后续仅文档提交不递归重写HEAD。

**墙钟不自动重置。** 原话只明确“重开”、未给墙钟数字；按工程workflow§8/AGENTS信封缺项0，新增墙钟当前0。原93 s准备及本次自20:29:08Z开始的实际执行、等待/起停/保全/收尾仍计原420 s；已经运行的等待不回溯改成裁定闲置。原发令前置§2对实际执行区间间裁定/调度闲置的读法携带，不凭跨会话时间伪造实际执行秒数。根转交20:31:53Z约已用本次165 s，未完收尾，只作当时快照；余量须现场实测，不能凭本节继续报当时162 s。磁盘1GB及新UNKNOWN停报保持，旧附属历史UNKNOWN例外不扩到新量。

若原实际余量足以容纳新attempt原剧本/起停/核验/Z-B，即按已签同余额续，**无需新增授权**；不足时不改剧本/压缩必要收尾，不把“直接重开”解释成新420 s。

**B-REOPEN-WALL已签并落实：** 根会话随后仅问墙钟，用户逐字选「同意，仅追加这次重开的最多 420 秒」，题面及答复已同批入账（同日「用户仅追加具名重开的最多420秒墙钟」）。因此这次重开实际全区间≤420 s，全B累计≤840 s；旧耗时/编排失误/UNKNOWN照记，不能归零、不追认首Play符合，磁盘仍1GB，两次增量共账，模型/session/run沿原未用额，不再加Play、不准第三次。该attempt准备/等待/起停/Play/保全/评分/Z-B共账，无宽限。新基线在本授权落实提交后现场记录，未发生的时刻/耗用不预填。

根会话补核：用户退出回复由本会话机器timestamp解析为20:31:03.985Z，第一次执行基线20:29:08.238Z至此保守115.747 s，另加原93 s；旧源保全实测0.976 s（结束unix1791664410.076908），已核三段合计209.723 s，旧其他未核收尾不假记0。裁定/合同闲置仍沿原§2分列读法，已运行的等待不回溯免扣。旧源同卷无覆盖保全139文件/2,287,134 B，两清单数量/字节/SHA全等，旧frames/truth/overlay已挪开；原陪同编排源副本亦已保留，不把旧数据放进第二attempt评分。根实物来源为outputs机器证据，接受仅代录、未执行保全。

新attempt计划沿原剧本，T_sess cap230 s并与本次新鲜f₀/原1490帧门、实际remaining−55 s共同取min；等待新鲜帧最多90 s且受本次420 s全区间限制，不再次用25 s提前窗口。Unity启动60–90 s、会话最多230 s、Z-B55 s及准备≤30 s须实际共同核上限；四项计划最大值合计405 s（90+230+55+30），余15 s；实际起停/额外核验也须落在同一420 s内，不够仍减会话至足额或按原STOP停止，不能改剧本或压缩安全收尾。现场新计量及两轮磁盘实际增量仍由Implementation核足，新采集前凭据同批Unity日志代录，提交后最终HEAD只记操作单/机器证据，不递归改日志。


本节只落实授权/限制，不签新Play已开始、Unity verdict、DONE或UNITY_NA；Overall/Lifecycle仍REVIEW_PASSED/ACTIVE，旧债/负结果保留。

open_items: R1-4, R2-2, PLAY-PRE, PLAY-AC22-26, RESOURCE-UNKNOWN

### B历史附属UNKNOWN例外落实（2026-10-10，Acceptance）

owner = Acceptance；范围仅为用户本轮「同意继续」及账本同日「用户同意 B-HISTORIC-AUX-UNKNOWN 窄例外…」。已按 Air Implementation 根会话转交的逐字题面/最终提问与原话入账，**推荐 A 已授权生效**；下方「发令预算待裁定」§3 的尚未授权与 S-B-PRE 历史结论由本节承接，不删历史。

唯一效力：仅 CAPTURE:PLAY:1，从 B 签发起到下一执行准备开始前现场新建计量基线时止的编码客户端/派发工具自动日志、缓存、共享数据库和临时暂存不可重建历史峰值，继续记 UNKNOWN、不再**单独**阻断发令。Implementation 记录基线时间与来源；已核清单/文档/git 等照记查重，未知不记0，不返还已用，不追认完整历史 ≤1 GB 或全合同符合，A 的 UNKNOWN 与旧债/负结果不变。

基线以后新用量/峰值及本次 runtime 覆盖/帧/真值、会话/点击模型日志、归档/哈希、评分与 Z-B 全部保持原共账与可核预留；新的 UNKNOWN 或预留不可证明仍 S-B-PRE/S-B-BUDGET。未改变 1 GB、420 s、93 s 已用/后续最多327 s、T_sess、设备、模型/ID、一次Play不重试或 STOP。没有后续自动缓存豁免，不以用户答复代余额测量。

下一执行仍按「发令前置核清」§4唯一顺序及操作单§2，现场前置1–3与HEAD/porcelain重取/代录、已知B账/新计量基线/后续峰值计量方法与产物/Z-B预留全部齐备后，才生成覆盖并继续唯一Play/新鲜f₀/T_sess、会话/点击/收尾；不重排其步骤。因资源核清仍未完成，本节只落实例外，**不签整体发令通过或采集开始**。

Unity日志「UT-P1-ENG-CAPTURE-001-PLAY1」待Implementation最终复取后交Acceptance一次代录现场原始记录（NOT_STARTED），不以本授权落实阶段身份代最终采集凭据。Overall/Lifecycle仍REVIEW_PASSED/ACTIVE，AC-22…26仍NOT_RUN；不新增AC/verdict/DONE/UNITY_NA。本轮只写文档与只读身份/全局门，不执行测试、模型、Play、评分或覆盖。

open_items: R1-4, R2-2, PLAY-PRE, PLAY-AC22-26, RESOURCE-UNKNOWN

### 发令预算待裁定（2026-10-10，Acceptance；Air 陪同会话转交）

owner = Acceptance；范围仅为现行「发令前置核清」§2–4、操作单 §2 的 B 磁盘发令条件。Implementation 按 workflow §4.3 的歧义退回通道转交。本节不重开候选核对/复核，不修改 AC、代码、配置、工具或信封，不运行测试、模型、Play、评分或下载。结论：**现有合同下尚不可启动覆盖生成、会话、模型、Play 或 ID；B 历史附属写入峰值 UNKNOWN 仍阻断完整余额判断。** Overall/Lifecycle 保持 REVIEW_PASSED/ACTIVE，AC-22…26 仍 NOT_RUN。

#### 1. 已答执行分工与墙钟

账本 2026-10-10「用户选 CAPTURE-PLAY-EXECUTOR A…」已落实选择 A；原「发令前置核清」§4 的待选文字为当轮历史。用户已在 Air 开 Implementation 陪同会话；转交信息中的本会话答复为「是，接手 CAPTURE 的 Air 陪同执行」「是，现场就绪，现在可配合」。这是执行分工/现场窗口确认，不是 UNKNOWN 例外或新增额度；不把已答分工再次上交用户。

墙钟沿「发令前置核清」§2 原裁定：残留保全 93 s 已用，后续执行准备、等待/起停/Play/Z-B 共账最多 327 s，须再扣新增执行准备并预留收尾。合同判读、只读来源核清与裁定/调度闲置不计作运行时准备，也不把两个执行区间变成跨会话连续计时；不改变 420 s 或 T_sess 的原上限。尚未开始新执行区间。

#### 2. 现存快照的证明边界

来源 = Air Implementation 陪同会话 2026-10-10T20:17Z 的只读实测转交。筛选常规文件 mtime 或 ctime 不早于 B 签发（19:52Z），无 stat 错误；这里只代录转交读数，不冒称接受侧独立重测：

| 共享目录集合 | 现存文件数 | 分配块字节 | 逻辑字节 |
|---|---:|---:|---:|
| ~/.codex | 56 | 499,032,064 B | 492,624,031 B |
| /private/tmp/claude-501 | 49 | 2,912,256 B | 2,733,946 B |
| 本会话 TMPDIR（由环境运行时解析） | 5 | 77,824 B | 65,676 B |

这些是**共享目录经时间筛选后的现存集合大小**：旧数据库整文件被触碰也会全量计入，既不是本项新增下界，也不是本项历史峰值上界；不能把约 502 MB 归因到 B，不能据其低于 1 GB 判余额足。现存 stat 不重建已删除文件、覆盖前较大版本或未登记暂存峰值；同样不能凭“无 stat 错误”声称历史完整。原已核 188,416 B、接受前置提交报告另测 237,568 B，以及其后本项文档/git 对象等应由实现按来源逐笔核实查重；本节不把报告数未经查重相加为完整账，也不返还历史已用量。

合同依据：「发令前置核清」§2 明令未测缓存/暂存 UNKNOWN、不据下界推余额；「B信封落实」已签维度与操作单 §2.3 要求逐维用量可核及 Z-B 预留足；工程 workflow §8 和 acceptance 细则禁止接受角色改资源边界。阶段 A 的 R-C2-RESOURCE 用户处置只属 A，不能转成 B 例外。当前没有可得的、覆盖上述历史删除/覆盖/暂存全过程的独立记录，因此**不能在既有合同内只靠该快照合法核清完整上界**。只读查到可证明的历史来源时可按原规则补核；没有该来源时停止追查，不无限扫描或为核账生成新工件。

#### 3. needs_user：B-HISTORIC-AUX-UNKNOWN（唯一窄问题；尚未授权）

**推荐 A：仅本次 CAPTURE:PLAY:1，允许此前 B 陪同工具日志/缓存/暂存的未知历史峰值不再单独阻断发令。** 例外闭集 = 从 B 签发起，到本项下一次执行准备开始前新建计量基线时为止，编码客户端/派发工具自动产生的日志、缓存、共享数据库及临时暂存的未可重建历史峰值。基线时间由实现现场实测记录，不从本节日期臆填。已知读数与历史 UNKNOWN 原样保留，不改记 0，不追认此前新增磁盘 ≤1 GB，也不宣称完整 B 磁盘符合。该例外不返还、抹掉或重复计算已实测的清单、文档、git 对象与其他 B 用量。

A 不增加设备、磁盘、墙钟、模型/ID、Play 或重试额度，不改变原 1 GB 封顶；**本次 runtime 覆盖/帧/真值、会话与点击模型日志、归档/哈希、评分及 Z-B 收尾全部仍须实测共账与预留，不能列入例外**。基线以后的新用量/峰值仍适用原核清要求；发生新的不可核用量或不能证明后续产物/Z-B 预留足，仍按 S-B-PRE/S-B-BUDGET 停报，不能用本次历史例外豁免。用户选择 A 也不是立即按 Play：先入账并由 Acceptance 落实，再由 Implementation 核实已知 B 账/新计量基线/后续峰值计量方法与产物/Z-B 预留，采集前 HEAD/porcelain 代录及操作单 §2 全部现场前置齐备，才按唯一顺序执行。

**备选 B：保持原条件，本次继续停在发令前。** 仅在有上述历史全过程来源时只读补核；来源不可得则等待用户另定，不耗唯一 Play、不另开诊断、不清缓存伪造余额。推荐 A 的理由是缺口局限于采集前工具附属写入的不可重建历史，后续采集实物及守账不放宽；它是用户对证据限制的具名处置，不能由接受或实现角色代拍。

对用户的完整窄问题：**是否同意 A——仅这次 CAPTURE:PLAY:1，保留此前工具日志/缓存/暂存峰值 UNKNOWN 且不追认 1 GB 合规，允许这段历史未知不再单独阻断发令；已知用量照记，后续 runtime/模型日志/归档/评分/收尾继续在原 1 GB、420 s 及一次 Play 信封内实测核足，新的 UNKNOWN 仍停报？不同意则选 B，保持停在发令前。**

本节仅形成待审阅申请，未写成已授权裁定、不代录采集开始或填 Unity 发令日志。现存非 Play、端口/槽位、候选/权重等转交快照不能替代批准后现场重取；历史 Open 债、负结果与主张上限不变。

open_items: R1-4, R2-2, B-HISTORIC-AUX-UNKNOWN, PLAY-PRE, PLAY-AC22-26, RESOURCE-UNKNOWN

### 发令前置核清（2026-10-10，Acceptance）

owner = Acceptance；范围 = 「B信封落实」发令前置 1–5、操作单 §2.1 保全核验、墙钟/磁盘口径及 Air 执行分工；状态 = 残留处置满足，前置 2–3 的可读部分已核，现场与用量预留仍待重取，第 4–5 项未执行，交用户选择执行者。本轮只读磁盘及文档增量，不运行 Unity/Play、模型、测试、评分或重放，不生成覆盖，不改 runtime/outputs、授权账本、AC 或额度；不签独立 verdict、DONE、UNITY_NA。下列原 B信封落实中 RUNTIME-ARCHIVE「尚未授权/执行」为历史，本节承接现行事实。

#### 1. 残留保全：满足（前置第 1 项的处置部分）

授权以账本 2026-10-10「用户同意 RUNTIME-ARCHIVE…」为准（at: 已更正）；实现记录为操作单 §2.1。只读核该节所记录的运行时生成保全目录、manifest-pre/post 与 compare.txt，重新逐文件读取实际原件：两清单逐字节相同，均 258 行、8,748,594 B，实际 258 文件的相对路径/字节/SHA-256 与清单逐项相等，无符号链接；runtime、outputs、保全目录及两目标 st_dev 均 16777231。runtime/frames 与 runtime/m3_body_truth.jsonl 两源均不存在，保全目录 du 为 9,204 KiB。原件不进本次评分/在线输入。执行记录的源静止、排他建目录及两次 mv -n 成功且源已移离，与现状及用户现场无写者确认一致；不声称能只凭当前目录重建每条历史命令。

结论限这两个旧对象的保全处置；没有生成本次覆盖、分配 session/run 或消耗 Play。发令时若两源重新出现、保全对象变化或出现写者，按 S-B-PRE 停报，不再次移动、不覆盖、不回迁。其余 runtime 路径仍不在本轮处置范围。

#### 2. 墙钟与磁盘：唯一读法，不改上限

**墙钟：93 s 必须计入同一个 420 s 上限。** 依据 AC-21、AC-20/21 修订 1（AR1-6）、B信封落实「runtime 残留的唯一处置读法」及 RUNTIME-ARCHIVE 账本末项。准备区间 20:01:41Z→20:03:14Z = 93 s；后续执行准备（如覆盖生成）、等待唯一 Play、起停/Play 与 Z-B 实际区间共账，重叠时间只计一次。裁定/调度间的闲置等待不把这两个分列执行区间变成跨会话连续计时，也不能拿分列为由免扣准备耗时。累计 = 93 s + 后续上述实际耗时 ≤ 420 s；因此后续总窗口最多 **327 s**，有新增准备耗时再扣，须在此内预留 Z-B，不是再给 420 s。累计到 420 s 未静止即执行 S-B-WALL，安全撤权必须做、超限照记。T_sess 原上限 min(290 s,(1490−f₀)/5) 不变；还须满足实际剩余窗口及收尾预留，不能自动取 290 s 或把 327 s 当会话许可。未足以容纳原剧本及收尾就 S-B-PRE/S-B-BUDGET 停报，不改剧本或另开 Play。

**磁盘：统一按 Air 新增 ≤ 1 GB 共账，GB 不改 GiB。** 已有 8,748,594 B 原件同卷 rename 不增加其数据，9,204 KiB 保全目录总占用不是新增量；实现移入后/写清单前后 du 差 **60 KiB = 61,440 B**（逻辑 51,811 B）计 B。清单逻辑字节已包含在 60 KiB 内，不再叠加。实现报告提交 git 松散对象 +124 KiB 虽未写进 §2.1，已在 supervisor 派发日志「残留保全」finished.report 留源；本轮运行时解析该提交及父提交，用 rev-list --objects 的 6 个对象逐个 stat 复算：全部为松散对象，分配块合计 **124 KiB = 126,976 B**；objectsize:disk / st_size 合计 108,657 B，是同一对象集合的压缩文件长度，不与分配块值相加。本节将报告落实为可核实 B 磁盘读数，无需新额度。

上述两笔不同对象合计 **184 KiB = 188,416 B**，仅为已核小计，不是完整 B 用量或可用余额。此后本项文档实际增量、git 新对象、派发/暂存及本次覆盖/日志/哈希/评分/收尾新增继续计 B，旧 A 未核项留 A，不借迁机或换信封抹去 UNKNOWN；同一对象/增量只计一次，删去或打包不能返还历史已用峰值。df 全盘读数不作本项新增量。本轮文档/提交对象的最终字节须收工后补读交回报告，未测缓存/暂存保持 UNKNOWN、不假记 0；下一执行者先只读核清来源、逐维已用及 Z-B 预留，未齐不能启动。接受角色本轮不改阶段 A 机器账，也不拿下界证明 B 余额足。

#### 3. 前置第 2–3 项：当前只读快照，非发令凭据

快照采于 2026-10-10T20:07:21Z 起（包元数据与 git 对象补读同轮）。下面 HEAD 与配置 SHA 由读取程序运行时写入，不手抄通过候选或工件标识；正式发令必须重取 HEAD/porcelain、候选解析与所有现场读数，填操作单 §9 并交接受/辅助代录 Unity 日志。本轮不创建 Unity 用例或伪填尚未发生的发令记录。

| 项 | 当下只读读数 / 判定 |
|---|---|
| HEAD / porcelain | `489de4181ab02140e621177b282486c13ee8b31c`；git status --porcelain exit 0、空输出（0 行），为修改前快照；提交后会变化，不能代填发令 HEAD |
| 通过候选对应 | 从同名复核最近 passed_candidate 运行时解析（不复制其值），git cat-file 为 commit、merge-base --is-ancestor exit 0；PLAY_GOVERNING 全集差异 0 行，冻结集未点名本操作单；派发 base 为当前 HEAD 祖先，其后仅 supervisor-dispatch.jsonl 登记差异 |
| 白名单文档差异 | 通过候选至快照仅 8 路径：docs/authorizations.md、current-status.md、同项 K1K2K3K4-handoff.md / ledger.json / play-ops.md、supervisor-dispatch.jsonl、同名提案、同名复核；无实现差异。文档新增是签发/落实/核验/登记，不把授权文本当代码放行；操作单 §7 两段评分与 AC-22 分列不改 |
| 全局 blocks/releases | 按 check_docs.py 全目录配对函数扫描 docs/reviews/*.md（含同文件顺序）、implementation-status 的 RELEASED_SCOPE_GAP；未配对 blocks={}、账本 releases={}、消耗门错误=[]。当前本项 R1-4/R2-2 OPEN 不冒充 release |
| 轨道 / 单写者 / 共享槽位 | handoff_activity：消耗性 [P1-ENG-CAPTURE-001]、零消耗 [P1-ENG-JET-001]、错误=[]；派发日志仅本 Dispatch-Id 未终结。pgrep 会话/eng_capture/旧操作页无结果（exit 1）；lsof +D runtime 无输出（exit 1）。仅本轮本机可见范围，不承诺之后仍空闲；发令重核 |
| 磁盘 | df -h .：/dev/disk3s5，228Gi / Used 187Gi / Avail 12Gi / 94%，挂载 /System/Volumes/Data；≥1 GB 满足，完整 B 用量及产物/Z-B 预留尚未核齐，不从可用量推余额 |
| 8774 / 覆盖与目标 | lsof -nP -iTCP:8774 无输出、exit 1；test ! -e runtime/scenario_config.json exit 0、test -w runtime exit 0；两旧源与 outputs/eng-capture/play（包括本次 session/归档目标）均不存在；未生成覆盖 |
| Unity 现场 | 现存 Unity 6000.4.1f1 编辑器进程的 projectpath 为本工程；仅核版本/工程字段，不记录进程凭据。非 Play 仅有 RUNTIME-ARCHIVE 用户旧确认，本轮无人重新确认界面，发令时须本人确认工程/场景/非 Play 状态 |
| 解释器 / 包 | Python 3.12.13；仅 importlib.metadata 读取 ultralytics 8.4.104、torch 2.13.0、lap 0.5.13、numpy 2.5.1、opencv-python 5.0.0.93；与操作单 §1 一致，补丁差解释携带，未导入模型 |
| 冻结权重 | 5,458,330 B，现算 sha256 与 det-assoc-v1.models.json.weights.sha256/size_bytes 相等；freeze 文件现算 sha 与该配置.freeze.sha256 相等；未加载权重 |

配置身份补读（程序现算；逐值及字节均以现场重取为准）：

| 文件 | 本轮身份 |
|---|---|
| `config/scenario.untethered.json` | 3,377 B；`962764bc0fd47cd3e51253ce19ecabb369c23e0261393419ac38ba059cd16d87`；与通过候选逐字节相同 |
| `config/p1-eng-capture-001.json` | 2,246 B；`c15c3c3c19b71bdd526e1c17664b751f2545459af7be7d1dc844e92682decf52`；与通过候选逐字节相同 |
| `config/p1-eng-frame-001-body.json` | 787 B；`7193fe77fd03d9a4f9565150d6a37dc75a83a56160bbfe2d167b4e710e35dbfc`；与通过候选逐字节相同 |
| `config/det-assoc-v1.models.json` | 1,197 B；`76919cf73ff47b2dffca84419758b06171393bdf9d19d6a108f40bea547e6c1d`；与通过候选逐字节相同 |
| `docs/evidence/P1-ENG-FAST-002-freeze.json` | 2,899 B；`f231e450d967c301f0a4651bd9102d9e5c6073abfbed3d026fedc96fa590c93c`；与通过候选逐字节相同 |

scenario 源 sensor = 640×480、5 Hz、retained_frame_count=128；第 4 项才按 §3 仅覆写为 1500，其余值须逐值相同。本轮第 2 项候选/全局门/轨道只读检查满足；第 3 项磁盘可用、端口、配置/冻结权重满足，但实时 Unity 非 Play 与逐维实际用量/Z-B 预留未齐，**整体尚不可发令**。本轮文档提交不会替代下一现场检查；漂移/未知沿原 S-B-PRE/S-B-BUDGET 处置。

#### 4. 执行者、顺序与 needs_user（第 4–5 项）

**CAPTURE-PLAY-EXECUTOR 待用户选择，推荐 A：用户在 Air 亲自开启 Implementation 陪同会话并给出当下 Play 窗口。** A 中实现角色负责终端前置复取、用量核清/预留、§3 覆盖生成与 SHA 记录、取本次新鲜 f₀/计算 T_sess、§4 会话/点击页命令及 STOP 监控、零模型归档/两次评分与实现者证据；用户负责确认 Unity 现场、唯一 Play 的进入/退出、§5 点车剧本与 AC-26 目检。此分工不把按 Play 或人眼操作委托给代理、不增加额度。理由：一次不可重跑、后续最多 327 s 且会话/页面需终端配合，已有实现角色最适合核身份/参数、监控预算和收尾，用户能专注剧本。备选 B：用户本人在 Air 照操作单 §2–9 执行全部终端命令及 Play/点击，保留原始现场读数，后交实现整理证据、接受/辅助代录 Unity 日志；不要求用户选 A 才能使用已签信封。

这是一项执行分工/设备窗口选择，不重问 CAPTURE:PLAY:1、RUNTIME-ARCHIVE 或 STOP，也不替用户扩大它们。**supervisor 不能凭本核清或常规接力自动派发下一步。** 权限来源：docs/roles/supervisor.md「停下条件」(a)「交接 Owner 为用户且不在启用的代拍类」、(b)「下一步需要 Unity Play、人眼保真或用户设备操作」。本节点命中这两项，supervisor 应原样转呈推荐、记录用户选择再交回负责角色；若用户明确指示 supervisor 在当前 Air 窗口派发一个有界 Implementation 陪同会话，该直接指示优先于常规停下条件，才可登记并派发，不能由接受角色把推荐写成已授权例外。未选择时不生成覆盖/启动会话或 Play。

选定执行者后的唯一顺序：先现场重取前置 1–3 与 HEAD/porcelain（操作单 §9；接受/辅助在采集前代录 Unity 日志）→ 核足后续 ≤327 s 减新增准备耗时及磁盘/Z-B 预留 → §3 生成覆盖、核 1500/其余逐值与 SHA，写 §9 → 用户开始等待并进入唯一 Play（等待起计本次按钮墙钟，共账 93 s）→ 首次本次新鲜 latest/旁车出现后、会话前核身份/新鲜性、取 f₀ 算正且合法 T_sess，写 §9 → §4 会话与点击页（各终端保持相同 PY/SID/OUT，页面无需等会话结束，两个进程并行运行）→ 用户 §5 剧本、执行者监控 §6 STOP/用量 → §8 串行 HOLD/停会话/用户停 Unity/UNKNOWN → 写者静止及本次身份核清后 §7 无覆盖归档、哈希、两段评分/AC-22 分列、资源实账 → 实现整理 PlayK2K4 自证，交接受核对再独立复核。任一步失败按原 STOP，不重启/不重试 Play、不换 ID。未完成采集前凭据代录也不得开始采集。

Overall/Lifecycle 保持 REVIEW_PASSED/ACTIVE；AC-22…26 全部 NOT_RUN，旧负结果/债与主张上限保持。本轮不新增 AC、finding、block/release 或通过态。

open_items: R1-4, R2-2, CAPTURE-PLAY-EXECUTOR, PLAY-PRE, PLAY-AC22-26, RESOURCE-UNKNOWN

### B信封落实（2026-10-10，Acceptance）

owner = Acceptance；范围 = CAPTURE:PLAY:1 逐维落实、Air 预检核对、操作单发令前置与旧 runtime 残留处置裁定；状态 = B 已签，残留归档授权待用户，尚不可发令。本轮仅文档及只读核对，consumed={}；未运行 Unity/Play、模型、测试、评分、重放、安装或下载，未移动或删除 runtime 文件，不写授权账本，不签 verdict、DONE 或 UNITY_NA。

**唯一 B 授权来源：** `docs/authorizations.md` 2026-10-10「P1-ENG-CAPTURE-001 — 用户签发阶段 B 额度 CAPTURE:PLAY:1 并确认 B 类 STOP 处置（supervisor 会话代录）」。已逐维核对该条与 §5.2、§6、终局 AR1-6 的 B 类拆分行、操作单 §0/§6：额度与停止边界一致，无信封维度歧义；U-2/B 类 U-4 已签。本节落实既有授权，不另签发、扩大或转用额度；前述“B 未签 0”、Air 待核与资源待补是当轮快照，现行效力由本节及上述账本承接。签发不等于现场发令前置已完成。

#### 已签维度与生效边界

| 已签维度（CAPTURE:PLAY:1） | 生效边界 / 操作单守账 |
|---|---|
| 执行机 | MacBook Air 承载 Unity、会话、快层及零模型评分；mini 无 B 新增磁盘额度，产物留 Air，不传入 mini 落盘 |
| Unity Play | 正式 1 次、诊断 0、失败不重试；尝试进入但 Unity 未进 Play 也按 S-B-UNITY 占本次，不以重启或诊断另开一次 |
| scenario / session / run ID | 0 / 1 / ≤ 3；现有场景配置原样复用；常驻段 1 + 现行重建上限 2，不是 3 次独立会话或 Play 许可；实际尝试及失败照记 |
| 会话 YOLO 加载 | ≤ 1；重建只复用会话已加载对象，失败不返还；不继承 A 的加载、全套或候选余额 |
| 按钮墙钟 / 会话时长 | ≤ 420 s；从等待唯一一次 Play 开始计，包括起停、Z-B 收尾，不给超时宽限；起会话前用本次新鲜 f₀ 算 `T_sess` ≤ min(290 s, (1490 − f₀)/5)，不可用旧 latest 或臆填 f₀ |
| Air 新增磁盘 | ≤ 1 GB；覆盖、日志、封存、哈希、评分与收尾共账，启动前预留；不是 df 可用量。零模型/零 ID 操作仍可能占磁盘、墙钟，UNKNOWN 不假记 0、不据未知推余额 |
| 板上、VLM/API、云 GPU、下载/安装 | 均 0；不扩第二/三轮、不改场景、不继承其他信封 |

**B 类 STOP 确认：** 以上唯一账本条已确认 S-B-PRE、S-B-UNITY、S-B-TERM、S-B-WALL、S-B-UNSAFE、S-B-BUDGET 六行。只按终局 AR1-6 拆分表及操作单 §6 的必停依赖、Z-B 和可继续闭集执行；§6 旧“零消耗安全收尾”不作为磁盘/墙钟豁免。S-B-PRE 仅获准 Air 只读复核、不启动模型/会话/Play/ID；S-B-UNITY 本次计已用，无再次进入；S-B-TERM 不重启/重建；S-B-WALL 立即停止、实际超时照记；S-B-UNSAFE 立即停止且 AC-25 FAIL；S-B-BUDGET 只准未越界且已预留的零模型收尾写入/分析，回用户。安全撤权不等待新许可；UNKNOWN 或紧急停止实际超限记录偏差，剩余额度不转用，STOP 不冒充通过。

#### Air 预检读数核对

已核操作单 §1 九项原始读数与 handoff §R8；采纳其“全部核过”仅为 §8.2 环境前置核清：

- HEAD/空工作树及通过候选祖先关系为预检当时读数。本轮重新从同名复核最近 `passed_candidate` 运行时解析，祖先检查通过、其后 PLAY_GOVERNING 代码差异为空；发令仍必须重取，不能复制旧 HEAD 当现场凭据。
- Python 3.12.13 对 mini 3.12.14、numpy 2.5.1 对 2.5.3 均为同次版本补丁差；§8.2 允许“一致或逐项说明”，Air 既往 Play 环境来源与本机解释器可用性说明足以满足这项只读预检，不要求升级/装包。ultralytics、torch、lap、opencv-python 逐项一致，冻结 ultralytics 版本一致；不承诺两机数值逐位相同，不以元数据读取代替本次模型加载/Play 实测。
- 权重现算身份/体积与冻结配置一致；Unity 6000.4.1f1 打开本工程有 Editor.log 与现存进程事实，现场仍由用户确认界面。覆盖 JSON 可解析、runtime 可写且覆盖路径无残留；8774 空闲；Air→mini Tailscale 直连只证明路径可达，不证明物理同局域网，也不给 mini 落盘许可。
- 磁盘读数可用 **12 GiB、已用 94%**，满足 ≥ 1 GB；**发令前必须重读 `df -h .`**，仍 ≥ 1 GB 且能预留本次输出/收尾才继续。94% 本身不是新增 STOP 阈值；读数漂移或余量无法确认走 S-B-PRE，不能把可用量当新增磁盘额度。
- tick 间隔 ≤ 1 帧与进程内往返时延仍待本次 Play 日志实测，不预填 AC-22 通过。§R8 三笔资源补记已承接通过轮消费的回归核实副本等义务；A 的 codex/暂存缓存、后续提交字节 UNKNOWN 保持，不推完整余额、不转入 B 或补记为 0。

#### runtime 残留的唯一处置读法与 needs_user

**裁定：先完整保全旧原件、挪开两个源路径，再做本次 Play；不采用留在原位仅记基线的方案。** 原观察为 `runtime/frames/` 257 项（latest.json 2026-10-04）及 `runtime/m3_body_truth.jsonl` 1,543,923 B。只读代码依据：`SensorFrameWriter` 的 `frameIndex` 从新组件初值起，`PublishFrameBundle` 写同名帧及 latest；`CoverageEvaluator::WriteM3BodyTruth` 首次以 `FileMode.Create` 打开真值。原位 baseline 不能防止旧原件被新 Play 覆写；旧 latest 也不能作 §4 f₀，直接 §7.1 `mv -n` 会混入旧帧或因目标冲突跳过源文件。

**RUNTIME-ARCHIVE（needs_user，推荐同意，尚未授权）：** 允许 Air Implementation 在用户确认 Unity 非 Play、相关会话/点击页等写者均静止及共享槽位独占后，仅把上述两个完整对象以同卷 rename、无覆盖方式移入 `outputs/eng-capture/preexisting-runtime/` 下当场排他创建的唯一目录（路径运行时生成并记录，不是 scenario/session/run ID）。移前后逐文件数量、字节数与 SHA-256 清单相等；不删除、不复制后删源、不跨卷、不覆盖、不改旧内容、不动其他 runtime 路径。目标存在/不同卷/源仍在写/身份变化/核验不符即停报；部分移动保留现场与记录，不盲目重试或回迁覆盖。原件与清单始终留 Air、不进本次评分或在线输入；新增目录/清单/元数据写入实测计 B 的 1 GB，留足后续余量，不假称零磁盘。该准备无模型/推理/Play/API/正式 ID，Consuming no；不增加额度，实际准备墙钟单列并保守与后续起停/Play/收尾合计核 420 s，不另给额外时间窗口。

必须先由用户在发生授权的会话确认并逐字入账，再单独交 Air Implementation 执行和交回核验；本轮只写方案、不执行。理由和权限来源明确：上述唯一 B 账本条末项逐字写“本条不授权删除或移动”，已有 §7.1 对本次产物的归档许可不能扩为旧用户数据迁移许可。用户未同意前按 S-B-PRE，不启动会话/模型/Play/ID；B 已签各上限保持，暂不消耗。本 needs_user 不重问信封或 B STOP，推荐理由是保全旧数据并排除 f₀/归档污染。

#### 发令前置清单（操作单 §2，逐项现场核验）

1. RUNTIME-ARCHIVE 授权入账且处置核验完成，两个旧源路径已挪开；不存在其他写者。覆盖路径若已存在停回接受，不删除；本次输出目标若已有对象也停报、不覆盖或换 ID 规避。
2. Air 发令角色重取 HEAD/porcelain；运行时解析通过候选，确认祖先及仅文档白名单差异，写入操作单 §9 和 Unity 日志（由接受/辅助代录）。全局 blocks/releases 无未释放阻断、轨道与共享槽位互斥通过；此刻机检不能替代发令时复核。
3. 复读磁盘、端口与现场 Unity 工程/非 Play 状态；核现行操作单、配置与冻结权重身份无漂移。已签逐维用量/余额可核、收尾预留足够；未核即 S-B-PRE/S-B-BUDGET，不能推未知余额。
4. 在已签 B 准备内按 §3 生成唯一覆盖，`retained_frame_count` = 1500，记现场 sha 并与 `--body-scenario-config` 逐值核对；失败停报，不启动模型/会话/Play/ID。
5. 用户进入**唯一一次正式 Play**，从等待 Play 起计按钮墙钟；确认本次新 latest/帧旁车新鲜、身份与覆盖相符后取起会话前 f₀，算合法且正的 T_sess，再执行 §4 会话/点击页。无新帧不取旧值、不默认 0、不另一次 Play；Unity 未进入走 S-B-UNITY。按 §5 四段剧本、§6 STOP、§7 两段评分/AC-22 分列、§8 Z-B 收尾，实际耗用如实记录；f₀、起止墙钟及 STOP 填 §9。

本轮只落实已签与上述唯一读法，不新增 AC、不更改阈值、参数、剧本或评分器。Overall/Lifecycle 保持 REVIEW_PASSED/ACTIVE，AC-22…26 仍 NOT_RUN、无 UNITY_NA 附议、未验收；R1-4/R2-2 OPEN 及所有旧负结果/债/主张上限保持。最终 Play 产物仍须走 PlayK2K4 实现证据 → 接受核对 → 独立复核与用户 Unity 目检。

open_items: R1-4, R2-2, RUNTIME-ARCHIVE, PLAY-PRE, PLAY-AC22-26, RESOURCE-UNKNOWN

### 通过轮消费（2026-10-10，Acceptance）

owner = Acceptance；范围 = `K1K2K3K4` 最终有效通过轮的只读消费与归因收口；状态 = 阶段 A 停点通过已消费，等待用户安排已定 Air 预检及决定阶段 B 信封。依据同名复核全文、现行合同、账本本项各条、handoff §R0–§R7 与资源账；不再做第三次常规候选检查。以下 R2冻结裁定、IR-R1-3答复落实及 C1/C2 原文保留为历史，其中“R2-1未闭／通过待消费”由本节承接。本轮未跑测试、模型、评分、重放、Play、板端或下载，consumed={}；不改实现、复核文件或授权账本。

**消费对象：** `docs/reviews/P1-ENG-CAPTURE-001.md`「回归核实」§0–§5 的终局 `PASS`，沿 `R2@K1K2K3K4` 冻结集 {R2-1} 路径 (ii) `NOT_MECHANIZABLE` 闭合；代码零 diff，不新编轮 3。`passed_candidate` 已在本会话从该文件最近一条机读行运行时解析，并核实 git 对象存在、为当前 HEAD 祖先及其后 PLAY_GOVERNING diff 为空；手维护文档不复制 SHA。后续使用时重新解析：

```python
import re
from pathlib import Path
passed_candidate = re.findall(
    r"^passed_candidate: ([0-9a-f]{40})$",
    Path("docs/reviews/P1-ENG-CAPTURE-001.md").read_text(),
    re.M,
)[-1]
```

本次接受决定将 Overall 置 `REVIEW_PASSED`，Independent review 记上述终局 `PASS` 已消费；仅解除停点 1 的依赖门，不签发 Play 或资源。复核无未 release 的 `blocks_consuming_gate`，本轮不写任何 block/release；仍须按全局机检、共享槽位及现场候选对应关系发令。

| Finding | 依据与机械归因 | 消费收口 |
|---|---|---|
| R1-1 | BC-15 = AC-15 → 实现错误 | R2 §2 红绿独立核实已闭：端口缺行、截断、乱序、重复拒绝；保留 R2-2 的非端口删行主张上限。 |
| R1-2 | BC-20 = AC-20/21、AR1-6 → 实现错误 | R2 §2 红绿独立核实已闭：S-A-INPUT 收尾写盘入账；墙钟附注已补，不另造 finding。 |
| R1-3 | BC-22 = AC-22，兼 AC-23/25 → 实现错误 | R2 §2 已闭；IR-R1-3 用户答复由 AC-22 修订 1 落实，工具较大分母与合同分母分列；复核回归核实 §1 已核说明，不改变既有运行读数。 |
| R2-1 | BC-23 = AC-23 → 实现错误 | 回归核实 §1/§5 已闭：操作单 §7 两段取读同时成立、缺段不计通过。保留 R2 §2 披露的 R1 闭合要求漏写换回段之复核责任事实，不以机械归因覆盖。 |
| R1-4、R2-2 | SCOPE_GAP → AC/BC 缺失（非阻断） | `docs/implementation-status.md`「范围外已知缺陷」两条 OPEN 保持；未修、不关闭、不签 release，不追加范围。 |

| AC / 义务 | 当前状态与证据边界 |
|---|---|
| AC-1…16、AC-20；AR1-2/3/6 | 阶段 A 代码及相称证据随停点通过；见复核 R1 §1–§4、R2 §1–§4、handoff §R0/§R1a/§R4/§R6。全套候选 3 失败集与候选 2 相同，基线 61 + IR-2 合同预期 1，本项新增回归 0；不称全套全绿。范围外缺口按上表记债。 |
| AC-17/18/19 | 沿用候选 2 正式回放：AC-17 PASS、AC-18 九项 PASS、AC-19 六格非劣化；候选 3 不重跑理由及生产工件新旧重放一致性见 handoff §R3，复核 R2 §0 已附议。不得改称候选 3 的真实运行产物，不扩统计或板端主张。 |
| AC-21、AC-27、AC-28 | 操作单两段与 AC-22 分列由回归核实通过；AC-21 仍为未来操作草案，Air 原始预检与现场发令核验未完成。保真及人工预登记沿已核证据，不以阶段 A 保真代替 Play 用户目检。 |
| AC-22…26 | 停点 `PlayK2K4` 全部 `NOT_RUN`，评分口径通过不等于 Play 验收；B 未签 = 0。产物仍须另走实现证据 → 接受核对 → 独立复核，并有用户 Unity 目检。 |
| Unity / 完成 | Unity `NOT_RUN`；复核回归核实 §4 未附议任何 `UNITY_NA`。本项不是 `DONE`，也不作 `CLOSED_*`。 |

**下一步与用户待决：** 保持 Lifecycle `ACTIVE`，因为仍有具名用户交接（安排 Air 会话、后续 U-2/B类U-4 决定），无暂停/终止授权。U-3 的执行者与时机已在账本 10-09 选定，不重问：用户在 Air 开会话，由 Implementation 按 §8.2、操作单及终局 U-3 做零消耗只读预检，原始读数写入操作单。该动作已获准，推荐先完成；mini 无法代证 Air 环境，本派发不连设备或执行它。预检不跑模型/Play、不安装、不写共享 runtime；覆盖文件只核可生成方案，实际生成待 B 已签；Unity 打开事实按用户现有界面/日志核，不用静态版本代证。

CAPTURE:PLAY:1（或用户明确签发的同名阶段 B 信封）及 B 类 STOP 处置未签，现行额度全部 0。**推荐现在先不签，Air 预检全部核清后，再由用户逐维签 §5.2 与终局 AR1-6 的 B 类 STOP/磁盘/收尾边界，保持正式 Play 1 次、失败不重试；理由是该不可重跑步骤的代码停点现已通过，但环境前置尚缺。** 用户选择后须在发生授权的会话逐字入账，再交接受角色落实；本节仅作推荐，不代拟成已签或自行放行。B 不含 mini 新增磁盘额度，推荐评分及产物留 Air；需要其他维度另回用户。

**资源补记仍待实现角色下次提交：** 复核「回归核实」§5 报副本检出峰值 **81,022,976 B**，已删除、净新增 0，仍按峰值入 A 磁盘账；当前资源账尚无此笔。实现角色按既有候选归属、来源与查重补记，连同后续文档/收尾 git 对象等义务核实，UNKNOWN 不假记 0、不据未完整账推余额。R2 两笔及后续三笔已由 handoff §R7.3 与复核回归核实 §2 核清，不重复记。本接受角色无 `docs/evidence/*-ledger.json` 写权，本轮不补账。候选 3/3、全套 3/3、构造 6/6 已用尽，未签维度不转用，不新增代码候选或执行额度。

open_items: R1-4, R2-2, AIR-PRE, U-2, U-4-B, RESOURCE-REGRESSION

### R2冻结裁定（2026-10-10，Acceptance）

owner = Acceptance；范围 = 同名复核 R1/R2 全文、现行合同、账本本项授权、handoff §R0–R6、资源账与操作单 §7；状态 = 冻结集裁定完成，IR-R1-3 上交用户。保留以下 C1/C2 原文为当时候选核对，不签独立 verdict、不消费通过轮。候选由复核 R2 §0 `round_candidate` 与 git 运行时解析；本轮只读评分器直接关联函数，未执行测试、模型、评分、重放、Play、板端或下载，consumed={}。

#### 冻结集 {R2-1} 与唯一闭合路径

**R2-1：范围内必修（BC-23 = AC-23），不改标 SCOPE_GAP。** AC-23 与操作单 §4 S4 已点名换回红车后的转向/修复/报告；删掉该段读数会遗漏已接受验收义务。机械归因按依据列为实现错误；同时保留复核 R2 §2 披露的“R1 闭合要求漏写换回段”事实，不用机械归因覆盖上轮复核责任。

**指定路径 (ii)：NOT_MECHANIZABLE 操作单定点复看，不开轮 3。** 采用复核 R2 §3/§5 提出的既有评分器两次调用，限于补齐操作单编排与取读数说明；真人 S4 换回点击身份与两份输出取用需核操作单和现场日志，不能以仓内代码断言替代。本裁定不把评分函数本身标成不可机检，也不授权代码变更。实现角色只补 `docs/evidence/P1-ENG-CAPTURE-001-play-ops.md` §7 及相应 handoff/资源补记，要求：

1. 第一调用仍取 S2 红车绑定至 S4 首次点击前一段；按实际点击日志行序核序号（页面拒收行仍占工具序号），不硬填示例序号、不用序号推断目标身份。
2. 第二调用使用同一 session-dir、click-log、truth，以 `--s2-click <S4换回红车且已绑定的点击序号>`，**不带 `--s4-click`**，另存输出；取其 `AC-23` 为换回段，起点为换回提交事件后首个新绑定授权帧，直到会话末。不得把未绑定、无授权帧或缺必需日志当作通过。
3. AC-23 结论必须同时覆盖两段修复/准时报告与原合同其余读数；换回失败或缺段记失败/证据缺失，不能以首段通过代替。第二调用的 AC-25 不采用；AC-25 仍只用第一调用原 S2→S4 保持窗。AC-22 两次 S4 点击仍按全会话原合同统计，不重复计数；原真值隔离、阈值、参数与剧本不变。
4. 只写未来操作说明，本次不得执行两次评分或启动 B。实现提交后直接交 Review，按 workflow §4.4 阻断 finding 回归通道，在原复核文件“回归核实”小节定点复看 §7 上述具名行，核修前缺段/修后两段齐备；是否闭合及终局 verdict/机读通过指针仅由复核角色写。本次不将操作单加入 PLAY_GOVERNING 冻结文件集；若实际改动超出该文档路径，必须停报、重新按开轮资格处理，不能借本裁定免轮。

CAPTURE:A:1 候选 3/3、停点全套 3/3、真实构造 6/6 已用尽；路径 (ii) 不创建代码新候选、不加载模型、不跑全套，仅文档/补记仍按原 A 磁盘义务处理。**路径 (i) 本轮不授权；engineering-workflow §6 窄修替代不适用**：`analyze_play.main` 是 K4 Play 对外指标路径，触及其两段汇总不满足“不触及对外指标路径”的前提；该通道也不自动增加候选额度。若用户另选代码闭合，须**上交用户**另签具名新候选、停点全套及构造等所需维度后才实施，原余额不能转用。本轮推荐 (ii)，理由是现有函数/CLI 已支持任意起点和不限末端，足以补齐原 AC-23，无需模型或代码新候选；不是放宽验收。轮 3 如因获批代码修复开启，范围仍为冻结集、RED_LINE、修复触及行 CLASS_1/2，终局通过或回用户；本项无可用 D2b 信封。

#### IR-R1-1…5 读法裁定

| 项 | 裁定 / 唯一读法 | 依据与边界 |
|---|---|---|
| IR-R1-1 | 确认：取提交事件后首个按新绑定授权的帧；追平时可为提交帧，已处理时不回写旧效果。 | 沿 C2 IR-C2-1，按 event_seq 归属，两段均用同规则；S2/换回未绑定不记通过，NOT_EVALUABLE 不等于验收满足。 |
| IR-R1-2 | 确认：缺真值 FOLLOW 帧留分母、不计带内、记 EVIDENCE_MISSING；S2 缺真值整项证据缺失。 | 账本 10-10 IR-C2-5 与 AC-25；未给 S4 的窗到 max(最后授权帧, 最大真值帧) 含末帧，hold_window 末值为该值+1。由实现角色按 R2 §3 CLASS_3 逐字补正 handoff §R2，不扩大缺失删失。 |
| IR-R1-3 | **上交用户；未确认扩大 AC-22 分母。** 现行合同仍为全部“发出的”点击，含发出后被拒、超时、UNKNOWN、未绑定；工具把未发送的畸形 click_refused 也记 FAIL，是偏严附加口径。 | USER-4A 保留原点击目标；偏严可能把原合同通过改成失败，同样改变用户验收目标，接受角色不能代拍。点击工具序号含拒收行与验收分母是两件事，查 S2/S4 序号仍须按实际全行序。用户答复前不把较大分母的总 FAIL 直接认作 AC-22 合同 FAIL，也不宣称口径已获确认。 |
| IR-R1-4 | 确认：缺原键同帧 prior 记 EVIDENCE_MISSING，留分母、不计通过；AC-17 R-1 暂定描述只统计 PASS/FAIL 并单列缺失。 | 账本 10-10 IR-C2-5；不改下一原始检测、阈值、原键或删失判据，不将暂定读数作为门或生存概率。候选 2 九项读数不变。 |
| IR-R1-5 | 确认：段末未结束失观测照列 ended_at=None；截止在段内而未报告/撤权记不准时，截止在段外记 None。 | AC-23 段语义；换回段以会话末为末端，不能漏掉会话内到期事件；段外未观察到截止不能泛称该失观测已修复/已准时。 |

**上交用户 IR-R1-3 推荐：保持原“全部发出的点击”验收分母，页面未发送的畸形拒收单列描述；理由：保留已定目标，偏严也不能静默换掉失败判据。** 用户若选择将其也纳入 AC-22，须明确这是扩大分母的目标变更，另由接受角色追加合同修订；不是本轮已授权。若保持原分母，现有工具较大分母读数须与合同分母明确分列，如何落实及是否需代码/额外额度待答复后确定，不借本轮 R2-1 文档路径授权指标代码变更。

#### 非阻断债、补记与交接

R2-2 按 R2 §3 不可达判据维持 SCOPE_GAP/OPEN，来源、触发、影响和未来承接已写 `docs/implementation-status.md`「范围外已知缺陷」；R1-4 OPEN 保持。本轮不扩大 AC-15 到无端口输入行删除检测，不签任何 release。R1-1…3 红绿闭合及 §R3 候选 3 不重跑正式回放的附议沿 R2；AC-17/18/19 是候选 2 运行读数，不改称候选 3 产物；AC-22…26 仍 NOT_RUN、B 未签 0，无 UNITY_NA/DONE。

实现角色下次提交须按复核 R2 §0 原读数补记资源账：副本峰值 **80,961,536 B**（已删、净新增0仍按峰值记）及会话暂存 **17,797,120 B**，合计 98,758,656 B；分别保留来源/轮次并避免重复计入，按既有候选归属，不新增候选号。同时补核既有收尾提交 git 对象及本轮后续文档等磁盘义务，未知不假记为0、不据现存账推完整余额；账内 3 GiB 字段不构成超出用户 3 GB 的授权。本接受角色无 `docs/evidence/*-ledger.json` 写权，本轮未补账。

当前 Owner = 用户，等待 IR-R1-3 目标答复；接受角色落实答复后交 Implementation 补操作单/CLASS_3/账，再直接交 Review 回归核实。R2-1 仍未闭，不放行依赖停点的后续动作。Overall 保持 IMPLEMENTED，R2 原 REWORK_REQUIRED 不改，冻结集不增项；本裁定不签独立结论。C2 关注的当前处置沿 R1/R2 原核实与上述两条债，不再把历史“待核”当作下一角色的新义务。

open_items: R2-1, IR-R1-3

### IR-R1-3答复落实（2026-10-10，Acceptance）

owner = Acceptance；范围 = 账本 2026-10-10「用户答 IR-R1-3：AC-22 保持原『全部发出的点击』分母，未发送畸形拒收单列」、上节冻结裁定、复核 R2、handoff §R2、操作单 §7 与评分器直接关联函数；状态 = 用户答复已落实，交 Implementation 文档补正。上节原文保留为当时裁定，其中 IR-R1-3「上交用户／待答复」及 Owner 由本节承接；R2-1 冻结范围与路径 (ii) 不变。本轮未执行测试、模型、评分、重放、Play、板端或下载，consumed={}；不写用户账本、实现或复核文件。

#### AC-22 修订 1：原分母与现有工具读数分列（解释既有条款）

**唯一读法：分母仍为全部发出的点击，页面未发送的畸形拒收单列描述、不计入 AC-22 判定。** 依据为上述用户答复；不扩大 AC-22 分母、不改 e2e ≤ 1 帧与全部 PASS 的判据。发出后被拒、超时、UNKNOWN、未绑定仍留合同分母；受理子段与墙钟仍分别报告，不能替代 e2e。

**指定不改代码的文档取读方式。** 只读核 `tools/eng_capture/analyze_play.py::click_latency/main` 与 `tools/eng_capture/click_web.py::ClickApp.click`：工具把原日志 `click_received` 与 `click_refused` 按行序合为 `AC-22.rows`，每行保留 `index`、`click_id`、`request_id`、`bound`、`e2e_frames`、`verdict` 等；畸形分支在调用提交器前写 `click_refused`、`reason=malformed_click` 后返回。因此原日志和逐行输出足以分列，无需改 `analyze_play`、过滤输入或另跑评分。

操作单 §7 必须规定未来取读步骤（本次只补说明，不执行）：

1. 保留第一调用完整输出及原点击日志，原样单列工具较大口径的 `denominator`、`verdict`、受理子段汇总与逐行记录，标为「含未发送畸形拒收的工具读数，非 AC-22 合同判定」。第二调用沿用相同点击流，AC-22 不再计一次。
2. 按原日志中 `kind in {click_received, click_refused}` 的实际全行序（1 起）与 `click_id` 对照输出 `index/click_id`。**仅剔除原日志明确为 `click_refused` 且 `reason=malformed_click` 的未发送行**；逐行列其原序号、click_id、拒收原因，并另列畸形行数。不凭 `refused=True`、`request_id=None` 或 FAIL 一概剔除；其余被拒、超时、UNKNOWN、未绑定行全部保留。
3. 合同分母 = 工具行数 − 上述已核未发送畸形行数；另列保留行的原序号/click_id、绑定状态、e2e、受理子段、墙钟及 PASS/FAIL 数。非空合同分母下，保留行全部满足已绑定且 e2e ≤ 1 帧才是 AC-22 PASS；任一保留行未绑定或 e2e > 1 帧为 FAIL。无发出点击记 NOT_EVALUABLE、不计通过；日志缺失、身份或行数无法对应记 EVIDENCE_MISSING、不计通过，不借剔除减少未知分母。原始工具总 FAIL 不直接等同合同 FAIL。
4. `--s2-click/--s4-click` 与 S4 换回序号仍按未剔除的原全行序核定，畸形行仍占工具序号；不能用合同分母重编号或改工具输入。S2/S4 目标身份与绑定事实须从现场记录和提交/授权日志核实，不能由序号推断。

这解释并落实用户选择，不增加验收义务或资源额度。若实施时发现逐行输出与原日志不能支持上述分列，必须停报；需要改 `analyze_play` 时触及 K4 对外指标路径，CAPTURE:A:1 候选 3/3、停点全套 3/3、构造 6/6 已用尽，engineering-workflow §6 窄修替代不适用，须**上交用户**另签具名新候选、全套及所需构造等维度。推荐仍先保留原工具与日志并完成文档分列，理由是现有字段已可追溯且不需新代码候选；不能自行扩额或把代码变更包装成文档补正。

#### 合并交 Implementation 的文档任务清单

| 文件 / 具名位置 | 本次任务与完成边界 |
|---|---|
| `docs/evidence/P1-ENG-CAPTURE-001-play-ops.md` §7 | 同批落实上节 R2-1 路径 (ii) 的两次调用及本节 AC-22 分列。第一调用用已核 S2 与 S4 首次点击序号；第二调用同 session-dir/click-log/truth，`--s2-click <S4换回红车且已绑定的原序号>`、不带 `--s4-click`，输出另存。AC-23 同时取两段修复/准时报告及原合同其余读数，未绑定、无授权帧、缺段不计通过；第二调用 AC-25 不采用，AC-25 只取第一调用原保持窗，AC-22 全会话只统计一次。保留原阈值、参数、剧本与真值隔离；本次不执行评分、不启动 B。 |
| `docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` §R2 | IR-R1-2 按复核 R2 §3 CLASS_3 逐字补正为：「未给 S4 时保持窗至 max(最后一个已授权帧, 最大真值帧) 为止（含该帧；`hold_window` 末值记其 +1），修前到最大真值帧且不含该帧」。IR-R1-3 原扩大分母读法须注明已由本节用户答复落实承接，指向 §7 的原工具／合同分列，避免继续当现行指令；不改已有数字、运行读数或 disposition。补文档改动范围与未执行声明，供定点复看。 |
| 同项 handoff 资源小节与 `docs/evidence/P1-ENG-CAPTURE-001-ledger.json` | 按复核 R2 §0 原读数补记副本峰值 **80,961,536 B**（已删除、净新增0仍记峰值）及暂存 **17,797,120 B**，合计 **98,758,656 B**；分笔保留来源/轮次、核既有事件避免重复，归既有候选、不新增候选号。补核既有收尾 git 对象及后续文档等磁盘义务，未知不假记0，不据未完整账宣称余额；用户上限仍为 3 GB，账内 3 GiB 字段不授予额外空间。接受角色本轮未补账。 |
| `docs/current-status.md` 本项交接 | 实现完成上述文档与资源补记、提交推送后直接交 Review；交接只指向已补 §7、handoff 具名说明及资源账，不重复铺陈。不得声明 R2-1 已独立闭合或停点已放行。 |

**完成后直接交 Review** 在 `docs/reviews/P1-ENG-CAPTURE-001.md` 原文件「回归核实」小节定点复看操作单 §7 两段齐备、AC-22 原日志对照与分列、handoff 补正及资源补记；沿上节 `NOT_MECHANIZABLE` 回归通道，不经新 C 轮、不新编复核轮。终局 verdict 与机读通过指针只由 Review 写；本轮不签独立复核、verdict 或 release。允许路径限上表文档及资源账补记，若实际改动超出必须停报，重新按开轮资格与预算处理，不借路径 (ii) 免轮。

IR-R1-3 用户待决已解除；R2-1 仍未闭，R1-4/R2-2 OPEN 债保持，Overall `IMPLEMENTED`、Lifecycle `ACTIVE`、R2 原 `REWORK_REQUIRED` 不变。AC-22…26 仍 NOT_RUN、B 未签0，无 UNITY_NA/DONE，不放行依赖停点的后续动作。

open_items: R2-1

### C2@K1K2K3K4（2026-10-10，Acceptance；现行核对）

**核对结论：不满足，附未决关注照交新鲜上下文 `R1@K1K2K3K4`。** C1 已用掉本停点唯一一次退回，本轮不再退回，不签独立 verdict 或 REVIEW_BLOCKED。按本次用户要求保留下面 C1 原文作为历史；C2 是现行核对。owner = Acceptance；范围 = 派发指定的完整候选 2 diff、候选 1→2 返工增量、直接关联代码、现行合同与逐条证据；候选与基线身份从本派发和 git 运行时解析。已核两次返工提交的派发尾注及末提交仅更新证据/账/状态的事实。未跑测试、模型、Play、板端或下载，consumed={}；不改实现、AC、用户账本或信封。

证据简称沿用 C1：H = 同项 `-K1K2K3K4-handoff.md`；T = `-tests.log` / `-tests-baseline.log` / `-focused.log`；P = `-replay.md`；L = `-ledger.json`（均在 `docs/evidence/`）。另只读 P 所指本机原始 JSON/JSONL 与预登记文件，未执行评分器或 reducer。下列“满足”只表示本轮合同核对主张，待 R1 独立核实；“不满足/证据缺失”不定 finding 分级。

#### C2 — C1-1…5 与 RR-1 落实

| 项 | 核对 | 返工与证据对应 / 未决边界 |
|---|---|---|
| C1-1 | 证据缺失 | `same_frame_prior/post` 核键、sensor/library 帧、phase、valid，prior 另核 S；匹配观测、点击、修复提交的主要反例已覆盖，缺 prior 不再借 post 发预测。H §0、T 修前红/修后绿对应真实新用例。但 `_assess_original` 的 lost/缺行早退先于 post 校验，H 的“任一 post 不合格均 HOLD”还缺该路径证明，见 C2-P1。 |
| C1-2 | 满足 | 原始检测与各键同帧 prior 落盘；评分先找缺口后首个真值 IoU≥0.5 的原始检测，再取注入前原键 prior，不再要求 accepted OBSERVED、不随修复换键。H §0、ScoringTests 与 P §4 九项原件对应。缺 prior 的额外删失读法不予扩大，见 IR-C2-5。 |
| C1-3 | 满足 | `run_new_arm` 入历史→click→on_frame；本帧已提交跳过重复②–④，状态/效果版本一致检查已加；会话追平点击在该帧授权前提交，日志按 event_seq 归属绑定。具名修前红/后绿对应。RR-1 依账本用户答复落实，保留两点剧本和557–600，不删首帧、不平移窗口。 |
| C1-4 | 满足（具名限速路径） | `note_control_limited` 先写输入，reducer 有同名分支；新进程全字段逐条相等的红绿对应。四类端口失败亦已记录/重放，弥补 C1 预复核关注；输入缺行的总体 AC-15 仍不满足，见 C2-P2。 |
| C1-5 | 不满足 | 每帧交模型前原子共账、崩溃 in_flight 拦截、候选归属/事件和/零维度检查与红绿对应。但逐维超限总检查与收尾预留未齐；历史磁盘峰值 UNKNOWN 未核清便继续候选2消耗，不能据现存字节推完整余额，见 C2-P3 与资源核对。 |

#### C2 — AC 逐项核对

| AC | 核对 | 候选与证据对应关系 / 主张边界 |
|---|---|---|
| AC-1 | 满足 | 类别策略、缓存键、capture 工厂与 ClassPolicyTests 对应；规格/权重及旧缺省保留。H §2、T。 |
| AC-2 | 满足 | 中心补偿 H/J、速度与宽高不变、旧函数逐元素比较、GMC 来源闭集与具名测试对应；本次返工未动。H §2、T。 |
| AC-3 | 证据缺失 | 双阶段快照生产、捕获/兼容历史与桥隔离保持；消费同帧核验主要路径已补，lost+坏 post 边界见 C2-P1。H §0/§2。 |
| AC-4 | 满足 | TaskSpec 不可变、origin/counter 矩阵、拒绝不推进与 TaskSpecTests 对应。 |
| AC-5 | 证据缺失 | 锁存/到期优先/竞争矩阵及有效 prior 门对应；原轨迹未 tracked 时 post fail-closed 的普遍主张待核，见 C2-P1。 |
| AC-6 | 满足 | 连续证据、激活/库键、到期优先、原键同帧 prior 与候选有效 post 提交对应 RepairTests；IR-C2-2 保持原截止。 |
| AC-7 | 满足 | 事务快照/半改/完整恢复读回、旧 coasting、成功才关 episode 与 CommitTests 对应；follow 闭集保持，四种失败新进程重放新增用例对应。输入完整性另见 AC-15。 |
| AC-8 | 满足 | AuthorizationTests 对应 G 一致性、原八行首命中与合法变差边；不把纯函数总表证明外推为上游 KF 输入合法。IR-C2-4 见下。 |
| AC-9 | 证据缺失 | 缺/坏 prior 不发预测云台且 HOLD 的会话反例已补；预测取原键同帧 prior，云台中心/机体框底隔离保持。lost+坏 post 的行为与主张待核，见 C2-P1。 |
| AC-10 | 满足 | 帧计时、积压、到期、原因闭集前缀及精确追加与 ReportTests/桥测试对应。 |
| AC-11 | 满足 | StopTests/回滚失败会话路径对应安全 HOLD、撤权、旧效果作废、单写者和后续速度禁发。 |
| AC-12 | 满足 | sha/历史链/歧义/纪元/compat 拒绝与 ClickTests 对应；新增追平顺序反例对准 C1-3。受理子段不替代尚未运行的 AC-22 e2e。 |
| AC-13 | 满足 | language-off 零 worker 与动态基线兼容逐帧比较（lost/退化/非空 coasting）证据保持；LanguageWorker 本次零 diff。 |
| AC-14 | 满足 | 点击页权限、像素/原字节 sha、退出码、UNKNOWN/seal、on_reply 记录器异常及旧 argv 两处闭集测试对应；本次返工未动。 |
| AC-15 | 不满足 | 限速和四类端口失败的原件重放已补；但 ReplayPort 缺 port 行/队列耗尽时默认成功或本地回读，没有完整性拒绝，见 C2-P2。正常原件重放成功不覆盖缺输入。 |
| AC-16 | 满足 | 冻结路径闭集保持；score_ 真值隔离、登记 clicks 传两臂与 SelectionInputIsolationTests 对应，不以真值生成初始化。 |
| AC-17 | 满足 | RR-1 已答；原报告现象门561–565复现、新臂557–600共44帧、失败/误绑/BROKEN/状态效果不一致均0，与 P §1–2 相符。557 key=11/episode=2、记录/效果version=2、瞄准新中心，最小IoU 0.761；保留候选1错误读数原文。 |
| AC-18 | 满足（本次九项均可评） | 四个 m 的 on/off 与强制换库键共9项，原报告均 PASS；下一检测562/563/565/567，原键11 prior 的IoU约0.804–0.844；到期后不续跟、报告563/撤权565、注入实际新键13分证。不可推广额外 NOT_EVALUABLE，见 IR-C2-5。 |
| AC-19 | 满足 | 六基72序列/每格12/两臂各1152推理、Wilson/删失/误跟与原报告及 P §5 相符；新15/72、基线34/72，六格非劣化只限本次，基26两臂全断轨限制保持。 |
| AC-20 | 满足（修订2/3的分列口径） | T 全套2656、28 failures/34 errors/56 skips；静态比较62条失败头与候选1逐条一致（基线61、IR-2预期1），新增回归0，不称全套全绿。IR-2仍只因三获批路径，冻结测试零 diff；本候选全套1/1、构造2。资源流程另列，不由此证明AR1-6。 |
| AC-21 | 满足（操作单草案） | play-ops 含动态 HEAD/porcelain、Air预检、四段剧本、STOP逐码/收尾、运行限额；B未签0，无Play证据。未来读数工具的未决边界见 C2-P4，不提前判 AC-22…26。 |
| AC-27 | 满足 | 用户账本与本人 consistent 确认对应；现算六张样帧 sha 均一致，剧本 sha 一致，正式回放前确认，不代签人眼结论。 |
| AC-28 | 满足 | 用户六个 k−1 预登记点、具名登记/剧本/原帧 sha 与固定六基一致；两臂每基12次复用，真值改变不改选择输入与缺点/错帧拒绝用例对应。 |

#### C2 — IR-C2-1…5 裁定（既有合同的唯一读法，不追加 AC）

1. **IR-C2-1：确认，限于所述两种请求时序。** k 尚未处理时先在历史入 k 后提交再授权。k 已处理且本请求当时尚未挂起时，提交取消费时历史头，先前已发送效果仍属旧版本，新绑定首个效果在下一处理帧；不能回写旧授权/效果、也不凭帧号归到新绑定。不要求为这个事后请求补发同帧第二效果。已有待处理请求仍须在相应帧⑤前消费，不借该例外延期；RR-1 回放仍按请求先挂起、①先提交建模。AC-22 全部点击分母与端到端≤1保持，尚无B实测。
2. **IR-C2-2：确认。** 点击头 post 缺失/错帧/错phase/无效即拒绝、零业务状态变化，旧目标继续按自身合法性授权；修复候选 post 不合格只表示本帧不提交，既有证据及原截止不改、不延寿，不凭坏 post 初始化。H/T 已有相应反例；不泛称旧目标必然仍可 FOLLOW。
3. **IR-C2-3：确认。** 未接受原观测的帧使用原键同帧 prior（预测与本帧补偿后），不能把被拒量测吸收后的 posterior 当预测。该读法不扩为 KF 全历史重放，也不豁免 prior 对齐/有效/S可逆检查。
4. **IR-C2-4：给唯一读法。** 仅在 G 一致、前四行未命中且本帧确无可用几何中心时，geometry=invalid 命中行5 GEO_REJECT，HOLD/不发可确认；KF失败具体缘由应保留在输入/事件中。若几何仍有效而 covariance=kf_invalid，则沿原表命中行8，不将所有 KF 失败一概改记 GEO_REJECT；域外输入仍先一致性拒绝。此处不改原因闭集或优先级。
5. **IR-C2-5：多检测选法确认；缺 prior 删失不确认、上交用户。** 在时间上首个符合真值IoU≥0.5的原始检测帧，多个符合检测取真值IoU最大者，可作为独立评分的确定读法，不允许跨到更晚帧，也不改变在线接受。该帧若缺原键同帧 prior，应记**证据缺失**，不自动扩为合同允许的 NOT_EVALUABLE，更不能从可评分母移除后宣称通过；无符合检测才按原删失条件处理。本次9项 prior齐全，不影响现有读数。若要采纳实现提出的额外删失须用户决定；**推荐保持原检测/分母/阈值，先补证据或保留缺失；理由：缺内部预测证据不等于没有真实观测，扩大删失会放宽用户已定目标。** AC-24复用同样读法，P §4和工具docstring的额外删失表述只是待核主张。

#### C2 — 资源与四项稳定停点核对

L 事件金额与全部 counters 的和现核相等，in_flight 无未结项：候选2/3；回放加载累计3/6（候选1=2/2、候选2=1/2），推理7924/16500（每候选3962/5500）；全套2/3（每候选1/1），构造4/6（各2）；开发期真实加载8/20；账记磁盘47,019,465 B，ID/Unity/Play/板/API/云/下载安装各0。已记录回放146.18 s、全套549.988 s均在30 min内。**这些已记录值未超 CAPTURE:A:1；完整磁盘用量及执行流程符合性仍为证据缺失/不满足。** L 将3GB写成3GiB，不能据其较大字节数获得额外授权；现有记录低于两者不证明完整峰值。

H §6 补核30,380,346 B涵盖 scratch/docs/代码/git/pyc的现存保守上界，但明确“一次性worktree历史峰值UNKNOWN，不据以推余额”；随后仍启动候选2正式回放/全套，与 AR1-6 的 UNKNOWN不得推余额及 S-A-BUDGET 停依赖相悖。H §0已承认早期focused启动未核账等偏差，§6“所有消耗步骤启动前核账”不采纳为无条件主张；补记不追认。L 的旧 not_counted 说明和收尾提交本身对象未补账亦不能当完整核清。接受角色不改 L、不豁免未知、不签新额度。

**上交用户 R-C2-RESOURCE：推荐依既定 S-A-BUDGET 停止后续模型/回放/全套及其依赖消耗，保留既有读数与偏差；先只读核清可证明的历史磁盘上界，无法核清则由用户明确处置 UNKNOWN，不由现存余额追认。理由：预算信封不能由接受角色扩大，已签合同将未知用量作为停止条件。** 本次 C2/R1静态交接照行，B继续未签0；这不是再退回实现，也不是独立复核门判定。

| workflow §4.3.1 条件 | 核对 | 理由 |
|---|---|---|
| 1 范围/接口冻结 | 满足 | 候选2末提交后代码未变，RR-1沿用户原目标，IR裁定未扩接口/门/信封；IR-C2-5额外删失未纳入合同。 |
| 2 相称测试/编译通过 | 证据缺失 | 已记录具名红绿、全套新增回归0、正式9项读数成立；C2-P1/2/3边界仍未对准，不能据 H §8 一概认定四项全成立。 |
| 3 已知Unity失败修复 | 满足（阶段A不适用） | 阶段A零Unity，B未执行，不签UNITY_NA、不解除B门。 |
| 4 状态/候选/范围/风险齐备 | 满足 | 已有候选提交推送及H/P/T/L；本批同步C2未决与准确复核交接。范围/风险完整不替代通过。 |

#### C2 — 预复核关注项（待核实主张，不是独立 finding）

- **C2-P1（AC-3/5/9、AR1-2）：** `target_manager._assess_original` 在 row缺失/lost/out_of_frame/removed/ended 时先返回，`kf_ok`仅由prior有效决定，未运行same_frame_post；`_miss_original`遂可用prior预测。H/T只证匹配坏post与lost坏prior，未证lost有效prior+错帧/无效post。R1需核清该早退是否违反终局“post无效同样撤权”的范围，并核云台/HOLD，不只非FOLLOW；本轮不自行改合同豁免。
- **C2-P2（AC-15、§3.8）：** `ReplayPort._next/follow/restore_binding_state/binding_state_matches/pointer` 缺行退回成功/本地模型；`replay_tm_inputs`先将全文件port按种类入队，未核耗尽/残留或调用所处请求/帧的一致性。删去必需port行且剩余行sha合法时不能以正常重放成功证明缺引用拒绝；四种完整失败脚本通过不能排除缺行漂移。旧格式回退不是本项缺输入的默认成功许可。
- **C2-P3（C1-5、AR1-6）：** `ledger.problems`核类型/事件和/候选总数，未遍历CAPS核全部现有总量与每候选上限；`check_launch`只核needs所列维度，其他维度自洽但超限的账仍可能启动。`replay.ledger_balance`磁盘need=0只要求余额>0，未预留输出/收尾；`formal_run.run`先写工件后record磁盘，record超限先拒且不写实际超限量，S-A-INPUT早退无磁盘record；CountingModel仅预测前核墙钟，非推理阶段与收尾未覆盖整次30min。需核其启动/失败收尾是否真正履行原逐维/实际共账义务；不以本次实际时长短替代边界证明。
- **C2-P4（未来B读数，AC-22…25）：** `analyze_play.click_latency`用click_received与submit_begin数组索引配对，页面本地拒绝无submit_begin时可错配后续请求；wall_s始终None。`main/score_red_car_loop`未显式限定红车S2–S4范围；`score_body_band`忽略缺真值的FOLLOW帧却可能计入inside，未输出约定非FOLLOW帧数。R1核这些是否已影响操作单/可用工具主张；B仍NOT_RUN，不把静态工具存在当实测通过，不为本轮增加AC或消耗。

**下一角色：Review，新鲜上下文 `R1@K1K2K3K4`。** 复核范围按本派发候选2完整diff运行时解析（含直接关联代码、完整合同、H §0/§8与本C2核对/IR/资源/关注项）；本停点不再经核对退回。是否满足开轮自证、如何给独立结论均由复核角色决定，本轮不签REVIEW_BLOCKED或verdict；未闭资源用户入口随交接保留。

open_items: C2-P1, C2-P2, C2-P3, C2-P4, IR-C2-5, R-C2-RESOURCE

**C1@K1K2K3K4（2026-10-10，Acceptance；最新一版）：不满足，使用本停点唯一一次核对退回，交 Implementation。** 本轮重读派发指定的完整候选 diff（范围见实现 handoff 文首、git 派发提交）、直接关联代码、AC/终局/IR 合同、原始证据与资源账；未跑测试、模型、Play、板端或下载，consumed={}。候选身份从 git 与派发记录运行时解析，不另抄 SHA。“满足”仅是合同核对主张，仍须新鲜上下文独立复核；本轮不签 verdict，不新增或改写 AC、帧集、参数或信封。

### 逐项核对

证据简称：H = `docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md`；T = 同项 `-tests.log` / `-tests-baseline.log` / `-focused.log`；P = 同项 `-replay.md`。逐行核 H §2 的具名证据指针及真实代码/测试，决定性对应如下。

| AC | 核对 | 候选与证据对应关系 / 未闭问题 |
|---|---|---|
| AC-1 | 满足 | `_detect`、缓存键、capture 工厂与 `ClassPolicyTests` 对应；缺省不变，冻结规格/权重零 diff。H §2、T。 |
| AC-2 | 满足 | `apply_pose_center` 的 H/J、宽高及其速度不变、旧函数逐元素比较与 `PoseCenterTests` 对应；GMC 闭集精确追加。H §2、T。 |
| AC-3 | 不满足 | 两阶段快照生产、capture/compat 历史及桥隔离对应；消费未校验 prior 帧/phase，无效 post 仍可授权，违反终局修订，见 C1-1。 |
| AC-4 | 满足 | 不可变 TaskSpec、origin/counter 矩阵与 `TaskSpecTests` 对应；拒绝不推进，接受新任务与 acquire 分开。H §2、T。 |
| AC-5 | 不满足 | 锁存、到期、竞争裕度矩阵对应；同帧有效 prior 前提未落实到消费，见 C1-1。 |
| AC-6 | 不满足 | 连续证据、激活、到期优先、无键不提交及配置拒绝对应；修复门仍能消费错帧/错 phase prior，见 C1-1。 |
| AC-7 | 满足 | `CommitTests`、真实 ResidentCore 快照/恢复及兼容脚本对应半改、读回失败、旧绑定保留；follow 调用点闭集对应。H §2、T；失败端口重放充分性见预复核关注。 |
| AC-8 | 满足 | `AuthorizationTests` 与纯函数可达域、首命中、合法变差边对应；防御域和非空 age 带分证。不将该证明外推为 KF 消费安全（C1-1）。 |
| AC-9 | 不满足 | 通道/P_center/显式 HOLD/框底量测测试对应；缺 prior 但有效 post 仍可发预测云台，无效 post 原匹配仍可 FOLLOW，见 C1-1。 |
| AC-10 | 满足 | `ReportTests` 与帧计时/积压/到期边界对应；旧原因完整前缀动态解析、精确追加。H §2、T。 |
| AC-11 | 满足 | `StopTests` 与会话回滚失败测试对应安全通道、版本撤权、单写者 STOP/STALE、无后续速度效果。H §2、T。 |
| AC-12 | 满足 | `ClickTests` 对应 sha/历史/歧义/链断/换 episode/compat 拒绝与受理子段；不替代未运行的 AC-22 e2e。H §2、T。 |
| AC-13 | 满足 | `LanguageOffTests` 对应零 worker；`LanguageCompatTests` 在动态接受基线导出上逐帧比较，含 lost 出画/退化与非空 coasting。H §2、T。 |
| AC-14 | 满足 | `test_capture_click_web` 与监听/nonce/Host/Origin、字节 sha、退出码、seal、两处 operator_web diff 对应；旧 argv 意图保留。H §2、T。 |
| AC-15 | 不满足 | 新进程脚本重放、sha/缺引用拒绝对应正常路径；servo_clamp 产生的 `control_limited` 没有重放输入，后续 event_seq 亦漂移，见 C1-4。 |
| AC-16 | 满足 | 禁改路径零 diff；滚转 clicks 只由登记点参数传入两臂，真值不生成选择输入；`test_capture_isolation` 与 `RollSelectionInputTests` 对应。 |
| AC-17 | 不满足 | 准入、两点剧本、动态基线及现象门对应；557 混合新绑定与旧效果，现 PASS 不采纳（RR-1上交用户、C1-3）；R-1暂定读数还依赖错误 AC-18 评分。 |
| AC-18 | 不满足 | 四种 m/off 对照及实际强制换键对应；下一真观测被换成 accepted OBSERVED，不能支持 m=4/6 的 NOT_EVALUABLE；修复后还可能比较新键 prior，见 C1-2。 |
| AC-19 | 满足 | 六基/72序列/每臂1152实推理、删失、六格Wilson/n对应 P §5 与原报告；六格非劣化仅本次描述，不提升主张。 |
| AC-20 | 满足 | 读完 T 全套与基线归因：2639 tests，28 failures/34 errors/56 skips；61条基线已有、三获批路径导致的1条IR-2预期失败，本项新增回归0。冻结测试零 diff，后续 scenario 断言只读另核；不称全套全绿。构造2，候选1全套已用尽。 |
| AC-21 | 满足 | `-play-ops.md` 含动态 HEAD/porcelain、Air预检待填、覆盖1500、T_sess/f0、四段剧本及12 STOP；B未签0，草案不是执行证据。 |
| AC-27 | 满足 | 用户账本、人眼确认文件及4+2样帧对应，六图现算sha均相符；正式回放前已确认，不重新代签。H §4.1。 |
| AC-28 | 满足 | 用户六点/k−1原帧/登记人/sha与固定基帧计划对应；两臂每基复用12次，测试覆盖缺点/错帧/sha与真值改变不改选择输入。H §4.2、P §5。 |

### 窄修与实现读法裁定

- **F-1：合同内。** 导出根下只读链接规格相对文件，维持基线源码与权重身份、零额外加载；`BaselinePackageTests` 对准缺陷。
- **F-2：保存前后状态在 C10 内；据此改判 PASS 不确认。** `run_new_arm` 实际 step→on_frame/授权→click，与 docstring 及 H 的“替换先于授权”理由不符，见 RR-1/C1-3。“回放前修”不代替合同符合性。
- **F-3：合同内；RR-2 确认。** JSON 被加载器拒绝仍计首次尝试，核身份后加载权重属同候选一次崩溃重载；取严格的候选1加载2/2，不换号释放次数。成功报告 model_loads=1只描述成功进程，失败尝试仍共账；候选≤3与真实返工diff要求继续生效。
- **F-4：合同内补齐暂定读数，非修复红绿；F-5：合同内测试夹具隔离。** 均在停点全套前；不归零真实账本，不据读数改参数。
- **RR-1：上交用户，当前不采纳 AC-17 PASS。** 原工件557的 pre_click 为静止车 key=3/旧框，帧末改写为红车 key=11/episode=2，但 effect_seq=558仍瞄旧框、version亦属旧绑定。取旧记录为FAIL（误绑1帧），只取新绑定为PASS，接受角色不替用户选择以放宽目标。**推荐保持557–600与原两点剧本，按§3.3①先替换请求再授权，采用同一提交后状态/效果的帧记录；理由：保留用户起点与门值，避免只换记录标签将旧目标效果算作红车成功。** 若用户选择仅考核帧末绑定状态，须明确是否容许该帧已有旧效果；本轮不代写授权、不删557、不平移窗口。未决不妨碍先修其他既有合同缺陷。
- **RR-3：仅接受为带n的暂定描述，不作门/标定。** 两种残差明确几何点/水平距离，代码排除 pre_click 混合帧（n=43）合理；“误TENTATIVE”仅真值仍可见时进入窗口的代理计数，不是身份误判率。最大可评通过缺口可作本组样本暂定R-1描述，不是概率生存界；现AC-18偏差使其n/下界证据失效，随C1-2重算，保留旧读数。

### 具名退回项

以下仅履行既有合同，不新增AC，不定独立复核 finding 分级。

1. **C1-1 — KF 消费 fail-closed（AC-3/5/6/9；终局AR1-2）。** `resident_core.py:307` 只核键；`target_manager.py:1566/1640` 消费未核sensor/library帧及phase，`motion_size_gate:516`只核valid。`_accept_original:1597` 在post缺失/无效时仍刷新t0、标OBSERVED，`authorization_inputs:1756` 再按within放行；缺prior时 `_miss_original` 还可凭有效post发预测云台。落实已明确的错帧/错阶段/缺失/无效撤权，以原匹配成功、lost、修复相关路径focused反例证明t0/提交及云台/HOLD行为。现missing-prior测试只断言非FOLLOW，不能证明云台不发。
2. **C1-2 — 恢复AC-18检测判据（含RR-3）。** `replay.py:686–712`用accepted OBSERVED/框代替“缺口后首个真值IoU≥0.5的检测”；BROKEN不表示检测不存在。保存/读取实际策略后原始检测及原预测来源，按原时间窗独立评分，即使不接受观测也可评；修复后不能换为新绑定键自己的prior。补对准两类反例的零模型回归，分列不续跟/注入成立/预测IoU，纠正P/H与暂定读数；缺所需落盘输入就报证据缺失，不编造原值。
3. **C1-3 — 点击/授权顺序与工件一致性。** `replay.py:475–495`先生成旧效果，再将click后信念盖到记录。按既有§3.3①/§3.5处理提交帧，保持同帧/episode/version的状态与效果一致；保留原工件，不补写新effect冒充已发生。RR-1评分读法按上方用户入口，未答不宣称现候选AC-17 PASS。
4. **C1-4 — 限速路径可重放（AC-15、§3.4/3.8）。** `track_loop.py:868–872`经servo_clamp调 `note_control_limited`，`target_manager.py:1821`只发事件、不写输入；`replay_tm_inputs`无相应分支，不能重建事件及后续序号。沿现有日志接口补足可复算输入，用新进程仅输入/配置核全字段事件一致，不删CONTROL_LIMITED事件使测试通过。
5. **C1-5 — 共账与启动门（AR1-6、信封落实）。** `formal_run.run`仅在整段缓存/滚转返回后记推理，`CountingModel.predict:378`只有内存计数；中途失败/退出丢已提交帧，违反逐帧共账。`ledger_balance:942`未核候选上限/合法归属或UNKNOWN/零维度，缺字段直接异常不足以核清余额。落实已签逐维拒绝、失败不返还、崩溃耗用可追溯，不扩额度；下次消耗前核清账中已记偏差，不沿用“所有启动前核账”的无条件主张。

### 资源与稳定停点核对

账本事件金额与对应counters逐项相等：候选1；加载2/2（整批2/6），推理3962/5500（整批3962/16500），全套1/1（整批1/3）、构造2/2（整批2/6），focused8/20，账记磁盘9,086,591 B<3 GB；回放约138 s、全套549.62 s各<30 min；零维度0。**记录数值在CAPTURE:A:1内，流程符合性不满足。** 开头两次carrier focused已自记启动前未核账/未显式设环境偏差（第二次-v/重跑亦违测试输出纪律），不追认。磁盘账只列outputs根，零模型日志/临时产物是否全部共账未给完整盘点，列证据缺失，须补核原账、不用余额掩盖未知。C1-5为守卫/共账问题；成功进程数不替代整批证明。候选1不得再加载/重跑全套；真实返工候选只能用原余额并留归因，不换号规避、不借focused替代指标/决策改动应跑的全套；越界或用量UNKNOWN按STOP回用户。

| workflow §4.3.1 条件 | 核对 | 理由 |
|---|---|---|
| 1 范围/接口冻结 | 不满足 | 候选已冻结，但F-2/RR-1记录与实际授权顺序不一致，不能认定全部合同解释已落实。 |
| 2 相称测试/编译通过 | 不满足 | AC-20分列成立；KF/评分/日志失败路径未被对准，AC-17/18通过自证不足。 |
| 3 已知Unity失败修复 | 满足 | 仅阶段A、零Unity，H明示不适用；不记UNITY_NA，不解除B门。 |
| 4 状态/候选/范围/风险齐备 | 满足 | 候选已提交推送，H/P/T/账与风险已给；本轮同步退回/未决。 |

**下一停点：** 本轮不交R1；Implementation修C1-1…5、更新逐AC证据/自证，RR-1待用户。再次交 `C2@K1K2K3K4` 时只读最新完整候选，无第二次退回机会，附未决关注照交新鲜上下文 `R1@K1K2K3K4`；不由接受角色签REVIEW_BLOCKED/verdict。

**预复核关注项：** `ReplayPort`只保pointer/coasting（`target_manager.py:784`），ResidentCore快照还含designation/ended/events；半改follow与restore/readback失败是否由输入完整复原缺新进程用例（AC-7/15，勿只比较成功脚本）。`analyze_play.score_prediction_windows`亦按accepted OBSERVED寻下一观测，复用前按AC-18/24原检测定义核实。AC-19基26全断轨只保留限制，不增基帧或优越性门。

open_items: C1-1, C1-2, C1-3, C1-4, C1-5, RR-1

## 决策记录

- 2026-10-09 D1（构思，supervisor 派发）：范围取草案 §5 第一轮改动闭集，按用户 10-09 快层方向落实只移中心与收养；骨架 v3 按 §2.2 取舍，v3.1 按 §2.3 处置；AC-1…26；额度只起草。
- 2026-10-09 D2（构思，supervisor 派发）：逐条回应 D1 首退 AR1-1…7（§10）；按 USER-4A 落实诊断原件限用途准入、点击端到端 ≤ 1 帧、12±2 m 进带并保持、有限口径与三项占位；新增捕获/兼容两种会话模式、只读 KF 快照与落盘重放输入、提交/清除路径表、STOP 码表、AC-27 保真；T_pred 占位 5→4；信封补齐各维与整批封顶；新提请 (i)–(m)；待用户 U-1…U-4。零消耗。

### D1 接受裁定（2026-10-09，Acceptance）

**裁定：`REVISION_REQUESTED`，首次设计退修。** 本轮只读审查提案、主线、授权、骨架、诊断设计/结果及直接关联代码，不运行测试、模型、Play 或板端动作。§1 主线引用正确；C2 与用户「补偿只移中心、宽高不变」一致，C4/C5 的连续性修复属于用户已定的第一轮收养方向。VLM 旁路是第一轮的有界准备，不替代主线中的 VLM；不授权第二/三轮、场景、设备、下载或快层研究扩张。未接受，不进入实现；§5 各未签维度仍为 0，RECHARTER:REPLAY:1 的诊断额度不转用。

**轨道逐字裁定：本轮不准许 `Workflow: engineering-v1` 生效。** 申请保留；新 ID 与用户开项语境支持工程提案方向，但本轮未 `ACCEPTED`，按 engineering-workflow §0 fail-closed，不能据抬头采用工程轨道的放宽。D2 补齐下列合同及用户边界后再裁定；不要求作者把本工程申请机械改成研究 BC 表。本项含 K2 新控制与 K4 验收口径，用户开项只是起草授权，不能替代下列用户裁定或额度签发。

#### §7 (a)–(h) 逐条答复

| 项 | 答复 |
|---|---|
| (a) | 本轮不准许生效，见上述轨道裁定；工程定位本身与主线相容。 |
| (b) | 同意设计上合并 `K1K2K3K4`，逐项自证 → C → 新鲜上下文 R；唯一一次 Play 必须先有代码/操作单通过并被消费，签额也不能跳过。Play 产物另经 `PlayK2K4`；放行应取该停点最终有效通过轮，不锁死只能 R1。 |
| (c) | **当前不能把诊断产物直接纳入 AC-17/18/19 门证据。** workflow §4.3.2 写明「产物不进证据链、不作为任何门判定依据」，账本 RECHARTER:REPLAY:1 也逐字限制不进任何证据链。重跑新代码不自动解除输入来源限制。上交用户：推荐只授权具名原始帧/位姿/真值作为新离线回归夹具，新候选新日志独立取证，旧 Play 与旧回放结论仍为诊断、不追认 Unity 或旧门。答复前只可作诊断设计依据，不冻结为正式通过线。 |
| (d) | R1-5 的 on_reply 子路径因本项新 click 故障域而触发，AC-14 的 UNKNOWN + seal + 具名回归方向成立；须覆盖记录器自身再次抛异常也先在内存 seal、保留 request_id/已发送事实，不能靠同一失效日志证明封锁。R1-5 的 CLI kill/quiesce 收尾子路径不因本裁定销账；本项不复用计划收尾器，原债保持 OPEN，未来复用仍须承接。 |
| (e) | 同意显式运行时 `class_policy`，manifest/检测缓存同时绑定策略、`agnostic_nms` 与补偿源；冻结权重/规格不改不代表原 per_class 验证自动覆盖 unify_vehicle。旧臂显式 per_class+pose-aabb，新臂显式 unify_vehicle+pose-center；D2 写清 SOT/旧离线工厂缺省兼容范围，避免把所有构造器缺省一并改掉。 |
| (f) | 当前**不向暂停的 LOOP-002 提案追加指针**：10-09 开项账本明确该项仍暂停、不追加内容。本提案 §2.5/§6 已足够登记语义差异；旧 verdict 仅绑定旧候选。恢复及基线由用户决定，不因共享文件改动把旧通过迁给新代码。 |
| (g) | 可以限定为提交入口的兼容迁移，旧语言收养判据延后且本轮 Play 不可达；但 D1 的点击专属 TaskSpec/当前 tracked 校验与语言 BOUND_COASTING、旧 acquire 收养互相冲突，尚不能接受，须按 AR1-3 写清路径和回归。不得借兼容迁移引入新语言自动授权或静默删除已有能力；若做不到兼容，缩减/变更语言范围上交用户。 |
| (h) | **不接受自行把「进带并保持」改为 p50≤14.5、max≤22.2。上交用户。** 来源 FRAME-001 补测 R3 表是另一候选/控制条件的描述读数（第一圈 14.032831/22.170916，第二圈 14.090850/15.263881），不是本项保持门。按 COORD-017，移植限值只能描述，不可直接变成本项 STOP/验收线。推荐保留 12±2 m 原目标并报告带内比例/越界原值；若用户愿改成非劣化合同，须先明确评价时段、基线条件及限值，接受角色不代选。 |

#### D2 必改清单（具名残留；不是独立复核 finding）

| ID | 位置与问题 | 修改要求与可核对的完成条件 |
|---|---|---|
| AR1-1 | §3.3/3.7、AC-6/9/10/18/24：在 t0+T_repair 先判 BROKEN，同时允许提交≤该帧；T_pred=T_repair=5 又要求第5帧 look_at，和撤权优先冲突。 | 固定到期边界（推荐年龄≥T_repair先到期、修复提交严格早于该帧），统一所有不等号和同帧顺序；预测测试以完整授权条件为前提，提前可靠恢复/争议/几何拒绝/协方差超限均不再强制预测 look_at。T_pred 与到期同帧时明确谁优先；逐列 t0+T_report、t0+T_pred、t0+T_repair 前/当/后结果。 |
| AR1-2 | C3、§3.1–3.4/3.8、AC-3/8/15：HistoryEntry 没有 KF mean/covariance 字段，却要求每帧由历史取得预测协方差；运动门 S 仅写库位置块，缺测量噪声/单位；日志只给序号/原因，不足以重放 reducer 输入。 | 明确在线取得 KF 预测及协方差的只读接口、单位/同帧阶段/缺失非有限退化处置；S 的组成及像面噪声假设明列，不能拿世界系 R-4 代替像面标定。区分内部未裁剪预测框与对外 image-clipped 观测，out_of_frame 不得泄入桥。日志保留事件 payload 或不可变引用、版本及三种时间；AC-8 枚举每个有限轴的具体取值、年龄分带及授权偏序，AC-15 从落盘输入而非隐藏内存重放。KF快照全量回放可继续延后，无须为本条扩成完整地面滤波重写。 |
| AR1-3 | C5、§2.2/3.2/3.5、AC-7/13：全部提交都校验 j 当前 tracked，与含 unconfirmed 的 N_adopt 证据及语言 BOUND_COASTING 不相容；TaskSpec 只合法点击，却要求语言确认/旧 acquire 也经过管理器。现行 `_retire_pointer` 动态 follow(None) 和 DetAssocTracker.follow 转发亦不在 AC-7 字面调用闭集中。 | 按 INITIAL/USER_RESELECT/CONTINUITY_REPAIR/旧语言兼容分别定义准入、任务投影、coasting与副作用；原始/未确认检测只作修复证据，何时存在可提交的活跃库键必须写清。点击 k→当前链需逐帧检查断证，不只是两个端点 tracked。限定语言旧收养到现行 acquire 兼容路径，不套用到断链首次点击。枚举授权绑定与清除指针路径/转发例外；提交被拒/异常还须保持旧任务、episode、coasting、designation及版本不变，不能在新绑定成功前关闭旧 episode；补语言/coasting、拒绝重选保留旧目标和 follow 半改后抛异常用例。 |
| AR1-4 | §2.5、AC-14/16/17/19/21：点击页声明直接复用 Submitter/CliRunner，实际 argv/submit 参数没有 click 坐标/frame/sha；旧 frozen 归档回放要使用旧指针逻辑，D1 同时改它；合成评分与保真前提未冻结。 | 写清新 click 提交/argv 扩展所在文件与最小 diff 闭集，校正「operator_web 除记录路径外零diff」等互斥要求；已有语言/网页动作保持原合同。写清旧臂如何运行旧解析/默认值而不复用已改变的新管理器；固定合成评分真值映射、出画/删失与每格分母（旧诊断有3D投影等设计外偏差，不直接继承为通过）。新合成/点击呈现管线按 workflow §4.3.2 在冻结/正式采集前完成至少2张样帧人眼保真并留指针；不据此申请第二次Play。原诊断输入的正式准入另待用户 (c)。 |
| AR1-5 | §4 末、AC-12/17/18/23/24/25：点击≤1帧改成受理以后≤1帧，端到端承诺被缩短；IoU/误绑/保持的判断分母、门与描述读数混用。 | 两段时延分别记录，页面点击→受理不可从失败/超期点击中删样本；弱化原「点击到绑定」目标须上交用户，推荐保留原目标与端到端实测、受理后≤1帧只作子合同。对每条数值列合同/物理、目标条件真实读数、厂商、异条件移植四类出处和基线，明确5Hz/640×480合同条件、PASS/FAIL/NOT_EVALUABLE与缺观测分母；无下一次观测不得假判IoU通过。AC-25保持口径按(h)上交用户；未经用户确认的设计预算不能写成已定值。 |
| AR1-6 | §5/6/8：回放「每候选≤1次」与重载「共≤2」、候选总数及签发草案互相含混，Play表有run≤3而草案漏run；全套全集/解释器及Air环境仍假设；STOP只有文字没有具名码与后续处置。 | 统一每候选正常/崩溃共账上限、候选总数及整批封顶、真实loader清单（只读，不跑全套），run/session/scenario每维都入签发草案；写明确解释器/数据根/权重/现成包入口，原数据根环境常设规则与mini单项下载例外不得混用。Air只读核清作为阶段B签发前置，依赖未核环境的维度暂不申请签发。逐个STOP码写停哪些后续、哪些已签安全收尾可继续，并交用户随信封确认；预算/来源失败停依赖，不因停止而宣称读数通过。 |
| AR1-7 | §6/7(c)/9：把新回放当证据但其输入直接来自被禁止进证据链的诊断，且§9未显式列出这一用户决定；T_report、ρ_click、误绑预算等设计预算缺用户选择入口。 | 单列诊断原件限用途准入和未签预算入口，与U-1…5一起呈用户；不由接受/构思角色解除常设限制，不复制旧诊断结论作新通过。列明需用户定的设计预算（T_report、ρ_click及U-4风险口径），N_adopt=2仍是占位、不是已完成R-3标定；D2可明确写待用户及条件边界，但未答前不能冻结依赖它们的通过门或启动消耗。 |

#### §9 用户事项核对与上交用户入口

- **U-1**：需要阶段A模型/回放额度的理由成立，**不推荐按D1原样签**；推荐先按AR1-6补成一致清单并解决(c)用途边界，再签精确草案。未签0，本轮不代签、不运行模型或全套。
- **U-2**：一次Play、代码先复核的理由成立；推荐D2合同与Air零消耗前提核清后、代码停点通过消费时再签。若用户选择提前签，生效条件须取最终有效通过轮及已核环境，仍不提前放行；不增加重试。
- **U-3**：mini回放/全套、Air承载Unity必要会话与快层符合已有机器分工，推荐保持；这不是新设备授权，不重复询问已定分工。具体解释器/磁盘事实仍需只读核实，不能靠10-08曾运行代替。
- **U-4**：第一轮不声称误收养率的推荐成立；错误帧=0只是本次样本观察，不是风险上界。N_adopt=2只能占位，R-3没有数据，不得称最优或已满足用户风险预算。推荐用户明确同意此有限口径，并一并定T_report/ρ_click设计预算；接受角色不替用户定。
- **U-5**：保持LOOP-002暂停与不代答旧题的推荐成立，且暂停已获授权，不重新请求；恢复、改基线、关闭留到用户明确决定，不预定Play后必须关闭。
- **USER-SOURCE（对应(c)）**：推荐用户逐字限定原始诊断输入可用作本项新离线回归夹具，旧诊断不追认；依据为workflow §4.3.2与RECHARTER:REPLAY:1限制。若不同意，则AC-17/18/19只能诊断并另定验收证据来源；接受角色不放宽。
- **USER-ACCEPTANCE（对应(h)/AR1-5）**：推荐保留原点击到绑定及进12±2m带并保持目标，另报分段时延/越界读数；若改为受理后1帧和移植非劣化线，须用户明确批准。未经批准不把放宽写成已接受合同。

本轮仅裁定与交接，不产实现者证据/独立verdict、不修改LOOP-002门与提案、不销R1-5/F8债，不改账本、旧Log或正式设计。D2由构思角色在同一work ID修订，逐条回应AR1-1…7；用户事项不计作已答，不靠等待自动生效。

open_items: AR1-1, AR1-2, AR1-3, AR1-4, AR1-5, AR1-6, AR1-7

### D2 接受裁定（2026-10-09，Acceptance）

**裁定：`REVISION_REQUESTED`，同一提案第二次设计退修。** 已完整核对 D2 正文、§10 对 D1 完成条件的回应、§7/§9、USER-4A 逐字选择与主线/快层/RECHARTER 授权，并只读相关真实代码及库的更新顺序。本轮不跑测试、模型、Play、板端或下载；下表是合同审查，不是实现证据或独立复核 finding。范围方向成立，但 AR1-2、AR1-3、AR1-6 尚未闭合，不交实现自行解释矛盾。

**轨道逐字裁定：本轮不准许 `Workflow: engineering-v1` 生效。** 抬头申请保留；未 `ACCEPTED`，按 engineering-workflow §0 fail-closed。用户开项与四项答复没有签发任何额度；两阶段各未签维度仍为 0，不继承 RECHARTER 或暂停项余额。本轮不修改正式设计、LOOP-002 的提案/门、既有 verdict 或债务账本。

#### AR1-1…7 完成条件逐条核对

| ID | 闭合判定 | 对完成条件的核对与残留 |
|---|---|---|
| AR1-1 | 闭合 | §3.3 固定 age≥T_repair 先到期、修复严格早于到期；T_pred≤T_repair−1，逐列边界与一般式一致。AC-6/9/10/18/24 不再对恢复/争议/几何/协方差拒绝帧强制预测命令。占位 2/3/4/5 满足结构约束。 |
| AR1-2 | 部分闭合，保留 | 内外框隔离、噪声/单位、非有限退化、落盘输入与 AC-15 已补；**prior 接口仍缺**：§3.1 只在 `tracker.update` 返回后复制快照，匹配/重激活的原 ID 此时是 posterior，§3.1 运动门和 §3.2/3.3 接受原 ID 观测却需要同帧量测更新前的 μ/P。库 `byte_tracker.py::update` 顺序为 multi_predict→补偿→关联/量测更新→返回，不能拿 posterior 做创新门。须明列补偿后、关联更新前的只读 prior 及更新后 posterior，按键/帧/phase 落盘，缺 prior fail-closed；加原 ID 重匹配但创新过大被拒的用例。**AC-8 的全域单轴单调性也不成立**：ACTIVE/fresh/TENTATIVE/UNKNOWN/几何有效/age=1/协方差 within，OBSERVED 命中行8（不发）；仅改 PREDICTED 命中行7（预测），按已写偏序反而升级。须明确可达域与不一致组合的拒绝/归一化，列合法的“变差”边再作单调性证明；不能既枚举全笛卡尔积又要求该反例不升级。 |
| AR1-3 | 部分闭合，保留 | 路径/清除/转发闭集、未确认证据与活跃键、逐帧点击链、成功后关旧 episode、半改异常已补。**计数矛盾**：§3.2/AC-4 要每次接受提交递增 intent_revision/episode；§3.5 repair 却同 episode 仅增 association_revision，lang_acquire 沿用 designation。须按 origin 写明计数矩阵，repair 不冒充新任务。**兼容拒绝路径矛盾**：现行 `ResidentCore.designate` 一进入即递增 `_next_designation_id`，失败也分配 ID；D2 改成成功才分配、被拒 designation 不变，与 (i)/AC-13“全部现行行为”冲突。推荐保留旧语言尝试计数，区分解析尝试与绑定提交，补拒绝→成功序列。**回滚接口不完整**：现行 `follow(new)` 换指针清 `_coasting`，再 `follow(old)` 与读回 pointer 不会恢复旧 coasting；须写清同一事务内旧 coasting/计数等快照与恢复/核对接口，并用非空旧 coasting 的半改异常证明全状态恢复，恢复失败仍 fail-closed。 |
| AR1-4 | 闭合 | §2.5/3.5 与 AC-14/16 统一为 Submitter 传参扩展和 on_reply 窄修两处；基线源导出隔离旧管理逻辑，AC-19 明列映射/删失/断轨/分母。AC-27 对两种新呈现各至少2帧保真；落实时须在协议冻结或首次正式采集中较早者之前完成，不能仅在评分前补验。输入准入按下文 (k)，旧诊断结论不转为通过。 |
| AR1-5 | 闭合 | USER-4A 保留原目标；AC-22 端到端与子段分记、全点击含失败计分母；AC-18/24 无后续观测记 NOT_EVALUABLE，AC-25 进带和保持分别判、另报越界。§4.1 列出处/条件，FRAME 读数仅描述。待标定参数依赖的结果仍标暂定，不能据新门读数事后改参数/帧集/口径。 |
| AR1-6 | 部分闭合，保留 | 每候选/整批共账、真实loader清单、ID各维、mini解释器与Air前置已补。**STOP 收尾错误**：§6 “仍可执行（零消耗安全收尾）”中的 S-A-INPUT 允许“全套”，而 F12/AC-20/§5.1 明列全套可能真实构造 YOLO≤2；它不是零消耗收尾。须拆成零模型安全收尾与“仅对应信封已签、前置无依赖且余额足够时可继续”的具名步骤，写明各耗用维度。其余 STOP 逐条沿用该判据、将越界在启动前拦截；用户未确认的处置不生效、照旧停报用户。不得用清单异常后的部分全套宣称 AC-20 通过。 |
| AR1-7 | 闭合 | USER-4A 已解决原件限用途准入、有限收养口径及三个用户占位预算；§6/AC-17 不继承旧导出/结论，N_adopt 非 R-3 标定。§9 保留未签额度/STOP 用户入口，不重问已答四项；准入范围不得由作者或接受角色扩展。 |

#### §7 新提请 (i)–(m) 逐条答复

| 项 | 裁定 |
|---|---|
| (i) | 同意捕获模式启用新行为、兼容模式保留 per_class+pose 与旧语言收养的边界；不能接受“全部现行行为”与 designation/episode 副作用的冲突，按 AR1-3 收束。若拟改变旧语言失败计数/外部回执语义而非保持兼容，**上交用户**：推荐保留兼容，理由是本轮只修快层且语言新行为属第二轮。 |
| (j) | 同意进程内 `send_request` 与两处 diff 闭集的设计；四种退出语义、单在途、seal/UNKNOWN 及原 argv 不变仍为 AC-14 必证，现有 CLI kill/quiesce 子债不销账。避免子进程开销不证明 AC-22 已过。 |
| (k) | 同意使用运行时解析的接受提交源码导出与本次独立检测缓存；“现象门”只复现 AC-17 明列的红车失观测现象，不得称精确复现旧会话或借用 RECHARTER PASS。**准入按用户原话只限原始帧、位姿、真值**，因此不读旧会话日志/frames.jsonl 作证据输入的写法与当前闭集相符；SHA256SUMS 仅作完整性参照。它不表示已授权整目录，也不禁止读取准入帧 json 内原有位姿字段。若确需额外旧日志/frames.jsonl 字段，或认为原件内位姿也应排除，均**上交用户**，不自行放宽/收窄：推荐保持现行原件闭集并在新日志重建状态，理由是足够支撑现象回归且避免诊断结论回流；确有不可替代字段时先逐字段说明用途申请。 |
| (l) | 同意 T_pred 占位5→4，仅为满足严格早于到期的结构约束；未改变 USER-4A 三个已选参数，不表示真实条件标定或用户同意新增额度。 |
| (m) | 具名码/停止后续/保留失败的形式成立；**原表尚不足以原样交用户签发**，先按 AR1-6 校正全套与零消耗的混写，再随 U-1/U-2 分阶段交用户确认。接受角色不代签 STOP 处置。 |

#### §9 待用户与第二次退修后的去向

USER-4A 四项已答，不重问；U-1…U-4 未答：U-1 推荐待终局接受及 STOP 表校正后签精确阶段A清单；U-2 推荐待最终有效代码通过轮消费及 Air 预检核清后另签一次 Play；U-3 推荐阶段B准备时由用户/获准的 Air 会话只读核清、保持已定机器分工；U-4 推荐随各阶段信封确认校正后的 STOP 处置。理由分别为避免给未收束合同额度、不可重跑步骤先复核、环境不可由mini推断、停止后耗用必须有明确授权。当前额度全部0，本轮不写账本。

**不派发常规 D3 退修。** workflow §4.2 与 engineering-workflow §3 要求第二次退修后上交二选一：(a) 接受当前范围并逐条列出已知缺口；(b) 关闭为负结果记录。当前账本没有绑定 CAPTURE 的 supervisor D1 决策信封；JET/ACQ/FAST 的信封不能跨项继承，虽残留3项≤D1的7项，仍由**用户**决定，supervisor 只转呈。推荐 **(a)** 保留当前有界范围，并把上表 AR1-2/3/6 逐项作为具名缺口、以明确合同解释收束，理由是用户方向和验收目标均已确定，残留是可修正的接口/计数/资源表矛盾；不得默许实现者自选解释或降低安全门。用户选 (b) 则由接受角色按该授权收为负结果，不冒充通过。第三次裁定依据用户选择作终局接受（列缺口及明确 binding clarifications）或关闭，不能再次自行 `REVISION_REQUESTED`；未收到选择前不进入实现，不改 Lifecycle，不签 `ACCEPTED`/`DONE`/`CLOSED_*`。

open_items: AR1-2, AR1-3, AR1-6

### 终局裁定（第三次，依用户 (a)）

**2026-10-09，Acceptance；裁定：`ACCEPTED`。** 依据账本同日「用户终局二选一：选 (a) 接受当前范围并具名列出缺口」，终局接受当前 D2 的 §1–§8、AC-1…27 与下列唯一合同解释；不再设计退修。D1、D2 裁定原文保留为历史，本节在冲突处优先，不覆盖原条款、不新增工作范围。AR1-2/3/6 是具名合同缺口及实现必证义务，不是独立复核 finding，也不是获准跳过的安全门。当前未实现、未复核、未验收；本轮未跑测试/模型/Play/板端/下载，不产行为通过证据。

**轨道逐字裁定：本轮准许 `Workflow: engineering-v1` 生效。** 本项为开项时即申请该轨道的新工程 ID；用户已定主线、快层方向、USER-4A 验收目标并选择终局接受此工程提案（含 K2/K4）。按 engineering-workflow §0/§3 采用任务合同与 K 停点，不改变安全、真值隔离、独立复核、用户验证或信封纪律。§7 的 `K1K2K3K4` → C → 新鲜 R → 接受消费，先于唯一一次 Play；其产物另过 `PlayK2K4`。§7 (i)–(l) 按 D2 答复及本节接受，(m) 改取本节 STOP 表；§9 U-1…U-4 仍待用户。本项额度全部 0，不转用任何旧项余额；本轮交用户签发，之后才派发实现。

#### AR1-2 — 双阶段 KF 输入与授权可达域缺口（binding clarifications）

**AC-3/5/6/15 修订 1（解释 §3.1/3.3/3.8）：** 关联器提供只读 `prior_snapshots(frame_id)` 与 `post_snapshots(frame_id)`，均按 `(sensor_frame_id, library_frame_id, track_key, phase)` 对齐、深复制、不得反写库 KF。每帧在 `_pre_first_associate` 完成本帧补偿后、首轮关联及任何量测更新前复制 `strack_pool` 与 `unconfirmed` 的 prior，H=None/none/optflow 也在同一阶段复制；未确认行按库现状只补偿、不额外预测。`update` 返回后复制 tracked（含未确认）及 lost 的更新后快照；发生量测更新者标 posterior，未更新者标 prior，不把未匹配行伪标 posterior；本帧新建键无更新前 prior，显式缺失。快照字段沿 §3.1（xywh、vx/vy、P_pos、单位与有效性），增阶段/帧/键；`matched_det_index` 对应本帧完整策略后检测数组，检测中心取未裁剪原始框。原 ID 重匹配与新候选的运动/尺寸门一律用**原绑定键同帧 prior**，S 仍为 prior P_pos + diag((w/20)²,(h/20)²)，禁止用 posterior、上帧快照或候选自己的 prior 替代。缺失/错帧/无效 prior 或 S 不可逆 → 本帧观测不被接受、修复不提交、云台不发、机身 HOLD；走未匹配/到期规则，不刷新 t0。接受原观测后 belief 可取该键的 post 快照；post 无效同样不授权。点击新实例以当前有效 post 初始化，不要求新键具备 prior，也不做延后的 KF 历史滤波重放。

两阶段快照及缺失/无效原因、匹配检测索引、位姿/内参/画幅、原始检测、removed/ended 键、请求顺序、输入版本和配置引用进入 `tm_inputs.jsonl`；保留 §3.8 三种时间、批次及 newest/backlog 标记。初始化输入另存 mode、配置原文与初始业务状态（首会话为空）；看门狗、STOP/点击等非帧事件亦按消费顺序落盘，含实际用于判定的时间，不在重放时读取当前墙钟。只用落盘输入与配置重放，不重跑检测或 KF、不读旧日志/真值/隐藏内存；所引历史在输入中实存或引用同文件已校验的不可变行，缺引用即拒。输入行 sha 按 UTF-8、键排序、紧凑 JSON、禁 NaN 的原文（不含自身 sha 字段）计算，配置 sha 对配置文件字节计算。内部快照/未裁剪框不进桥，桥仍只发裁剪 OBSERVED 框。

**AC-8 修订 1（解释 §3.4）：** 3,072 格仍是防御性总输入表，另测 T_pred=2/T_repair=5；先验证一致性，再按原八行第一命中授权。可达规范域 G 定为：本轮 semantic=UNKNOWN；ACTIVE 的 OBSERVED 必为 SUPPORTED、age=0、KF 有效且协方差 within；ACTIVE 的 PREDICTED 必为 age≥1，SUPPORTED/TENTATIVE 仅 age<T_repair，BROKEN 仅 age≥T_repair，DISPUTED 可在 age≥1 锁存。geometry 可 valid/invalid；PREDICTED 的协方差可 within/exceeds/kf_invalid。task=none/CANCELED/stopped 的 belief 字段不授予权限；stale 将观测输出投影 STALE，八行以 watchdog 优先撤权。ACTIVE 不满足上述组合 → HOLD/不发，原因 `authorization_input_inconsistent`（追加到原因闭集末尾）；CONTRADICTED 是域外防御输入，优先撤权，不变成本轮可达语义能力。总表逐格区分“一致性拒绝”与“八行首命中”，禁止为域外格造 OBSERVED 或预测命令。

单调性仅对 G 内下列合法变差边证明：ACTIVE→none/CANCELED/stopped；fresh→stale；valid→invalid；PREDICTED 的 within→exceeds→kf_invalid；PREDICTED 且未到期时 SUPPORTED→TENTATIVE；同一 PREDICTED/SUPPORTED 或 TENTATIVE 的年龄带递增（两端均未到期）；SUPPORTED/TENTATIVE 的 PREDICTED→DISPUTED。另证三个联动事件不升级：OBSERVED/SUPPORTED/age0 → PREDICTED/TENTATIVE/age1 的失观测；窗口内 PREDICTED/S或T → BROKEN/到期年龄；OBSERVED/SUPPORTED/age0 → DISPUTED 的本帧竞争（先锁存、撤权，最终规范化为未接受该帧、按旧 t0 计 age）。DISPUTED/BROKEN 不互转、不恢复；恢复、新点击及成功修复是改善事件，不套变差量词。OBSERVED→PREDICTED 单独改变且保留 age/连续性不在合法边中，D2 反例按域外拒绝；不声称完整笛卡尔积的无条件单调性。偏序仍为 §3.4 两分量偏序。

**必证：** `test:tests/test_det_assoc_tracker.py::KfSnapshot*` 覆盖同帧 prior/post 分离、错帧/缺失、匹配后 posterior 看似近而 prior 创新过大；`test:tests/test_target_manager.py::Continuity*` 证明该原 ID 不刷新 t0、不 FOLLOW；`::Authorization*` 给逐格域分类与上述闭集边的计数/结果；`::Replay*` 从新进程落盘输入复算转换/拒绝/绑定/效果，篡改或缺引用拒绝；`artifact:docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` 按 AC 指针自证。本项缺口只能以实现及独立复核核实履行，当前不记完成。

#### AR1-3 — origin 计数与全状态事务恢复缺口（binding clarifications）

**AC-4/7/13 修订 1（解释 §3.2/3.5）：** 业务计数按下表，初值 intent_revision/episode 分配序号为 0；新 episode 的 association_revision=0，repair 才递增。episode 分配序号只增不复用，关闭不加号；TaskSpec 不可变，repair/同任务 acquire 不改其 selector。compat 的外部 segment/verify 纪元与既有 `_new_pointer_epoch`/retire 顺序逐条保持，新增 target_episode_id 不替代旧外部 track_id。

| origin / 结果 | intent_revision | episode 分配 / 当前绑定 | association_revision | designation 尝试计数 |
|---|---|---|---|---|
| click 首绑或重选成功 | +1，新 TaskSpec | +1，新 episode；成功后才关闭旧 episode | 新 episode=0 | 不变 |
| repair 成功 | 不变 | 同 episode/换库键 | +1 | 不变 |
| lang_confirm 得 BOUND/BOUND_COASTING 且绑定成功 | +1，新 LanguageCompat | +1，新 episode | 新 episode=0 | 每次解析尝试预先 +1，成功不再加 |
| lang_confirm 得 TRACK_ENDED、按旧路径进入 acquire | +1，新 LanguageCompat（确认任务已接受，尚未绑定） | 不分配；原指针按旧 `_begin_acquiring` 释放，旧 episode 关闭 | 无当前绑定 | 本次尝试预先 +1 |
| lang_acquire 成功 | 不变，沿用已确认 TaskSpec/designation | +1，首次绑定该 acquire 任务 | 新 episode=0 | 不再加 |
| click/repair 被拒或可恢复提交异常 | 不变 | 不变，旧绑定保留 | 不变 | 不变 |
| lang_acquire 被拒或可恢复提交异常 | 不变，已确认 TaskSpec 保留 | 不分配、无新绑定；后续 acquire 失败/继续仍取旧流程 | 不变 | 不变 |
| lang_confirm 解析失败或绑定被拒/可恢复异常 | 不变 | commit 前业务状态不变；解析失败后的会话状态仍取旧路径 | 不变 | 已发生的解析尝试 +1 保留 |
| release / teardown（含 acquire 失败） | 不变 | 关闭当前 episode、无绑定；重复释放无重复关闭 | 不变（无绑定） | 不变 |

兼容尝试分配与绑定事务是两个明确阶段：会话对每次原本会调用 designate 的确认，先从 `_next_designation_id` 取号并 +1（起点仍为 1），再调用纯 `resolve_designation`；其失败/成功结果照旧写 core.designation、会话 designation 及原回执/事件。纯解析函数自身不改计数/指针/coasting；e1 的旧 designate 外壳仍执行原分配/结果记录。commit 的“零状态变化”基线是**本次尝试已记录后、commit 入口前**的状态，绝不回滚真实发生的尝试，也不在成功时另分配 ID。TRACK_ENDED 进入旧 acquire 是已确认任务转换，不能误当 click 的断链补身份或成功绑定。兼容路径不调用捕获授权函数、不添加预测/修复/新报告；既有语言状态、原因、指针/coasting/外部纪元序列保持。`test:tests/test_capture_session.py::LanguageCompat*` 增失败→成功、BOUND_COASTING、TRACK_ENDED→acquire成功/失败逐条对旧代码；`test:tests/test_target_manager.py::TaskSpec*` 按表覆盖四个 origin 与 release/teardown，不再断言每次 commit 都新建任务。

**AC-7/11 修订 1（解释事务）：** 核心提供内部 `snapshot_binding_state()`、`restore_binding_state(snapshot)`、`binding_state_matches(snapshot)`，在同一单写者事务内深复制/恢复/逐字段核对 `{pointer, coasting（含 designation_id/steps）, designation, next_designation_id, ended_ids, 未排出的 core events}`；管理器同步快照 `{TaskSpec, TaskRuntime（mode/phase/episode/deadlines）, BindingRecord, TargetBelief, RepairBuffer, intent_revision, episode分配序号, association_revision, 待发布效果}`。会话外部纪元副作用（segment_index/segments_seeded/retired_track_ids/verify_epoch/track_id/loop及publisher的track_id）在核心提交成功后才执行，拒绝或回滚期间不变。先算新记录，后 follow(new)，成功后写业务记录/必要coasting并发布纪元效果；STOP、提交、授权和发布串行，发布前核版本/有效期。

follow(new) 抛异常（包括半改）→ 尝试 follow(old)，然后恢复**完整**核心与管理器快照、读回逐字段核对；仅 pointer 相同不足以成功。可恢复则保留旧 coasting、TaskSpec/episode、尝试结果与旧跟随资格；审计 rejected/follow_failed 可追加，业务计数不变，event_seq 只随实际追加审计递增，effect_seq 只随已提交效果递增，不发布失败事务效果。follow(old)、恢复或核对任一失败 → 不继续旧/新跟随，串行写 HOLD、停止云台新效果、作废在途效果、best-effort release_binding，标 REINIT_REQUIRED/binding_rollback_failed；指针清除不确定也必须日志显式 UNKNOWN，不能声称已恢复。新增内部快照接口不属于第二写指针入口，供管理器事务及静态检查白名单；会话仍无直接/getattr follow，§3.5 原转发/e1例外保持。`test:tests/test_target_manager.py::Commit*` 必须以旧 coasting 非空且 steps>0 注入半改异常，核对完整快照；分别注入复原抛错、coasting恢复错和读回不符证明 fail-closed，另证成功重选后才关旧 episode。缺口当前未实现，不销任何旧债。

#### AR1-6 — STOP 收尾耗用混写缺口（binding clarifications）

**AC-20/21 修订 1（解释 §5/§6）：** 下表替代 §6 最后一列的“零消耗”解释，作为 U-4 待确认合同；它本身不签发资源。零模型收尾 Z-A = 停当前回放/全套进程、保存已有缓存/日志、写失败/耗用/UNKNOWN与交接；Z-B = 停会话/Unity（不再启动）、串行 HOLD/撤权、保留未决请求 UNKNOWN、封存本次原件及哈希清单、对已得文件零模型评分。两者都禁止加载/重载模型、新推理、新 Play/ID、下载/安装/板端/API；**零模型不等于零磁盘或零墙钟**，写文件仍计对应阶段磁盘及运行/按钮墙钟，在启动时为收尾留余量；不得借 STOP 给超限收尾追加预算。安全撤权必须执行，若已用量不明或紧急停止实际超限，如实记录偏差并回用户，不冒充获准余量。mini 文档写裁定/交接为本轮零消耗，不是模型执行许可。

全套 F = 每候选仅一次（含失败也占本次），真实构造≤2且整批≤6、全套≤3、每次≤30 min，新增磁盘计 A≤3 GB；只能在 CAPTURE:A:1 已签、相应余额足、F12清单不扩、与坏输入无依赖时继续。零模型 focused/保真不计模型加载，但输出/样帧计 A磁盘；真实加载 focused 每次计 A开发期≤20且输出计磁盘。回放正常/崩溃重载合计每候选≤2/整批≤6，实际尝试启动加载即记次、失败不返还；实际已提交推理帧（失败/重跑含在内）逐帧共账≤5,500/16,500，每次回放≤30 min，A磁盘≤3 GB。重载只能同候选一次，不能通过换候选号规避，候选≤3且对应真实 diff/返工归因。正式 ID=0/0/0，输出目录不是正式 run ID。所有启动前逐维核账，账缺失/损坏/UNKNOWN不得推余额；下载/安装仍0，mini单项 lap 例外不继承。

| STOP | 必停依赖 | Z 收尾 | 仅用户确认 U-4 且对应信封已签/余额足/前置独立才可继续的步骤及维度 |
|---|---|---|---|
| S-A-BUDGET | 将越界维度及其依赖 | Z-A；未知用量记 UNKNOWN | 不继续模型/全套/回放；回用户 |
| S-A-INPUT | 本候选 AC-17/18/19 全部回放 | Z-A | F 可独立继续（耗全套次数/构造/墙钟/磁盘）；仅合成/替身且不读坏准入文件的 focused 可继续（真实加载如有仍计≤20），其日志计A磁盘；坏来源不自行修复放行 |
| S-A-FIDELITY | 正式回放及受影响呈现冻结 | Z-A | 闭集内修管线、零推理样帧重做保真（A磁盘）；有确认后按原余额执行首次正式回放，不作第二次Play许可 |
| S-A-REPRO | 新臂评分与 AC-17/18/19 读数作废 | Z-A | 不补跑、不换门/剧本/参数；回接受与用户 |
| S-A-CRASH | 同候选回放，第3次加载禁止 | Z-A | 不继续该候选回放；不以残缓存记通过 |
| S-A-LOADER | 启动超清单构造前拦截并停本次全套 | Z-A | 无同次重跑；若已超出照记全部尝试、AC-20 NOT_RUN；回用户 |
| S-B-PRE | 不启动会话/Play/模型，不分配ID | 只记不符及交接 | 仅获准Air只读复核，不能动用B未签维度 |
| S-B-UNITY | 本次Play计已用，不再尝试 | Z-B | 仅零模型分析已得文件（B磁盘/墙钟）；无再次进入Play |
| S-B-TERM | 剩余剧本 | Z-B | 同上；无会话重启/重建 |
| S-B-WALL | 剩余剧本，立即停止 | Z-B | 不启动额外运行；收尾实际墙钟照记，不给420s外隐含宽限 |
| S-B-UNSAFE | 立即停止会话，剩余剧本 | Z-B；AC-25 FAIL | 仅零模型分析（B磁盘/墙钟）；不追认不安全命令 |
| S-B-BUDGET | 将越界维度及其依赖 | Z-B | 不继续任何模型/ID/Play；只有未越界且已预留的零模型收尾写入/分析，回用户 |

U-4 未确认时，STOP 停依赖并回用户，表中“可继续”不生效，不自动重试；停止/撤权义务不等待新许可。B所有步骤（含Z-B）仍共账 §5.2：Play1、session1、run≤3、模型加载≤1且重建只能复用已加载对象、按钮≤420s/T_sess既定上限、Air新增≤1GB；失败计实际已尝试ID/加载/Play，余额不转用。局域网拷贝不是下载许可，也不豁免磁盘：B没有mini新增磁盘额度，缺项为0，推荐评分与产物留Air；mini只能读取已有文件而不产生新增工件，若需传入并落盘另请用户签该维度。STOP产物保留 NOT_RUN/FAIL/NOT_EVALUABLE 与UNKNOWN，不作通过。`artifact:docs/evidence/P1-ENG-CAPTURE-001-play-ops.md` 必按12码列用户确认来源/生效阶段、逐维守账、收尾预留与停依赖；`test:tests/test_capture_session.py::Stop*` 和操作工具替身用例证明启动前拦截与停止后无模型/重启，`artifact:docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` 留清单与资源账指针。当前是已接受合同解释，实际U-4仍未签。

#### §9 用户入口（推荐、理由与签发前置）

| 题 | 推荐（不是已授权） | 理由与签发前置 |
|---|---|---|
| U-1 | 按 §5.1/§5.3 **加本节 AR1-6** 逐维签 CAPTURE:A:1，保持原上限，不加Play/下载/板端 | 终局合同已明确；签发文本须包含每候选/整批加载、推理、全套、focused、墙钟/磁盘、全部零维度及A类STOP处置。签前确认仍用§8.1已核机器/环境/来源、无事实漂移；漂移先零消耗补核，不自动装包。用户逐字入账后交实现，首次正式回放前AC-27保真齐备；未签0 |
| U-2 | 暂不签；代码最终有效通过轮被接受消费且Air预检齐后另签一次 CAPTURE:PLAY:1 | 不可重跑步骤先复核；届时逐维签§5.2、B类STOP与本节磁盘/收尾边界，发令现场HEAD/porcelain对应通过候选或文档白名单、全局blocks及共享槽位通过、操作单/覆盖sha核清；一次失败不重试，签额不跳门 |
| U-3 | 阶段B准备时由用户或用户指定的Air会话做§8.2只读预检，保持mini/Air分工 | mini无法证明Air事实；不运行模型/Play、不安装、不写共享runtime，覆盖文件可生成性先只读核方案，实际生成属于已签B准备。Unity能打开工程须用户现有界面/日志事实确认，静态版本不冒充打开实测。版本差异逐项核可用性，无法确认即S-B-PRE；原始读数入操作单后才申请依赖它们的B维度；本轮不代选时机/执行者 |
| U-4 | A签发时确认A码处置，B签发时确认B码处置，采用本节拆分表 | 全套有模型构造，归档也占磁盘/墙钟；各阶段签发须明确可继续闭集及耗用、确认STOP默认处置与耗尽停报。未确认不得自动继续；不借表格扩额度、安全撤权优先不变 |

USER-4A、快层方向、诊断原件准入与原点击/距离目标已答，不重问；不改 LOOP-002 提案/门/暂停、不销 R1-5/F8 或其他旧债，不签独立verdict、UNITY_NA或DONE。AR1-2/3/6 作为上文具名缺口保留至实现自证及独立核实；现行下一接手方为用户，收到U-1/A类U-4逐字签发后接受角色落实信封再交Implementation，其他未签维度仍0。

open_items: AR1-2, AR1-3, AR1-6

### 信封落实（2026-10-09，Acceptance）

**授权来源与核对结论：** `docs/authorizations.md` 同日「P1-ENG-CAPTURE-001 — 用户签发第一轮阶段 A 额度 CAPTURE:A:1 并确认阶段 A STOP 处置；Air 预检定为阶段 B 准备时由 Air 会话执行」是本次唯一阶段 A 执行额度来源。已逐维核对其选定项、信封明细、STOP 确认与本提案 §5.1/§5.3、终局裁定 AR1-6 拆分表，一致、无待用户澄清的歧义；U-1 与 A 类 U-4 已签发。本节落实已有授权，不另签发、扩大或转用额度；§5/§9 及终局裁定中的“待签”是签发前快照，现行效力以本节与账本为准。

| 已签维度（CAPTURE:A:1） | 核对后的生效边界 |
|---|---|
| 执行机 / 环境 | Mac mini；`.venv-yoloe/bin/python`；`ENG_DET_DATA_ROOT` 不设；进程设 `YOLO_OFFLINE=True`、`YOLO_AUTOINSTALL=False`；不装包 |
| 候选 | 首候选加至多 2 个返工候选，整批 ≤ 3；对应真实 diff/返工归因，不换候选号规避共账 |
| 停点全套 | 每候选仅 1 次，失败也占次；整批 ≤ 3 次；每次真实 YOLO 构造 ≤ 2、整批 ≤ 6，限 F12 清单；每次墙钟 ≤ 30 min |
| 离线回放加载 | 每候选正常 1 + 同候选崩溃重载至多 1，共账 ≤ 2；整批 ≤ 6；尝试启动即计、失败不返还 |
| 离线推理帧 | 每候选 ≤ 5,500，整批 ≤ 16,500；失败/重跑实际提交帧共账；权重身份按 §8.1 与冻结配置运行时核对；故障注入 0 推理 |
| 开发期 focused 真实权重加载 | 整批 ≤ 20；零模型 focused 不计加载，输出仍计磁盘 |
| 回放墙钟 / 新增磁盘 | 每次回放 ≤ 30 min；mini 新增磁盘整批 ≤ 3 GB，产物在 `outputs/eng-capture/`、不入仓；STOP 收尾仍共账，不隐含宽限 |
| scenario / session / run ID | 0 / 0 / 0；临时测试目录不是正式 ID，不写共享 `runtime/` |
| Unity/Play、板上、VLM/API、云 GPU、下载/安装 | 全部 0；不继承 RECHARTER 下载例外或任何旧项余额 |

**A 类 STOP 处置已确认：** 用户按终局裁定 AR1-6 的 S-A-BUDGET、S-A-INPUT、S-A-FIDELITY、S-A-REPRO、S-A-CRASH、S-A-LOADER 六行确认，不取 §6 旧“零消耗安全收尾”列的混写解释。逐码必停依赖、Z-A 与可继续闭集均按该拆分表；S-A-BUDGET 不继续模型/全套/回放，越界停报、余量不转用。S-A-INPUT 下独立 F/focused、S-A-FIDELITY 下闭集修管线/零推理保真及确认后的首次正式回放，只在已签对应余额足、前置独立时执行；其余码不因本节获得补跑许可。Z-A 的写入与墙钟也占 A 额度，先留收尾余量；用量 UNKNOWN/账损坏不推余额，实际紧急停止超限如实记偏差并回用户。

**U-3 已答与未签项：** 等阶段 A 代码复核通过后，在阶段 B 准备时由用户在 Air 开会话执行 §8.2 只读预检，原始读数写入 `docs/evidence/P1-ENG-CAPTURE-001-play-ops.md`；mini 不代证 Air 环境。只读预检不加载模型、不 Play、不安装、不写共享 runtime，覆盖文件只读核可生成方案，Unity 打开事实依终局 U-3 核实。CAPTURE:PLAY:1（U-2）及 B 类 U-4 均未签、生效额度 0；必须先消费 `K1K2K3K4` 最终有效通过轮、核清 Air 预检，再另条签发。当前不得启动 B 准备中需 B 额度的操作、会话/ID/Play 或 B 类可继续步骤；停止/安全撤权义务不等待授权。

**实现开工与停点交付：** 交 Implementation 仅实现阶段 A，唯一合同为 §2–§7、AC-1…27 与终局裁定 AR1-2/3/6；开工先按 §8.1 零消耗核机器/环境/权重/准入来源有无漂移，漂移先补核，不能自动安装。本轮只读补核：Python 3.12.14；ultralytics 8.4.104、torch 2.13.0、opencv-python 5.0.0.93、lap 0.5.13、numpy 2.5.3（仅包元数据、未导入模型）；权重 5,458,330 B、现算 sha 与 §8.1/冻结配置身份一致；数据根环境变量未设、缺省根存在；磁盘可用 118.31 GiB。准入原件完整性/帧时刻逐项核验仍是实现开跑前义务，本轮不冒充已完成。每次启动按 AR1-6 核全部维度余额，首次正式回放前完成 AC-27 人眼保真。

停点交付只取 §7 停点 1 与终局各“必证”指针：`docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` 按 AC-1…21、AC-27 附测试/工件、资源账、风险与准确完整候选 diff 范围，并设具名“四项稳定停点自证”小节，按 workflow §4.3.1 逐项附 AC 证据；操作单按 AR1-6 列 12 码、确认来源/生效阶段与收尾预留（B 未签明确标 0）。候选更新状态、提交并推送后停依赖推进，先交 Acceptance `C1@K1K2K3K4`，再新鲜上下文独立复核，最终有效通过轮由接受角色消费；本节不填写实现后的核对表、不产通过证据。AR1-2/3/6 具名缺口仍待实现自证与独立核实，旧债、LOOP-002 暂停及验收/主张上限保持。本轮未跑测试/模型/Play/板端/下载，consumed=none。

open_items: AR1-2, AR1-3, AR1-6

### 阶段A实现 IR 裁定（2026-10-09，Acceptance）

**来源与效力：** 逐条答复 `docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` §5 的 IR-1…IR-9；只读其直接关联代码、测试及本项账本条目。本轮为合同问题裁定，不是 `C1@K1K2K3K4`、独立复核或实现通过。前述正文及裁定原文保留；本节在所点名的歧义处给唯一读法。按派发要求显式列 `CLARIFY` / `NEW_OBLIGATION`；工程轨道实际记账仍用追加的 `AC-n 修订 m` / 新 `AC-n`（engineering-workflow §2、acceptance 角色细则），不回写原 AC 表。除 IR-7 来源的新 AC-28 外均为解释既有义务。

#### IR-1 — 改为兼容模式保留旧历史消费语义

**CLARIFY；AC-3/13 修订 2，依据 §2.1 两模式、C3、§3.6 与 AR1-3。** 不确认“两模式同用增强 lost 行”的读法：兼容语言路径全部现行行为不变是明确边界。增强历史由捕获入口显式启用；缺省、compat、e1 及其他原有工厂保持旧消费视图。捕获视图保留有限但出画/退化的 lost 行，带 `out_of_frame`，指针判 UNMATCHED；兼容视图在旧 `_norm_box` 会丢弃的条件下仍视为无该行，判 `bound_track_removed` 并按旧帧触发 `tracker_failure`，不等库删 ID。未确认等补列也不得改变兼容的 resolve/coasting/状态序列；快照与原始检测的附加记录不授予旧路径新权限。不得从 class_policy 或 GMC 值猜会话模式。

**完成条件：** `test:tests/test_resident_core.py::HistoryContractTests` 分证捕获保留/UNMATCHED与缺省旧丢弃/REMOVED；`test:tests/test_capture_session.py::LanguageCompatTests` 增出画与退化 lost、coasting 非空两类同脚本新旧比较，逐帧核指针、designation、coasting、纪元、state/reason，并证明 `tracker_failure` 的发生帧一致；`artifact:docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` 更新 AC-3/13。当前 `rows_from_library`、`ResidentCore.pointer_result` 与兼容脚本尚不能据此记满足。

#### IR-2 — CAPTURE 内登记一个合同预期失败，不改 LOOP-002 门件

**CLARIFY；AC-20 修订 2，依据 §2.1 C1/C3/C6、§6 对 LOOP-002 的影响与 engineering-workflow §6。** 唯一读法：保留完整 discover、原始失败输出及 `tests/test_loop2_freeze.py` 原文；将 `test_loop2_freeze.Loop2FreezeTests.test_play_governing_paths_outside_the_ownership_table_have_no_diff` 单列为 CAPTURE 合同内在预期失败，不计本项“新增回归失败”。它核的是 LOOP-002 原归属表与原基线，不能为另一已接受工作项授予范围；本裁定不改变该测试对 LOOP-002 候选的约束、冻结基线、旧 verdict、门或暂停，不跳过测试、不加 expectedFailure、不更新其基线。

**完成条件：** 全套日志如实保留该 FAIL；AC-20 摘要分别列基线已有失败、本项新增原始失败、上述合同预期失败、本项新增回归失败。仅当该用例失败确由原基线到本候选的 `controller/det_assoc_tracker.py`、`controller/resident_core.py`、`controller/track_loop.py` 三个获批路径 diff 引起、该测试本身零 diff、其余 `PLAY_GOVERNING_FORBIDDEN` 路径及 `config/scenario.*` 零 diff，才适用这一项扣除；记录运行时解析测试内基线所得的逐路径 diff 结果。后一个 scenario 断言因前断言失败未执行，须用只读 diff 单独补核，不能标已跑绿。任何其他失败/ERROR或额外禁改路径不适用扣除，新增回归失败仍须为 0。`artifact:docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` §2/§6 与 tests.log 联合给证；不得称原始全套全绿。当前只读 diff 确认三路径闭集，正式全套仍 NOT_RUN。本裁定限 CAPTURE，未触及暂停项门件，无需上交用户放宽 LOOP-002。

#### IR-3 — 确认闭集测试迁移读法

**CLARIFY；AC-2/10/12 修订 1，依据 §3.1/§3.6/C7。** 确认既有成员逐位不变、新成员只在末尾追加的断言；仍须精确相等、无重复、无任意额外成员。`GMC_SOURCES` 旧前缀 `pose,optflow,none`，后缀恰 `pose-center,pose-aabb`；`STATE_REASONS` 旧 26 项逐位不变，后缀恰 §3.6 十项再加 IR-5 的一致性原因；`ACTIONS` 旧前缀不变、仅追加 click。`test_every_action_is_writable` 对 click 补四个合法点击字段，对旧动作不传该字段且保留旧读写断言。

**完成条件：** `test:tests/test_pose_gmc.py::PoseHomography::test_gmc_sources_closed_set`、`test:tests/test_language_bridge.py::Loop2BridgeTests::test_state_reasons_appended_without_reordering` 与 `::RequestBridgeTests::test_every_action_is_writable` 给精确闭集证据；旧完整前缀与接受基线运行时逐位比较，不能仅检前缀内几个切片。本轮确认迁移意图，实际测试充分性留 C/R 核实。

#### IR-4 — 确认 FakeResident 接口迁移读法

**CLARIFY；AC-7 修订 2、AC-13 修订 3，依据 C5、§3.5、AR1-3。** 确认 `tests/test_language_loop.py::FakeResident` 提取同一 `_runner`，保留 designate 兼容外壳并补 `resolve_designation(box,k,designation_id)` 转发纯解析；不得调用 designate 冒充纯解析，不改 runner 判据与既有业务断言。新接口必须不自行分配 designation_id、不写指针/coasting。

**完成条件：** `test:tests/test_language_loop.py` 原断言意图保留；`test:tests/test_target_manager.py::CommitTests` 证明纯解析不变；`test:tests/test_capture_session.py::LanguageCompatTests` 按 AR1-3 origin 表比较失败→成功、BOUND_COASTING与 TRACK_ENDED→acquire。本轮不代签核对表。

#### IR-5 — 确认两处包含一致性原因

**CLARIFY；AC-8 修订 2、AC-10 修订 2，依据 AR1-2 AC-8 修订 1、§3.6。** 确认 `authorization_input_inconsistent` 同时是授权 reason_codes 闭集成员与 `STATE_REASONS` 最后追加成员；内部授权事件必须记录此码，桥接若使用此码不得被闭集拒绝。它不是新的可达模型能力，也不把域外输入升级为正常 TRACKING；一致性拒绝仍 HOLD/不发。授权闭集已有的 `CONTROL_LIMITED` 保留，“末尾追加”以保留既有成员与位次为准。

**完成条件：** `test:tests/test_target_manager.py::AuthorizationTests` 保持一致性拒绝的完整原因断言；`test:tests/test_language_bridge.py::Loop2BridgeTests::test_state_reasons_appended_without_reordering` 核第 37 项与唯一性，并覆盖该原因的桥 payload 读写；`artifact:docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` AC-8/10。

#### IR-6 — 确认原轨迹重匹配的竞争公式

**CLARIFY；AC-5/6 修订 2，依据 §3.3 ③、门 0、运动/尺寸门与 AR1-2。** 原绑定键 o 本帧过门时，竞争者闭集 = 同帧 tracked/unconfirmed 的其他库键，未被门 0 排除、非 removed/ended、有本帧匹配检测且对 o 的同帧有效 prior 通过运动与尺寸门。令原检测 NIS 为 NIS_o，竞争者为 NIS_c；存在 `NIS_c − NIS_o < m_nis` 即 DISPUTED，不取绝对值（竞争者明显更优也撤权），等于 m_nis 不触发。只用本帧 NIS；§3.3 ④ 新键收养的连续帧累计 NIS 竞争规则另行保持。缺原 prior 时不评竞争、不接受原观测，沿 AR1-2 fail-closed。

**完成条件：** `test:tests/test_target_manager.py::ContinuityTests` 覆盖裕度小于/等于/大于、负差、门 0 排除、无检测/失效 prior、removed/ended 与未确认竞争者；锁存时 t0 不刷新、无 FOLLOW/预测 look_at。`::RepairTests` 仍证累计 NIS 两候选规则；关联门不改待标定参数。

#### IR-7 — 固定滚转序列，改掉真值生成初始化点击

**CLARIFY；AC-16/19 修订 1，依据 AC-19、AC-16 与设计 §6 真值隔离。** 确认每序列热身用 k−8…k−1 八张原帧，变换用 k…k+15 十六张连续原帧，各用自身位姿生成绕光轴 H；第 i 张（i=1…16）角度为 `sign·min(i·ω,Θ)`，到 Θ 后保持。基帧规则固定为 [k−8,k+15] 准入连续完整、[k−8,k] 真值框可得且全在画内；合格 k 排序后取第 `floor((i+1)·n/7)` 位（零基索引，i=0…5），必须恰六个互异基帧，不足六个不得缩分母记通过。首次正式回放前冻结规则与配置，不依门读数挑基帧/参数。

**不确认真值框中心作初始化点击：** 当前 `formal_run.py::score_click_point` 的结果经 `roll_sequence` 进入两臂 clicks，虽函数名为 score_，仍把真值派生坐标送入绑定路径，违反 AC-16；静态字符串测试不能证明数据流隔离。真值只可用于已接受的基帧选择、变换后评分与保真叠图，不可生成选择点、轨迹键、修复候选或 KF 输入。两臂各序列使用同一个在原始热身末帧上由人预登记的图像点击；72 序列复用六点，不逐序列再选。

**NEW_OBLIGATION；新 AC-28，唯一来源 IR-7 初始化方式待裁定。** 为上述隔离增加具名可核对的六基点击预登记工件，属于同一 AC-19 离线夹具，不增加设备/模型/Play/ID 或信封额度；不是 AC-27 保真确认，也不改 AC-17 原有两点剧本。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-28 | 首次正式回放前，按固定规则列六个 k，逐个由人只看准入原始 k−1 帧预登记 (frame_id,x_px,y_px)，记录原帧字节 sha、登记人及剧本 sha；不展示真值/模型框/评分。两臂每基各 12 种滚转复用该点。缺点/错帧/sha 不符拒绝启动；不自动补真值点、不基于结果改点或删序列。真值读写与绑定输入的数据流分离，改变评分真值不得改变已登记 clicks 或送入两臂的选择输入 | `test:tests/test_capture_replay.py`（预登记校验、两臂同点、真值改变不改变选择输入）；`test:tests/test_capture_isolation.py`（实际数据流隔离）；`artifact:docs/evidence/P1-ENG-CAPTURE-001-replay.md` §5；`artifact:docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` AC-28 | K4（并入 K1K2K3K4） | 2026-10-09 |

**完成条件：** 实现者移除真值→click 的数据流，补 AC-28 工件与替身回归；记录六基选择和 72 序列/每臂 1,152 帧的展开结果、原评分分母及删失口径。正式回放前由用户完成六点预登记；实现者可先零模型准备原图页面和校验，输出计 A 磁盘。AC-27 用户正在核，本轮不确认、不重做或代写结论。

#### IR-8 — 确认工具内注入，须核实真正换库键

**CLARIFY；AC-18 修订 1，依据 C10 与 AC-18“强制对目标开新轨迹”。** 确认工具内包装关联代价的方式，561–562 帧排除未扰动新臂当时原绑定键，原键保留 lost/prior；不改冻结关联器参数、controller 生产关联规则或直接调用 follow 造成功。唯一完成含义是该两帧确实未给原键量测更新、目标检测生成另一库键且后续成为活跃 tracked；只安装 get_dists 钩子不等于完成。所有能匹配原键的库关联阶段均不得绕过注入，低置信度第二轮关联也需核实。

**完成条件：** `test:tests/test_capture_replay.py` 用真实钉版关联器加缓存/替身检测（零模型）覆盖第一轮与低置信度第二轮，逐帧断言旧键 lost/同帧 prior、新键出现/激活与注入退出后不再排除；正式 `artifact:docs/evidence/P1-ENG-CAPTURE-001-replay.md` §4 给旧/新键、匹配检测索引、帧与修复/报告事件，并照 AC-18 原门判 PASS/FAIL/NOT_EVALUABLE。若没形成新键，只记注入未成立，不当作已完成用例或自动再跑。删检测四种 m 与 auto_repair=off 对照原样保留，全部零推理。

#### IR-9 — 确认安全 hold 通道，预测收据另追加

**CLARIFY；AC-9 修订 1、AC-11 修订 2，依据 C6、AC-11、AR1-3 与 §2.5 A3。** 确认 STOP/STALE/回滚失败经 `BodyCommand.hold(reason)` 的现有机身安全通道写出，收据 `body_safety_hold`、detail.reason 分别 `operator_stop`/`frame_stall`/`binding_rollback_failed`；不扩 `hold_body()` 的 `EXPLICIT_HOLD_REASONS` 三值闭集、不改变兼容模式旧路径。预测云台单列 `predicted_look_at` 收据通道，仅在现有通道闭集末尾追加；经过现行发布最终门及管理器版本/有效期核验，不建立同帧观测资格，不放行机身速度。写失败不得记 WRITTEN。

**完成条件：** `test:tests/test_capture_session.py::StopTests` 与 `::PredictionTests` 核显式 hold、停止后旧效果丢弃、各撤权反例与预测 WRITTEN；`test:tests/test_target_manager.py::CommitTests` 的回滚失败还须经会话安全通道核 hold 收据、无后续新云台效果；既有 `test_explicit_hold_receipts_three_reasons` 断言不放宽。`RECEIPT_CHANNELS` 同步精确追加预测通道，分析工具按该通道计 AC-18/24，不混算观测 look_at。

#### 产物不入仓与下一步

**CLARIFY；AC-20 修订 3，依据 §5.1、信封落实及账本 CAPTURE:A:1 的“outputs/eng-capture/，不入仓”。** 实现角色下一轮在 `.gitignore` 追加 `/outputs/eng-capture/`，不改其他忽略项；提交前以 `git check-ignore outputs/eng-capture/fidelity/` 核覆盖、`git ls-files -- outputs/eng-capture/` 核无已跟踪产物，只提交具名证据摘要。当前仓库 `.gitignore` 缺此行，本轮只读确认该根无 tracked 文件，不写配置、不删除或移动既有产物。

IR-1…9 均已裁定，无 IR 解释待用户放宽；解释成立不等于实现履行。待用户 AC-27 保真确认后交回 Implementation 继续阶段 A：落实 IR-1/7/8/9 等合同与 ignore 行、准备并取得 AC-28 六点预登记，核账及全部回放前置，再首次正式回放→必要窄修→每候选一次停点全套→补齐四项稳定自证后交 `C1@K1K2K3K4`。全过程只用 CAPTURE:A:1 原余额；B 未签 0；LOOP-002 门/暂停、旧债与主张上限不变。AR1-2/3/6 保留至实现及独立核实，本轮不销账、不签任何通过态；只运行角色/文档自检，无测试/模型/Play/板端/下载。

open_items: AR1-2, AR1-3, AR1-6
