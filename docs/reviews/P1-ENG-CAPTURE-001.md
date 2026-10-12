# P1-ENG-CAPTURE-001 独立复核（第一轮 VLM 旁路移动目标捕获，engineering-v1，停点 `K1K2K3K4`）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-CAPTURE-001-R1@K1K2K3K4-20261010T032656Z-a586`，`requested.round = R1@K1K2K3K4`）。
轨道：提案抬头逐字 `Workflow: engineering-v1`，接受角色在「终局裁定（第三次，依用户 (a)）」`ACCEPTED` 时逐字裁定生效 → 按 `docs/engineering-workflow.md` 复核；依据列仍写 `BC-n`，读作任务合同第 n 条验收项 `AC-n`（含其修订）。
零消耗：零 scenario/session/run ID、零 Unity Play、零 VLM/API/云 GPU、零下载/安装、零真实 YOLO 加载/构造/推理（focused 重跑排除 F12 清单的 `test_det_assoc_carrier`；`BaselinePackageTests` 只核权重文件身份）、零回放、零全套。只在一次性副本 `.claude/worktrees/review-P1-ENG-CAPTURE-001` 接触实现代码；主工作树实现文件只读；本会话未修改任何实现文件（收工边界自查见 §5）。

## R1@K1K2K3K4（2026-10-10）

### §0 候选、基线、开轮资格与重跑

- `round_candidate: e22d75d8c1f02097b3c96c03ccbf84f45d5ee503`（派发指定；= 交接证据文首「本轮末提交」，`origin/main` 祖先；代码/测试冻结于其祖先 `9bb0430`，其后只有证据、账本与状态板）。
- 全量 diff 基线：本文件此前不存在，无 `passed_candidate`；`$BASE` = 提案 `Status: ACCEPTED` 首次进入的提交（运行时 `tools.eng_capture.common.accepted_base_commit()` = `9f1a8cc…`，与 `-tests-baseline.log` 归因基线相同）。`git diff --stat $BASE..$CAND -- controller tools tests config` = **29 文件 +9970/−85**（PLAY_GOVERNING 非空 → 开轮；`Assets/`、`ProjectSettings/`、`Packages/packages-lock.json`、`config/scenario.*`、`controller/scenario_tether.py`、`controller/standoff_planner.py`、`controller/trackers.py`、`tools/eng_sft`、`tools/eng_jet` 零 diff；`tools/eng_loop2/` 只有 `operator_web.py`）。首个复核轮，无上一复核轮候选、无既往 finding 闭合义务。
- 停点自证（`docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` §8）四项：①冻结成立（`9bb0430..e22d75d` 零代码 diff）；②相称测试——停点全套 1 次已跑（Ran 2656 / F28 / E34 / S56，本轮按模块重数 62 条失败 = scene006 29 + play_ops 24 + 导入错误 5 + trackers 1 + track_loop 1 + carrier 1 + loop2_freeze 1，与 handoff「基线 61 + IR-2 预期 1、新增 0」一致），每条 C1 返工项带具名红绿；③不适用（阶段 A 零 Unity，不记 `UNITY_NA`）；④状态/候选/范围/风险齐备。C2 把②记「证据缺失」只因 C2-P1/2/3 边界未对准，不构成自证不成立 → **不给 `REVIEW_BLOCKED`，开轮**。
- 复核副本 detach 于候选；树哈希 `HEAD:tests = 036f46cf97bf58b7fa6113dd42a1dbff818571a9`、`HEAD:controller = fc6ab89754ad795429e89f83bac079e9c1e8f7e3`、`HEAD:tools = c78a5fedf350071c1f5e8423fd4cb9e87cead53c`、`HEAD:config = 8bb9f62bd594fa57f36af90a9a9fd57fa8cb875c`。解释器：mini `.venv-yoloe/bin/python`（3.12.14；进程设 `YOLO_OFFLINE=True YOLO_AUTOINSTALL=False`）。副本缺 `outputs/`，以只读符号链接 `outputs/{eng-det,eng-loop,eng-capture}` 指回主树原件（不写）。
- **focused 重跑**（副本内 `-m unittest discover -s tests -p <模块>.py`，19 个模块，输出写会话暂存目录、只回显摘要）：`test_language_loop` 205 OK、`test_language_bridge` 50 OK、`test_target_manager` 44 OK、`test_capture_session` 26 OK、`test_capture_click_web` 13 OK、`test_capture_replay` 37 → 36 OK + 1 ERROR（`AdmittedInputTests.test_check_input_matches_sums_and_alignment`：`check_input` 对准入文件 `resolve()` 后 `relative_to(PROJECT_ROOT)`，符号链接解析到主树，副本环境产物，非候选缺陷；首次运行 5 个 `NewArmEndToEndTests` ERROR 亦为副本缺权重链接所致，补链接后全部 OK）、`test_capture_isolation` 6 OK、`test_pose_center` 6 OK、`test_pose_gmc` 8 OK、`test_resident_core` 37 OK、`test_det_assoc_tracker` 37 OK、`test_gated_publisher_slew` 3 OK、`test_track_loop` 27（1 FAIL = 基线 CSRT，与 `-tests-baseline.log` 同）、`test_eng_acq_e1` 17 OK、`test_eng_loop2_operator_web` 31 OK、`test_eng_loop2_analyze` 63 OK、`test_loop2_isolation` 10 OK、`test_loop2_freeze` 3（1 FAIL = IR-2 合同预期失败）、`test_frame_follow_replay` 19 OK。
- **C1 返工具名回归修前红核实**：副本内 `git checkout 2d12c50 -- controller tools`（候选 1 代码，测试留候选 2）→ `-k c1_`：`test_target_manager` 7 用例 19 子例 FAIL、`test_capture_session` 2 FAIL、`test_capture_replay` 10 FAIL + 6 ERROR；恢复候选 2 → 上述 focused 全绿。C1-1…C1-5 的红绿主张成立。
- **证据核对**：`-ledger.json` 计数 = 事件和（全部 15 维）、无未结算 in_flight、候选 2/3；每候选加载 {1: 2, 2: 1} ≤ 2、推理 {1: 3962, 2: 3962} ≤ 5,500、全套 {1: 1, 2: 1}、构造 {1: 2, 2: 2}、focused 真实加载 8/20、磁盘 47,019,465 B（账本 `mini_new_disk_bytes_total` 写 3,221,225,472 = 3 GiB；用户 2026-10-10 已按上界裁定磁盘维未越界）。`LanguageWorker` 类文本在 `$BASE` 与候选逐字节相同（sha 前缀 `7ec8941d5b4ec487`，AC-13）；`follow(`/`designate(` 调用点闭集 = `target_manager.py`（commit/_rollback/_release）+ `resident_core.py::designate` 外壳 + `det_assoc_tracker.py::follow` 转发，`language_loop.py` 零直接或 `getattr` 调用（AC-7）；`controller/` 与 `click_web.py` 代码中无真值 token（AC-16）；`.gitignore` 含 `/outputs/eng-capture/`（AC-20 修订 3）；`operator_web.py` diff 恰 §2.5 两处（AC-14）。
- 本轮磁盘（用户 2026-10-10 裁定「以后的临时工作区必须实测记账」）：一次性副本检出峰值 **81,477,632 B**（`du -sk`，不含符号链接目标；收工已删除，净新增 0）；会话暂存目录 27,131,904 B（含 focused 日志与两份探针脚本）。本角色无 `docs/evidence/` 写权限，账本补记由接受/实现角色按此读数处理。

### §1 逐文件核对摘要

| 文件 | 结论 |
|---|---|
| `controller/target_manager.py`（新，K2/K3） | §3.2 记录与 AR1-3 计数矩阵（click/lang_confirm +intent/+episode、repair 只 +association_revision、lang_acquire +episode 不加 intent、被拒零变化）、`transition` 唯一写 `continuity_status`、§3.3 同帧顺序 ②→③→④→⑤ 与 C1-3「本帧 ① 已提交则直接 ⑤」、`same_frame_prior/post` 四元对齐 + S 可逆（C1-1）、IR-6 竞争公式（`NIS_c − NIS_o < m_nis`，不取绝对值）、门 0、`derive_authorization` 先 G 一致性再八行首命中（AR1-2 修订 1）、`commit_binding` 事务（快照 → follow(new) → 失败 follow(old)+restore+readback → fail-closed）、`PORT_CALLS` 落盘。**缺陷**：`ReplayPort` 对缺行/截断默认成功或退回本地模型，见 R1-1。 |
| `controller/det_assoc_tracker.py`（K1/K3） | `class_policy` 闭集与缺省 `per_class`、`unify_vehicle` = `agnostic_nms=True` + cls 置 0、缓存键含策略；`_pre_first_associate` 在补偿后、首轮关联前复制 prior（none/optflow/H 缺失同阶段）；`_post_snapshots` 以 `track.frame_id == library_frame_id` 分 posterior/prior（lost 行 `mark_lost` 不改帧号 → prior，与 §3.1 一致）；未确认行、`matched_det_index`、`silently_dropped_ids`；`history_view` 缺省 compat（IR-1）。 |
| `controller/resident_core.py` | `KfSnapshot`/`make_kf_snapshot`（非有限、w/h ≤ 0、非对称、非 PSD → invalid+原因）、`RawDetection`、`TrackRow`/`HistoryEntry` 新列只在非缺省时进记录（旧字段集不变）；compat 视图丢弃出画/退化 lost 与未确认行（IR-1）；`pointer_result` 对 lost/出画/未确认均非 ok；`designate` 拆为 `allocate_designation_id` + 纯 `resolve_designation` + `record_designation`，外壳只供 e1；快照三件套深复制。 |
| `controller/language_loop.py` | `--language off` 不读 K 收据、不建适配器/worker、`LANGUAGE_ONLY_ACTIONS` → `language_disabled`；`_CaptureHook` 在 k 帧 ⑤ 之前提交追平点击（C1-3）；`_resolve_click` 以 `runtime/frames` 当刻字节 sha 核 `image_mismatch`；兼容路径先 `allocate_designation_id` 再纯解析再记录（失败也占号，AR1-3），BOUND* 经 `commit_binding(lang_confirm)`，TRACK_ENDED → `accept_language_task`；`_retire_pointer` 清指针改经 `release_binding`；`stop()` 先 `request_stop` 再 `_capture_hold`；`_binding_fail_closed` HOLD/撤关联/REINIT。`LanguageWorker` 零 diff。IR-C2-1 两种时序读法与代码一致。 |
| `controller/track_loop.py` / `gated_publisher.py` / `language_bridge.py` / `pose_gmc.py` | `capture_hook` 为 None 时常驻路径逐字不变；`_capture_frame` 只对本批最新帧发布（B7），观测只在 OBSERVED、预测经 `predicted_look_at` 单列通道（IR-9，`RECEIPT_CHANNELS` 末尾追加）、`servo_clamp` 裁剪时 `note_control_limited`（C1-4）；`ACTIONS` 追加 `click`、`STATE_REASONS` 末尾追加恰 11 项（§3.6 十项 + IR-5）、`validate_click_fields`；`GMC_SOURCES` 后缀恰 `pose-center,pose-aabb`。 |
| `tools/eng_capture/replay.py` / `formal_run.py` / `baseline_runner.py` / `common.py` | S-A-INPUT 现算 sha + 帧时刻对齐；AC-27/AC-17/AC-28 启动前校验（样帧 sha 现核、红车 557、六基 k−1 帧 sha）；基线臂在导出 `$BASE:controller/` 上运行（F18 等价运行时核）；新臂 ① 点击先于 `on_frame`；`score_next_real_observation`/`score_injection` 按 AC-18 原文（原始检测、原键同帧 prior，IR-C2-5 多检测取 IoU 最大）；IR-8 注入经 `get_dists` 与 `_second_association` 包装、`force_new_track_report` 核真正换键；AC-19 口径冻结（H 映射真值多边形、<50% 删失、断轨/误跟/右删失、每格分母）；`CountingModel` 每帧提交前 `InflightCounter.add`（C1-5）。**缺陷**：S-A-INPUT 早退写盘不记账，见 R1-2。 |
| `tools/eng_capture/ledger.py`（新） | 整体校验（必需字段、非负整数、无 UNKNOWN、计数 = 事件和、零维度恒 0、无未结算 in_flight、候选 ≤ 上限）→ 候选归属 → 逐维余额；原子写；`record`/`InflightCounter.add` 越上限先拒。**缺口**：`problems`/`check_launch` 不核全部计数 ≤ 其上限（只核 `needs` 所列维度），见 R1-4（`SCOPE_GAP`）。 |
| `tools/eng_capture/analyze_play.py`（K4 Play 评分口径） | `per_frame_from_logs` 绑定键按 event_seq 归属（C1-3）、`score_prediction_windows` 与 AC-18 同口径（C1-2）、`velocity_only_on_supported`。**缺陷**：`click_latency` 按位置配对、`wall_s` 恒 None、`score_body_band` 缺真值 FOLLOW 帧计入带内且不出「非 FOLLOW 帧数」、`score_red_car_loop` 未限红车段，见 R1-3。 |
| `tools/eng_capture/click_web.py` / `tools/eng_loop2/operator_web.py` | 只监听 127.0.0.1、nonce + Host/Origin；浏览器实际解码字节算 sha；`click_received_unix_s` 与当刻 `latest.json` 先记；`InProcessSend` 退出码 0/2/4/5；`ClickArgv` 只组 click/stop；R1-5 子路径先内存 seal + `unknown[request_id]` 再写日志（记录器再抛不影响）；保真/六基登记模式不读真值、不叠框。`operator_web.py` diff 恰两处。 |
| `config/p1-eng-capture-001.json` | 14 参数逐值带 §3.7 类别，占位 T_report 3 / N_adopt 2 / ρ 1.5 / T_pred 4 / T_repair 5 过结构约束；`body_band_formula` 供 AC-25。 |
| `tests/`（10 件） | 全部注入替身/缓存，零真实加载；`TaskSpec*`/`Continuity*`/`Repair*`/`Commit*`/`Authorization*`/`Replay*`、`PredictionTests`/`ReportTests`/`StopTests`/`ClickTests`/`LanguageCompatTests`（对 `$BASE` 导出包逐帧比较）、`KfSnapshotTests`（真实钉版 BoT-SORT）、`NewArmEndToEndTests`（真实关联器 + 缓存检测）、`test_capture_isolation`（AST 真值 token、禁改路径 diff）、`test_capture_click_web`（四种退出码、两处 diff、R1-5 两条具名回归）。`ReplayTests` 只覆盖完整输入与「改一行 / 删引用」两类拒绝，未覆盖缺行/截断（R1-1）。 |
| 证据：`-K1K2K3K4-handoff.md` / `-replay.md` / `-tests.log` / `-focused.log` / `-ledger.json` / `-play-ops.md` / `-fidelity-confirmation.json` | AC 指针与真实测试名逐条对应；`-replay.md` §1–5 读数与 `replay-report.json` 口径一致（本轮未重跑回放，不复算读数）；play-ops 含 12 码、确认来源、B 维度 0。`-play-ops.md` §7 评分命令依赖 R1-3 修复。 |

### §2 AC 逐项（依据列 `BC-n` 读作 AC-n；「成立」= 代码与具名测试对应、本轮重跑通过）

| AC | 结论 | 核对 |
|---|---|---|
| AC-1 | 成立 | `ClassPolicyTests` 五例；缺省不变、冻结规格/权重零 diff、无 cls==1 决策。 |
| AC-2 | 成立 | `test_pose_center` 六例（H(中心)、宽高/宽高速度不变、J 变换、H=None、`pose`≡`pose-aabb` 逐元素）。 |
| AC-3（修订 1/2） | 成立 | `HistoryContractTests`/`KfSnapshotTests`/`BridgeIsolationTests`；C1-1 消费侧对齐已核（§1）。C2-P1 见 §4 O-1：不构成缺陷。 |
| AC-4 | 成立 | `TaskSpecTests`（不可变、合法形状、计数矩阵四 origin + release/teardown）。 |
| AC-5（修订 1/2） | 成立 | AST 静态检查 + `ContinuityTests`（#1 #2、1 帧回 SUPPORTED、prior 创新过大、IR-6 矩阵、C1-1 四例）。 |
| AC-6（修订 1/2） | 成立 | `RepairTests`（#3 #4、无键永不提交、门 0、累计 NIS 竞争、结构约束拒绝、C1-1 两例）。 |
| AC-7（修订 1/2） | 成立 | `CommitTests`（纯解析、半改恢复含非空 coasting、三种恢复失败 fail-closed、会话安全通道 hold、拒绝重选保旧目标、断链不补身份、成功后才关旧 episode、调用点闭集）。 |
| AC-8（修订 1/2） | 成立 | 2304 + 3072 格首命中与域分类、合法变差边 >500 对单调、D2 反例域外、候选观测不驱动云台。 |
| AC-9（修订 1） | 成立 | `PredictionTests`（行 7 预测 look_at + 显式 hold、提前恢复/协方差超限/DISPUTED/kf 无效/几何拒绝反例、C1-1 缺 prior 不发、P_center 与框底量测分离）。 |
| AC-10（修订 2） | 成立 | `ReportTests`（边界逐列、墙钟无关、积压不发命令）+ 桥闭集精确追加。 |
| AC-11（修订 1/2） | 成立 | `StopTests` + 回滚失败安全通道。 |
| AC-12（修订 1） | 成立 | `ClickTests`（sha/历史/歧义/链断/重选/compat 拒绝/受理子段/C1-3 追平顺序）。 |
| AC-13（修订 1/2/3） | 成立 | `LanguageOffTests` + `LanguageCompatTests` 七场景对 `$BASE` 导出包逐帧一致（含 IR-1 出画/退化/coasting）；`LanguageWorker` 逐字节同（本轮独立核）。 |
| AC-14 | 成立 | `test_capture_click_web` 13 例。 |
| AC-15 | **不成立**（R1-1） | 正常原件、篡改行、缺引用三类已证；缺行/截断不拒且伪造或洗白事件。 |
| AC-16 | 成立 | `test_capture_isolation` 六例；本轮 grep 复核。 |
| AC-17 | 成立（候选 2 已运行，PASS） | 评分器 `score_new_arm_window` 与 RR-1 用户答复一致（同帧同版本否则 `STATE_EFFECT_INCONSISTENT`）；读数本轮不复算。 |
| AC-18（修订 1） | 成立（九项 PASS） | C1-2 原检测判据与 IR-C2-5 读法已落代码；缺 prior 记 `original_key_same_frame_prior_missing` 的 NOT_EVALUABLE 与用户裁定「记证据缺失、不扩 NOT_EVALUABLE」在读数层等价（本次九项 prior 齐全、不影响读数）；见 CLASS_3 建议 §3 末。 |
| AC-19（修订 1） | 成立（六格非劣化） | 口径冻结在 `score_truth_geometry`/`score_roll_sequence`/`score_roll_cells`；选择输入只来自 AC-28 剧本。 |
| AC-20（修订 2/3） | 成立 | 全套 1/1 候选 2，62 条失败分列与本轮按模块重数一致，新增回归 0。 |
| AC-21 | 成立（草案） | 12 码、确认来源、B=0、§7 命令依赖 R1-3。 |
| AC-22 / AC-25（停点 `PlayK2K4`，本停点只核评分口径） | **口径不成立**（R1-3） | 见 §3。 |
| AC-27 / AC-28 | 成立 | 确认文件结构与账本一致；六基规则/登记页/启动校验/真值改变不改选择输入。 |
| AR1-6 共账 | **部分不成立**（R1-2、R1-4） | 逐帧共账与启动门成立；S-A-INPUT 写盘不记账；上限全维校验缺口。 |

### §3 Findings

| ID | CLASS | 依据 | 范围判据 | 标题 |
|---|---|---|---|---|
| R1-1 | CLASS_2 | BC-15 | 可达：生产入口（会话崩溃或中途退出留下的 `tm_inputs.jsonl` 前缀；任何缺行文件）能产生该状态，AC-15 点名「只读落盘输入与配置重放…篡改即拒」 | 重放对不完整输入不拒绝，缺行时伪造/洗白事件 |
| R1-2 | CLASS_2 | BC-20 | 可达：S-A-INPUT 是提案 §6 点名的 STOP 状态 | S-A-INPUT 早退路径写盘不记磁盘账（AR1-6 / AC-20/21 修订 1） |
| R1-3 | CLASS_2 | BC-22 | 可达：AC-22 原文把被拒点击列入分母；§7 停点 1 含「K4 回放与 Play 评分口径」 | `analyze_play` AC-22/23/25 评分口径缺陷 |
| R1-4 | CLASS_2 | SCOPE_GAP | 不可达：`record`/`InflightCounter.add` 自身越上限即拒，只有手改账本才会出现 | 启动门不核全部计数 ≤ 上限（非阻断，路由接受角色记债） |

**R1-1（CLASS_2，BC-15 = AC-15、AR1-2「只用落盘输入与配置重放…缺引用即拒」）。** `controller/target_manager.py::ReplayPort._next` 队列空时返回 None → `follow` 默认成功、`pointer`/`restore_binding_state`/`binding_state_matches` 退回本地模型；`replay_tm_inputs` 把文件内全部 `port` 行按调用种类预入队，不核每次端口调用都消费到一条记录、不核残留、不核调用顺序。副本内探针（生产路径夹具：真实 `TargetManager` + `ResidentCore`/测试模块 `_FaultyCore` 写出的日志，只删行或取字节前缀）：(A) 读回不符的回滚失败日志删去 `readback` 端口行 → 重放不拒绝，在线末事件 `commit rejected binding_rollback_failed`（fail-closed）被重放成 `follow_failed`（可恢复）——**失败路径被洗白**；(B) 捕获日志截断在点击请求行之后（崩溃前尚未写端口行）→ 重放不拒绝并发出 `binding_committed`——**伪造在线未必发生的绑定**；(C) 删去一条 `pointer` 行 → 不拒绝。AC-15 测试只覆盖「改一行」与「删 history 引用」两类拒绝；本缺陷使「篡改即拒」对删行/截断失效，也使 AC-7 失败路径的重放证明依赖输入完整这一未被机检的前提。**闭合要求**：`tests/test_target_manager.py::ReplayTests` 增具名回归（生产路径夹具 = 真实 reducer 写出的 `tm_inputs.jsonl`，再删任一 `port` 行 / 取到点击请求行的字节前缀）断言 `replay_tm_inputs` 抛 `ReplayRejected`（修前必失败）；实现方式由实现角色定（例如：端口记录单队列按序消费并核 `call` 一致、重放中每次端口调用必须消费到记录否则拒绝、结束时残留即拒；可选逐行链式 sha）。不得为通过而放宽既有 `test_rollback_failure_paths_replayed_in_new_process`。

**R1-2（CLASS_2，BC-20 = AC-20/21 修订 1 即终局裁定 AR1-6「零模型不等于零磁盘或零墙钟，写文件仍计对应阶段磁盘」）。** `tools/eng_capture/formal_run.py::run` 在 `check_input` 不通过时写 `input-check.json` 与 `replay-report.json` 到输出目录后 `return 3`，不记 `mini_new_disk_bytes`（正常路径与 S-A-REPRO 路径均记）。副本内探针（临时账本副本、`check_input` 打桩不通过、`frame_ids=[]`）：退出码 3、输出目录 466 B、账本磁盘事件 0 条。虽然字节很小，AR1-6 的义务是每条 STOP 收尾写入都入账、不留 UNKNOWN。**闭合要求**：`tests/test_capture_replay.py::LaunchGuardTests`（或 `BaselinePackageTests` 同夹具）增具名回归：`formal_run.run` 走 S-A-INPUT 早退后临时账本须含该输出目录实测字节的 `mini_new_disk_bytes` 事件（修前必失败）。非阻断附注（同一资源账区域，不单列 finding）：`CountingModel` 的 30 min 墙钟门只在每次 `predict` 前核，最后一次推理之后的评分/落盘阶段不受核（本次实测 146 s，余量充足）；实现角色可在收尾写报告前补一次墙钟判定，证据写明。

**R1-3（CLASS_2，BC-22 = AC-22；AC-23/AC-25 见正文）。** `tools/eng_capture/analyze_play.py`：(a) `click_latency` 把 `click_received`（点击页收到即记）与 `submit_begin` 按**数组位置**配对；`Submitter.submit` 在 `in_flight`/`sealed`/`binding_already_submitted`/`stop_already_sent` 时只记 `refused` 不记 `submit_begin`，因此一次被拒点击之后所有行错位。探针（一次被拒点击 + 一次提交成功且 e2e = 1 的点击）：第 1 行（被拒、无请求）被记上第 2 次的提交 `commit_head`、`e2e = 11 → FAIL`，第 2 行 `request_id None → FAIL`，总判 `FAIL`（真实应 1 行 FAIL（被拒）+ 1 行 PASS，总判 FAIL 虽同，但逐行读数与受理子段全错；若被拒点击发生在最后一次之后则会把 PASS 误记）。AC-22 原文「分母 = 全部发出的点击（含被拒…）」正是该状态。(b) `wall_s` 表达式两分支都是 None，合同要求「另记墙钟（描述）」从未落盘。(c) `score_body_band`：`inside = len(follow) − len(outside)` 把**无真值行**的 FOLLOW 帧计入带内（探针：10 帧有真值全在带内 + 10 帧无真值 → `in_band_fraction = 1.0`），且未输出 AC-25 要求的「非 FOLLOW 帧数」。(d) `score_red_car_loop` 对全部帧统计失观测/准时报告，未限定 AC-23「红车 ≥ 1 圈内」（S2 提交至 S4 首次点击），S1 静止车阶段的丢失会被算作 AC-23 失败（偏严但口径不符）。AC-22…25 的运行属停点 `PlayK2K4`（B 未签 = 0，均 `NOT_RUN`），本轮不改任何已报读数；但 §7 停点 1 把「K4 回放与 Play 评分口径」列入本停点，评分工具的口径缺陷在此阻断。**闭合要求**：`tests/test_capture_replay.py::AnalyzePlayTests` 增具名回归（夹具 = `ClickApp.click` + 真实 `Submitter`（`sealed`/`in_flight` 替身 CLI）写出的 `click-web.jsonl` 字节，或至少含一条 `refused` 且无 `submit_begin` 的真实记录器输出）断言被拒点击单独成行、其后点击按 `request_id` 正确配对且 `wall_s` 非 None；`score_body_band` 夹具含无真值 FOLLOW 帧 → 不计入带内并输出 `non_follow_frames`；`score_red_car_loop` 接受红车段 [S2 提交帧, S4 首次点击帧) 并只在段内统计（修前均必失败）。配对建议：`click_received` 行带 `request_id`（页面侧在 `Submitter.submit` 返回后补写）或以 `binding_key` 关联，不再按位置。

**R1-4（CLASS_2，`SCOPE_GAP`，非阻断；路由接受角色记入 `docs/implementation-status.md`「范围外已知缺陷」）。** `tools/eng_capture/ledger.py::problems`/`check_launch` 只核候选数 ≤ 上限与 `needs` 所列维度余额，不核每个计数 ≤ 其整批/每候选上限；一本已越界的账（例如 `stop_suite_runs = 4 > 3`）在只申请回放维度时仍能通过启动门。工具自身写路径（`record`、`InflightCounter.add`、`start_candidate`）越上限即拒，所以该状态只能由手改账本产生 → 不可达，记债不阻断。

**CLASS_3 建议（不阻断，由实现角色下次提交应用）**：`tools/eng_capture/replay.py::score_injection` docstring 与 `-replay.md` §4 判据句「原键在该帧无同帧 prior → NOT_EVALUABLE（不编造）」与用户 2026-10-10 裁定「缺原键 prior 记证据缺失，不扩 NOT_EVALUABLE、不从分母去掉」措辞不一致（本次九项 prior 齐全、读数不受影响；代码 `not_evaluable_reason = original_key_same_frame_prior_missing` 已把缺失单列）。逐字替换建议：`-replay.md` §4 第 44 行「无此检测或原键无同帧 prior → NOT_EVALUABLE（不编造）」→「无此检测 → NOT_EVALUABLE；原键无同帧 prior → 记证据缺失（`original_key_same_frame_prior_missing`，不从分母去掉、不计通过）」。代码 docstring 同句由实现角色按同义修改（复核不改 `tools/`）。

### §4 C2 关注项、IR 读法与其他核对

- **O-1（C2-P1 答复：不立 finding）**：`_assess_original` 对原键本帧非 tracked（lost/出画/removed/ended）早退、不运行 `same_frame_post`，`kf_ok` 只由同帧 prior 决定，`_miss_original` 据此以 prior 发预测。这与合同一致：AR1-2 修订 1「post 无效同样不授权」的句子紧随「接受原观测后 belief 可取该键的 post 快照」，限定在**接受原观测**（原键本帧匹配）的路径；lost 键在库内本帧无量测更新，其「更新后快照」按 §3.1/AR1-2 标 `prior`（`_post_snapshots` 实现、`KfSnapshotTests.test_new_key_unconfirmed_and_lost_post_is_prior` 已证），若对 lost 键也要求有效 `posterior`，行 7 预测在生产中永不可达，与 §3.3 边界表矛盾。真实关联器上 lost 键的「post（phase=prior）」与 prior 是同一 KF 状态的两次复制，不存在「有效 prior + 无效 post」的生产组合。原键本帧 tracked 而 post 无效 → `kf_ok=False`、不接受、无预测、HOLD（`test_c1_1_matched_original_with_invalid_or_missing_post_not_accepted` 四例 + 本轮代码读）。
- **C2-P2** → R1-1（阻断）。**C2-P3** → R1-2（阻断）+ R1-4（`SCOPE_GAP`）+ 墙钟附注。**C2-P4** → R1-3（阻断）。
- **IR-C2-1…5**：代码与接受裁定读法一致（追平路径 k 帧授权前提交、k 已处理时历史头提交且旧效果不改写；点击/修复 post 不合格拒绝/不提交零状态变化；未接受帧预测取原键同帧 prior；KF 不合格无几何中心 → 行 5 `GEO_REJECT`，几何有效而协方差 `kf_invalid` → 行 8；多检测取 IoU 最大）。IR-C2-5 的措辞差见 §3 CLASS_3。
- **AR1-2/3/6 具名缺口独立核实**：AR1-2（双阶段快照、同帧 prior 门、G 域与合法边、落盘输入重放）与 AR1-3（计数矩阵、两阶段分配、完整事务恢复）在代码与具名测试上成立；AR1-6（逐帧共账、启动门、尝试即记、磁盘实测）在正常路径成立，R1-2/R1-4 为其边界缺口。
- **UNITY_NA**：实现未申请、Gate board Unity 列 `NOT_RUN`；本轮**不附议任何 `UNITY_NA`**（阶段 A 零 Unity，AC-22…26 属 `PlayK2K4`，`DONE` 仍需 Unity/硬件证据）。
- **真值泄漏（RED_LINE 检查）**：`controller/`、`click_web.py` 无真值 token；`formal_run.py` 无 `score_click_point`，`roll_sequence` 的 `clicks` 只来自参数；真值只在 `score_` 函数；桥文件无内部字段（`BridgeIsolationTests`）。未见红线。
- **环境注记（非缺陷）**：`replay.check_input` 用 `resolve().relative_to(PROJECT_ROOT)` 计清单相对路径，准入根为符号链接时抛 `ValueError`（副本环境触发）；生产机 mini 为真实目录，不影响证据。
- **消耗性门机检**：本轮无 `上轮漏检` CLASS_2、无 `blocks_consuming_gate` 行；状态板当前 0 条消耗性交接。

### §5 Verdict

**`REWORK_REQUIRED`**（本停点第 1 次，1/2）。阻断 finding：R1-1、R1-2、R1-3（均 CLASS_2，直接交回实现角色，修复回本角色 `R2@K1K2K3K4`，不经核对轮；每条绑定上文具名回归，复核以修前红/修后绿核实）。R1-4 `SCOPE_GAP` 交接受角色记债，不阻断。CLASS_3 一条由拥有写权限的角色下次提交应用。本轮不写 `passed_candidate`。

收工边界自查：本会话未修改 `controller/`、`Assets/`、`tools/`、`tests/`、`config/` 任一文件；副本已 `git worktree remove --force`；主工作树改动仅 `docs/reviews/P1-ENG-CAPTURE-001.md` 与 `docs/current-status.md`。

## R2@K1K2K3K4（2026-10-10）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-CAPTURE-001-R2@K1K2K3K4-20261010T185824Z-423b`，`requested.round = R2@K1K2K3K4`）。零消耗：零 ID、零 Unity/Play、零模型加载/构造/推理、零回放、零全套；只在一次性副本接触实现代码，本会话未修改任何实现文件（§5 边界自查）。

### §0 候选、基线、开轮资格与重跑

- `round_candidate: 1cb45baea6ef2b28381d3ea3d08314594ce0d7b4`（派发指定；`origin/main` 祖先；代码/测试冻结于其父 `ddaf982`（主题「R1返工 候选3代码」），`ddaf982..1cb45ba` 于 PLAY_GOVERNING 零 diff）。
- 开轮资格：本文件无 `passed_candidate`，全量基线仍为 `$BASE` = `accepted_base_commit()` = `9f1a8cc…`；`git diff $BASE..1cb45ba -- controller tools tests config` = 29 文件 +10408/−85（非空 → 开轮）；`Assets/`、`ProjectSettings/`、`Packages/packages-lock.json`、`config/scenario.default.json` 零 diff。增量轮：修复触及行 = `git diff e22d75d..1cb45ba`（上轮 §0 `round_candidate`）于 PLAY_GOVERNING = **7 文件 +521/−83**：`controller/target_manager.py`（+104/−）、`tools/eng_capture/{analyze_play,click_web,formal_run,replay}.py`、`tests/{test_target_manager,test_capture_replay}.py`；与交接 §R1 声明闭集逐字一致，`resident_core`/`det_assoc_tracker`/`track_loop`/`language_loop`/`ledger`/`baseline_runner`/`operator_web`/配置零 diff（AC-13 `LanguageWorker`、AC-14 两处闭集、AC-16 禁改路径因此不变）。
- 停点自证（交接 §R6）四项成立：①冻结（上句）；②全套 1 次（`-tests.log`：Ran 2666 / F28 / E34 / S56，墙钟 557.70 s；`FAIL:`/`ERROR:` 头 62 条排序后与候选 2 日志（`git show e22d75d:…-tests.log`）**逐条相同**，本轮独立 diff 为空 → 新增回归 0）+ 三条阻断 finding 具名红绿；③不适用（阶段 A 零 Unity，不记 `UNITY_NA`）；④齐备。**不给 `REVIEW_BLOCKED`，开轮。**
- 副本 detach 于候选；树哈希 `HEAD:tests = 0db1abae8efefbf72a1fa724e954cb54d889cabf`、`HEAD:controller = b820e2b8369d77619ebacf706a44fa941b5aeb6b`、`HEAD:tools = e4286d4f772403f05620869bcdb6f3c6a37a9bca`、`HEAD:config = 8bb9f62bd594fa57f36af90a9a9fd57fa8cb875c`。解释器 mini `.venv-yoloe/bin/python` 3.12.14，进程设 `YOLO_OFFLINE=True YOLO_AUTOINSTALL=False`；副本 `outputs/{eng-det,eng-loop,eng-capture}` 为指回主树的只读符号链接。
- **focused 重跑**（副本内 `-m unittest discover -s tests -p <模块>.py`，与 R1 同 19 模块，输出写会话暂存目录、只回显摘要）：`test_language_loop` 205 OK、`test_language_bridge` 50 OK、`test_target_manager` **47** OK（R1 为 44，+3 = R1-1 具名回归）、`test_capture_session` 26 OK、`test_capture_click_web` 13 OK、`test_capture_replay` **44** → 43 OK + 1 ERROR（同 R1：`AdmittedInputTests.test_check_input_matches_sums_and_alignment` 的 `resolve().relative_to(PROJECT_ROOT)` 在符号链接副本抛 `ValueError`，副本环境产物、非候选缺陷）、`test_capture_isolation` 6 OK、`test_pose_center` 6 OK、`test_pose_gmc` 8 OK、`test_resident_core` 37 OK、`test_det_assoc_tracker` 37 OK、`test_gated_publisher_slew` 3 OK、`test_track_loop` 27（1 FAIL = 基线 CSRT）、`test_eng_acq_e1` 17 OK、`test_eng_loop2_operator_web` 31 OK、`test_eng_loop2_analyze` 63 OK、`test_loop2_isolation` 10 OK、`test_loop2_freeze` 3（1 FAIL = IR-2 合同预期）、`test_frame_follow_replay` 19 OK。非 OK 三条与 R1 完全相同，无新增。
- **R1-1…R1-3 具名回归修前红/修后绿（本轮独立核实）**：副本内 `git checkout e22d75d -- controller/target_manager.py tools/eng_capture/{formal_run,analyze_play,click_web,replay}.py`（候选 2 代码，测试留候选 3）→ `test_target_manager -k r1_1`：Ran 3，**FAILED (failures=47)**；`test_capture_replay -k r1_ -k ir_c2_5`：Ran 7，**FAILED (failures=4, errors=3)**，七条具名用例（`test_r1_2_input_stop_records_output_disk_bytes`、`test_r1_2_final_wall_clock_judged_before_report`、`test_r1_3_refused_click_is_its_own_row_and_later_clicks_pair_by_request`、`test_r1_3_red_car_loop_counts_only_the_red_car_segment`、`test_r1_3_body_band_missing_truth_not_in_band_and_non_follow_counted`、`test_ir_c2_5_injection_missing_original_prior_is_evidence_missing`、`test_ir_c2_5_prediction_window_missing_prior_stays_in_denominator`）全部红；`git checkout HEAD -- <同 5 文件>` 复原（`git diff HEAD` 零行）→ 两组均 OK（3/3、7/7）。与 `-focused.log`「R1返工」红绿数字一致。
- **§R3「不重跑正式回放」零模型核验（本轮独立复算）**：候选 2 正式回放工件 `outputs/eng-capture/replay/candidate2-20261010T024317Z/new-arm-tm_inputs.jsonl`（sha256 前缀 `709756a3`，829 frame + 2 request + 4 port 行）在候选 2 代码与候选 3 代码下 `python -m controller.target_manager replay … config/p1-eng-capture-001.json` 均退出 0、837 行，两份输出 `cmp` **逐字节相同**（sha256 前缀 `09d0e9fbed908caa705b`）。结合修复触及行逐项读码（在线 `_record_port`/`commit_binding`/`_rollback`/`_release` 零改动；`formal_run` 只改两条 STOP 分支与写报告前 `wall_clock`/退出码；`replay.score_injection` 只改原键无 prior 分支，候选 2 九项 `iou` 非空未取该分支；`analyze_play`/`click_web` 正式回放不导入），**附议 §R3：候选 3 不重跑正式回放，AC-17/18/19 读数仍以候选 2 运行为准、不称候选 3 产物。**
- 本轮磁盘（用户 2026-10-10 裁定临时工作区实测记账）：一次性副本检出峰值 **80,961,536 B**（`du -sk`，不含符号链接目标；收工已删除，净新增 0）；会话暂存目录 **17,797,120 B**（focused/红绿日志、两份重放输出、探针脚本与探针产物）。本角色无 `docs/evidence/` 写权限，账本补记由接受/实现角色按此读数处理。

### §1 修复触及行逐文件核对

| 文件 | 结论 |
|---|---|
| `controller/target_manager.py`（R1-1） | `ReplayInputIncomplete(ReplayRejected)`；`ReplayPort` 由「按种类分队列、缺行默认成功/退回本地模型」改为单段按序消费：`begin_segment`（未知 call 即拒）、`_next` 要求段首记录种类相同否则记违例并抛、`end_segment` 段内残留即违例且违例非空即抛；`follow`/`pointer`/`restore_binding_state`/`binding_state_matches` 不再有默认分支；删除未用 `scripted`/`load`（仓内无其他调用者，grep 核）。`replay_tm_inputs` 把每条 `port` 行归属其前最近一条非端口行（init 后直接出现端口行即拒），处理每条输入行前 `begin_segment`、行末 `end_segment`。**在线不变量独立核**：`_record_port` 只在 `commit_binding`（先写 `commit_request`/点击 `request` 或处于帧行处理内）、`_rollback`、`_release`（先写 `release` 行）与 `_read_pointer` 内调用，在线路径零 diff，故端口行必紧随其触发输入行。**吞异常路径核**：`_next` 抛出的 `ReplayInputIncomplete` 在 `commit_binding`/`_rollback` 的 `except Exception` 被吞后，后续端口调用继续记违例，行末 `end_segment` 仍抛 → 不会被洗成 `follow_failed`/`binding_committed`（探针：候选 2 工件删任一 `request` 行 → `2 unconsumed port record(s)` 拒绝）。在线写盘格式零改动，候选 2 生产工件重放逐字节相同（§0）。残留边界见 R2-2。 |
| `tools/eng_capture/formal_run.py`（R1-2 + 墙钟附注） | S-A-INPUT 早退在写完 `input-check.json`/`replay-report.json` 后 `record_ledger("mini_new_disk_bytes", output_bytes(output), candidate, …)` 再 `return 3`（`ledger.record` 先核候选归属与上限、原子写）；`final_wall_check` 写 `report["wall_clock"]`、超限写 `budget_deviation`，S-A-REPRO 与正常路径写报告前各判一次，正常路径超限退出码 6、不改读数。非阻断注记：若 `record_ledger` 因磁盘越上限抛 `LedgerRefused`，文件已写、异常上抛（fail-closed 可见，不静默）。 |
| `tools/eng_capture/analyze_play.py`（R1-3 (a)–(d) + IR-C2-5） | (a) `click_latency` 以 `click_id` 配对（`click_submitted` → 退 `submit_begin`/`refused` 的 `binding.click_id`），`click_refused`（页面拒收）计入分母、被拒行 `request_id=None`/`refused=True`/FAIL；(b) `wall_s` = `binding_committed.at_unix_s − click_received_unix_s`（会话日志 `_journal` 每条带 `at_unix_s`，本轮核）；(c) `score_body_band` 缺真值 FOLLOW 帧单列 `follow_frames_without_truth`、不计带内、保持项 `EVIDENCE_MISSING`，`non_follow_frames` 取授权非 FOLLOW 帧，S2 帧无真值整项 `EVIDENCE_MISSING`；(d) `score_red_car_loop(…, segment=)` 只统计段内、段末未结束失观测 `ended_at=None` 与段外截止记 None，`red_car_segment_start` 取 S2 提交事件后首个授权帧（IR-C2-1 口径）；`main` 以 `[red_car_segment_start, S4 首次点击帧)` 调用。AC-24 缺原键 prior → `EVIDENCE_MISSING` 留在分母、总判不为 PASS。真值仍只进 `score_`（`red_car_segment_start` 无真值）。**缺陷**：`main`/操作单只评 S2→S4 首次点击一段，AC-23「换回红车后」段不再被评，见 R2-1。 |
| `tools/eng_capture/click_web.py` | `click_id` 写进 `click_received`/`click_refused`/提交 `binding`（`Submitter.submit` 的 `submit_begin`/`refused`/`submit_result` 均落 `binding`，本轮读 `operator_web.py:583–` 核），提交返回后补 `click_submitted`；`binding_key = click:<click_id>`（仍每次唯一）；argv 不变（`test_capture_click_web` 13 例过）；无真值 token。 |
| `tools/eng_capture/replay.py` | 只改 docstring 与 `score_injection` 原键无 prior 分支 `verdict = EVIDENCE_MISSING`（原因码不变）；其余零 diff。 |
| `tests/test_target_manager.py` | `ReplayTests.production_logs`：真实 `TargetManager` + `_FaultyCore` 在线写出 5 份 `tm_inputs.jsonl`（完整脚本 + 四种回滚失败），先核原件可重放；三条 `test_r1_1_*`：逐删每条 `port` 行（42 子例，>10）、受理点击请求行为止前缀与读回行前前缀、相邻异种端口行交换/重复 → 均断言 `ReplayRejected`。夹具为生产路径（真实写盘函数），断言修前失败（§0）。 |
| `tests/test_capture_replay.py` | `LaunchGuardTests.test_r1_2_*`：真实 `formal_run.run` + 临时账本副本 + `check_input` 打桩，加载器被调即断言失败，断言账本恰一条磁盘事件 = `output_bytes` 实测；`AnalyzePlayTests.test_r1_3_*`：生产 `ClickApp` + 真实 `Submitter` + `InProcessSend` 进真实 `LanguageSession`（`CaptureHarness`，替身常驻追踪器）写出的点击日志/会话日志/tm_inputs；`_two_car_session` S1 点静止车、S2 点红车；`test_ir_c2_5_*` 两例。唯一既有夹具改动 `test_click_latency_counts_every_click` 补 `click_id`，断言不变（diff 核）。 |
| 证据 | `-replay.md` §4 判据句已按 R1 CLASS_3 逐字替换、文首加「候选 3 未重跑」；`-play-ops.md` §7 加点击序号核定与红车段说明（但见 R2-1）；`-ledger.json` 15 维计数 = 事件和、无 in_flight、候选 3/3、全套 {1,2,3} 各 1 = 3/3、构造 6/6、加载 {1: 2, 2: 1}、推理 {1: 3962, 2: 3962}、磁盘 169,971,064 B（候选 2 名下含 R1 副本峰值 81,477,632 + 暂存 27,131,904 + git 对象）；`-focused.log`「R1返工」三节数字与本轮红绿一致。 |

### §2 R1 finding 闭合与 AC 变化

| 项 | 结论 |
|---|---|
| R1-1（BC-15） | **闭合**：具名回归修前 47 红 / 修后绿；候选 2 生产工件不误拒；吞异常路径不洗白（§1）。 |
| R1-2（BC-20） | **闭合**：`test_r1_2_input_stop_records_output_disk_bytes` 修前红 / 修后绿；墙钟附注已补（非闭合件）。 |
| R1-3（BC-22；AC-23/25） | **(a)(b)(c) 闭合，(d) 按 R1 闭合要求字面闭合**（段 [S2 提交后首个授权帧, S4 首次点击帧)、`test_r1_3_red_car_loop_counts_only_the_red_car_segment` 修前红 / 修后绿）；但 R1 闭合要求只写了「红车 ≥ 1 圈内」一段，漏写 AC-23 同条「换回红车后转向不丢，或在窗口内修复/报告」段，修复按字面收窄后该段读数消失 → 新 finding R2-1（R1 闭合要求不完整，责在本角色上轮）。 |
| R1-4（`SCOPE_GAP`） | 未修，已由接受角色记债（`docs/implementation-status.md`，候选之后提交 `1c6d6f4`），本轮不再核。 |
| CLASS_3（R1） | 已应用（`-replay.md` §4、`score_injection` docstring）。 |
| AC-15（修订 1） | 成立（删端口行/截断/乱序/重复即拒；残留见 R2-2）。 |
| AC-20（修订 2/3） | 成立（候选 3 全套 1/1，失败集与候选 2 逐条相同，本轮独立 diff 核）。 |
| AC-22 / AC-24 / AC-25 口径 | 成立（(a)(b)(c) 与 IR-C2-5 落代码；运行仍 `NOT_RUN`，属 `PlayK2K4`）。 |
| AC-23 口径 | **不成立**（R2-1）。 |
| AC-21 | 草案；§7 评分命令与 R2-1 同一缺口。 |
| AR1-6 共账 | 成立（S-A-INPUT 收尾入账；写报告前墙钟判定）。 |
| 其余 AC-1…14、16…19、27、28 | 相关代码本轮零 diff，R1 结论不变；AC-17/18/19 读数沿用候选 2（§0 附议）。 |

### §3 Findings

| ID | CLASS | 依据 | 范围判据 | 标题 |
|---|---|---|---|---|
| R2-1 | CLASS_2 | BC-23 | 可达：AC-23 原文与操作单 §4 S4 行点名「换回红车后转向不丢，或在窗口内修复/报告」；修复触及行（`analyze_play.main` 段选择、`-play-ops.md` §7） | AC-23 评分只取 S2→S4 首次点击一段，S4 换回红车后的段不再被评 |
| R2-2 | CLASS_2 | SCOPE_GAP | 不可达：删去无端口记录的中间输入行只能由手改文件产生（追加写盘崩溃只产生前缀，前缀已拒） | 重放对删去无端口调用的非端口输入行（如 frame 行）不拒绝 |

**R2-1（CLASS_2，BC-23 = AC-23）。** `tools/eng_capture/analyze_play.py::main` 只以 `segment=(red_car_segment_start(S2), S4 首次点击帧)` 调用一次 `score_red_car_loop`，`-play-ops.md` §7 也只给这一次调用；修前（候选 2）全程统计虽混入 S1 静止车帧，S4 之后的失观测仍在 `losses`/`all_losses_on_time` 内，修后被 `inside` 过滤排除（docstring 明写「S4 之后…不计入」），AC-23「S4 两次换目标…换回红车后转向不丢，或在窗口内修复/报告」从此没有任何工具读数，操作单 §4 S4 行却仍把它列为读数。`score_red_car_loop` 函数本身已支持任意段，缺的是 `main`/操作单对换回段的调用。**闭合要求（二选一，由接受角色在冻结集裁定时指定）**：(i) 代码闭合——`main` 增换回红车点击序号参数（或由点击行自动取 S4 第二次已绑定点击），`AC-23` 输出含两段（`red_car_loop` 与 `after_s4_return`，后者段 = [换回提交后首个授权帧, 会话末)），`tests/test_capture_replay.py::AnalyzePlayTests` 增具名回归（夹具沿 `_two_car_session` 再点静止车、再点回红车的生产会话日志）断言换回段内失观测被统计、段外不计（修前必失败）；PLAY_GOVERNING diff 非空 → 轮 3 终局。(ii) `NOT_MECHANIZABLE` 操作单闭合——`-play-ops.md` §7 增第二次调用 `--s2-click <换回红车且被绑定的点击序号>`（不带 `--s4-click`）取其输出 `AC-23` 作换回段读数（该次输出的 AC-25 不采用），并写明 AC-23 结论 = 两段同时成立；操作单不在本 work item 冻结集、非 PLAY_GOVERNING，不开新轮，闭合改本文件「回归核实」小节定点复看 §7 具名行。两种方式均不改任何已报读数（AC-22…25 仍 `NOT_RUN`）。

**R2-2（CLASS_2，`SCOPE_GAP`，非阻断；路由接受角色记入 `docs/implementation-status.md`「范围外已知缺陷」）。** 行 sha 只覆盖本行，输入行之间无链式引用；探针（候选 2 生产工件，删去一条其后无端口行的 `frame` 行，行 418 / 行 834）→ 重放不拒绝、事件 836 条（原件 837），事件序列静默分叉。交接 §R5 已如实披露；R1-1 闭合要求只约束端口行与截断，本轮按字面已闭。AC-15 原文「篡改任一输入行 → 行 sha 校验失败」字面指改行，删行不在其列，而生产入口（追加写盘）只能产生前缀，故按 R1-4 同一判据记为不可达；接受角色若按 AC-15/AR1-2「缺引用即拒」判为范围内，则改「范围内必修」（可选闭合：行记录带前一行 sha 的链式引用，或 frame 行号连续性核）。

**CLASS_3 建议（不阻断，由拥有写权限的角色下次提交应用）**：`docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` §R2 IR-R1-2 句「未给 S4 时保持窗到最后一个已授权帧（修前到最大真值帧且不含该帧）」与代码 `end = max([*authorized, *truth]) + 1` 不一致（`hold_window` 末值为二者最大值 +1；因 FOLLOW/授权帧 ⊆ 授权帧，读数不受影响）。逐字替换为：「未给 S4 时保持窗至 max(最后一个已授权帧, 最大真值帧) 为止（含该帧；`hold_window` 末值记其 +1），修前到最大真值帧且不含该帧」。

### §4 实现读法 IR-R1-1…5、UNITY_NA 与其他核对

- **IR-R1-1…5（交接 §R2；实现角色无提案写权，待接受角色裁定，本轮只核代码与读法一致并给意见）**：IR-R1-1 红车段起点取 S2 提交后首个授权帧——代码 `red_car_segment_start` 与之一致，且与已裁定 IR-C2-1「k 已处理时提交帧已发效果属旧绑定」同口径，**附议**；IR-R1-2 缺真值 FOLLOW 帧 `EVIDENCE_MISSING`、不从分母去掉——与用户 IR-C2-5 裁定同原则，**附议**（措辞差见 CLASS_3）；IR-R1-3 页面拒收的畸形点击（`click_refused`，未发送）计入 AC-22 分母——AC-22 原文「全部发出的点击（含被拒…）」字面是「发出」，畸形点击未发出，本读法偏严（只多记 FAIL、不可能多记 PASS），**可接受但须裁定**；IR-R1-4 `EVIDENCE_MISSING` 为新判定值、AC-17 R-1 暂定读数只计 PASS/FAIL——与 IR-C2-5 裁定一致，**附议**；IR-R1-5 段末未结束失观测的段外截止记 None、不判——与 (d) 段语义自洽，**附议**，但与 R2-1 一并看：换回段以会话末为段末时「不判」只覆盖截止落在会话结束之后的失观测。
- **UNITY_NA**：实现未申请，Gate board Unity 列 `NOT_RUN`；本轮**不附议任何 `UNITY_NA`**。
- **真值泄漏（RED_LINE）**：修复触及行中 `controller/`、`click_web.py`、`red_car_segment_start`、`click_latency`、`final_wall_check` 均无真值 token（`test_capture_isolation` 6 例过 + 本轮 diff 读）；真值仍只进 `score_` 函数。未见红线。
- **消耗性门机检**：本轮无 `上轮漏检` CLASS_2、无 `blocks_consuming_gate` 行；状态板 0 条消耗性交接；R2-2 走 `SCOPE_GAP` 账本路径。
- **信封注记（非 finding）**：CAPTURE:A:1 停点全套 3/3、构造 6/6、候选 3/3 已用尽；R2-1 若走 (i) 代码闭合，新候选与全套均无额度（engineering-workflow §6 窄修通道以「不触及对外指标路径」为前提，`analyze_play` 属 K4 Play 指标路径，是否适用由接受角色裁定，否则回用户）；走 (ii) 不耗任何额度、不开新轮。

### §5 Verdict

**`REWORK_REQUIRED`**（本停点第 2 次，2/2 → 未闭 finding 集**冻结** = {R2-1}，交接受角色逐条裁定「范围内必修」或 `SCOPE_GAP`，并指定 R2-1 闭合路径 (i)/(ii) 与 IR-R1-1…5 读法；R2-2 `SCOPE_GAP` 记债）。R1-1、R1-2、R1-3 已闭合（修前红/修后绿本轮独立核实）。轮 3 终局：通过，或回用户；(ii) 路径无 PLAY_GOVERNING diff 时不开轮 3，按 workflow §4.4 阻断 finding 回归通道在本文件「回归核实」小节定点复看后写终局 verdict。本轮不写 `passed_candidate`。

收工边界自查：本会话未修改 `controller/`、`Assets/`、`tools/`、`tests/`、`config/` 任一文件（副本内红绿检出已 `git checkout HEAD --` 逐字节复原，`git diff HEAD` 零行后删除副本）；副本已 `git worktree remove --force`；主工作树改动仅 `docs/reviews/P1-ENG-CAPTURE-001.md` 与 `docs/current-status.md`。

## 回归核实（2026-10-10；冻结集 {R2-1} 路径 (ii) `NOT_MECHANIZABLE` 定点复看，不新编轮号）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-CAPTURE-001-R2回归核实-20261010T192959Z-66fa`，`requested.round = R2回归核实`）。依据：workflow §4.4「阻断 finding 的闭合」(4) 与 D2b 无资格路径（本小节 = 原复核文件「回归核实」），同名提案「Contract conformance」之「R2冻结裁定」（冻结集 {R2-1}、唯一路径 (ii)）与「IR-R1-3答复落实」（AC-22 修订 1、文档任务清单），账本 2026-10-10「用户答 IR-R1-3」。零消耗：零 ID、零 Unity/Play、零模型、零评分/重放、零测试（NOT_MECHANIZABLE 定点复看，不开轮、不跑评分）；只在一次性副本读实现代码核对操作单字段名/CLI 参数，本会话未修改任何实现文件（§5 边界自查）。

### §0 候选、范围与开轮资格

- 复看对象：`4d9418722173113329f1e6c5348bcc421ad0a860`（派发指定；`origin/main` 祖先；主题「R2文档闭合 …」）。相对其父 `d8ca5d5` 只改 4 个文件：`-play-ops.md`（+32/−2）、`-K1K2K3K4-handoff.md`（+51/−2）、`-ledger.json`（+42/−1）、`docs/current-status.md`（+4/−3）。
- PLAY_GOVERNING：`git diff ddaf982..4d94187 -- controller tools tests config Assets ProjectSettings Packages` **为空**；副本树哈希 `HEAD:tests = 0db1abae…`、`HEAD:controller = b820e2b8…`、`HEAD:tools = e4286d4f…`、`HEAD:config = 8bb9f62b…` 与 R2 §0 逐字相同 → 代码仍是候选 3，操作单不在冻结文件集（裁定 (ii)-4）→ **不开轮 3，不写 `round_candidate`**，按 §4.4 回归通道在本小节定点复看。
- 实际改动闭集与裁定允许路径（操作单 §7、handoff §R2/§R7、账本、状态板）逐字一致，未超出 → 不触发「停报、重新按开轮资格处理」。

### §1 具名行定点复看（修前 = `d8ca5d5:-play-ops.md` §7；修后 = 候选 §7.1–7.4；字段名/CLI 以副本 `tools/eng_capture/analyze_play.py::click_latency/red_car_segment_start/score_red_car_loop/main`、`click_web.py::ClickApp.click` 只读核）

| 裁定条 | 修前 | 修后 | 结论 |
|---|---|---|---|
| (ii)-1 第一调用 = S2 红车段至 S4 首次点击前；按实际行序核序号、不硬填、不由序号推身份 | 一次调用、硬填 `--s2-click 2 --s4-click 3` | §7.1 第一调用占位 `<S2序号>`/`<S4首次序号>`；§7.2 第 1 条只读列行命令（过滤 `kind ∈ {click_received, click_refused}`、1 起，与 `click_latency` 的 `received` 列表同过滤同顺序，`rows[*].index = i+1`）；§7.2 第 2 条身份/绑定从现场记录与 `AC-22.rows[*].bound`/`commit_event_seq`、会话日志 `binding_committed` 核实 | 成立 |
| (ii)-2 第二调用：同 session-dir/click-log/truth，`--s2-click <换回且已绑定序号>`，不带 `--s4-click`，另存；取其 `AC-23`，起点 = 换回提交后首个新绑定授权帧，至会话末；未绑定/无授权帧/缺日志不算通过 | **缺**（只评一段） | §7.1 第二调用（三输入同、无 `--s4-click`、`play-readings-return.json`）；§7.3 第 2 条段 = [换回提交后首个新绑定授权帧, 会话末)；第 4 条 `verdict = NOT_EVALUABLE`/`reason = S2 not bound`、`frames_in_segment = 0`、缺日志均不作通过。代码核：`--s4-click` `default=None` → `s4 = None` → `score_red_car_loop(segment=(red_car_segment_start(…commit_event_seq), None))`，`inside` 末端不限、`segment: [first, null]`；起点按 event_seq > 提交事件（IR-R1-1 裁定） | 成立 |
| (ii)-3 AC-23 两段与原合同其余读数同时成立、缺段不以首段代替；第二调用 AC-25 不采用；AC-22 不重复计 | **缺**（「AC-23 只在红车段…内统计」） | §7.3 第 1、3、4、5 条；读数键 `losses`/`ended_at = null`/`all_losses_on_time`/`supported_frames_not_red_car_count` 与代码输出键逐字一致；IR-R1-5 段末未结束失观测截止在段内未发生记不准时、段外记 `None` 与代码 `report_on_time = (report_frame in reports) if report_frame <= last else None` 一致 | 成立 |
| (ii)-4 只写未来操作、不执行 | — | §7 文首注「本次未执行任何评分、重放或 Play，B 未签 = 0」；handoff §R7.4 未执行声明 | 成立 |
| IR-R1-3答复落实 1–4（工具读数与合同分母分列；仅剔 `click_refused` 且 `reason = malformed_click`；合同分母 = 工具行数 − 畸形行数；PASS/FAIL/NOT_EVALUABLE/EVIDENCE_MISSING 规则；序号不重编号；不能分列即停报） | **缺** | §7.4 第 1–4 条、§7.2 第 2 条。代码核：`click_refused` 仅在 `ClickApp.click` 畸形分支写出（`reason="malformed_click"`，提交器调用前返回），`click_latency` 对其记 `refused=True`/`request_id=None`/`verdict=FAIL`；输出键 `denominator`/`verdict`/`acceptance_subsegment_all_le_1`/`rows[*].{index,click_id,request_id,refused,refused_reason,bound,e2e_frames,acceptance_subsegment_frames,wall_s}` 与 §7.4 引用逐字一致；行判定 `PASS` = 已绑定且 `e2e ≤ 1` 与 §7.4 第 3 条同口径 | 成立 |
| CLASS_3（R2 §3，IR-R1-2） | 「保持窗到最后一个已授权帧」 | handoff §R2 IR-R1-2 末句与 R2 §3 逐字替换文本逐字相同 | 已应用 |
| IR-R1-3 承接注 | 扩大分母读法未标承接 | handoff §R2 IR-R1-3 句首〔R2文档闭合注〕指向「IR-R1-3答复落实」与 §7.4，原文保留为当时读法 | 成立 |

非 finding 观察（不改任何数字/判据，不设义务）：§7.2 第 2 条「`<换回序号>` = S4 点回红车的那次点击」未重复 §7.1 注释的「且已绑定」，但同条已要求从提交/授权日志核实绑定事实、§7.3 第 4 条已把未绑定排除在通过之外，操作员行为不因此不同。

### §2 资源补记核对（账本末 5 笔；handoff §R7.3）

- 账本整体：`counters` 全部 15 维 = 事件和（本轮独立重算，差异 0）；无 `in_flight`；`mini_new_disk_bytes` 事件 16 条、无重复金额；末 5 笔和 105,264,875 B，累计 275,235,939 B，与 R2 §1 所记 169,971,064 B 之差恰为末 5 笔和；`python -m tools.eng_capture.ledger check --candidate 3`（只读、零需求）无 problems。
- 第 1/2 笔 80,961,536 / 17,797,120 B = 本文件 R2 §0 原读数，逐字相同；`scratchpad/r2` 现存 15,610,374 B（本轮 `stat` 实测）≤ 第 2 笔，按复核读数计成立。
- 第 3 笔：`git rev-list --objects ddaf982..d8ca5d5 | git cat-file --batch-check='%(objectsize:disk)'` 本轮重算 = **16 提交 / 90 对象 / 4,637,031 B**，与账本逐字相同。
- 第 4 笔 1,851,741 B：具名项本轮实测 `acc-r14` 292,745 + `acc-r2f` 777,319 + `acc-ir13` 766,587 + 两份派发提示 10,364 + 4,179 + 任务输出 66 = 1,851,260 B，账本多记 481 B（`find -newermt` 时点差，偏保守），不构成缺口。
- 第 5 笔 17,447 B（上界）：本轮实测文档增量 `-play-ops.md` 4,443 + handoff 7,590 + `current-status.md` 485 = 12,518 B、账本文件增量 3,311 B，合计 15,829 B ≤ 17,447 B，上界成立（handoff 较账本注多 11 B 为 §R7.3 回填，已在上界内）。
- 未知项如实保留（codex 进程 `~/.codex/` 缓存、收尾提交 git 对象），未假记 0。账内 `mini_new_disk_bytes_total` 3 GiB 字段不构成超出用户 3 GB 授权，handoff 已写明。

### §3 Findings

无新 finding（冻结集路径 (ii) 的复看范围 = 具名行 + `RED_LINE`；修复触及行全为文档，无 CLASS_1/2）。R1-4、R2-2 `SCOPE_GAP`/OPEN 保持，不签 release；无 `blocks_consuming_gate` 行、状态板 0 条消耗性交接。

### §4 UNITY_NA 与红线

- **UNITY_NA**：实现未申请，Gate board Unity 列 `NOT_RUN`；本次**不附议任何 `UNITY_NA`**（AC-22…26 属 `PlayK2K4`，B 未签 = 0）。
- **真值泄漏（RED_LINE）**：操作单 §7 真值只作 `analyze_play --truth` 输入（代码内只进 `score_` 函数，R2 §4 已核、代码零 diff）；§7.2 列行命令只读点击日志；handoff/账本不含真值。未见红线。

### §5 终局 Verdict

**`PASS`**：冻结集 {R2-1} 按裁定路径 (ii) 闭合（修前缺换回段 → 修后两段齐备、AC-22 合同分母与工具读数分列）；R1-1、R1-2、R1-3 已于 R2 红绿闭合；R2-2、R1-4 为 `SCOPE_GAP` 记债不阻断；无 `RED_LINE`、无未 release 的 `blocks_consuming_gate`。本停点 `K1K2K3K4` 复核终局通过，交接受角色消费放行（AC-22…26 仍 `NOT_RUN`、B 未签 0、Unity `NOT_RUN`；**不是 `DONE`**，阶段 B 及 Play 仍需用户另签）。

passed_candidate: 4d9418722173113329f1e6c5348bcc421ad0a860

（代码 = 候选 3，`ddaf982..4d94187` 于 PLAY_GOVERNING 零 diff；该提交同时含操作单 §7.1–7.4，故以其为通过指针。）

本轮磁盘（用户 2026-10-10 裁定临时工作区实测记账）：一次性副本检出峰值 **81,022,976 B**（`du -sk`，未建符号链接；收工已删除，净新增 0）；会话暂存目录新增 0 B（本轮未写暂存文件）；本文件与状态板增量见下一轮补记。本角色无 `docs/evidence/` 写权限，账本补记由接受/实现角色按此读数处理。

收工边界自查：本会话未修改 `controller/`、`Assets/`、`tools/`、`tests/`、`config/` 任一文件；副本只读、`git status --porcelain` 为空后已 `git worktree remove --force`；主工作树改动仅 `docs/reviews/P1-ENG-CAPTURE-001.md` 与 `docs/current-status.md`。
