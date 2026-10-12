# P1-ENG-FASTFIX-001 预检读数

依据：同名提案「D2 接受裁定」交接句与 §5.0「预检先行」、§8.2。本文只记读数，不改提案题面；与草案不符处列在各节「差异」，由 Acceptance 核清后更新题面。

## D2预检（2026-10-10，Implementation）

- 轮次 `D2预检`，Dispatch-Id `P1-ENG-FASTFIX-001-D2预检-20261010T230735Z-70e6`；实现角色（Opus 子代理），零消耗只读。
- 执行机：MacBook Air（仓库主树，派发基线 = 本提交的父提交）；Mac mini 经 `ssh macmini`（BatchMode，只读单条命令，一次连通，无重试）。
- 开始 2026-10-10T23:09:03Z（首个读数时刻）；结束 2026-10-10T23:12:41Z（自检通过、提交前）。
- 未做：导入项目代码、构造模型/跟踪器、加载权重、跑测试、回放、启动 Unity、传输/复制任何文件、下载/安装、`git fetch`（mini 上也未 fetch）、写 `outputs/`/`runtime/`。只用 `ls`/`du`/`df`/`shasum -a 256`/`git rev-parse|status|merge-base|rev-list|diff --stat`/`pgrep`/`lsof`，以及 `python3 -I` 只用标准库解析 JSON/JSONL 与读 `time.get_clock_info`。

### 1. Mac mini（阶段 A 依赖）

| 项 | 读数 | 命令 | 结论 |
|---|---|---|---|
| USER-4A 准入原件 | 根 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261008T213653Z/`（41,136 KiB）；`play/diag-loop2-214005/frames/` jpg 829、json 829、另 `latest.json`；`m3_body_truth.jsonl` 829 行；`replay-transfer/SHA256SUMS` 1,669 行，其中帧 jpg 829、帧 json 829 | `ls`/`grep -c`/`wc -l`/`du -sk` | 满足 |
| 现算 sha 对清单 | 1,669 行全部 `OK`，0 失败、0 缺文件（清单含权重与 board 日志等，故多于 1,659） | `shasum -a 256 -c replay-transfer/SHA256SUMS`（仓库根） | 满足 |
| 冻结权重 | `outputs/eng-det/runs/run-1/weights/last.pt` 5,458,330 B，sha256 `d6a0d6a9cdee06a0790f5d9812a1fe98db033520981c0ffafe786c3cbbe059c9`，与 `config/det-assoc-v1.models.json` `weights.sha256`/`size_bytes` 一致；该 config 文件 sha `76919cf7…` 与 Air 相同；freeze 文件 `docs/evidence/P1-ENG-FAST-002-freeze.json` 现算 `f231e450…c93c` = config `freeze.sha256` | `shasum -a 256`、`ls -l` | 满足 |
| `lap`（只看 dist-info，未构造） | 仓库 `.venv-yoloe`（Python 3.12.14）：lap 0.5.13、ultralytics 8.4.104、torch 2.13.0、numpy 2.5.3、opencv-python 5.0.0.93；数据根 `~/TetheredDroneTracking-full/.venv-yoloe`（python3.12）：lap 0.5.13、ultralytics 8.4.104、torch 2.13.0、numpy 2.5.1；`ENG_DET_DATA_ROOT` 在非交互 ssh shell 中未设 | `ls site-packages \| grep dist-info` | 包存在：满足；「可构造跟踪器」未验（按派发不构造） |
| 仓库 HEAD 与工作树 | mini `HEAD` = mini 本地 `origin/main` = `353812a…`（mini 未 fetch，本地远端引用陈旧）；`git status --porcelain` 空（干净）；该提交是 Air `origin/main`（派发基线 `b93003d…`）的祖先，落后 66 个提交；`git diff --stat 353812a b93003d -- controller tools tests config` 为空（落后部分只有文档） | `git rev-parse`/`status`；Air 上 `merge-base --is-ancestor`/`rev-list --count`/`diff --stat` | 干净：满足；落后 66：见差异 1 |
| 磁盘余量 | `/System/Volumes/Data` 可用 124,710,676 KiB（约 127.7 GB），已用 41% | `df -k` | 满足（对照阶段 A 新增 ≤2 GB） |
| 写者进程 | `pgrep -fl -i "unity\|python"` 无输出 | 同左 | 无写者 |

### 2. Air 运行时槽位、写者、残留、磁盘（阶段 B/C 依赖）

| 项 | 读数 | 命令 | 结论 |
|---|---|---|---|
| 写者进程 | 无 Unity、无 Python 进程；`lsof +D runtime` 只见本次只读 shell 自身 | `pgrep -fl -i unity`、`pgrep -fl -i python`、`ps`、`lsof +D` | 满足 |
| 帧桥活槽位 | `runtime/frames/` 不存在；`runtime/scenario_config.json` 不存在 | `ls -d` | 槽位空 |
| `runtime/` 残留 | 2026-10-10 17:21（CAPTURE formal-redo 收尾）遗留桥文件 8 个：`body_command.json`、`gimbal_command.json`、`tracking_observation.json`、`metrics.json`、`tracker_state.json`、`language_request.json`、`road_scene_audit.json`、`route_corridor_audit.json`；`runtime/runs/` 下 9 个当日 resident 目录（`capture-play-1-resident1…3`、`capture-formal-754e3a3f001f-resident1…3`、`capture-formal-d5a16e011762-resident1…3`）及 2 个 FRAME-001 目录；其余为 7–10 月历史 hold 目录/文件；`runtime/` 合计 5,827,904 KiB、98,542 个文件（gitignore `/runtime/*`） | `ls -la runtime`、`find -newermt`、`du -sk` | 有残留：见差异 2 |
| 磁盘余量 | 可用 14,873,268 KiB（约 15.2 GB），已用 93% | `df -k` | 满足（对照 B/C 各 ≤1 GB） |
| 解释器与权重（附带） | 仓库 `.venv-yoloe` Python 3.12.13：lap 0.5.13、ultralytics 8.4.104、torch 2.13.0、numpy 2.5.1、opencv-python 5.0.0.93；权重 sha 同 §1 | `ls site-packages`、`shasum -a 256` | 记读数；numpy/补丁版本与 mini 仓库 venv 不同，见差异 3 |

### 3. Air formal-redo 第 584–783 帧（AC-8 与 TX 依赖）

根 `outputs/eng-capture/formal-redo/`，会话 `capture-formal-d5a16e011762`；一次性只读脚本用 `python3 -I` 标准库解析（脚本在会话 scratchpad，未入仓）。

| 项 | 读数 | 结论 |
|---|---|---|
| 存在与连续 | `capture-formal-d5a16e011762/unity-runtime/frames/` 第 584–783 帧 jpg 200、json 200，无缺号；每个 json 的 `frame_id` 与文件号一致 | 满足 |
| 归档清单一致 | 400 个文件现算 sha 与 `FORMAL-REDO-SHA256SUMS.json` 及会话 `SHA256SUMS.json` 全部一致，无缺项 | 满足 |
| jpg 对收据 | 区间内收据 188 条（observation 64 / look_at 63 / body_command 61），`snapshot_sha256` 188/188 等于对应帧 jpg 现算 sha | 满足 |
| 元数据对 `frames_processed` | 区间相关 `frames_processed` 194 行，键 `at_monotonic_s`/`at_unix_s`/`frame_ids`/`raw_states`/`metadata_sha256` 齐全，三列表等长；覆盖 197/200 帧，`metadata_sha256` 全部等于帧 json 现算 sha、无空值、无重复覆盖；**第 648、649、650 帧不在任何 `frames_processed` 中** | 197 帧满足；3 帧见差异 4 |
| 点击 | 第 584 帧 `click_received` 恰 1 条，`frame_id`/`k`(=584)/`point`/`image_sha256` 齐全，`image_sha256` 等于第 584 帧 jpg sha | 满足 |
| 收据字段 | 顶层 `sequence`/`channel`/`outcome`/`frame_id`/`reason`/`at_monotonic_s`/`at_unix_s`/`detail` 188/188；`detail.load_elapsed_s`/`frame_delta`/`latest_frame_id`/`snapshot_sha256` 188/188；`capture_age_s` 187/188（缺的 1 条 = 第 647 帧 observation `PUBLISH_REJECTED`/`publish_expired`，seq 1330，`load_elapsed_s` 0.5450） | 时钟模拟所需字段齐；见差异 5 |
| 无收据帧 | 区间内 136 帧无任何收据（§3.8 按批内顺序推进的情形） | 记读数 |
| 体积 | 片段 jpg+json 7,871,315 B（约 39 KB/帧）；两份日志按区间取整行（`frames_processed` 194 行 + 第 584 帧点击 1 行 + 收据 188 行）171,422 B；合计 8,042,737 B（约 8.0 MB），字段抽取只会更小 | 满足（对照 TX ≤50 MB、Air 暂存 ≤50 MB） |
| 帧目录全貌（附带） | 帧目录 jpg 1,503 个，帧号 0–1641，区间外缺 139 个号；`latest.json` 指向第 2 帧、`published_unix_s` 1791667316.14 | 记读数，见差异 6 |

### 4. 同主机 monotonic 跨进程可比

- 系统事实：Air（macOS 26.6.2，arm64）系统 `python3` 3.14.6 与仓库 `.venv-yoloe` 3.12.13、mini（macOS 15.8）`.venv-yoloe` 3.12.14 的 `time.get_clock_info('monotonic')` 均为 `implementation='mach_absolute_time()'`、`adjustable=False`、分辨率 41.7 ns。`mach_absolute_time` 是本次开机以来的系统级时基，同主机各进程共用，不随墙钟调整（读法依据：CPython 对 macOS monotonic 的实现说明；未跑基准）。
- 存档旁证（只解析已有日志，未运行任何计时）：formal-redo 中 Unity 帧元数据 `capture_monotonic_clock_id = system-stopwatch/v1` 的 `capture_monotonic_s` 与会话进程收据 `at_monotonic_s` 之差，和对应 `capture_unix_s`/`at_unix_s` 之差相比，1,744 条收据的残差在 −1.2 ms 至 +0.5 ms（中位 −0.6 ms；`capture_unix_s` 只保留到毫秒）。即 Air 上 Unity 进程与 Python 会话进程的 monotonic 同基可比。
- 结论：满足（依系统事实与存档旁证）；计量工具进程与会话进程的重叠计法仍按 §8.2 在冒烟中以 unix 时间对照核。

### 差异与待 Acceptance 核清（不改提案正文）

1. **mini 仓库落后**：mini `HEAD` 落后 Air `origin/main` 66 个提交（只有文档差异，代码/工具/测试/配置无差异）。阶段 A 开工前需由执行者在 mini 上拉取到派发基线；预检未 fetch/pull。
2. **Air `runtime/` 残留**：帧槽与覆盖文件为空，但 CAPTURE 收尾遗留 8 个桥文件、当日 resident 目录与约 6.0 GB 历史 hold 目录。S-PRE 把「runtime 残留」列为不符条件，而草案未给残留判据（哪些文件必须不存在、是否先归档）；建议 Acceptance 在 B/C 操作单前置里写明判据。
3. **解释器差异**：Air 仓库 venv 为 Python 3.12.13、numpy 2.5.1；mini 仓库 venv 为 3.12.14、numpy 2.5.3（mini 数据根 venv 为 numpy 2.5.1）。ultralytics/torch/lap/opencv 版本一致。草案未要求两机逐版本一致，只记读数。
4. **第 648–650 帧无 `frames_processed`**：第 647 帧致命后拆载体，648、649 未被处理（会话帧环也无这两帧副本），650 为新载体 `resident_loop_started` 帧（会话日志第 1250 行）。三帧原件 jpg/json 存在且与两份归档清单一致。§3.8 写「缺任一帧或字段 → AC-8 `NOT_RUN`」，字面上这三帧的元数据无法与 `frames_processed.metadata_sha256` 对照；它们是重建间隙的结构性结果，而不是归档缺失。需要 Acceptance 裁定：按字面记 `NOT_RUN`，还是把「会话未处理的帧」按「无收据帧按批内顺序推进」处理、以归档清单 sha 代替对照。
5. **第 647 帧收据无 `capture_age_s`**：符合 F1 首命中顺序（`load_elapsed > t_pub_s` 先返回，未计算 capture_age）。§3.8 的时钟注入只用 `load_elapsed_s` 与 `latest_frame_id`（两者 188/188 齐全），但 F14 把 `capture_age_s` 列为抽取字段；需要确认该缺项不算「缺字段」。
6. **帧目录全貌与 F14 描述**：帧目录内 `latest.json` 指向第 2 帧，发布时刻晚于会话开始约 330 s（会话 299.9 s），区间外缺 139 个帧号；第 584–783 帧不受影响（sha 对两份清单与收据全部一致）。只记录，不推断原因。
7. **单帧体积**：实测约 39 KB/帧，低于 §5.1 TX 行「约 50 KB/帧」的估计；50 MB 上限有余量。

### 本轮实际耗用

- 墙钟：约 4 min 读数（23:09:03Z–23:12:41Z），另含开工读文档与提交推送时间。
- 新增磁盘：本证据文件（约 10 KB，git）与会话 scratchpad 中的一次性脚本和输出（约 10 KB，不入仓）。
- 模型加载、推理、测试、回放、Play、ID、API、传输、下载、安装、云：均为 0。ssh 只读连接 4 次，无重试。
