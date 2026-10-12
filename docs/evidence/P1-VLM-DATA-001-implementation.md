# P1-VLM-DATA-001 实现者证据（G0 目录门 + D0 数据引擎，第 1 个实现批次）

Work ID: `P1-VLM-DATA-001`
角色：实现（implementation，本轮在 Claude Code `/implement` 备用入口执行）
日期：2026-08-26
设计合同：`docs/proposals/P1-VLM-DATA-001-grounding-data-foundation.md`
revision 2 + §14 BC-DATA-1…5（round 3 `ACCEPTED_WITH_BINDING_CLARIFICATIONS`）
授权：`docs/authorizations.md` 2026-08-26「授权进行实现」；提案 §15 划定范围。
返工轮：接受轮 4（§16）+ 轮 5（§17）+ 轮 6（§18）+ **复核轮 1** 与其消化轮
接受轮 8（§20，BC-DATA-13…19）后的第 **4** 个候选——见 **§8**（轮 4）、
**§9**（轮 5）、**§10**（轮 6）、**§11**（复核轮 1 / 接受轮 8）。

## 0. 本批次做了什么、没做什么

**做了**：`tools/dist_data/` 十四个纯离线模块 + `tests/test_dist_data_*.py`
十九个单测文件（**380** 个用例；279 → 307 → 326 → 342 → 366 → 自查后 380）。全部逻辑可在无图像库、无网络、无 GPU 的
标准库环境下运行。

**没做（授权明确排除，一件未碰）**：真实归档上的正式 S1–S8 create-once /
G0 / D0 工件生成、A1/A2/A3 人工审计、C1、教师/验证模型调用、模型下载、
API/GPU、Unity/Edit Mode/Play、scenario/session/run ID、场景或车辆修改、
`UNITY_NA` 主张、任何后续训练或确认性实验。`runtime/dist-data/` 在本批次
结束时**不存在**：所有工件写入只发生在单测的临时目录里。

`controller/`、`Assets/`、`config/`、既有运行时协议**零改动**。

## 1. 关键文件与协议

| 文件 | 阶段 | 内容 |
|---|---|---|
| `tools/dist_data/contract.py` | S0 | §2.3–§2.7/§2.11/§5 全部冻结常量；`contract_document()` 可哈希快照；F1–F4 的唯一权威副本（BC-DATA-1） |
| `tools/dist_data/artifacts.py` | 全 | create-once 存储、字节幂等、supersession 协议、**DAG 禁行边机检**、BC-DATA-2 终决排序键、不可变输入核对 |
| `tools/dist_data/roots.py` | S1 | 附录 A 闭集 pattern 表、glob→正则（`*` 不跨 `/`、`**` 跨层）、用途类资格、逐帧真值 join 表、场景/道路字节提供者 |
| `tools/dist_data/build_inventory.py` | S1 | 枚举 + **恰一匹配断言**、纯标准库 JPEG 尺寸读取、sidecar/truth join、lineage 折叠、原因码；CLI |
| `tools/dist_data/bind_layout.py` | S2 | 场景字节三级解析、逆施/正施 relocation、removal 双向语义、phantom 登记、`road_data` 字节绑定、BC-DATA-3 交叉验证；CLI |
| `tools/dist_data/project_boxes.py` | S3 | 相机（归档基向量 + 内参自洽断言）、AABB 八角点、近平面裁剪、amodal/visible 框、状态闭集、画家序遮挡、站位簇分箱、路线扫掠代理 |
| `tools/dist_data/build_catalog.py` | S3/S5 | 逐帧 catalog + exposure 字段、`TARGET_UNBOUNDED` 逐 schema 判定、`pre_split_floor_eligible`（BC-DATA-2）、颜色 HSV 统计与组一致性、S6 降级、最小程序规则、`prospective_mother_eligible` |
| `tools/dist_data/make_splits.py` | S4 | pHash（32×32 DCT / 左上 8×8 / 中位数 / 64 bit）、并簇 atom、留出物体整数算术、test 全枚举字典序、D3、dev、泄漏断言、exposure 矩阵、两个终态 |
| `tools/dist_data/audit_tool.py` | S6 | 三互斥 panel 生成、配额分配与容量不足终态、A1/A2/A3 判定线、attempt 有限状态机（3 attempt × (1+2) supersession = 9 panel 上限） |
| `tools/dist_data/g0_report.py` | S7 | `mother_candidates` 冻结、F1–F4、分层分母、排除直方图、门判定 |
| `tools/dist_data/gen_mother_templates.py` | S8 | 门前置断言、逐 id 字节等价断言、模板表达（往返自检）、簇统计、留出/手写预留清单 |
| `tools/dist_data/tier1_lang.py` | 全 | ontology/v1、规范化 AST（幂等）、renderer/parser（可逆）、唯一性执行器 |
| `tools/dist_data/verifier_contract.py` | §2.11 | `verifier_input/v1`（含 BC-DATA-4 的 tier / ontology_ref / parser_ref / 逐引用 sha）、`verifier_output/v1` nullable 规则、纯函数 verdict、16 条离线夹具 |

### 合同实现要点（逐条对应）

- **禁行边（§2）**：`artifacts.STAGES` 给每类工件钉死阶段号，`ArtifactStore.read`
  在 `stage > requesting_stage` 时抛 `ForbiddenEdgeError`。S7 读 S8 会失败，
  S1 读 S2 会失败，同阶段（S7 的 `g0_report` 读 `mother_candidates`）允许。
- **create-once（§2.2）**：同 attempt 重写相同字节幂等、不同字节即
  `CreateOnceError`；supersession 必须同时给 `supersedes` 与原因，且被
  supersede 的 attempt 必须仍在盘上。工件信封**无任何时钟字段**（时间戳会
  破坏字节幂等）。
- **BC-DATA-1**：F1–F4 只有 `contract.FLOORS` 一处定义；S7 的 F3/F4 只读
  `mother_candidates` 冻结外延；`apply_audit_downgrades` 只做减法。
- **BC-DATA-2**：`pre_split_floor_eligible(f)` 与 `floor_eligible(f, split)`
  分开实现；atom < 2 → `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA`，> 20 →
  `SPLIT_ENUMERATION_LIMIT_EXCEEDED`；所有哈希排序键 =（原始 32 字节, UTF-8
  id 字节）；subset 终决元组含 atom id。
- **BC-DATA-3**：`cross_validate_layout` 只接收 id 恰一映射的静态 distractor
  对，按 `(SHA-256(frame_id/object_id), frame_id, object_id)` 取前 50，不足
  50 即 `INVALID` 且不以动态 target 补数；`target_world_center_hit_ratio`
  只算中心落框率，返回值里**没有** IoU 字段。
- **BC-DATA-4**：`validate_input` 检查 tier / ontology_ref / parser_ref /
  三个 artifact ref（attempt + sha）；`tier=mechanical` 带 model evidence 或
  `tier=model` 缺任一字段 → `REJECT(FORMAT)`。verdict 是 input + 域的纯函数。
- **BC-DATA-5**：9 条类别映射是每 attempt 重跑的固定 checklist，不进三 panel；
  panel 互斥性在生成时机检；容量不足报 `AUDIT_PANEL_CAPACITY_INSUFFICIENT`
  而不缩小分母；组级颜色错是数据结论不计 attempt 失败。
- **§2.11 语义等价**：AST 不等价时 verdict 恒为 `REJECT(AST_MISMATCH)`，
  即使当帧执行选中同一对象（夹具 `ast_mismatch_same_object` 覆盖）。

## 2. 实际运行的命令与结果

全部在本机 macOS 15（Darwin 25.5.0）执行。

```
python3 -m unittest discover -s tests -p 'test_dist_data_*.py' -q
→ Ran 279 tests ... OK          （python3 = 3.14.6，无 numpy/PIL/cv2）

.venv-yoloe/bin/python -m unittest discover -s tests -p 'test_dist_data_*.py' -q
→ Ran 279 tests ... OK          （BC-BODY1-34 钉死解释器，3.12.13）

.venv-yoloe/bin/python -m unittest discover -s tests -q
→ Ran 814 tests，FAILED (failures=1, errors=1, skipped=1)

python3 -m unittest discover -s tests -q
→ Ran 709 tests，FAILED (errors=9, skipped=6)
```

**全套失败项全部是既有的、与本批次无关的环境失败**，已按 §4.3.1 条件 3
逐项核对：

- `.venv-yoloe` 的 2 项 = 状态板长期记录的 opencv-contrib CSRT 缺失：
  `test_trackers.TrackerAdapterTests.test_pinned_opencv_csrt_initializes_and_updates`
  与 `test_track_loop.TrackLoopTests.test_cli_runs_pinned_csrt_to_a_versioned_summary`。
  **改动前基线核对**：`git stash -u` 后同一命令 → `Ran 535 tests`，同样这
  2 项失败；恢复后 `Ran 814 tests`，仍只有这 2 项。本批次新增 279 个用例，
  **新增失败 0**。
- 默认 `python3`（3.14.6）的 9 项全部是 `import cv2` / `import numpy` 的
  模块导入错误（`test_benchmark_reanchor`、`test_detector_scouting`、
  `test_rate2_protocol`、`test_rate3_difficulty_audit`、`test_rate3_protocol`
  的一个守卫用例、`test_rate_study`、`test_scene004_gate0_probe`、
  `test_scene004_scouting`、`test_scene006_probe`），与本批次无关；本批次
  新增的 279 个用例在该解释器下**全部通过**（纯标准库）。

零 Play、零 Edit Mode、零 scenario/session/run ID、零 API/GPU、零模型下载。

## 3. 对真实归档的只读诊断（**不是**正式工件，不进证据链）

为验证附录 A 的「pattern 互不重叠、每个文件恰匹配一个」这一**合同前提**
是否在磁盘上成立，运行了一次 `--dry-run`（不写任何工件、不创建任何 ID）：

```
python3 -m tools.dist_data.build_inventory --dry-run
→ InventoryError: 附录 A 冻结根清单是闭集，S1 要求每个被枚举文件恰匹配一个 pattern。
  零匹配 215 个；多匹配 0 个。
```

结果分两半：

- **好消息**：**多匹配 0 个**——附录 A 的 pattern 互不重叠这一断言在
  24,154 个被枚举 jpg 上成立；逐 pattern 计数与附录 A 的估计逐行吻合
  （5×128 / 4×128 / 128 / 46+54+128+128 / 768 / 2×512 / 512 / 512 / 259 /
  759 / 497 / 512 / 266 / 391 / 310 / 98 / 51 / 6 / 256 / 128 / 29 / 2405 /
  2431 / 4096 / 3668 / 188 / 2888 / 173，A.3 各行同样吻合）；`runtime/**`
  下的 jpg 总数 **24,152**，与附录 A 的对账目标一致（另 2 个是
  `docs/evidence/P1-M3-BODY-001-1b/` 的 `DOC_COPY`）。
- **坏消息**：**零匹配 215 个**，见 §5 的 R1/R2 退回项。

工具按合同 fail-closed 停机，**没有**静默纳入、静默跳过或自行扩表。

## 4. 未验证项与已知限制

1. **未在真实归档上运行任何正式阶段**：第一候选时 S1 曾按合同硬错误停机
   （§3）；BC-DATA-6/-7 后 S1 只读 dry-run 已通过（§8.4/§10.4），S2–S8 仍未
   在真实数据上正式运行。
2. **没有图像解码器**：pHash 与颜色统计需要像素。默认 `python3` 3.14.6 无
   numpy/PIL/cv2；本批次把像素访问放在注入式适配器 `PixelSource` /
   `GraySource` 之后，**没有**实现基于 PIL/cv2 的具体适配器（那属于正式
   工件生成，未获授权）。钉死的 `.venv-yoloe` 有 numpy/PIL/cv2，可在获得
   授权后补一个适配器实现。**这是下一批次的具名缺口。**
3. **S3–S8 没有独立 CLI**：只有 S1/S2 有 `main()`。其余阶段交付的是阶段
   载荷构造函数 + `ArtifactStore.write` 这一组合路径，端到端组合由
   `tests/test_dist_data_pipeline.py` 可执行地演示（含禁行边、字节幂等、
   闭门拒绝 S8 三项断言）。真实归档上的驱动脚本未写。
4. **审计叠加图渲染未实现**：`audit_tool.py` 只做协议（panel 生成、配额、
   判定线、状态机）。渲染需要图像库，且属于未授权的人工审计步骤。
5. **合成世界的门必然关闭**：`test_dist_data_pipeline` 里 F1–F4 全不达标，
   这是被断言的**正确**行为（下限不因规模回调），不是缺陷。
6. **`UNITY_NA` 未主张**：本批次纯离线，提案 §2.10 拟以 `UNITY_NA` 申请，
   但须复核角色在复核文件中附议；实现角色不主张、不代填。

## 5. 退回接受角色的事项（§4.3 歧义与合同缺口，实现角色不得自行重新解释）

### R1（阻断正式 S1）— 附录 A 闭集缺 215 个文件

零匹配文件按目录归组：

| 数量 | 目录 |
|---|---|
| 107 | `runtime/p1-scene-006/probe-baseline-vfov60/frames/frame_*.jpg` |
| 107 | `runtime/p1-scene-006/probe-candidate-vfov40/frames/frame_*.jpg` |
| 1 | `runtime/test-results/rs3-clock-smoke/phase1-hold/frames/init-box-preview.jpg` |

附录 A.3 的 `PROBE_TRUTH_ONLY` 行写「探针真值（**无 jpg**）」——磁盘上
SCENE-006 的两个探针目录各有 107 张 jpg，与该行文字直接矛盾。
`rs3-clock-smoke/phase1-hold` 的 `init-box-preview.jpg` 与同目录的 173 张
`frame_*.jpg` 并列，但 A.3 的 `PREVIEW` 各行都没有覆盖它。

**实现侧不做任何处置**：不加 pattern（那是改冻结闭集）、不放宽断言（那是
放宽验收条件）。请接受角色裁定：补两/三行到附录 A 并给出用途类，或另行
处置。`P1-SCENE-006` 当前是 `CLOSED_PROTOCOL_PRECONDITION_UNSATISFIED`，
其探针帧的用途类归属需要接受角色决定，不是实现角色能推定的。

### R2（不阻断，但会给出错误用途类）— m3-armA 真值 pattern 过匹配

A.1 的 `runtime/runs/p1-m3-body-001-arm-a-*/m3_body_truth.jsonl`
（用途类 `VALID_FORMAL`）在磁盘上匹配 **6** 个文件，其中
`runtime/runs/p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold/m3_body_truth.jsonl`
属于 void trial hold，按 A.1 的 m3-void 行应为 `VOID_TRIAL_HOLD`。
pattern 之间不重叠（该文件只匹配这一行），所以 S1 的恰一匹配断言不会触发，
但它会被登记为 `VALID_FORMAL`。请接受角色确认是收紧 pattern 还是接受该
标注（图像侧不受影响：void hold 的**帧**由 m3-void 行正确标为
`VOID_TRIAL_HOLD`，帧资格不依赖真值文件的用途类）。

### R3 — 合同未给定数值的实现判定（全部取 fail-closed 方向，请逐条确认）

1. **路线扫掠代理区（§2.3）**：实现为「逐路线线段取（线段 ⊕ 全体目录车辆
   AABB 尺寸最大包络）的 AABB」。轴对齐线段上与精确 Minkowski 和重合，
   斜线段上是其外包围（保守）。**没有引入任何采样间距常量**。
2. **动态目标阻断体的画家序深度**：BC-DATA-3 禁止用 `target_world_*` 构造
   AABB，二维框给不出深度。实现把它放在**最近**（`-inf`）位置——它会遮挡
   与之重叠的目录对象，方向是少算不多算。
3. **「属性未知 = 通配冲突」及其后果（最重要一条）**：类别 `UNKNOWN` 的
   动态目标、AABB 不可恢复的 phantom 的颜色、`UNVERIFIED` 的颜色，在唯一性
   执行器里都按「不能用来排除」处理，即与任何相应属性的表达冲突。这直接
   蕴含：**任何一帧只要动态目标可见（真值框可用），该帧就不存在唯一命中的
   最小程序，整帧产不出母集候选**。§2.3 的字面（「类别 UNKNOWN 意味着它
   可能与任何类别的表达冲突」+ 执行域 = `blocking(f)`）就是这个意思，实现
   照字面执行；但它对 F3/F4 的压低幅度可能远超 §5.2 的 at-risk 披露——
   m3 十次 run 与 scouting 族的绝大多数帧都属于「目标可见」。请接受角色
   确认这是预期语义（若是，G0 的 at-risk 段落宜相应更新）。
4. **最小程序的关系枚举序**：关系按 `contract.RELATION_TYPES` 顺序，ref 取
   「在执行域内唯一解析的名词短语」，按（类别词升序，无色在前、颜色升序）
   枚举，取第一个使目标唯一命中的组合。§2.9 只说「确定性优先序」，本序是
   实现给出的唯一化。
5. **phantom 代理体积的「同类」**：取 §2.6 冻结类别映射的 9 类（合同里唯一
   定义过的「类」），不是 prefab 级。
6. **颜色主带必须唯一**：占比恰 0.5 且两带并列时判无主色（`UNVERIFIED`）。
   §2.6 只写了「主带占比 < 0.5 → 无主色」，没写并列。
7. **BC-DATA-3 排序键里的 `frame_id`**：取 inventory 里的**路径**（全局
   唯一），不是 sidecar 的数字 `frame_id`（跨族不唯一）。
8. **族的场景字节解析**：逐帧向上找最近的内嵌 `scenario.json` /
   `scenario_config.json` 快照（第 1 优先），否则向上找最近的
   `manifest.json` 的 `scenario_config_sha256` 再在字节提供者里找哈希相等
   者（第 2 优先）；族内解析出**不唯一**的字节时整族
   `EXCLUDED_UNBOUND_SCENARIO`（§2.3 只写了「两者皆无」的情形）。
9. **lineage 组的 primary**：按用途类闭集表序，同序按路径升序。
10. **S6 对 S5 只做减法**：`apply_audit_downgrades` 只清字段、不加字段、
    不改样本集合（BC-DATA-1 的机械落实）。

## 6. 给复核角色的复核范围

新增文件全部在 `tools/dist_data/` 与 `tests/test_dist_data_*.py`，
行数按 COORD-007 R7 运行时解析，不再手写（`git ls-files` + `wc -l` 即得；
C3-1 由接受轮 8 §20.3 (a) 升级为**删除**该手维护数字而非更新它）。建议按提案
§2.10 的四项加两项：

1. **DAG 禁行边与 create-once / supersession 语义**：`artifacts.py` 全文 +
   `tests/test_dist_data_artifacts.py` + `tests/test_dist_data_pipeline.py`
   的三条禁行边断言。重点：阶段号表是否与 §2 一致、同阶段读是否应允许、
   信封无时钟字段是否足以保证字节幂等。
2. **投影与遮挡合同实现**：`project_boxes.py`。重点：近平面裁剪是否覆盖
   12 条棱、amodal/visible 口径、状态闭集求值顺序（NOT_IN_VIEW → TOO_SMALL
   → TRUNCATED → 遮挡）、画家序 tie-break、θ_occ 的分母是否为 A 的 visible
   框面积、站位分箱的方位/俯角定义。
3. **切分泄漏断言**：`make_splits.py`。重点：全枚举目标向量四分量、
   `(3n+5)//10` 与 32 辆、dev 的整数比较、连带规则是否真的不让 test/D3 侧
   的非 floor 帧回流训练侧、四集两两互斥断言是否覆盖原子/谱系/帧三层。
4. **审计协议执行痕迹**：`audit_tool.py`。重点：三 panel 互斥是否由生成
   过程保证而非事后检查、配额转移的确定性序、`floor()` 上限、状态机的
   9 个 panel 上限与「无修复不得重审」。
5. **附加：布局派生的可逆性**：`bind_layout.py`。
   `test_inverse_then_forward_reproduces_base_geometry` 断言「逆施 default
   再正施 default 逐轴回到已调整基础几何」，请独立复算；phantom 只登记在
   非 default 布局类这一条尤其需要对着 §2.3 (a)/(b) 逐字核。
6. **附加：唯一性 fail-closed 语义**：`tier1_lang.execute` 的
   `_noun_conflicts` 与 §5 的 R3-3。这是本批次对 F3/F4 影响最大的判定。

**G0 报告数字复算**：本批次没有产出任何 G0 数字（S1 在真实归档上停机），
所以这一项**无可复核对象**；请在复核文件中如实记为不适用，而不是通过。

## 7. 给用户的 Unity 用例或观察点

**无。** 本批次纯离线，不产生任何 Unity 行为、不改场景、不改运行时协议。
提案 §2.10 拟以 `UNITY_NA` 申请，但须复核角色在复核文件中附议后方可用于
关闭；实现角色不主张。

---

## 8. 接受轮 4 返工（第 2 个候选，2026-08-26）

接受轮 4（提案 §16）判定 **`STOP_POINT_NOT_CONFIRMED /
IMPLEMENTATION_REWORK_REQUIRED`**：条件 2 已满足、条件 3 不适用，但**条件 1
未满足**——R1/R2 都改变 S1 的确定输出，不能以「正式工件尚未授权」降格为已知
限制。R1→BC-DATA-6、R2→BC-DATA-7、R3 十项→BC-DATA-8 全部接受并冻结。
本节记录 §16.3 (a)–(d) 的闭合。

### 8.1 落地的改动

| 合同条款 | 改动 | 文件 |
|---|---|---|
| BC-DATA-6 | 附录 A.3 补三条 pattern：两个 SCENE-006 探针目录 → 新用途类 `INVALID_RENDER_PROBE`（family/layout = null、decision `INVENTORY_ONLY`）；rs3 `init-box-preview.jpg` → `DERIVED_OVERLAY`。**pattern 用 `*.jpg` 而非 `frame_*.jpg`**——两目录各含 1 张 `prompt_*.jpg`，写窄会残留 2 个 zero-match | `roots.py` `_A3` |
| BC-DATA-6 | `INVALID_RENDER_PROBE` 进三处闭集；**不新增** inventory reason code（`INVENTORY_ONLY` 已在闭集内）。插在 `THIRD_PARTY_ASSET` 与 `PROBE_TRUTH_ONLY` 之间——**表序即 lineage primary 优先级**，探针必须排在全部 mother/floor 类之后 | `contract.py` `USAGE_CLASSES`、`roots.py` `USAGE_ELIGIBILITY` / `USAGE_DECISION` |
| BC-DATA-6 | dry-run 现在**显式报告** zero-match / multi-match，而不只在违规时抛错 | `build_inventory.py` `match_audit` |
| BC-DATA-7 | 删除宽泛的 `runtime/runs/p1-m3-body-001-arm-a-*/m3_body_truth.jsonl`，换三条零重叠精确 pattern（`trial-1-attempt-4` / `trial-2-attempt-2` / `trial-[345]`，合计恰五份 `VALID_FORMAL`）+ 一条 void run 目录 pattern（`VOID_TRIAL_HOLD` / `m3-armA` / default）。根级 void pattern 不变 | `roots.py` `_A1` |
| BC-DATA-8.3 | **「永不可指称」原先没有任何机械实施点**：`SceneObject.referable` 在整个解析路径中从未被读取。现 `_resolve_ref` 要求唯一命中对象 `referable is True`；唯一性**分母仍含通配对象**（未知不能用来排除），只是通配对象自己永不可被选作 ref | `tier1_lang.py` `_resolve_ref`、`build_catalog.py` `_unique_reference_specs` |
| BC-DATA-8.4 | ref 颜色枚举改为**升序**（新增 `contract.COLOR_WORDS_ASCENDING`）；原先用的是 §2.6 判定带词表序，与冻结文字「颜色词升序」不符 | `contract.py`、`build_catalog.py` |
| 同源 fail-open | 关系执行原先把位置/道路侧未知的候选**静默丢弃**，等于判它「不存在」，与本模块自己的「未知即通配冲突」政策相反（phantom 默认就没有 `world_xz`）。现三种关系一律：任一候选属性未知 → 关系不可用 | `tier1_lang.py` `execute` |

### 8.2 两处必须如实说明的错位

BC-DATA-8.3 与 8.4 冻结的是**我上一轮 R3 的文字描述**，而那两条描述与我当时的
代码本身就不一致：

- **R3-3**：我写「未知属性通配冲突 ⇒ 目标可见的帧产不出唯一程序」，但代码里
  可见的 UNKNOWN 动态目标能被选作关系 **ref**（域内没有该类目录对象时它是唯一
  命中），于是 `minimal_program` 会返回
  `the taxi to the viewer's right of the ambulance` 之类——场里根本没有
  ambulance，被指的是那个身份未知的动态目标。这既违反「永不可指称」，也正是
  A3 审计**零容忍**的假唯一。phantom 同构。
- **R3-4**：我写「颜色升序」，代码用的是词表序（`COLOR_WORDS` 与 `sorted()`
  实测不等）。

本轮把**代码改到与冻结文字一致**（属落实已接受合同，不是重新解释）。这两处
错位的责任在实现侧的自述不准确，据此记录在案。

### 8.3 具名回归（修复前必失败）

新增 `tests/test_dist_data_round4.py`（28 个用例）。修复前实测
**17 个失败 / 28**，修复后 28/28 通过。分组：

- `BcData6RootClosureTest`（7）：探针 `frame_*` 与 `prompt_*` 各恰一匹配且为
  `INVALID_RENDER_PROBE`；`init-box-preview.jpg` 为 `DERIVED_OVERLAY` 而同目录
  `frame_*.jpg` 仍为 `SMOKE`；三处闭集齐全；不进 floor/训练；无新 reason code；
  表序钉住。
- `BcData7TruthClosureTest`（5）：五份有效 truth 与 void run truth 的恰一匹配
  与用途类；宽泛 pattern 确已删除；arm-B 未被波及。**全部走
  `roots.matching_entries`（遍历每一行），不依赖表序。**
- `BcData8NeverReferableTest`（5）：可见 UNKNOWN 动态目标下
  `_unique_reference_specs == []`、`minimal_program is None`、
  `_resolve_ref is None`；phantom 同构；正常可指称 ref 仍能解析（防过度封死）。
- `BcData8ReferenceOrderTest`（2）：升序表；枚举序为类别升序 → 无色在前 →
  颜色升序。
- `UnknownPositionBlocksUniquenessTest`（4）：三种关系下未知属性阻断唯一性；
  全已知域仍正常解析。
- `RealArchiveClosureTest`（5，只读）：zero-match/multi-match 均为 0；逐 pattern
  钉住 107/107/1；rs3 同目录仍 173；arm-A 有效 truth 恰五份；void run truth 恰
  一份。

另**加强**了既有的 `test_unknown_class_blocker_kills_every_program`：原用例把
动态目标构造成不可见（`center_px=None`），恰好绕开裁定文字里的「**可见**」
前提，所以它在缺陷存在时也是绿的。现改为可见目标并加断言。

### 8.4 §16.3 闭合条件逐条

```
(a) BC-DATA-6/-7 + 具名回归          → 已落地，见 §8.1 / §8.3
(b) BC-DATA-8 语义 + 测试/证据指针    → 已落地（8.3/8.4 两处改到与冻结文字一致）
(c) 两解释器 focused 全绿、全套零新增失败：
    python3 3.14.6        focused 307/307 OK
    .venv-yoloe 3.12.13   focused 307/307 OK
    .venv-yoloe 全套       842 tests，失败仍只有既有的两项 CSRT/opencv-contrib
                          （535 基线 → 842，新增失败 0）
    python3 3.14.6 全套    737 tests，9 项既有 cv2/numpy 导入错误，与本批次无关
(d) 只读真实归档 dry-run：
    python3 -m tools.dist_data.build_inventory --dry-run
    → S1 inventory：记录 29923（图像 24154、真值 5769），lineage 组 19754
      恰一匹配审计：zero-match = 0，multi-match = 0
      INCLUDED 29262 / INVENTORY_ONLY 426 / EXCLUDED_DERIVED 77 /
      EXCLUDED_DIAGNOSTIC_CHANNEL 128 / EXCLUDED_UNRELEASED 30
    R1 与 R2 均已闭合；**未创建任何工件**（`runtime/dist-data/` 仍不存在）
```

`INVENTORY_ONLY` 的 426 = 214 张探针 jpg + 212 个探针 truth sidecar，与
BC-DATA-6「只盘点」一致。

### 8.5 本轮新退回接受角色的三项（R4-1…3，均为潜伏 fail-open，未擅自改）

1. **R4-1 phantom 的 `class_word is None` 未设防**：`bind_layout.apply_layout`
   的 `same_class` 用 `class_for_scene_object(...) == class_word` 比较；若
   `class_word` 为 `None`，会匹配到**建筑/道具**，代理体积变成楼那么大。当前
   全部 phantom 的 prefab 名都是 `Vehicle_*`，故不触发。建议改为硬错误，但那
   会引入 BC 未覆盖的新终态，故退回。
2. **R4-2「同类无实例 → 半长 0」实际是 fail-open**：注释写着 fail-closed，
   但半长 0 的 phantom 不再阻断任何东西。当前不触发。
3. **R4-3 场景字节的祖先向上走可能撞到 `runtime/scenario_config.json`**：
   §2.3 明令当前可变 config 不得充当历史布局源，而该文件正是运行时覆盖文件。
   **实测该文件当前不存在**，故为潜伏隐患而非现行缺陷；一旦 Unity 跑过就会
   出现。建议把内嵌快照的向上走上界收紧到帧所在归档/run 目录树，或把该路径
   显式列入排除并加断言测试。

三项都不阻断本轮停点（均不改变当前 S1–S8 的确定输出），但都应在正式工件生成
获授权之前定夺。

### 8.6 复核范围增量

在 §6 六项之外增加：

7. **`referable` 的机械实施点**：`tier1_lang._resolve_ref` 与
   `build_catalog._unique_reference_specs`。重点核：唯一性分母是否仍含通配
   对象（未知不得用来排除），而通配对象自己是否确实永不可作 ref；两者是否
   一致（`_unique_reference_specs` 现在直接复用 `_resolve_ref`，避免两处判据
   漂移）。
8. **根闭集补正**：`roots.py` `_A1` / `_A3` 的四条 truth pattern 与三条 image
   pattern 是否零重叠、是否覆盖全部真实归档文件；请独立复算 zero-match = 0 与
   multi-match = 0，以及 107/107/1、173、恰五份、恰一份这六个计数。

---

## 9. 接受轮 5 落地（BC-DATA-9，与轮 4 返工同批）

接受轮 5（提案 §17）在轮 4 返工进行中落盘，裁定
**`ACCEPTED_WITH_BINDING_CLARIFICATIONS / BC-DATA-8.3_SUPERSEDED`**：它先认定
一条会改变 F3/F4 计数的新事实，再要求与 BC-DATA-6/-7 一起落地后返回同一停点。

### 9.1 事实裁定与我的实现改动

动态目标**不在场景文件中**，而由 `TetheredScenarioBootstrap.CreateTarget` 的
单一运行时构造链生成；F23 后 `TargetVisualFactory` 的几何与两组红色字面量由
独立 EditMode/分析器 oracle 冻结，git 历史证明 M0 至今字面量等价，再加用户
逐字事实认定「这是一辆纯色的红车」。据此现有冻结归档族的目标字段定为
**`class=car` / `color=red`**——这是**已版本化的构造源权威**，不是 AR2-3 所禁的
读当前场景。

| 条款 | 改动 | 文件 |
|---|---|---|
| BC-DATA-9.1 | 新增冻结常量 `DYNAMIC_TARGET_SOURCE_AUTHORITY` / `DYNAMIC_TARGET_SOURCE_VERIFIED_FIELDS` / `DYNAMIC_TARGET_REFERABLE`，以及 `dynamic_target_fields(source_bound)`：源可证绑定 → `car`/`red`，否则**逐字段** `UNKNOWN`（不得用路径名/当前场景/当前 config 补齐） | `contract.py` |
| BC-DATA-9.1 | `FrameInput.target_source_bound`；`build_frame_entry` 把 `target_source_bound` 与解析出的 `target_fields` 写进逐帧记录 | `build_catalog.py` |
| BC-DATA-9.2 | `frame_world` 用解析出的字段构造目标；收窄后的冲突判定由既有 `_noun_conflicts` 自动给出（已知字段比较、未知通配） | `build_catalog.py` |
| BC-DATA-9.2 | `TARGET_BLOCKER_ID` 由 `dynamic-target:UNKNOWN` 改为 `dynamic-target`——旧名在轮 5 后是错的 | `build_catalog.py` |
| BC-DATA-9.3 | ref 禁令**已在轮 4 返工中落地**（`_resolve_ref` 要求唯一命中对象 `referable is True`），轮 5 恰好逐字确认了该修法：「若唯一命中的是动态目标，ref 仍不可用」 | `tier1_lang.py` |

### 9.2 与轮 4 修法的关系（必须说清楚）

轮 4 我把 8.3 实现成「目标与**全部**名词通配冲突」。轮 5 把该适用域**收窄**为
「只对**仍然未知**的字段」。两者不冲突的部分是 ref 禁令——那条我在轮 4 就做了，
轮 5 逐字确认。需要改的是通配范围：现在目标只与无色 `car`、`red car` 冲突，
不与非 `car` 或已验证非红的 `car` 冲突。

**后果是计数可能回升**（轮 4 语义下目标可见的帧一律产不出候选，轮 5 语义下
只有 car 系目标被挡）。幅度只能由未来获授权的正式 G0 给出；F1–F4 的定义、
分母、去重单位与全部下限一律不动。按 BC-DATA-9.4，磁盘上没有任何正式 S1–S8
工件，故本轮**不伪造 supersession attempt**，只声明：旧语义下的任何临时计数
不得成为门证据。本批次从未产出过任何 G0 数字，故无实际作废对象。

### 9.3 §17.3 增量条件逐条

- **(a)** source-verified `car/red` 记录 + 源不可证时逐字段 `UNKNOWN` 回退
  → `contract.dynamic_target_fields()`，逐帧记录落在 `target_fields`。
- **(b)** 冲突矩阵具名回归 → `tests/test_dist_data_round5.py`
  `ConflictMatrixTest` 五格逐格断言：无色 `car` 冲突、`red car` 冲突、
  已验证非红 `car` 不冲突、非 `car` 不冲突、颜色 `UNVERIFIED` 的城市 `Car`
  仍与 `the red car` 一起冲突（且已验证非红的可被排除）。
- **(c)** 唯一命中但 `referable=false` 的动态目标不得成为 ref
  → `NeverAReferenceTest`：域内 `the car` / `the red car` 恰一命中动态目标时
  `_resolve_ref` 仍返回 `None`，且 `_unique_reference_specs` 不含任何 car 系
  spec；同时断言可指称的城市 `Car` 仍能正常作 ref（防过度封死）。
- **(d)** 旧的「unknown class blocker kills every program」用例已**改名并改
  语义**为源身份不可证的 fallback：
  `test_source_unprovable_target_blocker_kills_every_program`
  （`tests/test_dist_data_catalog.py`），且 `BcData8NeverReferableTest` 现用
  `contract.dynamic_target_fields(False)` 构造目标，类文档明写它只代表
  fallback、不再表示现有冻结目标。

新增 `tests/test_dist_data_round5.py` 19 个用例（`SourceAuthorityTest` 6、
`ConflictMatrixTest` 6、`NarrowedWildcardTest` 3、`NeverAReferenceTest` 2、
`F1ExclusionTest` 2）。其中 `F1ExclusionTest` 钉住 BC-DATA-9.3 的
「动态目标不计入 F1 的 101 个对象」。

### 9.4 合并后的最终验证（轮 4 + 轮 5 同一候选）

```
python3 3.14.6        focused 326/326 OK
.venv-yoloe 3.12.13   focused 326/326 OK
.venv-yoloe 全套       861 tests，失败仍只有既有两项 CSRT/opencv-contrib
                      （535 基线 → 861，新增失败 0）
python3 3.14.6 全套    756 tests，9 项既有 cv2/numpy 导入错误，与本批次无关

python3 -m tools.dist_data.build_inventory --dry-run
→ 记录 29923（图像 24154、真值 5769），lineage 组 19754
  恰一匹配审计：zero-match = 0，multi-match = 0
runtime/dist-data/ 不存在；runtime/frames/ 仍为 0 项
```

§16.3 (a)–(d) 与 §17.3 (a)–(d) 全部闭合。§8.5 的 R4-1…3 三项退回项不受轮 5
影响，仍待接受角色定夺。

---

## 10. 接受轮 6 返工（第 3 个候选，2026-08-26）

接受轮 6（提案 §18）判定 **`STOP_POINT_NOT_CONFIRMED /
IMPLEMENTATION_REWORK_REQUIRED`**：条件 2 由 Acceptance 在候选工作树上**独立
复现**（两解释器 focused 各 326/326、只读 dry-run 29,923 条 / zero-match = 0 /
multi-match = 0 / `runtime/dist-data/` 不存在），条件 3 不适用，
**BC-DATA-6/-7/-9 全部有效**；只有条件 1/4 因 R4-1…3 仍开。

### 10.1 实现侧记一课

我上一轮把 R4-1…3 作为「潜伏、当前不触发、不改变确定输出」的事项**退回定夺**，
建议不阻断停点。轮 6 明确驳回该降格：

> 三项都违反 §2.3 的 same-class proxy 与归档字节 fail-closed 合同，
> **不能因今天的归档恰未触发而降格为停点后风险**。

对 fail-closed 数据合同而言，「今天恰好没踩到」不等于合同被满足；判据是代码
路径本身是否可能违约，不是当前归档是否触发。此后遇到同类判断按此标准处理。

### 10.2 落地的改动

| 条款 | 改动 | 文件 |
|---|---|---|
| BC-DATA-10 | `class_for_scene_object(prefab_name)` 返回 `None` 时**立即** `LayoutError`——在代理构造前、在 S2 create-once 写盘前。删除 `None == None` 的同类筛选路径，不借用 building/prop/未映射实例包络，不生成该 phantom，不新增静默跳过或 UNKNOWN 通配代理 | `bind_layout.apply_layout` |
| BC-DATA-11 | 类别已知但该类在目标布局中无存活实例 → 同样 `LayoutError`。**「三个半长置 0」分支已删除**：零面积体会继续参与遮挡/唯一性/F 计算，方向 fail-open，不是 fail-closed。代理尺寸只允许来自该冻结类别**仍存在**实例的逐轴最大半长 | `bind_layout.apply_layout` |
| BC-DATA-12 | 新增 `FORBIDDEN_SNAPSHOT_PATHS`（含精确路径 `runtime/scenario_config.json`，**永久禁止**，即使将来 pattern 放宽也不得命中）、`SNAPSHOT_EXCLUDED_PREFIXES`（`config/` 永不因祖先关系成为内嵌快照）与谓词 `is_allowed_embedded_snapshot()`。祖先搜索只接受完整匹配 `roots.SCENARIO_BYTE_PROVIDERS` 冻结 pattern 的候选；**不合格候选既不绑定也不遮蔽下一优先级**——继续向上找最近的合格快照，仍无则退 manifest SHA，最后 `EXCLUDED_UNBOUND_SCENARIO` | `bind_layout` |

### 10.3 §18.3 (b) 的五条具名回归分支

新增 `tests/test_dist_data_round6.py`（16 个用例）。**修复前 9/16 失败**，且
每条都按对应缺口失败（§18.3 (c) 的要求是「按对应缺口失败」，不是笼统的红）：

| 分支 | 测试 | 修复前的实测症状 |
|---|---|---|
| 1 unknown-class phantom 硬失败 | `UnknownClassPhantomTest` | 未抛错，且**产出了代理** `phantom:Prop_TrafficCone@…`——它从 building/tree 借到了包络（`None == None` 判为同类） |
| 2 known-class 空集合硬失败 | `EmptySameClassPhantomTest` | 未抛错，产出 `min_x_m = max_x_m = 50.0` 的**零体积**代理（literally 一个点） |
| 3 根级可变 config 单独存在时仍 unbound | `MutableRootConfigTest` | 判成 `BOUND` / `embedded_snapshot`，路径正是 `runtime/scenario_config.json` |
| 4 可变 config 与有效 manifest 并存时走 manifest | `MutableRootConfigTest` | 返回 `embedded_snapshot` 而非 `manifest_sha_match`——不合格候选**遮蔽**了下一优先级 |
| 5 合法 run 内嵌快照仍优先 | `LegitimateSnapshotTest` | （防过度封死的守卫，修复前后均绿） |

另加三条边界：候选必须**确为该帧祖先**（同级 run 的快照不得命中）、
`config/*.json` 不因祖先关系成为快照、`ProviderClosureTest` 钉住谓词与冻结
provider 闭集一致。

### 10.4 §18.3 闭合条件逐条

```
(a) 逐字落地 BC-DATA-10/-11/-12      → 见 §10.2
(b) 五条具名回归分支                  → 见 §10.3（另加 3 条边界守卫）
(c) 修复前按对应缺口失败 9/16；修复后：
    python3 3.14.6        focused 342/342 OK
    .venv-yoloe 3.12.13   focused 342/342 OK
    .venv-yoloe 全套       877 tests，失败仍只有既有两项 CSRT/opencv-contrib
                          （535 基线 → 877，新增失败 0）
    python3 3.14.6 全套    772 tests，9 项既有 cv2/numpy 导入错误，与本批次无关
(d) 只读真实归档 dry-run，分类须不变：
    记录 29923（图像 24154、真值 5769），lineage 组 19754
    恰一匹配审计：zero-match = 0，multi-match = 0
    INCLUDED 29262 / INVENTORY_ONLY 426 / EXCLUDED_DERIVED 77 /
    EXCLUDED_DIAGNOSTIC_CHANNEL 128 / EXCLUDED_UNRELEASED 30
    → **与轮 6 复现的数字逐项一致**；`runtime/dist-data/` 仍不存在
(e) 实现者证据与 Review 范围已更新（本节 + §10.5）
```

**收紧不改变任何现有绑定**（这是 (d) 能成立的原因，事前已实测）：真实归档里
会被祖先搜索看到的内嵌快照候选共 **28** 个，其中落在 `SCENARIO_BYTE_PROVIDERS`
闭集外的是 **0** 个；`runtime/scenario_config.json` 今天既不存在也不匹配任何
provider pattern，对它的禁令是防将来而非改现在。

**真实布局下两条硬失败均未触发**：default 布局 0 个 phantom；scene-004 的
3 个 phantom 分别是 `car` / `container truck` / `police car`，三者在该布局中都
有存活实例，代理尺寸分别为 `6.32×6.76×2.20` / `9.09×9.09×4.16` /
`6.32×6.32×2.32` m，**没有任何零体积代理**。

### 10.5 复核范围增量

在 §6 的六项与 §8.6 的两项之外增加：

9. **两条 phantom 硬失败**：`bind_layout.apply_layout`。重点核：`class_word is
   None` 的检查是否确在同类筛选**之前**、是否确在 create-once 写盘之前；
   `not same_class` 分支是否真的抛错而非返回退化体；以及真实布局的 3 个
   phantom 尺寸是否可独立复算。
10. **内嵌快照闭集**：`bind_layout.is_allowed_embedded_snapshot` 与
    `resolve_frame_scenario`。重点核：不合格候选是否确实**既不绑定也不遮蔽**
    （分支 4 是这条的唯一守卫）；祖先关系是否真的被验证（而不是只比对
    pattern）；`config/` 前缀排除是否与「manifest SHA 相等时仍可作 provider」
    并存不冲突（`build_provider_index` 未改，仍收录 `config/scenario.*.json`）。

§8.5 的 R4-1…3 至此**全部由 BC-DATA-10/-11/-12 裁定并落地**，无待决退回项。

---

## 11. 复核轮 1 返工（第 4 个候选，2026-08-26）

停点在**接受轮 7** 确认成立，候选 3（`57e7af2`）交独立复核；**复核轮 1**
返回 `REWORK_REQUIRED`（F1 CLASS_1 + F2–F10 CLASS_2），并**附议 `UNITY_NA`
分类**；**接受轮 8**（§20）消化复核结果，冻结 BC-DATA-13…19。本节记录
§20.3 (a)–(e) 的闭合。

### 11.1 F1 是本项目迄今最重要的一条 finding

复核用**我自己的代码**在真实归档上跑了一遍 S1 + S2 绑定——**这件事我从未
做过**。结果：9 个族里 6 个整族 `EXCLUDED_UNBOUND_SCENARIO`，23,706 个
INCLUDED 帧只有 **1,024（4.3%）**可绑定，scene-004 布局类**零绑定族**。
G0 会返回 `INSUFFICIENT`，但那是**绑定方案**造成的，不是数据不够。

根因是合同内部矛盾而非单纯实现缺陷：BC-DATA-8.8 规定「逐帧向上取最近内嵌
快照」，代码忠实照做；但 §2.3 与附录 A.2 讲的是**族内** manifest，而族内
manifest/快照**全部存在、哈希全部吻合**，只是位于帧的**非祖先**子树，祖先
搜索按构造永远够不着。

**归因里有我的一半，我接受**：这个数字当天零成本可测，我交停点时从未测量
或披露，实现者证据 §4-1 还停留在第一候选的时态，而 §5.2 的 at-risk 算术全部
以这些族计入 floor 为前提。按 R1/R2 先例列为阻断是对的。**教训（常驻）**：
交停点前必须实测并披露本批次代码在真实归档上的**确定输出**，不能只报测试
绿灯——绿灯只证明代码符合我写的断言，不证明它符合合同。

### 11.2 落地的改动

| 条款 | 改动 | 文件 |
|---|---|---|
| BC-DATA-13 | 绑定域从 `family` 改为 **`source_unit`**（拥有 `frames/` 的归档目录，或点名的 flat hold），聚合成 `scenario_partition = (family, scenario_sha256)`；一个 family 允许多个合法 SHA，只有无法唯一绑定的 **unit** 退出。缺失祖先快照/manifest 时走**闭集关联**：(a) m3 归档/hold → 附录 A root 模板点名的 run 目录；(b) A.2 三族 → 表头点名的 hold provider，前提是归档 `scenario_id` 恰为 `p1-scene-004`；(c) 其余只读自身归档树。manifest 内**零个** SHA = 无声明；**多个互异** SHA = **歧义硬失败**，不得由父级快照掩盖 | `bind_layout`、`roots` |
| BC-DATA-13/-18 | layout 几何按**精确 scenario SHA** 逐 partition 派生；逆施 default 的唯一来源是基础几何自身的 `source_scenario_sha256`（`default_inverse_premise`），不再取「首个 BOUND default family」；单个 partition 不可证时只使**它** `INVALID` | `bind_layout.build_layout` |
| BC-DATA-16 | `occluders(f)`（全部静态 AABB + phantom + 动态 blocker）与语言域分离：`blocking(f)` / `referable(f)` / exposure 只含九类车辆 + phantom + 动态目标；building/nature/prop 标 `occluder_only`，仍参与画家序遮挡。m3 truth 缺可见性证据键时是**未知**→ `TARGET_UNBOUNDED` | `build_catalog` |
| BC-DATA-17 | 新增 `_noun_satisfies`（**严格**匹配）与 `_noun_conflicts`（通配，用于唯一性分母）**两个判据**：带颜色的 ref 只有该 referent 自身已验证且词值相等才可被选中，`UNVERIFIED` 仍阻断唯一性但绝不能被选成任意颜色 ref。候选冻结 `resolved_reference_object_id`；模板生成与 S4 泄漏断言**两侧对称**检查 target 与 ref | `tier1_lang`、`build_catalog`、`make_splits`、`gen_mother_templates` |
| BC-DATA-18 | 逆施 default removal 的「原实例仍存在」判定**只**用 `match_tolerance_m`，不再加类内半对角线（邻居冒充 → 静默吞掉 phantom，fail-open） | `bind_layout` |
| BC-DATA-19 | 连带退出帧的候选写显式 `split="dropped"` + 原因（不再抛错），且不计 floor；`splits` 载荷**自带**逐 `(frame_id, object_id)` 四集角色与逐对象 exposure；S8 三元组物化 `station_key`，`unit_count` = distinct `(object_id, station_key)` | `g0_report`、`make_splits`、`gen_mother_templates` |
| BC-DATA-14/-15 | 审计 key 的 `/` 分隔与三处「距离」= 相机前向深度经裁定确认；新增具名常量 `camera_forward_depth()` 并加钉桩回归 | `build_catalog` |

### 11.3 §20.3 (c)：F1 的闭合证据（只读真实归档 S1 + S2）

逐 family / partition 报告（`build_inventory` + `bind_families`，零工件、零 ID）：

```
family        layout     status  分区  帧      partitions
detect-scout1 default    BOUND    1     768    68170d80…×768
m3-armA       default    BOUND    1     996    f9c92052…×896
m3-armB       default    BOUND    1     640    f9c92052…×640
rate          default    BOUND    2    5197    4bddb2f2…×1335, 78b06c46…×3546
s004-qual     scene-004  BOUND    1    7952    00c8802a…×7952
s004-scout    scene-004  BOUND    1    4836    00c8802a…×4836
s004-smoke    scene-004  BOUND    1    3061    00c8802a…×3061
scene-val     default    BOUND    1     256    f6005eb4…×256

INCLUDED 图像帧 23,706，落在已绑定 partition 的 23,290 = 98.2%
```

对照复核 F1 的实测表：

| 指标 | 复核实测（候选 3） | 本候选 |
|---|---|---|
| 整族 UNBOUND | **6 / 9** | **0** |
| 可绑定 INCLUDED 帧 | 1,024（**4.3%**） | 23,290（**98.2%**） |
| scene-004 布局类绑定族 | **0** | 3（全部经 A.2 点名 provider） |
| m3 有效帧 | 全数退出 | armA 896 + armB 640 经关联 run 快照绑定 |
| rate 两套 SHA | 互相毒化 → 整族退出 | **保留为两个 partition**（1,335 / 3,546） |

剩余未绑定的 416 帧全部是**个别 source unit**（void hold、calibration hold、
rerun-prep 等确无归档字节者）——按 BC-DATA-13 只让 unit 退出，不牵连 family。

### 11.4 §20.3 逐条闭合

```
(a) 删除证据 §6 手维护 LOC 数字并闭合升级后的 C3-1 → 已删除并改为运行时解析
    （COORD-007 R7 可派生标识禁手写）；C3-2 与观察项（__init__ 的 stages.py
    误引）一并处置
(b) 两解释器 focused 全绿、钉死环境全套相对基线新增失败 0：
    python3 3.14.6        focused 366/366 OK
    .venv-yoloe 3.12.13   focused 366/366 OK
    .venv-yoloe 全套       901 tests，失败仍只有既有两项 CSRT/opencv-contrib
                          （535 基线 → 901，新增失败 0）
(c) 只读真实归档 S1 + S2 绑定诊断 → §11.3
(d) runtime/dist-data/ 仍不存在；dry-run 29,923 条 / zero-match 0 /
    multi-match 0 / INCLUDED 29262 / INVENTORY_ONLY 426 / 77 / 128 / 30，
    与轮 6 复现的分类**逐项一致**
(e) Review 范围见 §11.6
```

§20.3 点名的 **16** 条具名回归全在 `tests/test_dist_data_round8.py`（24 用例），
命名与裁定逐字一致。**修复前 17/24 失败**——用 `5735838` 的
`tools/dist_data/` 加 `cc4f53a` 的首版测试文件、真实 `runtime/` 与 `config/`
挂进隔离工作树复算得 `failures=13, errors=4`。

**更正记录**：本节初稿写「十二条」与「18/24」，两者都错。条数是本角色统计
`test_[a-z0-9_]+` 时把 `test_m3_armA_family_binds_via_run_snapshot` 的大写
`A` 截断而漏计（实际 4+4+2+2+4 = 16）。`18/24` 则是把**23 用例版**上实测的
18 条失败，配到了**24 用例版**的分母上——那 18 条测于我把自己写错的
`test_verified_ref_color_still_resolves` 拆成两条**之前**；拆分后其中一条
修复前即通过，正确数是 17/24。

### 11.5 一处我自己写错的测试

`test_verified_ref_color_still_resolves` 我原本断言「已验证 blue car 可作
ref」，实测失败。查后确认**是我的断言错了**：同框有颜色 `UNVERIFIED` 的 car
时，它按通配仍冲突 `{car, blue}`，冲突集为 2 → ref 本就不该可用，这正是
BC-DATA-17「`UNVERIFIED` 仍可按未知通配阻断唯一性」的要求。已拆成两条：
`test_verified_ref_color_resolves_when_no_unverified_peer_blocks_it` 与
`test_unverified_peer_still_blocks_a_verified_colour_ref`。

### 11.6 复核范围增量

在 §6 / §8.6 / §10.5 之外增加：

11. **绑定域重构**：`bind_layout.resolve_frame_scenario` / `bind_families` /
    `build_layout` 与 `roots.source_unit_for` / `associated_run_directory`。
    重点核：source unit 的切分规则对 flat hold 与 `frames/` 归档是否都正确；
    闭集关联三支是否真的**只**按点名模板/provider 走（无模糊匹配、无同族
    邻居借用）；歧义 manifest 是否确实**不**回退父级；partition 的几何是否
    按精确 SHA 派生且互不毒化；§11.3 的八行 partition 表可独立复算。
12. **两个名词判据**：`tier1_lang._noun_conflicts`（通配，唯一性分母）与
    `_noun_satisfies`（严格，ref 选中）。重点核：二者是否在所有调用点各司其
    职、未被互换；`UNVERIFIED` 是否仍进分母但永不被选中。
13. **两侧对称的留出禁令**：候选是否确实冻结 `resolved_reference_object_id`，
    以及 S4/S7/S8 三处断言是否都查 target **与** ref。

### 11.7 提交候选 4 后的实现侧自查：四条阻断缺陷（同批修复）

候选 4 提交后本角色自跑了一轮只读独立核验（逐条把 BC-DATA-13…19 对着改完的
代码验一遍）。**查出四条阻断缺陷，全部已用生产路径实测复现并在本批修复。**
它们的共性与复核 F1 同类：**成员/分支存在 ≠ 它在生产路径上真的生效**。

| # | 缺陷 | 实测症状 |
|---|---|---|
| 1 | `default_inverse_premise` 把唯一性判在**路径条数**上（`len(providers) != 1`），而 provider index 以 sha 为键、同一 sha 下的多条路径按定义**字节相同** | 真实归档该 sha 有 **12 条同字节副本** → 抛 `LayoutError` → `build_layout` 在 partition 循环**之前**崩溃，S2 **一个 partition 也派生不出来** |
| 2 | 祖先遍历分两趟（先扫完全部祖先的快照，再回头读 manifest） | **更远**祖先的合法快照抢在**更近**的歧义 manifest 之前定案，BC-DATA-13 (v) 的硬失败永不触发；实测返回 `BOUND` 而非硬失败 |
| 3 | `held_out_reference` 只在 S4 由谓词的**可选**参数打标，S7 从不重新派生 | 生产驱动不传 `held_out`（该参数有默认值）时标记恒为 `False` → 留出的 bus 渲进训练表达 **`the taxi nearest to the bus`**，F4 的修复形同虚设 |
| 4 | `splits` 的 `sample_roles` / `exposure_matrix` 有成员名但**无装配器** | `per_frame_object_roles` 默认 `()`，没有任何函数把 catalog 记录桥接成角色 → 两个成员**恒为空**，BC-DATA-19 只满足了字面 |

**缺陷 1 是我第二次犯同一个错**：`build_layout` 在真实归档上的确定输出，我在
交候选 4 时**又一次没有测量**——§11.3 的诊断只跑了 `build_inventory +
bind_families`，从未触及 `build_layout`。§11.1 记的教训当时并没有真正落实到
这一批的自查清单里。现已把「真实归档上 S1 → S2 → 逐 partition 几何派生」整条
链纳入固定自查项。

同批还处置了核验指出的另外三项：BC-DATA-13 (b) 后半句「已有 manifest/快照
必须与 A.2 provider 字节一致」原先未实现（已加 sha 门）；BC-DATA-13 (c) 的
「只读**自身归档树**」被实现成「只读祖先」，unit 子树内的快照从不被读（已加
子树搜索，且要求子树内字节唯一），同时祖先扫描越出 unit 一直到仓库根（已把
上界收到 source unit）；m3 可见性证据原按「键在不在」判定且漏掉
`has_unoccluded_sample`，值为 `null` 会被误读成「不可见」（已改为按 bool
取值判定，三键同权）。

**修复后的真实归档确定输出**（只读，零工件）：

```
逆施前提 = config/scenario.default.json（sha f9c92052…，同字节副本 12 条）

partition                      状态    帧     实例  phantom
m3-armA|f9c92052…              BOUND    896    779    0
m3-armB|f9c92052…              BOUND    640    779    0
detect-scout1|68170d80…        BOUND    768    779    0
scene-val|f6005eb4…            BOUND    256    779    0
rate|4bddb2f2…                 BOUND   1594    779    3
rate|78b06c46…                 BOUND   3546    779    0
s004-scout|00c8802a…           BOUND   4836    779    3
s004-qual|00c8802a…            BOUND   7952    779    3
s004-smoke|00c8802a…           BOUND   3061    779    3
partition 可派生 9 / 不可派生 0

INCLUDED 图像帧 23,706，已绑定 23,549 = 99.3%
```

（99.3% 高于 §11.3 的 98.2%：子树搜索修复额外收回了
`ut-p1-m2-rate-002-002-rerun-stopped-scene-defect` 的 259 帧。）

**回归**：新增 `tests/test_dist_data_round8_followup.py` 14 用例，对候选 4 的
`tools/dist_data/`（`git stash` 隔离实测）**10/14 失败**，修复后 14/14 通过。
另按核验意见强化两条 §20.3 点名回归：
`test_ambiguous_manifest_hard_fails_without_parent_fallback` 原先把「父级快照」
放在**兄弟目录**、根本走不到该分支（已改为 unit 内真祖先）；
`test_unverified_ref_color_cannot_resolve_or_enumerate` 的枚举半边原是**对空
列表的循环**、恒真（已改为显式空断言 + 一个非空对照域）。

**核验同时确认的诚实口径**：§20.3 的 16 条点名回归里，
`test_audit_panel_key_uses_frozen_slash_separator` 与
`test_painter_order_uses_camera_forward_depth` 在修复前即通过——因为
`audit_tool.py` 与 `project_boxes.py` 与轮 8 前**字节相同**，BC-DATA-14/-15 是
对既有实现的**裁定追认**。这两条是**钉桩**不是回归，本证据不把它们计入
「修复前必失败」的条数。

**最终验证**：focused 366 → **380/380 双解释器全绿**；全套 535 基线 →
**915**，失败仍只有既有两项 CSRT/opencv-contrib，新增失败 0；dry-run 分类
逐项不变（29,923 / zero-multi 0）；`runtime/dist-data/` 仍不存在。

---

## 12. 复核轮 2 返工（第 5 个候选，2026-08-27）：F11 / F13 / F14

复核 verdict 与 finding 原文：`docs/reviews/P1-VLM-DATA-001.md` Round 2
（`REWORK_REQUIRED`，F11–F14 全 CLASS_2，零 CLASS_1）。

### 12.0 本批次的授权与范围口径（如实先写）

- **接受角色对本轮尚未作返工归因**（复核轮 2 之后没有接受轮 10）。本批次
  按**用户在实现会话中的直接指示**开工：「先动 F11/13.14，12 等待裁定」。
  该指示属关键授权，实现角色对 `docs/authorizations.md` 只读，**须由接受或
  辅助角色补记账本**；账本补记前，本批次的开工依据只有本节这段转述。
- **F12 一行未动**。它的闭合以接受角色对 BC-DATA-13 (b)「已有 manifest」
  检查范围的裁定为前提（unit 子树内全部 manifest ↔ 明文收窄到 unit 根）。
  实现角色不得自行重新解释 binding clarification，故 `resolve_frame_scenario`
  的 (b) 分支与 `_unit_subtree_snapshot` **保持候选 4 的字节**。
- **C3-3 未应用**：CLASS_3 的分级复判与逐字应用属接受角色，实现角色无权。
- 范围仍是已授权的纯离线集合：`tools/dist_data/` + `tests/test_dist_data_*.py`
  + 本证据 + 状态板。`controller/`、`Assets/`、`config/`、`ProjectSettings/`、
  packages lock、`runtime/` 零改动；`runtime/dist-data/` 仍不存在（实测）。
  未开正式 S1–S8 工件、人工审计、D1–D3/C1、模型/下载/API/GPU、Unity/Play、
  任何 scenario/session/run ID。

### 12.1 F11：角色装配改为「不可绕过」，而不是「有装配器可用」

复核的判据是**生产路径上是否真的生效**，不是成员是否存在。修法照缺陷 3
（S7 重新派生）的模式，把装配移进被调用方，让驱动无从漏传：

| 变更 | 文件 | 效果 |
|---|---|---|
| `assign_splits(atoms, catalog_entries)`：删除带空默认值的 `per_frame_object_roles`，改为**必填**的 catalog 记录；角色在函数内部由 `sample_roles_from_entries` 派生 | `tools/dist_data/make_splits.py` | 调用方既不能漏传角色，也不能交一份与 catalog 不一致的角色表 |
| `build_g0_report(...)`：删除独立的 `exposure` 形参，改为 `exposure = splits_payload["exposure_matrix"]` | `tools/dist_data/g0_report.py` | 报告与 S4 工件不可能各说各话；缺该成员时 KeyError 硬失败，不静默补空表 |
| 唯一端到端驱动 `_splits()` 改为 `assign_splits(atoms, self.entries)`；`_frozen_and_report()` 删掉 `exposure=make_splits.exposure_matrix([])` | `tests/test_dist_data_pipeline.py` | 管线落盘的 splits 工件自带 16 条逐 sample 角色与非空 exposure 汇总 |

**具名回归**（按复核原文落在唯一端到端驱动上，不是装配器单测）：

- `PipelineTest.test_splits_artifact_carries_assembled_sample_roles`
- `PipelineTest.test_g0_report_exposure_comes_from_the_splits_payload`

### 12.2 F13：`_self_removed` 只用条目自带容差

`unadjusted_base` 的 phantom 候选记录现在随身携带**本条目**的
`match_tolerance_m`；`apply_layout._self_removed` 只用它，不再调
`_phantom_match_tolerance`（该函数已删除，无其他调用点）。缺字段时按 `0.0`
（恰等）处理，是最严的一侧。方向与 BC-DATA-18 在逆施侧的裁定一致。

**具名回归**：`tests/test_dist_data_review2.py`

- `test_neighbour_removal_cannot_cancel_phantom_registration`（修复前必失败）
- `test_self_removal_at_the_same_original_still_cancels_the_phantom`（对照组，
  修复前后均通过——证明修复没有把「自己移除自己」这条也一并关掉）
- `test_fixture_separation_is_between_entry_tolerance_and_half_diagonal`
  （夹具前提断言：`0.1 m < 2 m < 2.121320 m`）

### 12.3 F14：`NOT_MECHANIZABLE` 的定点复看

`tests/test_dist_data_round8.py` 模块 docstring 「§20.3 点名的**十二条**回归」
→ 「**十六条**」。并非只改数字：逐条比对了 §20.3 的 16 个点名，
**16/16 都在该文件中以逐字一致的函数名存在**（机械核对，非目检）。
方向仍是原来的少报，未掩盖任何缺失回归。

### 12.4 修复前红 / 修复后绿（两种独立取法）

**(1) 候选 4 原封接线上的语义红**（先写用例、production 一行未动时实测）：

```
FAIL test_splits_artifact_carries_assembled_sample_roles
     AssertionError: [] is not true : catalog 非空时 sample_roles 不得为空（BC-DATA-2/19）
FAIL test_g0_report_exposure_comes_from_the_splits_payload
     AssertionError: {} is not true
FAIL test_neighbour_removal_cannot_cancel_phantom_registration
     AssertionError: 0 != 1 : 邻居实例被本布局类移除，不得取消另一位置的 phantom 登记（fail-open）
（对照组 test_self_removal_at_the_same_original_still_cancels_the_phantom 修复前即通过）
```

**(2) 只回退 `tools/dist_data/`、保留 tests/ 的隔离重跑**（workflow §4.4 (2)
的实现者侧自证；接受角色仍须自己再做一次）：`Ran 5 tests … FAILED
(failures=1, errors=2)`，恢复后工作树 diff 的 SHA-256 与回退前逐字节相等
（`7dbf8932…0077`）。

**修复后**：

```
python3 3.14.6        focused 385/385 OK
.venv-yoloe 3.12.13   focused 385/385 OK
.venv-yoloe 全套       920 tests，failures=1 errors=1 skipped=1
                      —— 仍只有既有两项 CSRT/opencv-contrib：
                      test_trackers.TrackerAdapterTests.test_pinned_opencv_csrt_initializes_and_updates
                      test_track_loop.TrackLoopTests.test_cli_runs_pinned_csrt_to_a_versioned_summary
                      新增失败 0（基线 915 → 920，正是本批次新增的 5 条）
```

裸 `python3` 跑**全套**不是基线：该环境缺 numpy/PIL/cv2，9 项一直是导入期
错误，与本批次无关；全套基线一律以钉死的 `.venv-yoloe` 为准。

### 12.5 真实归档确定输出：F13 改动**未**触动今日的派生

只读复跑 S1 + 真实 `build_layout`（内存喂 inventory，零工件、零 ID、零写盘），
与候选 4 记录逐项相等：

```
S1 29,923 条；zero_match 0 / multi_match 0
decision: EXCLUDED_DERIVED 77 / EXCLUDED_DIAGNOSTIC_CHANNEL 128 /
          EXCLUDED_UNRELEASED 30 / INCLUDED 29,262 / INVENTORY_ONLY 426
逆施前提 = config/scenario.default.json（sha f9c92052…）

partition                      状态    帧     实例  phantom
detect-scout1|68170d80…        BOUND    768    779    0
m3-armA|f9c92052…              BOUND    896    779    0
m3-armB|f9c92052…              BOUND    640    779    0
rate|4bddb2f2…                 BOUND   1594    779    3
rate|78b06c46…                 BOUND   3546    779    0
s004-qual|00c8802a…            BOUND   7952    779    3
s004-scout|00c8802a…           BOUND   4836    779    3
s004-smoke|00c8802a…           BOUND   3061    779    3
scene-val|f6005eb4…            BOUND    256    779    0
partition 可派生 9 / 不可派生 0
INCLUDED 图像帧 23,706，已绑定 23,549 = 99.3%
runtime/dist-data/ 存在：False
```

这正面证实了复核对 F13 的定性：**今日归档纯潜伏**（default 3 条 removal →
3 候选；s004 三个 partition 与 `rate|4bddb2f2…` 各 3 phantom 存活，与修复前
相同）。按 BC-DATA-10/-11/-12 的「今日未触发不降格」标准修复，不是因为
数字变了才修。

### 12.6 未做、退回接受角色的事项

1. **F12**（BC-DATA-13 (b)「已有 manifest」的检查范围）——等裁定。取
   「unit 子树内全部 manifest」时，绑定的具名回归应是：unit 子树内嵌套
   manifest 声明异 sha 的 fixture 下 (b) 关联必须不成立（按当前代码必失败，
   实测返回 `appendix_a2_archive_provider` BOUND）。
2. **C3-3**（证据 §11.2 文件列多列 `audit_tool`）——CLASS_3 复判与应用属
   接受角色。
3. 复核的 5 条观察项未处置：`_unit_subtree_snapshot` 的子树快照矛盾语义与
   F12 同属一个函数群，宜同批定；`test_scout4_family_binds_via_family_manifest`
   的名实出入亦然。三者都等 F12 裁定后一并做，本轮不动。
4. `UNITY_NA` 仍不由实现角色主张；本批次 PLAY_GOVERNING 增量仍只有
   `tools/dist_data/` 与 `tests/test_dist_data_*.py`，复核轮 1/2 的附议条件
   （纯离线）未被越出。

### 12.7 给复核角色的复核范围（本批次增量）

本批次的复核范围**不在此处手写计数**（COORD-007 R7：可派生量一律运行时
解析）。范围 = `git diff --name-only <上一通过候选或复核轮候选>..<本候选>`
按 workflow §4.4 的**唯一权威** PLAY_GOVERNING 定义过滤后的结果——该定义
只引用、不复抄；端点与候选同样运行时派生，不在本证据里钉当前 SHA。
交复核时把解析出的路径**逐行**列出，而不是给一个文件数——数出错时操作员
会照着少查（复核轮 3 F15 即由此产生）。建议重点：

1. `make_splits.assign_splits` 的必填参数是否真的消除了「传空」的生产路径，
   以及 `sample_roles` 的 split 回填是否与 `frames_by_split` 一致（被 test/D3
   连带规则 dropped 的帧其角色应当整体不出现，而不是落到某个 split 上）。
2. `g0_report.build_g0_report` 删掉 `exposure` 形参后，报告的
   `exposure_matrix` 是否与同一份 `splits_payload` 严格同一对象值；
   `tests/test_dist_data_gate.py` 的合成载荷补了 `exposure_matrix` 是否算
   绕过（本角色认为不算：它测的是门判定，且显式空表）。
3. `bind_layout._self_removed` 的新容差是否覆盖了「候选来自旧调用方、无
   `match_tolerance_m` 字段」的路径（缺字段 → 0.0 → 只有恰等才取消）。
4. §12.5 的真实归档表请独立复算，重点是 phantom 列 0/0/0/3/0/3/3/3/0 与
   修复前完全相同。
5. F12 未动是**有意为之**，请按未闭合处理，不要因本批次通过而认为它闭合。

---

## 13. 复核轮 2 返工续：F12 / BC-DATA-20（同一停点，第 5 个候选完成）

接受轮 10（提案 §22）在本会话进行中落盘并以 **BC-DATA-20** 裁定了 F12 的
检查域，用户随即指示继续做完 F12。§12 里「F12 等裁定」的口径到此解除；本节
是同一批次的续做，四条 finding 一并回到同一个 §4.3.1 停点。

### 13.1 改了什么

| 变更 | 文件 |
|---|---|
| 新增 `a2_subtree_consistency(repo_root, unit, provider_sha256)`：BC-DATA-20 的检查域实现 | `tools/dist_data/bind_layout.py` |
| `resolve_frame_scenario` 的 A.2 分支改调它，取代原来只读 `unit/manifest.json` 的检查 | 同上 |
| `_manifest_scenario_sha` 拆出 `_manifest_declarations`：**不可读/不可解析**返回 `None`，**零个声明**返回 `[]` | 同上 |

拆分的理由是 BC-DATA-20 里这两种情形后果不同：不可读 → (b) 关联不成立；
零声明 → 按 BC-DATA-13 (v) 视为无声明、不构成矛盾。原函数把两者都折成
`None`，无法承载该区分。`_manifest_scenario_sha` 的对外行为逐字不变。

检查域按 §22.2 逐条实现：

- **(1) 边界**：只遍历 `repo_root/unit` 及其后代；每个候选 `resolve()` 后必须
  仍在该 root 内，否则不入域（不跟随越界链接补证）。`rglob` 本身也不递归
  进符号链接目录。今日 `runtime/` 下符号链接数 = **0**（实测）。
- **(2) 证人闭集**：任意深度 basename 恰为 `manifest.json` 的归档 manifest；
  以及任意深度、通过 `is_allowed_embedded_snapshot` 的内嵌快照（与
  `_unit_subtree_snapshot` 同一判据）。sidecar/truth/其他 JSON 不入集合。
- **(3) 判据**：按相对路径升序统一求值——根级/祖先/最近文件**没有**覆盖旁支
  矛盾的优先权。每个非空声明与每份合格快照的实测 SHA 都必须等于 provider 的
  实测 SHA；同字节多副本允许。
- **(4) 不可证即不关联**：返回确定性的 `reason` / `path` / `declared_sha256` /
  升序 `witnesses`；`resolve_frame_scenario` 据此返回 `EXCLUDED_UNBOUND_SCENARIO`，
  不再回退 sidecar/provider/父级/邻居。既有 `bind_families` 结构保证只退出
  **本 unit**，不牵连同 family 的其他 unit 或其他 partition。
- **(5) 成功条件不放宽**：`scenario_id == p1-scene-004` 的前置与 provider 字节
  一行未动；域内无显式证人时照常 BOUND。

### 13.2 具名回归（`tests/test_dist_data_review2.py`）

- `test_a2_nested_manifest_consistency_is_enforced_across_unit_subtree`
  （§22.3 (2) 点名）：正例用 scout-3 **自己的**真实旁支 manifest
  `…-20260729/session/manifest.json`（声明 `00c8802a…b514`，恰等于 provider
  实测 SHA）→ BOUND；负例把**另一份真实归档、字节不改写**的
  `runtime/runs/rate20-calib/manifest.json`（声明 `4bddb2f2…9d2`）放到同一个
  旁支位置 → 必须 UNBOUND，并点名见证路径。前置 `scenario_id` 两例都由帧
  sidecar 提供，走的是同一条 (b) 分支，差别只在这份显式证人。
- `test_a2_subtree_snapshot_conflict_is_not_hidden_by_the_provider`
  （§22.3 (3)）：子树内放两份**真实归档**场景字节（A.2 provider 与
  `config/scenario.default.json`），字节不唯一使 `_unit_subtree_snapshot` 返回
  `None`（既有 fail-closed），从而落到 (b)；修复前这里直接 BOUND、矛盾被吞掉。
- 三条对照组：`test_fixture_reproduces_the_reported_side_branch_position`
  （夹具前提：旁支既非帧祖先、不在 unit 根、也不是快照，且该 unit 无关联 run
  目录）、`test_a2_association_survives_when_the_subtree_has_no_explicit_witness`
  （§22.2 (5) 不放宽成功条件）、`test_a2_consistency_domain_stops_at_the_source_unit`
  （兄弟 unit 的矛盾 manifest 不入域——不扩成全仓扫描）。
- 追加一条不可读分支的对照：`test_a2_unreadable_subtree_manifest_blocks_the_association`，
  用归档里的**真实 JPEG 字节**（一字节不改）占住那个 manifest 路径，
  `json.loads` 必然失败——不手写损坏的 JSON。

夹具全部按真实相对路径把归档字节复制进临时根，经生产入口
`resolve_frame_scenario` 求值，无一处手写 JSON 状态，也不直接测新 helper。

### 13.3 修复前红 / 修复后绿

只回退 `tools/dist_data/`、保留 tests/ 的隔离重跑（恢复后工作树 diff 的
SHA-256 逐字节相等）：

```
FAIL test_a2_nested_manifest_consistency_is_enforced_across_unit_subtree
     AssertionError: 'BOUND' != 'EXCLUDED_UNBOUND_SCENARIO'
     （实测返回 source=appendix_a2_archive_provider —— 与复核 F12 原文一致）
FAIL test_a2_subtree_snapshot_conflict_is_not_hidden_by_the_provider
     AssertionError: 'BOUND' != 'EXCLUDED_UNBOUND_SCENARIO'
Ran 5 tests … FAILED (failures=2)   ← 三条对照组修复前即通过
```

修复后：

```
python3 3.14.6        focused 391/391 OK
.venv-yoloe 3.12.13   focused 391/391 OK
.venv-yoloe 全套       926 tests，failures=1 errors=1 skipped=1
                      仍只有既有两项 CSRT/opencv-contrib，新增失败 0
                      （基线 915 → 926 = 本轮新增的 11 条）
```

### 13.4 §22.3 (4)：真实归档确定输出**逐字节未漂移**

只读复跑 S1 + 真实 `build_layout`（零工件、零 ID、零写盘），输出与 §12.5
的 F12 修复前记录 **diff 为空**：

```
S1 29,923 条；zero_match 0 / multi_match 0
partition 可派生 9 / 不可派生 0；实例 779 × 9
phantom 0/0/0/3/0/3/3/3/0（detect-scout1、m3-armA、m3-armB、rate|4bddb2f2、
                          rate|78b06c46、s004-qual、s004-scout、s004-smoke、scene-val）
INCLUDED 图像帧 23,706，已绑定 23,549 = 99.3%
runtime/dist-data/ 存在：False（修复前后均实测）
```

scout-3 的旁支 manifest 今日声明恰等于 provider SHA，所以 BC-DATA-20 生效后
它仍然 BOUND —— 与复核对 F12「今日纯潜伏」的定性一致。

### 13.5 两条须由复核/接受角色定夺的披露（实现角色不自行降格）

1. **歧义硬失败的作用域被动扩大**。§22.2 (3) 明写「多个互异 SHA 仍是既有歧义
   硬失败」，我按字面执行；但既有实现只在**祖先 / 关联 run / unit 根**的
   manifest 上调用该判定，现在子树内任意深度的 manifest 也会触发。后果不同：
   该 `LayoutError` 从 `bind_families` 抛出、在 `build_layout` 的 per-partition
   `try` **之前**，会中止整个 S2，而不是只使一个 unit unbound。今日归档无任何
   manifest 含多个互异 SHA（51 份经 `_manifest_declarations` 递归实测：29 份各恰
   1 个声明、22 份 0 个、歧义 0 份、不可读 0 份），故未触发。若接受
   角色认为应改为「只使该 unit unbound」，那是对 BC-DATA-13 (v) 的修订，超出
   实现角色权限。
2. **只读诊断耗时约翻倍**：同一台机器上 S1+S2 全量复跑由 **1:51 → 4:04**。
   原因是 A.2 分支对每一帧都重扫一次 unit 子树（s004 三族共 15,849 帧）。
   结果正确、无缓存即无过期风险；但复核与接受都要复跑这条链，故先如实报出。
   可选优化是按 `(repo_root, unit, provider_sha)` 在单次 `bind_families` 内做
   记忆化——本轮**没有做**：缓存过期恰恰是本 finding 家族「矛盾被静默掩盖」的
   同一失败模式，是否值得引入应由复核/接受裁定，不由实现角色自选。

### 13.6 给复核角色的复核范围（F12 增量）

1. `a2_subtree_consistency` 是否逐条对上 §22.2 的五款，特别是「根级/祖先/最近
   文件没有优先权」是否真的由「按相对路径升序统一求值」实现，而不是任何形式的
   就近短路。
2. `_manifest_declarations` 的 `None`（不可读）与 `[]`（零声明）二分是否在所有
   调用点都被正确消费；`_manifest_scenario_sha` 的对外行为是否逐字未变。
3. `_inside` 的越界判据（`resolve()` 后必须等于 root 或以 root 为祖先）是否覆盖
   了 `..`、绝对路径链接与目录链接三种形态；今日 `runtime/` 无符号链接，故这条
   是**潜伏**保护，请按「今日未触发不降格」标准核。
4. §13.5 两条披露请独立判断，尤其第 1 条的作用域扩大是否越出了 BC-DATA-20 的
   授权范围。
5. §13.4 的真实归档表请独立复算：9/9、23,549/23,706、phantom 0/3 分布与
   `runtime/dist-data/` 不存在。

---

## 14. 接受轮 14 §26.2：像素适配器 + S0–S9 生产 driver（第 6 个候选，2026-08-27）

裁定：提案 §26（`WITHIN_EXISTING_IMPLEMENTATION_AUTHORIZATION / CODE_ONLY`）。
本批次**只算代码**：不在真实归档上产出任何正式工件，不渲染或执行 A1/A2/A3
人工审计，不安装依赖，不动 API/GPU/Play/ID。`runtime/dist-data/` 前后均不存在
（实测）。

### 14.1 新增两个模块

| 文件 | 职责 |
|---|---|
| `tools/dist_data/pixel_source.py` | `ArchivePixelSource`：同时实现 `PixelSource.crop_rgb` 与 `GraySource.gray_matrix`，另附 `phash()`。只读，缺库/坏字节/尺寸不合同一律 `PixelError` |
| `tools/dist_data/run_pipeline.py` | `PipelineDriver` + CLI：把已接受的 S0–S9 阶段函数接成唯一生产入口；默认动作是**只读 preflight** |

`tools/dist_data/bind_layout.py` 有一处**披露的**小改动：`build_layout` 增加
可选关键字参数 `inventory=`。缺省仍经 store 读冻结的 S1 工件（禁行边照旧
生效）；只读 preflight 传内存里的 S1 载荷，从而在**不落盘**的前提下跑完整的
S2（含逐 partition 几何派生）。`inputs` 在该路径下显式记为
`{"source": "in_memory_preflight"}`——不伪造 attempt/SHA 让它看起来引用了
冻结工件。理由见 §14.5。

### 14.2 适配器：让图像库只负责解码

灰度换算与 32×32 降采样都在本模块用显式算术完成，**不调用**
`Image.convert("L")` 或 `Image.resize()`。原因是那两者的结果依赖 Pillow 版本、
SIMD 与重采样滤波器实现，而 pHash 直接决定近重复并簇 → 原子 → 切分 → F3/F4；
让门数字随环境漂移是不可接受的。

- **降采样不是自由度。** 实测归档全部 **24,152** 张 jpg 都是 **640×480**，
  `640 % 32 == 480 % 32 == 0`，所以块均值是精确整除的块平均（20×15），
  无插值、无滤波器选择余地。尺寸不整除时硬失败，绝不回退插值。
- **求值顺序刻意选成「先按通道求整数和，再算一次 luma」**：luma 对 R/G/B 线性，
  故 `mean(luma) == luma(mean)`，定义不变，但整数求和是精确的，浮点结合律
  不再参与。numpy 路径与纯 Python 路径因此**逐位相同**，由
  `test_gray_matrix_numpy_and_pure_python_paths_agree_bitwise` 钉死（实测
  numpy 1.8 ms / 纯 Python 22.5 ms per frame，结果 `==`）。
- **解码缓存按 `(相对路径, st_mtime_ns, st_size)` 归键**，字节一变即失效。
  按路径单键缓存会让陈旧内容静默生效，正是复核轮 2/3 那一族 finding 的失败
  模式；`test_decode_cache_invalidates_when_the_bytes_change` 钉死。

### 14.3 driver：把「不可绕过」做成机制

- **每一次跨阶段取数都走 `ArtifactStore.read(..., requesting_stage=N)`**，
  所以 §2 的禁行边真的参与生产路径，而不是只在单测里被断言
  （`test_forbidden_edge_holds_on_the_production_read_path`）。
- **每一次产出都走 `store.write`**（create-once + 字节幂等；
  `test_rerunning_a_stage_is_byte_identical`）。
- **S6 人工审计：driver 拒绝合成。** F1 的冻结定义是「验证 = S5 判定 + A1
  通过」，没有审计工件就没有双验证对象；`stage7_gate` 在缺
  `audit@<attempt>` 时抛 `PipelineError` 并点名该定义
  （`test_stage7_refuses_without_the_human_audit_artifact`）。凭空当作通过是
  fail-open，且 A1/A2/A3 的渲染与执行在 §26.2 的明确不包含清单里。
- **收束点写 S9、不进 S8**：门未过 → `INSUFFICIENT_SYMBOLIC_GROUNDING_DATA`；
  `SplitTerminal` 同样收束。两条都保全已有工件
  （`test_closed_gate_records_a_stop_point_and_never_reaches_s8`、
  `test_split_terminal_also_stops_before_s8`）。流程判断集中在可测的
  `run_stages()` 里，便于逐条复核。
- **BC-DATA-15**：`audit_strata()` 按 `camera_forward_depth` 排序
  （tie-break 为 `sample_id` 的 UTF-8 字节）再等分三段，只产出人工审计需要的
  分层输入，不判定、不生成 panel、不推进审计状态机。
- **一个未加字段的取舍**：S8 需要相机以把 `amodal_px` 归一化，而 S3 载荷不带
  sidecar。没有往 S3 payload 里加字段（那是改 schema），改为由 `_camera_for()`
  按 frame_id 重读该帧自己的 sidecar 源字节。

### 14.4 测试与实测

新增 `tests/test_dist_data_pixels.py`（13）与 `tests/test_dist_data_driver.py`
（14）。适配器的金标全部**用归档真实帧字节**并由用例**独立复算**（不信适配器
自述）：crop 窗口按「像素中心落在框内」逐像素枚举复算，块均值按整数通道和
逐块复算，坏图用归档里的真实 JSON sidecar / 截断字节冒充 jpg。

```
python3 3.14.6        focused 418，OK（9 skip：全部是需要 Pillow 的金标）
.venv-yoloe 3.12.13   focused 418/418 OK 零 skip
.venv-yoloe 全套       953，failures=1 errors=1 skipped=1
                      仍只有既有两项 CSRT/opencv-contrib，新增失败 0
                      （基线 926 → 953 = 本批次新增的 27 条）
```

**裸 `python3` 的 9 项 skip 是本批次引入的新形态，如实报出**：该解释器没有
Pillow，金标无法解码 jpg。fail-closed 与纯算术判据的用例不依赖任何图像库，
两个解释器都跑；钉死环境仍是零 skip。

**§26.2 (e) 的只读 preflight（真实归档，零写盘）**，经新 CLI
`python -m tools.dist_data.run_pipeline --repo-root .` 实测：

```
records 29,923 | zero_match 0 / multi_match 0 | INCLUDED 图像帧 23,706
9/9 partition BOUND，invalid 0，实例 779 × 9
phantom 0/0/0/3/0/3/3/3/0（顺序同 §13.4）
bound_frames 23,549 = 99.3%
unbound source units 4（与复核轮 3 的「157 帧四 unit 无字节」同一组）
wrote_nothing = true；runtime/dist-data/ 前后均不存在；runtime/ git 干净
两个解释器各跑一遍，输出 JSON 逐字节相同
```

与 §13.4 的记录逐项相同——新增的适配器与 driver **没有使任何绑定漂移**。

### 14.5 退回接受角色的事项（实现角色不自行裁定）

1. **两处合同未给定的像素自由度，本模块显式取定并请逐条确认**（取的都是
   可独立复算、与库实现无关的那一侧）：
   (a) `GRAYSCALE_COEFFICIENTS = (0.299, 0.587, 0.114)`（ITU-R 601-2 luma，
   float 域、无整数截断）；(b) `crop_rgb` 的取像素判据 = **像素中心落在框内**
   （`x0 ≤ i + 0.5 < x1`）再与图像边界求交，空集返回空序列 → `UNVERIFIED`。
   §2.4/§2.5 与 `contract.py` 都没有钉这两项，而它们都会改变门数字。
   **本批次没有产出任何正式工件，所以还没有任何结果被冻结在这两个选择上**；
   若接受角色另有裁定，改一个常量即可。
2. **`build_layout` 的 `inventory=` 参数**（§14.1）是为了让只读 preflight 跑
   完整 S2 而不落盘。替代方案是 preflight 只跑到 `bind_families`——但那样
   `instances`/`phantoms` 只能报 0，是假精度，而候选 4 的阻断缺陷正是
   「只跑 build_inventory + bind_families、从未触及 build_layout」才漏掉的
   （§11.1 已把整条链列为固定自查项）。请确认这一取舍。
3. **preflight 耗时（同机实测，两个解释器都跑了一遍）**：
   `python3` 3.14.6 **3 分 54 秒**、`.venv-yoloe` 3.12.13 **7 分 16 秒**。
   与 §13.5 第 2 条的 `python3` 序列对齐看：F12 前 1:51 → F12 后 4:04 →
   本批 driver preflight **3:54**——**driver 本身没有再引入耗时**，4:04 与
   3:54 是同一量级的同类测量，多出来的一倍只是钉死解释器比 3.14.6 慢。
   仍未加记忆化，理由同 §13.5 第 2 条。
   **附带的确定性证据**：两个解释器的 preflight 输出 JSON **逐字节相同**
   （`python3 == venv` 实测 `True`），含全部 partition、phantom 与计数。
4. **覆盖缺口，如实列出**：`--run` 分支的阶段序在自动测试里是用合成的
   `order` 列表覆盖 `run_stages()` 的流程判断，**没有**端到端跑过真实的
   S0→S2（那需要在真实归档上落盘，本轮未授权）。审计叠加图 renderer 按
   §26.2 未实现。

### 14.6 给复核角色的复核范围（本批次增量）

范围仍按 §12.7 的口径运行时解析，不在此写计数。建议重点：

1. `pixel_source.gray_matrix` 是否真的与库的 `resize`/`convert("L")` 无关；
   两条求和路径逐位相同这一性质是否被测试真正覆盖，还是只测了同一条路径。
2. `crop_rgb` 的半开区间与边界求交是否有 off-by-one；空集返回空序列在
   `estimate_color` 里是否确实走向 `UNVERIFIED`（fail-closed 方向）。
3. driver 是否真的**没有**复制任何阶段算法——请逐个 `stage*` 方法核对它只做
   取数、调用、落盘三件事。
4. `stage7_gate` 拒绝合成审计这一条，是否与 F1 的冻结定义一致，有没有留下
   任何「空审计等于通过」的旁路。
5. `build_layout` 的 `inventory=` 分支是否可能被正式路径误用（正式路径必须
   仍走 store 读取），以及 `inputs` 的 preflight 标记是否足以防止误认。
6. §14.5 四条披露请独立判断。

---

## 15. 复核轮 4 返工：F17 / F18 / F19（F16 等接受裁定，2026-08-28）

复核 verdict 与 finding 原文：`docs/reviews/P1-VLM-DATA-001.md` Round 4
（`REWORK_REQUIRED`，F16–F19 全 CLASS_2，零 CLASS_1）。

### 15.0 授权与范围口径（先写）

- **接受角色对本轮尚未作返工归因**（复核轮 4 之后没有接受轮 16）。本批次
  按**用户在实现会话中的直接指示**开工：「先动 F17/F18/F19」。该指示属关键
  授权，实现角色对 `docs/authorizations.md` 只读，**须由接受或辅助角色补记**。
- **F16 一行未动。** 它的闭合以接受角色对「§2.3 历史布局交叉验证在组合中的
  落点」的裁定为前提（S2 载荷内逐族计算，还是 S3 前独立步骤）。实现角色不得
  自行选择落点，`cross_validate_layout` 的接入与 `layout_binding_valid` 的
  派生因此都留在原状。
- 范围仍是接受轮 14 §26.2 的 code-only 集合。真实归档只跑了只读 preflight，
  `runtime/dist-data/` 前后均不存在；未开正式工件、audit、模型/API/GPU、
  Play 或任何 ID。

### 15.1 F17：`INVALID` partition 只让**它自己**的帧退出

`stage3_frames_catalog` 现在在取几何前检查 `binding_status`，非 BOUND 的
partition 其帧整体退出并计入新的 `skipped_invalid_frames`。原实现直接取
`partition["instances"]`，而 `build_layout` 的异常分支**不写**该键，于是一个
派生失败的 partition 会 `KeyError` 掉整个 S3——既违反 BC-DATA-18 的 partition
局域隔离（合同要的是「只使该 partition INVALID」），也让管线不可用。

**具名回归**：`InvalidPartitionCase.test_invalid_partition_excludes_its_frames_without_killing_s3`。
夹具按 `build_layout` 异常分支的**真实形态**构造（只有 `binding_status` /
`reason`，没有 `instances`/`phantoms`），一 BOUND + 一 INVALID；断言 BOUND 侧
4 帧照常产出、INVALID 侧 4 帧计入 `skipped_invalid_frames`、catalog 里只剩
BOUND 侧的族。

### 15.2 F18：A1/A2 分层样本域收回到目录车辆

`audit_strata` 原来只按 `status == "OK"` 过滤。BC-DATA-16 只把 building /
nature / prop 挡在 blocking/referable/exposure 外，**不挡在状态机外**，所以
它们照样取得 OK 状态并进入三分位样本池，未来 panel 生成会把不可审计的非车辆
混进 12 格配额与分母。现按 `contract.class_for_scene_object(object_id) is not
None` 收回到 §2.7 的审计对象域。

**核实了复核的一处附带说法**：「phantom 已被 OK 过滤天然排除」——属实，
phantom 的状态是专用值 `PHANTOM` 而非 `OK`（本轮实测投影输出确认），所以
上一行过滤即已排除，不依赖名字形状。

**具名回归**：`AuditDomainCase.test_building_reaches_ok_status_but_is_not_an_audit_object`。
夹具先断言前提（建筑**确实**能取得 OK 状态），再断言它不得进入样本池。

### 15.3 F19：归档守卫补齐，并按复核指定的环境定点复跑

`test_corrupt_bytes_fail_closed` 与 `test_truncated_bytes_fail_closed` 原来
只有 `@needs_pillow`，缺 `ArchiveFrameTest` 那样的归档守卫。现把守卫提为模块级
`require_archive()`，三处统一调用。

**这条的要害不只是代码**：复核纪律要求的重跑环境正是**不带 `runtime/` 归档的
一次性副本**，而 §14.4 的披露只写了主树的两种形态（钉死零 skip / 裸 9 skip），
漏掉了这一种。本轮在无归档副本上双解释器各跑一遍，前后对照：

```
修复前  .venv-yoloe 3.12.13   Ran 420  FAILED (errors=2, skipped=40)
        python3     3.14.6    Ran 420  OK (skipped=42)   ← 被 Pillow skip 掩盖
修复后  .venv-yoloe 3.12.13   Ran 420  OK (skipped=42)
        python3     3.14.6    Ran 420  OK (skipped=42)
```

错误全部转为 skip，与复核给的闭合判据一致；按其指示未新增测试。

### 15.4 顺带处置的一条观察项

`preflight()` 的 `wrote_nothing` 原是硬编码 `True`，现改为由前后两次存在性
检查**派生**（`(not before) and (not after)`）。

### 15.5 修复前红 / 修复后绿

只回退 `tools/dist_data/`、保留 tests/ 的隔离重跑（恢复后工作树 diff 的
SHA-256 逐字节相等）：

```
ERROR test_invalid_partition_excludes_its_frames_without_killing_s3   KeyError: 'instances'
FAIL  test_building_reaches_ok_status_but_is_not_an_audit_object      8 个建筑样本进入样本池
Ran 16 tests … FAILED (failures=1, errors=1)   ← 其余 14 条修复前即通过
```

修复后：

```
python3 3.14.6        focused 420，OK（9 skip：需 Pillow 的金标）
.venv-yoloe 3.12.13   focused 420/420 OK 零 skip
无归档副本            双解释器均 420 OK (skipped=42)      ← F19 的闭合判据
.venv-yoloe 全套       955，failures=1 errors=1 skipped=1
                      仍只有既有两项 CSRT/opencv-contrib，新增失败 0
                      （基线 953 → 955 = 本批新增的 2 条）
```

### 15.6 真实归档：只读 preflight 与修复前**逐字节相同**

F17/F18 都不在 preflight 的执行路径上（它只跑 S1 + S2），但按 §11.1 的常驻
自查项仍实测而非推断：`python -m tools.dist_data.run_pipeline --repo-root .`
的输出与 §14.4 保存的同解释器结果 `cmp` **无差异**——29,923 records、
9/9 BOUND、779 实例 × 9、phantom 0/0/0/3/0/3/3/3/0、23,549/23,706、四个
unbound unit、invalid 0；`runtime/dist-data/` 前后不存在，`runtime/` git 干净。

### 15.7 未做、退回接受角色的事项

1. **F16**（§2.3 交叉验证的落点）——等裁定。裁定后的实现面至少要动三处：
   `build_layout` 或 S3 前的独立步骤里逐族计算、`stage3` 的
   `layout_binding_valid` 改为按族/partition 的结果派生、`stage7_gate` 只接受
   计算出的 `cross_validation` 而不是 `.get(..., {})`。绑定的具名回归按复核
   原文：合成世界中有真值框族的布局整体平移超阈值时，S3/S7 必须使该族帧退出
   floor 且报告记 `INVALID`（按当前代码必失败）。
2. **S5 入口过滤非车辆**（复核观察项，建议同批做）——**本轮有意未做**：它不在
   用户点名的 F17/F18/F19 内，且会改变 S5 工件内容。已复核其安全性供接受角色
   一句话裁定：`frame_world` 只查 `blocking` 内对象，而 BC-DATA-16 已把非车辆
   挡在 `blocking` 外，故它们的记录从不被读；`prospective_mother_eligible` 对
   `record is None` 与 `class_verified=False` 的处置相同；`compute_f1` 只数
   `dual_verified_object_ids`，非车辆因 `class_verified=False` 永不入选。
   **收益是实的**：正式 A1 的组数 G 与 `crop_rgb` 的像素工作量会被非车辆组
   虚增。
3. 复核轮 4 其余观察项（`SplitTerminal` 的端到端覆盖、轮 2/3 遗留项）维持原状。

### 15.8 给复核角色的复核范围（本批次增量）

范围按 §12.7 的口径运行时解析。建议重点：

1. `stage3` 的 `binding_status` 检查是否放在**取任何几何键之前**，以及
   `skipped_invalid_frames` 与 `skipped_unbound_frames` 是否语义可分。
2. `audit_strata` 的类别过滤是否与 §2.7 的审计对象域一致，会不会把**该**审计
   的车辆也误挡（phantom 由 `status` 排除，不靠名字形状——请独立复核这一点）。
3. F19：除被点名的两条外，本轮已用**无归档副本双解释器全绿（0 error）**
   反证 focused 套件内没有别的用例在缺归档时炸——`test_dist_data_review2.py`
   与 `test_dist_data_round8.py` 的归档 glob 都在各自 `ArchiveCopyCase.setUp`
   的守卫之后。请独立复算这条反证，而不是只看被点名的两条。
4. §15.7 第 2 条的安全性分析请独立判断；第 1 条 F16 仍未闭合，不要因本批次
   通过而认为它闭合。

---

## 16. F16 / BC-DATA-23：历史交叉验证接入生产 S2（2026-08-28）

裁定：提案 §28（接受轮 16，`BC-DATA-23`）。F17–F19 已在 §15 落地，本节是同一
批次里 F16 的部分。**本节末尾有一条新的阻断问题退回接受角色**（§16.5），
它决定真实归档上两个 partition 的去留，实现角色不得自行处置。

### 16.1 逐款落地

| BC-DATA-23 | 落点 |
|---|---|
| (1) 落在 S2、写 `layout` 之前 | `build_layout()` 在 partition 循环之后、`return` 之前逐 partition 验证并把结果并进载荷；`stage2_layout()` 之后才 create-once 写盘。S3 不重算。 |
| (2) 决定单位 = 精确 `(family, scenario_sha256)` | 新 `_frames_by_partition()` 只按 S1 冻结记录把 INCLUDED 帧归到 `partition_id`；不同 SHA 的 partition 各自成组，永不混算。 |
| (3) 输入只来自 S1 冻结映射与归档字节 | 新增**共用**的 `bind_layout.load_frame_truth()`，S2 与 S3 都调它（`run_pipeline` 原来那份 `_truth_row` 已删除），不再有两套会漂移的路径规则；相机只由同名 sidecar 构造（`_camera_for_frame`）。 |
| (4) schema 分轨 | `cross_validate_partition()`：`scouting` 只把 `distractor_id` 恰一映射到本 partition 静态实例的非空 bbox 交给 `cross_validate_layout`；`m3` 只把 `target_world_*_m` + 同帧 truth box 交给 `target_world_center_hit_ratio`，`pair_count` 恒为 0（不补静态对）、不算 target IoU；全帧无冻结 truth source → `NOT_APPLICABLE_NO_ARCHIVED_FRAME_TRUTH`；有 source 却零可检样本 → `INVALID`。 |
| (5) 载荷与报告不可省略 | `layout["cross_validation"]` 按 partition id 排序，逐项含 `mode/status/reason/pair_count/sample_count` 与对应指标；失败同步把该 partition 置 `INVALID`。`build_g0_report` 的独立 `cross_validation` 形参**已删除**，改读 `layout_payload["cross_validation"]`（缺成员 KeyError 硬失败），与 F11 对 `exposure` 的修法同构；S3 也在入口断言该成员存在。 |
| (6) S3 只消费验证后的状态 | `_partition_of_unit()` 返回 `(只含 BOUND 的几何表, 逐 unit 状态表)`；几何查找表不再映入非 BOUND，退出计数由状态表提供，`layout_binding_valid` 由 `partition["binding_status"] == BOUND` **派生**，字面量 `True` 已删除。F17 与本条同一状态源。 |
| (7) preflight 走同一 S2 | preflight 调同一个 `build_layout`，因此自动跑新验证，并逐 partition 报告诊断（见 §16.4）。 |

### 16.2 具名回归

- `test_s2_cross_validation_invalidates_shifted_static_layout_and_reports_it`
  （§28.3 (1) 点名）。夹具里**唯一的变量是 `scenario_config.json` 这一格放哪一份
  归档字节**：放该采集自己的场景 → 几何与真值同源；放 `scene-004` 的 hold →
  几何被整体改过。帧、sidecar、distractor 真值三者在两种情形下逐字节相同，
  夹具从不手写 `cross_validation`/`binding_status`。
- `test_s2_m3_target_check_uses_center_ratio_without_static_pair_backfill`
  （§28.3 (1) 点名）：断言 `mode == "m3"`、`pair_count == 0`、`iou_median is None`、
  状态由中心落框率决定。真实 m3 归档夹具实测 `center_hit_ratio = 1.0`。
- 按 §28.3 (2)(3) 把 §15 的两条改名为点名的
  `test_driver_skips_invalid_partition_and_preserves_bound_partition` 与
  `test_audit_strata_excludes_non_vehicle_occluders`。

### 16.3 修复前红 / 修复后绿

只回退 `tools/dist_data/`（恢复后工作树 diff 逐字节相等）：

```
FAIL  test_s2_cross_validation_invalidates_shifted_static_layout_and_reports_it
      AssertionError: 'cross_validation' not found in {...}  : BC-DATA-23 (5)：必有成员
ERROR test_s2_m3_target_check_uses_center_ratio_without_static_pair_backfill
      KeyError: 'cross_validation'
```

修复前那次运行还顺带证实了 F16 的 fail-open 形态：**几何是 scene-004、真值是
detect-scouting 的那个 partition，修复前照样是 `BOUND`**——这正是该条款要防的
「基础场景在采集后被改动过」。

修复后：

```
python3 3.14.6        focused 422，OK（9 skip：需 Pillow 的金标）
.venv-yoloe 3.12.13   focused 422/422 OK 零 skip
无归档副本            双解释器均 422 OK (skipped=44)
.venv-yoloe 全套       957，failures=1 errors=1 skipped=1，仍只有既有两项
                      CSRT/opencv-contrib，新增失败 0
```

### 16.4 §28.3 (5)：真实归档逐 partition 如实报告（**不为维持旧 9/9 调任何参**）

只读 preflight（零写盘，`runtime/dist-data/` 前后均不存在，`runtime/` git 干净）：

```
partition                     状态      mode      pairs  样本   centre_hit   iou_median
detect-scout1|68170d80…       INVALID   scouting     50    278   0.78        0.9999915943
m3-armA|f9c92052…             BOUND     m3            0    682   0.9765395894   —
m3-armB|f9c92052…             BOUND     m3            0    153   0.9215686275   —
rate|4bddb2f2…                BOUND     none          0      0    —             —
rate|78b06c46…                BOUND     none          0      0    —             —
s004-qual|00c8802a…           BOUND     none          0      0    —             —
s004-scout|00c8802a…          INVALID   scouting     50   4836   0.82        0.9999932120
s004-smoke|00c8802a…          BOUND     none          0      0    —             —
scene-val|f6005eb4…           BOUND     none          0      0    —             —

9 partition 中 7 BOUND / 2 INVALID；已绑定帧 23,549 → 17,945
```

**这与 BC-DATA-23 (7) 的预告一致：旧的 9/9 不能预断新验证结果。** 但两条
INVALID 的形态高度可疑，见下条。

### 16.5 **退回接受角色的阻断问题**：`cross_validate_layout` 拿 amodal 投影去比**已裁剪**的归档真值框

两个 INVALID 的指纹是同一个：**IoU 中位数 ≈ 0.99999（几何几乎完美吻合），
中心落框率却只有 0.78 / 0.82**。这两者不可能同时来自「布局被改过」——作为对照，
真正错配的几何（scene-004 几何 × detect-scouting 真值）实测是 **IoU 0.0 /
centre 0.0**。

逐对查明的根因：归档 distractor 真值框是**裁剪到视口**的可见框，而
`cross_validate_layout` 用 `project_boxes.project_aabb()` 得到的是 **amodal**
（未裁剪）框。凡是车辆跑出画面下沿的样本，两框的 x 与上沿逐位相同、只有下沿
不同，例如：

```
frame_0000000166  projected [137.1, 407.5, 229.7, 560.1]
                  truth     [137.1, 407.5, 229.7, 480.0]   ← 480 = 图像高度
```

amodal 框的中心因此落到裁剪框外，被记成「中心未命中」，而 IoU 仍然很高。
**把投影框按视口裁剪后同一批 50 对实测**：

```
amodal（当前实现）        centre_hit = 0.780   iou_median = 0.999992  → FAIL
clipped to viewport      centre_hit = 1.000   iou_median = 0.999995  → PASS
```

**实现角色不自行修**：`cross_validate_layout` 是 §2.3 的冻结阶段算法（复核轮 1
已核其实现），BC-DATA-23 与 §26.2 都明令不得复制或重新解释阶段算法。请接受
角色裁定应比 amodal 还是裁剪后的可见框；若取后者，绑定回归应是：车辆跑出下沿
的真实归档样本下，中心落框率不得因裁剪口径差异而降级。

**在裁定之前，§16.4 的两条 INVALID 不应被当作「基础场景被改过」的证据。**
本轮按合同如实报出，未调任何阈值、样本或附录 A。

另外一并报出、不构成阻断的观察：**m3-armB 的中心落框率 0.9216 距 0.9 阈值只有
0.0216**，样本仅 153；该 partition 的判定对样本集变化很敏感。

### 16.6 另一处需要确认的读法：逐帧真值**缺文件**不算「不可读」

`roots.truth_source_for()` 对每一帧都给出真值路径，但归档里逐帧真值是**部分
覆盖**的（实测 detect-scout1 768 帧只有 705 个 truth 文件）。本实现把「该帧没有
真值文件」按 `(None, schema)` 处理、交由各自合同处置，而不是 BC-DATA-23 (4) 的
「源字节不可读 → partition INVALID」——依据是 S1 自己就把 `truth_join.present`
记成逐记录的布尔事实，说明缺文件是被建模的正常状态。若按相反读法，
detect-scout1 这类明明有 705 个可检样本的 partition 会直接 INVALID。请确认。

### 16.7 给复核角色的复核范围（本批次增量）

范围按 §12.7 的口径运行时解析。建议重点：

1. `cross_validate_partition` 是否逐款对上 §28.2 的 (2)(4)，特别是 m3 分支
   **不产生任何静态对**、不算 target IoU 这两条。
2. `load_frame_truth` 现在是 S2/S3 的唯一实现——请确认 `run_pipeline` 里已无
   第二套路径规则，且两阶段拿到的 truth 逐帧相同。
3. `_partition_of_unit` 的两表拆分是否真的做到「几何查找表不含非 BOUND」，
   同时退出计数仍能区分 unbound 与 invalid。
4. `build_g0_report` 删掉 `cross_validation` 形参后，报告与 S2 工件是否不可能
   各说各话；缺成员是否确实硬失败。
5. **§16.5 与 §16.6 两条请独立判断**；在 §16.5 裁定前，§16.4 的两条 INVALID
   只是如实报告，不是「场景被改过」的结论。

---

## 17. BC-DATA-24：viewport 比较域与真值缺席语义（2026-08-28）

裁定：提案 §29（接受轮 17）。两条退回问题都按 §16.5/§16.6 报的方向裁定，
本节是落地。**这不是放宽阈值**：50 对下限、centre `>= 0.9`、IoU median
`>= 0.5`、SHA 排序、候选集与 partition 单位一字未改。

### 17.1 (1)(2) 比较域

`cross_validate_layout` 仍先用 `project_aabb()` 产生 amodal 像素框，再与该帧
`camera.viewport()` 求交；中心命中与 IoU **都只**用这个交框。amodal 为 `None`
或与 viewport 无交集 → 该对按 centre miss + IoU `0.0`。裁剪发生在**选样之后**，
候选集与前 50 对的排序不受影响（BC-DATA-24 (2)）。`project_aabb()`、S3 的
`amodal_px`、遮挡/截断状态与 m3 中心检查一律未动。

**同批修正一处夹具**：`tests/test_dist_data_layout.py` 的 `CrossValidationTest`
把「完美真值框」建成了**未裁剪的 amodal 投影**，即旧域；且原来那排实例
`x = -1+i … 1+i` 有 **40/60 完全落在视口外**，在旧域里靠「预测框 = 真值框」
互相抵消才侥幸通过。现改为 12 × 5 的在视网格（`setUp` 断言 60/60 在视口内），
「完美真值」取裁剪框，与归档 `bbox_xywh_norm` 同域。

### 17.2 (3)(4) 缺席语义

实现侧无需改动：BC-DATA-23 落地时 `load_frame_truth` 已按「缺文件 →
`(None, schema)`、存在但坏 → `TruthJoinError` → partition `INVALID`」实现，
轮 17 裁定确认了这一读法。新增回归把该语义钉死（见 §17.3 的诚实说明）。

### 17.3 具名回归与修复前红

- `test_s2_cross_validation_clips_projection_to_archived_viewport_domain`
  （§29.3 (1) 点名）：走生产 S2、消费归档帧/sidecar/truth 字节副本。同源几何
  在裁剪域 centre `1.0` / IoU `> 0.99` → `BOUND`；scene-004 错配对照仍
  centre `0.0` / IoU `0.0` → `INVALID`。另有一条辅助断言证明夹具里**确实含
  amodal 越过视口下沿的可检对**，否则本用例会在一批完全在画面内的对上空过、
  证明不了裁剪。
- `test_s2_partial_truth_absence_skips_missing_frames_without_masking_corruption`
  （§29.3 (2) 点名）：删掉三分之一逐帧真值文件（帧与 sidecar 原样保留）后
  partition 仍 `BOUND` 且 `mode` 仍是 `scouting`（缺席不得降级成
  `NOT_APPLICABLE`）；再把一个**实际存在**的归档 truth 字节副本破坏 →
  `INVALID` 且 reason 含「不可解析」。

只回退 `tools/dist_data/` 的未提交增量（恢复后工作树 diff 逐字节相等）：

```
FAIL test_s2_cross_validation_clips_projection_to_archived_viewport_domain
     AssertionError: 0.9 != 1.0            ← 未裁剪时中心命中率掉到 0.9
FAIL test_s2_partial_truth_absence_skips_missing_frames_without_masking_corruption
     AssertionError: 'INVALID' != 'BOUND'
```

**关于第二条红的诚实说明**：它的红来自裁剪（缺席后样本集变化使未裁剪的中心率
跌破 0.9），**不是**来自缺席处理本身——缺席与坏字节两条分支在 BC-DATA-23 落地
时就已正确，轮 17 只是裁定确认了那个读法。该用例因此是把 (3)(4) 语义**钉死**的
覆盖回归，不宜被引用为「(3)(4) 的修复前必失败证明」。

### 17.4 §29.3 (3)：重跑同一零写入 preflight

```
partition                     状态     mode      pairs  样本   centre_hit   iou_median
detect-scout1|68170d80…       BOUND    scouting     50    278   1.0         0.999995
m3-armA|f9c92052…             BOUND    m3            0    682   0.9765395894   —
m3-armB|f9c92052…             BOUND    m3            0    153   0.9215686275   —
rate|4bddb2f2…                BOUND    none          0      0    —             —
rate|78b06c46…                BOUND    none          0      0    —             —
s004-qual|00c8802a…           BOUND    none          0      0    —             —
s004-scout|00c8802a…          BOUND    scouting     50   4836   1.0         0.999995
s004-smoke|00c8802a…          BOUND    none          0      0    —             —
scene-val|f6005eb4…           BOUND    none          0      0    —             —

9/9 BOUND，invalid 0；已绑定帧 23,549；wrote_nothing = true；
runtime/dist-data/ 前后均不存在；runtime/ git 干净
```

**这个 9/9 与 F16 之前的 9/9 不是同一件事，也不是把数调回去的结果。** F16 之前
交叉验证在生产入口**从未执行**（`cross_validation` 恒空、`layout_binding_valid`
硬编码 `True`）；现在它真的跑了，两个 scouting partition 是**凭 centre 1.0 /
IoU 0.999995 通过的**。诊断差异清晰可见：detect-scout1 的中心命中率 `0.78 →
1.0` 完全来自比较域修正，其余参数一字未动。

**仍需报出的敏感度**：`m3-armB` 的中心落框率 `0.9216` 距 `0.9` 阈值只有
`0.0216`，样本仅 153，对样本集变化敏感。该项不受本轮裁剪影响（m3 走点投影）。

### 17.5 套件

```
python3 3.14.6        focused 424，OK（9 skip：需 Pillow 的金标）
.venv-yoloe 3.12.13   focused 424/424 OK 零 skip
.venv-yoloe 全套       959，failures=1 errors=1 skipped=1，仍只有既有两项
                      CSRT/opencv-contrib，新增失败 0
```

### 17.6 给复核角色的复核范围（本批次增量）

范围按 §12.7 的口径运行时解析。建议重点：

1. 裁剪是否**只**发生在选样之后——候选集、`_pair_sort_key` 排序、前 50 对与
   `>= 50` 判定是否与裁剪完全无关。
2. `project_aabb()`、S3 的 `amodal_px`、遮挡/截断状态、m3 中心检查是否确实
   一字未动（BC-DATA-24 (2)）。
3. §17.1 对 `test_dist_data_layout.py` 夹具的修正是否只是把「真值框」改成归档
   语义，有没有顺手弱化任何断言；新网格 60/60 在视口内是否真的成立。
4. §17.3 第二条红的诚实说明是否准确——(3)(4) 的实现确实早于本轮。
5. §17.4 的 9/9 是否确实来自比较域修正而非任何参数回调；detect-scout1
   `0.78 → 1.0` 是否可独立复算。

---

## 18. BC-DATA-25：高基数行集的单一逻辑工件 + 有界流式存储（2026-08-29）

裁定：提案 §33（接受轮 21）。**逻辑 schema 一字未改**——行、字段、顺序、
`referable`/`blocking`/`exposure`、`TARGET_UNBOUNDED`、统计与跳过计数、
四集汇总、门值全部逐字义保留；改的只是物理表示与消费机制。

### 18.1 组合工件层（`tools/dist_data/artifacts.py`）

| 合同款 | 落点 |
|---|---|
| (2) manifest + 有界 gzip-NDJSON shards | `write_composite()`；manifest 就写在既有的 `<artifact>/<attempt>/<artifact>.json`，shards 在同目录 `shards/NNNNN.ndjson.gz`。每 shard 未压缩上限 `64 * 1024 * 1024`，单行超限时独占一 shard |
| (2) gzip 字节幂等 | `_gzip_bytes()` 固定 `mtime=0` / `compresslevel=9`；实测 CPython 在 `mtime=0` 下写出的 OS 字节即 `255`，另加一道防御性改写 |
| (3) manifest 内容 | storage 版本/编解码/上限/gzip 参数、输入 artifact refs（**§19 才真正接上生产 driver**，本节初版仅有形参）、有序 shard 表（零填充序号、相对路径、SHA-256、行数、压缩与未压缩字节、首尾 `frame_id`）、`row_count`、有序行流累积哈希 `stream_sha256`。`ArtifactRef.sha256` 哈希 manifest，manifest 递归哈希全部 shard |
| (5) 有界 | 写侧一次只持有**一个** shard 的字节：`_flush()` 固化后立即落盘并出作用域；读侧 `read_composite_rows()` 逐 shard 解压产出 |
| (6) 以 manifest 为唯一提交点 | shards 先写 private `.staging/`、`fsync`、逐 shard 复核 SHA 与压缩字节，再整体 `rename` 到 `shards/`，manifest 最后经 `os.link` 原子发布（目标已存在即失败）。manifest 不存在时 `attempts()` 天然视为缺席（既有实现即要求该文件存在） |
| (6) 孤立 staging | 无 manifest 却有 `.staging/` → `IncompleteCompositeArtifactError`，**不删除、不重用、不续传**；中断路径显式不做清理 |
| (6) 幂等与 create-once | manifest 已存在时重跑**不写任何文件**：重新计算 manifest 字节与逐 shard SHA 比对，一致则返回同 ref，任一字节不同即 `CreateOnceError` |

### 18.2 S3 / S4 改为有界流

- **S3**：`stage3_frames_catalog()` 内部改成生成器，逐帧 `yield`，**不再累积
  任何 entry**；计数放在可变盒子里，manifest 汇总在流耗尽后求值——为此
  `write_composite` 的 `summary` 允许传零参可调用。
- **S4**：~~`assign_atoms()` 从 `assign_splits` 抽出，供流式与整表两条路**共用
  同一实现**，保证 split 语义逐字相同。~~ **本句在 §18 当时的候选上不成立**：
  复核轮 6 F22 实测反证——`assign_splits` 本体一行未动，`assign_atoms` 是
  **新增的第二份复制实现**，两条路的等价只靠回归夹具维系，不是结构保证。
  该措辞由接受轮 24 的 F22 返工（§20.3）**才真实成立**，此处按 §36.3 保留
  原文并注明历史，不改写成当前时态。新增 `assign_splits_streaming()` 一遍
  扫描既产出有序角色行、又用 `ExposureAccumulator` 累加四集汇总；角色仍
  **只能**由它产出，复核轮 2 F11 的不可绕过性在流式路径同样成立。
  S4 对 entry 流做三遍确定性扫描（族+pHash → 逐 atom 汇总 → 角色行），
  每遍只驻留小值（帧 id、pHash、集合），从不驻留 entry 或全角色集。
- **行序不需要全表排序，但被断言**：实测 S1 记录按路径升序、`entry["objects"]`
  按 `object_id` 升序，故 encounter order 已等于 `(frame_id, object_id)`。
  `assign_splits_streaming` 对此**逐行断言**，上游一旦改序即 fail-closed，
  绝不静默产出乱序工件（本轮开发中该断言真的拦下过一个乱序夹具）。
- **S5/S6/S7/S8** 全部改走 `CatalogStream`：可重复迭代的类型化流，每次
  `__iter__` 重新校验分片；`__len__` 取自 manifest 的 `frame_count`，
  ~~**不支持下标**——正是为了让任何试图物化全集的写法直接失败。~~
  **破折号后半句不成立**：复核轮 6 F21 实测反证——缺少下标只挡住按位取数，
  挡不住 `list()` 或逐行 `append` 物化**派生**全集，而 S5/S6/S7/S8 当时正是
  这样做的。接受轮 24 的返工（§20.2）**只使 S5 一支**有界成立；S6/S7/S8 仍是
  `DEFERRED_BOUNDEDNESS_DEBT_BEFORE_STAGE_AUTHORIZATION`，在各自阶段的执行
  授权前阻断。此处按接受轮 25 §37.2 保留原文并标注历史，不改写成当前时态，
  也不得据此把 BC-DATA-25 (5) 款首的「生产消费全程有界」写成全部闭合。

### 18.3 §33.3 点名的五条回归（`tests/test_dist_data_composite.py`）

| 用例 | 判据 |
|---|---|
| `test_streamed_frames_catalog_is_logically_identical_and_bounded_memory` | 跨多 shard 夹具下读回行序列与整表逐字段一致；`weakref` 追踪证明 >90% 已消费 entry 被回收——生产路径若 `list()` 化全集必失败 |
| `test_composite_publish_is_atomic_and_orphan_staging_fails_closed` | 分片中断后无 manifest、`attempts()` 为空、staging 原样保留；再次写入 `IncompleteCompositeArtifactError` 且现场文件不变 |
| `test_streamed_splits_preserves_all_sample_roles_and_exposure_counts` | 角色行与整表 `assign_splits` **完全相同**；`exposure_matrix` 逐字段对等；`sample_count == len(roles)`；七个非角色键逐一对等；行序升序 |
| `test_streamed_consumers_match_legacy_small_fixture_s4_to_s8` | S3 行流与「修前整表」构造逐字段一致；S4–S7 门与终态一致（四条 floor 全不达标）；S8 关门仍拒绝物化 |
| `test_composite_tamper_and_create_once_are_rejected` | 改字节／丢 shard／改顺序／改行数四种篡改全部 fail-closed，每次恢复后重新可读；同输入幂等、异字节 `CreateOnceError` |

另加 `test_production_shard_cap_is_the_frozen_64_mib`：上面几条会临时缩小
上限做多分片夹具，故先把生产常量本身钉死，防止夹具值漏进生产。

### 18.4 套件与边界

```
python3 3.14.6        focused 430，OK（9 skip：需 Pillow 的金标）
.venv-yoloe 3.12.13   focused 430/430 OK 零 skip
无归档副本            双解释器均 430 OK (skipped=46)
.venv-yoloe 全套       965，failures=1 errors=1 skipped=1，仍只有既有两项
                      CSRT/opencv-contrib，新增失败 0（926 → 965）
```

**S0–S2 三件正式工件一字节未动**（逐件复核大小与 SHA-256 前缀，与执行当时
相同）；正式根下无 `shards/`、无 `.staging/`；所有新测试只写临时根。
`test_dist_data_driver.py` 里那条「正式输出根不得被写」的断言从「根不存在」
改成「本次测试进程未增删改它一个字节」——因为轮 20 的限域执行之后该根
**合法存在**，旧写法已不成立；判据由模块导入时的逐路径 SHA 快照与结束时
比对，比原来更强。

### 18.5 未做的事与推算

**没有在真实归档上跑 S3。** 轮 21 §33.3 明写「本轮不授权正式续跑」，且禁止
以「S3 尚无工件」为由自行续跑，因此本批只有代码与合成/临时夹具证据。

据既有实测量推算（**算术，不是执行结果**）：每 entry 序列化 238 KiB，
23,549 帧 ≈ 5.4 GiB 未压缩，按 64 MiB 上限约 **85 个 shard**；写侧常驻内存
≈ 一个 shard 的行缓冲（≤ 64 MiB）加当前 entry，与帧数无关。真实数字须待
获授权续跑后实测，不得引用本推算代替。

### 18.6 给复核角色的复核范围（本批次增量）

范围按 §12.7 的口径运行时解析。建议重点：

1. **逻辑 schema 真的没变**：请拿修前整表算法作基准，逐字段比对 S3 行与 S4
   角色行，而不是只读流式实现自证。
2. **有界性是否真的成立**：`write_composite` 是否在任何路径上都只持有一个
   shard（含 manifest 已存在的幂等复核路径）；S4 三遍扫描是否只驻留小值。
3. **不可绕过性**：角色是否仍只能经 `assign_splits_streaming` 产出；
   `CatalogStream` 不支持下标是否足以挡住物化全集的写法。
4. **提交点语义**：`os.link` 发布在目标已存在时是否确实失败；中断后
   staging 是否绝不被自动清理或续传。
5. **行序断言**：`(frame_id, object_id)` 升序依赖上游两处排序，请确认该断言
   覆盖了两处中任一被改动的情形。
6. §18.5 的推算未经执行验证，请按未验证项对待。

---

## 19. 接受轮 22 SP22-1 / SP22-2：组合工件边界返工（2026-08-31）

裁定：提案 §34（接受轮 22，`STOP_POINT_NOT_CONFIRMED /
COMPOSITE_BOUNDARY_REWORK_REQUIRED`）。四项停点条件中前三项满足，**第 4 项
不满足**——§18 的证据与状态板把两件事写成已闭合，生产路径与测试却没做到。
两条都由 Acceptance 在真实写盘路径上实测反证，**结论成立，本节是返工**。

### 19.1 SP22-1：manifest 的输入 lineage 从来没接上

`write_composite()` 有 `inputs` 形参，但生产的 `stage3_frames_catalog()` 与
`stage4_splits()` 两处调用都没传，信封实际写出 `"inputs": []`。§18.1 表格里
「输入 refs」的说法因此**不成立**，该行已在本轮改正；原有六条组合工件回归
也没有一条检查生产 driver 的 lineage。

修复：取数点改为交出 ref——新增 `PipelineDriver._read_ref()`（`_read()` 成为
它的薄封装），`CatalogStream` 暴露 `.reference`。S3 的 manifest 引用**本次
实际读取**的 `inventory` 与 `layout` ref，S4 引用本次实际读取的
`frames_catalog` ref；一律取自同一次生产读取，不按路径事后伪造。

### 19.2 SP22-2：manifest 发布失败后的 final-shard 残留没有 fail-closed

原实现先把 `.staging/` rename 成 `shards/`，再发布 manifest。若发布失败，
现场是「无 manifest、无 `.staging/`、有 `shards/`」——而下一次写入只检查
`.staging/`，于是照常新建 staging，最后以 `OSError: Directory not empty`
失败，**既不是**合同要求的 `IncompleteCompositeArtifactError`，**又改动了
现场**。

修复：manifest 缺席时把 `shards/` 与 `.staging/` **两种残留同等看待**，在写
任何新字节之前抛 `IncompleteCompositeArtifactError`；不删除、不重用、不续传、
不新增残留。

### 19.3 具名回归与修复前红

- `test_production_manifests_record_the_actual_input_artifact_refs`：逐字段比对
  两份 manifest 的 `inputs` 与上游 `ArtifactRef.as_reference()`，并另验 S4
  lineage 的 sha 确实等于盘上那份 frames_catalog manifest 的哈希（防占位值）。
- `test_manifest_publish_failure_leaves_shards_and_fails_closed`：mock 掉
  `_atomic_publish` 制造「staging 已 rename、manifest 未 commit」的故障窗口，
  断言首次现场（`shards/` 在、manifest 与 `.staging/` 不在、`attempts()` 为空），
  再次调用 `IncompleteCompositeArtifactError`，且 attempt 目录**逐路径 SHA-256
  快照前后不变**、无新增 staging。

只回退 `tools/dist_data/` 的未提交增量（恢复后工作树 diff 逐字节相等）：

```
FAIL  ...record_the_actual_input_artifact_refs
      AssertionError: Lists differ: [] != [{'artifact': 'inventory', …}]
ERROR ...publish_failure_leaves_shards_and_fails_closed
      OSError: [Errno 66] Directory not empty: …/.staging -> …/shards
```

两条红与接受轮 22 描述的形态逐字对应。

### 19.4 套件与边界

```
python3 3.14.6        focused 432，OK（9 skip：需 Pillow 的金标）
.venv-yoloe 3.12.13   focused 432/432 OK 零 skip
.venv-yoloe 全套       967，failures=1 errors=1 skipped=1，仍只有既有两项
                      CSRT/opencv-contrib，新增失败 0
```

S0–S2 三件正式工件仍一字节未动（SHA-256 复核）；正式根下无 `shards/`、
无 `.staging/`；本轮未运行正式 S3–S5，未写任何 runtime 工件。§18 的其余
回归与结论保留，只有 §18.1 那一行被反证的措辞已改正。

### 19.5 给复核角色的复核范围（本批次增量）

1. lineage 是否真的来自同一次生产读取——请确认没有任何按路径重建 ref 的
   旁路，且 S4 用的是它实际迭代的那份 manifest 的 ref。
2. 残留判定是否**在写任何字节之前**发生，且两种残留形态都覆盖；失败后
   现场是否确实零改动。
3. §18.1 的措辞改正是否已覆盖全部被反证的表述（~~本轮只发现这一处~~ ——
   **该唯一性表述已按接受轮 24 §36.3 撤回**：复核轮 6 F22 又找到第二处，即
   §18.2 的「共用同一实现」，形态与 SP22-1 相同（证据声称的机制在生产中不
   存在）。撤回的是「只有一处」的判断，不是 §18.1 那次改正本身）。

---

## 20. 复核轮 6 返工：F20 / F21 / F22（接受轮 24，2026-09-01）

裁定：提案 §36（接受轮 24，`REVIEW_R6_FINDINGS_ACCEPTED / F20_F21_F22_ROUTED /
IMPLEMENTATION_REWORK_REQUIRED`）。三条分级（F20 `CLASS_1`、F21/F22
`CLASS_2`）接受角色逐条同意，无升降格；SP22-1/SP22-2 保持闭合，复核轮 6 的
七条观察项**不在本轮范围**，一条也没有顺手改。

本轮只改 `tools/dist_data/{run_pipeline,build_catalog,make_splits}.py`、新增
`tests/test_dist_data_round24.py`、本证据文件与状态板；仍属轮 21 放行的
code/tests/temp-fixture 范围，**不是正式数据执行授权**。

### 20.1 F20（`CLASS_1`）：S7 流式化切断的 `split` 侧信道

修前 `catalog["entries"]` 是同一批**可变** dict，S7 先逐 entry 打上
`entry["split"]`，`build_g0_report()` 读到的就是带键的同批对象。流式化后
`read_composite_rows` 每次迭代都 `json.loads` 出**新对象**，那次打键对
`build_g0_report` 内的 5+ 遍重迭代一概不可见：`compute_f2` 的
`split not in SPLITS → continue` 使 F2 恒 0、`station_keys` 恒空，
`frames_by_split` 把全部帧计进 `"None"`。

修复不是「再打一次键」，而是把 split 变成**流本身的属性**：新增
`run_pipeline.SplitDecoratedStream`，包住 `CatalogStream`，**每一次**
`__iter__` 都用 S4 派生的同一份 `split_of_frame` 逐条装饰后产出；
`__len__` 透传 manifest 的 `frame_count`（`exclusion_histogram` 需要）。
装饰在行流上逐条完成，**不物化 `frames_catalog`**，驻留仍是一条 entry，
一次性 generator 那种「只够消费一遍」的做法不被采用。`stage7_gate` 里那句
已成死赋值的 `entry["split"] = …` 随之删除；`split_of_frame` 全 S7 只此
一份，与 `freeze_mother_candidates` 用的是同一个映射。冻结 F1/F3/F4、F2
阈值与 g0_report schema **一字未改**。

同夹具下修前/修后 g0_report 的**全部**差异（逐键 diff，其余键逐字节相同）：

```
floors.F2.global                          0  -> 4
floors.F2.per_split.dev                   0  -> 4
floors.F2.per_split.test                  0  -> 4
floors.F2.station_keys                   []  -> ["0:0:0:0","1:0:0:0","3:0:0:0","4:0:0:0"]
station_clustering.keys                  []  -> ["0:0:0:0","1:0:0:0","3:0:0:0","4:0:0:0"]
stratified_denominators.frames_by_split  {"None": 8} -> {"dev": 4, "test": 4}
mother_candidates 工件                    逐字节相同
```

与复核轮 6 副本内探针的 `0 vs 4` / `{"None": 8} vs {test: 4, dev: 4}` 逐字
对应。**F20 闭合。**

### 20.2 F21（`CLASS_2`）：S5 逐对象有界；S6–S8 的债**没有**清零

按 §36.2 选定的 (a) 支路。新增 `build_catalog.BoundedObservationSelector`：
逐 object 只保留 `(camera_depth_m, frame_id)` 升序下最小的
`contract.COLOR_SAMPLE_FRAME_COUNT` 条，驻留上界 `O(对象数 × K)`，与帧数
解耦。`build_field_catalog` 的入参由 `Sequence` 改为 `Iterable` 并只迭代
一次，逐条收进选择器；生产 driver 的 `stage5_field_catalog` 不再构造
observation list，而是对可重复迭代的 `CatalogStream` 做两遍**各自有界**的
扫描：第 1 遍只收对象域（≤ 对象数个字符串，**一条 observation 也不构造**），
第 2 遍把观测**以生成器**交给 S5。两遍共用唯一的过滤定义
`_color_observation_rows`，对象域与观测流不可能各用一套判据。

**K、排序/平局语义、对象域、像素 crop、颜色估计、字段与最终 payload 字节
全部不变**：`insort` 与 `sorted` 同为稳定插入，排序键在同一对象内唯一
（一帧一对象至多一条观测），因此候选集与顺序与整表 `sorted(...)[:K]` 逐条
相同；除具名回归外另在 300 组随机输入（含平局、含 `n < K` 与 `n ≫ K`）上
逐对象比对选择结果，全等。

**S6/S7/S8 的同型线性物化本轮既未修复也未预授权执行**：
`audit_strata`（S6 深度样本）、`stage7_gate`（`candidates`）、
`stage8_mother_set`（`amodal_box_of`）仍是全量物化，按 §36.2 登记为
`DEFERRED_BOUNDEDNESS_DEBT_BEFORE_STAGE_AUTHORIZATION`——任何 S6–S8 执行
授权草案都必须先回接受角色给出有界方案或量化例外裁定。**本节只闭合 S5
一支，不得读成 BC-DATA-25 (5) 款首总则的债务清零。**

### 20.3 F22（`CLASS_2`）：代码收敛，并纠正历史文证

按 §36.3 选定的 (a) 支路。`assign_splits()` 现在调用 `assign_atoms(atoms)`
作为 atom 指派、连带规则与泄漏断言的**唯一**实现，平行复制的同构逻辑
（floor 过滤 → `choose_test_atoms` → D3 → `split_dev` → 连带规则 → 泄漏
断言）整段删除；整表路径只在共享 base 上装配不可绕过的 sample roles，流式
路径继续在同一 base 上产出角色行与汇总。split 语义与所有输出字段不变：
`dropped_frames`/`d3_holdout_empty` 改由同一 base 派生（`base["dropped"]`、
`not assignment[SPLIT_D3]`，与原 `sorted(set(dropped))`、`d3_atom is None`
同值），另在 200 组随机 atom/entry 集（含抛异常的分支）上与修前实现逐字段
比对输出，全等。

文证纠正（§36.3 要求，**不得静默改成当前时态**）：§18.2 的「已抽出共用」
保留原文并标注其在旧候选上被复核轮 6 F22 反证、由本返工才真实成立；
§19.5 (3) 的「本轮只发现这一处」同步**撤回**。**F20/F22 闭合，F21 的 S5
分支闭合。**

### 20.4 三条具名回归与修复前红（`tests/test_dist_data_round24.py`）

| 用例 | 判据 |
|---|---|
| `test_streamed_g0_report_preserves_nonzero_f2_and_frames_by_split` | 走生产 `stage7_gate()`；夹具在修前整表语义下 F2 非零（`global=4`，`station_keys` 非空）；逐字段比对**正式写出**的 g0_report `floors.F2`（含 `station_keys`）、`station_clustering.keys` 与 `stratified_denominators.frames_by_split`，基准是同批 entry 按修前语义打键后经同一 `compute_f2` / `stratified_denominators` 求得 |
| `test_stage5_field_catalog_is_logically_identical_and_bounded_per_object` | 每对象 16 条跨帧观测（K=5，4 条一个深度档，平局由 frame_id 决出，故「按帧序取前 K」必然产出不同候选）；完整 payload 与**逐字转写的修前整表算法**逐字段相等；生产路径上以 `weakref` 实测同时存活的 observation ≤ `object_count × K + 1`（+1 = 正在传递中的那条） |
| `test_legacy_and_streaming_split_paths_share_assign_atoms` | 结构回归：整表 `assign_splits` 与流式 `assign_splits_streaming` 各调用共享 `assign_atoms()` 恰一次，且两者的 `frames`/`leakage_assertions` 与那一次共享计算的结果**对象同一**（不是同构复制）；七个非角色键逐一对等 |

修复回退（只回退 `tools/dist_data/` 的未提交增量，恢复后三个文件 SHA-256
逐一相等）后三条各以绑定症状失败：

```
FAIL  ...streamed_g0_report_preserves_nonzero_f2_and_frames_by_split
      AssertionError: 0 != 4 : floors.F2.global
FAIL  ...stage5_field_catalog_is_logically_identical_and_bounded_per_object
      AssertionError: 64 not less than or equal to 21 : 生产路径同时驻留 64 条
      observation，超过 object_count × K + 1 = 21；S5 疑似仍在物化全集
FAIL  ...legacy_and_streaming_split_paths_share_assign_atoms
      AssertionError: 1 != 2 : 整表与流式两条生产路径各须调用一次共享
      assign_atoms()；实测 1 次，说明仍存在平行复制实现
```

F21 那条在修前**只有有界性断言失败**，逻辑等价断言照常通过——这正是本轮的
承诺：改的是驻留，不是输出。

### 20.5 套件与边界

```
python3 3.14.6        focused 435，OK（9 skip：需 Pillow 的金标）
.venv-yoloe 3.12.13   focused 435/435 OK 零 skip
.venv-yoloe 全套       970，failures=1 errors=1 skipped=1，仍只有既有两项
                      CSRT/opencv-contrib，新增失败 0（967 → 970）
```

`git diff --check` 干净。正式根仍**恰三件**工件 `contract`/`inventory`/
`layout`@attempt-1，字节 5,014 / 28,574,739 / 2,220,725 与轮 20 执行收据
逐一相等，mtime 停在 2026-08-28；全根**零** `shards/`、零 `.staging/`。
**本轮未运行正式 S3–S5**，未写任何 runtime 工件；正式 S0/S1/S2 字节不变。
S6–S9/G0/D0、audit、supersession、依赖/模型/API/GPU/Play/ID 与后续训练
继续未授权。探针（g0_report 前后逐键 diff、选择器随机对照、`assign_splits`
随机对照）只存在于 scratchpad 与临时根，未进仓库。

### 20.6 给复核角色的复核范围（本批次增量）

范围按 §12.7 的口径运行时解析。建议重点：

1. **F20 是否真的在「每一遍」都成立**：`SplitDecoratedStream` 是否对
   `build_g0_report` 内每一处 entry 迭代（`station_of_frame`、`compute_f2`、
   分母表 4 处、排除直方图、共视分布）都生效，且 `__len__` 透传后
   `exclusion_histogram` 的 `frame_total` 未变。
2. **装饰是否引入新的物化或副作用**：逐条打键改的是 `read_composite_rows`
   当次产出的新 dict，请确认没有任何跨迭代共享或缓存。
3. **F21 的等价性**：请拿修前整表 `sorted(...)[:K]` 作基准独立验证选择器，
   特别是平局（同 `camera_depth_m`）与 `n < K` 两种边界。
4. **F21 的有界性判据是否可证伪**：`weakref` 计数是否真的落在生产路径上，
   `object_count × K + 1` 的 `+1` 是否只对应「正在传递中的那条」。
5. **两遍扫描的代价**：S5 现在完整解压两遍 shard（第 1 遍只为对象域）。
   正确性无碍，但请判断是否值得在续跑授权前合并遍数。
6. **F22 是否只剩一份实现**：请确认 `make_splits` 内已无第二份 atom 指派
   逻辑，且结构回归的对象同一性断言不会被将来的「防御性拷贝」误伤。
7. **S6–S8 的债**：§20.2 只闭合 S5 一支，请确认证据与状态板没有任何一处
   把它写成 BC-DATA-25 全债务清零。

---

## 21. 接受轮 25：F21 失效有界性文字的两处定点更正（2026-09-01）

裁定：提案 §37（`STOP_POINT_NOT_CONFIRMED /
F21_STALE_BOUNDEDNESS_CLAIM_REWORK_REQUIRED / REVIEW_ROUND_7_NOT_OPENED`）。
§4.3.1 条件 1–3 满足（接受角色独立复现双解释器 focused 各 435、隔离副本内
`git revert -n` 复现三条具名回归的 `0 != 4` / `64 not <= 21` / `1 != 2`、恢复后
3/3 转绿且生产字节与主树相同）；**条件 4 因两处被复核轮 6 F21 反证的绝对断言
仍在而失败**——F22 的文证在轮 24 改了，同源的 F21 那句没连带清理，这是实现侧
的漏项。

本轮**只改文字**：零生产行为变化、零测试变化、零正式工件变化、零授权边界
变化，三条 round-24 回归一条未动。

### 21.1 两处更正（§37.2 (1)(2)）

- **`tools/dist_data/run_pipeline.py`，`CatalogStream` docstring**：原句
  「本类**不**支持下标，正是为了让任何试图物化全集的写法直接失败」改为精确
  事实——本类只强制消费者经可重复、逐 shard 校验的迭代接口取数；缺少下标
  **不阻止** `list()` 或逐行 `append` 物化派生全集，**有界性必须由每个消费点
  分别证明**。并写明 S5 已由 `BoundedObservationSelector` 闭合、S6/S7/S8 仍是
  `DEFERRED_BOUNDEDNESS_DEBT_BEFORE_STAGE_AUTHORIZATION`，在各自阶段的执行
  授权前必须先回接受角色。
- **本文件 §18.2 末条**：旧句保留（删除线）并标注破折号后半句被复核轮 6 F21
  实测反证，注明轮 24 返工**只使 S5 一支**成立、S6–S8 债务仍在，且不得据此把
  BC-DATA-25 (5) 款首的「生产消费全程有界」写成全部闭合。未改成当前时态。

### 21.2 未做、退回接受角色的一处（本轮按字面收窄）

§18.6 (3)「`CatalogStream` 不支持下标是否足以挡住物化全集的写法」是**同源
表述**：它以问句形式提给复核角色，而复核轮 6 F21 已经答「挡不住」。§37.2 的
字面清单只点名两处并要求不得顺手扩张，故本轮**未动该行**，是否同批修正退回
接受角色裁定。此处如实记录，不当作已闭合。

### 21.3 复跑与边界

```
python3 3.14.6        focused 435，OK（9 skip）
.venv-yoloe 3.12.13   focused 435/435 OK 零 skip
.venv-yoloe 全套       970，failures=1 errors=1 skipped=1，仍只有既有两项
                      CSRT/opencv-contrib，新增失败 0
round-24 三条具名回归  3/3 通过
```

`git diff --check` 干净。正式根仍恰三件工件 `contract`/`inventory`/`layout`
@attempt-1，字节 5,014 / 28,574,739 / 2,220,725 未动，零 `shards/`、零
`.staging/`；未运行正式 S3–S5。S6–S9/G0/D0、audit、supersession、依赖/模型/
API/GPU/Play/ID 与后续训练继续未授权。

### 21.4 给接受角色的定点复看范围（`NOT_MECHANIZABLE`）

1. `CatalogStream` docstring 是否已无绝对断言，且「有界性逐消费点证明」与
   「S5 闭合 / S6–S8 仍阻断」两句都在。
2. §18.2 的旧句是否保留可见并标注被反证，是否未被改成当前时态、未把
   BC-DATA-25 (5) 款首写成全部闭合。
3. §21.2 退回的第三处（§18.6 (3)）是否需要同批修正——本轮按字面未动。

---

## 22. 接受轮 28：正式 S3→S4→S5 continuation 执行（2026-09-01）

授权：提案 §40（接受轮 28，`FORMAL_S3_S5_CONTINUATION_AUTHORIZED /
PREAUDIT_UPPER_BOUND_DIAGNOSTIC_ONLY`），用户逐字「授权，继续」见
`docs/authorizations.md` 2026-09-01 条目。本节只记录执行收据、核验与观察；
诊断交付仍是唯一的 `docs/evidence/P1-VLM-DATA-001-S0-S5-pre-audit-upper-bound.md`
（**审计前上界、非门 verdict**）。按 COORD-007 R7，本节不手写候选 SHA、attempt 名
与工件 SHA；它们在执行时由 git、复核文件机读行与 `ArtifactStore` 运行时派生，
收据 JSON 留在实现会话 scratchpad，不进仓库。

### 22.0 本批做了什么、没做什么

- **做了**：§40.1 三项硬门（运行时派生通过候选并断言 HEAD 祖先、候选后
  PLAY_GOVERNING diff 为空、工作树干净、钉死 `.venv-yoloe` 3.12.13；正式根只读
  核验；不走 `--run`）；按 §40.2 (1) 用**三个独立进程**依次调用已复核生产入口
  `PipelineDriver.stage3_frames_catalog()` → `stage4_splits()` →
  `stage5_field_catalog()`，attempt 由 `ArtifactStore.attempts()` 运行时枚举、
  取 S0–S2 共有的唯一 attempt；每阶段完成后立即以另一进程做只读核验；S3–S5
  全部成功后按 §40.3 只读、在内存中计算 `U_F1`…`U_F4`。
- **没做**：未改任何生产代码/测试/合同/依赖（本批 `git status` 只有文档）；未重写
  S0–S2（三件字节 SHA 在每个阶段前后逐一相等）；未 retry、清理、删除、续传或
  supersede；未写 audit、S6/S7/S8/S9；未调 `stage7_gate()` / `build_g0_report()`；
  未加任何 instrumentation code——wall time 与 peak RSS 全部来自进程外
  `/usr/bin/time -l`（macOS `maximum resident set size`），进程内只读
  `resource.getrusage`；零 Unity/Play/ID/API/GPU/下载。
- 执行脚本只是 scratchpad 里的胶水（预检、单阶段调用、核验、上界计算），每个都
  只调用 `tools.dist_data` 的既有函数，不复制阶段算法；它们不属于 PLAY_GOVERNING，
  也未提交。

### 22.1 执行前硬门（§40.1）实测：32 项全过

| 门 | 实测 |
|---|---|
| 候选 | 复核文件最近一行 `passed_candidate` 运行时解析；`git merge-base --is-ancestor` 成立；候选→HEAD 在 `controller/`、`Assets/`、`tools/`、`tests/`、`config/`、`ProjectSettings/`、`Packages/packages-lock.json` 上 diff **为空**（区间内 5 个改动路径全是 docs） |
| 工作树 / 解释器 | `git status --porcelain` 为空；`sys.executable` 位于 `.venv-yoloe`，Python 3.12.13 |
| 正式根 | `attempts()` 对 12 类工件枚举：S0/S1/S2 各恰一个且同名 attempt，S3–S9 全空；全根恰 3 个文件，无 `.staging/`、无无 manifest 的 `shards/`、无 `*.publishing` |
| S0–S2 完整性 | 三件可解析、结尾换行、信封 `artifact`/`attempt`/`stage`/`work_id`/`schema_version` 正确、`supersedes` 空；`store.read(..., requesting_stage=3)` 通过；字节 **5,014 / 28,574,739 / 2,220,725** 与轮 20 收据相等 |
| lineage | layout 信封 `payload.inputs` 恰引用 inventory 且 SHA 与磁盘实测相等；layout `base_geometry_sha256` = contract 的 `base_geometry.sha256` = 几何文件当前实测 SHA；contract `floors` 与 `contract.FLOORS` 相等 |
| 收据对账 | records **29,923**、`match_audit` zero/multi 均 **0**、INCLUDED 图像 **23,706**、9 partition 全 `BOUND`、9 条 `cross_validation`、BOUND 帧合计 **23,549**、每 partition 779 实例；S1 里 **5,769** 条 INCLUDED 真值记录经 `immutable_input_check` 重算 SHA 全部未变 |

由此派生 S3 期望：`frame_count` 23,549、`skipped_unbound_frames` 157
（= 23,706 − 23,549）、`skipped_invalid_frames` 0。

### 22.2 三阶段收据（§40.2 (1)(4)）

| 阶段 | 阶段函数返回 | 阶段 wall（进程内 / 进程 real） | peak RSS（进程外） | 新增文件 / 字节 |
|---|---|---|---|---|
| S3 `frames_catalog` | frames **23,549**、skipped_unbound **157**、skipped_invalid **0** | 226.129 s / 226.64 s | 420,282,368 B（≈ 401 MiB） | 84（manifest 35,034 B + 83 shard）/ 932,583,106 B |
| S4 `splits` | **无 terminal**；atoms **3**；`frame_counts` train **0** / dev **7,060** / test **3,045** / d3 **0** | 297.518 s / 298.96 s | 3,129,065,472 B（≈ 2.91 GiB） | 4（manifest **515,074,557 B** + 3 shard）/ 518,279,288 B |
| S5 `field_catalog` | objects **106**、dual_verified **9** | 64.276 s / 66.03 s | 674,250,752 B（≈ 643 MiB） | 1 / 94,325 B |

每个阶段进程在调用前断言：S0–S2 SHA 与预检相等、前置阶段工件在、本阶段及
之后工件缺席、零残留；调用后断言：全部既有文件逐路径 SHA 未变、零残留、
本阶段 manifest 已发布且 `attempts()` 恰返回同一 attempt。三个阶段的
`post_problems` 均为空。S3 shard 表：83 个，行数合计 23,549，未压缩
5,515,458,884 B、压缩 932,548,072 B，每 shard 96–300 行。S4 角色流 3 个 shard，
1,032,602 行，未压缩 183,337,279 B、压缩 3,204,731 B；dropped 13,444 帧 +
指派 10,105 帧 = 23,549。

### 22.3 每阶段核验（§40.2 (2)）

| 阶段 | 项数 | 内容 | 核验 wall / peak RSS |
|---|---|---|---|
| S3 | 13/13 | S0–S2 未变；manifest SHA = 阶段返回值；信封身份；`inputs` 恰为本次读取的 inventory、layout 两个 ref 且 SHA 与磁盘相等；storage 块 = 冻结常量（64 MiB、gzip level 9、mtime 0、OS 255）；shard 表序号/路径/压缩字节/gzip 头/跨 shard 帧序一致、目录无多余文件；**经生产 `read_composite_rows` 全量迭代**（逐 shard SHA、行数、累积哈希）：23,549 行 = `row_count` = `frame_count`，帧 id 严格升序，对象/referable/blocking 逐帧升序；计数 = 预检期望；零 `.staging/` | 34.4 s / ≈ 627 MiB |
| S4 | 13/13 | S0–S3 未变；信封；`inputs` 恰为本次读取的 S3 manifest ref；storage 块；shard 表；全量迭代 1,032,602 行，`(frame_id, object_id)` 严格升序，role/split 在闭集内；行数 = `row_count` = `exposure_matrix.sample_count`；`frame_counts` = 各 split 帧表长度；零 `.staging/` | 3.65 s / ≈ 3.61 GiB（解析 491 MB manifest） |
| S5 | 11/11 | S0–S4 manifest 未变；`store.read` 通过且 SHA = 阶段返回值；信封；`stage` = 5；对象数/双验证数 = 阶段返回值 | < 1 s / 27 MiB |

**S5 信封 `inputs` 为空（如实披露）**：生产 `stage5_field_catalog` 经普通
`store.write` 落盘、未传 `inputs`，SP22-1 只接上了 S3/S4 的组合工件 lineage。
本批未改代码；S5 的输入身份只能由同一进程实际读取的 S3 manifest 与 layout 的
运行时 SHA 对账。是否补 lineage 由接受角色裁定。

### 22.4 S3 行流实测摘要（核验遍统计，只读）

| 量 | 实测 |
|---|---|
| 帧 | 23,549（每帧登记对象 779 个的帧 6,106、782 个的帧 17,443） |
| `target_unbounded` 帧 | **16,472**（70.0%） |
| `pre_split_floor_eligible` 帧 | **4,390** |
| referable 对象-帧 | **27,870**（每帧最多 5；`co_visible_count` 0/1/2/3/4/5 = 5,775 / 9,748 / 6,689 / 681 / 579 / 77） |
| blocking 对象-帧 | 102,231（每帧最多 17） |
| 对象状态合计 | OK 213,182 · NOT_IN_VIEW 17,399,521 · TOO_SMALL 155,304 · TRUNCATED 153,262 · EXCLUDED_OCCLUDED 423,402 · PHANTOM 52,329 |
| exposure 合计 | referent 27,870 · distractor 67,985 · absent 2,334,923 · occluder_only 15,966,222 |
| 站位簇键 | 54 个不同键，`key` 为 null 的帧 0 |
| 按用途类 | CALIBRATION 286 · PROTOCOL_INVALID 8,126 · SMOKE 3,762 · VALID_FORMAL 3,722 · VALID_PARENT_HOLD 4,224 · VALID_SCOUTING_CLOSED 3,173 · VOID_TRIAL_HOLD 256 |
| 按布局类 / 族 | default 7,700 · scene-004 15,849；detect-scout1 768 · m3-armA 896 · m3-armB 640 · rate 5,140 · s004-qual 7,952 · s004-scout 4,836 · s004-smoke 3,061 · scene-val 256 |
| `layout_binding_valid` 假 / `sidecar_complete` 假 | 0 / 0 |

### 22.5 审计前上界（§40.3；只读、内存；结果见诊断报告 §1–§4）

S3–S5 全部成功后，用一个独立进程按报告 §2 的链路复用既有纯函数计算
`U_F1`…`U_F4`：`apply_audit_downgrades(field_catalog, [])`（A1 零降级）、
`SplitDecoratedStream` 装饰的 S3 行流、`frame_world` + `prospective_mother_eligible`
逐 referable 对象求候选、`freeze_mother_candidates`、`compute_f1..f4`、
`stratified_denominators`。`passed` 布尔量丢弃，`build_g0_report()` /
`stage7_gate()` 未调用，未写任何工件；计算前后正式根 92 个文件逐路径 SHA 相同。
四值状态一律 `NOT_EVALUATED_PRE_AUDIT`：`U_F1` 9/101（5 类）、`U_F2` 全局 46 /
test 22、`U_F3` train∪dev 25 / test 20 / 留出 9、`U_F4` train∪dev 4 / test 7；
冻结候选外延 5,398 条（7 个对象、3,560 帧）。F2 在轻量投影与装饰行流上各算一遍
逐字段相等。wall 100.9 s，peak RSS 2,957,262,848 B（由解析 S4 manifest 主导）。

### 22.6 性能观察（§40.2 (4)，只披露、不改）

1. **S5 双遍解压**：83 shard × 2 遍 = wall 64.3 s（约 30 s/遍），peak RSS ≈ 643 MiB，
   与逐对象 K 有界驻留相容。
2. **S4 peak RSS ≈ 2.91 GiB、manifest 515,074,557 B**：`atoms.near_duplicate_pairs`
   占 512,888,211 B（2,663,282 对跨族近重复帧对）；`merge_atoms` 对 C(23,549, 2) ≈
   2.77×10⁸ 对做 Hamming 比较是 S4 wall time 的主体，并把全部合格对写入 manifest。
   之后每个解析 S4 manifest 的消费者都付出 2.5–3.6 GiB 驻留（S4 核验 3,875,700,736 B、
   上界进程 2,957,262,848 B）。这是已复核代码的既有行为，未修改；它不在复核轮 6 F21
   点名的 S6–S8 帧线性物化清单里，属于新的观察，交接受角色裁定。
3. **S3 有界如设计**：写出 5.5 GB 未压缩行流 peak RSS ≈ 401 MiB。

### 22.7 观察与退回接受角色的事项（实现角色不自行裁定）

1. **F1 结构上限 16**：S5 域内 class 可验证车辆 16 个（双验证 9），其余 85 个目录
   车辆从未在任何 BOUND 帧取得 `OK` 状态——审计无法改变该上限。
2. `target_unbounded` 帧 16,472 / 23,549（70.0%）压低 floor-eligible 帧（4,390）与
   候选外延（5,398 条、7 个对象、全部 attribute 程序）。
3. S4 train split 为空：3 个 atom 中 test 取 2、无 D3 可选、剩余唯一 atom 按
   `split_dev` 整体落入 dev——冻结规则的机械结果。
4. S5 信封 `inputs` 为空（§22.3）；S4 manifest 尺度（§22.6 第 2 条）。
5. 报告各负差额只是「乐观上界相对 floor 的诊断差额」，未签发任何 G0 verdict；下一步
   （人工审计、采集补数或其他处置）由用户与接受角色决定。

### 22.8 边界自查与返回

- 本批 `git status` 只有三份文档：诊断报告、本文件、状态板；`tools/`、`tests/`、
  `controller/`、`Assets/`、`config/`、`ProjectSettings/`、`Packages/packages-lock.json`
  零改动，故按 §40.3 **不开新 Review 轮**，先回 Acceptance 做执行归因。
- 正式根：六类工件各恰一个 attempt；`audit`…`stop_point` 均不存在；零 `.staging/`、
  零 `*.publishing`、无孤立 `shards/`。S0–S2 字节与轮 20 收据相等。
- 未授权边界一项未越：S6/A1–A3、S7/G0、S8/D0、S9、audit、retry/supersession、
  C1/D1–D3、依赖/模型/API/GPU、Unity/Play、任何 ID、场景/车辆修改、后续训练。
- `docs/implementation-status.md` 未改（里程碑证据的归因文字留给接受角色）。

---

## 23. 接受轮 29 返工：SP29-1 / BC-DATA-26 近重复闭包的有界证明表示（2026-09-01）

裁定：提案 §41（接受轮 29，`IMPLEMENTATION_REWORK_REQUIRED / S4_MANIFEST_SCALE`）。
真实归档实测的 S4 manifest 515,074,557 B 中，`atoms.near_duplicate_pairs`
2,663,282 对占 512,888,211 B，随合格 pair 数二次增长，违反 BC-DATA-25 §33.2(4)(5)。
本轮属既有零消耗缺陷修复权限：只改 `tools/dist_data/make_splits.py`、新增
`tests/test_dist_data_round29.py`、本文件与状态板；不改门值、S0–S3/S5–S9 语义、
正式工件或依赖；S5 lineage 债（§41.4）**未顺带改**。

### 23.1 改了什么（`tools/dist_data/make_splits.py`，唯一生产改动）

- **`merge_atoms` 语义逐字保留**：`sorted(phash_of_frame)` 后
  `itertools.combinations` 的 `(left, right)` 字典序全对遍历、同族跳过、
  `hamming ≤ PHASH_NEAR_DUPLICATE_HAMMING`、并查集合并、`atom_id_for`、
  `near_duplicate_pair_count`（**每一对合格 pair 仍计数**）全部不变。
- **删除 `near_duplicate_pairs`**；改记 `near_duplicate_union_witnesses`：合格 pair
  只有在 `union.find(left_family) != union.find(right_family)`（即首次连接两个不同
  family 分量）时才记录，随后合并。因此 witness 数恒为 `family_count − atom_count`，
  manifest 中不再有任何按合格 pair 数增长的成员。
- **生产路径自检两条不变量**后才返回：witness 数 = family_count − atom_count；
  `replay_union_witnesses` 按同顺序重放重建的 `atoms` 与实际分量逐字相等。任一
  不成立即 `SplitError`（fail-closed），不靠调用方或测试。
- **新增 `replay_union_witnesses(family_of_frame, witnesses)`**：只做并查集重放，
  拒绝非二元组、未知帧、同族 pair 与冗余 pair（已在同一分量），返回与
  `merge_atoms()["atoms"]` 同形的 `{atom_id: 升序成员族}`。
- 分量→atoms 的表达式抽成私有 `_atoms_of`，两处共用（与修前表达式同义）。
- `run_pipeline.stage4_splits` **未改**：manifest 的 `atoms` 块仍原样写入
  `merge_atoms` 的返回值，现在携带 witnesses；S7 只读 `splits["atoms"]["atoms"]`，
  未变。全仓 `tools/`、`tests/` 中 `near_duplicate_pairs` 除 make_splits 外零引用
  （grep 实测），删除它不影响任何生产消费者。

### 23.2 两条具名回归（`tests/test_dist_data_round29.py`）与修复前红

| 用例 | 判据 |
|---|---|
| `test_archive_scale_near_duplicates_keep_s4_summary_bounded` | (1) 函数级：4 族全同 pHash，每族 50 帧与 300 帧两档，合格 pair 数分别恰为 15,000 与 540,000（帧数 ×6 → pair ×36，二次增长被机械证明）；摘要中无 `near_duplicate_pairs`；witness 数 = 4 − 1；摘要内任何列表长度 ≤ family 数；canonical 字节 15,000 对→540,000 对只允许 count 位数变化（≤ +8 B）；重放重建同一 atoms。(2) 生产路径：三族世界（famA≈famB 同签名、famC 远）每族 40 帧，经 `stage3_frames_catalog()` → `stage4_splits()` 正式写出的 S4 manifest：无 `near_duplicate_pairs`，`near_duplicate_pair_count` 恰 1,600，2 个原子，witness 1 = 3 − 2，重放等价，atoms 块 < 4 KiB，列表长度 ≤ 3 |
| `test_union_witnesses_replay_exact_atoms_and_preserve_pair_count` | 6 族小夹具含传递并簇与冗余合格 pair（9 对合格、3 个 witness）：与**修前 `merge_atoms` 的逐行转写**比较，`near_duplicate_pair_count`、分量、`atom_id` 逐字相等；witnesses 恰等于从修前全量 pair 列表同序机械抽取的「首次连接」子序列；每个 witness 本身是合格 pair、跨族、Hamming ≤ 8；重放重建修前 atoms；输入字典 5 种乱序下输出与 canonical 字节均相同；冗余 witness / 同族 pair / 未知帧重放一律 `SplitError` |

修复前红（把 `make_splits.py` 临时换回 HEAD 版本、测试文件不变，`.venv-yoloe`）：

```
FAIL test_archive_scale_near_duplicates_keep_s4_summary_bounded
     AssertionError: True is not false : S4 摘要仍携带全量 near_duplicate_pairs
     （随合格 pair 数二次增长的成员；修前实测 540000 对被整份驻留并写出）
FAIL test_union_witnesses_replay_exact_atoms_and_preserve_pair_count
     AssertionError: False is not true : S4 摘要缺少 near_duplicate_union_witnesses
     （修前生产代码只有全量 pair 列表）
Ran 2 tests  FAILED (failures=2)
```

恢复后文件 SHA-256 与修后副本逐一相等，2/2 转绿。第一条正是 §41.3 (4) 要求的
「全量列表 / 上界断言变红」；断言改用 `assertFalse(... in ...)` 而非 `assertNotIn`，
以免失败消息回显 54 万对的容器（首次演示时输出达 57 MB，这里如实记录）。

### 23.3 只读归档尺度对照（不写任何工件、不重跑任何阶段）

用 scratchpad 脚本只读读取**现有**正式 S4 manifest 的全量 `near_duplicate_pairs`
与 S3 行流的族映射，同序抽取「首次连接」子序列并经生产 `replay_union_witnesses`
重放（正式根前后 92 个文件逐路径 SHA 相同）：

| 量 | 实测 |
|---|---|
| 冻结 manifest | 3 atoms，`near_duplicate_pair_count` 2,663,282，pair 列表 2,663,282 项且按字典序 |
| family 数 | 8 |
| witnesses | **5** = 8 − 3：m3-armA~detect-scout1、m3-armA~rate、s004-qual~s004-smoke、s004-qual~s004-scout、rate~scene-val |
| 重放 | 重建的 atoms 与冻结 manifest 的 `atoms` **逐字相等** |
| atoms 块 canonical 字节 | 512,888,212 B → **1,247 B**（pair count 原样保留） |
| 代价 | 36.7 s，maxrss 2.62 GiB（全部来自解析冻结的 491 MB manifest） |

现有正式 S4 manifest 是 create-once 工件，本轮**不改、不覆盖**；若将来要以新表示
物化正式 S4，只能走新 attempt，即需用户另行授权的 supersession（§41.4）。

### 23.4 套件与边界

```
python3 3.14.6        focused 437，OK（9 skip：需 Pillow 的金标）
.venv-yoloe 3.12.13   focused 437/437 OK 零 skip
.venv-yoloe 全套       972，failures=1 errors=1 skipped=1，仍只有既有两项
                      CSRT/opencv-contrib，新增失败 0（970 → 972 = 本轮两条新用例）
```

`git diff --check` 干净；角色写入检查通过。正式根仍恰六类工件各一个 attempt、
零 `.staging/`，本轮测试只写临时根；未重跑正式 S3–S5，未 supersede。S6–S9/G0/D0、
audit、supersession/补采集、依赖/模型/API/GPU/Play/ID 与后续训练继续未授权。

### 23.5 给复核角色的复核范围（本批次增量）

范围按 §12.7 的口径运行时解析（本轮 PLAY_GOVERNING 增量 = 一个生产模块 + 一个
新测试文件）。建议重点：

1. witness 记录条件是否严格在 `union.union` **之前**判定，且合格 pair 的计数不受
   该条件影响（count 仍是全量）。
2. `replay_union_witnesses` 的四条拒绝分支是否都 fail-closed，`merge_atoms` 内的
   两条不变量自检是否可能被绕过。
3. 测试中 `_legacy_merge_atoms` 是否忠实转写自修前生产函数（`git show` 上一候选）。
4. `_atoms_of` 与修前「components → atoms」表达式是否同义（键升序、成员升序）。
5. S4 manifest 的其余成员（`frames`、`dropped_frames` 等）本轮未动；请确认没有
   其它按帧数以外的量增长的成员被漏报。

### 23.6 停点

实现侧 §4.3.1 条件：(1) 范围与接口已冻结（一个模块、一个新测试文件）；
(2) 相称测试通过（双解释器 focused、钉死环境全套）；(3) 无 Unity 事项（纯离线
工具，`UNITY_NA` 待复核附议）；(4) 证据、状态板与候选已更新。PLAY_GOVERNING diff
非空，故经 Acceptance 停点确认后应开 Review round 8。
