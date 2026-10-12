# P1-ENG-FAST-002 — 快层替换实现：在域微调 YOLO11 检测器 + ByteTrack/BoT-SORT 关联插件（离线训练、合格判定与插件接入，零 Play）

Status: QUALIFICATION_GATE_NOT_MET（2026-09-28 阶段 1 描述性收口；非复核通过或 DONE；D2 接受及 AC-n 历史保留）
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（Claude Code `/fable`，Fable 5.1；D2 由 supervisor 派发的 Fable 子代理起草）
Created: 2026-09-26
Last updated: 2026-09-28

> **来历**：`P1-ENG-FAST-001` 探针 2026-09-26 `DONE`（读数表 `docs/evidence/P1-ENG-FAST-001-report.md`「读数表」）。用户看完结论后裁定
> （账本同日「用户裁定：快层换成熟方案…」，逐字）：「但问题是本身的快层也不够灵敏，实验结果很差所以才想找一个成熟的替代方案，毕竟重点在vlm
> 不在快层，快层影响实验得不偿失」；三条路线中选「1. 在域微调 YOLO + ByteTrack（推荐）」（AskUserQuestion 所选选项原文）；随后指示
> 「调整一下，把这个任务交给supervisor做，你只负责想法」。本提案是该裁定的落实：把快层换成工业界标准的「检测 + 关联」栈，
> 检测器用仓库自有带框 Unity 帧在域微调，使快层不再是闭环实验的变量。**本项不给任何研究主张**，不改 `P1-ENG-LOOP-001` 的合同、verdict
> 与余额；`P1-ENG-LOOP-001` 继续暂停，其「续跑或收口」顺延到本项结论之后（账本同日条目）。
> **探针给出的硬约束**（本提案据此设计，数字见 §0 事实 4）：零训练的预训练检测器看不到红立方体（S 层 0/198、≥65 m 2/89），
> BODY 段 ID 保持率为 0 是「检不到」而非「关联丢」；桌面检测时延远低于 5 Hz 预算。所以「成熟替代」必须含在域训练，且合格判定必须先于接入。

> **AR1 → 本稿映射（D2）**：AR1-1 → §3.1.1 三域划分（T 训练 / V 选择 / H 最终评估）、§3.2 选择规则与冻结点、§3.3/§3.4「H 只评一次」、
> AC-2/3/4/10/13；AR1-2 → §3.1.2 分层语义抽查与处置、§3.1.3 ignore 规则与 FP/帧可复算定义、AC-1/3；AR1-3 → §3.4.1 三种身份口径、
> §3.5「初始化帧只调用关联器一次」、§3.6 载体 vs 插件同输入同输出、AC-5/6；AR1-4 → §3.3/§3.4 最小样本量、逐格/逐门判定规则、单阈值、
> 双设备时延、门未过时的状态与交接、§6.3 收紧读法；AR1-5 → §3.8 两阶段完成门（撤回 `UNITY_NA`）、设计属性边界「局部备选」、§5 信封与
> Unity 验证授权分离、AC-12；AR1-6 → §0/§8/§5 删除固定 HEAD 与工件 SHA、§5 明示签发前为 0。
> **本场景专用检测器在本稿只是设计 v0.3 §3 的局部备选**，不宣称取代「换目标不重训练」属性；是否升级为替代由用户裁定（§3.8、§7 (g)）。

## 0. 现状与只读事实（本会话只读核实；`file:line` 以 D1/D2 落盘日的 `main` 为准，实现时按符号名重定位；零模型运行、零训练、零写入 `runtime/`）

| # | 事实 | 来源 |
|---|---|---|
| 1 | 跟踪器插件协议 `TrackerPlugin`：`init(image, box_norm) -> bool`、`update(image) -> TrackerResult`、`manifest_identity()`；`TrackerResult(box_norm, ok, confidence, confidence_source, reason)`；工厂 `create_tracker` 闭集 `csrt` / `nanotrack-v2` / `scripted`；CLI `--tracker` choices `("csrt", "nanotrack-v2")`、缺省 `csrt`（LOOP-001 运行时显式传 `--tracker nanotrack-v2`）。换快层不需要动 `TrackLoop` 主循环 | `controller/trackers.py`（`TrackerPlugin`、`create_tracker`）；`controller/track_loop.py`（`--tracker` 参数定义） |
| 2 | `TrackLoop` 逐帧把 `ok=False` 记为该帧 `LOST`、下一帧 `ok=True` 即回 `TRACKING`；`confidence=None` 归一为 `placeholder 1.0`；`confidence_source` 闭集 `{"tracker","placeholder"}`，其他值判 `invalid_confidence_source`。`TrackLoop.initialize()` 只对初始化帧调用 `tracker.init()` 一次并把 `last_frame_id` 置为该帧；处理循环从之后的帧开始逐帧调用 `update()` 一次 | `controller/track_loop.py`（`initialize`、处理循环、`_publication_ready_result`） |
| 3 | 冻结 NanoTrack-v2 无分数阈值（`score_threshold: None`），只在异常/失败/框无效/分数越界时报 lost；LOOP-001 合同事实 13 与 AR1-5 据此设计了角色 B 语义核验 | `controller/trackers.py`（NanoTrack 插件）；LOOP-001 提案事实 13、AR1-5 |
| 4 | FAST-001 读数（复核 `PASS` 后消费）：红立方体 T0-bank 召回 BODY S 0/198、M 33.2%、L 0/12；默认几何 50–65 m 6.2%、≥65 m 2.2%（IoU 0.3）；同会话 oracle 参考在 scout-1 也只有 50–65 m 1.8%、≥65 m 0%；ByteTrack 8 s/13 s 保持率 scout-1 55%/40%、scout-4 25%/0%、BODY 九段 0（绑定帧 0–67/128）；DINOv2 margin Δ13 s 35%；Mac T0 检测 p95 CPU 68 ms / MPS 30 ms | `docs/evidence/P1-ENG-FAST-001-report.md`「P1 分桶召回」「P2b 序列回放」「时延」「读数表」 |
| 5 | 正式设计 v0.3 §3：SOT 主通道 + YOLOE 低频提议通道，「目标无关（换目标不重训练）」是工程属性不是论文卖点；§3.4 选型表 SOT 主通道首选 NanoTrack / HiT-Small 级、备选 CSRT 等「同一接口可插拔」，YOLO11n（COCO car）列为提议器备选、SAM 2 列为离线参照 | `docs/phase1-single-drone-design.md` §3 引言、§3.4 选型表 |
| 6 | S3 帧目录 `runtime/dist-data/frames_catalog/attempt-2`（151 分片，43,535 帧，全部 `layout_binding_valid ∧ sidecar_complete`）；每对象字段 `amodal_px`、`visible_px`、`visible_norm_xywh`、`status`（闭集 `OK`/`TRUNCATED`/`EXCLUDED_OCCLUDED`/`TOO_SMALL`/`NOT_IN_VIEW`/`PHANTOM`）、`camera_depth_m`、`exposure`；目标车框来自 `target_blocker_px` 裁剪到画幅；上游可见短边下限 `MIN_VISIBLE_SIDE_PX = 12` | 分片首条实读；`tools/eng_sft/adapters/unity_s3.py`（`cropped_target_box`）；`tools/dist_data/contract.py`（状态闭集、`MIN_VISIBLE_SIDE_PX`） |
| 7 | 规模（FAST-001 缓存索引 `outputs/eng-fast/P1-ENG-FAST-001/cache/catalog-index.jsonl.gz` 只读统计，`OK` 车辆 + 目标车）：车辆框 57,430 个 / 31,352 帧，短边 S/M/L = 5,011/22,659/29,760，轴向深度 <35/35–50/50–65/≥65 m = 38,231/11,924/4,819/2,456；目标车有框 15,963 帧，S/M/L = 1,840/9,055/5,068；每帧 `OK` 车辆 p50 1 / p90 3 / max 11；抽样 400 帧 jpg 全部在本机 `runtime/` 下。前 40 分片（11,436 帧）车辆状态计数：`OK` 10,796、`EXCLUDED_OCCLUDED` 13,133、`TOO_SMALL` 4,490、`TRUNCATED` 1,472——只取 `OK` 会漏掉大量部分可见车辆（§3.1 标签规则据此裁定） | D1 只读脚本（读数写入 §8） |
| 8 | 近重复原子划分 `runtime/dist-data/splits/attempt-2/splits.json`（`payload.atom_assignment` / `payload.atoms`）：**train = 1 个原子** {a2}；**dev = 1 个原子**，含 6 族 {detect-scout1, m3-armA, a1-s2, a7, rate, scene-val}（族间存在近重复连通，不能按族做近重复隔离）；**test = 2 个原子** {m3-armB} 与 {a3, a4, a6, a9, s004-qual/scout/smoke}；609 行 VLM 冻结评估集全部落在 test 原子（FAST-001 AC-1 断言 eval ∩ 参考库 = ∅） | `splits.json` 本会话实读；`docs/evidence/P1-ENG-FAST-001-inputs.json` `atoms` / `atoms_of_split` |
| 9 | 环境：Mac `.venv-yoloe` = ultralytics 8.4.104（内置 `BYTETracker`/`BOTSORT`、检测训练器）、torch 2.13.0（MPS 可用）、opencv 5.0.0、`lap` 0.5.13（FAST-001 装入）；5060 = RTX 5060 Laptop 8 GB，`.venv-language` torch 2.11+cu128，无 ultralytics 记录（FAST-001 账本 5060 pip 0）；T7 存有 `/Volumes/T7/CityScene/fast_benchmark/models/yolo11n.pt` 副本，来源未核，其 sha256 由实现时 `shasum -a 256` 解析并与官方公布值比对（一致则下载 0，否则官方下载 1 次） | D1 `python -c` 与 `shasum`；`docs/evidence/P1-ENG-LOOP-001-before-binding-server-startup-5060.json` |
| 10 | 可复用件（零字节改动导入）：`tools/eng_fast/inputs.py`（S3 索引、原子、身份断言）、`detect.py`（`run_frames`）、`recall.py`（`bucket_table`、`fp_per_frame`、`object_outcomes`）、`replay.py`（`run_sequence`、`bind`、`window_outcome`、`window_summary`、`sequence_metrics`，七类结局与守恒式）、`common.py`（分桶口径 S <32 / M 32–63 / L ≥64 px）、`ledger.py`（信封扣额） | `tools/eng_fast/*.py`；`docs/reviews/P1-ENG-FAST-001.md` §1 |
| 11 | FAST-001 记债 R1-2（`replay.py:window_outcome()` 在 `(t_i, t_i+W]` 无调用帧时可零证据判 `KEPT`，本候选序列帧间隔 p95 ≤ 0.21 s 不可达）：复用不规则大间隔序列前须先承接 | `docs/implementation-status.md`「范围外已知缺陷」P1-ENG-FAST-001 / R1-2 |
| 12 | LOOP-001 合同与 NanoTrack 绑定处：§1「跟踪本身由冻结的 NanoTrack-v2 承担」、事实 7/13、CLI 示例 `--tracker nanotrack-v2`、AR1-5（无分数阈值 → 角色 B 核验触发含「分数骤降」）、AC-4 `raw_lost`/`raw_ok` 只作底层事实、`SUSPECTED` 只有人能解除；阶段 B 余额：追加诊断余 1（`diag-loopb-7`）、正式 0/8、启动 5/10、查询 20/400 | LOOP-001 提案 §1、事实 7/13、AR1-5、AC-4；`docs/parked-status.md` 同名节 |
| 13 | 演示目标车 = 两个红立方体（非目录网格）；LOOP-001 定局 ③ Unity 零改动 | `Assets/TetheredTracking/Scripts/TargetVisualFactory.cs`（FAST-001 事实）；账本 2026-09-19 |
| 14 | 用户 2026-09-26 已首次启用 supervisor 无人值守并签发本项决策信封（classes D1/D4/D5/D6，至 2026-10-10）；SUB 子额度、§5 训练/下载/传输信封、任何消耗均未授权 | 账本 2026-09-26「用户签发 supervisor 决策信封并首次启用…」 |
| 15 | `replay.py:bind()` 每帧用**真值框**以 IoU ≥ 0.30 重绑定 track ID（并列取 IoU 大者再 ID 小者），因此 §3.4 的保持率是「关联层能力」口径，不是插件「一次绑定不改绑」口径；两者在 D1 被混用（AR1-3） | `tools/eng_fast/replay.py:bind`（docstring）；D1 §3.4–3.6 |
| 16 | 各族目标车有框帧与短边分桶（缓存索引只读统计，S <32 / M 32–63 / L ≥64 px）：detect-scout1 705（S 470 / M 202 / L 33）、m3-armA 682（377/282/23）、m3-armB 153（12/141/0）、a1-s2 1,234（152/571/511）、a2 1,247（114/695/438）、a3 1,280（107/672/501）、a4 1,294（159/743/392）、a6 1,308（176/730/402）、a7 1,653（142/1,072/439）、a9 1,571（131/1,158/282）、s004-scout 4,836（0/2,789/2,047）；rate、scene-val、s004-qual、s004-smoke 无目标车。S 层目标帧集中在演示路线两族（scout-1 + m3-armA 共 847），survey 各族每族 ≈ 110–180 | 本会话只读脚本（§8） |
| 17 | `catalog-sim-times.jsonl.gz` 覆盖全部 15 族（survey 19,986 帧、s004-scout 4,836、BODY 九段 1,152 等），survey 与 s004-scout 序列可按仿真时间回放；帧间隔分布本会话未算，§3.4 按间隔切分子序列后回放 | 同上 |

## 1. 目的与价值

把快层换成**成熟栈**（类级检测器 + 运动关联），并用仓库自有带框 Unity 帧在域微调检测器，使 `P1-ENG-LOOP-001` 的闭环实验只剩 VLM 这一个变量。交付两样可证伪的东西：

1. **训练好的检测器权重 + 合格判定报告**：候选在选择域 V 上按预注册规则选定并**冻结**后，在从未触碰的最终评估域 H 上**只评一次**（§3.1.1/§3.2），报告分桶召回、FP/帧与序列回放 ID 保持率；门未过则如实报告 `GATE_NOT_MET` 回用户，本项内不再训练、不再评 H。
2. **`det-assoc-v1` 跟踪器插件**：实现现有 `TrackerPlugin` 接口（事实 1），离线载体自测通过，默认插件不变、本信封零 Play。它是 v0.3 §3.4 SOT 主通道「同一接口可插拔」的**局部备选**，与冻结的 NanoTrack-v2 并列注册，不取代缺省路径与「换目标不重训练」属性（§3.8）。

本项是运行时可选插件 + 离线训练/判定，**不申请 `UNITY_NA`**（AR1-5）：`DONE` 需要用户 Unity 验证（§3.8 阶段 2，另签授权）；本信封只覆盖到「实现者证据 + 独立复核」。检测器是**本场景专用**（在域训练），不主张开放词表、真实航拍或跨环境。

## 2. 范围与不做的事

### 2.1 交付（单候选，停点 `K3K4` 合并一次通过）

| 件 | 内容 | 落点 |
|---|---|---|
| D1 数据集构建 | S3 → YOLO 标签（§3.1 规则）+ ignore 集 + 三域清单（每帧 sha、族、原子、域、状态计数）；分层语义抽查记录与处置 | `tools/eng_det/dataset.py`、`spotcheck.py`；`outputs/eng-det/dataset/`（不入库）；`docs/evidence/P1-ENG-FAST-002-dataset.json`、`-spotcheck.json` |
| D2 训练与选择 | ultralytics 训练器、固定配置与 seed；V 上的选择记录；**冻结文件**（权重 sha、规格 sha、conf、imgsz、关联算法与参数、选择依据） | `tools/eng_det/train.py`、`select.py`；`outputs/eng-det/runs/`；`docs/evidence/P1-ENG-FAST-002-train.json`、`-freeze.json` |
| D3 合格判定 | H 上一次性：分桶召回 / FP/帧 / 序列回放保持率 / 插件口径回放 / 时延，复用 FAST-001 工具 | `tools/eng_det/qualify.py`、`plugin_replay.py`；`docs/evidence/P1-ENG-FAST-002-{recall,replay,latency}.json` |
| D4 插件 | `DetAssocTracker`（`name="det-assoc-v1"`）+ 工厂注册 + CLI 闭集扩一项 + 模型规格文件 | `controller/det_assoc_tracker.py`、`controller/trackers.py`（工厂 3–5 行）、`config/det-assoc-v1.models.json` |
| D5 测试与报告 | 具名反例、库边界、真值隔离断言、载体自测；报告与 LOOP-001 换插件备忘；阶段 2 Unity 验证用例说明 | `tests/test_eng_det_*.py`、`tests/test_det_assoc_tracker.py`、`tests/test_det_assoc_carrier.py`；`docs/evidence/P1-ENG-FAST-002-report.md`、`-K3K4-handoff.md` |

### 2.2 明确不做

1. 不改 Unity、场景、`Assets/`、`ProjectSettings/`；演示目标仍是红立方体（事实 13）；换目标外观是 LOOP-001 恢复时的独立裁定。
2. 本信封内不做 Play、不生成 scenario/session/run ID；不动 LOOP-001 阶段 B 余额、合同、verdict、F3/F8 记债。阶段 2 Unity 验证（§3.8）须另签授权。
3. 不改 `TrackLoop` 帧/观测协议、`tracking_observation.json` schema、`confidence_source` 闭集（不触发 K1）；不写任何机身/云台命令（不触发 K2）。
4. 不实现 ReID / `IdentityProfile` / 跨段自动重指定：绑定的 track 被库移除后只报 lost，重新播种仍走 LOOP-001 的人工确认路径（2026-09-19 定局 ④）。
5. 不主张 Jetson/TensorRT、真实航拍、开放词表；不闭合 DETECT-001 验收 4；不训练或改动 VLM、`tools/eng_sft/`。
6. 不改 FAST-001 工具语义（只导入）；不修 R1-2（事实 11），改由 §3.4 的子序列切分规则使其不可达并以测试断言。
7. 不使用 H（test 原子）任何帧做训练、选择或调参；H 在本项内**只评一次**（§3.2 冻结点）；不改旧 benchmark 划分，不宣布旧 benchmark 退役。
8. 不修改 `docs/phase1-single-drone-design.md` §3「换目标不重训练」属性；本项只把 `det-assoc-v1` 作为局部备选（§3.8）。

## 3. 接口与数据契约

### 3.1 标签规则（K4；预注册，接受角色裁定 (a)）

- **类别**：两类。`0 = vehicle`：`object_id` 以 `Vehicle_` 开头的目录车（93 辆全部一类，检测器不区分车型；身份由 VLM 与关联层负责）；`1 = target`：`dynamic-target`，框 = `target_blocker_px` 裁剪到画幅（事实 6，与 `unity_s3.cropped_target_box` 同一函数）。
- **框**：`visible_px` 裁剪到画幅后归一化 top-left xywh（可见部分框，不是 amodal），与运行时跟踪器输出口径一致。
- **正样本纳入条件**：状态 ∈ {`OK`, `TRUNCATED`, `EXCLUDED_OCCLUDED`, `TOO_SMALL`} 且裁剪后短边 ≥ 12 px（= 上游 `MIN_VISIBLE_SIDE_PX`），且不属于 §3.1.2 抽查判定的剔除层；`NOT_IN_VIEW` 不纳入（无可见框）。理由：快层要在部分遮挡与小尺寸下保持连续检测，只取 `OK` 会把画面中大量可见车辆当背景（事实 7）。每状态纳入/排除/ignore 计数写入 `-dataset.json`。
- **整帧排除**：目标车在视野内（`blocking` 含 `dynamic-target`）但无可用框（`frame_wildcard` / `target_source_bound=false` / 裁剪退化）的帧整帧不进训练、不进任何分母（避免未标注的可见目标成为负样本或假 FP），计数报告。
- **抽帧**：训练帧按时间序每 2 帧取 1（5 Hz 近重复）；V 与 H 的评估与序列回放不抽帧。

#### 3.1.1 三域划分（AR1-1；原子级，事实 8/16）

| 域 | 组成 | 用途 | 帧 / 目标车有框帧 / 目标 S 层帧 / 车辆框 |
|---|---|---|---|
| **T 训练** | train 原子 {a2} ∪ dev 原子内 {a1-s2, detect-scout1, m3-armA, rate, scene-val} | 只用于训练（抽帧 1/2） | 12,499 / 3,868 / 1,113 / 19,117 |
| **V 选择** | dev 原子内 {a7}（整族） | 训练期 val 监控；conf 阈值、run 选择、关联算法与参数选择；V-门 | 3,168 / 1,653 / 142 / 4,805 |
| **H 最终评估** | test 两原子 {m3-armB} ∪ {a3, a4, a6, a9, s004-qual, s004-scout, s004-smoke} | 冻结后**只评一次**：表 A、FP/帧、G-5/G-6、插件口径回放 | 27,868 / 10,442 / 585 / 33,508 |

- **断言**（AC-1）：T ∩ H = ∅、V ∩ H = ∅（按帧 sha 与按原子各一次）；T ∩ V = ∅（按帧 sha 与按族）；609 行评估集帧 ⊂ H。
- **V 的诚实边界**：V 与 T 同属 dev 原子（族间近重复连通，事实 8），所以 V 上的数字**偏乐观、只用于选择**，报告中标 `SELECTION_DOMAIN`，不作泛化证据；泛化证据只来自 H。
- **为什么 scout-1 / m3-armA 进 T 而不是 V**：S 层目标帧 847 帧集中在这两族（事实 16），是远端小目标的主要训练信号，也是 LOOP-001 演示路线；放进 V 会使训练几乎没有远端小目标样本。代价是演示路线的读数变成「训练过的几何」（表 B，`TRAINED_ON_ATOM`），只回答「演示路线上看不看得见」，不是泛化——H 中 m3-armB（同路线不同会话）与 survey a3/a4/a6/a9（S 层共 573 帧）承担泛化读数。
- **旧划分不改**：`splits.json` 与 609 行评估集原样保留；本项只在其上派生三域，不宣布旧 benchmark 退役（工程继承清单「train/dev/test、pHash/对象谱系」行）。

#### 3.1.2 派生标签的分层语义抽查与处置（AR1-2；engineering §7）

- **时机与盲法**：数据集构建后、任何训练开始前做一次；抽查者只看图像 + 派生框，不看任何模型输出；T/V/H 一视同仁（标签 QA，不是模型选择）。
- **分层**：类别 {vehicle, target} × 状态 {`OK`, `TRUNCATED`, `EXCLUDED_OCCLUDED`, `TOO_SMALL`}（target 无状态维）× 短边档 {12–31, 32–63, ≥64 px} × 族组 {a2, survey-dev(a1-s2), 演示路线(scout-1+m3-armA), rate, scene-val, a7, m3-armB, survey-H(a3/a4/a6/a9), s004}。每个非空层随机抽 8 框（seed 20260926；不足 8 取全部），上限 300 框；另按族组各抽 10 帧整帧看「有无可见 ≥12 px 车辆无框」。
- **标签闭集**：每框 `OK` / `LOOSE`（框与可见对象重叠明显偏移，估计 IoU < 0.5）/ `WRONG`（框内没有该对象）/ `INVISIBLE`（对象实际不可见）；每帧 `UNLABELED_VISIBLE_VEHICLE` 计数。抽查者 = 实现角色（离线看图，不是 Play）；用户可复看，不强制。
- **处置规则（先写后查）**：某层 (`WRONG`+`INVISIBLE`)/n > 20% → 该层（类别 × 状态 × 短边档，跨全部族组）整层转 **ignore**（不作正样本、评估时作 ignore 区，§3.1.3），记 `STRATUM_IGNORED`；10–20% → 保留为正样本但报告标 `STRATUM_FLAGGED`；`LOOSE` 单独计数只报告。某族组整帧抽查 `UNLABELED_VISIBLE_VEHICLE` 帧比例 > 10% → 该族组的 FP/帧数字标 `UNLABELED_RISK`，G-3 仍按规则判但报告必须并列该标记。原始 S3 与 `splits.json` 一律不改；抽查记录（帧 sha、框、判定）写 `-spotcheck.json`。
- **抽查不替代完整性核验**：`-dataset.json` 同时记每域帧数、每状态计数、sha 清单与三域断言（engineering §7「互补」）。

#### 3.1.3 ignore 规则与 FP/帧可复算定义（AR1-2；AC-1/AC-3 反例）

- **ignore 集**（每帧）：(i) 状态 ∈ {`OK`,`TRUNCATED`,`EXCLUDED_OCCLUDED`,`TOO_SMALL`} 但裁剪后短边 < 12 px 的对象框；(ii) `PHANTOM` 且带框的对象（可见性未知，保守处理）；(iii) §3.1.2 判定 `STRATUM_IGNORED` 的层内对象。`NOT_IN_VIEW` 无框，不进任何集合。
- **训练侧**：ultralytics 无 ignore 语义。(i) 类不填充（过小、填充反而制造伪影），作为背景；(ii)(iii) 类在派生训练图上用该图均值色填充矩形（只改派生副本，不改 S3），填充计数报告。
- **评估侧匹配**（`recall.py` 口径不变，新增 ignore 过滤一层，写在 `qualify.py`）：检测按分数降序、与未匹配正样本 IoU ≥ 阈值（0.50 主口径 / 0.30 副口径）贪心一对一匹配；未匹配检测若与任一 ignore 框的 IoA（交集 / 检测面积）≥ 0.5 → 丢弃（不算 TP 也不算 FP）；其余未匹配检测 = FP。
- **FP/帧** = 评估域内 FP 总数 / 评估域帧数，帧数不含整帧排除帧；只在冻结 conf（§3.2）下判门，另一阈值列只描述。**不再断言「故是真 FP」**：FP 是相对「≥12 px 标注 + ignore 规则」的可复算量，仍受未标注对象与 `UNVERIFIED` 几何影响（§6.1）。
- **测试反例**（AC-1/AC-3）：检测落在 ignore 框上 → 不计 FP；同一正样本两条检测 → 1 TP + 1 FP；整帧排除帧上的检测 → 不进分母也不计 FP；`STRATUM_IGNORED` 层对象在训练标签中缺席且在评估中为 ignore；短边 11 px 对象 → ignore 而非正样本。

### 3.2 训练、选择规则与冻结点（K4；预注册；全部选择只看 T/V，H 零参与）

| 项 | 值 | 备注 |
|---|---|---|
| 模型 | `yolo11n`，初始化自官方 COCO `yolo11n.pt` | T7 副本 sha 与官方一致则下载 0，否则下载 1 次（§5） |
| 输入 | run-1 `imgsz=640`（原生 640×480 letterbox） | run-2 备选 `imgsz=960` |
| epoch | 先跑 1 epoch 计时（记 `t_epoch`），`epochs = min(40, floor(墙钟上限 / t_epoch))`，一次定下不改；`patience` 关（不早停） | 墙钟上限见 §5 |
| batch / seed | 16 / 20260926；MPS 上 AMP 关 | OOM 降 8 → 4 再回用户 |
| 增广 | 库默认（含 `scale=0.5`、mosaic），`flipud=0` | 不做超参搜索 |
| 训练期 val | V 每 5 帧取 1 帧（只驱动库的 val 曲线，不参与权重选择） | 曲线只作信息 |
| 权重 | 每 run 取 `last.pt`，不取 `best.pt` | 不按任何评估选 epoch |
| conf 阈值 | 在 V 上按规则选：取 {0.25, 0.40} 中使 V FP/帧 ≤ 0.50 的**最小值**；都不满足取 0.40 并标 `CONF_FLOOR_NOT_MET` | 0.25 = DETECT-001 冻结阈值 |
| run 规则 | run-1 基线；仅当 run-1 的任一 **V-门**（§3.3 V 列）未过时开 run-2（`imgsz=960`，同数据同 epoch 规则）；run-3 仅用于标签/脚本缺陷修正后的重跑（被修正的 run 作废，不参与选择）；≤ 3 次，每次开跑前在 `-train.json` 写理由 | 不因 H 结果开任何 run |
| run 选择 | 有效 run 中 V-门通过数最多者；并列取 V `target` S 层召回 @0.5 高者；再并列取 run-1 | 规则先写死 |
| 关联选择 | 只在 V 序列（§3.4）上跑 {ByteTrack, BoT-SORT(含 GMC)} × {`match_thresh` 0.8/0.7} × {`track_buffer` 30/60} 共 8 组，取 13 s 保持率最高者；并列依次取 ByteTrack、buffer 30、match 0.8 | 冻结进规格文件 |
| **冻结点** | 选定后写 `docs/evidence/P1-ENG-FAST-002-freeze.json`：权重 sha256 与字节数、规格文件 sha、conf、imgsz、关联算法与参数、V-门读数、有效 run 清单、冻结时 `git rev-parse HEAD`（运行时解析）、时间戳。**冻结之后本项内禁止任何训练与选择变更**；`qualify.py` 读取 H 前必须验证冻结文件存在且权重 sha 一致，否则拒绝运行 | AC-13 |
| **H 只评一次** | `-ledger.json` 记 `h_evaluations`，上限 1；第 2 次调用 fail-closed。H 评估后无论门是否通过，本项内不再训练、不再评 H；再评 H 需新工作项 | AC-13 |

### 3.3 检测器合格判定（K4；复用 `tools/eng_fast/recall.py` + §3.1.3 ignore 层）

- **表 A（H，主表，冻结后一次）**：`vehicle` 与 `target` 分开，短边 S/M/L × 深度四档（目录帧用轴向深度；m3-armB 有斜距则分表），IoU 0.30 / 0.50 双口径、bootstrap 95% CI；候选类别无关（与 FAST-001 同）。
- **表 V（选择域，描述性）**：同表 A 结构在 V 上出数，逐格标 `SELECTION_DOMAIN`；V-门据此判定，用于 run/conf 选择（§3.2）。
- **表 B（seen-geometry，描述性）**：scout-1 与 m3-armA（演示路线，T 内），逐格标 `TRAINED_ON_ATOM`；只回答「训练过的几何上能不能看见」，不是泛化。
- **FP/帧**：按 §3.1.3 定义，冻结 conf 判门，另一阈值只描述。
- **判定规则（AR1-4）**：
  - 最小样本量 `N_min`：召回格 ≥ 50 个正样本；FP/帧 ≥ 300 帧。格 n < `N_min` → 该格写 `N/A(INSUFFICIENT_N=<n>)`，**不得算 `MET`**。
  - 一门 = 其全部定义格：所有格可判且通过 → `MET`；任一格可判且未过 → `GATE_NOT_MET`；无未过格但有不可判格 → `NOT_EVALUABLE(<格>)`（≠ `MET`，报告与交接按未过处理，用户可裁定接受为范围声明）。
  - 全部检测门在**冻结 conf 单一阈值**下判定；IoU 主口径 0.50（G-4 例外为 0.30，与 FAST-001 R2 同口径对照）。
  - H 的门只判一次；V-门同定义在 V 上判，只用于选择。
- **预注册门**（接受角色可在 `ACCEPTED` 前调整、用户确认；未过 = `GATE_NOT_MET`，不是失败伪装）：

| 门 | 定义（格） | 值 | V-门对应 |
|---|---|---|---|
| G-1 | H `target` 召回 @IoU 0.5：M 格、L 格 | 各 ≥ 0.90 | V-1 同 |
| G-1s | H `target` 召回 @IoU 0.5：S 格（≥12 px） | ≥ 0.70 | V-1s 同 |
| G-2 | H `vehicle` 召回 @IoU 0.5：M、L 格 ≥ 0.90；S 格 ≥ 0.70 | 同上 | V-2 同 |
| G-3 | H FP/帧（冻结 conf） | ≤ 0.50 | V-3 同（并驱动 conf 选择） |
| G-4 | 表 B：scout-1 + m3-armA 目标车 50–65 m 格与 ≥65 m 格召回 @IoU 0.3（`TRAINED_ON_ATOM`） | 各 ≥ 0.80 | — |

### 3.4 关联合格判定（K3/K4；复用 `tools/eng_fast/replay.py` 七类结局与守恒式，逐字不改）

- **序列构造**：每族按仿真时间升序（事实 17）为一条序列，真值 = 目标车框（可见）/ `None`（不可见）；**帧间隔 > 2 s 处切分为子序列**，短于 13 s + `track_buffer` 帧的子序列丢弃并计数。因子序列内任一间隔 ≤ 2 s < W，事实 11 的 R1-2（窗口内无调用帧）不可达；`tests.test_eng_det_qualify` 断言每条子序列最大间隔 ≤ 2 s 且 `check_timestamps` 通过。不改 `replay.py`。
- **V 序列**：a7 的子序列（选择关联算法与参数，§3.2）。**H 序列**：m3-armB 四段（FAST-001 已有）、s004-scout、survey a3/a4/a6/a9 的子序列；scout-1 / scout-4 / BODY arm A 五段只作与 FAST-001 R4 的同序列对照（scout-1、arm A 在 T 内，标 `TRAINED_ON_ATOM`；scout-4 在 H）。
- **算法**：`BYTETracker` / `BOTSORT` 钉版 8.4.104，`update(boxes, img)` 每帧一次；参数按 §3.2 只在 V 上选定并冻结；H 只跑一次。
- **口径 A（关联层能力）** = `replay.bind()` 每帧真值重绑定 + `window_outcome` 七类结局（与 FAST-001 R4 同口径）；G-5/G-6 按此判。
- **判定规则（AR1-4）**：保持率格 `N_min` = 30 个已判定窗口（D ≥ 30）；同 §3.3 的 `MET` / `GATE_NOT_MET` / `NOT_EVALUABLE` 规则；「无适用段」（例如 m3-armA 无 D>0 段）→ 该格 `N/A(NO_SEGMENT)`。

| 门 | 定义（格） | 值 |
|---|---|---|
| G-5 | 13 s 窗口保持率（冻结算法）：scout-1 一格；m3-armA 中 D>0 的段合并一格（`TRAINED_ON_ATOM`） | 各 ≥ 0.90 |
| G-6 | 13 s 窗口保持率：H 序列合并一格，另逐族列（m3-armB、s004-scout、a3/a4/a6/a9 各一格，只报告） | 合并格 ≥ 0.80 |
| — | 8 s 保持率、ID 切换/分钟、碎片数、`LOST_BEYOND_BUFFER`/`UNRESOLVED_END_MISS`/`drift_return` 计数 | 报告，不设门 |

#### 3.4.1 三种身份口径（AR1-3；报告必须分开标注，不得互相替代）

| 口径 | 绑定方式 | 真值用途 | 用于 |
|---|---|---|---|
| A 关联层能力 | `replay.bind()` 每帧真值 IoU ≥ 0.30 重绑定 | 绑定 + 评分 | G-5/G-6；与 FAST-001 R4 对照 |
| B 插件身份（离线） | `plugin_replay.py` 用**插件本体** `DetAssocTracker`：在子序列首个可见帧用真值框（用户框的离线替身）调用 `init` 一次，之后逐帧 `update`，不改绑 | 只进入评分：每帧 `ok ∧ IoU(插件框, 真值) ≥ 0.5` → `HIT`；`ok` 但 IoU < 0.5 → `DRIFT`；lost 且真值可见 → `MISS`；真值不可见 → 不计 | 报告 H 与 V 的 `HIT` 占可见帧比例、首次 `bound_track_removed` 时刻、`DRIFT` 计数；**不设门**，是 LOOP-001 换插件裁定要看的数字 |
| C 载体一致性 | `TrackLoop --tracker det-assoc-v1` 同一初始化帧与框（§3.6） | 不进入 | AC-6：与口径 B 的逐帧 `(state, box, reason)` 完全相同（同输入同输出，真值零参与） |

### 3.5 插件 `det-assoc-v1`（K3）

- **类**：`controller/det_assoc_tracker.py:DetAssocTracker`，`name="det-assoc-v1"`、`backend="ultralytics"`、`version="8.4.104"`；工厂 `create_tracker("det-assoc-v1", spec_path=…)` 注册；CLI `--tracker` choices 加一项，缺省值不变（仍 `csrt`；LOOP-001 显式传参）。
- **模型规格** `config/det-assoc-v1.models.json`（schema `tethered-tracker-models/v1` 同族）：权重路径 + sha256 + 字节数、`imgsz`、`conf`、NMS IoU、类别表、设备策略（`mps` 不可用回退 `cpu`，记入 manifest）、关联算法与冻结参数、冻结文件 sha；sha 不符或字段缺失 fail-closed（镜像 NanoTrack 规格检查）。
- **`init(image, box_norm)`**：对初始化帧检测一次 + 关联器 `update` **恰一次**；绑定 = 输出 track 中与初始化框 IoU 最大者，且 IoU ≥ 0.50（并列取分数高者）；否则返回 `False`（走 `TrackLoop` 既有初始化失败路径）。`init` 后不再对同一帧调用 `update`（事实 2：`TrackLoop` 处理循环从下一帧开始；测试断言库 `frame_id` = 已送入帧数，含初始化帧）。
- **`update(image)`**：检测 + 关联；绑定 id 在本帧输出中 → `TrackerResult(box, ok=True, confidence=检测分数, "tracker")`；绑定 id 仍在库的 lost 列表（buffer 内） → `lost("bound_track_unmatched")`；已被库移除 → `lost("bound_track_removed")`。buffer 内库自身把同 id 重新匹配回来即恢复 `ok`（同一 track 身份，不是新绑定）；**不**自动改绑新 id。
- **调用契约**：每处理帧调用一次且按帧序（`TrackLoop` 已保证；追平批也是顺序调用）；库 `frame_id` 每调用加 1。
- **manifest**：权重 sha、规格 sha、冻结文件 sha、库版本、`score_threshold = conf`、`threshold_source = "spec"`、设备；`confidence_source` 只用 `"tracker"`。
- **确定性**：无随机源；同序列两次运行输出逐帧相同；CPU 与 MPS 框差 ≤ 1e-3（FAST-001 实测 1e-5）。
- **真值隔离**：插件模块只导入图像、规格与 ultralytics；测试断言其不导入 `tools.dist_data`、`tools.eng_sft`、`tools.eng_fast`、评估器或任何真值读取路径；运行时不读 S3/S4。

### 3.6 `TrackLoop` 离线载体自测（K3；口径 C）

在临时 runtime 目录用归档帧（scout-1 一条子序列）驱动 `TrackLoop`（`--tracker det-assoc-v1`），初始化帧与框取自 §3.4.1 口径 B 同一次运行的记录，断言：观测桥 schema `tethered-tracking-observation/v1` 逐字段不变、无新增字段、`confidence_source="tracker"`、`TRACKING`/`LOST` 逐帧记录、零写入临时目录之外；载体逐帧 `(state, box, reason)` 与口径 B 的插件输出完全相同。真值只在口径 B 的评分中出现，不进载体。

### 3.7 与 LOOP-001 的换插件备忘（AC-11，只写不改）

列出 LOOP-001 合同中与 NanoTrack 绑定的条款（事实 12）及换插件时需接受角色裁定的点：`--tracker` 缺省与 CLI 示例；事实 13/AR1-5 的「无分数阈值」前提变为「有 conf 阈值 + buffer 内 unmatched」，角色 B 核验的「分数骤降」触发需重定义；`raw_lost` 语义不变但出现频率不同（buffer 内 unmatched 帧会逐帧报 lost）；口径 B 的 `HIT`/首次 `bound_track_removed` 读数；换插件属 LOOP-001 的 K3（模型决策/身份）候选，首次真实闭环 Play 归 LOOP-001。本项不改 LOOP-001 任何文字。

### 3.8 完成门与设计属性边界（AR1-5）

**两阶段完成门**（`DONE` 三证据不放宽；本项不申请 `UNITY_NA`）：

| 阶段 | 内容 | 证据 | 授权 | 到达后 Overall（建议 token，由接受角色裁定） |
|---|---|---|---|---|
| 阶段 1（本信封） | 数据集、训练、冻结、H 一次评估、插件、载体自测、报告 → `C1@K3K4` → `R1@K3K4` | AC-1…11、AC-13 | §5 执行信封（`ACCEPTED` 后另签） | `IMPLEMENTED_REVIEWED_AWAITING_UNITY`（门全过）或 `QUALIFICATION_GATE_NOT_MET`（任一 H 门未过，插件仅 `IMPLEMENTED`） |
| 阶段 2（另签） | 用户 Unity 诊断 Play 一次：LOOP-001 演示路线、`--tracker det-assoc-v1`、≤ 90 s；记录插件 manifest 载入、目标肉眼可见期间 `TRACKING` 帧占比、无异常退出、Play 机时延 p95；写 `docs/unity-test-log.md` `UT-FAST-002-1` | AC-12 | 用户另签：本项独立 1 次诊断 Play 信封，**或**用户裁定复用 LOOP-001 `diag-loopb-7`（见 §7 (h)） | `DONE`（仅当阶段 1 全过 + 复核 PASS + AC-12 通过） |

- 阶段 1 结束时状态板 Overall **不得**写 `DONE`；阶段 2 未获授权则停在阶段 1 token，交接行写「待用户签发 Unity 验证授权」。
- **设计属性边界**：`det-assoc-v1` 在本稿是 v0.3 §3.4 SOT 主通道「同一接口可插拔」下的**局部备选**（本场景专用、换目标需重训练），与冻结 NanoTrack-v2 并列；缺省路径与「换目标不重训练」属性不变，正式设计不因本项同步改动。若用户裁定把它升级为缺省快层（替代该属性），由接受角色在 `ACCEPTED` 后另起设计同步，不在本 D2 内。

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | 数据集按 §3.1/§3.1.1/§3.1.3 构建：三域清单含每帧 sha/族/原子/域/状态计数与 ignore 集；T∩H、V∩H、T∩V 三对零交集（帧 sha 与原子/族两级断言）；609 行评估集帧 ⊂ H；整帧排除与每状态纳入/ignore 计数落盘；§3.1.2 抽查记录与处置落盘且在训练前完成 | artifact:`docs/evidence/P1-ENG-FAST-002-dataset.json`、`-spotcheck.json`；test:`tests.test_eng_det_dataset`（反例：H 帧混入 T 或 V → 失败；V 帧混入 T → 失败；`OK` 以外状态短边 ≥12 px 被纳入；短边 11 px → ignore；`frame_wildcard` 帧被整帧排除；`STRATUM_IGNORED` 层在标签中缺席） | K3K4 | 2026-09-26 |
| AC-2 | 训练与选择按 §3.2 可复现：1 epoch 计时与 epoch 数推导、seed、设备、每次 run 理由与墙钟、`last.pt` sha 与字节数记账；conf/run/关联参数三项选择只引用 V 读数；冻结文件字段齐全 | artifact:`docs/evidence/P1-ENG-FAST-002-train.json`、`-freeze.json`；cmd:`shasum -a 256 outputs/eng-det/runs/<run>/weights/last.pt` 与冻结文件一致；test:`tests.test_eng_det_select`（选择函数只接受 V 表输入；H 表输入 → 拒绝） | K3K4 | 2026-09-26 |
| AC-3 | H 表 A、表 V、表 B、FP/帧按 §3.3 出数（双 IoU、冻结 conf 判门 + 另一阈值描述、CI、`N_min` 与 `N/A(INSUFFICIENT_N)`），G-1…G-4 逐门写 `MET`/`GATE_NOT_MET`/`NOT_EVALUABLE`，无单一总召回；FP/帧按 §3.1.3 可复算 | artifact:`docs/evidence/P1-ENG-FAST-002-recall.json`、`-report.md`「检测器合格判定」；test:`tests.test_eng_det_qualify`（表结构、门判定、n < `N_min` 不得 `MET`、§3.1.3 五条 FP 反例） | K3K4 | 2026-09-26 |
| AC-4 | 序列回放按 §3.4：子序列切分（最大间隔 ≤ 2 s 断言）、七类结局守恒、8 s/13 s 保持率、切换/碎片/`drift_return` 计数；关联参数只在 V 序列选定并冻结进规格；G-5/G-6 按 §3.4 规则逐门写结论；口径 B 插件回放按 §3.4.1 出数并与口径 A 分列 | artifact:`docs/evidence/P1-ENG-FAST-002-replay.json`；test:`tests.test_eng_det_qualify`（守恒式、H 未参与选参断言、`NO_SEGMENT`/`INSUFFICIENT_N` 处理、口径 B `HIT`/`DRIFT`/`MISS` 合成反例） | K3K4 | 2026-09-26 |
| AC-5 | 插件实现 §3.5：接口与工厂/CLI 注册；规格或冻结文件 sha 不符 fail-closed；`init` 绑定规则（IoU ≥0.5、并列取高分、无匹配返回 False、关联器恰调用一次）；`update` 三种结果与 reason 闭集；不自动改绑新 id；库 `frame_id` = 送入帧数 | test:`tests.test_det_assoc_tracker`（具名反例 ≥ 9：初始化框无匹配、并列、buffer 内 unmatched、移除后 lost、新 id 出现在原位置不改绑、规格 sha 篡改拒绝、冻结文件 sha 不符拒绝、设备回退记 manifest、连续两次运行逐帧相同、`init` 后 `frame_id` = 1） | K3K4 | 2026-09-26 |
| AC-6 | 载体自测 §3.6 通过：观测桥 schema 与 `confidence_source` 闭集零改动；载体逐帧 `(state, box, reason)` 与口径 B 同初始化的插件输出完全相同；CLI 缺省插件值不变，未显式选 `det-assoc-v1` 的既有路径行为零改动 | test:`tests.test_det_assoc_carrier`；cmd:`git diff --stat <实现起点 HEAD，运行时解析>..HEAD -- controller/track_loop.py controller/tracking_entry.py runtime/README.md` 只含 CLI 闭集一处（或为空） | K3K4 | 2026-09-26 |
| AC-7 | 时延：Mac 上插件 `update`（检测 + 关联）CPU 与 MPS（可用时）各 ≥300 帧 p50/p95；G-7 = 每个已测设备 p95 ≤ 200 ms（任一设备未过即 `GATE_NOT_MET`，MPS 不可用记 `N/A(DEVICE_UNAVAILABLE)` 且不影响 CPU 判定）；CPU/MPS 框差 ≤ 1e-3 | artifact:`docs/evidence/P1-ENG-FAST-002-latency.json` | K3K4 | 2026-09-26 |
| AC-8 | 真值隔离：插件模块导入闭集断言（不导入 `tools.dist_data`/`tools.eng_sft`/`tools.eng_fast`/评估器）；运行时不读 S3/S4；Unity 真值只在离线标签、抽查与评分中使用 | test:`tests.test_det_assoc_tracker.TruthIsolation` | K3K4 | 2026-09-26 |
| AC-9 | 账目与只读：信封各维度计数 ≤ 用户签发值（签发前为 0，任何动作前先核对账本）；`runtime/` 前后全树哈希一致；产物只在 `outputs/eng-det/` 与 `docs/evidence/`；权重不入库；`h_evaluations` = 1 | artifact:`docs/evidence/P1-ENG-FAST-002-ledger.json`；cmd:`git status --porcelain -- runtime` 为空 | K3K4 | 2026-09-26 |
| AC-10 | 报告含 §6.3 预注册读数表逐格取值与「不可推出」栏；三域与三口径逐处标注（`SELECTION_DOMAIN` / `TRAINED_ON_ATOM` / 口径 A/B）；门未过时含 §6.2 分支执行记录且明示「本项内不再训练」；全文无「跟踪改善」「闭环成功」「优于 NanoTrack」类主张 | artifact:`docs/evidence/P1-ENG-FAST-002-report.md` | K3K4 | 2026-09-26 |
| AC-11 | LOOP-001 换插件备忘 §3.7 落盘，逐条指向 LOOP-001 合同条款；LOOP-001 提案、状态与余额零改动 | artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「LOOP-001 换插件备忘」；cmd:`git diff --stat <实现起点 HEAD>..HEAD -- docs/proposals/P1-ENG-LOOP-001-*.md docs/parked-status.md` 为空 | K3K4 | 2026-09-26 |
| AC-12 | 阶段 2 Unity 验证（§3.8）：用户 Play 一次记录 `UT-FAST-002-1`（插件 manifest 载入、目标肉眼可见期间 `TRACKING` 帧占比、无异常退出、时延 p95）；未获授权或未通过则 Overall 不得为 `DONE` | artifact:`docs/unity-test-log.md` `UT-FAST-002-1`（用户或接受/辅助角色代录） | 阶段 2（另签） | 2026-09-26 |
| AC-13 | 冻结与一次性 H 评估：冻结文件先于任何 H 读取写出；`qualify.py` 无冻结或权重 sha 不符时拒绝；`h_evaluations` 上限 1，第 2 次 fail-closed；冻结后无新 run（`-train.json` 中所有 run 时间戳 < 冻结时间戳） | test:`tests.test_eng_det_qualify.FreezeGuard`（反例：无冻结文件 → 拒绝；sha 不符 → 拒绝；第 2 次 H 评估 → 拒绝）；artifact:`-freeze.json`、`-ledger.json` | K3K4 | 2026-09-26 |

## 5. 预算信封（申请值；**用户逐字签发前各维度均为 0，任何训练、下载、安装、传输、启动均不得开始**；签发后成功、失败、重试全部计入同一上限，耗尽即停）

两条互斥的执行线，**由用户在 `ACCEPTED` 后签发时二选一**（本角色只给推荐，不代承诺资源）：

| 维度 | 线 A：Mac `.venv-yoloe`（推荐：零新环境、零传输） | 线 B：5060 本地训练（快，但要装环境） |
|---|---|---|
| 下载 | 1：官方 `yolo11n.pt`（≈5.6 MB）；若 T7 副本 sha 与官方公布值一致则 0 | 同左 + 新建 `.venv-det`（torch cu128 ≈2.5 GB + ultralytics 及依赖）；或复用 `.venv-language` 加装 ultralytics（风险：动 VLM 环境，需用户明示） |
| 训练运行 | ≤ 3 次，每次墙钟 ≤ 6 h，合计 ≤ 14 h（用户机器占用） | ≤ 3 次，每次 ≤ 2 h |
| 传输 | 0 | 数据集上行 ≤ 1.5 GB、权重下行 ≤ 20 MB（走既有 Tailscale 路径） |
| 评估/回放模型启动 | 不限次，逐次记账；H 评估恰 1 次 | 同左（评估仍在 Mac） |
| 磁盘 | `outputs/eng-det/` ≤ 5 GB | 同左 + 5060 侧 ≤ 3 GB |
| Play / scenario·session·run ID / API / 云 GPU·h / Unity | 0 / 0 / 0 / 0 / 否（阶段 2 Unity 验证**不在本信封**，另签） | 同左 |

信封内的工程性重试与 supersession 不需新授权，由接受角色在本提案决策记录写一行归因（engineering §8）；任何越界（第 4 次训练、换更大模型、云端、Play、第 2 次 H 评估）回用户。LOOP-001 阶段 B 余额与 FAST-001 §5 余额均不得挪用。

## 6. 限制、不承诺、失败模式与预注册读法

### 6.1 限制与不承诺

1. 检测器是**本场景专用**（同一城市、同一 93 辆布局车与同一红立方体）；不主张对其他场景、真实航拍、其他目标外观的召回；换目标外观需重训练。它是局部备选，不取代设计 v0.3 §3 属性（§3.8）。
2. 标签为可见部分框（非 amodal），gold 几何来自 Unity 投影，`UNVERIFIED`；§3.1.2 抽查只按预注册规则剔除/标记层，不裁定标注体系；FP/帧受未标注对象影响（`UNLABELED_RISK` 标记）。
3. 表 B、G-4、G-5 是 T 内演示路线的数字（`TRAINED_ON_ATOM`），只回答「演示路线上能不能看见/保住」；V 上的数字偏乐观、只用于选择；H 表 A 与 G-6 才是泛化到不同会话的证据。
4. 序列回放不含 Unity 同机负载、云台/机身闭环与 K1 发布门；口径 A 是离线关联层表现，口径 B 是离线插件身份表现，都不等于在线跟踪成绩，不主张 `C_track` 改善。
5. 关联层无 ReID：同类多车近距交错时的身份靠运动与 IoU（BoT-SORT 另有 GMC），交错导致的 ID 切换只报告不修。
6. 单 seed、≤ 3 run、单次 H 评估；bootstrap CI 只作描述；门值由预注册给出，不是研究阈值。
7. 不主张 Jetson/TensorRT；不闭合 DETECT-001 验收 4；不改 LOOP-001 任何 verdict；阶段 1 结束不等于 `DONE`。

### 6.2 失败模式与预注册分支（冻结前 / 冻结后分开）

| 情形 | 处置（先写后跑） |
|---|---|
| 冻结前：run-1 任一 V-门未过 | run-2 `imgsz=960`（同数据、同 epoch 规则）；按 §3.2 run 选择规则取一者冻结；两次都记录 |
| 冻结前：MPS 训练 OOM / 不支持算子 | batch 8 → 4；仍失败改 CPU 计时；`t_epoch` 使 epoch < 5 则停下回用户（不硬跑） |
| 冻结前：官方 `yolo11n.pt` 下载不可达 | T7 副本仅在 sha 与官方公布值一致时可用；否则停下回用户 |
| 冻结前：抽查判定 `STRATUM_IGNORED` | 按 §3.1.2 剔除后重建数据集再训练（不计 run 次数，因未开跑） |
| 冻结后：H 任一 G-1…G-4 未过 | 报告 `GATE_NOT_MET(<门>)`，**本项内不再训练**；插件与载体自测照常交 `C1@K3K4`（代码仍可复核）；Overall 建议 `QUALIFICATION_GATE_NOT_MET`；回用户三选一：(i) 接受「M 层以上 / 演示几何」范围声明进入 LOOP-001 换插件裁定；(ii) 换目标外观（LOOP-001 合同变更，Unity 改动另立）；(iii) 更大模型/更多数据 = 新工作项与新信封（H 在新项内重新定义或声明已消耗） |
| 冻结后：G-5/G-6 未过而 G-1…G-4 过 | 报告 `ASSOC_GATE_NOT_MET`：检测够、关联不够，回用户；备选（buffer 加长、GMC）只能在新工作项内于 V 上试，本项不重评 H |
| 冻结后：G-7 未过 | 报告；插件仍交复核；LOOP-001 换插件裁定时按 Play 机实测另议 |
| 任一格 `N/A(INSUFFICIENT_N)` | 门 `NOT_EVALUABLE`，按未过处理进报告与交接；用户可裁定接受为范围声明 |

### 6.3 预注册读数表（报告逐格填值；读法为条件句，只支持离线陈述，「不可推出」为硬约束）

| 格 | 取值来源 | 读法 | 不可推出 |
|---|---|---|---|
| R1 H `target` 召回 S/M/L @0.5 | AC-3 | 若 M/L ≥0.90 且 S ≥0.70，则在未训练会话的离线单帧评估中红立方体在该三档可被检出；若 S 低而 M/L 高，则远端小目标在离线评估中仍是短板，走 §6.2 冻结后分支 | 在线 5 Hz 下的召回；换目标外观后的召回；「持续检测」 |
| R2 表 B 演示路线 50–65 m / ≥65 m 目标召回 @0.3 | AC-3 | 若各 ≥0.80，则训练过的演示路线几何在离线单帧上远端可检出；否则 LOOP-001 主剧本远端仍需人工/VLM 兜底 | 泛化；任何跟踪成绩 |
| R3 H `vehicle` 召回与 FP/帧 | AC-3 | 若召回高且 FP ≤0.5，则静止车候选层在离线评估中的漏检与误检都低；FP 高则关联层要在更多干扰中匹配 | 换 ID 频率（由 R4 直接测）；未标注对象的真实 FP |
| R4 口径 A 13 s 保持率 V/H（冻结算法） | AC-4 | 与 FAST-001 R4 同口径同序列对照：若 scout-1 从 40% 升到 ≥0.90（`TRAINED_ON_ATOM`）且 H ≥0.80，则「检不到」这一因在离线回放中已消除；若 H 仍低，则离线回放中的短板在关联层 | 在线可行性；真实指定期的保持率；「问题已定位」以外的归因 |
| R4b 口径 B `HIT` 比例、首次 `bound_track_removed` 时刻 | AC-4 | 只描述：一次绑定不改绑的插件在离线序列上能维持多久；这是 LOOP-001 换插件裁定要看的数字 | 任何门结论；在线表现 |
| R5 Mac 插件 p95（每设备） | AC-7 | 若每设备 ≤200 ms，则单进程离线 5 Hz 预算可达；否则退回 CPU/缩小 `imgsz` 另测 | 同机 Unity 负载；Jetson；Play 机实测 |
| R6 相对 NanoTrack 的可比读数 | AC-4 + FAST-001 R4 | 只能说「离线回放上关联层保持率的差」，且 NanoTrack 无同口径回放数据，本表**不**写「优于 NanoTrack」 | 任何换栈优劣结论——由用户按 LOOP-001 恢复裁定 |

## 7. 必经停点与提请裁定

- **`K3K4` 合并单候选**（engineering §4「相互关联的触发可合并」）：K4 = 三域划分、标签/ignore 规则、抽查处置、冻结点、对外指标与门；K3 = 插件的绑定/丢失/不改绑决策。一次 `C1@K3K4` → 新鲜上下文 `R1@K3K4`。不触发 K1/K2/K5。
- **不申请 `UNITY_NA`**（AR1-5）：完成门按 §3.8 两阶段；阶段 2 Unity 验证另签。
- **提请接受角色在 `ACCEPTED` 时裁定**：(a) §3.1 纳入状态、12 px 下限与 §3.1.3 ignore 规则；(b) §3.3/§3.4 门值与 `N_min`（可调，用户确认）；(c) K3K4 合并；(d) §3.1.1 三域划分（scout-1/m3-armA 进 T、a7 作 V）；(e) 插件落点（新模块 vs `trackers.py` 内）与 CLI 闭集扩项；(f) LOOP-001 换插件是否作为其 K3 候选（本角色读法：是）；(g) **待用户**：`det-assoc-v1` 是否只作局部备选（本稿）还是升级为替代 v0.3 §3「换目标不重训练」属性（本角色推荐：本项内维持局部备选，升级留待 LOOP-001 恢复裁定时一并决定）；(h) **待用户**：阶段 2 Unity 验证的授权来源——本项独立 1 次诊断 Play（推荐；不动 LOOP-001 余额）或复用 `diag-loopb-7`；(i) 阶段 1 Overall token 命名（§3.8 建议值）。
- **推进方式**：本项轮次由 supervisor 调度（账本 09-26）；§5 信封首签与 (g)(h) 归用户。

## 8. 只读试读数字（2026-09-26 本机只读；零训练、零模型推理）

| 项 | 数字 | 来源 |
|---|---|---|
| S3 帧 | 43,535（全部可用，151 分片；manifest sha 见 `splits.json` `inputs[0].sha256`，运行时解析） | FAST-001 缓存索引 |
| `OK` 车辆框 / 有框帧 | 57,430 / 31,352；S/M/L 5,011 / 22,659 / 29,760；深度 <35/35–50/50–65/≥65 m = 38,231 / 11,924 / 4,819 / 2,456 | 同上 |
| 目标车有框帧 | 15,963；S/M/L 1,840 / 9,055 / 5,068；逐族见事实 16 | 同上 |
| 三域（全部可用帧 / 目标有框帧 / 目标 S / 车辆框） | T 12,499 / 3,868 / 1,113 / 19,117；V 3,168 / 1,653 / 142 / 4,805；H 27,868 / 10,442 / 585 / 33,508（合计 43,535 ✓） | 事实 16 汇总 |
| 训练帧（抽帧 1/2 后估计） | ≈ 6,250（T 12,499 的一半；`rate`/`scene-val` 无目标车，只贡献车辆类）；加入 §3.1 非 `OK` 状态后框数将明显多于 19,117 | 推导 |
| 非 `OK` 可见车辆（前 40 分片 11,436 帧样本） | `EXCLUDED_OCCLUDED` 13,133、`TOO_SMALL` 4,490、`TRUNCATED` 1,472 vs `OK` 10,796 | 分片实读 |
| 仿真时间覆盖 | 15 族全部有 `catalog-sim-times` 行；survey 19,986、s004-scout 4,836、BODY 九段 1,152 | 事实 17 |
| 图像 | 640×480 jpg，本机 `runtime/` 下（抽样 400/400 存在）；无需 T7 | D1 |
| 单帧标签体积 | ≤ 12 行 × ~30 B；全集标签 < 5 MB | 推导 |
| 训练吞吐 / 帧间隔分布 | **未测 / 未算**；AC-2 第一步实测 1 epoch 定 epoch 数（§3.2）；子序列切分计数在 AC-4 报告 | — |
| 参照时延 | YOLOE-11s-seg p95 CPU 68 ms / MPS 30 ms（yolo11n 更轻，只作参照） | FAST-001 AC-10 |

## Contract conformance（核对表）

`C1@K3K4` 首次核对（2026-09-28）；候选 `git diff 8d8407c..1fc99f5`，包括本派发两个实现提交及其证据，基线 `8d8407c`。结论为**首次退回**，不是独立复核 verdict；本停点核对退回额度已用 1/1。已签八门中实现报告的 G-1、G-5、G-6 未过是候选读数；下述 AC-4 偏差使 G-5/G-6 尚不能当作合同口径的最终证据。核对轮不运行测试，也不改实现或 AC 条款。

| AC | 结论 | 核对理由与指针 |
|---|---|---|
| AC-1（Q-1/Q-2 修订） | 不满足 | 数据集重建、三域及 609 行断言、目标层重抽证据见 `docs/evidence/P1-ENG-FAST-002-dataset.json`、`-spotcheck.json`；但 Q-1 修订要求整帧排除帧不进任何评估分母，`tools/eng_det/qualify.py:_pieces` 把 scout-1 全部 T 行交回放，`tools/eng_det/evaluate.py:target_truth` 只将排除帧真值改为 None，仍送入关联器和窗口，见 AC-4。须区分“缺真值帧”与“整帧排除帧”。 |
| AC-2 | 满足 | `tools/eng_det/train.py:run` 的计时、run 与 last.pt 记录，`tools/eng_det/select.py` 的 V 门、conf/run/关联选择和 `-train.json`、`-freeze.json` 可对应 §3.2；IR-2 计时与主体训练同扣一个 run 且合计 13,276 s，在 6 h 内。 |
| AC-3（含修订） | 满足 | `tools/eng_det/evaluate.py:match_frame/evaluate/detection_gates` 及 `-recall.json` 分别给双 IoU、ignore、N_min 与 G-1…G-4；`-report.md`「逐门结论」列八门；这些检测门结论仍待独立复核。 |
| AC-4（含修订） | 不满足 | §3.4 逐字“每族…为一条序列”，`tools/eng_det/evaluate.py:sessions` 与 `tools/eng_det/qualify.py:_pieces` 改按帧目录会话分组；这会改变回放窗口集合及 G-5/G-6。scout-1 的 63 个 Q-1 排除帧继续送入回放并以 None 真值参与窗口；`tests/test_eng_det_qualify.py:SequenceTests` 只验证 None，不覆盖排除帧应不进评估的问题。`-replay.json` 的 0.815/0.788/0.411 因而暂不能证明合同口径。 |
| AC-5 | 满足 | `controller/det_assoc_tracker.py:init/update`、工厂/CLI diff 与 `tests.test_det_assoc_tracker` 对应绑定阈值、一次初始化、lost/rebind、规格校验及显式选择。 |
| AC-6 | 满足 | `tests.test_det_assoc_carrier` 从首个 update 起与 `-replay.json` `carrier_reference` 比较；初始化帧单验 placeholder，与 AR2-2 接受释义相符。 |
| AC-7 | 满足 | `-latency.json` 的 Mac CPU/MPS 各 320 帧、p95 48.4/31.9 ms、框差记录对应 G-7；尚待复核重读。 |
| AC-8 | 满足 | `controller/det_assoc_tracker.py` 未导入离线真值工具，`tools/eng_det/dataset.py:truth_visibility_flag` 与 `evaluate.py:target_slant_m` 只在离线链路，见 `tests.test_det_assoc_tracker.TruthIsolation`。 |
| AC-9 | 满足 | `-ledger.json` 记下载 1、训练 1、H 评估 1、模型启动 13、runtime 双树前后同哈希；`git diff 8d8407c..1fc99f5` 无 runtime/ 写入。 |
| AC-10 | 证据缺失 | `-report.md` 有 §6.2/§6.3 和限制栏，但其中 G-5/G-6 与关联归因依赖 AC-4 的偏离回放；须按获裁定口径更正或明确撤销这些读数后才能证明逐格报告义务。 |
| AC-11 | 满足 | `-report.md`「LOOP-001 换插件备忘」逐条列合同接口与身份差异；候选 diff 未改 LOOP-001 提案、状态或余额。 |
| AC-12 | 满足 | 阶段 2 尚未到前提，状态板及 `-report.md` 均记 `NOT_RUN`、不申请 Play、不得 `DONE`；本行不表示 Unity 验证通过。 |
| AC-13 | 满足 | `tools/eng_det/qualify.py:FreezeGuard`、`-freeze.json`、`-ledger.json` 显示先冻结后 H 1/1，训练 run 结束早于冻结；第二次 `run` 的拒绝路径有具名测试。 |

**IR-2…11 的合同读法裁定（只解释，不增改 AC）**：IR-2 同一 run 计时、保守墙钟；IR-3 填充后还原正样本重叠像素；IR-5 规格/冻结文件以规格核心 sha 断循环；IR-6 演示路线限 scout-1、M3 arm A/B；IR-7 加严 H 保留帧断言；IR-8 类别无关匹配、NMS 0.7、两类均关联；IR-9 目标有斜距处单列斜距而无距离记 NA；IR-10 时延包含预热；IR-11 载体测试插件实例逐次记模型启动——均可按已签条款及当前证据读，不改变门值、信封或范围。**IR-4 不予核准为纯解释**：按会话替代按族改变 §3.4 序列与窗口；排除帧入回放又与 Q-1 冲突。前者需用户确定合同口径，后者交实现修正；不得用本节口头认可更改合同或从 H 再试数。

**预复核关注项**（交下一候选及独立复核核实；不在此分级）：`tools/eng_det/evaluate.py:split_subsequences` 的中位间隔折算 13 s + buffer 帧应与 §3.4 的短段剔除同义；`tools/eng_det/train.py:filled_image` 的正样本重叠还原是否确实未破坏 ignore 区，核对本批训练副本与账本；`tools/eng_det/qualify.py:run` 与 `tools/eng_det/select.py:freeze` 的 H 只评一次与互引哈希；候选中 `docs/evidence/supervisor-dispatch.jsonl` 两行派发登记也在完整 diff 内，复核范围不能漏掉其来源边界。

**返回差异**：先取得按族/按会话口径的用户裁定；实现角色依裁定对 AC-4 的序列、Q-1 排除帧及相关测试/报告作定向修正，不动冻结模型/参数、不重新推理或训练。若修正需重新计算已产出的 H 窗口或读数，必须先取得用户关于已缓存 H 检测重评分的明确授权；无授权不得绕过 `h_evaluations=1`。修复候选回同停点 `C1@K3K4` 第二次核对，届时即使未满足也照交复核并附本表关注项。

**需用户决定（本轮不得代选）**：

1. **IR-4 序列单位**：推荐准许把 §3.4 的“每族一条”明确修订为“每会话一条、族内多会话合并窗口”，理由是 M3 arm A/B 多 trial 仿真时刻重叠，按族拼接会混合不连续轨迹；此项改变采样/门口径，须先改合同再更正证据。无论如何，Q-1 排除帧不进评估仍须实现修正。
2. **已缓存 H 检测的评分更正**：若 IR-4/Q-1 修复须重算 H 窗口或复核发现评分代码缺陷，推荐只允许对冻结权重、冻结阈值与已缓存 H 检测作一次具名勘误式重评分，留存旧读数与差异；禁止新推理、改冻结、改帧集或据 H 选参。理由是当前合同 H 只评一次且 `h_evaluations=1/1`，即使不重推理，再评分也超出现有一次性授权；没有用户逐字许可不得执行。
3. **复核后的 §6.2 分支**：仅登记到 `R1@K3K4` 之后再问。推荐 (i) 仅作“目标 M 层以上/训练过的演示几何”范围声明并进入 LOOP-001 换插件裁定，理由是无需本项新增训练或 H 消耗；G-1/G-5/G-6 未过及口径 B 低保持率必须同时交用户，不据此放行本项阶段 2 Play 或宣称改善。选 (ii)/(iii) 均需另定合同或信封。

**Overall 时点**：用户已签八门合取的 `QUALIFICATION_GATE_NOT_MET` 映射；当前 Gate board `ACCEPTED` 先保持，因为 §3.8 阶段 1 包含 C1 与独立 R1，且 AC-4 口径尚未闭合。R1 核实后由接受角色消费逐门结论并写该 token；不因实现报告建议在独立复核前冒充阶段 1 收束，也不写 `DONE`。

## 决策记录

| 日期 | 事项 | 结论 | 依据 |
|---|---|---|---|
| 2026-09-26 | 用户裁定快层方向 | 快层换成熟方案；三路线选「1. 在域微调 YOLO + ByteTrack」；本项由 supervisor 调度推进、构思只出想法；LOOP-001 继续暂停，其二选一顺延到本项结论后 | 账本同日「用户裁定：快层换成熟方案（在域微调 YOLO + ByteTrack）…」逐字 |
| 2026-09-26 | D1 落盘（构思） | engineering-v1 申请；AC-1…11；停点 K3K4 合并；申请 `UNITY_NA`；§5 线 A/B 申请值；构思侧假设：红立方体不换、Unity 零改动、两类检测器（vehicle/target）、held-out = test 原子、门值预注册可调 | D1 §0–§8 |
| 2026-09-26 | D1 接受裁定 | `REVISION_REQUESTED`（第一次）；AR1-1…6；engineering-v1 未裁定生效 | 下节「D1 接受裁定」 |
| 2026-09-26 | D2 落盘（构思，supervisor 派发 Fable 子代理） | `PROPOSED`（回应 AR1-1…6）：三域 T/V/H 与冻结点、H 只评一次（AC-13）；分层抽查与 ignore/FP 可复算定义；三种身份口径分列、`init` 恰调用关联器一次；`N_min` 与逐门判定规则、双设备时延、门未过分支；撤回 `UNITY_NA`，两阶段完成门（AC-12）、局部备选不取代 v0.3 §3 属性；删除固定 HEAD/SHA、§5 签发前为 0。零实现、零训练、零下载/启动/传输/Play | 头部「AR1 → 本稿映射」；§0 事实 15–17；§3.1.1–3.1.3、§3.2、§3.4.1、§3.8、§4 AC-12/13、§5–§7 |
| 2026-09-26 | D2 接受裁定 | `REVISION_REQUESTED`（第二次）；AR2-1…3 未闭；engineering-v1 申请未生效；退修上限后的二选一交 supervisor D1 仅代选 (a) | 下节「D2 接受裁定」 |
| 2026-09-27 | D2 用户选 (a) 后的接受处置 | `ACCEPTED` 当前范围；AR2-1/2 的执行释义固定，AR2-3 的用户保留项保持未闭；engineering-v1 裁定生效；实现与消耗待用户条件 | 下节「用户选 (a) 后的接受处置」；账本 2026-09-26「用户处置第二次设计退修」 |

### D1 接受裁定（2026-09-26）

**REVISION_REQUESTED**。方向层用户授权支持起草本项，但下列合同冲突使 AC-1…11、G-1…G-7 与完成门尚不能冻结。`Workflow: engineering-v1` 保持申请，尚未裁定生效；`K3K4` 合并原则上可行，须在 D2 修正后裁定。零实现、训练、下载、Play 与 ID；§5 申请值不构成执行信封。退回构思角色 D2，逐项回应：

| ID | D2 必须修正 | D1 依据 |
|---|---|---|
| AR1-1 | 把训练次数、模型/算法/参数与插件 conf 的**选择规则**全部锁在 train/dev 侧；明确最终一次 held-out 评估的候选冻结点。现 §3.2 按 G-3 held-out 结果从 0.25 改选 0.40、§6.2 按 held-out 门失败启动 run-2，均以 test 指导选择；若保留探索性重训，须另列未触碰的最终评估域或把该域结果降为探索性，不能继续称独立 held-out 合格判定。相应改 AC-2…4、AC-10。 | §3.1 划分、§3.2「不按 held-out 选」、§3.3 G-3、§6.2 run-2 分支；工程继承清单「train/dev/test、pHash/对象谱系」行。 |
| AR1-2 | 为 §3.1 派生标签加入按类别、状态、短边和来源族分层的图像语义抽查与错误处置，原始 S3 不覆盖；把 ≥12 px 纳入集以外的可见对象、未核实/缺框对象如何作为 ignore 或 FP 分母处理写成可执行规则。修正「故是真 FP」断言，并给 G-3 的 FP/帧可复算定义及测试反例。 | §3.1 仅以状态/框字段作标签、§3.3 FP 断言、§6.1「UNVERIFIED」；engineering §7；工程继承清单「S5 人工审计尚未完成」。 |
| AR1-3 | 统一 §3.4 回放、§3.5 插件与 §3.6/AC-6 的身份比较口径。现 `tools/eng_fast/replay.py:bind` 每帧用真值框以 IoU≥0.30 重绑定，插件仅初始化帧用用户框以 IoU≥0.50 绑定且不自动改绑；因此「载体绑定框与回放绑定逐帧一致」不能作合同断言。改为同一初始化框、同一逐帧输出与冻结身份语义的比较，真值只进入离线评分；写明初始化帧只调用关联器一次。 | `tools/eng_fast/replay.py:bind/window_outcome`、`controller/track_loop.py:initialize` 与处理循环；§3.4–3.6、AC-5/6。 |
| AR1-4 | 将 G-1…G-7 的零分母/无适用段、逐格还是合并判定、同一阈值下判定、CPU/MPS 时延要求和门未过时的 Overall/交接写成确定规则；缺数据不得算 `MET`。对 §6.3 的「持续检测」「关联问题已定位」等推论收紧到对应离线证据。 | §3.3/§3.4 各门、AC-3/4/7、§6.3；FAST-001 报告「读数表」只支持离线描述。 |
| AR1-5 | 重写 `UNITY_NA` 与设计属性边界：本项注册可在 `TrackLoop` 显式选用的运行时插件，会改变 Unity 运行行为，不能仅凭缺省不变认作纯离线。若保持插件交付，列出独立复核后用户 Unity 验证的完成门，并把当前零 Play 信封与后续另签授权分开；不得在未验证时标 `DONE`。说明本场景专用检测器是局部备选还是取代 v0.3 §3「换目标不重训练」属性；后一种需用户明确裁定后才同步正式设计。 | workflow §3/§4.5、engineering §11；设计 v0.3 §3；§1、§2.1 D4、§6.1、§7。 |
| AR1-6 | 删除本 D1 手维护叙述里的固定 HEAD、工件 SHA 和可派生 run 目录标识，改成来源文件/运行时解析指针；明确 §5 两线申请值在用户逐字签发前均为 0。 | AGENTS.md「可派生标识禁手写」「授权信封」；§0 引言/事实 9、§8、§5。 |

**用户待定（本轮不代拍）**：若 D2 仍要求以本场景专用检测器取代 v0.3 §3 的目标无关工程属性，推荐用户明确批准该设计边界；理由是 09-26 方向授权选了训练路线，但未逐字裁定正式设计属性的废止。D2 可先把它限定为局部备选，待用户裁定是否升级为替代。执行信封须 D2 获 `ACCEPTED` 后由用户另签。

open_items: AR1-1,AR1-2,AR1-3,AR1-4,AR1-5,AR1-6

### D2 接受裁定（2026-09-26）

**REVISION_REQUESTED（第二次）**。AR1-1、AR1-6 已按 §3.1.1/§3.2/AC-13 与 §0/§5/§8 收束；AR1-2、AR1-3、AR1-4/5 仍有下表所列可证伪合同缺口。D2 的 T/V/H 隔离、只在 V 选参、H 一次评估、三种身份口径、`UNITY_NA` 撤回及局部备选边界原则上可用；用户已裁定局部备选（授权账本 2026-09-26 同名条目）。§7 (a)–(f)(i) 与 `Workflow: engineering-v1` **尚未接受裁定生效**；K3K4 可合并的判断维持为有条件。零实现、训练、下载、传输、Play、ID 与 API；§5 仍是申请值。

| ID | 仍须处置的合同缺口 | 依据与所需结果 |
|---|---|---|
| AR2-1 | §3.1.2 的非空分层按每层最多 8 框抽样，同时设总上限 300 框，但未规定非空层数导致超过 300 时的分配/截断顺序；`STRATUM_IGNORED` 又按各层错误率判定。 | 明确可复现的抽样与超额规则，保证每个参与错误率裁定的非空层有可计算分母，或明确不可评估层的保守处置；同步 AC-1。属于 AR1-2 残留。 |
| AR2-2 | §3.4.1 口径 C/§3.6/AC-6 要求载体与口径 B 逐帧 `(state, box, reason)` 完全相同，但真实 `TrackLoop.initialize()` 对初始化帧发布的是用户裁剪框、`placeholder` 结果；`TrackerPlugin.init()` 只返回 bool，不能取得插件所绑定的检测框。口径 B 的首次可见帧使用真值框作用户框替身，不意味着插件输出与载体初始化观测相同。 | 指定比较从首个 `update` 帧开始，初始化帧另按载体真实输出检查；或给出不改现有主循环/协议即可同值的明确实现合同与反例。同步 AC-6。属于 AR1-3 残留；依据 `controller/track_loop.py:initialize`、`controller/trackers.py:TrackerPlugin`。 |
| AR2-3 | §3.3 单列 G-1s，却在 AC-3 与 §6.2 的「G-1…G-4」处未说明是否计入；§3.8 阶段 1 的「门全过」与 §6.2 G-7 未过仅报告的处置不一致。AC-12/§3.8 只要求记录 Unity 可见期 `TRACKING` 帧占比，没有通过阈值、失败/无可见帧读法，却以「AC-12 通过」作为 `DONE` 条件。 | 列出阶段 1 逐门合取、G-1s/G-7/`NOT_EVALUABLE` 对 Overall 与下一交接的确定映射；定义 AC-12 的通过、失败、不可评估条件及证据，门值须由用户确认后冻结。属于 AR1-4/5 残留。 |

按 workflow §4.2，本轮是第二次退修，不自行发第三次。D1 决策信封在效且本轮具名残留 3 < D1 的 6，交 supervisor 仅可代选 (a)「接受当前范围并逐条列出已知缺口」，每轮至多一次；若不代选，则交用户在 (a) 与 (b)「关闭为负结果记录」间裁定。supervisor 不得代签或代定 §5 信封、G 门值/AC-12 通过阈值、§7 (h) 阶段 2 Unity 授权来源或轨道/设计边界。推荐用户维持 §7 (g) 已签的局部备选、确认阶段 1 各门与阶段 2 AC-12 门值，并为阶段 2 单独签本项 Play 授权而不动暂停的 LOOP-001 `diag-loopb-7`；§5 线 A/B 在 `ACCEPTED` 后另签。无用户授权前保持零消耗。

open_items: AR2-1,AR2-2,AR2-3

### 用户选 (a) 后的接受处置（2026-09-27）

**ACCEPTED（当前范围，非完成/执行授权）**。用户在账本 2026-09-26「P1-ENG-FAST-002 — 用户处置第二次设计退修」逐字选「选a」；按 workflow §4.2(a) 保留当前交付范围并接受其已知缺口。提案头部 `Workflow: engineering-v1` 的申请由本接受角色裁定**生效**：目的、范围、接口、AC-1…13、§5 申请信封与限制构成工程任务合同，`K3K4` 合并为一个必经候选，先 `C1@K3K4` 后独立 `R1@K3K4`；K1/K2/K5 未由本范围触发。局部备选定位依用户 2026-09-26 已记录裁定，v0.3 §3 的换目标不重训练属性、LOOP-001 合同与余额不变。本节为接受时的 binding clarifications；遇到与前文的冲突，以本节明确的 AC 对应释义为准，不由实现角色自行补全。

| 已知缺口 | 接受处置及对应验收项 | 可核对依据 |
|---|---|---|
| AR2-1 | **AC-1 释义**：§3.1.2 的 300 框为硬上限。以该节类别、状态、短边档、族组组成的非空层为闭集；每框按 `SHA256("20260926|" + 层键 + "|" + 帧 sha + "|" + object_id)` 升序排序。按层键字典序逐层各取第一框，再按相同层序逐轮各取下一框，直到 300 框或每层 8 框均取完；每层不得重复框。每个非空层至少取得一框，记录其候选数、抽中数和层键；实际抽中数 `n≥1` 才计算该层 (`WRONG`+`INVISIBLE`)/n，按原 §3.1.2 的 >20%、10–20% 规则处置，并将触发 `STRATUM_IGNORED` 的类别×状态×短边档跨族组 ignore。若实际非空层数 >300 或某层无法取得一框，抽查判为 `NOT_EVALUABLE`，训练不得开始，交用户裁定；不得跳层或默认为通过。另行每族组 10 帧整帧抽查仍按原条款。 | artifact:`docs/evidence/P1-ENG-FAST-002-spotcheck.json` 的层清单、顺序、n、判定；test:`tests.test_eng_det_dataset` 覆盖超过 300 框、每层至少一框与不可评估路径。 |
| AR2-2 | **AC-6 释义**：口径 B 与口径 C 使用同一帧序及同一个初始化用户框；初始化帧单独验证 `TrackLoop.initialize()` 发布该用户框的 placeholder 观测、插件 `init` 的 bool 结果、关联器只调用一次且库 `frame_id=1`。逐帧 `(state, box, reason)` 相等的比较范围从**第一个 `update` 帧**开始，到该子序列末帧；初始化帧不拿插件所绑定检测框与载体用户框比较。口径 B 的真值只用于离线构造用户框替身及评分，不进入口径 C 的运行时输入。`init=False` 路径另验载体既有初始化失败行为。 | test:`tests.test_det_assoc_carrier` 覆盖初始化观测、首个 update 起逐帧相等及 `init=False`；artifact:`docs/evidence/P1-ENG-FAST-002-replay.json` 记录共用初始化帧/框。 |
| AR2-3 | **AC-3/4/7/12 与 §3.8 的待用户条件**：阶段 1 建议合取 G-1、G-1s、G-2、G-3、G-4、G-5、G-6、G-7；任一 `GATE_NOT_MET` 或 `NOT_EVALUABLE` 均不得写 `IMPLEMENTED_REVIEWED_AWAITING_UNITY`，须记录逐门结论、限制与下一交接，且不得以 `DONE` 收束。此建议连同 §3.3/§3.4 的各门数值及 `N_min` 交用户确认后方可冻结，不能以本次 `ACCEPTED` 视作用户确认。AC-12 的可见期 `TRACKING` 占比阈值、无可见帧/缺失证据的不可评估读法、异常退出及 Play p95 的通过条件均待用户逐项确定；在这些条件未确定及 §7(h) Unity 授权来源未签前，AC-12 只表示应记录的字段，不能判 `PASS`。§3.8 的阶段 1 token 与失败/不可评估映射也待用户裁定；阶段 1 即使复核通过仍不得写 `DONE`。 | artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「逐门结论」与用户后续账本裁定；artifact:`docs/unity-test-log.md` `UT-FAST-002-1`（获授权后）。 |

**执行边界**：§5 线 A/B 均是申请值；用户逐字选线、签明各维度前全部为 0，不进行训练、下载、安装、传输、模型启动、H 评估、Play 或创建 ID。阶段 2 推荐本项独立 1 次诊断 Play 信封，不借 `P1-ENG-LOOP-001` 暂停余额；§7(h) 最终来源仍由用户定。阶段 1 门、AC-12 通过条件与 §5 信封未签时，交用户裁定，收到后由接受角色在合同「待裁定」节按工程轨道追加对应 `AC-n 修订`，不覆写旧行；实现角色之后才按签发范围行动。本裁定无新研究主张、无 `UNITY_NA`、无 Unity 或复核通过结论。

open_items: AR2-3,USER_STAGE1_GATES,USER_AC12_PASS,USER_UNITY_SOURCE,USER_EXECUTION_ENVELOPE

### 待裁定：用户授权后的 AC-n 合同补齐（CLARIFY，2026-09-27）

本节只解释已接受的 AC-3/4/7/9/12 与 §3.8、§5、§7(h)，不追加 D 轮，也不追改上方 D2 当时的裁定。授权来源是 `docs/authorizations.md` 2026-09-27「P1-ENG-FAST-002 — 用户按推荐确认阶段 1 门值与合取映射、AC-12 通过条件四条、§7(h) 本项独立 1 次诊断 Play，并选签 §5 线 A」；同日「初步采用现有评测数值作为首版目标」只说明此前意向，以前一条逐项确认及信封为准。以下每行沿用原 AC 编号，标签 `CLARIFY`。

| 编号 | 合同修订（CLARIFY） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-3 | `CLARIFY`：冻结 §3.3 的 G-1 `target` M、L 召回 @IoU 0.5 各 ≥0.90；G-1s `target` S（≥12 px）召回 @IoU 0.5 ≥0.70；G-2 `vehicle` M、L 召回 @IoU 0.5 各 ≥0.90，S ≥0.70；G-3 冻结 conf 下 FP/帧 ≤0.50；G-4 表 B 两个指定深度格召回 @IoU 0.3 各 ≥0.80。`N_min`：召回每格 ≥50 个正样本、FP/帧 ≥300 帧；不足者不得 `MET`。H 结果后不得追调。 | artifact:`docs/evidence/P1-ENG-FAST-002-recall.json`；artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「逐门结论」 | K3K4 | 2026-09-27 |
| AC-4 | `CLARIFY`：冻结 §3.4 的口径 A G-5 两格 13 s 保持率各 ≥0.90、G-6 H 合并格 13 s 保持率 ≥0.80；每个判门保持率格 `N_min` ≥30 个已判定窗口，不足者不得 `MET`。口径 B 的 `HIT` 比例与首次 `bound_track_removed` 仍只描述，不设门值；是否另设门值待用户裁定，不得由实现者推定。 | artifact:`docs/evidence/P1-ENG-FAST-002-replay.json`；artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「逐门结论」 | K3K4 | 2026-09-27 |
| AC-7 | `CLARIFY`：G-7 每个已测设备插件 `update` p95 ≤200 ms；设备不可用按原 AC-7 记 `N/A(DEVICE_UNAVAILABLE)`，不算该设备失败。现有 AC-7 明列 Mac CPU 与可用时 MPS 的采样要求；是否还纳入其他实际使用设备判门，用户未裁定，不得自行扩大或以此宣称设备范围已闭合。 | artifact:`docs/evidence/P1-ENG-FAST-002-latency.json`；artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「逐门结论」 | K3K4 | 2026-09-27 |
| AC-3 | `CLARIFY`（关联 AC-4/7）：阶段 1 判门闭集为 G-1、G-1s、G-2、G-3、G-4、G-5、G-6、G-7 八门合取；仅八门逐一 `MET` 且 `C1@K3K4`、独立 `R1@K3K4` 通过，才可写 `IMPLEMENTED_REVIEWED_AWAITING_UNITY`。任一门 `GATE_NOT_MET` 或 `NOT_EVALUABLE`，不得写该 token 或 `DONE`；逐门记录结果、限制及下一交接，采用 `QUALIFICATION_GATE_NOT_MET` 记录未达资格（报告中保留失败与不可评估的原始区别）。阶段 1 即使全过也不得写 `DONE`。 | artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「逐门结论」；artifact:`docs/reviews/P1-ENG-FAST-002.md` | K3K4 | 2026-09-27 |
| AC-12 | `CLARIFY`：阶段 2 `UT-FAST-002-1` 仍须记录插件 manifest 载入；通过条件四条为：(i) 目标肉眼可见期间 `TRACKING` 帧占比 ≥0.80；(ii) 无可见帧或证据缺失记 `NOT_EVALUABLE`，不得算通过；(iii) 任何异常退出判失败；(iv) Play 机时延 p95 ≤200 ms。四条全满足且 manifest 载入证据齐全，才可判 AC-12 通过；否则不得 `DONE`。 | artifact:`docs/unity-test-log.md`「UT-FAST-002-1」 | 阶段 2 | 2026-09-27 |
| AC-12 | `CLARIFY`（关联 AC-9）：§7(h) 来源已确定为本项独立 1 次诊断 Play：阶段 1 八门全过且 `R1@K3K4` PASS 后，由用户在 LOOP-001 演示路线以 `--tracker det-assoc-v1` 执行 ≤90 s；不借 `P1-ENG-LOOP-001` 的 `diag-loopb-7`。阶段 2 仅 Play=1，scenario/session/run ID=0，需 ID 时先回用户；本阶段不提前消耗。 | artifact:`docs/authorizations.md`「2026-09-27 P1-ENG-FAST-002 — 用户按推荐确认阶段 1 门值与合取映射、AC-12 通过条件四条、§7(h) 本项独立 1 次诊断 Play，并选签 §5 线 A」；artifact:`docs/unity-test-log.md`「UT-FAST-002-1」 | 阶段 2 | 2026-09-27 |
| AC-9 | `CLARIFY`（关联 AC-2/13）：§5 阶段 1 选签线 A，设备 Mac `.venv-yoloe`，线 B 未签。下载 ≤1 次（官方 `yolo11n.pt` ≈5.6 MB；T7 副本 sha 与官方公布值一致则为 0）；训练 ≤3 次、每次墙钟 ≤6 h、合计 ≤14 h；传输 0；评估/回放模型启动不限次但逐次记账，H 评估恰 1 次；`outputs/eng-det/` ≤5 GB；Play、scenario/session/run ID、API、云 GPU·h 均为 0。成功、失败、重试同扣上限，耗尽即停；第 4 次训练、较大模型、云端或第 2 次 H 评估先回用户。LOOP-001 阶段 B 与 FAST-001 §5 余额不转用。 | artifact:`docs/authorizations.md`「2026-09-27 P1-ENG-FAST-002 — 用户按推荐确认阶段 1 门值与合取映射、AC-12 通过条件四条、§7(h) 本项独立 1 次诊断 Play，并选签 §5 线 A」；artifact:`docs/evidence/P1-ENG-FAST-002-ledger.json` | K3K4 | 2026-09-27 |
| AC-4 | `CLARIFY`（解释 AC-4 及本节前一 AC-4 行）：依 `docs/authorizations.md` 2026-09-27「用户按推荐：口径 B 维持描述性读数不设判门；设备判门范围限 AC-7 已列 Mac CPU 与可用 MPS」，口径 B 的 `HIT` 比例、首次 `bound_track_removed` 时刻及 `DRIFT` 只作描述性读数，不设门、不进入阶段 1 八门合取；本节前一 AC-4 行的「是否另设门值待用户裁定」义务已核销。 | artifact:`docs/evidence/P1-ENG-FAST-002-replay.json`；artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「逐门结论」 | K3K4 | 2026-09-27 |
| AC-7 | `CLARIFY`（解释 AC-7 及本节前一 AC-7 行）：同一账本授权将 G-7 判门设备闭集限定为 Mac CPU 与可用时的 MPS，各按原 AC-7 ≥300 帧及 p95 ≤200 ms；MPS 不可用记 `N/A(DEVICE_UNAVAILABLE)`，不影响 CPU 判定。其他设备不判 G-7 门，本节前一 AC-7 行的设备范围未闭义务已核销；不据此推断其他设备性能。 | artifact:`docs/evidence/P1-ENG-FAST-002-latency.json`；artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「逐门结论」 | K3K4 | 2026-09-27 |

**已核销**：口径 B 不设门；G-7 设备范围仅 Mac CPU 与可用 MPS。Q-1/Q-2 已由用户在 2026-09-28 选 (a)，对应合同修订见下节；阶段 1 线 A 信封和阶段 2 前置门不变。

### 待裁定：K3K4 抽查后 Q-1/Q-2 的接受处置（CLARIFY，2026-09-27）

依据 `docs/evidence/P1-ENG-FAST-002-K3K4-handoff.md`「抽查结果」「待裁定」及 `docs/evidence/P1-ENG-FAST-002-spotcheck.json`。本表保留 2026-09-27 的权限与选项记录；2026-09-28 用户选定两项 (a)，执行口径以下方 AC-n `CLARIFY` 修订为准。旧合同下 AC-1 的 §3.1.2 跨族组处置使目标 S 层整层 ignore，H 该格正样本 0；按已签 AC-3 八门合取，G-1s 为 `NOT_EVALUABLE`，不得以训练后的 M/L 读数冒充阶段 1 通过。

| 问题 | 接受裁定及用户选项 | 理由与边界 |
|---|---|---|
| Q-1（AC-1/3） | **用户已选 (a)**：将 `target_unbounded=true` 帧新增为整帧排除，训练与评估分母均剔除并逐域计数；重建后重新核对三域及「609 行评估帧 ⊂ H」断言，若不成立再停下，不静默删改该断言。 | 现 §3.1 整帧排除只覆盖 `wildcard_reason` 等有边界失败，未覆盖 `target_unbounded`；抽查的 rate/scene-val/s004 可见红立方体却无目标框。该项改变 T/H 帧集、训练样本与 G-3 分母，授权见下方账本指针。 |
| Q-2（AC-1/3） | **用户已选 (a)**：仅在已有逐帧真值可见性标志的演示路线派生离线标签中，将标为不可见的目标框转 ignore，按 AR2-1 原算法在训练前重抽目标层一次并按新结果处置；无标志的会话沿现规则，不以示例三框预判整层结果。 | B178/B264 为 `INVISIBLE` 且可见性标志 false，B003 为 `OK` 且 true。scout `target_visible`、BODY `geometrically_visible` 只从既有 Unity 真值 sidecar 进入离线派生标签、抽查和评分；Unity 侧真值生成仍由 `CoverageEvaluator` 边界承担，插件/控制器/感知输入/对外传感器元数据均不得接收该标志。若实现需要新增运行时真值通道，则不在本项授权内。 |

IR-1 仅登记：同层相同帧 sha 与 `object_id` 去重、保留最小 `frame_id`，是已接受 AR2-1「每层不得重复框」的现有实现读法；不形成新 AC。线 A 余额不变。

### Q-1/Q-2 用户选 (a) 后的 AC-n 合同修订（CLARIFY，2026-09-28）

授权来源：`docs/authorizations.md`「2026-09-28 P1-ENG-FAST-002 — 用户按推荐：Q-1 选 (a) 排除 `target_unbounded` 帧、Q-2 选 (a) 以离线真值可见性标志修正目标标签并重抽目标层；CLARIFY 派发核查 F3a 不退回（supervisor 会话代录）」。以下只追加对既有 AC-1/3/8 与 AR2-1、§3.1.3 的解释；原 AC 行、原始 S3、旧划分、门值、八门合取和线 A 信封不覆盖、不改写。

| 编号 | 合同修订（CLARIFY） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | `CLARIFY`（Q-1，解释 AC-1/§3.1/§3.1.1）：在既有整帧排除条件之外，`target_unbounded=true` 的帧整帧排除，不进入 T 训练图、V/H 评估或任何训练与评估分母；在 `-dataset.json` 按 T/V/H 逐域记录排除帧数及重建后保留帧数。先按此规则重建派生数据集，再重核 T∩H、V∩H、T∩V 的原断言和「609 行评估集帧 ⊂ H」原断言；任一不成立则训练前停下回报，不删改或放宽断言。 | artifact:`docs/evidence/P1-ENG-FAST-002-dataset.json`「domain_assertions」「summary」；test:`tests.test_eng_det_dataset`（`target_unbounded` 整帧排除、逐域计数及断言失败拒绝） | K3K4 | 2026-09-28 |
| AC-1 | `CLARIFY`（Q-2，解释 AC-1/AR2-1/§3.1.2/§3.1.3）：仅对已有逐帧真值可见性标志的演示路线会话，在派生离线标签中将标志为 false 的目标框转 ignore；scout 取既有 `target_visible`，BODY 取既有 `geometrically_visible`。该框按 §3.1.3 既有 ignore 训练填充与评估 IoA 过滤规则处理，不再作为正样本或目标层抽样候选；未提供该标志的会话沿原标签规则。完成 Q-1 重建与此标签修订后、任何训练前，仅对目标层按 AR2-1 已签的层键、排序、轮取上限、判定阈值与跨族组处置算法重抽一次，记录新候选数、抽中框、判定及处置；车辆层不因本项重抽，不用旧抽查结果或示例三框预判新层结论。 | artifact:`docs/evidence/P1-ENG-FAST-002-dataset.json`、`-spotcheck.json`；test:`tests.test_eng_det_dataset`（有标志 false → ignore、无标志 → 原规则、目标层重抽与 AR2-1 处置） | K3K4 | 2026-09-28 |
| AC-3 | `CLARIFY`（Q-1/Q-2，解释 AC-3/§3.1.3/§3.3）：G-3 的 FP 总数和帧分母仅取重建后保留的评估帧；G-1/G-1s/G-2/G-4 的正样本与 ignore 集按修订后的派生标签和目标层重抽处置重算。保留冻结 conf、原 `N_min`、门值、三态判定与阶段 1 八门合取；任何格不足 `N_min` 仍记 `N/A(INSUFFICIENT_N)`，不得以旧目标层结果或 M/L 读数替代 G-1s。 | artifact:`docs/evidence/P1-ENG-FAST-002-recall.json`、`-report.md`「逐门结论」；test:`tests.test_eng_det_qualify`（排除帧不计 FP/分母、ignore 不计正样本或 FP、样本不足不得 `MET`） | K3K4 | 2026-09-28 |
| AC-8 | `CLARIFY`（Q-2，解释 AC-8）：`target_visible` 与 `geometrically_visible` 只可从既有 Unity 真值 sidecar 进入离线派生标签、抽查与评分；不进入插件、控制器、感知输入或对外传感器元数据，不新增 Unity 运行时真值通道。若实现需新增运行时真值通道，停下回报，超出本项授权。 | test:`tests.test_det_assoc_tracker.TruthIsolation`；artifact:`docs/evidence/P1-ENG-FAST-002-report.md`「真值隔离」 | K3K4 | 2026-09-28 |

执行次序：按 AC-1 重建并核对断言，再重抽目标层并按新结果处置，随后才可按已签线 A 信封推进训练及 `K3K4`；下载、模型启动、H 评估及 Play 仍各受原信封与阶段门约束，不因本次修订新增额度。

### 阶段 1 收口裁定（2026-09-28；用户已裁定）

依据 `docs/authorizations.md` 2026-09-28「全局 — 用户按推荐入账：主线目标锚定…」D.4 及 2026-09-27「用户按推荐确认阶段 1 门值与合取映射…」第 2、4 项，本项阶段 1 **收为描述性结果**，Overall 记 `QUALIFICATION_GATE_NOT_MET`、Lifecycle 记 `ENDED`。这只表示原范围停止，**不是**资格复核通过、插件代码通过、Unity 验证或 `DONE`；不产生快层替换优劣、在线保持率或 Jetson 性能主张。冻结门值及八门合取不追调，也不新设门。

`docs/evidence/P1-ENG-FAST-002-report.md`「逐门结论」原样列 G-1、G-5、G-6 为 `GATE_NOT_MET`，G-1s、G-2、G-3、G-4、G-7 为 `MET`，无 `NOT_EVALUABLE`；其中 G-1 的 H target M/L = 0.987/0.731，G-5 的 scout-1/m3-armA = 0.815/0.788，G-6 的 H 合并 = 0.411。按已签 AR2-3/AC-3 映射，只要一门未过便不得写 `IMPLEMENTED_REVIEWED_AWAITING_UNITY` 或 `DONE`。以上是实现者报告的**未独立复核读数**；`C1@K3K4` 首次核对已退回，不能把报告的逐门标签当成合同口径经核实的最终判门。

**AC-4 偏差声明**：`C1@K3K4` 核对表指出 IR-4 将 §3.4「每族一条序列」改为按帧目录会话分组，改变窗口集合；Q-1 的 scout-1 共 63 个整帧排除帧仍以空真值送进关联回放和窗口，与「整帧排除不进任何评估分母」冲突。报告中 G-5/G-6 的 0.815/0.788/0.411 及相关口径 A/B 读数均按报告原样保留，仅供描述，**不能证明原 AC-4 的 G-5/G-6 合同判门**。不修 IR-4、不重评分或重推理 H、不改冻结权重与参数、不开 `R1@K3K4`。原核对表「返回差异」「待用户裁定」及「Overall 时点」记录的是当时待处理路径，现由本节用户处置取代，不再派发本项返工或复核。

**承接与复用**：插件 `controller/det_assoc_tracker.py` 及其工厂/CLI 接入的代码复核，交未来 `P1-ENG-ACQ-001` 的 K3；该新项尚无提案与 Gate 行，本节只记承接去向，不预签其合同、复核或额度。检测器冻结权重指针见 `docs/evidence/P1-ENG-FAST-002-freeze.json` 的 `weights.path`（本机 `outputs/eng-det/runs/run-1/weights/last.pt`），数据集工具为 `tools/eng_det/`，派生数据索引为 `outputs/eng-det/dataset/index.jsonl.gz`，检测缓存为 `outputs/eng-det/dets/`；来源和限制分别见 `docs/evidence/P1-ENG-FAST-002-{train,dataset,freeze,ledger}.json` 与同名报告「限制与不承诺」。这些 `outputs/` 资产不入库；新项复用前须核实本机文件、来源、散列及上述偏差，旧 H 回放读数不作为新项资格证据。§7(h) 本项独立诊断 Play 以阶段 1 八门全过且 `R1@K3K4` PASS 为前提，现已不可能满足，**不再使用**；本项剩余额度不转给 `P1-ENG-ACQ-001`、`P1-ENG-LOOP-001` 或其他工作项。阶段 2 AC-12 未运行，Unity `NOT_RUN`。
