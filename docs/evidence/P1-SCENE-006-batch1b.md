# P1-SCENE-006 amendment 1 batch 1b — 实现者证据

Work ID: `P1-SCENE-006`（amendment 1 revision 5，batch 1b；batch 1c 未开工）
日期: 2026-08-03
角色: 实现（implementation）
依据: `docs/proposals/P1-SCENE-006-post-v2-anchor-route-amendment.md`
revision 5（Acceptance round 6 `ACCEPTED`，BC-AM1-1–6；正式设计 v0.3.13；
用户逐字授权 §8 a+b+c+d+f、e=A+B 双筛）

## 1. 停点身份（§5.6 四层拓扑的 ①②）

**返工轮次说明**：首个 `C_1b`（`f6a41e3`）经 Acceptance 停点审计 round 1
（提案 §23）判 `STOP_NOT_CONFIRMED / REWORK_REQUIRED`——阻断项 B1B-R1：
8 份 trace 工件缺 §5.6 的逐工件双字段身份。本轮按 §23 逐字返工条件执行：
trace schema 加入与其他候选工件同口径的 `capture` 身份并让跨进程
checker/测试对全部 13 份工件强制核对；工具变更形成新 tool commit 后
**完整重跑** batch 1b（路线审计、P1、P2、8 份 trace 全部重新生成，无手工
补 JSON、无沿用旧门值）。两轮门值完全一致（身份级修复不触碰门语义）。

- **tool commit `C_tool` = `fe37ad207bcc0e7030d0be9415248af97e0e8896`**
  （B1B-R1 修复：trace schema `capture` 身份 + 写入 fail-closed +
  checker 强制；其引入 diff 只触及冻结工具/测试路径，不含任何工件）。
  其前序工具链 `3ac640a → 6e9fc64 → d11cae5`（候选模式工具）与返工提交
  `fe37ad2` 均在复核 diff `345b3ea..C_1b` 内。
- **冻结工具路径集**（首次采集前列全；此后新增/删除/漏列即工具变化）：
  `Assets/TetheredTracking/Editor/Scene006/**`、
  `Assets/TetheredTracking/Tests/EditMode/**`、
  `tools/run_scene006_probe.py`、`tools/scene006_trace_hash.py`、
  `tools/scene006_candidate_check.py`、`tests/test_scene006_probe.py`、
  `tests/test_scene006_trace_hash.py`、`tests/test_scene006_candidate_check.py`、
  `tests/fixtures/scene006-trace-v2-sample.json`。
- **采集身份**：全部 13 份工件（路线审计、P1×2、P2×2、trace×8）在同一
  clean HEAD 上采集，`capture_commit = tool_commit = fe37ad2`，采集前
  `git status --porcelain` 为空（**逐工件记录**，含 8 份 trace），二者
  相等故无零 diff 证明义务。场景零写入证明：每份工件记录场景 `.unity`
  文件采集前后 SHA-256（相等）与 `scene_saved = false`。
- **evidence/stop commit `C_1b`**：本文件与全部工件所在的提交（hash 见
  状态板与 git log）。独立复核 diff 端点 = **`345b3ea..C_1b`**。

## 2. 范围与边界符合性（BC-AM1-1–6）

- 只执行 §8 a+b+c+d+f、e=A+B：族 A 格心 `(150,108)`、族 B 格心
  `(195,30)`、族 B 路线为冻结路线的 `(+60,-60)` 纯平移、五行车辆按
  §3.3.2 逐行临时侧移。无近似坐标、无替代路线、无配置/场景字节、
  零 Play、零 capture、零 scenario/session/run ID；batch 2 未触及。
- 双筛两族均完整跑完 P1+P2，不设优先级、未提前停止；§5.4 决赛集
  裁决（P3）未执行——属 batch 1c。
- 写入路径严格限于 §7.2：`Assets/TetheredTracking/Editor/Scene006/`、
  `Assets/TetheredTracking/Tests/EditMode/`、SCENE-006 专用
  `tools/scene006_*.py` 与 `tests/test_scene006_*.py`(+fixture)、
  `docs/evidence/`。`config/`、运行时 `Scripts/`、既有通用分析器与
  既有冻结工件零改动（`345b3ea..C_1b` diff 可证）。
- 采集命令（单次 headless Edit Mode）：

```bash
…/Unity -batchmode -nographics -projectPath ~/TetheredDroneTracking \
  -executeMethod TetheredTracking.Scene006.Scene006CandidateGenerator.RunBatch1b \
  -quit -logFile runtime/test-results/p1-scene-006-batch1b.log
```

## 3. F1 / F2 / F4 前置修正（复核 round-1 未闭义务）

- **F1（trace_sha256 可外部复算）**：新 `p1-scene-006-trace/v2` schema
  在每个状态旁发布 float32 位模式（`*_bits` 8 位 hex 字符串），哈希
  算法不变（int32-LE k + 7 个 float32-LE 位模式）。跨进程重算器
  `tools/scene006_trace_hash.py` 与 C# `RecomputeSha256` 互为独立实现；
  `tests/fixtures/scene006-trace-v2-sample.json`（Python 独立构造，
  含负零位模式 `80000000`）把两种实现钉在同一字节序列上。本批 8 份
  候选 trace 工件全部通过重算（见 §7）。batch-1 的 v1 trace 工件保持
  冻结不改。
- **F2（§5.4.4 字面头段修剪）**：`Scene006PathCertificate.Evaluate`
  改为字面语义——系留胶囊头段 `[0, 1.70 m]` 查询全部障碍、只忽略
  绑定的唯一实测支撑实例（按实例名绑定，与 T5 `support_ids` 一致），
  余段不忽略任何实例；命名不存在的绑定实例直接抛错（fail closed）。
  配套 `Scene006SceneRig.BuildAllInstancePrisms` 产出含道路面与支撑
  允许清单的全实例棱柱集（道路面棱柱取自 road_data surfaces，厚度取
  与冻结地面 0.2000004 一致的 0.2 m 板厚）。batch-1 基线路径（T5 障碍
  集 + null 绑定）行为不变；batch-1 T4 数值保持历史、不重跑。族 B 的
  24 个近道路面候选（最近 1.00 m）在 P3 证书中将按字面算法失败——
  这正是 F2 承重的语义差。
- **F4（空串规范化）**：`CandidateRecord` 新增序列化前计算的 `legal`
  布尔；`""` 明确定义为 `rejection_reason` / `blocking_object` /
  `scene003_rejection_reason` 的无值约定（preflight schema 升 v2；
  batch-1 的 v1 工件冻结不重生成）。消费方校验器
  `tools/scene006_candidate_check.py` 对每份 P1 工件逐候选核对
  `legal == (rejection_reason == "")` 并对账全部计数。

## 4. 族 B：§3.3.2 重算比对 + 落点审计 + 路线合法性（工件
`P1-SCENE-006-familyb-route-audit.json`，status `CLEAR`）

- **重算全部逐字命中**：5/5 行的最近段索引、方向、位移与新位置与
  §3.3.2 冻结表完全一致（容差 5e-4；现净空列复核
  `0.0000/0.0000/1.2056/0.0000/0.0000`，对表 `0.00/0.00/1.21/0.00/0.00`）。
  障碍实例计数 764（= §9 口径 764 个有厚度障碍），与 §9.11 的
  "763 = 764 − self" 一致。
- **落点审计全过**：五辆落点 footprint 0.25 m 网格全覆盖于路面矩形
  并集（§2.2b 复核），与全部地面障碍及已落位车辆零重叠（§2.2a 以
  停放车辆本身为审计对象）。
- **SCENE-002 权威路线审计对平移路线 CLEAR**：道路违规 0、三维扫掠
  障碍违规 0（审计障碍 779）、车辆走廊违规 0（审计车辆 101）。
- 实现过程记录：首次采集因两个工具缺陷触发
  `RELOCATION_RECOMPUTE_MISMATCH`（工件丢行与质心/根位置混淆），均
  为工具侧缺陷而非规则与冻结表的分歧；修正后重采，全部命中。该
  终态未成为本批结论。

## 5. P1 — 逐 `(anchor, altitude)` T5（工件 `…-p1-familyA.json` /
`…-p1-familyB.json`）

对两族格心的完整 1257 候选格在 `{16,20,24,28,32} m` 五高度各跑一次
冻结 T5（`Scene006AnchorPreflight` 候选模式，逐高度合同）：

| 族 | 五高度 legal | 结论 | 合格网格对 |
|---|---|---|---|
| A `(150,108)` | 86/1257（五高度相同） | `P1_OK` | 2 锚点 × 5 高度 = **10** |
| B `(195,30)` | 158/1257（五高度相同） | `P1_OK` | 6 锚点 × 5 高度 = **30** |

与提案 §3.2/§3.3 的离线诊断（86 / 158、五高度不变）逐项一致；§5.3
预注册的 8 个筛查锚点全部落在合格对内（无 `BLOCKED_*` 终态）。逐高度、
逐候选状态与支撑 y（草地实测 `1.3113418617649586e-06` 同源）在工件内。

## 6. P2 — 预注册网格 T1/T2/T3（工件 `…-p2-familyA.json` /
`…-p2-familyB.json`，逐锚 v2 trace 工件 8 份）

- **`s_init`（权威工具值）**：A 两锚点 `22.5000` / `24.5000`，B 六锚点
  `176.2279` / `184.2279` / `186.2279`——与提案 §3.2/§3.3 的诊断值
  一致。高度无关性逐锚显式核验（五高度 argmin 全同，fail-closed 检查）。
- **首圈步数（权威工具值）**：8 个锚点全部 **538 ≤ 540**，无
  `HORIZON_SHORT`。提案离线诊断（A 482/477、B 497/477/472）与工具值
  不一致，按 §10 几何预筛类规则**以工具为准**，差异交接受角色归因；
  不影响任何门（两口径都在 horizon 内）。
- **族 A：0/50 格入带 → `BLOCKED_GEOMETRY_INFEASIBLE`。** 全部 50 格
  实测 `L_occ ∈ [0.0000, 0.0278]`（远低于 T3 下限 0.05）——提案 §3.5
  的风险画像成立：体育场 AABB 上界（~0.14–0.47）极松，真实射线遮挡
  几乎为零；逐 tick 遮挡归因见工件（仅零星 tick，阻塞体为体育场/冷杉）。
- **族 B：`P2_OK`，3/150 格入带**（无逐格终态、无保真矛盾）：

  | anchor | h | vfov | T1 p05 (px) | L_point | L_occ | total |
  |---|---|---|---|---|---|---|
  | `(195,30)` | 20 | 40 | 37.061 | 0.3389 | 0.0574 | 0.3963 |
  | `(197,30)` | 16 | 35 | 30.290 | 0.5000 | 0.0537 | 0.5537 |
  | `(197,30)` | 16 | 40 | 35.143 | 0.4407 | 0.0648 | 0.5056 |

  逐格未舍入值、T1 域 `min(w,h)` 全样本与逐 tick 遮挡归因（阻塞体以
  `Building_Factory` / `Natures_Big Tree` 为主）均在工件内；§5.4 决赛
  集裁决（冻结评分、tie-break）与 P3 全审计属 batch 1c，本批未执行。
- 族 A 的意外通过如实记录：部分格 T2/T1 落带（如 h=20 vfov=30
  `L_point=0.4778`），无一格 T3 入带；不反推调参。

## 7. 实际运行的命令与结果

- Unity EditMode：`…/Unity -batchmode -nographics -runTests
  -testPlatform EditMode -testFilter TetheredTracking.Tests`
  **206/206 通过**（187 既有 + 19 新增；新增覆盖 F1 位模式复算与
  跨进程 fixture、F2 字面修剪三态、F4 对账、求解器方向/并列/无解/
  根位置、候选格算术与遮挡归因、平移路线逐字比对、trace 身份
  fail-closed 与序列化往返）。
  `runtime/test-results/p1-scene-006-editmode-b1b.xml`。
- Python：`.venv-track/bin/python -m unittest discover -s tests`
  **315 项，1 失败为既有 F3**（`test_check_docs` 基底破损，复核已归因
  给协调批次 `902a72c`，非本批引入）；`test_scene006_trace_hash` 5/5、
  `test_scene006_candidate_check` 12/12（含真实工件校验与 trace 身份
  强制）。
- 工件校验：`tools/scene006_candidate_check.py check` 对全部 13 份
  工件通过（F4 对账、计数、门重算、p05/median 由域样本独立重算、
  网格对与 P1/P2 一致性、**全部 13 份的 §5.6 身份字段**）；8 份 trace
  工件经 `tools/scene006_trace_hash.py` 跨进程重算全部匹配。
- 环境事故记录：当日报编译失败是 Unity 许可层问题（过期
  licensing client 占用 mutex 拒 1.18.1 握手 → 内建模块 entitlements
  全部 unknown → IMGUI 模块未引用），与本批代码无关；清理过期客户端
  进程后恢复。该事件不触碰任何门值。

## 8. 实现语义解释记录（交复核核对，非门变更）

1. **落点重算的 (c) 障碍集**：764 个有厚度障碍中仅排除自身，其余 4
   辆目标车辆按原始位置计入（§9.11 的 "763 = 764 − self"）；(d) 另查
   已按应用顺序落位车辆的新位置。
2. **footprint 全部取 ground XZ 范围**（road_data ground bounds），
   厚度过滤用 full 高度；车辆偏航经 TRS 变换。
3. **路线距离按 §9.11 字面**：0.25 m 采样路线折线求点–footprint
   距离；最近段以 footprint 质心判定、并列取最小索引；左法向
   `(-dir.z, dir.x)`（已逐行对表验证）。
4. **道路面棱柱板厚 0.2 m**（F2 全实例集）：road_data surfaces 无厚度
   字段，取与冻结 `ground_plane_y_m=0.2000004` 一致的板厚；只影响
   P3 证书，batch 1b 不消费。
5. **P2 逐 tick 归因的阻塞体取射线命中物的场景根名**（遮挡代理
   collider 的父链顶端），与 §5.3 要求的逐 tick 遮挡归因一致；可见性
   谓词与 batch-1 基线逐点等价（同一 `OccludingRoots` 射线，测试钉死）。
6. **s_init 高度无关由检查保证而非假设**：五高度 argmin 不一致即
   fail closed（未触发）。

## 9. 未验证项与已知限制

- P3（决赛集裁决、T4 字面证书、T6、T5 复核性重跑）未执行，属
  batch 1c；本批任何数字都不是决赛点结论。
- 族 B 候选光学的 T1′ 属 batch 2（`BLOCKED_USER_GO`）。
- trace 首圈 538 与提案离线诊断（472–497）的差异已由 Acceptance 在
  提案 §23 归因：离线诊断停在"实际回到 s_0"之前的口径，不是门变更；
  族 A `L_occ` 实测与 AABB 上界差异与 §3.5 既有校准（体育场 ~6.9× 松）
  一致。
- 族 A 的 `BLOCKED_GEOMETRY_INFEASIBLE` 按 §5.3 预注册属回构思终态；
  本批未改网格/阈值/场景内容，交接受角色按 §5.4/§5.5 处分（族 B 已
  产出 3 个入带格，联合 `F` 非空）。
- Edit Mode `Camera.Render()` 未在本批使用（P2 为投影+射线，无渲染）。

## 10. 复核范围（精确文件清单）

工具（`C_tool` 全量，diff `345b3ea..C_1b`）：
- `Assets/TetheredTracking/Editor/Scene006/`：新增
  `Scene006CandidateContract.cs`、`Scene006RelocationSolver.cs`、
  `Scene006CandidateEvaluation.cs`、`Scene006CandidateGenerator.cs`、
  `Scene006TraceArtifact.cs`；修改 `Scene006PathCertificate.cs`（F2）、
  `Scene006AnchorPreflight.cs`（F4）、`Scene006Evaluation.cs`（F2 接口）、
  `Scene006SceneRig.cs`（全实例棱柱）、`Scene006Visibility.cs`（归因）、
  `Scene006EvidenceGenerator.cs`（F2 接口）。
- `Assets/TetheredTracking/Tests/EditMode/`：新增
  `Scene006CandidateEditModeTests.cs`；修改 `Scene006EditModeTests.cs`
  （F2 签名适配）。
- `tools/scene006_trace_hash.py`、`tools/scene006_candidate_check.py`、
  `tests/test_scene006_trace_hash.py`、
  `tests/test_scene006_candidate_check.py`、
  `tests/fixtures/scene006-trace-v2-sample.json`。

工件（`C_1b`）：本文件 +
`P1-SCENE-006-familyb-route-audit.json`、
`P1-SCENE-006-p1-family{A,B}.json`、`P1-SCENE-006-p2-family{A,B}.json`、
`P1-SCENE-006-trace-{A,B}-*.json`（8 份，其中 B 族同 `s_init` 四锚点
的 trace 内容相同、哈希相同，属预期）。

重点复核项：F2 字面修剪的三处语义（只豁免绑定实例、余段不豁免、
命名缺席 fail-closed）；§3.3.2 重算与冻结表的逐行一致性；P1/P2 门
算术与 batch-1 基线的等价性；§5.6 双字段与零写入证明；§6 的 3 个
入带格逐格重算。

## 11. Unity 用例

batch 1b 全部为 Edit Mode 离线执行，零 Play、零采集：无用户 Unity
运行用例。复核/接受如需复现，重跑 §2 的采集命令与 §7 的测试/校验
命令即可（全程无头、零写入 `config/` 与场景文件）。
