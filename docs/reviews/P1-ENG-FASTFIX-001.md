# P1-ENG-FASTFIX-001 — 独立复核记录（engineering-v1）

复核角色（最强池，Fable 子代理，supervisor 派发）。轨道：提案抬头 `Workflow: engineering-v1`，接受角色 D2 `ACCEPTED` 裁定生效（提案「D2 接受裁定」）；依据列仍逐字 `BC-n`，读作任务合同 `AC-n`。停点 `K1K2K3K4`（提案 §7 合并停点）。

## R1@K1K2K3K4（2026-10-11，Mac mini）

Dispatch-Id `P1-ENG-FASTFIX-001-R1@K1K2K3K4-20261011T214822Z-a8eb`；requested.round `R1@K1K2K3K4`。

### §0 候选、基线、开轮资格与重跑

- `round_candidate: 72b5c998f34a83930bd9c8d590cabd613ede0cc8`（派发指定；= 状态板交接行候选 3 的补录提交，`origin/main` 祖先，运行时核 `git merge-base --is-ancestor` 成立）。
- 全量 diff 基线：本文件此前不存在，无 `passed_candidate`；`$BASE` = 首条「A实现 候选1代码」提交的父提交（运行时 `git log --format=%H --grep='A实现 候选1代码' -1`^ = `1345d2e4…`，与 handoff §2 定义相同）。`git diff --stat $BASE..72b5c99 -- controller tools tests config` = **25 文件 +6133/−128**（PLAY_GOVERNING 非空 → 开轮）；全部路径 41 文件 +9317/−138（其余为证据/提案/状态板/派发日志，含他角色提交）。
- 冻结路径零 diff（运行时核）：`controller/det_assoc_tracker.py`、`config/p1-eng-capture-001.json`、`config/scenario.default.json`、`config/det-assoc-v1.models.json`、`Assets/`、`ProjectSettings/`、`Packages/packages-lock.json`、`tools/eng_loop2/`、`tools/eng_capture/`。改动文件 ⊆ 提案 §2.1 闭集（`controller/{gated_publisher,track_loop,language_loop,target_manager,language_bridge,resident_core}.py`、`config/p1-eng-fastfix-001.json`、`tools/eng_fastfix/`、`tests/`）。
- 首个复核轮：无上一复核轮候选、无既往 finding 闭合义务。候选含「续修C1」两笔实现提交（`c8c90fb` 代码+测试+证据、`72b5c99` 仅补录证据/账本）；修复增量 `git diff c8c90fb^..72b5c99` 只触及 `controller/{track_loop,gated_publisher,language_loop}.py`、`tools/eng_fastfix/{meter,ledger,window_meter}.py` 与四个测试文件，与 handoff 候选 3 节声明一致。
- 一次性副本：`.claude/worktrees/review-P1-ENG-FASTFIX-001`（detach 于候选，收工删除）。测试树哈希（副本 `git rev-parse`）：`HEAD:tests = 78d8f35f6a7415054fe3b4e9236be6c3bd41272b`、`HEAD:controller = 47cdd77ae2f1cba4baa59450f9c62647175fe39d`、`HEAD:tools = 0a92e9ae82ae1eebe00c8ea7427711c74b2f0a9d`、`HEAD:config = 4b4906a4a7202aeede9c9544f3c0db40589184a1`。
- **重跑（focused 一次，数据根 `~/TetheredDroneTracking-full/.venv-yoloe` 只读复用，零真实模型加载）**：与 handoff 候选 3 节相同的 23 个测试文件。注意：该 venv 的 site-packages 含顶层 `tests` 包，`python -m unittest tests.test_x` 在副本内全部 `ModuleNotFoundError`（环境，非候选缺陷；首次尝试日志 `r1-focused.log` 保留），改用 `python -m unittest discover -s tests -p <file>.py`（handoff 同款命令）。结果（原始输出 `~/fastfix-r1-20261011T214803Z/r1-focused-discover.log`，不带 `-v`）：**21 文件 OK、2 文件失败**——`test_track_loop::test_cli_runs_pinned_csrt_to_a_versioned_summary`（失败）与 `test_language_k_binding`（导入错误，同一 `tests` 包遮蔽）均为候选 1 全套日志 `docs/evidence/P1-ENG-FASTFIX-001-tests.log` 已有的基线失败（行 742/355，逐名相同）；**新增失败 0**。`test_language_loop` 205 OK（含 `StateMirrorTests::test_frozen_paths_are_untouched_in_the_working_tree`，在干净副本内通过 → C2-P4 的「提交后复跑」现有本轮持久化原始输出，归档 focused 日志中的该条红为运行时工作树未提交文件所致的环境失败，非缺陷）。本项模块：`test_capture_session` 62 OK、`test_fastfix_publish` 25 OK、`test_target_manager` 76 OK、`test_fastfix_meter` 11 OK、`test_fastfix_ledger` 11 OK、`test_fastfix_window_meter` 4 OK、`test_det_assoc_tracker` 37 OK。
- `test_fastfix_replay`（3）与 `test_capture_isolation` 的动态毒化真值用例首跑因副本无 `outputs/` 而 skip；在副本内以只读符号链接 `outputs/eng-loop`、`outputs/eng-det` 指向主树（准入帧元数据与权重 sha 核验；`model_loader=lambda _p: object()` 替身、`CachedOrLiveModel(cache, None, …)` 合成检测，真实 YOLO 构造 0）后复跑：`test_fastfix_replay` 3 OK、`test_capture_isolation` 13 OK（原始输出 `r1-focused-admitted.log`）。主树 `git status` 全程干净。

### §1 逐文件核对摘要（全量 diff，$BASE..候选）

- `controller/gated_publisher.py`（+278/−）：`_gate_classified` :818–869 逐步全量求值（步 3 `verify_frame_identity` 无条件调用，不因步 2 跳过；4a/1 缺快照即终止；5c 缺 `capture_unix_s` 终止——合同表未写「终止」但 5d/5e 无法求值，附议为必要）；`_classified_verdict` :792–804 `detail.hits` 全列、第一完整性命中 → `PUBLISH_REJECTED`+`_set_fatal`、仅时序 → `PUBLISH_DROPPED` 且不碰 `fatal_reason`；单次 `monotonic()/unix()` 读数 :850–851；`settle_frame` :744–774 优先级 FATAL > WRITE_FAILED > DROPPED(+1) > PUBLISHED(唯一清零) > NO_ATTEMPT，`streak ≥ n_drop` 以本帧第一时序原因 `_set_fatal` 并记 `escalation`；`_derived` :671–694 观测 DROPPED 后同帧云台/速度不求值（`dropped_with_frame`）、观测 WRITTEN 后越线 `partial_after_observation=true` 且不回改。AST 比对基线：`_gate`、`hold_body`、`set_nadir`、`slew_look_at`、`_append` 函数体逐字相同；`_safety_hold` 仅在写失败时加 `ctx.write_failed`；兼容分支 `else` 路径逐字相同。
- `controller/track_loop.py`（+278/−）：仅最新帧 `begin_frame`/`settle_frame`（:819–821、:852–854），旧帧 `effect=None` 不发命令；速度 DROPPED → `BodyCommandNotWritten` → 恰一次回退 hold（:1320–1331），规划器 hold 与回退互斥；`TIMING_SEGMENTS` :1465–1473 六段首尾相接、`capture_timing_record` :1484–1497 段和 = `total_s`，`gate_eval_s` 取 `settle.gate_evals`；C1-1 的 `_ensure_assoc_timing/_wrap_assoc_update` 实例级包装（不改 `det_assoc_tracker.py`）；`_capture_partial_timing` :992–1008 失败帧保留已到达标记——但恒传 `settle=None`（见 R1-1）。
- `controller/language_loop.py`（+334/−）：`_prepare_reacquire_hint` :3071–3090 仅 `seg_source == "publisher"` 且 `publisher.escalation.reason == seg_end` 才算时序升级（`escalation` 只由 `settle_frame` 在 streak ≥ N_drop 置），非时序拆载体 → `reacquire_skipped(not_timing_escalation)`；在 `_teardown_resident(seg_end, cancel_task=hint is None)` 之前、旧载体仍在时生成（:2874–2877）；`_note_hint_candidate`/`_on_frame_settled` :3014–3059 只对最新帧、结算 ∈ {PUBLISHED, DROPPED} 才收候选（`full_kf_state_from_associator` 深复制）；窗口在 `resident_loop_started` 开（:2780–2795，`m_ready` 单次读数同时写事件与 `open_reacquire_window`），到期每 tick 核（:2890）；取消顺序 stop（:3973）> release（:1686–1700，token 不符 → `REQUEST_INVALID`）> click（:1731 `cancel_reacquire("user_click")` 只置 status/清缓冲）；C1-3 核实：`_action_click` :1721–1752 的 `finally` 只剩会话投影 `_enter("REINIT_REQUIRED", reason=seg_end)`，函数体内无 `release_binding`；投影 `publish_degraded` :2911–2929 只在管理器 `TRACKING/None|predicting` 且本最新帧 DROPPED 时改写，其他原因优先；捕获模式门控：`_CaptureHook`、`classified/n_drop`、`record_marks`、`_SessionModelCache(monotonic=…)`、`fastfix`、`InputsLog(chain=…)`、`_expire_reacquire_tick` 全部在 `if self.capture`/`resident and not language` 之下，兼容模式无新可达行为（`CompatUnchangedTests::test_compat_session_uses_current_paths`）；`LanguageWorker`/`CandidatesBackend`/`_validate_candidates_source`/围栏读取无 diff hunk。
- `controller/target_manager.py`（+821/−）、`controller/resident_core.py`（+175）、`controller/language_bridge.py`（+6）：PLACEHOLDER_TM
- `config/p1-eng-fastfix-001.json`（新）：t_pub_s 0.4 / k_pub 2 / n_drop 3 / t_reacq 10 / auto_reacquire on，无 `rho_reacq`；结构约束在 `target_manager.py::load_fastfix_config`（:407–435），`ConfigTests` 10 个坏例覆盖拒启；`K_PUB`/`T_STALL_S`/`RESIDENT_REBUILD_LIMIT` 在 `language_loop.py` diff 中无赋值行变动（`ConfigTests::test_frozen_constants_have_no_diff` 另以 AST 字面值核）。
- `tools/eng_fastfix/`（`common/ledger/meter/replay/score/window_meter`，新）：`replay.py` 自 `tools.eng_capture.replay` 只导入 `CacheFrame, CachedOrLiveModel, CountingModel, boxes_rows, library_boxes`（后两者为框行转换辅助，略超 §2.4 字面「帧读取与缓存键辅助」，备注不分级；模块导入会连带加载 `tools/eng_capture/ledger.py` 但零调用 → R1-4 不触发），不导入 `score.py`、无真值 token，注入规则/`not_applicable`/缓存 `live=None`/新载体跳 3 帧/两臂与 §3.8 一致；`score.py` 是唯一真值读取者（`score_truth_path/rows/box` 在 `score_*` 内）；`meter.py` 停令线程与采样线程分离、采样逐条目检查 `stop_event`、只遍历声明根、1 MB 截断记 `meter_truncated`、C1-4 后目录/条目 OSError → `MeterUnknown` → S-UNKNOWN，采样线程任何异常/死亡由停令线程检出；`window_meter.py::main` 单循环，`fh.write/flush` 与旗标写失败会未持久化 UNKNOWN 直接退出、无存活看门狗（C2-P2 事实成立；该要求已被「R1简化计量落实」§1 替代，R1 不以此拒启，也不签 AC-15/19 通过）；`ledger.py` `check_launch`/`record`（先记后跑、失败不退款、原子写）/`read`（损坏或 sha 不符 → `LedgerUnknown`）/`create_continuation`/`check_disk_window` 与 AC-19 一致。
- `tests/`（新 5 + 扩 6）：`test_capture_isolation.py` 静态导入图（`controller/*.py` + replay/meter/ledger/common）、`score_*` 外无真值 token、毒化真值字节相同 + 打开审计（本轮以准入帧实跑通过）、冻结路径/闭集/`LanguageWorker` 静态核；**`window_meter.py` 不在 `FASTFIX_RUNTIME_FILES`，静态图检查未覆盖**（手工核：只导入 ctypes/json/os/pathlib/time，无真值、无 `controller`；备注见 §3 N-2）。
- `tests/test_det_assoc_tracker.py`（候选 2 窄修）：仅把 `eng_fastfix` 加入「显式传新值」白名单并改 docstring，与 handoff §4 声明一致。

### §2 AC 逐项（依据列 `BC-n` 读作 AC-n；「成立」= 代码与具名测试对应、本轮重跑通过）

| AC | 本轮判定 | 依据（代码:行 / 测试，本轮副本重跑） |
|---|---|---|
| AC-1 | 成立 | `_gate_classified` 逐步/交叉/完整性优先/`hits` 全列/负 `load_elapsed`、负 `capture_age`、缺 `capture_unix_s` 均完整性；`ClassifyRowTests`（步 1/2/3×3/4a/4b/4c/5a/5b/5c/5d/5e）、`ClassifyCrossTests`（2+3、4c+5e、5b+5d、5b+3）、`CompatGateTests`（同注入首命中致命、`_gate` AST 源文本与基线相等）均经真实 `GatedPublisher`+快照环走生产门路径。 |
| AC-2 | 成立 | `DegradeTests` 四路径（观测命中/预测命中/观测后云台越线/观测+云台后速度越线）断言收据、hold==1、无 `orphan_control`、`fatal_reason` None、管理器状态与对照逐字段相同、下一帧恢复、`resident_rebuilds=0`；底层写失败仍上抛 fail-closed。 |
| AC-3 | 成立 | `settle_frame` 优先级与计数（§1）；`EscalateTests` 恰在 N_drop 升级、PUBLISHED 清零、完整性任意 streak 致命、C1-2 降级帧 + HOLD 底层写失败 → WRITE_FAILED/streak 守 2/无升级（生产路径）；`test_hold_no_attempt_and_write_failure_neither_count_nor_clear` 直接写 `_frame_ctx`（非生产路径，但同一主张另有生产路径用例覆盖，不单独分级）；`CompatUnchangedTests` 对基线模块逐收据比对。 |
| AC-4 | 成立 | `BacklogTests`（monotonic-only 10×0.5 s 只最新帧有收据/结算；墙钟同步版走 5e 完整性，IR-9）、`ProjectionTests`（`publish_degraded`/恢复、其他原因优先、闭集末尾追加静态检查）。 |
| AC-5 | 成立（测试覆盖缺口见 N-1，不阻断） | 提示生成/跳过原因闭集 `REACQUIRE_SKIP_CAUSES`（`target_manager.py` :156–165、:1945–1972）；f_last = 绑定键、结算 ∈ {PUBLISHED, DROPPED} 的最大帧，`hint_stale`/`hint_invalid`（`full_state_problem` :992–1023 非有限/非对称/非半正定 LDLᵀ）；窗口 `_open_reacquire_window`/`reacquire_expired` :1986–2019 双截止严格 `>`、每 tick 到期；同帧 stop > release > click（单请求槽）；`cancel_task=False` 释放旧 episode；提交事务 `_commit_precheck`/`_plan_commit` reacquire 分支 :1601–1690，evidence 字段齐全，TaskSpec/intent 不改；回滚/`binding_rollback_failed` fail-closed；`ReacquireHintTests`/`ReacquireWindowTests`/`ReacquireReplayTests`、`ReacquireSessionTests`（窗口内零 look_at/速度、每最新帧恰一次 hold、零新帧 tick 到期、拒收点击零状态变化）。 |
| AC-6 | 成立 | `synthesize_reacq_prior` :905–928 用库 KF 对象连推 n 步再 `pose_center_transform`（与 `apply_pose_center` 同式）；`REACQ_PRIOR` 不入 `KF_PHASES`；`reacquire_gate` 与 `motion_size_gate` 共用 `_motion_size_core`（N-3）；`ReacquireNegativeTests` 位置过门尺寸/运动不过、出画 `reacquire_failed`、25°/帧滚转、映射失败无证据、`test_gate_uses_only_synthetic_prior`（候选自身 prior 替换反证）、`test_pinned_library_kf_and_apply_pose_center_match`（本轮数据根 venv 实跑，未 skip）、`test_motion_size_gate_unchanged_against_accepted_base`（500 随机用例对基线模块）。 |
| AC-7 | 成立（候选 1 读数沿用） | `replay.md` §1–2：on 臂 n_committed=3、IoU 0.926/0.943/0.815 全 ≥ 0.5，off 臂 0，9 注入 `not_applicable`；候选 3 增量 `c8c90fb^..72b5c99` 不触及 `target_manager.py`/`replay.py`/`score.py`（运行时 `--stat` 核），沿用成立；`test_fastfix_replay` 3 例本轮以合成检测实跑通过。不是在线门等价证明。 |
| AC-8 | `NOT_RUN` | TX 未签 0，附议 `NOT_RUN`，不阻断。 |
| AC-9 | **不成立** | 正常/旧帧/解码失败/关联异常/管理器异常路径成立（`FrameTimingTests` 段和 = total、`gate_eval_s == 收据 load_elapsed_s`、journal_prev、桥文件无新字段）；**底层观测/云台写异常路径丢已读门读数**，见 R1-1。 |
| AC-10 | 成立 | §1 配置项；`ConfigTests` 10 个坏例 + `test_frozen_constants_have_no_diff` + 会话拒启。 |
| AC-11 | 成立 | `MeterTests::test_stop_latency_during_a_long_sample_is_within_one_second`（SlowWalker 15 万路径/5 s）、只遍历声明根、start/end、1 MB 截断、无 `controller`/真值导入；C1-4 五条 UNKNOWN 用例。 |
| AC-12 | 成立 | 冻结路径零 diff、改动文件 ⊆ 闭集、`LanguageWorker`/`CandidatesBackend` 无 diff；静态导入图 + `score_*` 外无真值 token + 毒化真值字节相同/打开审计（本轮实跑）；兼容既有测试本轮新增失败 0。覆盖缺口 N-2 不阻断。 |
| AC-13 | 成立 | `R22ChainTests` 行间链式/删行拒绝含 `reacquire_hint` 行；`tools/eng_fastfix/replay.py` 零调用 `tools/eng_capture/ledger.py` → R1-4 不触发；不改旧债状态。 |
| AC-14 | 本候选按工程 §6 窄修替代（不记全套通过） | 候选 1 全套 1 次（2776，基线失败 29/34）；候选 3 改动限具名文件、不触及真实模型加载器/数据划分/对外指标路径，focused 23 文件 + 具名红绿替代；本轮复核独立重跑 23 文件新增失败 0（§0）。附议替代充分。 |
| AC-15 | 不判（B/C 未执行） | 操作单文字已按 C1-4 补；C2-P2/P3 与整窗计量要求已被「R1简化计量落实」替代，**不签 AC-15 通过**；B/C 首签前由接受角色核。 |
| AC-16/17/18/20 | `NOT_RUN` | B/C 未签 0；AC-18 无 `UNITY_NA` 申请。 |
| AC-19 | 代码侧成立；现场项不判 | `ledger.py` 拦截/先记后跑/不退款/UNKNOWN 拒启/校验和；`window_meter.main` 故障持久化缺口为事实（C2-P2），依现行合同不作 R1 拒启或 AC-19 通过依据。 |

### §3 Findings

| ID | 分级 | 依据列 | 内容 |
|---|---|---|---|
| **R1-1** | **CLASS_2**（失败路径） | `BC-9`（读作 AC-9；§3.5「每次门求值另记 `gate_eval_s`」） | `controller/track_loop.py::_capture_partial_timing` :1005 恒以 `settle=None` 调 `capture_timing_record` → `gate_eval_s=[]`、`settle_outcome=None`；而异常在 :852 `settle_frame` 之前抛出时 `publisher._frame_ctx["gate_evals"]` 仍持有本帧已读门读数（`_classified_verdict` :797–798 已追加）。可达生产路径：底层 `observation` 写抛错（`gated_publisher.py` :534 直接上抛、无收据）、底层 `look_at`/`predicted_look_at` 写抛错（:581、:717）——即 AC-2 所述「底层写失败 → 上抛 fail-closed」。机身写失败不走此路径（`_body_step` 吞下并置 fail-closed 原因后正常结算，门读数保留）。既有 `FrameTimingTests::test_publish_exception_emits_one_row_with_tm_segment` 把 `GatedPublisher.observation` 整体替换为抛错函数，门未运行、未断言 `gate_eval_s`，不能证明此主张（C2-P1 成立）。范围判据：可达（AC-2 点名的失败路径）。**闭合绑定**：新具名回归 `tests/test_capture_session.py::FrameTimingTests::test_write_failure_after_real_gate_keeps_gate_eval`（名可改，证据文件列名）——会话 harness 生产路径，让真实分级门通过后 inner 写出器 `observation`（或 `look_at`）抛 `OSError`，断言该帧恰一行 `frame_timing`、`gate_eval_s == [该次门 load_elapsed_s]`（与收据/`_frame_ctx` 同值）、`missing_reason.frame == "publish_failed:OSError"`、已到达段照记；修前红/修后绿由本角色下一轮核实。修复不得改 `settle_frame` 结算语义与 fail-closed 上抛。 |
| N-1 | 覆盖缺口（不分级、不阻断） | — | AC-5「提示深复制」与 §3.3「协方差非对称或非半正定 → `hint_invalid`」无直接测试：`tests/` 无用例在取提示后改动跟踪器 KF 并断言提示不变（会话替身 `FakeLibTrack` 每 step 重建列表，复制与引用不可区分）；8×8 `full_state_problem` 的非对称/非半正定拒绝只在 2×2 `make_kf_snapshot` 有旧用例。代码按读核为深复制（`resident_core.py` :1069–1098 逐元素 `float()` 复制入冻结 dataclass）与 LDLᵀ 判定正确。建议实现角色在返工同批补两例（不改接口），非闭合条件。 |
| N-2 | 覆盖缺口（不分级、不阻断） | — | `tests/test_capture_isolation.py` `FASTFIX_RUNTIME_FILES`（:155–156）未含 `tools/eng_fastfix/window_meter.py`，静态导入图/真值 token 检查未覆盖该文件；本轮手工核其只导入 ctypes/json/os/pathlib/time、无真值与 `controller`。建议加入集合。 |
| N-3 | 备注 | — | `motion_size_gate` 函数体被重构为 phase/None 检查 + `_motion_size_core`（diff hunk @@ -532,6 +670,25），合同要求的是「对库 prior 的行为逐字不变」，行为由 `test_motion_size_gate_unchanged_against_accepted_base`（500 随机用例对导出基线模块，本轮实跑未 skip）钉住；不构成 AC-6 不符。 |
| N-4 | 备注 | — | `track_loop.py` :840–841 忽略 `publisher.observation` 返回值，DROPPED 帧（及兼容 REJECTED 帧，修改前即如此）的 loop 记录 `publication["published_observation"]=True`；不影响收据/桥文件/streak，AC 表未约束，不分级。 |
| N-5 | 备注（SUSPECT） | — | `_batch_settle` 每 tick 顶部置 None（`language_loop.py` :2806），零新帧或 NO_ATTEMPT tick 也会让 `publish_degraded` 投影回落，与 §3.2「下一 PUBLISHED 帧恢复」措辞不完全相同；降级投影按最新帧定义，行为无害，留接受角色读法。 |
| N-6 | 备注 | — | `tools/eng_fastfix/replay.py` 自 `tools.eng_capture.replay` 另导入 `boxes_rows`/`library_boxes`（框行转换辅助，略超 §2.4 字面）；模块导入连带加载 `tools/eng_capture/ledger.py` 但零调用，R1-4 不触发。 |
| N-7 | 备注 | — | 提示键在拆载体时不在 `tracked+lost` 中 → `library_kf_predictor` None → 每帧 `reacq_predictor_unavailable`、到期失败（fail-closed，合同允许），无 `shared_kalman` 回退；`language_loop.py` :3078 非时序拆载体且无绑定时不记 `reacquire_skipped`（合同「无绑定不生成」，是否须记事件由接受角色读法）。 |
| C3-1 | CLASS_3 | — | `docs/evidence/P1-ENG-FASTFIX-001-K1K2K3K4-handoff.md` :221「提交后复跑见下节」之后无对应命令/输出（C2-P4 事实成立）。逐字替换补丁（由实现角色下次提交应用）：把「提交后复跑见下节」替换为「提交后复跑原始输出见 `docs/reviews/P1-ENG-FASTFIX-001.md` R1 §0（干净副本 205 OK）」。不改任何数字/哈希。 |

### §4 C2 关注项、IR 读法、UNITY_NA 与红线

- **C2-P1**：成立 → R1-1（阻断）。实例层懒建工厂包装（`_ensure_assoc_timing/_wrap_assoc_update`）只读核为对 `update` 的实例属性赋值包装、不改调用/返回；真实 BoT-SORT 对象上的可赋值性本轮无真实构造，未实测（保持 handoff「未验证项」）。
- **C2-P2**：事实成立（`window_meter.main` 写/旗标失败不持久化 UNKNOWN、无看门狗），已被「R1简化计量落实」§1 替代为非拒启项；本轮不签 AC-15/19 已修。
- **C2-P3**：属续做窗口计量执行偏差，用户已同意 FASTFIX-CONTINUATION-UNKNOWN 保留 UNKNOWN；本轮不复算、不追认。
- **C2-P4**：成立（评价缺口 C3-1）；本轮独立重跑在干净副本得 `test_language_loop` 205 OK（含该用例），归档红为环境所致。
- **C1 既有关注项**：提示 f_last 深复制/完整协方差（代码成立，覆盖缺口 N-1）；双截止/同帧人工优先（成立）；事务回滚（成立）；生产输入删行链（`R22ChainTests` 成立）；完整性/时序交叉（`ClassifyCrossTests` 成立）；异常帧时间线（R1-1 缺口外成立）。
- **IR-1…16**：接受裁定与候选 3 代码一致；IR-13 `eng_fastfix` 白名单仅限 `tests/test_det_assoc_tracker.py` 静态策略例，未扩基础设施豁免。
- **UNITY_NA**：实现者未对本候选申请 `UNITY_NA`（阶段 A Unity/Play=0，AC-16…18 `NOT_RUN`），无须附议；AC-8 `NOT_RUN` 附议。
- **红线**：`controller/` 六文件与 `tools/eng_fastfix/` 运行时入口 grep 无 `truth`/`CoverageEvaluator`/`m3_body` 命中；真值只在 `score.py::score_*`；毒化真值动态用例本轮实跑通过；位姿取自帧环传感器元数据。无 `RED_LINE`。
- **开轮/机读**：首轮，无 `blocks_consuming_gate`（无「上轮漏检」）；不写 `passed_candidate`。

### §5 R1资源记录（提案「R1简化计量落实」§2–3）

- 授权：`docs/authorizations.md` 2026-10-11「用户同意 FASTFIX-CONTINUATION-UNKNOWN、签 FASTFIX-R1-RESOURCE（R1 墙钟改为 1 小时）」（行 67）、「用户选 R1 简化计量…」（行 58）、「用户代 vlm 侧确认 R1 的 FASTFIX-MINI-MUTEX 窗口 ready」（行 50）；合同指针：提案「R1资源落实」§1–2（被 §4 替代部分除外）与「R1简化计量落实」§1–4。
- 来源校验（只读）：候选承接 A 账 候选 3/3、加载 3/14（`docs/evidence/P1-ENG-FASTFIX-001-ledger-A.json` 与 `-ledger-A-continuation.json` 未改、未重算）；R1 真实加载尝试 **0**（全部替身/合成检测，无 YOLO 构造）；候选新增 0；未建 R1 JSON 账本（按 §3 不建）。
- 窗口与起点（supervisor 原件 `~/fastfix-r1-20261011T214803Z/supervisor-readings.txt`）：ready 21:47:44Z；t0 = unix 1791755283.819（2026-10-11T21:48:03.819Z）；F0 = 119,660,436 KiB × 1024 = 122,532,286,464 B（`df -k /System/Volumes/Data` Available）。
- Review 读数（命令 `df -k /System/Volumes/Data` / `du -sk <绝对路径>`，UTC 为实际读取时刻）：

| 时刻（UTC） | F（Available×1024，B） | D = max(0, F0−F)（B） | du 副本（B） | du R1 临时目录（B） | S（B） |
|---|---|---|---|---|---|
| 21:50:13Z（建副本前） | 122,534,137,856 | 0 | — | 4,096 | — |
| 21:50:24Z（副本建好） | — | — | 82,116,608 | 4,096 | 82,120,704 |
| 21:52:35Z（首轮 focused 后） | 122,445,828,096 | 86,458,368 | 82,116,608 | 24,576 | 82,141,184 |
| 21:55:38Z（全部 focused 复跑后） | 122,325,942,272 | 206,344,192 | 82,116,608 | 49,152 | 82,165,760 |
| 22:01:34Z（删除副本前终读） | 122,190,905,344 | 341,381,120 | 82,116,608 | 49,152 | 82,165,760 |

- 停止线 2,700,000,000 B：D 与 S 全程远低于停止线，未触发 S-DISK；D 含同机其他进程写入，不作完整峰值主张（合同 §2 限制）。墙钟：验证（测试重跑）止于 21:55:38Z，读码/写文件止于 22:01:34Z，均在 t0+3000 s = 22:38:03Z 之前；最终 F1/t1/D 与 released 由 fast supervisor 调度 note 承接（本文件内账截至 22:01:34Z，其后副本删除/自检/提交推送尾量由 supervisor 终读覆盖）。
- 原件落点：`~/fastfix-r1-20261011T214803Z/`（`r1-focused.log`、`r1-focused-discover.log`、`r1-focused-admitted.log`、`tmp/`，收工保留）。STOP：无；未验证项见 §2/§3。

### §6 Verdict

**`REWORK_REQUIRED`**（本停点第 1 次，1/2）。阻断 finding：R1-1（CLASS_2，`BC-9`，直接交回实现角色；修复回本角色 `R2@K1K2K3K4`，不经核对轮；闭合绑定上文具名回归，复核以修前红/修后绿核实）。非阻断：N-1、N-2（覆盖缺口，建议同批补测试，不作闭合条件）、N-3…N-7（备注/读法留接受角色）、C3-1（CLASS_3 逐字补丁，由实现角色下次提交应用）。AC-8/16/17/18/20 `NOT_RUN` 附议；AC-14 窄修替代附议、不记全套通过；AC-15/19 现场项不签。无 `RED_LINE`、无 `blocks_consuming_gate`。开轮资格：R1-1 修复会触及 `controller/track_loop.py`（PLAY_GOVERNING）→ 修复候选有资格开 `R2@K1K2K3K4`；返工只限 R1-1（及可选 N-1/N-2 测试），不得整理新功能候选、不追加 A 候选额度之外的真实加载。本轮不写 `passed_candidate`。

边界自查：本会话未修改任何实现文件（`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零改动；副本内只建 `outputs/eng-loop`、`outputs/eng-det` 只读符号链接供测试读取，随副本删除）；主工作树只写本文件与 `docs/current-status.md`。

## R2@K1K2K3K4（2026-10-12，Mac mini）

Dispatch-Id `P1-ENG-FASTFIX-001-R2@K1K2K3K4-20261012T021740Z-6223`；requested.round `R2@K1K2K3K4`。增量轮（COORD-009 (b)）：先读 R1 全部 finding；本轮新阻断只来自修复触及行上的 CLASS_1/2、旧 finding 闭合失败、`RED_LINE` 与未改动行上标 `上轮漏检` 的 CLASS_1。

### §0 候选、基线、开轮资格与重跑

- `round_candidate: fd45b825ee6860a5151080801003727e05bee532`（派发指定；= 状态板交接行候选 4 的自证提交，`origin/main` 祖先，运行时 `git merge-base --is-ancestor` 成立）。候选 4 = `b8059c6`（代码+测试+C3-1 补丁）+ `fd45b82`（证据/状态板），与 handoff「R1-1窄修候选4自证」声明一致。
- 修复触及行基线 = R1 §0 `round_candidate`（`72b5c99`）。`git diff 72b5c99..fd45b82 -- controller tools tests config` = **4 文件**：`controller/track_loop.py`（+13/−3）、`tests/test_capture_session.py`（+59）、`tests/test_target_manager.py`（+59）、`tests/test_capture_isolation.py`（+2/−1）；`tools/`、`config/`、其余 `controller/` 零 diff。PLAY_GOVERNING 非空 → 开轮。
- 全量 diff 基线：仍无 `passed_candidate`，`$BASE` = 首条「A实现 候选1代码」提交的父提交（运行时解析 = `1345d2e4…`，与 R1 相同）。`git diff --stat $BASE..fd45b82 -- controller tools tests config` = 25 文件 +6262/−128（R1 为 +6133/−128，增量恰为本轮 4 文件）。冻结路径零 diff（运行时核）：`controller/det_assoc_tracker.py`、`config/scenario.default.json`、`config/det-assoc-v1.models.json`、`config/p1-eng-capture-001.json`、`Assets/`、`ProjectSettings/`、`Packages/packages-lock.json`、`tools/eng_loop2/`、`tools/eng_capture/`。改动文件 ⊆ 提案 §2.1 闭集。
- 自证四项（workflow §4.3.1）：范围冻结（只修 R1-1 + 可选 N-1/N-2/C3-1）、相称测试（focused 23 文件 + 具名红绿，`docs/evidence/P1-ENG-FASTFIX-001-tests-c4-focused.log`、`-r1-1-red.log`、`-r1-1-green.log`）、Unity 0/`NOT_RUN` 保持、证据/状态板同批——均成立，不 `REVIEW_BLOCKED`。
- 一次性副本：`.claude/worktrees/review-P1-ENG-FASTFIX-001`（detach 于候选，收工删除）。测试树哈希（副本 `git rev-parse`）：`HEAD:tests = a20af4bbf38f322c091c9c757f879cbe255e3ef9`、`HEAD:controller = 0f68a55333f5f6ffe01ff90cfb635eea397c8f89`、`HEAD:tools = 0a92e9ae82ae1eebe00c8ea7427711c74b2f0a9d`（与 R1 相同）、`HEAD:config = 4b4906a4a7202aeede9c9544f3c0db40589184a1`（与 R1 相同）。
- **R1-1 修前红/修后绿（本角色在副本核实）**：副本内 `git checkout 72b5c99 -- controller/track_loop.py`（只回退实现文件、保留候选 4 新测试）→ `TMPDIR=<R2 临时目录>/tmp ~/TetheredDroneTracking-full/.venv-yoloe/bin/python -m unittest discover -s tests -p test_capture_session.py -k write_failure_after_real_gate` → **Ran 2, FAILED (failures=2)**，两例均 `AssertionError: Lists differ: [] != [0.21875]` / `[] != [0.21875, 0.21875]`（只败在 `gate_eval_s`，原始输出 `~/fastfix-r2-20261012T021159Z/r2-r1-1-red.log`）；`git checkout fd45b82 -- controller/track_loop.py` 恢复后同命令 → **Ran 2, OK**（`r2-r1-1-green.log`）。恢复后副本 `git diff --stat HEAD` 为空。
- **重跑（focused 一次，零真实模型加载）**：与 R1 §0 / handoff 候选 4 节相同的 23 个测试文件，`discover -p <file>.py`（同一 venv 的顶层 `tests` 包遮蔽，环境非缺陷），副本内只读符号链接 `outputs/eng-loop`、`outputs/eng-det` 指向主树（准入帧元数据；替身检测，真实 YOLO 构造 0）。结果（原始输出 `~/fastfix-r2-20261012T021159Z/r2-focused.log`、退出码 `r2-focused-exits.txt`，02:20:45Z–02:21:18Z，不带 `-v`）：**21 文件 OK、2 文件失败**——`test_track_loop::test_cli_runs_pinned_csrt_to_a_versioned_summary`（失败）与 `test_language_k_binding`（导入错误）均为候选 1 全套日志已有的基线失败（逐名相同，与 R1 §0 相同）；**新增失败 0**。本项模块：`test_capture_session` 64 OK（62+2）、`test_target_manager` 78 OK（76+2）、`test_capture_isolation` 13 OK、`test_fastfix_replay` 3 OK、`test_language_loop` 205 OK、`test_fastfix_publish` 25、`test_fastfix_meter` 11、`test_fastfix_ledger` 11、`test_fastfix_window_meter` 4、`test_det_assoc_tracker` 37 OK。主树 `git status` 全程干净。

### §1 修复触及行逐文件核对（`72b5c99..fd45b82`）

- `controller/track_loop.py`：`_capture_frame` 在 `try` 前初始化 `settle = None`（:811；原 `settle = None` 位于机身步之后、`settle_frame` 之前的 :851 被删，语义不变——`settle_frame` 返回前它恒为 None）；异常分支 `_capture_partial_timing(..., settle=settle if settle is not None else self._unsettled_gate_evals(bundle.frame_id))`（:871）；新 `_unsettled_gate_evals` :993–999 只读 `publisher._frame_ctx`，`isinstance(ctx, Mapping)` 且 `ctx["frame_id"] == int(frame_id)` 才返回 `{"gate_evals": list(...), "outcome": None}`，否则 None（回落旧行为 `gate_eval_s=[]`）；不调用 `settle_frame`、不碰 streak/`escalation`/`fatal_reason`；`_capture_partial_timing` 新增仅关键字 `settle=None`（:1003），其他三处调用（`frame_missing`/`load_failed`/`step_failed`）不传、行为不变（`git diff` 无其他调用点变动）。与发布器对照：`begin_frame` :730 建 ctx 含 `"frame_id": int(frame_id)` 与 `"gate_evals": []`；`_classified_verdict` :797–798 每次门求值追加 `load_elapsed_s`；`observation` :534 底层写抛错时 WRITTEN 收据未追加、ctx 仍在；`_derived` :706–716 云台/速度底层写抛错同样上抛（`record_write_failure` 时先记 WRITE_FAILED 收据并置 `write_failed`）；`settle_frame` :747 首行把 `_frame_ctx` 置 None——故结算后再抛（如 `on_frame_settled`）走 `settle is not None` 分支，带真实 `settle_outcome`（handoff「未验证项」已如实声明，属同一字段更准确的记录，不分级）。`raise` 保留，fail-closed 上抛未改；`_emit_capture_timing` 不在异常路径调用 → 每帧仍恰一行。`Mapping` 已自 `typing` 导入（:12）。结论：R1-1 修复范围恰为合同「保留本帧已读门读数、不改 `settle_frame` 结算或 fail-closed 上抛」。
- `tests/test_capture_session.py::FrameTimingTests::_write_failure_after_real_gate`（+两例）：生产路径 fixture——`CaptureHarness` 构造真实 `LanguageSession`（真实 `TrackLoop`/`GatedPublisher`/`FixtureFramePublisher` 写临时 `runtime/`，收据与 `frame_timing` 从会话落盘文件读回）；`tail_harness(tail_s=0.0)` 使 `load_elapsed` 低于 `t_pub`、真实分级门 PASS（断言 `seen` 全为 `PASS`，并由包装 `_classified_verdict` 取同次门 `detail.load_elapsed_s`）；替换的是 `gated._publisher`（inner 写出器）的 `observation`/`look_at`，门与收据链路不绕过；断言恰一行、`failed`、`settle_outcome is None`、`missing_reason.frame == "publish_failed:OSError"`、已到达段 `(0.125, 0.03125, 0.0)`、`publish_s` None、`gate_eval_s == [门读数]`（观测例 1 个、云台例 2 个且首读数 == 该帧 `observation` WRITTEN 收据 `detail.load_elapsed_s`）、观测例该帧无 observation 收据。满足 R1 §3 R1-1 闭合绑定与 workflow §4.4 闭合四条（(1) 生产路径 fixture；(2) 本轮红/绿；(3) 不触及 Play 治理门三文件；(4) 不适用）。
- `tests/test_target_manager.py::ReacquireHintTests`（+两例，N-1）：8×8 非对称/非半正定 → `hint_invalid`（经 `make_full_kf_state` + `escalate`，`skipped == ["hint_invalid"]`）；深复制例走生产取数 `full_kf_state_from_associator`，取数后原地改库轨迹 `mean`/`covariance`，状态与提示不变。覆盖 N-1，代码未改。
- `tests/test_capture_isolation.py`：`FASTFIX_RUNTIME_FILES` 加入 `tools/eng_fastfix/window_meter.py`（:155–157），:176 的静态导入图/真值 token 检查随之覆盖该文件；本轮 13 例 OK。覆盖 N-2。
- `docs/evidence/P1-ENG-FASTFIX-001-K1K2K3K4-handoff.md`：C3-1 逐字补丁已按 R1 §3 原文应用（`b8059c6`）；新节「R1-1窄修候选4自证」与本轮核实一致（diff 行数 +13/−3、四项自证、逐 AC 指针、未验证项、最小资源记录）。
- `docs/current-status.md`（`fd45b82`）：Current state 段、Gate board 行（A 候选 4）、交接行与 Log 条目与候选事实一致；供 supervisor 后续登记的窗口字段已由其后提交承接（`81256c8`、`16fb52c`）。

### §2 AC 增量判定（依据列 `BC-n` 读作 AC-n；未列者沿 R1 §2，本批未改相应代码）

| AC | 本轮判定 | 依据 |
|---|---|---|
| AC-9 | **成立** | R1-1 闭合：真实门后底层观测/云台写失败路径保留 `gate_eval_s`（两例红→绿，§0）；正常/旧帧/解码失败/关联异常/管理器异常路径沿 R1 成立（`FrameTimingTests` 本轮 64 OK）。 |
| AC-2 | 成立（沿 R1） | fail-closed 上抛未改（`raise` 保留；新例 `harness.publish(1)` 仍抛 `OSError`）；`DegradeTests` 本轮重跑通过。 |
| AC-3 | 成立（沿 R1） | `settle_frame` 零 diff；`_unsettled_gate_evals` 不触碰 streak/升级；`EscalateTests`/`CompatUnchangedTests` 通过。 |
| AC-5 | 成立（N-1 覆盖缺口已补） | 新两例实跑通过；代码未改。 |
| AC-12 | 成立（N-2 覆盖缺口已补） | 冻结路径零 diff、改动文件 ⊆ 闭集（§0）；静态图集合扩至 `window_meter.py`；兼容既有测试新增失败 0。 |
| AC-14 | 本候选按工程 §6 窄修替代（不记全套通过） | 候选 4 相对候选 1（上个全套候选）累积改动限具名文件、不触及真实模型加载器/数据划分/对外指标路径；focused 23 文件 + 具名红绿；本轮独立重跑新增失败 0。**附议替代充分**。 |
| AC-8/16/17/18/20 | `NOT_RUN` | TX/B/C 未签 0；附议 `NOT_RUN`，不阻断。AC-15/19 现场项不签（沿 R1）。 |

### §3 Findings（本轮）

| ID | 分级 | 依据列 | 内容 |
|---|---|---|---|
| R1-1 | **已闭合** | `BC-9` | 修前红（2 失败，只败 `gate_eval_s`）/修后绿（2 OK）本轮在副本核实（§0）；生产路径 fixture；修复不触及 Play 治理门三文件；不改 `settle_frame`/fail-closed。 |
| N-1、N-2 | 已覆盖 | — | 候选 4 同批补测试，§1。 |
| C3-1 | 已应用 | — | 逐字补丁与 R1 §3 相同（§1）。 |
| N-8 | 备注（不分级、不阻断） | — | 若异常恰在 `settle_frame` 内部抛出（它已在首行把 `_frame_ctx` 置 None），`_unsettled_gate_evals` 返回 None → `gate_eval_s=[]`；`settle_frame` 为纯内存运算、无 I/O，仓库内无可达触发状态，仅作读法备注。 |
| N-3…N-7 | 保持 | — | 读法留接受角色，本轮不新增范围（工程 §5「返工轮不追加范围外新主张」）。 |

本轮无新 CLASS_1/2、无 `RED_LINE`、无 `上轮漏检`、无 `blocks_consuming_gate`。

### §4 UNITY_NA 与红线

- `UNITY_NA`：实现者未对候选 4 申请（阶段 A Unity/Play = 0，AC-16…18 `NOT_RUN`），无须附议；AC-8 `NOT_RUN` 附议。
- 红线：修复触及行 grep 无 `truth`/`CoverageEvaluator`/`m3_body`；真值仍只在 `score.py::score_*`；`test_capture_isolation` 毒化真值/静态图用例本轮实跑通过（含新纳入的 `window_meter.py`）。无 `RED_LINE`。

### §5 R2资源记录（提案「返工资源落实」§2–3，沿「R1简化计量落实」§2–4）

- 授权：`docs/authorizations.md` 2026-10-12「用户签 R1-1 窄修返工资源（第 4 个候选 + 实现/R2 两个简化计量窗口）」（行 66）、「用户代 vlm 侧确认 R2 窗口的 FASTFIX-MINI-MUTEX ready」（行 50，at 02:11:42Z）；合同指针：提案「返工资源落实」§2（R2 窗口列）与「R1简化计量落实」§2–4。
- 来源校验（只读）：候选承接 4/4（本窗新增 **0**，不修代码、不整理新候选）；真实模型加载本窗 **0**，累计仍 3/14（两份旧 JSON 账本未改、未重算）；未建 JSON 账本。
- 窗口与起点（supervisor 原件 `~/fastfix-r2-20261012T021159Z/supervisor-readings.txt`）：ready 02:11:42Z；t0 = unix 1791771119.843857（2026-10-12T02:11:59.844Z）；F0 = 108,975,092 KiB × 1024 = 111,590,494,208 B；收尾线 03:01:59Z、硬界 03:11:59Z。本角色开工 02:18:35Z（派发 started）。
- Review 读数（`df -k /System/Volumes/Data` Available×1024；`du -sk <绝对路径>`×1024；原件 `~/fastfix-r2-20261012T021159Z/review-readings.txt`）：

| UTC | F（B） | D = max(0, F0−F)（B） | du 副本（B） | du R2 临时目录（B） | S（B） |
|---|---|---|---|---|---|
| 02:19:56Z（建副本前） | 111,583,703,040 | 6,791,168 | — | 8,192 | — |
| 02:19:56Z（副本建好） | — | — | 82,292,736 | 8,192 | 82,300,928 |
| 02:21:36Z（红绿 + 全部 focused 后） | 111,500,992,512 | 89,501,696 | 82,292,736 | 36,864 | 82,329,600 |
| 02:22:47Z（删除副本前终读） | 111,513,386,368 | 77,107,840 | 82,292,736 | 36,864 | 82,329,600 |

- 停止线 2,700,000,000 B：D 与 S 全程远低于停止线，未触发 S-DISK；D 含同机其他进程写入，不作完整峰值主张（合同限制）。墙钟：验证（红绿 02:20:33Z–02:20:34Z，focused 02:20:45Z–02:21:18Z）与读码止于 02:22:47Z 删除副本，均在 t0+3000 s = 03:01:59Z 之前；最终 F1/t1/D 与 released 由 fast supervisor 调度 note 承接（本文件内账截至 02:22:47Z，其后自检/提交推送尾量由 supervisor 终读覆盖）。
- 原件落点（收工保留）：`~/fastfix-r2-20261012T021159Z/`（`supervisor-readings.txt`、`review-readings.txt`、`r2-r1-1-red.log`、`r2-r1-1-green.log`、`r2-focused.log`、`r2-focused-exits.txt`、`tmp/`）。STOP：无；互斥窗口内未见别路冲突。

### §6 Verdict

**`REVIEW_PASSED`**（`R2@K1K2K3K4`）。R1 阻断 finding R1-1 已闭合（本轮红绿核实，生产路径 fixture）；修复触及行无新 CLASS_1/2；N-1/N-2 覆盖已补、C3-1 已应用；无 `RED_LINE`、无 `blocks_consuming_gate`。AC-9 成立；AC-14 窄修替代附议、不记全套通过；AC-8/16/17/18/20 `NOT_RUN` 附议；AC-15/19 现场项不签。本候选通过不等于验收：阶段 A 仅离线证据，TX/B/C 未签 0、Unity/Play 0、旧/续做磁盘 UNKNOWN 与 OPEN 债保持；通过轮的消费、Overall 与 AC 表更新归接受角色。

passed_candidate: fd45b825ee6860a5151080801003727e05bee532

边界自查：本会话未修改任何实现文件（`controller/`、`Assets/`、`tools/`、`tests/`、`config/` 零改动；副本内的 `controller/track_loop.py` 回退/恢复只为修前红核实、恢复后 `git diff` 为空且副本已删除；`outputs/eng-loop`、`outputs/eng-det` 只读符号链接随副本删除）；主工作树只写本文件与 `docs/current-status.md`。
