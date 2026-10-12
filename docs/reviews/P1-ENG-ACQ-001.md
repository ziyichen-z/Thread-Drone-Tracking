# P1-ENG-ACQ-001 独立复核（指针式快层与换目标捕获，engineering-v1，停点 `K1K2K3`）

角色：复核（review，Claude Code，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-ACQ-001-R1-20260929T173236Z-6a0e`，`requested.round = R1@K1K2K3`）。
轨道：提案抬头逐字 `Workflow: engineering-v1`，接受角色在「§4.2(a) 接受处置」`ACCEPTED` 时逐字裁定生效 → 按 `docs/engineering-workflow.md` 复核；依据列仍写 `BC-n`，读作任务合同第 n 条验收项 `AC-n`。
零消耗：不做检测推理、不加载 YOLO 权重、不跑序列回放（`CarrierSelfTest`、`ResidentCarrierReplay` 未跑，理由见 §0）、不 Play、不访问 5060、不生成任何 ID；只重跑 focused 与三个会话级探针（副本内，脚本在会话暂存目录，不入库）。

## R1@K1K2K3（2026-09-29）

### §0 候选、基线与开轮资格

- `round_candidate: 798881e7fcd096c415221dbe87845c14fe635642`（上一实现派发 `…-c5a7` 的 `finished.candidate`；`git diff 798881e..HEAD -- controller tests tools config Assets` 为空，其后提交只有 C2 与 supervisor 登记文档）。
- 全量 diff 基线：本文件此前不存在，无 `passed_candidate`；基线取实现前基线 `3ef75cf`。`git diff --stat 3ef75cf..798881e` 共 42 文件，已逐文件核对（实现文件：`controller/{det_assoc_tracker,gated_publisher,language_bridge,language_loop,pose_gmc,resident_core,track_loop,trackers}.py`、`runtime/README.md`、`.gitignore`、`tools/eng_acq/*` 8 文件、`tests/` 12 文件；其余为证据、状态板、提案、账本与派发日志）。
- 开轮资格：PLAY_GOVERNING（`controller/`、`tools/`、`tests/`）diff 非空 → 开轮。首个复核轮，无上一复核轮候选、无修前红/修后绿义务。
- 停点自证（`docs/evidence/P1-ENG-ACQ-001-K1K2K3-handoff.md`「自证四项」）四项成立：接口已冻结、全套与分组 focused 已跑（新增失败 0）、零 Play、状态板与候选已提交推送；不判 `REVIEW_BLOCKED`。
- 复核副本 `.claude/worktrees/review-P1-ENG-ACQ-001`（detach 于候选）；为让权重/冻结文件校验可用，在副本内建只读符号链接 `outputs/eng-det → 主树 outputs/eng-det`（未写入）。测试树哈希 `HEAD:tests = 66fbebe5d5b0c9e68e83ff52206bbf9e8d801c13`。
- focused 重跑（输出写会话暂存目录，只回显摘要）：
  - 系统 `python3`（3.9.6）`tests.test_trackers tests.test_track_loop tests.test_det_assoc_tracker tests.test_det_assoc_carrier.ResidentCarrierCalls tests.test_resident_core tests.test_pose_gmc` → `Ran 105 … OK (skipped=12)`（跳过 = 库用例）；
  - `.venv-language` `tests.test_language_loop tests.test_language_bridge tests.test_gated_publisher_slew tests.test_track_loop` → `Ran 239 … OK (skipped=2)`；
  - 数据根 `.venv-yoloe`（`cd tests`）`test_det_assoc_tracker test_det_assoc_carrier.ResidentCarrierCalls test_resident_core test_pose_gmc test_eng_acq_e1 test_eng_acq_guards test_eng_acq_windows` → `Ran 97 … OK`。
  - 未跑：`CarrierSelfTest`（真实检测推理，信封检测推理 = 0）与 `ResidentCarrierReplay`（每次计 2 次序列回放，本派发零消耗）。AC-6「载体与线束逐帧一致」本轮以读码核实二者走同一 `ResidentCore.record` + `rows_from_library`（`controller/det_assoc_tracker.py::step` 与 `tools/eng_acq/e2.py::replay_segment` 逐行对照），数值一致性依赖实现者账本记录，未独立复现。
- 证据只读复算（副本内脚本）：`-e1.json` 648 层全 `EVALUATED`、守恒式逐层成立（0 违例）、`not_run` 合计 0、`OUTHIST_*` 合计 0、两臂各 2 次字节一致；扰动臂分位差 0.043514/0.009972/0.006268 ≤ 0.05、`reads_c2_prediction_file=false`；`-e2.json` 27 格、无缺格、`h_sequences_used=false`，a7 位姿自检中位 2.576 px vs 无补偿 95.380 px；账本 `sequence_replays 35/40`、`cpu_wall_s 4352.755/10800`，其余维度 0。AC-11：本人复查主树 `git log --all -S80971838` 仅命中本工作项自身提交（08ac1b1、798881e），本机 `catalog-index.jsonl.gz` sha256 与基线一致；assets 权重/freeze/nanotrack 两件逐字比对、frozen-B/V 按事实 10 前后缀比对。

### §1 逐文件核对摘要

| 组 | 文件 | 结论 |
|---|---|---|
| 常驻核心 | `controller/resident_core.py` | 历史键 = 传感器 `frame_id`、严格递增、深度 ≥ 100、淘汰 FIFO；`select_track`（IR-1）；六值闭集与 `level2.reason` 闭集在 `_finish` 断言；`level2_mapping` 逐事件同 AC-3 接受释义（对照 `controller/reanchor.py::replay_tracker` 的 `head_frame_id` 语义：超时 `frame.frame_id−1`+1 = 首个未处理帧，`invalid_replay_box` 取失败帧）；coasting 第 `coasting_limit` 次 step 转 `TRACK_ENDED`、找回优先（C1 返工成立）。 |
| 插件 | `controller/det_assoc_tracker.py`（全文，含 FAST-002 `compat` 路径，H-7/AC-12） | `compat` 路径 `init/update` 逐字未改（绑定 IoU ≥ 0.5、并列取分数高者再取小 id、从不改绑）；`resident` 方法集互斥、`step` 帧序检查在检测前；`make_resident_associator` 只覆写 `_pre_first_associate`；`apply_pose_warp` 按 BoT-SORT xywh / ByteTrack xyah 分别改写并用雅可比转速度与协方差；`manifest_identity` 增 `mode/history_depth/gmc_source/resolver/level2`，权重/规格/冻结三 sha 不变。未见新缺陷。 |
| 位姿 | `controller/pose_gmc.py` | H = K'₂·R₂ᵀ·R₁·K'₁⁻¹、K' 取 `-fy`（v 向下）；`_inverse_intrinsics` 与雅可比公式逐项核对正确；只读平台位姿。 |
| 载体 | `controller/track_loop.py`、`controller/trackers.py` | 常驻判定（IR-2）、`start` 不调 `init`、逐帧读-处理-发布交替、窗口外逐帧 `publish_skip_reason`、`_look_at_written` 按收据推进基准（IR-22）；旧路径未改；CLI `--tracker` 闭集仍为 `csrt/nanotrack-v2/det-assoc-v1`（常驻只经会话 `--resident`）。**见 R1-3、R1-2。** |
| 发布器 | `controller/gated_publisher.py` | `slew_look_at` 每 `designation_id` 至多一次、写/拒均留收据；`clear_association` 使转向期速度指令 `orphan_control`。 |
| 会话/桥 | `controller/language_loop.py`、`controller/language_bridge.py`、`runtime/README.md` | 九态、三个新原因、`PUBLISHING_STATES`、`designation` 字段校验；跟踪中指定、六值迁移、`_restore_pre_query`（IR-16）、`ACQUIRING` 到位/收养/超时（IR-6/7）；`LanguageWorker` 类零改动（H-1 声明属实）。**见 R1-1、R1-2、R1-4。** |
| 线束 | `tools/eng_acq/{common,data,e1,e2,run,report,cleanup}.py` | 真值只进样本构造与评分（`data.Frame.objects` 只在 `e1.build_samples`/分桶与 `e2` 评分读取；关联器输入为冻结检测缓存，sidecar 无目标真值字段——本人核对三序列 sidecar 键集）；15 桶互斥穷尽、守恒断言、第二级前缀共享与帧上限（SUB:3）、a7 全样本；`follow(None)` 保证样本独立（IR-20）。未见新缺陷。 |
| 测试 | `tests/test_{det_assoc_tracker,det_assoc_carrier,resident_core,pose_gmc,track_loop,gated_publisher_slew,language_loop,language_bridge,eng_acq_e1,eng_acq_guards,eng_acq_windows}.py` | 具名用例存在且对准各 AC；但 `ResidentServoTests` 用 `_RecordingPublisher`（无发布门），会话转向用例未断言收养后的伺服指令，故 R1-2/R1-3 未被覆盖。 |

### §2 AC 逐项与 C2 预复核关注项

| AC | 结论 | 依据 |
|---|---|---|
| AC-1/2/4/5 | 成立 | 读码 + 重跑 `ResidentProtocol`、`History`、`test_pose_gmc`、`ResidentLibrary`。 |
| AC-3/19 | 成立 | `level2_mapping` 逐事件对照；`LevelOne`/`LevelTwo` 全部通过（含 C1 返工三例）。 |
| AC-6 | 结构成立（逐帧数值一致未独立复现，见 §0） | 同一 `ResidentCore` 与行转换；`ResidentCarrierCalls` 通过。 |
| AC-7/8/20 | 成立 | §0 证据复算。 |
| AC-9/10/11/12/16 | 成立 | 账本零维度；H-1/H-2 声明属实；AC-11 查找与基线标签可复查；复核范围逐字列入；清理为「移入废纸篓（可恢复）」。 |
| AC-13 | 成立（迁移与闭集） | `ResidentSessionTests` 8 例。 |
| AC-14 | 成立（至多一次、超时 → `LOST(acquire_failed)` + hold、`orphan_control`、到位与 N-of-M 红绿） | AC-14 未覆盖的 §3.7 世界点外推另见 R1-1。 |
| AC-15 修订 1 | **不成立** | 见 R1-2、R1-3。 |
| AC-17/18 | `NOT_RUN`（Play D1 未签），如实 | 候选声明触及预览内容，Play D1 前须人眼保真。 |

C2 关注项：(1) 首个 `slew_look_at` 用 k 帧世界点 → 确认为缺陷，R1-1；(2) AC-11 查找范围与 `BASELINE_FIXED_PRIOR_UNVERIFIABLE` 标签 → 核实成立；(3) AC-15 拒发收据与限速基准 → `_look_at_written` 实现成立，但基准在转向后失真（R1-2），且追平窗口判定与门 ④ 不同源（R1-3）。

### §3 Findings

| ID | 分级 | 依据 | 阻断 | 摘要 |
|---|---|---|---|---|
| R1-1 | CLASS_2 | `IN_SCOPE_NO_BC` | 是 | 转向指令未用外推世界点 |
| R1-2 | CLASS_2 | `BC-15` | 是 | 转向后伺服限速基准仍是旧目标点，收养后把云台拉回旧方向 |
| R1-3 | CLASS_2 | `BC-15` | 是 | 追平窗口按批首 latest 判定，批内新帧到达即门 ④ `catchup_stale` 终止常驻载体 |
| R1-4 | CLASS_2 | `SCOPE_GAP` | 否（路由接受角色） | k 帧世界点几何被拒时上报 `cause=slew_timeout`（未发转向） |

#### R1-1 转向指令未用外推世界点（`controller/language_loop.py::_begin_acquiring`）

- 合同：§3.7「世界点：k 帧位姿 + 指定框底中点 ∩ 显式水平面；若 k 帧命中轨迹有 ≥ 2 帧历史，用其地面点差分速度 × 经过时间外推（红车），否则静止。发布：`slew_look_at(point, designation_id)`，每个 `designation_id` 至多一次」。
- 实现：`_begin_acquiring` 算出 `velocity` 后仍调用 `self.publisher.slew_look_at(point, designation_id)`，`point` = k 帧未外推点；外推（`_acquire_point`）只用于到位与收养的投影判据。转向每指定只有一次，移动目标的云台因此指向 Δ 秒前的位置，而到位判据要求外推点在画内——对红车（§6(ii) 预注册的主要 `TRACK_ENDED` 情形、§3.10 剧本「切回红车」）结构性地倾向 `slew_timeout`。
- 探针（副本内，`tests/test_language_loop.py` 同一 `Harness`/`FakeResident`）：track 5 逐帧右移 5 帧后被移除，确认 → `ACQUIRING`；`velocity_world_mps = [3.880, 0, 0]`，`time_k = 1.4 s`、历史头 2.6 s；收据 `slew_look_at.point_world_m = [128.120, 0, 117.000]` = `world_point_k`，而头帧外推点 = `[132.776, 0, 117.000]`（差 4.66 m；Δ = 8 s、5 m/s 时约 40 m）。
- 范围判据：可达（§3.7 与 §6(ii)、§3.10 点名）；AC-14 只列至多一次、超时、速度拒绝与到位/收养红绿，未覆盖世界点外推 → `IN_SCOPE_NO_BC`。
- 闭合回归（生产路径，修前必红）：会话级用例（真实 `GatedPublisher` 收据）断言移动目标 `TRACK_ENDED` 确认后 `slew_look_at.point_world_m` = k 帧点 + 速度 ×（发令时历史头仿真时刻 − t_k），静止目标仍为 k 帧点。

#### R1-2 转向后伺服限速基准仍是旧目标点（`controller/track_loop.py::_publish_resident` / `language_loop.py::_begin_acquiring`、`_new_pointer_epoch`）

- 合同：§3.8「相邻两次指令的视线角变化 ≤ ω_max/hz，超出时把指令点沿地面**向目标点**移动到角变化恰为上限处」；AC-15 修订 1「相邻已发指令视线角变化 > ω_max/hz … 均不满足」。
- 实现：`slew_look_at` 直接经发布器写 `gimbal_command.json`，但 `TrackLoop.last_servo_point` 不更新也不清空；`_new_pointer_epoch` 同样不动它。收养成功回到 `TRACKING` 后，首个伺服 `look_at` 以**转向前旧目标**的最后指令点为基准限速，于是从旧点向新目标只走 6°，实际把云台从已到位的转向点拉回旧方向；`ACQUIRE_FAILED`（云台停在转向点）后再次 `BOUND` 也同样从旧点起算。
- 探针（副本内，同一 `Harness`，`_to_acquiring` + 收养 track 9）：旧伺服点 → 转向点视线角 33.544°；收养后首条写入的 `look_at` 距旧伺服点恰 6.000°，距转向点 27.563°（写入的 `gimbal_command.json` 为该点）。即相邻两条已写云台指令（`slew_look_at` → `look_at`）视线角变化 27.6° > 6°，且方向背离已收养目标。
- 范围判据：可达（§3.7 收养 → `TRACKING` → §3.8 伺服是本项主路径，§3.10 剧本逐步使用）→ `BC-15`（AC-15 修订 1 与 §3.8）。
- 闭合回归：会话级用例经 `ACQUIRING` 收养后，断言首条伺服 `look_at` 相对转向指令点的视线角 ≤ ω_max/hz（或朝收养目标单调接近），且 `ACQUIRE_FAILED` 后新 `BOUND` 的首条伺服同样以最后一条已写云台指令为基准。

#### R1-3 追平窗口按批首 latest 判定，与门 ④ 不同源（`controller/track_loop.py::_process_resident/_resident_frame`）

- 合同：AC-15 修订 1「对每个已处理、指针 track 有效、处于现有发布窗口内且能通过现有发布门的帧，恰发一次 `look_at` … 追平时窗口外更旧帧仍逐帧 `step` … 不为该旧帧发 `look_at`；… 向旧帧发令均不满足」；IR-3 读法明写窗口的目的是避免门 ①/④ 判 `catchup_stale`；H-6/§3.4.1「回放结束后到达的帧走常驻 `step` 追平 … 发布最终门五项与 `K_pub` 不变」。
- 实现：`_process_resident` 在批首取一次 `latest`，`_resident_frame` 用 `latest − frame_id ≤ K_pub` 决定是否发布；门 ④ 却在发布时重读 `latest.json`。批内只要 Unity 写出新帧（5 Hz、每帧处理数十毫秒、第二级回放同步阻塞 ≤ `T_replay` 2 s 后必然有积压），批首窗口的最旧帧在发布时已是 `L_w − frame_id > K_pub`，观测被拒 `catchup_stale` → `fatal` → 会话拆掉常驻载体、指针退役、`REINIT_REQUIRED(catchup_stale)`——即 H-6 声称已被常驻机制取代的诊断 6 硬停止。
- 探针（副本内，`FakeResident.step` 在处理到批首 latest−3 时由夹具写出 1 个新帧，模拟 Unity 并发出帧）：TRACKING 下积压 6 帧（批首 latest = 7）后一次 tick：收据 `observation` 帧 5 `PUBLISH_REJECTED(catchup_stale, frame_delta=3)`，随后 `look_at` `PUBLISH_REJECTED(orphan_control)`；会话 `REINIT_REQUIRED/catchup_stale`，`loop=None`。
- 范围判据：可达（Unity 与控制器并发是生产常态；追平由 §3.4.1、IR-3、AC-15 修订 1 点名；第二级回放后必有积压）→ `BC-15`（主），相关 AC-6/H-6。
- 闭合回归：会话级（真实 `GatedPublisher` + 夹具在批内并发写帧）断言：批内新帧到达时不产生 `catchup_stale` 拒绝、常驻载体不被拆除；按发布时最新帧判定落到窗口外的帧逐帧记 `publish_skip_reason` 且不发观测/`look_at`。

#### R1-4 世界点几何被拒时上报 `slew_timeout`（`controller/language_loop.py::_begin_acquiring`）

- 实现：`box_ground_intersection` 抛 `GeometryRejected/ValueError/TypeError`（含 k 帧已被淘汰 → 元数据为空）时调用 `_acquire_failed(acquire, "slew_timeout")`，`designation.acquire.cause = slew_timeout`，但并未发出任何转向。探针（副本内把会话 `maximum_ground_range_m` 调为 1 m 触发几何拒绝）：`LOST/acquire_failed`，`acquire = {status: ACQUIRE_FAILED, cause: slew_timeout}`，`slew_look_at` 收据 0 条。
- 范围判据：在 v1 云台 ≤ 45° 离底、25 m 高度与缺省 `maximum_ground_range_m` 下，框底射线不越地平线；k 帧淘汰需 k→h 与 coasting 合计 > 128 帧（≈ 19 s 以上延迟），生产入口难以从已归档工件产生 → 不可达边界，`SCOPE_GAP`，非阻断，路由接受角色记债（建议 `acquire.cause` 用不冒充转向超时的值，例如 `geometry_rejected`；`acquire` 子对象非闭集，不需改 `STATE_REASONS`）。

### §4 UNITY_NA

本项不申请 `UNITY_NA`（阶段 2 改变运行时行为，Unity 证据 = 另签 Play D1）；复核**附议「不适用 `UNITY_NA`」**。AC-17/18 维持 `NOT_RUN`，不得据此记 `DONE`。

### §5 非 finding 观察（不阻断，仅供实现角色参考）

- 常驻载体重建（`_ensure_resident_loop` 每次新建插件）后 `designation_id` 自 1 重来，会话日志/桥文件内的 `designation_id` 跨载体不唯一；「每 `designation_id` 至多一次转向」按发布器实例计，发布器同时重建，行为上无影响，故未列 finding。
- `--resident` 未配 `--tracker det-assoc-v1` 时 `create_tracker(..., resident=True)` 在首个 tick 抛 `ValueError`（fail-closed 崩溃而非 `CONFIG_MISMATCH` 回执）；CLI 未接入 Play 流程（IR-17），未列 finding。

### §6 Verdict

**`REWORK_REQUIRED`**（`R1@K1K2K3` 第 1 次）。阻断：R1-1、R1-2、R1-3（CLASS_2，直接交回实现角色）；R1-4 `SCOPE_GAP` 非阻断，路由接受角色。修复后**直接回复核 `R2@K1K2K3`，不经核对轮**；R2 对每条阻断 finding 以 `git revert -n <fix>` 做修前红/修后绿。本轮无 `上轮漏检`，不写 `blocks_consuming_gate`。

边界自查：本会话未修改任何实现文件；只写本文件与状态板。

## R2@K1K2K3（2026-09-29）

角色：复核（review，Claude Code，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-ACQ-001-R2-20260929T181913Z-2c7e`，`requested.round = R2@K1K2K3`）。复核返工直接回本角色，不经核对轮；本轮为该停点第 2 个复核轮（此前 `REWORK_REQUIRED` 1 次）。零消耗：零 ID/Play/API/检测推理/权重加载/序列回放/5060；只在副本内重跑 focused、三次 `git revert -n` 红绿与一个会话级探针（脚本在会话暂存目录，不入库；本机 CPU 合计约 15 s，未写入实现者账本）。

### §0 候选、基线与开轮资格

- `round_candidate: 3d228394f561ae24b1206e296696a06ef0635379`（上一实现派发 `…-1d8f` 的 `finished.candidate`）。
- 修复触及行 = `git diff 798881e7fcd096c415221dbe87845c14fe635642..3d22839`（上一复核轮 `round_candidate`）：PLAY_GOVERNING 只有 `controller/gated_publisher.py`（+14/−1）、`controller/language_loop.py`（+9/−1）、`controller/track_loop.py`（+38/−6）、`tests/test_language_loop.py`（+172），逐行已读；四个实现提交各自只改声明文件（922230e：`language_loop.py`；7cf133c：`gated_publisher.py`、`track_loop.py`；264a034：`track_loop.py`；22ed467：测试），3d22839 只改证据/账本/状态板。其余非代码变更（提案、`authorizations.md`、派发日志）归接受角色 C2 与 supervisor 提交，未见实现角色越权。
- 全量 diff：本文件无 `passed_candidate`，基线仍取实现前 `3ef75cf`；`3ef75cf..798881e` 已在 R1 逐文件核对，本轮对全量 diff 的增量即上条。
- 开轮资格：PLAY_GOVERNING diff 非空 → 开轮。停点自证四项（交接「自证四项」）成立，不判 `REVIEW_BLOCKED`。
- 副本 `.claude/worktrees/review-P1-ENG-ACQ-001`（detach 于候选），为冻结文件校验建只读符号链接 `outputs/eng-det`（未写入）。测试树哈希 `HEAD:tests = bd79373e4f2982087f46954ec3fc275159193940`。
- focused 重跑（输出写会话暂存目录，只回显摘要）：
  - 系统 `python3`（3.9.6）`tests.test_trackers tests.test_track_loop tests.test_det_assoc_tracker tests.test_det_assoc_carrier.ResidentCarrierCalls tests.test_resident_core tests.test_pose_gmc` → `Ran 105 … OK (skipped=12)`；
  - `.venv-language` `tests.test_language_loop tests.test_language_bridge tests.test_gated_publisher_slew tests.test_track_loop` → `Ran 243 … OK (skipped=2)`；
  - 数据根 `.venv-yoloe`（`cd tests`）七模块 → `Ran 97 … OK (skipped=8)`。8 个跳过均为 `test_det_assoc_tracker` 库用例（`LibrarySemantics` 7 + `ResidentLibrary` 1），原因是本机 `.venv-yoloe` 当前导入 `lap` 失败（`ModuleNotFoundError`），属环境，不是实现缺陷；这些用例覆盖的 `controller/det_assoc_tracker.py` 在本轮修复触及行之外（自 R1 候选未改）。实现者日志同组记 97 OK 无跳过，差异如实记录。
  - 未跑：`CarrierSelfTest`（真实检测推理）、`ResidentCarrierReplay`（计序列回放）。本人核实二者不受本轮修复影响：常驻窗口只在会话 `_ensure_resident_loop` 设置（`resident_publish_window=self.receipt.k_pub`），线束 `tools/eng_acq/` 不导入 `track_loop`/`gated_publisher`/`language_loop`；窗口为 `None` 时 `_resident_frame` 不重读、`publish` 恒真、机身步条件与原先相同；`RuntimePublisher` 无 `last_gimbal_point_world_m` 属性，`_servo_baseline` 退回 `last_servo_point`。
- E1/E2 不重跑：同上，修复不在线束路径上；同意交接「E1/E2 不重跑（理由）」。

### §1 旧 finding 闭合（修前红/修后绿，副本内逐个 `git revert -n <fix>` → 跑四条新回归 → `git reset --hard` 恢复；`.venv-language`）

| Finding | 修复 | 回归（`tests/test_language_loop.py::ResidentSessionTests`） | revert 后 | 候选 | 结论 |
|---|---|---|---|---|---|
| R1-1 | 922230e | `test_acquiring_slew_point_extrapolated_for_moving_target` | 仅该例 FAIL：`128.1202067673083 != 129.2841447371158`（收据仍是 k 帧点） | 4 例 OK | **闭合** |
| R1-2 | 7cf133c | `test_acquiring_servo_baseline_follows_slew_command` | 仅该例 FAIL：`27.563252666500073 not less than or equal to 6.000001` | 4 例 OK | **闭合** |
| R1-3 | 264a034 | `test_resident_catchup_new_frame_mid_batch_not_stale`、`test_resident_catchup_batch_end_pushed_out_skips_body_step` | 两例 FAIL：批内 `observation` `PUBLISH_REJECTED(catchup_stale)` | 4 例 OK | **闭合** |

三次 revert 均无冲突，每次只有对应回归变红，互不串扰。闭合四条件：(1) fixture 走生产路径——真实 `GatedPublisher` 写收据与 `gimbal_command.json`、`FixtureFramePublisher` 写生产格式帧包与 `latest.json`（R1-3 的并发帧也经它写出），跟踪器替身内核是真实 `ResidentCore`，与 R1 写明的闭合口径一致；(2) 本轮红绿已核；(3) 修复未触及 Play 治理门（`analyze_m3_body.py`、`preflight_reanchor_env.py`、`controller/run_log.py`）；(4) 不适用。

逐条读码：

- R1-1：`_begin_acquiring` 以发令时 `core.head_frame_id` 的历史条目 `simulation_time_s` 调同一 `_acquire_point`，转向点 = k 帧点 + 地面差分速度 ×（t_head − t_k）；无速度、无头条目或无 t_k 时退回 k 帧点。时间轴与 `_acquire_step` 的到位/收养判据相同（仿真时刻），只读帧元数据，无真值。`designation.acquire` 键集未变（`_update_designation_acquire` 键表未改），新增 `slew_time_s`/`slew_point_world_m` 只进会话日志 `acquire_started`。读法与 R1 写明的闭合口径逐字一致。
- R1-2：`GatedPublisher.last_gimbal_point_world_m` 只在伺服 `look_at` 本次收据为 `WRITTEN` 与 `slew_look_at` 写入后推进；拒绝、静音、`slew_repeated` 与写异常不推进。`_servo_baseline` 取该值（`None` 即无基准），无此属性的发布器退回 `last_servo_point`（IR-22 不变）。收养后与 `ACQUIRE_FAILED` 后新 `BOUND` 两条路径都已由回归钉住。
- R1-3：`_resident_frame` 在该帧 `step`/`pointer_result` 之后、`_publish_resident` 之前经 `_publish_time_latest` 重读门 ④ 所读同一文件（会话 `repository.frames_directory/latest.json`；只增不减，读失败退回批首值），据之判定窗口；窗口外帧照常 `step` 并逐帧记 `publish_skip_reason`；批末帧被挤出窗口时本批不做机身步。门 ①–⑤、`K_pub`、门拒 fatal 处理未改。会话停帧判据按「本批处理帧数」计进度（`_advance_resident`），跳过发布不会误判 `frame_stall`。

### §2 修复触及行复查与 AC

- 修复触及行上**未发现新的 CLASS_1/2**；无 `RED_LINE`（转向点、限速基准与窗口判定只用帧元数据中的平台位姿、仿真时刻与 `latest.json`，未接触 Unity 真值）。
- AC-15 修订 1：R1-2、R1-3 闭合后，指定纪元内（含转向 → 收养、`ACQUIRE_FAILED` → 新 `BOUND`）已成立；**常驻载体重建跨界**不成立，见 R2-1（未改动行，`上轮漏检`，不阻断本轮）。AC-14 与 §3.7 世界点外推：R1-1 闭合后成立。其余 AC 结论同 R1 §2（本轮未触及）。AC-17/18 仍 `NOT_RUN`。
- IR-23（批内窗口判定与门 ④ 两次读之间的毫秒级残余竞态）：本人核实该残余存在，且在现行合同下无法只靠实现消除——AC-15 修订 1 要求窗口内且能过门的帧恰发一次、门 ①④ 条件与失败处理不变；把窗口收窄一帧会漏发 `K_pub` 边缘帧，吞掉门拒又改变失败处理，二者都是合同口径变化。故不列 finding，R1-3 按其闭合口径闭合；**附议交接受角色裁定**。风险只出现在追平批的窗口边缘帧（帧差恰为 `K_pub = 2`），且观测门与 `look_at` 门各有一次；结果是 fail-closed 的 `REINIT_REQUIRED(catchup_stale)`，不发错误指令。建议在 Play D1 前裁定，并在 D1 记录 `catchup_stale` 次数。
- IR-24：本人探针确认它是 AC-15 修订 1 的实际违例，列为 R2-1（下节）；实现者已披露，归属判定见 R2-1。

### §3 Findings（本轮新增）

| ID | 分级 | 依据 | 阻断 | 摘要 |
|---|---|---|---|---|
| R2-1 | CLASS_2 | `上轮漏检` | 否（未改动行；阻断下一个消耗性门） | 常驻载体重建后限速基准丢失，新 `BOUND` 首条伺服相对上一条已写云台指令不限速 |

#### R2-1 常驻载体重建后限速基准丢失（`controller/language_loop.py::_ensure_resident_loop`）

- 合同：AC-15 修订 1「相邻已发指令视线角变化 > ω_max/hz … 均不满足」；§3.8「相邻两次指令的视线角变化 ≤ ω_max/hz」；§3.6 表「`IDLE`/`LOST`/`REINIT_REQUIRED` | `confirm` → 同上」点名重建后的再指定路径；IR-4（C1 已裁定）点名回退/缺帧/门拒/停帧时拆载体、下一 tick 从最新帧重建。
- 实现：`_ensure_resident_loop` 每次新建 `GatedPublisher`（`last_gimbal_point_world_m = None`）与 `TrackLoop`（`last_servo_point = None`），不承接上一载体最后一条已写云台点；`_servo_baseline` 返回 `None`，`servo_clamp` 不限速。`gimbal_command.json` 是会话唯一的云台通道，重建前后两条已写指令在通道上相邻（重建与 `REINIT_REQUIRED` 期间没有其他云台写入）。
- 探针（副本内，同一 `Harness`/`FakeResident`，监听 `RuntimePublisher.look_at` 的实际写入序列）：track 1 在 `BOX_A` 跟踪中 → 删一个中间帧制造 `frame_gap` → `REINIT_REQUIRED`、载体拆除 → 下一 tick 重建（`resident_loops_started` 1→2）→ `ask`/`confirm` 指定 `BOX_B` 上的 track 2 → `TRACKING`。旧载体最后一条已写点 `[128.120, 0, 117.000]`，新载体首条已写点 `[114.347, 0, 129.221]`，视线角 **33.544°**，上限 6°。
- 范围判据：可达——重建由 IR-4 的生产事件触发（缺帧、门拒含 IR-23 残余、停帧），重建后再指定是 §3.6 表列路径 → CLASS_2。R1 已审过 `_ensure_resident_loop` 与限速基准，当时漏检；本轮修复没有改动这些行（R1 候选里 `last_servo_point` 同样随 `TrackLoop` 重建清空，行为不变），因此依据列填 `上轮漏检`，不阻断本轮，改为阻断下一个消耗性门（Play D1）。
- 闭合（二选一，由接受角色定）：(a) 实现修复——重建时把上一载体最后一条已写云台点交给新发布器（实现者 IR-24 的建议），配会话级回归：制造 `frame_gap` → 重建 → 再指定远处目标，断言首条伺服相对上一条已写云台点 ≤ ω_max/hz，修前必红；本角色在下一复核轮以红绿核实后写 release；(b) 接受角色裁定 IR-24 为可接受边界，改标 `SCOPE_GAP`，在 `docs/implementation-status.md` 账本记 `RELEASED_SCOPE_GAP`（视同 release；此后 `R2-1` 不得再次 block）。

blocks_consuming_gate: R2-1

当前 Active handoffs 没有 `Consuming = yes` 的行，本提交无须暂停任何交接；此行会让 `tools/check_docs.py` 拒绝在 release 前开启任何未暂停的消耗性交接（含 Play D1）。

### §4 未闭与路由

- R1-4（`SCOPE_GAP`，非阻断）：本轮未修，状态不变，仍待接受角色在「范围外已知缺陷」账本记债。
- IR-23：附议交接受角色裁定（§2）。IR-24：并入 R2-1 的闭合选择。IR-19（冻结路径测试）仍待接受角色裁定，不属本轮。
- §5 观察（R1）未处理，仍为非 finding。

### §5 UNITY_NA

本项不申请 `UNITY_NA`；复核**再次附议「不适用 `UNITY_NA`」**。本轮通过不等于 `DONE`：AC-17/18 `NOT_RUN`，Play D1（另签信封 + 人眼保真 ≥ 2 张）与 R2-1 release 是后续前提。

### §6 Verdict

Verdict: PASS_WITH_NOTES
passed_candidate: 3d228394f561ae24b1206e296696a06ef0635379

R1-1、R1-2、R1-3 均以修前红/修后绿闭合；修复触及行上没有新的 CLASS_1/2 或 `RED_LINE`。附注：R2-1（`上轮漏检` CLASS_2，已写 `blocks_consuming_gate`，release 前不得开 Play D1 等消耗性门）；IR-23 附议交接受角色裁定；R1-4 `SCOPE_GAP` 待记债。交接受角色：裁定 R2-1 走 (a) 还是 (b)，裁定 IR-23/IR-24/IR-19，为 R1-4 记债；Overall 与 Lifecycle 由接受角色维护。

边界自查：本会话未修改任何实现文件；主工作树只写本文件与状态板；副本内的 `git revert -n` 均已 `git reset --hard` 恢复，副本收工删除。

## R3@K1K2K3（2026-09-29）

角色：复核（review，Claude Code，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-ACQ-001-R3-20260929T185832Z-9e15`，`requested.round = R3@K1K2K3`）。复核返工直接回本角色，不经核对轮；本轮为该停点第 3 个复核轮（此前 `REWORK_REQUIRED` 1 次 = R1，R2 为 `PASS_WITH_NOTES`），未触发 COORD-009 (c) 冻结。零消耗：零 ID/Play/API/检测推理/权重加载/序列回放/5060；只在副本内重跑 focused 与一次 `git revert -n` 红绿（本机 CPU 合计约 10 s，未写入实现者账本）。

### §0 候选、基线与开轮资格

- `round_candidate: 3a2f583c9d5961ce996557671d8c85128b18eee6`（上一实现派发 `…-7a42` 的 `finished.candidate`）。
- 上一复核轮候选 = 上一通过候选 = `3d228394f561ae24b1206e296696a06ef0635379`（R2 §0/§6）。修复触及行 = `git diff 3d22839..3a2f583`：PLAY_GOVERNING 只有 `controller/language_loop.py`（+10，`LanguageSession.__init__`、`_ensure_resident_loop`、`_teardown_resident` 三处）与 `tests/test_language_loop.py`（+58，一条回归），逐行已读。实现提交 2b50cf6 只改 `language_loop.py`、3363eb2 只改该测试、3a2f583 只改证据/账本/状态板；区间内其余提交为 R2 复核文件、接受角色处置（提案、`implementation-status.md` R1-4 记债与通过轮消费节）与 supervisor 登记/代录（`authorizations.md`、派发日志），未见实现角色越权。交接「复核范围（`R3@K1K2K3`）」声明与实际 diff 一致。
- 开轮资格：PLAY_GOVERNING diff 非空 → 开轮。停点自证四项（交接「自证四项」）成立，不判 `REVIEW_BLOCKED`。
- 副本 `.claude/worktrees/review-P1-ENG-ACQ-001`（detach 于候选），为冻结文件校验建只读符号链接 `outputs/eng-det`（未写入）。测试树哈希 `HEAD:tests = b2bc6606d48869d7f14a846e452fe4641bd27727`。
- focused 重跑（输出写会话暂存目录，只回显摘要）：
  - 系统 `python3`（3.9.6）`tests.test_trackers tests.test_track_loop tests.test_det_assoc_tracker tests.test_det_assoc_carrier.ResidentCarrierCalls tests.test_resident_core tests.test_pose_gmc` → `Ran 105 … OK (skipped=12)`；
  - `.venv-language` `tests.test_language_loop tests.test_language_bridge tests.test_gated_publisher_slew tests.test_track_loop` → `Ran 244 … OK (skipped=2)`（较 R2 多 1 例 = 本轮新回归）；
  - 数据根 `.venv-yoloe`（`cd tests`）七模块 → `Ran 97 … OK (skipped=8)`；8 个跳过仍为 `test_det_assoc_tracker` 库用例（本机 `.venv-yoloe` 导入 `lap` 失败，环境问题，同 R2 所记），覆盖文件不在本轮修复触及行内。
  - 未跑 `CarrierSelfTest`/`ResidentCarrierReplay`、E1/E2 不重跑：修复只在会话层常驻载体拆除/重建路径，`tools/eng_acq/` 不导入 `language_loop`，载体 `step`/`pointer_result`/发布路径未改；同意交接「E1/E2 不重跑（理由）」。

### §1 R2-1 闭合（修前红/修后绿；副本内 `git revert -n 2b50cf6` → 跑 `ResidentSessionTests` → `git reset --hard` 恢复 → 再跑；`.venv-language`）

| Finding | 修复 | 回归（`tests/test_language_loop.py::ResidentSessionTests`） | revert 后 | 候选 | 结论 |
|---|---|---|---|---|---|
| R2-1 | 2b50cf6 | `test_resident_rebuild_servo_baseline_carries_last_written_gimbal_point` | 22 例中仅该例 FAIL：`33.54443408552766 not less than or equal to 6.000001`（与 R2 探针 33.544° 一致） | 22 例 OK（含 R1-1/2/3 四条回归） | **闭合** |

revert 无冲突，只改 `controller/language_loop.py`（−10）。闭合四条件：(1) fixture 走生产路径——真实 `LanguageSession`、`GatedPublisher`、`RuntimePublisher` 写桥与收据，`FixtureFramePublisher` 写生产格式帧包，`frame_gap` 由删除中间帧文件经生产检测触发，重建经会话 `_ensure_resident_loop`；监听的是 `RuntimePublisher.look_at` 实际写入序列（含转向通道），并以收据 `look_at_world_m` 交叉绑定首条伺服；(2) 本轮红绿已核；(3) 未触及 Play 治理门（`analyze_m3_body.py`、`preflight_reanchor_env.py`、`controller/run_log.py`）；(4) 不适用。回归非空转：断言重建与再指定期间无其他云台写入（通道相邻前提）、该帧直接地面点相对旧点 > 12°、首条角度 > 5.9°（确被限速到上限处）。

逐行读码（修复触及行）：

- `_teardown_resident`：`finalize()` 后从旧发布器取 `last_gimbal_point_world_m`，非 `None` 才覆盖会话级 `_last_gimbal_point_world_m`；`finalize` 不清该属性，取值即旧载体最后一条 `WRITTEN` 云台点（伺服 `look_at` 或 `slew_look_at`，R1-2 语义）。拆除入口（缺帧/回退/门拒/停帧/段终/stop）都经此函数，`_finalize_segment` 的常驻分支也转到这里。
- `_ensure_resident_loop`：新 `GatedPublisher` 构造后立即赋值，`TrackLoop._servo_baseline` 读到元组即作基准；首个载体为 `None`，与修前相同。`loop.start` 失败分支 `finalize` 的新发布器未写云台，会话值不变，下次重建仍承接同一点——正确。
- 发布门 ①–⑤、`K_pub`、`slew_look_at` 至多一次、失败处理均未改；只读发布器自身记录的已写点，无 Unity 真值 → 无 `RED_LINE`。

### §2 修复触及行复查与 AC

- 修复触及行上**未发现新的 CLASS_1/2**；无 `RED_LINE`；无旧 finding 闭合失败；未改动行上无新增 `上轮漏检` CLASS_1。
- AC-15 修订 1：R2-1 闭合后，常驻载体重建跨界的「相邻已写云台指令视线角 ≤ ω_max/hz」成立；指定纪元内部分同 R2 §2。其余 AC 结论同 R1/R2（本轮未触及）。AC-17/18 仍 `NOT_RUN`。
- IR-23 已由接受角色接受为具名残余边界（提案「R2@K1K2K3 通过轮消费与 R2-1 处置」），本轮不重开。

### §3 Findings（本轮新增）

无。

releases_consuming_gate: R2-1

（与 R2 §3 的 `blocks_consuming_gate: R2-1` 按文件顺序配对；依据 = §1 修前红/修后绿与修复触及行读码。release 只解除本 finding 对消耗性门的阻断，不等于 Play D1 获授权：D1 仍须用户另签信封并先完成人眼保真。）

### §4 非 finding 观察（不阻断）

- `nadir` 条件：常驻 `start` 会 `set_nadir()` 写云台，此时承接的旧点已不是通道上相邻的上一条已写指令；但 `nadir` 下 `_publish_resident` 不发伺服 `look_at`，基准不被使用，行为无影响，故不列 finding。若将来在 `nadir` 下启用伺服，基准应随 `set_nadir` 失效。
- 承接的基准点在 `REINIT_REQUIRED` 期间保持不变；视线角以新帧相机位置为原点计算，与载体内的既有 §3.8 语义相同。
- R1 §5 两条观察仍未处理，仍为非 finding。

### §5 未闭与路由

- R1-4（`SCOPE_GAP`）已由接受角色在「范围外已知缺陷」账本记债（`OPEN`），不属本轮。
- IR-19/23/24 已由接受角色裁定；无新增待裁定。

### §6 UNITY_NA

本项不申请 `UNITY_NA`；复核**再次附议「不适用 `UNITY_NA`」**。本轮通过不等于 `DONE`：AC-17/18 `NOT_RUN`，Play D1（另签信封 + 人眼保真 ≥ 2 张）是后续前提。

### §7 Verdict

Verdict: PASS_WITH_NOTES
passed_candidate: 3a2f583c9d5961ce996557671d8c85128b18eee6

R2-1 以修前红/修后绿闭合并已写 `releases_consuming_gate: R2-1`；修复触及行上没有新的 CLASS_1/2 或 `RED_LINE`。附注：§4 非 finding 观察；R1-4 `SCOPE_GAP` 债仍 `OPEN`；IR-23 残余按接受裁定在 Play D1 记录 `catchup_stale`。交接受角色消费本轮；Overall 与 Lifecycle 由接受角色维护。

边界自查：本会话未修改任何实现文件；主工作树只写本文件与状态板；副本内 `git revert -n` 已 `git reset --hard` 恢复，副本收工删除。

## R1@K1K3（2026-09-29）

角色：复核（review，Claude Code，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-ACQ-001-R1-20260929T222243Z-5804`，`requested.round = R1@K1K3`）。新停点 `K1K3`（提案「candidates 后端接线窄范围修复 CLARIFY」：AC-21 / B1–B3，AC-18 修订 3 本批就绪部分）的第 1 个复核轮；与 `K1K2K3` 分开计数。零消耗：零 ID/Play/API/VLM/检测推理/YOLO 权重加载/序列回放/5060 与 Unity 主机访问；只在副本内重跑 focused、一次旧控制器红绿与一个零消耗探针（脚本在会话暂存目录，不入库）。

### §0 候选、基线与开轮资格

- `round_candidate: 742adf0b8fac83d885729edd95d4bdcc94044988`（派发候选；按提案「预复核关注项与 R1@K1K3 交接」运行时解析：主题 `P1-ENG-ACQ-001 K1K3 停点自证…` 的最后一笔实现提交，其前一笔为 `…candidates 后端接线 B1–B3 窄修`）。`git diff 742adf0..HEAD -- controller tests tools config Assets` 为空，其后只有 C1 与 supervisor 登记文档。
- 全量 diff 基线 = 本文件最近一行 `passed_candidate`（R3@K1K2K3 §7）= `3a2f583`。`git diff 3a2f583..742adf0` 上 PLAY_GOVERNING 只有 5 个文件，全部来自实现提交 09abf55：`controller/language_bridge.py`（+25/−4）、`controller/language_loop.py`（+131/−5）、`tools/eng_acq/candidates_preflight.py`（新，238 行）、`tests/test_language_bridge.py`（+27）、`tests/test_language_loop.py`（+234/−2），已逐行读。742adf0 只改证据、操作单与状态板。区间内其余提交为接受角色 CLARIFY/裁定、supervisor 代录（`authorizations.md`、派发日志）与此前的样帧/操作单准备提交，均不含 PLAY_GOVERNING。交接「复核范围」声明与实际 diff 一致。
- 开轮资格：PLAY_GOVERNING diff 非空，开轮。停点自证四项（交接「自证四项」）成立，不判 `REVIEW_BLOCKED`。
- 副本 `.claude/worktrees/review-P1-ENG-ACQ-001`（detach 于候选）。测试树哈希 `HEAD:tests = dabaf2291c6b6620a7ccb6e2dd7551d31624a27c`。
- focused 重跑（输出写会话暂存目录，只回显摘要）：`.venv-language` `tests.test_language_loop tests.test_language_bridge tests.test_language_k_binding tests.test_language_selector tests.test_gated_publisher_slew tests.test_track_loop` → `Ran 324 … OK (skipped=4)`，与交接一致。未跑 `.venv-yoloe` 跟踪器/载体用例（`CarrierSelfTest` 做检测推理、`ResidentCarrierReplay` 回放序列，本信封均为 0；本批未改 `det_assoc_tracker`/`resident_core`/`trackers`/`track_loop`），同意交接理由。
- 旧控制器红绿（非阻断 finding 不强制，作测试非空转抽查）：副本内 `git checkout 3a2f583 -- controller/` 后跑 5 条 `CandidatesBackendWiringTests` 和桥 B3 用例 → 6 例全 ERROR；恢复 `742adf0` 后 → 6 例 OK。与交接「head 6 条全红 / full 全绿」一致；逐缺陷 minusB1/B2/B3 以交接红绿日志为准，本轮没有重做。
- 预检 CLI 零消耗核对（临时 runtime/out-dir，缺省 R=128）：`-m tools.eng_acq.candidates_preflight` 退出码 0、`verdict=OK`；`--samples 99` 被参数校验拒绝。

### §1 AC-21 逐项（依据列 `BC-21` 读作 AC-21）

- **B1**：`resolve_model_form` 在 `_run_session` 第一行执行，早于共享 runtime 判断、读收据、`_build_adapter` 和建会话目录。省略 `--model-form` 时，`candidates` 取 `detector-tracks`，其余后端仍取 `c2-merged`（原缺省不变）。交叉形态、非 `det-assoc-v1`、缺 `--resident` 均抛 `CONFIG_MISMATCH`。`_build_adapter` 对 `candidates` 构造真实 `CandidatesBackend()`，零模型。replay 收据配 `--backend candidates` 时，`arguments.backend != receipt.backend` 在会话前拒绝，replay 免校验路径不能替代。**满足。**
- **B2**：`KReceipt.from_document` 拒绝交叉形态，并拒绝 `candidates` 的非有限或负 p95。`_validate_candidates_source` 依次核对：`host=mac`；`model_identity` 逐字等于三字段；`source_reports` 恰为 `{mac}`；报告字节 SHA；报告 `host=mac` 且 `verdict=OK`；机器名；后端/形态/身份/hz/R/p95 与收据逐项相等；`p95_s` 有限且 ≥0；两组各 ≥100 样本、最近秩 p95 可复算、`p95_s` 取两组较大值；资格式。CLARIFY「还须验证…」所列各项均已落实。`LanguageSession.__init__` 的适配器身份与收据比对在 `candidates` 下同样生效。生效场景 R/hz 检查点位于建会话目录之后、任何桥写入与会话锁之前，同读法 6。VLM 双报告分支未改（测试确认单份 `mac` 报告仍被拒）。**满足**；PR-1 见 §3。
- **B3**：`require_backend_model_form` 把 `candidates`⇔`detector-tracks` 设为成对闭集，原 3×3 组合保持不变。`_validate_model_block` 同时服务写盘（`result_payload`）与读回（`read_result`）。`_emit_result` 的 model 块取适配器 identity，未改。B3 会话用例走真实 `LanguageSession` 的 ask→`LanguageWorker`→结果写盘→`read_result`→预览→confirm→`BOUND`；候选逐一等于 N 帧 `tracked` 历史的面积降序。**满足。**
- **K1 时间语义**：`K_ret/K_conf/K_pub` 仍由收据 p95/hz 在 `from_document` 自洽校验，截止检查点未改。预检 `hz`/`R` 与会话都用 `read_scenario` 读同一生效配置（`scenario_config_path=None`）。**K3**：`CandidatesBackend.predict_one` 的选框规则未改，identity 只改为引用同值常量。无 Unity 真值进入候选、收据或预检（预检只用合成行与合成帧名，不读图）→ 无 `RED_LINE`。
- **AC-18 修订 3（本批部分）**：操作单 §2.7、§3 附注、§4 T1 与修复候选的 CLI 一致（T1 省略 `--model-form`，收据路径与预检 `--out-dir` 一致）。Play 未运行，仍 `NOT_RUN`。

### §2 读法 1–6 与交接「未验证项」

- 读法 1–6 已由接受角色裁定接受，与代码一致，本轮不重开。
- 交接「未验证项与已知限制」如实：正式收据只能在 Unity 主机生成，本机夹具不代表该机；p95 只覆盖适配器；`.venv-yoloe` 用例未跑；R1-4 `SCOPE_GAP` 不在本批范围。

### §3 Findings（本轮）

#### K1K3-R1-1 单宿主报告未绑定代码版本（PR-1 的 `environment.git_head` 部分）｜`SCOPE_GAP`｜非阻断，路由接受角色

- 事实（副本零消耗探针核实）：`_validate_candidates_source` 从不读报告 `environment.git_head`。预检工具在另一个 HEAD 生成的报告（改 `git_head` 后用生产 `build_receipt` 重出收据，SHA 自洽）会被 `validate_measurement_sources` **接受**。操作单 §3 附注写「§2.7 的收据须由本机在当前 HEAD 下生成」，但 §2.7 回传的 `run` 摘要（键：`machine_name/hz/retained_frame_count/p95_s/qualifies/verdict/group_p95_s/report/receipt/receipt_sha256`）和第三条命令（只打印收据字段）都**不含** `git_head`，§3 命令也不读报告。接受角色照现稿无法凭回传输出核实这一条。
- 不可达的理由（依据列取 `SCOPE_GAP`）：预检工具与 `candidates` 单宿主分支从本候选才出现，所以任何合法报告都由本候选代码生成。§3 已要求 HEAD 的实现代码等于 `passed_candidate`，此时「由另一版本适配器生成的报告」在本候选下产生不出来。CLARIFY「经 C1/R1 通过后本地生成」中的时间条件，代码本来就无法判定（同一 SHA 在通过前后生成的报告不可区分），属于程序性核对；AC-21 列举的会话前拒绝项（身份/宿主/R/hz/报告 SHA）都已落实。影响上限也很小：p95 只覆盖适配器，本机实测为微秒级，`K_ret = ceil(p95·hz)+2` 在 p95 < 0.2 s（5 Hz）时恒为 3。
- 何时变可达：之后任一候选改动 `CandidatesBackend`/预检工具，而 Unity 主机沿用旧报告时。建议（供接受角色裁定，本角色不改文件）：(a) 记入「范围外已知缺陷」账本；(b) 下次实现角色触及操作单时，在 §2.7 第三条命令后加一条打印报告 `environment.git_head` 的只读命令，供 §3 与 `git rev-parse HEAD` 对照。例如 `<PY> -c "import json; print('report git_head:', json.load(open('outputs/eng-acq/P1-ENG-ACQ-001/play-d1/k-receipt/candidates-mac-report.json'))['environment']['git_head'])"`。或 (c) 以后的候选在 `_validate_candidates_source` 比较 `git_head` 与当前 HEAD。

**PR-1 其余部分（不列 finding）**：`groups.*.tracked_rows` 与 `status_mismatches` 未被校验。但生产预检里只要 `status_mismatches > 0`，报告就是 `verdict=FAIL`，已被 `verdict == "OK"` 拒绝；`tracked_rows` 由工具固定为 0/8。要让「`OK` 且组构成不实」的报告通过，只能手改报告再重算收据 SHA，这是伪造，CLARIFY 已明令禁止（「不得…只改 JSON 字段」）。再多的内容校验也挡不住同样可伪造的字段，所以没有可达缺陷。

### §4 非 finding 观察（不阻断）

- 手写的畸形报告（如 `groups` 为列表）在 `_validate_candidates_source` 抛 `AttributeError`，不在 `except (OSError, ValueError, KeyError, TypeError)` 之内，所以以 traceback 退出，而不是 `CONFIG_MISMATCH`。它仍在建会话目录之前失败（fail-closed），且只能由手写报告触发。VLM 分支是同样的既有写法。
- 组样本数不等于 `sample_count` 时报错文案为「too few samples」，只是措辞，不影响拒绝。
- macOS 的 `platform.node()` 可能随网络或共享名变化；变化时启动前 `CONFIG_MISMATCH`，按操作单 T1 说明回 §2.7 重做即可，fail-closed。
- R ≥ 1500 是 Play 信封条件，由操作单 §3 检查，代码不强制（测试合法使用 R=128），与 CLARIFY 分工一致。

### §5 未闭与路由

- K1K3-R1-1（`SCOPE_GAP`）交接受角色：记债或按 §3 建议裁定。
- R1-4（`SCOPE_GAP`）账本 `OPEN` 不变，不属本轮。
- 本轮无 `上轮漏检`/`上游漏检`，不写 `blocks_consuming_gate`。

### §6 UNITY_NA

本项不申请 `UNITY_NA`；复核**附议「不适用 `UNITY_NA`」**。本轮通过不等于 `DONE`。AC-18 仍 `NOT_RUN`：正式收据须由用户在 Unity 主机按操作单 §2.7 生成，并经接受角色按 §3 / workflow §4.5 放行后才能 Play。

### §7 Verdict

Verdict: PASS_WITH_NOTES
passed_candidate: 742adf0b8fac83d885729edd95d4bdcc94044988

AC-21 的 B1/B2/B3 经读码与 focused 重跑（324 例 OK）成立；K1/K3 语义无新 CLASS_1/2，无 `RED_LINE`。PR-1 已核实：`git_head` 未绑定，记 K1K3-R1-1 `SCOPE_GAP`，非阻断、路由接受角色；组构成部分不可达，不列 finding。交接受角色消费本轮；Overall 与 Lifecycle 由接受角色维护。本机不放行 Unity 主机预检或 Play，放行按提案与操作单 §3 由接受角色执行。

边界自查：本会话未修改任何实现文件。主工作树只写本文件与状态板。副本内 `git checkout 3a2f583 -- controller/` 已恢复到 `742adf0`（`git status --porcelain` 为空）；副本收工删除。

## R2@K1K3（2026-09-29）

角色：复核（review，Claude Code Opus 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-ACQ-001-R2@K1K3-20260930T035126Z-0474`，`requested.round = R2@K1K3`）。停点 `K1K3` 的第 2 个复核轮，对象为「Play D1 本地操作页窄范围代码批次 CLARIFY」的 AC-22/23/24 与 AC-18 修订 4。零消耗：零 ID/Play/API/VLM/检测推理/权重加载/序列回放/下载/远端访问；只在副本内重跑 focused、一次修前红抽查与一个会话级探针（脚本在会话暂存目录，不入库）。

### §0 候选、基线与开轮资格

- `round_candidate: 3190e058052b5bd1cec71b084f27fd7fea096aa3`（派发候选 = 上一实现派发 `…-K1K3操作页返工-…-14ac` 的 candidate，主题 `P1-ENG-ACQ-001 K1K3操作页返工：…` 的实现提交）。`git diff 3190e05..HEAD` 在 PLAY_GOVERNING 与页面文件上为空，其后只有 supervisor 登记/代录与 C3 提交。
- 修复触及行 = `git diff <上一复核轮 round_candidate 742adf0>..3190e05`；全量 diff 基线 = 本文件最近一行 `passed_candidate`（R1@K1K3 §7）= 同一 `742adf0`，两者重合。PLAY_GOVERNING 上只有 `tests/test_eng_acq_operator_web.py`（新，1193 行）与冻结集点名的操作单 `docs/evidence/P1-ENG-ACQ-001-play-d1.md`（§4 与接受角色 bb5a8f7 的 §2.7/§3 改动）；页面 `docs/evidence/P1-ENG-ACQ-001-operator-web.py`（新，1614 行）按合同属本批实现文件，一并逐行读。实现改动只来自 92aff44（首版）与 3190e05（返工，页面 +90/−11、测试 +178、§4 三句 +3/−3）；`controller/`、`tools/`、`config/`、`Assets/`、`ProjectSettings/` 与旧 LOOP-001 页面零改动。区间内其余提交为接受角色 CLARIFY/C2/C3、R1@K1K3 消费与 supervisor 登记/代录，未见实现越权。交接「复核范围」与实际 diff 一致。
- 开轮资格：PLAY_GOVERNING diff 非空，开轮。停点自证四项（交接「K1K3 操作页返工」自证四项）成立，不判 `REVIEW_BLOCKED`。
- 副本 `.claude/worktrees/review-P1-ENG-ACQ-001`（detach 于候选）。测试树哈希 `HEAD:tests = da56a41e0f86c08ca7625107a7aabf57eb013f14`。
- focused 重跑（输出写会话暂存目录）：`.venv-yoloe` `-m unittest discover -s tests -p test_eng_acq_operator_web.py` → `Ran 68 … OK`；系统 `python3` 3.14.6 同命令 → `Ran 68 … OK`；本机有 `node`，两例页面脚本用例实跑未 skip。
- 修前红抽查（非阻断 finding 闭合，不强制；验证新例非空转）：副本内把 92aff44 版页面经 `ACQ_OPERATOR_WEB_PATH` 跑同一测试文件 → `Ran 68`，11 failures + 1 error，红的恰为返工新增 12 例，原 56 例绿；与交接红绿日志一致。临时页面已删，副本 `git status --porcelain` 为空。
- 全套：不是复核开轮义务；交接的 1980 例、同名 13 项 FAIL/ERROR 名单与 C3 核对一致，本轮未重跑。

### §1 C2-1 / C2-2 与 AC 逐项（依据列 `BC-n` 读作 AC-n）

- **C2-1（AC-22）**：`App._retry` 先 `poll`、查同号、`resolve_late_receipts`，再调 `retry_block`，最后才 `_run` 原 argv。`retry_block` 依次核同号、原视图 `VIEW_KEYS` 全等、动作在当前九态 `legal`、argv `--token` 等于现视图令牌、confirm 另核 index 在显示内/`confirmable`/预览名与 SHA 等于 `_click` 存下的 `preview_seen`。任一不符 `refused` 落日志、零 CLI、条目保留等迟到回执。`App.state` 用同一函数给 `retry_allowed/retry_block`，页面 `retryOk` 再核 `legal` 与所示视图。会话自己的 request_id 去重仍是最终裁定。**满足**。
- **C2-2（AC-24）**：`mark_play_start` 先 `poll`，失败或 `sid_block` 即 `refused(action=play_start_mark)`、不写标记；`state()` 给 `timer.mark_block`，`paintButtons` 对 `#mark` 用 `dead || mark_block`。**满足**（同号判据自身的误报见 §3 K1K3-R2-1）。
- **AC-22 其余**：`STATE_ACTIONS` 与 CLARIFY 九态表逐格一致（含 `TRACKING` 可 ask、`ACQUIRING` 仅 stop、`backend_fatal` 仅 stop、`TERMINAL`/表外无动作、`respecify` 仅在 ask/respecify 的 `APPLIED`/`PENDING_QUEUED` 之后）；`CliRunner` 用 `sys.executable -m controller.language_loop`、cwd = 页面所在仓库；页面源码不含任何桥写函数，`ReadOnlyBridge` 用例证实只读；只监听 127.0.0.1，POST 需 nonce + Host/Origin。**满足**。
- **AC-23（K1 时效、K3 身份）**：`ReceiptCheck` 用会话自己的 `KReceipt.from_document`、`validate_measurement_sources`、`read_scenario`，并要求收据 payload 等于 `session_started.k_receipt`；`frames_limit = k_ret + k_conf`、`t_ret_s`、`t_conf_s = T_CONF_S` 只取自该收据。已读会话侧 `_check_confirmation`：会话用单调钟（查询提交 + `t_ret_s + T_CONF_S`、呈现后 `T_CONF_S`、`0 ≤ latest−N ≤ k_ret+k_conf`）；页面用结果 `query_unix_s` 与结果信封 `issued_unix_s`（早于会话的 `candidate_presented_monotonic_s`，只会更严），刷新/重启不续期。预览名 `{frame_id}-{query_id}.png` 与会话 `_preview` 一致，服务端只按 SHA 发同一份字节，确认需浏览器 `load` 且 `naturalWidth>0` 后回报的 `{name, sha256}`。会话 `_action_confirm` 仍核 `candidate_result_id`、index 范围与预览存在。无 Unity 真值进入页面（只读桥文件、会话目录与收据）→ 无 `RED_LINE`。**满足**。
- **AC-24 其余**：启动前 `sid_usage`（`acq-d1-1`、同号归档、无/多个 `session_started`、TERMINAL、无该号活锁）退出码 2 且不建目录；180 s 只提示、`play_deadline_notice` 只记一次、不发 CLI；首次标记持久化、重启读回；日志不可读则手工计时；操作单 §4 页面用法与 T1/T2/T3 回退命令由测试用真实解析器解析。**运行中同号判据有误报，见 §3，不满足**。
- **AC-18 修订 4**：§4 写明须本批新 `passed_candidate`、attempt 2 按 §2.7/§3 重新预检与 Acceptance 放行，页面不替代 §3；`acq-d1-1` 硬拒。Play 未发生，仍 `NOT_RUN`。

### §2 C3 预复核关注项的核实

- **会话进程异常退出（无 TERMINAL）不自动禁动作**：不列 finding。读 `controller/language_loop.py::main`：会话已死时 CLI 写请求后 5 s 无回执 → 退出码 5；页面记「结果未知」、不自动重发，死会话不执行任何动作，与 §4 T3 CLI 回退行为相同；桥请求带 `session_id`，换新号的会话按 `IGNORED_FOREIGN_SESSION` 忽略。CLARIFY/AC-22…24 未点名该触发，且没有错误动作或错误证据产生，不构成缺陷，也不记 `SCOPE_GAP`。改进建议见 §4。
- **离线证据边界**：页面脚本只在 node 中以真实 `/api/state` 快照执行 `paintButtons`，真实浏览器点击/解码与真实会话均未验证；本轮同意交接「未验证项」的表述，离线绿例不作 AC-18 Unity verdict。

### §3 Findings（本轮）

#### K1K3-R2-1 正常结束后误报「同号被复用」并永久停用（`Monitor.poll` / `Monitor._block_reason`）｜CLASS_2｜依据 `BC-24`｜阻断

- 事实：会话每次结束都走 `LanguageSession._enter("TERMINAL")`，先 `_journal("state", TERMINAL)` 追加会话日志，再 `_publish_state(force=True)` 经 `protocol.atomic_write`（含 `fsync`）写 `tracker_state`。页面 `Monitor.poll` 先 `_read_state()`（`tracker_state`），后在锁内 `_read_logs()`（会话日志），随后 `_block_reason(state)` 判「`self.closed` 且 state 不是 `TERMINAL`」即写**粘滞**的 `self.block = "会话已结束后本号又有活动：同号被复用"`。只要一次轮询的 state 读取落在两次写之间（窗口约为 fsync + 读取间隔，轮询周期 0.1 s），页面就在正常 stop 后把这次尝试标成同号复用；`block` 不会解除。点击、重试或计时标记的 `poll` 与后台 `poll_forever` 并发时，较旧的 state 读取在较新的日志读取之后入锁，是同一根因的第二条路径（读码）。
- 探针（副本，会话暂存目录 `probe_terminal_race.py`，用测试文件的生产写入器：`Env.terminal()` = `LanguageSession._journal`、`Env.state()` = `bridge.write_tracker_state`）：TRACKING → 写 TERMINAL 日志 → poll → 再写 `tracker_state` TERMINAL → poll，结果 `sid_block = "会话已结束后本号又有活动：同号被复用"` 持续存在，`timer.mark_block` 与 `mark_play_start()` 均报「同号不可复用」（该拒绝会以 `refused` 写进操作日志）；对照组两次写完后才 poll → `sid_block = None`。
- 影响与分级：结束后本无合法动作，不会发错 CLI；但页面横幅与操作日志会给出「同号被复用」的硬判据文字。attempt 1 的登记外 Play 正是因复用 `acq-d1-1` 作废，这条误报会让操作者或接受角色把一次正常结束的 attempt 2 当成同号复用处置（workflow §4.4：涉及判据/终态名、会改变操作员行为的文字最低 CLASS_2；根因是跨文件读取的顺序/并发，属并发/原子性）。
- 范围判据：可达。触发是每次正常结束（T3/T4 `stop`、`duration_reached`），入口即生产会话；被误触发的判据是 CLARIFY 点名的「结束后又有活动」与 AC-24「SID 复用硬提示」。行在本轮修复触及范围内（页面为本停点新文件）。
- 闭合要求（修法由实现角色定，本角色不改文件）：只在能证明 `tracker_state` 晚于 TERMINAL 日志记录时判「结束后又有活动」，例如先见到本会话 `tracker_state = TERMINAL` 之后再见非 TERMINAL，或比较 `tracker_state` 的 `sequence`/`since_unix_s` 与 TERMINAL 记录；并发轮询不得用较旧的 state 覆盖判定。具名回归须走生产写入路径：先 `LanguageSession._journal` 写 TERMINAL、poll、再 `write_tracker_state` TERMINAL、poll → 无 `sid_block`、计时标记不因同号被拒；原正例 `test_activity_after_close_record_blocked`（TERMINAL 后又出现 IDLE）仍须红。R3 以 `git revert -n <fix>` 做修前红/修后绿。

本轮无 `上轮漏检`/`上游漏检`，不写 `blocks_consuming_gate`。

### §4 非 finding 观察（不阻断，供实现角色参考）

- 返工把 `retry_block` 文案并入 `render` 重绘键。confirm 的结果未知条目遇帧差门时，文案含随帧变化的 `late`（「已过帧差门（{late}/{limit}）」），整排按钮会随每次刷新重建，点击可能丢失。该场景基本只在会话停滞时出现，此时按钮本就无效、CLI 回退可用；顺手修即可（重绘键用稳定原因码）。
- 会话异常退出后页面仍显示最后一次 `tracker_state`。可在状态栏显示 `tracker_state` 自身的时刻/序号新旧，帮助操作者及早改用 T2/T3；不是合同义务。
- `SidDuringRunTests::test_archive_or_activity_after_close_disables_play_mark` 名称含「activity after close」，实际只测归档；同号判据共用 `sid_block`，覆盖不缺，只是测试名不符。
- 操作单 §4「会话号：…`acq-d1-<n>`（n 从 1 起…）」是旧句，本批未改；`acq-d1-1` 已由页面硬拒、CLARIFY 要求新号，由接受角色在下次触及时顺带改写即可。
- 操作日志写入无跨线程锁（点击、计时提示、计时标记可并发 `append`），单行通常远小于缓冲区，交错概率极低；若交错，重启读日志转「手工计时」，fail-closed。

### §5 未闭与路由

- K1K3-R2-1（CLASS_2，`BC-24`）直接交回实现角色；修复后**直接回复核 `R3@K1K3`，不经核对轮**。这是本停点第 1 次 `REWORK_REQUIRED`，未触发冻结。
- K1K3-R1-1、R1-4 `SCOPE_GAP`/`OPEN` 不变，不属本轮。
- 新 `passed_candidate` 写出前，attempt 2 的 §2.7/§3 预检、放行与 Play 均不得启动。

### §6 UNITY_NA

本项不申请 `UNITY_NA`；复核**附议「不适用 `UNITY_NA`」**。AC-18 仍 `NOT_RUN`，本轮不给 Unity verdict。

### §7 Verdict

Verdict: REWORK_REQUIRED

C2-1、C2-2 经读码、focused 68 例重跑与修前红抽查成立；AC-22、AC-23 满足，无 `RED_LINE`。AC-24 的运行中同号判据在每次正常结束时可能误报「同号被复用」并永久停用（K1K3-R2-1，CLASS_2，阻断），交回实现角色，修复后直接回 `R3@K1K3`。Overall 与 Lifecycle 由接受角色维护。

边界自查：本会话未修改任何实现文件。主工作树只写本文件与状态板；副本内临时页面已删除，`git status --porcelain` 为空，副本收工删除。

## R3@K1K3（2026-09-30）

角色：复核（review，Claude Code Opus 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-ACQ-001-R3@K1K3-20260930T041057Z-f34e`，`requested.round = R3@K1K3`）。停点 `K1K3` 的第 3 个复核轮，前一轮 R2@K1K3 是本停点第 1 次 `REWORK_REQUIRED`，未冻结。对象为 K1K3-R2-1 的闭合与修复触及行。零消耗：零 ID/Play/API/VLM/检测推理/权重加载/序列回放/下载/远端访问；只在副本内重跑 focused、一次修前红/修后绿与一个零消耗并发探针（脚本在会话暂存目录，不入库）。

### §0 候选、基线与开轮资格

- `round_candidate: 5e8e4d4b756da92a521c8c7ed98707df775ff02a`（派发候选 = 上一实现派发 `…-R2@K1K3返工-…-ce72` 的 candidate）。`git diff 5e8e4d4..HEAD` 只有 `docs/evidence/supervisor-dispatch.jsonl`。
- 修复触及行 = `git diff <上一复核轮 round_candidate 3190e05>..5e8e4d4`：实现改动只有两笔。a677137「页面修复」只改 `docs/evidence/P1-ENG-ACQ-001-operator-web.py`（+48/−11）；5e8e4d4「回归测试与证据」改 `tests/test_eng_acq_operator_web.py`（+81/−1）、本停点交接/红绿/全套证据与状态板。两笔已逐行读。区间内其余提交为 supervisor 登记/代录、接受角色 C3 与 R2@K1K3 复核提交，未见实现越权。`controller/`、`tools/`、`config/`、`Assets/`、`ProjectSettings/` 相对全量基线零改动。
- 全量 diff 基线 = 本文件最近一行 `passed_candidate`（R1@K1K3 §7）= `742adf0`。`742adf0..3190e05` 已在 R2 逐文件核对，本轮增量即上条。交接「复核范围（`R3@K1K3`）」与实际 diff 一致。
- 开轮资格：PLAY_GOVERNING diff 非空（`tests/` 与操作页），开轮。停点自证四项（交接「R2@K1K3返工」自证四项）成立，不判 `REVIEW_BLOCKED`。
- 副本 `.claude/worktrees/review-P1-ENG-ACQ-001`（detach 于候选）。测试树哈希 `HEAD:tests = 568fc431e0915cbe202db094f9059b129cfa8b61`。
- focused 重跑（输出写会话暂存目录）：仓库 `.venv-yoloe`（Python 3.12.13，只读）`-m unittest discover -s tests -p test_eng_acq_operator_web.py` → `Ran 72 … OK`，本机有 `node`，页面脚本用例实跑、无 skip。与交接一致。
- 全套：不是复核开轮义务，本轮未重跑。已核对交接全套日志：`Ran 1984`，`FAILED (failures=4, errors=9, skipped=19)`；FAIL/ERROR 名单与 3190e05 版日志逐名相同（13 项）。

### §1 K1K3-R2-1 闭合（修前红/修后绿；副本内 `git revert -n a677137` → 跑同一测试文件 → `git reset --hard` 恢复 → 再跑）

- 修前（撤「页面修复」、保留新测试）：`Ran 72`，`FAILED (failures=2)`。红的恰为 `SidDuringRunTests::test_normal_end_between_journal_and_state_is_not_reuse`（本 finding 具名回归）与 `::test_concurrent_poll_with_older_state_read_is_not_reuse`（第二条路径），断言均为 `sid_block = "会话已结束后本号又有活动：同号被复用"`，正是 R2 §3 描述的误报。
- 修后（恢复到候选，`git status --porcelain` 为空）：`Ran 72 … OK`。
- 两条正例 `::test_activity_after_close_record_blocked`（见过 TERMINAL 状态后又出现 IDLE）与新增 `::test_new_state_after_close_record_blocked_without_seeing_terminal_state` 在修后仍判阻断，满足 R2 §3 闭合要求「原正例仍须红」。
- 零消耗并发探针（副本；测试文件的生产写入器 + 真实墙钟 `time.time`；两条线程不停 `poll`，模拟后台轮询与点击轮询并发，主线程按会话写序先 `_journal` TERMINAL、后 `write_tracker_state` TERMINAL）：正常结束 300 次，修后误报 0 次、修前（同一 `git revert -n`）300 次；结束后再写本号 IDLE（同号复用正对照）50 次，修前修后都 50 次阻断。
- **K1K3-R2-1 闭合。**

### §2 修复触及行复查与 AC

- **判据 (a)(b) 与会话写序对得上**（读 `controller/language_loop.py`，本批未改）：`_enter` 先把 `self.state` 设为 TERMINAL，再 `_journal`（`at_unix_s = self._unix()`，生产为 `time.time`），然后 `_publish_state(force=True)`。状态信封的 `issued_unix_s` 在建 payload 时由 `controller.protocol` 取 `time.time()`，同一墙钟。结束前的任何非 TERMINAL 状态信封都在该日志记录之前签发，所以 (b) 的严格 `>` 不会命中正常结束。结束后同一会话不会再写非 TERMINAL：`_ensure_resident_loop` 遇 TERMINAL 返回；`_maybe_verify`、`_resume_designate_retry`、`_advance_segment` 只在各自非终态下动作；`IGNORED_TERMINAL` 回执重写的仍是 TERMINAL。所以 (a) 只会在同号被另一进程复用时命中。钟回拨的残余风险交接已如实披露，且该误判只会停用本就没有合法动作的结束后页面，同号复用另有第二个 `session_started`、同号归档与启动前 `sid_usage` 拦截。
- **轮询串行**：`poll_lock` 只包 `_poll`，内部只再取 `monitor.lock`。调用方 `poll_forever`、`mark_play_start`、`_click`、`_retry` 调 `poll` 时都不持 `pending_lock`/`timer_lock`/`monitor.lock`，不引入新的锁序环；异常经 `with` 释放。较旧的状态读取不再在较新的日志读取之后判定，也不再覆盖较新快照。
- `closed` 时 `legal` 仍为空，修复没有放开任何结束后动作。`_block_reason` 只有 `_poll` 一个调用方，新参数有缺省值。`App.log` 的 `log_lock` 不重入、持锁期间不调用其他锁。
- 页面脚本：结果未知框重绘键改用 `retry_allowed`（ok/blocked）；原因文字由 `paintButtons` 按 `data-request-id` 用 `textContent` 就地更新（无注入）；`blocked↔ok` 翻转仍整框重建。`PageScriptButtonTests` 在 node 中实跑通过。
- 新测试走生产写入路径：`Env.terminal()` = `LanguageSession._journal`，`Env.state()` = `bridge.write_tracker_state`，其中 `production_clock` 把 `controller.protocol` 的时钟钉到测试钟。改名例内容未变；新增 `test_activity_after_close_disables_play_mark` 覆盖计时标记服务端拒绝。
- **AC-24**（依据列 `BC-24` 读作 AC-24）：运行中同号判据不再在正常结束时误报，复用仍阻断，**现满足**。AC-22、AC-23 的实现行本轮未改，R2 结论不变。页面只读桥文件、会话日志与收据，无 Unity 真值进入，无 `RED_LINE`。AC-18 修订 4：Play 未发生，仍 `NOT_RUN`。

### §3 Findings（本轮新增）

无。修复触及行上没有新的 CLASS_1/2 或 `RED_LINE`；本轮无 `上轮漏检`/`上游漏检`，不写 `blocks_consuming_gate`。

### §4 非 finding 观察（不阻断）

- `test_concurrent_poll_with_older_state_read_is_not_reuse` 修前的红依赖 `second.join(0.3)` 内第二次轮询跑完；机器极慢时修前红可能转绿（红不稳，绿是确定的）。本轮修前红已复现，探针也独立证实，不影响闭合。
- `_activity_after_close` 名为判定、实际还会置 `terminal_state_seen`，属写法问题，行为正确。
- R2 §4 第二条（状态栏显示 `tracker_state` 新旧）不是合同义务，本轮仍未做；第四条（操作单 §4 `acq-d1-<n>` 从 1 起的旧句）归接受角色，仍待改写。

### §5 未闭与路由

- K1K3-R2-1 已闭合。K1K3-R1-1、R1-4 `SCOPE_GAP`/`OPEN` 不变，不属本轮。
- 本轮通过不放行 Play：attempt 2 仍须接受角色消费本轮，并按操作单 §2.7/§3 与 workflow §4.5 完成预检和放行；离线绿例不作 AC-18 Unity verdict。

### §6 UNITY_NA

本项不申请 `UNITY_NA`；复核**附议「不适用 `UNITY_NA`」**。AC-18 仍 `NOT_RUN`，本轮通过不等于 `DONE`。

### §7 Verdict

Verdict: PASS_WITH_NOTES
passed_candidate: 5e8e4d4b756da92a521c8c7ed98707df775ff02a

K1K3-R2-1 以修前红/修后绿（2 例）和零消耗并发探针（修前误报 300/300，修后 0/300，复用正对照 50/50 两边都阻断）闭合；focused 72 例 OK。修复触及行上没有新的 CLASS_1/2 或 `RED_LINE`，AC-24 现满足。附注见 §4；K1K3-R1-1、R1-4 `SCOPE_GAP` 债仍 `OPEN`。交接受角色消费本轮；Overall 与 Lifecycle 由接受角色维护。

边界自查：本会话未修改任何实现文件。主工作树只写本文件与状态板；副本内 `git revert -n` 已由 `git reset --hard` 恢复（`git status --porcelain` 为空），副本收工删除。
