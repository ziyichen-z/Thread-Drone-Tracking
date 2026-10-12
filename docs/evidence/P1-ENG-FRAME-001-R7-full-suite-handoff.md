# P1-ENG-FRAME-001 — R7 后续 K2 全套/自证交接（Implementation，2026-10-01）

Status: IMPLEMENTED_AWAITING_C3。本次仅补测试证据与停点自证，未改三路径窄修、合同或任何 skip。一次完整全套已消费，不重跑；正式补测余额与 Unity/Play/run 均未动。交接受 C3@K2 只读核对，独立 R3/Play 尚未放行。

## 一次全套结果与逐名归因（AC-24）

依据账本同日「用户确认一次完整测试的具名模型额度并调用原子代理」，原样执行 `YOLO_OFFLINE=true YOLO_AUTOINSTALL=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv-yoloe/bin/python -m unittest discover -s tests` 一次（无-v、无过滤）；stdout/stderr完整写 `docs/evidence/P1-ENG-FRAME-001-R7-full-suite.log`。结果 Ran 2064 tests in 137.386s，FAILED (failures=4, errors=21, skipped=19)，exit 1。完整测试执行成立，绝非全绿。

旧 `docs/evidence/P1-ENG-FRAME-001-tests.log` 为2061/4败9错19跳；逐名比较记录在 `R7-full-suite-result.json`，旧13条全部保留、解决0、新增12条ERROR。R7新增3个顶层测试没有FAIL/ERROR，先前focused5/5红绿证据沿读R7-implementation，不在本轮重跑。

旧13条原因：dist_data_round4三条归档truth/frame闭合失败；round8两条缺scenario快照；rate3一条缺归档manifest；SFT四模块与language_k_binding一模块因site-packages同名tests遮蔽而导入失败；CSRT两个入口因本机cv2无TrackerCSRT_create失败。具体全限定名称与完整旧/新栈保留两份原日志和机器比较，未补数据/装包或修无关债。

新增12条逐栈审计如下，每条均在HTTPServer.server_bind→TCPServer.server_bind→socket.bind(server_address)抛PermissionError EPERM；不是仅按异常类型归类。ACQ三条在setUp的web.build_server(App,0)，源码HOST=127.0.0.1；language九条在_serve(ScriptedAdapter等假adapter)的build_server(runtime,port=0)，生产默认host=127.0.0.1。受限环境拒绝临时loopback监听，均未到请求、行为断言或远程后端。相关测试/生产文件相对旧通过候选零diff。尚未验证它们在允许loopback环境中的本轮行为；不称新增失败0，不据静态归因冒称12条通过。

| 新增ERROR（完整名称另见机器记录） | 原日志行 | 直接原因 |
|---|---:|---|
| test_listens_on_loopback_only | 116 | loopback socket.bind EPERM |
| test_post_requires_nonce_and_same_origin | 134 | loopback socket.bind EPERM |
| test_preview_endpoint_serves_only_the_bound_bytes | 152 | loopback socket.bind EPERM |
| test_a_confirmed_idle_clears_the_unconfirmed_clock | 249 | loopback socket.bind EPERM |
| test_a_known_server_side_reason_is_preserved | 270 | loopback socket.bind EPERM |
| test_a_server_side_exception_message_reaches_the_client | 291 | loopback socket.bind EPERM |
| test_backend_failure_is_reported_as_backend_error | 312 | loopback socket.bind EPERM |
| test_client_deadline_abandons_without_re_entering | 333 | loopback socket.bind EPERM |
| test_multipart_carries_surface_and_g4 | 354 | loopback socket.bind EPERM |
| test_round_trip_preserves_finish_reason_and_identity | 375 | loopback socket.bind EPERM |
| test_server_busy_is_not_queued_and_blocks_re_entry | 396 | loopback socket.bind EPERM |
| test_server_hard_limit_marks_stuck_and_needs_a_restart | 417 | loopback socket.bind EPERM |

## 实际资源及执行环境

仅既有仓库.venv-yoloe（Python3.12.13），默认受限workspace sandbox，无测试提权/外网例外；四个离线/禁自动安装变量在shell进程设置并由子进程继承。没有变更ENG_DET_DATA_ROOT、隐藏模型、安装或补包。纯本地CPU，未启动Unity、正式tracker或采集；测试临时夹具中的run名称不视为正式采集ID。正式补测Play1/模型1/run1余额不动。

一次全套已执行，模型尝试按具名静态上界保守记账Nano≤4（权重读取≤8）、YOLOE≤2、DINOv2≤2、CSRT两个adapter入口；失败不回补。没有插入instrumentation/更改测试，Nano/YOLOE/DINO构造尝试和成功数不能从unittest聚合日志测量，明确未知；两条真实preflight子进程在检查skip前执行，但其返回payload被用例捕获，不能根据聚合19skip推断DINO是否完成。CSRT两个入口均因缺构造函数失败，真实实例成功0。不得把上界冒称实测成功数，后续按全次上限保留消费账目。

四变量抑制已审计的库下载/安装/联网探测路径，外网限制未解除，loopback绑定拒绝是实际观测。无流量监测，不能宣称实测DNS/HTTP零；没有外部服务/下载安装命令或权限例外，未见新增真实loader。前一静态审计版本导入DNS局限仍保留，不能追认。CPU峰值内存、模型具体加载成功与网络流量不在此次可测证据内。

## 完整候选与范围（AC-25/AC-26）

测试HEAD及旧passed_candidate从git/复核机读行动态解析写入R7-full-suite-result.json，不在手维护文档写死。核对使用该文件的40条基线→测试HEAD name-status，加本次3份新证据文件及状态/准备说明更新；提交后以git diff旧passed_candidate..HEAD读取完整patch。当前候选实际差异路径全列下表，不排除协调/授权文件。R7生产实现仅tools/frame_follow_replay.py::analyze_run，测试及fixture两路径；其余为各角色证据/流程/协调文件，角色归属可沿git log逐路径确认，不能把协调路径计为实现扩大合同。

- `.agents/skills/chore/SKILL.md`
- `.agents/skills/chore/agents/openai.yaml`
- `.agents/skills/fable/SKILL.md`
- `.agents/skills/fable/agents/openai.yaml`
- `.agents/skills/implement/SKILL.md`
- `.agents/skills/implement/agents/openai.yaml`
- `.agents/skills/review/SKILL.md`
- `.agents/skills/review/agents/openai.yaml`
- `.agents/skills/supervisor/SKILL.md`
- `.agents/skills/supervisor/agents/openai.yaml`
- `docs/authorizations.md`
- `docs/current-status.md`
- `docs/evidence/P1-ENG-FRAME-001-R7-acceptance-inspection.json`
- `docs/evidence/P1-ENG-FRAME-001-R7-acceptance-inspection.md`
- `docs/evidence/P1-ENG-FRAME-001-R7-environment.log`
- `docs/evidence/P1-ENG-FRAME-001-R7-full-preflight.json`
- `docs/evidence/P1-ENG-FRAME-001-R7-full-suite-handoff.md`
- `docs/evidence/P1-ENG-FRAME-001-R7-full-suite-preparation.md`
- `docs/evidence/P1-ENG-FRAME-001-R7-full-suite-result.json`
- `docs/evidence/P1-ENG-FRAME-001-R7-full-suite.log`
- `docs/evidence/P1-ENG-FRAME-001-R7-green-tests.log`
- `docs/evidence/P1-ENG-FRAME-001-R7-implementation.md`
- `docs/evidence/P1-ENG-FRAME-001-R7-recompute.json`
- `docs/evidence/P1-ENG-FRAME-001-R7-red-tests.log`
- `docs/evidence/P1-ENG-FRAME-001-play-ops.md`
- `docs/evidence/P1-ENG-FRAME-001-play-result.json`
- `docs/evidence/P1-ENG-FRAME-001-play.md`
- `docs/evidence/P1-ENG-FRAME-001-play2-paused.json`
- `docs/evidence/P1-ENG-FRAME-001-preflight.json`
- `docs/evidence/P1-ENG-FRAME-001-retry-preflight.json`
- `docs/evidence/P1-ENG-FRAME-001-supplement-ops.md`
- `docs/evidence/P1-ENG-FRAME-001-supplement-preparation.json`
- `docs/evidence/P1-ENG-FRAME-001-unpaused-play.json`
- `docs/evidence/supervisor-dispatch.jsonl`
- `docs/implementation-status.md`
- `docs/phase1-single-drone-design.md`
- `docs/proposals/P1-ENG-FRAME-001-tracking-framing-and-body-follow-survey.md`
- `docs/reviews/P1-ENG-FRAME-001.md`
- `docs/unity-test-log.md`
- `docs/workflow-changelog.md`
- `tests/fixtures/frame_follow_metrics_unity.json`
- `tests/test_frame_follow_replay.py`
- `tools/frame_follow_replay.py`


controller/Assets/config/ProjectSettings/Packages相对最近通过候选零差异；三窄修路径、FRAME配置、无缆场景和回放六个完整hash均与预检一致。Unity EditMode不重跑：相关代码/冻结配置零差异；现有Logs/P1-ENG-FRAME-001-editmode-rework.xml身份实算记录在机器证据，既有284/284只作未触及路径依据，未给新工具独立签通过。tools/tests的PLAY_GOVERNING差异非空，旧R2不能放行新工具，须C3→独立R3→接受消费。

## 四项稳定自证（workflow §4.3.1）

| 条件 | 实现者自证与限制 |
|---|---|
| 1 范围/接口冻结 | 成立。AC-21既有R7 aggregate.c_track字段路径兼容，保留top-level/summary优先、null/zero、六位输出、显式metrics端点。没有协议/指标/安全或模型语义改动，原授权三路径冻结 |
| 2 相称实现者测试/编译 | 成立于本窄修。AC-21红→绿5/5、真实旧输入两端点复算与138原件不变已交证；AC-24本轮全套一次完成，旧13与新增12逐名分列，新增全部具名loopback绑定环境拒绝、无本改归因逻辑失败。AC-24要求执行一次并分列失败，未改为全绿或删用例。12条HTTP行为仍未在本环境执行到断言，这是候选验证局限，交C3/复核判断影响 |
| 3 已知Unity失败 | 成立于代码停点，未触及Unity且既有EditMode修复终跑284/284可沿读旧K2-handoff/R2。AC-21用户跟随/起停目检及完整按钮墙钟仍缺证，明确NOT_RUN；AC-23已有读数不替代人眼。未自行签Unity PASS或DONE |
| 4 候选/状态/风险更新 | 本证据具名归因与完整文件清单、状态交接受、角色/docs自检后提交推送。原review只读未改，没有新独立通过凭据，环境/资源未知如上披露。提交候选后立即停，不自行派发review或开始补测 |

AC-1…10/27…29（§T）与AC-11…20（§P）未触及部分沿读K2-handoff对应具名自证及R2；AC-19/20配置/回放冻结hash一致；AC-22真值隔离零改动；AC-25全候选清单含流程路径，不扩大实现；AC-26本文件为R7后续增量自证，原§T/§P/§共用不覆盖历史或假称重跑。R1-3 SCOPE_GAP/OPEN不修不闭。

## 交接接受

接受按C3@K2完整读取基线→最终候选所有patch、直接关联代码与上述四项证据，核对12条环境归因及未测行为限制；不跑测试、不直接视旧R2为新通过。正式独立R3由接受按已签新鲜上下文授权办理，若自证不成立如实阻塞，不能跳过核对/复核放行Play。后续用户补测仍须人眼、全按钮墙钟、480秒和冻结端点忠实输出。实现到此停止。

收工检查：`python3 tools/check_role_writes.py --role implementation` 通过（本批5路径），`python3 tools/check_docs.py` 通过；仅本批evidence/current-status写入。候选以本批提交及推送结果定位，不虚构Dispatch-Id。
