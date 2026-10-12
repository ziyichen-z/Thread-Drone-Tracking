# P1-ENG-SFT-002 — 受限语言选框三态协议：Unity 数据合同 + Qwen3-VL-2B LoRA 训练与云端执行（协议优先、词表靠 prompt）

Status: ACCEPTED（D3，接受角色 2026-09-13 按用户 workflow §4.2 (a) 处置正式落定；engineering-v1 生效；AC-1…14 及首次接受释义共同构成合同；候选 1（K4）执行信封及 2026-09-15 追加已逐字入账；R2@K4 PASS_WITH_NOTES 与候选1 UNITY_NA 正式附议已于2026-09-18由接受侧消费，K4候选1验收通过；F2/F3非阻断记债OPEN；候选2（K3）2026-09-18已授权，云端单张RTX 5090、累计≤8 GPU·h、GPU租金≤6美元，AC-12已判NOT_RUN(SFT_003_NOT_DONE)，C1@K3退回实现、K3 C/R=1/0且唯一核对退回已用，工作项未DONE；设计退修计数保持 2，D1/D2 裁定原文保留）
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（Claude Code `/fable`，Fable 池）
Created: 2026-09-12
Last updated: 2026-09-18

> 承接 `COORD-010` §5 第二步「按短板做数据适配/微调」。**来历**：用户 2026-09-12 把原 `P1-ENG-SFT-001` 拆为数据件（001）与训练件（002）；
> 2026-09-13 关闭 001（`CLOSED_BY_USER`，零实现）、暂停 003、恢复 002，并选择「数据合同并入 002 自带」（账本同日三条：「用户关闭 SFT-001、
> 继续 SFT-003」「用户指示暂停 003、恢复 002」「数据合同并入 002 自带」）。本稿 §3 Part A 逐字承接 001 D3 修订 1 的数据合同并闭合接受侧
> 对 001 的 AD3-1…3（见「AD3 → 本稿」）；Part B 是训练与云端执行。已定方向（账本 2026-09-12「方向四项定局」「训练线方向讨论四项定局」）：
> 训练一律只用 Unity；训练目标 = 三态协议，九类词表只在 prompt 中给出、不作训练目标；训练集构成由零样本探针失误画像驱动；已绑定的
> 红色目标车作为 `car` 候选入域；学生 `Qwen/Qwen3-VL-2B-Instruct`，算力 = 直接租云 GPU（LoRA）。SynDrone 跨环境评估依赖
> `P1-ENG-SFT-003`（已由用户暂停，条件分支见表 L）。D3 已 `ACCEPTED`，`Workflow: engineering-v1` 经接受角色裁定生效；§5 仍为申请值，
> 执行信封另由用户逐字授权。`P1-VLM-DIST-001` 保持延期，本项不主张教师增量；不接入运行时（闭环接入另立）。
> **AD3 → 本稿**：AD3-1 → 表 D 全部组（含 G4 与 legacy 优先纳入、405 行守恒）与 §8 表 1/表 4 出自同一次试选（610 行、并集 3,968 帧、逐张
> SHA 绑定）；AD3-2 → 表 E：E5 none 按固定类别顺序逐类轮转、试选与正文同一算法，350 只限 unique 配额（class+color 合计），歧义样本受
> E4/E6 控制并单列 `has_dynamic_target`；AD3-3 → 表 A′ 在 Unity 适配层实现「未绑定 / 缺框 / 裁剪后退化」整帧通配（试选：目标在场
> 10,364 帧中缺框 0），AC-2 具名边界用例。
> **AR1 → 本稿（D2，2026-09-13）**：AR1-1 → §1 训练池口径（train∪dev 七族减 `detect-scout1`，表 E1）、表 D′ 取样常量与函数、§8 表 6a/6b 实测与投影分列、
> `data/`/`upload/`/`panel/` 分根计额；AR1-2 → 表 K 云端包闭集与生成先后、`PACKAGE_INCOMPLETE`（token 预检的 D2 写法已被 D3 的本地 tokenizer 预检取代）；
> AR1-3 → 表 J 与 AC-14（用户逐字「用户只看 ≤24 张」）；AR1-4 → 表 L 与 AC-12 重写（用户逐字「我倾向于不等」）。AD3 主要修正与已核对的行数/帧绑定不变。
> **AR2 → 本稿（D3，2026-09-13；用户处置 (a)）**：AR2-1 → 表 D′ 的 G3′ 键改回 `surface`（与 d5 一致，不改评估定义）、并列次序补 `noun_type, surface`
> （复现 d5 的隐式追加次序）；表 C `station_key` 实取 S3 `station_bin.key`、浮点原值口径、新增包内 `frame_path`；§8 表 6c 为 d7 全字段实测（T7 已挂载，
> 含 609 行评估集与 `legacy_probe[]`），并更正评估行数：LEGACY_ONLY 9 条 legacy 行落在 **8** 个评估行（一对重复键），故评估集 = 601 + 8 = **609** 行，
> D2 的「610」系按 legacy 行数计数；d5/d6/d7 数字各带来源标签、不回写。AR2-2 → 删除两例外推：表 H 改为本地同版 tokenizer 对全部 gold 逐条实测的
> 预检收据（tokenizer 四文件 ≈ 12 MB 下载列入候选 1 申请信封）+ 云端对上云的训练/冒烟 gold 重算并比对（`TOKENIZER_MISMATCH`）；评估 gold 不上云。
> AR2-3 → 表 K 拆为 K4 数据包（帧、数据、清单、收据；`smoke.jsonl` 由 `build` 产出；**不含代码**）与 K3 代码束（`code-manifest.json`）；盲行与 sample 的
> `frame_path` 在 `build` 时即写定为包内路径，打包不改任何 jsonl 字节并记运输映射；AC-5（K4）/AC-7（K3）证据时点分列；表 C 的 upload 行改引表 K。
> 接受侧认定项同步：§7 K4 = AC-1…6 + AC-14；表 J 冻结前提改为用户份额判定齐全（`AUDIT_INCOMPLETE`）；表 H base 行网格断言限定 Unity。

## 0. 动机（构思侧只读复算，单模型、单次 greedy、未经复核，只作动机）

探针 `UT-OFFLINE-PROBE-2026-09-12`（405 行 / 279 帧，test）复算：命中 gold 276（68.1%）；框到其他类别的车 65（16.0%）；框到同类
另一辆 28（6.9%）；松框/部分重叠/无车/无效 36。有限假设：H1 类别词分类学不对齐是主要损失（car 45%、pickup 52%、truck 68%、suv 71%），
且它是环境特定的标签约定，故不作训练目标、只在 prompt 中定义并监测退化；H2 严格歧义 23 行报告 0 次，零样本不会输出歧义状态，是闭环
合同所需的显式状态（`P1-ENG-ASSET-001` 报告 §5 G-1/G-4），是本项首要目标；H3 关系 64% 只评测；H4 S 层 47% 与 32 px/token 有关，
只保留样本、不主张改善。定位本身不是瓶颈（框落在某辆车上 87–94%）。以上不是训练能力上限。

## 1. 目的与价值

1. **数据合同（K4）**：三态标签算法在执行域上逐指令派生（`unique` / `ambiguous` / `none`），训练与评估同一函数；训练集（S4 train∪dev 七族中
   除 `detect-scout1` 外的六族，闭集见表 E1）构成由失误画像驱动；选层集 = `detect-scout1`；冻结评估集（S4 test，探针同款去重，legacy 405 行逐行守恒，
   目标车子组单列）；prompt v2 逐字（词表段可替换）、严格解析器、评分器与判定脚本；盲文件与云端包清单。零模型。
2. **训练与评估（K3）**：LoRA 微调 Qwen3-VL-2B，回答 (a) 微调能否让模型输出三态协议（严格歧义报告、none、误报率）；(b) 词表只由
   prompt 给定时，选框成功率对 prompt v2 零样本是否非劣（退化监测）；(c) 若 003 恢复，只用 Unity 训练的协议行为在 SynDrone 上零样本
   是否同向改善且定位不退化（可迁移性，合成到合成，必要非充分）。
3. 交付可复现的构建器、训练脚本、云端运行器、回传校验、adapter manifest、摘要与报告。

不证明闭环接管行为，不主张教师增量、跟踪性能、真实航拍或 Jetson 性能。

## 2. 范围与不做的事

**候选 1（K4，零 GPU、零模型运行）：**

| # | 交付 |
|---|---|
| 1 | `tools/eng_sft/receipts.py`、`adapters/unity_s3.py`（S3 行 → 统一对象记录，含规则 ① 与 AD3-3 通配）、`three_state.py`、`build_sft_data.py`（对账、三态、训练/选层/评估集、legacy 守恒、泄漏断言、盲文件、云端包清单、冻结收据） |
| 2 | `tools/eng_sft/prompt_v2.py`（词表段可替换）、`parse.py`、`evaluate.py`（表 B/F/G）；全部无模型夹具测试 |
| 3 | 受版本控制冻结工件：`docs/evidence/P1-ENG-SFT-002-{dataset-manifest,eval-manifest,leakage-report,legacy-conservation}.json` |
| 4 | 本地：`train.jsonl`、`smoke.jsonl`（表 H 冒烟 32 条，`build` 产出）、`select.jsonl`、`select-eval.jsonl`(+`.blind`)、`eval.jsonl`(+`.blind`)、`legacy/`、`receipts/`（含 tokenizer 预检收据）、`upload/`（表 K 的 K4 数据包与 `upload/manifest.json`）；tokenizer 四文件存 `outputs/eng-sft/tokenizer/<revision>/`（≈ 12 MB，候选 1 信封下载项） |
| 5 | 数据报告 `docs/evidence/P1-ENG-SFT-002-data-report.md`（计数、守恒、泄漏、seen、字节、失误画像对照；无模型结果） |
| 5′ | 标签语义抽查（表 J）：`tools/eng_sft/label_audit.py`（分层抽样、叠框面板、面板收据、ASSET-001 同帧同标签交集表、`AUDIT_FINDING_OPEN` 收据）、`docs/evidence/P1-ENG-SFT-002-label-audit.md`（抽样参数、分层实取、面板清单、用户判定统计、实现者预筛表；不复制用户判定原文）；用户判定原文由接受/辅助角色代录 `docs/unity-test-log.md` 条目 `UT-P1-ENG-SFT-002-label-audit` |

**候选 2（K3，全部模型执行在候选 1 最终通过轮之后）：**

| # | 交付 |
|---|---|
| 6 | `tools/eng_sft/train_lora.py`（表 H 配方、冒烟、三配置）、`cloud_runner.py`（`bundle` 代码束与 `code-manifest.json`、`verify` 两份清单与冻结链核对、tokenizer 复核、零样本对照、训练、盲预测、作业收据）、`verify_return.py`；无 GPU 单元测试 |
| 7 | 云端作业（用户自跑）：作业 A = 数据包与代码束校验（表 K ⑦）→ tokenizer 复核（表 H）→ 零样本对照（Unity 盲评估集；SynDrone 盲评估集仅当表 L 前置与兼容条件成立）→ 冒烟 → C1/C2/C3 训练 → 三个 adapter 各在盲选层子集预测；本地 = 回传校验 → 评分选优；作业 B = 被选 adapter 在 Unity 盲评估集（及 SynDrone，同上条件）预测一次；本地 = 评分、表 G 判定 |
| 8 | 回传工件（本地 `returned/<job_id>/`）、adapter manifest、`docs/evidence/P1-ENG-SFT-002-{zero-shot-v2-summary,train-summary,eval-summary}.json`、`tests.log` |
| 9 | 报告 `docs/evidence/P1-ENG-SFT-002-report.md`：三个问题的直接回答、表 G 四层状态、目标车子组、分层表、失败案例（每组 min(10, n)）、v1 诊断附表、（条件）跨环境对照、模型/数据来源与许可、费用与 GPU·h 账目 |

**不做的事（闭集）：** 不训练关系指令（G4 只评测）；不改 gold 框合同、不修 S5 颜色、不回写 #27；不重新划分 S4、不退役旧 test，test 与
`unassigned` 任何帧不进训练或选层；不用 SynDrone 或任何非 Unity 数据训练；不用云端 LLM API；不做教师语言、Tier-2、四臂；不换学生（4B
训练不进 8 GB，Qwen2.5-VL-3B 是 Research 许可）；不量化、不做 Jetson；不处理小目标、不做候选选择器；不接入 `controller/`；不采集、
不 Play、不创建 scenario/session/run/attempt 身份；不发布（K5 另立）；不新增第四种输出状态；不做相同车辆身份分辨；不为 AC-12 等待 003（前置不成立即 `NOT_RUN` 终态）；本地只下载 tokenizer 四文件（≈ 12 MB，候选 1 信封）、不下载权重。

## 3. 接口与数据契约

### Part A 数据合同（承接 001 D3 修订 1）

**输入闭集（只读；身份一律运行时解析并记入输入清单，不手写 SHA；任一不符即只写失败收据）**

| 输入 | 身份来源 | 用途 |
|---|---|---|
| S0 `contract@attempt-2/contract.json` | S3 manifest `inputs` 链 | 词表/关系闭集常量核对 |
| S3 `frames_catalog@attempt-2`：`frames_catalog.json` + `shards/*.ndjson.gz`（151 片） | manifest 逐片 `lines`/`compressed_bytes`/SHA | 逐帧对象状态、`blocking`/`referable`、框、`target_blocker_px`、`target_source_bound`、族、站位 |
| S4 `splits@attempt-2/splits.json`（`shards/` 7 片只做 SHA 核对） | 文件 SHA 现算 | `frame_id → split` |
| S5 `field_catalog@attempt-2/field_catalog.json` | 文件 SHA 现算，并与探针清单 `source.field_catalog_sha256` 相等 | 类别/颜色验证状态 |
| S1 `inventory@attempt-2/inventory.json` 的 `records[]`（`kind ≠ truth`） | 文件 SHA 现算；每条 `path/sha256/bytes` | 帧图像绑定核验 |
| 帧 JPEG（动态成员 = 各集合 manifest 列出的帧） | 逐张 SHA 对 S1 记录 | 训练/评估图像 |
| `runtime/eng-asset/P1-ENG-ASSET-001/instructions.ndjson.gz` | SHA 现算，并与探针清单 `source.instructions_sha256` 相等 | AC-1 旧七值对账参照；G4 的 `UNIQUE_RELATION` 行来源 |
| `docs/evidence/P1-ENG-ASSET-001-instructions-summary.json` | 受版本控制 | 七值直方图相等断言 |
| 探针 `probe/manifest-default.json`、`predictions.jsonl`（T7 → 本地 `legacy/`） | 首次读取现算 SHA；报告列出供与 Unity 日志前缀比对 | legacy 405 行守恒；v1 诊断附表 |
| **不读取**：`layout@attempt-2`、帧 sidecar、真值文件、`runtime/` 其他内容 | — | — |

**复用的既有函数（不改）：** `build_catalog.frame_world(entry, field_catalog)`（S7 调用形态；执行域 = `blocking(f)`）、
`tier1_lang._noun_conflicts`、`tier1_lang._noun_satisfies`、`SceneObject.referable`、`tier1_lang.execute` + `hits_expected_target`
（G4）、`tier1_lang.render`；`tools/eng_asset/inventory.classify_uniqueness`（只用于 AC-1 旧七值对账）。

**表 A 三态派生（`three_state(objects, noun)`，输入为适配器产出的统一对象记录）**

令 D = 执行域对象集合，C = {o ∈ D : `_noun_conflicts(o, noun)`}，M₀ = {o ∈ C : `o.referable` ∧ `_noun_satisfies(o, noun)`}。
**规则 ①**：若 `dynamic-target` ∈ C 且适配器标记其 `definite = true`（见表 A′）且 `_noun_satisfies(dynamic-target, noun)`（noun 为 `{car}`
或 `{car, red}`），则 M = M₀ ∪ {dynamic-target}；否则 M = M₀。按序、互斥：

| 序 | 状态 | 条件 | 目标 |
|---|---|---|---|
| 1 | `none` | C = ∅ | 无框 |
| 2 | `unique` | C = M ∧ \|M\| = 1 | M 的唯一对象框 |
| 3 | `ambiguous` | C = M ∧ 2 ≤ \|M\| ≤ 4 | M 全部对象框，按 (x1, y1, x2, y2) 升序 |
| 4 | `gray_overflow` | C = M ∧ \|M\| ≥ 5 | 排除（计数披露） |
| 5 | `gray_definite_plus_uncertain` | \|M\| ≥ 1 ∧ C ≠ M | 排除训练；评估 G3′（诊断，无门） |
| 6 | `gray_uncertain_none` | M = ∅ ∧ C ≠ ∅ | 排除（不确证不存在，不标 none） |

规则 ① 与 `P1-VLM-DATA-001` BC-DATA-8.3/9（动态目标永不可作 target/ref）**不同**：那是研究指称唯一性合同；本项是工程数据合同，把已绑定
且框有效的目标车视为可框选的 `car` 候选，其框与其他 gold 同源（真值投影）。不改上游函数。

**表 A′ 闭集逐项处置（Unity 适配器 `adapters/unity_s3.py` 负责把 S3 行转成统一对象记录）**

| 情形 | 适配器输出 | 效果 |
|---|---|---|
| 该类 0 / 1 / ≥2 个 `OK` 目录车 | 目录对象，referable=True，class_word 已验证 | none（若无其他可能匹配）/ unique / ambiguous |
| 同类非 OK（`TRUNCATED`/`TOO_SMALL`/`EXCLUDED_OCCLUDED`，可见面积 > 0） | 目录对象，referable=False | ∈ C 而 ∉ M → 灰区 |
| 未知类别阻断体（8 辆无 S5 条目车）/ 类别未验证 | class_word=None | 全帧 noun 灰区 |
| 同类 phantom | class_word 已知、color_word=None、referable=False | class noun 灰区；异类 phantom 无影响 |
| 动态目标在视野内、`target_source_bound` 且 `target_blocker_px` 裁剪到画幅后正面积 | `dynamic-target`：class `car`、color `red`、`definite=true`、框 = 裁剪后归一化 | 规则 ①：`car`/`red car` 的确证候选（unique 目标或 ambiguous 候选）；对其他类 noun 无影响 |
| 动态目标在视野内、未绑定 **或** 缺框 **或** 裁剪后退化（AD3-3） | 适配器把该帧标记 `frame_wildcard=true`：该帧**不产生任何 noun 的样本**（全部视为灰区），不依赖上游 `frame_world` 的字段赋值 | 整帧排除；计数披露（试选：0 / 10,364） |
| 动态目标不在视野内 | ∉ D | 无影响 |
| 颜色未验证 | color_word=None | class noun 不受影响；color noun 灰区 |
| 已知颜色反例 #27（`Vehicle_Bus_color03`） | 对象在 D 中 | 该帧全部 `bus` 的 color noun 排除（训练与评估）；不回写 S5 |

noun 枚举：每帧九个 class noun；color noun 对帧内存在 `OK` 且颜色 `VERIFIED` 的 (class, color) 组合与（规则 ① 成立时）`(car, red)` 枚举；
color unique 记 `color_required`（= 该 class noun 非 unique），评估 G2 只取 `color_required=true`，训练两者都用；不生成 color-none。
与旧七值：`UNIQUE_CLASS` ⇔ unique 且 M = {该对象}（§8 表 2）。G4 = `UNIQUE_RELATION` 行程序在 D 上 `execute` 唯一且命中目标 ⇒ 合法
`unique` 输出，只评测（frame_wildcard 帧同样排除）。gold = S3 `visible_norm_xywh` 或目标车裁剪框。

**表 B prompt v2 与解析（逐字冻结；词表段 `{vocab}` 按数据集替换；构造函数只接受 (图像路径, surface, g4 标志, 词表段名)，结构上不可见 gold）**

- 图像原尺寸；处理器 `size = {"shortest_edge": 65536, "longest_edge": 16777216}`；Unity 640×480 时断言 `image_grid_thw == [1, 30, 40]`。
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

  第三段即词表段 `{vocab}`；G4 追加段（仅 G4 行）：`"to the viewer's left of X" means the described object appears further to the left in the
  image (smaller x) than the object X; "to the viewer's right of X" means further to the right (larger x).`
- 输出闭集：三种 JSON；无 `label`。gold 整数化：`x1 = ⌊x·1000 + 0.5⌋` 等，裁到 [0, 1000]，x2 ≤ x1 则 x2 = x1 + 1（1000 处反向减 1）；候选按
  (x1, y1, x2, y2) 升序。预测 `bbox_2d/1000` 与 gold 浮点框算 IoU。
- gold 序列化（训练标签、冒烟核对与本地评分同一函数 `gold_text(sample)`）：Python `json.dumps` 缺省分隔符（`", "` 与 `": "`）、键序 `status` →
  `bbox_2d` / `candidates`、纯 ASCII；三种骨架逐字：`{"status": "none"}`、`{"status": "unique", "bbox_2d": [x1, y1, x2, y2]}`、
  `{"status": "ambiguous", "candidates": [{"bbox_2d": [x1, y1, x2, y2]}, ...]}`（候选 2…4，按 (x1, y1, x2, y2) 升序）；实测长度见 §8 表 6a。
- 解析器（fail-closed）：去 fence 并计数 → JSON → `status` 闭集 → 框长度 4、整数、0–1000、`x1<x2 ∧ y1<y2` → `candidates` 2…8；`parse_error`
  闭集 {`JSON_ERROR`, `SCHEMA_ERROR`, `RANGE_ERROR`, `ORDER_ERROR`, `TRUNCATED`}；**任一 `parse_error ≠ null` 即 `status_pred = null`**（原始
  status 只存 `raw_status`）；记录 `gen_tokens`、`finish_reason`、`prompt_sha256`、`image_grid_thw`。

**表 C 派生工件 schema（`p1-eng-sft-002/<name>/v1`；每件记录来源文件的运行时 SHA）**

| 工件 | 必含字段 |
|---|---|
| 统一对象记录 | `object_id, class_word（None=未知）, color_word（None=未验证）, referable, status, visible_norm_xywh, definite（仅 dynamic-target）`；帧级 `frame_wildcard` |
| `sample` | `sample_id, frame_id, frame_path, frame_sha256, split, family, station_key, frame_index, noun_type ∈ {class, color}, surface, noun, state, color_required, target_object_ids[], target_boxes_norm_xywh[], target_bbox_2d_1000[], stratum ∈ {S, M, L, NA}, thin_key, has_dynamic_target, oversample_copies`；`sample_id = "s-" + sha256(seed|frame_id|surface)[:16]`；`frame_id` = S3 原路径，`frame_path = frames/<frame_sha256>.jpg`（包内路径，`build` 时写定）；`station_key` = S3 `station_bin.key`（如 `66:58:8:1`）；`target_boxes_norm_xywh` = S3 `visible_norm_xywh`（目标车为裁剪归一化框）**原值**，按 Python `json.dumps` 缺省（`float.__repr__` 最短往返表示）写出、不四舍五入，`target_bbox_2d_1000` 与 `gold_text` 从同一原值计算；`stratum`/`thin_key` 按表 D′；`gold_text` 现算不落字段；d7 实测单行 ≤ 1,108 B（§8 表 6c） |
| `eval-row` | `row_id（= "<group>-" + sha256(seed|frame_id|surface)[:16]）, frame_id, frame_path, frame_sha256, family, frame_index, station_key, group ∈ {G1, G1t, G2, G2t, G3, G3t, G3p, G4, G5, LEGACY_ONLY}, gate_row（仅 G1/G2/G3/G5 为 true）, surface, noun 或 relation_program, gold_state ∈ {unique, ambiguous, none, null}, diagnostic ∈ {GRAY_DEFINITE_PLUS_UNCERTAIN, LEGACY_ONLY_DEDUPE_EXCLUDED, null}, definite_ids[], target_object_ids[], gold_boxes_norm_xywh[]（原值口径同 sample）, gold_bbox_2d_1000[], stratum ∈ {S, M, L, NA}, gold_text_len（`gold_state ≠ null` 时的 gold 字符长度，否则 null）, has_dynamic_target, color_required, seen_target, seen_candidates[], seen_all, legacy_probe[]`（每条 `{row_id, group_v1, object_id_v1, gold_v1_xywh, same_class_visible_v1}`；重复键的 2 条 legacy 行挂在同一评估行）；d7 实测单行 ≤ 1,644 B |
| `blind-row`（云端用） | `row_id, frame_path, surface, g4, vocab`——无 gold 字段；`frame_path` 与同 `row_id` 的 eval-row / sample 相同（包内路径，`build` 时写定，打包不改写）；盲文件行数与 manifest 相等 |
| `legacy-conservation` | 405 条：`{row_id, group_v1, frame_path（S3 原路径）, surface, new_state, eval_row_id, group, disposition ∈ {ADMITTED, LEGACY_ONLY}}`；`eval_row_id` 指向 gate/诊断行或同名 `LEGACY_ONLY` 评估行（重复键 2 条指向同一行），不为 null；Σ = 405 |
| `dataset-manifest` / `eval-manifest` | 只含内容：行数、状态/组/类别计数、规则常量与实取（表 E 各步）、jsonl 与盲文件行数与 SHA、帧集合数量与总字节；不含自身/提交 SHA |
| `freeze` 收据（本地，提交后生成） | HEAD、冻结闭集文件（四份 JSON + `prompt_v2.py`/`parse.py`/`evaluate.py`/`three_state.py`）的跟踪/干净状态与 SHA、jsonl/盲文件 SHA |
| `upload/manifest.json` / `upload/code-manifest.json` | 见表 K（K4 数据包清单与 K3 代码束清单；本表不另列，避免两处定义） |
| `prediction`（云端产出，本地评分追加） | `row_id, model_id（base revision 或 adapter sha256）, prompt_sha256, image_grid_thw, raw_output, fence_stripped, raw_status, parsed, parse_error, status_pred, gen_tokens, finish_reason, latency_ms` + 评分字段 |
| `job-receipt`（云端）/ `adapter` manifest | 见 Part B 表 I |

**表 D′ 取样常量与函数（AR1-1；实现者逐字实现，试选与本表同一算法；`seed = tdt-eng-sft-002-2026-09-13`）**

| 项 | 定义 |
|---|---|
| 目标短边 `px` | 样本全部目标框（unique 1 框；ambiguous = M 全部候选框；G3′ = M 的框；G4 = 目标框）各取 `min(w·640, h·480)` 后再取**最小值**（最小候选短边）；none 与无框样本 `px = null` |
| 层 `stratum` | `px < 32` → `S`；`32 ≤ px < 64` → `M`；`px ≥ 64` → `L`；`px = null` → `NA`（none 行的无框层；只出现在 G5 与训练/选层 none） |
| 键 `key(s)` | unique → 目标 `object_id`（class 与 color unique 同此；目标车即 `dynamic-target`）；ambiguous → 候选 `object_id` 升序以 `\|` 连接；none → `surface`（如 `the taxi`）；G3′ → `surface`（与 d5 `keyf` 一致，D2 曾误写为 M 串，D3 改回，不改评估定义）；G4 → 目标 `object_id` |
| 哈希序 `h(s)` | `sha256(UTF-8(seed + "\|" + frame_id + "\|" + key(s)))` 十六进制字符串升序；`frame_id` = S3 `frame_id` 原文（`runtime/...jpg` 路径）；并列再按 `(frame_id, key, noun_type, surface)` 字符串升序——实现为 `sort(key=(h, frame_id, key, noun_type, surface))`；并列只发生在同帧同对象的 class/color unique 之间（`noun_type` 字典序 class < color 复现 d5 逐帧先 class 后 color 的追加次序，d7 已核实计数不变）；表 D/E 全部「哈希序」均指此序 |
| 帧序号 `idx` | `frame_id` 尾部 `frame_(\d+).jpg` 的整数 |
| E2 稀疏（训练池与选层集各自执行） | 按 `(family, state, noun_type, key, idx)` 升序遍历；对每个 `(family, state, noun_type, key)` 记录上一个**被保留**的 `idx`（初值 −∞），当前 `idx − last ≥ gap` 才保留并更新 last；`gap`：ambiguous 2；none 5；unique 且（类别 ∈ {car, pickup truck, truck, suv} 或 `px < 32`）2，其余 unique 5 |
| E5 轮转 | 九类队列各按 `h(s)` 升序；按类别名字典序固定顺序逐类各取一条轮转，某类取满 ⌈N_none/9⌉ 或队列耗尽即跳过，直到取满 N_none 或全部耗尽（不足额不回填） |
| 评估准入 `admit(row)` | 准入键 `(group, key(s)（none 取 surface）, family)`；条件：该键已准入行数 < 4 **且** 与该键**全部**已准入行的 `\|idx − idx′\| ≥ 30`；G5 另加每类别 ≤ 12；不满足即拒绝、不回填 |
| legacy 优先内次序 | 每组先处理有 legacy 匹配（`(frame_id, surface)` 与探针清单行相等，可对应多条 legacy 行）的样本，按其 legacy `row_id` 集合的最小值字符串升序逐个 `admit`；准入 → 该样本全部 legacy 行 `ADMITTED`，拒绝 → 全部 `LEGACY_ONLY`；守恒表逐 legacy 行记原 group/gold |
| 层轮转 | legacy 之后的候选按层分桶，桶内 `h(s)` 升序；按 `S → M → L → NA` 固定顺序逐层各取一行轮转（空层跳过），每取一行即 `admit`，直到配额满（仅 G3′ 50 / G5 100）或全部桶耗尽；无配额组取尽全部可准入行 |
| 试选实现 | 构思 scratchpad `sft_d5_dryrun.py`（并入版）、`sft_d6_measure.py`（D2 临时表示）与 `sft_d7_measure.py`（D3 全字段，本表口径）只供定位，不是冻结工件；生产实现须使本表与 §8 表 1/4/5/6c 数字逐项复现（AC-2/AC-3） |

**表 D 冻结评估集（S4 test；去重与探针逐字相同：每 (组, 键, 族) 帧序号间隔 ≥ 30、≤ 4 张；键 = 目标对象 / 候选集串 / 类别；目标车键 =
`dynamic-target`；legacy 行按新状态先行纳入并逐 row_id 守恒；配额 = 去重后全部可得，只有 G3′/G5 封顶；AD3-1：下表实取与 §8 表 1 出自同一次试选）**

| 组 | 定义 | 试选实取 | 其中 legacy 行 | 指标 |
|---|---|---|---|---|
| G1 | class noun `unique`，目标为目录车 | 210 | 210 | Success、误报歧义率、误报 none 率、无效率 |
| G1t | class noun `unique`，目标为目标车 | 23 | 0 | 同上，单列 |
| G2 | color noun `unique` ∧ `color_required`，目录车 | 49 | 49 | 同 G1 |
| G2t | `the red car` unique，目标车（不要求 `color_required`；试选 23 行与 G1t 同帧同层，只报告） | 23 | 0 | 同上，单列 |
| G3 | class noun `ambiguous`，候选不含目标车 | 48 | 12（11 个评估行） | 报告率、集合 F1、严格成功 |
| G3t | class noun `ambiguous`，候选含目标车 | 12 | 2 | 同上，单列 |
| G3′ | class noun `gray_definite_plus_uncertain` | 50（封顶） | 37 | 诊断，无门 |
| G4 | `UNIQUE_RELATION` 行 | 86 | 86 | Success（须 status=unique） |
| G5 | class noun `none`（层 = `NA`） | 100（每类 ≤ 12） | 0 | none 率 |
| LEGACY_ONLY | 旧行新状态合法但被去重排除的评估行（进盲文件，只进 v1 诊断附表） | 8 行（承载 9 条 legacy 行；其中 1 行为重复键 2 条） | 9 | 只进 v1 诊断附表 |

合计 601 gate/诊断行 + 8 LEGACY_ONLY 评估行 = **609** 行（D2 写 610 系按 legacy 行数计数，d7 核实更正）；405 行守恒 = ADMITTED G1 210 / G2 49 / G3 12 / G3t 2 / G3′ 37 / G4 86（396）+ LEGACY_ONLY 9，不变。
排序与准入：表 D′（legacy 优先 → `S → M → L → NA` 层轮转，层内 `h(s)` 升序，seed `tdt-eng-sft-002-2026-09-13`）。功能门（表 G）在 G1∪G2、G3、G5 上计算；
`t` 子组只报告，不入门。

**表 E 训练集与选层集（确定顺序；试选与正文同一算法；AD3-2 已闭合）**

| 步 | 规则 | 试选实取 |
|---|---|---|
| E1 | 训练池 = S4 `train ∪ dev` 七族的三态样本（frame_wildcard 帧除外）：train = `p1-vlm-survey-a2-p1-c1-s1`（2,523 帧）；dev = `detect-scout1`（768）、`m3-armA`（896）、`p1-vlm-survey-a1-p1-c1-s2`（2,916）、`p1-vlm-survey-a7-p1-c1-s1`（3,168）、`rate`（5,140）、`scene-val`（256）。选层集 = `detect-scout1` 整族；训练子集 = 其余六族（闭集 = 上列去掉 `detect-scout1`）；test 与 `unassigned` 零帧 | 稀疏前池按族：a2 12,330 / m3-armA 3,889 / a1 19,250 / a7 22,255 / rate 34,416 / scene-val 2,560 / detect-scout1 4,796 样本；选层稀疏后 unique 925、ambiguous 41、none 504 |
| E2 | 稀疏（每 (族, 状态, noun_type, 键) 帧序号间隔，算法/键/层按表 D′）：`ambiguous` 2；`unique` 且（类别 ∈ 弱类 {car, pickup truck, truck, suv} 或 S 层）2，其余 5；`none` 5 | 训练稀疏后 unique 8,991、ambiguous 466、none 11,202；逐族 (unique/ambiguous/none)：a2 1,299/203/1,990、m3-armA 694/0/185、a1 2,143/103/2,906、a7 2,613/160/3,306、rate 1,934/0/2,451、scene-val 308/0/364 |
| E3 | **unique 配额**（class + color unique 合计）：每类 ≤ 700（哈希序），同一对象在类内 ≤ 350 | 4,006：car 517（目标车 350 + 目录车 167）、container truck 700、pickup truck 700、suv 700、taxi 400、bus 334、ambulance 285、truck 272、police car 98 |
| E4 | ambiguous 每候选集键 ≤ 60（哈希序）；不受 E3 的 350 约束 | 411（truck 180、car 90、pickup 75、container 28、police 18、taxi 16、suv 4；含目标车 65） |
| E5 | none 取数 N_none = ⌊0.10 · (\|U\| + \|A\|) / 0.90⌋；按类别名字典序（ambulance, bus, car, container truck, pickup truck, police car, suv, taxi, truck）固定顺序逐类轮转（表 D′），每类队列按哈希序，每类 ≤ ⌈N_none/9⌉；实取 \|N\| ≤ N_none，不足额不回填 | 490（55/55/55/55/54/54/54/54/54）= N_none |
| E6 | 复制系数 k = 最小整数 k ≥ 1 使 k·\|A\| ≥ 0.15 · (\|U\| + \|N\| + k·\|A\|)，上限 8（等价于 min(8, ⌈0.15 · (\|U\| + \|N\|) / (0.85 · \|A\|)⌉)，\|N\| 取 E5 实取），写入 manifest，训练加载时复制 | k = 2（份额 15.5%） |
| E7 | 最终训练多重集 = U + none_kept + k × A；优化器实际见过的帧 = distinct 帧 | 5,318 样本 / 3,198 帧 / 143.2 MB |
| E8 | 选层评估子集 = 选层集全部 ambiguous + 哈希序 unique min(300, 可得) + none 100，不重复取样 | 41 + 300 + 100 = 441 行 / 322 帧 |
| E9 | seen：对象在优化器实际见过的帧的执行域中出现即 seen | 76 个对象（含 `dynamic-target`） |

**表 F 评分（`evaluate.py`；分母 = 该组 manifest 全部 gate 行，任何失败不剔除）**

| 项 | 规则 |
|---|---|
| 预测文件有效性 | 行集合与 manifest 一一对应：缺行 / 重复 `row_id` / 多余行 → 整次 `PREDICTIONS_INCOMPLETE`，不评分 |
| G1/G1t/G2/G2t/G4 Success | `status_pred = unique` ∧ IoU ≥ 0.5；其他状态或 null 均失败；误报歧义率、误报 none 率、无效率分列 |
| G3/G3t | 报告率；IoU ≥ 0.5 边上的最大基数一对一匹配（≤ 4 × ≤ 8，穷举）；TP/FP/FN、F1；严格成功 = 报告 ∧ F1 = 1 |
| G5 | none 率 |
| G3′ | 诊断：报告率；status_pred=unique 时任一 M 命中率 |
| 分层 | S/M/L、seen/unseen、类别 |
| 配对差 | G1∪G2 同一行域（259 行）：d = mean(success_A − success_B)；bootstrap 行级 B = 2,000、seed 20260912、百分位 2.5/97.5；描述性 |
| v1 诊断附表 | 405 行（含 LEGACY_ONLY）v1 输出映射三态后配对；只报告 |

**表 G 判定（D3 接受时冻结；工程描述性判定）**

| 层 | 规则 |
|---|---|
| 功能门 | (a) G3 报告率 ≥ 0.70 且严格成功 ≥ 0.50；(b) G1∪G2 误报歧义率 ≤ 0.10 且误报 none 率 ≤ 0.05；(c) G5 none 率 ≥ 0.80 → `GATE_MET` / `GATE_NOT_MET` |
| 词表非劣（退化监测） | (d) G1∪G2 配对差点估计（微调 − prompt v2 零样本）≥ −2.0 pp → `NON_INFERIOR` / `INFERIOR`；CI 只披露 |
| 目标车子组与增量 | G1t/G2t/G3t 与逐组配对差、seen/unseen 分列；描述性 |
| 跨环境（条件） | 按表 L：前置（`P1-ENG-SFT-003` 于候选 2 执行授权前 `DONE`）与兼容条件 (1)–(6) 全部成立才运行；逐项配对指标 m1–m6、迁移比零/小分母 `NA` 规则与机械判定 `TRANSFER_OBSERVED` / `NOT_OBSERVED` / `NOT_RUN(<原因>)`；描述性，不入功能门 |
| 完成状态 | 交付 + 独立复核 + `UNITY_NA` 附议 → `DONE`；`GATE_NOT_MET`/`INFERIOR` 是评估事实，不阻止 DONE，不自动追加 run |

**表 J 派生标签语义抽查（K4；engineering-workflow §7 与完整性核验互补；用户 2026-09-13 逐字「用户只看 ≤24 张」，账本同日条目）**

| 项 | 规则 |
|---|---|
| 抽样域 | 冻结前的最终集合：训练多重集（distinct 样本）∪ 选层评估子集 ∪ 评估集 gate 行；G3′ / LEGACY_ONLY 不抽 |
| 风险层与配额（用户判定行 / 实现者预筛行） | J1 class unique：4 / 8（弱类 {car, pickup truck, truck, suv} 各 ≥ 1 张进入用户份额）；J2 color unique（`color_required = true` 优先）：3 / 4；J3 class ambiguous 候选集完整：4 / 8（候选数 3–4 优先，≥ 1 张含目标车）；J4 none：4 / 8（每类 ≤ 1，用户 4 张覆盖 4 个不同类别）；J5 目标车 unique（G1t/G2t 或训练 `has_dynamic_target` unique）：3 / 4；J6 G4 关系行：3 / 4；J7 #27 排除帧（`Vehicle_Bus_color03` 在场且 `bus` 颜色指令已排除）：2 / 0。合计用户 ≤ 23 行（申请上限 24 张唯一图片）、实现者预筛 ≤ 36 行；每行一张唯一图片 |
| 抽样方法 | 每层在其抽样域内按 `h(s)`（表 D′，seed 同）升序取样；同一 `object_id`（none 取 surface）每层 ≤ 1 行、同一帧全局 ≤ 1 行；用户份额先取、预筛份额续取；层不足额时留空并披露，不回填 |
| 面板 | 沿 ASSET-001 面板形态：原帧完整不裁剪、标题置于帧外、叠加目标/候选框与指令；J3 面板叠加**全部** M 候选框并编号；J4 只显示指令；J7 叠加该 bus 的 S5 颜色字段；`panel-receipt.json` 记 HEAD、样本身份、原图 SHA、叠加图 SHA；面板与原图副本落 `outputs/eng-sft/P1-ENG-SFT-002/panel/`（≤ 20 MB，不计入 64 MB 数据目录） |
| 谁核对原图 | **用户**判定用户份额（≤ 24 张，`OFFLINE_VISUAL_CHECK`，零 Play），原文由接受/辅助角色代录 `docs/unity-test-log.md` 条目 `UT-P1-ENG-SFT-002-label-audit`；**实现角色**对预筛份额看图预筛并把逐行结果写入 label-audit 文件「预筛」表——预筛只作披露，**不计为语义核验**，不改变任何冻结决定 |
| 记录字段（用户判定与预筛同表列） | `panel_index \| 层 \| 状态 对/错/不确定 \| 候选完整 对/错/不确定/NA（仅 J3） \| 颜色 对/错/不确定/NA（仅 J2/J5/J7） \| 关系方向 对/错/不确定/NA（仅 J6） \| 错误类型`（多选闭集 `漏车` / `多车` / `类别错` / `颜色错` / `目标车框错` / `关系方向错` / `框不紧或截断` / `其他`）；「不确定」单列，不计为对；未判定行计 unjudged |
| 复用 ASSET-001 | 生成器计算本次面板 `(frame_id, object_id)` 与 `docs/evidence/P1-ENG-ASSET-001-label-audit.md` 60 张面板的交集，交集行在报告引用其类别/颜色/框判定（具名 panel_index），但**三态状态**仍须本次判定（旧抽查无此项，且不构成 S6 审计） |
| 停止与回合同 | 用户份额任一行未判定（unjudged）→ `AUDIT_INCOMPLETE`，`freeze` 拒绝运行（未判定不等于无错，预筛不替代用户核验）；用户判定出现任一「错」→ `label_audit.py` 写 `AUDIT_FINDING_OPEN` 收据，`freeze` 拒绝运行；实现角色在「待裁定」节逐行列出并给出归因假设（规则缺陷 / 上游标签缺陷 / 面板显示问题），接受角色裁定：(i) 规则缺陷 → 修规则、重建、只对受影响层重新抽样再判（计一次本地构建尝试与一次用户复判）；(ii) 上游标签缺陷（如 #27 类）→ 该帧对应 noun 排除并写入 §6 限制，不回写上游；(iii) 显示问题 → 重绘再判。用户份额判定齐全、全部「错」有裁定且受影响层复判无新「错」后方可冻结；「不确定」不阻止冻结，报告披露计数 |
| 预算（申请，计入候选 1 信封） | 面板生成 ≤ 2 次（每次 ≤ 5 min CPU）；用户判定 1 次（可分段）+ 复判 ≤ 1 次；实现者预筛 ≤ 36 张；代录 1 次 |

### Part B 训练与云端执行

**表 H 训练配方（D3 接受时冻结；候选配置闭集与顺序唯一；执行额度另授权）**

| 项 | 值 |
|---|---|
| base | `Qwen/Qwen3-VL-2B-Instruct`，revision `89644892e4d85e24eaac8bacfd4f463576704203`（探针同版），bf16；Unity 行每张断言 `image_grid_thw == [1, 30, 40]`（SynDrone 行按表 L (4) 用其 manifest 期望值），否则 `IMAGE_GRID_MISMATCH` |
| LoRA | `r = 16, alpha = 32, dropout = 0.05`；目标模块 LLM 各层 `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj`；ViT 与 merger 冻结 |
| 固定项 | cosine、warmup 3%、有效 batch 16、梯度检查点开、seed `20260912`、`max_new_tokens 160`、greedy、batch 1（推理）、损失只算 assistant token；训练多重集按 `oversample_copies` 展开；epoch = 一次完整遍历 |
| 候选配置（按序，≤ 3 run） | C1：epochs 2, lr 1e-4；C2：epochs 3, lr 1e-4；C3：epochs 2, lr 5e-5 |
| 选优 | 盲选层子集（441 行）回传后本地评分：三态状态级 macro 准确率最高者；差 ≤ 0.5 pp 并列 → 优先 epoch 少者，再优先 lr 低者 |
| 正式 adapter | = 被选 run 的 adapter；不重训、不合并选层集 |
| 冒烟 | 32 条 `smoke.jsonl` 由 K4 `build` 产出并入 dataset-manifest：unique class 8 + color 8、ambiguous 8（试选 class 5 + color 3）、none 8，各按表 D′ 哈希序取自训练 distinct 样本；≤ 60 优化步；通过 = 末步 loss < 0.05 且 32/32 greedy 状态正确；否则 `SMOKE_FAILED` 停止回接受角色 |
| token 预检 | **本地预检（K4，`build_sft_data.py precheck`，冻结前）**：用同版 tokenizer 文件（`Qwen/Qwen3-VL-2B-Instruct` revision `8964…4203` 的 `tokenizer.json` / `tokenizer_config.json` / `vocab.json` / `merges.txt`，≈ 12 MB，下载额度列入候选 1 申请信封；不下载权重）对训练 / 冒烟 / 选层 / 评估**全部** `gold_text` 逐条计数（`add_special_tokens=False`，不套模板），max ≤ 152；预检收据绑定四份 gold 文件 SHA、`gold_text` 函数源码 SHA、tokenizer 文件 SHA 与 revision、transformers 版本、计数开关，另测模板固定开销（`<\|im_start\|>assistant\n` 与 `<\|im_end\|>` 的 token 数）写入收据；`gold_state = null` 行无 gold，不进预检、计数披露。**云端复核（K3）**：同版 tokenizer 对包内 `train.jsonl` + `smoke.jsonl` 重算，逐文件计数与 max 须等于本地收据，不等 → `TOKENIZER_MISMATCH` 停止；评估 gold 不上云，其本地收据随冻结收据副本入包。任一 > 152 → `GOLD_TOKEN_OVERFLOW`，不截断、不扩预算；152 只是拒绝阈值。不使用任何外推（字节界或骨架界）；未获 tokenizer 下载授权则预检无法完成，`freeze` 拒绝运行并回接受角色 |
| 中断/失败 | 每次启动计一次尝试；部分预测文件作废不续跑；失败或中断的 GPU 占用计入信封 |

**表 K 云端包闭集、可见字段与生成先后（AR1-2 / AR2-3；K4 数据包与 K3 代码束分列；训练标签上云，选层/评估 gold 永不上云）**

| 项 | 规则 |
|---|---|
| 包根 | 本地 `outputs/eng-sft/P1-ENG-SFT-002/upload/`（独立于 64 MB 数据目录；≤ 0.3 GB，按 §5「上传」项计额；帧为**复制**而非符号链接，使包自含可校验）；用户自行上传到私有云盘/对象存储（不公开） |
| K4 数据包（候选 1，`build_sft_data.py package`，`freeze` 收据存在后） | (a) 帧 JPEG：训练 ∪ 选层评估子集 ∪ 评估（含 LEGACY_ONLY 行帧）并集，`frames/<sha256>.jpg`；(b) `data/train.jsonl`（表 C sample，**含训练标签**）；(c) `data/smoke.jsonl`（32 条，含标签）；(d) `data/select-eval.blind.jsonl`、`data/eval.blind.jsonl`（无 gold）；(e) `manifests/dataset-manifest.json`、`manifests/eval-manifest.json`（无 gold）、`manifests/freeze-receipt.json`、`manifests/precheck-receipt.json`（副本）；(f) `upload/manifest.json`：列出 (a)–(e) **每个**文件的相对路径、字节、SHA-256（帧逐张），不含自身，另记帧运输映射 `frames/<sha>.jpg → 源 frame_id` 与两份 manifest/收据副本 SHA。**不含任何代码**、不含 `select-eval.jsonl` / `eval.jsonl`（gold）、`legacy/`、`legacy-conservation.json`、`leakage-report.json`、`runtime/` 其他内容 |
| K3 代码束（候选 2，`cloud_runner bundle`） | `code/tools/__init__.py`、`code/tools/eng_sft/__init__.py`、`code/tools/eng_sft/{cloud_runner,train_lora,prompt_v2,parse,receipts}.py`、`code/tools/eng_asset/__init__.py`、`code/tools/eng_asset/receipts.py`（`receipts.py` 的唯一仓内依赖，纯标准库）、`code/tools/requirements-eng-sft.txt`；`upload/code-manifest.json` 列出代码束每个文件的路径、字节、SHA 与来源 HEAD，不含自身；表 L 前置成立时另加 `data/syndrone-eval.blind.jsonl`、`manifests/syndrone-eval-manifest.json`、`vocab/syndrone.txt` 与其帧（列入 `manifest.json` 增补段）。**不含** `three_state.py`、`build_sft_data.py`、`evaluate.py`、`label_audit.py` |
| 可见字段 | `train.jsonl` / `smoke.jsonl` 行 = 表 C sample 全字段（gold 由 `gold_text` 现算）；盲行 = `row_id, frame_path, surface, g4, vocab`；两份 manifest 只含计数、常量、jsonl/盲文件 SHA、帧数与字节、序列化字节统计 |
| `frame_path` 与运输映射 | 盲行与 sample 的 `frame_path = frames/<sha256>.jpg` 在 `build` 时写定（SHA 取 S1 记录并逐张核验），`package` 只复制帧字节到该路径、**不改写任何 jsonl**（jsonl 字节 = 冻结收据）；云端读图后现算 SHA 须等于文件名，否则 `PACKAGE_INCOMPLETE` |
| 生成先后与互不自引用 | ① `build` → jsonl（含 `smoke.jsonl`）/盲文件/四份冻结 JSON（manifest 只记 jsonl/盲文件/帧的 SHA，不记自身与提交）；② `precheck` → 本地 tokenizer 预检收据（表 H）；③ 提交冻结闭集（四份 JSON + `three_state.py` / `prompt_v2.py` / `parse.py` / `evaluate.py`）；④ `freeze` → 冻结收据（记 HEAD、冻结闭集各文件 SHA 与 `git ls-files` 版本、jsonl/盲文件 SHA、预检收据 SHA；不入库、不被任何冻结文件引用；前提：表 J 用户份额判定齐全、无未裁定「错」，预检收据存在）；⑤ `package` → K4 数据包 + `upload/manifest.json` + 本地 `package` 收据（记 `upload/manifest.json` SHA）；⑥ K3 `bundle` → 代码束 + `upload/code-manifest.json` + 本地 `bundle` 收据；⑦ 云端 `cloud_runner verify` → 按两份清单逐文件现算 SHA（缺文件 / 多文件 / 不符 → `PACKAGE_INCOMPLETE`），jsonl/盲文件 SHA = manifest 记录 = 冻结收据副本、prompt 模板 SHA 相等（否则 `FROZEN_SET_MISMATCH`），再 tokenizer 复核（`TOKENIZER_MISMATCH`）。完整冻结集（含 gold 文件与 `evaluate.py`）只在本地由 `freeze` 校验；云端只校验其实际持有的字节；本地 `verify_return` 把回传收据中的两份清单 SHA 与本地 `package` / `bundle` 收据比对 |
| 无 GPU 缺件回归 | K4：`test:tests.test_eng_sft_build.PackageTests.test_data_package_excludes_code_gold_and_forbidden_files`、`test:tests.test_eng_sft_build.PackageTests.test_package_requires_freeze_receipt_and_lists_every_member_with_transport_map`；K3：`test:tests.test_eng_sft_cloud.PackageTests.test_missing_or_extra_member_in_either_manifest_refuses_run`、`test:tests.test_eng_sft_cloud.PackageTests.test_code_manifest_lists_every_bundle_member_except_itself` |
| Python 依赖 | 云端 `PYTHONPATH=<包根>/code` 后 `python -m tools.eng_sft.cloud_runner`；`requirements-eng-sft.txt` 钉版本（torch / transformers / peft / accelerate / pillow）；包内模块不 import `controller.*`、不 import `tools.dist_data`（三态已在本地派生） |

评分与判定只在本地用 `evaluate.py` 对回传预测执行；gold 文件永不进入包根。

**表 I 训练侧 schema（`p1-eng-sft-002/<name>/v1`）**

| 工件 | 必含字段 |
|---|---|
| `job-receipt`（云端） | `job_id = sft-<utc>-<冻结收据 SHA 前 8 位>`（不是 scenario/session/run/attempt 身份）、两份清单 SHA 与表 K ⑦ 完整性核对结果、冻结链核对结果、tokenizer 复核结果（逐文件计数与本地预检收据比对）、按数据集的 `image_grid_thw` 断言结果、各阶段启动次数/耗时/GPU 占用、GPU 型号、产物 SHA、费用（用户填） |
| `adapter` manifest | base id + revision、adapter sha256/字节、LoRA 配置、seed、数据 manifest SHA、步数/epoch、被选原因、`job_id`、`env.json` SHA |
| 三份摘要 | 表 F 全部指标与分层、表 G 各层状态、配对差与 CI、v1 诊断附表、各阶段尝试与 GPU·h 账目 |


**表 L 跨环境评估接口与判定（AR1-4；条件分支，不阻塞 Unity 两停点；用户 2026-09-13 逐字「我倾向于不等」，账本同日条目）**

| 项 | 规则 |
|---|---|
| 前置判定时点 | 用户签发候选 2 执行信封当日：`P1-ENG-SFT-003` Gate board Overall = `DONE` 且其冻结收据存在 → AC-12 进入作业 A/B；否则 AC-12 = `NOT_RUN(SFT_003_NOT_DONE)` **终态**，本项不再等待、不自动授予 003 恢复或执行额度；日后跨环境评估另立工作项消费本项 adapter manifest（2B + LoRA 推理可在用户 5060 上执行） |
| 兼容条件（全部满足才运行；任一不满足 → `NOT_RUN(INCOMPATIBLE_EVAL_SCHEMA:<项>)` 写入 eval-summary，不阻塞 K3） | (1) 003 冻结 eval-row 通过本项 `evaluate.py --validate` 的 schema 校验：必含 `row_id, frame_path, group ∈ {G1, G3, G3p, G5}, gate_row, surface, gold_state ∈ {unique, ambiguous, none, null}, gold_boxes_norm_xywh[], stratum`；(2) 003 盲文件行与其 eval-row 一一对应、无 gold 字段；(3) 003 的 prompt v2 非词表段与本项 `prompt_v2.py` 模板（`{vocab}` 占位）逐字节相等（模板 SHA 相等）；词表段取 003 冻结文本并记 SHA；(4) 003 manifest 提供 `image_grid_thw_expected`；本项运行器按**数据集**断言：Unity 行 `[1, 30, 40]`、SynDrone 行 = 该期望值，缺字段即不满足；(5) 解析与评分**只用本项** `parse.py` / `evaluate.py`（同一实现评 Unity 与 SynDrone；003 自带评分器只用于其零样本基线）；(6) 泄漏断言：003 帧 SHA ∩ 本项训练∪选层帧 SHA = ∅ |
| 运行 | base 与被选 adapter 各在 003 盲文件（≤ 400 行）预测一次（base 在作业 A、adapter 在作业 B；同一信封）；回传校验同 Unity |
| 逐项配对指标（同一行域，adapter − base，pp） | m1 G3 报告率（↑）；m2 G3 严格成功（↑）；m3 G1 误报歧义率（↓，取负号后 ↑）；m4 G1 误报 none 率（↓，取负号后 ↑）；m5 G5 none 率（↑）；m6 G1 Success（↑，定位/词表退化监测）；各指标在 Unity（本项冻结评估集同名组）与 SynDrone 上分别计算 d_U(m)、d_S(m) |
| 迁移比 | r(m) = d_S(m) / d_U(m)，仅当 \|d_U(m)\| ≥ 5.0 pp 才计算，否则 `NA(UNITY_DELTA_SMALL)`；d_U(m) < 0 时 r 只披露、不参与结论 |
| 结论闭集（机械判定，实现者不解释） | `TRANSFER_OBSERVED` ⇔ d_U(m1) ≥ +10.0 且 d_S(m1) ≥ +10.0 且 d_S(m6) ≥ −5.0；`NOT_OBSERVED` ⇔ 运行完成但上式不成立；`NOT_RUN(<原因>)` ⇔ 前置或兼容条件不满足。三值均为描述性，不入功能门、不改变 DONE；阈值在 D3 接受时冻结 |
| 不承诺 | 合成到合成，必要非充分；SynDrone 词表与分辨率不同，不比较绝对值，只比较配对差；不做 SynDrone 训练；不推断真实航拍 |

**写入分层（三类互斥，路径闭集）**

| 类别 | 路径闭集 | 谁写 |
|---|---|---|
| A1 实现者源码/测试 | `tools/eng_sft/{__init__,receipts,three_state,build_sft_data,label_audit,prompt_v2,parse,evaluate,train_lora,cloud_runner,verify_return}.py`、`tools/eng_sft/adapters/{__init__,unity_s3}.py`、`tools/requirements-eng-sft.txt`、`tests/test_eng_sft_{build,three_state,audit,parse,evaluate,train,cloud}.py`、`tests/fixtures/eng_sft/`（生产路径产出）、两份报告、`docs/evidence/P1-ENG-SFT-002-label-audit.md`（表 J 抽样参数/分层实取/面板清单/统计/预筛表，不复制用户判定原文）、`.gitignore` 一条 `outputs/eng-sft/`、提案「待裁定」节、`docs/current-status.md`（按角色权限） | 实现角色 |
| A2 工具输出 | 受版本控制（各 ≤ 2 MB）：四份冻结 JSON、三份摘要、`docs/evidence/P1-ENG-SFT-002-tests.log`；本地 `outputs/eng-sft/P1-ENG-SFT-002/`：`data/`（训练/冒烟/选层/评估 jsonl 与盲文件、`legacy/`、`receipts/` 含 tokenizer 预检收据；≤ 64 MB，**不含**只读原图——原图只从 `runtime/` 按路径读取，不复制进数据目录）、`upload/`（表 K 云端包，含帧复制，≤ 0.3 GB，按「上传」项计额）、`panel/`（表 J 面板与原图副本，≤ 20 MB）、`returned/<job_id>/`（≤ 512 MB，adapter ≤ 200 MB）；`outputs/eng-sft/tokenizer/<revision>/`（tokenizer 四文件 ≤ 20 MB）；全目录 ≤ 0.9 GB | 工具（实现角色运行；云端阶段用户运行 `cloud_runner`） |
| A3 其他角色 | `docs/unity-test-log.md` 条目 `UT-P1-ENG-SFT-002-label-audit`（接受/辅助代录用户 ≤ 24 张判定原文；`OFFLINE_VISUAL_CHECK`，零 Play）与 `UT-P1-ENG-SFT-002-cloud-runs`（接受/辅助代录用户云端运行事实；`OFFLINE_GPU_RUN`，零 Play；工具不解析该条目——`P1-ENG-ASSET-001` F8 日志入口不使用）；`docs/reviews/P1-ENG-SFT-002.md`；`docs/implementation-status.md` 与提案决策/核对表/复判 | 对应角色 |

**收据：** `tools/eng_sft/receipts.py` 只 import `tools.eng_asset.receipts` 的 `sha256_file`、`utc_stamp`、`peak_rss_bytes`、`output_record`；自定义
`WORK_ID`、schema 前缀、输出根、禁写闭集（ASSET-001 §3 再加 `runtime/eng-asset`、`outputs/eng-asset`、`tools/eng_asset/`、`outputs/eng-sft3`）、
失败原因闭集 {`MANIFEST_COUNT_MISMATCH`, `SHARD_HASH_MISMATCH`, `INPUT_HASH_CHANGED`, `OUTPUT_PATH_FORBIDDEN`, `HISTOGRAM_MISMATCH`,
`LEGACY_SOURCE_MISMATCH`, `EVAL_GROUP_EMPTY`, `CONSERVATION_MISMATCH`, `FROZEN_FILE_DIRTY`, `FROZEN_SET_MISMATCH`, `PREDICTIONS_INCOMPLETE`,
`RETURN_HASH_MISMATCH`, `IMAGE_GRID_MISMATCH`, `GOLD_TOKEN_OVERFLOW`, `SMOKE_FAILED`, `PACKAGE_INCOMPLETE`, `TOKENIZER_MISMATCH`, `AUDIT_INCOMPLETE`, `AUDIT_FINDING_OPEN`}；输入清单阶段 `build`、`precheck`、`audit`、`freeze`、`package`、`bundle`、`return`、`stop`
各写 before/after 快照，只追加；失败只写失败收据。

**冻结机制：** 冻结闭集（四份 JSON + 四份脚本）提交后、表 J 用户份额判定齐全（否则 `AUDIT_INCOMPLETE`）且不存在未裁定的 `AUDIT_FINDING_OPEN`、且本地 tokenizer 预检收据存在时，运行 `build_sft_data.py freeze` 生成冻结收据（不入库、不被冻结文件引用；生成先后见表 K）；校验链：包内
jsonl/盲文件 SHA = manifest 记录 = 冻结收据，manifest/脚本 SHA = 冻结收据 = 该 HEAD 下 `git ls-files` 版本；「某路径 status 为空」不单独等同已提交。

**红线（继承）：** `tools/eng_sft/` 不 import `controller.*`；不改运行时任何文件；训练标签来自真值目录属离线数据加工，运行时真值隔离规则不变。

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | 对账与输入清单：只读 §3 输入闭集，逐件核对 S3/S4 manifest 计数（S3 43,535 / 151 片；S4 2,523/13,144/8,450/0；S5 690/93/37）与分片 SHA、S1 记录对帧 SHA、S5/instructions SHA 与探针清单 `source` 相等；`classify_uniqueness` 重算 57,430 行七值直方图与 `P1-ENG-ASSET-001-instructions-summary.json` 逐值相等；不符即 fail-closed；输入清单阶段快照只追加 | `test:tests.test_eng_sft_build.ReconciliationTests.test_shard_hash_mismatch_writes_failure_receipt_only`；`test:tests.test_eng_sft_build.ReconciliationTests.test_histogram_mismatch_fails_closed`；`test:tests.test_eng_sft_build.ReceiptTests.test_input_manifest_phases_append_only`；`artifact:docs/evidence/P1-ENG-SFT-002-dataset-manifest.json` | K4 | 2026-09-13 |
| AC-2 | 适配器、三态与集合：Unity 适配器按表 A′ 产出统一对象记录（含 `definite` 与 `frame_wildcard`），表 A′ 每行具名边界回归（含未绑定、缺框、裁剪后退化三种 wildcard 输入各自核对）；`three_state` 按表 A（含规则 ①）；训练池 = 表 E1 七族闭集，选层 = `detect-scout1`、训练 = 其余六族，test 与 `unassigned` 零帧；E2–E9 按确定公式与顺序执行且**试选与生产同一实现**，层/键/哈希/平局/E2 稀疏/E5 轮转逐字按表 D′，各步实取（含逐族 E2 计数）写入 manifest；生产切片 `UNIQUE_CLASS` ⇔ unique-self 逐行相等；`has_dynamic_target` 的 unique 样本 ≤ 350 且歧义样本单列 | `test:tests.test_eng_sft_build.AdapterTests.test_table_a_prime_cases_including_three_wildcard_inputs`；`test:tests.test_eng_sft_three_state.ThreeStateTests.test_rule_one_and_six_states`；`test:tests.test_eng_sft_build.ThreeStateTests.test_unique_class_equivalence_on_production_slice`；`test:tests.test_eng_sft_build.SplitTests.test_quota_roundrobin_and_copies_are_deterministic`；`test:tests.test_eng_sft_build.SplitTests.test_table_d_prime_stratum_key_hash_and_tie_order`；`artifact:docs/evidence/P1-ENG-SFT-002-dataset-manifest.json` | K4 | 2026-09-13 |
| AC-3 | 冻结评估集、守恒与泄漏：评估集只取 S4 test，按表 D 生成（legacy 优先、G4 独立 `execute`、目标车子组单列），准入/legacy 优先内次序/`S → M → L → NA` 层轮转逐字按表 D′；评估行 = 601 gate/诊断行 + LEGACY_ONLY 评估行（试选 8 行，承载 9 条 legacy 行）= 609 行，盲文件同行数；eval-row 带表 C 全字段（含 `frame_path`/`station_key`/`gold_state`/`diagnostic`/`gate_row`/`stratum`/`gold_text_len`/`legacy_probe[]`）；`legacy-conservation` Σ = 405，重复键行各自保留 gold 且指向同一评估行；`leakage-report` 断言训练∪选层 ∩ 评估 帧 SHA 交集 = ∅、训练∪选层 ∩ (test ∪ unassigned) = ∅、seen 按 E9；G1/G3/G5 任一为空 → `EVAL_GROUP_EMPTY`；eval-manifest 记录各组行数、并集帧数、逐张 SHA 绑定与总字节、各 jsonl 序列化总字节与单行 max/p50、各组 gold 字符长度 max/p50 与骨架计数 | `test:tests.test_eng_sft_build.EvalSetTests.test_conservation_sums_to_405_and_keeps_per_row_gold`；`test:tests.test_eng_sft_build.EvalSetTests.test_g4_and_target_subgroups_in_same_selection`；`test:tests.test_eng_sft_build.EvalSetTests.test_admit_gap_legacy_priority_and_stratum_rotation`；`test:tests.test_eng_sft_build.EvalSetTests.test_legacy_only_rows_carry_duplicate_key_probe_entries`；`test:tests.test_eng_sft_build.EvalSetTests.test_leakage_assertions_fail_on_injected_test_frame`；`test:tests.test_eng_sft_build.EvalSetTests.test_empty_key_group_fails_closed`；`artifact:docs/evidence/P1-ENG-SFT-002-eval-manifest.json`；`artifact:docs/evidence/P1-ENG-SFT-002-legacy-conservation.json` | K4 | 2026-09-13 |
| AC-4 | prompt、解析、评分、判定：`prompt_v2.py` 逐字等于表 B（词表段单独冻结并导出哈希），构造函数无法接收 gold；解析器按表 B（`parse_error ≠ null ⇒ status_pred = null`）；评分器按表 F（一对一最大匹配、分母不剔除、完整性、子组单列）；判定脚本按表 G；bootstrap 参数固定；全部无模型夹具测试 | `test:tests.test_eng_sft_parse.ParserTests.test_error_closed_set_clears_status_pred`；`test:tests.test_eng_sft_evaluate.MatchingTests.test_max_cardinality_one_to_one_matching`；`test:tests.test_eng_sft_evaluate.VerdictTests.test_layer_statuses_on_fixture_predictions`；`test:tests.test_eng_sft_evaluate.PromptTests.test_prompt_builder_cannot_see_gold_and_vocab_is_frozen`；`test:tests.test_eng_sft_evaluate.CompletenessTests.test_missing_or_duplicate_rows_invalidate_run` | K4 | 2026-09-13 |
| AC-5 | 盲文件、K4 数据包、预检与冻结收据：盲行与 sample 的 `frame_path` 在 `build` 时写定为 `frames/<sha256>.jpg`（SHA 取 S1 记录并逐张核验），打包不改任何 jsonl 字节；`smoke.jsonl` 由 `build` 按表 H 规则产出并入 dataset-manifest；`precheck` 用同版 tokenizer 对全部 gold 逐条实测并写绑定收据（表 H；需候选 1 信封含 tokenizer 下载，未授权则停在预检）；`package` 只在 `freeze` 收据存在后运行，产出表 K 的 K4 数据包（**不含代码**），`upload/manifest.json` 逐文件列 SHA 与帧运输映射且不含自身、不列 gold 评估文件与禁写内容；本地 `package` 收据记 `upload/manifest.json` SHA；`freeze` 在提交后生成，前提：表 J 用户份额判定齐全且无未裁定「错」、预检收据存在；任一冻结文件未跟踪/脏 → `FROZEN_FILE_DIRTY`；manifest 不含自身/提交 SHA | `test:tests.test_eng_sft_build.BlindTests.test_blind_rows_have_no_gold_fields_and_package_relative_frame_path`；`test:tests.test_eng_sft_build.PrecheckTests.test_precheck_receipt_binds_gold_files_function_and_tokenizer`；`test:tests.test_eng_sft_build.PackageTests.test_data_package_excludes_code_gold_and_forbidden_files`；`test:tests.test_eng_sft_build.PackageTests.test_package_requires_freeze_receipt_and_lists_every_member_with_transport_map`；`test:tests.test_eng_sft_build.FreezeTests.test_dirty_or_untracked_frozen_file_is_refused`；`test:tests.test_eng_sft_build.FreezeTests.test_freeze_requires_complete_audit_and_precheck_receipt` | K4 | 2026-09-13 |
| AC-6 | 数据报告与边界：报告给出表 D/E 实取（含表 E1 族闭集与逐族 E2 计数）、守恒摘要、泄漏与 seen、按表 C 全字段实测的序列化字节（各 jsonl 总字节与单行 max/p50）与 gold 字符长度、tokenizer 预检收据摘要（revision、文件 SHA、逐文件 token max/p50、模板开销）、执行收据（耗时、峰值 RSS ≤ 1 GB）、输入身份（含探针清单现算 SHA）、失误画像对照表（§8 表 8 格式）、表 J 抽查统计与 ASSET-001 交集表；候选 1 实现 diff 只含 A1/A2；`data/` ≤ 64 MB（不含只读原图与 tokenizer 文件）、`upload/` ≤ 0.3 GB、`panel/` ≤ 20 MB、`tokenizer/` ≤ 20 MB，受版本控制 A2 各 ≤ 2 MB；不 import `controller.*`；全套测试摘要区分基线已有失败与新增失败 | `test:tests.test_eng_sft_build.WriteBoundaryTests.test_output_inside_forbidden_roots_is_refused`；`test:tests.test_eng_sft_build.WriteBoundaryTests.test_no_controller_imports`；`test:tests.test_eng_sft_build.WriteBoundaryTests.test_directory_caps_split_by_root`；`cmd:python3 -m unittest discover -s tests > docs/evidence/P1-ENG-SFT-002-tests.log 2>&1; tail -n 3 docs/evidence/P1-ENG-SFT-002-tests.log`；`artifact:docs/evidence/P1-ENG-SFT-002-data-report.md` | K4 | 2026-09-13 |
| AC-7 | 代码束、包完整性与冻结链（K3）：`cloud_runner bundle` 产出表 K 代码束与 `upload/code-manifest.json`；云端 `verify` 按两份清单逐文件现算 SHA，缺/多/不符 → `PACKAGE_INCOMPLETE`，帧现算 SHA 须等于文件名；jsonl/盲文件 SHA = manifest 记录 = 冻结收据副本、prompt 模板 SHA 相等，不符 `FROZEN_SET_MISMATCH` 不运行；`verify_return` 比对回传收据两份清单 SHA 与本地 `package` / `bundle` 收据；候选 2 不改任何冻结文件与 K4 数据包（diff 与 SHA 断言） | `test:tests.test_eng_sft_cloud.PackageTests.test_missing_or_extra_member_in_either_manifest_refuses_run`；`test:tests.test_eng_sft_cloud.PackageTests.test_code_manifest_lists_every_bundle_member_except_itself`；`test:tests.test_eng_sft_cloud.FreezeTests.test_mismatched_manifest_or_receipt_refuses_run`；`test:tests.test_eng_sft_cloud.FreezeTests.test_frozen_files_and_data_package_untouched_by_candidate_2` | K3 | 2026-09-13 |
| AC-8 | tokenizer 复核与图像网格（K3）：云端下载后、任何推理前，同版 tokenizer 对包内 `train.jsonl` + `smoke.jsonl` 全部 `gold_text` 重算，逐文件计数与 max 须等于本地预检收据（不等 → `TOKENIZER_MISMATCH` 停止），max ≤ 152 否则 `GOLD_TOKEN_OVERFLOW`；评估 gold 不上云；结果入 `job-receipt`；每张图按数据集断言 `image_grid_thw`（Unity `[1,30,40]`；SynDrone 按表 L (4)）；不符即失败收据、不截断 | `test:tests.test_eng_sft_train.PrecheckTests.test_overflow_fails_closed_without_truncation`；`test:tests.test_eng_sft_train.PrecheckTests.test_cloud_recount_mismatch_stops`；`test:tests.test_eng_sft_train.GridTests.test_grid_assertion_is_per_dataset`；`artifact:docs/evidence/P1-ENG-SFT-002-train-summary.json` | K3 | 2026-09-13 |
| AC-9 | 零样本对照：base + prompt v2 在 Unity 盲评估集运行一次；本地评分；`zero-shot-v2-summary.json` 含表 F 全部指标、分层与 v1 诊断附表 | `artifact:docs/evidence/P1-ENG-SFT-002-zero-shot-v2-summary.json`；`artifact:outputs/eng-sft/P1-ENG-SFT-002/returned/<job_id>/job-receipt.json`（SHA 入摘要） | K3 | 2026-09-13 |
| AC-10 | 训练与选优：冒烟通过后按表 H 顺序 ≤ 3 run；三个 adapter 各在盲选层子集预测；本地按选优规则选出正式 adapter；adapter manifest 与 `train-summary.json` 记录表 I 字段、各阶段尝试与 GPU·h；无 GPU 单元测试覆盖配方冻结、模板渲染、assistant-only 损失掩码、冒烟抽样、选优/并列 | `test:tests.test_eng_sft_train.TemplateTests.test_assistant_only_loss_mask`；`test:tests.test_eng_sft_train.ConfigTests.test_only_three_candidates_in_order`；`test:tests.test_eng_sft_train.SelectionTests.test_tie_break_prefers_fewer_epochs_then_lower_lr`；`artifact:docs/evidence/P1-ENG-SFT-002-train-summary.json` | K3 | 2026-09-13 |
| AC-11 | 正式评估与判定：被选 adapter 在 Unity 盲评估集运行一次（作业 B）；回传校验通过后本地评分；`eval-summary.json` 给出表 G 各层状态、目标车子组与分层；`GATE_NOT_MET`/`INFERIOR` 时报告含失败分析，不追加 run | `test:tests.test_eng_sft_cloud.ReturnTests.test_return_hash_mismatch_refuses_scoring`；`artifact:docs/evidence/P1-ENG-SFT-002-eval-summary.json`；`cmd:python3 tools/eng_sft/evaluate.py --verdict docs/evidence/P1-ENG-SFT-002-eval-summary.json` | K3 | 2026-09-13 |
| AC-12 | 跨环境评估（条件分支，表 L）：前置在候选 2 执行授权当日一次性判定（`P1-ENG-SFT-003` DONE 且冻结收据存在），不成立 → `NOT_RUN(SFT_003_NOT_DONE)` 终态、本项不等待；成立时先机检兼容条件 (1)–(6)，任一不满足 → `NOT_RUN(INCOMPATIBLE_EVAL_SCHEMA:<项>)`；通过后 base 与被选 adapter 各在 003 盲文件（≤ 400 行）预测一次，本地用本项 `parse.py`/`evaluate.py` 评分；eval-summary 给出 m1–m6 在两环境的配对差、迁移比（小分母 `NA`）与机械结论 `TRANSFER_OBSERVED` / `NOT_OBSERVED`；SynDrone 零帧进入训练/选层（泄漏断言）；任何分支都不阻塞 K3 候选交付 | `test:tests.test_eng_sft_cloud.TransferTests.test_syndrone_frames_never_in_training_package`；`test:tests.test_eng_sft_cloud.TransferTests.test_incompatible_schema_yields_not_run`；`test:tests.test_eng_sft_evaluate.TransferTests.test_transfer_verdict_is_mechanical_with_na_rule`；`artifact:docs/evidence/P1-ENG-SFT-002-eval-summary.json` | K3 | 2026-09-13 |
| AC-13 | 报告与账目：三个问题的直接回答、表 G 判定表（含表 L 结论与原因）、按类别/S-M-L-NA/seen-unseen 分层、每组 min(10, 实际失败数) 条失败案例（row_id、指令、预测、gold、本地图片指针）、模型/数据来源与许可（base Apache-2.0；adapter/数据未发布）、各阶段尝试/GPU·h/推理行/费用对信封逐项核对；候选 2 diff 只含 A1/A2；本地全目录 ≤ 0.9 GB（`returned/` ≤ 512 MB）；不 import `controller.*` | `test:tests.test_eng_sft_cloud.WriteBoundaryTests.test_no_controller_imports_and_forbidden_roots`；`artifact:docs/evidence/P1-ENG-SFT-002-report.md` | K3 | 2026-09-13 |
| AC-14 | 派生标签语义抽查（表 J）：`label_audit.py` 按表 J 分层配额与 `h(s)` 序确定性抽样（同对象每层 ≤ 1、同帧全局 ≤ 1、用户份额 ≤ 24、预筛 ≤ 36，不足额留空披露）；面板收据记 HEAD/样本身份/原图 SHA/叠加图 SHA；ASSET-001 交集表按 `(frame_id, object_id)` 生成；用户判定由接受/辅助代录 `UT-P1-ENG-SFT-002-label-audit`，label-audit 文件只存统计与预筛表；任一用户「错」→ `AUDIT_FINDING_OPEN` 且 `freeze` 拒绝，闭合路径按表 J；预筛结果披露且不计为核验 | `test:tests.test_eng_sft_audit.SamplerTests.test_layer_quotas_and_uniqueness_are_deterministic`；`test:tests.test_eng_sft_audit.ReceiptTests.test_open_finding_blocks_freeze`；`test:tests.test_eng_sft_audit.ReuseTests.test_asset001_intersection_table`；`artifact:docs/evidence/P1-ENG-SFT-002-label-audit.md`；`artifact:docs/unity-test-log.md#UT-P1-ENG-SFT-002-label-audit` | K4 | 2026-09-13 |

AC 编号一经接受即稳定；实现期合同问题写「待裁定」节，答复只追加。

### 首次接受释义（2026-09-13，随 D3 一并冻结）

以下逐行挂接原 AC，消除首次接受时的执行歧义；与正文冲突处以本表为准。原 AC 和历史裁定不覆盖。
本表没有增加工作目标、数据集、模型配置或资源额度，不是实现后核对轮新增义务。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-2 修订 1 | 表 D′/E 的算法、取样常量与当前输入闭集冻结；“试选与生产同一实现”指实现者的试运行与正式构建调用同一生产函数，不要求复用构思 scratchpad。d7 的 `hk` 五元组为本次并列口径。原输入且未发生表 J 裁定修标时，表 D/E 行数与图像并集必须复现；不符停在待裁定，不为凑数改变种子/准入/配额。 | `test:tests.test_eng_sft_build.SplitTests.test_table_d_prime_stratum_key_hash_and_tie_order`；`artifact:docs/evidence/P1-ENG-SFT-002-dataset-manifest.json` | K4 | 2026-09-13 |
| AC-3 修订 1 | 评估闭集固定为表 D 的十组，609 行；legacy 守恒单位是原始 `row_id`，405 条。当前 LEGACY_ONLY 的 8 行均来自 G3p 灰区，`gold_state=null`，不因表 D 原句“新状态合法”而编造三态 gold；G3p 与 LEGACY_ONLY 合计 58 行不进 gold token 预检。两组保留 `definite_ids`、`legacy_probe`；三态 gold 框数组为空。G3p 的表 F “任一 M 命中”在本地按 `frame_id + definite_ids` 从已绑定 S3 原框取回（dynamic-target 沿表 A′），不取旧探针 v1 单目标框代替 M；缺源/缺框按既有 `INPUT_HASH_CHANGED` 拒绝该次评分并写失败收据，不剔除行或影响功能门定义。 | `test:tests.test_eng_sft_build.EvalSetTests.test_legacy_only_rows_carry_duplicate_key_probe_entries`；`test:tests.test_eng_sft_evaluate.MatchingTests.test_gray_diagnostic_uses_bound_s3_definite_boxes`；`artifact:docs/evidence/P1-ENG-SFT-002-legacy-conservation.json` | K4 | 2026-09-13 |
| AC-4 修订 1 | `gold_text(sample)` 与表 B 的坐标整数化共用纯函数，置于 K4 已交付、已冻结、K3 代码束已枚举的 `prompt_v2.py`；本地构建/预检/评分与云端训练/冒烟/预检均调用它，不在未上云的 `three_state.py` 中隐藏依赖、不复制第二份序列化。prompt 构造函数仍只接收表 B 四种参数，与 gold 函数分开。x/y 两轴各执行同一退化修正；只冻结三态序列化和 152 拒绝阈值，不声称实际 token 数已通过。 | `test:tests.test_eng_sft_evaluate.PromptTests.test_prompt_builder_cannot_see_gold_and_vocab_is_frozen`；`test:tests.test_eng_sft_train.PrecheckTests.test_cloud_recount_mismatch_stops` | K4 / K3 | 2026-09-13 |
| AC-5 修订 1 | 预检 gold 文件闭集 = `train.jsonl`、`smoke.jsonl`、`select-eval.jsonl`、`eval.jsonl`；选层指实际用于选优的 441 行，不另输出未使用的全量 `select.jsonl`。sample/评估/盲行落盘统一用 d7 的 UTF-8、`ensure_ascii=True`、紧凑分隔符、每行末尾一个 LF；gold 文本仍用表 B 的缺省空格分隔符。`freeze` 核对预检收据所绑定四文件、gold 函数与 tokenizer 的 SHA 等于当前文件；缺失或过期不得冻结（缺收据为 `FROZEN_SET_MISMATCH`，已绑定输入变化为 `INPUT_HASH_CHANGED`）。`package` 与 K3 `bundle` 不改已冻结 jsonl 字节。 | `test:tests.test_eng_sft_build.PrecheckTests.test_precheck_receipt_binds_gold_files_function_and_tokenizer`；`test:tests.test_eng_sft_build.FreezeTests.test_freeze_requires_complete_audit_and_precheck_receipt` | K4 | 2026-09-13 |
| AC-6 修订 1 | §8 表 6c 是 d7 临时程序按完整字段所得的尺度测量，不是生产文件必须逐字节相等的快照；保留原数字，生产报告另列同口径测量与差异理由，不能改样本集合/字段以追平字节。硬上限是 AC-6 分目录与 RSS 上限；表 6b 的 token/吞吐/GPU 时间/adapter 体积均不冻结为性能事实。构建尝试申请 ≤8 次包含真实输入的对账、构建、冻结与打包入口，失败计数；独立复核重跑按 §5 零 GPU 项目记录。 | `artifact:docs/evidence/P1-ENG-SFT-002-data-report.md`；`test:tests.test_eng_sft_build.WriteBoundaryTests.test_directory_caps_split_by_root` | K4 | 2026-09-13 |
| AC-7 修订 1 | 表 K 的 `upload/manifest.json`、`upload/code-manifest.json` 是相对本地工作项根的路径；各自成员路径相对包根 `upload/`，清单本身位于该根，不再建立嵌套 `upload/upload/`。云端允许文件集合 = K4 清单成员 ∪ K3 清单成员 ∪ 两份清单本身；分别校验各自成员，再拒绝并集之外的文件，不能把另一清单及其合法成员误判为多件。K3 中的 K4 代码副本（prompt/parse）须与冻结收据匹配，K4 数据包及清单不得修改。 | `test:tests.test_eng_sft_cloud.PackageTests.test_missing_or_extra_member_in_either_manifest_refuses_run`；`test:tests.test_eng_sft_cloud.FreezeTests.test_frozen_files_and_data_package_untouched_by_candidate_2` | K3 | 2026-09-13 |
| AC-12 修订 1 | 表 L 的前置与六项兼容条件冻结为本项的准入规则，不冻结尚未试读的 003 schema/规模、不恢复 003。仅在前置与兼容条件成立且候选 2 信封明确覆盖时，表 K 枚举的 SynDrone 盲文件、manifest、词表和其 manifest 枚举的帧加入 K3 `code-manifest.json` 的独立数据成员段；不按表 K 原句增改 K4 `manifest.json`。云端仍按 AC-7 修订 1 校验两份清单。此分支包根/上传申请上限统一为 §5 条件值 0.6 GB；默认 Unity 分支仍为 0.3 GB，全目录仍 ≤0.9 GB；任一所需额度缺失为 0，回用户，不自动执行。 | `test:tests.test_eng_sft_cloud.TransferTests.test_incompatible_schema_yields_not_run`；`test:tests.test_eng_sft_cloud.FreezeTests.test_frozen_files_and_data_package_untouched_by_candidate_2`；`artifact:docs/evidence/P1-ENG-SFT-002-eval-summary.json` | K3 | 2026-09-13 |
| AC-14 修订 1 | 表 J 抽样域按其已枚举 J1…J7 解释：J1…J5 使用训练 distinct ∪ 441 行选层 ∪ 评估中 G1/G1t/G2/G2t/G3/G3t/G5；J6 使用 86 行 G4；J7 使用已绑定 S3 中 #27 在执行域且 bus 颜色指令被排除的帧（保留被排除 surface 作显示证据，不加入训练/评估）。G3p/LEGACY_ONLY 不抽。用户份额先按 J1→J7 取完，预筛再按 J1→J6 续取；同帧全局唯一，同对象限制对多候选行逐个 object_id 检查，none 用 surface。J1 用户按表 J 弱类顺序各取一行；J3 用户先取含目标车的一行（若可得），其余按候选数3–4优先再哈希序；J2 按 color_required 优先再哈希序；其余按表 D′ 哈希序（J7 用 surface 键），平局补 frame_id/surface。不足额披露不回填、不突破24张；未判定/错误阻止冻结，不确定单列；复判只在后续获批次数内执行。 | `test:tests.test_eng_sft_audit.SamplerTests.test_layer_quotas_and_uniqueness_are_deterministic`；`test:tests.test_eng_sft_audit.ReceiptTests.test_open_finding_blocks_freeze`；`artifact:docs/evidence/P1-ENG-SFT-002-label-audit.md` | K4 | 2026-09-13 |

首次接受释义共 8 行，原 AC-1…14 不重编号。未列修订的 AC-1/8/9/10/11/13 按正文执行；AC-3/4 的本地诊断取框只消费 §3 已枚举只读输入，仍不把 gold 传入模型 prompt。

## 5. 预算信封（申请值；`ACCEPTED` 后由用户逐字授权入账，缺项视为 0；候选 1 与候选 2 可分两次授权）

**当前授权指针（2026-09-18）：** 下表保留原申请值；候选1以账本2026-09-14授权、2026-09-15追加及2026-09-16「批准 R1@K4 F1 返工追加信封」为准：真实入口累计上限14、面板3、预筛39、代录2；precheck上限5、用户复判上限1不变，本次仅补判3张。K4已验收通过。候选2默认Unity分支已获用户“授权签发”，详见账本2026-09-18同名条目；设备已指定云端单张RTX 5090、累计≤8 GPU·h、GPU租金≤6美元；AC-12签发日已判NOT_RUN(SFT_003_NOT_DONE)，SynDrone相关额度为0。

| 项目 | 上限（申请） |
|---|---|
| Consuming | no（不创建 scenario/session/run/attempt 身份、不 Play、不用模型 API；`job_id` 只是作业收据标识） |
| 候选 1 本地构建累计尝试（对账/构建/冻结；含失败） | ≤ 8 次；每次 ≤ 5 min 桌面 CPU，峰值 RSS ≤ 1 GB（试选 387 MB） |
| 候选 1 标签语义抽查（表 J） | 面板生成 ≤ 2 次（每次 ≤ 5 min CPU）；用户判定 ≤ 24 张唯一图片，1 次 + 复判 ≤ 1 次；实现者预筛 ≤ 36 张；`panel/` ≤ 20 MB；代录 1 次 |
| 候选 1 tokenizer 预检 | tokenizer 四文件下载一次（≈ 12 MB，`Qwen/Qwen3-VL-2B-Instruct` 同 revision；不下载权重）；`precheck` 运行 ≤ 3 次（含失败），零 GPU |
| 候选 2 各阶段启动次数（含失败与中断） | 零样本对照 ≤ 2、冒烟 ≤ 2、训练 run ≤ 4（三配置 + 1 次重试）、正式评估 ≤ 2、SynDrone 评估 ≤ 2（仅 003 DONE 时）；**总启动 ≤ 8**（含 SynDrone 时 ≤ 10） |
| GPU 占用（云端 24–48 GB 单卡；覆盖训练、推理与作业内空闲，含失败/中断） | ≤ 8 GPU·h（含 SynDrone 时 ≤ 10） |
| 推理行数（含重试） | Unity：零样本 ≤ 2 × 609 + 选层 ≤ 4 × 441 + 正式 ≤ 2 × 609 + 冒烟 ≤ 2 × 32 ≈ 4,264 行；SynDrone（条件）≤ 4 × 400，表 L 前置不成立时为 0 |
| 租金 | 上限由用户填写（估算依据 §8 表 6） |
| 下载 | 候选 1：tokenizer 四文件一次（≈ 12 MB）；候选 2：base 权重一次（≈ 4.4 GB）+ pip 依赖；不下载其他模型 |
| 上传（用户自有云盘/对象存储，不公开） | ≤ 0.3 GB（试选：帧并集 180.9 MB + jsonl/脚本；含 SynDrone 时 ≤ 0.6 GB）；包在 `upload/` 根生成（表 K），不计入 64 MB 数据目录 |
| 云端磁盘 / 本地目录 | ≤ 20 GB / `data/` ≤ 64 MB（不含只读原图）、`upload/` ≤ 0.3 GB（= 上传项，帧复制）、`panel/` ≤ 20 MB、`returned/` ≤ 512 MB（adapter ≤ 200 MB）；全目录 ≤ 0.9 GB |
| 返工重跑 | 若 `C1@K3`/`R@K3` 要求重新执行，重跑消耗上述同一信封；超出回用户 |
| 零 GPU 项目 | 无 GPU 单元测试、本地评分/判定、独立复核重跑、回传校验 |
| 用户决策点 | ≤ 5（候选 1 接受与授权入账；表 J 判定与代录；候选 2 执行信封；云端运行事实代录；判定结果代录） |
| 发布 | 否 |

## 6. 限制与不承诺

- 只支持事实陈述：本 Unity 场景九类词表内的三态协议与选框成功率；泛化只按评估集逐行 `seen` 披露（试选：G1 210 行中 30 行目标未见）；
  不主张真实航拍、开放词表、跟踪性能、恢复能力、Jetson 性能或教师增量。词表对齐**不是训练目标**，表 G(d) 只监测退化。
- gold 是 amodal 投影 AABB（框 `UNVERIFIED`，S6 未执行）；颜色词只覆盖 37 辆已验证车 + 目标车的 `red`；#27 反例所在帧的 `bus` 颜色指令
  整帧排除；不生成 color-none。目标车是脚本生成的红色立方体车，单一对象，unique 样本在 car 类内 ≤ 350，歧义样本 65 单列；
  `G1t/G2t/G3t` 不与 G1/G2/G3 混算；规则 ① 是本项工程数据合同，不回改 DATA-001。
- 评估集在探针同款去重下 G1/G2/G4 可得行就是旧探针的 210/49/86；G2 只有 7 个对象；G3 48 行；5 Hz 近重复极高，行级 CI 只是描述性区间。
  探针已读取 test 279 帧做零样本推理；本项对冻结评估集再做零样本与微调评估各一次；test 不进训练、不进选层。
- 若 prompt v2 零样本已满足功能门 (a)(b)(c)，训练仍按信封执行一次以取得配对对照，报告写明「prompt 已满足功能门」；若 (d) 不成立而
  (a)(b)(c) 成立，只能陈述「协议达成、词表对齐退化 x pp」。
- 跨环境评估依赖 003（已暂停）；003 未 DONE 时记 `NOT_RUN`，不推断可迁移性。云端由用户执行，实现角色不接触云端；adapter 与预测不入仓库。
- `IMPLEMENTED` ≠ `DONE`：候选 1 与候选 2 各需实现证据 + 独立复核通过 + `UNITY_NA` 经复核附议；`GATE_NOT_MET`/`INFERIOR` 不阻止 DONE，
  也不授权追加 run。
- G2t 不要求 `color_required`（目标车是 `red` 的唯一来源）：试选 23 行与 G1t 同帧同层，只报告、不入门。
- token 预检：本地同版 tokenizer 对全部 gold 逐条实测（K4，需候选 1 信封含 ≈ 12 MB tokenizer 文件下载），收据绑定 gold 文件 / 函数 / tokenizer
  版本 / 计数开关；云端只对上云的训练与冒烟 gold 重算并与收据比对；评估 gold 不上云。不使用任何外推（字节界或骨架界）；152 只是拒绝阈值；
  未获下载授权则预检无法完成、不能冻结，回接受角色。
- 评估集 609 行：LEGACY_ONLY 8 个评估行承载 9 条 legacy 行（一对重复键），405 行守恒不变；D2 的 610 系按 legacy 行数计数。
- 训练标签（`train.jsonl` / `smoke.jsonl` 的 gold）随包上云，属离线数据加工；选层/评估 gold 永不上云。
- 表 J 抽查是 n ≤ 60 的描述性核验（用户 ≤ 24 + 实现者预筛 ≤ 36），不构成 S6 审计、不改 gold 定义、不重标旧目录；预筛不计为核验。
- 表 J 用户 #20/#21 颜色「错」均保留：分别显示 `Vehicle_Bus_color03` 与 `Vehicle_Bus_color01 (1)`，不是同一对象。
  两帧的 bus 颜色 noun 已因 #27 在执行域而排除；本次裁定只处理这两帧，不将 #21 的一次判错外推为该对象、同族或全部非纯色车的重标。
  预筛 #33 的颜色疑点保留为未核验限制；本项不检验“无纯色匹配时选最接近颜色”，也不能宣称具备该鲁棒性。
- AC-12 前置在候选 2 执行授权时一次性判定，不成立即 `NOT_RUN` 终态：本项不等待 003，也不自动授予 003 恢复/执行额度。
- §8 表 6b 的 token/算力数字是投影，不是实测；8 GPU·h 信封按投影仍覆盖三 run 与全部推理但余量变小（≈ 6.5 h），超出回用户。

## 7. 必经停点

- **`K4`（候选 1，零 GPU、零模型；tokenizer 文件下载与预检在此）**：AC-1…6 + AC-14，走 `C1@K4` → `R<n>@K4`；独立复核可用真实工件重跑构建器（≈ 1–2 min，零 GPU）。
- **`K3`（候选 2）**：AC-7…13；候选含本项训练/云端源码 diff（`train_lora.py`、`cloud_runner.py`、`verify_return.py` 与测试），开轮资格成立；
  走 `C1@K3` → `R<n>@K3`。任何 GPU 行动以 K4 **最终通过轮** + `UNITY_NA` 附议 + 用户候选 2 执行信封为前提。
- 执行顺序：K4 通过 → 候选 2 执行授权 → 实现者交付源码并通过 focused 测试 → 用户按 §2 作业 A/B 执行 → 回传校验、评分、报告 → 停点自证 →
  `C1@K3` → 独立复核；复核要求重新执行的重跑在同一信封内。
- AC-12 前置判定时点 = 用户签发候选 2 执行信封当日（表 L）；不成立即 `NOT_RUN(SFT_003_NOT_DONE)` 终态，K3 候选照常交付。表 J 抽查在 K4
  候选冻结前完成，用户判定与复判计入候选 1 信封；`freeze` 以无未裁定 `AUDIT_FINDING_OPEN` 为前提。
- 不触发 `K1`/`K2`/`K5`。Unity 列申请 `UNITY_NA`（纯离线、零运行时行为），须复核角色在 `docs/reviews/P1-ENG-SFT-002.md` 附议。

## 8. 只读试读与试运行数字（2026-09-13 并入版试选 `sft_d5_dryrun.py`：表 A（含规则 ①、AD3-3）/D/E 同一算法一次产出；D2 补测 `sft_d6_measure.py`（临时表示）；D3 补测 `sft_d7_measure.py`：表 C 全字段序列化含 609 行评估集与 legacy 字段（T7 已挂载）；零写入、零 ID、零模型；脚本留 scratchpad）

**表 1 执行收据**：S3 全量流式扫描 + `frame_world` 逐帧构域 + 三态派生 + 配额/轮转 + 评估试选（含 G4 与 legacy 优先纳入、405 行守恒）+
全集合逐张 SHA 绑定：d5 留存输出 57.9 s（正文此前写 58.1 s 系另一次运行读数，以留存输出为准；AD3-1 注：各数字标注收据来源）、D2 复算 d6 56.3 s（训练/选层部分，临时表示）、D3 复算 d7 58.1 s（全字段，含 609 行评估集与 legacy 字段，RSS 389 MB）；d5/d6 峰值 RSS 387 MB；SHA 绑定：训练 3,198/3,198（143.2 MB）、选层评估子集 322/322（18.8 MB）、评估含
LEGACY_ONLY 帧 448/448（18.8 MB）、并集 3,968/3,968（180.9 MB）；目标车在场帧 10,364，其中已绑定但缺框/退化 0，未绑定 0。

**表 2 旧七值（目标行）× 新 class-noun 状态（全量 57,430 行；规则 ① 只增加目标车为确证候选，不改变目录车行的 unique 判定）**

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

**表 4 评估集试选（test；与表 D 同一次）**：G1 210 / G1t 23 / G2 49 / G2t 23 / G3 48 / G3t 12 / G3′ 50 / G4 86 / G5 100 = 601 行 + LEGACY_ONLY 8 评估行（承载 9 条 legacy 行，d7 核实；D2 前按 legacy 行数写 9/610）= 609 行；
G1 S/M/L 30/95/85、9 类 48 对象、目标 seen 180；G4 S/M/L 22/38/26、9 类 29 对象；G3 8 类 28 对象；守恒 Σ = 405（无遗漏）。

**表 5 训练与选层（表 E 实取）**：训练多重集 5,318（unique 4,006 + none 490 + 2 × 411）/ 3,198 帧 / 143.2 MB；unique 分层 S 458 / M 1,747 /
L 1,801；目标车 unique 350 + 歧义 65；seen 76；选层评估子集 441 行 / 322 帧 / 18.8 MB。

**表 6a d6 临时表示实测（D2，`sft_d6_measure.py`；`station_key = None`、浮点四舍五入 6 位、无 `frame_path`；已被表 6c 取代，只保留来源标签）**：
train.jsonl 4,907 条 3,300,747 B（单行 max 877 / p50 670）、select-eval.jsonl 281,756 B、盲文件 82,778 B；gold 字符 max 143（训练）/ 145（test 全体可得歧义样本）；
prompt v2 固定文本 1,226 字符（不含 surface，最长 surface 25 字符）；评估集行级字节当时未复算（T7 未挂载）；56.3 s / RSS 387 MB。


**表 6c d7 全字段实测（D3，`sft_d7_measure.py`；表 C 现合同全部字段：`station_key` 实取、浮点原值、`frame_path` 包内路径、609 行评估集含 `legacy_probe[]`；序列化 `json.dumps(separators=(",", ":"))` 每行一条；legacy 清单 T7 现算 SHA `7c259a34…9bd3` 与 Unity 日志前缀一致；取样计数与 d5 逐项相同）**

| 文件 | 行数 | 总字节 | 单行 max / p50 / min（B） |
|---|---|---|---|
| `train.jsonl`（distinct；ambiguous 411 条加载时 ×2 → 5,318） | 4,907 | 3,975,066（3.79 MB） | 1,108 / 808 / 630 |
| `smoke.jsonl` | 32 | 26,108 | 1,009 / 809 / 659 |
| `select-eval.jsonl`（含 gold，留本地） | 441 | 341,500（0.33 MB） | 918 / 789 / 651 |
| `select-eval.blind.jsonl` | 441 | 77,927 | 191 / 177 / 173 |
| `eval.jsonl`（含 gold 与 `legacy_probe[]`，留本地） | 609 | 634,764（0.61 MB） | 1,644 / 1,091 / 709 |
| `eval.blind.jsonl` | 609 | 112,096 | 227 / 180 / 174 |
| `legacy-conservation.json`（逐行计） | 405 | 114,452 | 328 / 277 / 249 |

gold 字符长度（`gold_text`，纯 ASCII）：训练 distinct 4,907 条 max 143 / p50 53；冒烟 32 条 ≤ 143；选层 441 条 max 109；评估 551 行有 gold（G3′ 50 +
LEGACY_ONLY 8 = 58 行 `gold_state = null`）max 145（G3/G3t 3 候选）、unique 各组 ≤ 55、G5 18；全部集合无 4 候选行。`legacy_probe` 条目共 405（3 个评估行
各承载 2 条重复键 legacy 行）。冒烟组成：unique class 8 + color 8、ambiguous 8（class 5 + color 3）、none 8。执行收据：58.1 s，峰值 RSS 389 MB；SHA 绑定
训练 3,198 / 选层 322 / 评估 448 / 并集 3,968 全部相符，180.9 MB。token 数未测（本地无 tokenizer，待候选 1 预检）。

**表 6b 投影（未实测，接受时不冻结）**：四份冻结 JSON 各 ≤ 2 MB；每样本 token ≈ 300 视觉 + prompt（≈ 1,250 字符 ≈ 280–320）+ 模板 ≈ 20 + gold ≤ 152 ⇒ ≤ 约 800；
每 run 5,318 × epoch × ≈ 700 token：C1/C3 2 epoch ≈ 7.4M、C2 3 epoch ≈ 11.2M（原 7.2M 系按 450 token 估算，偏低）；2B LoRA bf16 A100 级 2–4k token/s →
三 run 合计 ≈ 1.8–3.6 h；Unity 推理 610 行 × ≈ 2 s ≈ 20 min、选层 3 × 441 ≈ 45 min；adapter r=16 ≈ 18M 参数 ≈ 37 MB bf16。

**表 7 对象级划分（沿 001 D1，只描述划分）**：train+dev 有唯一指令的对象 53、test 53、其中不在 train+dev 的 31、S4 留出且在 test 的 20。

**表 8 零样本失误画像 × 训练构成**

| 类别 | 零样本 G1 Success | 001 D3 训练 unique | 本稿 unique（E3 后） | 本稿 ambiguous | 混淆对暴露（E3 后样本数） |
|---|---|---|---|---|---|
| car | 45% | 68 | 517 | 90 | car→taxi 178；car→suv 215 |
| pickup truck | 52% | 356 | 700 | 75 | pickup→container 222；pickup→suv 194 |
| truck | 68% | 40 | 272 | 180 | truck→container 118 |
| suv | 71% | 884 | 700 | 4 | suv→pickup 220 |
| container truck | 82% | 1,401 | 700 | 28 | — |
| taxi | 86% | 420 | 400 | 16 | — |
| bus / ambulance / police car | 90% / 92% / 100% | 252 / 249 / 70 | 334 / 285 / 98 | 0 / 0 / 18 | — |

零样本 66 个失误行中仅 19 行的目标车与混淆车都曾出现在训练帧，修复只能靠类别级线索。

## Pending rulings（待裁定）

**2026-09-14，Owner：Acceptance。** 来源为实现报告 §11(a)…(e)、§0 计次口径及 §8 的表 J 裁定请求，
状态板同日交接；实现角色未把问题写入本节，本角色按原来源接收并在此答复。以下只追加既有 AC 的释义，
不覆盖首次接受释义，不新开 D/C/R 轮，不新增 AC。D3 `ACCEPTED` 与 engineering-v1 保持。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-4 修订 2 | 答复 §11(a)：表 B 的 G4 关系释义段固定接在词表段之后、Coordinates 段之前；非 G4 不插入。表 B 原段文字、四参数边界与 AC-4 修订 1 的 gold 隔离不变。 | `test:tests.test_eng_sft_evaluate.PromptTests.test_prompt_builder_cannot_see_gold_and_vocab_is_frozen`；`artifact:docs/evidence/P1-ENG-SFT-002-data-report.md` §11(a) | K4 | 2026-09-14 |
| AC-14 修订 2 | 答复 §11(b)及 J7 身份问题：表 J 的去重约束优先于名义配额；J5 仅一个 dynamic-target，用户 1/预筛 0；J4 九类，用户 4/预筛至多 5，不足额披露不回填。J7 是“#27 在执行域而整帧 bus 颜色 noun 被排除”的帧级证据；叠框对象可以是该帧被排除 noun 的其他 bus，但显示的 object_id、框和 S5 颜色必须指向同一对象，并与触发排除的 counterexample_object_ids 分列；同对象每层≤1按叠框对象计，不用触发对象替代。不是为满足配额挑选另一辆车或改变哈希序。 | `artifact:docs/evidence/P1-ENG-SFT-002-label-audit.md` §2/§3；`artifact:outputs/eng-sft/P1-ENG-SFT-002/receipts/audit-plan.json`；`test:tests.test_eng_sft_audit.SamplerTests.test_layer_quotas_and_uniqueness_are_deterministic` | K4 | 2026-09-14 |
| AC-3 修订 2 | 答复 §11(c)：当前八行 LEGACY_ONLY 按 AC-3 修订 1 保留灰区原因，diagnostic=GRAY_DEFINITE_PLUS_UNCERTAIN；group=LEGACY_ONLY 标示其评估去向。守恒表 group 保留去重前 v2 组 G3p，group_v1 保留原探针组，eval_row_id 指向实际 LEGACY_ONLY 行，disposition=LEGACY_ONLY；这三个组/去向字段不得混用。 | `artifact:docs/evidence/P1-ENG-SFT-002-legacy-conservation.json`；`test:tests.test_eng_sft_build.EvalSetTests.test_legacy_only_rows_carry_duplicate_key_probe_entries` | K4 | 2026-09-14 |
| AC-1 修订 1 | 答复 §11(d)：接受 S4 的 train/dev/test/d3 两两不交核对，作为既有输入完整性及来源声明的 fail-closed 校验。任一帧出现于两个 split，按实现请求使用 MANIFEST_COUNT_MISMATCH 失败收据并停止，不允许映射覆盖旧值；不改变 S4、集合或输入闭集。 | `artifact:docs/evidence/P1-ENG-SFT-002-data-report.md` §1/§11(d)；`artifact:outputs/eng-sft/P1-ENG-SFT-002/receipts/input-manifest.json` | K4 | 2026-09-14 |
| AC-14 修订 3 | 答复 §8：#20/#21 分别裁为表 J (ii) 上游标签缺陷，用户颜色「错」不改；对应帧全部 bus 颜色 noun 按表 A′ 已排除，不回写 S5、不另改 gold。表 J 的“受影响层复判”适用于修规则/重绘造成用户所判内容或入选样本变化；本次两帧的排除已生效、J7 只显示被排除样本，数据和图字节不变，故无需重建、重绘或复判。实现者须将该具名裁定及原判定/面板/排除证据绑定到闭合记录，保留原 AUDIT_FINDING_OPEN 历史；freeze 只放行已落实处置的 #20/#21，新增错/未判定/未裁定仍拒绝，不能靠删除原收据绕过。 | `artifact:docs/unity-test-log.md` 的 UT-P1-ENG-SFT-002-label-audit；`artifact:outputs/eng-sft/P1-ENG-SFT-002/receipts/audit-finding-open.json`；`test:tests.test_eng_sft_audit.ReceiptTests.test_open_finding_blocks_freeze`；`test:tests.test_eng_sft_build.FreezeTests.test_freeze_requires_complete_audit_and_precheck_receipt` | K4 | 2026-09-14 |
| AC-6 修订 2 | 答复 §0 计次口径：依账本，真实输入的对账/构建/freeze/package 入口累计≤8，失败也计；precheck 独立计≤3，不在报告同时列入构建计数又漏记实际预检。当前已报告 build 2次、precheck 1次；plan/prescreen/stats 不生成面板，不计 panels 的≤2次，不能借此免除其中实际调用的受限入口。§7 混淆暴露矩阵按生产报告明确的 E3 class+color unique 保留样本口径披露，与构思数字分列；既有取样不变，不为追平该描述性数字重建。 | `artifact:docs/authorizations.md` 2026-09-14 候选1信封；`artifact:docs/evidence/P1-ENG-SFT-002-data-report.md` §0/§7/§9 | K4 | 2026-09-14 |

**两条颜色裁定的逐项依据（只读工件核实，不是独立复核）：**

| 用户行 | 实际对象与源记录 | 裁定与处置 |
|---|---|---|
| #20 | audit-plan/panel-20 的 object_ids 为 Vehicle_Bus_color03；同帧 S3 为 OK、blocks=true，框与面板一致；S5 gray/VERIFIED。 | (ii) 上游标签缺陷；用户颜色错与 S5 VERIFIED 并列保留，沿表 A′ 排除该帧 bus 颜色 noun。 |
| #21 | audit-plan/panel-21 的 object_ids 为 Vehicle_Bus_color01 (1)，S3 为 OK、blocks=true，S5 也为 gray/VERIFIED；同帧 Vehicle_Bus_color03 是 TOO_SMALL、blocks=true（仍在 D 中），不是叠框对象。 | (ii) 上游标签缺陷；不是 #27 对象的第二次观测，也不是错贴 S5 字段的显示问题。#27 触发的是整帧排除，因而该帧仍符合 J7；不将一次判错外推到其他帧。 |

接受侧按输入清单定位 S3 两行/S5 两对象，并阅读已有面板及四个 gold 文件；这两帧在
train/smoke/select-eval/eval 中均无行。全域排除 train 25/test 316 仍标为实现报告数字，未在本轮重跑构建复算。
这只支持本次具名处置，不证明全部数据无错、框合格或新训练效果。

§11(e) 的预筛 #33 继续仅披露，不升级成用户语义核验；不因“同族”一词扩展 #27 闭集。
用户关于非纯色车/最接近颜色的想法已在 Unity 日志原文与 §6 保留为后续设计输入，
未选择新的匹配协议，本次不改表 A/B/G。若将来采用，须另行明确目标语义和验收并取得范围授权。

**下一步：Implementation** 落实以上释义、原收据保留及闭合记录，修正报告中“判定未回”、
“只有一次 build”与把 #20/#21 写成同一对象的叙述；随后在原信封内 freeze → package → 停点全套测试、
报告定稿与自证 → C1@K4。本轮未运行实现测试、未核对完整候选，不签独立 verdict 或 UNITY_NA。

**2026-09-18，Owner：Acceptance；K3 训练与预先验证方案答复。** 用户本会话要求
“审查实现提供的训练以及预先验证的方案”；问题来源为实现报告
`docs/evidence/P1-ENG-SFT-002-report.md` §5 P-K3-1…5。本次裁定 **ACCEPTED（以下合同释义）**；
其中 P-K3-4 的现有执行方案不满足预算边界，须按答复修正操作单和相应实现后再租机。
这不是新的设计退修，也不是稳定候选核对或独立复核：D3 ACCEPTED、设计退修2、K3 C/R=0/0保持。
用户已授权的5060诊断按独立信封执行，不作为K3通过证据；原始授权已从实现会话逐字补入账本。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 1 | 答复 P-K3-1，接受冒烟取法：仅冻结 smoke 的32行、不展开 oversample_copies，lr=1e-4、有效批16、30 epoch共60优化步；warmup=ceil(0.03×60)=2，随后cosine，调度在更新后推进。末步loss指第60步更新前该有效批的assistant token平均交叉熵；通过仍须loss<0.05且32/32 greedy输出经冻结parse后的状态等于gold，解析失败算错。末步更新后权重用于32行预测；冒烟adapter不参与选优，记录身份后可删除。未过即SMOKE_FAILED回接受角色，不借诊断或重试调低门槛、增加步数。 | `artifact:docs/evidence/P1-ENG-SFT-002-report.md` §5 P-K3-1；`test:tests.test_eng_sft_train.ScheduleTests.test_smoke_runs_exactly_sixty_steps_on_thirty_two_rows`；`test:tests.test_eng_sft_train.SmokeTests.test_smoke_needs_low_last_loss_and_all_states_correct` | K3 | 2026-09-18 |
| AC-10 修订 2 | 答复 P-K3-2，接受具名配方补齐：AdamW beta=(0.9,0.999)、eps=1e-8、weight_decay=0、梯度裁剪1；每epoch完整遍历展开多重集，ceil(N/16)步、末批保留；逐epoch以random.Random(f"{seed}:{epoch}")洗牌（epoch从0起），warmup=ceil(总步数×0.03)。当前N=5318，C1/C3各666步、C2为999步。损失为有效批assistant token的CE总和/该批assistant token总数，标签只含gold与im_end，不含换行、prompt、图像或padding；逐行模板标签数=独立gold计数+1，不等按TOKENIZER_MISMATCH停。base bf16、LoRA fp32、SDPA；LLM层内七投影按表H、ViT/merger冻结。micro-batch仅切分既定有效批与梯度累积，不能改变步数或归一分母；8×2是部署初值，不保证与其他切分逐位数值相同（dropout/浮点顺序），实际值随配方记录。报告以这些具体参数为准，不笼统声称整套实现等同HF Trainer默认。 | `artifact:docs/evidence/P1-ENG-SFT-002-report.md` §5 P-K3-2；`test:tests.test_eng_sft_train.ScheduleTests`；`test:tests.test_eng_sft_train.TemplateTests`；`artifact:docs/evidence/P1-ENG-SFT-002-train-summary.json` | K3 | 2026-09-18 |
| AC-10 修订 3 | 答复 P-K3-3，选优分数=(acc_unique+acc_ambiguous+acc_none)/3；每类按冻结441行选层集的gold状态分组，分子为解析成功且状态正确行数，解析失败计错，不使用框正确率。候选闭集C1/C2/C3；并列集为距最高分≤0.005的候选（不是传递式两两并列），精确分数比较，依次选epoch少、lr低者。只用本地选层gold，正式评估gold不参与选优，不重训。 | `artifact:docs/evidence/P1-ENG-SFT-002-report.md` §5 P-K3-3；`test:tests.test_eng_sft_train.SelectionTests`；`artifact:outputs/eng-sft/P1-ENG-SFT-002/receipts/selection-<job_id>.json`（job_id从回传收据运行时解析） | K3 | 2026-09-18 |
| AC-13 修订 1 | 答复 P-K3-4：接受持久化启动账、失败计次、提前6分钟保留回传/销毁余量和stopped_budget记录；不接受把逐行/逐步检查称为实例自动停费。≤8 GPU·h与≤6美元沿用户信封，安装、下载、预检、运行、A→B等待、异常处理、回传这七段均受同一累计边界约束。用户保持运行的选择仅在余额内；租机前操作单须给出绝对最迟结束时刻的计算、由用户在控制台销毁实例的动作及异常/未收到实现答复时同样执行的截止安排；到点不能无限等待回传或诊断。可沿用从创建时刻保守计时，但不得把它说成供应商精确计费。单GPU小时价只估算compute，须把实际报价中的存储/流量费用列清并在现有6美元内预留，不另生额度；费用不明则不租用该报价。min(8,6/小时价)−0.1只能作为compute层守卫，不能声称覆盖全部费用或全部阶段。版本漂移、设备、下载、次数上限沿原信封，不能用CLI绕过开关获得豁免。 | `artifact:docs/evidence/P1-ENG-SFT-002-report.md` §3/§5 P-K3-4（待修正）；`test:tests.test_eng_sft_cloud.LedgerTests`；`artifact:docs/authorizations.md` 2026-09-18候选2信封及实现会话补录 | K3 | 2026-09-18 |
| AC-7 修订 2 | 答复 P-K3-5：接受bundle生成空的code/tools/__init__.py，清单记source=null及生成说明、字节与SHA；不是伪造仓库源文件。python -B及包外工作目录用于避免生成额外文件；正式云端校验仍按AC-7修订1的两清单并集，__pycache__没有例外。5060诊断的smoke子集校验仅对诊断有效，不能替代正式作业的全包校验；K4冻结字节和清单不改。 | `artifact:docs/evidence/P1-ENG-SFT-002-report.md` §5 P-K3-5；`test:tests.test_eng_sft_cloud.PackageTests.test_code_manifest_lists_every_bundle_member_except_itself`；`test:tests.test_eng_sft_cloud.PackageTests.test_missing_or_extra_member_in_either_manifest_refuses_run` | K3 | 2026-09-18 |

**执行前修正与验证边界（既有合同及授权的落实，不新增AC或独立finding分级）：**

| 项 | 只读观察与处理 | 何时落实 |
|---|---|---|
| K3-P1 预算及停费 | cloud_runner的BudgetGuard只在阶段入口、预测行/训练步边界被调用；ensure_base、网格预检、安装环境及A→B空等无持续检查，也不调用实例销毁。报告§3“运行器会自己停”及Traceback后无截止地保留实例，不能保证用户额度。按AC-13修订1写出用户可执行的截止/销毁路径；单步或网络挂起也不能依赖下一次callback。保留现有守卫单测，但不能把它们描述为已经测试平台停费。 | 租机前；Implementation修正实现/操作单并给出对应证据指针 |
| K3-P2 自检信封落实 | 原授权只装peft/accelerate、复用探针环境及同版权重；报告§2裸pip命令可能解析并安装其他依赖。Implementation须先给出保持已有环境的受限安装步骤；缺依赖不能借自检自动下载整套云端requirements或权重。selfcheck当前只记录pins drift并不拒绝，用户回传后应由实现者说明实际版本差异，不能称“云端同版已验证”。自检读取域限smoke行/帧及校验元数据；可将现有subset校验所需成员作诊断运输副本，避免操作单直接复制整份训练/选层/评估包；不改原K4包。计次沿同一work目录累计，失败也计，不换目录重置。 | 5060自检前更新操作单；授权无需重问 |
| K3-P3 实测边界 | 34项无GPU测试覆盖纯函数与FakeEngine编排，不执行真实load_model、PEFT前反向、processor或CUDA。5060最多5步/micro-batch=1可以检查接口和adapter存读，但不能证明云端60步冒烟达标或5090/micro-batch=8可用。train_lora._assistant_loss_sum先产全序列logits再选assistant位置，故不能从LoRA参数量推断峰值显存；实际峰值/耗时由用户诊断及授权内正式作业记录。“几分钟/3–4小时/20–30分钟”均标估算，不能作为守卫的实测依据。默认micro-batch若调整，保留有效批16并记录；失败仍按信封计次，不新增免费云端探测。 | 操作单定稿与诊断回传解读；正式证据待K3 |

平台事实只用于解释既有预算边界：Vast.ai区分compute、storage、bandwidth，停止实例仍有存储费；
销毁删除实例数据并终止其持续存储费用。来源（2026-09-18查阅）：
[Vast.ai Pricing](https://docs.vast.ai/guides/instances/pricing)、
[Managing Instances](https://docs.vast.ai/guides/instances/manage-instances)。未核实任何具体5090报价。

**交接：** Implementation先落实上表并更新报告/代码束，用户按已入账信封做5060诊断，Implementation解读结果；
K3-P1落实后才租机执行既定A→本地选优→B。稳定候选自证后照常C1@K3→Review，本次不替代任何门。
本批接受后追加AC修订5行（累计11），新AC=0；未运行实现测试或GPU任务，未签发UNITY_NA或独立复核。

## Contract conformance（核对表）

**C2@K3 — 2026-09-18；Owner：Acceptance；结论：AC-7…13 全部满足，附未决关注项交 Review `R1@K3` 与 `UNITY_NA` 附议（本停点核对退回已用完，不再退回）。**
D3 `ACCEPTED`、engineering-v1 与 AC 原文/11 行追加修订保持；本轮不是设计退修或独立复核，未新增 AC、未运行测试、
未调用实现入口、未重评分。C1@K3 的四项退回（C1-K3-1…4）已由 Implementation 修正并自证（报告 §7/§8）；
旧 C1@K3 核对表由 git 历史保留。K3 C/R=2/0、C 退回 1，K4 C/R=2/2 不变。

**候选与读取范围。** 基线 = 复核文件 R2@K4 `passed_candidate`（运行时解析）；候选 = 本批 HEAD
（提交主题 `P1-ENG-SFT-002 C1@K3 退回项修正：续跑/A→B 包身份、选优收据绑定、自检数值边界与执行披露，交 C2@K3`，
SHA 运行时解析）。完整候选 diff 仍为相对基线的 18 文件；相对 C1 候选的增量为单一修正提交 6 文件
（`cloud_runner.py`、`verify_return.py`、`test_eng_sft_cloud.py`、报告、tests.log、状态板）。本轮重读该增量完整
diff、AC 与 11 行修订、报告 §6.1.4/§6.2.9/§7/§8 及直接关联的 `_prepare`/`Job`/`run_job_b`/`summarise`/`check_pins`
代码；用标准库只读核实：冻结闭集 8 文件磁盘 = 冻结收据 = HEAD = 基线 blob 逐一相等；回传 A/B 收据 6 个包身份
字段逐一相等，且等于本地 bundle/package 收据（代码清单 `65807e07…`、上传清单 `264839e5…`）；选优收据
`job_receipt_sha256` = 当前作业 A 收据现算 SHA（`02337fa2…`）；eval-summary 的 `job_b_receipt_sha256` = 作业 B
收据现算 SHA（`8982f204…`）；代码束 10 成员中 8 个与当前源码逐字节相同、`cloud_runner.py` 为修前 blob
（`c540d2c…`）、空 `__init__.py` 为 bundle 生成件；bundle 收据时刻与来源提交均早于修正提交（未重打）。

| 验收项 | 核对结果 | 理由与证据指针 |
|---|---|---|
| AC-7（含修订1/2） | 满足 | C1-K3-1 已修。`package_identity` 取全包校验 6 身份字段；`require_same_package` 缺字段或不等即 `LaunchRefused`。续跑在任何写入、跳过旧阶段、消费 adapter 前核对旧收据包身份、`env.json` 环境与已装版本（JSON 往返同形比较），不改写首跑 `package`/`pins`/`env.json`，只追加一条 `resumes`；作业 B 在建目录前核对 A 收据包身份（`_prepare` 的 `expected_package`）。具名测试：`JobTests.test_resume_with_changed_bundle_or_environment_is_refused_before_any_write`（生产路径改受束源文件→提交→重打合法新束，环境变化另测；断言旧回传逐文件不变、启动账不变、不重训）、`JobTests.test_job_b_refuses_job_a_from_another_bundle_before_creating_job`（不建 B 目录、eval 计次 0）、同包续跑成功路径追加断言（`resumes` 1 条、身份不变）。真实 A/B 无续跑（启动 6/8 均首次成功），身份相等只读核实为真。 |
| AC-8 | 满足 | 维持 C1 结论；修正提交未触及 `train_lora.py` 与 tokenizer/网格路径，收据与测试指针同 C1（train-summary.tokenizer_recheck/image_grid、PrecheckTests/GridTests）。 |
| AC-9 | 满足 | 维持 C1；零样本摘要未被修正提交触及，base+prompt v2、609 行、103 行解析失败保留分母不变。 |
| AC-10（含修订1…3） | 满足 | 维持 C1；配方/调度/掩码/选优代码不在修正 diff；selection 新鲜度修复只加拒绝路径，`select` 本身不改。 |
| AC-11 | 满足 | C1-K3-2 已修。`summarise` 要求选优收据 `job_id` 与 `job_receipt_sha256` 等于当前作业 A 回传，否则 `RETURN_HASH_MISMATCH`；具名测试 `ReturnTests.test_summarise_refuses_selection_not_bound_to_current_job_a`（部分 A 选优→续跑完成→旧选优被拒→重新 select→通过）。当前真实选优收据绑定当前 A 只读核实为真；「修后重算三份摘要逐字段相同」是实现者声明，本角色未复算，列关注项 3。 |
| AC-12 | 满足 | 维持 C1：签发日 `NOT_RUN(SFT_003_NOT_DONE)` 终态，摘要照录，零 SynDrone 消耗。 |
| AC-13（含修订1） | 满足 | C1-K3-3 已修：`run_selfcheck` 在计次与任何模型调用前要求 rows∈[1,4]、steps∈[1,5]、micro_batch≥1 且为真整数（拒 bool）；`TorchEngine` 构造同查；具名测试 `SelfcheckTests.test_selfcheck_rejects_out_of_range_values_before_counting` 覆盖 9 组越界值与 `TorchEngine(0/−1)`，断言计次文件不存在、引擎零调用。C1-K3-4 已修：§6.1.4 记已入账与接受侧裁定，§6.2.9/§7.6 区分阶段时长（合计 7,463.6 s）、作业 B 收据 2.89 h、末次 status 2.925 h、保守覆盖约 3.01 h 与账单 $1.72，D-2 写明为已发生流程偏差只披露不补证。残留措辞见关注项 4。账目对信封逐项核对在 §6.2.9（6/8 启动、2,573 行、$1.72）。 |

**交 Review `R1@K3` 的未决关注项（待核实主张，本角色不作 finding 分级）。**

1. 三处失败路径修复的红绿与覆盖：修前红/修后绿为实现者声明（报告 §8，原始输出未入仓）；请复核按通道对修复
   触及行定点核实，含 `rebundle_changed` 生产路径夹具确实改变合法代码束身份。
2. 历史证据与修后代码的版本区分：云端实跑为历史代码束（`cloud_runner.py` 为修前 blob），修后拒绝路径仅
   FakeEngine/纯参数测试覆盖、未在真实 GPU 运行；报告 §7.3 的区分声明本轮已只读核实（束未重打、身份字段相等）。
3. 「修后代码重算三份摘要与已提交逐字段相同」未由本角色复算（核对轮不调用实现入口）；复核可按报告 §7.5 用
   `verify_return summarise`（零 GPU，约 1 分钟）复算并用 AC-11 命令读判定。
4. 报告 §6.2.9 D-1 行仍写「待入账」，与同报告 §6.1.4 的「已入账」不一致（文档一致性小项；实质披露已落实）。
5. D-2 租前核价缺口为已发生流程偏差，只披露不补证；C1@K3 的 D-1…3 裁定保持。

`UNITY_NA` 申请：候选 2 零 Unity/Play/运行时改动，纯离线训练与评估；须复核角色在复核文件附议，本角色不预签。
功能门 `GATE_NOT_MET` 按原表 G 允许负结果交付；+26.6 pp 不得解释为纯定位能力、跨域、跟踪或 Jetson 改善；
本项仍未 `DONE`。修正后测试声明：focused eng_sft 91/91；停点全套 Ran 1247 / errors 9 / skipped 21，与基线
（1202/9/21）9 项 errors 逐项同名同因、新增失败 0，本角色只读核对 tests.log 计数与错误名单一致（未复跑）。


## Acceptance rulings（复判）

**2026-09-16，Owner：Acceptance；R1@K4 路由裁定，不消费最终通过 verdict。**
已完整读取本项 R1 复核文件、表 J/AC-14 及其修订、AC-5、原始授权、原用户判定和直接关联的
抽样/面板/闭合入口。未运行测试、抽样器或真实数据入口，不开 C3、不改 AC、不写复核文件。

| 复核文件 / 轮次 / finding | 裁定 | 日期 |
|---|---|---|
| docs/reviews/P1-ENG-SFT-002.md / R1@K4 / F1 | **维持 CLASS_1、BC-14、范围内必修。** 修复前的域遗漏评估侧 G3，合同确定抽中的 J3 #9–#11 未经用户判定，AC-14 与 AC-5 的冻结前提尚未成立。9月15日“先修代码，不重抽”保留缺口待裁定，未豁免合同；本次裁定须重抽并补判变化的3张。沿复核 F1 闭合要求执行，额度批准前不重跑 plan/panels 或重冻结打包。既有冻结收据与包保留为失败候选历史，不据此放行 K3。 | 2026-09-16 |
| docs/reviews/P1-ENG-SFT-002.md / R1@K4 / F2 | 保留本轮 SCOPE_GAP、非阻断，记入 implementation-status 账本 OPEN。本次只重打包相同冻结数据，复核已核包体远低于上限；不在此返工扩大到新输入/超限包。后续扩大包域或复用该入口处理可超限数据前，须承接“暂存区先校验体积、失败保留旧包”缺陷及回归。 | 2026-09-16 |
| docs/reviews/P1-ENG-SFT-002.md / R1@K4 / F3 | 保留本轮固定已归档输入条件下的 SCOPE_GAP、非阻断，记账 OPEN。本次不重跑 build，已有 predictions 已被独立核实存在且绑定，不将该缺陷宣称已修；未来重新构建、改变挂载/来源或复用可变输入入口前须承接必需预测文件缺失的 fail-closed 回归。缺失不属于获准可忽略输入，不改 AC-1 输入闭集。 | 2026-09-16 |

**F1 返工交接与证据保留（沿复核 §3/§5，不新增验收项）：**

1. 获用户额度且入账后，实现角色先保留旧计划、旧面板/收据、开放与闭合记录、冻结/包收据的可追溯副本，
   与旧候选对应；不覆盖唯一历史副本，不改原始输入。备份计入既有目录上限，不获额外磁盘额度。
   在现候选代码上运行 plan，按 R1 F1 已枚举闭集核对3张用户差异和10张预筛差异，提交抽样契约后生成面板。
2. 用户仅复判新 J3 #9–#11（the taxi / the bus / the container truck，各3候选）的状态与候选完整性。
   其余18张逐行核对 key/frame_id/surface/object_ids/原图与叠加图 SHA 相同才沿用原判定；不按 panel_index 单独转移判定。
   接受/辅助保留旧判定原文及旧图身份另作历史，当前机读判定在新3张回传前保持未完成，不把旧“对”嫁接到新图。
   #20/#21 原“颜色错”和 AC-14 修订3的具名处置保持；若出现新错或额外身份变化，停下回合同，不自行凑数。
3. 实现者只补看发生变化的预筛 #32–#41，其余19张满足身份/图字节一致条件时沿用并披露来源，
   预筛始终不替代用户语义核验。R1 要求的新10张加已看29张，按累计不清零口径申请上限39，不能仍称累计≤36。
4. 判定代录后 stats → close（重绑判定与面板，保留#20/#21原开放历史）→ freeze → package；
   成功路径需2次受限入口，不重跑 build/precheck，不改六份 jsonl、四份冻结 JSON 或训练/评估样本。
   报告、抽查与交集表随新计划同步。F4/F5 由实现角色按复核逐字补丁应用；若测试数量随补强变化，
   依最终日志如实更新，不机械写死 R1 的41例。复核§4第1–3项是非阻断补强建议，不提升为新 AC 或额外阻断 finding。
5. 修复自证后直接交回复核；候选和修前基线分别由 git 与 R1 的 round_candidate 运行时解析。
   开轮资格仍按 workflow §4.4；满足时走 R2@K4，不再经 C 轮。F1 的人工证据链按复核 NOT_MECHANIZABLE 定点复看，
   非阻断测试建议不另建停点。当前K4 C/R=2/1、C退回1、R返工1；第二次 REWORK_REQUIRED 后才冻结未闭集。

**F1 返工追加信封（下表保留提交用户时的实耗与申请；2026-09-16 用户已批准，见表后记录）：**

| 项目 | 当前实耗 / 上限 | 申请新累计上限及用途 |
|---|---|---|
| 面板生成 | 2/2 | 3（+1次；生成新计划面板；失败计数） |
| 真实输入对账/构建/freeze/package 入口 | 11/12 | 14（+2额度；余3次供 freeze+package 成功路径2次及1次失败余地；本批不重跑build） |
| 用户复判 | 0/1；首次21张 | 沿用现有1次，只新增看3张，累计唯一用户图片至多24；不追加复判次数 |
| 实现者预筛 | 29/36 | 39（+3上限；允许新看10张，已看29张不清零） |
| 判定代录 | 1/1 | 2（+1次，保留原文与历史并代录本次3张判定、重绑身份） |

单次入口≤5min桌面CPU/RSS≤1GB、面板单次≤5min；预检上限5、下载及AC-6目录上限不变。
模型/推理/训练/GPU/API/Play/正式ID/上传/发布仍为0，K3未授权。
**授权落定（2026-09-16）：** 用户在本接受会话对上述申请逐字回复“授权批准”，已入账同日
「批准 R1@K4 F1 返工追加信封」。四项申请上限生效；当前实耗入口11/14、面板2/3、预筛29/39、
代录1/2、precheck2/5、复判0/1，旧消耗不清零。现交Implementation按本节返工链执行；
本会话未执行入口或生成面板，用户新3张判定仍待返回；F1仍未闭合，不是K4通过。

**2026-09-18，Owner：Acceptance；R1@K3 最终通过轮消费与 DONE 裁定。**
已完整读取 `docs/reviews/P1-ENG-SFT-002.md` R1@K3 轮块（verdict、`passed_candidate` 机读行、AC 逐条表、
§0 方法、§3 findings、§4 注记、§5 动作、UNITY_NA 附议节、§7 边界自查）与直接关联的回传/收据/摘要绑定；
通过候选后无实现漂移（其后仅接受/复核两批文档提交，`tools/`/`tests/`/`controller/`/`Assets/`/`config/` 零改动）。
本轮不运行测试、不调用实现入口、不写复核文件。

| 复核文件 / 轮次 / finding | 裁定 | 日期 |
|---|---|---|
| docs/reviews/P1-ENG-SFT-002.md / R1@K3 / F6 | CLASS_3、依据 `BC-13` → 实现错误（非阻断文档措辞）。四条逐字补丁交 Implementation 下一次提交应用到 K3 报告（A1 写权限），不改数字/哈希/ID/disposition、不重跑任何入口；应用后无需复核轮，接受侧收工时只读核对。 | 2026-09-18 |
| docs/reviews/P1-ENG-SFT-002.md / R1@K3 / F7 | 保留 `SCOPE_GAP`、非阻断，记入 `docs/implementation-status.md` 账本 `OPEN`。已归档 budget.json 用缺省流量值、实例已销毁，触发状态不可达；本批不纳入范围。后续复用 `budget-plan`/`budget-init` CLI 前承接负值 `LaunchRefused` 拒绝与 LedgerTests 具名回归。 | 2026-09-18 |
| docs/reviews/P1-ENG-SFT-002.md / R1@K3 / F8 | 保留 `SCOPE_GAP`、非阻断，记账本 `OPEN`。真实 A/B 看门狗从未触发、需新云端消耗才可达，且截断收据仍 fail-closed；本批不纳入范围。后续复用看门狗/finalize 路径前承接进程内锁或唯一临时名修复与并发写回归。 | 2026-09-18 |

**DONE 裁定（三证据，engineering §11 / workflow §4.6）。** 候选 2：实现者证据（K3 报告 §6/§7/§8、三份摘要、
tests.log 1247/9/21 新增失败 0）+ 独立复核 R1@K3 `PASS_WITH_NOTES`（AC-7…13 满足、红绿与复算核实成立、
无阻断、无 `RED_LINE`）+ 候选 2 `UNITY_NA` R1@K3 正式附议成立。候选 1（K4）三证据已于 2026-09-18 消费
（R2@K4 + `UNITY_NA` 附议 + 用户 OFFLINE_VISUAL_CHECK 21/21）。两停点均闭合、AC-1…14 全部满足
（AC-12 为合同内 `NOT_RUN(SFT_003_NOT_DONE)` 终态）→ **工作项裁定 `DONE`**，Gate board Overall 同批改写。
合同 §6：`GATE_NOT_MET`/`INFERIOR` 不阻止 DONE、不授权追加 run；剩余云端额度随 DONE 作废、不迁移。
未闭条目随 DONE 列出：F2/F3/F7/F8 `SCOPE_GAP` `OPEN`（implementation-status 账本）、F6 补丁待应用。
机械归因：F6 `BC-13` → 实现错误 1（CLASS_3）；F7/F8 `SCOPE_GAP` → BC 缺失 2；`IN_SCOPE_NO_BC`/`上轮漏检`/
`上游漏检`/`RED_LINE` 均 0。计数：K3 C/R=2/1、C 退回 1、R 返工 0；K4 C/R=2/2 不变。
本裁定不主张跨域/跟踪/Jetson 能力；+26.64 pp 只是对零样本 prompt 的配对对照。


## 决策记录

**2026-09-18 候选2执行授权入账与AC-12一次性分支裁定。** Owner：Acceptance。
用户逐字“授权签发”，并补充“6美元，租用5090，预计能使用8小时（0.5-0.6$/h）”，均已记入账本
「签发候选2（K3）执行信封：5090、8 GPU·h、6美元」。候选2默认Unity分支设备为云端单张RTX 5090，
累计≤8 GPU·h、GPU租金总额≤6美元（两项同时约束，先达即停）；总启动≤8及§5各阶段子上限、
指定base权重一次/pip依赖、私有上传≤0.3 GB和目录上限生效。小时单价仅记用户估算，不主张已核实报价。
Implementation先交源码/无GPU测试/代码束/操作单，用户随后按§2/§7顺序执行云端；接受角色不代跑，
不改K4冻结集。本次仅落实既有合同与用户设备/额度，不新增AC或轮次；未执行任何入口或发生费用。

AC-12按签发日2026-09-18裁定：003为PROPOSED_D2且PAUSED_BY_USER，未DONE，前置不成立，
**NOT_RUN(SFT_003_NOT_DONE)** 为本候选跨环境分支终态；SynDrone评估/推理/GPU/上传为0，不等待003。
实现摘要须照既有AC-12记录终态/原因，001关闭与003暂停保持；后续003恢复不自动重开本分支。
K3进度仍为未开始，C/R=0/0，候选1的UNITY_NA不延伸K3；F2/F3 OPEN和两条设计输入保持。

**2026-09-18 K4 最终通过轮消费与候选 1 收尾。** Owner：Acceptance；按 workflow §4.6 / engineering §11
消费 `docs/reviews/P1-ENG-SFT-002.md` 的 `R2@K4 PASS_WITH_NOTES` 及候选 1 `UNITY_NA` 正式附议。
通过候选从该文件最近的 `passed_candidate` 运行时解析；本次核实其后仅复核/状态文档提交，无实现漂移。
实现报告 §15、停点日志、独立复核 R2 §1/§2 与用户离线判定/正式附议三类证据齐备：
**K4 候选 1（AC-1…6、AC-14）验收通过；整个工作项仍未 DONE，K3（AC-7…13）未执行且未授权。**
D3 ACCEPTED 与 engineering-v1 保持，不重开 C/D/R，不改 AC 或历史核对表，不自签独立 verdict。

F1 已由 R2 核实闭合，F4/F5 已应用；F2/F3 保持 SCOPE_GAP / OPEN，触发条件沿复判与缺陷账本。
归因与四项度量、全部 R2 注记和两条设计输入统一记录在 `docs/implementation-status.md`
「P1-ENG-SFT-002 — K4 候选 1 收尾与待授权 K3」，本段不另建一份缺陷账本。
信封内执行归因：修复抽样域后依用户2026-09-16追加信封重绘、补判3张、补看10张及重绑闭合，
再 freeze/package 各一次；入口11→13/14、面板2→3/3、复判0→1/1、预筛29→39/39、代录1→2/2，
precheck2/5不变；build/precheck与冻结数据未重跑/改写。该归因消费R2按收据核实结果，本会话零入口消耗。

**下一步仅为用户决定候选 2 执行信封。** 按§5默认Unity分支申请：云端24–48 GB单卡、累计≤8 GPU·h；
零样本≤2次、冒烟≤2次、训练≤4次、正式评估≤2次，同时总启动≤8（均含失败/中断）；Unity推理≤4,264行；
base权重一次（约4.4 GB）及pip依赖、私有上传≤0.3 GB、云盘≤20 GB、本地及回传目录沿§5；租金上限及币种待用户填写。
实现角色交付候选2源码/测试与操作单，用户执行云端作业A/B；API/Unity Play/正式ID/公开发布=0，不包含Jetson。
本段只是把既有申请提交用户，不授予额度。AC-12严格在签发候选2信封当日判定；003当前暂停且未DONE，
若签发当日仍如此则记NOT_RUN(SFT_003_NOT_DONE)，SynDrone额度为0、不等003，本日不提前签发其终态。

**2026-09-16 接受侧交接核实与 C2-4 用户决定补录。** Owner：Acceptance；仅维护授权账本、
本决策记录及状态板，不重开 C 轮、不修改既有 AC 或 C2 核对结论。已只读核实原始问答，
用户 2026-09-15 所选“先修代码，不重抽（推荐）”及其问题/说明已逐字入账。
该决定保留窄域抽查的证据缺口交复核核实，不等于接受 AC-14 豁免或认定证据充分。
本机尚无本项独立复核文件；当前下一动作仍为 Review 核实开轮资格、候选与未决项。

信封内执行归因：实现报告 §13 记载 C2 修复触及冻结评分代码，继而重 freeze/package 各一次，
入口从 9/12 到 11/12，precheck 仍 2/5，面板 2/2、复判 0/1；这是实现者报告的执行事实，
本次没有重跑、独立验证修复或消费通过 verdict。C2 表仍记录其当时核对候选；复核当前候选应按提交主题
`P1-ENG-SFT-002 C2@K4 返工交接：重冻结重打包完成，候选交 R1@K4` 在 git 历史运行时解析，
基线沿核对表；完整修复与证据见报告 §13，不将旧 C2 表当作对修后代码的新核对结论。
报告 §13 关注项 2 声称 §0 已清理旧计次文字，但 §0 仍有“待接受/辅助角色补记授权账本”及
≤8/≤3 的旧口径；此文档差异随交接交复核核实，本角色不代改实现证据，也不新增 finding 分级。
K4 C/R=2/0、退回1，K3未授权；001关闭、003暂停，均不改变。

**2026-09-15 C2@K4 核对与追加授权补录。** Owner：Acceptance；写入提案、授权账本、状态板及正式设计失效进度指针。
C2 按最新核对表附 C2-1…5 与 #27 关注项交 Review，不第二次退回、不增 AC、不签独立 verdict；设计退修2、K4 C/R=2/0。
原实现会话用户所选“加到 12 次，预检加到 5（推荐）”及问题/选项说明已核实转录；信封只更新累计入口与预检上限。
信封内返工归因：第三次 build 为 C1 对账/失败路径修复后重建，第三次 freeze/package 绑定修正后的冻结评分源码及清单，
累计入口9/12；precheck仍2/5，未重置消耗。此为执行归因，不替代复核依据列的最终返工归因。
正式设计只同步进度，合同版本不变；零实现测试/模型/Unity/数据加工，旧里程碑及范围外缺陷账本无新结论。

**2026-09-14 实现期合同裁定与授权补录。** Owner：Acceptance；范围为提案、授权账本、正式设计和状态板，
零实现写入。待裁定新增六行 AC 修订（AC-1/3/4/6 各一，AC-14 两行），新 AC=0；
D 设计退修2、C/R仍0/0。#20/#21 按表 J (ii) 分别处理，不需要新图或用户复判，闭合记录仍由实现交付。
tokenizers 原始 AskUserQuestion 问答已只读核实并逐字入账，补录不扩展其他下载或 K3 信封。
信封内重试归因：第二次面板用于修正 J3 class-only 域与 J1 弱类顺序，属实现纠偏，累计2/2；
第二次 build 为补齐 AC-6 描述性混淆暴露矩阵，累计2/8；均不新增额度，不将其冒充已独立验证。

**2026-09-13 数据选择与补采成本评估（用户要求；建议性，非合同变更）。**

用户请求：“好的，那这个数据选择的有没有问题？要不要补采一些？评估一下补充采集的成本”。
Owner：Acceptance；只读现合同、旧资产盘点、采集与处理收据、颜色诊断和相关文献。结论：现有数据值得用于首轮受限协议实验，
但没有证据保证规模充分或效果达标；不建议为启动实验重复原七锚点巡览。追加投入优先解决独立评估和定向覆盖，不能以增加连续帧替代。
本段不新增 AC、不改变已接受取样/划分、不重启旧采集或003，也不把本次讨论记为资源授权。

| 数据选择判断 | 事实与影响 |
|---|---|
| 三态构成方向合理，样本数不等于独立信息量 | 表E为4,907条不同图文样本、3,198张图片；歧义411条复制两份后才是5,318条训练样本。约75.3% unique / 15.5% ambiguous / 9.2% none可供首轮实验，不是经实验确定的最优配比。2/5帧间隔在5Hz段仅0.4/1秒，仍可能近重复；ASSET盘点中的两种布局共用101辆目录车。 |
| car补强可能学到简化目标车捷径 | car unique 517中350为同一个动态目标车，占67.7%；目录普通车仅167。保留目标车符合工程用途，但不能将其等同于多种普通轿车的覆盖。优先新增不同目录车实例/外观及car与taxi、suv等同框的可判定样本。 |
| 多候选覆盖偏窄 | 歧义411条中truck180、car90、pickup75；suv只有4，bus/ambulance为0。d7显示集合中没有四候选行；选层歧义仅41条，gold长度支持的都是两候选；评估有三候选。建议的补充重点是新的候选组合与三/四候选场景，不是再次复制现有411条。 |
| 标签比帧数更值得优先核实 | S5只有37辆颜色VERIFIED，且#27已有反例；框来源为amodal投影，尚无S6全面人工审计。颜色诊断指出五帧选择上限、双色车及色带/组约束问题，重复同路线不能保证改善。现合同的有限用户抽查应先完成；若扩充颜色标签，需独立的本地标注/版本合同，不能回写旧证据或自动把其余56辆当作可靠颜色样本。 |
| 当前test适合作回归，普适性证据不足 | 配额参考了已看过的test失误；G1的210行中180行目标曾在训练帧出现，G2的49行仅涉及7个对象。不是声称同帧泄漏，而是对象/环境相关及评估适应风险。新数据若用作独立评估，应先按整布局/会话隔离；若又拿它改配额，就不再是未触碰的最终留出。 |

定向补充的建议顺序：① 新布局中三/四候选、普通目录car及相似异类同框；② 查询类确实不存在、但存在易混类别的hard-none；
③ 可靠颜色对照和尺度/视角变化。遮挡或过小而无法确认的目标不能直接标none；“两个同款车中哪个是之前跟踪对象”仍需历史身份输入，
本次补静态图不会解决。可先规划150–300条新留出图文样本作诊断；这是估算规模，尚未测可得率，也不足以单独确证小幅提升。
是否另留训练部分须在采集前决定；新增Unity布局检验的是场景变化，仍不能替代另一渲染域或真实图像评估。

成本依据与估算（不含002本来就要付出的训练/实现成本；人时与机器等待分开）：
- 已测：旧七个有效会话共19,986帧、954MB，覆盖89/101辆车；全部可达锚点已用。
  来源：`docs/evidence/P1-VLM-DATA-002-stage-a-implementation.md` §19–20。
- 旧计划值：约12分钟/会话，八会话约1.6小时，并非已测端到端工时。
  来源：`docs/proposals/P1-VLM-DATA-002-grounding-survey-acquisition.md` §5。
- 已测：旧S1/S2预检13.9分钟、S0–S5全量处理39.4分钟；这是旧数据链单次成本，不是新方案报价。
  新帧是否需重算全部划分/目录、能否隔离加工尚待设计，不能按新增帧数机械线性外推。
  来源：`docs/evidence/P1-VLM-DATA-002-S0-S5-pre-audit-upper-bound.md` §4。

| 选择 | 增量资源与人工（规划估计，非授权/实测承诺） | 判断 |
|---|---|---|
| 保持现数据，完成现合同抽查再做首轮 | 新Play/新增归档为0；现合同用户≤24张，按每张30–60秒约12–24分钟首次看图，不含争议处理。更广的100–200张审计约0.8–3.3人时，另需面板/标签规则及复核，超出现信封 | 推荐当前先走；可先发现标注问题，不因总量焦虑补采 |
| 原路线再跑七会话 | 若沿用旧量级，约2万帧、约1GB归档；按旧计划约84分钟Play，加准备、处理和验证，至少半天日程余量，发生返工另计 | 边际多样性有限，不推荐 |
| 复用现Unity资产，改2–3个布局/采集配置做定向小批 | 假设每会话约2,500–3,000帧，约5,000–9,000帧、0.24–0.43GB归档（按旧954MB/19,986帧比例）；派生件与重算目录另计。场景/配置及合同准备约4–12工程人时，接入/验证约4–12工程人时，共约1–3个8小时工作日；用户Play及准备约1小时，加100–200张核验约1–3小时，用户合计暂估2–4小时。核对/独立复核的排队与返工日历时间另计 | 若补采，优先此项；以上以既有模型、渲染器、采集工具可复用为前提，不保证150–300条合格独立样本产率，须小规模先验可得性 |
| 另一个虚拟环境作独立评估（暂停的003） | 003已探测Town01下载4.98GB，申请磁盘≤12GB；按20/50/100Mbps纯传输约33/13/7分钟，未计服务器和解包。适配、标签核验与K4工作仍未完成，下载时间不是总成本；现≤400行与CPU≤15分钟是申请上限，非试读实测 | 对跨域问题比重复Unity扫视更直接；只评不训，需用户决定恢复，不能自动动用 |

以上Unity补采在复用现有电脑与资产、无采购/API/云GPU时可不产生额外服务租金，但人工和机器占用不为零；电费未估。
若新增样本入训，三配置同epoch/分辨率下的训练部分可先按有效训练样本数比例估算：新增1,000条约增加18.8%的样本呈现量；
这不等于总账单增加18.8%，且当前GPU时长本身尚未实测。新渲染器、新资产制作、可见框工具或端到端身份数据不在上述1–3天估算内。

文献只支持补充维度，不给本项目所需样本量或工时背书：[GREC](https://arxiv.org/html/2308.16182v2) §2–3明确覆盖零/一/多目标并评完整集合；
[SynDrone](https://arxiv.org/html/2308.10491v1)的多城镇/高度与真实数据实验说明应直接检验域差异，不能由同场景加帧推出迁移。
综上，保持002有限实验定位；若用户希望先加强结论可信度，优先独立评估小批。后续若采集/标签/取样范围发生改变，先形成可审查变更与独立信封，
不得消费已关闭DATA-002的余量或把新帧直接塞进002已接受的数据合同。本轮只写建议性记录与状态指针；门、额度、D/C/R计数不变。

**2026-09-13 用户要求的价值与意图对照（建议性评估，非新 D/C/R 轮）。**

用户请求：“另外评估一下这个方案有没有意义，对原有的意图有没有偏离。可以查询相关文献作为参考”。
结论：本项有受限三态视觉指称与工程数据链的价值，符合用户后续授权收敛的方向；对长期目标只完成一块离线子任务。
保留 D3 `ACCEPTED`，不视作优先级、效果或部署可行性的证明；不新增/改写 AC，不签发执行授权。

| 意图及仓库依据 | 本项能回答的范围与剩余距离 |
|---|---|
| 工程首版“语言选目标→SOT接管→持续跟踪”（账本2026-09-07工程任务描述；正式设计§1） | 三态、解析与选框为前置组件；没有VLM→SOT接入或闭环验证，探针完成不等于系统复现完成（账本2026-09-12方向四项定局已说明）。 |
| “有一定普适性”“训练一个环境、验证全新环境”（账本2026-09-12训练线方向讨论） | AC-12可以NOT_RUN后完成002，故跨域目标被后移；这有用户“不等”授权，但不等于该目标已达成。Unity→SynDrone改善只支持这一对合成域与这一模型/协议上的迁移，不能推出真实数据训练或真实部署会改善。 |
| “两个一样的车里面分辨出哪个是本来在追的车”（同一账本条目） | 明确未覆盖：模型输入没有历史目标模板/轨迹/身份上下文，三态标签不监督历史身份；本项只能枚举匹配候选。若当前观测与描述无法区分两个对象，增加SFT也不能补出缺失身份信息。 |
| Jetson 8GB部署与个人工程能力（project-background.md） | 可积累数据构建、LoRA、评估与失败处理能力；LoRA不把2B基础模型变小，云端训练成功不证明端侧内存、时延或多组件并行可用。 |
| 旧教师语言蒸馏与系留正确身份跟踪主张（正式设计§1；PROJECT_BRIEF） | 本项没有教师、matched-template对照、控制实验或C_track证据，无法支持这些主张；这是已授权延期后的工程子任务，不能称为蒸馏研究的完成。 |

价值判断与风险（本段是分析，不作为新验收义务）：
- 任务有依据：GREC将视觉指称扩为零/一/多目标，采用完整集合成功与无目标准确率；本项三态与集合F1方向合理。
  但本项ambiguous是候选多解，不是置信度校准/视觉不确定性；灰区主要被排除训练，不能把协议达成写成“模型知道自己不知道”。
  见 [GREC技术报告](https://arxiv.org/html/2308.16182v2) §2–3 与 [RECANTFormer，EMNLP 2024](https://aclanthology.org/2024.emnlp-main.1214/)。
- LoRA是SFT可采用的参数更新方式，既不与SFT互斥，也不自动保证泛化或模型压缩；协议适配是合理用途，具体效果待同版prompt-v2基线验证。
  见 [LoRA](https://arxiv.org/abs/2106.09685)。文献合理性不构成本项2B模型效果或资源实测。
- “词表靠prompt”是任务定位，不能解释为训练过程隔离类别学习：训练仍以类别/颜色短语条件化框与状态，LLM层LoRA仍可能学习Unity关联。
  同一场景帧/对象相关性和按已看test失误设计配额，使现有test更适合作工程回归；SHA隔离不等于全新环境或独立语言泛化验证。
- 609是评估行数，G1∪G2为259、G3为48、G5为100；功能门没有unique绝对Success下限，非劣仅约束相对base的点差。
  因此“GATE_MET且NON_INFERIOR”仍可能是较低绝对选框率；目标车t子组不入门，不能从这些门推出跟踪播种可用。
  DONE允许报告负结果，对实验交付合理，但后续接入应根据实际结果决定，不机械消费DONE作为能力通过。
- “合成域A→B提升”不逻辑蕴含“真实域训练/部署有效”。[SynDrone原论文](https://arxiv.org/html/2308.10491v1) §4.1/表7实际评测真实数据；
  [Domain Randomization](https://arxiv.org/abs/1703.06907)也用真实场景验证迁移。二者支持合成数据路线的可行性，不能替代本项域外证据。
- 身份问题的研究输入不同：[SiamRPN++](https://arxiv.org/abs/1812.11703)以模板和搜索区匹配，
  [车辆Re-ID，ICCV 2017](https://arxiv.org/abs/1708.03918)结合外观与时空信息；这些例子说明需要身份条件，不预断言任一方法能解决同款车的不可观测情形。

建议保留002为一次有限协议适配实验，不继续围绕同场景配额扩大调参；用现合同中的prompt-v2对照判断LoRA实际增量。
跨环境评估可后做，但在其完成前只称Unity内适配；长远重点应回到VLM→SOT接入、错误播种/人工确认和设备可行性。
若用户改选“最短工程闭环”而希望prompt-v2已足够时取消后续训练，或把跨域改为必做，则须先由用户改变当前合同/优先级；本次未执行该变更。
本轮仅只读文档与文献，未运行模型、数据处理或实现测试，未新增实现/数据资产；当前执行额度仍为0。

**2026-09-13 接受侧 D3：`ACCEPTED`（用户 §4.2 (a) 处置后的正式落定，非第三次退修）。**

Owner：Acceptance；范围：本提案、正式设计 §1、状态板。消费账本同日「查看accept结果并修正」所记录的保留范围处置；
本轮用户另明确「开始正式裁定」，只启动本次设计裁定，不视作候选 1/2 执行授权。
**裁定本工作项走 `Workflow: engineering-v1`，自本次 `ACCEPTED` 生效。** 本项是已获用户指定的独立离线数据/训练工程任务，
不改变运行时安全合同、旧研究主指标、硬件目标或公开发布范围。任务合同 = §1…7、AC-1…14 与上述首次接受释义；
表 G/H 与本项表 L 准入/描述性判据落定。§8 试读记录是尺度依据，不是实现证据或独立复核；§5 仍为申请信封，实际额度为 0。

| 上轮缺口 | 本轮认定与理由 |
|---|---|
| AR2-1 | 闭合。d7 `keyf` 对灰区返回 surface，`hk` 补齐五元组；`station_key` 实取 S3、浮点原值、包内 frame_path、eval-row/legacy 字段均在源码及留存测量中。输出为训练 4,907 distinct / 5,318 多重样本、选层 441、评估 601+8=609、legacy 405 条且 unmapped=0；并集 3,968 帧 SHA 全绑定，58.1 s / RSS 389 MB。接受609更正；脚本输出标题残留“610”不是实际行数。按 AC-2/3/5/6 首次释义消除序列化与计数口径歧义。 |
| AR2-2 | 闭合。表 H 已删除两字符串外推，改为本地四份实际 gold 的同版 tokenizer 逐条预检与绑定收据，云端仅重算训练/冒烟；152为拒绝阈值。AC-4/5 首次释义明确共享函数所在冻结模块、四文件闭集与过期收据拒绝。当前未测token数，不把未来预检当作已通过；下载须候选1独立授权。 |
| AR2-3 | 闭合。K4数据包不含K3源码，smoke由K4 build生成；K3再产代码束，两份清单绑定回传。frame_path冻结前写定，package不改jsonl；AC-7/12首次释义使两份清单按并集校验、条件扩展不改写K4清单，保留K4→K3及K3源码diff开轮资格。 |

保留 AR1-3/4 的用户有限抽查与不等待003决定；AC-14 首次释义把表 J 已点名的 G4、目标车与 #27 取样域展开为闭集，
未扩大用户看图上限。已知限制仍为 amodal/UNVERIFIED gold、#27、S6未审计、行级CI描述性、test已被探针看过、
对象重叠与目标车子组不入门；ASSET F8不在本项使用，不记release。表 G 未达功能门或非劣门可如实报告并完成工程交付，
不自动追加训练；不据本轮设计接受宣称任何效果成立。原001关闭、003暂停和旧里程碑状态不变。

只读证据来源：`/private/tmp/claude-501/-Users-zc-TetheredDroneTracking/d627bd45-7483-4be3-a928-898e1ee08779/scratchpad/`
中的 `sft_d7_measure.py` / `sft_d7_out.txt`，连同本提案完整正文、D1/D2裁定、授权账本、正式设计、工程继承清单与
ASSET盘点/既有直接关联函数；d5/d6来源沿前两轮。没有运行试读脚本、tokenizer、实现测试或模型，没有加工正式数据，
没有改实现代码或写复核文件。首次接受后同步正式设计 v0.3.40。

设计退修计数保持 **2**，C/R **0/0**。下一步只申请候选1：实现范围限§2候选1，桌面CPU对账/构建/冻结/打包累计≤8次，
每次≤5min、RSS≤1GB；面板≤2次（每次≤5min）、用户≤24张唯一图片首次判定+≤1次受影响层复判、实现者预筛≤36张、
代录1次；指定revision tokenizer四文件下载1次（预估12MB、目录硬上限20MB）、预检≤3次；目录上限见AC-6。
候选1仅生成本地上传包，不上传；权重/模型推理/训练/GPU/API/Play/正式ID/发布=0。信封获得用户逐字授权后交实现角色，
至K4须自证→接受侧C轮→独立复核及UNITY_NA附议；K3执行另行授权，当前不启动。

**2026-09-13 接受侧 D2：`REVISION_REQUESTED`（第二次设计退修；上交用户，不自动交构思 D3）。**

Owner：Acceptance；范围：本提案裁定与状态板。完整读取 D2 正文、AC-1…14、D1 退修、最新两项授权及 d6 源码/留存输出，
与前轮已读 d5、正式设计和工程继承限制对照。表 J 的用户 ≤24 张与 AC-12 不等待003均已有授权，不重复询问。
本项尚未 `ACCEPTED`，工程轨道不生效，AC/schema/尺度、配方和信封不冻结；正式设计保持原状。

| D1 条目 | D2 回应认定 |
|---|---|
| AR1-1 | 训练池七族、层定义、none轮转、分目录计额及实测/投影分列已回应；d6确有序列化输出，保留训练/选层计数。仍有试选与现合同不一致（AR2-1），不能整体声称“同算法、同schema”。 |
| AR1-2 | 训练标签可上云、评估gold留本地、包成员/manifest与收据先后已补；保留方向。token证明不足（AR2-2），完整包与两停点依赖冲突（AR2-3），尚不能按字面执行。 |
| AR1-3 | 表J/AC-14主要回应：有限风险分层、用户判定与AI预筛分开、错误阻止冻结及回合同路径；不要求扩大用户24张上限。§7的K4“AC-1…6”应同步含AC-14；“冻结前完成抽查”须按已选用户行判定齐全执行，未判定不等于无错，预筛不替代用户核验。保留其描述性、覆盖有限及不确定单列的限制。 |
| AR1-4 | 表L/AC-12主要回应：授权时一次判前置、不等待003、逐项配对/小分母NA、机械结论及单一评分实现；不重启003。本项若日后接受，SynDrone按表L/AC-8的数据集网格条款执行，表H的Unity网格句须同步限定Unity，不能覆盖表L。当前未测003的schema/规模不冻结。 |

**剩余缺口闭集与保留范围时的处理建议：**

| 编号 | 问题与可定位依据 | 处理建议（待用户处置后落定，不是执行授权） |
|---|---|---|
| AR2-1 | **取样/序列化与试读证据不一致。** 表D′把G3′键写成M对象ID串，d5 `keyf`（行95）却对 `gray_dpu` 返回surface；两者会改变准入分组和哈希次序，不能把d5的50行/legacy/并集数字直接作为D2该算法的证明。d6 `sample_rec`（行128–134）固定 `station_key=None`，且浮点框逐值round至6位；表C却要求S3 `station_bin.key`，未规定该浮点变换。其877 B与3,300,747 B是该临时表示的测量，不是现合同全部字段的测量。d6未构建完整610行评估集，正文也明确尚无其序列化实测。此外 `(h,frame_id,key)` 不能消除同帧同目标的class/color unique并列：三项全相同，仍依赖未冻结的先后顺序。 | 推荐维持d5已经核对过的G3′ surface键，避免为文档补全改变评估定义；若保留新键，必须重新只读核对完整评估选择、守恒与图像并集。明确class/color并列次序；按最终表C实际读取station_key，浮点存储口径明确且不改gold含义，再补对应序列化测量（含完整eval-row及legacy字段）。原d5/d6数字保留来源标签，不回写或冒充新测量；不能将缺schema/尺度试读的义务整体后移至已冻结合同的K4生产构建。 |
| AR2-2 | **表H两条字符串检查不能推出全称token上界。** `tok("0123456789")`长度和两组数字列表的长度差只验证那些输入；合同未证明任意0…1000坐标在JSON上下文中的分词长度单调，也未固定special-token/模板开关。即使这两条都通过，逻辑上仍不能据此断言所有选层/评估gold都短于“全1000骨架”。本轮未运行tokenizer，不声称该型号实际失败；问题是所写证明条件不足，失败即停只能拦住检查失败，拦不住错误外推。 | 推荐取消两例外推，改成同版tokenizer对实际本地gold的长度预检收据，绑定gold文件、序列化函数、tokenizer revision及计数开关；评估gold仍不上云。如果继续坚持本地零tokenizer下载，则给出经完整tokenizer规则核实的保守界和覆盖的有限输入闭集，云端核对该规则/版本与界，而非抽查两个字符串。任何新增下载位置/额度须后续用户信封明确；152保持拒绝阈值，不能因过不了预检而自动扩长或截断。 |
| AR2-3 | **K4验收依赖尚未交付的K3代码。** AC-5在K4要求真实 `package` 产出表K完整闭集，K中包含 `train_lora.py`/`cloud_runner.py` 与smoke.jsonl；§2却将这些训练/云端代码放在候选2，§7规定K4通过后才交付候选2源码。K4因此无法按当前候选划分完成AC-5。表C仍列旧版较小的upload清单，与表K/AC-5也不一致。包帧改名为 `frames/<sha>.jpg` 后，盲行最终路径与冻结前后SHA的关系仍须写清；不能通过打包时静默改盲行而同时声称字节与冻结收据相等。 | 推荐保留K4→K3：K4交付冻结数据/盲文件、数据清单和打包器的无模型验证；完整含训练源码的可执行包在K4通过、候选2代码存在后生成，并归K3验收。逐项标明AC-5与AC-7的证据时点，表C/K保持同一清单定义；包内最终frame_path在冻结前确定，或明确独立运输映射及其绑定，原冻结字节不暗改。不要把全部训练代码前移K4后仍无条件承诺新的K3复核轮；复核开轮资格保持原规则。 |

本轮只读证据来源：d6目录 `/private/tmp/claude-501/-Users-zc-TetheredDroneTracking/d627bd45-7483-4be3-a928-898e1ee08779/scratchpad/`
中的 `sft_d6_measure.py` / `sft_d6_out.txt`；d5目录及文件见D1读取范围。临时源码只用于定位，非正式实现或冻结工件。
未运行试选/序列化/实现测试/模型/tokenizer，未下载或加工正式数据；未写实现代码或复核文件，未签独立复核。

**用户处置（workflow §4.2）：** 设计退修计数为 **2**，C/R仍 **0/0**。选择(a)接受当前范围并逐条列出AR2-1…3已知缺口、
确认其处理路径，或(b)关闭为负结果记录。建议(a)：三项是合同可执行性与证据衔接问题，不需要改变训练目标。
选择(a)不自动等于实现GO或schema/尺度已冻结；上述缺口处理及所需只读试读核对完毕后，接受侧才能正式落定合同，
执行信封仍独立授权。当前只等待用户处置，不自行发第三次退修；001保持关闭、003保持暂停，其D1原文恢复义务保留。

**2026-09-13 接受侧 D1：`REVISION_REQUESTED`（审 D1 修订 2；本项首次设计退修）。**

Owner：Acceptance；范围：本提案决策记录与状态板。用户恢复 002、将 001 数据合同并入、K4 → K3、训练只用 Unity、
协议优先与动态目标入域，均已有账本授权，不重复询问方向。该范围具备申请工程轨道的基础，但当前合同尚不能按字面执行，
本轮不 `ACCEPTED`，`Workflow: engineering-v1` 未生效；AC/schema/尺度、表 G/H 与预算仍为申请值，正式设计不更新。
这是提案设计审查，不是 C 轮或独立复核；不签实现 verdict，不增已接受 BC/AC，不启动实现或模型。

**对并入修正的核对（只读，不重跑试选）：**

| 来源项 | 本轮认定 |
|---|---|
| AD3-1 | 原缺口的主要修正已回应：`sft_d5_dryrun.py` 读取 legacy 清单，纳入 G4 独立 execute、legacy 优先与逐 row_id 守恒，`bind()` 逐张比较 S1 SHA/字节；所留输出为 601 + 9 = 610 行、405 行全部映射、并集 3,968/3,968 绑定。认可其作为构思试选依据，不作为独立复核通过或完整 schema 测量。所留输出耗时 57.9 s，正文 58.1 s；下次注明各自收据来源，不影响该组计数。 |
| AD3-2 | 固定九类轮转在脚本与 E5 对应，输出 55/55/55/55/54/54/54/54/54；E3 的 350 已限 unique，E4 的含目标车歧义 65 单列。训练 5,318、选层 441 的主要算术一致，保留这些修正；其余确定性细节见 AR1-1。 |
| AD3-3 | 表 A′ 已在适配层明确未绑定、缺框、裁剪后退化三种整帧 wildcard，AC-2 点名三种回归；试选源码按此跳过该帧。真实输出 10,364 帧未触发，不代替将来的失败路径测试；上游 `frame_world` 保持原样。 |

**退修闭集（一次回应以下四项；不要求现在下载、加工正式工件或运行模型）：**

| 编号 | 问题与依据 | D2 必须明确的处理 |
|---|---|---|
| AR1-1 | **取样合同与尺度依据仍有未定义部分。** 表 D/E 使用 S/M/L、键、哈希序，但未定义多候选的层归属、none 的无框层、E2 的键函数与同哈希次序；试选实际用最小候选短边、`NA`、`seed\|frame_id\|key`，这些会决定取样。§1 写只用 dev 六族除选层族，E1/试选却用 train∪dev（含 a2），AC-2 的「其余六族」不能代替该口径。§8 表 6 的完整 sample ≤800 B、gold 最大128字符/所谓74 token上界，并非本次 d5 脚本/输出所测；d5 没有按表 C 序列化或统计 gold 长度，旧 d2 的数字/标点启发式也不是实际 tokenizer 上界。 | 统一训练池为已选方向下的 train∪dev 减 detect-scout1，列明族闭集或具名清单；把层、各状态键、哈希编码/分隔符、平局次序、legacy 优先内次序写到表 D/E，使实现者无需从临时脚本猜规则。保留已核对的行数/帧绑定；补同一候选集合按表 B/C 实际序列化的单行/总字节、gold 字符长度及来源，内存/算力预测与实测分列。token 152 只保留为未来真实预检的拒绝阈值，不称已证上界。说明本地64 MB是否排除只读原图以及180.9 MB上传包在何处生成、按何项计额，不能让复制图像的操作与目录上限冲突。 |
| AR1-2 | **云端执行的数据闭集不自洽。** 表 H/AC-8 要求云端首次下载后对训练/选层/评估全部 gold 做 tokenizer 预检，表 C/Part B 却只上传评估盲文件并写「gold 永不上云」；该句按字面还排除了训练监督。包仅列 prompt 和训练/runner 等，没列启动时要比对的 dataset/eval manifest，也没交代包内 Python 模块依赖；四份脚本冻结链与云端实际持有的文件不对应。 | 明确训练标签可上云、选层/评估 gold 留本地；为 gold 长度预检给出可执行的数据流与执行位置（例如本地同版 tokenizer 生成绑定输入/模板/版本的预检收据，云端验收收据），并明确诊断行中无合法三态 gold 者的处理。列全云端运行与校验必需文件、训练标签/盲文件/清单的可见字段及依赖；云端只验证其实际持有的字节，完整冻结集在本地校验，双方用收据绑定。给包自身/manifest/收据的生成先后、互不自引用规则及无GPU缺件回归。若改需新增本地 tokenizer 下载，先写入候选2申请信封，仍须后续用户授权；不允许为预检把评估 gold 上传。 |
| AR1-3 | **新标签只有程序自洽检查，没有语义抽查合同。** engineering-workflow §7 要求完整性核验与按风险分层的语义抽查互补。AC-1…6 没有抽查项；ASSET-001 原抽查是目录车逐对象的描述性检查，报告 §2 明确不构成 S6 审计，不能覆盖本项新生成的 none、候选集合与 dynamic-target gold。仅保留「框 UNVERIFIED」不能替代本项标签核验。 | 在K4数据报告/验收里明确对派生标签的有限语义抽查：至少说明 unique（含颜色）、ambiguous完整候选集、none、dynamic-target 与已知颜色反例排除这几个风险层，抽样方法/上限、谁核对原图、记录字段，以及发现错误后停止冻结并回合同处理的路径。可复用旧抽查中同帧同标签的具名结果，其余缺口显式补查；不恢复旧S6、不改变原gold定义、不把旧目录重标。先把步骤及本地加工/看图上限列入申请合同，本轮不执行、不自行新增额度。 |
| AR1-4 | **条件式跨环境接口与判定尚不可执行。** 表 G 的「协议指标配对差」没有指定指标、改善方向和 Unity 分母为0/负值的处理，也没有 TRANSFER_OBSERVED 的判据；表 B/H/AC-8 每张图硬断言 Unity 网格，与未来003自行定义的数据接口没有条件边界。AC-12 的三态/评分来源及两任务独立实现的一致性也未指定，003 DONE 本身不能证明与002冻结接口相同。 | 保持003暂停、当前阶段NOT_RUN，明确该分支不阻塞Unity两停点的交付，也不自动授予恢复/执行额度。若保留未来可执行分支，先把通用字段/预测解析/评分兼容条件、图像网格断言适用域、逐项配对指标及迁移比零/负分母的NA规则写清；TRANSFER_OBSERVED必须有可机械判断的方向/条件，不能由实现者看到结果再解释。也可把该分支明确锁在003恢复后的合同裁定前，届时按已冻结Unity接口另做兼容裁定；本轮不冻结未知003 schema/尺度、不重启其审查。 |

读取范围：本提案完整正文/AC/决策、001 D3及D1/D2接受决定、账本2026-09-12/13相关授权、正式设计§1/§2/§6、
工程继承清单与缺陷账本、ASSET-001盘点报告§0–3/标签抽查合同与R2相关结论、探针日志；只读查看
`build_catalog.frame_world`、`tier1_lang` noun判据及构思临时脚本/输出。
临时来源目录：`/private/tmp/claude-501/-Users-zc-TetheredDroneTracking/040b8b56-256b-47ae-9eea-39f9521e4755/scratchpad/`，
文件 `sft_d5_dryrun.py`、`sft_d5_out.txt`，以及旧 `sft_d2_dryrun.py` 的gold长度段；临时来源只供定位，不是冻结工件。
本轮没有运行上述脚本、实现测试、下载、模型或数据构建。ASSET F8不使用其可变日志入口，不产生新release或旧债闭合。

计数：本项设计退修 **1**，C/R **0/0**；001保留自己的退修2和用户关闭记录，不回改、不借本轮签通过。
下一角色=Ideation，提交D2回应AR1-1…4；接受侧下轮复审。未接受前执行额度仍为0，003暂停与原D1裁定恢复义务保留。

- 2026-09-12 D1 `PROPOSED`：构思角色落盘；由用户处置 `P1-ENG-SFT-001` D2 第二次退修时拆出（账本同日条目）。前置 = SFT-001
  `DONE`；轨道申请 `engineering-v1` 待裁定；表 H 配方、AC-1…7、§5 信封均为申请值；接受审查可延后至 SFT-001 K4 通过后。
  零实现、零模型运行、零派生工件。
- 2026-09-12 D1 修订 1（构思角色；用户方向讨论后）：训练目标改为协议优先、词表靠 prompt；新增 AC-8 SynDrone 跨环境零样本评估
  （依赖 `P1-ENG-SFT-003`，只评不训，结论闭集描述性）；§5 启动/GPU·h/推理行/上传按 SFT-001 D3 修订 1 与 SynDrone 更新
  （GPU·h ≤ 10）。零实现、零模型运行。
- 2026-09-13 用户暂停（账本同日「用户指示暂停第二份提案」）：本项转 `PAUSED_BY_USER`，不因 `P1-ENG-SFT-001` `DONE` 自动恢复审查或
  执行；方向决定、AC 申请值与 verdict 不变；恢复由用户决定。
- 2026-09-13 用户恢复（账本同日「用户指示暂停 003、恢复 002」）：解除 `PAUSED_BY_USER`；原前置 SFT-001 已关闭，数据合同来源
  （并入本项自带 / 重开 SFT-001 / 新立最小数据项）待用户选择，构思角色随后修订再交接受审查；verdict、AC 申请值与信封不变。

- 2026-09-13 D1 修订 2（构思角色；用户恢复本项并选「数据合同并入 002 自带」，账本同日条目）：§3 Part A 逐字承接 001 D3 修订 1 的数据合同
  并闭合接受侧 AD3-1…3（G4 与 legacy 同一次试选、610 行、405 行守恒、全集合 SHA 绑定；none 固定顺序轮转、350 只限 unique 配额、歧义单列；
  适配层实现未绑定/缺框/退化框整帧通配并具名边界用例）；Part B 训练与云端执行沿修订 1；AC 重编为 AC-1…6（K4）+ AC-7…13（K3）；§5 补本地
  构建尝试上限、分两次授权；SynDrone 阶段随 003 暂停记 NOT_RUN。零实现、零模型运行。设计退修计数 0（本项尚无接受轮裁定）。
- 2026-09-13 D2（构思角色；回应接受侧 D1 首次 `REVISION_REQUESTED` AR1-1…4，裁定原文逐字保留于上方）：AR1-1 → §1 训练池口径（train∪dev 七族减
  `detect-scout1`）、表 D′（层含 `NA`、最小候选短边、各状态键、`seed|frame_id|key` 哈希与平局、E2 稀疏、评估准入、legacy 优先内次序、层轮转）、
  表 D/E 修订（G2t 口径、E1 族闭集与逐族 E2 计数、E5/E6 用实取 |N|）、§8 表 6a 实测 / 6b 投影（train.jsonl 3.15 MB、单行 max 877 B、gold 字符
  max 145；评估集行级字节因 T7 未挂载待 K4 实测）、§5 与写入分层的 `data/`/`upload/`/`panel/` 分根计额；AR1-2 → 表 K 云端包闭集与生成先后、
  表 H token 预检三项 + 本地骨架断言、`PACKAGE_INCOMPLETE`/`TOKENIZER_PROPERTY_UNVERIFIED`、AC-5/7/8 重写；AR1-3 → 表 J 与 AC-14（用户 2026-09-13
  逐字「用户只看 ≤24 张」，账本同日条目）；AR1-4 → 表 L 与 AC-12 重写（用户 2026-09-13 逐字「我倾向于不等」，账本同日条目）。AD3 主要修正与
  已核对行数/帧绑定不变；零实现、零模型、零下载；设计退修计数 1；交接受侧复审。
- 2026-09-13 D3（构思角色；用户按 workflow §4.2 处置第二次退修 = (a) 保留范围并修正，逐字「查看accept结果并修正」，账本同日条目；接受侧 D2 裁定原文
  逐字保留于上方）：AR2-1 → 表 D′ G3′ 键改回 surface、并列次序补 noun_type/surface（复现 d5）、表 C `station_key` 实取/浮点原值/`frame_path`、§8 表 6c d7
  全字段实测（T7 已挂载，用户逐字「已接上 T7（推荐）」）并更正评估集为 609 行（LEGACY_ONLY 8 评估行承载 9 条 legacy 行；405 守恒不变）；AR2-2 → 表 H
  改为本地同版 tokenizer 逐条预检收据 + 云端重算比对（`TOKENIZER_MISMATCH`），删除两例外推，tokenizer 四文件下载列入候选 1 申请信封；AR2-3 → 表 K 拆为
  K4 数据包（不含代码，`smoke.jsonl` 由 build 产出）与 K3 代码束，`frame_path` 在 build 时写定、打包不改 jsonl 字节并记运输映射，AC-5（K4）/AC-7（K3）
  分列，表 C upload 行改引表 K；接受侧认定项：§7 K4 = AC-1…6 + AC-14、表 J 冻结前提含用户份额判定齐全（`AUDIT_INCOMPLETE`）、表 H base 行网格限定
  Unity。零实现、零模型、零下载；设计退修计数保持 2；交接受侧按用户处置 (a) 落定合同。
- 2026-09-14 用户授权候选 1（K4）执行信封（构思会话代录，账本同日「授权候选 1（K4）执行信封」条目；用户逐字「好的，那下一步可以开始执行了」→
  「授权候选 1，按接受侧申请值（推荐）」）：本地构建累计 ≤ 8 次（每次 ≤ 5 min、RSS ≤ 1 GB）、面板 ≤ 2 次、用户判定 ≤ 24 张 + 复判 ≤ 1 次、预筛 ≤ 36 张、
  代录 1 次、tokenizer 四文件下载 1 次（≈ 12 MB，目录 ≤ 20 MB）、预检 ≤ 3 次；GPU/推理/训练/API/Play/正式 ID/上传/发布 = 0；候选 2 未授权。交实现角色
  按 §2 候选 1、AC-1…6/14 与首次接受释义开 K4；停点自证 → `C1@K4` → `R<n>@K4`，`UNITY_NA` 须复核附议。
