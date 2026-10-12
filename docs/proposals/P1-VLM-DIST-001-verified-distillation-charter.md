# P1-VLM-DIST-001 — 验证式蒸馏章程 v2：教师语言监督对极小 VLM 指称 grounding 的增量

Status: ACCEPTED_WITH_BINDING_CLARIFICATIONS
Author/role: 构思角色（ideation，Fable 池；本会话兼任进度监督视角）
Created: 2026-08-24
Last updated: 2026-08-25
Revision: 2（2026-08-25。回应 Acceptance round 2 `REVISION_REQUESTED`
§13 AR2-1…6；逐条回应见 §14。**round 2 是第二次 BC-C7-8 计数，
本稿是最后一次自行
修订**；round 3 若仍退修则交用户二选一。revision 1 = 回应 round 1
AR1-1…8，见 §12）
上位关系：继承 2026-08-06「VLM 是主菜」、2026-08-24 优先级重排与
**2026-08-25 用户核心主张授权**（`docs/authorizations.md` 当日首条）。
本章程请求接替 `P1-VLM-SCOPE-002`（暂停中）成为 VLM 线活跃提案，
处置请求见 §8。核心主张变更 → 须用户按 §9 逐字授权。

## 0′. 修订索引

### 修订索引（revision 2 = 最后一次自行修订：回应轮 2 AR2-1…6）

| # | revision 2 合同项 | 落点 | 实质变化 |
|---|---|---|---|
| R2C-1 | 语言→框 grounding 为主任务；**教师必要性是实验结论，不是前提**；唯一确认性主张 = verified teacher-language SFT 相对 matched template-SFT 的增量 | §1.2、§2.1、§3.3 | 四臂改为零样本 / **template-SFT** / raw-teacher-SFT / verified-teacher-SFT；删除一切「教师必要」「学生获得大模型能力」预设句式 |
| R2C-2 | C1 降为工程热身：无教师、不称蒸馏、不担主张、小额 compute/seed 上限、审计近重复矛盾标签与**坐标捷径** | §2.3 | C1 = 管线联调件；总上限与三项审计由 round 3 BC-DIST-4 收紧；标签非输入函数时只证明管线跑通 |
| R2C-3 | 两类教师严格分开；**评测教师非必需** | §2.4、§4 | 生成教师是主实验变量；评测教师仅作可选 G1/能力上界，信息条件不同，禁止混称同一「教师能力」 |
| R2C-4 | 程序唯一性可验 ≠ 自由文本与 `semantic_program` 同义 | §2.2、§3.3 | Tier-1 可逆 renderer；Tier-2 经独立验证模型 + 盲抽人工审计；round 3 BC-DIST-2 再冻结规范化程序等价 |
| R2C-5 | 报告问答不进首个确认性范围 | §1.2、§4 | 写死为范围外；防任务/输出/指标再膨胀 |
| R2C-6 | 101 车辆目录先过零 API 的 **G0**；未验证字段不得进入表达；不得为补数据改场景或启动 Play | §3.1、§4 | G0 逐字段验证；表达词表 = 已验证字段闭包；数据缺口 → 表达族出局，不补采 |

### 修订索引（revision 1，回应 Acceptance round 1，保留存档）

| # | AR 项 | 落点（rev 1 时） | 现状 |
|---|---|---|---|
| AR1-1 | 后训练有效 ≠ 教师迁移 | 四臂 estimand | **被 R2C-1 继承并修正**：机械标签臂改为模板语言臂，教师增量落在语言监督差上——修复了 rev 1 中 verified-KD ⊆ GT-SFT 的构造性塌缩 |
| AR1-2 | 主终点/统计/G1 纪律 | 冻结合同 | 继承（§5，指标换为 grounding 口径） |
| AR1-3 | 清单与切分 | lineage 清单/三互斥集 | 继承（§3.2，新增**表达来源不相交**约束） |
| AR1-4 | 输入不足以产生输出 | 输入 schema + 逐字段 verifier | C1 热身继承；主任务输出仅框，验证移至 §2.2 |
| AR1-5 | C2 可行性 | C1-only | **反转为 grounding 为主**，但前置 = R2C-6 的 G0 目录门，比 rev 1 更严 |
| AR1-6 | 过滤因果与覆盖 | 同母样本/全量 test 评估 | 继承（§3.3） |
| AR1-7 | 文献与资源 | 按原文口径 | 继承（§0.2/§0.3 增补） |
| AR1-8 | 授权门次序 | 先合同后授权 | 已闭合（§9；最终主张与明确排除由用户 2026-08-25 逐字授权） |

## 0. 依据

### 0.1 项目内动机（构思侧离线复算，未经复核，只作动机）

沿用 SCOPE-002 §0 的 O1–O9。主任务的系统位置：grounding 是改令与
交接锁定的原语（"跟那辆白色出租车" → 框 → 重锚定）；热身任务 C1 的
守护动机（O3/O4：tracker 黏看台、置信度反升）保留为工程叙事，不再
承担研究主张。数据底盘表述沿 revision 1 更正：24,152 jpg 为异质归档
总数、几何 779 项中 vehicle 101 个，可用性一律由 D0 清单与 G0 目录
门建立。

### 0.2 文献依据（沿 revision 1，按原文口径）

Distilling Step-by-Step（2305.02301）｜Capacity-Gap 复检
（2604.08880，摘要口径 often degrades → 门 G2）｜To CoT or not
（2409.12183）｜STaR（2203.14465）/ RFT（2308.01825）｜VPD
（2312.03052）。

### 0.3 教师为什么可能有增量（2026-08-25 检索；九情景对照）

对「小模型训练为何需要教师端」的检索归纳为九类情景（教师当标注器／
示范开放生成／**符号真值→语言监督转换**／多样性扩增／推理过程监督／
暗知识软标签／质量偏好反馈／数据定制／生成-验证不对称）。在真值
完备的本仿真中，「标注器」与「软标签」类**不成立**（rev 1 的 C1 主张
正是死在这里）；存活的情景集中在语言侧。**关键先例 = LLaVA
（2304.08485）**：其教师为纯文本 GPT-4，全程不看图，只读 COCO 已有
真值（caption + 框）生成 158K 条语言监督——教师的角色是**把符号真值
翻译成有多样性的语言监督**。本章程的生成教师与之同构（读目录 +
几何真值，不读像素）。**先例的边界（AR2-6）**：LLaVA 只支撑
「text-only 教师可由符号视觉资产合成语言监督」，**不曾机械验证其
自由文本，也不证明本仓库已具备等价的语义字段**（后者归 G0 判定）。
教师是否真带来增量，是本实验要回答的问题，不是引用先例即可预设的
结论（R2C-1）。

## 1. 目标与研究主张

### 1.1 首要目标（用户 2026-08-24 逐字）

一次完整、诚实、可复现的后训练项目经验；全离线、零 Play、零 Unity
改动。

### 1.2 研究问题与主张（R2C-1；用户 2026-08-25 核心授权）

> **正式研究问题**：经验证的大模型语言监督，是否能在独立语言测试集
> 上，使 ≤3B VLM 的 referring-expression grounding 显著优于同数据
> 量、同预算的程序化模板 SFT？
>
> **T-G1（唯一确认性主张）**：verified teacher-language SFT 相对
> matched template-SFT 的主指标增量 ≥ δ（δ 由 D2 提案采集前冻结）。
> **教师是否必要由此判定**：只有教师臂稳定胜过模板臂，才支持「教师
> 语言监督有增量」；反之如实报告「模板监督足矣」——预注册负结果，
> 同样可发。
>
> **可选次级主张（仅在启用评测教师时）**：学生对评测教师的追平率。
> 评测教师必须**在同一冻结确认性 grounding test 上作答**（图像+指称→
> 框，与学生同卷同规则）——不得因它生成过语言就当能力上界；只作
> 上界参照，不进确认性主张，不表述为「学生获得大模型视觉能力」。
>
> **门 G2 沿用**：任何训练臂须优于同学生零样本，否则计负。

**范围外（写死）**：报告问答（R2C-5）、C1 之外的任何主张、接力采集、
场景改动、任何 Unity/Play、Jetson 实机（M7 归用户显式启动）。

## 2. 任务定义

### 2.1 主任务 G：域内指称 grounding

```
输入 = { 整帧图像, expression（指称表达文本） }
输出 = { box: 归一化 top-left xywh，裁剪到 [0,1]（沿项目框协议） }
真值 = 目标物体的投影框（semantic_program 在 eligible catalog 上唯一
       执行 → 物体 → 八角点投影 → 视口裁剪；投影合同沿 rev 1 §2.2）
逐样本判定 = IoU(输出框, 真值框) ≥ 0.5 → 1，否则 0；无效输出 = 0
```

### 2.2 semantic_program 与两级语言（R2C-4）

每条表达先有机器可执行的语义程序，再有文字：

```
semantic_program = 属性谓词（class/color/…，只取 G0 已验证字段）
                 + 可选空间关系（左/右/前/后/近邻/路口侧，只取 G0
                   已验证的几何关系）
唯一性机械验证 = 程序在该帧可见 catalog 上执行结果恰为一个物体
```

- **Tier-1 受限语言（确认性骨架）**：由**可逆 renderer** 从程序生成
  文字，parse(render(p)) ≡ p 机械可证；模板臂的训练语言与部分测试
  分层来自此级。
- **Tier-2 教师自由语言（只入训练）**：先由真值目录选定 target 与
  程序，生成教师读符号记录后输出 **`{expression, semantic_program}`
   对**。三层验证逐项区分（AR2-4）：
  ① **机械保证**——教师提交的 program 在当帧**完整 eligible
  catalog** 上执行必须恰好唯一选中该 target，target 框只来自冻结
  投影合同（不来自教师）；② **模型判断**——独立验证模型（与生成
  教师不同型号）把 expression 解析回 program，与 ① 执行结果一致；
  ③ **人工抽查**——盲抽审计（样本量与误差率上限预注册，误差率如实
  报告）。生成教师自评不算任何一层；任一层不过 → 整条弃用并按原因
  计数。
- **确认性测试集的表达来源**：与两个训练生成器**不相交**（第三来源
  生成 + 盲抽人工审计合格，或人工撰写），按 Tier-1 风格 / 自然风格
  分层报告；主指标算在全集，分层数字必须同表呈现。

### 2.3 C1 指称核验 = 工程热身（R2C-2）

无教师；不称蒸馏；不承担论文主张；上限 ≤ 2 配置 × 1 seed，整个热身
累计 ≤ 5 GPU·h；审计前置——近重复矛盾标签率、template/current-crop
矛盾率、**coordinates-only shortcut 基线**（只喂坐标不喂图的对照，
逼近主模型则判捷径）。**若标签不能由输入唯一决定，C1 只能称
「外观一致性热身」，最多证明训练评测管线跑通**。产物：跑通的数据/
训练/评测管线，供主任务复用。

### 2.4 两类教师（R2C-3，信息条件不同，禁止混称）

| 角色 | 输入 | 地位 | 消耗 |
|---|---|---|---|
| **生成教师** | 符号记录（程序/目录/几何），**不读像素** | **主实验变量**：Tier-2 语言监督的来源 | 纯文本调用，量 ≈ 训练母样本数 |
| **评测教师** | 图像 + 指称 | **可选**：仅当报告次级追平率/G1 上界时启用；不在 T-G1 因果链上 | 视像调用，仅评测集规模 |

## 3. 数据章程

### 3.1 G0 目录门（R2C-6，零 API，先于一切）

- **磁盘已有 vs 待建立（AR2-3 逐字段）**：已有 = 资产名、canonical
  name、统一 `ground-obstacle` classification、world AABB。仍缺 =
  自然语言类别映射、已验证颜色（`color01` 等是资产代号不是颜色）、
  实例朝向/动态状态、道路与地标关系图、逐帧可见/遮挡、投影有效性、
  co-visible 候选集、关系唯一性。后者全部由 G0 建立或宣告缺失。
- 对 101 个 `vehicle` 实例建立**逐字段验证状态表**（类别映射 + 抽查、
  颜色像素/材质统计 + 抽查、动态状态与 relocation 标记、道路关系
  几何）。
- **表达词表 = 已验证字段的闭包**：颜色未验证 → 不得生成「白色」；
  **动态关系（如「跟在…后面」）在逐帧动态状态建立之前一律禁止**，
  静态空间关系（左/右/近邻/路口侧）以位置几何验证后方可用。
- **预注册下限与具名终态**：G0 按独立 lineage/对象/视角报告 eligible
  数、co-visible 候选数、可唯一执行的属性/关系数与有效独立样本数；
  任一低于预注册下限 → 本章程以
  `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA` 收束。
- **数据缺口的唯一处置 = 该表达族出局或具名收束**；不得为补数据修改
  场景、加车、移动车辆或启动 Play。
- G0 零 API、零 Play；产物为 create-once 目录工件（哈希冻结）。

### 3.2 清单与切分（沿 revision 1，全部继承）

lineage 清单、切分原子 = 谱系组、近重复哈希约束、三互斥集
（train/dev ∣ untouched confirmatory test ∣ D3 演示 holdout）在任何
教师调用前冻结；**新增**：测试表达与训练生成器不相交（§2.2）；
臂 A 48 s 事件维持已知 challenge set（只与 C1 热身叙事相关）。
样本量一律 planning estimate。

### 3.3 四臂训练监督（R2C-1；同帧-目标-框母集、同样本量、同预算、同 seed 集）

| 臂 | 训练语言来源 | 说明 |
|---|---|---|
| 零样本 | 无训练 | G2 基线 |
| **template-SFT** | Tier-1 可逆 renderer（纯程序化） | **对照臂：教师增量的分母** |
| raw-teacher-SFT | 生成教师 Tier-2 原样（未过验证层） | 隔离验证层贡献 |
| verified-teacher-SFT | 生成教师 Tier-2 经 §2.2 独立验证层 | **主张臂** |

- 四臂共用同一 (帧, 物体, 真值框) 母集；每对配一条对应来源的表达，
  样本数逐臂相等；raw/verified 用同一批教师调用。
- 全臂表现与验证层贡献都在**完整确认性 test**（未按任何教师正确性
  条件化）上评估；弃用样本按原因留档。

## 4. 批次、任务量与停点

| 批次 | 内容 | 量估计（planning） | 消耗 | 停点 |
|---|---|---|---|---|
| **G0 + D0** | G0 目录门 → lineage 清单 → 三互斥集冻结 → 投影/唯一性/可逆 renderer/独立验证层合同 | 1–1.5 周；人工抽查：目录 ~100 项 + 标签 ~400 条 + 表达同义性盲抽 ~200 条 | 零 Play、零 API、零 GPU | 强制（新工具 + 数据正确性独立复核） |
| **C1 热身** | 管线联调 + 三项审计（近重复矛盾、template/current-crop 矛盾、coordinates-only shortcut） | ≤2 配置 × 1 seed，累计 ≤5 GPU·h | GPU（须另行逐字授权） | 不承担主张，不是 G0/D0 通过条件 |
| **D1** | 差距与可行性：学生池零样本 grounding 同卷（G1 门）；生成教师小规模试产（程序→语言合格率）；（可选）评测教师上界 | 生成教师试产 ~200–500 次纯文本调用；评测教师如启用 ~1–2k 视像调用 | API（届时逐字授权） | 门 G1 |
| **D2** | 四臂 × 2–3 seed ≈ 8–12 runs（每 run 1–6 GPU·h）+ 生成教师全量产语言（≈ 母样本数的纯文本调用）+ 独立验证层全量执行 | **15–80 GPU·h**；生成教师 5k–15k 次纯文本 + 验证模型同量级 | GPU + API（届时逐字授权） | 门 G2 + T-G1 判定 |
| **D3** | 描述性系统演示（学生作改令/ACQUIRE 原语在演示 holdout 回放）+ 按关系型/难度/表达风格分解的边界报告 | 数天 | 零 Play | 强制（主张产出） |

报告问答不进任何批次（R2C-5）。每批独立提案、接受裁定、独立复核；
预算逐批逐字授权，本章程零预批。

## 5. 可证伪的验收条件

1. **G0 门**：目录逐字段验证状态表 create-once；抽查错误率 ≤ 预注册
   上限；未验证字段的表达族生成器机械封禁。
2. **G1（差距门）**：dev 上学生零样本主指标高于预注册上限（域已
   饱和）→ 按冻结阶梯升级关系复杂度；阶梯用尽 → 诚实收束。
3. **主指标（唯一）**：确认性 test 上 `Success@IoU≥0.5`（逐样本
   0/1 合同见 §2.1；无效输出计 0）；次级：mean IoU、invalid-output
   rate、ambiguity-reject rate、按表达风格/关系型/距离档分层、验证层
   retention 与误差率。**统计单位 = lineage/对象簇**，5 Hz 近重复帧
   不作独立样本。**选择纪律**：学生池 D1 前具名；模型/配置/阶梯只在
   dev 选；test 一次性判定。
4. **T-G1 判定**：verified-teacher-SFT − template-SFT 的同 seed 配对
   差（bootstrap 95% CI，seed 数 D2 提案冻结）≥ δ；raw 臂单列。
   δ 不得由本批数据反推。
5. **G2**：任何训练臂不优于同学生零样本 → 该臂计负。
6. **表达验证层**：独立验证模型与生成教师不同型号且版本锁定；盲抽
   人工审计误差率如实报告并 ≤ 预注册上限，超限 → Tier-2 全量重审或
   弃用（如实入档）。
7. **C1 热身**：只验管线（数据可复现、训练收敛、评测一致）；三项
   审计结果入档；不产生任何研究结论。
8. **全程**：模型/prompt/版本冻结哈希；API/GPU 逐批记账；
   `UNITY_NA` 逐批经独立复核附议。

## 6. 基线与消融

四臂（§3.3）为主结构；oracle = 真值框上界；（可选）评测教师上界。
消融：验证层开/关（raw vs verified）、数据量阶梯、表达风格分层、
（可选）学生规模。全部在 dev 分析，确认性结论只引 test 一次性数字。

## 7. 资源与风险

| 项 | 说明 |
|---|---|
| GPU | 15–80 GPU·h（四臂 × seed；C1 热身 ≤5 GPU·h 上限另计）；云单卡 24–48 GB；数额 D2 逐字授权 |
| API | 生成教师纯文本 5k–15k 次（便宜一个量级）+ 独立验证模型同量级 + 评测教师可选 1–2k 视像；数额 D1/D2 逐字授权 |
| 教师增量为零 | 预注册负结果：「程序化模板监督足矣」，如实可发 |
| Tier-2 同义性误差 | 独立验证层 + 盲抽审计 + 误差率上限；超限弃用 |
| 学生零样本已饱和 | G1 阶梯（关系复杂度）；饱和则诚实收束 |
| 目录字段验证不足 | 表达族出局，不补采（R2C-6） |
| 教师/验证模型版本漂移 | 版本锁定 + 冻结 prompt + 测前重跑 |

## 8. 与既有工作项的关系（沿 revision 1，处置归接受角色 + 用户）

`P1-VLM-SCOPE-002` 维持 `PAUSED_BY_USER_REDIRECTION`，资产继承为
记录（如实带状态）；`P1-VLM-SCOPE-001` / `P1-VLM-CAL-001` BC-C7-8
终态归用户；M3′/M1/`P1-EVAL-001`/v0.3.17/`PROJECT_BRIEF.md` 原状
不动，技术 revision 通过前不提请任何基线改写。

## 9. 需要用户决定

1. **最终主张文本**：§1.2 的正式研究问题与 T-G1 已由用户
   2026-08-25 逐字授权；授权只覆盖接受裁定与正式设计同步。
2. 是否启用**评测教师**（次级追平率与 G1 上界；不影响 T-G1 因果
   链）：建议 D1 时按预算决定。
3. D1/D2 的教师与验证模型选型及数额：到各批次逐字授权。
4. 学生候选池是否限定「量化后体积适配 8GB」档（建议：是，仅资格
   条件）。

## 10. 本稿边界

不修改任何代码、配置、设计基线、verdict；不执行任何实验；零 Play、
零 ID、零 API、零 GPU；G0/D0–D3 各自另行提案与复核；§0 数字未经
复核不进证据链；样本量均为 planning estimates。

## 11. Acceptance review decision

### Acceptance round 1 — 2026-08-24

Decision: **REVISION_REQUESTED**

Rationale:

首要方向值得保留：把目标收拢为一次完整的极小 VLM 后训练项目，优先做
可机械裁判的 C1，结构化短输出而非自由长 CoT，并强制比较学生自己的
pre-distillation baseline，均比前一条接力章程更贴近用户当前优先级。
文献原文也支持三点：rationale 可作训练时辅助目标；CoT 在非数学/符号
任务上的收益有限；蒸馏后必须与学生蒸馏前能力比较，不能只报教师追平率。

但 revision 0 尚不能把结果归因为「获得了大模型能力」。C1 的最终标签
完全由 IoU/仿真真值生成，正文还明写零教师也能完成 SFT；若只比较零样本、
教师和训练后学生，任何增益都可能只是机器标签监督微调，而不是教师知识
迁移。当前消融也没有同数据、同训练预算的无教师 SFT 对照。其次，§0.1
把异质归档中的 24,152 张 jpg 直接写成均配套相机位姿/真值，并把 779 个
场景物体 AABB 写成可给「全部车辆」打框，均未被磁盘事实支持：jpg 总数
确为 24,152，但包含 protocol-invalid、void hold、scouting、preview/overlay
和重复归档；场景几何文件的 779 项是全部障碍物，分组为 318 nature、290
prop、101 vehicle、70 building。可用图像、逐帧相机信息、目标真值与车辆
语义元数据的 join 覆盖率尚未建立。最后，主指标、确认性切分与 G1 自适应
加难的裁决合同均未冻结；同一批归档既供训练又供 D3 十-run 回插，会让
已知臂 A 失效事件泄漏进模型/阈值选择。

Required revisions for revision 1:

1. **AR1-1 — 拆开「后训练有效」与「教师能力迁移」两个 estimand。**
   T-D1 至少分成：(a) 学生经机器真值 SFT 相对自身 zero-shot 的增益；
   (b) verified teacher distillation 相对**同学生、同机器标签、同样本、
   同训练预算**的无教师 SFT 的增量。每个进入确认性比较的学生至少同卷
   报 `zero-shot`、`GT-SFT/no-teacher`、`raw-teacher KD`、`verified-teacher
   KD`；rationale 如保留，在同一设计上作正交消融。教师输出若未成为学生
   的训练监督，不得称为蒸馏。预注册两个不同负结果：学生后训练无增益，
   以及后训练有增益但教师增量为零；后者只能支持「机器标签 SFT」，不能
   支持 T-D1 的大模型能力迁移。教师自身还须过绝对性能下限，避免用一个
   弱教师的百分比制造“追平”。
2. **AR1-2 — 冻结唯一主终点、统计合同和 G1 的选择纪律。** C1 必须给出
   三分类混淆矩阵的逐样本定义、`UNCERTAIN` 的计分与 risk/coverage（或
   等价 abstention）合同、唯一主指标、绝对门、教师追平率公式、学生增量
   公式、seed 聚合、置信区间和多学生/多配置裁决顺序；不得在 test 上选
   “最好学生/最好配置”。T-D2 必须冻结事件零点、检出、时延、误报分母、
   多 run 聚合及三条系统基线的可比口径。G1 的难度阶梯、每级数据 manifest
   和停止规则须在教师调用前冻结，只能用 calibration/dev 选级；最终主张
   在一次 untouched confirmatory test 上判定。若 C2 保留，另给 grounding
   主指标、无效输出和裁决顺序，不与 C1 自由择优。
3. **AR1-3 — 先建立可用数据清单与不可逆切分，再谈样本量。** D0 的第一
   产物须是 create-once inventory：每张图像的路径与内容哈希、采集谱系、
   scenario/config/scene 标识、valid/void/diagnostic 用途、frame metadata/
   camera pose/truth join 状态、允许或排除原因、所有 crop/改写的 source-frame
   lineage。切分原子至少覆盖采集谱系、scenario/arm、目标与干扰体外观及
   近重复内容哈希，不能只按 `run_id`；同一底层采集的正式归档、hold、
   exchange 副本不得跨 split。必须在任何 D0 数据生成、D1 调用或模型选择
   前划出：(a) D1/D2 untouched confirmatory test；(b) 与之不重叠的 D3
   系统回放 holdout。任何 test 图像及其裁剪、教师回答、rationale 或改写
   均不得进入训练。臂 A 的 48 s 事件因已经据此选题，只能标为预先已知的
   challenge set/描述性回放，不能冒充新条件确认集。3–6 万/1–3 万继续只作
   planning estimate，D0 inventory 完成前不得写成可用样本事实。
4. **AR1-4 — 让 C1 的输入确实足以产生每个输出字段。** 冻结推理时实际
   可用的输入 schema；任何 truth/evaluator 字段不得进入学生输入。若输入
   只有 resize 后 crop，正文必须删除无法由该输入判定的 `on_road` 与
   `size_plausible`，或明确加入在线可得的全帧/框坐标/图像尺寸/上下文并在
   所有比较臂一致提供。为 `color_match`、`class_match`、`on_road`、
   `size_plausible` **每一项**给出机械标签与 verifier；当前 §3.3 漏了
   `class_match`。同时冻结遮挡/不可见与 IoU 中间带如何生成
   `UNCERTAIN`、模板 crop 的时点与可见性、目标描述的词表/来源，防止描述
   或 evidence 字段把答案直接泄漏给模型。
5. **AR1-5 — 重写 C2 的标签可行性合同，或把 C2 移出第一章程。** 779
   不能再称为车辆数；先从 101 个 `vehicle` 组实例建立可审计的 eligible
   catalog，逐项给出身份、类别/颜色元数据来源、动态目标/已移动实例的
   排除或更新规则。投影必须定义八角点、相机内外参版本、近裁面/相机后方、
   视口裁剪、完全不可见、遮挡、旋转模型的 world-AABB 过包围与无效样本
   处置，并以人工抽查量和误差门验证。若现有工件不能可靠建立这些字段，
   revision 1 应把首批范围锁为 C1-only，C2 另立提案；不得以“视进度加入”
   让确认性范围在结果出现后漂移。
6. **AR1-6 — 修正验证式过滤的因果与覆盖口径。** verifier 必须覆盖全部
   输出字段；raw/verified 两臂使用同一冻结母样本与教师调用，过滤失败样本
   永久留作诊断，报告逐原因 retention。过滤贡献在**完整、未按教师正确性
   条件化的 test population**上评估，不能只在 teacher-pass 子集上报；
   同时报教师在完整 test 上的绝对表现。`aux_rationale` 与 C2 改写只能来自
   train split，不能把 test truth 经教师通道带回训练。
7. **AR1-7 — 校正文献定位和资源/部署表述。** arXiv 2604.08880 的摘要是
   “often degrades”，不是已证明“多数配置”；arXiv 2505.16322 是
   AdaSTaR 的自适应采样工作，不足以单独支撑当前 RFT 机制概括，改引原始
   STaR/RFT 或准确收窄表述。补入直接近邻 Visual Program Distillation
   （arXiv 2312.03052：候选程序执行后验证再蒸馏进 VLM），并说明本项目的
   区别是仿真监控域、字段级机械 verifier 与极小学生。D0–D3 仍须各自提案；
   D1/D2 预算、模型下载、API/GPU 均在对应提案逐字授权，不能由本章程预批。
   “≤3B/量化体积可进 8GB”只能是候选资格，不能提前成为 Orin 可运行或时延
   主张；任何 `UNITY_NA` 仍须独立复核文件附议，不能写成预期即成立。
8. **AR1-8 — 把换轨和旧项处置留在正确授权门。** Revision 1 先完成上述
   技术合同，再给用户一个精确、可逐字授权的最终主张文本，并把 C1-only
   与 C1+C2 的首批范围列成互斥选项。`P1-VLM-SCOPE-002` 保持当前
   `PAUSED_BY_USER_REDIRECTION`；关闭为 superseded、对其资产的继承边界，
   以及 `P1-VLM-SCOPE-001` / `P1-VLM-CAL-001` 的 BC-C7-8 终态均不得由本
   提案自动生效。教师/API、GPU 与具体模型池到 D1/D2 再问，不在章程接受
   轮预取。用户本轮所说“整个项目的目的有修改”确认要按新目的审查，
   但没有给出 T-D1/T-D2 的精确最终文本；在技术 revision 通过前不修改
   v0.3.17、`PROJECT_BRIEF.md`、任何 milestone 或 legacy gate。

Disposition:

- 这是本提案第一次正式 `REVISION_REQUESTED`。交构思角色起草 revision 1；
  本轮没有 binding implementation clarifications，也不建立实现交接。
- 本轮不接受 §8 的关闭/继承请求，不裁定 §9 第 3–6 项，不授权 D0–D3、
  实现、训练、模型下载、API/GPU、Edit Mode/Play、ID/配额或硬件资源。
- 设计基线仍为 `docs/phase1-single-drone-design.md` v0.3.17；
  `PROJECT_BRIEF.md`、M1/M3′/M7 与全部 legacy gate 原状不动。

Accepted design-document changes: **NONE**（提案尚未接受）。

## 12. Acceptance round 1（AR1-1…8）逐条回应（revision 1，2026-08-24）

1. **AR1-1**：接受——这是 estimand 级缺陷：标签来自机械真值时，
   增益可能只是机器标签 SFT，与教师无关。→ §1.2 拆 T-D1a/T-D1b；
   §3.3 四臂同母样本同预算；两种负结果与教师资格门预注册；
   「教师输出未入训练监督不得称蒸馏」逐字采纳。
2. **AR1-2**：接受。→ §5.3 唯一主指标（三分类 macro-F1）+ 逐样本
   合同 + 选择纪律（dev 选、test 一次判）；§5.5 T-D2 事件零点/时延/
   误报分母/聚合写死；G1 阶梯 manifest 教师调用前冻结（§5.1）。
3. **AR1-3**：接受，且承认 §0.1 原表述夸大（24,152 为异质总数；
   779 为全部障碍物、vehicle 仅 101）。→ §3.2 清单先行、lineage
   切分、三互斥集先划、48 s 事件降为 challenge set；样本量全部
   改标 planning estimate。
4. **AR1-4**：接受。→ §2.1 冻结含全帧缩略图 + 框坐标的输入 schema
   （各臂一致），四字段各配 verifier（补 `class_match`），
   `UNCERTAIN`/模板时点/词表冻结与防泄漏条款；字段不可判则整体
   移出并入档。
5. **AR1-5**：接受。→ 首批锁 C1-only；C2 移出（§2.2 前置合同 +
   另立提案）；§9 互斥选项交用户。
6. **AR1-6**：接受。→ §3.3：verifier 全字段覆盖、raw/verified 同母
   样本同教师调用、逐原因 retention、完整 test population 评估、
   败样本留档、增广仅 train。
7. **AR1-7**：接受。→ §0.2 按原文口径改写 2604.08880 与 STaR/RFT
   引用、补 VPD 近邻与区分；§7/§4 预算逐批、8GB 仅资格、
   `UNITY_NA` 逐批附议。
8. **AR1-8**：接受。→ §9 重排为「先技术合同、后授权」：给出最终
   主张逐字文本草案与互斥范围选项；SCOPE-002 维持暂停；本章程零
   预批。

## 13. Acceptance review decision — round 2

### Acceptance round 2 — 2026-08-25

Decision: **REVISION_REQUESTED**

Rationale:

Revision 1 对 AR1-1…8 的字面回应完整：四臂 estimand、lineage 清单、
一次性 confirmatory test、C1 字段 verifier、C2 移出、完整 test
population、文献校正与逐批资源门都应保留。但构思角色在交付后自行
推出两条更根本的失败，接受侧复核后同意其阻断性。

第一，当前 hard-JSON 合同中，GT-SFT 已拥有每个输出字段的完整机械
标签；verified-KD 只保留与这些标签逐字段相同的教师答案，因而教师
没有新增监督信息，至多改变样本选择。子集可能因课程/正则效应偶然优于
全集，所以 `T-D1b ≤ 0` 不是数学定理；但任何差值都缺少「教师能力
迁移」的可识别机制。第二，现有 C1 的目标身份并非总是可由单帧可观测
输入唯一确定；全帧与框坐标可能引入位置捷径，却不能区分视觉等价的
同款实例。现有 T-D2 又针对道路先验在已知 arm-A challenge set 上已经
近乎完美分离的失效，独立 holdout 还可能没有可计分的身份切换事件；
继续完整四臂 + 系统回放会把两条主张都押在事前可预见的弱/负结果上。

补充文献核验支持**换到符号真值→语言监督**的方向，但不支持直接接受
当前映射。LLaVA 的 data-generation teacher 确为 language-only GPT-4：
它不看图，而读 captions 与 object boxes 的符号表示，生成 58K
conversation、23K detailed-description、77K complex-reasoning 样本。
这证明大教师可以把既有视觉符号资产改写为多样语言监督；它没有证明
这些自由文本被机械验证，也没有证明本仓库已经具备等价的 COCO 语义。
磁盘上的 101 个 `vehicle` 条目只有名称、canonical name、统一
`ground-obstacle` classification 与 world AABB；`color01` 等是资产
代号，不是已验证自然语言颜色，且文件没有朝向、速度、道路/路口关系、
逐帧遮挡或唯一指称字段。因此「跟在公交后面的白车」目前仍是拟议数据，
不是可生成事实。VPD 的候选程序执行验证是更接近的先例，但自然语言与
结构化程序语义一致性仍不能由“框投影正确”自动证明。

Required revisions for revision 2（本提案最后一次自行修订）:

1. **AR2-1 — 采用 C′ 的主张分层，删去已失去识别性的头号主张。**
   C1 降为**无教师 GT-SFT 工程热身**，只证明 inventory→LoRA→评测→
   复现管线可运行；不得称蒸馏、不得支撑「获得大模型能力」，并在批次
   提案设小额 compute/seed 上限。T-D2 降为描述性系统回放，不设为
   confirmatory 主张。正式主张改为：纯文本生成教师把 train-only 的
   符号场景记录转成经验证的域内指称语言，是否令 ≤3B 学生在
   language→box grounding 上产生超出同预算程序化模板 SFT 的增量。
   「报告问答」不进首个确认性范围；若保留，只列 exploratory 或另立项。
2. **AR2-2 — 冻结两个教师角色和可归因四臂。** 生成教师不读像素，
   只读 train split 的冻结符号记录，产 language supervision；评测教师
   读图，只在另行授权的 G1 上与学生同卷测差距，二者不得混称。主实验
   至少包含 `zero-shot`、`template/programmatic SFT`（无教师）、
   `raw teacher-language SFT`、`verified teacher-language SFT`；四臂匹配
   source image、target identity、样本数、训练预算与 seed。学生统一输入
   `image + referring expression`，输出规范化 box；目标框来自真值投影，
   不来自生成教师。若仍主张「获得大模型 grounding 能力」，评测教师必须
   在同一冻结 grounding test 上作答，不能只因它生成过语言就当能力上界。
3. **AR2-3 — 把“101 个车辆目录”降为 D0 待证前提。** Revision 2 须
   逐字段列出磁盘已有与仍缺：资产名/AABB 已有；自然语言类别映射、真实
   颜色映射、实例朝向/动态状态、道路与地标图、逐帧可见/遮挡、投影有效性、
   co-visible 候选集和关系唯一性仍待建立。D0 增设零 API 的 G0：按独立
   lineage/对象/视角报告 eligible 数、同时可见候选数、可唯一执行的属性/
   空间关系数与有效独立样本数；未过预注册下限则以
   `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA` 收束，不得就地加入新车、改场景或
   Play。`following` 等动态关系在没有逐帧动态状态前禁止生成。
4. **AR2-4 — 给“验证式语言生成”一个真实而非循环的 verifier。** 先由
   真值目录选择 target，再让教师输出 `{expression, semantic_program}`；
   program 在当帧**完整 eligible catalog**上执行，必须恰好唯一选中该
   target，target box 再由冻结投影合同给出。只核对教师自己的 box、或让
   同一教师自评，均不得称机械验证。自由文本与 program 是否同义不是框
   检查能证明的事实：须冻结受限语言/可逆 renderer，或加入独立验证者 +
   盲抽人审并报告误差；正文逐项区分机械保证、模型判断和人工抽查。
5. **AR2-5 — 重新冻结确认集与指标，防止教师文风泄漏。** Train/dev/test
   除 source lineage/对象外，还须按表达模板/生成来源隔离；confirmatory
   test 使用人写或独立来源表达，不得由训练生成教师同分布回填。grounding
   唯一主指标建议 `Success@IoU≥0.5`，另报 mean IoU、invalid-output rate、
   ambiguity-reject rate 与按关系类型分解；统计单位按 lineage/对象簇，
   不把 5 Hz 近重复帧当独立样本。C1 热身另做近重复矛盾标签率、
   template/current-crop 矛盾率和 coordinates-only shortcut baseline；若
   标签不是输入函数，只能称外观一致性热身。
6. **AR2-6 — 精确限定先例、授权和范围。** LLaVA 只支撑“text-only
   teacher 由 captions/boxes 合成视觉指令数据”，不得写成它机械验证了
   开放指称或直接证明本地数据充足；survey taxonomy 只作背景，不替代
   原始方法证据。相似车并行/超车、新车辆、场景字节或新 Play 都是另行
   范围扩大，未获授权；D0/D1/D2、模型下载、API/GPU 仍逐批授权。
   Revision 2 起草前由用户逐字选择 C′ 并确认精确主张；未经授权不得用
   本轮技术认可改写 v0.3.17 或 `PROJECT_BRIEF.md`。

Disposition:

- 这是本提案第二次正式 `REVISION_REQUESTED`。Revision 2 是 BC-C7-8
  下最后一次自行修订；若 Acceptance round 3 仍不能接受，本角色不得
  发第三次退修，必须交用户二选一：接受当前范围并逐项列缺口，或关闭为
  负结果记录。
- 技术上同意以 **C′** 作为 revision 2 的唯一推荐方向，但这不是用户的
  核心主张授权，也不是 `ACCEPTED`。用户授权前由 User 持有交接，不让
  构思角色自行把补充材料写成正式主张。
- 本轮不接受任何实现、D0–D3、训练、模型下载、API/GPU、Edit Mode/Play、
  ID/配额、场景/车辆改动或旧 work item 处置；v0.3.17、
  `PROJECT_BRIEF.md` 与全部 legacy gate 原状不动。

Accepted design-document changes: **NONE**（提案仍未接受）。


## 14. Acceptance round 2（AR2-1…6）逐条回应（revision 2）

构思角色把轮 2 的六组要求整理为 R2C-1…6；其中核心主张、C1 定位与
报告问答边界后来由用户在 2026-08-25 逐字授权，其余验证/G0 条款是
接受轮要求的技术约束，不伪称用户原话。映射为 AR2-1↔R2C-1/2/5、
AR2-2↔R2C-1/3、AR2-3↔R2C-6、AR2-4↔R2C-4、AR2-5↔R2C-2/4、
AR2-6↔R2C-6 与授权边界：

1. **R2C-1 主任务与主张**：研究问题按最终用户授权写入 §1.2；「教师必要性
   是实验结论」全文贯彻——四臂的对照臂改为 matched template-SFT，
   这同时修复了 revision 1 的构造性塌缩（机械标签完备时
   verified-KD ⊆ GT-SFT，教师增量被锁死为 ≤0）。
2. **R2C-2 C1 热身**：五条件写死（§2.3），含坐标捷径与近重复矛盾
   标签等三项审计；「最多证明管线跑通」入档。
3. **R2C-3 教师拆分**：生成教师 = 主实验变量（纯文本读符号）；评测
   教师 = 可选、仅上界/次级，不在 T-G1 因果链（§2.4）；两者信息
   条件不同、禁止混称。
4. **R2C-4 验证层补齐**：采纳**双层**——Tier-1 受限语言 + 可逆
   renderer 作确认性骨架（机械可逆）；Tier-2 自由语言只入训练，须
   独立验证模型（非生成教师）text→program 一致 + 盲抽人工审计并
   报告误差率；自评不算（§2.2）。
5. **R2C-5**：报告问答写死为首个确认性范围外（§1.2/§4）。
6. **R2C-6**：G0 零 API 目录门先行；表达词表 = 已验证字段闭包；缺口 =
   表达族出局，不改场景、不启动 Play（§3.1）。

补充逐项（轮 2 独有细目的落点）：评测教师须在同一冻结 test 上作答
（§1.2）；磁盘已有/仍缺字段清单与 `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA`
终态（§3.1）；教师输出 `{expression, semantic_program}` 对与三层验证
的机械/模型/人工区分（§2.2）；`Success@IoU≥0.5` 命名、ambiguity-
reject、lineage/对象簇统计单位（§5.3）；C1 的 coordinates-only
shortcut 基线与「外观一致性热身」命名（§2.3）；动态关系禁令与 LLaVA
先例边界（§3.1/§0.3）。**本稿是 BC-C7-8 下最后一次自行修订**；
round 3 若仍退修，交用户二选一。

## 15. Acceptance review decision — round 3

### Acceptance round 3 — 2026-08-25

Decision: **ACCEPTED_WITH_BINDING_CLARIFICATIONS**

Rationale:

Revision 2 已消除前两轮的两个结构性失败。确认性 estimand 不再把教师
与完备机械标签作无信息差比较，而是把教师限定为训练语言来源，并以同一
学生、同帧-目标-框母集、同数据量与同训练预算的程序模板 SFT 为主对照；
教师是否必要只由该增量实验判定。C1 已降为无教师、无论文主张的封顶
热身；生成教师与可选评测教师的信息条件分开；自由语言的程序唯一性、
模型判断和人工审计不再混称机械保证；G0 先验证本地目录，缺字段时缩词表
或以具名负终态收束。AR2-1…6 因而在章程层闭合。

授权链也已纠正：构思侧先前把接受角色的六点审查意见误记为用户原话，
该账本条目现已明确作废。用户随后在本接受会话逐字授权 language→box
grounding、唯一确认性主张、教师非预设必要、C1/报告问答边界，并把权限
限定为本轮裁定和正式设计同步；这份真实原话是本轮唯一核心授权依据。

Binding clarifications（后续批次必须按字面执行）：

1. **BC-DIST-1 — 主对照的样本配平与 raw 臂地位。** D2 冻结的每个
   train target 必须给 template-SFT 与 verified-teacher-SFT 各恰好一条
   表达；帧、target identity、真值框、样本数、训练 step/token budget、
   seed 集全部相同。教师候选每 target 的最大尝试数 `K` 在任何全量生成
   前冻结；`K` 次内无合格表达的 target 必须从两个主臂对称排除并报告
   覆盖率。raw 臂只作验证层诊断：对同一冻结候选池采用预先规定的候选
   选择规则，不得以不等样本量、不同 target 构成或额外训练预算支撑
   T-G1。T-G1 只由 verified 对 template 判定。
2. **BC-DIST-2 — 语言验证必须比较规范化程序语义。** 独立验证模型把
   expression 解析为冻结 ontology 下的规范化 AST；通过条件是该 AST 与
   target-first `semantic_program` 在规范化后语义等价，不能只因二者在
   当前帧碰巧选中同一对象就通过。程序仍须在当帧完整 eligible catalog
   上唯一命中 target；target box 只来自冻结投影真值。独立模型判断与盲抽
   人审误差必须分栏报告，生成教师自评永远不算验证。
3. **BC-DIST-3 — 确认集构成与统计判据先冻结。** D2 任何训练、全量教师
   生成或 confirmatory-test 解封前，批次提案须冻结测试表达来源与风格
   分层比例、`δ`、seed 数、cluster 定义、重采样层级/次数和缺失输出规则。
   T-G1 成立的唯一判据为：按同 seed 配对、按 lineage/对象簇重采样所得
   `verified − template` 95% CI 的**下界 ≥ δ**，且 verified 臂通过 G2；
   点估计、单一风格分层或挑选最佳 seed 均不能替代。test 仍只解封一次。
4. **BC-DIST-4 — G0/D0 与 C1 热身分离。** G0/D0 是零 Play、零 API、
   零 GPU 的独立目录/数据合同停点。C1 热身另列批次，最多 2 配置 × 1
   seed，**累计总 GPU 用量 ≤5 GPU·h**，且须另获资源授权；它不是 G0/D0
   通过条件。必须记录三项而非“两项”审计：近重复矛盾标签率、
   template/current-crop 矛盾率、coordinates-only shortcut baseline。

Disposition:

- 提案作为设计章程接受，正式设计同步为 v0.3.18；`PROJECT_BRIEF.md`、
  既有运行时协议、旧 VLM work item 终态和 M1/M3′ 证据均不变。
- 本接受**不授权** D0–D3、C1 热身、实现、模型下载、API、GPU、
  Unity/Play、场景/车辆改动或 `UNITY_NA`。任何下一批先另行取得用户范围/
  资源授权，再提交批次提案；实现角色现在没有可执行交接。
- 评测教师保持可选；若未来启用，只能作同卷上界/次级报告，不能改变
  T-G1 或把生成教师称为视觉能力教师。

Accepted design-document changes: `docs/phase1-single-drone-design.md` v0.3.18
（核心研究问题、M6 归属与研究边界同步；无运行时实现语义变更）。

## COORD-010 disposition（2026-09-07）

Overall: `DEFERRED_RESEARCH_TRACK`。四臂/T-G1 退出近期工程首版前置；未执行确认性实验，不能记作负结果或“教师无增量”。恢复研究时重新审查数据、协议和预算，原确认性主张的证明要求保留。
依据：`docs/authorizations.md` 当日 COORD-010「批准 §10 A+B+C 整体落地」条目，
规则批 `R2@batch1` 已通过；本节由接受角色执行 §7 状态迁移，不新增 D/C/R 轮或 BC。
本节是当前处置入口；上方设计决定、历史执行安排及复核轮次原样保留，不再构成继续执行指令。
工程继承唯一清单见 `docs/implementation-status.md`「COORD-010 — 工程继承清单」；
来源缺口唯一收口记录见 `docs/unity-test-log.md`「COORD-010 — DATA-002 来源缺口收口」。
原图、目录、划分与归档不改写；后续加工、模型推理或训练须独立工作项及授权。
