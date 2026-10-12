# P1-ENG-FAST-001 独立复核（快层替换探针，engineering-v1，停点 `K4`）

角色：复核（review，Fable 池，Claude Code `/review`，新鲜上下文，用户自行开会话运行；非 supervisor §3 派发，无 `Dispatch-Id`）。
轨道：提案抬头逐字 `Workflow: engineering-v1`，接受角色在 D3 `ACCEPTED` 时裁定生效 → 按 `docs/engineering-workflow.md` 复核；依据列仍写 `BC-n`，读作任务合同第 n 条验收项 `AC-n`。
零消耗：不启动 YOLOE/DINOv2/VLM、不查询 5060、不下载、不 Play、不生成任何 ID；只重跑 focused 测试与只读脚本核算证据 JSON。

## R1@K4（2026-09-26）

### §0 候选、基线与开轮资格

- `round_candidate: d493dcf1a72fd1892580e5341f24619e8cb9c32e`（状态板交接时的 HEAD = C1 核对提交）。实现候选提交 = `5659e025c705e5a9d14c4eaa222f5937e2e66815`（K4 候选，`git log` 派生）；本人以 `git diff 5659e02 d493dcf -- tools/eng_fast tests/test_eng_fast_*.py .gitignore docs/evidence/P1-ENG-FAST-001-*` 核实两提交间本工作项全部文件**字节相同**，两 SHA 之间的其余差异是 COORD-015 落地/收尾提交（另有独立复核 `docs/reviews/COORD-015.md`，`passed_candidate` 91e0590），不属本工作项。
- 全量 diff 基线：本文件此前不存在，无 `passed_candidate`；基线取实现开工提交的父提交 `1225ab0`（§5 信封入账）。`git diff 1225ab0..5659e02` 共 31 文件（`.gitignore` 1 行、状态板、`tools/eng_fast/` 13 文件、`tests/test_eng_fast_*.py` 5 文件、`docs/evidence/P1-ENG-FAST-001-*` 10 文件），已逐文件核对；C1 提交 `d493dcf` 只改提案「Contract conformance」/Status 行、状态板与 `docs/parked-status.md` 一行加注。
- 开轮资格（workflow §4.4）：PLAY_GOVERNING 上 diff 非空（`tools/eng_fast/*`、`tests/test_eng_fast_*.py`）→ 开轮。冻结件 `git diff --stat 1225ab0..d493dcf -- Assets config controller tools/eng_sft tools/run_detector_scouting.py ProjectSettings Packages/packages-lock.json` 为空（AC-11 冻结件零改动成立）。
- 停点自证（workflow §4.3.1 四项，`docs/evidence/P1-ENG-FAST-001-K4-handoff.md`「自证四项」）核实：(1) 范围冻结成立（候选只新增合同 §2.1 点名的文件与一行 `.gitignore`）；(2) 相称测试：本人重跑 focused 两解释器各 44 例 OK（见下）；全套 `-tests.log`（`Ran 1578`，`failures=1, errors=9, skipped=27`）的 9 个 ERROR 名单与 `docs/evidence/P1-ENG-LOOP-001-tests-k1k2k3-c5-fix.log` 逐名相同（系统解释器缺 cv2 等的 loader 导入失败 + `test_rate3_reanchor_clock_mismatch_raises_defensively`），1 个 FAIL 为 `test_dist_data_round4.RealArchiveClosureTest.test_zero_unmatched_and_zero_multi_matched_jpg`（主树 `runtime/frames/` 诊断残留所致，与本候选无关：该残留在 `runtime/` 前后全树清单里均在且清单一致）；本批新增失败 0 属实。全套重跑是实现者义务，本人未重跑；(3) Unity 不适用（零 Play，见 §4）；(4) 状态板、候选与未验证风险已更新。自证条件成立，不判 `REVIEW_BLOCKED`。
- 复核副本：`.claude/worktrees/review-P1-ENG-FAST-001`（detach 于 `d493dcf`）；测试树哈希 `HEAD:tests` = `8f24a0e65ec3d9383580a0bb33d8e99fb1e2e700`，`HEAD:tools/eng_fast` = `a6d7c28e1097d0cf074b457aad2b87f9f696eb4a`。
- 重跑（副本内，输出写会话临时目录只回显摘要）：
  - 系统 `python3 -m unittest tests.test_eng_fast_inputs tests.test_eng_fast_recall tests.test_eng_fast_margin tests.test_eng_fast_replay tests.test_eng_fast_vlm_parse` → `Ran 44 tests … OK (skipped=3)`（跳过的 3 条 = 钉版库边界，与 `-tests.log` 一致）；
  - `.venv-yoloe/bin/python -B -m unittest discover -s tests -p "test_eng_fast_*.py"` → `Ran 44 tests … OK`（0 跳过；`LibraryBoundary` 三条实跑，含 30/31/32 次空调用边界，两算法各一次）。注：在 `.venv-yoloe` 下 `-m unittest tests.test_eng_fast_*` 模块名形式会被 site-packages 内一个顶层 `tests` 包遮蔽而 `ModuleNotFoundError`，须用交接文件给出的 `discover` 形式；不是候选缺陷。
- 本轮为首轮，无修前红/修后绿义务；下文无阻断 finding，故无红绿重跑。

### §1 逐文件核对摘要（31 文件 + C1 提交）

| 组 | 文件 | 结论 |
|---|---|---|
| 公共件 | `tools/eng_fast/__init__.py`、`common.py`、`ledger.py` | 分桶口径（S <32 / M 32–64 / L ≥64；`<35`/`35–50`/`50–65`/`≥65`；IoU 0.30/0.50）逐字同合同 §3.1；`_refuse_runtime` 结构性拒绝写入 `runtime/`；信封上限逐字同账本 2026-09-24 条目（缺项 0），动作前扣额、越界抛 `EnvelopeExceeded`。 |
| 输入 | `inputs.py` | scout v1/v2 双 schema、BODY v2、S3 索引（分片 sha 核对、43,535 行）、S4 原子查表 fail-closed、`bank_pool`/`select_bank`/`bank_assertions`/`candidate_set` 与 §3.2.1、§3.5.1（IR-1）一致；详见 §2 AC-1/AC-6。 |
| 检测 | `detect.py` | T0-bank 走 `YoloeProposer.initialize` 同一库内 VP 路径取每帧 `pe`，跨帧算术平均后 L2 归一化、`set_classes` 一次固定，回退分支预注册；T0-oracle 用 `reference.json` 框 + `reference-preview.jpg`（sha 核对）；阈值/`imgsz`/device 取冻结配置。 |
| 召回 | `recall.py` | 类别无关 max IoU、双口径、`same_instance_in_bank`/`INSTANCE_UNKNOWN`/`same_instance_by_design` 三标记、`bucket_table` 只出分桶格（无单一总召回，测试有断言）、FP/帧描述性、`legacy_alignment` 逐 tick 对照旧结果。 |
| margin | `margin.py` | 同会话（帧目录父目录）最近帧 ±0.2 s、同类 ≥2、确定性哈希序取前 300（IR-4）、`CROP_INVALID` 记录、分层/分类别统计。 |
| 回放 | `replay.py` | 具名适配层 `as_boxes()`/`run_sequence()`；`BYTETracker(args)`/`BOTSORT(args)` 无 `frame_rate`；每帧一次 `update(boxes, img)`、`frame_id == n` 断言；七类结局 `window_outcome` 按 §3.4 固定顺序（本人逐条对照，见 §2 AC-5）；守恒式在 `_counts` 内断言。 |
| 四臂 | `vlm_arms.py`、`baseline.py`、`vlm_remote.py` | prompt = v2 首段+词表段+(G4 段) 逐字 + 索引版候选/回复段；`merge_pages` 闭集顺序 = §3.5.3；解析器单一来源（5060 与 Mac 同一份）；臂 A 候选匹配 IoU ≥0.5、`NO_CANDIDATE_MATCH`；臂 D kNN(k=5)/18+1 桶色相直方图/关系按 x 中心与上游同一 40 px 分隔且方向与 `tier1_lang` 一致；5060 脚本账本动作前扣额、smoke 前 32 行首次尝试判停、`INVALID` 重试 1 次从重试余量扣。 |
| 编排/报告 | `run.py`、`run_more.py`、`report.py` | 阶段划分与模型进程启动计数一致（detect 1、margin 1、armd 1、latency YOLOE 1 + DINOv2 1）；`sys.dont_write_bytecode` 防 `runtime/` 下 `__pycache__`；报告全部由证据 JSON 生成，数字同源。 |
| 测试 | `tests/test_eng_fast_{inputs,recall,margin,replay,vlm_parse}.py` | 44 例；AC-1 反例 `test_reference_from_evaluated_atom_fails`、AC-5 的 11 条具名反例 + `adapter_boxes_fields`/`one_update_per_frame`/`library_buffer_boundary`、AC-6 解析/合并/臂 A/评分/配对/prompt 逐字/臂 D 用例均对准条款；合成 fixture 仅用于纯函数判定逻辑，库边界三条直接调钉版库。 |
| 证据 | `-inputs.json`、`-recall.json`、`-margin.json`、`-replay.json`、`-vlm-arms.json`、`-latency.json`、`-ledger.json`、`-report.md`、`-tests.log`、`-K4-handoff.md` | 本人以只读脚本逐项核算，见 §2；报告数字与 JSON 同源（由 `report.py` 生成）。 |
| 其他 | `.gitignore`（`/outputs/eng-fast/`）、`docs/current-status.md`、C1 提交 `d493dcf`（提案核对表、`docs/parked-status.md` 一行） | 与合同 §2.1 及流程一致；C1 核对表 11 项「满足」本人逐项复核成立（下）。 |

### §2 AC-1…11 逐项核实（含 C1 四项预复核关注项）

| AC | 本人核实（副本内只读脚本 / 读码；不信报告数字） | 结论 |
|---|---|---|
| AC-1 | `-inputs.json`：五来源隔离断言 5/5 `passed`；被评原子 scout-1/armA = dev 原子 `3d828d…`，scout-4/armB = test 原子 `c0b2c7…`/`be8296…`，catalog-448 = 两个 test 原子；库 `a2` 全部参考帧原子 `f56088…`（train），库 `td` 车辆参考帧原子 `3d828d…`（dev）、红立方体 `f56088…`；参考帧 ∩ 评估帧 sha = ∅。`splits_pairwise_disjoint = true`。`verify_frame` 对 S1 清单内帧核 sha、清单外帧只记 sha（无外部参照可比，非缺陷）。IR-2（scout-1 实存 v1）逐文件核对且单序列 schema 唯一。 | 满足 |
| AC-2 | `-recall.json` 斜距/轴向深度两表分开；每格 `hit_030/hit_050/n/ci95`；域外格逐字 `N/A(NO_SESSION_REFERENCE)` / `N/A(NOT_AUTHORIZED_T1_UNSIGNED)`；目录车按 `not_in_bank`/`same_instance_in_bank` 两子行；`a2` 库 `BANK_PARTIAL(5/9)` 标注；`no_unbucketed_total = true` 且测试断言表顶层只有分桶子表。 | 满足 |
| AC-3 | `legacy_alignment`：scout-1 0/45、scout-4 172/187，逐 tick 命中不一致 0，max IoU 差 0.0 / 1e-6，`ALIGNED`；口径（MISSING tick 计漏、PAIRED_VISIBLE 分母）与旧结果文件一致。 | 满足 |
| AC-4 | Δ 1/5/13 s 合格对 3,784/819/464，各计分 300（≥200），`CROP_INVALID` 0；嵌入器 = 冻结 `DinoV2Embedder`（构造器内核 sha）。 | 满足 |
| AC-5 | 11 序列 × 2 算法 × 2 窗口 = 44 个窗口摘要全部 `conserved`，逐距离桶守恒，`retention = KEPT/D` 复算一致，`one_update_per_frame` 全真；`window_outcome` 逐条对照 §3.4：(1) `UNBOUND_START` (2) `t_i+W > t_last → CENSORED_END` (3) 窗口内连续 `INVISIBLE` > buffer → `TRUTH_GAP` (4) 顺序扫描 `BOUND_OTHER → ID_SWITCH`、段长达 buffer+1 → `LOST_BEYOND_BUFFER`（含跨窗口末端）、同 ID 恢复且 L ≤ buffer → 继续、序列末仍漏检 → `UNRESOLVED_END_MISS`、无事件 → `KEPT`，一致。**IR-8 库边界本人在钉版库实测复现**：空调用 30 → 同 ID、31 → 仍同 ID、32 → 新 ID（两算法相同）；候选按合同字面阈值 L ≥ 31 记 `LOST_BEYOND_BUFFER`，L = 31 原 ID 找回单列（scout-4 8 s 73/73、13 s 43/43 全部在 L = 31），与 C1 裁定一致；保持率因此偏保守，报告已披露。 | 满足 |
| AC-6 | 候选集（IR-1）本人独立复算：K=0 行 26、每行 K ≤ 12、Σceil(K/16) = 583、K>0 行 583；609 行 gold `target_object_ids` 与 G3′ `definite_ids` 100% 在候选集内；1,673 个候选全部 `referable`、`class_word` 非空；同 448 帧的全部 `OK` 对象合计 10,191（对比 1,673 辆车），支持 IR-1「合同 §5 的 929/588 源自全部 OK 物体」的判断。查询：基线 B 583/583、C 583/583，重试 B 9、C 26，合计 1,201（5060 `budget.json` 一致）；35 条重试的首次尝试全部 `INVALID`、重试输出与首次逐字相同；`finish_reason` 全为 `stop`，生成 token 最大 45（<64，无截断）；smoke 32/32 行两臂各 32 次查询，首次 `INVALID` 率 B 0% / C 3.1%（未停臂）；Mac 复解析不一致 0；无 `NOT_RUN`。分组/分母/层同 §3.5.1；A_C2 G1 161/210、S/M/L 11/30、77/95、73/85 与 SFT-002 摘要逐格相同；`-vlm-arms.json` 内「上界」只出现于否定句（无乘积字段）。 | 满足 |
| AC-7 | 报告「P4 与 DETECT-001 的关系」含验收 4 缺口原文、qual-3 读法（节奏≠召回、决策计数≠FP）、复用冻结件、差异、不闭合声明、四条待复现风险。 | 满足 |
| AC-8 | R1–R8 逐格有取值+证据指针、条件性读法、「不可推出」栏；报告中「换栈」只出现于合同预注册读法条件句与「不给结论」声明，无结论句。 | 满足 |
| AC-9 | `-ledger.json`：计数 download 1 / pip Mac 1 / 5060 pip 0 / YOLOE 2 / DINOv2 3 / 5060 启动 2 / 查询 1,201（重试 35）/ Play、ID、API、GPU·h 0，全部 ≤ 信封；传输 112,129 B / 44,283,392 B / 803,965 B ≤ 300 KB / 150 MB / 5 MB；`runtime/` 前后全树 97,505 文件 `tree_sha256` 相同、`git status --porcelain -- runtime` 为空；本人核 `outputs/…/downloads/lap-0.5.13-…arm64.whl` sha256 = `8a793935…1074`、1,478,096 B，与账本记录一致。5060 启动 Mac 侧记 2（首次 PowerShell 解析失败未加载模型）而 5060 侧记 1，保守口径已披露。 | 满足 |
| AC-10 | CPU/MPS 检测各 320 帧（预热 5 帧不计）p50/p95，DINOv2 单裁图各 300，ByteTrack `update` 768 次（CPU）；CPU/MPS 框一致性 0 帧计数不符、最大差 1e-05；文件内「Jetson/5060/TensorRT」只出现于范围声明句，无时延字段。关联 `update` 为纯 CPU 代码（numpy/lap），无 MPS 变体可测，报告栏位如实留空、无外推（C1 关注项 (4) 成立）。 | 满足 |
| AC-11 | 冻结件 diff 为空（§0）；`-tests.log` 基线归因本人核实（§0 第 4 条）；`.venv-yoloe` 下 44 例本人复跑通过。 | 满足 |

C1 四项预复核关注项：(1) IR-1 与 583/583 —— 已上表 AC-6 独立复算成立；(2) IR-8 —— 边界实测本人复现，判定按字面、子计数披露成立（补充建议见 §3 观察 1）；(3) 全套 1 failure / 9 errors 归因与 `runtime/` 只读、信封扣额 —— §0 与 AC-9 成立；(4) AC-10 MPS 栏 —— 成立。

### §3 Findings

| 编号 | 分级 | 依据列 | 位置 | 内容 | 闭合绑定 |
|---|---|---|---|---|---|
| R1-1 | CLASS_3 | `上游漏检` | `docs/proposals/P1-ENG-FAST-001-fast-layer-replacement-probe.md:7` | C1 提交更新了 Status 行（`C/R 1/0`、`C1@K4 已交 R1@K4`）与核对表，但抬头 `Last updated: 2026-09-24` 未随改（核对表日期 2026-09-26）。不驱动任何工具或操作员动作。 | 不阻断。逐字替换补丁（由提案写权角色下一次提交应用）：`Last updated: 2026-09-24` → `Last updated: 2026-09-26` |
| R1-2 | CLASS_2 | `SCOPE_GAP` | `tools/eng_fast/replay.py` `window_outcome()`（`window = [...]` 为空时 `last_in_window = start`，随后 `not inside and miss == 0 → break` → `KEPT`） | 边界：若 (t_i, t_i + W] 内**没有任何调用帧**（相邻帧间隔 > W）且 t_i + W ≤ t_last，函数在零证据下返回 `KEPT`。`check_timestamps` 只拒绝重复/倒退，不拒绝大间隔；AR1-3 点名的「不规则时间戳」未覆盖此支。**不可达**：本候选全部 11 个归档序列帧间隔 p95 ≤ 0.21 s（`-replay.json` `frame_interval_s`），无任何 > 8 s 的间隔；生产入口不能从已归档工件产生该状态。 | 非阻断，路由接受角色记入 `docs/implementation-status.md`「范围外已知缺陷」（状态 `OPEN`）。建议修复：空窗口作为排除类（如 `TRUTH_GAP` 或新增 `EMPTY_WINDOW` 并同步守恒式）或直接抛 `InvalidTimestamps`；回归测试建议名 `tests.test_eng_fast_replay.NamedCounterexamples.test_empty_window_not_kept`（合成：`times = [0, 9.0, 9.2, …]`，`start = 0`，W = 8）。 |

无 CLASS_1；无阻断 CLASS_2；无 `RED_LINE`（Unity 真值只在事后评分：`bind()`/`object_outcomes()`/`row_outcome()`；检测器与跟踪器输入只有图像与检测；T0-oracle 参考与 DETECT-001 scouting 同协议；候选不触及 `controller/`、`Assets/`、`config/`，不写任何桥文件）。无 `blocks_consuming_gate`。

### §4 非阻断观察（不计 finding）

1. 报告「读数表」R4 格的保持率数字正确且与 JSON 同源，但该格未指向两节之上的 IR-8 说明（L = 31 原 ID 找回按合同字面记为 `LOST_BEYOND_BUFFER`；scout-4 8 s 有 73 起、13 s 43 起，若计入 `KEPT` 则 ByteTrack 8 s 保持率由 25.5% 变为约 33%）。用户裁定时须连读「P2b 序列回放」末段与 `drift_return（其中 L=31）` 列；建议下一次重生成报告时在 R4「取值」末尾追加一句「L = 31 原 ID 找回按合同字面计入 `LOST_BEYOND_BUFFER`，子计数见 P2b 表 drift_return 列（IR-8）」（改 `report.py:_section_readout`，零消耗 `run report` 重生成，不改任何数字）。
2. 5060 `Budget` 未把 183 次重试余量与基线隔离（基线可用满 1,700），与合同「全部计入同一上限」一致，仅提示：若基线查询数接近上限，重试会得不到额度而按 `INVALID` 计。本次 1,166 基线离上限远，未触发。
3. `.venv-yoloe` 内 `tests.test_eng_fast_*` 模块名形式不可用（site-packages 顶层 `tests` 包遮蔽），交接文件的 `discover -p` 形式正确；建议后续证据命令统一用 `discover` 形式。
4. 臂 D 裁图库与评估候选同实例回流（`same_instance_in_bank` 60.4%）已在交接「未验证风险 3」与报告披露；本人复核其只用于 R7 描述性对照，未进任何门。

### §5 `UNITY_NA` 附议

**附议**。理由：候选 diff 不触及 `Assets/`、`config/`、`controller/`、`ProjectSettings/`、`Packages/`；不写任何 `runtime/` 桥文件（`_refuse_runtime` 结构性拒绝 + 前后全树 97,505 文件哈希相同 + `git status --porcelain -- runtime` 为空）；零 Play、零 scenario/session/run ID（账本计数 0）；新增件全部是离线工具、测试与证据。本项不改变 Unity 运行行为，`UNITY_NA` 成立。

### Verdict

**PASS（`R1@K4` 通过）**：AC-1…11 逐项成立，无阻断 finding；R1-1 为 CLASS_3 补丁、R1-2 为不可达 `SCOPE_GAP` 记债，均不阻断。`UNITY_NA` 已附议。`DONE` 三证据（实现者证据 + 独立复核通过 + `UNITY_NA` 附议）的复核侧已齐，关闭裁定与归因归接受角色；本项不给「换栈/保留」结论，探针数据交用户对 `P1-ENG-LOOP-001` 二选一。

passed_candidate: d493dcf1a72fd1892580e5341f24619e8cb9c32e
