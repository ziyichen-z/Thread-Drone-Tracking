# P1-ENG-CAPTURE-001 — 停点 `K1K2K3K4` 交接证据（R1返工；候选 3，交 `R2@K1K2K3K4`）

- 轮次：`R1返工`（Dispatch-Id `P1-ENG-CAPTURE-001-R1返工-20261010T182657Z-2adb`），实现角色（Opus 子代理，Mac mini，`.venv-yoloe/bin/python`，进程设 `YOLO_OFFLINE=True`、`YOLO_AUTOINSTALL=False`）；前序轮次 `C1返工`、`阶段A回放`、`阶段A续`、`阶段A实现`（原文见文末附录与 git 历史）。
- 后续轮次 `Air预检`（Dispatch-Id `P1-ENG-CAPTURE-001-Air预检-20261010T194445Z-0e28`；MacBook Air 只读预检与资源补记，零消耗）：预检原始读数在 `docs/evidence/P1-ENG-CAPTURE-001-play-ops.md` §1，资源补记见 §R8。
- 后续轮次 `R2文档闭合`（Dispatch-Id `P1-ENG-CAPTURE-001-R2文档闭合-20261010T192319Z-db92`；仅文档与资源账补记，零代码、零执行）：改动范围、§R2 补正、资源补记与未执行声明见 §R7，供 Review 在复核文件「回归核实」小节定点复看。
- 合同：同名提案 §2–§7、AC-1…28 及各修订、「终局裁定」AR1-2/3/6、「信封落实」、「阶段A实现 IR 裁定」、「Contract conformance」C2（IR-C2-1…5）；复核文件 `docs/reviews/P1-ENG-CAPTURE-001.md` R1@K1K2K3K4 §3（R1-1…R1-4、CLASS_3 建议、墙钟附注）；账本 2026-10-10「用户答 C2 上交两项」（磁盘按上界判未越界、以后临时工作区实测记账；IR-C2-5 保持原判据记证据缺失）。
- **本轮结论：R1-1、R1-2、R1-3 三条阻断 finding 全部修复，每条附修复前必失败、修复后通过的具名回归（生产路径夹具，§R0）；既有 `test_rollback_failure_paths_replayed_in_new_process` 未改未放宽且通过；墙钟附注已补写报告前判定；CLASS_3 两处已应用，并按用户 IR-C2-5 裁定把「缺原键 prior」在 AC-18/24 评分代码中记为 `EVIDENCE_MISSING`（留在分母、不计通过）。R1-4（`SCOPE_GAP`）未修，由接受角色记债。真实返工 diff 记为候选 3（账本返工归因事件）。正式回放不重跑（判定与零模型核验见 §R3）；停点全套 1 次，本项新增回归失败 0（§R4）。四项稳定停点自证成立（§R6），直接交 Review `R2@K1K2K3K4`（不经核对轮）。**
- 候选与 diff（运行时解析，不手写其他 SHA）：候选 3 代码 = 本轮主题含「R1返工 候选3代码」的提交（`git log --format=%H --grep='R1返工 候选3代码' -1`），其后本轮只有证据、账本与状态板；修复触及行 = `git diff <复核文件 R1 §0 round_candidate> <候选3代码提交> -- controller tools tests config`（7 个文件）；全量 diff 基线同前（`tools.eng_capture.common.accepted_base_commit()`）。

## R0. R1 finding 修复与具名回归（修前红 = 候选 2 代码（当时 HEAD 为派发登记提交、代码同候选 2：`git checkout HEAD -- <5 个代码文件>`，仅新测试在位，跑完逐字节复原）；修后绿 = 候选 3；原始输出 `docs/evidence/P1-ENG-CAPTURE-001-focused.log`「R1返工」三节）

| 项 | 缺陷（复核原文要点） | 修复 | 具名回归（修前 → 修后） |
|---|---|---|---|
| **R1-1**（CLASS_2，BC-15 = AC-15；AR1-2「缺引用即拒」） | `ReplayPort` 队列空时 follow 默认成功、pointer/restore/readback 退回本地模型；`replay_tm_inputs` 不核每次端口调用都消费到记录、不核残留与顺序 → 删行/截断不拒并伪造或洗白事件 | `controller/target_manager.py`：端口行按在线写出顺序归属于其前最近一条非端口输入行（该行处理期间的端口调用紧随其后落盘）；重放处理每条输入行前装入其端口段，每次端口调用必须按序消费到**同种类**下一条记录，否则（缺行/截断/乱序）记违例并抛 `ReplayInputIncomplete`（`ReplayRejected` 子类）；行处理完端口段必须恰好用完（多出/重复即拒）；违例另记在端口上，即使异常在事务回滚分支被 `except Exception` 吞掉，行末 `end_segment` 仍拒绝；init 后直接出现端口行即拒。删去旧格式「缺行退回本地模型」分支与未用的 `scripted` 接口（仓内无其他调用者）。在线写盘格式与在线路径零改动 | `tests/test_target_manager.py::ReplayTests::test_r1_1_deleting_any_port_line_is_rejected`（5 份生产日志 = 完整点击/跟踪/修复/重选/停止脚本 + `_FaultyCore` 四种回滚失败；逐一删去每条 `port` 行，42 子例修前不拒）、`::test_r1_1_truncated_after_click_request_is_rejected`（取到被受理点击请求行为止的字节前缀；取到读回端口行之前的前缀）、`::test_r1_1_port_lines_reordered_or_duplicated_are_rejected`（交换相邻不同种类端口行、重复一条端口行）：修前 47 处 FAIL → 修后 OK；`test_rollback_failure_paths_replayed_in_new_process` 等既有 ReplayTests 全部照过（未改） |
| **R1-2**（CLASS_2，BC-20；AR1-6「零模型不等于零磁盘」） | `formal_run.run` S-A-INPUT 早退写 `input-check.json`/`replay-report.json` 后 `return 3`，不记 `mini_new_disk_bytes` | `tools/eng_capture/formal_run.py`：早退在写完两文件后按输出目录实测字节 `record_ledger("mini_new_disk_bytes", …)`（零模型，加载前） | `tests/test_capture_replay.py::LaunchGuardTests::test_r1_2_input_stop_records_output_disk_bytes`（临时账本副本、`check_input` 打桩不通过、`frame_ids=[]`、加载器被调即断言失败）：修前账上磁盘事件 `[]` → 修后恰一条 = 输出目录实测字节、候选 2、加载 0 |
| 复核附注（墙钟） | `CountingModel` 的 30 min 门只在每次推理前核，最后一次推理后的评分/落盘不受核 | `formal_run.final_wall_check`：S-A-REPRO 与正常两条写报告路径在写 `replay-report.json` 前判一次，结果入 `wall_clock`；超限照写报告、记 `budget_deviation`（S-A-BUDGET 偏差，回用户）、正常路径退出码 6（不冒充在限内，不改已得读数） | `LaunchGuardTests::test_r1_2_final_wall_clock_judged_before_report`：修前 AttributeError → 修后 OK（附注非阻断，非 finding 闭合件） |
| **R1-3**（CLASS_2，BC-22 = AC-22；AC-23/25 见正文） | (a) `click_latency` 按数组位置配对 `click_received`/`submit_begin`，页面本地拒绝无 `submit_begin` 时其后全部错位；(b) `wall_s` 恒 None；(c) `score_body_band` 把缺真值的 FOLLOW 帧计入带内、无「非 FOLLOW 帧数」；(d) `score_red_car_loop` 未限红车段 | (a) `click_web.ClickApp.click` 每次点击生成 `click_id`，写进 `click_received`/`click_refused` 与提交 `binding`（`submit_begin`/`refused`/`submit_result` 都带它），提交返回后补写 `click_submitted`（click_id → request_id 或拒绝）；`analyze_play.click_latency` 按 click_id 配对，被拒点击单独成行（`refused`/`refused_reason`、request_id 为空、FAIL），页面拒收的畸形点击亦计入分母；(b) `wall_s` = 提交事件 `at_unix_s` − 页面收到点击 `click_received_unix_s`（描述）；(c) 缺真值 FOLLOW 帧不计入带内、单列 `follow_frames_without_truth`（分母不去掉，保持项记 `EVIDENCE_MISSING` 不判 PASS），新增 `non_follow_frames`（保持窗内已授权而非 FOLLOW 的帧数）；(d) `score_red_car_loop(…, segment=)` 只在红车段内统计，`main` 以 [`red_car_segment_start`, S4 首次点击帧) 调用 | `tests/test_capture_replay.py::AnalyzePlayTests::test_r1_3_refused_click_is_its_own_row_and_later_clicks_pair_by_request`（夹具 = 生产 `ClickApp` + 真实 `Submitter`（在途锁占用 → 拒绝；会话封住 → 拒绝）+ `InProcessSend` 发到真实捕获会话 `CaptureHarness` 写出的 click-web.jsonl 与会话日志）：修前第 1 行被记上第 2 次的 request_id → 修后 `[None, rid, None]`、第 2 行 e2e/提交帧/墙钟正确；`::test_r1_3_body_band_missing_truth_not_in_band_and_non_follow_counted`（FOLLOW/授权帧取自生产捕获会话日志）：修前 TypeError（无非 FOLLOW 帧数入口、缺真值帧算带内）→ 修后 OK；`::test_r1_3_red_car_loop_counts_only_the_red_car_segment`（生产会话 S1 点静止车、S2 点红车；`per_frame_from_logs`）：修前 AttributeError/TypeError（无段）→ 修后段内「非红车」0、段外静止车帧被排除 |
| CLASS_3 + IR-C2-5 | `-replay.md` §4 判据句与 `score_injection` docstring「原键无同帧 prior → NOT_EVALUABLE」与用户裁定措辞不一致 | `-replay.md` §4 第 44 行按复核逐字替换；`score_injection` docstring 同义修改。另按用户裁定（不扩 NOT_EVALUABLE、不从分母去掉、不计通过）把该分支的判定值由 `NOT_EVALUABLE` 改为 `EVIDENCE_MISSING`（`replay.score_injection` 与同口径的 AC-24 `analyze_play.score_prediction_windows`；后者该窗留在可评分母、总判不为 PASS），原因码 `original_key_same_frame_prior_missing` 不变；候选 2 九项均有 prior（IoU 已记），该分支未被取到，读数不变 | `ScoringTests::test_ir_c2_5_injection_missing_original_prior_is_evidence_missing`、`AnalyzePlayTests::test_ir_c2_5_prediction_window_missing_prior_stays_in_denominator`：修前 FAIL（NOT_EVALUABLE / 总判 PASS）→ 修后 OK（非 finding 闭合件，供复核核实读法） |
| R1-4（`SCOPE_GAP`） | 启动门不核全部计数 ≤ 上限 | **未修**（复核路由接受角色记债；本角色不写 `implementation-status.md`） | — |

既有测试夹具的唯一改动：`AnalyzePlayTests::test_click_latency_counts_every_click` 的手写点击日志补上 `click_id`（`click_received` 与 `submit_begin.binding`），使其与现行 `ClickApp`/`Submitter` 实际写出的格式一致；断言不变。

## R1. 改动范围（候选 2 → 候选 3，7 个代码/测试文件）

| 文件 | 改动 |
|---|---|
| `controller/target_manager.py` | R1-1：`ReplayInputIncomplete`；`ReplayPort` 端口段按序消费；`replay_tm_inputs` 端口段归属与行末核对。在线路径（`_record_port`、`commit_binding`、`_rollback`、`_release` 等）零改动 |
| `tools/eng_capture/formal_run.py` | R1-2 S-A-INPUT 收尾记磁盘；`final_wall_check` 与退出码 6 |
| `tools/eng_capture/analyze_play.py` | R1-3 (a)–(d)；`per_frame_from_logs` 行带 `event_seq`；AC-24 `EVIDENCE_MISSING` |
| `tools/eng_capture/click_web.py` | R1-3(a) `click_id` 与 `click_submitted`；`operator_web.py` 零 diff（AC-14 两处闭集不变） |
| `tools/eng_capture/replay.py` | CLASS_3 docstring；`score_injection` 缺原键 prior → `EVIDENCE_MISSING` |
| `tests/test_target_manager.py`、`tests/test_capture_replay.py` | §R0 具名回归；上述一处夹具格式补齐 |

`resident_core.py`、`det_assoc_tracker.py`、`track_loop.py`、`language_loop.py`、`ledger.py`、`baseline_runner.py`、配置与冻结文件本轮零 diff。

## R1a. AC 逐条（候选 3；指针沿附录 C1返工 §2，变化处写明）

状态口径同附录：`IMPLEMENTED_FOCUSED_PASS` = 实现完成且具名测试通过、候选 3 停点全套中这些用例均不在失败清单内——不是独立复核、不是 DONE。

| AC | 证据指针（候选 3 新增/变化） | 候选 3 状态 |
|---|---|---|
| AC-1、AC-2、AC-4、AC-8、AC-10、AC-11、AC-12、AC-16、AC-27、AC-28 | 同附录 §2 | IMPLEMENTED_FOCUSED_PASS（本轮相关代码零 diff；AC-16 `test_capture_isolation` 6 例照过：新增 `red_car_segment_start` 不读真值，`click_web.py` 只加 click_id） |
| AC-3、AC-5、AC-6、AC-9 | 同附录 §2（C1-1 用例） | IMPLEMENTED_FOCUSED_PASS（在线 KF 消费路径零 diff） |
| AC-7（修订 1/2） | 同附录 §2；`test:tests/test_target_manager.py::ReplayTests::test_rollback_failure_paths_replayed_in_new_process`（未改） | IMPLEMENTED_FOCUSED_PASS；`follow(` 调用点闭集不变（`test_follow_call_sites_closed_set`），`ReplayPort` 仍只在重放内 |
| AC-13（修订 1/2/3） | 同附录 §2 | IMPLEMENTED_FOCUSED_PASS（`language_loop.py` 与 `LanguageWorker` 零 diff） |
| AC-14 | `test:tests/test_capture_click_web.py`（13 例照过） | IMPLEMENTED_FOCUSED_PASS；`operator_web.py` 零 diff，两处闭集不变；`ClickApp` 新写 `click_id`/`click_submitted`，提交 argv 不变 |
| **AC-15（修订 1）** | `test:tests/test_target_manager.py::ReplayTests::test_r1_1_*`（三例）+ 既有 ReplayTests；`cmd:python -m controller.target_manager replay <候选2 new-arm-tm_inputs.jsonl> config/p1-eng-capture-001.json`（§R3 第 3 点） | IMPLEMENTED_FOCUSED_PASS（R1-1 已修：删行/截断/乱序/重复即拒；生产工件重放不变） |
| AC-17、AC-18（修订 1）、AC-19（修订 1） | `artifact:docs/evidence/P1-ENG-CAPTURE-001-replay.md`（候选 2 运行；§4 判据句 CLASS_3 已替换）；`test:tests/test_capture_replay.py::ScoringTests::test_ir_c2_5_injection_missing_original_prior_is_evidence_missing` | 读数沿用候选 2 正式回放（候选 3 不重跑，§R3）：现象门复现、AC-17 PASS、AC-18 九项 PASS、AC-19 六格非劣化；AC-18 缺原键 prior 分支改记 EVIDENCE_MISSING（未被取到） |
| **AC-20（修订 2/3）** | `cmd:YOLO_OFFLINE=True YOLO_AUTOINSTALL=False .venv-yoloe/bin/python -m unittest discover -s tests`；`artifact:docs/evidence/P1-ENG-CAPTURE-001-tests.log` | **已运行（候选 3 唯一一次）**：Ran 2666，F28/E34/S56，失败集 62 条与候选 2 逐条相同，新增回归 0；构造 2（§R4） |
| AC-21 | `artifact:docs/evidence/P1-ENG-CAPTURE-001-play-ops.md`（§7 加点击序号核定说明，R1-3 的直接后果） | 草案；B 未签 = 0 |
| **AC-22…AC-25 评分口径（停点 `PlayK2K4`，本停点只核口径）** | `test:tests/test_capture_replay.py::AnalyzePlayTests::test_r1_3_*`（三例）、`::test_ir_c2_5_prediction_window_missing_prior_stays_in_denominator` | 口径已修（R1-3 (a)–(d)；AC-24 IR-C2-5 对齐）；运行 `NOT_RUN`（B 未签 = 0） |
| AR1-6 共账 | `test:tests/test_capture_replay.py::LaunchGuardTests::test_r1_2_*`；账本 | S-A-INPUT 收尾写盘入账（R1-2 已修）、写报告前墙钟判定；R1-4 上限全维校验为 `SCOPE_GAP`（接受角色记债，未修） |

## R2. 本轮实现读法（待复核核实；实现角色不写提案，列此并在接力报告 needs_user 标明）

- **IR-R1-1（AC-23 红车段起点）**：复核原文「[S2 提交帧, S4 首次点击帧)」。按已裁定的 IR-C2-1，消费时 k 已处理的点击在历史头提交、该帧已发效果属旧绑定；故红车段起点取「S2 提交事件之后第一个授权事件的帧」（`red_car_segment_start`，按 event_seq；追平路径即提交帧本身），不把提交帧上旧绑定（静止车）的确认跟踪帧算成「非红车」。S2 未绑定 → AC-23 记 `NOT_EVALUABLE`（与现行 AC-25「S2 not bound」同口径）。
- **IR-R1-2（AC-25 缺真值）**：授权 FOLLOW 而缺真值的帧不计入带内、仍在比例分母内，保持项记 `EVIDENCE_MISSING`（不判 PASS、也不判 FAIL；套用用户 IR-C2-5「缺数据记证据缺失、不计通过、不从分母去掉」）；S2 提交帧缺真值 → 整项 `EVIDENCE_MISSING`（修前 KeyError）；未给 S4 时保持窗至 max(最后一个已授权帧, 最大真值帧) 为止（含该帧；`hold_window` 末值记其 +1），修前到最大真值帧且不含该帧。
- **IR-R1-3（AC-22 分母）**：〔R2文档闭合注：本条扩大分母读法**已不是现行指令**，由同名提案「Contract conformance」之「IR-R1-3答复落实」承接——用户 2026-10-10 答复保持原「全部发出的点击」分母、未发送畸形拒收单列描述、不计入 AC-22 判定；工具现行输出仍含畸形行，原工具读数与合同分母分列取读见 `docs/evidence/P1-ENG-CAPTURE-001-play-ops.md` §7.4；以下原文保留为当时读法〕页面因字段畸形拒收（`click_refused`，未发送）的点击也计入分母、记 FAIL（AC-22「含被拒」）。`--s2-click/--s4-click` 序号因此按点击行序（含被拒）核定，操作单 §7 已加说明。
- **IR-R1-4（AC-18/24 判定值）**：缺原键同帧 prior 的判定值为 `EVIDENCE_MISSING`（新增值，不改阈值、检测判据或分母）；AC-17「R-1 生存下界」暂定读数仍只计 PASS/FAIL 可评缺口（不是门，口径未变）。
- **IR-R1-5（AC-23 段末未结束的失观测）**：照列（`ended_at = None`）；其 T_report/T_repair 截止落在段内而未发生记不准时，落在段外记 None（段外不判）。
- **墙钟超限**：写报告前判定超 30 min → 报告照写、`budget_deviation` 记 S-A-BUDGET 偏差、退出码 6；读数保留不追认。

## R3. 候选 3 是否重跑正式回放：**不重跑**（判定与理由）

1. 合同与信封：AC-17/18/19 的回放加载与推理是每候选上限（「每候选 YOLO 1 次加载」为额度维度），不是每候选必跑义务；阶段 A 信封对候选 3 仍留加载 2、推理 5,500，不重跑不放弃任何额度，复核或接受若判需要仍可在余额内执行。
2. 候选 2 → 3 对正式回放计算路径的影响逐项：
   - `controller/target_manager.py`：只改离线 reducer 重放（`ReplayPort`/`replay_tm_inputs`），正式回放新臂走在线 `TargetManager` + 真实核心，不经过这两处；在线写盘格式零改动。
   - `tools/eng_capture/formal_run.py`：S-A-INPUT、S-A-REPRO 两个 STOP 分支（候选 2 回放均未进入）与正常路径写报告前新增 `wall_clock` 字段/退出码（不参与任何读数计算）。
   - `tools/eng_capture/replay.py`：`score_injection` 只改「原键无同帧 prior」分支的判定值与 docstring；候选 2 九项注入均有原键 prior（`replay-report.json` 各项 `iou` 非空），该分支未被取到。
   - `analyze_play.py`、`click_web.py`：只属 Play 评分/点击页，正式回放不导入。
   - 检测、关联、合成滚转、基线臂、AC-17/19 评分函数零 diff。
   故候选 3 重跑只会重做同一计算，AC-17/18/19 读数仍以 `docs/evidence/P1-ENG-CAPTURE-001-replay.md`（候选 2 运行）为准，不声称为候选 3 运行产物。
3. 零模型核验（R1-1 对生产工件的影响）：候选 2 正式回放落盘的 `outputs/eng-capture/replay/candidate2-20261010T024317Z/new-arm-tm_inputs.jsonl`（sha256 前缀 709756a3，含 4 条端口行）在候选 3 代码下 `python -m controller.target_manager replay … config/p1-eng-capture-001.json` 退出 0、837 条事件，与同一输入在候选 2 代码（`git archive` 导出到暂存目录、`-I` 运行）下的输出**逐字节相同**；即新的端口段校验不误拒真实生产工件，AC-15 生产工件重放结论不变。

## R4. 测试与资源账（本轮）

**停点全套（AC-20，候选 3 唯一一次）**：`docs/evidence/P1-ENG-CAPTURE-001-tests.log`（HEAD = 候选 3 代码提交，启动时工作树只有账本改动；`YOLO_OFFLINE=True YOLO_AUTOINSTALL=False /usr/bin/time -p .venv-yoloe/bin/python -m unittest discover -s tests`，不带 -v）：Ran 2666，failures 28、errors 34、skipped 56，墙钟 557.70 s real（unittest 报 555.392 s，≤ 30 min），exit 1。**失败 id 集（`FAIL:`/`ERROR:` 头 62 条，含子测试）与候选 2 全套逐条相同**（排序后 `diff` 为空）：基线已有 61（归因同附录 C1返工 §6 表，接受基线未变）、IR-2 合同预期失败 1（`test_loop2_freeze` 仍只列 `det_assoc_tracker.py`/`resident_core.py`/`track_loop.py` 三路径）、**本项新增回归失败 0**；本轮新增 10 个用例（§R0）全部通过。日志说明：本次启动命令把 stderr（unittest 结果与计时）定向到会话暂存文件，完成后原样追加在 stdout 之后（文件内有分隔说明行），二者未交错；不是第二次运行。真实 YOLO 构造：F12 清单 `CarrierSelfTest` 类级 `_ready()` 为真、两例均执行 = 2，未超清单（S-A-LOADER 未触发）。

**focused（开发期，零模型）**：`docs/evidence/P1-ENG-CAPTURE-001-focused.log`「R1返工」三节——修前红（候选 2 代码 + 新测试）、修后绿、19 个相关模块全量（只有基线 CSRT 与 IR-2 预期失败）。另做的零模型核验：§R3 第 3 点生产 tm_inputs 新旧代码重放逐字节相同。本轮开发期真实权重加载 0、回放加载 0、推理帧 0。

**资源账**（`docs/evidence/P1-ENG-CAPTURE-001-ledger.json`；CAPTURE:A:1；本轮 / 累计 / 上限）：候选 3 开始（返工归因事件）→ 候选 3/3；停点全套 1 / 3 / 整批 3（候选 3 1/1）；全套真实构造 2 / 6 / 整批 6；回放加载 0 / 3 / 6（候选 3 0/2）；回放推理帧 0 / 7,924 / 16,500（候选 3 0/5,500）；开发期真实加载 0 / 8 / 20；mini 新增磁盘：开工补记（候选 2 名下，用户 10-10「以后的临时工作区必须实测记账」）R1 复核一次性副本峰值 81,477,632 + 复核暂存 27,131,904 + git 对象 9bb0430..a6a7e4a 2,396,607；本轮收尾补记见账本末条（会话暂存目录、两份已删除临时导出的峰值、证据增量、本轮代码提交 git 对象）；累计见账本 `counters.mini_new_disk_bytes` / 3 GB。scenario/session/run、Unity/Play、板上、VLM/API、云 GPU、下载/安装全 0。全套启动前经 `tools.eng_capture.ledger check` 核账（整体校验、候选 3 归因、全套/构造余额、磁盘），进程设两个环境变量。

**整批余额提示**：本轮后停点全套 3/3、全套构造 6/6、候选 3/3 均已用尽；若 `R2@K1K2K3K4` 再判返工，信封内已无停点全套与新候选额度，只剩 engineering-workflow §6 的窄修替代通道（前提是不触及真实模型加载器、数据划分或对外指标路径），否则须回用户。

## R5. 风险与未验证项

- R1-1 的端口段归属依赖「端口调用只发生在某条输入行的处理期间、且其记录紧随该行之后写出」这一在线不变量（现行代码成立：`_read_pointer`/`_record_port` 只在提交、回滚、释放内调用，而这些入口都先写自身输入行或位于帧/点击/释放行的处理内）；日后若新增不先写输入行的端口调用入口，重放会拒绝（fail-closed），不会静默放过。
- 恰好截在某输入行全部端口记录之后（会话在两行之间崩溃）的前缀仍是一致的合法前缀，重放给出截止该点的事件、不拒绝；这不是缺行。删去非端口输入行（帧/点击行）不在 R1-1 闭合范围，重放不一定拒绝（事件会分叉）。
- R1-3 的 Play 评分修复未在真实 Play 日志上执行（阶段 B 未签 = 0，AC-22…26 `NOT_RUN`）；夹具为仿真会话替身 + 生产点击页/提交器。
- AC-17/18/19 读数来自候选 2 运行（§R3）；附录 C1返工 §7 的其余风险不变（占位参数、单次回放、n = 12 只作非劣化、基 26 未分析）。

## R6. 四项稳定停点自证（workflow §4.3.1；候选 3）

| 条件 | 自证 | 指针 |
|---|---|---|
| 1 实现范围和接口已冻结 | **成立**：候选 3 代码/测试冻结于本轮「候选3代码」提交（其后只有证据、账本、操作单说明与状态板）；返工只修 R1-1…R1-3、墙钟附注与 CLASS_3/IR-C2-5，未改门值、剧本、参数、信封或在线协议；新读法 IR-R1-1…5 已列待核 | §R0；§R1；§R2 |
| 2 相称的实现者测试/编译通过 | **成立**：三条阻断 finding 各有生产路径夹具的修前红/修后绿具名回归；停点全套一次，失败集与候选 2 逐条相同、本项新增回归失败 0；正式回放按 §R3 判定不重跑，生产 tm_inputs 新旧重放逐字节相同 | §R0；§R3；§R4 |
| 3 已知 Unity 失败已修复 | 不适用（阶段 A 零 Unity；不记 UNITY_NA） | — |
| 4 复核文件、状态板、候选 commit、未验证风险已更新 | **成立**：本文件、focused.log、tests.log、账本、replay.md（CLASS_3）、play-ops（§7 点击序号说明）已更新并提交推送；状态板交接行交 Review `R2@K1K2K3K4`（R1-4 交 Acceptance 记债）；风险见 §R5 | 状态板交接行；§R5 |

结论：**候选 3 到达稳定停点，直接交 `R2@K1K2K3K4`**（复核返工不经核对轮；本停点 `REWORK_REQUIRED` 已 1/2）。未经复核不记 DONE；AC-22…26 仍属 `PlayK2K4`、B 未签 0。

## R7. R2文档闭合（R2-1 路径 (ii) 操作单补正、§R2 CLASS_3、资源补记；交 Review「回归核实」定点复看）

- 轮次：`R2文档闭合`（Dispatch-Id `P1-ENG-CAPTURE-001-R2文档闭合-20261010T192319Z-db92`），实现角色（Opus 子代理，Mac mini）。依据：同名提案「Contract conformance」之「R2冻结裁定」（冻结集 {R2-1}、路径 (ii) `NOT_MECHANIZABLE`、IR-R1-2 补正、磁盘两笔）与「IR-R1-3答复落实」（AC-22 修订 1 与「合并交 Implementation 的文档任务清单」）；复核文件 R2@K1K2K3K4 §0（磁盘读数）、§3（R2-1、CLASS_3）；账本 2026-10-10「用户答 IR-R1-3」与「用户答 C2 上交两项」（临时工作区实测记账）。
- **本轮不声明 R2-1 已闭合**：是否闭合、终局 verdict 与机读通过指针只由 Review 在 `docs/reviews/P1-ENG-CAPTURE-001.md`「回归核实」小节写。候选仍为候选 3（代码零 diff），本轮不创建新候选。

### R7.1 改动范围（闭集，仅文档与资源账）

| 文件 | 改动 |
|---|---|
| `docs/evidence/P1-ENG-CAPTURE-001-play-ops.md` §7 | 改写为 §7.1–7.4：§7.1 两次 `analyze_play` 调用（第一调用 `--s2-click <S2序号> --s4-click <S4首次序号>` → `play-readings.json`；第二调用同 session-dir/click-log/truth、`--s2-click <换回序号>`、不带 `--s4-click` → `play-readings-return.json`），删去原硬填示例序号 `2`/`3`；§7.2 点击序号按含拒收行的原全行序核定（附只读列行命令）、目标身份与绑定从现场记录及提交/授权日志核实；§7.3 AC-23 两段同时取读与结论规则（第二调用 AC-25 不采用、AC-22 只计一次）；§7.4 AC-22 原日志对照、仅剔除 `click_refused` 且 `reason = malformed_click` 的未发送行、合同分母与工具读数分列、PASS/FAIL/NOT_EVALUABLE/EVIDENCE_MISSING 规则、不能分列即停报 |
| 本文件 | 文首加本轮指针；§R2 IR-R1-2 末句按复核 R2 §3 CLASS_3 逐字替换；§R2 IR-R1-3 加承接注（原文保留为当时读法）；新增本节 |
| `docs/evidence/P1-ENG-CAPTURE-001-ledger.json` | 经 `python -m tools.eng_capture.ledger record`（既有写入入口，工具未改）追加 5 笔 `mini_new_disk_bytes`，归候选 3（§R7.3） |
| `docs/current-status.md` | 本项交接行交 Review（回归核实）、Current state 本项磁盘补账句更新、`## Log` 一条 |

`controller/`、`tools/`、`tests/`、`config/`、`Assets/`、`ProjectSettings/`、`Packages/` 零 diff（`git diff --stat` 核）；操作单不加入 PLAY_GOVERNING 冻结文件集。

### R7.2 供定点复看的具名行（修前 → 修后）

| 裁定条 | 修前（HEAD `-play-ops.md` §7） | 修后具名位置 |
|---|---|---|
| R2冻结裁定 (ii)-1 第一调用、按实际行序核序号、不硬填 | 一次调用、硬填 `--s2-click 2 --s4-click 3`，另段说明需核序号 | §7.1 第一调用；§7.2 第 1–2 条 |
| (ii)-2 第二调用（同三输入、换回序号、不带 `--s4-click`、另存；起点 = 换回提交后首个新绑定授权帧、至会话末；未绑定/无授权帧/缺日志不算通过） | **缺**（只评 S2→S4 首次点击一段） | §7.1 第二调用；§7.3 第 2、4 条 |
| (ii)-3 AC-23 两段与原合同其余读数同时成立、缺段不以首段代替；第二调用 AC-25 不采用；AC-22 不重复计 | **缺**（「AC-23 只在红车段…内统计」） | §7.3 第 1–5 条 |
| (ii)-4 只写未来操作、不执行 | — | §7 文首注 |
| IR-R1-3答复落实 取读步骤 1–4 | **缺** | §7.4 第 1–3 条、§7.2 第 2 条（序号不按合同分母重编号）、§7.4 第 4 条（不能分列即停报） |
| CLASS_3（IR-R1-2） | 「保持窗到最后一个已授权帧」 | 本文件 §R2 IR-R1-2 末句 |
| IR-R1-3 承接 | 扩大分母读法未标承接 | 本文件 §R2 IR-R1-3 句首注 |

### R7.3 资源补记（账本 `docs/evidence/P1-ENG-CAPTURE-001-ledger.json`；CAPTURE:A:1）

| 笔 | 金额（B） | 来源 / 读数方法 |
|---|---|---|
| 1 | 80,961,536 | 复核 R2 §0：R2 复核一次性副本检出峰值（`du -sk`，不含符号链接目标；已删除、净新增 0，仍按峰值计） |
| 2 | 17,797,120 | 复核 R2 §0：R2 复核会话暂存目录（即 supervisor 会话 `scratchpad/r2`；本轮实测现存普通文件 15,610,374 B ≤ 该读数，按复核读数计、不另计） |
| 3 | 4,637,031 | 本轮实测：git 对象 `ddaf982..d8ca5d5`（候选3代码提交之后至本轮派发登记，16 提交、90 对象，`git cat-file objectsize:disk` 合计；覆盖 R1返工末条所留「收尾提交自身 git 对象未测」，与此前 `a6a7e4a..ddaf982` 不重叠） |
| 4 | 1,851,741 | 本轮实测：supervisor 派发会话暂存中 R1返工收尾实测（2026-10-10T18:54:17Z）之后新增、未入账的普通文件（接受三轮 `acc-r14`/`acc-r2f`/`acc-ir13` 运行目录、两份派发提示、任务输出；不含已由第 2 笔覆盖的 `r2`） |
| 5 | 17,447 | 本轮实测：本轮文档增量（`-play-ops.md`、本文件、`docs/current-status.md` 相对 HEAD 的字节增量）+ 账本增量（含本笔的上界） |

- 查重：前 2 笔为复核 R2 新读数，账内此前无同额同源事件（R1 复核两笔 81,477,632 / 27,131,904 B 另计）；第 3 笔区间与既有 git 对象各笔不重叠；第 4 笔以上一次收尾实测时刻为界。全部归既有候选 3（R2 复核对象 / 当前归属候选），不新增候选号。
- 累计（本轮后）：`counters.mini_new_disk_bytes` = 275,235,939 B，对用户 3 GB（3,000,000,000 B）上限；账内 `mini_new_disk_bytes_total` 3 GiB 字段不构成超出用户 3 GB 的授权。其余维度本轮 0：候选 3/3、停点全套 3/3、构造 6/6、回放加载 3/6、推理 7,924/16,500、开发期加载 8/20 均不变；scenario/session/run、Unity/Play、板上、VLM/API、云 GPU、下载/安装全 0。
- **未知（不假记 0、不据以推余额）**：接受三轮 `codex exec` 进程自身在 `~/.codex/` 下的会话日志与缓存未测；本轮收尾提交自身的 git 对象未测，留待下一轮补记。

### R7.4 未执行声明

本轮未跑任何测试（focused/全套）、未加载模型、未执行评分/重放、未 Play、未启动阶段 B、未下载/安装；只读核对 `tools/eng_capture/analyze_play.py::click_latency/red_car_segment_start/score_red_car_loop/main`、`tools/eng_capture/click_web.py::ClickApp.click` 与 `tools/eng_capture/ledger.py` 写入入口以确认 §7 字段名与 CLI 参数；§7.2 只读列行命令只在会话暂存的 3 行合成文件上核过语法（已删除）。AC-22…26 仍 `NOT_RUN`、B 未签 = 0；R1-4/R2-2 OPEN 债不变；无 UNITY_NA/DONE。


## R8. Air预检（§8.2 只读预检 + 资源补记；不改代码、不建候选）

- 轮次：`Air预检`（Dispatch-Id `P1-ENG-CAPTURE-001-Air预检-20261010T194445Z-0e28`），实现角色（Opus 子代理，MacBook Air）。依据：账本 2026-10-09 CAPTURE:A:1 条第 2 题（U-3）、同名提案「信封落实」U-3 与「通过轮消费」资源补记义务、复核文件「回归核实」§5。
- 预检：九项原始读数与结论写入操作单 §1（结论「全部核过」；两处补丁号版本差逐项说明；另记 `runtime/` 既往 Play 残留观察交接受角色）。只读：未加载模型、未 import torch/ultralytics、未跑测试、未启动或操作 Unity、未 Play、未生成覆盖文件、未写 `runtime/`、未安装/下载、未拷贝、未在 mini 写入（mini 侧仅只读 `ssh … true`/`test -d`/`git rev-list|cat-file`）。

### R8.1 资源补记（账本 `docs/evidence/P1-ENG-CAPTURE-001-ledger.json`；CAPTURE:A:1；经既有 `python3 -m tools.eng_capture.ledger record`）

| 笔 | 金额（B） | 来源 / 读数方法 |
|---|---|---|
| 1 | 81,022,976 | 复核「回归核实」§5：回归核实一次性副本检出峰值（`du -sk`；已删除、净新增 0，仍按峰值计）；该复核会话暂存 0 B |
| 2 | 2,124,548 | mini 只读实测：git 对象 `d8ca5d5..353812a`（8 提交、45 对象，`objectsize:disk`；同范围 Air 打包后 35,941 B，按 mini 计）；承接 §R7.3 所留「收尾提交自身 git 对象未测」，与 `ddaf982..d8ca5d5` 不重叠 |
| 3 | 25,129 | mini 工作树文档净增 `4d94187..353812a`（git blob 字节差：复核文件 9,579、提案 5,990、派发日志 8,831、状态板 729） |

- 查重：第 1 笔与 R1 复核副本 81,477,632 B、R2 复核副本 80,961,536 B 为不同轮次的不同副本，账内无同额事件；三笔均归既有候选 3，不新增候选号。
- 累计（本轮后）：`counters.mini_new_disk_bytes` = 358,408,592 B，对用户 3 GB 上限；其余维度不变，B 未签 = 0。
- **未知（不假记 0、不据以推余额）**：通过轮消费 `codex exec` 运行目录、supervisor 暂存与 `~/.codex/` 缓存未测；本轮 Air 文档增量在 Air（无 A 磁盘维度，量级为数 KB），mini 拉取本轮及其后提交的对象与工作树字节留待下一轮补记。

---

## 附：C1返工交接原文（候选 2；历史，不改写；原各级标题降一级）

## P1-ENG-CAPTURE-001 — 停点 `K1K2K3K4` 交接证据（C1返工；候选 2 正式回放与停点全套已跑，交 `C2@K1K2K3K4`）

- 轮次：`C1返工`（Dispatch-Id `P1-ENG-CAPTURE-001-C1返工-20261010T022016Z-8465`），实现角色（Opus 子代理，Mac mini）；前三轮 `阶段A回放`（`…-20261010T012252Z-5d32`）、`阶段A续`（`…-20261010T005430Z-8e0f`）、`阶段A实现`（`…-20261009T233249Z-2373`）。
- 合同：同名提案 §2–§7、AC-1…27，「终局裁定（第三次，依用户 (a)）」AR1-2/3/6，「信封落实」，「阶段A实现 IR 裁定」IR-1…9、AC-28、AC-20 修订 2/3，「Contract conformance（核对表）」C1@K1K2K3K4 的 C1-1…C1-5、F-1…F-5、RR-2/RR-3 裁定与预复核关注项；账本 2026-10-10「用户答 RR-1：修顺序，按提交后状态判 AC-17」。
- **本轮结论：C1-1…C1-5 全部修复，每条附修复前必失败、修复后通过的具名回归（§0）；RR-1 按用户答复落实（保留 557–600 窗口与两点剧本，§3.3 ①→⑤ 先提交替换请求再授权，按同一提交后状态/效果评分）；预复核关注项中属合同义务的两项（端口结果可重放、AC-24 原检测定义）一并落实。真实返工 diff 记为候选 2（返工归因入账，不换号）。候选 2 正式回放：现象门复现、AC-17 PASS（557 帧状态与效果同属新绑定）、AC-18 九项全部可评且 PASS、AC-19 六格非劣化；停点全套一次，失败 id 集与候选 1 逐条相同，本项新增回归失败 0。四项稳定停点自证成立（§8），交 `C2@K1K2K3K4`；本停点已无第二次核对退回，实现读法 IR-C2-1…5 交核对轮裁定（§5.2）。**
- 基线（修改前）= 本提案 `ACCEPTED` 裁定提交，运行时解析：`.venv-yoloe/bin/python -c "from tools.eng_capture.common import accepted_base_commit as a; print(a())"`。完整候选 diff：`git diff <基线> <本轮末提交> -- . ':(exclude)docs/current-status.md' ':(exclude)docs/authorizations.md' ':(exclude)docs/proposals' ':(exclude)docs/evidence/supervisor-dispatch.jsonl'`；本轮返工 diff（候选 1 → 候选 2）：`git diff 2d12c50 9bb0430 -- controller tools tests config`（9 个文件；`9bb0430` 之后只有证据、账本与状态板）。不在本文件手写其他 SHA。

### 0. C1 退回项与预复核关注项落实（具名回归：修前红 = 候选 1 代码 + 新测试；修后绿 = 候选 2；原始输出 `docs/evidence/P1-ENG-CAPTURE-001-focused.log`「C1返工」三节）

| 项 | 缺陷（核对表原文要点） | 修复 | 具名回归（修前 → 修后） |
|---|---|---|---|
| **C1-1** KF 消费 fail-closed（AC-3/5/6/9；AR1-2 修订 1） | prior 只核键、门只核 valid；post 缺失/无效仍刷新 t0 并按 within 放行；缺 prior 时凭有效 post 发预测云台 | `controller/target_manager.py`：`same_frame_prior`（`priors_available`、键、传感器帧、库帧、阶段 = prior、有效、S 可逆）与 `same_frame_post`（同对齐、阶段 = posterior、有效）；③ 原轨迹重匹配、竞争、④ 修复证据一律用原键同帧 prior；接受原观测还须同帧有效 posterior，任一不合格 → 不接受、不刷新 t0、`kf_ok=False` → 本帧无预测（云台不发）、HOLD；未匹配帧预测中心改取原键同帧 prior（不再取 post）；授权输入只在信念快照为本帧对齐有效的 posterior（OBSERVED）/prior（PREDICTED）时计 within；点击须提交帧有效 post（否则 `kf_post_invalid` 拒绝、零状态变化），修复提交须候选键有效 post（否则本帧不提交）；`motion_size_gate` 另拒非 prior 阶段 | `test_target_manager.ContinuityTests.test_c1_1_matched_original_with_misaligned_or_missing_prior_not_accepted`（6 子例）、`::test_c1_1_matched_original_with_invalid_or_missing_post_not_accepted`（4）、`::test_c1_1_lost_original_without_valid_prior_has_no_predicted_gimbal`（3 + 对齐正例）、`::test_c1_1_click_with_invalid_head_post_rejected_keeps_old_target`（2）；`RepairTests.test_c1_1_repair_with_misaligned_original_prior_never_commits`（2）、`::test_c1_1_repair_commit_requires_valid_candidate_post`；`test_capture_session.PredictionTests.test_c1_1_missing_prior_with_valid_post_has_no_gimbal_and_holds`。全部修前 FAIL → 修后 OK；均断言 t0/提交与云台不发（观测与预测）+ HOLD，而非只断言非 FOLLOW |
| **C1-2** AC-18 检测判据（含 RR-3） | 以 accepted OBSERVED 代替「缺口后首个真值 IoU≥0.5 的检测」；修复后比较新键 prior | `tools/eng_capture/replay.py`：新臂逐帧记录保存策略后原始检测 `raw_detections_px` 与各键同帧 prior `priors_xywh_px`；`score_next_real_observation` 按原定义找下一真实观测（不要求被接受）；`score_injection` 预测框取注入前原绑定键同帧 prior，分列不续跟/行 7/修复/报告；`formal_run` 把各注入评分窗口逐帧记录落盘；`tools/eng_capture/analyze_play.score_prediction_windows`（AC-24）同一口径（预复核关注项） | `test_capture_replay.ScoringTests.test_c1_2_next_observation_is_raw_detection_even_without_accepted_observation`、`::test_c1_2_prediction_is_original_key_prior_not_repaired_key`、`AnalyzePlayTests.test_c1_2_prediction_windows_use_raw_detections_and_original_prior`：修前 ERROR/FAIL → 修后 OK；原 `test_injection_iou_and_not_evaluable` 改用新记录格式。正式读数见 `docs/evidence/P1-ENG-CAPTURE-001-replay.md` §4，R-1 暂定读数随之重算（§3），候选 1 读数原文保留在其附录 |
| **C1-3** 点击/授权顺序与工件一致性（RR-1） | 回放先生成旧效果、再把点击后信念盖到记录 | 回放 `run_new_arm`：本帧入历史后先处理点击（§3.3 ①，提交帧 = 本帧），再 `on_frame` ②–⑤；管理器 `_frame` 对「本帧 ① 已提交」的绑定不再重复 ②–④（提交即本帧已接受观测）、直接 ⑤；记录带 `version`，评分器要求效果与记录同帧同版本，否则 `STATE_EFFECT_INCONSISTENT`；取消 `pre_click`。会话 `controller/language_loop.py`：追平路径（页面帧 k 尚未处理）在 k 帧入历史、授权之前提交点击并立即执行纪元/状态副作用，k 帧效果属新绑定；k 已处理时在历史头提交（读法见 §5.2 IR-C2-1）。`analyze_play.per_frame_from_logs` 绑定键按事件顺序归属。候选 1 原工件不改、不补写 | `test_capture_replay.NewArmEndToEndTests.test_c1_3_click_frame_state_and_effect_are_post_commit_and_consistent`（取代 F-2 的 `test_click_frame_record_is_post_commit_state`）、`ScoringTests.test_c1_3_window_requires_same_frame_state_and_effect`、`AnalyzePlayTests.test_c1_3_per_frame_binding_follows_event_order_not_frame_label`、`test_capture_session.ClickTests.test_c1_3_catch_up_click_is_applied_before_that_frame_is_authorized`：修前 FAIL → 修后 OK |
| **C1-4** 限速路径可重放（AC-15） | `note_control_limited` 只发事件不写输入，重放缺事件、其后序号漂移 | `note_control_limited` 先写 `control_limited` 输入行（frame_id、effect_seq）再发事件；`replay_tm_inputs` 复现；不删事件 | `test_target_manager.ReplayTests.test_c1_4_control_limited_replayed_in_new_process`（新进程只读输入/配置，全字段逐条相等）：修前 FAIL → 修后 OK |
| 预复核关注项（AC-7/15）：失败端口重放 | `ReplayPort` 只保 pointer/coasting；restore/读回失败无落盘输入；错误文本二次加前缀 | 端口每次调用结果逐条落盘（`PORT_CALLS` = follow/restore/readback/pointer），`ReplayPort` 按调用种类分队列复现，`ReplayedPortError` 逐字复现原错误文本 | `ReplayTests.test_rollback_failure_paths_replayed_in_new_process`（半改复原成功、复原 follow 失败、coasting 恢复失败、读回不符；以 `_FaultyCore` 真实核心子类在线产生）：修前 4 子例全 FAIL → 修后 OK |
| **C1-5** 共账与启动门（AR1-6） | 推理只在整段返回后记账、只有内存计数；`ledger_balance` 不核候选/归属/UNKNOWN/零维度，缺字段 KeyError | 新 `tools/eng_capture/ledger.py`：整体校验（必需字段、非负整数、无 UNKNOWN、计数 = 事件和、零维度恒 0、无未结算 in_flight、候选数 ≤ 3）→ 候选归属（只有已开始且有归因事件的当前候选可耗用）→ 逐维余额；`InflightCounter` 每帧在交给模型**之前**原子落盘 +1（越上限先拒绝；崩溃留 in_flight、未结算启动门拒绝，`settle` 记原因后结算，耗用不返还）；`CountingModel` 接入并加 30 min 回放墙钟门；`formal_run` 加载尝试前记账、两阶段逐帧共账、结束按实测字节记磁盘；记账原子写 | `test_capture_replay.LaunchGuardTests.test_c1_5_counting_model_persists_each_submitted_frame_before_inference`、`::test_c1_5_ledger_balance_refuses_unattributed_unknown_inconsistent`（9 子例）：修前 ERROR/FAIL → 修后 OK；`::test_ledger_balance_refuses_over_budget` 与 `BaselinePackageTests.test_formal_run_hands_the_verified_weights_file_to_the_loader` 夹具改用临时账本副本（测试不触碰真实账本） |

C1-5 账内既有偏差的补核（核对表「资源与稳定停点核对」）：① 候选 1 开始时只改计数未落事件 → 补一条事件（计数不再加）；② 00:03:02Z 两条 carrier focused 的启动前未核账/未设环境变量/`-v` 重跑偏差 → 补一条金额 0 的补核事件，偏差保留不追认，此后不再主张「所有启动前核账」；③ 磁盘账只列 outputs 根 → 补一条保守上界事件 30,380,346 B（§6 明细）。三条均在任何新消耗之前写入（本轮首个提交 `9bb0430`）。

### 1. 改动范围（完整候选 diff 的文件闭集）

候选 1 的文件闭集与组件说明不变（见本文件 git 历史 `bb5b050` 版 §1）；本轮返工 diff 只触及：

| 文件 | 本轮改动 |
|---|---|
| `controller/target_manager.py` | C1-1 同帧快照对齐与 fail-closed；C1-3 ① 已提交帧跳过 ②–④；C1-4 `control_limited` 输入；端口结果逐条落盘与 `ReplayPort` 分队列复现 |
| `controller/language_loop.py` | C1-3 追平点击在 k 帧授权前提交（`_pending_capture_click`、`_resolve_click`/`_commit_pending_click`/`_finish_click`）；`LanguageWorker` 零 diff |
| `tools/eng_capture/ledger.py`（新） | C1-5 启动门与逐帧共账 |
| `tools/eng_capture/replay.py`、`formal_run.py`、`analyze_play.py` | C1-2/C1-3/C1-5 |
| `tests/test_target_manager.py`、`test_capture_session.py`、`test_capture_replay.py` | §0 具名回归与夹具 |

`resident_core.py`、`det_assoc_tracker.py`、`track_loop.py`、`gated_publisher.py`、`language_bridge.py`、`pose_gmc.py`、`click_web.py`、`operator_web.py`、配置与冻结文件本轮零 diff。

### 2. AC 逐条（AC-1…21、AC-27、AC-28；候选 2）

状态口径：`IMPLEMENTED_FOCUSED_PASS` = 实现完成且具名测试通过（本轮停点全套中这些用例均不在失败清单内）——不是独立复核、不是 DONE；「已运行」= 本轮正式回放/全套实际执行。

| AC | 证据指针 | 本轮状态 |
|---|---|---|
| AC-1 | `test:tests/test_det_assoc_tracker.py::ClassPolicyTests` | IMPLEMENTED_FOCUSED_PASS（本轮未改） |
| AC-2 | `test:tests/test_pose_center.py`；`test:tests/test_pose_gmc.py::PoseHomography::test_gmc_sources_closed_set` | IMPLEMENTED_FOCUSED_PASS（未改） |
| AC-3（修订 1/2） | `test:tests/test_resident_core.py::HistoryContractTests`；`test:tests/test_det_assoc_tracker.py::KfSnapshotTests`；`test:tests/test_capture_session.py::BridgeIsolationTests`；消费侧 fail-closed 见 §0 C1-1 | IMPLEMENTED_FOCUSED_PASS（C1-1 已修） |
| AC-4 | `test:tests/test_target_manager.py::TaskSpecTests` | IMPLEMENTED_FOCUSED_PASS |
| AC-5/6（修订 1/2） | `test:tests/test_target_manager.py::ContinuityTests`（含 §0 C1-1 四个 `test_c1_1_*` 与 IR-6 矩阵）；`::RepairTests`（含两个 `test_c1_1_repair_*`） | IMPLEMENTED_FOCUSED_PASS（C1-1 已修） |
| AC-7（修订 1/2） | `test:tests/test_target_manager.py::CommitTests`；`::ReplayTests::test_rollback_failure_paths_replayed_in_new_process`；`test:tests/test_language_loop.py` | IMPLEMENTED_FOCUSED_PASS；调用点闭集不变（§3） |
| AC-8（修订 1/2） | `test:tests/test_target_manager.py::AuthorizationTests` | IMPLEMENTED_FOCUSED_PASS（纯函数未改） |
| AC-9（修订 1） | `test:tests/test_capture_session.py::PredictionTests`（含 `test_c1_1_missing_prior_with_valid_post_has_no_gimbal_and_holds`）；`test:tests/test_target_manager.py::ContinuityTests::test_c1_1_lost_original_without_valid_prior_has_no_predicted_gimbal` | IMPLEMENTED_FOCUSED_PASS（C1-1 已修；预测中心 = 原键同帧 prior，读法 IR-C2-3） |
| AC-10（修订 2） | `test:tests/test_capture_session.py::ReportTests`；`test:tests/test_language_bridge.py::Loop2BridgeTests::test_state_reasons_appended_without_reordering` | IMPLEMENTED_FOCUSED_PASS |
| AC-11（修订 1/2） | `test:tests/test_capture_session.py::StopTests`；`test:tests/test_target_manager.py::CommitTests::test_session_rollback_failure_holds_via_safety_channel` | IMPLEMENTED_FOCUSED_PASS |
| AC-12（修订 1） | `test:tests/test_capture_session.py::ClickTests`（含 `test_c1_3_catch_up_click_is_applied_before_that_frame_is_authorized`）；`test:tests/test_language_bridge.py::RequestBridgeTests::test_every_action_is_writable` | IMPLEMENTED_FOCUSED_PASS（追平路径 ①→⑤；受理子段仍 ≤ 1） |
| AC-13（修订 1/2/3） | `test:tests/test_capture_session.py::LanguageOffTests`、`::LanguageCompatTests` | IMPLEMENTED_FOCUSED_PASS（兼容路径与 `LanguageWorker` 本轮零改动） |
| AC-14 | `test:tests/test_capture_click_web.py` | IMPLEMENTED_FOCUSED_PASS（未改） |
| AC-15（修订 1） | `test:tests/test_target_manager.py::ReplayTests`（含 `test_c1_4_control_limited_replayed_in_new_process`、`test_rollback_failure_paths_replayed_in_new_process`）；生产工件 `new-arm-tm_inputs.jsonl` 新进程重放退出 0（replay.md 文首） | IMPLEMENTED_FOCUSED_PASS（C1-4 与端口重放已修） |
| AC-16（修订 1） | `test:tests/test_capture_isolation.py` | IMPLEMENTED_FOCUSED_PASS（新 `score_next_real_observation` 在 `score_` 前缀内；记录器不读真值） |
| AC-17 | `cmd:.venv-yoloe/bin/python -m tools.eng_capture.replay run … --candidate 2`；`artifact:docs/evidence/P1-ENG-CAPTURE-001-replay.md` §0–3；`test:tests/test_capture_replay.py::NewArmEndToEndTests::test_c1_3_*`、`::ScoringTests::test_c1_3_*`、`::ScoringTests::test_provisional_readings` | **已运行（候选 2）**：S-A-INPUT 过；现象门复现（561–565）；新臂 557–600 44 帧全部 OBSERVED 且 IoU ≥ 0.5（最小 0.761）、状态/效果不一致 0、BROKEN/误绑 0 → **PASS**（RR-1 用户答复读法：557 帧记录与效果同属新绑定，version 2/2，瞄红车） |
| AC-18（修订 1） | `artifact:docs/evidence/P1-ENG-CAPTURE-001-replay.md` §4；`test:tests/test_capture_replay.py::ScoringTests::test_c1_2_*`、`::NewArmEndToEndTests` | **已运行（候选 2，C1-2 原检测判据）**：m=1/2/4/6 与 off 对照、强制开新轨迹（`INJECTED`）九项全部可评、全部 PASS（IoU 0.804–0.844）；行 7 帧均有预测 look_at；T_report 563 / T_repair 565 准时；到期后原 ID 不续跟 |
| AC-19（修订 1） | `artifact:docs/evidence/P1-ENG-CAPTURE-001-replay.md` §5；`test:tests/test_capture_replay.py::RollPreregistrationTests`、`::RollSelectionInputTests` | **已运行**：72 序列全可评、每格 n = 12；六格新臂断轨率均 ≤ 基线（15/72 vs 34/72），只作非劣化 |
| AC-20（修订 2/3） | `cmd:YOLO_OFFLINE=True YOLO_AUTOINSTALL=False .venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-CAPTURE-001-tests.log 2>&1`（HEAD `9bb0430`）；`artifact:docs/evidence/P1-ENG-CAPTURE-001-tests-baseline.log`（候选 1 轮基线归因，基线未变） | **已运行（候选 2 唯一一次）**：Ran 2656，failures 28 / errors 34 / skipped 56；失败 id 集（62 条含子测试）与候选 1 全套逐条相同：基线已有 61、IR-2 合同预期失败 1、**本项新增回归失败 0**；F12 真实构造 2；墙钟 550 s（§6）。候选 1 的 tests.log 原文见 git `bb5b050` |
| AC-21 | `artifact:docs/evidence/P1-ENG-CAPTURE-001-play-ops.md` | 草案（本轮未改；B 未签 = 0） |
| AC-27 | `artifact:docs/evidence/P1-ENG-CAPTURE-001-fidelity-confirmation.json` | 用户已确认 consistent（候选 2 启动前样帧 sha 现核一致） |
| AC-28 | `test:tests/test_capture_replay.py::RollPreregistrationTests`/`::RollSelectionInputTests`；`test:tests/test_capture_isolation.py::SelectionInputIsolationTests`；`artifact:docs/evidence/P1-ENG-CAPTURE-001-replay.md` §0/§5 | 用户本人已登记六点；候选 2 启动前校验通过；两臂每基 12 种滚转复用同一登记点 |

### 3. AC-7 `follow`/`designate` 调用点

闭集不变（`controller/target_manager.py` commit/release/回滚、`resident_core.py` e1 兼容外壳、`det_assoc_tracker.py` 转发、`language_loop.py` 零），以 `test_follow_call_sites_closed_set` 的 AST 判定为准；本轮新增的会话点击路径不直接或经 `getattr` 调 `follow`。

### 4. 保真、预登记与准入

未变：AC-27 确认文件、AC-17 剧本（sha256 956a387f…）、AC-28 六基剧本（sha256 4ca6eae2…，计划 5d40e321…）与 S-A-INPUT 均在候选 2 启动前现核通过（`replay.md` §0）。细节见本文件 git 历史 `bb5b050` 版 §4。

### 5. IR-1…9 落实与本轮实现读法

IR-1…9 落实不变（见本文件 git 历史 `bb5b050` 版 §5 表）；IR-2 合同预期失败在候选 2 全套中仍只因 `controller/det_assoc_tracker.py`、`controller/resident_core.py`、`controller/track_loop.py` 三路径（全套日志该失败输出逐字），`tests/test_loop2_freeze.py` 零 diff；其余禁改路径与 `config/scenario.*` 本轮零 diff。RR-2（候选 1 加载 2/2）与 RR-3（暂定描述）按核对表裁定执行。

#### 5.2 实现读法（待 `C2@K1K2K3K4` 裁定；实现角色不写提案，故列于此并在接力报告 needs_user 标明）

- **IR-C2-1（会话点击提交帧，§3.3 ①/§3.5、AC-12/22）**：追平路径（消费时 k 尚未处理）已改为 k 帧入历史后、授权前提交（提交帧 = k，同帧状态与效果一致）。k 已处理（消费时 k ≤ 历史头）时，请求在该帧 ⑤ 之后才被消费，提交帧取历史头、该帧已发效果属旧绑定（请求当时尚未挂起，不违 ①），新绑定首个效果在下一被处理帧；Play 读数按事件顺序归属绑定键（`analyze_play`），不把旧效果算到新绑定名下。回放按「请求先于 k 帧授权挂起」建模（RR-1）。若核对轮认为 k 已处理时亦须对历史头追加一次新绑定效果或延至下一帧提交，请裁定。
- **IR-C2-2（AR1-2「点击新实例以当前有效 post 初始化」）**：提交帧 post 缺失/错帧/非 posterior/无效 → 点击拒绝，回执 detail `kf_post_invalid`（零状态变化、继续旧目标）；修复提交帧候选键 post 不合格 → 本帧不提交（证据保留、截止不变）。
- **IR-C2-3（§3.1/§3.2 内部预测）**：原轨迹未被接受的帧，预测中心取原绑定键**同帧 prior**（库「预测 → 本帧补偿」后状态）；lost 行两者数值相同，差别只在「库已匹配但未过本项门」的帧（不再用吸收了被拒量测的 posterior）。
- **IR-C2-4（授权原因）**：KF 不合格帧无预测中心 → 几何轴按现行实现记 invalid、首命中行 5（`GEO_REJECT`）；结果同为 HOLD/不发。
- **IR-C2-5（AC-18/24 下一真实观测）**：同一帧若有多个与真值 IoU ≥ 0.5 的检测，取 IoU 最大者；原键在该帧无同帧 prior → NOT_EVALUABLE（原因 `original_key_same_frame_prior_missing`，不编造）。

### 6. 测试与资源账

**停点全套（AC-20，候选 2 唯一一次）**：`docs/evidence/P1-ENG-CAPTURE-001-tests.log`（HEAD `9bb0430`，启动时工作树只有账本改动；`YOLO_OFFLINE=True YOLO_AUTOINSTALL=False .venv-yoloe/bin/python -m unittest discover -s tests`，不带 -v）：Ran 2656，failures 28、errors 34、skipped 56，墙钟 550 s（unittest 报 549.988 s）。失败 62 条（含子测试）与候选 1 全套（git `bb5b050` 版日志）逐条相同：

| 类别 | 条数 | 内容与依据 |
|---|---|---|
| 基线已有 | 61 | 接受基线 `9f1a8cc` 逐模块归因（`docs/evidence/P1-ENG-CAPTURE-001-tests-baseline.log`，候选 1 轮所做，基线未变）：`test_eng_loop2_play_ops` 24、`test_eng_sft_*`/`test_language_k_binding` 导入错误 5、`test_scene006_probe` 29（环境）、`test_trackers`/`test_track_loop` CSRT 2、`test_det_assoc_carrier.CarrierSelfTest.test_carrier_matches_caliber_b_from_first_update` 1（不一致帧列表仍为 `[2, 4, 5, 6, 8, 12, 17, 18, 19, 20]`） |
| IR-2 合同预期失败 | 1 | `test_loop2_freeze…test_play_governing_paths_outside_the_ownership_table_have_no_diff`（§5） |
| **本项新增回归失败** | **0** | 新增的 17 个用例（§0 具名回归等）全部通过 |

真实 YOLO 构造：F12 清单 `CarrierSelfTest` `_ready()` 为真、两例均未 skip，各 1 次 = 2，未超清单（S-A-LOADER 未触发）。

**focused（开发期，零模型）**：`docs/evidence/P1-ENG-CAPTURE-001-focused.log`「C1返工」三节——修前红（候选 1 代码 + 新测试）、修后绿与 27 个相关模块全量（只有基线 CSRT 与 IR-2 预期失败）；本轮开发期真实权重加载 0。另以替身模型、临时账本副本在 scratchpad 做过一次正式执行体零模型彩排（不写真实账本、不是证据），确认两阶段 in_flight 结算、注入窗口落盘与磁盘记账路径可达。

**资源账**（`docs/evidence/P1-ENG-CAPTURE-001-ledger.json`；CAPTURE:A:1；本轮 / 累计 / 上限）：候选 2 开始（返工归因事件）→ 候选 2/3；回放加载 1 / 3 / 每候选 2、整批 6（候选 2 1/2）；回放推理帧 3,962 / 7,924 / 每候选 5,500、整批 16,500（候选 2 3,962/5,500，逐帧提交前落盘）；停点全套 1 / 2 / 整批 3（候选 2 1/1）；全套真实构造 2 / 4 / 整批 6；开发期真实加载 0 / 8 / 20；mini 新增磁盘：本轮 +30,380,346（补核上界）+6,741,842（候选 2 回放输出）+6,757（启动/运行日志与 rescore）+ 收尾补记（见账本末条）/ 累计见账本 `counters.mini_new_disk_bytes` / 3 GB；墙钟：回放 146.18 s、全套 550 s（各 ≤ 30 min）。scenario/session/run、Unity/Play、板上、VLM/API、云 GPU、下载/安装全 0。所有消耗步骤启动前经 `tools.eng_capture.ledger check` 核账、进程设两个环境变量。

磁盘补核明细（30,380,346 B，保守上界，2026-10-10T02:42Z 实测）：本会话目录 scratchpad/tasks 自 2026-10-09T23:30Z 起全部普通文件 20,769,162 B（含候选 1 零模型试跑 dry1/dry2/smoke1、补丁备份、红绿日志、本轮零模型彩排；亦含接受/supervisor 产物，按保守计入）；仓内 `docs/evidence/P1-ENG-CAPTURE-001-*` 124,781 B；接受基线以来改动/新建的代码测试配置现大小 1,372,243 B；git 对象 base..HEAD 磁盘 6,947,729 B（含其他角色提交，保守）；仓内 `*.pyc` 1,166,431 B。一次性 worktree 已删除、现不占用，历史峰值未测（UNKNOWN，不据以推余额）。

### 7. 风险与未验证项

- 所有读数只在本仿真、本组占位参数下成立；T_pred、T_repair、g_motion 等仍为待标定占位；单次回放，不是统计结论；AC-19 每格 n = 12，区间重叠，只证非劣化；基 26 两臂全断轨原因未分析。
- 会话点击在「k 已处理」路径的提交帧读法待裁定（IR-C2-1）；捕获模式 Play 路径未在 Air 上跑过（阶段 B 未签 = 0），AC-22…26 未执行。
- 合成滚转 live 推理经同一已加载模型（原始帧缓存在 MPS 上推理）；两臂一致，未与纯 CPU 推理比较。
- C1-1 的同帧对齐在真实关联器上恒成立（快照由同一 `step` 生成），故候选 2 回放读数与候选 1 的差别来自 C1-2 判据与 C1-3 顺序；KF 不合格的 fail-closed 只由替身用例覆盖。

### 8. 四项稳定停点自证（workflow §4.3.1）

| 条件 | 自证 | 指针 |
|---|---|---|
| 1 实现范围和接口已冻结 | **成立**：候选 2 代码/测试冻结于 `9bb0430`（其后只有证据、账本与状态板）；返工只修 C1-1…C1-5 与预复核关注项中的合同义务，未改接口闭集、门值、剧本、参数或信封；新读法 IR-C2-1…5 已列待裁定 | §0；§1；§5.2 |
| 2 相称的实现者测试/编译通过 | **成立**：每条阻断修复都有修前红/修后绿具名回归；停点全套一次，本项新增回归失败 0（基线 61、IR-2 预期 1 分列）；候选 2 正式回放 AC-17 PASS、AC-18 九项可评全 PASS、AC-19 六格非劣化 | §0；§2；§6；`docs/evidence/P1-ENG-CAPTURE-001-replay.md` |
| 3 已知 Unity 失败已修复 | 不适用（阶段 A 零 Unity；不记 UNITY_NA） | — |
| 4 复核文件、状态板、候选 commit、未验证风险已更新 | **成立**：本文件、replay.md、tests.log、focused.log、账本已更新并提交推送；状态板交接行交 Acceptance `C2@K1K2K3K4`；风险见 §7；完整候选 diff 见文首 | 状态板交接行；§7 |

结论：**候选 2 到达稳定停点，交 `C2@K1K2K3K4`**（本停点核对退回已用尽；IR-C2-1…5 请裁定，未决关注照交新鲜上下文 `R1@K1K2K3K4`）。AR1-2/3/6 具名缺口的独立核实属复核；未经复核不记 DONE。
