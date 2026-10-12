# P1-SCENE-006 batch 2 — 配置阶段证据（`C_b2config` 与正式离线 T1′）

Work ID: `P1-SCENE-006`（§33 `C_B2TOOL_REVIEW_PASSED / CONFIG_STAGE_AUTHORIZED`）
日期: 2026-08-04
角色: 实现（implementation）
依据: `docs/proposals/P1-SCENE-006-post-v2-anchor-route-amendment.md` §30
BC-B2-3/4/5/6/7/8 与 §33 的四步配置阶段交接；工具基线
`C_b2tool′ = b85f461`（独立 Review round 7 `PASS`，端点 `d21aafc..b85f461`）。

执行顺序按 §33 逐条：①影响面清单（本文件 §1，写任何配置字节**之前**完成）
→ ② self-diff 只含新配置的 `C_b2config` → ③ 在该 clean HEAD 上跑正式
离线 T1′ → ④ 停于 `C_b2`，不自行裁定 T1′ 门。

## 1. BC-B2-5 影响面清单：`config/scenario.default.json` 的直接读者

清单在写入新配置字节之前生成，逐项证明仍绑定旧文件。所有绑定都是**源码
字面量或常量默认参数**，没有目录扫描、没有按 `scenario_id` 查找、没有
"取 `config/` 下最新文件"一类动态解析——因此向 `config/` 增加一个文件在
构造上无法改变任何一条。

| # | 直接读者 | 位置 | 绑定方式 | 加入新配置后 |
|---|---|---|---|---|
| 1 | `ScenarioConfig.Load()`（运行时/Play 唯一装载入口） | `Assets/TetheredTracking/Scripts/ScenarioConfig.cs:144-146` | 先查覆盖槽 `runtime/scenario_config.json`，不存在则用字面量 `ProjectFile("config","scenario.default.json")` | 不变：两个操作数都是字面量，新文件名不在其中；本批次也不向覆盖槽安装任何文件 |
| 2 | `TetheredScenarioBootstrap`（①的唯一调用者） | `Scripts/TetheredScenarioBootstrap.cs:40` | 经 ① | 不变 |
| 3 | `P1Scene004AnchorEvidenceGenerator.Generate` | `Editor/P1Scene004AnchorEvidenceGenerator.cs:28-32` | 字面量 `"scenario.default.json"` | 不变 |
| 4 | `RoadSceneEvidenceGenerator` | `Editor/RoadSceneEvidenceGenerator.cs:98-101` | 字面量 | 不变 |
| 5 | `SceneCorridorEvidenceGenerator` | `Editor/SceneCorridorEvidenceGenerator.cs:36-39` | 字面量 | 不变 |
| 6 | `Scene006SceneRig.LoadFrozenScenario(out sha, fileName = DefaultScenarioPath)` | `Editor/Scene006/Scene006SceneRig.cs:24,36-46` | 常量默认参数 `"scenario.default.json"` | 不变：四个调用点都不传 `fileName` |
| 6a | └ `Scene006CandidateGenerator.cs:150` | | 经 ⑥ | 不变 |
| 6b | └ `Scene006EvidenceGenerator.cs:235`（`RenderProbeFrames` 基线） | | 经 ⑥ | 不变 |
| 6c | └ `Scene006EvidenceGenerator.cs:270`（`RunCandidateProbe`） | | 经 ⑥，**故意读旧默认**，只为取 BC-B2-5 的 `baseline_scenario_sha256` | 不变（这正是要求的行为） |
| 6d | └ `Scene006FinalistGenerator.cs:602` | | 经 ⑥ | 不变 |
| 7 | EditMode 测试 | `RoadSceneAuditEditModeTests.cs:99,120,157,870`、`Scene006EditModeTests.cs:51`（对默认配置取 SHA-256 钉死）、`SceneAdjustmentsEditModeTests.cs:16` | 字面量 | 不变；配置落盘后重跑全套 Edit Mode 是机械证据（见 §3） |
| 8 | `tools/run_track_experiment.py:19` `DEFAULT_SCENARIO` | | 字面量，argparse 默认值 | 不变 |

绑定到**其它**配置、与默认无关者（列出以示新文件同样不干扰它们）：
`P1Scene003AnchorEvidenceGenerator` → `scenario.p1-detect-scouting.json`；
`P1Scene004SceneEvidenceGenerator` → `scenario.p1-scene-004.json`；
`P1Rate003DifficultyEvidenceGenerator` → `Targets[]` 的
`scenario.p1-scene-004.json` 与 `scenario.p1-scene-004-d2.json`；写运行时
覆盖槽的三个 Python 安装器各自绑定自己的源（`run_detector_scouting.py:40`
→ `scenario.p1-detect-scouting.json`、`run_rate_study.py:31-32` → 5/20 Hz
rate-study、`run_rate3_study.py:126-129` → scene-004 四个变体）。无一读默认
配置，也无一会读到新文件。

**新入口显式选择新路径**：`RunCandidateProbe` 第 270 行读旧默认（仅为
`baseline_scenario_sha256`），第 271–277 行经常量
`Scene006CandidateProbe.CandidateConfigPath = "config/scenario.p1-scene-006.json"`
显式加载新配置——不是改默认指向，而是新入口自带路径。

**机械证据**：`git grep -n "scenario\.p1-scene-006\.json" -- Assets tools
tests config` 的全部命中为 `Scene006CandidateProbe.cs`（常量 + 文档注释）
与 `tests/test_scene006_probe.py`（v2 manifest fixture 字符串）。没有任何
既有读者能到达新文件；`DefaultScenarioPath` 与上表所有字面量在本阶段
diff 中零改动（`C_b2config` 的 self-diff 只含新增文件，见 §2）。

## 2. `C_b2config`：唯一新增配置

**`C_b2config = 0e6407b7a62e1f81231afe82dfa7f9233acbabf1`**；其 self-diff
为单条 `A config/scenario.p1-scene-006.json`（`git show --name-status`
可复核），既有配置文件零改动。

`config/scenario.p1-scene-006.json` 以 `config/scenario.default.json` 为
基底逐字节复制，仅改 BC-B2-3/4 列明的字段：`scenario_id`、
`anchor_world_m`、`drone.initial_altitude_m`、`sensor.vertical_fov_deg`、
`target.route_world_m`、`scene_adjustments.vehicle_relocations` 与
`expected_distractor_count`。其余字段（schema、random_seed、
road_data_sha256、drone 其余 5 项、gimbal 2 项、sensor 其余 5 项、target
的 track_id/speed_mps、evaluation 3 项、route_corridor 9 项）保持默认
配置的字节与取值。既有配置文件零改动。

### 2.1 写入前的离线逐项核对（float32 语义复算）

在提交之前用独立 Python 复算（`numpy.float32`，与 Unity `JsonUtility`
的单精度解析同口径），逐条复现 `LoadAndBind` 将执行的检查，全部通过、
零失败：

- `scenario_id = p1-scene-006-difficult-v1`；anchor x/z 精确等于
  197.0/30.0；anchor y 解析为 `1.3113417e-06`，与冻结常量差 ≤ 1e-9。
- 高度 16.0 与 vfov 40.0 同时等于已复核 P3 决赛点（工件 `P3_OK`）。
- 路线八顶点逐点等于"默认路线 + (+60,−60)、y 不变"的 float32 结果——
  两个坐标基与 ±60 在 float32 中均可精确表示，无舍入，故为**位级相等**
  （不依赖 `Vector3 ==` 的容差带）。同时与 §3.3 公布的八点字面量一致。
- 五行 relocation 各自唯一匹配 `Scene006CandidateContract.FamilyBRelocations`
  （prefab + original xz，1e-4 带内），`match_tolerance_m = 0.1`、
  `mark_as_distractor`/`remove_from_scene` 全 `false`、落点在 1e-4 带内、
  `expected_distractor_count = 0`（BC-B2-4）。两行同 prefab 的皮卡相距
  58 m，0.1 m 匹配带不可能混淆。
- BC-B2-3 未列的全部标量逐项等于默认配置，含 F17 新增扫描的
  `schema_version` 与两个 corridor bool。
- `FromJsonStrict` 在出现 `scene_adjustments` 时强制存在的 8 个字段齐备。

该复算是写字节前的自检，**不替代**工具侧绑定：权威判定仍是
`RunCandidateProbe` 内 `LoadAndBind` 的 fail-closed 结果（§3）。

## 3. 正式离线 T1′

**终态：`tool_state = FAIL`（`RECALL_BELOW_FAIL_MAX`），`gate_state = null`。**
工件：`docs/evidence/P1-SCENE-006-probe-candidate-40deg.json`。按 §33 第 3
条如实返回，未做任何补救（见 §3.4 末段）。

### 3.1 采集身份（§5.6 双字段，本次是 F16 修复后的第一次真实使用）

| 字段 | 值 |
|---|---|
| `capture_commit` | `0e6407b`（`C_b2config`，clean HEAD） |
| `tool_commit` | `b85f461`（Review round 7 `PASS` 的工具候选） |
| `git_status_porcelain` | `""`（采集前置，非空即拒） |
| `frozen_tool_paths` | 9 条（batch-1b 停点记录集合，写入 manifest） |
| `tool_path_zero_diff_verified` | `true` |
| 场景零写入 | `scene_file_sha256` before = after = `dec58698…c9bf` |

两个 commit **不相等**，正是 round-6 F16 指出的合法 formal-T1′ 形态：若
仍按旧代码盖 capture HEAD，本次工件会把 `0e6407b` 记成 `tool_commit`、
使零 diff 证明区间为空。工具在进程内完成推导与证明；我另在壳层用同一
pathspec 复算 `b85f461..0e6407b` 对冻结路径零 diff（空输出）。

采集命令（渲染需要图形设备，故不加 `-nographics`）：

```bash
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  -batchmode -projectPath ~/TetheredDroneTracking \
  -executeMethod TetheredTracking.Scene006.Scene006EvidenceGenerator.RunCandidateProbe \
  -quit -logFile runtime/test-results/p1-scene-006-probe-candidate.log
```

### 3.2 渲染前 fail-closed 绑定链（全部通过）

- 候选 config SHA-256 `ec4154d1…c831`；旧默认 config SHA-256
  `f9c92052…2ce3`（`baseline_scenario_sha256`，BC-B2-5）。
- P3 工件 `docs/evidence/P1-SCENE-006-p3-finalist.json` SHA-256
  `87b24e7e…0578`，状态 `P3_OK`。
- `trace_sha256 = 46036a6c…326c` 与 P3 `finalist_trace_sha256`
  **逐位相同**；`s_init = 184.22793579101562` 相同——候选 config 的路线
  字节因此在探针期被闭合到 float32 位级（round-6 F19(a) 依据的机制，本次
  实测成立）。
- 发现的 `k* = 2` 等于 P3 `t6.k_star = 2`（`expected_k_star` 在写 manifest
  之前前置校验）。
- 106 个预注册 tick 全部渲染 + 提示帧 `prompt_000002.jpg`。
- 权重绑定校验 `verified = true`；`model_identity` 记录检测器
  (`8e439445…`)、DINOv2 权重 (`b938bf1b…`)/源码 (`c27dcdaf…`)、
  NanoTrack backbone/neckhead 与两份模型清单的 SHA-256（BC-B2-5）。

### 3.3 消费端七步链结果（BC-B2-6）

```bash
.venv-yoloe/bin/python -m tools.run_scene006_probe analyze \
  --probe-root runtime/p1-scene-006/probe-candidate-vfov40 \
  --output docs/evidence/P1-SCENE-006-probe-candidate-40deg.json
```

| 项 | 值 | 门 |
|---|---|---|
| 完整性 | 图像 106/106、truth 106/106、缺失 0 | 无 `PROBE_INCOMPLETE` |
| 保真 | `fidelity_contradictions = []` | 无 `PROBE_FIDELITY_CONTRADICTION` |
| V=1 tick | 52 | — |
| 目标样本 | **52** | ≥ 40 ✓ |
| 干扰样本 | **112** | ≥ 40 ✓ |
| **recall** | **4/52 = `0.076923`** | `< 0.85` ⇒ **`FAIL`** |
| `gate_state` | `null`（owner = acceptance） | 工具永不写 `PASS` |

嵌入层（`report_only = true`，不参与 recall 判定）：target cosine 中位
`0.5824`、max-distractor cosine 中位 `0.4003`、margin 中位 `0.1939`
（p05 `−0.0647`）、冻结 0.5/0.1 双门通过 `32/52 = 0.6154`。

### 3.4 失败形态的只读刻画

> **F22 口径更正（2026-08-04，T1′ 平价重定 amendment §3.4.3）**：本节原
> 把 `44.07 px` 标成 `p05`，实为 52 个样本按升序的**第三小值**
> （lower / nearest-rank）。同一样本的 type-7 `p05` 是 `48.67 px`
> （`docs/evidence/P1-SCENE-006-prompt-selection-p2.json` 的
> `min_side_band.q05 = 48.67423629760742` 独立复算得同值）。两种口径
> 永不共用 `p05` 标签。无门影响：本节是只读刻画，未参与任何判定。

以下全部由已产出的工件与 truth 边车统计得出，**没有重跑、没有挑帧、
没有改动任何参数**：

- **目标不小**：52 个 V=1 tick 的 `target_min_side_px` 最小 `25.09`、
  **第三小值（lower / nearest-rank）`44.07`**、type-7 分位 `p05 = 48.67`、
  中位 `74.47`、最大 `107.79`；slant `21.4–36.6 m`；52 帧
  `target_box_status` 全为 `OK`，`visible_sample_fraction` 中位 `1.000`。
  即失败不是"目标太小/投影不出来"。
- **检测器多数帧完全没有重叠提议**：52 个样本中 47 个
  `maximum_target_iou = 0.000`；命中的 4 帧（k = 390/395/510/520）IoU 为
  `0.951/0.936/0.862/0.878`——检到时定位很准。
- **不是候选配置引入的新现象**：同一冻结工具与模型的 batch-1 基线
  （60° vfov，`docs/evidence/P1-SCENE-006-probe-60deg.json`）`tool_state`
  同为 `FAIL`，recall `16/99 = 0.1616`。候选光学下更低，但两者都远低于
  0.85 下限。
- 按 §33 第 3 条与 BC-B2-7：**未**修改帧集、样本下限、阈值、FOV、锚点、
  路线、车辆或模型，**未**重跑或换种子来"救"这个数，也**不**在此裁定
  最终 T1′ 门——那是 Acceptance 的单列 disposition。

### 3.5 新配置落盘后的回归

- Unity Edit Mode **225/225 通过**
  （`runtime/test-results/p1-scene-006-editmode-b2config.xml`）——其中
  `Scene006EditModeTests` 对**默认**配置取 SHA-256 的钉死用例通过，是
  §1 清单第 7 项"新配置不扰动默认读者"的机械证据。
- Python `.venv-track/bin/python -m unittest discover -s tests`：
  **326 项，1 失败 = 既有 F3**（`test_check_docs`，协调基线破损，与本批
  无关），与配置落盘前一致。

## 4. 未验证项与已知限制

- 探针目录落在 `.gitignore` 的 `/runtime/*` 内，帧与 manifest **不进
  版本库**；进版本库的是分析器唯一写出的门工件。复现路径是 §3.1/§3.3
  两条命令（同一 `C_b2config` + 同一冻结工具决定性重放）。
- 顺带更正 round-6 F19(e) 的操作注记：探针产物是**被忽略**而非仅未跟踪，
  因此不会弄脏后续运行的 porcelain——本次 `RunCandidateProbe` 结束后
  `git status --porcelain` 仍只列出分析器新写的门工件。
- `tool_state = FAIL` 是**工具终态**，不是最终门裁定；`gate_state` 为
  `null`、`gate_state_owner = acceptance`。
- 嵌入层数值为 report-only 参考量，本阶段不构成任何门。
- 本阶段仍零 Play、零正式 capture、零 scenario/session/run ID；运行时
  `Scripts/`、M3′、DETECT criterion 4、BC-M34-7 与主指标零改动
  （BC-B2-8）。

## 5. 复核范围与 Unity 用例

- 提交序列：`e00d88b`（§1 清单证据）→ **`C_b2config = 0e6407b`**
  （self-diff 仅新增 `config/scenario.p1-scene-006.json`）→
  **`C_b2 = d2db9f3`**（本停点：T1′ 门工件 + 本证据 + 状态板）。
  独立复核端点 **`d21aafc..d2db9f3`**。
  Acceptance 的写入审计基线仍是 `d21aafc`（BC-B2-7）。
- 复核重点建议：候选 config 字节对 BC-B2-3/4 的逐字符合性（§2.1 的独立
  复算可复跑）；§5.6 双字段身份与零 diff 证明在真实 formal 路径上的正确
  性（§3.1）；T1′ 七步链的完整性/样本下限/recall 计算是否按冻结协议执行；
  以及"失败形态刻画"是否只用了已产出数据、未越权解释。
- Unity 用例：本阶段无用户 Play 用例（BC-B2-8）。原计划的"用户非 Play
  视觉检查五辆落点与场景合理性"是否仍在 T1′ `FAIL` 之后进行，由
  Acceptance 在处分中决定；实现角色不代行。
