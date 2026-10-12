# P1-SCENE-006 batch 1 — 实现者证据

Work ID: `P1-SCENE-006`（batch 1，共两批；batch 2 未授权、未实施）
日期: 2026-08-02
角色: 实现（implementation）
依据: `docs/proposals/P1-SCENE-006-difficulty-scene-rebuild.md` revision 4
（Acceptance round 5 `ACCEPTED_WITH_BINDING_CLARIFICATIONS`，BC-SC6-1–6；
正式设计 v0.3.12）

## 1. 范围与边界符合性

只实施了已接受的 batch 1：T1–T6 工具/测试、现场景（60° 光学）
T1–T5 对照基线、环心 10 m 候选格零写入 T5 preflight、T1′ 探针工具
（含 60° 自检）。未实施 batch 2 的任何部分。

- 写入路径严格限于 BC-SC6-1：新增
  `Assets/TetheredTracking/Editor/Scene006/`（新 asmdef + 10 个工具文件）、
  `Assets/TetheredTracking/Tests/EditMode/Scene006EditModeTests.cs`、
  `tools/run_scene006_probe.py`、`tests/test_scene006_probe.py`、
  `docs/evidence/`（本文件与三份机器工件）、`runtime/p1-scene-006/`。
  既有文件只改两处：`TetheredTracking.EditModeTests.asmdef`（references
  增加对新 asmdef 的引用一行）与 `docs/current-status.md`（状态板）。
- `config/`、`Assets/TetheredTracking/Scripts/`、既有通用分析器与既有
  冻结工件零改动（`git diff` 可证）。
- 零 Play、零 scenario 创建、零 session/run ID、零配置字节写入。
  全部运行均为 Edit Mode 无头 Editor 执行与离线 Python。
- 未声称任何"新光学/新场景 T 目标完成"；60° 自检只是工具自检（§5.6
  批次归属行）。

## 2. 新增文件与职责

### 2.1 Unity 侧（`Assets/TetheredTracking/Editor/Scene006/`，新程序集
`TetheredTracking.Scene006.Editor`，仅 Editor 平台，引用
`TetheredTracking.Runtime`）

| 文件 | 职责 |
|---|---|
| `Scene006RouteGeometry.cs` | 闭路线周长/采样/点到路线距离/`s_init` 离轴 argmin；逐操作复现内部 `RateStudyScouting` 语义 |
| `Scene006Trace.cs` | §5.2.2 冻结 trace：`Configure` 等价初态 + `PlaceAtRouteDistance` 字面放置 + `Step` float32 复现（含 `<0.5f` 停顿与 `delta.y=0`）；541 状态；首圈测量；SHA-256 绑定 |
| `Scene006GimbalReplay.cs` | §5.2.4/5 云台语义：`LateUpdate` 逐式复现（45° 钳位、yaw 保持规则、`RotateTowards ≤ 24°/0.2 s`）；冻结初态 `Euler(90,0,0)` |
| `Scene006Visibility.cs` | §5.3 保真门：与 `CoverageEvaluator.EvaluateVisibility` 逐点等价的 15 采样谓词（分母恒 15、`≥0.2`、`RaycastAll(…, ~0, Ignore)` 距离 −0.05）、投影 truth box、type-7 分位 |
| `Scene006StationSet.cs` | §5.2.6/7 `p_hover`（AGL）与站点集合（4 m 格、7 个高度层、`r(h)`、并入 `p_hover` 去重、`(h,x,z)` 字典序） |
| `Scene006PathCertificate.cs` | §5.4 路径证书：直线段 + 梯形剖面时长、`δ=0.25` 含端点采样、机体球 1.625 m、系留胶囊 0.375 m（段–棱柱距离黄金分割精确解 + AABB 粗筛）、相切即违规 |
| `Scene006SceneRig.cs` | Edit Mode 场景准备：开城市场景、应用冻结 `scene_adjustments`、验证 road data、目标复制品（bootstrap 同款双立方体）、评估相机（FOV/aspect/近远平面与 runtime 一致）、遮挡代理 collider |
| `Scene006Evaluation.cs` | T1/T2/T3/T4/T6 编排与基线工件 schema |
| `Scene006AnchorPreflight.cs` | §5.5 T5：003 审计器 + §5.5 参数合同 + 新增路线–锚点 ≥1.5 m 子门 + `BLOCKED_ANCHOR_PLACEMENT_V2` 处分 |
| `Scene006ProbeRenderer.cs` | §5.6 T1′ 帧集合：106 个预注册 tick + T6 提示帧的 Edit Mode 离线渲染、truth sidecar、manifest |
| `Scene006EvidenceGenerator.cs` | `-executeMethod` 入口 `GenerateBaseline` / `RenderProbeFrames` |

关键约束：`Scripts/` 只读使新代码无法进入 `TetheredTracking.Runtime`，
而 EditMode 测试程序集只能引用命名程序集——故工具置于新 Editor
asmdef，测试 asmdef 增加一行引用（既有测试不受影响，162 项原测试
全部保持通过）。运行时 internal 谓词/放置/路线语义在新程序集内按
源代码逐操作复现，并由测试程序集（有 `InternalsVisibleTo`）与真实
组件/内部函数逐步对照验证。

### 2.2 Python 侧

- `tools/run_scene006_probe.py`：T1′ 探针分析器（§5.6 七步判定链：
  权重哈希 → `PROBE_INCOMPLETE` → `PROBE_FIDELITY_CONTRADICTION` →
  样本数 → recall 三段；工具态永不自动 `PASS`；嵌入/margin 只报告）。
- `tests/test_scene006_probe.py`：11 项合成探针目录测试（桩注入）。

## 3. 实际运行的命令与结果

### 3.1 Unity Edit Mode 测试（编译 + 187 项测试）

```bash
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  -batchmode -nographics -projectPath ~/TetheredDroneTracking \
  -runTests -testPlatform EditMode -testFilter TetheredTracking.Tests \
  -testResults runtime/test-results/p1-scene-006-editmode.xml \
  -logFile runtime/test-results/p1-scene-006-editmode.log
```

**187/187 通过**（162 项既有 + 25 项新增；Unity 6000.4.1f1）。新增测试
覆盖：冻结输入哈希绑定（scenario/road_data 与提案引用哈希一致）、
路线几何与内部 `RateStudyScouting` 逐项相等、trace 与真实
`LoopTargetVehicle` 逐步逐位相等（s_init = 0 与 123.4 两条、541 状态、
位置 0 漂移/旋转 0 漂移）、trace 哈希确定性与敏感性、首圈 538 ≤ 540
（提案记录的 538/539 交替得证）、云台逐式用例、15 采样构造与评估器
逐点相等、遮挡/视锥计数、投影与内部 `ProjectRenderers` 逐位相等、
type-7 手算值、站点集合构造与去重、梯形时长、证书机体/系留分类、
preflight 合同参数与三种处分（AVAILABLE / 路线子门 / V2）、合成场景
端到端门算术。

### 3.2 Python 测试

```bash
.venv-track/bin/python -m unittest tests.test_scene006_probe   # 11/11 OK
PYTHONPATH=. .venv-yoloe/bin/python tests/test_scene006_probe.py  # 11/11 OK
```

`.venv-yoloe` 下 `python -m unittest tests.test_scene006_probe` 的虚线
模块路径被 ultralytics 自带的 `site-packages/tests/` 包遮蔽（既有环境
问题，`tests.test_scene004_gate0_probe` 等同病）；`PYTHONPATH=.` 直跑
同等通过。探针模块在 `.venv-track`（无 torch）下可导入，真实模型仅
在判定链到达第 5 步时惰性构造。

### 3.3 现场景 T1–T5 基线（Edit Mode，零 Play）

```bash
…/Unity -batchmode -nographics -projectPath ~/TetheredDroneTracking \
  -executeMethod TetheredTracking.Scene006.Scene006EvidenceGenerator.GenerateBaseline \
  -quit -logFile runtime/test-results/p1-scene-006-baseline.log
```

工件：`docs/evidence/P1-SCENE-006-baseline.json`、
`docs/evidence/P1-SCENE-006-anchor-preflight.json`、
`runtime/p1-scene-006/trace-sinit0.json`（全 541 状态，SHA-256
`682dfad0…cca8`；首圈实测 538 步，未超 horizon）。

输入全部来自冻结字节：`config/scenario.default.json`（SHA-256
`f9c92052…e3`）、`config/road_data.json`（`111e0759…94`），`s_init=0`，
`p_hover=(132.0, 25.2, 117.0)`，60°/640×480，遮挡代理由
`EvaluationOcclusionGeometry` 同款网格 collider 提供（764 个障碍
棱柱参与 T4）。

| 门 | 结果 | 数值 |
|---|---|---|
| T1 | **FAIL** | 域 540/540（C_frustum=1.0）；min(w,h) p05 = **18.881 px** < 25；median 24.126、min 17.915、max 85.020；无保真矛盾 |
| T2 | **FAIL** | `L_point = 0.0000` < 0.10（与 SCOPE-002 的 0.0000 出视锥占比一致） |
| T3 | **FAIL** | `L_occ = 0.0630` ∈ [0.05, 0.40] 但 `1−C_geom = 0.0630` < 0.15；遮挡集中于 k≈209–242 共 34 个样本（斜距 25.005–73.462 m 全环） |
| T4 | **PASS** | `G_station = 0.0630` ≥ 0.05；最佳站点 (148, 20.2, 105) C=1.000；证书通过 726/1040（机体拒 122、系留拒 307、路径拒 0） |
| T5（现锚点复核） | **BASELINE_CLEAR** | 现锚点格 305/1257 合法，路线子门拒 222 |
| T6 | **PASS**（描述性） | `k* = 0`；提示帧 min(w,h) 35.45 ≥ 域中位 24.13 |

T4 属"意外通过"（§7.2 待检假设条款）：如实记录，归因交接受角色；
它是候选预筛而非 BC-M34-4(b) 见证，对现场景的 PASS 不构成任何候选
场景主张。T3 的 6.3% 遮挡同样是实测新信息（远端遮挡弧 k≈209–242）。

### 3.4 T5 候选格 preflight（零配置写入，同一批次内）

**`BLOCKED_ANCHOR_PLACEMENT_V2`：0/1257 合法。** 全部 1257 个候选支撑
通过（`Natures_Grass Tile`，实测支撑 y = 0.0000013 m——§3.4 的高程
重导按预期解除了 SCENE-003 的 `SUPPORT_HEIGHT_MISMATCH`），但全部
被 `Building_Stadium` 净空拒绝（`CLEARANCE_INTERSECTION`）；路线子门
0 拒绝。按 BC-SC6-2：记录 V2 并返回接受/构思角色，**本批次不请求
batch-2 用户 GO**；未扩大候选区、未移除体育场、未改安全参数。

### 3.5 T1′ 探针（60° 自检）

```bash
…/Unity -batchmode -projectPath ~/TetheredDroneTracking \
  -executeMethod TetheredTracking.Scene006.Scene006EvidenceGenerator.RenderProbeFrames \
  -quit -logFile runtime/test-results/p1-scene-006-probe-render.log
.venv-yoloe/bin/python -m tools.run_scene006_probe analyze \
  --probe-root runtime/p1-scene-006/probe-baseline-vfov60 \
  --output docs/evidence/P1-SCENE-006-probe-60deg.json
```

渲染：106 个预注册 tick（k=15,20,…,540）+ 提示帧 s_0（k\*=0，与
tick 集合构造性不相交），JPEG q85 640×480，truth sidecar 逐帧绑定
trace 哈希；manifest 冻结配对规则与权重绑定声明。

分析结果（工件 `docs/evidence/P1-SCENE-006-probe-60deg.json`）：
权重绑定全部通过（detector/DINOv2 源与权重/两个 NanoTrack ONNX）；
完整性零缺失；无保真矛盾；目标样本 99（106 tick 中 V=1 者）、干扰
样本 820，均 ≥ 40。**工具态 `FAIL`（`RECALL_BELOW_FAIL_MAX`）：
strict recall 16/99 = 0.161616 < 0.85**——命中集中在近端
（k=25–90 与 k=530–540 两个近锚点弧段），其余环段检测失效，与
SCENE-003 记录的远端 `0/45` 结构性全盲一致。嵌入只报告：target
cosine 中位 0.4149，max-distractor 中位 0.4797，margin 中位
−0.0498，双门（0.5/0.1）通过占比 0.1818。该 FAIL 是**现场景（已知
探测失效场景）上的工具自检结果**——证明探针链路端到端工作且如实报
告失败；它不是任何候选光学下的 T1′ 结论，最终门态永远归接受角色。

## 4. 实现语义解释记录（交复核核对，非门变更）

1. **d_trim 的实现形态**：§5.4.4 的"头段照常查询、只忽略唯一实测支撑
   实例"由 §5.5 排除集结构性实现——道路面与支撑允许清单实例本就不在
   障碍集合内，头段对其余实例照常失败；1.70 m 修剪界与
   `1.70×sin(13.212980°)=0.388571≥0.375` 记入 T4 工件。否则每个合法
   锚点的系留胶囊都会与自身支撑面碰撞，证书恒失败。
2. **`p_hover` 的零长路径证书**：站点集合并入 `p_hover`（§5.2.7），其
   "路径"长度为 0；实现按同一构造取 N=0 的退化情形——单样本即悬停
   构型本身（机体球 + 垂直系留照常判定），不作为路径拒绝。若按字面
   长度 ≤ ε 判拒，则 `C_hold` 自身被排除出 `max_p`，与 §5.2.7 并入
   语义矛盾。
3. **支撑 y 的请求值**：候选合同以 y=0.0 请求（±0.05 容差），权威值
   为审计实测并逐候选记录的 `support_surface_y_m`；T4/T6 的 AGL 公式
   使用实测支撑 y。现锚点复核沿用其配置 y=0.2（路面支撑）。
4. **缺 sidecar 的 fail-closed 解释**（python 探针）：truth sidecar 缺
   失的 tick 无法自证 V=0，按 `PROBE_INCOMPLETE` 处理（渲染器对每个
   预注册 tick 恒写 sidecar，缺失即工具链故障）。
5. **`s_init` argmin 的解析实现**：逐段取垂足（含端点）的解析扫描，
   平局取较小 s；现场景基线按 §5.2.2 固定 `s_init=0`，该函数仅供
   候选侧与测试。

## 5. 未验证项与已知限制

- T1′ 的候选光学（30°）执行属 batch 2，本批次未做也不得声称；
  60° 自检不证明任何新光学有效性。
- 探针 recall 是 oracle 指向的可探测上界
  （`ORACLE_POINTED_DETECTABILITY_UPPER_BOUND`），非闭环 recall。
- Edit Mode 的 `Camera.Render()` 与运行时 Play 采集路径
  （`SensorFrameWriter`）不是同一渲染栈；两者投影几何一致（相同
  intrinsics 与位姿语义），但帧级像素差异未做逐字节对照（本批次无
  Play 可比对象）。
- T4 站点 C 值与证书在 Edit Mode 离线谓词上测得；`K_acq=10` 仍为
  预注册工程窗口，非结构必达证明（R21）。
- 滚动 horizon 540 步对 `s_init=0` 实测首圈 538 覆盖之；其他 `s_init`
  未测（batch 2 候选侧事情）。

## 6. 复核范围（精确文件清单）

新增：
- `Assets/TetheredTracking/Editor/Scene006/`（asmdef + 10 个 .cs）
- `Assets/TetheredTracking/Tests/EditMode/Scene006EditModeTests.cs`
- `tools/run_scene006_probe.py`
- `tests/test_scene006_probe.py`
- `docs/evidence/P1-SCENE-006-batch1.md`（本文件）、
  `P1-SCENE-006-baseline.json`、`P1-SCENE-006-anchor-preflight.json`、
  `P1-SCENE-006-probe-60deg.json`

改动（各一行级）：`Assets/TetheredTracking/Tests/EditMode/TetheredTracking.EditModeTests.asmdef`
（references +1）、`docs/current-status.md`（状态板）。

重点复核项：§5.2/§5.3/§5.4/§5.5/§5.6 各冻结语义与上述第 2 节复现
点的逐行一致性；第 4 节五条解释记录；T4 意外通过与 T3 遮挡实测的
归因工作（交接受角色）。

## 7. Unity 用例

batch 1 全部为 Edit Mode 离线工具，零 Play、零采集：无用户 Unity
运行用例。复核/接受如需复现，直接重跑 §3.1/§3.3/§3.5 的无头命令
即可（全程无头、零写入 config/ 与场景文件）。
