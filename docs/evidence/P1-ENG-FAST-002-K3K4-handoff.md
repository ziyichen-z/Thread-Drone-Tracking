# P1-ENG-FAST-002 `C1@K3K4` 候选：阶段 1（线 A）自证与交接

- 派发：supervisor（COORD-015），`Dispatch-Id: P1-ENG-FAST-002-K3K4-20260928T031413Z-ec0f`，`requested.round: K3K4`（续派上一实现派发 `P1-ENG-FAST-002-K3K4-20260927T220318Z-a2e7` 的训练前停点；上一轮本文件内容见 git 历史）。
- 角色：实现（Claude Opus 5.5 子代理）。合同：提案 §2–§7、「用户选 (a) 后的接受处置」、「待裁定：用户授权后的 AC-n 合同补齐」、「Q-1/Q-2 用户选 (a) 后的 AC-n 合同修订（CLARIFY，2026-09-28）」。
- 执行信封：`docs/authorizations.md` 2026-09-27「…并选签 §5 线 A」·「信封 · 阶段 1（线 A）」。
- **结论**：到达 `K3K4` 停点。阶段 1 八门：G-1、G-5、G-6 `GATE_NOT_MET`，G-1s、G-2、G-3、G-4、G-7 `MET` → **`QUALIFICATION_GATE_NOT_MET`**；H 已评 1 次，本项内不再训练、不再评 H；插件与载体自测交 `C1@K3K4`（插件只记 `IMPLEMENTED`）。读数与逐门结论见 `docs/evidence/P1-ENG-FAST-002-report.md`「逐门结论」。

## 执行次序核对（Q-1/Q-2 CLARIFY「执行次序」）

1. 按 Q-1 重建数据集并重核三域与「609 行评估集帧 ⊂ H」断言（另加 H 保留帧口径）→ 全过（`-dataset.json`「domain_assertions」）。
2. 按 Q-2 修订目标标签，按 AR2-1 原算法只对目标层重抽一次（训练前）→ 无目标层 ignore，G-1s 训练前可判（H 目标 S 正样本 406）；无需新增运行时真值通道（`-spotcheck.json`「target_resample」）。
3. 两步通过后才下载基座与训练；随后 V 上选择、冻结、H 一次评估、插件/载体/时延（`-train.json`、`-freeze.json`、`-recall.json`、`-replay.json`、`-latency.json`）。

## 自证（workflow §4.3.1 四项条件）

1. **范围与接口已冻结**：交付件 D1–D5 全部落盘；插件接口即 `TrackerPlugin`（未改协议），规格 `config/det-assoc-v1.models.json` 与冻结文件互相核对；冻结后无 run、无选择变更。
2. **实现者测试通过**：全套（系统 `python3`）`Ran 1551`，82 个错误与派发 base_head 全套基线（`Ran 1489`，82 错）逐条同集，**本批新增失败 0**（基线错误为系统解释器缺 numpy/cv2 等环境项）——artifact:`docs/evidence/P1-ENG-FAST-002-tests.log`；需要 ultralytics/lap 的 focused（`.venv-yoloe`，`test_*det*.py`）`Ran 100 OK`——artifact:`docs/evidence/P1-ENG-FAST-002-focused-venv-tests.log`。
3. **Unity 失败**：本阶段零 Play，无已知 Unity 失败；阶段 2 前提（八门全过且 R1 PASS）未满足。
4. **复核范围、状态板、候选与风险已更新**：见下「复核范围」「未验证项与风险」；状态板交接行已转 Acceptance（`C1@K3K4`）。

## AC-n 逐条证据指针

| AC | 结论 | 指针 |
|---|---|---|
| AC-1（含 Q-1/Q-2 CLARIFY） | 数据集重建、三域与 609 断言全过；目标层重抽 152 框，无目标层 ignore；车辆层沿用 | artifact:`docs/evidence/P1-ENG-FAST-002-dataset.json`「domain_assertions」「summary」「q2_visibility_flags」；artifact:`docs/evidence/P1-ENG-FAST-002-spotcheck.json`「target_resample」「stratum_ignored_layers」；test:`tests.test_eng_det_dataset`（33 项：Q-1 整帧排除/原因优先、Q-2 标志 False→ignore、True/缺失→原规则、仅演示路线、评估帧只在 H 排除帧→失败、目标层重抽处置 4 项） |
| AC-2 | run-1 可复现记账；三项选择只引用 V；冻结文件字段齐全 | artifact:`docs/evidence/P1-ENG-FAST-002-train.json`「runs」「dataset_export」「selection」；artifact:`docs/evidence/P1-ENG-FAST-002-freeze.json`；cmd:`shasum -a 256 outputs/eng-det/runs/run-1/weights/last.pt`（= 冻结文件 `weights.sha256`）；test:`tests.test_eng_det_select`（H 表输入 4 处拒绝 + 规则 6 项） |
| AC-3（含 CLARIFY） | 表 A/V/B、FP/帧、双 IoU、CI、N_min；G-1 `GATE_NOT_MET`、G-1s/G-2/G-3/G-4 `MET` | artifact:`docs/evidence/P1-ENG-FAST-002-recall.json`「gates」「table_A_H」「table_B_demo_route」「table_V_selection」；artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「检测器合格判定」「逐门结论」；test:`tests.test_eng_det_qualify`（§3.1.3 五条 FP 反例 + Q-2 ignore + IoA/conf、门三态、n < N_min 不得 MET、FP 300 帧） |
| AC-4（含 CLARIFY） | 子序列最大间隔 ≤ 2 s、守恒式、8/13 s、切换/碎片/drift_return；关联参数只在 V 选并冻结；G-5/G-6 `GATE_NOT_MET`；口径 B 与 A 分列、不设门 | artifact:`docs/evidence/P1-ENG-FAST-002-replay.json`「caliber_A」「caliber_B」「gates」；test:`tests.test_eng_det_qualify.SequenceTests`、`.CaliberBTests`、`tests.test_eng_det_select.OnlyVTests` |
| AC-5 | 插件接口/工厂/CLI；规格与冻结 sha fail-closed；绑定规则；三种结果；不改绑；`frame_id`=送入帧数 | test:`tests.test_det_assoc_tracker`（17 项：初始化无匹配、并列取高分、buffer 内 unmatched 后同 ID 恢复、移除后 lost、原位新 ID 不改绑、权重 sha 篡改、冻结 sha 不符、字段缺失 6 种、设备回退记 manifest、两次运行逐帧相同（ByteTrack/BoT-SORT）、`init` 后 `frame_id`=1、`init` 恰调一次检测+关联） |
| AC-6（AR2-2 释义） | 初始化帧单独验证；首个 update 起 767 帧逐帧相同；`init=False` 既有路径；schema/字段集不变；零写入临时目录外 | test:`tests.test_det_assoc_carrier`（2 项，`.venv-yoloe`）；artifact:`docs/evidence/P1-ENG-FAST-002-replay.json`「carrier_reference」；cmd:`git diff --stat "$(git log --format=%H --grep='Dispatch-Id: P1-ENG-FAST-002-K3K4-20260928T031413Z-ec0f' | tail -1)^" HEAD -- controller/track_loop.py controller/tracking_entry.py runtime/README.md`（只含 CLI 闭集一处） |
| AC-7（含 CLARIFY） | G-7 `MET`：CPU p95 48.4 ms、MPS p95 31.9 ms（各 320 帧）；CPU/MPS 框差 1.3e-7 | artifact:`docs/evidence/P1-ENG-FAST-002-latency.json` |
| AC-8（含 CLARIFY） | 插件导入闭集；可见性标志/斜距只进离线标签、抽查、评分；未新增运行时真值通道 | test:`tests.test_det_assoc_tracker.TruthIsolation`；artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「真值隔离」 |
| AC-9（含 CLARIFY） | 各维度 ≤ 信封；`runtime/`（仓库与数据根）全树哈希前后一致；产物只在 `outputs/eng-det/`（1.0 GB ≤ 5 GB）与 `docs/evidence/`；权重不入库；`h_evaluations`=1 | artifact:`docs/evidence/P1-ENG-FAST-002-ledger.json`（counters、`runtime_trees_before/after`）；cmd:`git status --porcelain -- runtime`（空） |
| AC-10 | §6.3 读数表逐格、不可推出栏；三域三口径标注；§6.2 分支记录与「本项内不再训练」；无禁用主张 | artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「§6.3 预注册读数表」「§6.2 预注册分支执行记录」 |
| AC-11 | 换插件备忘逐条指向 LOOP-001 条款；LOOP-001 零改动 | artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「LOOP-001 换插件备忘」；cmd:`git diff --stat "$(git log --format=%H --grep='Dispatch-Id: P1-ENG-FAST-002-K3K4-20260928T031413Z-ec0f' | tail -1)^" HEAD -- docs/proposals/P1-ENG-LOOP-001-*.md docs/parked-status.md`（空） |
| AC-12 | 阶段 2，未到前提（八门未全过），未执行、未申请 | —（`NOT_RUN`） |
| AC-13 | 冻结先于 H；FreezeGuard 拒绝无冻结/sha 不符/冻结后 run/第 2 次 H；run 结束早于冻结 | test:`tests.test_eng_det_qualify.FreezeGuard`（6 项）；artifact:`docs/evidence/P1-ENG-FAST-002-freeze.json`、`-ledger.json`（`h_evaluation` 1） |

## 消耗（账本 `docs/evidence/P1-ENG-FAST-002-ledger.json`）

下载 1/1（官方 `yolo11n.pt`，字节数与发布值一致）；训练 1/3（run-1，13,276 s；合计 3.69 h / 14 h）；H 评估 1/1；模型启动 13（不限次逐次记账：V 表 1、训练前 T 集干跑 2、时延 2、H 评估检测器 1 + 插件 1、载体测试 3 次运行 × 2 = 6）；传输 0；pip 0；Play/ID/API/云 0。`outputs/eng-det/` 1.0 GB。

## 待裁定（实现读法，交接受角色；实现角色不自行扩大解释）

低风险、均已按下列读法实现并有测试或证据指针；若接受角色不同意，按其裁定修正（H 不重评）。

- **IR-1**（上一轮已登记）：抽查同层相同帧 sha + `object_id` 去重。
- **IR-2**（§3.2 epoch 计时）：「先跑 1 epoch 计时」作为 run-1 的一部分单独执行（epochs=1，独立目录，权重不用），同扣 1 次训练；`t_epoch` 取该次整次墙钟（含建模/扫描/val，偏保守）；`epochs=min(40,⌊6 h/t_epoch⌋)`，并收紧为「计时 + epochs×t_epoch ≤ 6 h」（本次两者都得 40）。
- **IR-3**（§3.1.3 训练填充）：ignore 框填充均值色后，把落在正样本框内的像素还原（T 299 框、V 71 框与正样本相交），避免填充毁掉正样本。
- **IR-4**（§3.4 序列）：序列单位 = 会话（帧目录）而非整族（m3-armA/B 各 trial 仿真时间重叠）；整帧排除帧（仅 scout-1 的 63 帧）留在关联器输入中、真值记 None；「13 s + track_buffer 帧」按该子序列中位帧间隔折秒。本次所有子序列均未被切分或丢弃。
- **IR-5**（冻结/规格互引）：规格记冻结文件 sha；冻结文件记「去掉 `freeze` 字段的规格核心 sha」，避免循环。
- **IR-6**（Q-2 适用集合）：演示路线会话 = scout-1、M3 arm A、M3 arm B；s004-scout 有标志但非演示路线，影子统计全 True，零数值影响。
- **IR-7**（609 断言加严）：原断言按 H 域成员判定；另加「评估帧 ⊂ H 保留帧」，两者都过。
- **IR-8**（匹配与插件检测）：评估匹配类别无关（同 FAST-001）；插件 NMS IoU 取 ultralytics 预测缺省 0.7；插件对两类检测都关联（不按类别过滤）。
- **IR-9**（距离轴）：表 A 车辆用轴向深度、目标在有斜距的会话（m3、scout）用斜距、survey 目标无距离（`NA`）；G-4 斜距取既有真值 sidecar（只进评分）。
- **IR-10**（时延）：分位数含预热帧（前 10 帧另列），不剔除。
- **IR-11**（测试中的模型启动记账）：载体测试每次运行实例化插件 2 次，计入 `model_start`（本轮 3 次运行共 6）。

## 复核范围（`R1@K3K4`，新鲜上下文）

- 代码：`tools/eng_det/{dataset,spotcheck,train,select,evaluate,qualify,plugin_replay,latency}.py`、`controller/det_assoc_tracker.py`、`controller/trackers.py`（工厂 5 行）、`controller/track_loop.py`（CLI 闭集 1 行）、`config/det-assoc-v1.models.json`（生成件）。
- 测试：`tests/test_eng_det_{dataset,select,qualify}.py`、`tests/test_det_assoc_{tracker,carrier}.py`（库相关用例需 `.venv-yoloe`：数据根 `~/TetheredDroneTracking-full/.venv-yoloe`，用 `python -m unittest discover -s tests -p 'test_*det*.py'`）。
- 证据：本文件与上表各 artifact；候选 diff：`git diff "$(git log --format=%H --grep='Dispatch-Id: P1-ENG-FAST-002-K3K4-20260928T031413Z-ec0f' | tail -1)^" HEAD`（上一派发的数据集/抽查代码在更早提交，复核时一并看 `tools/eng_det/` 全部文件）。
- 重点：K4 ——Q-1/Q-2 规则落地、目标层重抽与处置、三域断言、§3.1.3 匹配/ignore/FP、门判定与 N_min、冻结守卫；K3 ——插件绑定/丢失/不改绑、`init` 恰一次关联、载体一致性；AC-8 真值隔离。

## 未验证项与风险

- H 只评一次，所有 H 读数不可重跑；复核如发现评分代码缺陷，修正后只能对**已缓存的 H 检测**重新评分（不重新推理、不改冻结），是否允许由接受角色/用户裁定。
- 权重、检测缓存、导出训练集在 `outputs/eng-det/`（不入库，本机 1.0 GB）；复核需本机或同样的数据根。
- 目标框为 Unity 投影派生（`UNVERIFIED`），G-1 L 未过集中在训练未覆盖的 s004-scout 近距离帧、且以框重叠不足为主（IoU 0.3 下 0.927）——这是读数，不是本项内可调的缺陷。
- 口径 B 显示绑定轨迹通常 8–21 s 内被移除且不改绑；这是合同 K3 语义的直接结果，换插件是否可接受归 LOOP-001 裁定。

## 下一交接

Acceptance：`C1@K3K4` 核对轮（读本文件「AC-n 逐条证据指针」「待裁定」与候选 diff），核对后交 `R1@K3K4`。复核之后按 §6.2 冻结后分支回用户三选一（(i) 范围声明进入 LOOP-001 换插件裁定 / (ii) 换目标外观另立 / (iii) 新工作项新信封）；阶段 2 Play 前提未满足，不申请。
