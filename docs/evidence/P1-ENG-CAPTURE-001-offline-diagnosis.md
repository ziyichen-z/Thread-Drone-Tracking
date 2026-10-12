# P1-ENG-CAPTURE-001 — 一次零消耗离线诊断（诊断，不进验收证据）

Owner: Air Implementation（supervisor 派发，Opus 子代理）；Dispatch-Id `P1-ENG-CAPTURE-001-离线诊断-20261010T214432Z-4102`。唯一合同：同名提案「收口与诊断落实（2026-10-10，Acceptance）」§2；资源与 STOP：同提案「诊断信封落实」§1–§2 及账本 2026-10-10 CAPTURE:DIAG:1。本文件只是下一轮修正的输入，不产本项 verdict/AC 证据，不改原失败、AC-23…26 缺项、R1-4/R2-2 OPEN 与旧资源偏差/UNKNOWN。

## 结论摘要（供用户阅读）

1. 正式重做「第一个拐角跟丢」与 publish_expired 在时间上重合：红车绑定后到第 647 帧，日志显示一直是「看得见、连续」（OBSERVED/SUPPORTED，无预测/疑似段）；第 647 帧这一帧处理了 0.545 s，超过发布时限 0.4 s（=2 帧/5 Hz），被判为协议错误，跟踪段直接终止。
2. 终止后系统进入「需重新指定」并取消任务，无人机原地悬停约 60 s（相机位置从第 650 帧到 952 帧不变）；原图上红车约在第 680 帧于路口右转驶离——用户看到的「拐角丢失」最可能是**一次处理超时导致主动撤权，然后不会自动找回**，而不是检测器在拐角看丢了车。
3. catchup_stale（重做第 980 帧、第三 Play 第 642/723 帧）是另一种表现：控制器连续多帧追不上 5 Hz（处理滞后 0.4–2 s），待发布帧比最新帧落后 3–4 帧，超过 2 帧上限即终止。
4. 确定程度：「拐角现象 = publish_expired 撤权 + 不自动恢复」为**日志已证的时序 + 原图支持，可信度高**；「为何偶发单帧超时/持续积压」只有假设（主机争用，如同机监控每 10 s 全量遍历约 14 万文件并写 17.7 MB 的 meter.json；或重建后处理变慢），日志无法定案。
5. 下一轮最该改：让单次发布超时/追帧过旧**不再直接终止并丢弃目标**——改为丢弃该帧发布、保持指针并在下一帧继续（或重建后自动以最后绑定重新捕获）；同时把 0.4 s 发布时限与实测处理尾部（p95 0.16–0.25 s、个别 0.5–0.8 s）一起重新核定，并把采集监控移出关键时序。

## 1. 输入来源、哈希核对与混存限制

入口：`docs/evidence/P1-ENG-CAPTURE-001-play.md` §0、`-formal-play.md` §0、`-formal-redo.md` §0–1。session 身份均按各自 `control/launch.json`（play 为会话目录）运行时解析，下文以 `${SID}` 指代，不手抄目录名/SHA。

| 原清单（Air 已保全） | 条目数 | 本次逐件流式 SHA-256 | 结论 |
|---|---|---|---|
| `outputs/eng-capture/formal-redo/FORMAL-REDO-SHA256SUMS.json` | 4533 | 4533 一致 / 0 不符 / 0 缺失 | 保全一致 |
| `outputs/eng-capture/formal-redo/${SID}/SHA256SUMS.json` | 4515 | 4515 / 0 / 0 | 保全一致 |
| `outputs/eng-capture/formal/FORMAL-SHA256SUMS.json` | 3409 | 3409 / 0 / 0 | 保全一致 |
| `outputs/eng-capture/formal/${SID}/SHA256SUMS.json` | 3393 | 3393 / 0 / 0 | 保全一致 |
| `outputs/eng-capture/play/${SID}/SHA256SUMS.json` | 2715 | 2715 / 0 / 0 | 保全一致（仅背景对照） |

无输入漂移/哈希不符。哈希一致只证保全一致，**不证正式源完整**。

**formal-redo 混存的帧级对应**（控制器 `frames_processed.metadata_sha256` 对 unity-runtime 非真值传感器旁车字节哈希）：控制器处理 1511 帧（2…1520）。第 142…1520 帧 1371 帧**可对应**；第 3…141 帧 139 帧**缺失**（旁车已被停止后的误触重启覆盖/不在）；第 2 帧**冲突**（现存为停止后新写的同号旁车）。本诊断涉及的全部关键时刻（第 274…1520 帧）都落在可对应区间。第三 Play（formal）717 帧全部可对应。真值文件（`m3_body_truth.jsonl`）只作为既有清单内的字节身份对象参与哈希核对，未打开解析。

## 2. 现象 A：正式重做「第一个拐角跟丢」时间线

来源：`formal-redo/sessions/${SID}/language-session.jsonl`（下称 journal）、`publish-receipts.jsonl`（下称 receipts）、unity-runtime 非真值旁车与原 RGB。t 为相对 session_started 的墙钟秒。

| t (s) | 帧 | 记录 | 读法 |
|---|---|---|---|
| 3.91 | 1 | resident_loop_started resident1（model_loads=1） | 常驻载体 1 |
| 54.69 | 274 | click_received → binding INITIAL → TRACKING | 原点击 1（预登记为静止车） |
| 116.79 | 584→585 | click_received → USER_RESELECT，旧段 superseded_by_click 退休 | 原点击 2（预登记为红车） |
| 116.95–117.58 | 586–589 | CONTROL_LIMITED ×4 | 新目标起步限速，正常 |
| 54.8–129.7 | 275–647 | 每帧 authorization：OBSERVED / SUPPORTED / geometry valid / covariance within / watchdog fresh / FOLLOW | **全段无预测、无疑似、无断续**；机体指令朝向约 89°、速度约 2 m/s 直行跟随（receipts body_command；相机位置 x 由 133→157.6 m） |
| 646→647 | 646 | 捕获→处理滞后 0.14 s；647 为 0.57 s | 第 630…645 帧滞后 0.04–0.07 s，**孤立单帧尖峰**，无积压批 |
| receipts | 647 | observation PUBLISH_REJECTED `publish_expired`，load_elapsed_s=0.545，frame_delta=2 | 代码 `controller/gated_publisher.py` `_gate` ⑤：load→publish 耗时 > t_pub_s；t_pub_s=K_PUB/hz=2/5=0.4 s（`controller/language_loop.py` K_PUB） |
| 129.67–129.81 | 647 | segment_retired / resident_loop_closed `publish_expired` → REINIT_REQUIRED | `language_bridge.PROTOCOL_ABORT_REASONS` 含 publish_expired；`language_loop` 发布门 seg_end → `_teardown_resident` 并进入 REINIT_REQUIRED |
| 130.30 | 650 | resident_loop_started resident2（rebuilds=1，model_loads 仍 1） | 载体重建，但**不恢复绑定** |
| 130.7–190.5 | 653–952 | authorization：task CANCELED / HOLD / NO_TASK | 无人机悬停：旁车相机位置第 650…952 帧恒为同一点（约 x=160.1 m） |
| — | 646 / 680 / 700 | 原 RGB 有限查看 3 帧 | 646：红车正驶入路口；680：红车已右转进入横街；700：红车继续驶离向画面右缘。画面中唯一的红色轿车（另有一辆红顶巴士），身份为外观判断，未用真值 |
| 190.49 | 952 | 原点击 3（预登记静止车）→ INITIAL | 此后进入现象 B 第二次 |

**读法**：用户所称「第一个拐角跟丢」与「第 647 帧发布超时 → 撤权 → 悬停不追」在时间和画面上重合；丢失前感知层没有任何丢失信号。第一个拐角处的发生顺序是**先撤权（647），后转弯（约 650–680）**，因此不是转弯导致检测丢失，而是转弯前一刻主动停追，车随后转出。

## 3. 现象 B：publish_expired / catchup_stale 触发驻留重建（分次）

触发条件（代码已证，`controller/gated_publisher.py` `_gate`）：① 待发布帧不是最近加载帧 → catchup_stale；④ latest.json 帧号 − 待发布帧号 > k_pub(2) → catchup_stale；⑤ 加载→发布耗时 > 0.4 s 或捕获墙钟年龄 > T_STALL_S(3.0 s) → publish_expired。任一命中即该段致命终止、驻留重建并要求重新点击；第 3 次需要重建时 `rebuild_limit` 终止会话。

| Play | 帧 | 原因 | 拒绝明细（receipts detail） | 前序处理滞后（捕获→处理） | 状态 |
|---|---|---|---|---|---|
| 第二 Play（背景） | 585 | publish_expired | load_elapsed 0.571 s，delta 2 | 未展开 | TRACKING |
| 第二 Play（背景） | 901 | publish_expired | load_elapsed 0.794 s，delta 0 | 未展开 | TRACKING |
| 第三 Play formal | 302 | publish_expired | load_elapsed 0.425 s，delta 2 | 前序 0.04–0.14 s，孤立尖峰 0.48 s | TRACKING |
| 第三 Play formal | 642 | catchup_stale | delta 3 | 第 603…642 帧持续 0.3–2.1 s，批量追帧（每批 2–6 帧） | TRACKING（绑定后约 9 s） |
| 第三 Play formal | 723 | catchup_stale → rebuild_limit | delta 3 | 第 720…723 帧 0.11–0.67 s | TRACKING |
| 正式重做 | 647 | publish_expired | 见现象 A | 孤立尖峰 | TRACKING |
| 正式重做 | 980 | catchup_stale | delta 4 | 第 953…980 帧中位 0.457 s、最大 1.19 s，每批 2 帧 | TRACKING（点击 3 后约 6 s） |

分段处理滞后（中位 / p95 / 最大，秒；第 142 帧前的重做旁车缺失不计）：

| 段 | 正式重做 | 第三 Play |
|---|---|---|
| 载体 1 空闲 | 0.045 / 0.087 / 0.438 | 0.040 / 3.203（启动）/ 4.401 |
| 载体 1 跟踪 | 0.088 / 0.239 / 0.905 | 0.049 / 0.144 / 0.483 |
| 载体 2 待重指定 | 0.126 / 0.641 / 1.780 | 0.056 / 0.146 / 0.575 |
| 载体 2 跟踪 | 0.457 / 0.993 / 1.188 | 0.808 / 1.925 / 2.123 |
| 载体 3 待重指定 | 0.131 / 0.300 / 0.999 | 0.186 / 0.390 / 0.592 |
| 载体 3 跟踪 | 0.131 / 0.310 / 1.055 | 0.194 / 0.635 / 0.673 |

已写出的发布（重做 1742 条 / 第三 Play 488 条）load_elapsed 中位 0.088 / 0.035 s、p95 0.16 / 0.18 s、最大 0.332 / 0.327 s；全部 6 次致命拒绝都在 TRACKING 中、都只超出门值一个尾部量级（0.425–0.794 s 或 delta 3–4）。

## 4. 各解释的支持 / 反证

| 编号 | 解释 | 级别 | 支持 | 反证 / 缺口 |
|---|---|---|---|---|
| E1 | 拐角丢失 = 第 647 帧 publish_expired 撤权 + 重建后不自动恢复绑定 | **日志已证时序 + 原图支持** | §2 时间线；authorization 全段 OBSERVED；相机 650…952 不动；原图 646/680/700 红车转出 | 用户主观「拐角」时刻无逐帧记录；红车身份按外观判断，未用真值 |
| E2 | 单帧发布超时/追帧过旧被当作协议错误、一次即致命，是把短暂延迟放大成整段丢失的机制 | **代码已证** | `PROTOCOL_ABORT_REASONS` 含两原因；`_gate` 一次命中即 `_set_fatal`；`_teardown_resident` 后 REINIT_REQUIRED，capture 模式无自动重捕 | 该严格性是 AC-3 合同设计选择，本诊断不判断其应否放宽 |
| E3 | 0.4 s 发布时限与本机处理尾部过近 | 可支持解释 | 写出发布 p95 0.16–0.18 s、最大 0.33 s，致命值 0.43–0.79 s；三次 Play 共 6 次全部是尾部越线 | 门值来自 K_PUB 常量，非本机实测标定；是否该调需新验证 |
| E4 | 偶发尖峰来自同机争用（采集监控每 10 s `os.walk` 约 14.2 万路径并写约 17.7 MB `meter.json`，nice 10） | 待验证假设 | `formal-redo/companion-source.py` 循环；meter.json 实际 17,706,844 B、per_path 141,865 项 | 监控未记每次采样时刻，无法与 302/647 等尖峰对齐；也可能是 GC/推理尾部 |
| E5 | 重建后跟踪段处理变慢（载体 2 跟踪滞后中位 0.46/0.81 s，明显高于载体 1） | 待验证假设 | §3 分段表两次正式 Play 同向 | 载体 3 跟踪又回落；重做载体 2 待重指定已偏慢；`_teardown_resident` 未见明显资源泄漏，原因未知 |
| E6 | 检测器/关联在拐角失配导致丢失 | **反证占优** | — | 647 前无 PREDICTED/SUSPECTED/continuity 异常；撤权先于转弯 |

## 5. 无法核定项

- 用户口中「第一个拐角」的精确帧与第二次（第 952 帧后）跟随中的主观体验，无逐帧记录；只能以原图车辆外观对应，**UNKNOWN 级身份**。
- 不读真值，无法定量红车与画面/无人机的实际距离及是否短暂遮挡；遮挡 vs 身份丢失的区分本次未需要（E6 已由日志排除感知丢失），但若下一轮要量化跟随误差，需另定真值只读口径。
- E4/E5 的根因（尖峰与积压来源）在现有记录中不可定案：缺采样时刻、缺逐阶段（解码/推理/关联/写盘）耗时。
- formal-redo 第 3…141 帧旁车缺失、第 2 帧冲突，早期 IDLE 段无法逐帧对应；不影响上述关键时刻。
- 第二 Play 两次 publish_expired 只列门值明细，未展开时间线（背景对照，不扩成新实验）。

## 6. 下一轮最小修正建议与需新验证项（仅建议）

1. **发布门失败降级为丢帧而非终止**：单帧 publish_expired / catchup_stale 只拒发该帧并撤一帧控制（或进入短暂 HOLD），指针与跟踪核保留，下一帧可发布即恢复；连续 N 帧失败才终止。需新验证：构造延迟注入（单帧 0.6 s、连续 3 帧积压）下不丢指针、HOLD/恢复帧数在报告预算内。
2. **重建后自动以最后绑定重新捕获**：若仍需重建，用最后确认的框/轨迹在新载体上 re-acquire，而不是要求用户重点；需验证重捕身份正确率与失败报告。
3. **门值重标定**：以本机实测处理分布重定 t_pub（或改为按帧龄而非加载→发布耗时），并把追帧上限与静音追平策略一起评估。需新验证：Air 实测处理时延分布与门值余量。
4. **采集监控移出关键时序**：磁盘计量改为低频/增量或在独立进程低优先级且不写巨型 JSON；同时为每次采样记时间戳，便于与尖峰对齐。需新验证：开/关监控对比的处理尾部。
5. **补逐阶段耗时日志**：每帧记录解码、推理、关联、发布各段耗时，用于定案 E4/E5。

以上均需另定范围与逐维信封；本诊断不修代码、不再 Play、不反调本项冻结参数/帧集/判据。

## 7. 本次实际资源与计量方法

- 起始：2026-10-10T21:44:48Z（unix 1791668682，开工第一步记录）；结束与总墙钟见本节末「收尾实测」行（提交前最后一次填写；提交/推送本身耗时含在 Acceptance 核对时可由 git 提交时刻复核）。
- 磁盘计量方法：开工基线 `.git` 12,097,980 KiB、项目 transcript 目录 707,936 KiB（与其他会话共用，不作本项基线）。本次可归属新增分配块 = 本报告文件分配块 + 本次提交新增 git 对象分配块 + 本子代理 transcript（`subagents/agent-ad003656e95bca0fd.jsonl`）及 tool-results 增量 + zsh heredoc 临时文件（每个 ≤ 8 KiB，命令结束即删，按并发最多 1 个计）。分析脚本全部经 stdin 送入 `python3 -I -`，不写 .pyc、不落盘；未复制原件、未导帧、未写 runtime/ 或 outputs/。删除不返还。
- 收尾实测（提交前 2026-10-10T21:49:55Z，unix 1791668995）：已用墙钟 313 s（≤1,800 s）；可归属新增分配块：子代理 transcript 1,792 KiB + meta 8 KiB + tool-results 72 KiB + 本报告 32 KiB = 1,904 KiB（约 1.95 MB）；`docs/current-status.md` 为原地改写，不新增分配块（仅瞬时，按 ≤ 408 KiB 保守计入）；本次提交新增 git 松散对象按 ≤ 512 KiB 预留（状态板 blob gzip 约 71 KiB + 报告 blob + 树/提交对象，每对象 ≥ 4 KiB 块）。保守峰值 ≤ 1,904 + 408 + 512 + 64（heredoc 临时与 transcript 后续增长余量外另计）≈ 2.9 MB，远低于 100,000,000 B。提交/推送后的最终墙钟与 transcript 增量由接力报告补记，属本文件写定后的实测，**不在本文件内预填**。
- UNKNOWN：Claude 客户端在 `~/.claude` 以外的缓存/日志（如应用级日志）不可逐项归属，未计入；以上为可观测归属块的保守值，不声称完整客户端峰值。

## 8. 禁止动作未执行声明

本次未加载/推理任何模型；未 Unity/Play；未创建/消耗 scenario/session/run ID；API/云/GPU/板端/其他设备/下载/安装/原件传输均 0；未改代码/配置/测试/原件/原清单/runtime/outputs；未运行测试、正式评分、analyze_play.main、score_*、replay、reducer、KF 或跟踪器；未导入 controller 或模型包（只用 grep/sed 读源码文本）；未语义读取真值文件；未保存可复用分析工具；未筛最佳段补正式结果。原失败、AC-23…26 缺项、R1-4/R2-2 OPEN 与全部旧资源偏差/UNKNOWN 保持不变。
