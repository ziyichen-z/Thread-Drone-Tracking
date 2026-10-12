# P1-TRACK-002 — 深度 SOT 插件（OpenCV TrackerNano / NanoTrack-v2，冻结权重）

Status: ACCEPTED_WITH_BINDING_CLARIFICATIONS (Codex round 2, 2026-07-24)
Author/role: Claude Fable / design ideation
Created: 2026-07-24
Last updated: 2026-07-24

## Problem and research value

CSRT 作为 M2a 占位追踪器的证据已足够定性：

1. **协议正常条件下的地板**（M2a，`P1-TRACK-001`）：follow `C_track≈0.30%`、nadir `≈3.11%`；
2. **随机失败模式**（RATE-001 批次 1）：同一起点下 CSRT 或如实报失败，或带 `ok=true` 漂移锁上背景（`rate20-follow-r3`：4999 发布 / 4998 错误）——失败模式不可预测。

**立项依据（如实记录）**：`P1-M2-RATE-001` 的预注册 R1/R2 规则**未被触发**（批次 1 输入无效，规则随该研究以 `UNDETERMINED_INVALID_INPUT` 关闭）。本项由用户 2026-07-24 行使范围决策权直接授权。

**主张收窄（round 2，响应修订 3）**：本项**不主张**新追踪器提供校准的丢失检测——OpenCV Nano 上游实现每次正常更新都返回 `true`，`getTrackingScore()` 为未校准分数且无默认丢失阈值。本项的研究主张仅为：**外观鲁棒性与跟踪连续性的提升**（由继任率研究的 R1′/R2′ 类指标度量）。"漂移不自知"问题的架构解仍是 M4 的 YOLOE 仲裁通道，不由本插件解决。

## Proposed behavior

### 1. 唯一实现路径（修订 1：移除模糊选项）

- **OpenCV `TrackerNano` API**（本机 pin 的 OpenCV 构建已暴露 `TrackerNano_create` / `TrackerNano_Params`，无需新增推理运行时）+ [OpenCV 4.x 文档](https://docs.opencv.org/4.x/d8/d69/classcv_1_1TrackerNano.html)链接的上游 **NanoTrack-v2** backbone + neck/head 两个 ONNX 模型；
- **身份矩阵在实现时记录并入 manifest/证据**：模型来源 URL 与 commit、两个模型文件的 SHA-256、代码与模型许可证、OpenCV pin 版本、DNN backend（默认 CPU target）、预处理身份（输入尺寸/归一化）；
- 除非实测发现文档化阻塞（记录后返回决策区），不考虑其他发行版/运行时。

### 2. 分数与 LOST 语义（修订 3：无可辩护外部阈值 → 不宣称校准丢失检测)

- `confidence` = `getTrackingScore()` 原值，`confidence_source="tracker"`，**仅作描述性诊断记录**；
- **不设丢失阈值**（不存在可辩护的外部来源；项目数据不得用于选阈值）；`LOST` 判定与 CSRT 相同：框非有限/退化/越界；上游 `update()` 恒 `true` 的行为如实写入证据；
- 阈值敏感性分析仅为描述性报告（分数轨迹 vs 漂移事件的对照），**不得反向选定部署值**；
- **对继任率研究的已声明后果**：`time_to_first_LOST` 对本插件是保守量（可能恒不触发），继任研究需以漂移主导率（`incorrect/matched`）作连续性等价判据——已写入 `P1-M2-RATE-002` 预注册规则。

### 3. 真实选择路径（修订 4：接口工作如实入范围）

- `controller/track_loop.py` 的 `run_tracker()` 当前无条件构造 `CsrtTracker`——本项新增 `--tracker {csrt|nanotrack-v2}` 选择器，并贯通 `run_track_experiment` 与率研究编排器；
- manifest 持久化：`tracker{name, backend, opencv_version, model_sha256{backbone, neckhead}, score_threshold: null, threshold_source: "none", preprocessing_id}`；
- **身份未知或模型缺失/损坏/哈希不匹配一律 fail-closed**，不得回退默认追踪器静默运行。

### 4. 范围裁剪（修订 2）

YOLOE 检测驱动通道**移出本项**——将来作为独立提案（建议 `P1-DETECT-001`，M4 检测/仲裁边界或显式 detector-only 基线），不得静默顶替 SOT、不继承本项 verdict。CSRT 保留为经典对照档不移除。

通用约束不变：冻结权重、零微调（含超参不得用实验数据选定）、权重下载需用户知情、无真值/scenario config 读取。

## Inputs, outputs, and affected interfaces

- 新代码：`controller/trackers.py` 新增 `NanoTrackV2Tracker`（模型加载 + 哈希校验 + 异常包装）；`track_loop`/`run_track_experiment`/率研究编排器的 tracker 选择器贯通；模型文件入库或按记录的 URL+哈希离线获取（加载测试不依赖网络）；
- 复用不改：`TrackerResult` 契约（字段不变；confidence 语义按 §2 记录）、观测/云台协议、`p1-track-run/v1`；
- `.venv-track` 无需新增推理依赖（TrackerNano 在现有 OpenCV 内）。

## Compatibility with the current v0.3.1 design

- 落实 §3.4 选型表"NanoTrack / HiT-Small 级"首选档；零微调立场保持；
- 本项交付插件 + 选择路径 + 资格试跑证据；率研究执行归 `P1-M2-RATE-002`；
- **依赖声明**：验收 4 的资格试跑依赖 `P1-M2-RATE-002` 的起跑屏障与单调时钟基础设施先通过其停点；本项验收 1–3 可先行。

## Acceptance criteria

1. **适配层与失败路径测试**（修订 6）：既有 fake-tracker/帧序套通过；新增覆盖——模型缺失/损坏/哈希不匹配、构造器/update 异常、非有限或越界分数、无效框、tracker 选择错误、manifest 身份往返、无网络确定性加载；
2. **安装冒烟**：两个模型 SHA-256 与来源记录、构造器可用、`pip check` 通过；
3. **时延预算**：本机 640×480 compute p95 **< 50 ms**（CPU target）；
4. **资格试跑（修订 5，预声明；亦为 `P1-M2-RATE-002` 的资格门，单次共用）**：在修正后的机器起跑屏障协议下一次全新会话，完整实况路径 + 声明的 warm-up 策略，要求：无 gap/reinit、compute p95 < 50 ms、follow 条件 `C_track_given_geom ≥ 25%` 且首次 LOST（或漂移主导发生）前 ≥ 30 s。**失败即拒绝本冻结候选、返回设计，不得用试跑数据调参**；
5. **遮挡冒烟（描述性）**：Cube 遮挡下分数轨迹与漂移事件对照记录；明示该观察不能证明校准丢失语义；
6. **边界与零微调审计**：无真值读取；运行前后模型哈希一致；`threshold_source="none"` 入 manifest；
7. Unity 用例 `UT-P1-TRACK-002-001`：用户观察资格试跑会话并反馈。

## Baselines and ablations

本项不产出对比数字；对比在 `P1-M2-RATE-002`（2×2×3）进行；CSRT 对照行 = M2a 归档数字。

## Failure modes and resource risks

- **NanoTrack-v2 在低多边形合成图像上失效**：资格试跑（验收 4）直接拦截 → 候选被拒、返回设计重议（下一步可能指向 detector-only 基线提案或渲染保真度问题），不烧 12 次用户会话；
- **模型供应链**：来源 URL + commit + SHA-256 + 许可证记录；哈希不匹配 fail-closed；
- **分数不可校准**：已按 §2 收窄主张，不构成本项风险。

## Suggested implementation scope

一个实现批次：插件类 + 选择器贯通 + 测试 + 身份矩阵与冒烟证据。**Out of scope**：L1–L4、ReID、YOLOE 仲裁/检测通道（`P1-DETECT-001` 另案）、率研究执行、CSRT 移除、任何阈值选定或权重改动。

## Open questions

无实质开放项；模型 URL/commit/哈希等身份矩阵数值在实现时填入并经 Sonnet 复核。

## Codex review decision

### Round 1 — 2026-07-24: REVISION_REQUESTED

Decision: **REVISION_REQUESTED**

Rationale:

The user-authorized move away from CSRT's demonstrated floor is sound, and the
existing `TrackerPlugin` / `TrackerResult` boundary is the right integration
point. The local pinned OpenCV build already exposes `TrackerNano_create` and
`TrackerNano_Params`, so a small, reproducible NanoTrack-v2 adapter is more
credible than adding an unspecified ncnn or general ONNX runtime. OpenCV's
documented Nano tracker uses two ONNX models (backbone and neck/head), exposes
`getTrackingScore()`, and links the NanoTrack-v2 model source directly:
<https://docs.opencv.org/4.x/d8/d69/classcv_1_1TrackerNano.html>.

The current proposal is not implementation-ready. Its Option A leaves the
actual model release, backend, license, and threshold unresolved. More
importantly, OpenCV's upstream Nano implementation returns `true` from every
normal update and only exposes an uncalibrated tracking score; it contains no
default loss threshold:
<https://github.com/opencv/opencv/blob/4.x/modules/video/src/tracking/tracker_nano.cpp>.
Therefore the proposal cannot yet claim that a "real confidence" automatically
fixes CSRT's unreported drift. Option B is a detector-driven channel, not a SOT
plugin, and folding it in as an automatic fallback would collapse the
SOT-only/detector-only distinction required by the accepted architecture.

The stated implementation scope also understates the real interface work.
`controller.track_loop.run_tracker()` currently constructs `CsrtTracker`
unconditionally, and `tools.run_rate_study` has no tracker selector. A new
class alone cannot become the rate-study vehicle or produce an auditable model
identity.

Required revisions:

1. **Select one concrete SOT implementation.** Use the already-available
   OpenCV `TrackerNano` API with the upstream NanoTrack-v2 backbone and
   neck/head ONNX pair unless a documented blocker is found. Record exact
   source commit/URLs, both model SHA-256 values, code/model license, OpenCV
   pin, DNN backend, and CPU target. Remove the vague "ONNX/ncnn release"
   choice from the accepted path.
2. **Remove Option B from this work item.** YOLOE detector-driven tracking may
   be proposed separately as an M4 detector/arbiter or explicit detector-only
   baseline. It must not silently substitute for SOT or inherit this work
   item's verdict.
3. **Resolve score and LOST semantics before implementation.** State the exact
   formula and pre-data source for any threshold applied to
   `getTrackingScore()`. The rate-study or Unity truth may not tune it. If no
   defensible external threshold exists, the plugin must report the score
   without claiming calibrated LOST detection, and the proposal must either
   choose another frozen tracker or explicitly narrow its research claim.
   Threshold sensitivity on project data is descriptive only and cannot select
   the deployed value.
4. **Include the real selection path.** Add a validated
   `--tracker nanotrack-v2` (or equivalent versioned configuration) to
   `track_loop`, thread it through `run_track_experiment` and the rate-study
   launcher, and persist tracker name, backend, OpenCV version, model hashes,
   threshold/value source, and preprocessing identity in the manifest.
   Unknown or missing model identity must fail closed.
5. **Strengthen the pre-campaign qualification gate.** After the corrected
   deterministic-start protocol exists, run a predeclared fresh-session pilot
   before authorizing 12 measured sessions. It must include the complete live
   path, warm-up policy, compute p95 `<50 ms`, no gap/reinit, and a non-floor
   correctness requirement such as `C_track_given_geom >= 25%` plus at least
   30 s before first LOST in follow. Failure rejects this frozen candidate;
   it must not trigger tuning on the pilot.
6. **Correct the scope and tests.** Cover model-missing/corrupt/hash-mismatch
   failures, constructor/update exceptions, non-finite/out-of-range score,
   invalid box, tracker selection, manifest round-trip, and deterministic
   model loading without network access. The Unity occlusion smoke remains
   descriptive and cannot by itself prove calibrated loss semantics.

Accepted design-document changes:

None in this round. The existing v0.3.1 preference for a NanoTrack/HiT-small
class SOT remains unchanged until a concrete, reproducible plugin proposal is
accepted.

### Round 2 — 2026-07-24: ACCEPTED_WITH_BINDING_CLARIFICATIONS

Decision: **ACCEPTED_WITH_BINDING_CLARIFICATIONS**

Rationale:

Round 2 resolves the six design blockers. It selects one concrete OpenCV
TrackerNano/NanoTrack-v2 path, removes the detector fallback, narrows the claim
instead of inventing a calibrated loss threshold, includes the real
CLI/manifest selection path, adds fail-closed model identity, and shares one
predeclared live qualification gate with the successor study. The adapter,
selector, offline tests, model acquisition, and standalone latency evidence
may enter implementation now.

Binding implementation clarifications:

1. **Artifact identity precedes implementation completion.** Pin an immutable
   upstream commit and exact backbone/neck-head URLs before accepting the
   downloaded files. Record both SHA-256 values and affirmative license
   evidence covering the model artifacts, not only OpenCV code. Missing or
   ambiguous model licensing blocks the candidate; it is not deferred to
   publication.
2. **No implicit threshold or fallback.** `getTrackingScore()` is recorded
   unchanged after finite/range validation. Normal updates do not become LOST
   by score, and no model-load/update failure may fall back to CSRT. Existing
   image-clipping semantics remain centralized in
   `_publication_ready_result`; the plugin must not introduce a second,
   conflicting box policy.
3. **Make the shared pilot mathematically executable.** Replace the ambiguous
   phrase "LOST (or drift dominance) occurs after 30 s" with a fixed
   post-release 30 s evaluation window. Admission requires all of:
   S1′–S3, no LOST/GAP/reinit in that window,
   `C_track_given_geom >= 0.25`, `matched_tracking_observations > 0`, and
   `incorrect_tracking_observations / matched_tracking_observations < 0.5`.
   The ratio uses evaluator definitions, is computed over that fixed window,
   and cannot tune weights, preprocessing, or a score threshold.
4. **Gate semantics.** Core code may reach a Sonnet stable-candidate stop
   before `P1-M2-RATE-002` infrastructure exists, but this runtime work item
   cannot become `DONE` until the shared pilot and user Unity case pass.

Required revisions:

None before implementation. Synchronize Acceptance 4 wording with
clarification 3 when the successor proposal is revised.

Accepted design-document changes:

- Record OpenCV TrackerNano/NanoTrack-v2 as the concrete frozen deep-SOT
  candidate for desktop simulation.
- Keep raw Nano tracking score descriptive and explicitly decline a calibrated
  LOST claim.
- Keep YOLOE detector/arbiter work outside this SOT item.

## Round 2 revision map（修订 → 落点）

| Codex 修订 | 落点 |
|---|---|
| 1 唯一具体实现 | §1（OpenCV TrackerNano + NanoTrack-v2 双 ONNX + 身份矩阵；移除 ncnn/泛 ONNX 措辞） |
| 2 移除 Option B | §4（YOLOE 通道另案 `P1-DETECT-001`，不继承 verdict） |
| 3 分数/LOST 语义 | §2 + Problem 主张收窄段（无阈值、不宣称校准丢失、后果声明给 RATE-002） |
| 4 真实选择路径 | §3（`--tracker` 贯通 + manifest 身份 + fail-closed）；Inputs/outputs |
| 5 资格试跑门 | Acceptance 4（预声明判据、失败拒候选、禁调参；与 RATE-002 资格门共用） |
| 6 范围与测试 | Acceptance 1/5（失败路径全覆盖；遮挡冒烟明示描述性） |
