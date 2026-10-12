# P1-ENG-LOOP-001 — 受限语言选框闭环接入：三态结果 → 人工确认 → SOT 播种（结果帧初始化后追平）→ 语义核验提醒 → 人工判丢与重新指定（电脑端可复现；Unity 单字段例外见 R-B1）

Status: CLOSED_SUPERSEDED（2026-09-28 接受侧依用户 D.3 收口；Lifecycle ENDED；由未来 P1-ENG-ACQ-001 取代；非验收通过。D4 `ACCEPTED`、engineering-v1 合同与 R7 `PASS_WITH_NOTES` 保留为历史；AC-3 修订 3/AC-12 修订 7 未实现，C7/R8 未开；F3/F8 `SCOPE_GAP`/OPEN，AC-13…15 正式 Play `NOT_RUN`；承接与作废余额见「收口裁定」）
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（Claude Code `/fable`，Fable 池）
Created: 2026-09-19
Last updated: 2026-09-28

> **来历**：`COORD-010` §5 拟议发布顺序的第一步「电脑端可复现闭环」，至今零代码。用户 2026-09-19 在监督会话点名
> 「下一步可以接入闭环开始测试了」，并在本构思会话逐题确认五项范围定局（账本同日条目
> 「P1-ENG-LOOP-001 — 立项点名与五项范围定局（方向层，不授予执行额度）」，逐字为 AskUserQuestion 所选选项）：
> ① 只立闭环接入，Jetson 探测不立项；② VLM 宿主**先测再定**（接口与机器无关，离线阶段实测 Mac MPS 与 5060 后按预写规则选）；
> ③ Play 演示**以动目标红车为主**，静止布局车只验播种链路与歧义路径，Unity 零改动；④ 丢失后**仅人工重指定**，不做任何自动重播种；
> ⑤ 停点**只 K1+K3**，K5 发布打包另立小项。D1 退修后用户同日追加定局 ⑥（账本「P1-ENG-LOOP-001 — VLM 定为辅助系统」）：
> **VLM 是辅助系统，提醒时决策主要由人负责**——于是 VLM 承担两个事件触发角色：A 语言指定者、B 语义核验者（§3.6），
> 都不进控制回路，播种、判丢、重指定全由操作者决定。点名与定局都是方向层，不是执行授权；§5 为申请值，执行信封另由用户逐字入账。
> 承接 `P1-ENG-ASSET-001` 报告 §5 的 10 条输入条件与缺口 G-1…G-6（G-7 不做）；复用 `P1-ENG-SFT-002` 的 prompt v2、
> 严格解析器、三态协议、609 行冻结评估集与候选 2 adapter（C2）。不依赖 `P1-ENG-SFT-003`。
> **AR1 → 本稿（D2，2026-09-19；D1 裁定原文保留在「决策记录」）**：AR1-1 → §3.3 四个检查点（查询/返回/确认/追平结束）、
> 可静音发布器、帧差下界与墙钟守卫、确认时重核图像哈希与元数据，AC-2/3/4 改为对桥文件写入断言，§7 说明为何不申请 K2 并交接受裁定；
> AR1-2 → §3.4 八态 × 九动作完整表（未列组合一律 `REQUEST_INVALID`）、请求回执与世代号、旧段只在进入 LOST/REINIT_REQUIRED/TERMINAL 时
> finalize 一次、stop 语义、无新帧与迟到回包的有界退出，段内跟踪器自恢复按定局 ④⑥ 不算恢复（疑似状态只有人能解除）；
> AR1-3 → §3.5 统一推理适配（一行 rows 调既有 `predict_rows`，保留 `finish_reason`）、回放按盲索引连接、重复键规则、身份核对，§8 连接数字；
> AR1-4 → §3.3 宿主决策表与 K_max 改写（先减余量再封顶）、模型形态三枚举（合并失败回未合并 adapter）、测量口径与固定超时、§3.5 含 ambiguous 的等价判定；
> AR1-5 → §3.6 语义核验（角色 B）给出丢失信号，AC-13 改为证据类别 E1–E3 与 FAIL/BLOCKED 归属，AC-14 列全结局，分数/贴边只作触发不作决策；
> AR1-6 → §5 成功/失败/重试全计的总计口径、阶段 A 只写隔离目录、删除 609 行复算、§7 合并停点短名 `K1K3` 与阶段 B 修复回路。
> §7 三项答复的消费：常数仍为申请值；AC-14 按协议呈现与如实报告验收、歧义识别成功单列；609 行复算删除。
> **AR2 → 本稿（D3，2026-09-19；用户 §4.2 (a) 处置见账本「用户处置第二次设计退修：保留范围并修正 AR2-1…6」；D1/D2 裁定原文保留）**：
> AR2-1 → §3.3 发布最终门（写桥时重核 `L_w`/元数据身份，失败即 `PUBLISH_REJECTED` 并 finalize）、发布收据为唯一证据（运行日志 `published_*` 只是意图）、`T_stall` 停帧与坏元数据 `ValueError` 映射、AC-2/3/4 重写；
> AR2-2 → 删除 `--on-suspect hold`，§3.4 边界表写明提醒/`dismiss`/`raw_*` 都不碰发布门，控制只由播种瞬态与人工/协议 finalize 改变，§7 不申请 K2；
> AR2-3 → §3.2 请求 `session_id`/`token`、单槽回执与 `pending`/`SUPERSEDED`、会话锁；`query_id` 全会话唯一；§3.4 自带 `LanguageWorker`（在途 + 一条 pending、`T_hard`/`worker_stuck`、stop join）；
> 失败包可空规则、`retry_exhausted` 带 `last_status`、`reason` 补 `metadata_invalid` 等、AC-6 分离尝试计数与帧递增；
> AR2-4 → §3.6 配对帧 = 本段最近已处理帧（非 latest）、同帧不重复、无框/滞后/身份失败的 `inconclusive` 出口、单计数器（none/drift 交替累计）、`verify_epoch` 使人工处置后旧回包失效；
> AR2-5 → §3.3 三段预算 `K_ret + K_conf + K_pub`（人工确认 10 s 单列）、AC-13 具体操作（事实 16 的同锚点臂 A 可见率 0.578 为离画依据）与终态闭集（`NOT_TRIGGERED`/`MISSED_ALERT`/…）、目检绑定核验源帧、AC-14 补全结局与「确认 N/A」；
> AR2-6 → §3.3 先资格后分档、B/B 平局取 Mac、第二轮 `INVALID` → `FAIL`；§5 两机合并次数、诊断 Play 的会话/进程/查询计入同一上限。
> **AD3 → 本稿（D4，2026-09-19；用户处置见账本「用户处置 D3 审查残留 AD3-1…4」；D1/D2/D3 裁定原文保留）**：
> AD3-1 → §3.3 加载时快照（注入 `image_loader`：一次读取、哈希、复制进会话帧环）与写前守卫五项（JPEG 哈希重算、元数据时间、`L_w`、加载时刻墙钟 `T_pub`、同帧关联 `orphan_control`），
> 「不初始化」只限初始化前失败、批末发布位于函数返回前的措辞修正，§3.6 核验改用帧环副本，AC-2/3 同步；
> AD3-2 → §3.5 HTTP 改为提交/轮询式单工服务（`SERVER_BUSY`、服务端 `T_hard`、放弃结果不返回、idle 前不重入）、§3.2 CLI 写者锁与「恰一次」只限已接纳请求、`outcome` 七值闭集、
> `reason` 补 `bundle_missing`/`candidate_expired`/`operator_reject`/`publish_expired`/`orphan_control`，确认失败拆为 `REQUEST_INVALID`（不改状态）与 `candidate_expired`（拒绝候选），AC-1/5/8/17 同步；
> AD3-3 → §0 事实 16 收窄为「存在不利观察段的假设」并补评估器采样阈值、EVAL-001 与臂 B 饱和/下界限制，AC-13 拆 `E1_ALERT`/`E1_ACHIEVED`、按离画事件的裁定窗口与优先级唯一归类；
> AD3-4 → §3.8/§5 诊断会话 `--diagnostic`：零正式 ID、段日志写诊断根、不建 `runtime/runs/`、产物不进 AC-13…15，模型启动/查询仍共用上限；§7 新增「设计轮收口边界」提请。

## 0. 现状与只读事实（本会话只读核实，`file:line` 以 2026-09-19 HEAD 为准）

| # | 事实 | 依据 |
|---|---|---|
| 1 | `TrackLoop.initialize(frame_id, box_norm)` **一次性**：已初始化再调用即 `RuntimeError`；初始化直接从 `FrameRepository.load()` 读精确保留帧，框经 `clip_box_norm` 裁剪，跟踪器可拒绝 | `controller/track_loop.py:336-347` |
| 2 | `process_available()` 从 `last_frame_id+1` **逐帧追到 latest**；中间任一保留帧缺失 → `GAP` 终止；latest 回退 → `REINIT_REQUIRED` 终止；LOST 时 `state="LOST"`，恢复时记 `recovered` | `controller/track_loop.py:391-473, 560-561` |
| 3 | 状态闭集 `{"TRACKING","LOST","ERROR_REINIT_REQUIRED"}` 只进日志记录，桥文件 `tracking_observation.json` 不承载状态；`confidence_source` 闭集 `{"tracker","placeholder"}`，其他值判 `invalid_confidence_source` | `controller/track_loop.py:65, 942-943, 985-993`；`controller/tracking_entry.py:12-60` |
| 4 | 观测包 `tethered-tracking-observation/v1` 带 `expires_after_s`（默认 2.0 s）、`command_id`、`issued_unix_s`；Unity 三个接收器均按 `issued_unix_s + expires_after_s` 判过期，机身接收器过期即 `Hold()` | `controller/protocol.py:23-35`；`Assets/TetheredTracking/Scripts/BodyCommandReceiver.cs:43-59`、`TrackingObservationReceiver.cs:107` |
| 5 | Unity 保留 `retained_frame_count=128` 帧（可配 4…10000），`capture_hz=5.0` → **25.6 s 保留窗**；帧包 = `frame_<id>.jpg` + `frame_<id>.json`（`tethered-sensor-frame/v3`，`capture_monotonic_clock_id=system-stopwatch/v1`），`latest.json` 原子指针 | `config/scenario.default.json`；`Assets/TetheredTracking/Scripts/SensorFrameWriter.cs:106-124, 212`；`controller/sensor_protocol.py:7-43` |
| 6 | 既有可复用件：`FrameHistory`、`SingleFlightWorker`（零队列模型 worker）、`replay_tracker` 追平、`before_update` 换跟踪器；参数名 `maximum_result_age_s`/`catchup_timeout_s`/`frame_buffer_s` 是「迟到结果」语义的现成先例。**但**其三重门/fail-closed 是 DETECT-001 外观相似度逻辑，本项不套用 | `controller/reanchor.py:233-258, 572, 704`；`controller/reanchor_runtime.py:76-145, 281-327` |
| 7 | 跟踪器插件闭集 `csrt` / `nanotrack-v2`（`P1-TRACK-002` 冻结核心）/ `scripted`（测试替身）；CLI 播种入口 `--init-frame/--init-box`，run 清单 `p1-track-run/v1` | `controller/trackers.py:168, 378, 508-529`；`controller/track_loop.py:1580-1585`；`controller/run_log.py:16` |
| 8 | 目标车：脚本红车 `LoopTargetVehicle`（`speed_mps=2.0`，闭合路线 8 点）；93 辆目录车为静止布局车；`RateStudyDistractor` 只是评估域标记，不会动 | `Assets/TetheredTracking/Scripts/LoopTargetVehicle.cs:8-78`、`TargetVisualFactory.cs:33`、`RateStudyDistractor.cs` |
| 9 | 三态协议：prompt v2 `build_prompt(image, surface, g4, vocab)`（词表九类、颜色六色，G4 段释义 viewer's left/right）；解析 `parse_prediction` fail-closed（`status` 闭集 `unique/ambiguous/none`，框 `[x1,y1,x2,y2]` 整数 0–1000，candidates 2…8）；评分 IoU ≥ 0.5 | `tools/eng_sft/prompt_v2.py:26-60, 100`；`tools/eng_sft/parse.py:26-30, 56`；`tools/eng_sft/evaluate.py:31` |
| 10 | 微调 C2（adapter 69,788,264 B，sha `4044dd4f…2d37`，base `Qwen/Qwen3-VL-2B-Instruct@89644892…4203`）609 行正式评估：G1 76.7%（S 层 36.7%）、G2 81.6%、G4 82.6%、G5 none 率 79%；G3 严格成功 25%、歧义报告率 39.6%；G1∪G2 误报 none 11.6%、误报 ambiguous 2.3%、格式失败 0；功能门 `GATE_NOT_MET` | `docs/evidence/P1-ENG-SFT-002-eval-summary.json`（`metrics`、`verdict`） |
| 11 | 时延（HF transformers 逐 token、batch 1、adapter **未合并**，上界）：5060 base 零样本 prompt v2 4 行 p50 1.73 s / max 3.05 s；5060 adapter 未合并 p50 5.43 s / max 16.97 s；5090 云端 C2 未合并 609 行约 1.28 s/行。**Mac M4 MPS 未测**；本机 `.venv-yoloe` 有 torch 2.13.0（MPS 可用）无 transformers，HF 缓存为空 | `outputs/eng-sft/P1-ENG-SFT-002/selfcheck/…/selfcheck.json`；`docs/evidence/P1-ENG-SFT-002-eval-summary.json` `accounting.per_stage`；本会话 `ls ~/.cache/huggingface/hub` |
| 12 | `initialize` 结束时立即 `_publish_latest`：发观测 + follow 云台 `look_at`（由帧 N 的框与相机位姿求地面交点）；`process_available` 逐帧记录但只发布批末帧的观测与机身步，`self.state` 只在批末赋值 | `controller/track_loop.py:336-384, 536-602, 644-674` |
| 13 | 冻结 NanoTrack 核心无分数阈值（`score_threshold: None`）：只在跟踪器异常、返回失败、框无效或分数越界时报 lost；目标出画面后通常继续返回 ok | `controller/trackers.py:437-488` |
| 14 | 预测文件按 `row_id` 存行（含 `raw_output`、`finish_reason`）；盲索引 `eval.blind.jsonl` 只有 `frame_path/g4/row_id/surface/vocab`，无 gold；`parse_prediction(raw, finish_reason=…)` 靠终止原因判 `TRUNCATED`；`predict_rows` 以整行（`frame_path/surface/g4/vocab/row_id`）为输入 | `tools/eng_sft/parse.py:56-72`；`tools/eng_sft/train_lora.py:696-757`；§8 连接数字 |
| 15 | 既有 `SingleFlightWorker`：超时后线程仍 busy、不能提交第二任务（`ROUND_SKIPPED_BUSY`），超时后完成的结果记 `ROUND_FAILED_AFTER_TIMEOUT`；`predict_rows` 的 `should_stop` 只在行前检查，行内 `generate` 只受 `MAX_NEW_TOKENS`（160）约束，不可中断 | `controller/reanchor.py:704-817`；`tools/eng_sft/train_lora.py:720-745` |
| 16 | 默认场景锚点 `(132.0, 0.2, 117.0)`、悬停 25 m 与 M3′ 批 1 审计锚点相同；路线闭环周长 213.0 m，2 m/s 一圈 106.5 s；路线各点相对相机的离底角 2.3°–70.1°；M3′ 臂 A（机身 hold、follow 云台）五次 Play 的 `C_geom` `0.578/0.578/0.597/0.578/0.578`。**限度（D4，AD3-3）**：评估器的「几何可见」= 采样点可见比例 ≥ `minimum_visible_sample_fraction`（`CoverageEvaluator.cs:1011-1034`），低于阈值不等于整车离开预览画面；EVAL-001 纵横比缺陷仍在；臂 B 五次饱和、效应量只是下界、不形成跟踪改善主张（状态板冻结措辞、compare 证据 §D）。因此该数字只支持「同锚点 hold 下存在不利观察段」的**假设**，不证明离画事件必出现或持续到三次核验 | `config/scenario.default.json`；`config/p1-m3-body-001-anchor-placement.json`；`docs/evidence/P1-M3-BODY-001-compare.md:71-72`；`Assets/TetheredTracking/Scripts/CoverageEvaluator.cs:1011-1034` |

**设计原则（由事实 10–16 推出）**：模型会错——歧义场合六成不报歧义而直接挑一辆、贴边目标一成多误报 none、小目标层过半失败——
所以首次指定必须人工确认、none 只做有界重试、丢失后重指定默认人工；保留窗只是必要条件，秒级模型时延与追平耗时能否共同满足发布门仍待实际候选验证。
超出资格或截止按合同拒绝，不预先承诺宿主可用、追平成功或真实 Play 通过。

## 1. 目的与价值

在现有 Unity 车辆场景与 Python 控制器上，用一条受限自然语言指令把既有 NanoTrack-v2 跟踪器播种到**操作者确认**的那辆车上，
并回答四个可证伪的问题：

1. **绑定与追平（K1）**：VLM 在帧 N 上算出的框到 N+k 帧才返回时，系统是否只在 N 上初始化、随后追平到当前帧，且追平前不向 Unity
   发布任何由旧图推出的观测或控制；超过 K_max 帧、超过墙钟截止、帧回退、停帧或同 ID 换图的结果是否被显式拒收（`COORD-010` §5；ASSET-001 G-2/G-3）。
2. **三态显式呈现（K3，角色 A）**：`ambiguous` 是否作为候选集交给操作者选一、`none` 是否经有界重试后显式报「未找到」，而不是被吞掉或自动挑一辆（G-1）。
3. **语义核验提醒（K3，角色 B）**：跟踪中低频用同一指令重问当前帧并与同帧跟踪框比较，能否在目标离开画面、跟踪框漂移或指令不再唯一时给出
   「疑似」提示；提示不触发任何动作，由人确认或驳回（定局 ⑥）。
4. **丢失显式报告与重新指定（K1+K3）**：外部消费者能否从桥文件读到 `SUSPECTED`/`LOST`/`REINIT_REQUIRED` 及原因，并通过重新指定换新
   `track_id` 继续；旧 id 如何作废可追溯（G-4/G-5/G-6）。

VLM 在整条链路里是辅助系统：只提候选、只提醒；不当逐帧检测器（一到六秒一次，小目标层 36%）、不当身份仲裁者（分不清两辆同色同类车，需 ReID）、
不当恢复规划者（L2/L3 研究线暂停）、不写任何机身或云台命令。跟踪本身由冻结的 NanoTrack-v2 承担。

交付对应 `COORD-010` §5 首版闭集的前八项：可运行示例（CLI）、依赖安装说明、模型来源/版本、受支持指令说明、人工回退、
关键路径测试、固定评估集与结果（引用 SFT-002 609 行与 C2 结果，不新建、不复算）、失败案例。演示成品与许可/发布打包归 K5 另立。

## 2. 范围与不做的事

### 2.1 两阶段与交付

| 阶段 | 消耗性 | 交付 |
|---|---|---|
| **A 离线**（候选 1，`K1K3` 合并停点） | 否 | `controller/language_bridge.py`（三个桥文件 schema、闭集、原子读写、请求回执）；`controller/gated_publisher.py`（可静音发布器，§3.3）；`controller/language_selector.py`（`InferenceAdapter` 统一推理适配 + 三后端 `local-hf` / `http` / `replay`）；`controller/language_loop.py`（会话状态机、角色 A/B、K1 检查点、CLI 子命令）；`tools/language_serve.py`（5060 薄 HTTP 服务，同一适配器）；`tests/test_language_bridge.py`、`tests/test_language_selector.py`、`tests/test_language_loop.py`（无 GPU：回放桩 + `scripted` 跟踪器 + 夹具帧发布器，全部写临时目录）；`runtime/README.md` 新增三条目；操作单 A（Mac）、B（5060）；证据 `docs/evidence/P1-ENG-LOOP-001-{report.md,latency-mac.json,latency-5060.json,merge-equivalence.json,tests.log}` |
| **B Unity Play**（候选 2，只有证据与 PLAY_GOVERNING 修复） | **是** | 操作单 C（Play 剧本 P1/P2）；每次 Play 的会话 JSONL、`tracker_state` 历史、全部语言结果（指定与核验）与叠加预览；用户 Unity 日志条目 `UT-P1-ENG-LOOP-001-*`；失败案例清单 `docs/evidence/P1-ENG-LOOP-001-play-cases.md` |

### 2.2 明确不做

1. 不改 Unity（`Assets/`、`config/` 零字节）；不改 `tethered-tracking-observation/v1`、`tethered-sensor-frame/v3`、控制包协议；不改 `TrackLoop.initialize` 的一次性语义；不改 `tools/eng_sft/` 任何冻结文件。
2. 不做自动重播种/自动恢复（定局 ④⑥）：核验只产生「疑似」，疑似状态只有操作者能解除；跟踪器段内自己从 lost 回到 ok 不算恢复；不做 ReID、几何/路网搜索、L1–L4 阶梯；不主张跟踪时长、IoU、恢复率等**跟踪性能**。
3. 不做基于跟踪分数或贴边的自动判丢：分数骤降与贴边只能触发一次核验查询，不能改变状态。
4. 不做 GUI；操作者入口只有 CLI + 桥文件。不做 G-7 世界坐标关系指令、不做「非纯色最接近」匹配、不做开放词表。
5. 不训练、不改数据、不换模型；不做 Jetson（独立立项）；不做 K5 发布打包，不公开发布。
6. 不新建评估集；不重跑 SFT-002 表 G 判定；不做 609 行复算；不把本项 Play 或核验结果写成对 SFT-002 功能门的补证。

## 3. 接口与数据契约

### 3.1 数据流（Unity 零改动；新增件全部在 Python 侧）

```
操作者 CLI ──写──► runtime/language_request.json ──读──► language_loop（会话进程；单飞 worker，同一时刻至多一个在途查询）
        ▲                                                  │ 角色 A：ask/respecify → 取 latest 完整 bundle N → select(N, surface, g4)
        │  回执 tracker_state.last_request                  │           → K1 检查点（§3.3）→ 候选 + 预览 → 人 confirm → 新段 initialize(N) 静音 → 追平 → 放行发布
        │                                                  │ 角色 B：TRACKING 中周期/触发 → select(N', surface, g4) → 与同帧 N' 跟踪框比较 → verdict → 只写状态
        └──读── runtime/language_result.json ◄──写──────────┤
                runtime/tracker_state.json   ◄──写──────────┤
                runtime/tracking_observation.json（既有 v1，不改）◄── GatedPublisher ◄── TrackLoop（每段一个实例）──► Unity 云台/机身
```

### 3.2 新桥文件（三个；均沿用 `protocol.packet` 的 `command_id`/`issued_unix_s`/`expires_after_s` 头与 `atomic_write` 原子发布）

**(a) `runtime/language_request.json` — `tethered-language-request/v1`（操作者 → 会话）**

| 字段 | 类型/闭集 | 说明 |
|---|---|---|
| `session_id` | 字符串，必填 | ≠ 当前会话 → 回执 `IGNORED_FOREIGN_SESSION`（会话启动时槽内残留的旧请求同样如此处理） |
| `request_id` | 字符串，非空 | 已消费的 id 再现 → `IGNORED_DUPLICATE` |
| `action` | `ask` / `confirm` / `reject` / `respecify` / `verify` / `confirm_lost` / `dismiss` / `release` / `stop` | 闭集；未知值 → `REQUEST_INVALID`，状态不变 |
| `instruction` | `{surface, class, color?, relation?}` | `ask` 必填；`respecify` 可省略即沿用会话最近一次已查询指令，无可沿用 → `REQUEST_INVALID` |
| `candidate_index` | 整数 ≥ 0 | `confirm` 必填 |
| `token` | 字符串 | 确认令牌：`confirm`/`reject` = 所答结果的 `result_id`；`confirm_lost`/`dismiss` = 当前 `suspect_id`；`release` = 当前 `track_id`；不匹配 → `REQUEST_INVALID` |

**单槽、写者锁与回执（AR2-3/AD3-2）**：CLI 写请求前以 `O_EXCL` 创建 `runtime/language_request.lock`（pid、request_id、时间），锁已存在 → 本次 CLI 拒绝 `WRITER_BUSY`、不写；写入后轮询 `tracker_state.last_request`
直到出现本 `request_id` 的回执才删锁、允许下一条；5 s 无回执则删锁并报「会话无响应」（该请求若稍后仍被消费，照常得到回执）。会话以 20 ms 轮询；「恰一次」只对**已成功接纳**（回执 `APPLIED`/`PENDING_QUEUED`/`SUPERSEDED`）
的请求承诺；绕过锁的写者属非法写者，其覆盖不承诺可检测，仅当会话观察到 `request_id` 变化而锁文件缺失时另记 `ILLEGAL_WRITER_SUSPECTED`。会话锁 `runtime/language_session.lock`（pid、session_id、启动时间）：
已有活锁 → 启动拒绝 `SESSION_SLOT_BUSY`，pid 已死的锁被替换并记录。回执 `outcome` 闭集固定七值：`APPLIED` / `PENDING_QUEUED` / `SUPERSEDED` / `REQUEST_INVALID` / `IGNORED_DUPLICATE` / `IGNORED_FOREIGN_SESSION` / `IGNORED_TERMINAL`。

**(b) `runtime/language_result.json` — `tethered-language-result/v1`（会话 → 操作者；只放当前世代最近一份，全部结果追加到 `<session_dir>/results.jsonl`）**

| 字段 | 类型/闭集 | 说明 |
|---|---|---|
| `query_id` | `<session_id>-q<seq>` | 全会话唯一，`seq` 对每次 designate/verify 尝试严格递增；同时作为 `predict_rows` 的 `row_id` 与每查询输出文件名 |
| `result_id`, `request_id`, `epoch`, `segment_index`, `attempt`, `attempt_limit` | 字符串/整数 | 回包的 `epoch`/`segment_index` 与当前不符 → 丢弃并只记 `IGNORED_STALE_EPOCH` 到 `results.jsonl` |
| `purpose` | `designate` / `verify` | 角色 A / 角色 B |
| `frame_id`, `frame_sha256`, `capture_monotonic_s`, `capture_unix_s`, `query_unix_s` | 帧绑定，**可空** | 未取得帧（`no_new_frame`、启动前 `load_failure`、`instruction_unsupported`）时四个帧字段为 `null` |
| `status` | `unique` / `ambiguous` / `none` / `parse_failed` / `stale_rejected` / `retry_exhausted` / `backend_error` / `no_new_frame` / `instruction_unsupported` | 前三个来自 `parse_prediction`；其余为闭环层状态，不落进观测 |
| `reject_reason` | `null` / `frames_late_exceeded` / `negative_frame_delta` / `wall_deadline_exceeded` / `bundle_missing` / `image_identity_changed` / `metadata_invalid` / `replay_miss` / `replay_conflict` / `replay_identity_mismatch` / `timeout` / `load_failure` / `worker_stuck` / `worker_died` | `stale_rejected`/`backend_error` 的细分 |
| `last_status`, `last_reject_reason` | 闭集同上，**可空** | 仅 `retry_exhausted`：最后一次尝试的原始状态与原因 |
| `candidates[]` | `{index, bbox_xywh_norm, bbox_2d_1000, clipped}` | `unique` 恰 1、`ambiguous` 2…8；其余状态为空数组 |
| `verify` | `{paired_frame_id, tracker_box_at_frame, iou, verdict ∈ {consistent, none, drift, ambiguous, inconclusive}, inconclusive_reason, consecutive_alert, alert_kind}` | 仅 `purpose=verify`（§3.6） |
| `model` | `{backend, model_form ∈ {c2-merged,c2-adapter,base}, base_repo_revision, weights_sha256, prompt_template_sha256, vocab_sha256, g4_segment_sha256\|null, device, finish_reason\|null, gen_tokens\|null}` | 未生成时 `finish_reason`/`gen_tokens` 为 `null`；`replay` 另带预测文件与盲索引 sha |
| `latency_ms`, `frames_late`, `k_ret`, `wall_elapsed_s` | 数值，**可空** | 未取得帧时 `frames_late` 为 `null` |
| `preview_path` | 路径，**可空** | 有候选或有核验配对时才生成：`<session_dir>/previews/<frame_id>-<query_id>.png`（原帧 + 带 index 的候选框；核验同时画配对跟踪框） |
| `raw_output`, `parse_error` | 诊断，**可空** | 逐字模型输出与解析错误闭集 |

**(c) `runtime/tracker_state.json` — `tethered-tracker-state/v1`（会话 → 操作者/任何消费者）**

| 字段 | 类型/闭集 | 说明 |
|---|---|---|
| `state` | `IDLE` / `QUERYING` / `AWAITING_CONFIRMATION` / `TRACKING` / `SUSPECTED` / `LOST` / `REINIT_REQUIRED` / `TERMINAL` | 面向人的会话状态（§3.4） |
| `suspect_kind`, `suspect_id` | `null` / `lost` / `drift` / `ambiguous` / `tracker_failure`；令牌 | 仅 `SUSPECTED` 非空；每次进入 `SUSPECTED` 发新 `suspect_id` |
| `tracker_raw_state` | `null` / `TRACKING` / `LOST` | 当前段 `TrackLoop` 原始状态镜像（事实，不是决策） |
| `reason` | `null` / `tracker_failure` / `verify_none` / `verify_drift` / `verify_ambiguous` / `operator_release` / `operator_reject` / `retry_exhausted` / `candidate_expired` / `frame_gap` / `frame_rollback` / `frame_stall` / `metadata_invalid` / `bundle_missing` / `image_identity_changed` / `catchup_stale` / `publish_expired` / `orphan_control` / `tracker_rejected_init` / `backend_fatal` / `duration_reached` / `operator_stop` | 进入 `SUSPECTED`/`LOST`/`REINIT_REQUIRED`/`TERMINAL` 的原因闭集 |
| `track_id`, `segment_index` | 字符串或 `null` / 整数 | 当前段 `<session_id>-t<k>`；无活段时 `null` |
| `publishing` | 布尔 | 当前段发布门是否打开（§3.3；只由播种瞬态与段 finalize 改变，核验提醒不改变） |
| `since_frame_id`, `since_unix_s`, `last_published_frame_id`, `last_progress_unix_s` | 帧/时间 | 状态起点；最近一次**实际写出**观测的帧（取自发布收据）；最近一次处理到新帧的时间（停帧判定用） |
| `retired_track_ids[]` | `{track_id, from_frame_id, to_frame_id, retired_reason}` | 每段只在进入 `LOST`/`REINIT_REQUIRED`/`TERMINAL` 时 finalize 并追加一次 |
| `verification` | `{paired_frame_id, last_verdict, last_query_id, consecutive_alert, alert_kind, next_due_unix_s, in_flight_query_id}` | 角色 B 状态 |
| `last_request`, `pending_request`, `epoch`, `sequence` | 回执 / 排队中的请求 / 世代号 / 单调整数 | 回执 `{request_id, action, outcome ∈ 七值闭集, at_sequence}`；`pending_request` 至多一条 |

**`confidence_source` 与观测桥**：观测桥文件不改，`confidence_source` 闭集 `{"placeholder","tracker"}` 与「未校准」含义在 `runtime/README.md` 对外声明（G-5）；模型身份只进 `language_result.json`。

### 3.3 `K1` 时间语义：绑定、拒收、静音播种、发布最终门、追平

**记号**：N = 查询帧；`sha_N` = 查询时图像 sha；`t_q` = 查询墙钟；`L_r`/`L_c`/`L_w` = 返回/确认/**写桥**时的 `latest_frame_id`；`hz`、`R` = 实际生效场景配置的 `capture_hz`、
`retained_frame_count`，会话启动读出并与 K 收据绑定：与收据不同 → 启动拒绝 `CONFIG_MISMATCH`（即本项只支持测量时绑定的配置闭集，默认 hz 5、R 128）。

- **三段预算（AR2-5）**：模型预算 `K_ret = ceil(p95_s × hz) + 2`（`p95_s` = 所选宿主、最终模型形态的实测）；人工确认预算 `K_conf = ceil(T_conf × hz)`，`T_conf` 申请值 10 s（默认 50 帧）；
  写桥容差 `K_pub` 申请值 2 帧。**宿主资格** `K_ret + K_conf + K_pub ≤ R − 8`，等价 `p95_s ≤ (R − 12 − K_conf)/hz`（默认 13.2 s）；余量由构造保证，不再封顶。`T_ret = K_ret/hz`。
- **四个检查点**（前三个失败 → `stale_rejected` + `reject_reason`，不初始化、不写桥，计入重试预算；「不初始化」只适用于初始化前的失败，写桥门失败属于已初始化段的终止）：

| 检查点 | 检查 | 失败出口 |
|---|---|---|
| 查询 | N 为完整 bundle、元数据 `frame_id == N` 且时钟合法；记 `sha_N`、元数据时间、`t_q` | 不发查询：`bundle_missing` / `metadata_invalid` |
| 返回 | `0 ≤ L_r − N ≤ K_ret`；`now − t_q ≤ T_ret`（含停帧：`L_r == N` 但墙钟超时）；N 两成员仍在、图像 sha == `sha_N`、元数据时间一致 | `negative_frame_delta` / `frames_late_exceeded` / `wall_deadline_exceeded` / `bundle_missing` / `image_identity_changed` / `metadata_invalid` |
| 确认 | `0 ≤ L_c − N ≤ K_ret + K_conf`；`now − t_q ≤ T_ret + T_conf`；N 身份重核；`token`/`epoch`/index 合法 | 同上；令牌不合 → `REQUEST_INVALID` |
| 写桥（最终门） | 见下「发布最终门」五项 | `catchup_stale` / `image_identity_changed` / `bundle_missing` / `frame_rollback` / `publish_expired` / `orphan_control` → 段 finalize，`REINIT_REQUIRED` |

- **加载时快照（AD3-1）**：会话向每段的 `FrameRepository` 注入自己的 `image_loader`（`track_loop.py:77-86` 允许）：对每个帧文件**只读一次字节**，计算 JPEG sha、记录加载墙钟与该帧元数据时间，
  把字节复制进会话帧环 `<session_dir>/frames/`（保留最近 `R` 帧），再解码交给跟踪器。快照在跟踪器、发布器、运行日志看到该帧之前建立，来源就是被实际处理的字节；角色 A 的查询帧 N 同样经此路径读取与复制，
  `initialize(N)` 再次加载时哈希不等即 `image_identity_changed`，不播种。
- **发布最终门（AR2-1/AD3-1）**：`GatedPublisher.observation(frame_id, …)` 写桥前自行核验五项：① 快照存在且 `frame_id` 等于最近一次加载的帧；② 重算盘上 `frame_<id>.jpg` 字节 sha 等于快照 sha
  （拒绝 JSON 不变而 JPEG 已换）；③ 重读元数据 `capture_monotonic_s`/`capture_unix_s` 等于快照；④ 重读 `latest.json`：`0 ≤ L_w − frame_id ≤ K_pub`；⑤ `now − 快照加载墙钟 ≤ T_pub`
  （申请值 `K_pub/hz`，拒绝「帧头未动但已过期」）。通过 → 写桥、记 `WRITTEN`、置 `accepted_frame_id`；否则丢弃并记 `PUBLISH_REJECTED(catchup_stale | image_identity_changed | bundle_missing | frame_rollback | publish_expired)`，
  会话 finalize 段进入 `REINIT_REQUIRED(同名)`。**同帧关联**：其后的 `look_at`/`body_command` 只在 `accepted_frame_id` 已置且尚未被下一帧的发布尝试覆盖时透传，否则丢弃记 `orphan_control`；
  被拒帧的观测及其衍生控制零写入。发布位于 `process_available` 帧循环内、该帧运行记录之前（事实 12），所以「追平期间零写入」指非批末帧与被拒帧；批末帧经门写出是追平结束的一部分。
  收据文件 `<session_dir>/publish-receipts.jsonl` 是**唯一**发布证据，运行日志 `published_*` 只是调用意图。
- **静音播种**：段创建即 `muted`（`hold_body`/`set_nadir` 永远透传），`initialize(N, …)` 的即时发布被丢弃；第一次 `process_available()` 前 `unmute`，之后每次写入都过最终门。
- **首次发布等待与停帧**：确认后若 `T_stall`（申请值 3 s）内没有 `frame_id > N` 的新帧 → `REINIT_REQUIRED(frame_stall)`；`TRACKING`/`SUSPECTED` 中 `last_progress_unix_s` 超过
  `T_stall` 未更新亦然。`process_available` 在无 rate lifecycle 时对坏元数据抛 `ValueError`（`track_loop.py:437-440`），由会话捕获映射为 `REINIT_REQUIRED(metadata_invalid)`；
  返回 0 且无异常是正常空转。
- **宿主决策（AR2-6）**：先判资格（上式），再分档：`A` = 合格且 `p95 ≤ 6.0 s`；`B` = 合格且 `p95 > 6.0 s`；`C` = 不合格；`FAIL` = 加载失败/OOM/两轮测量均 `INVALID`。

| Mac | 5060 | 决定 |
|---|---|---|
| A | 任意 | Mac `local-hf` |
| 非 A | A | 5060 `http` |
| B | B | p95 较小者；**相等取 Mac**（单机、无网络） |
| B | C/FAIL | Mac，`K_ret` 按 Mac p95 |
| C/FAIL | B | 5060，`K_ret` 按 5060 p95 |
| C/FAIL | C/FAIL | `HOST_UNDECIDED`：不冻结，上交用户 |

  `p95_s` 必须取最终运行形态在同一设备上的测量；6.0 s、`T_conf`、`K_pub`、`T_stall` 都是申请值。

### 3.4 `K3` 会话状态机（八态 × 九动作；未列组合一律回执 `REQUEST_INVALID`，状态不变）

**提醒与控制的边界（AR2-2）**：发布门只由两类事改变：播种瞬态（静音→放行，机制）与段 finalize（人工 `release`/`confirm_lost`/`stop` 或协议终止）。
核验提醒、`dismiss`、`raw_lost`/`raw_ok` 都**不碰**发布门；`--on-suspect` 选项删除。底层事实：`raw_lost` 时 `TrackLoop` 本就不发观测，`raw_ok` 恢复后它继续发观测，
会话既不补发也不拦截，Unity 侧仍按既有过期→`Hold()` 回退。因此本项没有由 VLM 语义结果触发的自动控制动作；协议失败（`seg_end`）仍自动 finalize 段并停止发布，这是既有 fail-closed 语义的沿用，不是新增控制策略。

| 会话状态 | `raw` | 向 Unity 桥的发布 |
|---|---|---|
| `TRACKING` / `SUSPECTED` | `TRACKING` | 跟踪器观测经最终门写出（提醒不改控制） |
| `TRACKING` / `SUSPECTED` | `LOST` | 无（`TrackLoop` 既有行为） |
| 播种瞬态 | — | 无（静音） |
| `LOST` / `REINIT_REQUIRED` / `TERMINAL` | — | 无（段已 finalize） |

**查询 worker（AR2-3）**：本项自带 `LanguageWorker`，不复用 `SingleFlightWorker`（事实 15）：每次查询一个守护线程，结果带 `query_id`/`epoch`/`segment_index`；同一时刻至多
一个在途 + 至多一条 **pending**（新的 designate/verify 需求在在途时排队，再来一条则旧 pending 回执 `SUPERSEDED`；在途结束即启动 pending）。在途有界：`local-hf` 由
`MAX_NEW_TOKENS=160` 自然有界、另设硬限 `T_hard`（申请值 60 s），超硬限记 `worker_stuck`、回包到达即丢弃、会话 finalize 段进入 `REINIT_REQUIRED(backend_fatal)` 并要求
`stop` 重启进程（线程不可中断，不再提交新查询）；`http` 由服务端单工与 `T_hard` 有界（§3.5）：客户端 `T_ret` 到期只把该查询记 `timeout`，**不视为服务端已结束**，在 `GET /status` 报 idle 前不提交 pending/重试/新段查询，等待受服务端 `T_hard` 约束；服务端 `stuck` → `backend_fatal`。`stop`：`epoch+1`、finalize 段、join 在途线程 ≤ 5 s，未结束记
`worker_abandoned` 后退出。设计上不存在两个在途查询，`verify` 与 designate 共用同一 worker。

内部事件：`R_des(ok)`、`R_des(fail)`（none/parse_failed/stale_rejected/backend_error/no_new_frame）、`R_ver(v)`、`raw_lost`/`raw_ok`、`seg_end(reason)`（frame_gap/frame_rollback/
frame_stall/metadata_invalid/bundle_missing/catchup_stale/image_identity_changed/publish_expired/orphan_control/duration_reached/backend_fatal）、`due`。

| 状态 | 事件/动作 | 下一状态 | 动作 |
|---|---|---|---|
| `IDLE` | `ask` / `respecify`（有可沿用指令） | `QUERYING` | `epoch+1`，`attempt=1`，`purpose=designate` |
| `IDLE` | `stop` | `TERMINAL` | `reason=operator_stop` |
| `QUERYING` | `R_des(ok)` | `AWAITING_CONFIRMATION` | 写结果与预览；`unique` 也**必须**确认 |
| `QUERYING` | `R_des(fail)` ∧ `attempt < attempt_limit` | `QUERYING` | 等 `frame_id > N` 的新帧最长 `T_ret`，无则记 `no_new_frame`（帧字段可空）；每次尝试各出一份结果，`attempt+1` |
| `QUERYING` | `R_des(fail)` ∧ `attempt == attempt_limit` | 有过段 → `REINIT_REQUIRED(retry_exhausted)`；否则 `IDLE` | 写 `retry_exhausted`（`last_status`/`last_reject_reason`） |
| `QUERYING` | `ask` / `respecify` | `QUERYING` | `epoch+1`，新查询排为 pending；在途回包按 `IGNORED_STALE_EPOCH` 丢弃 |
| `QUERYING` | `stop` | `TERMINAL` | 见 worker 规则 |
| `AWAITING_CONFIRMATION` | `confirm k`（确认检查点通过） | `TRACKING` | 新段 `track_id=<session>-t<k>`；静音 `initialize(N, box_k)` → 放行 → 追平（最终门）；`next_due = now + T_v`；`consecutive_alert=0` |
| `AWAITING_CONFIRMATION` | `confirm k`（`token`/`epoch`/index 不合法） | `AWAITING_CONFIRMATION` | 回执 `REQUEST_INVALID`，状态与候选不变 |
| `AWAITING_CONFIRMATION` | `confirm k`（合法但确认检查点失败） | 有过段 → `REINIT_REQUIRED(candidate_expired)`；否则 `IDLE` | 写 `stale_rejected`（`reject_reason` = 失败出口），候选作废，须重新 `ask`/`respecify` |
| `AWAITING_CONFIRMATION` | `reject`（`token` 合法） | 有过段 → `REINIT_REQUIRED(operator_reject)`；否则 `IDLE` | 丢弃候选 |
| `AWAITING_CONFIRMATION` | `ask` / `respecify` / `stop` | `QUERYING` / `QUERYING` / `TERMINAL` | 同上 |
| `TRACKING` | `due` / `verify` | `TRACKING` | worker 空闲则发 verify（§3.6），否则等下一轮询 |
| `TRACKING` | `R_ver(*)` | 按 §3.6 计数表：`consecutive_alert` 达 2 → `SUSPECTED(alert_kind)`；`ambiguous` → `SUSPECTED(ambiguous)`；否则 `TRACKING` | 只改计数与 `verification`，不碰发布门 |
| `TRACKING` | `raw_lost` | `SUSPECTED(tracker_failure)` | 发 `suspect_id`；发布门不变 |
| `TRACKING` | `release`（`token == track_id`） | `LOST(operator_release)` | finalize 段（一次） |
| `TRACKING` | `respecify` / `confirm_lost` / `dismiss` | `TRACKING` | `REQUEST_INVALID` |
| `TRACKING` | `seg_end(reason)` | `REINIT_REQUIRED(reason)` | finalize 段（一次） |
| `TRACKING` | `stop` | `TERMINAL` | finalize 段 |
| `SUSPECTED` | `confirm_lost`（`token == suspect_id`） | `LOST(reason=进入时 reason)` | finalize 段（一次） |
| `SUSPECTED` | `dismiss`（同上） | `TRACKING` | `consecutive_alert=0`，`verify_epoch+1`（在途/迟到核验回包丢弃），`next_due = now + T_v` |
| `SUSPECTED` | `respecify` | `QUERYING` | 等价 `confirm_lost` 后 `respecify` |
| `SUSPECTED` | `verify` / `due` / `R_ver(*)` / `raw_ok` / `raw_lost` | `SUSPECTED` | 只更新 `verification`/`tracker_raw_state`，不新发 `suspect_id`；**疑似状态只有人能解除** |
| `SUSPECTED` | `seg_end(reason)` / `stop` | `REINIT_REQUIRED(reason)` / `TERMINAL` | finalize 段 |
| `LOST` / `REINIT_REQUIRED` | `respecify` / `ask` | `QUERYING` | 无活段，不再 retire |
| `LOST` / `REINIT_REQUIRED` | `stop` | `TERMINAL` | — |
| `TERMINAL` | 任何请求 | `TERMINAL` | 回执 `IGNORED_TERMINAL`（进程退出后无人回执 → CLI 报「会话无响应」） |

`attempt_limit` 申请值 3，`T_v` 申请值 10 s。段 = `TrackLoop` + `GatedPublisher`，`run_id=<session_id>-seg<k>`，清单沿用 `p1-track-run/v1`；finalize 写段摘要并追加
`retired_track_ids`，只发生一次；会话 JSONL `<session_dir>/language-session.jsonl` 每次迁移一行。

### 3.5 后端接口、统一推理适配、回放连接与测量口径

```
class InferenceAdapter(Protocol):
    identity: Mapping[str, Any]                                   # §3.2(b) model 闭集（不含 finish_reason/gen_tokens）
    def predict_one(self, query_id: str, image_path: Path, surface: str, g4: bool) -> RawSelection
        # RawSelection = (raw_output, finish_reason, gen_tokens, latency_ms, prompt_sha256, model_id)
```

- **统一推理（AR1-3）**：`local-hf` 与 `http` 服务端都不写第二份推理代码，把一次查询包成**一行** rows
  `{row_id: query_id, frame_path: "<帧副本>", surface, g4, vocab: "unity-v2"}` 调既有 `train_lora.predict_rows(loaded, rows, package_root=<会话 scratch>, out_path=<session_dir>/queries/<query_id>.jsonl)`，
  从记录取 `raw_output/finish_reason/gen_tokens/latency_ms/prompt_sha256/model_id`；解析统一用 `parse_prediction(raw_output, finish_reason=…)`。`tools/eng_sft/` 零改动；selector 只接收图像、指令与 g4 标志。
- **模型形态**（`--model-form`）：`c2-merged`（缺省，前提是等价成立）/ `c2-adapter`（合并失败或等价不成立时的**唯一**自动回退）/ `base`（只在用户点名时用，结果分列）。
  合并：C2 `merge_and_unload` 后存 `outputs/eng-loop/P1-ENG-LOOP-001/model/c2-merged/`（不入库），身份 = 权重文件 sha；每台机器合并尝试 ≤ 2 次（§5）。
- **等价判定（AC-9）**：同设备（5060）、同 32 行 smoke、同 greedy：逐行 `status` 相同；`unique` 框 IoU ≥ 0.9；`ambiguous` 候选数相同且一对一匹配 IoU ≥ 0.9（穷举匹配，同 `evaluate.py` 口径）；
  任一侧 `parse_error ≠ null` 记不等价。不等价或合并失败 → 形态 `c2-adapter`，并以该形态实测时延。
- **`http`（AD3-2）**：`tools/language_serve.py` 是**单工、提交/轮询式**服务：`POST /query`（JPEG + surface + g4 + query_id）空闲时立即返回 `accepted`，忙时返回 `SERVER_BUSY`（不排队）；
  `GET /status` 报 `idle | busy(query_id, since) | stuck`；`GET /result/<query_id>` 取完成结果（只保留最近一次完成、只对提交时的 `query_id` 返回；被客户端放弃的查询照常跑完但结果不再返回）。
  服务端在途由 `MAX_NEW_TOKENS` 与 `T_hard`（60 s）有界，超硬限置 `stuck` 并拒绝一切新提交直到重启。客户端时延 = 提交到取回结果（含上传与轮询）；`T_ret` 到期记 `timeout`；测量期固定 60 s。
  同一实际模型永不重入，失效任务不累积（忙时拒绝而非排队）。
- **`replay`**：索引 = `eval.blind.jsonl`（无 gold；键 `(sha(frame_path), surface, g4)`）+ 预测 JSONL（按 `row_id` 连接）。加载核对 sha：盲文件对 `eval-manifest.json.files["eval.blind.jsonl"].sha256`，
  预测文件对 `eval-summary.json.predictions_sha256`（C2）或 `baseline_predictions_sha256`（base），不符 → `replay_identity_mismatch`；无匹配 → `replay_miss`；多行匹配（§8：4 行与 2 行两组）
  → 各行 `(raw_output, finish_reason)` 必须相同，取最小 `row_id`，否则 `replay_conflict`。帧源 `upload/frames/<sha>.jpg`（392 张）。只用于测试与 `replay-demo`。
- **时延测量口径（AC-10）**：每台宿主、最终形态：3 次预热（单列）+ 32 次计时（smoke 集，顺序固定）；边界 = `predict_one` 调用到返回（含图像读取、编码、生成；`http` 含传输）；
  `p95` = 32 样本升序第 31 个；任一样本异常/超时即样本失败，该轮 `INVALID`，允许重跑 1 轮，**第二轮仍 `INVALID` → 该宿主 `FAIL`**；加载失败/OOM 记 `FAIL`。
  报告：p50/p95/max、每 token ms、峰值内存（Mac：进程 RSS + MPS 分配；5060：`torch.cuda.max_memory_allocated`）、失败数、环境版本、`hz`/`R`、`K_ret`/`K_conf`/`K_pub`、资格与分档。

### 3.6 角色 B：语义核验（K3；提醒不是决策）

- **配对帧（AR2-4/AD3-1）**：核验帧 P = 本段**最近一帧已处理**的帧，**不是** `latest`；处理帧环 = 加载时快照（`frame_id`、图像 sha、元数据时间、帧环副本）+ 该帧运行记录（`box_norm`、raw 状态，
  由日志包装器在记录写入后登记），核验只在该帧记录写入后才可发起；送给 VLM 与画预览的图像取**帧环中的加载时副本**（哈希 = 快照哈希，由构造保证），不重读 `runtime/frames/`。发起条件：P 仍在盘且身份一致；`P.frame_id > 上一次核验的配对帧`（同帧不重复核验，跳过记 `inconclusive(same_frame)`、不计数）；`P.box_norm` 非空
  （raw 丢失时跳过记 `inconclusive(no_tracker_box)`，`SUSPECTED(tracker_failure)` 已另行提醒）；`latest − P.frame_id ≤ K_pub`（否则 `inconclusive(tracking_lag)`）。
- **何时问**：`TRACKING` 中每 `T_v` 一次；触发提前：跟踪框贴边（裁剪前后不同或任一边距 < 1%）、跟踪分数低于最近 25 帧中位数一半、操作者 `verify`；同一触发源 3 s 内至多一次；
  worker 忙则等下一轮询。触发只发起查询，不改状态。
- **问什么**：会话最近一次已确认的指令（surface、g4）在 P 上重问。
- **返回校验**：`epoch`/`segment_index`/`verify_epoch` 不符 → 丢弃；`now − t_q > T_ret` → `inconclusive(stale)`；P 身份变化/帧回退/元数据不符 → `inconclusive(frame_identity)`；
  `parse_failed`/`backend_error` → `inconclusive(同名)`。
- **verdict 与计数**（单计数器 `consecutive_alert`，`alert_kind` = 最近一次告警类）：

| verdict | 判据 | `consecutive_alert` | 状态 |
|---|---|---|---|
| `consistent` | `unique` 且 IoU(P 跟踪框, VLM 框) ≥ 0.5 | 置 0 | 不变 |
| `none` | `none` | +1，`alert_kind=lost` | 达 2 → `SUSPECTED(lost)` |
| `drift` | `unique` 且 IoU < 0.5 | +1，`alert_kind=drift` | 达 2 → `SUSPECTED(drift)` |
| `ambiguous` | `ambiguous` | 置 0 | 立即 `SUSPECTED(ambiguous)` |
| `inconclusive` | 上述任一校验失败 | 不变 | 不变 |

  `none`/`drift` 交替同样累计（两次连续告警即提醒，`kind` 取最近一次）；两次告警必来自不同配对帧（由同帧不重复保证）。每次核验结束 `next_due = 完成时刻 + T_v`。
  `dismiss`、`confirm_lost`、新段、`stop` 都使 `verify_epoch+1`，其后到达的旧核验回包一律丢弃，不得重新触发提醒。
- **边界**：语义一致性而非身份一致性；小目标与贴边误报（G1 S 层 36.7%、贴边误报 none 11.6%）会成为疑似误报，连续 2 次与人工确认是唯一兜底。核验永不 `initialize`、永不写桥、永不解除疑似。

### 3.7 受支持指令（闭集文法；与 SFT-002 评估集 G1/G2/G4 表面同模板）

```
<instruction> ::= "the " <class>                                              # G1  例：the suv
                | "the " <color> " " <class>                                   # G2  例：the red car
                | "the " <class> " to the viewer's " ("left"|"right") " of the " <class>   # G4  例：the suv to the viewer's left of the pickup truck
<class> ∈ {ambulance, bus, car, container truck, pickup truck, police car, suv, taxi, truck}
<color> ∈ {blue, gray, green, purple, red, yellow}
```

CLI 按文法解析并**重新序列化**为 `surface`，不接受自由文本；不合文法 → `instruction_unsupported`，不发查询。G4 行置 `g4=True`。

### 3.8 操作者 CLI（`python3 -m controller.language_loop …`）

`run --session-id S --session-root <dir> --runtime <runtime> --backend {local-hf,http,replay} --model-form {c2-merged,c2-adapter,base} --k-receipt <K 收据> --attempt-limit 3 --verify-interval-s 10 --tracker nanotrack-v2 --scenario-id … --condition follow --ground-plane-y-m … --planned-duration-s …`
起会话进程（写会话锁；`K_ret/K_conf/K_pub` 与 `hz/R` 从 K 收据读入并与实际配置核对）；操作者另开终端发 `ask "<instruction>"` / `confirm <k>` / `reject` / `respecify ["<instruction>"]` /
`verify` / `confirm-lost` / `dismiss` / `release` / `status` / `stop`，每条 = 原子写请求 + 等回执；`status` 打印 `tracker_state` 与最近结果的预览路径。`serve --port …` 起 5060 服务。
`replay-demo --session-root <tmp>` 用夹具帧发布器 + 回放桩在临时目录跑一遍 P1/P2 的协议路径（阶段 A 的可运行示例）。阶段 A 的一切会话都以 `--session-root` 指向
`outputs/eng-loop/P1-ENG-LOOP-001/sessions/` 或测试临时目录、`--runtime` 指向夹具目录，不写 `runtime/runs/`、不占共享 runtime 槽；阶段 B 的正式与诊断 Play 都以 `--runtime runtime/` 使用真实桥；`--diagnostic`（AD3-4）：会话号强制 `diag-` 前缀，段运行日志的 `RunLogger` 根指向会话根（`<session_root>/runs/`），不创建 `runtime/runs/`、不消耗 scenario/session/run ID，产物只作演练、不进 AC-13…15 证据；正式 Play 不带该标志，段目录 `runtime/runs/<session>-seg<k>/`。两者的桥文件、模型进程与查询计数相同。旧 `track_loop` CLI 不改。

## 4. 验收项（AC 表）

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | 三个桥文件按 §3.2 的 schema、字段闭集与可空规则实现并原子发布；未知 `action`/`status`/`reason`/`verdict` fail-closed；已成功接纳的请求恰消费一次并写回执（`outcome` 七值闭集逐一枚举），写文件不等于消费；CLI 写者锁并发 → `WRITER_BUSY`；`session_id` 不符与槽内残留请求 → `IGNORED_FOREIGN_SESSION`；会话锁 `SESSION_SLOT_BUSY`；`runtime/README.md` 新增三条目并写明 `confidence_source` 闭集与未校准含义 | test:tests.test_language_bridge；artifact:runtime/README.md | K1K3 | 2026-09-19 |
| AC-2 | 查询/返回/确认三个检查点的七个出口（`frames_late_exceeded`、`negative_frame_delta`、`wall_deadline_exceeded` 含停帧、`bundle_missing`、`image_identity_changed`、`metadata_invalid`、确认超 `T_ret + T_conf`）各有具名红/绿测试，每例断言夹具 runtime 的观测/云台/机身桥文件未被写入且发布收据为空 | test:tests.test_language_loop（`StaleRejection*`） | K1K3 | 2026-09-19 |
| AC-3 | 加载时快照与发布最终门：注入 loader 使快照先于跟踪器/发布器/日志建立（测试断言顺序）；`initialize` 即时发布被丢弃；批末帧经门写出，被拒帧及其衍生控制零写入；门的六个出口各有红/绿（`catchup_stale`、`image_identity_changed`＝JSON 不变换 JPEG、`bundle_missing`、`frame_rollback`、`publish_expired`＝帧头未动但超 `T_pub`、`orphan_control`）；第一条 `WRITTEN` 收据满足五项核验；确认后 `T_stall` 无新帧 → `REINIT_REQUIRED(frame_stall)`；坏元数据 `ValueError` → `REINIT_REQUIRED(metadata_invalid)`；返回 0 可空转；运行日志 `published_*` 与收据可不同且证据只取收据 | test:tests.test_language_loop（`GatedSeeding*`、`PublishGate*`、`CatchUp*`） | K1K3 | 2026-09-19 |
| AC-4 | `tracker_raw_state` 镜像段内原始状态（含追平批内逐帧记录）；`raw_lost` → `SUSPECTED(tracker_failure)` 且发布门不变；`raw_ok` 恢复后发布经最终门继续；`sequence` 单调；`LOST`/`REINIT_REQUIRED`/`TERMINAL` 后 `publishing=false` 且收据零新增；Unity/config/`tools/eng_sft/` 零改动 | test:tests.test_language_loop（`StateMirror*`）；cmd:`git diff --stat <上一通过候选>..HEAD -- Assets/ config/ tools/eng_sft/` 为空 | K1K3 | 2026-09-19 |
| AC-5 | 首次指定必须确认：`unique`/`ambiguous` 均停在 `AWAITING_CONFIRMATION`；无 `confirm` 不 `initialize`；`token`/`epoch` 不匹配或 index 越界 → `REQUEST_INVALID` 且状态不变；合法确认但检查点失败 → `stale_rejected` 与 `candidate_expired` 迁移；预览存在且 index 与候选一一对应 | test:tests.test_language_loop（`Confirmation*`） | K1K3 | 2026-09-19 |
| AC-6 | 有界重试：五类失败重试至 `attempt_limit`，`attempt` 严格递增；取得帧的尝试其 `frame_id` 严格递增，`no_new_frame` 尝试帧字段为 `null` 并计次；超限 `retry_exhausted` 带 `last_status`/`last_reject_reason` 并按 §3.4 落 `IDLE`/`REINIT_REQUIRED`；`ambiguous` 候选 2…8 全部呈现、`confirm k` 选一播种 | test:tests.test_language_loop（`BoundedRetry*`、`Ambiguous*`） | K1K3 | 2026-09-19 |
| AC-7 | 重指定：从 `LOST`/`REINIT_REQUIRED`/`SUSPECTED` 的 `respecify` 开新段（`track_id` 递增），旧段 finalize 与 `retired_track_ids` 追加恰一次（GAP、`release`、`confirm_lost` 三条路径）；`TRACKING` 下 `respecify` 被拒；缺省沿用上次指令，无可沿用 → `REQUEST_INVALID` | test:tests.test_language_loop（`Respecify*`） | K1K3 | 2026-09-19 |
| AC-8 | 每份结果携带 `query_id` 与 §3.2(b) `model` 身份闭集；`finish_reason` 经三后端一致保留（`length` → `TRUNCATED`）；失败包按可空规则合法；`http` 遇 `SERVER_BUSY`/`timeout` 后在 `GET /status` idle 前不重入服务端；观测桥 schema 常量与 `confidence_source` 闭集字节未变 | test:tests.test_language_selector；cmd:`git diff <上一通过候选>..HEAD -- controller/tracking_entry.py controller/protocol.py` 为空 | K1K3 | 2026-09-19 |
| AC-9 | 回放：盲索引 + 预测文件按 `row_id` 连接并核对两份 sha；重复键相同取最小 `row_id`、冲突 → `replay_conflict`、无匹配 → `replay_miss`；selector 不读 gold；`replay-demo` 覆盖 designate 四路径与 verify 五 verdict；5060 等价判定按 §3.5，不等价则回退 `c2-adapter` 并披露 | test:tests.test_language_selector；artifact:docs/evidence/P1-ENG-LOOP-001-merge-equivalence.json | K1K3 | 2026-09-19 |
| AC-10 | Mac 与 5060 各一份时延报告（§3.5 口径，第二轮 `INVALID` → `FAIL`）；按 §3.3 先资格后分档选宿主，写出 `K_ret/K_conf/K_pub` 与 `hz/R` 的 K 收据；`HOST_UNDECIDED` 时不冻结、上交用户 | artifact:docs/evidence/P1-ENG-LOOP-001-latency-mac.json；artifact:docs/evidence/P1-ENG-LOOP-001-latency-5060.json；artifact:docs/evidence/P1-ENG-LOOP-001-report.md §K 收据 | K1K3 | 2026-09-19 |
| AC-11 | 停点全套无 GPU 测试一次写文件；基线既有失败与本批新增失败分列；新增失败 0 | cmd:`python3 -m unittest discover -s tests > docs/evidence/P1-ENG-LOOP-001-tests.log 2>&1`；artifact:docs/evidence/P1-ENG-LOOP-001-tests.log | K1K3 | 2026-09-19 |
| AC-12 | 依赖与安装说明：`tools/requirements-language.txt`（钉 SFT-002 同版）+ 操作单 A/B/C；新环境 `.venv-language` 不改既有环境；`pip check` 通过 | artifact:tools/requirements-language.txt；artifact:docs/evidence/P1-ENG-LOOP-001-report.md §操作单 | K1K3 | 2026-09-19 |
| AC-13 | **Play 主剧本 P1**（场景零改动；机身沿用一次性 hold；`--condition follow`；目标循环，周长 213 m、106.5 s/圈；观察窗 2 圈 ≤ 220 s；事实 16 只支持存在不利观察段的假设，不保证离画）：操作 = 目标可见时 `ask "the red car"` → `confirm` → `TRACKING` ≥ 25 帧且有 `WRITTEN` 观测 → 操作者按核验预览（帧环源帧副本 + 跟踪框 + VLM 框）标记整车离画的首个核验帧 `F_out`（每次标记 = 一个**离画事件**）。事件裁定窗口 = `F_out` 起随后 3 次 verdict ≠ `inconclusive` 的核验完成，或 `3·T_v + T_ret` 墙钟先到。事件结局按优先级唯一归类：① 窗口内进入 `REINIT_REQUIRED` → `PROTOCOL_ABORT`（Unity/环境原因 BLOCKED，会话原因 FAIL）；② 窗口内进入 `SUSPECTED(lost\|drift)` → `E1_ALERT`，随后 `confirm_lost` → `respecify` → `confirm` → 新段 `TRACKING` 在本次 Play 内完成 → `E1_ACHIEVED`，未完成 → `E1_CHAIN_INCOMPLETE`；③ 窗口内先进入 `SUSPECTED(ambiguous)` → `AMBIGUOUS_ALERT`；④ 窗口内仅 `tracker_failure` 提醒 / 仅人工 `release` → `E2_ONLY` / `E3_ONLY`；⑤ 窗口内三次完成全为 `inconclusive` → `INCONCLUSIVE_WINDOW`（不计 FAIL、不计 E1）；⑥ 其余（窗口耗尽无提醒，含 none/consistent 交替）→ `MISSED_ALERT`（FAIL）。Play 结局 = 有事件 `E1_ACHIEVED` 则通过；无离画事件 → `NOT_TRIGGERED`；否则取首个事件结局。**通过条件**：≥ 1 次 Play `E1_ACHIEVED` 且该事件全程 `frames_late ≤ K_ret`、确认在 `T_conf` 内；正式 Play 额度用尽仍无 → AC-13 `NOT_MET`（不改场景、不保证成功），工作项不能 `DONE`，接受角色按 §4.6 归因后交用户。目检与提示都绑定核验源帧副本与 `query_id`，不以 `C_geom` 替代、不用返回时的画面判过去帧 | artifact:docs/unity-test-log.md `UT-P1-ENG-LOOP-001-P1`（含每个离画事件的 `F_out`、窗口内核验 `query_id`、`SUSPECTED` 帧、人工动作时刻）；artifact:会话 JSONL、`results.jsonl`、`publish-receipts.jsonl` 副本 | K1K3（Play 证据） | 2026-09-19 |
| AC-14 | **Play 歧义剧本 P2**（静止同类多车，一条评估集 G3 同款指令）：结局闭集与适用检查——`ambiguous`：呈现全部候选 + 预览、`confirm k` 播种成功；`unique`：仍须确认，记「歧义未识别」；`none`→`retry_exhausted`、`parse_failed`、`backend_error`、`stale_rejected`、`no_new_frame`：如实报告，确认 N/A。**通过条件** = 每个实际出现的结局其适用检查全部成立；「歧义识别成功」（G3 型指令至少一次报 `ambiguous`）单列计数，不作通过条件，不改模型 | artifact:docs/unity-test-log.md `UT-P1-ENG-LOOP-001-P2`；artifact:docs/evidence/P1-ENG-LOOP-001-play-cases.md | K1K3（Play 证据） | 2026-09-19 |
| AC-15 | 每次 Play 记录描述性数字：指定/核验查询次数、`frames_late`、端到端时延、重试次数、verdict 计数与疑似误报次数（按核验源帧目检）、`SUSPECTED`→人工处置延迟、重指定次数、终态；失败案例 ≥ 3 条或声明不足；失败不反复试到成功；报告不含跟踪性能/恢复率主张 | artifact:docs/evidence/P1-ENG-LOOP-001-play-cases.md | K1K3（Play 证据） | 2026-09-19 |
| AC-16 | 核验语义：配对帧 = 本段最近已处理帧；同帧不重复、无框跳过、跟踪滞后跳过、帧身份/回退/超时 → `inconclusive(reason)`；verdict 五值与单计数器规则（含 none/drift 交替累计）；`dismiss`/`confirm_lost`/新段/`stop` 后旧回包丢弃不重触发；核验从不 `initialize`、从不写桥、从不解除 `SUSPECTED`；designate 在途时跳过；触发 3 s 同源限频 | test:tests.test_language_loop（`Verify*`） | K1K3 | 2026-09-19 |
| AC-17 | §3.4 八态 × 九动作表逐格实现（参数化覆盖全表）：未列组合 → `REQUEST_INVALID`；`epoch`/`segment_index` 不匹配回包 → `IGNORED_STALE_EPOCH`；pending 至多一条、`SUPERSEDED` 回执；`T_hard` 超限 → `worker_stuck` → `REINIT_REQUIRED(backend_fatal)`；`stop` 后 `IGNORED_TERMINAL`、join ≤ 5 s 与 `worker_abandoned`；写者锁并发 CLI → `WRITER_BUSY`；服务端 `stuck` → `backend_fatal`；`SUSPECTED` 只由 `confirm_lost`/`dismiss`/`respecify`/`stop`/段终止离开 | test:tests.test_language_loop（`StateTable*`、`Worker*`） | K1K3 | 2026-09-19 |

AC 编号一经接受即稳定。AC-13…15 是 `DONE` 所需的 Unity 证据，本项**不申请** `UNITY_NA`。

## 5. 预算信封（申请值；`ACCEPTED` 后由用户逐字授权入账，缺项视为 0；阶段 A 与阶段 B 分两次授权；成功、失败、重试、诊断全部计入同一上限，耗尽即停）

| 项目 | 阶段 A（候选 1，离线） | 阶段 B（候选 2，Play） |
|---|---|---|
| Consuming | **no** | **yes** |
| scenario/session/run ID | 0：会话与夹具只写 `outputs/eng-loop/…/sessions/` 或测试临时目录，不写 `runtime/runs/`、不占共享 runtime 槽 | 正式语言会话 ≤ 8（每会话段 ≤ 4，`runtime/runs/<session>-seg<k>/`）；诊断会话 ≤ 2 且 **0 个正式 ID**（`diag-` 前缀、产物在诊断根）；scenario 沿用 `deterministic-loop-default`，零新 scenario |
| Unity Play | 0 | 正式 Play 总尝试 ≤ 8（含失败、中止、`NOT_TRIGGERED`），每次 ≤ 300 s 仿真时间；诊断演练 Play ≤ 2（workflow §4.3.2 通道：不创建、不消耗 scenario/session/run ID，产物不进证据链），其模型进程与查询**计入**下两行上限 |
| 模型 API 次数 | 0 | 0 |
| 训练 GPU·h | 0 | 0 |
| 合并动作 | Mac ≤ 2 次、5060 ≤ 2 次（含失败） | 0 |
| 本地模型进程启动 | Mac ≤ 6、5060 ≤ 6（含失败） | 正式 + 诊断合计 ≤ 10（`http` 时 5060 服务启动同计；诊断 Play 的启动计入此上限，不计正式 ID） |
| 本地模型查询行数 | Mac：测量 ≤ 2 轮 × 35 = ≤ 70；5060：等价 2 形态 × 32 = 64 + 测量 ≤ 2 轮 × 35 = ≤ 134；`replay-demo`/测试不计（无模型） | 每次 Play（正式或诊断）≤ 40 次查询（指定 + 重试 + 核验），合计 ≤ 400 |
| 下载/传输 | base 权重到 Mac 约 4.26 GB（1 次，校验失败可重试 1 次；5060 已有）；C2 adapter 69.8 MB 经局域网/T7 到 5060；pip 钉版装入 `.venv-language`；不发布、不上传公网 | 否 |
| 复算 | 无 609 行复算 | 否 |
| Jetson / 云端 | 否 | 否 |

信封内的工程性重试与 supersession 由接受角色在「决策记录」记一行归因；任何越界回到用户。

## 6. 限制与不承诺

1. 不主张跟踪性能、恢复能力、ReID、开放词表、真实航拍、跨场景迁移或 Jetson 性能；描述性数字不构成 Success@IoU 类指标，也不补证 SFT-002 功能门。
2. 模型能力的已知短板随用（事实 10）：歧义六成不报、贴边误报 none 一成多、S 层过半失败、`car` 类最弱；演示指令 `the red car` 依赖颜色词；核验因此会有疑似误报。
   本项以人工确认、有界重试与连续计数兜底，不改模型；失败按 AC-14/15 如实记录。
3. 核验是语义一致性，不是身份一致性：另一辆红车替换原目标时核验会报 `consistent`，本项如实披露，不作 ID switch 主张。
4. 单人操作：Play 阶段用户既跑 Unity 也当操作者，按操作单 C 执行；Unity 证据只认用户 Unity 日志。
5. `base` 形态只在用户点名时使用，结果分列；`c2-adapter` 回退形态的时延预计高于合并形态（事实 11），K_max 随之变大，报告如实写等待时间。
6. `EVAL-001` 的评估纵横比缺陷、`CoverageEvaluator` 真值隔离、既有控制链路的安全/系留假设随复用保留；本项不读 `metrics.json`、不读任何真值 sidecar。
7. `K_ret/K_conf/K_pub` 常数、6.0 s、`T_conf`、`T_stall`、`T_hard`、`attempt_limit`、`T_v`、连续 2 次、IoU 0.5/0.9 都是申请值，由接受角色裁定；不凭它们冻结任何合格线。
8. 核验提醒会晚于真实离画（周期 `T_v` + 连续 2 次 + 模型时延），P1 的 E1 判定按核验源帧而非离画瞬间；本项不主张检测延迟指标。

## 7. 必经停点

- **合并停点短名 `K1K3`**：阶段 A 候选 1 一次通过 `K1`（三个桥文件、检查点与拒收、静音播种、发布最终门与收据、停帧/坏元数据映射、`tracker_state` 镜像、K 收据与宿主规则 → AC-1…4、10、11）
  与 `K3`（三态→确认→播种、有界重试、重指定与谱系、核验语义、worker 与请求生命周期、模型身份与后端、等价 → AC-5…9、12、16、17）；核对轮 `C<n>@K1K3`、复核轮 `R<n>@K1K3`，计数按该停点累计。
- **阶段 B**只产出 Play 证据，不新增接口；Play 暴露缺陷且修复 diff 非空（PLAY_GOVERNING）时，修复回**同一** `K1K3` 停点、沿用其 C/R 计数与 K1/K3 覆盖，是否开新复核轮按 workflow §4.4 判；
  复核通过且用户另行签发阶段 B 信封前不得正式或诊断 Play。
- **`K2`**：D3 已删除 `--on-suspect hold`，本项无由 VLM 语义结果触发的自动控制动作，协议失败仍自动 finalize（§3.4 边界表）；播种瞬态静音按 D2 裁定 (b) 作为 `K1` 方向设计。本稿不申请 K2；若接受角色仍认定某项
  属 K2，构思侧先向用户提出具体范围选项取得裁定，不以合并候选替代授权。不触发 `K4`、`K5`（另立）。
- `DONE` 三证据：实现者证据（AC-1…12、16、17）+ 独立复核通过 + 用户 Unity 证据（AC-13…15）；阶段 A 结束只记 `IMPLEMENTED`。AC-13 `NOT_MET` 时工作项不能 `DONE`，处置回用户。
- 提请接受角色一并裁定：(a) 申请常数（6.0 s、`T_conf` 10 s、`K_pub` 2、`T_pub` = `K_pub/hz`、`T_stall` 3 s、`T_hard` 60 s、`T_v` 10 s、连续 2 次、IoU 0.5/0.9、`attempt_limit` 3）；(b) AC-13 离画事件裁定窗口与优先级是否唯一、客观；
  (c) **设计轮收口边界（提请）**：D4 闭合 AD3-1…4 后，若审查再发现同粒度残留（枚举一致性、单一机制的调用顺序细化、诊断口径措辞），构思侧提请改在 `ACCEPTED` 合同的「Pending rulings」按实现期裁定处理、不再开设计轮；
  是否采纳由接受角色裁定，未采纳则仍按 workflow §4.2 上交用户。

## 8. 只读试读与试运行数字（2026-09-19 本机只读；零写入、零 ID、零模型运行）

| 对象 | 数字 | 用途 |
|---|---|---|
| 冻结评估集 `outputs/eng-sft/P1-ENG-SFT-002/data/eval.jsonl` | 609 行、634,764 B（约 1,042 B/行）；分组 G1 210 / G5 100 / G4 86 / G3p 50 / G2 49 / G3 48 / G1t 23 / G2t 23 / G3t 12 / LEGACY_ONLY 8 | 引用结果，不作 selector 输入 |
| 盲索引 `data/eval.blind.jsonl` | 609 行、112,096 B；字段 `frame_path/g4/row_id/surface/vocab`（无 gold）；`g4=true` 86 行；`vocab` 全为 `unity-v2`；引用帧 392 张 | 回放索引 |
| 回放连接（AR1-3） | C2 `eval-adapter.jsonl` 与 base `zero-shot.jsonl` 各 609 行，`row_id` 与盲索引 609/609 一一对应、无缺多；键 `(sha(frame_path), surface, g4)` 唯一 605 个，重复两组（4 行、2 行），两组在 C2 与 base 中各行 `(raw_output, finish_reason)` **均相同**；C2 `finish_reason` 全 `stop`、`parse_error` 0；base `length` 31（→ `TRUNCATED`）、`SCHEMA_ERROR` 72 | §3.5 重复键规则与截断路径的真实样本 |
| 回放帧 `upload/frames/` | 2,327 张 640×480 JPEG，115 MB（约 49 KB/张）；评估清单记帧 448 张、19.76 MB | 回放桩帧源；夹具只取具名子集 |
| smoke 集 `data/smoke.jsonl` | 32 行、26,108 B（25 帧） | 时延测量与等价样本 |
| C2 adapter | `adapter_model.safetensors` 69,788,264 B，sha `4044dd4f…2d37`；base revision `89644892…4203` | 合并输入 |
| 帧包样本 `runtime/frames.1b-diagnostic-hold/frame_0000000012.*` | JPEG 31,042 B + JSON 1,118 B | 128 帧保留窗约 4.1 MB；追平 k 帧读盘约 32 KB × k |
| 5060 自检时延（未合并） | base 零样本 4 行 p50 1,726 ms / max 3,053 ms；adapter 4 行 p50 5,433 ms / max 16,973 ms | §3.3 阈值量级依据；合并后应回到零样本量级（待实测） |
| 本机环境 | `.venv-yoloe`：Python 3.12.13、torch 2.13.0、MPS 可用、无 transformers；`.venv-track`：无 torch；HF 缓存空 | 阶段 A Mac 侧需新环境与 base 权重下载 |

内存投影：`local-hf` bf16 2B 约 4.5–5 GB 权重 + 激活，Mac 16 GB 统一内存下与 Unity 同机运行是否可行**未实测**，属 AC-10 的实测对象；
5060 8 GB 显存已跑通 bf16 推理与 5 步 LoRA（自检）。

## Contract conformance（核对表）

**C6@K1K2K3（2026-09-23，Owner：Acceptance；本停点第二次核对，交 R7）。** D4 的 engineering-v1 合同及 R-B8…11 维持。候选按 `docs/evidence/P1-ENG-LOOP-001-K1K2K3-c5-fix.md` §1 运行时定位；完整 diff 基线为同名复核文件最后一条 `passed_candidate`（R6）。已先列清单，再核对完整候选涉及的 24 个文件、C5→C6 修复 diff、适用 AC、实现者证据及 `TrackLoop._body_step`、`_build_body_runtime`、`GatedPublisher._gate` 与会话日志路径；其间接受裁定、授权、诊断与旧复核文件仍属候选 diff，不从范围排除。范围分组如下：

| 范围 | 文件与核对 |
|---|---|
| 运行时与测试（3） | `controller/gated_publisher.py`、`controller/language_loop.py`、`tests/test_language_loop.py`：按 K1 同帧门、K2 速度/安全 hold、K3 段身份与终止逐项核对；`controller/body_planner.py`、`controller/track_loop.py`、`config/`、`Assets/`、`ProjectSettings/` 相对 R6 无 diff。 |
| 操作载体与自证（14） | C5 所列 11 文件，加 `docs/evidence/P1-ENG-LOOP-001-{K1K2K3-c5-fix.md,k1k2k3-c5-fix-selftest.log,tests-k1k2k3-c5-fix.log}`：C5 修复集中在 `-lap-samples.py`、`-frame-keeper.py`、`-c2-carrier-selftest.py`、`-operations-c.md`；旧传输清单仍属 R6 执行史，不视为新候选已传输。 |
| 关联事实源（7） | `docs/{authorizations.md,current-status.md,implementation-status.md,phase1-single-drone-design.md,proposals/P1-ENG-LOOP-001-language-select-closed-loop-integration.md,reviews/P1-ENG-LOOP-001.md,evidence/P1-ENG-LOOP-001-stage-b-prep.md}`：逐文件核对用户原话、R-B8…11、R6 消费和诊断5；这些是候选 diff 的组成部分，不冒称本轮实现或独立复核。 |

实现自证见 handoff §2–§6 与 c5-fix §2–§5。C5 修复的六项具名反证修前红、修后绿；载体自测 117/117；全套 1534 例、0 failures、9 个与 C5 前逐名相同的环境 errors、68 skips，新增失败 0；归档相关 skip 不作闭合证据。本角色只读日志、代码和工件，未运行实现测试。R6 `PASS_WITH_NOTES` 只覆盖旧 K1K3 范围；本轮不签独立 verdict。

| 编号 | 结论 | 理由（候选侧与尚缺证据分开） |
|---|---|---|
| AC-1 | 满足 | 三桥、写者锁与请求回执路径相对 R6 未改；R6 §1 已核实 F7 红绿，`-k1k2k3-carrier-selftest.log` §2 保留同 ID 自测。新收据闭集限发布日志，不改桥 schema。 |
| AC-2 | 满足 | 查询/返回/确认检查点未改；`tests.test_language_loop` 原 StaleRejection 路径和 focused 326 结果在 handoff §2/§3。 |
| AC-3 | 满足 | `gated_publisher.py` 的观测写前五项 `_gate` 未改；速度复用同帧 `accepted_frame_id`，失败收据与回退见新增 `BodyPlannerIntegrationTests`；是否有未覆盖并发/写盘路径交复核。 |
| AC-4（含修订4） | 满足 | `language_loop.py` 的 `BodyRuntime.fresh` 每段深拷贝规划器/估计器；`GatedPublisher.finalize` 后不写，新增段切换与后备失败测试覆盖。真实 Unity 机身运动仍待获准诊断。 |
| AC-5 | 满足 | 确认与预览核心、操作页相对 R6 未改；沿 R6 已通过范围与 handoff §3 零改动机检。 |
| AC-6 | 满足 | 重试与歧义状态机未改；沿 R6 通过范围，focused 日志含原测试。 |
| AC-7 | 满足 | 原人工判丢、重指定、段退休路径未改；新增 `test_each_segment_gets_its_own_planner_and_nothing_is_written_after_retirement` 检查第二段独立性。 |
| AC-8 | 满足 | 模型适配、HTTP 与身份 schema 未改；新增配置只在 Play `run` 入口绑定，5060 传输集合由清单构建器限定。 |
| AC-9 | 满足 | 回放与等价资产未改；原 2/32 不等价及 c2-adapter 选择不重判。 |
| AC-10 | 满足 | K 收据与宿主数字未改；`bind_body_runtime` 另核 `capture_hz`、命令有效期 2/hz 及生效场景；真实发布时效待诊断。 |
| AC-11 | 满足 | `-tests-k1k2k3-c5-fix.log` 记录停点全套 1534、0 failures、9 个既有 errors、68 skips；c5-fix §4 披露与 C5 前日志逐名相同，新增失败 0，本角色不重跑。 |
| AC-12（含修订6） | 证据缺失 | `-operations-c.md` §1–5 与 `-operator.sh` 冻结顺序、既有标签及样帧步骤；`-build-stage-b-manifest.py` 将 gate 源码纳入传输。新候选尚未独立通过，采集 checkout/5060 对齐、诊断6/7与两张具名样帧确认尚不到执行时点，不能提前算完成。 |
| AC-13（含修订2） | 证据缺失 | `-lap-samples.py` §`analyse` 改用帧仿真时刻与处理序判窗口，末帧晚处理的拒收/退役纳入；`read_jsonl` 对四份必需日志缺失/坏行 fail-closed。C5-1 的同帧 `WRITTEN`、C5-2 的 t0+106.5≤220 s 与 C5-3 的保存 JPEG/索引/加载快照三方哈希均已有代码和具名反证（c5-fix §2–§4）；≤220 s 按 Play 起点仿真时刻解读，属保守读法。正式 Play、九图逐张人工核对及一圈结果仍未到证据时点；索引仿真时刻与保存 JSON 元数据完整性的待核实风险见 C6-1。 |
| AC-14 | 证据缺失 | P2 正式 Play 未运行；旧协议与操作单 §6 保留，不能以载体自测代替用户 Unity 证据。 |
| AC-15 | 证据缺失 | `-operations-c.md` §7 规定逐次描述与失败清单，但正式 Play 0/8，报告尚无真实结果。 |
| AC-16 | 满足 | 核验配对、verdict 与人工解除路径相对 R6 未改；F3 排队计时债仍按 implementation-status 账本 OPEN。 |
| AC-17 | 满足 | 八态九动作及 worker 未改；新 `BODY_COMMAND_FAIL_CLOSED` 沿 AC-4 修订2 记原事件并终止，`test_a_failed_fallback_hold_fails_closed` 核对单次退休。 |
| AC-18 | 满足 | 页面相对 R6 零改动，R6 §1 已核实 F7；真实浏览器点击/人眼呈现仍须获准诊断，C5 不冒称该证据已经存在。 |
| AC-19 | 满足 | `bind_body_runtime` 复用冻结 `_build_body_runtime` 并拒绝配置漂移；`TrackLoop._body_step` 仍是唯一图像机身命令入口；新 `GatedPublisher.body_command` 将速度绑同帧 WRITTEN 观测，将安全 hold 单列收据，写失败后备失败按冻结路径 fail-closed。新增十项中六项在 R6 门上红，候选绿；此为候选符合性核对，须独立复核及真实诊断。 |

**C6 结论与预复核关注项。** C5 的两项退回已有代码修复及具名反证；C5-1…3 取保守读法，逐项见上。正式 Play 与人眼证据尚缺，AC-12…15 不能提前算通过；本停点已退回一次，按 workflow §4.3.3 将候选、核对表及以下未决关注照交新鲜上下文 R7@K1K2K3，不新增或改写 AC，不给 finding 分级或依据值。

| 编号 | 位置 | 待核实问题 |
|---|---|---|
| C6-1 | `-lap-samples.py` 的 `analyse`/`position` 与 `-frame-keeper.py` 的索引写入 | 取样只把保存 JPEG 哈希与索引 `jpg_sha256`、观测 `snapshot_sha256` 比对；索引 `simulation_time_s` 和位移所用保存 JSON 的字节未与索引 `json_sha256` 或段运行记录交叉核对。请复核索引或 JSON 意外损坏/错配时，会否错选九图或误报位移；这是待核实主张，不自定分级。 |
| C6-2 | `-lap-samples.py` 的 `window_not_fully_processed` 与操作单 §5 第 4 步 | 操作单见「一圈窗口已满」后即可停会话，但脚本要求出现第一次只处理窗口之后帧的 `frames_processed`。请核对实际操作停点是否可能产生保守的假阴性，并确认操作指令与机械门的一致性。 |

预算、F3 债与旧复核结论不变。本轮零 Play、模型、ID、传输及测试；新 K1K2K3 候选未独立通过，继续禁止消耗性动作。

## 决策记录

| 日期 | 轮次 | 结论 | 理由指针 |
|---|---|---|---|
| 2026-09-19 | D1 | `PROPOSED` | 构思侧落盘；用户五项范围定局见账本「2026-09-19 P1-ENG-LOOP-001 — 立项点名与五项范围定局（方向层，不授予执行额度）」；代码事实 §0；`engineering-v1` 为申请，待接受角色裁定 |
| 2026-09-19 | D1 | `REVISION_REQUESTED` | Acceptance：方向与五项用户定局保留；当前接口不能按字面安全、完整地实现，AR1-1…6 须由构思角色在 D2 逐项回应。设计退修 1，C/R 尚未开始；不冻结 AC/schema/阈值，不授予执行额度。 |
| 2026-09-19 | D2 | `PROPOSED` | 构思侧回应 AR1-1…6（映射见抬头「AR1 → 本稿」）：§3.3 检查点与静音发布器、§3.4 全表、§3.5 适配/回放/测量、§3.6 角色 B、AC-1…17、§5 总计口径、§7 `K1K3`；用户同日追加定局 ⑥「VLM 为辅助系统，提醒时决策主要由人负责」见账本同名条目；D1 裁定原文原样保留于下；`engineering-v1` 仍为申请 |
| 2026-09-19 | D2 | `REVISION_REQUESTED` | Acceptance：第二次设计退修，AR2-1…6 见文末 D2 裁定；保留用户定局 ⑥ 与有效修正，按 workflow §4.2 上交用户二选一，路由与执行信封未生效；C/R=0/0。 |
| 2026-09-19 | D2 后用户处置 | 用户选择 (a)，保留范围并继续修正 | 用户原话 "A"，账本同日「用户处置第二次设计退修：保留范围并修正 AR2-1…6」；交构思 D3，六组缺口不豁免，退修计数 2 与 C/R=0/0 保持；未授予执行额度，未 ACCEPTED。 |
| 2026-09-19 | D3 | `PROPOSED` | 构思侧按用户 (a) 处置修正 AR2-1…6（映射见抬头「AR2 → 本稿」）：发布最终门与收据、提醒/控制边界（删 `--on-suspect`）、请求令牌/单槽回执/worker 生命周期、核验配对与单计数器、三段时间预算与 AC-13 终态闭集、先资格后分档与全计信封；D1/D2 裁定原文保留；设计退修计数 2 保持；`engineering-v1` 仍为申请 |
| 2026-09-19 | D3 接受侧审查 | `AWAITING_USER_DISPOSITION`（未 ACCEPTED；不新增第三次退修） | 设计方向及本轮有效修正保留；固定残留 AD3-1…4 见文末。依 workflow §4.2 上交用户，设计退修仍为 2、C/R=0/0；路由、合同与执行信封未生效。 |
| 2026-09-19 | D3 后用户处置 | 用户选择 (a)，保留范围并继续修正 | 用户原话 "选A"，账本同日「用户处置 D3 审查残留 AD3-1…4」；交构思 D4，四项残留不豁免，退修计数 2 与 C/R=0/0 保持；未授予执行额度，未 ACCEPTED。 |
| 2026-09-19 | D4 | `PROPOSED` | 构思侧修正 AD3-1…4（映射见抬头「AD3 → 本稿」）：加载时快照与写前守卫五项、提交/轮询式单工 HTTP 与写者锁、`outcome`/`reason` 闭集补齐与确认失败拆分、事实 16 收窄与 AC-13 离画事件裁定、诊断会话零正式 ID、§7 设计轮收口边界提请；D1/D2/D3 裁定原文保留；退修计数 2 保持；`engineering-v1` 仍为申请 |
| 2026-09-19 | D4 接受侧裁定 | `ACCEPTED`；engineering-v1 生效 | AD3-1…4 由 D4 及八行首次接受释义闭合；AC-1…17 稳定，K1K3 保持。设计退修 2、C/R=0/0，阶段 A/B 信封仍待用户逐字授权；正式设计 v0.3.43。 |
| 2026-09-20 | 实现期合同裁定（不开 D/C/R 轮） | D4 `ACCEPTED` 保持；报告 §9 八问已答复 | 待裁定 P-A-1…8 转录并追加八行同编号 AC 修订（新 AC=0）；缺预览不准确认播种，不能以 null 退化宣称 AC-5 满足；其余保留或限定映射。阶段 A 签发及实现会话「先代码+测试，实测再议（推荐）」已核对/补账，额度不变；交实现落实与补证，未达 K1K3 停点。正式设计 v0.3.44。 |
| 2026-09-20 | 实现期 P-B-1 裁定及用户指定增量查看（不开 D/C/R 轮） | D4 `ACCEPTED` 保持；P-B-1 选择 (a) | 追加 AC-16 修订 2（实现期累计九行、新 AC=0）；代码关注 U-A-1…3 见核对表下的非 C 轮记录，交实现核实修正，不给实现通过结论。正式设计 v0.3.45；阶段 A 原信封不变，B 未授权。 |
| 2026-09-20 | P-B-2 实现期裁定及用户指定增量查看（不开 D/C/R 轮） | D4 `ACCEPTED` 保持；P-B-2 采用 (a) | 追加 AC-16 修订 3（实现期累计十行，新 AC=0）；P-B-1、U-A-2/3 已见对应修复，U-A-1 仍有恢复状态请求跨原截止残留。具体边界见最新非 C 记录，正式设计 v0.3.46；不新增资源授权。 |
| 2026-09-20 | U-A-1 残留与 P-B-2 修复查看（不开 D/C/R 轮） | D4 `ACCEPTED` 保持；具名修复静态关注收束 | 完整八文件增量已读，U-A-1 三处恢复守卫、P-B-2 五值诊断与 AC-8 loop 侧超时仍 busy 用例均有对应实现；最新非 C 记录列明证据边界。合同十行修订不变，实测和正式 C/R 仍未完成。 |
| 2026-09-20 | 核对轮 C1@K1K3（Owner：Acceptance） | 核对通过，交独立复核 R1@K1K3；C/R=1/0（C 退回 0） | 阶段 A 候选 1（交接提交，由 git 运行时解析；本轮写入期间 HEAD 被一笔纯文档协调提交推进一格，与候选零文件重叠）逐项核对结论见上文「Contract conformance」：AC-1…12、16、17 满足，AC-13…15 未到阶段 B 证据时点；五条预复核关注项 C1-1…5 随附，不定 finding 分级。信封内失败/回退/supersession 归因（工程轨道决策记录一行）：Mac 合并 2/2 均失败（首试进程在权重加载后消失、无产物；次试 exFAT AppleDouble 旁文件导致导入失败）与 5060 等价 32 行中 2 行不等价，均落入合同既有条款（§3.5 合并失败或等价不成立 → 唯一自动回退 `c2-adapter`），失败计数照计、原始记录保留，不构成范围或预算偏差；5060 首次服务启动后进程消失、无收据，为避免漏计保守补扣 1 次启动；K 绑定身份缺口属 AC-10 修订 1 范围内的实现修复——修前 35 次查询证据保留为 `before-binding-*` 系列、修后 35 次独立计算不合并样本，为信封内 supersession；5060 两次 SSH 超时零消耗；T7 exFAT 全套失败轮为环境失败单列、不算通过。全部计数在阶段 A 信封内（Mac 合并 2/2、加载 3/6、查询 35/70、下载 1/1；5060 合并 1/2、启动 6/6、查询 134/134、下载 0），无越界、无新增授权；阶段 B 仍未授权。 |
| 2026-09-22 | 消费 R2@K1K3（Owner：Acceptance；不开新轮） | `REVIEW_PASSED`；阶段 B 未授权，未 DONE | 消费同名复核 R2 的 PASS_WITH_NOTES，F1/F2 CLOSED；F3 按原 SCOPE_GAP 记债 OPEN。机械归因：BC-1 → 实现错误 2，SCOPE_GAP → BC 缺失 1（非阻断），其余依据 0。C/R=1/2、C退回0、R返工1；合同未增改。注记处置及阶段 B 申请见文末固定复判节；本次零消耗，预算未签发。 |
| 2026-09-22 | 用户签发阶段 B（不开新轮） | 阶段 B 信封生效；复核门保持 REVIEW_PASSED | 用户原话“签发”，逐字入账见 authorizations 同日「签发阶段 B（Play 证据）执行信封」；批准文末申请的原额度与先诊断次序，交实现准备操作单 C、用户执行 Play；未改变 AC、K 或 C/R，本次入账零消耗，尚无 Unity 证据。 |
| 2026-09-22 | R-B1…4 合同裁定与代录（不开 D/C/R） | `ACCEPTED` 单字段例外；阶段 B 暂阻 | 用户已选改设置及追加2诊断；追加 AC-4修订3/AC-12修订3，旧诊断3/2超用1如实保留，新额度0/2。诊断1环境中断、诊断2操作/环境未完成、登记外Play及恢复目录漏检为流程偏差；非复核finding，不改原机械归因。设置待实现，C2→R3后再诊断，正式首批追平/人眼前提未满足；模型启动2/10、查询1/400、正式0/8。 |
| 2026-09-22 | 核对轮 C2@K1K3（Owner：Acceptance） | 核对完成，附未决项交复核核实资格；C/R=2/2（C退回0） | 最新核对表：AC-11/12不满足、AC-13…15证据缺失；C2-1…3为待核实主张，先核实§4.3.1再决定是否开R3。合同不变，零实现/测试/模型/Play/传输；R2仅原候选，Overall继续BLOCKED_UNITY_FOCUS_PAUSE。 |
| 2026-09-22 | R-B5…7 合同裁定与代录（不开 D/C/R） | `ACCEPTED` 按钮页例外；交零消耗实现 | 用户原话入账；新增AC-18及AC-12修订4/5。诊断3/4均未播种，执行归因为可见窗/操作耗时及操作单误述，非独立finding。旧诊断3/2超用1、上次2/2、本次0/3，正式0/8、启动3/10、查询3/400；新候选走C3→R5，计数/终局限制不重置，未通过前停Play/模型服务。 |
| 2026-09-23 | 核对轮 C3@K1K3（Owner：Acceptance） | 核对完成，附C3-1…3交复核核实资格；C/R=3/4（C退回0、R返工2） | 最新Contract conformance：完整20文件diff与六个冻结载体已读；AC-12/18不满足、AC-13…15证据缺失，其他条款及AC-11的隔离基线证据保持。R5须新鲜上下文，旧例外/返工额度不延伸；本轮无合同变更、无实现测试或资源消耗，R5通过前Play/模型服务仍禁止。 |
| 2026-09-23 | 核对轮 C4@K1K3（Owner：Acceptance） | 核对完成，附C4-1交复核核实资格；C/R=4/4（C退回0、R返工2） | 按用户选择修复后的完整20文件候选已读；C3-1…3原场景有对应修复，AC-12满足、AC-18不满足、AC-13…15证据缺失。依据见最新Contract conformance；原归因、预算、合同和终局限制不变，R5须新鲜上下文；零实现测试/资源消耗，未放行Play/模型服务。 |
| 2026-09-23 | R-B12…13 实现期裁定（不开 D/C/R 轮） | `ACCEPTED` 保持；诊断 6 段 2–4 `catchup_stale` 硬停止归因为 K1 单批追平语义，新候选回 K1K2K3 | 门拒收正确、无 finding、机械归因不变；追加 AC-3 修订 3（初始化后静音直至积压 ≤ K_pub 才 unmute 过门，T_catchup 6 s fail-closed，K_pub/T_pub/T_stall/五项门不变）与 AC-12 修订 7（入画即指定、优先第 2 窗起点；诊断 7 仅新候选 R8 通过后用；正式 P1 连续 2 次同类失败回用户）；实现期修订累计 19、新 AC 累计 2；诊断追加 2/3、正式 0/8、启动 5/10、查询 20/400；正式设计 v0.3.50；本批零测试/代码/Play/模型/ID/传输。 |
| 2026-09-23 | 用户暂停返工（不开 D/C/R 轮） | `ACCEPTED` 保持；Lifecycle PAUSED，C7/R8 未开 | 用户原话见账本同日「用户暂停 AC-3 修订 3 返工，快层替换探针先出数据」；合同、修订、verdict 与余额不变；快层替换探针另立新工作项；恢复或收口待探针数据后由用户二选一。 |
| 2026-09-28 | 收口裁定（不开 D/C/R 轮） | `CLOSED_SUPERSEDED`；Lifecycle `ENDED` | 用户同日 D.3 已裁定由 `P1-ENG-ACQ-001` 取代；本项停止且不签 `DONE`。保留 F3/F8 `SCOPE_GAP`/OPEN、AC-13…15 `NOT_RUN` 与诊断 6 人眼记录；远端/本地清理承接，阶段 B 未用余额作废。详见下节与 `docs/parked-status.md`。 |

### 收口裁定（2026-09-28，Acceptance）

依据 `docs/authorizations.md` 同日「全局 — 用户按推荐入账：主线目标锚定…」D.3，本项收为 `CLOSED_SUPERSEDED`，被未来 `P1-ENG-ACQ-001` 取代。`CLOSED_*` 仅表示停止本范围工作，不是实现、独立复核或 Unity 验收通过，不产生研究主张。D4 接受与 R7@K1K2K3 `PASS_WITH_NOTES` 保持其原候选与旧追平语义的历史效力；AC-3 修订 3/AC-12 修订 7 未实现，C7/R8 未开，诊断 6 的 `catchup_stale` 硬停止保留。

承接 `P1-ENG-ACQ-001` 的未闭清单：

1. F3/F8 `SCOPE_GAP` 均 `OPEN`，唯一债务入口继续是 `docs/implementation-status.md`「范围外已知缺陷」原 work ID/F3、F8 行；F3 的 LanguageWorker 在途起点与延迟/排队回归、F8 的可变归档元数据哈希/时刻一致性回归及异常停用条件逐字按账本行承接，不销账、不改原 verdict。
2. AC-13…15 的正式 Play 验收仍 `NOT_RUN`；诊断 5/6 不是正式证据。新项须承接未验证的闭环行为和失败记录，不把本项记为 `DONE`。
3. 诊断 6 两张具名样帧的人眼保真记录保留：帧 22 `q2` 用户确认「一致，框在红车上」，帧 64 `q3` 用户确认「一致，两框都在红车上」；来源 `docs/unity-test-log.md`「P1-ENG-LOOP-001」与 `docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md` §13.3。新项触及采集、保存或预览路径时须重做核对。
4. 5060 F 盘 `repo-b` 副本、`runtime/hold-diag-loopb-*` 隔离物及诊断 6 留在 `runtime/` 的桥文件与帧，清理义务由新项承接；本轮不删除。来源见 `docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md` §13 与操作单 C §2.3。

阶段 B 已用量：追加诊断 2/3、正式 0/8、模型启动 5/10、查询 20/400、拒绝 0。未用诊断 1（`diag-loopb-7`）、正式 8、启动 5、查询 380 随收口作废，不转用；新项无本信封执行权限。新项尚无提案/Gate 行，本裁定不预签其合同、门值或额度。零测试、零 Play/模型/API/ID、零文件清理。

**接受侧 D1 裁定（2026-09-19，Owner：Acceptance）。** 本轮是提案决策，不是实现核对或独立复核。
已读状态板全交接、两轨流程、角色细则、方向授权、正式设计 §1/§2/§3/§5、工程继承清单与缺陷账本，
沿 ASSET-001 报告 §5、TRACK-002 冻结核心、SFT-002 最终通过证据核对本项直接依赖。
只读查阅现代码及既有 JSONL；未运行实现测试、模型、下载、Play 或创建正式 ID。
`engineering-v1` 仍为申请，未 ACCEPTED 前按缺省流程约束；本轮不改已接受设计、不否定既有 verdict。

| 编号 | 具体缺口与依据 | D2 必须交付的修订与核对落点 |
|---|---|---|
| AR1-1 | **K1 尚未隔离旧帧的实际控制副作用。** `controller/track_loop.py:336-384` 的 `initialize(N,…)` 会立即 `_publish_latest`，经 `:644-674` 发观测及 follow 云台命令；`controller/protocol.py:23-35` 将发布时间写成现在，Unity 接收器只按该时间过期，不能靠观测里的 N 阻止旧图驱动当前控制。`process_available` 在 `:536-602` 逐帧记日志但只发布批末观测，且只在批末赋 `self.state`，不同于 §3.3/AC-3 的逐帧发布叙述。§3.3 确认时仅重查文件存在：返回时合格、确认时已超 K_max 仍会播种；`latest−N<0` 也满足现上界。帧重置后同名文件存在不保证仍是查询图像。 | 明确在新会话层怎样抑制初始化/历史追平的观测和控制发布、何时允许发布当前结果；保持旧 TrackLoop 一次性语义和既有控制协议。对查询、返回、确认、追平结束分别写明时效与身份检查、截止时间起点、帧回退/停帧/同 ID 换图/中间缺帧的拒绝出口；确认须重核绑定的图像与元数据，不能只测路径存在。AC-2/3/4 对应具名测试须能区分「日志记录」与「写 Unity 桥」并覆盖确认超时、负帧差和初始化副作用。若方案实际改变安全约束/控制命令而非保持既有语义，先交用户裁定 K2，不以 Unity 零改动自动豁免。 |
| AR1-2 | **会话转移与闭集互相矛盾。** §3.2 将 respecify 的 instruction 同时写成必填与可省略；§3.4 允许 TRACKING→LOST 后自动回 TRACKING，却在 §2.2 声明不做自动恢复，且用户只选「仅人工重指定」。批内 LOST→TRACKING 会被现 `TrackLoop.state` 最终值吞掉。跟踪中拒绝 respecify 后建议先 stop，但 stop 是 TERMINAL，无后续重指定出口；GAP 行已 retire，REINIT_REQUIRED→respecify 又 retire 一次。QUERYING 中 stop/旧 worker 回包、无新帧时的重试等待没有定义。 | 给出本项已列七态 × 五动作的处理规则（可用默认拒绝合并），明确 stop 是否需新会话，旧段只 finalize/retire 一次，失效请求/结果与会话身份如何隔离。按用户定局消除自动恢复分支，或把保留段内自恢复的具体例外提请用户，不能由实现解释；定义批内 LOST 的捕获与人工恢复期间的发布策略。明确无新帧、后端未返回、stop 后迟到回包的有界退出；补全 `REQUEST_INVALID`、retry 最后原因、replay 身份和未取得帧时结果字段的存放/可空规则。将这些可达分支挂到 AC-1/4/5/6/7；不得把原子写文件等同于请求已被消费。 |
| AR1-3 | **后端不能按现合同直接复用。** `RawSelection`/HTTP 只返回 raw_text 与时延，但 `parse_prediction` 需 `finish_reason` 才能维持达到 token 上限即 TRUNCATED 的既有语义。真实预测文件没有 frame_sha256/surface，只有 row_id；只读核对 C2/base 预测各 609 行，与 eval 的 row_id 609/609 绑定，无缺多；eval 的 `(frame_sha256,surface)` 只有 605 个唯一键，两组重复键分别 4 行/2 行（当前 C2 的各组 raw_output/finish_reason 相同）。此外 `load_model` 只负责加载，实际 `predict_rows` 要求 frame_path/surface/g4/vocab/row_id，不能把裸 select 参数直接当现成推理入口。 | 补完统一推理的输入适配和输出（至少保留 finish_reason、模型/模板身份），HTTP 与 replay 不丢解析终止原因；不复制冻结解析器/模板。写明 prediction→row_id→盲索引/帧路径的连接与来源校验、重复键相同/冲突的确定处理，以及缺文件/缺行/模型身份不符时的失败。运行时选框只用图像/指令及必要索引，不将 eval gold/object 真值送入 selector。AC-8/9 增补截断、重复冲突、缺映射和身份不符的核对点；补只读连接数字，不需重跑模型或重建 SFT 数据。 |
| AR1-4 | **宿主与回退规则不完备。** §3.3 对 Mac=10 s、5060=30 s 无分支；加载失败/OOM 也无分支。合并失败时 §3.5/AC-9 要用未合并 C2，CLI 却只有 c2-merged/base，§6 又把该失败当 base 回退条件；实测合并模型的时延不能用于未合并实际模型的 K_max。HTTP 测量需要 timeout，而 timeout 又依赖测量后才能定的 K_max。`ceil(p95×5)+2` 在 p95=24 s 为 122，封顶 120 已失去所称余量。 | 统一实际模型的合并失败回退及 CLI 枚举，按最终运行的模型形态/设备测时延；列全两宿主成功/失败及阈值边界的决策分支。固定测量的端到端计时边界、p95 算法、预热/失败样本处理、测量期 timeout 与保留窗不足的退出；实际配置的帧率/保留数必须与计算绑定。合并核对不能只比 ambiguous 状态而遗漏该态最终会被 confirm 的框，明确候选匹配与 parse_failed 的判定。AC-9/10 与预算使用同一组可执行分支；常数仍是申请值，不由实现看结果后改合格线。 |
| AR1-5 | **Play 主剧本的必过链路缺少可达依据。** AC-13 将「驶出画面」直接接成 LOST/REINIT_REQUIRED；冻结 NanoTrack 核心 `controller/trackers.py:437-488` 没有 score 阈值，有限低分仍是 ok=True，不保证画外目标产生 LOST，更不保证沿用跟随控制能让目标离画。`REINIT_REQUIRED(frame_gap)` 证明协议失败，不证明视觉丢失。AC-14 只列 ambiguous/unique，未覆盖模型 none、解析/后端失败及重试耗尽。 | 在 Unity/config 零改动、冻结跟踪器与仅人工重指定范围内，给出 P1 的具体操作、触发条件及未触发时 FAIL/BLOCKED 的归属，区分自然视觉失败与故障注入证据；不得暗加 score 门或拿 GAP 冒充视觉丢失，也不得用回放桩替代 AC-13 的真实 Play 成功。若需缩改 AC-13 或新增失踪判定范围，明确提请用户而不自行降门。AC-14 列全现协议可达结局及哪些满足「呈现/确认/如实报告」，真实歧义识别成功单列；AC-15 保留失败而不反复试到成功。 |
| AR1-6 | **信封和复核回路尚不能机械执行。** §5 只限制「有效 Play」，失败尝试总数无界；阶段 A 的 5060「各≤2次 + 重试≤2」无重试单位/总启动与行数上限，未列 5060 合并动作；609 行复算与 §2.2 不重跑表 G 的关系未界定。新会话会写 session/run 身份，但 A 仍要求零正式 ID，未说明 replay-demo 的隔离与来源。§7 把阶段 B 的任何修复送往 K3，会遗漏 K1 修复并重置原合并停点的计数。 | 重写申请信封的总计口径：成功/失败/重试都计入的启动数与模型行数、每设备合并/回退动作、Play 总尝试/时长/会话/段上限及耗尽出口；阶段 A 的夹具标识只存在隔离测试目录，不占用正式 ID 或共享 runtime 槽。609 行复算不列必做，也不借其重新选模/改 SFT-002 表 G；若保留可选执行，单列目的与明确额度待用户批。确认一个合并停点短名并在 C/R/交接中一致使用；B 的 PLAY_GOVERNING 修复回原合并停点、保留计数与 K1/K3 覆盖，按 workflow §4.4 判开轮，不固定只看 K3。复核通过且用户另行签发 B 信封前不得正式 Play。 |

**§7 三项提请的答复。** (a) `+2`/`−8`、6/24 s 暂不冻结，先闭合 AR1-1/4 的时间边界与分支；
(b) 可以把 AC-14 定为协议呈现与如实报告验收，模型只给 unique 并保持人工确认不必判协议失败，
但不能称歧义识别通过，且须按 AR1-5 补全其他结局；(c) 不要求 609 行复算，既有冻结结果可引用，
32 行实测/等价性与实际运行模型绑定即可。本段是 D2 修订方向，不是对 D1 部分签发 ACCEPTED。

**交回构思角色。** D2 保留本裁定原文，逐条回复 AR1-1…6 并同步正文/AC/预算。
方向授权已足够继续文档修订，本轮不重复请求用户确认；如选择扩大安全/恢复范围或改变用户定局，再提出具体选项。
执行信封待完整合同可审后由用户另行签发，本轮没有新增授权可入账。设计退修计数 1；若 D2 再退修，按 workflow §4.2 上交用户，不能自行进入第三次退修。

**接受侧 D2 裁定（2026-09-19，Owner：Acceptance）：`REVISION_REQUESTED`，第二次设计退修，上交用户。**

本轮范围为 D2 全文、AC-1…17、AR1-1…6 回应及直接复用接口的只读设计审查；不是 C 轮或独立复核。
已核对当前结构节及全交接（0 消耗性 + 1 零消耗）、接受角色细则、两轨流程、工程继承清单与缺陷账本、正式设计 §1/§2/§3/§5，
以及 ASSET-001 报告 §5、TRACK-002 冻结核心、SFT-002 通过轮与真实盲索引/预测文件。仅本提案与状态板写入；未运行实现测试、模型、下载或 Play，未创建正式 ID。
账本同日定局 ⑥ 支持角色 A「语言指定」与角色 B「语义核验提醒」；本轮不重新要求用户确认该方向，不将其解释为已授权自动控制或可靠身份识别。
正文仍是待修订的 D2；以下裁定不签发部分 ACCEPTED，不冻结 AC/schema/常数，也不修改正式设计或旧工作项 verdict。

**AR1 回应核对（设计层，非实现验收）。**

| 原项 | 本轮核对 | 保留的有效修正与未闭部分 |
|---|---|---|
| AR1-1 | 部分闭合 | 查询/返回/确认的帧差下界、图像哈希和时间起点已明确；初始化静音方向可保留。发布前最终门仍缺，见 AR2-1。 |
| AR1-2 | 部分闭合 | respecify 可省略、release 出口、终态与单次 retire 原则已明确；提醒/控制边界及请求、worker、失败 schema 仍有冲突，见 AR2-2/3。 |
| AR1-3 | 原接口事实缺口闭合 | 一行 rows 调 `predict_rows` 的签名与输出字段成立；`finish_reason` 保留、盲索引按 row_id 连接及重复冲突规则可行。只读实核：盲索引 609 个唯一 row_id，C2/base 各 609 行，无缺多；605 个复合键，重复组 4/2 行且输出与终止原因均相同；三份文件哈希与所指清单/摘要一致，盲行所引用图像哈希不符 0；base 的 length 31 行可作为截断样本。异步查询身份另见 AR2-3，不要求重跑 SFT 评估。 |
| AR1-4 | 部分闭合 | c2-adapter 唯一自动回退、ambiguous 框等价、固定测量超时与不再封顶的资格式可保留；配置边界、超时执行与失败轮出口仍需闭合，见 AR2-3/6。 |
| AR1-5 | 部分闭合 | 已获授权的提醒角色补上候选信号来源，E1/E2/E3 不混同，GAP 不冒充视觉丢失。核验配对、连续计数及真实 Play 的操作/完整结局仍缺，见 AR2-4/5。 |
| AR1-6 | 主要闭合，信封仍有缺项 | 总 Play 尝试计失败/中止、隔离目录、删除 609 行复算、回原 K1K3 且计数不重置均可保留；5060 合并动作与诊断推理归账仍须写明，见 AR2-6。 |

**尚未闭合的具体问题（本轮固定列 AR2-1…6）。**

| 编号 | 缺口、可达例子与依据 | 若用户选择保留范围，须明确的修正 |
|---|---|---|
| AR2-1 | **解除静音早于最终检查，批末不等于发布时的当前帧。** §3.3 在第一次 `process_available()` 前 unmute；现代码 `controller/track_loop.py:411-435` 只在调用开始取一次 latest，`:536-602` 在返回前已经发布。确认后追平变慢、帧源在追平中继续推进/回退时，没有最终时效/身份拒绝点；AC-3 的 `frame_id ≥ L_c` 只排除早于确认时的帧，不能证明发布时间仍新鲜。无新帧时该函数直接返回 0，未定义首次发布等待与停帧终止。仅吞 publisher 调用也不会改变 `:654-674` 无条件置真的 `published_*` 日志位。 | 把最终发布资格与实际桥写入绑定，明确追平完成采用的帧头/新鲜度/身份、超时/回退/无新帧的有界出口；失败时桥零写入的断言必须在实际写入之前成立。说明静音期间旧日志 `published_*` 与实际写入收据如何区分，不把原日志当真发布证据。AC-2/3/4 覆盖确认通过后追平超时、追平中帧头改变、零帧可处理及日志/桥差异；现基线的坏元数据在无 rate lifecycle 时会抛 ValueError（`:437-440`），须由会话映射而非声称天然终止。 |
| AR2-2 | **“只提醒”与自动停发分支冲突，K2 不能由“只减少输入”豁免。** §3.3/CLI 的 `--on-suspect hold` 让 VLM 核验直接触发静音并最终改变控制回退，属于自动动作；§1/§3.6/AC-16 却要求提醒不触发动作、核验从不写控制。该模式下 dismiss 未明确解除静音。缺省 continue 则允许 raw_lost 后 raw_ok 自动重新发布，虽然面向人的状态仍是 SUSPECTED；“状态只有人解除”并不等于“控制只有人恢复”。 | 按已授权的辅助定位，可移除由 VLM 提醒直接触发的 hold 分支，明确 continue 下原跟踪器恢复输出只是底层事实、哪些发布由人重新许可；若保留自动停发或要求 LOST 后自动恢复控制，先向用户说明真实行为、范围与 K2 触发并取得具体裁定。列清 raw_lost、raw_ok、核验提醒、dismiss、confirm_lost 的状态与发布门组合；不能只改状态名掩盖控制语义。本轮不自行追加 K2，也不接受“放进 K1K3 同一候选”替代范围授权。 |
| AR2-3 | **请求世代与单飞生命周期尚未封闭，失败包无法按现 schema 表达。** §3.2 请求无 session/epoch 字段，AC-5 却要求检查确认 epoch；新会话对共享槽内上一会话 ask/release 无隔离规则。QUERYING 新 ask 只增加 epoch，不说明旧 worker 尚活时新任务如何排期；现 `SingleFlightWorker`（`controller/reanchor.py:704-817`）超时后仍 busy、不能提交第二任务，`predict_rows` 的 should_stop 也只在行前检查，不能中断行内 generate。§3.5 的 `<session>-<epoch>-<attempt>` 在连续 verify 时未定义递增，可能重复查询文件身份。另：metadata_invalid 不在 tracker_state.reason 闭集；无帧/加载失败仍强制要求帧、模型生成字段与预览；retry_exhausted 无最后状态字段；AC-6 无新帧失败却要求每条帧 id 递增。 | 定义请求归属/确认令牌和新会话隔离；单槽入口明确单个未回执请求的串行约束或等效不丢请求机制。统一每次 designate/verify 的唯一查询身份、旧结果落点；列出旧任务忙、超时仍活、stop/新 ask/新段/人工处置后的回包规则，并给本地与 HTTP 有界退出及计次。补齐具名失败字段可空规则、reason/last-status，区分“查询尝试计数递增”与“实际取得的新帧递增”。AC-1/5/6/8/17 不得靠实现者自行选择互相矛盾的条款。 |
| AR2-4 | **语义核验的同帧配对与“连续两次”尚无可执行定义。** §3.6 说 latest N' 必有段日志，但帧头可领先跟踪处理；raw_lost 的记录 box_norm 为 null（`track_loop.py:885-895`），unique 时 IoU 无定义。核验只明确返回超 T_max 的处理，没有把帧回退、同 ID 换图、元数据不符映射到 inconclusive。周期/手工/触发可以在同一停帧图上反复核验，形成两次 none；none→drift→none、none→inconclusive→none 时两个计数是否清零/保留未定义，TRACKING 表仅对 consistent 明确清零。 | 选取具名的图像/元数据/本段跟踪框快照，明确跟踪落后、无有效框和 K1 绑定失败的出口；不把未处理帧当作已有日志。定义不同帧/时间要求、两个计数遇到五个 verdict 的更新规则、核验结束后的 next_due 与单飞忙时行为；人工 dismiss/退段之后旧核验结果不得无条件重新触发提醒。AC-16/17 覆盖同帧重复、缺框、交错 verdict 与人工处置后旧回包；不新增身份识别性能义务。 |
| AR2-5 | **真实 Play 必过链路仍依赖未说明的条件，部分失败没有终态。** AC-13 仍以“机身 hold + follow 云台”直接推出目标驶离画面，未写使其离画的具体操作/触发条件；它只给离画后连续 3 次 consistent 的 FAIL，未定义始终未离画、持续 inconclusive、交替 none/drift、仅 E2/E3、额度/时长耗尽而无 E1 的处置。查询至确认共用 T_max 还使 p95 样本留给人确认的时间仅约 2/hz…3/hz（默认约 0.4…0.6 s，尚未扣预览/通信），不能只用推理 p95 论证人工操作可行。AC-14 的闭集还遗漏 stale_rejected/no_new_frame，且 none/后端失败无可确认候选时“确认三者成立”字面不可满足。 | 写出 Unity/config 零改动下的具体 P1 操作与观察窗口，不能保证离画时如实给不可触发结局；枚举上述失败/阻塞/未完成的归属与停止条件。确认预算须说明人的等待如何纳入、仍受保留窗和发布新鲜度约束，不用“模型能在窗内返回”代替。P2 逐结局明确哪些检查适用、无候选时确认 N/A；E1 的真实提醒成功与 E2/E3 的人工/故障路径仍分列。目检与提示须绑定对应帧及原图，不能用返回时的另一画面判过去帧误报/漏报。 |
| AR2-6 | **宿主判定和申请信封尚有机械缺口。** §3.3 A=p95≤6 与 C=p95>(R−10)/hz 在保留窗较短时重叠（如 R=16、hz=5、p95=2，A 与 C 同时成立且 K_max 资格失败）；B/B 同 p95 无决胜规则。§3.5 首轮 INVALID 可重跑，但第二轮 INVALID 未明确归到 FAIL/HOST_UNDECIDED。§5 仍只明列 Mac 合并 1 次，未给 5060 的合并次数；两次诊断 Play 若运行 VLM，其进程/查询是否占每 Play 与总上限不明确，不能由“诊断不计证据”推出推理免费。 | 宿主先通过保留窗资格，再分等待档，或明确只支持的配置闭集；补平局与测量重跑耗尽出口。把两机合并动作、失败计次及正式/诊断推理写成同一份有总上限的申请表，耗尽即停；不要求追加额度或重新跑 609 行。数值只是待用户签发的申请，不由本轮授权。 |

**§7 三项提请答复。** (a) 不冻结常数；发布/确认时间、核验计数与有效配置须先按 AR2-1/3/4/5/6 闭合。
(b) 初始化旧帧发布隔离可作为 K1 的方向继续设计；`--on-suspect hold` 的自动控制效应不能仅以命令类型未变豁免 K2，按 AR2-2 处理。
(c) 操作者目检可作为 Unity 证据，但须绑定被核验的源帧；“连续三次 consistent”只覆盖一种漏报，不能代替 AC-13 的完整终态规则。
以上为本轮审查意见，不签发首次接受释义或新的 AC，不撤销角色 B 的已授权方向。

**上交用户（workflow §4.2 第二次退修上限）。** 本轮设计退修累计 2，C/R=0/0；本轮没有新增关键授权可入账。
请用户选择：(a) 接受/保留当前范围，并逐条保留 AR2-1…6 为已知缺口，明确后续修正处置（不等于实现验收通过，也不自动授权执行）；
或 (b) 关闭本范围为负结果记录（不是 DONE）。接受侧建议 (a)：语言指定与人工主导核验方向成立，当前主要是合同与接入机制未闭合。
用户处置前不自动启动 D3/第三次退修，不进入实现、下载、模型或 Play；工程路由仍未生效，执行信封另行授权。

**用户处置已收到（2026-09-19，Acceptance 代录）。** 用户对上述 A/B 选择回复 "A"，已逐字记入
`docs/authorizations.md` 同日「用户处置第二次设计退修：保留范围并修正 AR2-1…6」。保留当前范围与六组具名缺口，
交构思角色修正正文、接口、AC 与预算后提交 D3，并保留 D1/D2 裁定原文和本轮已核对有效的修正。
此为用户授权的继续修订，不清零设计退修计数，不把 D2 改为 ACCEPTED；D3 由接受角色审查。
AR2-2 的自动控制/K2 取舍未由此另行授权；实现、下载、模型与 Play 额度仍为零。当前下一角色为 Ideation。

**接受侧 D3 裁定（2026-09-19，Owner：Acceptance）：尚不能 `ACCEPTED`，上交用户处置；不签发第三次 `REVISION_REQUESTED`。**

本轮完成 D3 全文、AC-1…17 与 AR2-1…6 的只读设计审查，并核对直接复用的 `TrackLoop`/发布器/推理入口、
新引用的 M3′ 证据与 `CoverageEvaluator` 可见性定义。不是实现核对或独立复核；未运行实现测试、模型、下载、Play 或创建正式 ID。
当前活跃交接 0 消耗性 + 1 零消耗。D1/D2 原裁定和用户 A 授权保留，退修计数仍为 2、C/R=0/0；
以下是对既有缺口修正是否成立的判断，不新增恢复能力、控制策略、数据或性能目标，不给既有实现签发新 verdict。

| 原项 | D3 审查结果 | 保留的修正与残留指针 |
|---|---|---|
| AR2-1 | 部分闭合 | 发布收据区分意图与真实写入、帧差最终门、空转与坏元数据出口有效；发布前快照来源、图像哈希与墙钟停帧仍未闭合，见 AD3-1。 |
| AR2-2 | 行为取舍闭合，措辞须同步 | 删除 `--on-suspect hold`；VLM 提醒不改发布许可，raw_lost/raw_ok 沿用冻结跟踪器输出，人工确认后才退段/重指定。这符合已授权辅助定位，不另行要求用户重选该方向。§3.4/§7 的“没有由人以外的主体关闭控制”“不含任何…会话自动改变控制输入”须收窄为“无 VLM 语义结果触发的自动控制动作”；协议失败仍自动 finalize。不凭该宽泛措辞豁免 K2，但本稿已删除的 hold 分支不再构成 K2 申请。 |
| AR2-3 | 部分闭合 | session/token、唯一 query_id、可空帧字段、重试最后原因、本地卡死后禁止重入与 stop 有界退出有效；HTTP 服务端在途、单槽请求与闭集一致性见 AD3-2。 |
| AR2-4 | 规则层主要闭合 | 已处理帧配对、无框/滞后跳过、不同帧、单计数器与交替累计、人工处置后旧回包丢弃均明确；快照应来自被实际处理的图像，不能返回后重读并冒充原快照，落点并入 AD3-1。 |
| AR2-5 | 部分闭合 | 三段预算给人工留出确认额度；P2 如实报告与确认 N/A 可保留。M3′ 引用不能推出目检离画，P1 终态仍不完备，见 AD3-3。 |
| AR2-6 | 宿主分支闭合，诊断口径未闭合 | 先资格后分档、B/B 平局取 Mac、第二轮 INVALID 记 FAIL、两机合并与诊断推理计数均可保留；诊断正式 ID 隔离见 AD3-4。 |

**本次残留固定为四项（用户处置对象，不是自行开启的第三次退修）。**

| 编号／原缺口 | 可达问题与依据 | 保留范围时的修正落点 |
|---|---|---|
| AD3-1／AR2-1、配对相关 AR2-4 | **最终门仍可能写出旧图观测，且快照取得时机未接通。** §3.3 仅重核帧差与元数据时间，图像只查存在：同 ID 换 JPEG 而 JSON 不变仍通过，违反 AC-3 的同 ID 换图拒绝。若帧头在 P 停住、处理 P 耗时超过 T_stall，写桥时 L_w=P、元数据不变仍通过；会话在 process_available 返回后检查停帧，不能撤回已经刷新发布时间的桥包。实际 `track_loop.py:170-193,644-674` 的 observation 只传 frame_id/track_id/框/分数，look_at 不传帧身份；§3.6 的处理帧环却在 process_available 返回后登记，而 :549-574 在返回及该帧日志之前就发布。 | §3.3/§3.6 明写在调用发布器前可取得的被处理 bundle 身份快照、图像哈希与具名时钟/截止绑定，以及 observation 与其后 look_at 的同帧关联；写入之前拒绝“帧头未动但已过期”和“JPEG 改变但 JSON 未变”。不能以返回后回填快照或更新时间代替写前守卫。同步 AC-2/3：四检查点总述“不初始化”只适用于初始化前的失败；发布门失败属于已初始化段终止；说明批末发布位于函数返回前，避免 AC-3“追平结束前零写入”的歧义。测试落点沿用 GatedSeeding/PublishGate/CatchUp，零写入指被拒帧的观测及其衍生控制。 |
| AD3-2／AR2-3 | **单飞只约束客户端，单槽回执和失败闭集仍有空洞。** §3.4/§3.5 用 HTTP 客户端 T_ret 超时宣称在途有界，但 5060 的 predict_rows/generate 可继续执行；随后启动 pending/重试可能叠加服务端生成，或在串行服务端留下失效排队请求。§3.2 的会话锁只锁 run，不锁独立 CLI 写者；两条请求若在一次 20 ms 轮询之间覆盖，消费者看不到前一 ID，不能承诺记录 LOST_BEFORE_CONSUME 或 AC-1“每条恰消费一次”。此外发布 bundle_missing 要进入同名 REINIT_REQUIRED，但 state.reason/seg_end 闭集没有该值；确认 token/index 不合法既有“状态不变”的默认规则，又落入 §3.4 确认失败退回 IDLE/REINIT_REQUIRED。 | 给出 HTTP 服务端实际模型占用、客户端超时后 pending/重试/stop 的确定规则，不能把断开连接视为 generate 已结束；同一实际模型不能重入，也不能积累不受限的失效任务。明确单槽写者如何互斥或限定唯一写者并拒绝并发、5 s 未确认后是否允许覆盖及回执的读取保证；恰一次须限定为已成功接纳的请求，非法写者另记，不承诺检测未观察到的覆盖。同步 AC-1/5/8/17 与 reason、seg_end、outcome 的枚举，区分 REQUEST_INVALID（不改变状态）与合法确认过期（拒绝候选）；不留“六种 outcome”与 IGNORED_* 通配计数。 |
| AD3-3／AR2-5 | **P1 仍不能唯一裁定部分失败。** 按 §3.6，F_out 起 none→consistent→none 的计数为 1→0→1，没有 E1；却不符合 AC-13 的连续三次 verdict∈{consistent,inconclusive}，因此不能按所写 MISSED_ALERT 判 FAIL。先 ambiguous 进入 SUSPECTED 后核验停止、或已有 E1 提示但人工重指定/确认未成功，也不能仅靠 E1_ACHIEVED 与“E1 前”PROTOCOL_ABORT 完整归类。事实 16 引用的几何可见率采用采样点可见比例阈值（`CoverageEvaluator.cs:1011-1034`），低于阈值不等于预览中整车离画；既有 EVAL-001 纵横比缺陷仍在。因此同锚点与 C_geom≈0.578 只能支持存在不利观察段的假设，不能证明 F_out 必出现或持续到三次核验。 | AC-13 把“提示 E1”与“整条链路 E1_ACHIEVED”分开，定义三次核验窗口里未达到目标提醒的 verdict 组合如何统一裁定、提前 ambiguous/协议中止/重指定失败的优先级及窗口/预算结束的唯一终态，保留真实整链路通过要求。F_out 仍由核验源帧目检确定，不以 C_geom 替代；若现固定场景无法触发，按客观 NOT_TRIGGERED/NOT_MET 回用户，不保证成功也不改场景。引用 M3′ 时补处理臂 B 五次饱和、效应量只为下界及不形成跟踪改善主张的限制（原 compare 证据 §D、状态板冻结措辞）；不重跑 compare、不把真值送入 selector。 |
| AD3-4／AR1-6、AR2-6 | **诊断 Play 的 ID 口径与现行通道冲突。** §5 把正式+诊断语言会话放在 scenario/session/run ID 合计 ≤10 一格，只声明诊断“不耗 scenario ID”；§3.8 又把两者都放到真实 runtime。workflow §4.3.2 明确诊断不创建、不消耗 scenario/session/run ID，产物不进证据链。推理次数共同计账可行，但不能因此把诊断会话变成正式 session/run。 | 明确诊断逻辑标签与正式 ID 的区别、诊断日志/段产物的隔离落点以及正式 ID 计数；使用真实桥进行诊断不等于允许创建 runtime/runs 下正式归档。模型启动/查询与 Play 计数继续共用现申请上限；不得把诊断产物用于 AC-13…15。不申请放宽工作流，也不增加额度；若作者实际需要正式 ID，则应归正式尝试并消耗正式上限。 |

**§7 两项提请答复。** (a) 三段预算及先资格后分档可作为修订基线；本稿未接受，不冻结常数、schema 或执行信封，
也不把 p95 推导写成宿主已经合格。(b) 当前 MISSED_ALERT 判据不足够完备，具体反例及修正落点见 AD3-3。
AR2-2 的方向问题不重开；本轮没有需要用 `REJECTED` 拒绝的新增范围申请，也没有新的关键授权可入账。

**上交用户。** 账本中的 A 已授权保留原范围并提交 D3，该授权已经执行，本次不重问 VLM 定位或自动恢复取舍。
但 D3 仍有上述四项合同缺口，依 workflow §4.2 与角色细则，接受角色不能自行发出第三次退修或替作者改定未闭机制。
建议用户选择 (a)：保留当前范围及已闭合修正，以 AD3-1…4 为具名残留继续修正；或 (b)：关闭本范围为负结果记录（不是 DONE）。
用户处置前维持 `AWAITING_USER_DISPOSITION`，不自动交构思新一轮；engineering-v1 仍未生效，未进入实现或授予 A/B 执行额度。

**接受侧 D4 裁定（2026-09-19，Owner：Acceptance）：`ACCEPTED`；`Workflow: engineering-v1` 在本工作项生效。**

已读最新结构节、全部交接及依赖门，复用本会话已读的两轨流程、角色细则、正式设计与工程继承清单；完整审阅 D4，重核 `FrameRepository.load/image_loader`、发布调用顺序、`RunLogger` 注入接口与授权账本中用户「选A」。活跃 0 消耗性 + 1 零消耗，工作树开工时干净；未运行实现测试、模型、下载、Play 或创建正式 ID。本轮只接受设计，不签实现复核或 DONE。

接受范围是用户已经选定的语言指定/人工确认、NanoTrack-v2 原段输出、低频语义提醒与人工重指定；不新增 VLM 自动控制、自动重播种、硬件或研究指标。新 work ID 的工程申请成立，K1K3 合并停点保持，K2 不因已经删除的 hold 模式追加，K5 另立。下表把本轮发现的局部歧义当场闭合；没有把已知缺陷推迟给实现者解释，也不以设计收口豁免未来复核。设计退修计数 2、C/R=0/0 保持。

| 原项 | D4 接受侧结论与最终合同落点 |
|---|---|
| AD3-1 | 加载时复制实际 JPEG、写前哈希与同帧关联机制成立；`image_loader` 只收到路径，须关联真正交给跟踪器的 FrameBundle 元数据；加载时刻也不能冒充采集时刻。由 AC-3 修订 1 当场固定，非留待实现的缺口。 |
| AD3-2 | 单工提交/轮询、busy 不排队、锁与七值回执、确认失败拆分成立；恰一次的对象、超时放弃结果的责任与断联截止由 AC-1/8/17 修订 1 固定。 |
| AD3-3 | 不再以 C_geom 证明离画，E1 提示与整链路成功分开，事件窗口及兜底分类可接受；源帧/窗口计数、事件前失败及同次 Play 失败优先级由 AC-13 修订 1 固定。 |
| AD3-4 | 诊断逻辑标签与正式 ID 已分离，RunLogger 支持另给根路径；具体目录和计数由 AC-12 修订 1 固定，诊断不产生验收证据。 |

**首次接受释义（合同组成部分，2026-09-19；不是实现期补义务）。** 原 AC-1…17 保留；下列同编号修订在冲突处优先，不把正文中的历史“申请/待裁定”措辞理解为放行。每行只解释本提案已列的路径，不扩大既有范围。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 修订 1 | 七值回执按 §3.2 固定；恰一次指请求接纳/去重，不承诺 PENDING_QUEUED 或 SUPERSEDED 的业务动作必被执行：被替换的 pending 不执行，APPLIED 的动作至多执行一次。回执变化追加到现有会话 JSONL，last_request 只作最新快照。5 s 超时可按 D4 释放写者锁，但 CLI 必报“结果未知，可能稍后执行”，不能自动换新 request_id 重发、不能宣称未执行；同 ID 重试由会话去重。写者锁只能由匹配 pid/request_id 的持有者释放；死写者锁在确认 pid 已死后清理并记日志。未知 action/非法参数的 REQUEST_INVALID 不改变候选、段或 epoch。 | test:tests.test_language_bridge；test:tests.test_language_loop（StateTable、请求超时/迟到/去重/锁持有者/替换 pending） | K1K3 | 2026-09-19 |
| AC-2 修订 1 | 查询/返回/确认用同一个不可变查询快照；确认除 §3.3 的累计帧差与累计截止外，须满足 0≤now−结果首次呈现时刻≤T_conf，重复显示不重置时刻。token/epoch/index 非法只 REQUEST_INVALID；合法请求的身份/时间失败才作废候选。新 ask/respecify 开新 epoch 时 attempt 重置为 1，旧在途/旧 pending 不消耗新 epoch 的重试次数。尚未取得帧的失败按可空规则输出；不把 K_max 当第四个可配置参数，旧简称在返回处指 K_ret、确认处指 K_ret+K_conf。 | test:tests.test_language_loop（StaleRejection、Confirmation、BoundedRetry） | K1K3 | 2026-09-19 |
| AC-3 修订 1 | 字节快照在 image_loader 中建立；元数据必须取该次 FrameRepository.load 返回的 FrameBundle.metadata 完整值，在该 bundle 交给 init/update 前绑定到同一 frame_id/sha（可在会话内包装 repository.load，不改冻结核心）。不能在 image_loader 中另读一份 JSON 冒充原 bundle 元数据；重复 load 不覆盖查询 N 的信任根。最终门比较盘上 JPEG 哈希与元数据完整值，缺失→bundle_missing、非法 schema/id/时钟→metadata_invalid、合法但身份变化→image_identity_changed。除原帧差门外，同时要求本机 monotonic 的 0≤写入时刻−加载时刻≤T_pub，以及 0≤本机 Unix 写入时刻−capture_unix_s≤T_stall；采集时间必须有限，未来时间拒为 metadata_invalid，过龄拒为 publish_expired。加载旧图不能刷新采集年龄，加载耗时计时不能因墙钟回拨变负后仍通过。每次 observation 尝试及 muted/finalize 先清 accepted_frame_id；仅成功 observation 建立关联，衍生 look_at/body_command 写前沿用该帧重核身份与截止，无关联→orphan_control。拒绝一次写入不倒改先前成功收据；例如观测成功后帧源变化导致云台拒绝，观测保留 WRITTEN、云台记拒绝并终止段，不假称整帧历史零写入。 | test:tests.test_language_loop（GatedSeeding、PublishGate、CatchUp：JSON/JPEG 错配、加载前已停帧、处理超时、负年龄、重复加载、观测后控制前变化） | K1K3 | 2026-09-19 |
| AC-8 修订 1 | HTTP 的 POST /query、GET /status、GET /result 均有客户端单次 I/O 截止≤min(5 s,本次剩余等待)，客户端从首次提交起以本机 monotonic 计总等待≤T_hard；断联/无法确认 idle 到期亦 backend_fatal，不能靠无法读取的服务端 stuck 保证有界。T_ret 到期后不接纳该 query_id 的结果、不重入服务端；服务端保留最近结果不等于客户端接受，删去“服务端知道客户端放弃并不返回”的隐含承诺，本合同不增加取消端点。服务端 busy/stuck 状态更新与 POST 接纳互斥，模型真正结束前不得报 idle；stuck 后即使迟到结束也须重启才可接单。query_id、epoch、segment_index、verify_epoch 与截止共同过滤旧回包；只用已绑定帧副本推理，副本在对应在途查询结束/被进程终止前不能被帧环淘汰。 | test:tests.test_language_selector；test:tests.test_language_loop（Worker：提交回执丢失、轮询断联、超时仍 busy、迟到结果、stuck 后返回、帧环淘汰） | K1K3 | 2026-09-19 |
| AC-10 修订 1 | 冻结规则常数：分档 6.0 s；T_conf=10 s、K_pub=2、T_pub=K_pub/hz、T_stall=3 s、T_hard=60 s、T_v=10 s、attempt_limit=3、连续告警 2、核验 IoU≥0.5、合并等价 IoU≥0.9。K_ret=ceil(p95×hz)+2、K_conf=ceil(T_conf×hz)，资格式及平局规则沿用 §3.3；K 收据绑定实际宿主/backend/模型形态及身份、hz/R、所用测量报告，变更任一绑定项不得沿用旧收据。资格仅证明模型时延与保留窗预算相容，不证明追平耗时合格；两宿主均不合格仍 HOST_UNDECIDED 回用户，不能自行放宽 T_pub 或门槛。§8 的真实盲索引连接/重复键数字足以冻结本项 schema 与回放尺度；实机时延值尚未产生，不虚填。 | artifact:docs/evidence/P1-ENG-LOOP-001-latency-mac.json；artifact:docs/evidence/P1-ENG-LOOP-001-latency-5060.json；artifact:docs/evidence/P1-ENG-LOOP-001-report.md §K 收据；test:tests.test_language_loop（配置/身份不匹配） | K1K3 | 2026-09-19 |
| AC-12 修订 1 | 阶段 A 的会话/段日志只用 §3.8 隔离根；诊断强制根为 outputs/eng-loop/P1-ENG-LOOP-001/diagnostics/<diag-label>/，RunLogger 的 runtime 参数传该诊断根（构造器自行追加 runs），不用真实 runtime 根创建段归档。diag-label/段名仅夹具标签，不注册或消耗正式 ID；同次运行中仍用真实桥并遵守会话槽互斥。正式 Play≤8 个 session、每 session≤4 个 run；诊断≤2 次、每次≤4 段且每次≤300 s 仿真时间。§5 模型启动/查询上限包含成功、失败与诊断；本地 HTTP 是所列设备上的推理传输，不是外部模型 API 额度。阶段 A/B 的具体预算仍只是申请，授权账本无额度前不执行。 | test:tests.test_language_loop（诊断路径与正式 ID 零创建）；artifact:docs/evidence/P1-ENG-LOOP-001-report.md §操作单/预算计数 | K1K3 | 2026-09-19 |
| AC-13 修订 1 | F_out 只取实际完成的不同配对帧核验，按其 query_id 绑定目检；同一持续离画段只标一个事件，再次入画后才可开启新事件。窗口起点为 F_out 对应结果首次呈现时刻，计入该结果；截止为第 3 个非 inconclusive 结果呈现与起点+3·T_v+T_ret 的较早者；截止后结果不补记，截止前同帧跳过不作一次完成。⑤ INCONCLUSIVE_WINDOW 仅适用于至少 3 次完成且窗口内完成结果全为 inconclusive，其余无提醒由⑥兜底；none→consistent→none 必为 MISSED_ALERT。E1_ALERT 后须由人 confirm_lost、目标再次在源帧可见时 respecify/confirm、新段至少一条合格 WRITTEN 才成为 E1_ACHIEVED；Play 结束未完成为 E1_CHAIN_INCOMPLETE。PROTOCOL_ABORT 只取错误闭集 {frame_gap,frame_rollback,frame_stall,metadata_invalid,bundle_missing,image_identity_changed,catchup_stale,publish_expired,orphan_control,backend_fatal}，正常 duration_reached/operator_stop、候选过期、操作者拒绝或重试耗尽不冒称协议错误，按未完成路径归类。Play 聚合顺序固定：发生该协议中止（含首个事件前）→PROTOCOL_ABORT；否则存在 MISSED_ALERT→该次 FAIL；否则有合格 E1_ACHIEVED→该次通过；否则初始确认/25 帧跟踪未完成→INITIALIZATION_INCOMPLETE（不通过）；否则无事件→NOT_TRIGGERED；否则取首个事件终态。PROTOCOL_ABORT 的环境 BLOCKED/会话 FAIL 分列，后来的成功不覆盖同次协议失败或漏报，原始事件记录不删。整个工作项仍要求至少 1 次合格 Play；其他尝试失败如实保留，不据此新增成功率指标。 | artifact:docs/unity-test-log.md UT-P1-ENG-LOOP-001-P1；artifact:docs/evidence/P1-ENG-LOOP-001-play-cases.md（窗口边界与逐事件/逐 Play 裁定） | K1K3（Play 证据） | 2026-09-19 |
| AC-17 修订 1 | 本次采纳 §7(c) 的实现期常规澄清通道，不采纳“把已经发现的设计矛盾留待实现再定”的解释：已知局部问题已由以上七行在首次接受时决定。实现遇到新的合同歧义写 Pending rulings，接受侧按同 AC 追加解释；范围/硬件/资源变更仍须用户授权，C 轮不得新增 AC，独立复核与 K1K3 计数规则不变。§3.4 本地 worker 超限后只允许 stop/状态读取；一般 REINIT_REQUIRED 可 ask 的表项不覆盖 backend_fatal 必须重启的特例。 | test:tests.test_language_loop（Worker、StateTable）；artifact:本提案 Pending rulings 与 Contract conformance | K1K3 | 2026-09-19 |

§7(a)/(b) 已由 AC-10/13 修订 1 正式答复，(c) 由 AC-17 修订 1 答复。AD3-1…4 在最终设计合同层闭合，不表示其实现已经通过。实现侧停点自证须同时覆盖原 AC 与上述修订；首次 C1@K1K3 前整理稳定候选、完整 diff 和逐项证据，之后交独立复核；真实 Play 须独立复核通过且用户签发 B 信封后执行。

**执行授权待用户。** 本轮不代签信封；用户此前两次 A 只授权文档修订。当前仅申请 §5 的阶段 A：实现/离线测试、两机各≤2 次合并/≤6 次模型启动，Mac≤70 查询行、5060≤134 查询行，所列下载/传输与隔离新环境；Play/正式 ID/外部模型 API/训练/Jetson/云端为 0。阶段 B 仍为后续单独申请。正式设计 §1 与状态板已同步；本轮无新增关键授权可入账。

### 用户指定网页功能审查（2026-09-22，Acceptance；不开 C/R）

用户本轮指定“审查一下新的测试网页，尤其是其功能是否有改进空间”。本次只读
`docs/evidence/P1-ENG-LOOP-001-operator-web.py` 全文、关联 CLI/桥读取路径、操作单 C §3
及相关载体自测；依据为 §3.4/§3.7、AC-18 与 R-B5…7。没有运行实现测试、浏览器点击、
Play 或模型；可访问的浏览器清单没有现成页面，故下列为源码支持的功能观察及待核实主张，
不是浏览器实测结论、完整候选 C3 或独立 finding/verdict。原核对表、AC、门值与轮次不变。

**判断：按钮化方向有用，下一步优先补齐“看清当前事实再行动”的能力。** 已有合法动作集、
候选/告警身份绑定、双截止与帧差提示、同 request_id 重试和点击日志值得保留。
以下优先级只表达产品改进顺序，不是复核 finding 分级，也不自动成为新验收义务。
下表 `web` 指上述 operator-web.py，函数名为定位锚点。

| 编号/建议顺序 | 可核对的现状与影响 | 建议与后续核实场景 |
|---|---|---|
| UI-1 / 优先核实 | `Monitor.preview_name` 只检查路径身份与文件存在；`PAGE` 的 `img`/`buttonSpecs` 没有图片 load/error/decode 就绪门。即使图片尚未加载或解码失败，候选确认仍可启用。载体 `Fixture.result` 只写 `b"png"`，现有自测不能证明浏览器真的看见图。 | 候选图成功显示且仍绑定同一 query/result 后再启用确认；加载中、损坏、404 明示原因，身份切换清除就绪状态。由后续 C/R 核实 AC-18“预览缺失不提供确认”的覆盖；实现侧补真实可解码图片及浏览器场景，不能把路径存在当人眼已看见。 |
| UI-2 / 优先核实 | `PAGE` 的定时器在 `sending` 时完全跳过 `refresh`；CLI 无回执等 5 s，外层超时可到 30 s。这段时间状态/帧/倒计时不更新，所有操作按钮也禁用。`refresh` 失败只改状态文字，不清绿色样式、不禁用旧按钮；`poll_forever` 出错保留旧快照，`render` 在旧 state 存在时不显示 note。 | 命令在途仍刷新只读信息，发送互斥单独保持；明确显示连接状态、最后成功读取时间、帧/发布是否前进。断连/读错时醒目标记旧数据并禁止以旧视图确认；无证据不声称进程已死。不要把桥头 expires_after_s 擅自改成协议过期门；停止入口受单写者锁的限制须明示，不能让人误认能即时停止。 |
| UI-3 / 优先改善 | `App._click` 不因 `unknown` 限制同一原动作；仅有 1.5 s 重复窗口。页面恢复原按钮后，再点会产生新 request_id，虽提供同 ID 重试，仍靠操作单提醒避免误点（操作单 C §3）。 | 未知请求单列成待处理项，明确“尚未确认是否执行”；抑制将相同动作误当新操作，并突出同 ID 重试。后到回执按原 ID 关联，若覆盖其他人工动作须先明确范围，不自动重发或自动改判执行成功。 |
| UI-4 / 优先核实 | `Monitor._latest_verify` 只按 segment 取最近核验；`tracker_failure` 没有触发 query，页面 secondary 区可立即显示告警前的旧核验。现有自测只断言 alert 区为空和“立即核验”提示，未核实 secondary 的时间关系。 | 对此路径标出“告警前参考”与“本次告警后核验”，显示核验帧/时间及在途状态；新核验未到时明确等待，避免把旧 consistent 当成新判断依据。保留 F5 对真正触发核验的绑定，不把后来图片覆盖触发图。 |
| UI-5 / 下一批体验改进 | 页面只在 `legal.has("ask")` 时展示组合框；SUSPECTED 合法的是 respecify，因此此时只能沿用指令，不能直接组合新指令。CLI `_action_respecify` 已支持显式新指令；缺省优先 confirmed_instruction 再 current_instruction，未必等于按钮所称“上次指令”。 | SUSPECTED 的组合输入可对应显式 respecify，并提示会结束旧段；显示实际将沿用的指令。若现有只读产物不足以可靠还原，回 Pending rulings，不新增隐式协议字段。核实先确认 A、再尝试 B 未确认时的重指定文案。 |
| UI-6 / 下一批体验改进 | 页面有 APPLIED 提醒与 last_published，但指定失败回 IDLE/REINIT_REQUIRED 后不呈现完整结果原因：`poll` 只在 AWAITING_CONFIRMATION 放 candidate，日志读取只留核验内容。控制器已有 retry_exhausted 的 last_status/last_reject_reason、attempt 等结果字段。 | 增加简短进度链“已发送→已受理/排队→候选→人工确认→跟踪→首次写出”和最近结果列表；展示失败原因、尝试次数、可执行的下一步。没有对应证据的阶段显示未知，不把 APPLIED 或历史发布帧当成当前仍在正常发布。 |

范围建议：先处理 UI-1/2/4 的可操作性与信息新鲜度，再改善 UI-3/5/6；暂不增加自动确认、
自动重试或放宽时间门。现有载体自测不覆盖这些浏览器行为，不能凭 75/75 消去上述关注。
本次仅记录改进意见：C3 接手者仍须完整候选核对，决定哪些关注进入 R5；范围外功能由实现角色
提出 Pending rulings 后按现行规则处理。当前已冻结候选不因本次建议自动获准改动，
也不因本次审查解锁 Play/模型服务；下一角色/动作只在状态板交接行维护。

## Pending rulings（待裁定）

**2026-09-20，Owner：Acceptance。** 来源为实现报告 `docs/evidence/P1-ENG-LOOP-001-report.md` §9，问题 1…8 对应 P-A-1…8。以下转录原问题并答复；本轮是实现期合同解释，不是 C 轮、独立复核或第三次设计退修。工程轨道按同 AC 追加修订，保留原 AC 与首次释义；新增修订 8 行、新 AC=0。合同歧义均已裁定，实现符合性仍待实现者落实、自证及后续 C/R。

**原问题（逐字转录报告 §9 的编号条目）。**

1. **AC-12 / 安全互锁**：新增 CLI 开关 `--allow-shared-runtime`。不带它时，
   `--runtime` 指向仓库真实 `runtime/` 一律拒绝启动（退出码 2），以机械保证阶段 A
   「不写 `runtime/runs/`、不占共享槽」。合同没写这个开关，请裁定保留还是删除。
2. **AC-3 / 收据第三类**：收据文件除 `WRITTEN`、`PUBLISH_REJECTED` 外，播种瞬态被
   静音丢弃的尝试记第三类 `MUTED_DROPPED`，并把「发布证据」定义为**只数 `WRITTEN`**。
   这样「`initialize` 即时发布被丢弃」才可机检。请裁定。
3. **AC-4 / `raw_lost` 的判据**：追平一批内若中间帧报丢、批末帧又 ok，按
   「批内任一帧 `ok=False` 即 `raw_lost`」触发 `SUSPECTED(tracker_failure)`
   （与「段内自恢复不算恢复」一致）。请确认这是预期口径。
4. **AC-6 / 未取得帧的尝试也占 `query_id`**：查询检查点在取帧前就失败
   （`bundle_missing`/`metadata_invalid`）时没有查询 job，实现仍分配一个 `query_id`
   并计一次 `attempt`（§3.2(b)「`seq` 对每次 designate/verify **尝试**严格递增」）。请确认。
5. **AC-5 / 预览的退化路径**：预览用 Pillow 渲染；解释器没有 Pillow 时
   `preview_path` 记 `null`，并在会话 JSONL 记 `preview_unavailable`。合同没写这条
   退化路径（阶段 B 的 `.venv-language` 必装 Pillow）。请确认。
6. **AC-8 / 后端异常的闭集归类**：`reject_reason` 闭集里没有「通用后端异常」一项，
   实现把后端抛出的非 `SelectorError` 异常统一记 `worker_died`，`status=backend_error`。请确认。
7. **AC-16 / 核验的 `inconclusive` 如何落进结果包**：后端失败时结果为
   `status=backend_error` + `reject_reason=<闭集>` + `verify.verdict=inconclusive(backend_error)`；
   超时与身份失败为 `status=stale_rejected` + `reject_reason=wall_deadline_exceeded`/
   `<身份失败原因>` + `inconclusive(stale|frame_identity)`。请确认这一映射。
8. **AC-4 / 不可达终端事件的兜底**：本项的段从不装 rate/qualification/re-anchor/
   body planner，所以 `TrackLoop` 的 `REANCHOR_FAIL_CLOSED` 等终端事件结构上不可达；
   万一出现，实现把原事件逐字记进会话 JSONL 并按 `metadata_invalid` 终止段。请确认兜底选择。

**接受侧答复（合同追加修订，2026-09-20）。** 证据指针是实现交付要求，不表示本轮已验证实现或已运行测试。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-12 修订 2 | P-A-1：保留 `--allow-shared-runtime`，解释 AC-12 修订 1 与 §3.8 的隔离边界。缺省对实际解析到仓库真实 runtime 根的路径（含相对路径/符号链接别名）拒绝启动、退出码 2，且拒绝前不得创建桥、锁或段日志。该开关只是阶段 B 操作入口，不是授权凭据；阶段 A 操作单不得使用它，诊断亦须 B 信封。显式开关不绕过会话锁、K 收据或诊断目录规则。 | test:tests.test_language_loop（DiagnosticSessionTests：默认拒绝、路径别名、拒绝零写入）；artifact:docs/evidence/P1-ENG-LOOP-001-report.md §操作单 | K1K3 | 2026-09-20 |
| AC-3 修订 2 | P-A-2：保留 `MUTED_DROPPED` 作为发布尝试收据第三类；收据结果闭集为 {WRITTEN,PUBLISH_REJECTED,MUTED_DROPPED}。只有成功写出的 WRITTEN 是实际发布证据，PUBLISH_REJECTED/MUTED_DROPPED 仅是拒绝/静音诊断，不能推进 last_published_frame_id、不能建立 accepted_frame_id；初始化静音不得被误算为 orphan_control 并终止段。沿用修订 1 的逐调用收据与已写记录不可倒改规则。AC-2 初始化前失败仍要求收据为空；AC-4 finalize 后仍零新增，不以第三类为由继续追加。 | test:tests.test_language_loop（GatedSeedingTests、PublishGateTests、StateMirrorTests）；artifact:会话 publish-receipts.jsonl | K1K3 | 2026-09-20 |
| AC-4 修订 1 | P-A-3：确认逐帧处理原始事实，解释 AC-4/§3.4：一批已处理记录中出现 ok=False（原始 LOST）即发 raw_lost，TRACKING 转 SUSPECTED(tracker_failure)；后续同批 raw_ok 不解除疑似、不改变 suspect_id。tracker_raw_state 镜像最后已处理帧的原始状态，因此批末可为 TRACKING 而会话仍 SUSPECTED；逐帧事实不被批末状态覆盖。raw_lost/raw_ok 都不改发布门，批末 raw_ok 的观测仍须通过既有最终门，提醒不是自动停发。 | test:tests.test_language_loop（StateMirrorTests：批内 LOST→TRACKING、状态与收据分别断言） | K1K3 | 2026-09-20 |
| AC-6 修订 1 | P-A-4：确认查询检查点 bundle_missing/metadata_invalid 的失败尝试也分配唯一 query_id；designate 的 attempt 递增并按原五类失败的 stale_rejected 路径进入有界重试，耗尽仍写 retry_exhausted 与最后原因。无法建立合法完整快照时四个帧绑定字段为 null，不虚构 frame_id/sha/采集时间；query_unix_s 仍记尝试时刻。已有合法快照后返回/确认失败保留原绑定。严格帧递增只约束取得帧的尝试，verify 的 same_frame/no_tracker_box/tracking_lag 发起前跳过不冒充已调用模型。尝试数、query_id 序号与实际模型调用数分列，前置拒绝不得冒充模型执行，真实调用成功/失败仍计原信封。 | test:tests.test_language_loop（BoundedRetryTests、StaleRejectionTests、VerifyTests）；artifact:会话 results.jsonl 与预算计数 | K1K3 | 2026-09-20 |
| AC-5 修订 1 | P-A-5：不接受「缺 Pillow、preview_path=null 仍可确认播种」作为合格退化。AC-5 原文的预览存在要求保持：有 unique/ambiguous 候选时，须先生成绑定源帧且 index 一一对应的预览，再允许 confirm；缺依赖/渲染失败可保留 null 与 preview_unavailable 会话诊断，但 confirm 必须 REQUEST_INVALID、候选/epoch/段不变且不 initialize、不写观测或控制。修好环境后仍须满足原 T_conf/身份门，不能靠补画/重显示重置首次呈现时间；必要时重新 ask。核验有配对帧时沿用 §3.2/§3.6 的预览要求，缺预览不能用返回时画面补判 AC-13 事件。无候选且无配对的原合法 null 不受影响。阶段 A 稳定候选须在有 Pillow 的环境提交具名预览生成/确认测试证据，缺依赖的 skip 不是 AC-5 满足；不新增看图轮次或资源额度。 | test:tests.test_language_loop（ConfirmationTests、PreviewRenderTests：成功预览与缺依赖拒绝确认）；artifact:docs/evidence/P1-ENG-LOOP-001-report.md §2/§3/§操作单 | K1K3 | 2026-09-20 |
| AC-8 修订 2 | P-A-6：限于 InferenceAdapter.predict_one 执行边界抛出的、未被 SelectorError 细分的普通 Exception，可映射 status=backend_error、reject_reason=worker_died；此值表示本查询执行失败，不宣称操作系统进程确已死亡。会话诊断保留异常类型与消息，不把解析失败、帧检查失败、用户 stop 或会话程序其他异常统统吞入该映射。已知 SelectorError 沿用原具体原因；T_hard/stuck/无法确认服务 idle 到期仍按修订 1 与 AC-17 修订 1 进入 backend_fatal 并只许 stop，不能用普通重试绕过。 | test:tests.test_language_selector；test:tests.test_language_loop（WorkerTests：普通后端异常、已知原因保留、硬截止） | K1K3 | 2026-09-20 |
| AC-16 修订 1 | P-A-7：确认双层表示，但 verify.verdict 字面只能是 inconclusive，原因另置 verify.inconclusive_reason，不能把 inconclusive(reason) 写成第六种 verdict。已失效的 epoch/segment_index/verify_epoch 先按原规则只记 IGNORED_STALE_EPOCH。当前查询的返回检查超过 T_ret → stale_rejected/wall_deadline_exceeded + inconclusive_reason=stale；返回身份失败原因闭集 {negative_frame_delta,bundle_missing,image_identity_changed,metadata_invalid} → stale_rejected/原原因 + frame_identity；frames_late_exceeded → stale_rejected/同名 + stale。适配器自身失败（包括其报告的 timeout）沿用 backend_error/原闭集原因 + backend_error；parse_failed 保留该 status、reject_reason=null、原因 parse_failed。inconclusive 不增减连续告警、不解除疑似、不播种或写控制；backend_fatal 的独立终止规则不被 inconclusive 屏蔽。 | test:tests.test_language_loop（VerifyTests、WorkerTests）；test:tests.test_language_bridge（verdict/原因分字段） | K1K3 | 2026-09-20 |
| AC-4 修订 2 | P-A-8：有条件保留 metadata_invalid 作为本项未启用子系统的异常段终止之协议兼容兜底；只适用于 TrackLoop 已报告终止、但事件不在本合同已定义 seg_end 映射内的情况（包括所问 REANCHOR_FAIL_CLOSED）。原事件及原原因逐字进入会话 JSONL，并明确标为 unexpected_segment_end；该诊断不是 tracker_state.reason 的新增枚举，也不声称已证明传感器元数据损坏。会话 finalize 恰一次、REINIT_REQUIRED、publishing=false，不继续原段。已定义的 frame_gap/frame_rollback/frame_stall/身份/发布拒绝/backend_fatal/duration_reached/operator_stop 不得被兜底覆盖。若在真实 Play 出现，按 AC-13 修订 1 的 metadata_invalid 协议中止归会话 FAIL，不能以「结构上不可达」忽略或改记环境 BLOCKED；报告保留真实终端事件。无需启用 rate/qualification/re-anchor/body planner 来演练此路径。 | test:tests.test_language_loop（StateMirrorTests：意外终止、已知原因保留、单次 finalize）；artifact:会话 language-session.jsonl | K1K3 | 2026-09-20 |

**交接。** Implementation 先按八行修订落实代码/测试/报告；特别是 P-A-5 不得用原缺依赖 skip 声称通过。两机等价/时延、K 收据与 pip check 仍缺，实测执行分工按账本 2026-09-19「离线件先行，实测另批」待用户安排；原阶段 A 信封不扩额、B 未授权。之后按 AC-11 整理停点测试与 §4.3.1 自证，才交 C1@K1K3。本轮未运行实现测试、未审完整候选 diff，不对报告中「满足」或「不可达」作实现通过背书。


**P-B-1（2026-09-20；来源：实现报告 §9.1）。** 原问题逐字转录：

**P-B-1 / AC-16**：`INCONCLUSIVE_REASONS` 闭集里的 `same_frame`、`no_tracker_box`、
`tracking_lag` 三个成员**当前不可达**。§3.6 的措辞是「同帧不重复核验，跳过记
`inconclusive(same_frame)`」，读起来像要产出一条结果包；而 AC-6 修订 1 要求这三种
**发起前**跳过「不冒充已调用模型」。实现取了后者：三者只写会话 JSONL 的
`verify_skipped`，不产结果行、不占 `query_id`、不调模型（`VerifyTests` 三条用例钉住）。
两种读法都自洽，但闭集里留着三个永不出现的值会让下游消费者误以为能收到它们。

请裁定二选一：**(a)** 明确这三种跳过只入会话 JSONL、不产生结果包，并相应从
`INCONCLUSIVE_REASONS` 移除这三个成员；或 **(b)** 让它们各发一条不带 `model` 块、
不占 `query_id` 的 `inconclusive` 结果行。在答复前实现保持现状 (a) 的行为、闭集不动。

**裁定：采纳 (a)。** 原因：发起前跳过未形成模型查询，沿用 AC-6 修订 1 的三列计数与 AC-13 修订 1 的完成核验定义；无需创造缺 query_id/model 的第二种结果行。此处是实现提问所需的 AC-16 释义；原条文保留，冲突处以本修订为准。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-16 修订 2 | P-B-1：解释 §3.6、AC-16 与 AC-6 修订 1，发起前跳过闭集 {same_frame,no_tracker_box,tracking_lag} 只在会话 JSONL 记 verify_skipped 及原原因，不产生 results.jsonl/language_result.json 结果、不占 query_id、不调模型、不计完成核验、不改变连续告警/疑似状态。结果包 INCONCLUSIVE_REASONS 移除这三个成员，剩余闭集为 {stale,frame_identity,parse_failed,backend_error}，映射沿用修订 1；本修订不改变其他前置失败和已发起查询的原记录规则。 | test:tests.test_language_loop（VerifyTests：三种跳过的日志、结果与计数）；test:tests.test_language_bridge（结果原因闭集）；artifact:docs/evidence/P1-ENG-LOOP-001-report.md §9.1 | K1K3 | 2026-09-20 |

**最新交接。** P-A-1…8 已有实现增量及日志，尚不代表逐项验收通过。Implementation 落实 P-B-1，并核实修正用户指定增量查看中的 U-A-1…3 与对应测试/报告；两机实测分工仍待用户安排，原信封不扩额。补齐 AC-9/10/12、AC-11 与 §4.3.1 自证后才交 C1@K1K3。此处不新增 C 退回次数，不授予阶段 B。


**P-B-2（2026-09-20；来源：实现报告 §9.2）。** 原问题逐字转录：

**P-B-2 / AC-16 修订 2**：AC-16 修订 2 把 `verify_skipped` 的原因闭集定死为
`{same_frame, no_tracker_box, tracking_lag}` 三个成员。但 §3.6 的发起前条件其实有
**四条**——第一条是「P 仍在盘且身份一致」，它在合同里从没被取名。实现里它对应三种
情形：帧环里没有该帧的快照、盘上字节/元数据与快照不符、`latest.json` 读不出来。

把它们硬塞进那三个名字会**错标**（我一度误改成 `no_tracker_box`，已回退）；留在
`verify_skipped` 里又会突破刚被定死的闭集。当前实现取第三条路：另记一种诊断
`verify_pairing_unavailable`（`reason` 取 `snapshot_missing` / `image_identity_changed` /
`bundle_missing` / `metadata_invalid` / `latest_unreadable`），语义与三种跳过一致——
只进会话 JSONL、不产结果、不占 `query_id`、不调模型、不改计数。

还有**同一问的另一半**（复核指出，一并提请）：designate 的查询检查点遇到
`bundle_missing`/`metadata_invalid` 时，按 AC-6 修订 1 要**分配唯一 `query_id` 并落一条
结果行**；而核验这条同名失败当前既不占号也不产结果行，两边不对称。

请裁定：**(a)** 认可这条独立诊断（并给它一个合同名），且确认核验侧**不**占号、
**不**产结果行；或 **(b)** 把它并入 `verify_skipped` 并扩充那三成员的闭集；或
**(c)** 按 designate 的查询检查点**对称处理**（走结果行：`status=stale_rejected`、
`reject_reason` 取原闭集值、`verify.inconclusive_reason=frame_identity`、四个帧绑定
字段可空）。答复前实现保持现状 (a)。

**裁定：采纳 (a)。** §3.6 的配对可用性检查在建立核验查询前进行；designate 的有界尝试已进入 AC-6 查询检查点，两者的记号规则有意不同。AC-16 修订 2 的三值闭集不应迫使实现错标其他前置失败。以下仅解释这条待裁定所列情形，不把已发起查询的身份失败改成无结果跳过，也不改变段自身的协议失败处理。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-16 修订 3 | P-B-2：解释 §3.6、AC-6 修订 1 与 AC-16 修订 1/2。核验建立查询前，配对帧 P 的快照缺失、原帧身份不可确认或 latest 指针不可读取，统一以会话 JSONL kind=verify_pairing_unavailable 记录；reason 闭集为 {snapshot_missing,image_identity_changed,bundle_missing,metadata_invalid,latest_unreadable}，分别保留快照缺失、身份校验原返回值、latest 读取失败的真实原因，并带已知 P.frame_id。此路径不占 query_id、不产 results.jsonl 或 language_result.json、不调用模型、不计完成核验，不改连续告警/疑似/已核验帧与结果状态；不扩充 verify_skipped 的三值闭集或结果原因四值闭集。designate 的 AC-6 前置失败仍占号并产结果；已经发起的 verify 返回身份失败仍按 AC-16 修订 1 产 inconclusive(frame_identity) 结果。不得借本诊断吞掉跟踪段自身的既有协议终止。 | test:tests.test_language_loop（VerifyTests：配对不可用的具名原因及状态/计数不变；designate 前置失败与 verify 返回失败保留原路径）；artifact:docs/evidence/P1-ENG-LOOP-001-report.md §9.2/§11 | K1K3 | 2026-09-20 |

**最新交接。** U-A-1 恢复 /status 的具名残留已见修复，P-B-2 报告/具名测试及 AC-8 loop 侧补证已到位，本次静态查看结论见上表；不代表全部合同已验收。AC-9/10/12 实测与停点自证仍缺；实测分工由用户安排，Implementation 按原阶段 A 信封及 AC-11/§4.3.1 继续，阶段 B 未授权。正式 C/R 尚未开始。


**R-B1…4（2026-09-22，Owner：Acceptance；来源：stage-b-prep §6.2）。** 以下逐字转录实现问题；本批为实现期合同裁定，不是新 D/C/R 轮。用户两项选择已逐字入账（authorizations 同日「单字段后台运行设置与追加两次诊断」）。

- **R-B1 Unity 失焦停帧的处置**：`ProjectSettings/ProjectSettings.asset` `runInBackground: 0 → 1`（单字段）。该路径属
  PLAY_GOVERNING（workflow §4.4），合同 §2.2 写「不改 Unity（`Assets/`、`config/` 零字节）」而未点名 `ProjectSettings/`，
  AC-4 的零改动机检只列 `Assets/ config/ tools/eng_sft/`。请裁定：(a) 是否允许、由谁改（实现角色提交该一行）；
  (b) 是否构成 `K1K3` 候选变化并按 §4.4 开 R 轮（`git diff <通过候选>..<新候选>` 于 PLAY_GOVERNING 非空）；
  (c) 采集候选对应性（Python 客户端仍从原通过候选运行、Unity 工程多一行设置）与 Unity 日志的写法。
- **R-B2 登记外 Play**：§4.1 末条（Unity 重启后进入、帧 0–19 并在 15:54–15:55 续跑至 `sim_t` 87.4 s；零会话/零查询/零 ID）
  是否计入「诊断 Play ≤2」或另计。
- **R-B3 诊断 1/2 的归因**：诊断 1 = 环境中断（5060 休眠 + Unity 失焦停帧，零查询）；诊断 2 = 未确认/未播种（操作者把
  request_id 填进 `confirm` + 超窗；Unity 失焦停帧），查询 1 行。实现角色建议均归「环境/流程」，非候选缺陷；由接受角色机械归因。
- **R-B4 首批追平门仍未测**：授权要求「先用诊断确认首批追平再进正式」，该前提未满足；在追加诊断入账且 R-B1 落地前，实现角色
  不开任何 Play。

**裁定：`ACCEPTED`（仅以下范围例外与两行合同追加修订）。** 不因 §2.2/AC-4 未枚举 ProjectSettings 就把它排除于“Unity 零改动”；本次以用户选择作为单字段例外的授权来源。原 AC 与修订均保留，冲突处以本次追加为准。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-4 修订 3 | R-B1：§2.2/§3.1/AC-4/AC-13 中 Unity 零改动的唯一例外为 ProjectSettings/ProjectSettings.asset 的 runInBackground: 0 → 1，由实现角色提交；同文件其他字段、ProjectSettings 其他文件、Assets/、config/、tools/eng_sft/、Packages/packages-lock.json 保持相对 R2 通过候选零改动。R2 基线只从 docs/reviews/P1-ENG-LOOP-001.md 的 R2 passed_candidate 运行时解析。本例外用于操作者切换终端/预览时持续供帧；实际效果须后续诊断核实，不以字段已改推定生效。K、T_pub/T_stall、帧/控制协议、跟踪核心与模型决策保持。 | cmd:git diff（从复核机读行解析 R2 基线，核对具名路径及单字段差异）；artifact:docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md（配置核对与后续诊断）；artifact:docs/unity-test-log.md（正式采集身份） | K1K3 | 2026-09-22 |
| AC-12 修订 3 | R-B1/2/4：用户新增诊断为后续 2 次（0/2），旧信封诊断实际 3/2、超用 1 单列，不追认、不冲销失败；每次≤300 s、≤4 段、零正式 ID、≤40 查询，原模型启动≤10/总查询≤400 与正式额度不增。先修设置及操作单、提交稳定候选，经 C2@K1K3→R3@K1K3 后再诊断；本批不是 R2 的 REWORK_REQUIRED 修复，不适用跳过 C 的返工例外。新候选未通过前，正式和诊断 Play 均不启动。正式采集使用最新通过候选：Python checkout HEAD 对齐；Unity 主树的 Assets/config/ProjectSettings/Packages 与该候选逐字一致且无未提交或未跟踪差异（含 _Recovery）；实际两处 HEAD/status 与路径 diff 由当轮发令角色在 Unity 已打开、按 Play 之前记录，正式证据写 Unity 日志。5060 的实际导入源码与操作脚本/清单须按新候选核对；Python 未改可验证字节相同后复用服务源码，不把混用版本笼统声称为一个 checkout。 | artifact:docs/evidence/P1-ENG-LOOP-001-operations-c.md；artifact:docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md；artifact:docs/unity-test-log.md；cmd:git rev-parse HEAD / git status --porcelain / git diff（各实际 checkout，基线运行时解析） | K1K3 | 2026-09-22 |

- **R-B1 开轮与对应性**：ProjectSettings 属 workflow §4.4 的 PLAY_GOVERNING，本字段变更必须回同一 K1K3；C/R 目前仍 1/2，候选自证后才开 C2/R3，不重置计数、不自动认定通过。按完整 diff 核对，COORD-013/014 工具/测试差异如实列为独立协调批次，不冒称白名单文档。操作单 C 及其直接执行载体 `docs/evidence/P1-ENG-LOOP-001-operator.sh`、`docs/evidence/P1-ENG-LOOP-001-operator-watch.py`、`docs/evidence/P1-ENG-LOOP-001-5060-runner-b.py` 作为本次阶段 B 冻结操作单范围一并交核对/复核；目录名 docs 不使操作者/预算行为免检。只读核对不新增实现逻辑；本次未签 C/R verdict。
- **R-B2 计数**：登记外 Play 按一次诊断消耗计入旧信封；15:45 与 15:54–15:55 的帧段暂按 prep 保存的一次进入/续跑计，不把未证实的第二次进入虚增为一次。若保留日志证实另有独立 Play，则据实补账并报告。无语言会话、零查询/ID 不豁免 Play 计数。旧信封因此实际 3/2，诊断 2 启动时已越出原上限；新增 2 次是随后独立授权，历史偏差仍存在。登记外帧、恢复目录与隔离物不删、不转正式证据。
- **R-B3 执行归因**：诊断 1 是环境中断（5060 失联/恢复与 Unity 手动重启），零查询；诊断 2 是操作流程未完成（预览未见、把 request_id 当 index 被 CLI 拒绝、已超确认窗），查询 1、未确认/未播种。失焦停帧与设置的关系是现有观察支持的待验证环境原因；不把相关性写成已证明修改有效。二者都无首批追平数据，不据此判定追平实现失败或实现无缺陷。恢复目录漏检与登记外 Play 属发令/计数流程偏差。此处是执行归因，不是独立 finding，不能虚填六值依据列；R1/R2 原机械归因和 F3 OPEN 不变。
- **R-B4 停止与后续**：新增诊断入账不等于立即可 Play。保留 §7 原复核前禁止 Play 顺序；实现做单字段配置核对及相称离线检查，报告明确“失焦恢复效果与首批追平未验证”，自证不得把这项风险写成已通过。候选资格由正常 C/R 路径处理。R3 通过后，新增诊断核实持续供帧、预览可见/编号、首批 load_elapsed_s/frame_delta/发布收据/确认延迟，并完成至少两张样帧人眼检查；诊断产物不进入 AC-13…15 或替代门证据。任一发布门失败或无可核对收据即停正式，按原返工渠道处理，不放宽 0.4 s、不暂停供帧造通过、不反复试到成功。正式 P1/P2 仍须全部既有前提满足。

本批新 AC=0、追加修订2（AC-4 修订3、AC-12 修订3），实现期累计12行；C/R、设计退修和独立 finding 计数不增。正式设计同步 v0.3.47。当前交接只在状态板记录。


**R-B5…7（2026-09-22，Owner：Acceptance；来源：stage-b-prep §8.6）。** 本批为实现期合同裁定、执行归因与授权代录，不开 D/C/R，不改当前核对表或独立复核文件。用户原话已逐字转录到 authorizations 同日「本地按钮操作页与追加三次诊断」。原 AC 及修订保留，以下追加项在冲突处优先。

- **R-B5：接受本地按钮页范围例外。** §2.2(4) 原本明确“不做 GUI”，故不能称旧范围天然包含按钮页；用户已选择全部操作者动作及本地网页，现仅对此作例外。它是既有 CLI 的本机操作外壳，不增加感知、控制、模型决策或自动确认。新载体路径固定为 `docs/evidence/P1-ENG-LOOP-001-operator-web.py`（页面资源内嵌，无新依赖）；与 operator.sh、operator-watch.py 集成，CLI 保留作后备。新 AC-18 来源仅为实现提问 R-B5 与用户选择。
- **R-B6：接受后续三次独立追加。** 旧信封实际3/2（超用1）、上次追加2/2耗尽均保留；本次新增0/3。服务端记录的是有查询的会话，不能用它替代 Play 计数，零查询/中止亦扣 Play。迁移不得重置累计启动、查询或历史事件；旧已计费诊断会话从现账本运行时枚举并冻结，零查询旧 Play 仍由操作登记保留，禁止用旧标签续跑。操作单分配三个未使用诊断标签，不在本批创建目录或身份。
- **R-B7：接受操作单同步修正。** 原“让它过期（会记 candidate_expired）”不符确认检查点触发语义，须改；推算时间窗只供人择时，不能成为模型/控制器输入或自动触发依据。诊断3/4的事实与主张边界见下方执行归因。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-18 | R-B5：本地按钮页仅监听127.0.0.1，用Python标准库和内嵌页面，无下载；显示本会话状态、绑定query_id/源帧的候选及核验预览、确认剩余时间。动作闭集为ask（预设the red car及§3.7文法输入）、逐候选confirm k、reject、verify、confirm-lost、dismiss、respecify、release、stop，按§3.4及AC-17修订1只呈现合法动作；backend_fatal只许stop/状态读取。每次点击只调用采集候选的controller.language_loop CLI，不手写桥文件、不自动确认/判丢/重指定、不自动启动Play或模型；命令参数与页面已呈现的session/result/suspect/track身份及候选index绑定，旧页面不得换绑新令牌。预览缺失/身份不符不提供确认；跨文件读序沿用F5的触发query_id绑定，后到核验不可替代告警帧。倒计时沿用AC-2修订1：查询起算T_ret+T_conf与结果首次呈现起算T_conf取更早截止，同时显示累计帧差门；从可信原始时刻读出，不以网页首次看到、刷新或补画重置，无法取得则明示不可确认，不伪造剩余秒数。客户端提示不代替会话最终检查；仅页面计时结束不产生候选过期事件或自动动作。点击期间防重复提交，未知/超时结果遵循AC-1修订1，不自动换request_id重发；记录点击动作/绑定身份与CLI stdout/stderr/回执到opdir，APPLIED不冒称播种或发布成功。页面模式watch不再弹独立预览，CLI后备仍保留；按钮行为用无模型、临时目录载体自测覆盖合法/非法状态、陈旧页面/令牌、预览缺失、重复点击/未知回执、两个截止与刷新不续期、F4发布显示与F5预览绑定，fixture调用生产写盘函数。真实浏览器呈现/点击与人眼检查留待获准诊断，不以载体自测替代。 | cmd:python3 docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.py（实现补相称用例，输出写文件）；artifact:docs/evidence/P1-ENG-LOOP-001-operations-c.md；artifact:docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md | K1K3 | 2026-09-22 |
| AC-12 修订 4 | R-B6：在修订3基础上另追加后续诊断3次（本次0/3）；旧3/2超用1及上次2/2不得冲销。每次≤300s、≤4段、零正式ID、≤40查询；正式≤8、启动≤10、总查询≤400等原边界不增。runner按本修订一次性迁移现B账本，保留AC-12-rev3原记录、累计计数与事件；新修订重复执行不再次加额，旧诊断标签拒绝查询，新诊断会话第4个拒绝，原总额/每次上限照旧，迁移失败不得清账重建。Play登记包含零查询/中止，与服务端查询账本分列对账。重建候选传输清单，按既有代码传输授权同步runner及清单；先核对身份与amend/preflight，后启动模型，计入原启动总额。本批仅零消耗实现，冻结操作单与载体自证、提交推送后走C3@K1K3→R5@K1K3；通过前禁止正式/诊断Play及5060模型服务启动，之后才用新增诊断检查首批追平与至少两张样帧人眼保真。采集checkout、主树Unity路径、实际导入源码与操作载体逐项对应最新通过候选，继承修订3现场检查。 | cmd:python3 docs/evidence/P1-ENG-LOOP-001-c2-carrier-selftest.py（账本迁移/幂等/旧会话冻结/第4个拒绝/总额边界）；artifact:docs/evidence/P1-ENG-LOOP-001-operations-c.md；artifact:docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md；artifact:docs/authorizations.md（本日按钮页与追加三次诊断） | K1K3 | 2026-09-22 |
| AC-12 修订 5 | R-B7：操作单C的额度、标签、按钮/CLI路径、预览布局与停止条件跟随AC-18/修订4。保留先检查后台持续供帧再ask的顺序；该步骤占去首窗后等待后续可见窗，不抢第一窗、不暂停Unity造通过。播种前相机固定时的约sim_t 0–12、99–118、206–225s只能标为路线/速度与相机元数据推算；第2窗有诊断4查询帧目视支持，第3窗未实帧验证，实际操作以用户看到目标入画为准，播种后不沿用该预测。删除“等待即自动candidate_expired”的操作指示：只有合法confirm触发时效检查，失败按既有状态表落IDLE或REINIT_REQUIRED并记stale_rejected/原因；不确认可保持AWAITING_CONFIRMATION，人可reject或重新指定。写清结果首次呈现后≤10s、查询起算≤16s及帧差≤80（当前K收据），各门同时满足；不得称候选出现后还有16s。对用户说明阶段B验证人工闭环与失败停下，首批追平尚未测到，诊断不替代AC-13…15、不评估跟踪性能或恢复率。 | artifact:docs/evidence/P1-ENG-LOOP-001-operations-c.md §0/§3/§4；artifact:docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md §8.3/§8.5（事实及推算边界）；cmd:git diff（冻结操作单与载体一致性） | K1K3 | 2026-09-22 |

**实现范围与候选路径。** 本批代码范围为 `docs/evidence/P1-ENG-LOOP-001-` 前缀下的 operator-web.py（新）、operator.sh、operator-watch.py、5060-runner-b.py、build-stage-b-manifest.py、c2-carrier-selftest.py，及操作单C、实现报告/测试输出/停点证据；controller、Unity、config、模型/K收据与协议不改。操作单C及上述五个执行载体（除自测）均点名纳入本项冻结操作单集合，按workflow §4.4属于PLAY_GOVERNING；测试/证据变更同列完整候选diff，不按docs目录免检。若仅用现有只读数据无法满足倒计时/身份绑定，先回Pending rulings说明缺字段，不自行扩大核心改动。

这是R4通过后用户另行要求的操作工具增量，不是复核REWORK_REQUIRED修复；因此须先C3，再由新鲜上下文复核角色按非空PLAY_GOVERNING diff开R5。上一通过候选与上一复核候选均从复核机读行解析。当前C/R仍2/4、C退回0、R返工2，原冻结集处置及终局限制保持，不授予新返工配额；若新轮不能通过，交用户裁定，不自行循环。R4本次上下文例外不延伸R5；R4只证明其原候选，不能预覆盖按钮版。

**执行归因（诊断3/4）。** 依据prep §8.3/§8.5：两次均持续供帧，未到播种，首批追平无收据；诊断3提问时目标已离画、候选未确认，诊断4候选框经实现目检落在红车、确认距呈现20.2s且累计24.0s，最终按frames_late_exceeded拒绝，IDLE下verify按合同拒绝。主要限制为目标可见时机与人工操作链耗时，过期后没有自动事件的操作单表述亦需修正。不能从这两次判定追平代码失败或没有缺陷，不把实现目检补成用户已完成人眼检查，也不将“16s”转述覆盖独立10s门。该执行归因不签独立finding、不填六值依据；F3未报告触发、仍OPEN，F1…F6原机械归因不变。

本批新增AC-18一行、追加AC-12修订4/5两行；工程原验收项现18、首次释义8、实现期修订累计14。零Play/模型/查询/正式ID/传输；正式AC-13…15仍NOT_RUN。R-B1…4及Acceptance rulings中旧计数和“尚未实测”均保留为当时结论；当前事实/计数以implementation-status同名节的本批更新为准，当前交接只在状态板维护。

**R-B8…11（2026-09-23，Owner：Acceptance；来源：stage-b-prep §11/§12）。** 用户要求机身跟随并选择纳入本项，原话见授权账本同日条目。此为实现期范围与验收变更，不开 D/C/R 轮；原 AC 与修订不覆盖删除，以下追加条款在冲突处优先。沿用冻结 `ThresholdBodyPlanner`、`config/p1-m3-body-001.json` 和既有 `body-planner-contract/v1`；不把 BODY-001 的 `THRESHOLD_ALLOCATION_PARTIAL` 改写为跟踪改善结论，不增加自动恢复或真值输入。

- **R-B8／停点。** §2.2(1) 的 Unity/config 零改动边界继续适用（既有 ProjectSettings 单字段例外除外）；允许在本项 Python 会话接入既有规划器。§2.2(2) 的“无自动重播种”、§3.3 的观测写前最终门和同帧控制关联继续适用；初始化 `hold_body`/`set_nadir` 与故障安全 hold 可走不依赖观测的安全通道，不能借此发送速度。§7 原“不申请 K2”只适用于 R6 及之前的候选。新段可发机身速度命令，故新候选必须走 `K1K2K3` 合并停点，逐项覆盖 K1 的帧/发布关联、K2 的控制与安全、K3 的人工决策边界；先 C5 再交新鲜上下文 R7，二者均不预签通过。此前 K1K3 通过候选只覆盖旧范围，原 C/R 与返工计数不重置。新范围如不能满足自证或复核门，正式 Play 仍停并回用户，不借 R5/F7 的一次性授权增加返工次数。
- **R-B9／正式 P1。** AC-13 原文及修订1的离画事件分类继续用于实际发生的事件和失败报告；新修订2替换“必须取得 E1_ACHIEVED 才通过”的总通过条件。新目标是一圈**单次演示**：同一已人工确认的红车段持续覆盖 106.5 s 仿真时间，运行态无 LOST/REINIT_REQUIRED/TERMINAL，九个预定等距检查点的源帧人工核对红车可见且跟踪框落在该车上，并有可核对的机身位移与受门控的速度命令；检查点/缺帧和失败均预先定义、完整保留。该演示不能推广成连续逐帧正确率、跨场景跟踪性能或 BODY-001 效应量；AC-15 的报告禁令仍在。若无离画事件，不再以旧 `NOT_TRIGGERED` 否决一圈演示；若发生离画，按修订1记录 E1 等链路，链路完成本身也不能替代一圈演示。正式额度耗尽仍无合格一圈则 AC-13 `NOT_MET`，不能 `DONE`，回用户。
- **R-B10／额度与操作。** 诊断5已计本次追加的1/3，剩余只可使用既有 `diag-loopb-6`、`-7` 两个标签；正式0/8，模型启动4/10，查询9/400（余391），每次/总上限、正式 ID 与共享槽规则不变。新候选通过 C/R 前零 Play、零模型启动；通过后先对齐两处实际 checkout、操作载体及5060导入源码，重建核对传输清单、完成 amend/preflight，才可用余下诊断验证机身命令、运动、首批追平及操作页。诊断不进 AC-13…15；若需要新诊断标签、额度或额外设备，先回用户。正式 P1 操作单须先冻结一圈取样规则及失败归类，经候选停点审查后执行。
- **R-B11／诊断5。** prep §11.2 对后台持续供帧、确认时序、首批追平和用户原话的记录保留为旧候选诊断事实；实现角色对两张图的观察不代替用户逐张核对的保真结论。用户原话已指出早期画框正确、后续被运动场遮挡；本次不签 workflow §4.3.2 的“两张样帧已逐张确认”门，操作单在正式采集前须让用户或发令角色核对两张具名样帧并记录路径、确认人、结论。诊断5不证明新候选的机身运动，也不补 AC-13…15。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-4 修订 4 | R-B8：AC-4 修订2所说“无需启用 body planner”仅属旧候选；新候选每个已确认段接入冻结 threshold 规划器，原 `raw_lost`/`raw_ok`、意外段终止、人工判丢/重指定/停止的状态及单次 finalize 规则不变。新段用独立规划器实例；未确认、初始化静音、退役段和终态不得发布由图像推出的机身控制。 | test:tests.test_language_loop（段创建、重指定、退役、意外终止与机身命令隔离）；artifact:会话 JSONL、publish-receipts.jsonl | K1K2K3 | 2026-09-23 |
| AC-19 | R-B8：在 `controller/language_loop.py` 的段构造中复用冻结 threshold 配置、场景和规划器契约，不改 `controller/body_planner.py`、`config/p1-m3-body-001.json`、Unity/控制包 schema；配置不符或规划器构造失败时拒绝启动，不降级为无规划器跟踪。`TrackLoop` 的一次性初始化 hold 保留；由有效图像推导的 `velocity_world` 只能走既有 `_body_step` 与 `GatedPublisher`，与同一帧合格 `WRITTEN` 观测绑定，拒收帧、静音、段终止后零速度命令。无观测、规划器异常、命令写失败或发布门拒收时，冻结合同要求的显式安全 hold 可经无观测的安全通道发出并留下真实写入/失败收据，不能标作同帧门控速度；安全 hold 再失败即 fail-closed，接收器过期 hold 只作独立后备。相称测试覆盖配置错误、播种/追平、有效移动、无观测、发布拒收、规划器异常、写失败/后备失败、段切换；日志与收据区分命令意图和实际写入，在线路径零 Unity 真值。 | test:tests.test_language_loop（新增 body 集成具名用例）；test:tests.test_m3_body_tools（冻结规划器相称回归）；artifact:docs/evidence/P1-ENG-LOOP-001-K1K2K3-handoff.md（逐项自证、配置与命令收据） | K1K2K3 | 2026-09-23 |
| AC-13 修订 2 | R-B9：正式 P1 仍为固定红车路线、`--condition follow`、≤220s 观察窗和既有资源/身份检查。首条合格 `WRITTEN` 观测对应仿真时刻为 t0；从 t0 起同一 track_id 的连续 106.5s 为一圈窗口，预先锁定 t0 + i·(106.5/8)s（i=0…8）九个取样时刻，取各时刻最近的已保存源帧与对应观测，偏差不得超过两个采集帧；缺帧、无有效框、红车不在图中或框未落在红车上均判该次不通过，不许事后移窗/选帧。九图由用户或发令角色逐张确认并记录路径、帧号、时刻及结论；窗口内不得出现 LOST/REINIT_REQUIRED/TERMINAL、`PUBLISH_REJECTED`、身份更换或协议中止；至少一条同帧门控 `velocity_world` 写入收据且源帧元数据的机身位置相对 t0 位移≥0.5m。满足这些条件的一次正式 Play 为 `LAP_DEMO_PASSED`；任何条件不满足如实列出，旧修订1的离画事件与 E1 结局仍照录，但 `E1_ACHIEVED` 不代替本次通过，未发生离画不记旧 `NOT_TRIGGERED` 失败。此门只证明一圈按九个预定点抽样的人机闭环演示，不证明逐帧跟踪正确率；额度耗尽无通过则 `NOT_MET`，工作项不能 DONE。 | artifact:docs/unity-test-log.md `UT-P1-ENG-LOOP-001-P1`（预定点、逐张人眼结论、机身位移、终态）；artifact:会话 JSONL、源帧副本、results.jsonl、publish-receipts.jsonl；artifact:docs/evidence/P1-ENG-LOOP-001-play-cases.md | K1K2K3（Play证据） | 2026-09-23 |
| AC-12 修订 6 | R-B10/11：操作单 C 和预算 runner 沿用已签发诊断与正式标签、累计记账，更新为先新候选 K1K2K3 通过、再诊断6/7、后正式 P1/P2；不得重置旧记录或增加标签。正式 P1 前完成两张具名样帧的人眼保真检查并保存路径/确认人/结论，冻结 AC-13 修订2 的九个取样规则及源帧保全方法；采集 checkout、Unity 主树、5060 导入源码与载体逐项对应最后通过候选。正式发令前记录 HEAD/status 并检查共享槽，候选不一致或安全收据缺失即停。 | artifact:docs/evidence/P1-ENG-LOOP-001-operations-c.md；artifact:docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md；artifact:docs/unity-test-log.md；cmd:git rev-parse HEAD / git status --porcelain（实际采集环境） | K1K2K3 | 2026-09-23 |

本批新增 AC-19 一行，追加修订三行；旧核对表保留为 R6 之前候选的当时结论，待新候选自证后才由 C5 替换。F3 仍 `SCOPE_GAP`/OPEN，AC-13…15 正式 Play 均未运行；本裁定零测试、零代码、零 Play/模型/ID/传输。

**R-B12…13（2026-09-23，Owner：Acceptance；来源：stage-b-prep §13.1…13.4）。** 诊断 6 在 R7 通过候选上取得：后台持续供帧（`unfocused_frames` 1047、`max_stall_s` 0.0）、段 1 首批追平 `WRITTEN`（42 帧 0.397 s、发布帧差 2）、机身同帧门控 `velocity_world` `WRITTEN` 110 条、安全 hold 48 条、`WRITE_FAILED`/fail-closed 0、位移 20.6 m、两张具名样帧用户逐张确认；段 2–4 首批 44/32/44 帧、每帧 20.7/19.0/39.4 ms、发布帧差 5/3/8，均按 AC-3 五项门 ④ 记 `PUBLISH_REJECTED(catchup_stale)` 并 finalize，操作单 §0 硬停止成立，正式 P1 未放行。以下是实现期合同问题的答复：不开 D 轮、不签独立复核、不跑测试、不改任何 verdict 或机械归因；用户阶段 B 信封「遇发布门失败先停正式尝试并按原返工渠道处理；不放宽 0.4 s 门、K 或场景、不反复试到成功」是本裁定的边界。

- **R-B12／归因与处置。** (1) 段 2–4 的拒收是 AC-3 门的正确 fail-closed；`_gate` 与收据无实现错误，不记 finding。(2) 不能稳定通过的原因不在门值，而在 §3.3「第一次 `process_available()` 前 unmute」把整个首批追平压进单批 `T_pub` 0.4 s / `K_pub` 2 帧：积压 32–44 帧（合同上限 K_ret+K_conf=80）要求每帧 ≲ 9 ms（80 帧时 ≲ 5 ms）。R1 §4 注记 6 与阶段 B 注记处置已预告「现有模型 p95 不能证明该门可过」；诊断 5/6 实测每帧 5 ms、9.5 ms 擦线通过，19–39 ms 失败，证明该单批要求在本机没有余量。这属 K1 合同的追平机制，由接受侧按追加修订 AC-3 修订 3 处理：改为静音多批收敛、每条 `WRITTEN` 仍逐条过五项门，不改 `K_pub`=2、`T_pub`=0.4 s、`T_stall`、场景、跟踪核心与积压来源（模型时延、人工确认时间），故不属信封所禁的「放宽门/K/场景」，是信封点名的「原返工渠道」；若用户认为改追平机制也须先问用户，可在 C7/R8 之前撤回，本裁定在通过前零消耗。(3) 段内每帧耗时随会话时间 2–4 倍变慢（跟踪 `compute_latency_ms` 与读帧/日志开销同时变慢）原因未测，不归因实现或环境；新候选须让追平期每批帧数、批墙钟、批末帧差与静音状态可从会话 JSONL 与收据机械复算，诊断 7 据此归因。(4) 处置：回 `K1K2K3` 停点，实现角色按 AC-3 修订 3 与 AC-12 修订 7 出新候选并自证，经 `C7@K1K2K3`（本停点核对轮退回额度已在 C5 用尽，C7 不退回、照交复核并附核对表）与新鲜上下文 `R8@K1K2K3`；K1K2K3 C/R 与返工计数不重置，R7 通过候选只覆盖旧追平语义。通过前零正式/诊断 Play、零模型服务启动、零传输。(5) `diag-loopb-7` 只在新候选 R8 通过、按操作单 §1 对齐两处 checkout、重建清单、传输授权范围内源码、`amend`/`preflight` 之后使用，作为 AC-12 修订 6 次序中新候选的必经诊断，检查静音追平收敛（首条 `WRITTEN` 距 `initialize` ≤ T_catchup、期间零写入零速度）、机身跟随与择时规则；不用于在正式运行之间试数。诊断 7 再次硬停止或额度不够即回用户，不自行新增标签或额度；正式 P1 在此之前不放行。
- **R-B13／播种时刻目标近离画。** (1) 指定→首条 `WRITTEN` 的时延 = 模型（≤ T_ret 6 s）+ 人工确认（≤ T_conf 10 s）+ 追平，实测约 8–13 s；固定朝下相机的红车停留窗按操作单 §4 推算为 sim_t 0–12 s、99–118 s、206–225 s。诊断 6 在第 1 窗（12 s）于 sim_t 4.4 s 指定，播种时红车已在画面右缘，云台饱和后约 3 s 跟踪框漂到看台与出租车。这是择时与冻结跟踪器能力的交互，不是任何 AC 的实现错误，也不改 AC-13 修订 2 的通过条件。(2) 合同层只做择时前提：AC-12 修订 7 把操作单 §4/§5 的「用第 1 窗」改为「红车刚进入固定朝下画面时立即指定（入画后 ≤ 2 s），优先第 2 窗起点（sim_t ≈ 99–101 s），第 1 窗仅在 sim_t ≤ 2 s 能指定时使用」；C5-2 的 t0 ≤ 113.5 s 与 220 s 观察窗不变，错过起点即等下一窗或如实中止，不延长 Play。(3) 不改场景、跟踪核心、冻结规划器阈值（`config/p1-m3-body-001.json`）与「仅人工重指定」定局；跟踪漂移导致一圈不通过按 AC-13 修订 2/AC-15 如实记为失败案例。(4) 停止规则（信封内约束，不增额度）：正式 P1 连续 2 次因同类原因（跟踪漂移或择时）不通过即停并回用户，由用户决定是否继续使用余下正式额度；不反复试到成功。
- **两张样帧与首批追平前提。** 诊断 6 的两张具名样帧（帧 22 候选 `q2`、帧 64 核验 `q3`）用户逐张确认「一致，框在红车上」「一致，两框都在红车上」，满足 workflow §4.3.2 与 AC-12 修订 6 对本渲染/采集管线的人眼保真前提，已代录 Unity 日志；新候选不触及帧采集、保存与预览路径时该记录沿用，触及则在诊断 7 重做。首批追平前提在旧语义下仅段 1 满足，新语义由诊断 7 重测。诊断 5/6 产物不进 AC-13…15 证据链。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-3 修订 3 | R-B12：§3.3「第一次 `process_available()` 前 unmute」改为静音追平收敛：段 `initialize(N)` 后发布器保持静音；每个处理批开始前读 `latest.json`，仅当积压（latest − 已处理末帧）≤ K_pub 时 unmute，该批批末帧再过五项最终门写出；积压 > K_pub 的批其批末帧观测与衍生控制记 `MUTED_DROPPED`、零写入、零速度命令（AC-19 安全 hold 通道不变）。自段 `initialize` 完成墙钟（会话 `segment_seeded` 记录）起 T_catchup = 6.0 s 内无首条 `WRITTEN` → 段 finalize `REINIT_REQUIRED(catchup_stale)`（依据：诊断 6 最差 39.4 ms/帧 × 合同最大积压 80 帧几何收敛约 3.9 s，取 1.5 倍）；T_catchup 与 AC-10 修订 1 冻结常数同列入具名测试。K_pub=2、T_pub=0.4 s、T_stall=3 s、五项门内容、`catchup_stale` 出口含义、`frame_stall` 规则不变；不改 `controller/track_loop.py` 冻结批处理、不改场景与跟踪核心。会话 JSONL 每条 `frames_processed` 带批帧数、批墙钟耗时、批末帧差与静音状态，追平表可机械复算。相称测试：单批可收敛（沿用）、多批收敛后首条 `WRITTEN` 过门、收敛期间零 `WRITTEN`/零速度、T_catchup 超时 fail-closed、unmute 后门再次失败仍拒收。 | test:tests.test_language_loop（`CatchUp*` 新增多批收敛/超时/零写入具名用例、`HostDecisionTests.test_frozen_constants`）；artifact:会话 JSONL、publish-receipts.jsonl；artifact:docs/evidence/P1-ENG-LOOP-001-K1K2K3-*（自证与追平表） | K1K2K3 | 2026-09-23 |
| AC-12 修订 7 | R-B12/13：操作单 C 随同一候选修订：§0 硬停止集合不变；§4/§5 择时改为「红车刚进入固定朝下画面时立即指定（入画后 ≤ 2 s），优先第 2 窗起点，第 1 窗仅 sim_t ≤ 2 s 可指定时使用」，C5-2 的 t0 ≤ 113.5 s 不变；§4 增加诊断 7 检查项（首条 `WRITTEN` 距 `initialize` ≤ T_catchup、期间收据零 `WRITTEN`/零速度、追平批表）与「记录 Play 期间同机运行的载体/进程清单」；§5 增加停止规则「正式 P1 连续 2 次同类原因不通过即停并回用户」。诊断 7 只在新候选 R8 通过并完成 §1 对齐/传输/`amend`/`preflight` 后使用；两张具名样帧人眼记录沿用诊断 6（不触及采集/保存/预览路径时）。 | artifact:docs/evidence/P1-ENG-LOOP-001-operations-c.md；artifact:docs/evidence/P1-ENG-LOOP-001-stage-b-prep.md；artifact:docs/unity-test-log.md | K1K2K3 | 2026-09-23 |

本批追加修订两行、新 AC=0（实现期修订累计 19、新 AC 累计 2）；无 finding、机械归因不变；F3/F8 仍 `SCOPE_GAP`/OPEN，AC-13…15 正式 Play 均未运行；本裁定零测试、零代码、零 Play/模型/ID/传输。


## Acceptance rulings（复判）

**2026-09-22，Owner：Acceptance。** 当前办理 R4 终局结果汇总与冻结集收尾，不开新 D/C/R 轮；
上文历次交接和下表 R2 消费按当时候选保留，当前动作只以状态板 Active handoffs 为准。
AC 原文、八行首次释义及十二行实现期修订保持。本批不改合同、不签独立复核。

| 来源（复核文件/轮次/finding） | 裁定 | 日期 |
|---|---|---|
| docs/reviews/P1-ENG-LOOP-001.md / R2@K1K3 / verdict | 消费 PASS_WITH_NOTES：K1K3 的独立复核门通过，AC-1…12/16/17 的阶段 A 证据满足；AC-13…15 待真实 Play，不申请 UNITY_NA，不标 DONE。通过候选只从该文件最后一条 passed_candidate 运行时解析。F1/F2 按 R2 红绿核实 CLOSED，不再重做常规候选核对。 | 2026-09-22 |
| docs/reviews/P1-ENG-LOOP-001.md / R1、R2@K1K3 / F3 | 按原 SCOPE_GAP 非阻断记债 OPEN，落点为 implementation-status 的同 work ID/F3 行；不改标、不写 RELEASED_SCOPE_GAP（本项未发出相应 block）。排队时间计入 worker 硬限可能误报 backend_fatal；现有时延样本只支持当前证据域未触发，不能当作未来时延的上界证明。下一次触及 LanguageWorker 或扩展延迟/排队域前承接；若 B 实际触发，保留原失败，按合同缺陷/返工渠道处理，不以记债豁免。 | 2026-09-22 |
| docs/reviews/P1-ENG-LOOP-001.md / R3→R4@K1K3 / F4 | 冻结集裁定「范围内必修」，依据 BC-12 对应 AC-12 修订3，发布帧号呈现是已冻结操作单的可达步骤。按 R4 §1 具名生产写者回归及修前红/修后绿核实记 CLOSED，不追加义务。 | 2026-09-22 |
| docs/reviews/P1-ENG-LOOP-001.md / R3→R4@K1K3 / F5 | 冻结集裁定「范围内必修」，依据 BC-13 对应 AC-13 修订1，告警提示须绑定触发 query_id。按 R4 §1 的跨文件时序回归及红绿核实记 CLOSED；该操作层闭合不替代 AC-13 的真实 Play。 | 2026-09-22 |
| docs/reviews/P1-ENG-LOOP-001.md / R3→R4@K1K3 / F6 | 冻结集裁定「范围内必修（非阻断 CLASS_3）」；依据 IN_SCOPE_NO_BC 保持，逐字补丁按 R4 §1 已应用，不再派发，不新增 AC。 | 2026-09-22 |
| docs/reviews/P1-ENG-LOOP-001.md / R4@K1K3 / F3 | 冻结集裁定维持 SCOPE_GAP/OPEN；唯一债务入口仍为 implementation-status 同名行，原触及路径前承接与实际触发即返工的限制不变。无 block 可 release，不写 RELEASED_SCOPE_GAP。 | 2026-09-22 |
| docs/reviews/P1-ENG-LOOP-001.md / R3 §4 注记2、R4 §4 注记5 / AC-11 | 采纳无 runtime 诊断残留的隔离副本作为本项停点全套运行位置。依据 -K1K3-r3-fix.md §5、-tests-r3-fix.log 与 R4 §0：1524例、0 failures、9既有errors、68 skips，新增失败0，AC-11 本候选满足。RealArchiveClosureTest 五项未执行，不声称归档闭合通过；主树原失败及404张残留保留，不删数据、不改旧枚举合同，不另立修复项、不追加 AC。此为复核路由的证据/运行环境处置，不把 skip 改成 PASS；后续触及旧归档枚举再单独处理。 | 2026-09-22 |
| docs/reviews/P1-ENG-LOOP-001.md / R4@K1K3 / verdict、上下文披露 | 汇总 PASS_WITH_NOTES：F4/F5闭合、F6已应用，AC-4/12的离线候选偏差已解；AC-13…15仍 NOT_RUN。R4 明示沿用 R3 会话且不满足新鲜上下文字面；roles/review.md 开工1要求「本会话必须是新鲜上下文」。当时账本无该例外授权，报告转述「做 R4@K1K3」不等于明确豁免。原 verdict 与 passed_candidate 不改写，当时暂不据此发消耗性交接，请用户决定仅本次接受该上下文例外，或交新鲜上下文复核角色补核本候选的 R4 终局依据；无新 diff 不擅开 R5。该流程事项不伪造为代码 finding 或 blocks 行。 | 2026-09-22 |
| docs/authorizations.md / 2026-09-22 接受本次 R4 同会话上下文例外 / 用户裁定 | 用户原话「接受本次例外，按既有信封继续」已逐字入账，解除上一行的上下文待裁定阻塞；仅本次例外，不改常驻规则、不追称新鲜上下文。正式消费 R4 PASS_WITH_NOTES，K1K3独立复核门通过，AC-1…12/16/17离线证据满足，AC-13…15仍NOT_RUN；按既有信封交实现/用户推进新增诊断，全部正式Play前提与额度保持。 | 2026-09-22 |
| docs/reviews/P1-ENG-LOOP-001.md / R5@K1K3 / F7 | 冻结集裁定「范围内必修」，维持 CLASS_2 / `BC-18`（工程轨道对应 AC-18），不改标 `SCOPE_GAP`：AC-18 明定未知结果不得自动换 `request_id`，AC-1 修订 1 明定 `WRITER_BUSY` 及同 ID 重试；操作单允许页面与终端 CLI 并用，锁忙路径可达。R5 §3 的探针证实未知条目及守卫丢失、新 ID 重发、迟到回执失联。归因为实现错误，不新增 AC、不记范围外债。R5 是本停点第 3 次 `REWORK_REQUIRED`，既有终局上限不重置；本裁定不授权超限返工、不派发实现，用户须决定仅 F7 的一次额外返工及新鲜上下文 R6，或终止本范围。决定前保持零 Play、零模型服务、零迁移/传输；F3 原 `SCOPE_GAP` 债不变。 | 2026-09-23 |
| docs/authorizations.md / 2026-09-23 R5/F7 一次定向超限返工 / 用户裁定 | 用户原话「授权一次定向返工」已逐字入账；按上一行待决对象，额外允许一次仅闭合 F7 的返工。实现角色按 R5 §3 补生产写者夹具的具名修前红/修后绿，稳定候选直接交新鲜上下文 R6@K1K3（返工不经 C5）；R6 同时检查修复触及行 CLASS_1/2 与 RED_LINE。R6 不通过则回用户，不自动授予 R7。此授权不增模型、Play、ID、传输等额度；R6 通过前仍禁消耗性执行。AC-13…15 与 F3 债不变，合同无新增或修订。 | 2026-09-23 |
| docs/reviews/P1-ENG-LOOP-001.md / R6@K1K3 / verdict、§4 注记3 | 消费 PASS_WITH_NOTES：F7 按 R6 §1 生产路径回归修前红/修后绿闭合，触及行无 CLASS_1/2、无 RED_LINE；K1K3 新范围独立复核门通过。用户在实现会话选择的一并处理竞态和新点击 exit 1 均在 AC-18／AC-1 修订1既有语义及 F7 同一路径内；后者修正「可能已写入却允许换 id 重发」的同类缺陷。两项零资源消耗、不改合同或授权信封；选择已在实现证据 §3 留原标签，无须新增关键授权条目。R6 的 F7 闭合不消除 F3 的 SCOPE_GAP/OPEN 债。 | 2026-09-23 |
| docs/reviews/P1-ENG-LOOP-001.md / R6@K1K3 / 复核档位披露、§4 注记7 | R6 是新鲜上下文；复核者披露为 Claude Opus 5.5，与实现提交所披露档位相同，满足 workflow §1.1 不低于实现者且非最便宜档的硬门。Fable 池当时可用性未核实，不追称已耗尽；接受其明示档位的本轮结果，不据此要求改写复核 verdict。阶段 B 已有正式/诊断信封及 5060 代码/清单传输授权可继续使用；先从最后 passed_candidate 对齐采集 worktree、重建并核对清单、传输授权文件、amend/preflight，再按操作单 §2 做发令检查。实现负责零消耗准备及获准诊断的技术操作，用户负责 Unity Play、人工按钮和两张样帧人眼保真；诊断不能代替 AC-13…15 正式证据。 | 2026-09-23 |

| docs/reviews/P1-ENG-LOOP-001.md / R7@K1K2K3 / verdict、F8 | 消费 `PASS_WITH_NOTES`：新 K1/K2/K3 候选独立复核门通过；聚焦与载体自测、C5 反证红绿及全套日志核对见 R7 §0–§2。通过候选只从复核文件最后一条 `passed_candidate` 运行时解析。F8 依 R7 §3 的生产写者不可达判据维持 `SCOPE_GAP` 非阻断，记入 implementation-status 同 ID/F8 行 `OPEN`；事后改写保存 JSON/索引可污染时刻或位移，复用可变归档或发现来源异常前承接一致性回归，实际证据异常须停，不以记债豁免。无 block 可 release，不写 `RELEASED_SCOPE_GAP`；F3 仍 OPEN。本轮不新增 AC、不改原 verdict、不签独立复核。 | 2026-09-23 |
| docs/reviews/P1-ENG-LOOP-001.md / R7@K1K2K3 / §4 注记1、3、4、9、10 | 段 finalize 不补显式 hold：AC-19 只列举无观测、规划器异常、写失败、发布门拒收四类显式安全 hold；AC-4 保留 finalize 后零收据，冻结 `_body_step` 为图像机身写入点。接受按既有字面维持接收器 0.4 s 过期后备，不新增终止时写入义务；若实际触发风险按失败记录，不将其当安全 hold 已写出的证据。C6-2 的处理后帧要求与现操作单一致，不修改冻结操作单；九点保守同帧收据规则维持。执行链先做本地零消耗对齐与清单重建；正式 P1 前两张具名样帧人眼保真仍为硬前提，AC-12…15 均未提前完成。5060 原授权只点名两个源码，新增 `controller/gated_publisher.py` 须用户另行授权后才传输；此前不启动模型或 Play。 | 2026-09-23 |
| docs/authorizations.md / 2026-09-23 用户暂停 AC-3 修订 3 返工，快层替换探针先出数据 / 用户裁定 | 用户原话「暂停返工，探针先出数据」已逐字入账。AC-3 修订 3 与 AC-12 修订 7 保留在合同内但不派发实现；C7/R8@K1K2K3 未开；R7 通过候选、F3/F8 记债、阶段 B 剩余额度（诊断 1、正式 8、启动 5、查询 380）与两张样帧人眼记录全部不变。本项 Lifecycle 转 PAUSED，停点与恢复条件见 docs/parked-status.md 同名小节；快层替换探针另立新工作项，其结论出来后由用户决定本项续跑（恢复交接、出候选走 C7/R8）或收口（`CLOSED_*`，同批写明保留义务）。零消耗。 | 2026-09-23 |

**归因与度量（截至 R4）。** F1/F2（BC-1）及 F4（BC-12）、F5（BC-13）→ 实现错误4；
F6（IN_SCOPE_NO_BC，非阻断CLASS_3）→ BC缺失1，F3（SCOPE_GAP，非阻断）→ BC缺失1，分计。
上轮漏检/上游漏检/RED_LINE各0；测试运行位置和上下文披露均为注记/流程处置，不混入finding。
设计退修2，K1K3 C/R=2/4、C退回0、R返工2；工程AC原项17、首次释义8、实现期修订12，
本批新AC/修订0。冻结集裁定在R4之后补齐，如实保留时序，不声称复核开轮前已裁定。
阶段A归因仍见C1决策行；阶段B旧诊断3/2（超用1）、新增0/2、正式0/8、模型启动2/10、
查询1/400均未改变。本次没有运行实现测试、模型、Play、传输或创建ID。

**R3/R4 注记处置。** R4 §4 注记1 的 tracker_failure 预览措辞沿用打印路径手动查看，不派发修辞修复；
R3 §4 注记1 的真实 Unity 正向 lc_check 尚未执行，首次输出仍须原样入 prep；注记5 的管道退出码
可能被 tee 掩盖，结果按 watch/session-process.log 判读，不用退出码冒称成功。既有操作单已承接，
不修改冻结操作单、不触发新候选。采集 worktree 本轮只读核实仍停在 R2 通过候选；
放行后依操作单§1/§2对齐最新 passed_candidate、重建并传输授权范围内代码清单、amend/preflight，
再按R-B4完成持续供帧、首批追平及至少两张样帧人眼检查。当前尚未执行或发令，正式采集仍须全部前提。

### 阶段 B 信封申请与注记处置（2026-09-22 已签发）

**申请对象：§5 阶段 B 原额度，Mac Unity/NanoTrack-v2 客户端 + 已选 5060/http/c2-adapter。**
模型、端点、hz/R、K 与测量来源绑定沿用现有 K 收据，不以新授权自动更换宿主、模型或放宽门槛。
用户已在本接受会话以原话“签发”批准本节申请，授权原文及完整信封见 `docs/authorizations.md`
2026-09-22「签发阶段 B（Play 证据）执行信封」。以下额度与执行次序现已生效；原消费时点未授权的记录保留为历史。

| 资源 | 已签发上限（成功、失败、中止、重试均计） |
|---|---|
| 正式 Play / ID | ≤8 次，每次≤300 s 仿真时间；≤8 个正式 session、每 session≤4 段（run 合计≤32）；沿用 deterministic-loop-default，新 scenario=0。NOT_TRIGGERED 亦扣次。 |
| 诊断 Play | 首次签发≤2；后续追加2见 Pending rulings R-B2/AC-12修订3与同日授权条目。旧实际3/2（超用1），新增0/2；每次≤300 s、≤4段、零正式ID，不进AC-13…15。 |
| 本地模型启动 | 正式与诊断合计≤10 次（5060 HTTP 服务启动同计）；不把阶段 A 剩余额度叠入本上限。 |
| 本地模型查询 | 每次正式或诊断 Play≤40 行，合计≤400；指定、重试、核验、失败调用均计，前置拒绝按 AC-6 分列，不冒充调用。 |
| 其余 | 外部模型 API=0、训练 GPU·h=0、合并=0；下载/资产传输=否；609 行复算、Jetson、云端、公开发布=否。既有本地 HTTP 推理传输沿用 AC-12 修订1。 |

**执行次序（随本次申请获用户批准）。** Implementation 先补操作单 C 与客户端环境核对，
用户按 C 操作 Unity；先用第1次诊断检查确认后首批追平，再进入正式 P1/P2。诊断只暴露问题，
不提供通过证据；若遇发布门失败或没有可核对收据，先停正式尝试、报告原因并按原返工渠道处理，
不反复试到成功。仅有诊断通过也不保证正式成功。实际资源耗尽即停，AC-13 无合格 E1 仍 NOT_MET、回用户。
操作单 C 与 play-cases 报告是既有阶段 B 交付，不由本轮消费 verdict 代写成已完成。

| 注记来源 | 处置 / 后续落点 |
|---|---|
| R1 §4 注记6：首批追平门 | 风险已评估：K_ret=30、K_conf=50，允许窗口可积压约80帧；冻结核心先整批加载再逐帧 update，T_pub=0.4 s 约容纳平均每帧5 ms，且仍须满足 K_pub=2 与采集年龄门。现有模型 p95 不能证明该门可过。首个诊断保存第一批的 load_elapsed_s/frame_delta、发布收据、终态与实际确认延迟；不修改 T_pub、K、场景、跟踪核心或靠暂停供帧“通过”。 |
| R1 §4 注记3 / C1-5：客户端解释器 | 操作单 C 点名同一 Mac 会话解释器中的 NanoTrack-v2、cv2、Pillow 与 HTTP 依赖，并由实现角色核对可导入性及 pip check；阶段 A 模型环境通过不替代客户端核对。保持原环境保护与 T7/F盘约定；若需额外下载/传输或更改绑定环境，先报告所缺条件和额度，不能把 §5 的“否”解释为已授权。 |
| R2 §4 注记1：F1 日志落点 | 消费复核已认可的 CLI stderr/stdout 落点；操作单 C 保存操作者 CLI 两路输出，与会话日志一起留存。不要求改成会话 JSONL、不新增桥协议；没有据此追加 AC。 |
| R2 §4 注记2：ignored 优先级 | 本批不要求改变回执优先级，保留复核注记：同 id 重新写入可能优先返回 IGNORED_DUPLICATE（包括 TERMINAL/外会话残留 id 被重用），不表示动作执行。新业务动作使用新 id，未知结果的重试沿用原 id；操作单 C 披露原候选行为。本次不把注记改造成新的协议承诺或 AC。 |
| R1 §4 注记2/5/7/8：日志解读 | inconclusive 已完成核验仍消耗配对帧；发起前跳过日志可能每 tick 重复；无合法帧的 designate 重试可能在一个 tick 耗尽；ILLEGAL_WRITER_SUSPECTED 可能来自合法请求的迟到消费。操作单 C/报告按原注记解释，不改查询/完成数或告警口径。 |
| R1 §4 注记1/4、R2 §4 注记3/4/5 | 保留防御性 raise、失败路径副本覆盖、写入身份分辨率、死锁测试 pid 复用、未使用辅助函数的非阻断限制；下一次触及相应路径时重读原注记。本批不自动派发修复、不称已闭合。 |

**采集候选与证据门。** 本次从复核机读行解析候选后只读检查提交关系和变更文件：
该候选是当前 HEAD 的祖先，本项运行时/合同/原始证据未漂移；后续差异包含 COORD-013
的工作流工具与测试，不能把整棵 HEAD 冒称“只有白名单文档差异”。正式采集前按 workflow §4.5
从已通过候选解析采集 checkout，并由发令角色把实际 HEAD/status 写入 Unity 日志；
若选当前 HEAD，须先处置该非文档差异的候选对应性，不能直接沿用旧通过指针。
发令时再次全局核对消耗性门、共享槽互斥与计数；本次签发代录未创建正式 ID，后续执行按已签发信封计数。
AC-13 的源帧/事件窗口/聚合优先级、AC-14 的各结局适用检查、AC-15 描述性数字与失败保留
全部沿用合同。新管线首次正式采集前的人眼保真检查按 workflow §4.3.2 执行；
Play 暴露实现缺陷时回同一 K1K3，沿用 C/R 计数，不预签新的通过 verdict。
