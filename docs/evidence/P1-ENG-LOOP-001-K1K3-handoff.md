# P1-ENG-LOOP-001 — 候选 1 / 阶段 A / K1K3 交接

Owner: Implementation（Cursor）
Date: 2026-09-20
Status: STABLE_CANDIDATE_AT_K1K3 → Acceptance C1@K1K3 → 独立 Review R1@K1K3
合同：D4 ACCEPTED、AC-1…17、八行首次释义、十行实现期修订（P-A-1…8、P-B-1/2）。
本文件是实现者自证与核对入口，不是接受结论或独立复核 verdict。

## 1. 最终候选与完整范围

候选从交接提交的 HEAD 运行时解析；首次实现之前的基线、当前源码/测试/证据 SHA
见 `P1-ENG-LOOP-001-candidate-manifest.json`。不在手维护文档写派生 SHA。
接受侧须看完整候选 diff、下列直接关联代码与证据，不只看本次绑定补丁。

```bash
base=$(python3 -c 'import json; print(json.load(open("docs/evidence/P1-ENG-LOOP-001-candidate-manifest.json"))["baseline_before_first_runtime_file"])')
git rev-parse HEAD
git status --porcelain
git diff "$base" HEAD --stat
git diff "$base" HEAD
```

实现范围：`controller/language_bridge.py`、`gated_publisher.py`、`language_selector.py`、
`language_loop.py`、`language_demo.py`；`tools/language_serve.py`、`language_latency.py`、
`requirements-language.txt`；四份 `tests/test_language_*.py`；`runtime/README.md`、
`.gitignore`；本项操作单、执行脚本、原始日志与实测/复算证据。接受角色另读自身
提案中的 Pending rulings 与 Contract conformance，不能把非 C 增量查看冒充 C 轮。

冻结边界：`Assets/`、`config/`、`tools/eng_sft/`、既有 protocol/tracking_entry/track_loop
从基线到本候选无改动，机读清单中 frozen_changed_paths=[]。他人未跟踪的
`docs/resume-appendix.md` 不属于本候选，不提交也不改动。

## 2. workflow §4.3.1 四项自证

| 条件 | 实现者自证与证据 |
|---|---|
| 范围与接口冻结 | D4 及八行首次释义/十行修订全部保持；本批 K 身份守卫落实原 AC-10 修订 1，没有新增 AC/预算/桥枚举或 Unity 协议变更。合同常数保持。 |
| 相称实现者验证 | 有 Pillow 聚焦257项 OK、零skip；停点全套1504项，0 failures/9既有cv2环境errors/24skip，新失败0；原始环境失败与修前红例另存。真实两机、等价、K复算、pip check和最终HTTP身份正反例已交。详情实测报告§4…8。 |
| 已知失败处理/未验证范围 | K权重身份漏检已修并红绿验证；Mac两次合并失败、5060不等价按既定回退处理，无待修模型异常。阶段A未运行Unity，不存在本批已知Unity失败；AC-13…15仅待单独B信封，绝不以离线证据冒充。 |
| 状态、候选与风险可追溯 | 状态板交接同步本候选；提交/推送后由git解析候选与diff。独立复核尚未开轮，Review仍N/A，范围和未验证风险由本文记录，不代写复核文件。风险见§4。 |

## 3. 逐 AC 与全部修订证据

所有测试模块名以 `tests.` 开头；旧实现报告 §2.1/§2.2 保留更细的具名用例定位，
其“待测”结论由本表与最新实测报告取代。证据前缀均为
`docs/evidence/P1-ENG-LOOP-001-`。

| AC | 阶段 A 自证指针 |
|---|---|
| AC-1（含首次修订1） | test_language_bridge、test_language_loop.RequestLifecycleTests；schema/回执/双锁/去重/未知结果不重发；runtime/README.md三桥文件。 |
| AC-2（含首次修订1） | StaleRejectionTests、PublishGateTests；帧成员/sha/元数据/墙钟/帧差检查及拒绝零写入，查询快照不冒充输入重采集。 |
| AC-3（含首次修订1、P-A-2修订2） | GatedSeedingTests/PublishGateTests/CatchUpTests；MUTED_DROPPED/REJECTED不推进关联，静音初始化/批末发布/最终门；旧报告§2.2具名拒绝回归。 |
| AC-4（P-A-3修订1、P-A-8修订2） | StateMirrorTests；批内raw_lost不被批末raw_ok覆盖，未知终端事件显式unexpected_segment_end，已知原因不改写；真实Play的PROTOCOL_ABORT归类待B。 |
| AC-5（P-A-5修订1） | ConfirmationTests/PreviewRenderTests；缺预览不播种、有Pillow真实渲染、令牌/index/原时间门；257项零skip。Play源帧目检约束待B。 |
| AC-6（P-A-4修订1） | BoundedRetryTests/AmbiguousTests、WorkerTests.test_model_calls_are_counted_apart_from_attempts；前置失败占号与真实调用分列；未发起核验不计查询。 |
| AC-7 | RespecifyTests；人工开新段、段终止幂等、旧段retire、TRACKING下拒绝非法重指定。 |
| AC-8（首次修订1、P-A-6修订2） | test_language_selector.HttpAdapterTests/LocalHfAdapterTests、loop WorkerTests；真实loopback单工、提交/轮询断联、idle恢复仍守原截止、硬限fatal、原始异常保留；Windows兼容具名测试与两机实测。 |
| AC-9 | ReplayAdapterTests/FrozenReplayAssetTests/ReplayDemoTests、LatencyMeasurementTests；真实盲索引连接与冲突/无匹配；merge-equivalence.json 32行2行不等价、64条原始输出，合同回退c2-adapter。 |
| AC-10（首次修订1） | latency-{mac,5060}.json、k-receipt.json、measurement-verification.json；最终5060/A、K=30/50/2；test_language_k_binding的13项，tests-k-binding-before.log修前红、tests-k-binding.log修后绿、live-binding-5060.json真实服务正反例；源报告SHA、身份、端点、设备与冻结K_pub拒绝。 |
| AC-11 | tests.log：1504，0 failures/9既有ERROR/24skip；tests-language-final.log：257 OK/零skip。测试缺口已由具名红绿补齐，不掩盖历史失败。 |
| AC-12（首次修订1、P-A-1修订2） | operations.md、pip-check-{mac,5060}.log、environment-{mac,5060}.txt；DiagnosticSessionTests的共享runtime路径别名和九CLI守卫；T7/F隔离布局、计数账本与cleanup-5060.json。 |
| AC-13（首次修订1） | 未运行；E1事件/窗口/聚合/源帧目检属于阶段B。对应脚本规范见旧报告和play-cases.md（若后续阶段建立），本项不把夹具标成Play证据。 |
| AC-14 | 未运行；歧义剧本P2的候选呈现、确认及各结局适用检查待阶段B；歧义识别成功单列，不改为通过条件，不申请UNITY_NA。 |
| AC-15 | 未运行；每次Play的查询/迟到/时延/重试/verdict/人工处置与终态、≥3失败案例或不足声明待B；不作跟踪性能或恢复率主张。 |
| AC-16（P-A-7修订1、P-B-1修订2、P-B-2修订3） | VerifyTests与旧报告§2.2/§9.2；配对源帧、五verdict、提醒不控桥、连续计数/限频、三值verify_skipped与五值verify_pairing_unavailable分层，query_id/输出/调用零占用。 |
| AC-17（首次修订1） | StateTableTests/WorkerTests；八态九动作非法格、stale epoch、pending/ SUPERSEDED、worker_stuck只能stop、join≤5s、WRITER_BUSY；HTTP模型变化采用同一fatal链。 |

八行首次释义与十行实现期修订均在上述同编号行定位，没有未答复的新合同问题。
接受侧仍须独立核对其完整文字，不由本实现者声明代替逐项验收。

## 4. 预算、失败与未验证风险

Mac：合并2/2、加载3/6、查询35/70、base下载1/1。5060：合并1/2、启动6/6、查询
134/134（等价64+修前35+修后35）、新base下载0。失败服务启动保守扣额；两机合并
失败/等价回退和修后supersession请接受角色按原合同归因，原始失败不覆盖。
5060服务和启动器已停、端口零监听；原A信封不得再启动或查询5060。

限制：32行固定smoke不是609行评估，也不证明跟踪改善或真实Play；p95预算不保证
max在窗内，正式运行仍需拒迟到结果；MPS内存采样为下界。两轮HTTP不是受控性能
对照。K与现有模型/端点/hz/R/报告字节绑定；新环境或绑定项变化须新收据。模型输入
仍为已核验冻结base/C2；操作单的输入SHA预检不可省略。离线证据不替代正式Play。

达到本停点后停止依赖性实现；下一动作仅为接受角色C1@K1K3及随后独立R轮。
未获C/R与独立阶段B信封前，不启动Unity/Play、正式ID或新模型实验，不标DONE。
