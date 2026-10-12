# P1-VLM-DATA-001 — G0 目录门 + D0 数据引擎（蒸馏章程首个执行批次）

Status: ACCEPTED_WITH_BINDING_CLARIFICATIONS（round 3；round 24 消费
Review round 6 `REWORK_REQUIRED` 并把 F20–F22 返工交给 Implementation；
正式 S3–S5 续跑与 S6–S9/G0/D0 仍未授权）
Author/role: 构思角色（ideation，Fable 池；本会话兼任进度监督视角）
Created: 2026-08-25
Last updated: 2026-09-01
Revision: 2（2026-08-25。回应 Acceptance round 2 §12 AR2-1…5；逐条回应见
§13。**本稿是 BC-C7-8 下最后一次自行修订**；2026-08-26 round 3 已按
§14 接受，未触发用户二选一。revision 1 = 回应 round 1 AR1-1…8，见 §11）
上位章程：`P1-VLM-DIST-001`（`ACCEPTED_WITH_BINDING_CLARIFICATIONS`，
round 3，2026-08-25；设计 v0.3.18）。本批次实现其 §3.1 G0 与 §3.2/
§2.2 D0，**BC-DIST-1…4 逐字随行**（BC-DIST-4：G0/D0 = 零 Play、
零 API、零 GPU 的独立目录/数据合同停点；C1 热身**不在**本批次）。
起草授权：`docs/authorizations.md` 2026-08-25「授权起草」条目。

> **COORD-008 banner（2026-09-02）**：§16–§43 是 COORD-008 之前流程下的
> 逐轮接受记录，保留为历史，不作后续批次的流程范例；后续裁定只追加 BC 表
> 行与「待裁定」问答，不再追加轮次章节。

## 0. 修订索引

### 修订索引（revision 2 ↔ AR2-1…5，最后一次自行修订）

| AR 项 | 落点 | 实质变化 |
|---|---|---|
| AR2-1 F4 反向依赖 | §2.4（谓词）、§2.8、§2.9、§5.1 | 新增只依赖 S1–S5 的具名谓词 `prospective_mother_eligible`；S7 据此算 F4 并冻结候选清单工件，S8 只物化同一清单 + 逐 id 等价断言；簇身份统一为**并簇后最终 atom** `(atom_id, object_id)`，D2 重采样单位不得细于它；附录 B 加口径注记 |
| AR2-2 切分唯一性与外观暴露 | §2.5 | 留出公式改整数算术 `(3n+5)//10`；seed→排列写死为 SHA(seed‖id) 升序；test 指派改全枚举 + 字典序目标向量（整数比较）；**dev 本轮拆定**（≈15% 帧）；D3 机械谓词 + 空集如实报告；删除「布局类携带外观隔离」误导句，新增逐样本 **exposure 矩阵**与冻结措辞（禁称「未见物体」） |
| AR2-3 schema 诚实绑定 | §2.3、§3、附录 A | 动态目标逐 schema 写死：m3 用归档真值框作图像面阻断体（世界坐标仅交叉核验）、scouting 二维框直接作阻断体、无逐帧真值族的扫掠区在画面内时标 `TARGET_UNBOUNDED`；删除「解析当前 Unity 场景」。Revision 2 初始的类别 UNKNOWN 在 round 5 被 BC-DATA-9 收窄：现有冻结构造源为 `car/red`，只有无法绑定的字段仍 UNKNOWN。relocation 平移向量匹配 + 归档容差派生 T_match、恰一匹配否则报错；removal 双向语义分立；附录 A 零重叠；`road_data.json` 按归档 sha 字节绑定 |
| AR2-4 verifier 可复算 | §2.11 | 输入补 `semantic_program`（规范 AST 字节）与 `expected_target_id` + 全部 attempt 绑定，PASS 成为纯函数；新增 `tier ∈ {mechanical, model}` 与审计字段 nullable 规则；夹具补「AST 相等但错 target」「同选对象但 AST 不等」两类 + 标准 PASS |
| AR2-5 审计有限状态机 | §2.7 | S6 开始时一次抽出互斥 panel-0/1/2，**至多 3 个 attempt**、每次进入须登记修复；耗尽 → `AUDIT_EXHAUSTED_FAIL` 返工，连续 2 次 catalog supersession 上交用户；A1 组降级 = 数据结论不计 attempt 失败；全部配额/允许失败条数/分母改整数并在渲染叠加图前打印 |

### 修订索引（revision 1 ↔ AR1-1…8，保留存档）

| AR 项 | 落点 | 实质变化 |
|---|---|---|
| AR1-1 循环 | §2（S0–S9 DAG）、§2.8 | G0/D0 循环拆除：投影/逐帧 catalog/切分改为 G0 **门内测量仪器**（S2–S6），母集与模板等训练可用数据只在 S7 门全过后生成（S8）；禁行边逐条写死 |
| AR1-2 源真值 | §2.2、§2.3、附录 A | 冻结根清单与用途类闭集；逐帧绑定内容哈希 + 采集组 + **归档场景字节**（run 内嵌快照 / manifest sha → 归档字节提供者），当前 config 禁止充当历史布局；create-once + 显式 supersession 协议 |
| AR1-3 切分 | §2.5 | 切分原子 = 复制族∪近重复约束；留出物体从「约 30」改为公式化 **32**；确认集只冻结图像/对象/框、**不生成表达**（明说）；50–100 条手写表达预留对象/帧 |
| AR1-4 F 单位 | §5、附录 B | F1–F4 全部重定义计数单位与分母；revision 0 的 F3 600/150 判定为**帧级重复计数**予以撤回；新数值按下游需求推导，附预扫描量级与 at-risk 披露；冻结后不得回调 |
| AR1-5 投影合同 | §2.4 | world 变换（relocation 平移/移除/phantom）、相机约定（sidecar 基向量 + 内参）、近裁剪、amodal/visible 口径、最小尺寸、θ_occ=0.5 及排序/tie-break/分母全部数值冻结 |
| AR1-6 审计 | §2.7 | 三项审计改为可判定协议：精确样本数、分层、seed 序列、预结果冻结时点、gold 定义（机械轨 = 归档真值框；人工轨 = 操作化判定规则）、失败分母与上限、复审用未见样本 |
| AR1-7 verifier | §2.11 | BC-DIST-2 独立验证层的输入/输出 schema、规范化 AST、语义等价判据（禁「碰巧同对象」）、拒绝原因闭集与审计字段冻结；只建接口与离线夹具 |
| AR1-8 终态授权 | §2.8、§9 | `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA` 终态、采集补数须另立消耗性 work item、接受≠执行授权、`UNITY_NA` 须复核附议，全部写死 |

## 1. 问题和研究价值

章程的确认性实验（verified teacher-language SFT vs matched
template-SFT）的一切都踩在两块地基上：**目录**（哪些车辆的哪些字段
是已验证事实，缺什么就禁什么表达）与**数据合同**（哪些图像可用、
怎么切分、框和表达怎样机械生成与验证）。G0/D0 把这两块地基一次建
好并过独立复核；G0 数字不过预注册下限时按章程以
`INSUFFICIENT_SYMBOLIC_GROUNDING_DATA` 收束或另行申请采集批——
**在花任何 API/GPU 之前知道素材够不够**。

构思侧预扫描（零成本只读，未经复核，只作动机）有两轮：

- 预扫描 1（2026-08-25，revision 0 §1）：24,152 张归档 jpg 中
  23,900+ 带完整位姿 sidecar；车辆 9 类 101 辆；相机站位按 1 m 圆整
  仅约 5 个；约 22k 帧属 SCENE-004 谱系。
- 预扫描 2（2026-08-25，本修订，附录 B）：按**诚实计数单位**（对象×
  站位簇、复制族×对象）重估量级后，revision 0 的 F3「train ≥ 600」
  只有把 5 Hz 近重复帧当独立样本才可能达到，予以撤回；诚实单位下
  全盘量级为站位簇 ~45–60、属性唯一单元 ~90–150、统计簇 ~30–45。
  投影约定已在归档真值框上验证（中心偏差 4–6 px）。

这正是 G0 存在的理由：数字可能不够，而「不够」必须在教师与训练批次
之前、以预注册下限的方式诚实暴露，而不是靠单位膨胀掩盖。

## 2. 范围与交付物：单向工件 DAG（AR1-1）

本批次 = 阶段 S0–S9 的**单向 DAG**。G0 门 = S1–S7；D0 数据生成 =
S8（仅门全过后）；S9 为停点。每个阶段只读**更早**阶段的 create-once
工件与冻结源字节；**禁行边**：

- 任何阶段不得读取序号更大阶段的工件；S7 门判定前不存在母集、模板
  或任何训练可用样本文件；
- S7 任一下限不达 → S8 永不执行，work item 按 §2.8 收束；
- 门判定发出后，S1–S6 工件不得再生（代码缺陷须走 §2.2 supersession
  协议并使 S7 判定作废重出，全程留档）；
- F1–F4 定义与下限在接受轮冻结后**不因任何测得结果回调**（AR1-4）。

### 2.1 S0 冻结常量

本提案 §2.3–§2.7、§2.11、§5 的全部数值与词表即合同本体；实现的第一
个动作是把它们逐字落为 `runtime/dist-data/contract.json` 并
SHA-256 冻结。任何常量改动 = 提案修订 + 重新接受，不存在「实现时
再定」的自由参数。本节常量含：类别映射表与颜色词表（§2.6）、
θ_occ=0.5 与投影常量（§2.4）、站位分箱（§2.4）、pHash 阈值与切分
seed 字符串（§2.5）、审计样本数与 seed 序列（§2.7）、F 定义（§5）。

### 2.2 S1 源清单 inventory（AR1-2）

**冻结根清单**：附录 A 的 pattern 表与用途类映射是**闭集**。S1 枚举
`runtime/**` 与附录 A 点名的 `docs/evidence/` 副本中的全部 jpg 及其
sidecar/truth 文件；pattern 按表序求值且**设计为互不重叠**——S1 对
每个文件断言恰匹配一个 pattern（零匹配或多匹配均**报错停机**，不静默
纳入、不静默跳过）。`runtime/frames/` 当前为空目录，S1 断言其为空；
非空即错。

**逐帧记录**（`inventory@attempt-k`，create-once）：

- 路径、字节数、内容 SHA-256、图像尺寸；
- **source-frame lineage 组**：同一次采集的正式归档/hold/exchange/
  文档副本按（内容哈希相等 ∨ 附录 A 声明的同源关系）折叠为一组，
  组内标 primary 与 duplicates；
- 采集族（附录 A 的 family id）、用途类（附录 A 闭集枚举）、
  scenario 绑定引用（见 S2）、sidecar join 状态（位姿/内参齐全性）、
  truth join 状态（该帧是否有归档目标/干扰体真值）；
- 纳入/排除判定与原因码（闭集：`EXCLUDED_UNBOUND_SCENARIO` /
  `EXCLUDED_NO_POSE` / `EXCLUDED_THIRD_PARTY` / `EXCLUDED_DERIVED` /
  `EXCLUDED_DIAGNOSTIC_CHANNEL` / `EXCLUDED_UNRELEASED` /
  `INVENTORY_ONLY` / `INCLUDED`）。

**不可变输入**：下游每个阶段打开任何源文件前重新计算其 SHA-256 并与
inventory 比对；不一致、缺失或根内新增文件 → **硬错误**。create-once
工件重跑必须字节幂等；因代码缺陷需要重做时，旧 attempt 目录原样保留，
新 attempt 记录 `supersedes` 与原因，**禁止覆盖后仍声称原哈希冻结**；
门判定绑定具体 attempt id。

**用途类 → 资格**（AR1-2「哪些只进 inventory、哪些可进母集及理由」；
逐族映射见附录 A）：

| 用途类 | inventory | 训练母集 | F 下限计数 | test/确认侧 | 理由 |
|---|---|---|---|---|---|
| `VALID_FORMAL` / `VALID_SCOUTING_CLOSED` / `VALID_PARENT_HOLD` | ✓ | ✓ | ✓ | ✓ | 有效归因的正式采集或其台账化 hold；证据链完整 |
| `PROTOCOL_INVALID` / `VOID_TRIAL_HOLD` / `SMOKE` / `CALIBRATION` | ✓ | ✓（仅 train/dev 扩增） | ✗ | ✗ | 图像与位姿真值本身未被否定，但测量协议无效/作废；不得支撑门数字或确认集 |
| `DIAGNOSTIC_HOLD` / `UNRELEASED_PLAY_HOLD` | ✓ | ✗ | ✗ | ✗ | COORD-005：诊断通道产物不进证据链、不作门判定依据；未释放 Play 未获归因 |
| `PREVIEW` / `DERIVED_OVERLAY` / `DOC_COPY` | ✓ | ✗ | ✗ | ✗ | 重编码/叠加/复制品，非一手传感器帧；防近重复污染 |
| `THIRD_PARTY_ASSET` | 仅根级记录 | ✗ | ✗ | ✗ | `runtime/models/**`、`runtime/yoloe/**` 等模型包自带图片，非场景采集 |
| `INVALID_RENDER_PROBE` | 仅记录 | ✗ | ✗ | ✗ | SCENE-006 旧探针 jpg 渲染的是已由 F23 否定保真的灰色替身；只盘点，不得作训练扩增、F 下限或 test |
| `PROBE_TRUTH_ONLY` | 仅记录 | ✗ | ✗ | ✗ | SCENE-006 探针 truth sidecar；配套 jpg 另按 `INVALID_RENDER_PROBE` 排除 |

### 2.3 S2 布局绑定与历史交叉验证（AR1-2）

**场景字节解析**（逐采集族，优先级固定，fail-closed）：

1. run 目录内嵌 `scenario.json` 快照（如 m3 十次 run）→ 直接哈希
   冻结采用；
2. 族内归档 manifest 携带的 `scenario_config_sha256`（如 scouting
   session manifest、rate-study 归档内嵌 `scenario_config.json`）→
   在**归档字节提供者**（run 内嵌快照、`runtime/scenario_config.*
   .hold.json`、族内归档快照）中寻找哈希相等的字节；找到 → 采用；
3. 两者皆无 → 该族 `EXCLUDED_UNBOUND_SCENARIO`，全部帧退出。

**当前 `config/*.json` 一律不得充当历史布局来源**；它们只允许作为
候选「字节提供者」参与第 2 步的哈希相等匹配（相等即字节同一，
不构成「用当前推断历史」）。

**有效布局派生**：基础几何 = `docs/evidence/P1-M3-BODY-001-scene-
geometry.json`（779 实例 world AABB，`P1-M3-BODY-001` 复核链内产出，
S0 哈希钉死；其 `source_scenario_sha256` 与 `scene_adjustments_
applied=true` 表明它是 default 布局的**已调整后**几何）。对任一
布局类：先按 default `vehicle_relocations` 逐条**逆施**，再按该
布局类的归档场景字节**正施**其 relocations。移动一律是**平移向量**
（`new_position − original_xz`，pivot 无关，AABB 整体平移，y 范围
不变）。**匹配合同（AR2-3）**：对每条 relocation，候选 = 同 prefab
基名实例；匹配点 = 实例 AABB 的 XZ 中心；容差
`T_match(entry) = match_tolerance_m + 该 prefab 类实例 XZ 半对角线
最大值`（前者取归档条目自带值，后者由基础几何确定性推导）；要求
**恰一个**候选落入 T_match，零个或多个 → **硬错误**，该布局类绑定
失败、帧全部退出。**removal 双向语义**：(a) default 条目
`remove_from_scene` 且实例不在基础几何中 → 在其他布局类里该实例进
**phantom 登记**（位置 = 归档 original_xz，AABB 尺寸不可恢复）；
(b) 某布局类自身的归档字节 `remove_from_scene` 一个基础几何中存在的
实例 → 该实例在该布局类**不存在**（从目录与遮挡体中一并移除，不是
代理）。产物 `layout@attempt-k`：逐布局类实例 AABB 表 +
relocation/removal/phantom 标记。

**`road_data.json` 字节绑定**：道路关系（`on_route_side` 族）只允许
消费与该布局类归档 scenario 的 `road_data_sha256` **哈希相等**的
字节（来源优先级：族内归档副本 → 其他归档副本 → 当前
`config/road_data.json` 仅在 sha 相等时作为字节提供者）；无匹配字节
→ 该布局类道路关系族标不可用（非致命，如实报告）。

**phantom 登记与动态目标**（唯一性域必须为它们建模；AR2-3 逐
schema 写死）：

- phantom（AABB 不可恢复的实例）：以同类实例 AABB 尺寸的**最大**
  包络为代理体积；只作遮挡体与唯一性冲突体，**永不可指称**；
- **动态目标车字段权威（Acceptance round 5 supersession）**：
  truth/run 快照仍然没有 prefab/类别字段，且仍禁止解析当前
  Unity 场景文件冒充历史身份。但该目标不在场景文件中，而是由
  `TetheredScenarioBootstrap.CreateTarget` 的单一运行时构造链生成；
  F23 后 `TargetVisualFactory` 的两块 cube 几何和两组红色字面量由
  独立 EditMode/分析器 oracle 冻结，git 历史亦证明工厂抽取前后
  M0 构造字面量等价且后续未改。再结合用户逐字事实认定
  「这是一辆纯色的红车」，现有冻结归档族的目标字段定为
  `class=car` / `color=red`。这是已版本化的构造源权威，
  **不是** AR2-3 所禁的读当前场景。其他/未来采集族只有在采集时
  源身份可证绑定到同一冻结构造合同时才继承这两字段；任一
  字段无法绑定时，该字段单独退回 `UNKNOWN` 通配冲突，不得用
  路径名、当前场景或当前 config 补齐。目标仍永不属于目录，
  `referable=false`，只作冲突/遮挡体。
- **有逐帧真值框的族**（m3 十次 run 与各 m3 hold：
  `p1-m3-body-truth/v2` 的 `truth_box_available` + `truth_box_*`；
  scouting 族：truth v1/v2 的 `target_bbox_xywh_norm` +
  `target_visible`/`target_box_status`）：归档真值框**直接作图像
  平面阻断体**加入该帧 `blocking(f)`；框不可用且真值行明确目标不在
  视野/不可见 → 该帧无目标阻断体。**边界 fail-closed**：帧无可 join
  真值行，或真值行示目标在视锥内/可见却无可用框（如
  `intersects_frustum=true` 而 `truth_box_available=false`、
  `target_visible=true` 而 bbox 为 null）→ 该帧同样标
  `TARGET_UNBOUNDED`（语义见下条）。二维框**不充当**三维位置。m3 族的
  `target_world_*_m` 只作**交叉核验**：抽样帧上世界坐标投影点必须
  落在同帧归档真值框内（≥ 90% 命中，否则该族标异常并进 G0 报告）。
- **无逐帧目标真值的族**（rate、scene-val、qual3-leftover、
  CLOCKSMOKE 等）：以归档场景字节的 `target.route_world_m` ⊕ 全体
  目录车辆 AABB 尺寸最大包络构造**全路线扫掠代理区域**；该区域投影
  与视口交面积 ≥ (12 px)² 的帧标 **`TARGET_UNBOUNDED`**——类别
  UNKNOWN 的目标可能在画面内，任何类别程序都可能被其歧义化，故该帧
  **整帧退出母集与全部 F 计数**（fail-closed；仅剩 inventory 与
  站位统计用途，站位簇 F2 亦不计）。

**历史布局交叉验证**（防「基础场景在采集后被改过」）：对每个有归档
真值框的族，用 §2.4 投影器把 layout 中对应对象投到该族抽样帧上，与
归档真值框比对。**冻结阈值**：可检对 ≥ 50 对（不足则全量），对象
中心落入归档真值框比率 ≥ 90%，框对框 IoU 中位数 ≥ 0.5（AABB 投影
对 mesh 紧框的预期差异已含在阈值内）。不达 → 该族布局绑定
`INVALID`，帧全部退出并计入 G0 报告。构思侧已用 m3 arm A 真值抽验
投影约定（中心偏差 4–6 px，附录 B；只作动机）。

### 2.4 S3 投影合同与逐帧 eligible catalog（AR1-5）

对每个 `INCLUDED` 帧 × layout 实例（含 phantom/目标代理）：

- **相机**：直接使用 sidecar 归档的 `camera_position_world_m` 与
  `camera_right/up/forward_world` 基向量（不从四元数重算，避免手性
  歧义）；内参用归档 `intrinsics_px`（v1/v2/v3 均有；同时按
  `vertical_fov_deg`+宽高重算并断言 |Δf| ≤ 0.5 px，不一致即错）。
  相机系：`x=d·right, y=d·up, z=d·forward`；像素
  `u = cx + fx·x/z`，`v = cy − fy·y/z`（top-left 原点，y 向下）。
- **几何**：AABB 八角点；角点 `z ≤ 0.3 m`（近裁剪面）时对 12 条棱
  在 `z = 0.3` 处裁剪后投影裁剪多面体顶点；全部角点在近面之后 →
  `NOT_IN_VIEW`。
- **框口径**：amodal 框 = 投影点集的紧包围盒；visible 框 = amodal ∩
  视口，随后归一化为 top-left `xywh` 并裁剪到 `[0,1]`（沿项目框
  协议）。母集与未来真值框一律取 **amodal-裁剪框**（= 章程 §2.1 的
  八角点投影→视口裁剪语义）。
- **状态闭集**（逐帧逐对象记录恰一个）：`OK` / `NOT_IN_VIEW` /
  `TOO_SMALL`（visible 框短边 < **12 px**）/ `TRUNCATED`（visible
  面积 / amodal 面积 < **0.25**）/ `EXCLUDED_OCCLUDED` /
  `PHANTOM`。
- **遮挡近似（保守排除）**：遮挡体 = 该布局类全部 779 实例 + phantom
  代理 + 动态目标（逐帧真值框或扫掠代理区域）。按相机系 AABB 中心
  距离升序为画家序（tie-break：`scene_object_name` 字典序）；对
  对象 A，若存在更近遮挡体 B 使
  `area(visible_A ∩ visible_B) / area(visible_A) ≥ θ_occ = 0.5`
  → A 记 `EXCLUDED_OCCLUDED`。分母 = A 的 visible 框面积。θ_occ、
  排序与 tie-break 均为 S0 冻结值，**不得在看任何 G0/confirmatory
  结果后调整**。
- **唯一性域**：`referable(f)` = 状态 `OK` 的目录对象；
  `blocking(f)` = visible 面积 > 0 的全部目录对象 ∪ phantom ∪ 目标
  代理。程序执行域 = `blocking(f)`（部分可见的同类车仍然阻断
  唯一性），命中恰一个且为 target 才算唯一。
- **站位簇分箱**（F2/F3 的全局键）：位置 `(⌊x/2⌋, ⌊z/2⌋)`（m）×
  前向方位角 15° 分箱 × 俯角带 `[0°,30°)/[30°,60°)/[60°,90°]`
  （俯角 = `−asin(forward_y)`）。键是世界全局的，跨族自动合并。

产物 `frames_catalog@attempt-k`：逐帧逐对象记录（含该对象在此帧作
潜在 target/干扰体出现的 exposure 字段）+ 逐帧 eligible/blocking 集
+ 逐帧 `TARGET_UNBOUNDED` 旗标（§2.3）+ 同框分布统计。**已注册
风险**：nature/prop 的巨大 AABB 过包围会把画家序遮挡判得偏严，压低
eligible 计数（方向 = 少算不多算，correctness 安全、计数受损）；
审计 §2.7 量化 false-EXCLUDE 率，但下限不因此回调。

**具名谓词 `prospective_mother_eligible(f, o)`（AR2-1，S7 与 S8 的
共同唯一依据）**：只依赖 S1–S5 工件的纯函数——

```
prospective_mother_eligible(f, o) ⇔
  f 为 INCLUDED ∧ 布局绑定 VALID ∧ sidecar join 齐全
  ∧ f 非 TARGET_UNBOUNDED（§2.3）
  ∧ o ∈ referable(f)（状态 OK 的目录对象；留出限制在此不加）
  ∧ §2.9 最小程序规则在 (f, o) 上存在唯一命中程序
    （class-only，或 class+color 且 color 已验证，或
    class(+color)+单一静态关系；执行域 = blocking(f)）
```

谓词本身**不含**用途类/split 条件；F3/F4 = 谓词外延分别限制到
train∪dev / test 侧 **floor-eligible** 帧（§5.1）后的单元/簇计数，
训练扩增（train-aug 用途类）对子在外延中带标记但**永不入 F 计数**。
S7 把谓词全外延 `{(f, o)}` 连同逐对最小程序、用途类、split、
floor 资格标记冻结为 create-once 工件 `mother_candidates@attempt-k`；
S8 不得重算或偏离（§2.9 等价断言）。谓词对「已验证」的读取指 S5
判定 + S6 审计通过后的最终状态表，仍全部先于 S7。

### 2.5 S4 切分冻结（AR1-3）

**切分原子**：采集族先按（scenario 字节 sha × 采集 profile/驱动 ×
路线）并成**复制族**（确定性重放使跨 session 帧近乎重合，如 m3
arm A 五次 trial 为一族）；再对全体 INCLUDED 帧计算 pHash（32×32
DCT 取左上 8×8、中位数阈值、64 bit；Hamming ≤ **8** 为近重复），
跨原子近重复对以并查集合并。**并簇后的连通分量 = 最终原子**，字段
名 `atom_id` = 分量内成员族 id 升序连接串的 SHA-256；`atom_id` 是
切分、F4 统计簇、G0 报告与未来 BC-DIST-3 重采样共用的唯一 lineage
键（AR2-1）。原子是不可分割的切分单位，覆盖：采集谱系、scenario/
布局类、同底层采集全部副本、近重复内容组。**外观暴露如实声明
（AR2-2）**：两个布局类复用同一批 101 辆车，留出对象也会以背景
干扰体身份出现在训练图像中——本合同**不主张任何外观级隔离**，隔离
仅在「指称目标与表达文本」层面（见下）。

**留出物体**（对象级，先于任何表达生成）：按类整数算术
`k_c = max(1, (3·n_c + 5) // 10)`（半数向上、无浮点），9 类合计
**32** 辆（23/20/13/12/9/8/6/5/5 → 7/6/4/4/3/2/2/2/2）；抽取规则
唯一化：对每个对象 id 取 `SHA-256("P1-VLM-DATA-001/heldout/v1" ‖
"/" ‖ scene_object_name)`，类内按（该哈希十六进制串, id）升序取前
k_c 个。**语义**：留出物体作为场景固有内容可出现在任何图像里；但
**永不作训练指称目标、永不出现在任何训练表达文本中**（生成器机械
封禁其 id 与其唯一化所需的属性组合）；其单元保留给确认集与用户
手写表达。n_c 小时按公式仍留 1 辆并如实报告该类训练侧目标稀缺。

**exposure 矩阵（AR2-2）**：S4 产出逐对象 × 逐集的暴露表——
`{train_referent 数, train_distractor_presence 数, test_referent
数, test_distractor_presence 数}`（由 §2.4 exposure 字段汇总），
随 splits 冻结并进 G0 报告。**冻结措辞**：留出对象上的结果只能
表述为「从未作为训练指称目标的对象」分层，**禁止**写成「未见
物体/unseen object 泛化」。

**三互斥集 + train/dev 内分**（原子级指派，(train ∣ dev) ∣
untouched confirmatory test ∣ D3 演示 holdout——章程「三互斥集」的
train/dev 合称一侧，本轮把 dev 一并拆定、不留后续门；四块两两在
原子级互斥）：

- 可见量（允许用于指派）：各原子的**覆盖统计**——帧数、站位簇集合、
  出现对象集合、布局类、用途类资格；**不可见量**（禁止用于指派）：
  唯一性计数、颜色可靠性、审计结果、任何模型输出、任何难度信号；
- **test 指派 = 全枚举 + 字典序目标向量（唯一解）**：对 floor-
  eligible 原子集合的全部非空真子集（预估原子数 ~8–15，全枚举可行；
  S4 断言原子数 ≤ 20，超出即错）逐一计算向量
  `(v1, v2, v3, v4) = (违反「≥ 2 个原子」?1:0, 违反「两个布局类
  都有代表」?1:0, |5·test 帧数 − 总 floor-eligible 帧数|（整数）,
  子集内各原子 key 升序元组)`，其中原子 key =
  `SHA-256("P1-VLM-DATA-001/split/v1" ‖ "/" ‖ atom_id)`；取向量
  字典序最小的子集为 test。布局类只有一类有 floor-eligible 原子时
  v2 恒为 1，对所有候选同罚、不构成歧义；
- **D3 holdout**：从剩余 floor-eligible 原子中取满足机械谓词
  「含 ≥ 1 个完整 run 目录（存在 `frames.jsonl` + 内嵌
  `scenario.json`）且其 post-run 归档 6 成员齐全」的原子里 key 最小
  的一个；无满足者 → D3 holdout 为空集并在 G0 报告具名披露（D3
  批次届时另行解决，不得事后挪用 test）；
- **dev 拆分**：train 侧原子按 key 升序累加帧数，取使 dev 帧数首次
  ≥ train 侧总帧数 15% 的最短前缀为 dev（整数比较：
  `20·dev_frames ≥ 3·total`）；其余为 train。dev 只用于未来 D1/D2
  的选型，test 保持一次性；
- **连带规则**：原子被指派到 test/D3 侧时，其成员中不具 test 资格的
  帧（`PROTOCOL_INVALID` 等）**整体退出**（不得回流训练侧——那是
  近重复泄漏）；
- 产物 `splits@attempt-k` 含逐原子指派、逐帧成员表、exposure 矩阵
  与**机械泄漏断言**（四集间谱系/原子/近重复组交集为空、留出物体
  不在任何训练表达预留中）；断言失败即停机。

**确认集语言（明说，AR1-3）**：本批次**不生成任何确认性测试表达**。
test 侧只冻结 (frame, target, amodal 框) 对与分层清单；表达来源
（用户手写 50–100 条 + 与训练生成器不相交的第三来源 + 盲抽审计）
属 D2 前置批次，届时按 BC-DIST-3 冻结比例。本批次为手写表达**预留**
test 侧留出物体单元清单（对象×帧组合），并冻结「test 图像、crop、
表达、改写与教师产物永不进入训练或模型选择」的机械断言接口。

### 2.6 S5 字段验证目录

- **class**：冻结映射表（S0）：`Ambulance→ambulance`、`Bus→bus`、
  `Car→car`、`Container→container truck`、`Pick up Truck→pickup
  truck`、`Police Car→police car`、`SUV→suv`、`Taxi→taxi`、
  `Truck→truck`；实例按 prefab 前缀机械归类；`_colorNN` 是资产
  皮肤代号，**不是颜色**（章程 R2C-6）。
- **color**：逐实例取其 `OK` 状态观测中距离最近的 **K=5** 帧（不足
  取全部；确定性排序），visible 框每边内缩 20% 后的像素做 HSV
  统计；冻结词表 {white, black, gray, red, orange, yellow, green,
  blue, purple, brown} 与判定带（S0 落数值：V<0.15→black；
  S<0.15∧V>0.85→white；S<0.15→gray；色相带 red[345°,15°)、
  orange[15°,45°)、yellow[45°,70°)、green[70°,170°)、
  blue[170°,260°)、purple[260°,300°)；orange 带且 V<0.55→brown；
  主带占比 < 0.5 → 无主色）。**一致性约束**：同 (prefab, 皮肤代号)
  组的全部实例必须解析到同一颜色词，违背 → **整组**
  `color:UNVERIFIED`；无主色/低置信实例亦 `UNVERIFIED`。
  `UNVERIFIED` 对象退出一切颜色表达（词表 = 已验证字段闭包）。
- **dynamic_state**：目录对象全部为静态场景车辆（布局派生即证）；
  被 relocation 移动过的实例带 `relocated` 标记；动态目标车不属
  目录、只作冲突体。**动态关系表达全批禁止**（章程 U6/BC）。
- **动态目标的 source-verified 字段**：§2.3 所述归档族可用
  `car` / `red` 进入 `blocking(f)`。两组冻结 RGB 均落在本节
  red 色相带，用户事实认定给出语义标签；这不代替目录对象
  的 S5 像素判定 + A1 审计，也不把动态目标纳入 F1 的 101 个对象
  分母/分子。唯一性仍读每个城市目录车辆的最终 S5+S6 字段：
  颜色 `UNVERIFIED` 必须按未知通配，不得当作「已知非红」。
- **static_relations**（只报可用性，无下限）：族定义冻结——
  `nearest_to(ref)`（场景系距离，d1 ≤ 0.8·d2 才有效）、
  `viewer_left_of/right_of(ref)`（帧内 visible 框中心水平距
  ≥ 40 px）、`on_route_side`（依 `road_data.json` join，可用性由
  G0 如实报告）。逐布局类逐族报可用对数。

### 2.7 S6 审计协议（用户人工，门前；AR1-6）

**有限状态机通则（AR2-5）**：每项审计（A1/A2/A3）在 S6 开始时用
冻结 seed 一次性生成**三个互斥 panel**（panel-p 的样本 key =
SHA-256(`P1-VLM-DATA-001/audit/<A#>/panel-<p>` ‖ 样本 id)，全体候选
按 key 升序、按分层配额不放回地顺次填入 panel-0/1/2），三个 manifest
同时 create-once 冻结，**之后**才渲染任何叠加图。attempt-k 使用
panel-(k−1)，**至多 3 个 attempt**；进入下一 attempt 的前置是登记
一条具体修复（缺陷描述 + 代码/数据变更），无修复不得重审。第 3 个
attempt 仍失败 → 该审计 **`AUDIT_EXHAUSTED_FAIL`**：本批次以
`REWORK_REQUIRED` 返回实现侧，重新进入审计必须以 supersession 产出
新 catalog attempt + 全新三 panel；**连续 2 次 catalog supersession
后仍未过 → 上交用户裁定**（继续投入或收束），不存在静默的第三条路。
全部 attempt/panel/判定留档；阈值与配额永不回调；审计通过是 S7 计数
的前置：F1 的「已验证」= S5 判定 + A1 通过。

- **A1 目录审计**（class + color）：
  - 配额：(a) 9 条类别映射逐条确认，允许失败 **0** 条；(b) 类别
    实例 crop **20** 个（每类 ≥ 2，余量按类大小降序补齐），允许
    失败 **≤ 1** 条；(c) 颜色：每个出现于 eligible 数据的
    (prefab, 皮肤) 组各 1 个 crop（组数 G 以实测为准，manifest 打印）
    + 实例 crop **25** 个（分层：布局类 × 距离三分位，格内不足则
    全取、余额按格大小降序转移），实例允许失败 **≤ 1** 条。
  - **组级颜色错不是 attempt 失败而是数据结论**：被用户判错词的组
    **立即永久 `UNVERIFIED`**（本批次内不得复活），不计入 (b)/(c)
    的失败条数；attempt 失败只由映射表错误、实例级错误超限或工具性
    缺陷（错渲染、错对象）构成——这回答「降级组是否仍计错误」：
    **不计**。
- **A2 投影框审计**（双轨，gold 语义写死）：
  - 机械轨：**全量**可检 (帧, 对象) 归档真值对（scouting truth 的
    target/distractor 框、m3 truth 的 target 框）自动比对；通过线 =
    §2.3 交叉验证阈值（中心命中 ≥ 90%、IoU 中位数 ≥ 0.5）；gold =
    采集时 Unity 写盘的真值框。
  - 人工轨：每 panel **200** 框（分层格 = 布局类 2 × 距离三分位 3 ×
    状态 {OK, EXCLUDED_OCCLUDED} 2 = 12 格 × 16 + 8 个按格实测容量
    降序补齐；格内候选不足则全取、余额按同序转移；manifest 在渲染前
    打印实际分母与整数允许失败条数）。gold = 审计人按冻结操作规则的
    判定：(i) 车辆全部可见像素在框内；(ii) 框相对可见范围单边过冲
    ≤ 35%（AABB 松弛容差）；(iii) 对象身份正确；(iv) 标
    `EXCLUDED_OCCLUDED` 的样本确实被遮挡 ≥ 约一半。通过线（整数）：
    总体拒绝 **≤ floor(0.05 × 实际样本数)** 条；false-INCLUDE
    （panel 内 pipeline 标 `OK` 而审计人判「实际被遮挡 ≥ 一半」）
    **≤ floor(0.02 × panel 内 OK 样本数)** 条——分母 = panel 内
    `OK` 样本数，非 200、非全 eligible（方向性：宁可错排除）。
- **A3 唯一性审计**：每 panel **100** 个 (帧, 最小程序, 选中对象)
  叠加样本（分层格 = 程序型 {class-only, class+color} 2 × 布局类 2
  = 4 格 × 25，不足全取、余额转移）；审计人核对被指对象在**画面
  全部车辆**（含目录外动态目标）中确属唯一命中；允许失败 **0** 条
  （零假唯一容忍）；任何一例假唯一 = attempt 失败 → 登记修复 →
  下一 panel。机器侧性质测试（§5.3）先行全过。

用户判定量：每 attempt ≈ 9 + 20 + G(≈25) + 25 + 200 + 100 ≈
**380 项 ≈ 1.5–2.5 小时**（全部首轮通过时只走 panel-0），在章程
G0+D0 行的「目录 ~100 + 标签 ~400」预算内；复审仅重做失败项所属
审计的下一 panel。

### 2.8 S7 G0 报告与门判定（AR1-1/AR1-8）

`g0_report@attempt-k`（create-once，哈希冻结）：F1–F4 按 §5 冻结
定义逐项计算——F3/F4 **只读 §2.4 的 `prospective_mother_eligible`
谓词与 `mother_candidates@attempt-k` 工件**（AR2-1：S7 不读任何 S8
产物，S8 亦不得反向影响门值）；**同表**给出全局与逐 split/逐对象/
逐站位/逐布局类/逐用途类分层分母；同框分布、站位聚类、关系可用性、
排除原因直方图（含 `TARGET_UNBOUNDED` 帧数）、exposure 矩阵、交叉
验证与审计结果全部入报告。

- 全部下限达标 → 门 OPEN，S8 启动；
- **任一下限不达 → 本 work item 以
  `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA` 收束**：S1–S7 工件与报告
  全部保全，S8 永不执行；采集补数只能由用户另立**消耗性** work
  item 授权（本批次不得改场景、加车、移动车辆或启动 Play——章程
  R2C-6 的唯一处置）；
- 门判定后发现 S1–S6 缺陷 → 判定作废，走 supersession 重出，
  原判定与缺陷归因留档。

### 2.9 S8 母集与模板样本（仅门后；D0 数据生成）

- **母集 = §2.4 冻结候选集的物化（AR2-1）**：S8 按
  `mother_candidates@attempt-k` 逐对生成 (帧, target, amodal 框)
  三元组，并对候选 id 集合做**逐 id 字节等价断言**——物化集合与 S7
  冻结外延差一条即硬错误（判定作废走 supersession），S8 没有增删改
  任何候选的权力；train-aug 对子按外延中的标记进入训练侧、不入 F
  计数；test/D3 侧只按 §2.5 冻结对与预留，不配训练表达。
- **模板表达（BC-DIST-1 的 template 侧）**：每个 train/dev target
  恰一条 Tier-1 表达；程序选择 = **最小程序规则**（确定性优先序：
  class-only 唯一 → 取之；否则 class+color（双验证）唯一 → 取之；
  否则 class(+color)+单一静态关系唯一 → 取之；仍不唯一 → 该
  (帧,对象) 不入母集）；渲染经 §2.11 可逆 renderer。教师侧 D2 在
  **同一母集**上生成（本批次零调用）。
- **统计按簇报告**：样本量、单元数、簇数按 §5 单位分层输出；5 Hz
  近重复帧只作训练扩增，从不作独立统计单位。
- 留出物体单元清单 + 用户手写表达预留清单（§2.5）随母集一并冻结。

### 2.10 S9 停点

稳定候选 + 独立复核（强制：新工具 + 数据正确性）；Unity 列拟以
`UNITY_NA`（纯离线批次）申请，**须复核角色在复核文件中附议**方可
用于关闭（AR1-8）。复核范围至少含：DAG 禁行边与 create-once/
supersession 语义、投影与遮挡合同实现、切分泄漏断言、审计协议
执行痕迹、G0 报告数字复算。

### 2.11 Verifier 接口合同（BC-DIST-2 机械半边；AR1-7）

本批次**不调用任何教师/验证模型**；交付冻结接口 + 离线夹具：

- **ontology/v1**：`program = {target: {class ∈ 9 类, color? ∈ 已
  验证词表}, relation?: {type ∈ {nearest_to, viewer_left_of,
  viewer_right_of, on_route_side}, ref: {class, color?}}}`；字段
  闭集，未验证字段/禁用关系（动态关系）在 schema 层拒绝。
- **规范化 AST**：键排序、枚举小写、可选字段缺省化、Tier-1 闭词表
  同义折叠（renderer 词表即闭包，折叠表 = 恒等 + 冻结的别名表）；
  规范化器幂等（`canon(canon(x)) = canon(x)` 性质测试）。
- **语义等价判据**：`canon(parse(expression)) == canon(semantic_
  program)` 的 **AST 相等**；执行结果一致是**必要补充检查**而非
  替代——「当前帧碰巧命中同一对象」单独出现时 verdict 为
  `REJECT(AST_MISMATCH)`。
- **verifier_input/v1（AR2-4：输入足以复算 verdict）**：
  `{expression, semantic_program（规范化 AST 字节，即「应等价于
  什么」）, expected_target_id, frame_ref(inventory id + attempt),
  catalog_ref(frames_catalog attempt), splits_ref(attempt),
  ontology_version}`——PASS/REJECT 由此成为输入 + 被引用冻结工件的
  **纯函数**，任何第三方可离线复算；
  **verifier_output/v1**：`{tier ∈ {mechanical, model},
  parse_status, canonical_ast|null, ast_equivalent: bool|null,
  execution: {selected_object_ids, unique, hits_expected_target}
  |null, verdict ∈ {PASS, REJECT}, reject_reason ∈ {UNPARSEABLE,
  ONTOLOGY_VIOLATION, AST_MISMATCH, EXECUTION_NOT_UNIQUE,
  EXECUTION_WRONG_TARGET, FORMAT},
  audit: {verifier_model_id: string|null, model_version:
  string|null, prompt_sha256: string|null, response_raw_sha256:
  string|null}}`；**nullable 规则入 schema**：`tier=mechanical`
  （Tier-1/纯离线路径）时 audit 四字段必须为 null，`tier=model`
  时必须非 null；PASS ⇔ AST 等价 ∧ 执行唯一 ∧ 命中
  `expected_target_id`。
- **离线夹具**：每个 reject 路径 ≥ 2 条手工构造样例，**必含**
  「AST 相等但执行命中非 expected target →
  REJECT(EXECUTION_WRONG_TARGET)」与「当帧执行同选一个对象但 AST
  不等价 → REJECT(AST_MISMATCH)」两类，另含 ≥ 2 条标准 PASS；
  加 Tier-1 全枚举往返（`parse(render(p)) ≡ p`）性质测试。本合同
  只建接口与夹具，不构成 API、教师数据或 D2 启动。

**新增文件**：`tools/dist_data/`（新目录，纯离线，不被运行时
import）+ `tests/` 对应单测 + `runtime/dist-data/`（gitignored
工件）+ `docs/evidence/P1-VLM-DATA-001-*.md`。**零改动**：
`controller/`、`Assets/`、既有 `config/` 字节、运行时协议。

## 3. 输入、输出与受影响接口

输入（只读）：附录 A 根清单内的 `runtime/**` 归档、
`docs/evidence/P1-M3-BODY-001-scene-geometry.json`（S0 哈希钉死）、
归档场景字节提供者、按归档 sha 绑定的 `road_data.json` 字节
（§2.3），以及 BC-DATA-9 指定的版本化冻结目标构造源权威。
**不读 Unity 场景文件**；目标源身份无法绑定时逐字段按 UNKNOWN 处理。
输出：S1–S9 工件（§2）。真值仅离线消费
（数据工程属评估侧）；在线控制路径零接触；运行时协议零修改。

## 4. 与 v0.3.18 的兼容性

实现设计 v0.3.18 M6 行的「G0/D0 数据合同」批次：章程 §3.1/§3.2/
§2.2 与 BC-DIST-2 机械半边、BC-DIST-4 停点。不触碰 BC-DIST-1/3 的
D2 项（K、δ、seed 数、测试表达来源比例等由 D2 提案冻结，但本批次
的母集/切分/预留结构必须使其可实施——§2.5/§2.9 即为此）。
v0.3.17 运行时实施基线与 `PROJECT_BRIEF.md` 不变。

## 5. 可证伪的验收条件

### 5.1 计数单位与分母（AR1-4，先于数值）

- **floor-eligible 帧**：布局绑定 VALID、用途类 ∈ {`VALID_FORMAL`,
  `VALID_SCOUTING_CLOSED`, `VALID_PARENT_HOLD`}、sidecar join 齐全、
  **非 `TARGET_UNBOUNDED`**（§2.3）、属于对应 split 的 INCLUDED
  帧。train 下限计 train∪dev 侧，test 下限只计 test 侧。
- **站位簇** = §2.4 全局分箱键在 floor-eligible 帧上的非空箱
  （跨族/跨 session 自动合并、不重复计）。
- **属性唯一单元** = (对象 o, 站位簇 s)：∃ floor-eligible 帧 f ∈ s
  使 `prospective_mother_eligible(f, o)` 成立且其最小程序为属性型
  （class-only 或 class+color，所用字段均已验证）。同单元任意多帧
  计 **1**（5 Hz 近重复与副本由此天然不膨胀）。
- **统计簇** = (`atom_id`, 对象)：≥ 1 个 floor-eligible 帧上
  `prospective_mother_eligible` 成立的对（AR2-1：lineage 键 =
  §2.5 并簇后**最终原子**，与 split、G0 报告、附录 B 注记同字段）。
  这就是 BC-DIST-3 「lineage/对象簇」重采样单位的存量清单，F4 直接
  度量未来置信区间的可用簇数；**D2 的重采样单位不得细于
  (atom_id, 对象)**。
- 每个 F 的报告必须同表给出：全局值 + 逐 split/逐类/逐布局类/逐
  站位/逐用途类分层分母（AR1-4）。

### 5.2 预注册下限（拟定值；接受轮冻结后不得由任何测得结果回调）

| # | 定义 | 拟定下限 | 推导依据（下游需求，非磁盘反推） |
|---|---|---|---|
| F1 | class+color 双验证对象数 / 101（对象级；「验证」= S5 判定 + A1 通过） | ≥ **60**，且 ≥ 6/9 类各有 ≥ 1 双验证实例 | 表达词表閉包需要颜色可用的对象过半，否则 template/teacher 两臂词表塌缩为 class-only |
| F2 | 站位簇总数（floor-eligible） | 全局 ≥ **40**；test 侧 ≥ **8** | 视角泛化最低多样性；test 需要跨 ≥ 8 视角箱才能主张非单点评估 |
| F3 | 属性唯一单元 | train∪dev ≥ **60**；test ≥ **25**；test 内留出物体单元 ≥ **8**；类覆盖 train ≥ 5 类、test ≥ 4 类 | train 单元 × 帧扩增 ≈ 10³ 级 SFT 样本的最低独立支撑；test 25 单元 × 每单元多帧/多表达 ≈ 50–100 确认样本；留出层单独可报 |
| F4 | 统计簇 | train∪dev ≥ **25**；test ≥ **10** | BC-DIST-3 cluster bootstrap 的 CI 在 <10 test 簇时不可信；train 簇 <25 时 dev 选型不稳 |

**撤回声明**：revision 0 的 F3「train ≥ 600 / 留出 ≥ 150」按帧级
计数才可能成立，属 AR1-4 点名的近重复膨胀，予以撤回，不作任何
后续基准。

**at-risk 披露（诚实预告，非下限调整依据）**：附录 B 预扫描显示
F4-test（~8–10 vs 下限 10）与 F3-train（~60–90 vs 下限 60）最接近
失败线。Revision 2 的两处修正会**进一步压低**这些计数：(a) F4 的
lineage 键改为并簇后 atom（scout-4 与 qual-3 若并簇，test 侧簇数
再降）；(b) `TARGET_UNBOUNDED`（§2.3）会把无逐帧目标真值族的
朝路线帧整帧剔出 floor——qual3-leftover 正是 test 侧的重要站位
来源，其计数损失幅度只有实测才知道。**这正是门的用途**：不达即走
`INSUFFICIENT_SYMBOLIC_GROUNDING_DATA`，把「要不要花一次采集批」
的决定还给用户，而不是把单位改软或把边界条款删掉。

**Round 4 加强披露（BC-DATA-8.3；已被 round 5 对现有冻结
动态目标的事实裁定 supersede，原文保留作历史）**：即使有可用归档二维框、因而没有
触发 `TARGET_UNBOUNDED`，只要类别 `UNKNOWN` 的动态目标在画面中可见，
它就与每个 target/ref 名词短语作通配冲突；ref 不能唯一解析，关系程序
也不能绕开。因此该帧不存在唯一命中的最小程序，所有
`prospective_mother_eligible` 对为空，F3/F4 不计该帧。m3 十次 run 与
scouting 族的大量可见目标帧会受影响；幅度只能由正式 G0 实测。本条不改
F1–F4 的冻结定义、分母或下限，不达仍按既有终态收束。

**Round 5 supersession 披露（BC-DATA-9）**：对 §2.3 已验证为
`car` / `red` 的现有冻结动态目标，通配规则只保留给仍为
`UNKNOWN` 的字段。因此它只与无色 `car` 或 `red car` 名词
冲突，不与非 `car` 或已验证为其他颜色的 `car` 冲突。同框
城市 `Car` 实例只有在颜色已验证为非红时才能被排除；
已验证为红或颜色 `UNVERIFIED` 都继续冲突 `the red car`。
动态目标始终 `referable=false`：它可以使城市车 target/ref 名词
不唯一，但它自身绝不得因成为唯一命中而被枚举为 ref。
任何已按 round 4 「与全部名词冲突」语义计算的 S7/
`mother_candidates`/G0 判定均作废，原 attempt 保留并按 §2.2
supersession 重出；当前磁盘尚无正式 S1–S8 工件，故本轮不
伪造一个 supersession attempt，只使旧语义下的任何临时计数不得
成为门证据。计数可能回升，幅度仍只能由未来获授权的正式
G0 给出；F1–F4 定义、分母和下限全部不变。

### 5.3 机械正确性

1. 清单/布局/catalog/切分/候选集/报告 create-once、重跑字节幂等、
   supersession 协议生效（含「旧 attempt 保留 + 新 attempt 归因」
   测试）；S8 对 `mother_candidates` 的逐 id 等价断言配必失败测试
   （注入一条偏差即报错）；
2. (train ∣ dev ∣ test ∣ D3) 四块零谱系/原子/近重复交集机械断言
   全过；留出物体零训练表达断言全过；
3. renderer/parser 往返性质测试（程序全枚举）、AST 规范化幂等、
   唯一性执行器性质测试、投影器金标测试（已知几何 + 归档真值框
   子集）全过；verifier 夹具全部 reject 路径覆盖；
4. 全套单测绿（`python3 -m unittest discover -s tests -v`）。

### 5.4 审计与停点

1. A1/A2/A3 按 §2.7 协议通过（含分母、上限、复审规则）；
2. §2.10 停点：稳定候选 + 独立复核通过；`UNITY_NA` 经复核附议。

## 6. 基线与消融

不适用（数据批次）；产出物是 D1/D2 全部臂的共同地基。四臂比较、
δ、seed 数等归 D2 提案（BC-DIST-1/3）。

## 7. 失败模式与资源风险

| 风险 | 处置 |
|---|---|
| F4-test / F3-train 触线（附录 B 预警；atom 并簇与 `TARGET_UNBOUNDED` 会再压低） | 如实走 `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA`；采集补数另立用户授权的消耗性 work item；本批不改场景不 Play |
| 无逐帧目标真值族的朝路线帧被 `TARGET_UNBOUNDED` 整帧剔除（qual3-leftover 受损最大） | 设计使然的 fail-closed；损失幅度入 G0 报告排除直方图；不得为保计数弱化边界条款 |
| 审计三 attempt 耗尽 / 反复 supersession | `AUDIT_EXHAUSTED_FAIL` → `REWORK_REQUIRED` 返工；连续 2 次 catalog supersession 后上交用户裁定（§2.7），无静默续跑 |
| AABB 画家序遮挡过严压低计数 | 保守方向（少算不多算）；A2 量化 false-EXCLUDE；下限不回调；限制节如实入报告 |
| scene-004 布局类含 AABB 不可恢复的 phantom（default 布局 `remove_from_scene` 实例） | §2.3 phantom 登记：代理体积冲突体、永不可指称；相关帧计数受损如实报告 |
| SCENE-004 谱系场景字节解析不齐 | 该谱系帧 `EXCLUDED_UNBOUND_SCENARIO`；F 下限在剩余帧上如实判定 |
| 历史布局交叉验证不过（基础场景曾变动） | 该族布局绑定 INVALID、帧退出；进 G0 报告与限制节 |
| 颜色像素统计受光照/材质干扰 | 冻结采样与判定带 + 组一致性约束 + A1 兜底；不可靠 → `UNVERIFIED` 退出颜色表达 |
| 近重复并簇吞掉 test 第二复制族 | 由 §2.5 机械规则如实发生；后果走 F4-test 下限判定，不得人工拆簇 |
| 资源 | 零 Play、零 API、零 GPU、零模型下载；用户审计 ≈ 380 项 ≈ 1.5–2.5 h（另行授权后执行）；实现/复核为常规池 |

## 8. 建议但不强制的实现范围

`tools/dist_data/{build_inventory,bind_layout,project_boxes,
make_splits,build_catalog,audit_tool,g0_report,gen_mother_templates,
tier1_lang,verifier_contract}.py` 十件 + 单测；实现顺序按 §2 的
S1→S9。S6 审计叠加图渲染进 `runtime/dist-data/audit/`（gitignored）。

## 9. 本稿边界（AR1-8）

- 不含 C1 热身、任何教师/验证模型调用、训练、模型下载、test 表达
  生成；D1/D2/D3 各自另行提案；BC-DIST-1…4 原文优先于本稿任何转述。
- **接受 ≠ 执行授权**：本修订即使获接受，也只代表设计可交接；当前
  账本未授权实现、运行、用户人工审计、C1、模型下载、API/GPU、
  Unity/Play 或 `UNITY_NA`；实施前须另获用户范围授权。稳定候选仍须
  独立复核，`UNITY_NA` 只能由该复核文件附议。
- 附录 B 与 §1 预扫描数字未经复核，只作动机，不进证据链，不作任何
  门判定依据。

## 10. Acceptance review decision

### Acceptance round 1 — 2026-08-25

Decision: **REVISION_REQUESTED**

Rationale:

把既有归档先做零成本目录/数据合同，再决定是否值得进入教师与训练批次，
方向正确；范围也保住了 `P1-VLM-DIST-001` 的零 Play/API/GPU 边界。但当前
稿还不能交给实现角色按字面执行：G0 的颜色 crop、逐帧可见 catalog、唯一
指称计数和 `test` 下限依赖 §2.2 才建立的投影器与切分，而 §2.2 又写成
G0 过门后才启动，形成门内循环；输入真值、split 原子、投影/遮挡合同和
人工审计仍留有会改变样本构成的实现期选择。F1–F4 的统计单位也不足以
阻止 5 Hz 近重复帧把下限冲高。因此本轮不冻结 F1–F4 的数值。

Required revisions:

1. **AR1-1 — 消除 G0/D0 循环，给出唯一工件 DAG。** Revision 1 必须按
   先后顺序列出每个阶段的输入、create-once 输出、门判定和失败后的禁行
   边：至少先冻结源清单，再建立 G0 判定所需的布局/投影/逐帧 eligible
   catalog 与 split 归组，随后才能计算 F1–F4；只有 G0 全过，母集、模板
   样本等 D0 数据生成才可继续。不得一面宣称 D0 在 G0 后启动，一面让
   G0 读取尚不存在的 D0 投影或 `test` 分配；G0 未过时不得先生成可供
   后续训练使用的数据集。
2. **AR1-2 — 冻结可复算的源真值与不可变输入。** 每个纳入 lineage 必须
   绑定图像内容哈希、底层采集组、采集时的 scenario/config/scene 身份、
   camera/pose/truth sidecar 和车辆布局来源；不能把当前可变的 config
   套到旧帧上推断历史布局。正式归档/hold/exchange 副本折叠到同一
   source-frame lineage；缺任一必要绑定即 fail-closed 排除。明确
   valid/void/diagnostic/preview 各类哪些只进 inventory、哪些可进母集及
   理由。下游只消费冻结清单，源字节缺失、改变或新增均须报错，不能静默
   重扫。create-once 工件若因代码缺陷重做，须保留旧 attempt 并用显式
   supersession，禁止覆盖后仍声称原哈希冻结。
3. **AR1-3 — 把三集切分写成防泄漏合同。** 切分原子逐项覆盖采集谱系、
   scenario/arm、target 与干扰体外观、同一底层采集的所有副本以及近重复
   内容组；冻结归组算法、冲突时的合并/排除规则、分层约束、seed 和
   manifest。把“约 30 辆”改成精确数量及按类不可行时的确定性处置，并
   写清留出物体虽可作为场景干扰体出现，却永不成为 train target 或
   train expression 的语义。D0 若只冻结 confirmatory 图像/对象而不生成
   独立来源语言，必须明说；同时为用户已指定的 50–100 条手写确认表达
   预留对象/帧，且 test 的图像、crop、表达、改写和教师产物均不得进入
   训练或模型选择。
4. **AR1-4 — 逐一冻结 F1–F4 的计数单位、分母和防重复规则后再提数值。**
   F1 要说明 60/101 是对象级、对象×lineage 级还是字段级，class/color
   任一不可靠时怎样计；F2 要给出坐标系、2 m 边界、视向角定义/环绕边界
   和同一视角跨 lineage 的合并规则；F3 要定义一个 target 计数究竟是
   frame-target、对象×视角簇还是独立 lineage/对象簇，并禁止 5 Hz 帧或
   副本重复计数，且解释 train 600 与 held-out 150 各属于哪个 split；
   F4 要定义独立 lineage 簇及 train/test 归属。Revision 1 可重提原数字，
   但须同时报告全局与各 split/对象/视角的分层分母；数值只在下轮接受时
   冻结，不得由实现期预跑结果回调。
5. **AR1-5 — 把投影、可见性和遮挡从“实现时冻结”提升为设计合同。**
   写死 world transform（含 relocation、旋转与 scale）、相机 convention、
   AABB 八角点、近裁面/背面/跨视口处置、归一化 top-left `xywh`、最小尺寸
   及 amodal/visible-box 口径；定义完整 eligible catalog 何时包含/排除
   部分遮挡目标。`theta_occ`、距离排序 tie-break 和重叠分母会改变样本
   构成，必须在看 G0 结果前以数值或唯一校准程序冻结，不能交给实现者
   自选，也不能在 confirmatory/test 上调参。
6. **AR1-6 — 把“约 100/200/100”审计改成可判定协议。** 为目录、投影框、
   唯一性分别给出精确样本数、按 lineage/对象/距离/遮挡/表达族的分层、
   抽样 seed/manifest 的预结果冻结时点、人工 gold 定义、分歧裁决、错误
   分母与对应的最大允许失败条数。`IoU>=0.8` 必须说明和哪一种 gold box
   比；“零假唯一”必须在完整 eligible catalog 上复核。审计失败后的修复
   attempt 全部保留，重新审计使用预注册的未见样本或明确全量复核，不得
   以反复重抽或放宽阈值过门。
7. **AR1-7 — 补齐 BC-DIST-2 要求的独立验证层合同。** 本批仍不得调用
   教师或验证模型，但 D0 必须冻结未来 verifier 的输入/输出 schema、
   ontology 与 AST 规范化、语义等价判据、拒绝/失败原因及审计字段；
   “当前帧碰巧命中同一对象”不得替代规范化程序等价。该合同只建接口和
   离线夹具，不构成 API、教师数据或 D2 启动。
8. **AR1-8 — 写死终态、停点与授权边界。** 任一冻结 G0 下限不达时，
   本 work item 以 `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA` 停止并保全报告；
   采集补数只能另立用户授权的消耗性 work item，不能在本批改场景、加车
   或 Play。即使 Revision 1 日后获接受，也只代表设计可交接：当前账本
   仍未授权实现、运行、用户人工审计、C1、模型下载、API/GPU、Unity/Play
   或 `UNITY_NA`；实施前须另获用户范围授权。稳定候选仍须独立复核，
   `UNITY_NA` 只能由该复核文件附议。

Accepted design-document changes:

- **None.** `docs/phase1-single-drone-design.md` v0.3.18、
  `P1-VLM-DIST-001` BC-DIST-1…4、既有运行时合同和所有旧 work item gate
  保持不变。本轮不授权实现、执行、人工审计、C1、模型调用/下载、
  API/GPU、Unity/Play、场景或车辆改动，也不冻结 F1–F4。

## 11. Acceptance round 1（AR1-1…8）逐条回应（revision 1，2026-08-25）

1. **AR1-1**：接受——revision 0 确有门内循环。→ §2 重构为 S0–S9
   单向 DAG：投影器、逐帧 catalog 与切分**移入 G0 门内**作测量仪器
   （S3/S4），母集/模板等训练可用数据只在 S7 全过后生成（S8）；
   「G0 未过不得先生成训练可用数据集」以禁行边写死。
2. **AR1-2**：接受。→ §2.2 冻结根清单闭集与用途类资格表（附录 A）、
   逐帧内容哈希/采集组/sidecar join；§2.3 历史布局只从**归档场景
   字节**解析（run 内嵌快照 → manifest sha 匹配归档提供者 → 排除），
   当前 config 明令禁止充当来源，另加归档真值框的历史交叉验证；
   create-once 幂等 + 显式 supersession + 源字节变动硬错误全部入 §2.2。
3. **AR1-3**：接受。→ §2.5：原子 = 复制族 ∪ pHash 近重复并簇（算法、
   阈值、seed、tie-break 冻结）；留出物体 = 公式化 32 辆 + 类内不可行
   的确定性处置 + 「可出现在图像、永不作训练指称目标/训练表达」语义；
   test/D3 连带规则防无效帧回流；**明说本批不生成确认性表达**，只冻结
   test (帧,对象,框) 与手写表达预留；机械泄漏断言入 §5.3。
4. **AR1-4**：接受，并**撤回** revision 0 的 F3 600/150（帧级膨胀）。
   → §5.1 先冻结四个计数单位（对象级 F1、全局站位箱 F2、对象×站位簇
   F3、复制族×对象 F4——后者即 BC-DIST-3 重采样簇存量）与分层分母
   要求；§5.2 按下游需求重推导数值并给 at-risk 披露；冻结后不得由
   测得结果回调。附录 B 给出预扫描量级（只作动机）。
5. **AR1-5**：接受。→ §2.4 写死相机约定（sidecar 基向量 + 内参一致性
   断言）、AABB 八角点 + 近裁剪棱裁、amodal/visible 双口径与母集框
   语义、12 px/0.25 门、θ_occ=0.5、画家序距离 + 字典序 tie-break、
   分母 = 被遮挡者 visible 面积；relocation 平移/移除与 phantom、
   动态目标代理入 §2.3。全部数值 S0 冻结，禁在任何结果后调整。
6. **AR1-6**：接受。→ §2.7：A1/A2/A3 各给精确样本数（9+20+~50 /
   200 / 100）、分层配额、seed 序列与「manifest 先冻结后渲染叠加」
   时点、错误分母与上限、复审用未见样本或全量。gold 双轨定义取代
   revision 0 悬空的 `IoU>=0.8`：机械轨 gold = 采集时归档真值框
   （阈值 §2.3），人工轨 gold = 冻结操作规则下的审计人判定；假唯一
   在 blocking 全域（含目录外动态目标）上复核，零容忍。
7. **AR1-7**：接受。→ §2.11 冻结 ontology/v1、规范化 AST 与幂等
   规范化器、AST 相等的语义等价判据（执行一致仅为必要补充，单独
   出现即 REJECT）、拒绝原因闭集、审计字段、离线夹具义务；零模型
   调用。
8. **AR1-8**：接受。→ §2.8 写死 `INSUFFICIENT_SYMBOLIC_GROUNDING_
   DATA` 终态与「采集补数另立消耗性 work item」；§9 写死接受 ≠
   执行授权、`UNITY_NA` 须复核附议、预扫描不进证据链。

## 12. Acceptance review decision — round 2（2026-08-25）

Decision: **REVISION_REQUESTED**

Rationale:

Revision 1 已实质闭合 AR1-1…8 的大部分设计债：S0–S9 把训练工件移到
门后，历史配置改为字节绑定，F1–F4 撤回帧级膨胀，投影/遮挡、审计和
verifier 都从实现期选择提升成了设计合同；预扫描风险也没有被拿来放宽
门值。剩余问题集中在五个可执行性缺口，而不是研究方向：F4 的定义仍
读取 S8 才存在的母集；split/held-out 的 seed 与 tie-break 还不能唯一
决定输出；scouting 的二维 truth bbox 被当成三维位置且当前 Unity 场景
没有采集时字节绑定；verifier 输入不足以复算自己的 PASS；审计失败后
仍可无限换未见 seed。这些都会改变样本、真值或门 verdict，不能交给
实现角色解释。本轮继续不冻结 F1–F4。

Required revisions for revision 2:

1. **AR2-1 — 彻底消除 S7→S8 反向依赖并统一 F4 的 cluster 身份。**
   §5.1 目前把统计簇定义为「至少一个**母集合格样本**」的
   `(复制族, 对象)`，但母集按 §2.9 只在 S7 通过后的 S8 才存在，故 F4
   仍无法在 S7 计算。Revision 2 须在 S5/S6 之前定义一个只依赖 S1–S5
   的 `prospective_mother_eligible(frame, object)`（或等价具名谓词），
   S7 用它计算 F4；S8 只能物化同一冻结候选集并做字节级等价断言，不能
   反向决定门值。同时明确统计簇中的 lineage 键究竟是 §2.5 并查集后的
   **最终 split atom** 还是并簇前复制族，并让 split、F4、报告、附录 B
   和未来 BC-DIST-3 重采样使用同一个字段/定义。
2. **AR2-2 — 把 held-out 与 split 算法冻结到唯一输出，并如实表示外观
   暴露。** `round(0.3*n_c)` 的半数舍入、seed→对象排列、test 子集搜索、
   「可行时」判定、多个最优子集的集合级 tie-break、D3 选择及不足分层
   处置都须给唯一算法；只写 SHA seed 或「按 id 字典序」不足以推出同一
   manifest。`train/dev` 要么本轮确定性拆开，要么明确本批只产
   development pool、内部 train/dev 由哪个后续门在任何模型选择前冻结。
   此外，§2.5 的「目标与干扰体外观由布局类维度携带」并不制造外观隔离：
   两个布局类复用同一批车辆，留出对象也按用户既定边界出现在训练图像
   中。保留「留出对象永不作 train target/expression」可以，但须删除
   外观已被 layout 自动隔离的暗示，冻结逐 sample 的 target identity、
   训练中作为 target/仅作为 distractor 的 exposure 矩阵及对应分层报告；
   不得把「见过作干扰体」写成未见对象泛化。
3. **AR2-3 — 按真实归档 schema 绑定动态目标、relocation 与根映射。**
   磁盘核对显示 m3 `p1-m3-body-truth/v2` 有 `target_world_*_m`，但
   scouting truth v1/v2 只有 `target_bbox_xywh_norm`、可见性和
   distractor id；二维 bbox 不能按 §2.3 充当「逐帧位置」。Revision 2
   须逐 schema 写死：有世界坐标时如何构造归档绑定的目标 AABB；只有
   bbox 时如何直接作为图像平面 blocking 体；目标 prefab/class 没有
   采集时字节证据时必须按 unknown fail-closed，不能解析当前可变 Unity
   scene 后冒充历史身份。default 逆施/目标布局正施也须使用归档
   `match_tolerance_m`，零匹配或多匹配均报错，并明确某布局自身再次
   `remove_from_scene` 时该 phantom 是**不存在**而非遮挡代理。附录 A
   的「各 run/staging…」类自然语言根须改成有优先级、零重叠的精确路径
   pattern；`road_data.json` 与任何 scene 字节也须由归档 hash 绑定。
4. **AR2-4 — 让 verifier 输入足以复算 AST 等价和 target 命中。**
   `verifier_input/v1` 当前只有 expression/frame/catalog/ontology，却要求
   输出 `ast_equivalent` 与 `hits_target`；它既没有 target-first
   `semantic_program`，也没有 expected target id，因此 PASS 不可复算。
   Revision 2 须加入不可变的 `semantic_program_ref`（或规范 AST 字节）
   与 `expected_target_id`，并把 inventory/catalog/ontology attempt/version
   全绑定；离线夹具须覆盖「AST 相等但错 target」「当前帧同选对象但 AST
   不等」及正确 PASS。模型审计字段在纯离线/Tier-1 路径是否 nullable 也
   要写成 schema，而不是留给实现者猜。
5. **AR2-5 — 把审计分层、整数门和复审次数变成有限状态机。** §2.7
   目前说下一 attempt 换未见 seed，但未限制 attempt 数，统计上仍可反复
   抽到通过。Revision 2 须在首轮结果前冻结 primary/recheck panel（或
   其他有限序列）、最大复审次数及耗尽终态；耗尽后只能全量复核、返回
   `REWORK_REQUIRED`/设计修订或具名失败，不能继续换 seed。为 A1/A2/A3
   写死每层整数配额、样本不足的确定性合并/全取规则、百分比对应的最大
   失败条数与分母；尤其说明 A1 被降为 `UNVERIFIED` 的组是否仍计错误，
   以及 A2 false-INCLUDE 的分母是全部 200、eligible 子集还是实际遮挡
   子集。全部旧 attempt 继续保留，阈值不得回调。

Disposition:

- 这是本提案的第二次正式 `REVISION_REQUESTED`。Revision 2 是
  BC-C7-8 下最后一次可自行修订；若 Acceptance round 3 仍不能接受，
  接受角色不得发第三次退修，必须上交用户二选一：(a) 接受当前范围并
  逐条列出已知缺口；(b) 关闭为负结果记录。
- `docs/phase1-single-drone-design.md` v0.3.18、`P1-VLM-DIST-001`
  BC-DIST-1…4、F1–F4 未冻结状态及所有既有 gate 保持不变。本轮不授权
  实现、运行、人工审计、C1、教师/verifier 调用、模型下载、API/GPU、
  Unity/Play、场景/车辆改动或 `UNITY_NA`。

Accepted design-document changes:

- **None.**

## 13. Acceptance round 2（AR2-1…5）逐条回应（revision 2，2026-08-25）

1. **AR2-1**：接受——F4 原定义确实读取了 S8 才存在的母集，是 AR1-1
   同类缺陷的残留。→ §2.4 新增只依赖 S1–S5 的具名谓词
   `prospective_mother_eligible`（floor 资格拆出谓词、作计数过滤器，
   train-aug 对子带标记不入 F 计数）；S7 冻结其全外延为
   `mother_candidates` 工件并据此算 F3/F4，S8 只物化 + 逐 id 等价
   断言（§2.8/§2.9）。簇身份统一为并簇后**最终 atom**：`atom_id`
   字段定义入 §2.5，F4 = `(atom_id, 对象)`（§5.1），D2 重采样单位
   不得细于它；附录 B 加「族值是 atom 口径上界」注记；at-risk 披露
   相应加码（§5.2）。
2. **AR2-2**：接受。→ §2.5：留出公式改整数算术
   `max(1, (3n+5)//10)`（合计仍 32）；seed→排列写死为
   SHA-256(seed‖id) 升序；test 指派改**全枚举 + 字典序目标向量**
   （整数比较、子集 key 元组终决，唯一解；原子数上限 20 断言）；
   「可行时」改为恒计入向量的违约分量；**dev 本轮拆定**（train 侧
   key 升序前缀、整数不等式 `20·dev ≥ 3·total`）；D3 改机械谓词 +
   空集具名披露。删除「外观由布局类携带」误导句，新增外观暴露如实
   声明、逐对象 exposure 矩阵（随 splits 冻结、进 G0 报告）与冻结
   措辞（禁称「未见物体」）。
3. **AR2-3**：接受，并承认 revision 1 把 scouting 二维 bbox 误写为
   「位置」、把当前 Unity 场景当历史身份来源两处错误。→ §2.3 逐
   schema 写死：目标类别一律 `UNKNOWN`（无采集时字节证据）；有真值
   框族用归档框作图像面阻断体（m3 世界坐标仅交叉核验），无真值行或
   「在视锥内却无框」的帧同标 `TARGET_UNBOUNDED`；无逐帧真值族以
   路线扫掠区域判 `TARGET_UNBOUNDED`，整帧退出母集与全部 F 计数
   （§5.1 floor 定义同步）。relocation 改平移向量匹配 +
   `T_match = 归档 match_tolerance_m + 类内 XZ 半对角线最大值`、
   恰一匹配否则布局绑定失败；removal 双向语义分立（自身 remove =
   不存在；default remove 他处恢复 = phantom）。§3 删除 Unity 场景
   输入；`road_data.json` 按归档 sha 字节绑定；附录 A 改零重叠精确
   pattern，并借此补上 revision 1 漏列的
   `b2-smoke/attempt1-backlog-race`（497 帧）与 rate-b2-formal 计数
   误记（4×512 → 3×512）。
4. **AR2-4**：接受。→ §2.11：输入补 `semantic_program`（规范 AST
   字节）、`expected_target_id` 与 inventory/catalog/splits attempt
   绑定，PASS 成为纯函数可离线复算；输出加 `tier ∈ {mechanical,
   model}`，audit 四字段的 nullable 规则写进 schema（mechanical 必
   null、model 必非 null）；夹具补「AST 相等但错 target」「同选对象
   但 AST 不等价」两类必含样例与标准 PASS。
5. **AR2-5**：接受。→ §2.7 改有限状态机：S6 开始时一次性生成互斥
   panel-0/1/2 并同时冻结，**至多 3 个 attempt**、每次进入须登记
   具体修复；第 3 次失败 → `AUDIT_EXHAUSTED_FAIL` 以
   `REWORK_REQUIRED` 返工，重启审计须 supersession 出新 catalog +
   全新三 panel，**连续 2 次 supersession 后上交用户**。配额与允许
   失败条数全部整数化（A1：9 映射 0 错、20 类 crop ≤1 错、G 组 +
   25 实例 ≤1 错；A2：200 = 12 格 × 16 + 8 按格容量降序补齐，拒绝
   ≤ floor(0.05·实际数)，false-INCLUDE ≤ floor(0.02·OK 样本数)，
   分母 = panel 内 `OK` 样本数；A3：100 = 4 格 × 25，0 容忍），
   不足格全取 + 余额确定性转移，manifest 渲染前打印实际分母与整数
   上限；A1 组降级 = 永久 `UNVERIFIED` 的数据结论、不计 attempt
   失败（正面回答接受轮问题）。全部 attempt 留档、阈值不回调。

## 14. Acceptance review decision — round 3（2026-08-26）

Decision: **ACCEPTED_WITH_BINDING_CLARIFICATIONS**

Rationale:

Revision 2 已正面闭合 AR2-1…5 的结构性问题：S7 不再读取 S8 母集，F4
统一到并簇后 atom；切分、留出与 dev 有了整数确定算法且不再宣称外观
隔离；动态目标按真实 m3/scouting schema fail-closed；verifier 补入期望
程序与 target；审计换 seed 被限制为有限状态机。对磁盘归档的定点核对也
确认：m3 truth v2 同时有 `target_world_*_m` 与归档二维框，scouting
truth v1/v2 只有二维目标/干扰体框，而归档 `scenario.json` 的 target
只有 track/速度/路线、没有 prefab/class。Revision 2 的 UNKNOWN 类别与
「二维框只作图像面阻断体」方向因此正确。

剩余歧义均可在不改变研究范围、不放宽 F 下限的前提下唯一化：S4 的
split 前资格不能读取尚未产生的 split；m3 动态目标不能冒充静态 layout
AABB-IoU 样本；verifier 的 tier/解析字节必须也属于输入；固定 9 条类别
映射不能同时声称属于三个互斥抽样 panel。以下条款按字面优先于正文冲突
处，实施者不得自行另选解释。

Binding clarifications:

1. **BC-DATA-1 — S7 候选外延与 F 冻结。**
   `prospective_mother_eligible` 的求值只可读取冻结的 S1–S6 工件，绝不
   读取 S8；正文「只依赖 S1–S5」应理解为「定义不依赖 S8」，S6 只可把
   S5 字段降级、不能新增字段或样本。S7 将该最终外延与逐对最小程序写成
   `mother_candidates@attempt-k` 后才计算 F3/F4，S8 只作逐 id 物化与
   等价断言。§5.2 的 F1–F4 数值与全部分母在本轮冻结，任何实测结果、
   审计失败或 atom 合并均不得回调。
2. **BC-DATA-2 — split 前资格、边界终态与 exposure。** S4 新增纯函数
   `pre_split_floor_eligible(f)`：等于 §5.1 的 floor 资格，但删除
   「属于对应 split」这一尚不存在的条件；test/D3/dev/train 的覆盖统计
   一律只从它派生，split 落定后才生成带 split 条件的
   `floor_eligible(f, split)`。可指派 atom 少于 2 个时以
   `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA` 收束；超过 20 个时以
   `SPLIT_ENUMERATION_LIMIT_EXCEEDED` fail-closed，二者均保全已有工件、
   不执行 S8。全部哈希排序的终决键为「哈希原始 32 字节，继以 UTF-8
   sample/atom id 字节」；subset 终决元组也包含 atom id，禁止依赖哈希
   无碰撞假设。`splits` 须保存每个 `(frame_id, object_id)` 在
   train/dev/test/D3 的 `{referent, distractor, absent}` 角色，再汇总成
   逐对象 × 四集 exposure 表；正文四个计数只是一组报告视图，不能省略
   dev/D3 或逐 sample 记录。
3. **BC-DATA-3 — schema 分轨的布局交叉验证。** 历史 layout 验证只用
   能以归档 distractor id 恰一映射到静态目录对象的真值框；按 layout
   class 汇总，使用按 `(SHA-256(frame_id/object_id), frame_id,
   object_id)` 排序的前 50 对，少于 50 对则该 layout 绑定 `INVALID`，
   不以动态 target 补数。m3 动态 target 的 `target_world_*_m` 仅执行
   §2.3 的中心落框率 ≥90% 检查；其归档二维框仍只作 blocker，既不构造
   target AABB，也不参加静态框 IoU 中位数。scouting target 同理只作
   blocker；scouting distractor 只有在 id 恰一映射时才可进入 layout
   验证。任何当前 Unity scene/config 的非哈希同一字节继续禁止参与。
4. **BC-DATA-4 — verifier 的全部决定源进入 input。**
   `verifier_input/v1` 还必须含 `tier`、`ontology_ref + sha256`、
   `parser_ref + sha256`；所有 inventory/catalog/splits 引用均同时带
   attempt id 与工件 SHA-256。`tier=mechanical` 时 model evidence 必为
   null；`tier=model` 时输入必须再带冻结的 raw-response artifact ref +
   SHA-256、model/version/prompt SHA 与 response parser ref + SHA，缺一
   即 `REJECT(FORMAT)`。因此 verdict 是「input + 被哈希引用字节」的纯
   函数，而不是重新调用模型的结果。本批只实现/测试 mechanical 路径与
   model-tier schema 夹具，**不调用模型**；未来 D2 才可在另行授权后
   生成 model-tier 响应工件。
5. **BC-DATA-5 — 审计 panel 的互斥域与容量。** A1 的 9 条类别映射是
   每次 attempt 都重跑的固定穷举 checklist，**不属于**三个互斥随机
   panel；其余 A1 crop、A2 `(frame, object)` 与 A3 `(frame, program,
   object)` 样本以这些完整元组为 sample id，panel-0/1/2 间不得重复。
   所有容量降序并列按冻结的 stratum key UTF-8 字节升序，样本并列按
   `(hash 原始字节, sample id UTF-8 字节)`；panel 按 0→1→2 顺序从
   剩余池填充。确定性转移后仍无法满足 A1 的 20/25、A2 的 200 或 A3
   的 100 个非固定样本配额时，报
   `AUDIT_PANEL_CAPACITY_INSUFFICIENT`，不得缩小分母后作通过判定。
   一次 catalog 最多 3 attempts；原 catalog 加最多 2 次 supersession
   后仍失败即上交用户，故同一审计最多 9 个 panel attempt，不存在继续
   换 seed 的隐含路径。A1 组级永久 `UNVERIFIED` 规则保持不变。

Disposition:

- Revision 2 与 BC-DATA-1…5 作为 G0/D0 批次设计合同接受；正式设计同步
  为 v0.3.19。F1–F4 自本轮起冻结：F1 ≥60 且覆盖 ≥6 类；F2 全局 ≥40、
  test ≥8；F3 train∪dev ≥60、test ≥25、test 留出对象单元 ≥8，类覆盖
  train ≥5/test ≥4；F4 train∪dev ≥25、test ≥10。
- 接受只关闭设计门，不构成实现、离线工件生成、人工审计、C1、教师/
  verifier 模型调用、下载、API/GPU、Unity/Play、场景/车辆修改或
  `UNITY_NA` 授权。预扫描仍只作动机；实际 G0 不达下限时必须按合同收束，
  不得以本轮接受为补采授权。
- 下一步若继续，先由用户另行授权零 Play/API/GPU 的 implementation
  scope；稳定候选仍须独立 Review，人工审计与 `UNITY_NA` 继续走各自门。

Accepted design-document changes: `docs/phase1-single-drone-design.md` v0.3.19
（登记已接受的 G0/D0 子合同、冻结 F1–F4 与零执行授权边界；运行时合同不变）。

## 15. Post-acceptance implementation authorization（2026-08-26）

用户逐字授权「授权进行实现」（`docs/authorizations.md` 当日条目）。该授权
只打开 revision 2 + §14 BC-DATA-1…5 的代码、自动测试、临时 fixture 与
实现者证据范围，允许形成稳定候选后交 Acceptance 确认停点；实现角色不得
修改设计含义或门值。它不打开真实归档上的正式 S1–S8 create-once/G0/D0
工件生成、A1/A2/A3 人工审计、C1、模型/下载/API/GPU、Unity/Edit Mode/
Play、ID/配额、场景修改、`UNITY_NA` 或后续训练/确认性实验。临时 fixture
不得进入正式门证据。

## 16. Acceptance post-implementation ruling — round 4（2026-08-26）

Decision: **STOP_POINT_NOT_CONFIRMED / IMPLEMENTATION_REWORK_REQUIRED**

### 16.1 §4.3.1 停点判定

- 条件 2 已满足：focused 279/279 在两个解释器均通过，全套相对 535-test
  基线新增失败 0；条件 3 不适用（本批零 Unity 行为，且没有已知 Unity
  失败）。
- **条件 1 未满足**：R1 证明冻结根表不能覆盖当前闭集归档，R2 证明一条
  void truth 会被写成 `VALID_FORMAL`。二者都改变 S1 的确定输出，不能以
  「正式工件尚未授权」降格为已知限制。
- 条件 4 尚未形成最终候选：现有候选、证据与风险记录齐全，但须先按
  BC-DATA-6/-7 更新代码、回归测试和实现者证据，再由 Acceptance 重验四项
  条件。**本轮不交 independent Review**；Review 只读返工后的新候选。

返工仍完全落在 2026-08-26 既有 implementation 授权内：只改
`tools/dist_data/`、`tests/test_dist_data_*.py` 与实现者证据；继续禁止
正式 S1–S8 工件、`runtime/dist-data/`、人工审计、C1、模型/API/GPU、
Unity/Play、ID/配额、场景/车辆修改与 `UNITY_NA`。

### 16.2 Binding rulings on R1–R3

6. **BC-DATA-6 — R1 的根闭集补正是阻断返工，不是扩数据捷径。**
   - `runtime/p1-scene-006/probe-baseline-vfov60/frames/*.jpg` 与
     `runtime/p1-scene-006/probe-candidate-vfov40/frames/*.jpg` 各自作为
     精确、互不重叠的 pattern，usage = `INVALID_RENDER_PROBE`，family /
     layout 均为 null，inventory decision = `INVENTORY_ONLY`。两目录各
     107 张（含 prompt jpg）；F23 已否定其运行时外观保真，故不得进入
     train/dev 扩增、F1–F4 或 test。
   - `<RT>/rs3-clock-smoke/phase1-hold/frames/init-box-preview.jpg` 是写有
     绿色初始化框的派生图，usage = `DERIVED_OVERLAY`，family/layout =
     null，decision = `EXCLUDED_DERIVED`；它不得继承同目录 173 张原始
     `frame_*.jpg` 的 `SMOKE` 资格。
   - `INVALID_RENDER_PROBE` 加入用途类闭集，但不新增 inventory reason；
     SCENE-006 truth sidecar 继续为 `PROBE_TRUTH_ONLY`。回归测试须逐 pattern
     钉住 107/107/1，真实归档只读 dry-run 须报告 zero-match = 0、
     multi-match = 0；不得以放宽「恰一匹配」断言闭合。
7. **BC-DATA-7 — R2 必须把 void run truth 从有效 truth 闭集中拆出。**
   A.1 的宽泛
   `runtime/runs/p1-m3-body-001-arm-a-*/m3_body_truth.jsonl` 删除，合法 arm-A
   truth 改为三个零重叠 pattern：trial-1-attempt-4、trial-2-attempt-2、
   trial-[345]，合计恰五份、usage = `VALID_FORMAL`。另加
   `runtime/runs/p1-m3-body-001-arm-a-trial-*-void-attempt-*-hold/m3_body_truth.jsonl`，
   usage = `VOID_TRIAL_HOLD`，family = `m3-armA`，
   layout = default；根级 void truth pattern 保持不变。回归测试必须同时
   断言五份有效 truth 与该 void truth 的恰一匹配和用途类，禁止依赖表序
   掩盖重叠。
8. **BC-DATA-8 — R3 的十项保守确定义全部接受并冻结。**
   1. 路线扫掠代理按逐线段 Minkowski 外包 AABB 与全体目录车辆最大 AABB
      包络构造；斜段保守外包可少算、不得加采样间距常量。
   2. 只有二维框的动态目标没有可证深度，画家序固定为最近（`-inf`）；
      重叠目录对象因此保守排除，限制进入 G0 报告。
   3. 类别/颜色未知按通配冲突；可见动态目标使 target/ref 名词短语均不能
      唯一解析，故该帧无最小程序。§5.2 的加强披露为绑定措辞，F 下限不改。
   4. 关系枚举按 `RELATION_TYPES`；ref 依（类别词升序、无色在前、颜色词
      升序），取第一个令 target 唯一的组合。
   5. phantom 的「同类」只指 §2.6 的九类冻结映射，不是 prefab 级。
   6. 颜色主带须唯一；恰 0.5 的两带并列仍为 `UNVERIFIED`。
   7. BC-DATA-3 排序键的 `frame_id` = inventory 全局唯一路径，不取跨族
      可重复的 sidecar 数字 id。
   8. 场景字节逐帧向上取最近内嵌快照，缺失时才取最近 manifest 的 sha
      提供者；族内解析到多套不同字节即整族 `EXCLUDED_UNBOUND_SCENARIO`。
   9. lineage primary 先按用途类闭集表序，再按路径 UTF-8 字节升序。
   10. S6 对 S5 只可清字段，不能加字段或改变样本集合。

### 16.3 返回 Implementation 的闭合条件

Implementation 须：(a) 落地 BC-DATA-6/-7 与具名回归；(b) 保持
BC-DATA-8 现有语义并补足对应测试/证据指针；(c) 两解释器 focused 全绿、
全套相对基线新增失败 0；(d) 只读真实归档 dry-run 闭合 R1/R2，仍不创建
正式工件。完成后更新实现者证据并返回同一 §4.3.1 停点；Acceptance
确认新候选后才交独立 Review。

## 17. Acceptance new-fact ruling — round 5（2026-08-26）

Decision: **ACCEPTED_WITH_BINDING_CLARIFICATIONS /
BC-DATA-8.3_SUPERSEDED**

本轮不是 round 4 返工复验，也不确认 §4.3.1 停点。它先裁定一条
会改变 F3/F4 计数的新事实：round 4 候选仍不可交 Review，
Implementation 须把本轮与 BC-DATA-6/-7 一起落地后再返回同一停点。

### 17.1 独立磁盘事实复核

1. `TargetVisualFactory` 只创建两个 cube：body `2×1×4 m`、
   roof/cabin `1.7×0.7×2 m`，分别上色 `(0.9,0.12,0.1)` 与
   `(0.65,0.08,0.07)`。两者 HSV 色相均位于 §2.6 冻结 red 带，
   且独立 EditMode、Editor appearance 和 Python oracle 均保有不反读工厂的
   预期副本。
2. git 历史中 M0 `AddCarVisual` 与当前工厂的两组几何/颜色
   字面量相同；后续只抽取为单一工厂，该字面量至今无 diff。
   当前运行时目标构造链也只有 `CreateTarget → AddCarVisual →
   TargetVisualFactory.AddTargetVisual`；Editor probe 是第二个消费者，不是另一条
   运行时目标路径。
3. 定点 truth 中 `target-0` 只有目标 id/可见性/框，没有资产身份；
   同帧 `Vehicle_Taxi (2)` 却带资产式 id。当前 `build_catalog.py`
   因此把动态目标写为 `(class=None,color=None,referable=false)`，
   `_noun_conflicts` 对未知字段按通配处理；这正是本轮要改的已接受适用域，
   不是实现已经做对的声称。

### 17.2 Binding clarifications

9. **BC-DATA-9 — 动态目标源字段、唯一性与 S7 supersession。**
   1. **字段裁定（回答 a）**：成立。对现有冻结归档族，
      `class=car` / `color=red` 是 source-verified 字段。证据基础是
      F23 冻结构造源 + 独立 oracle + M0 至当前的字面量历史等价性
      + 用户逐字认定「这是一辆纯色的红车」。AR2-3 禁的是读当前
      Unity 场景/config 推断历史 prefab；程序构造且历史等价的目标不在
      该禁令内。源身份无法绑定的族/字段仍逐字段回退 `UNKNOWN`。
   2. **BC-DATA-8.3 收窄（回答 b）**：“对全部名词通配”只适用于
      实际仍未知的字段。现有目标 `car/red` 与无色 `car` 和
      `red car` 冲突，与非 `car` 或已验证非红 `car` 不冲突。
      旧 §5.2 加强披露保留但标为 superseded，新披露按本条取代。
   3. **唯一性/F1 耦合（回答 c）**：对城市 `Car` 实例，已验证红色
      与颜色 `UNVERIFIED` 都与动态目标一起冲突 `the red car`；
      只有 S5 像素判定 + S6/A1 最终验证为其他颜色的 `Car` 才可排除。
      动态目标不计入 F1 的 101 个对象，且永不可指称：一个 ref 名词
      只有在冲突集恰一且唯一命中对象 `referable=true` 时才可用。
      若唯一命中的是动态目标，ref 仍不可用。
   4. **S7/F 处置（回答 d）**：任何按旧 BC-DATA-8.3 语义计算的
      S7/`mother_candidates`/G0 判定必须作废，原 attempt 保留，以 §2.2
      supersession 重出。磁盘尚无正式 S1–S8 工件，所以本轮只否定
      旧语义下的任何临时计数，不伪造 supersession 产物。F1–F4 的
      定义、分母、去重单位与全部下限一律不动；只允许候选外延按
      正确语义重算。

### 17.3 实现返回条件增量

round 4 §16.3 全部保留，并增加：(a) 动态目标的 source-verified
`car/red` 记录与源不可证时的逐字段 `UNKNOWN` 回退；(b) 具名回归覆盖
无色 `car`、`red car`、已验证非红 `car`、颜色 `UNVERIFIED Car`
与非 `car` 的冲突矩阵；(c) 唯一命中但 `referable=false` 的动态
目标不得成为 ref；(d) 旧的「unknown class blocker kills every program」测试只可
保留为源身份不可证的 fallback 用例，不得再表示现有冻结目标。
返回后 Acceptance 才同时复验 BC-DATA-6/-7/-9 与 §4.3.1 四项条件。

Disposition:

- 已接受设计同步为 v0.3.21；BC-DATA-8.1/.2/.4–.10 不变，
  BC-DATA-8.3 仅按 BC-DATA-9 收窄。F1–F4 下限不动。
- 本轮只改已授权的 `tools/dist_data/`、`tests/test_dist_data_*.py`
  与实现者证据所需的设计含义；不打开正式 S1–S8、人工审计、
  C1、模型/API/GPU、Unity/Play、ID、场景/车辆修改或 `UNITY_NA`。
- 本轮不交 Review；实现返回前的停点未成立状态不变。

## 18. Acceptance stop-point recheck — round 6（2026-08-26）

Decision: **STOP_POINT_NOT_CONFIRMED / IMPLEMENTATION_REWORK_REQUIRED**

### 18.1 §4.3.1 停点复验

- 条件 2 复验通过：Acceptance 在候选工作树分别用默认 Python 3.14.6 与
  `.venv-yoloe` Python 3.12.13 重跑 focused，均为 **326/326**；真实归档
  只读 dry-run 仍为 29,923 条、zero-match = 0、multi-match = 0，且
  `runtime/dist-data/` 仍不存在。条件 3 不适用：本批没有 Unity 行为或
  已知 Unity 失败。
- **条件 1 仍未满足**：R4-1/R4-2 会把无法按合同恢复的 phantom 代理
  分别变成建筑/道具级包络或零体积遮挡体；R4-3 会在路径出现后把当前
  可变的 `runtime/scenario_config.json` 当成历史内嵌快照。三项都违反
  §2.3 的 same-class proxy 与归档字节 fail-closed 合同，不能因今天的
  归档恰未触发而降格为停点后风险。
- 条件 4 的候选、证据与风险记录存在，但本轮三项 binding ruling 需要
  再改生产代码、具名回归和实现者证据，故第二候选不是最终稳定候选。
  **本轮不交 independent Review**；Review 只读下一次返回的候选。

### 18.2 Binding rulings on R4-1…3

10. **BC-DATA-10 — 未知 phantom 类别必须在代理构造前硬失败。**
    `class_for_scene_object(candidate.prefab_name)` 返回 `None` 时，S2 立即
    抛 `LayoutError`，不执行 `None == None` 的所谓同类筛选，不借用
    building/prop/未映射实例包络，也不生成该 phantom。失败发生在 S2
    create-once 工件写入前；不得新增静默跳过或 UNKNOWN 通配代理。
11. **BC-DATA-11 — 已知类别但同类实例为空同样硬失败。** phantom 的
    代理尺寸只允许来自该冻结类别在目标布局中仍存在实例的逐轴最大半长；
    集合为空时无法证明包络，S2 抛 `LayoutError`。三个半长置 0 不是
    fail-closed，必须删除；不得以点/零面积体继续遮挡、唯一性或 F 计算。
12. **BC-DATA-12 — 内嵌场景快照必须属于归档提供者闭集。** 逐帧祖先搜索
    只有在候选相对仓库路径完整匹配 `roots.SCENARIO_BYTE_PROVIDERS` 的冻结
    pattern、且候选确为该帧祖先时，才可认作 `embedded_snapshot`；精确路径
    `runtime/scenario_config.json` 永久禁止，即使未来 pattern 放宽也不得
    命中。非允许候选既不能绑定也不能遮蔽下一优先级：继续寻找最近的允许
    内嵌快照；仍无则按 manifest SHA 匹配，最后 `EXCLUDED_UNBOUND_SCENARIO`。
    `config/*.json` 继续只能在 manifest 声明 SHA 与字节完全相等时作 provider，
    永不因祖先关系成为内嵌快照。

### 18.3 返回 Implementation 的闭合条件

Implementation 须在既有授权范围内：(a) 逐字落地 BC-DATA-10/-11/-12；
(b) 增加具名回归，分别钉住 unknown-class phantom 硬失败、known-class
空集合硬失败、根级可变 config 单独存在时仍 unbound、可变 config 与有效
manifest 同时存在时走 manifest、合法 run 内嵌快照仍优先；(c) 在修复前
候选上证明这些具名回归按对应缺口失败，修复后两解释器 focused 全绿、全套
相对既有基线新增失败 0；(d) 重跑真实归档只读 dry-run，确认现有 29,923 条
分类不变且不创建正式工件；(e) 更新实现者证据与准确 Review 范围后返回同一
§4.3.1 停点。

Disposition:

- 已接受设计同步为 v0.3.22；BC-DATA-1…9、F1–F4 定义/分母/下限与
  动态目标 `car/red` 裁定均不变。
- 本轮返工仍只覆盖 `tools/dist_data/`、`tests/test_dist_data_*.py` 与
  实现者证据；不打开正式 S1–S8、人工审计、C1、模型/下载/API/GPU、
  Unity/Play、ID、场景/车辆修改或 `UNITY_NA`。

## 19. Acceptance stop-point confirmation — round 7（2026-08-26）

Decision: **STOP_POINT_CONFIRMED / REVIEW_PENDING**

### 19.1 §4.3.1 四项条件

1. **范围和接口已冻结。** 第三个候选逐字落地 BC-DATA-10/-11/-12：未知
   phantom 类别与已知类别无存活同类实例均在代理构造、create-once 写入前
   硬失败；内嵌快照只认冻结归档 provider，且可变根级
   `runtime/scenario_config.json` 永久禁止。生产 diff 仍限于获授权的
   `tools/dist_data/`，测试、实现者证据与状态记录；BC-DATA-1…12、F1–F4
   和设计 v0.3.22 均不再留实现期选择。
2. **自动测试与证据可复现。** Acceptance 独立重跑 focused，默认 Python
   3.14.6 与 `.venv-yoloe` Python 3.12.13 均为 **342/342**；钉死环境全套
   877 项仅有两项既有 CSRT/opencv-contrib 失败，默认环境全套 772 项仅有
   九项既有 cv2/numpy 导入错误。真实归档只读 dry-run 仍为 29,923 条、
   24,154 images、5,769 truth、19,754 lineage，zero-match = 0、
   multi-match = 0，五项分类计数不变，且 `runtime/dist-data/` 不存在。
   在一次性工作树把生产修复恢复到上一候选后，轮 6 文件恰有 **9/16**
   失败，分别命中未知类借用包络、同类空集零体积和可变 config 绑定/遮蔽；
   恢复本候选后工作树重新干净。
3. **Unity 条件不适用。** 本批是纯离线数据工具，未改变 Unity 行为，也无
   已知 Unity 失败；这里只确认停点条件 3，不裁定工作项的 `UNITY_NA`。
4. **候选、证据、状态和复核范围齐备。** 实现者证据 §10 闭合 §18.3
   (a)–(e)，复核范围由 §6、§8.6、§10.5 共同组成；当前没有未决实现风险
   或退回项。候选与本接受记录一并提交、推送后交独立 Review。

### 19.2 Disposition

- 确认第三个候选为稳定候选，Overall 置为
  `STOP_POINT_CONFIRMED_REVIEW_PENDING_R7`，交独立 Review 在一次性工作树
  新鲜重读并覆盖**整个工作项生产 diff**，不得只看最后一轮补丁。
- 本轮没有签发 Review verdict，也不授权正式 S1–S8 工件、人工审计、
  D1–D3/C1、模型/下载/API/GPU、Unity/Play、任何 ID、场景/车辆修改或
  `UNITY_NA`。Review 结论仍须由接受角色另轮归因。

## 20. Acceptance consumption of Review round 1 — round 8（2026-08-26）

Decision: **REWORK_ATTRIBUTED / IMPLEMENTATION_REWORK_REQUIRED**

### 20.1 Finding 分级复判与归因

- 同意 Review 的 **F1 = CLASS_1**、**F2–F10 = CLASS_2**。Acceptance 用候选
  生产路径独立复算真实归档绑定，结果与 Review 相同：detect-scout1 与
  scene-val 之外的 6 个 family 全部 unbound；问题不是数据下限自然失败，
  而是 BC-DATA-8.8 的逐帧祖先搜索与 §2.3、附录 A.2 自相矛盾。F1/F8/F9
  先按下列 BC-DATA-13/-14/-15 唯一化；其余 finding 不需要重新构思，按
  Review 的失败行为与 BC-DATA-16…19 返 Implementation。
- **C3-1 升格为 CLASS_2，原逐字补丁不应用。** 它改动 LOC 数字，按
  workflow §4.4 的数字文字规则最低 CLASS_2；补丁还会把可运行时派生的
  候选标识写入手维护证据，违反 COORD-007 R7。Implementation 应删除
  §6 的手维护 LOC 总数，改为指向 Review §0 的当轮实测范围；本项无稳定
  行为断言，标 `NOT_MECHANIZABLE`，闭合以定点复看证据 §6。
- **C3-2 维持 CLASS_3 并已逐字应用**：实现证据 §4-1 现在区分第一候选
  的 S1 停机、后续 S1 只读 dry-run 与从未正式运行的 S2–S8；不改数字、
  判据、ID、终态或执行授权。
- Review 观察项中，歧义 manifest 静默跳过父级继续绑定、畸形 m3 truth
  被当作不可见，均是 fail-open，分别并入 F1/F2 的 CLASS_2 返工；其余
  观察项保持非阻断，允许同批清理但不作为停点条件。
- Review 对纯离线范围的 `UNITY_NA` 附议成立。本轮记录该分类资格；它只
  关闭 Unity 列，不关闭任何阻断 finding。若返工越出 `tools/dist_data/`、
  对应测试与证据范围，附议自动失效并须重新 Review。

### 20.2 Binding rulings

13. **BC-DATA-13 — 场景绑定以归档 source unit 为唯一性域，BC-DATA-8.8
    被本条 supersede。**
    - `family` 是附录 A 的报告/谱系标签，不是「必须只有一个 scenario
      SHA」的绑定域。`source_unit` = 附录 A 某个具体 capture root 实例
      （拥有 `frames/` 的归档目录，或表中点名的 flat hold）；每帧先绑定
      source unit，再得到 `scenario_partition = (family, scenario_sha256)`。
      同一 family 出现多个合法 SHA 时保留为多个 partition，不得整族退出；
      只有无法唯一绑定的 source unit 退出。S4 复制族仍按 §2.5 的
      `(scenario SHA × profile/驱动 × 路线)` 合并，不能退回宽泛 family。
    - source unit 内先按 BC-DATA-12 搜最近合格祖先快照/manifest；缺失才走
      **闭集关联**：(a) m3 post-run、B3 residue hold 与 arm-A void hold 只
      通过附录 A root 模板映射到对应 `runtime/runs/<run-id>/scenario.json`
      或该 run manifest，禁止模糊名称/全库最近匹配；(b) 附录 A.2 的三个
      family 以表头点名的 `runtime/scenario_config.p1-scene-004.hold.json`
      为归档 provider，前提是 source unit 的归档 `scenario_id` 恰为
      `p1-scene-004`，任何已有 manifest/快照必须与该 provider 字节一致；
      (c) rate 等其他 source unit 只读自身归档树内的快照/manifest，无唯一
      SHA 的 unit 保持 unbound，不借同 family 邻居补齐。
    - 单个 manifest 内零个 SHA 视为无声明；多个互异 SHA 是歧义硬失败，
      **不得**跳过并继续父级搜索。`config/*.json` 仍只能在归档声明 SHA
      相等时作字节 provider；可变 `runtime/scenario_config.json` 永久禁止。
    - layout 几何按**精确 scenario SHA**派生，`layout_class` 只作报告分层。
      逆施 default 的唯一来源是基础几何自身的
      `source_scenario_sha256` 对应的唯一 provider，禁止取「首个 BOUND
      default family」。随后对每个 scenario partition 正施其自身
      relocations；不同 relocation 集互不使对方或 scene-004 失效。
14. **BC-DATA-14 — 审计 key 显式保留 `/` 域分隔。** §2.7 公式修正为
    `SHA-256(UTF8("P1-VLM-DATA-001/audit/<A#>/panel-<p>") ‖ UTF8("/") ‖
    UTF8(sample_id))`，随后仍以 `(hash 原始字节, sample_id UTF-8 字节)`
    终决。选择带分隔符是为消除 seed/id 边界拼接歧义，不是追认当前输出；
    当前没有任何正式 panel，故无 supersession 对象。
15. **BC-DATA-15 — 三处图像空间「距离」统一为相机前向深度。** 画家序、
    S5 每实例最近 K=5 帧、A1/A2 距离三分位均取对象 world AABB 中心的
    `z_depth = dot(center_world − camera_world, camera_forward_world)`（米），
    不是欧氏距离。理由是三者服务投影尺度/遮挡，z 才是针孔投影分母；
    欧氏距离会把横向偏轴混进尺度。画家序 tie-break 仍为 object id UTF-8；
    K=5 同深度按 inventory 全局 frame id；三分位先按 `(z_depth,
    sample_id UTF-8)` 排序。二维动态 blocker 的 `-inf` 规则不变。
16. **BC-DATA-16 — 遮挡几何域与语言对象域分离。** `occluders(f)` 保留
    全部静态场景 AABB + phantom + 动态 blocker，专用于画家序遮挡；
    `blocking(f)` 只含 visible 的九类车辆目录对象 + phantom + 动态目标，
    `referable(f)` 只含状态 OK、字段合规的九类车辆目录对象。building/
    nature/prop 永不进入 blocking/referable/exposure，却仍能遮挡车辆。
    m3 truth 缺 join，或同时缺可见性证据且无可用框时是未知，不是不可见，
    必须置 `TARGET_UNBOUNDED`；不得静默省略 blocker。
17. **BC-DATA-17 — ref 字段验证与留出禁令两侧对称。** 带颜色的 ref spec
    只有该 referent 自身 `color_status=VERIFIED` 且词值相等时才可匹配/
    枚举；`UNVERIFIED` 仍可按未知通配阻断唯一性，但绝不能被选成任意颜色
    ref。每个关系候选须冻结 `resolved_reference_object_id`。train/dev
    表达若 target 或 resolved ref 为 held-out object，或其唯一化属性组合
    会把 held-out object 写入文本，一律硬拒绝；S4/S7/S8 的泄漏断言同时
    检查 target 与 ref。
18. **BC-DATA-18 — removal 与布局前提继续 fail-closed。** 逆施 default
    removal 判断「原实例仍存在」时只允许 AABB 中心距 `original_xz_m`
    `≤ match_tolerance_m` 的同 prefab 实例；零个即登记 phantom，多个硬错，
    不得再加类内半对角线让邻居冒充被移除实例。任一 scenario partition
    的 relocations/默认逆施前提不唯一或不可证时，只使该 partition
    `INVALID`；不得从字典序首个文档派生其他 partition。
19. **BC-DATA-19 — dropped、splits 与 S8 单位必须可物化。** S7 对因
    test/D3 连带规则退出的候选写显式 `split_role=dropped` 与原因，不抛
    split 缺失错误；`splits` 按 BC-DATA-2 保存逐 `(frame_id, object_id)`
    四集角色和逐对象 × 四集 exposure。S8 每条三元组物化 `station_key`，
    `unit_count` = distinct `(object_id, station_key)`，不得再以 frame id
    充当 §5.1 属性唯一单元。

### 20.3 Implementation 返工与回归闭合

返工继续落在 2026-08-26 已授权的纯离线范围：`tools/dist_data/`、
`tests/test_dist_data_*.py`、实现者证据和必要状态记录。至少增加并在修复前
候选证明失败、修复后通过的具名回归：

- F1：`test_scout4_family_binds_via_family_manifest`、
  `test_m3_armA_family_binds_via_run_snapshot`、
  `test_rate_family_partitions_by_scenario_sha`、
  `test_ambiguous_manifest_hard_fails_without_parent_fallback`；
- F2/F3/F4：`test_non_vehicle_occluder_never_enters_language_domain`、
  `test_unverified_ref_color_cannot_resolve_or_enumerate`、
  `test_held_out_reference_is_rejected_and_persisted`、
  `test_malformed_truth_without_visibility_evidence_is_target_unbounded`；
- F5：`test_neighbor_cannot_suppress_default_removal_phantom`、
  `test_default_divergence_cannot_seed_other_layout`；
- F6/F7：`test_dropped_frame_candidate_freezes_with_dropped_marker`、
  `test_splits_persist_sample_roles_and_four_way_exposure`；
- F8/F9/F10：`test_audit_panel_key_uses_frozen_slash_separator`、
  `test_painter_order_uses_camera_forward_depth`、
  `test_color_and_audit_distance_use_camera_forward_depth`、
  `test_s8_unit_count_is_object_station_not_object_frame`。

fixture 必须调用生产路径或消费归档真实字节副本，遵守 workflow §4.4，不能靠
手写 JSON 状态绕过。实现者还须：(a) 删除实现证据 §6 的手维护 LOC 数字并
定点闭合升级后的 C3-1；(b) 两解释器 focused 全绿、钉死环境全套相对既有
基线新增失败 0；(c) 只读真实归档重跑 S1 + S2 绑定诊断，逐 source unit/
scenario partition 报告，证明 m3 与附录 A.2 不再因非祖先目录整族退出，
rate 的不同 SHA 分区保留而非互相毒化；(d) `runtime/dist-data/` 仍不存在；
(e) 更新完整 Review 范围后回同一 §4.3.1 停点。

### 20.4 Disposition

- 已接受设计同步为 v0.3.23；BC-DATA-13 supersede 8.8，BC-DATA-14/-15
  裁定 F8/F9，BC-DATA-16…19 唯一化其余返工。F1–F4 定义、分母、下限、
  动态目标 `car/red` 与 BC-DATA-10/-11/-12 的 fail-closed 边界均不变。
- Overall → `IMPLEMENTATION_REWORK_REQUIRED_R8`。Review round 1 的
  `REWORK_REQUIRED` 保留；`UNITY_NA` 只作为已附议的分类记录，不是通过。
- 本轮不授权正式 S1–S8/G0/D0 工件、人工审计、D1–D3/C1、模型/下载/
  API/GPU、Unity/Play、任何 ID、场景/车辆修改，也不改变
  `P1-VLM-DIST-001` 的独立章程边界。

## 21. Acceptance stop-point recheck — round 9（2026-08-27）

Decision: **STOP_POINT_CONFIRMED / REVIEW_PENDING**

### 21.1 §4.3.1 四项条件

1. **范围和接口已冻结。** 第四候选把 Review F1–F10 的实现返工与候选提交后
   自查出的四条阻断缺陷全部收在已授权的 `tools/dist_data/`、
   `tests/test_dist_data_*.py`、实现者证据和必要状态记录内；相对 Review
   round 1 候选的 PLAY_GOVERNING diff 只有 8 个 `tools/dist_data/` 文件与
   两份具名回归文件（1,415 insertions / 158 deletions）。
   `controller/`、`Assets/`、`config/`、`ProjectSettings/`、packages lock 与
   运行时合同零改动；BC-DATA-13…19、F1–F4 和设计 v0.3.23 均无待决实现期选择。
2. **自动测试、真实归档确定输出与阻断回归可复现。** Acceptance 独立重跑
   focused：Python 3.14.6 与钉死环境 Python 3.12.13 均为 **380/380**。
   钉死环境全套为 **915** 项，仍只有两项既有 CSRT/opencv-contrib 环境失败
   （1 failure + 1 error，另 1 skip），新增失败 0。只读 inventory 精确复现
   29,923 条、zero/multi-match 均为 0，五类 disposition 不变；内存注入 S1
   载荷后走生产 `build_layout` 的 S2 全链，**9/9 scenario partition 均 BOUND**，
   每个 779 实例，phantom 为冻结的 0/3 分布，绑定 **23,549/23,706 = 99.3%**，
   default 逆施前提来自字节相同的冻结 provider。全程零工件，
   `runtime/dist-data/` 前后均不存在。
   阻断 finding 的修复前失败通道也由 Acceptance 亲自闭合：在两份一次性
   隔离 worktree 中分别 `git revert -n` 两个修复提交并保留对应具名测试：
   round8 **17/24 红**（13 failures + 4 errors），恢复后 24/24；follow-up
   **10/14 红**（6 failures + 4 errors），恢复后 14/14。两树恢复干净后删除，
   主工作树实现文件零字节改动。BC-DATA-14/-15 的两条修复前通过用例仍只算
   对既有正确实现的钉桩，不虚称回归失败。
3. **Unity 条件不适用。** 返工仍是纯离线工具，不改变 Unity
   行为且无已知 Unity 失败；Review round 1 的 `UNITY_NA` 附议继续适用，但
   这里只确认停点条件 3，不据此关闭 work item。
4. **候选交接齐备。** 实现者证据 §11.6/§11.7、
   Review round 1 文件、状态板、未验证风险与本接受记录齐备；本记录提交并
   推送后，Review 从 git 与复核文件运行时解析候选，覆盖 Review round 1
   候选之后的全部 PLAY_GOVERNING diff。

### 21.2 Disposition

- Overall → `STOP_POINT_CONFIRMED_REVIEW_PENDING_R9`，交独立 Review round 2。
  开轮资格成立：相对 Review round 1 候选的 PLAY_GOVERNING diff 非空。
- 未验证风险不被绿灯掩盖：157 个 INCLUDED 帧仍不落在已绑定 partition；正式
  S1–S8/G0/D0 工件、人工 audit、F1–F4 门值与真实训练数据均未生成，且独立
  Review 尚未通过。Review 必须独立复算真实归档 S1→S2→逐 partition 几何，
  不只重跑单测。
- 本轮不签发 Review verdict，不关闭 work item，也不授权正式工件、人工审计、
  D1–D3/C1、模型/下载/API/GPU、Unity/Play、任何 ID、场景/车辆修改或新的
  `UNITY_NA` 分类。

## 22. Acceptance consumption of Review round 2 — round 10（2026-08-27）

Decision: **REWORK_ATTRIBUTED / IMPLEMENTATION_REWORK_REQUIRED**

### 22.1 Finding 分级复判

- **F11：同意 CLASS_2。** `sample_roles_from_entries` 单体存在不等于 S4
  生产路径接线成立；非空 catalog 仍可落出空 roles/exposure，违反
  BC-DATA-2/-19 的不可省略成员。返 Implementation，使角色装配在生产入口
  不可绕过，并以 Review 点名的端到端具名回归闭合。
- **F12：同意 CLASS_2，并以 BC-DATA-20 裁定范围。** BC-DATA-13 (b) 的
  「任何已有 manifest/快照」不能收窄为 unit 根层；真实 scout-3 旁支
  `session/manifest.json` 正位于该 source unit 自身归档子树，且是 round 1
  已点名的族内声明。今日字节一致只证明当前数据未触发，不能许可潜伏的
  异 SHA 被 sidecar + 点名 provider 掩盖。
- **F13：同意 CLASS_2。** `_self_removed` 与 F5(a) 同构；半对角线不得在
  正施侧重新成为邻居冒充容差。返 Implementation，按 Review 的 production
  fixture 与具名回归闭合。
- **F14：同意 CLASS_2 / `NOT_MECHANIZABLE`。** 数字文字最低 CLASS_2 的
  常驻规则适用；将 round8 测试模块 docstring 的「十二条」定点改为
  「十六条」，闭合只作逐字复看，不虚构行为回归。
- **C3-3：同意 CLASS_3。** 只删除实现证据 §11.2 文件列中未改动的
  `audit_tool`，不改变任何数字、哈希、ID、判据或 disposition；本轮按
  Review 的逐字补丁应用。

### 22.2 BC-DATA-20 — F12 的「已有 manifest/快照」检查域

BC-DATA-20 只澄清 BC-DATA-13 (b) 的附录 A.2 关联，不扩成全仓扫描，也不
改写 (a) m3 关联或 (c) 其他 source unit 的绑定合同：

1. **边界是当前 source unit 自身的归档子树。** 对附录 A.2 三个 family，
   从 `roots.source_unit_for(frame_path)` 得到唯一 capture root；一致性检查
   只遍历该 root 及其全部后代，禁止读取兄弟 unit、同 family 邻居或仓库
   其他位置。解析后的物理路径不得越出该 root；不得跟随越界链接补证。
2. **证人闭集。** 检查域包含：(a) 子树内任意深度、basename 恰为
   `manifest.json` 的归档 manifest；(b) 子树内任意深度、同时满足冻结
   `SCENARIO_BYTE_PROVIDERS` / `is_allowed_embedded_snapshot` 判据的内嵌
   scenario 快照。其他 JSON、frame sidecar 和 truth 不因文件名相似进入
   这项字节一致性集合；sidecar 只保留既有 `scenario_id` 前置证明职责。
3. **一致性判据。** 每份可读 manifest 中每个非空
   `scenario_config_sha256` 声明，以及每份合格快照的实测字节 SHA，必须
   全部等于 A.2 点名 provider 的实测 SHA。多路径的同字节副本允许；根级、
   祖先或最近文件没有覆盖旁支矛盾的优先权。manifest 内零个 SHA 仍按
   BC-DATA-13 (v) 视为无声明；多个互异 SHA 仍是既有歧义硬失败。
4. **不可证即不关联。** 域内 manifest 无法读取/解析，或任一非空声明/
   合格快照与 provider 不一致时，(b) 关联不成立，该 source unit 以确定性
   原因和排序后的见证路径记为 `EXCLUDED_UNBOUND_SCENARIO`；不得再由 frame
   sidecar、点名 provider、父级或邻居回退为 BOUND。只退出该 unit，不毒化
   同 family 的其他 unit 或其他 scenario partition。
5. **成功条件不放宽。** 只有既有 `scenario_id == p1-scene-004` 前置成立，
   且上述域内全部显式证人一致（或不存在显式证人）时，才可继续采用 A.2
   provider。该规则不改变 provider 字节、现有 9 个 partition、F1–F4、
   计数单位或任何冻结阈值。

### 22.3 返回 Implementation 的闭合条件

1. F11/F13 按 Review round 2 的具名回归逐字闭合；F14 定点复看；C3-3 已由
   Acceptance 应用，不再返实现。
2. F12 至少新增具名回归
   `test_a2_nested_manifest_consistency_is_enforced_across_unit_subtree`：fixture
   消费 scout-3 的真实 frame/sidecar、嵌套 manifest 与 A.2 provider 字节；
   正例保持 BOUND，负例使用另一份**真实归档、字节不改写**且声明不同 SHA
   的 manifest 置于相同旁支位置，必须使 (b) 关联返回 unit UNBOUND。禁止
   手写 JSON 状态或只测新 helper 而绕过 `resolve_frame_scenario` 生产入口。
3. 另加合格子树快照异字节的 production-path 回归，证明 `_unit_subtree_snapshot`
   的矛盾不能在 A.2 fallback 中被掩盖；这只是 BC-DATA-20 的同一一致性集合，
   不把 F12 泛化到 (a)/(c)。
4. 修复后重跑两解释器 focused、钉死环境全套、只读 inventory 与真实归档
   S1→S2→逐 partition 几何；九个现有 partition、23,549/23,706 绑定与
   0/3 phantom 分布不得因本修复漂移。`runtime/dist-data/` 前后均须不存在。
5. 每条可机械化阻断 finding 仍须满足 workflow §4.4 的修复前必失败通道；
   更新实现者证据和完整 Review 范围后回同一 §4.3.1 停点。

### 22.4 Disposition

- Overall → `IMPLEMENTATION_REWORK_REQUIRED_R10`。F11–F14 返 Implementation；
  F12 的范围歧义由 BC-DATA-20 闭合，不需要用户扩大范围或另拨资源。
- Review round 2 的 `REWORK_REQUIRED` 与 F11–F14 保留；F1–F10 的闭合确认、
  9/9 partition / 99.3% 只读结果及 Review 对纯离线 `UNITY_NA` 的附议不撤回。
- 本轮不授权正式 S1–S8/G0/D0 工件、人工 audit、D1–D3/C1、模型/下载/
  API/GPU、Unity/Play、任何 ID、场景/车辆修改，也不改变
  `P1-VLM-DIST-001` 的独立章程边界。

## 23. Acceptance stop-point recheck — round 11（2026-08-27）

Decision: **STOP_POINT_CONFIRMED / REVIEW_ROUND_3_PENDING**

### 23.1 F11–F14 闭合通道的独立复算

接受角色在一次性隔离 worktree 上亲自执行 workflow §4.4 的修复前通道，
主工作树实现字节始终未改：

- F11 的两条生产管线回归在 round-10 前工具字节上均以 `KeyError` 红；F13
  的邻居移除回归以 `0 != 1` 红，合计 `1 failure + 2 errors`。
- F12 保留真实 scout-3 frame/sidecar、旁支 manifest、异 SHA 归档 manifest
  与两份真实 scenario 字节，只临时回退 `bind_layout.py` 到 F12 修复前；
  `test_a2_nested_manifest_consistency_is_enforced_across_unit_subtree` 与
  `test_a2_subtree_snapshot_conflict_is_not_hidden_by_the_provider` 均按 Review
  原文错误返回 BOUND，恢复候选后转绿。
- 恢复候选后 F11/F13 三条 + F12 六条（含四个边界对照）共 9/9 通过；
  F14 定点复看确认 `tests/test_dist_data_round8.py` 写「十六条」，且 §20.3
  确有 4+4+2+2+4 = 16 个点名。隔离副本随后删除。
- 主工作树双解释器 focused 均 **391/391**；钉死解释器全套 **926** 为
  `failures=1, errors=1, skipped=1`，前两项只剩既有 `test_trackers...CSRT`
  error 与 `test_track_loop...CSRT` failure，新增失败 0。实现者的真实归档
  S1→S2 diff-empty 记录及零正式工件边界成立。

### 23.2 §13.5 两条披露裁定

1. **歧义 manifest 的 S2 全局硬失败：接受，非返工。** BC-DATA-20 §22.2
   (3) 已逐字保留「多个互异 SHA 仍是既有歧义硬失败」。这是 JSON 可读、
   但同一证人同时声明多个互斥身份的**语义歧义**，不属于 §22.2 (4) 的
   「不可读/不可解析或单一显式声明与 provider 不一致」unit-local 退出。
   因而检查域扩到整个 A.2 source-unit 子树时，硬失败的发现域同步扩张；
   它在 partition 产出前终止 S2，禁止交付部分工件，正是既有 fail-closed
   语义，不越出 BC-DATA-20。今日 51 份 manifest 为 29×单声明 + 22×零声明，
   歧义/不可读均 0，本裁定不改当前 9-partition 结果。
2. **只读诊断 1:51 → 4:04：接受为非阻断代价，本候选不加缓存。** 已接受
   合同没有 S1→S2 诊断时限；本批次是纯离线正确性停点。当前逐帧重扫慢但
   无陈旧状态，优于在 F12 闭合轮引入未冻结失效语义的 memoisation。性能
   优化可在独立后续范围中提出；不得为了加速本轮 Review 改动第 5 个候选。

### 23.3 授权与范围归因

`docs/authorizations.md` 中「继续做完 F12」仍是标明待确认的转述，**本轮不把
它引用为放行依据，也不替用户确认原话**。F12 的实现权限来自 2026-08-26
逐字「授权进行实现」的既有纯离线批次范围；用户之后的逐字指令「F12 等待
裁定」设的是顺序停点，Acceptance round 10 的 BC-DATA-20 已满足该前置，
没有新增资源、协议或阶段授权。候选推送另有逐字「可以推送吧」账本条目。

### 23.4 §4.3.1 停点与 Disposition

四项均成立：实现范围/接口已冻结；相称测试和修复前通道成立；无 Unity
失败且 Review round 2 的纯离线 `UNITY_NA` 附议未越界；实现证据、Review
范围、状态板、已推送候选与两条风险均已更新。故 Overall →
`STOP_POINT_CONFIRMED_REVIEW_R3_PENDING_R11`，交 Review round 3 新鲜上下文
独立复核。该结论**不是** Review verdict，也不关闭 work item；正式
S1–S8/G0/D0 工件、人工 audit、D1–D3/C1、模型/下载/API/GPU、Unity/Play、
任何 ID、场景/车辆修改继续未授权。

## 24. Acceptance consumption of Review round 3 — round 12（2026-08-27）

Decision: **REWORK_ATTRIBUTED / IMPLEMENTATION_DOC_REWORK_REQUIRED**

### 24.1 Verdict 与 finding 复判

- 接受 Review round 3 的 `REWORK_REQUIRED`。F11–F14 与 C3-3 **全部闭合**；
  Review 独立复算的 391/391、全套 926（1 failure / 1 error / 1 skip，既有
  CSRT pair）、9/9 partition、23,549/23,706、0/3 phantom、157 帧无字节
  unit、51 = 29+22 manifest 与符号链接三态均保留。零新代码/测试缺陷。
- **F15：同意 CLASS_2 / `NOT_MECHANIZABLE`。** 实现证据 §12.7 写「8 个
  文件（3+5）」而两个实际端点均为 9（3+6），且漏掉本节随后点名的
  `tests/test_dist_data_gate.py`。数值文字最低 CLASS_2，操作员会据此少查
  一条路径；分级正确。

### 24.2 返回 Implementation 的唯一修正

只改 `docs/evidence/P1-VLM-DATA-001-implementation.md` §12.7 首段。采用
COORD-007 R7 的首选闭合：**删除手维护的文件总数、tools/tests 分项数和
「含 1 个新增」计数**，改为说明复核范围须在运行时用 git 对实际端点及
workflow §4.4 的 PLAY_GOVERNING 闭集解析，并把解析出的路径逐行交 Review；
候选/端点继续运行时派生，不在手维护证据中钉当前 SHA。不得顺手修改本节
其他判断、任何代码/测试、门值、哈希、计数结果或授权范围。

修正批次只含实现证据与必要状态同步；运行实现角色写入检查、
`tools/check_docs.py` 与 `git diff --check`，提交并推送。证据不在
PLAY_GOVERNING 集合，故 workflow §4.4 下**不开 Review round 4**、不重跑
测试；回 Acceptance 对 §12.7 作 `NOT_MECHANIZABLE` 定点复看，并以运行时
`git diff --name-only` 确认路径闭集没有再被手写计数替代。

### 24.3 Disposition

- Overall → `IMPLEMENTATION_REWORK_REQUIRED_R12_F15_DOC_ONLY`；交
  Implementation 执行 §24.2 的唯一文档修正。
- Review round 3 的 `REWORK_REQUIRED` 与 F15 保留到定点闭合；F11–F14
  不重开，Review 对三轮纯离线 `UNITY_NA` 的附议维持。
- 本轮不授权正式 S1–S8/G0/D0 工件、人工 audit、D1–D3/C1、模型/下载/
  API/GPU、Unity/Play、任何 ID、场景/车辆修改，也不启动依赖本结果的工作。

## 25. Acceptance targeted closure of F15 — round 13（2026-08-27）

Decision: **F15_CLOSED / REWORK_CLOSED_WITHOUT_NEW_REVIEW**

### 25.1 `NOT_MECHANIZABLE` 定点复看

- 实现证据 §12.7 已删除文件总数、tools/tests 分项数及「含 1 个新增」；
  复核范围改为运行时解析 git 实际端点，按 workflow §4.4 的唯一权威
  PLAY_GOVERNING 定义过滤，并把解析出的路径逐行交 Review。候选与端点不钉
  SHA，文件数不再写回手维护证据。
- 第一次修正曾把 §4.4 的闭集逐项复抄，违反「其他文件只引用本定义，不复抄」；
  实现侧微修已删除该枚举。第二次定点复看确认 §12.7 只引用 §4.4，既无手写
  计数也无闭集副本。§12.0 的零改动路径陈述是本批次事实，不是定义复述。
- Acceptance 运行时核对两个修正批次：改动仅为实现证据与必要状态同步，
  PLAY_GOVERNING 路径为空；实际候选端点解析出的逐行范围与 Review round 3
  §0 的实测清单一致。`git diff --check` 与文档检查通过。

### 25.2 Disposition

- **F15 正式闭合**；Review rounds 1–3 的 F1–F15 与 C3-1…3 至此均无未闭项。
  Round 3 的历史 verdict 保留为 `REWORK_REQUIRED`，闭合依据是其指定的
  `NOT_MECHANIZABLE` 定点复看通道，不伪造新的 Review verdict 或通过指针。
- 修正证据不在 PLAY_GOVERNING，故不开 Review round 4、不重跑测试；三轮纯
  离线 `UNITY_NA` 附议维持。Overall →
  `REWORK_CLOSED_R13_F15_AWAITING_FORMAL_DATA_AUTHORIZATION`。
- Work item **不是 `DONE`**：正式 S1–S8/G0/D0 工件、人工 audit 与其后
  D1–D3/C1 仍须另行授权；本轮不授权模型/下载/API/GPU、Unity/Play、任何 ID、
  场景/车辆修改，也不启动依赖本结果的工作。

## 26. Acceptance scope ruling — round 14（2026-08-27）

Decision: **WITHIN_EXISTING_IMPLEMENTATION_AUTHORIZATION / CODE_ONLY**

触发问题：「补适配器 + 驱动」算不算既有实现授权内。该问句请求裁定，**不是**
一条新增资源或正式执行授权。

### 26.1 裁定

**算，但只算代码、自动测试、临时 fixture 与实现者证据；不算正式运行。**

依据如下：

1. Revision 2 已接受的交付本体是 S0–S9 单向 DAG；§2.4/§2.5 明定像素解码后
   的颜色统计与 pHash，§2/§3 明定 S1–S9 工件和生产阶段组合。具体
   `PixelSource` / `GraySource` 实现以及把现有阶段函数接成不可绕过的 driver，
   都是在落地既有合同，不新增阶段、schema、门值或研究主张。
2. 账本 2026-08-26「授权进行实现」逐字允许 revision 2 + §14 的
   `tools/dist_data/`、对应测试、临时 fixture 与实现者证据；其禁止项是**在真实
   归档上生成正式 S1–S8 create-once/G0/D0 工件**及人工审计等执行行为，不是
   禁止编写未来承载这些行为的已接受代码。因此实现证据 §4.2 将具体 adapter
   一概归为「正式工件生成、未授权」的解释过窄，由本轮 supersede。
3. 真实归档 driver 不是新的实验协议；它是 S0–S9 既有协议的组合入口。但只要
   对真实归档执行 S3–S9、写入正式或临时的完整 G0 门结果，就会提前产生本轮
   明令未授权的门工件/门数字，仍在禁止边界外。

### 26.2 本轮代码范围（binding）

允许 Implementation：

- 在 `tools/dist_data/` 增加基于**现有钉死环境中已安装**图像库的只读
  `PixelSource` / `GraySource` 具体 adapter；依赖缺失须显式 fail-closed，
  不下载、不安装新包、不改依赖清单。
- 增加一个生产 driver/CLI，把已接受的 S0–S9 阶段函数、create-once /
  supersession、禁行边和 `ArtifactStore` 接成唯一生产入口；不得复制或重新
  解释阶段算法、阈值、F1–F4、schema、split、verifier 或审计状态机。
- 在 driver 内按 BC-DATA-15 用 `camera_forward_depth` 装配 A1/A2 距离分层；
  不得自选另一距离、分位算法或 audit 终态。
- 增加自动测试与临时 fixture：adapter 金标/坏图 fail-closed、driver 的
  synthetic 端到端、禁行边、create-once/重跑字节幂等、门未过拒绝 S8，及
  正式输出根不会被测试误写。测试产物只进临时目录，不成为门证据。
- 做不产生 S3–S9 门结果的真实归档**只读 preflight/dry-run**，并证明
  `runtime/dist-data/` 前后不存在；不得把诊断结果写成正式 G0 verdict。

明确不包含：在真实归档上运行完整 driver；创建或 supersede 正式 S0–S9/
G0/D0 工件；渲染或执行 A1/A2/A3 人工 audit；安装依赖；C1、模型/下载、
教师/verifier 调用、API/GPU、Unity/Edit Mode/Play、任何 ID/配额、场景/车辆
修改、D1–D3 或后续训练。审计叠加图 renderer 不因「adapter + driver」四字
自动纳入；若确需实现，先回 Acceptance 点名其与已接受 §2.7 的精确边界。

### 26.3 停点与 Review

完成后 Implementation 更新证据与准确 Review 范围，运行双解释器 focused、
钉死环境全套及 `check_docs.py` / `git diff --check`，提交推送后回 Acceptance
确认 §4.3.1 停点。该批触及 `tools/` / `tests/`，PLAY_GOVERNING diff 必然
非空，须开 **Review round 4**；F15 保持闭合，不因新代码重开。Overall →
`IMPLEMENTATION_ACTIVE_R14_ADAPTER_DRIVER_CODE_ONLY`。正式工件与 audit 仍等待
用户另行授权。

## 27. Acceptance stop-point confirmation — round 15（2026-08-27）

Decision: **STOP_POINT_CONFIRMED / REVIEW_ROUND_4_PENDING**

对象为实现证据 §14 的第六候选；候选提交已推送，主树与远端一致且工作树
干净。候选端点与复核范围仍按 COORD-007 R7 / 证据 §12.7 在运行时解析，
不在本手维护文档钉可派生 SHA。

### 27.1 四项披露裁定（binding）

**BC-DATA-21 — 像素语义冻结。** 接受实现证据 §14.5 (1) 的两项选择：

1. RGB 解码后以 `Y = 0.299R + 0.587G + 0.114B`（ITU-R 601-2 luma）在
   float 域求灰度，不作整数截断；32×32 pHash 输入按块先求三个通道的精确
   整数和，再作一次 luma 与除法。源尺寸不能被 32 整除时 hard-fail，不准
   回退到库的 resize/filter。
2. 连续框的取像素规则为像素中心落入半开框：`x0 <= i+0.5 < x1`、
   `y0 <= j+0.5 < y1`，随后与图像边界求交；交集为空时返回空序列并使颜色
   字段 `UNVERIFIED`，不得扩框或就近取样。

这两项从本轮起属于 G0/D0 数据合同；未来改变须回 Acceptance 并显式
supersede。当前没有正式工件，故本轮冻结不作废任何门结果。

**BC-DATA-22 — 内存 preflight 例外。** 接受 `build_layout(..., inventory=)`，
但只作为 §26.2 (e) 的只读 preflight 注入点：载荷必须标记
`source=in_memory_preflight`，不得写成 S2 工件、不得供 `--run` 使用，也不得
绕过 `ArtifactStore` 的生产读边。正式 `PipelineDriver.stage2_layout()` 必须
省略该参数并从冻结的 S1 工件读取；Review round 4 须核对两条路径不可混认。

其余两项裁定：

- **耗时不阻断。** 两解释器输出逐字节相同，且 3:54 与前一版 4:04 同量级；
  已接受合同没有 preflight 时限。此停点不引入缓存；未来优化须先冻结缓存
  失效语义，不能以陈旧结果换速度。
- **真实 `--run` 覆盖缺口如实保留，不构成本轮返工。** 本授权明禁在真实归档
  落 S0–S9 工件，故合成 `run_stages()` 顺序测试加代码审查是当前可做上限；
  这不证明正式运行已经通过。即使 Review round 4 通过，真实 S3–S9/G0、人工
  audit 与正式工件仍须用户另行授权。

### 27.2 §4.3.1 停点核对

1. **范围/接口冻结**：第六候选只触及 §26 的 adapter、driver、preflight
   注入点与对应测试；BC-DATA-21/-22 已消除实现者返回的语义悬项。
2. **实现者检查相称**：Acceptance 复跑 focused，裸 `python3` 418 OK（9 条
   Pillow 金标按披露 skip）、钉死解释器 418/418 零 skip；钉死环境全套 953，
   仍只有既有 CSRT/opencv-contrib 的 1 failure + 1 error，新增失败为 0。
3. **已知 Unity 失败**：无。本批纯离线，不触及 Unity/场景/运行时协议；既有
   `UNITY_NA` 只覆盖复核过的旧代码，新增代码须由 Review round 4 重新附议。
4. **交接完整**：实现证据 §14、候选提交、状态板与未验证风险齐备；真实归档
   只读 preflight 的实现者记录为零写盘，`runtime/dist-data/` 当前仍不存在。

Review round 4 的 PLAY_GOVERNING 范围按运行时 git diff 解析，交接时逐行得到：

- `tools/dist_data/bind_layout.py`
- `tools/dist_data/pixel_source.py`
- `tools/dist_data/run_pipeline.py`
- `tests/test_dist_data_driver.py`
- `tests/test_dist_data_pixels.py`

复核文件尚无 `passed_candidate`（round 3 的历史 verdict 是
`REWORK_REQUIRED`）；Review 应按证据 §12.7 从上一复核轮候选到第六候选解析
端点，在一次性 worktree 逐文件检查上述实际增量，并重点覆盖证据 §14.6 与
BC-DATA-21/-22。F15 不重开。Overall →
`STOP_POINT_CONFIRMED_REVIEW_R4_PENDING_R15`。

## 28. Acceptance consumption of Review round 4 — round 16（2026-08-28）

Decision: **REVIEW_R4_REWORK_REQUIRED_CONSUMED / BC-DATA-23**

### 28.1 Finding 复判与归因

- **F16：同意 CLASS_2，归 Implementation。** `cross_validate_layout` 与
  `target_world_center_hit_ratio` 都只有单测调用，生产 S2 没有验证结果，S3
  又硬编码 `layout_binding_valid=True`，会让错位布局静默进入 F2–F4；这是
  真值质量的 fail-open，不因正式工件尚未授权而降格。落点按 §28.2 裁定。
- **F17：同意 CLASS_2，归 Implementation。** BC-DATA-18 规定 partition
  局域隔离；一个 `INVALID` partition 使 S3 `KeyError` 并拖垮全部 partition，
  虽方向 fail-closed，仍违反冻结隔离语义。
- **F18：同意 CLASS_2，归 Implementation。** A1/A2 的审计对象域是九类目录
  车辆；`occluder_only` 非车辆进入分层池会污染配额和分母。
- **F19：同意 CLASS_2，归 Implementation。** 一次性无归档 worktree 是规定
  复核环境；两条既有 Pillow 金标在该环境报 error 而非 skip，属于测试失败
  路径，不是可忽略的环境注记。

Review 对 BC-DATA-21/-22、§26.2 边界、四条 §14.5 披露及新增代码
`UNITY_NA` 的附议全部接受；F15 不重开。没有 CLASS_1、没有 CLASS_3 补丁。

裁定期间 Implementation 已按用户实现会话中的范围指示先落 F17–F19；该指示
以**转述**形式记入 `docs/authorizations.md`，不冒充逐字原话，也不预先证明
三项闭合。接受角色此处只确认其归因与返回条件，停点仍须在 F16 完成后统一核对。
复核观察项中，`preflight.wrote_nothing` 改为前后状态派生可保留；S5 入口再过滤
非车辆只是当前语义下的工作量优化，非 F18 闭合条件，本轮不扩入，维持非阻断。

### 28.2 BC-DATA-23 — F16 的生产落点与绑定单位（binding）

1. **落点 = S2、且在写 `layout@attempt-k` 之前。**
   `PipelineDriver.stage2_layout()` 调用的生产 `build_layout()` 必须完成历史
   交叉验证、把结果并入 S2 载荷，再由 driver create-once 写出 `layout`。
   S3 不重算交叉验证，也不得先冻结一个“待 S3 验证”的 layout 工件。
2. **决定单位 = BC-DATA-13 的精确 scenario partition**
   `(family, scenario_sha256)`；同 partition 的 source units 合并取样，不同
   SHA 永不混算。`layout_class` 只作报告分层。此款仅 supersede
   BC-DATA-3「按 layout class 汇总」中与 BC-DATA-13 精确几何冲突的决定
   单位；前 50 对排序、50 对下限、90% 中心命中、0.5 IoU 中位数及动态
   target 不补静态对数等规则全部不变。一个 partition 失败只使自身
   `INVALID`，不得毒化同 family 的其他 SHA 或其他 family。
3. **输入只来自 S1 冻结映射与归档源字节。** 每帧相机由同名 sidecar 的
   `camera_position/right/up/forward` 与内参构造；truth 只能经
   `roots.truth_source_for(frame_id)` 指向的归档字节读取。S2 与 S3 必须共用
   同一 truth-join 实现或等价单一助手，禁止各写一套会漂移的路径规则；当前
   Unity scene、非哈希同一的当前 config、路径名猜测均不得补证。
4. **schema 分轨逐字保留。** `scouting` 只把非空 distractor bbox 中能以
   `distractor_id` 恰一映射到该 partition 静态实例的对交给
   `cross_validate_layout`；不足 50 对即 `INVALID`。`m3` 只把归档
   `target_world_*_m` 与同帧 truth box 交给
   `target_world_center_hit_ratio`，中心命中率须 `>= 0.9`，不得构造 target
   AABB、算 target IoU 或拿它补静态 50 对；零个可检 m3 样本同样
   `INVALID`。一个 partition 的全部 INCLUDED 记录均无冻结逐帧 truth source
   时，结果显式记 `NOT_APPLICABLE_NO_ARCHIVED_FRAME_TRUTH`，不凭空使其
   invalid；一旦该 schema 按附录 A 应存在但源字节/sidecar 不可读或无法
   join，则该 partition `INVALID` 并记录确定性 reason。
5. **S2 载荷与报告不可省略。** `layout` 顶层必须含按 partition id 排序的
   `cross_validation`；每项至少写 `mode/status/reason`、样本或 pair 数及对应
   指标。验证失败同步把该 partition 的 `binding_status` 置 `INVALID`。
   S7/G0 必须读取这个必有成员，删除 `.get("cross_validation", {})` 的静默
   空表 fallback；缺成员须 hard-fail。
6. **S3 只消费验证后的状态。** source-unit 查找不得映入非 `BOUND`
   partition；每个产出 entry 的 `layout_binding_valid` 必须由实际 partition
   状态派生，禁止字面量 `True`。`INVALID` 帧退出 floor 并有计数，其余 BOUND
   partition 继续产出——F17 与本条按同一状态源闭合。
7. **只读 preflight 走同一 S2。** BC-DATA-22 的内存注入仍在写盘前调用同一
   交叉验证，并可报告诊断状态；这仍属于 §26.2 (e) 已授权的零写入 S1+S2
   preflight，不是正式 G0 verdict。旧的 9/9 只证明 scenario/几何派生，不能
   预断新交叉验证结果；新诊断无论如何不得回调阈值、样本或附录 A。

### 28.3 返回 Implementation 的闭合条件

既有 2026-08-26 纯离线实现授权及账本中本轮的转述顺序指示覆盖这些缺陷返工，
不产生新的执行或资源授权。F17–F19 虽已先落地，仍与 F16 一起按下列条件返回；
Implementation 须：

1. 按 BC-DATA-23 闭合 F16，并绑定修复前必失败的
   `test_s2_cross_validation_invalidates_shifted_static_layout_and_reports_it`
   与 `test_s2_m3_target_check_uses_center_ratio_without_static_pair_backfill`；
   fixture 必须走生产 S2/driver 路径并消费归档字节副本，不得手写最终
   `cross_validation`/`binding_status` 状态。
2. F17 绑定
   `test_driver_skips_invalid_partition_and_preserves_bound_partition`；生产路径
   同时有一 BOUND、一 INVALID partition 时，S3 只产前者并记录退出计数。
3. F18 绑定 `test_audit_strata_excludes_non_vehicle_occluders`；混合世界中
   building/nature/prop 不得进入任何 stratum。Review round 4 的 S5 非车辆
   工作量观察项维持非阻断，不在本轮借机改变 F1 对象域。
4. F19 为现有
   `test_corrupt_bytes_fail_closed` / `test_truncated_bytes_fail_closed` 补与
   `ArchiveFrameTest` 同源的归档存在守卫；在无归档一次性副本上双解释器
   focused 均须 OK（相应用例转 skip），无需为守卫再造第三条测试。
5. 对 F16–F18 按 workflow §4.4 保存修复前红、修复后绿证据；双解释器
   focused、钉死环境全套、`git diff --check`、文档检查通过。重跑真实归档
   只读 preflight，逐 partition 如实报告 BC-DATA-23 后的诊断结果并证明
   `runtime/dist-data/` 仍不存在；不得为维持旧 9/9 调参或改数据。

修复返回同一 §4.3.1 停点；`tools/` / `tests/` diff 非空，停点后须开
Review round 5。正式 S0–S9/G0/D0 工件、人工 audit、模型/下载/API/GPU、
Unity/Play、任何 ID/配额、场景/车辆修改及后续训练仍未授权。Overall →
`IMPLEMENTATION_REWORK_REQUIRED_R16_F16_F19`；设计同步为 v0.3.25。

## 29. Acceptance returned-contract ruling — round 17（2026-08-28）

Decision: **BLOCKING_CONTRACT_QUESTION_RULED / BC-DATA-24 / RETURN_IMPLEMENTATION**

对象为实现证据 §16.5 的 amodal-vs-clipped 阻断问题与 §16.6 的缺帧真值读法。
这是对既有 §2.3/§2.4 图像框域的消歧：不改变 50 对、0.9、0.5、抽样顺序、
partition 单位、附录 A 或任何 G0 下限，也不扩大正式执行授权。

### 29.1 裁定依据

1. §2.4 已把项目图像框冻结为「AABB 投影后与 viewport 求交」的
   amodal-裁剪框，归档 `bbox_xywh_norm` 也按项目协议裁在图像内。历史布局
   核验要回答几何是否错位，中心与 IoU 两个判据必须在同一图像域比较；拿
   未裁剪 amodal 框的中心去检验裁剪后的归档框，会把 viewport 边界误报为
   场景漂移。
2. 实现证据 §16.5 的指纹支持这一归因：同源几何的 IoU 中位数约为
   `0.99999`，裁剪预测框后中心命中 `0.780 → 1.000`；真正错配的对照同时是
   IoU `0.0` / centre `0.0`。因此这不是放宽阈值或看数调参，而是恢复冻结的
   比较域。
3. S1 已把逐帧 `truth_join.present` 作为布尔事实登记，§2.3 又以「可检对」
   计数；部分覆盖中的记录缺席是无观测，不等于一个存在的归档文件字节损坏。
   但缺席不能补样本，也不能掩盖既有的最小样本门。

### 29.2 BC-DATA-24 — viewport 比较域与真值缺席语义（binding）

1. **scouting 静态框的比较域 = viewport-clipped projection。**
   `cross_validate_layout` 仍先用 `project_aabb()` 产生 amodal 像素框，再与
   该帧 `camera.viewport()` 求交；中心命中与 IoU **都只**使用这个交框和
   已归档的裁剪真值框。amodal 为 `None` 或与 viewport 无交集时，该对按
   centre miss + IoU `0.0` 处理。不得裁到真值框本身、扩真值框或改阈值。
2. 本款**不**改变 `project_aabb()`、S3 的 `amodal_px`、遮挡/截断状态或
   m3 动态目标中心检查；只改变 §2.3 历史核验的同域比较。前 50 对的
   SHA 排序、pair 候选集、`>= 50`、centre `>= 0.9`、IoU median `>= 0.5`
   全部逐字保留，裁剪不得参与选样。
3. **缺席不等于不可读。** `truth_source_for(frame)` 无映射仍按
   BC-DATA-23 记无冻结 truth source；有 schema 映射但逐帧文件不存在，或
   共享 JSONL 中没有该 frame 的行，记该帧「无 truth observation」并跳过，
   不单独使 partition `INVALID`。它仍属于 schema 预期域：scouting 最终不足
   50 对、m3 最终零个可检样本，照旧 `INVALID`，不得把缺席补成
   `NOT_APPLICABLE`。
4. 存在的源文件不可读/不可解析、同一 frame 的 join 含冲突或歧义、或已有
   可用 truth row 却无法读取其 sidecar，仍按 BC-DATA-23 fail-closed 为
   partition `INVALID`；本轮只消除「正常缺席 = 坏字节」这一歧义，不放宽
   损坏与矛盾输入。
5. 现有实现下的两条 scouting `INVALID` 保留为裁定前诊断记录，但不得引用为
   「基础场景被改过」。应用本款后须重跑同一零写入 preflight，再按冻结门如实
   报告；不预断两条新状态。

### 29.3 返回 Implementation 与停点条件

当前**不是** §4.3.1 停点。Implementation 在既有 code-only 授权内：

1. 按 BC-DATA-24 修改既有阶段实现，不复制第二套投影或 truth join；绑定
   `test_s2_cross_validation_clips_projection_to_archived_viewport_domain`。该测试
   必须走生产 S2 并消费归档帧/sidecar/truth 字节副本，证明同源的下沿截断样本
   在裁剪域通过，同时原有 scene-004 错配对照仍为 `INVALID`。
2. 绑定
   `test_s2_partial_truth_absence_skips_missing_frames_without_masking_corruption`：
   正常缺帧在剩余样本满足冻结门时不否决 partition；把一个实际存在的归档
   truth 字节副本破坏后必须 fail-closed。fixture 不得手写最终状态。
3. §28.3 的 F16–F19 具名回归全部保留；补修复前红/修复后绿、双解释器
   focused、钉死环境全套、`git diff --check` 与文档检查。随后重跑同一真实
   归档零写入 preflight，逐 partition 报告并证明 `runtime/dist-data/` 仍不存在。
4. 更新实现证据与准确 Review 范围，提交推送后回 Acceptance 核对四项停点；
   `tools/` / `tests/` diff 非空，停点成立后开 Review round 5。

正式 S0–S9/G0/D0 工件、人工 audit、模型/下载/API/GPU、Unity/Play、任何
ID/配额、场景/车辆修改及后续训练仍未授权；F15、BC-DATA-21/-23、Review
round 4 的披露与纯离线 `UNITY_NA` 附议不重开。Overall →
`IMPLEMENTATION_REWORK_REQUIRED_R17_CLIPPING`；设计同步为 v0.3.26。

## 30. Acceptance stable-candidate stop-point confirmation — round 18（2026-08-28）

Decision: **STOP_POINT_CONFIRMED / OPEN_REVIEW_ROUND_5**

对象为 §29.3 返回的 BC-DATA-24 候选及 Review round 4 的 F16–F19 累积返工。
接受角色按 workflow §4.3.1 逐项复核，四项条件全部成立：

1. **范围与接口冻结。** BC-DATA-24 只在选样后把 scouting 的 amodal 投影与
   viewport 求交；候选集、排序、前 50 对、阈值、partition 单位、
   `project_aabb()`、S3 `amodal_px`、遮挡/截断与 m3 分支均保持冻结。
   F16–F19 的修复边界和 §15–§17 的 Review 范围已完整给出；本候选未扩大到
   S5 优化、正式工件、人工审计、运行时或资源使用。
2. **相称测试通过。** 实现证据 §17 记录两条 §29.3 生产路径回归的修复前红、
   修复后绿，以及零写入真实归档 preflight 的 9/9 BOUND、23,549 bound frames。
   接受角色独立重跑两条具名回归 2/2、layout 套件 22/22、双解释器 focused
   424/424；钉死环境全套 959 仅保留既有 CSRT/opencv-contrib 的 1 failure +
   1 error + 1 skip，本批新增失败为 0；候选区间 `git diff --check` 通过。
3. **已知 Unity 失败为零。** 本轮只改纯离线 `tools/dist_data/` 与测试，不改
   Unity/runtime 协议，且没有待修 Unity 失败，故停点条件 3 成立；当前增量的
   `UNITY_NA` 关闭资格仍须 Review round 5 独立附议，不借用旧轮次越权关闭。
4. **候选与交接齐备。** 候选已提交并推送，证据 §17、状态板、未验证风险与
   Review 重点均已更新；git 端点和 PLAY_GOVERNING 路径由复核会话运行时解析，
   不在手维护文档复制 SHA、路径计数或闭集定义。

§4.4 开轮资格成立：相对上一复核候选的 PLAY_GOVERNING diff 非空。Review
round 5 应累计核对 F16–F19、BC-DATA-23/-24 与证据 §15.8、§16.7、§17.6，
尤其复算裁剪发生在选样之后、夹具修正未弱化门、9/9 并非调参回归，以及缺席
回归的红只证明裁剪而非 (3)(4) 旧分支。`m3-armB` 的 centre `0.9216` 对门
`0.9`、153 样本的敏感度继续作为已披露风险，不阻断代码复核。

正式 S0–S9/G0/D0 工件、人工 audit、模型/下载/API/GPU、Unity/Play、任何
ID/配额、场景/车辆修改及后续训练仍未授权。Overall →
`STOP_POINT_CONFIRMED_REVIEW_R5_PENDING_R18`。

## 31. Acceptance review consumption — round 19（2026-08-28）

Decision: **PASS_WITH_NOTES_CONSUMED / CODE_REVIEW_CHAIN_CLOSED /
AWAIT_FORMAL_DATA_AUTHORIZATION**

接受角色独立核对 Review round 5 的 verdict、机读通过指针、候选祖先关系与
候选后的 PLAY_GOVERNING diff；指针与受审候选一致，候选之后无实现路径变化。
因此消费本 work ID 的首个通过轮，不返回 Implementation：F1–F19 与 C3-1…3
全部闭合，BC-DATA-1…24 在当前交付代码上的实现/复核链关闭。

### 31.1 四条 notes 的接受处置

1. **m3-armB 贴线风险：同意为非阻断披露。** `141/153 = 0.9216` 对 `0.9`
   仅余约 3.3 个样本裕量；正式运行须原样报告并禁止为过门调参。它不推翻
   今日 9/9，也不预断未来样本集仍通过。
2. **混 schema partition：同意为潜伏合同问题。** 附录 A 今日每个 partition
   schema 单一，现有优先序不可触发；未来若引入混合 schema，必须先返回
   Acceptance 冻结合并语义，不得沿用 scouting-first 行为作默示裁定。
3. **跨版本红灯噪声：同意测量口径。** 后续闭合复算继续按各修复批次自己的
   tests 与前一批 tools 配对，区分契约红灯和跨版本常量缺失的非诊断噪声。
4. **遗留观察项：不阻断本轮。** `wrote_nothing` 派生值已闭；S5 非车辆预过滤
   维持 round 16 的明确推迟；`SplitTerminal` 端到端覆盖与 Review round 2/3
   的观察项保留为后续测试债，不伪装成本批已完成，也不单独启动实现。

### 31.2 Unity 与终态边界

Review round 5 对当前增量附议 `UNITY_NA`，累计覆盖轮 1–5；接受角色据此把
**已复核的纯离线代码批次** Unity 列记为 `UNITY_NA`。这只关闭代码批次的
Unity 分类，不等于整个 work item `DONE`，也不授权任何运行。

正式 S0–S9/G0/D0 工件、A1/A2/A3 人工 audit、D1–D3/C1、模型/下载/API/GPU、
Unity/Play、任何 ID/配额、场景/车辆修改及后续训练仍未授权。该 work item
暂停在用户授权门；若用户继续，须先逐字记录授权并发出精确执行交接。Overall →
`REVIEW_R5_PASS_CONSUMED_R19_AWAITING_FORMAL_DATA_AUTHORIZATION`。

## 32. Acceptance limited-execution authorization — round 20（2026-08-28）

Decision: **FORMAL_S0_S5_AUTHORIZED / PREAUDIT_UPPER_BOUND_DIAGNOSTIC_ONLY**

用户逐字授权见 `docs/authorizations.md` 当日条目：
「S0–S5 + 一份明确标注为『审计前上界、非门 verdict』的诊断报告」。本轮只
解释如何在既有合同内执行该窄范围，不改变 BC-DATA-1…24、F1–F4、下限、
split、附录 A 或 Review round 5 的四条 notes。

### 32.1 正式工件范围（binding）

1. 只允许对当前冻结真实归档 create-once 生成 S0 `contract`、S1
   `inventory`、S2 `layout`、S3 `frames_catalog`、S4 `splits`、S5
   `field_catalog` 六类正式工件；共用一个由 `ArtifactStore` 运行时枚举后选择
   的下一未用 attempt，不在手维护文档复制 attempt 名或工件 SHA。
2. 执行前从 Review 文件运行时解析最近 `passed_candidate`，断言其为当前 HEAD
   祖先且候选后 PLAY_GOVERNING diff 为空；工作树须干净，使用钉死的
   `.venv-yoloe` 环境。授权时只读核查 `runtime/dist-data/` 不存在；若执行前
   已出现任何正式 attempt，先停下对账，不覆盖、不自动 supersede。
3. 使用已复核的 `PipelineDriver.stage0_contract()` →
   `stage5_field_catalog()` 顺序调用，不复制阶段算法。当前 `run_stages()` 在
   S4 terminal 时会自动写 S9，超出本授权，因此本批**不得**调用可能进入该
   自动 S9 分支的总控 `--run` 路径。任一阶段异常或 S4 terminal：立即停下，
   原样保留已写工件，记录失败并返回 Acceptance；不得补写 S9、重试或删目录。
4. 本批不修改任何生产代码、测试、合同或依赖。若现有已复核代码无法在上述
   边界内完成，属于新的设计/实现问题，先返回 Acceptance，不就地修补。

### 32.2 诊断报告合同（binding）

唯一交付文件为
`docs/evidence/P1-VLM-DATA-001-S0-S5-pre-audit-upper-bound.md`。无论 S0–S5
成功或提前停机，标题、摘要、所有数字表头都必须显著携带逐字标签：
**「审计前上界、非门 verdict」**。

- S0–S5 全部成功时，可只读消费这六类正式工件，并复用既有纯函数在内存中
  计算 `U_F1`…`U_F4`。唯一允许的乐观假设是：A1/A2/A3 导致**零降级、零
  拒绝、零修复**，且 S0–S5 不发生 supersession；禁止写入合成 `audit`，禁止
  调 `stage7_gate()`，禁止写 `mother_candidates` / `g0_report` / S8 / S9。
- 报告须列出 S0–S5 的实测摘要、上界算法、假设、分母、冻结 floor 参考和
  差额，但所有 U 值的状态统一为 `NOT_EVALUATED_PRE_AUDIT`；不得出现把它们
  升格为门结论的 `OPEN` / `CLOSED` / `PASS` / `FAIL` /
  `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA`。即使某 U 值低于 floor，也只能写
  “乐观上界相对 floor 的诊断差额”，不能签发 G0 verdict。
- “上界”只对**同一份未 supersede 的 S0–S5 工件**成立：A1 可降级颜色组，
  A2/A3 可拒绝样本；若审计发现工具/数据缺陷并触发未来 supersession，本报告
  自动失效，不能约束新 attempt 的值。报告须原样保留 Review round 5 的
  m3-armB 141/153 贴线风险与禁止调参纪律。
- 若 S0–S5 未全部成功，报告仍须落盘，但 U 表写
  `UNAVAILABLE_S0_S5_INCOMPLETE`，只记录停在哪一阶段和 fail-closed 原因；
  不用部分工件猜数。

### 32.3 返回与未授权边界

Implementation 完成后更新证据与状态板，运行文档/角色检查并提交；因本批不
允许 PLAY_GOVERNING 修改，不开新的代码 Review 轮，先返回 Acceptance 核对
阶段范围、create-once 收据和诊断标签。若磁盘出现任何实现 diff，则该 diff
不在本授权内，必须停下而不是夹带提交。

S6/A1–A3、S7/G0 正式门、S8/D0、S9、supersession/重试、C1/D1–D3、
模型/下载/教师/verifier/API/GPU、Unity/Edit Mode/Play、任何 ID/配额、
场景/车辆修改及后续训练仍未授权。Overall →
`FORMAL_S0_S5_AUTHORIZED_R20_PREAUDIT_UPPER_BOUND_ONLY`。

## 33. Acceptance archive-scale ruling — round 21（2026-08-29）

Decision: **BATCH_STOP_ATTRIBUTED / BC-DATA-25 /
CODE_ONLY_IMPLEMENTATION_REWORK_REQUIRED**

对象为 §32 正式 S0–S5 执行返回的 S3 归档尺度问题。本轮是对既有
数据合同的物理存储与消费方式消歧：不改研究主张、F1–F4、任何门值、
frame/object 域、投影/遮挡/唯一性/split 语义或附录 A。

### 33.1 事实复核与归因

1. Acceptance 从磁盘重新枚举当前运行时选定的 attempt：仅 S0
   `contract`、S1 `inventory`、S2 `layout` 有完整且可解析的 create-once
   工件；S3 `frames_catalog`、S4 `splits`、S5 `field_catalog` 及
   S6–S9 工件全部缺席。S0–S2 的信封身份和哈希可复算，S2 九个
   partition 与授权前 preflight 逐项一致。最近复核通过候选是
   HEAD 祖先，其后 PLAY_GOVERNING diff 为空。
2. 实现证据的一次墙钟中断发生时 S3 从未完成、从未写出，后续只读 S0–S2
   并继续首次 S3 的记录可接受，不追认为覆盖或 supersession。随后
   `exit=137` 才是本批次的 fail-closed 终止；实现角色没有修码、重试、
   删除、supersede、合成 audit 或写 S7–S9，执行边界合格。诊断报告的
   标题/摘要/数字表均带「审计前上界、非门 verdict」，四个 U 值均为
   `UNAVAILABLE_S0_S5_INCOMPLETE`，没有产生 G0 verdict。
3. 归因为 **archive-scale blocking implementation/representation defect**：
   现有 `stage3_frames_catalog()` 同时驻留全部 23,706 个 frame entry，而每个
   entry 包含 779 条对象记录。仅 JSON 约 5.4 GiB，Python 对象图为其数倍，
   16 GiB 主机因此被 OOM kill。同样的高基数问题会在 S4 将约
   frame×object 角色全部收集为 `sample_roles` 列表时再现；只把 S3 JSON 换成
   一次流式写盘不能闭合 S0–S5。
4. 拒绝「只记 referable/blocking 对象」：它会删除 §2.4 要求的逐帧逐对象
   唯一状态与 BC-DATA-2 要求的 `{referent,distractor,absent}` 暴露域，属于
   schema/计数口径缩水。也拒绝「仅提高内存」作正式闭合：它不给出有限
   上界，且不解决 S4/S5 及后续消费者的整包反序列化。

### 33.2 BC-DATA-25 — 高基数行集的单一逻辑工件与有界流式存储（binding）

1. **逻辑 schema 不变。** S3 仍对每个 BOUND partition 的每个
   `INCLUDED` frame × 该 partition 的全部 layout instance/phantom 记录恰一条
   对象状态；frame entry 的字段、对象字段、顺序、`referable`/`blocking`、
   `exposure`、`TARGET_UNBOUNDED`、统计与跳过计数全部逐字义保留。S4 的
   `sample_roles` 仍逐 `(frame_id, object_id)` 保存原有四字段和排序，
   `exposure_matrix.sample_count` 必须等于完整角色行数。不得删行、采样、改门值、
   改排序或以汇总表替代原始行。
2. **S3 仍只有一个逻辑 `frames_catalog@attempt-k` 与一个
   `ArtifactRef`。** 物理表示改为：一个小型 manifest 作发布点，加按原
   entry 次序切分的 deterministic gzip-NDJSON shards。每行是一个完整 frame
   entry 的 canonical JSON；每个 shard 的**未压缩** canonical 行字节总量上限
   `64 * 1024 * 1024`（单行自身超限时独占一 shard）。gzip 必须固定 header
   （含 `mtime=0`、OS=255）与压缩参数，使同输入字节幂等。
3. manifest 须含 storage schema version、输入 artifact refs、有序 shard 表，
   并对每个 shard 记录零填充序号、相对路径、SHA-256、行数、压缩/未压缩
   字节数、首/尾 `frame_id`；顶层记录总行数、`frame_count`、两类 skip 计数
   与有序行流的累积哈希。`ArtifactRef.sha256` 哈希 manifest，manifest 递归
   哈希全部 shard；因此仍是一个可复算的逻辑工件，不新增 DAG 阶段或
   可被下游单独引用的 shard 工件。
4. **S4 `splits@attempt-k` 对 `sample_roles` 采同一组合工件规则。**
   `splits` 仍只有一个 manifest/`ArtifactRef`；小型摘要（atom/family/frame
   assignment、held-out、leakage、`exposure_matrix`）留在 manifest payload，完整
   `sample_roles` 按 `(frame_id UTF-8, object_id UTF-8)` 有序行流放入同规则
   shards。下游只能经 `ArtifactStore` 的类型化迭代器读取，不得直接依赖
   shard 路径或把它们冒充多个 S4 工件。
5. **生产消费全程有界。** S3 不得累积全部 entry；S4 可对类型化
   entry 流做确定性多遍扫描，可驻留 frame id/pHash/atom 摘要与 779 对象的
   汇总，不得驻留全部 frame entry 或全部 `sample_roles`。S5、S6 分层、
   S7 和 S8 的现有 `frames_catalog` 消费点全部改走同一类型化迭代器；这只
   改变取数机制，不预先授权执行 S6–S9。任何下游工件在输入流全部校验/
   消费完成前不得发布。
6. **组合 create-once 以 manifest 为唯一可见提交点。** shards 先在同文件系统
   private staging 中完整写入、固化、哈希复核，manifest 最后以不覆盖的原子
   发布作为 commit marker。manifest 不存在时，`attempts()`/下游一律视为工件
   缺席；发布后每次读取须复核 manifest 与所有 shard 身份/哈希/行数/
   顺序。同输入重跑只能在全套字节一致时幂等返回，任一字节不同即
   `CreateOnceError`。孤立 staging/部分 shard 不得自动删除、重用或续传，须
   `INCOMPLETE_COMPOSITE_ARTIFACT` fail-closed 返回 Acceptance。

### 33.3 Implementation 返回条件与授权边界

本轮的**代码、自动测试、临时 fixture 与实现者证据**属于 2026-08-26
既有 implementation authorization：它落地的是已接受行语义的有界存储，不是
新数据域、新门或新研究主张。Implementation 只可修改 `tools/dist_data/`
内的组合工件适配/现有消费点、对应 `tests/test_dist_data_*.py`、实现证据与状态板；
不改 S0 常量、投影/遮挡/字段/split/F 算法，不安装依赖。

返回至少须有下列具名生产路径回归（名称可加类名前缀，核心后缀不改）：

- `test_streamed_frames_catalog_is_logically_identical_and_bounded_memory`：小夹具与修前
  单 JSON 的逻辑 entry 序列逐字节一致；跟踪型生成器在超过一 shard 的规模下
  证明已消费 entry 被释放，若生产路径 `list()` 化全集则必失败。
- `test_composite_publish_is_atomic_and_orphan_staging_fails_closed`：在分片中断时不出现
  正式 artifact ref，部分 staging 原样保留并阻止自动重用。
- `test_streamed_splits_preserves_all_sample_roles_and_exposure_counts`：逐行角色、排序、
  split 归属、四集汇总与 `sample_count` 全部对等，不驻留全角色集。
- `test_streamed_consumers_match_legacy_small_fixture_s4_to_s8`：S4–S8 现有小世界
  输出/终态与修前逐字义等价，且全部只走类型化迭代器。
- `test_composite_tamper_and_create_once_are_rejected`：改 shard 字节、丢 shard、改顺序/
  行数及对已发布工件试图写异字节均 fail-closed。

实现角色还须保留当前 S0–S2 三件正式工件一字节不动，所有新测试只写
临时根；运行双解释器 focused、钉死环境全套、`git diff --check`、角色/文档检查，
更新证据与准确 Review 范围后返同一 §4.3.1 停点。PLAY_GOVERNING diff 必为非空，
停点成立后须开 Review round 6；Review round 5 的历史 `PASS_WITH_NOTES` 保留，
但不覆盖 BC-DATA-25 新代码。

**本轮不授权正式续跑。** 2026-08-28 账本逐字明禁重试与代码修改；该次
限域执行已以 fail-closed 停机返回。Review round 6 通过并由 Acceptance 消费后，
用户仍须新授权「保留既有、未 supersede 的 S0–S2，在新复核候选上从 S3
续到 S5」。届时须先再核工件完整性、代码候选、工作树与零孤立 staging；
不得重跑/改写 S0–S2，也不得在没有新授权时以「S3 尚无工件」为由自行续跑。
S6–S9/G0/D0、audit、任何 supersession、依赖/模型/API/GPU/Play/ID 与后续训练继续
未授权。Overall → `IMPLEMENTATION_REWORK_REQUIRED_R21_ARCHIVE_SCALE_CODE_ONLY`。

## 34. Acceptance stop-point ruling — round 22（2026-08-31）

Decision: **STOP_POINT_NOT_CONFIRMED / COMPOSITE_BOUNDARY_REWORK_REQUIRED /
REVIEW_ROUND_6_NOT_OPENED**

本轮只裁定 workflow §4.3.1 的稳定候选停点，不给实现签发独立复核，也不改
BC-DATA-25、逻辑 schema、门值或任何执行授权。

### 34.1 四项停点条件

1. **范围与接口冻结：满足。** 候选只改 `tools/dist_data/` 的组合工件适配、
   既有消费点和对应测试；BC-DATA-25 §33.2 仍是完整且唯一的接口合同。
2. **相称的实现者测试/编译：满足。** Acceptance 在当前候选上重新运行
   `python3` 与 `.venv-yoloe` 的 focused 套件，各 **430** 条通过；前者
   `skipped=9`，后者零 skip。实现者报告的全套 965 结果本轮未重跑，仍只算
   实现者证据；它不是本轮退回原因。
3. **已知 Unity 失败：满足/不适用本代码停点。** 本批是离线数据工件代码，
   没有待修 Unity 失败；本轮也不签发新的 `UNITY_NA` 或运行时结论。
4. **复核目标、状态、候选与未验证风险准确更新：不满足。** 候选已提交并
   推送，工作树在本轮文档更新前干净，且相对最近通过候选的
   PLAY_GOVERNING diff 非空；但实现证据 §18.1 与状态板把下列两项写成已经
   闭合，真实生产路径和测试却没有做到。因此候选不是可交付 Review 的稳定版本。

结论：四项没有全部满足，**不得开启 Review round 6**。非空的
PLAY_GOVERNING diff 只证明修复后具备开轮资格，不替代稳定候选条件。

### 34.2 两项阻断返工

**SP22-1 — manifest 输入 lineage 缺失。** BC-DATA-25 §33.2(3) 要求 manifest
含输入 artifact refs；`write_composite()` 虽有 `inputs` 参数，但生产
`stage3_frames_catalog()` 与 `stage4_splits()` 两次调用都没有传入该参数，
实际信封因此写出 `"inputs": []`。实现证据 §18.1 的“输入 refs”主张不成立，
现有六条组合工件测试也没有检查生产 driver 的输入 lineage。

返工须让 S3 manifest 引用本次实际读取的 `inventory` 与 `layout` refs，让 S4
manifest 引用本次实际读取的 `frames_catalog` ref；引用必须来自同一生产读取，
不得事后按路径伪造。新增生产路径回归须直接检查两份 manifest 的 `inputs` 与
上游 `ArtifactRef.as_reference()` 逐字段相等。

**SP22-2 — manifest 发布失败后的 final-shard 残留没有按合同 fail-closed。** 当前
路径先把 `.staging/` rename 成 `shards/`，再调用 `_atomic_publish()`。Acceptance
用真实 `write_composite()` 写盘路径、只 mock manifest 原子发布失败：首次失败后
manifest 缺席、`.staging/` 缺席而 `shards/` 已存在；下一次写入没有在落盘前识别
该残留，会另建 `.staging/`，最后以普通 `OSError: Directory not empty` 失败，
不是 §33.2(6) 要求的 `INCOMPLETE_COMPOSITE_ARTIFACT`，现场也被新增残留改变。

返工须在 manifest 缺席时把既有 final `shards/` 与孤立 `.staging/` 同样视作
不完整组合工件：在写任何新字节前抛 `IncompleteCompositeArtifactError`，不删除、
不重用、不续传、不新增残留。新增生产路径回归须覆盖“staging 已整体 rename、
manifest 尚未 commit”这一故障窗口，并断言首次现场和再次调用前后逐字节不变。

### 34.3 保留事实与边界

- 当前正式根仍只有 S0/S1/S2；Acceptance 复核其大小/SHA-256，并确认无
  `shards/` 或 `.staging/`。本轮没有运行正式 S3–S5，没有写 runtime 工件。
- 其余 BC-DATA-25 回归与双解释器 430 focused 结果保留；两项新增回归必须与
  现有具名回归一起返回，证据与状态板须删除已经被反证的闭合措辞。
- 修复仍属于 round 21 的 code/tests/temp-fixture 授权。修复后回到同一
  §4.3.1 停点；Review round 6 通过并被 Acceptance 消费后，正式 S3–S5 续跑
  仍须用户新授权。S6–S9/G0/D0、audit、supersession、依赖/模型/API/GPU/Play/ID
  与后续训练全部继续未授权。

Overall → `IMPLEMENTATION_REWORK_REQUIRED_R22_COMPOSITE_BOUNDARY`。

## 35. Acceptance stable-candidate ruling — round 23（2026-09-01）

Decision: **STOP_POINT_CONFIRMED / IMPLEMENTED / REVIEW_ROUND_6_OPENED**

本轮只确认 workflow §4.3.1 稳定候选停点并交给独立 Review；不签发复核
verdict、不关闭 work item，也不扩大任何数据或资源授权。

### 35.1 四项条件复查

1. **范围与接口冻结：满足。** BC-DATA-25 §33.2 未改；round 22 的两项返工
   只闭合 manifest lineage 与发布失败残留，逻辑行、字段、顺序、计数、门值、
   投影/遮挡/split 与 S0 常量均未改变。
2. **相称测试：满足。** 两条 SP22 生产路径回归先在 tools-only 回退下以裁定的
   原症状变红，修复后双解释器 focused 各 **432** 条通过；Acceptance 在当前
   候选上独立重跑并复现同一结果。实现者的钉死环境全套 **967** 仍只有两项
   既有 CSRT/opencv-contrib 环境失败，新增失败为零。
3. **已知 Unity 失败：满足/不适用。** 本批是离线数据工件代码，没有待修
   Unity 失败；本轮不新增 `UNITY_NA`，也不产生正式运行时 verdict。
4. **复核目标、状态、候选与风险：满足。** §18.1 被反证的措辞已就地改正，
   §19 记录两项修复、修复前红、套件和准确增量复核范围；候选已提交并推送，
   本轮文档更新前工作树干净。正式 S0/S1/S2 复核不变，正式根无 shards/staging，
   未运行正式 S3–S5；该未验证边界在证据与状态板中均明确保留。

四项全部满足，候选可标 `IMPLEMENTED`，但按完成规则仍非 `DONE`。

### 35.2 Review round 6 开轮与边界

最近通过候选、当前候选与路径均按 workflow §4.4 在运行时解析；两者之间的
PLAY_GOVERNING diff 非空，故 Review round 6 开轮资格成立。复核角色须在一次性
worktree 中覆盖完整运行时派生 diff，不能只审实现者列出的范围；增量重点见
证据 §18.6 与 §19.5，尤其是完整逻辑等价、有界性、manifest lineage、
manifest-last 发布及两种无 manifest 残留的 fail-closed 行为。历史 Review
round 5 `PASS_WITH_NOTES` 只覆盖 BC-DATA-1…24，不覆盖 BC-DATA-25 新代码。

Review round 6 通过并由 Acceptance 消费后，正式 S3–S5 续跑仍须用户新授权。
S6–S9/G0/D0、audit、supersession、依赖/模型/API/GPU/Play/ID 与后续训练继续
未授权。Overall → `IMPLEMENTED_AWAITING_REVIEW_R6`。

## 36. Acceptance review-attribution ruling — round 24（2026-09-01）

Decision: **REVIEW_R6_FINDINGS_ACCEPTED / F20_F21_F22_ROUTED /
IMPLEMENTATION_REWORK_REQUIRED**

Acceptance 逐条复判 Review round 6：F20 `CLASS_1`、F21/F22 `CLASS_2`
分级均同意，无升降格；本轮无 CLASS_3。SP22-1/SP22-2 保持闭合，Review
已独立复现其修复前红与修后生产路径，本轮不重开。

### 36.1 F20 — 冻结 F2/分层分母的 split 侧信道（binding）

同意 `CLASS_1`。流式 `CatalogStream` 每次迭代产生新 dict，S7 在一次迭代中
写入的 `entry["split"]` 不会出现在 `build_g0_report()` 的后续重迭代中；因此
F2、`station_keys` 与 `stratified_denominators.frames_by_split` 被静默改写。

返工必须让 `build_g0_report()` 的**每一次** entry 迭代都获得由 S4
`split_of_frame` 派生的同一 split，且不得为了恢复侧信道而物化完整
`frames_catalog`。可用可重复迭代的 split-decorating adapter 或等价显式接口；
一次性 generator 不满足多遍消费。冻结 F1/F3/F4、F2 阈值与 g0_report schema
一字不改。

绑定回归名为
`test_streamed_g0_report_preserves_nonzero_f2_and_frames_by_split`：必须走生产
`stage7_gate()`，夹具在修前整表语义下产生非零 F2，并逐字段比较正式写出的
g0_report `floors.F2`（含 `station_keys`）与
`stratified_denominators.frames_by_split`；只比较 gate/unmet_floors 不合格。
候选修复回退后该测试必须以零值对非零值失败。

### 36.2 F21 — S5 选择精确有界返工；S6–S8 明确留债（binding）

同意 `CLASS_2`，并选择 Review 给出的 **(a) S5 有界返工**，拒绝以“16 GiB
大概率可过”的推算风险替代 BC-DATA-25 §33.2(5)。S5 位于下一次可能授权的
正式 S3–S5 路径，必须在该授权之前闭合。

现有 S5 语义是：对每个 object 按 `(camera_depth_m, frame_id)` 升序取
`contract.COLOR_SAMPLE_FRAME_COUNT` 个 observation，再做完全相同的 crop、HSV、
组一致性与 create-once 输出。返工须在扫描流时逐对象只保留该排序下最小 K 项，
驻留上界为 `O(object_count × K)`；不得改变 K、排序/平局语义、对象域、像素 crop、
颜色估计、字段或最终 payload 字节。`build_field_catalog` 的入口可调整，但生产
driver 与测试不得先构造全量 observation list 再声称下游有界。

绑定回归名为
`test_stage5_field_catalog_is_logically_identical_and_bounded_per_object`：每对象提供
明显多于 K 的跨帧 observation，完整 payload 与修前整表算法逐字段相等，并在
生产路径上证明任何时刻保留量不超过 `object_count × K`；仅检查最终候选数不合格。
修复回退后必须因全量驻留断言失败。

S6/S7/S8 的同型线性派生物**本轮不伪装成闭合，也不预授权执行**。它们登记为
`DEFERRED_BOUNDEDNESS_DEBT_BEFORE_STAGE_AUTHORIZATION`：任何 S6–S8 执行授权草案
都必须先回 Acceptance，分别给出输出下界相容的有界方案或量化例外裁定；本轮
只允许 F20 所需的 S7 正确性修复，不借机执行、改门或扩大输出域。

### 36.3 F22 — 选择代码收敛并纠正文证（binding）

同意 `CLASS_2`，选择 Review 给出的 **(a) 代码收敛**。`assign_splits()` 必须
调用 `assign_atoms(atoms)` 作为 atom 指派、连带规则与泄漏断言的唯一实现，
删除当前平行复制逻辑；整表路径只在共享 base 上装配不可绕过的 sample roles，
流式路径继续在同一 base 上产出 roles/summary。split 语义和所有输出字段不改。

新增结构回归
`test_legacy_and_streaming_split_paths_share_assign_atoms`，须证明整表与流式生产函数
都会调用共享实现；保留现有逐字段等价回归。实现证据 §18.2 必须注明旧候选的
“已抽出共用”曾被 Review F22 反证、现由本返工才真实成立；§19.5 (3) 的“只发现
一处”同步撤回，禁止静默改成当前时态掩盖历史错误。

### 36.4 返回条件与边界

- 只修改 F20–F22 所需的 `tools/dist_data/`、对应 `tests/test_dist_data_*.py`、
  实现证据与状态板；Review round 6 的七条观察项均非本轮范围，不得顺手扩张。
- 三条具名回归须在修复回退后各自以绑定症状失败，恢复后双解释器 focused、
  钉死环境全套、`git diff --check`、角色/文档检查通过；正式 S0/S1/S2 保持
  字节不变，正式根不得出现 shards/staging，禁止正式 S3–S5。
- 实现证据须分开写明：F20/F22 已闭合；F21 的 S5 分支已闭合；S6–S8
  boundedness debt 仍在且在各阶段授权前阻断，不得写成 BC-DATA-25 全债务清零。
- 修复后回同一 §4.3.1 停点。F20 必然产生非空 PLAY_GOVERNING diff，故稳定
  候选后开启 Review round 7；不触 Play 治理门三文件，无强制闭环轮义务。

本轮代码返工继续属于 round 21 已放行的 code/tests/temp-fixture 范围，不是正式
数据执行授权。正式 S3–S5、S6–S9/G0/D0、audit、supersession、依赖/模型/
API/GPU/Play/ID 与后续训练全部继续未授权。Overall →
`IMPLEMENTATION_REWORK_REQUIRED_R24_F20_F21_F22`。

## 37. Acceptance stop-point recheck — round 25（2026-09-01）

Decision: **STOP_POINT_NOT_CONFIRMED / F21_STALE_BOUNDEDNESS_CLAIM_REWORK_REQUIRED /
REVIEW_ROUND_7_NOT_OPENED**

本轮只复查 workflow §4.3.1 的四项停点条件，不签发独立 Review verdict，
也不改变 §36 的 F20–F22 功能合同、冻结门值或任何执行授权。

### 37.1 四项停点条件

1. **范围与接口冻结：满足。** 返工批只触及 §36.4 允许的三个
   `tools/dist_data/` 模块、一份具名回归、实现证据与状态板；F20 的 split
   装饰、F21 的 S5 精确有界选择和 F22 的共享 `assign_atoms()` 均按 binding
   条款落地，schema、阈值、对象域、排序和正式工件零变化。
2. **相称的实现者测试/编译：满足。** Acceptance 在主树独立复现双解释器
   focused 各 **435** 条通过；实现者钉死环境全套 **970** 的新增失败仍为零。
   一次性隔离副本中先 `git revert -n` 返工提交、再只恢复候选测试，三条具名
   回归恰以 `0 != 4`、`64 not <= 21`、`1 != 2` 变红；恢复三个生产模块后
   3/3 转绿且与主树逐字节相同。
3. **已知 Unity 失败：满足/不适用。** 本批仍是纯离线数据工具代码，没有待修
   Unity 失败；本轮不新增 `UNITY_NA` 或任何运行时 verdict。
4. **复核目标、状态、候选与未验证风险：不满足。** 候选已提交并推送，正式根
   仍恰有 S0/S1/S2 三件工件（5,014 / 28,574,739 / 2,220,725 bytes），零
   `shards/`/`.staging/`，且未执行正式 S3–S5；但是 Review round 6 F21 已明确
   反证的旧断言仍同时存在于 `run_pipeline.CatalogStream` docstring 与实现证据
   §18.2：二者仍声称“不支持下标”会让**任何**全集物化直接失败。真实代码的
   S6/S7/S8 仍分别物化深度样本、候选和 `amodal_box_of`；§20.2 虽正确登记
   `DEFERRED_BOUNDEDNESS_DEBT_BEFORE_STAGE_AUTHORIZATION`，却不能使前述相反的
   现行文字自动失效。候选因此仍会把未来授权检查范围错误缩小，违反状态/风险
   准确性与失效文字同批修正纪律。

四项未全部满足，**Review round 7 不开启**；功能修复、三条回归和正式根边界
全部保留，不因这项文字阻断而回滚。

### 37.2 返回 Implementation 的唯一窄修

1. 把 `CatalogStream` docstring 的绝对断言改为精确事实：它只强制消费者经可重复、
   逐 shard 校验的迭代接口取数；缺少下标**不阻止**消费者用 `list()`/`append`
   物化派生全集，有界性必须由每个消费点分别证明。明确 S5 已由选择器闭合，
   S6–S8 债务仍在。
2. 在实现证据 §18.2 保留旧句的历史可见性并标注其被 Review F21 反证；注明
   round 24/本返工只使 S5 成立，S6–S8 仍受 §20.2 的授权前阻断。不得静默改成
   当前时态，也不得把 BC-DATA-25 (5) 款首总则写成全部闭合。
3. 此精确文字闭合没有可写的行为断言，按 workflow §4.4 走
   `NOT_MECHANIZABLE` 定点复看：返回后 Acceptance 逐字检查上述两处；既有三条
   round-24 回归仍须保持 3/3 通过。不得改生产行为、测试、七条 Review 观察项、
   正式工件或授权边界。

修正仍属 round 21 放行的 code/evidence 范围；返回同一 §4.3.1 停点。通过后
PLAY_GOVERNING diff 仍非空，才开启 Review round 7。正式 S3–S5、S6–S9/G0/D0、
audit、supersession、依赖/模型/API/GPU/Play/ID 与后续训练继续未授权。
Overall → `IMPLEMENTATION_REWORK_REQUIRED_R25_F21_STALE_BOUNDEDNESS_CLAIM`。

## 38. Acceptance targeted closure and stable-candidate confirmation — round 26（2026-09-01）

Decision: **THIRD_SITE_HISTORICAL_QUESTION_NONBLOCKING / STOP_POINT_CONFIRMED /
IMPLEMENTED / REVIEW_ROUND_7_OPENED**

本轮按 §37.2 的 `NOT_MECHANIZABLE` 路径逐字复看两处更正，并重新核对
workflow §4.3.1 四项停点条件；不签发独立 Review verdict，不改变 §36 的功能
合同、冻结门值或执行授权。

### 38.1 第三处文字裁定

实现证据 §18.6 (3) 的「`CatalogStream` 不支持下标是否足以挡住物化全集的
写法」**不是第三条现行事实主张**，无需再返工：

1. 它以问句写在旧候选的「给复核角色的复核范围」中，记录的是当轮要求复核的
   可证伪问题，而不是自证结论；
2. 复核轮 6 F21 已正式回答「挡不住」，且证据 §21.2 明确把该问句与 F21 的答案
   相连，没有把它引用为当前闭合依据；
3. 当前 docstring、§18.2、§20.2、§21.1 和状态板均一致写明：有界性逐消费点
   证明，只有 S5 已闭合，S6–S8 仍是授权前阻断债务。

因此保留 §18.6 (3) 才能如实保存旧轮次的复核问题；把历史问句误作现行断言并
静默改写，反而会抹掉 F21 的发现来源。未来状态、授权或实现文证不得把该问句
当作肯定答案引用。

### 38.2 四项停点条件

1. **范围与接口冻结：满足。** 返回批只改两处指定文字和状态/证据；唯一
   PLAY_GOVERNING hunk 是 `CatalogStream` docstring。生产行为、测试、schema、
   门值、正式工件和授权边界均未改变。
2. **相称的实现者测试/编译：满足。** 实现者报告双解释器 focused 各 435、
   round-24 三条回归 3/3、钉死环境全套 970 且新增失败 0。Acceptance 再独立
   复现双解释器 focused 各 **435/435** 和三条回归 **3/3**。
3. **已知 Unity 失败：满足/不适用。** 仍是纯离线数据工具候选，没有待修 Unity
   失败；不新增 `UNITY_NA` 或运行时 verdict。
4. **复核目标、状态、候选与未验证风险：满足。** 两处旧绝对断言已按 §37.2
   更正；§38.1 已裁定第三处历史问句。候选已提交并推送；正式根只读复核仍恰有
   S0/S1/S2 三件工件（5,014 / 28,574,739 / 2,220,725 bytes），零 `shards/`、
   零 `.staging/`，未运行正式 S3–S5。S6–S8 有界性债务和所有未授权边界均
   保持显式。

四项全部满足，§4.3.1 停点成立。Overall → `IMPLEMENTED_AWAITING_REVIEW_R7`。

### 38.3 Review round 7 与继续边界

按 workflow §4.4 从复核文件最后一个 `passed_candidate` 运行时解析基线；到当前
候选的 PLAY_GOVERNING diff 非空，故**开启 Review round 7**。复核须在一次性
worktree 新鲜重读完整运行时派生差异，重点覆盖证据 §20.6 / §21.4、F20 的每遍
split decoration、F21 的 S5 payload 等价与对象×K 有界性、F22 的共享
`assign_atoms()`，并核对 §38.1 的历史问句裁定没有被当成现行肯定主张。

本轮没有正式数据执行授权。即使 Review 通过，也须先回 Acceptance 消费 verdict，
再由用户另行授权才能恢复正式 S3–S5；S6–S9/G0/D0、audit、supersession、依赖/
模型/API/GPU/Play/ID 与后续训练全部继续未授权。

## 39. Acceptance review-consumption ruling — round 27（2026-09-01）

Decision: **PASS_WITH_NOTES_CONSUMED / F20_F21_S5_F22_CLOSED /
REVIEW_GATE_CLOSED / AWAITING_FRESH_FORMAL_S3_S5_AUTHORIZATION**

Acceptance 独立复判并消费 Review round 7；通过候选由复核文件的机读
`passed_candidate` 行派生，不在本文件复抄 SHA。

### 39.1 Verdict 与 finding 归因

- `PASS_WITH_NOTES` 有效：复核在一次性 worktree 覆盖完整运行时派生
  PLAY_GOVERNING diff，复现三条修复前绑定红、修复后绿、F20 独立探针与
  F21 修前基准转写，并记录零新增阻断 finding、零 CLASS_3。
- F20、F21 的 S5 分支和 F22 全部闭合；轮 25 两处文字更正与轮 26 的历史
  问句裁定均获独立附议。Acceptance 自己在轮 25 已完成三条阻断回归的隔离
  回退复算，因此 workflow §4.4 的闭合链完整，不需再开返工。
- Review 对纯离线增量的累计 `UNITY_NA` 附议予以接受。它只覆盖当前离线
  工具候选；一旦越出该范围即失效。

### 39.2 三项 notes 的处置

1. `SplitDecoratedStream` 未透传 `manifest`/`reference`：当前 S7 无调用点，
   缺失时为 `AttributeError` 的 fail-closed 方向，**不阻断本候选**。未来若有
   消费者经装饰流读取 lineage，须在其实现范围内先补透传与回归。
2. S5 为对象域扫描和 observation 选择各完整解压一遍 shards：这是已披露的
   性能成本，不改变输出、确定性或对象×K 驻留上界，**不要求代码返工**；任何
   正式 S3–S5 授权都须把该成本列为运行监控项。
3. Review round 6 的七条观察项继续原样登记；本轮没有授权顺带实现它们。

S6/S7/S8 的帧线性派生物仍是
`DEFERRED_BOUNDEDNESS_DEBT_BEFORE_STAGE_AUTHORIZATION`。这项债务不推翻 S5
闭合，但会在任何 S6–S8 执行授权草案前阻断，必须先回 Acceptance 给出有界
方案或量化例外裁定。

### 39.3 当前门与用户决策点

Overall → `REVIEW_R7_PASS_CONSUMED_R27_AWAITING_FORMAL_DATA_AUTHORIZATION`。
该状态**不是 `DONE`**：正式 S3/S4/S5 工件尚不存在，G0/D0 与审计也未执行。

本轮不产生执行 GO。下一步只允许用户决定是否基于已复核候选签发新的正式
S3–S5 continuation 授权；若授权，仍须先核对既有 S0/S1/S2 工件完整性、候选/
工作树一致性和零 orphan staging，且不得重写 S0–S2。S6–S9/G0/D0、audit、
retry/supersession、依赖/模型/API/GPU/Play/ID 与后续训练全部继续关闭。

## 40. Acceptance limited-continuation authorization — round 28（2026-09-01）

Decision: **FORMAL_S3_S5_CONTINUATION_AUTHORIZED /
PREAUDIT_UPPER_BOUND_DIAGNOSTIC_ONLY**

用户逐字授权「授权，继续」，已当场记入 `docs/authorizations.md`。其直接上文
是 §39.3 的唯一决策点，因此本轮只把该 GO 解释为下述正式 S3–S5 continuation，
不恢复或扩张其他阶段。

### 40.1 执行前硬门（binding）

1. 从复核文件最近一行 `passed_candidate` 运行时解析通过候选，断言其为当前
   HEAD 祖先，且候选后的 PLAY_GOVERNING diff 为空；工作树须干净，使用钉死的
   `.venv-yoloe` 环境。可派生 SHA、attempt 名和工件哈希不得抄入手维护文档。
2. 只读核验正式根：既有 S0 `contract`、S1 `inventory`、S2 `layout` 三件
   create-once 工件必须完整、可解析、lineage 自洽并与既有执行收据相符；S3
   `frames_catalog`、S4 `splits`、S5 `field_catalog` 必须缺席；全根必须零
   `.staging/`，也不得有无 manifest 的 orphan `shards/`。任一不符立即停止。
3. 不运行任何会重写 S0–S2 的阶段，不调用可能自动进入 S9 的总控 `--run`
   路径，不修改生产代码、测试、合同、依赖或冻结参数。

### 40.2 唯一获准的正式 continuation（binding）

1. 以既有 S0–S2 为只读输入和同一 create-once attempt，按已复核生产入口依次
   调用 `PipelineDriver.stage3_frames_catalog()` → `stage4_splits()` →
   `stage5_field_catalog()`；不得复制阶段算法或绕开 manifest-last 发布路径。
2. S3/S4/S5 每阶段完成后立即核验其工件可读性、manifest/shard lineage、
   create-once 身份与零 `.staging/`；同时确认 S0–S2 字节未改。S4 若返回
   terminal，立即停在 S4，不写 S5 或 S9。
3. 任一前置不符、异常、进程终止、发布残留或阶段 terminal：立即停下，原样
   保留现场并返回 Acceptance；本授权只含这一次 continuation，**不授权第二次
   重试、清理、删除、续传或 supersession**。
4. 把 S5 双遍 shard 解压作为显式监控项：用进程外观测或既有遥测记录各阶段
   wall time 与可得的 peak RSS，至少单列 S5；观察结果只作性能披露，不得据此
   改代码、K、样本、split、阈值或对象域。缺少现成观测能力时先返回，不为此
   加 instrumentation code。

### 40.3 诊断报告与返回（binding）

沿用唯一报告
`docs/evidence/P1-VLM-DATA-001-S0-S5-pre-audit-upper-bound.md`：标题、摘要和
每组数字必须保留逐字标签 **「审计前上界、非门 verdict」**。S3–S5 全部成功
才可从同一未 supersede 的 S0–S5 工件只读计算 `U_F1`…`U_F4`，状态仍统一为
`NOT_EVALUATED_PRE_AUDIT`；不得写 audit、调用 S7 或签发 G0 verdict。若提前
停机，U 表保持 `UNAVAILABLE_S0_S5_INCOMPLETE`，只记录阶段与 fail-closed 原因。

Implementation 返回时更新实现证据和状态板，证明 S0–S2 未改、获准工件边界、
诊断标签、性能观察与工作树范围，运行角色/文档检查后提交并推送。零
PLAY_GOVERNING 修改时不开新 Review 轮，先回 Acceptance 做执行归因。

### 40.4 继续关闭的边界

S6/A1–A3、S7/G0、S8/D0、S9、正式 audit、retry/supersession、C1/D1–D3、
依赖/模型/下载/教师/verifier/API/GPU、Unity/Edit Mode/Play、任何
scenario/session/run ID、场景/车辆修改与后续训练全部未授权。Overall →
`FORMAL_S3_S5_CONTINUATION_AUTHORIZED_R28_PREAUDIT_UPPER_BOUND_ONLY`。

## 41. Acceptance execution attribution and archive-scale rework — round 29（2026-09-01）

Decision: **IMPLEMENTATION_REWORK_REQUIRED / S4_MANIFEST_SCALE**

### 41.1 正式 continuation 归因

接受 §40 的执行合规性与收据：32/32 执行前硬门通过；S0–S2 前后字节不变；
三个已复核阶段入口依次成功，S4 没有 terminal；每阶段立即核验通过；全根零
`.staging/` / `.publishing/`；没有 aggregate `--run`、重试、清理、supersession、
代码/测试改动或未授权资源使用。轮 28 的一次性 GO 已耗尽。S3–S5 现有工件原样
保留为本次执行现场，不覆盖、不删除，也不据此签发 G0 verdict。

报告的 `U_F1`…`U_F4` 标签和状态合规：它们仍只是「审计前上界、非门 verdict」
且一律 `NOT_EVALUATED_PRE_AUDIT`。`U_F1`、`U_F3`、`U_F4` 在零审计降级的乐观
假设下已经低于冻结 floor；16 个 class-verifiable 对象的结构上限也使 F1 的 60
对象 floor 在本 attempt 上不可达。这是数据充分性事实，不是 G0 verdict，既不授权
审计，也不自动授权补采集或回调门值。

### 41.2 SP29-1 — S4 manifest 归档尺度违约（`CLASS_2`）

真实归档首次证明 `splits` manifest 为 **515,074,557 B**，其中外层 `atoms` 块的
磁盘跨度为 **512,888,211 B**，`near_duplicate_pairs` 键+值实际占
**512,887,863 B / 2,663,282 对**；每个普通
JSON 消费者因此产生约 2.5–3.6 GiB 驻留。它违反 BC-DATA-25 §33.2(4) 的
「小型摘要留在 manifest」和 §33.2(5) 的生产消费有界要求。能够在本机完成不把
违约降成性能 note；Review round 7 的通过只覆盖当时的代码与合成尺度证据，历史
verdict 保留，但不能覆盖这项后来才出现的真实尺度反证。

### 41.3 BC-DATA-26 — 近重复闭包的有界证明表示（binding）

1. **研究与 split 语义不变。** pHash 定义、Hamming ≤ 8、跨族全对比较、并查集
   连通分量、`atom_id`、`near_duplicate_pair_count`、atom/split/frame/role/
   exposure/leakage 输出及排序全部保留；不得采样 pairs、改变阈值或拆开已合并 atom。
2. **取消非合同性的全量 pair 调试载荷。** `near_duplicate_pairs` 从 S4 manifest
   payload 删除；该成员从未被 §2.5/BC-DATA-25 冻结为研究输出，也没有生产消费者，
   不得为维持它而再次让 manifest 随合格 pair 数二次增长。
3. manifest 改存确定性的 `near_duplicate_union_witnesses`：仍按当前
   `(left_frame_id, right_frame_id)` 字典序遍历，只在该 pair 首次连接两个不同
   family component 时记录这一对。witness 数必须恰为
   `family_count - atom_count`，每对都满足跨族与阈值条件，按同顺序重放必须重建
   完全相同的最终 family→atom 分量。全量合格 pair 仍逐个计入
   `near_duplicate_pair_count`，但不得驻留；manifest 中任何成员均不得按合格
   pair 数增长。
4. 至少新增两条生产语义回归：
   `test_archive_scale_near_duplicates_keep_s4_summary_bounded` 用大量同 pHash 帧证明
   pair count 二次增长而 retained witnesses 仍受 family 数上界约束、无
   `near_duplicate_pairs`；
   `test_union_witnesses_replay_exact_atoms_and_preserve_pair_count` 证明小夹具上 count、
   components、atom ids 与修前路径逐字等价。前一条在修前生产代码上须以全量列表/
   上界断言变红，修后转绿。
5. 返工只准修改 `tools/dist_data/` 的 S4 近重复装配/必要的类型与对应
   `tests/test_dist_data_*.py`、实现证据和状态板；不改门值、S0–S3/S5–S9 语义、
   正式工件或依赖。实现者须跑相称 focused 与钉死环境全套，更新风险与范围后返回
   Acceptance 的 §4.3.1 停点；PLAY_GOVERNING diff 非空时再开 Review round 8。

### 41.4 其余观察的裁定与边界

- S5 普通信封的 `inputs: []` **不追溯构成本轮失败**：BC-DATA-25 §33.2(3) 与
  round-22 SP22-1 明确约束 S3/S4 两个 composite manifest，§40.2 的
  `manifest/shard lineage` 也只适用于这两类工件。它登记为
  `DEFERRED_S5_LINEAGE_DEBT_BEFORE_SUPERSESSION_OR_STAGE6_AUTHORIZATION`；未来若授权
  S5 supersession 或 S6，须先由 Acceptance 冻结 S5 对 S3/layout 的准确 refs 与
  生产回归。本轮不得顺带改。
- S5 双遍解压仍是 round 27 已接受的有限性能成本；3-atom 导致 train 为空是冻结
  split 算法在真实输入上的确定性结果，不是实现缺陷；F1 结构上限属于数据不足。
- 现有 S3–S5 不得被下游当作可放行候选。S6/A1–A3、S7/G0、S8/D0、S9、audit、
  retry/supersession、补采集、模型/API/GPU/Play/ID 与后续训练全部继续未授权。
  Overall → `IMPLEMENTATION_REWORK_REQUIRED_R29_S4_MANIFEST_SCALE`；下一位是
  Implementation，且仅执行 §41.3 的零消耗代码/测试返工。

## 42. Acceptance stop-point confirmation — round 30（2026-09-01）

Decision: **STOP_POINT_CONFIRMED / REVIEW_ROUND_8_OPEN**

### 42.1 §4.3.1 四项条件

1. **范围与接口冻结：满足。** 运行时派生的上一通过候选到当前候选，
   PLAY_GOVERNING 差异恰为 `tools/dist_data/make_splits.py` 与新增
   `tests/test_dist_data_round29.py`；其余改动仅为实现证据和状态板。BC-DATA-26
   的 pair count、components、atom ids 与 split 语义保持冻结，S0–S3/S5–S9、
   阈值、依赖和正式工件均未改。
2. **相称测试：满足。** 实现者记录双解释器 focused 437/437（默认解释器仅
   Pillow 金标 9 skip）和钉死环境全套 972、仅既有两项 CSRT/opencv-contrib
   失败。Acceptance 在主树独立复现钉死环境 focused **437/437** 与两条具名回归
   **2/2**；并在一次性隔离 worktree 对修复提交执行 `git revert -n`、保留候选测试，
   两条回归恰以「仍携带 540000 对全量列表」和「缺少 union witnesses」**2/2 变红**；
   恢复候选后 **2/2 转绿**，隔离树与主树均干净。
3. **Unity 条件：满足。** 本批只改纯离线 S4 数据工具与 Python 回归，不触及 Unity/
   Play 行为；既有累计 `UNITY_NA` 只覆盖到 Review round 7，本轮仍须 Review round 8
   独立附议，Acceptance 不预签新的 concurrence。
4. **候选、证据与风险：满足。** 候选已提交并推送；证据 §23、状态板与准确复核范围
   已更新。正式根仍为 92 文件、零残留且未 supersede；S5 lineage debt、S6–S8
   boundedness debt、乐观上界低于 floors 以及未来新表示 S4 必须经用户授权新 attempt
   的边界均未被遮蔽。

### 42.2 Review round 8 开轮与边界

按 workflow §4.4 运行时解析最近 `passed_candidate`；到当前候选的
PLAY_GOVERNING diff 非空且恰为上述两个文件，故 Review round 8 开轮资格成立。
Review 必须在一次性 worktree 新鲜重读完整差异，至少核对：witness 在 union 前判定、
全量 pair count 不被缩减；`replay_union_witnesses` 的 fail-closed 分支；修前转写与
components→atoms 等价；生产 S4 manifest 确实不再含全量 pair 成员；除 pair 调试
载荷外没有改变 split、lineage、计数或门语义。复核结果追加到既有 review 文件，
通过轮必须写机读 `passed_candidate`；发现任何 `CLASS_1/2` 只写 finding 并退回实现。

Overall → `IMPLEMENTED_AWAITING_REVIEW_R8`。本轮不开正式 supersession、S6–S9/G0/D0、
audit、补采集或任何资源；Review 通过后也须先回 Acceptance 消费 verdict，随后是否
为新表示 S4/S5 授权 supersession 仍由用户另行决定。

## 43. Acceptance review-consumption ruling — round 31（2026-09-02）

Decision: **REVIEW_R8_PASS_CONSUMED / AWAITING_USER_SUPERSESSION_DECISION**

### 43.1 通过轮消费

Review round 8 的机读 `passed_candidate` 有效；该候选是当前 HEAD 的祖先，候选之后
PLAY_GOVERNING diff 为零，主树干净。接受其 `PASS_WITH_NOTES`：§42.2 五项检查均由
Review 独立复现，BC-DATA-26 的全对比较、全量 count、components、`atom_id` 与 split
语义保持不变，全量 pair 载荷被 family-bounded deterministic witnesses 取代且生产重放
fail-closed。两条具名回归在修前精确 2/2 红、恢复候选后 2/2 绿；冻结正式 manifest
只读重放得到 8 family、5 witness、同一 3 atom，count 2,663,282 不变，canonical
atoms 块 512,888,212 B → 1,247 B。零 `CLASS_1`/`CLASS_2`/`CLASS_3` finding。

接受 Review 对本候选纯离线增量的 `UNITY_NA` 附议，累计维持 rounds 1–8。BC-DATA-26
的代码复核门至此关闭；work item 不因此 `DONE`，也不产生正式 supersession 授权。

### 43.2 四项 notes 的裁定

1. `len(pair) != 2` 分支缺少直接测试属于非阻断覆盖债；JSON 生产输入为 list，其他三条
   拒绝分支及双不变量已有覆盖。当前候选不返工；若用户授权下一代码批次，顺带补入该
   fail-closed 回归，不单独为此重开 Review。
2. 字节口径按 Review 实测校正：**512,888,211 B 是外层 `atoms` 块值的磁盘跨度**，
   `near_duplicate_pairs` 键+值为 **512,887,863 B**；canonical 整块为
   **512,888,212 B**。§41.2 已就地更正；pairs 占比 99.99993%，原 `CLASS_2`
   归因与有界修复结论不变。
3. 证据 §23.1 的「零引用」应精确读作「零生产消费者」：候选中的引用只在生产装配
   `make_splits.py` 与 round-29 的 legacy 对照回归。Review 的全仓复核已证实核心主张；
   本裁定作为后续引用的权威口径，不改写实现角色的历史证据。
4. focused 的准确形态是主树 python3 **437 ran / 9 skip / 0 failed**、钉死环境
   **437/437 / 0 skip**，复核副本两解释器各 **437 ran / 46 skip / 0 failed**。
   状态板使用这一完整口径；旧压缩短句不再作为测试形态来源。

四项均不改变代码、门语义、正式工件或 verdict，因此本批为零 PLAY_GOVERNING 的
Acceptance 消费批，不开 Review round 9。

### 43.3 未授权边界与下一决策

现有正式 S0–S5 继续 create-once 原样保留。以新表示物化正式 S4/S5 需要用户另行授权
新 attempt；在任何 supersession 或 S6 授权前，Acceptance 还必须先冻结 S5 对 S3/layout
的准确 refs 与生产回归，闭合
`DEFERRED_S5_LINEAGE_DEBT_BEFORE_SUPERSESSION_OR_STAGE6_AUTHORIZATION`。S6–S9/G0/D0、
audit、补采集、依赖/模型/API/GPU/Unity/Play/ID 与后续训练全部继续未授权，乐观上界低于
floors 的数据充分性事实不变。

Overall → `REVIEW_R8_PASS_CONSUMED_R31_AWAITING_USER_SUPERSESSION_DECISION`。下一位是
User：决定是否授权上述有界 supersession 路径；若 GO，先回 Acceptance 冻结 S5 lineage
合同，再交 Implementation，不能直接运行正式 stage。

## 附录 A — 冻结根清单与用途类 pattern 映射（S1 的闭集输入）

**Pattern 语义（AR2-3）**：POSIX glob，`*` 不跨 `/`、`**` 跨任意层；
`<RT>` = `runtime/test-results` 前缀宏。表按 A.1→A.2→A.3 顺序求值，
pattern 设计为互不重叠：S1 对每个被枚举文件断言**恰匹配一个**
pattern，零或多匹配即硬错误。jpg 的同名 sidecar json 随其 jpg 归行；
truth pattern 单列；run 目录内其余元数据（manifest/scenario/summary
等）不入图像清单，由 S2 作字节提供者按需读取并哈希绑定。计数为构思
侧盘点（S1 以实测为准；jpg 总量应对账 24,152）。「族」= §2.5 复制族
的初始划分（近重复并簇可再合并）。

### A.1 default 布局类帧归档（relocations 与 m3 基线一致，S2 从归档字节复核）

| 族 | pattern（jpg；truth 另注） | ~帧 | 用途类 | 下限/test 资格 |
|---|---|---|---|---|
| m3-armA | `<RT>/p1-m3-body-001-arm-a-*-post-run/frames/frame_*.jpg`（5 目录）；truth `runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4/m3_body_truth.jsonl`、`runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2/m3_body_truth.jsonl`、`runtime/runs/p1-m3-body-001-arm-a-trial-[345]/m3_body_truth.jsonl`（合计 5 份） | 5×128 | `VALID_FORMAL` | ✓/✓ |
| m3-armB | `<RT>/p1-m3-body-001-arm-b-trial-*-post-run/frames/frame_*.jpg`（4 目录，B3 无归档）；`runtime/frames.arm-b-trial-3-shared-residue-hold/frame_*.jpg`（B3 残留台账 hold）；truth `runtime/runs/p1-m3-body-001-arm-b-trial-*/m3_body_truth.jsonl` | 4×128+128 | `VALID_FORMAL`；B3 残留 = `VALID_PARENT_HOLD` | ✓/✓ |
| m3-void（并入 armA 族） | `runtime/frames.arm-a-trial-*-void-attempt-*-hold/frame_*.jpg`；truth `runtime/m3_body_truth.arm-a-trial-*-void-attempt-*-hold.jsonl` 与 `runtime/runs/p1-m3-body-001-arm-a-trial-*-void-attempt-*-hold/m3_body_truth.jsonl`；同名根级 hold 伴生文件随行 | 46+54+128+128 | `VOID_TRIAL_HOLD` | ✗/✗ |
| detect-scout1 | `<RT>/p1-detect-001-scout-1-closed-exchange/frames/frame_*.jpg`；truth `runtime/p1-detect-scouting/p1-detect-001-scout-1/truth/frame_*.json` | 768（truth 705；未 join 帧按 §2.3 边界条款处理） | `VALID_SCOUTING_CLOSED` | ✓/✓ |
| rate-b2-formal | `<RT>/ut-p1-m2-rate-002-b2-formal/r20-follow-[12]/pass/frames/frame_*.jpg`；`<RT>/ut-p1-m2-rate-002-b2-formal/r20-follow-3/attempt-2-complete-admissible/frames/frame_*.jpg` | 3×512（revision 1 误记 4×512，本轮更正） | `VALID_FORMAL` | ✓/✓ |
| rate-b2-invalid（并入 rate 族） | `<RT>/ut-p1-m2-rate-002-b2-formal/r20-follow-3/attempt-1-invalid-s1-pause-gap/frames/frame_*.jpg`；`<RT>/ut-p1-m2-rate-002-002-rerun-stopped-scene-defect/frames/frame_*.jpg`；`<RT>/ut-p1-m2-rate-002-001-case3-attempt1/frames/frame_*.jpg`；`<RT>/ut-p1-m2-rate-002-002-b2-smoke/attempt1-backlog-race/frames/frame_*.jpg`（revision 1 漏列，本轮补上） | 512+259+759+497 | `PROTOCOL_INVALID` | ✗/✗ |
| rate-aux（并入 rate 族） | `<RT>/ut-p1-track-002-001-b2-pilot/pass/frames/frame_*.jpg`、`<RT>/ut-p1-m2-rate-002-001-case3-4-rerun-pass/frames/frame_*.jpg`（`VALID_FORMAL`）；`<RT>/ut-p1-m2-rate-002-002-b2-smoke/attempt2-pass/frames/frame_*.jpg`、`<RT>/ut-p1-m2-rate-002-002-batch-b-integration/release-attempt/frames/frame_*.jpg`（`SMOKE`） | 512+266+391+310 | 前二 ✓/✓；后二 ✗/✗ |
| rate-calib | `<RT>/ut-p1-m2-rate-002-002-b2-smoke/calibration-hold/frames/frame_*.jpg`；`<RT>/ut-p1-m2-rate-002-002-batch-b-integration/calibration-hold/frames/frame_*.jpg`；`<RT>/ut-p1-m2-rate-002-002-rerun-prep/ordinary-frames-before-rerun/frame_*.jpg` | 98+51+6 | `CALIBRATION` | ✗/✗ |
| scene-val | `<RT>/ut-p1-scene-002-001-attempt3-pass/cleared-active/frames/frame_*.jpg` | 256 | `VALID_FORMAL` | ✓/✓ |
| 1b-diag | `runtime/frames.1b-diagnostic-hold/frame_*.jpg` | 128 | `DIAGNOSTIC_HOLD` | ✗/✗ |
| unreleased-0820 | `runtime/frames.unreleased-play-20260820-hold/frame_*.jpg`；truth `runtime/m3_body_truth.unreleased-play-20260820-hold.jsonl` 及同名根级 hold 伴生文件 | 29 | `UNRELEASED_PLAY_HOLD` | ✗/✗ |

### A.2 scene-004 布局类帧归档（2 条 relocations；字节提供者 = `runtime/scenario_config.p1-scene-004.hold.json`，manifest sha `00c8802a…` 匹配）

| 族 | pattern | ~帧 | 用途类 | 下限/test 资格 |
|---|---|---|---|---|
| s004-scout（scout-3 并入 scout-4 族） | `<RT>/p1-scene-004-scout-4-closed-exchange/frames/frame_*.jpg` + truth `runtime/p1-scene-004-scouting/p1-scene-004-scout-4/truth/frame_*.json`；`<RT>/p1-scene-004-scout-3-protocol-invalid-same-id-retry-20260729/frames/frame_*.jpg` + truth `<RT>/p1-scene-004-scout-3-protocol-invalid-same-id-retry-20260729/session/truth/frame_*.json` | 2405+2431 | scout-4 = `VALID_SCOUTING_CLOSED`；scout-3 = `PROTOCOL_INVALID` | scout-4 ✓/✓；scout-3 ✗/✗ |
| s004-qual（qual-1/2 并入 qual-3 族） | `runtime/frames.qual3-leftover-hold/frame_*.jpg`（qual-3 PASS 的留存）；`<RT>/p1-detect-001-qual-2-protocol-invalid-exchange/frames/frame_*.jpg`；`<RT>/p1-detect-001-qual-1-premeasurement-exchange/frames/frame_*.jpg` | 4096+3668+188 | qual-3 = `VALID_PARENT_HOLD`；qual-2 = `PROTOCOL_INVALID`；qual-1 = `CALIBRATION` | qual-3 ✓/✓；余 ✗/✗ |
| s004-smoke | `runtime/rate-study/P1-M2-RATE-003-CLOCKSMOKE/smoke-*/frames/frame_*.jpg`；`<RT>/rs3-clock-smoke/phase1-hold/frames/frame_*.jpg` | 2888+173 | `SMOKE` | ✗/✗ |

### A.3 inventory-only 与排除 pattern

| pattern | 内容 | 处置 |
|---|---|---|
| `runtime/qual3-preview/frame159-overlay*.jpg` | 叠加图 2 | `DERIVED_OVERLAY` |
| `runtime/runs/*/init-frame*.jpg`、`runtime/runs/*/reference*.jpg` | run 起始/参考预览（rate 各 run 与 qual-1/2） | `PREVIEW` |
| `runtime/rate-study/staging/*/init*.jpg`、`runtime/rate-study/previews/*.jpg`、`runtime/rate-study/P1-M2-RATE-002-B2/previews/*.jpg`、`runtime/rate-study/P1-M2-RATE-002-B2/calibrations/rate20/reference*.jpg` | rate 预览与标定参考 | `PREVIEW` |
| `<RT>/ut-p1-m2-rate-002-002-batch-b-integration/campaign/**/reference*.jpg`、`<RT>/ut-p1-m2-rate-002-002-batch-b-integration/campaign/**/previews/*.jpg`、`<RT>/ut-p1-m2-rate-002-002-rerun-stopped-scene-defect/campaign/**/reference*.jpg`、`<RT>/ut-p1-m2-rate-002-002-rerun-stopped-scene-defect/campaign/**/previews/*.jpg` | campaign 标定/预览 | `PREVIEW` |
| `runtime/p1-detect-scouting/p1-detect-001-scout-1/reference*.jpg`、`runtime/p1-scene-004-scouting/p1-scene-004-scout-4/reference-preview.jpg` | scouting session 参考预览 | `PREVIEW` |
| `docs/evidence/P1-M3-BODY-001-1b/frame_*.jpg` | 1b 人检副本 2 | `DOC_COPY`（按内容哈希折叠入源 lineage） |
| `runtime/models/**`、`runtime/yoloe/**` | 模型包自带图片 | `THIRD_PARTY_ASSET`（根级排除，不入行级枚举） |
| `runtime/p1-scene-006/probe-baseline-vfov60/frames/*.jpg` | 旧 baseline 探针 jpg 107 张；F23 已否定灰色替身外观保真 | `INVALID_RENDER_PROBE`（仅 inventory） |
| `runtime/p1-scene-006/probe-candidate-vfov40/frames/*.jpg` | 旧 candidate 探针 jpg 107 张；F23 已否定灰色替身外观保真 | `INVALID_RENDER_PROBE`（仅 inventory） |
| `<RT>/rs3-clock-smoke/phase1-hold/frames/init-box-preview.jpg` | 绿色初始化框派生图；不得继承同目录原始帧的 `SMOKE` 资格 | `DERIVED_OVERLAY` |
| `runtime/p1-scene-006/probe-*/truth/frame_*.json` | 探针 truth sidecar；配套 jpg 按上两行另行排除 | `PROBE_TRUTH_ONLY` |
| `runtime/frames/` | 活动桥目录 | 断言为空 |

## 附录 B — 构思侧预扫描 2（量级预估；只作动机，未经复核，不进证据链）

方法（零成本只读）：以 §2.4 同款投影约定（sidecar 基向量 + 归档
内参）对 10 个族抽样 ~1,570 帧，全 779 实例作遮挡体，min-side
12 px、IoA ≥ 0.5 画家序近似；近平面角点直接丢弃（**低估**大近景）、
nature/prop AABB 过包围（**高估**遮挡）、站位跨族未并箱（**高估**
簇数）、以皮肤代号代颜色（对颜色词**高估**唯一性）。先以 m3 arm A
归档真值框验证约定：目标中心投影偏差 4–6 px（根锚点 vs 网格中心的
预期偏置）。

量级结果（对象×站位簇 = 属性唯一单元；族×对象 = 统计簇）：

| 族 | 抽样帧 | 同框≥2 占比 | 站位簇 | class 唯一单元 | 出现对象 |
|---|---|---|---|---|---|
| m3-armA | 160 | 80% | 1 | 3 | 3 |
| m3-armB | 128 | 54% | 5 | 9 | 3 |
| detect-scout1 | 96 | 58% | 20 | 49 | 15 |
| rate-b2 | 86 | 0% | 1 | 1 | 1 |
| scene-val | 32 | 100% | 1 | 2 | 2 |
| s004-scout3/4 | 各 ~200 | 62% | 各 14 | 各 ~29–30 | 各 5 |
| s004-qual2/3 | 230/256 | 39%/62% | 13/13 | 24/25 | 4/4 |
| s004-smoke | 181 | 10% | 13 | 23 | 4 |

推论（只作动机）：站位簇全盘 ~45–60（并箱后）；floor-eligible 侧
属性唯一单元 ~90–150；统计簇（族×对象）~30–45，其中 test 可分配
~8–12——**F4-test 与 F3-train 是最贴线的两项**（§5.2 at-risk
披露）。revision 0 的 600/150 在此单位下不可达，佐证其为帧级膨胀。

**口径注记（revision 2）**：(a) 表中「族」为并簇前复制族，是
atom 级 F4 的**上界**——若 §2.5 pHash 并簇合并（如 scout 与 qual
族），`(atom_id, 对象)` 计数将低于表值（AR2-1 统一后的口径）；
(b) 预估未建模 `TARGET_UNBOUNDED` 剔帧与 S6 审计降级，两者都只会
再降低计数。方向与 §5.2 at-risk 披露一致。

## COORD-010 disposition（2026-09-07）

Overall: `CLOSED_PARTIAL_DELIVERY_ENGINEERING_HANDOFF`。原 G0/D0 工作包以部分产物交付收束；Review 8 通过及第二代 S5 谱系核验保留，G0/D0 未完成，S6–S9 不再是此工作包待执行项。工具存续限制转工程继承清单，未消除历史欠项。
依据：`docs/authorizations.md` 当日 COORD-010「批准 §10 A+B+C 整体落地」条目，
规则批 `R2@batch1` 已通过；本节由接受角色执行 §7 状态迁移，不新增 D/C/R 轮或 BC。
本节是当前处置入口；上方设计决定、历史执行安排及复核轮次原样保留，不再构成继续执行指令。
工程继承唯一清单见 `docs/implementation-status.md`「COORD-010 — 工程继承清单」；
来源缺口唯一收口记录见 `docs/unity-test-log.md`「COORD-010 — DATA-002 来源缺口收口」。
原图、目录、划分与归档不改写；后续加工、模型推理或训练须独立工作项及授权。
