# P1-ENG-JET-001 独立复核（Jetson Orin Nano 板端探测阶段 A：S0/S1/S2/SR + 中继，engineering-v1，停点 `K1K3K4`）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-JET-001-R1@K1K3K4-20261003T223702Z-2316`，`requested.round = R1@K1K3K4`）。
轨道：提案抬头逐字 `Workflow: engineering-v1`，接受角色在「D2 接受裁定」`ACCEPTED` 时逐字裁定生效 → 按 `docs/engineering-workflow.md` 复核；依据列仍写 `BC-n`，读作任务合同第 n 条验收项 `AC-n`（含其修订）。
零消耗：零 scenario/session/run ID、零 Unity Play、零付费 API/GPU/VLM、零下载/安装、零上板/ssh、零真实模型构造/推理、零回放、零全套/SR 重跑（全套 1/1、det-assoc 2/2、部分回放 2/2、SR 5/5 均无余额，本轮未申请）。只在一次性副本内读码、重跑 focused `tests/test_eng_jet_*.py`、以候选的纯函数对本机已取回的原始收据/结果文件**重算** S1/S2/SR 的 verdict 与读数（不构造模型、不碰板子）。

## R1@K1K3K4（2026-10-03）

### §0 候选、基线与开轮资格

- `round_candidate: b4f145655155d2c4870c9001f2a85d539f4cf53a`（= 交接「K1K3K4C1返工：报告现状/历史分列与候选重冻结」§2 规则运行时解析：`git log main --grep='^P1-ENG-JET-001 K1K3K4C1返工 收工'` 仅 1 条、触及交接文件、为 `origin/main` 祖先；与派发提示的候选 SHA 相同）。
- 全量 diff 基线：本文件此前不存在，无 `passed_candidate`；`$BASE` = `4cbd7bd9a649af1f6e165fa4bd794a29dcc18c2d`（`K1K3K4 开工` 唯一主题提交的父提交，与 `-ledger.json`「git_diff_assets_controller_config.base」相同）。`git diff --name-only $BASE..$CAND` = **33 路径**，与交接 1A 节 §3 清单逐一相同：`.gitignore`（仅 `/outputs/eng-jet/`）、`tools/eng_jet/` 10 件、`tests/test_eng_jet_{bench,guards,relay,track_responder}.py`、`tests/test_det_assoc_carrier.py`（仅两处构造 + 导入替换，`create_tracker` 引用已全部移除，其余断言/skip 门不变）、§3.4 八个 JSON + report + handoff + 两份测试日志、提案/账本/状态板/派发登记/发令表（COORD-015 Kimi 回退补记，非本项）。`git diff --stat $BASE..$CAND -- Assets controller config` **为空**；`controller/`、`Assets/`、`config/`、`runtime/`、工作流基础设施、`tools/check_*`、复核/设计文件均不在 diff 内。1A 候选 → 本候选增量 6 路径（账本、状态板、派发登记、提案、报告 18 行、交接 52 行），纯文档。
- 开轮资格：PLAY_GOVERNING（`tools/`、`tests/`）diff 非空 → 开轮。首个复核轮，无上一复核轮候选、无修前红/修后绿义务。
- 停点自证（交接「K1K3K4C1返工」§5 与 1A 节 §6）四项：①范围/接口冻结成立（上述 cmd 空、1A..CAND 零代码）；②相称测试「在用户具名例外下成立（不记通过）」——全套 1/1 已跑（2136 / F27 / E10 / S56，`-full-suite.log` 尾部与交接一致），Carrier 具名例外与 scene006 环境分列按账本 2026-10-03「用户裁定线 A 全套结果…」授权范围携带入 R1，本角色接受其进入复核、不视作自证不成立；③零 Unity，不适用；④候选解析规则、范围、AC 指针、风险齐备。→ 不判 `REVIEW_BLOCKED`。
- 复核副本 `.claude/worktrees/review-P1-ENG-JET-001`（detach 于候选）；测试树哈希 `HEAD:tests = 0bc3d70a647803519ad3605eae6ecd71c18dc038`，`HEAD:tools/eng_jet = 34e8ffd4e87bc04aeaf01b23b522ee84ee560bec`。解释器：数据根 `~/TetheredDroneTracking-full/.venv-yoloe/bin/python`（3.12.14，只读使用、不装包）。
- **focused 重跑**（副本内 `YOLO_OFFLINE=true YOLO_AUTOINSTALL=false … -m unittest discover -s tests -p 'test_eng_jet_*.py'`，输出写会话暂存目录，只回显摘要）：**72 tests OK（skipped=1）**；跳过的是 `test_eng_jet_bench.InjectionOnly.test_plugin_identity_unchanged_and_timers`（副本无 gitignored 冻结权重 `outputs/eng-det/runs/run-1/weights/last.pt`，其 `skipTest("冻结权重不在本机")` 分支），其余 71 例实跑（含本机双进程回环 `LoopbackTwoProcess` 两例与进程内断链回环）。实现者 `-focused-tests.log` 为 72/72 无 skip（主树有权重），一致。副本 `git status --porcelain` 跑后为空。
- **证据重算（零模型，候选纯函数 × 本机原始文件）**：
  - SR：对 `outputs/eng-jet/P1-ENG-JET-001/sr-f/{f1-echo,f2-echo,f3-track,f4-track-drops}` 原始收据重跑 `relay.analyze`：f2/f3 `bundles_sent 1500 / complete 1500 / completeness 1.0 / order 0 / pointing_incomplete 0 / sha_mismatch 0`、到达 p95 16.245 / 16.690 ms、偏差中位 8.909 / 7.851 ms、漂移 −2.454 / −2.437 ppm、回声回程 p95 5.644 ms、真实回程 p95 6.117 ms（n = 29）、`frame_age_ms` p95 124.94；f4 两次断链实测 10.004 / 60.001 s、缺口 49 / 299、latest 帧差 50 / 300、断链期间板侧 publish 0、`no_backfill` 真、回稳 0.134 / 1.940 s（阈值 16.203 / 15.340 ms）、TrackLoop 一次 `GAP`（latest 332，previous 282）；f1 `1501 送 / 1 完整 / 顺序违反 1500`。**全部与 `-relay.json` 逐值相同**。原始收据直接核：f2/f3 桌面机收据链路事件只有启动 `connect` 与收工 `disconnect` 各 1，`send_bundle` 各 1,500；f4 事件序列 `connect, drop_start, disconnect, connect, reconnected_after_drop, drop_start, disconnect, connect, reconnected_after_drop, disconnect`，`send_bundle` 1,152。回稳读法 `relay.RECOVERY_*` 由 `git log -S` 定位在补跑F 开工提交 `cdd20d5`（2026-10-03T16:28:31Z），早于 f4 数据窗（16:54Z 起），预注册成立。
  - S1：`s1s2-system-d/results-d/s1-det-assoc-v1-fp16-{640,480x640}-frames.json`（sha 与 `-fastlayer.json` `raw_frames_sha256` 相同）的逐帧检测 × 本机 `frozen-V.jsonl.gz`（sha `783ec7e2…a7c41`，与事实 5 一致）重跑 `compare_detections` + `s1_verdict`：方形 p95 59.2934 ms（n 320）、计数不一致 3、最大差 0.0991905、未配对 66 → `STOP(FP16_BOX_DIVERGENCE)`；矩形 p95 58.9542、计数不一致 0、未配对 0、最大差 0.0259141 → 同 STOP（不进 verdict）。**与证据逐值相同**。
  - S2：`s2-system-e/results-e/s2-det-assoc-v1-fp16-640-15hz.json`（sha 与证据 `raw_sha256` 相同）重跑 `bin_rows`/`throttle_events`/`other_cooling_changes`/`frequency_evidence_gaps`/`s2_verdict`：六格 n 4407/4458×5、p95 66.993…67.453、丢帧 78+28×5 = 218、热事件 0、`ruling_needed` 空、比值 1.0021 → `STOP(FRAME_DROP)`。**与证据逐值相同**；首次 init 3,452.8 ms、最大 update 129.0 ms 与报告 §2e 一致。
- cmd 核对：AC-10 `git diff --stat $BASE..$CAND -- Assets controller config` 空；代码中引用的全部账本条目标题（SUB:1/3/2/5、CPU-1、题 7 (α)、(α′)、IR-8 D5 代拍、known_hosts、`PENDING_USER` (h)(n) 四条）在 `docs/authorizations.md` 逐字存在；`-env.json` 六项 S0 检查全过（Super、GPU 1,020 MHz、6 核 1,728 MHz、`MAXN_SUPER`、`multi-user.target` + display-manager inactive、空闲 RAM max 725 MB，n 298）。

### §1 逐文件核对摘要

| 文件 | 结论 |
|---|---|
| `tools/eng_jet/common.py` | 受保护根 `PROTECTED_ROOTS = (主树 runtime/, 数据根)` 结构性拒写（`refuse_protected` 用 `_resolved` 处理不存在路径）；`require_scratch` 只允许 `outputs/eng-jet/`、`~/eng-jet/`、系统临时目录且不允许根本身；nearest-rank 分位数 `max(1, ⌈q·n − 1e-12⌉)` 与 §2.1 一致（n = 320 → 第 304 个，n = 25 → 第 24 个，单测钉住）；信封常量与账本/提案 CLARIFY 逐字对应（SUB:1 6.5 GB 含历史、SUB:2 四种上限、SUB:5 det-assoc ≤ 2 / 回放 ≤ 2 共用全套次数）。`a7_frames_dir` 只读数据根或主树同一相对路径。 |
| `tools/eng_jet/relay.py`（K1） | 前向白名单 `classify_forward` 只收 `frames/frame_<10位>.jpg|json` 与 `frames/latest.json`，越界/`truth/`/`language_request.*` 一律 `reject_path`；板侧成员先 sha 核再 `os.replace` 原子落盘，指针只在两成员已在**本连接**收到且盘上 sha 复核一致且 `frame_id` 严格递增时发布（`refuse_pointer` 记 `incomplete_bundle`/`order_violation`）；新连接 `members.clear()` 但 `last_published` 保留（跨连接顺序守卫）。回程白名单 5 文件、内容变化即推、桌面机原子写入 `outputs/eng-jet/runtime-desktop/`。断链：发送端阻塞重连（退避 ≤ 2 s）、`forward_once` 只发当前 `latest.json`、`last_sent` 仅在三件全部送入后更新（送入失败则重连后重发当前包）；回程去重状态见 R1-1。对时四时戳式 `offset = ((t2−t1)+(t3−t4))/2`、`delay = (t4−t1)−(t3−t2)` 正确；`recv_matching` 丢弃旧 seq（冒烟缺陷修复，红绿已记）。分析器：到达时延 = 板发布 − 桌面发布 − 偏差（最近 5 样本最小延迟过滤），回程 = 桌面到达 − (板写入 − 偏差)，`capture_age_s` 未校正/校正两列并报，完整率分母 = `send_bundle` 数、分子要求两成员 sha_ok + 已发布 + 与回放收据 sha 一致，`latest_pointing_to_incomplete_bundle` 以到达单调钟独立复算，`lost_in_flight` 单列不扣分母（AC-4 修订 1）；`disconnect_analysis` 的窗口、缺口、`no_backfill`、回稳（预注册 `RECOVERY_*`）与 `recovery_after` 读法一致。`DesktopRelay.forward_once` 跳过 `published_unix_s` 早于本进程启动 5 s 以上的残留指针（f1 返工，`DesktopStalePointer` 红绿）。 |
| `tools/eng_jet/replay_publish.py` | 只改 `frame_id`/`capture_unix_s`/`capture_monotonic_s`，`capture_monotonic_clock_id` 逐字沿用，JPEG 字节不改（`ReplayAndEcho` 钉住差异键闭集）；发布顺序先两成员后 `latest.json`（`tethered-frame-manifest/v1`，`published_unix_s` 桌面墙钟）；运行目录须 `require_scratch`。 |
| `tools/eng_jet/track_responder.py`（K1/K3） | 引擎身份 sha 不符即 `ENGINE_IDENTITY_MISMATCH` 退出、不调插件工厂；init 框 = 板上首帧 `detection_rows` 中规格 `classes` 唯一 `target` 类（类号 1）最高分框，不读真值、不用离线替身；`TrackLoop(repository, plugin, publisher, RecordSink, track_id, condition="follow", ground_plane_y_m=0.2, maximum_ground_range_m=1000, planned_duration_s)` 与 `run_tracker` 非会话分支同形（构造签名经 `controller/track_loop.py:225–262` 核对）；驱动 `process_available(latest)`，终止后不重播种、不重启、只记 `post_terminal_frame`（AC-6 语义）；`RecordSink` 仅改名 `state → loop_state`（IR-21），其余键值原样；`RecordingPublisher` 只在 `RuntimePublisher` 各写桥之后记时戳、不改写桥函数。`controller/` 零改动。 |
| `tools/eng_jet/fastlayer_bench.py`（K3） | 冻结插件只经 `DetAssocTracker(spec_path, device, model_loader, tracker_factory)` 注入；`manifest_identity()` 仍报 `.pt` sha（证据 `weights_sha256 d6a0d6a9…`、`spec_sha256`、`freeze_sha256`、`device cuda:0`、`device_fallback None`）；`TimedModel` 仅矩形引擎改写 `imgsz`（AC-2 修订 4）；`detection_rows` 与 `tools/eng_det/evaluate.Detector.detect_image` 同口径（裁剪、归一化 xywh、7/6 位舍入，逐行比对一致，差别只在显式传 `iou=nms_iou`）；`compare_detections` 计数窗帧 0…49、判门窗帧 1…320、同类贪心 IoU ≥ 0.5、两侧未配对一律进不一致清单（AC-2 修订 1 / IR-6）；`s1_verdict` 时延先于一致性；`s2_verdict` 顺序 THERMAL_THROTTLE → FRAME_DROP → LATENCY_OVER，频率证据缺失/未确认告警时 verdict 留空（AC-3 修订 1）；`count_drops` 落后满一帧计丢；`export_engine` 导出前后核 `.pt` sha；`verify_summary` 原第一项字面保留（修订 6 替代判据在接受裁定与证据中体现，代码不改写原判据）。 |
| `tools/eng_jet/env_probe.py` | 15 条只读命令，无 `sudo`/`nvpmodel -m`/`systemctl isolate`/`jetson_clocks`（`NoSystemSettingChanges` 钉住）；`evaluate` 按 §2.1 表内顺序取第一个失败原因码，MAXN_SUPER 可选未选、非 headless 不记 PASS；dmesg 非 root 被拒时以 `journalctl -k -b 0` 替代并保留原文（IR-1）。 |
| `tools/eng_jet/assets.py` / `evidence.py` / `ledger.py` | 板上清单扫描：路径禁项 + JSON/JSONL 内容禁键 `grep -rlE`，第三方包树文件名命中单列、内容命中仍违规；`ac12_split`/`ir22_named_protocol_split` 只按具名路径分列、不改原 `violations`/`ac12_clean`（证据中 `ac12_clean: false`、`true_violation_count: 2` 原样保留）；`compact_listing` 不影响违规判定；`_forward_ok`、`disconnect_ok`、`relay_doc_f` 的 verdict 合成与 §2.1 SR 通过线一致；`ledger.build` 逐维度对照信封，`sub5_dimension` 不与 `sub2.other_model_loads` 重复扣账，`git_diff_stat` 以运行时 HEAD 取样（1A §2 已说明取样时点）。见 R1-2、§5。 |
| `tests/test_eng_jet_*.py`（4 件） | 覆盖：板侧拒发不完整/乱序/越界/sha 不符、保留修剪、无补发、残留指针、对时错位回归、双进程回环原子发布顺序与回程绑定、真实 TrackLoop 应答器（init 来源、身份不符不加载、GAP 不重播种、无 target 不 init）、进程内断链回环、回稳读法合成场景、S0/S1/S2 纯函数、禁键/禁路径扫描、受保护根拒写、代码束纯标准库、`tools/eng_jet` 不导入真值包、`controller/` 不导入 `tools.eng_jet`、SUB:1/SUB:2 计账、IR-22 分列、链路事件分列。未覆盖：`BoardRelay.return_watch` 重连去重（R1-1）、`sub5_dimension`（§5）、`relay_doc_f` 的 `disconnect_ok` 合成。 |
| `tests/test_det_assoc_carrier.py` | 仅 `CarrierSelfTest` 两例把 `create_tracker("det-assoc-v1")` 改为 `DetAssocTracker(spec_path=SPEC, device="cpu")` 并替换导入（AC-10 修订 6 字面）；`clip_box_norm` 导入与其余流程/断言/skip 不变；`ResidentCarrierReplay` 未动。 |
| 证据 JSON / 报告 / 交接 | 报告 §1 verdict 表与各 JSON 一致：S0 `PASS`、S1 `STOP(FP16_BOX_DIVERGENCE)`、S2 `STOP(FRAME_DROP)` + `RESUMED_AFTER_USER_RULING(S1)`、SR `PASS` + 双 `RESUMED`（各指账本标题，逐字存在）、S3–S5 `NOT_RUN(阶段 B 信封未签)`；§2d/§2e/§2f/§3 Q1–Q4 抽查数字（p95 59.29、GMC p95 39.02、六格 p95、f2/f3 到达/偏差/漂移、回程、端到端、回稳）均可追溯到 JSON 并与本轮重算相同；§5「不可推出」含 SR 范围、n = 29、S1 解释未验证、链路抖动等；无「验收通过」/研究资格/未测 Jetson 主张；C1-AC13-1 的 §5 三条分列与 §2g/§2h/§6 时点标注已消除现行/历史歧义。 |

### §2 AC 逐项与 C2 关注项（依据列 `BC-n` 读作 AC-n）

| AC | 结论 | 依据 |
|---|---|---|
| AC-1 | 成立 | 六项读数原文与预注册判定齐、`PASS`；修订 1（非 root `nvpmodel -q`、`journalctl -k -b 0` 替代）读法已由接受裁定，代码与证据一致；`not_executed` 列明未改系统设置。 |
| AC-2 | 证据义务成立；verdict `STOP(FP16_BOX_DIVERGENCE)` 保持，**不记满足**（§2.1：STOP 步骤不记满足） | 两版引擎 sha/导出参数/TRT 10.16.2.10、320 帧四分项、`within_50ms=false`、计数/最大差/IoU 直方图/逐帧最大差直方图/不一致帧清单（284 条）齐；引擎由 sha 核对过的冻结 `.pt` 导出（前后 sha 相同）；规格/权重/关联参数未改（`manifest_identity` 与事实 3 相同）；本轮重算 verdict 相同；修订 1/3/4/5/6/7 标注齐（二进制兼容、`[W]` 告警影响未明）。用户 (α) 只放行后续，S1 不改写。 |
| AC-3 | 证据义务成立；verdict `STOP(FRAME_DROP)` 保持，**不记满足** | 六格 p50/p95/max、GPU/CPU 上限与当前频率、温度、丢帧、tegrastats 功耗/温度分格齐；30 Hz 条件（p95 ≤ 33）未触发；修订 1 三项合取顺序与代码一致；本轮重算 verdict 相同。 |
| AC-4 | 成立 | f2/f3 各 1,500 送出 / 1,500 完整发布（sha 一致）/ 顺序违反 0 / 指向不完整包 0；到达时延 p50/p95/max、偏差中位/漂移已报；`TAILSCALE_SMOKE` 只在非结论小节、f1 返工轮单列 `rework_rounds`；修订 1（分母 = 实际送出、不扣在途）与修订 2（启动/收工事件保留、传输中事件 0——本轮直接从原始收据核实）成立。 |
| AC-5 | 成立（描述性） | 回声 n 1,500 与真实 n 29 两模式回程/端到端 p50/p95/max、`capture_age_s`（n 1,500 / 1,498）与 `load_elapsed`（n 1,500 / 28）对照 `T_STALL_S`/`T_pub`、真实 `frame_age_ms` n 1,500 超线 0 均报；init 来源 = 板上首帧检测器自身 target 类最高分框（`init_detection.pick` 与 `init.box_norm` 相同，`select_init_box` 读码 + 单测）；修订 1 分母分列成立。n = 29 只作描述，报告已如实限定。 |
| AC-6 | 成立 | 10 s / 60 s 各一次（实测 10.004 / 60.001），两侧存活（退出码全 0、`process_stops` 全真）、断链期间板侧写桥 0、缺口 49 / 299、latest 帧差 50 / 300、TrackLoop 第一次重连 `GAP` 终止、不重播种继续存活（`post_terminal_frames` 868）、回稳 0.134 / 1.940 s ≤ 60 s（预注册读法先于运行写定）；软件定时断链依 IR-8 / D5 代拍账本。 |
| AC-7 / AC-8 / AC-9 | **不满足**（`NOT_RUN(阶段 B 信封未签)`，未运行） | 三份 JSON 只有 `NOT_RUN` 与 0 查询/0 下载；本轮不代替完整探测验收。 |
| AC-10 | 成立 | `within_envelope: true`：板上 pip 7 / 242,752,639 B ≤ 8 / 300 MB；到板 18,870,709 ≤ 100 MB；SR 5/5（冒烟 1/1，每轮 ≤ 61,704,978 B）；墙钟 8,545 ≤ 28,800 s；导出 9.7 / 375.4 / 367.9 s ≤ 1,200 s；VLM 0；板上盘 5,163,883,873 ≤ 13 GB（SUB:1 生效）；SUB:1 23 包 / 5,616,357,711 B / 新增盘 4,829,972,625 B 在限内；Mac pip 0、模型 6（CSRT 2 + NanoTrack 2 上界 + det-assoc 2）、outputs 70,231,574 B；全套 1/1、部分回放 2/2；`Assets/controller/config` diff 空（本轮 cmd 复核）。计账为累计数量核验，设备/外联未运行时监测（§5）。 |
| AC-11 | 成立 | `.pt`/`freeze.json`/`frozen-V`/规格 sha 与体积一致；a7 帧 0…320 与 0…1,499 逐帧对 FAST-002 参照一致；D/E/F 使用前板上 334 / 335 / 30 件复核全一致；SR 四轮回放帧逐帧参照一致；阶段 B 资产 `NOT_USED`。参照文件字段见 R1-3（非泄漏）。 |
| AC-12 | 成立（在具名读法下） | 板上清单 37,714 文件；机械违规 3 = `home/cuda-cache/index`（修订 2 具名驱动缓存文件名）+ `runtime/sr-f/{f3-track,f4-track-drops}/gimbal_command.json` 内容禁键（修订 4 具名）；本轮**核实来源**：`controller/gimbal_entry.look_at` + `controller/protocol.packet` 只写 `protocol/channel/command_id/issued_unix_s/expires_after_s/command{mode,target_world_m{x,y,z}}`，唯一命中键 `target_world_m`；值由 `TrackLoop._publish_latest` → `box_ground_intersection(box_norm, 帧元数据, ground_plane_y_m)` 由**检测框 + 帧元数据相机位姿 + 显式地平面**求得（`controller/geolocate.py:57`），是控制输出、非 smoke `target_*` 真值；桌面机回传副本（`outputs/eng-jet/runtime-desktop/gimbal_command.json`）键集与上相同。本机取回的 f3/f4 `track-records.jsonl`、`track-receipts.jsonl`、两侧 `relay-receipts.jsonl` 以 AC-12 禁键正则直接 grep 命中 0；扣除具名后真正违规 0；原 `ac12_clean: false` 保留，不改写。受保护根零写入（主树 `runtime/`、数据根 `-newermt` 均 0）；`refuse_protected` 断言与单测存在；`tools/eng_jet` 不导入真值包、代码束纯标准库。 |
| AC-13 | 成立 | §1 表 verdict 闭集内、`RESUMED` 指向账本标题、Q1–Q4 数字、建议、不可推出清单齐；抽查数字可追溯并与重算相同；现行/历史分列已闭合 C1-AC13-1。 |
| AC-14 | 成立 | 执行记录表含每步机器/时间/HEAD 解析规则（含两个取样时点说明）；`UNITY_NA` 附议见 §4。 |
| AC-15 | 成立 | (h)(n) `answered` 并列账本标题（逐字存在），(i)–(m) `unanswered` 且对应动作零执行（无租云/WSL2/3a/base 下载/重刷/`systemctl isolate`/`nvpmodel -m`；`stage_b.signed=false`）。 |
| AC-16 | 成立 | 补跑E `MPLCONFIGDIR=/home/jetson/eng-jet/home/mpl` 匹配、补跑F 四轮 `all_match: true`，`YOLO_CONFIG_DIR`/`CUDA_CACHE_PATH` 重定向保留，外部新写仅 `~/.local/state/wireplumber/restore-stream`（ssh 会话服务，IR-18 同源）。 |

C2 关注项核实：**Carrier/scene006** → 见 R1-5 / R1-6（`SCOPE_GAP`，非阻断）；**K1 恢复只发当前包、缺口即 GAP、回程重连去重、残留指针边界、分析器按 frame_id 归并** → 读真实代码：不补发与 GAP 语义成立并已入报告建议 3(b) 交 ACQ-001；回程去重状态跨连接保留列 R1-1（CLASS_3）；残留指针守卫比较桌面机自身墙钟、5 s 宽限，本会话同号帧照常转发（单测钉住）；分析器按 frame_id 归并在 f1 的同号旧指针情形把 1 个旧包计为完整（证据 `rework_rounds.analysis_note` 已如实说明，f1 不进结论）。**AC-12 具名字段/来源** → 已核实（上表）。**SUB:5 无专门单测、NanoTrack/回放保守计账、外联未监测、IR-20 告警、轮间链路抖动、S3–S5 NOT_RUN** → 均为如实披露的限制，非 finding（§5）。**IR-15（ultralytics 8.4.104 的 psutil/polars/pynvml 为惰性导入）** → 数据根同版本轮子源码核：三者无模块顶层 `import`，16 处均在函数体内，读法成立。

### §3 Findings

| ID | 分级 | 依据 | 阻断 | 摘要 |
|---|---|---|---|---|
| R1-1 | CLASS_3 | `BC-6` | 否 | `BoardRelay.return_watch` 的回程去重状态 `_last_return` 跨连接保留，重连后不重发未变化的当前回程文件版本，与模块说明「回程同理只发当前版本」不一致 |
| R1-2 | CLASS_3 | `BC-4` | 否 | `relay.analyze` 的 `link_events` 截断 `[:50]`，AC-4 修订 2 的「传输中事件」计数从截断列表派生 |
| R1-3 | CLASS_3 | `BC-12` | 否 | AC-11 帧参照源 `P1-ENG-FAST-002-dataset-frames.jsonl.gz` 行含标签类字段（`positives`、`target_visible_flag`、`ignores`），桌面机解析整行后只取 `sha256`；不上板、不进插件/控制器 → 非泄漏，但参照源宜改为纯 sha |
| R1-4 | CLASS_3 | `BC-10` | 否 | `ledger.build` 的 `mac.pip = 0`、`system_settings.changed = []` 为常量断言而非测量；`sub5_dimension`/`relay_doc_f.disconnect_ok` 无专门单测 |
| R1-5 | CLASS_2 | `SCOPE_GAP` | 否（路由接受角色） | `CarrierSelfTest::test_carrier_matches_caliber_b_from_first_update` CPU 对 MPS 参考逐帧比较 10 处不等（索引 2 = `frame_id=3` 宽差 ≈ 4.8e-8，其余 9 条未知；比较后三类断言未执行；两例不再经 `create_tracker` 工厂）——det-assoc 冻结插件 CPU/MPS 数值一致性不在本项合同（`controller/` 零改动、无 AC 覆盖），按 AC-10 修订 8 用户具名例外携带 |
| R1-6 | CLASS_2 | `SCOPE_GAP` | 否（路由接受角色） | `tests/test_scene006_probe.py` 29 条（25 FAIL + 4 ERROR）相对 R7 新增：本机主树缺 re-anchor/NanoTrack 权重，`verify_weight_binding` 首项即 `FAIL_WEIGHT_HASH`；相关代码相对 R7 零 diff（本轮核对交接给出的 diff 命令口径），未在补齐资产环境验证 |

#### R1-1 回程文件重连后不重发当前版本（`tools/eng_jet/relay.py::BoardRelay.return_watch`）

- 合同/说明：§3.2「不缓存补发过期帧（只补发当前 `latest.json` 指向的包），回程文件同理」；模块 docstring「恢复后只发当前 `latest.json` 指向的包；回程同理只发当前版本」。AC-6 记录「恢复后行为如实记录」。
- 实现：`return_watch` 对每个回程文件以 `_last_return[name] == digest` 去重；`run()` 接受新连接时只 `members.clear()`，`_last_return` 不清。若某版本已 `sendall` 入内核缓冲后链路断开（数据丢失），`_last_return` 已更新 → 重连后该版本不再发送，直到文件内容再变化。
- 影响：有界——至多每次重连丢失一份未变化的回程文件版本；回声/真实模式下 `tracking_observation.json` 每帧变化，f4 实测 `returns_received == observations_written`（29/29），本轮读数不受影响；AC-4…6 判定不变。
- 补丁（逐字，由实现角色在下一次提交应用；属 PLAY_GOVERNING 文件，按 workflow §4.4 开轮资格处理）：在 `BoardRelay.run` 的 `self.members.clear()` 之后加一行 `self._last_return.clear()`，并在 `tests/test_eng_jet_relay.py::BoardRelayInProcess` 补一例：`_last_return` 置为当前文件 digest 后模拟新连接，断言 `return_watch` 一轮内重发。

#### R1-2 `link_events` 截断（`tools/eng_jet/relay.py::analyze`、`evidence.py::_link_event_split`）

- `analyze` 把 `connect/drop_start/disconnect/link_down/reconnected_after_drop` 事件写入 `link_events` 时 `[:50]` 截断；`contract_readings_relay` 的 `in_transfer_event_count` 从该列表派生。本轮 f2/f3 各仅 2 条、f4 10 条，无截断发生，且本角色已从原始收据直接核实 f2/f3 传输中事件 0；读数不受影响。
- 补丁：`"link_events": [...]` 去掉 `[:50]`（或另给 `link_events_total`），`_link_event_split` 读全量。

#### R1-3 帧参照源含标签类字段（`tools/eng_jet/assets.py::frame_reference`）

- `verify_frames`/`replay_frames_check` 以 `docs/evidence/P1-ENG-FAST-002-dataset-frames.jsonl.gz` 为 a7 帧 sha 参照；该文件每行键为 `atom, domain, excluded, exclusion_reason, family, frame_id, ignores, positives, sha256, status_counts, target_visible_flag`。代码只投影 `frame_id → sha256`，运行在桌面机，不上板、不进 `DetAssocTracker`/`TrackLoop`/中继负载；板上清单扫描无该文件。不构成真值泄漏（非 `RED_LINE`）。
- 建议：改用只含 `frame_id, sha256` 的参照（例如 `-assets.json` 内已记录的逐帧 sha 列表或 `frozen-V` 头部派生），并在 `-assets.json.frames[].reference` 注明「参照源含标签字段、仅取 sha」。

#### R1-4 计账常量与未覆盖函数（`tools/eng_jet/ledger.py`、`evidence.py`）

- `mac.pip` 与 `system_settings.changed` 为硬编码 0 / 空；`within_envelope` 只比较累计数量，不检测设备、外联或系统设置（接受核对表 AC-10 行已如实注明）。`sub5_dimension`、`relay_doc_f` 内 `disconnect_ok` 合成式无专门单测（实现交接 §8 已披露）。
- 建议：`tests/test_eng_jet_guards.py` 补 `LedgerSub5`（det-assoc ≤ 2、回放 ≤ 2、与 `mac_full_suite_run` 共用 ≤ 1、越界为假）；把 `disconnect_ok` 提为具名纯函数并单测。

#### R1-5 / R1-6（`SCOPE_GAP`，路由接受角色记入「范围外已知缺陷」账本）

- R1-5：失败源于 CPU-1 把两例改为显式 CPU 构造后与口径 B（MPS）参考逐帧严格相等断言不成立；本项合同不含 det-assoc 的 CPU/MPS 数值一致性（`controller/det_assoc_tracker.py` 零改动，AC-1…16 无此项），不可从本项生产入口产生。按账本 2026-10-03「用户裁定线 A 全套结果：Carrier CPU 失败选 A…」与 AC-10 修订 8 作本停点具名例外携带，本轮**不以此阻断**；未验证残余（其余 9 条形态、比较后 `confidence_source`/观测桥字段集/临时目录外写入断言、真实工厂覆盖损失）须由接受角色记债，不得读作通过。
- R1-6：环境缺资产导致的失败，与候选无关（R7 零 diff）；记债并保留「相对 R7 新增」与「环境归因、后续断言未验证」双列。

### §4 UNITY_NA

AC-14 申请 `UNITY_NA`，理由「零 Play、不改 Unity 运行行为，硬件证据即板上实测文件」。本轮独立核实：`git diff --stat $BASE..$CAND -- Assets controller config` 为空；候选未触及 Unity 场景/脚本/文件桥、帧与控制协议字段（中继只搬运既有文件，`replay_publish` 只改帧号与时钟）；`-ledger.json` `unity_play 0`、`scenario_session_run_ids 0`；硬件证据为板上原始日志（sha 入证据）且本轮从本机取回原件重算一致。**复核附议 `UNITY_NA`**（仅限本候选的阶段 A 范围；S3–S5 若日后加代码属另一候选，届时另议）。

### §5 非 finding 观察（不阻断）

- S1 一致性 STOP 的「输入形状（方形 letterbox vs 参照矩形 letterbox）」解释（报告 §2d）：矩形引擎计数不一致 0、未配对 0、最大差 0.0259 的读数与该解释相容，但未经额外运行验证；本轮不据此改判，交 ACQ-001/后续立项参考。
- S2 丢帧 218 含首次 init 冷启动 50（3,452.8 ms）；合同未排除冷启动，verdict 成立；1,529 次 `update` 超 66.7 ms 节拍但未满一帧（线束口径不计丢）已在报告披露。
- 回稳 `recovery_s` 取合格连续 10 帧首帧的桌面发布时刻相对重连（0.134 / 1.940 s），确认时刻在约 2 s 后；接受已裁定该读法，报告写法一致。
- SR 真实模式回程 n = 29（第 30 帧起 `bound_track_unmatched`、compat 不改绑）、`end_to_end` 含 init 冷启动追帧（p95 239.6 ms）；只作描述。两机偏差中位 8–9 ms、漂移 −2.4 ppm 只代表 mini↔Jetson 有线 + 板上 NTP。
- 任一断链（≥ 1 帧缺口）使 compat `TrackLoop` 以 `GAP` 终止、需人工重初始化——K1 接口发现已写入报告建议 3(b) 交 ACQ-001；本项不改门。
- IR-20 的 TRT `[W]` 跨设备计划告警在 E/F 各次加载均出现，原因与影响未核实；读数按裁定保留，不扩大主张。
- 全套相对 R7：18 条「未出现」无逐名 skip 日志、skip 19→56 只聚合可比；NanoTrack 2 / CSRT 2 为构造尝试上界；未设 `YOLO_OFFLINE` 跑全套、外联未监测。均为实现/接受已披露的限制。
- `tests/test_eng_jet_bench.py::InjectionOnly` 依赖 gitignored 冻结权重，副本内跳过；在有权重的主树通过（实现日志 72/72）。

### §6 Verdict

Verdict: PASS_WITH_NOTES

`R1@K1K3K4` 通过：无 CLASS_1/2 阻断 finding、无 `RED_LINE`、无 `上轮漏检`，不写 `blocks_consuming_gate`。R1-1…R1-4 为 CLASS_3，补丁由实现角色在下一次提交应用（R1-1/R1-2 触及 `tools/eng_jet/relay.py`，按 workflow §4.4 开轮资格处理，不作为本轮消费前提）；R1-5 / R1-6 `SCOPE_GAP` 非阻断，路由接受角色入「范围外已知缺陷」账本并作归因。AC-7/8/9 `NOT_RUN(阶段 B 信封未签)` 不满足，S1/S2 `STOP` 不记满足——本 verdict 是对候选（阶段 A 实现、证据与读数）的独立复核通过，**不是阶段 A 探测验收、不是 `DONE`、不推出任何 Jetson 性能或部署结论**；`UNITY_NA` 已附议（§4）。交接受角色消费；Overall 与 Lifecycle 由接受角色维护。

passed_candidate: b4f145655155d2c4870c9001f2a85d539f4cf53a

边界自查：本会话未修改任何实现文件；主工作树只写本文件与状态板。副本内只读码、跑 focused 与纯函数重算（临时输出在会话暂存目录），`git status --porcelain` 为空，副本收工删除。

## R2@K1K3K4（2026-10-04）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-JET-001-R2@K1K3K4-20261004T021255Z-b2a6`，`requested.round = R2@K1K3K4`）。零消耗：零模型构造/推理、零回放、零上板/ssh、零全套/SR 重跑、零下载安装（全套/SUB:6/SR 均无余额，本轮未申请）。只在一次性副本内读码、重跑 focused、对 R1-1…4 回归做修前红/修后绿、写零模型交错探针、以标准库核对纯参照与账本事件文件。

### §0 候选、双基线与开轮资格

- `round_candidate: a0e3594b5fd081133d06ebdc3b4fd40b539b3e4a`（= 交接「K1K3K4全套SUB6：…」§6 规则运行时解析：`git log main --grep='^P1-ENG-JET-001 K1K3K4全套SUB6 收工'` 恰 1 条、触及交接文件、为 `origin/main` 祖先；与派发提示 `candidate_bound` 相同）。
- 双基线：上一通过候选 `PASSED` = 本文件最近 `passed_candidate` = `b4f14565…4f53a`（R1）；上一复核轮候选 = R1 §0 `round_candidate` = 同一 SHA，故「修复触及行」与「全量 diff」本轮同源。`CODE`（`K1K3K4R1注记修补 收工`）= `c2ef50f0…48d23`；`git diff --stat $CODE $CAND -- tests tools controller Assets config .gitignore` **为空**（全套执行版本与候选代码一致）。`BASE`（`K1K3K4 开工` 父提交）= `4cbd7bd9…c2d`，`git diff --name-only $BASE..$CAND` = 38 路径，`git diff --stat $BASE..$CAND -- Assets controller config` **为空**。
- `git diff --name-only $PASSED..$CAND` = 18 路径：代码/测试 6 件（`tools/eng_jet/{relay,evidence,assets,ledger}.py`、`tests/test_eng_jet_{relay,guards}.py`，+346/−47）；新增证据 `docs/evidence/P1-ENG-JET-001-a7-frame-sha256.jsonl.gz`、`-R1notes-focused-tests.log`、`-SUB6-full-suite.log`；`-ledger.json`（+151/−0，纯追加）、`-report.md`（§2i 与现状行）、`-K1K3K4-handoff.md`（两节）、`docs/implementation-status.md`（R1-5/6 两行 OPEN + R1消费节）、提案（SUB:6 落实、C3 核对表）、账本（SUB:6 与 A补丁:2 两条，逐字存在）、状态板、派发登记、本文件（R1 轮）。逐文件已核，无未声明的代码改动。
- 开轮资格：PLAY_GOVERNING（`tools/`、`tests/`）diff 非空 → 开轮。R1 为通过轮，本停点 `REWORK_REQUIRED` 此前 0 次。
- 停点自证（交接 SUB6 §7）四项：①成立（`CODE..CAND` 零代码 diff、IR-26/27 已裁定）；②「在用户具名例外下成立（不记通过）」——账本 2026-10-04「用户签发 SUB:6…并为新候选重新具名 Carrier/scene006 两项例外」授权范围 (2) 逐字存在，本角色接受其进入复核；③不适用；④齐。→ 不判 `REVIEW_BLOCKED`。
- 副本 `.claude/worktrees/review-P1-ENG-JET-001`（detach 于候选）；测试树哈希 `HEAD:tests = 185ad7f3281b67b9fd6399b330d09c434899d0c4`，`HEAD:tools/eng_jet = 8b3f0b0479ef8a17b155a54c84b57f4ab5fc423c`；解释器 `~/TetheredDroneTracking-full/.venv-yoloe/bin/python`（3.12.14，只读使用）；执行机 `zc5s-Mac-mini.local`。
- **focused 重跑**（副本内 `YOLO_OFFLINE=true YOLO_AUTOINSTALL=false … -m unittest discover -s tests -p 'test_eng_jet_*.py'`，输出写会话暂存目录）：**82 tests OK（skipped=1）**；跳过者经单独定位为 `test_eng_jet_bench.InjectionOnly`（副本无 gitignored 冻结权重），与 R1 相同；候选 `-R1notes-focused-tests.log` 为 82/82 无 skip（主树有权重），一致。副本 `git status --porcelain` 跑后为空。
- **R1-1…4 回归红/绿（副本内 sed 回退 → 跑 → `git checkout` 恢复，各一次）**：R1-1 去掉 `adopt_link` 内 `_last_return.clear()` → `test_reconnect_resends_current_return_version` FAIL（`0 != 1`）；R1-2 恢复 `[:50]` → `AnalyzeLinkEventsFull` FAIL（`50 != 61`），去掉 `None` 读法 → `test_link_event_split_reads_full_list_and_refuses_truncated` FAIL（`49 is not None`）；R1-3 放宽读取方键检查 → `PureFrameReference.test_loader_rejects_label_keys` FAIL（`ValueError not raised`）；R1-4 改回 `drops["disconnects"]` → `DisconnectPass` ERROR（`KeyError`）。恢复后 relay 2 例、guards 8 例全绿。
- **全套证据核对（不重跑）**：`-SUB6-full-suite.log` `Ran 2146 tests in 231.849s` / `FAILED (failures=27, errors=10, skipped=56)`；与 CPU1 `-full-suite.log`（2136）比较：`FAIL:`/`ERROR:` 名 37 = 37 逐名相同，`======` 至 `Ran` 的失败详情段逐字节相同，全文差异仅 8 行（进度点行、两处临时目录名、`Ran` 行）；scene006 29 + Carrier 1（同一断言行、同一不一致索引集）= 相对 R7 新增 30，全部在 AC-10 修订 10 / AC-13 修订 4 具名边界内，例外外 0；2146 − 2136 = 10 = 本候选新增用例数（LedgerSub5 2、DisconnectPass 1、PureFrameReference 4、ContractSyncFullSuite 1、BoardRelayInProcess 1、AnalyzeLinkEventsFull 1），其名均不在失败清单、skip 数不变 → 全套中执行通过。
- **SUB:6 计账对账（本机即执行机）**：`outputs/eng-jet/P1-ENG-JET-001/ledger-events.jsonl` 含 2 条 `"sub": "SUB:6"` note 事件，与 `-ledger.json`「dimensions.mac.sub6.items」两项**逐键相同**；`common.disk_usage_bytes(outputs/eng-jet)` 现为 70,235,427 B = `after_accounting`；`-ledger.json` 相对 PASSED 只有 `+` 行（151/0），顶层 `within_envelope`、`mac.models`、SUB:2/SUB:5 块未改；SUB:6 各维度均 ≤ 账本授权范围 (1)。
- **纯参照独立核验**：`P1-ENG-JET-001-a7-frame-sha256.jsonl.gz` 61,905 B、3,168 行、键集恰 `{frame_id, sha256}`、首末帧 0…3167；`load_pure_reference()` 与 `legacy_frame_reference()`（原文件 43,535 行）投影逐项相等；`pure_reference_bytes(legacy)` 与已提交文件字节相同（确定性）；不在 `BUNDLE_FILES`（6 件）内。

### §1 逐文件核对（修复触及行 = 全量代码增量）

| 文件 | 结论 |
|---|---|
| `tools/eng_jet/relay.py` | `return_once` 由 `return_watch` 循环体原样抽出（判据、收据、计数不变）；`adopt_link` 在 `_link_lock` 内关旧连接、换 `self.link`、`members.clear()`、`_last_return.clear()`；`run()` 改调 `adopt_link`。`analyze` 去 `[:50]` 并加 `link_events_total`。**R2-1**：`return_once` 对 `self.link` 快照、`link.send` 与 `_last_return[name] = digest` 均不持 `_link_lock`，`Link.send` 返回后、写 digest 前若 accept 线程执行 `adopt_link`，清表被随后写回的旧 digest 覆盖，新连接跳过当前版本（§3）。其余路径：快照后 adopt → `send` 因 `alive=False` 抛 `ConnectionError` → break，digest 不写，下一轮重发，正确；`sendall` 中途被 `close` → `OSError` → 同上，正确。 |
| `tools/eng_jet/evidence.py` | `_forward_section` 仅在分析结果含 `link_events_total` 时带出（历史 JSON 不补造）；`_link_event_split(events, total)`：`total > len` → 截断、`total` 缺且 `len ≥ 50` → 未知（None）、否则 False；计数仅在 False 时派生，历史 f2/f3（2 条）/f4（10 条）读数不变。`disconnect_pass` 自 `relay_doc_f` 提出、判据逐字相同，缺 `disconnects` 判假。C3-P2 核实：`exit_codes` 由 `sr_round_f` 固定 4 键（`_rc` 缺文件返回 None → `None == "rc=0"` 为假，fail-closed）、`process_stops` 由 `relay.analyze` 固定 3 键、`disconnects[].recovery` 由 `disconnect_analysis` 必有（未重连时为 `{"recovered": False, "reason": …}` → `.get("within_limit")` 为 None → 假）；空字典空真只在手写输入下可达，生产入口不可达（§5）。 |
| `tools/eng_jet/assets.py` | `project_frame_sha`（只投影 a7 前缀、同帧冲突拒绝）、`legacy_frame_reference`（原读法保留）、`pure_reference_bytes`（gzip `mtime=0`、按 frame_id 排序）、`load_pure_reference`（两键闭集、64 位小写 hex、a7 前缀，违者抛错不静默）、`derive_pure_reference`（只读原文件、经 `common.atomic_write_bytes` 写出、记来源 sha/行数）、`frame_reference` 改读纯参照、`verify_frames` 新增 `reference_keys/derived_from/note`；CLI 加 `derive-frame-reference`。`BUNDLE_FILES` 未改，纯参照不上板。 |
| `tools/eng_jet/ledger.py` | 仅加 `CONSTANT_ASSERTION_NOTE`、`WITHIN_ENVELOPE_BASIS` 三处字面标注；`mac.pip`、`system_settings.changed`、`within` 数值与判据不变。无 SUB:6 维度（C3-P3，§5）。 |
| `tests/test_eng_jet_relay.py` | `test_reconnect_resends_current_return_version`（`FakeLink` 顺序两连接；修前红已核）只覆盖顺序调用，不覆盖 R2-1 交错；`AnalyzeLinkEventsFull` 合成 61 条收据（修前红已核）。 |
| `tests/test_eng_jet_guards.py` | `LedgerSub5`（上限/越界/共用全套/不重复扣账/常量标注）、`DisconnectPass`（逐条件证伪 + 缺键）、`PureFrameReference`（投影丢标签键、冲突拒绝、派生两键、来源不变、确定性、读取方拒绝、已提交文件 = 投影）、`test_link_event_split_reads_full_list_and_refuses_truncated`；修前红已核（§0）。 |
| 证据/文档 | `-ledger.json` 纯追加且与事件文件一致（§0）；`-report.md` §2i 数字可追溯到 SUB6 日志与账本块，旧「现状」行改标历史、不改 S1/S2/SR 读数；交接两节与本轮 git 解析逐项相同；`implementation-status.md` R1-5/6 两行 `SCOPE_GAP`/OPEN 与 R1 §3 一致；提案 SUB:6 落实三条修订与账本授权范围 (1)(2) 逐字对应。 |

### §2 AC 逐项（依据列 `BC-n` 读作 AC-n；未变化项沿 R1）

| AC | 结论 | 依据 |
|---|---|---|
| AC-1 / AC-2 / AC-3 | 沿 R1（S0 `PASS`；S1/S2 `STOP` 不记满足） | 七份 JSON 相对 PASSED 零 diff（`-ledger.json` 除追加块外同）；本轮不重算。 |
| AC-4（修订 3） | 成立 | 历史 forward 读数不变；全量 `link_events` + `link_events_total`；可能截断 → `None`（不是 0），`contract_readings_relay` 传总数；红绿已核。 |
| AC-5 | 沿 R1 成立（描述性） | 应答器/init 来源/控制器零改动。 |
| AC-6（修订 2） | **证据义务成立；新候选恢复行为存在偏差 → R2-1 阻断** | f4 为补丁前历史实测、读数不变；§3.2「回程同理只发当前版本」+ `adopt_link` 文档「重连后重发每个回程文件的当前版本」在 §3 交错下不成立。 |
| AC-7 / AC-8 / AC-9 | 不满足（`NOT_RUN(阶段 B 信封未签)`） | 三份 JSON 零 diff。 |
| AC-10（修订 9/10） | 成立 | SUB:6 全套 1/1、det-assoc 2/2、回放 2/2、NanoTrack/CSRT 上界 2、其余 0、outputs +3,853 B、墙钟 349 s ≤ 900；事件与 JSON 逐键相同；`Assets/controller/config` diff 空（本轮 cmd 复核）；Carrier 例外同名同类（同断言、同索引集）。 |
| AC-11（修订 1） | 成立 | 纯参照 3,168 行与原投影逐项相等、字节确定、历史 `-assets.json` 未改写。 |
| AC-12 | 成立 | 纯参照无标签字段、不在到板代码束；`refuse_protected`/受保护根断言未改。 |
| AC-13（修订 4） | 成立 | §2i 读数与日志/账本一致；scene006 29 条逐名逐类型同 CPU1，环境分列保留；无新 Jetson 主张。 |
| AC-14 | 成立（新候选 `UNITY_NA` 附议见 §4） | 交接 SUB6 §1–§2 执行机/时间/版本解析可运行时复算。 |
| AC-15 / AC-16 | 沿 R1 成立 | `pending_user`、`stage_b`、ac16 字段零 diff。 |

### §3 Findings

| ID | 分级 | 依据 | 阻断 | 摘要 |
|---|---|---|---|---|
| R2-1 | CLASS_2 | `BC-6` | **是** | `BoardRelay.return_once`/`adopt_link`：回程去重 digest 在 `link.send` 返回后、不持 `_link_lock` 写回，可覆盖 `adopt_link` 对 `_last_return` 的清空，新连接跳过当前版本——R1-1 补丁未闭合其声明语义（C3-P1 核实成立） |

#### R2-1 回程去重状态跨连接写回交错（`tools/eng_jet/relay.py::BoardRelay.return_once` / `adopt_link`）

- 合同：AC-6「`TrackLoop` 终止/继续语义…恢复后行为如实记录」；§3.2 / 模块 docstring「回程同理只发当前版本」；`adopt_link` docstring 承诺「清空 `_last_return` 使重连后重发每个回程文件的当前版本」。
- 实现：`return_once` 行 276 `link = self.link` 快照、行 ~289 `link.send(...)`、行 ~292 `self._last_return[name] = digest` 三步均在 `_link_lock` 外；`adopt_link` 在锁内 `close()` 旧连接并 `_last_return.clear()`。交错 T1 `old.send` 成功返回（已 `sendall` 入内核缓冲）→ T2 accept 线程 `adopt_link(new)`：`old.close()`、`_last_return.clear()` → T1 恢复写 `_last_return[name] = digest`、`returns_sent += 1`、写 `send_return` 收据 → 下一轮 `return_once` 在 `new` 上因 digest 相等跳过。`Link.send` 自身的 `_lock` 只保护 socket 写，不覆盖此写回。
- 复现（副本内零模型探针，`FakeLink` 子类在 `send` 返回前调用 `board.adopt_link(new)` 以确定化该交错）：`round1 sent on old: 1 | old.alive: False | board.link is new: True`、`_last_return` 非空、`round2 sent on new: 0`、`new.sent: []` → 新连接拿不到当前版本直到文件再变化。既有回归 `test_reconnect_resends_current_return_version` 只有顺序调用，无法捕获。
- 范围判据（可达）：触发状态 = AC-6 点名的断链后重连（生产入口 `BoardRelay.run` 的 accept 线程与 `return_watch` 线程并发，无守卫）；交错窗口为 `sendall` 返回到 dict 写入之间的若干字节码，发生需定时巧合，但一旦发生即复现 R1-1 所述丢版本。影响有界：每次重连至多各回程文件一份未变化版本不重发；`tracking_observation.json` 每帧变化可自愈，`gimbal_command.json`/`body_command.json`/`tracker_state.json`/`language_result.json` 在内容长期不变时丢失持续到下一次变化；f4 历史读数（补丁前代码）不受本 finding 改变，本轮不改任何数字。分级依据 workflow §4.4「并发/原子性」= CLASS_2；与 R1-1 的 CLASS_3 不同在于本条是修复触及行上新引入接口（`adopt_link`/`return_once`）自身声明语义的失效，而非既有行为的注记。
- 闭合要求（workflow §4.4 阻断 finding 四条）：修复任选其一——(a) `return_once` 在 `link.send` 返回后于 `_link_lock` 内仅当 `self.link is link` 时写 `_last_return[name]`（否则不写、不计 `returns_sent`，或计入但注明连接已替换）；(b) 去重状态随连接存放（如 `self._return_state: tuple[link, dict]` 或挂在 `Link` 实例上），`adopt_link` 换连接即换表，旧线程写回落到旧表。绑定修前必失败回归：`tests/test_eng_jet_relay.py::BoardRelayInProcess` 新增一例，fixture 沿用真实 `BoardRelay` 运行目录与 `write_bytes` 写回程文件（现有用例同口径），用 `send` 内调用 `adopt_link(new)` 的 link 替身确定化交错，断言换连接后一轮内 `new` 收到当前版本且 `_last_return` 不含旧连接写回。修复触及 `tools/`，`R3@K1K3K4` 由本角色红绿核实；不触及 Play 治理门。

R1-1…R1-4 闭合状态：R1-2、R1-3、R1-4 修前红/修后绿已核（§0），闭合；R1-1 补丁已应用并通过其顺序回归，但其声明语义在 R2-1 交错下未闭合，由 R2-1 承接，不另立「R1-1 闭合失败」条目。R1-5/R1-6 `SCOPE_GAP` 已入账本 OPEN，本轮不改判。

### §4 UNITY_NA（新候选）

AC-14 对新候选申请 `UNITY_NA`。独立核实：`git diff --stat $BASE..$CAND -- Assets controller config` 为空；6 件代码/测试增量均在 `tools/eng_jet/`、`tests/test_eng_jet_*`，只改板侧回程去重状态与桌面侧证据/账本/参照工具，不触及 Unity 场景/脚本、文件桥字段、帧与控制协议；`-ledger.json` `unity_play 0`、`scenario_session_run_ids 0`；SUB:6 全套在 Mac mini 本机、零 Play。**复核附议新候选的 `UNITY_NA`**（仅限阶段 A 范围；本附议不等于 verdict 通过——verdict 见 §6）。

### §5 非 finding 观察（不阻断）

- **C3-P2**（`evidence.disconnect_pass`）：`all()` 对空 `exit_codes`/`process_stops` 空真只在手写输入下可达；生产入口 `sr_round_f` 固定 4 键、`relay.analyze` 固定 3 键，`_rc` 缺文件返回 None 判假，`recovery` 必有。非 finding；实现角色可在下一次触及该文件时顺带断言四个具名键齐备（不开轮不要求）。
- **C3-P3**（`-ledger.json` SUB:6 块手工追加）：已核实事件文件与 JSON 逐键相同、diff 纯追加、顶层合计与 SUB:2/SUB:5 未改、不重复扣账；`ledger.build` 无 `sub6_dimension`，重跑 `ledger build` 会丢该块——交接 §3 与 JSON `recorded_by` 已披露。本轮按披露的限制对待；任何日后 `ledger build` 重跑前须先补代码支持，否则账本回退即为 AC-10 缺陷。
- `return_once` 写 `send_return` 收据表示「已 `sendall`」而非「对端已收」，与补丁前一致；分析器 `returns_received` 以桌面收据为准，不受影响。
- `adopt_link` 内 `members.clear()` 与旧连接 `serve_connection` 线程仍可能并发 `handle_file`（补丁前同样存在，仅移位），`publish_pointer` 的 sha 复核与 `last_published` 守卫使其只表现为该连接尾包被拒，不改前向读数；不在修复触及语义内，不列 finding。
- `_link_event_split` 对无 `total` 且 `len ≥ 50` 的旧结果判「未知」是保守读法，历史 f2/f3/f4 均 < 50，读数不变。
- 全套相对 R7「未出现 18」无逐名记录、skip 56 聚合、NanoTrack/CSRT 静态上界、未设 `YOLO_OFFLINE` 外联未监测、补丁未上板/f4 为补丁前实测——均为实现/接受已披露限制，照旧携带。

### §6 Verdict

Verdict: REWORK_REQUIRED

`R2@K1K3K4` 返工：1 条阻断 finding R2-1（CLASS_2，`BC-6`，修复触及行上的并发/原子性缺陷，C3-P1 主张核实成立），无 `RED_LINE`、无 `上轮漏检`，不写 `blocks_consuming_gate`（非未改动行上的漏检，不触发消耗性门机检）。本停点 `REWORK_REQUIRED` 计 1/2。修复直接回本角色（engineering-workflow §5，不经核对轮），`R3@K1K3K4` 按开轮资格开轮并对 R2-1 做修前红/修后绿。R1-2/3/4 已闭合；R1-5/6 债不变；AC-7/8/9 `NOT_RUN` 不满足、S1/S2 `STOP` 不记满足；新候选 `UNITY_NA` 已附议（§4）。本轮不写 `passed_candidate`；上一通过候选仍为 R1 行。Overall/Lifecycle 由接受角色维护。

needs_user（本角色不签、不借任何额度）：修复候选属 `tools/eng_jet/relay.py` + `tests/test_eng_jet_relay.py` 的零模型窄修，focused 全覆盖；其 workflow §4.3.1 第 2 项（停点全套）与 Carrier/scene006 例外是否随新候选再次具名，须用户决定——推荐 (a) 用户具名「本窄修候选以 focused + R2-1 红绿代替全套、原 SUB:6 两项例外读法沿用」（理由：改动不触及任何真实加载器，与 K1K3K4R1注记修补 §4 选项 (b) 同形，成本 0）；备选 (b) 另签 SUB:7 一次全套（预计与 SUB:6 同形：全套 1、det-assoc CPU 2、回放 2、墙钟 ≤ 15 min）。

边界自查：本会话未修改任何实现文件；主工作树只写本文件与状态板。副本内 sed 回退仅用于红检并已 `git checkout` 恢复，探针文件在会话暂存目录，副本 `git status --porcelain` 为空，副本收工删除。

## R3@K1K3K4（2026-10-04）

角色：复核（review，Claude Code Fable 子代理，新鲜上下文；supervisor 派发 `Dispatch-Id: P1-ENG-JET-001-R3@K1K3K4-20261004T024258Z-9f00`，`requested.round = R3@K1K3K4`）。零消耗：零模型构造/推理、零回放、零上板/ssh、零全套/SR 重跑、零下载安装、不签任何额度。只在一次性副本内读码、重跑 focused、对 R2-1 绑定回归做修前红/修后绿。

### §0 候选、双基线与开轮资格

- `round_candidate: 0e1c6cb5417bdd9c50564e56d9c7ad8ed48dfd06`（= 交接「K1K3K4R2返工：…」§3 规则运行时解析：`git log main --grep='^P1-ENG-JET-001 K1K3K4R2返工 收工'` 恰 1 条、触及交接文件、为 `origin/main` 祖先；与派发提示候选 SHA 相同）。
- 双基线：上一复核轮候选 `PREV` = R2 §0 `round_candidate` = `a0e3594b…b3e4a`；上一通过候选 `PASSED` = 本文件最近 `passed_candidate` = `b4f14565…4f53a`（R1）；`BASE` = `4cbd7bd9…c2d`。
- 修复触及行 `git diff $PREV..$CAND -- tools tests controller Assets config` = **仅 2 文件**：`tools/eng_jet/relay.py`（+13/−4：`return_once` 写回判定与 docstring、`adopt_link` docstring）、`tests/test_eng_jet_relay.py`（+31：`BoardRelayInProcess::test_adopt_during_return_send_keeps_new_link_dedup_clean`）。`$PREV..$CAND` 全部 8 路径：上述 2 件 + 状态板、交接新节、`-R2rework-focused-tests.log`（新增）、派发登记、提案（C3 核对表，3c8b778）、本文件（R2 轮，3d1e6d7）；逐路径已核，无未声明的代码改动。
- 全量 diff `$PASSED..$CAND` = 19 路径（R2 的 18 + 新 focused 日志），代码/测试仍为 6 件；`git diff --stat $BASE..$CAND -- Assets controller config` **为空**；`$BASE..$CAND` 39 路径。候选之后至本轮开工 HEAD（`6b76213`）`tools/tests/controller/Assets/config` **零 diff**（期间 9 笔均为账本代录、接受落实、派发登记）。
- 开轮资格：PLAY_GOVERNING（`tools/`、`tests/`）diff 非空 → 开轮。本停点 `REWORK_REQUIRED` 此前 1/2，本轮为 R3，不属冻结集/轮 3 终局情形（未发生第 2 次返工）。
- 停点自证（交接 §4）：①成立；②原「待用户决定」已由账本 2026-10-04「用户选 (a)：R2-1 窄修候选以 focused 加 R2-1 修前红/修后绿代替停点全套、SUB:6 两项例外读法沿用」授权范围 (1)(2)(3) 与接受「R2-1 窄修候选例外落实与 R3 交接」（AC-10 修订 11/12、AC-13 修订 5）落实——条目逐字存在、适用候选与本候选相同，本角色接受其进入复核（不记全套已跑）；③不适用；④齐。→ 不判 `REVIEW_BLOCKED`。
- 副本 `.claude/worktrees/review-P1-ENG-JET-001`（detach 于候选）；测试树哈希 `HEAD:tests = 140f0bf361c0bb7a0f0aaef398652eca30746214`，`HEAD:tools/eng_jet = 5ca8db78b4192191cc4d7c126f5c89deb8c780bb`；解释器 `.venv-yoloe/bin/python`（3.12.14，只读使用）；执行机 `zc5s-Mac-mini.local`。
- **focused 重跑**（副本内 `-m unittest discover -s tests -p 'test_eng_jet_*.py'`，输出写会话暂存目录）：**`Ran 83 tests` / `OK (skipped=1)`**，墙钟 44 s；跳过者为 `test_eng_jet_bench.InjectionOnly`（副本无 gitignored 冻结权重），与 R1/R2 相同；候选 `-R2rework-focused-tests.log` 为 `Ran 83 tests / OK` 无 skip（主树有权重），一致。副本 `git status --porcelain` 跑后为空。
- **R2-1 修前红/修后绿**（副本内 `git diff $PREV..$CAND -- tools/eng_jet/relay.py | git apply -R` 只回退 `relay.py` 修复、保留新测试 → 跑 → `git checkout -- tools/eng_jet/relay.py` 恢复）：红 = `test_adopt_during_return_send_keeps_new_link_dedup_clean` **FAIL**（`AssertionError: 'tracking_observation.json' unexpectedly found in {...'5275e4bc…'}`，即旧连接 digest 覆盖了 `adopt_link` 的清空，与 R2 探针及交接 §2 记录同形），同批 `test_reconnect_resends_current_return_version` 仍 OK；绿 = 恢复后两例 `Ran 2 tests / OK`。四条闭合条件：(1) fixture 为真实 `BoardRelay` 运行目录 + `write_bytes` 写回程文件（与既有用例同口径，无手写状态）；(2) 本轮红绿已核；(3) 不触及 Play 治理门；(4) 不适用（已机械断言）。

### §1 逐文件核对（修复触及行）

| 文件 | 结论 |
|---|---|
| `tools/eng_jet/relay.py::BoardRelay.return_once` | 采用 R2-1 闭合要求 (a)：`link.send` 返回后在 `_link_lock` 内判 `replaced = self.link is not link`，仅未替换时写 `_last_return[name] = digest`；替换时不写回、仍计 `returns_sent`/`sent`、收据加 `link_replaced: true`、随即 `break`（旧连接已关，余下文件留给下一轮新连接发）。未替换路径的行为、收据字段与补丁前逐字相同（`**extra` 为空）。`adopt_link` 在同一 `_link_lock` 内关旧连接、换 `self.link`、清两表，故「清空 → 旧轮次写回覆盖」交错已不可能。其余并发路径复核：快照后、`send` 前被 adopt → `Link.send` 持自锁判 `alive=False` 抛 `ConnectionError` → break，不写回，正确；`sendall` 中途被 `close` → `OSError` → `Link.close()` 并抛 → break，正确；`sendall` 成功后被 adopt → 本修复路径，正确。 |
| `tools/eng_jet/relay.py::BoardRelay.adopt_link` | 代码零改动，仅 docstring 补 R2-1 同锁说明，与实现一致。 |
| `tests/test_eng_jet_relay.py::BoardRelayInProcess::test_adopt_during_return_send_keeps_new_link_dedup_clean` | 连接替身 `AdoptOnSendLink.send` 在 `FakeLink.send` 返回前调用 `board.adopt_link(new)`，确定化「send 返回 → 换连接清表 → 写回」交错；断言覆盖：第一轮旧连接发 1 且 `old.alive=False`、`board.link is new`、`_last_return` 不含旧写回、第二轮新连接一轮内收到当前版本（路径+字节）并写入新 digest、第三轮 0、收据 `link_replaced` 依次 `[True, False]`。修前红已核（§0）。`board.receipts.close()` 后 `addCleanup` 再 close 为幂等（`_handle.close()` 重复调用无副作用）。 |
| 其余 6 路径（文档/日志/登记） | 交接「K1K3K4R2返工」§1–§6 与本轮 git 解析逐项相同（修改位置、红绿命令与断言文本、83/83、`PREV/PASSED/BASE` 规则）；状态板该轮改动为 Gate board 行与交接行 + 一条 Log；`-R2rework-focused-tests.log` 5 行 `Ran 83 tests / OK`；派发登记为 SUB6/C3/R2/R2返工 四次登记事件；提案与本文件改动来自 C3/R2 两笔具名提交。 |

### §2 AC 逐项（依据列 `BC-n` 读作 AC-n；未变化项沿 R2）

| AC | 结论 | 依据 |
|---|---|---|
| AC-1 / AC-2 / AC-3 | 沿 R1/R2（S0 `PASS`；S1/S2 `STOP` 不记满足） | 七份 JSON 相对 PASSED 零 diff。 |
| AC-4 / AC-5 | 沿 R2 成立 | `analyze` 对回程只按 `ev == "send_return"`（板侧，行 786）与 `recv_return and ok`（桌面侧，行 869）计数，不读新键 `link_replaced`；历史收据无此键，f2/f3/f4 读数不变。 |
| AC-6（修订 2） | **成立（R2-1 已闭合）** | §3.2「回程同理只发当前版本」与 `adopt_link` 文档「重连后重发每个回程文件的当前版本」在 R2 交错下现成立：清空与写回同锁、连接身份核对；红绿已核。f4 仍为补丁前历史实测、读数不变（本轮不改任何数字）。 |
| AC-7 / AC-8 / AC-9 | 不满足（`NOT_RUN(阶段 B 信封未签)`） | 三份 JSON 零 diff。 |
| AC-10（修订 9–12） | 成立 | 修订 11：focused 83/83 + R2-1 红绿代替本候选停点全套——证据 `-R2rework-focused-tests.log` 与本轮副本重跑一致；不记全套已跑。修订 12 / AC-13 修订 5：Carrier/scene006 例外沿用，本候选未重跑这两组，本轮不读作通过；`Assets/controller/config` diff 空。 |
| AC-11 / AC-12 | 沿 R2 成立 | `assets.py`、`BUNDLE_FILES` 相对 PREV 零 diff。 |
| AC-13（修订 4/5） | 成立 | 报告/读数相对 PREV 零 diff；无新 Jetson 主张。 |
| AC-14 | 成立（本候选 `UNITY_NA` 附议见 §4） | 交接 §3 解析可运行时复算，本轮已复算。 |
| AC-15 / AC-16 | 沿 R1 成立 | 零 diff。 |

### §3 Findings

无。修复触及行上无 CLASS_1/2，无 `RED_LINE`，无 `上轮漏检`，无 CLASS_3 补丁。R2-1 闭合（§0 红绿 + §1）；R1-1 的声明语义随 R2-1 闭合而闭合；R1-2/3/4 已于 R2 闭合；R1-5/R1-6 `SCOPE_GAP` 债不变（账本 OPEN，本轮不改判）。

### §4 UNITY_NA（本候选）

AC-14 对本候选申请 `UNITY_NA`。独立核实：`git diff --stat $BASE..$CAND -- Assets controller config` 为空；修复触及行仅 `tools/eng_jet/relay.py` 与 `tests/test_eng_jet_relay.py`，只改板侧回程去重写回判定与一条进程内回归，不触及 Unity 场景/脚本、文件桥字段、帧与控制协议；`-ledger.json` 相对 PREV 零 diff（`unity_play 0`、`scenario_session_run_ids 0`）；本轮零 Play。**复核附议本候选的 `UNITY_NA`**（仅限阶段 A 范围；本附议不等于阶段 A 验收）。

### §5 非 finding 观察（不阻断）

- 去重表读取 `self._last_return.get(name)` 仍在锁外（交接 §6 已披露）：可能的交错是 `adopt_link` 已把 `self.link` 换成新连接、尚未执行 `_last_return.clear()` 时，`return_once` 对新连接快照并读到旧 digest 而跳过该文件；随后清空生效，下一轮（`POLL_S = 0.005 s`）必发当前版本且写回。无版本丢失、无错误计数，只是该文件的首发最多迟一轮（≤ 5 ms）；「重连后重发每个回程文件的当前版本」仍成立，不列 finding。
- 替换时那次发送计入 `returns_sent` 并写 `send_return` 收据（R2 闭合要求 (a) 允许的「计入但注明」口径），与补丁前「`send_return` 表示已 `sendall` 而非对端已收」一致；分析器 `returns_received` 以桌面 `recv_return` 为准，不受影响。
- 修复未上板、未在真实断链/重连下运行；交错只由进程内替身确定化；f4 为补丁前实测——交接 §6 已披露，照旧携带。
- R2 §5 的 C3-P2/C3-P3 观察、Carrier/scene006 例外边界、NanoTrack/CSRT 上界、skip 聚合、`YOLO_OFFLINE` 未设、SUB:6 块手工追加等限制照旧携带；本候选全套层面回归未实测（用户具名例外下替代，不读作通过）。

### §6 Verdict

Verdict: PASS_WITH_NOTES

`R3@K1K3K4` 通过：R2-1（本停点唯一阻断 finding）修前红/修后绿已核、闭合四条成立；修复触及行无新 CLASS_1/2、无 `RED_LINE`、无 `上轮漏检`，不写 `blocks_consuming_gate`；本停点 `REWORK_REQUIRED` 终计 1/2。AC-7/8/9 `NOT_RUN(阶段 B 信封未签)` 不满足，S1/S2 `STOP` 不记满足，本候选停点全套按用户具名例外以 focused + 红绿代替、Carrier/scene006 例外沿用——本 verdict 是对候选（R1 补丁 + SUB:6 证据 + R2-1 窄修）的独立复核通过，**不是阶段 A 探测验收、不是 `DONE`、不推出任何 Jetson 性能或部署结论**；本候选 `UNITY_NA` 已附议（§4）。R1-5/R1-6 `SCOPE_GAP` 债不变。交接受角色消费（engineering-workflow §5/§11）；Overall 与 Lifecycle 由接受角色维护。

passed_candidate: 0e1c6cb5417bdd9c50564e56d9c7ad8ed48dfd06

边界自查：本会话未修改任何实现文件；主工作树只写本文件与状态板。副本内 `git apply -R` 回退仅用于红检并已 `git checkout` 恢复，测试输出在会话暂存目录，副本 `git status --porcelain` 为空，副本收工删除。
