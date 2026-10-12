# P1-SCENE-006 — T1′ 平价重定 amendment（外观/构造 parity + prompt parity）

- Work ID：`P1-SCENE-006`（沿用，不新开 ID）
- 状态：**`ACCEPTED_WITH_BINDING_CLARIFICATIONS`**（Acceptance round 3；BC-P2-1–8）
- 角色：构思（ideation）
- 日期：2026-08-04
- 上游合同：主 amendment §35（R17–R22）与 §36（用户授权收据与交接五项）
  （`docs/proposals/P1-SCENE-006-post-v2-anchor-route-amendment.md`）；
  复核 round 8 + addendum F20–F23（`docs/reviews/P1-SCENE-006.md`）；
  冻结 T1′ 协议 = 基础提案 §5.6 与 §5.2/§3.6
  （`docs/proposals/P1-SCENE-006-difficulty-scene-rebuild.md`）；
  COORD-005（workflow §4.3.2）；授权账本 2026-08-04
  "授权 F23 T1′ 有界重定 amendment"条目（`docs/authorizations.md`）。

## 0. 边界声明（先读这一节）

1. 本文件是**新的独立提案**，状态只可为 `PROPOSED`；它不把 amendment 1
   revision 5、§35、§36 或任何历史轮次重写成已接受，不修改
   `docs/phase1-single-drone-design.md`，不自行标 `ACCEPTED`。
2. 本提案获 Acceptance `ACCEPTED` 并给出逐条 binding clarifications
   之前：不开放任何代码/配置/测试修改，不运行任何诊断或正式 probe，
   不做 COORD-005 样帧检查，不启动 BC-B2-8 五辆落点目检，不推进
   M3′/DETECT criterion 4/M1。
3. 用户授权（账本 2026-08-04，逐字）限定的范围本提案全文遵守：只含
   probe 目标与运行时目标的外观/构造 parity、prompt parity、COORD-005
   至少 2 张样帧人眼确认、F20–F22 三项，以及被接受后的**一次**新的正式
   离线 T1′ 与其稳定候选复核。禁区零变化的逐项机制见 §8。
4. 原 `C_b2 = d2db9f3` 的全部工件（`runtime/p1-scene-006/
   probe-candidate-vfov40/`、`docs/evidence/P1-SCENE-006-probe-candidate-
   40deg.json`、灰色帧、`4/52`）与批 1 的 `16/99` 只读保留：不进入新门
   分母，不作为同尺度基线，不得依据其数值选择新 prompt、parity 带或任何
   阈值（本提案的反调参立场逐条见 §5.7）。
5. 一次执行纪律：整个重定方案预注册**恰好一次**正式离线 T1′ 执行；任何
   作废执行（工具缺陷或输入身份失配）都不自动补跑（§3.5.4）。预检与
   正式执行的额度分界见 §3.5.3。

## 1. 问题和研究价值

### 1.1 F23 缺口的准确形态

复核 round 8 对 `C_b2 = d2db9f3` 的代码符合性为 `PASS`——每个数字逐位
复算成立。addendum F23 随后证明**测量对象和提示帧都不是运行时的**：

- `Scene006SceneRig.CreateTargetReplica`
  （`Assets/TetheredTracking/Editor/Scene006/Scene006SceneRig.cs:89`）用
  两块 primitive 立方体复刻了运行时目标的几何（车身 localPosition
  `(0, 0.5, 0)`、localScale `(2, 1, 4)`；车顶 `(0, 1.2, -0.2)`、
  `(1.7, 0.7, 2)`），但**不赋任何材质**——正式 T1′ 的 106 帧渲染的是
  灰色无纹理替身，落在灰色沥青上。
- 运行时构造 `TetheredScenarioBootstrap.AddCarVisual`
  （`Assets/TetheredTracking/Scripts/TetheredScenarioBootstrap.cs:252`）
  用**同两块立方体、同尺寸**，但把车身涂成红 `(0.9, 0.12, 0.1)`、车顶
  暗红 `(0.65, 0.08, 0.07)`。scout-4（`172/187 = 0.919786`）与 DETECT
  qual-3 测的都是这辆红车。几何相同，外观不同。
- 提示帧第二处 parity 缺口：`k* = 2` 的真值框左边缘 `x = 0.000`
  （边界截断裁剪），`min(w, h) = 143.2294464111328 px`（P3 工件
  `t6.prompt_min_side_px`），是 T1 样本域中位数
  `63.25716018676758 px`（`t6.t1_domain_median_px`）的 **2.264 倍**，
  离轴 `23.1°` 对测量域钳位的 `45.0°`。§5.6 只要求 `V(s_{k*}) = 1` 和
  非空 `OK` 框，从未冻结"不截断"或尺度/视角可比性。

两处都是**已接受规格缺口**（Acceptance §35 归因），不是实现者偏离：
实现者按 BC-B2-2/6 字面执行了被接受文本。

### 1.2 后果与研究价值

`4/52 = 0.076923` 因此只是"v0.3.14 所指定灰色探针"的协议局部负结果：
它不能支持"候选场景/40° 光学/冻结检测器栈不可探测"，不能关闭
`P1-SCENE-006` 为场景级负结果，不能进入 M3′/M4′"不存在可分场景"论证
或投稿主张（§35 第 3–4 条）。三个 recall（`4/52`、`16/99`、scout-4
`172/187`）不同尺度，唯一的灰-灰内部对照(`4/52` vs `16/99`)保持历史
有效但同样只属灰色协议。

T1′ 是设计 §6 反天花板条款在探测轴上的唯一资格门。没有有效的 T1′，
候选场景既不能被资格化、也不能诚实地失败——SCENE-006 卡死在
`QUALIFICATION_UNDETERMINED_SPEC_GAP_F23`，M3′ 的场景适配门与投稿的
负结果叙述都失去载体。本重定恢复该门的效力；其两种走向都有研究价值：

- **PASS 带**（`≥ 0.90` 且嵌入证据获接受裁定）→ 场景在冻结栈下可探测，
  反天花板探测轴成立；
- **FAIL**（`< 0.85`）→ 在外观与 prompt 都公平后场景仍不可探测——这才
  是可进研究记录的场景级负结果（区别于灰色替身的协议事故）。

### 1.3 为什么是重定而不是就地修复

BC-B2-7 禁止在 `C_b2` 停点改变 T1′ 渲染对象；§5.5 反调参纪律要求
测量对象/参数变化在看到新数字**之前**决定；复核 F23 的"What I am not
doing"同判。唯一合法路径 = 新的构思/接受轮 + 预注册 parity 定义 + 新
工件身份 + 用户范围授权。该授权已于 2026-08-04 逐字落账。

## 2. 输入、输出与受影响接口

### 2.1 输入（全部只读、可独立复算）

| 输入 | 用途 | 只读性 |
|---|---|---|
| `docs/evidence/P1-SCENE-006-p3-finalist.json`（round 5 已复核，`sha256 = 87b24e7e…0578`）：`t6.samples[k]`（k = 0…10 的 `frustum_visible`/`geometrically_visible`/`min_side_px`）、`t6.t1_domain_median_px`、`finalist_trace_sha256`、`selection.finalist.s_init` | warmup 段逐 k 交叉核对与 trace/s_init/一致性钉（AR3 后尺度/离轴带改锚 D 域，§3.2.2；`t1_domain_median_px` 仅作 P3 一致性钉，不再作带锚） | 既有已复核工件，不改 |
| `config/scenario.p1-scene-006.json`（`0e6407b` 提交字节，capture manifest `scenario_sha256 = ec4154d1…c831`） | 唯一场景定义；F21 回归钉的钉住对象 | 字节零变化（§8） |
| 基础提案 §5.2（trace/步内次序/云台律）、§3.6（T6）、§5.6（T1′ 冻结协议） | 除 §3 明列的取代项外逐字继承 | 不改 |
| `docs/reviews/P1-SCENE-006.md` round 8 + F20–F23 | 缺口定义与验收对照 | 不改 |
| `config/detector-reanchor.models.json`、`config/nanotrack-v2.models.json` 权重哈希 | 链第 1 步绑定，沿用 | 不改 |
| 原 `C_b2` 工件与批 1 `16/99` | 仅历史引用（§0.4） | 只读，非调参源 |

### 2.2 输出（被接受并实现后）

1. `Assets/TetheredTracking/Scripts/TargetVisualFactory.cs`（新）：目标
   视觉唯一构造源；`TetheredScenarioBootstrap.AddCarVisual` 与
   `Scene006SceneRig.CreateTargetReplica` 均改为委托它（§3.1）。
2. prompt 律 v2 选择工具与**已提交**选择工件
   `docs/evidence/P1-SCENE-006-prompt-selection-p2.json`（§3.2；含 D 域
   全表与分位端点、池 P 的逐 k E 表、`k*′` 与诊断 tick `k_diag`）。
3. v3 capture manifest（新增 `target_appearance`、`prompt_eligibility`、
   `expected_k_star_p2`、`selection_artifact_sha256` 等字段）与
   **自包含**门工件
   `docs/evidence/P1-SCENE-006-probe-candidate-40deg-p2.json`（F20，§3.4）。
4. F21 回归钉 EditMode 测试；F22 分位口径更正（§3.4）。
5. 新采集目录 `runtime/p1-scene-006/probe-candidate-vfov40-p2/`（新
   ProbeId `p1-scene-006-candidate-vfov40-p2`）与证据文件
   `docs/evidence/P1-SCENE-006-t1prime-p2.md`（含 COORD-005 人眼记录）。

### 2.3 受影响接口与零影响面

受影响：上列文件，加 `Scene006CandidateProbe.cs`/
`Scene006ProbeRenderer.cs`（选择阶段、manifest 字段、冻结路径集 v2）、
`tools/run_scene006_probe.py`（新字段校验与身份回显）、对应测试。

零影响（写入边界外，§8 逐项给机制）：scenario schema 与全部配置字节、
帧桥/控制协议、控制器/感知/评估器语义、`CoverageEvaluator`、主指标、
M3′ 章程（BC-M34-*）、DETECT criterion 4、Play/session/run ID 体系。
`AddCarVisual` 的修改是**纯委托重构**，运行时渲染结果必须逐字面不变
（§3.1.3），scout-4/qual-3 基线不受扰动。

## 3. 算法与行为规格（重定协议本体）

### 3.1 R17 — 测量对象 parity：单一构造源

1. **构造源与冻结 API（AR5 重写）**：新建 `TargetVisualFactory`
   （运行时程序集），公开合同冻结为：

   ```csharp
   public static class TargetVisualFactory
   {
       public static readonly Color BodyColor = new Color(0.9f, 0.12f, 0.1f);
       public static readonly Color RoofColor = new Color(0.65f, 0.08f, 0.07f);

       public readonly struct Build
       {
           public readonly GameObject Body;
           public readonly GameObject Roof;
           public readonly Renderer BodyRenderer;
           public readonly Renderer RoofRenderer;
           public readonly Collider BodyCollider;
           public readonly Collider RoofCollider;

           public Build(
               GameObject body, GameObject roof,
               Renderer bodyRenderer, Renderer roofRenderer,
               Collider bodyCollider, Collider roofCollider)
           {
               Body = body;
               Roof = roof;
               BodyRenderer = bodyRenderer;
               RoofRenderer = roofRenderer;
               BodyCollider = bodyCollider;
               RoofCollider = roofCollider;
           }
       }

       public static Build AddTargetVisual(Transform parent);
   }
   ```

   该声明按字面可编译（AR5a：`readonly struct` 的全部实例字段
   `readonly` 并由显式构造器赋值）；两个方法签名与字段集冻结，
   `AddTargetVisual` 的方法体属实现内容。

   语义逐条冻结：两块 `GameObject.CreatePrimitive(PrimitiveType.Cube)`；
   `SetParent(parent, false)` 后**显式**覆写 localPosition / localRotation
   （= identity）/ localScale——车身 `(0, 0.5, 0)`/`(2, 1, 4)`、车顶
   `(0, 1.2, -0.2)`/`(1.7, 0.7, 2)`；材质赋值走现状路径
   `GetComponent<Renderer>().material.color = BodyColor / RoofColor`
   （默认 primitive 材质，不引入新 shader/渲染设置）；**collider 原样
   保留并经 `Build` 返回，由消费者移除**；工厂不设 `hideFlags`、不做
   命名簿记。几何/颜色字面量在**生产构造路径**（Assets 内实际构建
   对象的代码）只存在于工厂一处；独立验证 oracle 的 expected 副本
   按 §3.1.4(a) 单列冻结，不受此唯一性约束（AR5b）。
2. **双消费者（AR5：清理归属冻结为消费者所有）**：
   - `AddCarVisual(parent)` 改写为：调用工厂一次，然后
     `Destroy(b.BodyCollider); Destroy(b.RoofCollider);`——除此**再无
     任何构造语句**；运行时输出与现状逐字面一致（同几何、同色、
     collider 同样被移除）。
   - `CreateTargetReplica` 改写为：创建 root GameObject（名称与
     `DontSave` 簿记照旧）→ 调用工厂一次 → `DestroyImmediate` 两个
     collider → 对 `Body`/`Roof` 设 `hideFlags = DontSave` →
     `TargetRenderers = { BodyRenderer, RoofRenderer }`。
   - 允许的消费者差异**穷举为三类且全部作用于返回值**：(i) collider
     移除 API（运行时 `Destroy`，Editor `DestroyImmediate`）；(ii)
     Editor 侧 `hideFlags` 后处理；(iii) 父/根对象命名与归属簿记。
     其余任何差异都是缺陷。可行性依据：
     `TetheredTracking.Scene006.Editor` 程序集已引用运行时类型
     （`Scene006SceneRig` 直接使用 `EvaluationOcclusionGeometry`、
     `ScenarioConfig`），单一构造源无程序集障碍。
3. **运行时不变性（保护 DETECT 基线）**：重构后运行时目标的渲染结果
   必须与现状逐字面一致。`SetParent` 形态等价性论证：cube 由
   `CreatePrimitive` 生成于原点、identity 旋转，工厂显式覆写全部
   local TRS，故 `SetParent(parent)`（现运行时形态）与
   `SetParent(parent, false)` 产物逐字段相同；测试断言**最终**
   local TRS 与颜色，不断言中间调用形态。钉法：(a) 工厂合同 EditMode
   测试断言 raw `Build` 的 mesh/localPosition/localRotation/localScale/
   材质颜色逐分量等于**测试源码内硬编码的 expected 副本**，且两个
   collider **存在**（证明清理确属消费者）；(b) rig 真实入口测试：
   `CreateTargetReplica` 后按测试自持副本断言已涂色、无 collider、
   `DontSave` 生效；(c) 复核核对 `AddCarVisual` 为"工厂调用 + 两行
   Destroy"式纯委托，且**生产构造路径**无第二处颜色/尺寸字面量
   （§3.1.4(a) 的 oracle 副本除外、逐文件可枚举）。颜色、尺寸、位置
   字面量**一个字节都不许动**——它们是 scout-4/qual-3 所测对象的定义。
4. **生产源与验证 oracle 分离（AR5b 重写）**：
   (a) **oracle 清单——每个比较点的 expected/actual 来源逐项冻结。**
   字面量唯一性只约束生产构造路径；下列**四份版本化独立 expected
   副本**特意重复同一组数值，使"改工厂而不改 oracle"必然变红，缺一
   即验收不过：

   | 比较点 | expected 来源 | actual 来源 |
   |---|---|---|
   | 工厂合同 EditMode 测试（§3.1.3a） | 测试源码硬编码字面量 | 工厂 `Build` 实物 |
   | rig 入口 EditMode 测试（§3.1.3b） | 测试源码硬编码字面量 | `CreateTargetReplica` 构建的 replica |
   | 渲染器 P 阶段外观干跑预检（§3.5.3） | Editor 侧 `Scene006AppearanceContract` 静态冻结块（**不引用**工厂常量） | 现场构建 replica 的遍历值 |
   | 分析器 `target_appearance` 比对 | 分析器源码内 Python 冻结常量块 | manifest `target_appearance`（渲染器从实物 replica 读出） |

   四处 expected 都**不得**从工厂、被测对象、manifest 或配置反读。
   (b) **自动外观回归（fail-closed，沿用）**：渲染器在正式采集**写盘
   前**遍历 replica 的全部 Renderer，把逐立方体
   `{mesh 名, localPosition, localScale, material color RGBA, shader 名}`
   写入 manifest `target_appearance` 块；分析器把该块与 (a) 表第 4 行
   的独立常量比对，任何不等 → 整份探针按
   `PROBE_FIDELITY_CONTRADICTION` 类处理（沿用 §5.6 链第 3 步语义），
   不产出 recall。
5. **不设后备形态（AR5b 删除原后备条款）**：程序集可达性已论证
   （§3.1.2），双构造后备撤销。若实现期仍发现单一构造源不可行，唯一
   合法动作是带着具体障碍退回 Acceptance 重裁；Implementation 不得
   自行切换协议或恢复双构造。

### 3.2 R18 — prompt 律 v2（AR3 重写：对 D 域 parity，运行前冻结，fail-closed）

1. **候选池（AR3b 恢复为 warmup 窗口）**：`P = [0, 10] ∩ ℤ`（T6 预注册
   `K_acq` 窗口），按 `k` 升序判定。提示帧保持已接受设计的阶段关系：
   T6 采集帧 `s_{k*′}`、`k*′ ≤ 10 < 15`，与测量帧集 `M = {15, 20, …,
   540}` 构造性不相交，永不进入 recall 分母。**Revision 1 的
   `[0, 540] \ M` 扩池及其"扩池不改帧集"解释撤回**（AR3b）：该扩展
   同时触及逐字冻结的"帧集"、已接受设计中 T6/T1′ 的 prompt 阶段关系
   与核心研究主张，不能由构思/接受角色从"prompt parity"的授权文字中
   自行推定。在现有授权下 prompt 帧域即 warmup 窗口；若 E 在本池上为
   空，走第 7 条的 `PROTOCOL_PRECONDITION_UNSATISFIED` 终态，**不得为
   避免空集扩池**；任何路中 prompt 帧域及主张变化只能在该终态发生后，
   凭选择工件的逐 k 证据另行请求用户逐字授权（本提案不预支）。
2. **测量域 D 与分布（AR3a 重写：与 recall 分母同一集合，禁止缩域）**：
   在任何 detector/embedding 运行之前，选择工具从冻结 trace/场景按
   §5.2 语义重放，对全部 106 个测量 tick 计算 `V(s_k)`、
   `target_box_status`、`min(w, h)_px`、applied 离轴角。先定义
   `D_V = { k ∈ M : V(s_k) = 1 }`——即基础 §5.6 的目标分母集合；再
   **逐成员**检查 `target_box_status = OK`：任一 `D_V` 成员不满足即
   renderer/evaluator 保真矛盾，选择工具立即 fail-closed **拒绝生成
   工件**（P 阶段预检做同一检查再拦一次），**不得**计算分位、选择
   prompt 或把该成员从域中删除——与 §5.6 链第 3 步"任一成员 truth
   box 不可投影 = 整份 `PROBE_FIDELITY_CONTRADICTION`"同义。全员通过
   后令 `D = D_V`，对 `D` 计算 `min_side_px` 与离轴角的 **type-7 分位
   `q05`/`q95`**；选择工件必须**机械断言 `|D|` 等于正式目标分母计数**，
   分析器侧以同一断言回验。**选择工具禁止读取旧采集目录**
   （`runtime/p1-scene-006/probe-candidate-vfov40/` 的帧与 truth 边车
   既不是输入也不是对照）；`D` 的一切数值由几何重放独立产生，复核可
   在 worktree 逐位重算。
3. **资格谓词 E(k)**（对池内每个 k，全部在 `p_hover`、§5.2 冻结
   trace/云台律上确定性计算；图像尺寸 640×480）：
   - (a) `V(s_k) = 1`（§5.1 谓词，视锥 + 射线，不变）；
   - (b) 真值框可投影且 `OK` 非空（不变）；
   - (c) **不截断**：裁剪后真值框四边距画幅边界均 `≥ 2.0 px`，即
     `x·640 ≥ 2 ∧ y·480 ≥ 2 ∧ (x+w)·640 ≤ 638 ∧ (y+h)·480 ≤ 478`
     （闭区间；`k* = 2` 的 `x = 0.000` 属被裁剪证据，此判据把"投影
     超出画幅被裁剪"与"完整在幅内"机械区分）；
   - (d) **尺度带（AR3 重锚）**：
     `min(w, h)_px(k) ∈ [q05_t7(D_minside), q95_t7(D_minside)]`；
   - (e) **离轴带（AR3 重锚，双边）**：applied 离轴角
     `∈ [q05_t7(D_offnadir), q95_t7(D_offnadir)]`。
   (d)(e) 均为双边闭区间，量纲显式（px / deg）、分位口径显式
   （type-7），端点由 `D` 确定性导出、写入选择工件——**不是手选
   常量**。机械拒绝性由构造保证：任何"尺度高于域上分位 / 离轴低于域
   下分位"的 F23 类提示帧按定义出带。Revision 0 的 `2.0 × M` 倍频程
   上限与 `median − 30°` 护栏**撤销**（AR3：它们不能机械拒绝
   `23.1°` vs `45°` 类失配）。
4. **选择函数**：`k*′ = min { k ∈ P : E(k) }`（`P` = warmup 窗口，
   第 1 条）。无平局问题。
5. **选择工件（先提交、后采集）**：
   `docs/evidence/P1-SCENE-006-prompt-selection-p2.json` 记录：
   106 测量 tick 全表（V/status/min_side/离轴）、`D_V` 全员 `OK` 断言
   与 `|D|` = 分母计数断言、两组 type-7 `q05`/`q95` 端点、全池
   （= warmup `[0, 10]`）逐 k E 全表
   `{V, 框 (x, y, w, h), 四边余量 px, min_side_px, applied 离轴角,
   E(k), 首个不满足子句}`、选定 `k*′`、诊断 tick `k_diag`（§3.3.2），
   以及**逐位交叉核对**：全池各 k 的
   `frustum_visible`/`geometrically_visible`/`min_side_px` 必须与 P3
   `t6.samples` 逐位相等；`t1_domain_median_px`（仅一致性钉）、
   `finalist_trace_sha256`、`s_init`、config `scenario_sha256` 同时
   绑定相等。任何不等 → 选择工件拒绝生成（fail-closed），回实现返工。
6. **采集侧绑定**：v3 manifest 以 `expected_k_star_p2` + 选择工件
   SHA-256 取代旧 `expected_k_star`（P3 `t6.k_star = 2` 的绑定仅对
   T1′(v2) 退役；P3 的 trace/s_init/config 绑定全部保留）。渲染器在
   写盘前独立重算 `D` 分位端点、E 全表与 `k*′`，与选择工件任何一行
   不等即中止且不写正式工件。分析器校验 manifest 的
   `prompt.tick_k == expected_k_star_p2 == 选择工件 k*′`。
7. **空集处分（AR4 收窄）**：`E` 全空 → 终态
   **`T1P2_PROMPT_LAW_UNSATISFIABLE`**：不渲染、不消耗执行额度。合法
   主张上限 = **`QUALIFICATION_UNDETERMINED /
   PROTOCOL_PRECONDITION_UNSATISFIED`**——只证明"当前预注册 parity
   协议在池 `P` 上无可用提示帧"，**不证明**场景无法干净初始化，更不
   作为终端负结果关闭依据。处置：回 Acceptance/Ideation 重议协议；
   任何改场景/光学/prompt 帧域/窗口的出路都需新的用户逐字授权（凭
   选择工件逐 k 证据提出）。Revision 0"初始化可观测性负结果"的升格
   主张**撤回**。
8. **主张定界（AR3b 恢复初始化域语义）**：T1′(v2) 的 PASS 带主张是
   "给定该场景自身 T6 采集窗口内一张不截断、且尺度/离轴均落在 `D` 的
   type-7 `[q05, q95]` 带内的提示帧，冻结栈可沿困难段再探测目标"。
   提示帧仍是初始化域帧——revision 1"域内提示再探测"的主张改写
   **撤回**。提示帧相对 `D` 分位的确切位置（尺度、离轴、`k*′`）是
   工件与证据的**强制报告项**，不混入门判定，也不得事后重释主张。
   初始化可观测性本身归 T6（已 PASS，未动）。

### 3.3 R19 — COORD-005 人眼保真门（≥ 2 样帧，硬前置，AR1 重排）

1. **时点（AR1 重排：先于稳定候选冻结与独立复核）**：次序冻结为——
   批次 T 实现完成（工厂、选择工具、**选择工件已提交**、manifest/
   分析器 v3、测试）→ 经诊断通道渲染样帧并完成人眼确认与记录 →
   **然后**才声明 T 稳定候选 → Acceptance 停点审计（workflow §4.3.1
   五条件）→ independent Review → `PASS` 后方可唯一正式执行。人眼
   检查因此严格早于"协议冻结或首次正式采集"两个时点（workflow
   §4.3.2）。人眼失败 → 回实现修复 → **重新**生成诊断样帧并重新确认
   → 重新声明稳定候选、重新停点审计、重新复核；失败前的任何 Review
   verdict 一律作废不得沿用；不消耗执行额度。诊断活动走 COORD-005
   诊断验证通道：零 scenario/session/run ID，样帧本体不进证据链、不作
   门判定输入（人眼**记录**按 §4.3.2 进证据文件）。
2. **内容（AR2 更正）**：用 parity 修复后的同一渲染管线渲染**恰好
   2 张**诊断样帧，tick = `{k*′, k_diag}`，两者都由选择工件在渲染前
   给出：`k_diag` = `D` 按 tick 升序的 **lower median**（索引
   `⌊(|D| − 1) / 2⌋` 的成员），属 `D` 故必然 `V = 1` 且真值框 `OK`
   非空；该选择只用几何/truth，不读取任何检测分数。**Revision 0 硬编
   码 tick `275` 撤回**——既有真值边车证明该 tick
   `TARGET_NOT_VISIBLE`，不能承担外观检查（AR2）。输出到独立诊断目录
   （文件名前缀 `diag_`，不得写入正式 ProbeDirectory）。对照物 =
   运行时外观参照（归档 qual-3/scout-4 会话帧，或用户的一次诊断性
   Play 目检）。确认命题：目标为与运行时同构造的红/暗红双立方体车，
   非灰色替身；场景车辆与光照无范畴错误。
3. **记录（硬性）**：样帧路径、确认人（用户或当轮发令角色）、结论写入
   `docs/evidence/P1-SCENE-006-t1prime-p2.md`。缺记录 = 协议缺口 =
   复核阻断项（workflow §4.3.2 原文义务；复核在停点审计后核对该记录
   已在场）。
4. **反调参**：诊断帧上禁止运行检测器/嵌入器/任何打分；诊断帧不得复用
   为正式帧（正式执行整体重渲染）；诊断通道不得用于在正式运行之间
   "试数"。确认失败 → 终态 **`T1P2_HUMAN_FIDELITY_FAIL`**（协议阻断，
   回实现返工，不消耗执行额度）。

### 3.4 F20 / F21 / F22 的落实

1. **F20 身份耐久**：分析器把 v3 manifest 的完整身份块逐字回显进**已
   提交**门工件：`capture_commit`、`tool_commit`、
   `git_status_porcelain`、`frozen_tool_paths`（v2 集）、
   `tool_path_zero_diff_verified`、`scene_file_sha256_before/after`、
   `baseline_scenario_sha256`、`scenario_sha256`、`trace_sha256`、
   `selection_artifact_sha256`、`manifest_sha256`。任何字段缺失或与
   manifest 不等 → fail-closed 不产出。验收可证伪性：删除 `runtime/`
   捕获目录后，仓库单独仍可核对全部身份字段文本。
2. **F21 真实配置回归钉（AR6c 补强）**：新增 EditMode 测试对
   `config/scenario.p1-scene-006.json` **真实文件**执行 `LoadAndBind`，
   断言 (i) 文件 SHA-256 等于**测试源码中硬编码的完整字面量**
   `ec4154d1c7a945b70a8d8ed9fa1c6937552fde1a3fc88e364eb83881eb31c831`
   （由本提案与接受文本冻结；**禁止**在运行时从当前配置自身、
   gitignored manifest 或任何派生物读取期望值——否则配置与"期望"可
   一起漂移而不红）；(ii) 绑定后的锚点 `(197.0, 30.0)`、高度
   `16.0`、vfov `40.0`、8 顶点路线 = default `+(+60, −60)` 逐位、五条
   relocation 行、`expected_distractor_count = 0` 与冻结值逐项相等。
   此后任何对该配置的编辑都会挂测试套件，而不是等到重跑才暴露。
3. **F22 分位口径更正（同批次，证据 owner 执行）**：
   `docs/evidence/P1-SCENE-006-batch2-config.md` §3.4 及状态板任何回显
   把 `44.07 px` 改标为"第三小值（lower/nearest-rank）"，并列报 type-7
   分位 `48.67 px`；或统一重算为 type-7。两种口径永不共用 `p05` 标签。
   无门影响（F22 原文），但属本批次验收项。

### 3.5 新工件身份、冻结路径集 v2 与一次执行纪律（R20）

1. **新身份**：ProbeId `p1-scene-006-candidate-vfov40-p2`；采集目录
   `runtime/p1-scene-006/probe-candidate-vfov40-p2/`；门工件
   `docs/evidence/P1-SCENE-006-probe-candidate-40deg-p2.json`；manifest
   增加 `t1prime_protocol = 2`。旧目录/工件只读，新旧永不合并。
2. **冻结路径集 v2** = batch-1b 九条逐字 + 第十条
   `Assets/TetheredTracking/Scripts`（目录 pathspec）。理由：目标构造
   进入渲染路径后，运行时脚本也成为 T1′ 渲染语义的一部分；
   `tool_commit..capture_commit` 零 diff 证明必须覆盖它。`tool_commit`
   按 F16 语义在十条路径上 `git log -1` 导出。capture HEAD 可等于
   工具候选（本次无新配置提交），也可仅隔文档提交——两者都以零 diff
   证明为准。
3. **两阶段与额度分界（AR6a 具名拆分）**：
   - **预检阶段 P（零额度）**：正式 ProbeDirectory **创建之前**的全部
     检查——选择工件交叉核对（§3.2.5/6 的重算比对）、外观干跑预检
     （按 §3.1.4 字段清单构建并核对 replica，不写盘）、模型/权重配置
     哈希预检、身份链预检（porcelain 空、十路径零 diff、场景哈希）、
     COORD-005 记录在场性。任一失败 → 具名
     **`T1P2_PRECHECK_FAIL_<原因>`**，回实现返工，零额度消耗；预检
     产物不得写入正式目录或与正式工件混放。
   - **正式执行阶段 X（耗额度）**：始于渲染器在全部预检通过后**创建
     正式 ProbeDirectory** 的时刻；此后任何中止一律按一次执行已消耗
     处理。X = 单次渲染器调用 + 单次分析器调用，在满足身份链的干净
     HEAD 上进行；启动时 ProbeDirectory 已存在或非空即拒绝（防第二
     次）；复核按 round-8 方法核对 reflog 单线与单一 probe 日志。
4. **作废执行规则（AR6b 命名修正，fail-closed 于额度）**：X 阶段终止
   于冻结链第 1 步（模型/权重哈希不符）＝
   **`T1P2_EXECUTION_VOID_INPUT_IDENTITY`**（输入/环境身份失配，不称
   工具缺陷）；终止于链第 2–3 步（`PROBE_INCOMPLETE`、
   `PROBE_FIDELITY_CONTRADICTION`——含 §3.1.4 外观回归不等到达写盘
   时点）＝ **`T1P2_EXECUTION_VOID_TOOL_DEFECT`**。两类作废产物均
   只读归档、逐类归因；**一次执行额度均视为已消耗**，任何重跑都需
   用户新的逐字授权。本提案不自授重试。链第 4–7 步的产出是该次执行
   的有效终读。哈希失配正常应被 P 阶段预检拦下（零额度）；到达 X 仍
   失配说明预检与执行之间发生了状态漂移，按已消耗如实记录。
5. **前置序（AR1 重排，全部满足才可执行）**：(a) 本提案 `ACCEPTED` +
   binding clarifications；(b) 批次 T 实现完成，选择工件已提交且交叉
   核对通过；(c) COORD-005 人眼确认与记录完成（**先于**稳定候选声明，
   §3.3.1）；(d) T 稳定候选声明 + Acceptance 停点审计 + independent
   Review `PASS`（本 work item 改变门的模型输入语义，属 workflow
   §4.3.1 强制停点）；(e) P 阶段预检全绿。

## 4. 与 v0.3 设计（v0.3.14 + §35/§36 更正）的兼容性

**逐字继承、零变化**的 §5.6 条款：106 帧集合 `k = 15, 20, …, 540` 与
生成方式；目标/干扰配对与逐类处分；权重哈希绑定；最低样本数 40/40；
recall 带 `0.85/0.90`；嵌入/margin 证据只报告不判门；处分链次序与
"工具态永不 `PASS`、`gate_state` 由接受角色单列"；批次归属纪律。
§5.2 trace/步内次序/云台律、§3.6 T6 门本体（其批 1 `PASS` 记录原样
成立）、T1–T5/P1–P3 全部批 1 工件与结论：不动。

**仅对 T1′(v2) 取代**的条款：提示帧选择律（T6 采集帧的"最小可见"
选择 → §3.2 在同一 warmup 窗口 `[0, 10]` 内按 `D` 锚定 parity 带的
资格选择，`expected_k_star_p2` 绑定；帧域与 `k*′ ≤ 10 < 15` 不相交
性质不变）；
manifest/工件身份（v2 块自包含化，F20）；冻结路径集（+`Scripts`）；
探针身份常量（§3.5.1）。设计文档的对应落笔由 Acceptance 在接受时
完成（预计 v0.3.15），本提案不触碰设计文件。

BC-M34-4/5/6/9、BC-M34-7、DETECT criterion 4、主指标定义：零变化。
BC-B2-8 的五辆落点/场景合理性非 Play 目检：**不豁免、不由本提案
执行**，仍是 work item 终端收束的前置。

## 5. 可证伪的验收条件

### 5.1 A — 外观 parity

- A1：工厂公开合同 EditMode 测试（§3.1.3a：raw `Build` 字面量逐分量 +
  两 collider 在场）与 rig 真实入口测试（§3.1.3b）都通过，expected
  均为测试源码硬编码副本（§3.1.4a）；只改生产工厂任一颜色/尺寸/位置
  分量、不动 oracle，即红。
- A2：复核确认 `AddCarVisual` 为"工厂调用 + 两行 `Destroy`"纯委托、
  消费者差异不超出 §3.1.2 穷举三类、生产构造路径无第二处颜色/尺寸
  字面量、§3.1.4(a) 四份 oracle 副本齐备且都不从工厂/被测物/manifest/
  配置反读（diff + grep 级核对）。
- A3：正式 manifest `target_appearance` 与冻结字面量分析器比对通过；
  人为改动 replica 材质可被该链路机械捕获（可证伪）。
- A4：COORD-005 记录存在、结论为确认（§3.3.3）。

### 5.2 B — prompt 律

- B1：选择工件（含 106 tick 全表、`D_V` 全员 `OK` 与 `|D|` = 分母
  断言、type-7 `q05`/`q95` 端点）可由复核在一次性 worktree 独立重算
  并逐位复现。
- B2：warmup 段逐 k 交叉核对与 P3 逐位相等（§3.2.5）；不等则工件
  拒绝生成。
- B3：渲染器写盘前重算 `D` 端点、E 全表与 `k*′`，与选择工件不等即
  中止（可用合成篡改测试证伪）。
- B4：正式 prompt 帧/真值 sidecar 哈希绑定 manifest；其真值框事后
  按 §3.2.3 重验必须满足 E（对渲染产物的封闭复检）。
- B5：`E` 全空时不存在任何渲染产物且终态为
  `T1P2_PROMPT_LAW_UNSATISFIABLE`（主张上限见 §3.2.7）。

### 5.3 C — 身份与耐久

- C1：门工件自包含身份块逐字段与 manifest 相等（F20）。
- C2：十条冻结路径 `tool_commit..capture_commit` 零 diff；porcelain
  空；场景哈希前后一致。
- C3：`scenario_sha256` 等于 batch-2 提交值（**本次不允许任何新配置
  提交**——配置字节已存在且被禁区冻结）。
- C4：F21 钉测试在套件中且通过；F22 口径在证据与状态板同批更正。

### 5.4 D — 终态矩阵（R22，穷举）

| 阶段 | 终态 | 触发 | 额度 | 合法主张上限 | Acceptance 处分空间 |
|---|---|---|---|---|---|
| 预运行 | `T1P2_PROMPT_LAW_UNSATISFIABLE` | E 在池 `[0, 10]` 上全空 | 不消耗 | **`QUALIFICATION_UNDETERMINED / PROTOCOL_PRECONDITION_UNSATISFIED`**：仅"预注册 parity 协议在 warmup 池上无可用提示帧"，无任何场景级主张（AR4） | 回 Acceptance/Ideation 重议；改场景/光学/prompt 帧域 = 新用户逐字授权（凭选择工件逐 k 证据） |
| 预运行 | `T1P2_HUMAN_FIDELITY_FAIL` | COORD-005 确认失败 | 不消耗 | 无（协议缺陷） | 回实现返工；失败前 Review verdict 作废（AR1），重走 H→S |
| 预检 P | `T1P2_PRECHECK_FAIL_<原因>` | §3.5.3 P 阶段任一检查失败（选择/外观干跑/哈希/身份链/记录在场性） | 不消耗 | 无 | 回实现返工 |
| 执行 X | `T1P2_EXECUTION_VOID_INPUT_IDENTITY` | 链 1：模型/权重哈希不符 | **已消耗**，重跑需用户逐字授权 | 无 | 归因输入/环境身份失配（AR6b）；向用户提示是否再授权 |
| 执行 X | `T1P2_EXECUTION_VOID_TOOL_DEFECT` | 链 2–3：`PROBE_INCOMPLETE` / `PROBE_FIDELITY_CONTRADICTION`（含外观回归不等） | **已消耗**，重跑需用户逐字授权 | 无 | 归因工具缺陷；向用户提示是否再授权 |
| 执行 X | `INCONCLUSIVE`（下限） | 目标或干扰样本 `< 40` | 已消耗 | 样本不足，无探测结论 | 不得放宽下限或加帧；回用户 |
| 执行 X | `FAIL` | recall `< 0.85` | 已消耗 | **平价协议下的场景级再探测负结果**（受 §3.2.8 主张定界） | 可作 SCENE-006 负结果处置基础；终端关闭仍需 BC-B2-8 目检 + 用户授权 |
| 执行 X | `INCONCLUSIVE`（带间） | recall `∈ [0.85, 0.90)` | 已消耗 | 不可判 | 不得重跑救带；回用户 |
| 执行 X | `AWAITING_EMBEDDING_FEASIBILITY_REVIEW` | recall `≥ 0.90` | 已消耗 | 工具态非 PASS；等待接受裁定 | 引完整嵌入/margin 工件单列裁定最终门态 |

矩阵外无合法终态；工具态在任何路径都不产出 `PASS`；`gate_state`
硬 `null`、owner 为 Acceptance（沿用）。任何终态都不得把 `4/52`、
`16/99` 混入分母或称同尺度基线；跨协议比较只许定性、标注协议差异、
不作证据（§0.4）。

### 5.5 证据完备

正式工件必须含：全部 `V = 1` 目标样本（`|D|` 条）逐条
IoU/cosine/margin（沿用）、`prompt_eligibility` 全表与 `D` 分位端点
回显、`k*′` 来源段及其尺度/离轴相对 `D` 分位的位置（§3.2.8 报告项）、
`target_appearance` 块、完整身份块。证据文件必须含 COORD-005 记录与
§3.2.8 的主张定界文字。

### 5.6 预注册规则的地位（AR3 后重写）

新律只保留一个手选常量：截断余量 `2.0 px`（像素栅格最小可靠间隔）。
尺度带与离轴带不再有手选端点——规则本身（type-7 `[q05, q95]` 中央
90% 区间，AR3 指定的可选形态之一）是手选并预注册的，端点由 `D` 从
冻结几何确定性导出、在选择工件中落数。Revision 0 的 `2.0 × M` 倍频程
上限与 `median − 30°` 护栏**已撤销**（AR3：不能机械拒绝 F23 类差异）。
Acceptance 在接受前可收紧/否决（如改 `[q10, q90]`；binding
clarifications 即冻结点）；**接受后与看到任何新渲染/新数字后均不可
再调**。

### 5.7 反调参立场（§36 第 4 项的逐条回应）

- 新律的全部参数来源：P3 已复核几何量（`M`、逐 k 可见性/尺寸）、
  §5.2 确定性重放（离轴中位数、逐 k 框）、以及 §5.6 的既有常量。
  **无一来自灰跑的 recall/IoU/cosine/命中集合。**
- 本提案引用的灰跑数字（`4/52`、`x = 0.000`、`23.1°`、命中/未中几何
  画像）全部只出现在 §1 问题陈述与授权账本归因中，均为历史事实引用，
  不参数化任何新判据。
- 选择工件在渲染前提交并绑定；正式工件产出后任何参数/帧集/阈值/测量
  对象调整都被 §3.5、§5.4 与 §5.5（基础提案）双重禁止。

## 6. 基线、消融、失败模式和资源风险

### 6.1 对照与消融

- **无同尺度基线**：`16/99` 属灰色协议，scout-4 属另一场景/Play 模式。
  T1′(v2) 只对预注册绝对带（`0.85/0.90`，禁区冻结）判读——此立场在
  运行前写死，防止事后挑对照。
- **不做消融**：一次执行纪律排除 A/B（不重跑 60° 灰-红对照）；重定
  目标是恢复门效力，不是研究外观效应。

### 6.2 失败模式

| 模式 | 先验缓解 | 残余处置 |
|---|---|---|
| warmup 池 `[0, 10]` 全部截断/出带 → E 空 | 几何连续性（似然非保证）：`D` 最早成员（k = 15 起）与 warmup 末段（k = 8–10）仅隔约 1 s，`D` 锚定的 `[q05, q95]` 带对晚段 warmup 帧有真实容纳可能 | `T1P2_PROMPT_LAW_UNSATISFIABLE`，不耗额度；主张按 AR4 只到协议前置不满足；此后如需路中帧域，凭选择工件逐 k 证据请求用户逐字授权 |
| 人眼确认失败 | 单一构造源使替身与运行时同码 | 返工，不耗额度；失败前 Review 作废并重走 H→S（AR1） |
| 输入身份失配到达 X 阶段 | P 阶段哈希/身份链预检正常拦截（零额度） | `T1P2_EXECUTION_VOID_INPUT_IDENTITY`，已耗额度 + 用户再授权（AR6b） |
| 工具缺陷中断正式执行 | 选择/外观干跑双预检 + 既有链 2–3 | `T1P2_EXECUTION_VOID_TOOL_DEFECT`，已耗额度 + 用户再授权 |
| recall 落 `[0.85, 0.90)` | 无（诚实带间） | `INCONCLUSIVE` 终读，回用户 |
| recall `< 0.85` | 无（真实场景难度） | 场景级负结果路径（§5.4） |

### 6.3 资源

一个实现批次（工厂重构 + 选择工具 + manifest/分析器 v3 + 测试 +
F22 更正）＋一轮独立复核＋2 张诊断样帧（分钟级用户时间）＋一次离线
执行（107 帧渲染 + CPU/MPS 分析，分钟级）。零 Play、零 session/run
ID、零新依赖、零配置字节。BC-B2-8 目检的用户时间在本提案之外。

## 7. 建议但不强制的实现范围

| 阶段（AR1 次序） | 内容 | 门 |
|---|---|---|
| T（实现） | §3.1 工厂 + §3.2 选择工具/工件 + §3.4 F20/F21/F22 + manifest/分析器 v3 + 测试 | 完成后**先进 H**，不得先声明稳定候选 |
| H（人眼） | 诊断通道 2 样帧 `{k*′, k_diag}` + 记录进证据 | 失败回 T 返工并重走 H；通过才允许声明稳定候选 |
| S（停点 + 复核） | T 稳定候选声明 → Acceptance §4.3.1 停点审计 → independent Review | `PASS` 才开 C；H 失败后的返工必须重走 H→S，旧 Review 作废 |
| C（采集） | §3.5.3 P 阶段预检 → 一次正式执行（X）+ 门工件 + 证据 | 完整端点独立复核（round-8 同法） |

建议写入边界（超出即越权）：§2.2 全部列出文件、
`Assets/TetheredTracking/Tests/EditMode/`、`tests/test_scene006_probe.py`、
`docs/evidence/P1-SCENE-006-batch2-config.md`（仅 F22 行）、新 Assets
文件的 Unity 自动生成 `.meta`、`runtime/p1-scene-006/
probe-candidate-vfov40-p2/`（gitignored）、状态板。

## 8. 授权禁区零变化对照（§36 第 3 项义务）

| 禁区 | 零变化机制 | 复核核对方式 |
|---|---|---|
| 候选场景 | 场景文件哈希前后比对（沿用），须等于 batch-2 记录值 | manifest/工件 `scene_file_sha256_*` |
| 光学（40°/16 m） | 配置字节零变化 + F21 钉 | `scenario_sha256` 相等 + 钉测试 |
| 锚点/路线/车辆 | 同上（配置唯一定义源）；工厂字面量禁改 | F21 断言逐字段 + A1 |
| 模型 | 权重哈希绑定沿用（链第 1 步） | 工件 `model_identity` |
| 帧集 | 测量帧集 `M` 的 tick 字面量逐字不动、分母域不变；提示帧仍取自 T6 warmup 窗口 `[0, 10]`（§3.2.1），仅选取律收紧 | diff + 工件比对 |
| 样本下限/阈值 | `40/40`、`0.85/0.90`、`0.5/0.1` 字面量不动 | diff + 工件 `frozen_protocol` |
| Play/session/run ID | 全程 Edit Mode 离线；诊断通道无 ID；`runtime/runs/` 零新增 | 复核 grep（round-8 同法） |
| M3′ / criterion 4 / 主指标 | 相关文件不在写入边界 | `check_role_writes` + diff |

## 9. 对 §36 交接五项的逐条对照

1. 独立提案、`PROPOSED`、不重写历史 → 本文件头 + §0.1。
2. R17–R22 逐条 → §3.1（R17）、§3.2（R18）、§3.3（R19）、§3.5（R20）、
   §3.4（R21 = F20/F21/F22）、§5.4（R22）。
3. 受影响接口与精确写入边界 + 禁区零变化证明 → §2.3、§7、§8；诊断
   样帧与唯一正式执行的区分 → §3.3.1/§3.3.4 对 §3.5.3/5。
4. 旧工件只读、不进分母、不当基线、不作调参源 → §0.4、§5.7、§6.1。
5. 提交后仅交回 Acceptance；无新 `ACCEPTED` + binding clarifications
   前 Implementation 零动作 → §0.2、§3.5.5。

## 10. 本提案自身的边界声明

本提案由构思角色撰写，未修改任何代码、配置、测试、正式设计、复核或
设计审查文件；未运行任何 Unity/Python 工具产生新工件；引用的全部数字
来自已提交的既有工件与复核记录。状态转移权在 Acceptance：`ACCEPTED`
（附 binding clarifications）/ `REVISION_REQUESTED` / `REJECTED`。
若 Acceptance 对 §5.6 预注册常量、终态命名或批次划分有更严格意见，
按其 clarifications 为准；本提案预先接受"收紧不放宽"的修订方向。

---

## 11. Acceptance round 1（2026-08-04）

Decision: **`REVISION_REQUESTED`**

### 裁定理由

提案正确守住了用户授权的大边界：同一 work ID、旧 `C_b2`/灰色工件只读、
测量帧集与模型/门值不动、一次正式执行、F20–F22、COORD-005 和强制复核
停点都已进入方案；“单一视觉构造源”也是修复 F23 的正确主方向。因此本轮
不 `REJECTED`。但以下问题会让人眼门晚于协议冻结、让第二张人眼样帧根本
没有目标，或让所谓 prompt parity 继续容纳 F23 已指出的视角失配；这些都
不能留给实现角色解释，必须由 Ideation 修订正文后再审。

### Required revisions（逐条可核对）

1. **AR1 — COORD-005 必须早于稳定候选冻结与独立复核。** §3.3.1/§7
   当前次序是 `T 工具稳定候选 → Review PASS → H 人眼检查 → C 正式采集`；
   workflow §4.3.2 要求人眼保真检查发生在新渲染/采集管线“协议冻结或首次
   正式采集（先到者）之前”。一旦 T 已声明稳定候选并交独立 Review，渲染
   语义就已冻结，H 排在 Review 后不合规。修订为：实现工具与选择工件 →
   生成诊断样帧并完成人眼确认/记录 → 声明 T 稳定候选 → Acceptance 停点
   审计 → independent Review → `PASS` 后才允许唯一正式执行。人眼失败时
   回实现修复，并重新经过“诊断确认 → 同一停点 → Review”；不得沿用失败
   前的 Review，也不消耗正式执行额度。
2. **AR2 — 删除硬编码诊断 tick `275`，改为真实测量域成员的确定性选择律。**
   现有同几何 truth 边车
   `runtime/p1-scene-006/probe-candidate-vfov40/truth/frame_000275.json`
   明确给出 `frustum_visible=false`、`geometrically_visible=false`、
   `target_box_status=TARGET_NOT_VISIBLE`、`visible_sample_fraction=0.0`；它
   不是 §3.3.2 所称“测量域中位序成员”，无法承担外观检查。第二张样帧须
   从冻结 106 tick 中的真实 T1′ 测量域
   `D={k: V(s_k)=1 ∧ target_box_status=OK}` 按运行前冻结的确定性规则选取
   （例如按 tick 排序取 lower median），并把 `D`、排序、选中 tick 与
   非空 truth box 写入选择工件。该选择只用几何/truth，不得读取检测分数。
3. **AR3 — prompt parity 必须相对 T1′ 的实际测量域 `D`，不能相对 T1
   rays-off 的 540-sample 域。** 当前尺度锚点
   `t6.t1_domain_median_px=63.257…` 和 `median_offnadir(T1 域)`来自不同
   样本域，而最终 recall 分母来自 106 tick 中 `V=1` 的目标样本；二者
   不能支撑“prompt 与 probe parity”。修订时先从冻结 trace/场景对 `D`
   预运行重算 `min_side_px` 与 applied off-nadir 分布，再给出**精确、双边、
   有量纲/分位口径**的允许域及空集处分。现 `median−30°` 护栏也未关闭
   F23：若测量域中位为 `45°`，旧 prompt 的 `23.1°` 仍满足 `≥15°`；
   `2.0×M` 与 30° 不能仅凭“一个倍频程/宽护栏”称为 parity。Revision 1
   必须给出能机械拒绝该类差异的定律（可使用预注册 type-7 中央区间或另
   一套有依据的闭区间），并说明选择工件在任何 detector/embedding 运行前
   冻结；不得使用 `4/52` 的命中、IoU、cosine 或 recall 调参。
4. **AR4 — `E` 空集不得升格为场景级初始化负结果。** `E` 除 T6 的
   `V=1` 外还加入本 amendment 新设的截断/尺度/视角 parity 工程带；空集
   最多证明“当前预注册 parity 协议在 warmup `[0,10]` 无可用 prompt”，
   不能证明场景本身无法干净初始化，更不能作为终端负结果关闭依据。把
   `T1P2_PROMPT_LAW_UNSATISFIABLE` 的合法主张上限改为
   `QUALIFICATION_UNDETERMINED / PROTOCOL_PRECONDITION_UNSATISFIED`，回
   Acceptance/Ideation；任何改变场景/光学/窗口仍需新用户授权。
5. **AR5 — 把单一构造源 API 与 collider 清理语义写到可按字面实现。**
   §3.1 同时要求两个消费者“只调用工厂”，又允许调用方分别使用
   `Destroy` / `DestroyImmediate`，目前无法判断 collider 是工厂还是调用方
   所有。Revision 1 须冻结具体接口（返回哪些对象/Renderer、清理模式如何
   传入、谁移除 collider、何时设置 `hideFlags`），并保证几何/材质只有一处
   字面定义。测试须覆盖两个真实消费入口或等价的公开工厂合同，而不只是
   对工厂自身字面量做一次断言；运行时 `AddCarVisual` 的输出必须保持不变。
6. **AR6 — 消除前置/正式失败和 F21 身份钉的歧义。** (a) §3.1.4、
   §3.5.4 与 §5.4 目前把 appearance mismatch 同时写成“不耗额度的预检”
   和“正式链 1–3、已耗额度”；修订为两个具名阶段：正式调用前的外观/
   选择预检失败不耗额度，正式调用开始后的任何中止按一次执行已消耗，二者
   工件与目录状态不得混用。(b) 权重哈希不符应归为输入/环境身份失配，不能
   一律命名为 `TOOL_DEFECT`，尽管额度仍可按用户的一次执行限制消耗。
   (c) F21 的 expected config hash 必须在接受文本/测试中冻结为完整字面量
   `ec4154d1c7a945b70a8d8ed9fa1c6937552fde1a3fc88e364eb83881eb31c831`；
   测试不得运行时从当前配置自身或 gitignored manifest 读取 expected 值，
   否则配置与“期望”可一起漂移而不红。

### 本轮不改变的状态

- 用户 §36 有界范围授权继续有效，但不等于设计接受；无需再次请求同一范围。
- `QUALIFICATION_UNDETERMINED_SPEC_GAP_F23`、round-8 code `PASS`、旧
  `4/52` 的协议局部含义和 BC-B2-8 义务均不变。
- 不开放 Implementation、诊断样帧、正式 probe、配置修改或下游工作。
- Ideation 只修订本提案并逐条回应 AR1–AR6；revision 1 提交后返回
  Acceptance round 2。

---

## 12. Ideation revision 1 — 对 round 1 六条的逐条回应（2026-08-04）

六条全部接受，无抗辩项。本轮修订未运行任何工具、未产生新工件；所有
新数值锚点（`D` 的 type-7 `q05`/`q95`）推迟到实现期由冻结几何导出。

1. **AR1 接受 — 人眼门移到稳定候选冻结之前。** §3.3.1、§3.5.5、§7
   重排为"实现（含选择工件提交）→ 诊断样帧人眼确认/记录 → 稳定候选
   声明 → Acceptance 停点审计 → independent Review → 唯一正式执行"。
   人眼失败的处置（回实现、重走 H→S、失败前 Review verdict 作废、
   零额度）写入 §3.3.1、§5.4 与 §6.2。
2. **AR2 接受 — 撤回硬编码 tick 275（事实错误）。** 该 tick 既有真值
   为 `TARGET_NOT_VISIBLE`，revision 0 未核对可见性即预注册，撤回。
   §3.3.2 改为 `k_diag` = `D` 按 tick 升序的 lower median（索引
   `⌊(|D| − 1) / 2⌋`），由选择工件在渲染前给出，属 `D` 故必然可见且
   框 `OK`；选择只用几何/truth，不读检测分数。
3. **AR3 接受 — parity 重锚到 T1′ 实际测量域 `D`。** §3.2 重写：
   选择工具先从冻结 trace/场景重放出与 recall 分母同域的
   `D = {k ∈ M : V = 1 ∧ OK}` 及其 `min_side`/离轴分布；尺度带与
   离轴带 = `D` 的 type-7 `[q05, q95]` 双边闭区间（量纲、分位口径
   显式），端点确定性落数于选择工件；`2.0 × M` 倍频程与
   `median − 30°` 护栏撤销（二者不能机械拒绝 `23.1°` vs `45°` 类
   失配）；`t1_domain_median_px` 降为 P3 一致性钉。**附带设计后果
   （Ideation 按 R18 明示）**：`D` 若离轴钉死在钳位角而 warmup 结构
   性偏正（云台律下目标近点必然低离轴），"warmup-only 池 + D 锚定
   双边带"会结构性空集；故候选池扩为 `[0, 540] \ M`——测量帧集 `M`
   逐字不动、分母不变，提示帧本就是 `M` 外的一张额外渲染帧，
   `k*′ ∉ M` 不相交性质保留；revision 0"不扩池"论证撤回（§3.2.1）。
   主张定界随之更新（§3.2.8）：PASS 带 = 域内公平提示下的再探测
   能力；运行时初始化提示质量归 T6 与强制报告项，不混入本门。选择
   工具禁读旧采集目录（§3.2.2）。
   **（Round 2 更正注记：本条两点被 AR3a/AR3b 部分推翻——`D` 口径
   改为 §3.2.2 的 `D_V` 全员 `OK` 检查、禁止缩域；`[0, 540] \ M`
   扩池与"域内提示再探测"主张改写撤回，池恢复 `[0, 10]`。见 §14。）**
4. **AR4 接受 — 空集主张收窄。** §3.2.7 与 §5.4 把
   `T1P2_PROMPT_LAW_UNSATISFIABLE` 的合法主张上限改为
   `QUALIFICATION_UNDETERMINED / PROTOCOL_PRECONDITION_UNSATISFIED`，
   回 Acceptance/Ideation 重议；revision 0 的"初始化可观测性负结果"
   升格撤回；改场景/光学/窗口仍需新用户授权。
5. **AR5 接受 — 工厂 API 与清理语义冻结到可按字面实现。** §3.1.1
   给出完整公开合同（`Build` 返回体/顶/两 Renderer/两 Collider；
   工厂建体、赋色、不清理、不设 hideFlags）；collider 移除冻结为
   **消费者所有**（运行时 `Destroy`、Editor `DestroyImmediate`，各一
   处、作用于返回值）；几何/颜色字面量全库唯一。测试覆盖 = 工厂公开
   合同（raw `Build` 字面量 + collider 在场）+ rig 真实入口
   （`CreateTargetReplica` 涂色/无 collider/`DontSave`）；运行时入口
   由复核 diff 钉为"工厂调用 + 两行 `Destroy`"纯委托（AR5 允许的
   "等价公开工厂合同"路线，§3.1.3）。
6. **AR6 接受 — 三处口径修正。** (a) §3.5.3 拆分具名两阶段：预检 P
   （正式目录创建前，失败 = `T1P2_PRECHECK_FAIL_<原因>`，零额度）与
   正式执行 X（始于目录创建，任何中止 = 已消耗）；§5.4 矩阵同步。
   (b) 链 1 作废态改名 `T1P2_EXECUTION_VOID_INPUT_IDENTITY`（输入/
   环境身份失配），链 2–3 保持 `TOOL_DEFECT`；两者均耗额度、重跑需
   用户逐字授权（§3.5.4）。(c) F21 期望哈希冻结为测试源码内完整字面
   量 `ec4154d1c7a945b70a8d8ed9fa1c6937552fde1a3fc88e364eb83881eb31c831`，
   禁止运行时从配置自身或 gitignored manifest 反读（§3.4.2）。

Revision 1 完毕；状态回到 `PROPOSED`，交 Acceptance round 2。授权
禁区、只读工件、一次执行纪律与 §8/§9 的对照义务全部维持。

---

## 13. Acceptance round 2（2026-08-04）

Decision: **`REVISION_REQUESTED`**

### 裁定理由

Revision 1 已实质关闭 AR1、AR2、AR4 与 AR6：人眼门次序、诊断 tick、
空集主张、执行额度/身份归因和 F21 全哈希钉均已写到可核对程度；AR3 把
尺度与离轴带改锚实际测量几何域、撤回单边宽护栏，也是正确修订。因此本轮
不 `REJECTED`。但正文同时引入一个未经现有授权覆盖的 prompt 池与研究主张
变化，并在 AR3/AR5 留下会改变分母或根本无法按字面编译/验证的合同冲突；
Implementation 仍不得开始。

### Round-1 条款处置

| 条款 | Round 2 disposition | 理由 |
|---|---|---|
| AR1 | **CLOSED** | §3.3.1/§3.5.5/§7 已冻结 `T→H→S→C`，人眼失败回 T 并重走 H→S，零正式额度。 |
| AR2 | **CLOSED** | `k_diag` 已改为真实域的确定性 lower median，撤回不可见 tick 275，且禁止读取检测结果。 |
| AR3 | **PARTIALLY_CLOSED / OPEN** | type-7 双边带与 detector 前冻结已满足；但 `D` 的定义会缩分母，且 `[0,540] \ M` 扩池改变 T6 prompt 关系与 T1′ 主张。 |
| AR4 | **CLOSED** | E 空只到 `QUALIFICATION_UNDETERMINED / PROTOCOL_PRECONDITION_UNSATISFIED`，无场景级结论。 |
| AR5 | **OPEN** | collider 归属已清楚；精确 `Build` 声明不可按字面编译，独立回归钉与“全库唯一字面量”互相冲突，后备形态仍让实现者自行选协议。 |
| AR6 | **CLOSED** | P/X 额度边界、`INPUT_IDENTITY` 与 `TOOL_DEFECT`、F21 完整字面哈希均已消歧。 |

### Required revisions（逐条可核对）

1. **AR3a — `D` 必须与 recall 分母同一集合，禁止用 `status=OK` 静默
   缩域。** §3.2.2 当前写
   `D={k∈M: V(s_k)=1 ∧ target_box_status=OK}`，却称其“与 recall 分母
   同域”；基础 §5.6 的真实合同是**所有** `V=1` tick 构成目标分母，任一
   该成员 box 不可投影必须整份进入 `PROBE_FIDELITY_CONTRADICTION`，不是
   删除该 tick。Revision 2 须先定义
   `D_V={k∈M: V(s_k)=1}`，逐成员检查 `status=OK`；有一个不满足即在 P
   阶段 fail-closed、不得计算分位或选择 prompt。全员通过后方可令
   `D=D_V`，且选择工件必须机械断言 `|D|` 等于正式目标分母计数。§3.2、
   §3.3.2、§5.2/§5.5 与 §12 的全部“D”口径同步。
2. **AR3b — 不接受 `[0,540] \ M` 路中扩池或其改写后的研究主张。**
   现授权虽允许修订 prompt parity，却逐字冻结“帧集”；已接受设计又把
   T1′ prompt 明定为 T6 的 `k≤10` acquisition 帧。Revision 1 不只是换
   选择律，而是允许任意非测量路中帧，并把门的主张改成“给定测量域同带
   prompt 的再探测能力”，明确不再代表初始化提示。这同时触及冻结帧域、
   T6/T1′ 阶段关系和核心研究主张，不能由 Ideation/Acceptance 从“prompt
   parity”四字中自行推定授权。**在现有授权下**，Revision 2 必须把池恢复
   为 `P=[0,10]∩ℤ`，仍按已修正的 `D` 双边带选取；若 E 空，就走已经正确
   收窄的 `PROTOCOL_PRECONDITION_UNSATISFIED`，不得为避免空集扩池。
   若 Ideation 坚持路中 prompt，须先回 Acceptance，由用户另行逐字授权
   prompt 帧域和 T1′ 主张变化；在取得授权前不得把 §3.2.1/§3.2.8/§4/
   §6.2/§8 的“扩池不改帧集”当成已成立解释。
3. **AR5a — 把 `Build` 改成一份可编译的精确 C# 合同。** §3.1.1 给出的
   `public readonly struct Build` 内含六个非 `readonly` 实例字段；C#
   不允许 readonly struct 具有这种字段，Implementation 按字面执行会编译
   失败。Revision 2 必须明确选择并完整写出一种合同：例如为六字段全部加
   `readonly` 并给出构造器，或改成只有 getter 的属性；也可明确撤掉 struct
   的 `readonly`。不得只写“实现者自行采用等价形态”。
4. **AR5b — 区分“单一生产构造源”和“独立验证 oracle”，并冻结后者
   来源。** A1 要求改任一工厂颜色/尺寸/位置就让测试变红，分析器又要把
   `target_appearance` 与冻结值独立比较；这要求测试/分析器的 expected
   值不能从被测工厂或 actual manifest 自身反读。正文却要求几何/颜色
   字面量在“整个代码库只存在于工厂一处”，两者不可能同时成立。Revision 2
   须把唯一性限定为**生产构造路径**，明确允许并要求版本化测试/分析器以
   独立 expected contract 硬钉同一数值；逐项写明各比较的 expected/actual
   来源，保证改生产工厂而不改 oracle 会失败。§3.1.5 后备双构造也删除：
   本 revision 已论证程序集可达，若实现期仍发现工厂不可行，必须退回
   Acceptance，不得由 Implementation 自行切换协议。

### 本轮不改变的状态

- 用户 2026-08-04 的有界授权继续有效，但不覆盖路中 prompt 帧域或新的
  “域内提示再探测”研究主张；本轮未取得也未代录任何新授权。
- `QUALIFICATION_UNDETERMINED_SPEC_GAP_F23`、round-8 code `PASS`、旧
  `4/52` 的协议局部含义、F20–F22 与 BC-B2-8 义务均不变。
- 不更新正式设计 v0.3.14；不开放 Implementation、诊断样帧、正式 probe、
  BC-B2-8 检查或任何下游工作。
- Ideation 只提交 revision 2，逐条回应 AR3a/AR3b/AR5a/AR5b，然后返回
  Acceptance round 3。

---

## 14. Ideation revision 2 — 对 round 2 四条的逐条回应（2026-08-04）

四条全部接受，无抗辩项。本轮未运行任何工具、未产生新工件；未请求也
未预支任何新授权。

1. **AR3a 接受 — `D` 与 recall 分母同一集合，禁止缩域。** §3.2.2
   重写：先定义 `D_V = {k ∈ M : V(s_k) = 1}`（即基础 §5.6 目标分母
   集合），逐成员检查 `target_box_status = OK`；任一不满足即选择工具
   fail-closed 拒绝生成工件（P 阶段预检同检），与 §5.6 链第 3 步
   `PROBE_FIDELITY_CONTRADICTION` 同义，不删成员、不缩域。全员通过后
   `D = D_V`；选择工件与分析器**双侧**机械断言 `|D|` 等于正式目标
   分母计数。§3.2.5、§5.2 B1、§5.5 口径同步，§12 第 3 条加更正注记。
2. **AR3b 接受 — 池恢复 `[0, 10]`，扩池与主张改写撤回。** §3.2.1
   恢复 warmup 窗口为唯一 prompt 帧域；§3.2.8 恢复初始化域语义；
   §4/§5.4/§6.2/§8 中"扩池不改帧集"的全部解释清除。E 空即走已收窄的
   `PROTOCOL_PRECONDITION_UNSATISFIED`，不为避免空集扩池；此后如仍需
   路中帧域，凭选择工件逐 k 证据另行请求用户逐字授权，本提案不预支。
   结构可满足性依据（似然、非保证，§6.2）：`D` 最早成员（k = 15）与
   warmup 末段（k = 8–10）几何相邻，仅隔约 1 s。
3. **AR5a 接受 — `Build` 改为可编译精确合同。** §3.1.1 逐行写出
   `readonly struct`（全部实例字段 `readonly` + 显式构造器）；字段集
   与两个签名冻结，方法体属实现内容；不再有"等价形态由实现者采用"的
   空间。
4. **AR5b 接受 — 生产构造源与验证 oracle 分离并冻结来源。** 字面量
   唯一性收窄为**生产构造路径**；§3.1.4(a) 冻结四份版本化独立
   expected 副本（工厂合同测试、rig 入口测试、Editor 侧
   `Scene006AppearanceContract` 干跑预检块、分析器 Python 常量块）及
   每个比较点的 expected/actual 来源表，全部不得从工厂/被测物/
   manifest/配置反读；"改生产工厂而不改 oracle 必红"进入验收
   （§5.1 A1/A2）。§3.1.5 后备双构造删除——实现期若发现单一构造源
   不可行，唯一动作是退回 Acceptance 重裁。

Revision 2 完毕；状态回 `PROPOSED`，交 Acceptance round 3。授权禁区、
只读工件、一次执行纪律与 §8/§9 对照义务全部维持。

---

## 15. Acceptance round 3（2026-08-04）

Decision: **`ACCEPTED_WITH_BINDING_CLARIFICATIONS`**

### 裁定理由

Revision 2 已逐条关闭 round 2 的四项阻断：`D_V` 现在与基础 §5.6 的
`V=1` 分母严格同集并在任何分位前逐成员 fail-closed；prompt 池恢复
T6 warmup `[0,10]`，路中扩池和研究主张改写均已撤回；`Build` 的字段/
构造器合同可实现；生产构造源与独立验证 oracle 已分列，且实现者无权
退回双构造。本方案因此落在用户 2026-08-04 的有界授权内，不改变任何
冻结禁区，也不使用旧 `4/52` 调参。

剩余两处不需要再退 Ideation：§3.1.1 的无方法体分号是 API 签名记法，
不能作为 literal C# 源文件；选择工件生成期的 `D_V` 保真失败又早于
§3.5.3 的 P 阶段。下列 binding clarifications 把二者及执行次序钉死；
与正文冲突时以下条款优先，Implementation 不得自行解释。

### Round-2 条款处置

| 条款 | Round 3 disposition | 理由 |
|---|---|---|
| AR3a | **CLOSED** | `D_V={k∈M:V=1}` 先建域，成员全 `OK` 后才令 `D=D_V`；选择侧和分析侧双断言分母计数。 |
| AR3b | **CLOSED** | 唯一 prompt 池恢复 `[0,10]`；E 空 fail-closed，路中帧域须另取用户逐字授权。 |
| AR5a | **CLOSED_WITH_BC-P2-2** | 六个 readonly 字段与构造器已冻结；方法签名的文档分号由 BC 明确为非源码记法。 |
| AR5b | **CLOSED** | 单一生产构造源、四份独立 oracle、逐比较 expected/actual 来源和无后备合同均已冻结。 |

### Binding clarifications（实现角色逐条核对）

1. **BC-P2-1 — 接受范围与优先级。** 接受 revision 2 正文及 revision 1
   已由 §13 关闭的 AR1/2/4/6；§12 中被更正的 `D=V∧OK`、路中扩池及
   “域内提示再探测”文字只作历史，不得实现。若正文与本节冲突，以
   BC-P2-1–8 为准。正式设计同步为 v0.3.15；配置、场景、光学、锚点、
   路线、车辆、模型、测量/提示帧域、样本下限、阈值、Play/session/run
   ID、M3′、DETECT criterion 4 和主指标均保持冻结。
2. **BC-P2-2 — 工厂 API 的 literal 边界。** §3.1.1 中六个 readonly
   字段、显式构造器、`AddTargetVisual(Transform parent)` 的返回类型/
   参数签名和 §3.1.1–3 的构造语义均为 binding。代码块末行的分号只是
   API 记法，**不是**可复制进普通 static class 的无方法体 C#；实现必须
   提供可编译方法体，创建两块对象并返回包含六个非空实际引用的 `Build`。
   不得改成另一返回类型、恢复双构造或加入未列出的消费者差异。
3. **BC-P2-3 — 生产源与 oracle。** 生产构造字面量只在工厂一处；
   §3.1.4(a) 四份 expected 副本必须各自在其版本化测试/Editor/Python
   位置硬钉，不得引用工厂常量、被测对象、manifest 或配置。每份 oracle
   均覆盖该比较点实际使用的 mesh、TRS、RGBA 与 shader 字段；任何字段
   若无法从当前未改运行时合同确定，Implementation 必须退回 Acceptance，
   不得删字段、从 actual 反读或以人眼门替代自动检查。
4. **BC-P2-4 — `D_V` 前置保真终态。** 选择工件生成期若任一
   `D_V` 成员 `target_box_status != OK`，立即终止为
   **`T1P2_PRECHECK_FAIL_PROBE_FIDELITY_CONTRADICTION`**：零正式额度、
   不计算分位、不选择 prompt、不生成诊断帧、不声明稳定候选；输出仅限
   具名失败报告与 106-tick 逐成员证据，回 Implementation 归因。该路径
   不得混入 X 阶段的已消耗 `T1P2_EXECUTION_VOID_TOOL_DEFECT`。
5. **BC-P2-5 — E 空工件。** `D_V` 全员 `OK` 但 warmup E 空时，选择
   工件仍须生成并提交：包含 106-tick 表、`D=D_V` 与计数断言、type-7
   端点、11 个 warmup tick 的完整 E 证据，且
   `selected_tick=null`、`terminal=T1P2_PROMPT_LAW_UNSATISFIABLE`。
   此终态零额度、无诊断帧、无稳定候选、无 Review/正式执行；回
   Acceptance/Ideation，任何扩 prompt 帧域须用户新授权。
6. **BC-P2-6 — COORD-005 与稳定候选次序。** 只有 nonempty 选择工件
   已提交后才可渲染恰好两张诊断帧 `{k*′,k_diag}`；禁止 detector/
   embedding，记录路径、确认人、结论。确认通过后才可声明稳定候选；
   失败回实现并重走 H→S。稳定候选提交前不得把诊断帧本体放入正式证据
   或 ProbeDirectory，但确认记录必须已在证据文件。
7. **BC-P2-7 — 强制停点与正式额度。** T 稳定候选形成后，Acceptance
   以 `d2db9f3` 为上一通过候选运行 workflow §4.3.1 写入审计并逐路径
   归因；停点成立后交 independent Review，`PASS` 前不得创建正式目录。
   正式 P 阶段全绿后，X 以创建
   `runtime/p1-scene-006/probe-candidate-vfov40-p2/` 为额度起点，最多一次；
   X 后完整端点再交 independent Review。任何依赖结果的实现继续停止。
8. **BC-P2-8 — 身份、处分与关闭边界。** F20 自包含身份、F21 完整配置
   哈希字面量、F22 type-7/third-smallest 更正均为 T 阶段验收项。工具态
   永不自动 `PASS`；`FAIL`、两类 `INCONCLUSIVE`、两类 consumed void 和
   `AWAITING_EMBEDDING_FEASIBILITY_REVIEW` 严格按 §5.4 处分。即使最终
   T1′ 获 Acceptance PASS，也不关闭 BC-B2-8、M1、M3′ 或 DETECT
   criterion 4；SCENE-006 终端关闭仍需既有目检义务与用户授权。

### 开工与当前门态

- **仅开放 Implementation 阶段 T**：工厂、选择工具/工件、manifest/
  分析器 v3、F20–F22 与相称测试；完成 nonempty 选择工件后进入 H，不能
  直接声明稳定候选或运行正式 T1′。
- 当前资格仍为 `QUALIFICATION_UNDETERMINED_SPEC_GAP_F23`；接受的是
  重定合同，不是预签 E nonempty、代码正确、Review PASS 或 T1′ PASS。
- 旧 `C_b2`、灰帧与 `4/52` 全部只读；本轮没有新授权、运行或资源消耗。

---

## 16. Acceptance 对 Implementation 阶段 T 的裁定（2026-08-05）

Decision: **`REVISION_REQUESTED`**

### 已成立的终止归因

Implementation 提交的零额度选择工件足以证明 BC-P2-5 分支：
`D_V=D` 共 52 个 `V=1` 成员且全部 `target_box_status=OK`；type-7 带为
`min_side_px=[48.67423629760742,106.98741378784179]`、
`applied_off_nadir_deg=[43.78608341217041,45.0]`；warmup `[0,10]`
没有同时满足可见、不截断和双带的成员，故 `selected_tick=null` 与
**`T1P2_PROMPT_LAW_UNSATISFIABLE`** 的分支归因成立。

它只支持 **`QUALIFICATION_UNDETERMINED /
PROTOCOL_PRECONDITION_UNSATISFIED`**：不是场景负结果，不消耗正式额度，
不允许诊断帧、稳定候选、独立 Review 或正式 ProbeDirectory。不得扩展
prompt 帧域；若要改变 `[0,10]`，仍须用户新的逐字授权和新的
Ideation/Acceptance amendment。

阶段 T 本批仍不能接受：Unity EditMode 为 240/243，且选择工件含 JSON
标准禁止的裸 `NaN`；测试辅助还把相关用例中的全部 error 日志一并忽略。
下列条款是同一既有范围内的有界返工，不开放 H、S、Review 或 X。

### Binding clarifications（返工时逐条核对）

9. **BC-P2-9 — RGBA 只容纳 Unity 色彩表示往返误差。** 选择选项 B；
   选项 A 拒绝。四份独立 oracle 的 expected 仍分别硬钉作者合同
   `(0.9,0.12,0.1,1)` 与 `(0.65,0.08,0.07,1)`，不得改写为从 actual
   读回的数值。仅 RGBA 四分量采用逐分量绝对误差 `<=1e-6`；不得使用
   相对容差、舍入、actual 派生 expected 或复合范数。mesh、shader、
   TRS、角色、数量及其余字段维持既有精确合同。测试须证明当前 Unity
   往返误差通过，并证明任一颜色分量偏差 `>1e-6` 必失败。该数值只是
   Unity sRGB/linear 表示边界的测试容差，不修改任何实验样本下限、
   detector/embedding 门、T1–T6 阈值或主指标。
10. **BC-P2-10 — 选择工件必须是标准 JSON。** 版本化 `.json` 不得包含
    `NaN`、`Infinity` 或 `-Infinity`。不可用的数值字段在序列化边界写为
    JSON `null`，并由既有 `visible`/status 字段说明不适用；不得用有限
    哨兵伪装成测量值。Unity writer、Python reader 与测试同步该合同，
    重新生成选择工件，并增加严格 RFC 8259 parser 回归。内部计算是否
    使用 NaN 不属于本条；提交的证据边界必须可由严格解析器读取。
11. **BC-P2-11 — 不得全局吞掉测试 error。** 删除
    `LogAssert.ignoreFailingMessages=true` 这类整用例豁免；只可逐条期待
    已知的 Edit Mode `renderer.material` 实例化消息，且任何额外 error
    仍使测试失败。覆盖工厂、rig、Editor 预检及三个既有消费者测试。

### 返回条件

Implementation 只修 BC-P2-9–11，重新生成同一零额度选择工件并重跑完整
Unity/Python 证据；已知 Python F3 口径不变。返回时须给出严格 JSON 解析
通过、Unity 全绿、颜色越界 mutation 变红及额外 error 未被吞掉的证据。
仍不得渲染诊断帧、声明稳定候选、打开独立 Review、创建正式目录或改变
任何冻结禁区；正式额度保持未消耗。Acceptance 随后只确认返工与上述终止
处分，不把该分支交 Review。

---

## 17. Acceptance 对阶段 T 返工的确认（2026-08-05）

Decision: **`ACCEPTED`**

### 核对结论

1. **BC-P2-9 CLOSED。** 四份 oracle 仍各自硬钉作者 RGBA；`1e-6` 仅用于
   RGBA 逐分量绝对误差，TRS/mesh/shader/role/count 仍精确。界内与界外
   mutation 均覆盖，未改任何研究门、样本下限、T1–T6 阈值或主指标。
2. **BC-P2-10 CLOSED。** 提交工件的 57 个裸 `NaN` 已全部成为 JSON
   `null`，其余数值、`D=52`、两条带、`k_diag=400` 与 11 行 E 证据不变。
   Ruby 严格解析、项目 strict reader、Unity 往返和 Python 回归均通过；
   v1/v2 旧工件只读保留，没有被改写。
3. **BC-P2-11 CLOSED。** `ignoreFailingMessages` 已从相关测试路径删除；
   每块 cube 的既知 Edit Mode 材质消息用具名 `LogAssert.Expect` 逐条计数，
   其他 error 仍由 Unity Test Framework 按默认规则判失败。
4. **范围与复验通过。** `07e2623..30294d0` 的 implementation role-write
   审计通过；Unity XML 为 246/246，Acceptance 复跑 focused Python 26/26、
   full Python 339 项仅既有 F3；`git diff --check` 通过。没有诊断帧、稳定
   候选、Review、正式 ProbeDirectory 或额度消耗。

### 终止处分

阶段 T 返工接受，但接受对象不是稳定候选或独立复核 verdict。BC-P2-5
终态最终确认为 **`T1P2_PROMPT_LAW_UNSATISFIABLE`**，资格仍是
**`QUALIFICATION_UNDETERMINED / PROTOCOL_PRECONDITION_UNSATISFIED`**。
本分支到此停止，不进入 H/S/Review/X，也不产生 `UNITY_NA` 主张。

继续 P1-SCENE-006 已无现授权内路径：维持 warmup `[0,10]` 就只能保留该
终态；若要扩 prompt 帧域，必须先取得用户新的逐字授权，再由 Ideation
提交 amendment 并经 Acceptance 接受。现有裁定不预支该授权，也不改变
配置、场景、光学、锚点、路线、车辆、模型、测量帧集、样本下限、阈值、
Play/session/run ID、M3′、DETECT criterion 4、BC-B2-8 或主指标。

---

## 18. User disposition 与关闭边界（2026-08-05）

User decision: **`PRESERVE_AND_CLOSE_REDIRECTION`**

用户逐字回复“保留并关闭，下一步是交给review？”。依 §17 给出的二选一，
该决定保留空 E 工件并把本次 T1′ parity-redirection 分支关闭为
**`CLOSED_PROTOCOL_PRECONDITION_UNSATISFIED`**；不授权扩大 prompt 帧域。

**下一步不是 Review。** BC-P2-5 要求本终态停在 H/S/Review/X 之前，且
§17 接受的返工不是稳定候选。把它交 Review 会违反已接受执行次序，也不会
把协议前置不满足变成场景资格结论。

本分支关闭不等于整个 `P1-SCENE-006` work item 已关闭。BC-B2-8 仍明确要求
用户完成新配置下五辆落点与场景合理性的非 Play Unity 视觉检查；本提案从未
豁免该前置，用户本句也未逐字豁免。故整个 work item 当前为
**`BLOCKED_BC_B2_8_VISUAL_CONFIRMATION`**。目检 PASS 后由 Acceptance 使用
本节已取得的关闭授权完成最终收束；失败则如实保留并归因，不回到本分支调参。

---

## 19. Acceptance final closure（2026-08-05）

Disposition: **`CLOSED_PROTOCOL_PRECONDITION_UNSATISFIED`**

用户 `UT-P1-SCENE-006-001` Attempt 1 在 HEAD `1c990b4` 完成 BC-B2-8
非 Play 视觉检查并报告 **PASS**：五辆冻结迁移车辆均在道路上，无明显建筑/
道具/车辆重叠，无可见悬浮或下沉，朝向合理；五点整体场景合理性 PASS。
检查后选择 Don't Save，版本化场景字节不变；没有新增 session/run ID，P2
正式 probe 目录从未创建，额度保持未消耗。

因此 §18 的用户关闭授权与 BC-B2-8 前置均已满足，整个 `P1-SCENE-006`
work item 以空 E 协议前置不满足终态关闭。该 disposition 不是 `DONE`、不是
场景资格 PASS/FAIL、不是 `UNITY_NA`，也不新增独立 Review；旧 round 8 只
覆盖其原候选。`4/52` 仍只作灰色 probe 的协议局部历史，M1、M3′、DETECT
criterion 4、BC-M34-4(b) 和主指标不因本关闭而成立或改变。
