# P1-EVAL-001 实现证据（评估器/传感器视锥 aspect 一致性）

Work ID：`P1-EVAL-001`（workflow §4.2 缺陷立项于
`docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md` round 4 §G，
逐条实现契约见同文件 round 7 §C；BC-BODY1-17）。
本批次是该缺陷修复的唯一实现批次，自身 §4.3.1 停点，**不含** 1b/1c/Play。

## 1. 范围与边界声明

- 改动文件（全部）：
  - `Assets/TetheredTracking/Scripts/CoverageEvaluator.cs`（实现）；
  - `Assets/TetheredTracking/Tests/EditMode/TetheredTrackingEditModeTests.cs`
    （3 个新投影测试 + 1 个新 metrics 记录测试 + 1 处既有调用点适配）；
  - `Assets/TetheredTracking/Tests/EditMode/P1DetectScoutingEditModeTests.cs`
    （1 处调用点适配）；
  - `Assets/TetheredTracking/Tests/EditMode/Scene006EditModeTests.cs`
    （2 处调用点适配）；
  - `docs/current-status.md`（状态）、本证据文件。
- **未触碰** `SensorFrameWriter`、帧/控制协议、scenario/config 字节、设计 §6
  指标定义/公式/阈值；既有 `tethered-evaluation/v1` 字段零删除、零改名、
  零改义（纯追加一个顶层对象）；既有 `C_geom` 族结果不重跑、不重开
  （BC-BODY1-17 (e) 披露立场不变）。
- 零 Play、零 scenario/session/run ID、零配额消耗；Unity 仅 batchmode
  Edit Mode 测试。

## 2. 缺陷事实（round 4 §C 认定，本批次不重述论证）

`SensorFrameWriter.Capture` 挂上 640×480 RenderTexture 渲染（JPEG 是正确的
4:3）后在 `:173` 置 `camera.targetTexture = null`，之后才发布帧；
`CoverageEvaluator.OnFramePublished` 的 `WorldToViewportPoint` 因此按当时
Game view/屏幕 aspect 投影。真值评估器与传感器图像可能不是同一视锥，方向是
抬高 `C_geom` 并使 `C_quality` 的 `areaPixels`/`centerError` 与真实图像口径
不符。属 M0 冻结代码既有缺陷。

## 3. 实现内容（对照 round 7 §C 逐条）

### 3.1 契约 1：投影来源唯一

- 新增 `CoverageEvaluator.SensorAspectOrThrow(ScenarioConfig)`：评估投影
  aspect 的**唯一来源**，即 `config.sensor.width / (float) config.sensor
  .height`；`config == null`、`sensor == null` 或 width/height 非正时抛
  `InvalidOperationException("evaluation_sensor_dimensions_invalid")`
  （fail-closed，绝不回落到相机当前 aspect）。`ScenarioConfig.Normalize`
  既有行为把 width/height 钳入 `[64, 4096]`（`ScenarioConfig.cs:263-264`），
  本 guard 是其后的第二道保险。
- `Start()` 在 config 赋值后立即绑定 `evaluationAspect =
  SensorAspectOrThrow(config)`——**首个评估帧之前**完成绑定，此后只读；
  测试路径 `ConfigureAggregationForTests` 同样绑定。默认场景有效值
  `640/480`。
- 新增纯函数 `WorldToSensorViewportPoint(camera, worldPoint,
  sensorAspect)`：以钉住 aspect 复现 `Camera.WorldToViewportPoint` 的透视
  （垂直 FOV、非 physical）投影。**不读** Game view、Screen 或
  targetTexture 解除后的相机 aspect，**不改** 任何相机状态（无
  `camera.aspect` 写入，渲染路径零影响）。实现细节：
  `camera.worldToCameraMatrix` 是 OpenGL 约定（前方点 z 为负），实现取
  `forward = -cameraSpace.z` 回到 Unity 相机系再投影；z ≤ 0 的丢弃语义与
  `WorldToViewportPoint` 调用方完全一致。
- 评估器内**全部**投影点切到钉住实现，库内不再存在未钉住的
  `WorldToViewportPoint` 调用：
  - `EvaluateVisibility` 15 点视锥采样（原 `:740`）；
  - `ProjectBounds` 真值框（原 `:790`），签名加 `float sensorAspect`；
  - `ProjectRenderers`（scouting 真值 distractor 框）透传钉住值，
    `WriteScoutingTruth` 调用点传入 `evaluationAspect`。

### 3.2 契约 2：逐 run 可核验记录

`MetricsDocument` 末尾追加顶层 `evaluation_projection`（追加位置即 JSON
字段序末尾），**恰含** `sensor_width_px`、`sensor_height_px`、
`aspect_width_over_height` 三键；`BuildMetricsDocument` 每次写
`metrics.json` 时填充，默认运行分别为 `640`、`480`、`640f/480f`。
`schema_version`、既有字段、公式、阈值不动。

下游兼容性（消费方核查）：Python 侧全部按 `.get()` 键查找校验
（`tools/run_rate_study.py:796/860`、`tools/run_rate2_study.py:697`、
`tools/run_rate3_study.py:1654`、`controller/track_loop.py:1500`、
`controller/qualification_protocol.py:680+`），无精确键集校验，追加键
零影响；C# 侧 `JsonUtility.FromJson` 忽略未知键。

### 3.3 契约 3：测试证伪旧缺陷（不只断言属性）

新增 4 个 Edit Mode 测试（`TetheredTrackingEditModeTests.cs`）：

| 测试 | 锁定内容 |
|---|---|
| `SensorProjection_MatchesUnityOracleAtPinnedAspect` | 相机 aspect 显式设为 16:9（≠4:3 sensor），钉住投影与「相机 aspect 强制为 640/480 时 Unity 自己的 `WorldToViewportPoint`」逐点一致（多姿态多点，容差 1e-5）；同点 y 分量与 16:9 投影相同（垂直 FOV 与 aspect 无关）、x 分量不同 |
| `SensorProjection_FalsifiesGameViewAspectDependency` | 构造 16:9 视锥内、4:3 视锥外的边缘点（z=10、x=9、垂直 FOV 60°）：旧路径 `camera.WorldToViewportPoint` 判「在锥内」（x≈0.938），钉住投影判「出画」（x≈1.085）——正是被抬高 `C_geom` 的那类样本 |
| `ProjectBounds_PinnedToSensorAspectUnderMismatchedCameraAspect` | 真值框级：钉住 `ProjectBounds` == Unity oracle（aspect 强制 4:3 手工投影），≠ 16:9 投影的宽度、== 其高度 |
| `SensorAspect_NonPositiveDimensionsFailClosed` | width=0 / height=-1 抛 `InvalidOperationException`；既有 config 校验行为锁定（Normalize 把 0/-3 钳为 64）；默认值恰为 `640f/480f` |

另有 `MetricsJson_RecordsPinnedEvaluationProjection`（聚合测试类）：锁定
`MetricsJsonForTests()` 中 `evaluation_projection` 对象存在、**恰含三键**
（按对象体逗号计数）、值为 640/480/640f/480f，且
`schema_version`/`thresholds`/`aggregate`/`occlusion_geometry` 既有键仍在。

既有调用点适配（编译必需，断言语义不变）：
`ProjectBounds_UsesNormalizedTopLeftOrigin`（aspect=1，与相机 aspect=1
一致，等价性不变）、`P1DetectScoutingEditModeTests:347`（640/480）、
`Scene006EditModeTests` 两处（640/480，与 probe 相机创建即钉住的 aspect
一致——该测试同时充当钉住实现 vs Unity oracle 的多姿态等价校验，含
相机背对返 null 用例）。

### 3.4 契约 4：窄范围

见 §1 文件清单；零 `SensorFrameWriter`/协议/scenario/公式改动，零重跑。

### 3.5 契约 5：自身停点

精确候选、测试与未验证风险记录于本文件 §5/§6；候选提交后交 Acceptance
执行 §4.3.1 五条件（含 implementation 写入审计），Review PASS 前不开始
1b、1c 或 Play。

## 4. 批次内返工记录（诚实披露）

首次实现误用 `worldToCameraMatrix` 的 z 符号（OpenGL 约定前方为负 z），
Edit Mode 复跑 6 项失败（4 个新测试 + 2 个既有等价测试全部按预期方向
暴露该缺陷——测试证伪能力间接验证）。修为 `forward = -cameraSpace.z`
后剩 2 项失败：(a) 新测试 `ProjectBounds_Pinned…` 的**测试内** oracle
漏写 Clamp01 而评估框越右缘被裁——把测试 bounds 改为完整处于 4:3 与
16:9 两框内，oracle 无须自带裁剪语义；(b) 既有等价测试
`Scene006EditModeTests.ProjectionMatchesInternalProjectRenderers` 偏差
超容差。对 (b) 做了逐角点数值诊断（临时 `-executeMethod` 台架，用后
已删）：Unity 原生 `WorldToViewportPoint` 内部精度高于脚本侧暴露的
float 矩阵路径（同一角点 Unity 报 z=20.5 精确值，`worldToCameraMatrix`
float 报 20.5000038），两侧差异是**随场景坐标量级放大的浮点路径噪声**
——5000 m 探针坐标下实测 ≤1.4e-5（640 px 下约 0.009 px），生产距离
（百米级）下小两个数量级；公式无系统性错误（投影矩阵路径
`pm·cs/clip.w` 与本实现逐位吻合）。该等价测试容差定为 5e-5 并就地注释
（原为 1e-6，钉于两侧共享同一 Unity 调用的时代；结构级缺陷在 1e-4
量级仍会暴露，z 翻转即为其一）。第四跑全绿（§5）。
缺陷未离开本批次工作树。

另：首次 Unity 复跑误用 `6000.4.10f1`（项目钉住 `6000.4.1f1`，
`ProjectSettings/ProjectVersion.txt`），编辑器自动改写
`ProjectVersion.txt` 与 rider 包版本，已 `git checkout` 还原三文件；
最终证据全部来自 `6000.4.1f1`（与 P1-TEST-001 以来一致）。

## 5. 实际运行的命令与结果

```
.venv-track/bin/python -m unittest discover -s tests
# Unity Edit Mode（batchmode，项目钉住版本）：
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  -batchmode -projectPath ~/TetheredDroneTracking \
  -runTests -testPlatform EditMode -testFilter TetheredTracking.Tests \
  -testResults .../runtime/test-results/p1-eval-001-editmode.xml \
  -logFile .../runtime/test-results/p1-eval-001-unity.log
```

| 检查 | 结果 |
|---|---|
| 完整 Python 套件 | **424 项，1 项失败**——`tests/test_check_docs.py::test_compliant_minimal_status_passes` 既有失败，与本批次无关（两文件零触碰；1a-α §8 以来同一归因，仍待用户授权的协调批次修复） |
| Unity Edit Mode | **263/263 通过**（`runtime/test-results/p1-eval-001-editmode.xml`，6000.4.1f1，log 末尾 `Exiting with code 0`；较 1a-β 的 258 项恰 +5：3 个钉住投影测试 + 1 个 fail-closed 测试 + 1 个 metrics 记录测试） |

## 6. 未验证项与已知限制

1. **`WorldToSensorViewportPoint` 的适用前提**：透视、垂直 FOV、非
   physical、无 lens shift/斜投影——恰为运行时 SensorCamera 的构造
   （`TetheredScenarioBootstrap.cs:202-206` 只设 fieldOfView/near/far）。
   若未来传感器相机引入 physical 属性或正交模式，该函数须重审（不在
   本契约范围）。
2. **既有 `C_geom` 族数字的披露立场不变**（BC-BODY1-17 (e)）：它们在未
   记录、未受控的 aspect 下采集；本批次不重开、不重跑、不重新解释。
3. **每次 `WriteMetrics` 都带 `evaluation_projection`**（含 release 前的
   周期写）——这是契约 2 的逐 run 记录义务，非缺陷。
4. **真实 Play 下的端到端视锥一致性未验证**：本批次零 Play（契约边界）；
   运行时一致性由 1b COORD-005 人眼保真检查与 1c 承接。
5. RATE-003 评估真值 sidecar 的像素换算（`CoverageEvaluator.cs:437-442`
   旧行号）只做 normalized→px 缩放，本批次未改；其 box 输入现来自钉住
   投影，口径自洽。

## 7. 给复核角色的复核范围

精确候选 commit 与基线由 Acceptance 停点确认时钉定；预期 diff 即 §1
文件清单。重点核对项：

1. round 7 §C 五条逐条符合（§3 对照表）；
2. 评估器内无残留未钉住 `WorldToViewportPoint`（全库 grep）；
3. `WorldToSensorViewportPoint` 数学正确性（z 符号、x/y/z 三分量、
   z≤0 丢弃语义）与「不读相机 aspect、不写相机状态」；
4. `evaluation_projection` 恰含三键、追加位置、既有字段零变化（可对比
   候选与上一候选的 `MetricsDocument`）；
5. 测试是否真正证伪（契约 3 禁止只断言 `camera.aspect` 数值）：边缘点
   测试的几何数字（16:9 内 / 4:3 外）请独立复算；
6. **既有测试改动两处**：`Scene006EditModeTests.ProjectionMatches…`
   等价容差 1e-6 → 5e-5（§4 (b)：根因为 Unity 原生路径与脚本 float
   路径的精度差，噪声随坐标量级放大，5000 m 探针坐标实测 ≤1.4e-5；
   这是本批次唯一改动的既有断言强度）；三个调用点仅追加 aspect 实参；
7. Python 消费方兼容性（§3.2 清单）；
8. 窄范围边界：diff 中无 `SensorFrameWriter`、协议、scenario、公式/
   阈值改动。

## 8. 交回接受角色的待裁事项

1. **`Scene006Visibility.cs:155-156` 与 `:199-200` 的文档注释引用
   `CoverageEvaluator.cs` 行号（`781-812`/`500-510`），本批次后偏移**
   （新位置 `:853`/`:521` 附近）。该 Editor 文件在窄范围之外，本批次未
   动；语义复制关系不变（Scene006 台架创建即钉
   `EvaluationCamera.aspect = imageWidth/imageHeight`，两侧仍在采集
   aspect 投影，等价测试通过）。请裁定由谁、在何批次修正行号引用
   （性质同 N7 文档准确性）。
2. 状态板 `P1-EVAL-001` 行待 Acceptance 停点审计后翻转；N7–N10 与 1c
   门禁不变。
