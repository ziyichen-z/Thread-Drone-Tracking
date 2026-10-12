# P1-ENG-FAST-001 — 快层替换探针：预训练检测器分桶召回、检测+关联序列回放、VLM 四臂对照、与 DETECT-001 的关系（全离线，零 Play）

Status: ACCEPTED（D3，2026-09-24；接受角色裁定 `Workflow: engineering-v1` 生效；设计退修 2、C/R 1/1；§5 执行信封已于 2026-09-24 由用户逐字授权；R1@K4 PASS 已由接受角色消费，工作项 DONE 见 `docs/implementation-status.md` 同名收尾节）
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（Claude Code `/fable`，Fable 池）
Created: 2026-09-23
Last updated: 2026-09-26

> **来历**：用户 2026-09-23 暂停 `P1-ENG-LOOP-001` 的 AC-3 修订 3 返工（账本同日「用户暂停 AC-3 修订 3 返工，快层替换探针先出数据」，
> 逐字：「暂停返工，探针先出数据，理由是非对称性——C7/R8 是三轮会话里最贵的部分……探针是零消耗、天级出数」）。账本约定探针清单四项，
> 数字、分桶与 IoU 口径由本提案冻结并经接受审查。本会话向用户追问一题：第 2 项「关联可行性」的范围，用户选「静态 margin + 序列回放（推荐）」
> （AskUserQuestion 所选选项原文），故 §2 的 P2 含两半。本提案是方向层立项的落实，不是执行授权；§5 为申请值，执行信封由用户 `ACCEPTED` 后逐字签发，
> 阶段 B 的 Play/查询额度不得挪用（账本原文）。
> **AR1 → 本稿（D2，2026-09-24；D1 裁定原文保留在「D1 退修要求」）**：AR1-1 → §3.5.4 以同行 2×2 配对诊断替换「乘积上界」，AC-6、§6.1-1、R6 同步删除上界主张；
> AR1-2 → §3.2.2 适用域矩阵（域外格写 `N/A(<理由>)`）、§3.1 距离轴分离（斜距 vs 轴向深度，两张表）、§3.5.1 分组/分母/层闭集、成功口径改为「对象身份相等」；
> AR1-3 → §3.4 窗口保持率的起点资格、末端删失、漏检恢复、帧数 buffer 与不规则时间戳规则及五条具名反例，AC-5 同步；
> AR1-4 → §3.5.3 分页合并闭集（K=0、多页 unique、任一页 ambiguous、`INVALID`）、§5/§8 用 609 行清单精确对账（臂 B 929 页、臂 C 588 行、余量 183）与停止处置；
> AR1-5 → §6.2 读法全部改为条件性/描述性并逐格列「不可推出」、§3.2.1 T0-bank 参考库的确定选择规则、留出关系与身份清单（AC-1）。§7 裁定 (a)–(d) 已消费。
> **AR2 → 本稿（D3，2026-09-24；用户 §4.2 (a) 处置见账本同日「用户处置第二次设计退修：保留范围并修正 AR2-1…3」；D1/D2 裁定原文保留）**：
> AR2-1 → §3.2.1 参考库隔离单位改为 `splits.json` 的近重复**原子**（族与会话都被其包含），删除「留一段」；评 scout-1 与 BODY-001 arm A 五段时参考池只剩 train 原子 `{a2}`，评 arm B / scout-4 / 609 行帧时为 train∪dev 原子；库不足的确定处置（`BANK_PARTIAL(k/9)` / `N/A(BANK_EMPTY)`）、`same_instance_in_bank` 标记与 AC-1 的原子零交集断言；
> AR2-2 → §3.4 七类互斥结局（三类排除 + 四类判定）按固定顺序分类，分母 = 四类判定之和，逐序列、逐桶写计数守恒式；跨窗口末端的漏检段以其实际结局判定，序列结束仍未恢复的记 `UNRESOLVED_END_MISS`，**计入分母且不算保持**；AC-5 反例由 6 条增至 11 条；
> AR2-3 → §3.4 改写为钉版 8.4.104 的实装接口（`BYTETracker(args)` / `BOTSORT(args)` 无 `frame_rate`；每帧一次 `update(boxes, img)`；`track_buffer` = 30 次调用；秒数只用于报表），具名适配层 `replay.py:as_boxes()` / `run_sequence()` 与库边界红绿；并如实披露 `.venv-yoloe` 缺 `lap`（事实 21）：§5 新增 1 次 `lap>=0.5.12` wheel 安装为必需信封项，D2「关联零下载 / pip 0」不成立。

## 0. 现状与只读事实（本会话只读核实，`file:line` 以 2026-09-24 HEAD 为准；零模型运行、零写入 `runtime/`）

| # | 事实 | 依据 |
|---|---|---|
| 1 | 快层现状：冻结 NanoTrack-v2 核心无校准丢失阈值（`score_threshold: None`），目标出画后通常继续返回 ok；RATE-002 B2 Decision A 的失败机制是目标驶向远端（斜距 ~75 m、车高 ~9 px）后模板交接给静态背景并锁死，锁定期间分数 0.83–0.94 与正确期不可区分 | `controller/trackers.py:437-489`；`docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md:15-34` |
| 2 | NanoTrack 历史成绩只覆盖有限几何：TRACK-002 30 s pilot 0.99、DETECT-001 良性小环 150 s `C_track|geom` 0.92、RATE-002 默认路线机身 hold 0.24–0.25、BODY-001 只在前 62.5 m 评 `C_track|geom`（=1.0）；默认路线整圈从未验证 | 账本 2026-09-23 条目上文语境（接受角色逐条核实）；`docs/implementation-status.md:1670-1685` |
| 3 | `P1-DETECT-001` 验收 6 资格（qual-3）：detector 节奏 75/75 = 检测**节奏**达成，不是召回；决策 AGREE 36 / TENTATIVE 19 / NO_CANDIDATE 20，零 REANCHOR；验收 4「背景锁定打破测试」（冻结 B2 困难场景、含 t≈40 s 交接点的 ≥150 s 窗口、incorrect/matched < 0.5 且 ≥1 次三门通过的 DISAGREE 重播种）**从未运行**，是该项未闭的证据缺口 | `docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md:309-356`；`docs/implementation-status.md:1670-1685`；账本 2026-09-23 |
| 4 | scout-1（`p1-detect-scouting`，锚点 `(132.0, 0.2, 117.0)` 与默认场景相同）：真值 705 帧、目标可见 659、斜距 25.0–73.4 m（p50 47.7）、≥65 m 86 帧、目标短边 <32 px 424 / 32–64 px 202 / ≥64 px 33；冻结分析（2 Hz 采样、≥65 m、conf ≥0.25、IoU ≥0.30）oracle-pointed 召回 **0/45**，DINOv2 目标余弦 27 样本中位 0.398、过 0.5 阈值 1/27，干扰车分离机会 0 | 本会话统计 `runtime/p1-detect-scouting/p1-detect-001-scout-1/truth/`；`tools/run_detector_scouting.py:47-53`；`docs/evidence/P1-DETECT-001-scouting-implementation.md:36-66, 329-339` |
| 5 | scout-4（SCENE-004 良性小环）：2,405 帧全可见，斜距 26.1–30.5 m，目标短边 p50 61.6 px（<32 px 0 帧）；严格召回 172/187、目标余弦中位 0.699 vs 干扰 0.459、0.1 margin 通过 174/187 | 本会话统计 `runtime/p1-scene-004-scouting/p1-scene-004-scout-4/truth/`；`docs/evidence/P1-SCENE-004-implementation.md:667-673` |
| 6 | BODY-001 九段归档（默认路线、机身 `(132, 25.2, 117)` 起始）：每段保留 128 帧 JPEG + `m3_body_truth.jsonl` v2（目标/机身世界坐标、`truth_box_*`）；可见且带框 5,856 行：斜距 25.0–73.4 m（p50 40.9）、≥50 m 2,310、≥65 m 537；短边 p50 32.6 px、<32 px 2,855、≥64 px 214 | 本会话统计 `runtime/test-results/p1-m3-body-001-arm-*-post-run/` |
| 7 | **演示目标车是两个红色立方体**（车身 2×1×4 m + 车顶 1.7×0.7×2 m，`PrimitiveType.Cube`），不是目录车辆网格；预训练「car」检测器对它的召回无任何既有证据 | `Assets/TetheredTracking/Scripts/TargetVisualFactory.cs:75-102`；`LoopTargetVehicle.cs` |
| 8 | LOOP-001 K1 合同与实测：`hz` 5、`R` 128、`K_pub` 2、`T_pub` 0.4 s；诊断 6 段 2–4 首批追平 32–44 帧、每帧 19–39 ms、帧差 3–8 → `catchup_stale`；指定→首条 `WRITTEN` 实测 8–13 s；AC-3 修订 3（静音多批追平、`T_catchup` 6 s）已裁定但未派发，随本项暂停 | LOOP-001 提案 §3.3、Pending rulings R-B12…13；`docs/parked-status.md`「`P1-ENG-LOOP-001`（2026-09-23…）」 |
| 9 | 仓库 YOLOE `runtime/yoloe/yoloe-11s-seg.pt`（sha `8e439445…`）checkpoint 的 `names` 是占位 `'0'…'79'`、无 `pe`：**离线没有内置文本词表**；文本提示 `set_classes(get_text_pe(...))` 要下载 MobileCLIP-BLT `mobileclip_blt.ts`；**视觉提示**路径（`YOLOEVPSegPredictor`，参考框 + `cls`）已在 DETECT-001 本机零下载跑通；ONNX 导出静态、不能换提示 | 本会话 `torch.load` 只读元数据；`ultralytics/nn/text_model.py:279-292`；`controller/reanchor_models.py:145-193`；`docs/parked-status.md`「YOLOE simulation/deployment split」 |
| 10 | 关联算法库内自带（但其导入期依赖 `lap` 缺失，见事实 21）：`ultralytics 8.4.104`（`.venv-yoloe`）内置 ByteTrack / BoT-SORT（`with_reid: False`，纯 IoU/运动，无权重）；DINOv2 ViT-S/14 源码+权重已钉在仓库（Apache-2.0）；`.venv-yoloe` 的 torch 2.13.0 / torchvision 0.28.0 与 `config/detector-reanchor.models.json` 钉版一致 | `ultralytics/cfg/trackers/{bytetrack,botsort}.yaml`；`config/detector-reanchor.models.json` |
| 11 | 桌面时延先例（本机 CPU，640×480，YOLOE VP + DINOv2）：detector 74–98 ms、外观门 21–26 ms、worker 95–125 ms；NanoTrack 每帧 5–39 ms（诊断 5/6） | `docs/evidence/P1-DETECT-001-implementation.md:120-123, 180-183`；LOOP-001 R-B12 |
| 12 | 609 行冻结评估集：448 个 `frame_id`（392 张不同字节的图）；分组 G1 210 / G2 49 / G3 48 / G3′ 50 / G4 86 / G5 100 / G1t 23 / G2t 23 / G3t 12 / LEGACY_ONLY 8；层 S 127 / M 211 / L 171 / NA 100；族 a4 155 / a6 142 / a3 119 / a9 100 / s004-scout 70 / m3-armB 23；`has_dynamic_target` 68 行；G3/G3t/G3′ 110 行 106 帧，候选数 1/2/3 = 36/64/10；**整帧接地的 base 零样本与 C2 预测各 609 行已在本机**（`zero-shot.jsonl`、`eval-adapter.jsonl`） | 本会话统计 `outputs/eng-sft/P1-ENG-SFT-002/data/eval.jsonl`；LOOP-001 §8 |
| 13 | 帧目录 `runtime/dist-data/frames_catalog/attempt-2` 43,535 行，每行含全部布局对象的 `status`（闭集 `OK`/`TOO_SMALL`/`TRUNCATED`/`EXCLUDED_OCCLUDED`/`NOT_IN_VIEW`/`PHANTOM`）、`visible_norm_xywh`、`referable`、`camera_depth_m`（相机轴向深度，**不是斜距**）；609 行的 448 个帧 ID **全部**在目录中；每帧 `OK` 可指称车辆 min/p50/max = 0/12/55（合计 6,597）；全目录 ≥2 辆同类 `OK` 车辆的帧 2,905 | 本会话统计（gzip 只读） |
| 14 | VLM 既有成绩（C2 微调，609 行）：G1 76.7%（S 36.7%）、G2 81.6%、G4 82.6%、G1t/G2t 65.2%、`car` 类最弱（35–43%）；G3 报告 39.6% / 严格 25%；G5 none 79%；base 零样本 v2 G1∪G2 51.0%、G4 8.1%、解析失败 103 | `docs/reviews/P1-ENG-SFT-002-stage-summary.md` §4–§5 |
| 15 | 宿主：5060 已有 `.venv-language`（torch 2.11+cu128、transformers 5.17）、base 权重、C2 adapter，服务已停；base 零样本 4 行自检 p50 1.73 s；Mac `.venv-yoloe` 无 transformers、HF 缓存空。T7 上存在 `/Volumes/T7/CityScene/fast_benchmark/models/yolo11n.pt`（仓库外、来源未核） | LOOP-001 §8、stage-b-prep §4；本会话 `ls` |
| 16 | S4 attempt-2 族划分：train = {a2}；dev = {detect-scout1（即 scout-1）, m3-armA, a1-s2, a7, rate, scene-val}；test = {m3-armB, a3, a4, a6, a9, s004-qual, s004-scout（即 scout-4）, s004-smoke}。train∪dev 任一帧的 L 层（短边 ≥64 px）`OK` 目录车最多覆盖 4 个类别（a7 `frame_0000002550`，20 辆 `OK`）；带绑定红立方体且短边 ≥32 px 的 train∪dev 帧：arm A 305、scout-1 235、a7 1,511、a2 1,133、a1-s2 1,082 | 本会话统计 `runtime/dist-data/splits/attempt-2/splits.json` `family_assignment` 与帧目录 |
| 17 | 609 行 × 候选集 K（`OK` 目录车 ∪ 已绑定动态目标）：K=0 行 21、p50 14、p90 35、max 55；K>16 行 260、>32 行 67、>48 行 14；`Σ_{K≥1} ceil(K/16)` = **929** | 本会话统计 |
| 18 | YOLOE 跨图参考库的库内路径：`YOLOE.get_visual_pe(img, visual)` 逐参考图得每类嵌入，`YOLOE.set_classes(names, embeddings)` 固定后可对任意源图 `predict`；`predict(source=[…], visual_prompts=…)` 的多图模式是「每张源图各自提示」，不是跨图库 | `ultralytics/models/yolo/model.py`（`YOLOE.get_visual_pe`/`set_classes`/`predict`） |
| 19 | S4 attempt-2 `splits.json` 以**近重复原子**（`payload.atoms.atoms`：近重复对连通的族并集）为划分单位，`leakage_assertions.pairwise_disjoint = true`（6 对）：train 原子 = {a2}（2,523 帧）；dev 原子 = {`detect-scout1`, `m3-armA`, a1-s2, a7, `rate`, `scene-val`}（13,144 帧；近重复见证对含 arm A void 帧 ≈ scout-1 帧 ≈ RATE-002 帧）；test 原子两个 = {`m3-armB`} 与 {a3, a4, a6, a9, `s004-qual`, `s004-scout`, `s004-smoke`}（8,450 帧）。`payload.frames` 逐帧路径可查：BODY-001 五段 arm A post-run 目录（各 128 帧）与 scout-1（768 帧）在 dev，四段 arm B post-run 目录（各 128 帧）与 scout-4（2,405 帧）在 test | 本会话只读 `runtime/dist-data/splits/attempt-2/splits.json`（`payload.atoms` / `atom_assignment` / `frames` / `leakage_assertions`） |
| 20 | 钉版 `ultralytics 8.4.104` 跟踪器实装接口：`BYTETracker.__init__(self, args)`、`BOTSORT.__init__(self, args)`——**没有 `frame_rate` 形参**；`max_frames_lost = args.track_buffer`（30，按 `update` 调用次数计）；`update(self, results, img=None, feats=None, **kwargs)` 每调用 `frame_id += 1`，`results` 须暴露 `.conf` / `.xywh` / `.cls` 并支持布尔索引（库自身传 `result.boxes.cpu().numpy()`；`Boxes(tensor[N,6]=[x1,y1,x2,y2,conf,cls], orig_shape)`）；输出行 `[x1,y1,x2,y2,track_id,score,cls,idx]`；丢失移除 `_remove_stale_lost` 在同一次 `update` 的关联**之后**执行，条件 `frame_id − end_frame > max_frames_lost`，故两次绑定之间严格介于其中的调用帧数 L ≤ 30 才可能同 ID 恢复、L ≥ 31 必为新 ID（`with_reid: False`）；BoT-SORT 的 GMC（`sparseOptFlow`）仅在 `img is not None` 时运行；`build_encoder(with_reid=False)` 返回 None（无权重）；构造器调用 `reset_id()`，每个新实例的 ID 从 1 起 | `trackers/byte_tracker.py:249-300, 481-486`；`trackers/bot_sort.py:161-173`；`trackers/track.py:47-48, 78, 110-121`；`trackers/utils/stracks.py:58-69`；`trackers/utils/reid.py:139-140`；`engine/results.py:956-973` |
| 21 | `.venv-yoloe` **没有 `lap`、也没有 `scipy` 和 pip**（`uv` 在 `/opt/homebrew/bin/uv`）；`trackers/utils/matching.py:7-14` 在模块级 `import lap`，失败时调用 `check_requirements("lap>=0.5.12")` 尝试自动 pip 安装再导入——本机 `from ultralytics.trackers import BYTETracker` 直接 `ModuleNotFoundError: No module named 'lap'`。因此 P2b 的库回放**不是零下载**：需要向 `.venv-yoloe` 安装一次 `lap>=0.5.12`（wheel 1 个），D2 事实 10 与 §5「pip 0」据此更正 | 本会话 scratchpad 只读导入尝试（无模型、无 `runtime/` 写入）；`matching.py:7-14`；`ls site-packages` |

**从事实推出的探针设计原则**：(a) 换栈要回答的不是「检测器平均召回多少」，而是在 **LOOP-001 的默认几何**（斜距 25–73 m、目标短边中位 26–33 px、S 层过半）
和**脚本红立方体目标**上召回多少，所以分桶以斜距/深度与短边为轴、目标种类单列；(b) 追平机制的替代品是「从会话开始持续处理每帧的检测+关联」，
其可行性取决于目标 track-ID 能否跨 8–13 s 保持，所以 P2 要有序列回放；(c) VLM 的价值只在候选选择层比较才公平，四臂共用 oracle 候选集，配对诊断只在同行做交集、不做乘法；
(d) gold 全部是 amodal 投影 AABB（`UNVERIFIED`），双 IoU 口径并列，不冻结合格线；(e) 零 Play、零 ID、零训练，只读 `runtime/`。

## 1. 目的与价值

给用户一份可用来二选一（续跑 LOOP-001 追平返工 / 换成检测+关联快层）的**数据**，回答四个可证伪问题：

1. **P1 分桶召回**：仓库现有预训练检测器（先零下载的 YOLOE 视觉提示，可选 COCO YOLO）在带真值框的 Unity 帧上，按目标短边 S/M/L × 距离四档 × 目标种类（目录车 / 脚本红车）的召回与每帧误检各是多少；默认几何 ≥50 m 与 S 层是否仍接近 scout-1 的 0/45。
2. **P2 关联可行性**：(a) 静态——同帧多辆同类车时 DINOv2 余弦 margin 能否区分（复用 scout-4 的 0.5/0.1 口径作描述）；(b) 序列——在 scout-4 / scout-1 / BODY-001 归档上离线跑检测+ByteTrack 类关联，目标 track-ID 在 8 s / 13 s 窗口内的保持率、ID 切换与碎片数。
3. **P3 VLM 四臂对照**：同一 609 行，整帧接地（既有结果，零查询）vs 裁图编号选择 vs 整帧编号框（set-of-mark）vs 嵌入/颜色直方图无 VLM 基线，按分组 × S/M/L 报告——在 oracle 候选条件下 VLM 在候选选择层还剩多少价值、S 层能否靠裁图放大。
4. **P4 与 DETECT-001 的关系**：写清本探针复用了 DETECT-001 哪些冻结件、与其验收 4 未闭的背景锁定证据缺口是什么关系、哪些结论仍待复现。

本项**不给「换栈/保留」结论**，只按 §6.2 预注册读数表填值；裁定归用户（账本原文「探针结论出来后由用户决定续跑或收口」）。

## 2. 范围与不做的事

### 2.1 交付（单候选，停点 `K4`）

| 件 | 内容 |
|---|---|
| 代码 | `tools/eng_fast/`：`inputs.py`（帧/真值/目录联表、参考库选择与身份清单）、`detect.py`（检测器层：T0 视觉提示库、T0-oracle、可选 T1）、`recall.py`（分桶召回与 FP/帧、适用域矩阵）、`margin.py`（P2a）、`replay.py`（P2b 序列回放与 ID 统计）、`vlm_arms.py`（P3 臂 B/C 的图与 prompt 生成、分页合并、解析、评分；臂 A 候选匹配换算；配对诊断）、`baseline.py`（臂 D）、`latency.py`、`report.py`（读数表）；`tests/test_eng_fast_*.py` 无 GPU |
| 产物 | `outputs/eng-fast/P1-ENG-FAST-001/`（git 忽略；候选须追加 `.gitignore` 行 `/outputs/eng-fast/`，与 `outputs/eng-sft/` 同规则）；证据 `docs/evidence/P1-ENG-FAST-001-{report.md,inputs.json,recall.json,margin.json,replay.json,vlm-arms.json,latency.json,ledger.json,tests.log}` |
| 5060 侧 | 只跑臂 B/C 的 VLM 查询：一个自含脚本 + 预渲染图包 + 盲索引，结果 JSONL 回传本机评分（评分在 Mac，模型在 5060） |

### 2.2 明确不做

1. 零 Unity Play、零采集、零 scenario/session/run ID、零训练、零云端；不改 `Assets/`、`config/`、`controller/`、`tools/eng_sft/`、`tools/run_detector_scouting.py`（零字节）。
2. 不接入运行时、不写任何桥文件、不改 LOOP-001 合同/候选/证据；不替 LOOP-001 决定续跑或收口。
3. 不做 Jetson / TensorRT / 5060 检测时延主张（工程流程 §9：无板端实测不得声称）；时延只报 Mac CPU/MPS 桌面数字。
4. 不新建评估集、不复算 609 行整帧接地（臂 A 直接复用既有预测）；不把本项任何数字写成 SFT-002 功能门的补证或跟踪性能主张。
5. 不调参：检测阈值沿用 DETECT-001 冻结 0.25、关联参数用库默认 `bytetrack.yaml`/`botsort.yaml`，不用探针数据反向选参。
6. 不闭合 DETECT-001 验收 4 的缺口（那需要困难场景 Play），只写清关系。
7. 除 §5 必需的 `lap` wheel 1 次（事实 21）外不下载任何文件，可选行须用户逐字签发；不自动重指认目标（定局 ④ 由用户决定，与本项无关）。
8. 不用 oracle 候选臂的成绩推断检测器候选下的 VLM 成绩或架构（AR1-1/AR1-5）；那需要另立用检测器候选跑 B/C 的探针。

## 3. 接口与数据契约

### 3.1 输入（全部只读；身份清单写入 `-inputs.json`，缺失/不一致 fail-closed）

| 来源 | 帧 | 真值 | 距离轴 | 用途 |
|---|---|---|---|---|
| scout-1 `runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames/` + `runtime/p1-detect-scouting/p1-detect-001-scout-1/truth/` | 768 图 / 705 真值（配对数以清单为准） | `p1-detect-scouting-truth/v2`：目标框、`target_slant_range_m`、`target_visible`、干扰车框 | **斜距**（真值字段） | P1（默认几何、远端）、P2b |
| scout-4 `runtime/test-results/p1-scene-004-scout-4-closed-exchange/frames/` + `runtime/p1-scene-004-scouting/p1-scene-004-scout-4/truth/` | 2,405 / 2,405 | 同上 | 斜距 | P1（良性对照）、P2b |
| BODY-001 九段 `runtime/test-results/p1-m3-body-001-arm-*-post-run/{frames,m3_body_truth.jsonl}` | 9 × 128 图；真值按 `frame_id` 配对 | `p1-m3-body-truth/v2`：`truth_box_*`、目标/机身世界坐标 | 斜距 = 目标与机身世界坐标欧氏距离 | P1（**脚本红车**、默认几何）、P2b |
| 帧目录 `runtime/dist-data/frames_catalog/attempt-2`（43,535 行）+ 各族帧 | 609 行的 448 帧（P3、P1-d）；P2a 取 ≥2 辆同类 `OK` 的帧对 | 每对象 `visible_norm_xywh`（裁剪后 amodal 投影 AABB）、`status`、`referable`、`camera_depth_m`；动态目标按 `tools/eng_sft/adapters/unity_s3.py` 规则 ① 取框 | **轴向深度** `camera_depth_m`（单独成表，表头逐字写「轴向深度」，不与斜距表合并或相加） | P1-d（目录车全类）、P2a、P3 候选集 |
| 609 行 `outputs/eng-sft/P1-ENG-SFT-002/data/eval.jsonl` + `upload/frames/` + 既有预测 `zero-shot.jsonl` / `eval-adapter.jsonl` | 448 帧 19.8 MB | gold 三态与框、`stratum`、`group`、`definite_ids`、`target_object_ids` | — | P3 |

**gold 口径**：全部为世界 AABB 投影裁剪框（amodal，`UNVERIFIED`，SFT-002 表 J 抽查外无人工紧框）；报告每处标注。
**分桶口径（冻结申请，§7 裁定 (a) 已允许沿用）**：短边 S <32 / M 32–64 / L ≥64 px（`build_sft_data.py:604-612`）；距离档 `<35` / `35–50` / `50–65` / `≥65` m（65 = DETECT-001 远端阈值），
斜距表与轴向深度表各自使用同一组边界但**分表**；目标种类 {目录车网格, 脚本红立方体}。**IoU 口径**：每处并列 ≥0.30（DETECT-001 scouting）与 ≥0.50（SFT-002）。

### 3.2 检测器层（`detect.py`；统一输出 `[x1,y1,x2,y2]_norm, score, cls`，评分时类别无关）

| 档 | 模型 | 提示/类别 | 下载 | 状态 |
|---|---|---|---|---|
| **T0-bank** | `yoloe-11s-seg.pt`（仓库，sha 核对）视觉提示库（§3.2.1） | 两类：`vehicle`（目录车样例库）、`target-primitive`（红立方体样例）；`set_classes` 固定后对源帧 `predict` | 0 | 基线，必做 |
| **T0-oracle** | 同上 | DETECT-001 scouting 口径：同会话 `reference.json` 绑定框作单类视觉提示（`YOLOEVPSegPredictor`，与 `YoloeProposer.initialize` 同路径） | 0 | 必做，只在有同会话参考的来源 |
| T1a（可选） | YOLOE 文本提示 | 九类词 | MobileCLIP-BLT `mobileclip_blt.ts`（大小以 ultralytics 资产为准，记 sha） | 用户签发后才做；默认不做 |
| T1b（可选） | COCO YOLO11n（`yolo11n.pt`，约 5.6 MB） | COCO `car`/`truck`/`bus` 并集 | 官方资产下载 1 次，或从 T7 副本导入并核 sha 与官方一致 | 用户签发后才做；默认不做 |

阈值 0.25、`imgsz` 640、`device` cpu 与 mps 各跑一次时延、召回只报 cpu（两者框应一致，差异如实报）。

#### 3.2.1 T0-bank 参考库：确定选择规则与留出（AR1-5）

- **隔离单位与候选参考池（AR2-1）**：隔离单位是 S4 attempt-2 `splits.json` 的**近重复原子**（事实 19；原子 = 近重复对连通的族并集，同族、同会话都在同一原子内，因此「同族/同会话排除」由原子排除**包含**，不再单列）。被评估帧的原子按 `payload.frames` 的路径查得（查不到 → `SPLIT_LOOKUP_MISSING`，整体 fail-closed，不猜族）；参考池 = train∪dev 原子 **减去** 被评估帧所在原子：
  - 评 scout-1（dev 原子）与 BODY-001 arm A 五段（dev 原子，`m3-armA`）：池 = train 原子 `{a2}`（2,523 帧）；arm A 任一段、scout-1、a7、a1-s2、`rate`、`scene-val` 都不得作参考——D2「留一段」规则**删除**；
  - 评 BODY-001 arm B 四段（test 原子 `{m3-armB}`）、scout-4 与 609 行帧（test 原子）：池 = train∪dev 原子全部。
  原子排除是绝对优先级，先于类别覆盖与并列规则；库不足时不放宽（处置见下两条）。
- **`vehicle` 类样例（目录车）**：贪心覆盖九类——每轮在候选池中选「短边 ≥64 px 的 `OK` 目录车能新增覆盖类别数最多」的帧（并列取 `OK` 车辆数多者，再并列取帧字节 sha 字典序最小者），把该帧每个新增类别中面积最大的一个框加入库；直到九类覆盖或无帧能新增；参考帧总数 ≤ 6。事实 16 说明单帧至多 4 类，故预计 3–6 帧。覆盖不足九类时记 `BANK_PARTIAL(<k>/9)`（格照常出数并标注）；池内没有短边 ≥64 px 的 `OK` 目录车时，该来源的 T0-bank 目录车格写 `N/A(BANK_EMPTY)`。
- **`target-primitive` 类样例（红立方体）**：参考池（按上条原子规则）中带绑定动态目标且目标短边 ≥32 px 的帧，取目标框面积最大者 1 帧（并列取 sha 最小）：评 scout-1 / arm A 时只能来自 a2（事实 16：a2 有 1,133 帧合格），评 arm B / scout-4 / 609 行帧时来自 train∪dev 原子；池内无合格帧 → 该来源的 T0-bank 红立方体格写 `N/A(BANK_EMPTY)`。红立方体参考与被评目标必然是同一脚本实例（演示目标就是它），报告标 `same_instance_by_design`，不作留出。
- **嵌入固定**：对每张参考帧调用 `get_visual_pe(img, visual)` 得该帧含有类别的嵌入；每类在参考帧间取算术平均后 L2 归一化，`set_classes(["vehicle","target-primitive"], vpe)` 一次固定，之后所有评估帧只 `predict`。若实现时发现库路径不接受多帧平均（记录报错原文），预注册回退：每类只用覆盖类别数最多的那一张参考帧的嵌入，并在报告标 `BANK_FALLBACK_SINGLE_FRAME`。
- **身份清单与同实例标记**：每个来源一份 `(参考帧路径, sha256, 框, object_id, 类别, 族, split, 原子)` 列表、被评来源的原子、嵌入张量 sha 写入 `-inputs.json`（AC-1）；断言两条：评估帧∩参考帧 = ∅（按 sha）**且** 参考帧原子∩{被评原子} = ∅（按原子；帧 sha 零交集不能证明隔离，AR2-1）。目录车 gold 对象逐个标 `same_instance_in_bank`（其 `object_id` 是否出现在参考框中），AC-2 的目录车格按该标记分两子行；没有 `object_id` 的真值框（scout 干扰车）标 `INSTANCE_UNKNOWN`。

#### 3.2.2 适用域矩阵（AR1-2；报表逐格按此出数，域外格写 `N/A(<理由>)`，不以缺格冒充失败）

| 来源 | T0-bank | T0-oracle | T1a/T1b（若签发） | 距离表 |
|---|---|---|---|---|
| scout-1 | ✓（池 = train 原子 {a2}） | ✓（`reference.json`） | ✓ | 斜距表 |
| scout-4 | ✓ | ✓（`reference.json`） | ✓ | 斜距表 |
| BODY-001 九段 | ✓（arm A 五段：池 = train 原子 {a2}；arm B 四段：池 = train∪dev 原子；§3.2.1） | `N/A(NO_SESSION_REFERENCE)` | ✓ | 斜距表 |
| 609 行的 448 目录帧（全部 `OK` 目录车 ∪ 动态目标为召回对象） | ✓ | `N/A(NO_SESSION_REFERENCE)` | ✓ | 轴向深度表 |

### 3.3 P1 召回与 P2a margin（`recall.py`、`margin.py`）

- 召回：每个真值/目录目标框在同帧检测输出（类别无关）中 max IoU ≥ 阈值即命中；按 §3.1 分桶报 `hit/n`、bootstrap 95% CI（2,000 轮，seed 20260923）；FP/帧 = 未与任何真值/`OK` 车辆框（IoU ≥0.3）匹配的检测数/帧，按来源分列，**只作描述，不与任何决策计数比较**（AR1-5）。
- 每格分母 n 与来源/档/种类/检测器档一并写出；域外格按 §3.2.2 写 `N/A(<理由>)`。
- margin（复用 scout-4 方法，`DinoV2Embedder`）：在同族同会话、≥2 辆同类 `OK` 车辆的帧对 (f_i, f_{i+Δ})，Δ ∈ {1, 5, 13} s（按 sidecar `simulation_time_s`，容差 ±0.2 s），锚 = f_i 上对象 o 的裁剪嵌入，
  margin = cos(锚, f_{i+Δ} 上 o) − max cos(锚, f_{i+Δ} 上同类其他对象)；报 margin 分布、`≥0.1` 通过率、锚-自身 `≥0.5` 通过率，按短边层与类别分桶；每 Δ 目标 ≥200 对（事实 16 的族池：a2 698、a9 588、a6 566、a4 298、a3 269 帧可用；不足如实报）；裁剪 <2 px 记 `CROP_INVALID`。

### 3.4 P2b 序列回放（`replay.py`；AR1-3 与 §7 裁定 (d) 的可复算定义）

- **输入与调用（AR2-3；钉版 8.4.104 实装接口，事实 20）**：三类序列（§3.1 前三行）按 `simulation_time_s` 严格升序 t_0 < … < t_last（重复或倒退时间戳 → 该序列 `INVALID_TIMESTAMPS`，不出数）。每个（序列, 算法）新建一个实例：`BYTETracker(args=IterableSimpleNamespace(**YAML.load(check_yaml("bytetrack.yaml"))))` 与 `BOTSORT(args=IterableSimpleNamespace(**YAML.load(check_yaml("botsort.yaml"))))`（与 `trackers/track.py:47-48, 78` 同一构造路径；**没有也不传 `frame_rate`**，D2 该参数删除）；每帧恰好一次 `tracker.update(boxes, img)`：`boxes = Boxes(tensor[N,6]=[x1,y1,x2,y2,score,cls]（像素）, orig_shape=(H,W)).cpu().numpy()`，无检测时传 `(0,6)` 空张量仍调用；`img` = 该帧 BGR uint8（BoT-SORT 的 GMC 需要它，ByteTrack 忽略）；输出行 `[x1,y1,x2,y2,track_id,score,cls,idx]`；序列结束时 `tracker.frame_id` 必须等于帧数（AC-5 断言）。`track_buffer`（默认 30）就是 `max_frames_lost`，按**调用帧数**计，不换算成秒；报告给出该序列「30 次调用对应的中位秒数」与帧间隔的 p5/p50/p95，秒数只用于报表，不进入任何判定。具名适配层：`replay.py:as_boxes()`（检测输出 → `Boxes`）与 `replay.py:run_sequence()`（逐帧调用与绑定）；验收测试 `adapter_boxes_fields`（`xywh`/`conf`/`cls` 往返与布尔索引）、`one_update_per_frame`（`frame_id == n`）、`library_buffer_boundary`（合成序列：目标连续 5 帧出现、空检测恰 30 次调用后再出现 → 同 `track_id`；空 31 次 → 新 `track_id`；两算法各一次；这是对库边界的实测，事实 20 的读码结论以它为准）。依赖：`lap>=0.5.12`（事实 21）须先按 §5 安装 1 次；安装失败 → 记 `LAP_UNAVAILABLE`，P2b 全部格写 `N/A(LAP_UNAVAILABLE)` 并回用户，不改用其他求解器、不改库代码。
- **可见集与绑定**：V = 真值判目标可见且框合法的帧；对 i ∈ V，绑定 ID b_i = 与真值框 max IoU ≥0.3 的 track ID（并列取 IoU 大者，再并列取 ID 小者），无匹配 b_i = ∅（漏检）。
- **起点、帧类型与漏检段**（W ∈ {8, 13} s）：起点集合 = V 的每一帧 i。相对起点 ID b_i，窗口内每个调用帧 j（t_i < t_j ≤ t_i + W）四选一：`BOUND_SAME`（j ∈ V，b_j = b_i）、`BOUND_OTHER`（j ∈ V，b_j ∉ {b_i, ∅}）、`MISS`（j ∈ V，b_j = ∅）、`INVISIBLE`（j ∉ V）。**漏检段** = 两个 `BOUND_*` 帧之间（或至序列末）连续的 `MISS`/`INVISIBLE` 调用帧极大段，段长 L = 段内调用帧数（含不可见帧，因为跟踪器不知道可见性）；跨过窗口末端的段按其**实际结局**判定（允许读取窗口末之后、直到序列末的帧，只为闭合该段，不为发现新事件）。
- **七类互斥结局（AR2-2；按序判定，命中即止）**：(1) b_i = ∅ → `UNBOUND_START`；(2) t_i + W > t_last → `CENSORED_END`；(3) 窗口内存在连续 `INVISIBLE` 调用帧数 > `track_buffer` 的段 → `TRUTH_GAP`（只看真值，不看跟踪器）；(4) 否则按时间顺序扫描窗口，最先发生者定结局：遇 `BOUND_OTHER` 帧 → `ID_SWITCH`；某漏检段长 L 达到 `track_buffer` + 1 → `LOST_BEYOND_BUFFER`（不论其后如何结束；之后若同 ID 回来只可能是漂移回归，子计数 `drift_return`）；漏检段以 `BOUND_SAME` 结束且 L ≤ `track_buffer` → 继续扫描（§7 裁定 (d)：算保持）；跨窗口末端的段在窗口末之后以 `BOUND_OTHER` 结束 → `ID_SWITCH`，以 `BOUND_SAME` 结束且 L ≤ `track_buffer` → 继续，序列结束仍未结束且 L ≤ `track_buffer` → `UNRESOLVED_END_MISS`；扫描完毕无事件 → `KEPT`。(1)–(3) 为**排除类**（不进分母），(4) 的四种为**判定类**。
- **分母与守恒**：保持率 = `KEPT` / D，D = `KEPT` + `ID_SWITCH` + `LOST_BEYOND_BUFFER` + `UNRESOLVED_END_MISS`（唯一分母，不再使用「合格起点」一词；`UNRESOLVED_END_MISS` 没有同 ID 恢复证据，**计入分母且不算保持**，读数偏保守，其计数并列给出）。每个（序列, W, 算法）在 `-replay.json` 写守恒式 |V| = `UNBOUND_START` + `CENSORED_END` + `TRUTH_GAP` + D 并断言相等（AC-5）；按起点距离档分桶时每桶各自守恒。
- **序列级指标**：ID 切换次数 = i ∈ V、b_i ≠ ∅ 且与上一个绑定非空帧的 ID 不同的次数；碎片数 = V 内漏检连续段数；最长同 ID 持续秒数 = 同 ID 连续绑定（允许 ≤ `track_buffer` 帧漏检）的最长 t 跨度；漏检段长分布。
- **具名反例（合成序列，红绿；11 条）**：D2 六条 `start_unbound_excluded`、`end_censored_excluded`、`recover_same_id_within_buffer_kept`、`recover_new_id_is_switch`、`miss_beyond_buffer_not_kept`、`truth_gap_excluded` 保留；新增 `end_gap_resolved_same_id_after_window_kept`（段跨窗口末、窗口外同 ID 恢复且 L ≤ buffer → `KEPT`）、`end_gap_resolved_other_id_after_window_switch`、`end_gap_unresolved_at_sequence_end_not_kept`（序列末仍漏检、L ≤ buffer → `UNRESOLVED_END_MISS`，进分母不算保持）、`drift_return_beyond_buffer_not_kept`（L ≥ buffer+1 后同 ID 回来 → `LOST_BEYOND_BUFFER`）、`counts_conserve`（守恒式对每个分桶成立）。
- 不调参、真值只用于事后评分（Unity 真值仍未进入任何控制器）。

### 3.5 P3 VLM 四臂（`vlm_arms.py`、`baseline.py`）

#### 3.5.1 分组、分母与层（AR1-2；口径与 `tools/eng_sft/evaluate.py:31-51` 一致）

候选集（B/C/D 共用）= 该帧目录 `OK` 可指称车辆 ∪ 已绑定动态目标（`has_dynamic_target` 且规则 ① 有框），编号按框左上角行优先；K = 候选数（事实 17）。候选框与 gold 框同源（都来自目录/规则 ①），因此
索引类臂的**成功判据是对象身份相等**（选中候选的 `object_id` = gold `target_object_ids`），不做 IoU 计算，也不写成「IoU=1」。

| 组 | 行数 | 报表量 | 分母 / 层 |
|---|---|---|---|
| G1 / G1t / G2 / G2t / G4（成功组） | 210 / 23 / 49 / 23 / 86 | Success = 输出 `unique` 且选中对象 = gold 对象 | 各组行数；层取行 `stratum` |
| G3 / G3t（集合组） | 48 / 12 | 报告率 = 输出 `ambiguous` 的行占比；严格成功 = 选中索引的对象集合 = gold 对象集合 | 各组行数；层取行 `stratum`（gold 集最小短边） |
| G5（none 组） | 100 | none 率 | 100；`stratum` 为 NA，**不分层** |
| G3′（诊断） | 50 | `ambiguous` 报告率；任一 gold 成员命中率 | 50；只作诊断，不进任何门 |
| G1∪G2 误报 | 259 | 误报 none 率、误报 ambiguous 率 | 259 |
| LEGACY_ONLY | 8 | **排除**所有报表，只列计数 | — |

臂 A 的候选匹配换算：整帧预测框与候选框 max IoU ≥0.5 者视为选中该候选（`ambiguous` 各候选逐个映射），无候选达阈值记 `NO_CANDIDATE_MATCH`（对成功组计失败、单列计数）；SFT-002 原 IoU 口径的成绩原样并列引用，不重算。

#### 3.5.2 四臂定义

| 臂 | 输入 | 输出 | 查询 |
|---|---|---|---|
| A 整帧接地 | 既有 base 零样本与 C2 预测（prompt v2） | 既有三态+框 → §3.5.1 换算 | 0 |
| B 裁图编号选择 | 每页 ≤16 个候选裁图（框外扩 1.5 倍、等比缩放到 224 px 边、拼 4×4 网格），每格标号与 `x=…,y=…` 中心归一坐标；页数 = ceil(K/16)；K=0 不查询 | 每页 JSON 三态（索引），按 §3.5.3 合并 | 929 页（事实 17） |
| C 整帧编号框（set-of-mark） | 原帧叠加全部 K 个候选框与编号（线宽 1 px、字号自适应，编号不遮框内）；K=0 不查询 | JSON 三态（索引） | 588 行（609 − K=0 的 21 行） |
| D 无 VLM 基线 | 类别：DINOv2 嵌入对 train∪dev 族裁图库 kNN（k=5）多数票；颜色：HSV 色相直方图对六色原型（原型取自 S5 `VERIFIED` 颜色对象的 train∪dev 裁图）最近邻；G4：按候选 x 中心序 | 满足指令的候选数 0/1/≥2 → none/unique/ambiguous | 0 |

- 模型：`Qwen/Qwen3-VL-2B-Instruct@89644892…4203` bf16、greedy、`max_new_tokens` 64（申请参数，不是格式成功保证；截断记 `INVALID(TRUNCATED)`）、网格图/原帧不缩放；**只用 base**——C2 是整帧接地格式的适配，不套用到 B/C（限制 §6.1-3）。
- prompt：沿用 prompt v2 的词表段、G4 段逐字（`tools/eng_sft/prompt_v2.py`），只把坐标段/回复段换成索引版；全文逐字入 `-vlm-arms.json`。
- 每查询记录 token 数、时延、`finish_reason`；行序固定为 `row_id` 字典序，前 32 行即 smoke（不额外查询）：任一臂在这 32 行的 `INVALID` 率 >10% → 该臂停止，记 `STOPPED_FORMAT`，其余行 `NOT_RUN(STOPPED_FORMAT)`，不改 prompt 重试。

#### 3.5.3 臂 B 分页合并与失败路径闭集（AR1-4）

每页结果 ∈ {`unique(k)`, `ambiguous(S)`, `none`, `INVALID`}；`INVALID` = 非 JSON / 缺字段 / 索引越界或重复 / `ambiguous` 少于 2 个索引 / 截断。

| 条件（按序判定，命中即止） | 行结果 |
|---|---|
| K = 0 | `none`（确定性，零查询；行标 `K0`，计入各分母） |
| 任一页 `INVALID` 且重试额度耗尽 | `INVALID`（对成功/集合/none 组都计失败，单列） |
| 任一页 `ambiguous` | `ambiguous`，索引集 = 各页 `ambiguous` 集 ∪ 各页 `unique` 索引 |
| `unique` 页数 ≥ 2 | `ambiguous`，索引集 = 这些 `unique` 索引 |
| `unique` 页数 = 1，其余页全 `none` | `unique(k)` |
| 全部页 `none` | `none` |

重试：`INVALID` 页最多重试 1 次（同 prompt、同参数、记 `retry=1`），从 §5 的 183 行余量扣；余量耗尽后不再重试，行按上表判 `INVALID`。臂 C 同样闭集（单页）。
**预算对账**：臂 B 929 + 臂 C 588 = 1,517 行基线查询；余量 1,700 − 1,517 = 183 供重试；查询上限到达即停止发查询，剩余页/行记 `NOT_RUN(BUDGET)`，AC-6 按「部分完成」如实报各组已完成行数，不申请追加查询补齐（追加须回用户）。

#### 3.5.4 配对诊断（替换 D1「乘积上界」，AR1-1）

只在成功组（G1/G1t/G2/G2t/G4）逐行做：`det_hit` = T0-bank（cpu）在该帧对 gold 对象的 max IoU ≥0.3；`arm_ok` = 该臂 Success。按分桶报 2×2 表 `{det_hit × arm_ok}` 四格计数与行数 n，
并报 `P(arm_ok ∧ det_hit)`、`P(arm_ok | det_hit)`。**明示**：这是同一行上两种独立测量的交集，不是任何链路的成功率或上界；B/C 的裁图/框来自 oracle 候选，改用检测器框后 VLM 的成绩未测量，本项不推断。

### 3.6 时延（`latency.py`）与账目（`-ledger.json`）

- Mac CPU 与 MPS：T0 检测 ≥300 帧每帧 p50/p95（含预处理）、DINOv2 单裁图 p50、ByteTrack `update` p50；记录芯片、torch/ultralytics 版本、同机是否运行 Unity（否）。5060：只记 VLM 每查询时延。
- 账目逐项：本地模型进程启动次数（Mac 按模型分列）、5060 启动与查询行数（基线/重试分列）、下载字节（只应有 §5 的 `lap` wheel，记版本/sha/字节）、pip/uv 安装记录、传输文件清单与 sha；`runtime/` 前后 `git status --porcelain` 与目录哈希清单相同。

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | 输入身份：三类序列、帧目录联表、609 行帧的路径→sha 清单、真值来源/schema/行数、配对数与未配对原因，以及 §3.2.1 每个来源的参考库清单（参考帧 sha、框、`object_id`、类别、族/split/**原子**、嵌入张量 sha）、被评来源的原子，与两条断言「评估帧∩参考帧 = ∅（sha）」「参考帧原子∩{被评原子} = ∅」写入 `-inputs.json`；任一必需输入缺失、sha 不符、`SPLIT_LOOKUP_MISSING` 或任一交集非空即整体失败（无静默跳过）；测试含反例「参考帧来自被评原子 → 失败」 | artifact:docs/evidence/P1-ENG-FAST-001-inputs.json；test:tests.test_eng_fast_inputs | K4 | 2026-09-24 |
| AC-2 | P1 召回表：按 §3.2.2 适用域矩阵逐格出数——每格给出 `hit/n`、CI、FP/帧（描述性），按短边 × 距离档 × 目标种类 × 检测器档，双 IoU 口径并列；斜距表与轴向深度表分表；域外格逐字写 `N/A(<理由>)`；目录车格按 `same_instance_in_bank` 分两子行，参考库覆盖不足记 `BANK_PARTIAL(k/9)`、池空写 `N/A(BANK_EMPTY)`；不出现任何未分桶的单一总召回 | artifact:docs/evidence/P1-ENG-FAST-001-recall.json；test:tests.test_eng_fast_recall | K4 | 2026-09-24 |
| AC-3 | T0-oracle 在 scout-1（≥65 m、2 Hz tick）与 scout-4 上的复算与既有 0/45、172/187 逐格一致（同阈值同口径）；不一致时如实报差异并停止引用旧数 | artifact:docs/evidence/P1-ENG-FAST-001-recall.json（`legacy_alignment`） | K4 | 2026-09-24 |
| AC-4 | P2a margin：Δ ∈ {1, 5, 13} s 各 ≥200 帧对（不足如实报），报 margin 分布、`≥0.1` 与 `≥0.5` 通过率，按短边层与类别分桶；嵌入器为仓库钉版 DINOv2（sha 核对） | artifact:docs/evidence/P1-ENG-FAST-001-margin.json；test:tests.test_eng_fast_margin | K4 | 2026-09-24 |
| AC-5 | P2b 回放：三类序列 × {ByteTrack, BoT-SORT}，按 §3.4 七类互斥结局报 8 s/13 s 窗口保持率（唯一分母 D = `KEPT`+`ID_SWITCH`+`LOST_BEYOND_BUFFER`+`UNRESOLVED_END_MISS`；七类计数与 `drift_return` 子计数；每（序列, W, 算法）及每距离桶的守恒式 |V| = 三排除类 + D 断言相等）、ID 切换、碎片、最长同 ID 秒数、漏检段长分布、帧间隔分位与 `track_buffer` 秒数换算；调用接口逐字如 §3.4（无 `frame_rate`，每帧一次 `update(boxes, img)`，`frame_id == n`），参数为库默认且逐字入摘要；测试 `adapter_boxes_fields`、`one_update_per_frame`、`library_buffer_boundary` 与 §3.4 的 11 条具名反例红绿；`lap` 未装即 `N/A(LAP_UNAVAILABLE)` 并回用户 | artifact:docs/evidence/P1-ENG-FAST-001-replay.json；test:tests.test_eng_fast_replay | K4 | 2026-09-24 |
| AC-6 | P3 四臂表：按 §3.5.1 分组/分母/层报 A(base)/A(C2)/B/C/D 成绩、误报率、`INVALID`/`NO_CANDIDATE_MATCH`/`K0` 计数、§3.5.4 配对 2×2 表；臂 A 零新查询（既有文件 sha 入摘要）；B/C 按 §3.5.3 闭集合并，prompt、解码参数、token、时延逐行；查询计数与 §5 对账，`STOPPED_FORMAT`/`NOT_RUN(BUDGET)` 行数如实列出；摘要不含任何「上界」或乘积字段 | artifact:docs/evidence/P1-ENG-FAST-001-vlm-arms.json；test:tests.test_eng_fast_vlm_parse（含分页合并闭集与 `INVALID` 用例） | K4 | 2026-09-24 |
| AC-7 | P4：报告一节写明 DETECT-001 验收 4 缺口原文、qual-3 数字读法（节奏≠召回、决策计数≠FP）、本项复用的冻结件与差异、本项不闭合该缺口、待复现风险清单 | artifact:docs/evidence/P1-ENG-FAST-001-report.md §P4 | K4 | 2026-09-24 |
| AC-8 | 读数表：报告按 §6.2 逐格填值并附证据指针，每格附「不可推出」一栏原文，不含「换栈/保留」结论句 | artifact:docs/evidence/P1-ENG-FAST-001-report.md §读数表 | K4 | 2026-09-24 |
| AC-9 | 只读与账目：`runtime/` 零写入（前后 `git status --porcelain` 与哈希清单相同）、零 Play/ID、产物只在 `outputs/eng-fast/` 与 `docs/evidence/`；启动/查询（基线与重试分列）/下载（只允许 §5 的 `lap` wheel 1 次，版本、sha、字节入账）/pip 安装/传输逐项对照 §5 信封写入 `-ledger.json`，任一越界即停 | artifact:docs/evidence/P1-ENG-FAST-001-ledger.json；cmd:git status --porcelain | K4 | 2026-09-24 |
| AC-10 | 时延：Mac CPU 与 MPS 各 ≥300 帧的检测 p50/p95、DINOv2 单裁图、关联 `update`；摘要不含任何 Jetson/TensorRT/5060 检测时延字段 | artifact:docs/evidence/P1-ENG-FAST-001-latency.json | K4 | 2026-09-24 |
| AC-11 | 冻结件零改动：候选 diff 不触及 `Assets/`、`config/`、`controller/`、`tools/eng_sft/`、`tools/run_detector_scouting.py`；全套测试写 `-tests.log`，区分基线既有失败与本批新增 | cmd:git diff --stat <base>..<candidate>；artifact:docs/evidence/P1-ENG-FAST-001-tests.log | K4 | 2026-09-24 |

## 5. 预算信封（申请值；`ACCEPTED` 后由用户逐字授权入账，缺项视为 0；成功、失败、重试、smoke 全部计入同一上限，耗尽即停）

| 项目 | 上限 |
|---|---|
| Consuming | **no** |
| scenario/session/run ID | 0 |
| Unity Play | 0（含诊断 Play 0） |
| 模型 API 次数 | 0 |
| 训练 GPU·h | 0 |
| 本地模型进程启动（Mac，`.venv-yoloe`） | YOLOE ≤ 10、DINOv2 ≤ 8（含失败；每次进程启动计 1，不按帧计） |
| 5060 模型启动 / 查询行数 | base 启动 ≤ 4；查询 ≤ **1,700** = 臂 B 929 页 + 臂 C 588 行 + `INVALID` 重试 ≤ 183（smoke 为正式前 32 行，不另计）；每查询 ≤ 64 新 token；上限到达即停，剩余记 `NOT_RUN(BUDGET)` |
| 下载 | **1**：`lap>=0.5.12` wheel（P2b 必需，事实 21；`uv pip install` 进 `.venv-yoloe`，记版本/sha/字节；若无预编译 wheel 而需源码编译则停下回用户，不另装编译链）。可选行（默认 0，须用户逐字签发；§7 裁定 (c)）：T1a MobileCLIP-BLT 1 次；T1b `yolo11n.pt` 官方资产 1 次或从 T7 副本导入 1 次（核 sha） |
| 传输（Mac ↔ 5060，局域网/T7） | 代码与清单 ≤ 300 KB；臂 B/C 预渲染图包（929 张网格图 + 588 张叠框图）+ 448 帧 ≤ 150 MB；回传结果 JSONL ≤ 5 MB；逐文件 sha 清单 |
| pip 安装 | Mac 1（`lap`，与上一行同一件事，不另计下载）；5060 0（`.venv-language` 已齐） |
| 复算 / 训练 / Jetson / 云端 / 发布 | 否 |

信封内的工程性重试与 supersession 由接受角色在「决策记录」记一行归因；任何越界回到用户。LOOP-001 阶段 B 剩余额度与本项无关、不得挪用。

## 6. 限制、不承诺与预注册读数表

### 6.1 限制与不承诺

1. 全部数字是**离线、桌面、oracle 候选或 oracle 参考**条件下的描述性结果：P1 的 T0-oracle 与 DETECT-001 一样只是「oracle-pointed 可检测性上界」；P3 的 B/C/D 用 oracle 候选集，§3.5.4 的配对表只是同行交集，**不是**任何链路的成功率或上界，也不预测检测器候选下的 VLM 成绩。
2. gold 为 amodal 投影 AABB（`UNVERIFIED`）；贴边/部分露出对象的 IoU 天然偏低，本项不裁定是标注还是模型问题；目录帧的距离是相机轴向深度，与 scout/BODY 的斜距分表、不混算。
3. C2 adapter 不套用到 B/C 臂，因此 B/C 与 A(C2) 的差异混合了「格式」与「微调」两个因素；A(base) 才是 B/C 的同模型对照，报告必须两列都给。
4. 序列回放不含 Unity 同机负载、不含云台/机身运动闭环、不含 5 Hz 实时约束、不含 K1 发布门；ID 保持率只说明关联层在归档几何上的离线表现，不是闭环跟踪主张，不等同真实指定期，也不主张替代 NanoTrack 后 `C_track` 会改善。
5. 脚本红立方体只有 BODY-001 九段与 scout 序列的样本（同一锚点、同一路线）；换其他路线/光照没有证据。
6. 不主张 Jetson/TensorRT 性能；不主张开放词表、真实航拍、跨环境；不闭合 DETECT-001 验收 4；不改任何 LOOP-001 verdict。
7. 单次 greedy、单 seed；bootstrap CI 只是描述性区间（5 Hz 近重复帧多）；不冻结任何合格线。
8. T0-bank 的参考库由 §3.2.1 规则机械选出，不按结果调整；若库路径不支持多帧平均，按预注册回退并标注，不视为失败也不据此改规则。
9. 评 scout-1 与 arm A 时参考池只有 a2（原子隔离的必然结果），T0-bank 在默认几何来源上的召回是「单来源参考库」条件下的数字，换更丰富的参考库可能不同；`same_instance_in_bank` 子行只用于揭示同实例回流的影响，不据此裁定。
10. 保持率的分母把 `UNRESOLVED_END_MISS` 算作未保持，读数偏保守；该类与 `LOST_BEYOND_BUFFER` 的占比要与 R1 远端召回并读，不能把远端漏检造成的低保持率读成关联层缺陷。

### 6.2 预注册读数表（报告逐格填值；「参考线」只是既有证据的对照，不是门；每格「读法」都是条件句，「不可推出」为硬约束）

| 格 | 取值来源 | 参考线（既有证据） | 读法（条件性、描述性；供用户裁定） | 不可推出 |
|---|---|---|---|---|
| R1 默认几何远端召回：T0-bank 在 scout-1 + BODY-001 的 `≥50 m` 与 `≥65 m` 档、双 IoU | AC-2 | scout-1 T0-oracle 0/45（≥65 m）；VLM C2 S 层 36.7% | 若远端召回接近 0，则预训练检测器不能覆盖默认路线远端，换栈需另立数据/模型工作；若明显非零，则「持续检测」在远端有输入 | 任何闭环跟踪成绩；在线 5 Hz 下的召回 |
| R2 脚本红车召回：BODY-001 全档、S/M/L | AC-2 | 无既有证据（事实 7） | 若目录车可检而红立方体不可检，则演示目标本身是换栈的阻断项，需换目标外观或换样例策略 | 换成网格车后的召回 |
| R3 FP/帧（各来源，描述性） | AC-2 | 无同口径既有证据（qual-3 的 NO_CANDIDATE/TENTATIVE 是三门决策计数，**不是** FP，不并列） | 若 FP/帧高，则关联层每帧要在更多干扰候选中匹配；配合 R5 读 | 换 ID 频率（那由 R4 直接测量） |
| R4 8 s / 13 s 窗口 ID 保持率（scout-4 / scout-1 / BODY-001，两算法） | AC-5 | 指定→确认实测 8–13 s（事实 8）只给出窗口长度的来历 | 离线回放是**必要条件**读法：若离线也保不住，则在线更难；若离线保得住，只说明归档几何上关联层不先天失败；分母含 `UNRESOLVED_END_MISS`（保守），四类判定计数并列，低保持率须与 R1 并读以区分「检测不到」与「关联丢 ID」 | 在线可行性；真实指定期的保持率；同机负载下的表现 |
| R5 静态 margin `≥0.1` 通过率（S/M/L） | AC-4 | scout-4 174/187、scout-1 0 机会 | 若 S 层通过率低，则同类多车场景仍需 ReID 或人工，定局 ④ 不变 | 训练后的 ReID 能力 |
| R6 臂 B/C 相对 A(base) 与 A(C2) 的 S 层差值（oracle 候选条件下） | AC-6 | A(C2) G1 S 36.7%、G1t/G2t 65.2% | 若 oracle 候选下裁图/编号选择显著高于整帧，则值得另立探针用**检测器候选**复测 B/C；若不高，则裁图放大不是 S 层的出路 | 检测器候选下的成绩；任何架构结论 |
| R7 臂 D 相对各 VLM 臂（oracle 候选条件下） | AC-6 | — | 若 D 在 G1/G2 接近 B/C，则这两类指令的选择步骤有无 VLM 替代方案值得另测；G3/G4 另看 | 「不需要 VLM」；检测器候选下的成绩 |
| R8 Mac 检测 p95 与 5 Hz 预算 200 ms | AC-10 | DETECT-001 detector 74–98 ms（CPU） | 若 p95 > 200 ms，则桌面 5 Hz 持续检测在本机不成立（与 Jetson 无关）；若 ≤，则只说明单模型单进程可达 | 同机 Unity 负载下的时延；Jetson 时延 |

## 7. 必经停点

- **`K4`**（数据划分/标签/对外指标：分桶口径、gold 口径、四臂评分与读数表）单候选一次通过：核对轮 `C1@K4` → 新鲜上下文复核 `R1@K4`。
- 不触发 `K1`/`K2`/`K3`（零运行时代码、零协议、零控制、零模型决策接入）；不触发 `K5`。
- 纯离线 `UNITY_NA` 分类申请已获接受侧裁定（不影响 Unity 运行行为），仍须复核角色附议；`DONE` = 实现者证据（AC-1…11）+ `R1@K4` 通过 + `UNITY_NA` 附议。
- D1 提请 (a)–(d) 的裁定已消费：(a) 分桶边界与双 IoU 沿用，斜距/轴向深度分表（§3.1）；(b) 分页合并按 §3.5.3，`max_new_tokens=64` 只作申请参数；(c) T1a/T1b 可选、默认不执行，其额外下载额度为 0（D3 必需的 `lap` wheel 申请另见 (j) 与 §5）；(d) `track_buffer` 内同 ID 恢复算保持，无起点绑定与不完整窗口不进分母（§3.4）。
- D2 提请 (e)–(g) 已由 D3 接受侧采纳：(e) §3.2.1 参考库贪心规则与 ≤6 帧上限；(f) §3.5.3 的 `INVALID` 单次重试与 183 行余量；(g) 若查询上限先于四臂完成到达，AC-6 记「部分完成」并回用户，不自动追加。
- D3 提请 (h)–(j) 已由接受侧采纳：(h) §3.2.1 隔离单位取近重复原子、评 scout-1/arm A 时池仅 {a2}、库不足的 `BANK_PARTIAL`/`N/A(BANK_EMPTY)` 与 `same_instance_in_bank` 子行；(i) §3.4 七类结局与唯一分母，`UNRESOLVED_END_MISS` 计入分母不算保持；(j) §5 的 `lap` wheel 1 次列为必需信封申请项（唯一偏离「零下载」之处），安装失败即 P2b `N/A(LAP_UNAVAILABLE)` 回用户。

## 8. 只读试读与试运行数字（2026-09-23/24 本机只读；零写入、零 ID、零模型推理；YOLOE 仅 `torch.load` 读元数据）

| 对象 | 数字 | 用途 |
|---|---|---|
| scout-1 真值 | 705 帧、可见 659；斜距 25.0 / p25 28.9 / p50 47.7 / p75 60.1 / 73.4 m；≥50 m 312、≥65 m 86；短边 p50 25.7 px，<32 424 / 32–64 202 / ≥64 33 | P1 远端桶样本量；R1 |
| scout-4 真值 | 2,405 帧全可见；斜距 26.1–30.5 m；短边 p50 61.6 px，<32 0 / 32–64 1,390 / ≥64 1,015 | 良性对照；P2b |
| BODY-001 九段 | 9 × 128 帧 JPEG；真值 8,252 行，可见带框 5,856；斜距 25.0 / p50 40.9 / 73.4 m，≥50 m 2,310、≥65 m 537；短边 p50 32.6，<32 2,855、≥64 214 | 脚本红车桶；P2b 13 s 窗口（每段 25.6 s，末端删失起点占比将如实报） |
| 族划分（事实 16） | train {a2}；dev {scout-1, arm A, a1-s2, a7, rate, scene-val}；test {arm B, a3, a4, a6, a9, s004-*} | §3.2.1 参考池与留出 |
| 参考库候选 | train∪dev 单帧 L 层类别覆盖上限 4（a7 `frame_0000002550`，20 辆 `OK`；a7 另有 6 帧达 4 类）；红立方体 ≥32 px 帧：arm A 305、scout-1 235、a7 1,511、a2 1,133、a1-s2 1,082 | §3.2.1 预计 3–6 帧成库 |
| 帧目录 attempt-2 | 43,535 行；609 行的 448 帧 100% 联表；每帧 `OK` 车辆 0/12/55（min/p50/max），合计 6,597；≥2 辆同类 `OK` 帧按族：a2 698、a9 588、a6 566、a4 298、a3 269、a1-s2 220、a7 144、scout-1 77、s004-scout 45 | P3 候选集规模；P2a 帧对池 |
| 609 行 × 候选集 K（事实 17） | K=0 行 21；p50 14、p90 35、max 55；K>16 行 260、>32 行 67、>48 行 14 | 臂 B/C 规模 |
| 臂 B/C 精确查询数 | 臂 B `Σ_{K≥1} ceil(K/16)` = **929** 页；臂 C 588 行；合计 1,517；余量 183（1,700 − 1,517） | §5 对账；§3.5.3 停止处置 |
| 609 行评估集 | 448 帧 ID / 392 图；G3 类 110 行候选 1/2/3 = 36/64/10；`has_dynamic_target` 68 行；既有预测 base 609 + C2 609 行 | 臂 A 零查询；分组 |
| YOLOE checkpoint | `names` 80 个占位、无 `pe`、head `YOLOESegment` nc 80 → 无离线文本词表；VP 路径已跑通；`get_visual_pe`/`set_classes` 为库内公开接口 | §3.2 T0/T1 划分、§3.2.1 |
| 关联库 | ultralytics 8.4.104 内置 ByteTrack/BoT-SORT，`with_reid: False`，零权重；`track_buffer` 默认 30 帧 | §3.4（导入期依赖 `lap` 缺失，见事实 21） |
| 划分原子（事实 19） | train {a2} 2,523 帧；dev 原子 6 族 13,144 帧（含 5 段 arm A post-run 各 128、scout-1 768）；test 原子 {m3-armB}（4 段 arm B post-run 各 128 + void 128）与 7 族 8,450 帧（含 scout-4 2,405）；`pairwise_disjoint = true` | §3.2.1 参考池 |
| 跟踪器接口（事实 20） | `BYTETracker(args)`/`BOTSORT(args)` 无 `frame_rate`；`update(results, img)`；`max_frames_lost = track_buffer = 30` 调用；移除条件 `frame_id − end_frame > 30` 在关联之后 | §3.4 实装接口与边界红绿 |
| `lap`（事实 21） | `.venv-yoloe` 无 `lap`/`scipy`/pip；`import ultralytics.trackers` → `ModuleNotFoundError: lap`；`uv` 可用 | §5 必需安装 1 次 |
| 桌面时延先例 | detector 74–98 ms、外观门 21–26 ms（CPU） | R8 量级 |
| 5060 | base 零样本 4 行 p50 1.73 s；1,517 行基线约 45 分钟量级（未实测，仅投影） | §5 |
| 内存投影 | Mac：YOLOE-11s + DINOv2-S 与 DETECT-001 同量级（已在 16 GB 本机跑过）；5060：bf16 2B 已跑通；网格图 4×224 = 896 px 边，视觉 token 数按处理器实际记录（可能高于 640×480 的 300） | 可行性 |

## Contract conformance（核对表）

**`C1@K4`（2026-09-26，接受侧只读核对）：交 `R1@K4` 独立复核。** 候选为同名 K4 实现提交（从 git 日志解析），基线为其父提交；核对范围为该提交完整 31 文件 diff（含 `.gitignore`、状态板、`tools/eng_fast/`、`tests/test_eng_fast_*.py`、全部同名证据），以及理解变更所需的冻结适配器、跟踪器与授权来源。证据 JSON 全部解析核对结构、分母和账目；本轮未运行实现测试、模型或 Play，未修改 AC-1…11。

| 验收项 | 结论 | 依据与边界 |
|---|---|---|
| AC-1 | 满足 | `-inputs.json` 的五来源帧/真值清单、两库参考身份与五组原子/SHA 断言均在；`inputs.py:stage_inputs` 的来源查表及 `tests/test_eng_fast_inputs.py` 的同原子反例。scout-1 实存 v1 schema 按 IR-2 披露，未当作 v2 冒称。 |
| AC-2 | 满足 | `-recall.json` 的斜距/轴向深度两表、双 IoU、种类/实例/短边/距离交叉格及适用域 N/A；`recall.py:bucket_table` 与报告「P1 分桶召回」。FP/帧按 §3.3 逐来源单列，且披露 scout/BODY 真值范围。 |
| AC-3 | 满足 | `-recall.json:legacy_alignment`：scout-1 0/45、scout-4 172/187，逐 tick 命中差异 0；`recall.py:legacy_alignment`。 |
| AC-4 | 满足 | `-margin.json:summary`：1/5/13 s 各 300 对计分，嵌入身份与分层/分类别结果在；`margin.py` 与具名测试。 |
| AC-5 | 满足 | `-replay.json` 的 11 序列×两算法、8/13 s 七类计数、逐桶守恒及帧调用/间隔；`replay.py:window_outcome` 与 `tests/test_eng_fast_replay.py` 的 11 条具名反例和钉版库适配测试。IR-8 的库边界实测与合同事实 20 冲突，按 §3.4「实测为准」披露，指标仍按合同 L≥31 保守记失并单列 L=31 同 ID 漂移；交复核重点核验。 |
| AC-6 | 满足 | `-vlm-arms.json` 含五臂各 609 行、1,201 查询逐行记录、分组/分层与配对表；`inputs.py:candidate_set`、`vlm_arms.py`、`vlm_remote.py` 和具名测试。IR-1 依 §3.5.1 正文「OK 可指称车辆」与帧级绑定目标取候选，K0=26、B/C 各 583；§5 的 929/588 是与正文冲突的试读数字，账本仍以用户签发的 1,700 总上限及 183 重试上限约束，实际 1,166+35 未越界。候选定义与计数差异已在报告/交接文件披露，交复核重点核验。 |
| AC-7 | 满足 | `-report.md`「P4 与 DETECT-001 的关系」逐项列验收 4 未运行、qual-3 数字、冻结件、差异和复现风险。 |
| AC-8 | 满足 | `-report.md`「读数表」R1–R8 各有证据、条件性读法和「不可推出」栏，未给换栈/保留结论；R1 目录车斜距缺值明示为无格。 |
| AC-9 | 满足 | `-ledger.json` 的前后 97,505 文件全树哈希相同、`runtime/` Git 状态为空，启动/下载/安装/查询/传输逐项在信封内；零 Play/ID/API/训练。 |
| AC-10 | 满足 | `-latency.json`：Mac CPU/MPS 检测各 320 帧、DINOv2 各 300 裁图、ByteTrack CPU 768 次 update；报告明确 MPS 关联栏未测，不产生其时延主张，也无 Jetson/5060 检测数字。 |
| AC-11 | 满足 | 完整候选 diff 未触及冻结的 `Assets/`、`config/`、`controller/`、`tools/eng_sft/`、`tools/run_detector_scouting.py`；`-tests.log` 记录停点全套 Ran 1578、9 项既有环境 error、1 项先存归档 failure、本批新增失败 0，钉版环境的本批 44 条通过。此处只核对实现者日志，未重跑。 |

**IR-1…17 裁定（实现读法；不是 AC 修订）：** IR-1 接受车辆闭集与帧级动态目标，原 929/588 不可再当实际查询数；IR-2 接受实存 scout-1 v1/v2 识别并逐文件记 schema；IR-3 接受有 `distractor_id` 时的实例标记；IR-4 接受确定性帧对与 300 对上限；IR-5 接受 T0-bank、缺真值帧不入 V 与窗口内 TRUTH_GAP 计法；IR-6 接受臂 D 每对象 20 张确定抽样；IR-7 接受灰色无彩桶与已验证车辆原型；IR-8 接受 30/31/32 帧实测披露，但保持合同 L≥31 的判定阈值及漂移子计数；IR-9 接受固定渲染与 prompt 字节身份；IR-10 接受首 32 行首次 INVALID 判停及基线后重试；IR-11 接受臂 A 未匹配即失败；IR-12 接受已披露真值范围下的描述性 FP；IR-13 接受缺轴向深度入 NA；IR-14 接受混合参考池的聚合标注与来源分行；IR-15 接受 `runtime/` 全树哈希；IR-16 接受 LEGACY_ONLY 查询但排除报表；IR-17 接受 scout-1 前 320 帧与预热剔除。上述只限定本候选的证据读法，不授权追加查询、改动预注册指标或扩展合同范围。

**预复核关注项（均为待核实主张，不作独立 finding）：** (1) `inputs.py:candidate_set`、`run_more.py:stage_pack/stage_score` 与 `-vlm-arms.json`：逐行验证车辆闭集、帧级动态目标、gold 覆盖及 583/583 查询重算，特别核对 IR-1 处与合同 §5 试读数字的冲突；(2) `replay.py:window_outcome`、`tests/test_eng_fast_replay.py:test_library_buffer_boundary` 与 `-replay.json`：在钉版库核验 31 帧仍同 ID 的实测、L≥31 保守记失和漂移子计数，判断报告的「保持率」标签是否充分披露这一差异；(3) `-tests.log` 与 `-ledger.json`：核实全套 1 failure/9 errors 的先存归因、前后 `runtime/` 只读清单与信封总/重试扣额；(4) `-latency.json`：确认 AC-10 的 MPS 栏只对应检测与 DINOv2，关联 update 仅 CPU，报告未外推。

## 决策记录

| 日期 | 轮次 | 结论 | 理由指针 |
|---|---|---|---|
| 2026-09-23 | D1 | `PROPOSED` | 账本 2026-09-23 探针清单；用户追问答复「静态 margin + 序列回放（推荐）」；§0 事实 1–15 |
| 2026-09-24 | D1 | `REVISION_REQUESTED`；engineering-v1 申请尚未裁定生效 | 下列 AR1-1…5；零实现、零下载/启动/查询/传输；§5 仍只是申请值 |
| 2026-09-24 | D2 | `PROPOSED`（回应 AR1-1…5） | 头部「AR1 → 本稿」映射；§3.2.1/§3.2.2/§3.4/§3.5.1–3.5.4/§5/§6.2/§8；事实 16–18；零实现、零下载/启动/查询/传输 |
| 2026-09-24 | D2 | `REVISION_REQUESTED`（第二次；上交用户二选一）；engineering-v1 申请未裁定生效 | D2 已修正 AR1-1/2 的来源域与分组、AR1-4/5 的预算和读法；AR2-1…3 仍使参考留出和 ID 保持率不可按字面复算。§7 (e)–(g) 未裁定；§5 仍是申请值，零实现/消耗 |
| 2026-09-24 | 用户 §4.2 (a) | 保留范围并修正 AR2-1…3；不授予执行额度 | 账本同日「用户处置第二次设计退修：保留范围并修正 AR2-1…3」（本构思会话 AskUserQuestion 所选选项） |
| 2026-09-24 | D3 | `PROPOSED`（用户 (a) 处置后修正 AR2-1…3，设计退修计数 2 保持） | 头部「AR2 → 本稿」映射；§0 事实 19–21；§2.2-7 / §3.2.1 / §3.2.2 / §3.4 / §3.6 / §4（AC-1/2/5/9）/ §5 / §6 / §7 (h)–(j) / §8；零实现、零下载/启动/查询/传输 |
| 2026-09-24 | D3 | `ACCEPTED`；`engineering-v1` 生效，AC-1…11 与 `K4` 接受；纯离线 `UNITY_NA` 分类申请成立，关闭仍须复核附议 | 用户 §4.2 (a) 授权仅保留范围并修正；AR2-1→§3.2.1/AC-1/2，AR2-2→§3.4/AC-5，AR2-3→§3.4/AC-5 与 §5；§7 (e)–(j) 按本稿采纳；§6.1/§6.2 为主张上限；§5 仍是申请值，不签发下载、安装、启动、查询或传输额度 |

**接受侧裁定边界：** `K4` 只覆盖离线数据划分、标签与读数口径；不触发运行时 K1–K3，也不构成换栈结论或旧里程碑关闭。`UNITY_NA` 的理由是本项仅新增离线工具与报告、不改 Unity/控制器；最终能否用于 `DONE` 须由独立复核在 `R1@K4` 附议。`lap` 导入失败或库边界红绿不符时按 AC-5 如实停/报，不以未测 P2b 数字填满读数表。下一步由用户按授权账本逐字签发或拒绝 §5 信封，签发前实现与任何下载、安装、模型启动、5060 查询及传输均不开始；暂停的 `P1-ENG-LOOP-001` 与其余额不变。

### D2 退修要求（接受角色；不自行发起 D3，交用户二选一）

1. **AR2-1｜参考库留出规则冲突。** §3.2.1 先要求评估时排除「同族或同会话」参考帧，后又规定 BODY-001 arm A 第 t 段仅排除该段、其余 arm A 段可作参考。若这些段同属 `m3-armA` 族，后一规则允许同族回流；AC-1 的帧 SHA 零交集只能排除同帧，不能证明族隔离。须按 `family_assignment` 明定 BODY-001 各段与参考池的族/会话映射、冲突时的排除优先级及库不足的确定处置，不能以「留一段」替代已宣称的同族排除。
2. **AR2-2｜8/13 s 保持率的分母与末端漏检未闭合。** §3.4 把有起始 ID 且末端时间足够的窗口称为「合格起点」，但又把窗口内 `TRUTH_GAP` 排出分母，最终公式仍除以「合格起点数」；两种分母会得出不同保持率。窗口末仍在漏检且段长 ≤ `track_buffer` 时，字面规则又可判保持，尽管没有同 ID 恢复证据。须写明互斥分类顺序、最终分母和缺口计数守恒；未观察到同 ID 恢复的末端漏检不得默认为保持，并给 AC-5 相应反例。
3. **AR2-3｜回放所述库接口与实装不符。** §3.4 要向 `BYTETracker`/`BOTSORT` 传 `frame_rate`，但当前钉版 `ultralytics/trackers/byte_tracker.py` 的构造器只收 `args`，`max_frames_lost = args.track_buffer`，按 `update` 调用帧数计。须明确实际调用接口与秒数仅用于报表的换算，或明确具名适配层及其验收证据，不能让实现角色自行猜测参数行为。

按 workflow §4.2，第二次退修后不再由接受角色自行要求 D3。用户须选择：(a) 接受当前范围并逐条保留上述已知缺口及相应主张上限；(b) 关闭为负结果记录。用户选择前不裁定工程轨道、不签发执行信封、不启动实现，也不改变暂停的 `P1-ENG-LOOP-001`。

**用户处置（2026-09-24）**：用户在构思会话选 (a)「保留范围，落 D3 闭合 AR2-1…3」（账本同日条目逐字）；D3 见上文，接受角色审查 D3 不视为第三次自行退修。

### D1 退修要求（接受角色；交构思角色 D2）

1. **AR1-1｜修正“乘积上界”的数学口径。** §3.5、AC-6、§6.1-1、R6 把 oracle 候选臂成功率与 T0 召回率的乘积称为真实链路上界；两个边际的乘积既不是联合成功率，也不是其一般上界。D2 删除该上界主张，分别报告同口径边际；若要给配对诊断，须在相同评估行上定义检测命中与 oracle 臂成功的交集及分母，并注明它不能证明改用检测器候选后的 VLM 成绩。R6 的架构读法不得从 oracle 成绩直接推出。
2. **AR1-2｜闭合 P1/P3 报表的来源与分组域。** §3.2 明定 T0-oracle 仅适用 scout-1/scout-4，AC-2 却要求它在 BODY-001/目录帧出数；按实际适用域逐格列 `N/A` 和理由，不以缺格冒充失败。§3.1 的目录 `camera_depth_m` 不能标成斜距；§3.5、AC-6 的“609 行 G1–G5 × S/M/L”须逐字定义 G3′/G1t/G2t/G3t/LEGACY_ONLY 的归组或排除，以及 G5 的 NA 层和各分母。候选命中 gold 对象不等于框 IoU=1，须改正成功口径文字。
3. **AR1-3｜使 P2b 窗口保持率可复算。** §3.4、AC-5 明定：起点无绑定 ID 如何计；可见起点距序列末端不足 8/13 s 如何纳入分母；漏检后以同一 ID 恢复与未恢复各如何计；`track_buffer` 是帧数时如何按实际帧间隔处理不规则时间戳。给出至少起点未绑定、末端删失、buffer 内恢复及 ID 切换的具名反例，避免把缺少完整窗口的起点计成保持。
4. **AR1-4｜闭合臂 B 分页与预算的失败路径。** §3.5 的“所有页 unique 恰一”有两种读法；写明恰一页 unique、其余页 none 的合并，以及 K=0、多页 unique、任一页 ambiguous、无效 JSON/越界索引的确定结果。§8 目前只把 Σceil(K/16)≤900 称为估算：用已试读的 609 行清单给出准确查询数（含相同帧不同指令的行），再与 §5 的 1,700、smoke/重试余量对账；不足时明确停止与未完成 AC-6 的处置，不靠超额查询补齐。
5. **AR1-5｜约束预注册读法和参考输入。** R3 将 FP/帧与 qual-3 的 NO_CANDIDATE/TENTATIVE 次数并列并推断换 ID，这两者不是同一指标；R4 将离线回放与真实指定期直接等同；R6/R7 从 oracle 候选对照推断架构或“不需要 VLM”。D2 将这些格改成条件性、描述性的用户决策提示，列明不可推出的闭环结论。§3.2 T0-bank 的参考帧/框须有确定选择规则和输入身份清单，逐受测族说明来源及留出关系，防止评估族回流参考库。

§7 提请的裁定：(a) §3.1 的 S/M/L、`<35`/`35–50`/`50–65`/`≥65` 与双 IoU 阈值可沿用，但须按 AR1-2 区分轴向深度；(b) 分页合并待 AR1-4，`max_new_tokens=64` 可留作申请参数而非格式成功保证；(c) T1a/T1b 均保持可选、默认不执行，下载额度仍为 0；(d) 允许把 `track_buffer` 内漏检后的**同 ID 恢复**列为窗口保持，但须按 AR1-3 排除无起点绑定与不完整窗口。工程轨道仅在后续 `ACCEPTED` 时裁定；本轮不得启动实现或动用 §5 信封。
