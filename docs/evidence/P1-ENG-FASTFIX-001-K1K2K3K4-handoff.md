# P1-ENG-FASTFIX-001 代码停点 K1K2K3K4 交接（阶段 A，A实现）

- 轮次 `A实现`；Dispatch-Id `P1-ENG-FASTFIX-001-A实现-20261010T233353Z-dc6c`；实现角色（Opus 子代理，Mac mini）。
- 合同：同名提案 D2 `ACCEPTED`（`engineering-v1`）正文 §2.1–§3.8、AC-1…20、「D2 接受裁定」首次接受释义 1–6、「D2预检核清」、「A首签落实」§1–3。
- 信封：`docs/authorizations.md`「2026-10-10 P1-ENG-FASTFIX-001 — 用户首签 FASTFIX:A:1（阶段 A，Mac mini 离线）…」；资源账见 §R。
- 请求：Acceptance 核对轮 `C1@K1K2K3K4`（本停点首次候选），核对后交 Review `R1@K1K2K3K4`。不触发 K5；B/C 未签、未运行。

## §1 开工同步与路径登记（「A首签落实」§3 第 1–2 步）

| 项 | 事实 |
|---|---|
| supervisor 代做的同步（不是实现角色完成的步骤） | supervisor 开工时在 mini 主树 `git fetch -q` + `git pull -q --ff-only`：HEAD `353812a` → `d26d894`（75 提交），reflog 完成时刻 2026-10-10T23:32:45Z，前后工作树干净；新增 git 字节 = 当刻落盘 pack 2,166,179 B + idx 13,112 B = **2,179,291 B**（`ls -l .git/objects/pack`，实测）；墙钟起点未记录（reflog 秒级只记完成时刻），入账取 5 s 保守估计区间 |
| 实现角色开工核对 | 23:34:50Z 工作树干净，HEAD = origin/main = 派发登记提交；`git fetch` + `git merge --ff-only origin/main` → Already up to date（0.56 s，新增 0 B） |
| 二次同步（supervisor 转告 COORD-019） | 00:17:29Z `git fetch` + 仅快进到 origin/main（含 COORD-019 三提交与 vlm 路登记），0.73 s；`.git` du +380 KiB；未 merge/reset/覆盖 |
| 仓库 | `~/TetheredDroneTracking`（主树；vlm 路独立克隆 `~/TetheredDroneTracking-vlm` 与 `~/vlm-diag/` 不在本项计量根内） |
| 解释器 | `~/TetheredDroneTracking-full/.venv-yoloe/bin/python`（Python 3.12.14；只读使用、未装包；全部运行带 `PYTHONDONTWRITEBYTECODE=1`、`YOLO_OFFLINE=True`、`YOLO_AUTOINSTALL=False`） |
| 权重/规格 | `~/TetheredDroneTracking/outputs/eng-det/runs/run-1/weights/last.pt` sha `d6a0d6a9…059c9`（现核 = `config/det-assoc-v1.models.json`，diff 为空） |
| 准入原件 | `~/TetheredDroneTracking/outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261008T213653Z/`（只读；回放前现核 1,658 帧文件 sha 全一致） |
| 输出/计量根 | `outputs/eng-fastfix/`（新增 `.gitignore` 行，不入仓）；计量根 = `outputs/eng-fastfix`、`.git`、`$TMPDIR`、会话 scratchpad、`~/.claude/projects/-Users-zc5-TetheredDroneTracking`（客户端日志，含父会话，偏大） |

## §2 候选与 diff 范围

- 候选 1 = 提交「P1-ENG-FASTFIX-001 A实现 候选1代码…」+「…忽略 outputs/eng-fastfix/…」；候选 2 = 候选 1 + 本交接同批提交中的具名窄修
  （只改 `tests/test_det_assoc_tracker.py` 一处白名单，见 §4）。**交复核的是候选 2**（本交接所在提交）。
- 完整候选 diff：`git diff <二次同步后的 origin/main 基点>..<本交接提交>`，可用 `git log --format=%H --grep='P1-ENG-FASTFIX-001 A实现'` 运行时解析首末提交
  （`git diff $(git log --format=%H --grep='A实现 候选1代码' -1)^ <本交接提交>`）。不手抄 SHA。
- 推送前按 supervisor 转告（COORD-019）把本项提交变基到 origin/main 之后（只带入上游文档/派发登记提交，无代码改动）；故候选提交 SHA 在全套运行后变化、内容不变，全套日志记录的是变基前的同内容提交。
- 改动文件：运行时 `controller/{gated_publisher,track_loop,language_loop,target_manager,language_bridge,resident_core}.py`、
  `config/p1-eng-fastfix-001.json`、`tools/eng_fastfix/{__init__,common,ledger,meter,replay,score}.py`（⊆ §2.1 闭集）；测试
  `tests/test_fastfix_{publish,meter,ledger,replay}.py`（新）与 `tests/test_{capture_session,target_manager,capture_isolation,language_bridge,language_loop,det_assoc_tracker}.py`（扩/改）；
  `.gitignore` 一行（非运行时，IR-12）；证据 `docs/evidence/P1-ENG-FASTFIX-001-*`。`controller/det_assoc_tracker.py` diff 为空。

## §3 四项自证（workflow §4.3.1）

1. **范围与接口冻结**：G1–G5 按 §3.1–§3.7 落实；新名字只在闭集末尾追加；实现读法 IR-1…16 列于 §6 待裁定，不自行扩大闭集。
2. **相称测试通过**：停点全套（候选 1 唯一一次）新增回归 1 条 → 具名窄修（候选 2）focused + 修前红/修后绿闭合，见 §4；全部新增用例通过。
3. **Unity**：本阶段 Unity/Play = 0，无已知 Unity 失败；B/C 现场项未运行（`NOT_RUN`）。
4. **状态板、候选提交、未验证风险已更新**：状态板交接行与 Log 同批更新；复核文件属复核角色（本角色不写），复核范围见 §5；未验证风险见 §7。

## §4 测试证据

**停点全套（AC-14，候选 1 唯一一次）**：`docs/evidence/P1-ENG-FASTFIX-001-tests.log`（启动时 HEAD = 候选 1 第二提交，工作树只有账本改动；
`/usr/bin/time -p <数据根>/.venv-yoloe/bin/python -m unittest discover -s tests`，不带 `-v`）：**Ran 2776，failures 29、errors 34、skipped 56**，
real 562.78 s，exit 1。失败集（`FAIL:`/`ERROR:` 头，含子测试）63 条 vs 基线 = CAPTURE 候选 3 全套 `docs/evidence/P1-ENG-CAPTURE-001-tests.log` 的 62 条
（其后至本项基点 `controller/ tools/ tests/ config/` 无改动，git 现核）：**基线已有 62 条全部仍在（无消失）；新增 1 条**：
`test_det_assoc_tracker.ClassPolicyTests.test_new_values_only_passed_by_capture_entry_points`——其白名单只认捕获会话入口与 `tools/eng_capture/`，
本项 AC-7 捕获模式离线回放 `tools/eng_fastfix/replay.py` 显式传 `unify_vehicle`/`pose-center` 被判越界。
环境差异：基线由仓库 `.venv-yoloe` 跑，本次按派发用数据根 venv（numpy 2.5.1 vs 2.5.3），失败集除上述 1 条外逐条相同。

**具名窄修（候选 2）**：只改 `tests/test_det_assoc_tracker.py` 该用例白名单加入 `tools/eng_fastfix/`（与会话同一捕获链，IR-13）。修前红 = 上述全套日志中
该条 FAIL；修后绿 = `PYTHONPATH=tests <venv> -m unittest test_det_assoc_tracker.ClassPolicyTests`（6 OK）与 `test_det_assoc_tracker` 整模块（37 OK）。
按 engineering-workflow §6：只改具名测试文件、不触及真实加载器/数据划分/对外指标路径，**未跑候选 2 全套、不记全套通过**；复核可判替代不足并要求全套。

**真实构造**：全套按 F12 闭集 = `CarrierSelfTest` 类级 `_ready()` 为真、两例均执行（其一为基线已有失败）→ **2 次**（按闭集推定，未插桩计数；
未超闭集，S-LOADER 未触发）；AC-7 回放 1 次（`CountingModel.loads`=1）。

**逐 AC 证据**（开发期 focused 均在数据根 venv，`PYTHONPATH=tests`）：

| AC | 停点 | 证据指针 | 结果 |
|---|---|---|---|
| AC-1 | K1 | `test:tests/test_fastfix_publish.py::ClassifyRowTests`（§3.1 逐行 12 例）、`::ClassifyCrossTests`（2+3、4c+5e、5b+5d、5b+3 及预测云台完整性不降级）、`::CompatGateTests`（同注入首命中首拒；`_gate` 函数体与接受基线 AST 段逐字相同） | 通过 |
| AC-2 | K1K2 | `test:tests/test_capture_session.py::DegradeTests`（观测时序命中；预测云台命中；观测 WRITTEN 后云台越线；观测与云台 WRITTEN 后速度越线（复现 0.55 s 形态）；每 DROPPED 帧恰一条 hold、无 orphan、管理器与未注入对照逐字段相同、下一帧 PUBLISHED/FOLLOW 恢复、`resident_rebuilds=0`） | 通过 |
| AC-3 | K1K2 | `test:…::EscalateTests`（第 N_drop 帧结算升级、原因名不变、重建 +1；PUBLISHED 清零；完整性任意 streak 致命；hold/NO_ATTEMPT/写失败不计不清）、`::CompatUnchangedTests`（兼容会话不启用分级/结算/标记/链；未分级发布器收据与接受基线导出包逐条相同） | 通过 |
| AC-4 | K1 | `test:…::BacklogTests`（只最新帧开上下文与结算、第 3 个降级最新帧升级；墙钟同步推进时 10×0.5 s 积压触 5e 完整性致命，IR-9）、`::ProjectionTests`（`publish_degraded` 与恢复、其他原因优先、闭集末尾追加静态检查） | 通过 |
| AC-5 | K3K2 | `test:tests/test_target_manager.py::ReacquireHintTests`、`::ReacquireWindowTests`、`::ReacquireReplayTests`；`test:tests/test_capture_session.py::ReacquireSessionTests`（会话全链：升级→提示→新载体→窗口→提交、窗口内零 look_at/速度且每最新帧恰一次 hold、帧号/零帧 monotonic 截止、歧义、点击取消并执行点击、拒收点击取消任务、stop/release 优先、token 不符拒、off 臂与非时序拆载体、rebuild_limit 作废提示、`tm_inputs` 重放事件逐条相同） | 通过 |
| AC-6 | K3 | `test:tests/test_target_manager.py::ReacquireNegativeTests`（尺寸/运动不过、出画失败、25°/帧滚转映射后判门与未映射对照、映射失败/非有限/S 奇异/相机背后无证据且缓冲清零、门只用合成先验的反证、`reacquire_gate` 拒库阶段、`motion_size_gate` 与接受基线 500 组随机输入逐值相同、钉版库 `KalmanFilterXYWH.predict` n 步与 `apply_pose_center` 均值/完整协方差对照） | 通过 |
| AC-7 | K3K4 | `artifact:docs/evidence/P1-ENG-FASTFIX-001-replay.md` §1–2 | **满足**：on 臂 n_committed = 3，全部提交 IoU ≥ 0.5（0.926/0.943/0.815）；off 臂自动提交 0；9 次 not_applicable |
| AC-8 | K1K3 | `artifact:…-replay.md` §3 | **`NOT_RUN`**（TX = 0；648–650 缺处理记录） |
| AC-9 | K1 | `test:tests/test_capture_session.py::FrameTimingTests`（每帧恰一条、假时钟段之和逐值 = total、`gate_eval_s` = 同次门 `load_elapsed`、`journal_prev_s` 单列、失败帧缺段带原因、桥文件无新字段） | 通过 |
| AC-10 | K1 | `test:tests/test_fastfix_publish.py::ConfigTests`（读配置、违约束拒绝启动、首候选 = 现行常数、无 `ρ_reacq`、`K_PUB`/`T_STALL_S`/`RESIDENT_REBUILD_LIMIT` 与接受基线字面量相同、会话坏配置拒启） | 通过 |
| AC-11 | K2 | `test:tests/test_fastfix_meter.py`（15 万路径 × 5 s 假遍历中停令延迟 ≤ 1 s、只遍历声明根、采样 start/end、1 MB 级上限截断记 `meter_truncated` 并停、S-DISK、只 lstat、不导入 controller/不含真值） | 通过 |
| AC-12 | K4 | `test:tests/test_capture_isolation.py::FastfixTruthIsolationTests`（静态导入图、`score_` 名与真值词只在 `score.py::score_*`、毒化真值旁置时回放产物逐字节相同且审计无真值打开、捕获会话旁置真值不被打开）、`::FastfixFrozenPathTests`（禁改路径 diff 为空、运行时改动 ⊆ §2.1 闭集、`LanguageWorker`/`CandidatesBackend`/`_validate_candidates_source` 不变）；兼容模式既有测试无新增失败（全套，§4） | 通过 |
| AC-13 | K4 | `test:tests/test_target_manager.py::R22ChainTests`（v2 生产字节删任一中间行——含 `frame`/`reacquire_hint`/`reacquire_window`/`teardown`——与重排即拒；帧连续性；修前红生产对照 `test_base_v1_silently_accepts_deleted_line`：v1 删行静默重放）；R1-4 不触发（本项账本自写，未调用 `tools/eng_capture/ledger.py` 任何函数；回放只导入 `CountingModel`/`CachedOrLiveModel`/`CacheFrame`/`library_boxes`/`boxes_rows`）；两条旧债状态不改 | 通过 |
| AC-14 | K1K2K3K4 | `cmd:` 见上；`artifact:docs/evidence/P1-ENG-FASTFIX-001-tests.log` | 候选 1 全套已跑：新增 1 → 候选 2 窄修红/绿（未跑全套）；构造 2 |
| AC-15 | K1K2K3K4 | `artifact:docs/evidence/P1-ENG-FASTFIX-001-play-ops.md` | 两份操作单已准备（B/C 未签、未执行） |
| AC-16…18、20 | Play | — | `NOT_RUN`（B/C 未签） |
| AC-19 | K4 | `test:tests/test_fastfix_ledger.py`；实账 `artifact:docs/evidence/P1-ENG-FASTFIX-001-ledger-A.json` | 通过；本阶段已按该账本启动前拦截 |

## §5 复核范围（R1@K1K2K3K4）

候选 2 全部 diff（§2）。重点：`GatedPublisher._gate_classified`/`_classified_verdict`/`begin_frame`/`settle_frame`/`_derived` 分支（K1/K2）；`TrackLoop._capture_frame`
帧上下文与计时（K1）；`TargetManager` 重捕状态机（`prepare_reacquire_hint`、`open_reacquire_window`、`_reacquire_frame`、`reacquire_gate`、`_commit_precheck`/`_plan_commit`
的 `reacquire` 分支、`_release`/`_teardown`/`_stop` 的取消、`synthesize_reacq_prior`/`pose_center_transform`）（K3）；会话接线（`_prepare_reacquire_hint`、
`_note_hint_candidate`/`_on_frame_settled`、`_handle_reacquire_result`、窗口开窗、点击/release 取消、投影）（K2/K3）；链式 `InputsLog`/`check_chain`/重放（K4/R2-2）；
`resident_core.FullKfState` 只读访问器；`tools/eng_fastfix/` 与隔离（K4）。复核 focused 与红绿可全用替身（零模型）；`ReacquireNegativeTests::test_pinned_library_kf_and_apply_pose_center_match`
与 `test_fastfix_replay.py` 需数据根 venv（导入钉版库、不构造模型）。

## §6 实现读法待裁定（IR；实现角色不写提案，请 Acceptance 在核对轮裁定）

| IR | 读法 | 位置 |
|---|---|---|
| IR-1 | `m_assoc` 取 `tracker.step()` 返回时刻（`det_assoc_tracker.py` diff 须为空，库 `update` 返回不可在其外取）；`associate_s` 含库关联与历史记录。`m_read0` = 图像字节读取前（`FrameRepository.load` 先读/校验元数据 JSON，该段不在 `total_s` 内） | `track_loop.py::_resident_frame`/`_emit_capture_timing`；`gated_publisher.FrameSnapshotRing.image_loader` |
| IR-2 | 帧结算优先级 FATAL > DROPPED（+1）> WRITE_FAILED（不计不清）> PUBLISHED（清零）> NO_ATTEMPT；同帧既降级又写失败按 DROPPED 计 | `GatedPublisher.settle_frame` |
| IR-3 | 分级门 5a–5e 用同一次 `monotonic()`/`unix()` 读数，读取位置与现行 `_gate` 相同（身份与帧差核验之后） | `_gate_classified` |
| IR-4 | 新载体起点帧（f_ready）在 `loop.start` 内先于 `resident_loop_started` 处理，窗口在该事件开；证据从 f_ready+1 起收，f_ready 计入帧截止 | `language_loop._ensure_resident_loop` |
| IR-5 | 窗口内（ACQUIRING、无绑定）沿用现行授权函数：落「输入不一致 → HOLD/不发」（`authorization_input_inconsistent`），授权函数未改 | `target_manager.derive_authorization` |
| IR-6 | 窗口内 release 只在 `REINIT_REQUIRED` 且 token = 拆载体前对外指针时受理；点击取消提示后若点击被拒，以 `release_binding("reacquire_canceled", cancel_task=True)` 取消任务，会话原因回到触发拆载体的 `seg_end` | `_action_release`/`_action_click` |
| IR-7 | 合成先验对提示 posterior 直接连推 n 次库 `predict`（未施加库 `multi_predict` 对非 Tracked 轨迹的宽高速度置零），再一次性 `pose_homography(f_last, f)` | `synthesize_reacq_prior` |
| IR-8 | 会话提示候选 = 本批最新帧、管理器本帧已接受观测、帧结算 PUBLISHED/DROPPED；回放无发布门，每帧按 PUBLISHED 记 | `_note_hint_candidate`；`replay.CaptureRun._note_candidate` |
| IR-9 | AC-4「10 帧 × 0.5 s」若墙钟同步推进，最新帧采集年龄 ≈ 5 s > `T_stall` → 步 5e 完整性致命（不降级）；streak 路径以只推进 monotonic 的同一积压验证 | `BacklogTests` |
| IR-10 | 库 KF 预测器取不到不列入跳过原因；窗口照开、逐帧无证据、到期失败 | `_prepare_reacquire_hint` |
| IR-11 | 链式 v2 只用于捕获会话落盘输入；兼容模式与 CAPTURE v1 旧工件按原规则重放；v2 init 带 FASTFIX 参数时重放须给同一 FASTFIX 配置 | `InputsLog`/`replay_tm_inputs` |
| IR-12 | `.gitignore` 加 `/outputs/eng-fastfix/` 一行（非运行时，在 §2.1 代码闭集之外） | `.gitignore` |
| IR-13 | 两处既有静态白名单随本项扩写：`test_det_assoc_tracker` 捕获入口白名单加 `tools/eng_fastfix/`（候选 2 窄修）；闭集断言（`STATE_REASONS`、`RECEIPT_OUTCOMES`、`continuity_broken` 位次）改为前缀逐位 + 末尾追加；本项闭集检查只核运行时路径并排除协调批次基础设施 | 测试文件 |
| IR-14 | AC-7 回放时钟 = 帧元数据 `capture_monotonic_s`；就绪帧 = 注入帧 + 4；只对点击帧前 10 帧起（第 520–828 帧）建缓存与回放 | `tools/eng_fastfix/replay.py` |
| IR-15 | 计量工具输出截断即按「计量失联」请求停令（不无监控继续）；客户端日志根取整个项目目录（含父会话，偏大） | `meter.py`；§R |
| IR-16 | AC-11「≤ 1 s」测量为停令文件出现到 `run()` 返回；节拍 0.5 s、采样线程逐条目检查停止事件 | `MeterTests` |

## §7 未验证项与已知限制

- 全部会话层证据为假时钟/假检测（零模型）；真实时序、积压与重建耗时只在 B 冒烟/C 正式中观察（未签）。门值 0.4 s/2 帧为移植限值，未在本机标定。
- AC-7 只覆盖红车可见的 530–600 区间（3 次可适用注入）；误绑 0 为 n = 3 样本观察，不推误重捕率；回放为离线等价时钟。
- AC-8 `NOT_RUN`；AC-16…18/20 未运行；无 `UNITY_NA` 主张（运行时功能，需 Play）。
- 候选 2 未跑全套（窄修替代）。全套真实构造按 F12 闭集推定 2。

## §R 阶段 A 资源账（截至本交接提交前；`docs/evidence/P1-ENG-FASTFIX-001-ledger-A.json`）

| 维度（信封） | 已耗 | 说明 |
|---|---|---|
| 候选（≤ 3） | 2 | 候选 1；候选 2 = 具名窄修 |
| 真实 YOLO 构造（≤ 14） | 3 | AC-7 回放 1（实测）+ 候选 1 全套 2（F12 闭集推定）；尝试即记 |
| 验证执行及收尾墙钟（≤ 2 h） | 1030.614 s（账本区间并集，含收尾估计上界 210 s） | 区间并集：两次同步（supervisor 段为 5 s 估计）、focused/探针、回放 11.6 s、评分、全套 562.9 s、窄修红绿、计量运行及自检/提交/变基/推送收尾；未计时项仍标估计。Acceptance C1 只读核账后勘误摘要，未改账或新增执行 |
| 新增磁盘峰值（≤ 2 GB） | ≤ 20 MB（入账 20,000,000 B） | 构成见账本该条；TMPDIR 峰值为 2 s 采样所得（瞬时更短写入不可见，属采样分辨率限制）；`df` 受系统其他写入影响不作依据 |
| live 推理帧 | 309 | 不单列维度（受加载与墙钟约束）；只记读数 |
| scenario/session/run ID、Unity/Play、API、云、训练、下载、安装、板端、角色 TX | 0 | — |

并行作业：vlm 路 supervisor 在同机另起零消耗诊断（独立克隆与仓库外目录），其磁盘/墙钟不在本账；本账未按整盘余量计。

## §C1R C1退回修复：C1-4 资源零消耗核清 → S-UNKNOWN 停报（2026-10-11）

- 轮次 `C1退回修复`；Dispatch-Id `P1-ENG-FASTFIX-001-C1退回修复-20261011T004342Z-a778`；实现角色（Opus 子代理，Mac mini）。依据：同名提案「Contract conformance（核对表）」→「C1@K1K2K3K4」→「定向退回与资源勘误」末段（先零消耗核清既有峰值覆盖/保守上界与剩余量，不能复原的部分依原 S-UNKNOWN 停报）。
- 开工：2026-10-11T00:45:52Z 主树干净，HEAD = origin/main = 本次派发登记提交；`git fetch` + `git merge --ff-only origin/main` → Already up to date（0.64 s，`.git` du +0）。
- **结论：A 既有新增磁盘峰值无法复原出可核的保守上界 → `S-UNKNOWN`。** 账本 `disk_peak_bytes` 本轮置 `UNKNOWN`，A 一切后续消耗停止；C1-1…4 的代码/文档修复**未开始**，候选 3 未开（候选仍 2/3）；未跑任何测试、未构造模型。

### §C1R-1 墙钟（可核清：保守上界）

- 账本校验和有效，区间并集现算 = 1030.614 s，与 `used.wall_s` 一致。
- 但 reflog 显示账本区间外仍有实现执行：`merge origin/main: Fast-forward` 于 unix 1791677733（00:15:33Z），候选 1 两笔提交（含 pre-commit 钩子自检）于 1791677875、1791677892；三者均不在任何已记区间内（耗时未计时）。另有 4 段估计区间（5/40/45/210 s）。
- 保守上界：A 实现会话的全部执行（账本区间 + reflog 可见的执行）都落在 [1791675160.0, 1791678843.457]（supervisor 同步估计起点 → 收尾估计终点）内，跨度 **3683.457 s**；本轮把该跨度作为一条保守区间补入账本（并集只增不减，不推余额）。起点仍沿用原 5 s 估计这一处估计标签。
- 本轮零消耗核清执行区间并集 203.763 s（含被中止的窗口文件扫描保守区间 202.8 s），另记收尾估计上界 240 s。

### §C1R-2 加载与候选（无新信息，沿原读法）

- 真实 YOLO 构造 3/14：AC-7 回放 1（`CountingModel.loads` 实测）+ 候选 1 全套 2（F12 闭集推定、非插桩；C1 已按此读法核账）。本轮 0。
- 候选 2/3；本轮未开候选 3。

### §C1R-3 磁盘峰值（不可复原 → UNKNOWN）

| 缺口 | 事实 | 能否复原 |
|---|---|---|
| 时间覆盖 | 计量工具只覆盖 [1791677901.1, 1791678551.9]（650.8 s，`outputs/eng-fastfix/meter-A/meter-replay.jsonl`，303 次采样，采样峰值增量 10,703,749 B）；focused-1…13、探针、两次同步、候选 1 提交与收尾均**无任何采样** | 否：事后无记录 |
| 采样间瞬时 | 2 s 间隔、每次遍历约 0.1–0.2 s；测试临时目录在两次采样之间建删即不可见 | 否：退出进程的写字节计数不可回取 |
| 根覆盖 | 计量根只有 `outputs/eng-fastfix`、`.git`、`$TMPDIR`、会话 scratchpad、`~/.claude/projects/<本项目>`。本轮对 A 窗口（mtime ∈ 19:32:40–20:34:04 本地）做的只读扫描（约 200 s 后中止，只覆盖 `$HOME` 一部分）已见计量根外 869 个文件/34,865,756 B，例如 `~/.claude/plugins/` 约 16.4 MB、`~/.claude/file-history/` 1.4 MB、`~/.claude/backups/` 3×72 KB、`~/Library/Application Support/Claude/` 2.0 MB、`~/Library/Logs/Claude/` 0.28 MB；归属（本角色 / 客户端自更新 / vlm 路与其他会话）无法判定；`$(getconf DARWIN_USER_CACHE_DIR)`、工作树内非 git 跟踪文件、`/private/tmp` 未扫到 | 部分可列（下界），完整上界否 |
| 进程级累计写 | 套件进程已退出，单进程 rusage 不可取；Claude.app 进程联盟（2026-10-09 23:56 本地起）累计 `byteswritten` 5,531,361,280 B、逻辑延迟写 10,432,124,786 B（读于 unix 1791679928），含全部会话与两路自应用启动以来的写入，> 2 GB，无法分出 A 的份额 | 否 |

故原 20 MB 入账既不覆盖全部根、也不覆盖瞬时，且无可核的保守上界 ≤ 2 GB 可替代；依 §6 S-UNKNOWN 与首次接受释义 5「无法计量的部分为 UNKNOWN，停报，不自行补 0 或申请豁免」处置：不推余额、不重试、不开新消耗。

### §C1R-4 停报待裁定（回用户）

- 题 `FASTFIX-A-DISK-UNKNOWN`：A 既有新增磁盘峰值 UNKNOWN 如何处置。账本已 UNKNOWN 锁定（`ledger.py` 对其后一切启动拒绝），续做 C1-1…4 必须由用户另行决定。
  - 选项 1（推荐）：用户确认 A 既有磁盘峰值保持 UNKNOWN 并记偏差（不补 0、不改旧账），并决定是否准许在 A 剩余量内续做 C1-1…4（候选 1、加载 11、墙钟按 §C1R-1 保守上界的剩余），续做时每次执行前后读取 Claude.app 进程联盟累计写字节，差值作为该执行新增磁盘的保守上界（含同应用其他会话与 vlm 路写入，只会偏大），叠加声明根采样；需另起后继账本承接已用量。理由：已见落盘副作用为 MB 级，剩余修复是四项窄修；联盟计数是对本客户端拉起进程全部写入的可核上界，可补上 C1-4 指出的瞬时与根覆盖缺口。由接受角色把该选项写成可签题面后再呈签。
  - 选项 2：A 到此结束，FASTFIX 停在 C1 首次退回未修；B/C 不可达。
  - 为何只能用户定：S-UNKNOWN 处置与「计量缺失后能否继续」属用户首签的 STOP/UNKNOWN 处置范围，实现/接受/supervisor 都不能补 0 或代拍豁免。
- 未改：代码、配置、测试、工具、提案、授权账本；旧债与 AC-8 `NOT_RUN` 保持。

## 续做计量预检（续修C1，2026-10-11）

- 轮次 `续修C1`；Dispatch-Id `P1-ENG-FASTFIX-001-续修C1-20261011T060317Z-d73d`；实现角色（Opus 子代理，Mac mini，主树 `~/TetheredDroneTracking`）。依据：同名提案「续做信封落实」§3–5。
- 开工 06:04:34Z：主树干净，HEAD = origin/main = `git rev-parse` 解析的派发登记提交；`git fetch` 后 origin/main 未动（无需快进，新增 git 字节 0）。派发提示 sha256 现核与派发一致。
- t0 沿用 supervisor 快照原值（`outputs/eng-fastfix/continuation/t0.json`，与 scratchpad 原件 sha256 `ec34347e…916803` 一致），不换 t0。

### 读取器与字段（只读，零模型，不提权、不安装）

| 项 | 读数 |
|---|---|
| 读取器 | `tools/eng_fastfix/window_meter.py`（本轮新增，`/usr/bin/python3` 3.9 运行，ctypes 调 libSystem `proc_pidinfo(PROC_PIDCOALITIONINFO=20)`、`coalition_info_resource_usage(cid, buf, 128)`、`proc_pid_rusage(pid, RUSAGE_INFO_V4)`、`os.statvfs`）；与 t0 读取器同一结构前缀（16×uint64，经典 `struct coalition_resource_usage` 顺序），返回值 0、`proc_pidinfo` 返回 40 = 结构长度 |
| Claude.app | pid 64627，lstart `Fri Oct  9 23:56:00 2026`，资源联盟 75839（本 Bash 进程与其子进程同属 75839，已读证） |
| 字段/单位 | 字节；`C(t)=Σ_f [f(t)−f(t0)]`，f ∈ {`byteswritten`, `logical_immediate_writes`, `logical_deferred_writes`, `logical_metadata_writes`}，四项保守相加（重叠不扣减）；不扣 `logical_invalidated_writes` |
| 覆盖实证（本轮，计入 U） | 子进程 `dd` 写 16 MiB 后退出（无 fsync）：`byteswritten` +16,777,216、`logical_deferred_writes` +16,793,600、`tasks_exited` +10 → 已退出成员与延迟写均入联盟累计；Python `mmap` 写 8 MiB + `msync`：`byteswritten` +8,392,704、延迟写 +8,404,992 → 映射写入亦计入。四项相加对同一字节至少计 2 次（偏大） |
| 外部写者 E(t) | (1) 具名 ChatGPT.app `codex exec-server --remote`（pid 23472，lstart Oct 7 15:54:13，联盟 54194）：进程终身 `ri_diskio_byteswritten + ri_logical_writes` = 24,576 B，作为 t0 前后完整上界按绝对值计入；无子进程、`lsof` 无仓库/vlm-diag 路径；(2) 另见 `~/.codex` app-server 守护进程 pid 12118（Sep 25）/82757（Oct 9，联盟 1231）：同样以进程终身写量绝对值计入（2,400,256 B + 668,618,656 B，偏大）；(3) 外部联盟 54194、1231 自首读（06:07:57Z）起四字段增量加入 E；首读前（t0→06:07:57Z，约 5 min）两外部联盟的其余进程**归属判定为非本项写者**：本项执行者全部在 Claude.app 联盟内（fast supervisor 与本角色均为 Claude 会话），vlm 路窗口内不派任务、fast supervisor pgrep 无 `codex exec`/传输/转换残留，06:09Z 复核 pgrep 同样为空，vlm 工作目录 t0 后新文件 0 |
| 系统服务 | swap 文件在 `/System/Volumes/VM`（同一 APFS 容器），3 个 1 GiB swapfile 出生于 Sep 26/Oct 6（早于 t0），t0 后无新建；Spotlight 索引/日志/swap 等系统服务写入不属本项执行者，但其落盘占用自 06:07:57Z 起全部含在下行 R(t) 容器量内 |
| R(t) | 声明根并集取数据卷所在 APFS 容器占用 `(f_blocks − f_bavail)·f_frsize`（`statvfs('/System/Volumes/Data')`），自首读基线的已见最大新增量（只增不减）；下表全部声明根与 VM 卷同属该容器（`stat -f %d` 16777229 / VM 16777232 同容器），容器量即对全部根精确去重；APFS 可清除空间回收可能掩盖同期增长，故 R 只作补充核对，瞬时覆盖由 C/E 累计量负责 |
| 判限 | `U(t)=C(t)+E(t)+R(t)`；节拍 0.4 s 持续采样，逐行落盘 `outputs/eng-fastfix/continuation/window-meter.jsonl`（含 m/unix/原值/C/E/R/U/旗标；8 MB 上限，截断即 UNKNOWN）；U ≥ 2,700,000,000 → 旗标 `STOP_DISK`，≥ 3,000,000,000 → `STOP_BUDGET`；读取失败、联盟号/进程身份变更、计数回退 → 旗标 `UNKNOWN`（不换 t0、不重置）。每步启动前读旗标与当前 U，长步骤（全套）启动前核 U + 保守需求 + 收尾预留 |
| 首读 | 06:07:57Z：C = 28,836,059；E = 671,043,488；R = 0；U = 699,879,547 B |

### 声明根（存在读数，同一容器；不授权写入或全盘遍历）

存在：主树工作树与 `.git`、`outputs/eng-fastfix/`、`runtime/`、会话 scratchpad、`~/.claude/{projects,file-history,backups,plugins}`、`~/Library/Application Support/Claude`、`~/Library/Logs/Claude`、`~/Library/Caches`、`/private/tmp`、`$TMPDIR`（`/var/folders/6x/…/T`）与 `…/C`、数据根 `.venv-yoloe`、vlm 工作目录（静止，t0 后新文件 0）、`/System/Volumes/VM`。不存在：无。

### 结论

全项可核（联盟累计含退出成员与延迟/映射写的实证、外部写者归属与完整上界、根并集与基线、节拍与旗标）→ 准许在原闭集续修 C1-1…4。计量在整窗持续运行直至终读；未覆盖的残余假设：t0→06:07:57Z 区间外部联盟其余进程按归属排除（非上界），由 Acceptance 核对该归属读法。

## 续修C1：C1-1…4 修复与 C2 自证（候选 3）

- 候选 3 = 本节所在提交（主题以 `P1-ENG-FASTFIX-001 续修C1` 开头）。**完整候选 diff**：同 §2 的候选 1 起点至本提交
  （`git diff $(git log --format=%H --grep='A实现 候选1代码' -1)^ <本提交>`）；**本轮修复增量**：`git diff <本提交>^ <本提交>`
  （运行时只解析，不手抄 SHA）。改动文件 ⊆ §2.1 闭集：`controller/{track_loop,gated_publisher,language_loop}.py`、
  `tools/eng_fastfix/{meter,ledger,window_meter}.py`（`window_meter.py` 新增，属「新 `tools/eng_fastfix/`」）、测试
  `tests/test_{capture_session,fastfix_meter,fastfix_ledger,fastfix_window_meter}.py`、证据 `docs/evidence/P1-ENG-FASTFIX-001-*`。
  `controller/det_assoc_tracker.py`、`config/*`、`controller/{target_manager,language_bridge,resident_core}.py` 本轮 diff 为空。

### 逐条修复与具名证据（修前红 = 派发基线 HEAD（候选 2 源码）导出到 scratchpad + 新测试；修后绿 = 本候选）

| 退回 | 修复 | 具名测试（修前 → 修后） |
|---|---|---|
| C1-1（AC-9） | `track_loop.py::_ensure_assoc_timing/_wrap_assoc_update`：给库关联器 `update` 套实例级计时包装（载体首帧懒建时包其工厂 `_make_resident_tracker`），`m_assoc` = 关联器实际返回时刻；step 返回后的历史组装归 tm 段。`_detect_mark/_step_marks` 只认本帧 step 区间内标记（不串帧）。step 异常保留已到 `m_det/m_assoc`；`_capture_frame` 管理器/发布阶段异常恰一行计时（`tm_failed:*`/`publish_failed:*`，已到段照记） | `tests/test_capture_session.py::FrameTimingTests::test_associate_segment_ends_at_associator_update_return_not_step_return`（红：associate_s 0.28125≠0.03125 → 绿）、`::test_association_exception_keeps_detect_mark_and_one_row`（红：detect_s None → 绿）、`::test_manager_exception_emits_one_row_with_reached_segments`（红：0 行 → 绿）、`::test_publish_exception_emits_one_row_with_tm_segment`（红：0 行 → 绿）、`::test_failure_before_detect_does_not_reuse_previous_frame_detect_mark`（守护用例，修前修后均绿） |
| C1-2（AC-3） | `gated_publisher.py::settle_frame`：结算优先级改为 FATAL > WRITE_FAILED > DROPPED > PUBLISHED > NO_ATTEMPT；混合降级/写失败帧不计不清不升级，结算另记 `dropped`；写失败照现行上抛 fail-closed | `::EscalateTests::test_dropped_frame_with_failed_hold_write_neither_counts_nor_escalates`（生产路径：两帧处理超时降级后第三帧降级且 HOLD 底层写失败；红：结算 DROPPED、streak→3 升级 → 绿：WRITE_FAILED、streak 2、无 `publish_escalated`） |
| C1-3（AC-5，释义 1） | `language_loop.py::_action_click`：删 finally 中 `release_binding(cancel_task=True)`；点击只作废提示/缓冲，任务终态由现行点击事务决定（拒收零状态变化）；仅会话投影原因从 `reacquiring` 回到 seg_end | `::ReacquireSessionTests::test_rejected_click_during_window_keeps_task_state`（替换原 `test_rejected_click_during_window_cancels_task`；红：runtime CANCELED/version 变 → 绿：TaskSpec/runtime/version/绑定/intent_revision/episode_seq 点击前后及后续 3 帧逐字段相同）；成功点击路径 `::test_click_during_window_cancels_hint_then_runs_click`、stop/release `::test_stop_and_release_take_priority_over_auto` 照旧绿 |
| C1-4（AC-15/19） | `meter.py`：`walk_sizes` 对 PermissionError/条目 OSError/目录读失败抛 `MeterUnknown`（仅竞争消失条目跳过、缺席根记 0）；采样线程任何异常、无停令退出（停令线程检测失联）、输出写失败 → `stop_condition` S-UNKNOWN 并停令。操作单 `P1-ENG-FASTFIX-001-play-ops.md` §0/§2/§4/§6/§8：阶段计时从第一条命令起、收尾预留 600 s、计量先于一切阶段写入、整窗 U(t)=C+E+R（多执行者联盟 `window_meter.py snapshot` + 容器量）+ 声明根小计（含 `.git`、TMPDIR、客户端日志/项目根）、终读之后才停计量；保全清单逐文件路径/字节/sha + 数量/总字节汇总；Play 实际起止登记、第 270 s 发停令、`T_sess ≤ 270` | `tests/test_fastfix_meter.py::test_unreadable_directory_is_unknown_not_zero`（红：无 `MeterUnknown`）、`::test_unreadable_entry_oserror_is_unknown`/`::test_unexpected_sampler_exception_stops_with_unknown`/`::test_sampler_thread_lost_is_detected_by_stop_checker`（红：修前 20 s 超时挂起 = 采样线程死亡后停令线程空等）、`::test_output_write_failure_is_unknown`（红：PermissionError 上抛 → 绿：S-UNKNOWN） |
| 续做账本（§5） | `ledger.py::create_continuation/check_disk_window`；`window_meter.py`（多联盟 `snapshot`） | `tests/test_fastfix_ledger.py::ContinuationTests`（4 例：承接计数/区间/来源字节不变、重复建账拒、尝试不返还、90% 停止线+收尾预留、UNKNOWN 拒启、来源损坏拒建）、`tests/test_fastfix_window_meter.py`（4 例：t0 固定累计、四字段相加不扣 invalidated、容器峰值不降、旗标、回退/联盟变更/身份变更/读失败 → UNKNOWN、多联盟去重求和）；修前红 = 模块/函数不存在 |

修前红/修后绿命令：`git archive HEAD controller tools tests config docs/evidence` 导出修前源码到会话 scratchpad，覆盖新测试文件后逐个
`<数据根>/.venv-yoloe/bin/python -m unittest discover -s tests -p <file> -k <name>`（单例 20 s 超时）；修后同命令在主树。

### 测试（开发期 focused；本候选全套未跑——工程 §6 具名窄修替代）

- 修后 focused 23 个文件（`docs/evidence/P1-ENG-FASTFIX-001-tests-c3-focused.log`，不带 `-v`）：20 个 OK；3 项失败中
  `test_track_loop::test_cli_runs_pinned_csrt_to_a_versioned_summary` 与 `test_language_k_binding`（导入）是候选 1 全套日志已有的基线失败；
  `test_language_loop::StateMirrorTests::test_frozen_paths_are_untouched_in_the_working_tree` 只因提交前工作树有未提交的 `controller/track_loop.py`
  （该用例检查 `git status`），提交后复跑原始输出见 `docs/reviews/P1-ENG-FASTFIX-001.md` R1 §0（干净副本 205 OK）。新增失败 0（以候选 1 全套失败集为基线逐条比对）。
- **全套未跑**：本轮磁盘按整窗 U(t) 计，focused 23 文件（约 720 例）一次即使 U 增约 0.54 GB（四字段保守相加约为实写 2 倍），
  全套 2776 例按比例将越过 2.7 GB 停止线；依工程 §6 以 focused + 修前红/修后绿替代，**不记全套通过**。真实 YOLO 构造本轮 0
  （未跑 `test_det_assoc_carrier`；所跑文件不在 F12 真实构造闭集内）。AC-7 回放未重跑：本轮改动不触及 `tools/eng_fastfix/replay.py`、
  `target_manager.py` 及重捕门/提交路径，§4 候选 1 回放证据沿用（复核可按需判定）。

### 四项自证（workflow §4.3.1，对准候选 3）

1. **范围与接口冻结**：只修 C1-1…4，未改 AC/接口/参数/闭集名；新增工具 `window_meter.py` 与账本函数属 §2.1「新 `tools/eng_fastfix/`」；冻结 `det_assoc_tracker.py` diff 为空（计时只在实例层包装 `update`，不改其调用、参数与返回）。
2. **相称测试**：上表修前红/修后绿与 focused 全绿（基线失败除外）；全套按 §6 替代，见上节。
3. **Unity**：A 阶段 Unity/Play = 0；B/C 未签、未运行，AC-16…18/20 `NOT_RUN`；AC-8 `NOT_RUN`。
4. **状态板/候选/风险**：状态板交接行与 Log 同批更新；复核范围 = §5 + 本节修复增量；未验证风险见下。

### 逐 AC 现状（候选 3；C1 核对表其余「满足」项未改动，证据沿 §4）

AC-3、AC-5、AC-9、AC-15、AC-19 → 本节具名修复；AC-1/2/4/6/10/11/12/13 证据沿 §4，本轮相关测试文件复跑全绿；AC-7 沿用候选 1 回放；AC-14 本候选为 §6 窄修替代（非全套）；AC-8、AC-16…18、AC-20 `NOT_RUN`。

### 未验证项与风险

- 关联边界包装依赖库关联器对象允许实例属性赋值；替身或不允许赋值时 `m_assoc` 缺并带 `mark_unavailable` 原因（不伪造）。真实 BoT-SORT 实例上的包装未在本轮实测（无真实构造）。
- `tm_s` 现包含 step 尾部历史组装耗时（合同段定义 m_assoc→m_tm），不再计入关联段。
- 操作单整窗计量在 Air 上未运行；Claude.app 等执行者联盟背景写入可能使 1 GB 的 B/C 信封偏紧（操作单已写停报口径），B/C 首签前由 Acceptance 核。
- 续做窗口计量的残余读法：t0→06:07:57Z 外部联盟其余进程按归属排除（见「续做计量预检」），交 Acceptance 核。

## 续修C1 资源账与窗口（FASTFIX-MINI-MUTEX；交 fast supervisor 登记 released）

| 项 | 读数 |
|---|---|
| 窗口 start / t0 | 2026-10-11T06:02:54Z（unix 1791698574.102261，supervisor 快照，未换） |
| 整窗计量 | `tools/eng_fastfix/window_meter.py`，0.4 s 节拍，自 06:07:57Z 持续运行至终读（`outputs/eng-fastfix/continuation/window-meter.jsonl`，不入仓；运行中进程为本轮首版单联盟形态，后加多联盟/`snapshot` 不改单联盟计算式）；全程旗标无 STOP_DISK/STOP_BUDGET/UNKNOWN |
| 提交1前 U(t) | 1,932,992,026 B（unix 1791699810；C 1,168,743,198 + E 705,564,436 + R 46,813,184 量级，见账本条目原文）；< 2,700,000,000 停止线 |
| 后继账本 | `docs/evidence/P1-ENG-FASTFIX-001-ledger-A-continuation.json`（来源 `ledger-A.json` 字节不变、校验和与 sha 记于 `source`；承接候选 2→本轮 +1 = 3/3、加载 3/14（本轮 0）、墙钟原区间全部承接）；`disk_peak_bytes` 只指 t0 起 U(t)，旧 A 同名维 UNKNOWN 保留在 `source.used` |
| 墙钟 | 续做区间 [t0, 提交1前 + 420 s 收尾估计上界]，A 累计并集 5,791.114 s ≤ 7,200 s（续做 ≤ 3,072.780 s 内）；估计标签保留，实际收尾时刻见下 |
| 加载/候选 | 真实 YOLO 构造 0（本轮）；候选 3（最后一个） |
| 停止原因 | 正常收尾（无 STOP）；全套因磁盘停止线未跑（工程 §6 替代） |
| 终读 | 提交1推送完成（2026-10-11T06:24:08Z，origin/main = 提交1，无需变基）后、可归属子进程静止（pgrep 无 unittest/回归脚本，仅计量进程）时读 U(t) = 1950843992 B（unix 1791699866.730，C 1195065360 + E 708965448 + R 46813184），无旗标；本补录提交2与推送、计量停令在其后执行，其字节/时长计入收尾预留（账本墙钟区间止于提交1前 + 420 s，即 06:30:38Z 前）；提交2推送后的最终终读值由接力报告 `window_end` 给出，供 fast supervisor 登记 released |

## R1-1窄修候选4自证

合同：同名提案「返工资源落实（2026-10-12，Acceptance）」§1–3（计量引用「R1简化计量落实」§2–4）；复核 `docs/reviews/P1-ENG-FASTFIX-001.md` R1 §3 R1-1（必修）、N-1/N-2/C3-1（可选）。授权：`docs/authorizations.md`「2026-10-12 … 用户签 R1-1 窄修返工资源」。派发 `P1-ENG-FASTFIX-001-R1-1窄修-20261012T010330Z-1e19`。

### 候选标识与 diff（运行时解析，不手抄 SHA）

- 候选 4 = 主题以 `P1-ENG-FASTFIX-001 R1-1窄修 候选4代码` 开头的提交（代码+测试+C3-1 补丁，`git log --format=%H --grep='R1-1窄修 候选4代码' -1`）加本节所在证据提交（只改证据/状态板）；本批两笔提交共同绑定候选 4。
- 相对 R1 候选（复核 R1 §0 `round_candidate`，即主题 `续修C1：补录窗口终读…` 的提交）的完整候选 diff：`git diff <round_candidate> <本节提交>`；代码/测试只 4 个文件：`controller/track_loop.py`（+13/−3）、`tests/test_capture_session.py`（R1-1 两例 + 共用辅助）、`tests/test_target_manager.py`（N-1 两例）、`tests/test_capture_isolation.py`（N-2 一行）；`docs/evidence/` 本文件（C3-1 逐字补丁 + 本节）与三份日志。`round_candidate` 与派发基线 HEAD 之间 `controller tests tools config` diff 为空（运行时 `git diff --stat` 核）。
- 冻结：`controller/det_assoc_tracker.py`、`config/*`、`controller/{gated_publisher,language_loop,target_manager,language_bridge,resident_core}.py`、`tools/` 本批 diff 为空；未改 `settle_frame` 结算语义、fail-closed 上抛、接口/参数/AC。

### 修复（R1-1，BC-9 读作 AC-9）

`controller/track_loop.py::_capture_frame`：`settle` 提到 `try` 前初始化；异常分支调 `_capture_partial_timing(..., settle=settle 或 _unsettled_gate_evals(frame_id))`。新 `_unsettled_gate_evals` 只读发布器 `_frame_ctx`（帧号须同本帧），返回 `{"gate_evals": [...本帧已读门读数], "outcome": None}`——不调 `settle_frame`、不动 streak/结算，`settle_outcome` 仍为 None（未结算）；结算之后的异常沿用已得 `settle`。`_capture_partial_timing` 新增可选 `settle` 关键字，其他三处调用（frame_missing/load_failed/step_failed）不传、行为不变。

### 四项自证（workflow §4.3.1）

1. **范围/接口冻结**：只修 R1-1 + 可选 N-1/N-2/C3-1；改动文件见上，属提案 §2.1 闭集（`controller/track_loop.py`、`tests/`、证据）；不触及真实模型加载器、数据划分/对外指标路径，满足工程 §6 窄修替代前提。
2. **相称测试（零真实加载）**：
   - R1-1 生产路径具名回归（会话 harness `tail_harness(tail_s=0.0)`，真实分级门放行后令 inner 写出器抛 `OSError`）：`tests/test_capture_session.py::FrameTimingTests::test_write_failure_after_real_gate_keeps_gate_eval`（观测写出器；断言恰一行、`gate_eval_s == [本帧门 detail.load_elapsed_s]`、`settle_outcome` None、`missing_reason.frame == "publish_failed:OSError"`、已到达段 detect/associate/tm 照记、该帧无 observation 收据）与 `::test_gimbal_write_failure_after_real_gate_keeps_gate_evals`（云台 `look_at` 写出器；两次门读数、首读数与该帧 observation `WRITTEN` 收据同值）。注：尾段 0.25 s 的旧 harness 使 load_elapsed 越过 t_pub 而 DROP，到不了底层写——这也是旧 `test_publish_exception_emits_one_row_with_tm_segment` 无法证明此主张的原因。
   - **修前红**（修复前、新测试已加、代码 = R1 候选）：`docs/evidence/P1-ENG-FASTFIX-001-r1-1-red.log`——2 例均 `AssertionError: Lists differ: [] != [0.21875]` / `[] != [0.21875, 0.21875]`（只败在 `gate_eval_s`）。**修后绿**：`docs/evidence/P1-ENG-FASTFIX-001-r1-1-green.log`（Ran 2, OK）。命令：`TMPDIR=<窗口目录>/tmp ~/TetheredDroneTracking-full/.venv-yoloe/bin/python -m unittest discover -s tests -p test_capture_session.py -k write_failure_after_real_gate`（`tests` 包遮蔽故用 discover）。
   - N-1（AC-5 覆盖，非闭合条件，修后新增即绿）：`tests/test_target_manager.py::ReacquireHintTests::test_full_8x8_covariance_asymmetric_or_not_psd_is_hint_invalid`、`::test_hint_state_is_a_deep_copy_of_library_track`（经生产取数 `full_kf_state_from_associator` 后原地改库轨迹 mean/covariance，状态与提示不变）。N-2（AC-12 覆盖）：`tools/eng_fastfix/window_meter.py` 加入 `FASTFIX_RUNTIME_FILES`，`FastfixTruthIsolationTests` 4 例 OK。
   - **focused**（提交候选 4 代码后在干净主树跑，与 R1 §0 同 23 文件，不带 `-v`）：`docs/evidence/P1-ENG-FASTFIX-001-tests-c4-focused.log`——21 文件 OK；失败 2：`test_track_loop::test_cli_runs_pinned_csrt_to_a_versioned_summary`、`test_language_k_binding`（导入错误），均为候选 1 全套日志 `docs/evidence/P1-ENG-FASTFIX-001-tests.log` 已有基线失败（逐名相同）；**新增失败 0**。`test_capture_session` 64 OK（原 62 + 2）、`test_target_manager` 78 OK（原 76 + 2）、`test_language_loop` 205 OK（含冻结路径工作树用例，提交后跑）、`test_capture_isolation` 13 OK、`test_fastfix_replay` 3 OK（主树准入帧，替身检测）。全套/新回放未跑，**不记全套通过**。
3. **已知失败与 Unity**：R1-1 已修绿；Unity/Play/现场 0，AC-8、AC-16…18、AC-20 `NOT_RUN`，无 `UNITY_NA` 申请。
4. **证据/状态/风险**：本节、三份日志与状态板交接行同批提交；未验证风险见下。

### 逐 AC 指针

| AC | 指针 |
|---|---|
| AC-9 | test:`tests/test_capture_session.py::FrameTimingTests::test_write_failure_after_real_gate_keeps_gate_eval`；test:`::test_gimbal_write_failure_after_real_gate_keeps_gate_evals`；artifact:`docs/evidence/P1-ENG-FASTFIX-001-r1-1-red.log`、`-r1-1-green.log` |
| AC-5 | test:`tests/test_target_manager.py::ReacquireHintTests::test_full_8x8_covariance_asymmetric_or_not_psd_is_hint_invalid`、`::test_hint_state_is_a_deep_copy_of_library_track`（N-1 覆盖，代码未改） |
| AC-12 | test:`tests/test_capture_isolation.py::FastfixTruthIsolationTests::test_runtime_entries_never_import_score_or_name_truth`（N-2 集合扩至 `window_meter.py`）；冻结路径零 diff（`test_language_loop::StateMirrorTests::test_frozen_paths_are_untouched_in_the_working_tree` 提交后 OK） |
| AC-14 | cmd:23 文件 focused（上）→ artifact:`docs/evidence/P1-ENG-FASTFIX-001-tests-c4-focused.log`；工程 §6 窄修替代，不记全套通过 |
| 其余 | 证据沿候选 3 节/§4，本批未改相应代码 |

### 未验证项与风险

- `_unsettled_gate_evals` 读 `GatedPublisher` 私有属性 `_frame_ctx`（为不改发布器接口而取只读；不存在/帧号不符即回落旧行为 `gate_eval_s=[]`）。
- 结算后异常（如 `on_frame_settled` 抛错）现带真实 `settle_outcome`；修前为 None。无具名测试，属同一字段语义的更准确记录。
- 底层写失败后会话的 fail-closed 去向未改动、本批未新增断言（沿用 AC-2 既有测试）。
- C2-P2/P3、旧/续做磁盘 UNKNOWN、OPEN 债保持；真实 BoT-SORT 包装可赋值性仍未实测。

### R1-1窄修资源记录（最小记录，替代 JSON 账本）

- 来源校验（只读）：A 账承接候选 3/3 → 本窗新增候选 1，累计 **4/4**（用户一次性 +1，尝试即记）；真实模型加载本窗 **0**，累计仍 3/14（`ledger-A.json`、`ledger-A-continuation.json` 未改）；未建新 JSON 账本。
- 窗口：supervisor 原件 `~/fastfix-impl-20261012T010321Z/supervisor-readings.txt`——ready 01:03:15Z；t0 = 2026-10-12T01:03:21.426Z（unix 1791767001.426）；F0 = 116,889,340 KiB × 1024 = 119,694,684,160 B；收尾线 01:53:21Z、硬界 02:03:21Z。本角色开工 01:04:20Z。
- 本角色读数（`df -k /System/Volumes/Data` Available×1024；`du -sk <窗口目录>`×1024；原件 `~/fastfix-impl-20261012T010321Z/impl-readings.txt`）：

| UTC | F（B） | D = max(0, F0−F)（B） | du 窗口目录（B） |
|---|---|---|---|
| 01:04:33Z（目录 + tmp/ 建好） | 119,691,223,040 | 3,461,120 | 4,096 |
| 01:08:09Z（focused 前） | 119,691,743,232 | 2,940,928 | 24,576 |
| 01:08:47Z（focused 后） | 119,702,089,728 | 0 | 40,960 |
| 01:10:20Z（提交前终读） | 120,721,948,672 | 0 | 40,960 |

- 已见 D 最大 3,461,120 B（01:04:33Z）；S（窗口目录建好/收尾前两次读数较大者 = 40,960 B，唯一本窗新建目录；主树写入由卷 D 观察）与 D 全程远低于 2,700,000,000 B 停止线；无 STOP。验证止于 01:08:47Z（< 收尾线）。卷 D 含同机其他进程写入，不作完整峰值主张。最终 F1/t1/D 与 released 由 fast supervisor 调度 note 承接。
- 原件落点（收工保留）：`~/fastfix-impl-20261012T010321Z/`（`r1-1-red-before-fix.log`、`r1-1-green-after-fix.log`、`c4-focused.log`、`c4-focused-exits.txt`、`n1-hint-tests.log`、`n2-isolation-tests.log`、`impl-readings.txt`、`tmp/`）。
