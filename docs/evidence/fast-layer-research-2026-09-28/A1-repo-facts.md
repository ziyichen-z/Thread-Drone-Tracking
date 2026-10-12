# A1 仓库事实核查：接口 A 下的快层（目标指针 + 陈旧指定框回溯解析 + 转向捕获）

- 生成：2026-09-28，只读调研；主树 `~/TetheredDroneTracking`，HEAD `6d52c27`（main）。
- 标注：`[仓库核实 file:line]` = 本次读到的代码/文档；`[仓库核实 … 只读统计]` = 本次对仓库数据的只读计数；`[估计]` = 由仓库常数推算或未能直接核实。
- 路径：无前缀者相对主树；`~full/` = `~/TetheredDroneTracking-full/`（数据根，见 F9.1）。本文件是唯一写入。

## 0. 会改变方案选择的要点（先读；细节见事实表编号）

1. **陈旧度按 20–65 帧设计，不是 7–9 帧。** 1.4–1.7 s 只是云端离线评估时延；LOOP-001 选定的闭环宿主（5060/HTTP/c2-adapter）实测 p50 4.18 s、p95 5.43 s、max 7.19 s；Mac MPS p95 8.76 s；加人工确认，指定→首条写桥实测 8–13 s（F2.3）。
2. **帧与位姿历史已经够长，缺的只是「按 frame_id 的全部 track 历史」。** Unity 盘上保留最近 128 帧（jpg + 含完整相机位姿的 json），LOOP-001 会话帧环再按 R 复制并可钉住查询帧（F1.1、F1.5、F6.3）。
3. **现状下不存在「跟踪 A 时指定 B」。** `ask` 在 TRACKING 被拒；指定期间没有活段，控制器不写任何控制，云台停在最后 look-at 点、机身 0.4 s 后 hold。今天的框陈旧只来自目标运动，不来自自运动（F2.6、F2.7）。
4. **catchup_stale 的根因是「在 N 帧 init + 回放积压 + 单批 K_pub=2/T_pub=0.4 s 门」。** 常驻检测+关联逐帧处理可以去掉回放；T_catchup 6 s 只写在合同里，代码未实现（F1.9、F1.10、F2.11）。
5. **云台协议只有 look_at_world / nadir。** Unity 侧 45° 离底限位、120°/s（5 Hz 下每帧最多 24°）、无看门狗。转向捕获可零 Unity 改动（发 B 的世界落地点），但现发布门要求同帧已写观测，否则 `orphan_control` 终止段（F4.3、F3.11）。
6. **§3.6 LOS 前馈 + 像素残差未实现。** 唯一云台指令是「当前框底中点 ∩ 水平面」落地点；世界系估计器只算不用（F4.2）。
7. **det-assoc-v1 内部已有全部 track 行，只是不外露。** `init()` 会新建 BoT-SORT（ID 重置），不能用来改绑；库 frame_id = update 调用次数；track_buffer 30 次（5 Hz ≈ 6 s）（F3.2–F3.4）。
8. **机身只会「云台接近限位后沿相机方位走」。** 无观测即 hold；25 m 高度缆绳水平可达 24.5 m；默认锚点 36 m 内只有 4 辆布局车、49.5 m 内 6 辆（F5.2–F5.5）。
9. **零 Play 离线实验原料基本齐，但全在数据根。** 609 行 C2 逐行预测在 `~full/`（sha 与证据一致）；主树 `.venv-yoloe` 无 `lap`。609 行多为 survey 扫视序列：静止目标在 t0+4.2 s 仍 OK 可见仅 64/343，需在演示路线序列上合成指定（F9.1–F9.9）。
10. **治理红线。** 接口 A 决定尚未入授权账本；「自动重指认触及定局 ④」已被接受角色写入账本；定局 ⑥ 要求播种/判丢/重指定由人决定；H 域已被 FAST-002 评过一次（F2.10、F2.11、F9.10）。

## 1. 事实表

### Q1 帧与时序

| # | 事实 | 来源 |
|---|---|---|
| F1.1 | Unity 每 `1/capture_hz` 捕获一帧（缺省 5 Hz、640×480、JPEG q85）；`frame_id = frameIndex++`，每次 Play 从 0 起；先原子写 jpg、json，再原子写 `latest.json`；发布后删除 `frame_id − R` 的旧帧（R = `retained_frame_count`，缺省 128 ≈ 25.6 s） | [仓库核实 Assets/TetheredTracking/Scripts/SensorFrameWriter.cs:102-126,159-213,215-238,285-291；config/scenario.default.json:19-26] |
| F1.2 | 每次 Unity `Update` 至多捕获一帧 → 实际帧率 = min(capture_hz, Unity 帧率)。归档 sidecar 实测帧间隔 p50：survey a4、BODY arm A/B 0.200 s；scout-1 0.199 s（其归档 scenario_config 写 capture_hz 20，768 帧只覆盖 121 s，平均约 6.3 Hz → 渲染负载下达不到配置值）；**s004-scout-4 0.050 s（20 Hz）** | [仓库核实 SensorFrameWriter.cs:144-151；~full/runtime/test-results/p1-detect-001-scout-1-closed-exchange/scenario_config.json；config/scenario.p1-scene-004.json；~full/runtime/test-results/*/frames/frame_*.json 只读统计] |
| F1.3 | 帧元数据 v3 含 frame_id、simulation_time_s、capture_unix_s、capture_monotonic_s(+clock id)、相机位置、旋转四元数、forward/right/up、VFOV/HFOV、fx/fy/cx/cy、gimbal_saturated、tether_saturated | [仓库核实 SensorFrameWriter.cs:43-86,240-283] |
| F1.4 | `TrackLoop` 内存中不留帧/位姿历史：每次 `process_available` 从盘上逐帧加载 `last+1..latest`（缺帧 → GAP 终止；latest 回退 → `frame_id_reset_or_rollback` 终止），逐帧 `tracker.update`，**只对批末帧**发观测/云台/机身 | [仓库核实 controller/track_loop.py:391-603（416-446,469,539-564）] |
| F1.5 | LOOP-001 会话帧环 `FrameSnapshotRing`：容量 = R，每帧字节只读一次并复制 JPEG 到 `<session>/frames/`；元数据（含位姿）只在内存；可 pin 在途查询帧。另有 `processed` 队列（maxlen 512）只记每帧框/ok/状态/置信度，无位姿 | [仓库核实 controller/gated_publisher.py:98-231；controller/language_loop.py:535-543,769-775,851,1240] |
| F1.6 | reanchor 的 `FrameHistory` 按采集单调时钟保留 6 s（图像 + 元数据 + SOT 框） | [仓库核实 controller/reanchor.py:256,572-622] |
| F1.7 | 冻结常数与 K 收据：hz 5、R 128、p95 5.429 s → K_ret = ceil(p95·hz)+2 = 30 帧、T_ret 6.0 s；K_conf 50 帧、T_conf 10 s；**K_pub 2 帧、T_pub = K_pub/hz = 0.4 s**；T_stall 3 s；资格 30+50+2 = 82 ≤ R−8 = 120 | [仓库核实 language_loop.py:70-94,125-138,191-197；docs/evidence/P1-ENG-LOOP-001-k-receipt.json] |
| F1.8 | 发布最终门五项：① 待发布帧 = 帧环最近一次加载帧；②③ 盘上 JPEG 与元数据与快照一致；④ `0 ≤ latest − frame_id ≤ K_pub`；⑤ 加载后本机耗时 ≤ T_pub 且采集墙钟年龄 ≤ T_stall。①④ 不过即 `catchup_stale`；任一不过 → `PUBLISH_REJECTED` + fatal → 段 finalize → `REINIT_REQUIRED(同名)` | [仓库核实 gated_publisher.py:576-622；language_loop.py:1727-1728,1750-1752] |
| F1.9 | **T_catchup = 6.0 s 只在合同里**（AC-3 修订 3：初始化后保持静音，积压 ≤ K_pub 才 unmute；自 `segment_seeded` 起 6 s 无首条 WRITTEN → `REINIT_REQUIRED(catchup_stale)`）。代码中无此常数与逻辑；C7/R8 未开即随 LOOP-001 暂停 | [仓库核实 docs/proposals/P1-ENG-LOOP-001-language-select-closed-loop-integration.md:3,833；docs/parked-status.md:104；controller/ 全文 grep 无 T_CATCHUP] |
| F1.10 | diag-loopb-6 硬停止是什么：段 1 首批追平 42 帧 0.397 s、帧差 2 → WRITTEN；段 2–4 首批积压 44/32/44 帧、每帧 20.7/19.0/39.4 ms，批末发布时 latest 已前进 5/3/8 帧 > K_pub → 门④ `catchup_stale` → finalize。接受侧归因：「单批追平压进 0.4 s/2 帧」要求每帧 ≲ 9 ms，属机制问题，不是门值或实现错误 | [仓库核实 LOOP-001 提案:825-827] |

### Q2 现在的指定路径

| # | 事实 | 来源 |
|---|---|---|
| F2.1 | VLM 看到的帧 = 查询时 `latest` 的完整 bundle N（经帧环加载；模型读帧环副本 `copy_path`）；结果包绑定 `frame_id`、`frame_sha256`、`capture_unix_s`。**接口 A 的「框 + frame_id」形态在结果包里已存在** | [仓库核实 language_loop.py:1168-1211,1213-1261,413,2172-2175] |
| F2.2 | 返回检查：`0 ≤ latest − N ≤ K_ret(30)`、墙钟 ≤ T_ret(6 s)、N 身份重核；确认检查：`latest − N ≤ K_ret + K_conf(80)`、墙钟 ≤ T_ret + T_conf、呈现后 ≤ T_conf | [仓库核实 language_loop.py:1519-1560] |
| F2.3 | 时延：5060/HTTP/c2-adapter（选定宿主）p50 4.178 s、p95 5.429 s、max 7.194 s、每 token 中位 123 ms；Mac MPS local-hf p50 4.404 s、p95 8.756 s（K_ret 46）；云端 SFT-002 评估逐行 `latency_ms` p50 1.375 s、p95 2.596 s；含人工确认，指定→首条 WRITTEN 实测 8–13 s。换算：框到手时通常旧约 21 帧（p95 约 27），播种时约 40–65 帧 | [仓库核实 docs/evidence/P1-ENG-LOOP-001-measurement-report.md:35-44,137-140；~full/outputs/eng-sft/P1-ENG-SFT-002/returned/*/predictions/eval-adapter.jsonl 只读统计；LOOP-001 提案:828]；帧数换算 [估计] |
| F2.4 | 进入跟踪：人 `confirm(index, token)` → `_seed_segment`：**每段新建 tracker 与 TrackLoop**（`create_tracker(tracker_name)`，缺省 nanotrack-v2），`loop.initialize(N, 候选框)` 在 N 的图像上 `tracker.init`；发布器创建即静音，初始化的即时发布被 `MUTED_DROPPED`，随后 `unmute`；下一 tick 从 N+1 回放到 latest，只有批末帧过门写桥 | [仓库核实 language_loop.py:1023-1056,1567-1676（1606-1611,1638,1651）；track_loop.py:336-389；gated_publisher.py:394-446] |
| F2.5 | 新目标不在画面中央时：代码不区分，框在哪就在哪 init；追平后发 look_at（框底中点地面交点），云台转过去，机身等云台接近限位才动。回放期间目标若已出画，SOT 会漂（R-B13：诊断 6 播种时红车已在右缘，云台饱和后约 3 s 框漂到看台与出租车） | [仓库核实 track_loop.py:644-676；TetheredGimbal.cs:27-46；LOOP-001 提案:828] |
| F2.6 | `ask` 只在 {IDLE, QUERYING, AWAITING_CONFIRMATION, LOST, REINIT_REQUIRED}；`respecify` 另可在 SUSPECTED（先 finalize 旧段）；TRACKING 下两者皆 `REQUEST_INVALID`，须先 `release` → LOST | [仓库核实 language_loop.py:983-1021,1106-1115] |
| F2.7 | 无活段时会话不处理帧；段 finalize 只关门并登记 retired，不写 hold/nadir。Unity 云台无超时回中，保持最后 look-at 点；机身命令 0.4 s 过期后 Hold。→ 指定期间相机静止在旧点 | [仓库核实 language_loop.py:907-914,1709-1712,1773-1808；GimbalCommandReceiver.cs:40-74,84-88；TetheredGimbal.cs:16-25；BodyCommandReceiver.cs:47-51；config/p1-m3-body-001.json:17] |
| F2.8 | SUSPECTED 触发：(a) TRACKING 中本批任一帧 raw ok=False → `tracker_failure`；(b) 角色 B 核验一次 ambiguous，或 none/drift 连续 2 次。解除只有人：`dismiss`（回 TRACKING）、`confirm_lost`（finalize → LOST）、`respecify`；跟踪器自恢复不解除 | [仓库核实 language_loop.py:1734,1754-1755,1945-2041,1076-1104] |
| F2.9 | 重播种 = `ask`/`respecify` → 新 epoch 查询 → 人确认 → 新段、新 track_id（`{session}-t{n}`），旧 id 进 `retired_track_ids` | [仓库核实 language_loop.py:1123-1166,1571,1773-1808] |
| F2.10 | 「定局 ④」逐字：「④ 丢失后**仅人工重指定**，不做任何自动重播种；」。定局 ⑥：「VLM 是辅助系统，提醒时决策主要由人负责」，「播种、判丢、重指定全由操作者决定」。定局 ③：Play 以动目标红车为主，静止布局车只验播种链路与歧义路径，Unity 零改动。§2.2：不做自动重播种/自动恢复、ReID、几何/路网搜索、L1–L4 | [仓库核实 LOOP-001 提案:13-16,100；docs/authorizations.md:1430-1446] |
| F2.11 | 接受角色 2026-09-23 已核实并入账：「自动重指认触及 2026-09-19 定局 ④」；「检测加关联从会话开始持续处理每帧，不存在回放」 | [仓库核实 docs/authorizations.md:870] |

### Q3 插件接口改造

| # | 事实 | 来源 |
|---|---|---|
| F3.1 | `TrackerPlugin` 只有 `init(image, box)->bool`、`update(image)->TrackerResult`（单框 + ok + 置信度 + 来源 + reason）、`manifest_identity`；**update 不带 frame_id** | [仓库核实 controller/trackers.py:24-49] |
| F3.2 | det-assoc-v1：`_step` 每帧拿到库输出的全部 track 行 `[x1,y1,x2,y2,track_id,score,cls,idx]`（仅已激活），`update` 只挑绑定 id；`init` 每次**新建关联器**并调一次 update，绑定 = 与初始化框 IoU 最大且 ≥ 0.50；绑定 id 在 lost 池 → `bound_track_unmatched`，被移除 → `bound_track_removed`，从不改绑；`_bound_id is None` 时 update 直接返回、不跑检测 | [仓库核实 controller/det_assoc_tracker.py:6-12,31,213-261] |
| F3.3 | 库状态可导出：实例有 `tracked_stracks / lost_stracks / removed_stracks`（removed 截最近 1000）与 `frame_id`（= update 调用数）；STrack 有 track_id、state、KF mean/covariance、start_frame/end_frame、score、cls、idx。插件已暴露 `library_frame_id`、`bound_track_id` | [仓库核实 .venv-yoloe/lib/python3.12/site-packages/ultralytics/trackers/byte_tracker.py:255-259,265-300,482-491；utils/stracks.py:24,54-55；det_assoc_tracker.py:263-269] |
| F3.4 | 冻结关联参数：BoT-SORT、GMC `sparseOptFlow`、match 0.7、**track_buffer 30（按调用计，5 Hz ≈ 6 s；间隔 ≥ 31 次必为新 ID）**、new_track_thresh 0.25、with_reid false；检测 conf 0.25、imgsz 640、device mps/cpu | [仓库核实 config/det-assoc-v1.models.json:2-33；docs/proposals/P1-ENG-FAST-001-fast-layer-replacement-probe.md:47] |
| F3.5 | 库钩子 `_pre_first_associate`：Kalman 预测后、首轮关联前施加 GMC 的 2×3 warp（仅 img 非空；失败退单位阵）→ 子类可注入外部（如由位姿算的）warp | [仓库核实 byte_tracker.py:352-362] |
| F3.6 | `tracking_observation.json` = `tethered-tracking-observation/v1` {frame_id, track_id, bbox_xywh_norm, confidence}；Unity 只读单观测，README 声明观测不带状态。**只发布被指向的 track 则 schema 可不变** | [仓库核实 controller/tracking_entry.py:45-58；TrackingObservationReceiver.cs:42-60,103-118；runtime/README.md:31-40] |
| F3.7 | CoverageEvaluator 身份判定 = `observation.track_id == "target-0"`，且只有运动红车有真值 → 静止车 B 的指针跟踪在 metrics.json 中一律记 incorrect（LOOP-001 的 track_id 形如 `{session}-t{n}`，本就对不上；该项声明不读 metrics） | [仓库核实 CoverageEvaluator.cs:793-831；config/scenario.default.json:28；language_loop.py:1571；LOOP-001 提案:391] |
| F3.8 | 语言桥请求只有 9 个动作，信封字段 session_id/request_id/action/instruction/candidate_index/token，**无「框 + frame_id」字段**；结果/状态闭集中没有 SWITCHED/NO_MATCH/AMBIGUOUS/TRACK_DIED 类值 | [仓库核实 controller/language_bridge.py:51-61,74-84,107-147,432-445] |
| F3.9 | 改造触点（最小集合）：`trackers.py` 协议与结果类型；`det_assoc_tracker.py` 的 `_step`/`update`/新 `designate`/指针；`track_loop.py:469` 调用处需传 frame_id（或调用方记历史）；`language_loop.py` 的 `_seed_segment`（每段新建 tracker）、`_advance_segment`（无段不处理帧）、`_ASK_STATES`、`_action_confirm`；`gated_publisher.py` 的 `_derived` 同帧关联规则；`language_bridge.py` 闭集与 `runtime/README.md`；测试 `tests/test_{trackers,det_assoc_tracker,det_assoc_carrier,track_loop,language_loop,language_bridge}.py` | [仓库核实 上列 file:line] |
| F3.10 | 停点定义：K1 帧/控制协议及坐标与时间语义；K2 安全约束与控制命令；K3 模型决策、目标身份与重播种；K4 划分/标签/对外指标；K5 对外发布；关联触发可合并一次停点。FAST-002 自述「K3 = 插件绑定/丢失/不改绑决策，不触发 K1/K2/K5」 | [仓库核实 docs/engineering-workflow.md:79-91；docs/proposals/P1-ENG-FAST-002-in-domain-detector-association-fast-layer.md:282] |
| F3.11 | `look_at`/`body_command`（速度）只在同帧观测已 WRITTEN 时放行，否则 `PUBLISH_REJECTED(orphan_control)` 并 fatal；`hold_body`/`set_nadir` 永远透传；hold 走不绑帧的安全通道 | [仓库核实 gated_publisher.py:413-419,453-525] |

### Q4 云台控制

| # | 事实 | 来源 |
|---|---|---|
| F4.1 | 设计 §3.6：指向 Kalman 预测位置（前馈）+ 有检测时像素残差小增益修正；估计传播 + 云台角速率控制 50 Hz | [仓库核实 docs/phase1-single-drone-design.md:771-781] |
| F4.2 | **未实现**：唯一云台指令 = `_publish_latest` 对批末帧框「框底中点射线 ∩ 显式水平面」发 `look_at_world`（M2a 无滤波 LOS 占位）；无预测前馈、无像素残差、无 50 Hz 回路。`WorldEstimateFilter` 只在接机身时运行并记日志，任何决策都不读 | [仓库核实 track_loop.py:644-676,738-742；controller/geolocate.py:57-114（88-89）；controller/world_estimate.py:17-24；设计:760-763] |
| F4.3 | `gimbal_command.json` = {mode: look_at_world, target_world_m{x,y,z}} 或 {mode: nadir}，**不是角度/角速度**。Unity 20 Hz 轮询；过期包忽略但不回中；离底角 = min(请求, 45°)、偏航朝目标、无横滚；LateUpdate 以 120°/s `RotateTowards`；请求 > 45.1° 置 Saturated | [仓库核实 controller/gimbal_entry.py:12-31；GimbalCommandReceiver.cs:20-74；TetheredGimbal.cs:9-46；config/scenario.default.json:15-18] |
| F4.4 | 相机：VFOV 60°、640×480、HFOV ≈ 75.18°、fx = fy ≈ 415.69 px、cx 320、cy 240；相机挂机体、零偏移，姿态以世界系绝对设置（机体偏航不影响视向） | [仓库核实 SensorFrameWriter.cs:252-279；TetheredScenarioBootstrap.cs:198-209；TetheredGimbal.cs:5-6；language_loop.py:2374-2379] |
| F4.5 | 自运动量可得：每帧元数据给出采集时刻相机实际位置与姿态，相邻帧之差就是实际自运动（比指令量更准）；控制器知道自己发过的 look-at 点（运行日志 `look_at_world_m`），Unity 回转规律确定 | [仓库核实 SensorFrameWriter.cs:250-270；track_loop.py:904] |
| F4.6 | 量级：120°/s ÷ 5 Hz = 每帧最多 24°，约等于图像平移 185 px [估计]。归档实测每帧旋转：survey a4 p90 8.1°、max 22.0°，21 帧窗 p50 36°；演示路线 scout-1 p90 0.78°、max 3.9°；BODY arm A t3、arm B t5 各一段 max 1.7°/1.1° | [仓库核实 ~full/runtime/test-results/*/frames/frame_*.json 只读统计] |

### Q5 机身规划（BODY-001 阈值规划器）

| # | 事实 | 来源 |
|---|---|---|
| F5.1 | 输入 `PlatformState`（frame_id、采集单调时钟、相机位置、camera_forward、两饱和旗）+ `WorldEstimate`（必须非空，但阈值策略不读）；输出 hold 或 velocity_world（vy = 0），有效期 2/hz = 0.4 s | [仓库核实 controller/body_planner.py:71-176,387-447；config/p1-m3-body-001.json:13-19] |
| F5.2 | margin = 45° − 已施加离底角；margin < 10°（离底 > 35°）触发，> 20°（< 25°）释放；方向 = 相机水平方位；4 m/s；发速度前做锚点→候选位置缆绳走廊检查（779 棱柱、半径 1.0 m），相交就按 0.05 m 缩短，不可行则 hold；不读饱和旗与估计器；参数冻结（sha 锁） | [仓库核实 body_planner.py:325-461；config/p1-m3-body-001.json:5-26；docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md:264-321] |
| F5.3 | 只在批末帧、且该帧跟踪 ok 时 decide；**无观测 → hold**；LOOP-001 中速度须绑同帧 WRITTEN 观测 | [仓库核实 track_loop.py:564,803-813；gated_publisher.py:453-497] |
| F5.4 | Unity 运动学 plant：速度 ≤ 4 m/s、加速度 4 m/s²、高度 8–32 m、缆长 35 m 球约束（越界夹回并置 TetherSaturated）；缺省悬停 25 m，锚点 (132, 0.2, 117) | [仓库核实 TetheredDronePlant.cs:8-62；config/scenario.default.json:6-14] |
| F5.5 | 远目标：25 m 高度缆绳水平可达 √(35²−25²) = 24.5 m；离底 25° 对应水平 11.7 m、45° 对应 25 m → 自锚点「可居中不饱和」半径约 36 m、「45° 饱和居中」约 49.5 m；更远只能在画内不居中（45° 时画幅远边离底 75°，地面约 93 m）[估计]。默认场景布局车（AABB 中心）距锚点水平距离：≤24.5 m 2 辆、≤36.2 m 4、≤49.5 m 6、≤70 m 19、≤93 m 39 | [估计；布局数 仓库核实 ~full/runtime/dist-data/layout/attempt-2/layout.json 只读统计] |
| F5.6 | 新目标在画面边缘时：云台先转（90° 约 0.75 s），离底 > 35° 后机身才走（走满 24.5 m 约 6–7 s）；转向途中跟踪一丢即 hold [估计，由 F4.3/F5.2/F5.3 推出] | [估计] |

### Q6 世界系

| # | 事实 | 来源 |
|---|---|---|
| F6.1 | `box_ground_intersection(box, metadata, ground_plane_y_m, max_distance)` 需要该帧 width/height、fx/fy/cx/cy、相机位置与 right/up/forward；取框底边中点；水平面 y 必须显式（M2a 规则：不得从路线真值推导）；射线朝上/超距 → `GeometryRejected` | [仓库核实 geolocate.py:57-114；设计:760-763] |
| F6.2 | 地面高度：路线 y = 0.2；接机身时 `ground_plane_y_m` 必须等于路线 y，否则拒绝启动；language_loop CLI 缺省 0.0。布局车底面 y 中位 −0.004、车高 2.2–4.2 m → 斜视下框底中点不是触地点，误差可到米级 [估计] | [仓库核实 track_loop.py:1178-1186；language_loop.py:649,2660；layout.json 只读统计] |
| F6.3 | **旧帧 t0 上的框可以算世界点**，前提是拿到 t0 元数据：盘上保留最近 128 帧；LOOP-001 查询帧 N 在帧环中被 pin，`QuerySnapshot` 持有其完整元数据 | [仓库核实 SensorFrameWriter.cs:212；gated_publisher.py:98-231；language_loop.py:300-309,1240] |
| F6.4 | `reanchor.world_los(box, metadata)`：由框中心算世界系视线单位向量，并校验基向量与四元数一致；不需要地平面假设 | [仓库核实 reanchor.py:327-393] |
| F6.5 | `WorldEstimateFilter`：CV 模型 `[x,z,vx,vz]`，测量协方差由像素/姿态/地面高三源传播；LOOP-001 每段深拷贝新实例；输出未被云台/规划器消费 | [仓库核实 world_estimate.py:1-25,194；language_loop.py:675-686] |

### Q7 再锚定（DETECT-001）

| # | 事实 | 来源 |
|---|---|---|
| F7.1 | 机制：每 2 s 一轮 YOLOE 视觉提示候选 + DINOv2 ViT-S/14 外观余弦（≥ 0.5、歧义 margin 0.1）+ 世界系视线运动门（与锚 LOS 夹角 ≤ 0.1 + 0.5 rad/s·dt）；AGREE（与 SOT IoU ≥ 0.3）刷新锚；连续 2 轮一致 DISAGREE 或 SOT 已丢 → 在 6 s 帧史中「源帧 init + 回放到帧头」（源年龄 ≤ 2 s、追平 ≤ 2 s），下一次 update 前原子替换 tracker；连续 3 次失败 fail-closed | [仓库核实 reanchor.py:241-265,462-562,572-693；controller/reanchor_runtime.py:84-306] |
| F7.2 | 冻结约束：参数逐项与冻结值比对，不符即拒绝；tracker 工厂必须是 nanotrack-v2；`maximum_result_age_s` = 2 s → 4–13 s 旧的 VLM 框原样进去会被判 stale | [仓库核实 reanchor.py:219-227,241-265；reanchor_runtime.py:98-108] |
| F7.3 | 证据与暂停：Lifecycle `PAUSED`、Overall `QUALIFICATION_PASSED_ACCEPTANCE4_OPEN`；qual-3 检测节奏 75/75，决策 AGREE 36 / TENTATIVE 19 / NO_CANDIDATE 20，**零 REANCHOR**；验收 4（困难场景背景锁定打破）从未运行；scout-1 ≥ 65 m oracle 指向召回 0/45、DINOv2 目标余弦中位 0.398。仓库未见单列的暂停理由（PAUSED 标记随 COORD-012 的 Lifecycle 列出现）[不确定] | [仓库核实 docs/current-status.md:67；docs/parked-status.md:75；FAST-001 提案:30-31；docs/implementation-status.md:1695-1707] |
| F7.4 | 可复用：`world_los`、`angular_distance`、`box_iou`、运动门逻辑、`FrameHistory`、`replay_tracker`、`SingleFlightWorker`、原子替换模式。不宜原样复用：YOLOE 远距召回与 DINOv2 区分度差、2 s 年龄门、NanoTrack 绑定。用作「转向到位后的重捕」需换在域检测器候选，并先解决定局 ④（F2.11） | [仓库核实 reanchor.py:358-414,462-704] |

### Q8 场景与注入

| # | 事实 | 来源 |
|---|---|---|
| F8.1 | `track_loop` CLI 有 `--init-frame N --init-box X Y W H --tracker {csrt,nanotrack-v2,det-assoc-v1} --body-policy threshold`：在保留帧 N 上用人给框冷启动；一个进程只能 init 一次 | [仓库核实 track_loop.py:1557-1561,1580-1586,1617-1646,336-338] |
| F8.2 | `replay` 后端按帧 JPEG sha 查表回放 SFT-002 预测，只能对上归档帧；`ScriptedAdapter` 只是测试替身（CLI 选不到）；`replay-demo` 的 `FixtureFramePublisher` 发布夹具帧（固定正下方位姿，不是真实 sidecar） | [仓库核实 controller/language_selector.py:231-389；language_loop.py:2321-2409,2523-2553；controller/language_demo.py:1-20] |
| F8.3 | → **现在没有「不经 VLM、在运行中的会话里注入一次 (box, frame_id)」的入口**；最近的替代是 track_loop 冷启动（中途切换要重启进程，期间云台停在旧点） | [仓库核实 同 F8.1/F8.2/F3.8] |
| F8.4 | 真值隔离：Unity 真值只进 CoverageEvaluator；注入框若由布局/真值投影生成即违规 → 只能人框选（RATE 研究有「预览叠框 → 人确认」先例）或人从检测候选中选 | [仓库核实 CLAUDE.md；runtime/README.md:60-62；tools/run_rate_study.py:285-351] |
| F8.5 | 默认场景：布局工件默认分区 vehicle 组 101 个实例（FAST-002 文档写「93 辆目录车」，口径差异未核 [不确定]）；运动目标 = 红色双立方体，2 m/s 绕 213 m 矩形环（106.5 s 一圈）；有 1 辆标记为干扰的 Taxi 被移到锚点旁 | [仓库核实 layout.json 只读统计；FAST-002 提案:83；LOOP-001 提案:63；config/scenario.default.json:27-49；FAST-001 提案:34] |
| F8.6 | 演示路线上的静止车：跟红车的归档中出现过 OK 可见的不同静止车 arm A 3 辆、arm B 2 辆、scout-1 14 辆（scout-1 高频：Taxi(2) 287 帧、Container_color01 247、SUV_color01(4) 225）；固定朝下时红车停留窗 sim_t 0–12、99–118、206–225 s | [仓库核实 ~full/outputs/eng-fast/P1-ENG-FAST-001/cache/catalog-index.jsonl.gz 只读统计；LOOP-001 提案:828] |
| F8.7 | 静止车 B 只能离线评：S3 目录由 sidecar 相机字节 + 冻结布局 AABB 投影 + 遮挡近似离线算出，可对任何保留下来的 Play 帧复算；但 Unity 只留 128 帧，需要另行归档 | [仓库核实 tools/dist_data/project_boxes.py:1-40；SensorFrameWriter.cs:212] |
| F8.8 | 在域检测器两类：0 = vehicle（全部目录车一类）、1 = target（红立方体）；H 域车辆召回 S/M/L 0.949/0.906/0.952 → 任何静止车都能成为 track，指针可以指向它 | [仓库核实 config/det-assoc-v1.models.json:19-22；docs/evidence/P1-ENG-FAST-002-report.md:40] |

### Q9 离线实验资产

| # | 事实 | 来源 |
|---|---|---|
| F9.1 | **主树 `runtime/` 只有 README.md，`outputs/` 只有 `eng-det`**；帧、sidecar、S3 目录、SFT-002 预测、FAST-001 缓存都在 `~full/`；`tools/eng_det` 缺省 `DATA_ROOT = ~/TetheredDroneTracking-full`（可用 `ENG_DET_DATA_ROOT` 改），并把两处 runtime 设为只读保护 | [仓库核实 本次 ls；tools/eng_det/common.py:4,26-29] |
| F9.2 | S3 目录 `~full/runtime/dist-data/frames_catalog/attempt-2`（manifest + 151 分片，43,535 行）：每行 frame_id（仓库相对 jpg 路径）、family、objects[779]{object_id, status ∈ {OK, TOO_SMALL, TRUNCATED, EXCLUDED_OCCLUDED, NOT_IN_VIEW, PHANTOM}, visible_norm_xywh, visible_px, amodal_px, camera_depth_m, referable…}、`target_blocker_px`（运动目标框）、station_bin；**行内无仿真时间** | [仓库核实 frames_catalog.json 与 shards/00000.ndjson.gz 只读；FAST-001 提案:40] |
| F9.3 | 紧凑索引 `~full/outputs/eng-fast/P1-ENG-FAST-001/cache/catalog-index.jsonl.gz`（43,535 行；`vehicles[]` 仅 OK 车 {object_id, box, class_word, color_word, depth_m, referable} + `dynamic`）；时间 `catalog-sim-times.jsonl.gz`（43,535 行 {frame_id, t}）；每帧 sidecar 另有完整位姿 | [仓库核实 只读；FAST-002 提案:45] |
| F9.4 | 冻结 YOLO11n 检测缓存（conf 0.25、MPS）在主树：`outputs/eng-det/dets/frozen-H.jsonl.gz` 16,855 帧（survey a3/a4/a6/a9 各 2.8–2.9k 连续无缺、s004 scout-3/scout-4 各约 2.4k、m3-armB 5×128）；`frozen-B` 1,664 帧（scout-1 768 + arm A 7×128）；`frozen-V` 3,168 帧（a7）；每帧 dets = [x, y, w, h(归一), conf, cls] | [仓库核实 只读统计；FAST-002 报告:12-20] |
| F9.5 | 关联回放函数现成：`tools/eng_fast/replay.run_sequence` 每帧恰一次 update，返回**每帧全部输出行**；`tools/eng_det/evaluate.tracker_for/replay_piece` 按冻结参数建 BoT-SORT（GMC 读图）；`bind` 用真值 IoU ≥ 0.3 逐帧绑定（只用于评分）。已记债 R1-2：`window_outcome` 在大间隔序列上可能零证据判 KEPT | [仓库核实 tools/eng_fast/replay.py:103-139；tools/eng_det/evaluate.py:322-370；FAST-002 提案:39] |
| F9.6 | `lap`：主树 `.venv-yoloe` 没有；`~full/.venv-yoloe` 有 lap 0.5.13。FAST-002 按「pip 0」只读调用数据根解释器跑 BoT-SORT | [仓库核实 本次 ls；docs/evidence/P1-ENG-FAST-002-ledger.json] |
| F9.7 | SFT-002 逐行预测：`docs/evidence/P1-ENG-SFT-002-eval-*.json` 只有汇总（metrics、405 行 v1 诊断，无预测框）；主树 outputs 没有；**在 `~full/outputs/eng-sft/P1-ENG-SFT-002/returned/sft-20260918T223245Z-bd1f5ebb/predictions/eval-adapter.jsonl`（C2，609 行）与 `…T202551Z…/zero-shot.jsonl`（base）**，sha256 与 eval-summary 记录一致（0ccb4f1e… / f6e31c38…）；字段 row_id、boxes_1000、parsed{status, bbox_2d}、status_pred、raw_output、latency_ms、finish_reason。金标 `data/eval.jsonl`（sha 5d86013f…，与 eval-manifest 一致）：frame_id、family、frame_index、target_object_ids、gold_boxes_norm_xywh、gold_state、group、stratum | [仓库核实 只读 sha 比对；docs/evidence/P1-ENG-SFT-002-eval-summary.json；-eval-manifest.json] |
| F9.8 | 609 行构成：survey a3/a4/a6/a9 516 行、s004-scout 70、m3-armB 23；以红车为目标 58 行（在动的只有 m3-armB 6 行 + s004-scout 8 行；survey 场景红车速度 0）；C2 预测 unique 442 / ambiguous 46 / none 121；金标与预测都 unique 的 347 行中框 IoU ≥ 0.5 占 87%、≥ 0.3 占 90.5%、中位 0.86 | [仓库核实 只读统计] |
| F9.9 | 陈旧后仍可见（391 行 unique 单目标；按仿真时间取 t0+Δ 之后首帧，目标在索引中为 OK）：静止目标 Δ = 1.4 s 222/344、4.2 s 64/343、5.4 s 46/343、10 s 31/342；红车 31/46、28/46、22/46、24/44。原因：survey 是扫视采集（每视角停 1.2 s） | [仓库核实 只读统计；config/p1-vlm-survey-plans/p1-vlm-survey-a4-p1-c1/plan.json] |
| F9.10 | H 域已被 FAST-002 评过一次（「本项内不再训练、不再评 H」），其 §6.2(iii) 要求新项「重新定义或声明已消耗」；609 行评估帧全部落在 H 保留帧；scout-1、m3-armA 在训练原子内（B 表读数偏乐观） | [仓库核实 FAST-002 报告:6,10,20,86] |
| F9.11 | FAST-002 关联读数只针对红车：13 s 保持率 scout-1 0.815、m3-armA 0.788、H 合并 0.411（ID 切换 1,593、超 buffer 丢失 2,349，无 ReID）；一次绑定不改绑口径 H HIT 0.414、首次移除中位 17.0 s，scout-1 8.0 s 后移除。**静止车的 track 连续性没有任何读数** | [仓库核实 FAST-002 报告:48-61] |
| F9.12 | 时延：det-assoc-v1 在 Mac 上 update p50/p95 CPU 43.7/48.4 ms、MPS 19.8/31.9 ms（单进程离线）→ 5 Hz 下常驻逐帧处理有余量 | [仓库核实 FAST-002 报告:63-65] |

## 2. 三层任务的集成点（改哪里、动哪个停点）

### 层 1：保持居中追踪
- **感知**：换 det-assoc-v1 → 改 `SessionConfig.tracker_name` 缺省与 `run --tracker`（language_loop.py:647, CLI），并改 LOOP-001 合同 §1「NanoTrack 承担跟踪」。FAST-002 阶段 1 为 `QUALIFICATION_GATE_NOT_MET`（G-1 L 格、G-5、G-6），`C1@K3K4` 已退回（current-status 当前义务段）→ 换插件本身是 LOOP-001 的 K3。
- **居中控制**：把 `track_loop._publish_latest`（644-676）的 look-at 点从「框底中点落地点」改为「估计器预测 + 像素残差修正」；估计器已在 `_body_step` 运行（755-800）。只动 Python、Unity 零改动 → **K2**（控制命令）；若改时间对齐/坐标口径另加 **K1**。
- **要角度/角速率模式**：改 `GimbalCommandReceiver.cs`/`TetheredGimbal.cs` 与协议 → K1 + K2 + Unity 实测（违背 LOOP-001「Unity 零改动」定局 ③ 的延续假设）。
- **机身**：BODY-001 阈值规划器参数 sha 冻结、项目已关闭且措辞冻结；换策略需新提案 → K2。

### 层 2：重新指定 → 目标迁移 → 转向捕获
1. **常驻多目标关联（去掉回放）**：插件需要「无绑定也逐帧 `_step`」模式（现 245-247 在无绑定时直接返回）；会话需在 IDLE/QUERYING/AWAITING 也逐帧处理（现 `_advance_segment` 无段即返回；`_seed_segment` 每段新建 tracker）→ **K1**（帧处理时间语义）+ **K3**。
2. **按传感器 frame_id 的全 track 历史**：插件或调用方加环形历史，键为 `bundle.frame_id`（`track_loop.py:469` 现只传图像）；深度 ≥ K_ret（30）或 K_ret+K_conf（80），≤ R = 128 → **K1**。
3. **`designate(box, frame_id)` 闭集**：查 t0 历史 → IoU 匹配（沿用 0.50 或另定）→ 歧义 margin → 查该 id 现状（tracked / lost / 已移除）→ SWITCHED / NO_MATCH / AMBIGUOUS / TRACK_DIED；结果进 `language_result`/`tracker_state` 闭集与 `runtime/README.md` → **K3 + K1**。
4. **指针切换**：只改绑定 id，**不能走 `init()`**（会重建关联器、ID 从 1 重来）；重定义段、track_id、`retired_track_ids`；`ask`/`respecify` 在 TRACKING 放行 → **K3**（状态机）。B 若在当前帧可见，切换后现有「观测 + look_at」路径下一帧就会把云台转向 B，不需要新指令。
5. **转向捕获（B 已不在画内时）**：由 t0 元数据 + 框算 B 的落地点（`geolocate`）或视线（`world_los`），发 `look_at(B)`；但 `GatedPublisher._derived` 要求同帧 WRITTEN 观测，否则 `orphan_control` 终止段 → 需要新的「无观测转向」通道及其安全语义（超时、次数、回 hold）→ **K2 + K1**。机身：阈值规划器无观测即 hold、方向取相机方位 → B 在约 36–50 m 以外需新策略或接受饱和 → **K2**。
6. **自运动**：常驻关联下，陈旧解析 = 查 t0 历史里的 track id；相机转动由 GMC（或经 `_pre_first_associate` 注入位姿 warp）处理；静止车可再用世界点做一致性校验。
7. **发布门**：常驻后「静音播种 + 单批追平」不再需要，但 K_pub/T_pub 最终门与转向期（无观测）的写入规则要重写 → **K1**。
8. **证据**：若把离线解析成功率作为对外指标报告 → **K4**。建议 K1+K2+K3 合并一个候选走一次停点（workflow 允许合并）。
9. **Unity 诊断的零新代码起点**：`track_loop --init-frame/--init-box --tracker det-assoc-v1 --body-policy threshold` + 人框选静止车 B，可先验证「偏心目标 → 云台转向 → 机身跟随」链路；做不到中途切换（F8.1、F8.3），且静止车成败只能离线复算或目检（F3.7、F8.7）；在 LOOP-001 范围内用静止车做主演示与定局 ③ 冲突（F2.10）。

### 层 3：Jetson 部署
- 设计 §8 与 workflow §9：必须独立立项，写明设备与额度并获授权；桌面量化不能替代板端；仓库内没有任何 TensorRT/Jetson 实测 [仓库核实 设计:1089-1104；engineering-workflow.md:148-156；authorizations.md:870]。
- 可移植性：插件 `device_policy` 只允许 mps/cpu（无 cuda），需扩规格或导出 TensorRT → 插件身份变更 **K3**，报时延指标 **K4** [仓库核实 det_assoc_tracker.py:96-98,136-146]。
- BoT-SORT 的 GMC 是 CPU 上的 OpenCV 光流，板端开销未知；VLM 在 5060 上 p50 4.18 s，板端未测 [估计]。

## 3. 尚不存在的东西

1. 按传感器 frame_id 索引的全 track 历史（插件与 TrackLoop 都没有；只有离线工具的临时输出）。
2. `designate(box, frame_id)`、闭集结果、指针切换 API、插件的「无绑定常驻」模式。
3. 跟踪中重指定的状态机分支；带「框 + frame_id」的请求字段或脚本化注入入口。
4. 无同帧观测的「转向」控制通道及其安全语义（超时、回中、次数上限）。
5. §3.6 的 LOS 预测前馈 + 像素残差、50 Hz 云台回路、角度/角速率云台模式。
6. 基于相机位姿的自运动补偿（现只有库内图像 GMC）。
7. AC-3 修订 3 / T_catchup 的代码。
8. 静止车的在线评估通道（CoverageEvaluator 只认 `target-0`）；超过 128 帧的 Play 帧归档。
9. 静止车 track 连续性读数；陈旧解析离线实验的线束、判据与报告格式。
10. 板端（Jetson）实测。
11. 用户 2026-09-28「接口 A」决定的授权账本条目（账本没有的授权视为未发生）。

## 4. 风险与未知

1. **时延口径决定设计**：按 1.4 s、4.2/5.4 s（HTTP）还是 8–13 s（含人工确认）设计，决定历史深度与 TRACK_DIED 比例；5060 的 max 7.19 s 已超过 T_ret 6 s（报告自述不保证每次都在 K 窗内）。现 `K_ret` 规则会拒掉更旧的结果，放宽是 K1 合同变更。
2. **定局 ④⑥**：若「指定 → 切换 → 转向 → 重捕」全自动、不经人确认，是否违背 ⑥；转向途中丢失后自动重捕是否算 ④ 的「自动重播种」。需用户裁定并入账，否则提案会在接受环节被退。
3. **ID 连续性**：无 ReID；H 13 s 保持率 0.411；track_buffer 30 次 ≈ 6 s，若 B 在 t0 后离画超过 6 s，t0 的 id 必然已死 → TRACK_DIED 会常见；兜底要靠世界点或外观，而 DINOv2 对远小目标区分度差（F7.3）。
4. **大幅自运动**：每帧最多 24° 旋转，`sparseOptFlow` GMC 在大旋转下是否可靠未知 [估计]；survey 序列（每帧 max 22°）可作压力测试。
5. **检测器局限**：H 目标 L 格 0.731（s004 近距离框重叠不足）；本场景专用、换目标外观需重训，不满足设计 §3「换目标不重训练」（设计:399；FAST-002 报告:118）。
6. **世界点误差**：框底中点 ≠ 触地点，车高 2.2–4.2 m、斜视 → 米级；运动红车在 4–13 s 内移动 8–26 m [估计]。
7. **离线数据代表性**：survey 为脚本扫视、演示路线序列短（128 帧窗）、s004 为 20 Hz 需下采样、B 族在训练原子内偏乐观、H 已被消耗一次；609 行在 Δ ≥ 4 s 时可用样本少（F9.9）。
8. **工作区**：主树缺数据与 `lap`；实验需以数据根只读运行（FAST-002 先例），写入落 `outputs/` 新目录并入 `.gitignore`（已有 eng-* 先例）。
9. **共享冻结代码**：`track_loop.py` 同时服务 RATE/DETECT/BODY 协议，LOOP-001 把其批处理视为冻结；改它会波及既有协议与测试。
10. **在途项次序**：FAST-002 在 `C1@K3K4` 退回、IR-4 待用户，「不改绑」是其 K3 合同；LOOP-001 暂停中（续跑/收口待用户），其 F3 债在改 `LanguageWorker` 时需承接（docs/implementation-status.md:32）。
11. **Unity 诊断难判成败**：层 2 在 Play 中指向静止车时 metrics.json 不可用，需离线复算（F8.7）或人工目检；注入框不得来自真值（F8.4）。
12. **口径未核**：布局车 101 vs 文档 93；DETECT-001 暂停的正式理由未见单列。
