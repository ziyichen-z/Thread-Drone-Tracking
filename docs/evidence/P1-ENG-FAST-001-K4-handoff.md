# P1-ENG-FAST-001 K4 候选交接（Implementation / Claude Code，2026-09-24）

工作项：`P1-ENG-FAST-001`（engineering-v1，停点 `K4`，单候选）。合同：`docs/proposals/P1-ENG-FAST-001-fast-layer-replacement-probe.md`
（D3 `ACCEPTED`）。执行信封：`docs/authorizations.md` 2026-09-24「用户签发 §5 执行信封」。报告：`docs/evidence/P1-ENG-FAST-001-report.md`。

用户在本实现会话开工时的两项选择（`AskUserQuestion` 所选选项标签逐字，非授权、不扩信封）：
「一口气做到 K4 候选（推荐）」；「取保守读法继续，逐条记入证据交 C1 裁定（推荐）」。

## 实现读法（待裁定）

合同字面未写死、或字面与合同自带数字/事实不一致处，按用户选择取保守读法继续，逐条列出交 `C1@K4` 裁定；
被否即返工。**不改任何阈值、门值与合同已定分母**；每条写明字面、所取读法、理由与影响。

| 编号 | 合同位置 | 字面 / 冲突 | 所取读法 | 理由 | 影响的数字 |
|---|---|---|---|---|---|
| IR-1 | §3.5.1 候选集；事实 13/17；§3.5.2 臂 B/C 查询数；§5 对账 | 正文「目录 `OK` 可指称**车辆** ∪ 已绑定动态目标（`has_dynamic_target` 且规则 ① 有框）」；但合同自带数字（每帧 0/12/55、合计 6,597，K=0 21 行，Σceil(K/16)=929、臂 C 588）复算只在「帧内**全部** `OK` 物体（含树、道具、建筑）∪ 行级 `has_dynamic_target`」下成立。另：`has_dynamic_target` 是**行级**「答案含目标车」标志，按字面只在目标车就是答案时才把它列为候选，泄露答案（242 行目标车在画面且已绑定、但不是答案） | 候选 = 冻结适配器执行域内 `status = OK` 的目录**车辆** ∪ **帧级**已绑定目标车（`unity_s3.adapt_frame` 的 `dynamic_target_definite`，规则 ① 有框） | 与正文「车辆」、§1(c)「oracle 候选」语义一致；避免答案泄露；gold 覆盖 100%（609 行全部 gold 对象都在候选集内） | K=0 26 行（合同 21）；每行 K ≤ 12，臂 B 583 页（合同 929）、臂 C 583 行（合同 588）；基线查询 1,166（合同 1,517），仍在 1,700 上限与 183 重试余量内 |
| IR-2 | §3.1 scout-1 真值 schema | 写 `p1-detect-scouting-truth/v2`；实际 705 个文件全为 `/v1`（框为 `{x,y,width,height}` 对象） | 接受 v1/v2 两种 schema（逐文件核对、同一序列 schema 唯一） | 字段一致，只是版本号不同 | 无 |
| IR-3 | §3.2.1「没有 `object_id` 的真值框（scout 干扰车）标 `INSTANCE_UNKNOWN`」 | scout 真值的 `distractor_id` 就是 Unity 对象名（如 `Vehicle_Taxi (2)`），与目录 `object_id` 同一命名空间 | 用 `distractor_id` 计算 `same_instance_in_bank`；无 id 的框仍标 `INSTANCE_UNKNOWN` | 前提（「没有 object_id」）不成立；按 id 标记比合并成 unknown 更能揭示同实例回流 | scout 干扰车分子行 |
| IR-4 | §3.3 P2a 帧对 | 未写抽样规则、层取哪一帧、帧池是否含未分配帧、动态目标是否算「同类车」 | f_i 上 o 与 ≥1 辆同类 `OK` 车同框；f_{i+Δ} = 同会话（帧目录父目录）最近帧、±0.2 s，o 仍 `OK` 且另有 ≥1 辆同类 `OK`；帧池 = S3 全部可用帧（与 §8 各族计数 a2 698 / a9 588 / … 逐族一致，含未分配帧）；只取已知类别目录车（不含目标车）；每 Δ 按 `sha256(seed|Δ|anchor|object)` 序取前 300 对；层 = o 在 f_{i+Δ} 的框 | 确定性、可复算；与合同 §8 帧池数字一致 | margin.json 全部 |
| IR-5 | §3.4 P2b 输入 | 未写喂跟踪器的检测来自哪一档；无真值文件的帧（scout-1 63 帧）归属未写；`TRUTH_GAP` 段跨窗口末端时是否截断未写；碎片定义「V 内漏检连续段」的连续性 | 检测 = 各来源对应参考库的 T0-bank（cpu，缓存，与召回同一份）；无真值帧不在 V（按 `INVISIBLE` 调用帧处理）；`TRUTH_GAP` 只数窗口内部分；碎片 = 按 V 帧序（跳过不可见帧）的 ∅ 极大段数 | T0-bank 是合同「基线，必做」档；其余取不放宽的读法 | replay.json |
| IR-6 | §3.5.2 臂 D 类别库 | 「train∪dev 族裁图库」规模与抽样未写 | 已验证类别的 `OK` 目录车与帧级已绑定目标车（记 `car`），短边 ≥16 px；每个 `object_id` 按确定性哈希序取前 20 张 | 规模可控、确定性；不按结果调整 | 臂 D |
| IR-7 | §3.5.2 臂 D 颜色 | 「HSV 色相直方图对六色原型」；六色含 `gray`，纯色相无法表示无彩色；「S5 VERIFIED 颜色对象」未限定类别 | 18 个色相桶（S ≥ 64、V ≥ 51 的像素）+ 1 个无彩色桶，L1 归一化，L1 最近邻；原型取 S5 `VERIFIED` 且颜色在六色词表内的**车辆**（帧目录索引只含车辆执行域），每对象 ≤10 张 | 灰色需无彩色桶才可表示；车辆颜色与指令对象同类 | 臂 D 颜色指令 |
| IR-8 | §3.4 / 事实 20 / AC-5 `library_buffer_boundary` | 事实 20 读码：空检测 L ≤ 30 同 ID、L ≥ 31 新 ID；合同同时写「这是对库边界的实测，事实 20 的读码结论以它为准」 | **实测**（两算法相同）：30 → 同 ID；31 → **仍同 ID**；32 → 新 ID（`merge_track_pools` 先按 `removed_stracks` 剔除 lost 池、后追加本帧移除项，被标记移除的轨迹在下一帧仍参与关联）。测试按实测断言；§3.4 判定阈值仍按字面（L ≥ 31 → `LOST_BEYOND_BUFFER`），L = 31 的原 ID 找回单列子计数 `drift_return_at_L_eq_buffer_plus_1` | 以实测为准记录库边界；判定取字面阈值 = 对保持率保守 | replay.json 的 `LOST_BEYOND_BUFFER` 与 drift 子计数 |
| IR-9 | §3.5.2 臂 B/C 渲染与 prompt | 编号起点、框/字颜色、标签位置、网格空格、编码未写；prompt「只把坐标段/回复段换成索引版」 | 编号从 1 起（行优先：y 再 x）；臂 B 固定 4×4、每格 224 px + 32 px 标签带（896×1024，32 的倍数、处理器不缩放），空格灰底；臂 C 白色 1 px 框、黑底白字编号置于框外（上方放不下则放框下）；JPEG q95、同帧同页去重；prompt = v2 首段 + 词表段 + （G4）关系段逐字，坐标段/回复段换成索引版（全文按 sha 入 `vlm-arms.json`） | 白色不在六色词表内，避免框色诱导颜色指令；不缩放保证处理器输入即渲染图 | 臂 B/C |
| IR-10 | §3.5.2 smoke / §3.5.3 重试 | smoke「前 32 行」是否含 K=0 行、INVALID 率按首次还是重试后、重试时机未写 | smoke 行 = 全部 609 行按 `row_id` 字典序前 32 行（K=0 行不查询）；INVALID 率按**首次尝试**；重试在全部基线查询之后逐页 1 次 | 首次尝试更严格；先保证基线覆盖 | 臂 B/C 停臂判定 |
| IR-11 | §3.5.1 臂 A 换算与 G3′ | `ambiguous` 预测中部分框无候选达 0.5 时如何计；G3′「任一 gold 成员」的 gold 集 | 任一预测框无候选达阈值 → 标 `NO_CANDIDATE_MATCH`，该行成功/严格成功记失败；G3′ 成员 = `definite_ids` | 不放宽成功判据 | 臂 A |
| IR-12 | §3.3 FP/帧 | 真值清单不完整（scout 只列 1–2 辆干扰车、BODY 不列干扰车） | 按字面「未与任何真值框匹配」计，报告注明真值清单范围 | 描述性，不与决策计数比较 | FP/帧 |
| IR-13 | §3.2.2 轴向深度表 | 目录帧的目标车没有 `camera_depth_m` | 目标车在轴向深度表记距离档 `NA` | 不从其他字段推算 | 目录帧红立方体格 |
| IR-14 | §6.2 R1「scout-1 + BODY」 | 两来源参考库不同（scout-1/arm A 池 {a2}，arm B 池 train∪dev） | 聚合行照出并在行名标注两池混合；各来源分行另列 | 不隐藏池差异 | R1 |
| IR-15 | §3.6 / AC-9「目录哈希清单」 | 清单粒度未写 | `runtime/` 全树逐文件 (路径, 字节, sha256) 前后比对 + `git status --porcelain -- runtime` | 最严格读法 | ledger.json |
| IR-16 | §3.5.1 LEGACY_ONLY | 排除所有报表；是否查询未写 | 照常查询（在 583 行内），报表排除、只列计数 | 与合同原查询规模的口径一致 | 查询数 |
| IR-17 | §3.6 时延帧 | 「≥300 帧」取哪些帧未写 | scout-1 前 320 帧（默认几何），5 帧预热不计；T0-bank-a2 | 默认几何、确定性 | latency.json |

## 自证四项（workflow §4.3.1；按 AC 编号附证据指针）

1. **范围与接口已冻结**：候选只新增 `tools/eng_fast/`（`inputs`/`detect`/`recall`/`margin`/`replay`/`vlm_arms`/`vlm_remote`/`baseline`/`report`，
   另有编排 `run`/`run_more` 与公共件 `common`/`ledger`）、`tests/test_eng_fast_{inputs,recall,margin,replay,vlm_parse}.py`、`.gitignore` 一行
   `/outputs/eng-fast/` 与 `docs/evidence/P1-ENG-FAST-001-*`；冻结件（`Assets/`、`config/`、`controller/`、`tools/eng_sft/`、
   `tools/run_detector_scouting.py`）零字节改动，只导入（AC-11）。产物全部在 `outputs/eng-fast/P1-ENG-FAST-001/`（git 忽略）。
2. **相称的实现者测试通过**：见下文「测试」小节（focused 与停点全套各一次；全套分列基线既有失败与本批新增失败）。
3. **已知 Unity 失败**：不适用——零 Play、零 Unity 运行；纯离线 `UNITY_NA` 分类待 `R1@K4` 复核附议。
4. **复核文件/状态板/候选 commit/未验证风险已更新**：状态板交接行改交接受角色 `C1@K4`；候选 commit 由 git 派生（本文件所在提交），
   不手写 SHA；未验证风险见下文「未验证风险」。

## AC 证据指针

| AC | 证据 | 状态 |
|---|---|---|
| AC-1 输入身份与参考库隔离 | `docs/evidence/P1-ENG-FAST-001-inputs.json`（`sources`、`banks`、`isolation_assertions`、`detector_identity`）；`tests/test_eng_fast_inputs.py`（含反例 `test_reference_from_evaluated_atom_fails`） | 5 个来源两条断言全过；{a2} 池 `BANK_PARTIAL(5/9)` |
| AC-2 P1 分桶召回 | `docs/evidence/P1-ENG-FAST-001-recall.json`（`tables.slant_range` / `tables.axial_depth`、`fp_per_frame`、`applicability_matrix`）；`tests/test_eng_fast_recall.py` | 出数；无单一总召回 |
| AC-3 旧数复算 | `recall.json` `legacy_alignment`：scout-1 0/45、scout-4 172/187，逐 tick 命中 0 处不一致，max IoU 差 0.0 / 1e-6 | `ALIGNED` |
| AC-4 P2a margin | `docs/evidence/P1-ENG-FAST-001-margin.json`；`tests/test_eng_fast_margin.py` | Δ 1/5/13 s 各计分 300 对（合格池 3,784 / 819 / 464） |
| AC-5 P2b 回放 | `docs/evidence/P1-ENG-FAST-001-replay.json`；`tests/test_eng_fast_replay.py`（11 条具名反例 + `adapter_boxes_fields`、`one_update_per_frame`、`library_buffer_boundary`，后三条需 `.venv-yoloe`） | 出数；库边界实测与事实 20 差 1 帧（IR-8） |
| AC-6 P3 四臂 | `docs/evidence/P1-ENG-FAST-001-vlm-arms.json`；`tests/test_eng_fast_vlm_parse.py` | 见下文「P3 查询与对账」 |
| AC-7 P4 | `docs/evidence/P1-ENG-FAST-001-report.md` §P4 | 写明 |
| AC-8 读数表 | `docs/evidence/P1-ENG-FAST-001-report.md` §读数表 | R1–R8 逐格、附「不可推出」 |
| AC-9 只读与账目 | `docs/evidence/P1-ENG-FAST-001-ledger.json`（`counters`、`events`、`runtime_readonly`） | 见下文「消耗对账」 |
| AC-10 时延 | `docs/evidence/P1-ENG-FAST-001-latency.json` | CPU/MPS 各 320 帧；无 Jetson/5060 检测时延字段 |
| AC-11 冻结件零改动 + 全套测试 | `git diff --stat <base>..<candidate>`（base = 开工提交的父提交，可由 `git log` 派生）；`docs/evidence/P1-ENG-FAST-001-tests.log` | 见「测试」 |

## 测试（COORD-009：开发期 focused；停点全套一次）

- 证据：`docs/evidence/P1-ENG-FAST-001-tests.log`（系统 `python3` 全套一次 + `.venv-yoloe` 补跑 `test_eng_fast_*` 一次）。
- 全套：`Ran 1578`，`FAILED (failures=1, errors=9, skipped=27)`。
  - **基线既有 errors 9 个**，逐名与 `docs/evidence/P1-ENG-LOOP-001-tests-k1k2k3-c5-fix.log` 相同（系统解释器缺 cv2 等钉版依赖的导入失败与 `test_rate3_reanchor_clock_mismatch_raises_defensively`）。
  - **基线环境 failure 1 个**：`test_dist_data_round4.RealArchiveClosureTest.test_zero_unmatched_and_zero_multi_matched_jpg`（zero-match 916，
    列出的是 `runtime/frames/*.jpg`）。`runtime/frames/` 的 257 个文件是 LOOP-001 `diag-loopb-6`（2026-09-23 18:23）的诊断残留，本批开工前的
    `runtime/` 全树清单里就有、本批前后全树哈希一致（ledger.json `runtime_readonly.identical = true`）；该测试只导入 `tools.dist_data`。
    LOOP-001 各日志在隔离副本中运行，此测试在副本里 skip（skipped 68 vs 本次 27），故其日志无此项。
  - **本批新增失败：0**。本批新增 5 个测试文件在系统解释器下 40 通过 + 3 跳过（库边界 3 条需钉版库）；在 `.venv-yoloe` 下 44 条全部通过。
- 本批**零改动**任何既有代码或测试文件：`git status --porcelain -- Assets config controller tools/eng_sft tools/run_detector_scouting.py` 为空。

## P3 查询与对账

- 候选集按 IR-1：K=0 26 行、臂 B 583 页（全部单页，K ≤ 12）、臂 C 583 行。smoke（`row_id` 字典序前 32 行）首次尝试 INVALID：B 0/32、C 1/32
  （3.1%），两臂均未停。基线 1,166 + `INVALID` 重试 35（B 9、C 26）= **1,201** 次查询（上限 1,700；重试余量 183 用 35）。
- 重试全部与首次输出相同（greedy 确定性解码），最终 INVALID 行 B 9、C 26，按 §3.5.3 计失败并单列。
- Mac 端用同一解析器复解析 1,201 条回传，与 5060 记录 0 处不一致。
- 交叉核验：臂 A(C2) 按候选匹配换算后 G1 = 161/210，S/M/L = 11/30、77/95、73/85，与 SFT-002 原 IoU 口径 76.7% / 36.7% / 81.1% / 85.9% 逐格相同；
  A(base) G1 108/210 = 51.4% 亦同。

## 消耗对账（§5 信封；AC-9）

| 项 | 上限 | 实际 | 说明 |
|---|---|---|---|
| Mac YOLOE 进程启动 | 10 | 2 | detect 1、latency 1 |
| Mac DINOv2 进程启动 | 8 | 3 | margin 1、armd 1、latency 1 |
| 5060 base 启动 | 4 | 2 | 第 1 次启动命令 PowerShell 解析失败（嵌套引号），脚本未执行、零模型加载、零查询，Mac 账本动作前已扣，按保守口径保留；第 2 次实际加载 1 次（5060 `budget.json` `base_start` = 1，base `model.safetensors` sha `7de1838c…` 与 LOOP-001 记录一致） |
| 5060 查询 | 1,700 | 1,201 | 基线 1,166 + 重试 35（重试余量 183） |
| 下载 | 1 | 1 | `lap-0.5.13-cp312-cp312-macosx_11_0_arm64.whl`，1,478,096 B，sha256 `8a793935…1074`（与 PyPI 公布一致），预编译 wheel、无源码编译 |
| Mac pip 安装 | 1 | 1 | `uv pip install --no-deps --offline` 本地 wheel 进 `.venv-yoloe` |
| 5060 pip 安装 | 0 | 0 | |
| 传输 代码与清单 | 300 KB | 112,129 B | `fast001-code.tar.gz`（盲索引 + 清单 + `vlm_remote.py`，gzip 后按实际传输字节计） |
| 传输 图包 | 150 MB | 44,283,392 B | 736 张渲染图，无原始帧 |
| 传输 回传结果 | 5 MB | 803,965 B | 5 个文件（`results.jsonl` 794,181 B、`budget.json`、`state.json`、`run-summary`、`run.log`） |
| Play / ID / 模型 API / 训练 GPU·h | 0 | 0 | |

逐项事件（动作前扣额的时间戳、sha、字节）见 `docs/evidence/P1-ENG-FAST-001-ledger.json`；`runtime/` 前后全树清单一致（97,505 个文件）。

## 复核范围（交 `C1@K4` 核对后给 `R1@K4`）

- **完整候选 diff**：本候选提交相对开工前一提交（`git log` 可派生）的全部改动——`tools/eng_fast/*`、`tests/test_eng_fast_*.py`、`.gitignore` 一行、
  `docs/evidence/P1-ENG-FAST-001-*`、状态板。
- **重点核查**：(1) IR-1…IR-17 的读法是否可接受（尤其 IR-1 候选集与 IR-8 库边界）；(2) §3.2.1 参考库选择与原子隔离（`inputs.select_bank` /
  `bank_pool` / `bank_assertions`）；(3) §3.4 七类结局判定与守恒（`replay.window_outcome` / `window_summary`）；(4) §3.5.3 分页合并闭集与解析器
  （`vlm_remote.parse_index_reply` / `vlm_arms.merge_pages`）；(5) 报告读数表无「换栈/保留」结论、每格有「不可推出」；(6) 冻结件零改动与 `runtime/` 只读。
- **复现方式（零消耗部分）**：`python3 -m unittest tests.test_eng_fast_inputs tests.test_eng_fast_recall tests.test_eng_fast_margin tests.test_eng_fast_replay tests.test_eng_fast_vlm_parse`；
  库边界：`.venv-yoloe/bin/python -B -m unittest discover -s tests -p "test_eng_fast_replay.py"`；召回/回放/评分/报告可在主树用缓存重算
  （`.venv-yoloe/bin/python -m tools.eng_fast.run recall|replay|score|report`，不启动模型、不查询）；检测、margin、臂 D、时延与 5060 查询会消耗信封额度，
  复核不应重跑。缓存与回传原件在 `outputs/eng-fast/P1-ENG-FAST-001/`（git 忽略，复核副本需只读链接主树该目录）。
- **`UNITY_NA` 附议**：本项零 Play、只新增离线工具与报告，不改 Unity/控制器，请复核角色在 `R1@K4` 附议或驳回。

## 未验证风险

1. IR-1 改变了合同自带的查询规模数字（929/588 → 583/583）；若接受角色裁定应按「全部 `OK` 物体」出候选，臂 B/C 需另起查询（信封剩余 499 次，
   不够重跑两臂全部 1,517 次，届时须回用户）。
2. IR-8：钉版库实测边界比事实 20 多 1 帧；判定仍按字面阈值，L = 31 的原 ID 找回已单列（scout-4 8 s 窗口 73 起），若裁定改用实测边界，
   `LOST_BEYOND_BUFFER` 与保持率需按缓存重算（零消耗）。
3. 臂 D 的类别库与评估候选多为同一场景静态实例（`same_instance_in_bank` 60.4%），臂 D 成绩含同实例回流，只作 §6.2 R7 的描述性对照。
4. 颜色原型只覆盖 5 色（train∪dev 无 `VERIFIED` 的黄色车辆），含「yellow」的指令在臂 D 必然无法命中；609 行中未出现 yellow 颜色指令。
5. 臂 B/C 的渲染细节（IR-9）属实现选择，未做敏感性对照；时延不含同机 Unity 负载。
