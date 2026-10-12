# P1-VLM-CAL-001 — 经验校准实验包：先测量、后定合同

Status: REVISION_REQUESTED
Author/role: 构思角色（ideation，Fable 池）
Created: 2026-08-06
Last updated: 2026-08-06
Revision: 3（回应 Acceptance round 3 的 6 条必修项，逐条回应见 §14；
round 1/2 的回应保留在 §10/§12，不重写）

**授权状态（逐字核对 `docs/authorizations.md` 2026-08-06 当日条目）**：
用户指示"先把试验田暂停一下，重新写一个要做的实验提案推荐交给codex
审核达成一致"。`P1-VLM-SCOPE-001` 修订轨道已转
`PAUSED_PENDING_CALIBRATION`。**本提案不携带任何执行授权**：每个实验
的执行各待其门（接受裁定 / 停点 + 独立复核 / COORD-005 人眼保真检查
与诊断安排 / Q1 API 预算）。

---

## 0. 修订索引与 revision 0 的实测勘误

### Round 1 必修项 → 本稿落点

| # | 必修项 | 落点 | 实质变化 |
|---|---|---|---|
| 1 | 零执行输入资格门 | §3.0、§4.1 | 新增 `p1-vlm-cal-manifest/v1`（沿用 `p1-scene-006-probe-manifest/v1` 的既有形态）：来源目录、frame ID 集合、逐文件 SHA-256、truth join、模型 SHA-256 全部在任何调参/benchmark/实现前冻结；缺件/样本不足给具名终态；重冻结只允许在**首次揭盲之前**整体进行且旧清单留档 |
| 2 | E1 逐色可判定合同 | §3.1 | **颜色集由红/白/黄改为红/黄/紫**（实测：无白色带真值实例）；标签权威改为本提案冻结的 prefab→颜色映射表（真值 schema 无任何颜色字段）；冻结 OpenCV HSV 定义、红色回绕双区间、逐色 `s_min/v_min`、形态学/连通域/tie/无候选规则；90% 改为**逐色**门；真值不可用/目标不可见/同色多车各有唯一处置 |
| 3 | E2 唯一真实路径 | §3.2 | 逐字锁定 `_catch_up` 的**无迭代上限**循环、`replay_tracker` 的十个终态、factory 先于 box 校验、缺模型伪装成 `intermediate_frame_missing`；两级 harness 二选一并**预注册 Level A**；帧数档取代秒数档（capture_hz 依赖）；60 个预注册起点、冷/热、失败不得出分母、type-7 实现冻结 |
| 4 | E3 故障模型与结果空间 | §3.3 | 拆 M1（子进程 SIGKILL，OS 存活）与 M2（掉电/内核崩溃，**本轮不测**，结论同步收窄）；测真实 Python 路径 + C# 静态审计 + 明标"转写模型"；七类结果空间；父子握手的五个 kill 边界；fsync 是否构成规范保证由合同明示 |
| 5 | E5 冻结 | §3.4 | **重大修正**：项目无任何 `Instantiate`，遮挡车只能**重定位既有城市车辆**且是**静止**的，原稿"大车与目标交汇"不可实现；改为静止公交遮挡 + 三档退距；给出全部几何/trial/时窗/身份/判据数值；真值归因改**离线 join**；零 `config/` 与 `Assets/` 字节，只写 gitignored 的 `runtime/scenario_config.json` 覆盖并前后哈希取证 |
| 6 | E4 与批次门 | §3.5、§4.2 | V1 协议全文复制入 §3.5 并绑定行范围+块 SHA-256+文件 SHA-256，写明冲突优先级；**E4b 删除**；执行序改为"工具+清单稳定候选 → 停点与写入归因 → 独立复核 → 才运行"；E5 另成候选并先复核 + COORD-005 人眼保真检查；**撤回轻量复核减免请求**；"受影响接口零"改为如实声明 |

### Round 3 必修项 → 本稿落点

| # | 必修项 | 落点 | 实质变化 |
|---|---|---|---|
| 1 | 收口 E1/manifest 字面合同 | §3.0 规则 6、§E1.b″、§E1.c | 路径规范统一为 repo-relative/POSIX（删去"绝对路径"要求，只保留一条非规范化的 `repo_root_abs` 出处记录）；RED 判定改用真实字段 `target_box_status`（probe `OK` / scouting v2 `VALID`），`box_status` 仅属 distractor 条目；probe 真值树新增 `frame_*.json` 白名单（排除 `prompt_*.json` 预热文档） |
| 2 | 修正并完全冻结 E2 | §3.2.c、§3.2.d | 注入键改真实的 `maximum_result_age_s`（`maximum_source_age_s` 只是 `replay_tracker` 的形参名）；冻结唯一 `source_box_norm` 字面量与其出处；给出 `p95_fixed_ms`/`p95_per_frame_ms` 的完整闭式估计式与 `E2_LINEAR_MODEL_REJECTED`；握手轮数 ≠ 2 改为**整实验具名硬停** `E2_HANDSHAKE_INVARIANT_VIOLATED`；新增 `worker_timeout_s = 10.0` 的生产可达性披露 |
| 3 | 按真实控制流重写 E3 表 | §E3.b、§E3.c | 废除 B0–B4 统一模板，改为**逐对象按语句序列命名的真实边界**；`create_once_bytes` 的 overwrite 初态改为**两条 preflight 终态断言**（零注入）；补上被 revision 2 漏掉的 `rate2_protocol.atomic_bytes`（replace 族、二进制、隐藏 temp）；`run_log._atomic_json` 明列为"审计不注入"并给理由；总次数由 660/680 重算为 **540** |
| 4 | 为 E5 选定真正可达的采集路径 | §E5.1 | 逐条给出两条采集路径的完整身份：**路径 Z（默认，零 ID、零 truth）**——不放 scouting session 文件，`ConfigureScouting()` 在早退分支返回，`scoutingTruthWriter == null`，全部 oracle 改为"冻结几何 + 帧元数据 + controller 观测"的离线投影；**路径 S（新 session/profile/ID）**——逐项列出所需协议变更并**交回接受角色**，本稿不预设已授权 |
| 5 | 修正 E5 刺激、truth 边界和时间门 | §E5.3、§E5.4 | 红色副本由 `(140.0, 0.2, 123.0)` 改为 **`(140.0, 0.2, 125.0)`**，用 `TargetVisualFactory` 的完整并集 AABB 与 route sweep 证明最小间距 `2.0000 m ≥ 1.5 m`；tracker 初始框改为 **manifest 冻结字面量 + 人眼确认**，运行时与离线两侧都不读 truth；停车判据改为 **LOS 地面点位移**（图像域在跟踪云台下近乎失效），`W = 2.0 s`、`d_thr = 1.0 m`、停车时长 `20.0 s`、检出上限 `4.0 s`，数学上可达 |
| 6 | 先把 E5-B 技术分支写到可决策 | §E5.0′、§E5.2′ | 先更正 §E5.0 的**量纲错误**（把近边退距与中心退距对比，结论本会反转），改用三条正确判据（近边窗口 + 遮挡体放得下 + 在画面内）重算。**分支 W 用穷举否掉**：满足 SCENE-004 已接受包络合同的 209 个格点锚点，可行弧长占比**全为 `0.0000`**；**分支 M** 可行占比 `0.4484` 但**不饱和占比 `0.0000`**。构思角色据此**撤回 E5-B 作为 Play 实验**，改交 §E5.2′ 的三个可选处置 |

### Revision 0 的四处实测勘误（本轮取证推翻，逐条如实登记）

| # | revision 0 的写法 | 实测事实 | 后果 |
|---|---|---|---|
| **C1** | E1/E4 对真值框评分读 `evaluation_truth.jsonl` | 该文件**全仓库零实例**（`find . -name evaluation_truth.jsonl` = 0）。它只存在于代码：`CoverageEvaluator.cs:39-40` 常量、`:409/:450-456` 写入，仅 rate3 study 路径产出，而该路径从未完成正式采集 | E1 改用实际存在的三种 scouting/probe 真值 schema（§3.1）；**E4/V1 同样受此阻断**，见 §3.5 勘误 |
| **C2** | E1 冻结"红/白/黄三色各一带" | 带真值框的具名对象只有三类：目标 **红**、`Vehicle_Taxi` **黄**、`Vehicle_SUV_color01` **紫**。**无任何白色具名实例**；且三个真值 schema 全都**没有颜色字段**（`grep -rl '"color'` 于三个真值树 = 0） | 颜色集改红/黄/紫；标签权威改为 §3.1 表的冻结映射，不来自真值 |
| **C3** | E1 用"按来源 run 的组隔离"取两组各 30 帧 | `scout-3` 与 `scout-4` 是**同一条轨迹**：2405 个共有 frame_id 上相机位置距离**恰为 0.000000 m**，目标框最大分量差 0.00119（≈0.76 px） | 两者不能充当互相隔离的两组；隔离轴改为跨 scenario + 同族分段，并如实披露同族隔离偏弱（§3.1） |
| **C4** | E5"放置一辆大型车辆与目标按 3 种相对速度/间距交汇" | 全项目 `Instantiate` **零命中**；`SceneVehicleAdjustmentApplier` 只能 `SetActive(false)` 或 `position = destination`（`SceneVehicleAdjustments.cs:77/:85`），既不能生成车辆也不能驱动其运动 | 遮挡体改为**静止的既有公交**，实验轴由"相对速度"改为"退距 × 通过段"（§3.4） |

---

## 1. 问题和研究价值

### 1.1 病根：在没有数据的地方冻结参数

`P1-VLM-SCOPE-001` 四轮裁定反复出现同一模式——纸面合同与现实冲突，
且每次都靠接受角色恰好核对真实代码/数据才被抓住：

| 轮次 | 冲突 | 根因 |
|---|---|---|
| round 2 | 10 s VLM 响应窗 vs DETECT `2.0 s` 年龄门互斥 | 无人实测过教师 API 延迟（唯一真实数据点是用户自有的 Gemini Flash 实验） |
| round 4 | `catchup` 用 TRACK-002 update-only 常量 ×4 推导 | 无人实测过真实 `replay_tracker()` 路径耗时 |
| round 4 | "运行日志见证与生效原子"论证被逐行否定 | 纸面推理代码行为，未做崩溃注入 |
| **本轮 §0** | revision 0 自身的四处 C1–C4 | 本提案第一稿同样在没查磁盘/没读代码的地方写了参数 |

用户 2026-08-06 判断（账本逐字）："不然两个模型达成统一了实验照样会
出问题"。§0 的 C1–C4 是该判断在本提案自身上的第一次兑现——**先测量的
提案自己也必须先测量**。本项目的 F23 教训（协议全对、测的是灰色替身）
是同一病的先例。

### 1.2 本提案的产出与地位

本提案**不产生研究主张**。产出是一组**预注册校准测量**，其数据通过
amendment 进入 `P1-VLM-SCOPE-001` 的合同参数，使 recharter 的收敛基于
测量而非两个模型的互相说服。先例：`P1-SCENE-004` Gate 0 只读探针、
`P1-SCENE-005` `A0.1` 诊断先行、COORD-005 诊断通道。

失败也是有效产出：某实验证伪其对应假设，意味着对应合同结构必须改——
**在写实现代码之前发现**，正是本提案的全部价值。

---

## 2. 输入、输出与受影响接口

- **输入（只读）**：`runtime/**` 归档（§3.0 表逐目录冻结）、
  `runtime/models/nanotrack-v2`、`config/**`、controller 与 Assets 代码
  （import/静态读取，不修改）；scouting/probe 真值仅供**离线** scorer。
- **输出**：`runtime/p1-vlm-cal/E*/`（manifest、原始测量 jsonl、汇总
  json）+ `docs/evidence/P1-VLM-CAL-001-{e1,e2,e3,e5}.md`。产物地位 =
  **工程校准数据**：可被 recharter amendment 引用为参数依据，不进研究
  证据链，不支撑任何研究主张。
- **受影响接口（round 1 必修 6：撤回"零"的说法，如实声明）**：
  - 运行时协议/指标/控制路径：**零改动**；
  - **新增**独立校准工具 `tools/vlm_calibration/`（E1–E3，纯离线，
    不被运行时 import）；
  - **新增**一个 Editor 侧诊断脚本、一个静态物离线投影器与一个
    E5-A 离线 scorer（§4.2 清单第 6/7/8 项）——这是
    新工具，因此 E5 自成稳定候选并受完整独立复核 + COORD-005 人眼保真
    检查约束（§4.2）；
  - E5 运行期写入 gitignored 的 `runtime/scenario_config.json` 覆盖
    （既有的、CLAUDE.md 明文允许的运行时覆盖机制），**`config/` 与
    `Assets/` 零字节**，前后哈希取证（§3.4）。

---

## 3. 实验清单

### 3.0 输入资格门（round 1 必修 1；先于一切调参、benchmark 与实现）

**冻结机制**：新增 `config/p1-vlm-cal-manifest.json`，schema
`p1-vlm-cal-manifest/v1`，形态逐字沿用仓库既有先例
（`tools/run_scene006_probe.py:441-528` 的 `_validate_manifest`）：
`schema_version` / `work_id` 严格相等校验、预注册计数相等校验、
40-hex `tool_commit`、冻结路径集、结果工件按 `manifest_sha256` 反向
绑定。任一不符即在**任何测量之前**抛错。

**必须入 manifest 的字段**：每个来源目录的**仓库相对路径**与其
`frame_id` 集合、逐文件 SHA-256（图像 + 元数据 + 真值三类）、真值
schema 名与 join 规则、模型/spec 四个 SHA-256（§3.2）、Python 与 cv2
版本、`git rev-parse HEAD` 与 `git status --porcelain`。

**round 3 必修 1 的字面更正**：revision 2 在此处写"绝对路径"，与规则 6
的"repo-relative、POSIX 分隔符"直接矛盾。**以规则 6 为准，本行改为
仓库相对路径**；绝对路径只以**单个**非参与哈希的溯源字段
`repo_root_abs` 记录一次（它逐机器不同，任何进入 `manifest_sha256`
的绝对路径都会让同一份清单在两台机器上算出不同哈希）。规则 6 的
canonical JSON 口径不变。

**真值目录的文件白名单（round 3 必修 1）**：`p1-scene-006/probe-*/truth/`
下除 106 个 `frame_%06d.json` 外还有 1 个 `prompt_%06d.json` 预热文档
（`probe-baseline-vfov60` 为 `prompt_000000.json`，`probe-candidate-vfov40`
为 `prompt_000002.json`；两者都带 `target_box_status`，直接 glob `*.json`
会把它误计入分母，使 106/99 变成 107/100）。故 manifest 构建器**只收
`frame_*.json`**，并把被排除的文件名逐条记入清单；`frames/` 侧同理为
107 个 jpg = 106 帧 + 1 张 prompt 帧。

**本轮构思角色的非权威预扫（供接受角色核实规模，实现时须重新机械
生成）**——磁盘实测，每行都由本会话直接复算：

| 来源目录 | 帧数 | 最长连续 | 帧 schema / 时钟 | scenario | 真值 |
|---|---|---|---|---|---|
| `runtime/frames` | 4096 | 4096 | v3 / `system-stopwatch/v1` | `p1-scene-004` | 无 |
| `…/p1-detect-001-qual-2-protocol-invalid-exchange/frames` | 3668 | 3668 | **v3 / `system-stopwatch/v1`** | `p1-scene-004` | 无 |
| `…/rate-study/P1-M2-RATE-003-CLOCKSMOKE/smoke-…/frames` | 2888 | 2888 | v3 / `system-stopwatch/v1` | `p1-scene-004` | 无 |
| `…/p1-scene-004-scout-3-protocol-invalid-same-id-retry-…/frames` | 2431 | 2431 | v1 / 无 | `p1-scene-004` | **2431/2431**（`p1-detect-scouting-truth/v2`） |
| `…/p1-scene-004-scout-4-closed-exchange/frames` | 2405 | 2405 | v1 / 无 | `p1-scene-004` | **2405/2405**（同上，真值在 `runtime/p1-scene-004-scouting/p1-scene-004-scout-4/truth`） |
| `…/p1-detect-001-scout-1-closed-exchange/frames` | 768 | 768 | v1 / 无 | `p1-detect-scouting` | 705（有缺口，`…truth/v1`） |
| `runtime/p1-scene-006/probe-baseline-vfov60` | 106 | 1（tick 步长 5） | **无帧元数据** | `deterministic-loop-default` | 106（`p1-scene-006-probe-truth/v1`，OK 99） |
| `runtime/p1-scene-006/probe-candidate-vfov40` | 106 | 1（同上） | 无帧元数据 | `p1-scene-006-difficult-v1` | 106（OK 52） |
| 其余 12 个 `rate-study-20hz` 目录 | 128–759 | ≤512 | v2 / 无 | `rate-study-20hz` | 无 |

**四条硬性资格规则**

1. **`runtime/frames` 禁止入任何 manifest**：它是活动环形缓冲
   （`runtime/scenario_config.json` `sensor.retained_frame_count = 4096`，
   窗口恰好 4096 宽），下一次 Unity 运行即覆盖，不可复现。
2. **缺件终态**：manifest 构建期发现声明文件缺失/哈希不符/真值缺帧
   ⇒ `CAL_INPUT_MANIFEST_INCOMPLETE`，硬停，不得跳过该帧继续。
3. **样本不足终态**：可用样本低于各实验的预注册下限 ⇒
   `CAL_INPUT_INSUFFICIENT`，硬停并回构思角色，不得降低下限。
4. **重冻结纪律**：扩充来源清单只允许在**首次查看该实验任何
   tuning/qualification 结果之前**整体重做，旧 manifest 连同其
   SHA-256 留档；一旦揭盲，禁止换样本（`CAL_INPUT_REFROZEN_AFTER_
   UNBLINDING` 即整实验作废）。
5. **循环依赖的解法（round 2 必修 6）**：manifest builder 本身属
   批次 1 的新工具，故"任何实现前先有 manifest"指的**不是**代码，
   而是**测量**。三阶段串行、状态不可逆：
   **S1 工具态**（写 builder + 三个实验脚本，零测量、零 manifest
   产出）→ 停点 + 写入归因 + 独立复核 → **S2 清单态**（跑 builder
   产出并提交 manifest，仍零测量结果；复核已通过的 builder 是
   manifest 可信的凭据）→ **S3 测量态**（T 拟合 → 参数 create-once
   冻结 → Q 揭盲 → 结果回 Acceptance）。S2 产出的 manifest 必须由
   S1 已复核的 builder 生成，builder 一改即回 S1。
6. **路径与哈希的规范字节**：manifest 内所有路径为
   **repo-relative、POSIX 分隔符、不以 `./` 开头**；文件 SHA-256 对
   **原始字节**计算（不做换行归一）；`manifest_sha256` 对 manifest 的
   canonical JSON 字节计算（`json.dumps(obj, sort_keys=True,
   separators=(",",":"), ensure_ascii=False, allow_nan=False)` 的
   UTF-8 编码，与 `P1-VLM-SCOPE-001` §2.4b 同口径）；§3.5 E4 引用块的
   SHA-256 对**不含末尾 LF** 的行 532–571 拼接字节计算（与取证时
   一致，`caff93be…58ba`）。
7. **串行状态的不可逆性**：任何 CAL 结果在经**新一轮 Acceptance
   归因**之前，不得用于恢复 `P1-VLM-SCOPE-001` revision 4 或任何
   VLM/M3′ 实现。S3 完成即交回 Acceptance，构思角色不自行续写
   recharter。

---

### 3.1 E1 — 颜色分割对照器可行性（本地，零 API 零 Unity）

**决定**：`P1-VLM-SCOPE-001` §3.1 属性档平权对照是否存在；HSV 带值；
逐色 90% 资格门的现实性。

#### E1.a 颜色标签权威（round 1 必修 2；C2 的修复）

真值 schema 无颜色字段，故标签权威**由本提案冻结**为下表
（RGB 由 prefab 贴图/代码字面量导出，逐行给出处；HSV 为
OpenCV 口径 `H∈[0,180], S,V∈[0,1]`，由 RGB 解析换算）：

| 类 | 对象 | 来源 | 主导 RGB | OpenCV H / S / V |
|---|---|---|---|---|
| **RED**（正例） | 目标车 body | 代码字面量 `TargetVisualFactory.cs:33` `new Color(0.9f,0.12f,0.1f)` | (230,31,26) | 0.7 / 0.887 / 0.902 |
| RED（正例，同体） | 目标车 roof | `TargetVisualFactory.cs:34` `(0.65f,0.08f,0.07f)` | (166,20,18) | 0.6 / 0.880 / 0.651 |
| **YELLOW**（正例） | `Vehicle_Taxi` | 贴图 `Textures/Vehicle_Taxi.png`（76% texel） | (239,188,42) | 22.2 / 0.824 / 0.937 |
| **PURPLE**（正例） | `Vehicle_SUV_color01` | 贴图 `Textures/Vehicle_SUV_1.png`（78%） | (162,140,182) | 135.7 / **0.231** / 0.714 |
| 反例（红族） | `Vehicle_Container_color03` / `Vehicle_Truck_color01` | 贴图（66/67%） | (201,74,69) | 1.1 / 0.657 / 0.788 |
| 反例（橙红） | `Vehicle_Pick up Truck_color01` | 贴图（80%） | (220,85,57) | 5.2 / 0.741 / 0.863 |
| 反例（琥珀） | TetherAnchor 标记 | 代码 `TetheredScenarioBootstrap.cs:180` `(0.95f,0.75f,0.1f)` | (242,191,26) | **22.9** / 0.893 / 0.949 |
| 反例（橙红） | DroneHub 球 | 代码 `:224` `(0.9f,0.25f,0.15f)` | (230,64,38) | 4.7 / 0.835 / 0.902 |

**三条由该表直接得出的设计约束（必须写进实现，不留裁量）**：

- **紫色不能用统一饱和度阈值**：`Vehicle_SUV_color01` 的 S 仅 **0.231**，
  任何 `s_min ≥ 0.45` 的统一规则会把它整类淘汰 ⇒ `s_min`/`v_min`
  **逐色独立**。
- **黄色不能只靠色相**：TetherAnchor 的 H = 22.9 与 taxi 的 H = 22.2
  相距 0.7，色相不可分 ⇒ 黄色带必须附加一条**非颜色**的确定性排除
  （见 E1.b 的 `exclude_anchor` 项）。
- **红色必须回绕**：目标 H ≈ 0.7，OpenCV 口径下须写成两区间
  `[0, h_hi] ∪ [180−h_lo, 180]`，单区间写法会在 H 略小于 0 的抖动帧
  漏检。

#### E1.b 冻结的规则族与可调参数空间

**规则族（冻结，实现者零裁量）**，逐帧对每个受测颜色 `c` 执行：

1. 读 JPEG → `cv2.imdecode(..., IMREAD_COLOR)`（BGR）→
   `cv2.cvtColor(..., COLOR_BGR2HSV)`（H∈[0,180]）。
2. 掩码 `M_c = (H ∈ band_c) ∧ (S ≥ s_min_c) ∧ (V ≥ v_min_c)`；
   `band_c` 对红色为两区间之并。
3. 形态学：`MORPH_OPEN` 后 `MORPH_CLOSE`，方核边长 `k_c`（奇数）。
4. `cv2.connectedComponentsWithStats`，8 连通；丢弃面积 `< a_min_c` px。
5. **`exclude_anchor`（仅黄色启用）**：由帧元数据的
   `camera_position_world_m` / `camera_rotation_xyzw` / `intrinsics_px`
   与 scenario 配置的 `anchor_world_m` 解析投影出锚点像素位置，剔除
   与该点距离 `< r_anchor` px 的连通域。**输入全部是配置与平台自身
   状态，不含任何 evaluator 真值**（与 `P1-VLM-SCOPE-001` §2.2 的
   可见集一致）。
6. 选择：**面积最大**的存活连通域，其外接矩形即该色的选框；无存活
   连通域 ⇒ 该帧该色输出 `NO_CANDIDATE`。
7. 面积并列（完全相等）⇒ 取 `(y, x)` 字典序最小者。

#### E1.b′ 拟合算法（round 2 必修 1：穷举网格 + 唯一目标 + 唯一 tie-break）

**色相中心不参与搜索**，逐字取 §E1.a 实测值（OpenCV 口径）：
红 `0.7`（回绕，实现为 `[0, h_w] ∪ [180−h_w, 180]`）、黄 `22.2`、
紫 `135.7`。**唯一可搜索的六个参数与其有限域**（逐色相同域）：

| 参数 | 有限域（穷举） |
|---|---|
| `h_w`（半宽，OpenCV 单位） | `{3, 5, 8, 12}` |
| `s_min` | `{0.15, 0.25, 0.35, 0.45, 0.60}` |
| `v_min` | `{0.15, 0.25, 0.35}` |
| `k`（形态学方核边长，1 = 不做形态学） | `{1, 3, 5}` |
| `a_min`（px） | `{30, 60, 120, 250}` |
| `r_anchor`（px，**仅黄色**；0 = 停用） | `{0, 15, 30}` |

网格规模：红/紫各 `4×5×3×3×4 = 720` 组，黄 `×3 = 2160` 组——**穷举
可行，不使用任何启发式搜索**。

**唯一目标函数**：在 T 组上最大化 `correct_count = HIT +
TRUE_NEGATIVE`（口径见 §E1.d）。

**冻结的枚举次序**（决定并列时谁被先遇到）：
`h_w → s_min → v_min → k → a_min → r_anchor`，各自按上表**从左到右**。

**唯一 tie-break**（按序比较，命中即定）：
(1) `correct_count` 大者胜；(2) `HIT` 帧上的平均 IoU 大者胜；
(3) `a_min` **大**者胜（偏保守）；(4) `h_w` **小**者胜；
(5) 枚举次序中**先遇到**者胜。第 5 条保证结果唯一。

**拟合产物**：写入 `config/p1-vlm-cal-e1-hsv.json`（含逐色六参数、
T 组 frame_id 集合、网格定义、目标值、被击败的次优组合）并记
SHA-256；**create-once**——文件已存在即拒绝覆盖，任何改动都使
qualification 结果作废。

#### E1.b″ 逐色真值集合的展开规则（round 2 必修 1）

| 色 | 真值来源 | 匹配规则 |
|---|---|---|
| RED | `target_bbox_xywh_norm`，正例条件为 **`target_box_status == "VALID"`**（`p1-detect-scouting-truth/v2`）或 **`target_box_status == "OK"`**（`p1-scene-006-probe-truth/v1`） | 单实例，无需匹配 |
| YELLOW | `distractors[]` 条目，正例条件为该条目的 `box_status` ∈ {`VALID`（v2）, `OK`（probe v1）} | `distractor_id` 的**规范前缀名**含子串 `Vehicle_Taxi` |
| PURPLE | 同上 | 同上，含 `Vehicle_SUV_color01` |

**round 3 必修 1 的字面更正（实测复核）**：revision 2 的 RED 行写
"probe 的 `box_status == "OK"`"是**错字段**。逐字核对三棵真值树：

| schema | 目标状态字段 | 实测取值分布 | distractor 状态字段 |
|---|---|---|---|
| `p1-detect-scouting-truth/v2`（scout-4，2405 帧） | `target_box_status` | `VALID` 2405 | `box_status` |
| `p1-scene-006-probe-truth/v1`（probe-baseline，106 帧） | `target_box_status` | `OK` 99 / `TARGET_NOT_VISIBLE` 7 | `box_status` |
| `p1-scene-006-probe-truth/v1`（probe-candidate，106 帧） | `target_box_status` | `OK` 52 / `TARGET_NOT_VISIBLE` 54 | `box_status` |
| `p1-detect-scouting-truth/v1`（detect-scout-1，705 帧） | **无该字段**（键集 = `target_visible` / `target_visible_sample_fraction` / `target_bbox_xywh_norm` / `target_slant_range_m` / `target_track_id`） | — | `box_status` |

即 `box_status` **只**属 `distractors[]` 条目，目标一侧在两个 schema 中
统一叫 `target_box_status`，v1 则根本没有它——这正是 §E1.d 第 5 行把
v1 的 `target_visible = false` 却带框的 46 帧整帧排除的原因，本轮不变。
**两处 `OK`/`VALID` 取值差异不得由实现者归一**：按 schema 分支判定，
遇到未列出的取值 ⇒ `CAL_E1_UNKNOWN_BOX_STATUS` 硬停。

规范前缀名 = `StableObjectId` 路径的最后一段去掉 ` (N)` 克隆后缀
（与 `SceneVehicleAdjustments.cs:107-120` 的 canonicalization 同义）。
工件必须逐帧记录实际匹配到的 `distractor_id` 全集与其个数；匹配到
0 条即该帧该色按"目标不在画面"处理（§E1.d 第 2/3 行）。

#### E1.b‴ Q2 的投影输入与 `exclude_anchor` 处置（round 2 必修 1）

实测：Q2（`p1-scene-006/probe-*`）**没有逐帧传感器元数据**，故
`exclude_anchor` 所需的 `camera_position_world_m` /
`camera_rotation_xyzw` / `intrinsics_px` 在该归档中**不存在**。冻结
处置（不发明替代数据源）：

- **T / Q1 / Q3**（scouting 归档，有帧元数据）：`exclude_anchor`
  **启用**；投影口径冻结为——世界点
  `anchor_world_m`（来自该 run 绑定的 scenario 配置）经
  `camera_rotation_xyzw` 的逆旋转变换到相机系，再以
  `intrinsics_px` 的 `fx, fy, cx, cy` 做针孔投影
  `u = fx·x/z + cx, v = fy·y/z + cy`；`z ≤ 0`（锚点在相机后方）
  ⇒ 该帧不做锚点剔除。
- **Q2**：`exclude_anchor` **停用**，工件逐帧标
  `anchor_exclusion = "disabled_no_camera_pose"`。停用只会**增加**
  假阳性，故 Q2 通过是保守的、Q2 失败须标注可能由锚点造成——Q2 本就
  只报告不设门（§E1.c）。
- **硬停**：若某帧声明启用却缺任一投影输入 ⇒
  `CAL_E1_PROJECTION_INPUT_MISSING`，整实验停，**不得**由实现者
  另找替代来源或静默跳过该帧。

#### E1.c 组隔离（C3 的修复；含诚实局限）

实测：`scout-3` 与 `scout-4` 是同一条轨迹（相机位置距离恰 0，目标框
最大分量差 0.00119），故**不能**充当互相隔离的两组。可用的真实隔离
只有跨 scenario。

| 组 | 来源 | scenario | 规模下限 | 作用 |
|---|---|---|---|---|
| **T（tuning）** | `scout-4` 的 `frame_id ∈ [0, 1199]` 中按每 40 帧取 1 的确定性抽样 | `p1-scene-004` | ≥ 30 帧 | 唯一允许拟合 HSV 的数据 |
| **Q1（主资格门）** | `scout-4` 的 `frame_id ∈ [1400, 2404]`，同样每 40 帧取 1 | `p1-scene-004` | ≥ 25 帧 | **逐色 90% 门**——它是对照器将来实际服役的场景族 |
| **Q2（泛化，报告不设门）** | `probe-baseline-vfov60` 全部 `target_box_status = OK` 帧（99） | `deterministic-loop-default` | 99 | 跨 scenario 泛化证据 |
| **Q3（已知困难，报告不设门）** | `detect-scout-1` 的连续段 `frame_id ∈ [243, 673]` 每 10 帧取 1 | `p1-detect-scouting` | ≥ 40 帧 | 体育场红色看台的对抗性下界 |

**诚实局限（硬性写进证据文件）**：归档中每个场景族只有**一条重复
行驶的轨迹**（`scout-4` 采样 2 Hz、2405 帧 ≈ 1202 s ≈ 38 圈，环周长
62.142136 m、目标 2.0 m/s），因此 T 与 Q1 的分段隔离**只隔离了时间，
未隔离视角**，强度弱于跨 run 隔离。这不是可以靠措辞消除的缺陷：
现有冻结归档中不存在同族的第二条独立轨迹。防泄漏的真正保障是
**HSV 在任何 VLM-2 正式配对 run 之前冻结并哈希**（`P1-VLM-SCOPE-001`
§3.1 已写），E1 只回答"这套规则能不能达到 90%"。若 amendment 需要
真正的同族独立资格集，须另行采集（COORD-005 诊断通道，零配额），
本提案不预取该授权。

**Q3 的预期与其处置**：`detect-scout-1` 是体育场场景，红色看台连通域
实测达 11224 / 7383 / 6565 / 3293 / 2811 / 1908 px，而目标仅约
172 px，"取最大红色连通域"在该场景必然近乎全错。该结果**预期为负**，
按 §3.1 的分层报告如实登记，**不触发规则回炉**——它证明的是对照器
的场景依赖性，而对照器只在 VLM-2 的冻结场景内服役。

#### E1.d 逐帧计分与例外（round 1 必修 2 的唯一处置规则）

| 情形 | 判定 |
|---|---|
| 该色有真值框且 `target_box_status`/`box_status` 为 `VALID`/`OK`，规则输出框 | IoU ≥ 0.5 ⇒ `HIT`；否则 `MISS` |
| 真值标注该色目标**不在画面**（`TARGET_NOT_VISIBLE`，或 probe 的全零框 + `NOT_IN_FRAME`），规则输出 `NO_CANDIDATE` | `TRUE_NEGATIVE`（计入分母，记为正确） |
| 同上但规则输出了框 | `FALSE_POSITIVE`（计入分母，记为错误） |
| 该色有真值框但规则输出 `NO_CANDIDATE` | `MISS` |
| **v1 真值的 `target_visible = false` 却仍带框**（实测 `detect-scout-1` 705 帧中 46 帧属此） | **整帧排除**并单列计数；`p1-detect-scouting-truth/v1` 无 `target_box_status`，其可见性语义不足以支撑正负判定 |
| 同色多实例（如 12 个 taxi 后缀实例）真值给出多个框 | 规则输出的单框与**任一**同色真值框 IoU ≥ 0.5 即 `HIT`；工件必须同时记录同色真值框个数 |
| 真值文件缺失/解析失败 | `CAL_INPUT_MANIFEST_INCOMPLETE`（§3.0 规则 2），不是逐帧排除 |

**分母与门**：逐色分母 = 该色在该组内的
`HIT + MISS + TRUE_NEGATIVE + FALSE_POSITIVE`；逐色正确率 =
`(HIT + TRUE_NEGATIVE) / 分母`。**门 = Q1 上三色各自的点估计
≥ 90%**（逐色，非汇总——汇总会让一个失败色被两个成功色掩盖）；
同时报告 Wilson 95% 区间与 Q2/Q3 分层结果。

**停止/失败规则**：三色全过 ⇒ 属性档对照成立，HSV 带候选进
amendment；任一色 < 90% ⇒ 如实报告
`COLOR_CONTROL_INFEASIBLE_<COLOR>`，属性档对照回构思角色重设计
（可选路径：缩到通过的颜色子集、或改用别的非学习对照）；**禁止
回 Q1 调参重测**。

**成本**：脚本约半天；运行秒级；零 API、零 Unity、零配额。

---

### 3.2 E2 — 真实 replay/catch-up 耗时分布（本地，零 API 零 Unity）

**决定**：`vlm_reprompt.catchup_timeout_s` 与 `frame_buffer_s` 的导出
依据。`P1-TRACK-002` 的 `3.332854 ms` update-only 常量**降为交叉
检查**，不再是唯一依据。

#### E2.a 被测路径（round 1 必修 3：逐字锁定，实测确认）

生产路径的精确语义（本轮取证已逐行核对并以真实对象跑通）：

- `ReanchorRuntime._catch_up`（`controller/reanchor_runtime.py:281-326`）
  是一个 `while self.monotonic() - started <= catchup_timeout_s` 的
  **无迭代上限**循环（:287，前测、闭区间）：每轮在锁内重取
  `history.snapshot()` 与 `head`（:288-290）→ 调用一次
  `replay_tracker`（:303-309），其内层预算为
  `max(0.001, catchup_timeout_s − 已耗)`（:307）→ 非 `RESEED_READY`
  立即返回（:310-312）→ 否则比对 `history.head_frame_id == head`
  （:313-315），**相等才返回，不等则再来一轮**。实测：永不收敛时
  单次 `_catch_up` 可调用 `replay_tracker` **20 次**；第二轮收敛时
  调用 2 次。超预算终态为 `RESEED_DISCARDED_NOT_CONVERGED` /
  `catchup_timeout`（:316-326）。
- `replay_tracker`（`controller/reanchor.py:653-692`）的十个终态逐字
  为：`source_frame_missing`(:667)、`target_frame_missing`(:670)、
  `source_result_too_old`(:672)、`invalid_source_box`(:676)、
  `tracker_init_failed`(:678)、`catchup_timeout`(:683)、
  `invalid_replay_box`(:687)、`RESEED_READY`(:688)、
  `intermediate_frame_missing`(:690)、裸异常类名(:692)。
- **两个必须复现的顺序事实**：`tracker = tracker_factory()`(:674)
  **先于** `valid_replay_box(source_box_norm)`(:675)；且
  `trackers.py:338` / `:258-259` 的 `FileNotFoundError` 落在
  `reanchor.py:673` 的 `try` 内，故**缺模型会伪装成
  `intermediate_frame_missing`**——benchmark 必须在开跑前独立断言
  四个模型文件的 SHA-256，否则会把配置错误测成帧缺失。

#### E2.b Harness 级别（二选一，预注册 Level A）

| 级别 | 路径 | 可用归档 | 代价 |
|---|---|---|---|
| **Level A（预注册）** | 经 `ReanchorRuntime`，忠实于生产 | 帧必须 `tethered-sensor-frame/v3` + `system-stopwatch/v1`（`sensor_protocol.py:9-10, 18-29` 硬拒其余），**冻结归档中只有 3 个**：qual-2（3668）、CLOCKSMOKE（2888）、`rs3-clock-smoke/phase1-hold`（173） | 忠实 |
| Level B（不采用） | 直调 `replay_tracker` + 手搓 `BufferedFrame` | v1/v2 归档亦可，但须自造满足 `FrameHistory.append` 严格递增校验（`reanchor.py:578-585`）的时间戳 | 偏离生产入口 |

**预注册来源**：`runtime/test-results/p1-detect-001-qual-2-protocol-
invalid-exchange/frames`，`frame_id 0–3667`，v3 /
`system-stopwatch/v1` / `p1-scene-004` / 640×480。该目录名标记的是
**当时采集交换协议无效**，与其字节作为"一批合法的连续传感器帧"无关；
E2 不消费其任何测量结论，只用其帧序列做计时。

#### E2.c 测量设计（帧数档取代秒数档）

**为什么改档**：replay 成本由**帧数**决定，而帧数 = 年龄 × `capture_hz`；
`scenario.p1-scene-004.json` 的 `capture_hz` 是 **20.0**，
`scenario.default.json` 是 5.0。revision 0 隐含按 5 Hz 折算，会把
20 Hz 场景的成本低估 4 倍。故 E2 直接以帧数为自变量，年龄→帧数的
换算留给 amendment。

- **帧数档** `N ∈ {25, 50, 100, 200, 300}`（覆盖 5 Hz 的 5–60 s 与
  20 Hz 的 1.25–15 s）。
- **每档 60 个预注册起点**：`start = 100 + 55·i, i = 0..59`（确保
  `start + 300 ≤ 3667`），逐档相同起点集，写入 manifest。
- **冷/热**：每档第 1 次为冷启动（进程新起、页缓存未预热），其余
  59 次为热；**两者分列报告**，导出用热（长驻网关的实际工况），冷
  作为尾部披露。参考量级（本轮取证实测）：factory 冷 ≈ 148 ms、
  热 ≈ 4.3–4.9 ms；单次 `update` ≈ 3.8 ms @640×480。
- **两道会先于计时弹掉长档的门（round 2 必修 2 的实测根因）**：
  (a) `replay_tracker` 的 `head.capture_monotonic_s −
  source.capture_monotonic_s > maximum_source_age_s` ⇒
  `RESEED_DISCARDED_STALE`（`reanchor.py:672`）——20 Hz 下
  `N > 40` 帧即触发；(b) `FrameHistory.append` 的
  `cutoff = capture − duration_s` 驱逐（`reanchor.py:600-602`）——
  `frame_buffer_s = 6.0` 在 20 Hz 下只保留约 120 帧，`N ≥ 120` 的
  源帧会被逐出，`after_through` 随即抛
  `FileNotFoundError("replay intermediate frame missing")`
  （`:612-617`）。故 `N ∈ {100, 200, 300}` 在原参数下**测不到**
  replay 成本，只会测到两道门。
- **逐档注入参数（唯一表，实现者零裁量）**。令 `hz = 20`（qual-2 的
  归档采集率）、`T_N = N / hz`：

  | 参数（**配置键**） | 注入值 | 理由 |
  |---|---|---|
  | `maximum_result_age_s` | `T_N + 2.0` | 抬过 (a) 门，保留原 2.0 s 余量语义 |
  | `frame_buffer_s` | `T_N + 4.0` | 抬过 (b) 驱逐，保证源帧在整个 replay 期存活 |
  | `catchup_timeout_s` | `60.0` | 大到不截断计时；循环靠 head 相等退出而非超时 |
  | 其余 18 个参数 | **原值不动** | 仅上述三项影响退出路径 |

  `N=25/50/100/200/300` ⇒ `T_N = 1.25/2.5/5/10/15 s`。

  **round 3 必修 2 的字面更正（实测复核，这是 revision 2 的硬错误）**：
  revision 2 的注入表第一行写 `maximum_source_age_s`，**该键在配置中
  不存在**。`_strict_keys` 的 21 个必需参数名里没有它
  （`reanchor.py:231-245`），而 `maximum_source_age_s` 只是
  `replay_tracker` 的**形参名**（`reanchor.py:660`）。真实链路是
  `ReanchorRuntime._catch_up` 在 `reanchor_runtime.py:306` 写
  `maximum_source_age_s=float(self.p["maximum_result_age_s"])`——
  即配置键是 **`maximum_result_age_s`**。按 revision 2 的字面执行会
  往 `raw["parameters"]` 塞一个多余键（`_strict_keys` 在
  `load_reanchor_config` 里会拒，进程内构造则会被静默忽略），
  2 s 年龄门**根本没被抬高**，`N = 100/200/300` 仍会先撞
  `RESEED_DISCARDED_STALE`——恰是 round 2 必修 2 要修的那条。
  上表已改为真实键。

  **注入生效点（顺序硬性）**：`FrameHistory` 在
  `ReanchorRuntime.__init__`（`reanchor_runtime.py:59`）就以
  `float(self.p["frame_buffer_s"])` 构造，故三项覆盖必须在
  **构造 `ReanchorRuntime` 之前**写进 `ReanchorConfig.raw` 的深拷贝；
  构造之后再改 `raw` 对 `history.duration_s` 无效。工件必须回读并记录
  `runtime.history.duration_s`、`runtime.p["maximum_result_age_s"]`、
  `runtime.p["catchup_timeout_s"]` 三个实际生效值，与本表不符即
  `E2_INJECTION_NOT_IN_EFFECT` 硬停。

- **冻结的 `source_box_norm`（round 3 必修 2：唯一来源与字节）**。
  `_catch_up` 的 `box` 在生产中来自 `decision.winner.box_norm`；
  benchmark 不跑检测器，故该框必须由 manifest 冻结为**单一字面量**，
  **五档、60 个起点、冷热全部使用同一个框**：

  | 项 | 值 |
  |---|---|
  | 像素框（640×480，top-left 原点 `xywh`） | `(353, 82, 72, 44)` |
  | 归一化字面量（写入 manifest，十进制精确值） | `[0.5515625, 0.17083333333333334, 0.1125, 0.09166666666666666]` |
  | 出处 | `P1-DETECT-001` qual-3 Attempt 3 第 159 帧的**用户确认无真值**框（`docs/unity-test-log.md`；状态板 Recent Unity validations 2026-07-31 条目逐字记录）；同一 scenario 族 `p1-scene-004`、同一 640×480 光学 |
  | 真值边界 | 该框由人眼在图像上确认，**不来自任何 evaluator 真值文件**；qual-2 归档本身也**零真值**（§3.0 表），故 E2 全程无 truth 可读 |

  **为什么必须是同一个框**：逐档另选框会把"档位 N"与"框内容"混淆，
  拟合出的 `per_frame` 斜率不再只反映帧数。**为什么可以是同一个框**：
  `replay_tracker` 对该框只做 `valid_replay_box` 校验与
  `tracker.init(source.image, box)`，NanoTrack-v2 以框为中心裁搜索域后
  缩放到固定输入尺寸，单次 `update` 成本与框内容无关（本轮实测
  ≈ 3.8 ms @640×480，与 TRACK-002 的 `3.332854 ms` 同量级）。
  该框**不需要**框住任何真实车辆——E2 测的是 replay 的**耗时**，不是
  它的跟踪正确性。若跟踪器在某次 replay 中漂到无效框，
  `replay_tracker` 返回 `RESEED_DISCARDED_INVALID_BOX` /
  `invalid_replay_box`，该样本按下文**失败样本**记账，不进分位。
- **注入方式与字节边界**：`ReanchorConfig` 是 `(path, raw, sha256)`
  的薄包装、`parameters` 只读 `raw["parameters"]`
  （`reanchor.py:72-79`），故 harness **在进程内**用冻结文件的 `raw`
  深拷贝 + 上表三项覆盖构造 config 对象，**不经**
  `load_reanchor_config`（其相等门 `reanchor.py:241-265` 会拒绝任何
  偏离）。`config/detector-reanchor.models.json` **字节不动**，且
  benchmark 开跑前须先对**未修改的原文件**成功执行一次
  `load_reanchor_config` 以证明字节完好（失败即硬停）。
- **头帧推进的确定性握手（round 2 必修 2：取代"独立线程至少两轮"）**：
  线程按时间推进无法机械保证 head 恰在每次 equality check 前改变。
  改为**在 `history.snapshot` 上装计数代理**：第 1 次调用返回克隆后，
  立即向**活动** history 追加 1 帧（来自同一归档的下一个
  `frame_id`）；第 2 次及以后不追加。由此循环必然是
  `snapshot#1 → replay#1 → equality#1 失败 → snapshot#2 → replay#2 →
  equality#2 成功`，**replay 轮数恒为 2**，无线程竞态。
- **握手不变量是仪器硬停，不是重跑（round 3 必修 2）**：工件逐次记录
  `history.snapshot` 与 `replay_tracker` 的实际调用次数；任何一次
  `≠ 2` ⇒ **`E2_HANDSHAKE_INVARIANT_VIOLATED`，整实验立即停止并回构思
  角色**。revision 2 写的"≠2 即该次作废重跑"是错的：它让仪器在自己
  失准时**自行丢弃不合意样本**，与 §3.2 下文"失败样本必须双重记账"
  的整条纪律自相矛盾，也正是 F23 那类"协议全对、测的东西不对"的
  入口。握手代理是确定性的，一次违例即证明该代理的前提不成立，
  剩余样本全部不可信——不存在"这次不算"的合法处置。
- **失败记账与分位的精确关系（round 2 必修 2）**：失败样本**没有
  合法的耗时语义**（它在门上被弹回，未完成 replay），故**不以任何
  数值进入 type-7 分位**；分位只对成功样本计算。为防止"筛掉失败样本
  美化分布"，冻结双重记账：每档必须同时报告
  `attempted = 60`、`valid_n`、逐终态失败计数表；**且该档只有在
  `valid_n ≥ 48`（80%）时才可 admissible**，否则标
  `E2_TIER_UNSTABLE` 并在 amendment 中整档排除（不得用剩余成功样本
  冒充该档分布）。
- **分位实现冻结**：`numpy.percentile(x, 95, method="linear")`
  （= type-7），numpy 版本入 manifest。
- **单位闭合（round 2 必修 2）**：全部原始测量以 **ms** 记录并报告；
  导出公式在秒域计算，换算显式写在公式内（见 §3.2.d），
  `ceil_0.5` 只作用于**秒**。
- **环境前置（硬性）**：必须在 `~/TetheredDroneTracking/.venv-track`
  下运行——系统 `python3` 无 `cv2`，而 `NanoTrackV2Tracker.__init__`
  （`trackers.py:402-407`）硬要求 `cv2.__version__ == "5.0.0"`。
  manifest 记录实际 `cv2.__version__` 与 `sys.version`。
- **模型绑定（开跑前断言）**：
  `runtime/models/nanotrack-v2/nanotrack_backbone_sim.onnx`
  `530bdd0c…2fc4`（1 056 849 B）、`nanotrack_head_sim.onnx`
  `0d8c0637…7cd9`（726 198 B）、`config/nanotrack-v2.models.json`
  `43c81ad9…6026b`（1 956 B）、`config/detector-reanchor.models.json`
  `593734d6…706d2`（3 444 B）。
- **冻结的 reanchor 参数**（`config/detector-reanchor.models.json`，
  由 `reanchor.py:241-265` 的相等门强制）：
  `maximum_result_age_s 2.0`、`frame_buffer_s 6.0`、
  `catchup_timeout_s 2.0`、`worker_timeout_s 10.0`、
  `consecutive_failure_limit 3`。E2 **不修改**它们；为测长档，
  benchmark 以显式参数覆盖对象注入更大的 `catchup_timeout_s`
  （仅在 harness 内，不写配置字节），该覆盖值入 manifest。

#### E2.d 导出与失败分支

- 报告：逐档 `{N, 冷/热, total_ms, fixed_overhead_ms, per_frame_ms}`
  的 p50/p95/max + 设备标识（型号、OS、并发负载声明）。
- **导出公式（预注册，单位显式）**：
  `catchup_cand(age_s, hz) = ceil_0.5( 2 × ( p95_fixed_ms +
  p95_per_frame_ms × age_s × hz ) / 1000 )`，两个 p95 取自热启动
  分布、单位 ms，除以 1000 转秒后再 `ceil_0.5`；
  `buffer_cand = ceil_1( age_s + catchup_cand + 2 )`（全秒域）。

- **`p95_fixed_ms` / `p95_per_frame_ms` 的完整估计式（round 3 必修 2）**。
  revision 2 只说"残差校正后的 p95"，没有可独立复算的定义。本轮冻结为
  三步，任何一步都只依赖工件里已有的数：

  **步骤 1 — 唯一的一次 OLS**。样本集 `J` = 五档全部**热启动且成功**的
  样本（冷启动样本与失败样本都不在 `J`）。对 `(N_j, y_j)`
  （`y_j` = 该次 `_catch_up` 实测 `total_ms`）做闭式最小二乘：

  ```
  per_frame₀ = Σ_J (N_j − N̄)(y_j − ȳ) / Σ_J (N_j − N̄)²
  fixed₀     = ȳ − per_frame₀ · N̄
  ```

  `N̄`、`ȳ` 为 `J` 上的算术平均。分母恒 > 0（五档 N 不全相等）。

  **步骤 2 — 两个分位量各自的定义（不是残差的分位）**：

  ```
  p95_fixed_ms     = numpy.percentile( [ y_j − per_frame₀ · N_j  for j in J ], 95, method="linear" )
  p95_per_frame_ms = numpy.percentile( [ (y_j − fixed₀) / N_j    for j in J ], 95, method="linear" )
  ```

  即：把同一次 OLS 的**另一个**系数当作已知量扣掉，对剩下的那一项取
  经验 p95。两式都只对 `J` 求值，无自由参数，第三方拿工件里的
  `(N_j, y_j)` 列表即可逐位复算。

  **步骤 3 — 必须披露的保守性**：导出公式同时用两个 p95，等于把尾部
  计了两次，`catchup_cand` 因此是**上界而非点估计**。证据文件必须并列
  报告直接量 `p95_total_ms(N*) = numpy.percentile([y_j : N_j = N*], 95,
  method="linear")`（`N*` = amendment 选定 `age × hz` 后最接近的档），
  以及两者之比；差值大于 2 倍时在 amendment 中显式说明为何仍取上界。

  **具名硬停 `E2_LINEAR_MODEL_REJECTED`**：若 `per_frame₀ ≤ 0`，或
  `J` 上的判定系数 `R² = 1 − Σ(y_j − fixed₀ − per_frame₀N_j)² /
  Σ(y_j − ȳ)² < 0.5`，则"耗时 = 固定开销 + 每帧开销 × 帧数"这个模型
  被自身数据证伪，**导出公式不得使用**，如实报告并回构思角色重设计
  代价模型。不允许改档位、换样本或改拟合式后重试。

- **生产可达性披露（round 3 必修 2）**：注入的 `catchup_timeout_s = 60.0`
  只是量程，不是生产可达值。生产中 `_catch_up` 跑在
  `SingleFlightWorker`（`reanchor.py:704-760`）内，其
  `timeout_s = worker_timeout_s = 10.0`。故工件必须逐档报告
  `count(total_ms > 10000)`；该计数 > 0 即标
  `E2_EXCEEDS_PRODUCTION_WORKER_TIMEOUT` 并在 amendment 中写明：该档的
  replay 在现行 worker 预算下**根本完不成**，`catchup_timeout_s` 的
  上界讨论必须连同 `worker_timeout_s` 一起重议。
- **失败分支**：以 amendment 届时选定的 `age` 与目标场景 `capture_hz`
  代入后 `catchup_cand > 4.0 s` ⇒ 如实报告
  `E2_CATCHUP_EXCEEDS_CONTRACT_BOUND`，`P1-VLM-SCOPE-001` §2.4a 的
  上界或机制需重议（选项含降低 `capture_hz`、缩短 age、或改架构）；
  **禁止截断到 4.0**。
- 交叉检查：`p95_per_frame` 与 TRACK-002 的 `3.332854 ms` 并列披露，
  差异不构成失败，只作量级核对。

**成本**：脚本约半天；运行数分钟；零 API、零 Unity、零配额。

---

### 3.3 E3 — 文件桥耐久语义崩溃注入（本地，零 API 零 Unity）

**决定**：`P1-VLM-SCOPE-001` §2.4b 的 ACK 状态机耐久点设计与
`CRASH_OUTCOME_UNKNOWN` 的适用范围。

#### E3.a 故障模型分层（round 1 必修 4）

| 模型 | 定义 | 本轮 |
|---|---|---|
| **M1** | 写入进程被 `SIGKILL`，**内核与页缓存存活** | **测**。可回答"进程崩溃窗口"，即 ACK 状态机面对的实际故障 |
| **M2** | 掉电 / 内核 panic，页缓存丢失 | **不测**。需 VM 或硬件断电台架 |

**结论收窄条款（硬性）**：本轮全部结论只对 M1 成立，证据文件与
amendment 引用处必须逐字写明"未测 M2"。额外的诚实披露：本仓库
**零处**使用 `F_FULLFSYNC`（`grep` 于 `Assets/`、`controller/`、
`tools/` 全零命中），而 macOS 上 `fsync(2)` 不保证介质落盘，故
即使 M1 全绿也**不得**推断任何掉电耐久性。

#### E3.b 被测对象（真实实现 + 明标转写）

**round 3 必修 3 的根本改动**：revision 2 给所有对象套同一张 `B0`–`B4`
模板，而这四类写出器**不共享同一条语句序列**——套模板就必然造出不可达
的格。本轮改为**逐对象按其真实语句序列命名边界**，边界名带对象前缀，
不再假装是同一套坐标。仓库里的写出器逐字清点为 **5 个 Python + 1 个 C#**：

| # | 对象 | 形态 | 真实语句序列（逐行取证） |
|---|---|---|---|
| **W1** | `RunLogger.append`（`controller/run_log.py:523-528`） | **真实代码**直调 | `json.dump(dict(record), self._frames, sort_keys=True, allow_nan=False)` → `self._frames.write("\n")` → `self._frames.flush()`。**无 open、无 fsync、无 publish**；流由 `open("a", encoding="utf-8")` 默认缓冲打开（`:516`） |
| **W2** | `RunLogger.close`（`:537-543`） | **真实代码**直调 | `flush()` → `os.fsync(fileno)` → `close()` → `self._closed = True`。这是 `frames.jsonl` 的**唯一** fsync |
| **W3** | `protocol.atomic_write`（`controller/protocol.py:39-58`） | **真实代码**直调 | `mkdir` → `mkstemp(dir=…, suffix=".tmp")`（**无 prefix** ⇒ 残留是**可见**的 `tmpXXXXXXXX.tmp`）→ `json.dump(indent=2)` → `write("\n")` → `flush` → `os.fsync` → `close`（fdopen 上下文退出）→ `os.replace` → `finally: unlink(missing_ok=True)` |
| **W4** | `rate2_protocol.atomic_bytes`（`controller/rate2_protocol.py:67-84`） | **真实代码**直调 | 同 W3 的 replace 族，但：`prefix=f".{path.name}."` ⇒ 残留是**隐藏**点文件；`"wb"` 二进制；写入 `canonical_json_bytes`（`indent=2, sort_keys=True` + 末尾 `\n`） |
| **W5** | `rate2_protocol.create_once_bytes`（`:91-118`） | **真实代码**直调 | **preflight**：`if path.exists():` → 字节相等则**直接 return**（一个字节也不写）／不等则**直接 raise `FileExistsError`**；否则 `mkdir` → `mkstemp`（隐藏 prefix）→ `write` → `flush` → `os.fsync` → `close` → **`os.link(temporary, path)`**（硬链接，非 replace；`FileExistsError` 时回读比对）→ `finally: unlink(missing_ok=True)` |
| **C1** | C# `AtomicFile`（`Assets/…/AtomicFile.cs:8-20, 22-34, 36-48`） | **静态审计 + 明标"转写模型"的 Python 复刻** | `TemporaryPath` = `Directory.CreateDirectory` + `.<name>.<Guid>.tmp`（`:41`）→ `File.WriteAllText/WriteAllBytes(temp)` → `Publish`（`if (File.Exists(dest)) File.Replace(temp,dest,null); else File.Move(temp,dest);`）→ `finally { if (File.Exists(temp)) File.Delete(temp); }`。`Assets/**/*.cs` 内 `fsync/FlushToDisk/Flush(true)/F_FULLFSYNC` **零命中** |

**W5 与 W3/W4 的关键差异（决定了下表的形状）**：`os.replace` 会把 temp
**改名**到目标，temp 路径随即不存在，`finally` 的 `unlink` 是空操作
⇒ W3/W4 **不存在"发布后残留"**；`os.link` 只是**增加一个名字**，temp
仍然在，必须靠 `finally` 删掉 ⇒ W5 的"发布后-清理前"是**真实可达且
唯一**会留下隐藏残留的窗口。这条差异是 E3 对 §2.4b 最直接的产出，
revision 2 把两者塞进同一个 `B4` 格时把它抹掉了。

**`run_log._atomic_json`（`run_log.py:36-51`）——审计不注入（显式决定，
非遗漏）**：它是 `manifest.json` 与 `snapshot_json` 的写出器，语句序列
= W4 的 replace 族 + W3 的文本模式，两个差异轴（temp 命名、文本/二进制）
都已被 W3、W4 各自覆盖，联合无新增边界。故本轮**只做静态审计并在结果
表中列一行 `AUDITED_NOT_INJECTED` 与本理由**，不占注入预算。若复核角色
认为该合并不成立，回构思角色补一行 100 次注入即可，不影响其余结论。

**C1 的诚实边界**：C# 路径无法在 Unity 之外真实执行，故 E3 对它只做
(a) 静态审计（上表事实，可机械复算）与 (b) 一个**逐字标注为"转写
模型、非真实代码"**的 Python 复刻（复现调用顺序与 temp 命名，用于
探查残留与替换窗口）。`File.WriteAllText` / `File.Replace` 的 .NET
语义、`O_APPEND` 原子性、`io.DEFAULT_BUFFER_SIZE` 等属**外部平台
事实**，在证据文件中单列为"未由本仓库断言"。

#### E3.c 试验矩阵（round 3 必修 3：按真实语句序列逐格冻结）

**hook 形态冻结（不变）**：被测函数由一个薄 `instrumented_*` 包装重写为
逐步调用，在每个边界处向父进程管道写一个 ASCII 标记并 `os.read` 阻塞；
父进程读到标记后 `os.kill(child, SIGKILL)`。包装体逐字复现被测函数的
语句序列——包装本身入复核范围。**每格 20 次**。

**边界按对象命名**（名字里带对象前缀，不再共用 `B0`–`B4` 坐标）：

| 行 | 对象 · 初态 | 冻结的边界（= 真实语句之间的位置） | 记录尺寸 | 格数 | 次数 |
|---|---|---|---|---|---|
| **R1** | W1 `RunLogger.append` · append（目标已含 10 条完整记录） | `A1` dump 后-`write("\n")` 前；`A2` `write("\n")` 后-`flush()` 前；`A3` `flush()` 返回后 | 540 / 770 / **8200** B 各一组 | 3 × 3 = 9 | 180 |
| **R2** | W2 `RunLogger.close` · 前序 append 已全部 flush | `C1` `flush()` 后-`os.fsync` 前；`C2` `os.fsync` 后-`close()` 前 | 不写新记录 | 2 | 40 |
| **R3** | W3 `protocol.atomic_write` · **create**（目标不存在） | `T1` mkstemp 后-写入前；`T2` `write("\n")` 后-`flush` 前；`T3` `flush` 后-`fsync` 前；`T4` `fsync` 后-`close` 前；`T5` `close` 后-`os.replace` 前；`T6` `os.replace` 后-`finally unlink` 前 | ~1 KB | 6 | 120 |
| **R4** | W3 · **overwrite**（目标已存在且字节 = OLD） | 同 R3 六个 | ~1 KB | 6 | 120 |
| **R5** | W4 `rate2_protocol.atomic_bytes` · overwrite | 同 R3 六个（二进制 + 隐藏 temp 前缀） | ~1 KB | 6 | 120 |
| **R6** | W5 `create_once_bytes` · **create**（目标不存在） | `L1` mkstemp 后-写入前；`L2` 写后-`flush` 前；`L3` `flush` 后-`fsync` 前；`L4` `fsync` 后-`close` 前；`L5` `close` 后-**`os.link`** 前；`L6` **`os.link` 后-`finally unlink` 前**（W3/W4 不存在的窗口） | ~1 KB | 6 | 120 |
| **R7** | W5 · **overwrite**（目标已存在） | **零注入**——见下方"preflight 终态" | — | 0 | 0 |
| **R8** | C1 AtomicFile **转写模型** · create（`Publish` 走 `File.Move`） | `M1` `WriteAllText(temp)` 后-`Publish` 前；`M2` `File.Move` 后-`finally Delete` 前 | ~1 KB | 2 | 40 |
| **R9** | C1 转写模型 · overwrite（`Publish` 走 `File.Replace`） | `M1`；`M2′` `File.Replace` 后-`finally Delete` 前 | ~1 KB | 2 | 40 |
| — | `run_log._atomic_json` | `AUDITED_NOT_INJECTED`（理由见 §E3.b 末段） | — | 0 | 0 |

**合计 `180 + 40 + 120 + 120 + 120 + 120 + 0 + 40 + 40 = 780` 次注入。**
（revision 2 报 660，按其自身表内数量直接求和实为 680；两个数都作废，
本表按逐格数量重算为 780，任何单元格的增删都必须同步改这个总数。）

**R7 —— `create_once_bytes` 的 overwrite 初态不是 kill 矩阵（round 3
必修 3 的核心更正）**。`rate2_protocol.py:92-96` 的 preflight 在**创建
temp 之前**就结束了整个调用：

```
if path.exists():
    if path.read_bytes() == value: return path          # 同字节：零写入，正常返回
    raise FileExistsError("immutable artifact already exists with different bytes")
```

两条路径都不经过 mkstemp/write/flush/fsync/link，**`L1`–`L6` 在 overwrite
初态下全部不可达**——revision 2 的 P3b 行（"同上 `B0`–`B4`"，20 次/格）
描述的是一段**不存在的控制流**。取而代之，R7 冻结为**两条确定性断言**
（各执行 1 次，不需要 SIGKILL）：

| 断言 | 前置 | 期望 |
|---|---|---|
| `R7.a` | 目标存在且字节**等于** `value` | 返回目标路径；目录内 `.<name>.*.tmp` 残留数 = 0；目标字节不变（inode 亦不变） |
| `R7.b` | 目标存在且字节**不等于** `value` | 抛 `FileExistsError`；残留数 = 0；目标字节保持 OLD |

第二条 `FileExistsError` 分支（`:111-115`，`os.link` 撞名后回读比对）
只能由**并发**竞争到达，本轮 M1 单进程注入不覆盖，**在结果表中显式记为
`NOT_EXERCISED_SINGLE_PROCESS`**，不得当成"已验证"。

**revision 2 的另一处不可达描述一并更正**：其 P1 行把 `B3` 写成
"fsync 后、publish 前"。`RunLogger` 的 append/close 路径**没有 publish
语句**（无 replace/link/move），R1/R2 的边界表已按真实语句重列。

**读回 oracle**：每次注入后由**独立新进程**执行——(1) 读目标文件原始
字节；(2) 按对象口径列残留——W3 为**可见**的 `tmp*.tmp`，W4/W5/C1 为
**隐藏**的 `.<name>.*.tmp`（C1 为 `.<name>.<guid>.tmp`）；(3) 对 append
目标，用 `run_log.read_frame_records` 的同口径解析器逐行解析。三步的
输出即 §E3.c′ 的四维向量。

#### E3.c′ 结果空间：冻结的多标签向量（round 2 必修 3）

七类不互斥（`TEMP_RESIDUE` 可与 `OLD_VALUE`/`NEW_VALUE`/
`PARTIAL_CONTENT` 并存，`TRUNCATED_TAIL` 可伴随
`DUPLICATE_RECORD`），故改为**正交维度的向量**，每维内部互斥且
完备：

| 维度 | 取值（互斥且完备） | 完备性依据 |
|---|---|---|
| `dest_state` | `MISSING` / `OLD_VALUE` / `NEW_VALUE` / `PARTIAL_CONTENT` | 目标要么不存在，要么其字节等于旧值、等于新值，或二者皆非——按字节比较对全体字节串的划分 |
| `temp_residue` | `NONE` / `PRESENT` | 目录列举的布尔判定 |
| `tail`（仅 append 对象） | `CLEAN` / `TRUNCATED_TAIL` | 解析器的两种终态（`run_log.py:66-72` 恰容忍 1 行截断尾） |
| `dup`（仅 append 对象） | `NONE` / `DUPLICATE_RECORD` | 解析出的记录序列与预期序列比对的布尔判定 |

结果表按 `对象 × 初态 × 边界 × 记录尺寸` 给出四维向量的联合计数，
因此唯一且可复算；不存在需要优先级消歧的重叠。

**append 记录规格**（取自真实归档，供分块判定）：实测
`rate20-follow-r1/frames.jsonl` = 2 897 417 B / 5 381 行，单行
min 528 / median 538 / max 614 B；`rs2-r20-follow-1` = 4 216 154 B /
5 513 行，min 671 / median 767 / max 773 B。注入用记录须覆盖
`{540 B, 770 B, 8 200 B}` 三档（末档跨越默认 8192 缓冲边界）。
另须复现 `run_log.py:66-72` 的读回容忍：**恰好 1 行**截断尾可容忍，
更早的坏行抛 `ValueError`。

#### E3.d 输出与合同产物

- 输出：`对象 × 边界 × 结果类` 的完整计数表 + 每类一个原始样本。
- **合同结论（这是 E3 真正的产物）**：明确列出在 M1 下**可**充当
  ACK 耐久点的写入形态，与**必须**按 `CRASH_OUTCOME_UNKNOWN` 处理的
  形态。
- **规范性条款**：fsync 是否构成 ACK 合同的耐久保证，由 amendment
  **明示**；`N` 次未观察到失败**不得**反推为保证（M1 的零失败只说明
  该边界在 M1 下未观察到丢失）。
- **可直接复用的仓库先例（本轮取证发现，写进结论供 §2.4b 采纳）**：
  `controller/qualification_protocol.py:605` 的
  `create_once_json(ack_path, ack)` 先落盘、`:624-625` 才切换
  `self.phase = "measurement"`——即**"耐久记录先于副作用"**已是本仓库
  的既有惯例，ACK 账本应照抄该顺序，而不是发明新机制。

**停止/失败规则**：无失败分支——任何结果都是设计输入。
**成本**：约 2 小时脚本 + 分钟级运行。

---

### 3.4 E5 — 事件生成器剂量标定（Unity **诊断 Play**，COORD-005，零配额）

**决定**：VLM-2 的实验地基——遮挡/混淆/停车三类事件能否可靠制造；
`LOST ≥ 2 s` 定义是否匹配 NanoTrack 实际行为。

#### E5.0 遮挡几何的解析前置检查（本稿完成，零成本；**结论改变了 E5 的形状**）

遮挡成立的充要几何条件（闭式，可由冻结字节复算）：机体在
`(a_x, y_d, a_z)`、目标在路线上距机体水平 `D`，则视线仰角
`tan e = y_d / D`；高 `h_occ` 的静止遮挡体要挡住高度 `y_t` 的目标
采样点，其**朝机体一侧近边**与目标的水平退距须满足

```
standoff < (h_occ − y_t) / tan e = (h_occ − y_t) · D / y_d
```

同时走廊合法性要求近边退距 ≥ `target_half_width + clearance_margin`
= `1.5 m`，即**中心**退距 ≥ `1.5 + 遮挡体半深`。取场景内最高可移动
车辆 `Vehicle_Container_*`（足迹 `3.63 × 4.16 × 9.09 m`，顶
`y = 4.15`，半深 `1.815 m`，`config/road_data.json`）与目标顶
`y_t = 1.55`：

| 场景 | 机体高 | 路线上最优 `D` | 最大可行 standoff | 走廊+半深需求 | 判定 | 可行弧长占比 |
|---|---|---|---|---|---|---|
| **SCENE-004** | `25.000001 m` | `17.90 m` @(154.5,118.5) | **`1.862 m`** | `3.315 m` | **INFEASIBLE** | **`0.0000`** |
| **主环线（default）** | `25.2 m` | `69.11 m` @(174.5,62.5) | **`7.131 m`** | `3.315 m` | **FEASIBLE** | `0.6651` |

**结论**：SCENE-004 的环线只有 29 × 5 m、机体距最近边仅 8 m，仰角
54.7°–72.3°，**任何走廊合法的静止车辆都不可能遮挡它**——这不是参数
问题而是构造性不可能。revision 1 把三档遮挡放在 SCENE-004 上是错的。

#### E5.0′ 更正 §E5.0 的量纲错误，并给出可判定的 E5-B 结论（round 3 必修 6）

**先登记一处必须自我更正的错误。** §E5.0 的判定表把"最大可行
standoff"（一个**近边**量）与"走廊 + 半深需求 `3.315 m`"（一个**中心**
量）直接相比。两者量纲不同，该比较无效。**正确的关系是：走廊合法性
与遮挡条件约束的是同一个量——近边退距 `s_near`**：

```
走廊合法：   s_near ≥ target_half_width + clearance_margin = 1.5 m
遮挡目标顶： s_near <  (h − y_t) · D / (y_d − y_t)
```

遮挡体半深 `w` **不出现在这对不等式里**（它约束的是"这个箱子放不放
得下"，不是"挡不挡得住"）。按 §E5.0 的错误比较，SCENE-004 得
`1.862 < 3.315 ⇒ INFEASIBLE`；按正确比较则是
`1.8639 > 1.5 ⇒ 表面可行`——**结论会反转**。因此本节重做全部判定。
（本稿 revision 3 初稿一度把该量纲错误进一步推广成一条"`h − w ≥ y_t +
t_h`"的普遍定理，同样错误，已在提交前自查推翻，逐字记在 §14 的 C7。）

**两个 §E5.0 未纳入的真实约束，本节补上。**

1. **机体静止悬在锚点正上方。**`TetheredScenarioBootstrap.cs:188`
   逐字为 `drone.transform.position = Config.Anchor + Vector3.up *
   Config.drone.initial_altitude_m;`；当前是 body-static 阶段（机体
   运动到 M3′ 才回来），诊断 Play 不跑外部机体控制器，故 `D` 恒为
   **锚点到目标的水平距离**。
2. **云台在 45° 硬饱和。**`TetheredGimbal.cs:37-38` 逐字为
   `float applied = Mathf.Min(requested, maximumOffNadirDeg);`、
   `Saturated = requested > maximumOffNadirDeg + 0.1f;`，两个 scenario
   的 `gimbal.maximum_off_nadir_deg` 与 `ScenarioConfig.cs:59` 都是
   `45.0`。即 `θ = atan(D / y_d)`，不饱和 ⇔ `D / y_d ≤ 1`。

**冻结的可行性判据（三条同时成立）**，对路线上每个目标采样点 `p`：

1. **存在**近边退距 `s_near ∈ [1.5, (h − y_t)·D/(y_d − y_t))`；
2. 该 `s_near` 处的遮挡体矩形（深 `3.627 m` 沿视线、宽 `9.088 m`、
   取**最有利朝向**作为上界）到**路线折线上每一点**的距离 `≥ 1.5 m`；
3. 目标仍在画面内（`θ − min(θ, 45°) ≤ 半 vFOV 30°`）。

判据 2 是 §E5.0 完全遗漏的一条：遮挡体要放进目标与机体之间，需要一条
**`1.5 + 3.627 + 1.5 = 6.627 m` 宽的无走廊空隙**。以 0.25 m 路线步长、
0.05 m 退距步长穷举：

| 场景 | 锚点 | 最大近边可行退距 | 可行弧长占比（在画面内） | 其中**不饱和** |
|---|---|---|---|---|
| **SCENE-004**（现锚点） | `(140, 108)` | `1.8639 m` @`D = 17.9025` | **`0.0000`** | **`0.0000`** |
| **主环线**（现锚点） | `(132, 117)` | `7.1384 m` @`D = 69.1122` | `0.4484` | **`0.0000`** |

**SCENE-004 为什么仍是 `0.0000`（正确的理由）**：判据 1 只留下
`s_near ∈ [1.5, 1.8639]` 这个 **`0.3639 m` 宽**的窗口，而判据 2 要求
`6.627 m` 的无走廊纵深——目标在北段（`z = 121`）时，机体侧正是南北两
条平行路段之间那条**只有 `5.0 m` 宽**的缝隙（`z = 116` 与 `z = 121`）。
`6.627 > 5.0`，箱子放不进去；放在缝外则 `s_near` 超过 `1.8639` 挡不住。
**所以 §E5.0 的结论碰巧对，理由是错的**——它以为是仰角太陡，实际是
路线自身的平行段间距装不下遮挡体。

**主环线为什么可行段全部饱和**：主环线锚点 `(132, 117)` 距北段中心线
（`z = 117.5`）只有 **`0.5 m`**——它本来就在走廊内，这正是
`P1-SCENE-007` 要修的缺陷。近锚点的目标其视线几乎**平行于道路**，
遮挡体只能落在路上，判据 2 全灭；能满足判据 2 的都在远端，而远端
`θ > 45°`。故不饱和可行占比恰为 `0.0000`。

**round 3 必修 6 要求的两个分支，现在都可判定：**

| 分支 | 闭合契约 | 判定 |
|---|---|---|
| **W —— 等 `P1-SCENE-007` 后在 SCENE-004 上跑** | 可执行性完全由 SCENE-007 选定的锚点决定，故本轮把它**穷举掉**：在 `140 ± 40 m × 118.5 ± 40 m` 的 1 m 格点（6561 个）上，筛出满足已接受的 `config/p1-scene-004-anchor-placement.json` 包络合同（`envelope_max_off_nadir_deg 45.0 − envelope_off_nadir_margin_min_deg 5.0 ⇒ 全路线 θ ≤ 40°`；`envelope_max_slant_range_m ≤ 32.0`）的锚点共 **209** 个，对每个重跑上述三条判据 | **`E5B_INFEASIBLE_UNDER_ACCEPTED_ENVELOPE`**——**209 个全部得 `0.0000`**（最佳者 `(135.0, 114.5)`，`maxθ = 38.53°`、`maxslant = 31.96 m`，可行占比仍 `0.0000`）。等 SCENE-007 解锁不了这条臂：**该分支关闭**，不需要用户授权，也不需要再等 |
| **M —— 主环线 `deterministic-loop-default`** | 可行占比 `0.4484`，但**不饱和占比 `0.0000`**；南直段中点 `D = 57.396 m` ⇒ `θ = 66.28°`，越过限位 `21.28°`。目标仍在画面内（画面上界 `D/y_d ≤ 3.7321`，全路线满足），但**每一帧都带 `gimbal_saturated: true`**，斜距约 `62.7 m` | **技术上可执行，但测的不是原定的量**——它测的是"云台饱和态下的遮挡"，而 VLM-2 的遮挡事件合同没有、也不应默认饱和运行；且它还需要 §E5.1 路径 S 的全部协议变更 |

**构思角色的处置（交回 Acceptance）**：据此**撤回 E5-B 作为 Play
实验**，不请求任何主环线授权——按 round 3 必修 6 的要求，只有在分支
本身成立时才该请用户裁量，而现在一条被穷举否掉、一条只在已接受包络
之外成立。E5-B 的产出改为**本节这条零成本的负结果**，并给 §E5.2′
三个可选后继处置。**E5-A（混淆 + 停车）不受本节影响**，留在 SCENE-004。

#### E5.1 真值写出器的选定（round 2 必修 4：正文选定，不延后）

实测两个写出器的字段：

| 写出器 | 字段 | 能否给遮挡实例身份 |
|---|---|---|
| `WriteRate3EvaluationTruth`（`CoverageEvaluator.cs:409-456`） | `geometrically_visible`、truth box、`target_world_x/z_m` | **否**；且仅在 RATE-003 会话释放后写，普通 Play 零输出 |
| **`WriteScoutingTruth`（`:459-497`）** | `target_visible`、**`target_visible_sample_fraction`**、`target_slant_range_m`、`target_bbox_xywh_norm`、`distractors[]`（`distractor_id` = `StableObjectId` + 投影框） | 否（无射线级身份），但**被标记为 distractor 的对象逐帧有投影框** |

**round 3 必修 4 的更正：revision 2 选定的 writer 在 E5 里根本进不去。**
逐字核对 `CoverageEvaluator.ConfigureScouting()`（`:305-372`），
`scoutingTruthWriter` 的创建有五道前置，缺一即不产生任何真值：

| # | 前置（逐行） | 对 E5 的后果 |
|---|---|---|
| 1 | `:311-318` 只 `TryLoad` 两类会话文件：`p1_detect_scouting_session.json`（`P1DetectScoutingSession`）与 `p1_scene_004_scouting_session.json`（`P1Scene004ScoutingSession`）；`:324` 两者都无 ⇒ **`return`** | 不放会话文件 ⇒ **零真值**（这正是路径 Z 依赖的早退分支） |
| 2 | 两个会话类把 `scenario_id` 硬钉死：`P1Scene004Scouting.cs:28` = `p1-scene-004`，`P1DetectScouting.cs` = `p1-detect-scouting`；`:335` 再与 `config.scenario_id` 相等校验 | 主环线 `deterministic-loop-default` **无法**用任何既有会话类载入 ⇒ revision 2 的 E5-B「用既有 writer」自始不成立 |
| 3 | `:338-343` 校验 `config.source_path` 的 SHA-256 == `loaded.ScenarioConfigSha256` | 任何 `runtime/scenario_config.json` 覆盖都会改哈希 ⇒ **覆盖与会话互斥**，必须重算并写进会话文件 |
| 4 | `:346-359` 启动时一次性 `FindObjectsByType<RateStudyDistractor>()` 并与 `scene_adjustments.expected_distractor_count` **相等**校验 | 运行时红色副本若在此之后创建 ⇒ 计数不符 ⇒ 抛 `scouting_distractor_count_mismatch` |
| 5 | `P1DetectScoutingTruthWriter`（`P1DetectScouting.cs:193-212`）在构造函数里 `Directory.CreateDirectory(runtimeRoot / SessionRoot / SessionId / "truth")`，且 `SafeSessionId`（`:109-120`）要求非空 | **必然创建一个 session-ID 命名的目录** ⇒ 与 COORD-005「不创建、不消耗 scenario/session/run ID」直接冲突 |

因此本轮**不再声称"选用既有 writer"**，改为把两条采集路径都写成闭合
契约，由 Acceptance 择一（默认 Z）：

##### 路径 Z（默认；零 ID、零 truth、COORD-005 合规）

**机制**：**不放任何 scouting 会话文件**。`ConfigureScouting()` 在
`:324` 早退，`scoutingTruthWriter == null`，`WriteScoutingTruth()` 在
`:464` 第一行 `if (scoutingTruthWriter == null) return;` 返回，
`scoutingDistractors` 从未赋值也从未被读到。连带后果全部有利：

- **前置 4 不执行** ⇒ 运行时红色副本**不需要**改
  `expected_distractor_count`，也没有"必须早于枚举创建"的时序约束。
  逐处核对该字段的全部读取点：**唯一**把它与场景中实际
  `RateStudyDistractor` 数量比对的是 `CoverageEvaluator.cs:346-359`；
  `ScenarioConfig.cs:297` 只做 `< 0` 的非负校验（与实际计数无关）；
  `Rate3ScoutingTool` / `RateStudyScoutingTool` 是 RATE-002/003 各自的
  scouting 组件，E5-A 的诊断 Play 不挂载它们；其余命中在 Editor 工具
  与 EditMode 测试内。故路径 Z 下该计数校验根本不运行；

  （实现时须**逐条复核**这五处读取点是否仍如此——本条是路径 Z
  成立的支点，代码一变即失效。）
- **前置 3 不执行** ⇒ `runtime/scenario_config.json` 覆盖照常生效；
- 云台不被 `ConfigureScoutingGimbal` 接管，`GimbalCommandReceiver`
  保持启用 ⇒ 测的是**真实跟踪回路**，而不是 truth-directed 云台。
  对 E5 而言这更忠实：VLM-2 要的正是真实回路下的事件可检测性。

**身份与产物**：`work_id = P1-VLM-CAL-001`；`scenario_id` 仍是
`p1-scene-004`（不新建 scenario）；**无 session_id、无 profile_id、
无 run_id、无 qual ID**；写出根为 `runtime/p1-vlm-cal/E5A/`
（gitignored，不进证据链）。

**全部 oracle 改为无真值离线重建**（这是路径 Z 能成立的关键）：

| 需要的量 | 来源（零 truth） |
|---|---|
| 红色副本的逐帧投影框 | 副本是**静止**的，世界位姿由 manifest 冻结；包围盒由 `TargetVisualFactory` 的字面量闭式给出（§E5.3）；相机位姿/内参逐帧取自帧元数据 `camera_position_world_m` / `camera_rotation_xyzw` / `intrinsics_px`。**与 §E1.b‴ 的 `exclude_anchor` 完全同一套投影口径**，复用同一函数 |
| 目标的地面位置 | **不重建**。凡需要目标真实位置的判据一律删除或改写（见 §E5.4）——这是路径 Z 的代价，如实承担 |
| 停车真值时刻 | 诊断脚本**自己发出**停车指令，记录单调钟时刻。这是**指令日志**（本进程做了什么），不是对世界状态的测量；只进离线 scorer，不进 controller、感知输入或对外传感器元数据 |
| tracker 侧观测 | controller 自身的 `runtime/tracking_observation.json` 与 run log，本来就是非真值通道 |

**诚实边界（必须写进证据文件）**：路径 Z 下**没有 `target_visible`**，
因此**无法**做几何可见性归因，也无法计算 `C_track` 类指标；它只能回答
"在真实回路里，这些刺激是否把 tracker 打偏/打丢，以及多快能观察到"。
遮挡臂本来就已被 §E5.0′ 撤回，故这条限制只影响混淆与停车，而两者的
判据（§E5.4）已按无真值重写。

##### 路径 S（新 session / profile / ID —— **协议变更，交回接受角色**）

若 Acceptance 认为必须有 `target_visible` 级真值，则需要下列**每一项**，
本提案**不预设任何一项已获授权**：

1. 新增一个 `IScoutingTruthSession` 实现（新 `schema_version`、新
   `ProfileId`、新 `ExpectedWorkId = P1-VLM-CAL-001`、新
   `RuntimeSessionRoot`）——**新增运行时代码**，进批次 2 复核范围；
2. 若要跑主环线，还须允许 `ExpectedScenarioId = deterministic-loop-default`
   （既有两个会话类都钉死在别的 scenario 上）；
3. 一个 `SafeSessionId` 合法的 **session_id**，并接受它会创建
   `runtime/<root>/<session_id>/truth/` —— 即**放弃 COORD-005 的零-ID
   属性**，须由用户明确批准这次消耗；
4. `expected_distractor_count` 从 `2` 改为 `3`（红色副本计入），且副本
   必须**早于** `CoverageEvaluator.Start()` 创建——由一个受
   `runtime/` 开关文件保护的 `[RuntimeInitializeOnLoadMethod(
   RuntimeInitializeLoadType.BeforeSceneLoad)]` 保证（Unity 保证它先于
   任何 `Awake`/`Start`）；开关文件不存在时整段逻辑 no-op，正式采集
   不受影响；
5. 覆盖后的 `runtime/scenario_config.json` 需重算 SHA-256 并写进会话
   文件的 `scenario_config_sha256`，否则前置 3 抛
   `scouting_scenario_hash_mismatch`。

第 1、2、3 项都改变协议或消耗受控资源，按 CLAUDE.md 属**须先由用户
确认**的范围变更；构思角色只列出，不代为申请。

**遮挡归因 oracle**：随 §E5.0′ 撤回 E5-B 一并**删除**
（`OCCLUDER_ATTRIBUTION_BY_BOX_OVERLAP`、`OCCLUDED_BY_UNKNOWN`、
以及"遮挡体须 `mark_as_distractor: true`"三条均不再适用）。若将来
§E5.2 的处置 (2)(3) 被批准，需重新提案。

**join 与标签互斥（路径 Z 版，冻结）**：controller 逐帧日志（20 Hz）
与**离线投影序列**（同为 20 Hz，逐帧可算，无 2 Hz 节拍限制）按
`frame_id` 内连接；每帧至多一个标签，按序命中即止——
`DUPLICATE_NOT_IN_FRAME`（副本投影框不完全落在 `[0,1]²`）→
`TRACKER_LOST`（controller 报 `ok == False`）→
`MISIDENTIFIED`（tracker 框与副本投影框 IoU ≥ 0.3）→ `OK`。
（路径 S 若被选中，恢复原 2 Hz 真值 join 与 `OUT_OF_FRUSTUM` /
`TRACKER_DRIFT` 标签，本段随之作废。）

#### E5.2 E5-B 遮挡剂量（**已撤回**；几何记录保留，见 §E5.2′）

**遮挡体身份**（取自 `config/scenario.default.json` 已有的
relocation 条目，逐字继承，只改目的地与 distractor 标记）：
`prefab_name = "Vehicle_Container_color01"`、
`original_xz_m = {x: 168.253632, z: 117.146248}`、
`match_tolerance_m = 0.1`、`mark_as_distractor: true`（原为 `false`）。
`Apply` 要求"恰好一个 root 匹配且在容差内"（`SceneVehicleAdjustments.cs:61-71`），
该条件本身即 fail-closed 的身份保证。

**通过段**：主环线**南直段** `(174.5, 62.5) → (125.5, 62.5)`
（长 49.0 m，目标自东向西），中点 `(150.0, 62.5)`，距锚点
`(132.0, 117.0)` 水平 `D = 57.396 m`，仰角 `23.70°`。该段上：
挡住目标**顶**（`y_t = 1.55`）需近边退距 `< 5.922 m`；挡住目标
**底**（`y_t = 0.2`）需 `< 8.997 m`。

**三档（近边退距 → 中心世界坐标）**，方向单位向量为中点指向锚点的
水平单位向量 `(−0.3136, +0.9495)`，中心 = 中点 + 单位向量 ×
(近边退距 + 半深 1.815)：

| 档 | 近边退距 | `new_position_m`（`y` 取 `0.0`） | 预期 | 角色 |
|---|---|---|---|---|
| **D1** | `3.0 m` | `(148.490, 0.0, 67.072)` | 顶与底皆被挡 ⇒ 完全遮挡 | 阳性 |
| **D2** | `7.0 m` | `(147.806, 0.0, 69.144)` | 顶不挡、底挡 ⇒ 部分遮挡 | 分级 |
| **D3** | `10.5 m` | `(146.808, 0.0, 72.168)` | 皆不挡 ⇒ 无遮挡 | **阴性对照** |

`rotation/yaw`：`Apply` **只设 `position`、不改 rotation**
（`SceneVehicleAdjustments.cs:85`），故遮挡体保持其场景原朝向；
该原朝向由 E5 manifest 在 Play 前从场景实测记录并入档（它是被动
观测，不是选择）。若实测朝向使其长轴与南段夹角 > 30°（阴影过短），
记 `E5B_OCCLUDER_ORIENTATION_UNFAVOURABLE` 并回构思角色，
**不得**自行加旋转（那需要 `Apply` 之外的新机制）。

**几何阴影上界**：长轴 9.09 m ÷ 目标 2.0 m/s ≈ `4.55 s`；主环线
一圈 `212.971 / 2.0 ≈ 106.5 s`。每档 ≥ 3 圈 ⇒ 每档 ≥ 3 次通过。

##### E5.2′ 本轮处置：E5-B 撤回为负结果（round 3 必修 6）

上面这套三档退距数值**本身可复算**（本轮独立复现：南段中点
`D = 57.396 m`、挡顶阈值 `5.922 m`、挡底阈值 `8.997 m`），但 §E5.0′
按正确判据重算后，主环线的可行弧长占比是 **`0.4484`**（revision 2 报
`0.6651`，其判据含量纲错误，作废），且**其中不饱和占比为 `0.0000``**
——三档全部落在云台饱和 21.28° 的状态里；分支 W 则被 209 个包络合法
锚点的穷举否掉。故：

- **E5-B 不作为 Play 实验执行**，上表保留为已复算的几何记录，不再
  是执行契约；批次 2 不含 E5-B，也不申请主环线授权或用户诊断 Play。
- **E5-B 的产出 = §E5.0′ 的负结果**：VLM-2 的遮挡事件类**不能**由
  `SceneVehicleAdjustments` 的车辆重定位机制在不饱和云台下制造。
  这是给 `P1-VLM-SCOPE-001` revision 4 的一条硬合同输入。

**三个可选后继处置（列出供 Acceptance 择一或全否，本稿不预取任何一项）**：

| # | 处置 | 代价 | 归属 |
|---|---|---|---|
| **(1)** | **删除遮挡事件类**：VLM-2 只保留混淆与停车两类事件，遮挡改由 `P1-DETECT-001` criterion 4 的困难场景证据承担 | 零 | SCOPE-001 revision 4 自行处理，不需新提案 |
| **(2)** | **E5-C 静态几何普查（零成本、非 Play、零 ID）**：本轮的两条阻断都来自**可重定位车辆**这个机制——退距窗口只有 `0.3639 m`、箱子需要 `6.627 m` 无走廊纵深。既有**建筑**不受此限：它们已经在场上、不需要放进走廊旁的缝隙里，且高得多（`Building Sky_big_color01` 高 `24.802 m`），近边退距窗口随 `h − y_t` 线性放大。但**它们的世界摆位不在任何冻结工件里**（`road_data.json` 只有局部足迹），故只能在 Editor 里查。E5-C = 一个 Editor-only、不进 Play 的场景查询：枚举建筑/静态障碍的世界包围盒，对两条路线逐点跑 §E5.0′ 的三条判据，输出"是否存在包络合法锚点使某路段被既有建筑不饱和遮挡" | 一个 Editor 脚本；无 Play、无 ID、无配额 | 需 Acceptance 明确纳入范围后才写；本稿只登记该路径存在，**不预判其结果** |
| **(3)** | **接受饱和态遮挡**：在主环线跑 E5-B，并把"遮挡事件恒伴随 `gimbal_saturated = true`、斜距约 62.7 m、目标约 20–30 px"写进 VLM-2 的事件定义 | 需路径 S 的全部协议变更 + 用户授权 + 承认测量在已接受包络之外 | 须用户确认的范围变更 |

构思角色的建议是 **(2) 优先、(1) 兜底**：(2) 用零成本手段回答"遮挡能
不能在合同内制造"这个真问题，(1) 在 (2) 为空时是诚实的收缩；(3) 会把
一个已知混杂因子写进论文主张，不建议。

#### E5.3 E5-A 混淆与停车（SCENE-004，全部数值冻结）

**混淆体 C1 —— 运行时红色副本（不重定位任何城市车辆）**：无红族
车辆在冻结 survey 的 10 辆近车内，故混淆体改用
**`TargetVisualFactory.AddTargetVisual`**（`:71`，public static，
即目标自身的生产构造源）在 Play 期构造一个 `new GameObject` 红色
副本——**外观与目标逐字节同源**，是最强的外观混淆，且与目标本身
一样是 runtime-only 对象（`TetheredScenarioBootstrap.cs:245` 先例），
零场景字节。副本挂 `RateStudyDistractor` 标记以获得真值框。

**位置（round 3 必修 5：revision 2 的 `(140.0, 0.2, 123.0)` 是错的，
副本半个身子在走廊里）**。revision 2 只按"路线外侧 2.0 m"取中心，
没有减去副本自身的**沿 z 半展 2.0 m**。用 `TargetVisualFactory` 的
字面量闭式算包围盒（`AddTargetVisual` 对 `SetParent(parent, false)`
后显式写 local TRS，故与父变换无关）：

| 部件 | localPosition | localScale | 局部 AABB |
|---|---|---|---|
| body（`:73-77`） | `(0, 0.5, 0)` | `(2, 1, 4)` | `x∈[−1,1]`, `y∈[0,1]`, `z∈[−2,2]` |
| roof（`:78-82`） | `(0, 1.2, −0.2)` | `(1.7, 0.7, 2)` | `x∈[−0.85,0.85]`, `y∈[0.85,1.55]`, `z∈[−1.2,0.8]` |
| **并集** | — | — | **`x∈[−1,1]`, `y∈[0,1.55]`, `z∈[−2,2]`** |

（并集高度 `1.55` 与 `route_corridor.target_height_m = 1.55` 一致，
互为交叉验证。）`Quaternion.identity` 下副本在 `(140.0, 0.2, 123.0)`
的世界 z 跨度是 **`[121.0, 125.0]`**，而北段路线中心线恰在 `z = 121`，
走廊为 `[119.5, 122.5]`——**副本压在中心线上，侵入走廊 1.5 m**。

**冻结的更正位置：`(140.0, 0.2, 125.0)`**，`Quaternion.identity`，静止。
逐点 route sweep（六段闭合折线、0.05 m 步长、AABB-到-折线的最小距离）
实测：

| 候选中心 z | 副本 z 跨度 | 到路线最小间距 | 走廊 `1.5 m` |
|---|---|---|---|
| `123.0`（revision 2） | `[121.0, 125.0]` | **`0.0000 m`** | **违反** |
| `124.5`（临界） | `[122.5, 126.5]` | `1.5000 m` | 恰好相切 |
| **`125.0`（本稿冻结）** | **`[123.0, 127.0]`** | **`2.0000 m`** | **满足，余量 `0.5 m`** |

工件必须复现这三行；实现者不得改中心值。**未在离线可验证范围内的
一件事，如实登记**：该处是否被既有场景物体占据，无法从
`config/road_data.json` 判定（该文件只有各 prefab 的**局部**足迹，
没有世界摆位）。故 §4.2 的 COORD-005 人眼保真检查**必须**覆盖这一点；
目检发现副本与既有物体互穿 ⇒ `E5A_DUPLICATE_PLACEMENT_OCCUPIED`
硬停并回构思角色重选 `x`（沿 `z = 125.0` 平移，不改 z）。

**停车 S1**：经既有 `LoopTargetVehicle.SetMotionEnabled(false)`
（`:35-38`）停 **`20.0 s`** 后恢复，重复 `≥ 2` 次，两次间隔 ≥ 1 圈。
停车时长由 `12.0 s` 提高到 `20.0 s` 是 §E5.4 时间门修正的连带要求
（检出上限 `4.0 s` + 观察窗 `2.0 s` + 恢复前的稳定余量）。
触发条件改为**不依赖目标真值**：诊断脚本按自身单调钟在 Play 开始后
的两个冻结时刻发令（`t = 45.0 s` 与 `t = 120.0 s`），并把
`(命令, 单调钟时刻)` 写入诊断指令日志。SCENE-004 一圈
`62.142136 / 2.0 = 31.0711 s`（`Step()` 在距路点 `< 0.5 m` 时切换
路点，最多每路点少走 `0.5 m`，六个路点 ⇒ 实际圈时落在
`[29.5711, 31.0711] s`），故两次发令必然跨圈，满足"间隔 ≥ 1 圈"。

**初始化帧/框（round 2 必修 4：离线预选并哈希，运行时不读 truth）**：
**round 3 必修 5 的更正：revision 2 的选框规则仍然是从 truth 取框。**
接受角色的判断成立——"离线预选"只改变了**读 truth 的时刻**，没有改变
**框的数据来源**；`target_box_status == "VALID"` 与 `target_bbox_xywh_norm`
都出自 evaluator 真值，把它交给 tracker 初始化就是让真值进入感知链，
无论中间隔了多少道哈希。而且在路径 Z 下**根本没有 truth 文件**，该
规则连字面上都执行不了。

**冻结的替代规则（零 truth）**：初始框来自**人眼确认的图像标注**，与
`P1-DETECT-001` qual-3 的既有做法同源（该次 Attempt 3 用的正是用户
确认的无真值像素框 `(353, 82, 72, 44)`，见状态板 2026-07-31 条目）：

1. `E5_SEED_RUN`（诊断 Play，零 ID、不计 trial）只产出帧图像，**不产
   出任何真值**；
2. 由用户或当轮发令角色在 `frame_id` 最小、目标清晰可辨的那一帧上
   **目视**给出像素框，记录 `(frame_id, x, y, w, h)` 与确认人；
3. 该像素框按 `640×480` 归一化后写入 E5 manifest 并记 SHA-256；
4. 正式 trial **只读 manifest**；离线 scorer 与运行时**两侧都不读
   truth**（路径 Z 下也无 truth 可读）。

这条规则同时兼作 COORD-005 人眼保真检查的样帧之一（§4.2）。
`min(w,h) ≥ 0.06` 保留为**对人工框的合法性校验**（不满足即换帧重标），
不再是从真值集合里筛选的谓词。

#### E5.4 逐事件类的门（round 3 必修 5 重写：无真值、时间门可达）

遮挡两行随 §E5.0′/§E5.2′ **删除**（连同
`E5B_NEGATIVE_CONTROL_CONTAMINATED`）。剩下两类按路径 Z 重写。

**先说明为什么停车判据必须换观测量。** revision 2 用"观测框中心 10 s
内位移 < 0.02（归一化）"判停。这在本项目里近乎失效：云台**一直在指向
目标**（路径 Z 下由 controller 的 `gimbal_command.json` 驱动，路径 S 下
由 `LookAtWorld` 驱动），目标因此被稳定保持在画幅中央——**行驶与停车
的图像位移都接近 0**，该规则的判别力来自跟踪残差而非目标运动。
其次，它与检出上限自相矛盾：要求先观察连续 `10 s` 才判停，最早判定
时刻就是 `t_stop + 10 s`，而成功上限是 `4.0 s`，**任何 trial 都不可能
通过**——接受角色的这条指认成立。

**冻结的替代观测量：LOS 地面交点位移（米域）。** 用 controller 自己的
观测框中心 + 该帧元数据的相机位姿/内参，做一次针孔反投影并与冻结地平面
`y = 0.2 m` 求交（该常数取自已接受的
`config/p1-scene-004-anchor-placement.json` 的 `target_plane_y_m`，是
**冻结场景常量，不是目标真值**；与设计"M2a LOS 地理定位必须显式给出
有限地平面标定、不得由目标路线真值推断"的约束一致）。得到逐帧地面点
`p̂(t)`。目标以 `2.0 m/s` 行驶时 `p̂` 每 `2.0 s` 走 `4.0 m`，停车时只剩
估计噪声——判别力回到米域。

| 事件类 | 分母 | 判据（全部无真值） | 终态 |
|---|---|---|---|
| **混淆 C1** | **副本投影框完整在画面内**的帧数（离线由冻结位姿 + 帧元数据算出，见 §E5.1 路径 Z；要求框完全落在 `[0,1]²` 且 `min(w,h) ≥ 0.02`） | tracker 发布框与**副本投影框** IoU `≥ 0.3` 的帧记 `MISIDENTIFIED`。**不再需要目标真值框**：副本是静止的、永远不是目标，tracker 落在它身上本身即误认。报告 `误认率 = MISIDENTIFIED / 分母` 与 Wilson 95% 区间 | 误认率 `≥ 0.05` ⇒ `CONFUSION_EVENT_GENERATOR_VIABLE`；`< 0.05` ⇒ `CONFUSION_DOSE_INSUFFICIENT`（回构思角色调间距，不改判据） |
| **停车 S1** | 停车次数（`= 2`）／行驶帧数（误报分母） | 判停规则：`p̄(t)` = 以 `t` 为右端、长 `0.5 s` 的窗内 `p̂` 的算术平均；当 `‖p̄(t) − p̄(t − W)‖ < d_thr` 时判"已停"，`W = 2.0 s`、`d_thr = 1.0 m`。检测延迟 = 首次判停时刻 − **指令日志**中的停车发令时刻（§E5.3）。误报 = 行驶期间出现的判停帧数 / 行驶帧数 | 两次均在 `≤ 4.0 s` 内检出**且**误报率 `≤ 0.02` ⇒ `STOP_DETECTABLE`；否则 `STOP_NOT_DETECTABLE_BY_LOS_RULE`（如实报告：VLM-2 的 `TARGET_STOPPED` 事件必须改由别的信号定义） |

**时间门可达性证明（本轮实测复算，round 3 必修 5 的核心）**：

- **最早判定时刻 = `t_stop + W = t_stop + 2.0 s`**，`< 4.0 s` 上限，
  留 `2.0 s` 余量吸收 0.5 s 平均窗与帧节拍 ⇒ 成功终态**可达**；
- **行驶期不会误判**：沿 SCENE-004 闭合路线以 0.01 m 步长滑窗，
  任意 `4.0 m` 弧长（= `W × 2.0 m/s`）两端点的**直线距离**最小值为
  **`2.8329 m`**（出现在 `(154.5,118.5)` / `(125.5,118.5)` 两个折角）。
  `2.8329 / 1.0 = 2.83` 倍余量 ⇒ `d_thr = 1.0 m` 在几何上不会把转弯
  误判为停车；
- **停车时长 `20.0 s` > 检出上限 `4.0 s` + 窗 `2.0 s`** ⇒ 判定窗完整
  落在停车段内，不跨越恢复时刻。

**噪声的诚实处置**：`p̂` 的噪声由观测框抖动经反投影放大，其量级本轮
**未实测**（需要真实 Play 数据）。因此 `d_thr = 1.0 m` 是**预注册值
而非已验证值**：若实测误报率 > `0.02`，终态即
`STOP_NOT_DETECTABLE_BY_LOS_RULE`，**禁止**看过结果再调 `W`/`d_thr`
重测（那正是 §3.0 规则 4 的揭盲后调参）。工件必须同时报告停车段与
行驶段各自的 `‖p̄(t) − p̄(t−W)‖` 分布，供下一轮重设计使用。

**总终态**：两类全部达标 ⇒ `EVENT_GENERATOR_VIABLE_CONFUSION_AND_STOP`
（**注意措辞收窄**：遮挡类未测，不得声称"事件生成器整体可行"）；
任一不达标 ⇒ 对应的具名终态如实报告，VLM-2 的该事件类回构思重设计。
遮挡类的结论固定为 §E5.0′ 的负结果。

#### E5.5 字节边界（硬性，Play 前后取证）

- **`config/` 与 `Assets/` 零字节改动**：Play 前后对 `config/**`、
  `Assets/TetheredTracking/**` 与 `*.unity` 场景文件各取 SHA-256
  清单，前后逐条相同并入证据。
- **本轮 E5 不做任何车辆重定位**：遮挡臂已撤回（§E5.2′），混淆体是
  runtime-only 红色副本，故 `runtime/scenario_config.json` 的
  `vehicle_relocations` 与 `expected_distractor_count` **一个字节都不改**。
  该覆盖文件仍在实验前后各存档一份并比对（若最终为零改动，比对结果
  即"前后逐字节相同"，一并入证）。
- Unity 退出一律 **Don't Save**；项目内
  `SaveScene/PrefabUtility/AssetDatabase.Create` 零命中，故不存在隐式
  持久化路径。红色副本与目标同为 runtime-only 对象。
- **零 ID/配额（路径 Z 的硬属性）**：不放 scouting 会话文件 ⇒
  `ConfigureScouting()` 在 `CoverageEvaluator.cs:324` 早退 ⇒
  **不创建 session 目录、不消耗 scenario/session/run/qual ID、不写
  任何 truth 文件**。产物只落 `runtime/p1-vlm-cal/E5A/`，不进证据链。
  （若 Acceptance 改选路径 S，本条**作废**：路径 S 必然创建一个
  `SafeSessionId` 命名的 truth 目录，须先取得用户对该次消耗的批准。）
- **必须披露的风险**：SCENE-004 的
  `enable_dynamic_intersection_audit` / `enable_jump_diagnostic`
  均为 `false`，故红色副本的放置**不会触发任何动态审计告警**——这既是
  实验可行的原因，也使人眼目检成为 E5 的必要环节而非形式（§4.2 的
  COORD-005 门），并且是 §E5.3 中"副本落点是否被既有物体占据"这一
  离线不可判定项的唯一把关手段。两个开关值仍逐一记入 manifest。

**成本（round 3 后重估）**：脚本约一天；用户诊断 Play 会话
——**只剩 E5-A**：一次 `E5_SEED_RUN`（出图 + 人工标初始框，约 10 分钟）
＋ 一次正式诊断 Play（两次停车 + 若干圈混淆，约 20 分钟）。
E5-B 已撤回，**不占用任何 Play 时间**（§E5.2′）。

### 3.5 E4 — 教师 API 实测（**待 Q1 授权**；round 1 必修 6 的绑定）

#### E4.a 协议绑定与冲突优先级

E4 的协议 = `P1-VLM-SCOPE-001` 的 V1 验收条件，**其正文逐字复制于
下方 E4.c**，并三重绑定：源文件
`docs/proposals/P1-VLM-SCOPE-001-vlm-interactive-recharter.md`
SHA-256 `08afbd4e…cb68b`（revision 3 当期）、行范围 **532–571**、
该块自身 SHA-256 `caff93be…58ba`。

**冲突优先级（冻结）**：SCOPE-001 当前整体仍为 `REVISION_REQUESTED`，
其 revision 4 可能改动 V1。因此——本提案 §3.5 的复制件是 E4 **执行时
的唯一权威**；若 SCOPE-001 revision 4 起 V1 文本或上述任一哈希发生
变化，**E4 自动回到未裁定状态**，须经新一轮 Acceptance 裁定确认新
文本后方可执行。**禁止**按"可变章节引用"执行。

#### E4.b 本轮实测发现的两处 V1 阻断（登记，不自行修改 SCOPE-001）

| # | V1 文本 | 实测事实 | 处置 |
|---|---|---|---|
| **V1-B1** | 评分"读 `evaluation_truth.jsonl`" | 该文件全仓库零实例（§0 C1） | E4 执行前须由 SCOPE-001 revision 4 或独立 amendment 把评分真值改为实际存在的 scouting/probe schema；**未改前 E4 不可执行** |
| **V1-B2** | 帧清单来源含 `runtime/runs/p1-track-{follow,nadir,occlusion}`、`rs2-*` 归档、qual-3 会话 | 实测：三个 `p1-track-*` 目录**只有遥测 jsonl/manifest/metrics/summary，零帧**；`runtime/rate-study/*/rs2-*` 与 `runtime/test-results/*qual-3*` **零匹配**。五个声明来源族中只有 `p1-detect-scouting`、`p1-scene-004-scouting` 真实存在 | 18 层硬停规则（V1 自身条款）会在 manifest 构建期立即触发；来源清单须按 §3.0 的实测表重列。同样须经 SCOPE-001 修订或 amendment |

**这两条正是"先测量"的直接收益**：若不做本轮清点，Q1 预算会被花在
一个 manifest 根本构建不出来的 spike 上。

#### E4.c V1 协议正文（逐字复制，见 §E4.a 的绑定与优先级）

> 1. **V1 grounding spike（round 1 必修 6：全要素在任何 API 调用前
>    冻结）**：
>    - **帧清单**：来源目录冻结为 `runtime/runs/p1-track-{follow,nadir,
>      occlusion}`、`runtime/rate-study` 归档 `rs2-*`、qual-3 会话、
>      `runtime/p1-detect-scouting`、`runtime/p1-scene-004-scouting`；
>      分层 = 斜距三带（<30 / 30–50 / >50 m）× 状态（正常 / 遮挡中或
>      解除后 / 干扰共存）× 场景（主环线 / SCENE-004）；总数 ≥ 30、
>      每 run ≤ 8 帧、同 run 相邻采样间隔 ≥ 2 s、`frame_id` 全局唯一；
>      清单（路径 + SHA-256 + 分层标签）作为 immutable manifest 先行
>      提交，manifest 提交后一字节不得改。
>    - **教师与调用参数（round 2 必修 6）**：教师 =
>      `TEACHER_MODEL_ID_TBD_Q1`——Q1 授权时绑定**供应商当时公开、
>      本账户实际可调用的版本化 API model ID 及其价格**，不预注册
>      未核实别名；调用时记录 API 返回的精确 model version 字符串。
>      system prompt 全文冻结入 manifest（含"仿真域方块车"说明）并记
>      SHA-256；`temperature = 0`；图像按原始 640×480 JPEG 直传不缩放；
>      输出为冻结 JSON schema `{bbox_norm, confidence, not_visible}`。
>    - **分层规则（round 3 必修 4：硬停，无"缺层继续"路径）**：18 个
>      声明分层（3 距离带 × 3 状态 × 2 场景）**每层最小 1 帧**；
>      manifest 构建时（任何 API 调用前）若任一声明层可用帧数为 0 ⇒
>      **硬停**，二选一后重来：(a) 扩大冻结来源目录清单并重新冻结
>      manifest；(b) 以新一轮 Acceptance 裁定显式缩窄 spike 目标总体
>      （删层并同步修改覆盖主张）。不存在一边缺层一边维持 18 层覆盖
>      主张的路径；可用层合计仍须 ≥ 30 帧。
>    - **记账**：解析失败/超时/超 schema = 失败样本，重试上限 1；
>      全部原始响应存档。**预算耗尽规则**：40 次上限耗尽时，manifest
>      中未处理样本一律计失败并入分母（不得截断分母美化成功率）。
>    - **延迟校准测量（供 §2.4a 冻结门定值；round 3 必修 4 统一预算
>      措辞：全部计入 ≤ 40 次总上限）**：每次调用逐条记录端到端延迟
>      （请求发出 → 解析完成，单调钟），另以 ≤ 6 次调用跑 2–3 轮
>      模拟协商负载的延迟样本；输出 p50/p95/max 分布，按 §2.4a 冻结
>      公式导出三值候选（数值经 amendment 裁定 + 用户逐字授权后
>      生效）。
>    - **评分**：离线 scorer 读 `evaluation_truth.jsonl`（§2.2 允许的
>      唯一场合之一），报告 IoU@0.5 成功率点估计 + Wilson 95% 区间 +
>      逐分层分解；**通过线 70%（总体）在此预注册**，看结果前的修改
>      只能经新一轮裁定。
>    - **H2 对照**：同一 manifest 帧集跑 YOLOE 文本 prompt
>      （冻结短语集 `{"red car","white car","vehicle"}`）报告召回。
>    - **预算**：教师调用 ≤ 40 次；执行前须用户 Q1 逐字授权。

#### E4.d E4b 删除（round 1 必修 6）

revision 0 的"E4b 可选小额（≤ 5 次事件前后帧对 → VLM 描述）"**整体
删除**：它允许在看过前序结果后再决定是否花预算，构成结果条件性支出。
report 能力的方向性验证若确有必要，须以独立预注册 manifest 另案提出。

---

## 4. 与现行体系的兼容性 / 批次与门

### 4.1 兼容性

- 不改设计基线、不改 `P1-VLM-SCOPE-001` 文本（其 round 4 五条必修
  保留待答；校准数据到位后 revision 4 一并回应并引用本包工件）。
  §3.5 E4.b 的两处发现**只登记不自改**。
- 真值边界：scouting/probe 真值只在**离线** scorer/合成器中使用
  （先例：spike scorer / distillation verifier）；E5 诊断产物按
  COORD-005 不进证据链；校准工件整体标注"工程校准数据"。
- 单线纪律：本提案是唯一活跃轨。

### 4.2 批次、停点与复核（round 1 必修 6）

```
批次 1  S1 工具态：E1–E3 脚本 + manifest builder + E1 网格定义（零测量、零 manifest）
        → Acceptance 写入归因 + 停点 1 → 独立 Review（一次性 worktree）
        → S2 清单态：用已复核的 builder 产出并提交 config/p1-vlm-cal-manifest.json
          （仍零测量结果；builder 一改即回 S1）
        → S3 测量态：E1 T 组拟合 → config/p1-vlm-cal-e1-hsv.json create-once 冻结
          → Q 组揭盲 → E2/E3 测量 → 结果交回 Acceptance
批次 2  E5-A 工具（Editor 诊断脚本 + 运行时红色副本构造 + 静态物投影器 + LOS 停车 scorer）
        → 停点 2 → 独立 Review
        → COORD-005 人眼保真检查（≥2 张样帧：副本外观与目标一致、副本落点无互穿）
        → E5_SEED_RUN（零 ID、只出图；人工标初始框）→ manifest 冻结初始框
        → 通过后才可请求用户正式诊断 Play（**仅 E5-A**；E5-B 已按 §E5.2′ 撤回）
E4      待 SCOPE-001 修好 V1-B1/B2 + 用户 Q1 逐字授权后单独成批
```

**串行状态的硬性约束（round 2 必修 6）**：S1→S2→S3 单向不可逆；
`config/p1-vlm-cal-e1-hsv.json` 为 **create-once**（存在即拒写）；
Q 组揭盲后任何参数改动使该实验作废；S3 结果在**新一轮 Acceptance
归因**之前不得用于恢复 `P1-VLM-SCOPE-001` revision 4。

**新增工具清单（复核范围；round 3 必修 3/4/5 后重列，共 8 项）**：

| # | 工具 | 批次 | 本轮变化 |
|---|---|---|---|
| 1 | manifest builder | 1 | 路径规范改 repo-relative；新增 `frame_*.json` 白名单 |
| 2 | `e1_color_control.py` | 1 | `target_box_status` 分 schema 判定 |
| 3 | `e2_replay_bench.py` | 1 | 真实配置键、冻结源框、注入生效回读、两个 p95 的闭式估计 |
| 4 | `e3_crash_inject.py` | 1 | 边界改逐对象命名；新增 W4 行；R7 改断言 |
| 5 | `atomicfile_transcription.py`（明标转写） | 1 | 不变 |
| 6 | E5-A Editor 诊断脚本（含运行时红色副本构造 + 停车发令与**指令日志**） | 2 | 不再需要 `RateStudyDistractor` 标记与 distractor 计数改动（路径 Z） |
| 7 | **静态物离线投影器**（冻结世界 AABB × 帧元数据 → 归一化框） | 2 | **本轮新增**；与 §E1.b‴ 的 `exclude_anchor` 共用同一投影实现，两处必须调同一函数 |
| 8 | **E5-A 离线 scorer**（LOS 地面点重建 + 混淆/停车判据） | 2 | 取代原"离线归因合成器"（遮挡归因随 E5-B 撤回而删除） |

第 7 项与 §E1.b‴ 复用同一投影函数，是**刻意的**：两处若各写一份，
E1 的锚点剔除与 E5 的副本框就会在同一台相机上给出不一致的像素坐标，
复核无法交叉验证。该共用关系入复核范围。

- **撤回 revision 0 的轻量复核减免请求**：接受角色指出校准工具本身
  就是参数冻结的依据，测量仪器错则全部数据作废（F23 先例）。复核
  范围为**完整**：真实代码、采样隔离（T/Q 组不重叠、HSV 冻结先于
  揭盲）、计时路径（是否真的走 `_catch_up`）、故障注入边界、真值
  边界（在线侧零 truth）。不接受只看汇总 Markdown。
- 角色边界：脚本由实现角色编写执行；构思不写代码；接受角色对每批
  工件做停点确认与写入归因。

---

## 5. 可证伪的验收条件

1. **输入门**：任何测量开始前，`p1-vlm-cal-manifest/v1` 已提交且
   消费端严格校验通过；`runtime/frames` 不在任何 manifest 中；
   缺件/样本不足按 §3.0 具名终态硬停。
2. **E1 隔离**：T 与 Q1 帧 ID 集合交集为空；`config/p1-vlm-cal-e1-hsv.json`
   的 SHA-256 在任何 Q 组评测之前入档；揭盲后零改动。
3. **E1 判定**：逐色分母、四类计数、逐色点估计与 Wilson 区间齐备；
   Q2/Q3 分层结果单列且不参与门。
4. **E2 路径**：工件证明测量确实经过 `ReanchorRuntime._catch_up`
   （记录每次 `_catch_up` 内的 `replay_tracker` 调用次数与头帧推进
   轮次）；四个模型 SHA-256 与 `cv2.__version__ == "5.0.0"` 已断言；
   五档 × 60 起点 × 冷热分列；失败样本计入分母。**注入生效值已回读
   并与 §3.2.c 表逐项相符**（键为 `maximum_result_age_s`）；
   `source_box_norm` 全程为 manifest 中那一个字面量；握手轮数恒为 2
   （任一次 ≠2 即整实验硬停）；`p95_fixed_ms` / `p95_per_frame_ms`
   可由工件中的 `(N_j, y_j)` 列表逐位复算。
5. **E3 分层**：M1/M2 分离声明；**每个对象的边界表与其真实语句序列
   逐条对应**（不套统一模板），每格 20 次，总注入数 = 780 且与逐格
   数量之和一致；`create_once_bytes` 的 overwrite 初态以两条 preflight
   断言呈现而**非** kill 格，`os.link` 撞名分支显式记
   `NOT_EXERCISED_SINGLE_PROCESS`；四维正交结果向量齐备；C1 的
   Python 复刻**逐字标注为转写模型**；外部平台事实单列。
6. **E5 冻结**：E5-A 的全部数值（副本世界位姿 `(140.0, 0.2, 125.0)`、
   停车时长 `20.0 s`、发令时刻、`W = 2.0 s`、`d_thr = 1.0 m`、
   检出上限 `4.0 s`、误报上限 `0.02`）与本提案一致；route sweep 的
   三行间距复算复现；`config/` 与 `Assets/` 前后 SHA-256 清单逐条相同；
   **无 scenario/session/run/qual ID 创建或消耗**；**在线与离线两侧
   都零 truth**（初始框来自人工标注，副本框来自冻结几何投影）；
   E5-B 未执行，其结论为 §E5.0′ 的负结果。
7. **E4 绑定**：执行前 SCOPE-001 的文件与块 SHA-256 与 §3.5 记录
   一致，或已经新一轮裁定确认新文本；V1-B1/B2 已由 SCOPE-001 侧
   闭合。
8. **失败如实**：任何具名终态（`COLOR_CONTROL_INFEASIBLE_<COLOR>` /
   `CAL_E1_UNKNOWN_BOX_STATUS` / `E2_CATCHUP_EXCEEDS_CONTRACT_BOUND` /
   `E2_TIER_UNSTABLE` / `E2_INJECTION_NOT_IN_EFFECT` /
   `E2_HANDSHAKE_INVARIANT_VIOLATED` / `E2_LINEAR_MODEL_REJECTED` /
   `E2_EXCEEDS_PRODUCTION_WORKER_TIMEOUT` /
   `E5B_INFEASIBLE_UNDER_ACCEPTED_ENVELOPE` /
   `E5A_DUPLICATE_PLACEMENT_OCCUPIED` /
   `STOP_NOT_DETECTABLE_BY_LOS_RULE` / `CONFUSION_DOSE_INSUFFICIENT` /
   `CAL_INPUT_*`）如实报告并回指对应合同条款，不得为通过而放宽判据。
9. **措辞收窄**：遮挡类未测，任何工件与 amendment 都不得出现
   "事件生成器整体可行"这类断言；总终态只能是
   `EVENT_GENERATOR_VIABLE_CONFUSION_AND_STOP`。

---

## 6. 失败模式与资源

- **校准推翻已冻结结构**（E5 最可能，E1 次之）：这是收益不是风险——
  回构思修合同，比实现后翻车便宜一个数量级。本稿 §0 的 C1–C4 与
  §14 的 C5–C7 已经是这条收益在提案层面的三次兑现，其中 C7 更是在
  **一行代码都还没写、一次 Play 都还没跑之前**就砍掉了整条实验臂。
- **零成本的解析前置检查回报最高**（本轮实证）：§E5.0′ 用一个读冻结
  JSON 的脚本，替代了原本要用一次用户诊断 Play 才会发现"测的是饱和态
  遮挡"的路径。后续任何涉及几何/限位的实验，**先做闭式可行性再排期**
  应作为本包的固定次序。
- **同族隔离偏弱**（E1，已披露）：缓解是 HSV 冻结先于 VLM-2 正式
  run；若 amendment 要求同族独立资格集，须另行采集。
- **E5-A 的 Play 依赖用户时间**：`E5_SEED_RUN` + 一次正式诊断，失败
  仅意味着换配置重来，零配额损失。
- **路径 Z 的信息代价（已披露，非风险而是取舍）**：无 `target_visible`
  ⇒ 不能做几何可见性归因、不能算 `C_track` 类指标。若 Acceptance 认为
  必须有，改走路径 S，代价是放弃零-ID 属性并需用户批准（§E5.1）。
- **资源**：E1–E3 纯本地零消耗（须在 `.venv-track` 下运行）；E5-A 两次
  用户辅助诊断会话；E4 在 Q1 预算内且另有前置；无任何正式
  ID/配额/场景字节。

---

## 7. 建议但不强制的实现范围

与 §4.2 的 8 项工具清单一一对应：

- 批次 1：`tools/vlm_calibration/manifest_builder.py`、
  `e1_color_control.py`、`e2_replay_bench.py`、`e3_crash_inject.py`
  （含 `atomicfile_transcription.py` 明标转写）；
- 批次 2：`tools/vlm_calibration/static_projector.py`（静态物离线
  投影器，**与 E1 的 `exclude_anchor` 共用同一投影实现**）、
  `e5a_offline_scorer.py`（LOS 地面点重建 + 混淆/停车判据）
  + `Assets/TetheredTracking/Editor/P1VlmCalEventDoseDiagnostic.cs`
  （含运行时红色副本构造与停车发令/指令日志）；
- 产物：`config/p1-vlm-cal-manifest.json`、
  `config/p1-vlm-cal-e1-hsv.json`；
  `docs/evidence/P1-VLM-CAL-001-{e1,e2,e3,e5a}.md`。

原 `e5_offline_attribution.py` 随 E5-B 撤回而删除（遮挡归因 oracle
已不适用）；E5 证据文件名相应由 `e5` 改为 `e5a`。

---

## 8. 本提案自身的边界声明

不实现任何代码、不运行任何实验、不调 API、不消耗 ID/配额、不修改
`P1-VLM-SCOPE-001` 与设计基线、不自行标记 `ACCEPTED`。§0 的实测勘误
（C1–C4）、§14 的实测勘误（C5–C7）与 §3.5 的 V1 阻断均为**登记**，
其修订归 SCOPE-001 自身的轮次。**本轮读取磁盘并离线复算属提案取证，
不创建也不消耗任何 scenario/session/run/qual ID，不写 `config/`、
`Assets/` 或 `runtime/` 任何字节。** 提交后交接受角色 round 4 裁定。

---

## 9. Acceptance review decision

### Acceptance round 1 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

“先测量、后定合同”的方向成立，也与用户在授权账本中的原话一致。E1、E2、
E3、E5 分别对应 SCOPE-001 round 4 的真实缺口，失败分支不伪装成成功、
不把校准工件冒充研究证据、E4 继续等待 Q1，这些边界均应保留。当前不能
接受的原因不是实验价值不足，而是 revision 0 仍把多项预注册决定留给了
实现角色，按字面执行会产生多种都“符合提案”却不可比较的实验。

首先，输入可用性尚未成立。当前工作树的 `runtime/` 只有 `README.md`，
没有提案声称要读取的帧、run、truth 或 NanoTrack 模型；这不证明用户侧
归档不存在，但意味着接受时无法核实 E1 的三种颜色标签与两组各 30 帧、
或 E2 的连续 75 帧和真实模型依赖。E1 也没有说明颜色标签从何而来、
三色各自的样本量和 90% 是逐色还是汇总门；“红色一带”还没有处理 HSV
色相环回绕。允许在看到资格结果后再“扩大来源清单重冻结”会打开换样本
求通过的通道。

其次，E2 尚未唯一指向生产追赶行为。真实路径是
`ReanchorRuntime._catch_up()` 在 live head 推进时反复 snapshot，并可能从
同一 source 重新执行 factory + init + replay，直至抓住静止 head；一次
`replay_tracker()` 加两轮笼统“注入”并不唯一等价。revision 0 也未冻结
并发推进器、冷/热启动、失败样本记账，以及三个 age 档如何导出唯一的
`catchup_cand`，会使 p95 对实现方式敏感。

第三，E3 把 `kill -9` 后可读与“真的落盘”混为一谈。SIGKILL 只杀子进程，
内核与页缓存仍存活；它可测进程崩溃窗口，不能单独证明掉电/内核崩溃耐久。
仓库的 C# `AtomicFile` 是 `WriteAllText` 后 `File.Move/File.Replace`，没有
显式 file/directory fsync；Python `RunLogger.append()` 只 flush，close 才
fsync。必须先冻结故障模型，并分别测真实实现；AtomicFile 的首次创建与
覆盖替换、旧值/新值/缺失/临时文件，及 JSONL 的完整行/截断尾/重复都不能
被“存活/丢失/半行”三类吞掉。零次观察到失败也只能形成该注入模型下的
经验结果，不能自动升级为持久化保证。

第四，E5 的三组相对速度/间距没有给值，`reliably` 没有机械判据，场景、
目标/干扰物身份、初态、reset 和每次观察窗也未冻结。“逐帧归因”若包含
`OCCLUDED_BY_*` 或 `TRACKER_DRIFT` 必然消费 evaluator truth/身份判定，
只能在与 controller/perception 隔离的离线诊断 join 中产生；不能成为在线
输入或运行时事件。临时放车还必须说明只在 Play 内存态发生、退出不保存，
否则与“零场景字节”和现有未授权场景修改相冲突。

最后，E4 不能把整体仍为 `REVISION_REQUESTED` 的 SCOPE-001 revision 3
称为“已冻结协议”而仅按可变章节引用；E4b 的“可选”也会允许看过前序结果
后决定是否花预算。E5 又会新增 Unity/诊断工具，因此“受影响接口零”和
“只轻量复核汇总证据”都不成立。任何用于参数冻结的采样、计时、持久化或
truth join 工具都必须先形成稳定候选并接受独立复核；E5 的 Play 前还受
COORD-005 人眼保真检查约束。

Required revisions for round 2:

1. **增加零执行输入资格门。** 在任何调参、benchmark 或代码实现前，冻结
   E1/E2 的源目录、run/scenario/seed、frame ID、文件 SHA-256、truth join
   和模型/spec SHA-256 清单；给出缺件/样本不足终态。扩充清单只允许在
   首次查看 tuning/qualification 结果之前整体重冻结，旧清单留档；之后
   不得换样本求通过。
2. **把 E1 写成逐色可判定合同。** 冻结颜色标签权威来源、每色 tuning 与
   qualification 最小样本量、按 run 的组隔离、BGR/RGB→HSV 定义、红色
   回绕表示、阈值/形态学/连通域/tie/无候选规则，以及 90% 是逐色还是
   汇总点估计或置信界门。truth 不可用、目标不可见和同色多车必须有唯一
   计分/排除规则；qualification 一旦揭盲禁止回调 HSV。
3. **让 E2 测到唯一的真实路径。** 逐字指定实际 NanoTrack factory/spec/
   模型、`_catch_up` snapshot→replay→head-equality 循环、5 Hz live-head
   推进器与至少两次推进的实现、冷/热启动和设备负载、60 次预注册起始
   frame、timeout/invalid-box/异常的失败记账。冻结 type-7 实现，以及
   三个 age 档到单一 `catchup_cand`/后续 buffer 的机械映射；失败不得从
   p95 分母中静默删除。
4. **重写 E3 的故障模型与结果空间。** 分开“子进程 SIGKILL、OS 继续运行”
   与“掉电/内核崩溃”；本轮若只测前者，结论必须同样收窄。分别调用或忠实
   包装真实 C# AtomicFile 与 Python RunLogger，冻结由父子握手触发的每个
   kill 边界、首次创建/覆盖替换和 append 记录大小/分块；输出至少区分
   old/new/missing/partial/temp residue/truncated-tail/duplicate。文件与目录
   fsync 是否构成规范保证由合同明示，不能由 20 次未失败反推。
5. **冻结 E5 而不是留待实现者设计。** 给出三组几何/速度/间距数值、每组
   trial 数、随机性/初态/reset/时窗、目标与遮挡/干扰物身份、相机/机身/
   云台/追踪器配置和 `reliable` 精确判据。truth attribution 只做离线 join，
   并冻结 LOST/DRIFT/OCCLUSION 的互斥或优先级与 frame join；诊断 Play
   只允许内存态临时布置、Don't Save、零 ID/配额。若需要保存场景或配置
   字节，先停下取得用户新授权。
6. **钉住 E4 与批次门。** 把 V1 协议正文复制进本提案或绑定不可变文件
   hash/行文快照并说明冲突优先级；E4b 在 Q1 前预先选择精确 manifest 或
   删除，不得结果后可选。执行序改为：E1–E3 工具/清单稳定候选 →
   Acceptance 写入审计与停点确认 → 独立复核 → 运行本地校准；E5 工具另成
   稳定候选并先复核、完成人眼保真检查后才可请求诊断 Play。复核必须覆盖
   真实代码、采样隔离、计时路径、故障注入和 truth 边界，不接受仅看汇总
   Markdown 的减免。

Disposition:

- `P1-VLM-CAL-001` 转 `REVISION_REQUESTED_ROUND_1`，退回构思角色提交
  revision 1；测量优先方向及 E1–E5 的问题分解保留，不要求回到纸面
  recharter 循环。
- `P1-VLM-SCOPE-001` 继续 `PAUSED_PENDING_CALIBRATION`，round 4 已关闭的
  项目与五条未闭义务均不改变。
- 本轮不授权任何实现、实验、Edit Mode/Play、API、训练、场景/配置写入、
  ID/配额或时序参数生效；v0.3.16 与既有 legacy disposition 不变。

---

## 10. Revision 1 逐条回应（构思角色，2026-08-06）

**本轮方法说明**：先做只读取证（磁盘归档清点 + 真实代码逐行阅读 +
对抗性复核），再改稿。取证推翻了 revision 0 自身的四处写法，已在 §0
建表登记（C1–C4）。这与接受角色的判断一致："revision 0 仍把多项预注册
决定留给了实现角色"——其中四项不仅是留白，而是**与磁盘事实相反**。

**1 — 零执行输入资格门。** §3.0 新增。冻结机制沿用仓库既有
`p1-scene-006-probe-manifest/v1` 的形态（严格 schema/work_id/计数
相等校验 + 40-hex commit + 冻结路径集 + 结果按 `manifest_sha256`
反绑），不发明新机制。清单字段含逐文件 SHA-256（图像/元数据/真值
三类）、真值 schema 与 join 规则、四个模型 SHA-256、Python/cv2 版本、
`HEAD` 与 porcelain。给出构思角色的**非权威预扫表**（9 个来源目录的
帧数/最长连续/schema/时钟/scenario/真值覆盖，全部本会话直接复算）。
四条硬性规则：`runtime/frames` **禁入任何 manifest**（实测它是
`retained_frame_count = 4096` 的活动环形缓冲，下次运行即覆盖）、
`CAL_INPUT_MANIFEST_INCOMPLETE`、`CAL_INPUT_INSUFFICIENT`、以及
"重冻结只在首次揭盲前、旧清单留档、揭盲后换样本即整实验作废"。

**2 — E1 逐色可判定合同。** §3.1 重写，含两处 revision 0 的实测勘误：
(a) **`evaluation_truth.jsonl` 全仓库不存在**（C1），评分改用实际存在
的 `p1-detect-scouting-truth/v2`、`/v1` 与 `p1-scene-006-probe-truth/v1`；
(b) **颜色集不存在**（C2），无任何白色具名实例，且三个真值 schema 都
没有颜色字段，故颜色集改**红/黄/紫**、标签权威改为 §3.1 冻结的
prefab→颜色映射表（逐行给出代码字面量或贴图出处 + OpenCV HSV 换算）。
由该表直接导出三条不留裁量的设计约束：紫色 S 实测仅 **0.231**（统一
`s_min ≥ 0.45` 会整类淘汰）⇒ `s_min/v_min` 逐色独立；TetherAnchor
H = 22.9 与 taxi H = 22.2 色相不可分 ⇒ 黄色带必须附加非颜色的
`exclude_anchor`（其输入只有配置与平台位姿，不含真值）；红色 H ≈ 0.7
⇒ 必须写成回绕双区间。规则族七步（BGR→HSV、掩码、开闭运算、8 连通、
面积下限、锚点排除、最大面积 + `(y,x)` tie-break、`NO_CANDIDATE`）
全部冻结，仅六个参数可在 T 组拟合并即刻哈希。组隔离按 C3 重做：实测
`scout-3` 与 `scout-4` 是**同一条轨迹**（相机位置距离恰 0），不能互为
隔离组，故 T/Q1 改为 `scout-4` 的两个不相交分段、Q2 跨 scenario、
Q3 体育场对抗段；并**如实披露同族隔离只隔离时间不隔离视角**这一
无法用措辞消除的局限。四类例外（真值不可用、目标不可见、v1 的
`target_visible=false` 仍带框的 46 帧、同色多实例）各有唯一处置；
90% 改为**逐色**门（汇总会让失败色被掩盖）。

**3 — E2 唯一真实路径。** §3.2 重写。逐字锁定 `_catch_up` 的
**无迭代上限**语义（实测永不收敛时单次调用 `replay_tracker` 20 次、
内层预算 `max(0.001, 2.0 − 已耗)`）、十个终态字面量、
`tracker_factory()` 先于 `valid_replay_box` 的顺序、以及**缺模型会
伪装成 `intermediate_frame_missing`** 这一陷阱（故 benchmark 须先断言
四个模型 SHA-256）。两级 harness 二选一并**预注册 Level A**——实测
`sensor_protocol.py:9-10,18-29` 硬拒非 v3/`system-stopwatch/v1` 帧，
冻结归档中仅 3 个目录合格，故来源改为 qual-2（3668 连续帧）。
**秒数档改帧数档**（`N ∈ {25,50,100,200,300}`）：实测 SCENE-004 的
`capture_hz` 是 **20.0** 而非 5.0，按秒冻结会低估 4 倍。60 个预注册
起点、冷/热分列（实测 factory 冷 ≈148 ms / 热 ≈4.3–4.9 ms、update
≈3.8 ms）、头帧推进器须至少推进 2 轮以覆盖真实再循环分支、失败样本
计入分母且 `>20%` 标 `E2_TIER_UNSTABLE`、`numpy.percentile(...,
method="linear")` 冻结 type-7、`.venv-track` + `cv2 5.0.0` 硬前置。
导出公式改为对 `(age, hz)` 的显式函数，超界即
`E2_CATCHUP_EXCEEDS_CONTRACT_BOUND`，**禁止截断**。

**4 — E3 故障模型与结果空间。** §3.3 重写。M1（子进程 SIGKILL、OS
存活）与 M2（掉电/内核崩溃）分离，本轮**只测 M1** 且结论逐字收窄；
额外披露仓库 `F_FULLFSYNC` 零命中、macOS `fsync(2)` 不保证介质落盘，
故 M1 全绿也不得推断掉电耐久。被测对象分四项：三条 Python 真实代码
直调（`RunLogger` 无 fsync / `protocol.atomic_write` 有 fsync 但无
prefix 故残留可见 / `rate2_protocol` 用 `os.link`），C# `AtomicFile`
只做静态审计 + **逐字标注为"转写模型、非真实代码"**的 Python 复刻，
并把 .NET 语义列为"未由本仓库断言"的外部事实。五个父子握手 kill
边界、七类结果空间（含 `TEMP_RESIDUE` 与 `DUPLICATE_RECORD`）、
三档记录尺寸（540/770/8200 B，末档跨 8192 缓冲边界）取自真实归档实测
（min 528 / median 538 / max 773）。明确"N 次未失败不得反推为保证"。
另把本轮取证发现的仓库既有先例写进结论：
`qualification_protocol.py:605` 的 `create_once_json` 先落盘、
`:624-625` 才切状态——**"耐久记录先于副作用"已是本仓库惯例**，ACK
账本应照抄而非另创。

**5 — E5 冻结。** §3.4 重写，含 revision 0 最大的一处勘误（C4）：
全项目 `Instantiate` **零命中**，`SceneVehicleAdjustmentApplier` 只能
`SetActive(false)` 或 `position = destination`，**既不能生成车辆也
不能驱动其运动**，故"大车与目标按相对速度交汇"不可实现，撤回。改为
**静止公交（`Vehicle_Bus_*`，3.7×9.3×3.57 m，场景最大足迹）+ 三档
退距**，几何由冻结字节可复算（机体 `(140,25.000001,108)`；北段远端
视线仰角 `atan(25/17.69)=54.7°` ⇒ 3.57 m 高遮挡体须距目标
≤ 2.52 m），据此冻结 D1 `1.0 m` / D2 `2.5 m` / D3 `4.0 m`（D3 为
阴性对照）。三类事件各自的 trial 数、观察窗、初态、复位、身份与
配置全部给值；`TARGET_STOPPED` 用既有 `SetMotionEnabled` API。
`reliable` 给出机械判据（每次 trial 都须有 ≥2.0 s 的 `ok == False`
连续段且起点落在通过窗 ±2 s 内）。真值归因按要求改为**离线 join**，
在线侧只记 controller 信号，并冻结标签互斥优先级；E5 manifest 须在
Play 前逐字命名该模式实际启用的真值写出器。字节边界：`config/` 与
`Assets/` 前后 SHA-256 清单逐条相同，重定位只经 gitignored 的
`runtime/scenario_config.json` 运行时覆盖（CLAUDE.md 既有机制），
Don't Save，零 ID/配额。另主动披露一项风险：SCENE-004 的两个动态
审计开关均为 `false`，把公交移到路线旁**不会触发任何告警**——这既是
实验可行的原因，也使人眼目检成为必要环节。

**6 — E4 与批次门。** §3.5：V1 协议正文**逐字复制**入 E4.c，并三重
绑定（源文件 SHA-256 `08afbd4e…cb68b`、行范围 532–571、块 SHA-256
`caff93be…58ba`）；冲突优先级写明——复制件为执行时唯一权威，
SCOPE-001 revision 4 一旦改动 V1 或任一哈希，**E4 自动回到未裁定
状态**。E4.b 登记本轮实测发现的两处 V1 阻断：`evaluation_truth.jsonl`
不存在（V1-B1）、五个声明来源族中三族实为空目录或零匹配（V1-B2，
实测 `p1-track-{follow,nadir,occlusion}` 只有遥测无帧、`rs2-*` 与
`*qual-3*` 零匹配），二者未闭前 E4 不可执行；本提案只登记不自改
SCOPE-001。**E4b 整体删除**（结果条件性支出）。§4.2 执行序改为
"工具 + 清单稳定候选 → 停点与写入归因 → 独立复核 → 才运行测量"，
E5 另成批次并加 COORD-005 人眼保真检查；**撤回轻量复核减免请求**，
复核范围写明覆盖真实代码、采样隔离、计时路径、故障注入与真值边界。
§2 的"受影响接口零"改为如实声明（运行时协议零改动，但新增校准工具
与一个 Editor 诊断脚本）。

**授权与边界**：本稿不主张任何新授权；E1–E3 的执行待接受裁定 +
停点 + 独立复核，E5 另待人眼保真检查与诊断安排，E4 待 V1 阻断闭合与
Q1 逐字授权。不实现、不运行、不调 API、不写 `config/`/`Assets/`
字节、不动设计基线与 SCOPE-001。提交后返回 Acceptance round 2。

---

## 11. Acceptance review decision — round 2

### Acceptance round 2 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

Revision 1 的实测勘误是有效进展。接受角色在磁盘上复核到：scout-4 的
T/Q1 确有 30/26 个预注册帧，Q1 中红/黄/紫分别有 26/15/13 帧至少一个
有效正例；qual-2 的 v3/`system-stopwatch/v1` 连续帧与四个 NanoTrack
绑定文件确实存在；SCOPE-001 全文件 SHA-256 也与 §3.5 一致。C1–C4、
E4 的 V1-B1/B2、M1-only 崩溃结论、完整独立复核与 COORD-005 人眼门均
应保留。本轮不再把“归档不存在”当作阻断。

但 revision 1 仍没有把实验唯一化，且有两处按当前代码必然先失败的合同。
E1 只列出可调参数名，没有冻结每个参数的搜索范围/网格、拟合目标、搜索
次序或并列择优；实现者仍可在同一 T 组上得到多套都“符合提案”的 HSV
参数。Q2 又被明确记为“无帧元数据”，而黄色 `exclude_anchor` 逐字要求从
帧元数据读取位姿与内参，现稿没有冻结 Q2 的替代来源和投影口径。

E2 的五档在真实入口下并不可按文执行。`ReanchorRuntime` 用
`maximum_result_age_s=2.0`、`frame_buffer_s=6.0` 建立 `FrameHistory`；
20 Hz 时 50 帧以上首先越过 2 s stale 门，约 120 帧以上的 source 又会被
duration eviction 移除。§3.2 只允许 benchmark 覆盖
`catchup_timeout_s`，所以 100/200/300 帧档测不到所声称的 replay 成本。
“独立线程至少推进两轮”也没有握手点，不能机械保证 head 在每次
equality check 前恰好改变；p95 公式还把以 `ms` 报告的量直接送入按秒
`ceil_0.5`，单位未闭合。

E3 仍把关键选择留给实现者。P1 append、P2 replace、P3 link 与 C1
transcription 并不共享同一组适用边界，但现稿只说“每个适用边界”，没有
冻结对象 × 首次创建/覆盖/append × 记录尺寸 × kill 边界矩阵和各边界的
具体 hook。七类结果也不是天然互斥：`TEMP_RESIDUE` 可与 `OLD_VALUE`、
`NEW_VALUE` 或 `PARTIAL_CONTENT` 同时出现，`TRUNCATED_TAIL` 也可伴随
`DUPLICATE_RECORD`；无多标签规则或优先级就无法形成唯一计数表。

E5 的几何与判据同样未闭合。D1/D2/D3 只给相对路线中心线的退距，没有
给公交的精确沿段坐标、最终 `(x,y,z)`、冻结实例与朝向；相似车配置也只
写“北段路线旁 2.0 m”。现有 `CoverageEvaluator` 的
`evaluation_truth.jsonl` 只给 `geometrically_visible`/truth box，不给
遮挡实例身份；现稿却把实际 truth writer/schema/path 延后到 Play 前由
manifest 再选，无法保证生成 `OCCLUDED_BY_<instance>`。此外只有遮挡
给了 `reliable`：D3 阴性对照、相似车 identity confusion 和
`TARGET_STOPPED` 可检测性均没有各自的机械指标、分母与成功/失败终态。

Required revisions for round 3:

1. **冻结 E1 拟合算法。** 对每个颜色逐项给出 band、`s_min`/`v_min`、
   `k`、`a_min`、黄色 `r_anchor` 的有限搜索域/步长，冻结目标函数、搜索
   次序与并列 tie-break；明确 target/distractor ID 到逐色真值集合的展开
   规则。为 Q2 冻结相机位姿、内参和 anchor 的唯一来源及投影公式；缺任一
   输入必须走具名硬停，不能由实现者另找替代。
2. **把 E2 写成可执行的 Level-A harness。** 冻结每个 N 档注入的
   `maximum_result_age_s`、`frame_buffer_s`、`catchup_timeout_s` 及所有
   其他会影响退出的参数，说明它们只存在于 harness、原配置字节不变；
   用 barrier/事件逐步规定 snapshot、head append 与 equality check，给出
   精确 replay 轮数。统一秒/毫秒单位，并说明失败样本以哪个数值进入
   type-7 分位；配置/模型错误仍必须在计时前硬停。
3. **补齐 E3 试验矩阵与分类器。** 明列每个真实对象和 C1 转写模型的
   create/overwrite/append 初态、适用 B0–B4、hook 位置、记录尺寸、重复数
   与读回 oracle；把七类改成冻结的多标签向量，或给出无重叠的优先级和
   完备性证明。未适用格必须显式 `N/A`，不得留给实现者判定。
4. **完全冻结 E5。** 对三档公交、红族干扰车逐个给出 survey 身份、
   `original_xz_m`、容差、最终 `(x,y,z)`、rotation/yaw、通过窗的机械
   推导与 reset；把初始化 frame/box 预先离线选定并哈希，运行时不得读取
   truth 来选框。提案正文须选定实际 truth writer、schema、path、遮挡
   root-ID oracle 与 frame join；若需新增 writer，就把它明确列入批次 2
   和复核范围，不能延后到 manifest 再选。
5. **为 E5 三类事件分别给门。** D1/D2 的阳性可靠性之外，冻结 D3
   阴性对照允许的 LOST/遮挡上限；定义相似车混淆的 target/distractor IoU
   身份判定、分母与终态；定义停车事件的可观察输入、检测延迟/误报口径、
   分母与终态。任一阴性对照失败必须污染因果解释，不能只作描述。
6. **收紧 manifest 与批次交接。** 解决“任何实现前先有 manifest”与
   “manifest builder 属批次 1 新工具”的循环依赖，冻结 repo-relative
   路径规范及 hash 的规范字节（包括 E4 block 是否含末尾 LF）。明确
   T-only 拟合、参数 create-once 冻结、Q 揭盲、结果回 Acceptance 的
   串行状态；本包任何结果在新一轮 Acceptance 归因前不得恢复
   SCOPE-001 revision 4。

Disposition:

- `P1-VLM-CAL-001` 转 `REVISION_REQUESTED_ROUND_2`，退回构思角色提交
  revision 2；revision 1 已核实的 C1–C4、输入预扫、M1-only 边界、E4
  blockers 与完整 review/人眼门全部保留，不要求重做已闭部分。
- `P1-VLM-SCOPE-001` 继续 `PAUSED_PENDING_CALIBRATION`；不得因本轮
  文档进展恢复 revision 4 或任何 VLM/M3′ 实现。
- 本轮不授权实现、实验、Edit Mode/Play、API、场景/配置写入、ID/配额
  消耗或时序参数生效；不产生新的用户授权义务。

---

## 12. Revision 2 逐条回应（构思角色，2026-08-06）

**本轮方法**：与 revision 1 同法——先读真实代码与冻结字节，再改稿。
本轮又产生一处**推翻自身设计**的实测发现（E5 遮挡在 SCENE-004 上
构造性不可能，§E5.0），已按"失败也是有效产出"如实登记并重构。

**1 — 冻结 E1 拟合算法。** §E1.b′ 新增：色相中心不搜索（取 §E1.a
实测值），六个参数各给**有限枚举域**（红/紫 720 组、黄 2160 组，
穷举可行、不用启发式）；唯一目标函数 `HIT + TRUE_NEGATIVE`；冻结
枚举次序 `h_w→s_min→v_min→k→a_min→r_anchor`；五级 tie-break 以
"枚举次序中先遇到者胜"收口保证唯一解。§E1.b″ 给出 target/distractor
ID → 逐色真值集合的展开规则（按 `StableObjectId` 的规范前缀名匹配
`Vehicle_Taxi` / `Vehicle_SUV_color01`，去 ` (N)` 克隆后缀，匹配 0 条
按"不在画面"处理）。§E1.b‴ 处置 Q2：实测该归档**无逐帧传感器元
数据**，故 `exclude_anchor` 在 Q2 **停用**并逐帧标注
`disabled_no_camera_pose`（停用只增假阳性，故 Q2 通过是保守的；Q2
本就不设门），T/Q1/Q3 上则冻结完整投影公式（世界锚点→
`camera_rotation_xyzw` 逆旋转→`intrinsics_px` 针孔投影，`z ≤ 0` 不
剔除）；缺任一输入走具名硬停 `CAL_E1_PROJECTION_INPUT_MISSING`，
**不允许实现者另找替代来源**。

**2 — 把 E2 写成可执行的 Level-A harness。** 接受角色的判断经实测
确认且根因已定位到两处代码：`reanchor.py:672` 的
`head.capture − source.capture > maximum_source_age_s` 使 20 Hz 下
`N > 40` 帧即 `RESEED_DISCARDED_STALE`；`reanchor.py:600-602` 的
`cutoff = capture − duration_s` 驱逐使 `frame_buffer_s = 6.0` 只保留
约 120 帧，`N ≥ 120` 的源帧被逐出后 `after_through` 抛
`intermediate_frame_missing`。§3.2.c 因此给出**逐档注入表**：
`maximum_source_age_s = T_N + 2.0`、`frame_buffer_s = T_N + 4.0`、
`catchup_timeout_s = 60.0`，其余 18 项原值不动；注入方式为**进程内
构造 `ReanchorConfig`**（它只是 `(path, raw, sha256)` 的薄包装，
`parameters` 只读 `raw`），绕开 `load_reanchor_config` 的相等门而
**不动任何配置字节**，且开跑前须对原文件成功执行一次
`load_reanchor_config` 证明字节完好。头帧推进改为**确定性握手**：
在 `history.snapshot` 装计数代理，仅第 1 次调用后向活动 history 追加
1 帧，由此 replay 轮数**恒为 2**、无线程竞态，工件逐次记录实际调用
次数、≠2 即作废。单位闭合：原始量一律 ms，导出公式内显式 `/1000`
后再在秒域 `ceil_0.5`。失败样本**不以任何数值进入 type-7 分位**
（它们无合法耗时语义），改以 `attempted/valid_n/逐终态计数` 三重
记账 + `valid_n ≥ 48` 的 admissible 门防止"筛掉失败美化分布"。
配置/模型错误在计时前硬停（四个 SHA-256 + `cv2 5.0.0` + 原配置
可加载）。

**3 — 补齐 E3 试验矩阵与分类器。** §E3.c 给出 8 行矩阵（P1a/P1b/
P2a/P2b/P3a/P3b/C1a/C1b × 初态 × 适用 B0–B4 × 记录尺寸 × 重复
20），未适用格**显式 `N/A`** 并要求打印，合计 660 次注入；hook 形态
冻结为 `instrumented_*` 薄包装 + 管道标记 + 父进程 `SIGKILL`，包装
本身入复核范围；读回 oracle 为独立新进程的三步。§E3.c′ 把七类改为
**四个正交维度的向量**：`dest_state`（四值，按字节比较对全体字节串
的划分即完备性证明）、`temp_residue`、`tail`、`dup`，每维内部互斥
且完备，联合计数唯一可复算，**不存在需要优先级消歧的重叠**。

**4 — 完全冻结 E5。** 先做了 round 2 未要求但必须先做的
**解析前置检查（§E5.0）**：遮挡条件闭式为
`standoff < (h_occ − y_t)·D / y_d`，走廊合法性要求中心退距
`≥ 1.5 + 半深`。以场景最高可移动车辆（`Vehicle_Container_*`，顶
`4.15 m`，半深 `1.815 m`）代入——**SCENE-004 的最大可行 standoff
仅 `1.862 m` < 需求 `3.315 m`，可行弧长占比 `0.0000`，即构造性
不可能**；主环线最优 `7.131 m`、占比 `0.6651`，可行。故 E5 拆为
**E5-A（混淆+停车，留 SCENE-004）** 与 **E5-B（遮挡，移主环线）**，
并把"E5-B 是否可在 SCENE-007 未修复前跑"作为一条范围裁量**交回
Acceptance，不预取**。§E5.1 在正文**选定** writer：既有
`WriteScoutingTruth` / `p1-detect-scouting-truth/v2` /
`.../truth/frame_%010d.json`，**不新增 writer**；同时诚实降级——
射线级遮挡身份在任何现有 writer 中都不存在，故归因逐字命名为
`OCCLUDER_ATTRIBUTION_BY_BOX_OVERLAP` 并冻结其规则与
`OCCLUDED_BY_UNKNOWN` 兜底；join 节拍由代码约束固定 0.5 s
（`P1Scene004Scouting.cs:62/:73` 硬要求 `sample_hz ≈ 2.0`）。
§E5.2 给出 E5-B 的全部数值：遮挡体身份逐字继承默认场景已有
relocation 条目（`original_xz_m {168.253632, 117.146248}`、
容差 `0.1`，只改目的地并置 `mark_as_distractor: true`）、通过段
（南直段中点 `D = 57.396 m`、仰角 `23.70°`、挡顶阈值 `5.922 m`、
挡底阈值 `8.997 m`）、三档近边退距与**中心世界坐标**
`D1 (148.490, 0.0, 67.072)` / `D2 (147.806, 0.0, 69.144)` /
`D3 (146.808, 0.0, 72.168)`。朝向问题如实处理：`Apply` **只设
position 不改 rotation**，故朝向为被动观测量，不利时记
`E5B_OCCLUDER_ORIENTATION_UNFAVOURABLE` 回构思，**不得**自行加旋转。
§E5.3 解决混淆体的身份难题——冻结 survey 的 10 辆近车中**无红族
车辆**，故混淆体改用 `TargetVisualFactory.AddTargetVisual`（目标
自身的生产构造源）在 Play 期构造**运行时红色副本**，外观与目标
同源（最强外观混淆）、与目标同为 runtime-only 对象、零场景字节，
位置冻结 `(140.0, 0.2, 123.0)`（走廊外 0.5 m）。初始化帧/框改为
**离线预选并哈希**（规则：`frame_id` 最小且 `VALID` 且
`min(w,h) ≥ 0.06`），运行时只读 manifest 不读 truth；首个配置以
`E5_SEED_RUN` 产出该值且不计 trial。

**5 — 为 E5 三类事件分别给门。** §E5.4 四行表：遮挡阳性（D1/D2）
给可靠性判据；**D3 阴性对照给上限式判据**（通过窗内
`target_visible == false` 的 tick ≤ 1 且无 ≥ 2 s 的 `ok == False`
段），超限即 `E5B_NEGATIVE_CONTROL_CONTAMINATED` 并**使遮挡的因果
解释整体作废、阳性结果不得单独引用**；混淆给身份判定（与目标框
IoU < 0.3 且与副本框 IoU ≥ 0.3）、分母（邻域 tick 数）、误认率与
Wilson 区间、`0.05` 终态线；停车给**仅 controller 侧**的可观察输入
（观测框中心 10 s 内位移 < 0.02）、检测延迟、误报率分母与
`≤ 4.0 s` / `≤ 0.02` 双终态，不达标即
`STOP_NOT_DETECTABLE_BY_MOTION_RULE` 如实报告。

**6 — 收紧 manifest 与批次交接。** §3.0 新增规则 5–7：循环依赖以
**三阶段串行**解开——S1 工具态（写 builder，零 manifest）→ 停点 +
复核 → S2 清单态（用**已复核的** builder 产出 manifest，零测量）→
S3 测量态（T 拟合 → create-once 冻结 → Q 揭盲 → 交回 Acceptance），
builder 一改即回 S1；路径规范为 repo-relative/POSIX/无 `./` 前缀，
文件哈希对原始字节、manifest 哈希对 canonical JSON 字节（与
SCOPE-001 §2.4b 同口径），**E4 引用块的哈希对不含末尾 LF 的
532–571 行拼接字节**（与取证一致）；并冻结"S3 结果在新一轮
Acceptance 归因前不得恢复 SCOPE-001 revision 4"。§4.2 相应重写为
S1/S2/S3 批次图，并列出**新增工具清单共 7 项**全部入复核范围。

**授权与边界**：本稿不主张任何新授权。唯一交回 Acceptance 裁量的
新问题是 §E5.0 的 E5-B 循环选择（主环线 vs 等 SCENE-007）。不实现、
不运行、不调 API、不写 `config/`/`Assets/` 字节、不动设计基线与
`P1-VLM-SCOPE-001`。提交后返回 Acceptance round 3。

---

## 13. Acceptance review decision — round 3

### Acceptance round 3 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

Revision 2 已经关闭了上轮的多个开放结构：E1 有了有限穷举域、唯一
目标和 tie-break；E2 的确定性 snapshot 握手取代了线程竞态；E3 改成
正交结果向量；S1→S2→S3 解开了 builder/manifest 循环依赖；E5.0 对
SCENE-004 遮挡不可行的自否定量结果也应保留。这些都不要在下轮
重写或重算。

但本轮按真实入口逐字核对后，仍有三类可执行性阻断。首先，E2 向
`ReanchorConfig.raw` 注入的 `maximum_source_age_s` 不是配置键；运行时
`ReanchorRuntime._catch_up()` 实际把 `self.p["maximum_result_age_s"]` 传给
`replay_tracker(... maximum_source_age_s=...)`。因此现表不会抬高 2 s 年龄门，
N=100/200/300 仍会先 stale。而且 harness 没有冻结每档的
`source_box_norm` 来源，回归导出只说 OLS 后取“残差修正 p95”，没有
可独立复算的精确估计式。

其次，E3 的 P3b 不可达。`create_once_bytes()` 在目标已存在时会先
读回比较：同字节立即返回，异字节立即抛 `FileExistsError`；两条路都
在创建 temp/link 前结束，所以 overwrite 初态不能遍历 B0–B4。表中 P1 的
`B3=fsync 后、publish 前` 也把不存在的 publish 语义带入 close 路径。
按当前表内数量直接求和为
`3×2×20 + 2×20 + 4×5×20 + 2×3×20 = 680`，不是文中的 660。

最后，E5 目前无法使用所声称的既有 writer。
`CoverageEvaluator.ConfigureScouting()` 只加载 `P1-DETECT-001 /
p1-detect-scouting` 和 `P1-SCENE-004 / p1-scene-004` 两类冻结 session，并硬验
scenario hash/identity/session ID。默认主环线是 `deterministic-loop-default`，故 E5-B
不新增 session/profile 和加载路径就不可能进入 `WriteScoutingTruth`。该
writer 本身又必需 `session_id` 并创建 session-root truth，与 COORD-005 诊断
通道“无 scenario/session/run ID”直接矛盾。`ConfigureScouting()` 还在启动时一次性
枚举并核对 distractor 数，而现稿没有保证 E5-A 的运行时红色副本先于
该枚举创建。

E5 的刺激和门也有三个独立矛盾。红色副本中心放在
`(140.0, 0.2, 123.0)` 不等于实体在走廊外：`TargetVisualFactory` 的 body
尺寸是 `(2,1,4)`，`Quaternion.identity` 下 z 方向半长 2 m，会覆盖到
z=121 路线。预选初始框的规则仍从 Unity truth 取 `bbox_norm` 后把它交给
tracker，这仍违反“truth 只属评估器、不得进入 perception/tracker”的硬边界；
离线冻结不会改变数据来源。停车门要求先观察连续 10 s 位移不足才判停，
却又要求在真值停车后 4 s 内检出；最早判定时间已超过成功上限，
因此任何 trial 都不可能通过。

Required revisions for round 4:

1. **收口 E1/manifest 字面合同。** 统一 §3.0 “绝对路径”与规则 6
   “repo-relative/POSIX”的相反要求；把 RED probe 的 `box_status`
   改成真实 schema 字段 `target_box_status`（或给出可复核的显式映射）。
   其余已冻结网格、目标、顺序和 Q2 停用/硬停不变。
2. **修正并完全冻结 E2。** 注入表必须使用真实配置键
   `maximum_result_age_s`，并冻结每个 N 的 `source_box_norm` 唯一来源/
   字节、五档到 `p95_fixed_ms`/`p95_per_frame_ms` 的完整数学估计式。
   snapshot 调用数不等于 2 是具名仪器硬停，不是“作废重跑”。
3. **按真实控制流重写 E3 表。** P3b 只能记录目标已存在时的
   preflight return/failure，不得虚构 B0–B4 kill 格；为 close、replace、link、
   transcription 分别命名真实边界，重算并统一每行与总次数。
   正交结果向量保留。
4. **为 E5 选定真正可达的采集路径。** 逐条说清 E5-A/E5-B 的
   scenario/work/profile 身份、载入文件、writer 创建时机、输出根和 ID 规则；
   保证红色副本在 distractor 枚举前存在。若坚持 COORD-005 的零-ID
   诊断通道，就必须提出不依赖现有 scouting session 的明确 writer；若要
   新 session/profile/ID，必须把这项协议变更显式交回接受角色，不得
   在提案中默认已授权。
5. **修正 E5 刺激、truth 边界和时间门。** 用完整 renderer/vehicle
   bounds 与 route sweep 证明红色副本全身出走廊；tracker 初始框必须来自
   不使用 Unity truth 的冻结来源。修正“连续 10 s 后判定”与“4 s 内检出”
   的数学矛盾，使每个成功终态实际可达。
6. **先把 E5-B 技术分支写到可决策，再申请范围选择。** Revision 3 必须
   分别给出“等 SCENE-007”和“主环线零测量诊断”的闭合执行契约，
   并显式列出后者所需的场景/协议变更。在该分支本身可执行前，
   Acceptance 不让用户为一个尚不成立的方案预授权。

Disposition:

- `P1-VLM-CAL-001` 转 `REVISION_REQUESTED_ROUND_3`，退回构思角色提交
  revision 3。Revision 2 已闭合的 E1 穷举/tie-break、E2 确定性握手、
  E3 正交结果向量、E5.0 不可行证明与 S1→S2→S3 顺序全部保留。
- E5-B 移入默认主环线会扩大当前诊断范围，但本轮没有一条可执行
  且符合 COORD-005 的主环线采集路径，因此**未向用户请求范围授权，
  也未授权该移动**。技术契约闭合后由 Acceptance 停下来请用户选择，
  关键授权将逐字记入 `docs/authorizations.md`。
- `P1-VLM-SCOPE-001` 继续 `PAUSED_PENDING_CALIBRATION`；本轮不授权实现、
  实验、Edit Mode/Play、API、场景/配置写入、ID/配额消耗或时序参数生效。

---

## 14. Revision 3 逐条回应（构思角色，2026-08-06）

**本轮方法**：与前两轮同法——先读真实代码与冻结字节，再改稿。本轮又
产生一处**推翻自身设计**的实测发现（§E5.0′：云台 45° 限位使遮挡臂在
任何场景、任何锚点、任何高度下都不可能不饱和），已按"失败也是有效
产出"如实登记，并据此**主动撤回 E5-B**，而不是替它找一个能过关的说法。

### Revision 2 的三处实测勘误（本轮取证推翻，逐条如实登记）

| # | revision 2 的写法 | 实测事实 | 后果 |
|---|---|---|---|
| **C5** | E2 注入 `maximum_source_age_s = T_N + 2.0` | 该键**不在配置中**。`_strict_keys` 的 21 个必需参数无此名；`maximum_source_age_s` 只是 `replay_tracker` 的形参（`reanchor.py:660`），真实链路是 `reanchor_runtime.py:306` 的 `maximum_source_age_s=float(self.p["maximum_result_age_s"])` | 按字面执行则 2 s 年龄门根本没抬高，`N=100/200/300` 仍先 stale——正是 round 2 必修 2 要修的那条。已改真实键并补"注入生效回读"硬停（§3.2.c） |
| **C6** | E3 的 P3b：`rate2_protocol` overwrite 初态走 `B0`–`B4` 五格 × 20 次 | `create_once_bytes` 的 preflight（`rate2_protocol.py:92-96`）在目标已存在时**同字节即 return、异字节即 raise**，两条路都在 mkstemp 之前结束 ⇒ 五格全不可达。且 revision 2 漏了同文件的 `atomic_bytes`（replace 族） | 矩阵按真实语句序列重写，R7 改为两条零注入断言，补 W4 行；总数 660/680 → **780**（§E3.b/§E3.c） |
| **C7** | §E5.0 的判定表把"最大可行 standoff `1.862 m`"（**近边**量）与"走廊 + 半深需求 `3.315 m`"（**中心**量）直接相比 | 两者量纲不同，比较无效。走廊合法性与遮挡条件约束的是同一个近边量 `s_near`，遮挡体半深 `w` 不进这对不等式。按正确比较，SCENE-004 是 `1.8639 > 1.5`，**表面可行**——即 §E5.0 的结论会反转。此外 §E5.0 还漏了两条真实约束：机体静止在锚点正上方（`TetheredScenarioBootstrap.cs:188`）、云台 45° 硬钳（`TetheredGimbal.cs:37`），以及遮挡体本身要放得下（需 `1.5+3.627+1.5 = 6.627 m` 无走廊纵深） | 按三条正确判据重算：SCENE-004 现锚点 `0.0000`（真实理由是南北平行段只隔 `5.0 m`，装不下遮挡体，**不是**仰角太陡）；主环线 `0.4484` 但不饱和 `0.0000`。E5-B 两分支仍都不成立：W 经 **209 个包络合法锚点穷举**全为 `0.0000`，M 只在饱和 21.28° 下成立。**E5-B 撤回为负结果**（§E5.0′、§E5.2′） |
| **C7-bis** | 本稿 revision 3 **初稿自身**曾把 C7 的量纲错误推广成一条定理"不饱和遮挡要求 `h − w ≥ y_t + t_h`，89 条 footprint 全扫最优 `2.3394 < 2.55` ⇒ 与场景/锚点/高度无关地不可能" | 该定理**错误**，根源是同一处近边/中心混用；`w` 只影响"箱子放不放得下"，不影响"挡不挡得住"。按正确判据，不饱和遮挡在纯角度上只需 `θ > 29.955°`，远在 45° 限位之内 | 提交前自查推翻并整节重写（§E5.0′）。**最终结论（撤回 E5-B）不变，但支撑论证已全部更换**；此处如实登记，以免复核角色把一条错误定理当成本包的既有结论继承下去 |

### 逐条回应

**1 — 收口 E1/manifest 字面合同。** §3.0 删去"绝对路径"，统一到规则 6
的 repo-relative/POSIX，绝对路径只留一个不参与哈希的 `repo_root_abs`
（任何进入 `manifest_sha256` 的绝对路径都会让同一清单在两台机器上算出
不同哈希）。§E1.b″ 的 RED 判定改用真实字段 **`target_box_status`**，
并按 schema 分支给值（scouting v2 = `VALID`，probe v1 = `OK`），
`box_status` 明确只属 `distractors[]`；四棵真值树的字段与取值分布逐棵
列表复算（含 `p1-detect-scouting-truth/v1` **没有**该字段，故 §E1.d
第 5 行的整帧排除规则不变）；未列出的取值 ⇒ `CAL_E1_UNKNOWN_BOX_STATUS`
硬停。另发现并冻结一条清单卫生规则：probe 真值树里有 1 个
`prompt_*.json` 预热文档（`prompt_000000.json` / `prompt_000002.json`，
两者都带 `target_box_status`），直接 glob `*.json` 会把 106/99 变成
107/100，故 builder 只收 `frame_*.json` 并登记被排除的文件名。
**已冻结的网格、目标函数、枚举次序、tie-break、Q2 停用与硬停不变。**

**2 — 修正并完全冻结 E2。** 注入键改 `maximum_result_age_s`（C5）；
补"注入生效点"条款——`FrameHistory` 在 `reanchor_runtime.py:59` 于
`__init__` 内构造，故三项覆盖必须在构造 `ReanchorRuntime` **之前**
写入 `raw` 深拷贝，且工件必须回读 `history.duration_s` 等三个实际生效
值，不符即 `E2_INJECTION_NOT_IN_EFFECT`。`source_box_norm` 冻结为
**单一字面量** `[0.5515625, 0.17083333333333334, 0.1125,
0.09166666666666666]`（= qual-3 Attempt 3 第 159 帧的用户确认无真值
像素框 `(353, 82, 72, 44)`），五档 × 60 起点 × 冷热全部同框，并写明
"为什么必须同一个框"（否则档位与框内容混淆）与"为什么可以同一个框"
（NanoTrack 裁搜索域后缩放到固定输入，单次 `update` 成本与框内容无关）。
握手轮数 ≠ 2 由"作废重跑"改为**整实验硬停**
`E2_HANDSHAKE_INVARIANT_VIOLATED`——接受角色指得对，让仪器在自己失准时
自行丢样本，与本节"失败样本必须双重记账"的纪律自相矛盾。两个 p95 给出
**完整闭式**：一次 OLS 得 `(fixed₀, per_frame₀)`，再对
`[y_j − per_frame₀·N_j]` 与 `[(y_j − fixed₀)/N_j]` 各取
`numpy.percentile(..., 95, method="linear")`；配 `E2_LINEAR_MODEL_REJECTED`
（`per_frame₀ ≤ 0` 或 `R² < 0.5`）与保守性披露（两个 p95 同用会重复计
尾部，故 `catchup_cand` 是上界，须并列报告 `p95_total_ms(N*)`）。另补
生产可达性披露：注入的 `catchup_timeout_s = 60.0` 超出生产的
`worker_timeout_s = 10.0`，逐档报告 `count(total_ms > 10000)`。

**3 — 按真实控制流重写 E3 表。** 废除 `B0`–`B4` 统一模板——四类写出器
不共享同一条语句序列，套模板必然造出不可达格。改为逐对象按语句序列
命名边界（`A*` append / `C*` close / `T*` replace / `L*` link /
`M*` transcription），并把仓库里的写出器逐字清点为 5 个 Python + 1 个 C#。
`create_once_bytes` 的 overwrite 初态改为两条**零注入**的确定性断言
（同字节 return / 异字节 raise，两者都要求残留数 = 0），`os.link` 撞名
分支显式记 `NOT_EXERCISED_SINGLE_PROCESS`。补上被漏掉的
`rate2_protocol.atomic_bytes`（replace 族、二进制、隐藏 temp），并把
`run_log._atomic_json` 明列为 `AUDITED_NOT_INJECTED` 且给出理由（两个
差异轴已被 W3/W4 覆盖），**不留隐性遗漏**。顺带记下 E3 对 §2.4b 最直接
的产出：`os.replace` 改名后 temp 即不存在，`finally unlink` 是空操作，
故 replace 族**没有**"发布后残留"窗口；`os.link` 只加名字，temp 仍在，
`L6` 是**唯一**会留下隐藏残留的真实窗口——revision 2 把两者塞进同一个
`B4` 格时把这条差异抹掉了。总注入数重算为 **780**。

**4 — 为 E5 选定真正可达的采集路径。** 先把 `ConfigureScouting()` 的
五道前置逐行列出（会话文件二选一、`scenario_id` 硬钉死、scenario 配置
哈希相等、启动时 distractor 计数相等、writer 构造即建 session 目录），
说明 revision 2 的"用既有 writer"为何在 E5 里进不去。然后给出两条闭合
路径：**路径 Z（默认）** 不放会话文件，`ConfigureScouting()` 在
`CoverageEvaluator.cs:324` 早退，`scoutingTruthWriter == null` ⇒ 零真值、
零 session 目录、零 ID，且连带免掉 distractor 计数与 scenario 哈希两道
约束，云台保持由 controller 驱动（测的是真实跟踪回路）；全部 oracle 改
为"冻结几何 + 帧元数据 + controller 观测"的离线重建，并**如实写出代价**
——路径 Z 没有 `target_visible`，做不了几何可见性归因，也算不了
`C_track` 类指标。**路径 S（新 session/profile/ID）** 逐项列出五项协议
变更（新 `IScoutingTruthSession` 实现、放开 `ExpectedScenarioId`、
接受 session-ID 目录的创建即放弃零-ID 属性、`expected_distractor_count`
`2 → 3` 且副本须早于 `Start()` 由受开关文件保护的
`RuntimeInitializeOnLoadMethod(BeforeSceneLoad)` 创建、覆盖后重算
`scenario_config_sha256`），并声明**本提案不预设任何一项已获授权**。
遮挡归因 oracle 随 E5-B 撤回一并删除。

**5 — 修正 E5 刺激、truth 边界和时间门。** 三处全部改掉：
(a) **副本位置**：用 `TargetVisualFactory` 的字面量算出并集 AABB
`x∈[−1,1], y∈[0,1.55], z∈[−2,2]`（高度 `1.55` 与
`route_corridor.target_height_m` 互证），确认 `(140.0, 0.2, 123.0)` 的
z 跨度 `[121.0, 125.0]` **压在北段中心线上**、侵入走廊 `1.5 m`；改为
**`(140.0, 0.2, 125.0)`**，route sweep 实测最小间距 `2.0000 m ≥ 1.5 m`，
并给出 `123.0 / 124.5 / 125.0` 三行可复算对照。离线不可判定的一项
（落点是否被既有物体占据，`road_data.json` 只有局部足迹、无世界摆位）
如实登记，交 COORD-005 目检把关，配 `E5A_DUPLICATE_PLACEMENT_OCCUPIED`
硬停。
(b) **初始框**：接受角色指得对——"离线预选"只改了读 truth 的时刻，没改
数据来源；且路径 Z 下根本没有 truth 文件。改为 `E5_SEED_RUN` 只出图、
由人眼标注像素框、归一化后写入 manifest，运行时与离线两侧都不读 truth；
`min(w,h) ≥ 0.06` 降级为对人工框的合法性校验。
(c) **停车门**：先说明 revision 2 的图像域规则近乎失效（云台一直指向
目标，行驶与停车的图像位移都接近 0），再说明它数学上不可能通过
（最早判定 `t_stop + 10 s` > 上限 `4.0 s`）。改用 **LOS 地面交点位移**
（地平面常数取已接受的 `target_plane_y_m = 0.2`，是冻结场景常量而非
目标真值，符合"必须显式给出有限地平面标定"的既有约束）：`W = 2.0 s`、
`d_thr = 1.0 m`、停车时长 `20.0 s`、检出上限 `4.0 s`。可达性三条实测
证明：最早判定 `t_stop + 2.0 s < 4.0 s`；沿路线滑窗，任意 `4.0 m` 弧长
两端直线距离最小 **`2.8329 m`**（折角处），对 `1.0 m` 有 2.83 倍余量；
停车 `20.0 s` > `4.0 + 2.0`。噪声量级本轮未实测，故 `d_thr` 标为
**预注册而非已验证**，超标即 `STOP_NOT_DETECTABLE_BY_LOS_RULE`，
**禁止**看过结果再调 `W`/`d_thr` 重测。混淆判据同步改为无真值：分母 =
副本投影框完整在画面内的帧数，`MISIDENTIFIED` = tracker 框与副本投影框
IoU ≥ 0.3（副本静止且永远不是目标，落在它身上即误认，不需要目标真值框）。

**6 — 先把 E5-B 技术分支写到可决策，再申请范围选择。** 做这一条时先
发现 §E5.0 的判定本身用错了量纲（C7），于是整节重做：

- **更正判据**。走廊合法性与遮挡条件约束的是同一个**近边**退距
  `s_near`（`1.5 ≤ s_near < (h − y_t)·D/(y_d − y_t)`），遮挡体半深不进
  这对不等式；它以另一种方式起作用——箱子要放进目标与机体之间，需要
  `1.5 + 3.627 + 1.5 = 6.627 m` 的**无走廊纵深**。再补上 §E5.0 漏掉的
  机体静止（`TetheredScenarioBootstrap.cs:188`）与云台 45° 硬钳
  （`TetheredGimbal.cs:37`）两条事实，得到三条判据并穷举重算。
- **分支 W（等 SCENE-007）用穷举否掉**：在 6561 个 1 m 格点里筛出满足
  已接受的 `config/p1-scene-004-anchor-placement.json` 包络合同
  （`θ ≤ 45 − 5 = 40°`、slant `≤ 32.0 m`）的锚点共 **209** 个，逐个重跑
  三条判据，**可行弧长占比全部为 `0.0000`**（最佳者 `(135.0, 114.5)`，
  `maxθ = 38.53°`、`maxslant = 31.96 m`）⇒
  `E5B_INFEASIBLE_UNDER_ACCEPTED_ENVELOPE`。等 SCENE-007 解锁不了这条
  臂，该分支关闭，不需要用户授权也不需要再等。
- **分支 M（主环线）**：可行占比 **`0.4484`**（revision 2 的 `0.6651`
  作废），但**不饱和占比 `0.0000`**——主环线锚点距北段中心线仅
  `0.5 m`（正是 SCENE-007 要修的缺陷），近锚点视线几乎平行于道路，
  遮挡体无处安放；能放下的都在 `θ > 45°` 的远端。技术上能跑，测到的
  却是"云台饱和态下的遮挡"，还要叠加路径 S 的全部协议变更。
- 故**撤回 E5-B 作为 Play 实验**，产出改为 §E5.0′ 的负结果，并列出三个
  可选后继：(1) 删除遮挡事件类；(2) **E5-C 静态几何普查**（两条阻断都
  来自"可重定位车辆"这个机制，既有建筑不受此限且高得多，但其世界摆位
  不在任何冻结工件里，只能在 Editor 查；零成本、非 Play、零 ID，
  **不预判结果**）；(3) 接受饱和态遮挡。建议 **(2) 优先、(1) 兜底**，
  (3) 不建议（会把已知混杂因子写进论文主张）。三项**均不预取**，
  等 Acceptance 裁定。
- **顺带如实登记 C7-bis**：本稿初稿曾把 C7 的同一处量纲错误推广成一条
  "与场景/锚点/高度无关"的普遍定理，提交前自查推翻并整节重写。最终
  结论（撤回 E5-B）不变，但支撑论证已全部更换——特此写明，以免复核
  角色把一条错误定理当成本包既有结论继承下去。

**授权与边界**：本稿**不主张任何新授权，也不再有交回 Acceptance 的范围
选择题**——round 3 让构思角色把 E5-B 写到可决策，结果是它不该被决策而
该被撤回。批次 2 因此只含 E5-A，且在路径 Z 下零 ID、零 truth、零
`config/`/`Assets/` 字节。不实现、不运行、不调 API、不动设计基线与
`P1-VLM-SCOPE-001`。提交后返回 Acceptance round 4。

---

## 15. Acceptance review decision — round 4

### Acceptance round 4 — 2026-08-06

Decision: **REVISION_REQUESTED**

Rationale:

Revision 3 的主要自纠有效：E1 已改用真实
`target_box_status`，E2 已改成真实配置键并冻结源框/估计式/握手
硬停，E3 已按真实语句序列拆开 replace/link/append/close，路径 Z 也
正确证明了既有 scouting writer 为何不可用。红色副本全尺寸、无
truth 人工初始框与可达的停车时间门均应保留。

但 E5-B 的核心结论是用错场景得到的。`P1-SCENE-007` 的输入是
`scenario.default.json` 的主环线，候选为现锚点 `(132,117)` 周围
`12 m` 内、`0.5 m` 网格，成功后的新 scenario 除 `scenario_id` 和
`anchor_world_m` 外与 default 逐键相同。本稿 W 分支却在
`(140,118.5)` 周围 40 m 上枚举，读取
`p1-scene-004-anchor-placement.json` 的 32 m/40° 包络，并对 SCENE-004 的
六段短环线求解。这 209 个点不是 SCENE-007 候选，所以它们全为
`0.0000` 不能证明“等 SCENE-007 也解锁不了”，E5-B 撤回也不能作为
已成立的负结果交给 SCOPE-001。

遮挡公式的竖直坐标仍没有统一。实际目标 parent 被放在 route
`y = 0.2 m`，`TargetVisualFactory` 的局部顶是 `1.55 m`，故目标顶的
世界坐标是 `1.75 m`，不是表中的 `y_t = 1.55 m`。机体世界高度同样是
`anchor.y + initial_altitude_m`。现稿混用世界 y 与局部高度，会改变
`s_near` 窗口；且“最有利朝向”没有冻结旋转优化域或算法，`0.4484`
与 `0.0000` 无法只按正文独立复算。§14 开头又称“任何场景、任何
锚点、任何高度都不可能不饱和”，这正是同节 C7-bis 已明确推翻的假定理。

非 E5 部分也有三处字面不一致。修订索引称 E3 总数为 540，矩阵、
验收条件和 §14 均为 780。`repo_root_abs` 被写作 manifest 内字段又
称“不参与 `manifest_sha256`”，但后文把哈希输入定义为整个 manifest
的 canonical JSON，未定义排除投影。E2 的 `y_j` 是整次 `_catch_up`
耗时，确定性握手已包含两次完整 replay（约 `N + N+1` 次 update）；
导出式又在该拟合量外乘 2，却没有说明这是有意的安全因子还是重复
计入两轮，也不能把由两轮导出的 slope 与 TRACK-002 的单次 update
`3.332854 ms` 直接当作同一物理量交叉检查。

路径 Z 还有一个门级别冲突。COORD-005 的诊断产物“不进证据链、不作为
任何门判定依据”；现稿却用同一零-ID 诊断 Play 签发
`CONFUSION_EVENT_GENERATOR_VIABLE` / `STOP_DETECTABLE` 并作为恢复 SCOPE-001
的合同输入。即使只把它当非绑定诊断，混淆门也没有最小曝光帧数/
独立经过次数，且只用 tracker 框与副本框 IoU：当真目标与副本投影
本身重叠时，正确跟踪真目标也可能被记成 `MISIDENTIFIED`。停车延迟则没有
冻结诊断发令时钟与帧 `capture_monotonic_s` 的同一 `system-stopwatch/v1`
时基及“先记录还是先停车”的顺序，不能定义可复算延迟。

Required revisions for round 5:

1. **用真正的 SCENE-007 分支重做 E5-B 判定。** 使用 default 主环线、
   `(132,117)` 为中心的 12 m / 0.5 m 候选域及 SCENE-007 实际约束；
   不得用 SCENE-004 路线/包络代替。SCENE-007 尚未接受，对支撑/障碍
   数据未决的部分可先给严格上界，但不得声称已穷举“全部合法锚点”。
2. **统一 E5 世界坐标与可复算算法。** 公式只用 world-y（包括目标顶
   `route_y + 1.55` 与机体 `anchor_y + altitude`），冻结遮挡体方向的优化
   域/步长/tie-break 与路线采样端点口径。把旧 §E5.0 标为非规范历史勘误，
   删除 §14 开头已被 C7-bis 推翻的普遍断言。
3. **暂不撤回、删除或扩大遮挡事件类。** 正确重算后才能提交
   `E5-B withdrawn`、E5-C 新普查或饱和态 Play 选择；三者分别涉及核心
   事件集收缩、范围扩大或混杂语义，技术契约闭合后须由 Acceptance
   停下来请用户选择并逐字入账。
4. **区分路径 Z 的诊断观察与门证据。** 若保持 COORD-005 零-ID，
   其结果只能标为非绑定诊断，不能签发 viability/闭合门；若要作为
   SCOPE-001 的绑定校准输入，须给出另一条受复核、具有身份且经用户授权
   的正式采集契约。同时冻结混淆的最小曝光帧/独立经过数、排除
   真目标与副本投影重叠帧的无 truth 规则，以及停车指令日志的
   `system-stopwatch/v1` 时基和“记时→停车”或“停车→记时”唯一顺序。
5. **闭合 E2 的两轮量纲。** 逐字说明拟合的 `y_j` 是两次 replay 的整体
   耗时，并决定导出式外层的 `2×` 是删除还是作为独立安全因子保留；
   若保留，给出命名、理由与对 4 s/10 s 失败门的影响。与 TRACK-002
   update-only 交叉检查时必须先把两轮 slope 还原到单 update 口径。
6. **清除所有字面分叉。** 修订索引的 E3 总数与正文统一；对
   `repo_root_abs` 二选一：移到 manifest 外，或冻结“哈希前删除该键”的
   唯一投影算法和消费端校验；并把人眼保真检查、seed 出图/标注与
   所谓“正式诊断”的先后顺序写成唯一可执行序列。

Disposition:

- `P1-VLM-CAL-001` 转 `REVISION_REQUESTED_ROUND_4`，退回构思角色提交
  revision 4。Revision 3 已闭合的 E1 字段映射、E2 真实配置键/冻结源框/
  握手硬停、E3 真实边界分组、路径 Z writer 可达性分析、红色副本尺寸与
  无 truth 初始框全部保留，不要重写已闭部分。
- E5-B 撤回、E5-C 新范围、饱和态 Play 与删除遮挡事件类均**未被
  接受或授权**；技术契约未闭合，本轮不向用户预取核心范围决定。
- `P1-VLM-SCOPE-001` 继续 `PAUSED_PENDING_CALIBRATION`；本轮不授权实现、
  实验、Edit Mode/Play、API、场景/配置写入、ID/配额消耗或时序参数生效。
