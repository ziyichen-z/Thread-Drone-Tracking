# P1-EVAL-001 independent review

Status: ROUND_1_PASS_WITH_NOTES (candidate `61ea20b`)

Round history: round 1 `PASS_WITH_NOTES`（`61ea20b`）。轮次只追加，旧发现
不删除。

Reviewer: review 角色（independent review, strongest pool; fresh context）

Implementation author: implementation 角色（Cursor）

## Round 1 — 评估投影钉住 + 逐 run 投影记录

Date: 2026-08-07

- Accepted contract: 提案 round 4 §G 缺陷立项 + BC-BODY1-17、round 7 §C
  五条逐字实现契约、round 8 §B 复核范围
  （`docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md`）。
- Candidate: `61ea20b`（精确实现区间 `0762ba6..61ea20b`；上一复核通过
  代码候选 `a234270`）。复核前用户释放推送
  （`docs/authorizations.md` 2026-08-07 条），候选链已推送至
  `origin/main`，本轮复核对象与推送内容为同一提交。
- 复核副本：`git worktree add --detach
  .claude/worktrees/review-P1-EVAL-001 61ea20b`，收工已删除。主树实现
  文件零修改。
- 范围主张按纪律视为待核实，不作为复核边界；候选与两个基线的全部变更
  逐文件核对。

### 1. 变更完整性与区间归因

`git diff 0762ba6..61ea20b --stat`：恰 5 个路径（`CoverageEvaluator.cs`
+102、三个 EditMode 测试文件、证据文件 +202），与声明零偏差。全区间
`a234270..61ea20b` 的额外 6 个文档路径逐文件 `git log` 归因：`d9a0b11`
（1a-β 批次记录）、`718fa45`/`0762ba6`（Acceptance rounds 6/7）、
`4788aff`（Review round 2）——区间内唯一实现代码提交就是候选本身，与
round 8 条件 5 审计结论一致。diff 内容层面：零 `SensorFrameWriter`、零
帧/控制协议、零 scenario/config 字节、零设计 §6 公式/阈值改动；
`MetricsDocument` 既有字段零删除、零改名，`schema_version` 保持
`tethered-evaluation/v1`。

### 2. 测试全部自跑（不采信报告数字）

| 项 | 实现者/接受者声明 | 本轮独立复跑（副本内） |
|---|---|---|
| Unity EditMode `TetheredTracking.Tests`（6000.4.1f1，batchmode，全新 Library） | 263/263 | **263/263 Passed, failed=0**（结果 XML `total=263`；5 个新增测试与改容差等价测试全部在列并通过） |
| 完整 Python 套件（.venv-track） | 424 / 1 失败 | **424 ran / 1 failure**，唯一失败 = 既有 `test_check_docs.test_compliant_minimal_status_passes`；两文件在 `a234270..61ea20b` 零差异，归因附议不变 |

环境注记（N-EVAL-3，见 §8）：新鲜副本首跑 Python 曾出现 26 失败 + 4
错误，全部集中于 `test_scene006_probe`，探针诊断根因为
`FAIL_WEIGHT_HASH`——副本缺少 gitignore 的 `runtime/yoloe`、
`runtime/models` 权重文件，权重哈希门按设计 fail-closed。从主树复制
权重（只读资产）后复跑即得上表结果。此为副本环境效应，非候选缺陷；
反而实证了权重哈希门的 fail-closed 行为。

### 3. `WorldToSensorViewportPoint` 数学独立复核（round 8 §B 条 2）

- **z 约定**：`worldToCameraMatrix` 为 OpenGL 约定（前方 z 负），实现取
  `forward = -cameraSpace.z` 复原 Unity 相机系；返回 z = forward，与
  `WorldToViewportPoint` 的「前方为正距离」语义一致。
- **x/y 公式**：`x = 0.5 + 0.5·x_cam/(forward·tan(fov_v/2)·aspect)`、
  `y = 0.5 + 0.5·y_cam/(forward·tan(fov_v/2))`——垂直 FOV 定义下
  aspect 只作用于水平分量，正确。
- **z≤0 丢弃语义**：两个调用点保持原判据（采样点 `viewport.z > 0f` 门、
  角点 `viewport.z <= 0f` continue）。forward = 0 时除零产生
  ±Inf/NaN，两门的比较均判 false → 丢弃，fail-closed 方向。
- **运行时相机前提**：`TetheredScenarioBootstrap.CreateDrone` 中
  SensorCamera 由 `AddComponent<Camera>` 默认构造，仅设
  `fieldOfView = config.sensor.vertical_fov_deg`/near/far——透视、非
  physical、无 lens shift、无自定义投影矩阵，与钉住数学假设逐条吻合。
- **不读不写相机状态**：函数体只读 `worldToCameraMatrix`（transform
  派生）与 `fieldOfView`，零 `camera.aspect`/`Screen`/Game view 读取，
  零相机状态写入。测试路径中 oracle 对 `camera.aspect` 的读写只在
  测试代码内。
- **评估器内无残留原生投影**：全库 grep 确认 `CoverageEvaluator.cs` 内
  `WorldToViewportPoint` 仅存于注释；两处投影调用点
  （15 点采样、`ProjectBounds`）与 scouting 真值 `ProjectRenderers`
  透传均已切到钉住实现。
- **绑定时序**：`config` 仅两处赋值（`Start()`、
  `ConfigureAggregationForTests`），二者紧跟
  `evaluationAspect = SensorAspectOrThrow(config)`；`Start()` 绑定先于
  事件订阅，故先于首个评估帧。`SensorAspectOrThrow` 对
  null/非正维度抛 `InvalidOperationException`，绝不回落相机当前
  aspect；`ScenarioConfig.Normalize` 的 `[64,4096]` 钳制为第一道防线
  （测试锁定）。

### 4. `evaluation_projection` 记录与下游兼容（round 8 §B 条 3）

- `MetricsDocument` 末尾追加顶层 `evaluation_projection`，序列化类恰含
  `sensor_width_px`、`sensor_height_px`、`aspect_width_over_height` 三
  字段；`BuildMetricsDocument` 每次构造填充（含 release 前周期写），
  `MetricsJson_RecordsPinnedEvaluationProjection` 以对象体逗号计数 +
  强类型反序列化双重锁定恰含三键与 640/480/640f÷480f 默认值。
- 下游兼容独立核查：`controller/track_loop.py:1492+` 只在运行终了按
  `.get()` 快照校验（非控制输入）；
  `qualification_protocol.validate_metrics` 只核对
  `qualification_release` 子对象；全库 grep 无任何 metrics 键集严格
  校验；C# 侧 `JsonUtility.FromJson` 忽略未知键。追加键零破坏。
- 真值泄漏检查：新增内容全部为 config 派生值且只进 `metrics.json`
  （评估器输出侧）；控制器、感知输入、对外传感器元数据零触碰。

### 5. 证伪测试独立复算（round 8 §B 条 4）

- 边缘点几何独立复算：fov 60°、z=10 → 半高 5.7735 m，16:9 半宽
  10.264 m，4:3 半宽 7.698 m；测试点 (9,0,10) 恰在两者之间。旧路径
  x = 0.5+0.5·(9/10.264) ≈ 0.938（判入），钉住路径
  x = 0.5+0.5·(9/7.698) ≈ 1.085（判出）——正是抬高 `C_geom` 的样本
  类型，测试确实证伪旧缺陷而非只断言属性。
- oracle 测试把相机 aspect 显式切到 640/480 取 Unity 原生投影为基准，
  再切回 16:9 验证「钉住 ≠ 失配投影」（x 异、y 同），bounds 级测试同
  构且带独立手写 min/max oracle；均非复述生产实现。
- fail-closed 测试覆盖 width=0/height=-1 抛出与 Normalize 钳制。
- 批次内返工记录（证据 §4）显示首版 z 符号错误被 6 项测试按预期方向
  暴露——测试证伪能力已被批次内事实验证。

### 6. 唯一既有断言弱化：等价容差 1e-6 → 5e-5（round 8 §B 条 5）

`Scene006EditModeTests.ProjectionMatchesInternalProjectRenderers` 现比较
钉住投影 vs `Scene006Visibility`（原生 `WorldToViewportPoint`）在同
aspect（测试相机显式 640/480）下的结果。独立判断：

- 浮点解释成立：两侧不再共享同一 Unity 调用，脚本侧 float32 矩阵路径
  在 5000 m 探针坐标下的相消误差（相对误差 ~1e-7 × 5000 m，除以前向
  距离）落在 1e-5 量级视口单位，与证据 §4 实测 ≤1.4e-5 吻合；5e-5 容差
  留有约 3.5× 裕度。
- 结构性缺陷不可被遮蔽：aspect 混用（16:9 vs 4:3）误差在 1e-1 量级、
  z 符号翻转导致 null/镜像、FOV 错误在 1e-2 量级——均高出容差 3 个
  数量级以上；且本批次 z 符号错误确实曾被该测试暴露。
- 本轮 263/263 复跑含该测试通过。**附议该容差变更**；它仍是本批次唯一
  既有断言强度改动。
- `Scene006SceneRig.cs:128` 台架创建即钉
  `EvaluationCamera.aspect = imageWidth/imageHeight`，证据 §8.1 主张
  属实：Editor 工具链与评估器仍在同一采集 aspect 下投影，语义复制关系
  成立。

### 7. `UNITY_NA` 立场

本项**未申领** `UNITY_NA`，正确：这是运行时评估器行为变更，端到端视锥
一致性由既定顺序 1b（COORD-005 人眼保真检查）与 1c 用户 Play 承接，
gate board Unity 列保持 `NOT_RUN`。复核角色对此明确**附议**。既有
`C_geom` 族数字保持披露不重跑立场（BC-BODY1-17 (e)），本轮未重开任何
历史结果。

### 8. Notes（全部非阻断）

| Note | 内容 | 到期点 |
|---|---|---|
| N-EVAL-1 | `Scene006Visibility.cs:155-156/:199-200` 注释引用的 `CoverageEvaluator.cs` 行号已偏移（新位置 `:853`/`:521` 附近）。附议 Acceptance round 8 §C 的 `NOTE_OPEN_DOC_ACCURACY` 归置：仅注释、语义复制关系经等价测试成立，不阻断 | 与 N7 一并在 1c 协议/证据冻结前修正 |
| N-EVAL-2 | `RateStudyScouting.ProjectRenderersUnclipped`（`RateStudyScouting.cs:159`，供 Rate3ScoutingTool/RateStudyScoutingTool）仍按相机当前 aspect 投影。它不属评估器、属冻结/递延的 RATE 资产（v0.3.10 语义冻结），本批次不触碰是正确的窄范围纪律；但 M5 若重启 RATE-003，复用该工具前必须重审其 aspect 语义 | RATE-003 作为 M5 敏感性资产重启前 |
| N-EVAL-3 | 新鲜复核副本缺少 gitignore 的 `runtime/yoloe`、`runtime/models` 权重会使 `test_scene006_probe` 以 `FAIL_WEIGHT_HASH` 级联 26 失败 + 4 错误（fail-closed 按设计工作）。后续复核会话建副本后应从主树复制这两个只读权重目录再跑全套 | 每次新鲜 worktree 复核开工时 |
| N-EVAL-4 | `WorldToSensorViewportPoint` 适用前提（透视、垂直 FOV、非 physical、无 lens shift）与当前 SensorCamera 构造逐条吻合（证据 §6.1 已披露）。未来传感器相机引入 physical 属性/正交/自定义投影矩阵时该函数必须重审 | 任何 SensorCamera 光学构造变更前 |

### 9. Verdict

**`PASS_WITH_NOTES`**。round 7 §C 五条契约与 round 8 §B 六条复核范围
逐条核实成立，无阻断缺陷；候选 `61ea20b` 的代码复核门通过。修复与
notes 归置交回 Acceptance；1b、1c 与用户 Play 按既定门序推进，本轮零
Play、零 scenario/session/run ID、零配额消耗，主树实现文件零修改。
