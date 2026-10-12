# P1-VLM-DATA-001 独立复核

Work ID: `P1-VLM-DATA-001`（G0 目录门 + D0 数据引擎，charter batch）
复核角色：review（最强池，新鲜上下文；历史名 Claude Sonnet）
设计合同：`docs/proposals/P1-VLM-DATA-001-grounding-data-foundation.md`
revision 2 + BC-DATA-1…12（round 3/4/5/6）；设计 v0.3.22。

---

## Round 1 — 2026-08-26

### 0. 候选、开轮资格与方法

- **候选**：`57e7af21e5afc5246a016750d910d6913d66cc3c`（返工候选 3，接受轮 7
  确认停点）。HEAD `c54077f67b7b6c863d0906f731fdc527a448e452` 相对候选为纯
  文档提交（PLAY_GOVERNING diff 0 行，本轮实测）。
- **开轮资格（COORD-007 R1）**：本 work ID 首个复核轮，复核文件无历史机读
  通过指针；复核范围 = 整个工作项生产 diff `f372e2c..57e7af2`，PLAY_GOVERNING
  集合上 31 个全新文件、9,852 行（`tools/dist_data/` 14 模块 5,540 行 +
  `tests/test_dist_data_*.py` 17 文件 4,312 行），非空，开轮成立。
  `controller/`、`Assets/`、`config/`、`ProjectSettings/`、
  `Packages/packages-lock.json` 在该区间零改动（实测）。
- **方法**：一次性复核副本 `git worktree add --detach … 57e7af2`。全部 14 个
  生产模块通读；17 个测试文件读 7 个全文（round4/5/6、pipeline、layout）+
  其余按用例清单核对；行为疑点写探针（P1–P6，均在副本内，收工随副本删除）。
  真实归档只读核查用副本代码 `--repo-root` 指向主树（主树代码与候选字节相同，
  实测 `git diff 57e7af2..HEAD -- tools/ tests/` 为空、工作树干净）。
- **测试树哈希**：候选 tree `4e3385c309a2b886e34ab3f8718f01524d981473`；
  17 个 focused 测试文件串接 SHA-256
  `bf13c5acddaeed28f6ec86f174b25b3e3d654158907aa79cd08ab34aac853a28`。

### 1. 复核自跑的证据（不信报告数字，全部重跑）

| 项 | 实测 | 与声明比对 |
|---|---|---|
| focused（副本，无归档数据） | python3 3.14.6：342 ran，OK，**19 skipped**（真实归档类用例自动跳过）；.venv-yoloe 3.12.13 同 | 声明的 342/342 零 skip 只能在有归档的树上成立 |
| focused（主树 = 候选同字节） | python3 3.14.6：**342/342 OK 零 skip**；.venv-yoloe 3.12.13：**342/342 OK 零 skip** | ✓ 与实现者/接受轮 7 一致 |
| 只读 dry-run（副本代码 + 主树归档） | 记录 **29,923**（图像 24,154、真值 5,769），lineage 组 **19,754**，zero-match = **0**，multi-match = **0**；INCLUDED 29,262 / INVENTORY_ONLY 426 / EXCLUDED_DERIVED 77 / EXCLUDED_DIAGNOSTIC_CHANNEL 128 / EXCLUDED_UNRELEASED 30；`runtime/dist-data/` 运行前后均不存在 | ✓ 全部逐字复现 §10.4 |
| §8.6 六计数 | 探针 jpg 107 / 107、`init-box-preview.jpg` 1、rs3 同目录 `frame_*.jpg` 173、arm-A 有效 truth 恰 5 份、void run truth 恰 1 份（`runtime/runs/*/m3_body_truth.jsonl` 全列直查） | ✓ |
| 修复前 9/16（§18.3 (c)） | 副本内把 `bind_layout.py` 回退到 `38cc7bb` 后 round6 实测 **9/16 红**（6 failures + 3 errors；BC-DATA-10 两条、-11 两条、-12 两条失败 + `FORBIDDEN_SNAPSHOT_PATHS`/`is_allowed_embedded_snapshot` 三条 AttributeError），恢复后副本干净 | ✓ 按对应缺口失败 |
| 基础几何 | `docs/evidence/P1-M3-BODY-001-scene-geometry.json` SHA-256 = `77834bd3…ef9c13`，与 S0 钉死值相同；779 实例 / 101 车辆 | ✓ |
| 真实 phantom | default 恰 6 条 relocation、恰 3 条 removal；scene-004 三代理独立复算 `6.32×6.76×2.20` / `9.09×9.09×4.16` / `6.32×6.32×2.32` m | ✓ 与 §10.4 一致 |
| G0 报告数字复算 | **不适用**：本批次未产出任何 G0 数字（按实现者证据 §6 要求如实记为不适用，不是通过） | — |

逐条核对结论（workflow §4.4 清单内、未列为 finding 的部分）：S0 冻结常量与
§2.1–§2.7/§2.11/§5 逐字一致（9 类映射、色带、θ_occ=0.5、12 px/0.25、站位
分箱、pHash 参数、留出公式合计 32、F1–F4 冻结值、A1/A2/A3 整数配额）；
create-once 字节幂等 / supersession 留档 / DAG 禁行边（同阶段允许、S7 读 S8
硬错误）实现正确；BC-DATA-6/-7 的根闭集补正、BC-DATA-9 的冲突矩阵与 ref
禁令、BC-DATA-10/-11/-12 的三条硬失败均已按裁定落地并有按缺口失败的具名
回归；近平面 12 棱裁剪几何正确；切分全枚举向量、dev 前缀、连带规则、三层
泄漏断言、审计三 panel 生成即互斥与 9-attempt 状态机均符合 BC-DATA-2/-5；
verifier 纯函数判据与夹具覆盖 §2.11 点名两类。工具包不被
`controller/`/`Assets/` import，`runtime/dist-data` 在 `.gitignore` 的
`/runtime/*` 规则内。角色边界：区间内 6 个 commit 逐个核对，实现批次只写
tools/tests/状态板/自身证据，接受批次只写文档（账本条目由接受轮 5 写入），
无越权。

### 2. Findings（逐条分级；CLASS_1/2 → REWORK_REQUIRED）

#### F1（CLASS_1）场景绑定语义在真实归档上使 6/9 族全部 `EXCLUDED_UNBOUND_SCENARIO`，G0 的确定结论被绑定方案本身翻转

用候选自己的 `build_inventory + bind_layout.bind_families`（只读）跑真实
归档，逐族结果：

| 族 | 布局 | 绑定 | INCLUDED 图像帧 | 失败方式 |
|---|---|---|---|---|
| detect-scout1 | default | **BOUND**（sha `68170d80…`） | 768 | exchange 目录内嵌 `scenario_config.json` |
| scene-val | default | **BOUND**（sha `f6005eb4…`） | 256 | 归档内嵌 config |
| m3-armA | default | UNBOUND | 996 | 全帧 `no_scenario_binding` |
| m3-armB | default | UNBOUND | 640 | 同上 |
| rate | default | UNBOUND | 5,197 | 两套不同 sha（1,335 帧 vs 3,546 帧）+ 316 帧无绑定 |
| s004-scout | scene-004 | UNBOUND | 4,836 | 全帧 `no_scenario_binding` |
| s004-qual | scene-004 | UNBOUND | 7,952 | 同上 |
| s004-smoke | scene-004 | UNBOUND | 3,061 | 同上 |

23,706 个 INCLUDED 图像帧中仅 1,024（4.3%）落在可绑定族；**scene-004 布局类
零绑定族**，两大 floor 来源（scout-4 2,405、qual-3 hold 4,096）与全部 m3
有效帧全数退出。F2 全局 ≥40 / F3 train∪dev ≥60 在剩余两族上算术不可达，
G0 的确定结论 = 因**绑定方案**而非数据不足的 `INSUFFICIENT`。

**根因是设计自身的内在矛盾，代码忠实实现了后者**：BC-DATA-8.8（接受轮 4
冻结）把解析定为「**逐帧向上**取最近内嵌快照，缺失才取最近 manifest」，
`resolve_frame_scenario` 照此只搜帧的祖先目录；但 §2.3 第 2 步的原文示例是
「**族内**归档 manifest（如 scouting session manifest）」，A.2 表头明写
「字节提供者 = `runtime/scenario_config.p1-scene-004.hold.json`，manifest
sha `00c8802a…` 匹配」。实测：族内 manifest/快照**全部存在且哈希全部吻合**
——m3 run 目录有 `scenario.json` 与 `manifest.json`（`scenario_config_sha256
= f9c92052…` = `config/scenario.default.json` 字节 sha）；scout-4 与 scout-3
的族 manifest 声明 `00c8802aaacf…` = hold provider 字节 sha——只是它们全部
位于帧的**非祖先**子树（m3 帧在 post-run 归档、六成员内无快照；scout-4
exchange 只有 frames+metrics；scout-3 manifest 在旁支 `session/`；qual-3 与
各根级 hold 为平铺目录）。祖先搜索按构造永远够不着。

附带两条同源事实：(a) m3-void 与 B3 残留 hold 并入 m3 族，其根级 hold 目录
在任何逐帧方案下都无绑定路径，按「族内不唯一/不全 BOUND 即整族退出」的
现行聚合，m3 族即使修好 manifest 侧也仍整族退出；(b) A.1 把全部 rate 归档折
为单一「rate」族，而其内部至少两套不同 scenario 字节——与 §2.5 复制族定义
（以 scenario 字节 sha 为键）冲突，该族在字节唯一性条款下永不可绑定。

**归因与闭合**：代码与 BC-DATA-8.8 字面一致，故不是单纯实现缺陷；但候选交
停点时这一**当天即可零成本测得**的确定输出从未被测量或披露（实现者证据
§4-1 仍停留在「S1 硬错误停机所以 S2 未跑」的第一候选时态），§5.2 的
at-risk 算术全部以这些族计入 floor 为前提。按 R1/R2 先例（「改变确定输出，
不能以正式工件尚未授权降格」）列为阻断。闭合需要：接受角色先裁定绑定语义
（恢复 §2.3 族级解析、或修订 A 表/BC-DATA-8.8 并处置 (a)(b)），实现按裁定
落地；绑定具名回归（真实归档只读 fixture）：
`test_scout4_family_binds_via_family_manifest`、
`test_m3_armA_family_binds_via_run_snapshot`——按当前代码必失败（今日实测
UNBOUND），修复后必须 BOUND 且 sha 分别为 `00c8802a…`/`f9c92052…`。

#### F2（CLASS_2）§2.4 的遮挡全集与唯一性域在交付组件上不可同时成立；非车辆进入执行域后通配冲突灭掉全部唯一性

§2.4 要求：遮挡体 = 该布局类**全部 779 实例**（nature/prop 的过包围还是已
注册风险）；而唯一性域 blocking(f) = visible>0 的**目录（车辆）对象** ∪
phantom ∪ 目标代理，referable(f) = 状态 OK 的目录对象。交付的
`build_catalog.build_frame_entry` 把 referable/blocking 直接从传入的同一份
`layout_bodies` 投影结果聚合，无任何目录限定；`frame_world` 对无字段记录或
非车辆对象给出 `class_word=None`，而 `_noun_conflicts` 把 None 当通配。副本
内探针（P1）：两辆车 + 一栋可见建筑 →
`execute({'target':{'class':'taxi'}})` 命中 `['Building Sky_big_color01',
'Vehicle_Taxi']`、`unique=False`，`minimal_program` 对孤例 taxi 也返回
None；建筑同时进入了 blocking 列表（合同禁止），若建筑状态为 OK 还会进入
referable/exposure。真实布局 678 个非车辆实例几乎逐帧可见 ⇒ 全量唯一性
湮灭、F3/F4 → 0。反向组合（只传车辆）则丢失建筑遮挡（探针 P2：同一几何去
掉建筑后无任何遮挡判定）→ false-INCLUDE 方向 fail-open。管线测试的合成
世界只有车辆，两难从未被测试触达。闭合绑定具名回归：混合世界 fixture 断言
(a) 非车辆不入 blocking/referable/exposure，(b) 孤例车辆 class-only 唯一不
受建筑影响，(c) 建筑仍参与遮挡判定——按当前代码 (a)(b) 必失败。

#### F3（CLASS_2）ref 名词可解析到颜色 `UNVERIFIED` 的对象：未验证颜色写进表达文本，违反「词表 = 已验证字段闭包」

`_resolve_ref` 只要求「冲突集恰一 + referable」，不要求已验证字段匹配。
探针 P3/P4（副本内实测）：域 = {UNVERIFIED 颜色的 car、已验证 blue 的
car、两辆 taxi}——`_resolve_ref({'class':'car','color':'red'})` 返回那辆
UNVERIFIED car；`_unique_reference_specs` 把同一辆车枚举成 black/brown/
gray/green/orange/purple/red/white/yellow **九种颜色**的「唯一」ref；
`minimal_program` 实际产出 `the taxi nearest to the black car`——black 只是
字母序第一，该车是不是黑的无人验证过。§2.6 明令「`UNVERIFIED` 对象退出
一切颜色表达（词表 = 已验证字段闭包）」；本包自己的 verifier 夹具
`ontology_unverified_ref_color` 也把未验证 ref 颜色定为
`REJECT(ONTOLOGY_VIOLATION)`，而生成侧 `execute`/`render` 调
`validate_program` 时从不传 `verified_colors`——生成器会产出自家验证器都
拒绝的表达，且 A3 零假唯一审计将按此必然失败。通配对象继续阻断唯一性
（分母不变）是对的；错的是它能**被选中**为带颜色词的 ref。闭合绑定具名
回归：上述域下 `_resolve_ref('red car')` 必须返回 None、
`_unique_reference_specs` 不得含未在该 referent 上验证的颜色词——按当前
代码必失败。

#### F4（CLASS_2）留出物体禁令只封 target 侧：ref 解析到留出对象的表达仍进训练文本

§2.5：留出物体「永不作训练指称目标、**永不出现在任何训练表达文本中**
（生成器机械封禁其 id 与其唯一化所需的属性组合）」。
`gen_mother_templates.build_template_expressions` 只在
`triple["held_out_object"]`（target 侧）时硬错误；
`make_splits.assert_held_out_never_referenced` 同样只查 candidate 的
`object_id`。关系程序 `the taxi nearest to the blue bus` 中 ref 唯一解析到
留出的 blue bus 时，没有任何检查点；冻结候选记录也**不存**每程序的 ref
解析对象，S8 无从执行该封禁。闭合绑定具名回归：ref 解析到留出对象的
train 侧候选必须被模板生成拒绝（当前必失败）；实现侧需在冻结外延中携带
ref 解析结果或等价机制。

#### F5（CLASS_2）bind_layout 两处潜伏 fail-open（与 BC-DATA-10/11/12 同标准：今日未触发不等于合同被满足）

(a) **逆施 removal 的邻居误匹配吞掉 phantom**：`unadjusted_base` 用
`_unique_match`（T_match = 条目容差 + 类内 XZ 半对角线最大值）判定被移除
实例「是否在基础几何中」；同 prefab 邻居落进 T_match 时被当成该实例 →
静默跳过 phantom 登记（探针 P5：邻居距原位 2.0 m < T_match 2.736 m ⇒
候选清单为空）。§2.3 (a) 的登记义务被邻居几何绕过，方向 = 少一个冲突/
遮挡体，fail-open。今日归档实测未触发（default 恰 3 removal → 恰 3 候选），
纯潜伏。闭合绑定具名回归：上述 fixture 下必须仍产出 phantom 候选或硬错误
（当前必失败——现返回空且不报错）。
(b) **default 分歧时 scene-004 仍从任意首个文档推导**：`build_layout` 在
做「default 各族 relocations 唯一」检查之前，就取**第一个** BOUND default
族的文档做逆施前提；分歧时 default 判 UNBOUND，但 scene-004 照常 BOUND 且
其几何取决于族的字典序（探针 P6 实测：default =
`EXCLUDED_UNBOUND_SCENARIO`「同一布局类的族解析出不同 relocations」，
scene-004 = BOUND 779 实例，前提取了先到的空 relocations 文档）。§2.3 的
逆施前提未证时应整体硬失败。今日归档 default 侧 bound 族仅两个且
relocations 字节一致（实测 distinct = 1），纯潜伏。闭合绑定具名回归：
分歧 fixture 下 build_layout 必须硬错误或使 scene-004 一并 UNBOUND
（当前必失败）。

#### F6（CLASS_2）S7 冻结对连带退出帧上的候选直接崩溃，冻结外延无法表示

`freeze_mother_candidates` 对 split 缺失的候选抛 GateError。连带规则把
test/D3 原子的非 floor 帧整体 drop（不入任何 split），而这些帧（
`PROTOCOL_INVALID`/`SMOKE` 等）按谓词定义仍产生 mother 候选（usage ∈
MOTHER 类、谓词不含 split 条件）。真实归档中 rate/qual 族必然混含此类帧，
其原子一旦被指派到 test（全枚举结果之一），S7 在真实数据上硬崩溃，
「谓词全外延连同标记冻结」（§2.4/BC-DATA-1）无法达成。管线测试全部
VALID_FORMAL，未覆盖。闭合绑定具名回归：含 dropped 帧候选的 fixture 下
freeze 必须以显式标记（如 `split: dropped`）冻结而非抛错（当前必失败）。

#### F7（CLASS_2）`splits` 工件缺 §2.5/BC-DATA-2 点名的成员：exposure 矩阵与逐 sample 角色记录

BC-DATA-2：「`splits` 须保存每个 `(frame_id, object_id)` 在四集的
{referent, distractor, absent} 角色，再汇总成逐对象 × 四集 exposure 表…
不能省略…逐 sample 记录」；§2.5 产物清单同样点名 exposure 矩阵随 splits
冻结。`assign_splits` 的载荷只有 atom/family/frames/dropped/泄漏断言；
`exposure_matrix` 是独立函数、其结果只进 G0 报告，且无任何辅助函数从
catalog entries 组装逐 sample 角色。管线测试将 `assign_splits` 载荷直接落
为 splits 工件（缺该成员）并以 `exposure_matrix([])` 空表交报告。闭合绑定
具名回归：splits 载荷必须含逐 sample 角色与 exposure 汇总（当前必失败）。

#### F8（CLASS_2）审计样本 key 公式与 §2.7 冻结字面不一致（多插一个 `/` 分隔符）

§2.7：「panel-p 的样本 key = SHA-256(`P1-VLM-DATA-001/audit/<A#>/panel-<p>`
‖ 样本 id)」——无分隔符；对照 §2.5 的两处公式都显式写出 `‖ "/" ‖`，可见
省略即无。`audit_tool.sample_sort_key` 实为
SHA-256(seed + "/" + sample_id)。两种 key 的 panel 归属不同 ⇒ 工具行为随
文字不同（R3-4 词表序/升序分歧的同种问题）。尚无任何 panel 生成，零作废
对象。闭合：接受角色裁定采用哪个公式（修文字或修代码），并绑定钉死该
公式的具名回归（对已知样本集断言逐 panel 成员）。

#### F9（CLASS_2）冻结词「距离」在三处被静默确定为相机系 z 深度，未走 R 项裁定

§2.4「按相机系 AABB 中心**距离**升序为画家序」、§2.6「取…**距离最近**的
K=5 帧」、§2.7 A1/A2 分层「**距离**三分位」——实现三处均用
`to_camera_space(center)[2]`（前向深度），非字面的欧氏距离。宽 AABB 大幅
偏轴时两种序可不同（nature/prop 巨大 AABB 恰是已注册风险场景），遮挡判定
与颜色采样帧选择随之改变。这是 R3 类实现期确定化，但未像 R3-1…10 那样
返回接受角色裁定。闭合：接受角色裁定语义（z 或欧氏），绑定钉死该语义的
具名回归（构造 z 序与欧氏序相反的两体 fixture）。

#### F10（CLASS_2）S8 `cluster_statistics` 的「unit_count」不是 §5.1 单位；station_key 未随三元组物化

§2.9「统计按簇报告：样本量、单元数、簇数按 §5 单位分层输出」。
`cluster_statistics` 的 `unit_count` = distinct `(object_id, frame_id)`，
而 §5.1 属性唯一单元 = `(对象, 站位簇)`；且 `materialize_mother_set` 复制
字段清单不含 `station_key`，S8 工件内根本无法算出正确单位。帧数 ≫ 站位簇
数，该字段一旦入正式 D0 工件即是系统性虚高的「单元数」。闭合绑定具名
回归：S8 统计的单元口径必须等于 §5.1 定义（当前必失败）。

### 3. CLASS_3（不阻断；逐字替换补丁，交接受角色复判后应用）

- **C3-1** `docs/evidence/P1-VLM-DATA-001-implementation.md` §6 首段：
  将「共 **8,731** 行（生产 5,365 / 测试 3,366，含空行与注释）」替换为
  「共 **9,852** 行（生产 5,540 / 测试 4,312，含空行与注释；第三候选
  `57e7af2` 实测）」。（第一候选旧数，未随三轮返工更新。）
- **C3-2** 同文件 §4-1：将「**未在真实归档上跑通任何一个阶段**：S1 在真实
  归档上按合同硬错误停机（§3），S2–S8 因此也未在真实数据上运行过。」替换为
  「**未在真实归档上运行任何正式阶段**：第一候选时 S1 曾按合同硬错误停机
  （§3）；BC-DATA-6/-7 后 S1 只读 dry-run 已通过（§8.4/§10.4），S2–S8 仍未
  在真实数据上正式运行。」（已执行步骤的时态；现行文字与 §8.4 自相矛盾。）

### 4. 观察项（不分级，不阻断，随返工顺带处置即可）

- `tools/dist_data/__init__.py` docstring 引用不存在的 `stages.py`（阶段表
  实在 `artifacts.py` 的 `STAGES`）。代码内注释，复核不出补丁，随返工修正。
- `AuditStateMachine.note_catalog_supersession` 的升级信号用了闭集外标签
  `AUDIT_ESCALATE_TO_USER`（`contract.AUDIT_TERMINALS` 只有两员）；语义符合
  §2.7「上交用户」，建议纳入闭集或改名说明其非终态。
- `ArtifactStore.write` 非原子写盘：进程中断可能留下半写文件，重跑将以
  CreateOnceError/JSON 解析错误 fail-closed 停机（不静默、方向正确），但
  该状态只能靠 supersession 走出，宜在运维说明中写明。
- `atom_id` 连接符取单空格（合同未定连接方式）；族 id 无空格，无碰撞风险。
- `_manifest_scenario_sha` 对携带多个互异 `scenario_config_sha256` 的
  manifest 返回 None 并继续向上搜——歧义 manifest 被跳过而非 fail-closed；
  今日归档无此形态。
- m3 truth 行若同时缺 `truth_box_available` 与两可见性字段（畸形行），
  `target_blocker_from_truth` 按「不在视野」处理（fail-open on corruption）；
  实测 v2 行字段齐全，纯假设性。F1 返工触及该函数时宜一并收紧。
- `route_sweep_rects` 把折线首尾闭合成环；本项目路线为闭环，语义正确；
  若未来出现开放路线则多算一段（保守方向）。

### 5. `UNITY_NA` 分类：**附议**

本批次 PLAY_GOVERNING 变更仅 `tools/dist_data/` 与
`tests/test_dist_data_*.py`（实测 `f372e2c..57e7af2` 区间）；
`controller/`、`Assets/`、`config/`、运行时协议零改动，工具包不被运行时
import，唯一盘上副作用目录 `runtime/dist-data/` 本轮不存在。**复核附议
`UNITY_NA` 分类**（纯离线数据工具，不影响 Unity 运行行为）。该附议只解决
Unity 列的分类资格；work item 的关闭仍以全部阻断 finding 闭合为前提，且
若未来返工越出上述纯离线范围须重新取得附议。

### 6. Verdict

**`REWORK_REQUIRED`**（round 1，候选
`57e7af21e5afc5246a016750d910d6913d66cc3c`）。

- 阻断：F1（CLASS_1）+ F2–F10（CLASS_2），每条已绑定修复前必失败的具名
  回归；F1/F8/F9 的闭合含接受角色的设计侧裁定（代码与 BC-DATA-8.8 字面
  一致，矛盾在合同内部），其余为实现侧修复。
- 本轮为 `REWORK_REQUIRED`，按 COORD-007 R7 不写机读通过指针行。
- 修复批次是否开新复核轮由 workflow §4.4 开轮资格（PLAY_GOVERNING diff
  非空）决定；F1–F10 的闭合走 §4.4 回归测试通道。
- 边界自查：本会话未修改主工作树任何实现文件；探针 P1–P6 只存在于一次性
  复核副本，随 `git worktree remove --force` 一并删除。

---

## Round 2 — 2026-08-27

### 0. 候选、开轮资格与方法

- **候选**：`3a7dff6`（返工候选 4 + 自查修复批，接受轮 9 确认停点）。其后
  `7f9d4f2`（实现侧文档更正，白名单内：`docs/roles/implementation.md` 明文
  含里程碑证据同步）与 `422e399`（接受轮 9）相对候选 PLAY_GOVERNING diff
  为 0（实测）；主树代码与候选字节相同、工作树干净（实测）。
  候选 tree `a64014adc1b0a03d97d217e6fce993c0407474cb`。
- **开轮资格（COORD-007 R1）**：复核文件无机读通过指针（round 1 为
  `REWORK_REQUIRED`）；复核范围 = round 1 候选之后的全部 PLAY_GOVERNING
  diff `57e7af2..3a7dff6`——恰 8 个 `tools/dist_data/` 文件 + 2 个新测试
  文件，1,415 insertions / 158 deletions（实测，与接受轮 9 声明一致），
  非空，开轮成立。`controller/`、`Assets/`、`config/`、`ProjectSettings/`、
  `Packages/packages-lock.json` 零改动（实测）。
- **方法**：一次性复核副本 `git worktree add --detach … 3a7dff6`。净 diff
  逐 hunk 读完；重写的 `bind_layout.py` 与两份新测试文件（round8 24 例、
  round8_followup 14 例）全文重读；受影响生产路径（`roots` 增量、
  `build_catalog` 语言域/目标证据/ref 冻结、`make_splits` 装配器与断言、
  `g0_report` 冻结、`gen_mother_templates`、`tier1_lang` 双判据）逐条对
  BC-DATA-13…19 核。真实归档核查用与候选字节相同的主树代码只读运行；
  修复前红灯在副本内检出 `5735838`/`cc4f53a` 的 `tools/dist_data/` 复现。
  区间 5 个 commit 逐个核对角色边界（实现批次只写 tools/tests/状态板/自身
  证据与白名单内的里程碑同步；接受批次只写文档；CLASS_3 由接受轮 8 应用），
  无越权。
- **测试树哈希**：17+2 个 focused 测试文件串接 SHA-256
  `a1ec6d13695d5ff2f95c4a73597a4bc9a805f5a6efe858639572aa37361d237d`。

### 1. 复核自跑的证据（不信报告数字，全部重跑）

| 项 | 实测 | 与声明比对 |
|---|---|---|
| focused（副本，无归档） | 双解释器均 380 ran OK，27 skipped（归档类自动跳过） | — |
| focused（主树 = 候选同字节） | python3 3.14.6 **380/380 OK 零 skip**；.venv-yoloe 3.12.13 **380/380 OK 零 skip** | ✓ 接受轮 9 |
| 全套（钉死解释器） | **Ran 915**，FAILED (failures=1, errors=1, skipped=1)，恰为既有两项 CSRT/opencv-contrib | ✓ |
| S1（生产 `build_inventory`，只读） | 29,923（图像 24,154、真值 5,769），lineage 19,754，zero-match 0，multi-match 0；INCLUDED 29,262 / INVENTORY_ONLY 426 / 77 / 128 / 30 | ✓ 逐项 |
| S2 全链（生产函数内存注入，镜像 `build_layout` 函数体，零工件） | **9/9 partition BOUND**，逐 partition 帧数与证据 §11.7 表逐行相同（896/640/768/256/1594/3546/4836/7952/3061），每个 779 实例；premise = `config/scenario.default.json`（`f9c92052…`，**12 条同字节副本**）；phantom 0/3 分布，三代理尺寸 = round 1 复算值（6.32×6.76×2.20 / 9.09×9.09×4.16 / 6.32×6.32×2.32 m）；绑定 **23,549/23,706 = 99.3%**；`runtime/dist-data/` 前后不存在 | ✓ 逐项 |
| 157 个未绑定 INCLUDED 帧 | 恰 4 个 source unit：`frames.arm-a-trial-1-void-attempt-{1,2}-hold`（46+54，对应 run-dir hold **空目录**）、batch-b-integration `calibration-hold`（51，仅 metrics/state/latest）、rerun-prep `ordinary-frames-before-rerun`（6，仅 latest.json）。四者确无任何归档场景字节，按 BC-DATA-13 只退 unit 正确；全部属 `VOID_TRIAL_HOLD`/`CALIBRATION`（train-aug 类，不入 floor/test），对 F 下限零影响 | ✓ fail-closed 属实 |
| 修复前红灯（副本内） | round8 @ `5735838` tools：**17/24 红（13F+4E）**，红集覆盖 F1–F7/F9/F10 全族，两条钉桩（audit key、painter depth）修复前即绿——与「钉桩不计回归」的诚实口径一致；followup @ `cc4f53a` tools：**10/14 红（6F+4E）**；恢复候选后 38/38 绿 | ✓ 逐条 |
| scout-3 旁支事实 | `session/manifest.json` 声明恰一 sha `00c8802aaacf…` = A.2 provider 字节 sha（今日一致） | 见 F12 |

**F1–F10 与四条自查缺陷的闭合逐条核毕**（生产代码 + 具名回归双侧）：
BC-DATA-13 绑定域重构（source unit 切分、三条闭集关联模板、A.2 provider
的 `scenario_id` 前提、单趟由近及远、歧义 manifest `LayoutError` 不被父级
掩盖、祖先上界 = unit、子树快照字节唯一、partition 聚合与逐 sha 几何）；
BC-DATA-16 语言域闸门（非车辆 `occluder_only`，仍参与遮挡；动态目标经
循环外显式入 `blocking` 与 `frame_world` 域内重建，未被闸门误伤；m3 证据
按取值判定、缺证据 = `TARGET_UNBOUNDED`）；BC-DATA-17 双判据
（`_noun_satisfies` 严格 / `_noun_conflicts` 通配，`_resolve_ref` 单一
收口，`_unique_reference_specs` 经其枚举；`resolved_reference_object_id`
候选冻结；S7 **重新派生** `held_out_reference`；S8 硬拒 + S4 断言两侧
对称）；BC-DATA-18（逆施 removal 只用条目容差；`default_inverse_premise`
以基础几何 `source_scenario_sha256` 为唯一来源、唯一性判在字节不判路径
条数——12 副本真实归档实证）；BC-DATA-19（dropped 显式标记且不计 floor、
无标记仍硬错；splits 载荷携带角色与 exposure；S8 `station_key` 物化、
`unit_count` = (对象, 站位簇)）；BC-DATA-14/-15 钉桩（`audit_tool`、
`project_boxes` 与轮 8 前字节相同，裁定为追认，证据未把两条钉桩计入
「修复前必失败」——附议该口径）。C3-1 定点复看闭合（§6 手维护 LOC 已
删除、改运行时解析）；C3-2 已逐字应用；round 1 观察项中 `__init__`
的 `stages.py` 误引已修，歧义 manifest 静默跳过与畸形 truth fail-open
已分别并入 F1/F2 修复。

### 2. Findings（续 round 1 编号；CLASS_1/2 → REWORK_REQUIRED）

#### F11（CLASS_2）splits 角色装配未接入任何端到端生产路径：唯一集成驱动仍产出空 `sample_roles`/`exposure_matrix`

自查缺陷 4 只修了一半：装配器 `sample_roles_from_entries` 存在且两条
followup 用例单测通过，但 `assign_splits(atoms, per_frame_object_roles=())`
的角色参数仍是**带空默认值的可选参数**，而仓库唯一的端到端驱动
`tests/test_dist_data_pipeline.py` 本轮**零改动**：`_splits()` 仍调
`assign_splits(atoms)`（无角色），S4 落盘的 splits 工件对非空合成 catalog
携带**空** `sample_roles` 与**空** `exposure_matrix`；`_frozen_and_report`
仍以 `exposure=make_splits.exposure_matrix([])` 交 G0 报告。BC-DATA-2/19
「不能省略逐 sample 记录」在唯一被演示的组合路径上被实质省略且无任何
报错——与缺陷 3 被修前的形态同构（成员存在 ≠ 生产路径上生效；缺陷 3 的
修法是在 S7 重新派生使驱动无从漏传，本项没有对应机制）。闭合绑定具名
回归：管线 splits 工件必须断言 catalog 非空时 `sample_roles` 非空、
`exposure_matrix.per_object` 非空，且 G0 报告的 exposure 来自同一载荷
（按当前管线接线必失败）；实现侧使装配不可绕过（参数改必填、或在
`assign_splits`/独立 S4 组装函数内部由 catalog 记录派生）。

#### F12（CLASS_2）BC-DATA-13 (b) 的字节一致性检查只读 unit 根级 manifest；真实归档中实际存在的旁支族 manifest 任何分支都不读

裁定原文：「任何**已有** manifest/快照必须与该 provider 字节一致，否则
这条关联不成立」。实现只检查 `unit/manifest.json`
（`resolve_frame_scenario` 的 (b) 分支）。磁盘实测：scout-3 的真实族
manifest 在 `…-20260729/session/manifest.json`（正是 round 1 F1 点名的
旁支位置），既非帧祖先、又不匹配子树**快照**文件名、也不在 unit 根——
三条路径都不读它；该 unit 经帧 sidecar `scenario_id` + provider 直接
BOUND。今日其声明 sha 恰等于 provider 字节 sha（实测 `00c8802aaacf…`，
一致），故纯潜伏；但嵌套 manifest 声明**异** sha 时 (b) 关联照常成立，
矛盾被掩盖——这正是该条款要防的形态，按 BC-DATA-10/-11/-12 确立的
「今日未触发不降格」标准列为阻断。闭合：接受角色先裁定「已有 manifest」
的检查范围（unit 子树内全部 manifest，或明文收窄到 unit 根并说明理由）；
若取前者，绑定具名回归：unit 子树嵌套 manifest 声明异 sha 的 fixture 下
(b) 关联必须不成立（按当前代码必失败——实测返回
`appendix_a2_archive_provider` BOUND）。

#### F13（CLASS_2）`_self_removed` 的 phantom 取消判据仍用「0 + 类内半对角线」容差：邻居可冒充自移除实例、静默吞掉 §2.3 (a) 义务的 phantom

BC-DATA-18 刚在逆施侧禁止「加类内半对角线让邻居冒充被移除实例」
（F5(a) 已修，`tolerance_override` 只用条目容差）；但 `apply_layout` 的
`_self_removed`（判定「本布局类自身字节是否移除了该 phantom 对应实例」，
成立则取消登记）用 `_phantom_match_tolerance` =
`match_tolerance({"match_tolerance_m": 0.0}, …)` = **0 + 类内 XZ 半对角线
最大值**。布局类 removal 条目的 `original_xz_m` 距 phantom 候选原位在
半对角线内（如 2 m < 2.736 m）而实为**另一实例**时，phantom 被静默取消
——丢一个 §2.3 (a) 必登记的冲突/遮挡体，fail-open，与 F5(a) 完全同构。
候选构造时把 default 条目的 `match_tolerance_m` 丢弃了（`phantoms.append`
只存 prefab + 原位），同一实例在两份归档 config 中的 `original_xz_m` 是
同一存档量，本应以条目容差（或恰等）匹配。今日归档未触发（default 3 条
removal → 3 候选，s004 与 rate|4bddb2f2 均恰 3 phantom 存活）。闭合：
候选记录携带条目 `match_tolerance_m`，`_self_removed` 只用它；绑定具名
回归：布局 removal 原位距 phantom 原位 2 m（> 条目容差、< 半对角线）的
fixture 下 phantom 必须仍登记（按当前代码必失败——被取消）。

#### F14（CLASS_2，按数字文字规则下限定级）`tests/test_dist_data_round8.py` 模块 docstring 的回归条数与 §20.3 不符

Docstring 写「§20.3 点名的**十二条**回归全部在此」；§20.3 实点名 **16**
条（4+4+2+2+4，`7f9d4f2` 已按用户复算更正证据与状态板，但该更正是纯
文档提交，不能触碰 tests/，而 `3a7dff6` 早于发现）。按 workflow §4.4
「凡涉及数值的文字一律最低 CLASS_2」（接受轮 8 对 C3-1 的同规则适用）
列为阻断；方向是**少报**（16 ≥ 12，未掩盖任何缺失回归），一行即闭。
无稳定行为断言，标 `NOT_MECHANIZABLE`，闭合改定点复看该 docstring。

### 3. CLASS_3（不阻断；逐字替换补丁，交接受角色复判后应用）

- **C3-3** `docs/evidence/P1-VLM-DATA-001-implementation.md` §11.2 末行：
  将「新增具名常量 `camera_forward_depth()` 并加钉桩回归 | `build_catalog`、`audit_tool` |」
  替换为「新增具名常量 `camera_forward_depth()` 并加钉桩回归 | `build_catalog` |」。
  （`audit_tool.py` 本轮零字节改动——其 key 公式与分层接口既有行为即合同
  行为，钉桩在 round8 测试内；文件列多列了一个未改动文件。）

### 4. 观察项（不分级，不阻断，随返工顺带处置即可）

- `_unit_subtree_snapshot` 对子树内**字节不唯一**的合格快照返回 None 后
  继续走闭集关联——(a)/(b) 类 unit 的子树快照矛盾会被关联结果掩盖（今日
  m3 post-run 六成员组与 A.2 各 unit 均无此形态，纯假设）；F12 返工触及
  同一函数群时宜一并定语义（矛盾即 unit unbound，与 manifest 歧义同向）。
- m3 truth 行仅含 `has_unoccluded_sample: false` 而另两键缺失时按「不在
  视野」处理；「在视锥内但被遮挡」的行会漏 blocker（实测 v2 行三键齐全，
  纯假设性；正式运行前宜在 G0 报告中记录该口径）。
- `test_scout4_family_binds_via_family_manifest` 复制的族 manifest 在其
  fixture 中实际未被读取（绑定经 sidecar `scenario_id` + provider 成立）；
  测试名与机制略有出入，F12 返工时该用例自然要改。
- `test_rate_family_partitions_by_scenario_sha` 的 inventory 记录为手写
  最小 dict（帧与场景字节为真实归档副本）；接口漂移由管线端到端兜底，
  返工若重排 S1 记录 schema 需同步。
- BC-DATA-15 的 A1/A2 距离三分位装配仍在未来正式驱动的调用侧
  （`audit_tool` 的 `stratum_of_sample` 由调用方供给）；formal 批次驱动
  成形时需按 `camera_forward_depth` 组装并复核。

### 5. `UNITY_NA` 分类：**附议维持**

本轮 PLAY_GOVERNING 增量仍仅 `tools/dist_data/` 与
`tests/test_dist_data_*.py`（实测 `57e7af2..3a7dff6`）；`controller/`、
`Assets/`、`config/`、运行时协议零改动，`runtime/dist-data/` 始终不存在。
Round 1 的 `UNITY_NA` 附议继续适用，范围条件不变（越出纯离线范围即失效
并须重新取得附议）。

### 6. Verdict

**`REWORK_REQUIRED`**（round 2，候选 `3a7dff6`，接受轮 9 停点）。

- **round 1 的 F1–F10 全部确认闭合**（含四条自查缺陷的修复与真实归档
  9/9 partition / 23,549 帧绑定的独立复算）；返工方向与质量成立。
- 阻断：F11–F14（均 CLASS_2）。F11/F13 为实现侧修复 + 必失败具名回归；
  F12 的闭合含接受角色对「已有 manifest」检查范围的裁定；F14 为
  `NOT_MECHANIZABLE` 定点复看。零 CLASS_1；无任何 F1–F4 门值、冻结常量
  或既有绑定结果被推翻。
- 本轮为 `REWORK_REQUIRED`，按 COORD-007 R7 不写机读通过指针行。
- 修复批次是否开新复核轮由 workflow §4.4 开轮资格（PLAY_GOVERNING diff
  非空）决定；F11–F13 闭合走 §4.4 回归测试通道，F14 走定点复看。
- 边界自查：本会话未修改主工作树任何实现文件；探针（S1→S2 复算脚本、
  归档字节拷贝、两段修复前检出）只存在于 scratchpad 与一次性复核副本，
  副本已随 `git worktree remove --force` 删除。

---

## Round 3 — 2026-08-27

### 0. 候选、开轮资格与方法

- **候选**：`d05614d`（第 5 候选 = F11/F13/F14 批 `2aa1bc0` + F12/BC-DATA-20
  续批，接受轮 11 确认停点）。其后 `a209bb1`（推送记录）、`05b74c2`（辅助
  补账）、`187ef6c`（接受轮 11）相对候选 PLAY_GOVERNING diff 为 0（实测）；
  主树代码与候选字节相同、工作树干净（实测）。候选 tree
  `55ca3fefb0f6f5f6d72438926991f83403697c19`。
- **开轮资格（COORD-007 R1）**：复核文件仍无机读通过指针；复核范围 =
  round 2 候选之后的全部 PLAY_GOVERNING diff `3a7dff6..d05614d`——实测
  **9 个文件**（3 个 `tools/dist_data/`：`bind_layout`/`g0_report`/
  `make_splits` + 6 个 `tests/`：`gate`/`pipeline`/`review2`（新增）/
  `round8`/`round8_followup`/`splits`），467 insertions / 44 deletions，
  非空，开轮成立。`controller/`、`Assets/`、`config/`、`ProjectSettings/`、
  `Packages/packages-lock.json` 零改动（实测）。
- **方法**：一次性复核副本 `git worktree add --detach … d05614d`。9 个文件
  净 diff 逐 hunk 读完；`a2_subtree_consistency`/`_manifest_declarations`/
  `_inside` 与 `test_dist_data_review2.py` 全文读；BC-DATA-20 §22.2 五款
  逐条对照。真实归档核查用与候选字节相同的主树代码只读运行；两段修复前
  红灯在副本内检出 `3a7dff6`/`2aa1bc0` 的 `tools/dist_data/` 复现；符号
  链接越界行为写独立探针实测。区间 6 个 commit 逐个核对角色边界（接受轮
  10/11 纯文档、实现两批在白名单内、推送记录批与辅助补账批未动任何 gate
  结论/verdict/证据数字），无越权。
- **测试树哈希**：19 个 focused 测试文件串接 SHA-256
  `f7729f5b28319a15a11c01ccd35def16e964d62560cbbc456fb9e01c3d71beca`。

### 1. 复核自跑的证据（不信报告数字，全部重跑）

| 项 | 实测 | 与声明比对 |
|---|---|---|
| focused（副本，无归档） | 双解释器均 391 ran OK，33 skipped | — |
| focused（主树 = 候选同字节） | python3 3.14.6 **391/391 OK 零 skip**；.venv-yoloe 3.12.13 **391/391 OK 零 skip** | ✓ 接受轮 11 |
| 全套（钉死解释器） | **Ran 926**，FAILED (failures=1, errors=1, skipped=1)，恰为既有 CSRT/opencv-contrib 两项 | ✓ |
| 真实归档 S1→S2 全链（生产函数内存注入，零工件） | 与 round 2 实测**逐项相同**：S1 29,923 / 24,154 / 5,769 / 19,754 / zero=0 / multi=0 / 五分类不变；**9/9 partition BOUND** 同帧数（896/640/768/256/1594/3546/4836/7952/3061）；premise `config/scenario.default.json`（`f9c92052…`×12 副本）；phantom **0/0/0/3/0/3/3/3/0** 同三代理尺寸；绑定 **23,549/23,706**；157 帧仍为同四个无字节 unit（46+54+51+6）；`runtime/dist-data/` 前后不存在。**BC-DATA-20 生效未使任何绑定漂移**（scout-3 旁支 manifest 声明恰等 provider SHA → 仍 BOUND） | ✓ §13.4「diff 为空」属实 |
| 修复前红灯（副本内） | Stage A（tools@`3a7dff6` + 候选测试，F11×2 + F13 组 3）：**1 failure + 2 errors**（两条管线回归 KeyError、邻居移除 0 != 1，两条对照绿）；Stage B（tools@`2aa1bc0`，A.2 六条）：**3 failures**（nested / snapshot-conflict / **追加的 unreadable** 三条修复前均错 BOUND，三条对照绿）；恢复候选后 review2 9/9、合计 21/21 绿 | ✓ 轮 11 的 1F+2E 与「两条点名错 BOUND」一致；unreadable 一条实测也是真红（其「追加」时序使实现者侧 5-测量与接受侧 6-测量互不矛盾） |
| manifest 普查（§13.5 (1) 的披露数字） | 全 `runtime/` 递归 `_manifest_declarations`：**51 份 = 29 单声明 + 22 零声明 + 0 歧义 + 0 不可读**；A.2 三族 unit 子树内为 2 份（scout-3 单声明 + 1 零声明） | ✓ 逐字 |
| 符号链接（§22.2 (1) 潜伏保护） | `runtime/` 实测符号链接 **0**；独立探针三态：unit 内**目录链接**指向域外矛盾 manifest → 不入域不误报；unit 内**文件链接**指向域外 → resolve 越界被拒、不补证；域内真实矛盾 → 正常命中 `…manifest_sha_mismatch` | ✓ 「不跟随越界链接补证」成立 |
| 只读诊断耗时 | 本轮 S1→S2 复算与披露同量级（数分钟；round 2 约 2 分钟内），与「1:51 → 4:04」方向一致 | ✓ 非阻断代价属实 |

### 2. F11–F14 与 C3-3 的闭合逐条核毕

- **F11 闭合**：`assign_splits(atoms, catalog_entries)` 参数**必填**、角色在
  函数内部由 `sample_roles_from_entries` 派生（照缺陷 3 的 S7 重派生模式，
  驱动无从漏传也无从传不一致表）；`build_g0_report` 删除独立 `exposure`
  形参、改读 `splits_payload["exposure_matrix"]`（缺成员 KeyError 硬失败）；
  唯一端到端驱动接线更新，两条点名回归断言**落盘工件**的 `sample_roles`
  非空、exposure 与同一载荷相等。dropped 帧的角色按 `split_of_frame` 成员
  过滤整体不出现。`test_dist_data_gate.py` 合成载荷显式携带空
  `exposure_matrix` 成员——附议实现者判断：这不是绕过（门判定单测 +
  显式成员正是 KeyError 合同要求的形态）；`test_dist_data_splits.py` 的
  `assign_splits(atoms, [])` 为指派/泄漏单测的显式空目录，亦非绕过。
- **F12 闭合（按 BC-DATA-20）**：`a2_subtree_consistency` 五款逐条对上——
  (1) 边界 = unit 归档子树，`_inside` 以 `resolve()` 判越界（探针实测）；
  (2) 证人闭集 = 任意深度 `manifest.json` + 合格快照，sidecar/truth 不入；
  (3) 全量枚举后按相对路径升序统一求值，**无就近短路**，根级/祖先无优先权，
  同字节多副本允许；(4) 不可读（`None`）与 mismatch 均使 (b) 关联不成立、
  只退本 unit、不回退 sidecar/provider/父级/邻居，见证路径确定性点名；
  (5) `scenario_id` 前置与 provider 字节未动，无显式证人时照常 BOUND。
  `_manifest_declarations` 的 `None`（不可读）/`[]`（零声明）二分在两个
  调用点均正确消费；`_manifest_scenario_sha` 对外行为逐字不变；单份
  manifest 多互异 SHA 仍走既有歧义硬失败。round 2 观察项「子树快照矛盾被
  关联掩盖」对 A.2 就此闭合（snapshot-conflict 回归覆盖）；(a)/(c) 类按
  §22.3 (3) 明文不泛化，维持观察项。
- **F13 闭合**：phantom 候选随身携带条目 `match_tolerance_m`，
  `_self_removed` 只用它（缺字段按 0.0 恰等，最严侧）；
  `_phantom_match_tolerance` 已删除且无其他调用点。夹具前提
  0.1 < 2.0 < 2.121320 钉死；对照组证明自移除取消未被误关。
- **F14 闭合（定点复看）**：docstring 现写「十六条」，§20.3 实点名 16
  （4+4+2+2+4），round 2 已逐字核对 16 个函数名全部在位。
- **C3-3 已由接受轮 10 应用**：§11.2 文件列现为 `build_catalog`（实测）。

### 3. §13.5 两条披露的独立复判

1. **歧义硬失败作用域扩大：附议接受轮 11 的接受**。BC-DATA-13 (v) 的
   歧义硬失败在 round 2 复核时即为「从 `bind_families` 抛出、终止整个
   S2」的语义（当时按合同附议）；BC-DATA-20 §22.2 (2) 把 manifest 证人域
   扩到子树，(3) 逐字保留既有硬失败，发现域随之扩张是裁定的直接蕴含。
   「同一证人声明多个互斥身份」与 (4) 的「单一显式声明与 provider 不一致/
   不可读」是不同故障类，前者禁止交付任何部分工件是 fail-closed 正向。
   今日 51 份 manifest 歧义 0（本轮独立普查），无现实触发。若未来改为
   unit-local 退出，属 BC-DATA-13 (v) 修订，须走接受轮，不得实现自选——
   与轮 11 的定性一致。
2. **1:51 → 4:04 无缓存：附议接受为非阻断代价**。已接受合同无诊断时限；
   memoisation 的失效语义未冻结时引入缓存，恰是本 finding 家族「陈旧状态
   静默掩盖矛盾」的同一失败模式。性能优化应另立范围、冻结失效判据后再做；
   本轮不因耗时退回。复核自身复算同量级耗时，如实计入本轮成本。

### 4. 授权链归因的附议

`docs/authorizations.md` 三条补记处置规范：「可以推送吧」「先动
F11/13.14，12 等待裁定」逐字入账；「继续做完 F12」如实标为**转述、未经
用户确认、不得引用为放行依据**。附议接受轮 11 §23.3 的归因：F12 续做的
权限链 = 2026-08-26 逐字「授权进行实现」的既有纯离线范围 + 逐字指令
「12 等待裁定」所设顺序停点已被接受轮 10 的 BC-DATA-20 满足——**不依赖**
那条未确认转述。辅助批次未动任何 gate 内容（diff 实测）。

### 5. Findings（续编号）

#### F15（CLASS_2，按数字文字规则下限定级）证据 §12.7 的复核范围文件数与实测不符，且与其自身 (2) 款自相矛盾

§12.7 首段：「`git diff <复核轮 2 候选>..<本候选>` 的 PLAY_GOVERNING 增量
恰为 **8 个文件**（**3 个 `tools/dist_data/` + 5 个** `tests/test_dist_data_*.py`，
含 1 个新增）」。实测：对 §12 批次端点（`3a7dff6..2aa1bc0`）与最终候选
端点（`3a7dff6..d05614d`）都是 **9 个文件（3 tools + 6 tests）**；漏计的
是 `tests/test_dist_data_gate.py`——而 §12.7 自己的第 (2) 款正在讨论该
文件的合成载荷是否算绕过，句内自相矛盾。按 workflow §4.4「凡涉及数值的
文字一律最低 CLASS_2」（C3-1 升格与 F14 的同一规则）定级；操作员按该句
枚举复核范围会少查一个文件（本轮按 git 全量 diff 复核，未受影响）。该
数字同时是 COORD-007 R7 意义上的可派生量（`git diff --name-only` 即得），
宜照 C3-1 闭合先例**删除手写计数、改运行时解析**，或改正为 9（3+6）。
证据文件不在 PLAY_GOVERNING 集合内：修复为纯文档批次，按 §4.4 开轮资格
不触发新复核轮，闭合走 `NOT_MECHANIZABLE` 定点复看本节文字。

### 6. 观察项（不分级，不阻断）

- round 2 观察项状态：子树快照矛盾掩盖——**A.2 已闭**（本轮回归覆盖），
  (a)/(c) 类按 BC-DATA-20 明文不泛化、维持观察；`test_scout4_…manifest`
  名实出入——仍在（该 fixture 的族 manifest 位于 unit 外，本轮后仍不被
  任何分支读取，绑定实经 sidecar + provider）；m3 部分证据行、手写
  inventory 记录 dict、BC-DATA-15 三分位装配在未来驱动侧——均维持原状。
- 祖先/关联-run 解析路径上的 manifest **不可读时仍按无声明跳过**（
  `_manifest_scenario_sha` 既有行为）；BC-DATA-20 的不可读硬拒只覆盖
  A.2 一致性域。属裁定明文范围之外的既有语义，非缺陷；正式驱动成形时
  宜在 G0 报告记录该口径。
- 实现者证据 §13.3 的修复前测量是 5 用例版（unreadable 回归其后追加），
  接受轮 11 与本轮的 6 用例测量与之时序相容；三方数字互不矛盾，已在
  §1 表中记明。

### 7. `UNITY_NA` 分类：**附议维持**

本轮 PLAY_GOVERNING 增量仍仅 `tools/dist_data/` 与
`tests/test_dist_data_*.py`（实测 `3a7dff6..d05614d`）；`controller/`、
`Assets/`、`config/`、运行时协议零改动，`runtime/dist-data/` 始终不存在。
Round 1/2 的 `UNITY_NA` 附议继续适用，范围条件不变。

### 8. Verdict

**`REWORK_REQUIRED`**（round 3，候选 `d05614d`，接受轮 11 停点）。

- **F11、F12、F13、F14 全部确认闭合**（生产代码、具名回归、两段修复前
  红灯、真实归档零漂移四侧核毕）；C3-3 已应用；两条 §13.5 披露均附议；
  授权链归因附议。生产代码与测试**零新缺陷**。
- 阻断仅 **F15**（CLASS_2，实现者证据 §12.7 的复核范围计数错误）。修复
  为纯文档批次（证据非 PLAY_GOVERNING，不触发新复核轮），闭合走
  `NOT_MECHANIZABLE` 定点复看；接受角色归因后由实现角色改正证据文字
  即可回停点。
- 本轮为 `REWORK_REQUIRED`，按 COORD-007 R7 不写机读通过指针行。
- 边界自查：本会话未修改主工作树任何实现文件；探针（S1→S2 复算、符号
  链接三态、两段修复前检出、归档字节拷贝）只存在于 scratchpad 与一次性
  复核副本，副本已随 `git worktree remove --force` 删除。

---

## Round 4 — 2026-08-28

### 0. 候选、开轮资格与方法

- **候选**：`611721e`（第 6 候选：像素适配器 + S0–S9 生产 driver，接受轮
  14 §26.2 code-only 范围，接受轮 15 确认停点）。其后 `99554d9`（接受轮
  15）相对候选 PLAY_GOVERNING diff 为 0（实测）；主树代码与候选字节相同、
  工作树干净（实测）。候选 tree
  `5972742b4d5bf2ffb52b6d14e024f963ac5be534`。
- **开轮资格（COORD-007 R1）**：复核文件仍无机读通过指针；范围按证据
  §12.7 运行时解析 = round 3 候选之后的全部 PLAY_GOVERNING diff
  `d05614d..611721e`——逐行：`tools/dist_data/bind_layout.py`（+24/−6，
  BC-DATA-22 注入点）、`tools/dist_data/pixel_source.py`（新，253 行）、
  `tools/dist_data/run_pipeline.py`（新，638 行）、
  `tests/test_dist_data_driver.py`（新，371 行）、
  `tests/test_dist_data_pixels.py`（新，231 行）；与接受轮 15 交接的逐行
  清单一致，非空，开轮成立。`controller/`、`Assets/`、`config/`、
  `ProjectSettings/`、`Packages/packages-lock.json` 零改动（实测）。
- **方法**：一次性复核副本 `git worktree add --detach … 611721e`。两个新
  模块与两个新测试文件全文读；`bind_layout` 增量逐 hunk；BC-DATA-21/-22
  与 §26.2 边界逐款对照；driver 逐 `stage*` 方法核「只做取数/调用/落盘」；
  被 driver 调用的既有函数（`merge_atoms`/`SplitTerminal`/
  `held_out_objects`/`build_field_catalog`/`build_d0`/
  `vehicle_envelope_half_extents`/`normalized_xywh`）逐一核存在性与语义。
  真实归档核查用与候选字节相同的主树代码只读运行；像素语义写**独立算术
  探针**（不用被测模块的任何助手）。区间 8 个 commit 逐个核对角色边界
  （账本确认条目、两次 F15 文档修正、四个接受轮、候选批次），无越权。
- **测试树哈希**：21 个 focused 测试文件串接 SHA-256
  `313f8dae86dcf05ccb4d543c83a7ce97bb203033b3b154fc09a390f69d10200b`。

### 1. 复核自跑的证据（不信报告数字，全部重跑）

| 项 | 实测 | 与声明比对 |
|---|---|---|
| focused（主树） | 钉死 .venv-yoloe 3.12.13：**418/418 OK 零 skip**；裸 python3 3.14.6：**418 OK + 9 skip**（Pillow 金标） | ✓ §14.4/轮 15 逐字 |
| focused（副本，无归档） | 裸 python3：418 OK + 42 skip；**钉死解释器：418 = 2 errors + 40 skips —— FAILED** | 见 **F19**（披露只覆盖主树形态） |
| 全套（钉死解释器） | **Ran 953**，failures=1 errors=1 skipped=1，恰为既有 CSRT/opencv-contrib 两项 | ✓（926 → 953 = 本批 27 条） |
| 像素独立算术探针（真实帧 `scout-3/frame_0000000003.jpg`） | 三个块 (0,0)/(31,31)/(13,5) 的 gray_matrix 与我自己的整数通道和→一次 luma→除法**逐位相等**；负界小数框 `(-2.7,477.2,3.499,481.0)` 的 crop 与我逐像素中心枚举**相等**（9 px）；库 `convert("L")+resize` 同块值 **82.0 ≠ 83.772…**（冻结算术非库行为别名）；`phash()` 与 `make_splits.phash(gray_matrix)` 相等 | ✓ BC-DATA-21 落地为真 |
| 生产 CLI preflight（真实归档，双解释器） | `python -m tools.dist_data.run_pipeline --repo-root .`：records **29,923**、zero/multi 0、五分类不变、INCLUDED 23,706、**9/9 BOUND** 逐 partition 帧数与轮 2/3 相同、实例 779×9、phantom **0/0/0/3/0/3/3/3/0**、bound **23,549**、同四个 unbound unit、invalid 0；`wrote_nothing`、artifact root 前后不存在、`runtime/dist-data/` 不存在、`runtime/` git 干净；**两解释器输出逐字节相同**（cmp） | ✓ §14.4 与轮 15 逐项；披露 (3) 的字节同一性亲测 |
| BC-DATA-22 两径不可混认 | `stage2_layout()` 不传 `inventory=`（读冻结 S1 工件，禁行边生效）；preflight 传内存载荷且 `inputs = [{"kind":"inventory","source":"in_memory_preflight"}]`，不伪造 attempt/SHA；`--run` 不触 preflight 路径 | ✓ |
| 审计分层 | `audit_strata` 按 `(camera_forward_depth, sample_id UTF-8)` 排序后等分三段 ✓ BC-DATA-15；样本域见 **F18** | 部分 ✓ |

**§26.2 边界逐款核毕**：adapter 只用钉死环境已装库、缺库 `PixelError`
指回钉死解释器、不安装不改依赖清单；driver 逐 `stage*` 只做取数/调用/
落盘，未复制任何阶段算法（S3 真值 join 按 S1 闭集映射原样读取、S4 并簇
调 `merge_atoms`、S7 调 `freeze_mother_candidates`/`build_g0_report`、S8
调 `build_d0`）；跨阶段取数全走 `ArtifactStore.read(requesting_stage=N)`
（禁行边生产路径生效，测试实证）；S6 人工审计拒绝合成（缺 `audit@` 硬
错误点名 F1 定义）；门未过/`SplitTerminal` 均写 S9 收束、S8 永不执行且
既有工件保全（测试实证 + `SplitTerminal` 类型与 `.terminal/.detail` 属性
与 driver except 匹配，实读确认）；测试不产出正式工件根（断言 + 本轮
实测 `runtime/dist-data/` 始终不存在）。`held_out_objects` 过滤非车辆且
全 779 体逐帧在场 ⇒ n_c 口径与全目录等价。F15 的 §12.7 修正核毕（无手写
计数、引用 §4.4 不复抄、运行时派生）；账本「继续做完 F12」条目已由用户
逐字确认为**经确认的转述**，处置合规。

### 2. Findings（续编号；均为新增 driver/adapter 批次所出）

#### F16（CLASS_2）§2.3 历史布局交叉验证在唯一生产入口没有任何执行点；S3 硬编码 `layout_binding_valid=True`，G0 报告的交叉验证节恒为空

`cross_validate_layout`（BC-DATA-3 语义，round 1 已复核其实现正确）在
生产代码中**零调用点**（实测全仓 grep：仅测试调用）。`build_layout` 不
计算它；`stage7_gate` 交给报告的是
`self._read("layout", …).get("cross_validation", {})`——**恒为空 dict**；
`stage3_frames_catalog` 对每帧硬编码 `layout_binding_valid=True`。§2.3
冻结条款「对每个有归档真值框的族…中心命中 ≥ 90%、IoU 中位数 ≥ 0.5，
不达 → 该族布局绑定 `INVALID`，帧全部退出并计入 G0 报告」在组合后的
生产管线中**无法发生**：基础场景在采集后被改动过的族会静默保持
VALID、进入 floor 计数，报告的 `cross_validation` 为空也不报错。这正是
该条款要防的形态（真值质量污染，fail-open）。今日纯潜伏（无正式运行
授权；附录 B 动机性抽验显示今日归档大概率能过检）。闭合：接受角色先
裁定该检查在组合中的落点（S2 载荷内逐族计算，或 S3 前独立步骤），实现
将 `layout_binding_valid` 改为按族/partition 的交叉验证结果派生、报告
只接受计算出的结果；绑定具名回归：合成世界中有真值框族的布局整体平移
超阈值时，S3/S7 必须使该族帧退出 floor 且报告记 `INVALID`（按当前代码
必失败——保持 VALID、报告为空）。

#### F17（CLASS_2）`INVALID` partition 使 S3 崩溃而非按 §2.3「帧全部退出」

`_partition_of_unit` 把**全部** partition（含 `binding_status=INVALID`）
的 source unit 都映射进查找表；`stage3_frames_catalog` 对命中 INVALID
partition 的帧取 `partition["instances"]`——而 `build_layout` 对派生失败
的 partition **不写** `instances`/`phantoms` 键（异常分支只记
`binding_status`/`reason`）→ `KeyError` 使整个 S3 崩溃。BC-DATA-18 的
partition 局域隔离（「只使该 partition INVALID」）在 S3 被打破：一个
partition 派生失败会让**全部** partition 无法产出 catalog，而合同要求的
是该 partition 的帧退出、其余照常。方向 fail-closed（崩溃非静默错数）
但违反隔离语义且不可用。今日纯潜伏（9/9 BOUND，invalid 0）。闭合：
S3 跳过非 BOUND partition 的帧并计数（如 `skipped_invalid_frames`）；
绑定具名回归：一 BOUND + 一 INVALID partition 的 fixture 下 stage3 必须
成功产出 BOUND 侧 entries 并排除 INVALID 侧帧（按当前代码必失败——
KeyError）。

#### F18（CLASS_2）`audit_strata` 的样本域含 `occluder_only` 非车辆：审计对象域应为目录车辆

§2.7 的 A1/A2 样本全部是目录车辆概念（类别映射/颜色 crop/框身份/
「车辆全部可见像素在框内」的 gold 规则；A2 分层格的状态轴
{OK, EXCLUDED_OCCLUDED} 是语言域状态）。`audit_strata` 只按
`status == "OK"` 过滤——建筑/nature/prop 在投影后同样可得 OK 状态
（BC-DATA-16 只把它们挡在 blocking/referable/exposure 外，不挡在状态机
外），于是进入三分位样本池；未来 panel 生成若消费该池，将把不可审计的
非车辆样本混入 12 格配额与分母。与 F2 同族（语言域分离在新组件上又漏了
一处），且合成 driver 测试世界只有车辆，测试盲区与 F2 当年相同。今日
纯潜伏（panel 生成未授权未实现）。闭合：`audit_strata` 过滤到语言域
审计对象（`class_for_scene_object(object_id) is not None`；phantom 已被
OK 过滤天然排除）；绑定具名回归：混合世界下 `audit_strata` 不得含建筑
样本（按当前代码必失败——被计入）。

#### F19（CLASS_2）两条 Pillow 金标缺归档存在守卫：focused 套件在规定的复核环境（无归档一次性副本）FAILED

`tests/test_dist_data_pixels.py` 的
`FailClosedTest.test_corrupt_bytes_fail_closed` 与
`test_truncated_bytes_fail_closed` 只有 `@needs_pillow` 守卫，直接
`sorted((PROJECT_ROOT / ARCHIVE_FRAMES).glob(...))[0]`——归档缺失时
IndexError。同文件 `ArchiveFrameTest` 的归档守卫（`skipTest`）没有覆盖
这两条。本轮实测：一次性复核副本（无 `runtime/` 归档）上钉死解释器
focused = **418 ran, FAILED (errors=2, skipped=40)**——而复核纪律要求的
重跑环境正是该副本；裸 python3 因 Pillow 先 skip 而侥幸 42 skip 全绿。
§14.4 的披露只写了主树两形态（零 skip / 9 skip），未覆盖此形态。闭合：
两条用例补与 `ArchiveFrameTest` 同款归档守卫；闭合核验（定点复跑）：
无归档副本双解释器 focused 均须 OK（错误转为 skip），不必新增测试。

### 3. §14.5 四条披露的独立复判

1. **两项像素自由度（BC-DATA-21 冻结）：附议接受轮 15**。ITU-R 601-2
   float luma + 整数块和求值序、像素中心半开判据——独立算术探针逐位/
   逐像素验证为真，且与库 `convert+resize` 实测**不同**（82.0 vs
   83.772…），证明冻结的是可复算算术而非库行为别名；640/480 均被 32
   整除，块均值确无自由度；不整除硬失败已由测试钉死。
2. **`inventory=` preflight 注入（BC-DATA-22）：附议**。两径不可混认
   实测成立（§1 表）；替代方案（只跑到 `bind_families`）会重蹈候选 4
   「从未触及 build_layout」的覆盖盲区，取舍正确。
3. **耗时：附议非阻断**。本轮双解释器各自完整复跑并 `cmp`：**输出逐
   字节相同**；耗时与披露同量级。无缓存即无陈旧语义，维持轮 3 立场。
4. **合成-only `--run` 覆盖缺口：附议如实，且本轮印证其后果**——F16/
   F17 正是「真实/异常组合从未端到端跑过」才可能残留的组合缺陷，披露
   本身的方向正确；缺口在正式运行授权前只能靠代码复核补，本轮已逐
   `stage*` 读毕。

### 4. 观察项（不分级，不阻断）

- `stage4_splits` 的 `SplitTerminal` except 分支无端到端覆盖（
  `test_split_terminal_also_stops_before_s8` 用手工 stub 阶段测的是
  `run_stages` 的收束处理；异常类型与属性已实读匹配）。返工触及 S4 时宜
  补一条 <2 atom 合成世界直穿 `stage4_splits` 的用例。
- `preflight()` 的 `wrote_nothing: True` 是硬编码字面量（前后存在性字段
  才是证据）；宜派生为存在性检查的合取。
- driver 的 S5 `object_ids` 含 OK 状态的非车辆（field catalog 会为建筑
  生成 `class_verified=False` 记录）：dual-verified/F1 分母分子不受污染
  （实读确认），但正式 A1 的组数 G 与像素工作量会被非车辆组虚增；F18
  返工时宜同批在 S5 入口过滤。
- 轮 2/3 遗留观察项维持原状（(a)/(c) 类子树矛盾语义、祖先 manifest
  不可读跳过口径、m3 部分证据行、BC-DATA-15 三分位在 panel 侧的最终
  装配——最后一项本轮已由 `audit_strata` 部分落地，剩余归 F18）。

### 5. `UNITY_NA` 分类：**对新增代码附议，累计维持**

本轮 PLAY_GOVERNING 增量仍仅 `tools/dist_data/` 与
`tests/test_dist_data_*.py`（运行时解析，逐行见 §0）；`controller/`、
`Assets/`、`config/`、运行时协议零改动；`runtime/dist-data/` 于 preflight
前后与测试后均不存在（实测）。**对第 6 候选的新增代码附议 `UNITY_NA`**；
连同轮 1–3 的附议覆盖至今全部复核过的代码，条件不变（越出纯离线范围即
失效）。

### 6. Verdict

**`REWORK_REQUIRED`**（round 4，候选 `611721e`，接受轮 15 停点）。

- **BC-DATA-21/-22 与 §26.2 边界全部确认落地**；像素算术、preflight
  字节同一性、9/9 partition 零漂移、953 全套、418 双形态 focused 均独立
  复现；四条披露全部附议；F15 闭合与账本确认处置核毕。
- 阻断：**F16–F19（均 CLASS_2）**。F16 需接受角色先裁定交叉验证在组合
  中的落点；F17/F18 为实现侧修复 + 必失败具名回归；F19 为测试守卫补齐 +
  定点复跑核验。零 CLASS_1；无任何冻结常量、既有绑定结果或已闭 finding
  被推翻。
- 本轮为 `REWORK_REQUIRED`，按 COORD-007 R7 不写机读通过指针行。
- 边界自查：本会话未修改主工作树任何实现文件；探针（像素独立算术、
  preflight 双解释器运行与 cmp、S1→S2 相关只读运行）只存在于 scratchpad
  与主树只读进程，复核副本未被修改并已随
  `git worktree remove --force` 删除。

---

## Round 5 — 2026-08-28

### 0. 候选、开轮资格与方法

- **候选**：`33537f8`（第 7 候选 = F17/F18/F19 批 `5c80dc3` + F16/BC-DATA-23
  批 `487430f` + BC-DATA-24 批，接受轮 18 确认停点）。其后 `e9fc3f9`（接受
  轮 18）相对候选 PLAY_GOVERNING diff 为 0（实测）；主树代码与候选字节
  相同、工作树干净（实测）。候选 tree
  `7cf090e3ef4a3a1527e4f830eb9aba6755dfbb80`。
- **开轮资格（COORD-007 R1）**：范围运行时解析 = round 4 候选之后的全部
  PLAY_GOVERNING diff `0e0993f..33537f8`——逐行：
  `tools/dist_data/bind_layout.py`（+267：`cross_validate_partition`/
  `load_frame_truth`/viewport 裁剪）、`tools/dist_data/run_pipeline.py`
  （±109：两表拆分/派生 valid/共用 truth join/车辆过滤/派生 wrote_nothing）、
  `tools/dist_data/g0_report.py`（`layout_payload` 必有成员）、
  `tests/test_dist_data_driver.py`（+336）、`tests/test_dist_data_layout.py`
  （夹具修正）、`tests/test_dist_data_pipeline.py`、
  `tests/test_dist_data_pixels.py`（`require_archive`）、
  `tests/test_dist_data_gate.py`；非空，开轮成立。`controller/`、`Assets/`、
  `config/`、`ProjectSettings/`、`Packages/packages-lock.json` 零改动，
  `contract.py`/`project_boxes.py`/`roots.py` 亦零改动（阈值/选样法/闭集
  **结构性**未动，实测 diff 为空）。
- **方法**：一次性复核副本 `git worktree add --detach … 33537f8`。8 个文件
  净 diff 逐 hunk 读完；BC-DATA-23 七款、BC-DATA-24 五款逐条对照；三段
  修复前红灯按「修复批次自己的测试 × 前一批 tools」的口径在副本内复现；
  0.78→1.0 用**自写度量代码**在同一批 SHA 序 50 对上双域复算；真实归档
  preflight 经生产 CLI 完整复跑。区间 6 个 commit 逐个核对角色边界（三个
  实现批、三个接受轮含两条转述账目），无越权。
- **测试树哈希**：21 个 focused 测试文件串接 SHA-256
  `687a8da3206eb008917b96e395b361c9e5ae600753ef82d51f18e3b4ba96b1f0`。

### 1. 复核自跑的证据（不信报告数字，全部重跑）

| 项 | 实测 | 与声明比对 |
|---|---|---|
| focused（主树） | 钉死 3.12.13：**424/424 OK 零 skip**；裸 3.14.6：**424 OK + 9 skip** | ✓ 轮 18 逐字 |
| focused（副本，无归档）——F19 闭合判据 | **双解释器均 424 OK (skipped=46)**，零 error | ✓ §15.3；轮 4 的 FAILED 形态已消除 |
| 全套（钉死解释器） | **Ran 959**，failures=1 errors=1 skipped=1，恰为既有 CSRT 对 | ✓（953 → 959 = 本批 6 条） |
| 三段修复前红 | A′（tools@`0e0993f` × tests@`5c80dc3`）：**恰 1 ERROR（F17 `KeyError: 'instances'`）+ 1 FAIL（F18 建筑入池）/16**；B′（tools@`5c80dc3` × tests@`487430f`）：F16 两条按 §16.3 形态红（FAIL 缺 `cross_validation` 成员 + ERROR KeyError；另有跨版本夹具常量 `CROSSCHECK_NOT_APPLICABLE` 造成的非诊断性 error，方向仍 fail-closed）；C（tools@`487430f` × 候选测试）：**恰 2 FAIL**，断言原文 `0.9 != 1.0` 与 `'INVALID' != 'BOUND'` 逐字复现——**缺席用例的红确来自裁剪域**，§17.3 诚实说明属实；恢复候选后 20/20 绿、tracked 零残留 | ✓ §15.5/§16.3/§17.3 |
| **0.78 → 1.0 独立复算（§30 点名）** | 自写度量代码，生产采样链取同一 278 样本帧 → 同一 SHA 序 50 对：**amodal 域 centre 0.780 / IoU 0.999991594；裁剪域 centre 1.000 / IoU 0.999994651**；生产函数在同 50 对上 1.0/0.999994651/BOUND 与我逐位一致。选样与裁剪无关、参数零变化——9/9 **不是调参回归** | ✓ §16.4/§17.4 逐位 |
| 生产 CLI preflight（真实归档） | 29,923 / zero-multi 0 / INCLUDED 23,706 / bound **23,549** / **9/9 BOUND（验证后状态）** / `wrote_nothing`（现为派生值）/ 工件根前后不存在 / `runtime/` git 干净；逐 partition 交叉验证：detect-scout1 scouting 50 对/278 样本 centre 1.0 IoU 0.9999946514；**m3-armA 0.9765395894（682）**、**m3-armB 0.9215686275（153 = 141/153 精确）**；s004-scout 50/4836 centre 1.0 IoU 0.9999950280；rate×2/s004-qual/s004-smoke/scene-val 无逐帧真值 → mode none（与附录 A 一致） | ✓ §17.4 逐位 |
| 夹具修正核（§30 点名） | `test_dist_data_layout.py`：旧夹具 40/60 实例在视口外、「完美真值」= amodal（旧域自证）；新 12×5 网格 setUp 断言 60/60 在视口内、完美真值 = 裁剪框（归档同域）；测试方法与断言**未弱化**（只改 fixture 语义） | ✓ 收紧非放宽 |

**BC-DATA-23 七款逐条核毕**：(1) 验证在 partition 循环后、`return`/写盘前
并入载荷，S3 不重算；(2) 决定单位 = 精确 `(family, sha)`，失败只翻自身；
(3) `load_frame_truth` 为 S2/S3 唯一 truth join（`run_pipeline._truth_row`
已删，全仓 grep 无第二套），相机只由同名 sidecar 构造；(4) 分轨逐字——
scouting 恰一映射对交 `cross_validate_layout`（<50 INVALID）、m3 只走中心
落框率（`pair_count` 恒 0、`iou_median` 恒 None、不补静态对）、无 source →
`NOT_APPLICABLE_NO_ARCHIVED_FRAME_TRUTH`、有 source 零样本 → INVALID、
`TruthJoinError` → INVALID 带 reason；(5) `cross_validation` 必有成员按
partition id 排序，`build_g0_report` 形参改 `layout_payload`（缺成员
KeyError，与 F11 同构），S3 入口同断言；(6) 几何查找表只装 BOUND、状态表
分离供 `skipped_invalid_frames`/`skipped_unbound_frames` 二分，
`layout_binding_valid` 由 partition 状态**派生**（字面量 True 已删）；
(7) preflight 走同一 `build_layout`，诊断逐 partition 附于输出。
**BC-DATA-24 五款核毕**：裁剪在 `candidates[:50]` 选样**之后**的度量循环
内、两判据同用交框、真值框不裁、amodal None/无交集按 miss+0.0；
`project_aabb`/S3 `amodal_px`/遮挡/截断/m3 分支零改动（文件级 diff 为空）；
缺席（无文件/无行）= 无观测跳过、仍受 <50/零样本门约束；存在而不可读 →
INVALID；错配对照（scene-004 几何 × scout 真值）实测 centre 0.0 / IoU 0.0
→ INVALID——**裁剪救不活真漂移**。F19 的 `require_archive` 三处统一。
账本两条转述条目（「先做 F17/F18/F19」「按 BC-DATA-24 继续」）均按用户
既定指示标注转述、边界完整；角色边界六提交干净。

### 2. Findings

**无新增阻断 finding。** F16、F17、F18、F19 全部确认闭合（每条有按对应
批次口径复现的修复前红 + 修复后绿 + 真实归档实证）；BC-DATA-23/-24 与
§26.2 边界零违反；阈值、选样法、附录 A、F1–F4 零漂移（结构性 diff 为空 +
同 50 对双域复算）。

### 3. Notes（不阻断，随后续批次处置）

- **m3-armB 中心落框率 `0.9216`（141/153）距门 `0.9` 仅 3.3 个样本**：
  已披露风险，附议轮 18 的非阻断定性；正式运行时该 partition 的判定对
  样本集变化敏感，不得为其调参（BC-BODY1-15 (d) 同源纪律）。
- `cross_validate_partition` 的 schema 优先序（scouting 非空即返回，m3
  样本被忽略）在今日附录 A 下不可触发（族内 schema 单一）；若未来出现
  混 schema partition，需回接受角色定义合并语义。
- 修复前红的跨版本测量口径：候选测试引用 `CROSSCHECK_NOT_APPLICABLE`
  常量，使「最终测试 × 更早 tools」的组合出现非诊断性 AttributeError
  噪声；本轮以批次对齐口径（A′/B′/C）分离出全部具名红。后续轮次照此。
- 轮 4 观察项状态：`wrote_nothing` 已改派生（闭）；S5 非车辆预过滤按轮
  16 裁定明示推迟（开，非阻断）；`SplitTerminal` 端到端覆盖仍未补（开）；
  轮 2/3 遗留项维持。

### 4. `UNITY_NA` 分类：**对本候选增量附议，累计维持（轮 1–5）**

本轮 PLAY_GOVERNING 增量仍仅 `tools/dist_data/` 与
`tests/test_dist_data_*.py`；`controller/`、`Assets/`、`config/`、运行时
协议零改动；`runtime/dist-data/` 于 preflight 前后与测试后均不存在
（实测）。附议条件不变：越出纯离线范围即失效。

### 5. Verdict

**`PASS_WITH_NOTES`**（round 5，候选 `33537f8`，接受轮 18 停点）——本
work ID 的**首个通过轮**。

- F1–F19 与 C3-1…3 至此全部闭合；BC-DATA-1…24 在交付代码上零违反；全部
  头条数字（424 双形态 + 副本 46-skip 全绿、959、三段修复前红、双域
  50 对复算、preflight 全表）独立复现。
- 注记 4 条（见 §3），无阻断问题；work item **不因本轮关闭**：正式
  S0–S9/G0/D0 工件、A1/A2/A3 人工审计、D1–D3/C1 与一切资源使用仍待用户
  另行授权，`UNITY_NA` 附议只解决 Unity 列分类资格。
- passed_candidate: 33537f8f040028adaf89cae9ffab9c1ecc7bd172
- 边界自查：本会话未修改主工作树任何实现文件；探针（双域复算、三段
  检出、归档字节拷贝）只存在于 scratchpad 与一次性复核副本，副本已随
  `git worktree remove --force` 删除。

---

## Round 6 — 2026-09-01

### 0. 候选、开轮资格与方法

- **候选**：`994ab7cd1ea614fe6dab852d601cd85b28abe0e5`（BC-DATA-25 代码批
  `80ff7a5` + 接受轮 22 SP22-1/SP22-2 返工批，接受轮 23 确认停点）。候选
  tree `3357f1d2f1b138e8dc2e4c90d188a6ea4e09e4c1`。其后 HEAD `dcba374`
  （接受轮 23）相对候选只改 3 个文档文件，PLAY_GOVERNING diff 0（实测），
  主树代码与候选字节相同。
- **开轮资格（COORD-007 R1）**：上一通过候选由本文件最近一行
  `passed_candidate` 派生 = `33537f8f040028adaf89cae9ffab9c1ecc7bd172`。
  运行时派生范围 `git diff 33537f8..994ab7c` 于 PLAY_GOVERNING 上 5 个
  文件非空：`tools/dist_data/artifacts.py`（±318）、`make_splits.py`
  （±160）、`run_pipeline.py`（±356）、`tests/test_dist_data_composite.py`
  （+439 新增）、`tests/test_dist_data_driver.py`（±57）；开轮成立。
  `controller/`、`Assets/`、`config/`、`ProjectSettings/`、
  `Packages/packages-lock.json` 零改动，`contract.py`/`build_catalog.py`/
  `bind_layout.py`/`g0_report.py` 等其余 dist_data 模块零改动（阈值、门值、
  投影/遮挡/split 算法层结构性未动，实测 diff 为空）。
- **方法**：一次性复核副本 `git worktree add --detach … 994ab7c`。区间全部
  9 个 commit 逐个核对角色边界（两个实现批只触碰代码+证据+状态板本 ID 行；
  接受/复核/正式执行批只改文档，实测 per-commit 文件清单）；5 个
  PLAY_GOVERNING 文件全文精读 + 全部 hunk 逐条读完；BC-DATA-25 §33.2 六款、
  SP22-1/SP22-2 逐条对照生产代码；行为疑点写探针（副本 + scratchpad，收工
  随副本删除）。文档侧 8 个文件按角色归属抽查。
- **测试树哈希**：23 个 focused 测试文件（`tests/test_dist_data_*.py`）串接
  SHA-256 `aaeeccd18e395f1fa4f86cb529a655d82299418522b735f392ca9534ead587eb`。

### 1. 复核自跑的证据（不信报告数字，全部重跑）

| 项 | 实测 | 与声明比对 |
|---|---|---|
| focused（主树，python3 3.14.6） | **Ran 432 OK, skipped=9** | ✓ §19.4 逐字 |
| focused（主树，`.venv-yoloe` 3.12.13） | **Ran 432/432 OK 零 skip** | ✓ §19.4 逐字 |
| focused（副本，无归档，双解释器） | **均 432 OK (skipped=46)**，零 error | ✓ 轮 5 副本形态口径延续 |
| SP22 修复前红（副本内 tools@`db0c2ec` × 候选测试） | **恰 1 FAIL + 1 ERROR**：`…record_the_actual_input_artifact_refs` `AssertionError: Lists differ: [] != [{'artifact': 'inventory', …]`；`…publish_failure_leaves_shards_and_fails_closed` `OSError: [Errno 66] Directory not empty: ….staging -> …shards`；其余 6 条组合工件测试在修前 tools 上仍绿；恢复候选后副本零残留 | ✓ §19.3 两条红逐字对应；轮 22 「原有六条无一检查 lineage」属实 |
| 正式根状态（主树只读） | 恰 3 件工件 `contract`/`inventory`/`layout` @attempt-1；字节 **5,014 / 28,574,739 / 2,220,725** 与轮 20 执行收据逐一相等；mtime 停在 2026-08-28；全根 **零** `shards/`、零 `.staging/` | ✓ §19.4「一字节未动」与「无 shards/staging」 |
| 行序前提（§18.2 声称「实测」） | `build_inventory.py` records 按 path 升序排序、`build_catalog.py` objects 按 `object_id` 升序排序，两处均实存；`assign_splits_streaming._rows()` 的逐行断言兜底为真实 fail-closed 路径 | ✓ |
| gzip OS 字节（§18.1 声称「实测恒 255」） | 双解释器 `mtime=0` 下第 10 字节均 **255** | ✓ |
| 组合工件层五条 §33.3 具名回归 + SP22 两条 | 逐条通读判据：weakref 释放 >90%、孤立 staging 保留+拒重用、SP22-2 rename 窗口逐字节快照不变、tamper 四形态+恢复可读、幂等/异字节、lineage 逐字段 + sha 绑盘上 manifest；生产常量 64 MiB 另有钉死用例 | 判据真实，覆盖见 F20 例外 |

**BC-DATA-25 §33.2 逐款核对**：(1) 逻辑行/字段/顺序/计数语义在 S3/S4 保留
（S3 生成器逐 inventory 记录产同一 entry，S4 角色行四字段与整表基准全等由
测试钉死并自查代码属实）；(2) S3/S4 各仍恰一个 manifest/`ArtifactRef`，
shard 上限 64 MiB、单行超限独占一 shard（`would_overflow` 仅在非空时触发，
自查成立）、gzip 固定 `mtime=0`/level 9/OS 255；(3) manifest 含 storage
版本、**inputs（SP22-1 修后来自同一次生产读取：S3 = `_read_ref` 的
inventory+layout ref，S4 = `CatalogStream.reference`，无按路径重建旁路，
全仓 grep 核实）**、有序 shard 表全字段、`row_count`、`stream_sha256`，
`ArtifactRef.sha256` 哈希 manifest 且 manifest 递归哈希 shard；(4) S4 摘要
留 manifest payload、角色行进 shards、下游只经 `read_composite_rows`/
`CatalogStream` 取数（生产内无直接 shard 路径依赖，grep 核实）；(5) S3 写侧
一次只持有一个 shard 字节 + 当前 entry（`_flush` 后 blob 出作用域），S4 三遍
扫描只驻留帧 id/pHash/atom 摘要/对象 id 集合，S5–S8 取数全部改走同一
`CatalogStream`——**但派生物驻留见 F21**；(6) manifest 为唯一提交点：
`os.link` 不覆盖原子发布、`attempts()` 以 manifest 存在为准、**两种无
manifest 残留（`.staging/` 与 post-rename `shards/`，SP22-2 修后）都在写
任何新字节之前 `IncompleteCompositeArtifactError`**、中断不清理、幂等重放
不写文件、异字节 `CreateOnceError`。读路径逐 shard 校验 SHA/压缩/未压缩
字节/行数 + 末尾 `row_count`/累积哈希；全部消费点均完整迭代（逐个核对
S4 三遍、S5、S6、S7 内 5 处、S8、测试 `list()`），生成器尾校验不被跳过。

### 2. Findings（续编号；CLASS_1/2 → REWORK_REQUIRED）

**F20（CLASS_1，`tools/dist_data/run_pipeline.py` `stage7_gate` ×
`tools/dist_data/g0_report.py`）：S7 流式化切断 `split` 侧信道，冻结指标
F2 与分层分母被静默归零。** 旧实现中 `catalog["entries"]` 是同一批可变
dict：`stage7_gate` 先循环打上 `entry["split"] = split_of_frame.get(…)`，
`build_g0_report(entries=catalog["entries"])` 随后读到的是**带 split 键**的
同批对象。流式化后 `build_g0_report(entries=stream)` 的每次迭代都由
`json.loads` 产出**新对象，无 split 键**：`compute_f2` 的
`entry.get("split") not in SPLITS → continue` 使 `global_keys`/`per_split`
永不累加，`stratified_denominators` 的 `frames_by_split` 把全部帧计入
`"None"`，`station_clustering.keys`（= `f2["station_keys"]`）恒空。副本内
探针实证（同一合成夹具、同一 S1–S4 工件）：流式生产路径写出的 g0_report
为 `F2 = {global: 0, per_split 全 0, station_keys: []}`、
`frames_by_split = {"None": 8}`；同批 entries 按修前语义打键后同一
`compute_f2` 得 `F2 = {global: 4, per_split: {dev: 4, test: 4}}`、
`frames_by_split = {test: 4, dev: 4}`。F1–F4 是 round 3 冻结的 G0 门指标
（F2 floor `min_global 40 / min_test 8`）：真实归档上本可达标的 F2 被无条件
判 0，gate 恒 `INSUFFICIENT`，g0_report 工件数字错误。F1/F3/F4 不受影响
（各自经 `field_catalog`/`frozen` 候选表取 split，路径独立核实）。候选内
`for entry in stream: entry["split"] = …` 已成死赋值（`frame_world`/
`prospective_mother_eligible` 不读该键，grep 核实）。**测试缺口同属本条**：
§33.3 第四条具名回归要求「S4–S8 现有小世界输出/终态与修前逐字义等价」，
现 `test_streamed_consumers_match_legacy_small_fixture_s4_to_s8` 对 S7 只
断言 `gate == INSUFFICIENT` 与 `unmet_floors == [F1..F4]`——小夹具下修前
同样四条全不达标，g0_report 输出本体从未与修前比对，缺陷恰好穿过。
闭合绑定回归：生产路径 fixture 需让修前语义下 F2 非零，断言流式
`stage7_gate` 产出的 g0_report 的 `floors.F2`（数值与 `station_keys`）与
`stratified_denominators.frames_by_split` 与修前逐字义等价；修复前该测试
必以 `0 != 非零` 失败。

**F21（CLASS_2，`run_pipeline.py` S5/S6/S7/S8 消费点）：随帧数线性增长的
全量物化未证有界，「生产消费全程有界」（§33.2 (5) 款首总则）在 S5 尚无
证据成立，而 S5 在下一步已声明的正式 S3–S5 续跑路径上。** 逐处实测：
`stage5_field_catalog` 把全部 `(frame × status OK 且 visible_px 非 None
对象)` 物化成 `observations` list 后整表传 `build_field_catalog`（真实
归档上界 23,549 × 779 ≈ 1.8×10⁷ 条，每条 ~300–400 B 对象开销；真实可见
数未知——正式 S3 从未跑完，无实测）；`audit_strata`（S6）物化全部
(frame × OK 车辆) 深度样本；`stage7_gate` 物化 `candidates`；
`stage8_mother_set` 物化全部 (frame × amodal 非 None 对象) 的
`amodal_box_of`（S8 量级最重）。合同 (5) 对 S5–S8 的分句只要求「改走同一
类型化迭代器」——这一点已做到，本条不指控该分句——但款首「生产消费全程
有界」是规范性总则，且本 work item 的 R21 立项恰因「量级估计错误 →
S3 OOM SIGKILL」。S5 现驻留远小于修前 S3 整表（每条 ~350 B vs 238 KiB/
entry，估算比 ~1:700），16 GiB 主机大概率可过，但这是**推算不是证据**，
与 §18.5 的推算同一性质。证据 §18.2「`CatalogStream` 不支持下标——正是
为了让任何试图物化全集的写法直接失败」的说法过强：下标之外的物化路径
（逐行 append 派生物）畅通，S5/S8 实际正在这样做。闭合二选一，由接受角色
裁定：(a) S5 改为逐对象有界累积（如按 `camera_depth_m` 的逐对象 top-K
维护，驻留 O(对象数 × K)），绑定生产路径回归断言驻留量与帧数解耦；或
(b) 接受角色以量化裁定接受现驻留为「已披露的推算风险」，把 S5 峰值内存
列入续跑授权前的未验证风险清单并在正式续跑首次执行时实测记录——(b) 为
`NOT_MECHANIZABLE`，闭合改定点复看续跑授权条款与证据披露段。S6–S9 的
同型物化随其执行授权另行处置，本条如实记录不预授权。

**F22（CLASS_2，`docs/evidence/P1-VLM-DATA-001-implementation.md` §18.2 ×
`tools/dist_data/make_splits.py`）：「`assign_atoms()` 从 `assign_splits`
抽出，供流式与整表两条路共用同一实现，保证 split 语义逐字相同」与代码
不符；§19.5 (3)「（被反证措辞）本轮只发现这一处」随之不成立。** 实测
diff：`assign_splits` 本体在 `33537f8..994ab7c` 一行未动，`assign_atoms`
是**新增的第二份复制实现**；两条路各自独立执行同构逻辑（floor 过滤 →
`choose_test_atoms` → D3 → `split_dev` → 连带规则 → 泄漏断言，本轮逐行
比对当前两份语义等价），等价性由
`test_streamed_splits_preserves_all_sample_roles_and_exposure_counts`
（小夹具、整表 `assign_splits` 作基准）维系，**不是结构保证**。「共用同一
实现」是等价论证的机制性主张，与 SP22-1 同形态（证据声称的机制在生产中
不存在）；读者据此会把漂移风险评为零并缩小未来修改的检查范围。生产路径
现只调 streaming 侧，整表 `assign_splits` 仅存于测试基准，方向上任何单侧
改动都会被等价测试拦截（前提：夹具触达改动路径），故不升 CLASS_1。闭合
二选一：(a) 代码收敛——`assign_splits` 真正改为调用 `assign_atoms`（现有
等价回归即为绑定测试，修复批照常入下一轮 diff）；或 (b) 证据措辞如实
改为「两份平行实现 + 等价回归兜底」，并同步修正 §19.5 (3) 的唯一性
表述——(b) 为 `NOT_MECHANIZABLE`，闭合改定点复看 §18.2 与 §19.5。

### 3. CLASS_3（不阻断；逐字替换补丁，交接受角色复判后应用）

本轮无。

### 4. 观察项（不分级，不阻断，随返工顺带处置即可）

- `write_composite` 不校验 `stage` 形参与 `STAGES[artifact]` 一致
  （`write()` 有该校验）；生产两处调用都不传（走默认），且禁行边判定
  始终以 `STAGES` 表为准（`read()` 自派生），无实害，接口不对称而已。
- `assign_splits_streaming` 行序断言用严格 `<`：完全相等的重复
  `(frame_id, object_id)` 行不会被拦（上游 S1 路径唯一 + entry 内对象
  唯一另有保证；改 `<=` 语义更强，顺带即可）。
- 同一 attempt 的并发 `write_composite` 会共享 `.staging/`（残留检查到
  mkdir 之间无锁）；单进程 driver 下不触发，同输入下分片字节确定性一致，
  最坏方向为 rename/link 失败 fail-closed，不静默产错件。
- gzip 分片字节幂等依赖 zlib 实现稳定：跨 zlib 版本重放同输入可能
  `CreateOnceError`（假阳、fail-closed 方向）；`stream_sha256` 在未压缩域
  不受影响。钉死解释器环境下非问题，记录备查。
- published 幂等重放路径会完整重算整条 rows 流（S3 = 全部投影+truth
  join 重做一遍）后才比对 manifest 字节；行为正确、开销一次全量计算。
- `build_g0_report` 内对 entries 迭代 5+ 次（`station_of_frame`、F2、
  分母表 4 处、排除直方图、共视分布），流式后每次都全量重解压 shard；
  S7 未授权执行，正确性无碍，续跑到 S7 前值得合并遍数。
- `run_pipeline._frame_index` 为既有死代码（`bind_layout` 自有一份并
  使用），非本批引入，随手可删。

### 5. `UNITY_NA` 分类：**对本候选增量附议，累计维持（轮 1–6）**

本轮 PLAY_GOVERNING 增量仍仅 `tools/dist_data/` 与
`tests/test_dist_data_*.py`；`controller/`、`Assets/`、`config/`、
`ProjectSettings/`、`Packages/packages-lock.json` 与运行时协议零改动
（实测 diff）；正式根三件工件字节对账一致，测试进程不触碰正式根
（`test_tests_never_write_the_formal_artifact_root` 逐路径 SHA 快照自证，
主树双解释器实跑通过）。附议条件不变：越出纯离线范围即失效。

### 6. Verdict

**`REWORK_REQUIRED`**（round 6，候选 `994ab7c`，接受轮 23 停点）。

- F20（CLASS_1）：S7 流式化静默改变冻结指标 F2 与分层分母的产出，副本内
  同夹具实证 `0 vs 4`／`{"None": 8} vs {test: 4, dev: 4}`；等价回归对
  g0_report 输出本体的缺口一并闭合。
- F21（CLASS_2）：S5（在下一步续跑授权路径上）及 S6–S8 的线性全量物化
  未证有界，处置方式（改造或量化披露裁定）交接受角色。
- F22（CLASS_2）：证据 §18.2「共用同一实现」与代码不符，§19.5 (3) 的
  唯一性表述连带不成立；收敛代码或改正证据二选一。
- 修复回到同一 §4.3.1 停点；SP22-1/SP22-2 本轮确认闭合（修复前红逐字
  复现 + 生产代码逐款核对），BC-DATA-25 其余各款在交付代码上零违反；
  focused 四种形态、正式根、修复前红全部独立复现。是否开轮 7 由修复批
  的 PLAY_GOVERNING diff 决定（F20 必触 `run_pipeline.py`/测试，按
  COORD-007 R1 必然非空；F20 不触 Play 治理门三文件，无闭环轮义务）。
- 边界自查：本会话未修改主工作树任何实现文件；探针（F20 对照、SP22
  修复前红、gzip/排序前提验证）只存在于 scratchpad 与一次性复核副本，
  副本已随 `git worktree remove --force` 删除。

---

## Round 7 — 2026-09-01

### 0. 候选、开轮资格与方法

- **候选**：`97b57c62da714b768f1d4c6b2e96fad44910bf43`（接受轮 24 返工批
  `8c71900` + 接受轮 25 窄修批，接受轮 26 确认停点）。候选 tree
  `9a65cb609066f7183c899b4e0708c392aab13c77`。其后 HEAD `72053df`（接受轮
  26）相对候选 PLAY_GOVERNING diff 0（实测），主树代码与候选字节相同。
- **开轮资格（COORD-007 R1）**：上一通过候选由本文件最近一行
  `passed_candidate` 派生 = `33537f8`（轮 6 为 `REWORK_REQUIRED`，无指针）。
  运行时派生范围 `git diff 33537f8..97b57c6` 于 PLAY_GOVERNING 上 7 个文件
  非空；其中 `33537f8..994ab7c` 段（5 文件）已由轮 6 全文精读并给出
  verdict，本轮维持其结论并把精读重点放在增量 `994ab7c..97b57c6`（4 文件：
  `tools/dist_data/run_pipeline.py` ±105、`build_catalog.py` ±50、
  `make_splits.py` ±51、`tests/test_dist_data_round24.py` +401），同时核对
  增量区间 `g0_report.py`/`contract.py`/`bind_layout.py`/`artifacts.py`
  零改动（实测 diff 为空——F2 阈值、g0_report schema、组合工件层未动的
  机械证明）。`controller/`、`Assets/`、`config/`、`ProjectSettings/`、
  `Packages/packages-lock.json` 全区间零改动。
- **方法**：一次性复核副本 `git worktree add --detach … 97b57c6`。区间 5 个
  新 commit 逐个核对角色边界（返工批 4 个 + 窄修批 1 个 governing 文件，
  三个接受轮零 governing 文件）；增量 4 文件全文/全 hunk 读完；轮 24 §36
  三条 binding 条款、轮 25 §37.2 两处窄修、轮 26 §38.1 历史问句裁定逐条
  对照代码与证据；轮 6 探针在候选上重跑作独立闭合判据。
- **测试树哈希**：24 个 focused 测试文件串接 SHA-256
  `b1134429780dc1b785ec5873b7f7802f754dd179ea46bc5a6dbe4aa49de01d12`。

### 1. 复核自跑的证据（不信报告数字，全部重跑）

| 项 | 实测 | 与声明比对 |
|---|---|---|
| focused（主树，python3 3.14.6 / `.venv-yoloe` 3.12.13） | **435 OK, skipped=9** / **435/435 OK 零 skip** | ✓ §20.5/§21.3 逐字 |
| focused（副本，无归档，双解释器） | **均 435 OK (skipped=46)**，零 error | ✓ 副本形态口径延续 |
| round-24 三条具名回归（主树） | **3/3 通过** | ✓ 轮 26 复现一致 |
| 三条修复前红（副本内 tools 三模块 @`994ab7c` × 候选测试） | **恰 3 FAIL**，断言原文逐字：`0 != 4 : floors.F2.global`；`64 not less than or equal to 21`（有界性断言，等价断言未红——「改驻留不改输出」属实）；`1 != 2`（assign_atoms 只被调 1 次） | ✓ §20.4 与轮 25 §37.1 (2) 逐字对应 |
| 轮 6 F20 探针在候选上重跑（独立于 round-24 测试） | 生产 `stage7_gate` 写出的 g0_report 与修前打键语义**逐字段相等且非零**：F2 `{global: 4, per_split: {dev: 4, test: 4}, station_keys: 4 键}`、`frames_by_split {dev: 4, test: 4}`（轮 6 时为 `0` / `{"None": 8}`） | ✓ F20 闭合的独立实证 |
| 修前 `build_field_catalog` 转写忠实性 | 测试内 `_legacy_whole_table_field_catalog` 与 `994ab7c:build_catalog.build_field_catalog` 逐行比对：分组、`sorted(...)[:K]`、crop/`_inset`/`estimate_color`、组一致性、五个输出键全部逐字义一致 | ✓ 基准不是流式自证 |
| 正式根（主树只读） | 仍恰三件 `contract`/`inventory`/`layout`@attempt-1，字节 **5,014 / 28,574,739 / 2,220,725** 与轮 20 收据相等；零 `shards/`、零 `.staging/` | ✓ §20.5/§21.3 |
| `git diff --check`（全区间） | 干净 | ✓ |

### 2. 三条 finding 的闭合逐条核毕

**F20（CLASS_1）——确认闭合。** `SplitDecoratedStream` 把 split 变成流本身
的属性：每次 `__iter__` 都用 S4 派生的同一份 `split_of_frame` 逐条装饰
`CatalogStream` 产出的新 dict，装饰逐条完成、不物化全集；`__len__` 透传
manifest `frame_count`（`exclusion_histogram` 的 `frame_total` 因此不变）。
`stage7_gate` 内全部三处 entries 消费（`atom_of_frame`、candidates 循环、
`build_g0_report(entries=stream)`——后者内部 `station_of_frame`、F2、分母表
4 处、排除直方图、共视分布共 5+ 遍）都走装饰流；原死赋值
`entry["split"] = …` 已删除；`split_of_frame` 全 S7 只此一份，与
`freeze_mother_candidates` 同源。dropped 帧 `get()` 返回 None 的语义与修前
一致（F2 continue、分母计 `"None"`）。绑定回归走生产路径、以修前打键语义为
基准、带夹具强度断言（修前 F2 必非零）并逐字段比对 `floors.F2`（含
`station_keys`）、`station_clustering.keys`、`frames_by_split`（含 NotIn
`"None"`）——恰好补上轮 6 指出的等价测试缺口。修复前红 `0 != 4` 复现；
`g0_report.py` 零改动证明 F1/F3/F4、F2 阈值与 schema 未动。

**F21（CLASS_2）S5 支——确认闭合；S6–S8 留债处置附议。**
`BoundedObservationSelector` 与修前 `sorted(...)[:K]` 的逐条等价成立：排序
键 `(camera_depth_m, frame_id)` 在同一对象内唯一（一帧一对象至多一条），
`bisect.insort`（right 语义）平局右插与稳定排序同向，满 K 快捷丢弃分支
`key >= kept[-1][0]` 丢新保旧与截断路径一致，`candidates()` 保序；驻留上界
`O(对象数 × K)` 与帧数解耦。`build_field_catalog` 入参改 `Iterable` 且只
迭代一次；driver 两遍扫描各自有界（第 1 遍纯对象 id 集合、一条 observation
不构造；第 2 遍生成器逐条交选择器），两遍共用唯一过滤定义
`_color_observation_rows`。K、排序/平局、对象域、crop、颜色估计、payload
字节全部不变（逐行 + 逐字段等价回归 + 修前红只红有界性断言三重印证）。
绑定回归的夹具有区分度（每对象 16 > K=5、四帧一深度档、`assertNotEqual`
按帧序 naive 前 K）；`weakref` 峰值计数 patch 的正是生产路径构造点
`build_catalog.ObjectObservation`，上界 `object_count × K + 1` 的 `+1` 对应
正在传递中的一条，且 `constructed > bound` 断言保证可证伪。修复前红
`64 not <= 21` 复现。**S6/S7/S8 的同型物化未修**：按轮 24 §36.2 登记
`DEFERRED_BOUNDEDNESS_DEBT_BEFORE_STAGE_AUTHORIZATION`，证据 §20.2、状态板
与 `implementation-status.md` 三处一致，全文排查零「债务清零/全部闭合」类
残留表述——该处置在轮 6 F21 给出的选项域内且方向 fail-closed（授权前
阻断），**附议**。

**F22（CLASS_2）——确认闭合。** `assign_splits()` 现调用
`assign_atoms(atoms)` 为 atom 指派、连带规则与泄漏断言的唯一实现，平行
复制段整体删除（diff 实测）；`dropped_frames` = `base["dropped"]`（原
`sorted(set(dropped))` 同值）、`d3_holdout_empty` = `not assignment[SPLIT_D3]`
（原 `d3_atom is None` 同值），其余输出字段不变。结构回归以 spy 证明两条
生产路径各调共享实现恰一次，并以 `assertIs` 断言输出与那次共享计算**对象
同一**（防同构复制回潮），另钉七个非角色键等价；修复前红 `1 != 2` 复现。
文证纠正到位：§18.2 S4 条删除线保留原句并标注「在 §18 当时的候选上不成立
……由接受轮 24 的 F22 返工才真实成立」，§19.5 (3) 的唯一性表述以删除线
撤回并说明撤回的是判断而非 §18.1 那次改正。

### 3. 轮 25 窄修与轮 26 历史问句裁定的独立复判

- **两处窄修核毕**：`CatalogStream` docstring 现为精确事实（只强制经校验
  迭代接口取数；缺下标不阻止物化派生全集并点名轮 6 F21 反证；有界性逐
  消费点证明；S5 已闭合、S6–S8 债在授权前阻断）——与 §37.2 (1) 逐点
  吻合；§18.2 末条删除线 + 历史标注 + 「不得写成全部闭合」——与 §37.2
  (2) 吻合。零行为/测试/工件变化（窄修批 governing diff 仅该 docstring）。
- **§38.1 裁定附议**：§18.6 (3) 原文为问句、位于旧候选「给复核角色的复核
  范围」节，其权威答案就是本文件轮 6 F21；全仓排查该句的全部出现处
  （§18.6 原文、§21.2 讨论、docstring 修正）均为历史或否定语境，无一处
  把它引作现行肯定主张。保留问句正确——静默改写反而会抹掉 F21 的发现
  来源。附议 `THIRD_SITE_HISTORICAL_QUESTION_NONBLOCKING`。

### 4. Findings

**无新增阻断 finding。** F20、F21（S5 支）、F22 全部确认闭合（每条有独立
复现的修复前红 + 修复后绿 + 我自己的探针/逐行等价论证）；轮 24 §36.4 边界
零违反（七条轮 6 观察项一条未被顺手改动，实测 diff 范围恰为三模块 + 一个
新测试文件 + 证据/状态板）；S6–S8 债务登记三处一致。CLASS_3 无。

### 5. 观察项（不分级，不阻断，随后续批次处置即可）

- `SplitDecoratedStream` 不透传 `manifest`/`reference` 属性：当前 S7 无
  调用点，若未来消费者经装饰流取 lineage 会 `AttributeError`（fail-closed
  方向）；需要时补两行透传即可。
- S5 两遍扫描 = 两次全量 shard 解压（第 1 遍只为对象域）；实现者已在
  §20.6 (5) 自行披露，正确性无碍，续跑授权前可考虑合并遍数（属性能，
  不属本轮义务）。
- 轮 6 观察项 7 条维持原状（本轮范围明确排除，未处置不算违反）。

### 6. `UNITY_NA` 分类：**对本候选增量附议，累计维持（轮 1–7）**

本轮 PLAY_GOVERNING 增量仍仅 `tools/dist_data/` 三模块与
`tests/test_dist_data_round24.py`；`controller/`、`Assets/`、`config/`、
`ProjectSettings/`、`Packages/packages-lock.json` 与运行时协议零改动
（实测 diff）；正式根三件工件字节不变，零 shards/staging，测试进程不触碰
正式根（逐路径 SHA 快照断言在 focused 内实跑通过）。附议条件不变：越出
纯离线范围即失效。

### 7. Verdict

**`PASS_WITH_NOTES`**（round 7，候选 `97b57c6`，接受轮 26 停点）。

- 轮 6 的 F20/F21（S5 支）/F22 全部确认闭合；S6–S8
  `DEFERRED_BOUNDEDNESS_DEBT_BEFORE_STAGE_AUTHORIZATION` 登记附议——它是
  显式的授权前阻断债，不是闭合；BC-DATA-25 在交付代码上此外零违反。
- 头条数字全部独立复现：focused 四种形态（435/9、435/0、435/46×2）、
  round-24 3/3、三条修复前红逐字、轮 6 探针翻绿、正式根字节、
  `git diff --check`。
- work item **不因本轮关闭**：正式 S3–S5 续跑须经 Acceptance 消费本 verdict
  后由用户另行授权；S6–S9/G0/D0、audit、supersession、依赖/模型/API/GPU/
  Play/ID 与后续训练全部继续未授权；S6–S8 执行授权草案须先回接受角色闭
  boundedness 债。
- passed_candidate: 97b57c62da714b768f1d4c6b2e96fad44910bf43
- 边界自查：本会话未修改主工作树任何实现文件；探针（F20 对照重跑、三条
  修复前红、转写比对）只存在于 scratchpad 与一次性复核副本，副本已随
  `git worktree remove --force` 删除。

## Round 8 — 2026-09-02

### 0. 候选、开轮资格与方法

- **候选**：`4739a3965a793dd6017bcc18bf10abe96575348a`（接受轮 29 返工批
  BC-DATA-26，接受轮 30 确认停点）。其后 HEAD `fdf8fd9`（接受轮 30）相对
  候选 PLAY_GOVERNING diff 0（实测），主树代码与候选字节相同。
- **开轮资格（COORD-007 R1）**：上一通过候选由本文件最近一行
  `passed_candidate` 派生 = `97b57c6`（轮 7）。运行时派生范围
  `git diff 97b57c6..4739a39` 于 PLAY_GOVERNING 上恰为 2 个文件：
  `tools/dist_data/make_splits.py`（±84）与新增
  `tests/test_dist_data_round29.py`（+379），与接受轮 30 §42.1 (1) 的声明
  一致；`controller/`、`Assets/`、`config/`、`ProjectSettings/`、
  `Packages/packages-lock.json` 与 `tools/dist_data/` 其余模块全区间零改动
  （实测 diff——`run_pipeline.stage4_splits`、S7 消费点、`contract.py`
  阈值、`artifacts.py` 组合工件层未动的机械证明）。
- **方法**：一次性复核副本 `git worktree add --detach … 4739a39`。区间 5 个
  新 commit 逐个核对角色边界（governing 文件只出现在实现返工批 `4739a39`；
  接受轮 28/29/30 与正式执行批均为纯文档）；两个 governing 文件全文读完；
  §41.3 五条 binding 条款与 §42.2 五点核对清单逐条对照代码；修复前红在
  副本内独立重建；另以自写探针对冻结正式 S4 manifest 做只读重放对照
  （见 §3）。
- **测试树哈希**：25 个 focused 测试文件串接 SHA-256
  `fd27aa067f854ae6155b7eaf512ec2456b9180ebbc9d72420974d087e8611ce2`。

### 1. 复核自跑的证据（不信报告数字，全部重跑）

| 项 | 实测 | 与声明比对 |
|---|---|---|
| focused（主树，python3 3.14.6 / `.venv-yoloe` 3.12.13） | **437 OK, skipped=9** / **437/437 OK 零 skip** | ✓ §23.4/§42.1 (2) 逐字 |
| focused（副本，无归档，双解释器） | **均 437 OK (skipped=46)**，零 error | ✓ 副本形态口径延续（轮 7 同 46 skip） |
| 两条 round-29 具名回归（副本，候选态） | **2/2 通过** | ✓ 轮 30 复现一致 |
| 修复前红（副本内 `make_splits.py` 换回 `97b57c6` × 候选测试，`.venv-yoloe`） | **恰 2 FAIL**，断言原文逐字：`True is not false : S4 摘要仍携带全量 near_duplicate_pairs（随合格 pair 数二次增长的成员；修前实测 540000 对被整份驻留并写出）`；`False is not true : S4 摘要缺少 near_duplicate_union_witnesses（修前生产代码只有全量 pair 列表）` | ✓ §23.2 引文逐字；第一条正是 §41.3 (4) 的「全量列表」断言红 |
| 恢复候选后重跑 | **2/2 转绿**，副本树干净 | ✓ |
| 正式根（主树只读） | **92 文件**；S0–S2 三件 `contract`/`inventory`/`layout`@attempt-1 字节 **5,014 / 28,574,739 / 2,220,725** 与轮 7 收据相等；正式 S4 manifest 磁盘 **515,074,557 B** | ✓ §23.3/§42.1 (4) |
| `git diff --check`（全区间） | 干净 | ✓ |

全套 972 未重跑：按 workflow §4.4，全套是实现者停点证据（§4.3.1 条件 2）
的义务，不是复核开轮义务；实现者与接受轮 30 双方数字（972，仅既有两项
CSRT/opencv-contrib 失败）已记录在案。

### 2. §42.2 五点与 §41.3 五条 binding 逐条核毕

1. **witness 在 union 前判定；count 不被缩减——成立。** 生产循环内
   `pair_count += 1` 位于 hamming 条件内、witness 条件外，与修前
   `near_duplicate_pairs.append` 完全同位（同族 `continue` 与
   `hamming ≤ PHASH_NEAR_DUPLICATE_HAMMING` 判定逐字未动）；随后
   `union.find(family_left) != union.find(family_right)` 判定严格先于
   `union.union`，仅首次连接对进入 `witnesses`。合格 pair 的全量计数与
   witness 记录条件因此结构性解耦。`itertools.combinations(sorted(...))`
   产出的 `(left, right)` 序列即全局字典序，遍历序与修前相同。
2. **`replay_union_witnesses` fail-closed——成立。** 四条拒绝分支齐备：
   非二元组、未知帧、同族 pair、冗余 pair（同族与已同分量合在一个条件里，
   同族时两侧 `find` 必相等，语义覆盖正确）；任一触发即 `SplitError`，无
   静默跳过。`merge_atoms` 的两条不变量自检（witness 数 =
   `family_count − atom_count`；同序重放重建相同 atoms）在唯一装配点的
   `return` 之前执行，生产路径（`stage4_splits` 行 338 唯一调用）无绕过
   路径。测试覆盖冗余/同族/未知帧三条拒绝分支（修前红 + 三个
   `assertRaises`）。
3. **修前转写忠实；components→atoms 等价——成立。** 测试内
   `_legacy_merge_atoms` 与 `git show 97b57c6:tools/dist_data/make_splits.py`
   的 `merge_atoms` 逐行比对：families/union/frames 初始化、循环结构、同族
   `continue`、hamming 条件、`union+append`、components 装配、
   `atom_id_for(members): sorted(members)`、键升序返回与三键 dict 全部逐字
   义一致（仅模块前缀引用差异）——基准不是新实现自证。新抽出的
   `_atoms_of` 与修前表达式同义（`setdefault(find).append` →
   `atom_id_for: sorted` → 键升序），两处调用共用。6 族夹具含传递并簇与
   冗余合格 pair（legacy count 恰 9），count/分量/atom_id 与 legacy 逐字
   相等，witnesses 恰等于对 legacy 全量 pair 列表同序机械抽取的「首次
   连接」子序列（`_first_connecting_pairs` 独立实现），每个 witness 显式
   断言跨族且 Hamming ≤ 8；5 种乱序输入输出与 canonical 字节均不变。
4. **生产 S4 manifest 有界——成立。** 函数级：4 族 ×50/×300 帧全同
   pHash，count 恰 15,000/540,000（帧 ×6 → pair ×36 的二次增长被机械
   证明），摘要无 `near_duplicate_pairs`、witness 数 = 4 − 1、任何列表
   长度 ≤ family 数、canonical 字节 15,000→540,000 对仅允许 count 位数
   变化（≤ +8 B）。生产路径：三族世界经真实 `stage3_frames_catalog()` →
   `stage4_splits()`（DriverCase 临时根 + 真实 create-once 写盘，fixture
   由生产路径产出），正式写出的 manifest 无 pairs 成员、count 恰 1,600、
   witness 1 = 3 − 2、经 S3 行流重放等价、atoms 块 < 4 KiB。
5. **除 pair 调试载荷外零语义改动——成立。** governing diff 唯二文件；
   `make_splits.py` 内 diff 只触及 `merge_atoms`/新增 `_atoms_of`/
   `replay_union_witnesses`，assign/held-out/exposure/leakage 及全部其他
   函数零改动；`run_pipeline.py` 零改动（manifest `atoms` 块仍原样写入
   `merge_atoms` 返回值，S7 仍只读 `splits["atoms"]["atoms"]`）。manifest
   payload 其余 15 个成员的增长维度实测为帧数/对象数/族数/shard 数，无
   按合格 pair 数增长的成员被漏报（§23.5 (5) 核毕）。全仓 `tools/`、
   `tests/` 中 `near_duplicate_pairs` 除 `make_splits.py` 与本轮新增回归
   （刻意的 legacy 基准）外零引用，「零生产消费者」独立证实。

### 3. 冻结正式 S4 manifest 的只读重放对照（独立复现 §23.3）

自写探针（scratchpad，副本代码 + 主树数据只读，`.venv-yoloe`）：

| 量 | 实测 | 与 §23.3 比对 |
|---|---|---|
| 冻结 manifest | 3 atoms；`near_duplicate_pair_count` 2,663,282 = `len(pairs)`；pair 列表**严格字典序**、**零同族对** | ✓ |
| S3 行流（生产 `read_composite_rows`，逐 shard 校验） | 23,549 帧、**8** family | ✓ |
| 首次连接子序列（自实现 union-find 抽取） | **5** = 8 − 3；家族对逐一为 m3-armA~detect-scout1、m3-armA~rate、s004-qual~s004-smoke、s004-qual~s004-scout、rate~scene-val | ✓ 五对具名逐字 |
| 生产 `replay_union_witnesses` 重放 | 重建 atoms 与冻结 manifest `atoms` **逐字相等** | ✓ |
| atoms 块 canonical 字节 | **512,888,212 → 1,247**（count 原样保留） | ✓ |
| 代价 | 37.8 s，maxrss 2.94 GiB（全量 pairs 解析所致——CLASS_2 归因的消费者驻留带独立复证） | ✓ 同量级 |

字节口径的精确分解（供后续引用者，见观察项 2）：磁盘上外层 atoms 块
**值**的跨度恰为 **512,888,211 B**，其中 `near_duplicate_pairs` 键+值
512,887,863 B（99.99993%）、内层 `atoms` 值 301 B、count 成员与分隔符
其余；canonical 化整块 512,888,212 B。正式根前后 92 文件未动（探针
只读），现有 S4 manifest 仍为 create-once 原样，本轮未 supersede。

### 4. Findings

**无新增阻断 finding。** BC-DATA-26 五条 binding 全部成立（每条有独立
复现的修复前红/修复后绿、逐行转写比对或结构性论证）；§41.3 (5) 范围边界
零违反（governing 恰两文件，S5 lineage 债未顺带改，正式工件未动）；区间
5 个 commit 角色边界干净（授权账本条目、design v0.3.29 增量、
implementation-status 三段增量与提案轮 28–30 逐一对应；上界报告标题/
摘要/上界表全带「审计前上界、非门 verdict」且四个 U 值均
`NOT_EVALUATED_PRE_AUDIT`）。CLASS_3 无。

### 5. 观察项（不分级，不阻断，随后续批次处置即可）

1. `replay_union_witnesses` 的 `len(pair) != 2` 拒绝分支无测试覆盖（其余
   三分支有修前红或 `assertRaises`）；另外长度恰为 2 的字符串可通过该
   检查后由未知帧分支拦截——JSON 反序列化产物必为 list，纯理论缝隙。
2. 「512,888,211 B」在上界报告 §6 与 SP29-1 中被表述为
   `atoms.near_duplicate_pairs`「单项」——实测该数是外层 atoms 块值的
   磁盘整体跨度（pairs 键+值实占 512,887,863 B，差 348 B 为同块 count 与
   内层 atoms 成员）。归因结论不受影响（pairs 占块 99.99993%）；后续
   引用建议采 §23.3 已用的 canonical 整块口径 512,888,212 B。
3. 证据 §23.1「全仓 `tools/`、`tests/` 中 `near_duplicate_pairs` 除
   make_splits 外零引用」在候选树上字面不精确：本轮新增的 round29 回归
   含刻意的 legacy 基准引用。其支撑的核心主张（零**生产**消费者）经
   独立 grep 证实为真；建议顺带精确为「除 `make_splits.py` 与 round29
   回归外」。
4. 状态板 Current state 的压缩表述「focused 437/437 on both interpreters」
   省略了 python3 形态的 9 skip（Pillow 金标）；提案 §42.1 (2) 与证据
   §23.4 记载准确，437 ran / 0 failed 为真。

### 6. `UNITY_NA` 分类：**对本候选增量附议，累计维持（轮 1–8）**

本轮 PLAY_GOVERNING 增量仅 `tools/dist_data/make_splits.py` 与
`tests/test_dist_data_round29.py`；`controller/`、`Assets/`、`config/`、
`ProjectSettings/`、`Packages/packages-lock.json` 与运行时协议零改动
（实测 diff）；正式根 92 文件未动、S0–S2 字节与轮 7 收据相等，测试
只写 `tempfile.TemporaryDirectory` 临时根（DriverCase 实读确认）。附议
条件不变：越出纯离线范围即失效。

### 7. Verdict

**`PASS_WITH_NOTES`**（round 8，候选 `4739a39`，接受轮 30 停点）。

- BC-DATA-26 的有界证明表示在交付代码上成立：研究与 split 语义（全对
  比较、阈值、并簇、`atom_id`、全量 count）逐字保留，全量 pair 载荷
  删除，witnesses 受 family 数上界约束且可重放重建，双不变量生产自检
  fail-closed；修复前红 2/2 逐字复现、修复后 2/2 绿。
- 头条数字全部独立复现：focused 四种形态（437/9、437/0、437/46×2）、
  具名回归 2/2 红→2/2 绿、冻结 manifest 重放（8 族/5 witness/3 atoms/
  512,888,212→1,247 B/count 2,663,282 不变）、正式根 92 文件与 S0–S2
  字节、`git diff --check`。
- work item **不因本轮关闭**：本 verdict 不授予正式 supersession——现有
  正式 S4 manifest 保持 create-once 原样，以新表示物化正式 S4/S5 须经
  用户另行授权的新 attempt；S5 lineage 债
  （`DEFERRED_S5_LINEAGE_DEBT_BEFORE_SUPERSESSION_OR_STAGE6_AUTHORIZATION`）
  维持授权前阻断；S6–S9/G0/D0、audit、补采集、依赖/模型/API/GPU/Play/ID
  与后续训练全部继续未授权；乐观上界低于 floors 的数据充分性事实不因
  本轮改变。verdict 先回 Acceptance 消费。
- passed_candidate: 4739a3965a793dd6017bcc18bf10abe96575348a
- 边界自查：本会话未修改主工作树任何实现文件；探针（冻结 manifest 重放
  对照、字节口径分解、修复前红）只存在于 scratchpad 与一次性复核副本，
  副本已随 `git worktree remove --force` 删除。
