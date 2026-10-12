# P1-ENG-SFT-002 — 候选 1（K4）数据报告

工作项：`P1-ENG-SFT-002`（工程轨道 `engineering-v1`）。本文件是 AC-6 的交付物，
只报告**离线数据加工**的事实：对账、三态派生、训练/选层/评估集、冻结工件、
tokenizer 预检与标签抽查统计。**零模型、零 GPU、零 Play、零 scenario/session/run/attempt
身份**；不含任何模型结果，也不构成能力主张。

数字一律取自受版本控制的四份冻结 JSON 与本地收据（`outputs/eng-sft/P1-ENG-SFT-002/receipts/`），
不手写可派生标识。提案 §8 的试读数字是构思侧只读复算，本报告只用作对照。

## 0. 执行口径与信封计次

| 项目 | 授权上限（账本 2026-09-14） | 本报告截止时已用 |
|---|---|---|
| 真实输入入口累计（对账/构建/`freeze`/`package`，含失败；AC-6 修订 2） | **14**（用户 2026-09-15 由 8 加到 12，2026-09-16 为 R1@K4 F1 返工再加到 14） | **13**：`build` ×3、`freeze` ×5（第 1 次 `INPUT_HASH_CHANGED` 失败，见 §6）、`package` ×5（第 1 次成功但运输映射漏报重复帧）；C2 返工用掉第 10、11 次，R1@K4 返工用掉第 12、13 次（重冻结 + 重打包，均一次成功），余 1；R1@K4 返工未重跑 `build` |
| `precheck` 运行（独立计，不并入上一行） | **5**（同日由 3 加到 5） | 2（第 2 次因 `prompt_v2.py` 注释改动使 gold 函数 SHA 变化而重绑；C1 返工未改 gold 字节，无需第 3 次） |
| 面板生成（`panels`） | **3**（2026-09-16 由 2 加到 3） | 3（第 1 次后自查出 J3 层定义与弱类顺序偏差，修正后重出；第 3 次为 R1@K4 F1：修复抽样域后按新计划重绘，见 §15） |
| 用户判定 / 受影响层复判 | 1 次 ≤ 24 张 / ≤ 1 次（累计唯一用户图 ≤ 24） | 首次 21 张（2026-09-14）；复判 **1/1**（2026-09-16，只看变化的新 J3 #9–#11 三张，累计唯一用户图 24）；#20/#21 按 AC-14 修订 3 不复判 |
| 额度追加的来历 | — | C1@K4 退回的修复触及被冻结的 `evaluate.py` 与对账记录，必须重跑 `build`/`freeze`/`package`；实现角色先核算再回用户，用户当场授权（所选选项标签逐字：「加到 12 次，预检加到 5（推荐）」），接受角色已逐字补入授权账本（2026-09-15 追加信封条目） |
| R1@K4 F1 返工额度的来历 | — | 接受角色复判维持 F1 必修并提交四项追加申请，用户逐字「授权批准」，接受角色已入账（账本 2026-09-16「批准 R1@K4 F1 返工追加信封」）；K3 仍未授权 |
| C2-4 处置 | — | 用户 2026-09-15 选「先修代码，不重抽（推荐）」：不重跑 `plan`、不重绘、不用复判额度；接受角色已逐字补入授权账本（2026-09-15 条目，2026-09-16 代录）。该决定**不是** AC-14 豁免或抽查证据合格裁定 |
| 实现者预筛 | 累计 ≤ **39** 张（2026-09-16 由 36 加到 39；每份计划的预筛份额仍按表 J ≤ 36） | 39：首轮 29 + R1@K4 返工新看变化的 #32–#41 共 10 张；新计划其余 19 张样本身份与图字节未变，沿用首轮结果并逐行注明 |
| 判定代录（接受/辅助角色） | 累计 ≤ **2** | 2：2026-09-14 首次 21 张；2026-09-16 新 #9–#11（辅助角色，Unity 日志同名条目） |
| tokenizer 下载 | 1 次（四文件，≈ 12 MB） | 1 次，11.0 MB |
| GPU·h / 推理 / 训练 / API / Play / 正式 ID / 上传 / 发布 | 0 | 0 |

**计次口径**（AC-6 修订 2 已裁定）：真实输入上的 `build` / `freeze` / `package` 每次调用
（含失败）计入受限入口累计（原信封 ≤ 8，2026-09-15 追加后 ≤ 12，2026-09-16 再追加后 ≤ 14）；`precheck` 独立计
（原信封 ≤ 3，追加后 ≤ 5），不重复计入前者。模块导入级的读几行分片、
纯夹具测试与只读核查脚本不计。表 J 的 `plan` / `prescreen` / `stats` / `close` 不生成面板，
不计入「面板生成」（只有 `panels` 计），也不借此免除其中实际调用的受限入口。

**信封外事项一件（已入账）**：`precheck` 需要同版 BPE 计数库，本机 `transformers` /
`tokenizers` 均未安装，而信封的「下载」只覆盖 tokenizer 四文件。实现角色停下来请示，
用户当场授权安装 `tokenizers`（所选选项标签逐字：「授权装 tokenizers（推荐）」），遂用
`uv pip install --python .venv-yoloe/bin/python` 装入既有 `.venv-yoloe`（`tokenizers 0.23.2`）。
该授权已由接受角色逐字补记 `docs/authorizations.md`（2026-09-14「补录实现会话安装 tokenizers
的授权」），补录不扩展其他下载或 K3 信封。

## 1. 输入身份与对账（AC-1）

只读 §3 输入闭集，身份运行时解析，逐件记入 `receipts/input-manifest.json`（阶段
`build` / `precheck` 各存 before/after 两份快照，只追加）。

| 输入 | 核对结果 |
|---|---|
| S3 `frames_catalog@attempt-2` | 帧 43,535 / 分片 151；逐片 `compressed_bytes` 与 SHA-256 相符；分片行数之和 = 43,535 |
| S4 `splits@attempt-2` | train 2,523 / dev 13,144 / test 8,450 / d3 0；7 片 SHA 相符；**另核对四个 split 两两不交**（见 §11 (d)） |
| S5 `field_catalog@attempt-2` | 对象 690 / `class_verified` 93 / 双验证 37；SHA `8d0ff722d62b66ac…` |
| S1 `inventory@attempt-2` | 逐帧 `path/sha256/bytes` 供帧绑定；见 §5 |
| `runtime/eng-asset/.../instructions.ndjson.gz` | SHA `06565a95d0d1dc7c…`，与探针清单 `source.instructions_sha256` 相等 |
| 探针 `probe/manifest-default.json`（T7） | 现算 SHA `7c259a347603d006…`，与 `docs/unity-test-log.md` 记录的前缀一致 |
| 探针 `predictions.jsonl`（T7） | 现算 SHA `25702e85876f9ac0…`，与 Unity 日志前缀一致；本候选只复制留档，不评分 |
| `P1-ENG-ASSET-001-instructions-summary.json` | 七值直方图基准 |

**七值直方图**：用 `tools/eng_asset/inventory.classify_uniqueness` 在对账域（43,535 帧中
可用帧的全部 `referable` 对象）重算 **57,430** 行，按 `(split, mother_usage, status)` 与
ASSET-001 摘要**逐值相等**；任一不等即 `HISTOGRAM_MISMATCH` 并只写失败收据。

## 2. 表 A′ / 表 A 派生与计数披露

- 目标车在场帧 **10,364**；其中未绑定 0、已绑定但缺框 0、裁剪后退化 0 →
  **整帧通配（`frame_wildcard`）0 帧**（与 §8 表 1 的 `0 / 10,364` 一致）。
- `unassigned` 帧 19,418（不进任何集合，只进对账域）。
- #27 反例（`Vehicle_Bus_color03`）所在帧的 `bus` 颜色指令整帧排除：train 25 / test 316（dev 0）。

**三态可得数（稀疏前，与 §8 表 3 对照）**

| split | class unique / ambiguous / none | class 灰区（确证+不确证 / 不确证 none） | color unique（需色）/ ambiguous / 灰区 / #27 排除 |
|---|---|---|---|
| train | 1,497 / 198 / 9,341 | 2,133 / 9,538 | 0 / 174 / 1,107 / 25 |
| dev | 17,444 / 555 / 58,288 | 5,910 / 36,099 | 1,303 / 11 / 1,796 / 0 |
| test | 10,084 / 552 / 43,659 | 4,268 / 17,487 | 1,110 / 24 / 2,292 / 316 |

逐项与 §8 表 3 相同。

## 3. 表 E：训练集与选层集实取

| 步 | 实取 |
|---|---|
| E1 | 训练池 = 七族（train `p1-vlm-survey-a2-p1-c1-s1` + dev 六族）；选层集 = `detect-scout1` 整族；训练子集 = 其余六族；test 与 `unassigned` 零帧 |
| E2 | 稀疏后训练池 unique 8,991 / ambiguous 466 / none 11,202；逐族 (unique/ambiguous/none)：a2 1,299/203/1,990、m3-armA 694/0/185、a1 2,143/103/2,906、a7 2,613/160/3,306、rate 1,934/0/2,451、scene-val 308/0/364；选层族稀疏后 unique 925 / ambiguous 41 / none 504 |
| E3 | unique 配额后 **4,006**：container truck 700、pickup truck 700、suv 700、car 517（其中目标车 350、目录车 167）、taxi 400、bus 334、ambulance 285、truck 272、police car 98 |
| E4 | ambiguous 每键 ≤ 60 后 **411**：truck 180、car 90、pickup truck 75、container truck 28、police car 18、taxi 16、suv 4；含目标车 65 |
| E5 | N_none = 490，实取 **490**（ambulance/bus/car/container truck 各 55，pickup truck/police car/suv/taxi/truck 各 54；每类上限 ⌈490/9⌉ = 55） |
| E6 | 复制系数 k = **2**，ambiguous 份额 15.46% |
| E7 | 训练多重集 **5,318** 样本 / distinct **4,907** 行 / **3,198** 帧；层（unique）S 458 / M 1,747 / L 1,801 |
| E8 | 选层评估子集 **441** 行 / **322** 帧（ambiguous 41 + unique 300 + none 100） |
| E9 | seen 对象 **76**（含 `dynamic-target`） |

逐项与 §8 表 5 / 表 E「试选实取」列相同。冒烟集 `smoke.jsonl` 由 `build` 产出，32 条 =
unique class 8 + unique color 8 + ambiguous 8（class 5 + color 3）+ none 8。

## 4. 表 D：冻结评估集、守恒与泄漏

| 组 | 行数 | 其中 legacy 行 |
|---|---|---|
| G1 | 210 | 210 |
| G1t | 23 | 0 |
| G2 | 49 | 49 |
| G2t | 23 | 0 |
| G3 | 48 | 12 |
| G3t | 12 | 2 |
| G3′（G3p） | 50 | 37 |
| G4 | 86 | 86 |
| G5 | 100 | 0 |
| LEGACY_ONLY | 8 | 9 |

合计 601 gate/诊断行 + 8 LEGACY_ONLY = **609 行**，盲文件同行数；`legacy_probe` 条目
合计 **405**（3 个评估行各承载 2 条重复键 legacy 行）。

**守恒**：`legacy-conservation.json` 405 条，ADMITTED 396（G1 210 / G2 49 / G3 12 /
G3t 2 / G3′ 37 / G4 86）+ LEGACY_ONLY 9，unmapped **0**；每条保留自己的 v1 组与 gold。

**泄漏与 seen**：训练∪选层 ∩ 评估（按帧 SHA）= ∅；训练∪选层 ∩ (test ∪ unassigned) = ∅；
seen 按 E9 = 76 个对象。评估行 `seen_target`：true 466 / false 43 / null 100（null 即 G5 的 100 行 none，没有目标对象；G3′ 与 LEGACY_ONLY 用 `definite_ids` 计，不是 null）。

**帧 SHA 绑定**：训练 3,198/3,198（150,188,287 B）、选层 322/322、评估（含 LEGACY_ONLY 行帧）
448/448、并集 **3,968/3,968（189,693,057 B = 180.9 MiB）**，缺失 0、不符 0。

**逐字节重复帧的披露（本次打包时发现，非合同变更）**：上面的帧数都是 `frame_id` 计数；
按帧字节 SHA 去重后，**并集 3,968 个 frame_id 只对应 2,327 张不同字节的图**：

| 集合 | frame_id | 不同字节的图 | 逐字节重复占比 |
|---|---|---|---|
| 训练 | 3,198 | **1,613** | 49.6% |
| 选层评估子集 | 322 | 322 | 0.0% |
| 冻结评估集（含 LEGACY_ONLY 行帧） | 448 | 392 | 12.5% |
| 并集 | 3,968 | 2,327 | 41.4% |

即训练集近一半的「帧」在像素上与同集合内另一帧完全相同（5 Hz 采样下静止段的必然结果，
最极端的一张图对应 196 个 `frame_id`）。这不改变任何已冻结的取样决定（E2 的稀疏按帧序号，
合同未要求按字节去重），也不影响泄漏断言——泄漏本来就按帧 SHA 判，训练∪选层与评估的
SHA 交集为空。但它意味着**「3,198 训练帧」不等于 3,198 张不同的图**，报告与后续任何
主张都不得把帧数读作视觉多样性。数据包因此只装 2,327 个图像文件（见 §9）。

## 5. 序列化字节与 gold 长度（与 §8 表 6c 同口径对照）

落盘口径：UTF-8、`ensure_ascii=True`、`separators=(",", ":")`、每行一个 LF（AC-5 修订 1）；
gold 文本另按表 B 的缺省空格分隔符。

| 文件 | 行数 | 总字节 | 单行 max / p50 / min | §8 表 6c |
|---|---|---|---|---|
| `train.jsonl` | 4,907 | 3,975,066 | 1,108 / 808 / 630 | 相同 |
| `smoke.jsonl` | 32 | 26,108 | 1,009 / 809 / 659 | 相同 |
| `select-eval.jsonl` | 441 | 341,500 | 918 / 789 / 651 | 相同 |
| `select-eval.blind.jsonl` | 441 | 77,927 | 191 / 177 / 173 | 相同 |
| `eval.jsonl` | 609 | 634,764 | 1,644 / 1,091 / 709 | 相同 |
| `eval.blind.jsonl` | 609 | 112,096 | 227 / 180 / 174 | 相同 |

gold 字符长度：训练 distinct 4,907 条 max 143 / p50 53；选层 441 条 max 109；评估 551 行有
gold（G3′ 50 + LEGACY_ONLY 8 = 58 行 `gold_state = null`）max 145；unique 各组 ≤ 55、G5 18。
与 §8 表 6c 相同。`legacy-conservation` 405 条按逐行计的字节在本实现里落成单份 JSON 文档
（145,844 B，含 totals 汇总），与表 6c 的「逐行计 114,452 B」是同一组行、不同封装，非数字冲突。

## 6. tokenizer 本地预检（表 H；`precheck` 2/5，收据在 C1 返工后仍有效）

- 计数库：`tokenizers 0.23.2`（HF 分词轮子，无 torch 依赖）；`add_special_tokens=False`、不套模板。
- tokenizer 四文件：`Qwen/Qwen3-VL-2B-Instruct` revision `89644892e4d85e24eaac8bacfd4f463576704203`，
  `tokenizer.json` / `tokenizer_config.json` / `vocab.json` / `merges.txt`，合计 11,491,943 B
  （目录上限 20 MB）；收据逐文件绑定 SHA-256。
- 收据另绑定四份 gold 文件的 SHA、`gold_text` 所在模块（`tools/eng_sft/prompt_v2.py`）的源码 SHA、
  revision 与计数开关。

| gold 文件 | 有 gold 行 / 无 gold 行 | token max / p50 / 合计 |
|---|---|---|
| `train.jsonl` | 4,907 / 0 | 87 / 32 / 153,101 |
| `smoke.jsonl` | 32 / 0 | 63 / 32 / 1,031 |
| `select-eval.jsonl` | 441 / 0 | 62 / 32 / 12,631 |
| `eval.jsonl` | 551 / 58 | 89 / 31 / 16,613 |

**全局 max 89 ≤ 152**（152 只是拒绝阈值，不是已通过的性能事实）。模板固定开销：
`<|im_start|>assistant\n` = 3 token、`<|im_end|>` = 1 token。K3 的云端复算只对上云的
`train.jsonl` + `smoke.jsonl` 重算并与本收据比对；评估 gold 不上云。

## 7. 失误画像对照（§8 表 8 格式）

| 类别 | 零样本 G1 Success（探针） | 本稿 unique（E3 后） | 本稿 ambiguous（E4 后） | 混淆对暴露（本报告口径） |
|---|---|---|---|---|
| car | 45% | 517（目标车 350 + 目录车 167） | 90 | car→taxi 194；car→suv 220 |
| pickup truck | 52% | 700 | 75 | pickup→container 220；pickup→suv 191 |
| truck | 68% | 272 | 180 | truck→container 118 |
| suv | 71% | 700 | 4 | suv→pickup 238 |
| container truck | 82% | 700 | 28 | — |
| taxi | 86% | 400 | 16 | — |
| bus / ambulance / police car | 90% / 92% / 100% | 334 / 285 / 98 | 0 / 0 / 18 | — |

零样本列取自用户离线探针（`docs/unity-test-log.md`，未经授权信封与独立复核，不得读作合格线）。
**混淆对暴露口径**：E3 保留的全部 unique 样本（class + color，与 E3 配额同域）中，帧执行域内
同时出现另一类别的样本数，由 `dataset-manifest.json` 的 `steps.confusion_exposure_unique_kept`
机械派生。§8 表 8 的同名数字（car→taxi 178、car→suv 215、pickup→container 222、pickup→suv 194、
suv→pickup 220）出自构思侧 scratchpad 的另一次统计，口径未在提案正文固定（很可能只计 class noun
样本）；两组数字并列披露，不互相覆盖，也不改变任何取样决定。

## 8. 表 J 标签语义抽查

抽样参数、分层实取、面板清单、ASSET-001 交集表与实现者预筛表见
`docs/evidence/P1-ENG-SFT-002-label-audit.md`（用户判定原文由接受/辅助角色代录
`docs/unity-test-log.md` 的 `UT-P1-ENG-SFT-002-label-audit`）。

- **R1@K4 F1 返工（2026-09-16/17，详见 §15）**：C2-4 修复后抽样域变为 J1 3003 / J2 1024 / J3 420，
  按候选代码重抽：用户 #9–#11 换成三条评估 G3 行（三候选），预筛 #32–#41 随之变化，其余 37 张样本身份与
  原图/叠加图字节不变；新 #9–#11 经用户复判后由辅助角色代录。下文数字除另注外均为返工后计划的数字。
- 实取：用户 21 行 + 预筛 29 行 = 50 张唯一图片（申请上限 24 / 36）。
- 两处按合同留空披露、不回填：**J5** 在「同一 `object_id` 每层 ≤ 1 行」下只能取 1 行
  （目标车是单一对象，配额 3/4 结构上不可达）；**J4** 在「每类 ≤ 1」下最多 9 行（用户 4 + 预筛 5）。
- 与 ASSET-001 的 60 张面板按 `(frame_id, object_id)` **无交集**，故无可引用的旧判定；
  三态状态本来也必须本次判定。
- 实现者预筛 29 张（返工后计划）：状态对 26、错 0、不确定 3（#25/#29 截断小目标、#44 左缘截断车辆不可判类），
  其中新看的 #32–#41 十张全部状态对（J3 候选完整亦对；可疑车辆逐一对照 S3 核为异类或非候选）。
  首轮计划的预筛 #33 颜色疑点（`Vehicle_Truck_color01 (1)`，S5 `color=gray` VERIFIED，面板上明显为红色，
  与 #27 同族）不在新计划里，作为历史披露保留（§11(g)、§14）。**预筛只作披露，不计为语义核验，不改变任何冻结决定。**
- **用户判定（2026-09-14，原文经辅助角色代录 `UT-P1-ENG-SFT-002-label-audit`，提交 `330cbf9`）**：
  21/21 判定齐全（`Judgment state: COMPLETE`），状态 21 张全「对」，J3 候选完整 4/4「对」，
  J2/J5 颜色「对」，J6 关系方向「对」，「不确定」0 张；**J7 的 #20/#21 颜色判「错」**（错误类型：颜色错 2）。
  分层统计见抽查文件 §5。
- **用户复判（2026-09-16，辅助角色代录进同一条目）**：新 #9–#11（the taxi / the bus / the container truck，
  各 3 候选）状态与候选完整均判「对」，错误类型空；#10/#11 用户指出边缘有车辆显示不完整，经实现侧给出截断
  口径与公开数据集惯例后，用户选「都记对，截断作备注」。21/21 齐全、`Judgment state: COMPLETE`；
  旧 #9–#11 的判定与旧面板身份另存于日志的历史小节。
- **`AUDIT_FINDING_OPEN` → 具名裁定 → 闭合记录**：`stats` 先写开放收据
  （`receipts/audit-finding-open.json`，panels 20/21），`freeze` 据此拒绝运行。接受角色
  2026-09-14 按表 J 把两行**分别**裁为 **(ii) 上游标签缺陷**（AC-14 修订 3），并认定不需要
  重建、重绘或复判——两帧的 `bus` 颜色 noun 本来就已按表 A′ 整帧排除，数据与图的字节不变。
  实现角色随后用 `label_audit close --disposition ii --ruling-anchor "AC-14 修订 3"` 写闭合记录
  （`receipts/audit-finding-closure.json`）：绑定裁定出处（提案路径 + 运行时解析的提交 +
  逐字锚点）、原开放收据的 SHA（收据保留不删）、逐张面板身份与「该 noun 确已排除」的证据
  （四份 gold 文件里该 (帧, surface) 行数均为 0），并记判定表摘要。`audit_gate_state` 此后
  只放行记录里的这两张：判定表一变摘要即失效、出现未裁定的「错」仍拒绝、删掉原收据也无法闭合
  （具名回归 `ReceiptTests.test_closure_record_releases_only_ruled_panels`）。
- **两张面板不是同一辆车**（AC-14 修订 2 的身份要求，抽查文件 §3「J7 身份披露」表）：
  #20 的叠框对象就是反例本身 `Vehicle_Bus_color03`（S3 `OK`、`blocks=true`，S5 `gray`/VERIFIED）；
  #21 的叠框对象是同帧另一辆 `Vehicle_Bus_color01 (1)`（S3 `OK`，S5 也是 `gray`/VERIFIED），
  触发整帧排除的 `Vehicle_Bus_color03` 在该帧是 `TOO_SMALL` 但仍在执行域内，另列在
  counterexample 列，不与叠框对象混用。用户的两次「错」按原文保留，不外推为该对象、同族或
  全部非纯色车的重标；全域排除计数 train 25 / test 316 是本次构建的实现侧数字。

## 9. 执行收据与边界（AC-6）

| 阶段 | 耗时 | 峰值 RSS | 产出 |
|---|---|---|---|
| `build`（尝试 1） | 63.9 s | 413,827,072 B（394.7 MiB） | 六份 jsonl + J7 候选 + legacy 副本 + 四份冻结 JSON |
| `build`（尝试 2，加 §7 暴露矩阵） | 63.1 s | 413,925,376 B（394.8 MiB） | 同上；除 `dataset-manifest.json` 外逐文件字节不变 |
| `panels`（第 2/2 次） | 0.3 s | 43,810,816 B | 50 张叠加图 + 50 张原图副本 + `panel-receipt.json` |
| `precheck`（1/3、2/3） | 0.3 s | 111,149,056 B | `precheck-receipt.json`（第 2 次因 gold 函数源码 SHA 变化重绑，token 计数与第 1 次逐项相同） |
| `close`（表 J 闭合记录） | < 0.1 s | 38 MB 级 | `audit-finding-closure.json` |
| `freeze`（入口 1/2，失败） | 0.1 s | 39,010,304 B | 只写失败收据 `INPUT_HASH_CHANGED`（预检收据过期），不产出冻结收据 |
| `freeze`（入口 2/2，成功） | 0.4 s | 38,961,152 B | `freeze-receipt.json`：HEAD、冻结闭集 8 个文件的 SHA 与 `git ls-files` blob、六份 jsonl SHA、预检收据 SHA、抽查摘要 |
| `package`（入口 1/2） | 1.4 s | 55,721,984 B | 成功，但运输映射每文件只留一个源 `frame_id`（漏报 1,641 个），据此修正后作废 |
| `build`（C1 返工后重建，入口 7/12） | 64.5 s | 391,872,512 B（373.7 MiB） | 六份 jsonl、eval-manifest、leakage-report、legacy-conservation **逐字节不变**；只有 dataset-manifest 增 160 行（`s0_constants_checked` 与 `s3_declared_lines_by_shard`）。同时证实 C1-2 的修正在当前输入上零行改变、C1-1 的重排不改产出字节 |
| `freeze`（入口 8/12） | 0.4 s | 38 MB 级 | 新冻结收据：绑定 C1 返工后的 `evaluate.py` 与重建后的 manifest |
| `package`（入口 9/12） | 1.5 s | 55 MB 级 | 重打包：2,335 成员 / 121,013,624 B；包内冻结收据副本 SHA 与本地一致 |
| `freeze`（C2 返工后，入口 10/12） | 0.5 s | 38 MB 级 | 绑定 C2 返工后的 `evaluate.py`；冻结闭集 8/8 与收据相符 |
| `package`（C2 返工后，入口 11/12） | 1.6 s | 55 MB 级 | 2,335 成员 / 121,013,624 B；先校验 → 暂存成包 → 原子替换 |
| `panels`（第 3/3 次，R1@K4 F1） | 0.6 s | 128,745,472 B（`.venv-yoloe`，`/usr/bin/time -l`） | 按新计划重绘 50 张；与旧收据逐张比对，37 张身份与原图/叠加图 SHA 全同，变化恰为 #9–#11、#32–#41 |
| `stats` / `close`（R1@K4 返工） | < 0.1 s | 38 MB 级 | `stats`：闭合记录因用户份额变化过期 → `AUDIT_FINDING_OPEN`，原开放收据逐字节保留（run 收据记 `preserved`）；`close`：按 AC-14 修订 3 重绑 |
| `freeze`（R1@K4 返工，入口 12/14） | 0.4 s | 98,484,224 B | 新冻结收据：冻结闭集 8/8、六份 jsonl、预检收据 SHA 与上一张收据逐项相同；`audit` 块新增用户份额摘要、闭合出处更新 |
| `package`（R1@K4 返工，入口 13/14） | 1.6 s | 122,667,008 B | 2,335 成员 / 121,013,717 B；与上一包相比只有 `manifests/freeze-receipt.json` 变化，帧运输映射逐项相同；暂存目录已清 |
| `package`（入口 2/2，旧） | 1.6 s | 55 MB 级 | K4 数据包：**2,335 个成员**（2,327 个帧文件 + 4 份 data + 4 份 manifests/收据副本）、121,010,373 B ≤ 0.3 GB；`upload/manifest.json` 逐文件列 SHA，运输映射 `包内路径 → 全部源 frame_id`（2,327 → 3,968），不含自身、不含代码、不含 gold 评估文件、不含 `legacy/` 与泄漏报告 |

表中 `precheck（1/3、2/3）` 为旧信封分母（追加后为 2/5）；`freeze（入口 1/2、2/2）` 与 `package（入口 1/2、2/2）` 是各阶段内的序号（按收据时间即累计第 3、4、5、6 次），`入口 7/12…11/12` 为累计计次；累计口径以 §0 为准。

R1@K4 返工后目录（`build_sft_data.directory_caps`）：`data/` 6,635,477 B、`upload/` 121,013,717 B、
`panel/` 13,989,924 B（含返工前面板与收据的历史副本 `history-r1k4-20260916/`）、`tokenizer/` 11,491,943 B，均在上限内。

峰值 RSS 394.8 MiB ≤ 1 GB，单次 ≤ 5 min。目录：`data/` 6,635,477 B ≤ 64 MB（不含只读原图）、
`panel/` 6,956,522 B ≤ 20 MB、`tokenizer/` 11,491,943 B ≤ 20 MB、`upload/` 121,010,373 B ≤ 0.3 GB；
受版本控制的 A2 工件各 ≤ 2 MB（最大 `legacy-conservation.json` 145,844 B）。全目录合计
约 146 MB ≤ 0.9 GB。

边界：`tools/eng_sft/` 不 import `controller.*`（具名回归
`WriteBoundaryTests.test_no_controller_imports`）；写出闭集命中即 `OUTPUT_PATH_FORBIDDEN`
（`test_output_inside_forbidden_roots_is_refused`）；本候选 diff 只含 A1/A2；原件零改写。

## 10. 测试

开发期只跑 focused（COORD-009）；全套在 K4 停点跑**一次**，输出写
`docs/evidence/P1-ENG-SFT-002-tests.log`，此处只回显摘要：

- **本停点（R1@K4 返工后）：Ran 1202 tests，errors=9，skipped=21；新增失败 0**。9 项 errors 与基线同名同因
  （`numpy` 1 + `cv2` 8，导入期）。本项用例 **46** = 1202 − 1156（build 29 / evaluate 8 / audit 7 / three_state 1 /
  parse 1），比上一停点多 5 条，逐条与修复前红见 §15；全部通过、零 skip。日志末尾区块给出对照。
  下面几行是上一停点（C2@K4 返工后）的记录，按 R1 F4 逐字补丁保留。

- 本批次（C2@K4 返工后）：**Ran 1197 tests，errors=9，skipped=21**。
- 基线（开工前提交 `4306485`，一次性 worktree 内同一命令、同一解释器）：**Ran 1156，errors=9，skipped=63**；
  **原始输出已留档** `docs/evidence/P1-ENG-SFT-002-tests-baseline.log`，可逐行核对（C1-7）。
- **本批次新增失败 0**；9 项 errors 两侧逐项同名同因，全部是**导入期**缺依赖：
  `numpy` 1 项（`test_benchmark_reanchor`）+ `cv2` 8 项（`test_detector_scouting`、`test_rate2_protocol`、
  `test_rate3_difficulty_audit`、`test_rate3_protocol.Rate3GuardTests.test_rate3_reanchor_clock_mismatch_raises_defensively`、
  `test_rate_study`、`test_scene004_gate0_probe`、`test_scene004_scouting`、`test_scene006_probe`）。
  **C1-7 更正**：上一版把九项全写成 numpy，实为 numpy 1 + cv2 8。本项不新增依赖，也不在本批次修复
  这两个既有环境缺口（范围外）。
- 本批次新增 41 条用例（1197 − 1156）= `tests/test_eng_sft_{build 28, evaluate 6, audit 5,
  three_state 1, parse 1}`，全部通过、零 skip。AC 点名的 33 条具名回归全部到位，另有 8 条边界用例
  （通配帧零样本、预检溢出、预筛披露、闭合记录放行、晚期失败零发布、打包入口守边界、分片实数行数与 S0 常量、打包失败不毁旧包）。
- **skipped 63 → 21 的真实原因**（C1-7）：不是本批次改动所致，而是基线 worktree 不带 git 忽略的
  `runtime/` 归档，依赖真实归档的用例在那边跳过、在主工作副本里实际执行。基线多出的 42 条按原因归并：
  真实归档不在本工作副本中 13、归档帧不在 11、`scenario_config.p1-scene-004.hold.json` 不在 6、
  归档 A1 run 不在 4、`p1-detect-001-scout-1-closed-exchange` 不在 3、scene-004 归档字节不在 2，
  其余 3 条与主副本同因。errors 的对照不受此影响（导入期失败与工作副本是否有归档无关）。

## 11. 实现期问题的裁定与落实（接受角色 2026-09-14）

§11 原列的五条已由接受角色在提案「待裁定」节以六行 AC 修订答复（新 AC = 0，D/C/R 计数不变）。
逐条落实情况：

| 裁定 | 内容 | 实现侧落实 |
|---|---|---|
| AC-4 修订 2 | G4 关系释义段固定接在词表段之后、Coordinates 段之前；非 G4 不插入 | 与已交付实现一致，文本与三段 SHA 不变；`prompt_v2.build_prompt` 注释改为引用该裁定（不再写作实现读法） |
| AC-14 修订 2 | 去重约束优先于名义配额（J5 用户 1/预筛 0、J4 用户 4/预筛至多 5，不足额披露不回填）；J7 显示的 object_id/框/S5 颜色须同一对象，并与触发排除的 counterexample 分列 | 抽查文件 §3 增「J7 身份披露」表（#20 叠框即反例本身；#21 叠框 `Vehicle_Bus_color01 (1)`，counterexample 另列）；具名断言进 `SamplerTests.test_layer_quotas_and_uniqueness_are_deterministic` |
| AC-3 修订 2 | LEGACY_ONLY 保留灰区 `diagnostic`，`group=LEGACY_ONLY`；守恒表 `group` 保留去重前 v2 组 G3p、`group_v1` 保留原探针组、`eval_row_id` 指向实际 LEGACY_ONLY 行、`disposition=LEGACY_ONLY`，四个字段不得混用 | 与已交付工件逐字段一致，未改动；具名回归 `EvalSetTests.test_legacy_only_rows_carry_duplicate_key_probe_entries` |
| AC-1 修订 1 | 接受 S4 两两不交核对，失败用 `MANIFEST_COUNT_MISMATCH` 并停止，不允许映射覆盖 | 与已交付实现一致（§1）；具名回归 `EvalSetTests.test_leakage_assertions_fail_on_injected_test_frame` 的第二段 |
| AC-14 修订 3 | #20/#21 各按 (ii) 上游标签缺陷；无需重建/重绘/复判；实现者须把具名裁定与原判定/面板/排除证据绑成闭合记录，保留原开放收据，`freeze` 只放行已落实处置的面板 | 新增 `label_audit close` 与闭合记录（§8），`audit_gate_state` 只放行记录内面板；具名回归 `ReceiptTests.test_closure_record_releases_only_ruled_panels` 覆盖锚点校验、处置闭集、原收据保留、判定摘要失效与「noun 未排除不得闭合」五条 |
| AC-6 修订 2 | 计次口径（入口 ≤ 8 含失败、`precheck` 独立 ≤ 3）、混淆暴露按 E3 class+color unique 口径与构思数字分列 | §0 计次表与 §7 口径说明已按裁定改写 |

**本轮另行披露、未被任何 AC 覆盖的两项**（实现侧发现，交 `C1@K4` 判断是否需要处置）：

(f) **逐字节重复帧**（§4）：训练 3,198 帧只有 1,613 张不同字节的图（49.6%），并集 3,968 → 2,327。
    取样规则未变、泄漏断言按 SHA 仍为空集；风险是「帧数 ≠ 视觉多样性」，报告已按此措辞。
(g) **预筛颜色疑点 #33**（§8）：`Vehicle_Truck_color01 (1)` S5 `gray`/VERIFIED 而面板明显为红色。
    接受侧已裁定其仅作披露、不升级为用户语义核验、不扩展 #27 闭集；本项保留为未核验限制。

尚未做、也未授权：K3 全部内容（AC-7…13），包括权重下载、云端 GPU、上传与训练。
C1@K4 的逐条回证见 §12。

## 12. C1@K4 退回项的逐条回证（2026-09-15）

接受角色 `C1@K4`（2026-09-15，K4 唯一一次核对退回）列出 C1-1…C1-7 与四条预复核关注项。
逐条回证如下；全部是现合同内的修复，不新增 AC、不改取样与冻结数字。

| 项 | 修复 | 证据 |
|---|---|---|
| C1-1 失败仍写出正式工件 | `run_build` 改为「核验全过才发布」：帧 SHA 绑定、泄漏断言、分片实数行数、输入重算都在落盘前跑完；七份 jsonl / legacy 副本 / 四份 JSON 先算字节与 SHA，发布阶段任一写出失败即回滚本次新写文件，落盘后逐份复核字节 | `test:ReconciliationTests.test_late_binding_failure_publishes_nothing`（晚期绑定失败 → 只写失败收据、七份 jsonl 与四份 JSON 一个不留、输入清单不进 union） |
| C1-2 类别验证状态漏传 | 适配层按表 A′ 对「有 S5 条目但 `class_verified=False`」清 `class_word`（不改上游 `frame_world`）；phantom 的类别来自 prefab 名，不受影响 | `test:AdapterTests.test_table_a_prime_cases_including_three_wildcard_inputs` 第 6 段；**全量只读核算**：执行域内只有 `Vehicle_*`，8 辆无 S5 条目（表 A′ 所指的那 8 辆），有条目但未验证的 **0** 个 → 当前输入上零行改变，重建后六份 jsonl 与三份 JSON 逐字节不变（§9） |
| C1-3 G3′ 评分入口与绑定源断开 | 新增 `evaluate.load_gray_boxes`，`main` 自己接通取框；`load_definite_boxes` 先把当前 S3 分片与 S5 的 SHA 与 build 输入清单 union 逐件比对，缺源/未登记/字节已变一律 `INPUT_HASH_CHANGED`；入口失败写 `failure-return-*.json` | `test:MatchingTests.test_gray_diagnostic_uses_bound_s3_definite_boxes`（已扩到 CLI：正常评分 → G3p 命中率 1.0 且出 v1 附表；源字节变 → 退出码 1 + `INPUT_HASH_CHANGED` 收据） |
| C1-4 freeze 未验证预检成员闭集 | 先核 `gold_files` 与 `tokenizer.files` 是否等于合同闭集（不等 → `FROZEN_SET_MISMATCH`）；被绑定文件缺失按 `INPUT_HASH_CHANGED` 记收据，不抛原生异常；待冻结 jsonl 缺失按 `FROZEN_SET_MISMATCH` | `test:FreezeTests.test_freeze_requires_complete_audit_and_precheck_receipt` 第 3b/3c 段 |
| C1-5 写出边界只在辅助函数中成立 | `package` 在 `rmtree`/建目录/复制之前先守边界；`evaluate --out` 走 `assert_output_allowed` 并写失败收据 | `test:WriteBoundaryTests.test_package_entry_guards_forbidden_root_before_touching_it`（断言禁写根下既有文件零改动）；`test:MatchingTests.test_gray_diagnostic_uses_bound_s3_definite_boxes` 的 `--out` 段 |
| C1-6 抽查闭合消费端漏核验 | `audit_gate_state` 复核原开放收据存在且 SHA 相符、逐张面板身份（key/frame_id/surface/overlay/叠框对象）与「该 noun 仍未回到 gold」；任一不成立即不再放行 | `test:ReceiptTests.test_closure_record_releases_only_ruled_panels` 第 3b/3c 段（删原收据 → `ORIGINAL_RECEIPT_MISSING` 且 freeze 被挡；同编号换面板 → 身份不符） |
| C1-7 全套测试归因与基线证据 | 归因更正为 numpy 1 + cv2 8；基线原始输出留档为独立证据文件；skipped 63→21 按原因逐项归并说明（基线 worktree 不带 git 忽略的 `runtime/` 归档） | `artifact:docs/evidence/P1-ENG-SFT-002-tests.log` 末尾区块；`artifact:docs/evidence/P1-ENG-SFT-002-tests-baseline.log` |
| 关注项 1 #27 匹配口径 | 改用具名 `instance_base()`（只切 `" ("`），命中的是同一 prefab 的 `(n)` 实例，异名不误命中；排除域未扩大，冻结取样数字未改 | `test:AdapterTests...` 第 7 段（`Vehicle_Bus_color03x` 不等于反例） |
| 关注项 2 冻结绑定链 | `freeze` 把六份 jsonl 的现算 SHA 与**已提交**的 dataset/eval manifest 记录值逐份对照，不符即 `FROZEN_SET_MISMATCH` | `test:FreezeTests...` 第 3d 段（提交一份被篡改的 manifest → 拒绝冻结） |
| 关注项 3 表 F/G 的 K4 交付边界 | `summarise` 增表 F 的 v1 诊断附表（逐条 legacy 行映射到本次评估行与预测）与表 G 的逐组配对差（含 t 子组）；K4 只交实现与夹具覆盖，K3 用实际预测填，不在 K3 改冻结的评分定义 | `test:VerdictTests.test_layer_statuses_on_fixture_predictions`、`test:MatchingTests...`（`v1_diagnostic_rows` 非空） |
| 关注项 4 S0 与分片行数 | `reconcile` 增 S0 词表/关系类型/`viewer_side_min_separation_px`/`nearest_to_dominance_ratio`/目标车 `referable` 与执行时常量逐项核对；分片按扫描**实数**行数与 manifest 自报值逐片比对 | `test:ReconciliationTests.test_shard_line_count_and_s0_constants_are_verified`；manifest 的 `reconciliation.s0_constants_checked` 与 `s3_declared_lines_by_shard` |

顺带修掉一个自查发现的潜在缺陷：`Archives` 的输入清单沿用默认 `PROJECT_ROOT` 记路径，
夹具与复核 worktree 下会记成绝对路径，导致按相对键查绑定查不到；现按本次执行的仓库根记录。

## 13. C2@K4 未决项的逐条回证（2026-09-15）

`C2@K4` 结论是「附未决项交独立复核」（C1 已用掉 K4 唯一一次核对退回），交下来的是 C2-1…C2-5
与两条保留关注项。实现侧在交复核前逐条处理如下；全部在现合同内，不新增 AC、不改冻结数字。

| 项 | 修复 | 证据 |
|---|---|---|
| C2-1 失败发布仍未闭合 | 发布段先备份将被覆盖的旧字节，任一步失败（含写入期 `OSError`）即删新建、还原被覆盖文件；`package` 改为先逐份核对 data 成员与冻结收据、在 `upload.staging` 成包、末次输入重算通过后才原子替换旧包；`precheck`/`freeze`/`package` 一律先重算输入再写成功收据 | `test:PackageTests.test_failed_package_leaves_previous_package_intact`（旧包逐文件字节不变、暂存目录已清）；`test:ReconciliationTests.test_late_binding_failure_publishes_nothing` |
| C2-2 G3/G3t 配对差恒为零 | `paired_difference` 增 `outcome` 参数：集合组按**严格成功**配对（`success` 对集合组本就是 None），另给报告率与 macro F1 的配对差；逐组结果标注所用 outcome | `tools/eng_sft/evaluate.py` 的 `row_outcome` / `summarise`；`test:VerdictTests.test_layer_statuses_on_fixture_predictions` |
| C2-3 v1 附表只拼接旧 gold | 新增 `map_v1_output`（`invalid_output` → null、`reported_ambiguity` → ambiguous、有框 → unique、否则 none；机械映射、只作诊断），`v1_diagnostic_rows` 消费 `data/legacy/predictions.jsonl` 并给出与本次状态是否一致；`main` 自动加载 | `test:MatchingTests.test_gray_diagnostic_uses_bound_s3_definite_boxes`（CLI 段断言附表非空）；v1 的 `success` 按其当时单目标 gold 原样带出，不与本次三态 gold 混算 |
| C2-4 抽查入口未适配评估行字段 | 新增 `noun_type_of()` 按真实 `eval_record` schema 推导（`relation_program` → relation；否则看 `noun.color`），不改表 C 字段 | 实测：**修前** G2 的 49 行被归 J1、G3/G3t 的 60 行整个掉出抽样域；**修后** G1→J1 210、G2→J2 49、G3/G3t→J3 60、G1t/G2t→J5 46、G5→J4 100、G4→J6 86。具名回归改用真实 `eval.jsonl` 行验归层与抽样域（`test:SamplerTests.test_layer_quotas_and_uniqueness_are_deterministic`） |
| C2-5 计数与 skip 身份 | 本项用例静态枚举 **41**（build 28 / evaluate 6 / audit 5 / three_state 1 / parse 1），与 1197 − 1156 一致；tests.log 补 21 条 skip 的逐条身份与两侧差异归并 | `artifact:docs/evidence/P1-ENG-SFT-002-tests.log` 末尾区块 |
| 关注项 1（#27 实例匹配） | 保留披露：`instance_base()` 只切 `" ("`，当前 J7 的 341 条候选里 `counterexample_object_ids` 全是 `Vehicle_Bus_color03`，未见后缀实例扩域改变取样；`leakage-report` 的 seen 集含 `Vehicle_Bus_color03 (1)` 是**对象身份**，与 #27 的匹配口径无关 | 交复核沿真实适配输入核实；不据此扩展 #27 或改冻结数字 |
| 关注项 2（报告 §0 口径） | §0 计次表改为入口 11/12、precheck 2/5；计次口径段写明原信封 ≤8/≤3 与追加后 ≤12/≤5；「待补记」字样已去掉，改为接受角色已入账。（2026-09-16 更正：上一版本节已声称完成，但 §0 当时仍残留旧口径与「待补记」，接受侧交接核实时指出，现已改齐） | 本报告 §0 |

**C2-4 的已知缺口（交复核与接受裁定，实现侧不自行处置）**：用户已判定的 21 张面板是在**修复前**
的较窄抽样域下抽出的（J2/J3 只取到 train/select 侧，评估侧的 G2/G3/G3t 从未进域）。用户
2026-09-15 决定「先修代码、不重抽」，故本候选**不重跑 `plan`、不重绘面板、不请求复判**；
现有判定、闭合记录与面板收据原样保留。若复核或接受角色认为必须让抽查证据落在正确域上，
按表 J (i) 的路径需要一次新的面板生成额度（2/2 已用尽）与一次用户复判（1/1 未用）。
（后续：R1@K4 将该缺口定为 F1（CLASS_1），接受复判维持必修，用户批准追加额度；已按 §15 闭合。）

## 14. 限制（不因本报告改变）

gold 是 amodal 投影 AABB（框 `UNVERIFIED`，S6 未执行）；颜色词只覆盖 37 辆已验证车加目标车的
`red`；#27 反例所在帧的 `bus` 颜色指令整帧排除——用户 2026-09-14 对 #20/#21 的两次颜色「错」
经接受角色按表 J (ii) 具名裁定保留，即该帧内**其他**同类 bus 的颜色词同样不可信，这两帧的
`bus` 颜色 noun 已排除且不回写 S5；预筛 #33 的颜色疑点保留为未核验限制。本项不检验
「无纯色匹配时选最接近颜色」，也不得声称具备该鲁棒性。帧数不等于视觉多样性：训练 3,198 帧
只有 1,613 张不同字节的图（§4）。不生成 color-none；目标车是脚本生成的红色立方体车，
单一对象，unique ≤ 350、歧义 65 单列；`G1t/G2t/G3t` 不与 G1/G2/G3 混算；test 已被探针读过，本项
对冻结评估集另做零样本与微调评估各一次（均属候选 2，未授权）。本报告不含任何模型结果，
`IMPLEMENTED` ≠ `DONE`。

## 15. R1@K4 返工的逐条回证（2026-09-16/17）

`R1@K4`（`docs/reviews/P1-ENG-SFT-002.md`）判 `REWORK_REQUIRED`：F1 阻断（CLASS_1，AC-14），F2/F3
`SCOPE_GAP`，F4/F5 CLASS_3，§4 三条非阻断测试建议。接受角色复判维持 F1 范围内必修、F2/F3 记债 OPEN，
用户批准追加信封后，实现侧按提案「Acceptance rulings（复判）」的返工链执行。全部在现合同内：不新增 AC、
不重跑 `build`/`precheck`、不改六份 jsonl 与四份冻结 JSON、不改训练/评估样本、不改 #20/#21 处置。

| 项 | 处置 | 证据 |
|---|---|---|
| 返工前证据保留（复判第 1 条） | 旧 `audit-plan`、开放/闭合/冻结/打包收据、`input-manifest`、上传清单、50 张面板与面板收据复制到 git 忽略的 `receipts/history-r1k4-20260916/` 与 `panel/history-r1k4-20260916/`，`index.json` 逐文件记 SHA（109 份，复制时与原件逐一相等）；旧抽查文件以提交历史保存，另存一份副本 | `artifact:outputs/eng-sft/P1-ENG-SFT-002/receipts/history-r1k4-20260916/index.json` |
| F1 闭合要求 1：重跑 `plan` 并提交抽样契约 | 抽样域 J1 3003 / J2 1024 / J3 420（J4 690 / J5 584 / J6 86 / J7 341 不变）；用户 #1–#8、#12–#21 不变；#9–#11 = `G3-0116591d5f30e396`（the taxi）/ `G3-49e42113164cef2f`（the bus）/ `G3-7171c2f1cb6b531f`（the container truck），均 3 候选；预筛 #32–#41 按新计划。与 R1 F1 的枚举逐项一致 | `artifact:docs/evidence/P1-ENG-SFT-002-label-audit.md` §2/§3；`artifact:outputs/eng-sft/P1-ENG-SFT-002/receipts/audit-plan.json` |
| F1 闭合要求 1：`panels` 重绘（面板 3/3） | 新旧 `panel-receipt.json` 逐张比对 key/frame_id/object_ids/surface/原图 SHA/原图副本 SHA/叠加图 SHA：37 张全同，变化恰为 #9–#11 与 #32–#41 | `artifact:outputs/eng-sft/P1-ENG-SFT-002/panel/panel-receipt.json` 与历史副本 |
| F1 闭合要求 2：用户只判变化的 3 张（复判 1/1） | 三张均状态「对」、候选完整「对」；#10/#11 的边缘截断原话作备注。S3 可见比例（可见面积 ÷ 投影包围盒面积，≥ 0.25 且短边 ≥ 12 px 才算 `OK` 候选）：#9 三辆 100%；#10 三辆 100% / 41.5% / 25.7%；#11 三辆 91% / 90% / 48.8%。18 张沿用原判定，前提（身份与图字节一致）已由上一行核实 | `artifact:docs/unity-test-log.md#UT-P1-ENG-SFT-002-label-audit`（辅助角色代录，含旧面板身份的历史小节） |
| 实现者预筛（累计 39/39） | 新看 #32–#41 十张，全部状态对；逐张对照 S3 车辆清单核实画面中的疑似同类车（#34 左缘紫车为 SUV/TRUNCATED、#37 右缘蓝车为 car、#38 左缘灰车为 car、#39 楼后蓝车为 car 等）；其余 19 张沿用并注明 | 抽查文件 §6 |
| F1 闭合要求 3：`stats` → `close` | `stats`：旧闭合因用户份额变化过期 → `AUDIT_FINDING_OPEN`；**原开放收据逐字节保留**（SHA 前缀 `283d6ab9`，即旧闭合所绑定的那份），run 收据记 `preserved`。`close --disposition ii --ruling-anchor "AC-14 修订 3"`：panels 20/21，裁定出处按提案最近提交运行时解析，原收据 SHA 不变，判定摘要与用户份额摘要重绑 | `artifact:receipts/audit-finding-closure.json`；`artifact:receipts/run-audit-*.json`（`stage_detail` = stats/close） |
| F1 闭合要求 3：`freeze`（入口 12/14）→ `package`（入口 13/14） | 冻结闭集 8/8、六份 jsonl、预检收据 SHA 与上一张冻结收据逐项相同；`audit` 块：用户 21/21、`COMPLETE`、wrong [20, 21] 已闭合、新增 `user_share_digest`。数据包 2,335 成员，只有冻结收据副本变化 | `artifact:receipts/freeze-receipt.json`；`artifact:upload/manifest.json`；`artifact:receipts/package-receipt.json` |
| F1 闭合要求 4 的机械部分 | 代码侧 `SamplerTests.test_layer_quotas_and_uniqueness_are_deterministic` 已由 R1 核实红绿；本次在冻结 jsonl 上以候选代码重算 `sample_panels`，与新 `audit-plan.json` 的 50 张逐张相同（`plan` 与复算同源） | R2 定点复看：重算、面板收据、Unity 日志 #9–#11、闭合记录、冻结收据 `audit` 块、包内收据副本 |
| 追加加固 ①：闭合绑定用户份额（F1 的机械防线） | 新判定值与旧 #9–#11 恰好相同，判定摘要（前缀 `53b7ad5f`）前后不变；原实现下旧闭合记录会继续放行 `freeze`，即旧样本上的判定可被带到新样本上。现闭合记录绑定用户份额的样本身份 + 叠加图 SHA（`user_share_digest`），计划重抽或重绘后旧闭合失效，须按新计划重新 `close`；冻结收据 `audit` 块记下该摘要 | `test:tests.test_eng_sft_audit.ReceiptTests.test_replanned_user_share_invalidates_closure`（返工前源码 FAIL：`None != 'AUDIT_FINDING_OPEN'`） |
| 追加加固 ②：`stats` 不改写原开放收据（AC-14 修订 3） | 同一组「错」面板重跑 `stats` 时原收据逐字节保留；集合变化时先原样另存 `audit-finding-open.superseded-<utc>.json` 再写新收据；收据 `panels` 恒为面板序号 | `test:tests.test_eng_sft_audit.ReceiptTests.test_rerun_stats_keeps_original_open_receipt`（返工前源码 FAIL：收据字节被改写） |
| F4 / F5（CLASS_3） | 按 R1 逐字补丁应用：§10 上一停点计数与边界用例列表；§9 表后追加入口标签口径说明 | 本报告 §9/§10 |
| §4 第 1 条（C2-2） | 新增集合组配对差回归：G3 四行中两行答 unique → 逐组配对差 −50 pp、`outcome = strict_success`，并给报告率与 macro F1 配对差 | `test:tests.test_eng_sft_evaluate.VerdictTests.test_set_group_paired_difference_uses_strict_success`（C2 修复前源码 32233f9：`KeyError: 'outcome'`） |
| §4 第 2 条（C2-3） | 夹具旧探针预测行改带真实 v1 字段（`invalid_output` / `reported_ambiguity` / `parsed.bbox_2d` / `success` / `iou`，四种形态轮转）；经评分入口断言 `status_v1` 逐行映射、`status_agrees_with_v1`、`success_v1`/`iou_v1` 原样带出、重复键两条各自成行 | `test:tests.test_eng_sft_evaluate.V1DiagnosticTests.test_v1_outputs_map_to_three_states_and_pair_with_current_run`（32233f9：`KeyError: 'v1_prediction_present'`） |
| §4 第 3 条（C2-1 构建侧） | 第二次 `build` 在发布段写到一半抛 `OSError`：被覆盖的旧文件逐份按原字节还原、本次新建的文件删除、不编造失败收据、输入清单记未成功 | `test:tests.test_eng_sft_build.ReconciliationTests.test_second_build_publish_failure_restores_replaced_files`（32233f9：FAIL，旧字节未还原） |
| F2 / F3（`SCOPE_GAP`） | 按接受复判记债 OPEN，本返工**不修**：本批不重跑 `build`，`package` 只重打包同一批冻结数据（121 MB，远低于 0.3 GB） | `artifact:docs/implementation-status.md` 范围外已知缺陷账本 |

**测试**：focused 46/46（系统 python3，零 skip）；停点全套一次 Ran 1202、errors 9（基线同名同因）、新增失败 0（§10）。
新增 5 条的修复前红在一次性 worktree 中核实：①② 用返工前源码，§4 三条用 C2 修复前源码（在返工前源码上已绿，
说明只补测试、不改 C2 代码），核毕删除 worktree。

**需要披露的事实与限制**：

1. **原开放收据的最早版本已不存在**：2026-09-14 第一次 `stats` 写的开放收据，在 2026-09-15 第二次 `stats`
   时被旧实现改写（即加固 ② 修的缺陷）；现保留的是 2026-09-15 版本（panels 仍为 20/21），也是旧闭合与新
   闭合共同绑定的那份。无法恢复更早的字节，本报告不声称其仍在。
2. **判定表行本身不绑定面板身份**：代录格式 v1 只按 `panel_index` 记值。加固 ① 只在存在闭合记录时起作用；
   「新判定确实针对新图」仍靠代录时的逐行核对和 R2 的定点复看（R1 已标 `NOT_MECHANIZABLE`），本次未改代录格式。
3. **截断门槛是后续设计输入，不是本轮缺陷**：S3 允许可见比例低至 25%（即最多约 75% 在画幅外）才算候选，
   比 VisDrone（截断 > 50% 的目标评估时跳过）与 KITTI Hard（最大截断 50%）宽；#10 的 25.7% 公交车接近门槛。
   用户选择记「对」并保留原话；是否收紧门槛交接受角色，涉及重建数据、属于合同与授权变化，本轮不改。
4. 首轮预筛 #33 的颜色疑点、#20/#21 颜色「错」及其具名处置、F2/F3 记债均保持原状；K3 仍未授权。
