# P1-ENG-FAST-002 阶段 1 报告（线 A：Mac `.venv-yoloe`；零 Play）

- 派发：supervisor（COORD-015），`Dispatch-Id: P1-ENG-FAST-002-K3K4-20260928T031413Z-ec0f`，`requested.round: K3K4`；角色：实现（Claude Opus 5.5 子代理）。
- 合同：提案 §2–§7 + 「用户选 (a) 后的接受处置」+「待裁定：用户授权后的 AC-n 合同补齐」+「Q-1/Q-2 用户选 (a) 后的 AC-n 合同修订（CLARIFY，2026-09-28）」。
- 数字来源：`-dataset.json`、`-spotcheck.json`、`-train.json`、`-freeze.json`、`-recall.json`、`-replay.json`、`-latency.json`、`-ledger.json`（均在 `docs/evidence/`，文件名前缀 `P1-ENG-FAST-002`）。本报告只摘录，数值以 JSON 为准。
- **标注约定**：`SELECTION_DOMAIN` = V（a7，与 T 同属 dev 原子，偏乐观，只用于选择）；`TRAINED_ON_ATOM` = 表 B / G-4 / G-5（scout-1、m3-armA 在 T 内，只回答「训练过的演示路线几何」）；`HELD_OUT` = H（test 两原子，冻结后只评一次）。口径 A = 关联层能力（每帧真值重绑定）；口径 B = 插件身份（一次绑定不改绑）；口径 C = `TrackLoop` 载体一致性。

## 结论（一句）

阶段 1 八门合取中 G-1、G-5、G-6 为 `GATE_NOT_MET`，其余五门 `MET`；按已签映射，阶段 1 记 **`QUALIFICATION_GATE_NOT_MET`**，不得写 `IMPLEMENTED_REVIEWED_AWAITING_UNITY` 或 `DONE`。**本项内不再训练、不再评 H**（H 已评 1 次）。插件 `det-assoc-v1` 与载体自测照常交 `C1@K3K4` 复核（插件只记 `IMPLEMENTED`）。

## 数据集与抽查（AC-1；Q-1/Q-2 CLARIFY）

| 域 | 帧 | Q-1 整帧排除（`TARGET_UNBOUNDED`） | 保留 | 目标正样本 S/M/L | 车辆正样本 S/M/L |
|---|---|---|---|---|---|
| T | 12,499 | 5,459（rate、scene-val 全部，scout-1 63） | 7,040 | 922 / 1,750 / 1,005 | 1,847 / 4,803 / 3,504 |
| V | 3,168 | 0 | 3,168 | 109 / 1,072 / 439 | 276 / 2,225 / 2,304 |
| H | 27,868 | 11,013（s004-qual、s004-smoke 全部） | 16,855 | 406 / 6,233 / 3,624 | 2,138 / 8,477 / 13,610 |

- 三域断言（帧 sha 与原子/族两级）与「609 行评估集帧 ⊂ H」全过；另加严一条：609 行评估帧也全部落在 H **保留帧**内（448 个帧 ID / 392 个帧 sha，全在 survey a3/a4/a6/a9、s004-scout、m3-armB）。
- Q-2：演示路线会话（scout-1、M3 arm A/B）既有真值可见性标志为 False 的目标框转 ignore（`iv_truth_invisible`）：T 136 框、H 4 框；训练填充 + 评估 IoA 过滤同 §3.1.3 (ii)(iii)。s004-scout 虽有 scouting 标志但不属演示路线，影子统计 4,836 帧全 True（对标签零影响）。标志只进离线标签、抽查与评分。
- 目标层按 AR2-1 原算法重抽（训练前、盲法、不参照旧判定）：19 个非空层、152 框，`OK` 136 / `LOOSE` 15 / `INVISIBLE` 1 / `WRONG` 0；无目标层 `STRATUM_IGNORED`；`target|->=64|a7` 1/8 = 12.5% → `STRATUM_FLAGGED`。车辆层沿用 2026-09-27 原处置（`EXCLUDED_OCCLUDED`、`TRUNCATED` 三档跨族组 ignore）。整帧抽查的 `UNLABELED_RISK`（rate、scene-val、s004）沿用原记录；其中 rate/scene-val 已全部整帧排除，s004 组被标记的 6 帧均来自已排除的 s004-qual/smoke，保留的 s004-scout 抽样帧 0/4 有未标注车辆——标记照原规则保留，仅作并列说明。

## 训练、选择与冻结（AC-2、AC-13）

- 基座：官方 `yolo11n.pt` 下载 1 次（5,613,764 B，与 GitHub 发布字节数一致；sha256 见账本）。
- run-1：imgsz 640、batch 16、seed 20260926、MPS、AMP 关、`flipud=0`、库默认增广、`patience=0`（库内即不早停）；训练图 3,521 张（T 保留帧 1/2 抽帧），训练期 val 634 张（V 1/5）。计时 epoch 370 s → epochs = min(40, ⌊21,600/370⌋) = 40；run 墙钟 13,276 s（3.69 h ≤ 6 h）。取 `last.pt`。
- 表 V（`SELECTION_DOMAIN`，conf 0.25，IoU 0.5）：target S/M/L = 0.917 / 0.927 / 0.977；vehicle S/M/L = 0.971 / 0.945 / 0.923；FP/帧 0.076（conf 0.40 时 0.037）。V-1、V-1s、V-2、V-3 全 `MET` → 按 §3.2 不开 run-2；有效 run 仅 run-1。
- conf：0.25 已使 V FP/帧 ≤ 0.50，取 0.25（无 `CONF_FLOOR_NOT_MET`）。
- 关联选择（只在 V 序列，口径 A 13 s 保持率）：BoT-SORT/0.7/30 = 0.419（最高），BoT-SORT/0.8/30 = 0.416，ByteTrack/0.7/30 = 0.369，buffer 60 的四组 0.24–0.27。冻结 **BoT-SORT（GMC sparseOptFlow）match 0.7、buffer 30**。
- 冻结 2026-09-28T07:20:39Z，先于任何 H 读取；`qualify.py` 读 H 前核对冻结文件、规格核心 sha 与权重 sha，并扣 `h_evaluation`（1/1）。所有 run 的结束时刻早于冻结时刻。

## 检测器合格判定（AC-3）

冻结 conf 0.25 单阈值，IoU 0.50 主口径（G-4 为 0.30）。括号内为 95% bootstrap CI（描述性）。

| 表 | 类别 | S | M | L | FP/帧 |
|---|---|---|---|---|---|
| A（H，`HELD_OUT`） | target | 0.879 (n 406) | 0.987 (n 6,233) | **0.731** (n 3,624；@0.3 = 0.927) | 0.154（16,855 帧；conf 0.40 描述：0.123） |
| A（H，`HELD_OUT`） | vehicle | 0.949 (n 2,138) | 0.906 (n 8,477) | 0.952 (n 13,610) | 同上 |
| V（`SELECTION_DOMAIN`） | target / vehicle | 0.917 / 0.971 | 0.927 / 0.945 | 0.977 / 0.923 | 0.076 |
| B（演示路线，`TRAINED_ON_ATOM`） | target | 0.968 (n 711) | 1.000 (n 484) | 1.000 (n 56) | 0.207（1,601 帧，描述） |

- 目标 L 格未过集中在一处：H 中带斜距的 L 目标（全部为 s004-scout，n 2,047）IoU 0.5 召回 0.525，而 survey 的 L 目标 0.998。IoU 0.3 下 L 格 0.927，说明多数检出了但框与 `target_blocker_px` 派生框重叠不足 0.5——s004-scout 是训练集中没有的场景配置（scene-004）近距离帧。只报告，不在本项内调整。
- H FP/帧按族（描述）：m3-armB 0.002、a3 0.132、a4 0.117、a6 0.192、a9 0.051、s004-scout 0.245（s004 组原有 `UNLABELED_RISK` 标记，并列）。
- 表 B 斜距档（G-4 用，IoU 0.3）：50–65 m 0.984（n 493），≥65 m 0.904（n 156）。

## 关联合格判定（AC-4）

口径 A（冻结 BoT-SORT/0.7/30，每帧真值 IoU ≥ 0.30 重绑定，FAST-001 R4 同口径）；子序列全部未切分（最大帧间隔 H 0.426 s、scout-1 0.206 s、m3-armA 0.259 s，均 ≤ 2 s），无丢弃子序列。

| 格 | 13 s 保持率（D） | 8 s | 备注 |
|---|---|---|---|
| G-5 scout-1（`TRAINED_ON_ATOM`） | 0.815（525） | 0.854 | FAST-001 R4 同序列 40% |
| G-5 m3-armA D>0 合并（`TRAINED_ON_ATOM`） | 0.788（226） | — | BODY arm A 五段单列 0.774（212）/ 8 s 0.846 |
| G-6 H 合并（`HELD_OUT`） | **0.411（6,728）** | 0.499 | ID 切换 1,593、超 buffer 丢失 2,349 |
| H 逐族（只报告） | m3-armB 0.521（73）；s004-scout 0.500（4,067）；a3 0.062；a4 0.041；a6 0.210；a9 0.545 | — | scout-4 单列 0.497（FAST-001 R4 25%） |

- survey 四族的窗口大量 `ID_SWITCH`（目标出画后以新 ID 回画，关联层无 ReID，§6.1-5）；s004-scout 无 ID 切换，但有 2,033 个超 buffer 漏检窗口（其中 2,033 个为同 ID 找回，`drift_return`）。
- 口径 B（插件本体，一次绑定不改绑，描述性、不设门）：H 可见帧 `HIT` 比例 0.414（`HIT` 4,243 / `DRIFT` 964 / `MISS` 5,048；8 段初始化成功、3 段无可见帧），首次 `bound_track_removed` 中位 17.0 s；逐族 m3-armB 0.986、s004-scout 0.801、survey 0.03–0.06。V 0.018（12.2 s 后移除）、scout-1 0.029（8.0 s 后移除）。即：一旦绑定的轨迹被库移除，插件按合同只报 lost、不改绑，后续可见帧全部 `MISS`。
- 口径 C：`tests.test_det_assoc_carrier` 在 scout-1 子序列（1 帧初始化 + 767 帧 update）上，载体逐帧 `(state, box, reason)` 与口径 B 完全相同；初始化帧发布用户框 `placeholder` 观测、库 `frame_id=1`；`init=False` 走载体既有失败路径。

## 时延（AC-7）

V 子序列 320 次 `update`（检测 + 关联，含预热帧）：CPU p50 43.7 ms / p95 48.4 ms；MPS p50 19.8 ms / p95 31.9 ms；两设备均 ≤ 200 ms。CPU/MPS 插件框最大差 1.3e-7、检测框最大差 2e-7，状态不一致 0 帧（≤ 1e-3）。单进程离线，无 Unity 同机负载。

## 逐门结论

| 门 | 定义 | 读数 | 结论 |
|---|---|---|---|
| G-1 | H target M、L @0.5 各 ≥ 0.90 | M 0.987；L 0.731 | **GATE_NOT_MET** |
| G-1s | H target S @0.5 ≥ 0.70 | 0.879（n 406） | MET |
| G-2 | H vehicle M、L ≥ 0.90，S ≥ 0.70 | 0.906 / 0.952 / 0.949 | MET |
| G-3 | H FP/帧 ≤ 0.50（冻结 conf） | 0.154（16,855 帧） | MET |
| G-4 | 表 B 目标 50–65 m、≥65 m @0.3 各 ≥ 0.80（`TRAINED_ON_ATOM`） | 0.984 / 0.904 | MET |
| G-5 | 13 s 保持率 scout-1、m3-armA 各 ≥ 0.90（`TRAINED_ON_ATOM`） | 0.815 / 0.788 | **GATE_NOT_MET** |
| G-6 | 13 s 保持率 H 合并 ≥ 0.80 | 0.411 | **GATE_NOT_MET** |
| G-7 | 每个已测设备 p95 ≤ 200 ms（Mac CPU、MPS） | 48.4 / 31.9 ms | MET |

阶段 1 映射（账本 2026-09-27 用户确认的八门合取）：三门未过 → **`QUALIFICATION_GATE_NOT_MET`**；无 `NOT_EVALUABLE` 门。

## §6.2 预注册分支执行记录

- 冻结前：run-1 V-门全过，未开 run-2；未 OOM；下载成功 1 次；抽查无目标层 ignore（不需重建）。
- 冻结后：G-1 未过（且 G-5、G-6 未过）→ 按「冻结后：H 任一 G-1…G-4 未过」分支：报告 `GATE_NOT_MET(G-1)`，**本项内不再训练**，插件与载体自测照常交 `C1@K3K4`；Overall 建议 `QUALIFICATION_GATE_NOT_MET`。关联门 G-5/G-6 同时未过（`ASSOC_GATE_NOT_MET` 情形的读数并列记录，但因 G-1 也未过，按前一分支处置）。G-7 通过。
- 复核后回用户三选一（原文 §6.2）：(i) 接受「M 层以上 / 演示几何」范围声明进入 LOOP-001 换插件裁定；(ii) 换目标外观（LOOP-001 合同变更，Unity 改动另立）；(iii) 更大模型/更多数据 = 新工作项与新信封（H 在新项内重新定义或声明已消耗）。本报告不代选。

## §6.3 预注册读数表

| 格 | 取值 | 读法（条件句，离线陈述） | 不可推出 |
|---|---|---|---|
| R1 H target 召回 S/M/L @0.5 | 0.879 / 0.987 / 0.731 | S、M 达门，L 未达；L 未达集中在训练未覆盖的 scene-004 近距离帧，且主要是框重叠不足（@0.3 为 0.927）。按条件句，本项只能说「在未训练会话的离线单帧评估中，S、M 档红立方体可被检出」 | 在线 5 Hz 下的召回；换目标外观后的召回；「持续检测」 |
| R2 表 B 50–65 m / ≥65 m @0.3 | 0.984 / 0.904（`TRAINED_ON_ATOM`） | 各 ≥ 0.80：训练过的演示路线几何在离线单帧上远端可检出 | 泛化；任何跟踪成绩 |
| R3 H vehicle 召回与 FP/帧 | 0.949 / 0.906 / 0.952；0.154 | 召回达门且 FP/帧 ≤ 0.5：静止车候选层在离线评估中漏检与误检都低（FP 受未标注对象影响，s004 并列 `UNLABELED_RISK`） | 换 ID 频率；未标注对象的真实 FP |
| R4 口径 A 13 s 保持率 | V 0.419（`SELECTION_DOMAIN`）；scout-1 0.815（FAST-001 R4 同序列 40%，`TRAINED_ON_ATOM`）；H 0.411 | scout-1 未到 0.90、H 未到 0.80：离线回放中的短板在关联层（目标出画再入画无 ReID、超 buffer 丢失），不在「检不到」 | 在线可行性；真实指定期的保持率；「问题已定位」以外的归因 |
| R4b 口径 B `HIT` 比例、首次 `bound_track_removed` | H 0.414、17.0 s（中位）；V 0.018；scout-1 0.029 | 只描述：一次绑定不改绑的插件在离线序列上，绑定轨迹通常在 8–21 s 内被库移除，此后不再输出该目标 | 任何门结论；在线表现 |
| R5 Mac 插件 p95 | CPU 48.4 ms；MPS 31.9 ms | 每设备 ≤ 200 ms：单进程离线 5 Hz 预算可达 | 同机 Unity 负载；Jetson；Play 机实测 |
| R6 相对 NanoTrack 的可比读数 | NanoTrack 无同口径回放数据 | 只能说「离线回放上关联层保持率的读数」；不作与 NanoTrack 的优劣结论 | 任何换栈优劣结论 |

## 真值隔离（AC-8）

- `controller/det_assoc_tracker.py` 只导入标准库、`controller.trackers` 与 ultralytics/torch；`tests.test_det_assoc_tracker.TruthIsolation` 三条断言：静态导入闭集、子进程导入后无 `tools.*`/`eng_*`/`dist_data` 模块、源码不含可见性标志与目录路径名。
- `target_visible` / `geometrically_visible` 与斜距只经 `tools.dist_data.roots.truth_source_for` 的既有 join 进入离线派生标签（`tools/eng_det/dataset.py`）、抽查与评分（`tools/eng_det/evaluate.py`）；不进插件、控制器、感知输入或传感器元数据，未新增任何运行时真值通道。
- 口径 B 的真值只用于构造初始化替身框与评分；口径 C 载体输入只有归档图像与该初始化框。

## LOOP-001 换插件备忘（AC-11，只写不改）

以下是 `P1-ENG-LOOP-001`（暂停中）合同里与 NanoTrack 绑定、换插件时须由接受角色裁定的条款；本项未改 LOOP-001 任何文字、状态与余额。

1. §1「跟踪本身由冻结的 NanoTrack-v2 承担」与 §3.8 CLI 示例 `--tracker nanotrack-v2`；另 `controller/language_loop.py` 的 `--tracker` 缺省为 `nanotrack-v2`。换插件需改这两处的约定（`track_loop` CLI 缺省仍 `csrt`，本项未改）。
2. 事实 7：跟踪器插件闭集现为 `csrt`/`nanotrack-v2`/`scripted` + 本项新增 `det-assoc-v1`（仅显式选择时导入）。
3. 事实 13 与 AR1-5：「冻结 NanoTrack 无分数阈值、目标出画后通常继续返回 ok」的前提在 `det-assoc-v1` 下变为「有 conf 阈值（0.25）+ buffer 内 unmatched 逐帧报 lost」；角色 B 语义核验中「分数骤降」触发需重定义。
4. AC-4：`raw_lost`/`raw_ok` 语义不变，但出现频率不同——buffer 内 unmatched 帧逐帧报 `bound_track_unmatched`，移除后持续报 `bound_track_removed` 且不改绑（口径 B：H 中位 17.0 s 后移除）。`SUSPECTED` 仍只有人能解除；重新播种仍走人工确认路径。
5. 口径 B 读数（H `HIT` 0.414、首次移除中位 17.0 s；演示路线同路线 m3-armB 0.986）是 LOOP-001 换插件裁定要看的数字；换插件属 LOOP-001 的 K3 候选，首次真实闭环 Play 归 LOOP-001。

## 限制与不承诺

- 检测器是本场景专用局部备选（同一城市、93 辆布局车、红立方体），不取代设计 v0.3 §3「换目标不重训练」属性；换目标外观需重训练。
- 单 seed、单 run、单次 H 评估；bootstrap CI 只作描述；门值是预注册值，不是研究阈值。
- 标签为可见部分框（Unity 投影，`UNVERIFIED`）；FP/帧受未标注对象影响。表 B、G-4、G-5 是训练过的演示路线几何；V 读数偏乐观；只有 H 表 A 与 G-6 是跨会话泛化证据。
- 所有读数是离线单进程结果，不含 Unity 同机负载、云台/机身闭环与 K1 发布门；不主张在线跟踪成绩或 `C_track` 变化；不主张 Jetson/TensorRT。
- 阶段 1 结束不等于 `DONE`；阶段 2 Unity 验证的前提（八门全过且 R1 PASS）未满足，本阶段不申请 Play。
