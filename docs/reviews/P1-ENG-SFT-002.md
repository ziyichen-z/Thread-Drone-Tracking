# P1-ENG-SFT-002 — 独立复核（engineering-v1）

Latest round: R1@K3 — PASS_WITH_NOTES（见文末「## R1@K3 — 2026-09-18」；R2@K4 块保留在其前；本抬头保留 R1@K4 原文，轮次只追加，各通过轮的机读行在各自轮块内，「上一通过候选」由文件中最近一行 `passed_candidate` 派生）

Reviewer/role: 复核角色 / independent verification（新鲜上下文会话，Fable 池 `/review`；
档位不低于实现者）
Workflow: engineering-v1（提案抬头第 3 行逐字 `Workflow: engineering-v1`；接受角色 2026-09-13
D3 `ACCEPTED` 决策记录逐字「裁定本工作项走 `Workflow: engineering-v1`，自本次 `ACCEPTED` 生效」
→ 工程轨道，按 `docs/engineering-workflow.md` §5/§6 与 `docs/roles/review.md`「工程轨道」节执行；
依据列仍取 workflow §4.4 六值闭集，`BC-n` 读作任务合同 `AC-n`）
Round: R1@K4
Date: 2026-09-16
Implementation snapshot: 状态板 Active handoffs 行「C2@K4 已完成，附未决项交独立复核」与提案
决策记录 2026-09-16 条把候选指向提交主题「P1-ENG-SFT-002 C2@K4 返工交接：重冻结重打包完成，候选交
R1@K4」（`git log --grep` 运行时解析 = `76c9773d…`）；其后实现角色又提交了主题「P1-ENG-SFT-002 K4
候选证据补丁：报告 §0 计次口径与授权状态改齐（仅证据文档）」的 HEAD（2026-09-16 21:41 −0400），
`git diff 76c9773..HEAD` 只触及 `docs/evidence/P1-ENG-SFT-002-data-report.md`（+5/−3），`tools/`、
`tests/`、四份冻结 JSON 与 `.gitignore` 逐字节相同。本轮以 **HEAD 为候选**（AC-6 的交付物就是该
报告），下方 `round_candidate` 取 HEAD；交接行的候选指针在状态板同批改齐。本 work ID 无上一通过
候选；全量 diff 基线 = 核对表所写「`tools/eng_sft/build_sft_data.py` 首次加入提交的父提交」
（`git log --reverse --diff-filter=A` 解析 = `4306485…`，与停点全套日志的「开工前提交」相同）：
33 个文件 +16,313/−24 —— A1 源码 `tools/eng_sft/{__init__ 9, receipts 363, three_state 138,
prompt_v2 211, parse 135, evaluate 679, label_audit 1306, build_sft_data 2550}.py`、
`tools/eng_sft/adapters/{__init__ 4, unity_s3 203}.py`；A1 测试 `tests/test_eng_sft_{build 976,
evaluate 359, audit 331, three_state 86, parse 70}.py`、`tests/fixtures/eng_sft/{__init__ 1,
synth 658}.py`；A2 八份 `docs/evidence/P1-ENG-SFT-002-*`（报告 356、dataset-manifest 616、
eval-manifest 217、leakage 99、legacy-conservation 4,075、label-audit 141、tests.log 316、
tests-baseline.log 231 行）；`.gitignore` 一条 `/outputs/eng-sft/`；其余 13 份为他角色文档
（授权账本、状态板、三份 SFT 提案、Unity 日志、正式设计）。`controller/`、`Assets/`、`config/`、
`ProjectSettings/`、`Packages/`、`tools/dist_data/`、`tools/eng_asset/` 零字节改动。
round_candidate: d17d81f688c1b4217a3d0a985466d5616089bb0c
Verdict: REWORK_REQUIRED

## 0. 复核范围与停点

- **停点与合同**：K4 = 候选 1，合同 §7「AC-1…6 + AC-14」，加首次接受释义 8 行与待裁定节
  6 行修订（AC-1 修订 1、AC-3 修订 2、AC-4 修订 2、AC-6 修订 2、AC-14 修订 2/3）。C 轮记录
  （`C1@K4` 退回一次、`C2@K4` 附 C2-1…C2-5 与两条关注项照交）与报告 §12/§13 只作待核实主张。
- **开轮资格（workflow §4.4）**：`git diff 4306485..HEAD` 在 PLAY_GOVERNING 集合上非空
  （`tools/eng_sft/` 10 文件、`tests/` 7 文件，+8,079 行，全部新增）→ 开轮。未触及 Play
  治理门文件（`analyze_m3_body.py`、`preflight_reanchor_env.py`、`controller/run_log.py`），
  无闭环轮义务。Active handoffs 无 `Consuming=yes` 行，本轮无 `blocks_consuming_gate`。
- **停点自证核实（workflow §4.3.1 四项）**：条件 1（范围/接口冻结：八文件冻结闭集 SHA 与
  `git ls-files` blob 在候选上逐一等于冻结收据）、2（相称测试：`tests.log` 末尾
  `Ran 1197 … errors=9, skipped=21`，基线日志 `Ran 1156 … errors=9, skipped=63`，9 项 ERROR
  两侧同名、均为导入期缺 `cv2`/`numpy`；本轮 focused 41/41 重跑通过）、3（零 Unity Play，申请
  `UNITY_NA`）、4（交接行、候选、风险已写；候选指针落后 HEAD 一个仅文档提交，见上）按字面
  成立，**不给 `REVIEW_BLOCKED`**。
- **副本与只读边界**：`git worktree add --detach .claude/worktrees/review-P1-ENG-SFT-002 <HEAD>`；
  读码、重跑、红绿与探针全在副本；主树 `outputs/eng-sft/P1-ENG-SFT-002/`（git 忽略：
  `data/`、`receipts/`、`upload/`、`panel/`）与 `outputs/eng-sft/tokenizer/` 只按绝对路径**只读**
  核对；未运行 `build`/`precheck`/`freeze`/`package`/`panels`（受限入口计次不变：11/12、2/5、
  2/2）；F1 的探针只在内存里调用 `label_audit.load_candidates` + `sample_panels`（纯函数，读六份
  jsonl，零写入、零收据）。红绿在另一个一次性副本（`32233f9` 修复前源码 + 候选测试）完成后即删。
  收工删除副本。
- **重跑（不信报告数字）**：副本内系统 `python3`（3.14.6）
  `python3 -m unittest tests.test_eng_sft_build tests.test_eng_sft_evaluate tests.test_eng_sft_audit
  tests.test_eng_sft_three_state tests.test_eng_sft_parse` → `Ran 41 tests in 7.367s … OK`（0 skip；
  输出写会话 scratchpad `review-focused.log`，只回显摘要）。静态枚举 `def test_`：build 28 /
  evaluate 6 / audit 5 / three_state 1 / parse 1 = 41 = 1197 − 1156（C2-5 成立）。测试树哈希
  `HEAD:tests` = `dd244b6e197fb723a18c38bf976414ca1d71763e`，`HEAD:tools/eng_sft` =
  `27558da61589b80dcb4fec89443587cb62790cd1`。
- **修复前红（C2 返工，非本轮阻断 finding 的义务，供 AC 行核实）**：副本 `32233f9`（C2 修复前
  源码）+ 候选的 `tests/test_eng_sft_{audit,build}.py`：`SamplerTests.test_layer_quotas_and_
  uniqueness_are_deterministic` **FAIL**（`'J1' != 'J2'`，C2-4 红）；`PackageTests.test_failed_
  package_leaves_previous_package_intact` **ERROR**（旧 `run_package` 先删包后校验，C2-1 红）；
  `VerdictTests.test_layer_statuses_on_fixture_predictions` 与 `MatchingTests.test_gray_diagnostic_
  uses_bound_s3_definite_boxes` 在修复前源码上**仍通过** → C2-2/C2-3 的具名证据不覆盖其修复（§4）。
- **工件独立核实（主树只读）**：冻结收据（`utc 20260915T053851Z`，`head` = `dcc53f2…`）的
  `frozen_set` 8/8 `sha256` 与 `git_blob` 等于候选副本现算/`git rev-parse HEAD:<path>`；六份 jsonl
  字节/SHA 等于收据 = 等于已提交两份 manifest 的 `files`；预检收据 SHA `d552c351…` 等于收据与包
  清单绑定值；`upload/manifest.json`（SHA `1abf8784…` = `package-receipt.json`）2,335 成员 =
  磁盘（无多无缺，不含自身）、8 个非帧成员逐 SHA 相符、随机 40 张帧 `sha256 == 文件名 == 清单`、
  运输映射 2,327 → 3,968、`contains_code=false`、无 `eval.jsonl`/`select-eval.jsonl`/`legacy/`/
  泄漏报告/`.py`；`upload/` 121,013,624 B（含清单 1,061,553 B；清单 `total_bytes` 119,952,071 不含
  自身）、`data/` 6,635,477 B、`panel/` 6,956,522 B、`tokenizer/` 11,491,943 B，均在 AC-6 上限内；
  收据峰值 RSS ≤ 413,925,376 B、单次 ≤ 64.5 s。受限入口计次按收据文件逐一数：`run-build` 3 +
  `freeze` 4（含 1 失败）+ `run-package` 4 = 11 ≤ 12、`run-precheck` 2 ≤ 5、`stage_detail=panels`
  2 ≤ 2、预筛 29 ≤ 36、用户 21 张一次、复判 0 —— 与报告 §0 一致。六份 jsonl 逐行核对：609 行
  /十组计数/gate 行 407（G1+G2+G3+G5）/`gold_state=null` 只在 G3p 50 + LEGACY_ONLY 8/
  `legacy_probe` 405（3 行各 2 条）/盲行五键且 row_id 逐行对应/训练 4,907（4006/490/411，歧义
  `oversample_copies=2`，多重集 5,318，帧 3,198，目标车 unique 350、歧义 65）/冒烟 32 ⊂ 训练/
  选层 441（41/300/100）/守恒 405（ADMITTED 396 + LEGACY_ONLY 9，`eval_row_id` 全部存在）/
  训练∪选层 ∩ 评估按 SHA = ∅/训练不同字节图 1,613、并集 2,327；`audit-j7-candidates.jsonl`
  341 行的 `counterexample_object_ids` 全为 `Vehicle_Bus_color03`（关注项 1：`instance_base` 未
  扩域，`leakage-report` seen 集里的 `Vehicle_Bus_color03 (1)` 是对象身份）。
- **红线检查**：`tools/eng_sft/` 不 import `controller.*`（`test_no_controller_imports` + 通读）；
  只读 S0/S1(kind≠truth)/S3/S4/S5、ASSET-001 指令逐行与摘要、T7 探针清单/预测；不读真值文件；
  写出闭集含 `runtime/*`、`config`、`Assets`、`controller`；不改运行时任何文件；训练标签属离线
  数据加工。无 `RED_LINE`。

## 1. 逐条 AC 核对

| 编号 | 结论 {满足, 不满足, 证据缺失} | 证据 | 理由 |
|---|---|---|---|
| AC-1（含修订 1） | 满足 | `build_sft_data.reconcile`/`scan`/`run_build`；`ReconciliationTests` ×3、`ReceiptTests.test_input_manifest_phases_append_only`；dataset-manifest `reconciliation` | S3 43,535/151 片逐片字节+SHA+`lines` 自报与扫描实数比对、S4 2,523/13,144/8,450/0 且两两不交（`MANIFEST_COUNT_MISMATCH`）、S5 690/93/37、S0 五项常量与执行时常量相等、指令/S5 SHA 与探针 `source` 相等、七值直方图 57,430 行逐值相等（`HISTOGRAM_MISMATCH`）；输入清单阶段 `<stage>#n` 只追加；发布段先算字节再核验、失败备份/还原（C2-1，读码 + `test_late_binding_failure_publishes_nothing`）。预测文件缺失时 `Archives.load` 放行见 F3（非阻断）。 |
| AC-2（含修订 1） | 满足 | `adapters/unity_s3.py`、`three_state.py`、`build_training_sets`；`AdapterTests` ×2、`ThreeStateTests` ×2、`SplitTests` ×2；dataset-manifest `steps` | 表 A′ 逐行（OK/非 OK/未知类别/phantom/未验证类别清 None/目标车 definite 与裁剪框/三种 wildcard/#27 `instance_base`）、表 A 六态按序含规则 ①；E1 七族闭集与选层族、E2 键 `(族,状态,noun_type,键,idx)` 与 2/5 间隔、E3 700/350（class+color 合计）、E4 60、E5 ⌊0.10(U+A)/0.90⌋ 固定顺序轮转 ⌈N/9⌉、E6 k 最小整数≤8、E8 41+300+100、E9 seen 逐字按表 D′/E；哈希 `sha256(seed|frame_id|key)`、并列 `(h, frame_id, key, noun_type, surface)`；manifest 实取 4,006/411/490/k=2/5,318/4,907/3,198/441/322/76 与 §8 表 1/5 逐项相同；wildcard 0/10,364。 |
| AC-3（含修订 1/2） | 满足 | `build_eval_sets`/`_Admitter`/`eval_record`/`conservation_records`/泄漏断言/`load_definite_boxes`；`EvalSetTests` ×6、`MatchingTests.test_gray_diagnostic_uses_bound_s3_definite_boxes`；eval-manifest、legacy-conservation、leakage-report | 十组定义、准入 ≤4/间隔 ≥30/G5 每类 ≤12、legacy 优先内次序（min row_id）、`S→M→L→NA` 轮转、G3p/G5 封顶；609 = 601 + 8，405 条守恒 396 + 9 且 `group`/`group_v1`/`eval_row_id`/`disposition` 四字段分列；G3p/LEGACY_ONLY `gold_state=null`、保留 `definite_ids`/`legacy_probe`；泄漏两条断言真实为空；G3′ 取框绑定 `build` 输入清单 union，缺源/未登记/字节变 → `INPUT_HASH_CHANGED`。注：G1t/G2t 各 23 行共享 21 帧，提案表 D「与 G1t 同帧」是试选口径，非合同要求，只报告。 |
| AC-4（含修订 1/2） | 满足（测试薄弱，见 §4） | `prompt_v2.py`、`parse.py`、`evaluate.py`；`ParserTests`、`MatchingTests` ×2、`VerdictTests`、`PromptTests`、`CompletenessTests`、`TransferTests` | prompt 五段逐字等于表 B，G4 段在词表段后/坐标段前（修订 2），`build_prompt` 四参数无 gold 通路；`gold_text` 单一函数、退化框逐轴修正；解析闭集五值且任一错误 `status_pred=null`；≤4×≤8 穷举最大基数匹配；缺行/重复/多余 → `PREDICTIONS_INCOMPLETE`；分母不剔除；表 G 阈值 0.70/0.50/0.10/0.05/0.80/−2.0 pp；bootstrap 2000/20260912/2.5–97.5。C2-2：集合组配对差改按严格成功，另给报告率/macro F1 差——代码正确但无修前红测试；C2-3：`map_v1_output` 在真实 `predictions.jsonl`（405 行，字段 `invalid_output`/`reported_ambiguity`/`parsed.bbox_2d`/`success`/`iou`）上得 unique 404 / null 1 / ambiguous 0（与探针记录一致），夹具行不带这些字段、测试只断言非空。 |
| AC-5（含修订 1） | 满足 | `run_precheck`/`run_freeze`/`run_package`；`BlindTests`、`PrecheckTests` ×2、`FreezeTests` ×2、`PackageTests` ×3；收据与包清单（§0） | `frame_path=frames/<S1 sha>.jpg` 在 `build` 写定、盲行无 gold；`smoke.jsonl` 32 条入 manifest；预检收据绑定四份 gold SHA、`gold_text` 源码 SHA、四个 tokenizer 文件 SHA/revision/库版本/计数开关，max 89 ≤ 152；`freeze` 核抽查前提、预检成员闭集、过期、冻结闭集跟踪/干净/blob、六 jsonl = 已提交 manifest；`package` 先校验、暂存、末次重算、原子替换，不含代码/gold/legacy/泄漏报告，清单逐文件 SHA + 运输映射且不含自身。F2（上限核在替换后）非阻断。 |
| AC-6（含修订 1/2） | 满足（CLASS_3 补丁 F4/F5） | 报告 §1–§9、§11–§13；`WriteBoundaryTests` ×4；`tests.log`/`tests-baseline.log`；目录实测（§0） | 报告给出表 D/E 实取（含 E1 族闭集与逐族 E2）、守恒、泄漏/seen、序列化字节与 gold 长度（与 §8 表 6c 逐项相同）、预检摘要、执行收据、输入身份、失误画像对照（口径分列）、表 J 统计与交集表；分目录上限与 RSS 在限内；候选 diff 中实现者写入只含 A1/A2；全套摘要区分基线失败与新增失败（9 项同名同因、新增 0）。§10 计数陈旧（1195/39/build 26/6 条）与 §9 入口标签口径不一致为 CLASS_3。 |
| AC-14（含修订 1/2/3） | **不满足** | `label_audit.py`（候选）；`SamplerTests`、`ReceiptTests` ×3、`ReuseTests`；`audit-plan.json`、`panel-receipt.json`、`label-audit.md`、`UT-P1-ENG-SFT-002-label-audit`、`audit-finding-{open,closure}.json`、冻结收据 `audit` 块 | 候选代码按修订 1 归层与取样（修前红/修后绿已核）、闭合记录与 `audit_gate_state` 的绑定复核成立、#20/#21 处置按修订 3 落实。但全部抽查**证据**产自修复前的窄抽样域：按候选代码在冻结 jsonl 上重算，用户份额 3/21 张（J3 #9–#11）与合同抽样不同，评估侧 G3 行零判定；`label-audit.md` §2/§3、面板收据、判定条目、闭合记录与冻结收据 `audit` 块都绑定这份不合合同的样本 → F1（CLASS_1）。 |

C2@K4 五项与两条关注项的落点：C2-1 闭合（读码 + 红绿）；C2-2 代码闭合、测试缺口（§4）；C2-3 代码
闭合、真实 schema 核实、夹具缺口（§4）；C2-4 代码闭合（红绿）、**证据缺口 = F1**；C2-5 闭合（41 =
1197 − 1156 静态枚举一致，21 条 skip 身份见 `tests.log`）；关注项 1（#27）闭合（§0）；关注项 2（§0
口径）由 HEAD 证据补丁闭合。

## 2. 读过的文件与测试

副本内逐行通读：`tools/eng_sft/{__init__,receipts,three_state,prompt_v2,parse,evaluate,label_audit,
build_sft_data}.py`、`tools/eng_sft/adapters/{__init__,unity_s3}.py`、`tests/fixtures/eng_sft/synth.py`、
`tests/test_eng_sft_{build,evaluate,audit,parse,three_state}.py`、四份冻结 JSON、
`docs/evidence/P1-ENG-SFT-002-{data-report,label-audit}.md`、`tests.log`/`tests-baseline.log` 头尾；
提案全文（合同、8 行首次释义、6 行待裁定修订、C2 核对表、决策记录）、`docs/authorizations.md` 全部
SFT-002 条目、`docs/unity-test-log.md` `UT-P1-ENG-SFT-002-label-audit`、状态板当前节与相关 Log。主树
只读：`outputs/eng-sft/P1-ENG-SFT-002/{data/*.jsonl, data/legacy/predictions.jsonl, receipts/*.json,
upload/manifest.json 与成员抽样, panel/}`、`outputs/eng-sft/tokenizer/<revision>/`。未读
`tools/dist_data/*` 源码正文（合同声明不改，diff 证实零改动）。

## 3. Findings

### Blocking

#### F1（CLASS_1，依据 `BC-14`）— 表 J 抽查证据出自修复前的窄抽样域：按合同抽样器重算，用户份额 3/21 张不同，评估侧 G3 行零判定

- **依据条款**：`AC-14`（按表 J 分层配额与 `h(s)` 序确定性抽样）与 `AC-14 修订 1`（J1…J5 抽样域 =
  训练 distinct ∪ 441 行选层 ∪ 评估 G1/G1t/G2/G2t/G3/G3t/G5；J3 用户先含目标车、再候选数 3–4
  优先、再哈希序）；表 J「停止与回合同」（用户份额判定齐全方可冻结）与 `AC-5`（`freeze` 前提）。
  C2-4 已知缺口；用户 2026-09-15「先修代码，不重抽」（账本 2026-09-16 补录）逐字把「要不要重抽」
  交复核与接受裁定，且「不是 AC-14 豁免、抽查证据合格裁定或 K4 通过」。
- **位置**：`outputs/eng-sft/P1-ENG-SFT-002/receipts/audit-plan.json`（`plan` 20260914T183952Z，
  修复前 `_layer_of` 直接读 `noun_type`，评估行按表 C 无此字段）→ `panel-receipt.json`
  （`panels` 20260914T184014Z）→ `docs/evidence/P1-ENG-SFT-002-label-audit.md` §2（抽样域 J1 3052 /
  J2 975 / J3 360）与 §3 面板 #9–#11 → `UT-P1-ENG-SFT-002-label-audit` 行 9–11 → `audit-finding-
  closure.json`（`verdict_digest 53b7ad5f…` 绑定 21 张）→ `freeze-receipt.json` `audit` 块
  （`user_panels 21 / judged 21`）→ 包内 `manifests/freeze-receipt.json`。
- **事实（探针，零写入）**：候选代码 `label_audit.load_candidates` + `sample_panels` 在冻结的六份
  jsonl 上重算：抽样域 J1 3003 / J2 1024 / J3 420（现计划 3052 / 975 / 360，差 = G2 49 行、G3+G3t
  60 行）；用户面板 #1–#8、#12–#21 身份不变；**#9/#10/#11（J3）从训练行
  `s-5f678f71557cf12e`（the pickup truck）/`s-2afd62c0319ebf8b`（the truck）/`s-3b23afb5eb4b0d6e`
  （the pickup truck，均 2 候选）变为评估行 `G3-0116591d5f30e396`（the taxi，a4，S，3 候选）/
  `G3-49e42113164cef2f`（the bus，a4，M，3 候选）/`G3-7171c2f1cb6b531f`（the container truck，a9，
  S，3 候选，承载 2 条 legacy 行）**——修订 1 的「候选数 3–4 优先」把评估集里 10 条三候选 G3 行排在
  前面，而旧域把它们整个丢掉；预筛 #32–#41 十张也变。把 `noun_type_of` 换回「照读 `noun_type`」的
  修复前口径重算，50 张面板与现计划**逐张相同**，唯一成因就是 C2-4 缺陷，不涉及数据变化。
- **后果**：(a) 用户已判的 J3 四张里没有任何评估侧行，而评估 G3 的 48 行 gold 正是功能门 (a) 的
  分母，合同选中的三张评估面板用户从未看过；(b) 按合同定义的用户份额不是「判定齐全」，`freeze`
  前提在合同意义上应为 `AUDIT_INCOMPLETE`，冻结收据 `audit` 块与数据包（含冻结收据副本）建立在
  合同算法不会产生的样本上；(c) 已提交的 `label-audit.md` §2/§3 与候选代码不一致——在候选上重跑
  `plan` 会改写它，即证据文件与冻结代码互相矛盾。
- **分级与范围判据**：改证据数字（域大小、面板身份）与结论（AC-14 用户份额判定齐全、freeze 前提
  成立）→ CLASS_1。触发状态由 AC-14 修订 1 逐字点名，生产入口 `plan` 从已归档 jsonl 直接可达 →
  可达、有 AC 覆盖 → `BC-14`，阻断。CLASS_1 按 workflow §4.4 交接受角色复判（写提案
  「Acceptance rulings（复判）」节）；修复仍由实现角色承担。
- **闭合要求**：
  1. [实现] 在候选代码上重跑 `plan`（不计受限入口）并提交新抽样契约：`label-audit.md` §2 域
     3003/1024/420，用户 #1–#8、#12–#21 的 key/frame/surface 不变，#9–#11 = 上列三条 G3 行，
     预筛 #32–#41 按新计划；`panels` 重绘——**需要用户追加面板生成额度 +1 次**（2/2 已用尽；
     表 J (i)「规则缺陷 → 修规则、只对受影响层重新抽样再判，计一次用户复判」）。
  2. [用户] 只判定变化的 #9–#11 三张（表 J「受影响层复判」1/1 未用）；其余 18 张判定沿用，前提是
     代录条目逐行核对 key/frame_id/overlay_sha256 与原面板一致；[接受/辅助] 更新
     `UT-P1-ENG-SFT-002-label-audit` 行 9–11 与原文。
  3. [实现] `stats` → `close`（#20/#21 处置不变，闭合记录须重绑新 `verdict_digest` 与面板身份）→
     `freeze` → `package`：**2 次受限入口，现余 1/12，需要用户追加 ≥ 1 次**；预筛表按新 #32–#41
     重看（≤ 36）；报告 §8/§13 与 `label-audit.md` 同步。**不重跑 `build`**（六份 jsonl、四份冻结
     JSON、预检收据不变），不改已判 18 张，不改 #20/#21 处置。
  4. 机械断言：代码侧 `SamplerTests.test_layer_quotas_and_uniqueness_are_deterministic` 已修前红/
     修后绿（本轮核实）；证据侧 `NOT_MECHANIZABLE` → `R2@K4` 定点复看：在冻结 jsonl 上重算
     `sample_panels` 与新 `audit-plan.json` 逐张相等、面板收据 overlay SHA、Unity 日志行 9–11、
     闭合记录摘要、冻结收据 `audit` 块、包内收据副本。
  5. 若用户不追加额度：接受角色须在复判节逐字裁定并回用户；本角色不会在现样本上把 AC-14 记为
     满足，也不签发本停点通过。

### Non-blocking

#### F2（SCOPE_GAP）— `run_package` 在原子替换之后才核 `upload/` ≤ 0.3 GB，超限时新包已发布、旧包收据残留

- **依据条款**：`AC-6`（`upload/` ≤ 0.3 GB）与合同 §3「失败只写失败收据、不发布该次工件」。
- **位置**：`tools/eng_sft/build_sft_data.py` `run_package`：先 `shutil.rmtree(upload_dir)` +
  `staging.rename(upload_dir)`，随后才 `_dir_bytes(upload_dir) > UPLOAD_DIR_MAX_BYTES` →
  `PackageIncomplete`；此时新包已替换旧包，上一轮 `package-receipt.json` 仍指向旧清单 SHA。
- **范围判据**：冻结输入下包为 121,013,624 B、帧并集 189.7 MB，无法从已归档工件触发 → 不可达 →
  `SCOPE_GAP`，路由接受角色记债或纳入范围（修法：在 `staging` 上计量，超限即删暂存、不替换）。

#### F3（SCOPE_GAP）— 探针 `predictions.jsonl` 缺失时 `build` 照常成功

- **依据条款**：`AC-1`（只读 §3 输入闭集，任一不符即 fail-closed）；§3 输入表把
  `predictions.jsonl` 列为输入（legacy 守恒与 v1 诊断附表来源）。
- **位置**：`build_sft_data.Archives.load`：`if probe_predictions.is_file():` 才登记与复制，
  缺失时 `legacy_predictions_sha256=""`，无失败收据；K3 的 v1 诊断附表将静默为空。
- **范围判据**：真实 T7 布局含该文件（SHA `25702e85…` 已登记），触发需另一种挂载状态 → 不可达 →
  `SCOPE_GAP`，路由接受角色。

#### F4（CLASS_3）— 报告 §10 测试计数陈旧（与 §13、`tests.log` 不一致）

- 依据条款 `AC-6`；不驱动任何工具或操作员动作。`docs/evidence/P1-ENG-SFT-002-data-report.md`
  §10 逐字替换补丁（由实现角色在下一次提交应用）：
  - `- 本批次（C1@K4 返工后）：**Ran 1195 tests，errors=9，skipped=21**。` →
    `- 本批次（C2@K4 返工后）：**Ran 1197 tests，errors=9，skipped=21**。`
  - `- 本批次新增 39 条用例（1195 − 1156）= \`tests/test_eng_sft_{build 26, evaluate 6, audit 5,` →
    `- 本批次新增 41 条用例（1197 − 1156）= \`tests/test_eng_sft_{build 28, evaluate 6, audit 5,`
  - `  three_state 1, parse 1}\`，全部通过、零 skip。AC 点名的 33 条具名回归全部到位，另有 6 条边界用例` →
    `  three_state 1, parse 1}\`，全部通过、零 skip。AC 点名的 33 条具名回归全部到位，另有 8 条边界用例`
  - `  （通配帧零样本、预检溢出、预筛披露、闭合记录放行、晚期失败零发布、打包入口守边界）。` →
    `  （通配帧零样本、预检溢出、预筛披露、闭合记录放行、晚期失败零发布、打包入口守边界、分片实数行数与 S0 常量、打包失败不毁旧包）。`

#### F5（CLASS_3）— 报告 §9 执行收据表的入口标签口径不一

- 依据条款 `AC-6 修订 2`。§9 表里 `precheck（1/3、2/3）` 用旧信封分母，`freeze（入口 1/2）`、
  `package（入口 1/2、2/2）` 是阶段内序号，后半段 `入口 7/12…11/12` 是累计计次；§0 已给出权威累计
  11/12、2/5。逐字**追加**补丁（在 §9 表格后、「峰值 RSS」段前插入一行，不改表内数字）：
  `表中 \`precheck（1/3、2/3）\` 为旧信封分母（追加后为 2/5）；\`freeze（入口 1/2、2/2）\` 与 \`package（入口 1/2、2/2）\` 是各阶段内的序号（按收据时间即累计第 3、4、5、6 次），\`入口 7/12…11/12\` 为累计计次；累计口径以 §0 为准。`

## 4. 缺失或薄弱的测试（非阻断记录，测试改动不触及冻结闭集）

1. C2-2：`VerdictTests.test_layer_statuses_on_fixture_predictions` 在修复前源码上仍通过；应加
   夹具使 G3 严格成功在两次预测间不同，断言 `paired_difference_by_group["G3"]["point_estimate_pp"]
   ≠ 0`、`outcome == "strict_success"` 且 `report_rate_diff`/`macro_f1_diff` 存在。
2. C2-3：夹具 `synth._probe` 的 `predictions.jsonl` 行只有 `row_id`/`raw_output`，`map_v1_output`
   在夹具上全部落 `none`；应让夹具行携带 `invalid_output`/`reported_ambiguity`/`parsed.bbox_2d`/
   `success`/`iou` 并断言 `status_v1` 分布与 `status_agrees_with_v1`。
3. C2-1（build 侧）：`replaced` 备份/还原路径（第二次 `build` 晚期失败时旧字节逐份还原）无回归；
   `test_late_binding_failure_publishes_nothing` 在全新根上运行，不覆盖覆盖-还原分支。
4. K3 提示（不属本停点）：本地预检用 `tokenizers.Tokenizer.from_file`，云端按表 H 用
   `transformers.AutoTokenizer`；两者对同一 `tokenizer.json` 的切分一致性由 K3 的
   `TOKENIZER_MISMATCH` 兜底，K4 不主张。

## 5. 交回实现角色的动作

1. F1（CLASS_1）：先交接受角色复判并向用户申请追加额度（面板生成 +1；受限入口 +≥ 1，建议 +2 留
   失败余地；复判 1/1 沿用）；裁定与额度落账后按 F1 闭合要求 1–3 执行；R2 定点复看第 4 条。
2. F2/F3：接受角色记债（`docs/implementation-status.md`「范围外已知缺陷」`OPEN`）或纳入范围；
   纳入则各绑一条修前红回归（`upload.staging` 超限不替换旧包；缺 `predictions.jsonl` 写
   `LEGACY_SOURCE_MISMATCH` 失败收据）。
3. F4/F5：在下一次提交逐字应用到报告（实现角色持有 A1 报告写权限）。
4. §4 第 1–3 条测试补强只改 `tests/`，不触及冻结闭集，可随返工提交。
5. 只允许触及表「写入分层」A1/A2；**不重跑 `build`、不重跑 `precheck`、不改六份 jsonl 与四份
   冻结 JSON、不改已判 18 张与 #20/#21 处置**；Unity 日志由接受/辅助角色代录。修后按 workflow
   §4.3.1 自证，直接交 `R2@K4`，不经核对轮；本停点第 2 次 `REWORK_REQUIRED` 后未闭集冻结、
   轮 3 终局。

## `UNITY_NA` 附议

**分类附议**（仅限本 work ID 的 `K4` 候选）：全量 diff 证实 `controller/`、`Assets/`、`config/`、
`ProjectSettings/`、`Packages/` 零字节改动；`tools/eng_sft/` 不 import 运行时模块、只读已归档
attempt-2 工件与 T7 探针、写出闭集保护 `runtime/*` 原件；零 Play/scenario/session/run/attempt 身份，
不改变任何运行时行为；表 J 用户看图是 `OFFLINE_VISUAL_CHECK`，不是 Unity 验证。`UNITY_NA` 分类对
本候选**成立**；正式附议绑定到本停点的通过轮 `passed_candidate`，本轮为 `REWORK_REQUIRED`，不产生
`passed_candidate`，也不构成 `DONE`。

## 6. 再复核结果

待 `R2@K4`：定点复看 F1 闭合要求第 4 条（重算 `sample_panels` 与新计划逐张相等、面板收据、Unity
日志行 9–11、闭合记录、冻结收据 `audit` 块、包内副本）；核实 F4/F5 补丁已应用、F2/F3 的接受角色
裁定；新阻断只来自修复触及行（相对本轮 `round_candidate`）上的 CLASS_1/2、旧 finding 闭合失败与
`RED_LINE`。本会话未修改任何实现文件（`controller/`、`Assets/`、`tools/`、`tests/`、`config/`
零改动；探针零写入）。

### 7. 边界自查（R1@K4 收工）

- 本会话只写入 `docs/reviews/P1-ENG-SFT-002.md`（新建）与 `docs/current-status.md`（锚点增量合并：
  Current state 一句、Gate board 本项行、Active handoffs 本项行、Immediate next actions 首段、
  Log 新条目）；`controller/`、`Assets/`、`tools/`、`tests/`、`config/`、`docs/evidence/`、
  `docs/proposals/`、`docs/authorizations.md` 零写入；两个一次性副本（候选副本与 `32233f9` 红绿副本）
  均已 `git worktree remove --force`。
- `python3 tools/check_docs.py` 通过。`python3 tools/check_role_writes.py --role review` 报出
  `docs/proposals/P1-ENG-SFT-002-lora-training-and-cloud-execution.md` 一条：该文件的未提交改动
  （+15 行「2026-09-16 接受侧交接核实与 C2-4 用户决定补录」决策记录）连同 `docs/authorizations.md`
  的 +16 行补录条目与状态板的接受侧文字，在本会话开工前已存在于主树（开工时 `git status` 即为
  这三个文件 M），属接受角色 2026-09-16 未提交批次，本会话未触碰、未恢复——恢复会抹掉他角色
  未沉淀的授权补录与决策记录（AGENTS.md「保留其他角色的新条目」）。该越权提示不是本角色写入，
  如实记于此；提交时请由接受角色（或用户）先提交其三文件批次，再提交本复核批次。

## R2@K4 — 2026-09-18

Reviewer/role: 复核角色 / independent verification（新鲜上下文会话，Fable 池 `/review`；档位不低于实现者）
Workflow: engineering-v1（同 R1；按 `docs/engineering-workflow.md` §5/§6 与 `docs/roles/review.md`「工程轨道」节执行；
依据列仍取 workflow §4.4 六值闭集，`BC-n` 读作任务合同 `AC-n`）
Round: R2@K4
Date: 2026-09-18
Implementation snapshot: 状态板 Active handoffs 本项行（`AWAITING_R2_AT_K4`）把候选指向提交主题
「P1-ENG-SFT-002 R1@K4 返工交接：F1 闭合链完成，候选交 R2@K4」（`git log --grep` 运行时解析 = `7650c82…`，
2026-09-17 00:04:55 −0400），开工时主树 HEAD 即该提交；主树另有构思角色 2026-09-17 未提交的状态板改动
（「本轮不开新项」Log 条目与下一动作一段），本会话未触碰。修复触及行基线 = R1 `round_candidate`
（`d17d81f…`）。本 work ID 仍无上一通过候选，全量 diff 基线沿 R1（`4306485…`）：35 个文件 +17,233/−24。
round_candidate: 7650c82be20591d6b6739ccc16d3318f5fdbd76d
Verdict: PASS_WITH_NOTES
passed_candidate: 7650c82be20591d6b6739ccc16d3318f5fdbd76d

### 0. 候选、修复触及行与方法

- **修复触及行**（COORD-009 (b)）：`git diff d17d81f..7650c82` 共 14 个文件 +1,030/−110。PLAY_GOVERNING
  部分 5 个文件 +334/−12：`tools/eng_sft/label_audit.py`（+88/−12：新增 `user_share_digest`、
  `_record_open_finding`；`audit_gate_state` 在绑定复核之后、未裁定检查之前新增「闭合记录的
  `user_share_digest` ≠ 当前计划 → `AUDIT_FINDING_OPEN`」；`run_close` 记录 `user_share_digest`；
  `run_stats` 改经 `_record_open_finding` 写开放收据并在 run 收据记 `finding_receipt`）、
  `tests/test_eng_sft_audit.py`（+95：`_open_and_close` 夹具与两条加固回归）、`tests/test_eng_sft_build.py`
  （+40：C2-1 构建侧还原回归）、`tests/test_eng_sft_evaluate.py`（+77：C2-2 严格成功配对差、新类
  `V1DiagnosticTests`）、`tests/fixtures/eng_sft/synth.py`（+46：`v1_prediction`/`v1_expected_status`，探针
  预测行改带真实 v1 字段）。`tools/eng_sft/` 其余 9 个文件、`tools/eng_sft/adapters/`、`tools/dist_data/`、
  `tools/eng_asset/` 与三个 Play 治理门文件零改动；`controller/`、`Assets/`、`config/`、`ProjectSettings/`、
  `Packages/` 相对 `4306485` 仍零字节改动。其余 9 个为文档：授权账本（+38，接受角色两条补录）、状态板、
  数据报告（§0/§8/§9/§10/§13 与新 §15）、抽查文件（新计划）、`tests.log`、账本 F2/F3 两行、提案（+68，
  接受角色复判节与授权指针）、Unity 日志（+74，辅助角色代录）、本复核文件（R1 落盘）。
- **开轮资格（workflow §4.4）**：相对上一通过候选（无，取 `4306485`）的 diff 在 PLAY_GOVERNING 上非空
  → 开轮；本轮为增量轮，新阻断只来自修复触及行上的 CLASS_1/2、旧 finding 闭合失败、`RED_LINE`。
  Active handoffs 无 `Consuming=yes` 行；本 work ID 从未写过 `blocks_consuming_gate`，无 release 义务。
- **停点自证核实（workflow §4.3.1 四项）**：(1) 冻结闭集 8/8 与六份 jsonl、预检收据同上一冻结收据逐项
  相同（§1 第 7 条）、抽样契约先提交后绘图（§1 第 2 条）；(2) focused 46/46、停点全套 `Ran 1202 …
  errors=9, skipped=21`，9 项 ERROR 与基线日志逐名相同（`diff` 两侧排序后的 `ERROR:` 行为空）、新增失败 0；
  (3) 零 Unity Play/ID，申请 `UNITY_NA`；(4) 交接行、候选、报告 §15 与限制已写。四项成立，不给
  `REVIEW_BLOCKED`。
- **副本与只读边界**：`git worktree add --detach .claude/worktrees/review-P1-ENG-SFT-002 7650c82`；读码、重跑、
  探针全在副本。红绿在第二个一次性副本 `review-P1-ENG-SFT-002-red`（`d17d81f` 源码 + 候选 `tests/`；随后
  `git checkout 32233f9 -- tools/`）完成。主树 `outputs/eng-sft/P1-ENG-SFT-002/{data,receipts,panel,upload}`
  与 `outputs/eng-sft/tokenizer/` 只按绝对路径**只读**；未运行 `build`/`precheck`/`freeze`/`package`/
  `plan`/`panels`/`prescreen`/`stats`/`close`（受限计次不变：入口 13/14、precheck 2/5、面板 3/3）。探针：
  候选代码 `label_audit.load_candidates` + `sample_panels` 在内存重算（读六份 jsonl，零写入、零收据）；
  `draw_panel` 用 `.venv-yoloe`（Pillow 12.3.0）把 7 张面板重绘到会话 scratchpad 后即删，未写 `panel/`。
  两个副本收工均 `git worktree remove --force`。
- **重跑（不信报告数字）**：副本内系统 `python3`（3.14.6）`python3 -m unittest tests.test_eng_sft_build
  tests.test_eng_sft_evaluate tests.test_eng_sft_audit tests.test_eng_sft_three_state tests.test_eng_sft_parse`
  → `Ran 46 tests in 8.710s … OK`（0 skip；输出写 scratchpad `review-r2-focused.log`，只回显摘要）。静态枚举
  `def test_`：build 29 / evaluate 8 / audit 7 / three_state 1 / parse 1 = 46 = 1202 − 1156。测试树哈希
  `HEAD:tests` = `4947a0801164d0f96f27a1626f7492721390fd88`，`HEAD:tools/eng_sft` =
  `c0399112762aa9ad4923f7b5dd6ceb7774c38eba`。
- **修复前红 / 修后绿（新增 5 条，均为修复触及行上的具名回归）**：`d17d81f` 源码 + 候选测试：
  `ReceiptTests.test_replanned_user_share_invalidates_closure` **FAIL**（`None != 'AUDIT_FINDING_OPEN'`：旧
  代码在计划重抽后仍放行）；`ReceiptTests.test_rerun_stats_keeps_original_open_receipt` **FAIL**（原开放收据
  字节被改写）。`32233f9`（C2 修复前）源码 + 候选测试：`VerdictTests.test_set_group_paired_difference_
  uses_strict_success` **ERROR**（`KeyError: 'outcome'`）、`V1DiagnosticTests.test_v1_outputs_map_to_three_
  states_and_pair_with_current_run` **ERROR**（`KeyError: 'v1_prediction_present'`）、`ReconciliationTests.
  test_second_build_publish_failure_restores_replaced_files` **FAIL**（旧字节未还原）。五条在候选上全部通过
  （含于 focused 46）。与报告 §15 的红色断言逐条相同。
- **红线检查**：`tools/eng_sft/` 仍不 import `controller.*`（`test_no_controller_imports` 在 focused 内通过）；
  返工只读冻结 jsonl、原帧与 Unity 日志，写出仍在 `outputs/eng-sft/…` 与 A2 证据文档；不读真值文件；
  无 `RED_LINE`。

### 1. F1 闭合要求 4 定点复看（`NOT_MECHANIZABLE` 证据链，逐项独立核实）

| # | 复看项 | 独立核实结果 |
|---|---|---|
| 1 | 冻结 jsonl 上重算 `sample_panels` 与 `receipts/audit-plan.json` 逐张相等 | 候选代码在主树六份 jsonl 上重算：抽样域 J1 3003 / J2 1024 / J3 420 / J4 690 / J5 584 / J6 86 / J7 341 = 计划 `domain_by_layer`；50/50 面板在 layer/share/source/key/frame_id/surface/object_ids 上逐张相同；用户 21 / 预筛 29。新 #9–#11 = `G3-0116591d5f30e396`（the taxi，S，3 候选）/ `G3-49e42113164cef2f`（the bus，M，3 候选）/ `G3-7171c2f1cb6b531f`（the container truck，S，3 候选，承载 2 条 legacy 行），三行在 `eval.jsonl` 中 `group=G3`、`gold_state=ambiguous`、`definite_ids` 与面板 object_ids 逐一相同；评估 G3 共 48 行（两候选 41、三候选 7）。与 R1 F1 枚举一致。 |
| 2 | 抽样契约先提交后绘图；面板收据与叠加图 | `panel/panel-receipt.json`（utc `20260917T032157Z`）`head` = `f88b65b…`（提交主题「R1@K4 返工：F1 新抽样契约（plan）与实现侧开工声明」，2026-09-16 23:21:51 −0400）；其 `audit_document_sha256` `1445732d…` = `git show f88b65b:docs/evidence/P1-ENG-SFT-002-label-audit.md` 的 sha256。50 张 `panel-NN.jpg` 现算 sha256 = 计划 `overlay_sha256` = 收据 `overlay_sha256`；50 张 `-original.jpg` = 收据 `original_copy_sha256`；收据 key/frame_id/surface/layer/share 与计划逐张相同。候选提交的抽查文件 sha256 `839a519d…` = `stats` run 收据（`20260917T040100Z`）记录的输出 SHA。 |
| 3 | 叠加图可复现 | 用候选 `draw_panel` 与 `.venv-yoloe`（Pillow 12.3.0）在 scratchpad 重绘 #1/#9/#10/#11/#20/#32/#41：7/7 sha256 等于收据 `overlay_sha256`；各原帧现算 sha256 = 收据 `source_sha256`。 |
| 4 | 与 `panel/history-r1k4-20260916/` 旧收据比对 | 旧收据（utc `20260914T184014Z`）与新收据逐张比对 key/frame_id/surface/layer/share/overlay：**37 张全同，变化恰为 #9–#11 与 #32–#41**；历史目录 50 张旧叠加图 sha256 = 旧收据 50/50；37 张未变面板与现行文件**字节全同**（含全部 18 张沿用判定的用户面板）。旧 #9–#11 key `s-5f678f71557cf12e`/`s-2afd62c0319ebf8b`/`s-3b23afb5eb4b0d6e`、旧叠加图前缀 `c12342b8`/`dd6da7a5`/`62a18ac4` 与 Unity 日志历史小节所载相同；旧计划域 3052/975/360 即 R1 F1 所指。 |
| 5 | Unity 日志同名条目 #9–#11 与历史小节 | 候选 `docs/unity-test-log.md` 经 `read_unity_verdicts`：21/21、`state=COMPLETE`、`wrong=[20, 21]`、`verdict_digest` `53b7ad5f…`（判定取值与 R1 时相同，故摘要不变——这正是加固 ① 要补的缝）。#9–#11 三轮 AskUserQuestion 原文（#9 固定选项、#10/#11 Other 自由文本、截断追问、「都记对，截断作备注（推荐）」）由辅助角色代录（提交 `a45e50b`），「缆车」原词保留；`## UT-P1-ENG-SFT-002-label-audit-history-2026-09-14` 位于下一 `## ` 标题之后、无 6 列表，`_entry_body` 不会读入。 |
| 6 | `receipts/audit-finding-closure.json` | utc `20260917T040106Z`；`disposition=ii`、锚点「AC-14 修订 3」、`ruling.commit` = `418a94e…`（写闭合时提案最近提交 = 接受复判提交）；`finding_receipt_sha256` `283d6ab9…` = 现 `audit-finding-open.json`（utc `20260915T025843Z`，panels [20, 21]）现算 sha256，且与历史副本**字节相同**（`stats` run 收据 `finding_receipt: preserved`）；`verdict_digest` `53b7ad5f…`；**新增 `user_share_digest` `18b484b7…` = 候选 `user_share_digest(plan)` 现算**；panels 20/21 的叠框对象/框/S5 颜色/counterexample/overlay 与计划相同。旧闭合（历史副本，utc `20260915T025856Z`，`ruling.commit` `e4965b2…`）无该字段，故 `stats` 于 `20260917T040100Z` 记 `AUDIT_FINDING_OPEN`（新检查在生产路径上实际触发），随后 `close` 重绑。 |
| 7 | `receipts/freeze-receipt.json` `audit` 块与包内副本 | utc `20260917T040114Z`、`head` `a45e50b…`（辅助代录提交，已含 `416b679` 的代码修复；`git diff a45e50b..7650c82` 只有状态板、报告、抽查文件、`tests.log`）；`frozen_set` 8/8 的 sha256 与 `git_blob` = 候选 `git rev-parse HEAD:<path>`/现算，且与上一冻结收据逐项相同；六份 jsonl 磁盘 sha256/字节 = 收据 = 上一收据；`precheck_receipt_sha256` `d552c351…` 不变；`audit` 块：`user_panels 21 / judged 21 / COMPLETE / wrong [20, 21] / uncertain []`、`closure` 指向新闭合、`verdict_digest` 与 `user_share_digest` 同第 6 条。`upload/manifests/freeze-receipt.json` 与本地收据**字节相同**；`dataset-manifest`/`eval-manifest`/`precheck-receipt` 副本与来源字节相同。 |
| 8 | 数据包 | `upload/manifest.json` sha256 `264839e5…` = `package-receipt.json`（utc `20260917T040132Z`）；成员 2,335 = 磁盘文件数（不含清单）；与历史 `upload-manifest.json` 比对**只有 `manifests/freeze-receipt.json` 一条不同**，`frame_transport_map`/`source_frame_ids` 逐项相同，`total_bytes` 119,952,164（旧 119,952,071，差 = 收据副本增长）；8 个非帧成员 sha256 现算相符；随机 40 张帧 `sha256 == 文件名 == 清单`；`contains_code=false`；`upload/` 121,013,717 B ≤ 0.3 GB。 |
| 9 | 受限入口计次（按收据文件数） | `run-build` 3 + `run-freeze` 4 + `failure-freeze` 1 + `run-package` 5 = **13 ≤ 14**；`run-precheck` 2 ≤ 5；`run-audit` 中 `stage_detail=panels` 3（`20260914T183502Z`、`20260914T184014Z`、`20260917T032157Z`）≤ 3；`prescreen` 2 次各 29 行（累计看图 29 + 变化 10 = 39 ≤ 39，每份计划 29 ≤ 36）；`stats` 3、`close` 2；用户唯一图 21 + 3 = 24 ≤ 24，复判 1/1；代录 2（`330cbf9`、`a45e50b`）≤ 2。与报告 §0/§15 及交接行一致。 |
| 10 | 目录上限（AC-6） | `data/` 6,635,477 B、`upload/` 121,013,717 B、`panel/` 13,989,924 B（现行 7,033,402 + 历史副本 6,956,522）≤ 20 MB、`tokenizer/` 11,491,943 B；run 收据峰值 RSS ≤ 128,745,472 B、单次 ≤ 1.6 s。 |
| 11 | 返工前证据保留（复判第 1 条） | `receipts/history-r1k4-20260916/index.json` 列 109 份（面板 100 + 面板收据 + 旧计划/开放/闭合/冻结/打包收据、`input-manifest`、上传清单、`label-audit-at-d17d81f.md`），逐份 sha256 现算 **109/109 相符**，记有 `old_candidate_commit_subject` = R1 候选主题。 |
| 12 | F4/F5 已应用 | 报告 §10「本批次（C2@K4 返工后）：**Ran 1197 tests…**」「新增 41 条用例（1197 − 1156）= …build 28…」「另有 8 条边界用例（…分片实数行数与 S0 常量、打包失败不毁旧包）」与 §9 表后追加行「表中 `precheck（1/3、2/3）` 为旧信封分母…累计口径以 §0 为准。」均逐字到位；§10 新增本停点段（Ran 1202 / 46 条）与 `tests.log` 一致。 |
| 13 | F2/F3 记债 | `docs/implementation-status.md` 范围外已知缺陷账本两行 `SCOPE_GAP` / `OPEN`（2026-09-16，接受角色）；提案复判节 F2/F3 行保留非阻断；本轮不修、代码未变（`build_sft_data.py` 相对 R1 零改动）。 |

**结论：F1 闭合。** 合同抽样器在冻结输入上产生的用户份额已被用户判定（新 3 张复判、18 张沿用且面板字节
全同），闭合记录、冻结收据与包按新计划重绑，AC-14 与 AC-5 的冻结前提在合同意义上成立。

### 2. 逐条 AC 核对（本轮更新；未列者沿 R1 §1 结论不变）

| 编号 | 结论 | 本轮证据与理由 |
|---|---|---|
| AC-1 / AC-2 / AC-3 / AC-5 | 满足 | `build`/`precheck` 未重跑；冻结闭集 8/8、六份 jsonl、预检收据与 R1 核实的同一批字节逐项相同（§1 第 7 条）；`freeze`/`package` 同链重出且只变冻结收据副本（§1 第 8 条）。 |
| AC-4 | 满足（R1 §4 第 1/2 条测试缺口已闭） | `evaluate.py`/`parse.py`/`prompt_v2.py` 字节未变；新增 `test_set_group_paired_difference_uses_strict_success`（G3 四行两行答 unique → −50 pp、`outcome=strict_success`、报告率与 macro F1 配对差存在、反向 +50 pp）与 `test_v1_outputs_map_to_three_states_and_pair_with_current_run`（夹具行带真实 v1 字段、四态轮转、重复键两条各自成行），修前 ERROR / 修后绿。 |
| AC-6 | 满足 | F4/F5 已应用；报告 §15 逐条回证与本轮独立核实相符；分目录上限在内（§1 第 10 条）；候选 diff 实现者写入只含 A1/A2；全套摘要区分基线失败与新增失败（新增 0）。 |
| AC-14（含修订 1/2/3） | **满足** | 抽样器确定性与配额（R1 已红绿）；本轮在冻结 jsonl 上重算与计划逐张相同（§1 第 1 条）；用户份额 21 ≤ 24、累计唯一用户图 24 ≤ 24、预筛 29 ≤ 36；面板收据记 HEAD/样本身份/原图 SHA/叠加图 SHA；用户判定由辅助角色代录、抽查文件只存统计与预筛表；#20/#21「错」→ `AUDIT_FINDING_OPEN` → (ii) 具名裁定 → 闭合记录重绑新用户份额；预筛披露不计核验。 |

### 3. Findings

**阻断：无。** 修复触及行（§0）逐行通读，未发现 CLASS_1/2；旧 finding F1 闭合成立（§1）、F4/F5 已应用、
F2/F3 按接受复判非阻断记债；无 `RED_LINE`。本轮不新开 finding 编号。

### 4. 非阻断注记（不是 finding，不带依据列；供接受角色与后续设计参考）

1. **`panel/` 上限被历史副本占用**：AC-6 的 `panel/` ≤ 20 MB 现含 6,956,522 B 的 `history-r1k4-20260916/`
   （13,989,924 B 合计）。若再出现一次需备份面板的返工，同目录再加一份副本会超限而被 `run_panels` 拒绝；
   届时备份应落在 `panel/` 之外或经用户同意清理，本轮无动作。
2. **加固 ① 的回归以手改计划 JSON 模拟重抽**：`test_replanned_user_share_invalidates_closure` 的初始状态由生产路径
   产出（`plan`→`panels`→判定→`stats`→`close`），随后直接改写 `audit-plan.json` 的 key/frame_id 与 `overlay_sha256`
   来模拟重抽/重绘。断言覆盖的正是 `audit_gate_state` 比较的字段，本轮接受；更贴生产的写法是让 `run_plan`
   在变化后的候选集上重跑。该测试不是 F1 的闭合绑定测试（F1 绑定的是 `SamplerTests…deterministic` + 本轮定点复看）。
3. **`_record_open_finding` 的 superseded 归档名取自旧收据 `utc`**：若旧收据缺 `utc` 且同一秒内两次 supersession，
   第二次会静默覆盖第一次归档。收据由同一 writer 写出、`utc` 恒在，从已归档工件不可达，本轮只记录不立 finding。
4. **已披露限制沿用（报告 §15）**：(a) 2026-09-14 首份开放收据字节已被旧实现改写、不可恢复，现存 09-15 版为新旧
   闭合共同绑定的那份；(b) 判定表行仍只按 `panel_index` 记值（代录格式 v1），加固 ① 只在存在闭合记录时生效，
   「新判定对应新图」靠代录逐行核对与本轮定点复看（R1 `NOT_MECHANIZABLE`）——建议接受角色把「判定行绑定面板身份」
   记为代录格式 v2 的设计输入；(c) 截断门槛（S3 可见 ≥ 25% 才算候选，宽于 VisDrone / KITTI Hard 的 50%；
   #10 有 25.7% 的公交车）是后续设计输入，用户已选「都记对，截断作备注」，本轮合同不改；(d) 首轮预筛 #33 颜色疑点、
   #20/#21「颜色错」及其具名处置不变。

### 5. 交回接受角色的动作

1. 按 workflow §4.6 与 engineering §11 消费本轮 `PASS_WITH_NOTES` 与下方 `UNITY_NA` 正式附议：汇总实现者证据
   （报告 §15、`tests.log`）、本轮独立复核与 `UNITY_NA` 附议，裁定 K4 候选 1 的门状态并改写 Gate board Overall
   （本角色未改 Overall token）；返工归因从依据列机械派生（本轮无新 finding）。
2. 记录 §4 第 4 (b)(c) 两条设计输入（判定行绑定面板身份；截断门槛），不改本合同、不新增 AC。
3. F2/F3 保持账本 `OPEN`；本 work ID 无 `blocks_consuming_gate` 行，无 release 动作。
4. K3（候选 2）仍未授权：任何 GPU 行动以 K4 最终通过轮消费 + `UNITY_NA` 附议 + 用户候选 2 执行信封为前提
   （提案 §7）；AC-12 前置在候选 2 授权当日一次性判定。
5. 计数：K4 C/R = 2/2；本停点 `REWORK_REQUIRED` 共 1 次（上限 2），未闭集未冻结；本轮为通过轮。
6. 提交：本复核批次（本文件 R2 块 + 状态板锚点增量）留在主树**未提交**，由接受角色或用户提交（状态板另含构思角色
   2026-09-17 未提交条目，非本角色写入，本会话未触碰）。

## `UNITY_NA` 正式附议（R2@K4，候选 1）

**正式附议成立**，绑定本轮 `passed_candidate`（`7650c82…`）：全量 diff 相对 `4306485` 证实 `controller/`、`Assets/`、
`config/`、`ProjectSettings/`、`Packages/` 零字节改动；`tools/eng_sft/` 不 import 运行时模块、只读已归档 attempt-2
工件、T7 探针与原帧、写出闭集保护 `runtime/*` 原件；零 Play/scenario/session/run/attempt 身份，不改变任何运行时行为；
表 J 用户看图（含 2026-09-16 复判 3 张）是 `OFFLINE_VISUAL_CHECK`，不是 Unity 验证。附议范围只限本 work ID 的
K4 候选 1；候选 2（K3）须另行申请与附议。附议不等于 `DONE`：`DONE` 仍由接受角色在三证据齐全后关闭。

### 6. 边界自查（R2@K4 收工）

- 本会话只写入 `docs/reviews/P1-ENG-SFT-002.md`（追加本 R2 块与抬头一行「Latest round」指针，R1 原文未删改）
  与 `docs/current-status.md`（锚点增量合并：Current state 两句、Gate board 本项行、Active handoffs 本项行、
  Immediate next actions 首段、Log 新条目、Last updated）；`controller/`、`Assets/`、`tools/`、`tests/`、`config/`、
  `docs/evidence/`、`docs/proposals/`、`docs/authorizations.md`、`docs/unity-test-log.md`、`docs/implementation-status.md`
  零写入；`outputs/` 零写入（探针在内存与 scratchpad）。
- 两个一次性副本（`review-P1-ENG-SFT-002` 候选副本、`review-P1-ENG-SFT-002-red` 红绿副本）均已
  `git worktree remove --force`。
- 自检结果（收工时实跑）：`python3 tools/check_role_writes.py --role review` → 「角色 'review' 写入范围检查通过（检查对象：
  未提交改动，共 2 个路径）」，exit 0；`python3 tools/check_docs.py` → 「docs 合规检查通过：分节上限、执行轨道纪律、Gate-echo、
  复核文件、消耗性门 blocks、DONE 行双证据、commit 引用、Last updated、hooksPath 均符合要求」，exit 0；`git status --porcelain` 只有
  `docs/current-status.md` 与 `docs/reviews/P1-ENG-SFT-002.md` 两个路径，`git worktree list` 已无本角色副本。未报出任何越权路径，
  无需恢复。**本会话未修改任何实现文件。**

## R1@K3 — 2026-09-18

Reviewer/role: 复核角色 / independent verification（新鲜上下文会话，Fable 池 `/review`；档位不低于实现者）
Workflow: engineering-v1（同 R1@K4；按 `docs/engineering-workflow.md` §5/§6 与 `docs/roles/review.md`「工程轨道」节执行；
依据列仍取 workflow §4.4 六值闭集，`BC-n` 读作任务合同 `AC-n`）
Round: R1@K3（本停点第 1 轮；K3 = 候选 2，合同 §7「AC-7…13」+ 首次接受释义 AC-7 修订 1 / AC-12 修订 1 +
待裁定节 AC-10 修订 1…3、AC-13 修订 1、AC-7 修订 2 及「执行前修正与验证边界」K3-P1…3）
Date: 2026-09-18
Implementation snapshot: 状态板 Active handoffs 本项行（`AWAITING_R1_AT_K3`，接受角色 C2@K3 交接；该交接及其提案核对表、
`implementation-status.md` 覆盖段在本会话开工时是主树**未提交**改动，本会话未触碰）把候选指向「当前 HEAD」，提交主题
「P1-ENG-SFT-002 C1@K3 退回项修正：续跑/A→B 包身份、选优收据绑定、自检数值边界与执行披露，交 C2@K3」（运行时解析 =
`461f288…`，2026-09-18）。上一通过候选由本文件 R2@K4 `passed_candidate` 派生（`7650c82…`）；全量 diff 相对它 18 个文件
+30,517/−131：A1 新增 `tools/eng_sft/{cloud_runner 1799, train_lora 940, verify_return 550}.py`、`tools/requirements-eng-sft.txt`
14、`tests/test_eng_sft_{cloud 914, train 302}.py`；A2 新增三份摘要（zero-shot 293,714 B / train 16,416 B / eval 373,862 B）、
K3 报告 642 行、`tests.log` 改写；其余 9 份为他角色文档（授权账本 +136、Unity 日志 +107、implementation-status +74、正式设计、
提案、状态板、本复核文件 R2 落盘）。`controller/`、`Assets/`、`config/`、`ProjectSettings/`、`Packages/`、`tools/dist_data/`、
`tools/eng_asset/`、K4 冻结闭集 8 文件零字节改动。本轮为 K3 停点第 1 轮：阻断范围 = 全量 diff 上的 CLASS_1/2 与 `RED_LINE`
（无「修复触及行」基线）；C1@K3 退回修正提交（`7eefb8e..461f288`，代码侧 `cloud_runner.py` +77、`verify_return.py` +8、
`test_eng_sft_cloud.py` +88）另按接受侧关注项①做红绿定点核实。
round_candidate: 461f288d5120c47088ac17cfbbfd011423d96562
Verdict: PASS_WITH_NOTES
passed_candidate: 461f288d5120c47088ac17cfbbfd011423d96562

### 0. 复核范围、停点自证核实与方法

- **开轮资格（workflow §4.4）**：`git diff 7650c82..461f288` 在 PLAY_GOVERNING 集合上非空（`tools/` 4 文件、`tests/` 2 文件，
  全部新增）→ 开轮。未触及 Play 治理门文件，无闭环轮义务。Active handoffs 无 `Consuming=yes` 行；本 work ID 从未写过
  `blocks_consuming_gate`，无 release 义务。
- **停点自证核实（workflow §4.3.1 四项）**：(1) 范围/接口冻结——AC-7…13 逐条有证据指针（§1）；冻结闭集 8/8 磁盘 SHA 与
  `git rev-parse HEAD:<path>` blob 逐一等于 K4 冻结收据；六份 jsonl 磁盘 SHA = 冻结收据；`upload/manifest.json` SHA = K4
  `package-receipt.json`（`264839e5…`，与 R2@K4 核实值相同）；K4 数据包未改。(2) 相称测试——副本内 focused 重跑通过（下）；
  停点全套 `tests.log`「Ran 1247 tests … FAILED (errors=9, skipped=21)」，`ERROR:` 行集合与基线（`7650c82:docs/evidence/
  P1-ENG-SFT-002-tests.log`）排序后 `diff` 为空、`FAIL:` 行 0 条、1247 − 1202 = 45 = 静态枚举 `def test_` train 14 + cloud 31；
  C1 退回三处失败路径的具名回归修前红/修后绿本轮核实成立（下）。(3) 零 Unity Play/ID，申请 `UNITY_NA`（文末附议）。
  (4) 交接行、候选、报告 §7 与限制 §7.6 已写。四项成立，**不给 `REVIEW_BLOCKED`**。
- **副本与只读边界**：`git worktree add --detach .claude/worktrees/review-P1-ENG-SFT-002 461f288`；通读、重跑、探针全在副本。
  红绿在第二个一次性副本 `review-P1-ENG-SFT-002-red`（候选 + `git checkout 7eefb8e -- tools/eng_sft/{cloud_runner,verify_return}.py`，
  即修前 blob `c540d2c…` / `3634d78…`）完成后即删。主树 `outputs/eng-sft/P1-ENG-SFT-002/{data,receipts,returned,upload,logs,selfcheck}`
  只按绝对路径**只读**（标准库 SHA/JSON）；三份摘要复算在会话 scratchpad 的隔离本地根副本（`data/`、`receipts/`、`returned/`、
  `upload/manifests/` 共 229 MB）上以 `verify_return.summarise(..., repo_root=<主树>, local_root=<scratch>, write=False)` 完成，
  run 收据落在 scratch，主树 `outputs/` 与 `docs/evidence/` 零写入（收工时两目录最新 mtime 仍为实现者 19:43/19:46）。
  未运行 `bundle`/`selfcheck-pack`/`job-a`/`job-b`/`selfcheck`/`select`，零 GPU、零云端、零启动计次。两个副本收工均
  `git worktree remove --force`。
- **重跑（不信报告数字）**：副本内系统 `python3`（3.14.6）`python3 -m unittest tests.test_eng_sft_train tests.test_eng_sft_cloud
  tests.test_eng_sft_build tests.test_eng_sft_evaluate tests.test_eng_sft_audit tests.test_eng_sft_three_state tests.test_eng_sft_parse`
  → `Ran 91 tests in 41.556s … OK (skipped=1)`（输出写 scratchpad `review-r1k3-focused.log`，只回显摘要）。唯一 skip =
  `FreezeTests.test_real_frozen_set_still_matches_local_freeze_receipt`，其 `skipUnless` 条件是仓库根下存在 `outputs/…/freeze-receipt.json`
  ——一次性副本不带 git 忽略的 `outputs/`，属副本环境而非候选缺陷；该断言本轮已在主树以只读探针独立核实（冻结 8/8）。
  实现者主树全套日志 skipped 21 与基线相同，说明该条在实现者环境未 skip。测试树哈希 `HEAD:tests` =
  `91bd793cce0518cfc07d47a92e119378c392f746`，`HEAD:tools/eng_sft` = `fb7b59ef1a2b7cb3a3de8d16364af65373992eca`。
- **修前红 / 修后绿（接受侧关注项①；C1-K3-1…3 的 5 条具名测试一次运行）**：修前源码 + 候选测试 → `Ran 5 tests … FAILED
  (failures=7, errors=1)`：`JobTests.test_job_a_resume_skips_finished_stages_and_counts_retry` **ERROR**（`KeyError: 'resumes'`）；
  `JobTests.test_resume_with_changed_bundle_or_environment_is_refused_before_any_write` **FAIL**（`LaunchRefused not raised`）；
  `JobTests.test_job_b_refuses_job_a_from_another_bundle_before_creating_job` **FAIL**；`ReturnTests.test_summarise_refuses_selection_
  not_bound_to_current_job_a` **FAIL**（`EngSftError not raised`）；`SelfcheckTests.test_selfcheck_rejects_out_of_range_values_before_
  counting` 子测试 `rows=-1`、`rows=0`、`steps=-1` 各 **FAIL** + 末尾 `assertFalse(selfcheck-count.json)` **FAIL**。与报告 §8
  「3 FAIL + 1 ERROR + 自检 4 子测试 FAIL」逐条相同；候选上 5/5 通过（含于 focused 91）。夹具全部由生产路径产出：`rebundle_changed`
  改受束源文件 → `git commit` → 重打合法新束（code-manifest SHA 变、K4 清单不变），环境变化用 `mock.patch.object(engine, "environment")`
  只换引擎返回值；断言旧回传目录逐文件 SHA 不变、启动账不变、不重训。
- **红线检查**：三份新模块不 import `controller.*` / `tools.dist_data`（`WriteBoundaryTests` 两条在 focused 内通过 + 通读顶层与延迟
  import）；代码束 10 成员闭集 = 表 K，`three_state/build_sft_data/evaluate/label_audit/verify_return` 不进束；`upload/data/` 只有
  `train/smoke/select-eval.blind/eval.blind` 四文件，`upload/` 顶层 = {frames, data, manifests, manifest.json, code, code-manifest.json}，
  选层/评估 gold 未上云（`verify_package` 允许集合 = 两份清单成员 ∪ 清单自身，并集外一律拒绝）；评分只在本地 `verify_return` +
  冻结 `evaluate.py`。训练标签上云是合同明写的离线数据加工。不改运行时任何文件。无 `RED_LINE`。

### 1. 逐条 AC 核对（K3：AC-7…13 及其修订）

| 编号 | 结论 {满足, 不满足, 证据缺失} | 证据 | 理由 |
|---|---|---|---|
| AC-7（含修订 1/2） | 满足 | `cloud_runner.run_bundle`/`verify_package`/`_check_members`/`package_identity`/`require_same_package`/`_prepare`；`PackageTests` ×3、`FreezeTests` ×3（+1 skip 见 §0）、`JobTests` C1-K3-1 两条 + 同包续跑追加断言；`verify_return.verify_returned`；`ReturnTests.test_returned_manifest_must_match_local_package_and_bundle`；主树只读探针 | 代码束按表 K 闭集生成、`code-manifest.json` 逐成员路径/字节/SHA/来源 blob、不含自身、`upload_manifest_sha256`/`freeze_receipt_sha256`/模板与词表 SHA 绑定、空 `code/tools/__init__.py` 记 `source: null`（修订 2）；`bundle` 前提 = freeze/package 收据存在、prompt/parse 副本 = 冻结收据、源文件已跟踪且工作区字节 = HEAD blob、末次输入重算、暂存后原子替换且 K4 清单 SHA 前后相等、`upload/` ≤ 0.3 GB。云端 `verify`：允许集合 = K4 成员 ∪ K3 成员 ∪ 两份清单（修订 1），多件/缺件/字节不符 → `PACKAGE_INCOMPLETE`，帧 `stem == sha256`；冻结链：数据清单与代码清单各记冻结收据 SHA、预检收据三方相等、四份 jsonl「成员 = 冻结收据 = dataset-manifest」、`eval.blind` = eval-manifest、prompt/parse 副本 = 冻结收据 `frozen_set`、运行中模板 SHA、`transfer_branch`，任一不符 `FROZEN_SET_MISMATCH`；`expect_code_dir` 断言正在运行的四个模块位于包根 `code/`。本地 `verify_returned` 比对回传收据 `upload_manifest_sha256`/`code_manifest_sha256` 与本地 package/bundle 收据、`job_id` 冻结前缀、逐文件字节/SHA、缺/多、`returned/` ≤ 512 MB、adapter ≤ 200 MB。真实工件：A/B 收据 `package` 6 个身份字段逐一相等且 = 本地 bundle（`65807e07…`）/package（`264839e5…`）收据，`full: true`、`frozen_chain: OK`、data 2,335 / code 10；A 回传 20/20、B 2/2 逐文件字节/SHA 相符、无缺无多；候选 2 相对 K4 通过候选冻结 8 文件 diff 0 行（§0）。 |
| AC-8 | 满足 | `cloud_runner.tokenizer_recheck`/`TorchEngine.check_grids`；`train_lora.recount_gold_tokens`/`compare_recount`/`check_grid`；`PrecheckTests` ×2、`GridTests`、`JobTests.test_tokenizer_file_mismatch_stops_before_inference`；`train-summary.tokenizer_recheck`/`image_grid` | 作业 A 顺序 = 全包校验 → base 下载一次 → tokenizer 四文件 SHA = 本地预检收据（不等 `TOKENIZER_MISMATCH`，测试断言零预测、零启动记账、留 preflight 失败收据）→ 同版 `tokenizers` 对包内 `train.jsonl + smoke.jsonl` 全部 `gold_text` 重算，逐文件 `gold_rows/rows_without_gold/token_max/token_p50/token_total` 五字段须等于预检收据，先查 > 152 → `GOLD_TOKEN_OVERFLOW` 不截断 → 网格预检对四份数据文件引用的全部帧逐张断言 `[1,30,40]`（`check_grids`），推理与训练每行/每样本再断言一次。真实：train 4,907 行 max 87 / smoke 32 行 max 63、`matches_precheck_receipt: true`、tokenizers 0.23.2；网格 2,327 张（A）/ 392 张（B）零不符；评估 gold 不在包内（§0）；结果均入两份 `job-receipt.json`。 |
| AC-9 | 满足 | `run_job_a` zero-shot 阶段（`engine.predict(source, eval_rows, …)` 无 adapter）；`verify_return.summarise` 零样本分支；`zero-shot-v2-summary.json` | base + prompt v2 在 609 行盲评估集运行一次（启动账 zero_shot 1/2）；预测 609 行、`row_id` 唯一 609、`model_id` = `Qwen/Qwen3-VL-2B-Instruct@8964…4203`（`summarise` 断言零样本预测全部为 base 产出）、`parse_error` 非空 103 行保留在分母；摘要含表 F 全部组（G1/G1_G2/G1t/G2/G2t/G3/G3p/G3t/G4/G5）指标、`by_class/by_seen/by_stratum` 分层、`paired_difference_*`、`v1_diagnostic_rows` 405、功能门判定（非劣判定按合同只在 eval-summary 出现，零样本摘要中已 `pop`），并绑定 `job_id`、`job_receipt_sha256`（= 现算 A 收据 SHA `02337fa2…`）、`predictions_sha256`。 |
| AC-10（含修订 1…3） | 满足 | `train_lora.{CANDIDATES,recipe_document,expand_multiset,plan_batches,lr_factor,assistant_label_mask,_training_batch,_assistant_loss_sum,train_candidate,smoke_verdict,selection_score,select_best}`；`ConfigTests` ×2、`ScheduleTests` ×2、`TemplateTests` ×2、`SmokeTests` ×2、`SelectionTests` ×2、`ModuleBoundaryTests`、`JobTests.test_smoke_failure_stops_before_training`；`train-summary.json`、`receipts/selection-<A>.json` | 配方常量逐项 = 表 H（base/revision/bf16、r16/α32/dropout 0.05、LLM 七投影正则且 ViT/merger 不命中、cosine + warmup 3%、有效批 16、梯度检查点、seed 20260912、greedy/160/batch 1、assistant-only）；修订 2 的 AdamW(0.9,0.999)/eps 1e-8/wd 0、裁剪 1.0、`ceil(N/16)` 末批保留、`random.Random(f"{seed}:{epoch}")` 洗牌、损失 = 有效批 assistant token CE 总和 / token 数、标签 = gold + `<|im_end|>`（模板内标签数 ≠ 独立计数 + 1 → `TOKENIZER_MISMATCH`）、micro-batch 只切分累积且 OOM 折半重做同一步并逐步记录；修订 1 冒烟 = 32 行不展开、lr 1e-4、30 epoch × 2 步 = 60 步、warmup 2、末步 loss 为该步更新前值、更新后权重预测 32 行经冻结 `parse` 后状态须全对（解析失败计错）、`SMOKE_FAILED` 停在训练前（测试断言）、冒烟 adapter 记 SHA 后删除；修订 3 选优 = 三态各自准确率算术平均（有理数精确）、并列 = 与最高分差 ≤ 0.5 pp（含等号，非传递）→ epoch 少 → lr 低，选层 gold 先核冻结收据 SHA，正式评估 gold 不参与。真实：冒烟 60 步、末步 loss 0.01334、32/32；C1/C2/C3 = 666/999/666 步、warmup 20/30/20、多重集 5,318、micro-batch 8→8 无折半、峰值显存 8,796,921,344 B、LoRA 196/196 且 ViT 0、可训练 17,432,576；选层预测各 441 行唯一、零解析失败；选优 C1 14161/18450 = 0.76753、C2 2474/3075 = 0.80455、C3 4789/9225 = 0.51913，并列集 {C2}，选中 C2，与报告 §6.1.2 逐值相同；adapter manifest 含表 I 字段（base id + revision、adapter sha/字节、LoRA 配置、seed、数据 manifest SHA 两种、步数/epoch、被选原因、`job_id`、`env.json` SHA）；`accounting` 记各阶段启动/耗时/推理行上界与预算快照。注：`lr_factor(0)=0` 使第 1 个优化步 lr 为 0（与 HF `get_cosine_schedule_with_warmup` 同式，测试显式断言；见 §4 注记 3）。 |
| AC-11 | 满足 | `run_job_b`；`verify_return.{verify_returned,select_adapter,summarise,failure_cases}`；`ReturnTests` ×4（含 C1-K3-2 具名回归）；`eval-summary.json`；`cmd: python3 tools/eng_sft/evaluate.py --verdict …` 本轮实跑退出码 0 | 作业 B：`--adapter` ∈ 闭集、A 须 `complete` 且 `runs[adapter].adapter_sha256` = 实例上 adapter 文件现算 SHA（否则 `RETURN_HASH_MISMATCH`）、A 记录的包身份 = 当前全包校验（C1-K3-1，建目录前）、不重下权重、tokenizer 复核与评估帧网格断言后在 609 行盲评估集预测一次（eval 1/2，总 6/8）。本地：`verify` 通过后 `summarise` 要求选优收据 `job_id`/`job_receipt_sha256` = 当前 A（C1-K3-2）、B `selected_adapter` 的 config/SHA/来源 = 选优结果、B 预测 `model_id` 全部 = 被选 adapter SHA、`eval.jsonl` 先核冻结收据 SHA、G3′ 取框经 `build_sft_data.load_definite_boxes` 绑定 build 输入清单；表 G 判定由冻结 `evaluate.summarise` 产出。真实：选优收据绑定当前 A（`02337fa2…`）；eval-summary `job_b_receipt_sha256` = 现算 B 收据 `8982f204…`、`predictions_sha256` = B 预测文件、`selected_adapter` = A.runs.C2 = 文件 SHA `4044dd4f…`；判定 `GATE_NOT_MET`（G3 报告率 0.3958 / 严格 0.25 / 误报歧义 0.0232 通过 / 误报 none 0.1158 / G5 none 0.79）、`NON_INFERIOR`（+26.64 pp，CI [20.46, 32.82]，阈值 −2.0）、`transfer NOT_RUN(SFT_003_NOT_DONE)`，`--verdict` 命令读出与摘要逐值相同；失败分析报告 §6.2.6、`failure_cases` 八组 min(10, 失败数) 按 `row_id` 升序（G1 49/10、G1t 8/8、G2 9/9、G2t 8/8、G3 36/10、G3t 12/10、G4 15/10、G5 21/10），IoU 用冻结 `evaluate.iou(gold_norm_xywh, predicted_1000)` 同一签名；启动账 6/8、无追加 run。**三份摘要用候选（修后）代码在隔离本地根重算，与已提交 JSON 递归比对逐字段相同、序列化字节数相同（293,714 / 16,416 / 373,862）**（接受侧关注项③）。 |
| AC-12（含修订 1） | 满足 | `cloud_runner.TRANSFER_STATUS`（束内固定、`verify_package` 断言 `transfer_branch`）；`verify_return.{transfer_decision,assert_transfer_frames_disjoint,package_frame_sha256}`；`TransferTests` ×2（K3）+ `test_transfer_verdict_is_mechanical_with_na_rule`（K4）；eval-summary `verdict.transfer` | 签发日一次性判定（账本 2026-09-18）为 `NOT_RUN(SFT_003_NOT_DONE)` 终态；代码束/bundle 收据/两份 job-receipt/eval-summary 均记同值，SynDrone 成员 0、包内无 `syndrone` 路径、推理/GPU/上传 0；兼容条件机检与泄漏断言仍有具名测试（`INCOMPATIBLE_EVAL_SCHEMA:MISSING_FIELDS:stratum`、`CONSERVATION_MISMATCH`）；本分支未阻塞 K3 交付。 |
| AC-13（含修订 1） | 满足（CLASS_3 补丁 F6） | 报告 §6.2（三问、表 G、分层、失败案例、来源/许可、账目）、§6.1.4/§6.2.9/§7.6 披露；`cloud_runner.{StageLedger,budget_plan,init_budget,BudgetGuard,Watchdog,_hard_exit_after,require_envelope_gpu,check_pins,run_selfcheck,_whole_number_between}`；`LedgerTests` ×5、`SetupStopTests`、`SelfcheckTests` ×4（含 C1-K3-3）、`JobTests.test_job_refuses_wrong_gpu_or_version_drift`、`WriteBoundaryTests` ×2；账本/Unity 日志代录 | 三问直接回答与表 G/表 L 结论、按类别/S-M-L-NA/seen-unseen 分层、每组 min(10, 失败数) 失败案例（row_id/指令/预测/gold/本地图片指针）、base Apache-2.0 与 adapter/数据不发布、账目对信封逐项（设备单张 5090 `gpu_count 1`、启动 1/1/3/1 总 6 ≤ 8、推理 609+32+3×441+609 = 2,573 ≤ 4,264、权重一次、上传 ≈ 120 MB 私有、`returned/` 211.3 MB ≤ 512 MB、全目录 440,382,155 B ≤ 0.9 GB、账单 $1.72 ≤ $6、保守覆盖 3.01 h ≤ 8 GPU·h、D-1 磁盘 32 GB 偏差已入账并裁定）均已交付且与我方对收据/摘要的只读核实一致。修订 1：启动账持久化且失败计次、各阶段子上限与总 ≤ 8（测试）；`budget-plan/-init` 四项费率必填、缺一 argparse 拒绝、负/None/GPU ≤ 0 拒绝、流量预留先从 6 美元扣、`min(8, (6 − 流量)/(GPU + 存储))`、绝对销毁截止 + 提前 6 分钟守卫、只初始化一次、上限不得超过信封；守卫在阶段入口/逐行/逐步/下载前/网格逐张检查，后台看门狗不依赖回调（测试）且触发时记账写收据后 `os._exit(3)`；操作单 §3 写明运行器不销毁实例、闹钟与硬截止；命令行无 `--allow-version-drift` 等绕过开关（测试断言 `SystemExit`）；非单张 5090 / 钉版本漂移 / 权重重下 一律 `LaunchRefused`。自检信封：`rows∈[1,4]`、`steps∈[1,5]`、`micro_batch≥1` 且真整数在计次与模型调用前拒绝（C1-K3-3）；不计次前置（缺模块/无 CUDA/本机无同版权重）；运输副本只含 smoke。候选 2 diff 中实现者提交只触及 A1/A2 与状态板（`git log --name-only` 逐提交核对，§0）。报告 4 处「待入账」/「41 项」残留措辞为 CLASS_3 → F6；不改数字、不驱动任何操作。 |

C2@K3 五条关注项落点：①红绿成立（§0）；②历史代码束与修后代码区分核实（束内 10 成员：8 个与候选源码逐字节相同、
`cloud_runner.py` = 修前 blob `c540d2c…`（= `b6f63f1`/`5ef2820`/`7eefb8e` 版本）、`code/tools/__init__.py` 为生成空文件；
`code-manifest.source_head` = `b6f63f1…`；bundle 收据 utc `20260918T183109Z` 早于修正提交；A/B 无续跑记录、6 次启动均首次成功；
修后 `cloud_runner.py` 未打进任何束、未上云——与报告 §7.3 一致）；③三份摘要复算逐字段相同（AC-11 行）；④残留措辞 → F6；
⑤D-2 披露保持（报告 §6.1.4/§7.6 写为已发生流程偏差，账本接受侧裁定同义；本轮不补证、不要求重租）。

### 2. 读过的文件与测试

副本内逐行通读：`tools/eng_sft/{cloud_runner,train_lora,verify_return}.py`、`tools/requirements-eng-sft.txt`、
`tests/test_eng_sft_{cloud,train}.py`；定位阅读冻结 `evaluate.py`（`iou`/`score_rows`/`load_gray_boxes`/`load_legacy_predictions`/
`--verdict`）、`build_sft_data.load_definite_boxes`、`receipts.py` 常量；`git diff 7eefb8e..461f288 -- tools/ tests/` 全文；K3 报告
全文；三份摘要（结构、verdict、配对差、分层、失败案例、accounting）；`tests.log`/基线日志 `Ran`/`ERROR:`/`FAIL:` 行；提案
Part B（表 H/K/I/L、写入分层）、AC-7…13 与 11 行修订、待裁定节、C1@K3/C2@K3 核对表（后者为主树未提交版本）、复判与决策记录；
`docs/authorizations.md` 2026-09-18 三条 K3 条目与接受侧裁定；`docs/unity-test-log.md` `UT-P1-ENG-SFT-002-cloud-runs`；
`docs/phase1-single-drone-design.md` v0.3.42 段；`docs/implementation-status.md` 本项节与 F2/F3 账本行；状态板当前节、交接与
K3 相关 Log。主树只读：`outputs/eng-sft/P1-ENG-SFT-002/{returned/<A>,returned/<B>}` 全部 22 个工件与两份 job-receipt、
`receipts/{bundle,package,freeze,precheck,selection-<A>,run-return-*}.json`、`upload/{manifest,code-manifest}.json`、
`upload/code/**`、`upload/data/`、`upload/manifests/`、`data/*.jsonl`。未读 `logs/`、`selfcheck/`、`panel/` 正文（非本停点证据）。

### 3. Findings

**阻断：无。** 全量 diff 逐文件通读，未发现 CLASS_1/2 可达缺陷；无 `RED_LINE`；C1@K3 三处修复红绿成立且夹具为生产路径。
本轮不写 `blocks_consuming_gate`。以下编号接续 R1@K4 的 F1–F5。

#### F6（CLASS_3，依据 `BC-13`）— K3 报告 4 处残留措辞：D-1「待入账」三处与 §5「41 项」测试计数

- **依据条款**：`AC-13`（报告与账目）；接受侧关注项④。均为已执行步骤的时态或叙述计数，不涉及数值判据、阈值、ID、执行顺序或
  终态名，不驱动任何工具或操作员动作 → CLASS_3 闭集内。`docs/evidence/P1-ENG-SFT-002-report.md` 逐字替换补丁（由持有 A1
  写权限的实现角色在下一次提交应用，不改任何数字/哈希/ID/disposition）：
  1. 抬头段（第 6–7 行）：`（§6.2）。三项执行偏差待接受/` + 换行 + `辅助角色入账，接受侧已裁定（§6.1.4）。` →
     `（§6.2）。三项执行偏差已入账并经接受侧裁定（§6.1.4）。`
  2. §4 表 AC-13 行末：`；云端磁盘偏差 D-1 待入账 |` → `；云端磁盘偏差 D-1 已入账并经接受侧裁定为该实例单次例外（§6.1.4） |`
  3. §5「已知限制」首条：`- 41 项无 GPU 测试覆盖纯函数与 \`FakeEngine\` 编排，` → `- 45 项无 GPU 测试覆盖纯函数与 \`FakeEngine\` 编排，`
  4. §6.2.9 表「云端磁盘」行：`| **偏差 D-1**，用户口头选择继续，待入账（§6.1.4） |` →
     `| **偏差 D-1**，用户知情后回「继续」，已入账并经接受侧裁定为该实例单次例外（§6.1.4） |`

#### F7（CLASS_2，范围判据：不可达 → 依据 `SCOPE_GAP`，非阻断，路由接受角色）— `budget-plan` / `budget-init` 的 `--inbound-gb` / `--outbound-gb` 不拒绝负值，可把 6 美元上限抬高

- **依据条款**：`AC-13 修订 1`（存储/流量须在现有 6 美元内预留、不另生额度）；与 C1-K3-3 同一类（CLI 数值只查上界或不查）。
- **位置**：`tools/eng_sft/cloud_runner.py` `budget_plan`：只校验四项费率 ≥ 0 且 GPU 价 > 0，`inbound_gb`/`outbound_gb`
  未校验；`main` 的 `add_rates` 暴露 `--inbound-gb`/`--outbound-gb`。副本内实测：`gpu_usd_per_hour=1.0`、流量价 16.0/17.334
  $/TB 时缺省 12/1 GB 得 `absolute_cap_hours 5.7907`（美元先到，封顶 $6.0）；`inbound_gb=-1000` 得 `transfer_reserve_usd −15.98`、
  `usd_limited_hours 21.98`、`absolute_cap_hours 8.0`（GPU·h 先到）→ 按同一小时价 8 h 计算费 $8 > $6，CLI `budget-plan … --inbound-gb -1000`
  退出码 0。`init_budget` 的 `minutes_since_start < 0` 抛 `ValueError`，`main` 未捕获（回溯退出，仍是拒绝，但不是 `拒绝启动` 退出码 2）。
- **范围判据**：触发状态 = 操作员在命令行键入负 GB；已归档 `budget.json`（`UT-P1-ENG-SFT-002-cloud-runs`）用的是缺省 12/1 GB，
  实例已销毁；不是提案/AC 点名的触发状态，也不能从已归档工件产生 → 不可达 → `SCOPE_GAP`。修法（供接受角色决定记债或纳入范围）：
  `budget_plan` 拒绝 `inbound_gb < 0` / `outbound_gb < 0`（`LaunchRefused`），`minutes_since_start < 0` 改抛 `LaunchRefused`，
  `LedgerTests.test_budget_plan_reserves_storage_and_transfer_inside_six_dollars` 追加负值断言。

#### F8（CLASS_2，范围判据：不可达 → 依据 `SCOPE_GAP`，非阻断，路由接受角色）— 看门狗线程与主线程可并发写同一 `job-receipt.json.tmp`

- **依据条款**：`AC-13 修订 1` / K3-P1（看门狗到点记账后结束运行器）；workflow §4.4「并发/原子性」。
- **位置**：`cloud_runner._hard_exit_after` 在后台线程内调用 `ledger.finish(...)`、`_json_dump(watchdog-stop.json)`、
  `job.finalize(...)`；主线程同时可能在 `_run_stage` → `job.save()` 或 `run_job_a/b` 的 `finally` → `job.finalize()`。
  `_json_dump` 用固定临时名 `path.name + ".tmp"` 再 `replace`，两个线程同时写同一 `.tmp` 时，先 `replace` 的一方可能把另一方
  写到一半的内容发布成 `job-receipt.json`（后者 `replace` 抛 `FileNotFoundError`，看门狗侧被 `except BaseException` 吞掉后
  `os._exit(3)`）。后果：回传收据可能是截断 JSON，本地 `verify_returned` 以未捕获的 `JSONDecodeError` 回溯而非 `RETURN_HASH_MISMATCH`
  结束——仍是 fail-closed，不会放行错误证据。`StageLedger.save` 同理（`ledger.finish` 主/看门狗两侧）。
- **范围判据**：触发 = 守卫时刻恰落在主线程写收据的窗口内；真实 A/B 结束时剩余 5.0 h，看门狗从未触发；需新的云端消耗才可达
  → `SCOPE_GAP`。修法：`Job.save`/`StageLedger.save` 加进程内锁，或看门狗只写 `watchdog-stop.json` 与标志、由主线程统一 finalize，
  或临时文件用唯一名（`tempfile` 于同目录）再 `replace`；`LedgerTests.test_watchdog_exit_records_stop_before_exiting` 追加并发写断言。

### 4. 非阻断注记（不是 finding，不带依据列；供接受角色与后续设计参考）

1. **`summarise` 不要求作业 A 收据 `complete`**：只要求 B `complete`、选优绑定当前 A、B 的 adapter 来源/SHA 与选优一致。若操作员
   保留续跑前的部分 A 副本并对其做过 select，且 B 用的 adapter 恰在该部分 A 中已训练完成，`summarise` 会以部分 A 的收据
   （`outcome` 非 complete、缺失 run）产出 train-summary。真实回传 A `complete: true`，且云端 `run_job_b` 已拒绝不完整的 A；
   从已归档工件不可达，只记录；建议 `summarise` 对 A 同样断言 `complete`。
2. **C1-K3-3 回归的修前红来源**：修前源码只查上界，子测试 `rows=-1`/`rows=0`/`steps=-1` 各跑完一次自检并计次，第 4 个子测试起
   由「自检已运行 3 次」的信封上限拒绝（`steps=0`、`micro_batch` 负值、`rows=True` 因此在修前未单独暴露），随后 `assertFalse(计次文件)`
   失败使方法中止，`TorchEngine(micro_batch=0/−1)` 两个子测试在修前未执行。修后全部路径在计次前拒绝、绿色完整；红色足以证明
   下界缺口，只是覆盖顺序值得知道。
3. **首个优化步 lr 为 0**：`lr_factor(0, total, warmup) = 0/warmup = 0`，与 HF `get_cosine_schedule_with_warmup` 同式（合同
   AC-10 修订 2 接受该式；`ScheduleTests` 显式断言）；读 `train-log.jsonl` 时步 1 的 loss 对应未更新的模型，C1/C3 实际有效更新
   665 步、C2 998 步。不改数字、不改结论，只作解读提示。
4. **一次性副本内的 skip**：`test_real_frozen_set_still_matches_local_freeze_receipt` 在不带 `outputs/` 的副本必 skip，其断言由本轮
   主树只读探针覆盖（§0）；后续复核轮同样如此，不视为候选缺陷。
5. **他角色未提交批次**：开工时主树已有接受角色 C2@K3 的 `docs/proposals/P1-ENG-SFT-002-…md`、`docs/implementation-status.md`、
   `docs/current-status.md` 未提交改动；本会话只做锚点增量合并状态板，未触碰前两者（见 §7）。

### 5. 交回接受角色与实现角色的动作

1. [接受] 按 workflow §4.6 / engineering §11 消费本轮 `PASS_WITH_NOTES` 与下方候选 2 `UNITY_NA` 正式附议：AC-7…13 满足；
   K4（AC-1…6/14）与 K3 两停点均已通过、各有 `UNITY_NA` 附议——工作项是否 `DONE` 由接受角色按「实现者证据 + 独立复核 +
   Unity/硬件证据（本项为两次 `UNITY_NA`）」三证据裁定并改写 Gate board Overall（本角色未改 Overall token）；返工归因从依据列机械
   派生（本轮 F6 `BC-13`、F7/F8 `SCOPE_GAP`；`IN_SCOPE_NO_BC`/`上轮漏检`/`上游漏检`/`RED_LINE` 均 0）。
2. [接受] F7/F8 记入 `docs/implementation-status.md`「范围外已知缺陷」账本（`SCOPE_GAP` / `OPEN`）或纳入范围；纳入则各绑一条
   修前红回归（§3 已给出测试落点）。本 work ID 无 `blocks_consuming_gate` 行，无 release 动作。
3. [实现] F6 四条逐字补丁在下一次提交应用到 K3 报告（A1 写权限），不改数字、不重跑任何入口。
4. 计数：K3 C/R = 2/1，本停点 `REWORK_REQUIRED` 0 次，未闭集未冻结；K4 C/R = 2/2 不变；F2/F3 保持账本 `OPEN`。
5. 提交：本复核批次（本文件 R1@K3 块 + 抬头「Latest round」一行 + 状态板锚点增量）留在主树**未提交**，由接受角色或用户提交；
   主树另含接受角色 C2@K3 未提交的提案核对表与 implementation-status 覆盖段（非本角色写入，本会话未触碰），请先提交该批次再提交本批次。

## `UNITY_NA` 正式附议（R1@K3，候选 2）

**正式附议成立**，绑定本轮 `passed_candidate`（`461f288…`）：全量 diff 相对 `7650c82…` 证实 `controller/`、`Assets/`、`config/`、
`ProjectSettings/`、`Packages/` 零字节改动；候选 2 新增的三份模块不 import 运行时模块与 `tools.dist_data`，只读已冻结的 K4 数据包、
本地 gold 与回传目录，写出限于 `outputs/eng-sft/…`、`docs/evidence/` 三份摘要与报告；云端作业 A/B（`UT-P1-ENG-SFT-002-cloud-runs`，
`OFFLINE_GPU_RUN`）与用户 5060 自检（诊断、非证据）均零 Unity Play、零 scenario/session/run/attempt 身份，不改变任何运行时行为；
`job_id` 只是作业收据标识。附议范围只限本 work ID 的 K3 候选 2；候选 1 的附议见 R2@K4。附议不等于 `DONE`：`DONE` 仍由接受角色
在三证据齐全后关闭。

### 7. 边界自查（R1@K3 收工）

- 本会话只写入 `docs/reviews/P1-ENG-SFT-002.md`（追加本 R1@K3 块与抬头一行「Latest round」指针，R1@K4/R2@K4 原文未删改）
  与 `docs/current-status.md`（锚点增量合并：Current state 两句、Gate board 本项行、Active handoffs 本项行、Immediate next actions
  首段、Log 新条目）；`controller/`、`Assets/`、`tools/`、`tests/`、`config/`、`docs/evidence/`、`docs/proposals/`、
  `docs/authorizations.md`、`docs/unity-test-log.md`、`docs/implementation-status.md` 零写入；主树 `outputs/` 零写入（探针只读，
  复算在 scratchpad 隔离副本）。
- 两个一次性副本（`review-P1-ENG-SFT-002` 候选副本、`review-P1-ENG-SFT-002-red` 红绿副本）均已 `git worktree remove --force`；
  主树另有两个非本角色的历史 worktree（`clever-brattain-6de4d8`、`epic-morse-0d4596`），本会话未触碰。
- 自检结果（收工时实跑）：`python3 tools/check_docs.py` → 「docs 合规检查通过：分节上限、执行轨道纪律、Gate-echo、复核文件、
  消耗性门 blocks、DONE 行双证据、commit 引用、Last updated、hooksPath 均符合要求」，exit 0。`python3 tools/check_role_writes.py
  --role review` → 「写入范围检查未通过，共 2 个越权路径：docs/implementation-status.md；docs/proposals/P1-ENG-SFT-002-lora-training-
  and-cloud-execution.md」，exit 1：这两条是接受角色 C2@K3 批次在本会话开工前已存在于主树的未提交改动（开工时 `git status` 即为
  这两文件加状态板 M），不是本角色写入；本会话未触碰、未恢复——恢复会抹掉接受角色未沉淀的核对表与账本覆盖段（AGENTS.md
  「保留其他角色的新条目」）。`git status --porcelain` 共 4 个路径：本角色的 `docs/current-status.md`、`docs/reviews/P1-ENG-SFT-002.md`
  加上述两文件；`git worktree list` 已无本角色副本。提交时请由接受角色（或用户）先提交其批次，再提交本复核批次。
  **本会话未修改任何实现文件。**
- 附：应用户要求，本轮核实过的结果另整理为阶段性成果摘要 `docs/reviews/P1-ENG-SFT-002-stage-summary.md`（只读汇总，
  非新证据，不改任何门；数字全部取自已提交摘要与 K3 报告）。
