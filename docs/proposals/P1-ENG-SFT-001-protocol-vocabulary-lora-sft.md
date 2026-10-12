# P1-ENG-SFT-001 — 受限语言选框的三态数据与评估合同（协议优先的 Qwen3-VL-2B 微调数据件）

Status: CLOSED_BY_USER（2026-09-13，用户直接关闭，不实现；D3 修订 1 正文与试选数字保留作参考，不产生任何主张）
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（Claude Code `/fable`，Fable 池）
Created: 2026-09-12
Last updated: 2026-09-13

> 承接 `COORD-010` §5 第二步。**D3 依据**：用户按 workflow §4.2 处置 D2 第二次退修为「收敛为两个更小的工作项」（账本
> 2026-09-12「用户处置 D2 第二次退修：收敛为两个更小的工作项」）：本项 = 纯离线 CPU 的数据与评估合同，零模型/零 GPU/零下载/
> 零上传；训练与云端执行 = `P1-ENG-SFT-002`（K3，前置本项 `DONE`）。**D3 修订 1 依据**：账本同日「训练线方向讨论四项定局」
> ——训练一律只用 Unity 数据；训练目标 = **三态协议优先，词表由 prompt 给定而不训进模型**；训练集构成由零样本探针的失误画像
> 驱动（§8 表 8）：① 已绑定的红色目标车作为 `car` 候选入域（表 A 规则 ①），② 选层族改为 `detect-scout1`，③ 稀疏间隔与类别/
> 对象配额按零样本成功率导出（表 E）；可迁移性用全新虚拟环境零样本评估（`P1-ENG-SFT-003`，SynDrone，只评不训）。相同车辆
> 身份分辨与真实航拍数据不入本轮。用户主动收敛与方向修订都不是常规退修，设计退修计数保持 2。`Workflow: engineering-v1`
> 只是申请；§5 为零消耗信封申请值。
> **AR2 → 本稿**：AR2-1 → 表 E（E5–E7 确定公式；选层子集不重复取样）；AR2-2 → 表 C（`gold_state`/诊断字段、legacy 逐 row_id
> 数组、405 行守恒表）、表 B/F（解析失败 `status_pred` 置空）；AR2-3 → §3 输入闭集（无手写 SHA、身份运行时解析）、冻结收据
> （manifest 不自绑定）、云端包清单与盲文件；AR2-4 → 拆分：本项唯一 K4 含全部代码 diff。

## 0. 动机（构思侧只读复算，单模型、单次 greedy、未经复核，只作动机）

探针 `UT-OFFLINE-PROBE-2026-09-12`（405 行 / 279 帧，test）复算：命中 gold 276（68.1%）；框到其他类别的车 65（16.0%）；框到
同类另一辆 28（6.9%）；松框/部分重叠/无车/无效 36。有限假设：H1 类别词分类学不对齐是主要损失（car 45%、pickup truck 52%、
truck 68%、suv 71%；car→taxi 7、suv→pickup 10、truck→container 8），且它是**环境特定**的标签约定，因此不作训练目标，
只在 prompt 中以闭集定义给出并监测退化；H2 严格歧义 23 行报告 0 次，零样本不会输出歧义状态，是闭环合同所需的显式状态
（`P1-ENG-ASSET-001` 报告 §5 G-1/G-4），是本项数据的首要目标；H3 关系 64% 只评测；H4 S 层 47% 与 32 px/token 有关，本项
只保留 S 层样本、不主张改善。定位本身不是瓶颈（框落在某辆车上 87–94%，命中框比 gold 更紧）。以上不是训练能力上限。

## 1. 目的与价值

交付一份**冻结的、数据源无关的、可被 `P1-ENG-SFT-002`/`P1-ENG-SFT-003` 逐字消费的**数据与评估合同：

1. 三态标签算法（`unique` / `ambiguous` / `none`）在执行域上逐指令派生，训练与评估同一函数；已绑定的动态目标车按规则 ①
   作为 `car` 候选，使数据覆盖闭环里真正会被语言选中的那辆会动的车。
2. 训练集构成由零样本失误画像驱动（表 E）：弱类别与歧义样本保留更多不同视图，强类别封顶，同一对象在类内封顶。
3. 冻结评估集（S4 test，探针同款去重，legacy 405 行逐行守恒），含目标车子组单列。
4. prompt v2 逐字文本（词表闭集定义在 prompt 中）、严格解析器、评分器与判定脚本（表 F/G）——`three_state`、解析、评分与
   数据集无关，SFT-003 只换标注适配器与 prompt 词表段。
5. 云端包清单与**盲**评估文件（不含 gold），使模型输入闭集在结构上只有图像与指令。

本项零模型运行，不产生任何性能数字；不证明闭环接管行为；不主张教师增量、跟踪性能、真实航拍或 Jetson 性能。

## 2. 范围与不做的事

**交付闭集（一个 K4 候选）：**

| # | 交付 |
|---|---|
| 1 | `tools/eng_sft/receipts.py`、`build_sft_data.py`（对账、三态派生、训练/选层/评估集、legacy 守恒、泄漏断言、盲文件、云端包清单、冻结收据）、`adapters/unity_s3.py`（S3 行 → 统一对象记录；SFT-003 另写 SynDrone 适配器） |
| 2 | `tools/eng_sft/prompt_v2.py`（词表段可按数据集替换）、`parse.py`、`evaluate.py`（表 B/F/G），全部无模型夹具测试 |
| 3 | 受版本控制冻结工件：`docs/evidence/P1-ENG-SFT-001-{dataset-manifest,eval-manifest,leakage-report,legacy-conservation}.json` |
| 4 | 本地工件：`train.jsonl`、`select.jsonl`、`select-eval.jsonl`、`eval.jsonl` 及其盲版本、`legacy/`、`upload/manifest.json`、`receipts/` |
| 5 | 报告 `docs/evidence/P1-ENG-SFT-001-report.md`：数据与评估合同的事实（计数、守恒、泄漏、seen、字节、边界、失误画像对照）；无模型结果 |

**不做的事（闭集）：** 不下载、不加载、不运行任何模型（含 tokenizer 预检，归 SFT-002）；不做零样本对照、不训练、不上云、不上传；
不训练关系指令（G4 只评测）；不改 gold 框合同、不修 S5 颜色、不回写 #27；不重新划分 S4、不退役旧 test，test 与 `unassigned` 任何帧
不进训练或选层；不做教师语言、Tier-2、四臂；不引入 SynDrone 或任何非 Unity 数据（SFT-003 只作评估）；不接入 `controller/`；
不采集、不开 Unity、不创建 scenario/session/run/attempt 身份；不发布；不新增第四种模型输出状态；不做相同车辆身份分辨。

## 3. 接口与数据契约

**输入闭集（只读；身份一律运行时解析并记入输入清单，不手写 SHA；任一不符即只写失败收据）**

| 输入 | 身份来源 | 用途 |
|---|---|---|
| S0 `contract@attempt-2/contract.json` | S3 manifest `inputs` 链 | 词表/关系闭集常量核对 |
| S3 `frames_catalog@attempt-2`：`frames_catalog.json` + `shards/*.ndjson.gz`（151 片） | manifest 逐片 `lines`/`compressed_bytes`/SHA | 逐帧对象状态、`blocking`/`referable`、框、`target_blocker_px`、`target_source_bound`、族、站位 |
| S4 `splits@attempt-2/splits.json`（`shards/` 7 片只做 SHA 核对） | 文件 SHA 现算并记录 | `frame_id → split` |
| S5 `field_catalog@attempt-2/field_catalog.json` | 文件 SHA 现算，并与探针清单 `source.field_catalog_sha256` 相等 | 类别/颜色验证状态 |
| S1 `inventory@attempt-2/inventory.json` 的 `records[]`（`kind ≠ truth`） | 文件 SHA 现算；每条 `path/sha256/bytes` | 帧图像绑定核验 |
| 帧 JPEG（动态成员 = 各集合 manifest 列出的帧） | 逐张 SHA 对 S1 记录 | 训练/评估图像 |
| `runtime/eng-asset/P1-ENG-ASSET-001/instructions.ndjson.gz` | SHA 现算，并与探针清单 `source.instructions_sha256` 相等 | AC-1 旧七值对账参照 |
| `docs/evidence/P1-ENG-ASSET-001-instructions-summary.json` | 受版本控制 | 七值直方图相等断言 |
| 探针 `probe/manifest-default.json`、`outputs/qwen3vl-2b-default-20260912/predictions.jsonl`（T7 → 本地 `legacy/`） | 首次读取现算 SHA 并记入清单；报告列出供与 Unity 日志所列前缀比对 | legacy 405 行守恒表；v1 诊断附表输入 |
| **不读取**：`layout@attempt-2`、帧 sidecar、真值文件、`runtime/` 其他内容 | — | — |

**复用的既有函数（不改）：** `build_catalog.frame_world(entry, field_catalog)`（S7 调用形态；执行域 = `blocking(f)`）、
`tier1_lang._noun_conflicts`、`tier1_lang._noun_satisfies`、`SceneObject.referable`、`tier1_lang.execute` + `hits_expected_target`
（G4）、`tier1_lang.render`；`tools/eng_asset/inventory.classify_uniqueness`（只用于 AC-1 旧七值对账）。

**表 A 三态派生（`three_state(world, noun, entry)`；noun = `{class}` 或 `{class, color}`）**

令 D = `frame_world(entry, S5).domain`，C = {o ∈ D : `_noun_conflicts(o, noun)`}，M₀ = {o ∈ C : `o.referable` ∧
`_noun_satisfies(o, noun)`}。**规则 ①（本项域规则）**：若 `dynamic-target` ∈ C、`entry.target_source_bound` 为真、
`entry.target_blocker_px` 非空且 `_noun_satisfies(dynamic-target, noun)`（即 noun 为 `{car}` 或 `{car, red}`），则
M = M₀ ∪ {dynamic-target}，其框 = `target_blocker_px` 裁剪到画幅后归一化；否则 M = M₀。按序、互斥：

| 序 | 状态 | 条件 | 目标 |
|---|---|---|---|
| 1 | `none` | C = ∅ | 无框 |
| 2 | `unique` | C = M ∧ \|M\| = 1 | M 的唯一对象框 |
| 3 | `ambiguous` | C = M ∧ 2 ≤ \|M\| ≤ 4 | M 全部对象框，按 (x1, y1, x2, y2) 升序 |
| 4 | `gray_overflow` | C = M ∧ \|M\| ≥ 5 | 排除（计数披露） |
| 5 | `gray_definite_plus_uncertain` | \|M\| ≥ 1 ∧ C ≠ M | 排除训练；评估 G3′（诊断，无门） |
| 6 | `gray_uncertain_none` | M = ∅ ∧ C ≠ ∅ | 排除（不确证不存在，不标 none） |

规则 ① 与 `P1-VLM-DATA-001` BC-DATA-8.3/9（动态目标永不可作 target/ref）**不同**：那是研究指称唯一性合同；本项是工程数据
合同，把已绑定的目标车视为可框选的 `car` 候选，其框与其他 gold 同源（真值投影）。不改上游函数，规则 ① 在 `three_state`
内于既有判定之后追加；未绑定或无框时仍按通配处理（全帧灰区）。

**表 A′ 闭集逐项处置**

| 情形 | 在 D 中的表示 | 效果 |
|---|---|---|
| 该类 0 / 1 / ≥2 个 `OK` 目录车 | referable=True，class_word 已验证 | none（若无其他可能匹配）/ unique / ambiguous |
| 同类非 OK（`TRUNCATED`/`TOO_SMALL`/`EXCLUDED_OCCLUDED`，可见面积 > 0） | ∈ C，referable=False | C ≠ M → 灰区 |
| 未知类别阻断体（8 辆无 S5 条目车）/ 类别未验证 | class_word=None，与任何 noun 冲突 | 该帧全部 noun 灰区 |
| 同类 phantom | class_word 已知、color_word=None | class noun 灰区；异类 phantom 无影响 |
| 动态目标在视野内、已绑定、框已知 | 规则 ①：`car`/`red car` 的确证候选 | 可为 unique 目标（帧内无其他 car）或 ambiguous 候选；对其他类 noun 无影响 |
| 动态目标在视野内、未绑定或无框 | 逐字段通配 | 全帧灰区 |
| 动态目标不在视野内 | ∉ blocking | 无影响 |
| 颜色未验证 | color_word=None | class noun 不受影响；color noun 灰区 |
| 已知颜色反例 #27（`Vehicle_Bus_color03`） | 对象在 D 中 | 该帧全部 `bus` 的 color noun 排除（训练与评估），计数披露；不回写 S5 |

noun 枚举：每帧九个 class noun；color noun 对帧内存在 `OK` 且颜色 `VERIFIED` 的 (class, color) 组合与（规则 ① 成立时）
`(car, red)` 枚举；color unique 记 `color_required`，评估 G2 只取 `color_required=true`，训练两者都用；不生成 color-none。
与旧七值：`UNIQUE_CLASS` ⇔ unique 且 M = {该对象}（§8 表 2）；G4 = `UNIQUE_RELATION` 行程序在 D 上 `execute` 唯一且命中目标，
只评测。gold = S3 `visible_norm_xywh`（amodal 投影，`UNVERIFIED`）或目标车 `target_blocker_px` 归一化框。

**表 B prompt v2 与解析（逐字冻结；词表段 `{vocab}` 按数据集替换——Unity 用九类段，SFT-003 用其自身闭集；prompt 构造函数
只接受 (图像路径, surface, g4 标志, 词表段名)，结构上不可见 gold）**

- 图像原尺寸；处理器 `size = {"shortest_edge": 65536, "longest_edge": 16777216}`；Unity 640×480 时断言 `image_grid_thw == [1, 30, 40]`
  （由 SFT-002 执行）。
- prompt v2（英文，逐字；Unity 词表段）：

```text
You are given one aerial image taken by a drone camera. Locate the object described by the instruction.
Instruction: {surface}
Vehicle categories form a closed set of nine mutually exclusive labels: ambulance, bus, car, container truck, pickup truck, police car, suv, taxi, truck. Always use the most specific label: "car" means an ordinary passenger sedan or hatchback and never includes a taxi, police car, suv, pickup truck or ambulance; "truck" means a cargo truck that is neither a pickup truck nor a container truck; "container truck" is a truck carrying a shipping container; "suv" and "pickup truck" are never "car". When a color is given it is one of: blue, gray, green, purple, red, yellow.
Coordinates: bbox_2d = [x1, y1, x2, y2] are integers from 0 to 1000 relative to the image width and height, origin at the top-left corner, x increasing to the right and y increasing downward, with x1 < x2 and y1 < y2.
Reply with exactly one JSON object and nothing else:
- exactly one object matches: {"status": "unique", "bbox_2d": [x1, y1, x2, y2]}
- two or more objects match: {"status": "ambiguous", "candidates": [{"bbox_2d": [x1, y1, x2, y2]}, ...]} listing every matching object
- no object matches: {"status": "none"}
```

  第三段（"Vehicle categories … yellow."）即词表段 `{vocab}`；G4 追加段（仅 G4 行）：`"to the viewer's left of X" means the described
  object appears further to the left in the image (smaller x) than the object X; "to the viewer's right of X" means further to the right (larger x).`
- 输出闭集：三种 JSON；无 `label`。gold 整数化：`x1 = ⌊x·1000 + 0.5⌋` 等，裁到 [0, 1000]，x2 ≤ x1 则 x2 = x1 + 1（1000 处反向减 1）；
  候选按 (x1, y1, x2, y2) 升序。预测 `bbox_2d/1000` 与 gold 浮点框算 IoU。
- 解析器（fail-closed）：去 fence 并计数 → JSON → `status` 闭集 → 框长度 4、整数、0–1000、`x1<x2 ∧ y1<y2` → `candidates` 2…8；
  `parse_error` 闭集 {`JSON_ERROR`, `SCHEMA_ERROR`, `RANGE_ERROR`, `ORDER_ERROR`, `TRUNCATED`}；**任一 `parse_error ≠ null` 即
  `status_pred = null`**（原始 status 只存 `raw_status`）；记录 `gen_tokens`、`finish_reason`、`prompt_sha256`、`image_grid_thw`。

**表 C 派生工件 schema（`p1-eng-sft-001/<name>/v1`；每件记录来源文件的运行时 SHA）**

| 工件 | 必含字段 |
|---|---|
| 统一对象记录（适配器输出） | `object_id, class_word（None=未知）, color_word（None=未验证）, referable, status, visible_norm_xywh`；Unity 适配器另给 `dynamic_target`（规则 ①） |
| `sample` | `sample_id, frame_id, frame_sha256, split, family, station_key, frame_index, noun_type ∈ {class, color}, surface, noun, state ∈ {unique, ambiguous, none}, color_required, target_object_ids[], target_boxes_norm_xywh[], target_bbox_2d_1000[], stratum, thin_key, has_dynamic_target, oversample_copies` |
| `eval-row` | `row_id, frame_id, frame_sha256, family, frame_index, group ∈ {G1, G1t, G2, G2t, G3, G3t, G3p, G4, G5, LEGACY_ONLY}, gate_row（G3p/LEGACY_ONLY 为 false）, surface, noun 或 relation_program, gold_state ∈ {unique, ambiguous, none, null}（G3p 为 null）, diagnostic ∈ {null, DEFINITE_PLUS_UNCERTAIN, LEGACY_ONLY_DEDUPE_CAP}, definite_ids[], target_object_ids[], gold_boxes_norm_xywh[], stratum, seen_target, seen_candidates[], seen_all, seen = null（none）, legacy_probe[]`（每条 `{row_id, group_v1, object_id_v1, gold_v1_xywh, same_class_visible_v1}`） |
| `blind-row`（云端用） | `row_id, frame_path, surface, g4, vocab`——无 gold、状态、对象、legacy 字段；盲文件行数与 manifest 相等 |
| `legacy-conservation` | 405 条：`{row_id, group_v1, frame_path, surface, new_state, eval_row_id 或 null, group, disposition ∈ {ADMITTED, LEGACY_ONLY}}`；Σ = 405 |
| `dataset-manifest` / `eval-manifest` | 只含内容：行数、状态/组/类别计数、规则常量与实取（表 E 各步）、每个 jsonl 与盲文件的行数与 SHA、帧集合数量与总字节；不含自身/提交 SHA |
| `freeze` 收据（本地，提交后生成） | HEAD、冻结闭集七文件的跟踪/干净状态与 SHA、jsonl/盲文件 SHA |
| `upload/manifest.json` | 训练帧 ∪ 选层评估子集帧 ∪ 评估帧、`train.jsonl`、`select-eval.blind.jsonl`、`eval.blind.jsonl`、`prompt_v2.py`；不含 gold 评估文件与 `runtime/` 其他内容 |

**表 D 冻结评估集（S4 test；去重与探针逐字相同：每 (组, 键, 族) 帧序号间隔 ≥ 30、≤ 4 张；键 = 目标对象 / 候选集串 / 类别；
目标车子组键 = `dynamic-target`；配额 = 去重后全部可得，只有 G3′/G5 封顶）**

| 组 | 定义 | 试选实取 | 指标 |
|---|---|---|---|
| G1 | class noun `unique`，目标为目录车 | 210 | Success、误报歧义率、误报 none 率、无效率 |
| G1t | class noun `unique`，目标为动态目标车（"the car"） | 23 | 同上，单列 |
| G2 | color noun `unique` ∧ `color_required`，目录车 | 49 | 同 G1 |
| G2t | `the red car` unique，目标为动态目标车 | 23 | 同上，单列 |
| G3 | class noun `ambiguous`，候选不含目标车 | 48 | 报告率、集合 F1、严格成功 |
| G3t | class noun `ambiguous`，候选含目标车 | 12 | 同上，单列 |
| G3′ | class noun `gray_definite_plus_uncertain` | 50（封顶） | 诊断，无门 |
| G4 | `UNIQUE_RELATION` 行 | 86 | Success（须 status=unique） |
| G5 | class noun `none` | 100（每类 ≤ 12） | none 率 |
| LEGACY_ONLY | 旧行新状态合法但被去重排除 | 9 行 | 只进 v1 诊断附表 |

排序：S/M/L 轮转，层内 `sha256(seed‖frame_id‖键)` 升序，seed `tdt-eng-sft-001-2026-09-12`；legacy 行先行纳入。legacy 守恒
（按各自 surface 重新派生、逐 row_id 保留、不覆写旧清单）：G1 210、G2 49、G3 12 行（11 个评估行）、G3′ 39 行 + 9 行
LEGACY_ONLY、G4 86；Σ = 405；legacy 行帧内均无目标车在场，规则 ① 不改变其状态。功能门（表 G）在 G1∪G2、G3、G5 上计算；
`t` 子组只报告，不入门。

**表 E 训练集与选层集（由零样本失误画像导出；确定顺序，全部零模型）**

| 步 | 规则 | 试选实取 |
|---|---|---|
| E1 | 训练池 = S4 `train ∪ dev` 三态样本；选层集 = 族 `detect-scout1` 整族划出；训练子集 = 其余六族（a1、a2、a7、rate、scene-val、m3-armA） | 选层：稀疏后 unique 925、ambiguous 41、none 504 |
| E2 | 稀疏（每 (族, 状态, noun_type, 键) 帧序号间隔）：`ambiguous` 2；`unique` 且（类别 ∈ 弱类 {car, pickup truck, truck, suv}（零样本 G1 < 75%）或 S 层）2，其余 5；`none` 5 | 训练稀疏后 unique 8,991、ambiguous 466、none 11,202 |
| E3 | unique 类别配额：每类 ≤ 700（哈希序），同一对象在类内 ≤ 350 | 4,006：car 517（目标车 350 + 目录车 167）、container truck 700、pickup truck 700、suv 700、taxi 400、bus 334、ambulance 285、truck 272、police car 98 |
| E4 | ambiguous 每候选集键 ≤ 60（哈希序） | 411（truck 180、car 90、pickup 75、container 28、police 18、taxi 16、suv 4；含目标车 65） |
| E5 | none 取数 N_none = ⌊0.10 · (\|U\| + \|A\|) / 0.90⌋，逐类轮转、每类 ≤ ⌈N_none/9⌉，哈希序 | 490（每类 50–55） |
| E6 | 复制系数 k = min(8, ⌈0.15 · (\|U\| + N_none) / (0.85 · \|A\|)⌉)，写入 manifest，由 SFT-002 加载时复制 | k = 2（份额 15.5%） |
| E7 | 最终训练多重集 = U + none_kept + k × A；优化器实际见过的帧 = distinct 帧 | 5,318 样本 / 3,185 帧 / 142.5 MB |
| E8 | 选层评估子集 = 选层集全部 ambiguous + 哈希序 unique min(300, 可得) + none 100，不重复取样 | 41 + 300 + 100 = 441 行 / 307 帧 |
| E9 | seen：对象在优化器实际见过的帧的 `blocking` 域中出现即 seen | 76 个对象（含 `dynamic-target`） |

**表 F 评分（`evaluate.py`；分母 = 该组 manifest 全部 gate 行，任何失败不剔除）**

| 项 | 规则 |
|---|---|
| 预测文件有效性 | 行集合与 manifest 一一对应：缺行 / 重复 `row_id` / 多余行 → 整次 `PREDICTIONS_INCOMPLETE`，不评分 |
| G1/G1t/G2/G2t/G4 Success | `status_pred = unique` ∧ IoU ≥ 0.5；其他状态或 null 均失败；误报歧义率、误报 none 率、无效率分列 |
| G3/G3t | 报告率 = #status_pred=ambiguous / n；IoU ≥ 0.5 边上的最大基数一对一匹配（≤ 4 × ≤ 8，穷举）；TP/FP/FN、F1；严格成功 = 报告 ∧ F1 = 1 |
| G5 | none 率 |
| G3′ | 诊断：报告率；status_pred=unique 时任一 M 命中率 |
| 分层 | S/M/L、seen/unseen、类别 |
| 配对差 | G1∪G2 同一行域（259 行）：d = mean(success_A − success_B)；bootstrap 行级 B = 2,000、seed 20260912、百分位 2.5/97.5；描述性 |
| v1 诊断附表 | 405 行 v1 输出映射三态后配对；只报告 |

**表 G 判定合同（申请值；本项接受时冻结，由 SFT-002 执行）**

| 层 | 规则 |
|---|---|
| 功能门 | (a) G3 报告率 ≥ 0.70 且严格成功 ≥ 0.50；(b) G1∪G2 误报歧义率 ≤ 0.10 且误报 none 率 ≤ 0.05；(c) G5 none 率 ≥ 0.80 → `GATE_MET` / `GATE_NOT_MET` |
| 词表非劣（退化监测，不是训练目标） | (d) G1∪G2 配对差点估计（微调 − prompt v2 零样本）≥ −2.0 pp → `NON_INFERIOR` / `INFERIOR`；CI 只披露 |
| 目标车子组与增量 | G1t/G2t/G3t 与逐组配对差、seen/unseen 分列；描述性 |
| 完成状态 | 由 SFT-002 的交付/复核/附议决定；判定结果是评估事实，不自动触发追加 run |

**写入分层（三类互斥，路径闭集）**

| 类别 | 路径闭集 | 谁写 |
|---|---|---|
| A1 实现者源码/测试 | `tools/eng_sft/{__init__,receipts,build_sft_data,prompt_v2,parse,evaluate}.py`、`tools/eng_sft/adapters/{__init__,unity_s3}.py`、`tests/test_eng_sft_{build,parse,evaluate}.py`、`tests/fixtures/eng_sft/`、`docs/evidence/P1-ENG-SFT-001-report.md`、`.gitignore` 一条 `outputs/eng-sft/`、提案「待裁定」节、`docs/current-status.md`（按角色权限） | 实现角色 |
| A2 工具输出 | 受版本控制（各 ≤ 2 MB）：四份冻结 JSON、`docs/evidence/P1-ENG-SFT-001-tests.log`；本地 `outputs/eng-sft/P1-ENG-SFT-001/`：`train.jsonl`、`select.jsonl`、`select-eval.jsonl`（+ `.blind`）、`eval.jsonl`（+ `.blind`）、`legacy/`、`upload/manifest.json`、`receipts/`；合计 ≤ 64 MB | 工具（实现角色运行） |
| A3 其他角色 | `docs/reviews/P1-ENG-SFT-001.md`（复核）；`docs/implementation-status.md` 与提案决策/核对表/复判（接受）；本项无 Unity 日志条目 | 对应角色 |

**收据：** `tools/eng_sft/receipts.py` 只 import `tools.eng_asset.receipts` 的 `sha256_file`、`utc_stamp`、`peak_rss_bytes`、`output_record`；
自定义 `WORK_ID`、schema 前缀、输出根 `outputs/eng-sft/P1-ENG-SFT-001/`、禁写闭集（ASSET-001 §3 再加 `runtime/eng-asset`、
`outputs/eng-asset`、`tools/eng_asset/`）、失败原因闭集 {`MANIFEST_COUNT_MISMATCH`, `SHARD_HASH_MISMATCH`, `INPUT_HASH_CHANGED`,
`OUTPUT_PATH_FORBIDDEN`, `HISTOGRAM_MISMATCH`, `LEGACY_SOURCE_MISMATCH`, `EVAL_GROUP_EMPTY`, `CONSERVATION_MISMATCH`, `FROZEN_FILE_DIRTY`}；
输入清单阶段 `build`、`freeze`、`stop` 各写 before/after 快照，只追加；失败只写失败收据。F8 日志入口不使用。

**冻结机制：** 四份 JSON 与三份脚本提交后运行 `build_sft_data.py freeze` 生成冻结收据（不入库、不被冻结文件引用）；SFT-002/003 的
校验链：包内 jsonl/盲文件 SHA = manifest 记录 = 冻结收据记录，manifest/脚本 SHA = 冻结收据 = 该 HEAD 下 `git ls-files` 版本。

**红线（继承）：** `tools/eng_sft/` 不 import `controller.*`；不改运行时任何文件；训练标签来自真值目录属离线数据加工，运行时真值
隔离规则不变。

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | 对账与输入清单：只读 §3 输入闭集，逐件核对 S3/S4 manifest 计数（S3 43,535 / 151 片；S4 2,523/13,144/8,450/0；S5 690/93/37）与分片 SHA、S1 记录对帧 SHA、S5/instructions SHA 与探针清单 `source` 相等；`classify_uniqueness` 重算 57,430 行七值直方图与 `P1-ENG-ASSET-001-instructions-summary.json` 逐值相等；不符即 fail-closed；输入清单三阶段 before/after 只追加 | `test:tests.test_eng_sft_build.ReconciliationTests.test_shard_hash_mismatch_writes_failure_receipt_only`；`test:tests.test_eng_sft_build.ReconciliationTests.test_histogram_mismatch_fails_closed`；`test:tests.test_eng_sft_build.ReceiptTests.test_input_manifest_phases_append_only`；`artifact:docs/evidence/P1-ENG-SFT-001-dataset-manifest.json` | K4 | 2026-09-12 |
| AC-2 | 三态派生与集合：`three_state` 按表 A（含规则 ①）经统一对象记录派生，表 A′ 每行具名回归（含绑定/未绑定/无框动态目标）；选层集 = `detect-scout1`、训练子集 = 其余六族、test 与 `unassigned` 零帧；E2–E9 按确定公式与顺序执行，各步实取写入 manifest；生产切片 `UNIQUE_CLASS` ⇔ unique-self 逐行相等；`has_dynamic_target` 样本在 car 类内 ≤ 350 | `test:tests.test_eng_sft_build.ThreeStateTests.test_table_a_prime_cases`；`test:tests.test_eng_sft_build.ThreeStateTests.test_dynamic_target_is_definite_candidate_only_when_bound_with_box`；`test:tests.test_eng_sft_build.ThreeStateTests.test_unique_class_equivalence_on_production_slice`；`test:tests.test_eng_sft_build.SplitTests.test_selection_family_and_quota_steps_are_deterministic`；`artifact:docs/evidence/P1-ENG-SFT-001-dataset-manifest.json` | K4 | 2026-09-12 |
| AC-3 | 冻结评估集、守恒与泄漏：评估集只取 S4 test，按表 D 生成（含 G1t/G2t/G3t 单列）；eval-row 带 `gold_state`/`diagnostic`/`gate_row`/`legacy_probe[]`；`legacy-conservation` Σ = 405，重复键行各自保留 gold；`leakage-report` 断言训练∪选层 ∩ 评估 帧 SHA 交集 = ∅、训练∪选层 ∩ (test ∪ unassigned) = ∅、seen 按 E9；G1/G3/G5 任一为空 → `EVAL_GROUP_EMPTY` | `test:tests.test_eng_sft_build.EvalSetTests.test_conservation_sums_to_405_and_keeps_per_row_gold`；`test:tests.test_eng_sft_build.EvalSetTests.test_target_subgroups_are_separate_and_non_gate`；`test:tests.test_eng_sft_build.EvalSetTests.test_leakage_assertions_fail_on_injected_test_frame`；`test:tests.test_eng_sft_build.EvalSetTests.test_empty_key_group_fails_closed`；`artifact:docs/evidence/P1-ENG-SFT-001-eval-manifest.json`；`artifact:docs/evidence/P1-ENG-SFT-001-legacy-conservation.json` | K4 | 2026-09-12 |
| AC-4 | prompt、解析、评分、判定：`prompt_v2.py` 逐字等于表 B（词表段可替换且逐字冻结，导出 `prompt_sha256`），构造函数无法接收 gold；解析器按表 B（`parse_error ≠ null ⇒ status_pred = null`）；评分器按表 F（一对一最大匹配、分母不剔除、完整性、子组单列）；判定脚本按表 G；bootstrap 参数固定；全部无模型夹具测试 | `test:tests.test_eng_sft_parse.ParserTests.test_error_closed_set_clears_status_pred`；`test:tests.test_eng_sft_evaluate.MatchingTests.test_max_cardinality_one_to_one_matching`；`test:tests.test_eng_sft_evaluate.VerdictTests.test_three_layer_status_on_fixture_predictions`；`test:tests.test_eng_sft_evaluate.PromptTests.test_prompt_builder_cannot_see_gold_and_vocab_is_frozen`；`test:tests.test_eng_sft_evaluate.CompletenessTests.test_missing_or_duplicate_rows_invalidate_run` | K4 | 2026-09-12 |
| AC-5 | 盲文件、云端包清单与冻结收据：盲文件只含表 C blind-row 字段且行数与 manifest 相等；`upload/manifest.json` 只列表 C 允许项；`freeze` 在提交后生成收据，任一冻结文件未跟踪/脏 → `FROZEN_FILE_DIRTY`；manifest 不含自身/提交 SHA | `test:tests.test_eng_sft_build.BlindTests.test_blind_rows_have_no_gold_fields`；`test:tests.test_eng_sft_build.PackageTests.test_upload_manifest_excludes_forbidden_and_gold_files`；`test:tests.test_eng_sft_build.FreezeTests.test_dirty_or_untracked_frozen_file_is_refused` | K4 | 2026-09-12 |
| AC-6 | 报告与边界：报告给出表 D/E 实取、守恒摘要、泄漏与 seen、字节与执行收据（耗时、峰值 RSS ≤ 1 GB）、输入身份、**失误画像对照表**（零样本逐类成功率 vs 训练逐类样本与混淆对暴露，§8 表 8 格式）；实现 diff 只含 A1/A2；本地目录 ≤ 64 MB、受版本控制 A2 各 ≤ 2 MB；不 import `controller.*`；全套测试摘要区分基线已有失败与本批新增失败 | `test:tests.test_eng_sft_build.WriteBoundaryTests.test_output_inside_forbidden_roots_is_refused`；`test:tests.test_eng_sft_build.WriteBoundaryTests.test_no_controller_imports`；`cmd:python3 -m unittest discover -s tests > docs/evidence/P1-ENG-SFT-001-tests.log 2>&1; tail -n 3 docs/evidence/P1-ENG-SFT-001-tests.log`；`artifact:docs/evidence/P1-ENG-SFT-001-report.md` | K4 | 2026-09-12 |

AC 编号一经接受即稳定；实现期合同问题写「待裁定」节，答复只追加。

## 5. 预算信封（申请值；`ACCEPTED` 后由用户逐字授权入账，缺项视为 0）

| 项目 | 上限（申请） |
|---|---|
| Consuming | no |
| scenario/session/run/attempt ID / Unity Play / 模型 API | 0 / 否 / 0 |
| 模型下载、模型运行（含 tokenizer）、训练 GPU·h、云端、上传、非 Unity 数据 | 全部 0（归 SFT-002 / SFT-003） |
| 本地计算 | 桌面 CPU；单次构建 ≈ 1–2 min，峰值 RSS ≤ 1 GB（试选 456 MB） |
| 派生工件 | 仅 §3 A2；受版本控制文件各 ≤ 2 MB，本地目录 ≤ 64 MB |
| 用户决策点 | ≤ 1（接受与授权入账） |
| 发布 | 否 |

## 6. 限制与不承诺

- 本项零模型运行，不产生任何性能数字；gold 来自真值目录投影（框 `UNVERIFIED`，S6 未执行）；颜色词只覆盖 37 辆已验证车 + 目标车
  的 `red`；#27 反例所在帧的 `bus` 颜色指令整帧排除；不生成 color-none。
- 动态目标车是脚本生成的红色立方体车（`TargetVisualFactory.cs`），非目录车型，目录里没有同款；它是单一对象，在 car 类内封顶
  350 条；`G1t/G2t/G3t` 单列，不与 G1/G2/G3 混算；规则 ① 是本项工程数据合同，不回改 DATA-001。
- 词表对齐**不是训练目标**：训练样本只承担协议（三态、枚举、框），九类语义靠 prompt 词表段；表 G(d) 只监测退化。可主张的泛化按
  评估集逐行 `seen` 披露；可迁移性另由 SFT-003 的 SynDrone 零样本评估支持，本项不主张。
- 评估集在探针同款去重下 G1/G2/G4 可得行就是旧探针的 210/49/86；G2 只有 7 个对象；G3 48 行；5 Hz 近重复极高，行级 CI 只是
  描述性区间。探针已读取 test 279 帧做零样本推理，本项只再次读取 test 帧元数据与图像字节做清单。
- `DONE` 需实现证据 + `R<n>@K4` 通过 + `UNITY_NA` 经复核附议；不表示任何模型能力。

## 7. 必经停点

- **唯一停点 `K4`**：AC-1…6 合并为一个候选（含全部本项源码 diff、冻结工件与报告），走 `C1@K4` → `R<n>@K4`；独立复核可用真实
  工件重跑构建器（≈ 1–2 min，零 GPU）。不触发 K1/K2/K3/K5。
- `P1-ENG-SFT-002` 的任何模型/云端行动以本项 `DONE` 为前提；`P1-ENG-SFT-003` 只复用本项的 `three_state`、解析与评分，其数据
  适配器在其自身 K4 停点接受。
- Unity 列申请 `UNITY_NA`（纯离线、零运行时行为），须复核角色在 `docs/reviews/P1-ENG-SFT-001.md` 附议。

## 8. 只读试读与试运行数字（D3 修订 1：按表 A（含规则 ①）/D/E 规则重做，零写入、零 ID、零模型；脚本留 scratchpad）

**表 1 执行收据**：S3 全量流式扫描 + `frame_world` 逐帧构域 + 三态派生 + 配额 + 试选 + 绑定核验：56.8 s，峰值 RSS 456 MB；
帧绑定（存在 ∧ 字节 = S1；D3 已做 SHA 核验 3,578/3,578）：训练 3,185/3,185、选层评估子集 307/307、评估 459/459；上传集合
3,951 帧 / 180.0 MB。

**表 2 旧七值（目标行）× 新 class-noun 状态（全量 57,430 行；规则 ① 之前，规则 ① 不改变目录车行的 unique 判定）**

| 旧七值 | unique-self | ambiguous-member | gray_definite_plus_uncertain |
|---|---|---|---|
| UNIQUE_CLASS | 38,972 | 0 | 0 |
| AMBIGUOUS_SAME_CLASS | 0 | 973 | 2,318 |
| COLOR_UNVERIFIED | 0 | 781 | 5,284 |
| UNIQUE_CLASS_COLOR | 0 | 898 | 2,028 |
| UNIQUE_RELATION | 0 | 613 | 1,724 |
| WILDCARD_UNKNOWN_CLASS | 0 | 0 | 3,839 |

**表 3 三态样本可得数（含规则 ①，稀疏前）**

| split | class unique / ambiguous / none | class 灰区（确证+不确证 / 不确证 none） | color unique（需色 / 不需色）/ ambiguous / 灰区 / #27 排除 |
|---|---|---|---|
| train（a2） | 1,497 / 198 / 9,341 | 2,133 / 9,538 | 0 / 1,120 / 174 / 1,107 / 25 |
| dev（六族） | 17,444 / 555 / 58,288 | 5,910 / 36,099 | 1,303 / 9,565 / 11 / 1,796 / 0 |
| test | 10,084 / 552 / 43,659 | 4,268 / 17,487 | 1,110 / 7,523 / 24 / 2,292 / 316 |

规则 ① 解锁的 `car` 数据（dev + a2 + scout1）：目标车为帧内唯一 car 3,435 帧、目标车 + 目录车歧义约 200 帧；`unassigned`
（与 test 同会话）继续零使用。

**表 4 评估集试选（test）**

| 组 | 可得 | 实取 | S/M/L | 类别 / 对象 | seen |
|---|---|---|---|---|---|
| G1 | 6,553 | 210 | 42/99/69 | 9 类 / 48 | 目标 180/210 |
| G1t | 3,531 | 23 | 11/9/3 | car / 目标车 | 23/23 |
| G2 | 934 | 49 | 12/20/17 | 3 类 / 7 | 49/49 |
| G2t | 3,707 | 23 | 11/9/3 | red car / 目标车 | 23/23 |
| G3 | 480 | 48 | 21/14/13 | 8 类 / 28 | 全候选 44/48 |
| G3t | 72 | 12 | 4/8/0 | car / 含目标车 | 12/12 |
| G3′ | 4,268 | 50 | 17/18/15 | 8 类 / 21 | 45/50 |
| G5 | 43,659 | 100 | — | 每类 8–12 | n/a |

评估集 515 gate/诊断行 + LEGACY_ONLY 9 行，459 帧，19.6 MB。**405 行守恒**：ADMITTED G1 210 / G2 49 / G3 12 / G3′ 39 / G4 86，
LEGACY_ONLY G3′ 9；重复键 3 组各行 gold 保留。seen 高是因为训练现在含 a2 与 a1/a7 六族，对象层面 76 个已见；泛化只按 seen 披露。

**表 5 训练与选层（表 E 实取）**：训练多重集 5,318（unique 4,006 + none 490 + 2 × 411）/ 3,185 帧 / 142.5 MB；unique 分层
S 466 / M 1,770 / L 1,770；目标车样本 unique 350 + 歧义 65；选层评估子集 441 行 / 307 帧 / 18.0 MB；seen 76 个对象。

**表 6 体积投影**：样本行 ≤ 800 B；`train.jsonl` ≤ 5 MB；`eval.jsonl` 524 行 ≤ 0.6 MB；四份冻结 JSON 各 ≤ 2 MB；gold JSON 紧凑
长度最大 128 字符、p50 47，保守 token 上界 74（供 SFT-002 `max_new_tokens = 160` 预检参考）。

**表 7 对象级划分（沿 D1，只描述划分）**：train+dev 有唯一指令的对象 53、test 53、其中不在 train+dev 的 31、S4 留出且在 test 的 20。

**表 8 零样本失误画像 × 训练构成（本次修订的依据；D3 原构成列作对照）**

| 类别 | 零样本 G1 Success | D3 训练 unique | 修订后 unique（E3 后） | 修订后 ambiguous | 混淆对暴露 D3 → 修订后 |
|---|---|---|---|---|---|
| car | 45% | 68 | 517 | 90 | car→taxi 11 → 178；car→suv 105 → 215 |
| pickup truck | 52% | 356 | 700 | 75 | pickup→container 451 → 222；pickup→suv 344 → 194 |
| truck | 68% | 40 | 272 | 180 | truck→container 62 → 118 |
| suv | 71% | 884 | 700 | 4 | suv→pickup 506 → 220 |
| container truck | 82% | 1,401 | 700 | 28 | — |
| taxi | 86% | 420 | 400 | 16 | — |
| bus / ambulance / police car | 90% / 92% / 100% | 252 / 249 / 70 | 334 / 285 / 98 | 0 / 0 / 18 | — |

（D3 暴露列为稀疏前原始帧数，修订后列为 E3 之后的样本数，口径不同，只看方向。）零样本 66 个失误行中仅 19 行的目标车与混淆车
都曾出现在训练帧，修复只能靠类别级线索。

## Pending rulings（待裁定）

无。

## Contract conformance（核对表）

待 `C1@K4`。

## Acceptance rulings（复判）

无。

## 决策记录

**2026-09-13 D3 修订 1 接受侧审查：未 `ACCEPTED`，上交用户；不签第三次 `REVISION_REQUESTED`。**
用户拆分与方向授权已核对：纯离线 K4、动态目标入域、detect-scout1 选层、协议优先与 SynDrone 只评不训均在已定方向内；
不需重问这些方向。本项具备申请工程轨道的范围基础，但尚未接受，`engineering-v1` 不生效，AC-1…6、schema、规模、表 G 与信封不冻结。
AR2-2 的逐 row_id legacy 数组、诊断标签与解析失败清空已在文字上回应；AR2-3 的 manifest 不自绑定与独立冻结收据方向有效；
AR2-4 由独立 SFT-002 拆出解决。AR2-1 取样及完整试读仍不能宣告闭合，以下三项是交用户的已知缺口闭集，不是构思侧新退修命令。

| 编号 | 问题与证据 | 保留当前范围时的具体处理建议（尚未授权/冻结） |
|---|---|---|
| AD3-1 | **完整评估规模与试读来源不一致。** 表 D 九个非 legacy 组之和为 210+23+49+23+48+12+50+86+100=601，加 9 个 LEGACY_ONLY 为 **610**，不是 §8 的 515+9=524，差额恰为 G4 的 86。所留 `sft_d4_dryrun.py` 的 `groups` 未含 G4，且不读取 probe 清单、不做 legacy 优先纳入或405行映射；`eval_frames` 仅来自该 `picked`。因此 459 帧/19.6 MB、上传 3,951 帧/180 MB 不能当作完整表 D 的绑定投影。脚本 `bind()` 只检查存在和字节，旧 D3 的 3,578 张 SHA 核验也不能自动覆盖新集合。 | 保留 G4 和405行历史，不删组凑524；610只是现有表项的算术和，不冒充新实测。先按 legacy 优先、逐 row_id 守恒及 G4 独立 execute 的完整表 D 做同一次只读试选，再报告各组、并集帧数、逐张SHA绑定、字节与内存。若结果与现表不同，区分原因和实测，不把局部试读写成完整合同证明；数据尺度在该核对前保持未冻结。 |
| AD3-2 | **取样规则和试读未唯一对应。** E5 写逐类轮转；试读脚本却全局哈希排序再按每类上限截取，所得每类50–55并非足额池下轮转490行的分配。AC-2 又把 `has_dynamic_target` 样本在car类内总数限制为350，而 E3/§6 定义的是 unique 对象配额，§8 还列350个unique加65个含目标车歧义样本。若该字段覆盖两种状态，就不能同时满足。 | 按用户已选方向保留逐类轮转，并明确九类的固定轮转顺序；试读与正文使用同一算法。把350限定为 E3 的 unique 配额（class/color unique合计），65个歧义样本另受 E4/E6 控制；`has_dynamic_target` 如实标记，不通过改字段隐藏歧义样本。取样变化后联动复算 E5–E9、seen与图像并集。 |
| AD3-3 | **表 A 的缺框失败路径不闭合。** 表 A/A′ 要求已绑定但无框的目标逐字段通配、整帧灰区；实际复用 `frame_world` 只按 `target_source_bound` 赋car/red，缺框不会清空字段。仅在M中不追加该目标，会使异类noun仍能确证，与A′不符；非空但裁剪后退化的框也未在规则①定义中明确处置。 | 在新Unity适配层或三态入口明确实现本项表A′的通配规则：未绑定、缺框或裁剪后无正面积时不产生gold，并按该规则保守处理；保留上游函数原样。AC-2具名边界用例分别核对这些输入，不能以真实归档未触发替代字面合同。 |

证据范围：完整 D3 修订1正文/AC与既有D1/D2决策、授权原文、正式设计§1、工程继承/缺陷账本，ASSET合同§3/报告§0–4与R2相关依据；
只读查看 `build_catalog.frame_world`、`tier1_lang._noun_conflicts/_noun_satisfies` 及构思试读脚本
`/private/tmp/claude-501/-Users-zc-TetheredDroneTracking/040b8b56-256b-47ae-9eea-39f9521e4755/scratchpad/sft_d4_dryrun.py`。
该临时脚本只作本轮问题定位，不是冻结工件；本轮未运行它、未重做数据加工、未跑实现测试/模型，不签独立复核。610由解析表D各行计数相加得到。

退修计数保持 **2**，C/R均 **0**。按 workflow §4.2，只交用户决定：(a) 保留并接受当前范围，逐条明确 AD3-1…3 的处理；
(b) 关闭为负结果记录。建议(a)，三项均可在现有方向内解决，但本轮不代替用户选择、不自行启动新一轮修订。
即使选择(a)，也不把未经核实的schema/尺度视为已冻结，须完成上述只读试选与合同核对后由接受角色正式落定；执行信封仍另行授权。
§5尚无本地构建累计尝试上限，后续请求执行授权前必须补成可逐项批准的数值；不以 `Consuming=no` 推导无限本地加工额度。
SFT-002保持用户暂停；其将来恢复时才消费已冻结工件，不能提前使用本稿数字。

**2026-09-12 D2 接受裁定：`REVISION_REQUESTED`（第二次），上交用户。**
用户已确定的协议/词表对齐与云端训练方向保留。本轮未接受、未关闭本项，`engineering-v1`
尚未生效，AC-1…9/阈值/配方/预算未冻结。构思侧 D2 的有效修订保留；以下是提案合同审查，
不是实现核对轮或独立复核，不使用 finding 分级或 SCOPE_GAP 账本替代设计裁定。

| D1 条目 | D2 核查结果 |
|---|---|
| AR1-1 | 主体已回应：表 A 将 noun 的 C/M 集合与旧七值分离，未知/动态/phantom/灰区处置及 #27 排除已写；G4 独立执行。诊断行的 schema 承载仍有 AR2-2，不能把“标签逻辑已改”写成完整数据合同已闭合。 |
| AR1-2 | 部分回应：改按 (组, 键, 族) 限额，train/dev 用途明确，seen 改按实际训练帧；补了真实试选数字。但选层子集数字自相矛盾（AR2-1），legacy 保留结构与原清单不符（AR2-2），§8 数字不能整体冻结。 |
| AR1-3 | 主体已回应：v1 退出验收门、一对一最大匹配、缺行/重复行整次失败、配对域与 bootstrap 参数已写；负效果与交付完成分开，不记“功能通过”。解析失败的状态计分仍未唯一化（AR2-2）。 |
| AR1-4 | 部分回应：输入含 S1/探针/ASSET 参照，新收据模块、四阶段追加、F8 不使用及 gold 不进 prompt 已明确；云端运行依赖/数据闭集与冻结身份仍未闭合（AR2-3）。 |
| AR1-5 | 主体已回应：逐字 prompt、三配置、正式 adapter 不重训、冒烟步数、token 预检、有限诊断措辞及 min(10,n) 案例已写。选层样本不足将直接改变选优（AR2-1）；token 预检仍属未来获授权下载后的义务，本轮不声称已通过。 |
| AR1-6 | 部分回应：K4 前零 GPU、job_id 与正式 ID 分离、失败计额已明确；但把全部源码前移 K4 后仍要求 K3 新 R 轮，产生开轮资格冲突；重试与推理额度也未对齐（AR2-4）。 |

**剩余缺口闭集（交用户决定，不是第三轮退修指令）：**

| 编号 | 可定位的问题与后果 | 保留当前范围时须明确的处理 |
|---|---|---|
| AR2-1 | 表 E 与 §8 表 5 均写选层集稀疏后 unique **220**、ambiguous **96**、none 1,990，却要求选层评估“全部 ambiguous + unique **300** + none 100 = **496**”。未许可选层重复取样，220 条不能取出 300 条；若全部用上，实际最多 **416** 条。这会改变三态 macro 选优、推理行数及云端包，§8 不能证明所写 496 条试选已按合同完成。训练 none 的“≤10%”也只给不等式而无唯一取数规则，426 并非该约束唯一解。 | 推荐把选层 unique 明确为 `min(300, 可得不同样本数)`，不对选层补重复；按当前读数为 220+96+100=416，联动修正清单/推理申请，并据实际试选核实其图像集合。训练先固定 unique/ambiguous 稀疏集，给出 none 取数与复制系数计算的确定顺序（或明确固定取数），不能将“426”当作算法。此建议尚未写成已接受条款；不要求新增图像或扩预算。 |
| AR2-2 | 表 C 让 eval-row 继承 `state ∈ {unique, ambiguous, none}`，却必须容纳 G3′ 的 `gray_definite_plus_uncertain` 与 LEGACY_ONLY；没有可合法编码的诊断状态。legacy 合并只存 `row_ids[]` 加单个 `gold_v1_xywh`，同帧同 surface 的旧行却可能有不同 gold，不能逐行原样保留。只读原清单确认该重复键恰 **3 组、每组 2 行**，405 行去重为 **402** 个键；D2 列出的 legacy 新样本数 210+49+11+31+86+6=**393** 与所写合并规则不相容。表 F 的 G3/G5 又只用 `#status=…` 计数，没有说明解析失败后 `status_pred` 是否清空；一个已读到 status、但截断或 candidates 不合法的响应可能被不同实现计为报告成功或失败。 | 区分模型三态与数据标签状态：诊断行单列诊断原因、gold 状态为空，不新增第四种模型输出；legacy 改为逐原 row_id 的记录数组，每条自带原 group/gold/same_class_visible，并给出405行完整映射及排除/合并的守恒表，不按393个样本反推原行。解析任一失败必须不计有效状态成功/报告（分母保留），status_pred 与 raw 字段分列。此项不要求重新跑旧探针或修改原清单。 |
| AR2-3 | §3 云端包只列“三份 jsonl”，本地却有 train/select/select-eval/eval 四份、且云端选优要消费 select-eval；云端的收据依赖模块/实际输出路径未纳入明确的可运行闭包。表 C 又要求受版本控制的 dataset/eval manifest 内含“冻结提交绑定（HEAD SHA、文件 SHA）”，表 D 再要求提交后五文件干净：若这表示该文件自身及包含它的提交，就是循环绑定；若指外部文件，则引用对象未定义。只核对五文件 SHA 也没有明确模型读取的 jsonl 行字节与它们如何绑定。 | 枚举实际云端必需文件及依赖（不复制无关 runtime），明确 select-eval 的路径与是否上传完整 select；本地工具与云端输出落点分别列清。冻结 manifest 只写内容/外部数据文件的计数和 SHA，不写自己的 SHA 或包含自己的提交 SHA；提交后由独立运行收据绑定冻结文件及提交，云端校验实际 train/select-eval/eval 字节到这条链。删除本稿输入表新手写的截短 SHA，来源身份沿具名上游工件/运行时清单解析。 |
| AR2-4 | §2 交付4与§7把 cloud_runner/train_lora/verify_return 及全部无模型测试都放到候选1；候选2仅增加云端结果、adapter、报告（均不在现行 PLAY_GOVERNING）。正常成功、代码不变时，相对 K4 通过候选的治理 diff 为空，不能按 workflow §4.4 开 `R1@K3`；“候选1不含结果，所以不会空diff”不成立。§5 的8次包含“中断重试1”，但基线/正式评估各仅1次、选层≤3、冒烟≤2已合计7次，额外一次可重试哪阶段及额外推理行额未定义；8 GPU·h 标为“训练”也未明确是否包含云端评估/闲置。 | 先确定真实的候选边界：可保留K4仅数据/解析/评分，然后把有实质模型执行逻辑的源码与测试交K3候选；或按工程流程合并K3/K4代码停点，再明确无治理diff的结果核验/消费路径。不能制造无意义代码diff凑开轮，也不能豁免独立复核。GPU前置引用最终通过轮而非限定必须R1。明确每阶段累计启动上限与总上限同时成立、额外重试适用范围、部分预测是否续跑以及累计推理行额；8 GPU·h覆盖范围按实际GPU占用明确。所有数字仍须后续用户执行信封授权，当前不动用资源。 |

**证据边界。** 本轮完整读取 D2 正文/AC-1…9、D1 六项要求、状态板当前结构与交接、方向授权、
工程流程与接受细则、正式设计 §1、工程继承/缺陷账本；旧分类/收据/探针依据沿 D1 指针。
新增只读核实仅解析 T7 的 `probe/manifest-default.json`，按 `(frame_path, surface)` 分组：
3个二元重复组；例如 `G3_AMBIG-0261` 与 `G3_AMBIG-0279` 指令和帧相同，目标对象不同且 gold 不同。
未生成数据工件、未加载 tokenizer/模型、未运行实现测试；§8 的59秒/RSS/绑定/新样本数仍是构思侧
报告，本会话未独立重跑该试选，不给其签复核通过。AR2-1 的416与 AR2-2 的402/393是合同与原清单
的算术核对，不替代修订后的真实试选。

设计退修累计 **2**，核对 **0**，复核 **0**。依 workflow §4.2，**下一动作只交用户二选一**：
(a) 接受当前范围并逐条保留 AR2-1…4 已知缺口，明确处理后由接受角色落定合同与轨道，再另行取得
执行信封；(b) 关闭为负结果记录，保留 D1/D2 与有效试读，不记 DONE、不推导训练失败。
建议保留方向，缺口属于数据/执行合同一致性；建议本身不是用户授权。本轮不自行启动 D3，
不将“查看revision结果”解释为接受缺口或消费预算；不改正式设计、旧门、复核文件或授权原文。

- 2026-09-12 D1 接受裁定：`REVISION_REQUESTED`，第一次设计退修，回构思角色准备 D2。
  用户已确定的协议/词表对齐、Qwen3-VL-2B、云端自跑方向保留；未发现需要改动旧研究
  主张、运行时安全或硬件目标的必要性，不作 `REJECTED`。本项属于可申请工程轨道的新工作项，
  但本轮未 `ACCEPTED`，故 `engineering-v1` **尚未生效**；AC-1…8、阈值、配方与信封均未冻结。
  不新增研究 BC，不同步为正式设计，不启动实现、模型或派生工件加工。§8 已有真实只读扫描数字，
  但其明确使用近似分类、不同稀疏规则，尚不能证明当前表 A/D/E 合同可构建；按 workflow §4.1/§4.2
  先完成下表指定的精确试读再冻结。接受侧只读范围为本稿全部、方向授权、工程继承/缺陷账本、
  正式设计 §1、ASSET-001 合同/报告及 R2@K4 相关依据、既有分类与收据函数、探针原清单；
  未运行实现测试、未运行模型，不签独立复核。D 退修计数 1，C/R 均未开轮。

| 编号 | D1 不接受的具体原因 | D2 修改要求（本轮闭集） |
|---|---|---|
| AR1-1 | **三态标签未按输入指令定义，可能遗漏匹配对象。** `tools/eng_asset/inventory.py:296` 的 `classify_uniqueness` 先寻找颜色/关系程序，再返回 `COLOR_UNVERIFIED` 或 `AMBIGUOUS_SAME_CLASS`。因此“两辆同类 OK”不等于旧七值中的 `AMBIGUOUS_SAME_CLASS`：同一帧可以对 `the bus` 歧义，对带颜色或关系的指令唯一。表 A 又只收全部同类 OK 框，未定义 ≥2 OK 外加 distractor/phantom/dynamic-target 的处置；none 未明确未知类别阻断体，§1 的“全部匹配候选”因此无法逐字成立。 | 分开保留“旧七值对账”与“当前 surface/program 的三态派生”，写出确定的优先序、候选对象域与排除域，明确 class-only 与 color/关系程序分别判定。闭集至少覆盖：0/1/≥2 个 OK、同类非 OK、未知类别阻断体、同类 phantom、已绑定/未绑定动态目标、缺 S5 条目、颜色未验证；不确证不存在的帧不得标 none。决定 ≥2 OK 外另有不可指称匹配体时是排除、诊断，还是有完整候选标签；不要求修上游或添加第四种模型输出。训练/评估使用同一标签算法，G4 对应合法的 unique 输出，G3′ 明确无训练/门用途。承接 ASSET 报告 §4 的 #27 已知颜色反例和框未审计限制，写明派生颜色样本的处理及可报告口径，不回写 S5。 |
| AR1-2 | **取样与原探针保留冲突，精确规模和隔离尚无依据。** 表 D 的“每对象 ≤4 张”不等于原探针规则；原清单同一对象在 G1 最多 13 行、G2 最多 16 行。405 行的 60 个旧 G3 中严格 23、灰区 37，不能按原 group/gold 直接作为新三态候选集。表 E 未说明先划族再过采样的顺序、不能满足时的处置；§8 的 31 个未见对象只按 UNIQUE 指令目标统计，ASSET 报告 §3 已明确它不证明对象从未出现在训练图像中。 | 明确去重键、排序、跨组上限、none 的“对象”键和 ambiguous 的候选集键；旧 probe_row_id/原 gold 保留为独立来源字段，新 group/三态 gold 的映射另列，不覆写旧清单。按修订后的 A/D/E 只读真数据试选，给出逐组/族/三态实取、原 405 行映射与冲突数、训练/选层族及帧数、绑定率、字节与峰值内存；不足额给出确定处理，关键组为空不得自动通过。先按原始图像划出选层，再仅对训练子集过采样；区分训练池、优化器实际见过的帧与选层。按实际使用图像中的 OK/distractor/dynamic-target 可见记录定义 seen，集合输出/none 的 seen 字段类型与不适用值写清；未知身份保守披露，不能沿用“31 未见”作已证明泛化。test 与 unassigned 排除继续保持。 |
| AR1-3 | **评分与结论边界不确定，并把诊断结果提升成门。** 表 F(d) 的“同时 ≥ 探针 v1 同子集数字”与本稿/Unity 日志的“非门证据、不冻结合格线”冲突。表 D 的集合 F1 未指定一对一匹配，多重框或重叠 gold 可产生不同得分；表 B 解析失败到表 F 分母的规则缺失。§0“训练必须赢过”与 F 的绝对门/非劣门不一致，满足 (a)(b)(c) 也不足以推出“prompt 足矣”或训练有增量。 | v1 配对子集仅作诊断附表，移除其门槛身份；正式门使用本项冻结评估与 prompt v2 对照。固定 G1/G2/G4 success 是否必须 status=unique、G3 有效歧义报告定义、IoU≥0.5 的最大基数一对一匹配及 TP/FP/FN/F1、重复/多余候选和 parse_error/缺行/重复 row_id/截断的处理，失败不得从成功率分母剔除。配对非劣明确比较同一 G1∪G2 行域、精确重采样次数/seed/分位数方法；行级 CI 只解释为相关样本上的描述性区间，不证明独立对象泛化。分开“功能门满足”“训练相对 v2 的增量”和工程完成状态，说明 NOT_MET 后保留失败分析并如何收口；不自动标 DONE 或追加训练。 |
| AR1-4 | **输入与写入闭集不完整，直接复用收据模块不满足新合同。** §3 只列 S0/S3/S4/S5 与 JPEG，AC-1 却称“五件 attempt-2 工件”；图片校验依赖 S1，原探针清单/预测和 ASSET 摘要也被消费但未完整入清单。旧 `tools/eng_asset/receipts.py` 的 work_id/schema/root 与禁写集合专属 ASSET-001，未禁止本稿新增的旧 eng-asset 目录。AC-5 指向 `tests.test_eng_sft_train`，A1 未允许该文件。 | 列明实际读取的输入闭集及动态成员的具名 manifest 来源，含 S1 图像索引、S3/S4 分片、ASSET 对账参照、probe 清单/原预测；仅实际使用的 layout 等依赖才纳入。定义 input-manifest 的阶段 before/after/停点并集、已有合法产物与失败收据的边界，禁止滚动覆盖唯一前态。收据只复用适用的低层函数或在新目录适配，显式定义本项身份/schema/根、失败原因闭集与新禁写集合，不修改旧模块或继承其默认输出位置；说明 F8 日志入口是否被使用，使用才承接验证。补齐 train 测试、adapter manifest/env、云端收据等合法落点；云端包 manifest、实际 JPEG 上传、仓库/云端路径映射与回传校验一致。金标准字段留在评分侧，模型输入闭集仅图像与冻结指令，不能把 eval-row 整行渲染给模型。 |
| AR1-5 | **模型配方仍需实现者选择，不能作为可复现合同。** 表 B 只要求 prompt 四段而无逐字文本、像素上下限无数值；“最优 prompt”没有候选闭集。表 G 有 6 个 epoch/lr 组合却仅准 3 个 run，未定组合顺序/平局规则/正式 run 用哪些数据；冒烟没有更新步数上限或选样规则。已有探针发生多框截断，本稿反而将上限从 128 降至 96，§8 未证明当前 gold 序列可装下。AC-7“每组 ≥10 失败”在不足十条或无失败时不可满足。 | 在 D2 给出唯一 prompt v2 文本、完整九类定义、G4 附加段、处理器像素参数与坐标整数化/排序平局规则；冻结在任何本项 test 模型输出之前，不称最优。列出至多 3 个候选配置及执行顺序、确定的选优/平局规则、正式训练数据组成和 epoch 计法、冒烟样本与最大步数/失败退出。用已有本地 tokenizer（可用时）做零模型 token 长度核对，或将该项列为首次获授权下载后、模型运行前必须通过的预检，明确支持的候选数与超长/量化退化处置；不得静默截 gold 或扩大预算。失败案例改为每组取 min(10, 实际失败数)，零失败如实记零。§0 的“训练改不了”“定位不是瓶颈”等改为本次诊断的有限假设，不将一次探针写成训练能力上限。 |
| AR1-6 | **停点、冻结时序与执行信封尚未对齐。** K4 包含用户 GPU 零样本结果，但§7 又称“租金…在数据/评估集经独立复核之后”；二者不能同时执行。K4 AC-4 依赖评估器，K3 才出现评估判定脚本，需分清首次交付范围。§5 禁 run ID 同时列 run 收据/训练 run；租金空白、冒烟 1 次与 ≤2×32 推理的对应关系不明；中断/失败是否计额及推理/复核是否含在 8 GPU·h 内尚未闭合。 | 保留 K4→K3 的分开检查方向，明确哪些工具/冻结 manifest/基线指标在候选 1，哪些训练/最终判定在候选 2；选择一致的 GPU 基线执行位置，不能把候选 1 所需结果写成候选 1 通过后才能执行。若接受数据复核前只做获授权的基线推理，直说该例外与训练仍被 K4 阻断；若要提前数据审查，明确可开轮的候选范围及依赖，避免空 diff 另开 R。提交冻结检查写明文件闭集、跟踪状态/工作树/云端导出验证，不将“某路径 status 为空”等同文件已被提交。分开正式 scenario/session/run/attempt 身份与普通训练执行收据标识，列出含失败/中断的各阶段累计尝试、GPU·h、推理、下载/上传、磁盘限制与用户待填写租金上限；无模型 focused/full/独立复核和本地加工也明确计入方式。信封仍只是申请，完整 ACCEPTED 后再请用户授权，不先索取空白预算。 |

**D1 只读事实来源与复算口径。** 原探针清单读取自
`/Volumes/T7/TDT-PROBE-DATA-2026-09-11-finish/probe/manifest-default.json`；解析 `rows` 共 405、
`frames` 共 279，按 `group` 分为 210/49/60/86；对各组 `object_id` 做 Counter，最大计数分别为
13/16/9/8；全组同一对象最大 31。`rules.dedupe` 原文是
`per (group, object, family): frame-index gap >= 30, at most 4 picks`；旧 G3 的
`same_class_visible` 直方图为 1→37、2→21、3→2。以上只读 JSON 聚合用于证明文字合同冲突，
不是新的模型实验、标签审计或门证据；不手写新的工件 SHA。三态冲突依据为
`tools/eng_asset/inventory.py` 的 `classify_uniqueness`、
`tools/dist_data/build_catalog.py` 的 `frame_world` 与
`tools/dist_data/tier1_lang.py` 的 `_noun_conflicts`/`_noun_satisfies`。
未见对象的使用限制、#27 与旧收据身份分别见 ASSET-001 报告 §3/§4、
`tools/eng_asset/receipts.py`；F8 仅沿 `implementation-status.md` 账本及 ASSET-001 R2@K4 原 finding 使用。
本轮不改上述来源或旧 verdict。六项修改可在已授权方向内完成，本轮无需新的用户方向选择；
若 D2 仍需第二次退修，则按 workflow §4.2 上交用户，不自行发出第三次退修。

- 2026-09-12 D1 `PROPOSED`：构思角色落盘；承接 `COORD-010` §5 第二步。用户四项方向决定（逐字见账本
  同日「P1-ENG-SFT-001 — 方向四项定局（方向层）」）：电脑端复现视为已由离线探针完成；下一步 =
  评估 + 训练方向；训练目标 = 协议与词表对齐；算力 = 直接租云 GPU。轨道申请 `engineering-v1`
  待接受裁定；AC-1…8、表 F 阈值、表 G 配方、§5 信封均为申请值；两停点结构（K4 → K3）待裁定。
  零实现、零派生工件、零模型运行；§8 为只读复算。

- 2026-09-12 D2 `PROPOSED`（构思角色，回应 AR1-1…6；待接受裁定）。逐条映射：AR1-1 → §3 表 A/A′（三态在
  `blocking` 域上按 `_noun_conflicts`/`_noun_satisfies`/`referable` 逐指令派生，C = M 才可确证，闭集逐项处置，
  #27 整帧排除，G4 = 合法 unique，G3′ 只诊断）、§8 表 2 交叉表；AR1-2 → 表 D（探针同款去重键/排序/上限，
  legacy 独立字段与新状态归组、LEGACY_ONLY）、表 E（先按族划分：选层 = S4 train、训练 = S4 dev；只对训练过采样；
  seen 按优化器实际见过的帧定义）、§8 表 3–5 精确试选；AR1-3 → 表 F（一对一最大匹配、分母不剔除失败、
  完整性）、表 G（v1 只作诊断附表；功能门 / 非劣 / 增量 / 完成状态四层分开，NOT_MET 收口）；AR1-4 → §3
  输入闭集（含 S1/探针/ASSET 参照、不读 layout）、收据新模块与失败原因闭集、四阶段清单只追加、云端包与回传
  校验、F8 不使用、prompt 构造不可见 gold、A1 补齐 train/cloud 测试；AR1-5 → 表 B 逐字 prompt 与像素/坐标/
  排序规则、表 H 三配置顺序与选优并列规则、正式 adapter = 被选 run、冒烟样本与步数、token 预检 fail-closed、
  失败案例 min(10, n)、§0 改为有限假设；AR1-6 → §7 候选 1 零 GPU、候选 2 含全部云端执行、冻结提交检查
  五文件闭集、`job_id` 与 run ID 分离、§5 含失败/中断累计与零 GPU 项目。设计退修计数 1；若本轮再退修则按
  workflow §4.2 上交用户。零实现、零派生工件、零模型运行。

- 2026-09-12 D3 `PROPOSED`（构思角色；**用户范围收敛版，非第三次常规退修**；待接受裁定）。依据：账本同日「用户处置 D2
  第二次退修：收敛为两个更小的工作项」。改动：标题与 §1–§2 收敛为纯离线数据/评估合同，训练、零样本对照与云端执行移入
  新提案 `P1-ENG-SFT-002`（K3，前置 = 本项 DONE）；AR2-1 → 表 E（E3/E4 确定公式、E6 选层子集 416 行不重复取样）；
  AR2-2 → 表 C（eval-row `gold_state`/`diagnostic`/`gate_row`/`legacy_probe[]`、blind-row、`legacy-conservation` 405 行
  Σ = 405）、表 B/F（`parse_error ≠ null ⇒ status_pred = null`）；AR2-3 → §3 输入闭集删除手写 SHA、身份运行时解析并与
  探针清单 `source` 相等、manifest 不含自身/提交 SHA、冻结收据独立、云端包清单枚举（训练帧 ∪ 选层评估子集帧 ∪ 评估帧、
  `train.jsonl`、两份盲文件、`prompt_v2.py`）；AR2-4 → 拆分后本项唯一 K4 停点含全部代码 diff。§8 按新规则重做试选
  （60.3 s / RSS 442 MB），含守恒表与 416 行子集。AC 重编为 AC-1…6（旧 AC-6…9 移入 SFT-002）。设计退修计数保持 2。

- 2026-09-12 D3 修订 1（构思角色；**用户方向讨论后的修订，非常规退修**；待接受裁定）。依据：账本同日「训练线方向讨论四项定局」。
  改动：标题/§0/§1/§6 把训练目标改为「协议优先、词表靠 prompt」（表 G(d) 降为退化监测）；表 A 加规则 ①（已绑定、有框的动态目标
  作为 `car`/`red car` 确证候选，明写与 DATA-001 BC-DATA-8.3/9 不同）；表 D 加 G1t/G2t/G3t 单列子组；表 E 重写为失误驱动的确定
  规则（选层 = `detect-scout1`；弱类别/歧义/S 层稀疏 2、其余 5；每类 ≤ 700、同对象 ≤ 350；歧义每键 ≤ 60；none 逐类轮转；k 公式）；
  表 B 词表段可替换以供 SFT-003；§8 全部重跑（56.8 s / RSS 456 MB）并加表 8 失误画像对照；AC-2/3/4/6 相应更新。
  设计退修计数保持 2；SynDrone 跨环境评估另立 `P1-ENG-SFT-003`。零实现、零派生工件、零模型运行。
- 2026-09-13 用户关闭（账本同日「用户关闭 SFT-001、继续 SFT-003」）：本项 `CLOSED_BY_USER`，零实现、零证据、不记 DONE；D1–D3 修订 1
  正文、接受侧 AR1/AR2 裁定与 §8 只读试选数字保留作参考。三态规则、解析器与评分器设计由 `P1-ENG-SFT-003` 自带（数据源无关），
  不再以本项为前置；`P1-ENG-SFT-002` 维持用户暂停。接受角色可按 workflow §4.6 补归因，不另开轮。
