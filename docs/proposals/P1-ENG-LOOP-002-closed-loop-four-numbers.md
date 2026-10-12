# P1-ENG-LOOP-002 — 闭环接入与四类数字首测：语言指定 → 指针快层 → 机身跟随（VLM 在环，Jetson 单主臂、5060 不启用）

Status: ACCEPTED（D4；engineering-v1；诊断P1核清完成，DIAG:RETRY:1一次已用尽；STOP3板端释放UNKNOWN、红车持续跟随问题待定位；OSB-R1-1交实现后置应用；Overall REVIEW_PASSED，无UNITY_NA/DONE）
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（D1：Claude Code `/fable`，Fable 5.1，Mac mini，用户直接开会话；D2：工程轨道 Opus 池，supervisor 派发子代理，Dispatch-Id `P1-ENG-LOOP-002-D2-20261006T205029Z-9519`，Unity 主机 MacBook Air；D3：同池同机，Dispatch-Id `P1-ENG-LOOP-002-D3-20261006T215137Z-d9fe`；D4：同池同机，Dispatch-Id `P1-ENG-LOOP-002-D4-20261006T224524Z-ebfd`）
Created: 2026-10-06
Last updated: 2026-10-08

> **来历**：用户 2026-10-06 认可「把三件已复核部件接成闭环并首次产出四类数字」为下一工作项，并以选项题选定「Jetson 为主，5060 备用」为第一轮 VLM 宿主；逐字见 `docs/authorizations.md` 2026-10-06「P1-ENG-LOOP-002 — 用户点名起草闭环接入提案、选 VLM 宿主 Jetson 为主、暂停 COORD-018 交接至 10-09（构思会话代录）」（方向层，不签发额度）。
> **承接**：`P1-ENG-ACQ-001` 依 D1 裁定 (c) **保留 `PAUSED` / `IMPLEMENTED_REVIEWED_AWAITING_UNITY`**，本项只引用其部件与未闭义务，不恢复、不收口、不改其门值、verdict、AC-18 `NOT_RUN`、attempt 2 非 verdict 或旧余额；`P1-ENG-FRAME-001`（`DONE`/`ENDED`）；`P1-ENG-JET-001` 板上 C2 Q4 产物仅为诊断件（§2.5 H-12）。
> **当前增量入口（2026-10-08）**：本提案「诊断窗口落实」§1–4及「绑定R1通过消费」§1–5/最新核对表；合同仍为「诊断绑定方案答复」§1–4/AC-10修订9/AC-13修订2。「R1@OpsDiagBindK1K2」PASS已消费，代码机读前提齐、本人新窗口已落实，现场与执行树门仍待；OSB-R1-1补丁后置，正式未放行。旧全套不绿、偏差/UNKNOWN及债保持。
> **执行授权只取账本**：完整B-main签发/N-3/三文件效力见「Mac mini四题答复落实」§1–4；六题选择及AC修订、事实/机器/验证边界见「R3六题答复落实」§1–4。操作流程现行增量合同为「OPS九题答复落实」§1–6：网页取代按键窗、发令前人工可见性确认/N-5保持、板服务执行人按已签分工由代理/脚本前台监督；新验证额度及诊断前提现行见「OPS验证额度落实与IR裁定」§1–5，环境基线/本人保真与IR7/8现行裁定见「OPS基线与IR78裁定」§1–5。Air原子范围未用余额作废、mini只读补核SSH1/1已结束；原R4与新K1K3 R1通过只覆盖旧范围，G1–G5/AC-18未闭。诊断收尾/偏差/UNKNOWN仍见「第四次诊断核清与操作流程修改路线」§1–2，四次许可均耗尽，不消费正式余额。
> **D2 只读口径**：本轮只对 Unity 主机磁盘已有文件做只读统计（零模型、零写 `runtime/`、零 SSH、零下载）；拿不到的标「未核」及核实阶段。D2 新写内容不手抄 HEAD/工件 sha/run 目录名（AGENTS「可派生标识禁手写」），一律写解析来源。
> **D3 同口径**：另对两份既有归档做只读的静止车投影与摘要链统计（系统 `python3` 纯标准库 + 仓库 `tools/dist_data` 纯函数，零模型；脚本只在会话临时目录、不入仓），结果见 F25–F29 与 §8；未核项照列。**D4 同口径**：只读核 `controller/language_loop.py` 的受理/重试/结果行/stop/worker 路径（F30），零模型、零写 `runtime/`、零 SSH；只改 §3.5 与 AC-5/8 的 AR1-1 部分、A4 呈现挂起语义、§3.6 N-5 来源与 §9。

## 0. 现状与只读事实

符号名以开工时 `git rev-parse HEAD` 为准，实现时按符号名重定位。F1–F13 沿 D1 只读结果并按 D2 复读更正；F14–F24 为 D2 新增；F25–F29 为 D3 新增（只读）；F30 为 D4 新增（只读源码）。

| # | 事实 | 出处 |
|---|---|---|
| F1 | FRAME-001 10-04 Play：`deterministic-loop-untethered`、5 Hz、仿真 273 s；`nanotrack-v2` 配置框初始化；`standoff-band-v1` + 云台居中；中心误差 p50/p90 37.5/40.8 px，跟随距离 p50/max 14.0/22.2 m，云台饱和 0、丢失 0；用户目检轻微抖动、拐角停止 | `docs/evidence/P1-ENG-FRAME-001-supplement-play-20261004.md` |
| F2 | ACQ-001 常驻部件（`det-assoc-v1` 常驻、六值闭集、`ACQUIRING`、最小伺服）已过 `R3@K1K2K3`/`R3@K1K3`；Play D1 attempt 2 非 verdict（约 602 s、YOLO 加载 2 次、Unity 帧目录 129M），§7 停点已触发 | `docs/parked-status.md`「P1-ENG-ACQ-001 暂停停点与未闭义务」；`docs/unity-test-log.md`「Acceptance `PlayD1裁定2`」 |
| F3（更正） | `bind_body_runtime` 把策略写死为 `"threshold"`，且**不传 `runtime=`**；`_build_standoff_runtime` 需 `runtime` 与有限 `ground_plane_y_m`，并要求 `scenario_tether.effective_scenario_path(runtime)` 文档 = body 场景。`run` 的 `--body-scenario-config` 缺省 `config/scenario.default.json`，`_run_session` 总是传 planner 配置 → 现行每次 `run` 都是 threshold | `controller/language_loop.py::bind_body_runtime`、`_run_session`、`build_parser`；`controller/track_loop.py::_build_body_runtime`、`_build_standoff_runtime` |
| F4（更正） | **任何**常驻段终止都经 `_teardown_resident` 置 `loop = None`，下一次 `_advance_resident` 由 `_ensure_resident_loop` 以 `create_tracker(..., resident=True)` 重建并在 `DetAssocTracker.__init__` 再次调用模型加载器；终止原因来自异常（`image_identity_changed`/`bundle_missing`/`metadata_invalid`）、发布门 `fatal_reason`（`catchup_stale`/`frame_rollback`/`publish_expired`/`orphan_control` 等）、`TERMINAL_EVENT_REASONS`（`frame_gap`/`frame_rollback`）、`duration_reached`（常驻段仿真时长 ≥ `planned_duration_s`，IDLE 无指针时同样触发）、`frame_stall`；`backend_fatal` 置 `REINIT_REQUIRED` 亦重建；只有 `stop` 进 `TERMINAL` 不重建。原因闭集 = `bridge.STATE_REASONS` | `controller/language_loop.py::_advance_resident`、`_teardown_resident`、`_ensure_resident_loop`、`_handle_backend_fatal`；`controller/language_bridge.py::STATE_REASONS` |
| F5 | K 收据：`decide_host` 只返回 `mac`/`5060`/`HOST_UNDECIDED`；`validate_measurement_sources` 非 candidates 后端要求 `source_reports == {mac, 5060}`；candidates 单宿主分支只认 `mac`；收据 `scenario_id` 在会话启动时**不校验**（只校验 hz 与 R） | `controller/language_loop.py::decide_host`、`validate_measurement_sources`、`_validate_candidates_source` |
| F6（更正） | `tools/language_serve.py` 顶层只 import 标准库与 `controller.language_selector`，但**传递闭包**含 `controller.{language_bridge, protocol, resident_core, reanchor, trackers}`（D2 复读其顶层 import 均为标准库或包内相对 import）；运行时惰性 import `tools.eng_sft.prompt_v2`（`_prompt_identity`，HttpAdapter/LocalHf/Replay 构造时）、`tools.eng_sft.parse`（`interpret()`，含 candidates 后端每次指定/核验）、`tools.eng_sft.train_lora`（仅 LocalHf 路径）；`controller/language_loop.py` 的 `serve` 子命令 `from tools import language_serve`；`tools/` 无 `__init__.py`（命名空间包） | `controller/language_selector.py`；`tools/language_serve.py`；`controller/language_loop.py`（`serve` 分支） |
| F7 | 板上 VLM 服务（JET-001 诊断，不进证据）：`llama-server` b11381、C2 合并自转 Q4_K_M GGUF + 官方 mmproj F16，OpenAI 兼容 `/v1/chat/completions`；609 行配对 G1∪G2 76.4% vs Mac bf16 77.6%，板端 34 行 `SCHEMA_ERROR`；往返 p50/p90 1.71/1.82 s；**旧服务已停、18081 已释放**（JET C2 核清 §1）。文件 sha 与路径以 JET-001 提案「阶段BC2诊断核清」为来源，本文不手抄 | `docs/proposals/P1-ENG-JET-001-jetson-onboard-feasibility-probe.md`「阶段BC2诊断核清」§1 |
| F8 | 板上快层（JET-001 S1/S2/SR，compat 模式）不在本项；本项 v1 快层留在 Unity 主机 | `docs/evidence/P1-ENG-JET-001-fastlayer.json` |
| F9 | 场景：`config/scenario.untethered.json` 5 Hz、`retained_frame_count` 128、围栏、红车 2 m/s；与 default 相比只差 `scenario_id`、`tether_enabled false`、`geofence_xz_m`，`scene_adjustments` 两文件**逐值相等**（D2 只读比较） | `config/scenario.*.json` |
| F10（更正） | Unity 主机即本 MacBook Air；`~/.ssh/config` 有 `Host Jetson`（Tailscale 地址）；**Unity 主机 → Jetson 的 SSH/HTTP 可达性未核**（D2 未连接，按 engineering §9 列 B0a） | 本机 `~/.ssh/config`（只读） |
| F11 | 无四类数字脚本；操作者 CLI 无延迟注入 | `docs/evidence/P1-ENG-ACQ-001-play-d1.md` §0 |
| F12 | 规模：`language_loop.py` 约 3,500 行等（D1 口径） | `wc -l` |
| F13 | 状态板：本项为零消耗活跃交接之一；`COORD-018` 暂停至 10-09 | `docs/current-status.md` |
| F14 | **SUSPECTED 现行语义**：保留指针与 `track_id`，`tracker_state.publishing` 为真（SUSPECTED ∈ `PUBLISHING_STATES`）；逐帧是否发观测取决于指针结果是否 ok（ok → 观测 + `decide`；不 ok → 无观测 + `hold(no_observation)`）；自动核验暂停，人工 `verify`/`ask`/`respecify` 可用 | `controller/language_bridge.py::PUBLISHING_STATES`；`language_loop.py::_publish_state`、`_maybe_verify`；`track_loop.py::_publish_resident`、`_body_step` |
| F15 | **hold 收据**：规划器 hold 写 `body_safety_hold` 收据；显式 `GatedPublisher.hold_body()`（段起点、进入 `ACQUIRING`、`acquire_failed`）**直通、不写收据**；几何拒绝帧仍发观测、估计器 `predict_only`、`decide` 照常调用、不发 `look_at`（事件 `GEO_REJECT`） | `controller/gated_publisher.py`（`hold_body`、`_gate`）；`track_loop.py::_resident_frame` |
| F16 | **几何拒绝误报**：`_begin_acquiring` 几何拒绝分支记 `acquire_geometry_rejected` 后以 `slew_timeout` 调 `_acquire_failed`（即 ACQ R1-4） | `controller/language_loop.py`（`acquire_geometry_rejected` 附近） |
| F17 | **会话 JSONL 无事件闭集**：`_journal` 的 `kind` 自由字符串，字面量约 35 种 + 核心事件动态名（`L2_*`、`COASTING_*`）；疑似 L2 事件被直接记录后又在下次排空时重复记录（未核，A6 按指定号去重计数，不靠事件条数） | `controller/language_loop.py::_journal`；`resident_core.py::_finish` |
| F18 | **时间字段**：无 `t_k`/`t_confirm` 字段；`designation` 事件带 `frame_id_k` 与 `head_frame_id`（= h，ACQ §3.4「designate 调用时常驻关联器已处理的最新传感器帧」）；确认时刻只有 `receipt`（action=`confirm`）的 `at_unix_s`/`at_monotonic_s`；结果到达只在内存（`QueryOutcome.finished_monotonic_s`），无落盘事件；Python 单调钟与 Unity `system-stopwatch/v1` 是否同钟**未核** | `language_loop.py`（`QuerySnapshot`、`QueryOutcome`、`_journal`）；attempt 2 会话 JSONL |
| F19 | **K 收据生成器**：`tools/language_latency.py::build_receipt_document` 要求 mac 与 5060 两份报告；`k-receipt` 退出码只认两宿主；http 测量适配器构造时**无 `weights_sha256`**；**无代码写 `transport.endpoint`**（只有测试手写），而会话 http 路径要求它；收据不绑定代码版本（`environment()` 只记包版本） | `tools/language_latency.py`；`tests/test_language_k_binding.py` |
| F20 | **身份块**：`language_bridge._validate_model_block` 按固定字段表重建 `model` 块，未知键**静默丢弃**（不拒绝）；`HttpAdapter` 每次回复的 `model_identity` 须与绑定时逐键相等，否则 `MODEL_IDENTITY_MISMATCH` | `controller/language_bridge.py::_validate_model_block`；`language_selector.py::HttpAdapter` |
| F21 | **既有隔离测试**：`tests/test_eng_acq_guards.py::ControllerIsolation` 的真值包闭集 = `eng_acq`/`eng_fast`/`eng_det`/`dist_data`/`eng_asset`，显式豁免 `tools.eng_sft` 与 `tools.language_serve`；另有 `test_analyze_m3_body.py` 禁 controller 读 `m3_body_truth`、`test_standoff_planner.py::TruthIsolationTests` | 各测试文件 |
| F22 | **attempt 2 归档实读**（只读）：Unity 侧目录 133M，其中帧环 1500 JPEG（124,914,153 B）+ 1500 份 `tethered-sensor-frame/v3` 旁车（含 `camera_position_world_m`、`camera_forward/right/up_world`、`intrinsics_px`、`simulation_time_s`），只覆盖帧 1512–3011；`m3_body_truth.jsonl` 3,012 行（帧 0–3011，`p1-m3-body-truth/v2`，`truth_box_available` 1,294 行，会话窗口 0–960 内 545 行）；会话目录 52M：`language-session.jsonl` 1,009 行、`publish-receipts.jsonl` 1,556 行（`body_safety_hold` 862 / `observation` 307 / `look_at` 307 / `body_command` 80）、`results.jsonl` 7 行、会话帧环 961 JPEG（帧 0–960，49,575,497 B，**无旁车**）；段日志 `resident1` 901 行 + `resident2` 61 行 | `outputs/eng-acq/P1-ENG-ACQ-001/play-d1/{acq-d1-2,sessions/acq-d1-2}/` |
| F23 | **attempt 2 帧交集**：会话 JSONL ∩ 真值 961；会话 JSONL ∩ Unity 帧环 **0**；三者交集 **0**；段日志 `capture_monotonic_s`、`simulation_time_s` 与真值同帧逐值相等（抽 5 帧）；Unity 帧环 1,500 帧旁车相机位置 = 真值机身位置；离线 IoU（段日志 `box_norm` vs 红车真值，307 个 TRACKING 帧）中位 0.902、最小 0.646；同归档 `metrics.json` 却报 `c_track 0`、307 次全部 incorrect（原因未核，本项不用 `metrics.json`） | 同上（只读统计） |
| F24 | **静止车几何来源**：`docs/evidence/P1-M3-BODY-001-scene-geometry.json`（779 实例、101 辆车，含 AABB；sha 由 `tools/dist_data/contract.py` 固定；`source_scenario_sha256` = default 场景 sha，`scene_adjustments_applied true`）；锚点 25 m 内 2 辆、40 m 内 6 辆；红车不在其中。投影：`tools/dist_data/project_boxes.py::Camera.from_sidecar` + `project_instances`（AABB 八角投影、画家序遮挡、状态闭集 OK/TOO_SMALL/TRUNCATED/EXCLUDED_OCCLUDED/NOT_IN_VIEW/PHANTOM）；`bind_layout.apply_layout` 施加 `vehicle_relocations`。Unity 只为红车写逐帧真值（`CoverageEvaluator`），静止车无 Unity 真值 | `tools/dist_data/{project_boxes,bind_layout,contract}.py`；`Assets/.../CoverageEvaluator.cs` |
| F25 | **归档摘要链（D3）**：attempt 2 与 FRAME-001 play-2 两份归档**都没有任何元数据字节摘要**：Unity 帧环与 `retained_frame_metadata/` 无索引文件；段日志行只有 `simulation_time_s`/`capture_monotonic_s`；`publish-receipts` 的 `detail.snapshot_sha256` 与 `results.jsonl` 的 `frame_sha256` 都是**图像** sha；`verify_frame_identity` 在内存逐值核对元数据但不落盘摘要。可独立交叉的只有：旁车相机位置 vs 真值行 `body_world_*`（逐轴 ≤ 1e-3 m：128/128、1500/1500）与 F23 的时刻三方相等；姿态基向量与内参**无独立第二来源**（只有同文件内 `vertical_fov_deg` 自洽） | `controller/gated_publisher.py::verify_frame_identity`；两份归档（只读） |
| F26 | **布局绑定来源（D3）**：standoff 段 manifest `body_planner` 运行时写 `effective_scenario_sha256`/`scenario_config_sha256`（FRAME-001 play-2 = untethered 当前 sha）；attempt 2 threshold 段 manifest 的 `scenario_config_sha256` = `runtime/hold-frame-001-acq-scenario-override/scenario_config.json` 的 sha，该文件 `scene_adjustments` 与 default 逐值相等；几何 `source_scenario_sha256` = default 当前 sha。`load_base_geometry` 断言几何 sha 且 `scene_adjustments_applied true`；`apply_layout` 的输入须是 `unadjusted_base` 逆施后的几何（对已调整几何直接正施 = 重复迁移） | 两份 manifest；`tools/dist_data/bind_layout.py` |
| F27 | **静止车投影试读（D3，§8 详）**：几何 101 辆车 `scene_object_name` 无重名；锚点 xz 40 m 内 6 辆。两份归档中这 6 辆**从未出现 `OK`**（FRAME-001 128 帧全 `NOT_IN_VIEW`；attempt 2 Unity 帧环 1500 帧 5 辆 `NOT_IN_VIEW`、1 辆 `EXCLUDED_OCCLUDED`）；从 Play 起始位姿（锚点、高 25 m）对每辆合成居中相机，6 辆投影均 `OK`，但离天底角只有 2 辆 ≤ `gimbal.maximum_off_nadir_deg` 45°（约 16°、21°；其余 49°–58°）。红车：真值 `target_world_*` 经旁车相机投影与真值框中心像素差中位 5.5/6.4 px（两归档），相机约定一致 | 几何文件；`config/scenario.untethered.json`；两份归档（只读） |
| F28 | **身份字段现状**：`_validate_model_block` 对全部 `*_sha256` 只做可选文本检查，**无格式/值域校验** | `controller/language_bridge.py::_validate_model_block` |
| F29 | **指定流转现状**：`ask`/`respecify` 同经 `_begin_designate`（新 epoch、丢弃旧候选）；`respecify` 无指令时复用已确认/当前指令；队列中被替换的查询写 `SUPERSEDED` 收据，旧 epoch 结果记 `IGNORED_STALE_EPOCH`；`ambiguous` 带候选也进 `AWAITING_CONFIRMATION`、可人工确认；无确认超时自动失效，`confirm` 时 `_check_confirmation` 判过期 → `stale_rejected` + `candidate_expired`；`reject` → `operator_reject`；`BOUND_COASTING` 超 `coasting_limit` 未找回 → `COASTING_TO_TRACK_ENDED` → `ACQUIRING` | `controller/language_loop.py`（`_action_respecify`、`_begin_designate`、`_superseded_receipt`、`_check_confirmation`、`_action_reject`、`_advance_resident`） |
| F30 | **样本归属与终止路径（D4）**：每行会话 JSONL 都带 `epoch` 与 `sequence`；受理的 `ask`/`respecify` 先 `epoch += 1` 再写 `receipt`，故受理行 `epoch` = 该次指定的新 epoch；`REQUEST_INVALID`（含桥层 `instruction_unsupported`）不是查询。`none`/`parse_failed`/查询检查点 `stale_rejected`/`backend_error`/`no_new_frame` 均经 `_designate_failure` 重试至 `ATTEMPT_LIMIT` 3，末次写 `retry_exhausted` + `last_status`/`last_reject_reason`；`worker_stuck` 写一行 `backend_error`（`reject_reason worker_stuck`）不重试并进 `backend_fatal`。**结果行 `request_id` 不能作键**：等新帧后恢复的重试经 `_resume_designate_retry` → `_issue_designate(None, None)` 为 `null`；确认检查点过期行带的是 `confirm` 命令的 `request_id`；取帧前失败的尝试另铸 `query_id` 而无 `query_submitted`；`IGNORED_STALE_EPOCH` 行只带 `query_id` 与旧 `epoch`。`stop()` 先 `epoch += 1`，`worker.stop` join ≤ 5 s（未结束记 `worker_abandoned` + `query_ids`）后进 `TERMINAL`，在途查询不写结果行；现行只有 `stop` 进 `TERMINAL`（`operator_stop`）。确认后常驻环缺失写 `designation_unavailable` 并恢复提问前状态；`ACQUIRING` 不在 `ask` 允许状态，`release` 只在 `TRACKING` | `controller/language_loop.py`（`_journal`、`_begin_designate`、`_issue_designate`、`_designate_failure`、`_resume_designate_retry`、`_handle_designate_outcome`、`_action_confirm`、`_designate_resident`、`stop`、`LanguageWorker.stop`、`_ASK_STATES`）；`controller/language_bridge.py`（`RESULT_STATUS`、请求解析） |

## 1. 目的与价值

主线目标（逐字引用 `docs/project-background.md` §3）：

> 做一个闭环系统：语言指定目标，快层跟上并保持居中，换目标时能迁移并跟上新目标，丢失与歧义显式报告。VLM 是主角（接口 A：输出框 + 所在 frame_id）；快层是非变量，但必须能换目标。部署目标是 VLM 与快层跑在 Jetson Orin Nano 8GB（headless），Unity 留桌面机。项目的难点是「发现目标 → 跟上」，不是保持跟踪。验证只看四类数字：陈旧指定解析成功率随延迟、转向存活率、捕获时间与成功率按偏角/距离分桶、误锁率与显式报告比例。不作为目标：单目标稳态保持率不设资格门；不做 ReID、SAM 2 在线、更大模型、INT8、SAHI、Unity 场景改动；不为快层做研究主张；VLM 剪枝等优化只在闭环跑通且曲线证明延迟重要之后。

三件部件各自过了复核或 Unity 验证，但从未同在一个回路（F1/F2/F7），四类数字一个都没在闭环里量过。本项只做三件事：**接线**（常驻指针快层跑在 `standoff-band-v1` 之上，VLM 由板上服务经既有 HTTP 协议接入）、**可测**（四类数字唯一算法与离线脚本、逐次延迟注入、丢失/失败时机身与云台显式合同、单会话单次权重加载）、**首测**（三剧本 Play 产出首批描述性读数与用户目检）。读数不设门；不改快层算法、不调规划器、不训练、不改 Unity。

## 2. 范围与不做的事

### 2.1 阶段 A（零消耗代码候选；合并停点 `K1K2K3K4`；§5.1 额度已首签，见「N-1答复落实」）

- **A1 会话接 standoff（K2）**：`run --body-policy {threshold, standoff}`，缺省 `threshold`。`standoff` 时 `bind_body_runtime` 以 `runtime=` 与 `ground_plane_y_m` 调 `_build_body_runtime(..., "standoff", runtime=...)`，走 FRAME-001 既有构造器。**生效场景回退不改**（AR1-4）：`effective_scenario_document`（缺省回退 default）对所有路径保持原样；`standoff` 入口改为**要求 `runtime/scenario_config.json` 存在**，缺失即 `ConfigMismatch` 拒绝启动——此时 language_loop 解析器与 `scenario_tether.effective_scenario_path` 都返回同一文件，无回退分歧；`--body-scenario-config` 须逐值等于该文件。段 manifest `body_planner` 记 `name` 与配置 sha（运行时计算）。`threshold`/段式路径、`config/scenario.default.json`、`scenario_tether` 的「language_loop 保留旧解析器」断言均不变。
- **A2 VLM 宿主 `jetson`（K1/K3）**：
  - (a) **服务端**：`tools/language_serve.py --backend llama-server --llama-bin <path> --weights <gguf> --mmproj <gguf> --llama-port <p>`：由 `language_serve` 以子进程启动 `llama-server`（只绑 `127.0.0.1`），启动前**自行计算** GGUF、mmproj、二进制三者 sha256 并与 `--expect-assets <json>`（阶段 B 由 AC-16 资产核实产出）逐键比对，不一致拒绝启动；`/status` 返回服务端自算身份、部署闭集摘要 `serve_code_sha256` 与 `platform.node()`。**部署摘要唯一定义（D3，AR1-5）**：对 `config/p1-eng-loop-002-board-deploy.json` 所列路径（含该清单文件自身），按仓库相对路径升序取 `[路径, 文件字节 sha256]` 对组成列表，规范 JSON（`sort_keys`、分隔符 `(",", ":")`、UTF-8）后求 sha256；同一纯函数放在 `tools/eng_loop2/deploy_digest.py`（纯标准库），板端 `language_serve` 对其源码根求值、桌面端 `language_latency`/会话对干净工作树求值，两端同一算法。**构建号**：服务启动时以子进程运行 `<llama-bin> --version`（不加载模型）并按 `^version: (\d+) ` 取构建号，记为 `b<数字>`；与 `--expect-assets` 不等即拒启。**服务生命周期**：`language_serve` 只在前台运行（禁止 `nohup`/后台/系统服务），SSH 会话结束前必须停服务并以同一会话的 `ss -ltn` 证明端口已释放（§5.2 板端墙钟因此完整覆盖服务驻留）。
  - (b) **适配器**：新文件 `tools/eng_loop2/llama_adapter.py::LlamaServerAdapter`（不放 `tools/eng_jet/`，避免与仍活跃的 JET-001 同文件并行修改，workflow §7 规则 3）：prompt v2 逐字（`tools/eng_sft/prompt_v2.py`）、`response_format` = 新入仓 `config/vlm-three-state.schema.json`、`temperature 0`、`max_tokens 160`、`cache_prompt false`、图像字节原样 base64 data URI；响应经冻结 `tools/eng_sft/parse.py`；原始 `finish_reason`、`gen_tokens`、原始文本与解析错误码随结果落盘，**不洗掉失败**（解析/约束失败照现行 `RESULT_STATUS` 闭集报告）。
  - (c) **新解码条件**（D1 (d)）：JSON 约束登记为本项新推理条件 `c2q4-json-v1`，经 K3；不回改 SFT-002 冻结 prompt/parse 或历史结果；三态与接口 A 不变；P2 两态 schema 不借用。schema 文件按 prompt v2/`parse.py` 的三态输出结构新写；JET-001 基座调试 S1 原件不在本机/本仓库（未核），**不声称同内容**，两项互不引为证据。llama-server b11381 对 `response_format` 携带 schema 的确切请求形状在本机未核，列为阶段 B 板上收据的前置假设（失败 → STOP `S-IDENTITY`/`S-RECEIPT`，§6.2）。
  - (d) **身份字段**（AR1-5；D3 补类型、值域、来源与比较链）：`model` 块新增 6 个**条件必需**可选字段，规则：6 键全有或全无；任一出现则其余 5 键必需，且 `backend == "http"`、`model_form == "c2-merged"`、既有 `weights_sha256` 与 `prompt_template_sha256` 非空并同为 hex64；全无时旧 HF/candidates/replay 结果与报告按现状通过。存在时逐键校验（不符即 `LanguageBridgeError`，不再只做可选文本，F28）：

    | 键 | 类型/值域 | 来源（谁算） | 期望值来源与比较点 |
    |---|---|---|---|
    | `mmproj_sha256` | 字符串，`^[0-9a-f]{64}$` | 板端服务启动时对 mmproj 文件字节自算 | AC-16 `-assets.json`（阶段 B 授权读数）→ `--expect-assets` 拒启；收据与会话启动逐键比 `/status` |
    | `runtime_binary_sha256` | 同上 | 板端对 `llama-server` 二进制字节自算 | 同上 |
    | `runtime_build` | 字符串，`^b[0-9]{1,7}$` | 板端 `--version` 输出解析（A2(a)） | 同上；**只是二进制自报标签**：身份锚点是二进制 sha，本项不重编译、不声称二进制源自某源码标签，JET-001 的构建读数不引用 |
    | `quantization` | 字符串，闭集 `{"Q4_K_M"}` | `-assets.json` 申报标签 | 经 `weights_sha256` 绑定（标签不独立解析 GGUF 头）；闭集外即拒 |
    | `response_format_sha256` | hex64 | 板端适配器对实际发送的 `response_format` 对象求规范 JSON sha | 桌面 `k-receipt` 由干净工作树的 `config/vlm-three-state.schema.json` 经同一纯函数重算并比报告值，不符退出码 6 |
    | `decode_config_sha256` | hex64 | 板端适配器对 `{"temperature":0,"max_tokens":160,"cache_prompt":false,"image_encoding":"base64-original-bytes"}` 求规范 JSON sha | 同上（常量入 `llama_adapter.py`，桌面重算） |

    规范 JSON 统一为 `sort_keys`、分隔符 `(",", ":")`、`ensure_ascii=False`、UTF-8。`prompt_template_sha256` 沿现行 `_prompt_identity`（`tools/eng_sft/prompt_v2.py`），桌面同样重算比对。**比较链**：干净工作树 HEAD（报告 `environment.git_head`、`dirty == false`）→ 桌面重算期望（response_format/decode/prompt/部署摘要）== 报告中 `/status` 读出的身份 → == 收据 `model_identity` 与 `serve_code_sha256` → 会话启动时 == 当刻 `/status`；资产三键另由 `--expect-assets` 在板端启动时拒启。`_validate_model_block` 固定字段表扩为含此 6 键；旧读者对新结果会静默丢弃新键（F20，限制保留），故新结果只由新代码读，`schema` 版本号 `tethered-language-result/v1` 不变是否足够由 K1 核对（D1 (d)：兼容性以测试证明，不以版本号代替）；不回改任何历史报告。
  - (e) **部署闭集**（AR1-6）：板上包 = `tools/language_serve.py`、`tools/eng_loop2/{__init__,llama_adapter,deploy_digest}.py`、`tools/eng_sft/{__init__,prompt_v2,parse}.py`、`controller/{__init__,language_selector,language_bridge,protocol,resident_core,reanchor,trackers}.py`、`config/vlm-three-state.schema.json`，按仓库相对路径原样置于板上一个源码根（`tools/` 为命名空间包，不加 `__init__.py`）；清单入仓为 `config/p1-eng-loop-002-board-deploy.json`（只列路径，清单文件自身也列入并随包部署；sha 由传输工具与 A2(a) 部署摘要运行时计算写证据）。`llama-server` 分支不得 import `train_lora`、`tools.eng_jet`、`tools.eng_loop2.analyze_play` 或任何第三方包。
- **A3 丢失/歧义/失败 → 机身与云台显式合同（K2）**：§3.4 闭集表写成可证伪条款，**不新增自动动作**（D1 (e)）。两处最小改动：(i) 显式 `hold_body()` 补写收据（沿用 `body_safety_hold` 通道，`reason` ∈ {`loop_start`, `acquiring`, `acquire_failed`}，通道闭集不变）；(ii) 会话 JSONL 增事件名闭集常量 `JOURNAL_KINDS`（现有字面量 + 动态核心事件前缀枚举 + 本项新事件），`_journal` 遇闭集外名字即抛错（测试覆盖全部现有调用点）。
- **A4 逐次延迟注入与意图标签（K1）**：操作者命令 `ask "<text>" [--delay-s Δ] [--intent <key>]` 与 `respecify ["<text>"] [--delay-s Δ] [--intent <key>]`（D3：两者同一参数集与同一语义，`respecify` 同样是一个样本，§3.5.1）：Δ ∈ [0, 8] s（缺省 0），作用于「结果到达 → 呈现给操作者」一段，由**会话**在消费 `QueryOutcome` 后挂起呈现，`LanguageWorker` 代码零改动（AR1-3 F3）；新增落盘事件 `result_arrived`（`query_id`、`at_monotonic_s`、`head_frame_id`）与 `result_presented`（`delay_s`、`at_monotonic_s`、`head_frame_id`）。`--intent` 取操作单预登记的对象键（`red_car` 或几何文件的 `scene_object_name`），只写进 `receipt` 日志，**不进查询、不进 prompt、不影响任何决策**（AC-9 断言）。`K_ret`/`K_conf`/`K_pub` 判定代码与起点不改；Δ 使某次确认越过现行检查点时按现行原因码处理，日志附 `delay_injected_s`。**呈现挂起语义（D4 补写，AR1-1；不改 Δ 域、参数与检查点）**：Δ 只施加于已过返回检查点、解释为 `unique`/`ambiguous`、将进入 `AWAITING_CONFIRMATION` 的结果；失败与重试路径不挂起、不写这两个事件。`result_arrived` 增字段 `status`（`unique`/`ambiguous`）。挂起期间状态保持 `QUERYING`（候选不可确认，`confirm` 按现行 `confirm_in_QUERYING` 回执）；结果行（`results.jsonl` 与 `runtime/` 结果文件）、呈现时刻（现行 `candidate_presented_monotonic_s`）与 `AWAITING_CONFIRMATION` 迁移都在 `result_presented` 时发生，预览图生成代码不改（H-9）；挂起中 epoch 改变（新受理 `ask`/`respecify` 或 `stop`）即丢弃该次呈现、不补写结果行。Δ = 0 时两事件同 tick 写出，行为与现行一致。
- **A5 单会话单次权重加载（K3）**（AR1-7、D1 (f)）：会话进程内对常驻检测器模型做**一次性加载缓存**：`_ensure_resident_loop` 经 `create_tracker(..., resident=True, model_loader=<会话缓存加载器>)` 透传（`create_tracker` 已把 `**resident_options` 转给 `DetAssocTracker`，`det_assoc_tracker.py`/`trackers.py` 零改动），重建 `TrackLoop` 与关联器状态但不再调用 `_default_model_loader`。终止原因分三类：`duration_reached` → `TERMINAL`（不重建）；`backend_fatal` → `TERMINAL`（VLM 不可用即结束本次，STOP `S-BACKEND`）；其余 `seg_end`（发布门/帧异常/`frame_stall`）→ 沿现行恢复重建，复用缓存模型，**每会话重建 ≤ 2 次**，第 3 次 → `TERMINAL(rebuild_limit)`（新增 `STATE_REASONS` 值，追加不重排）。重建产生的段 run 目录沿用户在 `PlayD1裁定2` 的口径不计新 run ID，但逐段记账。会话 `TERMINAL` 不等于 Unity 已退出 Play（D1 (f)）：操作单要求用户按停止按钮并记时刻。
- **A6 四类数字脚本（K4）**：`tools/eng_loop2/analyze_play.py` 按 §3.5 唯一算法读会话 JSONL、`results.jsonl`、`publish-receipts.jsonl`、段日志、Unity 帧环旁车、`m3_body_truth.jsonl` 与几何文件，产出四表、指定漏斗与全部分母；真值只进评分函数。**运行时侧摘要（D3，AR1-3/H-2）**：会话 `frames_processed` 事件增字段 `metadata_sha256`（与 `frame_ids` 同序；会话写该事件时对 `runtime/frames/frame_<N>.json` 当刻字节求 sha256，读不到 → `null` 并附 `metadata_sha256_missing_reason`），只改 `language_loop.py`，不改 Unity、不复制旁车。**输入 schema 冻结点（D3，AR1-9）**：§3.5.1 输入字段表随本合同在接受 `ACCEPTED` 时冻结（依据 D2 F22–F24 与 D3 F25–F27 的真归档只读读数）；阶段 A 实现后 A6 对 attempt 2 与 FRAME-001 归档的 `-archive-dryrun.json` 只作**确认**（描述、不作验收）；若与已冻结 schema 不符（字段缺失/改名、绑定失败率与本文读数矛盾），实现停止并把差异写进交接交接受，接受按 engineering §2 末条以合同修订答复并记入本提案决策记录、冻结后，实现才整理稳定候选交 `C1`——`C1` 只核对，不冻结、不改写合同。
- **A7 ACQ R1-4 承接（K1/K3）**：几何拒绝分支 cause 改 `geometry_rejected`（追加进 `STATE_REASONS`），不再冒充 `slew_timeout`，补回归（AR1-3）。
- **A8 K 收据单宿主生产路径（K1）**：见 §3.2；改 `tools/language_latency.py`（入闭集）。
- **A9 操作单与承接**：`docs/evidence/P1-ENG-LOOP-002-play-ops.md`（§3.6），承接表 §2.5。

阶段 A 写 `-K1K2K3K4-handoff.md` 后进入 `C1@K1K2K3K4`，再新鲜上下文 `R1@K1K2K3K4`。

### 2.2 阶段 B（消耗性；分两次申请签发；R1 通过且接受按 workflow §4.5 放行后）

- **B0a 只读事实预检**（零推理、零启动、零写入；engineering §9）：Unity 主机对 Jetson 一次 SSH 只读会话：部署目录/GGUF/mmproj/二进制是否存在及字节数、`python3 --version`、`df`/`free`、`ss -ltn` 确认无残留服务、Tailscale 往返（`ping` ≤ 5 包）。只读，但属板操作，需用户单独同意（needs_user N-2）。读数写 `-precheck.md`，B-main 维度按读数回填后再申请。
- **B-main（签发后）**：B0b 写入/启动类准备（Unity 主机：ACQ 残留不存在于 `runtime/scenario_config.json`（D2 只读已核：该文件当前不存在，FRAME-001 期旧覆盖已在 `runtime/hold-frame-001-acq-scenario-override/`），生成本项覆盖文件并记 sha；板上：传输部署闭集、AC-16 板端 sha 核实、启动服务、`/status` 身份核对）→ B1 板上 K 收据 → B2 三剧本 Play → B3 离线读数与用户目检。
- B 的消耗证据另过停点（§7，AR1-9）。

### 2.3 v1 不变项与本项自限

账本 09-28 D.6：5 Hz、不变焦、不加 ReID、不重训检测器、Unity 零改动、候选池 = 默认锚点附近可居中的静止车 + 运动红车、改锚点属配置改动需另裁定。本项自限：冻结检测器规格与 `freeze.json`、`designate` 参数（τ 0.5、m 0.2、`coasting_limit` 30、`T_replay` 2 s、`l_replay_frames` 128）、`AcquireParams`（`T_slew` 3 s 等）与伺服 30°/s、`standoff-band-v1` 参数、prompt v2 文本、`K_pub 2`、`T_STALL_S 3` 全部不改。

### 2.4 明确不做

不改快层算法/关联器参数；不调规划器；不训练、不改接口 A；不改 Unity 场景/脚本/`*.unity`；不做板上快层共驻（JET-001 S5）；不做 3c TRT Edge-LLM；不做搜索回扫或自动重问（D1 (e)）；不设资格门；不为快层/规划器做研究主张；不改 `config/scenario.default.json` 与生效场景回退；不改 LOOP-001 段式与 threshold 路径语义；不修 F17 疑似 L2 重复记录（只在 A6 去重，交接受决定是否另记债）；不新增 Unity 采集协议、不让会话帧环复制旁车；不做 K5；不动 5060 `repo-b`。

### 2.5 承接清单（逐条：来源、触发判定、本项处置、唯一债务入口）

| # | 来源与原文触发 | 本项是否触发（判定依据） | 处置与范围内验证 | 债务入口 / AC |
|---|---|---|---|---|
| H-1 | LOOP-001 **F3**（`docs/reviews/P1-ENG-LOOP-001.md` §3 F3；账本 `docs/implementation-status.md` SCOPE_GAP 行）：「下一次触及 LanguageWorker 或扩展延迟/排队域前承接独立在途起点及回归」 | A4 的 Δ 是**会话侧呈现延迟**，在 worker 返回结果之后，不进入 worker 等待/在途域；板上宿主 p95 预计低于现行 5060 收据（扩展的是确认前呈现延迟，不是在途/排队延迟） | `LanguageWorker` 类 diff 必须为空（AC-11 机检）；测试证明 Δ 期间 worker 空闲、`T_hard` 计时未运行。若实现发现必须改 worker → 停止并回接受，先承接 F3 独立在途起点与回归再继续 | 账本原行保持 `OPEN`；AC-11 |
| H-2 | LOOP-001 **F8**（R7@K1K2K3 §3）：「复用可变归档、允许人工改写或发现来源不一致前承接元数据哈希/时刻一致性回归；正式证据出现异常须停并如实报告」 | **触发**：A6 对可变归档评分 | **摘要链（D3）**：现有归档无任何元数据字节摘要（F25），故新增运行时侧摘要 `frames_processed.metadata_sha256`（A6）。A6 对每个使用旁车的评分帧核：(1) 归档旁车字节 sha == 会话运行时记录的 `metadata_sha256`；(2) 旁车 `frame_id`/`simulation_time_s` = 真值行 = 段日志行；(3) 旁车 `camera_position_world_m` 与真值 `body_world_*` 逐轴 ≤ 1e-3 m；(4) 旁车 `scenario_id` = 已绑定场景副本（§3.5.1）；会话 `results.jsonl` 的 `frame_sha256` = 会话帧环 JPEG。任一不符 → 该帧 `frame_identity_mismatch`，`-four-numbers.json` 顶层计数，正式证据中出现即 STOP `S-ARCHIVE`；运行时摘要为 `null` → 该帧 `NO_POSE(metadata_unbound)`。**缺失处置**：attempt 2 与 FRAME-001 两份旧归档没有 (1)，其静止车试读一律标 `metadata_unbound`，只作描述、不算 F8 承接证据。回归夹具含「同帧同刻只改姿态基向量/内参/位置」三种篡改，须被 (1) 拒绝（(2)(3) 不足以拒绝姿态/内参篡改，F25） | 本项只对**新 Play 归档**承接；复核通过后由接受决定 F8 账本行状态（本提案不改，不声称闭债）；AC-8 |
| H-3 | ACQ **R1-4**（账本行；`docs/reviews/P1-ENG-ACQ-001.md` R1-4）：「扩展视野/距离或延迟域、复用被淘汰 k 帧路径前，须改为不冒充转向超时的 cause 并补回归」 | **按触发处理**：standoff 机身移动使斜距域不同于 ACQ threshold 条件（F1 跟随距离 max 22.2 m），Δ 扩展确认前延迟，R 改 1500；不逐路径论证不可达 | A7 纳入范围：cause `geometry_rejected` + 回归（几何拒绝不得产生 `slew_timeout`）；被淘汰 k 帧路径沿现行 `FRAME_NOT_IN_HISTORY`（`l_replay_frames` 128 不改） | 修复候选经复核后由接受处置账本行；AC-17 |
| H-4 | ACQ **K1K3-R1-1**（账本行）：「未来改动 `CandidatesBackend` 或预检工具却复用旧报告时承接代码版本校验与回归」 | **不触发**：本项不改 `CandidatesBackend`、`_validate_candidates_source`、`tools/eng_acq/candidates_preflight.py`（diff 为空，AC-11 机检），B0a 是新只读预检、非该工具 | 新 jetson 单宿主收据自身绑定代码版本（§3.2），不复制该缺陷；不宣称承接 | 账本原行 `OPEN` 不变；AC-11 |
| H-5 | FRAME-001 **R1-3**：围栏 float32/float64 口径，「扩展该数值域前」承接 | 不触发：不扩围栏数值域 | 围栏读取代码 diff 为空 | `OPEN` 不变；AC-12 |
| H-6 | FAST-001 **R1-2**（空窗返回 `KEPT`）与 ACQ H-9 空窗断言 | **触发**：A6 改编七类结局 | 判据同 `tools/eng_acq/e2.py::assert_no_empty_window`（窗口内无帧或帧间隔 > 8 s），但该函数**抛 `EmptyWindow`**；本项显式转换为排除类 `TRUTH_GAP(empty_window)`（§3.5.4），不得 `KEPT`，回归覆盖（D3 更正） | FAST-001 账本行不改；AC-8 |
| H-7 | ACQ attempt 2 §7 停点（时长、加载 2 次、体积超预估） | 触发 | A5 单加载、§5 硬上限、§6.2 STOP 表 | AC-3、AC-10 |
| H-8 | ACQ `runtime/scenario_config.json` 残留义务 | D2 只读：该文件当前**不存在**（FRAME-001 期覆盖在 `runtime/hold-frame-001-acq-scenario-override/`） | 操作单 B0b 第一步复核不存在；若存在则移入 `runtime/hold-acq-d1/`，不删除 | AC-10 |
| H-9 | ACQ AC-17 人眼保真（触及预览/采集/保存路径须重做 ≥ 2 张） | A4 只改呈现时刻，不改预览图生成/保存代码 | 候选自证逐字声明是否触及；触及则 Play 前重做 | AC-11 |
| H-10 | ACQ H-5 清理清单（5060 `repo-b`、`hold-diag-loopb-*`） | 不触发 | 原样引用、零删除 | AC-11 |
| H-11 | FRAME-001 §9.1：language_loop 采用新跟随策略须另写修订 | 即 A1 | 回退不改、standoff 要求显式覆盖文件 | AC-1 |
| H-12 | JET-001 板上产物（诊断件）；B-C2-RESULT 10-06 按推荐答复（保留产物、不追认）；「C2 Q4 加 JSON 约束」诊断额度属 JET-001 | 本项作组件使用 | 本项在**自身**阶段 B 授权下重核 sha 与运行证据（AC-16）；JET-001 读数、原违规/UNKNOWN 与其 JSON 诊断额度均不引用、不转用、不追认 | AC-16 |

ACQ-001 的非 verdict、AC-18 `NOT_RUN`、清理清单、旧余额全部原样保留，不转为本项额度。

## 3. 接口与数据契约

### 3.1 会话 ↔ 快层 ↔ 规划器（K2/K3）

- 会话命令：`python3 -m controller.language_loop run --backend http --server-url http://<jetson>:<port> --model-form c2-merged --k-receipt <jetson 收据> --tracker det-assoc-v1 --resident --body-policy standoff --body-planner-config config/p1-eng-frame-001-body.json --body-scenario-config runtime/scenario_config.json --scenario-id deterministic-loop-untethered --planned-duration-s <T_sess> …`（三个 body 参数显式）。
- 覆盖文件 = `config/scenario.untethered.json` 全文 + `sensor.retained_frame_count` 改 1500（操作单生成命令、sha 运行时记录）；`standoff` 缺覆盖文件即拒绝（A1）。
- `T_sess` 由操作单按「会话起点 Unity 帧号 f₀」计算：`T_sess ≤ (1490 − f₀)/5` s，保证整场 Play 帧数 ≤ Unity 帧环 1500（§3.5.6 静止车位姿来源）。

### 3.2 VLM 后端与 K 收据（K1）

- **测量**：`tools/language_latency.py measure --host jetson --backend http --server-url <url>`：测量适配器从服务 `/status` 读取身份（不接受用户传入 sha），要求非空 `weights_sha256` 与 A2(d) 六字段；报告写 `host`、`transport.endpoint`、`environment.git_head` 与 `environment.dirty`（客户端工作树）、服务 `serve_code_sha256` 与 `machine`、每请求状态（含解析/约束失败，失败行不过滤）；3 预热 + 32 计时、按 `frame_id` 首见、p95 = 第 31 个（现行同口径）。
- **收据**：`k-receipt --single-host jetson --report <r> --runtime runtime --out <o>` 生成 `host: jetson`、`source_reports = {jetson: {path, sha256}}` 的收据，`k_ret = ⌈p95·hz⌉ + 2`、`k_conf`、`k_pub`、`R`、`scenario_id`、`model_identity` 全部来自报告与生效场景；生成前桌面以干净工作树重算 `response_format_sha256`、`decode_config_sha256`、`prompt_template_sha256` 与部署摘要（A2(a)(d)），与报告中 `/status` 值逐键比较；退出码：0 = 已生成且合格；6 = 报告缺失/不全/身份或部署摘要与重算不符/六键类型值域不合；新增 8 = 已生成但不合格（`K_ret + K_conf + K_pub > R − 8`）。现行 `--mac --gpu` 两宿主路径、`decide_host` 与退出码语义逐字不变。
- **会话启动校验**（仅 jetson 路径新增，旧路径不变）：收据 `host == "jetson"` 且报告自身 `host == "jetson"`；`source_reports` 恰为 `{jetson}` 且文件 sha 相符；`backend == "http"`；`transport.endpoint == --server-url`；服务 `/status` 身份与收据 `model_identity` 逐键相等（含六字段）；`scenario_id` = 生效场景；hz、R 现行校验；`environment.git_head` = 会话进程 HEAD 且收据报告 `dirty == false`；`machine` = `/status` 的 `machine`；`/status.serve_code_sha256` == 收据报告值 == 会话进程对干净工作树按 A2(a) 同一定义重算的部署摘要（D3：客户端 `git_head` 相等不能单独证明板上部署正确，故比较板端自算摘要）。任一不符 → `ConfigMismatch` 拒绝启动。
- 备用臂 5060：现行 `local-hf`/`http` 两宿主规则零改动；仅用户按 §7 (j) 启用时使用。

### 3.3 延迟注入与时间语义（K1）

- **时间轴唯一来源 = 仿真帧轴**：所有四类数字的时长以帧号经真值行 `simulation_time_s` 换算（同一 Unity 时钟），不跨 Python/Unity 单调钟相减（F18：同钟未核）。
- t_k := 查询帧 `frame_id_k` 的仿真时刻；h := `designation.head_frame_id`（确认后 `designate` 调用时的历史头）；t_confirm := h 的仿真时刻；`Δ_eff = sim(h) − sim(k)`（仿真秒）。分桶以 `Δ_eff` 为准，注入值 Δ 只作标签。
- 墙钟读数（`query_submitted`、`result_arrived`、`result_presented`、`receipt(confirm)` 的 Python 单调钟）只作描述性辅助列。

### 3.4 状态 → 观测/机身/云台闭集（K2；全部为现行语义显式化，不新增自动动作）

| 条件（逐帧判定） | 发观测 | 机身命令 | 收据 | 云台 |
|---|---|---|---|---|
| 指针 ok（TRACKING 或 SUSPECTED） | 是 | `decide`（估计器 `fused`），经发布门 | `observation`、`body_command`/`body_safety_hold` | 每帧 `look_at`，限速 30°/s |
| 指针 ok 但几何拒绝 | 是 | `decide`（估计器 `predict_only`） | 同上 + `GEO_REJECT` 事件 | 不发 `look_at` |
| 指针 raw LOST / `BOUND_COASTING` 未匹配（TRACKING 或 SUSPECTED） | 否 | `hold(no_observation)` | `body_safety_hold` | 不发 |
| no_pointer（IDLE / LOST(*) / `REINIT_REQUIRED` / 重建后） | 否 | 每个最新帧 hold | `body_safety_hold`；段起点显式 hold 补 `reason=loop_start` 收据（A3） | 不发 |
| `ACQUIRING` | 否 | 显式 `hold_body()` 一次后持续 hold | A3 补 `reason=acquiring` | 每次指定一次 `slew_look_at` |
| `LOST(acquire_failed)` | 否 | 显式 `hold_body()` 后持续 hold | A3 补 `reason=acquire_failed` | 保持当前指向 |
| `AMBIGUOUS` / `NO_TRACK_AT_K` / `FRAME_NOT_IN_HISTORY` | 指针不变 | 指针不变 | — | 指针不变 |

不变式（AC-4）：任一无观测帧上不得出现 `WRITTEN` 的速度型 `body_command`；SUSPECTED 只由人解除，SUSPECTED 下自动核验暂停；丢失后不自动 `ask`/重指定（D.1）。

### 3.5 四类数字：唯一算法（K4；描述性，不设门；真值只在离线评分；D3 按 AR1-1/2 重写，D4 补样本闭集、意图与归属）

#### 3.5.1 样本、对象身份与输入绑定

- **样本**（D4）：会话 JSONL 中 `kind == "receipt"`、`action ∈ {ask, respecify}`、`outcome ∈ {APPLIED, PENDING_QUEUED}` 的行（受理行 L_s；`detail` 为 `waiting_for_new_frame` 或取帧失败原因者同样是受理）恰为一个样本 s，键 = 其 `request_id`，样本 epoch e_s = 该行 `epoch`（F30）。其余回执（`REQUEST_INVALID`，含桥层 `instruction_unsupported`；`IGNORED_*`）不是样本，另列 `COMMAND_INVALID`（按 `detail` 分列）。同一样本内的重试（`attempt` 2、3）不另计。本项会话恒为 `--resident`（§3.1）。
- **意图（D4 定为独立标志，不是漏斗类）**：只来自受理行的 `--intent`（A4，只写进收据），不继承前一条命令、不从绑定对象倒推。每样本取 `intent_status` ∈ {`valid`, `no_intent`（缺失）, `intent_unknown`（键不在闭集 {`red_car`} ∪ {几何文件 `group == "vehicle"` 且名字唯一的 `scene_object_name`}，F27：101 辆无重名）}。漏斗（§3.5.2）只用运行时事件判定，**全部样本**入漏斗、守恒不分意图；凡用意图评分的数字（一、二、三、误锁、漏斗口径显式比例）在各自**第一步**把非 `valid` 样本归 `NOT_EVALUABLE(no_intent|intent_unknown)`，不进该数字其他任何结局类与任何比率分母（逐数字见 §3.5.3–3.5.5）；其漏斗终态照列于交叉表 `funnel × intent_status`。
- **归属链与冲突处置（D4）**：`request_id` →（受理行）e_s → 查询/结果 → `designation_id`。(i) **查询**：`purpose == "designate"` 的 `query_submitted`/`query_started` 行与 `results.jsonl` 行按行内 `epoch == e_s` 归 s，`attempt` 取行内字段；结果行 `request_id` 只作一致性核对、**不作键**（F30）；`purpose == "verify"` 行不属任何样本。(ii) **指定**：e_s 内受理的 `confirm`（`APPLIED`）之后的 `designation` 行给出 s 的 `designation_id` 与 h；下游 `acquire_*`、`COASTING_TO_TRACK_ENDED`、L2 事件按 `designation_id` 归 s，同（`kind`, `designation_id`, `frame_id`）重复行取行序首行并计 `duplicate_event_rows`（F17，不修日志）；s 的指针 epoch = e_s 内该 `designation`（或同 `designation_id` 的 `acquire_adopted`）之后的 `pointer_bound`。(iii) **冲突闭集**，任一成立 → s 入漏斗类 0 `ATTRIBUTION_CONFLICT(<编号>)`、不进四类数字任何分母：C1 两个受理行同 `request_id`（两者均冲突）；C2 两个受理行同 epoch，或受理行 epoch 未按行序严格递增；C3 同一设计查询 `query_id` 出现于两个 epoch；C4 e_s 内结果行 `request_id` 非 `null` 且既非 s 的、也非 e_s 内受理的 `confirm` 的 `request_id`；C5 e_s 内呈现结果行（`unique`/`ambiguous`）与终局失败行（`retry_exhausted`，或 `reject_reason == "worker_stuck"` 的 `backend_error`）合计多于 1，或 `designation`/`designation_unavailable` 多于 1、其前无受理的 `confirm`，或受理的 `confirm` 之后三者（过期结果行、`designation`、`designation_unavailable`）皆无；C6 同一 `designation_id` 归入两个样本。(iv) 归不到任何样本的设计查询/结果/指定行计顶层 `unattributed_rows`（按 kind），不入漏斗。冲突与未归属计数列于 `-four-numbers.json` 顶层，只描述，不新增 STOP（§6.2 不变）。
- **布局绑定（静止车）**：归档须含本会话生效场景文件的副本（操作单把 `runtime/scenario_config.json` 移入归档，§3.6），其 sha 须等于该会话每个段 manifest 的 `body_planner.effective_scenario_sha256`（运行时写，F26），否则全部静止车 `NOT_EVALUABLE(layout_unbound)`；副本 `scene_adjustments` 须与 sha 等于几何 `source_scenario_sha256` 的场景（default，字节由 AC-2 冻结）逐值相等，相等 → **直接使用 `load_base_geometry` 返回的已调整几何，不调用 `apply_layout`、不逆施**；不等 → 全部静止车 `NOT_EVALUABLE(layout_mismatch)`（本项不实现逆施再正施链）。评分时不读 `runtime/` 下任何可变文件。
- **帧身份绑定（H-2）**：使用旁车的帧须过 §2.5 H-2 的 (1)–(4)；不符 → `frame_identity_mismatch`；运行时摘要为 `null` → `NO_POSE(metadata_unbound)`。红车只用真值行，不依赖旁车（偏轴/斜距分桶除外）。
- **真值框**：红车 = 同帧 `m3_body_truth` 行，可见 ⇔ `truth_box_available`；无真值行 → `NO_POSE(no_truth)`。静止车 = 同帧旁车 `Camera.from_sidecar` + `project_instances(camera, 全部几何实例, extra_blockers=[红车])`，红车遮挡体 = (`"red_car"`, `denormalize_xywh(真值框)`, 深度 = `camera.to_camera_space(target_world_*)[2]`)，仅当同帧红车真值可见时加入；可见 ⇔ 状态 `OK`，用 `visible_norm_xywh` 作框；其余状态 → 不可见并记状态名；无旁车 → `NO_POSE(no_sidecar)`。**几何近似**：AABB 包络、画家序按 AABB 中心深度而红车按底盘枢轴深度、无渲染遮挡；静止车「真值」是几何近似，与红车 Unity 真值分列报告，不合并为同一口径。
- **指针框与帧序列**：会话全部段日志行按 `frame_id` 升序合并为该会话帧序列（同一 `frame_id` 重复出现取首行并计 `duplicate_frame_rows`）；帧时刻 = 真值行 `simulation_time_s`（§3.3）。帧 f 的指针框 = 该行 `ok == true` 时的 `box_norm`，否则无。
- **帧型**（对给定意图，按序取第一个成立者）：`NO_POSE` → `INVISIBLE`（意图不可见）→ `ON`（有指针框且与意图框 IoU ≥ 0.3）→ `OFF`（有指针框但 IoU < 0.3）→ `MISS`（无指针框）。
- **观察终点 E(样本)**：h 之后按会话 JSONL `sequence` 先到者——下一条被受理的 `ask`/`respecify`/`release`/`confirm-lost`/`stop` 之前最后一个已处理帧、会话 `TERMINAL` 前最后一个已处理帧、会话最后已处理帧。
- **首发布帧 f_p**：h 之后、本样本的指针 epoch（`pointer_bound`，含 `ACQUIRING` 采纳后绑定）内第一个有指针框的帧。

#### 3.5.2 指定漏斗（每个样本恰入一个终态；D4 按阶段重写，按序判定，命中即止）

记号：X_s = L_s 之后按行序第一个「下一受理行 / `kind == "state"` 且 `state == "TERMINAL"` 的行 / 日志末尾（Play 结束而未写 `TERMINAL`）」；`cause` = 该 `TERMINAL` 行的 `reason`（`STATE_REASONS` 闭集；A5 后含 `operator_stop`/`duration_reached`/`backend_fatal`/`rebuild_limit`），日志末尾记 `log_end`。P_s = e_s 内呈现结果行（`unique`/`ambiguous`；A4 下在 `result_presented` 时写）；F_s = e_s 内终局失败行（`retry_exhausted`，或 `worker_stuck` 的 `backend_error`）。phase = e_s 内有 `result_arrived` 而无 P_s → `presentation_pending`，否则 `query_pending`。中间尝试的失败行（随后又重试）不是终态。

0. `ATTRIBUTION_CONFLICT(C1…C6)`：§3.5.1 (iii)。
1. `SUPERSEDED(<phase>)`：无 P_s、无 F_s，X_s 为下一受理行。在途查询的 `IGNORED_STALE_EPOCH` 行、排队查询的 `SUPERSEDED` 收据、等新帧时无行，三种情形同归此类，前两者只作佐证。
2. `INTERRUPTED(<phase>, <cause>)`：无 P_s、无 F_s，X_s 为 `TERMINAL` 或日志末尾（`worker_abandoned` 另记标志）；或受理的 `confirm` 之后为 `designation_unavailable` → `INTERRUPTED(designation_unavailable, resident_loop_absent)`。
3. `QUERY_FAILED(<status>)`：F_s 为 `retry_exhausted` 且 `last_status` ∈ {`parse_failed`, `backend_error`, `no_new_frame`}，或 F_s 为 `worker_stuck` 的 `backend_error`（记 `backend_error`）。
4. `STALE_REJECTED(query|confirm, <reject_reason>)`：`query` = F_s 为 `retry_exhausted` 且 `last_status == stale_rejected`（原因取 `last_reject_reason`）；`confirm` = P_s 后受理的 `confirm` 之后有 `stale_rejected` 结果行（F29）。
5. `VLM_REPORTED(none)`：F_s 为 `retry_exhausted` 且 `last_status == none`。（中间尝试为 `none`、其后尝试给出候选者不在此类；`ambiguous` 带候选与 `unique` 一样进入确认阶段。）
6. `OPERATOR_REJECTED`：P_s 后、X_s 前受理的 `reject`。
7. `UNCONFIRMED_SUPERSEDED`：P_s 后、X_s 前无受理的 `confirm`/`reject`，X_s 为下一受理行。
8. `UNCONFIRMED_AT_END(<cause>)`：同 7 但 X_s 为 `TERMINAL` 或日志末尾。
9. `DESIGNATE_REPORTED(AMBIGUOUS|NO_TRACK_AT_K|FRAME_NOT_IN_HISTORY)`：受理的 `confirm` 后 `designation` 行为此三值。
10. `ACQUIRE_PATH(track_ended|coasting_timeout)`：`designation` 为 `TRACK_ENDED`，或 `BOUND_COASTING` 在出现 f_p 前经同 `designation_id` 的 `COASTING_TO_TRACK_ENDED` 转 `ACQUIRING`（F29）。
11. `BOUND_DIRECT(bound|coasting_recovered)`：其余 `BOUND`/`BOUND_COASTING`。

唯一性：C5 保证 P_s 与 F_s 至多其一、`confirm` 后去向唯一；无二者时由 X_s 三选一收口（类 1/2），有 P_s 时由 `reject`/`confirm`/X_s 收口（类 4–11），故每个非冲突样本恰入 1–11 之一。守恒：受理行数 = 十二类之和 = 各 `intent_status` 计数之和（不等即脚本抛错）。每样本另存原始字段：各尝试 status 序列、VLM 三态（含 `result_arrived.status`）、`finish_reason`、解析错误码、六值原始结果、`ACQUIRE_FAILED` cause、`delay_injected_s`、`Δ_eff`、`worker_abandoned` 标志。

#### 3.5.3 数字一：陈旧指定解析成功率随延迟

- n₁ = 终态 ∈ {`BOUND_DIRECT`, `ACQUIRE_PATH`, `DESIGNATE_REPORTED`}。第一步（D4）：`intent_status ≠ valid` → `NOT_EVALUABLE(no_intent|intent_unknown)`，不论终态。
- 其余样本：`BOUND_DIRECT` 的结局（窗口 (h, h + `coasting_limit` 30 帧]）：先到 E 且无 f_p → `CENSORED`；窗口内无 f_p → `BOUND_NO_PUBLISH`；f_p 帧型 `ON` → `RESOLVED_CORRECT`，`OFF` → `RESOLVED_WRONG`，`INVISIBLE`/`NO_POSE` → `NOT_EVALUABLE(<帧型>)`。`ACQUIRE_PATH` → `TO_ACQUIRE`（只在数字三计结局）；`DESIGNATE_REPORTED` → `REPORTED`。
- 报：条件率 `RC/(RC+RW)`；总率 `RC/(n₁ − NOT_EVALUABLE(全部子因) − CENSORED)`；并列全部类计数（含意图子因）。`Δ_eff` 桶 {[0,1), [1,2), [2,4), [4,8), [8,∞)} s。

#### 3.5.4 数字二：转向存活率（FAST-001 R4 七类结局的**本项改编**，不称逐字复用）

- **起点集 S** = 每个绑定样本（终态 `BOUND_DIRECT`/`ACQUIRE_PATH`）中 `intent_status == valid`、有 f_p 且 f_p 帧型 ∈ {`ON`, `OFF`} 者，各一个起点 f_p。进入 S 前按序判定并守恒（D4）：绑定样本数 = `NOT_EVALUABLE(no_intent|intent_unknown)` + `NO_FIRST_PUBLISH`（无 f_p）+ `START_UNSCORABLE(INVISIBLE|NO_POSE)` + |S|。W = 13 s（主）与 8 s（并列）。
- **按序判定**：(1) f_p 为 `OFF` → `UNBOUND_START`；(2) sim(f_p) + W > sim(E) → `CENSORED_END`；(3) 窗口 (f_p, f_p+W] 内任一 `NO_POSE` → `TRUTH_GAP(no_pose)`，`INVISIBLE` 连续 > `track_buffer` 30 → `TRUTH_GAP(invisible)`，窗口内无已处理帧或任意相邻帧间隔 > 8 s → `TRUTH_GAP(empty_window)`（ACQ `e2.assert_no_empty_window` 在此**抛 `EmptyWindow`**，本项改为显式排除类）；(4) 自 f_p+1 起按时间扫描，窗口内全扫，窗口外只在漏检段未结束时继续，至多到 E：`OFF` → `ID_SWITCH`；`ON` → 漏检段清零（若已在窗口外即止 → `KEPT`）；`MISS`/`INVISIBLE` → 漏检段 +1，达 31 → `LOST_BEYOND_BUFFER`；窗口外遇 `NO_POSE` → `TRUTH_GAP(no_pose_ext)`；到 E 漏检段仍未结束 → `UNRESOLVED_END_MISS`；窗口扫完且无未结束漏检段 → `KEPT`。
- **与 `tools/eng_fast/replay.py::window_outcome` 的差异（逐条）**：起点为每个绑定事件而非全部可见帧；身份按意图对象 IoU 而非 `track_id`（指针 `track_id` 在 `ON` 帧之间变化只计子计数 `pointer_track_changed`，不改结局）；序列末端改为 E；新增 `NO_POSE` 与 `empty_window` 排除；其余（漏检段计数含不可见帧、跨窗口尾延伸、31 帧判据）同原函数。
- 存活率 = `KEPT/D`，D = `KEPT + ID_SWITCH + LOST_BEYOND_BUFFER + UNRESOLVED_END_MISS`；守恒 `|S| = 排除三类 + D`。按进入路径（直接 / 经 `ACQUIRING`）与偏轴角桶分列。

#### 3.5.5 数字三：捕获时间与成功率；数字四：误锁与显式报告

- **捕获**：样本 = 终态 ∈ {`BOUND_DIRECT`, `ACQUIRE_PATH`}（n₃，两路径分列）。第一步（D4）：`intent_status ≠ valid` → `NOT_EVALUABLE(no_intent|intent_unknown)`。其余截止 `N_cap` = 52 帧（10.4 s 仿真）自 h 起，按 {f_p、`acquire_failed`（按 `designation_id` 归属）、E、截止} 时间先到者判定：E 先到 → `CENSORED`；`acquire_failed` 先到 → `ACQUIRE_FAILED(<cause>)`；截止先到 → `CAPTURE_TIMEOUT`；f_p 先到且 `ON` → `CAPTURED`，`OFF` → `WRONG_CAPTURE`，`INVISIBLE`/`NO_POSE` → `NOT_EVALUABLE(<帧型>)`。成功率 = `CAPTURED/(n₃ − CENSORED − NOT_EVALUABLE(全部子因))`，并列 `CAPTURED/(n₃ − NOT_EVALUABLE(no_intent|intent_unknown))`。time-to-bind = sim(f_p) − sim(h)（仅 `CAPTURED`）。time-to-center：自 f_p 起意图框中心距 (320, 240) < 64 px 连续 5 帧的首帧（`INVISIBLE`/`NO_POSE` 帧打断连续计数），截止 min(f_p + 13 s, E)：`CENTERED` / `CENTER_NOT_REACHED`（13 s 到）/ `CENTER_CENSORED`（E 先到）。分桶：偏轴角（k 帧旁车相机前向与意图中心方向夹角：画内 / 出画 ≤ 45° / > 45° / `NO_POSE`）× 斜距（< 20 / 20–35 / > 35 m / `NO_POSE`）；k 帧无旁车即 `NO_POSE` 桶。
- **误锁**：分母 = |S|（§3.5.4：意图有效、f_p 为 `ON`/`OFF` 的绑定样本）；误锁 = f_p 为 `OFF`，或其存活结局（W = 13 s）为 `ID_SWITCH`；存活结局为排除类且 f_p 为 `ON` 的样本计非误锁并另列子计数 `mislock_window_partial`。误锁时长 = [f_p, min(E, f_p + 13 s)] 内帧型 `OFF` 且段日志 `published_observation` 为真的帧数 ÷ 5，并列这些帧上 `WRITTEN` 的 `observation`/`body_command` 收据数；归属于该样本的指针 epoch。
- **显式报告比例**：ACQ §3.10 口径照列；漏斗口径 = 显式 /（显式 + 静默错误），总体只取 `intent_status == valid` 且非类 0 的样本，每样本两个指示量各至多计 1：显式 = 终态 ∈ {`QUERY_FAILED`, `STALE_REJECTED`, `VLM_REPORTED`, `DESIGNATE_REPORTED`} 或捕获结局 `ACQUIRE_FAILED`；静默错误 = 数字一 `RESOLVED_WRONG` 或数字三 `WRONG_CAPTURE`（同一样本两者都成立只计 1）。两指示量互斥（显式终态均非绑定类；`ACQUIRE_FAILED` 先于 f_p，与 `WRONG_CAPTURE` 同属一个捕获结局）。不进分子分母、另列：`OPERATOR_REJECTED`、`UNCONFIRMED_*`、`SUPERSEDED`、`INTERRUPTED`、`ATTRIBUTION_CONFLICT`、意图非 `valid` 样本（其显式类计数另列）。

#### 3.5.6 输出、分母与数值出处

- 每表列原始 n、每桶计数与全部排除/不可评估类；任何比率分母为 0 → 值 `null` 并标 `ZERO_DENOMINATOR`；n < 5 的桶标 `INSUFFICIENT_N`；全文不出现「通过」。
- 静止车可评分前提：帧在 Unity 帧环内（旁车）且过帧身份绑定；整场 Play 帧数 ≤ 1500（§3.1）。attempt 2 会话窗口与 Unity 帧环交集为 0（F23），其静止车全部 `NO_POSE`——试读事实，不是合同失败。
- **输入 schema 冻结点**：见 A6（随合同在 `ACCEPTED` 冻结；归档试读只作确认，不符走合同修订答复后才交 `C1`）。

| 数值 | 出处类别（COORD-017 (a)） | 比较基线 | 用法 |
|---|---|---|---|
| IoU 0.3 | 合同既有：场景 `evaluation.tracking_iou_threshold`、`CoverageEvaluator`、ACQ §3.9、FAST-001 `BIND_IOU` | FAST-001 R4 / ACQ E1 离线读数 | 身份判定线（描述） |
| 13 s / 8 s 窗口 | 移植：FAST-001 `WINDOWS_S` | FAST-001 R4、ACQ E2 离线 13 s | 描述 |
| 8 s 帧间隔 | 移植：ACQ `e2.EMPTY_WINDOW_MAX_GAP_S` | ACQ E2 | 排除判据 |
| 64 px / 5 帧、角度/斜距桶 | 移植：ACQ §3.10 申请口径 | ACQ Play D1 申请口径（无实测） | 描述 |
| `N_cap` 52 帧；f_p 窗口 30 帧 | 合同推导：现行 `coasting_limit`/`T_slew`/M/`K_pub` 申请值之和；`coasting_limit` | 无 | 描述性截止，不作门 |
| `track_buffer` 30 / 31 帧 | 合同既有冻结规格 | — | 结局判定 |
| 1e-3 m 位置一致性 | 合同推导：同一 Unity 写者同帧两字段，D3 两归档 1628/1628 帧满足（F25） | F25 | 帧身份判据 |
| 45° 离天底角 | 合同既有：`gimbal.maximum_off_nadir_deg` | F27 | B/C 派生（§3.6） |
| `Δ_eff` 桶 | 本项申请值（覆盖 0–8 s 注入域） | ACQ E1 离线 Δ 档 | 描述 |

移植/申请线一律只作描述，超线照记，不触发任何停止（COORD-017 (b)）。离线对照基线 = ACQ E1/E2 与 FAST-001 R4 既有读数，只并列、不比较出结论。

### 3.6 Play 剧本与操作单

- **B/C 派生（D3，AR1-2；阶段 A 由脚本运行时计算写入操作单，不手抄）**：候选池 = 几何文件 `group == "vehicle"` 中锚点 xz 40 m 内者（账本 09-28 D.6「默认锚点附近」）；保留「从 Play 起始位姿（锚点、`drone.initial_altitude_m`）对其 AABB 中心合成居中相机时，离天底角 ≤ `gimbal.maximum_off_nadir_deg` 且全几何投影状态 `OK`」者，按 xz 距离升序取前两辆为 B、C。D3 试读（F27）恰得 2 辆；阶段 A 若得 < 2 辆即停并回接受。归档帧不作派生依据（F27：两份归档中这 6 辆从未 `OK`）。
- **只凭运行时画面的操作者规则（D3，AR1-1）**：每次 `ask`/`respecify` 前，操作者只看会话实时预览确认意图对象在画面内；不在 → 不发命令，记 `SKIPPED_NOT_IN_VIEW`（不成样本，`-play.md` 逐次列出）。候选选择只看候选预览图与操作单预登记的文字描述（由几何对象名派生的车型/颜色，写在 Play 前）：恰一个候选相符 → `confirm` 该序号；零个或多个 → `reject`。离线真值与 IoU 只在评分脚本内使用，不得用于任何 Play 中的人工决定。
- **采样批准来源（N-5，D4 标明）**：下条 P1 序列 B→C→red→B（red 1、B 2、C 1 次）与上条只凭实时预览的 `SKIPPED_NOT_IN_VIEW` 规则由用户批准，逐字见 `docs/authorizations.md` 2026-10-06「P1-ENG-LOOP-002 — 用户就 D3 退修选 U-D3 (a) 继续修订，并批准 N-5 D3 的 P1 采样顺序（supervisor 会话代录）」，接受落实见决策记录「U-D3答复落实」。限制照留：Play 次数、计划命令总数、候选池不变；批准不证明 F27 合成居中等于 Play 实时可见；B/C 派生不足 2 辆即停、真值隔离、布局/帧身份绑定、几何近似与红车 Unity 真值分列、完整失败分母均不豁免；实际可见性、跳过次数与有效样本数未知，跳过不成样本且逐次列出；数字只描述，不作性能比较，也不与 D2 序列比较。批准只覆盖此采样方案，不外推到其他剧本、次数或资源。
- **P1（静止车与红车切换；D3 改为从起始位姿先切静止车）**：Play 起始（机身在锚点）`ask "<B 描述>" --intent <B>` → `confirm` → 观察 ≥ 15 s → `ask "<C 描述>" --intent <C>` → `confirm` → 观察 ≥ 15 s → `ask "the red car" --intent red_car` → `confirm` → 跟 ≥ 20 s → `ask "<B 描述>" --intent <B>`（按上条规则可能 `SKIPPED_NOT_IN_VIEW`）→ `confirm` → **观察捕获 ≥ 15 s**（记录实际结局，不预设 `TRACK_ENDED`）。改序理由：B/C 只在起始位姿附近可居中（F27），先跟红车 20 s 后机身已离开锚点，原序的 B/C 指定大概率不在画面。
- **P2（含混指令）**：`ask "the car" --intent <操作单预登记对象>` → 记录实际 VLM 三态与候选；有候选时按上条只凭预览图的规则 `confirm` 或 `reject` → `respecify "the red car" --intent red_car` → `confirm`。剧本只记录实际三态与人工选择。
- **P3（逐次延迟，同一 Play 内）**：三次 `ask "the red car" --intent red_car --delay-s Δ`，Δ 依次 0 / 2 / 4，每次 `confirm` 后观察 ≥ 15 s、`release` 再进下一次。
- **计次与重试**：正式 Play 恰 3 次（P1/P2/P3 各 1）；环境性重试**全局 ≤ 2 次、每剧本 ≤ 1 次**，只限首个机身命令前、闭集原因（Unity 未进 Play、`/status` 不可达、运行时锁冲突），两次之间代码与参数不变；重试与原始失败都保留并计入 Play/session 账。合计 session ≤ 5。
- 操作单节闭集：接受放行核对（HEAD = 复核文件 `passed_candidate`，运行时解析；工作树干净；`_Recovery` 不存在）、B0a 读数引用、B0b 步骤、覆盖文件生成与 sha、板上服务启动与身份核对、K 收据、三剧本逐字命令与 `T_sess` 计算、每次尝试记录模板（Play 按钮起止、会话 `TERMINAL` 时刻、Unity 末帧号）、§6.2 STOP 表、归档（`outputs/eng-loop2/P1-ENG-LOOP-002/play/<SID>/`，只移动不删除；**含本 session 的 `runtime/scenario_config.json` 移入归档**作布局绑定副本，§3.5.1）与体积核对；B/C 派生输出与预登记文字描述；板端服务前台启动/停止与端口释放记录；有效载荷计数器与峰值磁盘读数（§5.2）。

### 3.7 证据文件（`docs/evidence/P1-ENG-LOOP-002-*`）

阶段 A：`-K1K2K3K4-handoff.md`（自证四条件、改动文件闭集、承接声明、全套额度只读核对结果）、`-tests.log`、`-archive-dryrun.json`、`-four-numbers-fixture.json`、`-play-ops.md`、`-assets-local.json`。阶段 B：`-precheck.md`（B0a）、`-assets.json`（含板端）、`-k-receipt-jetson.json` + 报告、`-play.md`、`-four-numbers.json`、`-ledger.json`（逐维度消耗账）。

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | `--body-policy standoff`：构造 `standoff-band-v1`（`runtime=` 已传，段 manifest `body_planner.name` 与配置 sha 可核）；`runtime/scenario_config.json` 缺失 → `ConfigMismatch`；body 场景与覆盖文件不逐值相等 → `ConfigMismatch`；**反例**：缺省 `threshold` 且无覆盖文件时仍解析 default（场景 id `deterministic-loop-default`）、调用序列与 ACQ-001 通过候选一致（间谍记录）；`scenario_tether` 现有断言不改 | test: `tests/test_language_loop.py` | K2 | 2026-10-06 |
| AC-2 | threshold 与段式路径既有用例全绿且未改；`standoff_planner.py`、`p1-eng-frame-001-body.json`、`det-assoc-v1.models.json`、`prompt_v2.py`、`parse.py`、`config/scenario.default.json` 字节不变（sha 断言，sha 运行时取自基线提交） | test: 既有套件；`tests/test_loop2_freeze.py` | K2 | 2026-10-06 |
| AC-3 | 单会话模型加载计数 = 1：`duration_reached` → `TERMINAL` 不重建；`backend_fatal` → `TERMINAL`；其余 `seg_end` 重建复用缓存、加载计数不增；第 3 次重建 → `TERMINAL(rebuild_limit)`；替身加载器计数断言覆盖每类原因 | test: `tests/test_language_loop.py` | K3 | 2026-10-06 |
| AC-4 | §3.4 每行一例；不变式：无观测帧无 `WRITTEN` 速度型 `body_command`；显式 `hold_body()` 三种 reason 各有收据；SUSPECTED 下指针 ok/不 ok 两分支行为与表一致、自动核验暂停；丢失后无自动 `ask`；`JOURNAL_KINDS` 闭集覆盖全部调用点、闭集外名字抛错 | test: `tests/test_language_loop.py` | K2 | 2026-10-06 |
| AC-5 | `ask --delay-s Δ`：结果到达后恰延 Δ 呈现（注入时钟）；`result_arrived`/`result_presented` 事件字段齐（`result_arrived` 含 `status`）；挂起只施于 `unique`/`ambiguous` 结果，失败/重试不挂起、不写两事件；挂起中状态为 `QUERYING`、`confirm` 回执 `REQUEST_INVALID`、结果行与 `AWAITING_CONFIRMATION` 迁移在呈现时才发生；挂起中新受理 `ask`/`respecify` 或 `stop` → 丢弃呈现、不写结果行（各一例）；`K_ret`/`K_conf`/`K_pub` 判定与 Δ=0 时同一代码路径；越过检查点按现行原因码并带 `delay_injected_s`；Δ ∉ [0, 8] 拒绝；Δ 期间 `LanguageWorker` 空闲、`T_hard` 未计时；`--intent` 不出现在查询请求体与任何决策输入；`respecify` 带 `--delay-s`/`--intent` 与 `ask` 同语义各一例；`frames_processed.metadata_sha256` 与 `frame_ids` 同序、等于当刻文件字节 sha，文件缺失 → `null` + 原因 | test: `tests/test_language_loop.py` | K1 | 2026-10-06 |
| AC-6 | 收据：`k-receipt --single-host jetson` 由报告生成、退出码 0/6/8 语义；会话 jetson 启动校验 §3.2 每一项各有错配拒绝用例（缺报告、报告 host 不符、文件 sha 不符、无 `transport`、端点不符、身份任一键不符、`scenario_id`/hz/R 不符、`git_head` 不符或 dirty、`machine` 不符、`serve_code_sha256` 与本地重算不符、`response_format`/`decode`/`prompt` 身份与本地重算不符）；六键：部分出现、hex64 格式错、`runtime_build` 不合 `^b[0-9]{1,7}$`、`quantization` 闭集外、`backend`/`model_form` 不符各拒一例，六键全无的旧 HF/candidates/replay 报告照常通过；两宿主旧收据与 candidates 用例不变 | test: `tests/test_language_k_binding.py`、`tests/test_language_latency.py` | K1 | 2026-10-06 |
| AC-7 | `LlamaServerAdapter` 对假 OpenAI 兼容服务：请求体含 prompt v2 逐字、`response_format` = 入仓 schema、解码参数、图像原样 base64；响应经 `parse.py`；`finish_reason`/原始文本/解析错误码落盘；缺依赖（子进程起不来）、超时、非 JSON、schema 不符、`finish_reason=length` 各映射到现行状态码且不丢行；`language_serve` 自算三文件 sha、`--version` 构建号与 `--expect-assets` 不符即拒启；部署摘要函数对同一文件集在「临时源码根」与仓库工作树上结果相等、改任一文件字节或增删清单路径即变；`/status` 只在前台进程存活期间可达（进程退出后端口释放）；服务与适配器在临时目录夹具中处理请求后不留图像/响应文件，访问日志逐请求含请求体/响应体字节 | test: `tests/test_llama_server_adapter.py` | K3 | 2026-10-06 |
| AC-8 | `analyze_play.py` 对夹具产出 §3.5 漏斗与四表：十二类终态各至少一例且守恒（含 `respecify` 样本、`UNCONFIRMED_SUPERSEDED`/`UNCONFIRMED_AT_END`、`coasting_timeout` 入 `ACQUIRE_PATH`、`BOUND_NO_PUBLISH`）；**D4 夹具（AR1-1）**：查询未返回时 `stop`、`duration_reached`、无结果行的 `backend_fatal`、日志无 `TERMINAL` 截断各 → `INTERRUPTED(query_pending, <cause>)`（`stop` 含有/无 `worker_abandoned` 两例）；Δ > 0 呈现挂起中 `stop` → `INTERRUPTED(presentation_pending, operator_stop)`、新 `ask` → `SUPERSEDED(presentation_pending)`；查询未返回时新 `ask` 的在途（`IGNORED_STALE_EPOCH`）/排队（`SUPERSEDED` 收据）/等新帧（无行）三例均 → `SUPERSEDED(query_pending)`；`designation_unavailable` → `INTERRUPTED(designation_unavailable, …)`；重试：首次 `none`、第 2 次给候选者不入 `VLM_REPORTED`，`retry_exhausted` 的 `last_status` 为 `none`/`stale_rejected`/`parse_failed` 各入类 5/4/3，`worker_stuck` 行入 `QUERY_FAILED(backend_error)`；`request_id: null` 的恢复重试行与带 `confirm` 的 `request_id` 的过期行按 epoch 正确归属且不判冲突；C1–C6 各一例 → `ATTRIBUTION_CONFLICT` 且不进任何分母；未归属设计行计 `unattributed_rows`；`REQUEST_INVALID`（含 `instruction_unsupported`）不成样本；`no_intent`、`intent_unknown` 各一例：入漏斗且守恒、在数字一/二/三/误锁/显式比例第一步归 `NOT_EVALUABLE(intent)` 且不进分母；重复 `COASTING_TO_TRACK_ENDED` 行只计一次；同一样本 `RESOLVED_WRONG` 与 `WRONG_CAPTURE` 同时成立时静默错误只计 1；存活 §3.5.4 每条判定与「与原函数差异」各一例（跨窗口尾延伸至 E、`empty_window` 不抛错而排除、`OFF` 起点 `UNBOUND_START`、指针 `track_id` 变化不改结局），守恒式成立；捕获/误锁/显式报告分母与 `ZERO_DENOMINATOR`、`INSUFFICIENT_N`；`NO_POSE` 与不可见分列；布局：副本缺失/sha 不符 → `layout_unbound`、`scene_adjustments` 不等 → `layout_mismatch`、相等时不调用 `apply_layout`（间谍断言）；H-2：同帧同刻只改姿态基向量、只改内参、只改位置三种篡改夹具均 → `frame_identity_mismatch`，运行时摘要 `null` → `NO_POSE(metadata_unbound)`；红车遮挡体深度按 §3.5.1；对 attempt 2 与 FRAME-001 归档可运行并写 `-archive-dryrun.json`（描述，静止车标 `metadata_unbound`） | test: `tests/test_eng_loop2_analyze.py`；artifact: `-four-numbers-fixture.json`、`-archive-dryrun.json` | K4 | 2026-10-06 |
| AC-9 | 隔离（枚举闭集）：`controller/` 对 `tools.*` 的 import 只允许 {`tools.eng_sft.parse`, `tools.eng_sft.prompt_v2`, `tools.eng_sft.train_lora`, `tools.language_serve`, `tools.eng_loop2.deploy_digest`}（D3 新增后者：纯标准库摘要函数，供会话启动重算部署摘要）；`controller/` 与 `tools/eng_loop2/llama_adapter.py`、`tools/language_serve.py` 不 import 真值/评分闭集 {`tools.eng_acq`, `eng_fast`, `eng_det`, `dist_data`, `eng_asset`, `analyze_m3_body`, `frame_follow_replay`, `tools.eng_loop2.analyze_play`}，不含 `m3_body_truth`/`CoverageEvaluator` 记号；`intent` 不进任何 controller 决策函数 | test: `tests/test_loop2_isolation.py`（AST）；既有 `test_eng_acq_guards.py` 不改 | K3 | 2026-10-06 |
| AC-10 | 操作单含 §3.6 节闭集（含 B/C 派生输出与 < 2 辆即停、只凭预览的选择规则、场景副本移入归档、服务前台起停与端口释放、有效载荷与峰值磁盘记录）与 §6.2 STOP 表；缺任一节即不满足 | artifact: `-play-ops.md` | K1 | 2026-10-06 |
| AC-11 | 承接声明逐条（§2.5 H-1…H-12）：`LanguageWorker` 类、`CandidatesBackend`、`_validate_candidates_source`、`candidates_preflight.py` diff 为空（cmd 机检）；是否触及预览/采集/保存路径逐字声明；清理清单零删除 | artifact: `-K1K2K3K4-handoff.md`「承接声明」；cmd: `git diff <base>..<cand> -- <路径>` | K3 | 2026-10-06 |
| AC-12 | 围栏读取代码 diff 为空；FRAME-001 R1-3 账本行不改 | test: `tests/test_loop2_freeze.py` | K2 | 2026-10-06 |
| AC-13 | 停点全套一次写 `-tests.log`，区分基线既有失败与本批新增；功能改动在 PLAY_GOVERNING 路径上的 diff ⊆ §4.1 表；文档 diff ⊆ §4.1 允许表；闭集外任何 diff 在交接中逐文件说明，不满足即退回 | artifact: `-tests.log`；cmd: `git diff --stat <base>..<cand>` | K1K2K3K4 | 2026-10-06 |
| AC-14 | Unity Play（阶段 B）：正式 3 + 环境性重试 ≤ 2（§3.6 分配）；每次按钮墙钟与体积在 §5 上限内；单加载（AC-3 计数随段日志落盘）；读数由 AC-8 脚本产出；`-ledger.json` 逐维度含 §5.2 全部计量项（HTTP 有效载荷双向字节、SSH 传输字节、板端墙钟与服务驻留起止、板端与 Unity 主机峰值磁盘）；用户目检逐字入 Unity 日志；`K1K2K3K4` 候选阶段本条 `NOT_RUN` | artifact: `-play.md`、`-four-numbers.json`；`docs/unity-test-log.md` | K1K2K3K4 | 2026-10-06 |
| AC-15 | 板上 K 收据（阶段 B）：AC-6 生产路径生成，不手写 JSON；不合格（退出码 8）即 STOP，不进 Play | artifact: `-k-receipt-jetson.json` | K1 | 2026-10-06 |
| AC-16 | 资产核实：阶段 A 只读本机来源（检测器权重/`freeze.json`/body 配置 sha，`-assets-local.json`）；阶段 B 在授权下核实板端 GGUF/mmproj/二进制 sha 与部署闭集 sha（`-assets.json`），作为 `--expect-assets` 输入；任何处引用 JET-001 诊断读数作证据即不满足 | artifact: `-assets-local.json`、`-assets.json` | K3 | 2026-10-06 |
| AC-17 | ACQ R1-4 承接：几何拒绝 → `acquire_failed` cause `geometry_rejected`（追加入 `STATE_REASONS`），回归断言几何拒绝路径不产生 `slew_timeout` | test: `tests/test_language_loop.py` | K1 | 2026-10-06 |
| AC-18 | 阶段 B 消耗证据另过停点（§7）：接受 `C2@K1K2K3K4` 只读核对；复核角色在 `docs/reviews/P1-ENG-LOOP-002.md` 的「证据核实@K1K2K3K4」小节（PLAY_GOVERNING 无 diff 时，不开新轮）或 `R2@K1K2K3K4`（有 diff 时）给证据结论：以已复核的 `analyze_play.py` 对正式归档重放一次并与 `-four-numbers.json` 除生成时刻类元字段外逐值相等、`-ledger.json` 对信封与操作单逐维度一致、STOP 记录完整、H-2/布局绑定计数如实；`C2` 不得代签该结论；`K1K2K3K4` 候选阶段本条 `NOT_RUN` | artifact: `docs/reviews/P1-ENG-LOOP-002.md`「证据核实@K1K2K3K4」或 R2 节 | K1K2K3K4 | 2026-10-06 |

### 4.1 归属表

**功能文件（PLAY_GOVERNING）**

| 文件 | 动作 | AC |
|---|---|---|
| `controller/language_loop.py` | M：`--body-policy`、`bind_body_runtime`、standoff 覆盖文件要求、`ask`/`respecify` 逐次 Δ 与 `--intent`、两新事件、`frames_processed.metadata_sha256`、部署摘要重算、`JOURNAL_KINDS`、单加载缓存与终止分类、jetson 启动校验、R1-4 cause | AC-1/3/4/5/6/17 |
| `controller/language_bridge.py` | M：`model` 块六字段条件必需与类型/值域校验；`STATE_REASONS` 追加 `rebuild_limit`、`geometry_rejected` | AC-3/6/7/17 |
| `controller/language_selector.py` | M（最小）：`HttpAdapter` 身份比较含六字段 | AC-6/7 |
| `controller/gated_publisher.py` | M（最小）：显式 `hold_body()` 写 `body_safety_hold` 收据 | AC-4 |
| `tools/language_serve.py` | M：`--backend llama-server` 分支、自算资产 sha 与构建号、部署摘要、`/status` 字段、前台生命周期、逐请求访问日志 | AC-7 |
| `tools/language_latency.py` | M：jetson 测量身份来源、`transport`、`git_head`、`--single-host` 收据、退出码 8 | AC-6/15 |
| `tools/eng_loop2/{__init__,llama_adapter,deploy_digest,analyze_play}.py` | N | AC-6/7/8/9 |
| `config/vlm-three-state.schema.json`、`config/p1-eng-loop-002-board-deploy.json` | N | AC-7 |
| `tests/test_language_loop.py`、`tests/test_language_k_binding.py`、`tests/test_language_latency.py`、`tests/test_language_bridge.py`（`STATE_REASONS` 遍历与六键校验，§7 (m)） | M/N | AC-1…7/17 |
| `tests/test_llama_server_adapter.py`、`tests/test_eng_loop2_analyze.py`、`tests/test_loop2_isolation.py`、`tests/test_loop2_freeze.py` | N | AC-2/7/8/9/12 |

**允许的文档 diff**：`docs/evidence/P1-ENG-LOOP-002-*`（实现）、`runtime/README.md`（`model` 块字段、新事件、收据 reason）、`docs/current-status.md`（各角色按白名单）、`docs/reviews/P1-ENG-LOOP-002.md`（复核）、本提案（构思/接受按各自白名单）、`docs/implementation-status.md`（接受）、`docs/phase1-single-drone-design.md`（接受角色同步正式设计，D3 补，AR1-9）、`docs/authorizations.md`/`docs/unity-test-log.md`（按代录规则）。协调批次或他项提交按真实 diff 核对，不因本表豁免。不在表内且属 PLAY_GOVERNING 的文件（含 `standoff_planner.py`、`det_assoc_tracker.py`、`resident_core.py`、`track_loop.py`、`trackers.py`、`scenario_tether.py`、全部 `config/scenario.*.json`、`tools/eng_sft/*`、`tools/eng_jet/*`、`Assets/`）出现在候选 diff 即 AC-13 不满足。

## 5. 预算信封（申请值；**用户逐字签发前各维度均为 0**；成功、失败、重试共账，耗尽即停）

### 5.1 阶段 A（`K1K2K3K4` 候选；Consuming no；N-1 已按下表首签，见「N-1答复落实」）

| 项目 | 申请值 |
|---|---|
| 执行机器 / 解释器 | Unity 主机 MacBook Air，现有 `.venv-yoloe` 原样使用（只读环境；不装包、不为本项在仓库虚拟环境装 `lap` 或任何依赖，JET-001 SUB 额度不转用）；`ENG_DET_DATA_ROOT` 不设置 |
| 停点全套 | 每候选 1 次、≤ 3 候选 |
| 每次全套内模型加载（D3 零消耗静态清单，AR1-8） | NanoTrack-v2 真实 ONNX 构造 **2**（`test_trackers.py` 与 `test_track_loop.py` 的 nanotrack 各 1；本机 `runtime/models/nanotrack-v2/` 两个 ONNX 在盘）；det-assoc 冻结检测器 CPU 加载 **0**（`test_det_assoc_carrier.py::CarrierSelfTest` 2 例在数据根缺失时跳过，本项不设数据根）；CSRT 构造尝试 2、实例 0（本机 `opencv_python` 5.0 非 contrib 构建无 `TrackerCSRT` 符号，两例为基线既有错误，`-tests.log` 按 AC-13 区分）；YOLOE/DINOv2/VLM/HF 0（相关测试均为替身或只哈希）。口径：只读源码静态清单，**非插桩计数**；JET-001 SUB:6 口径不适用（该树无 NanoTrack ONNX、设了数据根）。阶段 A 首次全套若实际加载与本行不符 → 停并回用户，不补跑 |
| 零模型数据回放 | A6 对 attempt 2 与 FRAME-001 两份既有归档只读评分，每候选 ≤ 2 次 |
| 墙钟 / 新增磁盘 | 每次全套 ≤ 15 min；证据与夹具 ≤ 20 MB |
| 其余（scenario/session/run ID、Play、VLM、板、5060、API、GPU、下载、pip） | 0 |

### 5.2 阶段 B（Jetson 主臂；Consuming yes；两次签发）

**B-pre（先签，零推理）**：板只读 SSH 会话 ≤ 2、每次 ≤ 10 min；`ping` ≤ 10 包；板端写入 0、服务启动 0、请求 0。

**B-main（B0a 读数回来后按读数回填再签；下列为暂估申请值，未核项标注）**

| 项目 | 申请值与计量口径 |
|---|---|
| session ID / 常驻段 | session ≤ 5（正式 3 + 环境性重试 ≤ 2）；段重建每 session ≤ 2，不计新 run ID（`PlayD1裁定2` 用户口径），逐段记账 |
| Unity Play | ≤ 5 次；每次**按钮墙钟**（用户按 Play 至按停止，操作者记录）≤ 420 s，合计 ≤ 2,100 s；会话仿真 `T_sess` ≤ 290 s |
| YOLO 权重加载（Unity 主机） | 每 session 1，合计 ≤ 5（AC-3 计数为准） |
| 板上服务启动（`language_serve` + 子进程 `llama-server`，每次 = 1 次 GGUF 加载） | ≤ 4（收据 1 + Play 批次 1 + 故障重启 ≤ 2） |
| VLM 推理请求（板上） | K 收据 35 + 同口径重测 ≤ 1 批 35；Play 每 session ≤ 60（指定 + 自动核验）× 5；合计 ≤ 370 |
| 非推理请求（`/status`、`/health`） | ≤ 200 |
| 板端累计墙钟与服务驻留 | 自每次 SSH 会话开始至结束求和（含准备、传输、启动、运行、清理与故障重试）≤ 3 h；服务只在前台、SSH 会话结束前必停并以 `ss -ltn` 证明端口释放（A2(a)），故驻留时段被 SSH 时段完整覆盖；另逐次记服务起止时刻，单次驻留 ≤ 60 min |
| 板端磁盘（峰值） | 服务与适配器不落盘图像或响应（AC-7 断言），板端写入只有部署目录与日志；每次 SSH 会话结束前与每次停服务前各记一次部署根与日志目录 `du -sb`，取最大值为峰值，**峰值** ≤ 200,000,000 B；同时记 `df` 可用空间；**不传任何模型** |
| SSH 文件传输（双向） | Mac → 板部署闭集文件字节 + 板 → Mac 回传日志字节合计 ≤ 20,000,000 B，≤ 3 批 |
| HTTP 有效载荷（双向，D3） | Unity 主机 ↔ 板 `language_serve` 的请求体 + 响应体字节合计 ≤ 60,000,000 B（暂估：attempt 2 帧环 JPEG 平均约 83 KB → base64 约 111 KB，每推理请求 ≤ 125 KB × 370 ≈ 46 MB；响应 ≤ 16 KB × 370 ≈ 6 MB；非推理 ≤ 8 KB × 200 ≈ 2 MB）；计量 = 板端 `language_serve` 逐请求访问日志（路径、请求体字节、响应体字节、起止时刻）求和，日志随回传计入上行；不计 TCP/Tailscale 封装开销 |
| Unity 主机归档与峰值 | 每 Play：Unity 帧环 ≤ 140 MB（attempt 2 实测 1500 JPEG 124.9 MB + 旁车）+ 会话目录 ≤ 85 MB（attempt 2 实测 961 帧 49.6 MB，按 1500 帧外推 ≈ 77 MB + 日志）；合计每 Play ≤ 225 MB、全部 ≤ 1.2 GB；**峰值**（已归档 + 当前 Play 尚在 `runtime/` 的帧环与会话目录，归档只移动不复制）≤ 1,450,000,000 B，每次 Play 后记 `du -sk` 归档根与 `runtime/` |
| 零模型数据回放（Unity 主机） | 实现自证对正式归档 ≤ 2 次；复核证据核实（AC-18）≤ 1 次；均只读归档、不写 `runtime/` |
| Unity 主机 `runtime/` 写入 | 覆盖文件生成 ≤ 5 次（每 session 1）；残留移动（若存在）1 次 |
| 5060 / 模型 API / GPU·h / 云 / 下载 / pip | 0 |
| 系统/SSH/沙箱设置 | 不改 |

**备用臂 5060**（仅用户按 §7 (j) 启用时另签）：5060 服务启动 ≤ 2、查询 ≤ 100，计入同一 session/Play 上限。

#### B0a核清回填：确定上限与可申请范围（2026-10-07）

**签发后索引：本节保留B0a核清当轮的计划/申请表。用户随后只签表中只读补核子范围，原命令/停止闭集见「补核答复落实」§2–3，现行换机额度与交接见「SUB1换机答复落实」；完整运行计划未签，不由本表自动启用。**

上表保留为 D4 历史申请；现行申请以本表及末节「B0a核清」为准，**没有签发任何额度**。engineering §9 要求依赖未核环境假设的维度在核实前不申请签发。本次只读事实支持容量与资产存在性，不能证明动态依赖/系统 Python 闭集可运行；因此完整 B-main 的运行上限已确定为下表计划数，**本轮请求用户签发的只有只读补核**，不把计划数变成附条件自动授权。补核后由接受角色再核清、转呈完整运行信封；不重问已答 (h)(j)(k)，不动 AC。

| 维度 | 完整 B-main 确定计划上限（目前不请求签发） | 本轮确定签发申请 | 依据 / 口径 |
|---|---|---|---|
| 设备 / 执行人 | MacBook Air 会话/快层；Jetson 单主臂；板上服务本人前台启动 | MacBook Air → 同一 Jetson，角色仅只读 | N-2/(k)、B0a R01/R02；不借 JET 额度 |
| SSH | ≤3 次、各≤60 min、累计≤10,800 s | 新子范围只读连接≤1次、≤600 s，失败/重试共账；重试0 | 完整计划=准备1+收据服务1+Play服务1；补核不从N-2余量暗转，另签且独立累计 |
| ping | 0 | 0 | N-2已有5包读数，不补网络测量 |
| session / 段重建 / 新run ID | session≤5，段重建每session≤2，新run ID 0（原口径） | 各0 | 正式P1/P2/P3各1，环境性重试全局≤2、每剧本≤1；仅Unity未进Play/运行时锁冲突；删除/status不可达重试分支，主臂失败不重试 |
| Unity Play / 墙钟 / T_sess | ≤5次；每次≤420 s；累计≤2,100 s；T_sess≤290 s且守§3.1帧起点式 | 各0；Unity/Play=否 | 保持AC-14原范围；420为资源上限，非性能通过线 |
| YOLO加载（桌面） | 每session≤1，合计≤5 | 0 | AC-3；不能由重建取得新加载额度 |
| 板服务启动 / GGUF加载 | ≤2次（收据1+Play批次1）；故障重启0 | 0 | 用户(j)主臂失败就停下；两次计划切换仅在前一阶段成功且正常停止后，不是失败重启 |
| 板VLM请求 | ≤335（收据35+Play每session≤60×5）；收据重测0 | 0 | 取消原35次重测；失败、超时、内置尝试都计请求，不能用335余额重开失败批次 |
| 非推理HTTP（status/health） | ≤200，含loopback健康请求，失败也计 | 0 | 原上限保留，补核禁止HTTP；HTTP可达性仍留运行阶段首次服务核验，不预判可达 |
| 板墙钟 / 服务驻留 | ≤10,800 s；每次驻留≤3,600 s；被SSH完整覆盖 | 补核≤600 s；驻留0 | 包含准备/传输/清理；两次正常服务最多7,200 s，余量只用于准备/收尾，不放宽启动次数 |
| 板新增峰值磁盘 | ≤200,000,000 B；不传/复制模型，不删件抵扣 | 角色板写入0 | R03可用160,143,331,328 B；16文件本地合计242,801 B；计部署根/日志及可归属cache/tmp/pycache实际增长，不以旧eng-jet的10,653,045,123 B冒充本项新增 |
| SSH文件传输（双向） | ≤20,000,000 B、≤3批（部署1+回传≤2） | 0；只读命令/stdout不作文件传输 | 16文件242,801 B，余量用于日志回传；不打包模型/共享库，不改来源文件 |
| HTTP有效载荷（双向） | ≤60,000,000 B | 0 | 原125 KB×335+16 KB×335+8 KB×200约48,835,000 B仅体积投影；60MB是确定资源上限，不保证每行小于投影；实际访问日志逐请求求和，异常/不完整照记 |
| 桌面归档 / 峰值 | 帧环≤140,000,000 B、会话≤85,000,000 B、每Play≤225,000,000 B；全部≤1,200,000,000 B；峰值≤1,450,000,000 B | 0；只写本机核清文档 | 原归档真读数/投影；5×225MB=1,125MB，原总限保留；只移动不复制 |
| 正式归档零模型回放 | 实现≤2次，复核≤1次 | 0 | AC-18；本次不评分、不跑测试 |
| runtime写入 | 覆盖生成≤5次、残留移动≤1次 | 各0 | 仅后续正式运行；本次不写runtime |
| --version / 动态依赖核读 | 资产核实1次+两次正常启动自核，共≤3次--version | readelf/ldd等静态依赖读取；--version 0、import 0 | 薄可执行文件实际依赖未核；本次补核不执行llama或部署包，不安装缺命令 |
| 内存事实（非新额度/通过线） | R05 available 5,999,063,040 B、总7,849,054,208 B、swap0；模型本体1,926,804,800 B，运行RSS/峰值UNKNOWN | 只读free，不加载 | 本体不能代替工作集，不新增内存性能门，不据旧诊断或无OOM签可用性 |
| 5060 / 外部模型API / GPU·h / 云 / 下载 / pip / 设置 | 0 / 不改 | 0 / 不改 | 缺项0；板推理另按请求/墙钟计，不移用桌面GPU或JET预算 |

本轮只读补核的边界见「B0a核清」§3：只获资产/依赖/端口/目录事实，不自动进入部署或服务。以上两组额度不互相转换，N-2原账SSH1/2、ping5/10保持；其余未签维度继续0。


## 6. 限制、不承诺与停止规则

### 6.1 限制与不承诺

- 不承诺任何通过/资格结论、`C_track` 变化、保持率、Jetson 共驻或性能结论；四类数字是 ≤ 5 次 Play 的小样本描述性读数，`INSUFFICIENT_N` 为常态（三剧本合计约 9 次指定、6–8 次绑定）。
- JSON 约束消除格式失败是**未验证假设**（D1 (d)）；解析/约束失败率照记，不设线、不改 prompt、不换模型。
- 静止车切换是 v1 妥协（D.2）；偏轴「> 45°」桶在候选池内可能为空；`NO_POSE` 桶如实列出。
- 闭环读数不能推出板上共驻可行或无人值守可用；用户观察到的拐角停止/抖动不在本项范围。

### 6.2 STOP 表（COORD-017 (a)–(d)；缺省处置随 B-main 信封交用户确认，未确认不生效）

| 原因码 | 判定（运行时合同条件） | 出处类别 / 比较基线 | 缺省处置 |
|---|---|---|---|
| `S-PRECHECK` | B0a/B0b：板不可达、部署文件缺失、残留服务占端口 | 合同（无服务即无运行） | 停全部后续，回接受 |
| `S-RECEIPT` | 收据退出码 6/8，或 `response_format` 请求被服务拒绝 | 合同（LOOP-001 既有资格式） | 停全部后续，回用户（备用臂须 (j)） |
| `S-IDENTITY` | 资产 sha、构建号、`/status` 身份、部署摘要、`git_head` 任一不符 | 合同（AC-6/16） | 停全部后续，回接受 |
| `S-ENVELOPE` | 任一维度达上限 | 授权信封 | 停全部后续，回用户 |
| `S-LOAD` | 任一 session YOLO 加载 > 1 | 合同（AC-3） | 停全部后续（代码缺陷），回实现/复核 |
| `S-BACKEND` | `backend_fatal` | 现行原因码 | 停本次；同原因第 2 次 → 停全部后续 |
| `S-REBUILD` | `TERMINAL(rebuild_limit)` | 本项合同（A5） | 停本次，计入；下一剧本照常 |
| `S-WALL` | 按钮墙钟 > 420 s | 授权信封 | 停本次并停全部后续，回用户 |
| `S-ARCHIVE` | 每 Play 归档 > 225 MB，或 H-2 帧身份核验（§2.5，含运行时元数据摘要）在正式归档出现 `frame_identity_mismatch`，或场景副本缺失/不符（`layout_unbound`） | 授权信封 / LOOP-001 F8 | 停全部后续，回用户 |
| `S-SERVICE` | SSH 会话结束时服务仍在监听（`ss -ltn` 未释放）或发现后台驻留 | 本项合同（A2(a)） | 停全部后续，回用户 |
| `S-RING` | Play 末帧号 ≥ 1500（Unity 帧环覆盖早段） | 合同（§3.1） | 不停；静止车相应帧 `NO_POSE` 照记 |

`frame_stall`、`PUBLISH_REJECTED`、`catchup_stale` 等现行硬停止按 A5 重建分类处理并照记；移植/申请值（§3.5.6 表）一律不作 STOP。

## 7. 必经停点与提请裁定

- **`K1K2K3K4` 合并单候选**：K1 = 收据宿主/单宿主校验、延迟注入与时间语义、`model` 块字段、`STATE_REASONS` 追加；K2 = standoff 接线、§3.4 机身/云台合同与 hold 收据；K3 = VLM 适配器身份与解析、单加载与终止分类、R1-4 cause；K4 = 四类数字定义与脚本。`C1@K1K2K3K4` → 新鲜上下文 `R1@K1K2K3K4`；不触发 K5；不申请 `UNITY_NA`。
- **消耗证据另过停点**（engineering §4 末条，AR1-9；D3 改写）：阶段 B 结束后实现者写 `-play.md`、`-four-numbers.json`、`-ledger.json` 并自证（四条件 + STOP 处置记录）→ 接受 `C2@K1K2K3K4` 只读核对证据与操作单、信封、STOP 记录一致性（`C2` 不代签复核结论）→ 复核角色给证据结论（AC-18）：`git diff <passed_candidate>..<证据候选>` 在 PLAY_GOVERNING（含冻结集点名的 `-play-ops.md`）上非空 → 开 `R2@K1K2K3K4`；为空 → 依 workflow §4.4 **不开新轮**，由复核角色在原复核文件 `docs/reviews/P1-ENG-LOOP-002.md` 的具名小节「证据核实@K1K2K3K4」检查新工件（评分脚本对正式归档重放一致、账/操作单/信封逐维度、STOP 记录、H-2 与布局绑定计数）并给证据结论；该小节不计复核轮次、不改代码、不跑测试套件，只做 §5.2 列明的 ≤ 1 次零模型重放。**规则适配已裁定**：见「D3 接受裁定」的「§7 证据核实路径裁定（N-4 不触发）」；D4 保持该裁定及全部适用边界，不豁免独立性。阶段 B 中任何代码修补都形成新候选，依 engineering §4 末条写明「未在真实条件下验证」并回到停点。
- **合同修订而非核对轮冻结**（D3，AR1-9）：§3.5.1 输入 schema 随 `ACCEPTED` 冻结；实现后归档试读若不符，走接受的合同修订答复（engineering §2 末条，记入决策记录）后再交 `C1`；`C1` 不冻结、不改写合同。
- **提请接受角色裁定（D2 新增）**：(l) A3 的显式 hold 收据沿用 `body_safety_hold` 通道与新增 `reason` 值是否视作 K1 收据格式变更；(m) `STATE_REASONS` 追加 `rebuild_limit`、`geometry_rejected` 是否需同步 `runtime/README.md` 以外的外部读者；(n) F17 疑似 L2 重复记录是否另记 SCOPE_GAP；(o) F23 `metrics.json` `c_track 0` 与离线 IoU 矛盾是否另立排查（本项不用 `metrics.json`）。
- **待用户**（答复前缺省一律「不做」；推荐只供选择，不按推荐先执行；不在 supervisor 代拍闭集）：(h)–(k)、N-2 B-pre、N-3 STOP 缺省处置（随 B-main 信封，含 `S-SERVICE`）六题原文、推荐及理由保留于「D2 接受裁定」needs_user，现行前置门与转呈见「N-1答复落实」。N-1 已答，不重问；N-4 不触发。
- **推进方式**：D4 已接受；N-1 已按 §5.1 首签并落实，交 Implementation 阶段 A（由 supervisor 派发或用户开 `/implement`），自证后交 `C1@K1K2K3K4` 再独立复核；未签维度为 0，阶段 B 原前置门不变，全部额度首签、Play、板上启动归用户。

## 8. 只读试读与试运行数字（D2/D3 只读；Unity 主机磁盘既有文件）

- **attempt 2 归档**（F22/F23）：Unity 侧 133M（帧环 1500 JPEG 124,914,153 B，帧 1512–3011，旁车含位姿/内参）；会话侧 52M（会话帧环 961 JPEG 49,575,497 B，无旁车）；`language-session.jsonl` 1,009 行（`frames_processed` 941、`state` 19、`receipt` 16、`query_*` 14、`designation` 2、`pointer_bound` 2、`resident_loop_*` 4 等）；`publish-receipts.jsonl` 1,556 行；`results.jsonl` 7 行（全部 `ambiguous`，`frame_sha256` 7/7 与会话帧环相符）；`m3_body_truth.jsonl` 3,012 行。
- **绑定率**：会话 ∩ 真值 961/961；会话 ∩ Unity 帧环 0；段日志与真值时刻抽 5 帧逐值相等；红车离线 IoU 中位 0.902（307 帧）；会话窗口内红车真值可见 545/961。
- **FRAME-001 10-04 归档**（`runtime/runs/` 下 play-2，12M）：段日志 1,366 行、真值 1,390 行、旁车 128 份（帧 1262–1389，含位姿）、图像 128 张；无会话 JSONL/收据——可作静止车投影试读源（128 帧），不能作会话评分夹具。
- **体积外推**：1500 帧会话帧环 ≈ 77 MB（961 帧 49.6 MB 线性外推）；Unity 帧环 1500 帧 ≈ 125 MB + 旁车；故 D1「会话目录约 50 MB」不足，改为 §5.2 硬上限。
- **时延与 K（他项读数，未核）**：板上往返 p50/p90 1.71/1.82 s（JET-001 诊断）→ 若 p95 ≈ 2 s，`k_ret ≈ 12`；以 AC-15 实测为准。
- **板端环境（他项读数，未核）**：JET-001 `-env.json` 的系统 Python、内存与磁盘读数只作暂估，B0a 重读。
- **D3 静止车投影试读**（F27；`load_base_geometry` 直接使用、不施布局；红车遮挡体按 §3.5.1）：锚点 xz 40 m 内 6 辆，状态分布——FRAME-001 128 帧：6 辆 × 128 全 `NOT_IN_VIEW`；attempt 2 Unity 帧环 1500 帧：5 辆全 `NOT_IN_VIEW`、1 辆全 `EXCLUDED_OCCLUDED`；即两份归档对本项候选池的可评分帧数为 0，失败分母 = 全部帧（会话窗口另为 `NO_POSE`，F23）。只以车辆为遮挡体时 attempt 2 末段静止机位有 7 辆车出现 `OK`（6 辆恒 `OK`）、FRAME-001 有 6 辆间歇 `OK`；其中只有 1 辆在锚点 40 m 池内（即上文计入全几何遮挡后为 `EXCLUDED_OCCLUDED` 的那辆，离天底角 > 45°）。从起始位姿合成居中：6 辆投影均 `OK`；离天底角 2 辆 ≤ 45°（约 16°、21°），4 辆 49°–58°——故 §3.6 B/C 派生得 2 辆，并把 P1 改为起始位姿先切静止车。所有静止车读数标 `metadata_unbound`（F25），只作描述。
- **D3 帧身份试读**：两份归档旁车相机位置 vs 真值机身位置逐轴 ≤ 1e-3 m：1628/1628 帧；元数据字节摘要：两份归档均无（F25）。
- **D3 全套加载静态清单**：见 §5.1（只读源码，非插桩）。
- **未核清单**：Unity 主机 → Jetson 可达性；llama-server b11381 的 `response_format` 携带 schema 的请求形状与 `--version` 输出格式（A2(a) 解析式待阶段 B 板上核实，不符即 `S-IDENTITY`）；Python 与 Unity 单调钟是否同钟；全套加载的插桩计数（阶段 A 首次全套核对）；HTTP 有效载荷实际单请求字节（暂估自帧环 JPEG 平均）；`metrics.json` 矛盾原因；B/C 在 Play 实时画面中是否可见（只能 Play 中由操作者按 §3.6 规则判定）。

## 9. D4 修订回应（AR1-1 与 N-5 来源；D3 及更早回应表见 git 历史）

用户 U-D3 选 (a) 并批准 N-5（账本 2026-10-06 U-D3/N-5 条）。D4 只处置「U-D3答复落实」的 D4 范围：AR1-1 原残留与 N-5 来源标注；AR1-2（N-5 后设计层闭合）、AR1-3/5/8/9（D3 闭合）、AR1-4/6/7、§7 (l)–(o) 与证据核实路径/N-4 不触发裁定均不重开，正文未动。N-5 来源：§3.6 新增「采样批准来源」条，引账本 U-D3/N-5 条与「U-D3答复落实」，限制逐条保留、不外推。

| 项 | D3 残留 → D4 怎么改 | 改在哪 |
|---|---|---|
| AR1-1（终止归类） | 漏斗改为按阶段判定的十二类：新增类 0 `ATTRIBUTION_CONFLICT` 与类 2 `INTERRUPTED(query_pending\|presentation_pending\|designation_unavailable, <cause>)`；查询未返回或呈现挂起中遇 `TERMINAL`/日志截断 → `INTERRUPTED`，遇新受理 → `SUPERSEDED(<phase>)`；`cause` 取 `TERMINAL` 行 `reason`（`STATE_REASONS`）或 `log_end`。按 F30 改正 D3 与代码不符处：`none`/`parse_failed`/查询过期均先重试，终态只看 `retry_exhausted` 的 `last_status`，中间尝试不是终态；`instruction_unsupported` 是 `REQUEST_INVALID` 不是样本。A4 补写呈现挂起语义（只挂 `unique`/`ambiguous`、挂起中 `QUERYING`、结果行在呈现时写、epoch 变即丢弃、`result_arrived.status`），不改 Δ 域与检查点 | F30；A4；§3.5.2；AC-5、AC-8 |
| AR1-1（意图） | 选「独立标志」唯一方案：`intent_status` 不是漏斗类，全部样本入漏斗、守恒 = 十二类之和 = 各 `intent_status` 之和；数字一/二/三/误锁/显式比例各在第一步把非 `valid` 归 `NOT_EVALUABLE(no_intent\|intent_unknown)`，不进任何分母；数字二进入 S 前守恒式、误锁分母 = \|S\|、显式比例总体限 `valid` 且每样本两指示量各至多计 1 | §3.5.1；§3.5.3–3.5.5；AC-8 |
| AR1-1（归属/去重/冲突） | 键链 `request_id` →受理行 `epoch` → 查询/结果（按行内 `epoch`，结果行 `request_id` 只核对不作键）→ `designation_id` → 下游事件；L2 重复行按（kind, `designation_id`, `frame_id`）取首行；冲突闭集 C1–C6 入类 0、不进分母；未归属行计 `unattributed_rows`；均只描述、不新增 STOP。夹具逐条列于 AC-8（四种查询未返回终止、两种呈现挂起中断、三种查询中被替换、`designation_unavailable`、重试末态与 `worker_stuck`、两种 `request_id` 异形行、C1–C6、未归属、`REQUEST_INVALID`、两种意图无效、L2 重复、静默错误只计 1） | §3.5.1 (i)–(iv)；AC-8 |

## Contract conformance（核对表）

C11@OpsDiagBindK1K2（2026-10-08，Acceptance / Codex，对Claude Opus实现作异源只读核对）。**C10-1闭合；首退1/1已用。R1@OpsDiagBindK1K2 PASS已由「绑定R1通过消费」采用，本表保留C11只读核对归属。** 候选与完整范围见末节「C11@OpsDiagBindK1K2核对」§1，逐项证据见Ops交接§19及§18；不手抄派生SHA。不跑功能测试、不增改AC、不签独立finding/verdict；“满足”仅为本机代码/合同核对，正式后置缺证保持。

| 条款 | 核对结果 | 依据 / 未闭项 |
|---|---|---|
| AC-1 | 满足 | body/standoff与controller零diff；同名复核R1@OpsScoreDiagK1K4 §2代码侧结论携带。 |
| AC-2 | 满足 | 冻结件/threshold/段式路径零diff；R1@OpsScoreDiagK1K4 §2携带。 |
| AC-3 | 满足 | 单加载/重建运行时代码零diff；旧通过携带；真实板端单加载未验证。 |
| AC-4 | 满足 | hold/SUSPECTED/无观测发布路径零diff；旧通过携带。 |
| AC-5（含修订1） | 满足 | operator_web/controller零diff；旧通过携带，原K/T/Δ语义未变。 |
| AC-6 | 满足 | 六键/status/K收据/deploy_digest零diff；旧通过携带，真实板收据后置。 |
| AC-7（含修订1…5） | 满足 | 适配器/版本/来源加载及部署16路径零diff；旧通过携带。 |
| AC-8（含修订1…3） | 满足 | analyze_play/summarize_ops/原调度零diff；四表/分母/采样未变，旧通过携带；R1-5 OPEN。 |
| AC-9（含修订1） | 满足 | 仅新增标准库types；摘要独立进程/评分调用零改，隔离模块零diff且列入新树focused169（Ops交接§19.2）。 |
| AC-10（含修订1…6现行部分） | 满足 | 正式release_gate/require_gate/require_g4/SshUnit/各stage零diff；诊断新绑定单列修订9；旧通过携带。 |
| AC-10 修订7 | 满足 | summarize_ops及评分测试/play-ops页零diff；评分全批≤3/坏账拒评与旧通过携带。 |
| AC-10 修订8 | 满足 | 短私有ControlPath/计量/释放行为零diff；OSD-R1-1逐字docstring已应用、交接§14.3同步；旧通过携带，真实SSH未验证。 |
| AC-10 修订9 | 满足 | BIND-1…6/Q1=A代码及操作页对准合同；闭表/旧id硬拒、坏账/非法consumed拒、唯一条目及新放行格式、P1/身份记录见Ops交接§18.1–18.3/§19.1–19.3及DiagBindingTests。默认旧id仅直接构造兼容，不许可旧入口；真实条件未验证。 |
| AC-11（含修订1） | 满足 | operator_web/呈现采集零diff，SUB:2两张本人附议携带；提示与用时UNKNOWN。 |
| AC-12 | 满足 | extract_block/scenario_tether及围栏安全代码零diff；诊断页旧20个围栏块逐块字节保持（仅新增现行调用示例），BIND-Q1=A。 |
| AC-13（含修订1） | 满足 | 旧停点全套新增失败0但不绿的限制携带；当前闭集及窄修证据单列修订2，不重判旧通过。 |
| AC-13 修订2 | 满足 | C10-1闭合：三常量/引用收回DiagTestBase/DiagTests/DiagBindingTests，闭集外类零diff。Ops交接§19.2/c10-rework-focused.log对应新测试blob、169 OK；生产零改，原红绿行为按AST等价携带、旧测试哈希不携带，未全套。范围前提成立；C11未重跑红绿；R1§0已在新树独立复算修前红、focused内修后绿，PR-C11-1闭合，窄修替代充分，不记全套通过。 |
| AC-14（含修订1/2） | 证据缺失 | R2 §1/§2及本机DiagTests的失败停依赖/模式/收尾携带；正式3次Play/本人按钮起止/实账反馈NOT_RUN，本轮无Unity或正式资源新增。 |
| AC-15（含修订1/2） | 证据缺失 | 生产measure/收据路由零diff，R2 §2代码侧携带；正式板端报告/收据仍NOT_RUN。 |
| AC-16（含修订1…3） | 证据缺失 | 资产/来源/身份域零diff，R2 §2与Ops交接§7.0代码侧携带；正式板端assets/真实监督未验证，不转诊断原件作证据。 |
| AC-17 | 满足 | geometry_rejected运行时/回归零diff；旧通过携带，不追认旧ACQ/Unity。 |
| AC-18（含修订1） | 证据缺失 | 正式归档/四表/信封/STOP及独立≤1次重放仍NOT_RUN；原摘要一致性逻辑未改，不拿C轮或本人标签代独立证据。 |

AC-14/15/16/18正式证据缺失是既有后置门，不构成本次新增退回。累计AC修订30/新AC0不变；OpsDiagBindK1K2共C2轮（C10/C11）、首退1/1、R1轮/返工0/2；旧Ops/K终局、冻结集、归因与债保持。PR-C11-1及PR-C10-2已由R1核清；PR-C10-1归OSB-R1-1非阻断待办，详见「绑定R1通过消费」。open_items只计设计退修残留。


## 决策记录

| 日期 | 轮次 | 结论 | 理由指针 |
|---|---|---|---|
| 2026-10-08 | R1通过消费 | OpsScoreDiagK1K4 PASS已消费，REVIEW_PASSED；新诊断仍未放行 | 末节「R1通过消费与新诊断前提盘点」§1–4；绑定方案先交实现，窗口后置 |
| 2026-10-08 | SUB3核清与评分上限落实 | DIAG-CONTROL-1 CLASS_2范围内必修；评分全批≤3授权落实；合批新OpsScoreDiagK1K4停点，REWORK_REQUIRED | 本节同名裁定§1–5；AC-10修订7/8，累计28修订/新AC0；新诊断及额外全套未签0 |
| 2026-10-08 | C7@OpsK1K2K3K4 | C6-1满足、C6-2/3未闭；首退1/1不再退回，照交R1；本人保真可复用，替代交R判断 | 最新核对表、末节C7判读及同名C7证据§0–5；零消耗、无新AC/额度/verdict |
| 2026-10-08 | C6@OpsK1K2K3K4 | 首次退回实现；三项不满足，首退1/1；下一C7照交R1 | 最新核对表及同名C6证据§0–5；不新增AC/额度/verdict，零消耗 |
| 2026-10-07 | R1K1K3消费与诊断放行 | R1 PASS已消费；REVIEW_PASSED；诊断交本人一次；CLASS_3后置 | 同名裁定§1–3；正式G1–G5/AC-18不放行 |
| 2026-10-07 | C5@K1K3 | 可交新鲜Review R1@K1K3；IR-K1…K6确认；DIAG续试A已落实待门 | 最新核对表、-C5-K1K3.md §0–4及「DIAG续试授权落实」 |
| 2026-10-07 | R4消费与诊断故障裁定 | R4终局PASS已消费；当前REWORK_REQUIRED；诊断再试待用户 | 同名裁定§1–6；AC-7修订5/AC-16修订1/AC-10修订2；新K1K3修复停点 |
| 2026-10-07 | C4@K1K2K3K4 | 附不满足项照交Review R3，稳定门先行 | 最新核对表及同名C4证据§0–5；首退1/1，N-1全套3/3用尽，无运行放行 |
| 2026-10-06 | D1 | REVISION_REQUESTED | 本节「D1 接受裁定」；AR1-1…9；§7 (h)–(k) 未答 |
| 2026-10-06 | D2 | REVISION_REQUESTED（第二次） | 本节「D2 接受裁定」；6 项残留；交用户范围选择及 (h)–(k)、N-1…N-3 |
| 2026-10-06 | U-D2答复落实 | 用户 §4.2(a) 选择已落实；交构思 D3 | 本节「U-D2答复落实」；保留范围与六项已知缺口，不签 ACCEPTED/合同/额度 |
| 2026-10-06 | D3 | REVISION_REQUESTED（残留裁定，交用户） | 「D3 接受裁定」；AR1-1 漏斗缺项、AR1-2 采样变更待授权；N-4 不触发 |
| 2026-10-06 | U-D3答复落实 | 用户 §4.2(a) 与 N-5 已落实；交构思 D4 | 「U-D3答复落实」；两项原缺口列明，AR1-2 设计层闭合、AR1-1 待修；不签 ACCEPTED/合同/额度 |
| 2026-10-06 | D4 | ACCEPTED | 「D4 接受裁定」；AR1-1 设计层闭合、N-5 来源一致；engineering-v1、AC/schema 冻结；七题及未签额度保留 |
| 2026-10-06 | N-1答复落实 | 用户 §5.1 首签已落实；交 Implementation 阶段 A | 「N-1答复落实」；逐维度一致、首次全套不符即停；六题/未签0保持，不新增额度 |
| 2026-10-06 | 阶段A IR答复 → C1@K1K2K3K4 | 首次退回 Implementation | 「待裁定答复」AC-7 修订 1、AC-8 修订 1/2；「Contract conformance」；完整范围与偏差见同名 C1 证据；首次全套有效 |
| 2026-10-06 | C1返工IR答复 → C2@K1K2K3K4 | 照交新鲜上下文 Review R1 | IR-13…17已裁；35文件与AC逐条核对，AC-7异常IO计量未满足；PR-1/2/7依据见同名C2证据，首退不重开 |
| 2026-10-07 | R2消费 | REVIEW_PASSED；阶段B未放行 | 「R2消费：通过轮归因与阶段 B 前置」；R1-1实现错误已闭，AC-7满足；ACQ R1-4账本CLOSED，其余债保留，六题交用户 |
| 2026-10-07 | B-pre答复落实 | N-2已签、(h)(j)(k)已答；交 Implementation B-pre | 「B-pre答复落实」；授权边界修订1，AC不变；(i)/N-3待B0a核清，B-main未签0 |
| 2026-10-07 | B0a核清 | N-2账/事实已核；完整运行申请仍受环境UNKNOWN阻断，交用户 | 「B0a核清」及§5.2回填；只申请一次零模型只读补核与N-3逐码处置，不签额度/AC/通过 |
| 2026-10-07 | mini操作单IR答复 → C3@K1K2K3K4 | 附不满足项照交新鲜Review，稳定门先行 | 「mini操作单待裁定答复与 CHANGE 申请」及最新核对表；首退不重开，用户口径/AC申请未生效，零消耗 |


### D1 接受裁定（2026-10-06）

**结论：REVISION_REQUESTED。** 主线方向、Jetson 主臂与桌面快层接线可以继续设计；本文尚不是任务合同，`engineering-v1` 尚未生效，不进入实现。§5 全维度仍未签发，本轮 consumed=none。依据：现行 acceptance 细则、workflow §4.2/§4.3/§4.4/§6.1、engineering §2/§4/§6/§9/§11，以及账本 10-06 本项方向条目。完整读取本提案；沿工程继承清单与 SCOPE_GAP 账本核对 ACQ/LOOP/FRAME/JET 来源，并只读定位直接关联接口；这是提案裁定，不是候选核对或独立复核。

#### §7 (a)–(g) 裁定

| 项 | 裁定与依据 |
|---|---|
| (a) | 保留 `Workflow: engineering-v1` 申请。用户本轮明确委托本角色裁定；本项工程接线方向符合主线，不借旧研究门通过。正式路由只在后续 `ACCEPTED` 时生效；本轮不以申请行放宽任何规则。 |
| (b) | **触发 K4，保留 `K1K2K3K4`。** 四类数字是 project-background §3 点名的验证输出，且新建定义与评分器；描述性定位不免除对外指标停点。K1/K2/K3 亦按 §7 保留；不触发 K5。代码先核对/复核再消耗，消耗证据还须另过停点（AR1-9）。 |
| (c) | 采用提案的另一选项：**ACQ-001 保留 `PAUSED` / `IMPLEMENTED_REVIEWED_AWAITING_UNITY`，本项引用其部件与未闭义务**，不恢复、不收 `CLOSED_SUPERSEDED`。本项未接受且承接表不完整（AR1-3），不能现在宣称完成替代；LOOP-001 的关闭另有用户 09-28 明确终止授权，不自动类推。本次不改 ACQ 门、原 verdict、AC-18 `NOT_RUN`、attempt 2 非 verdict 或旧余额。 |
| (d) | **JSON 约束触及推理/解码条件，必须以本项新条件登记并经 K3；不回改 SFT-002 冻结 prompt/parse 或历史结果。** 保留三态及接口 A；P2 两态 schema 不得借用。结果 `model` 块可以设计为 v1 可选扩展，但字段数/名称/类型、旧读写兼容及端到端身份保留须按 AR1-5 补齐后才冻结；“schema 版本不变”不能代替兼容性证明。JSON 约束消除失败仅是假设，不是已验证事实。 |
| (e) | **不加搜索回扫或自动重问。** 依账本 09-28 D.1 与 §2.4，丢失后等待人处置；hold 与 SUSPECTED 的准确状态合同须按 AR1-4 统一。日后扩大行为另回用户。 |
| (f) | 取**仅 `duration_reached` 进入 TERMINAL**的设计方向，适用常驻路径，不把全部 `seg_end` 改成同一终态。其他恢复与“每 Play 单加载/单 run”的冲突须 AR1-7 解决；不能把到点终止会话当成 Unity 按钮已退出 Play 的证明（ACQ `PlayD1裁定2`）。 |
| (g) | IoU 0.3 在当前 scenario evaluation 与 ACQ §3.9 有来源，可作描述性身份判定线；13 s 来自离线窗口，64 px/5 帧和角度/距离桶来自 ACQ §3.10 的申请口径，**不能冒充本条件实测通过线**。0.8 帧比例不是 FAST-001 七结局规则，且缺出处；当前 §3.5 不冻结。按 AR1-1 补唯一算法、完整分母、比较基线与每个数值出处；依 COORD-017，不用移植/申请线停止后续步骤。 |

#### D2 具名退修项

以下是本轮互异残留闭集；构思逐项修订原提案及对应 AC，不交实现自行补合同。

| ID | 原文依据与可操作修订要求 |
|---|---|
| AR1-1 | **四类数字尚不可唯一复算**（§3.5、AC-8）。13 s 内正确帧比例≥0.8 与声称“逐字复用”的 FAST-001 `window_summary` 七类结局冲突（原口径为 `KEPT/D`，三排除类、四判定类）。选定并完整写出本项算法、每类/每桶分母、零分母、不可见/帧缺失/时间窗结束删失、`BOUND_COASTING` 与经 ACQUIRING 再 BOUND 的处理；定义 h 帧及 intended object 离线标识，不用绑定对象倒推指定对象。每个 confirm/指定恰计一次，原始六值与最终捕获结局分列，`ACQUIRE_FAILED` 不重复进比例分子；解析错误/过期/拒绝/未 confirm 亦须可追踪。时间基准和 t_k/t_confirm 来源、time-to-bind/center 的截止、“T_slew + 窗口”的单位及分桶末端/溢出闭集必须明确。给阈值出处与基线；不把数值扩为性能门。 |
| AR1-2 | **真值输入可得性没有原始试读支撑**（A6、§3.5/§8）。scenario 的 scene_adjustments 是局部迁移/删除清单，位置不能单独产生完整车辆投影框；`project_boxes.py::Camera.from_sidecar` 需要位姿/内参且对象还需包络。列出静止 B/C 的身份、几何/实际生效布局/遮挡与逐帧相机来源，红车真值的帧/可见性来源及跨文件绑定规则。提供实际归档只读字段/行数/帧交集/体积/绑定率；ACQ `PlayD1裁定2` (7) 已明示 Unity 环只留末段、会话环只覆盖会话，不能只凭“文件存在”保证同帧评分。来源缺失时输出具名不可评估及分母，不插值造真值、不新增 Unity 采集协议；若需新增采集先回用户。无真数据数字前不冻结输入 schema/尺度（workflow §4.2）。 |
| AR1-3 | **承接缺项且有触发条件被扩大**（§2.5、AC-11）。补 LOOP-001 F3/F8 的原始来源、触发判定、范围内验证与唯一债务入口：本项显式增加呈现延迟，须证明是否进入 worker 等待域；触及则先承接独立在途起点回归。归档评分须承接元数据 hash/时刻一致性，不把旧 F8 承接丢掉。ACQ R1-4 的触发包括扩展延迟/淘汰 k 帧域，本项 Δ 与 R 从128至1500已变化，不能直接写“不在范围”；逐路径证明仍不可达或把 cause/回归纳入拟议范围。K1K3-R1-1 按实际预检/报告复用路径判定，不因 B0 名字相同误指为已承接。保留全部 OPEN 状态、旧失败、清理清单/非 verdict/未运行验收及余额不转用。 |
| AR1-4 | **安全与兼容声明相互冲突**（A1/A3、§2.4/§3.1/§3.4、AC-1/4）。A3 将 SUSPECTED 写成 hold/no-look_at，表和 AC-4 却要求观测与规划器照常；以表中明确的既有 SUSPECTED 语义统一正文，并枚举 raw LOST、no_pointer、BOUND_COASTING、REINIT_REQUIRED、几何拒绝的闭集及每帧 hold 的发布门/失败收据，不将无观测解释成可以发速度。无覆盖场景回退从 default 改 untethered 本身改变 threshold/段式路径的生效场景，不能同时声称所有旧路径语义不变；限定新回退的适用入口、旧配置兼容与预期变化，并写反例验收，不暗改旧默认文件。 |
| AR1-5 | **Jetson K 收据与身份链没有完整生产路径**（A2、§3.2、AC-6/15、§4.1）。`tools/language_latency.py::build_receipt_document` 仍要求 mac+5060，k-receipt CLI 只写两宿主、退出码只认两宿主；该文件又在 AC-13 闭集外。明确单 Jetson 报告如何由生产工具生成/校验/绑定至服务真实身份，覆盖缺报告/hash/代码版本/场景/hz/R/设备/模型不符与拒绝，不手写 JSON 代替生成器；保留旧双宿主决策。原 A2 身份列 mmproj/runtime/quantization 三个新增名称，却称“两字段”；AC-6 又无条件要求 mmproj，使旧 HF 报告失效。枚举字段与条件必需性，核 GGUF、mmproj、固定源码/二进制和 prompt/schema/解码配置身份的来源，不仅相信用户传入 sha；补桥、HTTP 和收据贯通的兼容/错配测试，记录原始 finish_reason/解析错误且不洗掉失败。 |
| AR1-6 | **导入隔离与部署闭集不成立**（A2(d)、AC-7/9、§4.1）。现有 `controller/language_selector.py` 惰性导入冻结 prompt/parse/train_lora，`language_loop.py` serve 分支也导入 tools；禁止整个 controller 导入任意 tools 会把既有合法生产路径判失败。真值隔离须针对 evaluator/gold/truth/评分路径与合法纯推理依赖，枚举可核闭集。冻结 parse.py 本身纯标准库，但 `python3 -I -c "import tools.language_serve"` 未设置源码路径，不能证明所列传板包可导入；给实际部署包结构（含所需包文件）、隔离解释器/源码根引入方式、假服务与缺依赖/超时/坏响应的测试范围。测试只加载本项部署闭集，不借完整桌面环境让断言通过。 |
| AR1-7 | **剧本和单加载约束不可同时按字面执行**（A4/A5、B2、§3.6、AC-3/14、§5）。Δ 是 run 启动参数，P3 同一 Play 的三次 ask 无路径改为0/2/4；写可执行的逐次延迟接口或一致剧本及计次，不用三个 session 偷换一个 Play。非 duration seg_end 保留重建时会再次构造权重，与“每 session 单 run/单加载”冲突：明确哪些恢复可继续且如何保留单加载，哪些计入失败并结束，禁止未授权二次加载。P1 最后一次 red-car ask 补 confirm/捕获观察，P2 不假定语言含混必然是 schema ambiguous（SFT prompt v2 对 car 是普通车类）；剧本只记录实际三态与人工选择。逐剧本重试上限与全局最多2次、共5次的分配/停止规则写一致，原始失败保留。 |
| AR1-8 | **资源/阶段前置不自洽**（B0、AC-13/16、§5/§8）。阶段 A 不能既称全维度0又包含至多3候选全套真实 NanoTrack 加载；把全套所需模型加载/数据回放、执行机器、次数列为阶段 A 待用户另签，不借旧项额度。B0 的服务往返若调用推理计请求、启动导入/服务计相应板操作，残留移动/生成覆盖是写操作，不能列为“只读”；已核清旧板服务已停（JET C2核清§1），不能假定端点在线。分开真正只读事实预检与获签后写入/启动/查询，未核设备/链路维度只作暂估，按 engineering §9 先核实再申请。AC-16 板 sha 应在有授权的阶段B核实，阶段A只读已有来源。代码传输请求/响应有效载荷、准备/清理/故障重试、完整按钮Play墙钟、板计时起止与新增磁盘均需有明确合计口径和硬上限；“约50MB”不是封顶。诊断产物需新项自有身份及运行证据，B-C2-RESULT 已于10-06按推荐答复（推送前新入账），原违规/UNKNOWN保持；新JSON诊断额度只属JET-001，不覆盖本项、不以本轮引用追认。 |
| AR1-9 | **证据停点/STOP/候选范围需与现行规则对齐**（§6/§7、AC-13）。engineering §4 明定“消耗产出的证据另过停点”；阶段B只有接受核清不足，明确证据自证/核对与独立复核的路径，按 workflow §4.4 判断新轮资格，代码无diff不虚开新轮也不豁免证据停点。按 COORD-017 为每个 STOP 写出处/比较基线、判定所用运行条件、原因码与停止本次/全部后续的处置，随信封给用户确认；现有未确认处置不生效。§4.1 全文件diff闭集不能排除实现必改的提案/状态板或接受设计同步；枚举功能修改与必要文档的允许范围，协调变更仍按真实diff检查。可派生 HEAD/sha/run目录从git与来源解析，D2 新写内容不用手抄标识。 |

#### needs_user：§7 (h)–(k) 原题保留

下列逐字保留 §7 原题及推荐/理由，**未答、未授权，不交 supervisor 代拍**；D2 先修合同，阶段B信封题只能在代码独立复核通过、预检事实核清后提请。AR1-8 的阶段A模型加载/回放额度亦待用户首签，不能从题(i)阶段B签发推定。

- (h) 阶段 B 读数入 `docs/unity-test-log.md` 按正式用户验证还是 workflow §4.3.2 诊断通道（推荐正式，理由：这是主线数字的首次产出，应可被引用）；
- (i) §5 阶段 B 信封签发（`R1@K1K2K3K4` 通过后）；推荐在 D2 预算修正、预检核清与代码复核通过后按确定的逐维度上限签发，理由：现申请值存在 AR1-8 的计量/前置缺口，当前不能签发执行。
- (j) 5060 备用臂启用条件（推荐：仅当板上收据不过资格线或 B0 可达性失败且 Jetson 侧当日不可修复时启用，启用即另签右列）；理由：保持用户已选 Jetson 主臂且不借备用臂扩大未签额度。
- (k) 阶段 B 执行机器：会话与快层在 Unity 主机（用户 Mac），板上服务由谁启动（推荐：用户本人经既有 SSH 启动，角色只给逐字命令；理由：Unity 主机 → Jetson 的 SSH/网络放行归用户本机设置）。

交接：Ideation 仅修本提案为 D2，逐条回应 AR1-1…9，再交 Acceptance。§7用户题不以缺省/推荐视为已答；不恢复其他暂停项、不跑模型/板端/Play、不签额度。正式设计与实现证据不变；没有新增 BC/AC、生效合同或复核 verdict。

推送前同步：已完整核读账本10-06「用户答复 B-C2-RESULT 按推荐；签发『C2 Q4 加 JSON 约束』…」的新条目，保留该会话账本/日志与JET交接。JET的新诊断尚待接受合同落实与另会话执行；本D1不接管该任务、不转用其额度，JSON约束效果仍未验证，AR1-1…9与本项零消耗不变。

open_items: AR1-1, AR1-2, AR1-3, AR1-4, AR1-5, AR1-6, AR1-7, AR1-8, AR1-9


### D2 接受裁定（2026-10-06）

本节保留 D2 当轮判断与原题。U-D2 范围选择已由用户答复，下文等待该选择、禁止派 D3 的当轮交接由「U-D2答复落实」替代；(h)–(k)、N-1…N-3 仍未答，推荐与理由原文保持。

**结论：REVISION_REQUESTED（同范围第二次）。** §9 回应不能代替正文合同；AR1-4/6/7 的原退修问题闭合，AR1-1/2/3/5/8/9 各有具名残留（9 → 6）。未 `ACCEPTED`，engineering-v1 申请不生效；不交实现、不冻结 AC/schema、不签额度。D1 (a)–(g) 除下表明确解释处外保持。此为接受侧提案决策，不是 `C` 候选核对或独立复核；不填写 Contract conformance、不签 verdict。

范围与依据：完整读取 D2（含 D1 裁定与 §9），按 workflow §6.1 读取当前结构/全部交接、工程继承清单、完整 SCOPE_GAP 账本及相关 parked 来源；沿 `tools/eng_fast/replay.py::window_outcome/window_summary`、`tools/eng_acq/e2.py::guarded_window_summary`、`tools/dist_data/bind_layout.py::load_base_geometry/apply_layout`、`project_boxes.py::project_instances` 和直接关联会话/桥/发布门接口核对设计可执行性。全局 block/release 来源已核：ACQ R2-1 已配对 release，当前无未 release 的消耗门 block；开工文档机检通过，0 消耗性 + 2 零消耗交接。没有运行功能测试、模型、SSH、Unity，未写 runtime；consumed=none。

#### AR1-1…9 闭合核对与残留闭集

表中「闭合」只指设计退修要求已回应，不表示实现或验收通过。未闭项沿用 D1 ID，不新造复核 finding/分级；用户选定后才可交构思修订。

| ID | D2 判断 | 依据与仍须修订的内容 |
|---|---|---|
| AR1-1 | 未闭（部分修订成立） | §3.3 仿真帧轴、去掉 0.8、原始六值分列与出处表成立。但 §3.5.2 没覆盖未 confirm 而会话停止/新指令覆盖、`BOUND_COASTING` 至截止未找回再转 `TRACK_ENDED` 的唯一漏斗终态；样本只列 ask，P2 的 respecify 也发新查询且带 intent，未定义是否计样本。§3.5.3 无首发布帧时无结局；§3.5.5 未写捕获成功率、误锁率的准确分母、不可评估/删失排除规则、所有零分母输出及绑定在数字一/三间的去重。存活不是 FAST 原算法的「逐字复用」：原 `window_summary` 起点为全部可见帧，`window_outcome` 在窗口尾有未决 miss 时继续扫描窗口外至恢复/切换/31帧/序列末端；D2 改为每指定起点，却只写「段末未决」，又把 start 的 BOUND_SAME 从原 track_id 比较改成对象 IoU，缺跨窗口尾规则。H-6 所称同一空窗守卫实际抛 `EmptyWindow`，不是返回 `TRUTH_GAP`；须明确转换。写明本项改编与唯一状态优先级、帧缺口、观察/删失终点、误锁时长窗口和归属。P2 的「与意图 IoU 最大者」若使用离线真值会驱动人工 confirm，违背真值只进评分；改成仅看运行时图像的预登记人工选择，离线 IoU 留评分。同步 respecify 的 intent/延迟接口或删除不支持的参数。 |
| AR1-2 | 未闭（试读数字已补） | F22–F24/§8 的行数、体积、交集与无旁车限制有具体数字，不再以文件存在推定可评分。但 F24 已说明几何 `scene_adjustments_applied true`，§3.5.1 又直接对该 AABB `apply_layout`；生产函数要求未调整几何（`unadjusted` 参数，在 original_xz 唯一匹配），不能重复正施 default 迁移。本项布局与 default 同值时直接复用已核布局，或明确逆施再正施的生产链及失败条件。`project_instances.extra_blockers` 要 `(id, 像素框, 相机系深度)`，现仅写红车框，未列深度来源/换算。几何/实际布局绑定须取归档冻结来源，不凭评分时可变覆盖文件证明历史布局；给实际静止车投影试读状态、对象唯一映射与失败分母后才冻结相关输入，不能在 C1 核对轮补新合同。保留红车/静止车真值与几何近似的区别。 |
| AR1-3 | 未闭（承接路由大部成立） | H-1 的会话呈现延迟不进入 worker 等待域，结合 AC-5/11 空闲与零 diff 证明可接受；不以「预计 p95」免债。H-3 按触发纳入 cause 回归、H-4 按实际 candidates 路径不触发成立，旧 OPEN/余额/非 verdict 保留。H-2 却只核 frame_id/时刻与 JPEG sha，未核元数据字节 sha：篡改旁车 camera_position/内参且保留 frame_id/时刻会改变静止车投影而通过所列检查。原 F8（LOOP R7 §3）要求保存 JSON 对索引 json_sha256 并核时刻。AC-8 写「篡改旁车 sha」但正文未定义可信元数据摘要来源。枚举当前归档可用的摘要/快照链与缺失处置，纳入同帧同刻但改位姿/内参的回归；无可信来源不得假报 F8 已承接或闭债。 |
| AR1-4 | 闭合（设计层） | A1 保持旧回退，standoff 要求显式覆盖且逐值匹配，AC-1 有缺省 threshold 反例；A3/§3.4/AC-4 对 SUSPECTED ok/无观测、几何拒绝、raw LOST、ACQUIRING/REINIT 的声明已统一；显式 hold 收据填补原路径空缺。实际逐帧不变式与门失败收据待实现及 K1/K2 复核，不凭表格签安全通过。 |
| AR1-5 | 未闭（生产路径已补） | A2/§3.2/AC-6/7/15/16 已纳入单宿主生成器、服务自算资产与错配拒绝，旧报告条件兼容成立。但 A2(d) 只枚举六个键名与全有/全无，不列类型/值域/摘要格式，§9 所称「类型枚举」不属实；runtime_build 如何与固定源码/二进制匹配也未定。服务 `serve_code_sha256` 被记录而未列会话启动核对条件；客户端 git_head 相等不能证明板上实际部署闭集正确。写明本项预期部署清单摘要与服务自算摘要的比较链，prompt/schema/decode 身份来源、六键类型和值域、固定 build 的核实方式及错配反例。保留未知字段旧读者丢弃的限制，新条件只由新代码消费，不回改历史报告。 |
| AR1-6 | 闭合（设计层） | A2(e) 包含真实标准库导入闭包，合法冻结 parse/prompt 与 train_lora 路径有区分；§9 已指定临时源码根 + `-I -S`，现有 language_serve 自插源码根可供部署隔离入口；AC-7/9 明确假服务失败与 import 闭集。实现时该隔离检查须只摆部署清单文件、显式引入该临时根并调用新分支，不用桌面 sys.path/site-packages 偷补依赖；此为原要求释义，不新加 AC。 |
| AR1-7 | 闭合（原单加载/逐次剧本问题） | A4/AC-5 逐 ask Δ，A5/AC-3 由既有 model_loader 注入复用模型，重建最多2次与全局≤2/每剧本≤1重试口径可执行；P1 末次 confirm/观察已补，P2 不再假定 ambiguous。准许 D2 的 backend_fatal/rebuild_limit 终止分类作为 D1(f) 为解决加载冲突的补充，不把全部 seg_end 改 TERMINAL、不放宽既有发布门。P2 样本/人工选框与 respecify 参数残留归 AR1-1，不能因本行闭合漏掉。 |
| AR1-8 | 未闭（阶段拆分成立） | B-pre 与 B-main、全套单独待签、板sha移B、旧JET额度不转用已修。但 §5.2 的20MB只算代码与回传日志，未覆盖HTTP上传图像/查询响应等有效载荷；板墙钟按SSH会话之和，后台服务跨SSH断开存活的时段未计；新增磁盘按前后du差不能限制暂存/日志/失败件峰值。补双向有效载荷总量、服务驻留墙钟起止（或明确每次SSH结束必停服务）、峰值占用及硬上限/记录方式。§5.1 全套加载项仍暂估，应先完成所列零消耗清单核对，再申请 N-1；跟踪 focused/复核解释器须沿全局数据根只读环境，不能借此申请在仓库虚拟环境装lap或把JET SUB额度转用。本轮不签任何额度。 |
| AR1-9 | 未闭（STOP表已补） | §6.2 逐码条件/出处/处置及随信封确认成立。§7 的无 PLAY_GOVERNING diff 路径却用「R1脚本 + C2 + 用户目检」代替对新消耗证据的独立复核：工程§4要求消耗证据另过停点，AGENTS完成规则仍需独立复核。代码无diff时不得虚开R2，但须由复核角色在原文件的具名证据核实小节检查新工件、账/操作单、评分绑定并给证据结论；C2不得自签该角色的结论。若认为现行开轮资格不容该证据路径，明确回用户裁定，不在提案自行豁免。§4.1 文档闭集漏正式设计同步 `docs/phase1-single-drone-design.md`，与接受职责冲突，补入并仍按真实候选diff核。§3.5.6 的C1冻结输入schema亦违反核对轮不得新增/改写合同；试读返回须先走独立合同答复且冻结，再整理稳定候选交C1。 |

#### §7 (l)–(o) 接受题

| 项 | 裁定 |
|---|---|
| (l) | **是，归 K1**：hold收据从无到有、reason字段取值变化是发布收据协议变化；K2安全行为检查仍保留，合并停点无需改名。AC-4证明格式、通道/失败结局与三reason，不能以沿用通道名豁免。 |
| (m) | `STATE_REASONS` 为闭集，新增值须同步生产写者/桥校验、部署包、runtime README、操作单与枚举验证用例；现行 `tests/test_language_bridge.py` 有遍历常量的检查，核对真实diff时不得排除它。本项不改Unity协议，当前只读来源未显示Unity消费这些Python原因码；不据此虚列新的Unity读者。外部未枚举消费者发现后回接受，不自行扩大闭集。 |
| (n) | **不另记 SCOPE_GAP**。F17 尚属疑似，非独立复核finding；不能自行造finding/账本行。A6以指定/query唯一键计数的范围保持，AR1-1把去重键与冲突处置写全；不从事件条数反推指定数，不在本项顺手修重复日志。 |
| (o) | **本轮不另立排查或修运行时评估器**。F23只记录两种口径的矛盾与原因UNKNOWN，不能推出旧 `C_track` 错误或修复义务；本项明确不用旧metrics，按自有评分合同产出描述读数。将来若消费旧metrics才按实际来源另申请范围；原失败与未知不改写。 |

(m) 指出的枚举测试及正式设计若进入候选，须在归属表写清允许路径；当前未冻结文件闭集，不授权在核对轮临时排除混入文件。

#### needs_user（逐题；仅用户可答，未签维度仍0）

**U-D2 范围选择**：workflow §4.2：同一提案第2次 `REVISION_REQUESTED` 后「必须上交用户二选一：(a) 接受当前范围并逐条列出已知缺口；(b) 关闭为负结果记录」。本项账本仅有10-06起草/宿主方向授权，未见绑定 LOOP-002 的 `supervisor_decision_envelope`；JET/ACQ 的信封不覆盖它。交接 Owner=用户，不交supervisor代选、不自行派D3。推荐 **(a) 保留当前接线方向并显式接受上表6项已知缺口**，理由：3项已闭合、残留属于同范围合同可判定性，尚无证明此方向不可行的负结果；这项范围选择不等于额度首签、Unity通过或接受角色已 `ACCEPTED`。用户若允许继续修订，应明确处置上述缺口后才可能冻结合同；未答不进入实现。选(b)则回接受落终止与保留义务，不冒充验收。

以下 (h)–(k) **原题逐字保留**，推荐不构成答复；阶段B项须待代码复核与预检核清才提请执行：

- (h) 阶段 B 读数入 `docs/unity-test-log.md` 按正式用户验证还是 workflow §4.3.2 诊断通道（推荐正式，理由：这是主线数字的首次产出，应可被引用）；
- (i) §5 阶段 B 信封签发（`R1@K1K2K3K4` 通过后）；推荐在 D2 预算修正、预检核清与代码复核通过后按确定的逐维度上限签发，理由：现申请值存在 AR1-8 的计量/前置缺口，当前不能签发执行。
- (j) 5060 备用臂启用条件（推荐：仅当板上收据不过资格线或 B0 可达性失败且 Jetson 侧当日不可修复时启用，启用即另签右列）；理由：保持用户已选 Jetson 主臂且不借备用臂扩大未签额度。
- (k) 阶段 B 执行机器：会话与快层在 Unity 主机（用户 Mac），板上服务由谁启动（推荐：用户本人经既有 SSH 启动，角色只给逐字命令；理由：Unity 主机 → Jetson 的 SSH/网络放行归用户本机设置）。
- N-1 阶段 A 停点全套额度。推荐先由获授权的后续零消耗准备核清 §5.1 全套加载闭集、机器/解释器，再按每候选一次/候选数/加载/回放/墙钟/磁盘确定上限首签；理由：现加载项仍暂估，不能把缺项当已签，亦不能借旧项额度。
- N-2 B-pre 只读预检。推荐在设计范围确定且到达其前置门后，单签 §5.2 B-pre（只读SSH≤2、每次≤10min、ping≤10包，推理/写入/启动0）；理由：Unity主机链路与板环境尚未核，B-main依赖读数，预检本身不是板执行无限许可。
- N-3 STOP 缺省处置（随 B-main 信封）。推荐 AR1-8 修正资源口径后，逐码确认 §6.2（含S-RING记录NO_POSE并继续，非强保证帧覆盖）；理由：COORD-017禁止接受角色让未确认处置自行生效，不把描述性阈值变性能门。

交接：用户决定 U-D2 与用户专属题；supervisor 仅转呈/核查本报告，不代答、不启用执行，不拉起下一写角色。ACQ暂停、旧OPEN债、attempt2非verdict/AC-18未运行、清理义务与旧余额均保持；JET现行诊断合同交接保持。本批只改本提案裁定/状态与状态板，不修改正式设计、实现、复核文件或授权账本。

open_items: AR1-1, AR1-2, AR1-3, AR1-5, AR1-8, AR1-9

### U-D2答复落实（2026-10-06）

**结论：按用户 workflow §4.2(a) 选择保留当前范围，逐条列明六项已知缺口，允许构思角色继续修订为 D3。** 这是用户选择的落实，不是新的 D 轮退修或 `ACCEPTED` 裁定。Overall 保持 `REVISION_REQUESTED_ROUND_2`、Lifecycle 保持 `ACTIVE`；engineering-v1 申请未生效，不冻结 AC/schema，不交实现、不签任何额度。

授权依据：`docs/authorizations.md` 2026-10-06「P1-ENG-LOOP-002 — 用户就 D2 第二次退修选 U-D2 (a)：保留当前范围、接受 6 项已知缺口并继续修订（supervisor 会话代录）」。该条用户原话为“没问题，这样整个系统说的通，选A继续修订吧”。结合该条上文的 U-D2 二选一与 D2 六项残留，原话明确允许选(a)后继续修订；supervisor 读法与原话一致，没有将范围选择读成合同接受或执行许可，本轮不更正账本、不另代写用户原话条目。双层方向共识保留，开放词汇检测器前置筛选仍只是未来可选新项，不纳入本项。

#### 六项已知缺口与 D3 处置路径

以下沿用「D2 接受裁定」的原 ID、依据及修订要求；本表是交接索引，不替代该节完整残留原文，不新增或豁免义务。

| ID | 已知缺口 | 继续修订的处置（完整要求见 D2 同 ID 行） |
|---|---|---|
| AR1-1 | 四类数字尚无覆盖全部样本/结局的唯一算法；P2 人工选择存在真值驱动风险 | 补 ask/respecify、未确认/覆盖/停止、coasting未找回与无首发布帧的终态；明确分母、零分母、删失、去重、跨窗口尾与空窗转换；人工选框仅用运行时图像，离线 IoU 留评分；统一参数接口。 |
| AR1-2 | 已调整几何可能重复施布局，遮挡深度及历史布局绑定缺失；静止车投影尚无实际状态读数 | 明确几何生产链、失败条件、红车遮挡深度来源/换算及归档冻结布局绑定；补对象唯一映射、投影试读状态与失败分母，保留几何近似区别；未满足前不冻结相关输入。 |
| AR1-3 | 元数据字节没有可信摘要链，同帧同刻改位姿/内参仍可能通过 | 枚举归档可用摘要/快照链和缺失处置，纳入同帧同刻篡改位姿/内参的回归；无可信来源不声称 F8 已承接或闭债。 |
| AR1-5 | 六身份键缺类型/值域，runtime_build与资产匹配未定；板上部署摘要只记录未比较 | 补六键类型、值域、摘要格式及固定 build 核实；明确预期部署清单与服务自算摘要比较链、prompt/schema/decode 来源及错配反例，保留旧读者丢字段限制。 |
| AR1-8 | 双向 HTTP 有效载荷、后台服务驻留墙钟与磁盘峰值未计；全套加载仍暂估 | 补总量/起止/峰值的硬上限与记录口径；先核全套零消耗清单再申请 N-1，解释器沿全局只读环境约定；旧 JET 额度不转用。 |
| AR1-9 | 无代码 diff 时新消耗证据缺复核角色核实；候选范围漏正式设计，C1 冻结 schema 越界 | 明确原复核文件具名证据核实路径或回用户裁定，不虚开轮或豁免独立性；补正式设计允许路径；试读后先独立合同答复并冻结，再整理候选交 C1。 |

构思角色只修订本提案正文、对应拟议 AC、§9 回应及必要状态指针，逐条说明六项如何处置，再交 Acceptance 审 D3。AR1-4/6/7 的设计层闭合与 §7(l)–(o) 裁定保持；本轮不重开已闭项、不改范围。D3 尚未审查，不预签接受结论；若修订需要改变范围、用户专属题或资源边界，具名回用户，不借本次选(a)推定授权。

#### 未答用户题（needs_user）

唯一原题入口为「D2 接受裁定」的 `needs_user（逐题；仅用户可答，未签维度仍0）`：(h)、(i)、(j)、(k)、N-1、N-2、N-3 七条及其推荐/理由逐字保留。U-D2 已答，不再列为待用户决定；其余题不由本轮、构思或 supervisor 代答，未签维度仍为 0/不做，仍按各题前置门提请。接力报告七题详情引用该原文小节，避免另写一套漂移的题目。

本轮仅提案/状态落盘，consumed=none：未跑功能测试、模型、SSH、Jetson、Unity，未写 runtime。ACQ 暂停、旧 OPEN 债、attempt 2 非 verdict、AC-18 NOT_RUN、清理义务与旧余额不转用均保持；JET 现行交接不接管。全局消耗门来源及文档机检已核，当前没有未 release 的 block。


### D3 接受裁定（2026-10-06）

本节保留 D3 当轮判断及 `open_items`；U-D3/N-5 已由用户答复，等待两题、禁止派下一轮的当轮交接由下节「U-D3答复落实」替代；原七道用户题仍未答。

**结论：REVISION_REQUESTED（残留裁定，交用户；不自行发出下一轮退修）。** 六项中 AR1-3/5/8/9 在设计层闭合；AR1-1 的样本闭集仍缺合法终止路径，AR1-2 的技术修订成立但 P1 采样变更未获授权（6 → 2）。不签 `ACCEPTED`，engineering-v1 申请未生效，AC/schema 不冻结，§5 各维度仍0。用户 U-D2(a) 只授权保留范围并修订 D3，不是任意改采样或无限退修授权。依据 workflow §4.2 与账本10-06「用户就 D2 第二次退修选 U-D2 (a)」；本项无绑定的 supervisor 决策信封，JET/ACQ 的 D1 不转用，故 Owner=用户。

读取范围：完整 D3 正文、AC-1…18、§9 及 D1/D2/U-D2裁定；当前结构与全部交接、engineering/workflow/acceptance细则、工程继承清单和完整 SCOPE_GAP 账本；相关 parked 限制与正式设计 §2/§3/§4/§5；沿 FAST 窗口算法、ACQ 空窗守卫、几何加载/投影接口、LOOP F3/F8 原始 finding、会话 stop/worker/frames_processed 路径及全套加载测试源码核对。全局 blocks/releases 来源覆盖全部 reviews 与账本：唯一实质 block 为 ACQ R2-1，已顺序配对 release；当前0消耗性+2零消耗，Gate-echo一致。这是提案决策，不是 C 核对轮或独立复核；Contract conformance 不填，无 verdict/新 finding/债务销账。

#### 六项残留逐条核对（设计层）

| ID | D3 判断 | 正文与 AC 依据 / 残留 |
|---|---|---|
| AR1-1 | 未闭（主要修订成立） | A4/AC-5 已给 ask/respecify 同参数；§3.5/AC-8 已补跨窗口尾、空窗转换、分母、零分母、无首发布帧及只凭预览人工选择。但受理 ask 后在 QUERYING 停止、尚无结果/确认的样本，十类均不能容纳：第1类要求新 ask/respecify 替换，第2类要求结果失败码，第7类限定待确认。真实 `language_loop._action_stop`→`stop` 会写 `worker_abandoned`/TERMINAL，未必有结果；A5 的 duration/backend 终止亦不能保证结果。另 §3.5.1 缺 intent/未知 intent 把“样本”标 NOT_EVALUABLE，却未说明它是否仍入十类守恒、各数字分母如何排除。须在原正文与 AC-8 给查询未返回/延迟呈现中终止的唯一归类、意图无效作为独立可评分标志还是漏斗类的唯一选择、request_id→重试query_id→确认designation_id的归属与冲突处置，并用对应夹具核守恒；不靠脚本作者补解释。 |
| AR1-2 | 技术修订成立；采样变更未授权 | §3.5.1/AC-8 改为归档场景副本绑定段 manifest、相等布局直接 `load_base_geometry`，不重复正施；红车遮挡三元组含相机深度，静止几何近似与红车真值分列。F26/F27/§8 已列对象唯一性、投影状态、全帧失败分母及候选可居中读数，§3.6/AC-10 有派生与不足2辆即停。余项是下节 N-5：P1 不只是同一组样本改序，红车/B 的计划次数改变；未获用户决定前本行不闭合。 |
| AR1-3 | 闭合（设计层；旧债保持） | F25/H-2/A6/§3.5.1 明写旧归档无元数据摘要；新增运行时字节摘要与旁车比较，时刻/位置/场景另交叉核；AC-5/8 分别验证摘要生产、同帧同刻姿态/内参/位置篡改与 null 缺口，S-ARCHIVE 保留正式异常停止。旧归档 metadata_unbound 只描述，未声称已修 F8；运行时摘要与帧关联的实际正确性交 K1/K4 实现和复核验证。 |
| AR1-5 | 闭合（设计层） | A2(a)(d)(e)/§3.2/AC-6/7/9 已定义六键类型/值域、规范 JSON、二进制自报build与资产sha锚点、含清单自身的部署摘要、桌面重算→报告→收据→当刻服务比较链与错配用例；旧六键全无兼容和旧读者丢新键限制保留。实际板上 version/schema 请求形状仍为阶段B前置假设，不把他项读数当证据。 |
| AR1-8 | 闭合（设计层；额度未签） | §5.2/AC-7/10/14 已补 HTTP 双向载荷、SSH 双向文件量、前台服务起止/断SSH前释放端口、驻留被板墙钟覆盖、部署/日志及主机归档峰值口径、重放额度。§5.1 静态清单对照两个 NanoTrack 真实构造入口、CSRT入口、Carrier数据根/依赖跳过条件成立；本机数据根不存在且opencv包metadata为5.0.0.93，与其口径相符。不是实跑/插桩计数；N-1仍须用户首签，首次全套不符即停。focused/复核沿全局只读数据根解释器约定；该环境在执行机器不可用时报告阻塞，不安装lap、不借旧项额度。 |
| AR1-9 | 闭合（按下节规则适配解释） | A6/§3.5.6/§7 已把 schema 冻结移到 ACCEPTED，试读不符先合同修订再C1；§4.1 允许正式设计同步；AC-18/§7 由复核角色独立核新证据而非C2代签，按 PLAY_GOVERNING diff 分路。N-4不触发，尚无实际证据停点通过。 |

AR1-4/6/7 与 §7(l)–(o) 已有裁定保持；本轮不因读码新增 AC，不改构思正文/拟议 AC。上述未闭要求仍属原具名残留，供用户选择后的构思修订使用，不授权当前直接派下一轮。

#### §7 证据核实路径裁定（N-4 不触发）

**容于现行规则。** workflow §4.4 原文为“新复核轮只在 … 于 PLAY_GOVERNING 上非空时开启；为空时禁止开轮”，限制的是新代码复核轮；engineering §4 同时要求“消耗产出的证据另过停点”。§7/AC-18 的原文件具名小节由独立复核角色检查新工件并给证据结论，满足后者而未新编轮号，不是在无diff时虚开R2。此为两条现行义务的合并解释，不修改工作流基础设施，不调用仅适用于 D2b finding 的“回归核实”特例，也不建立例行纯闭环轮。

适用边界：C2仍完整按 §4.3.3 读候选diff、AC及证据，不只核摘要；复核角色只核已复核代码生成的新证据及信封/操作单/STOP/H-2/布局绑定，≤1次零模型重放须用户签在B-main，不能把“零模型”当免费授权。无diff小节不改R1代码verdict或通过候选机读指针，不声称新代码被复核；给具名AC证据满足/不满足结论后交接受汇总。发现数字/结论错误、失败路径或RED_LINE依 §4.4 分级与路由，不得以“不计轮”豁免阻断；如需修代码或冻结操作单，形成新候选，开轮资格/计数运行时从复核文件解析，不保证永远叫R2。无diff不产生新的 passed_candidate（D2b闭合特例不在本项）；同代码证据候选的文档差异依 §4.5 处理。

#### P1 采样变更裁定（N-5）

D2已提交正文 §3.6 的序列是 red→B→C→red（red2/B1/C1）；D3 是 B→C→red→B（red1/B2/C1）。正式Play次数/计划命令总数/几何候选池不变，**对象样本分配、切换方向与观测顺序改变**，并新增 SKIPPED_NOT_IN_VIEW 的采样选择。因此属于数据/采样协议实质变化，不能用 F27 只读试读或 U-D2“保留范围”追认；F27 的合成居中投影也不是实时画面可见的证明。本轮不批准，不由supervisor代选。保留作者提议供用户比较，未来执行以用户明确选择后经接受落实的正文为准。

#### needs_user（D3 接力入口）

- **U-D3**：按 workflow §4.2 二选一：(a) 保留当前接线范围并接受上表 AR1-1/AR1-2 两项已知缺口，明确允许构思下一轮处置；(b) 关闭为负结果记录。推荐(a)，理由：残留6→2、四项设计缺口已闭，尚无方向不可行证据；仍需用户单独决定N-5，不签AC/轨道/额度。
- **N-5 P1采样**：批准D3的 B→C→red→B 与只凭实时预览跳过规则，或保持D2对象次数并另拟可执行序列（含同样的真值隔离规则）。推荐批准D3，理由：起始先观测静止车有F27几何支持、可减少离锚点后的不可见，但实际可见性/有效样本数仍未知；必须接受red2→1、B1→2及跳过产生的选择限制，不作为性能比较。两选项均涉及采样，整题归用户。
- **(h)、(i)、(j)、(k)、N-1、N-2、N-3**：各题原文、推荐与理由逐字保留于「D2 接受裁定」`needs_user（逐题；仅用户可答，未签维度仍0）`，接力报告逐题引用；当前共九道待用户题，N-4不触发、U-D2已答，不混入待答列表。D2推荐中的“暂估/待修”是当轮依据；本轮§5.1清单和§5.2计量修订已核，仍未签N-1/B-pre/B-main/STOP，且B-main原有代码复核与预检前置不变。

交接：用户先决定U-D3/N-5，其余七题依原前置门提请；supervisor只转呈/核查，不代答、不拉起后续写角色。接受收到明确答复后落实，再按授权交构思或终止；未答维度0/不做。正式设计/里程碑证据未变，ACQ暂停、旧OPEN债/清理义务/attempt2非verdict/AC-18未运行/余额不转用均保持，JET交接不接管。本批只写本提案裁定及状态板，未跑功能测试、模型、SSH/Jetson、Unity，未写runtime；consumed=none。

推送前同步：远端新增账本10-06「用户答复 C2JSON-DRIVER_SELF_CHECK_STOP：JSON 约束诊断到此结束」已快进合并、原话保留。依交接须与现实一致规则，就地把JET已答事项的交接改为接受落实；不在本轮消费其门、合同或证据，不拉起该角色。

open_items: AR1-1, AR1-2

### U-D3答复落实（2026-10-06）

**结论：按用户 workflow §4.2(a) 选择保留当前接线范围，列明 D3 两项已知缺口，落实 N-5 批准并交构思修订 D4。** 本次是答复落实，不是新的 D 轮退修或 `ACCEPTED`；Overall 保持 `REVISION_REQUESTED_ROUND_3`、Lifecycle 保持 `ACTIVE`，engineering-v1 申请未生效、AC/schema 不冻结、§5 各维度仍 0。

授权依据：`docs/authorizations.md` 2026-10-06「P1-ENG-LOOP-002 — 用户就 D3 退修选 U-D3 (a) 继续修订，并批准 N-5 D3 的 P1 采样顺序（supervisor 会话代录）」。用户先说“继续修”，再于独立 N-5 选项题选择“批准 D3 顺序 (Recommended)”；该选项明确展示红车 2→1 次、B 1→2 次、实时画面看不到就跳过、数字只作描述不做性能比较。结合 U-D3 二选一与 D3 两项残留，supervisor 读法与原话一致；本轮不更正账本、不另代写用户原话条目。继续修订仅到本次 D4，不是无限退修或执行许可。

#### 两项已知缺口与 N-5 闭合影响

以下沿用 D3 原 ID 与完整要求；不回改该轮 `open_items: AR1-1, AR1-2`，不把设计层闭合写成实现/验收通过。

| ID | D3 已知缺口 | 本次答复落实后的处置 |
|---|---|---|
| AR1-1 | 样本漏斗未覆盖查询尚未返回/延迟呈现中终止；缺/未知 intent 的可评分性与分母未唯一化；标识归属与冲突处置未写全 | 仍未闭。D4 在 §3.5 原正文与拟议 AC-8 明确上述终止的唯一归类；选择意图无效作为独立可评分标志或漏斗类的一种一致方案，逐一说明漏斗守恒与四类数字分母/排除；写全 request_id→重试 query_id→确认 designation_id 的归属、去重和冲突处置，并列相应夹具要求。不得留给实现者补解释。 |
| AR1-2 | 布局/遮挡/投影试读技术修订已成立，唯一残留为 P1 对象次数/顺序及跳过选择未获用户批准 | N-5 现已获批，原残留在设计层闭合。§3.6 的 B→C→red→B（red1/B2/C1）与只凭实时预览的 SKIPPED_NOT_IN_VIEW 规则成为获准采样方案；Play 次数、计划命令总数、候选池不变。实际可见性、跳过次数及有效样本数仍未知；跳过不成样本、须逐次列出，数字只描述、不作性能比较。 |

N-5 不证明 F27 合成居中等于 Play 实时可见，不豁免 B/C 派生不足 2 辆即停、真值隔离、布局/帧身份绑定、几何近似与红车 Unity 真值分列或完整失败分母；技术依据仍是 D3 同 ID 行及 F26/F27、§3.5.1/§3.6/§8、AC-8/10。本轮仅落实该唯一授权缺口，没有新增试读、证据或债务销账。

#### D4 处置范围与交接

构思仅修本提案正文、相应拟议 AC、§9 回应及必要状态指针：补齐 AR1-1 原残留，在 §3.6/§9 标明 N-5 采样批准来源并保留限制；AR1-2 不再作为待用户批准项。D3 已闭 AR1-3/5/8/9、此前 AR1-4/6/7、§7(l)–(o) 与证据核实路径/N-4 不触发裁定保持。出 D4 后交 Acceptance 审查，不交实现；需改变范围、采样、用户专属题或资源边界时具名回用户，不能借本次选(a)或 N-5 推定新授权。

#### 未答用户题（needs_user）

(h)、(i)、(j)、(k)、N-1、N-2、N-3 七题及推荐/理由原样保留，唯一原题入口为「D2 接受裁定」的 `needs_user（逐题；仅用户可答，未签维度仍0）`；接力报告逐题引用该节，不另改写题目。D2 推荐中的“暂估/待修”属当轮依据，D3 已核清清单和计量修订但未签额度，仍按各题前置门提请。U-D3/N-5 已答，不再待用户；N-4 不触发。构思、接受或 supervisor 均不代答七题，未答/未签维度仍 0/不做。

本轮仅提案/状态，consumed=none；未跑功能测试、模型、SSH/Jetson、Unity，未写 runtime。正式设计/里程碑证据未变；ACQ 暂停、旧 OPEN 债、attempt 2 非 verdict、AC-18 NOT_RUN、清理义务与旧余额不转用均保持，JET 交接不接管。全局 reviews 的 blocks/releases 与缺陷账本已核：唯一实质 block ACQ R2-1 已顺序配对 release，当前无未 release 的 block。

### D4 接受裁定（2026-10-06）

本节保留 D4 当轮判断与 `open_items`；N-1 已首签，等待首签的当轮交接由下节「N-1答复落实」替代，其余六题及前置门保留。

**结论：ACCEPTED。轨道裁定：本工作项按 `Workflow: engineering-v1` 执行，自本裁定生效。** AR1-1 的原残留在设计层闭合，§3.6 N-5 来源与账本一致；其余已闭项及 D1/D2/D3 已有裁定保持，不重开。`open_items` 仅计设计退修残留；七道用户题仍未答，§5 未签维度均为 0。本轮不是 C 核对轮或独立复核，不填写 Contract conformance、不签代码 verdict、Unity 通过或 DONE。

依据：本轮用户明确派发 D4 提案裁定；workflow §4.2/§6.1、engineering §2–4/§6/§8–9/§11、acceptance 细则；账本 2026-10-06 本项方向、U-D2(a)、U-D3(a)/N-5 三条。读取完整当前提案、全部既有裁定、当前结构及全部交接、工程继承清单/完整缺陷账本和相关 parked/正式设计；只读核对 `language_loop.py` 的受理、重试、确认、指定、结果写入、worker 及 stop 路径。全局 reviews 的实质 blocks/releases 为 ACQ R2-1，已按文件顺序配对 release；当前 0 消耗性 + 2 零消耗、Gate-echo 一致。本轮零功能测试、零模型、零 SSH/板操作、零 Unity、零 runtime 写入，consumed=none。

#### D4 具名闭合核对（设计层）

| 核对项 | 裁定与具体依据 |
|---|---|
| AR1-1：终止与重试 | 闭合。§3.5.2 类 1/2 覆盖查询未返回与呈现挂起中的替换/TERMINAL/日志末尾，类 2 另接 `designation_unavailable`；类 3–5 区分重试末态和 `worker_stuck`，不是把中间 none/parse_failed 当最终失败。源码 `_designate_failure`/`_resume_designate_retry`/`_handle_designate_outcome`/`stop` 与 F30 相符；A5 的新终态是已裁定的拟议行为，不声称现行代码已实现。AC-8 明列相应夹具与十二类守恒。 |
| AR1-1：意图与分母 | 闭合。§3.5.1 以 `intent_status` 独立于漏斗，全部受理样本守恒；§3.5.3–3.5.5 各数字先排除 no_intent/intent_unknown，数字二进入 S 前另给守恒，误锁以 S 为分母、显式比例限定 valid 且每样本至多一次。AC-8 核两类无效意图、排除/零分母和静默错误去重；不把意图喂给决策。 |
| AR1-1：归属与冲突 | 闭合。§3.5.1(i)–(iv) 给受理 request_id→epoch→查询/结果→designation_id 及指针 epoch 的链；结果 request_id 为 null、或为 confirm 的 ID 时不作主键，符合 `_issue_designate(None, None)` 与 `_action_confirm` 的实际路径。C1–C6、未归属行和重复事件的处置具名、冲突不进分母；AC-8 每项有夹具要求。冲突计数只描述、不新增 STOP；旧日志重复疑点不转为新 finding。 |
| A4 / AC-5：呈现挂起 | 闭合。源码 `_handle_designate_outcome` 顺序为返回检查→interpret→候选/预览→结果写盘→记录呈现时刻→AWAITING_CONFIRMATION；失败先走重试。A4 将成功候选的呈现尾段延后，挂起保持 QUERYING，`_action_confirm` 现有状态门拒绝确认；新 ask/respecify 与 stop 都改变 epoch，丢弃旧呈现可与现有旧 epoch 结果隔离一致。AC-5 核上述状态/写盘/取消及 worker 空闲；实现须满足该条而不能仅加 sleep。Δ 域、参数、K 检查点/起点、预览代码、LanguageWorker 零 diff 与原停点均不改，是原 A4 合同细节；Δ=0 等价性仍须实现和复核证明。 |
| AR1-2 / N-5 来源 | 保持设计层闭合。§3.6 的 B→C→red→B、red1/B2/C1 与实时预览跳过规则逐项符合账本 10-06 U-D3/N-5 及「U-D3答复落实」；限制全部保留。未证明实时可见性/有效样本量，不外推次数、采样或额度。 |

#### 冻结合同与执行边界

冻结本提案 §1–6 的目的/范围/接口/限制、§4 AC-1…18（日期已填）、§4.1 功能及文档闭集，以及 §7 停点；§5 **只冻结申请口径，不签发额度**。输入 schema/尺度按 A6、§3.5.1/§3.5.6 在此冻结，原始依据为 F22–F27/§8 的真实归档只读读数；实现后试读若不符，按既有 A6 先回接受合同修订，不能留给 C1 冻结或改合同。四类数字及现行数值为描述性口径，不设性能门；本轮没有提交 D7 可调数值范围，不授权 supervisor 修改指标、采样、安全条件或预算。

K1/K2/K3/K4 合并 `K1K2K3K4`：代码先自证→`C1`→新鲜上下文独立复核，再申请/放行阶段 B；消耗证据再自证→`C2`→AC-18 独立证据核实。保持 D3 无 diff 证据核实裁定，N-4 不触发；开新轮与轮号按实际 PLAY_GOVERNING diff 和复核文件解析。§6.2 已逐码登记出处/基线、运行时条件及处置，移植/申请线只描述；N-3 未答，STOP 缺省处置未生效。正式验证、信封及用户目检仍是后续门，不申请 UNITY_NA。

ACQ 的 PAUSED、原门/verdict、attempt 2 非 verdict、AC-18 NOT_RUN、清理义务与旧余额不转用保持；LOOP/FAST/FRAME/JET 的 OPEN 债、旧负结果/UNKNOWN 不销账，JET 诊断产物不进本项证据，未用额度不转用。本次同步正式设计；没有里程碑或实现证据变化，不更新 implementation-status 或复核文件。

#### needs_user 与下一交接

(h)、(i)、(j)、(k)、N-1、N-2、N-3 **原题、推荐及理由逐字保留**，唯一原文为「D2 接受裁定」的 `needs_user（逐题；仅用户可答，未签维度仍0）`。本轮不代答；U-D2/U-D3/N-5 已答，不重复申请。D2 的“暂估/待修”是历史依据：D3 已核 §5.1 静态清单和 §5.2 计量，仍非实跑/插桩事实，也不是首签。

当前 Owner=用户：先按 N-1 首签阶段 A 停点全套/加载/零模型回放/机器/次数/墙钟/磁盘额度，落实后才交 Implementation 阶段 A；任何未签维度继续为 0。N-2 依其前置门另签 B-pre；(h)/(i)/(j)/(k)/N-3 依代码独立复核、预检核清等原前置门转呈，不提前启动 B-main、板服务或 Play。supervisor 只核查/转呈，不能代答这些题、首签信封或据 ACCEPTED 推定执行许可。

open_items: none

### N-1答复落实（2026-10-06）

**结论：用户 N-1 首签与冻结 §5.1 逐项一致，落实后交 Implementation 阶段 A。** 这是授权答复落实，不是新 D 轮、C 核对轮或独立复核。Overall 保持 `ACCEPTED`、Lifecycle 保持 `ACTIVE`，实现仍 `NOT_STARTED`；D4 的 engineering-v1、AC-1…18、输入 schema、文件闭集及停点不改，不签额外额度、不签实现/Unity/验收通过。

#### 授权原话、读法与冻结表核对

唯一执行授权来源：`docs/authorizations.md` 2026-10-06「P1-ENG-LOOP-002 — 用户首签 N-1 阶段 A 停点全套额度（按提案 §5.1 表；supervisor 会话代录）」。用户原话为“N-1 按表签”；账本上文已逐行展示 §5.1、静态清单口径与首次全套不符即停条款。以账本指向的 D4 接受版本运行时取出 §5.1，与落实前磁盘正文逐字比较，完全一致；不在本文手抄可派生 commit/工件标识。结合该明确语境，supervisor 读法未扩大用户原话；数值与维度核对如下。账本无需更正，本会话不代写用户原话条目。

| §5.1 维度 | 用户已签内容与对应核对 | 裁定 |
|---|---|---|
| 执行机器 / 解释器 | MacBook Air；现有 `.venv-yoloe` 原样只读使用，不装包；`ENG_DET_DATA_ROOT` 不设；不在仓库环境装 `lap` 或其他依赖，不借 JET SUB 额度 | 一致，仅所列机器/环境 |
| 停点全套 | 每候选 1 次、≤ 3 候选；成功、失败、重试共账 | 一致，不重置计数 |
| NanoTrack-v2 | 每次全套真实 ONNX 构造静态预期 2；账本上限 ≤ 2 | 一致；上限不取消首次实际不符即停 |
| det-assoc / CSRT | det-assoc 冻结检测器 CPU 加载 0；CSRT 构造尝试静态预期 2（上限 ≤ 2）、实例 0；基线既有错误按 AC-13 区分 | 一致；实例0见账本上文及冻结表 |
| 其他模型 | 每次全套 YOLOE/DINOv2/VLM/HF 0 | 一致 |
| 零模型数据回放 | A6 对 attempt 2 与 FRAME-001 两份既有归档只读评分，每候选 ≤ 2 次 | 一致，仅既有归档确认；不写 runtime |
| 墙钟 | 每次全套 ≤ 15 min | 一致 |
| 新增磁盘 | 证据与夹具 ≤ 20 MB（阶段 A 总额度，不按候选重置） | 一致 |
| 其余 | scenario/session/run ID、Play、VLM、板、5060、API、GPU、下载、pip 均 0；Unity/Play=否；不含云 | 一致，未签缺项0 |

**首次全套不符即停（已随 N-1 用户首签确认）**：§5.1 加载数来自只读源码静态清单，非插桩实测，不能写成已实跑符合。Implementation 在阶段 A 首次全套核对实际加载与该清单；任何不符即停止阶段 A 后续执行、保留当次日志及实际用量、回用户，不补跑、不换解释器/设数据根/安装依赖来消除差异；该次仍计入每候选一次及≤3候选共账。未知如实记未知，不推定符合。候选/回放/墙钟/磁盘耗尽或需越界也回用户；本次不把 N-1 的停止条款扩签为阶段 B §6.2 的 N-3 缺省处置。

#### 阶段 A 实现交接与停止边界

Implementation 开工先依 AGENTS/workflow §6.1、engineering 与实现细则读取当前结构和全部交接；本项合同必读 §0–8，重点 §2.1 A1…A9、§2.5 H-1…H-12、§3 全部接口/算法/操作单、§4 AC-1…18/§4.1、§5.1、§6–7，及 D1/D2/D3/D4 适用裁定、本节和授权原条。复用前先读 `implementation-status.md` 工程继承清单/完整缺陷账本，再沿 §2.5 读取原提案/复核/证据与相关 parked 义务；正式设计读本项条目及相应架构/控制/安全章节。不借 JET 诊断件、旧余额或暂停项授权。

实现只在冻结 §4.1 归属范围内完成阶段 A；本机资产只读核实按 AC-16，A6 旧归档确认与 B/C 派生按既有 A6/§3.6。归档确认与冻结 schema 不符或 B/C < 2 辆时停并交接受，先按既有合同修订路径处理；不得把问题留给 C1 补合同。开发期只跑 focused；跟踪 focused/复核仍遵全局数据根只读解释器约定，该环境在执行机器不可用就报告阻塞，不安装、不借本次全套环境授权改约定。全套只按本次 N-1，输出入 `-tests.log`，区分基线既有失败与本批新增失败，不带 `-v`，已知本批失败先修复及相称复测，不能交明显失败中间版。

停点路径：Implementation 在 `docs/evidence/P1-ENG-LOOP-002-K1K2K3K4-handoff.md` 具名「稳定候选四条件自证」小节按 AC 逐项列证据，覆盖 workflow §4.3.1 四条件、K1/K2/K3/K4 各触发、承接声明/未验证风险及 §5.1 实际用量；准备 §3.7 所列阶段 A 工件与完整候选 diff/改动文件。提交并推送稳定候选后停止依赖其结果的后续实现，交 Acceptance `C1@K1K2K3K4` 只读核对，再交新鲜上下文 Review `R1@K1K2K3K4`。独立复核返工按现行规则直接回复核；轮号、资格与次数上限按实际 diff/复核文件解析，不由本节预签通过。

阶段 A 的 AC-14/15/18 与 AC-16 板端部分为阶段 B 未执行项，明确记 `NOT_RUN`，不以本机替身/归档试读或代码通过冒充满足；不申请 `UNITY_NA`。N-2 B-pre 与 B-main、Play/板服务/5060/下载/安装/云均未签，不能启动；后续仍须代码独立复核通过、接受按 workflow §4.5 放行、相应用户签发与预检事实核清，消耗证据再走 §7/AC-18 的自证→C2→独立证据核实。

**Consuming=no**：AGENTS 定义按创建/消耗 scenario/session/run ID、Play 配额或 API 预算判定；阶段 A 均为0，本机停点模型构造与只读归档评分不改变该列，但必须守已签 N-1 信封。全局仍0条消耗性+2条零消耗活跃交接、Gate-echo一致；全局 reviews 的 blocks/releases 与缺陷账本均已核，实质 block ACQ R2-1 已顺序配对 release，无未 release 阻断。ACQ暂停、旧OPEN债、非verdict/AC-18未运行、清理义务及余额不转用保持，JET交接不接管。

#### needs_user（原题、推荐及理由原样保留）

N-1 已答并落实，不再申请；N-4 不触发。下列六题逐字取自「D2 接受裁定」needs_user，仍由用户决定、未签0/不做，不由接受/构思/supervisor代答。D2 的“暂估/待修”保留为当轮依据；D3/D4 已核清清单与计量但不使 B-pre/B-main 生效，仍按各题原前置门分阶段转呈。

- (h) 阶段 B 读数入 `docs/unity-test-log.md` 按正式用户验证还是 workflow §4.3.2 诊断通道（推荐正式，理由：这是主线数字的首次产出，应可被引用）；
- (i) §5 阶段 B 信封签发（`R1@K1K2K3K4` 通过后）；推荐在 D2 预算修正、预检核清与代码复核通过后按确定的逐维度上限签发，理由：现申请值存在 AR1-8 的计量/前置缺口，当前不能签发执行。
- (j) 5060 备用臂启用条件（推荐：仅当板上收据不过资格线或 B0 可达性失败且 Jetson 侧当日不可修复时启用，启用即另签右列）；理由：保持用户已选 Jetson 主臂且不借备用臂扩大未签额度。
- (k) 阶段 B 执行机器：会话与快层在 Unity 主机（用户 Mac），板上服务由谁启动（推荐：用户本人经既有 SSH 启动，角色只给逐字命令；理由：Unity 主机 → Jetson 的 SSH/网络放行归用户本机设置）。
- N-2 B-pre 只读预检。推荐在设计范围确定且到达其前置门后，单签 §5.2 B-pre（只读SSH≤2、每次≤10min、ping≤10包，推理/写入/启动0）；理由：Unity主机链路与板环境尚未核，B-main依赖读数，预检本身不是板执行无限许可。
- N-3 STOP 缺省处置（随 B-main 信封）。推荐 AR1-8 修正资源口径后，逐码确认 §6.2（含S-RING记录NO_POSE并继续，非强保证帧覆盖）；理由：COORD-017禁止接受角色让未确认处置自行生效，不把描述性阈值变性能门。

本轮 consumed=none：只更新本提案、正式设计的授权状态指针与状态板；不运行功能测试/模型/归档评分、SSH/Jetson/Unity，不写 runtime，不改变合同/AC/schema/门结论或新增额度。下一接手角色为 Implementation（阶段 A），交接请求与进度只见状态板 Active handoffs。

## 待裁定答复（阶段 A 实现读法 IR；先于 C1，2026-10-06）

来源唯一为 `docs/evidence/P1-ENG-LOOP-002-K1K2K3K4-handoff.md`「待裁定」IR-1…12。按 engineering §2 与 acceptance 细则先答复实现合同问题，再按答复后的合同做 C1；原 AC/条款及历史读数保留。本节没有新 AC，不改变目标、硬件、采样、主指标定义、阈值、STOP 或信封。合同解释不能替代代码/证据满足。

| IR | 裁定及适用边界 |
|---|---|
| IR-1 | **不触发 A6 schema 停止条件**。归档工件 41 项对照中 40 项一致，唯一 6/7 差异来自 §8「车辆遮挡体、末段静止机位」与实现「车辆+红车、全 1500 帧」的描述读数；字段/绑定失败率与 B/C 派生资格没有冲突。两种读数和范围均保留，不把 6 改成 7 或宣称该项对照一致；旧归档不是验收证据，不据此关闭 F8。无需修订 A6/schema。 |
| IR-2 | 接受以常驻代限定 designation_id 的解释，见 **AC-8 修订 1**。这是编号复用的消歧，不扩大样本/分母、也不免除原 epoch 归属。 |
| IR-3 | **部分接受，逐项边界见本节下文**；无真值帧时刻退用段日志不接受（§3.3/§3.5.1 已明确唯一来源），评分时长和分列要求照原文。源码中实现了算法不等于最终 JSON 已输出相应数字。C1 的 AC-8 偏差不以本条释义豁免。 |
| IR-4 | 接受共享常量位置，见 **AC-7 修订 1**；不准 controller 直接导入 llama_adapter，AC-9 闭集保留。 |
| IR-5 | 接受该 OpenAI 兼容包装作为 A2(c) 已列的阶段 B 待核假设；schema 字节及摘要以实际请求对象为准，非 b11381 已验证事实。失败仍走 S-IDENTITY/S-RECEIPT，不借假服务证明真实服务通过。 |
| IR-6 | **不接受缩窄干净工作树**。§3.2 收据/会话重算前与 §3.6 放行均要求工作树干净；忽略的 runtime/outputs 本来不进 git status，但 tests/文档等未提交改动不能被三条代码路径过滤掉。保留既有条款，交实现修复（C1-AC6）。 |
| IR-7 | 接受 jetson 不合格收据拒启；与 AC-15「退出码 8 不进 Play」及 §3.2 一致，不改旧两宿主行为。 |
| IR-8 | 接受常驻专用 hold_receipts 与 detail.reason 的位置：三值均随 body_safety_hold 收据可核；顶层 reason 与规划器既有格式一致。段式显式 hold 不加收据，AC-2 旧路径保留。 |
| IR-9 | 终止后不恢复状态、不发新查询及 state_changed 丢弃呈现符合 A4/A5；designation_unavailable 的实际原因标签见 **AC-8 修订 2**。受理行/confirm/去向仍须沿原 e_s 归属，不能借 stop 后 epoch 变化丢失 confirm；此生产路径留作预复核关注。 |
| IR-10 | 接受所列退出码、两个有界 timeout 参数、expect-assets 多余键与 version 非 0 拒启、启动时算一次部署摘要；均为既有启动/拒绝接口的实现读法，不给额外运行授权。旗标/version/health 真实板端兼容性仍待阶段 B 核实。 |
| IR-11 | **不接受访问日志漏记豁免**。AC-7 明写逐请求请求体/响应体字节，§5.2 双向总字节是资源账；坏请求/未支持方法不能按「极少」省略，也不能用声明长度冒充实际字节。C1-AC7 按既有条款返工。 |
| IR-12 | runtime/README.md 属 §4.1 允许文档 diff，且 §7(m) 要同步字段/事件/原因说明；本候选仅改该入库文档，没有运行时数据写入。因此不回退该文件。接受本轮仍不写 runtime/。 |

### AC-7 修订 1（IR-4；解释 A2(d) 常量位置与 AC-9 隔离）

DECODE_CONFIG 的唯一定义允许在纯标准库 `tools/eng_loop2/deploy_digest.py`，`llama_adapter.DECODE_CONFIG` 引用同一对象；controller 只经 AC-9 已允许的 deploy_digest 重算。常量内容、规范 JSON 摘要、实际发送配置及逐键身份链仍按 A2(d)/AC-6/7；不允许两份独立定义漂移。证据沿 `tests/test_llama_server_adapter.py::DeployDigestTests.test_decode_config_is_the_deploy_digest_object` 与两端摘要比对。原 AC-7 不删改。

### AC-8 修订 1（IR-2；解释 §3.5.1(ii)/(iii) C6 的编号域）

designation_id 是 ResidentCore 实例内编号；每行常驻代 = 该行之前 resident_loop_started 行数。指定/下游键为（常驻代, designation_id），重复事件键为（kind, 常驻代, designation_id, frame_id）；C6 只在同一复合键归入两个样本时成立。不同常驻代重复编号不算 C6。受理 request_id、e_s、查询/结果、confirm 与 pointer_bound 仍遵守 §3.5.1 原归属链；不得用复合键跨样本借指针。原样本集合、冲突闭集及各数字分母不变，AC-8 的 C6 与归属夹具按此解释核对；原 AC-8 不删改。

### AC-8 修订 2（IR-9；解释 §3.5.2 类 2 的 unavailable 原因）

受理 confirm 后指定不可用仍属于 `INTERRUPTED(designation_unavailable, <实际 reason>)`：常驻不存在为 resident_loop_absent，追平时终止为 session_terminal。仅原因标签据实区分；不增加漏斗类、不改优先级、意图与分母。事件与其 confirm 仍属该样本 e_s，不允许因终止时增 epoch 而失去归属。原 §3.5.2 与 AC-8 保留。

### IR-3 逐项读法边界

- 同一 sequence 可有多个事件，按文件行序取先后；E 取界限行之前最后 frames_processed 帧。仍须核 C2 受理 epoch 严格递增，不能排序掩盖日志冲突。
- f_p 只在 s 的原指针 epoch 内选；pointer_bound 帧之后至同 track_id 的 segment_retired.to_frame_id（含）作为帧范围可以接受，前提是 pointer_bound 本身确属 e_s/常驻代，不能取全文件的下一条其他样本指针。
- 30/52 帧按帧号截止，捕获同帧优先级 f_p > acquire_failed > E > 截止可接受；C2 相邻两受理行都冲突、C3 不用 presentation_discarded 作查询 epoch 来源、worker_abandoned 按 L_s..X_s 记录均为既有规则消歧。
- results 与 journal 无共同文件行序时，确认过期行须先限 e_s，再用呈现 query_id 或受理 confirm 的 request_id 核对；结果 request_id 仍不是样本键。coasting_timeout 必须在 f_p 前且同指定键，重复行取首行。
- 布局不绑定/不相等的静止车排除，不把其几何结果当可评估；缺 manifest effective_scenario_sha256 归 layout_unbound 可接受。数字二进入 S 前的布局排除须分列并守恒，不修改 S/D/误锁分母。显式运行时终态计数仍照 §3.5.5，不借布局排除隐去失败。
- H-2 依 (1)–(4) 原判据核对；无副本时静止车已经 layout_unbound，跳过 (4) 只能作为无可评分布局的描述计数，不能将其视为通过身份链。**无真值行时段日志时刻仅可列诊断，不能用于四类数字时长/截止/窗口**（§3.3、§3.5.1）。
- 偏轴/斜距按 §3.5.5；time-to-center 可并列从 f_p 与 h 起算，但必须实际输出时长与三种结局，不能以分类计数替代。13 s 闭区间端点由原帧轴/时间窗判据决定，不增容差或舍弃端点规则，浮点边界留复核核实。
- ACQ §3.10 描述口径与本项漏斗口径分开；误锁收据限样本指针 epoch/WRITTEN 类别，不能混入其他样本。command_invalid 的输出键拼写不改 REQUEST_INVALID 不成样本的语义。
- 意图闭集与非字符串 intent_unknown 可接受；derive-bc 的相机约定须符合仓库坐标、对象名去变体编号不猜颜色。B/C 派生 <2 停止及仅实时预览选 confirm/reject 的既有规则保留。
- **红车 Unity 真值与静止车几何近似分列报告、不合并同口径**保持 §3.5.1 原文；此项与最终 time-to-center 输出、指针归属、时刻回退的满足性见核对表，未被本节改写。

## C1返工读法答复（IR-13…17；先于 C2，2026-10-06）

来源：`docs/evidence/P1-ENG-LOOP-002-K1K2K3K4-handoff.md`「待裁定（C1返工新增）」。先裁以下读法，再填写本轮核对表；不新增 AC、不改写既有合同义务、样本、算法、阈值、信封或 STOP。代码与证据满足性另见核对表；接受读法不等于豁免异常路径。

| IR | 裁定与既有依据 |
|---|---|
| IR-13 | **本轮是 C2@K1K2K3K4（C1 首退后的第二次代码候选核对）。** AC-18/§7 与 D3/D4 历史预记的阶段 B「C2」按 workflow §4.3.3 的实际连续计数理解为后续下一 C 轮；如届时无插入轮则为 C3@K1K2K3K4，届时从实际记录解析，不提前保证编号。原 AC-18/历史正文不回写；代码 R1、阶段 B 独立证据核实及按 PLAY_GOVERNING diff 判开轮资格的义务均保持。 |
| IR-14 | 接受真值缺口的保守读法，依据 §3.3/§3.5.1 及已裁 IR-3：段日志时刻只诊断，不补四类数字。存活的 E 无真值时刻、且已知真值帧未能证明越过窗尾时，记 TRUTH_GAP(no_pose)；中心未达成且没有真值时刻证明完整观察到截止时，记 CENTER_CENSORED，已有真值证明截止则 CENTER_NOT_REACHED；Δ_eff/time-to-bind/center 的所需端点时刻缺失输出 null，Δ 桶为 NO_POSE。不得将未知时刻当窗口完整或成功。 |
| IR-15 | 接受所列十二字段及声明长度/实际字节分离，依据 AC-7、§5.2 与 IR-11。未读/未解析部分不能以 Content-Length 补算，request_body_complete=false 与 error 须据实；HTTP/0.9 响应无头可记头0，畸形声明拒绝与计量分支未知 POST 读体后404不改旧 HF 分支。**不接受把异常调用已传输的部分字节按0计的豁免**：逐请求双向实际字节义务保持，现实现的读写返回后加数是否漏部分 IO，见本轮 AC-7 与预复核 PR-7。431 未解析的声明不能假报体完整，也不能由字段设计推出整项计量已满足。 |
| IR-16 | 接受 AC-8 修订2 的归属消歧：只对原 epoch 无样本可归的 designation_unavailable，向前找最近受理 confirm；其间至少有 TERMINAL，且无新的受理样本行、designation 或 designation_unavailable，才回归 confirm 的原 e_s。其余保持原 epoch 归属/不可归属计数与 C5 冲突判据；不跨新的 ask/respecify 借确认，不改漏斗类/优先级/分母。生产序列夹具是证据，独立复核仍须核其边界。 |
| IR-17 | 接受全工作树未跟踪文件计入 dirty，依据 §3.2/§3.6 与已裁 IR-6：git status --porcelain --untracked-files=normal 无路径过滤；任何非忽略目录（含 docs/tests）未提交内容均不干净。忽略文件依 gitignore 不入 status，不新设豁免目录。 |

上述五项已答，无待用户合同选项；(h)–(k)、N-2、N-3 六题仍原样见「N-1答复落实」needs_user，按其原前置门处理，未签0。本轮 consumed=none。


## R2消费：通过轮归因与阶段 B 前置（2026-10-07）

本节保留通过轮消费时的事实与原题；N-2/(h)/(j)/(k) 的后续答复及现行执行入口见「B-pre答复落实」，不再重问四题。

**裁定：阶段 A Overall = `REVIEW_PASSED`，Lifecycle = `ACTIVE`。** 独立结论唯一来源为 `docs/reviews/P1-ENG-LOOP-002.md`「R2@K1K2K3K4」PASS及其 `passed_candidate`；本角色完整读两复核轮、适用合同/核对表、自证和未验证项，依 workflow §4.6 机械消费，不新开 C/R、不复判 CLASS_2、不自签复核。AC-7更新为满足；AC-14/15/18与AC-16板端仍 `NOT_RUN`，未申请/附议 `UNITY_NA`，缺阶段B Unity/硬件及独立证据核实，不签 `DONE`。

### 归因、用量与债务

- R1-1：CLASS_2、依据 `BC-7`（engineering §2 对应 AC-7）→ **实现错误1**；R2 §2生产路径具名回归修前红/修后绿已核实闭合。`IN_SCOPE_NO_BC`/本项新 `SCOPE_GAP`/`上轮漏检`/`上游漏检`/`RED_LINE`均0，不从C2照交归为上游漏检。PR-1/2非finding；PR-3/4/5由R1核实、PR-7归入R1-1，不另造债。
- 度量：C两轮、退回1次（不满足：AC-6/7/8/10；阶段B证据缺失未导致另退）；K1K2K3K4复核两轮、返工1次/上限2，未触发冻结集；工程AC解释修订3条（AC-7修订1、AC-8修订1/2），新AC0，本次新增/改写合同0；研究BC新增不适用。
- N-1用量保持交接「R1返工候选」§5.1：全套2/3、归档回放累计3次（各候选2/2、1/2、0/2）、证据约0.25 MB；本次0。R2判窄修替代充分，未跑全套、不记本候选全套通过；首次全套及CSRT拆分已由用户认可，不重置额度，不转用旧项余额。
- H-3 / ACQ R1-4：原复核R1@K1K2K3 §3的误报cause缺陷由本项AC-17修复（`geometry_rejected`），本项R1 §2读码/具名回归 `tests/test_language_loop.py::Loop2ContractTests.test_geometry_rejected_is_its_own_cause_not_slew_timeout` 核实、R2携带，裁定账本 `CLOSED`；唯一入口 `docs/implementation-status.md`。不改变旧ACQ候选/verdict、暂停/Overall、AC-18 NOT_RUN或非verdict尝试，恢复仍由用户决定。
- H-2 / LOOP F8：本项R1核实新评分路径摘要/时刻/布局绑定及篡改回归，只承接新Play归档；原lap-samples工具未修、旧归档无摘要、新正式归档未有，原F8仍 `OPEN`。LOOP F3、FAST R1-2、ACQ K1K3-R1-1、FRAME R1-3及JET两条OPEN均保持；本次不新增SCOPE_GAP或release。

### workflow §4.5 放行前置核对（零消耗）

| 前置 | 当前事实与裁定 |
|---|---|
| 已接受设计与代码独立复核 | D4 engineering-v1有效；R2 PASS已消费，代码前置门满足；正文/原题中历史“R1通过后”按本停点最终通过轮理解，不要求重跑R1。 |
| 版本/工作树对应 | 本轮开工运行时从复核文件解析通过候选，核其为HEAD祖先；`git diff --name-only <解析值>..HEAD`仅current-status、supervisor-dispatch、同名review，`git status --porcelain --untracked-files=normal`空，无代码差异。符合§4.5文档差异边界，但不等于采集已发令。 |
| 每次Play的严格操作单门 | 冻结操作单§1.1要求HEAD逐字等于解析候选，当前主树有后续文档提交，尚不满足该更严格检查；§1.2/1.3/1.4及当轮HEAD/status须在实际采集发令前重核、写Unity日志。本轮不改冻结操作单，不以文档兼容替代其等值门。 |
| 全局消耗性门 | 全局reviews完整机读blocks/releases及账本核对：ACQ R2-1顺序配对release，无未release实质block；轨道0消耗性+2零消耗，Gate-echo一致。没有block不等于执行授权。 |
| N-2 / B0a事实 | 设计/代码前置已满足，可转呈N-2有限B-pre首签；本轮未签、未操作板。预检文件尚未产出，Unity主机链路/板环境未知；B-main依engineering §9须待读数核清并回填。 |
| B-main / 人验 / 证据停点 | (h)–(k)、N-3与B-main仍未签/未答；真实旗标/version/schema、板端计数与半包/复位、真实缓存加载、新归档身份链未验证。B-main后仍须AC-15合格收据、AC-16板端资产、自有Unity/硬件证据与AC-18独立证据核实；B证据C/R轮号按IR-13与实际diff解析。 |

**仅确认代码前置门满足并转呈用户题，不签 B-main/Play 放行。** B-pre也须用户单签后才可执行；B-main/STOP须B0a核清后按确定逐维度上限提请，不把暂估、缺项或推荐当已签。supervisor核查F2不一致已知悉：复核提交由supervisor原样推送后可达，原结论/候选未改变；出处为状态板2026-10-07同名Log及派发日志，不影响通过轮消费。

### needs_user（六题原文、推荐与理由原样保留）

原文唯一来源为「D2 接受裁定」needs_user，N-1已答/N-4不触发，不重问。下列逐字转呈，均归用户，不在supervisor代拍闭集：

- (h) 阶段 B 读数入 `docs/unity-test-log.md` 按正式用户验证还是 workflow §4.3.2 诊断通道（推荐正式，理由：这是主线数字的首次产出，应可被引用）；
- (i) §5 阶段 B 信封签发（`R1@K1K2K3K4` 通过后）；推荐在 D2 预算修正、预检核清与代码复核通过后按确定的逐维度上限签发，理由：现申请值存在 AR1-8 的计量/前置缺口，当前不能签发执行。
- (j) 5060 备用臂启用条件（推荐：仅当板上收据不过资格线或 B0 可达性失败且 Jetson 侧当日不可修复时启用，启用即另签右列）；理由：保持用户已选 Jetson 主臂且不借备用臂扩大未签额度。
- (k) 阶段 B 执行机器：会话与快层在 Unity 主机（用户 Mac），板上服务由谁启动（推荐：用户本人经既有 SSH 启动，角色只给逐字命令；理由：Unity 主机 → Jetson 的 SSH/网络放行归用户本机设置）。
- N-2 B-pre 只读预检。推荐在设计范围确定且到达其前置门后，单签 §5.2 B-pre（只读SSH≤2、每次≤10min、ping≤10包，推理/写入/启动0）；理由：Unity主机链路与板环境尚未核，B-main依赖读数，预检本身不是板执行无限许可。
- N-3 STOP 缺省处置（随 B-main 信封）。推荐 AR1-8 修正资源口径后，逐码确认 §6.2（含S-RING记录NO_POSE并继续，非强保证帧覆盖）；理由：COORD-017禁止接受角色让未确认处置自行生效，不把描述性阈值变性能门。

| 题 | 现在可答的范围 / 仍缺前置 |
|---|---|
| N-2 | 可现在首签§5.2 B-pre：SSH≤2、每次≤10min、ping≤10包，推理/写入/启动0；下一步只产B0a事实读数，非B-main授权。 |
| (h) | 可现在决定正式用户验证或诊断的性质；原推荐正式保持。不会因此取得Play额度。 |
| (j) | 可现在决定备用臂触发条件；真实触发与5060另签额度尚未发生，不能提前启用或借JET额度。 |
| (k) | 可现在决定执行分工；推荐本人经既有SSH启动保持。代码命令可供审阅，实际板启动待B-main，不改系统/SSH/沙箱设置。 |
| (i) | 代码复核/预算计量修订前置已满足；B0a读数未有，不能现在首签暂估B-main执行；先N-2再核清回填，按确定逐维度上限提请。 |
| N-3 | 可审阅原§6.2；有效确认随B0a核清后的B-main信封逐码进行，当前处置未生效，不把描述线提升为性能门。 |

本轮 consumed=none：不跑模型/功能测试/归档评分，不写运行时状态，不碰Jetson或Unity。交用户决定上述题；答复由授权发生会话入账后，Acceptance落实合同与信封边界，再按相应范围交Implementation/用户执行；当前无已签阶段B可执行动作。

## B-pre答复落实（2026-10-07）

**结论：N-2 B-pre 已按 §5.2 申请值首签，N-2/(h)/(j)/(k) 四项答复落实，交 Implementation 仅执行 B0a 只读预检。** 这是授权核对、合同边界裁定与交接，不是新 D/C/R 轮；Overall `REVIEW_PASSED`、Lifecycle `ACTIVE`、原 AC-1…18 及三条 AC 解释修订不变。B-main 与 N-3 未签，全部相关维度仍0；AC-14/15/18与AC-16板端仍 `NOT_RUN`，无 `UNITY_NA`，不签 `DONE`。

### 1. 原话、supervisor 读法与 B-pre 信封逐项核对

唯一授权来源为 `docs/authorizations.md` 2026-10-07「P1-ENG-LOOP-002 — 用户首签 N-2 B-pre 只读预检、(h) 正式用户验证、(j) 不启用 5060 备用臂、(k) 本人经 SSH 启动板上服务（supervisor 会话代录）」。用户在分别展示范围/理由的四道题中选「按申请值签 (Recommended)」「正式用户验证 (Recommended)」「不启用备用臂」「我本人经 SSH 启动 (Recommended)」。逐条与账本完整展示文本、supervisor 读法及 §5.2 核对：一致；(j) 是用户明确选的非推荐项，不能沿用旧推荐。MacBook Air 身份由题面“本机（Unity 主机）”、F10 与交接机器分工相互确认。账本无需更正，本派发会话不代写用户原话条目。

| 已签维度 | §5.2 申请 / 账本逐项对应 | 裁定 |
|---|---|---|
| 机器 / 链路 | Unity 主机 MacBook Air → Jetson 既有 SSH | 一致；不迁至 Mac mini、不借 JET 信封 |
| 只读 SSH 次数 | ≤2 次 | 一致；成功、失败与重试共账，不重置 |
| 每次墙钟 | ≤10 min | 一致；从该次连接尝试开始至结束记起止与实际时长 |
| ping | 总计≤10 包 | 一致；§2.2/冻结操作单§2单次≤5包，执行同时守两层上限 |
| 推理请求 | 0 | 一致；不探测推理，不加载模型 |
| 板写入 / 服务启动 | 各0 | 一致；不部署、不传文件、不启动任何服务 |
| 其他未签维度 | scenario/session/run ID、Play、非推理 HTTP、5060、API、GPU、下载、安装、云均0；Unity/Play=否 | 未签缺项0；B0a读数文件是明确允许的本机文档产出，不写runtime |
| 设置 | SSH/系统/沙箱设置不改 | 保持；连不上或缺前提时报告，不能自行改设置/存键/放行 |

(h) 将未来阶段 B 的实际 Unity 读数与用户目检按**正式用户验证**记入 `docs/unity-test-log.md`；只确定证据性质，不授 Play、不将 B0a 或旧 JET 诊断升级为正式闭环结果。(k) 会话与快层在 MacBook Air；未来板上服务由**用户本人**经既有 SSH 以前台方式启动，角色只提供逐字命令。启动仍待 B-main；本次 N-2 中的角色只读 SSH 不等于获准替用户启动服务，前台生命周期、端口释放、身份与资源计量义务保持。

### 2. 授权边界修订 1（§5/§6.2/§7；源于用户 (j)，不修订 AC）

依据 engineering §2/§3 与 acceptance 细则的合同修订路径，将用户具名硬件/执行选择**追加**为现行边界；原正文、AC 与 STOP 申请表保留。此处只落实已经逐字入账的收窄选择，不签新额度、不修改运行时行为或验收义务。

| 原条款 | 本次答复的效力 / 冲突处置 |
|---|---|
| §3.2、§5.2 备用臂及 §7(j) | 现行选择为只用 Jetson、不启用5060；备用臂启动≤2/查询≤100仅为历史条件申请，当前无启用条件、各维度0。旧“当日不可修复时启用”推荐被用户否决，不可因主臂失败自动转臂，也不从旧项余额取得许可。以后改变此选择须用户另行答复、入账、接受合同修订及另签额度。 |
| §5.2 B-main 暂估重测/故障重启维度 | 全部仍未签0；不能据暂估次数在主臂失败后再试。B0a核清后逐维度确定申请，须与“主臂失败就停下”一致。 |
| §6.2 S-PRECHECK / S-RECEIPT / S-IDENTITY | 主臂链路、必需资产/身份或收据失败则停止后续、保留事实并按原归口回接受/用户；S-RECEIPT 的“备用臂须(j)”在当前(j)下没有可执行分支。B-pre不运行收据/身份推理核验，不虚报这些板端结果。 |
| §6.2 S-BACKEND | 用户“主臂失败就停下”约束今后的调度；发生主臂 backend_fatal 时不得按原申请的“同原因第2次才停全部”继续新主臂尝试，须停下回用户。保留该原表的历史申请，不改 AC-3 的当前会话 TERMINAL 语义；与本选择冲突的 B-main 重启/继续处置须在 N-3 逐码申请中明确修订。 |
| §6.2 其余码与 N-3 | 不从(j)推定已逐码确认整张STOP表；S-REBUILD、S-RING等保持原申请，非主臂失败的判断不任意扩写。“S-RING记NO_POSE并继续”仍待N-3，不变性能门。任何不能判明是否属主臂失败的情况先停、记录歧义回接受，不自行放宽。 |
| §7 停点与执行分工 | (h)(j)(k)/N-2已答，不再重问；只启用B-pre。B-main、实际采集放行及消耗证据停点原门保留；后续C/R轮号与资格按IR-13/实际diff解析。 |

冻结 `docs/evidence/P1-ENG-LOOP-002-play-ops.md` 仍是代码通过候选附随版本，本轮不改该 PLAY_GOVERNING 文件。其开头“板端0”、§13 S-BACKEND 等是旧阶段快照，**不得据此阻止本次单独已签B-pre，也不得据它启动B-main或覆盖新(j)**。B-pre仅引用其§2的事实清单/单次ping上限，不执行§1 Play门、§3–13。B-main申请/放行前由实现按本节同步操作单的签发状态、单主臂失败处置与本人启动分工；发现需要改AC/接口时先提交「待裁定」，接受按既有路径追加修订，核对轮不得暗改AC。冻结操作单若改动，必须按§7/workflow §4.4判开轮资格、经过相应核对与独立复核，不能以“文档同步”排除该diff；本轮不预签其通过。原HEAD等值门及实际Play发令前HEAD/status记录义务保持。

### 3. B-pre执行交接：B0a只读事实与停止边界

下一角色为 **Implementation（B-pre）**，由supervisor依状态板派发或用户开独立实现会话，**在 MacBook Air（Unity主机）执行，仅经既有SSH读取Jetson**。不是本接受会话执行，也不接管JET或恢复ACQ。开工依AGENTS/workflow §6.1读取全部结构与交接、engineering §8–9、实现细则；合同必读本节、§0 F7/F10、§2.2/§2.5 H-12、§5.2、§6.2、§7、R2消费前置及账本原条。先读工程继承清单/完整缺陷账本，沿JET提案「阶段BC2诊断核清」§1只定位既有GGUF/mmproj/二进制与部署目录来源，不把旧读数当本次事实或额度；正式设计读本项条目及§8端侧边界。冻结操作单只读§2作为B0a清单，不进入B0b。

只产 `docs/evidence/P1-ENG-LOOP-002-precheck.md` 的具名「B0a原始读数与逐维度用量」节：

1. 记录本机/目标设备、既有SSH别名来源、命令与起止时刻、退出码、原始stdout/stderr；路径与可派生标识运行时从来源解析，不手抄HEAD/sha/run名。
2. 尽量一次只读SSH完成：既有部署目录、GGUF、mmproj、llama二进制是否存在及字节数；系统 `python3 --version`、`df`、`free`、`ss -ltn` 的事实。不运行llama `--version`/导入部署包/构建/模型/测试，AC-16板端sha核实与真实服务核验留B-main。源目录/计划新部署根的存在性分列，缺失如实报告，不能为通过预检创建或补齐。
3. Tailscale往返只用 `ping`（单次≤5包、累计≤10）；写方向、目标、实际包数、往返/丢包原始读数。零HTTP，包括/status/health；SSH/ping/ss不证明Unity主机到服务HTTP可达性，保持该项未核，待B-main。
4. 逐次列SSH尝试（含失败）、每次墙钟与ping包数；列明推理/板写入/启动/传输/HTTP/ID/Play均0。仅本机证据文档落盘，不写runtime、不创建scenario/session/run目录，不编造服务或性能结果。未能取得的事实写UNKNOWN/未核及原因；额外包/命令缺失不安装。

**停止条件**：链路/认证失败、必需文件缺失、读数不全、残留监听/共享槽位冲突、需改变设置/写板/启动/HTTP/推理、超过或达到任一已签上限、合同歧义，均立即停止本次后续，保存已得事实与实际用量交接受；不能为修前提而试连/重试/清端口/部署/启动，第二次SSH只是总上限不是失败后的自动重试许可。每次在10min前结束，ping不越限；不得因N-3整表未签而突破B-pre边界。成功取齐读数也必须在B0a停下，提交并推送事实及状态，交Acceptance核清、回填B-main确定申请与N-3逐码处置；不自行进入B0b/B1/Play。

**Consuming=no**：按AGENTS判据，此范围创建/消耗scenario/session/run ID、Play配额与API预算均0；只读板操作有独立已签上限，不因零消耗列而免记账。全局0条消耗性+2条零消耗、Gate-echo一致；完整reviews的block/release来源与缺陷账本已核，唯一实质ACQ R2-1按文件顺序release，无未release阻断。保持单写者/共享槽互斥；不产生额外活跃交接。

### 4. needs_user（仅两题；原文、推荐与理由保留）

以下逐字取「R2消费」/「D2接受裁定」原题；**待B0a核清后**才以确定额度/逐码处置转呈，不由supervisor代拍。原“R1通过后”按已消费最终R2通过轮理解，原“待修”是历史依据；本次(j)要求的操作单/STOP同步仍须完成。N-2/(h)/(j)/(k)已答不重问，N-1已用量不重置，N-4不触发。

- (i) §5 阶段 B 信封签发（`R1@K1K2K3K4` 通过后）；推荐在 D2 预算修正、预检核清与代码复核通过后按确定的逐维度上限签发，理由：现申请值存在 AR1-8 的计量/前置缺口，当前不能签发执行。
- N-3 STOP 缺省处置（随 B-main 信封）。推荐 AR1-8 修正资源口径后，逐码确认 §6.2（含S-RING记录NO_POSE并继续，非强保证帧覆盖）；理由：COORD-017禁止接受角色让未确认处置自行生效，不把描述性阈值变性能门。

本轮consumed=none：未跑模型/功能测试/SSH/归档评分，不写运行时状态、不碰Jetson/Unity；只核对并落实已有授权。实现/复核/Unity证据未增加、AC与算法/采样不变；ACQ暂停/旧非verdict/清理义务、其具名cause债CLOSED及其余OPEN债保持，旧余额不转用。当前仅B-pre可执行，B-main仍未放行。


## B0a核清（2026-10-07，Acceptance；资源与前置裁定）

**答复后索引：本节§3/§5是核清当轮待答快照；四项已答的落实及现行执行交接见「补核答复落实」。完整B-main运行与N-3仍待补核后转呈用户。**

**结论：N-2已记录用量在信封内，B0a事实可保留；五项观察点已逐项裁定/归用户。完整B-main运行尚不具签发申请资格。** 本轮不是D/C/R，不签额度、独立verdict、AC满足或DONE；Overall REVIEW_PASSED/Lifecycle ACTIVE保持。只读原始输出与合同，不SSH/模型/测试/评分/runtime/Unity。本次工程§9 fail-closed只限制尚未签发的运行申请，不撤销N-2，不把未知改成失败，不修改AC或冻结操作单。

### 1. 原始读数与用量核对

完整来源：`docs/evidence/P1-ENG-LOOP-002-precheck.md`「B0a原始读数与逐维度用量」§1–8。§2命令没有模型/部署/HTTP/文件传输/设置修改，§3记S1唯一SSH成功1.218s<600s，P1发/收5包、单次5且累计5<10；§4逐行读数与§5/6一致。R10 rc=2表示候选新目录不存在，R07 rc=1表示指定进程名未命中，SSH总rc=0**不等于每条检查通过**。R03/R05/R16支持磁盘/内存/旧目录读数；内存是瞬时事实，不是可运行性证据。资产字节与路径只能证存在性，不能证sha/构建/依赖/性能。§3墙钟1.218s是实现记录，本机epoch原值未附，板date两端同秒只支持小于时刻分辨率；不冒称独立重算到毫秒。SSH stdout字节数亦为实现记录，不以Markdown拼接复原当原流。

N-2账：SSH已用1/2，ping已用5/10，其他受限动作0；保留系统登录日志/访问时间的附带披露，不将系统行为当部署写入。B-pre停止边界已执行：只读清单回来后未进入B0b，未知监听与合同歧义如实交接受；不认定未知监听已无共享槽冲突。全局block/release来源完整扫描，实质ACQ R2-1按文件顺序已release；无未release门阻断，仍不等于Play授权。

### 2. 五个观察点逐项裁定（不增改AC）

| 点 | 裁定与未闭项 | 下一核实/归口 |
|---|---|---|
| BOARD_ROOT | 本项计划独立根取`/home/jetson/eng-loop2`，源码置其`code/`，日志置`logs/`；不用/覆写JET的eng-jet/code。R10只证明候选模式当时不匹配，未核父目录链接/写权限，不宣称根已创建。新建仍待板写入信封，已有任何同名根不得覆盖。 | 补核精确路径/父目录/链接/权限/磁盘；后续新建方式、assets副本和根下cache/tmp须由实现准备操作单，提交后经相应停点；本轮不写板。 |
| 双Q4 | 权重候选只取JET提案「阶段BC2诊断核清」§2所核state.q4→传板verify-q4链中的C2路径；本机state/板原verify源缺失则UNKNOWN并停，不能按字节/文件名/mtime猜。mmproj沿同链transfer期望定位，板端新读sha必须与来源期望相等；本项assets只写自身新核值，不把旧JET结果当AC-16证据。 | 运行时解析来源，不手抄SHA/UTC目录；补核板文件与父目录非链接、stat/sha。不允许官方base替代或补下载。 |
| 共享库身份 | AC-7/16及A2(d)当前明确`runtime_binary_sha256`=单个llama-server文件，源码`tools/language_serve.py::llama_preflight`也只哈希三文件。72,424B不覆盖同目录.so；不得把单文件sha称整个推理栈身份。真实动态依赖未核，现有合同没有共享库机读绑定。 | 推荐用户在(i)先签零模型静态依赖/文件事实补核，再决定保持三文件范围并披露库身份限制，或经「待裁定」修订AC/实现/停点扩大绑定；本轮不自行选扩大、不新增AC、不预签整栈身份。 |
| 46273 | R06有未知监听、R07未见两种进程名，不足以证明监听归属/共享槽无冲突。计划llama仅127.0.0.1:18081、对外language_serve使用Tailscale:18082（仅候选，当前未监听），均不抢46273。无权清它、sudo、改网络或直接推断为Tailscale服务。 | 推荐用户确认46273归属与本项槽位互斥；补核非特权ss -ltnp/进程/端口快照，拿不到归属保留UNKNOWN回用户，不发HTTP。本人确认前不放行服务；新出现占端口即S-PRECHECK。 |
| 回填数字 | §5.2确定计划表已回填：2启动、335推理、200非推理，重测/故障重启0；其余按原口径具体列出，并分列本轮可申请值。磁盘余量充分容纳200MB计划预算不等于模型运行内存充分；libs/Python闭集运行等未知不靠余量豁免。 | engineering§9：本轮只申请≤1 SSH/≤600s静态补核，其余0；依赖未核环境的运行维度不申请签发。补核回来由接受再转呈完整B-main，没有自动提升/剩额挪用。 |

HTTP服务可达性、response_format确切服务响应仍是后续首次运行的合同核验，不能从ping/SSH证明。Python3.12.3版本已核，但本项模块import/可运行性尚未实测；闭集禁第三方保持，不凭版本保证可运行。原JET诊断/违规/UNKNOWN与ACQ暂停/清理/债务/旧余额不变。

### 3. needs_user（原题与具名推荐；只能用户签）

**(i) 原题：§5阶段B信封签发（R1通过后，现按已消费R2理解）。** 原推荐与理由仍见「B-pre答复落实」§4。本次推荐：**先签B-main只读补核子范围，不签完整运行信封**，确定申请=MacBook Air→同一Jetson既有SSH≤1次、墙钟≤600s、失败/重试共账且重试0；ping0；模型/--version/import/推理/HTTP/服务/板写入/文件传输/ID/Play/runtime/回放/5060/API/GPU·h/下载/安装/云全部0，不改设置。只产本机文档、Unity/Play=否，不借N-2余量或JET信封。理由：§2的共享库动态依赖、精确部署根及未知监听还缺事实，engineering§9禁止先签依赖假设的运行额度；完整计划各维度确定值与依据已在§5.2回填，暂不请求签发它们。

补核前在本机静态核部署闭集与传递依赖的标准库要求，不import；板端对应只读核解释器/标准库文件存在性，不把静态存在性写成可运行通过。补核只用已存在的非特权读命令：路径/父目录readlink/stat/test、C2/mmproj/二进制与实际依赖文件sha256sum、现有readelf/ldd的依赖事实、python3 --version、df/free/ss -ltnp/pgrep；不得执行llama --version、Python import、模型/服务/HTTP、安装缺失工具或为取事实改变设置。若命令缺失、目标来源链缺失/不符、链接异常、监听归属仍UNKNOWN、读数不全或任何疑义，即保存已得事实停下，交接受/用户，不追加第二次连接。执行角色须先定位并只读核JET来源链；来源不在本机只能报UNKNOWN，不能临时联网取件。600s到限前结束，原stdout/stderr、每个子命令退出码与本机epoch始末值完整保留。

同时请用户裁定(i)内两项未闭选择：**共享库推荐先取事实再决定身份范围**（不得把补核当AC修订授权）；**46273推荐由本人确认归属/槽位互斥并保持不触碰**。若用户要直接签完整运行信封，仍须先补齐工程§9事实与合同/操作单停点；接受角色不能以用户选“按表签”代判未核事实已满足。

**N-3 原题：STOP缺省处置（随B-main信封）。** 推荐逐码采纳下表，理由：保持原合同判定，落实(j)首次主臂失败即停、不启用5060，区分非主臂重建与描述性帧环损失。不改变AC、采样、算法、通过线；未逐码确认不生效。只读补核仍按上段更窄停止边界，不因N-3答复允许部署/服务/Play。

### 4. N-3 §6.2逐码处置申请（非生效修订）

§6.2原判定与出处逐字保留；此表是用户确认后待落实的处置申请，优先于历史推荐，当前不执行。STOP后允许的仅已签范围内停止本人前台服务/释放端口、记录实际账、保留工件及必要安全收尾，不能解释成禁止收尾或许可新加载/诊断/删除。

| 码 | 推荐处置申请 | 理由 / 与(j)关系 |
|---|---|---|
| S-PRECHECK | 停全部后续，回接受；链路或必需文件失败不试连/修前提/换臂 | 主臂前提失败；已计划新根在创建前不存在不冒充“已部署文件缺失”，部署完成后缺闭集文件才失败；未核链接/归属仍停并报未知 |
| S-RECEIPT | 停全部后续，回用户；重测0、5060分支0 | 6/8或schema拒绝触发；旧“备用臂须(j)”不适用当前选择 |
| S-IDENTITY | 停全部后续，回接受；不覆盖期望/换base/重建补包继续 | AC-6/16身份失败；本轮不扩大sha字段范围 |
| S-ENVELOPE | 任一维度到限即停全部新增动作，安全收尾后回用户；禁止借其他维度余额 | 唯一上限取用户账本，预计收尾需预留资源，不能等到耗尽才追加 |
| S-LOAD | 停全部后续，回实现/复核；保留计数，修复候选回停点 | AC-3代码缺陷；不增候选/全套额度 |
| S-BACKEND | 首次backend_fatal即停本次及全部后续，回用户；故障重启0 | 替换“同原因第2次才停”，落实主臂失败就停下，不改AC-3当前会话TERMINAL语义 |
| S-REBUILD | 停本次、计账；确认仅为A5非主臂的帧/发布段重建限制时下一既定剧本可继续；属主臂失败或不能判明则停全部回用户/接受 | 原非主臂分支不任意扩大；不加剧本、不改参数、不重跑本次 |
| S-WALL | 停本次并停全部后续，回用户 | 420s按钮墙钟资源限，非性能线 |
| S-ARCHIVE | 停全部后续，回用户；保留超限/身份或layout异常事实，不删/筛工件再续 | 原225MB及H-2/layout绑定；不以采样峰值未超称完整峰值证明 |
| S-SERVICE | 停全部后续，回用户；本人按已签前台收尾停止并核端口，不新开服务/清未知进程 | 驻留与释放要求不放宽；非特权读数拿不到的保持UNKNOWN |
| S-RING | 不停；静止车相应帧NO_POSE照记 | 原描述性可评分性限制，非主臂失败；不扩帧环/补采/改指标 |

其他现行硬停止按A5已冻结分类记录；主臂服务未就绪/运行退出（操作单服务退出码4/5）属(j)失败，首次即停全部回用户，不能由缺S-BACKEND事件漏过。HTTP不可达也不作环境性重试理由。none/ambiguous/解析失败等正常结果按原漏斗/现行内置尝试记录，不擅自改算法或把每行失败当新性能STOP；若表现为服务拒绝/schema不支持/backend_fatal则按具名码停。

### 5. 后续角色与未闭门

本轮交**用户**答(i)/N-3与其中未闭环境/身份选择；答复由发生会话逐字入账，再交接受落实。当前没有新已签可执行动作。若签只读子范围，Implementation只补核，结束回接受；完整运行维度待事实后另转呈，不自动启用。若需共享库机读身份扩大，先由实现写「待裁定」，接受沿engineering§2追加AC修订，用户资源/范围授权不得由本轮预定。冻结操作单还须同步单主臂、本人启动、明确根/端口与逐码处置/计量；按§7/workflow§4.4将其PLAY_GOVERNING diff纳入候选、C核对及独立复核，不能在本轮暗改或预签通过。实际Play前HEAD/status/Unity日志与证据停点门均保持。

原AC-14/15/18及AC-16板端NOT_RUN，无UNITY_NA，不签DONE；N-1已用量不重置。B0a是环境事实，不是正式闭环性能证据；本轮consumed=none。

## 补核答复落实（2026-10-07，Acceptance；只读子范围交接）

**换机后索引：本节保留原Air答复与执行合同。用户随后选SUB:1方案B并另签Mac mini同边界子范围，机器/额度/交接由「SUB1换机答复落实」替代；本节§2–3的用途、命令闭集、停止闭集与产出结构继续适用。**

**结论：四项答复与用户展示文本、supervisor读法及「B0a核清」§3逐项一致，账本无需更正；只落实已签只读补核，交Implementation执行后回Acceptance核清。** 本轮不是D/C/R，不签额外额度、不增改AC、不签独立verdict；Overall REVIEW_PASSED/Lifecycle ACTIVE保持。授权唯一来源为 `docs/authorizations.md` 2026-10-07「P1-ENG-LOOP-002 — 用户签 (i) B-main 只读补核子范围（SSH ≤1、≤600 s）；共享库先取事实再定；46273 保持不碰；N-3 待补核后随完整额度确认」。本派发会话不代写用户原话账本。

### 1. 四项答复与信封逐项核对

| 答复 | 原话选择 / 与B0a推荐及supervisor读法核对 | 落实效力 |
|---|---|---|
| (i) 只读补核 | 「签只读补核 (Recommended)」；SSH≤1次、≤600秒、失败不重试、非特权只读、其余0，与B0a§3和账本信封一致 | 仅MacBook Air→同一Jetson既有SSH；成功/失败共账，重试0；不借N-2余量/JET信封。完整B-main计划仍未签 |
| 共享库身份 | 「先取事实再定 (Recommended)」；先查实际依赖与sha，再选维持三文件范围/披露限制或修订扩大绑定，与B0a§2/3一致 | 补核不等于AC修订授权；单个llama-server sha不称整个推理栈身份。本轮不代选身份范围 |
| 46273 | 「不清楚，保持不碰 (Recommended)」；只读再看一次归属，拿不到记未知，与B0a§2/3一致 | 不探测/占用/清理100.100.100.100:46273，不sudo、不改网络。计划端口仍127.0.0.1:18081及Tailscale:18082；用户确认互斥前不放行服务 |
| N-3 | 「等补核后一起确认 (Recommended)」；完整额度与11码处置待补核后确认，与B0a§4及随信封生效规则一致 | 未逐码确认，不让推荐处置生效；不影响更窄的补核停止边界，不重问已答(h)(j)(k) |

信封逐维度：机器=MacBook Air（Unity主机）→同一Jetson既有SSH；只读SSH≤1次、从本机连接尝试开始至退出/终止墙钟≤600s、重试0。ping、模型加载、llama `--version`、Python import、推理、HTTP（含loopback/status/health）、服务启动/驻留、角色板写入、文件传输、scenario/session/run ID、Play、runtime写入、回放/评分、5060、外部API、GPU·h、下载、安装、云全部0；设置不改，Unity/Play=否。命令/stdin及原stdout/stderr为只读SSH记录，不作部署文件传输。只产本机文档，N-2原账SSH1/2、ping5/10及N-1用量保持，子范围独立计账、不重置/转换旧额度。

### 2. 执行机器、来源与命令闭集

Implementation由supervisor按状态板派发或用户另开实现会话，在**MacBook Air**执行；不迁Mac mini、不在本接受会话执行。开工按AGENTS/workflow§6.1读全部结构/交接与本项Gate，读engineering§8–9、实现细则、本节、「B0a核清」§2–4、§5.2回填、§2.1 A2(e)、§2.5 H-12及账本原条；先读工程继承清单/完整缺陷账本，再沿JET提案「阶段BC2诊断核清」§1–2与「阶段BC2JSON诊断授权落实」§1的来源链定位原件。JET只作输入来源，不转用其额度或升级诊断结果。

**本机先做静态准备，尚不连接：** 只读既有SSH配置/`ssh -G Jetson`，不读私钥；从既有原件运行时解析C2 `state.q4`→传板verify-q4、mmproj transfer期望、server来源路径/期望及bindir链接信息，不抄SHA/UTC目录/HEAD进手维护正文，不按同字节/文件名猜双Q4。来源不在本机、链歧义或不符即UNKNOWN、停下回接受，不能联网取件。对 `config/p1-eng-loop-002-board-deploy.json` 所列源码及传递导入做文本/AST静态读取，不import仓库模块或第三方，列标准库要求及板端待核文件路径；不跑测试/评分，不生成部署包或改冻结操作单。仅系统Python标准库可用于读取JSON/AST/哈希与本机计时记账，不调用模型加载器。

**板端只在唯一SSH会话内读下列闭集，保存逐条命令与退出码：**

| 目的 | 允许的现有非特权命令 / 目标闭集 |
|---|---|
| 设备、时刻、工具在盘 | `date`、`hostname`、`uname`、`id`、shell `command -v`；只核本表所需工具，不安装缺项 |
| 路径/权限/身份 | `test`、`stat`、`readlink`、`ls`；目标限解析出的C2/mmproj/server、其逐级父目录、server同目录库、实际依赖路径、系统Python/标准库对应文件及计划根 `/home/jetson/eng-loop2`（含计划code/logs）和父目录。新根不存在照记，父目录权限仅作只读判断、不以写文件试权限；三文件及其父目录不得异常经链接，共享库既有链接另列终点/来源、不混称普通文件 |
| 文件sha/依赖 | `sha256sum`核上述三文件与实际依赖文件；`readelf -h/-l/-d`、`ldd`仅读已按来源核定的现有ELF server/其依赖库，列NEEDED、RPATH/RUNPATH、解释器及解析依赖路径/链接终点，按解析依赖闭包核类型/sha；不执行llama `--version`/`--help`或目标程序，不用未核来源文件探测，不扫描无关全盘，不补造旧库sha期望 |
| 解释器/标准库在盘 | `python3 --version`及上述文件型读取；只核本机静态要求对应的板文件存在性/类型，不 `-c`、不import、不运行部署包；内建/扩展项不能由静态文件证明的如实标UNKNOWN，不称可运行通过 |
| 磁盘/内存事实 | `df`、`free`；只记瞬时读数，不作服务工作集/峰值或性能结论 |
| 监听/进程快照 | `ss -ltnp`一次非特权归属快照；`pgrep -a -f llama-server`与`pgrep -a -f language_serve`仅查两类相关进程。核18081/18082占用及46273归属；无匹配的rc=1如实记，不称所有进程都不存在，不用HTTP/端口主动连接核归属 |

shell仅允许变量赋值、有限循环/条件、`printf`/退出码记录等组织上述读命令；不执行闭集外远端工具。SSH脚本经stdin送入现有shell、板上不落脚本文件；现有`timeout`与本机超时终止仅用于守墙钟，不取得第二次连接许可。Implementation在连接前准备本机总墙钟限时与收尾预留，远端读命令须在600s前结束，长哈希不得挤占收尾；无可靠限时手段即停、不开始。保存本机epoch始末原值及UTC、SSH和每条子命令rc、完整原stdout/stderr；SSH总rc0不能掩盖子命令失败。

### 3. 产出、停止条件与Consuming判定

唯一事实落点：`docs/evidence/P1-ENG-LOOP-002-precheck.md`新增具名 **「只读补核原始读数与逐维度用量」** 节，保留B0a原始节/接受节，不覆盖失败、旧读数或旧账。该节按具名子节保存「本机静态来源与部署依赖清单」「命令与原始stdout/stderr」「逐次尝试与逐维度用量」「资产/共享库/部署根/监听事实」「停止条件与UNKNOWN」。自动读数/原流里的派生路径与sha照原样保存，手维护结论只指来源。不产正式 `-assets.json`、收据或性能证据；无SSH时也记录本机阻塞及实际SSH0，不伪造板读数。

停止闭集：本机来源缺失/歧义/不符、链路/认证失败、必需旧资产或工具缺失、资产身份不符、异常链接、父目录权限不能核实、依赖未解析/缺库、必需读数不全、计划18081/18082已占用或相关残留进程、补核快照仍无法辨明46273归属或显示共享槽冲突、需改变设置/写板/安装/启动/HTTP/推理、到达任一上限或预计余时不足、合同疑义，均保存已得事实并停止后续，交接受/用户；不追加第二次SSH、不清未知进程、不为修前提继续。新部署根尚未创建本身不是必需旧文件缺失，不在补核中创建。用户尚未确认互斥不阻止本次已签只读补核，但46273即使读到归属也须用户确认互斥才可放行服务；拿不到归属按已答选择记UNKNOWN，本次不得升级权限。非预期子命令失败/必需事实UNKNOWN出现后不再为补齐而追加探测，不能照脚本无条件继续；计划新根不存在的test非零、pgrep无匹配rc1分别按上述预期状态记录。读齐也在本子范围结束，不能进入B0b/B1/Play。

**Consuming=no**：按AGENTS判据，本范围scenario/session/run ID、Play配额、API预算均0；SSH/墙钟另按已签上限独立记账，不因no免记。保持同一条交接、全局0消耗性+2零消耗、单写者与共享槽互斥。完整reviews的blocks/releases来源已扫描，唯一实质ACQ R2-1按文件顺序已release；不解除其他放行门。Implementation提交/推送事实与状态后交Acceptance核清，不能自行签额或选库身份范围。

### 4. 待补核后转呈用户与未闭门

- **完整(i) B-main运行信封**：待补核逐项核清工程§9事实后，推荐据§5.2确定计划逐维度转呈；事实仍缺则保留阻断，不把一次静态补核等同部署可运行性或自动授权。
- **共享库身份范围**：待实际依赖/sha事实后转呈“保持三文件并披露限制”或“修订扩大绑定”；本轮不预选。若后者需合同/代码变化，实现先写「待裁定」，接受追加AC修订，资源/范围回用户并经过相应停点。
- **46273/共享槽互斥**：补核快照交用户确认；推荐保持不碰，未确认不放行服务；不再问已答的“不清楚”选择，不把新快照当用户确认。
- **N-3**：依已答延期选择，补核后与完整信封一起转呈「B0a核清」§4的11码推荐及理由，当前不生效。只有补核更窄停止闭集可执行。

冻结操作单的单主臂/本人启动/根与端口/STOP计量同步、其PLAY_GOVERNING候选核对及独立复核、实际采集版本/HEAD/status/Unity日志门、AC-18证据核实仍未完成；本轮不改冻结操作单。AC-14/15/18及AC-16板端NOT_RUN，无UNITY_NA，不签DONE。旧债/ACQ暂停/非verdict/清理及余额不转用保持；本轮consumed=none，零SSH/模型/测试/评分/板与Unity操作、零runtime写入；下一动作唯一见状态板交接行。


## 补核停止核清（2026-10-07，Acceptance；零消耗停止与余额裁定）

**答复后索引：本节保留Air停止事实、顺序偏差和当轮余额裁定。§4 SUB:1已由用户选B，原Air未用余额已作废；现行Mac mini子范围及执行前提见「SUB1换机答复落实」，不再沿本节§3续用Air余额。**

**结论：本机缺JET C2来源链原件的停止归因成立；已记录SSH 0/1、墙钟0/600 s，其余受限维度0。保留有限本机静态事实，不认定补核完成。** 本轮不是D/C/R，不签额度、不增改AC、不签独立verdict；Overall REVIEW_PASSED/Lifecycle ACTIVE保持。当前只交用户来源选择，原命令/停止闭集继续见「补核答复落实」§2–3。本派发不代写用户原话账本。

### 1. 停止、实际用量与记录限制

依据 `docs/evidence/P1-ENG-LOOP-002-precheck.md`「只读补核原始读数与逐维度用量」完整原始节及「停止条件与UNKNOWN」，对照账本10-07「用户签(i) B-main只读补核子范围」与上一节：

| 核清项 | 裁定与具体依据 |
|---|---|
| 停止归因 | L1 stdout两处原件根exists=False，state/budget/checkpoint缺失；本接受会话只读磁盘再次确认同一缺口。JET提案「阶段BC2诊断核清」原件根及§2、「阶段BC2JSON诊断授权落实」§1要求state.q4→verify-q4及server_sha256_now原流，不能由B0a板路径/字节替代。命中「本机来源缺失」，停止在SSH前成立；不归因于Jetson链路/认证/性能失败。 |
| 机器与来源所在 | 实现记录为MacBook Air；transfer原件src前缀与JET执行合同支持“原件可能在Mac mini”的推断，本轮没有访问Mac mini，未核原件现存/完整。对T7/用户目录的排查只有实现叙述、未附完整命令原流，不升级为全机穷尽性证明。 |
| SSH与墙钟 | 实现逐维度表记录连接0、连接墙钟0；L0为不连接的ssh -G，L1–L3为本机标准库解析，未列任何连接尝试/板输出；与supervisor finished报告的SSH 0/1一致。没有连接起止可供重算，不能把本机resolve.py的0.088 s计为SSH墙钟。这里只核记录一致性，不冒称独立网络审计。 |
| 其余用量 | ping、模型加载/llama --version/第三方或仓库import/推理/HTTP/服务、板写入/传输/ID/Play/runtime/回放评分、5060/API/GPU/下载/安装/云均记录0；不改设置、不提权、不触碰46273。系统Python标准库读取JSON/计时不是被禁的部署或模型import。N-2原账SSH1/2、ping5/10及N-1用量保持，不借用、不退款。 |
| 停止顺序限制 | 同一resolve.py原流在L1已报缺后仍输出L2/L3，且另有本机寻件叙述；不能把这段记为严格“缺失即停、只保存此前已得事实”的全过程合规。属本机静态续读的执行顺序偏差，未因此增加已记录SSH/模型等消耗；结果可按下表保留，不追认续读许可、不把UNKNOWN改通过。后续仍按原停止闭集即时止步，不用零消耗豁免停止。 |

### 2. 本机静态事实的保留范围

本接受会话仅用系统Python标准库读取两份已跟踪JSON，核L2/L3字段；未SSH、未执行模型/部署代码。实现原始记录不覆盖。

| 已得事实 | 可保留范围 | 不能推出的结论 |
|---|---|---|
| SSH别名（L0） | 原流中的Host Jetson、有效hostname/user/port作为当时本机配置快照；私钥未读 | SSH/HTTP可达、认证成功、共享槽互斥；本轮不重新连接或修改配置 |
| mmproj（L2） | stageb-transfer.json中cls=G且具名basename唯一1项，expected_bytes及64位expected_sha256、board_final可运行时解析；本轮重读吻合 | 板文件现在存在、类型/父目录非链接、当前sha匹配、可加载或性能通过；不手抄sha/派生目录 |
| llama-server路径与同目录清单（L3） | stageb-build-rerun.json的products.llama_server_stat_raw与board_batch_dir.path + build/bin/llama-server一致；旧stat为regular/72,424 B/775；bin_ls有26行，含库和链接名称/大小的旧快照 | JSON的products无server sha字段；所需旧server_sha256_now仍缺。26行是清单行数、不是26个库；不证明当前库/链接、实际NEEDED闭包、库sha或整栈身份 |
| C2及未执行项 | 预定本机来源链缺口、L4未执行、本轮无板读数均保留；JET原件仅为身份来源输入，仍需本项自身板核验 | 不按文件名/字节/mtime选双Q4，不用官方base替代，不把旧JET诊断当AC-16或性能证据 |

共享库readelf/ldd/sha、部署根父目录/链接/权限、标准库文件、瞬时df/free及18081/18082/46273/相关进程仍UNKNOWN或未评估；未连接的其他停止项不是通过。B0a旧快照不更新；共享库“先取事实再定”、46273“不清楚，保持不碰”和未确认互斥的边界保持。

### 3. 未用SSH信封效力（解释既有授权，不续签）

账本原信封没有写“本机静态停止即作废”，本次也未发起连接。**裁定：若用户选择补齐Air来源、执行机器仍为MacBook Air、目标仍同一Jetson、用途/命令/停止闭集不变，未用SSH≤1次/≤600 s可在同一原信封内继续；不是新增额度或重试，不重新给1次/600 s。** 必须先在Air按原§2核完整来源链、L4与可靠墙钟限时；任一来源/身份/前提仍缺即停。唯一连接一经尝试，成功/失败共账、重试0；不得借N-2余额凑第二次。

来源补齐涉及原信封未覆盖的机器间复制，当前不能由角色执行。换成Mac mini或其他执行机器不满足原机器维度，旧余额不能自行迁移：须用户逐字修订机器/用途/额度边界并入账，由接受落实后才能派发；本轮不首签/续签。用户来源答复与实际补齐事实尚未取得，现不交Implementation启动续补核；旧信封的条件效力不解除当前停止。

### 4. needs_user（原申请与选项；只能用户决定）

**P1-ENG-LOOP-002:2cd95ba5:SUB:1** 原申请（逐字取自supervisor-dispatch.jsonl「只读补核」finished.report的needs_user，非用户授权）：

> how Air gets C2 source chain originals: recommend user copies Mac mini outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/ read-only to same relative path on Air, then acceptance rules whether unused SSH<=1/<=600s can be reused, then re-dispatch; alt: change execution machine, also user-signed

请用户选择如何让MacBook Air取得C2来源链原件，或改执行机器；接受侧可选项如下（未选不执行）：

- **A（推荐）：用户本人先确认Mac mini原件存在并完整，再从Mac mini只读复制来源链原件到Air同一仓库相对路径。** 不改/删来源、不覆盖已有原件；推荐先带齐state.json、budget.jsonl、checkpoint.json、相关steps收据及其引用的verify-q4/precheck原流，以原件链运行时解析，不用手填期望替代。复制整根可能包含模型/工具产物，不把该建议当作无界复制或模型传输授权；若所需清单超出这些来源记录，先列明件数/字节/用途回用户。本轮没有实施或授权代理复制。理由：保持原机器与Unity侧环境，来源核齐后可依§3使用原SSH余额，避免换机改信封；Mac mini实际现存仍须确认。
- **B：改由Mac mini（或用户具名其他机器）执行只读补核。** 须用户另行明确执行机器及SSH次数/墙钟等边界并逐字入账；在新边界落实前原Air余额不转用。理由：原件可能已在该机，可减少复制，但这是设备维度变更，不能由接受/supervisor代答。

未闭门仍见「补核答复落实」§4：完整(i)运行额度、N-3十一停止码待完整补核后转呈，当前未签0；共享库身份范围待事实，不预选扩大；用户确认互斥前不放行服务；冻结操作单同步及对应停点、实际采集版本/HEAD/status/Unity日志门、AC-18证据核实均未完成。AC-14/15/18与AC-16板端NOT_RUN，无UNITY_NA，不签DONE；旧债、ACQ暂停/非verdict/清理与余额不转用保持。

本轮consumed=none；零功能测试/模型/SSH/复制/Jetson/Unity/runtime动作。全局机读blocks/releases完整扫描，唯一实质ACQ R2-1已按顺序release；仍不替代其他放行门。下一动作只见状态板交接行：用户来源答复后由Acceptance落实，supervisor再按实际可执行边界派发Implementation。


## SUB1换机答复落实（2026-10-07，Acceptance；Mac mini只读补核交接）

**结论：SUB:1方案B及“同Air原边界，只换机器”与用户展示文本、supervisor读法、原「补核答复落实」§2–3一致，账本无需更正。** 仅落实用户新签的Mac mini只读补核子范围，原Air未用余额作废；不是D/C/R，不新增或修订AC、不签独立verdict。Overall REVIEW_PASSED/Lifecycle ACTIVE保持；本接受会话零SSH、复制、模型、测试、Jetson、Unity与runtime操作，consumed=none。本派发不代写用户原话账本。

### 1. 原话、读法与逐维度信封核对

唯一授权来源：`docs/authorizations.md` 2026-10-07「P1-ENG-LOOP-002 — 用户选 SUB:1 方案 B：只读补核改在 Mac mini 执行，边界同 Air 原信封只换机器；Air 未用余额作废（supervisor 会话代录）」。用户先选「B：改在 Mac mini 上执行补核」，继而问“换到mini上执行吧，需要在mini上下一个unity吗”，再选「同 Air 原边界，只换机器 (Recommended)」。原话优先；选项展示明确机器、次数/墙钟/重试、原闭集不变、其余0及Air余额作废，不是把Air余额迁过去。

| 维度 / 答复 | 现行效力与核对 |
|---|---|
| 阶段、用途、机器 | B-main只读补核子范围（换机）；Mac mini → 同一Jetson既有SSH。只获取资产/依赖/部署根/监听事实，与原§2–3一致；JET仅提供来源输入，不借其额度。 |
| SSH次数、墙钟、重试 | ≤1次、从本机连接尝试开始至退出/终止≤600s、成功/失败共账、重试0；与用户展示及原口径一致。mini新子范围独立计账，本轮尚未执行。 |
| 零维度（逐项） | ping、模型加载、llama --version/--help、仓库或第三方import、推理、HTTP（含loopback/status/health）、服务启动/驻留、角色板写入、文件传输、scenario/session/run ID、Play、runtime写入、回放/评分、5060、外部API、GPU·h、下载、安装、云全部0；不改设置、不提权、不碰46273，Unity/Play=否。本机系统Python标准库静态解析及板端python3 --version仍仅按原§2的明确闭集，不增动态核验许可。 |
| 命令、停止与产出 | 原「补核答复落实」§2–3逐字适用，只替换执行机器与下节的新产出小节名；包括非特权只读、stdin脚本不落板、可靠总墙钟限时/收尾、逐命令rc与原流、任何停止条件命中即止，不因零消耗续探。 |
| Air余额 / 其他账 | Air已记录SSH0/1、墙钟0/600s保留；该未用1次/600s现作废，不再沿「补核停止核清」§3续用，不与mini叠加。N-2原账SSH1/2、ping5/10与N-1用量保持，不退款/重置/转用。 |
| (i)完整运行 / N-3 | 本次未签完整B-main运行信封、未确认N-3十一停止码；其维度0/处置不生效，补核后仍交用户。共享库先取事实再定身份范围、46273不清楚/保持不碰及用户确认互斥前不放行服务保持。 |

归因（engineering§8）：用户10-07明确变更只读补核的执行机器并另签同边界子范围，替代Air未用执行余额；不是工程性重试、余额转用或对Air静态停止后续读偏差的追认。原Air停止/有限静态事实/UNKNOWN与JET历史偏差均保留，不改为补核完成。

### 2. Mac mini执行前提与实现交接

下一角色为 **Implementation（Mac mini只读补核）**。用户须在**Mac mini上开独立实现会话，或开supervisor会话按该机状态板派发**；本Air会话不能在mini拉起角色，不由本接受会话执行。开工读取原「补核答复落实」§2规定的全部合同/规则/继承账本与来源，以及本节和新账本条目；以最新磁盘合并，保持全局单写者与共享槽互斥。仅只读补核的机器变更，不迁移会话/快层/Unity主机。

连接前必须在mini依原§2顺序只读核：

1. 既有`Host Jetson`别名可解析（既有配置/ssh -G，不读私钥、不连接），目标仍同一Jetson；别名/目标缺失、歧义或需改SSH设置即停。
2. C2来源链原件在mini**现存且完整**：沿JET提案「阶段BC2诊断核清」§1–2及「阶段BC2JSON诊断授权落实」§1定位state.json、budget.jsonl、checkpoint.json、相关steps收据及其引用verify-q4/precheck原流，运行时解析state.q4→传板verify-q4、mmproj transfer期望、server_sha256_now与bindir链接来源。不能把“可能在mini”当事实，不由B0a路径/字节或Air局部静态结果替代期望；任一必需原件/引用缺失、链歧义/不符即UNKNOWN、立即停止，不联网取件、不复制、不按文件名/mtime猜双Q4。
3. 来源齐备后才依原§2对部署闭集及传递导入做文本/AST静态读取、列标准库要求与板端待核路径，并准备可靠≤600s总墙钟限时和收尾预留；缺手段/需新增工具即停，不安装。系统Python标准库解析不是部署或模型import；不运行测试/评分、部署包或模型。

满足前提后，仅在本子范围唯一SSH会话内执行原§2表列的非特权只读命令与目标闭集；原§3**全部停止闭集**原样适用，非预期子命令失败/必需UNKNOWN后不为补齐而续探，不追加SSH、不清未知进程、不创建部署根、不进入B0b/B1/Play。当前mini原件现存/完整与别名解析均未由本Air会话核实，不记前提通过。

产出仍在 `docs/evidence/P1-ENG-LOOP-002-precheck.md`，**新增具名「Mac mini只读补核原始读数与逐维度用量」小节**，其下沿原§3五个子节（本机静态来源与部署依赖清单、命令与原始stdout/stderr、逐次尝试与逐维度用量、资产/共享库/部署根/监听事实、停止条件与UNKNOWN）。保留B0a、接受节及Air「只读补核原始读数与逐维度用量」和停止记录，不覆盖/删改。注明新授权与实际机器，mini用量单列；若前提缺失，也写阻塞、实际SSH0与未评估项。派生路径/SHA只保留在自动原流，手维护结论指来源；不产正式assets、部署收据或性能证据。实现提交/推送事实与状态后回Acceptance核清。

**Consuming=no**：ID/Play/API均0，SSH/墙钟仍独立计账；全局仍0消耗性+2零消耗。本轮全局reviews机读blocks/releases完整扫描，实质ACQ R2-1按文件顺序已release，其他放行门保持。

### 3. Unity答复与未闭项

**本只读补核无需在Mac mini安装Unity。后续阶段B Play按已答(k)仍由MacBook Air Unity主机运行会话与快层、Jetson运行VLM服务；此次只读换机也不要求mini安装Unity。** 依据原「B-pre答复落实」§1的(k)、§0 F8/F10与§5.2完整计划的设备行；mini只承接本次只读来源/SSH事实核查。板服务仍由用户本人经既有SSH前台启动，实际启动/Play等待完整B-main签发和原放行门；若另拟把Unity/会话/快层迁mini，属于尚未授权的机器/范围变更，须另行交用户，不由本次SUB:1推出。

SUB:1来源/换机选择已答，不重问；本轮无需更正账本或新增关键授权。**执行入口仍需用户在mini开上述会话**（推荐supervisor会话按已落盘交接派发，理由：执行前提必须在mini核实，本Air不能跨机派发）。完整(i)B-main运行与N-3、共享库身份范围和用户互斥确认待补核事实核清后转呈；原「补核答复落实」§4的冻结操作单同步/停点、实际采集版本/HEAD/status/Unity日志门及AC-18证据核实均保留。AC-14/15/18与AC-16板端NOT_RUN，无UNITY_NA，不签DONE；ACQ暂停/非verdict/清理与旧债/余额不转用保持。下一动作唯一见状态板交接行。


## Mac mini补核核清（2026-10-07，Acceptance）

**结论：mini 子范围已用 SSH 1/1、墙钟 4.489479 s/600 s、连接重试 0；有限静态事实可保留，但不认定全过程严格符合停止/原流纪律，不放行 B-main。** 本节为现行核清入口，前述“mini 来源/别名尚未核、交实现补核”是旧快照，现由本节替代。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE` 保持；本轮不是 D/C/R，不首签/追加额度，不消费新 verdict，不增改 AC，不签 DONE。登记轮次 `Mac mini补核核清`；Dispatch-Id `P1-ENG-LOOP-002-Macmini补核核清-20261007T050726Z-58d2`。本轮只读本机文档、来源记录与相关源码，未运行部署包、模型、测试或任何板/Unity/runtime 操作，consumed=none；不代写用户原话账本。

核清依据：`docs/evidence/P1-ENG-LOOP-002-precheck.md`「Mac mini只读补核原始读数与逐维度用量」五个原始子节（以下 M/D/R/S 均指其中原流）；账本 10-07「用户选 SUB:1 方案 B…」及其引用的原只读信封；本提案「SUB1换机答复落实」§1–2、「补核答复落实」§2–4。实现提交及来源 SHA/目录从派发日志、git 与原件运行时解析，不手抄为新身份锚点。开工基线之后只有 supervisor 派发登记变动，本轮不纳入其提交/写入归因。

### 1. 用量、命令及停止纪律裁定

| 核清项 | 裁定 / 原流与限制 |
|---|---|
| SSH / 墙钟 / 重试 | S1 唯一连接，epoch 止减起 = 4.489479 s，按原表精度 4.489 s；monotonic 4.490 s，远端 4 s 是另一精度，不能替代连接完整墙钟。成功 rc=0，stderr 0 B、限时未触发；SSH 1/1 已耗尽，未用秒数不构成第二次连接许可，重试 0/0。 |
| 其余逐维度 | ping、模型加载、llama --version/--help、仓库/第三方 import、推理、HTTP（含 loopback/status/health）、服务启动/驻留、角色板写入、文件传输/复制、scenario/session/run ID、Play、runtime 写入、回放/评分、5060、外部 API、GPU·h、下载、安装、云均记录 0；完整脚本/原流未显示这些动作。不改设置/不提权/不连接46273。SSH系统登录日志/访问时间变化不冒称角色部署写入为0的反例，亦不能据此保证全系统零写入。 |
| 来源/顺序 | L0、M1–M6 和最终 D 原流支持别名与来源核齐后连接；本轮只读核本机 state/budget/checkpoint/summary 与16份收据现存，来源身份依据仍取 state.q4→verify-q4→admitted、transfer mmproj、server_sha256_now/bindir，不按双Q4文件名猜。M6只是交叉一致性，不替代期望来源。未重算/加载模型，也不认证原JET诊断为通过证据。 |
| 板命令闭集 | R00–R12 用 date/hostname/uname/id/command -v、test/stat/readlink、sha256sum/readelf/ldd、python3 --version、df/free、ss -ltnp、两模式pgrep及限时timeout，目标在原§2闭集内；有限shell组织与只读目录枚举未扫描无关全盘。ldd 为授权具名依赖读取，不记GGUF加载/推理，不能将其结果称目标程序运行通过。 |
| 本机ssh-keygen -F | 只读既有known_hosts、地址沿L0解析，没有生成/添加键、读私钥或连接；属于原“只读既有SSH配置”的定位手段，未扩出联网/改配置许可。三条键仅证明当时记录存在，不证明当前主机身份/硬件序列号。 |
| SSH -T / -o | BatchMode=yes、ConnectTimeout=20 是本次调用的非交互/连接限时参数，未写配置；未使用放宽主机键验证/改known_hosts选项，符合不改设置与单连接限时用途。stdin脚本不落板，不计部署文件传输；不能由此豁免后续真正传输额度。 |
| [ -w ] / 本机组织 | [ -w /home/jetson ] 是test访问判断、未写文件，符合父目录只读权限判断。系统Python标准库解析/计时、生成仅供stdin的临时读脚本、bash -n语法检查不运行部署包、不生成部署包；会话临时记录不计正式归档/回放。 |
| deps.py两次本机重跑 | 实现披露第三版前两版禁止项匹配及层级区分错误；三次是本机静态解析，不是两次SSH重试，也不占模型/测试维度。**前两版命令原流、rc、时刻和当时停止判定未附**，仅第三版sha/摘要不能复原错误首次暴露的时间；不能证明遇疑义即停、不能追认“零消耗即准许纠错续行”。保留执行记录不全及可能停止后续读的限制，不凭叙述判全部合规；不退款/重置用量，不要求本轮补跑。 |
| 明确停止顺序偏差 | **R11已输出owner_46273=UNKNOWN_no_process_column，之后仍执行R12两条pgrep，最后R99/final_stop_hits才收尾。** 原§3要求必需UNKNOWN出现即停止后续、不为补齐续探。因此“R11最后一项/未追加探测”自述不成立；两条pgrep虽在命令闭集内，执行顺序仍越过停止边界。保留R12为偏差后有限快照，不能当成严格停止符合证据；同一连接末尾的时间/账记录属收尾。没有第二SSH/权限升级/运行等后续消耗记录。 |
| 子命令/潜在失败路径 | 原流完整SSH stdout按围栏换行边界复算35,675 B/hash与记录一致，显式独立rc为22条0及两条pgrep的1；pgrep无匹配和计划根ABSENT是预期状态。并非每个子调用都单列rc：R04/R06的stat/readlink等有合并输出；R03/R07等仅打印rc，不在错误时立即STOP；R09 [ -w ]=no也未即时STOP。当前成功读数不证明这些未触发失败路径合规，不签失败路径验证结论。 |

归因仅为本轮接受侧授权/记录核清：已证R11后R12续读属执行停止顺序偏差；deps前两版为记录缺口、全过程合规UNKNOWN。不是独立finding，不新造CLASS/BC缺失或返工计数，不改原证据/历史verdict；保留已得事实不追认越界许可。mini子范围结束；Air未用余额作废，N-2 SSH1/2、ping5/10和N-1已用量不重置、不转用。全局实质blocks/release仍是ACQ R2-1按文件顺序已release，无新消耗性门release；不替代其他放行门。

### 2. 事实可保留范围与 UNKNOWN 逐项归口（不增改AC）

| 对象 | 可保留 / 裁定 | 不能推出 / 下一归口 |
|---|---|---|
| 三文件 / 设备 | R02三文件regular、字节/现算sha符合M3–M5期望、逐级路径非链接；R00与来源hostname/架构、三文件一致，支持同板快照。 | 不是硬件序列号绑定、全栈/数值等价或可加载证明；本项正式assets、部署摘要与启动前复核仍按AC-16另做，AC-16板端保持NOT_RUN。 |
| 共享库 | R03–R07：server AArch64 PIE，NEEDED5；ldd解析20实体无not found（8构建库、9系统库、3CUDA库），逐项类型/终点/sha，实体字节重加759,979,752 B；23项bindir名称/大小/链接与历史清单一致。 | 库无历史sha期望，本次hash是首次快照而非旧hash匹配；NEEDED/ldd不覆盖运行时dlopen（含libcuda），也不认证源码构建链或整栈身份。现AC-7/16/A2(d)仅三文件身份不变；身份范围选择交§3题LIB。 |
| 部署根 / 容量 | R09父目录类型/链接/属主及test可写已读，计划根/code/logs均不存在；R10可用磁盘160,143,314,944 B、available内存5,989,392,384 B、swap0。当前清单16文件242,801 B与§5.2相同。 | 不存在是新建前预期，不是部署缺失；没有创建/部署成功、完整峰值或服务工作集证明，200MB只是资源申请上限。今后同名根已存在不得覆盖，现场重新核前提。 |
| 监听 / 46273 | R11仅时点证明计划18081/18082无监听；46273有监听无归属，必须保持UNKNOWN。R12偏差后两模式无匹配，仅限两模式。 | 不猜Tailscale、不证明所有进程不存在、无共享槽冲突/未来空闲。用户“保持不碰”已答，不重问是否清理；服务放行仍待本人互斥确认，见§3题SLOT，无代理新SSH额度。 |
| 解释器 / 标准库 | R08 Python3.12.3、22个.py/包及5子模块文件存在。builtin/扩展定位不可证及更下层_socket/_hashlib/select等未枚举照记UNKNOWN；原命令明确允许这些静态不可证项，不因此追认运行可用性。 | 模块可import、ABI/架构支持、真实库动态加载、HTTP/schema响应/性能均未实测；不以版本/文件/无not found当可运行结论。真实入口仍留已签后的首次合同核验；若运行申请需依赖尚未核实环境事实，按engineering§9先核、额度0，不能凭附条件授权跳过。 |
| 惰性导入 / train_lora | 复读真实源码：language_serve.main在backend=llama-server时直接return _main_llama；该路径构造LlamaServerAdapter/SingleFlightRuntime，predict_one走loopback HTTP；不调用load_local_adapter/LocalHfAdapter/inference_engine。train_lora仅在inference_engine被local-hf构造/推理调用时import；module被部署/载入不等于执行其中所有函数。 | A2(e)禁止的是llama-server分支实际import train_lora/第三方，不要求删除共用文件中旧local-hf函数。现有分支源码无需新增AC/删除冻结文件/扩部署清单；不得换成默认local-hf。这是分支读码裁定，不是板上运行事实。 |
| 其余清单外惰性文件 | trackers的cv2及create_tracker的det_assoc_tracker→pose_gmc，以及train_lora→eng_sft/eng_asset receipts，均属于其他构造/后端路径；板服务在上述入口只取trackers的类型/clip_box_norm等纯函数，未调用跟踪器工厂。 | “所有分支传递闭包19件”不能作llama分支必需部署清单。桌面快层第三方/检测器不迁板；A2(e)/AC-7闭集不放宽。现有IsolatedDeployEntryTests两条隔离用例可作既有候选指针，未在本轮重跑、不能替代板上首次启动核验；未来若真实触达禁项即停交实现待裁定/原停点，需改AC依engineering§2追加，范围/资源变更回用户，不在本轮生效。 |

不将本轮源码读法扩大为新C轮或独立复核结论。JET旧诊断的偏差/STOP/UNKNOWN、ACQ暂停/attempt2非verdict/清理与各OPEN债仍保留。

### 3. needs_user：原题、完整申请及推荐（仅待转呈，无执行效力）

四题由supervisor原样转呈，用户答复须在发生会话逐字入账，再由Acceptance落实；本轮不向用户提问。request_id按ENV/FACT具名稳定区分，跨重派沿用；**这些是完整信封首签、STOP确认及FACT/合同选择，不是既有执行信封内SUB追加**，不占/复用已答SUB:1，不伪造其标题sha或SUB批准。COORD-015 §5.2 ENV/FACT/改AC均不可代拍，现行执行信封子额度块未启用。

#### (i) 完整B-main：P1-ENG-LOOP-002:B-main:ENV:1

**原题：§5阶段B信封签发（R1通过后，现按已消费R2理解）。** 原推荐出处「B-pre答复落实」§4；本次完整申请取§5.2“B0a核清回填”确定计划，以下逐维度原样限额，不取已被(j)收窄的历史4启动/370请求/故障重启计划。

| 维度 | 完整运行申请 / 计量与依据 |
|---|---|
| 设备 / 人 / 阶段 | MacBook Air运行Unity/会话/快层；同一Jetson Orin Nano 8GB Super单主臂，用户本人既有SSH前台启动板服务；mini只读换机不迁Unity，不借JET额度。B0b→B1收据→B2三剧本→B3评分/证据核实。 |
| SSH / ping | SSH≤3次（准备1、收据1、Play批次1），各≤3,600 s、累计≤10,800 s；ping0。失败连接计次，不暗添第4连接或借N-2/mini余额；服务必须在本次SSH结束前停止。 |
| session / 段 / 新run ID | session≤5，正式P1/P2/P3各1，环境性重试全局≤2且每剧本≤1，仅Unity未进Play/运行时锁冲突；每session段重建≤2；新run ID0。主臂失败、/status不可达不重试。 |
| Play / 墙钟 / T_sess | ≤5次，每次按钮墙钟≤420 s、累计≤2,100 s；T_sess≤290 s且守§3.1帧起点式；由操作者逐次记按钮时刻，420是资源限非性能线。 |
| 桌面YOLO加载 | 每session≤1、总≤5，按AC-3计数；段重建不添加载额度。 |
| 板服务 / GGUF加载 / 重启 | ≤2次（收据1、正常结束后Play批次1），每次启动=1次GGUF加载；故障重启0。首次失败即停，余额不许可重开失败批次。 |
| 板推理 / 收据重测 | ≤335（35收据+每session≤60×5，指定与核验共账）；收据重测0；失败/超时/内置尝试计请求，不能用余额重开失败批次。 |
| 非推理HTTP | ≤200，包含/status、/health和loopback健康轮询，失败计入；共享库/未知端口补探不在用途内。 |
| 板墙钟 / 服务驻留 | 每次SSH完整起止累计≤10,800 s，含准备/传输/清理/失败；每次驻留≤3,600 s、逐次记录起止，被SSH完整覆盖；非服务余量不改启动次数。 |
| 板新增峰值磁盘 | ≤200,000,000 B，部署独立根/code、logs及可归属cache/tmp/pycache；不传/复制模型/共享库、不删件抵扣。每次SSH结束前及停服务前du -sb，最大采样与df照记，不将采样最大称连续峰值证明。 |
| SSH文件传输 | 双向≤20,000,000 B、≤3批（16清单源码部署1、日志回传≤2）；242,801 B是现本机源码束，不含后续日志，实际文件字节共账。 |
| HTTP有效载荷 | 请求体+响应体双向≤60,000,000 B，逐请求访问日志求和（含异常/不完整）；125KB/16KB/8KB只是投影，原335请求投影约48,835,000 B，非每行保证；TCP/Tailscale封装不计。 |
| Air归档 / 峰值 | 每Play帧环≤140,000,000 B、会话≤85,000,000 B、合计≤225,000,000 B；全批≤1,200,000,000 B；已归档+当前runtime峰值≤1,450,000,000 B。归档移动不复制，每Play后du -sk记录。 |
| 正式归档零模型回放 | 实现≤2次、独立复核AC-18≤1次，只读归档、不写runtime；不借暂停ACQ信封。 |
| runtime写入 | 本项覆盖文件生成≤5次（每session1）、既有残留移动≤1次；不授权删除旧证据。 |
| --version / 身份核实 | 资产核实1次+两次正常服务启动自核，共≤3次；不含--help、换模型/重建/安装。预检未执行此项，不把旧JET横幅当本项新读数。 |
| 其余 / 设置 | 5060、外部模型API、另列GPU·h、云、下载、pip/安装/编译、模型文件传板/额外图像文件传板各0（推理JPEG计上列HTTP有效载荷）；板推理仅按上表请求/墙钟，不能移用桌面GPU。系统/SSH/沙箱设置不改。新增scenario ID0，session按本表，不新增run ID。 |

**推荐：先解决题LIB/SLOT及剩余事实/操作单前提，再按本表首签；当前暂不签完整运行。** 理由：静态资产/容量/模块级闭集已核，仍不能把未知端口互斥、未测的Python下层依赖/实际运行栈当已满足；engineering§9禁止依赖未核环境事实的维度提前申请签发。本表为完整待决申请规格，不是让用户一句“签”自动消除UNKNOWN或有条件开跑。备选为暂缓本项运行，门值与义务保持；不把暂缓擅自写成Lifecycle PAUSED。若用户另拟补充事实操作，先列具体闭集/额度另签，mini SSH1/1已耗尽，本轮不申请新SSH或动态诊断。

不重问已答(h)正式验证、(j)不启用5060/主臂失败就停、(k)本人启动。实际执行还须冻结操作单同步单主臂/本人启动/根/端口/计量/STOP，其PLAY_GOVERNING候选经接受只读核对及独立复核；采集前解析通过候选、记录HEAD/status/Unity日志。预算签发不替代这些门。

#### N-3：P1-ENG-LOOP-002:N-3:ENV:1

**原题：STOP缺省处置（随B-main信封）。** 原推荐“逐码确认§6.2（含S-RING记录NO_POSE并继续）”，理由为COORD-017不许未确认处置自行生效。用户已答延期，本次随完整申请转呈，不重问延期选择。**推荐逐码采纳以下11码**，取「B0a核清」§4现行申请，保持原判定/出处，只收窄与(j)相冲突的继续分支；备选逐码列不同处置，Acceptance按资源/合同规则再落实，未答不生效。

| 码（原判定见§6.2） | 推荐处置 | 理由 |
|---|---|---|
| S-PRECHECK | 停全部后续，回接受；不修前提/试连/换臂续行 | 已计划新根创建前不存在不冒充部署缺失；身份/链接/归属未核仍停报未知。 |
| S-RECEIPT | 停全部后续，回用户；重测0、5060分支0 | 收据6/8或schema拒绝；不借旧备用臂选项。 |
| S-IDENTITY | 停全部后续，回接受；不覆盖期望/换base/补包继续 | 按AC-6/16现身份范围；库扩绑定另走题LIB。 |
| S-ENVELOPE | 任一维度到限停止新增动作，安全收尾后回用户 | 不跨维度借余额，提前预留收尾，失败共账。 |
| S-LOAD | 停全部后续，回实现/复核，修复候选回停点 | AC-3单加载缺陷；不增加候选/测试额度。 |
| S-BACKEND | 首次backend_fatal停本次及全部后续，回用户；故障重启0 | 替换旧“同原因第二次”，落实(j)。 |
| S-REBUILD | 停本次计账；仅确认A5非主臂帧/发布段限制时下一既定剧本可继续；主臂失败或不能判明停全部回用户/接受 | 不重跑本次、不加剧本/改参数，限定继续分支。 |
| S-WALL | 停本次及全部后续，回用户 | 420 s按钮墙钟资源上限，非性能线。 |
| S-ARCHIVE | 停全部后续，回用户；保留超限/H-2身份/layout异常，不删筛后续跑 | 原225MB/H-2/layout限制，采样未超不称连续峰值证明。 |
| S-SERVICE | 停全部后续，回用户；本人在已签前台收尾范围内停止并核端口 | 不新开服务/清未知进程，释放不可核照记UNKNOWN。 |
| S-RING | 不停，静止车相应帧NO_POSE照记 | 描述性可评分性限制，不扩帧环/补采/改指标。 |

服务未就绪/退出（服务退出码4/5）、HTTP不可达属首次主臂失败，停全部，不因无backend_fatal日志漏过。正常none/ambiguous/解析失败仍按原漏斗/内置尝试计，不能擅改算法或新增性能STOP。STOP后仅允许已签范围内本人停止/端口释放/记账/保留工件和必要安全收尾，无新加载/诊断/删除许可。

#### 共享库身份：P1-ENG-LOOP-002:LIB:FACT:1

**原题：llama-server同目录共享库：保持三文件范围并披露限制，还是修订合同扩大绑定？** 用户“先取事实再定”已完成取事实步骤，本次不再要求重取。**推荐保持AC-7/16/A2(d)三文件身份，逐次披露本节20实体库快照、无旧sha期望及dlopen不在闭包的限制；不称整栈身份。** 理由：当前目标为受控小样本闭环描述，已有明确三文件契约；新增库机读绑定改变接口/摘要/验收且仍不能自然覆盖驱动dlopen。备选“扩大绑定”：先由实现把库集合、链接/驱动策略、首次基线来源、传播到/status/收据/会话的字段及失败行为写待裁定，接受按engineering§2追加AC修订，用户另裁范围/资源，相应K1/K3稳定候选核对/复核；本轮未写修订、未生效、未授权部署。选择保持也不使剩余依赖/互斥事实变通过。

#### 46273与共享槽：P1-ENG-LOOP-002:SLOT:FACT:1

**原题：补核快照交用户确认46273归属与本项共享槽互斥；用户确认前不放行服务。** 新事实仍UNKNOWN，不再问已答“知不知道/清不清理”，不推断Tailscale归属。**推荐由本人提供已核归属及明确本次Jetson/18081/18082服务窗口与其他JET/LOOP任务互斥确认；无法确认则继续停在服务前。** 理由：不占计划端口仅是瞬时快照，不能证明无并行任务/资源冲突；归属事实不能由supervisor代答。备选本人明确要求在归属UNKNOWN的保留条件下继续且确认互斥：这是对原放行前提的用户直接变更，须逐字说明保留未知、授权范围后由Acceptance裁定落实，当前无此效力；不允许代理sudo、清进程、改设置或新连接。保持不碰46273已答，不作为新选项。

### 4. 收工门与下一责任方

下一责任方为用户答上述四题；Acceptance仅在逐字账本形成后落实。没有已签可执行运行动作；不把补核余额转作部署/启动。完整信封申请的未核环境限制、冻结操作单停点、采集HEAD/status/Unity日志、AC-18独立证据核实保持。AC-14/15/18与AC-16板端NOT_RUN，无UNITY_NA、不签DONE；N-1用量、旧债、ACQ暂停/非verdict/清理和旧余额不转用保持。状态板只写交接与本轮Log，历史核清/证据原文不覆盖。

## Mac mini四题答复落实（2026-10-07，Acceptance）

**结论：完整 B-main 已由用户按原申请表签发，LIB 选择与 N-3 十一码确认已落实；46273 归属已获用户事实答复，服务窗口互斥尚未确认。B-main 运行未放行，先交 mini Implementation 做零消耗操作单候选与事实缺口准备。** 本节是四题现行入口，替代抬头及前述各节中“完整运行/N-3未签”“mini原件/别名未核”“四题待答”的旧快照；历史读数、偏差与用量不回写。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE`、AC-14/15/18与AC-16板端 `NOT_RUN` 保持，无 `UNITY_NA`、不签 `DONE`。本轮不是 D/C/R，不首签或追加额度、不签 verdict；Dispatch-Id `P1-ENG-LOOP-002-Macmini四题答复落实-20261007T053433Z-f4d6`。仅本机文档裁定与自检，consumed=none。

### 1. 原话优先：LIB、SLOT 与 N-3 生效边界

授权唯一来源：`docs/authorizations.md` 2026-10-07「P1-ENG-LOOP-002 — 用户答 Mac mini 补核核清四题：签完整 B-main 运行信封（不随推荐）、N-3 逐码采纳 11 码、共享库保持三文件、46273 归属 = tailscaled（supervisor 会话代录）」。用户对第四题说“签，先推进”，**没有采纳“暂不签，先解决前提”的推荐**，也没有选择暂缓；不得将推荐写成用户决定。账本 supervisor 读法 (a)–(f) 与原话及题面范围一致，无需更正账本；其中“签发”指用户授予上限，不能扩读成环境事实已通过或现行门已豁免。“有什么授权的可以先列出来”是列清单的要求，不是给清单预授权。本会话不代写账本。

**LIB:FACT:1 已答闭合**：保持 AC-7/16/A2(d) 三文件身份，绑定 C2 Q4、mmproj、单个 llama-server 二进制；不新增共享库机读身份字段、不扩大摘要或验收。每次资产核实/启动记录及后续证据披露「Mac mini补核核清」§2 的20实体库快照及来源、没有历史 sha 期望、NEEDED/ldd 未覆盖运行时 dlopen 驱动库（含 libcuda）；本次 hash 是首次快照，不能写旧 hash 匹配或整栈身份。逐次披露不授权重新哈希/复制20库，若库发生变化照记身份限制并回接受，不擅自绑定新基线。LIB 已答不重问，三文件事实仍不替代 AC-16 正式板端资产工件。

**SLOT:FACT:1 部分已答**：接受用户提供的事实“46273 是 tailscaled（Tailscale 系统守护进程，root，PID 2033）在 tailnet IP 上的监听——不是 JET/LOOP 任何任务进程，也不是推理服务”。来源是用户声明，不冒称非特权 R11 原流已读出进程；原流 UNKNOWN 和 R11 后 R12 续读偏差保留。归属子前提已满足，**原“用户确认归属与共享槽互斥”是合取前提，尚未全部满足**：这句话只排除了46273本身是任务/推理服务，没有确认本项准备、收据、Play 服务窗口内同板资源和18081/18082与其他JET/LOOP任务互斥。`SLOT:FACT:1` 沿用，剩余只问该窗口互斥，不重问归属或是否清理；用户明确确认前不放行服务，不 sudo、不清未知进程、不改设置、不连接46273。旧18081/18082空闲只是一时快照，启动前仍按操作单核当前占用。

**授权边界修订 2（§5/§6.2/§7；不改 AC）**：用户逐码采纳「Mac mini补核核清」§3 N-3 表，且同时签完整信封，COORD-017 的用户确认条件现已满足；下列11码处置成为本项现行合同，优先于 §6.2 及旧操作单冲突文字。原判定、出处、描述性读数线、算法/采样/验收均不变。确认处置已生效与获准执行各步骤是两回事：仅在对应步骤通过环境、操作单/停点和现场门且其额度可用时执行；不得借 N-3 进入未放行 B-main。零消耗准备发现前提失败同样先停报，不因 S-RING 的继续分支扩大准备范围。

| 原因码 | 逐码落实的处置与生效限制 |
|---|---|
| S-PRECHECK | 停全部后续，回接受；不修前提/试连/换臂续行。计划新根在创建前不存在不是部署缺失；必需身份、链接、归属未核仍停报未知。 |
| S-RECEIPT | 停全部后续，回用户；收据重测0、5060分支0，保留6/8或schema拒绝。 |
| S-IDENTITY | 停全部后续，回接受；不覆盖期望、换base、重建补包或扩大三文件身份继续。 |
| S-ENVELOPE | 任一维度到限即停新增动作，预留已签安全收尾后回用户；不跨维度借余额。 |
| S-LOAD | 停全部后续，回实现/复核，修复候选回停点；不增加候选/测试额度。 |
| S-BACKEND | 首次backend_fatal停本次及全部后续，回用户；故障重启0，旧“同原因第二次”不再可用。 |
| S-REBUILD | 停本次并计账；仅确认A5非主臂帧/发布段限制时下一既定剧本可继续；主臂失败或不能判明停全部回用户/接受。不重跑本次、不加剧本/改参数。 |
| S-WALL | 停本次及全部后续，回用户；420s是按钮墙钟资源上限，非性能线。 |
| S-ARCHIVE | 停全部后续，回用户；保留超限/H-2身份/layout异常，不删筛工件续跑，不把采样最大称连续峰值证明。 |
| S-SERVICE | 停全部后续，回用户；本人在已签前台收尾范围内停止并核端口，不新开服务/清未知进程；释放不可核照记UNKNOWN。 |
| S-RING | 不停，静止车相应帧NO_POSE照记；不扩帧环、补采或改指标。 |

服务未就绪、退出（退出码4/5）及HTTP不可达均属首次主臂失败，停全部、故障重启0，不以缺backend_fatal事件继续。none/ambiguous/正常解析失败按原漏斗及内置尝试共账，不新增性能STOP。STOP后只允许已签范围内本人停止/端口释放/记账/保留工件及必要安全收尾，没有新加载、动态诊断或删除许可。

### 2. B-main 签发逐维度核对及 engineering §9 效力

用户题面明确引用「Mac mini补核核清」§3(i) **完整表**，因此账本信封的简写不删除该表的细分限制；不是旧 §5.2 的4启动/370请求版本。下表逐维度转写已签边界，不由接受角色新签。所有本次 B-main 维度实际消耗均0，已有N-1/N-2/mini子范围独立原账不重置、不转入本表。

| 维度 | 用户签发与完整申请表核对（均一致） | 当前执行效力 |
|---|---|---|
| 设备/执行人/阶段 | Air会话、快层及Unity；同一Orin Nano 8GB Super单主臂；本人既有SSH前台启动；B0b→B1收据→B2三剧本→B3评分/证据核实 | 不把mini补核换机授权扩为mini运行/部署授权；本人分工不变。 |
| SSH/ping | ≤3次，准备/收据/Play各1，各≤3,600s，累计≤10,800s；失败计次；ping0 | 已核链路可支持准备连接预算，但本轮及下一mini交接均不连接；不得暗作第4连接或补核专用新次数。 |
| session/段/run | session≤5；P1/P2/P3各1，环境性重试全局≤2且每剧本≤1，仅Unity未进Play/运行时锁冲突；每session段重建≤2；新run ID0 | 采集门前不可消耗；主臂或/status失败不可重试。 |
| Play/墙钟/T_sess | ≤5次，每次≤420s、累计≤2,100s；T_sess≤290s且守帧起点式 | 用户已签Unity/Play=是；操作单/现场放行前可执行值0。 |
| 桌面YOLO | 每session≤1，总≤5；段重建不新增加载 | Air现场条件及采集门前不可加载。 |
| 板服务/GGUF/重启 | ≤2次（收据1、正常结束后Play批次1）；每次1次GGUF加载；故障重启0 | 依赖未核环境且互斥未答，目前可执行值0；不得先烧首次加载探前提。 |
| 板推理/收据重测 | ≤335（35+60×5）；失败/超时/内置尝试共账；重测0 | 环境及服务/收据门前可执行值0。 |
| 非推理HTTP | ≤200，含loopback/status/health及失败 | 环境及服务放行前可执行值0；不用于库或46273补探。 |
| 板墙钟/驻留 | SSH完整墙钟累计≤10,800s；每次驻留≤3,600s、被SSH覆盖、结束前必停 | 准备与运行共账，服务相关可执行值0；非服务余额不增启动次数。 |
| 板新增磁盘 | ≤200,000,000B，独立根/code、logs和可归属cache/tmp/pycache；不复制模型/库，不删件抵扣 | 容量/父目录有读数，不证明部署成功/峰值；操作单核清前不写板。 |
| SSH文件传输 | 双向≤20,000,000B、≤3批（16源码清单部署1、日志回传≤2） | 源码束242,801B为原读数，候选变更后重算；操作单核清前不传，mini→Air来源复制不在本维度内。 |
| HTTP有效载荷 | 双向≤60,000,000B，异常/不完整按实际访问日志计；不计TCP/Tailscale封装 | 非每行体积保证；随运行维度锁住，不借投影替代计量。 |
| Air归档/峰值 | 帧环≤140,000,000B、会话≤85,000,000B、每Play≤225,000,000B；全批≤1,200,000,000B；已归档+当前runtime≤1,450,000,000B | 只移动不复制，逐Play du；真实采集前不写/搬归档。 |
| 正式归档零模型回放 | 实现≤2次，独立复核AC-18≤1次；只读、不写runtime | 上限已签；正式工件尚不存在，下一mini准备不评分，不挪作旧归档重放。 |
| runtime写入 | 覆盖文件生成≤5、残留移动≤1；无删除许可 | 仅Air正式运行范围，准备轮不动runtime。 |
| --version/身份 | 资产核实1+两次正常启动自核，合计≤3；不含--help、换模型/安装/重建 | 依赖未核运行栈的可执行值0；不扩作任意动态预检。 |
| 其余/设置 | 5060、外部API、另列GPU·h、云、下载、pip/安装/编译、模型/额外图像文件传板、新scenario/run ID各0；设置不改 | 推理JPEG仅计上列HTTP；SUB/决策信封未启用；没有库扩绑定、远程诊断或安装的默示许可。 |

**签名存在，但不追认提前申请符合 engineering §9。** 原申请自己已注明下层Python依赖/实际运行栈未核，§9规定依赖这些假设的维度在核实前不申请签发、按缺项0；用户一句“签，先推进”没有逐字修改此基础设施规则，也未断言这些事实已核。因此上表保留用户签发的上限与独立原账，**依赖未核事实的服务/GGUF、推理、HTTP、二进制执行及其下游Play等维度当前可执行值0**，不伪称全表未签、不自动附条件开跑，也不由接受角色把UNKNOWN当通过。已核资产路径、ELF AArch64、20库静态解析、容量及链路仅支持各自事实。准备SSH/静态读取不天然依赖Python动态可用性，可在后续具名操作单核清的原准备1次内取必要原读数；本轮不授mini新连接、不复用其耗尽子范围。

最短事实补齐应先在mini只读既有来源/源码，把必需依赖与不触达的local-hf/跟踪器分支分开，列明Python下层扩展与其库/架构的缺口、现有原读数能否覆盖真实执行栈的版本/架构支持、工具链及磁盘/内存/链路。不能把模块文件存在、无not found或旧JET成功叙述当本项可运行结论；也不要求先做一次未授权推理才能申请推理。目标条件下已有原始环境读数可补来源而不重跑。HTTP/schema响应、实际RSS/工作集、时延等首运行输出仍留放行后的首次合同核验，不预判可达/通过，不新增内存或性能STOP。

若仅用原签准备SSH和具名非特权静态读命令即可补齐所依赖事实，先核事实、Acceptance逐维度确认原签上限与已核合同仍相符，再作明确放行；不为同一已签额度机械重问。**若必须新增import/动态无模型探测、另一SSH/换执行机或其他原用途外动作，先由实现列逐字命令、机器、次数/墙钟、写入/传输等维度与停止闭集，交接受核清后由用户另签**（§4清单ENV:2）；现在未形成该子合同，不执行、不预报它已获授权。事实要求引起合同/额度变化时，按engineering§2先追加修订并另请用户决定资源；现有运行签名不覆盖变化部分。用户要直接豁免§9，须另行明确授权协调批次，不能从本轮原话推定。

### 3. 未闭门与最短执行顺序（mini / Air / Jetson 分开）

**下一写角色为 mini Implementation，限零消耗文档候选准备**，按本节和原「B-pre答复落实」「B0a核清」「Mac mini补核核清」完整合同读取。可做：只读本机已存来源、依赖清单与真实源码；准备事实缺口表/必要静态命令或待签无模型预检子合同；修订 `docs/evidence/P1-ENG-LOOP-002-play-ops.md`，在具名停点证据中附合同映射、完整候选diff解析式及四条件自证/未核风险。**不SSH、不复制、不import部署包、不模型/测试/回放、不板/Unity/runtime操作**；不把后续B-main预算加入此零消耗交接。纯操作单候选的相称验证据engineering§6及workflow§4.3.1写明适用性/已有证据，不能假报新全套通过；若需要任何运行验证或代码修改，先停止准备范围并交接受裁定机器/额度。

操作单须落实 AC-10 的既有义务：已签/暂锁维度分列；单主臂、本人启动、独立 `/home/jetson/eng-loop2/code` 与 `logs`、仅127.0.0.1:18081及Tailscale:18082；三文件与库披露；准备1+服务2的SSH/墙钟/传输/驻留计账；故障重启及收据重测0；十一STOP和首次服务/HTTP失败停全部；删除/status不可达环境重试分支；runtime残留仅移动与逐session布局归档；异常HTTP字节计量及采样峰值限制。不覆盖同名既存根，不与JET根混写。

随后按依赖顺序接力：

1. **mini候选 → Acceptance下一实际C轮 → 独立Review。** 冻结操作单是本项点名的PLAY_GOVERNING文件，其改动必须纳入完整候选diff，不能以文档改动绕过。轮号从实际C/R记录解析，不照抄历史AC-18的C2/R2。候选相对最近通过候选的PLAY_GOVERNING diff非空则开下一实际R轮；若返工按既有计数/冻结集规则，不预签通过。没有这次通过不得启动依赖操作单的B0b/加载/采集。
2. **用户在Air/Jetson补现场前提。** 用户先给§4 SLOT确认；用户在Air对齐经核对/复核的新候选与现有来源/资产，既有C2原件缺失则停，不让mini代理复制或借SSH部署批次复制mini→Air。准备命令与计量清单核清后，用户经Air既有SSH在原准备1次内只读取缺口事实（不sudo/改设置/动态诊断），保存逐命令stdout/stderr、rc、完整起止与账。若需ENV:2则先签其完整子合同。账本签名不代用户完成这一步。Acceptance核清事实与原签效力、现场门后明确放行，未知不强行消除。
3. **B0b/资产与B1。** 获放行后在Air/同板按已复核操作单做独立根部署、三文件/部署摘要正式核实、assets输入与--version计账；用户本人在既有SSH前台启动第一批服务，Air走生产35请求收据，退出码0且身份/schema等满足才可进Play。失败即N-3停，第二启动额度只用于第一批成功正常结束后的Play批次，不是修故障重开。代理不能替本人启动服务。
4. **每次采集现场门（Air）。** 当轮发令角色运行时解析最新通过候选，记录Air的 `git rev-parse HEAD` / `git status --porcelain`，在开始前写本轮 `docs/unity-test-log.md`，核Unity版本/场景/配置、无_Recovery、实际收据绑定与完整工作树dirty判据。workflow§4.5允许白名单文档差异，但当前操作单§1.1/§1.2和AC-6会话绑定更严（HEAD等值、全树干净）；先按严格合同准备可执行版本，**不能借宽规则忽略绑定**。若正常复核文档提交使等值不可满足，由实现写「待裁定」，接受按engineering§2追加AC-6/AC-10解释或修订再核对/复核，实质接口/资源变化交用户，不在本轮改成任意HEAD。然后用户本人在Air做三剧本、按Play/停止按钮、只凭实时预览选择、逐次记录墙钟/失败/目检，第二服务批次仍由本人前台启停并核释放。
5. **正式工件 → 实现自证 → 下一实际C轮 → AC-18独立证据核实。** 工件含play/four-numbers/ledger与正式资产、收据、H-2/layout/STOP和用户目检，实际消耗逐维度记账。独立复核仅1次已签零模型重放，与生成时刻类字段外逐值相等、账与信封/操作单一致；相对最新通过候选PLAY_GOVERNING无diff则原复核文件具名「证据核实@K1K2K3K4」不开新轮，有diff则下一实际R轮。任何运行后补丁保留“未在真实条件下验证”，不将代码R2 PASS替代新证据。三证据齐备才另作收尾裁定，本轮不保证通过。

**Consuming判定**：本轮和下一mini文档准备不创建/消耗scenario/session/run ID、Play或API，`no`；签名本身不消耗。Air真正进入B-main session/Play的交接才是`yes`，此前更新交接并全局核单消耗性上限、Gate-echo及完整blocks/releases，不能把采集挂在零消耗行。本轮全局仍0条消耗性+2条零消耗（JET等待用户方向、LOOP准备），暂停项不恢复；全局唯一实质ACQ R2-1 block/release已顺序配对，缺陷账本无新增release。SLOT/环境/操作单门即使没有blocks机读行也保持有效。

### 4. 后续用户本人授权或操作清单（needs_user；不含预授权）

已答LIB、N-3、(h)正式验证、(j)不启用5060、(k)本人启动、完整B-main上限不重问。以下分清“还需决定”和“已授权但必须本人执行”；均由supervisor列入检查点，发生会话原话入账/事实或Unity日志后再按对应门落实。本轮不向用户提问。

| request_id | 用户专属事项 / 时点 | 推荐与理由 |
|---|---|---|
| `P1-ENG-LOOP-002:SLOT:FACT:1` | **仍需确认**本项准备/收据/Play服务窗口与其他JET/LOOP任务在同板资源、18081/18082互斥；46273归属已答 | 推荐明确该窗口互斥；无法确认保持服务前停止。归属排除不等于窗口承诺，不能由代理代确认。 |
| `P1-ENG-LOOP-002:B-main:FACT:2` | **仍需本人现场操作/提供原读数**：在Air对齐候选与来源，按核清后的原准备SSH取Python下层/实际栈必要事实及当前根/容量/端口；不要求本轮立即运行 | 推荐先由mini备齐缺口与逐字清单，再本人提供目标条件原读数；§9依赖假设尚未核，不能用旧JET诊断结论或静态文件存在替代。原准备预算内不再签相同额度。 |
| `P1-ENG-LOOP-002:B-main:ENV:2` | **条件性新授权**：若上项无法在原用途内补齐，先提交明确命令/机器/次数/墙钟/写入/传输/STOP闭集的独立无模型预检子合同，再请用户签；现在只列准备要求 | 推荐只签核清后的最小必要子范围、无模型/无Play；下层import或动态探测不在旧只读补核闭集，不拿已签首次服务加载试未知环境。当前此新增类别/额度0，不预定数值或启用SUB。 |
| `P1-ENG-LOOP-002:B-main:USER:1` | **已授权、须本人操作**：各门通过后在Air既有SSH前台启停Jetson两次正常服务、核端口释放及用量，不含故障重启 | 推荐照新复核操作单逐字执行；(k)明确本人启动，后台驻留/代启动/46273探测均无许可。 |
| `P1-ENG-LOOP-002:B-main:USER:2` | **已授权、须本人操作**：在Air按通过版本执行Unity三剧本及有界环境重试、按停止/记墙钟/实时预览选择/目检反馈；采集前发令角色先记HEAD/status/Unity日志 | 推荐收据合格、现场版本与操作单门全满足后再Play；mini不是Unity主机，代码通过不等于用户验证，失败/跳过和NO_POSE照记。 |
| `P1-ENG-LOOP-002:B-main:CHANGE:1` | **仅触发时另决定/授权**：补核或STOP要求换设备/栈、改AC/接口或库身份、安装下载/额外复制、修改设置、增加SSH/加载/重测/Play/回放等额度、改变主臂停止处置；若需豁免§9则明确协调授权 | 推荐先保留失败/UNKNOWN与账，提交具体差异和逐维度申请再决定，不为可能事件先扩大信封；engineering§2/§8–9禁止用“先推进”或剩余额度追认新类别/边界。未发生不提请 blanket 授权。 |

与本项无关的ACQ恢复、旧残留永久清空、5060副本删除、JET新方向不作为B-main前置或新授权项混入；其既有独立清理/暂停/OPEN义务仍按原台账，B0b可动的仅原签残留移动≤1。N-1用量、mini SSH1/1耗尽及停止顺序偏差、deps原流缺口、旧JET诊断限制/UNKNOWN与ACQ非verdict/清理、各旧余额不转用均保留。本轮不增加AC、finding或C/R计数。

open_items: none

## mini操作单待裁定答复与 CHANGE 申请（2026-10-07，Acceptance）

**本节答复实现证据 `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` §8 全部八项；随后以 C3@K1K2K3K4 核对当前原候选，未代实现修改操作单或代码。** 四题原条、签发逐维度和旧核清仍完整保留。实现提出的资源单位/旗标选择不能仅因出现在待裁定表就自行生效；本节独立区分既有读法与需用户决定的申请，C轮不新增AC。完整候选、映射/四条件及PR-8…14见 `docs/evidence/P1-ENG-LOOP-002-C3-K1K2K3K4.md`。

### 1. IR-M1…M8 逐项裁定

| 编号 | 本轮裁定 / 既有合同效力 | 下一处理与未闭项 |
|---|---|---|
| IR-M1 | **需要另出代码候选、回K1/K3；不能按备选“保留缺省代码、先加载试未知”放行。** 当前命令只传-m/mmproj/host/port；原JET显式旗标/内存事实不证明当前缺省栈可运行，源码归档默认/理论KV量也不证明当前二进制必然OOM。engineering§9要求先核目标条件事实。 | 新旗标必须先冻结（下节AC-7修订2申请/CHANGE:1），不能由接受在C轮加义务或写代码。推荐完整采用既有原读数的十项资源旗标，不选其子集凭旧读数背书；新代码需AC-7失败映射/CLI与临时子进程夹具及相称停点证据、C核对/独立Review。现在只交Review检查现候选，未派实现改代码/运行。 |
| IR-M2 | **不采纳免计/result的默示资源解释。** GET/result不执行模型，原签“非推理HTTP≤200”未逐字豁免轮询；至少status/health/loopback健康及失败明确在内。保守现行口径/result亦计该200。335推理失败/超时/内置尝试共账，不能缩为accepted成功POST；wrapper POST与其实际chat须关联，不能把同次实际模型调用重复当两个推理，也不能漏失败尝试。 | CHANGE:2由用户选择维持总200并预算不足STOP，或先给轮询独立硬上限/改总限再另签；未选择不生效。Air↔language_serve每一/result/status/异常/不完整字节仍计60MB；非推理分类变化不豁免字节，不把loopback复制流再次当Air传输。静态轮询数量投影不称实耗/保证余量。 |
| IR-M3 | **不能直接裁“一条认证连接多channel各免费”为原签含义。** 原条≤3次准备/收据/Play各1及失败计次没有明示无限复用通道；把多ssh调用合并成一单位是资源解释变更。 | CHANGE:3推荐用户明确最多3认证主连接、各目的不变、有限通道闭集、每单元从尝试前至关闭后≤3600s/累计10800s。必须禁止socket失效时自动新建连接；任何新认证/失败尝试实计。准备脚本直接ssh与CM操作单须统一；未签时不执行。-o不写配置不能代替额度授权。 |
| IR-M4 | **认可“发布证据来源与执行源码检出分离”的解决方向，但当前命令不满足。** 原等值+全树干净门结构上不能读取后来写通过行的工作树review；必须保持实际HEAD=通过候选、收据/报告/会话绑定同值及dirty=false，不准任意HEAD/脏树豁免。 | AC-10修订1解释申请见§2：只允许固定已推送引用读取后续复核/授权证据，执行检出仍为最新有效通过候选；必须排除任何后续PLAY_GOVERNING差异，尤其操作单，不能grep掉全部docs。采集前实际记录HEAD/status后在独立文档检出写Unity日志并推送，再回执行检出重核。现在不变冻结操作单/AC-6；若改变绑定字段/接口须用户另决定。 |
| IR-M5 | **采纳为A2(e)既有闭集的调用读法**：系统Python带-I/-S/-B不加载site/.pth，避免第三方钩子与pycache；真实入口自行插入PROJECT_ROOT，清单内路径可据源码定位。 | 只接受隔离意图，不声称在板上import/运行已证。3.12.14源码代理不覆盖板3.12.3构建/函数内动态依赖；必需事实仍UNKNOWN则ENV:2另签最小无模型子合同，不挪首次服务加载试环境。无需新增AC或第三方安装。 |
| IR-M6 | **采纳已有身份比较链的等价读法**：传输完整性逐文件16项同序sha比较；服务启动自算部署摘要，/status→报告→收据→会话再与Air同纯函数摘要比较。 | 不免板端摘要或AC-16本项正式assets，不用JET诊断替代；B0b不另执行板端deploy_digest可减少动态动作。必须完整比较清单含自身、缺件即停，不只哈希三模型资产。未放行前不传/执行。 |
| IR-M7 | **拒绝以旧2.48s单次读数自动冻结20s就绪失败阈值，拒绝只在成功listening时估算计量。** 默认300s/0.25s规划上界约1201/启动；即使免/result，两个健康轮询也无≤200保证。 | 与CHANGE:2及AC-7修订2申请合并：推荐真实健康尝试计数、失败也计，在下一HTTP前守已签总账并预留status/收尾；若要改轮询间隔/超时/额度先给明确合同、最坏分配、失败终点再用户决定。20s只是实现示例未生效；代码相对通过候选需新停点，不在C轮加测试义务。 |
| IR-M8 | **采纳原3目的/3批用途内的顺序分配**：准备#1只读取必需事实，接受核清后，部署+资产核实在收据#2首次启动前，成功正常结束才开Play#3。四题§3步骤2–3已明确该顺序，不新增资源。 | 受IR-M3计次决策/现场放行制约；准备1、服务2、传输部署1+回传≤2、version1+2等原限不变。必须拆准备与运行G门，来源先齐、准备回来停下；不允许第4连接/补核重试/用mini旧额度。未签新单位不执行。 |

### 2. AC 修订及资源 CHANGE 申请（全部未生效）

以下只写具名申请，不加入冻结AC表、不计已生效修订；原三条AC解释修订仍3、新AC仍0。用户选择须发生会话原话入账，接受另行核清并冻结具体文本/验证范围，然后实现形成新稳定候选。未答则现有可执行值不提高，不由supervisor代拍。

| request_id / 拟修订 | 可审阅的差异申请、推荐与理由 |
|---|---|
| `P1-ENG-LOOP-002:B-main:CHANGE:1` / **AC-7 修订2申请** | 推荐选择代码路线：llama分支固定 `--parallel 1 --ctx-size 2048 --n-gpu-layers 99 --fit off --no-warmup --no-webui --no-cache-prompt --cache-ram 0 --cache-reuse 0 --offline`（十项逐字闭集），原-m/mmproj/host127.0.0.1/port保留；prompt/schema/decode/三文件身份与local-hf不变。该栈条件须由用户明确选定，接受再冻结，不从“保持三文件”推定同意改变上下文/并行/缓存。代码路径限原§4.1具名文件，新代码候选回K1/K3（既有K1K2K3K4停点计数不重置）；计量改动另按CHANGE:2具体选择冻结。模型/板/Play执行仍0；本派发无测试许可，N-1累计2/3、余1非本轮可用，后续验证先核原信封适用范围，不擅自申请扩大或称已耗尽。理由：旧唯一环境读数只覆盖显式条件，首加载不能做未核环境探针。 |
| `P1-ENG-LOOP-002:B-main:CHANGE:2` / **AC-7修订2申请的计量部分** | 推荐A：保留非推理HTTP≤200，逐次/result、status、health（含loopback与失败）共账，在下一请求前预算不足即S-ENVELOPE，不保证335请求余额均可用；335仍实际推理尝试上限、60MB字节全计。拟以代码计量覆盖健康成功/失败终点与总账，不用成功listening除以0.25作唯一来源。B为实现所求轮询豁免/单列：须先列/result闭集、硬上限、失败计账、两次健康与status最坏分配再用户另签；**当前不申请一个无界的新类别，不提高200，不冻结20s**。理由：把GET/result并入推理会改变用户签发含义，且就绪轮询仍可能单独超200。 |
| `P1-ENG-LOOP-002:B-main:CHANGE:3` / SSH单位申请 | 推荐明确“≤3认证主连接、准备/收据/Play各1”；每单元通道只限已列静态读/部署/前台服务/释放/日志收尾，有限次数清单由操作单列齐，无后台服务，不写SSH配置。尝试含失败计次；主连接尝试前至全部通道/主连接关闭后计墙钟，单次3600s/总10800s；禁止socket缺失自动回退新连接，每次实际新连接重新扣数，连接失败不重试。文件20MB/3批及驻留等原限全保留。理由：否则当前多条ssh调用不能据未明口径强称只用了3次。 |
| `P1-ENG-LOOP-002:B-main:CHANGE:4` / **AC-10 修订1解释申请** | 推荐采纳严格双来源结构：运行时固定已推送发布引用，读最新有效复核/授权；核通过候选到发布引用仅规则允许的非PLAY_GOVERNING文档差异，本操作单必须与通过候选对应；执行树detach通过候选、全树干净。实际HEAD/status先采集，另文档检出登记Unity原流后，采集检出重核相同HEAD/干净再运行；报告/收据/会话仍绑定实际通过候选，无接口变化。理由：消除review自引用不可能，同时禁止用新操作单配旧PASS。此解释申请待用户明确选择后接受冻结、操作单新候选核对/复核，不在当前C表改AC；如需任意HEAD或dirty豁免，须提出另一个实质AC-6修订，当前不推荐/不申请。 |

上表不是新的可执行信封；所有新增/变化部分未签0。已签B-main自身各上限仍原值，不撤销、不重新首签、不从条件申请增加连接/加载/Play/测试。不得实现时任意删成“至少五项”。

### 3. C3结论、下一角色及 needs_user

**照交新鲜上下文独立Review，先核稳定四条件；实际下一有资格轮为R3@K1K2K3K4。** 当前AC-10不满足、执行口径未冻结且有占位/门循环；本角色不退回第二次、不签Review verdict、不为了照交声称条件已满足。Review依真实候选/完整合同及累计计数决定REVIEW_BLOCKED或开轮/结论；不预签PASS，不开启依赖SSH/代码/Play。若需实现修复，按Review结果/用户已入账决策形成另一候选，回同停点，不用本C轮自动授实现/测试额度。

needs_user（本会话不提问，由supervisor转呈；每条推荐与理由）：

- CHANGE:1：推荐选显式十旗标的代码路线并冻结AC-7修订申请；缺省执行栈没有目标条件事实，不能首加载试未知。
- CHANGE:2：推荐先维持≤200逐次非推理HTTP共账并预算不足STOP；轮询豁免或新上限须另列有界申请，不能由接受改变签名含义。
- CHANGE:3：推荐明确有界三主连接/通道计次，禁止自动第四连接；原≤3次没有明示多channel免费。
- CHANGE:4：推荐严格发布证据/运行检出双来源解释；保持HEAD/dirty绑定并阻止新操作单借旧PASS。
- SLOT:FACT:1：推荐确认准备/收据/Play窗口同板资源与18081/18082互斥；46273归属已答，不能代未来窗口承诺。
- B-main:FACT:2：推荐新候选通过后由本人在Air齐来源并在核清的原准备预算取必要目标事实；mini静态代理不证明板依赖运行。ENV:2只在仍缺且必需时先另签最小子合同，现在不动态探测。
- USER:1/2（已授权本人动作）：推荐收据与现场门齐后本人前台启停、Unity三剧本及目检；不重签相同额度，不让mini/代理代操作。

原LIB/N-3/完整B-main签发不重问；AC-14/15/18与AC-16板端NOT_RUN，无UNITY_NA/DONE；旧债/暂停/偏差及独立用量不重置。本轮consumed=none，零SSH/复制/模型/功能测试/评分/Jetson/Unity/runtime。全局0消耗性+2零消耗，Gate-echo与blocks/releases原门保持。

open_items: IR-M1,IR-M2,IR-M3,IR-M4,IR-M7

## R3阻断消费与用户待决（2026-10-07，Acceptance）

### 1. REVIEW_BLOCKED 消费与不变边界

本轮按 supervisor 派发 `R3阻断消费`，消费 `docs/reviews/P1-ENG-LOOP-002.md`「R3@K1K2K3K4 派发（2026-10-07）」§0–4 / Verdict。依据 workflow §4.3.1 与 engineering §4–5：稳定条件①不成立（IR-M7 启动占位、IR-M1 旗标接口待冻结、IR-M3 SSH 单位待用户决定），故 **REVIEW_BLOCKED 已消费，R3 未开轮、不计复核轮次，返工计数保持 1/2，无冻结集**。这不是 REWORK_REQUIRED，不适用“返工直回复核”。本轮不是新 D/C/R，不改最新 C3 核对表，不新增 AC、finding、分级或归因计数。

阶段 A Overall REVIEW_PASSED / Lifecycle ACTIVE 保持，R2 通过仅覆盖其候选，新操作单仍未通过、AC-10 不满足。B-main / N-3 已签，运行未放行；本轮所有资源消费0。AC-14/15/18 与 AC-16 板端 NOT_RUN、无 UNITY_NA / DONE；LIB 三文件、N-3 十一码、本人服务启停与 Air Unity 分工、旧债/负结果/UNKNOWN/停止偏差和独立原账均保持。全局实质 blocks/releases 仍为 ACQ R2-1 已配对，不新增 block/release；SLOT、环境、操作单与现场门独立有效。

### 2. 转交实现的 O-1…O-6（下一候选输入，非 finding）

来源唯一为同名复核「R3@K1K2K3K4 派发」§2；本表转交观察及修订方向，不代复核分级。用户答复落实后实现逐项给新候选落点/证据；下一次 R3 依真实 diff 与增量规则重新核，不能把本次观察当已核通过、冻结集或 finding 闭合。

| 观察 | 下一候选输入 / 原落点 |
|---|---|
| O-1 | 操作单 §1.0 不能用 `grep -v '^docs/'` 放过操作单本身。按 CHANGE:4 落实，通过候选到固定发布引用的 PLAY_GOVERNING 差异须为空（集合只引用 workflow §4.4，含本项具名操作单）；证明新操作单不能搭旧 PASS 放行。 |
| O-2 | 操作单 §0.5 的主连接/复用口径与 mini 证据 §2.3 的直接 `Popen ssh` 冲突。按 CHANGE:3 统一准备/收据/Play 三单元的命令、失败计数及禁止自动新认证的行为，不能只改叙述而保留另开连接的脚本。 |
| O-3 | 操作单 §14 单元提前 STOP 与 §13 S-REBUILD 剧本级继续须逐字区分：仅已签 A5 非主臂帧/发布段限制允许下一既定剧本；主臂失败/原因未明仍停全部，不重跑本次、不启用新单元作重试。 |
| O-4 | 操作单抬头明确全部命令块在 bash 中执行，覆盖 §3.5 的 `$PATHS` 分词及附录 B 进程替换；不让 Air 缺省 zsh 隐式决定行为。 |
| O-5 | 操作单 §4 启动块的 `cd` 失败须直接停止，不能在后续独立语句继续启动；逐字命令和 STOP 路由一致。 |
| O-6 | mini 证据 §7 改为 N-1 全套“累计2/3、本轮未跑”；余1不是本次派发测试许可，不重置或挪用。 |

C3 证据 §3 PR-8…14 与上述观察重合处合并处理，不另造用户题；门循环、准备脚本失败路径、`Assets/_Recovery` 实际存在性判据、目标 Python 依赖未知等未决关注仍随候选携带。语法检查不等于 Air/板运行验证。

### 3. 六道最终用户题（原 request_id；供 supervisor 直接转呈）

本节收敛「mini操作单待裁定答复与 CHANGE 申请」§2–3、C3 证据 §3–4 与「Mac mini四题答复落实」§4 的既有申请；**同一题沿用原 ID，不增造题或重签完整信封**。下列 A/B/C 是供用户选择的文本，全部未答、未生效；发生会话逐字入账后 Acceptance 才追加合同落实。CHANGE:1 原泛化条件条现收敛为已触发的 IR-M1 具体申请，其他未来变化仍逐案提交，不包含 blanket 授权。六题均为 COORD-015 §5.2 不可代拍的合同/资源或本人事实事项，本轮不向用户提问、不代写原话账本。

#### CHANGE:1 — IR-M1 显式旗标代码路线还是其他路径

request_id: `P1-ENG-LOOP-002:B-main:CHANGE:1`

**原题与来源**：mini 证据 §8 IR-M1 问“缺省 `llama_server_command` 与唯一既有显式栈原读数不同，改代码回停点，还是保持代码首启核验？”；同提案 CHANGE:1 / AC-7 修订2申请已把推荐收敛为十项完整闭集。

**转呈题目：是否选择修改 llama 分支，逐字固定以下十项资源旗标，并在新候选经核对/独立复核后才进入已签 B-main？**

- **A（推荐）：选择代码路线**，固定 `--parallel 1 --ctx-size 2048 --n-gpu-layers 99 --fit off --no-warmup --no-webui --no-cache-prompt --cache-ram 0 --cache-reuse 0 --offline`，原模型/mmproj/host/port保留，prompt/schema/decode、三文件身份与 local-hf 不变；由 Acceptance 冻结 AC-7 修订申请，实现同步代码/测试、回同停点。
- B：保持当前代码并暂停服务推进；本人另给目标条件原读数或明确提出另一栈/合同变更，Acceptance 核清后再裁。原“保持缺省、先加载试未知”备选已被 IR-M1 拒绝，本题 B 不授权该动作或豁免 engineering §9。

**推荐理由/只能用户定**：旧唯一环境读数只覆盖该显式配置，不能用首次 GGUF 加载探未知；上下文、并行、层数与缓存是执行栈条件，不能从用户保持三文件推定已同意改变，接受角色不能替用户选目标栈或改资源边界。

**B-main 影响**：A 改执行条件及 AC-7，须新代码候选；不增加板启动/GGUF≤2、推理≤335、HTTP≤200、SSH≤3或任何其他已签上限，不消除环境/来源/SLOT门。B 保留签发上限、运行继续停。两者均不授 mini 板操作或新测试额度；N-1 全套仍2/3，后续验证先核机器/原信封适用性（原机器 Air），不从 B-main 借测试资源。

#### CHANGE:2 — 非推理 HTTP 逐次共账及 ≤200

request_id: `P1-ENG-LOOP-002:B-main:CHANGE:2`

**原题与来源**：mini §8 IR-M2 申请把 POST 与 GET/result 轮询合并为一次推理、豁免轮询计入非推理；IR-M7 申请就绪等待值/按成功 listening 时间估算健康次数。提案 CHANGE:2 已合并两项，拒绝默示豁免与自动冻结20s。

**转呈题目：是否保留非推理 HTTP 总上限200，把每次 result/status/health（含 loopback 和失败）共账，并在下一请求前预算不足即 S-ENVELOPE？**

- **A（推荐）：保留≤200逐次共账**。下一代码/操作单候选覆盖健康成功与失败终点、两服务批次累计账及收尾预留，在下一 HTTP 前守预算；不用成功 listening 时间除0.25作唯一来源。不给20s新阈值，原就绪超时只是现行等待上限，预算可更早停止；冻结文本须消除 IR-M7 占位并写清健康/result/status分配与失败处置。
- B：要求轮询单列/豁免或调整总限；先由实现提交 result 闭集、独立硬上限、失败计账、两次健康/status/收尾最坏分配及具体代码方案，再由用户另签完整变化维度。选择 B 仅要求准备有界申请，当前不生效、不授权无界类别或增额。

**推荐理由/只能用户定**：GET/result不执行模型，原签没有逐字轮询豁免；把它并入推理改变用户签发含义，健康轮询本身也可能耗尽200。资源类别/上限由用户决定，supervisor与Acceptance均不能代改。

**B-main 影响**：A 保持总200；335是实际推理尝试上限（失败/超时/内置尝试共账，同次 wrapper POST/chat 不重复算），不保证余额能全用完。Air↔language_serve 每行含异常/不完整的实际体字节仍计≤60,000,000B，loopback不重复算Air传输；B 未另签前仍按保守200口径、运行停。两项均不新增启动/重测，首次主臂失败停全部仍有效；计量代码改动亦须新稳定候选与相称验证。

#### CHANGE:3 — SSH ≤3 认证主连接，禁止自动第四连接

request_id: `P1-ENG-LOOP-002:B-main:CHANGE:3`

**原题与来源**：mini §8 IR-M3 申请每单元一条 ControlMaster、内复用通道不另计；IR-M8分配准备/收据/Play用途，提案 CHANGE:3 与 C3 PR-10 / R3 O-2 已指出口径及命令不一致。

**转呈题目：是否明确原≤3次为最多3条认证主连接（准备、收据、Play各1），单元内仅复用列齐的有限通道，禁止套接字失效自动再认证？**

- **A（推荐）：采用有界主连接口径**。操作单须列齐静态读/部署/前台服务/释放/日志收尾的有限通道和次数，并统一准备发起块；尝试含失败实计，每条尝试前至全部通道及主连接关闭后≤3,600s、累计≤10,800s。连接失败不重试；socket缺失/失效即停，不自动回退新认证，不开第四连接；不写SSH配置、无后台推理服务。
- B：不采纳主连接解释，继续保守按每个实际新认证连接/失败尝试计次；由实现另给总≤3且无隐式新连接的可执行单连接方案。若做不到，暂停并另提具体口径/额度申请，当前不自动增加次数。

**推荐理由/只能用户定**：原签准备/收据/Play各1，未明示多通道免费，当前两份命令冲突；只有额度签发者可明确资源计数单位，不能据`-o`不改配置推定授权。

**B-main 影响**：A只明确单位，不扩大用途/次数/墙钟；部署1+日志≤2、传输≤20,000,000B/≤3批、驻留和结束前停服务等原限全保持。任何实际另建连接扣原账，不能续用mini已耗尽或Air已作废旧补核余额。B可行方案核清前SSH仍不可执行。

#### CHANGE:4 — 严格发布引用 / 执行检出双来源

request_id: `P1-ENG-LOOP-002:B-main:CHANGE:4`

**原题与来源**：mini §8 IR-M4 问“通过候选自身不可能含后来签它的review，如何同时读通过指针、HEAD等值、全树干净并记采集日志？”；提案 CHANGE:4 / AC-10 修订1解释申请、C3 PR-8 与 R3 O-1 是同一题。

**转呈题目：是否采用固定已推送发布引用读取有效复核/授权，实际执行树检出最新有效通过候选且全树干净的双来源解释？**

- **A（推荐）：采用严格双来源**。发布引用在操作开始时运行时解析并固定，核祖先关系、最新有效通过行与后续门；通过候选到该引用仅允许规则许可的非PLAY_GOVERNING文档差异，含操作单的PLAY_GOVERNING差异必须为空，不能过滤全部docs。操作员所用操作单必须与该通过候选对应。执行树detach通过候选、实际HEAD等值/整树dirty=false；先采实际HEAD/status原流，在独立文档检出登记Unity日志并推送，回执行检出重核同值/干净后采集；收据/报告/会话仍绑定实际候选。
- B：暂不采纳、暂停执行；要求另一满足现行HEAD等值/全树干净的完整方案再裁。任意HEAD或dirty豁免不在本申请内，若本人希望改变须另提实质AC-6修订，当前不生效。

**推荐理由/只能用户定**：解决review自引用同时堵住新操作单借旧PASS；这是现行发布/执行放行前提的合同解释选择，不能由角色在命令中悄悄放宽或由supervisor代选。不是公开发布授权。

**B-main 影响**：A不改AC-6绑定字段、不增加执行资源、仍需操作单新候选通过；B保持已签上限及当前停止。两项都不许可未复核版本采集，也不把计划HEAD替代实际原流。

#### SLOT:FACT:1 — 同板资源 / 18081、18082 窗口互斥

request_id: `P1-ENG-LOOP-002:SLOT:FACT:1`

**原题与来源**：「Mac mini补核核清」§3要求本人确认46273归属与共享槽互斥；「Mac mini四题答复落实」§1已消费tailscaled归属，剩余仅服务窗口互斥。**不重问46273归属或清理。**

**转呈题目：能否确认本项准备、收据、Play窗口与其他JET/LOOP任务在同一Jetson的资源及18081/18082上互斥？**

- **A（推荐）：本人明确确认上述窗口互斥**，说明可用窗口/需先结束的其他任务；执行前仍核当前端口/残留，没有准备/服务重叠。
- B：现在不能确认，继续停在服务前；待本人完成协调后再确认，不让角色推断未来窗口或清进程。

**推荐理由/只能用户定**：端口空闲只是一时快照，tailscaled归属排除不代表未来无并行任务；本人掌握其他任务排期，supervisor不能代答FACT或替用户承诺互斥。

**B-main 影响**：A只补事实前提，不扩大SSH/服务/Play上限，不替代环境/候选/现场门；B保留签名但服务与下游可执行值0。无sudo、未知进程清理、46273连接或额外诊断许可。

#### B-main:FACT:2 — Air 上 C2 来源链原件如何对齐（角色不复制）

request_id: `P1-ENG-LOOP-002:B-main:FACT:2`

**原题与来源**：「Mac mini四题答复落实」§3步骤2/§4要求本人在Air对齐候选与来源，原件缺失即停；mini §1.2 F-11/附录A指出Air缺被忽略的C2来源原件。先前SUB:1只把补核换到mini，未把Air运行迁走，也未授mini→Air复制；本题是该既有事项的方法选择，非重问换机。

**转呈题目：新候选通过后，Air 所需 C2 来源链原件由本人从mini对齐，还是提供Air已有的完整原件位置，或暂缓？角色不执行复制。**

- **A（推荐）：本人在新候选通过后从mini对齐必要来源原件到Air**，保持原始字节及相对引用关系，提供来源/完整性记录；不搬模型或库，不重跑JET诊断、不把诊断升级为本项证据。角色仅核用户提供的来源及原读数。
- B：本人指出Air已存的完整原件位置与可核来源/完整性记录，接受核清后复用；不能仅给摘要、口头“已齐”或让角色从文件名猜身份。
- C：暂缓对齐，保持Air来源门停止。

**必要原件边界**：mini证据附录A所读C2诊断 `state.json`、`budget.jsonl`、`checkpoint.json`，由 `state.board.step` 运行时定位的板步 `receipt.json`，以及引用的原始server/worker/monitor流（mini §1.3 E）；另须对应的已版本化 `stageb-transfer.json` 与 `stageb-build-rerun.json`。路径/板批次/sha由这些来源解析，不手抄派生标识、不只拿三个模型文件代替来源链。实际最小文件清单/字节在本人操作前据新操作单核清，不把整个outputs树或模型复制当必需。

**推荐理由/只能用户定**：Air是既定会话/Unity主机、mini现有原件已支持有限补核；对齐原件保持既有执行分工，只有本人可确认Air事实并完成此跨机操作。既有资源信封不含角色复制mini→Air或任意跨机传输，supervisor不能代作FACT选择/新类别授权。

**B-main 影响**：A/B只补来源，原Jetson文件传输≤20MB/≤3批仍仅部署及日志，不能扣该额度替角色复制mini→Air；不借作废Air补核或耗尽mini预算，不迁Unity、不加SSH/模型加载。本人对齐完成、原件核清也不自动开准备SSH；只在新操作单通过、CHANGE:3与准备门落实后，按已签原准备1次取必要静态目标事实并回接受核清。若需动态import/无模型探测等原用途外动作，先形成既有ENV:2最小子合同另签，当前0；本题不预签ENV:2。C保留B-main上限和未闭门。

### 4. 用户答复后的最短接力与收工边界

**Acceptance落实 → Implementation新稳定候选 → 同停点下一实际C轮 → Review R3@K1K2K3K4。**

1. supervisor只转呈上节六题；答复发生会话逐字入账/提供事实，Acceptance核原签、选择效力与机器/验证范围，追加具名合同落实；未答/需进一步规格的变化继续停，不把推荐当答复。FACT:2本人动作可在候选通过后完成，不把它伪称当前已齐。
2. 实现依据落实后的文本返工操作单与O-1…6/C3关注；若选CHANGE:1代码路线，同步具名代码及AC-7测试，CHANGE:2计量方案需要的代码亦入同一候选。相称测试先核原N-1适用机器/剩余额度，窄修替代需满足engineering§6；触及真实模型加载器等不得自动借R2替代充分结论。本派发不执行测试、不授运行范围。
3. 实现四条件逐条自证、完整diff/AC指针/未核风险齐备后提交推送并停在K1K2K3K4，Acceptance做下一实际C轮（现记录C1…C3，接续C4；同停点C首退额度已用，不重置）。未开R3，故此次必须经C，不能按REWORK_REQUIRED直回复核。
4. Review先独立核四条件，再按PLAY_GOVERNING diff资格开R3；修复触及行基线由R2 `round_candidate`、全量基线由最新有效`passed_candidate`运行时解析，不把本次未开轮观察另立基线。返工仍1/2，后续依实际结论计数，不预签通过。

候选通过后才按「Mac mini四题答复落实」§3继续本人Air原件/现场事实 → Acceptance核清准备与逐维度放行 → 本人前台服务/收据/Unity → 正式工件另经C/AC-18证据核实。六题答复不是立即SSH/加载/Play放行；旧预算、债、暂停、现场HEAD/status/Unity日志及人眼条件全保留。

本轮只写本提案新节、implementation-status同名指针节、current-status本项交接/Log；consumed=none，零SSH/复制/模型/功能测试/评分/Jetson/Unity/runtime。收工运行角色写入及文档自检，结果见提交尾注与接力报告；不写用户原话账本。

open_items: IR-M1,IR-M2,IR-M3,IR-M4,IR-M7

## R3六题答复落实（2026-10-07，Acceptance）

**结论：六题均已有效答复；CHANGE:1–4 的 A 选择按下文冻结，SLOT 窗口互斥确认成立，FACT:2 为候选通过后的本人操作承诺，Air 原件当前仍未核齐。交 Implementation 形成新稳定候选，先 C4@K1K2K3K4，再由独立 Review 核稳定门及 R3 资格。** 本轮为合同答复落实，不是 D/C/R，不改最新 C3 核对表、不签候选通过或运行放行。D4 engineering-v1、Overall REVIEW_PASSED / Lifecycle ACTIVE 保持；R3 REVIEW_BLOCKED 未开轮、不计次，C首退1/1已用、复核返工1/2、无冻结集。AC-14/15/18与AC-16板端NOT_RUN，无UNITY_NA/DONE。

### 1. 原签、六题选择效力与不变上限

唯一答复来源：`docs/authorizations.md` 2026-10-07「用户答 R3 阻断消费六题：CHANGE:1–4 均选 A（推荐）、SLOT:FACT:1 确认窗口互斥、B-main:FACT:2 选 A 本人从 mini 对齐」条目。完整读用户原话、题面及补问，逐题对照上节§3 A文本；不是从 supervisor 读法推定选择。本条读法与原签相符，无需更正账本，本会话不代写用户原话。

| 原 request_id 尾码 | 原话/选择的效力 | 保留边界 |
|---|---|---|
| B-main:CHANGE:1 | A代码路线；十项资源旗标成为既定执行条件，冻结AC-7修订2(a)。 | 不允许保留缺省首加载试未知；prompt/schema/decode/三文件/local-hf不变。 |
| B-main:CHANGE:2 | A≤200逐次共账；冻结AC-7修订2(b)，非推理类别不豁免/result。 | 不增200，不保证335推理余额可全部使用，不冻结20s。 |
| B-main:CHANGE:3 | A有界主连接口径；明确原SSH单位并落实AC-10修订1(a)。 | 准备/收据/Play各1、失败计次、有限通道、墙钟及用途不扩。 |
| B-main:CHANGE:4 | A严格双来源；冻结AC-10修订1(b)。 | AC-6绑定字段与整树干净要求不变，不是公开发布授权。 |
| SLOT:FACT:1 | 初次“只是tailscale…”仅回应归属；**后续明确选择A确认互斥**才补齐未来窗口事实前提。 | 本项窗口同板无其他JET/LOOP任务占用18081/18082或GPU/内存；执行前仍核端口/残留，不授清进程等动作。 |
| B-main:FACT:2 | A本人从mini对齐，发生在新候选通过后；方法已定，实际操作/完整性核清未完成。 | 角色不复制、不搬模型/库、不重跑诊断，详情见§3。 |

原签取账本同日「用户答 Mac mini 补核核清四题」与其题面完整表（本提案「Mac mini补核核清」§3(i)），逐维度效力仍见「Mac mini四题答复落实」§2：SSH≤3/单次≤3,600s/累计≤10,800s，板服务及GGUF≤2、故障重启0，推理≤335、非推理HTTP≤200，SSH文件≤20,000,000B/≤3批，HTTP体≤60,000,000B，Play≤5/每次≤420s、session≤5；磁盘、归档、回放、version、runtime和所有零维度仍按该完整表。六题不重签/增额、不启用SUB或决策信封。用户开场“开始做测试准备”与具体六题共同只支持本节接力，不构成SSH/加载/Play或新测试类别许可；engineering§9未核事实规则未豁免。

### 2. 冻结AC修订（追加生效，原条及旧申请不覆盖）

以下源于已提出的IR-M1/M2/M3/M4/M7与用户明确选择，按engineering§2在本合同裁定节追加；不是C轮增改义务。旧「全部未生效」仅保留为申请时快照，本节是现行修订唯一文本。新AC为0；既有解释修订3加本节2项为累计5，不增finding/归因计数。

#### AC-7 修订 2（CHANGE:1/2；解释A2(a)、AC-7与§5.2计量）

(a) llama分支的`llama_server_command`逐字固定完整十项：`--parallel 1 --ctx-size 2048 --n-gpu-layers 99 --fit off --no-warmup --no-webui --no-cache-prompt --cache-ram 0 --cache-reuse 0 --offline`；原`-m`/`--mmproj`/`--host 127.0.0.1`/`--port`保留。不删成子集，不改变prompt/schema/decode、资产三键或local-hf路径。实现限§4.1具名文件，同步`tools/language_serve.py`及AC-7测试，回既有K1K2K3K4。原环境读数只覆盖选定配置，不证明新代码/板端已可运行；缺依赖/退出/就绪失败/超时、身份拒启、前台退出释放与原响应失败映射义务照旧。

(b) 非推理HTTP包括每次result/status/health（含loopback与失败），**两服务批次使用同一≤200累计账**，从首次健康尝试起记录真实请求尝试，成功和失败均有终点/结果，不以成功listening时间÷0.25推定实耗。下一请求前核累计已用+本次1+当前阶段尚必需的status/收尾预留≤200；不足即S-ENVELOPE、停止新增业务动作，仅原签安全收尾，不发送预算外请求。新候选须把健康/result/status/收尾路径的有限次数、预留来源与两批累计/交接方式列齐到操作单，并以代码计量覆盖实际路径；这是在总200内的调度实现，不另给类别、次数或超时。原就绪缺省等待上限300s及轮询间隔0.25s保留（只读来源：`tools/language_serve.py::DEFAULT_LLAMA_READY_TIMEOUT_S`/`_wait_llama_ready`）；操作单删除`<IR-M7 裁定值>`，使用现行300s而非20s，就绪等待可因预算更早停止，不能把300s等同可发1201次请求。需要改该上限/间隔或计数类别时先另提具体变化裁定，不借本条自行改阈值。

335仍为实际模型推理尝试上限，失败/超时/内置尝试共账；wrapper POST与其实际chat关联为同一尝试，不重复算两次推理。Air↔language_serve每行实际请求体/响应体（含result/status/异常/不完整）计≤60,000,000B，loopback不重复当Air传输。现行首次主臂/服务/HTTP失败停全部、重启0和N-3十一码保持，不用200余量续行失败批次。

**证明方式与范围**：`test:tests/test_llama_server_adapter.py` 的命令逐字闭集、临时子进程/假服务启动与原拒启映射，及健康成功/失败/超时、下一请求前不足即停、两批累计与预留的具名用例；涉及客户端计量则在§4.1对应测试文件同步覆盖result/status/实际推理关联。`artifact:docs/evidence/P1-ENG-LOOP-002-play-ops.md` 的分配/账模板与新停点证据逐条映射。本节不预写不存在的测试名、不称已通过，真实板端仍留后续授权核验。

#### AC-10 修订 1（CHANGE:3/4；解释§3.6操作单、§5.2与AC-6现场绑定）

(a) **授权边界修订3（SSH单位）**：原≤3次明确为最多3条认证主连接，准备、收据、Play各1；单元内仅复用操作单列齐的静态读/部署/前台服务/释放/日志收尾有限通道及次数。准备发起块与操作单必须一致，不能一边建主连接一边直接另开ssh；socket缺失/失效即停，禁止自动回退新认证，连接失败不重试，不开第四连接。实际另建认证连接/失败尝试仍实扣原账，不因标“复用”免计。从主连接尝试前至全部通道及主连接关闭后计每单元≤3,600s、累计≤10,800s；服务驻留被完整覆盖，部署1/日志≤2批、20MB等原限不变。不改SSH配置、不后台推理，不续用耗尽mini或作废Air补核余额。

(b) 操作开始时运行时解析并固定已推送发布引用，从该引用读取复核/授权，核候选祖先关系、最新有效通过机读行与其后门状态；**通过候选至该引用只允许规则许可的非PLAY_GOVERNING文档差异**。PLAY_GOVERNING唯一集合引用workflow§4.4，含本项`docs/evidence/P1-ENG-LOOP-002-play-ops.md`，该集合diff须为空；禁止过滤全部docs、新操作单借旧PASS。实际操作单须与该通过候选对应。

执行树detach到最新有效通过候选，实际HEAD等值、整树dirty=false（IR-17完整status含未跟踪、无路径过滤）；报告/收据/会话仍绑定该实际候选和原AC-6字段。采集前先取执行检出的实际HEAD/status原流，在独立文档检出登记Unity日志并推送，再回执行检出重核同值/整树干净后采集；不以计划HEAD替代原流、不豁免文档脏树。现场日志提交仅可增添规则许可文档，任何影响有效通过行/后续门或PLAY_GOVERNING的变化均须重新核门，不在既定发布证据上默示放行。

**证明方式与范围**：`artifact:docs/evidence/P1-ENG-LOOP-002-play-ops.md` 与准备证据中的统一命令/有限通道表/失败及收尾账；新停点证据用零板静态核对或相称本地夹具给出旧PASS+新操作单拒绝、无socket停止而非新认证、整树dirty拒绝及真实HEAD原流的证据指针。不得拿bash语法通过替代Air/板实际验证，不得为本条证明连接真实SSH、启动板服务或运行Unity；相称本地替身验证仍须遵§3机器/额度边界。AC-6程序绑定接口不变，正式现场记录与板运行仍后置。

### 3. SLOT与FACT:2事实效力及机器/验证边界

SLOT合取前提的46273归属与未来窗口互斥现均有用户声明；本轮不再把互斥列待答，不声称重新测得进程/端口或具名实际时间窗。服务前仍按新操作单核当前残留/18081/18082与资源互斥，不能从一次确认推断现场已满足。不sudo、不清未知进程、不改设置、不连接46273；原非特权UNKNOWN及停止顺序偏差保留。

FACT:2由用户在**新候选通过后**按上节§3必要原件闭集从mini对齐到Air：C2 `state.json`/`budget.jsonl`/`checkpoint.json`、由`state.board.step`解析的板步`receipt.json`及所引原始server/worker/monitor流、对应版本化`stageb-transfer.json`/`stageb-build-rerun.json`。操作前依新操作单核最小文件/字节，保持原字节与相对引用、提供来源/完整性记录；路径/身份由原件解析，不能只拿摘要或三个模型文件替代。角色只核本人提供的来源和原读数，不执行跨机复制；不搬模型/库、不转诊断为验收证据。该本人操作不扣B-main Jetson部署/日志传输额度，不移用旧余额、不迁Unity、不自动开准备SSH；来源核清后仍依准备门取目标事实、回接受明确放行。ENV:2保持条件性未签0，动态import/无模型探测须最小子合同另签。

**实现与验证机器裁定**：新候选允许在mini按§4.1做代码/测试文本和操作单修改、只读已有来源准备；这次选择不授mini运行模型、功能测试/回放、板操作或部署。N-1唯一首签仍是账本10-06「用户首签N-1阶段A停点全套额度」的**MacBook Air / 现有.venv-yoloe**；全套累计2/3、余1不是本轮接受派发的测试许可，也不等于已用尽。实现运行验证前逐项核原N-1机器/解释器、模型加载、每候选次数/墙钟/证据磁盘与剩余账，符合原签才可使用，不另由本角色增额；需要mini跑功能测试、换解释器或其他越界先停报用户，不能拿B-main代测试信封。跟踪focused/复核仍遵全局数据根只读环境约定，不安装。

AC-7相称验证是稳定条件②，不能仍沿纯操作单“代码零diff/无适用focused”声明。窄修替代全套仅在engineering§6全部前提成立时使用：列明改动文件、覆盖它们的focused及所修问题的红绿证据，明确未跑全套；触及真实模型加载器、数据划分或对外指标路径不适用。旗标/健康启动路径不能直接沿用R2窄修替代充分结论，须按新diff另判；若相称验证所需机器/额度不可用则保持候选未就绪并列具体缺口，不以待后补测试自证稳定。所有真实模型/板运行、复制、Unity及runtime操作本轮均0。

### 4. 实现交接、未闭项与下一停点

Implementation按§2冻结文本同步具名代码/AC-7测试、操作单和准备命令；**O-1…O-6及C3 PR-8…14全部随带**，唯一原详表为上节§2、`docs/reviews/P1-ENG-LOOP-002.md`「R3@K1K2K3K4 派发」§2和`docs/evidence/P1-ENG-LOOP-002-C3-K1K2K3K4.md`§3。重合项合并，不把观察当finding/冻结集/已闭证据：堵新操作单借旧PASS、统一主连接、区分单元STOP与已签A5非主臂S-REBUILD的剧本继续、抬头全部命令用bash、cd失败即停、全套账纠正累计2/3本轮未跑；同时保留准备门循环/来源先齐、readelf/ldd/pgrep失败路径、`Assets/_Recovery`真实存在性、目标Python动态闭包未知及现场版本关注。不靠签六题把这些实现偏差自动判满足。

证据中按AC-7修订2(a)/(b)、AC-10修订1(a)/(b)及O/PR逐条给落点/证据、完整候选diff解析式、四条件自证、验证适用性/实际原账与未核风险；提交推送后停在K1K2K3K4。接续实际C4（首退额度不重置）；Review先核四条件，再依PLAY_GOVERNING非空资格决定开R3，基线从同名复核R2 `round_candidate`与最新有效`passed_candidate`运行时解析。本轮未开新C/R，不适用REWORK_REQUIRED修复直回复核。

六题选择层的IR-M1/M2/M3/M4/M7已落实，无待用户重复选择；**实现/验证、Air原件与目标环境核清、新候选C/独立复核、现场HEAD/status/Unity日志/人眼条件及AC-18证据停点仍未闭**。后续顺序保持：新候选通过→本人Air原件/准备事实→接受逐维度明确放行→本人前台服务/收据/Unity→正式工件自证/下一实际C/AC-18独立证据核实。USER:1/2为已授权但后置的本人动作，ENV:2只有发生原用途外必需探测才另提具体申请；本轮needs_user无新增待答题，不把未来本人动作冒称已完成。

旧预算原账、Air余额作废/miniSSH1/1结束、LIB三文件及20库披露限制、N-3十一码、旧债/负结果/UNKNOWN/停止偏差、ACQ暂停/非verdict/清理与不转用约束保持。全局实质ACQ R2-1 blocks/releases已顺序配对，无新增block/release；本轮0消耗性+2零消耗，Gate-echo保持。本批只写提案、正式设计对应指针、implementation-status指针与current-status本项；consumed=none，未运行功能测试/模型/评分/SSH/复制/板/Unity/runtime，不写账本或复核文件。

open_items: none

## IR-N裁定（2026-10-07，Acceptance）

**结论：IR-N2按已签“收据重测0”直接裁定、冻结AC-15修订1；IR-N1的协议/节奏变化不能代选，收敛为CHANGE:5一道最终用户题，交用户、由supervisor转呈。** 来源为 `docs/evidence/P1-ENG-LOOP-002-r3answer-candidate.md` §3，中间提交由该文件的登记轮次、派发日志commits与git运行时解析；本轮核其直接关联代码，不做完整候选C核对、不签独立复核。Dispatch-Id `P1-ENG-LOOP-002-IR-N裁定-20261007T161427Z-5bac`，requested.round `IR-N裁定`。未答选项均无执行效力，CHANGE:1–4的已答选择不重问。

### 1. 原代码、原读数与投影核清

中间提交之后至开工版本的 `controller/language_selector.py`、`tools/language_serve.py`、`tools/language_latency.py` 无diff。以下是本轮只读核实与条件推算，替代实现证据/操作单中把投影称为必然结果的读法；不回写实现原报告。

| 对象 | 原代码/来源 | 本轮裁定的事实与上限 |
|---|---|---|
| `/result`节奏 | `HttpAdapter.__init__` / `predict_one`；`LanguageRequestHandler.do_GET` / `SingleFlightRuntime.result` | 缺省0.2s；POST受理后先立即GET，pending/busy后才sleep。服务端当前即时返回状态，不识别wait参数（把整个尾串当query_id）。POST计推理账，GET/result计非推理账，两者不能加在200这一分母中。 |
| 截止时间 | `HttpAdapter._call` / `predict_one`；`language_latency.main.common`；`language_loop.KReceipt.t_ret_s` | 单次I/O上限5s；测量CLI缺省T_ret=T_hard=60s。现行result请求只传remaining_hard，循环前检查T_ret，回包done没有再次检查软截止；因此实现所提“wait不超过两种剩余时间”尚未实现。Play的T_ret来自实际收据k_ret/hz，不是固定60s或4s，不得改其派生式。 |
| 两批账与预留 | `HttpBudgetLedger` / `HttpAdapter._budget_guard`；操作单§0.6 | 当前批次#2预留25、#3预留11为规划值，代码不因必需status已使用而递减reserve。#2的3次status：操作者curl、测量probe、首次factory.bind；#3的11次是curl1+至多5个session各2。收尾HTTP0。25中的未来health11没有已核最低/最坏次数依据，不能称保证下一批就绪；本轮不擅自减少预留或改健康节奏。 |
| 旧JET时延/就绪 | mini证据§1.2 F-6/F-8；JET提案「阶段BC2诊断核清」的原件入口 | 本机缺 `outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/` 的state/board receipt/server/worker原流，未复制或连板补取。**1.7–2.0s与2.48s本轮未独立核实**；版本化JET-vlm.json仍为S3 NOT_RUN，不能补充证明。旧609行诊断也不是本项schema/35行/HTTP wrapper的时延保证。后续本人原件对齐后核，不阻碍现在裁“原签不允许自动重测”。 |
| IR-N2 | `measure_host(max_rounds=2)` / `measure_round` / `main`jetson分支 / `jetson_adapter_factory` | jetson调用未覆盖缺省2；首轮INVALID会新建adapter、再bind/status，再3+32调用。**不是任一异常必定完成70个实际模型请求**：factory失败会break，fatal客户端后续调用可在本机拒绝；实际HTTP/模型尝试仍须逐行计。另有首轮捕获SelectorError后继续剩余样本的路径，须落实已签首次主臂/HTTP失败即停。 |

**重算而非照抄投影：** 假设首GET立即、I/O耗时忽略、完成时间恰为L，则旧路径轮询数为 `1 + ceil(L/0.2)`，不是只用L/0.2；若**假设**L为1.7–2.0s，得到10–11次，不是已核每请求9–10次。沿操作单规划H2=11与固定reserve25，#2可供result的额度 `200−25−3−11=161`，约可完成14–16个这样的请求；第几次具体STOP取决于每行耗时/失败/预算快照，不能冻结为16–17。35次各5个GET为175个非推理，POST35另记推理；“35×6=210超过非推理200”混账，应撤回该论据。即便如此，固定reserve25及已发生status/health仍可能提前阻断，故旧方案有实质预算风险。

若保留0.2s，成功请求可能只需一个GET；代码本身不能证明“收据绝无可能完成”或“等同暂停”。缺原件不以假定数字填空：**已证的是资源风险与原签的停止要求，不是本项实测不可执行结论**。健康300s/0.25s也只给时间边界，HTTP I/O/调度及200守账会截断；2.48/0.25不得充当实际11次账。

### 2. IR-N2直接裁定与冻结AC-15修订1（解释§3.2、AC-6/15及已签B-main/N-3）

关联原request_id建议 `P1-ENG-LOOP-002:B-main:CHANGE:6` **保留追溯、无需用户题**。依据账本10-07「用户答Mac mini补核核清四题」原签及本提案「Mac mini补核核清」§3(i)板推理/收据重测行、已签N-3处置：收据上限35、重测0、首次主臂失败停全部。这不是增加预算或新STOP阈值；不采人工在首轮后抢中断的B方案。

**AC-15修订1（追加生效；原AC-15不覆盖）：**

(a) `measure --host jetson` 的生产入口明确 `max_rounds=1`，正常轮仍为3预热+32计时；首轮INVALID/FAIL不得自动新建第二轮适配器、再bind/status或再推理。不能用335余额重开收据。`measure_host`的其他宿主默认两轮及旧两宿主收据路径保持原语义。

(b) jetson路径在首个测量失败（`SelectorError`或现行固定60s测量截止失败）后停止本轮剩余调用，保存已得原样本/失败原因、标非OK及不足样本；适配器/身份探针失败同样停止，不再发result/status/query来凑齐35。S_ENVELOPE保留预算原因并走已签S-ENVELOPE；其他首次主臂/HTTP失败走已签停止处置，不等待操作者或第二轮。正常返回的三态/parse_error仍按原classify记录，不把`none`或已记录解析状态自创成新性能STOP线。

(c) 操作单必须逐步检查退出码：measure非0（当前非OK为7）即停止，不无条件执行下一条k-receipt、不开Play；已有报告仍保留。measure为0才执行k-receipt，后者原0/6/8语义保持。不得把measure退出7写成k-receipt退出6；实际少于35的失败批如实记账，不填补/过滤失败行，不生成合格p95/收据。

**证明方式：** `test:tests/test_language_latency.py` 覆盖jetson生产CLI首轮失败无第二factory/status、预热及计时首失败后无余下请求、失败报告保留/不足32不合格、成功恰3+32、其他宿主仍可第二轮；`artifact:docs/evidence/P1-ENG-LOOP-002-play-ops.md` §5逐步非零即停及§0.6/#2分配；按AC-6/15列入新停点自证。这是对实现IR-N2及已签停止合同的直接答复，不是C轮新增义务；新AC0、解释修订累计6。本轮只冻结文本，未实现/运行测试/证明通过。

### 3. CHANGE:5最终用户题（供supervisor直接转呈；未答不生效）

request_id: `P1-ENG-LOOP-002:B-main:CHANGE:5`

**原题与来源：** `-r3answer-candidate.md` §3 IR-N1。CHANGE:2已选A确定/result逐次并入200，未签长轮询、1s节奏或新请求参数；本题不重问计账选择。上节纠正其投影，所有旧时延只作未核参考。

**转呈题目：保持非推理HTTP两批合计≤200、收据重测0及首次主臂失败即停，是否采用下述有界长轮询；或改为1s短轮询、保持0.2s、仅准备另一个有界额度申请？**

- **A（推荐）：有界长轮询代码路线。** 仅本项已绑定六键llama身份的客户端/服务路径使用 `GET /result/<query_id>?wait_s=<w>`，每次w=`min(4.0s,本次T_ret剩余,本次T_hard剩余)`，有限正数且不超过4s；服务正确分离query_id/参数，在同query_id完成/失败/stuck立即回复，仍pending只在本次w到期回复。客户端不额外sleep0.2s，下一请求前仍核200及预留；每query最多16次result尝试（失败也计），任何时间/次数/预算边界先到即停，禁止第17次或HTTP错误重试/回退短轮询。保持5s单次I/O上限，剩余截止不足时收缩I/O，**回包后重新核T_ret/T_hard，不接纳逾期done**；未支持参数的服务不默默回退。正常pending到期不是HTTP失败；真正失败仍按原映射与已签STOP。16是待用户确认的保守次数硬限，不能拿 `ceil(min(T_ret,T_hard)/4)` 当实际计量或无条件保证。健康300s/0.25s、推理335、200共账/字节/身份、K派生、LanguageWorker与旧非llama路径均保持；实现改具名代码/测试和操作单，回同停点。**这些规格全部待用户选择后接受冻结。**
- **B：1.0s短轮询代码路线。** 仅上述llama路径把pending后的间隔改为1s、首GET仍立即，仍守原截止/回包后期限和200预留，不改协议、不增200、不重测，其他路径0.2s保持。最多61次result尝试/query（含失败，实际先受原截止与200截断），截止余量不足不继续sleep/发请求；不放宽60s测量或收据派生T_ret。额外呈现等待最多一个轮询间隔只是忽略调度/I/O的算法界，不保证实测时延增加恰≤1s，K仍由新实际报告派生。代价是呈现粒度更粗，成功请求数仍不保证。
- **C：保持0.2s与即时GET协议。** 不修改该节奏，200与预留照守、首预算不足/失败照停，不用投影宣布自动暂停或修改Lifecycle。新候选仍须落实IR-N2及其他已冻结返工；用户接受可能在唯一收据批次内先遇S-ENVELOPE、随后停全部的风险。不是让旧未复核操作单立即开跑。
- **D：只要求准备有界新额度/类别申请。** 沿CHANGE:2 B路线先列result请求闭集、次数硬限、失败计账、两次健康/status/收尾最坏分配、具体代码与逐维度变化，再另题签发；本题D不提高200、不豁免轮询、不授新额度，准备/运行继续停。

**最坏分配与失败终点（随题转呈）：** 原规划status两批至多3+11、HTTP收尾0；实际health为H2/H3，均受健康等待及200守账截断，不能固定为11或保证剩余。A的潜在result需求上界为16×35=560（收据）、16×300=4800（Play），**远超总200，故A也不能保证35次收据或300次Play请求全可执行**；两批实际还须满足 `H2+H3+status+result+其他已发生非推理≤200`，每次请求前另守当时预留，先不足即S-ENVELOPE，重测/重启0，停全部仅安全收尾。B的独立次数硬限同样不能覆盖总200；C也如此。4s/1s/16/61均是待选执行边界，不是目标设备测得的性能通过线，不用于签新硬件性能主张。

**仅作条件算术：** 若A每推理一次GET即完成、H2=H3=11、status合计14，则收据非推理49；Play最多剩129个GET。若收据各两次GET，则收据84，Play最多94个GET。它们是按假设计算的总账空间上界，静态预留的实际阶段顺序可再压低空间；不是“Play90–125余额”或“能完成70–100推理”的实测承诺。不能按这些数字耗掉唯一加载来试探环境；原环境/来源门仍须先核。

**推荐理由：** A保留用户选定的逐次200总账、在正常结果4s内就绪时可用一个请求及时返回，减少轮询开销和固定sleep引入的呈现颗粒；这是代码机制的理由，不是旧JET时延证明本项一定可用。B改动较小但增加呈现粒度；C保留合同且成功概率未知；D仍需另签，当前没有具体预算变化可以生效。

**只能用户定的理由：** 本题A/B增加协议参数/等待常数/次数限并改变HTTP等待节奏与结果接纳时序，触及K1及既有IR-M7/AC-7修订2(b)的禁止自改阈值边界；C是在不可重测收据批次中接受该资源风险，D涉及资源类别/上限。不是D5全选项均不改合同的代选题，supervisor与Acceptance不得代选。不因“签、先推进”或CHANGE:2 A推定选择A。

**B-main影响：** A/B需新代码候选、相称验证与同停点C4/独立R3；C仍需修IR-N2/新操作单及停点，D待完整申请。四项当前都不增加SSH≤3、服务/GGUF≤2、335/200、60MB、Play≤5等任何原签维度，不转用旧余额、不授mini测试/板运行。原件缺失/动态闭包UNKNOWN、现场HEAD/status/Unity日志及AC-18门保持；运行未放行。

### 4. 接续、未闭项与本轮边界

交接Owner=用户，由supervisor只转呈§3这一题；CHANGE:6无需转呈或新账本签发。答复发生会话逐字入账，Acceptance核选择后追加冻结IR-N1具体文本，再交Implementation合并AC-15修订1及原O-1…6/PR-8…14，重算操作单§0.6有限路径/预留，纠正“必然不可完成”投影并逐步检查measure退出。若需旧JET数字，先核本人对齐的原件，缺件保持UNKNOWN，不能照抄实现投影或借首次服务试未知。

在IR-N1未定前不花N-1最后一次全套整理注定待改的候选；裁定后按原N-1机器/解释器/累计2/3、余1账核验证适用性，含真实模型加载器路径改动不得以窄修替代全套。Implementation四条件自证/完整候选diff/AC证据/风险齐备后提交推送→C4→Review先核稳定门及R3资格。中间实现的468 focused仅为其报告，本轮未复测、不据此签满足；未证明单轮/长轮询生产行为。

本轮不改变Overall REVIEW_PASSED/Lifecycle ACTIVE、R3未开轮/C首退1/1/复核返工1/2/无冻结集，最新C3表与旧REVIEW_BLOCKED保留；AC-14/15/18与AC-16板端NOT_RUN、无UNITY_NA/DONE。IR-N2合同已答、实现及证据仍未闭；IR-N1待用户。无新硬件/Unity/运行证据、债务release或消耗性门变化，全局唯一ACQ R2-1 block/release已顺序配对；本轮0消耗性+2零消耗，consumed=none，仅本机读文档/源码与文档/角色自检，不跑功能测试/SSH/复制/模型/板/Unity/runtime，不写账本或复核文件。

open_items: IR-N1

## CHANGE5答复落实（2026-10-07，Acceptance）

**结论：用户明确选A，IR-N1选择有效；追加冻结AC-7修订3的有界长轮询文本，交Implementation合并已有修订形成稳定候选。** 本轮为合同答复落实，不是D/C/R；不改最新核对表、不签独立复核或运行放行。Dispatch-Id `P1-ENG-LOOP-002-CHANGE5答复落实-20261007T163814Z-ccdc`，requested.round `CHANGE5答复落实`。旧「IR-N裁定」§3–4的未答/待转呈是当轮快照，本节替代其当前选择与交接，原文不覆盖。

### 1. 原签与选择效力核对

唯一选择来源为 `docs/authorizations.md` 2026-10-07「用户答 CHANGE:5：选 A 有界长轮询（推荐）」条目；已完整核用户原话、展示说明、上文语境及「IR-N裁定」§3 A文本。用户选「A 有界长轮询 (Recommended)」，题面明确200共账、收据重测0、首次主臂失败即停以及不能保证请求全做完；展示说明明确4s、16次、回包重核截止、不重试不回退。与原题A一致，授权长轮询代码路线及本节规格冻结，不是supervisor/Acceptance代选；B/C/D未选，无执行效力，不需更正或代写账本。

原签仍取账本10-07「用户答 Mac mini 补核核清四题」及本提案「Mac mini补核核清」§3(i)/N-3完整表；CHANGE:1–4与SLOT/FACT:2效力仍取账本同日六题条目及「R3六题答复落实」§1–4。CHANGE:5不增加SSH≤3、服务/GGUF≤2、故障重启0、推理≤335、非推理HTTP两批≤200、HTTP体≤60,000,000B、Play≤5等任何原签维度，不签新测试额度、mini测试、板/模型执行、SUB或决策信封。N-1仍按10-06首签及累计2/3账，余1的适用性在验证前核，不把本轮选择当测试许可。

### 2. AC-7 修订 3（IR-N1 / CHANGE:5；解释AC-7修订2(b)、A2、§3.2与AC-6/15）

以下**追加生效**，原AC及AC-7修订2不删改；仅对/result协议、节奏及回包期限作已获用户选择的具名修订，健康等待和其他资源限仍取原文。新AC0、解释修订累计7；不是核对轮新增义务。

(a) **路径及等待协议。** 仅本项已绑定A2(d)六键llama身份的客户端/服务路径使用 `GET /result/<query_id>?wait_s=<w>`。每次 `w = min(4.0s, 本次T_ret剩余, 本次T_hard剩余)`，须为有限正数且≤4s；没有正剩余即停止，不发请求。服务正确分离query_id与参数，在同query_id完成/失败/stuck时立即回复；仍pending则在本次w到期回复。未支持参数的服务不默默回退。保持既有身份/结果/失败映射，不改prompt/schema/decode、LanguageWorker或旧非llama路径。

(b) **客户端有限次数与守账。** 客户端不额外sleep0.2s，每query最多16次result尝试，失败也计；任何时间、次数、预算边界先到即停，禁止第17次、HTTP错误重试或回退短轮询。下一请求前仍按AC-7修订2(b)核200累计账及当时必需status/收尾预留；每次result/status/health（含loopback与失败）两服务批次逐次共账。正常pending到期不是HTTP失败；真正失败按原映射与已签N-3 STOP，预算不足即S-ENVELOPE停止全部新增业务动作，仅原签安全收尾，不用剩余推理额度重测/重启。

(c) **截止与结果接纳。** 保持5s单次I/O上限，剩余截止不足时收缩I/O；回包后重新核T_ret/T_hard，不接纳逾期done。测量沿现行60s截止；Play的T_ret仍来自实际收据k_ret/hz，K派生式与原检查点/起点不改，不固定成4s或60s。健康300s/0.25s不改。4s及16次是已选执行边界，非目标设备性能通过线；`ceil(min(T_ret,T_hard)/4)`不是实际计量或完成保证。

(d) **分配与失败终点。** 操作单§0.6列齐两批有限路径、预留来源与实际累计/交接；health为实际H2/H3，不把旧11次规划当最低或最坏事实，status规划至多3+11、HTTP收尾0仍须按具体路径核。A潜在result上界为16×35=560（收据）、16×300=4800（Play），均不能由200覆盖；实际守 `H2+H3+status+result+其他已发生非推理≤200`，并在每次请求前另守预留。**A不能保证35次收据或300次Play请求全部做完**，预算不足仍停全部。不得照抄「收据必然不可完成」「16–17次必STOP」或Play余额投影作实测/保证；旧JET时延/就绪原件未齐时保持UNKNOWN，原条件算术只按「IR-N裁定」§1/§3解读，不能借首次加载试未知。

**证明方式与具名范围：** `test:tests/test_llama_server_adapter.py` 覆盖真实服务/result与HttpAdapter路径的query_id/参数分离、w有限正值及4s上界、完成/失败/stuck即时回复、pending到期、16次硬限/无第17次、失败不重试不回退、200请求前守账、I/O随两种剩余收缩、回包后软/硬截止拒绝逾期done及旧非llama行为；`test:tests/test_language_latency.py` 与既有AC-6/15证据核测量生产入口；`artifact:docs/evidence/P1-ENG-LOOP-002-play-ops.md` §0.6及新停点证据逐条映射本修订。实现限§4.1既有具名文件（`controller/language_selector.py`、`tools/language_serve.py`及对应已列测试/文档），不得为长轮询改LanguageWorker。测试名/结果由实现实际产出，本轮仅冻结、不预签满足。

### 3. 实现交接、未闭项与本轮边界

Implementation合并「R3六题答复落实」AC-7修订2(a)/(b)、AC-10修订1(a)/(b)、「IR-N裁定」AC-15修订1与本节AC-7修订3，同步代码/测试文本、操作单及准备命令；**O-1…O-6与PR-8…14全部随带**，原详表分别见 `docs/reviews/P1-ENG-LOOP-002.md`「R3@K1K2K3K4 派发」§2、`docs/evidence/P1-ENG-LOOP-002-C3-K1K2K3K4.md` §3。重合项合并、观察不当finding/冻结集或已闭证据，不能只引用中间实现“已做”即判满足。重算§0.6有限路径/预留，纠正旧必然不可完成投影；逐步检查measure非零即停、不进k-receipt/Play，IR-N2已答合同但实现/证明仍待。

按「R3六题答复落实」§3与原N-1机器/解释器/次数/墙钟/加载/磁盘及累计2/3账核验证适用性；触及真实模型加载器路径不适用窄修替代全套，原签不适用或需增额/换机则停报具体缺口，不擅跑。按AC逐条附真实证据、完整候选diff解析式、四条件自证及未核风险，提交并推送稳定候选后停在K1K2K3K4，交C4→独立Review先核稳定门/R3资格。上一候选/通过指针运行时从复核机读行与git解析；C首退1/1、复核返工1/2及R3未开轮计数不重置。本轮不做候选核对、不改C3表、不消费新verdict。

IR-N1/IR-N2选择与合同层已答，**实现/相称验证、新候选C/独立复核、Air本人原件对齐与目标依赖核清、现场HEAD/status/Unity日志及适用人眼门、AC-18证据停点仍未闭**。后续仍为候选通过→本人Air原件/准备事实→接受逐维度明确放行→本人前台服务/收据/Unity→正式工件自证/下一实际C/AC-18核实；ENV:2条件性未签0，FACT:2不称当前已齐。Overall REVIEW_PASSED/Lifecycle ACTIVE、AC-14/15/18与AC-16板端NOT_RUN、无UNITY_NA/DONE，旧账/偏差/UNKNOWN、ACQ暂停/非verdict/清理和旧债均保持，无新增release。全局ACQ R2-1 block/release已顺序配对，0消耗性+2零消耗与Gate-echo保持。

本轮consumed=none，仅本机读文档及文档/角色自检和文档提交推送；不SSH、不复制、不加载模型、不跑功能测试、不碰Jetson/Unity/runtime，不写用户原话账本或复核文件。实现/稳定门义务已转Implementation，无新增待用户选择。

open_items: none

## C4核对与Review交接（2026-10-07，Acceptance）

C4@K1K2K3K4已完成，最新逐AC表见「Contract conformance（核对表）」；完整22路径/四条件/五条实现读法、AC修订及O/PR逐条覆盖、预复核关注唯一详表为 `docs/evidence/P1-ENG-LOOP-002-C4-K1K2K3K4.md` §0–5。R-1不符合AC-7修订3冻结证明文本；R-2…5在所列界限内成立，不作为合同变更。AC-7/10不满足、阶段B证据缺失照交新鲜Review核稳定门/R3资格，不再退回；本轮不预签REVIEW_BLOCKED/PASS或finding、无新增AC/容差/额度。

旧C3、旧R3派发REVIEW_BLOCKED及R2范围保留；实际C累计4、首退1/1、实际复核2轮、返工1/2无冻结集。最新N-1全套累计3/3用尽，13既有失败逐名相同、新增0但全套FAILED，不修改历史各轮2/3账。其他原账/停止偏差/UNKNOWN/债务/ACQ暂停不变；没有新运行或里程碑证据、release或UNITY_NA/DONE。下一Review先读候选自证与本C异议并独立判断；新候选通过后本人Air事实/目标环境、接受逐维度放行、现场HEAD/status/Unity日志与AC-18正式证据门仍待。consumed=none，不跑测试/SSH/模型/板/Unity/runtime，不写用户原话账本或复核文件。


## Acceptance rulings（复判）

| 来源 / 轮次 / finding | 裁定 | 日期 |
|---|---|---|
| docs/reviews/P1-ENG-LOOP-002.md / R1@OpsK1K2K3K4 §3 R1-4、R2 §1/§3；实现交接§12.4 | 维持 CLASS_2 / BC-10 机制缺陷归因及R2闭合；N按已签B-main裁为全批实现评分总次数2，不是每归档2或每摘要进程2。常量不改、不开新R；正式三归档不能全评的资源冲突交用户，详见「OpsK1K2K3K4通过消费与SUB:3放行」§2/§5。 | 2026-10-08 |
| `docs/reviews/P1-ENG-LOOP-002.md` / R3@K1K2K3K4 / R3-1 | 保持 CLASS_2 / `BC-7`（AC-7），范围内必修；选择 (i)，以 AC-7 修订4澄清修订3(c)及证明方式，代码/测试名/断言不改；竞速依据与闭合绑定见下节。未签闭合或 PASS，不改复核原文。 | 2026-10-07 |

## R3冻结集裁定（2026-10-07，Acceptance）

本轮是 workflow §4.4 / COORD-009 (c) 的冻结集裁定及 R3-1 分级/合同复判，不是 C 轮、独立复核或运行放行。Dispatch-Id `P1-ENG-LOOP-002-R3冻结集裁定-20261007T190158Z-55cb`，requested.round `R3冻结集裁定`。已读同名复核 R3 §3 与 Verdict、原冻结合同及 CHANGE:5 原签，并沿具名函数/测试/操作单核对依据；只核裁定所需直接关联路径，不另做全量候选复核。D4 engineering-v1 继续有效。

### 1. 冻结集逐条裁定与闭合绑定

未闭集严格为 **{R3-1, R3-2, R3-3}**，三条均为「范围内必修」，无 SCOPE_GAP 或新增债务/release。下表是实现范围与闭合绑定；Acceptance 本轮不签任何 finding 已闭。

| Finding / 依据 | 裁定及可达依据 | 修复范围与闭合绑定 |
|---|---|---|
| R3-1 / `BC-7`（AC-7） | 范围内必修，CLASS_2 保持：六键 llama 生产长轮询可达，旧证明方式字面不符真实失败路径期限，涉及操作/测试判据，不能降 CLASS_3。选 (i)，本轮先澄清合同；不把代码只随硬截止的行为改标 SCOPE_GAP。 | 文本按下节修订4与操作单§0.6对齐；`controller/language_selector.py` 与具名测试的名称/断言不改。R4 定点复看修订4、操作单§0.6及 `tests/test_llama_server_adapter.py::LongPollClientTests.test_wait_is_min_of_4s_and_both_remaining_deadlines_and_io_tracks_t_hard`，核真实 `_long_poll_result` → `_call` 与文本相符，才可闭合。采用复核§3为(i)给出的文本一致性闭合路径；无代码修复，不虚构修前红/修后绿，也不为文本澄清新增测试义务。 |
| R3-2 / `BC-10`（AC-10） | 范围内必修，CLASS_2 保持：第4节是单元#2/#3每次GGUF加载前的生产操作路径；`ss`失败时管道非0落在 `&&` 左侧，`pipefail` 本身不执行STOP，`pgrep`均1仍可启动。准备单元#1附录P不能替代本次核端口。 | 仅返工操作单第4节启动块，先捕获 `ss` 输出及退出状态，失败即 `S-PRECHECK` 停在服务启动前，成功才核端口。沿复核既定 `NOT_MECHANIZABLE` 路径由R4定点复看该块（含ss非0/无输出、成功占端口、成功空闲三分支），不以 `bash -n` 代替语义闭合，不连接板验证。 |
| R3-3 / `BC-10`（AC-10修订1(b)） | 范围内必修，CLASS_2 保持：第1.0节每单元/Play前必走；锚定正则读不到真实§0列表/反引号机读行，空值回落0使行序判据失效。PG空差异只管候选文件，不能证明其后未release的门状态不存在；原合同逐字要求核其后门状态。 | 仅返工操作单第1.0节：解析真实机读写法并核最新round/pass行序，缺有效行或后续未通过则STOP；从固定发布引用按workflow§4.4及 `check_docs.py` 规则核blocks/releases与账本 `RELEASED_SCOPE_GAP`，未release则STOP、不放行。可复用同一发布文档检出的现行自检结论，但须将非0与放行明确绑定，不能只打印提示；不改自检工具。沿既定 `NOT_MECHANIZABLE` 路径由R4定点复看第1.0节，并在一次性副本固定候选发布引用核LAST_ROUND_LINE非空、行序及配对输出。真实复核/账本字节从git读取，不手写JSON/状态造证；未release拒绝与配对/release允许的命令探针仅为该finding的相称闭合，不扩成新AC或板测试。 |

### 2. R3-1竞速复判与 AC-7 修订4（解释修订3(c)及其证明方式）

**原代码核实**：`_long_poll_result` 先算软/硬剩余以取w，再以 `remaining_hard()` 调 `_call`；`_call` 传给opener的是 `min(HTTP_IO_DEADLINE_S, deadline_s)`（5s与硬剩余取小）。`result_wait` 在服务端收到/解析后才以 `time.monotonic()+wait_s` 起算，随后条件变量循环，到期后还要回复/传输。客户端opener调用早于服务端起算；当软剩余不足4s且同时把I/O限成同一软剩余时，两端名义期限相同而起点不同，存在正常pending到期回包输给客户端超时的竞速。毫秒向下取整最多提供不足1ms的差值，不是链路或调度裕量；0.05s是重核间隔，不应当作每次固定超调。竞速可以发生，源码不能证明“几乎必先超时”或目标设备的发生率。

**复核§3因果链更正**：`_call` 捕获TimeoutError会 `_mark_unconfirmed()`，后者明确设置 `awaiting_idle=True` 并保留原在途起点；下一次 `predict_one` 先经原硬剩余的 `/status`，非idle不发POST。故不采纳“未置awaiting_idle、必直接多发一次POST/多扣推理账”的主张。会话 `_designate_failure` 可发起恢复，但不能绕过适配器idle门；真实HTTP失败仍受已签N-3首次失败停止纪律约束。竞速导致正常等待可能变成 `worker_died` 而非软到期 `timeout` 的原因码差异成立，足以要求把两种期限职责写清；不需要依赖上述错误POST推论。

**裁定选择(i)**：「w 随两种剩余收缩、I/O 随 T_hard 收缩」（代码不改）。w限制服务端本次等待，T_ret限制结果接纳与后续result发起；T_ret不另作在途HTTP套接字超时界。单次请求超时参数仍≤5s且随T_hard剩余收缩；若服务/链路不按w返回，软截止后仍可能在现行I/O窗口中等待，不承诺T_ret时刻立即返回。done回包重核双截止、不接纳逾期结果的义务保留。硬剩余与w相等时也不承诺消除网络竞速；原硬截止/fatal与HTTP失败映射照旧。本裁定不改变任一数值、资源、K派生式或结果接纳界。

不选(ii)：ε需要新增冻结的数值裕量；原签没有目标链路/调度上界支持某个ε，0.5s也不能从0.05s重核粒度推得。已有(i)可保持用户选定的4s/16次/回包截止与5s旧I/O上限，因此无需新阈值或用户题。本轮不预注册ε、不授权代码路线(ii)。

以下**追加生效**，原AC-7修订3及历史核对表不覆盖；修订4仅替代修订3(c)的I/O读法与其证明方式中对应文字，(a)(b)(d)及其他证明范围保持。AC解释修订累计8，新AC0，集外义务0。

**修订3(c)现行逐字澄清文本：** 保持5s单次I/O上限，I/O随T_hard剩余收缩，即传给opener的timeout参数为min(5s, 本次T_hard剩余)；w随T_ret与T_hard两种剩余收缩，仍按修订3(a)取值。T_ret不作为在途单次I/O的timeout参数；回包后重新核T_ret/T_hard，不接纳逾期done。测量沿现行60s截止；Play的T_ret仍来自实际收据k_ret/hz，K派生式与原检查点/起点不改，不固定成4s或60s。健康300s/0.25s不改。4s及16次是已选执行边界，非目标设备性能通过线；ceil(min(T_ret,T_hard)/4)不是实际计量或完成保证。

**证明方式与具名范围：** `test:tests/test_llama_server_adapter.py` 覆盖真实服务/result与HttpAdapter路径的query_id/参数分离、w有限正值及4s上界、完成/失败/stuck即时回复、pending到期、16次硬限/无第17次、失败不重试不回退、200请求前守账、w 随两种剩余收缩、I/O 随 T_hard 收缩、回包后软/硬截止拒绝逾期done及旧非llama行为；`test:tests/test_language_latency.py` 与既有AC-6/15证据核测量生产入口；`artifact:docs/evidence/P1-ENG-LOOP-002-play-ops.md` §0.6及新停点证据逐条映射本修订。实现限§4.1既有具名文件（`controller/language_selector.py`、`tools/language_serve.py`及对应已列测试/文档），不得为长轮询改LanguageWorker。测试名/结果由实现实际产出，本轮仅冻结、不预签满足。

### 3. 非 finding 备注与终局交接

PR-16保留原failed映射，不新增逾期failed fatal义务；PR-17保留毫秒线格式，不另设容差，但不将“发亚毫秒请求必然逾期”当已证结论。O-7维持实际已发生连接的保守other计账，不排除或放宽200；O-8不要求改可注入时钟。四项均不分级、不入冻结集、不新增AC或待办债。

Implementation按§1具名操作单返工，R3-1仅对齐文本，不改运行时代码/测试；完成四条件自证、提交推送稳定候选后**直回Review R4@K1K2K3K4（终局），不经核对轮**。复核范围只为冻结集 + RED_LINE + 修复触及行CLASS_1/2；开轮资格仍从复核机读通过指针运行时解析，操作单已被本冻结集点名，其返工属于PLAY_GOVERNING。R4为本停点第二次REWORK_REQUIRED后的终局轮；本项未签D2b决策信封，不自动追加返工轮，未闭则回用户。

本轮无用户题（needs_user=none）。本返工不触及真实模型加载器、数据划分或对外指标路径，验证按engineering§6相称窄修/定点路径，未跑全套必须据实写明；N-1全套3/3耗尽、不授第4次或新模型/回放额度，复核若认为证明不足再报具体缺口，不在本轮假设新资源需求。旧R2通过只限旧范围，R3 REWORK_REQUIRED 2/2及C4历史结论保留；Overall REVIEW_PASSED/ACTIVE不改为新候选通过。Air原件/环境、现场HEAD/status/Unity日志、AC-18正式证据门及AC-14/15/18与AC-16板端NOT_RUN照旧，B-main运行未放行、无UNITY_NA/DONE。

全局消耗性门来源扫描仅ACQ R2-1的block/release，按文件顺序已配对；本轮无新增blocks/releases或账本改标。0消耗性+2零消耗交接与Gate-echo保持。consumed=none：只读本机源码/文档与文档、角色自检；不SSH、不复制、不加载模型、不跑功能测试、不碰Jetson/Unity/runtime、不写复核文件/用户原话账本。

open_items: none

## 诊断冒烟授权落实（2026-10-07，Acceptance）

本轮为诊断范围、资源口径与交接裁定，requested.round = `诊断冒烟授权落实`，Dispatch-Id `P1-ENG-LOOP-002-诊断冒烟授权落实-20261007T192240Z-33e2`。唯一授权来源是 `docs/authorizations.md` 同日「P1-ENG-LOOP-002 — 用户要求放宽粒度、先跑再查错：选先诊断冒烟（推荐）、签粗粒度诊断信封（推荐）、在途 R3 返工与 R4 继续（推荐）」条的用户原话、(a)–(e) 与信封。D4 engineering-v1 保持；本节落实 workflow §4.3.2 已有通道，不新开 D/C/R，不追加或改写正式 AC，不签 verdict、运行验收或新额度。

### 1. 诊断范围、链路与产物边界

只做本项阶段 B **诊断冒烟**：用户本人在 Air 经既有 SSH 前台起同一 Jetson Orin Nano 8GB Super 上的 C2 Q4 + mmproj + llama-server，经本项 language_serve / HTTP 接入 Air 的语言会话、det-assoc-v1 常驻快层、standoff-band-v1 与 Unity Play。操作者可演练语言指定、预览/人工确认、跟随、换目标和丢失/歧义报告；不用正式三剧本完成数、样本数或四类数字作诊断通过线。快层留 Air，不搬到板上；不启用5060、云或外部API；服务与Play均由本人操作，角色仅准备步骤。

- 每份操作页、终端开场与保留的诊断记录明示「诊断；不进证据链；不作任何门判定」。不创建、不消耗 scenario/session/run ID；沿用既有场景标识，不登记正式会话/运行，不向 `runtime/runs/` 产出正式段。现有 `controller.language_loop run --diagnostic` 的 `diag-` 前缀仅为进程/锁/目录关联的诊断标签，配合独立 `--session-root` / `--diagnostics-root` 将段日志放在诊断根，不得把标签改称已签的新ID或计入正式注册表。实现须把这三个选项列齐，不能只用 `diag-` 名字而漏 `--diagnostic`。
- 诊断记录统一在本项独立的 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/` 下，路径在操作时解析；不回填 `docs/evidence/` 的正式 assets/K收据/四类数字/ledger，不入正式 Unity 验收日志。必要的临时测量报告、资产期望与K参数文件只服务于现有入口的身份/时效检查，明确为诊断输入；即使由现有生产函数生成、退出码为0，也不是 AC-6/14/15/16/18、K停点或任何门满足依据，不转作正式运行输入。诊断不用离线评分「试数」。
- 模型身份、冻结prompt/schema/decode、十项llama资源旗标、帧绑定/软硬截止、人工确认、真值隔离、围栏/发布门/hold与共享槽位互斥均保留。诊断不是绕过安全检查的入口；运行时的拒收/超时是待查现象，不是本轮的正式门判定。
- 反调参纪律按 workflow §4.3.2：正式门工件产出后，不得依据门数字改参数、帧集、阈值或测量对象；不得在正式运行之间借诊断试数。诊断发现的问题保留原现象，走正常具名返工/合同问题渠道；操作步骤不得夹带快层、规划器、K阈值或运行时代码修复。需要语义改动仍按原停点流程办理。

### 2. 粗维度与 HTTP 守账的诊断专用旁路

只认本条用户签发的粗维度，独立于正式 B-main/N-3 和 JET 旧诊断原账，成功、失败、中止与重启均不洗账：

| 维度 | 本次诊断边界与执行读法 |
|---|---|
| 总墙钟 | ≤3 h（10,800 s），包括SSH、准备/非模型代码同步、冷加载、必要诊断输入生成、Play、失败等待与安全收尾；操作前开始记时，保留收尾时间，不把SSH与Play拆成两个3 h信封或重启后清零。并行重叠时间不重复计，暂停/等待不重置整批计时。 |
| Unity/Play | ≤5次，用户本人在MacBook Air；按实际进入Play计，进入后的失败/中止照计。没有本诊断单次420 s、累计2100 s或P1/P2/P3分配上限；代码自身的帧窗/时效约束仍执行。 |
| 板服务/GGUF加载 | ≤3次，包含至多1次故障重启，非「3+1」；一次wrapper与它的一次llama子进程/GGUF加载为同一启动，不重复计，但实际再次加载/失败加载仍计入总3次。已有进程退出、释放端口后才可在剩余额度内作这1次故障重启，无自动重启循环或后台服务。 |
| 板推理、HTTP、SSH与字节 | 板推理不单独计数；非推理HTTP条数、传输/有效载荷/磁盘字节、SSH次数等细维度不设上限、不要求代码守账；均受总墙钟和用途约束。不继承正式200/335、三认证主连接、20MB/60MB、峰值磁盘等限额，也不把细账缺失当诊断停止原因。 |
| 零额度/禁止范围 | 5060、云、外部API、另列GPU·h、下载、安装、模型传板、新scenario/session/run ID均0；无新设备，不改系统/SSH/沙箱设置，不安装/编译依赖。板上本次推理由加载/墙钟约束，不把另列GPU·h=0读成禁止用户已签的板推理。 |

**现有CLI事实与裁定：** `tools/language_serve.py::_main_llama` 强制要求 `--http-ledger` / `--non-inference-reserve`，总限缺省200/335且只许调低；reserve=0仍守200/335，省略参数会拒启，把上限设巨数也会被解析器拒绝。因此这几种命令都不能兑现粗信封。本轮不修改该正式入口/合同，不通过删账、每次换账路径或不断重启「刷新200」来旁路。

**选定诊断组合路径：** 实现角色在独立诊断操作页写前台、进程内的一次性Python启动块，复用现有 `llama_preflight`、`llama_server_command`、`_wait_llama_ready(..., budget=None)`、`SingleFlightRuntime` 和 `build_server(..., budget=None, long_poll=True)`。不调用强制建账的 `_main_llama`，不实例化 `HttpBudgetLedger`，不用 `--http-ledger` / `--non-inference-reserve` / `--non-inference-limit` / `--inference-limit`；它们在本路径为“不适用”，不是0上限。诊断access_log可为None，或仅在诊断根留观察日志而不求和/守限；不得使用正式ledger。复用真实preflight、既有身份/部署摘要和子进程起停/释放逻辑，退出/信号均须关闭HTTP服务、停子进程并清临时图像；只在本人SSH前台存活期间服务，不修改源码、不猴补丁正式函数、不持久化后台/系统服务。启动块只在诊断操作页中提供，不新增 `tools/` 运行入口或改本次R4候选。

**双端守账关系：** 服务budget=None时不做429预算兜底、不返回 `http_budget` 字段；健康轮询无账本拦截。Air用全新诊断进程/HttpAdapter，`http_budget` 初始为None；`controller/language_selector.py::_take_budget` 在回复无快照时保持None，`_budget_guard` 因而不施加细账上限。不能沿用已吸收正式快照的适配器或接错正在守正式账的服务。保留300 s/0.25 s就绪机制、单query至多16次result、w≤4 s及T_ret/T_hard/I/O期限，它们是现有运行算法/失败行为，不是本次诊断HTTP或推理总量额度；不调大这些常数。命中这些行为记录为诊断问题，不套正式N-3“首次主臂失败停全部、重启0”的整批处置；仅按本节§4停止闭集与已签重启额度处理。

这是用户(b)(e)授权的诊断调用组合裁定，不是AC-7修订5，也不解除正式AC-7修订2/3/4、AC-10修订1、AC-15修订1、B-main/N-3或正式现场门。返回正式线须重新使用正式操作单、正式守账入口和独立剩余额度；诊断输入/余额不能转用。

### 3. 未核环境事实与代码传板读法

本轮不SSH、不复制、不import运行探测、不加载模型、不跑功能测试，不从文件名或旧快照声称当前环境已齐。以下事实在本人诊断准备中查明，静态读/必要无模型import可在本诊断用途及3 h内完成，不借已耗尽miniSSH或作废Air补核信封，也不先申请细粒度ENV:2额度。

| 未核项 | 已有来源与诊断现场处理 |
|---|---|
| 板上三文件当前是否在位/可用 | 本项 `docs/evidence/P1-ENG-LOOP-002-precheck.md`「Mac mini只读补核原始读数与逐维度用量」的R02及「资产/共享库/部署根/监听事实」证明当时三件在位且sha匹配；不是当前读数。路径、期望和构建号从已有原流/来源运行时解析，现场核三件，不手抄SHA。不存在/无法运行时记录问题；需要重新下载、安装或模型传板才可解决的，落§4停止条件，不用本条补模型。 |
| LOOP-002部署代码是否已在板、是否同版 | 同份补核R09中计划根/code/logs当时不存在；不能称现在已部署。本人检查 `config/p1-eng-loop-002-board-deploy.json` 所列16路径及清单自身（清单已包含自身），以本次Air源码运行时求的部署摘要比板端，不套旧PASS作为诊断放行前提，也不称新候选通过。 |
| 若代码缺失，传输是否属于本签 | **裁定属于已签诊断准备用途**：(b)明确传输字节/SSH次数不设细限、零项逐字禁止的是“模型传板”，(a)(d)(e)明确要求该服务链并交接受落实代码在位事实。只允许本人经既有SSH/SCP或SSH stdin的tar流同步上述纯源码/config闭集到独立诊断源码根；不传模型、权重、mmproj、二进制、共享库、轮子或其他资产，不覆盖旧证据/部署，不git拉网下载、不pip/安装/编译。代码同步与启动块stdin均计总墙钟；不消费正式部署1次/20MB余额。传输方式若实际需要安装工具、下载、新设备或模型/库迁移，不能用“代码传输”掩盖，停回用户。 |
| Air端解释器/快层依赖与本机资产 | 当前工作树候选、本机det-assoc-v1配置/freeze/权重、可用只读Python环境（含torch/ultralytics/cv2/numpy/lap等实际触达依赖）、Unity场景、既有SSH别名/链路及预览入口是否齐全尚未现场核实。旧静态/module在盘读数及测试不证明Air当前动态可用；只用已有本机离线资产/已装环境，不由本条下载/安装或迁Unity到mini。实际缺件先记录、说明可用旧位置；必须取得新资产才可运行时用§4题转呈。 |
| 端口、共享槽与系统状态 | SLOT互斥已由用户确认，不重问未来窗口题；现场仍核18081/18082与活会话槽、不清未知进程、不碰46273、不提权。库/驱动/运行内存及HTTP/schema实际可用性仍UNKNOWN，只作诊断现象，不建立新性能/内存STOP线，不追认旧JET结果或AC-16。 |

正式FACT:2的完整C2来源原件对齐及engineering§9正式环境核清仍未闭；诊断不把它们改成“已齐”，也不把正式证据前置套成本诊断要等R4才开始的门。身份检查所需原始期望仍须据实解析；步骤不可捏造来源/报告或用身份检查旁路来换取闭环。

### 4. 诊断停止闭集与条件性最终用户题

整批STOP只保留下列四类，不搬入正式§6.2/N-3十一码，不设新门或细额度：

1. **越出粗维度**：下一步将超过总3 h、Play5次、启动/加载3次或故障重启1次，或触达已签0项；停止新增业务动作并安全收尾。结束前有余量也不转入正式线。
2. **需要下载/安装/新设备**：包括需要传模型、二进制/库/依赖而原签0，当前已有离线资产无法支持所需链路；停在该动作前，由用户决定新范围与额度。
3. **安全/红线**：真值泄漏、身份/帧时间语义或控制安全被绕过、运行时安全失守、同板资源/槽位冲突无法安全解除等；立即停止相关执行、安全收尾，问题走正常返工，不以剩余额度绕过约束。
4. **用户中止**：本人要求停止即结束诊断，保留已有现象与粗用量。

缺库、非安全性HTTP/解析失败、K输入生成失败或代码启动报错先记录为诊断故障；失败的步骤不能假称完成，可继续已有环境内的其他安全诊断/定位，或在粗信封内作至多1次服务故障重启。代码所需修复交正常返工，不在操作页即兴修源码。无后续可执行动作时据实收尾，不为“先跑”强行补资产。UNKNOWN、200/335/字节数、旧全套用尽或R4未派发本身均不是本诊断新增STOP；红线与全局未release消耗性block仍不可旁路。

以下依「R3阻断消费与用户待决」§3的转呈格式保留**条件题**，当前没有已证实触发，不向用户提问、不代写账本、不授权supervisor代选。已签额度/代码同步读法不重问；实际触发时由实现给具名缺件/拟动作、设备/执行人、已有离线替代与所需额度，supervisor再原样转呈，不用一题预签任意下载/安装。

#### DIAG:ENV:1 — 已有环境不能支持诊断时的处置（仅触发后转呈）

request_id: `P1-ENG-LOOP-002:DIAG:ENV:1`

**原题与来源**：本节§3现场缺件/依赖事实与账本(a)–(e)零项。转呈时在本题附实际缺件清单及唯一拟动作，不以UNKNOWN代填，未触发不得当成当前待答前置。

**转呈题目：现场已确认的缺件无法用已有离线环境解决，是否让本批诊断到此保留失败，还是另行准备该具名缺件的独立范围/额度申请？**

- **A（推荐）：本批到此，保留诊断故障与已用粗账**；缺件/代码问题走正常返工，正式R4照旧。
- B：本人提供已有本机/板上离线资产或已装环境的准确位置；角色据实核查，只有仍落本粗信封时才续诊断，不含跨设备资产迁移或安装。
- C：先准备该具名缺件的独立申请，逐项列实际设备、动作、次数/墙钟、下载/安装/传输等所需额度，再由本人单独签发。选C只授权零消耗准备，不授权执行或泛化扩额。

**推荐理由/只能用户定**：下载/安装/新设备/模型传板现为0，不能用不设传输字节上限推导这些类别可做，接受或调度角色无首签权。A保留已签粗维度及真实失败，不因诊断目的扩大范围。

**信封/正式线影响**：A/B/C均不改正式B-main、N-3、R4范围或任何AC，不重置本批诊断粗账；需要延时/增Play/增加载或新增零项类别时，另列该具体变化的申请，不续用本题默认值。当前 needs_user=none；触发后保持本request_id交用户，不把推荐当答复。

### 5. 交接、轨道判定与本轮交付

正式线 **R4@K1K2K3K4终局仍待派发**，沿 `docs/evidence/P1-ENG-LOOP-002-r3rework.md` §2/§3/§7原候选与冻结集+RED_LINE+修复触及行范围；不撤销、不改写该行或R4输入，不因本节或诊断操作页重开C/换候选/要求复核诊断页。R3返工已经提交推送，本批接续诊断准备符合用户“排在返工之后”的顺序；诊断与正式复核不互设依赖，全局单写者保持。

诊断线交Implementation：只写 `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` 精简操作步骤及状态交接，文首标明“仅诊断，未经核对/独立复核，不得用于正式运行”。落实§1–4：既有环境核查/16路径代码同步方式、本人SSH前台budget=None组合块、诊断输入与Air `--diagnostic` 路径、操作者指令/目检、仅粗维度手记和起停/失败收尾；不复制正式长操作单全部门/账、不新增工具/脚本入口或修运行时代码，不SSH/复制/加载/测试/碰板/Unity/runtime。准备提交后直接交用户本人执行，不经C/R，不消费诊断额度；诊断故障后需修代码另走正常渠道。

**Consuming=yes裁定**：诊断交接行承载“步骤准备→本人诊断Play”这一已签通道，后续会使用本条Play≤5额度，依AGENTS/workflow§7规则0就是消耗性；无正式ID、不入证据不等于不耗Play。该值不宣称本轮或实现写步骤已消耗，也不授权代理代跑。这样占1消耗性，原JET用户方向与正式R4两条零消耗保持，共1+2，无须擅暂停任何现有项。所有引用本项标识逐字echo当前Overall REVIEW_PASSED（仍只限R2旧范围），本项Lifecycle ACTIVE与正式各门保持。诊断准备和运行接力沿用此行，不再另加第3条零消耗行；结束/触发用户待决时依实际进度更新。

全局机读block/release完整来源检查已通过：实质ACQ R2-1按文件顺序配对，无未release block；本轮不改复核文件或SCOPE_GAP账本。不把R3的REWORK_REQUIRED改成block已解除或新候选PASS。AC-14/15/18与AC-16板端NOT_RUN、正式现场HEAD/status/Unity日志与AC-18证据停点、旧债/偏差/UNKNOWN及暂停义务全部保持；无新里程碑证据，implementation-status不增诊断证据。

consumed=none：本轮只读本机文档/相关代码、落实本节及状态板并运行两项文档自检；SSH/复制/模型/测试/Jetson/Unity/runtime均0。不写用户原话账本、不签新信封或独立verdict。

open_items: none

## R4消费与诊断故障裁定（2026-10-07，Acceptance）

requested.round = `R4消费与诊断故障裁定`；Dispatch-Id `P1-ENG-LOOP-002-R4消费与诊断故障裁定-20261007T205352Z-ca8d`。本轮消费终局、按用户要求裁定新诊断故障并交实现，不是 C 核对或独立复核。D4 engineering-v1 保持；只读本机合同、原代码、复核/来源记录与诊断原件，不跑功能测试、SSH/复制/模型/Jetson/Unity/runtime 均0，不写复核文件或用户原话账本。

### 1. R4终局消费、归因与当前门

同名复核 R4@K1K2K3K4 §0–5/Verdict 是唯一独立结论：`PASS`，通过候选从该节 `passed_candidate` 运行时解析。`-r3rework.md` §7范围与§2–8自证相符；R3-1经修订4逐字文本/代码/具名测试定点核实，R3-2、R3-3经生产操作块的修前红/修后绿桩/只读git探针闭合；代码零diff，R4判窄修替代充分，未跑全套、不记全套通过。冻结集三条均已闭，不再留“待R4”交接。

机械归因：R1-1 `BC-7`→实现错误1，R2已闭；R3-1 `BC-7`、R3-2/3 `BC-10`→实现错误3，R4已闭。本项累计实现错误4；独立finding中的 `IN_SCOPE_NO_BC` / `SCOPE_GAP` / `上轮漏检` / `上游漏检` / `RED_LINE` 均0；不从关注项照交或本次诊断反馈改写这些统计。原K1K2K3K4：C累计4/首退1，实际复核4轮/返工2/2终局通过，一次REVIEW_BLOCKED未开轮；本轮不另开轮。此前AC解释修订8，本节追加3条解释修订后累计11、新AC0，不添加新验收编号。

消费 R4 足以确认原冻结集范围 `REVIEW_PASSED`，但本轮同时按用户具名故障裁定当前代码需修，故**最终 Overall=REWORK_REQUIRED、Lifecycle=ACTIVE**；独立 review 列保留 R4 PASS 已消费，不撤销历史 verdict。AC-7/10最新表解除R3原原因并标新故障待修；不是“诊断失败即正式验收失败”，也不把诊断读数认作门证据。阶段B正式放行 G1–G5 本轮不签，AC-14/15/18及AC-16板端仍NOT_RUN，无UNITY_NA/DONE。旧债/偏差/UNKNOWN/用量及ACQ暂停不变。

### 2. DIAG-VERSION-1：事实、合同读法与分级归属

诊断只读入口为 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/` 中用户本次目录的 `NOTES.md`、`board/check.txt` 与 `board/closeout.txt`（目录名由该根/本轮交接运行时定位，不手抄派生标识）。NOTES“返工交接”为辅助定位，不是独立复核。原始check显示三sha匹配、version_rc=0、ss_rc=0/pgrep_rc=1；原样两行：

> version: 0.5.0-dev (build 0, commit unknown)
> built with GNU 13.3.0 for Linux aarch64

本轮静态核实 `tools/language_serve.py::VERSION_PATTERN/read_runtime_build/llama_preflight`：只搜 `^version: (\d+) `，语义版本后的字符为点，故不匹配；preflight在创建服务/模型子进程之前拒启。正式资产生成块 `-mini-ops-prep.md` 附录B与诊断页附录1 gen复制同一限定，同样拒绝。仅改expect-assets不能修真实preflight；本次未同步代码/启动服务/进入Play，与原记录一致。

来源链按各原件的主张上限读取：`docs/evidence/P1-ENG-JET-001-stageb-source-archive.json` 的 `binding_chain/ archive` 将发布标签 b11381 绑定到固定提交请求返回的那份归档；`-stageb-build-rerun.json` 的 `input_binding/unpack/cmake/products` 经传板对象将该归档绑定到板上构建路径与产物stat，**该构建JSON没有二进制sha**。二进制sha期望还须经本项 `-precheck.md` mini M5/R02 与正式操作单附录A所核 C2 收据 `server_sha256_now` 链取得，不能从build-rerun凭空产生。原构建参数没有注入伪造BUILD_NUMBER；归档不带git元数据的构建自报0/unknown与这条来源记录相容，不把此输出当“源码标签未知=来源链不存在”。这只是既有资产来源解释，不将JET诊断/构建读数提升为本项正式AC-16核验，也不扩大三文件身份为共享库/驱动/dlopen整栈身份（LIB原签披露保持）。

A2(d)已逐字规定 runtime_build **只是二进制自报标签，身份锚点是二进制sha**，不是要求自报等于b11381。因此选既有字段域内方案：旧整数格式仍取该整数；本次完整语义版本行取其明确的 **build 0 → b0**。0是原流明确自报值，不是伪造或缺失时默认填0；不取语义版本首位“0”冒充build，不从源码标签补b11381，不改原流、换二进制、下载或重编译。源码标签/归档链独立作来源披露，完整原样version文本与退出码留资产原流及派生文档；不新增/放宽六键值域，不将raw版本文本塞进 model_identity 的 runtime_build 字段。

**裁定 CLASS_2、范围内必修**：真实固定资产可达的启动/身份失败路径，涉及操作行为，非CLASS_3或SCOPE_GAP；不改研究数字/结论，无CLASS_1/RED_LINE。本轮为用户要求的新故障裁定，不冒称复核finding或签机读block。归属是**阶段A遗漏真实version格式的合同假设/覆盖缺口**（原A2(a)明写旧正则，原实现按字面做，并非当时违反正则义务）；接受/核对与独立复核夹具只覆盖旧整数模板，遗漏没有在真实目标条件上确认该假设。修复由本项Implementation承担，不推给用户换资产，也不追改JET或原R4依据列。新候选须覆盖原生产preflight和两条gen路径，不能仅放行诊断脚本。

### 3. 追加生效：AC-7修订5、AC-16修订1

**AC-7 修订 5（解释A2(a)(d)、AC-6/7；仅替代A2(a)旧格式唯一性的读法）**：在保持 `^b[0-9]{1,7}$` 与六键比较链的前提下，版本解析接受两种有明确数值构建号的行：原 `version: <整数> …`；本次 `version: <语义版本> (build <整数>, commit <文本>)`。语义版本行读取括号内build整数，原文本/版本号/commit不改写；本次输出得到b0，commit unknown不当作源码认证。本次语义版本形式以原始行及明确build字段为界，不泛化任意含数字的文本；两种形式均只有唯一有效版本身份行且build域合法才可取值，缺行/重复或冲突行、缺明确build、非法域、非0退出、超时/OSError一律StartRefused，禁止缺失默认值。保留旧整数正常格式与已有非0/无法解析拒启行为；三sha和runtime_build与expect-assets逐键不等仍在模型加载前拒启。服务/status→报告→收据→会话的比较链、prompt/schema/decode、资源旗标、local-hf与HTTP守账不变。

**AC-16 修订 1（解释资产原流与runtime_build来源，不新增身份类别）**：正式资产gen与诊断gen遵循修订5同一解析语义，分别读取本路径实时原流及该次版本退出码；原样文本/rc及来源指针保留，二进制sha由当前板端核实并与既有来源期望匹配，源码归档/build/C2收据绑定链只作来源披露，不用旧JET读数或本次诊断check替代正式实时核验。正式原流/资产文档与诊断输入分别生成，不覆盖旧原件、不互转。保持三文件、量化闭集与库身份限制；raw version为审计元数据，不增加model块必需键或改变AC-6值域。当前AC-16板端仍NOT_RUN。

证明仍用既有 `test:tests/test_llama_server_adapter.py` 的生产preflight拒启/身份用例，加原样语义版本字节夹具的修前拒绝、修后b0与错配拒启；保留旧格式回归及invalid/非0/缺build/重复冲突分支。两条gen直接抽取候选操作页原块作离线输入核验，核相同文本/退出码映射与停止方向；不得启动真实二进制/模型。实际测试名/结果由实现写证据，本轮不预签通过。修订是用户诊断与具名返工定位触发的合同答复，不来自核对轮自查新增义务。

### 4. OPS-SOURCE-1：两处来源加载同批修复

已读正式操作单§0.3、§3第4步（用户称“3.4”）、mini附录B指向的命令：`set -a; . <(grep -v '^RESOLVE_OK$' ...); set +a`。操作单只启用pipefail，未检查grep生成/`.`加载退出码；进程替换生产者也不是本命令前台管道的退出状态，末尾set +a可掩盖加载失败，随后资产gen仍可执行。**核实了当前失败处理缺口**；本轮不跑shell探针，故不将“所有Air bash3.2必然静默失败”写作已重现事实。实现报告的具体兼容故障及旧/新行为需由实现/复核在Air `/bin/bash` 3.2一次性副本中核实；`bash -n`不够。诊断页改用普通文件避免该构造，但不能证明正式两处已修。

按用户请求裁为CLASS_2、范围内必修，主要对应AC-10（来源/资产前置的操作员路径）；不是格式债，不留SCOPE_GAP。实现负责修正式两处及mini附录B对应可复制命令，统一生成有界普通env文件、逐项检查生成状态/RESOLVE_OK、检查加载状态及必需变量一致性，失败须STOP停在资产生成/SSH/服务之前；保持合法来源输出字节与变量值，不改来源选择。**AC-10 修订 2（解释AC-10与§3.6来源前置）**：上述来源解析、过滤/普通文件生成、加载三步分别核退出状态；仅成功且完整输入可进入下一动作，后续set +a不作为加载成功凭据。只澄清既有缺件即停/来源对齐义务，不增新资产/设备/信封。本问题属阶段A操作单可执行性/失败路径遗漏，不改R4修复三处已闭结论。采用候选原块的离线成功/解析失败/生成失败/加载失败探针核修前红/修后绿；复核不得只签语法通过。

### 5. 实现闭集、新停点与资源边界

交Implementation零消耗本机返工。具名闭集：`tools/language_serve.py`（仅版本解析/拒启）、`tests/test_llama_server_adapter.py`（上述生产回归）、`docs/evidence/P1-ENG-LOOP-002-play-ops.md`（两处加载及版本说明/来源块引用）、`docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md`（附录B资产gen与加载命令）、`docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`（附录1 gen/相关说明）；证据写同名前缀具名文件。不改实际GGUF加载器、llama_adapter推理/prompt/schema/decode、controller/模型身份字段表、冻结件、指标、采样、K值/时间、安全或守账，不修JET源文件，不扩部署闭集/第三方依赖。必要越出此闭集先报具体合同问题，不借本节泛化修复。

本次版本来源解析澄清改变身份入口的协议读法，触发**新的K1K3身份修复停点**（K1字段来源/一致性链，K3 VLM身份拒启；不改变K2安全或K4指标）。这是R4终局通过之后用户具名授权裁定的新合同修复范围，**不是给旧冻结集追加R5、重开旧终局或清零旧2/2上限**。实施完成四条件自证→接受下一实际 `C5@K1K3` →新鲜独立 `R1@K1K3`（仅当相对最新passed_candidate的PLAY_GOVERNING diff非空；本修复tools/tests非空即有资格）。该停点后续计数按现行规则，原K1K2K3K4终局/计数留存。复核全量基线从R4通过指针派生，检查此次真实全量diff、原生产preflight、两条gen/普通文件加载闭环与RED_LINE；诊断反馈不是其通过证据。操作单继续为旧冻结集点名的PLAY_GOVERNING。

N-1全套3/3耗尽、真实模型加载/回放/设备操作本批0；此窄修不改真实模型加载器、数据划分或指标，按engineering§6以覆盖具名改动的零模型focused及修前红/修后绿/操作块探针代替全套，未跑必须据实写明、不能称全套通过。若实际修复触及真实模型加载器，或复核认为替代不足，停回用户列具体新增验证信封，不能先跑第4次。focused只用Air已有环境/临时替身，零真实模型/数据回放，不装包。没有新板/Unity证据，明确“修复未在真实板条件下验证”。代码修复不自动重新发令诊断或正式B-main，后者仍逐一G1–G5与AC-18。

### 6. 诊断收尾、余额效力与最终用户题

本次记录墙钟390s、Play0、板服务启动0（故障重启0）；NOTES与closeout记端口释放/无残留，诊断根未建、无同步/服务/Play，Air runtime恢复和工作树0为用户反馈，不提升为正式验收或本轮设备核实。本轮consumed=none；390s是用户已发生用量，不能算本角色消耗或从B-main扣除。

原授权语境“跑一次…冒烟”及账本范围“一次诊断冒烟”，同时允许活动批次内≤1故障重启，**不构成每次代码修复后无限重开批次授权**。本次已记结束时刻并完成故障收尾，不能把下一次另起计时/目录当原批自动续跑；零启动/Play不等于没开始，390s已计。保留算术余额10,410s、Play5、启动/加载3（其中故障重启≤1），当前不可执行、不转用、不重置；也不以本裁定自动作废或签发它。活动批次中的“可故障重启”不能替代已结束批次的续试范围决定。DIAG:ENV:1未触发：本次无已证实需下载/安装/换设备的缺件，不泛化问该题。

#### DIAG:RESUME:1 — 修复后是否明确允许余额续试

request_id: `P1-ENG-LOOP-002:DIAG:RESUME:1`

**原题与来源**：账本2026-10-07诊断冒烟授权(a)–(e)/粗信封、本节已结束事实与用户要求裁定再试。不是重问已签粗维度，也不请求自动新增3h。

**转呈题目：本次在预检版本解析失败后已收尾，修复候选经C5/新K1K3独立复核通过后，是否明确授权用户本人以原粗信封剩余额度再做一次诊断冒烟？**

- **A（推荐）：明确允许一次余额续试**。旧390s/0Play/0启动账保留；另次本人操作的新增完整墙钟≤10,410s（含准备、同步、失败等待与收尾），两次实际操作累计≤10,800s；新增Play≤5、启动/加载≤3（其中故障重启≤1，仍非3+1）。仍只Air+同板/同三文件，原零项/身份与安全、共享槽、独立诊断根、不进证据/不算门/不转用B-main保持。此选择修改“一次”范围为本次结束后允许再试一次，不包含继续无限返工重开；用户答复当场逐字入账、接受落实后方可交本人，不从推荐推定已授权。
- B：本次到此，保留故障与已用量；余额不执行，代码修复/C/R仍继续。未来是否诊断另由本人给范围和额度；不自动转为正式放行。

**推荐理由/只能用户定**：本次未到服务/Play演练，复用原剩余总量可完成原意且不增加资源上限；但已结束批次的再次开始超出“一次”范围解释权，Acceptance/supervisor不能替用户续签或改批次计时口径。COORD-015 §5.2范围/信封事项不可代拍。A/B均不改正式B-main/N-3、冻结指标或G1–G5；即使用户选A也须完成具名修复与上述前置，不授权本轮执行。

诊断交接行暂停于实际收尾（保留Consuming=yes，因未来续试含Play），Status=PAUSED_DIAGNOSTIC_ENDED_AWAITING_USER；不是工作项Lifecycle暂停，原JET方向行保持。实现行接替本轮接受行，Progress逐字含本轮名；0消耗性活跃+2零消耗活跃，Gate-echo随最终REWORK_REQUIRED更新。全局blocks/releases按完整来源检查，既有ACQ R2-1已配对，本轮不签block/release或改标SCOPE_GAP。

open_items: none

## DIAG续试授权落实（2026-10-07，Acceptance；C5@K1K3）

唯一来源：`docs/authorizations.md` 2026-10-07「P1-ENG-LOOP-002 — 用户答 DIAG:RESUME:1：选 A 允许一次余额续试（推荐）（supervisor 会话代录）」条。已核原题「R4消费与诊断故障裁定」§6 A及账本展示说明：用户选「A 允许一次余额续试 (Recommended)」，与A范围一致；题面「冷烟」是supervisor笔误，按同题上下文读作「冒烟」，不新增冷启动测试或资源类别。本轮不重写/代录用户原话账本，也不把supervisor读法当首签。

**生效范围**：用户本人仅可再做一次诊断冒烟，先满足本修复C5核对与新鲜独立R1@K1K3通过并由接受消费；C5当轮仅核对完成；现R1 PASS已由「R1K1K3消费与诊断放行」消费并核前置，可按该节交本人执行。旧390 s/Play0/启动0/故障重启0完整保留；续试新增完整墙钟≤10,410 s（173 min 30 s，包含准备、同步、等待、失败与收尾），两次操作累计≤10,800 s。新增Play≤5，板服务/GGUF加载≤3、其中故障重启≤1（非3+1；含拒启的保守启动计数照旧）。只限Air+同一Jetson+同三文件；5060/云/外部API/下载/安装/模型传板/新scenario/session/run ID等零项不变。细维度仍按原粗信封不设上限，不能从中推出零类别可执行；身份、prompt/schema/decode、时间与控制安全/真值隔离、共享槽、独立诊断根、不进证据/不判门/不转用B-main保持。再次结束后不随修复无限重开。

**操作页计时适用口径**：`docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` §0/1/7及附录0的3 h/180 min为原总量说明。续试不能另得180 min：新的clock-start只计本次增量，elapsed读数须与旧390 s共账，实际STOP按本节10,410 s新增上限及10,800 s累计上限；开工手记明确旧账、本次增量和累计。150 min不再开Play的建议是预留收尾，不扩大续试上限。本轮未改实现操作页；交本人时必须同时提供本节覆盖口径，不能只给旧页或把新目录读作额度重置。相关待复核主张见-C5-K1K3.md §3。

**交接/门**：诊断行保留Consuming=yes；原PAUSED_PENDING_R1_K1K3已由「R1K1K3消费与诊断放行」解除并交本人一次续试；用户已答，不再列待答续试题。未release消耗性block仍全局检查，当前实质ACQ R2-1已按文件顺序release；不新增block/release或SCOPE_GAP。C5不替代R1稳定门核实，不预签独立PASS，不解锁正式B-main/N-3/G1–G5或AC-18；板端/Unity未验证及旧债/偏差/UNKNOWN保持。本轮零消耗，无新的当前needs_user（DIAG:ENV:1仍仅实际触发后转呈）。

## R1K1K3消费与诊断放行（2026-10-07，Acceptance）

requested.round = `R1K1K3消费与诊断放行`；Dispatch-Id `P1-ENG-LOOP-002-R1K1K3消费与诊断放行-20261007T215632Z-39a6`。本轮是最终通过轮消费、归因及既签诊断续试前置核清，不是新增C轮、独立复核或阶段B正式放行。D4 engineering-v1保持；本轮零消耗，不SSH/复制/加载模型/跑测试，不碰Jetson/Unity/runtime，不写复核文件、实现证据或用户原话账本。

### 1. 通过轮消费、归因与Overall

唯一独立结论是 `docs/reviews/P1-ENG-LOOP-002.md`「R1@K1K3」§0–5/Verdict的 `PASS`。运行时从该节解析唯一 `passed_candidate`，核其与该轮 `round_candidate` 相等、为本轮开工HEAD祖先；候选至开工HEAD的PLAY_GOVERNING（含原冻结集点名正式操作单）diff为空。不手抄候选SHA，不把本轮文档提交另称代码候选。C5完整核对见 `docs/evidence/P1-ENG-LOOP-002-C5-K1K3.md` §0–4；正常通过消费按workflow §4.6不做第三次常规候选检查、不重跑测试。

R1独立核稳定四条件成立、窄修替代全套充分：focused 501例OK（skip4）、12例修前3F+20E/修后OK、原块gen16/16、来源加载9+10例；真实板/二进制/Unity未验证，未跑停点全套，不记全套通过。AC-7/10代码与操作文本结论已更新到最新核对表；AC-16代码/文本成立而板端仍NOT_RUN。PR-K1按操作员逐步执行语义成立、Air STOP仍须本人停步；PR-K2/3真实平台与诊断页全步骤未验证的限制保留，PR-K5计时覆盖在§3落实。

唯一finding K1K3-R1-1：`CLASS_3`、依据 `BC-7`（工程读作AC-7）→机械归因**实现错误1（非阻断证据叙述）**。连同原停点已闭4条，本项实现错误累计5（原阻断4已闭、本条非阻断待补）；`IN_SCOPE_NO_BC`/`SCOPE_GAP`/`上轮漏检`/`上游漏检`/`RED_LINE`均0，不把既有诊断故障裁定另计作独立finding。新K1K3：C1次（实际名C5）/退回0/1、R1次/返工0/2；原K1K2K3K4 C4次/首退1、R4轮/返工2/2终局、冻结集闭合和一次REVIEW_BLOCKED未开轮保持。AC解释修订11/新AC0，本轮新增0；N-1全套3/3用尽、旧失败/偏差/UNKNOWN/OPEN债和ACQ暂停不重置。

**裁定Overall=`REVIEW_PASSED`、Lifecycle=`ACTIVE`。** 新身份修复停点独立通过已消费，无未闭阻断；非阻断笔误不把Overall留在REWORK_REQUIRED。原R4终局PASS仍保留。AC-14/15/18与AC-16板端NOT_RUN，无UNITY_NA/DONE；B-main/N-3已签不等于运行放行，正式G1–G5、Air正式原件/目标环境、现场HEAD/status/Unity日志及AC-18证据停点未闭。

### 2. CLASS_3补丁后置与仓库静止窗口

K1K3-R1-1保持复核原分级/依据，不复判、不改SCOPE_GAP、不写block/release。补丁唯一来源为同名复核R1@K1K3 §3：由Implementation在 `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md` §4 AC-7行，将 `::SemverVersionPreflightTests` 后的“（4例）”按复核逐字补丁改为“（5例）”；空格和反引号按原补丁，只改该叙述计数。**不阻断诊断；本轮不应用。** 不开新复核轮、不改测试/实现/哈希/ID/disposition，不宣称已闭合。

用户本轮明确指定排在第二次诊断冒烟之后，故Implementation交接 `PAUSED_PENDING_DIAG_CLOSEOUT`，不是暂停工作项Lifecycle或取消补丁义务。诊断开始前先完成本轮文档提交/同步及必要派发核销；用户按现行页§2记录当时HEAD与干净工作树，使用同一源码快照。**从第二次诊断开始计时直到用户报告收尾完成，全仓库禁止提交（含supervisor登记/核销）、pull、切分支或修改已跟踪文件**；会话核HEAD与工作树干净。调度不得在该窗口派发写仓库角色或提前补笔误。用户收尾反馈后先核诊断已结束，再交Implementation的下一次文档提交应用补丁；诊断原件/粗账保留，不因补丁重开续试。

### 3. DIAG:RESUME:1逐项前置与本人交接

唯一额度来源为账本2026-10-07「用户答 DIAG:RESUME:1：选 A 允许一次余额续试（推荐）」；不是本轮新签。已逐项核「DIAG续试授权落实」及其原授权落实§1–4：

| 前置 | 核清结果 / 来源 |
|---|---|
| 用户明确允许结束后再试一次、已入账并落实 | 成立：上述账本A与「DIAG续试授权落实」范围一致；不是自动余额继承或无限重开。 |
| C5身份修复核对完成 | 成立：-C5-K1K3.md §0–4，退回0/1，无必需代码停点指针缺失。 |
| 新鲜独立R1@K1K3 PASS并由接受消费 | 成立：同名复核§0–5/Verdict与本节§1；当前源码治理路径未漂移。 |
| 全局消耗性门无未release block | 成立：运行仓库check_docs的完整reviews扫描和implementation-status账本release解析，未配对blocks={}、账本release={}，无遗漏按本work过滤；不新增release。 |
| 轨道与实际执行人 | 成立：本人诊断1条Consuming=yes；JET方向1条零消耗；补丁交接暂停，无其他已恢复项，Gate-echo随REVIEW_PASSED同步。角色不代跑。 |
| 现行操作页、额度覆盖与现场前置的交付 | 成立：本人照 `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` 现行版本§0–7/附录执行，**同时适用本节下面的续试覆盖口径**；其余步骤未签全链通过，现场环境/三文件/端口/共享槽仍按页§2–4由本人核，失败据实停步，不将UNKNOWN编成已齐或要求补签正式G1–G5。 |

**交用户本人执行第二次诊断冒烟，仅此一次，新建诊断目录，不续写首次目录。** 新clock-start只计本次增量；开工NOTES写旧账390s/Play0/启动0/故障重启0，本次增量与累计分列。操作页§0/1/7、elapsed显示及附录0的“3h/180min”是原总额，**本次实际新增上限为10,410s（173min30s），累计=390s+本次完整墙钟≤10,800s**，包含准备/同步/冷加载/等待/失败/Play及收尾，暂停不清零；不能照elapsed的180min分母再用完整3h。接近上限时提前停止新动作、留足安全收尾；150min不再开Play仍为收尾建议。本人可在新目录NOTES标明覆盖上限，不修改仓库操作页或已跟踪文件。

新增Play≤5，板服务/GGUF启动/加载≤3（含拒启的保守编号，含故障重启≤1，非3+1）；仅Air+同一Jetson+同三文件。原零项（5060/云/外部API/下载/安装/模型传板/新scenario/session/run ID）、身份/帧时间/控制安全/真值隔离、共享槽互斥与四类STOP保持。运行时解析路径/身份，不手抄SHA或伪造报告；现行页的诊断输入和三诊断选项必须齐，不写正式runtime/runs，不离线试数、不转用B-main额度/证据。收尾按页§7，反馈新目录路径、完整增量/累计粗账、启动/Play及释放/恢复事实；原件不进正式证据或Unity验收日志。再结束后不能随返工重开。

阶段B正式G1–G5与AC-18本轮**不签**；诊断不算任何门通过，条件题DIAG:ENV:1仍仅实际触发后转呈。当前needs_user=none；下一接手为用户本人，收尾后Implementation补CLASS_3。consumed=none。

open_items: none


## 诊断故障2裁定（2026-10-07，Acceptance）

requested.round = `诊断故障2裁定`；Dispatch-Id `P1-ENG-LOOP-002-诊断故障2裁定-20261007T223234Z-dbd6`。本轮为用户具名要求的诊断收尾归因、一次续试效力裁定与零消耗修复交接；D4 engineering-v1保持。不是D/C/R、不跑测试、不签独立finding/verdict，不SSH/复制/加载模型/碰Jetson/Unity/runtime，不改代码、诊断页、复核文件或授权账本；consumed=none。

### 1. 原件核对与DIAG-ENV-2归因

只读入口为 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/` 下本轮交接指向的第二次目录；按NOTES的累计822 s、clock-start/end及日志定位，不手抄目录名/SHA。读取 `NOTES.md`、`diag.env`、`board/serve-diag.env`、`board/closeout.txt` 与 `board/board-logs.tar`；tar只列目录/读取成员，不解包、不写回。另读该目录 `board/check.txt`、`board/expect-assets.json`、双端sha清单及起止时刻。它们仅供故障定位/粗账，原件不进正式证据或Unity验收日志。

- tar中 `run/serve-diag.sh`、`run/serve-diag.py` 与现行诊断页附录3/4代码块逐字相等；tar的env与本地 `board/serve-diag.env` 相等。env确有非空 `LLAMA_BIN`；Shell先source，再按 `LLAMA_*` 等前缀执行unset。`logs/serve-1.log`明确记录 `unset LLAMA_BIN`，随后附录4第23行 `os.environ["LLAMA_BIN"]` 抛 `KeyError`，`serve_rc=1`。异常在 `llama_preflight(args)`、`DIAG_LOAD_START`和创建子进程之前；未到模型加载，也不把本次算作preflight通过。
- 诊断输入的runtime_build为b0；check原流version_rc=0并明确build 0；双端sha清单逐字相等，支持本次版本gen/16路径同步走通的有限事实。不推出当前生产preflight、模型加载/推理、HTTP/闭环已走通，不将这些读数计作AC-16板端通过。
- closeout原流ss_rc=0/pgrep_rc=1，记PORTS_RELEASED/NO_RESIDUAL_PROCESS；clock-start/end跨度432 s。用户本轮明确已收尾，故「R1K1K3消费与诊断放行」§2仓库静止窗口现已结束。Air runtime恢复/全过程工作树无漂移不在这份closeout板端原流中证明，保留用户收尾反馈的来源上限，不追认完整执行合规。

**归因：诊断页一次性启动块的实现缺陷（DIAG-ENV-2），范围内必修；未见该故障由执行偏差造成。** 原「诊断冒烟授权落实」§2要求复用真实preflight/安全检查和前台budget=None组合，并未要求清掉诊断输入；「R4消费与诊断故障裁定」的合同读法也未规定此破坏性顺序。页中将操作输入与llama环境覆盖共用LLAMA前缀，再在读取前删除，是诊断页实现对既有链路义务的遗漏。正式操作单§4在父Shell保留路径，通过 `env -u` 作用于子环境，同时将路径先展开为CLI参数；诊断页的父Shell unset加Python环境读取组合不同，不能据正式文本反推合同要求了此故障。不是生产版本解析/模型代码缺陷，也无已证需下载/安装/新设备，DIAG:ENV:1不触发。

故障影响操作行为，性质最低CLASS_2、非CLASS_3；这是用户要求的诊断归因，**不是独立复核finding**，不写blocks/releases、不改变既有finding依据列/统计，不自行给复核记「漏检」。该页除gen修订外从未被宣称全链核对/独立复核通过。AC解释修订11/新AC0、原R4终局/冻结集闭合、新K1K3 C5/R1/返工0/2及累计实现finding5（其中CLASS_3待补1）全部保持。

### 2. 计次、旧账合并与DIAG:RESUME:1效力

按「R1K1K3消费与诊断放行」§2–3、「DIAG续试授权落实」及原诊断页§4保守编号口径，失败/拒启也计板服务启动；wrapper与子进程不重复计。本次启动未到GGUF不免计1；没有再次运行，故障重启仍0。启动日志从22:24:10Z至22:24:11Z，不替代整批432 s墙钟。

| 粗维度 | 首次旧账 | 第二次增量 | 合计已用 / 原总上限 | 仅算术余量（当前不可执行） |
|---|---|---|---|---|
| 完整墙钟（含准备/同步/等待/失败/收尾） | 390 s | 432 s | 822 / 10,800 s | 9,978 s（166 min 18 s） |
| Unity Play | 0 | 0 | 0 / 5 | 5 |
| 板服务启动编号（含拒启） | 0 | 1（rc=1；实际GGUF加载0） | 1 / 3 | 2 |
| 其中故障重启 | 0 | 0 | 0 / 1 | 1（在总启动内，非额外1次） |

第二次墙钟432≤已签新增10,410 s；其余粗维度未超签。诊断批次共2次，DIAG:RESUME:1允许的**一次续试已执行并结束，执行效力耗尽**。账本2026-10-07同名条用户展示说明逐字为「只允许再试这一次，不是每次修复都能重开」；余额数值不等于新尝试许可。不得重开第二次目录/计时、将第三次称原批故障重启，或借零Play/未加载模型自动再试。余量保留作申请基线，不能执行、不重置/转用B-main；新续试只能用户另签入账并由接受落实。本角色本轮消耗0，以上是本人已发生用量，不从正式信封扣除。

### 3. 修复闭集、先后与交付停点

交Implementation，解除 `PAUSED_PENDING_DIAG_CLOSEOUT` 的已满足收尾条件；本次派发明确要求同步该解除，不恢复任何其他PAUSED工作项。**下一次实现提交先应用K1K3-R1-1原逐字CLASS_3补丁，再在同批修诊断页**，不把补丁继续挂在未获授权的第三次诊断之后；不另开该CLASS_3复核轮。

写入闭集：① `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md` §4 AC-7行，严格按同名复核R1@K1K3 §3的4例→5例替换；② `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` §3 env生成/附录3–4与直接对应的§4说明，仅修诊断输入与llama环境清理的命名/传递冲突及该输入缺失的拒启说明；③同名前缀的零消耗修复说明/离线探针记录；④本项状态交接。原件只读、不复制进证据文件；修复记录不得把原件当门证据。

选定最小路径：Air已解析的LLAMA_BIN仍作为来源值，在诊断env中以独立 `DIAG_LLAMA_BIN` 名传递，附录4读取该诊断名；附录3仍清除继承的LLAMA/GGML/MTMD/HF/HUGGINGFACE/proxy覆盖，不能只把LLAMA_BIN泛化列入白名单或重新source全部旧环境。五项诊断输入（BOARD_DIAG、WEIGHTS、MMPROJ、DIAG_LLAMA_BIN、BOARD_TS）在使用前校验非空、加载失败/缺项有明确DIAG_FAULT与非零退出，停在生产preflight/子进程创建前；来源值不变、不编造路径或期望。保留现有显式缓存设置、三文件身份/部署摘要、十旗标、budget=None、就绪/截止、起停释放及粗计次；不改prompt/schema/decode、时间/控制安全/指标/采样/阈值。

禁止改controller/Assets/tools/tests/config、正式操作单及JET来源；不新增运行入口、第三方依赖、真实模型/回放/全套/SSH/板/Unity操作。Implementation可在已有Air环境做原页启动块的零模型离线桩探针，消费原块而非手写替代实现：旧块重现删除LLAMA_BIN/缺输入，新块诊断路径保持逐字、环境覆盖清除、缺输入拒启且不到preflight/加载；记录命令/范围/结果，不能声称真实板验证或全链通过。本接受轮不执行这些探针。

**停点为「诊断页修复交付」**：该最小修复不改变生产身份字段/协议或模型决策语义、不在本项PLAY_GOVERNING内（原冻结集只点名正式play-ops页），故不新增K停点/C/R，不向旧R4追加R5或向新K1K3硬加R2；沿原诊断授权(d)精简步骤不经C/R的通道交付。实现提交后交Acceptance只读核清闭集、补丁、输入传递和离线记录，不签独立PASS或真实板通过；只有新授权入账/落实后才可交本人执行。若必要修复越闭集或改变生产协议/语义，先报具体待裁定问题，按K触发规则重新路由，不能借此页暗修源码。原已通过生产代码Overall REVIEW_PASSED/ACTIVE保持；当前诊断页待修与执行授权阻塞分列，不撤销R1/R4。

### 4. needs_user：DIAG:RESUME:2（只能用户决定；待转呈，无执行效力）

request_id: `P1-ENG-LOOP-002:DIAG:RESUME:2`

**来源与题目**：第二次诊断因页内输入被清掉而在加载/Play前失败，已收尾；DIAG:RESUME:1的一次许可已耗尽。完成§3零消耗修复并由接受核清后，是否另行允许本人用原总上限的算术余量再做一次诊断冒烟？

- **A（推荐）：另签仅一次余额诊断。** 旧账822 s/Play0/启动1/故障重启0保留；第三次新增完整墙钟≤9,978 s、累计≤10,800 s，新增Play≤5、启动编号≤2、其中故障重启≤1（含在2内，非2+1）。第三次首次重新启动承接本次rc=1，按现页语义保守计故障重启1，之后不得再作故障重启。仅用户本人Air+同一Jetson+同三文件；新建独立诊断目录，不改/续写旧原件。准备/同步/等待/失败与收尾均计时；原零项、身份/安全/共享槽、四类STOP、budget=None、不进证据/不判门/不转用B-main保持。页面修复交付核清、新授权原话入账及接受落实后方可执行；第三次结束后本许可即耗尽，不随修复无限重开。诊断期间全仓库静止窗口照「R1K1K3消费与诊断放行」§2执行，须在新计时前完成必要文档提交/核销；本选项不授权代理代跑。
- B：诊断到此，保留两次故障和旧账；算术余量不执行、不转用，§3零消耗修复仍做。以后诊断须本人另定范围与额度；正式线仍按其原门办理，不把选择B当正式放行或关闭本工作项。

**推荐理由**：已定位为诊断页传递冲突且未到模型/Play演练，最小修复后用原余量可继续原演练目的，资源总上限不增加；但第三次改变“一次续试”的范围，只有用户可签，COORD-015 §5.2不可代拍，D5不适用。A/B整题交用户，推荐不是授权。当前阶段B正式G1–G5、Air正式原件/目标环境、现场HEAD/status/Unity日志与AC-18证据停点仍未闭，AC-14/15/18和AC-16板端NOT_RUN、无UNITY_NA/DONE。N-1全套3/3、旧失败/债/偏差/UNKNOWN、ACQ暂停保持。

### 5. 交接与轨道

裁定交接完成，原Acceptance故障行与Implementation补丁行合并为单一Implementation零消耗交接，Status=READY_DIAG_PAGE_FIX，Progress逐字含「诊断故障2裁定」；Return to=Acceptance/用户（§4待转呈）。收尾后已无获准诊断执行，不保留伪Consuming=yes行；未来用户真签并由接受落实时再按含Play动作设yes。JET方向行不变，最终0消耗性+2零消耗活跃，Gate-echo沿REVIEW_PASSED；不为新增用户题建立第三条零消耗交接。全局blocks/releases完整来源由check_docs扫描，不按本work过滤，本轮不写block/release或SCOPE_GAP。本轮consumed=none。

open_items: none


## 诊断页修复核清与RESUME2落实（2026-10-07，Acceptance）

requested.round = `诊断页修复核清与RESUME2落实`；Dispatch-Id `P1-ENG-LOOP-002-诊断页修复核清与RESUME2落实-20261007T224626Z-1d9f`。本轮是按「诊断故障2裁定」§3的只读交付核清、CLASS_3逐字补丁闭合与已入账用户A的落实；不是新D/C/R、独立复核或阶段B正式放行。D4 engineering-v1保持；本轮不跑测试/离线探针、不SSH/复制/加载模型、不碰Jetson/Unity/runtime、不改代码/诊断页/复核文件/授权账本；consumed=none。

### 1. 修复交付逐项核清与笔误闭合

完整读取本轮派发指定的修复派发登记至「诊断页修复交付」提交的diff（4路径，72+/7−），未排除状态板或修复记录；直接关联读取现行诊断页§0–7/附录0–7、同名复核R1@K1K3 §0–5/Verdict、修复记录全文、故障2裁定§1–5及原诊断授权/静止窗口。候选后至本轮开工HEAD只有账本/派发日志，三个交付文档无后续diff；独立R1@K1K3的passed_candidate运行时解析为HEAD祖先，至HEAD的PLAY_GOVERNING（含冻结集点名正式play-ops页）diff为空。

| 核清项 | 结论 | 具体依据与边界 |
|---|---|---|
| 写入闭集①–④ | 满足 | ①-idfix-k1k3.md一处计数，②诊断页§3/§4说明/附录3–4，③-diag-page-fix.md，④本项交接/Log，恰四路径；无运行时代码、正式操作单、JET来源或基础设施diff。 |
| K1K3-R1-1逐字补丁 | 满足 | 对照复核R1@K1K3 §3，完整旧文件仅将唯一的 `tests/test_llama_server_adapter.py::SemverVersionPreflightTests` 后「（4 例）」替换为「（5 例）」后与交付文件逐字相等；空格/反引号及其他字节未动。 |
| DIAG_LLAMA_BIN来源/传递 | 满足 | §3 printf的来源仍是Air resolve所得LLAMA_BIN，只改env键为DIAG_LLAMA_BIN；附录4 args.llama_bin读取同名诊断键，不改/猜路径或期望。 |
| 五项输入与载入失败拒启 | 满足 | §3逐项检查来源值，打印缺项后由操作者停步收尾（不是Air块自动exit）；附录3 source失败/BOARD_DIAG空明确DIAG_FAULT+exit97，清理后五键缺项exit97，先于Python；附录4五键校验先于ROOT使用/tools导入/preflight/Popen，缺项sys.exit(97)。生产preflight或模型创建均不到达。 |
| 附录3覆盖清理不放宽 | 满足 | 原LLAMA/GGML/MTMD/HF/HUGGINGFACE与proxy/PROXY循环逐字不变，无LLAMA_BIN白名单、无重新source旧环境；显式缓存设置保持。 |
| 其余逐字未动 | 满足 | 诊断页完整diff仅上述生成/传递/校验与对应说明；三文件身份/部署摘要、十旗标、budget=None、就绪/截止、起停释放、粗计次、prompt/schema/decode/时间/安全/指标/采样/阈值未改。 |
| 离线记录范围与限制 | 满足 | docs/evidence/P1-ENG-LOOP-002-diag-page-fix.md §1–4列原块消费方式、桩ss/pgrep/preflight和继承覆盖注入，修前KeyError/修后来源保留、清覆盖/缺项拒启、缺env/旧名env/Python直接缺项等记录；仅Air bash3.2/Python3.9桩，不含真实板、真实preflight/三文件/模型/HTTP/闭环验证。脚本/原流在会话暂存目录而非仓库，本角色未重跑或独立复算，不签独立PASS、真实板或全链通过。 |
| 页首「本页其余步骤未改」 | 满足 | 紧接具名「身份修复K1K3（2026-10-07）只改附录1 gen」的历史轮次说明，按该轮时态读取；不指本次诊断页修复。此次改动已在§3末段与修复记录§2明确标注，故不要求越闭集更正页首、不退回Implementation。页首的旧续试指针效力以本节§2替代，不解释成已签全页通过或自动续试。 |

**裁定：诊断页修复交付核清成立；K1K3-R1-1按workflow §4.4的CLASS_3逐字应用通道已闭合。** 不重分级、不改依据BC-7/AC-7、不走阻断finding红绿通道、不另开轮或伪造复核release；复核原文件不改。机械归因仍为实现错误累计5（原阻断4已闭、本条非阻断1现闭），不是新finding。DIAG-ENV-2文本修复已核，不声称真实故障已在板端消失。原R4终局/冻结集、新K1K3 C5/R1与退回/返工计数、AC解释修订11/新AC0及N-1全套3/3保持。

### 2. DIAG:RESUME:2选A落实与操作页覆盖口径

唯一额度来源是账本2026-10-07「P1-ENG-LOOP-002 — 用户答 DIAG:RESUME:2：选 A 另签一次余额诊断（推荐）（supervisor 会话代录）」用户原话及当时展示说明；已对照故障2裁定§4 A逐项相符。修复核清已在§1成立，本节落实该已签选择，不代写原话、不另签或扩大额度。DIAG:RESUME:1仍已耗尽；本次是**第三次、仅一次新许可，结束即耗尽，不随修复重开**。

| 粗维度 | 两次旧账（保留） | 第三次新增上限与读法 | 合计上限 |
|---|---|---|---|
| 完整墙钟 | 822 s | ≤9,978 s（166 min18 s）；含准备/同步/冷加载/等待/失败/Play/全部收尾，暂停不清零 | ≤10,800 s |
| Unity Play | 0 | ≤5；进入即计，失败/中止也计 | ≤5 |
| 板服务启动编号（含拒启） | 1（rc=1，实际GGUF加载0） | ≤2；wrapper与其子进程不重复计 | ≤3 |
| 其中故障重启 | 0 | ≤1，含在新增2内；**第三次首次启动接续旧rc=1，立即计故障重启1，之后不得再作故障重启** | ≤1 |

交本人照 `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` 现行版执行，**必须同时应用本节覆盖口径**：页§0/1/7、elapsed与附录0的180min/3h/启动3是原总额，不能重新用满。本次新目录NOTES先写旧账822s/Play0/启动1/故障重启0，分列本次增量和累计。新clock-start只记本次；完整墙钟直到收尾和手记完成，据实核起止跨度并报累计，不能只报服务存活时长。接近9,978s提前停新动作，预留安全收尾；原150min不再开Play仍为收尾建议，不把它当新增额度。

新独立诊断目录内附录3的本地启动编号只可1、2，参数3本次禁用（日志编号随新目录，账里另列累计第2/3次）。本地1启动即计故障重启1；若其非0异常/拒启则不得再启动，记现象收尾。只有上次正常Ctrl-C rc=0且进程退出/端口释放、墙钟仍足时，才可用第2个普通启动；它不是第二次故障重启。页§5“故障后重启再测”的许可本次已被首次启动用完，不能再用该句重开。任何调用均占启动编号，不因未到preflight/GGUF免计。

执行人仅用户本人，在Air+同一Jetson+同三文件；新建目录，不改/续写两次旧原件。只复用既有离线环境，按页现场核干净HEAD/status、三文件/部署身份、端口18081/18082和共享槽；这些仍非当前已齐事实。5060/云/外部API/下载/安装/编译/模型二进制库传板/新scenario-session-run ID/新设备/系统SSH沙箱改动仍0；原16路径纯源码同步、身份/帧时间/安全/真值隔离、budget=None及四类STOP保持，不转用B-main。不做离线评分试数、不入证据或正式Unity日志、不判AC门；DIAG:ENV:1仍仅实际触发后转呈，不新增当前用户题或预签缺件。

### 3. 静止窗口、交接与保留门

开始新计时前先完成本轮必要文档提交/推送、supervisor核销及现行源码快照同步；本人按页§2记录当时HEAD和干净工作树。**从第三次开始计时到本人报告收尾完成，全仓库禁止提交（含supervisor登记/核销）、pull、切分支或修改已跟踪文件；调度不得派发写仓库角色。** 同一源码快照贯穿准备/传板/会话；运行中的准备与代码同步计入新增墙钟。第二次静止窗口已结束不解除这次新窗口；仅本人收尾报告后才解除。

全局消耗性门使用check_docs全量reviews顺序配对与implementation-status账本release解析，未配对blocks={}、账本release={}；不按本work过滤、不新增block/release/SCOPE_GAP。交接Owner=用户本人，Status=READY_DIAG_RESUME2，Consuming=yes（有已签Play用途，本接受轮消费仍0），Progress逐字含本轮名，Return to=Acceptance（收尾核清）。JET方向行保持，最终1消耗性+1零消耗；Gate-echo仍REVIEW_PASSED，无其他暂停项恢复。具体谁执行/读哪页只在状态板交接行记一次。

收尾按页§7，反馈新目录入口、完整增量/累计粗账、每次启动/serve_rc/故障计次、Play计次，以及端口/残留/runtime恢复/工作树与收尾完成事实；原件只用于诊断故障/粗账核清，收尾交回Acceptance。若发生新问题按具名范围正常返工，不能在窗口中修源码或据剩余额度自动重开。

Overall=REVIEW_PASSED、Lifecycle=ACTIVE保持，不签独立PASS/真实板通过/UNITY_NA/DONE。阶段B正式G1–G5、Air正式原件/目标环境、现场HEAD/status/Unity日志和AC-18证据停点仍未闭；AC-14/15/18及AC-16板端NOT_RUN。原失败/偏差/UNKNOWN/OPEN债/ACQ暂停不重置。needs_user=none；本轮consumed=none。

open_items: none


## 第三次诊断核清与本人诊断落实（2026-10-07，Acceptance）

requested.round = `第三次诊断核清与本人诊断落实`；Dispatch-Id `P1-ENG-LOOP-002-第三次诊断核清与本人诊断落实-20261007T233409Z-e261`。本轮为用户点名的只读诊断收尾/计次/现象归因与已签第四次本人诊断落实，不是D/C/R，不改AC/阈值、不签独立finding或verdict。D4 engineering-v1保持；不SSH/复制/模型/测试/Jetson/Unity/runtime操作，不改代码、诊断页、复核文件或授权账本，consumed=none。

### 1. 原件、执行人及第三次收尾核清

原件入口为 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/` 中clock-start.utc等于2026-10-07T23:13:37Z的目录；目录名、源码HEAD和各sha从原文件运行时解析，不手写标识。只读NOTES、四份clock文件、prep/air-head、board/check-sandbox-denied/check/closeout/status-1/身份输入/两端摘要、receipt输出、sessions事件/结果/四张预览、segments摘要/manifest/帧记录及hold清单。board-logs.tar只在内存读成员，未解包或复制进仓库；不读真值、不评分、不产出正式证据。

执行人替换在账本同日「用户授权 Codex 代操作第三次诊断冒烟并发令开始（辅助会话代录）」内：用户要求代操作并发令开始，允许本会话Codex替代原“本人”限制；额度不新增。运行期间两项具名源码/图像指令传输确认先在NOTES记录，静止窗口结束后补入同一账本条。此前仅DIAG:RESUME:2原签“不授权代理代跑”已由此具名授权替代，不能据过时交接行判本轮执行人越权；此替换不延伸到第四次本人授权。

| 核清项 | 原件与裁定 | 限制/缺口 |
|---|---|---|
| 完整墙钟 | UTC起23:13:37Z、止23:25:50Z；epoch差733s，两种钟相符；NOTES末段称手记/收尾完成、窗口结束 | 开始/结束模板格空白，数据在clock与后加叙述；不补写旧原件，不用服务存活523s代替完整733s |
| 启动/加载与退出 | tar仅有serve-1.log；23:15:40Z起，23:24:23Z止；preflight ok、一次DIAG_LOAD_START、listening、DIAG serve_rc=0及wrapper serve_rc=0 | 日志含“Received second interrupt, terminating immediately”；不把rc0单独当全路径优雅清理证明，结合下一行释放核对；未见第二次启动 |
| 释放与日志 | closeout 23:24:45Z：ss_rc=0 / PORTS_RELEASED、pgrep_rc=1 / NO_RESIDUAL_PROCESS；回传tar可读 | 日志回传rc=0由NOTES自报，未单存该命令退出码；这是当时快照，不保证未来端口状态 |
| 身份/同步与诊断组合 | check原流三件sha与expect输入、status身份一致；air.sha=board.sha；status部署摘要=Air诊断摘要，无http_budget；版本build 0取b0；启动到模型/测量/收据 | 仅证明本次诊断发生了启动与既有修复路径未再报旧错；不是AC-16或正式目标环境/来源核清，不保证以后或全链 |
| Play/会话 | NOTES自报Play1，只有一个诊断会话及一常驻段；事件有4次ask、2次reject、2次confirm过期、stop；TERMINAL(operator_stop) | Play按钮精确起止UNKNOWN，23:19:11Z/23:24:19Z为手记命令/观察时刻；不从日志推造按钮时刻或称全程合规 |
| runtime/工作树 | NOTES自报runtime帧/真值恢复、诊断覆盖移入hold、工作树干净；hold仅overlay-diag；本轮开工git status干净 | 未保存前后runtime逐件快照/哈希及当时status原流，完整恢复同一性UNKNOWN；当前干净不补证当时无瞬时修改 |
| 静止窗口 | prep源码HEAD早于clock-start，收据/session绑定同一HEAD；当前可达git历史在733s窗口内无提交；其后仅账本/派发日志diff，最新独立通过指针至当前PLAY_GOVERNING diff为空 | NOTES报告收尾完成后才有传输确认入账/第四次授权/本次派发提交；历史不证明无未提交瞬时改动、pull或切支；未见违反窗口的已提交变更，不追认严格全过程合规 |
| 工具/操作限制 | check-sandbox-denied原流为SSH Operation not permitted；NOTES另报默认MPS不可用、真实主机MPS=True及单次授权后执行 | 归操作工具/权限环境限制；主机MPS读数和审批往返未单存完整原流，UNKNOWN；不推断依赖缺失，不授权改沙箱/SSH或提权 |

诊断标签虽在sessions/segments目录、manifest内出现session_id/run_id（段manifest还继承ACQ work_id），按原「诊断冒烟授权落实」§1及diagnostic=true读作进程/目录关联，不能变成正式注册ID、ACQ恢复或本项证据。第三次按操作者主动结束收尾；未见粗额度越界或已证真值/控制安全绕过，真值隔离操作由NOTES自报，不以本轮替代正式红线验证。

### 2. 粗账、一次效力与现象归因

对照「诊断页修复核清与RESUME2落实」§2–3和账本代操作条，第三次如下；拒启计启动、wrapper/子进程不双计，第三次首次启动接续上次rc1，按当轮覆盖计故障重启1。

| 维度 | 前两次旧账 | 第三次增量 / 已签新增上限 | 三次累计 |
|---|---|---|---|
| 完整墙钟 | 822s | 733 / 9978s | 1555s |
| Unity Play | 0 | 1 / 5 | 1 |
| 板服务启动（含拒启） | 1 | 1 / 2 | 2 |
| 其中故障重启 | 0 | 1 / 1，含在启动内 | 1 |

粗账一致、收尾核清成立（上述缺口照记）。**DIAG:RESUME:2第三次一次效力现已耗尽**：账本与上轮落实均写“结束即耗尽”，余9245s/Play4/普通启动1仅算术余量，无执行效力，不因本轮未TRACKING或后续修复重开、不转用B-main。第四次来源是独立新授权，不续用该余额。

| 现象 | 归因与具体依据 | 处置 |
|---|---|---|
| 启动修复、measure/收据 | DIAG-ENV-2本次未复现；serve日志/status、measure.stdout与k-receipt.stdout支持启动/生成；p95约2.70s只是诊断固定样本读数 | 不升级为性能门或AC通过；qualifies字段不产生验收效力，不据此调K/prompt/schema/decode |
| 首次红车误框/视野判断 | 源预览q1未见所请求红车，框在小物体；NOTES承认此前只看Unity全景。视野判断属于操作偏差；unique错误候选是模型现象，两者并列，错误根因未定 | reject事件成立；以后先看实时sensor/绑定源帧预览，不以全景或真值替代，不追认指定成功 |
| 两次出租车确认 | q2/q3原输出框与预览黄色车相符（目检，不评分）；results均stale_rejected，分别frames_late_exceeded / wall_deadline_exceeded。确认距capture墙钟约42.975/12.367s；单调钟距呈现约40.754/10.161s | `_action_confirm`在时效检查后才播种，`_check_confirmation`先核累计帧差，再累计截止及呈现10s窗。q3“立即”自报实际已超10s；归代理工具往返/目检交互延迟的操作限制，当前无代码错误拒收依据。精确耗时分项/工具耗时占比UNKNOWN；不承诺本人一定可完成，不改阈值 |
| the car唯一误框 | q4原始JSON给unique单框，预览框在画面下缘小物体；reject；输出到预览坐标一致，未见解析/画框实现错证 | 归模型候选/歧义表达现象；根因（模型/输入/提示）未定，不把“应多候选”改成新通过线，不训练/改prompt/改代码 |
| 未TRACKING、跟随/换目标/丢失 | session全部状态无TRACKING/ACQUIRING/SUSPECTED，无designation/acquire事件；常驻段1326帧LOST，观测/云台发布0 | 跟随/成功换目标/目标丢失报告未验证。初始LOST不等于丢失检测成功；出租车ask也不是已跟踪后成功换目标 |

**当前无已证必须先修复才可进行本人一次诊断的代码缺陷；不派Implementation修复。** 旧已闭5条独立finding计数保持，不把上述诊断观察另计独立finding/复判/SCOPE_GAP；若本人复现非延迟可解释的具名失败，收尾后再交Acceptance定闭集与角色，不在运行窗口中修源码。

### 3. 第四次本人授权落实与操作页覆盖

唯一额度来源为账本2026-10-07「用户另签一次本人诊断（辅助会话代录）」的题面及肯定答复；同日supervisor条仅复述同一授权，**不新增、不叠加额度**。用户“所有检查已经过了”为其陈述，不解释为全链通过、正式门关闭或免现场核查。本节落实已签第四次、仅一次本人诊断，不另索授权、不用旧算术余额。

| 维度 | 第四次新增上限 | 累计展示（旧账不洗） |
|---|---|---|
| 完整墙钟 | ≤1800s（30min），含准备/同步/冷加载/等待/失败/Play/全部收尾与手记，暂停不清零 | 原1555s另列；本次最多后累计3355s；这不是重签原10800s |
| Unity Play | ≤1，进入即计，失败/中止照计 | 原1另列；累计最多2 |
| 板服务启动（含拒启） | ≤1；wrapper和子进程不双计 | 原2另列；本次本地编号1=累计第3次 |
| 故障重启 | 0 | 原累计1保持；第三次rc0正常收尾，本次首启为新许可普通启动，不是第二次故障重启 |

照 `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` **现行版并同时应用本节覆盖**，不修改操作页：

- 页§0/1/7及附录0的180min/3h/Play5/启动3/故障重启1全为原总额展示，本次一律用1800s/Play1/启动1/故障重启0。elapsed的“/180分钟”不是本次限额；从新clock-start按秒核1800s，接近限额先停业务、预留足够收尾，不等旧150min建议。NOTES先写三次旧账与本次四维上限，分列增量/累计。
- 页§4/附录3只准新目录本地参数1；参数2、3禁用，脚本虽接受也无授权。任何调用/拒启都占本次唯一启动；正常停后也不得再起，故障后不得重启/再测。页§5“故障重启后再测”和§6下一Play句在本次均禁用；T_sess≤0/会话拒启/Play失败照计后收尾，不开第二次。
- Air/既有同一Jetson/同三文件、用户本人操作保持；辅助会话只分步指导、不代按Play/confirm/SSH启动。新建独立目录，不改/续写三次旧原件、日志或receipt；三件路径/sha与当前HEAD仍运行时解析，所有诊断输入本次新建，不能直接复用上一轮K收据来绕过身份/版本核查。
- 不重跑既有代码测试，启动前仍完整执行页§2–4所需当前工作树/身份/部署/端口与槽位检查，仅复用已有离线环境。源码闭集同步、budget=None、300s就绪与现有K/返回/确认时效算法、人工预览、控制安全/真值隔离均保持；身份不同不硬启，不看真值或评分选框。为减少代理往返，推荐本人在T3预先加载现有ops.sh，实时sensor确认对象可见，看到有效预览后本人及时confirm；未确认/误框照记reject，不能为赶时间略过目检或自动确认。
- 其余零项、四类STOP保持：5060/云/外部API/下载/安装/编译/模型二进制库传板/新设备/正式ID/系统SSH沙箱改动仍0；细HTTP/SSH/字节与板推理不单独限，但限用途/完整墙钟。STOP1按本次新上限触发；需要新资产/安全红线/本人中止按页收尾，DIAG:ENV:1仅实际触发后转呈。不转用B-main、不入正式证据/Unity日志、不判门。结束即用尽、余额作废，不自动重开。

### 4. 新静止窗口、交接与保留门

第三次窗口以NOTES收尾完成报告结束。本轮文档提交/推送、supervisor核销与源快照文档同步先完成；第四次尚未开始计时。用户开始新clock后，准备/源码传板等均在1800s内；本人按页核当时HEAD及干净status。同一源码快照贯穿本轮：**新clock-start至用户本人报告全部收尾/手记完成，全仓库禁提交（含supervisor登记/核销）、pull、切支和已跟踪文件修改，调度不得拉起写仓库角色**；安全收尾保留，原件不覆写。提供指导不解除静止窗口。

状态板唯一执行交接改Owner用户本人、Status=READY_DIAG_SELF4、Consuming=yes、Return to=Acceptance（收尾核清），Progress逐字含本轮名。收尾按页§7并报新原件入口、完整增量/累计粗账、启动/退出/故障计次、Play次数、TERMINAL、释放/runtime恢复/status以及手记完成；按钮时刻或原流缺失照记UNKNOWN，不补造。

needs_user=none：本次额度/执行人已签，无新需选择的题；下一步推荐直接按已签本人一次诊断执行，理由是上轮时效拒收与代理交互延迟相符且无已证前置代码必修。将来改阈值/代码、再试一次或添资产/设备仍须按各自规则另行处理，本节不预签。

Overall=REVIEW_PASSED、Lifecycle=ACTIVE；原R4终局/冻结集、新K1K3 C5/R1消费与计数、AC解释修订11/新AC0、N-1全套3/3、旧债/偏差/UNKNOWN/ACQ暂停均保持。本轮不签正式阶段B G1–G5/AC-18，不把真实诊断启动称板端正式验收：AC-14/15/18与AC-16板端仍NOT_RUN，无UNITY_NA/DONE。全局消耗性门由check_docs扫描完整reviews顺序配对及implementation-status账本，不按work过滤；不写block/release。最终1消耗性+1零消耗活跃、Gate-echo保持REVIEW_PASSED，其余暂停不恢复；consumed=none。

open_items: none


## 第四次诊断核清与操作流程修改路线（2026-10-07，Acceptance）

requested.round = `第四次诊断核清与操作流程修改路线`；Dispatch-Id `P1-ENG-LOOP-002-第四次诊断核清与操作流程修改路线-20261008T000237Z-3071`。本轮仅只读核清诊断和提交操作修改路线，不是D/C/R、正式证据核实或运行放行；不SSH、不启停板服务、不Play、不跑测试/模型/评分、不改代码/操作页/复核文件/授权账本。下列修订为**待用户裁定的草案**，不加入生效AC、不改变当前合同、门或主张；本轮consumed=none。

### 1. 第四次原件、分工、收尾与粗账

原件入口：`outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/` 中 `clock-start.utc` 为2026-10-07T23:45:20Z的目录（下称本次根）；目录名、源码HEAD、三文件/部署sha、诊断关联标签均从原件运行时解析，不手抄。读取NOTES、四份clock、prep/air-head与首尾status、board/check/sync/run-sync/两端sha/expect/status/closeout、receipt输出、sessions事件/结果、segments摘要；board-logs.tar仅内存读取成员，不解包/改写原件，不读真值、不做评分。

**分工依据**：账本2026-10-07「用户调整第四次诊断分工：本人Play与确认，其余Codex代操作」。该条具名覆盖上节§3的“本人SSH、辅助只指导”限制：本人Play/停止与目检后的候选确认/拒绝，Codex负责其余已签步骤；只适用本次诊断，不外推正式B-main。用户在聊天明确确认后代理提交候选0，按此分工读取，不以旧限制判代启动越权，也不把它解释为代理自动选框许可。

| 核清项 | 原件所支持的事实 | 偏差、缺口与UNKNOWN |
|---|---|---|
| 完整墙钟 | UTC 23:45:20Z→23:55:50Z；epoch相减630s，两种钟一致；NOTES末段报告手记/全部收尾完成 | 模板起止/实际格仍空，覆盖和实账写在后加叙述；不补填原件、不用服务504s或会话约290s替代完整墙钟 |
| 启动与退出 | tar仅一份serve-1.log，23:46:14Z→23:54:38Z；preflight ok、一次DIAG_LOAD_START、服务listening、两层serve_rc=0 | 正常启动1，wrapper/子进程不双计；日志含second interrupt，不据rc0单独宣称完整优雅退出，结合释放快照；未见第二次启动/故障重启 |
| 释放 | board/closeout 23:55:00Z：ss_rc=0、PORTS_RELEASED、pgrep_rc=1、NO_RESIDUAL_PROCESS；tar可读 | closeout_rc=0/日志回传rc=0由NOTES自报，未单存各命令退出流；端口读数只证明当时，不保证后续现场 |
| 来源/身份与输入 | CODE_SYNC_OK、RUN_FILES_OK；air.sha与board.sha逐字相等；诊断expect/status三sha与build相符、Air部署摘要与status一致，status无http_budget；receipt/session代码绑定等于prep/air-head | 有限诊断链事实，不能代替正式Air来源链/目标环境核清或AC-16。--version取b0，不改成源码发布号；诊断budget=None不豁免正式守账 |
| 固定样本/收据 | measure.stdout为OK、p95约2.625s，k-receipt.stdout为single_host_jetson；两份stderr空；NOTES报两命令rc0 | 仅本次诊断输入生成，不是AC-15正式收据或性能通过，qualifies不产生门效力；不据此调K/T/样本/prompt |
| Play/会话 | NOTES本人反馈Play/停止，只有一个诊断会话、一常驻段；3次ask、一条本会话confirm；TERMINAL(duration_reached) | 按钮精确起止UNKNOWN；23:49:20Z出帧观察、23:49:31Z收到反馈均非按钮时间。无本会话reject/release/confirm-lost/dismiss；不能补造完整剧本 |
| 残留命令 | session开始另记ILLEGAL_WRITER_SUSPECTED与一条外会话stop的IGNORED_FOREIGN_SESSION回执；该关联标签来自前次诊断 | 该旧请求未作为本会话stop应用，不计本轮发令成功；残留来源完整链/是否另有同时写者UNKNOWN，事件名本身不证明恶意或并发写者。不能据此声明runtime全部无残留，也不授权删锁/旧请求或清未知进程 |
| runtime与静止窗口 | 首尾air-status原流均空；hold有overlay-diag；NOTES报帧/真值仅移动且恢复、dirty_lines=0；可达git历史在630s窗口内无提交，prep源码HEAD为当前祖先 | 未留runtime前后逐件同一性快照；“未读真值/已恢复”保留操作者自报上限。首尾干净/无提交不能证明无瞬时改动、pull/切支；未发现已提交窗口违规，不追认全过程合规 |
| 准备操作 | NOTES明确额外隔离Python导入tools因-I无当前目录而失败，随后回原页权重/smoke核查；未改源码 | 属代理额外检查的调用方法偏差，非已证项目缺件；完整失败原流未单存，不据此授权装包或改环境 |

NOTES模板旧180min/Play5/启动3仅历史展示，本次覆盖明确1800s/Play1/启动1/故障重启0。按上一节及账本具名覆盖保守核计，未见粗维度越界：

| 粗维度 | 三次旧账 | 第四次增量 / 本次上限 | 四次累计 |
|---|---|---|---|
| 完整墙钟 | 1555s | 630 / 1800s | 2185s |
| Unity Play | 1 | 1 / 1 | 2 |
| 板服务启动（含拒启） | 2 | 1 / 1，普通启动 | 3 |
| 其中故障重启 | 1 | 0 / 0，含在启动内 | 1 |

**第四次已收尾，一次效力耗尽；1170s算术余量随本次结束作废，不可再执行或转用B-main。** 三次旧账与DIAG:RESUME:1/2耗尽保留。用户调整分工没有新增尝试/额度，后来的自动化方向也没有续签。NOTES已报告收尾/手记完成，第四次仓库静止窗口结束，故可进行本轮文档提交；不自动建立第五次窗口。诊断目录/manifest中的session_id/run_id仍按diagnostic=true作进程关联标签，不是正式注册ID，不恢复ACQ、不转证据。

### 2. 现象归因与主张上限

| 现象 | 原件与归因 | 本轮结论 |
|---|---|---|
| q1候选等不到 | results的query_id为q后缀、result_id为res后缀；事件有unique与result_presented。NOTES承认代理等待循环拿result_id匹配-q，后在同一Play内仅修代理等待条件 | 代理等待条件误用/呈现延迟，非已证生产服务未返回；完整等待循环与耗时分项未存，不能逐项复算工具占比；未改仓库代码，下一ask不追认q1成功 |
| q2呈现被打断 | 结果与呈现事件均在；NOTES报Preview切换打断，之后新ask取代旧候选 | 窗口/操作交互限制；没有窗口事件原流，精确切换时刻和责任分项UNKNOWN。不可把有unique结果计确认成功 |
| q3聊天确认转交后拒收 | results最后一行stale_rejected(frames_late_exceeded)，事件confirm回执detail同码、candidate_expired→IDLE；confirm受理距呈现约29.006s、距源帧capture墙钟约31.215s；此前frames_processed已到852，候选源帧697，已处理帧差155，大于诊断收据K_ret+K_conf=66 | 确认往返延迟足以解释拒收；_check_confirmation先累计帧差、后累计/呈现墙钟，未达播种。NOTES提交UTC是代理发令记录，真实受理用receipt时刻；APPLIED只表示处理该请求，不表示成功指定。不能因聊天“确认”或框目检相符追认TRACKING，也不改阈值 |
| 后续本人终端入口 | NOTES报用户未能完成直接confirm入口、代理未在Play前演练清楚 | 操作入口准备不足，非已证模型/身份门故障；提前演练按键入口应使用离线替身，不借本次余量重新Play |
| 未跟随/换目标/丢失 | session状态仅IDLE/QUERYING/AWAITING_CONFIRMATION/TERMINAL；无designation/acquire事件。段摘要1451帧均LOST，观测与云台发布0；没有建立指针或成功切换 | 跟随、成功换目标、跟踪后丢失/显式报告均未验证；初始LOST不等于成功检测丢失。三次同一出租车ask不等于换目标剧本通过 |
| 启动修复/收据 | 原版本/env故障本次未报，已实际到服务/测量/会话 | 仅诊断有限事实，不声明全链通过、板性能、四类数字或AC门；不计新独立finding、不复判/记漏检/SCOPE_GAP |

当前无已证需要改K/T或模型代码才能通过的错误拒收；新方向针对入口与验证操作，不把诊断读数用作调参或提高研究主张的理由。独立finding累计实现错误5且均已闭、原R4冻结集/终局、新K1K3 C5/R1消费及返工计数、原失败/偏差/UNKNOWN/OPEN债均保留。

### 3. 自动化路线与两份操作页逐节影响（待用户裁定）

方向唯一来源：账本2026-10-07「用户在 supervisor 会话指示修改验证操作流程：机械核对/板服务/剧本发令/结果判定改自动，确认改预览窗按键」。只授权整理路线，未授权下面冲突处生效或新资源。本方案建议同一Air程序按`核前提→准备→接受核清→部署/收据→等待用户Play→会话/预览→归档/停止服务→收尾摘要`推进；成功机械步骤不逐项问人，失败停止报告原流、原因码与已用量。**接受核清、独立复核和用户关键授权仍是状态门**，脚本不能自签或自动跨过未放行门。

| 正式play-ops节 | 改后职责/输出；保留边界 |
|---|---|
| §0.1–0.2 | 分工改为用户Play/停止与数字键/R，代理/脚本持有SSH前台子进程、收据和调度；符号、路径与发布/通过引用继续运行时解析，不硬编码身份。是否变更(k)由§6题1裁定 |
| §0.3 | 来源链逐件来源/字节/引用自动核验；缺件即停。mini→Air实际复制现为本人专属，自动复制须题2另定，只读完整性核验可自动化而不取消前提 |
| §0.4–0.6 | 一入口分阶段仍执行原SSH主连接/通道闭集与HTTP累计守账；不合并成无界长连接、不因自动化豁免health/result/失败、传输或驻留。正式与诊断模式显式分流，不从文件缺失自动退回budget=None |
| §1 | 严格双来源、最新有效passed_candidate/后续门、全局blocks/releases、HEAD/status/无_Recovery与日志提交后再核均自动记录；失败在任何依赖动作前退出，不能只echo后继续。人工接受放行事实的G4不能用“脚本成功”替代 |
| §2 | 自动执行原准备单元只读闭集与原流/rc/墙钟记录；输出给接受核清后暂停，G4未过不开收据单元。无import动态探测/补包/清未知进程 |
| §3 | 脚本生成覆盖、资产、部署摘要并核原件/逐文件同步；原runtime残留只移动、既存板根拒覆盖；部署仍16路径，桌面新工具不自动入板闭包 |
| §4 | 脚本监督SSH前台服务、正常发送中断并等待退出/核端口；断链、就绪/身份/释放失败照原STOP，故障重启0、无后台驻留，不清未知进程 |
| §5 | 自动跑生产measure→核rc/首失败→k-receipt→核0/6/8/绑定；保持3预热+32计时、收据重测0及T/K算法，不沿诊断收据放正式Play |
| §6 | 用户Play后脚本凭实际新帧启动会话/算T_sess；记录实际会话时刻，用户停止确认与Unity帧事实分列，不将出帧/TERMINAL伪称按钮时刻。无法确定精确按钮墙钟仍UNKNOWN、正式AC-14缺证，不改Unity脚本偷加时间来源 |
| §7 | B/C与P2对象/文本Play前预登记，不按模型表现或离线真值改目标/描述；派生不足2即停。几何对象名仅继承已批的预登记用途 |
| §8 | 候选仍仅看绑定源帧预览与预登记描述，由本人数字键确认/R拒绝。按题3建议取消逐ask人工可见性筛选，固定执行序列；原SKIPPED_NOT_IN_VIEW不可保留同名自动几何判定，须用户改采样后才能实施 |
| §9 | 固定P1 B→C→red→B、P2两请求、P3 Δ=0/2/4；等待当前呈现/本人选择/原截止后推进，不因错误、none或未TRACKING追加ask；观察≥15s、red跟随段≥20s按事件锚点自动计时。release只在TRACKING且当前track_id匹配时发，否则记未发/实际失败；stop到期或中止发一次。仅既定指令自动调度，不启搜索/自动重问 |
| §10 | 原3正式+全局≤2/每剧本≤1环境重试及两种原因不变；默认停止等待处置，不自动重试借余额。尝试成功/失败均共账 |
| §11 | 原流/命令回执/按键与预览绑定/各计量项机器填表；本人按钮时刻有可靠来源才写，否则UNKNOWN。最终用户反馈与自动摘要分开；不补造目检、PASS或完整恢复同一性 |
| §12 | 停Play后只移动归档、每session布局/摘要链保留；收尾调现有评分器，评分输出不回流已结束前的调度/选择；一次评分同时生成结果摘要，计入原回放次数，不另加“摘要回放” |
| §13–14/附录P | 原11码/首次主臂失败停全部、唯一S-REBUILD可继续分支、三单元/通道/传输账完整实现为自动停止和安全收尾；不能判明分支先停回接受，不自动将UNKNOWN判绿。附录P的非特权静态闭集不扩大 |

| 诊断smoke-ops节/附录 | 改后影响与隔离 |
|---|---|
| 页首/§0 | 换成新批准分工/入口，并明确已结束四次不再执行。粗上限必须来自下一次具名授权，不能沿旧3h/5Play/3启动或本次1800s重开；正式/诊断目的显式选择 |
| §1/附录0 | 机器创建独立根/时钟/粗账及手记骨架，已用旧账和本次上限分列；每批结束使一次许可失效，禁止余额自动续试 |
| §2/附录1–2 | 自动核环境/三文件/部署/端口/槽位与来源，失败停步报告；保留非特权、无下载/安装/未知清进程；不拿诊断前置当G1–G5已过 |
| §3 | 固定16源码/配置与已批诊断输入/启动块同步，字节核对自动完成；不得将新桌面UI/评分器或真值加进部署清单 |
| §4/附录3–5 | 代理/脚本持有前台服务生命周期与身份核对，诊断仍budget=None、十旗标/300s就绪/版本/env清理/有限输入保留；下轮启动/重启值仅按新签，不从页默认继承 |
| §5 | 自动生成本批诊断测量/收据输入，不入证据、不判门/调参，正式与诊断工件不能互转 |
| §6/附录6 | 三终端短命令改同一sensor/候选预览窗的数字键/R及自动调度，不切Preview或经聊天传confirm；禁止自动选框。诊断原有confirm-lost/dismiss需要本人语义判断，建议不自动执行，只记录SUSPECTED/LOST，详题5 |
| §7/附录7 | 自动停止/释放/日志保留/runtime仅移动恢复、记粗账与UNKNOWN；保留四类诊断STOP，不把正式11码的门判定套进诊断。结果只报告日志可证明的发生/未发生，诊断默认不评分、不自动调用正式analyze_play score |

预览按键规则草案：数字键与画面候选序号一一对应（沿0起）；R拒绝当前呈现结果。程序绑定**该画面**的session/epoch/query_id/result_id/源frame_id与图像字节，发令前再核当前状态/同令牌；旧窗/新epoch/无图/无候选/越界/重复键均不确认，记录原因。键盘焦点保持同窗，不调用外部Preview/聊天桥。未按键不默认确认、不随机选择、不重问；呈现挂起Δ期间不可确认；键入/实际显示/发送/回执时刻分别记录，不将真正打开窗时刻替换现有result_presented或延长截止。确认沿现有_action_confirm/_check_confirmation，K_ret/K_conf/K_pub、T_ret/T_conf/T_pub/T_hard/T_stall、累计帧差和墙钟全部不变；入口缩短人工往返**不保证**仍未过期。

诊断失败处理仍区分“停依赖步骤报告”和四类STOP：机械前置失败不进入依赖的服务/会话，不自动补前提；允许的其他安全诊断只按原页范围，不能把普通解析失败改成正式主臂失败STOP，也不能借可继续句新增一次尝试。

收尾结果应分两层：①从session/segment/publish日志客观记录是否designation、TRACKING、切换/释放、SUSPECTED/LOST/TERMINAL及有无实际命令，未播种即“未验证”；②仅正式离线评分调用既有§3.5算法判正确身份/捕获/误锁/报告比例，含NOT_EVALUABLE/NO_POSE/ZERO_DENOMINATOR类现行输出，不新增“跟随通过率”门。模型框正确、运动真的跟对或丢失报告正确不能只靠状态名/回执自证。评分与真值只在收尾评分进程，不能作在线可见性、按键默认、下一目标或定时触发输入，信息公平与失败分母保留。

### 4. 所需AC修订草案（编号稳定；未生效、不是本轮核对表）

以下来源为用户方向，按engineering §2先呈具体合同差异，待用户答复再由接受追加冻结，原文/历史不覆盖。全部复用既有AC编号，不新增AC；本轮生效修订仍累计11/新AC0。测试/工件指针是**未来证明义务**，本轮未执行、未签满足；源码与测试由实现角色准备。修订序号基于当前合同，落实前重读最新磁盘，若已占用顺延，不手改旧条。

| 草案编号 | 改前→改后读法 | 未来证明、停点与生效依赖 |
|---|---|---|
| AC-5 修订1 | 既有Δ呈现与手动CLI确认→同窗数字/R仅将本人选择提交现有入口，绑定画面与当前令牌、无默认选择/过期绕过，不重置呈现计时；原Δ/intent/帧摘要语义不变 | test: 新预览控制测试与既有language_loop检查点用例，旧窗/错令牌/重复/无图/挂起/过期各拒绝、有效键实际回执；artifact: 显示与按键绑定流；K1K3，题6 |
| AC-8 修订3 | §3.5漏斗/四表按既有可见性筛选后的受理命令→若题3选固定序列，全部受理命令仍按原12终态/意图/分母，不再人工预筛，不可事后因“不在视野”删除样本；新操作摘要只引用原评分结果与运行事件 | test: 新摘要测试、既有analyze用例；artifact: 完整计划/实际发令/拒收/缺日志与原四表一致，分母无静默减少；K4 |
| AC-9 修订1 | 原controller隔离闭集→新在线操作/预览工具同样禁止读取真值/评分/几何可见性/对象位置；仅命令预登记可以带既有intent，不能经intent选择候选或参与在线状态/控制决策 | test: 原隔离测试扩展具名在线文件与评分分离；artifact: 实际参数/输入边界；K3K4，题3/6 |
| AC-10 修订3 | 操作员逐节读输出/复制命令/看视野发令→单入口自动机械核对/服务/收据/固定剧本/收尾；成功继续仅限已放行阶段，失败非零退出/停依赖动作；按题1/2/3更新分工/来源复制/采样 | test: 新操作工具用生产入口+替身核每阶段失败/rc、严格双来源/全局blocks、SSH单元失效不回退、STOP后仅收尾；artifact: 两页§3映射与完整自动流程原流；K1K2K3K4 |
| AC-11 修订1 | 未触预览/采集/保存路径声明→明确本次新增桌面预览按键与归档调度，保留绑定源图字节、候选顺序/坐标与现行渲染输出，不改采集/帧环/Unity；LanguageWorker/CandidatesBackend/原预检及清理零删除保持 | cmd: 完整diff/冻结文件核对；artifact: 新窗至少2张人眼保真记录（题6）；K1K3 |
| AC-13 修订1 | §4.1原功能/文档闭集与旧全套证据→追加§5指定桌面工具/测试闭集，逐文件映射；不沿旧候选证据签新工具稳定。因涉及对外评分/采样路径，本路线不预准窄修免全套 | artifact: 新候选自证/相称focused/停点全套与基线失败分列；所需全套资源待题7，K1K2K3K4 |
| AC-14 修订1 | 正式3+≤2环境重试，用户目检逐字入Unity日志→保留本人Play/停止/候选决策/最终Unity PASS/FAIL/BLOCKED反馈，行为/结果由程序收尾摘要提供；不要求人工逐项验证同一机器计量或四数字，按钮时间缺证仍UNKNOWN | artifact: 新play/ledger/自动摘要与本人Unity反馈原话分开、现场HEAD/status先记录，次数/墙钟/单加载不变；题4，正式证据停点 |
| AC-15 修订2 | 人工运行生产measure/收据并判rc→脚本依生产路径按原rc/首失败/身份决定继续或停，不改固定样本、K公式、6/8/预算退出与重测0 | test: 新操作工具收据阶段替身/失败分支；artifact: 正式新收据、报告、实际守账；K1，题1 |
| AC-16 修订2 | 本人逐项核正式板身份/来源→脚本核同一实时原流/三文件/部署摘要/版本与来源闭集，不增加共享库身份、不以诊断原件替代正式；自动来源复制仅题2批准范围 | test: 生产来源/gen路径缺失/错配/非法版本失败；artifact: 来源与正式assets原流/逐字绑定；K1K3 |
| AC-18 修订1 | 正式工件→实际C→独立原评分重放与账/STOP核实→增加自动计划/按键/发令/收尾摘要与正式归档一致性检查，独立性和≤1次重放保持；不拿程序自动结论代复核/用户验收 | artifact: 原同名复核文件具名证据核实小节；PLAY_GOVERNING空diff不开新R，有diff按实际轮号；题4，正式证据停点 |

AC-1/2/3/4/6/7/12/17算法与冻结义务保持；新runner调用现有release/stop，不新发body/look_at或改变安全判据。服务监督复用已有前台启动/拒启/清理，HTTP新增请求仍全部守原AC-7及335/200总账，不改就绪/长轮询；若实现必须改部署摘要闭集、controller import或模型加载器，先给具名待裁定差异，本草案不能覆盖。

### 5. 实现闭集、停点、旧通过消费与零/消耗维度

**推荐最小实现闭集（等待用户答复、接受冻结后才交Implementation）**：

- 新增桌面 `tools/eng_loop2/play_ops.py`（统一分阶段入口、SSH前台监督/预算与STOP/剧本调度）、`tools/eng_loop2/preview_controls.py`（现有图像字节显示与本人按键提交）、`tools/eng_loop2/summarize_ops.py`（离线原流/计划/回执/账摘要；正式评分只调用原算法）。不另加服务/网络端点，不加第三方GUI依赖；现有环境能否提供同窗按键先由实现只读查明，不能“需要GUI”就装包。若不可用则报具名选择，不改成聊天桥。
- 新增 `tests/test_eng_loop2_play_ops.py`、`tests/test_eng_loop2_preview_controls.py`、`tests/test_eng_loop2_summarize_ops.py`；既有 `tests/test_loop2_isolation.py` 可追加新在线文件隔离覆盖；保留真实生产路径/现有函数，离线工具验证用替身，不手写通过收据冒称真实链。
- 两份操作页、`docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` 对应来源/资产可复制块、同名前缀新停点证据与测试输出、`runtime/README.md`（入口/日志说明）、本项状态；接受负责提案/正式设计/Unity及实现状态指针，复核文件仅复核角色写。
- `controller/`、`Assets/`、场景/规划器/检测器/prompt/parse/schema/原评分算法/部署16路径及JET来源均不在本路线代码写入闭集；新工具以既有命令/纯函数调用组合实现。不得触LanguageWorker扩排队域、偷偷加入自动confirm-lost/dismiss、引入自动选框或新搜索。必要改动先提待裁定，不因“自动化”默许。

**需一个新的操作流程合并停点，建议短名`OpsK1K2K3K4`（待合同冻结，覆盖K1/K2/K3/K4）**：K1为呈现/按键源帧与令牌/时序、收据与阶段放行；K2为自动release/stop/前台退出及安全失败调度（原控制算法不变仍须复核发令边界）；K3为本人选择与目标身份/播种入口；K4为若用户批准取消人工可见性筛选后的采样/分母及自动对外摘要。四条件自证→接受下一实际C轮→新鲜独立R；新停点以该独立短名和合同冻结的新操作范围区分原K1K2K3K4停点，轮号由实际新停点记录计，不把历史R4+1写成R5，不将身份修复R1直接延用来签新工具。若用户保留人工可见性筛选且摘要只引用原算法，K4仍检查采样保持与对外结果来源，不预豁免。无K5/发布。

原K1K2K3K4 R4终局/冻结集闭合、返工2/2与新身份K1K3 C5/R1 PASS/返工0/2消费全部保留。本轮无PLAY_GOVERNING改动，最新有效passed_candidate至开工HEAD该集合diff为空，**不开C/R**；两份历史核对/复核不升级为自动化通过。未来tools/tests及正式操作单diff非空，按workflow §4.4新停点开轮资格做全量diff、RED_LINE/双基线/上限检查；一次性返工限和冻结集不因“新工具”重置旧范围。任何新候选独立通过后接受只消费最终通过；诊断成功也不替代此流程。

正式G1–G5仍沿现操作单定义保持：G1–G3/G5未齐不启准备SSH，G4为目标环境事实由接受核清后才可启收据/Play单元；脚本只自动执行机械核对，不代签事实/权限门。操作单一变就是PLAY_GOVERNING，正式执行须从新通过候选重新固定发布引用、核原件/环境/现场HEAD/status/Unity日志，不能用原PASS搭新页；诊断原件/收据仍不得转用。AC-18正式消耗证据停点仍需实际C与独立原归档重放/账核实；无Unity验收、无UNITY_NA/DONE，AC-14/15/18与AC-16板端NOT_RUN保持。

| 阶段/维度 | 本路线效力与额度 |
|---|---|
| 本轮核清/路线与用户答复 | 零消耗no；本轮0模型/测试/回放/SSH/板/Play/API/新正式ID，不首签信封 |
| 未来本机实现、零模型focused/替身/按键事件探针 | 可列Consuming=no；仍须先冻结合同/机器/验证范围，不等于任意次数模型或数据回放许可。跟踪器相关focused沿数据根只读环境；不装包 |
| 新停点全套/真实模型与回放 | N-1全套3/3已用尽，余量0；本路线涉及对外结果/采样，不自行沿身份窄修替代全套。题7推荐先让实现只读列新候选验证清单/实际模型与回放维度，再申请用户具名额度，不预签第4次或mini执行 |
| 未来正式B-main | 原各维度已签但执行值仍0至G1–G5/新候选门齐；分工/工具不增加SSH3、服务2/故障重启0、HTTP200/推理335、Play5/时限、传输/磁盘/评分次数。脚本不能为轮询UI额外消耗板端status或越通道闭集 |
| 下一诊断/硬件试入口 | 第四次已结束、全部一次许可耗尽，任何新Play/板启动须另签；本次1170s作废，方向条无续试效力，不预设第五次额度。诊断仍独立根/budget=None/四STOP且不进证据 |
| 来源跨机复制/第三方依赖/新设备 | 现已批本人对齐用途不自动授权代理复制；题2先定执行人/源目的地/闭集，新增类别/额度另签。模型/库传板、5060/云/API/下载/安装/Unity代码变更仍0 |

### 6. needs_user：逐条冲突、推荐与只能用户定的原因

以下是待supervisor转呈的**具体合同选择**，不重复问已选“自动化四项/数字键与R/时窗不变”。每条未答继续旧合同，不按推荐实施；用户答复须发生会话逐字入账，再交Acceptance冻结上述草案。COORD-015 §5.2范围/协议/资源/用户验证红线不属supervisor代拍闭集，D7不能改人眼/阶段/信封，故不得代选。

| request_id（前缀均为P1-ENG-LOOP-002:OPS） | 方向与现行冲突/需定处 | 推荐项与理由 | 为何只能用户定 |
|---|---|---|---|
| :ACTOR:1 | 自动板服务/收据与正式§0.1的(h)(k)、B-main:USER:1/原本人前台启动限制相冲；第四次代操作授权不外推正式 | **仅改正式执行人**为代理/脚本，仍持有可见前台SSH子进程、正常停止/等待/释放，无后台驻留/故障重启；用户保留Play/停止。只免手敲命令，保留主臂失败/互斥和预算，更符合用户方向 | 原本人专属分工由用户签，本轮只获路线方向；正式硬件执行授权与分工须用户明确覆盖，不能由接受解释诊断授权为正式许可 |
| :SOURCE:2 | “来源对齐全自动”若含mini→Air复制，冲突FACT:2原“本人从mini对齐、角色不复制” | **先自动核现有Air原件完整性，缺件即停**；若确需复制再交具体源/目的地/原字节闭集，用户可授权该次代理复制。免机械检验不消除缺件/目标环境事实；不为可能缺件预签无界复制 | 来源复制执行人/目的地/新消耗类别是原关键授权边界，现方向条未给可执行复制合同，接受不能自行拓展 |
| :SAMPLING:3 | 只保留候选确认/拒绝，与§3.6/正式§8每次ask前本人目检、N-5 SKIPPED_NOT_IN_VIEW筛选及样本构成冲突 | **改为固定预登记序列全发**，取消在线可见性预筛；顺序/指令数/Δ/观察时长/对象池不改，无确认或未跟踪照记失败/未验证，所有已受理样本按原漏斗进入分母，绝不事后删除“不在视野”。不自动用几何/真值判SKIPPED_NOT_IN_VIEW；旧筛选结果分列、不得作可比性能结论。另一选项保留旧目检则用户仍须每次发令前确认可见，不满足“只做候选确认”的完整方向 | N-5采样是用户批准的协议，取消改变信息/样本/分母，涉及对外指标K4；只有用户可改，接受不得用自动脚本偷偷复刻人眼或以评分真值控制发令 |
| :UNITY:4 | “结果不靠人眼判定”与AC-14用户目检入Unity日志、AGENTS完成三证据/workflow§4.5用户Unity验证冲突可能 | **机器填写行为/计量/评分摘要，本人实际Play/停止/候选选择并对该次最终反馈PASS/FAIL/BLOCKED**，日志分列自动结果与原话；不要求本人重算四数字/逐项机械核对，但仍有真实用户验证。DONE、独立复核、现场HEAD/status不变 | AC-14用户反馈内容须本人确认这种验证形式；若要完全取消用户验证则须明确用户直接授权协调批次改AGENTS/workflow等基础设施，本工作路线不能豁免。本推荐无需改基础设施完成门 |
| :SUSPECT:5 | 诊断§6.2本人confirm-lost/dismiss由可见语义决定；“用户仅候选确认/拒绝”不涵盖该人判断；离线知道真丢失也不能反向驱动运行 | **只自动记录SUSPECTED/LOST/原显式报告，不自动confirm-lost/dismiss，也不为制造丢失新增遮挡/搜索/发令**；收尾若缺跟踪后丢失事件就写未验证，正式四数字按原算法报告。若要专门完成该人工分支另定契约，不冒充验证 | 移除诊断人工动作/自动化其判断触及已接受目标身份状态与验证范围，必须由用户选定取舍，接受不能自造自动语义确认或用评分真值回灌 |
| :PREVIEW:6 | 新键盘窗触及AC-11预览声明与workflow§4.3.2新渲染/采集管线首次冻结前≥2样帧人眼保真；“机械全自动”不能覆盖此语义红线/信息公平 | **保留一次≥2张离线样帧人眼检查**（用户或当轮发令角色，路径/确认人/外观结论入候选证据），其余原图/候选顺序/坐标/帧摘要绑定机械核验；在线只本人看源帧与预登记文本按数字/R，不展示真值/评分/几何身份提示，不延长原时窗。在线工具与离线评分器进程/输入分离 | 方向条要求把冲突交用户，语义目检是硬门，用户须确认保留此步骤；若要求取消须直接协调授权，不得以“数字键已选”自行豁免。真值隔离和信息公平本方案无放宽选项，改变将是另立范围/主张决定 |
| :VALIDATION:7 | 新工具/采样/摘要所需停点全套与N-1 3/3用尽、旧窄修替代条件冲突；运行试入口也超已耗尽第四次一次许可 | **先完成用户选择→接受冻结→实现本机零模型准备/只读验证清单，列机器/每候选次数/真实加载/回放/墙钟/磁盘后再申请新验证信封**；不现在预签全套/诊断，也不从B-main借额度。若实现能证明完全不触对外指标路径，按engineering§6另报具名窄修适用性由复核判断，不能本轮假定 | 新额度/类别或新一次诊断只能用户首签，现方向条明确不新增额度。未知清单不能先消耗再追认，supervisor无SUB信封可代批 |
| :GATE:8 | “机械核对只失败停”若被读成从准备成功直进板服务，与正式G4接受核清/明确放行及新候选四条件/C/R必经门冲突 | **自动机械部分，保留准备后的接受只读核清G4和新候选C/R门**；程序读到具名已放行状态后继续，成功不要求用户人工复核每行，但不自动签门。G1新候选、G2用户互斥+现场核、G3合同落实、G4事实核清、G5来源对齐各自独立 | 用户须确认“全自动”仅限机械执行；若要消除接受/复核必经节点，须直接授权协调批次修改基础设施，本工作项不能代改。现有G2窗口声明已答不重问，当前现场仍须核 |
| :STOP:9 | 自动收尾/继续不能直接替代正式S-REBUILD“确认非主臂才继续”的人工归因；诊断普通故障并非四类STOP，与正式首次主臂失败停全部不同 | **两模式分流、原原因码/处置不变**；不能机械证明S-REBUILD属于原允许继续闭集就停报UNKNOWN回接受，绝不自动重启/重试；诊断只停失败步骤的依赖，仍按原四STOP/一次信封收尾 | 用户已逐码批准N-3，任何把不明原因自动判可继续或重新归类诊断STOP都会改变协议/停止边界；推荐保留原签而不是新增继续权限，须用户确认自动化的保守归因路线 |

### 7. 收工交接与保持项

路线已具体化为§3逐节影响、§4十条AC修订草案、§5文件/停点/资源闭集和§6九题，尚未进入实现。状态板交接Owner改用户，Status=AWAITING_USER_OPS_DECISIONS，Progress逐字含requested.round；Return to=Acceptance（落实答复后交Implementation），Consuming=no。不新增第三条零消耗交接、不恢复暂停项，JET方向行保持，最终0消耗性+2零消耗，Gate-echo仍REVIEW_PASSED。

当前Overall=REVIEW_PASSED/Lifecycle=ACTIVE仅指既有通过范围；本轮不改核对表/AC生效计数/复核文件/blocks/releases/缺陷账本/里程碑证据。正式G1–G5、Air正式原件/目标环境、现场HEAD/status/Unity日志与AC-18未闭，AC-14/15/18和AC-16板端NOT_RUN，无UNITY_NA/DONE。第四次有限收尾/诊断现象不进证据，不改研究主张；旧负结果/用量/操作偏差/UNKNOWN/OPEN债和ACQ暂停不重置。正式设计与implementation-status仅同步现行指针/授权已耗尽事实，不增诊断验收证据。

open_items: none

## OPS九题答复落实（2026-10-07，Acceptance）

requested.round = `OPS九题答复落实`；Dispatch-Id `P1-ENG-LOOP-002-OPS九题答复落实-20261008T002357Z-d220`。**裁定：九题已答，以下十条AC修订与实现闭集追加生效；交Implementation做本机零消耗实现及验证清单，不放行运行。** 本轮是用户答复落实，不是D/C/R；不更新核对表、不签候选通过，不SSH/启动板服务/Play/测试/模型/回放，不改代码、工具、操作页、复核文件或用户原话账本。consumed=none；engineering-v1继续适用。

### 1. 四条授权的先后效力与九题闭合

唯一答复来源为 `docs/authorizations.md` 2026-10-07 下列四条supervisor代录条目，按其 `at:` 升序读取原话、题面与授权范围，不把部分答复中的“另议”读为最终未答：

1. 「用户在 supervisor 会话指示修改验证操作流程：机械核对/板服务/剧本发令/结果判定改自动，确认改预览窗按键」（at: 2026-10-08T00:01:55Z）：方向与时窗不变。
2. 「用户答 OPS 九题（部分）：确认入口改本地网页，题1/2/6/7按推荐，题3/4/5/8/9另议」（at: 2026-10-08T00:16:03Z）：**替代**确认入口，改参照LOOP-001本地按钮网页；1/2/6/7按推荐。
3. 「用户答 OPS:SAMPLING:3：不采纳「全部照发」，保留发令前人工确认」（at: 2026-10-08T00:22:40Z）：保留§3.6与N-5，网页发送/跳过；覆盖原方向的全自动ask读法。
4. 「用户答 OPS 剩余四题：UNITY:4/SUSPECT:5/GATE:8/STOP:9 按推荐」（at: 2026-10-08T00:23:35Z）：4/5/8/9已答，最终反馈入口为网页。

| OPS题尾码 | 冻结的选择与效力 | 保留边界 |
|---|---|---|
| ACTOR:1 | 正式板服务/收据执行人由本人改代理/脚本；本人仍按Unity Play/停止。 | 仅覆盖原本人专属执行人限制；可见前台SSH子进程、正常中断/等待/释放，原三单元/有限通道/守账及故障重启0保持。方向不等于现在启板。 |
| SOURCE:2 | 自动核Air现有来源原件完整性，缺件即停。 | FACT:2本人从mini对齐承诺不变；角色不跨机复制。若需要代理复制，先列原字节闭集/源目的地/额度再交用户签发。 |
| SAMPLING:3 | **不采纳全发**；网页按原剧本列下一条ask/respecify，本人凭实时预览点“发送”或“跳过（不在画面）”。 | 跳过记SKIPPED_NOT_IN_VIEW、不发请求、不成样本；N-5/分母/顺序/指令数/对象池保持。不用程序、检测器或真值替人判断可见性。 |
| UNITY:4 | 机器写计量/行为/评分摘要；本人实际Play/停止/选择，并在收尾网页点“通过/失败/受阻”提交最终反馈。 | 原话/实际按钮标签与自动摘要分列入Unity日志；反馈不自动变成DONE/门通过，不取消三证据。 |
| SUSPECT:5 | 只自动记录SUSPECTED/LOST及原显式报告，不提供或自动发confirm-lost/dismiss。 | 不新增遮挡/搜索/重问；没有跟踪后丢失即写未验证，不能用初始LOST代证。 |
| PREVIEW:6 | 网页入口沿用至少2张离线样帧人眼保真检查。 | 样帧路径/确认人/结论入新候选证据；旧LOOP-001记录不覆盖新网页。源图字节/候选顺序/坐标及公平信息保持，时窗不改。 |
| VALIDATION:7 | 实现先列机器、每候选次数、加载/回放/墙钟/磁盘等验证清单，再由用户另签新额度。 | N-1全套3/3耗尽，不预签第4次，不借B-main或耗尽诊断余额；清单未签依赖维度0。 |
| GATE:8 | 机械核对自动，准备后仍停在接受G4核清/明确放行；新候选四条件/C/R保持。 | G1–G3/G5齐才启准备单元，G4后才收据/Play；脚本不能自签接受/复核/权限门。 |
| STOP:9 | 模式分流、原原因码/处置保持；不明故障停依赖动作、报告UNKNOWN交接受，不自动重试。 | 正式首次主臂失败停全部；S-REBUILD仅机械证明属于原允许闭集才可继续下一既定剧本。诊断四类STOP保持，普通失败不改分类、不增尝试。 |

四条均不新增额度，不启用SUB、决策信封或新设备；本轮未发现需要用户另定的合同冲突，needs_user=none。未来实现若发现缺字段、闭集外改动或需新增消耗，提出具名待裁定项，不自行放宽；:VALIDATION:7是必经的后续清单/首签步骤，不是本轮未答题。

### 2. 十条AC修订的生效文本

来源为上轮§4具名草案和上述用户明确答复，按engineering §2追加，原AC及历史修订不覆盖、不删除。全部复用AC-1…18；本轮追加10条修订，累计生效修订21、新AC0；未增独立finding/归因或债务release。下列证据是**未来义务**，不是本轮已满足声明；表中的工具/测试路径以§3闭集为准。

| 编号 | 验收项（追加生效、可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-5 修订 1 | 网页按钮仅提交本人选择到原CLI/_action_confirm/_check_confirmation；落实本节下方W1–W5。Δ挂起/intent/帧摘要、K_ret/K_conf/K_pub与T_ret/T_conf/T_pub/T_hard/T_stall及累计帧差/墙钟起点不变。网页显示/刷新/点击不重置result_presented；页面计时结束只禁确认，不造candidate_expired、不默认reject或重问。 | test: `tests/test_eng_loop2_operator_web.py`；test: 既有 `tests/test_language_loop.py` 检查点生产用例（只复用不改）；artifact: 新停点证据“网页绑定与时序” | OpsK1K2K3K4（K1/K3） | 2026-10-07 |
| AC-8 修订 3 | §3.6/N-5人工可见性筛选原样。完整预登记计划逐步列实际发送/跳过/未执行/拒收与原因；仅本人点击跳过才记SKIPPED_NOT_IN_VIEW，不发ask/respecify、不成样本。已受理命令沿原epoch归属、12终态/意图/四表/分母；不得因未TRACKING、none、拒绝、过期或离线“不在视野”事后删样本。摘要仅引用原评分输出及客观事件，原NOT_EVALUABLE/NO_POSE/ZERO_DENOMINATOR等分列，无新通过率/性能门。 | test: `tests/test_eng_loop2_summarize_ops.py` 与新play_ops计划夹具；test: 既有 `tests/test_eng_loop2_analyze.py`（不改算法/用例）；artifact: 计划—回执—原四表对应表 | OpsK1K2K3K4（K4） | 2026-10-07 |
| AC-9 修订 1 | 原隔离闭集不变，在线新增play_ops/operator_web同样不得读取真值、评分产物、几何可见性/对象位置或导入原评分/几何工具；只使用实时传感器画面、会话原流及Play前冻结的文字/intent计划。B/C派生仅沿原Play前离线预登记步骤，几何结果不得决定在线发送、跳过、选框或触发时机。summarize_ops在运行收尾之后独立进程中使用原评分入口，其输出不得回流在线工具。 | test: `tests/test_loop2_isolation.py` 扩展两个在线文件及在线/离线边界；artifact: 新停点证据“输入与进程隔离” | OpsK1K2K3K4（K3/K4） | 2026-10-07 |
| AC-10 修订 3 | 单入口分阶段自动机械核对/前台服务监督/生产收据/观察计时/release/stop/归档；ask/respecify仅列下一步待本人发送/跳过，不全发。落实下方O1–O4及W1–W5；两份操作页逐节同步上轮§3路线，但所有数字键/R/同窗按键表述改网页，取消人工筛选的草案不采纳。SOURCE缺件停，原双来源/全局门/SSH三单元/有限通道/HTTP共账及STOP不变；每依赖步骤仅在前置门有具名有效放行且机械检查成功时推进。失败保留原流/rc/原因/实账并非零退出，仅做已签安全收尾。 | test: `tests/test_eng_loop2_play_ops.py`（生产入口+本地替身逐阶段正常/失败）；artifact: 两操作页映射与新停点证据“门、调度与收尾” | OpsK1K2K3K4（K1/K2/K3/K4） | 2026-10-07 |
| AC-11 修订 1 | 明确触及**桌面网页预览呈现与归档调度**，但原预览图生成/采集/帧环/保存协议/Unity代码不改。绑定原图字节/源帧摘要、候选序号/顺序/坐标及原渲染输出，网页仅显示不重绘换框、不补几何身份提示。新管线冻结/首次正式采集之前（先到者）完成一次至少2张离线样帧人眼保真核对并入新候选证据；原LanguageWorker/CandidatesBackend/_validate_candidates_source/candidates_preflight零diff，H-1…12与清理零删除保持。 | cmd: 完整候选diff及冻结文件比较（基线运行时解析）；artifact: 新停点证据“承接声明与人眼保真”（样帧路径/确认人/外观语义结论） | OpsK1K2K3K4（K1/K3） | 2026-10-07 |
| AC-13 修订 1 | 本增量功能/文档diff限§3逐路径闭集并逐文件映射AC；不得沿旧通过范围/全套替新工具自证。实现先出§5验证清单；相称零模型focused可在已冻结范围内用临时替身完成，停点全套所需真实加载/回放等未签前不跑。全套按新签每候选一次写原输出、区分基线失败/新增失败；本轮不预准窄修免全套。若提出engineering §6替代适用性，须具名diff/理由和相称验证交复核判断，不以待签或待测候选自证稳定。 | artifact: `docs/evidence/P1-ENG-LOOP-002-ops-validation-plan.md`；artifact: 新停点自证/测试输出；cmd: 完整diff逐文件核对 | OpsK1K2K3K4 | 2026-10-07 |
| AC-14 修订 1 | 正式3次+全局≤2环境重试/每剧本≤1及现行两原因保持，不自动重试。本人Play/停止、每次发令前可见性确认、候选选择/拒绝和收尾网页最终通过/失败/受阻反馈保留；机器填行为/计量/原评分摘要，不要求本人重算四数字或逐行机械检验。自动摘要与用户标签/补充文字、点击时间及对应尝试身份分列入正式工件/Unity日志，反馈缺失写未反馈，不默认通过。按钮起止缺可靠来源仍UNKNOWN，出帧/会话TERMINAL/网页反馈时间不能冒充Unity按钮时间；现场HEAD/status与日志提交再核、次数/墙钟/单加载/体积不变。 | artifact: `-play.md`、`-ledger.json`、自动操作日志/摘要；artifact: `docs/unity-test-log.md` 本次原始用户反馈（按代录权限） | 正式消耗证据停点（§4） | 2026-10-07 |
| AC-15 修订 2 | 脚本按原生产measure→退出码/首失败核实→k-receipt→0/6/8/身份绑定决定推进或停；固定3预热+32计时、T/K公式、重测0及修订1保持。不手写合格收据、不从诊断转正式；测量首失败即按原S-K/N-3停后续。 | test: `tests/test_eng_loop2_play_ops.py` 收据阶段生产命令/替身及rc0/6/8/首失败阻断；artifact: 后续正式报告/收据与实际守账原流 | OpsK1K2K3K4（K1）；真实证据后置 | 2026-10-07 |
| AC-16 修订 2 | 机械核当前正式原流/三文件sha/部署摘要/版本/来源闭集，并沿版本解析修订1、AC-7修订5的拒启语义；SOURCE只核现有Air原件，缺件停，不替本人mini对齐。正式/诊断原流与生成文档分别绑定各自输入，不增加共享库身份类别，不用旧JET/诊断材料替正式核验；全部派生身份运行时解析。 | test: `tests/test_eng_loop2_play_ops.py` 来源/gen正常及缺失/错配/非法版本拒绝；artifact: 后续正式assets/来源/逐字绑定原流 | OpsK1K2K3K4（K1/K3）；板端后置 | 2026-10-07 |
| AC-18 修订 1 | 正式归档/原四表/账/STOP独立核实增加自动计划、发送/跳过、网页选择绑定流及收尾摘要一致性检查。实际C轮只读核对后仍由独立复核角色用已通过原analyze_play对正式归档≤1次重放，除生成时刻类元字段外逐值相等，逐维度核原信封/操作单、H-2/布局绑定与完整失败分母；自动摘要/用户通过按钮不代独立结论。PLAY_GOVERNING空diff不开R，有diff按实际停点轮号；不预记历史C2/R2，不增评分/重放额度。 | artifact: `docs/reviews/P1-ENG-LOOP-002.md` 后续具名证据核实小节（仅复核角色写）；artifact: 原正式归档与操作摘要 | 正式消耗证据停点（§4） | 2026-10-07 |

#### 网页规则W1–W5（AC-5/10引用的有限闭集）

- **W1 本机载体与动作闭集**：新网页仅监听 `127.0.0.1`，Python标准库、内嵌页面/脚本/样式、无外部资源或下载；这是本次获批的桌面HTTP入口，不是新增板服务，不改变18081/18082用途或板部署闭集。参照 `docs/evidence/P1-ENG-LOOP-001-operator-web.py` 与LOOP-001 R-B5/AC-18的做法，旧载体只读、不直接启动，不继承旧预算/全部动作。页面显示当前状态/新旧数据提示、实时传感器画面、绑定源帧候选图、剩余时间/帧差、剧本下一步/实际进度与收尾摘要。按钮闭集为：当前计划ask/respecify的**发送/跳过（不在画面）**、逐候选**确认序号**、**拒绝**、安全中止的**停止会话**、收尾**通过/失败/受阻**；不提供自由改指令/Δ/intent/顺序、verify、confirm-lost、dismiss、任意路径/命令或重试按钮。release仅由runner按原计划执行；停止会话不代按Unity停止。候选恰一个符合预登记描述才本人确认该序号，零/多个符合则本人拒绝。UI与服务端都按当前CLI合法状态拒绝非法动作，TERMINAL无运行命令，backend_fatal仅状态读取/原合法stop。结果反馈仅在该次收尾摘要就绪后启用，不驱动运行或改门。
- **W2 画面与令牌绑定**：页面呈现快照携带session/状态/reason/epoch/query_id/result_id/源frame_id、候选序号及图像身份（适用的track_id/suspect_id也绑定）。候选预览须从本会话previews受限路径读，路径/源帧/query与当前result一致，字节可解码且未变；浏览器实际成功加载/解码该图后才可确认，提交时带所看图身份，服务端重读并核与当时呈现快照一致，不能把旧页面重绑到新结果。发送/跳过也绑定本次尝试/不可变计划步骤和呈现的当前状态，重复旧步骤不能推进下一步。新epoch/错session/陈旧页/图缺失损坏/未显示/越界序号/Δ挂起或状态不合法均拒绝并记录；跨文件读出不一致先禁动作，不能用后到结果替换原图。确认/拒绝/发送/release/stop通过采集候选原CLI，不手写桥文件/锁，不改controller。实时画面仅供本人决定是否发送，图像与候选窗口明示不同用途。
- **W3 原时窗的倒计时**：从会话原始 `query_unix_s` 与首次呈现时刻（现有结果信封 `issued_unix_s`，按生产写盘路径绑定）以及当前有效收据读出两截止：查询起点+T_ret+T_conf、首次呈现+T_conf，显示较早者与 `latest_frame_id−源frame_id ≤ K_ret+K_conf`。日期/时刻/帧数据缺失、非有限、回退、过期或不一致明示“不可确认”，不拿网页首次看到/图load/文件mtime补起点；实现发现原字段不足先提具名待裁定，不扩大核心改动。刷新/轮询/重绘/重新开页不续期，Δ仍会消耗查询累计时间。客户端仅提示，最终每次合法confirm仍沿现有会话帧差/墙钟/源帧身份检查；到期禁按钮、不开新ask/不默认选择/不造过期事件，也不以此UI保证确认来得及。
- **W4 防重复与未知结果**：同一计划步骤/绑定视图/动作最多一条在途提交；前后端都拒双击、多个标签页重复/并发、刷新重放、旧视图再次点击。调用前保存request_id及绑定，runner与网页共享互斥/一次提交记录，stop计时与中止按钮竞态不得发两次。超时、WRITER_BUSY或缺回执均保留原request_id/stdout/stderr/UNKNOWN，停依赖推进，不自动换id重发或重试；迟到回执只按原id核清，不借此自动恢复流程。原CLI去重/回执语义不改；APPLIED仅表示受理，只有后续designation/TRACKING/实际发布事件支持相应发生事实。未点击不默认发送、跳过、确认或拒绝；等待仍受原尝试/会话/资源截止约束。
- **W5 原流记录与本机访问**：操作日志分别记录呈现快照/源图字节身份、浏览器显示成功、点击动作/绑定/时间、实际CLI argv（无凭据）/发送/退出码/stdout/stderr/request_id/回执时间、计划步骤及跳过/未执行原因；按钮时间不冒充CLI受理或Unity按钮时间。本机网页请求不访问板端status作UI轮询，沿本地原流刷新，不制造额外板HTTP类别；只允许本机有效会话页面带服务生成nonce提交，跨来源/缺nonce/非法动作或路径拒绝，预览读路径限制在对应会话，不提供任意文件。日志随原归档保存，原件只读、账含失败/未知/中止，不把摘要成功改写为正式门绿。

#### 调度规则O1–O4（AC-10引用的有限闭集）

- **O1 顺序与前提**：沿 `核前提→准备→接受G4核清→部署/收据→等待本人Play→会话/网页→停止/归档/安全收尾→摘要/本人反馈`。准备单元只要求G1/G2/G3/G5，读齐也停止交接受；G4未明确放行不开单元2/3。严格双来源/整树干净/_Recovery/最新有效通过及后续门/全局blocks与releases配对保持，检查非0必须阻断依赖，不能只打印后继续。发布引用、候选与SHA运行时派生。
- **O2 原剧本**：P1 B→C→red→B，P2原两请求，P3 Δ=0/2/4及原对象/描述预登记保持；每ask/respecify都等待本人发送/跳过。跳过列原计划步骤并进下一既定步骤，不增加请求或按表现补样本；无点击只能等原截止/安全收尾，不自动归SKIPPED_NOT_IN_VIEW。模型none/错误/本人拒绝/未TRACKING均记实际失败或未验证，不追加ask。观察≥15s、red跟随≥20s沿原事件锚点计时；只有确认建立相应运行事实才标观察/跟随发生，否则保留未验证。release只在TRACKING且原track_id仍匹配时发，否则记未发/原因；stop到期或中止最多一次。不能用route推算可见窗、几何或评分替本人点击/触发下一指令。
- **O3 故障与停止**：正式11码、首次主臂失败停全部、S-RING原不停、S-REBUILD原唯一可继续闭集不变；不能机械证明A5非主臂分支则UNKNOWN停全部交接受，不因余额自动开连接、重启、重测、重跑或恢复。诊断只按原四类STOP与已签一次许可分流，普通失败停依赖步骤不改码；未签的新诊断拒绝启动。所有失败只允许原签且安全的中断/等待/释放/记录/移动恢复，不清未知进程/锁、不删数据、不装包。
- **O4 结果边界**：在线只记designation/TRACKING/切换/释放/SUSPECTED/LOST/TERMINAL及实际命令，不拿状态名证明跟对/身份正确。正式在Play停止和归档后由独立离线进程调用原analyze_play评分，一次调用同时生成原四表与引用它们的摘要，扣原实现回放次数，不另造“摘要回放”；诊断默认只做日志摘要、不调用正式评分、不判门。不借零模型名义读正式/旧真实归档完成未签回放。

### 3. 实现文件闭集与两份操作页覆盖

以下是**本增量**的写入闭集，替代上轮§5的待批最小建议；不重新开放原§4.1全部运行时代码。旧 `preview_controls.py` 按键工具不实施，替为 `operator_web.py`。实现可只读原生产代码/已批来源，不代表有这些路径的修改权限。

| 路径（逐文件闭集） | 本增量动作/边界 | AC |
|---|---|---|
| `tools/eng_loop2/play_ops.py` | 新增，统一分阶段入口/既有命令组合、前台SSH监督、计量/门/停止与原计划调度；在线不import真值/评分/几何，预登记只读冻结计划 | 8/9/10/14/15/16 |
| `tools/eng_loop2/operator_web.py` | 新增，标准库127.0.0.1内嵌按钮页、W1–W5；不直接写桥/调用模型、不扩动作 | 5/9/10/11/14 |
| `tools/eng_loop2/summarize_ops.py` | 新增，收尾独立离线日志/计量摘要；正式通过原CLI评分后引用原四表，不改评分算法/分母 | 8/9/14/18 |
| `tests/test_eng_loop2_play_ops.py` | 新增，生产入口+临时本地替身覆盖阶段成功/失败、门/来源/SSH失效无回退/守账/停止/人工发送跳过/观察与release时序 | 8/10/15/16 |
| `tests/test_eng_loop2_operator_web.py` | 新增，W1–W5合法/非法状态、旧页/错令牌/跨标签并发/图失败与显示门/两截止及刷新不续期/挂起/重复/UNKNOWN与迟到回执/本机访问拒绝 | 5/10/11/14 |
| `tests/test_eng_loop2_summarize_ops.py` | 新增，原计划与实际漏斗/跳过分离、失败分母保持、缺日志/未播种/初始LOST/用户未反馈、原四表引用与模式隔离 | 8/14/18 |
| `tests/test_loop2_isolation.py` | 只追加上述两个在线文件及在线/离线边界覆盖；既有隔离断言不删不放宽 | 9 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 逐节改自动步骤/本人发送跳过/网页/收尾反馈；G1–G5与原资源/STOP保持，正式采集仍后置 | 10/14/15/16/18 |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` | 对应修改网页与分工/调度/日志；页首明确四次已结束、无新许可，不从旧模板额度重开 | 10/11/14/16 |
| `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` | 只同步来源/资产可复制块及新入口引用，原字节来源/静态闭集保持，不跨机复制 | 10/16 |
| `docs/evidence/P1-ENG-LOOP-002-ops-validation-plan.md`、`docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md` 及 `docs/evidence/P1-ENG-LOOP-002-ops-*` 新测试输出/证据 | 实际清单、逐文件完整范围、四条件自证/逐AC证据/未测风险/人眼记录；未就绪如实写，不覆写旧运行原件 | 11/13及十条修订 |
| `runtime/README.md`、`docs/current-status.md` | 本机入口/日志与本项当前状态，按实现白名单更新，不写实际runtime桥/帧/锁 | 10/13 |

两份操作页、mini-ops-prep中的来源/资产可执行命令块均列入本增量冻结操作单集合，依workflow §4.4视为PLAY_GOVERNING，不能因docs路径免候选检查。上轮§3正式页逐节路线/诊断页逐节路线在不与本节冲突处保留；冲突点统一为网页替代按键窗、ask/respecify人工发送/跳过、SOURCE仅核现有Air原件、疑似只记录、最终网页反馈，禁止保留可执行的旧全发/数字键/R/聊天转交确认路线。CLI保留用于原命令入口及只读诊断后备；运行中的网页与CLI不得形成第二写者/绕过一次提交记录，失败先停止交接受。

禁止修改 `controller/`、`Assets/`、`config/`、`ProjectSettings/`、`Packages/`、Unity场景/脚本、原规划器/检测器、prompt/parse/schema/decode、`tools/language_serve.py`、`tools/language_latency.py`、`tools/eng_loop2/{__init__,llama_adapter,deploy_digest,analyze_play}.py`、其他既有测试或JET源文件/LOOP-001旧载体；原16部署路径/身份与模型二进制库保持。不加第三方依赖/服务/下载，不改自检工具/工作流基础设施。如现有CLI/字段不足以实现本合同，写具名待裁定（文件/差异/失败条件），不得将此表解释为允许改核心或添加部署件。接受负责本提案/正式设计/实现状态与Unity反馈指针，独立复核文件只由复核角色写。

### 4. 新操作范围停点与C/R、正式证据要求

冻结新合并停点短名 **`OpsK1K2K3K4`**（操作增量）：K1为画面/令牌/时间与收据、阶段门；K2为原release/stop调度与服务前台安全收尾；K3为本人候选选择/目标身份入口；K4为N-5采样保持和对外摘要/原评分引用。无K5。四项稳定条件与逐AC证据写 `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md` 的“稳定候选四条件自证”具名节，提交推送后停止依赖实现，再交接受**下一实际 `C6@OpsK1K2K3K4`**（沿本work ID已发生C1…C5连续计数；若此前新增实际C则运行时顺延）→新鲜独立 **`R1@OpsK1K2K3K4`**。本轮未开C/R；稳定条件②不能用“清单已写/待签/未测”代替。

核对只读完整候选diff/全部AC与修订/证据/直接关联代码，不跑测试/改合同/签verdict；本新范围C退回≤1，第二次照交复核带未决表。Review在一次性worktree先核四条件、相对最新有效passed_candidate的PLAY_GOVERNING非空才开轮；不足给REVIEW_BLOCKED不开轮。后续双基线/RED_LINE/全局blocks与releases/测试输出纪律及每停点返工≤2、冻结集、终局/有效D2b规则原样，返工直接回复核。旧K1K2K3K4 R4终局/冻结集闭合及返工2/2、新身份K1K3 C5/R1 PASS/返工0/2保持；新范围不能重启旧终局或借旧PASS签网页工具。上一候选/各SHA从git与复核机读行派生，不能手抄。

操作页/工具一旦改变，正式执行必须固定**新范围已独立通过且被接受消费**的候选，依原双来源机制逐门核G1–G5；只读准备产出仍交接受G4事实核清/明确放行，真实板环境未核不免。正式采集前当轮发令角色记录实际HEAD/status，按原机制登记并推送Unity日志后再核。用户操作不被脚本代按或伪造。AC-14/15/18和AC-16板端保持NOT_RUN，无UNITY_NA/DONE。

正式消耗证据仍沿原§7/AC-18的独立停点要求：收尾实现证据四条件→接受下一实际C（不预记C2）→复核在原文件具名“证据核实@OpsK1K2K3K4”节检查归档/账/STOP/摘要/用户反馈；相对当时有效通过候选PLAY_GOVERNING空diff不开新R，仅做已签≤1次零模型正式重放；非空则按实际停点/轮号开R、不得用该证据小节绕过代码复核。真实运行失败先保留事实并按原返工/授权路由，不把新摘要或按钮通过当独立证据。

### 5. 零消耗实现与后续验证信封的边界

| 阶段/维度 | 现在可做与明确后置 |
|---|---|
| 本轮Acceptance | 仅读写获批文档、自检、提交推送；0功能测试/SSH/板/Play/模型/回放/API/正式ID，consumed=none |
| 下一Implementation（Consuming=no） | 在本MacBook Air做§3代码/测试/操作页文本、本机只读来源/生产接口检查与验证清单；零模型focused/临时目录替身、已有离线样图网页保真可用现有环境，不装包、不写实际runtime、不启动旧载体/模型。可用标准库本机网页和本地假服务探针，真实板SSH/服务/请求与Unity/正式ID均0；载体不铸正式ID，夹具只用临时非正式关联标签。跟踪相关focused仍用数据根只读环境；mini可做文本/只读来源准备，不借此授权mini功能测试/模型运行。 |
| 新验证清单（VALIDATION:7） | **先列清单再首签**：每项列目的/覆盖AC、执行机/解释器、命令/套件、零模型或真实加载器及计数、数据/真实归档回放次数、每候选次数/最多候选数、墙钟/新增磁盘、预览样图来源/人眼执行人、网络/设备/Play/正式ID及未核事实。零项显式0、未知标UNKNOWN；新类型需独立说明，不拿旧静态加载数假定新全套一致。具名申请给用户，授权须发生会话入账再由接受落实；用户尚未签的各维度0。 |
| 新停点全套/真实模型/回放 | N-1已3/3，余0；真实模型加载、旧/正式归档回放及所需新增设备/额度未签0。不从B-main借测试额度；新工具涉及摘要/指标引用，本轮不预准窄修免全套。若实现提出engineering §6适用性证据，交复核判断替代是否充分；不跑第4次后补签，不把已有13基线失败改绿。 |
| 正式B-main | 既有逐维度信封/N-3不增不减，本轮只改ACTOR分工。仍SSH3/有限通道、服务2/故障重启0、推理335/非推理200共账、60MB HTTP/20MB SSH/3批、Play5/每次420s/累计2100s、session5/290s及其余完整表；新增本地UI不增加板轮询。G1–G5/新候选未齐前运行维度可执行0，SOURCE缺件不自动复制，ENV:2等条件性未签0。 |
| 新诊断/入口实跑 | 第四次与全部旧一次许可已耗尽，1170s余量作废；新诊断/Play/板启动另列独立目录、设备/完整墙钟/尝试/启动/重启等逐维度申请，不预设第五次额度。诊断budget=None/四STOP/原件不入正式证据边界保持。 |
| 其余 | 5060/云/外部模型API/GPU·h/下载/安装/模型或库传板/跨机代理复制/设置修改/Unity代码变更均0；不消费JET或LOOP-001旧额，不恢复ACQ。 |

无法完成新验证或保真时，实现提交进度/缺口与清单交接受/用户，不交“稳定候选”冒充条件齐备。最终运行形式需用户Play/停止、发送/跳过、候选确认/拒绝及最终反馈，自动化未承诺无人值守或时延/四数字通过。

### 6. 本轮交接与保持项

状态板交接Owner=Implementation、Consuming=no、Status=AWAITING_OPS_IMPLEMENTATION，Progress逐字含`OPS九题答复落实`；实现必读本节§1–5和旧§3.6/AC及追加修订，上轮§1–2诊断限制按需保留、不把草案当现行执行文本。下一输出先验证清单，代码停点证据就绪后按§4交C；新测试/验证额度只按§5申请，不自行执行板/Play。

Overall REVIEW_PASSED/Lifecycle ACTIVE保持且仅指旧通过范围；新Ops范围只是合同已冻结、尚未实现/复核。当前0消耗性+2零消耗，Gate-echo同步、不新增交接，不改最新核对表/verdict/复核文件、里程碑证据或缺陷账本/blocks/releases。正式Air原件/目标环境、G1–G5、现场HEAD/status/Unity日志、AC-18及原未运行义务保留；原负结果/诊断操作偏差/UNKNOWN/OPEN债、清理/ACQ暂停与用量不重置。正式设计/implementation-status同步本节指针，无新运行证据；本轮needs_user=none、consumed=none。

open_items: none


## OPS验证额度落实与IR裁定（2026-10-08，Acceptance）

requested.round = `OPS验证额度落实与IR裁定`；Dispatch-Id `P1-ENG-LOOP-002-OPS验证额度落实与IR裁定-20261008T014751Z-f9a9`。本节落实用户既有签发并答复实现待裁定，不开D/C/R、不改最新核对表、不签独立verdict/G4/运行通过。本轮零消耗：不SSH、启服务、Play、测试、模型加载/回放或改代码；consumed=none。

### 1. 唯一签发来源与生效边界

唯一来源为 `docs/authorizations.md`「2026-10-07 P1-ENG-LOOP-002 — 用户按申请签发 OPS 验证额度 SUB:1/SUB:2/SUB:3，SUB:2 人眼保真由用户本人看」条。已只读核对该条引用的实现提交中的 `docs/evidence/P1-ENG-LOOP-002-ops-validation-plan.md` 与磁盘清单一致；该文件§2是申请原文，§4是本次IR来源，不改写原申请/进度以冒充执行结果。用户选择“三项都按申请签 (推荐)”及“我本人看”的原话只留账本，本节转写执行合同。

三项为本次OPS验证的独立用途额度，**不是 supervisor_subdelegation 或决策信封首签**。旧N-1全套3/3、四次诊断一次许可/作废余额不恢复；B-main/N-3不增、不减、不借用。新代码仍只属IMPLEMENTED/非稳定候选，旧Overall REVIEW_PASSED不覆盖Ops工具。已签额度不证明机器/模型/链路现状已核，不放宽G1–G5、正式B-main、AC-18或安全/真值/人眼红线；正式模型身份、K/T、prompt/schema/decode、部署16路径、N-5/分母均保持。

### 2. 三项签发逐维度执行合同

request_id 前缀固定为 `P1-ENG-LOOP-002:9bac8fd0:SUB:`；下表尾码1/2/3分别对应完整request_id，彼此不得转用。成功、失败、超时、中止均计实际，启动前记占额，额度耗尽或下一步越界即停并交回，不补签后重跑。

| 维度 | SUB:1 停点全套 | SUB:2 人眼保真 | SUB:3 入口诊断 |
|---|---|---|---|
| 目的/合同 | AC-13修订1、稳定条件②；原全套原输出/基线与新增失败分列 | AC-11修订1、PREVIEW:6；至少2张离线样帧，入新候选人眼记录 | IR-OPS-5；真实前台SSH监督、中断/同会话释放、监听识别、身份/网页链路的诊断；非证据、不判门 |
| 执行机/环境 | MacBook Air系统python3，与旧N-1全套命令口径一致；不装包、不设数据根以扩加载域 | 同一Air系统python3 + 本机浏览器；operator_web fidelity只读页，127.0.0.1 | Air + 既有Host Jetson同一Orin Nano 8GB Super；复用现有解释器/资产，不新增设备 |
| 次数 | 每候选1次、最多3候选（稳定候选+至多2次返工）；开始即计，超时/失败不免费重跑 | 每候选1次、最多3；候选间网页呈现代码不变则复用同次记录并说明对应关系，不重做 | 整批1次，非每候选；失败也耗该次，不沿旧许可续试 |
| 模型加载 | 新三份工具测试/隔离追加0；既有全套部分按原清单（旧静态NanoTrack-v2真实ONNX构造2、CSRT尝试2/实例0，其余det-assoc/YOLOE/DINOv2/VLM/HF0）；**每次全套实际数UNKNOWN，按签发计入证据，不把旧静态数冒充本次实测** | 0 | 板服务启动≤1（含拒启/失败；板GGUF加载≤1），故障重启0；Unity主机YOLO加载≤1 |
| 数据/回放 | 真实归档回放0，不读旧/正式归档 | 清单所列Air第三、四次诊断现有候选预览PNG各取至少1张；只读外观样本，不评分/回放、不转原件为证据 | 真实归档回放/评分0，旧诊断原件不作本次输入或追加记录 |
| 墙钟 | 每次≤900s（15min） | 每次≤900s（15min） | 整批≤2700s（45min），含SSH、同步、冷加载、等待、Play、中止与收尾；不拆账/暂停清零 |
| 新增磁盘 | 每次证据日志≤2MB；临时目录清理 | 样图新增0B，不复制样图；必要路径/人名/结论文字记候选证据 | 板独立诊断根新增≤200MB；Air本次诊断目录≤250MB（含日志/缓存/图像/暂存及移动来的本次产物）；按十进制字节核，不只看末次du |
| 网络/SSH | 网络0；仅本机测试 | 仅127.0.0.1，本机，不访问板 | 既有SSH认证主连接≤2；板HTTP限本诊断链路，沿§4 budget=None粗账，不继承正式请求/字节限额 |
| Unity/Play/身份 | 0 / 0 / 正式ID0 | 0 / 0 / 正式ID0 | 本人Unity Play≤1；正式scenario/session/run ID0，只有diag-关联标签及独立段根 |
| 执行人 | Implementation跑停点全套 | **用户本人**看图并给外观语义结论；实现只准备只读页/待填证据，不代人眼PASS | 代理/脚本机械步骤与前台服务；**用户本人**Play/停止、发送/跳过、候选确认/拒绝与反馈 |

SUB:1命令沿清单§2：`/usr/bin/time -l python3 -m unittest discover -s tests`，输出写 `docs/evidence/P1-ENG-LOOP-002-ops-tests.log`（不带-v，仅回显摘要）；返工使用不同具名ops-*日志保留先前原输出。执行前可零消耗静态复核今日测试的真实加载路径并写清范围；UNKNOWN加载数是用户已披露并签的记录口径，不在本轮另造数值上限，不授权新增加载器/模型资产/归档读取。全套仍可能有旧13基线失败，须逐名核与新失败分列，不以签发称全套绿；新增或无法归为已知基线的失败先修复，不能交明显失败的中间候选。

SUB:2用清单§2点名的两次原诊断目录定位现有PNG，逐张运行时记录路径、字节sha与浏览器解码呈现，再由本人核与原图/运行时外观语义一致、候选序号/坐标/顺序未变。不得用合成图、自动sha相等、旧LOOP-001保真或代理视觉结论代替。原PNG不复制进证据；仅人眼记录入 `-OpsK1K2K3K4-handoff.md`「承接声明与人眼保真」，含确认人=用户本人、实际结论及对应候选呈现代码。本人未看/未答则NOT_RUN、停止交稳定候选；看图失败先修并在剩余额度内重核。

其余维度：5060、云/外部模型API、另列GPU·h、下载、pip/安装/编译、模型或库传板、跨机代理复制、系统/SSH/沙箱设置修改、Unity代码变更、新scenario/run ID均0；SUB:1/2板/Play/正式ID0。SUB:3非模型源码同步及本诊断输入只按§4闭集、墙钟/两端磁盘执行；不含模型/二进制/库/轮子或跨机取证。未列的新类别/新增额度仍回用户。

### 3. IR-OPS-1…6逐项裁定与追加AC

| IR | 裁定及写入位置/失败读法 |
|---|---|
| IR-OPS-1 | **采纳**。未来Acceptance核清该次正式prep原流、原签上限与全部必需环境事实并明确放行时，只在本提案追加的具名“G4准备核清与放行”节写独立行 `g4_release: <prep.stdout的64位小写sha256>`；可带列表记号/反引号，工具从固定发布引用取。该值运行时求、不手抄，无成功G4核清不得写、实现不得自签。匹配只证明该原流已获G4，不代G1/G2/G3/G5/当前候选与现场再核；准备读齐仍停交接受。本轮仅定格式，**没有实际g4_release放行行**。缺行、原流不匹配或读取失败→S-PRECHECK，不开收据/Play单元。 |
| IR-OPS-2 | **采纳**。未来当轮发令角色在文档检出的 `docs/unity-test-log.md` 本次正式运行条目写独立行 `release_raw_sha256=<登记的第1节原流文件64位小写sha256>`，同时保留原流路径、实际HEAD/status与场景/配置等原要求；提交推送后工具从固定发布引用核此行。执行检出重跑1.1–1.4与登记原文件对应段逐行相同才继续；缺登记/不一致/读取失败→S-PRECHECK回接受。不能用本合同格式示例、摘要/计划值或旧条目代现场登记；诊断不写正式Unity条目/该标记。 |
| IR-OPS-3 | **确认保持实现的fail-closed**：目前没有已冻结且可机械证明A5“非主臂帧/发布段限制”的事件组合，TERMINAL(rebuild_limit)一律S-REBUILD并标UNKNOWN、停全部后续，安全收尾交接受。不增造证明字段，不以reason字符串/主观判断/余额续下一剧本。原唯一允许继续分支保留为条件合同，但本新入口不可用，未来证明判据需具名待裁定与相应停点。S-RING原不停不受此解释改变。 |
| IR-OPS-4 | **确认新入口下环境性重试不可用**：本批不增加显式CLI参数、网页重试按钮或同单元重试路径。Unity未进Play/运行时锁冲突保留原流与失败/实账，单元收尾交用户/接受，不开下一单元或用人工CLI绕新入口。原全局≤2/每剧本≤1只是已签上限，不是必须用完或故障自动恢复许可；余额不作废、不移用，欲启新路径先具名待裁定。主臂失败/HTTP不可达不改成环境性原因。SUB:3本来就是Play≤1/故障重启0，不适用正式重试。 |
| IR-OPS-5 | **采纳按模式独立路由，替代诊断一律拒启的现状**；完整合同见本节§4。未落实合同/未核已签来源/不满足§5代码停点前提仍拒启，不由本裁定让当前旧工具即刻执行。 |
| IR-OPS-6 | **采纳分支与原流锚点读法**：NO_CANDIDATE、NO_DECISION、本人SKIPPED_NOT_IN_VIEW不启动观察窗，直接列下一既定步骤待本人发送/跳过，不自动发/补样本；NO_DECISION只结束页面选择步骤，不造reject/过期事件，失败样本仍入原分母。仅confirm/reject受理后观察≥15s，锚点是对应request_id的会话receipt写盘时刻；红车跟随≥20s从该选择后首次TRACKING状态事件起，未进入则从选择时刻等待并记跟随未验证。缺可绑定的原流/时间→UNKNOWN停依赖；**不采纳CLI返回/网页点击时刻或轮询发现时刻作为原流时刻的补值**。拒绝/未播种/旧epoch的TRACKING不能冒充新指定已跟随；release仍要求该步建立的原track_id匹配。 |

以下由上述实现待裁定来源解释既有AC与已签用途，按engineering§2追加，原文不删改；不是C轮读码新增义务。本轮追加3条修订，累计24条修订、新AC0；不新增finding或债务release。

| 编号 | 验收项（追加生效） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 4 | 解释修订3/W/O与IR-OPS-1…6：落实本节§3机读登记/G4、S-REBUILD未知停全部、无新重试路径、原流观察锚点及§4诊断独立路由。两操作页和mini来源块引用按§4同步，不允许格式示例自签门或正式/诊断混根混账；前台生命周期/安全收尾不变。 | test: `tests/test_eng_loop2_play_ops.py`与`tests/test_eng_loop2_operator_web.py`生产入口替身/失败闭合；artifact: 新停点“门、调度与收尾”及两页映射 | OpsK1K2K3K4 | 2026-10-08 |
| AC-14 修订 2 | 解释修订1与IR-OPS-4：原环境重试上限保留但本新入口无可用重试动作，失败停依赖/收尾交回，不自动或手工旁路续试；SUB:3仅本节§2/4独立一次、本人操作和粗账，不转正式证据/门。 | test: `tests/test_eng_loop2_play_ops.py`模式与次数/失败路径；artifact: 新停点模式隔离自证；诊断实账仅留诊断根 | OpsK1K2K3K4；正式证据仍后置 | 2026-10-08 |
| AC-16 修订 3 | 解释修订2与IR-OPS-5：诊断资产期望、报告/K输入、status/代码摘要分别核本次原流并只留独立诊断根；严格复用原诊断页版本/env/preflight/身份检查，不写正式assets/收据，不把budget=None变正式服务；正式仍核原G1–G5与守账链。 | test: `tests/test_eng_loop2_play_ops.py`诊断来源/启动块/身份及拒启替身；artifact: 新停点“输入与进程隔离” | OpsK1K2K3K4（K1/K3） | 2026-10-08 |

### 4. IR-OPS-5新工具诊断模式合同（SUB:3执行前提）

本节是「OPS九题答复落实」§3文件闭集内的模式组合解释，不扩大核心/部署写权限。实现只改该节已点名三个桌面工具、新三份测试/只追加隔离测试、三份操作页、runtime/README与ops-*证据/状态；不得改controller/Assets/config/语言服务/测量/评分源码或JET/LOOP-001旧件。诊断页由实现同步页首“现行SUB:3”及适用步骤，原3h/5Play/3启动/1重启与旧T3/附录6均仅历史、不能成为新工具的可执行入口。

1. **显式模式与根。** `play_ops --mode diagnostic`须命中本次完整request_id/账本条目并显示“诊断；不进证据链；不作任何门判定”，独立于formal阶段/ledger/ID。Air本次根在 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/<运行时UTC>/`，板本次根在 `/home/jetson/eng-loop2-diag/<同一批次标签>/`，均必须新建且不存在、不覆盖旧目录/正式 `/home/jetson/eng-loop2` / JET根。标签/SHA/HEAD从运行时来源解析。本次 `controller.language_loop run`列齐 `--diagnostic`、`diag-`关联标签、独立 `--session-root`与`--diagnostics-root`；无正式session登记/新run ID、段不进正式runtime/runs；runtime传感器槽仍互斥，残留只移入hold、安全收尾归位，不删未知锁/进程或源数据。
2. **现场核与源码同步。** 保留诊断页§2的Air现有环境/资产/smoke/干净树/无_Recovery及板三文件/版本/端口/共享槽只读核；当前链路UNKNOWN须在本次内实测，不回用旧mini/第四次当当前事实。期望三文件来自本项precheck的Mac mini R02原流，版本由诊断页附录1同生产语义解析；部署摘要由Air当前源码重算。只同步现有部署manifest的16个纯源码/config及清单自身（已包含在16中），另将该页附录1/3/4/5所需本次诊断输入/启动块放在独立run/，不是新部署路径。禁止模型/GGUF/mmproj/二进制/共享库/轮子传输，不跨机取C2原件。所有内容占两端磁盘和完整墙钟，不借正式20MB/三批余额。
3. **服务启动块唯一来源。** 运行时按诊断页现有标题前缀原样提取附录3 `serve-diag.sh`、附录4 `serve-diag.py`，经可见SSH前台执行；本次只许启动编号1，不能执行历史编号2/3。实现仅可在附录3同步SUB:3编号1限制/提示与新调用位置，不改附录4生产函数组合、十旗标/300s/0.25s/long_poll/退出清理；env载入后按原规则清LLAMA/GGML/MTMD/HF/HUGGINGFACE/proxy继承变量，保留DIAG_LLAMA_BIN独立传递和五个输入非空检查。不得复用正式第4节强制HttpBudgetLedger的启动块或设巨额上限。仍复用llama_preflight、llama_server_command、_wait_llama_ready(budget=None)、SingleFlightRuntime、build_server(budget=None,long_poll=True)，不调用_main_llama/不猴补丁/不设后台持久服务。监听只接受本次DIAG行；/status核六键身份/部署摘要并确认无http_budget，复用附录5判据；错接正式服务拒绝。Ctrl-C/退出须关闭HTTP/llama子进程、清本次临时图像、记录serve_rc与端口/残留释放原流。
4. **两连接与一次加载。** 主连接尝试前即扣次，成功/失败均≤2，最多一个准备用途主连接、一个前台服务/释放/回传主连接；通道可在存活主连接上复用，连接失效不得隐式直连或自动第三次认证。服务启动含拒启占1，故障重启0；测量与Play必须共用这一次服务驻留，不能按正式receipt/play阶段各起一次。前台 `ssh -tt`/交互bash由代理/脚本监督，保留原输入/输出、中断和**同一会话**释放核对；服务已退出再关通道/主连接。连接断开或无法核安全释放，记UNKNOWN/必要STOP3交回，不杀未知进程、不重开服务。日志回传与收尾也在≤2连接内，不预留无额度的新收尾认证。
5. **诊断输入与网页。** 诊断页§5的生产measure/k-receipt最多各一次（固定3预热+32计时、measure非0不跑k-receipt，非合格不进依赖会话），只留本次诊断根、不重测、不手造输入。板服务budget=None，Air用新HttpAdapter无正式预算快照，HTTP/推理条数与字节不单独设正式细限，仍受用途/45min/磁盘以及原16次result/软硬截止算法约束；另列GPU·h=0不否定已签这一次板GGUF诊断推理。原收据身份/帧时间/安全检查不可绕过。只用一轮Unity Play/一会话/一次YOLO加载演练原冻结计划中的一个既定剧本，开跑前本人选择P1/P2/P3之一并冻结，不按表现换脚本/补样本/开第二Play；未执行项原样记未执行，不要求正式三剧本完成数。网页W1–W5/O2/本人发送跳过、确认拒绝、疑似只记录与单写者保持；无自由改指令/阈值/Δ/对象池，无自动重问/选框/重试。到期只原合法stop/release与安全收尾，用户本人停Unity。
6. **粗账文件及磁盘/截止。** 新工具在本次诊断根写 `ops-diagnostic-ledger.json`（用途说明+request_id、开始/结束UTC/epoch、完整elapsed、主连接尝试、服务启动/重启与GGUF加载、本人Play起止/YOLO加载、两端字节峰值/读取来源、STOP类/故障/UNKNOWN/收尾释放；字段具体实现留ops-*证据映射，缺实测值写UNKNOWN不能默认0）。`ops-events.jsonl`/`ops-web.jsonl`/NOTES与子进程原stdout/stderr同根保留。每个受限动作之前查额/先记占额；壁钟从本批准备开始到最后收尾，等待/暂停不中断。准备/同步/缓存预估与现场du/df、Play期间两端轮询读数和末次读数一起记，峰值按实际核；新动作须预留安全停止/释放时间和磁盘余量，监测将达上限即停业务收尾，不能以只看末次体积守250/200MB。Unity按钮时刻只来自本人可靠记录，f₀/末帧/网页时间不替代；UNKNOWN由本人补事实、不伪造。安全收尾实际越界需明确记录偏差，不能追认额度扩大。
7. **四类STOP与普通故障分流。** STOP1=下一动作越§2任一已签维度或0项；STOP2=需下载/安装/编译/新设备或模型/库传板；STOP3=真值泄漏、身份/时间/控制安全旁路、失控或冲突不能安全解除；STOP4=用户决定停。四类沿旧类别但上限只取本次SUB:3，立即停止依赖/新增业务并安全收尾。普通缺库/HTTP/解析/收据/启动错误/UNKNOWN记 `DIAG_FAULT`与原rc，**不套正式11码/N-3、不把故障本身改成STOP**；仅可继续同一次、剩余额度内且不依赖失败结果的已冻结安全只读诊断/记录/释放，不继续无有效身份/收据的Play、不重启/重测/新连接或新Play。诊断失败出口非0并如实列未执行；必要修复走正常实现待裁定/停点，不在诊断窗口改源码。
8. **收尾/证据边界。** 停会话→本人停Play→Ctrl-C/等待服务退出→同会话端口/本次进程释放核→有限日志回传→仅移动本次runtime产物并还原hold→结束计时/粗账。仅 `summarize_ops --mode diagnostic` 独立进程读本次会话/操作原流，禁止读取真值/原四表、禁止调用评分或正式重放，不把用户反馈判门。诊断原件/报告/K输入不进docs/evidence、正式assets/receipt/ledger/four-numbers/Unity验收日志，不能写G4放行或AC-14/15/16/18已满足。后续可在进度中指向诊断根说明故障/未核风险，不能以诊断读数作为停点或正式通过证据。结束或失败即该次用尽，未用子维度不续试/不转正式，超限/缺件/闭集外改动具名交回接受或用户。

### 5. 执行顺序、停点与交接

1. **Implementation先本机落实IR。** 必读本节§1–4、上节「OPS九题答复落实」§1–5、清单§2/4与进度§1–5，在原逐文件闭集内做IR代码/测试/操作页修改；focused只跑相称零消耗替身，跟踪相关用数据根已有只读环境。补模式隔离、额度/拒启/UNKNOWN/原流锚点证据；不SSH/启板/Play，不借SUB:3先实跑。
2. **SUB:1/2就绪才交稳定候选。** 代码/操作页完成后按SUB:1每候选一次全套；准备SUB:2只读样图网页，**等待用户本人看图与结论**。实现把用户本人实际反馈/结论按本合同记入候选证据并注明来源；需入用户原话账本或Unity日志的部分转有权限角色代录，实现对两文件仍只读，不自给人眼通过。两项未完成则提交进度/缺口，Owner如实转本人看图或接受处理，不写四条件满足。新加载数UNKNOWN/基线失败/实际限额分列、真实板监督未验证风险保留。
3. **代码先过OpsK1K2K3K4。** 稳定自证四条件及全部AC/修订指针写 `-OpsK1K2K3K4-handoff.md` 具名小节，包含本轮三条修订和模式隔离；提交推送、停止依赖动作，交下一实际C6@OpsK1K2K3K4（若已新发生C则顺延）→新鲜独立R1@OpsK1K2K3K4。C退回≤1/Review返工≤2与冻结/终局/blocks规则保持。本轮不消费新verdict；旧R4终局与新K1K3 R1范围/计数不重置。SUB:3只有一次，按engineering§4先让所依赖代码过C/R并由接受消费，不用诊断结果补代码停点证据。
4. **随后SUB:3独立一次诊断。** 操作页/模式合同已实现、代码独立通过且消费、全局消耗性block无未release、安全共享槽就绪后，切消耗性交接（Consuming=yes）并固定对应通过代码；代理/脚本按§4前台执行，**用户本人Play/停止/发送跳过/候选选择**。候选之后有PLAY_GOVERNING变化先重新按原资格处理，不偷偷在等待本人窗口改页/代码。本次诊断与正式G4/Unity登记分开，不要求先得到正式G4，也不能用诊断生成G4；故障/额度归因交回接受，本次不自动接正式B-main。
5. **正式采集仍后置。** 三项签发没有取消G1–G5/现场HEAD/status/登记推送后再核/AC-18证据停点，正式准备用途仍按原单元映射，G4真实核清后才另行正式收据/Play。缺事实/新类别/修改范围/超额回用户；未经新代码独立通过与现场门齐不消费正式余额。

当前交接Owner=Implementation，Consuming=no（下一步代码与SUB:1/2停点准备/验证，不产生正式ID/Play/API）；Status=AWAITING_OPS_IR_IMPLEMENTATION，Progress逐字含OPS验证额度落实与IR裁定。暂无需要用户再裁的合同项，needs_user=none；SUB:2本人看图和SUB:3本人Play是已签操作义务，后续到点交本人执行，不当作已完成。当前0消耗性+2零消耗；Overall REVIEW_PASSED/Lifecycle ACTIVE只保持旧范围，Ops全套/本人保真/C/R尚未执行。原未运行AC/旧债/偏差/UNKNOWN与ACQ暂停保持，不改核对表、复核/设计复核文件、账本或blocks/releases；正式设计及implementation-status同步本节指针，不产新运行或里程碑证据。

open_items: none


## OPS基线与IR78裁定（2026-10-08，Acceptance）

requested.round = `OPS基线与IR78裁定`；Dispatch-Id `P1-ENG-LOOP-002-OPS基线与IR78裁定-20261008T034116Z-d407`。本轮答复实现待裁定与判读已产证据，不开D/C/R、不改最新核对表、不签独立verdict或运行放行。owner=Acceptance，写入范围限本提案、正式设计、implementation-status与状态板；consumed=none，不运行测试、SSH、板服务或Play，不修改代码、操作页、用户原话账本或原测试输出。

### 1. SUB:1环境基线与稳定条件②

**裁定：接受交接§4.1点名的12项为本次Ops停点的当前环境基线；本次SUB:1满足稳定条件②的相称测试要求。** 依据是完整读取 `docs/evidence/P1-ENG-LOOP-002-ops-tests.log` 与N-1的 `-tests.log`、`-tests-stable.log`、`-tests-rework1.log`，以及 `-OpsK1K2K3K4-handoff.md` §1–4.1、原focused日志。只接受这个闭集及下列限制，不把相对N-1新出现的失败改写为N-1已有，也不称全套通过或预签后续改动测试满足。

| 闭集/数量 | 接受读法与证据限制 |
|---|---|
| N-1 13项 | 三份日志均4 failure+9 error；六项在本次仍失败，原七项不再出现在失败列表不代表已修。CSRT因缺cv2未执行，五项导入错误消失的具体原因未核。保留旧日志、覆盖限制和加载数，不回改历史。 |
| 缺numpy/cv2 10项 | 本次原traceback逐项支持交接§4.1的8个导入ERROR和2个用例ERROR。**N-1原日志实际为uv CPython 3.12.13及计数包装器，本次为Homebrew CPython 3.14.6直接discover**；“同口径”只指全套用途，不能写同解释器/同依赖/同测试覆盖。缺库导致部分旧模块未执行，不能从2430相对旧2275/2336/2300的总数推断覆盖增加。用户签的是当前Air系统python3且安装0，本次按该签执行，不需为本停点恢复旧环境。 |
| JET回环2项 | 本次全套原文分别为 `test_eng_jet_relay.LoopbackTwoProcess.test_atomic_publish_order` 的 `18 != 25`，`test_eng_jet_track_responder.LoopbackTrackWithDrop.test_analyze_track_return_and_disconnect` 的 `0 != 1`。实现在交接§4.1报告派发base一次性worktree复现同类失败。接受只读核得两测试及 `tools/eng_jet/`、`controller/` 自Ops起点至本轮检出零diff，直接导入不走Ops工具；测试有固定回放/进程墙钟。足以作为本Ops停点的非本增量阻断基线携带；**base复跑原输出未随交接入仓，本轮未独立复跑，具体负载/计时根因仍UNKNOWN**，不能把“负载约4”称已证实原因或签JET链路通过。 |

本次结果仍为2430例、5 failure/13 error/54 skipped、rc=1；当前18项失败=旧六项+新环境十项+回环两项。Ops四模块以及交接点名的language_loop/analyze模块在这次全套失败列表中无失败，结合既有focused和§1–3映射，支持本次范围内相称验证。全套690.07s/日志44,896B在SUB:1上限内；实际模型加载数UNKNOWN按已签口径携带，不以静态构造数当实测。不外推真实板前台中断、模型/链路/Unity或全部旧断言满足。

SUB:1本候选1/1已用，**不得在同一候选重跑**；本裁定不要求安装/换环境或补第二次全套，无需用户另签。本次测试对应代码由交接页首/§4及git运行时解析；后续IR窄修不能直接借本结论称其测试已过，验证路径见§5。若出现闭集外失败、Ops相关失败或无法归因的新失败，先停并交接受；安装、额外同候选重跑或耗尽后的全套均须用户新签，不以改文档凑候选续额。

### 2. IR-OPS-7：接受消费的机读绑定

**采纳**交接§6格式。仅未来接受角色核实新范围 `R1@OpsK1K2K3K4`（或其实际最终通过轮）且完成消费裁定时，在本提案追加的具名「OpsK1K2K3K4通过消费与SUB:3放行」节写独立机读行，格式为 `sub3_release: <该有效passed_candidate的40位小写SHA>`；可带列表记号/反引号。数值必须由当轮发布引用的同名复核文件最新有效通过轮机读行**运行时解析、程序写入**，不手抄候选、不得引用旧K1K3/旧R4通过轮自签Ops消费。实现/脚本不得写本提案或自签此标记。

诊断工具从固定发布引用读提案，只认可该行值与门核得到的最新有效passed_candidate一致；读取失败、缺行或不匹配均DIAG_REFUSED/非0、不开任何受限动作。HEAD对应通过代码、PLAY_GOVERNING空diff、最新轮有效通过、全局blocks/releases、账本SUB:3一次有效性及现场共享槽安全核仍须分别满足；一行匹配不替其他门，也不转正式G4。合同格式示例不是放行行。**本轮没有实际sub3_release行，未消费Ops verdict，SUB:3仍未放行。** 实现只把“IR-OPS-7待裁定”文案同步为此现行读法，沿既有替身覆盖缺行/错值/读取失败及合法匹配，不扩动作或额度。

### 3. IR-OPS-8：输出忽略的归属与最小修复

**裁定：`.gitignore`是本仓库生成产物的版本管理配置，不在AGENTS.md/workflow§7/角色细则的工作流基础设施闭集内。** 已只读核 `tools/check_role_writes.py` 的INFRA_PATTERNS与ROLE_RULES：implementation采用allow `*` 加deny，`.gitignore`未被保护/禁止；acceptance无该路径写权。本轮不修改它，交Implementation执行，不需用户协调批次。

源事实为现 `.gitignore`有 `/outputs/eng-loop/` 而无 `/outputs/eng-loop2/`，`play_ops.DEFAULT_OUT`为后者，release_gate在整树干净核前创建release子目录；故正式流程会因自身输出自挡。采纳最小方案：**本增量逐文件写入闭集仅追加 `.gitignore`，且该文件只允许新增独立行 `/outputs/eng-loop2/`及相邻用途注释**。这是IR-OPS-8驱动的AC-10实施路径补齐，不是开放基础设施/任意配置修改，也不改正式根、诊断根、部署闭集、整树干净判据或预算。不得添加泛化 `/outputs/`、忽略源码/证据/配置，或对status过滤脏文件来绕门；其他现行忽略规则不删不改。

实现将这一行放入完整候选diff与逐文件证据；用临时git替身和 `git check-ignore`/`git status --porcelain` 核正式输出受忽略、无关未跟踪路径及已跟踪改动仍报dirty。既有 `tests/test_eng_loop2_play_ops.py` 可补相称回归，临时输出不写正式runtime、不启正式流程。操作页“已忽略”的声明待该修复验证才成为候选事实。PLAY_GOVERNING唯一定义保持，不自行把`.gitignore`改称操作单或改workflow/自检工具。

上述IR-OPS-7/8源于实现交接§6，按engineering§2追加解释既有AC；不是C轮读码新义务。以下追加1条修订，累计25条修订、新AC0；不新增finding或债务release。

| 编号 | 验收项（追加生效） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 5 | 解释修订4/O1与「OPS验证额度落实与IR裁定」§5.4：SUB:3接受消费按本节§2的机读绑定及拒启语义；正式输出根沿本节§3精确忽略而保留整树干净核，`.gitignore`写入只限具名一行/注释。旧G1–G5、双来源、安全收尾、模式隔离及诊断一次额度保持，格式说明不放行。 | test: `tests/test_eng_loop2_play_ops.py` 机读放行拒启/正常分支、临时git忽略与dirty拒启回归；cmd: 精确`.gitignore` diff及check-ignore/status；artifact: 新停点§3/§6/§7与操作页对应声明 | OpsK1K2K3K4 | 2026-10-08 |

### 4. SUB:2本人结论的核对读法

唯一来源为 `docs/unity-test-log.md`「UT-P1-ENG-LOOP-002-OPS-SUB2」：用户本人通过只读网页与原图对照，样帧是交接§5所列第三次328…q1和第四次188…q1两张，报告“两张都一致”。**满足AC-11修订1至少2张、用户本人确认外观语义一致的人眼保真要求**；按已签SUB:2记已执行1次，当前只缺实现把记录写入候选证据。第一张消防栓候选的追问不推翻呈现一致，也不证明VLM选对/跟对；沿日志和原诊断现象归因，不作正式指标或模型通过证据。

本人未逐项报绿色sha提示/已解码文字，提示行实见值记 `UNKNOWN（用户未逐项报告）`；用时未报告亦UNKNOWN，不能代写本人看到绿色、严格墙钟守限或新测试通过。不因缺少逐字提示行要求重新签发/重看：人眼外观一致已有明确答复，机械字节/解码绑定仍由代码与替身证据核查，不用自动sha替代人眼。

实现在 `-OpsK1K2K3K4-handoff.md` §5追加来源条目、确认人=用户本人、两张路径与各自一致结论、上述UNKNOWN及适用代码关系，并将页首/§7/§9的当前NOT_RUN和SUB:2=0改为最新事实；保留原准备记录为历史，不改用户日志或账本。呈现版本从用户日志登记和git运行时核，不手抄派生SHA；候选间网页呈现代码不变可复用本次记录，须明确对应关系；呈现代码变化则在已签剩余额度内请本人重核。原PNG只作为只读外观样本，不复制入证据，入候选的是人眼记录，不是诊断运行读数/正式采集验收。

### 5. Implementation交接与停止边界

下一角色读本节§1–4、原「OPS验证额度落实与IR裁定」§1–5、交接§4/4.1/5/6/7以及本人日志条目。在原OPS闭集加本节§3唯一`.gitignore`路径内：记录SUB:2最新事实，落实IR-OPS-7文案/既有fail-closed与IR-OPS-8精确忽略，同步操作页和候选逐AC证据。不要实际写sub3_release或执行诊断、SSH、板服务、Play。

交接§6附记的既有 `git fetch origin` 属固定发布引用的只读核对组成，不是新增板SSH连接或模型/依赖下载许可；只沿原origin取发布引用，不扩网络用途/额度。本轮未执行fetch；SUB:1测试本身网络0的限制保持。

本次SUB:1的条件②结论限已测代码。后续只触及上述具名路径/机读文案/忽略规则的窄修，不触真实模型加载器、数据划分或对外指标，可按engineering§6提出**已有停点全套+覆盖改动的零模型focused+修前红/修后绿**的替代适用性，逐文件列出理由/原输出，明写补丁未跑全套、不记全套通过；独立Review有权判替代不足。若需全套，真正变更的新候选仍可用SUB:1最多3候选中剩余至多2个、各一次，原日志保留另用ops-*具名日志，不需另签既有余额。任何同候选第二次/安装/新增类别/超额回用户。

全部条件成立后，由实现在交接§7逐条按workflow§4.3.1四条件自证并按AC编号附证据，不只写SUB:1/2两项：范围冻结和完整、相称测试/替代充分、已知Unity失败/人眼义务处置、复核文件入口/当前状态/候选提交/未测风险齐备。完整Ops diff基线从交接登记与git解析，含全部Ops工具/测试/操作页、精确忽略改动及证据，不仅末次窄修。提交推送后交 **C6@OpsK1K2K3K4**；未齐只交具名缺口，不自行宣称稳定或进入SUB:3。

needs_user=none；consumed=none。Overall REVIEW_PASSED/ACTIVE只保留旧范围；本轮不消费Ops通过或签DONE/UNITY_NA。原R4终局/冻结集、新K1K3通过与计数、N-1全套3/3、旧债/偏差/UNKNOWN/ACQ暂停保持；真实板监督未验证，正式G1–G5/现场登记/AC-18及AC-14/15/18、AC-16板端NOT_RUN仍在。交接owner/status只见状态板，不新增活跃轨道。

open_items: none


## C7@OpsK1K2K3K4 核对判读与复核交接（2026-10-08，Acceptance）

requested.round=`C7@OpsK1K2K3K4`；Dispatch-Id=`P1-ENG-LOOP-002-C7@OpsK1K2K3K4-20261008T050706Z-1e0f`。本停点C退回1/1已用，本轮只核对不再退回；C6-1满足、C6-2/3不满足照附最新核对表交新鲜R1。候选/通过基线/PG路径均运行时解析，唯一详表 `docs/evidence/P1-ENG-LOOP-002-C7-OpsK1K2K3K4.md` §0–2/5。不是新D裁定、AC修订或独立复核；原合同及累计25修订/新AC0保持。

**(a) SUB:2无需本人重看，R1无需等用户。** 原「OPS基线与IR78裁定」§4以呈现代码是否变化为判据；完整blob已变，旧交付§5.1的blob相等理由仅属当轮历史。对登记呈现版本至当前候选逐字核PAGE/FIDELITY_PAGE、保真服务/样帧加载、源图读取/身份/序号/顺序/坐标与显示路径均不变，本人两张一致记录可复用。静态比较方法与派生标识见C7证据§3；提示行/用时UNKNOWN不补写，不代判模型/Unity/正式指标。若R1核得真实呈现变化再按剩余SUB:2路由本人，本轮needs_user=none。

**(b) 最后竞态窄修的engineering§6适用与充分性交Review判断。** 相对最新全套候选三文件具名窄修、133例focused与确定性红绿已提交，补丁未全套且不记通过；原模型加载器/划分/评分算法未改，但受理记录关联计划—实际/完整失败分母，不仅用评分文件零diff代独立判断。本轮不要求全套或安装、不签条件②；若R1判不足交实现按现行SUB:1剩第3真候选的一次/新派发处理，不得同候选第二次或仅改文档凑候选。详见C7证据§4。

R1入口为`docs/reviews/P1-ENG-LOOP-002.md`，先独立核四条件与开轮资格；不成立由Review给REVIEW_BLOCKED不开轮。C7完成不等于新Ops独立通过或SUB:3放行，本轮无实际sub3_release行、无Unity/板/正式证据新增，无UNITY_NA/DONE，不改旧轮次/债务/资源账。

open_items: none

## OpsK1K2K3K4通过消费与SUB:3放行（2026-10-08，Acceptance）

requested.round=`OpsR2消费与R1-4裁定`；Dispatch-Id=`P1-ENG-LOOP-002-OpsR2消费与R1-4裁定-20261008T063600Z-9eeb`。owner=Acceptance；范围仅提案/状态板/正式设计/implementation-status。本轮消费最终通过、裁定争议与记债，不开D/C/R、不重新做常规候选检查、不签独立verdict；零SSH/启板/Play/功能测试/代码修改，consumed=none。

### 1. R2消费、AC状态与归因

**消费 `R2@OpsK1K2K3K4` 的 `PASS`**（同名复核§0–5及Verdict完整读取）。候选从该轮唯一有效passed_candidate运行时解析；只读git核实它是当前HEAD与origin/main祖先，两者至候选全部PLAY_GOVERNING及三操作单差异均空。这是来源核对，不是第三次候选检查。Overall仍REVIEW_PASSED/Lifecycle ACTIVE，现在覆盖Ops代码/操作单及旧通过范围携带，不代表正式证据完成。

| 范围 | 接受消费后的状态 / 证据指针 |
|---|---|
| AC-8修订3、AC-10修订1…5代码侧 | R1-1…4闭合，采用R2§1/§2独立结论；C7中不满足为历史候选结论。R1-5按§3单独记债，不把其异常路径签成已修。 |
| AC-1…7、9、11…13、17与AC-15/16代码侧 | 携带R2§2。SUB:2本人两张一致可复用，呈现路径未变，提示行/用时UNKNOWN保持（R2§4）。 |
| AC-14/15/18、AC-16正式板端 | NOT_RUN/证据缺失；前台SSH监督、中断、真实出帧/停止和跨设备归档仍仅替身（R2§5），无UNITY_NA/DONE。 |
| SUB:1测试证据 | 实现交接§12.2/12.3及ops-r1rework两份日志；R2核11例红绿、focused144 OK、全套新增失败0。16项环境/既有基线失败保留，全套不绿；3候选各1次已用尽，真实加载数UNKNOWN不改。 |

机械归因：Ops R1-1的BC-8、R1-2…4的BC-10 → 实现错误4、均闭合，连同旧范围累计实现错误9均闭合；R1-5 SCOPE_GAP → BC缺失（非阻断）1、OPEN；无新增上轮漏检/上游漏检/RED_LINE。Ops实际C2轮（C6/C7）/首退1，R2轮（R1/R2）/返工1/2止；旧K1K3 C5/R1与旧K1K2K3K4 R4终局/返工2/2/冻结集不重置。本轮解释修订1（§2），累计AC修订26、新AC0。

### 2. R1-4：守账N与正式冲突

**N=2，为整个已签B-main实现自证对正式归档的评分调用总次数**。依据为「Mac mini四题答复落实」§2正式归档零模型回放行、§5.2原表、实现交接§12.4和复核R1-4/R2§3。没有“每归档”限定，不能因三剧本目标扩成每归档2、每归档1或一摘要进程包三次评分。独立复核≤1次为另一个既有用途上限，不借给实现。

现行代码每实际调用一次原 `analyze_play score` 就扣一次，成功/失败共账；已有score输出只引用，账不可读拒评，下一调用越2则S-ENVELOPE/非0停依赖。保持FORMAL_SCORE_LIMIT=2和现行守账键；本轮无PG变化、不开新复核轮。守账在$OUT/play持久化，不能换输出根、删/重置账或手工绕summarize取得额外额度。

正常P1/P2/P3三个归档，第3次评分被拒是合同后果，不能写三剧本四表齐或AC-14/18通过，不能把失败出口改成功。**正式整批运行本轮不放行**，先转呈§5资源冲突；SUB:3评分本来为0，不受该冲突阻塞。以下源于实现§12.4及复核R1-4争议，追加解释既有AC，原文不覆盖，不改信封/目标/算法，不新增义务。

| 编号 | 验收项（追加生效） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 6 | 解释修订3/O1/O4与已签B-main：实现正式评分N=2为全批实际调用总次数，每调用前守账、成功/失败共账、已有输出只引用；不可读或下一次越界拒评并非零退出停依赖，不是每归档/摘要进程2次。保持常量/键；第三归档不能全评的冲突按本节§5回用户，不绕工具或换根重置预算；SUB:3评分仍0。 | test: `tests/test_eng_loop2_summarize_ops.py::ScoringTests.test_r1_4_formal_score_calls_are_guarded_before_each_call`；artifact: `docs/reviews/P1-ENG-LOOP-002.md` R2@OpsK1K2K3K4 §1/§3；artifact: 实现交接§12.4 | OpsK1K2K3K4；代码既有通过携带 | 2026-10-08 |

### 3. R1-5记债

采纳独立复核R1§3/R2§3的不可达判据与非阻断路由，不改分级、不要求本轮实现。on_reply写失败及CLI kill后35s仍未静止两条异常路径记 **OPEN**，唯一入口为 `docs/implementation-status.md`「范围外已知缺陷」R1-5行；扩大故障域或修该路径前由获批合同承接UNKNOWN/停依赖及具名回归。真实执行若触发保留原流/UNKNOWN、停依赖交回，不用本次PASS称异常已闭。复核未写block，不写RELEASED_SCOPE_GAP、不改复核文件或伪造release。

### 4. SUB:3代码前提放行与现场边界

**准予按已签SUB:3合同进入独立一次诊断的现场核对/执行交接**：IR-OPS-5模式合同落实、新代码C7→R1返工→R2通过且本轮消费、SUB:2已附议、全局check_docs完整扫描无未release消耗性block。本机当前诊断根未检出同request_id粗账，但不代Air实际执行检出/全部相关根去重。账本「用户答R3阻断消费六题…」SLOT:FACT:1已有本人窗口互斥确认；现场端口/残留/当前板资源安全仍须核，不用旧快照充当前事实。

以下实际机读行由程序从同名复核R2有效passed_candidate解析写入，只证明接受消费该代码；发布引用/通过检出及PG零diff、干净树/无_Recovery、账本/一次未用、Air环境/资产/烟测32行、现场共享槽/端口核仍分别强制。缺项拒启，UNKNOWN或冲突停报，不先启动试前提；不要求正式G4，也不生成G4。

sub3_release: e24e13f020cdec9163d01ffc71d7e52ecc587f8a

下一执行严格按诊断页「现行SUB:3」唯一入口和「OPS验证额度落实与IR裁定」§2/§4/§5.4：Air+既有Jetson、整批1次/45min/SSH主连接≤2/服务及GGUF≤1/故障重启0/YOLO≤1/本人Play≤1/板200MB及Air250MB，评分/正式ID/下载安装等0。**本人先选唯一P1/P2/P3（P2另选预登记对象）及在线操作窗口，Unity先打开而不按Play；代理/脚本在本人可同步配合后才进入受限动作。** 这是已签操作安排，不重签相同额度；本轮不代选剧本，不假报窗口/当前端口已核。

交接Consuming=yes预占唯一消耗性轨道，不表示已消费。执行树固定机读通过候选，文档树固定本次推送后发布引用；等待本人窗口期间不改PG/操作页。拒启区分未消耗门失败与已开始诊断并实际记账，开始/失败/结束按合同用尽一次，不以未按Play或子维度剩余续开。四类STOP/DIAG_FAULT与安全收尾保持，窗口不修源码；需修复回正常停点，额外全套/诊断或新类别先列清单后用户首签。

原件/粗账/报告只留独立诊断根，不进正式证据/Unity验收日志，不判AC-14/15/16/18，不自动接B-main；实现仅提交指针及故障/用量/UNKNOWN说明交接受核清。若未来用户选§5增评分额度，常量/测试为PG变化须新复核轮，届时本行不绑定新代码，须重新消费并核尚未使用的一次额度，不能复用旧绑定或已用诊断许可。

### 5. needs_user：正式评分资源冲突（待转呈）

| request_id | 待用户决定 / 推荐 | 理由与为何只能用户定 |
|---|---|---|
| P1-ENG-LOOP-002:B-main:SCORE:CHANGE:1 | **推荐**将B-main实现正式评分全批总上限≤2改为≤3次（不是每归档3；成功/失败共账、无免费重评），用于现行入口三个既定剧本各首次评分；独立复核≤1及其他维度保持。备选保持2并继续不放行完整正式批次，另定缺口/范围处置，不把两份四表冒称三份齐。 | 三剧本至少需三个评分调用，R2指出第3次必拒。资源只能用户首签，接受只能解释原限，supervisor不能代增未启用SUB维度。采纳须明确授权对应合同修订及常量/测试更新；改后进新复核轮。SUB:1已耗尽，额外验证先由实现列机器/次数/真实加载/回放/墙钟/磁盘清单再另签，不预授权第4次全套。 |

SUB:3本人剧本/窗口/Play/网页配合是已签操作待安排，不属新增授权；不重提SLOT确认或已答OPS题。正式仍需G1–G5、Air正式原件/目标环境、真实prep原流G4核清、现场HEAD/status/Unity日志登记及AC-18证据停点，目前无正式放行行。新设备/类别、SOURCE缺件需代理跨机复制、原用途外ENV探测等只在触发并形成清单后回用户，本轮不首签/预设额度。旧债/偏差/UNKNOWN、旧诊断余额耗尽、ACQ暂停及旧终局/计数均保持。

open_items: none


## SUB3核清与评分上限落实（2026-10-08，Acceptance）

requested.round=`SUB3核清与评分上限落实`；Dispatch-Id=`P1-ENG-LOOP-002-SUB3核清与评分上限落实-20261008T155601Z-356b`。本轮为用户点名诊断故障裁定及已签资源变化落实，不是C核对或独立复核；不改旧核对表/复核文件/用户原话账本，不新增机读block/release或实际运行放行。consumed=none；零SSH/启板/Play/功能测试/模型/回放/代码修改。

### 1. SUB3诊断P1核清、计次与主张上限

只读来源为 `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md` §13。原件路径沿该节诊断根运行时定位，读取 `ops-diagnostic-ledger.json`、`ops-events.jsonl`、`ssh/d1.tsv`、`raw/026-ssh-master-d1.stderr`、`raw/027-final-status.stdout` 与NOTES；原件留诊断根，不复制进证据/正式账/Unity验收日志。release/preflight通过只表示当次前提核通过，不证明真实链路或板端能力。

| 维度 | 核清结果与限制 |
|---|---|
| 整批/主连接 | consumed=true，整批1/1用尽；d1尝试1/2、rc255，先占次再执行，未重试/未开d2。整批已结束，主连接余额不续开、不转正式。 |
| 墙钟/磁盘 | 粗账elapsed_s=3.864497184753418；Air峰值14,648,011 B（含待归位runtime）、末次5,901,361 B，低于45min/250MB。板磁盘没有读数，board_peak_bytes=null；按事件链没有远端命令/同步/建根，故本批工具写入0，不把null改成实测0。 |
| 未执行 | 服务启动/故障重启/measure/k-receipt/Play计数均0；没有板channel、会话或模型启动命令，GGUF/YOLO实际执行0（粗账原字段UNKNOWN保留）。板身份/依赖/端口/服务释放/真实监督及Unity闭环仍未验证；not_executed空数组不解释为全部步骤完成。 |
| 收尾 | events记录frames与m3_body_truth.jsonl移入hold，closeout列同两项已归位；最终status原stdout为空、工作树行数0。service_release=done是没有本次服务的收尾分支，不是远端端口释放实测。未Play，按钮时刻不适用；原字段UNKNOWN不补写。 |
| UNKNOWN/偏差 | ssh报错前是否完成TCP/认证握手UNKNOWN，不能宣称“从未联网/认证”；可以确认未执行远端命令。未见资源越界/重试/旁路执行；这只是本次记录核清，不追认旧诊断偏差。NOTES空模板仍含旧180min/5Play/3启动历史数，不能拿它当本次授权或实账；本次只取已签SUB:3与粗账。 |

故障仍读作 **DIAG_FAULT ssh_master_failed d1**，不改套正式N-3/11码，也不因普通连接错误补造STOP1–4。本次未进入Play或产出四表，不能判AC-14/15/16/18满足，不能写G4/DONE/UNITY_NA；旧SUB:1三候选各1次与N-1三次全套均用尽、SUB:2本人记录/UNKNOWN、旧债与ACQ暂停保持。

### 2. DIAG-CONTROL-1归因、分级与修复合同

原stderr的实际套接字名含OpenSSH随机后缀，UTF-8字节长度运行时复算为120；后缀前为103。`tools/eng_loop2/play_ops.py::DiagConnection.__init__/open` 把ControlPath置于完整诊断根的ssh子目录，OpenSSH报本机unix_listener路径过长并rc255；生产入口此后只安全收尾。与网络/板端推理/Unity表现无关，握手UNKNOWN按§1保留。正式SshUnit较短路径的长度比较只是静态事实，未实跑，不据此签正式SSH通过。

**裁定CLASS_2、范围内必修**，主要对应AC-10修订4/5及IR-OPS-5§4的诊断主连接/同会话监督可执行性（若映射独立finding依据，BC-10读作AC-10）。可达的是已冻结P1与当前Air正常仓库路径，失败改变工具/操作者执行，不是CLASS_3或SCOPE_GAP；不改数字/研究结论，无CLASS_1/RED_LINE。归因为**实现错误：套接字路径选择未满足目标系统的本地限制**；既有假ssh未建立真实AF_UNIX套接字，覆盖遗漏由本次生产故障显露。不是独立复核finding，不追改旧R2依据列/归因统计、不自签“上轮漏检”机读block；独立Review仍须核新候选完整diff和红线。

修复保持诊断目录/正式目录与资源账独立，选择**本次进程拥有的短私有临时套接字目录**，以编码后的实际路径及OpenSSH临时后缀留量核本机限制，不能只截目录名/字符串字符数、只测无后缀名或用假ssh成功替代。短目录的权限、归属/唯一性、生命周期与原流指针由实现写明；不能复用/删除未知套接字，失败或无法建立安全短路径即拒启/非0停依赖。全部ControlMaster创建、check/通道/exit须使用同一实际路径；失效仍不隐式直连/自动认证/重试，成功失败均按原主连接账计次。仅清本进程拥有的临时目录，不能靠改全局SSH配置、仓库路径、正式/诊断输出根、dirty判据或绕过双来源门修复。短目录增长计入本次Air峰值，收尾释放后才清理，不把移到诊断根外当作免账。

本机回归须从生产路径构造真实长诊断根、调用真实路径分配/连接组合；至少一条修前因生产长路径必失败、修后通过的具名行为回归，并以**本机AF_UNIX实际bind/关闭**核短路径有效（不接Jetson/不执行真实ssh）。另核d1/d2独立、跨批不复用、失效无回退、失败计次/收尾及临时件归属；假ssh用于有限通道行为，不能是路径长度问题的唯一证明。本轮不跑这些测试，不预签已修/已闭。

### 3. 两条用户答复落实与追加AC

签发唯一来源是账本2026-10-08「用户按推荐签发 B-main 实现正式评分总上限 ≤2→≤3，并为 SUB:3 诊断选剧本 P1」；次序/本人窗口来源是同日「用户选先跑 SUB:3 诊断（P1）再改评分上限，操作窗口为现在」。原话只在账本；本轮不代写。诊断已结束，先诊断后修上限的次序已经满足；“现在”窗口不自动延续到未来新诊断。

**B-main评分资源修订1（SCORE:CHANGE:1）生效**：实现自证对正式归档的评分**全批实际调用总上限由≤2改为≤3**，不是每归档3/每摘要3；成功、失败、超时、中止共账、调用前扣次，没有免费重评。独立复核证据重放仍≤1且用途独立，其他B-main维度及G1–G5、AC-18不变。这一签发不是新增停点全套、诊断、模型/设备额度或正式整批放行。原§5.2及「Mac mini四题答复落实」中的2次、AC-10修订6与Ops通过消费§2保留为修改前记录，冲突处以本节追加修订为准。

| 维度 | 现行授权/代码处置 |
|---|---|
| 实现正式评分 | 全批≤3次；保持score-ledger.json/formal_score_calls持久键与原批次账，FORMAL_SCORE_LIMIT改为3。已有调用计数原样继承，不清账/删账/换根；若已用2，只剩1。原账不可读仍拒评。 |
| 三归档与拒评 | 三个既定归档各首次成功评分合计3；第4个实际调用在调用前S-ENVELOPE/非0、账不超3。已有输出只引用；任何失败已扣的次数不免费补回，不承诺三份四表必齐。 |
| 其他用途 | 独立复核≤1、诊断评分0、真实归档测试回放0；其余原已签信封/原STOP不增不减。代码当前仍2，授权生效不等于代码已实现/复核通过。 |

以下来自本次用户要求、实现交接§13.3与原SCORE:CHANGE:1授权/实现§12.4争议，解释已有AC；不是核对轮读码新增义务。追加两条修订，累计AC修订28、新AC0，原文不覆盖/删除。

| 编号 | 验收项（追加生效） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 7 | 替代修订6仅N=2/保持常量这一部分：按本节§3已签全批总次数3落实常量与三操作页相关现行说明，逐调用前扣账、成功/失败共账、已有输出引用/不可读拒评/非0停依赖保持。三次允许，第4次拒绝；账继承不重置，失败消耗/重评与跨摘要共账，诊断不评分。 | test: `tests/test_eng_loop2_summarize_ops.py` 生产summarize/run_score入口三允许/第四拒绝、失败扣次、持久化/已有输出/坏账；artifact: 新候选逐AC证据、三页合同映射 | OpsScoreDiagK1K4 | 2026-10-08 |
| AC-10 修订 8 | 解释修订4/5与IR-OPS-5：按本节§2修DIAG-CONTROL-1，实际短私有ControlPath及后缀留量可用、所有通道同路径、失败/失效无认证回退、原计次与安全收尾保持；临时件唯一归属/清理与Air峰值计量完整。诊断原件不作正式证据，新诊断额度未签0。 | test: `tests/test_eng_loop2_play_ops.py` 生产长根路径修前红/修后绿及本机AF_UNIX bind、计次/失效/释放/跨批隔离；artifact: 新候选路径与临时磁盘映射 | OpsScoreDiagK1K4（K1；既有K2安全约束携带） | 2026-10-08 |

### 4. 合批决定、实现闭集与稳定停点

**两项合成同一实现候选、一次核对入口和同一首轮独立复核**，不先对评分常量单独开轮。新接受的增量停点为 `OpsScoreDiagK1K4`：K1诊断监督入口/路径与既有同连接协议；K4正式评分调用资源边界与摘要拒评，不改变四数字算法、分母/采样。原K2服务释放/控制安全及K3身份/本人选择按原合同携带，不开放修改，无K5。本停点是在旧Ops R2 PASS已消费后落实用户新签资源变化及具名诊断修复；旧Ops C6/C7首退1/1、R1/R2返工1/2止、旧K1K3通过、旧K1K2K3K4 R4终局/冻结集/2/2均保留，不在旧通过轮追加finding或重开其终局。

本增量修改闭集为 `tools/eng_loop2/play_ops.py`（仅诊断ControlPath分配/释放/临时计量，不改正式SshUnit动作域）、`tools/eng_loop2/summarize_ops.py`（评分总上限及说明，不改原评分函数/分母）、`tests/test_eng_loop2_play_ops.py`、`tests/test_eng_loop2_summarize_ops.py`；文档仅三操作页（play-ops、diagnostic-smoke-ops、mini-ops-prep，相关现行说明/引用）、同名ops-*验证清单/原交接新增具名小节/测试日志与current-status。三页仍属冻结PLAY_GOVERNING操作单。operator_web/其呈现与隔离测试、.gitignore、runtime/README、controller、Assets、config、部署16路径、原评分analyze_play/语言服务/测量/模型/包环境与基础设施不在本次修改闭集；必要越出先具名待裁定。

下一Implementation先本机完成窄修与相称**零模型focused/具名红绿/本地AF_UNIX**，保留旧全套日志/基线、本人SUB:2呈现不变记录与UNKNOWN；不SSH/启板/Play/真实归档评分，不安装/写实际runtime。新诊断申请ID仅是§5待签建议，本次不修改执行白名单使旧SUB:3可再次执行；新额度签发后其账本绑定/入口适配另走具名合同答复，不自动用新工具绕耗尽许可。

**稳定条件②不预准豁免全套**：N-1及SUB:1用尽，评分调用路径关联对外指标，不能仅凭analyze_play零diff断言engineering§6窄修替代适用。实现先提交逐文件变更/生产回归/覆盖清单，说明是否触及真实模型加载器、数据划分或对外指标路径及替代充分性；不成立或Review判不足时，按原VALIDATION:7列机/解释器/命令/真实加载数或UNKNOWN/回放/每候选次数与最多候选数/墙钟/磁盘/网络/Play/ID完整清单交用户另签，**不得跑第4次全套后补签**。未满足四条件只交进度/清单，不冒称稳定、不交C/R；本轮没有替代通过结论或额外全套额度。

条件齐备后，实现在原Ops交接新增本停点具名节逐条自证四条件/逐AC证据，列完整候选diff及未在真实条件下验证的风险，提交推送后停止依赖实现→接受下一实际 `C8@OpsScoreDiagK1K4`（work ID的C连续计数；若磁盘实际已有新增C则运行时顺延）→新鲜独立 `R1@OpsScoreDiagK1K4`。本新范围首退≤1；复核从最新有效passed_candidate运行时派生全量基线，PG非空才开轮；红绿/focused/返工上限/冻结集/终局及全局blocks保持。不假报本轮C/R已开，不签独立通过；复核通过并被接受消费后才可另审新诊断或正式门。

### 5. needs_user：新诊断独立首签（建议；未授权，不执行）

**P1-ENG-LOOP-002:DIAG:RETRY:1**：推荐修复与评分合批通过消费后，再签**独立一次P1新入口诊断**。目的是核真实SSH前台监督/身份/网页链路及安全收尾，旧SUB:3未到板，不能靠零模型替身消除真实条件风险；不用于试数/优化、不评分/判门。备选暂不追加，保持真实链路未验证及正式不放行；不得用旧1/2连接余量免费续试。下表是完整申请清单，**当前每维度仍0**，不是附条件自动授权。

| 维度 | 推荐签发值 / 执行口径 |
|---|---|
| 机/执行人/入口 | 同一MacBook Air现有.venv-yoloe与Host Jetson Orin Nano 8GB Super，现有模型/解释器原样；代理/脚本前台机械步骤，用户本人Play/停止、发送/跳过、确认/拒绝与反馈。沿现IR-OPS-5生产入口，新的request_id/账本绑定先经接受合同落实，不给已耗尽SUB:3更名续用。 |
| 次数/剧本/墙钟 | 新独立整批≤1，P1固定（本题仍须用户采纳），无免费重试；完整墙钟≤2700s，含准备/源码同步/等待/测量/Play/中止/收尾，等待不清零；本人另给新在线窗口。 |
| SSH/服务/模型 | 主连接尝试≤2，失败也计，有限通道与同会话释放；板服务启动≤1（含拒启）/GGUF加载≤1/故障重启0，measure与Play共用一次驻留；YOLO加载≤1。 |
| 数据/测量/HTTP | 本次smoke32行读入，生产measure≤1（3预热+32计时）/k-receipt≤1，失败不续依赖；只留诊断根。HTTP/payload按既有budget=None用途粗账，不另借正式335/200/60MB额度，仍受原16次result/软硬截止和墙钟/磁盘约束。真实归档回放/评分0。 |
| Play/标签/runtime | 本人Unity Play≤1、诊断会话≤1；正式scenario/session/run ID0，diag-标签/独立session与段根，不改采样/N-5/指令/阈值；共享槽互斥，原runtime残留只hold/归位。 |
| 两端峰值/传输 | 板独立新诊断根新增≤200,000,000B，Air新增≤250,000,000B，含短私有套接字临时目录/缓存/日志/图像/hold与移动产物，不只末次du；仅既有16部署源码/config及本次诊断输入同步，无模型/二进制/库传板、不跨机取证，两端增量与传输受完整墙钟/峰值限约束。原件根仍诊断页固定模式、每批新根不覆盖，短临时件清理/归属映射须核。 |
| 明确0项 | 停点全套/真实归档测试回放、5060/云/外部模型API/另列GPU·h、下载/pip/安装/编译、新设备、模型/库/轮子传板、跨机代理复制、系统/SSH/沙箱设置变更、Unity代码/新正式ID均0。 |
| 未核/执行前提 | 当前Air↔板认证/HTTP、端口/残留、板资源/身份、前台中断/释放及Unity闭环未验证；新代码独立通过消费、唯一签发入账/机读绑定、干净执行树/PG空diff、现场核与本人新窗口齐才执行；四STOP/DIAG_FAULT/非证据/非0失败保持。 |

**为何只能用户定**：整批诊断1/1已用尽，新Play/板服务/连接/加载属于新增资源许可；账本未启用supervisor_subdelegation，接受/调度均不能首签或复活余额，用户已签评分3不涵盖诊断或额外验证。实现可先完成零消耗窄修，不等本题答复；依赖该新许可的动作一直停。若额外全套清单形成，再按§4另列具名题，不在本轮预设数值/自签。

当前Overall=REWORK_REQUIRED/Lifecycle=ACTIVE，含义是DIAG-CONTROL-1具名必修及新评分合同待实现；保留旧Ops R2 PASS已消费及其独立finding归因统计。原sub3_release只绑定旧已用尽一次，不能绑定新候选/许可；本轮不覆盖原机读行或写新实际放行行。正式G1–G5/Air正式原件环境/现场登记/AC-18以及AC-14/15/18、AC-16正式板端NOT_RUN、旧债/偏差/UNKNOWN/ACQ暂停保持，无UNITY_NA/DONE。

open_items: none

## 合批进度与全套清单核清（2026-10-08，Acceptance）

requested.round=`合批进度与全套清单核清`；Dispatch-Id=`P1-ENG-LOOP-002-合批进度与全套清单核清-20261008T175801Z-5131`。本轮仅核实现交接§14与VALIDATION:7申请，不是C8、设计退修或独立复核；不改AC、核对表、复核文件、原证据/用户原话账本，不自签额度或运行放行。consumed=none；未SSH、启板、Play、跑功能测试、加载模型、回放或改代码。

### 1. 进度核清与稳定条件

来源为 `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md` §14.1–14.7、`docs/evidence/P1-ENG-LOOP-002-score-diag-fix-focused.log` 全文、该轮实现提交及提交态日志补记的路径统计（由git运行时定位）。实际增量为两工具、两测试、play-ops与diagnostic-smoke-ops两页；mini-ops-prep无diff，符合原§4允许说明不需修改的读法。交接记录了短私有ControlPath/真实AF_UNIX探针、计量/释放，以及评分常量3/坏账拒评；修前12例8 failure+4 error、修后同12例OK、提交态四模块156例OK均有日志摘要。**这些是实现者的进度/证据声明，本轮未重跑、未做完整候选C核对或独立核实修复闭合。**

采纳交接§14.5的适用性判断：`summarize_ops.py`决定第三个正式归档的实际评分调用及四表引用，触及K4对外指标路径，engineering §6窄修替代前提不成立。不能以原评分算法零diff或focused全绿替代停点全套。本合批仍IMPLEMENTED/非稳定候选，未自证四条件，不交C8/R1；旧Ops R2 PASS不覆盖新修复。上次全套 `docs/evidence/P1-ENG-LOOP-002-ops-r1rework-tests.log` 的16项是历史对照集（3 failure/13 error/54 skipped），今日是否逐名不变UNKNOWN，不预签新全套全绿或新失败归因。

### 2. 全套申请核清：暂不呈可首签清单

对象为交接§14.6的 `P1-ENG-LOOP-002:42979c14:SUB:1`；标题摘要前缀已零消耗复算一致。账本没有本申请签发：旧SUB:1与N-1均耗尽，评分总额3授权不涵盖新全套，旧信封不能续用。本轮保留实现提出的Air系统python3/不装包、每候选1次/最多3候选、每次15min/日志2MB等**申请值**，不将其写成授权或自行增减。真实模型加载数UNKNOWN可按原OPS签发先例明确呈报，不能改成0或沿用旧静态数充当实测；UNKNOWN本身不是本轮退回原因。

**SUITE-LIST-1：数据/临时磁盘披露与命令不一致，须先补清单。** §14.6声称“0（不读正式或旧真实归档；评分全用替身）”，但指定命令无筛选地discover整个tests。只读源码与既有原输出提供以下反例：

| 来源 | 实际行为及核清边界 |
|---|---|
| `tests/test_dist_data_round4.py::RealArchiveClosureTest`，`setUp/_images/test_arm_a_truth_patterns_cover_exactly_five_files`等 | 当现有probe根存在时枚举旧runtime图像根、runs真值文件名；本轮只读exists核得该setUp前提存在。上次全套同类三条FAIL表明曾执行。即使只是目录/文件名读取，也不符合“不读旧真实归档”。 |
| `tests/test_dist_data_round8.py::ArchiveCopyCase.copy/place_frame`及`ScenarioBindingTest` | 当现有scene004 provider存在时，将旧归档真实帧/旁车/manifest/scenario字节读入并复制到TemporaryDirectory；本轮只读exists核得provider与M3帧根存在。上次原输出两条ERROR在copy2读取缺失scenario处失败，不能把此前归档读取/临时复制记0，也不能把后续未执行断言当通过。 |
| §14.6“证据日志≤2MB；临时目录随测试自动清理” | 2MB仅限制日志，不说明上述临时真实字节副本的峰值/用途范围；结束清理不等于峰值增长为0。新AF_UNIX父目录也应与其他测试临时目录一并披露。未核峰值保持UNKNOWN，不由接受角色拍数或从B-main借额度。 |

这是VALIDATION:7所需执行清单的具名缺口，**不是新代码finding、AC义务、C轮退回或对旧全套授权/结果的追溯改判**。“本项正式评分/显式真实归档重放0”与“全套既有测试完全不读取真实归档”含义不同，不能用前者掩盖后者。既有全套已签/已耗事实保留，不自裁其历史执行越权。

下一实现仅零消耗修订交接§14.6：沿当前discover静态盘点既有真实归档读取/枚举/临时复制的具名测试、来源根、执行条件、用途、次数读法与可得字节/峰值依据；拿不到的写UNKNOWN，明确哪些申请维度覆盖临时增长。分别写清本项正式评分/独立归档回放与既有测试内数据使用，不维持已被源码反例否定的全0声明。保持原套件/解释器/skip门/源归档不变，不为凑零删测试、移走归档或假报缺件；不跑全套/探测、改代码或申请装包。若确需改变命令、环境、数据域或申请额度，列明变化与理由，回接受核清及用户首签；不能自行扩执行范围。补正后接受再决定是否呈最终申请，未签依赖维度仍0。

### 3. needs_user（推荐、理由与为何只能用户定）

| request_id | 推荐及理由 | 为何只能用户定 / 当前效力 |
|---|---|---|
| P1-ENG-LOOP-002:42979c14:SUB:1 | **先由实现补正SUITE-LIST-1，再由接受核清转呈首签**；全套必要性已成立，申请的每候选1次/最多3候选/15min/日志2MB保留为实现申请，数据/临时增长补齐前暂不推荐按现清单直接签。不签则保持进度态，不交C8。 | 新全套越出旧SUB:1/N-1已用尽额度；engineering §6/§8及原VALIDATION:7要求用户首签。接受只能核清，supervisor执行子额度未启用，不得自签、预设真实加载/临时磁盘额度或先跑后追认。本题目前**待补清单，不呈为可执行签发包，全部未签0**。 |
| P1-ENG-LOOP-002:DIAG:RETRY:1 | **保持上节§5原推荐及完整申请**：合批修复通过消费后，用户另签一次独立P1新入口诊断并给新在线窗口；理由是真实SSH/板服务监督/Unity链路仍未验证。备选暂不追加。 | 旧SUB:3整批1/1已用尽，新增Play/板启动/连接/加载只能用户首签；评分3及新全套申请均不覆盖诊断。本题仍待用户答复，本轮不代答、不落实或复活余额；即使答复到来仍须单独落实合同与新代码通过消费前提。 |

### 4. 保留门与后续顺序

Overall=REWORK_REQUIRED、Lifecycle=ACTIVE保持；未开新D/C/R，不新增AC修订、finding、归因计数或block/release。先补清单→接受核清→仅用户新签并在答复会话逐字入账→接受落实→实现按签执行一次全套、逐名分列旧/新增失败并补四条件→成立才交C8@OpsScoreDiagK1K4及独立R1；不得以本节作首签或独立通过。后续真正返工候选的全套用途仍须取最终已签次数，不能以文档变化凑候选或同候选免费重跑。

原SUB:2本人两张一致/提示与用时UNKNOWN、旧Ops R2及归因/计数/R1-5 OPEN、旧终局冻结集/债务/诊断偏差/UNKNOWN/ACQ暂停均保持；没有新板或Unity验证。正式G1–G5/Air原件环境/现场登记/AC-18及AC-14/15/18、AC-16正式板端NOT_RUN，无UNITY_NA/DONE，不收入诊断原件/读数为正式或里程碑证据。唯一owner/status交接在状态板。

open_items: SUITE-LIST-1


## 全套清单再核清（2026-10-08，Acceptance）

requested.round=`全套清单再核清`；Dispatch-Id=`P1-ENG-LOOP-002-全套清单再核清-20261008T182434Z-9c66`。对象为实现派发「全套清单补正」提交中的 Ops 交接§14.6改行与§14.8；合同为上节「合批进度与全套清单核清」§2末段及§3–4。只读提交diff、相关源码、既有日志与ls/stat/du元数据；未测试、探测、SSH、启板、Play、加载模型、回放、下载或装包，未改实现。consumed=none；本轮不是D/C/R、不签独立复核、不改AC或用户原话账本。

### 1. SUITE-LIST-1裁定：满足披露要求，可转呈首签

补正已把「本项正式评分/独立归档回放0」与「既有测试内数据使用非0」分开；§14.8 B逐项列测试、来源根、执行/skip条件、用途、每全套次数、静态字节依据及UNKNOWN，D列临时目录、短AF_UNIX父目录和仓库内短暂写入，E明确日志2MB不覆盖临时增长。原discover命令、Air系统python3、每候选1次/最多3候选、15min/次、日志2MB申请值不变；没有通过删测试、移归档、改库门把读取凑为0。**SUITE-LIST-1闭合仅表示清单披露满足，不是运行通过、稳定自证或额度签发。** 最终呈报清单为交接§14.6、§14.8 A–E及本节§2–3的接受读法；原「暂不呈」入口由本节替代。

| 核清项 | 只读依据与主张边界 |
|---|---|
| 真实归档读取/临时复制 | 重读 `test_dist_data_driver.py::_formal_root_snapshot/ArchiveS2Case/CrossValidationTest`、`test_dist_data_round8.py::ArchiveCopyCase/ScenarioBindingTest`、`test_dist_data_inventory.py`、`test_dist_data_round4.py::RealArchiveClosureTest`：导入快照与测试末快照两遍；先复制再skip/ERROR；只枚举与读字节/副本有区别。原反例已被B1/B2/B3纳入。 |
| 其他已有数据路径与条件 | 对照 `test_dist_data_layout/projection/pixels`、jet relay/track responder及 `common.a7_frames_dir`、selector冻结资产、SFT冻结收据、preflight子进程指纹路径。a7测试内replay/回环属于B中的非0数据使用，不计作另行独立回放0项。库门静态推断不能冒称实测skip或模型加载0；B4门变化后的新读取不自动放行。 |
| 数量与峰值 | 本轮stat核实现列为最大快照成员的文件为515,074,557 B，du核dist-data约3.15百万kB；provider、probe与M3帧根存在，旧M3/RATE runs和数据根不在，系统python路径/site列表与补正相符。B2-9约6.45GB只是已识别快照读取量，不是全套总读量上限；≥515MB只是单缓冲下界。B1的约7.55MB只覆盖已识别副本，build_layout等生成量UNKNOWN，不能当单例或全套完整峰值上限。其余静态数沿实现表作申请依据，未逐字节复算、未实测。 |
| AF_UNIX与短暂写入 | 重读 `DiagTestBase/DiagTests/DiagControlPathTests`、`play_ops.py::DiagControlDir.allocate/release`及m3工具/scene006 trace测试：c*/el2d-*临时父子目录、后缀探针/套接字、主树测试临时JSON已披露；退出清理不推出峰值0，强制中止残留亦不能忽略。 |

**对§14.8 E末段的限缩**：不能把与清单相关的六条旧失败全部归为旧M3/RATE runs缺失。既有 `-ops-r1rework-tests.log` 中 `test_zero_unmatched_and_zero_multi_matched_jpg` 首报的是 `runtime/frames/` 未匹配图像路径；源码按全树图像模式判定，不取决于runs真值缺失。其余五条具名失败/错误与缺少旧runs工件有原日志对应。本轮不签新的失败归因，不改旧日志；这处归因文字按本段读，不影响清单的读取范围闭合。16项今日是否逐名不变仍UNKNOWN，新执行必须逐名分列，不提前判为基线全同。

### 2. 临时磁盘/读量/内存：推荐不另设数值上限，但必须明示许可

推荐用户在同一SUB:1首签中，**明确许可§14.8闭集内既有测试固有的源字节读取/目录枚举、临时副本和生成物、AF_UNIX临时件、D所列仓库内测试短暂写入，以及进程内存使用；总读量、临时磁盘峰值和内存峰值保持UNKNOWN，不另设这三项数值上限**。源归档不改写/删除/移动、不新增读取对象；执行机器/解释器/库门与原套件不变，测试次数和墙钟仍按§14.6限制，不允许额外独立回放、真实评分、额外诊断或探测。此为待用户选择的明确申请内容，**不是把缺项视为无限额或从日志2MB/B-main/旧额度借用**；若用户只签部分维度，未明示许可的依赖维度仍0，不能执行。

理由：本次是同机既有全套的停点回归，副本范围与生命周期已列明；当前静态数字只是局部量或下界，没有全套峰值依据。接受角色不能把7.55MB/515MB/6.45GB加工成可靠上限，也不应为拍上限先运行未授权探测。按明确测试闭集签其固有使用、维持既有次数/墙钟约束，足以把UNKNOWN如实交给用户取舍，并保持不装包、不扩数据域。

备选：用户要求另设临时磁盘/总读量/内存硬上限，则本申请暂不执行，先由实现零消耗列明申请数值的依据及现有执行方式能否遵守，再经接受核清与用户首签；若需运行测量、改命令/环境/测试或装包，另列范围/额度申请。不得把本轮推荐读成接受已新增或签发这些额度。未来候选如新增数据对象、改变库门/真实模型路径或环境，不以“最多3候选”自动扩许可，先更新清单核清，超出已签范围回用户。

### 3. needs_user（仅用户可首签，当前仍全维度0）

| request_id | 推荐项与理由 | 当前效力/备选 |
|---|---|---|
| P1-ENG-LOOP-002:42979c14:SUB:1 | **按补正清单及本节§2明确读法签发**：Air系统python3/不装包，原discover命令；每候选1次、最多3候选（本候选+至多2个真正返工候选），每次≤15min、日志≤2MB；真实模型加载数UNKNOWN随全套测试用途列明，新增12例零真实模型；既有测试归档读取/测试内回放及临时增长非0，具体域见§14.8，临时磁盘/总读量/内存UNKNOWN且不另设数值上限须明示采纳。仅本机127.0.0.1与AF_UNIX；SSH/板/Play/正式ID/下载/安装/5060/云0；独立归档回放/本项正式评分0；无需新人眼。理由：K4评分调用路径不适用engineering§6窄修替代，补清单后全套才可能补稳定条件②。 | **已可转呈，未签、未放行**；用户可不签（停在进度态），或要求另设三项硬上限（按§2备选补申请）。旧SUB:1/N-1耗尽、用户评分3不涵盖新全套；接受/supervisor均无首签权。 |
| P1-ENG-LOOP-002:DIAG:RETRY:1 | **保持「SUB3核清与评分上限落实」§5原推荐与完整申请**：新合批独立通过消费后另签一次P1新入口诊断及本人新窗口，核真实SSH监督/身份/Unity链路与收尾；理由是替身/本机AF_UNIX不证明真实条件。 | 仍待用户，不代答、不落实、不复活旧SUB:3余额；全套首签不连带诊断。备选暂不追加；以后签发仍须单独合同落实、代码通过消费和现场前提。 |

### 4. 后续门与保留义务

下一动作仅见状态板交接行：用户首签并在答复会话逐字入账→接受落实最终清单/范围→实现按签执行全套并逐名分列旧/新增失败、处理已知失败后补四条件→成立才交C8@OpsScoreDiagK1K4及新鲜独立R1。未满足条件不交C/R；同候选失败、中止不免费续跑，不以文档变化凑返工候选或挪用旧余额。

Overall=REWORK_REQUIRED、Lifecycle=ACTIVE；DIAG-CONTROL-1/评分≤3仍IMPLEMENTED、未全套/非稳定/未独立复核，旧Ops R2及归因/计数/R1-5 OPEN保持。本轮无新AC、finding、block/release、设计或里程碑证据。真实板/Unity未验证；正式G1–G5/Air原件环境/现场登记/AC-18、AC-14/15/18及AC-16正式板端NOT_RUN，无UNITY_NA/DONE；旧终局冻结集/债/诊断偏差/UNKNOWN/ACQ暂停保持。

open_items: none

## 全套与诊断签发落实（2026-10-08，Acceptance）

requested.round=`全套与诊断签发落实`；Dispatch-Id=`P1-ENG-LOOP-002-全套与诊断签发落实-20261008T184957Z-ec5c`。本轮落实已入账用户签发，范围仅本提案与状态板；不是D/C/R、不改AC或核对表、不签独立复核。未运行测试/探测、SSH/板/Play/模型/回放/下载/装包，未改代码、测试、工具、配置或用户原话账本，consumed=none。

### 1. 唯一签发来源与逐维度核对

来源为 `docs/authorizations.md` 顶部「2026-10-08 P1-ENG-LOOP-002 — 用户按推荐签发新全套 42979c14:SUB:1 与新诊断 DIAG:RETRY:1（supervisor 会话代录）」。已核该条、上节「全套清单再核清」§2–3、「SUB3核清与评分上限落实」§5，以及 `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md` §14.6/§14.8 A–E。

**裁定：两项均已由用户签发，额度及执行限制逐维度一致；全套可交实现按签执行，诊断尚不能执行。** 账本明示采纳全套§2临时增长读法，诊断按§5完整表引用的维度包含测量/HTTP/runtime/传输和全部0项，不把账本摘要的省略读为额外许可。诊断原推荐的“通过消费后再签”在本次用户明确签发下，落实为**现在签发、执行推迟至全部前提齐备**：通过消费、合同与机读绑定、现场核和本人新窗口均未豁免；本轮未发现须用户更正的维度冲突，不自行更改账本。该读法不构成合批通过或实际运行放行；用户仍可更正为“通过后再签”。

本节替代前两节及Ops交接§14.6/§14.8中两项“未签0/待首签”的当时效力；原申请、披露、旧负结果与限制保留，不回写原证据。新额度分别独立记账，旧SUB:1/N-1/SUB:3余额不复活、不同用途不转用；B-main/N-3及其正式放行前提不变。

### 2. 42979c14:SUB:1最终执行清单（已签）

完整request_id=`P1-ENG-LOOP-002:42979c14:SUB:1`；执行闭集为Ops交接§14.6、§14.8 A–E，按「全套清单再核清」§1的归因限缩及以下最终读法执行。

| 维度 | 已签执行值 / 范围 |
|---|---|
| 目的/机/解释器 | 新合批 `OpsScoreDiagK1K4` 停点全套，覆盖AC-10修订7/8及既有Ops/AC回归；MacBook Air现有系统 `python3`、不装包、不换环境/库门/数据域；执行检出为候选提交、工作树干净。 |
| 命令/输出 | 原 `python3 -m unittest discover -s tests > docs/evidence/P1-ENG-LOOP-002-score-diag-fix-tests.log 2>&1`，随后只回显该日志末3行，不带 `-v`；保留测试退出码与完整原输出。后续真正返工候选的原输出分文件保留，不覆盖前次结果。 |
| 次数/候选 | 每候选1次、最多3候选（当前合批候选+至多2个真正返工候选）；失败、超时、中止均计当次，不免费重跑、不以文档变化凑候选。本轮未运行，新信封尚未消耗。 |
| 墙钟/日志 | 每次≤15min，证据日志≤2MB；日志上限只限日志，不冒充临时增长上限。 |
| 模型 | 新增12例真实模型加载0；既有测试每次全套实际加载数UNKNOWN，按其测试用途如实列明，不把库门静态推断或旧数当实测0，不增加独立加载/探测。 |
| 数据 | 本项正式评分/独立归档回放0；既有测试内读取/枚举/临时复制/测试内回放非0，限§14.8 B/C逐名来源与用途，不新增读取对象。源归档不改写/删除/移动；不对正式或诊断归档调用本项评分，不写本项正式输出根。 |
| 临时增长/读量/内存 | **用户已明示许可**§14.8闭集内固有源字节读取/目录枚举、临时副本和生成物、AF_UNIX临时件、D所列仓库内测试短暂写入及进程内存使用；总读量、临时磁盘峰值、内存峰值UNKNOWN，三项不另设数值上限。这是已签有限测试闭集的许可，不是缺项无限额；6.45GB/7.55MB/515MB仍仅局部量或下界。按清单逐例清理，强制中止残留如实报告、不因最终清理记峰值0。 |
| 网络/设备/其他 | 仅本机127.0.0.1与AF_UNIX；SSH/板/Unity/Play/正式scenario/session/run ID/下载/安装/5060/云0；无需新人眼，SUB:2本人呈现不变记录及UNKNOWN携带。 |

未来候选新增数据对象、改变库门/真实模型路径/环境或超出次数/墙钟/日志上限时，先停、更新清单交接受核清，越出已签范围回用户；最多3候选不自动扩域。§14.8 B4门变化后的新读取仍不自动放行。源归档不为凑skip而挪走，套件/命令不为凑绿而删改。

### 3. DIAG:RETRY:1签发及执行前提（已签、未放行）

完整request_id=`P1-ENG-LOOP-002:DIAG:RETRY:1`；「SUB3核清与评分上限落实」§5完整申请表现按签发转为以下执行合同，原IR-OPS-5、四STOP/DIAG_FAULT/非0停依赖及非证据用途保持。

| 维度 | 已签执行值 / 范围 |
|---|---|
| 机/执行人/入口 | 同一MacBook Air现有.venv-yoloe与Host Jetson Orin Nano 8GB Super，现有模型/解释器原样；沿IR-OPS-5生产入口，代理/脚本仅前台机械步骤；用户本人Play/停止、发送/跳过、确认/拒绝与反馈。 |
| 次数/剧本/墙钟 | 独立整批≤1、P1固定，无免费重试；完整≤2700s，含准备/源码同步/等待/测量/Play/中止/收尾，等待不清零；必须用户本人另给新在线窗口。 |
| SSH/服务/模型 | 主连接尝试≤2，失败也计，同会话有限通道/释放；板服务启动≤1（含拒启）、GGUF加载≤1、故障重启0；measure与Play共用一次驻留，YOLO加载≤1。 |
| 数据/测量/HTTP | 本次smoke32行读入；生产measure≤1（3预热+32计时）/k-receipt≤1，失败不续依赖；仅诊断根。HTTP/payload沿既有budget=None用途粗账，不借正式335/200/60MB额度，仍受原16次result/软硬截止及墙钟/磁盘约束；真实归档回放/评分0。 |
| Play/标签/runtime | 本人Play≤1、诊断会话≤1；正式scenario/session/run ID0；diag-标签、独立session/段根，不改采样/N-5/指令/阈值；共享槽互斥，原runtime残留只hold/归位。 |
| 两端峰值/同步 | 板独立新诊断根新增≤200,000,000B，Air新增≤250,000,000B，含短私有套接字临时目录/缓存/日志/图像/hold/移动产物，计峰值而非末次du；仅既有16部署源码/config及本次诊断输入同步，完整传输受墙钟/峰值约束。按诊断页固定模式每批新根不覆盖，短临时件归属/清理映射须核。 |
| 明确0项 | 停点全套/真实归档测试回放、5060/云/外部模型API/另列GPU·h、下载/pip/安装/编译、新设备、模型/二进制/库/轮子传板、跨机代理复制、系统/SSH/沙箱设置变更、Unity代码/新正式ID均0。 |

**执行前提逐项保持，缺任一项即不执行：** 新合批代码独立复核通过且被接受消费；唯一签发入账及新request_id/合同/机读绑定落实；干净执行树、HEAD对应通过代码、PLAY_GOVERNING空diff、最新有效通过与全局blocks/releases核；现场核Air↔板认证/HTTP、端口/残留、板身份/资源、前台中断/释放及共享槽；用户本人新在线窗口。当前真实链路与Unity闭环仍未验证，不以签发承诺其通过。

本节已落实新诊断**资源/用途合同**，不宣称执行入口或机读放行已就绪。原 `sub3_release` 只对应旧通过代码及耗尽SUB:3，不能作为新许可/新合批消费标记；不得改名旧许可或复用旧账续跑。按原§4，新request_id的入口适配/账本绑定须另走具名合同答复；新消费标记只能在未来接受消费新范围有效通过轮时，由同名复核机读行运行时解析、程序写入，不能手抄SHA或本轮预写实际放行行。实现若需适配，先具名提交绑定方案/修改闭集与验证停点供接受裁定，不在本轮全套交接中顺带改绑定代码或启动诊断。

### 4. 后续动作、needs_user与保持项

Implementation下一交接仅执行§2当前候选一次全套：按签保留原输出/退出码/资源与清理记录；逐名对照 `docs/evidence/P1-ENG-LOOP-002-ops-r1rework-tests.log` 的16项历史失败，分列本次仍现、未再出现/未执行、新增失败及归因依据。不能把zero-unmatched归为旧runs缺失；全套不绿不等于本增量失败，也不能预签16项相同。闭集外、Ops相关或无法归因的新失败先停交接受，已知本范围失败先修复聚焦复测，真正返工候选仍按本信封每候选1次/最多3候选，额外同候选重跑须回用户。

按逐AC指针在原Ops交接本停点具名节补workflow§4.3.1四条件、完整候选diff与未在真实条件下验证的风险。条件不成立只交进度/清单；成立后提交推送、停止依赖实现，再交接受下一实际C轮（预期C8@OpsScoreDiagK1K4，运行时核连续计数）与新鲜独立R1。本轮不提前裁定稳定条件②满足，不开C/R或消费新通过。

| request_id | 推荐项与理由 / 当前状态 |
|---|---|
| P1-ENG-LOOP-002:DIAG:RETRY:1:WINDOW | **合批通过消费、绑定与现场准备齐备后，由用户本人给新在线窗口**；此前“现在”仅属于旧SUB:3，不延续到新诊断。目前窗口未给，此项不阻断全套交接、不要求重签已签额度。 |

Overall=REWORK_REQUIRED、Lifecycle=ACTIVE保持；旧Ops R2 PASS/归因/计数、R1-5 OPEN、旧终局冻结集/债、SUB:2本人记录/UNKNOWN、旧诊断偏差/UNKNOWN及ACQ暂停保留。正式G1–G5/Air原件环境/现场登记/AC-18未闭，AC-14/15/18及AC-16正式板端NOT_RUN，B-main/N-3已签不等于正式放行，无UNITY_NA/DONE；诊断不进正式或里程碑证据。交接Owner/status只见状态板；本轮仅新增签发效力，无新设计或里程碑验证结论。`open_items`仍只计设计退修残留，不把未齐执行前提记作已闭。

open_items: none

## C8@OpsScoreDiagK1K4核对（2026-10-08，Acceptance）

requested.round=`C8@OpsScoreDiagK1K4`；Dispatch-Id=`P1-ENG-LOOP-002-C8@OpsScoreDiagK1K4-20261008T190620Z-54d8`。owner=Acceptance；范围为本提案核对表/本节及状态板本项。仅只读源码、完整diff、证据与元数据，未测试、bind预核、SSH/板/Play/加载模型/回放/下载/装包，未改实现/AC/复核文件/用户原话账本；consumed=none。

### 1. 候选、完整diff与归属

对象由Ops交接§15的「签发全套执行」Dispatch-Id关联提交及git log唯一实现提交运行时解析；代码树沿§15.1/15.3登记解析。全量基线是同名复核最新有效passed_candidate（R2@OpsK1K2K3K4）；两者为当前HEAD及origin/main祖先。全量diff **16路径、+1961/−51**，候选到开工HEAD仅调度日志4行，PLAY_GOVERNING及三操作单空diff。完整diff、各新增/被替换正文及指针均已核读，不将中间角色文档排除。

| 路径闭集 | 归属与核对 |
|---|---|
| tools/eng_loop2/play_ops.py、summarize_ops.py；tests/test_eng_loop2_play_ops.py、test_eng_loop2_summarize_ops.py；diagnostic-smoke-ops、play-ops两页 | 全部6个PG变更路径；对应已冻结增量§4、AC-10修订7/8。mini-ops-prep零diff可携带，operator_web/原评分/controller/Assets/config/部署路径/环境/基础设施零diff；未改采样/指标算法。源码落点与测试闭集见Ops交接§14.1–14.5。 |
| OpsK1K2K3K4-handoff、score-diag-fix-focused.log、score-diag-fix-tests.log | 实现证据；含§13诊断指针、§14修复/清单及§15执行/四条件。诊断仍非证据，只判修复合同来源；全套644行/43,316B原输出完整读取，focused22行摘要完整读取。 |
| authorizations、implementation-status、phase1-single-drone-design、同名提案 | 已提交接受消费/记债/修复合同/清单/签发与用户答复的文档变化；授权三条来自supervisor代录，R1-5 OPEN等旧义务未销。正式设计的旧“未全套/未签”快照不作为当前执行入口，以本节和签发落实为准。 |
| 同名review、current-status、supervisor-dispatch.jsonl | 已提交独立R2记录、逐批状态与派发日志；非本次实现角色新签verdict/授权。R2完整轮次已读，旧计数/通过范围按当时规则携带。本轮四项披露还核读其finished.report，不替supervisor改日志。 |

直接关联重读：SshUnit.open/_check_and_claim/channel_argv/chan/chan_popen/close、tree_bytes/DiagAccount、DiagnosticRun.prepare_board/allocate_control/start_service/air_reading/closeout/_close_connections/_release_control，以及take_score_call/run_score/cite_score/summarize失败出口；测试长根夹具/真实bind替身/DiagTestBase及新增7+5例全文。测试原输出只证明实现者观察，本轮没有重跑或独立红绿核实。

### 2. 四条件与实现证据判读

| workflow §4.3.1 | C8判读 |
|---|---|
| ①范围/接口冻结 | 满足；增量§4及6个PG路径一致，无新绑定/诊断许可适配；C8-1是既有操作页合同的文字不符，不增AC。 |
| ②相称测试 | 满足本机实现者测试义务；已签全套1次/2474例，旧16项逐名同、新增0，12例修前8F+4E/修后OK、focused156 OK指针齐；不采用§6免全套、不记全套PASS。 |
| ③已知Unity失败/人眼 | 没有本候选已知Unity失败待修；operator_web及呈现路径相对R2零diff，R2 §4附议与本人两张一致原样携带，无须重看；真实Unity仍未验证。 |
| ④候选/状态/复核入口/风险 | Ops交接§15登记齐，风险§15.4如实后置；本轮纠正状态板失效时态。操作页C8-1未闭，暂不转R1；不由接受角色给REVIEW_BLOCKED。 |

只读复算FAIL/ERROR完整名称集合：新旧各16项、双向差集均空，原输出为3F/13E/54skip。10项numpy/cv2库门、5项旧runs工件/真值缺失有原日志对应；zero-match1490及首报五条与旧输出逐字相同、枚举代码/runtime零改，限于旧运行时树状态，不偷归为旧runs缺失、不签更深来源根因。Ops四模块无skip装饰且失败集无命中，12新增用例已执行/通过与总数增12相合。

### 3. 四项披露裁定与记账

1. **两空目录：保留UNKNOWN，不删未知件。** 本轮仅lstat/list核二者仍为空、各目录项64B、uid为本用户，mtime与§15.1一致；归属具体测试、是否由全套造成仍UNKNOWN。内容0B不等于增长0或清理齐备；保持§15.1/15.4原指针与未闭归属，不以此假报峰值0。全套正常退出不能把它们写成“强制中止残留”；也不能擅删或重跑探测以查归属。此项不否定12例/全套失败集合证据，无已核额外模型/板/ID消耗。
2. **Implementation列更新：权限内事实同步，超出派发列明写入范围。** 本项IMPLEMENTED/全套实账是实现职责；提交只改该列事实，Overall/Lifecycle/verdict未改，不是自签门或复核。但派发限定交接行+Log，修改仍应如实列为派发范围偏差；自检pass不抹去偏差。该事实值保留，本轮仅将“待C8”更新为实际首退。
3. **Current state失效时态：本轮就地修正。** “已签待执行/未全套/四条件仍待”不符合已完成§15；现按本候选全套1/1、C8首退、未复核及残留/偏差写回，保留旧SUB:1/N-1/SUB:3耗尽与新信封区分。
4. **套件外bind预核：越出已签用途闭集，不追认授权。** 「全套清单再核清」§2明确禁止额外诊断/探测，「全套与诊断签发落实」§2仅许可原discover及§14.8固有测试使用。127.0.0.1/AF_UNIX是允许的网络类别，不能单凭类别或零模型/零归档把一次套件外环境探测变成测试内许可。本轮按实现披露记**独立本机预核1次/未获该用途授权**，不计为第二次discover、不改全套本候选1/1、不扣或复活旧信封、DIAG:RETRY:1或正式余额。其起止/墙钟/临时峰值、具体原输出及与两目录的关联缺证，保持UNKNOWN；442.26s和1,044,905,984B仅属全套，不能覆盖预核。零模型/零归档按实现披露携带、不冒称独立插桩实测。偏差记录落本节并引用原§15.1及finished.report，不代写用户账本或签事后许可；后续套件外预核不得重复，确需执行先另列范围/清单回用户首签。

全套实账保持新42979c14:SUB:1第1候选一次已耗、本候选余0；另外至多2个真正返工候选未用，不以本轮文档纠正凑候选或重跑。两空目录/真实加载/读量峰值UNKNOWN与原负结果保留。以上范围偏差不是本轮新增独立finding或机械归因统计。

### 4. 唯一退回项及预复核关注

**C8-1（AC-10修订7，不满足）：** `docs/evidence/P1-ENG-LOOP-002-play-ops.md` §12本批新增句“账本缺失/不可读/计数非法即拒评”与 `summarize_ops.py::take_score_call`（不存在文件时初始化formal_score_calls=0）及三归档首次调用生产测试相反。要求仅把该短语纠正为“账本文件不存在时首次从0建立；已存在的账本不可读/缺计数键/计数非法即拒评，原账继承不重置”。不得因纠正文档删旧账、重置计数或把代码改成首轮一律拒评；不改N=3、原键、原评分函数/采样或诊断绑定。这是履行既有同步说明义务，不增合同、finding分级或额度。

待新鲜独立Review核实的主张（不构成本轮新增退回项）：
- PR-C8-1：`DiagControlDir.verify`只核类型/uid/权限，没有记录/比较初建目录的dev/inode；“目录被替换即拒绝”的实现说明比现代码判据宽。请按已冻结私有目录归属域判断同用户同权限替换是否可达，及release是否会删除非本对象原目录；接受不自分级、不扩威胁模型或要求实现顺带修码。
- PR-C8-2：`DiagControlDir.bytes/DiagnosticRun.air_reading/_release_control`及探针分配→占额→收尾各路径的峰值/UNKNOWN、异常时残留不删、check/通道/exit同ControlPath需独立核；真实OpenSSH/板未实跑，不能据本机替身消费为真实验证。
- PR-C8-3：全套原输出有unclosed file及subprocess仍运行的ResourceWarning；两空目录归属与预核用量UNKNOWN均原样保留，不据其推断新代码缺陷或进程已核清退出。

### 5. 后续范围与保持项

本新停点首次核对，**退回计数1/1**，R1尚未开。下一实现只做C8-1操作页文字纠正及必要交接/证据同步（保留原输出与代码），提交推送后停止依赖动作→下一实际C轮（预期C9@OpsScoreDiagK1K4，运行时核连续计数）。纯文字纠正不凑真实返工候选、不重跑全套；不得以本轮为任何测试/预核/模型/SSH/Play许可。若需改代码或新增范围，先按原合同具名待裁定，既有签发边界不扩。

第二次C核对无论残留是否全闭，按每停点首退≤1附最新表/关注项交**新鲜R1@OpsScoreDiagK1K4**；复核入口仍同名review文件。范围是从最新有效passed_candidate到纠正后证据候选的**完整diff**（含6个PG路径与文档角色归属），AC-10修订7/8、本地测试/四条件、旧范围携带及红线，不只看文字补丁；候选沿届时交接/git解析，PG非空才开轮，四条件不成立由Review给REVIEW_BLOCKED不开轮。复核focused一次+具名红绿、工作树独立、原返工上限/冻结集/全局blocks规则不变。本轮不提前签R1资格/verdict或实际放行行。

Overall=REWORK_REQUIRED/Lifecycle=ACTIVE、旧Ops R2 PASS/归因/返工1/2止、旧K停点终局/冻结集/R1-5 OPEN及其他债、N-5/K/T、ACQ暂停和旧诊断偏差/UNKNOWN保持。DIAG:RETRY:1已签但通过消费/新入口绑定/现场核/本人新窗口未齐，仍不放行；正式B-main/N-3已签亦不等于G1–G5/Air原件环境/现场登记/AC-18完成。AC-14/15/18及AC-16正式板端NOT_RUN，无UNITY_NA/DONE。无需当前用户新决策，窗口仍按原WINDOW题后置，不重问已签额度；owner/status唯一处见状态板。open_items仅记设计退修残留（本轮未开D）；具名核对退回项为上节C8-1。

open_items: none


## C9@OpsScoreDiagK1K4核对（2026-10-08，Acceptance）

requested.round=`C9@OpsScoreDiagK1K4`；Dispatch-Id=`P1-ENG-LOOP-002-C9@OpsScoreDiagK1K4-20261008T191758Z-2bde`。owner=Acceptance；仅核对本节/最新核对表与状态板本项事实。Git提案提交主题及历史小节连续C1…C8，最新已完成为C8；本轮实际C9，与派发一致。本新停点是第二次C核对、首退1/1已用；没有开D轮或签R轮结论。只读完整diff/直接关联代码/原日志/元数据，未跑测试、bind预核、SSH/板/Play/加载模型/回放/下载/装包，未改实现/AC/复核文件/用户原话账本；consumed=none。

### 1. 纠正后证据候选与完整范围

候选是Ops交接§16的C8退回纠正派发**唯一实现提交**，以该Dispatch-Id关联play-ops文件的git提交运行时解析（不是本轮接受文档提交、调度登记或后续HEAD）：

```sh
git log --format=%H --fixed-strings --grep='Dispatch-Id: P1-ENG-LOOP-002-C8退回纠正-20261008T191546Z-376a' -- docs/evidence/P1-ENG-LOOP-002-play-ops.md
```

基线取`docs/reviews/P1-ENG-LOOP-002.md`最后一个有效、独立行的`passed_candidate:`值（R2@OpsK1K2K3K4，须核其轮次verdict与有效性），不取文档内引用或round_candidate。本轮解析两端均为开工HEAD及origin/main祖先；候选到开工HEAD仅supervisor-dispatch.jsonl登记/核销，PG与三操作单均零diff。纠正提交仅play-ops§12、Ops交接§16及current-status事实同步三路径，代码/测试零diff。

**复核范围为该有效通过候选→上述纠正后证据候选的完整diff，16路径、+2061/−74。** 全部2537行diff及被替换正文已读，范围不缩为此次短语补丁。归属按C8§1四组：6个PG路径（play_ops/summarize_ops及对应两测试、diagnostic-smoke-ops/play-ops两页）；Ops交接/focused原摘要/全套原日志；authorizations/implementation-status/design/提案的已提交合同与接受记录；review/current-status/supervisor日志的复核与派发事实。中间C8核对与纠正均计入完整diff；mini-ops-prep、operator_web、原analyze_play、controller/Assets/config/部署清单/环境/基础设施零diff，无新绑定或授权适配。

直接关联代码重读C8§1所列SshUnit、DiagAccount/tree_bytes、DiagnosticRun准备/ControlPath分配/计量/服务/收尾，以及take_score_call/run_score/cite_score/summarize失败出口；测试RepoFixture/RepoTestBase、DiagTestBase长根/真实AF_UNIX替身、新增7+5例和评分夹具。全套644行原输出及focused22行摘要读全，supervisor对应finished.report亦完整核读；不剔除ResourceWarning或披露。只读复算新旧FAIL/ERROR名称集合各16、双向差集空：2474例、3F/13E/54skip，对照旧2462例同集；zero-match1490及首报五条沿C8§2原判读，不签额外根因。

### 2. C8-1闭合与最新核对表

play-ops§12现逐字区分“账本文件不存在时首次从0建立”与“已存在的账本不可读/缺计数键/计数非法即拒评，原账继承不重置”，空格不改变读法。`take_score_call`不存在文件初始化0；已有非dict/缺键/布尔/小数/负数/不可读拒评，先写扣次再调用，失败沿原账继承；已有score输出不调用。文字与代码、五例生产入口证据对准，**C8-1闭合，AC-10修订7改为满足**。未修改N=3、原键/函数/采样/诊断绑定、未删账/重置，纠正文档不凑返工候选或重跑全套。

| workflow §4.3.1 | C9核对（供Review独立确认，非独立verdict） |
|---|---|
| ①范围/接口冻结 | 增量§4/AC-10修订7/8与6个PG路径一致，C8-1同步义务已闭合，无新合同。 |
| ②相称测试 | Ops交接§14.2–14.5/§15.1–15.3逐AC证据齐；12新增修前8F+4E、修后OK、focused156 OK；已签停点全套本候选1/1、新增失败0，仍非全绿。C9不重跑或使用§6免全套。 |
| ③已知Unity失败/人眼 | 沿C8§2与同名review R2§4附议携带；呈现路径零diff，无本候选已知Unity失败待修；真实板/Unity仍未验证。 |
| ④候选/状态/入口/风险 | Ops交接§15四条件自证/逐AC指针与§16纠正齐；状态板失效时态就地更新；C8§3披露、§15.4风险与下节关注附送，不签Review开轮资格。 |

最新核对表为本提案固定Contract conformance节；其余AC代码侧携带与AC-14/15/16/18后置缺证保持，未追加BC/AC或把后置缺证转成本次新增退回。旧全套负结果、16项失败来源限制、全套实账与另外至多2个真正返工候选未用量保持C8§2–3；本候选全套余0。

### 3. 随表交付的预复核关注与披露

- **PR-C8-1**：DiagControlDir.verify只核lstat类型/uid/权限，未记录/比较初建目录dev/inode；“目录被替换即拒绝”说明更宽。请按冻结私有目录归属域核同用户同权限替换是否可达、release是否会删非本对象原目录；不扩威胁模型，接受不自分级或要求顺带修码。
- **PR-C8-2**：独立核DiagControlDir.bytes、DiagnosticRun.air_reading/_release_control及分配探针→占额→异常/正常收尾的峰值与UNKNOWN、残留不删、check/通道/exit同ControlPath。真实OpenSSH/板未执行，本机替身不能代真实验证。
- **PR-C8-3**：全套unclosed file及subprocess仍运行的ResourceWarning、两空目录归属UNKNOWN、套件外预核用量UNKNOWN原样保留；不推断进程已核清退出或签新代码缺陷。

C8§3四项披露裁定原样有效：不删未知目录、不以内容0B报增长/峰值0、不抹派发写入范围偏差、套件外bind预核1次不追认授权/不充套件/不转扣信封。预核起止/墙钟/临时峰值及具体原输出缺证仍UNKNOWN。Current state中“C8首退待纠正”改为已闭合/合批未复核；Gate board仅同步本项证据文字，不变门值。活跃交接实际0条消耗性/2条零消耗，纠正Immediate next actions旧1/1计数，未恢复暂停项。未核新的设备/模型/ID消耗或清理事实。

### 4. 照交新鲜R1与停止边界

按C8§5及workflow§4.3.3首退≤1，本轮**不再次退回实现，交新鲜R1@OpsScoreDiagK1K4**；owner/status与接手动作唯一处为状态板交接行。Review须以新鲜上下文在一次性worktree核§1运行时解析的候选及完整diff，读最新核对表/C8§3/C9§3、既有合同与旧范围携带，独立确认PG开轮资格和四条件；不成立则REVIEW_BLOCKED不开轮。复核按focused一次+每条阻断finding红绿一次纪律，未签任何SSH/板/Play/模型/回放/下载/装包额度；发现缺陷只写复核文件、返还实现，接受不修实现、不签finding/verdict或passed_candidate。

Overall=REWORK_REQUIRED/Lifecycle=ACTIVE、旧Ops R2 PASS/返工1/2止/归因、旧K终局冻结集与R1-5 OPEN等债、N-5/K/T/ACQ暂停、诊断偏差/UNKNOWN保持。合批实现仍未独立复核，依赖其结果的实现与消耗停止。DIAG:RETRY:1已签但新通过消费/入口绑定/现场核/本人新窗口未齐，继续未放行，不写新sub3_release；WINDOW题按原约定后置，本轮needs_user=[]。正式B-main/N-3已签不等于G1–G5/Air原件环境/现场登记/AC-18或AC-14/15/18、AC-16正式板端完成，仍NOT_RUN，无UNITY_NA/DONE。open_items仅为设计退修残留计数，不表示独立关注/正式缺证已闭。

open_items: none


## R1通过消费与新诊断前提盘点（2026-10-08，Acceptance）

requested.round=`R1通过消费`；Dispatch-Id=`P1-ENG-LOOP-002-R1通过消费-20261008T193602Z-1bc7`。本轮消费最终通过、机械归因及执行前提盘点；不是D/C/R、不增改AC、不重新做常规候选检查、不签独立复核。范围仅本提案（含最新核对表）、implementation-status及current-status；consumed=none，未运行测试/探测、SSH/板/Play/模型/回放/下载/装包，未改代码/测试/工具/配置或用户原话账本。

### 1. 通过消费、门值与计数归因

**消费同名复核「R1@OpsScoreDiagK1K4（2026-10-08）」§0–5及Verdict的PASS。** 已核复核派发与提交尾注相符、提交只含同名复核及状态板；通过候选由该节唯一独立`passed_candidate:`行运行时解析（不手抄SHA）。只读git来源核实：它是HEAD与origin/main祖先，其后全部PLAY_GOVERNING及三操作单差异空、开工工作树干净；这是通过来源核对，不是第三次代码核对。Overall由REWORK_REQUIRED转为**REVIEW_PASSED**、Lifecycle=ACTIVE，覆盖本合批代码/操作单及旧通过范围携带，不表示诊断或正式运行获准。

| 消费对象 | 采用的证据 / 状态 |
|---|---|
| AC-10修订7/8、DIAG-CONTROL-1 | R1§1–2独立核实代码侧成立；12例修前8F/4E→修后12/12、focused156 OK。具名ControlPath修复已通过本机代码停点，真实OpenSSH/板未验证；正式三归档评分NOT_RUN。 |
| AC-13修订1/稳定条件② | 采用R1§0及Ops交接§15–16：2474例、3F/13E/54skip，16项历史失败双向差集空、新增0；全套仍不绿，不记全套通过。新42979c14:SUB:1本候选1/1用尽，至多2个真正返工候选各1次未用；不能为纯文档变化凑候选。 |
| PR-C8-1…3、SUB:2 | R1§1/§3已核目录归属域、峰值与释放；OSD-R1-1文字补丁见§3。ResourceWarning为既有替身告警，不能据此签全部子进程已退出；两空目录归属、套件外预核越界/用量UNKNOWN保持C8§3。R1§4附议携带本人两张一致记录，提示/用时UNKNOWN，不需重看。 |
| AC-14/15/18及AC-16正式板端 | NOT_RUN/证据缺失；R1§4无UNITY_NA附议，本轮无UNITY_NA/DONE；B-main/N-3已签仍不等于G1–G5/Air原件环境/现场登记/AC-18齐备或正式放行。 |

本停点C2轮（C8/C9）、退回1次（C8-1“不满足”，无新增“证据缺失”退回）；R1轮、REWORK_REQUIRED返工0/2。新复核阻断finding0、RED_LINE0；OSD-R1-1 CLASS_3依据BC-10→**实现错误（非阻断文字）1条，待应用**，与既有阻断实现错误9条已闭合分列，不把文字待办算返工或代码回归。BC缺失/复核标准/核对轮归因新增0，原R1-5 SCOPE_GAP/OPEN及旧归因保持；DIAG-CONTROL-1仍是接受侧具名生产故障归因，不重复计为独立finding。累计AC修订28/新AC0，本轮新增0；旧Ops C6/C7首退1/1、R1/R2返工1/2止、旧K1K3与旧K1K2K3K4终局/冻结集不重置。

### 2. DIAG:RETRY:1执行前提逐项盘点

权威合同仍为「全套与诊断签发落实」§3–4及「SUB3核清与评分上限落实」§5；完整request_id=`P1-ENG-LOOP-002:DIAG:RETRY:1`，本轮未启动、不消耗其任何维度。

| 前提 | 当前盘点 / 缺口与责任 |
|---|---|
| 新合批独立通过并被接受消费 | **已满足**：本节§1消费R1 PASS。 |
| 唯一签发及资源/用途合同 | **已满足**：账本10-08「用户按推荐签发新全套42979c14:SUB:1与新诊断DIAG:RETRY:1」及原落实§3；独立一次P1/原全维度及0项不变，不重签额度、不复活旧SUB:3。 |
| 新入口/request_id及账本绑定合同 | **仍缺**：资源合同已落实，入口适配合同未裁。只读`play_ops.py`的DIAG_REQUEST_ID/DIAG_LEDGER_HITS/stage_diag仍限定旧SUB:3；_refuse_if_consumed按旧request_id守一次账。须实现先提交具名方案、修改闭集与验证停点给接受裁定，不能只改常量/改名旧许可续跑。 |
| 新机读消费/放行行 | **仍缺**：现有DIAG_RELEASE_LINE/preflight只认旧sub3_release，原行仅属耗尽SUB:3及旧通过代码。新键/新request_id与候选的绑定格式未裁，本轮不覆盖旧行、不写新实际行；方案裁定且适配代码通过并被消费后，接受再从当轮有效复核机读行运行时解析、程序写入新标记，不能让实现自签。人类消费结论不替代入口机读前提。 |
| 干净执行树/HEAD对应通过代码/PG空diff/最新通过及全局blocks核 | **本轮来源已核，执行时仍须重核**：开工干净、通过候选为祖先、PG与三页空diff；全局机检按完整reviews与release账本扫描。后续CLASS_3/入口适配会改变PG，当前静态事实不是未来发布放行凭据；不得绕过最新通过/双来源门。 |
| 现场核 | **仍缺、执行时现核**：Air↔板认证/HTTP、端口/残留、板身份/资源、前台中断/同会话释放、共享槽及短临时件归属/峰值映射。本轮未SSH或探测，旧读数/本机AF_UNIX替身不证明现场就绪；按原有限动作与已签整批墙钟记账，非额外免费探测。 |
| 用户本人新在线窗口 | **仍缺、后置**：原SUB:3“现在”已结束；账本新签发未给窗口。绑定、代码消费及现场准备可执行安排齐备后转§4；窗口不能豁免执行时现场核。 |

**结论：DIAG:RETRY:1仍未放行。** 不将入口缺口降为CLASS_3，不把已签资源或R1 PASS当可立即执行。原四STOP/DIAG_FAULT/失败非0停依赖、独立诊断根/非证据、完整墙钟及峰值账保持；真实链路/Unity闭环仍未验证。

### 3. 下一交付范围与OSD-R1-1去向

当前可独立推进的零消耗准备：实现按R1§3逐字补丁，在下一次提交仅替换`DiagControlDir.verify`的一行docstring，不修改判据、数字或执行顺序，不为CLASS_3另开轮；Ops交接§14.3相应叙述按复核指定归属域读法同步。接受本轮不代修、不把待应用记闭合。若后续发生行为变化，不能借本补丁免除K停点。

实现同时在原Ops交接具名小节提出新诊断绑定方案：新request_id对应唯一已签条目/新整批粗账且旧已用记录继续拒续；新机读消费键如何关联该request_id与最新有效通过候选、读取失败/缺行/错值拒启；实际修改文件闭集、操作页/调用格式及fail-closed回归指针；与本停点通过范围的关系、触发的K停点、相称验证及其资源清单。此阶段**只提交方案/逐字文字补丁，不实现绑定代码、不跑测试/探测/加载/回放、不SSH/板/Play**。先回接受具名合同答复；适配涉及入口与门核须走适用C/R，不预签豁免、复核轮号或额外全套。不能自动把现有全套信封未用返工额度移作新适配验证用途；如需资源先列清单核合同，越界转用户。

下一Owner/status只见状态板交接行。本项仍占1条零消耗；全局0消耗/2零消耗，不新增现场/用户并行交接、不恢复暂停项。旧SUB:1/N-1/SUB:3耗尽、旧诊断偏差/UNKNOWN、R1-5 OPEN与其他债、N-5/K/T/ACQ暂停保持。

### 4. needs_user（后置窗口；当前无须再签额度）

| request_id | 推荐项与理由 | 为何只能用户定 / 转呈时点 |
|---|---|---|
| P1-ENG-LOOP-002:DIAG:RETRY:1:WINDOW | 推荐在新绑定代码通过消费、机读标记和现场准备安排齐备后，由用户本人给新的P1在线窗口；理由是本人须Play/停止、发送/跳过、确认/拒绝及反馈，旧“现在”不可沿用。 | 原签发与「全套与诊断签发落实」§3–4逐字保留“用户本人另给新在线窗口”；这属于本人实际在场与Unity动作，接受/supervisor不能代给。先完成§3方案及后续适配，不现在催窗口、不重签已签额度；执行时仍须现场核，窗口本身不是GO。 |

open_items: none

## 诊断绑定方案答复（2026-10-08，Acceptance）

requested.round=`诊断绑定方案答复`；Dispatch-Id=`P1-ENG-LOOP-002-诊断绑定方案答复-20261008T194738Z-9d13`。本轮为实现待裁定方案的合同答复，不是D/C/R，不更新最新核对表、不签独立复核或实际机读放行行。owner=Acceptance，写入仅本节与状态板本项。consumed=none；未测试/探测、SSH/板/Unity/Play/加载模型/回放/下载/装包，未改代码/测试/工具/配置、复核文件或用户原话账本。

来源：Ops交接§17.1–17.6及其具名实现派发提交；本提案「R1通过消费与新诊断前提盘点」§2–3、「全套与诊断签发落实」§3–4、AC-10修订4/5/8及AC-13修订1；账本10-08「用户按推荐签发新全套 42979c14:SUB:1 与新诊断 DIAG:RETRY:1」；同名复核R1@OpsScoreDiagK1K4 §3 OSD-R1-1。只读关联源码核现状，不作完整候选C核对。D4的engineering-v1裁定保持。

### 1. BIND-1…6及BIND-Q1具名裁定

**采纳本方案，按下表限缩/明确后实现；这只冻结新绑定接口，不放行DIAG:RETRY:1。** 已签资源、P1、一次整批、四STOP/DIAG_FAULT/非0停依赖及旧耗尽事实均不变。

| ID | 裁定与执行读法 |
|---|---|
| BIND-1 | 采纳两项冻结闭表。旧完整id、常量名/值、原标题及sub3_release只作历史，status=exhausted；新完整id=DIAG:RETRY:1、status=signed、唯一账本标题片段、release_key=diag_release、playbooks=(P1,)按§17.3。signed只表示资源已签，不是执行许可。DIAG_LIMITS对象及每个数值不改，静态合同断言逐维度核。未知id无入口。 |
| BIND-2 | 采纳旧id代码级无条件拒续，即使旧outputs/粗账不在也拒；未知id/P2/P3在建新根前拒。**实现已指出的_refuse_if_consumed fail-open必须在本绑定候选内修，不留待办、不按CLASS_3处理，也不重判旧复核。** 对扫描到的粗账，读失败/非法JSON/非对象/缺request_id或非字符串身份均干净DIAG_REFUSED diag_ledger_unreadable，不用or {}吞错；同id仅consumed字面false可继续，缺键/null/0/空串/其他非布尔及true均request_consumed。身份可读的其他id账不占新id次数；其读坏仍拒，不能猜是旧账而跳过。建根前拒启不创建新粗账，不消耗；建根后的前提拒启粗账consumed=false。consume在首个受限动作前置位、之后成功/失败/中止用尽的既有语义不改。旧粗账不删改/改id/移根，新账与NOTES/事件/play-record使用新id并记录entry_binding的id、标题行原文、release_key、放行行号/值、门核passed_candidate/rel。 |
| BIND-3 | 采纳诊断preflight追加唯一条目校验，release_gate/正式1.5逻辑零改；从发布引用读账本，按二级标题分条，指定标题片段恰命中一条，其正文须含反引号包住的完整新id。标题在A、id在B/仅WINDOW扩展/0或多标题/读取失败均按§17.3原因拒启，不由全文两子串命中放行。后续撤回/否决仍由未来接受写标记前沿最新账本核清；本机粗账不是授权来源。 |
| BIND-4 | 采纳格式`diag_release: <request_id> <40位小写sha>`，实现正则只认完整id和合法候选值；占位格式、大写/短sha/他id/旧键不计。无本id合法行→missing，有本id合法行但无值等于门核passed→mismatch，提案读取失败→unreadable；不得把发布引用rel当passed。合法行仍不替代release_gate的最新通过、祖先、HEAD、PG/三页空diff、全局blocks/releases及DOCWT自检。实际行仅未来接受消费本绑定候选有效通过后，从复核机读来源运行时解析、程序写入；本轮及实现/脚本不得自签，不转正式G4。 |
| BIND-5 | 采纳现行DIAG:RETRY:1节、唯一P1调用与页首指针更新，原SUB:3节原文保留但明确历史/耗尽；逐项列原合同执行前提、拒启/用尽及非证据限制，实际id以账/NOTES/事件为准。示例只用占位符。--p2-object保留既有冻结计划输入用途，不许可改P1对象池/采样/指令或按诊断表现换剧本。 |
| BIND-6 / BIND-Q1 | **选A，围栏块零改。** 附录3旧SUB:3横幅/编号1文案作为历史标签加说明，extract_block取出的板输入字节不变；编号1与新签serve≤1一致，身份来自Air新粗账/NOTES/事件。B中性化文案本轮不采纳；若以后需要修改板输入，先具名回合同，不顺带实现。 |

BIND-2的机器承诺限当前粗账扫描域及旧id硬拒，不声称能在操作者删除全部新账后恢复新id耗用事实。旧手工无粗账目录不补造、不改归属或追认用量；执行前接受核新id尚未消耗，执行后粗账保留，未知耗用不得靠删除/缺账续跑。共享槽及单写者约定不变，不引入跨进程并发执行许可。

以下源于本次实现待裁定BIND方案，解释已签诊断前提，原合同/旧轮次不覆盖。追加2条修订，累计AC修订30、新AC0；不是核对轮新增义务，也不签独立finding、blocks/release或新资源。

| 编号 | 验收项（追加生效） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 9 | 解释修订4/5的诊断独立路由与机读前提，DIAG:RETRY:1按本节BIND-1…6/BIND-Q1绑定唯一已签条目、有效通过值及P1；旧SUB:3无条件拒续、坏粗账fail-closed、同id仅字面false未消耗；拒启/消费/原流身份及真实条件未验证按本节明确读法。不得自签新放行行或复用旧行/账续跑。 | test: `tests.test_eng_loop2_play_ops.DiagBindingTests`及既有`DiagTests`；artifact: Ops交接本绑定停点逐项自证、诊断页现行节、diag-binding-focused.log | OpsDiagBindK1K2 | 2026-10-08 |
| AC-13 修订 2 | 解释修订1及engineering§6：本节§2闭集窄修，具名focused加§3生产行为修前红/修后绿可替代此候选全套；需完整diff/逐项映射、未全套及旧失败限制声明，复核仍可判替代不足。越闭集/触及加载器、数据划分或对外指标路径先停回接受；新全套需另列用途/逐维度清单由用户首签，不挪用42979c14:SUB:1未用返工额度。 | artifact: Ops交接本绑定停点四条件自证与diag-binding-focused.log；cmd: 完整候选diff（来源运行时解析） | OpsDiagBindK1K2 | 2026-10-08 |

### 2. 修改闭集、K停点与通过范围

冻结停点短名为**OpsDiagBindK1K2**：K1为诊断入口/调用与request_id/放行行协议；K2为一次性守账和fail-closed安全门。此次不触K3模型决策/目标身份、K4数据/评分/对外指标、K5发布；诊断许可身份不是目标身份。若实际diff越界，先回接受重定范围，不借停点名豁免。

实现修改闭集采纳Ops交接§17.4，功能文件只`tools/eng_loop2/play_ops.py`诊断段、`tests/test_eng_loop2_play_ops.py`点名DiagTestBase/DiagTests/新增DiagBindingTests；同步`docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`文字（围栏不改），写原Ops交接新具名停点节、`docs/evidence/P1-ENG-LOOP-002-diag-binding-focused.log`及状态板。诊断段包含diag_start/NOTES/play-record身份记录与help、拒启文案；不改run_offline_summary的评分/摘要调用或算法。其余测试类及§17.4明确不改/闭集外文件保持零diff；若现有测试构造接口必须改动其他类，先具名说明回接受，不自行扩表。实现不写提案/账本/复核/implementation-status。

OSD-R1-1逐字docstring补丁及交接§14.3对应读法已应用，仅记录文字待办履行，不改finding依据/归因或追签代码通过；该tools路径变化随绑定候选完整PG diff携带，不单为CLASS_3开轮。上一通过基线从同名复核最近有效passed_candidate运行时解析；相对基线完整diff包含该行及新绑定闭集。旧R1 PASS已消费且旧Ops/K结论携带，**不覆盖绑定实现**；当前release_gate仍应拒启PG变化。

实现完后按AC-10修订9/AC-13修订2及携带条款写四条件自证、逐项证据/文件映射/完整diff与风险，提交推送并停依赖；再交接受下一实际C轮，轮号沿本项已完成C序列运行时核，不现在开轮；其后新鲜独立复核按有效基线/PG非空与实际轮号开本停点首轮。旧终局/冻结集和旧计数不重置。本轮不改最新核对表、既有复核或implementation-status的当轮记录；现行本答复及状态板同步OSD文字履行事实。

### 3. 相称验证与资源裁定（本轮未运行）

**采纳engineering§6窄修替代，不要求新全套或新增资源首签。** 理由是限定diff只改诊断门、身份记录与调用说明，不触真实模型加载器、数据划分、评分调用/对外指标，板部署闭集零diff，页内板输入围栏零diff；与此前K4评分合批必须全套的情形不同。这是有范围前提的实现验证合同，最终证据充分性由独立复核核实，不预判稳定条件②满足，不记全套通过。

- 本机现有系统`python3`，四模块focused按§17.6命令运行一次，输出写diag-binding-focused.log、只回显摘要、不带-v。临时本地git/bare origin、假SSH/假模型子进程、127.0.0.1/本机AF_UNIX及临时文件均属原AC-13修订1零模型focused用途；不执行真实ssh（含真实ssh -G）、接板、模型加载、真实归档读取/回放、Play、下载/安装/外网/正式ID。旧约200s只作估计，不新造额度或实测结论。现有ReleaseGateTests/正式路径及其他三个模块保持代码零改照跑，验证新诊断参数不改变正式门/评分/隔离。
- §17.5十二个具名用例及既有新id“再次启动拒”作为覆盖清单；补同id缺consumed/null/0/空串和缺身份/非字符串身份、标题与id跨条目/WINDOW扩展的子例。建根前拒启断言rc=3、无新根/粗账、受限动作0；建根后前提拒启断言rc=3、consumed=false、主连接/服务/Play/模型0。不能要求前一种有新粗账，也不能把未捕获异常当正确拒启。
- 回归粗账由真实DiagAccount/消费写盘或生产诊断入口产出，坏JSON/非对象/缺键用在其字节副本上定点破坏；授权/放行格式夹具用临时git文档检出发布，绝不改真实账/写真实放行行。修前/修后各一次仅覆盖所修功能缺口；基线由最新有效通过候选运行时解析，测试保持候选版、工具切回基线，在临时副本内进行。**不接受新API缺失ImportError/AttributeError，或因旧入口不认新id而提前拒启作为_refuse_if_consumed缺口的红证据**：须从生产生成账到真实守账路径，证明旧工具吞坏账/放过非法consumed而新工具干净拒启；接口差异如需桥接，夹具只桥身份/构造，不替写盘/守账函数。原来已拒的未知id等用例可绿绿，分列为保持性覆盖，不伪称十二例都修前红。正向新条目需能走过绑定前提并记完整entry_binding，证明不是一律拒启。
- focused/红绿日志保留原输出、退出码、命令/解释器/用例数与临时件归属/清理说明，写明未跑全套、旧全套16项历史失败/两空目录归属及套件外预核UNKNOWN未重核。零模型替身不证明真实OpenSSH/板/Unity链路，无新增人眼要求（呈现/采集路径不改，原SUB:2附议与UNKNOWN携带）。

若实际diff或独立复核使窄修替代不成立，先停止稳定交付/诊断，不自动跑全套；实现另交具名新request_id及完整申请：机器/解释器、原discover命令与新日志、每候选1次/候选数、墙钟/日志、真实加载UNKNOWN、源读/测试内回放闭集、临时磁盘/内存/读量许可、网络/SSH/板/Play等0项及清理。由接受核清后在needs_user转呈，推荐相称一次候选全套（返工额度另说明），理由为补停点条件②；只有用户能首签新用途/额度，未签0。§17.6备用清单不是现成签发包，42979c14:SUB:1的两个未用真正返工候选不得转用本适配，DIAG:RETRY:1也不覆盖验证。

### 4. 后续顺序、needs_user与保持项

下一步只推进§2闭集实现与§3零消耗验证/自证，交接Owner/status只见状态板。新绑定通过→接受消费并核最新授权/耗用事实、运行时解析写新机读行→安排现场核与本人窗口→在已签一次整批内执行。现场核须在本人新窗口和整批墙钟安排齐备后按原有限动作执行，不能在等待窗口时免费SSH/启板预探；窗口不替代现场/执行树门。本轮不写实际行，不启动诊断。

| request_id | 推荐项与理由 | 为何只能用户定 / 转呈时点 |
|---|---|---|
| P1-ENG-LOOP-002:DIAG:RETRY:1:WINDOW | 推荐绑定代码有效通过被消费、新机读标记与现场准备安排齐备后，再由用户本人给新P1在线窗口；须本人Play/停止、发送/跳过、确认/拒绝及反馈，旧“现在”不沿用。 | 本人实际在场/Unity动作不可由接受或supervisor代给；仅后置窗口，不阻断本次零消耗实现，也不重签已签诊断额度。 |

目前无新增全套/其他资源首签题。Overall=REVIEW_PASSED、Lifecycle=ACTIVE表示旧已消费范围保持，不代表新绑定已实现/复核。旧SUB:1/N-1/SUB:3耗尽、42979c14:SUB:1本候选一次已用与余额用途、旧诊断偏差/UNKNOWN、R1-5 OPEN/N-5/K/T/其他债及ACQ暂停保持；B-main/N-3仍未正式放行，G1–G5/Air原件环境/现场登记/AC-18仍缺，AC-14/15/18及AC-16正式板端NOT_RUN，无UNITY_NA/DONE。

open_items: none


## C10@OpsDiagBindK1K2核对（2026-10-08，Acceptance）

requested.round=`C10@OpsDiagBindK1K2`；Dispatch-Id=`P1-ENG-LOOP-002-C10@OpsDiagBindK1K2-20261008T201446Z-9324`。owner=Acceptance；仅写本提案及状态板。最近已完成C序列为C1…C9（提案、核对证据和git主题交叉核，派发登记不算完成），本轮实际编号与requested.round一致。本停点首次C核对，与旧OpsScoreDiagK1K4的C8/C9、首退及R1计数分开。D4 engineering-v1生效裁定保持；consumed=none，未跑测试/探测、SSH/板/Unity/Play/加载/回放/下载/装包，不写实现、独立复核、用户原话账本或放行行。

### 1. 候选来源、完整diff与直接关联代码

输入为Ops交接§18.1–18.5、diag-binding-focused.log及诊断页现行DIAG:RETRY:1节；合同为「诊断绑定方案答复」§1–4及AC-10修订9/AC-13修订2。代码候选由§18页首的git主题解析；证据候选用`git log --format=%H --fixed-strings --grep='Dispatch-Id: P1-ENG-LOOP-002-诊断绑定实现-20261008T195247Z-a7f3' -- docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md`唯一命中解析。基线取同名review末条有效passed_candidate（位于末条round_candidate之后）并核祖先关系；不手抄派生SHA。代码候选→证据候选→开工HEAD的PG及三操作页diff为空，后两提交只有证据/状态与派发记录。

**相对该基线的完整候选diff共10路径、+1464/−54，全部纳入核对**；未按实现摘要剔除文档/角色记录。PG与操作页共3路径、+487/−44：play_ops.py、对应测试、诊断页。其他7路径为current-status、Ops交接、focused日志、supervisor派发日志、implementation-status、提案、同名review。归属依次为各角色状态、实现方案/证据、supervisor登记核销、接受合同/通过消费、独立复核原始记录；无协调基础设施变更、无新账本变更。controller/Assets/config/ProjectSettings/包锁/runtime、部署16路径、summarize_ops/operator_web/analyze_play、正式play-ops与mini操作页零diff。

直接关联重读release_gate的最新round/pass行序、祖先/HEAD/PG三页/全局blocks/DOCWT门与1.5；MR/extract_block；DiagEntry/闭表、diag_entry_for、diag_ledger_binding、diag_release_binding；DiagAccount写盘/consume、DiagnosticRun建根/守账/preflight/prepare_board首个受限动作/execute/身份记录及独立摘要调用；RepoFixture/RepoTestBase、DiagTestBase/DiagTests/新增13例、闭集外直接构造及继承点。日志559行按用例/子例和失败出口核读，记录的工具/测试blob哈希与git字节相符；旧操作页20个围栏块均在候选原样存在，只新增现行调用示例。OSD-R1-1逐字补丁随完整diff携带，不单为该文字开轮。

### 2. 四条件、逐项映射与证据判读

| workflow §4.3.1 | 本轮核对（非独立verdict） |
|---|---|
| ①范围/接口冻结 | BIND接口已冻结，功能3路径与合同一致；但测试模块级三常量越§2三类闭集，C10-1，不能按“无新待裁定”自证为范围满足。 |
| ②相称测试 | 原日志focused169 OK/rc0/237s；13例修前35F+4E/rc1、修后13 OK/rc0。坏账9子例及consumed缺键/null/0/空串4子例经生产DiagAccount写盘/consume与真实main守账路径；基线仅桥身份/构造，7坏账及4非法consumed放过建根，list/string为未捕获异常，均非提前不认新id或缺新API。4个接口E与新id提前拒的F单列，保持性绿绿不计红证据。未全套，窄修替代因①范围前提不满足尚不可采用；这不是推翻既有日志绿或要求新全套。 |
| ③Unity/人眼 | 无本候选已知Unity失败；呈现/采集及板输入围栏零改，SUB:2附议携带；真实OpenSSH/板/Unity未验证。 |
| ④入口/候选/状态/风险 | §18四条件自证/逐AC指针/风险及候选均齐；本轮更新失效“绑定实现仍缺”时态及首退交接；独立入口仍同名review，新R1未开，不签REVIEW_BLOCKED或通过。 |

| 既有条款映射 | 核对 / 指针 |
|---|---|
| AC-10修订9 / BIND-1 | 两项冻结闭表、旧exhausted、新signed仅P1、旧常量名值和DIAG_LIMITS数值保持；test_retry1_account_records_binding_and_signed_limits独立字面断言。 |
| BIND-2 | 旧id/未知id/未签剧本建根前拒；扫描坏JSON/非对象/缺或非字符串身份干净拒，同id仅is False未用；建根后前提拒留下consumed=false/used0，首受限动作前consume原时点未改。新id粗账/NOTES/事件/play-record与entry_binding正向记录及再次启动拒见§18.3/DiagTests e2e；旧账不改，删除新账后不可恢复耗用的限制保持。 |
| BIND-3/4 | 唯一二级标题正文内反引号完整id；跨条目/WINDOW/重复/读取失败拒；MR完整id及40位小写值匹配门核passed，区分missing/mismatch/unreadable。正向绑定记录标题原文/行号、release_key、放行行号/值、passed/rel，非一律拒启；格式示例不计，未自签真实行。 |
| BIND-5/6 / Q1=A | 诊断页新P1唯一调用/前提/拒启与非证据限制齐，旧SUB:3原文保留且明示耗尽；附录3历史横幅说明不改输入字节。--p2-object不扩大对象池/采样，摘要仅记录id改动、调用/评分算法零改。 |
| AC-13修订2 | 验证和披露指针齐且日志不伪称全套绿；但§2闭集外模块级常量是明确不满足，不以事后披露获得范围许可。唯一首退C10-1见§4。 |

旧全套16项历史失败/两空目录归属UNKNOWN/套件外预核越界及用量UNKNOWN未重核；日志1条既有subprocess ResourceWarning不证明进程全部退出。全局reviews实际blocks/releases逐文件扫描仍仅ACQ R2-1且已配对release，未写新机读行；最终自检仍覆盖完整来源。

### 3. 两处披露、陈旧文字与预复核关注

- **模块级RETRY1/RETRY1_TITLE/SUB3：不满足，C10-1。** tests/test_eng_loop2_play_ops.py诊断节开头三定义位于DiagTestBase之外；合同§2和AC-13修订2明确点名只改DiagTestBase/DiagTests/新增DiagBindingTests，越闭集先停。共享字面目的合理，但本轮不能改闭集或追认越界；将定义及使用收回允许类可完成原合同，无新增义务/资源。
- **DiagAccount缺省旧id：可保留，不构成本次退回。** 该构造函数在允许诊断段内；唯一生产构造点DiagnosticRun显式传self.entry.request_id，stage_diag与__init__都先闭表核，旧id无条件拒续。闭集外DiagAccountTests及DiagControlPathTests的直接构造代码零改，前者历史断言不是执行许可。后者继承允许修改的DiagTestBase而走新夹具是已冻结基类改动的直接作用，不等于修改其类代码或新增真实验证；无需为兼容扩大测试闭集。
- **PR-C10-1（预复核关注，非退回/finding）：** release_gate docstring仍写“诊断=SUB:3签发条目”，函数整体零diff且合同明确禁改；参数实际来自self.entry，新模块说明/CLI/help/现行页均明确新条目。不要求本轮修禁改函数，不自定CLASS/依据；下一新鲜R1按具体可达调用与是否驱动操作判读该陈旧文字。`release_key`虽记录在entry，实际新行正则固定diag_release，与两项冻结表/旧id硬拒一致。
- **PR-C10-2：** 下一R1独立核BIND-2的扫描域/生产写盘红绿与字面False、建根前后拒启资源0，以及BIND-3/4正向绑定和失败分支；不把新增API缺失E/不认新id提前拒误作fail-open红。账本按##分条而不识别围栏同形标题及后续撤回的限制保持；未来接受写标记前核最新授权/耗用，不补造旧账、不清UNKNOWN、不扩威胁域。

### 4. 唯一首退、后续与保持项

**首次退回实现，仅C10-1；本停点核对首退用尽1/1。** 按既有§2/AC-13修订2，将三项模块级测试定义及其引用收回点名类闭集（例如放DiagTestBase、在允许类中引用），维持字面、用例与断言语义，不改生产绑定/限额/正式门，不修改其他测试类。同步Ops交接具名纠正节、完整diff/四条件及新测试树对应的相称focused证据；原红绿保留，工具与生产守账不变时明确哪些结果可携带、哪些夹具字节变化，不把旧测试哈希当新候选哈希。本轮不要求全套、不把现有信封余额改用途；相称验证仍按合同§3，任何越界先停回接受。

纠正候选提交推送并停止依赖→下一实际C轮（沿本项连续序列运行时核；预计C11@OpsDiagBindK1K2）重读完整diff及本表。按每停点首退≤1，第二次不再退回，附最新表/残留关注交新鲜R1@OpsDiagBindK1K2；Review独立判四条件与PG开轮资格，不成立则REVIEW_BLOCKED不开轮。首轮范围是最新有效passed_candidate→纠正后证据候选的完整diff，包含OSD文字和所有文档/日志归属；复核仍focused一次/阻断finding生产路径红绿一次，不获SSH/板/Play/模型/回放/下载/装包权限。Owner/status及接手动作唯一处为状态板交接。

当前绑定候选Overall=REWORK_REQUIRED/Lifecycle=ACTIVE；旧R1@OpsScoreDiagK1K4 PASS消费、Ops/K通过/归因/终局冻结集和R1-5 OPEN不回改，新停点R0。DIAG:RETRY:1已签未放行，绑定独立通过消费/实际新标记/现场及执行树门/本人新窗口仍缺；B-main/N-3未正式放行，G1–G5/Air原件环境/现场登记/AC-18与AC-14/15/18及AC-16正式板端NOT_RUN，无UNITY_NA/DONE；旧耗尽许可、42979c14:SUB:1余量用途、N-5/K/T/债/偏差/UNKNOWN与ACQ暂停保持。0消耗/2零消耗，不新增交接轨道。

needs_user：`P1-ENG-LOOP-002:DIAG:RETRY:1:WINDOW`推荐绑定有效通过消费/新标记和准备安排齐备后，由用户本人给新P1窗口；理由为本人Play及确认动作不可代给，当前后置、不催窗口、不重签额度。此题不阻断C10-1零消耗纠正；当前无新增授权请求。open_items仅计设计退修残留，不表示C10-1或正式缺证已闭。

open_items: none

## C11@OpsDiagBindK1K2核对（2026-10-08，Acceptance）

派发：`P1-ENG-LOOP-002-C11@OpsDiagBindK1K2-20261008T203703Z-8be4`；Owner Acceptance / Codex，对Claude实现作异源只读核对。按本项已完成C1–C10连续计数，实际C11与预估一致；D4工程轨道及诊断绑定方案答复§1–4、AC-10修订9/AC-13修订2为合同。本轮仅写本节/最新核对表和状态板，不跑功能测试、不改实现、不加AC/BC、不签独立复核、不签额度或放行行；SSH/板/Play/模型/回放/下载/装包均0。

### 1. 候选、双基线与完整核对范围

纠正候选为Ops交接§19记录的C10退回纠正派发的证据提交，代码提交由该节及其提交主题定位；不把后续supervisor登记或本轮核对文档提交当作实现候选。运行时解析证据候选：

```sh
git log --format=%H --fixed-strings --grep='Dispatch-Id: P1-ENG-LOOP-002-C10退回纠正-20261008T202817Z-3304' -- docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md
```

比较基线从`docs/reviews/P1-ENG-LOOP-002.md`最新有效通过轮的完整`passed_candidate:`行解析：同名R1@OpsScoreDiagK1K4的PASS，须核其在最新`round_candidate:`后且对应有效通过。本轮核过基线→纠正代码→证据候选→开工HEAD的祖先关系；纠正代码→证据仅证据日志/交接/状态，证据→开工HEAD的PG及三操作页零diff。派生SHA不抄入手维护文档。

已重读最新有效passed→证据候选的完整11路径diff（+1653/-69，2095行），并非只看纠正常量。PG及操作页3路径（+487/-44）：`tools/eng_loop2/play_ops.py`、`tests/test_eng_loop2_play_ops.py`、`docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`。其余8路径：本提案、状态板、同名复核、implementation-status、supervisor-dispatch.jsonl、Ops交接、原绑定focused日志与c10-rework-focused日志；逐一核归属，既有复核/消费是旧停点记录，不是本次独立通过。基础设施、授权账本、controller/Assets/config/ProjectSettings/Packages、play部署/汇总/操作服务/分析代码及正式两操作页均零diff。

直接关联代码重读诊断entry闭表、guard/账本扫描、release_gate调用及新绑定解析、DiagnosticRun身份/consume时点、真实main入口、生产写盘红绿测试；并读禁改release_gate实现、正式分支和闭集外兼容测试。OSD-R1-1逐字docstring补丁仍并入完整候选，未借此改行为。静态核对测试AST改动仅DiagTestBase/DiagTests/DiagBindingTests；生产工具blob在纠正前后相同。诊断页已有20个命令围栏按序逐字保留，仅增加新条目的围栏；正式操作页及mini-smoke页零diff；旧SUB:3命令仍是历史耗尽示例。

### 2. C10-1闭合、四条件及核对表依据

**C10-1闭合。** RETRY1/RETRY1_TITLE/SUB3三个模块级定义移为DiagTestBase类属性，允许类内改用self或DiagTestBase引用，字面值和断言保持；闭集外类及生产/操作页在该纠正提交零改。Ops交接§19.1–19.4给出新测试树blob/hash、三项移动及恢复引用后的AST等价核对；本轮核实元数据和脚本内容，不运行其测试或另造结果。DiagControlPathTests继承已允许改变的基类夹具，类自身代码未改；DiagAccount直接构造的旧缺省id兼容保持，唯一生产构造点显式传entry id，旧id仍无条件拒续，非执行许可。

| 稳定停点条件 | 本轮只读核对及限制 |
|---|---|
| 接受范围实现完备 | BIND-1–6、Q1/A及OSD逐字补丁见§18；C10-1类闭集纠正见§19.1/19.3。最新核对表逐AC列证据及正式后置缺证，不扩大合同。 |
| 相称验证与已知失败处理 | 新树四模块focused 169项OK、rc=0、约238秒，见c10-rework-focused.log及§19.2。原生产守账红13项/35子失败与4 API缺失E、绿13项OK见§18及原日志；新树未重跑红绿，仅按生产不变/测试AST等价携带行为，旧测试hash不作为新树hash。无全套新跑；旧全套新增失败0但不绿，UNKNOWN保持。证据充分性由R1独立判。 |
| 可重读证据/候选归属 | §18原候选与§19纠正/新focused分开，核元数据、完整日志、真实写盘入口及红的原因；API缺失E或旧入口提前拒新id不当作fail-open证据。两空目录归属UNKNOWN、套件外预核授权/用量UNKNOWN均未洗掉。 |
| 停止依赖与准确交接 | 候选已提交推送，交接§19明确停止依赖推进；本轮照交完整候选及残留关注，不启动诊断或正式采集。本停点首退1/1已用，新独立轮尚R0。 |

BIND-1：冻结两entry及共享原限额；旧SUB:3即使无旧账本也硬拒，新条目只P1，未知/P2/P3建根前拒。BIND-2：账本不可读/非JSON/非对象/缺失或非字符串request_id洁净拒；自身consumed仅字面False允许，缺失/null/0/空值拒，其他可读id不冒充新用量；建根前守账、预检拒绝零资源记账、第一次受限主尝试前consume及身份贯穿日志保持。BIND-3/4：新title/id匹配精确条目，诊断额外正文绑定；新diag_release完整id与小写40位SHA须等于当前有效passed，不能用旧rel行代替，缺失/歧义/跨条目/不匹配拒。真实新放行行仍缺，示例占位不是签发。BIND-5/6：新P1现行命令与历史旧耗尽入口分明，正式命令围栏不变，不扩池/额度。

最新核对表为本轮逐项结果：“满足”仅表示本机合同/代码对应，不是独立verdict、真实板端通过或全套通过。AC-13修订2按新focused与静态行为携带核，保留下节证据充分性关注；旧正式AC-14/15/18及AC-16板端仍NOT_RUN。

### 3. 残留关注（交R1，非独立finding或再次退回）

- **PR-C11-1：红绿携带的充分性。** 纠正仅移动常量且生产相同，§19用AST恢复证明断言等价，新树focused169通过；原红/绿没有在新树再跑。R1按四条件独立核该组合是否充分，不把旧fixture hash当新候选，不以4个新增API缺失E或新id早拒作生产fail-open红。旧全套不绿及UNKNOWN仍披露，不能据本轮宣称全套通过。
- **PR-C10-1保持：** 禁改release_gate的docstring仍写旧SUB:3，参数实际由冻结新entry提供，外层说明/CLI/help/现行操作页为新条目。R1按具体可达调用及是否驱动操作判读，接受角色不修禁改函数、不代定CLASS/依据。
- **PR-C10-2保持：** 独立核BIND-2扫描域、生产写盘红绿/字面False、建根前后拒启与资源0，以及BIND-3/4正向绑定和拒绝分支。按##分条、未识别围栏同形标题及后续撤回的限制保持；未来接受写标记前核最新授权/耗用，不补造旧账、不清UNKNOWN、不扩威胁域。

新focused日志中既有stub subprocess的ResourceWarning不证明真实子进程/板端退出。本轮无真实板/Unity/权限/资源验证，未以本机静态核对替代现场门。

### 4. 照交与保持项

**C10-1闭合；本停点唯一首退已用1/1，不再退回，附最新核对表及§3残留关注照交新鲜R1@OpsDiagBindK1K2。** Review在一次性worktree重读§1完整11路径候选、合同/直接关联代码与§18–19证据，独立判四条件及非空PG开轮资格；不成立给REVIEW_BLOCKED不开轮。复核仍按focused一次/每条阻断finding生产路径红绿一次，不获SSH/板/Play/模型/回放/下载/装包权限。Owner/status/接手动作唯一事实源为状态板Active handoffs。

Overall REWORK_REQUIRED/Lifecycle ACTIVE保持；本停点C10/C11两次核对、首退1/1、新独立轮R0。旧Ops/K通过、R1@OpsScoreDiagK1K4 PASS消费及归因/终局冻结集、R1-5 OPEN保留。DIAG:RETRY:1已签未放行，独立通过消费/实际新标记/现场与执行树门/本人新窗口仍缺；B-main/N-3已签仍未正式放行，G1–G5/Air原件环境/现场登记/AC-18未齐，AC-14/15/18及AC-16正式板端NOT_RUN，无UNITY_NA/DONE。旧SUB:1/N-1/SUB:3耗尽、既有余量用途、N-5/K/T/债/偏差/UNKNOWN与ACQ暂停保持；轨道仍0消耗/2零消耗。

needs_user：`P1-ENG-LOOP-002:DIAG:RETRY:1:WINDOW`推荐在绑定有效通过消费、新标记及准备安排齐备后，由用户本人给新P1窗口；本人Play/确认不可代给。当前后置，不催窗口、不重签额度，无新增授权请求；不阻断新鲜R1零消耗复核。open_items只计设计退修残留，不表示正式缺证或预复核关注已闭。

open_items: none


## 绑定R1通过消费（2026-10-08，Acceptance）

requested.round=`绑定R1通过消费`；Dispatch-Id=`P1-ENG-LOOP-002-绑定R1通过消费-20261008T205817Z-c318`。owner=Acceptance，范围仅本提案/最新核对表、implementation-status与current-status；本轮消费最终通过、裁定文字补丁应用时点与机读绑定，不是D/C/R、不增改AC、不重做第三次代码核对、不签独立复核或额度，不代写用户原话账本。consumed=none；未运行测试/探测、SSH/板/Unity/Play/模型/回放/下载/装包，未改代码/测试/工具/配置。

### 1. 通过来源、门值与逐项消费

消费同名复核「R1@OpsDiagBindK1K2（2026-10-08）」§0–5及Verdict的**PASS**。复核提交由派发尾注定位，尾注Dispatch-Id/Role-Check与指定派发相符，提交仅复核文件/状态板；§0 round_candidate与Verdict passed_candidate各唯一且相等，通过行是文件末条有效机读通过、在末条round_candidate之后。运行时解析该来源，核候选为HEAD/origin/main祖先、其后全部PLAY_GOVERNING及三操作页空diff、开工树干净且无Assets/_Recovery；这里只核来源/门事实，不另做完整代码复核。Overall从REWORK_REQUIRED转**REVIEW_PASSED**，Lifecycle=ACTIVE，涵盖本绑定停点与旧通过范围携带，不等于诊断实际运行或正式验收。

| 消费项 | 采用依据 / 结论 |
|---|---|
| AC-10修订9、BIND-1…6/Q1=A | R1§1–2代码侧成立：入口/唯一已签条目/新id与有效passed绑定、一次性坏账fail-closed、围栏8/8字节零改；真实OpenSSH/板/Unity未验证。 |
| AC-13修订2、PR-C11-1 | R1§0新测试树修前红35F/4E按原因分列，守账红不借新API缺失或旧id早拒；修后绿13/13及focused169 OK，复核判窄修替代充分。未全套、不记全套通过；旧全套16项历史失败/新增0与UNKNOWN保持。 |
| PR-C10-1/2、SUB:2 | R1§1–3已核守账/绑定正反分支，PR-C10-2无finding；PR-C10-1归OSB-R1-1（§2）；R1§4附议原两张本人一致记录可携带、提示与用时UNKNOWN。OSD-R1-1逐字补丁随本候选已应用。 |
| 正式AC-14/15/18及AC-16板端 | NOT_RUN/证据缺失；R1无UNITY_NA附议，本轮不签UNITY_NA/DONE、B-main或G1–G5。 |

计数：本停点C2轮（C10/C11），首退1次“不满足”（C10-1），新增“证据缺失”退回0；R1轮、REWORK_REQUIRED返工0/2，无冻结集新增。OSB-R1-1依据BC-10（AC-10修订9）机械派生**实现错误（非阻断文字）1条**；从OpsScoreDiag起两条非阻断文字归因分列：OSD-R1-1已应用、OSB-R1-1待应用，不算阻断返工；旧阻断实现错误9条已闭保持。BC缺失/复核标准/核对轮/RED_LINE新增0，R1-5 SCOPE_GAP/OPEN原入口保持。本轮无blocks/release、累计AC修订30/新AC0不变，旧Ops/K终局/冻结集和计数不重置。

### 2. OSB-R1-1去向与应用时点

采纳R1§3非阻断CLASS_3及逐字docstring替换，**交实现在本次DIAG:RETRY:1结束并经接受核清后，下一次实现提交应用（可并入下一稳定停点）**；若用户决定不运行，则在该诊断方向另行裁定后应用。本轮不应用、不记已闭、不为CLASS_3另开轮，不改finding分级/依据。该许可只覆盖复核给的一行文档串，明确作为「诊断绑定方案答复」§2禁改release_gate的文字补丁例外；函数体、判据、数值、执行顺序仍不许改。此为复核点名补丁去向裁定，无AC新增或资源变化。

后置理由：当前已通过候选在tools/无增量，release_gate要求执行HEAD等于有效passed且发布引用PG空diff；提前改该行会改变PG，不能凭“非阻断/不开轮”绕过执行门或让旧机读行覆盖新代码。补丁应用后仍按当时有效候选/PG门处理，不预签下一候选或豁免K停点。补丁未应用不影响本轮PASS。

### 3. BIND-4实际行与最新授权/耗用核清

写标记前已核最新完整账本：10-08「用户按推荐签发新全套42979c14:SUB:1与新诊断DIAG:RETRY:1」为唯一匹配二级标题条目，其正文含反引号完整新id（不是WINDOW扩展或跨条命中）；该条之后无新撤回/否决/更正或本人窗口条目。采用原签发及「全套与诊断签发落实」§3全维度/0项，额度不重签、不转用。围栏内同形二级标题位于目标之前，真实目标正文未被截断，满足BIND-3写前核清。

本机静态读取诊断根一层全部粗账：仅旧SUB:3一份，身份可读、consumed=true、master_connections=1；五个现有子目录NOTES均无完整新id，旧无粗账目录不补造、不猜用量。结合本轮来源C11/实现交接§18–19、R1§5与派发记录，未发现DIAG:RETRY:1启动/耗用，新一次尚未动用。结论只限现存来源与本机扫描域，不声称能恢复删账或证明外部无未记动作；执行前接受须再核最新授权与耗用，来源缺失/冲突/耗用UNKNOWN即停，不靠缺账续跑。原旧诊断偏差/UNKNOWN均保持。

全局按check_docs的完整reviews文件顺序blocks/releases扫描并扣除implementation-status的RELEASED_SCOPE_GAP，未配对阻断为空；不是只查本项。自检通过且来源/最新授权/现存耗用前提成立，故按BIND-4**本轮可写代码消费标记**。值由程序从本通过节唯一机读passed_candidate解析（并核与round_candidate及全文件末条通过相等），不手抄SHA、不用发布引用rel替代；原sub3_release及历史记录零改。本行不替代现场/执行树/本人窗口，不转正式G4：

diag_release: P1-ENG-LOOP-002:DIAG:RETRY:1 c4973d03e1db374c3b837e2ec7d0754a73eac378

提交推送后，以含本行的origin/main发布引用作独立文档检出；执行检出须另位于最新有效passed候选、树干净，对发布引用全部PG及三操作页空diff。不得直接在本轮文档提交HEAD启动，执行时依原工具重复核祖先/最新通过/全局blocks/DOCWT自检/账本及放行行；任一失败拒启。

### 4. DIAG:RETRY:1剩余前提与准备顺序

| 前提 | 当前事实 / 后续责任 |
|---|---|
| 独立通过及接受消费、资源/用途合同、新入口绑定 | 已满足；§1、原签发落实§3与绑定答复§1–4；一次P1及原所有维度不变。 |
| 新机读代码消费标记 | 本轮按§3生成；提交推送后可由发布文档检出读取。只表示代码前提，当前不启动。 |
| 最新撤回/耗用与全局blocks | 本轮已核未见新耗用/撤回、无未配对block；接受在窗口落实/执行前须重核，不把本轮静态事实永久化。 |
| 执行树/文档树双来源与本机资产/环境 | 具体核法已由操作页现行节及release_gate冻结；本机开工来源核成立，但执行检出、发布文档检出/其自检及Air实际工具/资产/smoke32行尚未作执行时核，不记就绪。不得在等待窗口时跑探测/加载/回放。 |
| 现场核/前台释放/峰值映射与共享槽 | 仍缺，原操作页步骤与信封已安排：窗口后在一次整批≤2700s内先Air门、再占额开有限主连接核板/认证/端口/残留/身份/资源并依原流核HTTP，短私有临时件计入Air峰值。不是额外免费预核；失败只做同次安全收尾，不重启/重测/另开连接。现场HTTP依服务启动顺序核，不能把“先核”读成额外先启服务。 |
| 用户本人新窗口 | 仍缺，旧“现在”不可沿用；现在代码消费/新标记齐，已有固定现场准备顺序，可转呈§5请本人给新P1窗口。窗口不是GO、不代替执行时全部门。 |

本轮仅解除代码/机读缺口；**诊断仍待窗口及执行时前提，当前未运行放行**。用户给窗口→授权发生会话按规则入账→接受落实并重核最新耗用/安排→supervisor按唯一交接派发原信封内执行，现场核与本人Play在同一整批。等待期间不SSH、不改PG、不启动本项正式/诊断依赖；不新增并行交接。原四STOP/DIAG_FAULT/非0停依赖、原根/账保留与非证据边界保持。

### 5. needs_user与保持项

| request_id | 推荐项与理由 | 为何只能用户定 |
|---|---|---|
| P1-ENG-LOOP-002:DIAG:RETRY:1:WINDOW | 推荐由用户本人给一个能覆盖≤45分钟准备、现场核、P1操作及收尾的新在线窗口，并在该窗口亲自Play/停止、发送/跳过、确认/拒绝与反馈；代码消费/标记已齐，现场准备顺序按§4安排，旧“现在”已结束。额度已签，不要求重签或另开免费预核。 | 原签发明确本人另给新窗口；实际在场与Unity动作不能由接受/supervisor代给，不能以D5代选。窗口本身不豁免执行树/现场门。 |

旧SUB:1/N-1/SUB:3耗尽、42979c14:SUB:1已用候选及未用返工额度用途保持；旧全套不绿、两空目录归属UNKNOWN、套件外预核越界/用量UNKNOWN、R1-5 OPEN、N-5/K/T/其他债/诊断偏差/ACQ暂停保持。SUB:2本人附议可复用，提示/用时UNKNOWN。B-main/N-3已签仍未正式放行，G1–G5/Air原件环境/现场登记/AC-18未齐，AC-14/15/18及AC-16正式板端NOT_RUN，无UNITY_NA/DONE、不关闭旧里程碑；诊断原件不转正式或里程碑证据。下一Owner/status只见状态板交接行，当前0消耗/2零消耗。

open_items: none


## 诊断窗口落实（2026-10-08，Acceptance）

requested.round=`诊断窗口落实`；Dispatch-Id=`P1-ENG-LOOP-002-诊断窗口落实-20261008T212837Z-b34b`。本轮仅窗口/消费前提只读重核与执行交接，不是D/C/R，不改AC、代码/测试/工具/配置、账本或复核，不写新机读放行行，不首签额度。consumed=none；未测试/探测、SSH/板/Play/加载/回放/下载/装包。

### 1. 窗口裁定与效力

账本10-08「用户给 DIAG:RETRY:1 本人新 P1 在线窗口：现在进行一次诊断」明确将本人答复读为采纳「绑定R1通过消费」§5推荐：起点沿该条at（近似时刻），覆盖≤45分钟准备、现场核、P1操作和收尾，用户本人在Air操作。**满足本次WINDOW要求，needs_user=[]**；不因未单列分钟数重问、不重签资源。读法可由用户更正；不是正式GO，也不豁免任何执行门。

本节更新的是窗口事实：原「绑定R1通过消费」§4–5、诊断页现行节第3项及implementation-status旧记录中的“窗口仍缺/当前未给”已由此条与本裁定取代，其余合同和操作命令原样。不改操作页以免引入PG变化。supervisor应接力立即派发；执行人记录实际整批准备起止，完整≤2700s，等待不清零、不把派发延迟变成新窗口。若本人已离场、撤回/更正，或剩余窗口无法覆盖准备及安全收尾，停回WINDOW由本人另定，不占额预探。

### 2. 最新撤回/耗用与全局门重核（静态来源）

完整读取账本并分条扫描：完整新id仅在原资源签发与本次窗口两条出现，唯一资源签发正文绑定成立；未见后续撤回/否决/更正或新耗用授权。读取本机诊断根一层全部粗账/NOTES：五个已有目录、仅一份旧SUB:3粗账（身份可读、consumed=true、主连接尝试1），NOTES无新id；结合「绑定R1通过消费」§3、同名复核R1@OpsDiagBindK1K2 §5与当前派发记录，未发现新id启动/耗用。只限现存来源与本机扫描域，不恢复删账、不证明外部无未记动作；未知/冲突即停，不凭缺账续跑。

调用check_docs的完整reviews顺序blocks/releases扫描并扣除implementation-status的RELEASED_SCOPE_GAP：未释放集为空。最新passed_candidate运行时解析为当前HEAD祖先；至开工HEAD全部PG与工具OPS_SHEETS三页空diff，树干净、无Assets/_Recovery。这里只核来源，**未核执行双检出或Air资产/现场，不记就绪**。派发前若账本/粗账/有效通过/全局blocks发生变化，交接受重核；实现不得自行裁撤回或UNKNOWN。既有diag_release保持，不补写/改值。

### 3. 唯一派发与执行顺序

supervisor按本项唯一交接派发**Implementation，requested.round=`诊断P1执行`**，执行机器为同一MacBook Air（Unity主机），板为现有Host Jetson同一Orin Nano 8GB Super；不另派板角色/用户并行交接。Implementation/原脚本跑全部机械步骤，用户只在本人动作点介入。严格复用诊断页现行DIAG:RETRY:1唯一命令，固定完整id/P1/冻结计划输入，不执行历史手工步骤或改剧本。

1. Implementation在整批准备中建立双检出：文档检出取含本裁定/原放行行的最新origin/main发布引用；执行检出从同名复核最新有效passed_candidate解析，HEAD须等于该值，树干净，对发布引用PG/三页空diff。不能直接从本轮文档HEAD启动；Unity打开执行检出的原闭环场景，本人先不按Play。
2. Implementation运行唯一诊断入口：先建根前新id/P1/全粗账门，再建根后放行/账本唯一绑定/diag_release/全局blocks/DOCWT自检及Air工具、现有环境、det-assoc资产、smoke32行门。失败拒启，不碰板；根/粗账按原拒启语义保留。短私有ControlPath归属/峰值及共享槽由实现现场核，不能另开免费探测。
3. 首个受限动作前置consumed=true并占额；Implementation用主连接#1完成认证、板身份/资源/端口/残留/三文件核，原16路径源码与诊断输入同步、新根/峰值映射核，随后关闭#1。不得传模型/库或改环境；现场核失败停依赖。
4. Implementation用主连接#2在可见前台SSH启动编号1的唯一板服务，监督生命周期；之后按原流核一次/status身份/HTTP及无http_budget，再做measure≤1、仅rc0才k-receipt≤1。HTTP核在服务之后，不另启服务预核；measure与Play共用驻留。
5. 仅前项合格才启动本机网页并提示本人：**本人按Play≤1**，每条ask/respecify前看实时画面点发送/跳过，候选点确认序号/拒绝；Implementation/脚本按冻结P1时序调度，不替本人判可见性、不读真值选框。计划末脚本stop，本人在Unity停止；本人可随时中止并记录可靠按钮时刻/反馈，UNKNOWN不伪填。
6. Implementation同次收尾：停会话→本人停Play→前台中断并等板服务退出→同一连接#2核释放/有限日志回传→关#2/私有临时件释放→runtime归位→诊断摘要与本人通过/失败/受阻反馈（不判门）→结束计时。原件/粗账保留在两端诊断根，反馈等待计墙钟，不新连接补核。

### 4. 停止、收尾与下一交付

原签发全部数值/0项沿「全套与诊断签发落实」§3及「SUB3核清与评分上限落实」§5不变。四STOP仍为越额、需新增环境/设备、红线/安全、本人决定停；普通错误/UNKNOWN记DIAG_FAULT和原rc，失败/非0不续依赖，仅同次安全收尾。Play中故障/STOP/到时不可逆封住业务动作，原stop最多一次、迟到回执不恢复；故障重启/重测/免费重试0。建根前拒启不建账，建根后前提拒启consumed=false；首个受限动作后无论成败/中止均用尽一次，不删改旧账、不以余额另开。

执行轮收工更新原Ops交接具名「诊断P1执行」节及状态板，返回实际粗账/事件/原流、资源峰值/UNKNOWN/未执行、停止原因、释放与runtime归位指针；只记录诊断，不复制原件进正式证据/Unity验收日志。提交推送后交Acceptance，requested.round=`诊断P1核清`，先核资源/偏差/问题及结束事实，才安排OSB-R1-1后置逐字补丁；执行轮不顺带改代码/补丁，不自行关闭或重启。拒启/失败也交同一核清入口；若需新窗口/额度/范围再由接受按缺项转用户。

Overall REVIEW_PASSED/Lifecycle ACTIVE及旧债、偏差、全套不绿/UNKNOWN保留；R1-5 OPEN、SUB:2附议/提示用时UNKNOWN、旧耗尽账/N-5/K/T/ACQ暂停不变。正式B-main/G1–G5与DONE/UNITY_NA不在本轮，AC-14/15/18及AC-16正式板端仍NOT_RUN。交接改为1消耗/1零消耗，非本轮实际消费。

open_items: none


## 诊断P1核清（2026-10-08，Acceptance）

requested.round=`诊断P1核清`；Dispatch-Id=`P1-ENG-LOOP-002-诊断P1核清-20261008T215727Z-4966`。owner=Acceptance；本轮仅资源/偏差/问题及结束事实核清、既有文字补丁去向与下一交接，不是D/C/R，不判正式门、不定跟随原因、不增改AC，不签独立复核/额度/新的机读放行行，不写用户原话账本。consumed=none；只读既有本机原件，未运行测试/探测、SSH/板/Play/加载/回放/下载/装包，代码/测试/工具/配置零改。

### 1. 来源、身份与资源实账

合同为「诊断窗口落实」§1–4及「全套与诊断签发落实」§3、诊断页现行DIAG:RETRY:1节及其引用的工具步骤/本人动作/STOP/原件边界。执行交付由git主题与实现Dispatch-Id定位，完整两路径diff（原Ops交接§20及状态板）已读；supervisor-dispatch.jsonl同一实现Dispatch-Id的finished行含全文报告。用户反馈只引用unity-test-log「UT-P1-ENG-LOOP-002-DIAG-RETRY1-P1」，不改其原话。

**原件入口唯一沿Ops交接§20.5的Air根解析**。已读该根粗账、NOTES、ops-events原流、ssh/d1.tsv与d2.tsv、play/ops-web.jsonl、ops-summary、原会话关键事件及board/serve-channel-1.log；board-logs.tar只在内存读取成员与serve-1.log尾部，未解包写盘、未读真值评分。板上原件未接触。粗账request_id/entry_binding、NOTES页首、diag_start/diag_entry_binding均为完整DIAG:RETRY:1，P1固定、consumed=true；原有效通过/发布身份沿原件及复核机读行解析，不手抄派生值。

| 维度 | 核清实账与限制 |
|---|---|
| 一次整批/耗用 | DIAG:RETRY:1已执行1次且用尽；成功/失败/中止均不留第二次，旧许可/账不改，不以缺账、剩余墙钟或连接关闭复活。 |
| 墙钟≤2700s | 粗账733.97s仅至21:49:07，事件流也止于摘要；另有300s反馈等待。工具21:36:53→21:54:08约1035s、准备至检出收尾21:35:14→21:54:37约1163s来自Ops§20.1/实现报告，非粗账完整计时。本人窗口约21:27Z→结束亦未过45min；当前来源未见超时，不把733.97写成全批用时。 |
| SSH/服务/模型 | 主连接2/2（d1/d2原tsv、粗账）；板服务启动1、GGUF1、YOLO1、重启0；本人Play1/会话1、measure1/k-receipt1（原rc0），不代表正式通过。板驻留结束未证实，粗账residency_s只到中断/等待边界，不能证明实际驻留已结束。 |
| Air≤250,000,000B | 粗账轮询峰值87,074,184B；实现另报文档检出跟踪文件75,197,059B、已移除，两项合计162,271,243B。已记录部分在限；临时检出已不存在，后者未独立重测，其他临时件/采样间峰值不由这两项证明，完整峰值UNKNOWN。 |
| 板≤200,000,000B | 原du已采峰值385,629B，末次21:42:05；之后无du，board_du_bytes=null。采样读数在限，完整峰值与终值UNKNOWN，禁止概括“各维度均已核在额内”。 |
| 0项/未执行 | 原账/报告未记新增下载/安装/编译、模型或库传板、云/5060/正式ID/真实归档回放或评分；faults/not_executed空只表示工具字段，不证明收尾/反馈齐全。手工偏差另列§2，不用deviations=[]抹去。 |

资源核清只限现存本机来源及实现声明；未发现次数超额不等于追认完整合同符合或证明外部无未记动作。旧全套不绿、耗尽账、预核越界/UNKNOWN及债务原样保留。

### 2. 结束事实、偏差与诊断问题登记

下列是具名诊断问题/未核事项，**不是独立finding、不自定CLASS/依据值、不记新SCOPE_GAP或机械归因、不写block/release**；后续修复须按其范围回合同与相称停点。

| ID | 已知事实与未核边界 | 去向 |
|---|---|---|
| DIAG-P1-RELEASE-1 | STOP3原因仍为板端port/process release cannot be confirmed。Ctrl-C/附录7/exit已发，原流无serve_rc、sh_rc或收尾完成标志；serve.release.released=false、ports_released/no_residual_process=false。false在此是未证明，不能推断仍占用或已释放；空still_listening也不是释放证据。d2客户端关闭/主连接exit rc0不能证明板服务与18081/18082释放。 | 新板只读额度见§4 BOARD:RO:1；在核实前保持UNKNOWN，不再启动依赖服务/正式流程。 |
| DIAG-P1-FINISH-1 | Ops§20.3/finished报告声明finish_channel主线程卡stdout缓冲锁、reader阻塞read1。当前函数在reader.join(timeout=5)后直接close(stdout)，与声明路径相容；未重现/未读到采样原件，精确根因仍待定位，不能以30s/5s超时断言整个收尾有界。 | §4 REPAIR:DIRECTION建议先做零消耗定位/方案，涉及前台监督与安全收尾须明确K2等范围，禁止直接把手工解卡写为固定旁路。 |
| DIAG-P1-SIGTERM-1 | 实现声明21:49:07只SIGTERM本批d2通道本机ssh客户端，事前中文告知；日志可见pty关闭，之后同一d2有限回传/exit与ControlPath释放。信号目标归属/实际信号由Ops§20.3及报告承接，粗账没有该动作，原件不足以独立证明全部信号细节；远端连带退出UNKNOWN。 | 登记为原脚本外手工收尾偏差，不追认已获常规kill许可；不新增连接/启动/Play计次，不改账或重复独立finding归因。是否清理板残留另见§4 CLEANUP。 |
| DIAG-P1-FOREIGN-1 | 原会话第2行ILLEGAL_WRITER_SUSPECTED、第3行confirm回执IGNORED_FOREIGN_SESSION；摘要一致性提示1条。工具提交原流无该旧请求；实现称来自共享runtime旧残留，现存来源不足以排除当时其他写者，不能只凭警告认定并发绕过，也不能认定它导致红车故障。 | 保留残留与原流；§4 CLEANUP/REPAIR:DIRECTION分开处理清理授权和隔离方案，不扩大为删runtime许可。 |
| DIAG-P1-FOLLOW-1 | 本人反馈：taxi换红车后机身居中一次便不再跟随，移动红车离画面；交互顺畅的口头观察照存。P1-3/epoch=3原会话第580/583行BOUND及TRACKING，619–620行同纪元tracker_failure/SUSPECTED；四次确认/状态仅是事件，不证明框身份、持续控制或跟随正确。具体发生机制、动作/观测链与原因UNKNOWN，不读真值定对错。 | 推荐优先检查重指定后指针→快层观测→机身命令连续性与丢失报告，先零消耗定位方案、保留原数值/采样/对象；§4 REPAIR:DIRECTION由用户选，不能直接改模型/控制/重播种策略或启动验证。 |
| DIAG-P1-ACCOUNT-1 | 按钮起止仍UNKNOWN，不以首帧/TERMINAL替代。网页feedback_given=[]/摘要“未反馈”与稍后口头反馈兼容：反馈已在用户日志记录，未在网页点击，不补写原账“通过”。NOTES空表仍带历史180min/5 Play/3启动，与现行粗账2700s/1/1不同；不是现行额度。 | 口头“诊断完成/已经停止”核的是本人结束动作，不是释放/正式验收；模板和完整墙钟、收尾状态/偏差记录缺口并入待拟方案，不本轮改工具或原件。 |

结束核清：工具按实现报告rc3（DIAG_END_WITH_ISSUES）退出、业务会话计划末stop APPLIED/TERMINAL，网页原流已sealed/plan_halted；本人“已经停止”已录。粗账runtime_restore=done、connections/logs=done、ControlPath removed=true；本机scenario_config不存在、开工main树干净，双检出归位/临时检出删除承接报告。**closeout.service_release=done只表示步骤走过，不能覆盖实际released=false/UNKNOWN**。诊断整批已结束，可履行后置文字补丁；板端生命周期未核清，本项不作正式结束/通过裁定。

### 3. OSB-R1-1后置应用与唯一下一交接

本节保留原派发范围；文字补丁现已履行，核清结论与现行交接见下节「OSB文字核清」。

「绑定R1通过消费」§2规定的“本次诊断结束并经接受核清”时点现已达到；不以释放UNKNOWN抹去该问题，也不把核清误作释放通过。交Implementation，requested.round=`OSB文字补丁`，在下一实现提交**逐字应用同名review R1@OpsDiagBindK1K2 §3的OSB-R1-1旧行→新行**，仅tools/eng_loop2/play_ops.py::release_gate的一行docstring。派发时旧行仍在（现已应用，履行核清见下节「OSB文字核清」）；保持四格缩进，函数体/参数/判据/数值/顺序及其他功能文件零diff。不改finding分级/依据、不自记复核CLOSED、不为CLASS_3另开C/R；补丁随未来候选全PG比较携带，不改旧passed_candidate或机读放行行。

实现仅更新原Ops交接具名履行小节（逐字diff/未运行行为验证声明）与状态板，运行角色/文档自检、提交推送后交Acceptance作文字履行核清。此轮零模型/零功能测试/零SSH/板/Play/回放/下载/装包/正式ID，不借42979c14:SUB:1余额或已耗尽诊断。**不顺带修§2任一功能问题**，不并入新的收尾/跟随代码。本补丁既有许可足够，不等待§4答复；supervisor沿唯一交接接力，用户待决由其转呈，不新增第三条零消耗交接。

### 4. needs_user（未签/未选，逐条由用户定）

| request_id | 推荐项与理由 | 为何只能用户定 |
|---|---|---|
| P1-ENG-LOOP-002:DIAG:P1:BOARD:RO:1 | 推荐独立一次零模型只读释放核：同一Air现有Host Jetson/同一Orin Nano 8GB Super，由Implementation执行；完整墙钟≤600s（含认证/准备/收尾）、SSH主连接尝试≤1（失败亦用尽）、Air新增日志/私有临时件合计≤2,000,000B、板新增0。仅已有ps/pgrep/ss/du及本批根/进程归属字段读取，核本批服务/18081与18082、根终值；不以pid单值认归属。HTTP/服务启动/GGUF/YOLO/Play/回放/下载/安装/编译/同步/kill/删文件/配置变更/正式ID/云/外部API/新增GPU·h均0，失败或UNKNOWN即停，无重试/第二连接。只记当前事实、不消除历史未采峰值；原件保留。备选用户本人在板上查看并报告可靠来源，或暂不核、保留UNKNOWN。 | 原一次与2连接已用尽，新设备操作/连接用途需用户独立首签；接受/supervisor不能把只读算免费或挪正式B-main信封。当前完整申请未签，全维度0；用户本人查看也需明确选择，不代其执行。 |
| P1-ENG-LOOP-002:DIAG:P1:CLEANUP | 推荐先只读核与保留全部诊断原件；若确有残留，再由实现报本批精确argv/UID/起点/根归属及最小退出方案，经接受转用户另定是否和如何退出/隔离。共享runtime旧请求不默认删除，原hold/归位事实保留。 | kill/终止/删除不是上述只读额度；服务退出事实未知、可能牵涉其他工作与原件保留，用户决定新处置范围。此题不首签任何清理额度、不追认先前SIGTERM、不允杀未知进程或删除原账。 |
| P1-ENG-LOOP-002:DIAG:P1:REPAIR:DIRECTION | 推荐继续现有闭环方向，优先DIAG-P1-FOLLOW-1与DIAG-P1-FINISH-1：先交实现做本机零消耗静态定位/具名修复方案（同时承接FOREIGN/ACCOUNT记录问题），交接受冻结闭集、相称验证与K停点后再实现；不按表现调数、换模型/对象/剧本/采样，不先重跑。备选保留问题暂不推进功能修复。修复若触及目标身份/重播种/控制安全，走K2/K3等相应停点，新全套/板/Play必须另列申请；本题不是资源签发。 | 此前交接只许可既有一行文字补丁（现已履行），功能修复方向可能改任务范围、模型决策/安全语义及资源用途；不能以D5整题代选或旧通过覆盖。用户选择后由接受落实合同，既有额度不转用；本轮不替用户决定根因/策略。 |

Overall REVIEW_PASSED/Lifecycle ACTIVE及旧通过/归因/冻结集不变，AC修订30/新AC0不变、R1-5 OPEN及SUB:2附议/提示用时UNKNOWN保持；§2问题不升格为正式UNITY_FAILED。正式B-main/G1–G5/Air原件环境/现场登记/AC-18未放行，AC-14/15/18及AC-16正式板端仍NOT_RUN，无UNITY_NA/DONE。OSB-R1-1已应用并经下节「OSB文字核清」确认逐字履行；用户答复必须在其发生会话入账后再落实，不把推荐当授权。open_items只计设计退修残留，非§2问题或§4待决销项。

open_items: none

## OSB文字核清（2026-10-08，Acceptance）

requested.round=`OSB文字核清`；Dispatch-Id=`P1-ENG-LOOP-002-OSB文字核清-20261008T220452Z-a72b`。owner=Acceptance；仅既有CLASS_3补丁的只读文字履行核清与失效时态更新，不是D/C/R、不增改AC、不签独立复核或额度、不写新的机读放行行/用户原话账本。consumed=none；未运行测试/探测、SSH/板/Play/加载模型/回放/下载/装包，代码/测试/工具/配置零改。

### 1. 来源与逐项文字核对

唯一合同为「诊断P1核清」§3，逐字补丁来源为同名review「R1@OpsDiagBindK1K2」§3 OSB-R1-1；履行证据为Ops交接§21。实现提交按Dispatch-Id `P1-ENG-LOOP-002-OSB文字补丁-20261008T220251Z-851b`及路径 `tools/eng_loop2/play_ops.py` 从git log唯一解析，不手抄派生SHA。已读该提交完整三路径diff（工具docstring、Ops交接§21与状态板），核其为开工HEAD祖先；之后至开工HEAD仅supervisor-dispatch.jsonl变化，当前工具字节与补丁候选一致。

| 核对项 | 结论 | 只读依据 |
|---|---|---|
| 旧行→新行与缩进 | 满足 | 直接从复核text围栏取旧/新行，去掉Markdown列表的两格缩进后，均保留源码四格；候选父版旧行逐字相等，新版新行逐字相等。 |
| 全文件仅此一处 | 满足 | 父版旧/新行计数1/0，新版0/1；父版仅替换该行一次所得完整字节与新版及当前磁盘相等。工具numstat恰+1/−1。 |
| 函数体及其他功能文件零diff | 满足 | 完整提交路径恰上述三项；完整工具差异只有docstring一行，函数签名/函数体/参数/判据/数值/顺序及工具其余字节一致；其他功能路径无变更。 |
| 履行披露及原边界 | 满足 | Ops交接§21.1逐字diff与实际一致，§21.2明确未运行行为验证、零消耗、不顺带修功能问题；未改复核文件、finding分级/依据、旧passed_candidate及机读放行行。 |

**结论：OSB-R1-1已逐字应用，文字履行核清完成。** 此结论不自记独立复核CLOSED，不另开C/R，也不使新PG差异获得通过：该补丁须随未来候选全PG比较携带，旧passed_candidate与发布标记不变。

### 2. 下一交接与保持项

用户待决仍逐条见「诊断P1核清」§4，三个完整request_id与推荐/理由保持；本轮未收到答复，不把推荐当授权，supervisor不能D5代选。既有文字补丁动作已完成，唯一交接改为用户等待三题答复；答复须在发生会话入账，之后交接受角色落实，不先交实现启动功能定位/板核/清理。

DIAG:RETRY:1已耗尽，释放/完整板峰值UNKNOWN、诊断问题/手工SIGTERM偏差、旧全套不绿及全部旧债/冻结集保留；Overall REVIEW_PASSED/Lifecycle ACTIVE、R1@OpsDiagBindK1K2返工0/2与归因计数不变，AC修订30/新AC0、R1-5 OPEN、SUB:2附议/提示用时UNKNOWN保持。正式B-main/G1–G5/Air原件环境/现场登记/AC-18未放行，AC-14/15/18及AC-16正式板端NOT_RUN，无UNITY_NA/DONE。open_items仅计设计退修残留，非诊断问题或用户待决销项。

open_items: none
