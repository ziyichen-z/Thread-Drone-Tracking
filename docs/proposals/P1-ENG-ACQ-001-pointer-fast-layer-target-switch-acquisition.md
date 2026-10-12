# P1-ENG-ACQ-001 — 指针式快层与换目标捕获：常驻关联 + 按 frame_id 轨迹历史 + `designate` 解析器 + 位姿单应补偿（阶段 1，离线 E1/E2）；跟踪中指定 + 无观测转向通道 + 最小伺服（阶段 2）

Status: ACCEPTED（2026-09-28，按 workflow §4.2(a) 接受 D2 当前范围；AR2-1 以接受释义收束，AR2-2 为具名限制；engineering-v1 生效；阶段 1+2 与 Play D1 信封均已由用户分别签发；AC-17 样帧前置已满足，AC-18 待正式 Play）
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（supervisor 无人值守派发的 Fable 子代理；D1 Dispatch-Id `P1-ENG-ACQ-001-D1-20260928T202308Z-224e`；D2 Dispatch-Id `P1-ENG-ACQ-001-D2-20260928T210833Z-4f78`）
Created: 2026-09-28
Last updated: 2026-09-29

> **来历**：用户 2026-09-28 重定义快层目标并按推荐一并裁定（`docs/authorizations.md` 同日「全局 — 用户按推荐入账：主线目标锚定、接口 A、指针式快层方案认可、定局 ③/④/⑥ 窄修订、P1-ENG-LOOP-001 与 P1-ENG-FAST-002 处置、v1 不变项、新工作项 P1-ENG-ACQ-001 / P1-ENG-JET-001」，下称「账本 09-28」，其 A–D 条按字母/序号引用）。本项是账本 09-28 D.8 点名的第一个新工程工作项，落实 C（指针式快层方案）与 D.1/D.2/D.6/D.7。
> **方案输入**（不是合同、不是证据；AC-n 以本提案为准）：`docs/evidence/fast-layer-research-2026-09-28/fast-layer-plan-2026-09-28.md` §0/§2/§3/§4/§6 与同目录 `A1-repo-facts.md`、`A2-external-survey.md`、`A3-jetson-feasibility.md`。本提案引用的仓库事实全部由本会话在 HEAD `0a6d2c2` 只读复核（§0），调研文件只作出处提示。
> **承接**：`P1-ENG-LOOP-001`（`CLOSED_SUPERSEDED`/`ENDED`）债务清单与 `P1-ENG-FAST-002`（`QUALIFICATION_GATE_NOT_MET`/`ENDED`）插件代码复核与可复用资产，按 `docs/parked-status.md`「P1-ENG-LOOP-001 收口与 P1-ENG-ACQ-001 承接（2026-09-28）」「P1-ENG-FAST-002 阶段 1 收口与承接（2026-09-28）」逐条列于 §2.5。
> **Jetson**：部署拓扑已由用户裁定（账本 09-28「全局 — 用户裁定：VLM 与快层部署到 Jetson…」），板端探测归 `P1-ENG-JET-001` 另立项；本项零 Jetson 主张。

## 0. 现状与只读事实（本会话只读核实；符号名以 HEAD `0a6d2c2` 为准，实现时按符号名重定位；零模型运行、零训练、零写入 `runtime/` 与数据根）

| # | 事实 | 来源 |
|---|---|---|
| 1 | 插件协议 `TrackerPlugin` 只有 `init(image, box_norm)->bool`、`update(image)->TrackerResult`、`manifest_identity()`；`update` 不带 `frame_id`，也不带相机位姿 | `controller/trackers.py`（`TrackerPlugin`、`TrackerResult`） |
| 2 | `det-assoc-v1`：`init()` 每次 `self._tracker = self._tracker_factory(...)` **新建关联器**（库 ID 从 1 重来），在初始化帧调一次 `_step`，绑定 = 与用户框 IoU 最大且 ≥ `BIND_IOU`；`update()` 在 `self._bound_id is None` 时**直接返回 `lost(not_initialized)`、不跑检测**；绑定 id 在 `lost_stracks` → `bound_track_unmatched`，否则 `bound_track_removed`；从不改绑；`_step` 每帧拿到库输出的全部 track 行 `[x1,y1,x2,y2,track_id,score,cls,idx]` 但只挑绑定 id；构造函数接受 `model_loader` / `tracker_factory` 注入 | `controller/det_assoc_tracker.py`（`DetAssocTracker.__init__/_step/init/update`、`BIND_IOU`、`REASON_*`） |
| 3 | 冻结规格：BoT-SORT、`gmc_method: sparseOptFlow`、`match_thresh 0.7`、`track_buffer 30`（按 `update` 调用计，5 Hz ≈ 6 s）、`with_reid false`；`conf 0.25`、`imgsz 640`、`device_policy mps→cpu`；权重 `outputs/eng-det/runs/run-1/weights/last.pt` sha256 `d6a0d6a9…059c9`、5,458,330 B；冻结记录 `docs/evidence/P1-ENG-FAST-002-freeze.json` sha256 `f231e450…c93c`（本机两者已复核一致） | `config/det-assoc-v1.models.json`；`docs/evidence/P1-ENG-FAST-002-freeze.json`；本机 `shasum -a 256` |
| 4 | ultralytics 8.4.104（主树与数据根 venv 均为此版本）：`BYTETracker.update` 在 KF 预测后、首轮关联前调用 `self._pre_first_associate(strack_pool, unconfirmed, img, results_high)`（BoT-SORT 在此施加 GMC warp）；实例持有 `tracked_stracks / lost_stracks / removed_stracks` 与 `frame_id`（= `update` 调用数） | `.venv-yoloe/lib/python3.12/site-packages/ultralytics/trackers/byte_tracker.py`（`update`、`_pre_first_associate`） |
| 5 | `TrackLoop.process_available` 逐帧 `self.tracker.update(bundle.image)`（只传图像），只对批末帧 `_publish_latest`：云台指令 = 框底中点射线 ∩ 显式水平面（`box_ground_intersection`）→ `look_at_world`；无预测前馈、无像素残差、无限速 | `controller/track_loop.py`（`process_available`、`_publish_latest`）；`controller/geolocate.py` |
| 6 | `GatedPublisher`：`hold_body`/`set_nadir` 永远透传；`look_at`/`body_command` 只在同帧观测已 `WRITTEN` 时透传，否则 `PUBLISH_REJECTED(orphan_control)` 并置 fatal；发布最终门五项（快照、JPEG sha、元数据、`0 ≤ L_w − frame_id ≤ K_pub`、`≤ T_pub`），①④ 不过即 `catchup_stale` | `controller/gated_publisher.py`（`GatedPublisher._derived`、`observation`、`_gate`）；`controller/language_loop.py`（`K_PUB = 2`、`T_CONF_S = 10.0`） |
| 7 | 语言会话：`_ASK_STATES = {IDLE, QUERYING, AWAITING_CONFIRMATION, LOST, REINIT_REQUIRED}`，不含 `TRACKING`/`SUSPECTED`（`TRACKING` 下 `ask`/`respecify` 回执 `REQUEST_INVALID`；`respecify` 在 `SUSPECTED` 等价 `confirm_lost` 后再问，先 finalize 旧段）；`_seed_segment` 每段 `create_tracker(self.config.tracker_name)` **新建跟踪器与 TrackLoop**，在查询帧 N 上 `init` 后回放到 latest；`_advance_segment` 无活段即不处理帧；`retired_track_ids` 段 finalize 时追加恰一次；`tracker_name` 缺省 `nanotrack-v2` | `controller/language_loop.py`（`_ASK_STATES`、`_seed_segment`、`_advance_segment`、`SessionConfig.tracker_name`） |
| 8 | 语言桥闭集：9 个动作、9 个结果状态、8 个会话状态、21 个 `STATE_REASONS`；请求信封无「框 + frame_id」字段；VLM 结果包已带 `frame_id`、`frame_sha256` 与框（接口 A 形态现成） | `controller/language_bridge.py`（`ACTIONS`、`RESULT_STATUS`、`SESSION_STATES`、`STATE_REASONS`）；`controller/language_loop.py`（结果包字段） |
| 9 | 帧元数据 `tethered-sensor-frame/v1`：`frame_id`、`simulation_time_s`、`capture_unix_s`、`camera_position_world_m`、`camera_rotation_xyzw`、`camera_forward/right/up_world`、`vertical_fov_deg 60`、`horizontal_fov_deg 75.178`、`intrinsics_px {fx=fy=415.692, cx 320, cy 240}`、`gimbal_saturated`、`tether_saturated`；这是平台自身状态（与既有 LOS 落地点、机身规划器已读的同一份元数据），不是目标真值。缺省 `capture_hz 5`、`retained_frame_count 128` | 数据根 `runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames/frame_0000000000.json`；`config/scenario.default.json` |
| 10 | 冻结检测缓存（主树，`.gitignore` 已排除 `outputs/eng-det/`）：`frozen-B.jsonl.gz` 1,664 帧（scout-1 768 + m3-armA 7×128）sha256 `412592fb…da5c`；`frozen-V.jsonl.gz` 3,168 帧（a7）sha256 `783ec7e2…c41`；两者头部 `weights_sha256` 与事实 3 一致，`conf 0.25 / imgsz 640 / device mps`；每帧 `dets = [x,y,w,h(归一),conf,cls]`；`frozen-H.jsonl.gz` 存在但本项不用 | `outputs/eng-det/dets/`；本机 `shasum -a 256` 与只读解析 |
| 11 | 数据根 `~/TetheredDroneTracking-full`（`tools/eng_det/common.py` 的 `DATA_ROOT`，可由 `ENG_DET_DATA_ROOT` 覆盖，整体只读保护）：三序列逐帧 sidecar 齐全（缺失 0，见 §8）；索引 `outputs/eng-fast/P1-ENG-FAST-001/cache/catalog-index.jsonl.gz`（每帧 OK 可见静止车 `{object_id, box, class_word, color_word, depth_m, referable}` + `dynamic` 红车框）与 `catalog-sim-times.jsonl.gz`（每帧仿真时刻）；数据根 `.venv-yoloe` 有 `lap 0.5.13`，主树 `.venv-yoloe` 无 `lap` | `tools/eng_det/common.py`；本机 `ls`/只读解析；`.venv-yoloe/bin/python -c "import lap"` 失败 |
| 12 | 关联回放件现成：`tools/eng_fast/replay.run_sequence(tracker, frames)` 每帧恰一次 `update(boxes, img)` 并返回每帧全部输出行；`tools/eng_det/evaluate.tracker_for/replay_piece` 按冻结参数建 BoT-SORT（`botsort` 时惰性读 JPEG 供 GMC）；`replay.bind` 用真值 IoU ≥ 0.3 逐帧绑定（只用于评分）；`tools/eng_det/plugin_replay.run_piece` 是口径 B 插件本体回放；FAST-001 R1-2 `SCOPE_GAP`：`window_outcome` 在 >8 s 空窗上可零证据判 `KEPT` | `tools/eng_fast/replay.py`；`tools/eng_det/evaluate.py`；`tools/eng_det/plugin_replay.py`；`docs/implementation-status.md` 账本 R1-2 行 |
| 13 | 可复用几何件：`controller/reanchor.py` 的 `world_los`、`angular_distance`、`box_iou`、`FrameHistory`（按采集单调时钟 6 s）、`replay_tracker`；`controller/geolocate.box_ground_intersection` 需显式 `ground_plane_y_m`（M2a 规则：不得从路线真值推导） | `controller/reanchor.py`；`controller/geolocate.py` |
| 14 | C2 逐行预测（609 行）在数据根 `outputs/eng-sft/P1-ENG-SFT-002/returned/sft-20260918T223245Z-bd1f5ebb/predictions/eval-adapter.jsonl`，金标 `data/eval.jsonl`；本会话只读复算：`unique` 442 / `ambiguous` 46 / `none` 121；金标与预测均 `unique` 的 347 行 IoU 中位 0.862、p25 0.743、p10 0.358、≥ 0.5 占 0.870、≥ 0.3 占 0.905。609 行全部落在 H 保留帧 | 数据根只读解析；`docs/evidence/P1-ENG-SFT-002-eval-manifest.json` |
| 15 | 云台：`gimbal_command.json` 只有 `look_at_world` / `nadir`（世界点，不是角度）；Unity 侧离底 ≤ 45°、`RotateTowards` 120°/s、过期不回中；机身阈值规划器（`P1-M3-BODY-001` 冻结参数）只在批末帧且跟踪 ok 时决策，无观测即 `hold`，速度指令须绑同帧 `WRITTEN` 观测 | `controller/gimbal_entry.py`；`Assets/TetheredTracking/Scripts/TetheredGimbal.cs`；`controller/body_planner.py`；`controller/track_loop.py` |
| 16 | 真值隔离：`CoverageEvaluator` 只认 `track_id == "target-0"` 且只有红车有真值 → 静止车的居中成败只能离线复算（`tools/dist_data/project_boxes.py` 可对归档 Play 帧算投影框）或人工目检；投影框不得作为运行时输入 | `Assets/TetheredTracking/Scripts/CoverageEvaluator.cs`；`CLAUDE.md`；`runtime/README.md` |
| 17 | （D2）三个解释器（主树 `.venv-track`、主树 `.venv-yoloe`、数据根 `.venv-yoloe`）均有 `cv2 5.0.0` 且 `hasattr(cv2, "TrackerNano")` 为真；`nanotrack-v2` 规格 `config/nanotrack-v2.models.json`、模型文件本地已有；`NanoTrackV2Tracker.update` 对库 `ok=False` 返回 `lost("tracker_reported_failure")`、分数非有限或越界返回 `lost(...)`，并非「恒返回成功」 | 本机只读 `python -c "import cv2"` 探针；`controller/trackers.py`（`NanoTrackV2Tracker.init/update`） |
| 18 | （D2）`controller/reanchor.replay_tracker(tracker_factory, history, *, source_frame_id, source_box_norm, target_head_frame_id, maximum_source_age_s, catchup_timeout_s, monotonic)`：源/目标/中间帧缺失 → `RESEED_DISCARDED_MISSING_FRAME`，源帧过旧 → `RESEED_DISCARDED_STALE`，`init` 失败 → `RESEED_FAILED`，回放中任一帧 `not ok` 或框无效 → `RESEED_DISCARDED_INVALID_BOX`，超时 → `RESEED_DISCARDED_NOT_CONVERGED`，否则 `RESEED_READY`（带回放后的跟踪器与 `last_result`）；`history` 只需 `get(frame_id)` 与 `after_through(a, b)`（帧 id 须连续，否则 `FileNotFoundError`） | `controller/reanchor.py`（`replay_tracker`、`FrameHistory.get/after_through`、`ReplayResult`） |
| 19 | （D2）ultralytics 8.4.104 `BYTETracker.update` 的返回只含 `tracked_stracks` 中 `is_activated` 的轨迹行；`lost_stracks` 各轨迹的 KF 预测框可由 `STrack.xyxy` 读出；`removed_stracks` 保留被移除轨迹 | `.venv-yoloe/.../ultralytics/trackers/byte_tracker.py`（`update` 末行、`STrack.xyxy`、`lost_stracks`/`removed_stracks`） |
| 20 | （D2）`TrackLoop.process_available` 按 `expected_ids = range(last+1, latest+1)` 逐帧 `repository.load(id)`（缺帧 → `GAP` 终止；回退 → `REINIT_REQUIRED`），每个 bundle 含 `frame_id`、`image`、`metadata`，随后 `self.tracker.update(bundle.image)`；`FrameRepository.load(frame_id)` 读 `runtime/frames/` 保留桶（`retained_frame_count` 128）并校验元数据 `frame_id` 一致 | `controller/track_loop.py`（`FrameRepository.load`、`process_available`） |

## 1. 目的与价值

主线目标（`docs/project-background.md` §3，逐字）：

> 做一个闭环系统：语言指定目标，快层跟上并保持居中，换目标时能迁移并跟上新目标，丢失与歧义显式报告。VLM 是主角（接口 A：输出框 + 所在 frame_id）；快层是非变量，但必须能换目标。部署目标是 VLM 与快层跑在 Jetson Orin Nano 8GB（headless），Unity 留桌面机。项目的难点是「发现目标 → 跟上」，不是保持跟踪。验证只看四类数字：陈旧指定解析成功率随延迟、转向存活率、捕获时间与成功率按偏角/距离分桶、误锁率与显式报告比例。不作为目标：单目标稳态保持率不设资格门；不做 ReID、SAM 2 在线、更大模型、INT8、SAHI、Unity 场景改动；不为快层做研究主张；VLM 剪枝等优化只在闭环跑通且曲线证明延迟重要之后。

本项把「快层必须能换目标」落成代码与四类数字中的前两类（阶段 1）并接通第三、四类的采集通道（阶段 2 + Play D1）：

- **问题**：现状快层是「单目标 SOT / 一次绑定不改绑」（事实 2、7）：切换目标只能 `release` 后重新 `init`，而 VLM 框到手时已旧 4–13 s（`docs/evidence/P1-ENG-LOOP-001-measurement-report.md`：5060 p50 4.18 s、p95 5.43 s；含人工确认 8–13 s），在旧帧 `init` 再回放积压帧正是 LOOP-001 诊断 6 `catchup_stale` 硬停止的机制根因（其提案 rulings R-B12/13）。
- **做法**：检测 + 多目标关联从会话开始常驻逐帧跑，对画面内所有车维护 track ID 与按 `frame_id` 的轨迹历史；被跟目标只是一个指向某 ID 的**指针**；VLM 的 `(box, frame_id=k)` 在 k 帧的历史里同帧匹配拿 ID，沿 ID 走到当前帧；换目标 = 改指针，不重建关联器；相机自运动用帧元数据位姿算纯旋转单应补偿；轨迹已死则以 k 帧位姿 + 框算世界点转向重捕。
- **价值**：快层仍是非变量（不重训、不加 ReID、冻结规格不动），但从「不能换目标」变成「能换目标并能说清为什么没换成」（六值闭集）；E1/E2 用仓库已有的检测缓存与位姿 sidecar 零消耗地量出「延迟 + 转向」叠加下指针能不能保住，这是方案最大的不确定点。数字只描述，不设门（账本 09-28 A、C）。

三层任务对应：层 1「保持居中」= §3.1/§3.8（常驻底座 + 最小伺服）；层 2「换目标迁移并跟上」= §3.2–§3.7；层 3 Jetson = `P1-ENG-JET-001`（本项不做）。

## 2. 范围与不做的事

### 2.1 阶段 1（离线候选；零训练、零 Play、零新检测推理）

- S1-a **常驻关联**：`det-assoc-v1` 去掉「无绑定直接返回」；无指针时同样逐帧 `_step` 并记历史，对外 `TrackerResult.lost("no_pointer")`。
- S1-b **按 `frame_id` 的轨迹历史**：深度 ≥ 100 帧（申请值 128 = `retained_frame_count`），键为传感器 `frame_id`，每条含该帧相机位姿与全部 track 行（§3.2）。
- S1-c **`designate(box_norm, frame_id)` 解析器**与六值闭集 `BOUND / BOUND_COASTING / TRACK_ENDED / NO_TRACK_AT_K / AMBIGUOUS / FRAME_NOT_IN_HISTORY`（§3.4）。
- S1-d **指针**：`follow(track_id)`；切换只改指针，不得走 `init` 重建关联器（§3.5）。
- S1-e **位姿单应补偿**：由相邻帧元数据位姿差算 H = K·R_Δ·K⁻¹，经 `_pre_first_associate` 子类钩子在关联前施加到全部轨迹预测框；`gmc_source ∈ {pose, optflow, none}` 可选，缺省 `pose`（§3.3）。
- S1-f **载体接入**：`TrackLoop` 向支持常驻协议的插件传 `frame_id` 与元数据；旧插件（csrt / nanotrack-v2）路径不变；`tracking_observation.json` schema v1 不改。
- S1-g **离线 E1/E2**（§3.9）：只用 scout-1、m3-armA、a7 三序列（账本 09-28 D.7），检测来自冻结缓存，CPU 回放；产出两组曲线 + E1 十五桶分布表 + 位姿单应自检表，写 `docs/evidence/`。
- S1-h **第二级「k 帧起跟回放」**（账本 09-28 C 三级解析之第二级；AR1-1）：第一级在 k 帧无轨迹过门时，用冻结 `nanotrack-v2` 在 k 帧图像上起跟、经与载体同一 `FrameRepository` 有界回放到常驻关联器已处理的最新帧 h，再由 h 帧检测轨迹按同帧判据「收养」；SOT 实例一次性、不发布、不触碰常驻关联器；结果映射进六值闭集，不加第七值（§3.4.1）。

### 2.2 阶段 2（在线候选；零 Play）

- S2-a **状态机放行跟踪中指定**：`TRACKING`/`SUSPECTED` 下允许 `ask`/`respecify`；`confirm` 走 `designate`，按六值处置（§3.6）。
- S2-b **无同帧观测的转向通道**（`TRACK_ENDED` 分支）及安全语义：每次指定至多一次、时限、到位判据、N-of-M 收养、失败回 `hold` 并报 `ACQUIRE_FAILED`（§3.7）。
- S2-c **最小伺服**：每个处理帧对指针 track 发 `look_at`，云台步进限速（§3.8）。
- S2-d **候选来源后端 `candidates`**：把当前帧的检测 track 作为候选呈现给操作者（不经 VLM），供 Play D1 与载体自测使用；下游 `confirm → designate` 路径与 VLM 路径完全相同（§3.10）。
- 阶段 1 完成即写证据并**直接进入阶段 2，不设门、不等待裁定**；两阶段合并为一个候选走 `K1K2K3`（§7）。

### 2.3 v1 不变项与定局窄修订（账本 09-28 D.1 / D.2 / D.6，逐字纳入合同）

- **定局 ④/⑥ 窄修订（D.1）**：「人确认一次指定后，执行该指定所需的解析、转向、重捕由系统自动完成并逐步上报；捕获后的丢失仍只由人处置。」→ §3.6/§3.7 的自动动作仅限「同一 `designation_id` 之内」；`ACQUIRE_FAILED` 与捕获后任何丢失都停在人工路径，不自动重播种。
- **定局 ③ 修订（D.2）**：v1 换目标演示允许以静止布局车为切换对象 → Play D1 剧本以静止车 B/C 为切换对象（§3.10）。
- **v1 不变项（D.6）**：5 Hz 不变；不变焦；不加 ReID；不重训检测器；Unity 零改动（场景、脚本、协议）；候选池 = 默认锚点附近可居中的静止车（约 4–6 辆，取决于 Play 时的实际可见性）+ 运动红车；改锚点位置属配置改动，需另裁定，本项不申请。
- 冻结规格（事实 3）逐字不改：`track_buffer 30`、`match_thresh 0.7`、`conf 0.25`、权重与 `freeze.json` sha 不变；E2 的 buffer 扫描只在离线线束里改传入参数，不改 `config/det-assoc-v1.models.json`。

### 2.4 明确不做（备忘 §6 + 主线 §3 不做清单 + 本项自限）

不重训检测器；不做 ReID；SAM 2 只作离线参照、不接入；不换 4B；不做 INT8；不做 SAHI；不改 VLM 协议与训练范式（接口 A = VLM 出框 + `frame_id`，不改为选候选 ID）；不改 Unity 场景与脚本；不做「旧框按相机运动平移后在当前帧 init SOT」（第二级只在 k 帧图像上起跟，§3.4.1）；第二级的 SOT 框不发布、不进观测与历史；不做无人确认的自动重播种；不为快层做研究主张；不设保持率/召回资格门；不再评 H 域、不用 H 域序列做 E1/E2（`frozen-H.jsonl.gz` 不读）；不做 LOS 预测前馈与像素残差（设计 §3.6 完整版）、不做 50 Hz 云台回路、不改云台为角度/角速率模式；不改机身阈值规划器（冻结 sha）；不做变焦；不做 Jetson/TensorRT；不把 §3.9 的离线数字外推为在线成绩。

### 2.5 承接清单（来源：`docs/parked-status.md` 两节；处置由本项 AC 落实，原 verdict 与账本状态不改）

| # | 来源 | 义务原文要点 | 本项处置 | AC |
|---|---|---|---|---|
| H-1 | LOOP-001 承接 1 | F3 `SCOPE_GAP`/OPEN：下次触及 `LanguageWorker` 或扩展延迟/排队域前承接独立在途起点及回归，保留查询帧年龄起点 | 阶段 2 不改 `LanguageWorker`、不扩延迟/排队域；候选须逐字声明触及与否；若触及则先加在途起点回归并如实报告 | AC-10 |
| H-2 | LOOP-001 承接 1 | F8 `SCOPE_GAP`/OPEN：复用可变归档、允许人工改写或发现来源不一致前承接元数据哈希/时刻一致性回归 | E1/E2 读的是数据根只读归档，不改写；线束对每帧核对 JPEG sha 与 sidecar `frame_id`/时刻一致，不一致即停并报告（不销账） | AC-9、AC-10 |
| H-3 | LOOP-001 承接 2 | AC-13…15 正式 Play 验收 `NOT_RUN`，诊断 5/6 不进证据链 | 本项不把旧 AC 写成已满足；闭环行为在本项以自己的 Play D1 剧本另签验证（§3.10、AC-18） | AC-18 |
| H-4 | LOOP-001 承接 3 | 人眼保真记录只覆盖当时采集/保存/预览管线；触及即重做 | S2-d 的候选预览触及预览路径 → Play D1 前须重做人眼保真检查（≥ 2 张样帧）并记入证据 | AC-17 |
| H-5 | LOOP-001 承接 4 | 5060 F 盘 `repo-b` 副本、`runtime/hold-diag-loopb-*` 隔离物与诊断 6 留在 `runtime/` 的桥文件与帧，按来源与保留要求清理 | 先出清理清单（路径、来源、大小、保留理由）写证据；本地删除与 5060 远端删除均为不可逆动作，**待用户裁定**（§7 (g)）；未裁定前零删除 | AC-16 |
| H-6 | LOOP-001 收口裁定 | AC-3 修订 3（静音多批追平 + T_catchup 6 s）与 AC-12 修订 7 未实现；诊断 6 `catchup_stale` 硬停止保留 | 本项以常驻逐帧处理**取代**「在 N 帧 init + 回放积压」机制，不实现 T_catchup；发布最终门五项与 `K_pub`/`T_pub`/`T_stall` 数值不变（§3.5）；诊断 6 记录不改 | AC-6 |
| H-7 | FAST-002 承接 | 插件 `controller/det_assoc_tracker.py` 及其工厂/CLI 接入的代码复核并入本项 K3 | 本项候选的 `R1@K1K2K3` 复核范围明写「整个 `det_assoc_tracker.py` + `trackers.py` 工厂 + `track_loop.py` CLI 闭集」，不只看 diff | AC-12 |
| H-8 | FAST-002 承接 | 权重、`freeze.json`、数据集工具、检测缓存复用前须核实本机文件、来源、散列与 AC-4 口径偏差；旧 H 回放读数不作新项证据 | AC-11 逐项记散列（本会话已复核，§0 事实 3/10）；AC-4 偏差（IR-4 分组、scout-1 63 个整帧排除帧）以声明方式写进 E1/E2 报告；报告不引用 FAST-002 的 G-5/G-6/H 读数为证据 | AC-11 |
| H-9 | FAST-001 R1-2 | `window_outcome` 在 >8 s 空窗零证据 `KEPT`（`SCOPE_GAP`/OPEN） | 三序列最大帧间隔 0.325 s（§8），不可达；E2 复用 `window_summary` 前在线束里加「空窗即拒绝」断言并记入报告 | AC-8 |

## 3. 接口与数据契约

### 3.1 常驻插件协议与调用路径（K3；AR1-3）

`DetAssocTracker` 增加构造参数 `mode ∈ {compat, resident}`（缺省 `compat`）；`create_tracker("det-assoc-v1")` 不带参数时仍返回 `compat` 实例（旧路径与口径 B 测试零改动）；常驻实例只由新增的 `create_tracker("det-assoc-v1", resident=True)`（等价 `DetAssocTracker(mode="resident")`）产生。两种模式的方法集互斥，误用即抛 `ProtocolMisuse`（`RuntimeError` 子类），不静默降级；`update` **不再**声称等价于 `step`，D1 的该句撤回：

| 模式 | 允许的方法 | 「同帧至多一次检测/关联」的判据 | 历史 |
|---|---|---|---|
| `compat` | `init(image, box)`、`update(image)`、`manifest_identity()`（现有代码路径逐字不变） | 只有 `init`（初始化帧一次）与 `init` 之后的每次 `update` 调 `_step`，`_detect` 调用数 = 1 + `update` 次数；`update` 早于 `init` 仍返回 `lost(tracker_not_initialized)` 且不检测 | 不建历史；`history(k)` 恒 `None`；`step`/`designate`/`follow`/`pointer_result` 抛 `ProtocolMisuse` |
| `resident` | `step(image, frame_id, metadata)`、`pointer_result(frame_id)`、`designate(box, k)`、`follow(id)`、`pointer()`、`history(k)`、`manifest_identity()` | 只有 `step` 调 `_step`，`_detect` 调用数 = `step` 次数；`frame_id` 须严格大于上一次 `step` 的 `frame_id`，同帧重复或回退抛 `ProtocolMisuse` 且不检测；`init`/`update` 抛 `ProtocolMisuse` | 每次 `step` 写恰一条，键 = 传入的传感器 `frame_id` |

- `step(image, frame_id: int, metadata: Mapping) -> FrameTracks`：检测 + 关联（按 `gmc_source` 用 `metadata` 位姿补偿）→ 写历史 → 返回该帧全部行（`track_id, box_norm, score, cls, state ∈ {tracked, lost}`；`tracked` 行取库输出，`lost` 行取 `lost_stracks` 的 KF 预测框，事实 19）。
- `pointer_result(frame_id) -> TrackerResult`：纯读历史、不检测；无指针 → `lost("no_pointer")`；指针 track 在该帧 `tracked` → ok 行；在 `lost` 池 → `lost(bound_track_unmatched)`；不在任何池 → `lost(bound_track_removed)`。载体每帧 `step` 后恰调用一次。
- **载体路径**：`TrackLoop` 构造时按是否具备 `step` 判定常驻协议。常驻路径以 `TrackLoop.start(frame_id)`（不带框、不调 `init`）开始；`process_available` 对每个 bundle 调 `step(bundle.image, bundle.frame_id, bundle.metadata)` 再调 `pointer_result(bundle.frame_id)`，此后的 `(state, box, reason)` 语义、发布门与记录路径与现有 `update` 路径共用；在常驻插件上调用 `TrackLoop.initialize(frame_id, box)` 抛 `ProtocolMisuse`。旧插件（`csrt`、`nanotrack-v2`、`compat` 模式 `det-assoc-v1`）的 `initialize → init`、`process_available → update` 调用序列逐字不变（AC-6 以间谍记录调用序列证明）。
- **历史键只取传感器 `frame_id`**：`library_frame_id`（库调用计数）单独记在条目里供核对，绝不作键；AC-2 用非连续起点（`frame_id` 自 1000 起）证明 `history(1000)` 命中而 `history(1)` 为 `None`。
- **同一实现两条路径**：`designate`/`follow`/`pointer`/`history` 与三级解析逻辑放在无 ultralytics 依赖的 `controller/resident_core.py`（`ResidentCore.record(frame_id, metadata, tracked_rows, lost_rows, removed_ids)` + 解析方法），插件 `step` 与 §3.9 线束共用（AC-6 用缓存检测替身证明两条路径逐帧一致）；`controller/` 不导入任何真值/索引模块（AC-9）。
- `manifest_identity()` 增 `mode`、`history_depth`、`gmc_source`、`level2 {tracker: "nanotrack-v2", model_sha256, t_replay_s}`；权重/规格/冻结 sha 三项不变。

### 3.2 轨迹历史（K1：时间语义）

- 环形缓冲，容量 `history_depth`（申请 128；下限 100）；键 = 传感器 `frame_id`（不是库 `frame_id`）；每条：`frame_id`、`simulation_time_s`、`capture_monotonic_s`、`camera_position_world_m`、`camera_rotation_xyzw`、`intrinsics_px`、`library_frame_id`（只记录、不作键）、`tracks[]`（`state ∈ {tracked, lost}`；`lost` 行为 KF 预测框，事实 19）、`removed_ids[]`（该帧被移除的 ID）。
- 查询 `history(k)`：k 不在缓冲 → `None`（→ `FRAME_NOT_IN_HISTORY`）。内存量级：每帧 ≤ 20 行 × 8 浮点，128 帧 < 1 MB。
- 帧序：`frame_id` 必须严格递增；回退或缺帧沿用 `TrackLoop` 既有 `frame_id_reset_or_rollback` / GAP 终止语义，历史随会话终止清空。

### 3.3 位姿单应补偿（K1/K3）

- 相邻处理帧 t−1 → t：R_Δ 由两帧 `camera_rotation_xyzw` 求得，H = K·R_Δ·K⁻¹（K 由 `intrinsics_px`），纯旋转、与景深无关；机身平移在 v1 忽略（25 m 高度、目标 ≥ 25 m 时视差每帧约 10 px 量级 [估计]，E2 读数会把它包含在残差里）。
- 施加点：`BOTSORT` 子类覆写 `_pre_first_associate`，在库 KF 预测后、首轮关联前，把 H 施加于 `strack_pool` 与 `unconfirmed` 的预测框（对四角施加 3×3 再取 AABB，或退化为库 `multi_gmc` 的 2×3；由 AC-5 的合成测试择一）。`gmc_source=optflow` 时保留库原 `sparseOptFlow`；`none` 时单位阵。
- 位姿来源只允许该帧自身元数据（事实 9）；禁止读取任何目标真值。

### 3.4 `designate(box_norm, k)` 解析器与六值闭集（K3；AR1-1）

参数（申请值；按 D1 裁定 (d) 作插件配置项并记录生效值，不改冻结规格）：`τ = 0.5`、次佳裕度 `m = 0.2`、备用判据「轨迹框中心落在指定框内」、`BOUND_COASTING` 等待上限 = `track_buffer`（30 次调用）、第二级 `T_replay = 2.0 s`（墙钟）、`L_replay ≤ history_depth`（帧）。

解析按账本 09-28 C 的三级顺序执行，在同一 `designation_id` 内自动完成并逐步上报（D.1）：**第一级** 同帧历史匹配（在 `history(k)` 的 `tracked` 行上比较，不含运动误差）；**第二级** k 帧起跟回放（仅当第一级无轨迹过门，§3.4.1）；**第三级** 世界点转向重捕（仅当命中轨迹已死；阶段 2 §3.7）。结果值只有六个；`resolution_level ∈ {1, 2}` 与 `level2` 子记录作为字段随结果写出，不构成第七个值。h = `designate` 调用时常驻关联器已处理的最新传感器帧（历史头）。

| 结果 | 条件 | 动作 |
|---|---|---|
| `BOUND` | (L1) 存在 j：IoU(box, box_j@k) ≥ τ 且 best − second ≥ m（或唯一满足备用判据），且 j 在 h 帧 `tracked`；或 (L2) 回放到 h 后被 h 帧某 `tracked` 轨迹 j 唯一收养 | `follow(j)`；新 `designation_id`；对外 `track_id` 换新纪元 |
| `BOUND_COASTING` | (L1) 同上但 j 在 h 帧位于 `lost_stracks` | `follow(j)`；观测按 `TrackLoop` 既有 LOST 语义不发；库在 buffer 内找回 → 自动回 `BOUND`；超时 → 转 `TRACK_ENDED` 处置 |
| `TRACK_ENDED` | (L1) 命中的 j 已在 `removed_stracks` 或不在任何池 | 阶段 1：只报告；阶段 2：第三级世界点转向通道（§3.7） |
| `NO_TRACK_AT_K` | (L1) k 帧无 `tracked` 轨迹过门，**且** (L2) 起跟回放未被收养或未能尝试（`level2.reason` 闭集见 §3.4.1） | 只报告；指针不变；由人决定再问 |
| `AMBIGUOUS` | (L1) k 帧 ≥ 2 条轨迹过门且裕度 < m；或 (L2) 收养时 h 帧 ≥ 2 条轨迹过门且裕度 < m | 只报告；指针不变；候选列表走既有确认界面 |
| `FRAME_NOT_IN_HISTORY` | `history(k)` 为 `None`（第二级不尝试） | 只报告；拒绝，重新查询 |

`VLM_NONE` / `VLM_MULTI` 是 VLM 自报（既有三态），到不了解析器，不在闭集内。解析结果写入 `tracker_state` 桥文件新字段 `designation {designation_id, frame_id_k, head_frame_id, result, resolution_level, track_id, level2}` 与会话 JSONL；`runtime/README.md` 同步。

#### 3.4.1 第二级：k 帧起跟回放与收养（K3；AR1-1）

- **触发**：第一级在 `history(k)` 上无 `tracked` 轨迹过门且 `history(k)` 存在。`AMBIGUOUS`、`TRACK_ENDED`、`FRAME_NOT_IN_HISTORY` 不触发第二级。
- **帧源**：与载体同一 `FrameRepository`（事实 20；离线线束为数据根归档），经适配器 `RepositoryFrameWindow(repository, k, h)` 提供 `get`/`after_through`，供事实 18 的 `replay_tracker` 原样复用；不新建内存帧缓存；`history_depth` 128 = `retained_frame_count` 128，二者同步淘汰。
- **回放**：`replay_tracker(tracker_factory=<注入的 nanotrack-v2 工厂>, history=window, source_frame_id=k, source_box_norm=box, target_head_frame_id=h, maximum_source_age_s=history_depth/capture_hz, catchup_timeout_s=T_replay)`。SOT 实例每次指定新建、只在本次 `designate` 内存活、结束即丢弃；其 `init` 作用于 SOT 实例，**不是** `DetAssocTracker.init`；常驻关联器对象、库 `frame_id`、各轨迹 ID 在回放前后不变（AC-4/AC-19 以对象身份与 ID 集合钉死）。回放同步执行、上界 `T_replay`，期间不 `step` 新帧、不发布；回放结束后到达的帧走常驻 `step` 追平（不是 init 回放），发布最终门五项与 `K_pub`/`T_pub`/`T_stall` 不变。
- **收养判据**（h 帧同帧一次判定）：候选 = `history(h)` 的 `tracked` 行；IoU(SOT 框@h, box_j@h) ≥ τ 且 best − second ≥ m（或唯一满足备用判据）→ 收养 j → `BOUND`（`resolution_level 2`）；≥ 2 条过门且裕度 < m → `AMBIGUOUS`（候选列表 = 过门轨迹）；无过门 → 失败 `no_adoption`。SOT 的框本身从不发布、不进观测、不进历史。
- **失败上报**（全部映射为 `NO_TRACK_AT_K`；`level2.reason` 闭集）：`not_attempted_frame_missing`（`history(k)` 有但帧源缺 k 或中间帧；`RESEED_DISCARDED_MISSING_FRAME`）、`source_too_old`（`RESEED_DISCARDED_STALE`）、`sot_init_failed`（`RESEED_FAILED`）、`sot_lost@<frame_id>`（`RESEED_DISCARDED_INVALID_BOX`：回放中某帧 `not ok` 或框无效/出画）、`replay_timeout@<frame_id>`（`RESEED_DISCARDED_NOT_CONVERGED`）、`no_adoption`。会话 JSONL 逐步记 `L2_STARTED{k, h}` → `L2_ADOPTED{track_id}` / `L2_AMBIGUOUS{candidates}` / `L2_FAILED{reason, replayed_frames, elapsed_ms}`。
- **可构造测试**（AC-19；SOT 用 `ScriptedTracker` 替身、检测器用缓存替身、`monotonic` 可注入）：(a) 成功：k 帧检测替身漏检对象、k+1…h 存在检测轨迹 j、SOT 脚本框在 h 覆盖 j → `BOUND`/`resolution_level 2`/`follow(j)`，关联器 `id()`、库 `frame_id`、ID 集合不变，SOT 工厂调用 1 次；(b) 失败：SOT 在 k+2 返回 `lost` → `NO_TRACK_AT_K`/`sot_lost@k+2`、指针不变；h 帧无过门 → `no_adoption`；两条过门裕度不足 → `AMBIGUOUS`；注入时钟超过 `T_replay` → `replay_timeout@<f>`；(c) 旧帧：k 早于历史窗 → `FRAME_NOT_IN_HISTORY`（SOT 工厂 0 次调用）；k 在历史窗但帧源已淘汰 k → `NO_TRACK_AT_K`/`not_attempted_frame_missing`。

### 3.5 指针与对外发布（K1/K3）

- 对外只发布指针指向的 track；`tracking_observation.json` schema v1 字段不变；对外 `track_id = <session>-t<n>`，n 随每次 `BOUND` 递增；被换下的 id 进 `retired_track_ids`（追加恰一次）。指针 track 在 buffer 内 unmatched → `raw LOST` + `reason bound_track_unmatched`（沿用），被移除 → `bound_track_removed` 并上报 `TRACK_ENDED`。
- 会话改为**单一常驻 `TrackLoop`**（会话启动即创建，`step` 逐帧），「段」改为「指定纪元」记账；播种不再 `init`、不再回放积压，静音播种机制退役；发布最终门五项、`K_pub 2`、`T_pub 0.4 s`、`T_stall 3 s` 数值不变。
- 每帧处理时延 p95 ≤ 帧周期是前提（FAST-002 报告 Mac MPS p95 31.9 ms，CPU 48.4 ms，均为离线单进程；本项在 AC-6 载体自测中重报，不作门）。

### 3.6 阶段 2 状态机：跟踪中指定（K3）

在 LOOP-001 八态之上新增一个会话状态 `ACQUIRING`，并把 `QUERYING`/`AWAITING_CONFIRMATION` 的「无活段」前提去掉：有指针时这两态**保持发布**（指针 track 继续观测与伺服）。未列组合一律回执 `REQUEST_INVALID`、状态不变。

| 状态 | 动作/事件 | 下一状态 | 动作 |
|---|---|---|---|
| `TRACKING` / `SUSPECTED` | `ask` / `respecify` | `QUERYING`（保留指针、继续发布） | `epoch+1`；`SUSPECTED` 计数保留 |
| `QUERYING`（有指针） | `R_des(ok)` / `R_des(fail)` | `AWAITING_CONFIRMATION` / 按 LOOP-001 规则 | 指针不变 |
| `AWAITING_CONFIRMATION` | `confirm k`（检查点通过）→ `designate(box_k, N)` | `BOUND` → `TRACKING`；`BOUND_COASTING` → `TRACKING`（raw LOST）；`TRACK_ENDED` → `ACQUIRING`；其余三值 → 回到确认前状态 | 六值写 `designation`；`BOUND*` 时旧指针 retire、计数清零 |
| `IDLE` / `LOST` / `REINIT_REQUIRED` | 同上 `confirm` | 同上（无旧指针可退） | 同上 |
| `ACQUIRING` | 收养成功（§3.7） | `TRACKING` | `follow(新 id)`，`designation.result` 改记 `BOUND` |
| `ACQUIRING` | `ACQUIRE_FAILED`（时限/未到位/无收养） | `LOST(acquire_failed)` | `hold_body`；云台不动；等待人 `ask`/`respecify` |
| `ACQUIRING` | `stop` / `seg_end` | `TERMINAL` / `REINIT_REQUIRED` | 沿用 |
| `TRACKING` | `raw_lost` 且 reason `bound_track_removed` | `SUSPECTED(tracker_failure)` | 沿用；**不自动重捕**（D.1） |

`STATE_REASONS` 增 `acquire_failed`、`slew_timeout`、`adopt_timeout`；`SESSION_STATES` 增 `ACQUIRING`。`confirm → designate` 的第二级回放同步有界（≤ `T_replay`），期间状态停留在 `AWAITING_CONFIRMATION`、不发布新帧，`L2_*` 事件逐步写会话 JSONL；回放结束按上表六值迁移（第二级失败即 `NO_TRACK_AT_K`，回到确认前状态、指针不变）。

### 3.7 无同帧观测的转向通道与安全语义（K2/K1）

- 触发：仅 `designate` 返回 `TRACK_ENDED` 且已由人确认（同一 `designation_id`）。
- 世界点：k 帧位姿 + 指定框底中点 ∩ 显式水平面（`box_ground_intersection`）；若 k 帧命中轨迹有 ≥ 2 帧历史，用其地面点差分速度 × 经过时间外推（红车），否则静止。
- 发布：新增通道 `slew_look_at(point, designation_id)`，**每个 `designation_id` 至多一次**，不要求同帧观测；收据写 `publish-receipts.jsonl`；期间 `body_command` 只允许 `hold_body`（速度指令仍须同帧观测）。
- 到位判据：相邻元数据位姿角速率 < ω_arr（申请 5°/s）连续 N_arr 帧（申请 2）且世界点投影落在画内；时限 `T_slew`（申请 3 s）。
- 收养：到位后窗口 M 帧（申请 5）内，检测 track 框中心与投影点距离 ≤ r_adopt（申请 40 px）连续 N 帧（申请 3）→ `BOUND`；多条同时满足 → 取距离最小且裕度 ≥ 15 px，否则 `AMBIGUOUS` 报人；窗口耗尽 → `ACQUIRE_FAILED(adopt_timeout)`。
- 失败：`hold_body`，云台停在当前指向，状态 `LOST(acquire_failed)`；不重试、不自动重播种。可达性边界：世界点超出 45° 限位时云台饱和、目标可能仍不在画内 → 以 `ACQUIRE_FAILED` 显式报告，不动机身（v1 候选池限定在可居中范围，§2.3）。

### 3.8 最小伺服（K2）

- 每个处理帧（不再只批末）对指针 track 发 `look_at`：点 = 当前框底中点 ∩ 水平面（沿用 `_publish_latest` 几何）。
- 步进限速：相邻两次指令的视线角变化 ≤ ω_max/hz（申请 ω_max = 30°/s → 6°/帧），超出时把指令点沿地面向目标点移动到角变化恰为上限处；残差 ≤ 上限时直接指向。
- 机身：阈值规划器与其输入路径不变。不做预测前馈；不做像素残差。

### 3.9 离线 E1/E2 线束（证据；不新增数据划分、标签或对外指标，故不触发 K4——提请 §7 (b)）

新包 `tools/eng_acq/`（只读数据根、写 `outputs/eng-acq/P1-ENG-ACQ-001/`，`.gitignore` 追加该目录），解释器 = 数据根 `.venv-yoloe`（有 `lap`，pip 0）。输入：事实 10 两份缓存、事实 11 sidecar/索引/时刻、事实 14 的 IoU 分布（只取统计量）。

- **常驻回放**：每序列用 `run_sequence` 对库关联器逐帧一次 `update(boxes, img)`（不是插件 `update`），`gmc_source ∈ {pose, optflow, none}`；每帧输出行、`lost_stracks` 预测框与 `removed` ID 交同一 `ResidentCore.record`（§3.1，与插件 `step` 同一实现）写历史。
- **E1 陈旧指定解析成功率随延迟（AR1-2）**：样本 = (k, o)：k 为序列帧、o 为 k 帧 OK 可见对象（静止车取索引 `vehicles[]`、红车取 `dynamic`）；指定框：**干净臂** = o 在 k 帧的真值框；**扰动臂**见下（§7 (i) 答复前不跑）。延迟 Δ ∈ {1, 2, 4.2, 5.4, 8, 13} s；解析帧 r = 同序列（m3-armA：同段）内首个 `t ≥ t_k + Δ` 的帧；解析 = 常驻回放到 h = r 时调 `designate(box, k)`（三级全走；第二级用数据根 JPEG 与 `nanotrack-v2`，事实 17）。每个 (k, o, Δ) 落入**且仅落入**下列 15 桶之一（`vis_r` = o 在 r 帧 OK 可见，真值；`IoU_r` = 指针 track 在 r 帧的框（coasting 取 KF 预测框）与 o 真值框的 IoU）：

| # | 桶 | 条件 |
|---|---|---|
| 1 | `NO_RESOLVE_FRAME` | r 不存在（序列/段在 t_k + Δ 前结束）；不调 `designate` |
| 2 | `BOUND_V_CORRECT` | `BOUND`，vis_r，IoU_r ≥ 0.3 |
| 3 | `BOUND_V_WRONG` | `BOUND`，vis_r，IoU_r < 0.3（误锁） |
| 4 | `BOUND_INVISIBLE` | `BOUND`，非 vis_r（误锁） |
| 5 | `COASTING_V_CORRECT` | `BOUND_COASTING`，vis_r，IoU_r ≥ 0.3 |
| 6 | `COASTING_V_WRONG` | `BOUND_COASTING`，vis_r，IoU_r < 0.3 |
| 7 | `COASTING_INVISIBLE` | `BOUND_COASTING`，非 vis_r（保守：不发布） |
| 8 | `ENDED_V` | `TRACK_ENDED`，vis_r（在线将走第三级） |
| 9 | `ENDED_INVISIBLE` | `TRACK_ENDED`，非 vis_r（正确报告） |
| 10 | `NOTRACK_V` | `NO_TRACK_AT_K`，vis_r |
| 11 | `NOTRACK_INVISIBLE` | `NO_TRACK_AT_K`，非 vis_r（正确报告） |
| 12 | `AMBIG_V` | `AMBIGUOUS`，vis_r |
| 13 | `AMBIG_INVISIBLE` | `AMBIGUOUS`，非 vis_r |
| 14 | `OUTHIST_V` | `FRAME_NOT_IN_HISTORY`，vis_r（Δ ≤ 13 s = 65 帧 < 128，预期 0，仍列） |
| 15 | `OUTHIST_INVISIBLE` | `FRAME_NOT_IN_HISTORY`，非 vis_r |

  分层 = 序列 × {静止, 红车} × S/M/L（k 帧真值框短边 <32 / 32–63 / ≥64 px）× `gmc_source` × 臂；每层每 Δ 一行，行内：`N_all` = 该层 (k, o) 数（与 Δ 无关）、`N_res = N_all − #1`、`N_vis` = #2+#3+#5+#6+#8+#10+#12+#14、`N_inv = N_res − N_vis`、15 桶计数、`level2 {attempted, adopted, ambiguous, failed_by_reason{§3.4.1 闭集}}`，以及描述性比例：`resolve_ok = (#2+#5)/N_vis`、`false_lock = (#3+#4+#6)/N_res`、`report_ok_invisible = (#7+#9+#11+#13+#15)/N_inv`、`explicit_unbound_visible = (#8+#10+#12+#14)/N_vis`、`level2_share = adopted/#2`。守恒（每层每 Δ，线束断言）：Σ#1…#15 = `N_all` 且 `N_vis + N_inv + #1 = N_all`；`N_all = 0` 的层仍输出一行（计数全 0、比例 `null`），分母为 0 的比例写 `null`。曲线 = `resolve_ok` 与 `false_lock` 随 Δ，逐层。真值只在样本构造（k 帧框、vis_r、IoU_r）出现。读数只作描述：不设资格门，不设对外新主指标。
- **扰动臂（§7 (i) 待用户）**：线束定义 `--perturb {none, c2_quantiles, uniform}`：`c2_quantiles` = 对真值框随机缩放 + 平移，使实现 IoU 分布的 p10/p25/p50 与 C2 347 行分位数之差 ≤ 0.05（固定种子）；`uniform` = IoU ∈ [0.3, 0.95] 均匀。答复前只跑 `none`（干净臂），两种扰动都不执行、线束不读取 C2 预测文件，`-e1.json` 写 `perturbed_arm: "PENDING_USER_(i)"`。
- **第二级代价上界**：第二级只在第一级 `NO_TRACK_AT_K` 时触发；每个 (k, o) 至多一次从 k 到 k + 13 s 的 SOT 回放（≤ 65 帧，各 Δ 共用前缀）；每（序列 × `gmc_source` × 臂）触发数 > 600 时按固定种子分层（对象类 × 尺寸）等比抽 600 并在报告标 `LEVEL2_SUBSAMPLED`；数据根 JPEG 只读。

  现行第二级上限见决策记录「信封修订 SUB:1/SUB:2 落实（2026-09-29；CLARIFY）」；本段原申请值保留作修订基线。
- **E2 转向存活率**：a7（每帧旋转 p90 21.7°、max 26.7°，§8）为压力序列，scout-1、m3-armA 为对照；3 gmc_source × `track_buffer ∈ {10, 20, 30}` 调用（= 2/4/6 s）；读数 = FAST-001 R4 口径 A 13 s 保持率（`window_summary` 七类结局与守恒式逐字复用，加 H-9 空窗断言）、每对象 ID 切换数、静止车 track 平均寿命；另出**位姿单应自检表**：a7 上旋转 ≥ 5° 的相邻帧，静止车真值框经 H 映射后与下一帧真值框的中心误差中位/p90，对照无补偿。
- **不做**：不用 609 行真实 C2 框在 H 序列上做对照（D.7）；不做 SOT 回放兜底；不在报告中给门值或「通过/不通过」。

### 3.10 Unity Play D1 剧本（另签；不在本提案信封内）

- 前提：`R1@K1K2K3` PASS；人眼保真检查（AC-17）完成；`runtime/scenario_config.json` 覆盖 `retained_frame_count`（申请 ≥ 1,500，≈ 5 min）以留住整段帧（配置，不改 Unity）。
- 剧本（≤ 3 min，1 次 Play）：`candidates` 后端启动 → 人从检测候选选红车并 `confirm` → 跟红车 ≥ 20 s → `ask` → 选静止车 B → `confirm` → 记时间到绑定 / 到居中 → 切 C → 切回红车（多半 `TRACK_ENDED` → 转向通道）。候选来自快层检测 track，**不得用真值投影**；操作者工具可选注入人工延迟（申请 {0, 4} s）以复现陈旧指定。
- 读数（描述，不设门）：time-to-bind、time-to-center（目标中心距画面中心 < r 连续 N 帧，申请 r = 64 px、N = 5）、按偏轴角（画内 / 出画但 45° 内 / 需机身）与斜距分桶的成功率、误锁次数与时长、显式报告比例（六值 + `ACQUIRE_FAILED` 占指定次数）。静止车 B/C 的成败由归档帧离线复算（`tools/dist_data/project_boxes.py`，真值只在离线评分）或人工目检；`metrics.json` 只对红车有效。
- 定位：本项 Unity 证据的唯一来源；其是否按正式用户验证入 `docs/unity-test-log.md`（而非 workflow §4.3.2 的诊断通道）由用户签发时定（§7 (h)）。

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | 常驻关联（AR1-3）：`resident` 模式插件在无指针状态下对连续 N 帧（传感器 `frame_id` 非连续起点）每帧恰调用一次检测与关联并写历史（`_detect` 调用数 = N，历史长度 = min(N, depth)），`pointer_result` 返回 `lost("no_pointer")`；`compat` 模式 `update` 早于 `init` 不检测且返回 `lost(tracker_not_initialized)`；`resident` 上调 `init`/`update`、`compat` 上调 `step`、`step` 同帧重复或回退均抛 `ProtocolMisuse` 且不检测。任一不成立即不满足 | test: `tests/test_det_assoc_tracker.py::test_resident_step_without_pointer`；`::test_mode_methods_are_exclusive`；`::test_step_repeated_or_rolled_back_frame_raises` | K1K2K3 | |
| AC-2 | 轨迹历史按传感器 `frame_id` 索引（AR1-3）、深度 ≥ 100（申请 128）、含位姿与 `tracked`/`lost` 全部行及 `removed_ids`；`history(k)` 对淘汰或未见的 k 返回 `None`；起点 `frame_id` = 1000 时 `history(1000)` 命中而 `history(1)` 为 `None`，条目 `library_frame_id` = 调用序号且不作键；键为库 `frame_id` 或深度 < 100 即不满足 | test: `tests/test_det_assoc_tracker.py::test_history_keyed_by_sensor_frame_id`；`::test_history_depth_eviction`；artifact: `manifest_identity().history_depth` | K1K2K3 | |
| AC-3 | 六值闭集每一值都有可构造的合成用例（含第一级 τ/m/备用判据边界、coasting 超时转 `TRACK_ENDED`、第二级 `BOUND`/`AMBIGUOUS`/`NO_TRACK_AT_K`）；`resolution_level` 与 `level2.reason` 只作字段；出现第七个值、任一值不可达或 `level2.reason` 超出 §3.4.1 闭集即不满足 | test: `tests/test_det_assoc_tracker.py::test_designate_*`（六值各 ≥ 1 例）；test: `tests/test_resident_core.py::test_designate_result_closed_set` | K1K2K3 | |
| AC-4 | 指针切换不重建关联器：连续两次 `designate→follow`（其中至少一次经第二级）后关联器对象 `id()` 不变、库 `frame_id` 单调、未涉及的 track ID 集合保持；切换路径任何调用 `DetAssocTracker.init`/新建 `_tracker` 即不满足（第二级 SOT 实例自身的 `init` 不计，测试断言其为独立对象且回放后被丢弃） | test: `tests/test_det_assoc_tracker.py::test_pointer_switch_keeps_associator`；`::test_level2_replay_keeps_associator` | K1K2K3 | |
| AC-5 | 位姿单应：合成纯旋转下，t−1 帧像素经 H 映射与 t 帧投影之差 ≤ 0.5 px；三种 `gmc_source` 可选且 `manifest_identity` 如实报告；a7 旋转 ≥ 5° 帧上的位姿自检表（映射中心误差中位/p90 对照无补偿）已产出。合成测试失败、来源不可选或自检表缺失即不满足；自检表显示补偿不优于无补偿时按 §6(i) 处置，不算本条不满足 | test: `tests/test_pose_gmc.py`；artifact: `docs/evidence/P1-ENG-ACQ-001-e2.json`「pose_warp_selfcheck」 | K1K2K3 | |
| AC-6 | 载体（AR1-3）：常驻 `TrackLoop` 用 `resident` 插件（注入缓存检测的 `model_loader` 替身，零推理）在 scout-1 子序列上逐帧 `(state, box, reason)` 与线束回放（同一 `ResidentCore`）完全一致；载体对每个 bundle 恰调用一次 `step(image, frame_id, metadata)` 与一次 `pointer_result(frame_id)`、从不调用 `init`/`update`（间谍计数）；`tracking_observation.json` 仍是 schema v1 且只含指针 track；旧插件路径（`csrt`/`nanotrack-v2`/`compat`）测试全通过且 `initialize→init`、`process_available→update` 调用序列不变；不再存在 init-at-N 回放路径。任一不成立即不满足 | test: `tests/test_det_assoc_carrier.py::test_resident_carrier_matches_replay`；`::test_resident_carrier_calls_step_once_per_frame_never_update`；`::test_legacy_carrier_call_sequence_unchanged`；cmd: `python3 -m unittest tests.test_trackers tests.test_track_loop tests.test_det_assoc_tracker tests.test_det_assoc_carrier` | K1K2K3 | |
| AC-7 | E1 干净臂产出（AR1-2）：§3.9 十五桶 × 分层 × 六个 Δ 的计数、`N_all`/`N_res`/`N_vis`/`N_inv`、五个描述性比例与 `level2` 子表；每层每 Δ 守恒 Σ桶 = `N_all` 且 `N_vis + N_inv + NO_RESOLVE_FRAME = N_all`（线束断言 + 合成守恒测试）；空层按 `N_all = 0`/`null` 输出；固定种子两次运行字节一致；`perturbed_arm` 字段答复 (i) 前为 `PENDING_USER_(i)`。缺桶、缺分母、守恒不成立、不可复现，或报告出现门值/「通过」字样即不满足 | artifact: `docs/evidence/P1-ENG-ACQ-001-e1.json`；`docs/evidence/P1-ENG-ACQ-001-report.md`「E1」；test: `tests/test_eng_acq_e1.py::test_buckets_exhaustive_and_conserved`；cmd: `tools/eng_acq/run.py e1 --perturb none` | K1K2K3 | |
| AC-8 | E2 产出：3 序列 × 3 gmc_source × 3 buffer 的 13 s 保持率（口径 A 逐字）、ID 切换数、静止车 track 寿命与位姿自检表；空窗断言存在且三序列不触发；缺格或用了 H 序列即不满足 | artifact: `docs/evidence/P1-ENG-ACQ-001-e2.json`；`-report.md`「E2」；test: `tests/test_eng_acq_windows.py::test_empty_window_rejected` | K1K2K3 | |
| AC-9 | 零消耗与隔离：数据根与 `runtime/` 零写入（受保护写入断言）；检测推理 0（缓存 + 替身）；pip 0；真值只出现在指定框构造与评分函数（静态检查：`controller/` 不导入索引/真值模块）；每帧 JPEG sha 与 sidecar 一致否则停。账本文件任一维度非零或断言失败即不满足 | artifact: `docs/evidence/P1-ENG-ACQ-001-ledger.json`；test: `tests/test_eng_acq_guards.py` | K1K2K3 | |
| AC-10 | 承接 H-1/H-2：候选证据逐字声明是否触及 `LanguageWorker`/延迟排队域与可变归档；触及则附对应回归并通过；声明缺失或触及而无回归即不满足 | artifact: `docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「承接声明」 | K1K2K3 | |
| AC-11 | 复用资产核实：权重、`freeze.json`、`frozen-B/V`、`index.jsonl.gz` 的本机 sha256 与来源记录一致并写入证据；报告含 AC-4 口径偏差声明；报告任何处引用 FAST-002 G-5/G-6/H 读数作为本项证据即不满足 | artifact: `docs/evidence/P1-ENG-ACQ-001-assets.json`；`-report.md`「资产与偏差声明」 | K1K2K3 | |
| AC-12 | 插件代码复核承接：交接行与自证小节把 `controller/det_assoc_tracker.py` 全文、`trackers.py` 工厂、`track_loop.py` CLI 闭集列入 `R1@K1K2K3` 复核范围；范围缺项即不满足 | artifact: `docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「复核范围」 | K1K2K3 | |
| AC-13 | 状态机：§3.6 每条新增/修改迁移各有用例，`ACQUIRING` 入闭集，未列组合回执 `REQUEST_INVALID` 且状态不变；有指针时 `QUERYING`/`AWAITING_CONFIRMATION` 期间发布不中断；任一迁移缺用例或未列组合改变状态即不满足 | test: `tests/test_language_loop.py::test_designate_while_tracking_*`；test: `tests/test_language_bridge.py`（闭集） | K1K2K3 | |
| AC-14 | 转向通道安全语义：同一 `designation_id` 第二次 `slew_look_at` 被拒；`T_slew`/收养窗口超时 → `LOST(acquire_failed)` + `hold_body` 收据；期间速度指令被拒（`orphan_control` 语义保留）；到位判据与 N-of-M 收养各有红绿用例；任一缺失即不满足 | test: `tests/test_language_loop.py::test_acquiring_*`；test: `tests/test_gated_publisher_slew.py` | K1K2K3 | |
| AC-15 | 最小伺服：指针 track 每处理帧发一次 `look_at`；相邻指令视线角变化 ≤ ω_max/hz（合成大偏差用例）；机身规划器输入不变；每帧不发或超限即不满足 | test: `tests/test_track_loop.py::test_servo_rate_clamp` | K1K2K3 | |
| AC-16 | 清理承接 H-5：清理清单（路径、来源、大小、保留理由、建议动作）写证据；§7 (g) 答复前缺省零删除（本地与 5060 均只读盘点）并在清单标 `AWAITING_USER`；清单缺项或未裁定即删即不满足 | artifact: `docs/evidence/P1-ENG-ACQ-001-cleanup.json` | K1K2K3 | |
| AC-17 | 人眼保真承接 H-4：候选声明触及预览/采集/保存路径与否；触及则 Play D1 前完成 ≥ 2 张样帧人眼核对并记入证据；§7 (h) 答复前 Play D1 不执行、本条记 `NOT_RUN`；声明缺失、触及而未核或把 `NOT_RUN` 记成满足即不满足 | artifact: `docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「人眼保真」；`docs/unity-test-log.md` 本项条目 | Play D1 | |
| AC-18 | Unity：`K1K2K3` 候选记 `NOT_RUN`；§7 (h) 答复前 Play D1 零执行、本条 `NOT_RUN`，即使 `K1K2K3` 通过 Overall 也停在 `IMPLEMENTED_REVIEWED_AWAITING_UNITY`、不得记 `DONE`；答复后按 §3.10 剧本执行并记录四类描述数字与六值/`ACQUIRE_FAILED` 分布；剧本步骤缺失、候选来自真值投影、或把描述数字写成通过即不满足 | artifact: `docs/unity-test-log.md` `UT-P1-ENG-ACQ-001-D1`；`docs/evidence/P1-ENG-ACQ-001-play-d1.md` | Play D1 | |
| AC-19 | 第二级起跟回放（AR1-1）：§3.4.1 (a) 成功、(b) 四种失败（`sot_lost@<f>`、`no_adoption`、`AMBIGUOUS`、`replay_timeout@<f>`）、(c) 两种旧帧各有具名用例；SOT 工厂调用数在不触发时为 0、触发时为 1；SOT 框不出现在观测、历史或桥文件；`level2` 记 `replayed_frames` 与 `elapsed_ms`。任一用例缺失或 SOT 框泄漏即不满足 | test: `tests/test_resident_core.py::test_level2_success_adopted`；`::test_level2_failure_*`；`::test_level2_old_frame_*` | K1K2K3 | |
| AC-20 | E1 扰动臂（AR1-4；§7 (i) 待用户）：答复前 `NOT_RUN`，不得记满足；用户选定采样并经接受角色更新本条后才可跑：`c2_quantiles` 须使实现 IoU 的 p10/p25/p50 与 C2 347 行分位数之差 ≤ 0.05，`uniform` 须使 IoU ∈ [0.3, 0.95]；桶、分母、守恒、复现与 AC-7 同 | artifact: `docs/evidence/P1-ENG-ACQ-001-e1.json`「perturbed_arm」；cmd: `tools/eng_acq/run.py e1 --perturb <用户选项>` | K1K2K3（待 (i)） | |

## 5. 预算信封（申请值；**用户逐字签发前各维度均为 0**，账本没有即视为未发生；签发后成功、失败、重试全部计入同一上限，耗尽即停）

| 项目 | 阶段 1 + 阶段 2（一个候选，`K1K2K3`） | Play D1（另签，本表只登记申请形状） |
|---|---|---|
| Consuming | no | yes |
| scenario/session/run ID | 0 | 1 次 Play 产生的 session ID |
| Unity Play | 0 | 1 次，≤ 3 min，`retained_frame_count` 配置覆盖 |
| 模型 API 次数 / VLM 查询 | 0（`candidates` 后端不经 VLM） | 0 |
| 训练 GPU·h | 0 | 0 |
| 检测推理次数 | 0（冻结缓存 + `model_loader` 替身） | Play 期间在线检测（本机 MPS/CPU，不计次） |
| 模型启动（YOLO 权重加载） | 0 | 1 |
| 下载 / pip 安装 | 0 / 0（数据根解释器只读调用） | 0 / 0 |
| 5060 或其他远端访问 | 0（H-5 远端清理待用户裁定后另计） | 0 |
| 本地磁盘写入 | 仅 `outputs/eng-acq/`、`docs/evidence/`、代码与测试 | 归档帧 ≈ 1,500 × ~60 KB ≈ 90 MB |
| CPU 回放 | E1/E2 ≈ 27 次序列回放（4,832 帧）+ E1 解析，本机 CPU | — |
| NanoTrack CPU 回放（第二级） | E1 每（序列 × gmc_source × 臂）≤ 600 个 (k, o) × ≤ 65 帧，本机 CPU；模型文件本地已有（事实 17），零下载 | Play 期间在线，不计次 |

**§7 (g)–(i) 答复前的缺省（AR1-4）**：零删除、零 Play、零 C2 统计量取样；本表 Play D1 列只是申请形状，不随 `K1K2K3` 信封签发；干净臂 E1 与 E2 不依赖 (i)，可在 `K1K2K3` 信封内先跑；扰动臂（AC-20）与 Play D1（AC-17/18）在用户答复并经接受角色更新合同前不执行、不计通过。

## 6. 限制、不承诺与失败模式

- **不承诺**：任何在线成绩、`C_track` 变化、保持率、Jetson/TensorRT 性能；E1/E2 是离线单进程、无 Unity 同机负载、无发布门的描述性读数；scout-1、m3-armA 在检测器训练原子内（检测偏乐观，但 E1/E2 量的是关联与解析），报告逐格标注 `TRAINED_ON_ATOM` / `SELECTION_DOMAIN`。
- **数据代表性**：a7 是脚本扫视采集（每视角停留短），静止车在 Δ ≥ 4.2 s 后仍可见的比例本身只有 38%（§8），E1 在 a7 上主要量「正确报告不可见」；m3-armA 几乎无自运动（旋转 p90 ≤ 0.7°），E2 上只作对照。
- **失败模式与预注册处置**：(i) 位姿单应在 a7 上不优于无补偿（AC-5 第二条）→ 如实报告，`gmc_source` 缺省改回 `optflow` 并在决策记录记归因，不改冻结规格；(ii) E1 在 Δ ≥ 8 s 的红车样本 `TRACK_ENDED` 占多数 → 记录，不改门（没有门），阶段 2 转向通道即为此设计；(iii) 每帧处理 p95 > 200 ms（Mac CPU）→ 报告并交接受角色裁定是否降 `history` 写入频率，不改 5 Hz；(iv) `designate` 出现闭集外情形 → 候选不成立，返工。
- **不可推出**：E1 成功率不能推出在线捕获成功率；E2 保持率不能推出转向中的在线存活；两者只支持「机制在离线回放中的行为」陈述。
- 检测器是本场景专用局部备选（设计 v0.3.54），换目标外观需重训——本项不做，主线 §3 也不要求。

## 7. 必经停点与提请裁定

- **`K1K2K3` 合并单候选**（engineering §4「相互关联的触发可合并」）：K1 = 历史时间语义、`step` 帧序、发布门与新字段、静音播种退役；K2 = `slew_look_at` 通道、限速、超时、`hold` 回退；K3 = 指针、六值闭集、状态机、插件身份（含 FAST-002 插件代码复核承接）。一次 `C1@K1K2K3` → 新鲜上下文 `R1@K1K2K3`。不触发 K5。
- **不申请 `UNITY_NA`**：阶段 2 改变运行时行为；Unity 证据 = Play D1（另签）。`K1K2K3` 通过后 Overall 最高记 `IMPLEMENTED_REVIEWED_AWAITING_UNITY`。
- **提请接受角色在 `ACCEPTED` 时裁定**：(a) `Workflow: engineering-v1` 申请；(b) E1/E2 作为 K3 证据附件而非 K4（不新增划分/标签/对外指标；本角色读法：是）；(c) 插件落点——在 `det_assoc_tracker.py` 内扩展 `DetAssocTracker` 并保留插件名 `det-assoc-v1`（规格与冻结 sha 不变，`manifest_identity` 增 `mode`）vs 新名 `det-assoc-v2`（本角色推荐前者）；(d) §3.4/§3.7/§3.8 申请参数（τ、m、`T_slew`、N/M、r_adopt、ω_max、ω_arr）是否作为插件/会话配置项而非冻结值；(e) 阶段 1 → 阶段 2 无门直通；(f) §3.6 的编码方式（`ACQUIRING` 新态 + 有指针时 `QUERYING` 保持发布）；(j)（D2 新增）第二级 SOT 用冻结 `nanotrack-v2`（事实 17）而非新模型，`T_replay`/`L_replay` 按 (d) 作配置项，第二级失败一律映射 `NO_TRACK_AT_K` + `level2.reason`（不加第七值）。D1 裁定 (b)–(f) 已作为本稿修订依据写入：(b) → §3.9 只作 K3 附件、不新建划分/标签/对外指标；(c) → §3.1 沿用 `det-assoc-v1` + `mode`；(d) → §3.4/§3.4.1/§3.7/§3.8 参数为配置项并记录生效值；(e) → §2.2；(f) → §3.6/AC-13/AC-14。
- **待用户**（AR1-4；**答复前的缺省：零删除、零 Play、零 C2 统计量取样**；推荐项只供用户选择、不按推荐先执行；用户选定后由接受角色更新对应 AC 文本再执行；三项均不在 supervisor D5 代选闭集内）：(g) H-5 清理：本地 `runtime/hold-diag-loopb-*` 与 5060 `repo-b` 的删除（推荐：清单入证据后本地删除、5060 由用户自行删除或授权一次 SSH；答复前 AC-16 只读盘点并标 `AWAITING_USER`）；(h) Play D1 的定位（推荐：作为本项正式用户 Unity 验证，1 次 Play 另签，入 `UT-P1-ENG-ACQ-001-D1`；若只签为诊断通道则本项停在 `IMPLEMENTED_REVIEWED_AWAITING_UNITY`；答复前 AC-17/AC-18 `NOT_RUN`、零 Play）；(i) E1 扰动模型（推荐：`c2_quantiles`，只取 347 行的分位数、不回放 H 帧；备选 `uniform` IoU ∈ [0.3, 0.95]；答复前只跑干净臂、AC-20 `NOT_RUN`、线束不读取 C2 预测文件）。
- **推进方式**：本项轮次由 supervisor 无人值守派发（决策信封 D1/D4/D5/D6，至 2026-10-10）；§5 执行信封首签、Play、H-5 删除归用户。

## 8. 只读试读与试运行数字（2026-09-28 本机只读；零训练、零模型推理、零写入；脚本留会话暂存目录，不入库）

- **缓存与资产**：`frozen-B` 1,664 帧（scout-1 768；m3-armA 7 段 × 128 = 5 段 `p1-m3-body-001-arm-a-trial-{1-attempt-4,2-attempt-2,3,4,5}-post-run` + 2 段 `frames.arm-a-trial-{1-void-attempt-3,2-void-attempt-1}-hold`），`frozen-V` 3,168 帧（a7）；头部 `weights_sha256` 与权重实测 sha 一致；每帧检测数均值 scout-1 6.17（max 13）、m3-armA 9.25（max 11）、a7 3.73（max 13）。索引命中 4,832/4,832 帧，sidecar 缺失 0。
- **时序与自运动**（相邻帧四元数夹角）：scout-1 span 121.0 s、dt p50 0.199 s、max 0.206 s，旋转/帧 p50 0.33°、p90 1.00°、max 24.11°；m3-armA 各段 25.4 s、dt p50 0.200 s、max ≤ 0.259 s，旋转 p90 ≤ 0.69°、max 2.43°；a7 span 633.4 s、dt p50 0.200 s、max 0.325 s，旋转/帧 p50 0.01°、**p90 21.70°、max 26.74°**（扫视跳变，E2 压力源）。三序列最大帧间隔 0.325 s ≪ 8 s（H-9 不可达）。
- **可见对象**：OK 静止车/帧均值 scout-1 2.00（max 5，14 个不同 id）、m3-armA 0.03–3.00（各段 1–3 个 id）、a7 1.52（max 7，28 个 id）；红车可见帧 scout-1 705/768、m3-armA 682/896、a7 1,653/3,168。
- **E1 样本量**（(k, 对象) 对；「Δ 后首帧仍 OK」比例，只描述数据、不是解析结果）：

| 序列 | 静止对 / 红车 k | Δ=1 | 2 | 4.2 | 5.4 | 8 | 13 |
|---|---|---|---|---|---|---|---|
| scout-1 | 1,535 / 705 | 静 1412/1520 (92.9%)；红 660/701 | 1304/1503 (86.8%)；645/694 | 1123/1469 (76.4%)；632/680 | 1034/1450 (71.3%)；624/672 | 866/1416 (61.2%)；602/655 | 612/1355 (45.2%)；569/624 |
| m3-armA | 1,923 / 682 | 1835/1840 (99.7%)；650/650 | 1761/1764；619/619 | 1598/1602；553/553 | 1505/1509；516/516 | 1311/1315；439/439 | 933/937 (99.6%)；289/289 |
| a7 | 4,805 / 1,653 | 3576/4795 (74.6%)；1494/1648 | 2732/4785 (57.1%)；1353/1643 | 1827/4763 (38.4%)；1074/1632 | 1516/4751 (31.9%)；951/1626 | 1223/4725 (25.9%)；858/1613 | 1571/4675 (33.6%)；1013/1588 |

- **C2 IoU 分布**（事实 14；扰动模型参数）：347 行，中位 0.862、p25 0.743、p10 0.358、≥ 0.5 占 0.870、≥ 0.3 占 0.905。
- **内存投影**：历史 128 帧 × ≤ 20 行 × 8 浮点 < 1 MB；E2 最重的 `optflow` 变体需逐帧读 JPEG（a7 3,168 帧 × 9 组合），CPU 可承受，无需 GPU。
- **D2 只读探针**：三个解释器 `cv2 5.0.0` 且 `TrackerNano` 可用（事实 17）；第二级在 E1 的上界 = 3 序列 × 3 gmc_source × 1 臂 × ≤ 600 (k, o) × ≤ 65 帧 ≈ 3.5 × 10⁵ 次 NanoTrack `update`，按 CPU 单帧 3–5 ms [估计] 约 20–30 min，无需 GPU；实际触发数由第一级 `NO_TRACK_AT_K` 频率决定，报告如实写。
- **未试读**：`LanguageWorker`、5060 副本与 `runtime/hold-diag-loopb-*` 的实际内容（H-5 清单在实现期只读盘点）；NanoTrack 单帧耗时未实测（上一行为估计）。

## Contract conformance（核对表）

**C3@K1K3（2026-09-29）：C2-1/C2-2 已补实现者证据，交 R2@K1K3 核实；本停点核对退回额度已用尽。** 本表只覆盖「Play D1 本地操作页窄范围代码批次 CLARIFY」的 AC-22/23/24 与 AC-18 修订 4；旧 K1K2K3 与 B1–B3 的已消费结论不因本轮改判。核读 C2 退回提交至操作页返工实现提交的完整候选 diff（页面、测试、操作单 §4 与证据/状态更新；提交按主题运行时解析）、`docs/evidence/P1-ENG-ACQ-001-K1K3-operator-handoff.md`「K1K3 操作页返工」、同名红绿块与全套日志，以及理解页面调用所需的 `controller/language_loop.py`、`controller/language_bridge.py`、`tools/eng_acq/candidates_preflight.py`。仅核对代码和已有证据，未运行测试；本表不签独立复核 verdict。

| AC | 结论 | 理由与直接指针 |
|---|---|---|
| AC-22 | 满足 | C2-1：`App._retry` 在 `_run` 前调用 `retry_block`，核同号、原/现 `VIEW_KEYS`、当前 `legal` 与 argv token；confirm 还重核候选 index、时效/帧差门和原预览 SHA。`App.state` 给每条未知结果 `retry_allowed/retry_block`，页面 `paintButtons/retryOk` 按现态与画面停用重试。`tests/test_eng_acq_operator_web.py` 的 `RetryStateTransitionTests` 六条状态/令牌/时效/图变更拒绝例和一条同视图正例、`PageScriptButtonTests::test_retry_button_follows_current_state_table` 对准缺口；修前 12 条新增例红、修后 68/68 绿见同名红绿日志返工块。原九态/CLI 边界证据见同名交接「逐 AC 证据」。 |
| AC-23 | 满足 | `ReceiptCheck.evaluate` 调会话自己的收据/报告解析与配置绑定；`Monitor._candidate/public` 取会话写盘时刻与收据值，`App._click` 重读结果、index、预览 SHA 与 `result_id`。交接「逐 AC 证据」「测试与红绿」的 `ReceiptBindingTests`、`ReceiptValuesTests`、`ConfirmGateTests` 和 M2–M4/M8 变异红对准这些门。浏览器解码回报只能由页面脚本观测，真实 Unity 主机尚未跑；不把这项离线核对写成 AC-18 通过。 |
| AC-24 | 满足 | C2-2：`App.mark_play_start` 先 `monitor.poll`，读失败或 `sid_block` 时记拒绝且不写标记；`App.state` 给计时标记 `mark_block`，页面 `paintButtons` 同时核 `dead/mark_block`。`SidDuringRunTests` 新三例核第二次启动、同号归档及读失败的服务端拒绝，`PageScriptButtonTests::test_mark_button_disabled_on_same_number_block` 核界面停用。操作单 §4 已写计时与 CLI 回退；其余 SID/日志/180 s 证据见交接「逐 AC 证据」。 |
| AC-18 修订 4 | 证据缺失 | 操作单 §4 T1/T4 写明新通过候选、§2.7/§3 重新预检与放行；`acq-d1-1` 被页面硬拒，旧页未改。正式 attempt 2 尚未发生，AC-18 维持 `NOT_RUN`；本轮不给 Unity verdict，也不放行 Play。 |
| 范围与测试归因 | 满足 | C2 退回提交至操作页返工实现提交的 diff 仅改新操作页、具名测试、操作单 §4、证据、状态及 supervisor 派发日志；旧 LOOP-001 页、`controller/`、`tools/`、`Assets/`、`config/`、`ProjectSettings/` 均未动。focused 68 例绿；本轮全套 1980 例、4 failures/9 errors/19 skipped。直接比对上一轮同机同解释器全套日志（1968 例）的 13 个 FAIL/ERROR 名称，集合相同、新增 0；新增 12 例全绿。13 项环境归因仍按交接「测试与红绿」；这里的「新增失败 0」只指相对该同环境日志的名单，不等于全套通过。 |

### 实现读法 IR-1…7 裁定（C2@K1K3；不增改 AC）

| 读法 | 裁定 | 依据与适用边界 |
|---|---|---|
| IR-1 | 接受 | `sid_usage` 把仅有一次启动、无 TERMINAL、同号活锁的目录读作 T1 当前活动会话；其他已用目录与归档拒绝，符合 CLARIFY。运行中另受 C2-2 约束。 |
| IR-2 | 接受 | `Monitor._read_logs` 仅凭 ask/respecify 的 `APPLIED`/`PENDING_QUEUED` 判有指令，对应会话 `_begin_designate` 先设置指令再记回执。 |
| IR-3 | 接受 | CLARIFY 对收据不符逐字要求「禁确认并报告原因」；保持 stop 等其他合法动作，不自行扩大为整页禁用。 |
| IR-4 | 接受 | 同号复用禁 CLI 动作，含 stop；§4 T3 CLI 回退仍可用。计时标记按钮已按 C2-2 补覆盖，待 R2 核实。 |
| IR-5 | 接受 | 首次用户标记持久化，无法可靠读取则提示手工计时；150 s 提醒是非自动提示，180 s 不自动 stop。 |
| IR-6 | 接受 | 结果身份、`k_ret`、index 连续及 `acq-d1-<n>` 号制均是现有身份/index 条款的收紧；不改变桥协议。 |
| IR-7 | 接受 | LOOP-001 专属查询序号/仿真时长提示不属本项 Play D1 信封；去掉提示不删除查询序号展示。 |

### 预复核关注项与未验证边界（C3@K1K3）

- 会话进程异常退出而无 TERMINAL 时页面不自动禁动作，见 `Monitor._block_reason` 与交接「未验证项与已知限制」。CLARIFY/AC-22…24 只点名启动时死锁拒绝及运行中第二次启动、同号归档、结束后活动；未写异常退出后的自动停用义务。本轮不把它归为 AC 字面缺口，也不因核对读码新增 AC；按 COORD-009 将此作为待 R2 核实的 `SCOPE_GAP` 候选，不预定 finding 分级或依据。页面故障时 §4 T3 CLI 回退仍有效。
- `App.retry_block` 的服务端重核与页面 `paintButtons` 已有 node 快照测试，真实 Unity 主机浏览器的点击/解码及真实会话尚未验证，见交接「未验证项与已知限制」；请 R2 核对这一证据边界，不把离线绿例当作 AC-18 Unity verdict。
- 本轮只把 C2-1/C2-2 从核对表关闭并交独立 R2 核实；R2 写通过候选之前，不启动 attempt 2 的 §2.7/§3 预检、放行或 Play。

open_items: K1K3_OPERATOR_REVIEW, ATTEMPT_2_PREFLIGHT, AC-18_UNITY_VERDICT

## 决策记录

- 2026-09-28 · D1 · `PROPOSED`（构思角色，supervisor 派发 `P1-ENG-ACQ-001-D1-20260928T202308Z-224e`）· 依据账本 09-28 A–D（C 方案认可、D.1/D.2/D.6/D.7/D.8）与两份收口裁定；零消耗、零代码；`Workflow: engineering-v1` 为申请，待接受角色裁定；§5 各维度 0。
- 2026-09-28 · D1 · `REVISION_REQUESTED`（接受角色，设计退修 1）· AR1-1…4 与 (a)–(i) 见下节「D1 接受裁定」。
- 2026-09-28 · D2 · `PROPOSED`（构思角色，supervisor 派发 `P1-ENG-ACQ-001-D2-20260928T210833Z-4f78`；回应 AR1-1…4，设计退修计数 1）· AR1-1 → §2.1 S1-h、§2.4、§3.4（三级顺序、`level2` 字段）、§3.4.1、§3.6、AC-3/AC-4/AC-19、§5/§8（第二级代价）、事实 17–19；AR1-2 → §3.9 E1（15 桶、分母、空层、守恒、扰动臂缺省）、AC-7、AC-20；AR1-3 → §3.1（`compat`/`resident` 互斥、载体 `step` 路径、历史键）、§3.2、AC-1/AC-2/AC-6、事实 20；AR1-4 → §3.9、§5、§7、AC-16/AC-17/AC-18/AC-20；D1 裁定 (b)–(f) 作为修订依据写入 §7 与对应节，(j) 新提请。主线判据（§1 逐字引用）、接口 A、Unity 零改动、不重训/不 ReID/不 H 域、不设资格门均不变；零消耗、零代码；`engineering-v1` 仍为申请，§5 各维度 0，(g)–(i) 仍待用户。
- 2026-09-28 · D2 · `REVISION_REQUESTED`（接受角色，设计退修 2）· AR1-3/4 已闭；AR1-1/2 各有剩余合同冲突，记 AR2-1/2；残留 2 ≤ D1 的 4，按已签 D1 决策信封交 supervisor 仅代选 §4.2(a)。工程轨道申请未生效，零执行额度。
- 2026-09-28 · D2 · `ACCEPTED`（接受角色执行 supervisor 已入账的 §4.2(a) 代拍）· 首次接受 §4 AC-1…20；AC-3/7/19 接受释义及 AR2-2 限制见下节。`Workflow: engineering-v1` 生效，`K1K2K3` 合并停点；§5 未签，零执行额度；AC-16/17/18/20 的待用户缺省不变。确认人：接受角色。

### D1 接受裁定（2026-09-28）

Decision: `REVISION_REQUESTED`（设计退修 1）。提案 §1 逐字引用主线，接口 A、指针常驻、AC-4 禁止经 `init` 切换、三序列离线取样、K1K2K3 合并停点及 LOOP-001/FAST-002 承接方向均与账本一致；下列合同缺口使当前版本尚不能按字面实现与逐项核验。不是 `REJECTED`，也未签发任何执行额度。

| ID | 必须修订的合同问题 | D2 可核对的完成条件 |
|---|---|---|
| AR1-1 | 账本 09-28 C 已认可三级解析，其中第二级为「k 帧起跟回放」；§2.4 却把 `NO_TRACK_AT_K` 的起跟回放兜底排除并推给后续立项。该分支在一次人确认后只报告、等待再问，也不满足 D.1 的「解析、转向、重捕由系统自动完成」。 | 在 §2/§3/AC 表恢复并定义第二级：触发条件、从 k 到当前帧的有界回放与身份/歧义判定、六值闭集映射、失败上报、与常驻主关联器及 AC-4 不经 `init` 重建的关系；给出可构造的成功、失败和旧帧测试。若要删除该级，先取得用户对 C 与 D.1 的新裁定，接受角色不能代删。 |
| AR1-2 | §3.9/AC-7 同时说「六值 + 正确/误锁拆分」和「七类」，末级分类数与可见性单列规则不自洽；成功率分母也未写明，无法证伪 AC-7 的守恒。 | 逐字列出互斥且穷尽的结果桶与可见/不可见处理，写明每个延迟/分层的分母、序列末端无解析帧及空样本表示；同步 §3.9、AC-7、报告规格与守恒测试。读数仍只作描述，不设资格门或对外新主指标。 |
| AR1-3 | §3.1 声称 `update(image)` 等价于 `step(image, frame_id, metadata)`，但前者没有传感器帧号/位姿；载体若同时调用二者会双计一帧，破坏 AC-1/AC-2 的逐帧与历史合同。 | 明定旧插件与常驻插件各自的调用路径、`update` 的兼容语义和同帧最多一次检测/关联的判据；在 AC-1/AC-2/AC-6 加具名测试，证明历史键只取传感器 `frame_id`，切换仍满足 AC-4。 |
| AR1-4 | §7「待用户」写成「按推荐执行并标待用户确认」，而 §3.9/AC-7 已无条件要求使用 C2 347 行统计量。用户尚未答复 (g)–(i)，尤其 (i) 会改变扰动采样，(h) 会改变 Unity 证据定位。 | 在 §3.9、AC-7/AC-18、§5/§7 写明答复前的缺省：零删除、零 Play、零 C2 统计量取样；允许先定义接口与跑不依赖 (i) 的干净臂，扰动臂及其 AC 验收等待用户，不能把未跑读数记为通过。用户若选择另一采样或 Play 定位，先经接受角色更新合同；不得由 supervisor D5 代选。 |

§7 (a)–(f) 本轮审查结论：(a) `Workflow: engineering-v1` 申请形态正确，且用户 D.8 已指定新工程项；**只有 `ACCEPTED` 时才能逐字裁定生效，本轮未生效，按缺省研究轨道 fail-closed，不得派实现**。(b) E1/E2 只作本项机制描述证据、不新建数据划分/标签或对外指标时可附 K3，不触发 K4；D2 须完成 AR1-2。(c) 同意扩展 `DetAssocTracker` 并沿用 `det-assoc-v1` 名称，`manifest_identity.mode=resident` 明示新语义，旧路径回归和 AC-4 均不可放宽。(d) 同意 τ、m、`T_slew`、N/M、`r_adopt`、`ω_max`、`ω_arr` 等作为插件/会话配置，当前申请值为默认值而非改动冻结规格；须记录生效值。(e) 阶段 1 证据写齐后可直接进阶段 2，两阶段共用一个 K1K2K3 候选，不设资格门；仍受执行信封首签约束。(f) 同意 `ACQUIRING` 新态与有指针 `QUERYING` 期间持续发布，失败和未列组合须保持 §3.6/AC-13/14 的可证伪边界。上述 (b)–(f) 是 D2 修订依据，待 `ACCEPTED` 时并入正式合同，不构成本轮实现授权。

§7 (g)–(i) 仍待用户，接受角色未代选：(g) 推荐清单入证据后本地删除、远端由用户自行删除或另授一次 SSH；答复前仅可只读盘点。(h) 推荐另签一次正式用户 Unity 验证；答复前 `NOT_RUN`，即使 K1K2K3 通过也不得记 `DONE`。(i) 推荐只取 C2 347 行 IoU 分位数、不回放 H 帧；答复前不得据此构造扰动臂。三项均触及删除授权、信封/Unity 证据定位或数据采样，超出 supervisor D5 代选闭集。

§5 阶段 1+2 申请值及 Play D1 申请形状目前均为 0 授权；仅待 D2 可接受后才向用户申请逐字签发。D1 不新增 BC/AC 冻结表、不同步正式设计，原 AC-1…18 仍为待修提案文本。

open_items: AR1-1,AR1-2,AR1-3,AR1-4

### D2 接受裁定（2026-09-28）

Decision: `REVISION_REQUESTED`（第二次设计退修）。逐条核对 D1 残留：

| D1 项 | 核对结论 | D2 依据 |
|---|---|---|
| AR1-1 | 部分关闭，余 AR2-1 | §2.1 S1-h、§3.4/§3.4.1 与 AC-3/4/19 已恢复从 k 帧起跟、至 h 帧收养、六值映射和成功/失败/旧帧测试；AC-4 明确常驻关联器不经 `init` 重建。但 §3.9「不做 SOT 回放兜底」与同节「第二级用数据根 JPEG」互斥，且实际复用的 `controller/reanchor.py::replay_tracker` 可对无效源框返回 `RESEED_DISCARDED_INVALID_BOX`、对非 init 异常返回 `RESEED_FAILED`，现有 `level2.reason` 映射未覆盖这两个实际分支。 |
| AR1-2 | 部分关闭，余 AR2-2 | §3.9 已列 15 个互斥桶、`N_all/N_res/N_vis/N_inv`、末端无解析帧与空层；AC-7 有守恒测试。但 §3.9 同时规定超过 600 个触发样本时只等比抽取 600，而每个原始 (k,o,Δ) 仍须落入 15 桶之一、`Σ桶=N_all`；未抽中样本没有解析结果，也没有已定义的桶或分母处理。 |
| AR1-3 | 关闭 | §3.1 的 `compat` 与 `resident` 方法集互斥，载体分别走 `update` 与 `step`，传感器 `frame_id` 作历史键；AC-1/2/6 给出具名计数、回退与旧路径测试。 |
| AR1-4 | 关闭 | §3.9、§5、§7 及 AC-7/16/17/18/20 将 (g)–(i) 未答复时的缺省固定为零删除、零 Play、零 C2 统计量取样；干净臂与 E2 可独立执行，扰动臂和 Play 均 `NOT_RUN`。这三项仍属于用户待裁定，不因 AR1-4 关闭而获授权。 |

| ID | 未闭合同缺口 | 下一版可核对的完成条件 |
|---|---|---|
| AR2-1 | 第二级回放的执行范围和失败映射不自洽，无法按 AC-3/19 穷尽验证六值与 `level2.reason` 闭集。 | 同步 §2.4、§3.4.1、§3.9、AC-3/19：明确禁做的是「旧框平移后在当前帧 init」还是 k 帧 SOT 回放；逐一给 `replay_tracker` 实际返回事件（含无效源框与非 init 异常）定义六值和 `level2.reason` 映射及具名失败测试；不得删用户已认可的第二级。 |
| AR2-2 | E1 第二级限额与全样本 15 桶守恒同时成立的规则缺失。 | 同步 §3.9、AC-7、报告规格与守恒测试：逐字规定超过 600 时每个未抽中 (k,o,Δ) 的纳入/排除、分母和输出表示；任何未运行解析不得冒充 `NO_TRACK_AT_K` 或成功。若变更数据采样或主指标定义，先交用户裁定。 |

§7 (a)–(f)、(j) 裁定：(a) `Workflow: engineering-v1` 申请符合新工作项形态，但本轮未 `ACCEPTED`，**工程轨道不生效**；不得派实现。(b) E1/E2 保持仅为 K3 的描述性机制证据、不新增数据划分、标签或对外指标时，不触发 K4；AR2-2 须先闭合。(c) 沿用 `det-assoc-v1` 名称及 `mode=resident`，保留兼容路径和 AC-4。(d) 所列 τ、m、`T_slew`、N/M、`r_adopt`、`ω_max`、`ω_arr` 及第二级 `T_replay/L_replay` 可作配置项，须记录生效值，不改冻结规格。(e) 阶段 1 证据写齐可直接进阶段 2，无资格门，仍须先有用户 §5 执行信封。(f) 同意 `ACQUIRING` 与有指针查询期间持续发布，失败/未列组合仍按 AC-13/14 核验。(j) 可沿用冻结 `nanotrack-v2` 作一次性 SOT；失败映射与例外分支须先按 AR2-1 收敛。以上是范围判断，不构成 `ACCEPTED`、BC/AC 冻结或执行授权。

§7 (g)–(i) 用户尚未答复；本轮不代选，缺省仍为零删除、零 Play、零 C2 统计量取样，分别维持 AC-16 清单 `AWAITING_USER`、AC-17/18 `NOT_RUN`、AC-20 `NOT_RUN`。其中 (g) 涉不可逆删除，(h) 涉 Play 信封和 Unity 证据定位，(i) 涉数据采样，均不在 supervisor D5 代选闭集。§5 申请值未经用户逐字签发，各维度仍为 0；未 `ACCEPTED` 前不提请执行信封。主线 §3 逐字引用、接口 A、v1 不做清单、K1K2K3 合并停点和两份收口承接均保留；不改设计正文、不签发 BC/AC 表。

按 workflow §4.2 及账本本项 D1 决策信封：第二次退修后接受角色不自行发第三次；本轮残留 2 项，不多于 D1 的 4 项，且本项尚无代拍，下一交接 Owner 为 supervisor，仅可代选 (a)「保留范围并逐条列已知缺口」；若信封条件不再成立则回用户二选一，不能自启实现。

open_items: AR2-1,AR2-2

### §4.2(a) 接受处置（2026-09-28）

**Decision: `ACCEPTED`（D2 当前文本，非执行或完成授权）。** 依据 `docs/authorizations.md` 同日「P1-ENG-ACQ-001 — supervisor 代拍：D2 第二次退修后按 workflow §4.2 代选 (a)…」执行；保留 §2.1 S1-h 与 §3.4.1 用户认可的第二级「k 帧起跟回放」，保留六值闭集、阶段 1+2 范围和 §4 原 AC-1…20 编号及正文。以下首次接受释义优先于前文冲突句；实现与复核按其字面读，不从冲突自行补义。

| 已知缺口 | 接受处置 | 停点与限制 |
|---|---|---|
| AR2-1 | **以 AC-3/19 接受释义收束。** §2.4 禁做的是「旧框平移后在当前帧 `init` SOT」；§3.9「不做 SOT 回放兜底」仅排除这条当前帧旧框路径，**不排除** §3.4.1 在 k 帧图像 `init` 一次性 SOT 并回放到 h。`DetAssocTracker.init` 仍不得用于换指针；回放后的 SOT 实例丢弃，框不进历史、观测或桥文件。失败映射与补充测试见下表。 | `K3`（并入 `K1K2K3`）；不增加解析结果第七值。 |
| AR2-2 | **保留为具名已知缺口。** §3.9 的每（序列 × `gmc_source` × 臂）最多抽 600 个触发 `(k,o)` 与 AC-7 原始全样本 15 桶、原分母及守恒式同时保留，接受角色不改采样或主指标。若触发数 >600，未抽中的每个 `(k,o,Δ)` 没有第二级解析结果，不能归入 15 桶、不能计作 `NO_TRACK_AT_K`/成功，也不能把抽中子样本的比例标成全样本曲线。须报告 `LEVEL2_SUBSAMPLED`、原始/抽中/未运行数及受影响层和 Δ，AC-7 对这些层记 `NOT_EVALUABLE_AR2-2`，不得宣称 AC-7 满足或全样本 E1 已完成；未超限的层仍按原 AC-7 守恒。 | `K3` 候选可实现和核对已定义的机制；若实际超限，完整 E1/AC-7 与据此作出的整体通过主张被此缺口阻断，交用户裁定后才能改合同或信封。不得以别的桶、分母或指标暗中消除缺口。 |

**AC 接受释义表**（工程轨道的 §4 五列表仍是 AC-1…20 的稳定基础合同；下表给具名条款的首次接受 `BASE` 释义，不新增编号，后续变化按 `AC-n 修订 <m>` 追加）：

| 编号 | 条款（可核对的字面读法） | 复核项 | 证明方式 | 标签 | 依据 | 日期 |
|---|---|---|---|---|---|---|
| AC-3 | 解释 AC-3/§3.4.1：第二级 `replay_tracker` 的 `RESEED_READY` 才进入 h 帧收养；唯一收养→`BOUND`，多轨过门且裕度不足→`AMBIGUOUS`，无过门→`NO_TRACK_AT_K`/`no_adoption`。`RESEED_DISCARDED_MISSING_FRAME`→`NO_TRACK_AT_K`/`not_attempted_frame_missing`；`RESEED_DISCARDED_STALE`→`NO_TRACK_AT_K`/`source_too_old`；`RESEED_DISCARDED_NOT_CONVERGED`→`NO_TRACK_AT_K`/`replay_timeout@<f>`，f 为首个未处理帧。`RESEED_DISCARDED_INVALID_BOX` 若 `reason=invalid_source_box`→`NO_TRACK_AT_K`/`invalid_source_box`，若 `reason=invalid_replay_box`→`NO_TRACK_AT_K`/`sot_lost@<f>`，f 为该失败帧。`RESEED_FAILED` 若 `reason=tracker_init_failed`→`NO_TRACK_AT_K`/`sot_init_failed`，其余异常→`NO_TRACK_AT_K`/`replay_error`，异常类另记诊断字段，不扩 `level2.reason`。 | 行为/边界失败/测试覆盖 | test:`tests/test_resident_core.py::test_level2_failure_*`；artifact:`docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「第二级映射」 | BASE | D2 AR2-1；`controller/reanchor.py::replay_tracker` | 2026-09-28 |
| AC-19 | 解释 AC-19：除原 (a)–(c) 用例，还须具名覆盖无效源框和非 init 异常两个实际分支，核对结果值、`level2.reason`、指针不变、常驻关联器身份不变，以及 SOT 框不发布；原 `sot_lost@<f>`、超时、旧帧用例继续必跑。 | 行为/边界失败/测试覆盖 | test:`tests/test_resident_core.py::test_level2_invalid_source_box`；test:`tests/test_resident_core.py::test_level2_non_init_exception`；test:`tests/test_det_assoc_tracker.py::test_level2_replay_keeps_associator` | BASE | D2 AR2-1；AC-3 接受释义 | 2026-09-28 |
| AC-7 | 解释 AC-7：原 15 桶、`N_all/N_res/N_vis/N_inv`、分层、六个 Δ、比例定义和两条守恒式均不变。触发数 >600 的受影响层按 AR2-2 记 `NOT_EVALUABLE_AR2-2`，仅可展示有来源标记的抽中子样本诊断，不能用它替代 AC-7 全样本结果；报告明确列未运行数。未触发超限时仍须按原 AC-7 全样本验证。 | 文档一致/边界失败/测试覆盖 | artifact:`docs/evidence/P1-ENG-ACQ-001-report.md`「E1」；test:`tests/test_eng_acq_e1.py::test_buckets_exhaustive_and_conserved` | BASE | D2 AR2-2；§3.9/AC-7 | 2026-09-28 |

复核项覆盖：行为 ✓ | 几何时序 ✓（§4 AC-2/5/14/15） | 边界失败 ✓ | 测试覆盖 ✓ | 文档一致 ✓。原 §4 AC-1…20 的证据指针和 `K1K2K3` / Play D1 停点不变；本表的证明方式是原证据的具名补充。§7 (a) **逐字裁定 `Workflow: engineering-v1` 生效**：本项是账本 09-28 D.8 新工程工作项，合同为 §1–8 与 AC-1…20，必经 `C1@K1K2K3` 后独立 `R1@K1K2K3`；K4/K5 不由当前范围触发。§7 (b) E1/E2 仅作为 K3 描述性证据，不新增划分、标签、对外指标；(c) 沿用 `det-assoc-v1` 与 `mode=resident`，旧 `compat` 路径和 AC-4 保留；(d) τ、m、`T_slew`、N/M、`r_adopt`、`ω_max`、`ω_arr`、`T_replay/L_replay` 为可记录生效值的插件/会话配置，不改冻结规格；(e) 阶段 1 证据写齐后可直进阶段 2，不设资格门；(f) `ACQUIRING` 与有指针查询期间持续发布，失败及未列组合按 AC-13/14 核验；(j) 第二级只用冻结 `nanotrack-v2` 一次性 SOT，并按 AC-3/19 上表映射失败。以上不签发执行额度。

**仍待用户。** §7 (g)–(i) 未代选、未获授权：零删除、零 Play、零 C2 统计量取样；AC-16 清单 `AWAITING_USER`，AC-17/18/20 `NOT_RUN`，不得记满足。§5 阶段 1+2 信封只为申请值：零 scenario/session/run ID、零 Play/API/GPU·h/检测新推理/模型启动/下载/pip/5060 访问；仅本地 `outputs/eng-acq/`、证据及代码测试写入，CPU E1/E2 约 27 次回放（4,832 帧）和每（序列 × `gmc_source` × 臂）最多 600 个 `(k,o)` × 65 帧 NanoTrack 回放。**推荐用户逐字签发此阶段 1+2 原申请信封**，以便按原限额验证机制；签发前所有额度均为 0，不得派 Implementation。Play D1 的 1 次 Play、1 个 session ID、≤3 min、在线检测与 1 次权重加载及约 90 MB 归档另签，不随本次信封生效。AR2-2 若实际触发超限，推荐用户选择允许全样本第二级解析并另签所需 CPU 上限，以保留原 15 桶和分母；这会改变现有抽样上限，**本次不代定**，保持具名缺口。用户未裁定前，AC-7 受影响层不得通过。

open_items: AR2-2,USER_EXECUTION_ENVELOPE,USER_G,USER_H,USER_I

### §5 信封与 §7 (g)(h)(i) 答复落实（2026-09-28；CLARIFY）

依据 `docs/authorizations.md` 同日「P1-ENG-ACQ-001 — 用户签发 §5 阶段 1+2 执行信封（序列回放 ≤40、本机 CPU 墙钟 ≤3 h）并答复 §7 (g)(h)(i)（supervisor 会话代录）」；用户已逐字签发和选择，本节由接受角色落实 §7「待用户」的先更新合同条件。以下 `AC-n 修订 1` 逐行解释 §4 的同号原条款，不覆盖或重编号；本节与原条款冲突时以本节为准，其他要求继续生效。

**执行信封生效值与归因（一行）：** §5 阶段 1+2 单候选 `K1K2K3` 已按申请值签发，唯 CPU 序列回放改为 ≤40 次，另加本机 CPU 墙钟 ≤3 h，覆盖全部本机 CPU 工作（含 E1/E2、第二级 NanoTrack 回放、解析及其他本机 CPU 工作），与回放次数上限先到者即停；每（序列 × `gmc_source` × 臂）第二级 ≤600 个 `(k,o)` × ≤65 帧；其余维度逐字按 §5 阶段 1+2 申请值（scenario/session/run ID、Play、API/VLM、GPU·h、检测推理、模型启动、下载、pip、5060/其他远端访问均 0，本地写入范围见 §5 与下表 AC-9 修订 1）；成功、失败、重试共用同一上限，信封内工程性重试与 supersession 计入同一额度；Play D1 申请列不在此信封内，1 次 Play 须另签。授权来源与改值归因均为上述用户账本条目，不从约 27 次申请估算额度。

| 编号 | 验收项修订（可证伪；引用原条款） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-7 修订 1 | 解释 AC-7：干净臂仍按 AC-7 与 AR2-2 接受释义核对；§7 (i) 已选 `c2_quantiles`，`perturbed_arm` 不再写 `PENDING_USER_(i)` 作为当前结果。未运行扰动臂时须如实记 `NOT_RUN`，运行后才可记所用模型和结果；不得把干净臂结果代作 AC-20 通过或把受 AR2-2 影响的层写成全样本通过。 | artifact: `docs/evidence/P1-ENG-ACQ-001-e1.json`；artifact: `docs/evidence/P1-ENG-ACQ-001-report.md`「E1」 | K1K2K3 | 2026-09-28 |
| AC-9 修订 1 | 解释 AC-9 的 `runtime/` 零写入断言：唯一例外是 AC-16 修订 1 所准许、清单先入证据后对本地 `runtime/hold-diag-loopb-*` 的删除；该删除及其清单须单独记录并从零写入断言中具名剔除。其余 `runtime/` 路径、数据根和 §5 写入限制照旧；清单前删除、删除其他文件或以清理掩盖线束写入均不满足。 | artifact: `docs/evidence/P1-ENG-ACQ-001-cleanup.json`；artifact: `docs/evidence/P1-ENG-ACQ-001-ledger.json`；test: `tests/test_eng_acq_guards.py` | K1K2K3 | 2026-09-28 |
| AC-16 修订 1 | 解释 AC-16/§7 (g)：先把本地 `runtime/hold-diag-loopb-*` 及 H-5 相关物的路径、来源、大小、保留理由、建议动作清单写入证据，再删除清单所列本地 `runtime/hold-diag-loopb-*`；记录实际删除路径与结果。5060 `repo-b` 由用户自行删除，本项 5060 访问仍为 0，实施角色不得远端盘点或删除；远端大小无既存来源时在清单写 `UNKNOWN_UNVERIFIED`，不可为补数访问 5060。诊断 6 留在 `runtime/` 的其他桥文件与帧仍只入清单，不因本次答复获得删除许可。清单缺项、先删后记或越界删除均不满足。 | artifact: `docs/evidence/P1-ENG-ACQ-001-cleanup.json` | K1K2K3 | 2026-09-28 |
| AC-17 修订 1 | 解释 AC-17/§7 (h)：Play D1 定位为本项正式用户 Unity 验证；触及预览/采集/保存路径时，Play D1 前 ≥2 张样帧的人眼保真核对仍须完成并入证据。§5 阶段 1+2 信封不含 Play；Play D1 未另签且未运行时本条记 `NOT_RUN`，不得以正式定位替代人眼检查或记满足。 | artifact: `docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「人眼保真」；artifact: `docs/unity-test-log.md`「UT-P1-ENG-ACQ-001-D1」 | Play D1 | 2026-09-28 |
| AC-18 修订 1 | 解释 AC-18/§7 (h)：Play D1 是正式用户 Unity 验证，按 §3.10 剧本与原 AC-18 证据口径执行，入 `UT-P1-ENG-ACQ-001-D1`；须另获 1 次 Play 授权，当前 Play/session ID/在线检测/权重加载额度均为 0，故当前及 `K1K2K3` 候选均记 `NOT_RUN`。即使 `K1K2K3` 通过，Unity 验证未通过前 Overall 最高为 `IMPLEMENTED_REVIEWED_AWAITING_UNITY`，不得记 `DONE`；正式定位本身不构成通过。 | artifact: `docs/unity-test-log.md`「UT-P1-ENG-ACQ-001-D1」；artifact: `docs/evidence/P1-ENG-ACQ-001-play-d1.md` | Play D1 | 2026-09-28 |
| AC-20 修订 1 | 解释 AC-20/§7 (i)：扰动臂唯一选定 `--perturb c2_quantiles`，只读取 C2 347 行 IoU 分位数统计量，不回放 H 帧、不读取逐帧 C2 预测文件作为线束输入；固定种子缩放与平移后，实现 IoU 的 p10/p25/p50 与来源分位数各差 ≤0.05，记录 347 行来源、三组分位数与差值。15 桶、分母、守恒、复现按 AC-7；执行前仍须守 §5 生效信封及 AR2-2 600 上限，未运行或受 AR2-2 阻断者如实记 `NOT_RUN`/`NOT_EVALUABLE_AR2-2`，不得记满足；`uniform` 不执行。 | artifact: `docs/evidence/P1-ENG-ACQ-001-e1.json`「perturbed_arm」；cmd: `tools/eng_acq/run.py e1 --perturb c2_quantiles` | K1K2K3 | 2026-09-28 |

§7 (g)(h)(i) 已获用户答复；原 §3.9/§3.10/§5/§7 及 §4 各条的「答复前」句只记当时缺省，不再作为现行禁止条件。AR2-2 保留原每（序列 × `gmc_source` × 臂）600 上限，未预授权全样本第二级解析或额外 CPU；超限层的 `NOT_EVALUABLE_AR2-2` 与须回用户改合同/信封的具名缺口不变。实现按阶段 1 → 阶段 2、`C1@K1K2K3` → `R1@K1K2K3` 交接；本节不签发 Play D1、不改变工程轨道或停点。

open_items: AR2-2,USER_PLAY_D1_ENVELOPE

### 信封修订 SUB:1/SUB:2 落实（2026-09-29；CLARIFY）

依据 `docs/authorizations.md` 同日「P1-ENG-ACQ-001 — 用户批准实现角色追加申请 SUB:1（a7 第二级全样本）与 SUB:2（每 (k,o) SOT 帧上限 ≤66），修订 §5 阶段 1+2 执行信封（supervisor 会话代录）」；来源为 `docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「待裁定」IR-9 与 `docs/evidence/P1-ENG-ACQ-001-report.md`「第二级代价与 AR2-2 / 65 帧上限」。以下修订优先于 §3.9、§5、§4 AC-7/20、前述 AR2-2 处置及修订 1 中冲突的旧上限；原条款、编号和历史候选读数均不覆盖。

**AR2-2 现行处置：** a7 在每个（序列 × `gmc_source` × 臂）组合的第二级触发 (k,o) **全样本运行**，取消该序列的 600 个 (k,o) 抽样上限；scout-1、m3-armA 等其他序列仍各 ≤600。§3.9 每个 (k,o) 的第二级 SOT 回放帧上限对**全部序列**由 ≤65 改为 ≤66，各 Δ 共用前缀；超过 66 帧的解析仍不得伪装成已运行。原 15 桶、分层、六个 Δ、`N_all/N_res/N_vis/N_inv`、五个比例定义、两条守恒式及主指标定义均不变。AR2-2 对 a7 的具名缺口在新候选完成全样本重跑并逐层核对前仍开；原候选 a7 `NOT_EVALUABLE_AR2-2`、Δ13 `NOT_EVALUABLE_FRAME_CAP` 均不追溯改判。新报告须按实际重跑结果判断受影响层是否可评估，不以签发上限代替结果。

**执行信封生效值与归因（一行）：** §5 阶段 1+2 的 a7 第二级 = 全样本、其他序列每（序列 × `gmc_source` × 臂）≤600 个 (k,o)、全部序列每 (k,o) SOT ≤66 帧；CPU 序列回放 ≤40 次（成功、失败、重试合计）、本机全部 CPU 工作墙钟 ≤3 h，先到者即停；scenario/session/run ID、Unity Play、API/VLM、训练 GPU·h、检测推理、YOLO 权重加载、下载、pip、5060/其他远端访问均为 0，本地写入范围、Play D1 另签及其余 §5 阶段 1+2 维度逐字不变；信封内重跑与 supersession 计入同一余额。`docs/evidence/P1-ENG-ACQ-001-ledger.json` 现记回放 35/40、CPU 墙钟 2169.736/10800 s；E1 解析既有记录计 0 次序列回放，余额足以先尝试缓存关联记录上的 a7 全样本与 Δ13 重跑，执行角色须逐次记账并在任一上限到达时停止。

| 编号 | 验收项修订（可证伪；引用原条款） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-7 修订 2 | 解释 AC-7/§3.9：E1 两臂的 a7 第二级对每个 `gmc_source` 跑全体触发 (k,o)，其他序列仍守 600 上限；所有序列的每 (k,o) SOT 最多 66 帧。新候选须重跑 a7 全样本和受旧 65 帧上限阻断的 Δ13 层，逐层重新给出 15 桶、原分母与守恒、比例、第二级子表及固定种子复现证据；未运行的 (k,o,Δ) 不入桶、不冒充 `NO_TRACK_AT_K` 或成功。签发修订本身不使旧候选的 `NOT_EVALUABLE_*` 变成满足。 | artifact: `docs/evidence/P1-ENG-ACQ-001-e1.json`；artifact: `docs/evidence/P1-ENG-ACQ-001-report.md`「E1」；test: `tests/test_eng_acq_e1.py::test_buckets_exhaustive_and_conserved` | K1K2K3 | 2026-09-29 |
| AC-20 修订 2 | 解释 AC-20/AC-7 修订 2：已选的 `c2_quantiles` 扰动臂同样适用 a7 全样本、其他序列 600 上限与全部序列每 (k,o) ≤66 帧；原分位数容差、15 桶、分母、守恒和复现要求不变。 | artifact: `docs/evidence/P1-ENG-ACQ-001-e1.json`「perturbed_arm」；artifact: `docs/evidence/P1-ENG-ACQ-001-report.md`「E1」 | K1K2K3 | 2026-09-29 |

本轮只落实已签授权，不做 `C1@K1K2K3` 核对或裁定 IR-1…20；实现角色按余额重跑并更新 E1 报告、自证后交新候选。Play D1 仍未签。

open_items: AR2-2,USER_PLAY_D1_ENVELOPE

### 信封修订 SUB:3 落实（2026-09-29；CLARIFY）

依据 `docs/authorizations.md` 同日「P1-ENG-ACQ-001 — 用户批准实现角色追加申请 SUB:3（scout-1 第二级每 (k,o) SOT 帧上限 ≤87），修订 §5 阶段 1+2 执行信封（supervisor 会话代录）」；来源为 `docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「待裁定」IR-21、「待用户（needs_user，续派 9b04）」与 `docs/evidence/P1-ENG-ACQ-001-report.md`「E1」。本节仅将 scout-1 每 (k,o) 第二级 SOT 帧上限由 ≤66 改为 ≤87，优先于前述修订 2 的全序列 ≤66 句；原条款、编号和历史候选读数不覆盖。

**执行信封生效值与归因（一行）：** §5 阶段 1+2 的 scout-1 每 (k,o) 第二级 SOT ≤87 帧；a7、m3-armA 仍各 ≤66 帧，a7 第二级全样本、其他序列每（序列 × `gmc_source` × 臂）≤600 个 (k,o)；序列回放 ≤40 次、本机全部 CPU 工作墙钟 ≤3 h，先到者即停；其余维度逐字不变（零 scenario/session/run ID、Play、API/VLM、训练 GPU·h、检测推理、YOLO 权重加载、下载、pip、5060/其他远端访问；本地写入仍限 §5 已签范围，Play D1 另签）。成功、失败、重试及 supersession 共用原余额；`docs/evidence/P1-ENG-ACQ-001-ledger.json` 当前回放 35/40、墙钟 3168.105/10800 s。来源报告估算 E1 两臂各两次整体重跑约 850 s、0 次序列回放，仍在余额内；实现角色须逐次记账、任一上限到达即停。

| 编号 | 验收项修订（可证伪；引用原条款） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-7 修订 3 | 解释 AC-7/AC-7 修订 2：E1 干净臂 scout-1 每 (k,o) 第二级 SOT 最多 87 帧；a7、m3-armA 仍最多 66 帧。a7 全样本、其他序列每组合 600 上限、15 桶、原分母、两条守恒式、六个 Δ、五个描述性比例及主指标定义均不变。新候选须在余额内重跑 scout-1 Δ13 层，连同 E1 两臂整体重跑与固定种子复现；未运行的 (k,o,Δ) 不入桶、不冒充已评估，旧候选的 `NOT_EVALUABLE_FRAME_CAP` 不追溯改判。 | artifact: `docs/evidence/P1-ENG-ACQ-001-e1.json`；artifact: `docs/evidence/P1-ENG-ACQ-001-report.md`「E1」；test: `tests/test_eng_acq_e1.py::test_buckets_exhaustive_and_conserved` | K1K2K3 | 2026-09-29 |
| AC-20 修订 3 | 解释 AC-20/AC-20 修订 2：已选 `c2_quantiles` 扰动臂的 scout-1 每 (k,o) 第二级 SOT 同样最多 87 帧；a7、m3-armA 仍最多 66 帧，其余采样、分位数容差、15 桶、分母、守恒与复现要求不变。 | artifact: `docs/evidence/P1-ENG-ACQ-001-e1.json`「perturbed_arm」；artifact: `docs/evidence/P1-ENG-ACQ-001-report.md`「E1」 | K1K2K3 | 2026-09-29 |

本轮只落实 SUB:3 授权，不做 `C1@K1K2K3` 核对，也不裁定 IR-1…21；它们留待新候选的 C1。AR2-2 须待新 E1 全样本结果逐层核对，Play D1 仍未另签。

open_items: AR2-2,USER_PLAY_D1_ENVELOPE

### C1 待用户裁定落实（2026-09-29；CLARIFY）

依据 `docs/authorizations.md` 同日「P1-ENG-ACQ-001 — 用户裁定 C1 待用户两项：IR-3 把 AC-15 的 look_at 义务限于发布窗口内处理帧；AC-11 确无既存 index 散列记录时固定本次基线（supervisor 会话代录）」。以下只追加 AC-11、AC-15 的同号修订，不覆盖 §4 原条款或 C1 当时候选的核对结论；本节与 §3.8、§4 AC-11/15 冲突处以本节为准。其余 AC、信封、采样、主指标及发布门 ①④ 均不变。本轮不做 C2 核对。

| 编号 | 验收项修订（可证伪；引用原条款） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-11 修订 1 | 解释 AC-11 的 `catalog-index.jsonl.gz` 来源散列句：先查找独立既存的该文件散列记录，与本机实测 sha256 比对；查找范围、逐处过程、命中记录及比对结果写入证据。若确无既存记录，须在证据中给出可复查的查找范围与未找到的结论，测量并固定本次完整 sha256 为后续基线，在报告标注「既往不可核」；不得把本次基线冒充既存来源记录。既存记录存在却不一致、未查即固定基线、缺完整散列或缺上述证据均不满足。权重、`freeze.json`、`frozen-B/V` 仍须逐项与既存来源散列比对；原 AC-11 的 AC-4 偏差声明和旧读数禁用不变。 | artifact: `docs/evidence/P1-ENG-ACQ-001-assets.json`「catalog-index.jsonl.gz」；artifact: `docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「AC-11 index 散列查找」；artifact: `docs/evidence/P1-ENG-ACQ-001-report.md`「资产与偏差声明」 | K1K2K3 | 2026-09-29 |
| AC-15 修订 1 | 解释 AC-15/§3.8：对每个已处理、指针 track 有效、处于现有发布窗口内且能通过现有发布门的帧，恰发一次 `look_at`；遗漏、重复或相邻已发指令视线角变化 > ω_max/hz 均不满足。追平时窗口外更旧帧仍逐帧 `step` 更新跟踪状态，且逐帧显式记录因窗口外跳过发布，不为该旧帧发 `look_at`；漏 `step`、漏跳过记录或向旧帧发令均不满足。机身规划器输入不变；现有发布门 ①④ 及其他门的条件与失败处理不变，不能以发令绕过发布门。 | test: `tests/test_track_loop.py::test_servo_rate_clamp`；test: `tests/test_track_loop.py::test_publish_window_skips_stale_backlog`；artifact: `docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「AC-15 发布窗口与跳过发布」 | K1K2K3 | 2026-09-29 |

C1 的 AC-3/IR-8 第 30 次 coasting 边界退回维持；AC-11 须先查找，AC-15 按上表返工，自证新候选交 `C2@K1K2K3`。C1 是唯一退回；C2 即使有未决项仍附核对表交独立复核。Play D1 未签，AC-17/18 仍 `NOT_RUN`。

open_items: C1_AC3_IR8,C1_AC11,C1_AC15,USER_PLAY_D1_ENVELOPE

### R2@K1K2K3 通过轮消费与 R2-1 处置（2026-09-29）

消费 `docs/reviews/P1-ENG-ACQ-001.md`「R2@K1K2K3」§0–6 的 `PASS_WITH_NOTES`：R1-1/2/3 修前红、修后绿闭合，修复触及行无新 CLASS_1/2；通过候选由复核文件机读行运行时解析。本轮不重做候选核对、不跑测试、不签独立复核。R2-1 是未改动行的 `上轮漏检` CLASS_2，按 workflow §4.4 不推翻 R2 通过轮，但其 `blocks_consuming_gate` 仍在效；AC-17/18 `NOT_RUN`，复核附议不适用 `UNITY_NA`，所以不能记 `DONE` 或开启 Play D1。

**R2-1 / IR-24：裁定路径 (a)，范围内必修。** §3.6 重建后再指定是现行生产路径；AC-15 修订 1 已要求跨相邻已写云台指令视线角 ≤ ω_max/hz，重建后首条伺服相对上一条已写点超限是现有合同的实违，不是不可达的 `SCOPE_GAP`。交实现角色在现有范围内跨载体传递最后已写云台点，补会话级 `frame_gap → 重建 → 远目标再指定` 回归（修前必红，修后首条已写伺服相对上一条已写指令 ≤ ω_max/hz），自证后直接回独立复核红绿核实；由复核角色写 `releases_consuming_gate: R2-1`。该修复不新增 AC、不放宽安全约束、不增加信封维度；若实现发现确需改合同或越出已有额度，先回接受角色按授权规则处理。release 前一切消耗性交接保持关闭。

**IR-23：接受为具名残余边界。** 复核 §2 核实窗口读取与门 ④ 读取之间仍可能恰逢新帧，仅在追平窗口边缘触发原有 fail-closed `REINIT_REQUIRED(catchup_stale)`，没有错误指令。现行 AC-15 修订 1 明定发布门 ①④ 条件与失败处理不变，本轮不缩窗口、不吞门拒、不改合同。Play D1 若获授权须记录 `catchup_stale` 次数及对应上下文，作为描述与后续裁定材料；不新设通过阈值，也不以离线 R2 结果宣称在线无此现象。若要消除这一残余而改发布门、窗口或验收条件，须先回用户签字。

**IR-19：维持 C2 核对表「IR-1…22 读法裁定」的接受读法。** `P1-ENG-LOOP-001` 已 `CLOSED_SUPERSEDED`，旧冻结路径测试检查未提交改动，不能覆盖本项已接受的 `track_loop.py` 修改；本轮不改旧测试。后续若触及该测试，另按当时范围判断。

**Play D1 待用户另签（不随本裁定生效）。** 推荐在 R2-1 经独立复核 release、AC-17 至少 2 张样帧由人眼确认并把路径/确认人/结论记入证据、正式 Unity 采集前按 workflow §4.5 核对候选与工作树、`candidates` 后端及保留帧配置就绪后，签发 §3.10 的正式用户验证信封：1 次 Play、仅该次产生的 1 个 session ID、≤3 min、`retained_frame_count ≥ 1500`；Play 期间本机 MPS/CPU 在线检测、YOLO 权重加载 1 次、归档上限约 1500 帧/90 MB；scenario/run 新 ID 0、API/VLM 0、训练 GPU·h 0、下载/pip/远端访问 0。成功、失败与重试共用该 1 次额度，超出另请用户授权。IR-23 的 `catchup_stale` 只作记录；AC-17/18 的正式 verdict 仍取用户 Unity 反馈。

### R3@K1K2K3 通过轮消费（2026-09-29）

消费 `docs/reviews/P1-ENG-ACQ-001.md`「R3@K1K2K3」§0–7 的 `PASS_WITH_NOTES`；通过候选只从 §7 `passed_candidate` 机读行运行时解析。R2 §3 的 `blocks_consuming_gate: R2-1` 与 R3 §3 的 `releases_consuming_gate: R2-1` 在同一文件按序、同 ID 配对；复核 §1 已核修前红/修后绿，R2-1 闭合，消耗性门阻断解除。本轮不重做候选核对、不跑实现测试、不签独立复核。R1-4 `SCOPE_GAP`/`OPEN` 账本债仍在；IR-23 按上节在 Play D1 记录 `catchup_stale`，不新设门值。

R3 §4 为非 finding 观察，当前无需返工或新增 AC：`nadir` 下 `set_nadir` 虽改变相邻已写云台指令，但该状态不发伺服 `look_at`，承接基准不会用于发令；`REINIT_REQUIRED` 期间保持基准与现有 §3.8 视线角口径一致。R1 §5 的旧观察也维持非 finding。若将来在 `nadir` 下启用伺服，须在该变更的 K2 停点检查 `set_nadir` 后基准失效与限速行为；本轮不预改合同。

代码停点已独立复核通过，Overall 为 `IMPLEMENTED_REVIEWED_AWAITING_UNITY`、Lifecycle 继续 `ACTIVE`。AC-17/18 仍 `NOT_RUN`，复核 §6 附议不适用 `UNITY_NA`；无正式 Unity verdict，不记 `DONE`。Play D1 信封仍须用户另签，上节推荐值不因 R2-1 release 自动生效。建议先由 Implementation 在零 ID/Play/API 下整理**当前候选**的两张可核对预览样帧路径清单（至少一张红车检测候选、一张静止 B/C 车检测候选；逐张标源帧与候选框），写入 `docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「人眼保真」；尚无当前候选样帧则明确记缺，不借旧管线诊断帧宣称通过。由用户或当轮发令角色逐张核对检测候选所框对象、颜色/身份与同帧 Unity 运行外观及语义一致，记录样帧路径、确认人、逐张结论。正式采集前再按 workflow §4.5 核对复核候选对应代码及 HEAD/工作树并记入 Unity 日志，确认 `candidates` 后端与 `retained_frame_count ≥ 1500` 配置就绪；任一前置未满足，不开启正式 Play D1。

### Play D1 信封与 AC-17 样帧核对落实（2026-09-29；CLARIFY）

**授权与归因：**依据 `docs/authorizations.md`「2026-09-29 P1-ENG-ACQ-001 — 用户确认 AC-17 三张预览样帧并签发 Play D1 信封（重试不计次数、由用户提起；supervisor 会话代录）」落实 §5 Play D1 申请列；该条的改值优先于 §5 旧申请和「R2@K1K2K3 通过轮消费与 R2-1 处置」的推荐值。正式用户 Unity 验证每次尝试 ≤3 min；**重试不计次数且仅由用户提起**，角色不得自行发起重试。每次尝试各 1 个 session ID、各 1 次 YOLO 权重加载、各归档约 1,500 帧 / 90 MB，`retained_frame_count ≥ 1500`；Play 期间本机 MPS/CPU 在线检测不计次。新增 scenario/run ID 0，API/VLM 0，训练 GPU·h 0，下载/pip 0，5060/其他远端访问 0；未授权代码或 Unity 场景改动、执行信封子额度块。每次尝试均入 `docs/unity-test-log.md` 的 `UT-P1-ENG-ACQ-001-D1`，正式 verdict 取用户指定的一次，未指定取最后一次；任何越界回用户。本段为已签信封归因，不把多次尝试推作角色自行重试额度。

**AC-17 裁定：**S2-d 触及候选预览内容，代码中的采集、保存、预览渲染路径未变。`docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「人眼保真」列出当前候选路径离线渲染的 S1/S2/S3 样帧、源归档帧与候选框；`docs/unity-test-log.md`「P1-ENG-ACQ-001 — AC-17 人眼保真样帧核对」记录用户逐张结论均为“无问题”。这些是既往 Unity 归档帧经当前候选预览路径离线渲染，足以核对图中对象、框、index 与归档运行外观/语义；据此裁定 AC-17 所定“Play D1 前 ≥2 张样帧人眼核对”前置已满足。该结论不称样帧是 Play 同帧实时画面，也不预判实时预览、采集链或 AC-18 的 Unity verdict。Play D1 操作单须要求在正式尝试中记录实时预览所框对象、颜色/身份与同帧 Unity 画面是否一致；如实记用户观察，不预置“无问题”结论。

**合同追加修订（原文保留，依据上述账本条目）：**

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-17 修订 2 | 解释 AC-17/修订 1 的样帧前置：当前候选路径对既往 Unity 归档帧的离线预览样帧可用于 Play 前人眼保真核对；S1/S2/S3 用户逐张“无问题”已满足 ≥2 张前置。正式 Play 的实时候选预览仍须对照同帧 Unity 画面记录，不以离线核对代替该运行观察或 AC-18 verdict。 | artifact: `docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「人眼保真」；artifact: `docs/unity-test-log.md`「P1-ENG-ACQ-001 — AC-17 人眼保真样帧核对」 | Play D1 | 2026-09-29 |
| AC-18 修订 2 | 解释 AC-18/修订 1 与 §3.10：Play D1 可有多次正式尝试，仅用户可提起每次重试；每次均按完整剧本独立记录操作、四类描述数字、六值/`ACQUIRE_FAILED` 分布及 `catchup_stale` 次数/上下文。每次结果保留在 `UT-P1-ENG-ACQ-001-D1`，正式 verdict 取用户指定的一次，未指定取最后一次；前次尝试不得被覆盖或自动合并为通过。Play 未运行仍 `NOT_RUN`，通过门仍取用户正式反馈。 | artifact: `docs/unity-test-log.md`「UT-P1-ENG-ACQ-001-D1」；artifact: `docs/evidence/P1-ENG-ACQ-001-play-d1.md` | Play D1 | 2026-09-29 |

**交接与停止条件：**本轮未运行 Play、未创建 ID。当前仓库没有本项可直接照做的 Play D1 操作单，`runtime/scenario_config.json` 尚未就绪；先交 Implementation 在零 Play/ID/API、零代码与 Unity 场景改动下准备本项操作单与配置就绪凭据，写清 `candidates` 后端、§3.10 完整剧本、每次尝试的账本与实时预览核对、失败/重试的用户发起限制，并确认 `retained_frame_count ≥ 1500`。准备后回 Acceptance：由当轮发令的 Acceptance 在**每次正式采集前**按 workflow §4.5 运行 `git rev-parse HEAD`、`git status --porcelain`，核对工作树与 R3 机读 `passed_candidate` 的实现代码一致（只容许白名单文档差异），并把结果、后端与保留帧配置就绪情况写入该次 Unity 日志条目；之后才交 User 按操作单启动。任一核对不满足则不开 Play、回 Implementation 修正或上报越界；AC-18 保持 `NOT_RUN`，Overall 不变。

open_items: PLAY_D1_OPERATIONS, PLAY_D1_PREFLIGHT, AC-18_UNITY_VERDICT

### candidates 后端接线窄范围修复 CLARIFY（2026-09-29）

**授权与边界。**依据 `docs/authorizations.md` 2026-09-29「用户授权窄范围代码修复（`candidates` 后端接线 B1–B3）」「用户指示：Unity 不在本机运行」「用户确认 AC-17 三张预览样帧并签发 Play D1 信封」三条及 `docs/evidence/P1-ENG-ACQ-001-play-d1.md` §0。新增授权仅为一个 **Consuming=no** 的 B1–B3 代码/测试批次：只改所需 `controller/`、`tests/`，必要时 `tools/`；scenario/session/run ID、Unity Play、模型 API/VLM、训练 GPU·h、检测推理、YOLO 权重加载、下载、pip、5060 及其他远端访问（含 Unity 主机）、序列回放全为 **0**。不改 Unity 场景或 Play D1 已签数值；执行信封子额度块不启用。用户选择「等代码修完再跑」Unity 主机就绪清单；角色不得远程访问该机。上一节末的「无操作单、代码未授权、按 R3 候选放行」交接和 `open_items` 是当时状态，现由本节和状态板取代。现有操作单是准备稿，修复及新候选复核前不做 §3 核对或 Play。

**IR-17 / B1–B3 的合同读法。**`run --backend candidates` 必须从 CLI 闭集进入 `CandidatesBackend()`，与 `--tracker det-assoc-v1 --resident` 配套；省略 `--model-form` 时对该后端取 `detector-tracks`，显式传其他形态或用非 `candidates` 后端配 `detector-tracks` 均在启动前拒绝。候选仍只来自查询帧 N 的常驻 `tracked` 历史，不调用 VLM/真值投影；不改变 `predict_one→interpret→预览→confirm→designate` 的选框与身份规则。结果 schema 的 `backend` 闭集追加 `candidates`、`model_form` 闭集追加 `detector-tracks`，并约束二者只能成对出现；原三后端和三种 VLM 形态的合法组合保持。`CandidatesBackend.identity` 中 `backend`、`model_form`、`source` 要与收据身份一致；会话首次 `ask` 的 `results.jsonl` 必须能写出并读回该 model 块，不能仅以直接调用 `predict_one` 与 `interpret` 证明 B3。

**K 收据、时效与生成顺序（B2）。**`candidates` 仍须 `--k-receipt`，不借用 `P1-ENG-LOOP-001` 的 `http`/5060/R=128 收据，也不伪造 VLM 权重身份。宿主固定为运行 Unity 与 Python 会话的**另一台 Mac**（收据 `host=mac`、`backend=candidates`、`model_form=detector-tracks`，`model_identity` 含上述三字段）；不得接受 5060/HTTP、VLM 权重或本机开发 Mac 的报告。对这一后端，`validate_measurement_sources` 走单宿主分支：只接受一份由 Unity 主机在代码修复并经 `C1@K1K3`、`R1@K1K3` 通过后本地生成的 `mac` 报告及其真实 SHA；报告须记录机器名，校验时与运行会话的本机机器名一致。还须验证报告的宿主、后端/形态/身份、实测 `p95_s`、`hz`、`retained_frame_count` 与收据相等，并验证报告 SHA、`p95_s` 有限且 ≥0、现有资格式成立。不得要求 5060 报告、运行双宿主选择，也不得让 `replay` 免校验路径代替生产 `candidates` 收据。现有 VLM 双报告校验与 `replay` 语义保持。

实测来源限**适配器本身**：在 Unity 主机按修复候选提供的本地预检命令，用合成历史行（`none` 与最多 8 个 `tracked` 候选）、归档帧名和单调钟对 `CandidatesBackend.predict_one` 分别做 ≥100 次无模型调用，取两组端到端墙钟 p95 的较大值；报告写明环境、样本数、两组 p95 与所取值，不把返回对象的 `latency_ms=0` 冒充实测。该预检不读取或回放序列，不启动 Unity/会话、不建 ID、不加载权重或调用检测器，故为零消耗；**用户**在 Unity 主机按就绪清单运行并回传报告/收据，接受角色核其来源与配置，角色不远程代跑。实现者可用临时合成报告/收据做零消耗红绿测试，但不得把开发机夹具当正式收据。若 Unity 主机尚无可用归档帧名，纯合成合法 `frame_<id>.jpg` 路径即可，预检不得读图。

用户在该机先按操作单 §2.6 生成完整 `runtime/scenario_config.json` 覆盖，再测并生成收据；正式 Play D1 当前预期 R=1500，**收据 R 必须逐字等于实际生效配置的 `retained_frame_count`**（且满足 Play 信封 ≥1500），`hz` 同样取该配置。R/hz、后端/形态/身份或报告内容变化即重新本机预检和生成收据；不得复制旧 R=128 收据或只改 JSON 字段。`K_ret=ceil(p95_s×hz)+2`、`T_ret=K_ret/hz`，`T_conf=10 s`、`K_conf=ceil(10×hz)`、`K_pub=2`、`T_pub=2/hz`，资格式 `K_ret+K_conf+K_pub≤R−8`；这些是既有 LOOP-001 AC-10 修订 1 与 `LanguageSession` 检查点的预算，对纯本地候选也适用。确认同时受查询起点 `T_ret+T_conf`、首次预览呈现起 `T_conf` 和累计帧差 `K_ret+K_conf` 限制，重复显示不续期；4 s 人工等待可能被任一门拒绝，须原样记 `stale_rejected`。上述 p95 只覆盖适配器转换，不是在线检测/整体 Play 时延或成功保证；Play 中若实际过期，按原失败路径记录，不放宽截止。

**B4/B5 裁定。**均**不并入**本代码批次。B4 的 `{0,4}` s 是可选操作者延迟，Play D1 操作单 §5 的预览后人工计时 0 或 4 s 即满足该选项；每次记录预览/确认时刻及实际等待，超截止如实失败，不新加 CLI 注入。B5 的四类数字继续按 §3.10 与操作单 §6 从会话 JSONL、逐帧归档、sidecar 和人工目检/离线真值评分逐次读取；允许记不可计算及原因，不因没有新脚本把描述数值判成通过或自动合并多次尝试。真值只在离线评分，不能进入候选。Play 尚未运行，AC-18 仍 `NOT_RUN`。

**合同追加（IR-17 是实现角色「待裁定」来源；原 AC 文本及既有修订保留）：**

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-21 | IR-17/B1–B3：无权重/无检测/无序列回放夹具中，`run --backend candidates` 与缺省或显式 `detector-tracks` 构造真实 `CandidatesBackend`；交叉形态、身份/宿主/R/hz/报告 SHA 不符在会话前 `CONFIG_MISMATCH`；合成 `mac` 单报告能通过且 VLM 双报告路径不退化。用真实 `LanguageSession` 的 `ask`→worker 返回→结果写盘路径验证 `results.jsonl` model 块为 `candidates`/`detector-tracks`、可由生产 schema 读回，候选来自 N 帧 `tracked` 历史并可预览/确认；只测 `predict_one+interpret`、需运行检测/VLM、或任何不符仍启动即不满足。实现证据须含 B1/B2/B3 各自修前红、修后绿的具名 focused 测试；停点全套输出写证据文件，区分既有/新增失败。正式收据待用户在 Unity 主机零消耗预检生成，不以合成夹具宣称就绪。 | test: `tests/test_language_loop.py`（CLI/单报告/会话写结果与确认路径具名测试）；test: `tests/test_language_bridge.py`（model 配对闭集）；artifact: `docs/evidence/P1-ENG-ACQ-001-K1K3-handoff.md`「自证四项」「测试与红绿」 | K1K3 | 2026-09-29 |
| AC-18 修订 3 | 解释 AC-18/修订 2 的 Play 就绪：B4 可用人工计时 0/4 s，超确认时效记失败；B5 四类描述数字逐次从 §3.10/操作单 §6 指定来源人工或离线读取，缺数标原因，不设门、不伪报通过。每次正式尝试前须有 Unity 主机 R≥1500 且与生效配置相等的单宿主 `candidates` 收据、新通过候选和 workflow §4.5 核对；此前不启动 Play，AC-18 `NOT_RUN`。 | artifact: `docs/evidence/P1-ENG-ACQ-001-play-d1.md` §2–6；artifact: `docs/unity-test-log.md`「UT-P1-ENG-ACQ-001-D1」 | Play D1 | 2026-09-29 |

**停点与交接。**本批改变 K1 的帧/时间与收据截止绑定、K3 的后端模型决策和候选结果身份，合并 `K1K3`；未改控制命令/安全约束、数据划分/标签/对外指标或发布候选，故不触发 K2/K4/K5。实现角色只在上述授权范围改动，focused 开发、停点全套与 §4.3.1 四项自证逐 AC 证据交 `C1@K1K3`；接受角色只读核对后交新鲜上下文独立复核 `R1@K1K3`。旧 `R3@K1K2K3` 的 `passed_candidate` 只证明旧代码；新候选的 `R1@K1K3` 通过并写新 `passed_candidate` 以前，不得拿旧行做 Play D1 操作单 §3 / workflow §4.5 放行。新复核通过后再由用户在 Unity 主机做 §2 就绪与零消耗收据预检、回传，由接受角色按每次正式采集前的 §4.5 核对后交用户 Play；本轮不运行 Unity/测试、不耗额度。

open_items: AC-21_IMPLEMENTATION, K1K3_REVIEW, UNITY_MAC_K_RECEIPT, AC-18_UNITY_VERDICT

### R1@K1K3 通过轮消费（2026-09-29）

消费 `docs/reviews/P1-ENG-ACQ-001.md`「R1@K1K3」§0–7 的 `PASS_WITH_NOTES`；通过候选仅由该轮 §7 `passed_candidate` 机读行运行时解析。AC-21/B1–B3 的 K1K3 代码停点经独立复核通过（focused 324 例 OK、旧控制器 6 例红/候选绿）；本轮不重做候选核对、不跑测试、不签独立复核。K1K3-R1-1 的依据 `SCOPE_GAP` 成立：当前候选下合法报告只能由当前预检工具生成；后续改动适配器或预检工具却沿用旧报告时才可达。按 workflow §4.6 记入 `docs/implementation-status.md`「范围外已知缺陷」为 `OPEN`，归因 BC 缺失类非阻断 1；原 R1-4 `OPEN` 不变。复核 §4 的非 finding 观察不设新验收项或门值。

按复核 §3 建议，由接受角色在 `docs/evidence/P1-ENG-ACQ-001-play-d1.md` §2.7 补只读命令打印报告 `environment.git_head`，§3 要求与 Unity 主机当前 `git rev-parse HEAD` 逐字核对；不改运行时代码或既有 AC。用户在另一台 Mac 先按操作单 §2 就绪清单、§2.6 生成 R=1500 覆盖、§2.7 本机生成单宿主 `candidates` 报告/收据，原样回传全部输出（含 HEAD、工作树与报告 `git_head`）；Acceptance 再按 §3 / workflow §4.5 对照本轮新通过候选核对并记入 Unity 日志，放行后才可交用户正式 Play。当前仅为零消耗预检交接，未运行 Unity 或创建 ID；Play 前交接仍 `Consuming=no`。AC-17 样帧前置已满足，AC-18 `NOT_RUN`，复核 §6 附议不适用 `UNITY_NA`；Overall `IMPLEMENTED_REVIEWED_AWAITING_UNITY`、Lifecycle `ACTIVE`，不得记 `DONE`。

open_items: UNITY_MAC_K_RECEIPT, WORKFLOW_4_5_PREFLIGHT, AC-18_UNITY_VERDICT, K1K3-R1-1

### Play D1 本地操作页窄范围代码批次 CLARIFY（2026-09-29）

**授权、事实与边界。**依据 `docs/authorizations.md` 2026-09-29「用户授权窄范围代码批次：把 LOOP-001 带按钮本地操作页适配为 Play D1 操作页」、`docs/unity-test-log.md`「UT-P1-ENG-ACQ-001-D1」attempt 1 与「未放行的登记外 Play」。用户已提起 attempt 2；本轮只签一个 `Consuming=no` 的页面及测试批次。实现限于把已复核的 `docs/evidence/P1-ENG-LOOP-001-operator-web.py` 适配为 `docs/evidence/P1-ENG-ACQ-001-operator-web.py`，及对应 `tests/`；操作单 §4 同步由实现角色更新。可复用旧页逻辑，但不得改旧 LOOP-001 页面或 `controller/`、`Assets/`、`config/`、`tools/`、`ProjectSettings/`、桥协议与运行时控制语义。scenario/session/run ID、Unity Play、API/VLM、检测推理、YOLO 权重加载、训练 GPU·h、序列回放、下载、pip、远端访问均为 0；不借本批运行正式收据预检或创建会话。旧 Play D1 信封数值和重试仅由用户提起的限制不变。

**状态与动作合同。**以下是页面可呈现的九个 `controller.language_loop` CLI 动作的闭集；「有指令」表示已有可重用指令，`respecify` 无指令时不出现。页面在发按钮前后均核对本会话状态与绑定 token；不提供表外按钮。`TRACK_ENDED` 是 `designation.result`，**不是**状态：确认后可进入 `ACQUIRING`，成功转 `TRACKING`，`ACQUIRE_FAILED` 转 `LOST(acquire_failed)`；页面显示结果与原因，不把 `TRACK_ENDED` 当第九/第十状态，也不代人再次指定。`BOUND_COASTING` 超时转此路径时同理。

| 状态 | 可用 CLI 动作 | 条件与显示 |
|---|---|---|
| `IDLE` | `ask`, `stop`；有指令时另有 `respecify` | 尚无指针 |
| `QUERYING` | `ask`, `stop`；有指令时另有 `respecify` | 有指针时继续显示发布状态 |
| `AWAITING_CONFIRMATION` | `confirm`, `reject`, `ask`, `stop`；有指令时另有 `respecify` | `confirm` 另受预览与三项时效门约束 |
| `TRACKING` | `ask`, `verify`, `release`, `stop`；有指令时另有 `respecify` | ACQ-001 常驻模式允许跟踪中再问 |
| `SUSPECTED` | `ask`, `verify`, `confirm-lost`, `dismiss`, `stop`；有指令时另有 `respecify` | 疑点 token 绑定本视图 |
| `ACQUIRING` | `stop` | 自动转向/收养期间只观察进展，不给重复确认、释放或重播种按钮 |
| `LOST` / `REINIT_REQUIRED` | `ask`, `stop`；有指令时另有 `respecify` | `reason=backend_fatal` 时仅 `stop` |
| `TERMINAL` | 无 | 只读结束态 |

**收据、确认与预览。**页面从**本次会话启动所用**的 `candidates` K 收据读取 `host=mac`、`backend=candidates`、`model_form=detector-tracks`、`hz`、`retained_frame_count`、`k_ret`、`k_conf`、`t_ret_s`、`t_conf_s`，并与会话/生效配置及 §2.7 报告核对；来源缺失、身份或 R/hz 不符时禁确认并报告原因，不能退回旧 LOOP-001 收据或手抄数值。查询起点 + `T_ret+T_CONF_S`、首次呈现起点 + `T_CONF_S`、累计帧差 `latest−N ≤ k_ret+k_conf` 三门取先到者；查询与呈现时间从会话写盘数据读取，刷新/重绘不续期。页面倒计时只是提示，CLI 会话检查点为最终裁定；过期禁确认，不自动重发。显示本次 `result_id`、查询 `frame_id`、候选每个 index 与框；确认仅允许选择**实际显示且浏览器解码成功**的绑定预览上的 index，提交同一视图的 `result_id`，服务端重读状态、预览与 token，变更即拒绝。无图、图损坏、index 缺失/错位、跨会话图或 stale 数据均禁确认。`APPLIED` 仅表示受理，随后仍看 `designation`/状态；请求结果未知时沿用旧页 request_id/收据核对与无自动重试语义。

**页面、安全与计时。**页面只监听 `127.0.0.1`，每个动作只调用同一工作树/解释器的 `python -m controller.language_loop <action>` CLI；只读现有桥与会话文件，不直接写桥文件、请求或锁，不自动确认/自动发动作。浏览器须明确显示会话号、状态、最后读取时刻、候选与当前绑定；启动前若既有会话目录或归档表明 SID 已用，明确报「同号不可复用」并阻止启动，不能清理或覆写旧目录；页面在 T1 已启动后的本次活动会话可读取该目录，但发现既往关闭记录、第二个 `session_started` 或归档同号时立即禁动作。Play 开始墙钟由用户明确标记并写入本次操作日志；显示已过时长、剩余 180 s 与到点提示，计时依据持久化首次标记，刷新不重置；**到点仅提示用户 `stop`，不自动 stop**，不得把页面启动或会话启动时刻冒充 Play 开始。无法可靠读取起点时提示手工计时并禁显示虚假的剩余时间。所有点击、拒绝、未知结果/重试、计时标记与 CLI 回执追加到 `outputs/eng-acq/P1-ENG-ACQ-001/play-d1/<SID>/operator/operator-web.jsonl`，连同绑定视图、参数与时间；不改 `sessions/<SID>/language-session.jsonl`。操作页不生成正式 verdict，不替代 Unity 日志。

**登记外 Play 裁定。**`docs/unity-test-log.md`「未放行的登记外 Play」所记 22:15–22:21 运行未经 §3 放行且复用了 `acq-d1-1`，**作废且不计正式尝试**，不能指定为 AC-18 verdict、不能并入 attempt 1 或 attempt 2。attempt 1 仍是 22:03–22:07 的已放行用户尝试，但用户已选「不作正式 verdict」；其 `sessions/acq-d1-1/language-session.jsonl` 只读第 1–855 行为 attempt 1，第 856 行起单独属于登记外运行，任何从全文件计算的事件数/时长/分布都不得用作 attempt 1 证据。保留原文件不修剪、不重写，`frames/` 未见改写的观察不推出其余工件无混入；attempt 1 读数以用户代录和有来源边界的原始记录为准，不能分离的量标不可计算。登记外运行的 YOLO 权重加载 **实际另计 1 次**，在消耗事实中单列；它不变成正式尝试额度，也不追认未放行 Play。其 runtime 槽位已单独归档，不拿来给 attempt 2 复用。

**合同追加（原 AC 与修订保留）。**本批触及 K1 的确认时间/帧门及 K3 的候选身份/目标动作，合并 `K1K3`；实现停点按 §4.3.1 自证、全套输出入证据，先 `C2@K1K3` 只读核对再交新鲜上下文 `R2@K1K3` 独立复核。不得以旧页或旧通过候选放行 attempt 2。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-22 | 操作页文件、127.0.0.1 监听、同解释器同工作树 CLI 唯一动作出口与九态动作闭集逐态测试；特别验证 `TRACKING` 可 ask、`ACQUIRING` 仅 stop、`TRACK_ENDED→ACQUIRING→TRACKING/LOST(acquire_failed)` 只展示自动路径、所有非 `TERMINAL` 态可 stop、`backend_fatal` 仅 stop、表外动作不发 CLI。任一缺项、直接写桥/请求/锁或自动确认即不满足。 | test: `tests/test_eng_acq_operator_web.py`（状态/CLI/写入边界具名测试）；artifact: `docs/evidence/P1-ENG-ACQ-001-K1K3-operator-handoff.md` | K1K3 | 2026-09-29 |
| AC-23 | 会话 `candidates` 收据与配置身份/R/hz 绑定、三重确认时效、预览实际解码/index/result_id 绑定的修前红/修后绿具名测试；过期、刷新、错 index/图、旧 token、缺报告或不匹配收据均禁确认且不发 CLI，`APPLIED` 不误报绑定。缺任一门或手抄时效值即不满足。 | test: `tests/test_eng_acq_operator_web.py`（收据/预览/时效/旧视图具名测试）；artifact: `docs/evidence/P1-ENG-ACQ-001-K1K3-operator-handoff.md` | K1K3 | 2026-09-29 |
| AC-24 | SID 复用硬提示、180 s 仅提示且刷新不重置、操作日志逐动作/拒绝/未知结果/计时落盘、操作单 §4 页面用法与 CLI 回退均有测试或可核证据；已用 `acq-d1-1` 不能再发动作，3 min 到点不自动 stop，页面故障时 CLI 仍按 §4 可用。漏日志、自动 stop 或页面取代 §3 放行即不满足。 | test: `tests/test_eng_acq_operator_web.py`（SID/计时/日志具名测试）；artifact: `docs/evidence/P1-ENG-ACQ-001-play-d1.md` §4；artifact: `docs/evidence/P1-ENG-ACQ-001-K1K3-operator-handoff.md` | K1K3 | 2026-09-29 |
| AC-18 修订 4 | attempt 1 用户不作正式 verdict；登记外 Play 作废、不计正式尝试，其权重加载单列实际消耗，混入日志按 1–855 / 856 起分段读取。attempt 2 已由用户提起，但须本批新 `passed_candidate`、操作单 §2.7/§3 重新预检与 Acceptance 放行，使用新 SID；页面不改变 Play D1 信封及 AC-18 `NOT_RUN`。 | artifact: `docs/unity-test-log.md`「UT-P1-ENG-ACQ-001-D1」；artifact: `docs/evidence/P1-ENG-ACQ-001-play-d1.md` §2.7/§3/§4 | Play D1 | 2026-09-29 |

open_items: AC-22_IMPLEMENTATION, AC-23_IMPLEMENTATION, AC-24_IMPLEMENTATION, K1K3_OPERATOR_REVIEW, ATTEMPT_2_PREFLIGHT, AC-18_UNITY_VERDICT

### R3@K1K3 通过轮消费与 attempt 2 归因（2026-09-30）

消费 `docs/reviews/P1-ENG-ACQ-001.md`「R3@K1K3」§0–7 的 `PASS_WITH_NOTES`；通过候选只由该轮 §7 机读行运行时解析。K1K3-R2-1 已由独立复核红绿闭合，AC-24 现满足；§4 的非 finding 观察不改变合同，操作单 §4 旧编号句已改为 attempt 2 用 `acq-d1-2`。K1K3-R1-1 与 R1-4 仍为 `SCOPE_GAP`/`OPEN`；AC-18 仍 `NOT_RUN`，不以本轮离线证据签 Unity verdict 或 `DONE`。依据与归因见 `docs/implementation-status.md`「P1-ENG-ACQ-001 — R3@K1K3 通过轮消费」。

信封归因：用户已在 `docs/unity-test-log.md`「Play D1 attempt 1」提起 attempt 2；原 Play D1 信封允许用户提起的重试且不计次数，故不追加额度或用户授权。本轮只交用户在 Unity 主机重新完成操作单 §2/§2.7/§3 并回传原始输出，再由 Acceptance 按 workflow §4.5 独立裁定放行；当前不放行、不创建新 ID、不运行 Play。
