# P1-TRACK-001 — 首个外部 SOT 基线（First external SOT baseline）

Status: ACCEPTED
Author/role: Claude Fable / design ideation
Created: 2026-07-23
Last updated: 2026-07-23

## Problem and research value

M0 已交付帧/观测契约与四指标 evaluator，但 `C_track` 至今只被一次手工框验证过（UT-P1-M0-001-001，frame 32）。系统还缺一条真实的每帧感知回路。本项交付 SOT 主通道 + 最小云台跟随，它同时是：

1. **M2a**（5 Hz 桌面基线）的载体——本项不关闭正式 M2，5/20 Hz 对比归后续 `P1-M2-RATE-001`；
2. 感知消融轴的第一格（SOT-only，设计文档 §7）；
3. 后续所有里程碑（世界系滤波、丢失阶梯、YOLOE 仲裁）的测量基底；
4. 第一个自动化 B0（gimbal-only）基线数字的来源。

## Proposed behavior

1. **外部追踪进程**（Python，desktop）：轮询 `runtime/frames/latest.json`，按 `frame_id` 单调去重，读取帧包，SOT 更新，经 `tracking_observation.json` 发布裁剪到 `[0,1]` 的归一化框。追踪进程的输入只有帧包（图像 + 相机元数据）与 CLI 参数；不读 scenario config，不读任何 Unity 真值。

2. **Tracker 插件接口（修订 1）**：

   ```
   init(image, box_norm) -> ok
   update(image) -> TrackerResult {
     box_norm: [x,y,w,h] | null,
     ok: bool,
     confidence: float | null,          # 可选
     confidence_source: "none" | "tracker" | "placeholder"
   }
   ```

   首个实现 OpenCV CSRT（`opencv-contrib-python`，pin 实测版本）。**CSRT 不产生校准置信度**：丢失判定 = `ok == false` 或框非有限/退化（宽高 ≤ 0 或越出合理范围）；**不设也不宣称任何 CSRT 置信度阈值**。既有观测协议要求数值 confidence，故仅在 `ok` 有效时发布**文档化的诊断占位值 `1.0`**，`confidence_source="placeholder"` 记入运行日志；协议文件本身不改。

3. **帧序与积压语义（修订 3）**：
   - 初始化必须打开 `--init-frame` 指定的、仍在保留窗口内的确切帧包，否则以明确错误退出（不悄悄改用其他帧）；
   - 此后 `frame_id` 严格单调处理：若一次轮询发现落后多帧且中间帧仍在保留窗口内，**按序逐帧喂给追踪器**维护其内部状态，但**只发布最新帧的结果**（观测通道是单槽可替换文件）；`backlog_count`/`skipped_count` 记入日志；
   - 中间帧已被保留窗口淘汰（缺口不可恢复）→ 状态置 `ERROR_REINIT_REQUIRED`，停止发布，明确记录，不做无解释跳跃；
   - `frame_id` 回退或重置（Unity 重启）→ 拒绝处理并以明确错误停止，要求重新初始化。

4. **最小 LOS 跟随（无 Kalman，修订 4）**：机身全程 hold。几何定义（全部来自帧 metadata，无目标真值）：
   - 框底中心像素：`u = (x + w/2)·W`，`v = (y + h)·H`（归一化 top-left 原点）；
   - 世界方向：`d = normalize( ((u−cx)/fx)·right_world + ((v−cy)/fy)·(−up_world) + forward_world )`；
   - 与水平面 `y = g` 求交，`g` 来自**显式标定输入 `--ground-plane-y-m`**（有限值，默认 0.0，运营者提供；**不得读取 `target.route_world_m` 推导**）：`t = (g − o_y)/d_y`；
   - 仅当 `d_y < 0` 且 `t ∈ (0, t_max]` 时向 `gimbal_command.json` 发 `look_at_world`；平行、向上、非正距离的交点一律拒绝，本周期**不发新云台指令**，事件记 `GEO_REJECT`。
   - 转角滞后是无预测占位的预期现象，量化记录构成 M3 引入 Kalman 的动机数据。

5. **丢失行为（修订 1/2）**：`ok == false` 或框无效 → 本周期**不发布观测、不发布云台指令**，状态记 `LOST`；云台保持最后指向（既有 C# 行为，由 Unity 用例观察确认）。不实现 L1–L4（M4 范围）。

6. **运行日志：每次运行一个目录，schema 本提案冻结（修订 5）**：

   ```
   runtime/runs/<run_id>/
     manifest.json   # schema_version="p1-track-run/v1", run_id, created_unix_s,
                     # scenario_id(由运行脚本注入), condition("follow"|"nadir"),
                     # tracker{name,backend,pinned_version}, cli_args 全量,
                     # init{frame_id, box_norm}, ground_plane_y_m,
                     # planned_duration_s, host 信息
     frames.jsonl    # 每处理一帧一行：{frame_id, capture_unix_s, simulation_time_s,
                     # box_norm|null, ok, confidence|null, confidence_source,
                     # state(TRACKING|LOST|ERROR_REINIT_REQUIRED),
                     # event|null(INIT|LOST|GAP|REINIT_REQUIRED|GEO_REJECT),
                     # compute_latency_ms, frame_age_ms, backlog_count, skipped_count}
     summary.json    # 正常收尾时写：总帧数、发布数、LOST/GAP/GEO_REJECT 计数、
                     # compute_latency p50/p95、frame_age p50/p95、实际时长
   ```

   崩溃截断处理：读取方容忍 `frames.jsonl` 末行不完整；提供 `--finalize <run_id>` 从 `frames.jsonl` 重建 `summary.json` 并记录 `truncated_tail_lines`。每次验收运行的目录整体归档为持久证据。

7. **零微调约束（用户 2026-07-23 决定）**：感知模块只以现成/零样本形态使用——CSRT 在线相关滤波属推理期状态更新，允许；未来深度插件只用冻结的通用预训练权重；禁止用仿真数据对检测/追踪/ReID 做任何权重更新。此纪律限定感知层，不约束 Phase 2 的交接策略蒸馏。

## Inputs, outputs, and affected interfaces

- 读：`runtime/frames/latest.json` 与帧包（既有协议，不改）。
- 写：`runtime/tracking_observation.json`（既有协议，不改，含占位 confidence 语义的文档说明）；`runtime/gimbal_command.json` 的 `look_at_world`（既有协议，不改）；新增 `runtime/runs/<run_id>/`（gitignore 已覆盖，验收运行目录另行归档为证据）。
- 新代码建议：`controller/track_loop.py`（入口 + 帧序状态机）、`controller/trackers.py`（插件接口 + CSRT 适配 + fake tracker）、`controller/geolocate.py`（框→地面点）、`controller/run_log.py`（run 目录/manifest/summary/finalize）。预计**不改任何 C#**。
- 运行环境（修订 7）：**独立 `.venv-track`**，与 `.venv-yoloe` 隔离（两者的 `opencv-python` / `opencv-contrib-python` 都提供 `cv2`，不得同环境共装）；pin 实测 contrib 版本；安装冒烟检查针对该版本实际暴露的构造器（`cv2.TrackerCSRT_create` 或 `cv2.legacy.TrackerCSRT_create`）。
- 不改 scenario schema。运行时长等实验编排参数由**运行脚本**（追踪进程之外）从 scenario config 计算并写入 manifest；追踪进程本身不读 scenario config。

## Compatibility with the current v0.3.1 design

- 实现 §3.2 SOT 主通道与 §3.6 LOS pointing 的无预测占位；不触碰 §3.3 仲裁、§4 机身规划、§5 丢失阶梯。
- 符合 v0.3.1 §3.4 可插拔选型表（CSRT = 占位 + 经典对照档，长期保留）与桌面仿真路径、目标无关/零微调立场。
- 评测边界不变：真值仅在 evaluator；追踪进程只见图像与相机元数据。
- 与 P1-TEST-001（Unity Edit Mode 测试）并行无冲突：本项不含 C# 变更。
- 本项验收后，正式设计文档应记录：M2a（5 Hz）拆分、CSRT 无置信度语义、`P1-M2-RATE-001` 后续项（由 Codex 在接受时同步）。

## Acceptance criteria

均可证伪。非零 `C_track` 只证明桥路打通（bridge check），**不是性能质量门槛**；任何 CSRT 算法层面的表现（漂移、早失、不能自愈）都不构成实现门失败，如实报告即可。

1. **B0 跟随运行**：全新 Unity Play 会话，默认确定性环路、机身 hold、LOS 跟随，运行时长 = 运行脚本按 `2 × (路线周长 / target.speed_mps) + 60 s` 计算并写入 manifest（"两圈"以此计时定义）；期间 `metrics.json` 出现持续非零 `C_track`；`C_geom` / `C_track` / `C_track_given_geom` / 质量诊断与完整 run 目录归档为 B0 基线记录。
2. **nadir 对照运行**：另一个全新 Play 会话，同 scenario、同初始帧/框策略、同 planned_duration，云台固定 nadir；两组结果都报告。
3. **时延**：tracker **计算时延** p95 < 200 ms（本机，5 Hz 预算门槛）；**端到端 frame age**（捕获→发布）单独报告，不设门槛。
4. **自动化失败路径（修订 2）**：fake tracker 强制返回失败的用例证明——失败周期不写入新观测、不写入新云台指令；帧序用例覆盖：积压按序喂帧且只发布最新、保留窗口缺口 → `ERROR_REINIT_REQUIRED`、`frame_id` 回退拒绝、`--init-frame` 不在保留窗口内时明确报错。
5. **Unity 遮挡观察（修订 2，不设门槛）**：按 M0 的 Cube 方法遮挡后，如实分类记录 CSRT 行为——返回失败 / 带成功标志漂移 / 移除后是否自愈——连同 `incorrect_tracking_observations` 一并报告；三种结果都不使实现门失败。
6. **geolocate 单元测试（修订 4）**：覆盖 top-left 图像 y 轴符号、旋转（非正对 nadir）相机位姿、平行/向上/非正距离交点的拒绝路径；合成位姿/内参下数值在容差内。
7. **依赖与测试（修订 7）**：`.venv-track` 安装冒烟检查通过（pinned 版本的实际构造器可用）；自动化覆盖包含插件适配层、归一化/像素框转换与裁剪、强制失败不发布、帧缺口、geolocate、日志序列化（含截断容忍与 `--finalize` 重建）；既有协议测试保持通过。
8. **边界审计**：追踪进程无任何 Unity 真值读取路径，且运行时不读 `target.route_world_m` 与 scenario config（时长计算在运行脚本层）。
9. **Unity 用例 `UT-P1-TRACK-001-001`**：用户观察云台跟车 ≥ 1 圈，metrics 行为与上述一致。

## Baselines and ablations

本项即感知消融轴第一格（SOT-only）。产出两组数字：nadir 固定（地板参照）与 LOS 跟随（B0 基线），均为全新 Play 会话、同参数、同时长。B1/B2、5/20 Hz 对比（`P1-M2-RATE-001`）、深度 SOT 插件均不在本项。

## Failure modes and resource risks

- **CSRT 在低多边形车体 + JPEG(85) 上漂移或早失**：如实报告 `C_track_given_geom`；若结果证明 CSRT 不可用，凭证据另立深度插件工作项（冻结权重），CSRT 仍长期保留为经典对照档，不删除。
- **CSRT 带成功标志漂移**（无置信度可依）：本项无 YOLOE 校验通道，无法在线识别——如实记录为已知限制，正是 M4 仲裁的动机证据。
- **look-at-latest 无预测**：转角滞后甚至丢目标——预期内，量化后作为 M3 动机。
- **框底中心-平面求交的系统偏差**（玩具车比例、斜视）：记录，不在本项修（§3.5 协方差传播属 M3）。
- 依赖风险：`cv2` 命名空间冲突（contrib vs 普通版）→ 独立 `.venv-track` 隔离；CSRT 构造器位置随版本漂移 → pin + 安装冒烟检查。
- 5 Hz 轮询竞态：由既有原子清单 + `frame_id` 单调去重覆盖；崩溃截断由 jsonl 容忍 + `--finalize` 覆盖。

## Suggested implementation scope

`controller/` 四个新文件 + `tests/` 扩展 + 证据文档；估计一个实现批次。**Out of scope**：Kalman/世界系滤波、YOLOE 运行时接入、L1–L4、机身运动、5/20 Hz 对比（`P1-M2-RATE-001`）、任何深度模型权重下载、正式 M2 关闭。

## Resolved scope decisions (round 2，原 Open questions)

1. **本项 = 5 Hz M2a 基线**，不关闭正式 M2；5/20 Hz 对比独立为 `P1-M2-RATE-001`。
2. **深度 SOT 插件**：证据触发、另行提案；CSRT 永久保留为经典对照档。
3. **run 日志 schema 在本提案冻结**（`p1-track-run/v1`，见 Proposed behavior 第 6 条）。
4. **初始框走 CLI + `--dump-frame`**，不做 Unity 侧框选 UI。

本轮无未决问题。

## Codex review decision

### Round 1 — 2026-07-23: REVISION_REQUESTED

Rationale:

The proposed CSRT-only plugin, body hold, and no-prediction LOS loop are a
well-bounded first desktop baseline and fit the existing M0 frame/observation
contracts. The proposal is not yet implementation-safe, however: it assumes a
CSRT confidence value that the OpenCV tracker API does not return, makes a
real-occlusion outcome an acceptance requirement even though CSRT may drift
while returning success, leaves frame-gap behavior undefined despite the
single-slot observation file, and does not define the ground-plane height used
by geolocation. The evidence log would also mix comparison runs unless its
run/schema boundary is fixed first.

Required revisions:

1. **Correct the tracker confidence contract.** OpenCV CSRT `update()` returns
   `(ok, bbox)`, not a calibrated confidence. Change the plugin result to make
   confidence optional and source-labelled. For CSRT, loss is based on
   `ok == false` or an invalid/non-finite box; if the existing observation
   protocol still requires a numeric confidence, publish a documented
   diagnostic placeholder such as `1.0` only for valid `ok` results. Do not
   claim or apply a CSRT confidence threshold.
2. **Separate failure-path verification from empirical occlusion behavior.**
   Add an automated fake-tracker case that deliberately returns failure and
   proves that no new observation or gimbal command is written; the existing
   C# hold-last-target behavior is then checked in the Unity case. For the
   Unity Cube occlusion, report whether CSRT returns failure, drifts while
   returning success, or later recovers, together with
   `incorrect_tracking_observations`; none of those algorithm outcomes alone
   may fail the implementation gate.
3. **Close frame sequencing and backlog semantics.** Initialization must open
   the exact retained `--init-frame` bundle or fail clearly. After that, define
   how every increasing `frame_id` is handled. The preferred policy is to feed
   retained intermediate frames to tracker state in order, publish only the
   freshest result (the observation channel is a single replaceable file), and
   record backlog/skipped counts. A missing intermediate frame beyond retention
   must produce an explicit `LOST`/`ERROR_REINIT_REQUIRED`, not an unexplained
   jump. State how out-of-order or restarted frame IDs are rejected.
4. **Define LOS geometry without target-truth leakage.** Specify the normalized
   top-left box-to-ray formula using metadata `camera_right_world`,
   `camera_up_world`, `camera_forward_world`, and intrinsics. If retaining the
   bottom-center/ground-plane intersection, add an explicit finite
   `--ground-plane-y-m` calibration input and reject parallel, upward, or
   non-positive intersections without publishing a new gimbal command. Do not
   read `target.route_world_m` to obtain this value. Unit tests must cover
   top-left image-y sign, rotated cameras, and invalid intersections.
5. **Freeze an internal run-log schema now.** Use a per-run directory such as
   `runtime/runs/<run_id>/` instead of one indefinitely appended
   `track_log.jsonl`. Include a schema version and run manifest with scenario
   ID, tracker/backend/version, CLI parameters, init frame/box, and condition
   (`follow` or `nadir`). Per-frame records need frame/capture/simulation time,
   box or null, `ok`, optional confidence plus its meaning, state/event,
   compute latency, end-to-end frame age, and gap/backlog counts. Define
   crash-truncated JSONL handling and archive a durable summary for each
   acceptance run.
6. **Tighten experiment semantics.** Use the protocol name
   `C_track_given_geom`, not `C_track|geom`. Run follow and nadir conditions
   from fresh Unity Play sessions with the same scenario, initial frame/box
   policy, and duration. State how "two loops" is timed or observed. Apply the
   p95 `< 200 ms` gate to tracker compute latency and report end-to-end frame
   age separately. Nonzero `C_track` proves the bridge works; it is not a
   performance-quality threshold.
7. **Isolate and test the dependency.** Create a dedicated `.venv-track`;
   do not install `opencv-contrib-python` beside the existing
   `opencv-python` in `.venv-yoloe`, because both provide `cv2`. Pin the tested
   contrib version and add an install smoke check for the actual constructor
   exposed by that version (`cv2.TrackerCSRT_create` or the legacy equivalent).
   Automated coverage must include the plugin adapter, normalized/pixel box
   conversion and clipping, forced failure/no-publication, frame gaps,
   geolocation, and log serialization in addition to the existing tests.
8. **Resolve the open-question scope explicitly.** Accept this item as the
   5 Hz M2a baseline only; it cannot close the formal M2 milestone, whose
   5/20 Hz comparison becomes a separate `P1-M2-RATE-001` work item. Keep
   deep SOT as a later evidence-triggered proposal without deleting CSRT as the
   classic baseline. Freeze the record schema in this proposal. Keep CLI frame
   selection; no Unity-side box UI is required. Update the compatibility heading
   and references from v0.3 to the current v0.3.1 baseline.

Accepted design-document changes:

None yet. After Fable incorporates the revisions and Codex accepts the new
round, the canonical v0.3.1 design should record the 5 Hz M2a split,
CSRT-without-confidence semantics, and `P1-M2-RATE-001` follow-up.

### Round 2 — 2026-07-23: ACCEPTED

Decision: ACCEPTED

Rationale:

Round 2 substantively closes all eight required revisions. In particular, it
no longer invents a CSRT confidence score, separates deterministic
failure-path verification from empirical occlusion behavior, closes retained
frame sequencing and unrecoverable-gap behavior, makes LOS geometry auditable,
freezes a per-run evidence schema, separates compute latency from frame age,
isolates the contrib dependency, and limits this item to the 5 Hz M2a baseline.
The proposal is therefore bounded and testable enough to enter implementation.

Binding acceptance clarifications:

1. `--ground-plane-y-m` is a **required finite calibration argument with no
   implicit default**. The value used for the default Unity fixture must be
   measured or deliberately supplied and recorded in `manifest.json`; neither
   the tracker nor a helper may infer it from `target.route_world_m`.
2. The experiment runner is a separate orchestration tool in the implementation
   scope (suggested path: `tools/run_track_experiment.py`). It may read scenario
   configuration only to record `scenario_id` and calculate
   `planned_duration_s`; it may pass those scalar orchestration values to the
   tracker, but never route points, speed, current target state, or other
   target truth. `track_id` and `condition` are explicit CLI/task inputs.
3. Ordinary tracker failure enters `LOST`: later increasing retained frames
   may still be fed to CSRT, and publication resumes only if it returns a valid
   successful result. `ERROR_REINIT_REQUIRED` is terminal for that process
   after an unrecoverable frame gap or frame-ID reset. Both transitions are
   logged explicitly.
4. Acceptance criteria 1 and 9 are interpreted as a **bridge and observation
   check**, not an uninterrupted-tracking quality threshold. Each fresh-session
   condition runs for the planned duration; the follow run must produce at
   least one evaluator-matched observation and final `C_track > 0`. The user
   observes the run for at least one planned route loop and records how long
   the gimbal actually follows; CSRT drift, early loss, or failure to follow a
   full loop remains a reported algorithm result rather than an implementation
   failure.
5. Raw run directories remain local runtime artifacts. Every acceptance run
   also gets a tracked durable evidence summary under `docs/evidence/` with the
   exact command/config, manifest and summary contents, and hashes/locations of
   the raw artifacts. “Archive” does not mean committing all JPEG frames.

No further Fable revision is required. These clarifications supersede the
proposal wording where it says `--ground-plane-y-m` defaults to `0.0`,
“持续非零”, or “云台跟车 ≥ 1 圈”.

Required revisions:

None.

Accepted design-document changes:

- Record `P1-TRACK-001` as the 5 Hz CSRT M2a baseline; formal M2 still requires
  the separate `P1-M2-RATE-001` 5/20 Hz comparison.
- Record that OpenCV CSRT exposes success plus a box but no calibrated
  confidence; its valid observations use protocol-required diagnostic
  confidence `1.0` with source `placeholder`, never a confidence threshold.
- Record the required non-truth ground-plane calibration and the distinction
  between transient `LOST` processing and terminal `ERROR_REINIT_REQUIRED`.

## Round 2 revision map（修订 → 落点）

| Codex 修订 | 落点 |
|---|---|
| 1 置信度契约 | Proposed behavior 2/5；Acceptance 4；Failure modes 第 2 条 |
| 2 失败路径与遮挡分离 | Proposed behavior 5；Acceptance 4（自动化）与 5（Unity 观察，不设门槛） |
| 3 帧序/积压 | Proposed behavior 3；Acceptance 4 |
| 4 LOS 几何与标定 | Proposed behavior 4（公式 + `--ground-plane-y-m` + 拒绝路径）；Acceptance 6/8 |
| 5 run 目录 schema | Proposed behavior 6（`p1-track-run/v1` 冻结）；Acceptance 1/7 |
| 6 实验语义 | Acceptance 1（时长公式）/2（全新会话）/3（compute vs frame age）；全文改用 `C_track_given_geom` |
| 7 依赖隔离与测试 | Inputs/outputs 运行环境段；Acceptance 7 |
| 8 范围定夺 | 标题/Problem 第 1 条（M2a）；Resolved scope decisions；Compatibility 更新至 v0.3.1 |
