# P1-ENG-CAPTURE-001 — 阶段 A 离线回放证据（AC-17/18/19/28；候选 2 正式回放，C1返工）

- 轮次：`C1返工`（Dispatch-Id `P1-ENG-CAPTURE-001-C1返工-20261010T022016Z-8465`），实现角色，Mac mini，`.venv-yoloe/bin/python`，进程设 `YOLO_OFFLINE=True`、`YOLO_AUTOINSTALL=False`。
- 命令：`.venv-yoloe/bin/python -m tools.eng_capture.replay run --fidelity-confirmation docs/evidence/P1-ENG-CAPTURE-001-fidelity-confirmation.json --click-script outputs/eng-capture/fidelity/user/click-script.json --roll-click-script outputs/eng-capture/roll-clicks/user/roll-click-script.json --candidate 2`；暂定读数另由零模型 `replay rescore --run-dir <输出目录>` 生成。
- 运行代码：候选 2 = C1返工首个提交 `9bb0430`（启动时 `git rev-parse HEAD` 与空的 `git status --porcelain` 记于 `outputs/eng-capture/replay/candidate2-launch.txt`）。
- 产物（mini 本机，不入仓）：`outputs/eng-capture/replay/candidate2-20261010T024317Z/`；sha256：`replay-report.json` b1e3c310…、`new-arm.json` 40e57528…、`baseline-arm.json` 962d2a2b…（与候选 1 逐字节相同：基线源与 per_class 检测确定）、`new-arm-tm_inputs.jsonl` 709756a3…、`input-check.json` a71d61ba…、`provisional-readings.json` ef4a14b2…（完整值 `shasum -a 256` 现算）。
- 资源：本次加载 1（尝试前记账）、推理 3,962 帧（原始 829 × 2 策略 = 1,658 + 合成两臂 2,304；C1-5 逐帧提交前落盘、两阶段各结算一次）、墙钟 146.18 s（`/usr/bin/time -l` real；最大常驻 963 MB）。候选 2 回放加载 1/2、推理 3,962/5,500；整批加载 3/6、推理 7,924/16,500。
- 零模型核验：只读 `new-arm-tm_inputs.jsonl` 与配置在新进程重放（`python -m controller.target_manager replay …`）退出 0、837 条事件（AC-15 生产路径工件可重放；逐条比对口径见 AC-15 具名测试）。
- **R1返工（候选 3）未重跑正式回放**：候选 3 相对候选 2 的代码改动不触及本文件读数所经的计算路径（判定与零模型核验见 `docs/evidence/P1-ENG-CAPTURE-001-K1K2K3K4-handoff.md` §R3）；本文件 §0–§5 读数仍是候选 2 正式回放的读数，§4 判据句已按复核 CLASS_3 逐字替换。
- 候选 1 的原读数原文保留在文末附录（C1@K1K2K3K4 不采纳其 AC-17 PASS；AC-18 判据有误；原工件不改、不补写）。

## 0. 前置（启动前均已核过，任一不符即拒绝启动）

| 前置 | 结果 |
|---|---|
| AC-27 保真确认 | 确认文件 6 张样帧 sha 现核一致（用户 `consistent`，账本 2026-10-10 条） |
| AC-17 剧本 | `click-script.json` sha256 956a387f…，与确认记录及账本一致；static_car 243 帧、red_car 557 帧 |
| AC-28 六基剧本 | `roll-click-script.json` sha256 4ca6eae2…，plan_sha256 5d40e321…；规则现算六基 k = 26、44、63、547、566、584，点击帧 k−1 字节 sha 逐个一致 |
| S-A-INPUT | 1,659 个文件现算 sha 与 `SHA256SUMS` 全部一致，829 帧帧时刻与真值对齐（`input-check.json` `ok: true`） |
| 账本启动门（C1-5） | `ledger check --candidate 2 --need replay_yolo_loads=1 --need replay_inference_frames=3962 --need mini_new_disk_bytes=0` 全 true（整体校验、候选 2 归因、零维度、无 in_flight）；运行中逐帧落盘、30 min 墙钟门 |
| 基线源 | 接受裁定提交 `controller/` 与 F18 Play 代码提交逐字节等价（运行时 git 解析，`replay-report.json` `baseline_source`） |

## 1. AC-17 基线臂与现象门

基线臂（导出的基线源、`per_class` + `pose`）：243 帧 static_car → BOUND（库键 3）；557 帧 red_car → BOUND（库键 11）。558–560 指针 ok，**561–567 指针非 ok（`bound_track_unmatched`）**。现象门（559–565 内至少一帧指针非 ok 且真值可见）：命中 561–565 → **reproduced = true**，不触发 S-A-REPRO。

## 2. AC-17 新臂逐帧判据（RR-1 用户答：修顺序，按提交后状态/效果判）

新臂（`unify_vehicle` + `pose-center` + 目标管理器，同一剧本）按 §3.3 ①→⑤：点击帧先提交替换请求，再对该帧授权与产生效果。243 帧 static_car → BOUND（库键 3，episode 1，INITIAL）；557 帧 red_car → BOUND（库键 11，episode 2，USER_RESELECT）。

**557 帧（提交帧）记录与效果同属新绑定**：库键 11、episode 2、OBSERVED/SUPPORTED、记录 version 2 = 效果 version 2、授权行 6、FOLLOW + 观测云台瞄新绑定框中心 (370.3, 279.9) px（静止车在 556 帧的瞄准中心为 (319.7, 182.9) px）。不再另存 `pre_click`。

**判据结果：PASS**。557–600 真值可见帧 44 帧全部 OBSERVED 且绑定框与真值 IoU ≥ 0.5（最小 0.761）；状态/效果不一致帧 0、TENTATIVE 窗口帧 0、BROKEN 0、误绑 0。评分器要求每帧效果与记录同帧、同版本，否则记 `STATE_EFFECT_INCONSISTENT`（不判通过）。

## 3. AC-17 另报暂定读数（不是门；占位参数下，均带 n；口径 RR-3 已获接受为暂定描述）

| 读数 | 值 |
|---|---|
| R-1 生存下界（本组样本暂定描述，不是概率生存界） | ≥ 6 帧（n = 4 个可评缺口：m=1 IoU 0.838、m=2 0.837、m=4 0.844、m=6 0.804，均 PASS；按 C1-2 恢复后的 AC-18 原检测判据重算） |
| 两种量测点水平残差（557–600 OBSERVED 且本帧观测效果的帧，n = 44） | 云台瞄准点 P_center：中位 0.042 m、均值 0.368 m、最大 2.319 m；框底中点射线 ∩ 地面：中位 2.224 m、均值 2.213 m、最大 2.263 m（真值只进 `score_`） |
| 误 TENTATIVE（真值仍可见时进入窗口的代理计数，不是身份误判率） | 全程进入 TENTATIVE 1 次（602 帧，其后 606 帧 BROKEN），进入帧真值框不可见 → 0（n = 1 次进入）；557–600 窗口内 TENTATIVE 帧 0（n = 44） |

## 4. AC-18 故障注入（新臂检测缓存，零推理；C1-2 恢复原文判据）

判据：**下一次真实观测 = 缺口后 T_repair 帧内首个与真值 IoU ≥ 0.5 的策略后原始检测**（不要求被接受为 OBSERVED，BROKEN 不表示检测不存在）；**预测框 = 注入前原绑定键（库键 11）在该帧的同帧 prior**（修复后也不换为新键 prior）；IoU ≥ 0.3 PASS、< 0.3 FAIL；无此检测 → NOT_EVALUABLE；原键无同帧 prior → 记证据缺失（`original_key_same_frame_prior_missing`，不从分母去掉、不计通过）。逐注入的评分窗口逐帧记录（原始检测、各键同帧 prior、绑定与效果）落盘在 `replay-report.json` 各注入项 `frames`，可只读复算。

| 注入 | 行 7 成立帧 / 均有预测 look_at | 预测 IoU（下一真实观测帧、检测与真值 IoU） | 不续跟（到期后原 ID 重现） | 修复 | 报告 `no_new_observation` / BROKEN |
|---|---|---|---|---|---|
| 删红车检测 m=1（auto_repair on） | [561] / 是 | **PASS** 0.838（562，0.958） | 是 | 无（原 ID 562 回 SUPPORTED） | 604 / 606（602 起红车真值不可见之后） |
| m=1 off | 同上 | PASS 0.838 | 是 | — | 同上 |
| m=2 on | [561, 562] / 是 | **PASS** 0.837（563，0.972） | 是 | 无 | 604 / 606 |
| m=2 off | 同上 | PASS 0.837 | 是 | — | 同上 |
| m=4 on | [561–564] / 是 | **PASS** 0.844（565，0.972） | 是（565 先到期，原 ID 565 重现不续跟） | 无 | 563（age 3 = T_report）/ 565（age 5 = T_repair） |
| m=4 off | 同上 | PASS 0.844 | 是 | — | 同上 |
| m=6 on | [561–564] / 是 | **PASS** 0.804（567，0.977） | 是 | 无 | 563 / 565 |
| m=6 off | 同上 | PASS 0.804 | 是 | — | 同上 |
| 强制对目标开新轨迹（561–562 排除原键 11） | [561] / 是 | **PASS** 0.837（563，0.972；预测框为原键 11 的同帧 prior） | 是 | 562、564（CONTINUITY_REPAIR，键 13） | 604 / 606 |

- 分列：**注入成立**（IR-8）——`INJECTED`：561、562 两帧原键 11 lost、同帧 prior 在；原匹配检测（索引 0）由新库键 13 接走，13 随后活跃 tracked；注入退出后不再排除。**不续跟**：凡有 BROKEN 的注入，其后各帧均 BROKEN 且无 FOLLOW。**预测 IoU**：九项全部可评、全部 PASS。
- 与候选 1 的差异：候选 1 以被接受的 OBSERVED 作下一观测、并在修复后取新键 prior，m=4/6 因此记 NOT_EVALUABLE；该判据经 C1-2 认定不符 AC-18 原文，候选 1 读数作废、原文保留在附录。
- auto_repair off 对照：四种删检测在 on 臂也未发生修复（原 ID 回来或到期），on/off 读数相同；只报告不修复的对照成立。

## 5. AC-19 合成滚转（AC-28 六基预登记点击）

六基 k = 26、44、63、547、566、584（点击帧 25、43、62、546、565、583，用户本人登记；两臂、每基 12 种滚转复用同一点）。72 序列 × 两臂，每臂 1,152 推理帧；72 个序列全部可评，每格 n = 12。

| ω（°/帧） | Θ | 基线臂断轨 / n（率，Wilson 95%） | 新臂断轨 / n（率，Wilson 95%） | 新 ≤ 基线 |
|---|---|---|---|---|
| 15 | 60° | 3/12（0.25，0.089–0.532） | 2/12（0.167，0.047–0.448） | 是 |
| 15 | 120° | 6/12（0.50，0.254–0.746） | 3/12（0.25，0.089–0.532） | 是 |
| 20 | 60° | 5/12（0.417，0.193–0.680） | 2/12（0.167，0.047–0.448） | 是 |
| 20 | 120° | 8/12（0.667，0.391–0.862） | 3/12（0.25，0.089–0.532） | 是 |
| 25 | 60° | 4/12（0.333，0.138–0.609） | 2/12（0.167，0.047–0.448） | 是 |
| 25 | 120° | 8/12（0.667，0.391–0.862） | 3/12（0.25，0.089–0.532） | 是 |

- 判据（只作非劣化、不声称阈值）：**六格新臂断轨率均 ≤ 基线臂**；区间均重叠，n = 12，不作优于主张。
- 误跟（计入断轨、单列）：基线臂 16 序列，新臂 12 序列；右删失缺口：基线 14、新臂 19。按基分（基线 / 新臂断轨序列数，每基 12）：26 → 12 / 12；44 → 6 / 0；63 → 4 / 0；547 → 8 / 0；566 → 0 / 0；584 → 4 / 3（合计 34 / 15）。读数与候选 1 相同（点击帧 ①→⑤ 顺序只改变不计分的热身末帧效果）。
- 基 26 两臂 12 序列全断轨，原因未分析，只保留为限制；不增基帧、不设优越性门（预复核关注项）。
- 设备说明：原始帧缓存在 MPS 上推理（规格 `device_policy` 首选 mps）；合成帧 live 推理经同一已加载模型，两臂相同。

## 6. 限制

- 全部读数只说明本仿真、5 Hz、现行检测器与 BoT-SORT 冻结参数、本组占位参数（T_pred 4、T_repair 5 等待标定值）下的工程行为；单次回放，不是统计结论。
- 不读旧会话日志、`frames.jsonl`、RECHARTER 导出或其读数；准入原件只作本项离线回归夹具。

## 附录：候选 1 正式回放原读数（保留原文；C1@K1K2K3K4 退回，AC-17 PASS 不采纳、AC-18 判据不符原文）


- 轮次：`阶段A回放`（Dispatch-Id `P1-ENG-CAPTURE-001-阶段A回放-20261010T012252Z-5d32`），实现角色，Mac mini，`.venv-yoloe/bin/python`，进程设 `YOLO_OFFLINE=True`、`YOLO_AUTOINSTALL=False`。
- 命令：`.venv-yoloe/bin/python -m tools.eng_capture.replay run --fidelity-confirmation docs/evidence/P1-ENG-CAPTURE-001-fidelity-confirmation.json --click-script outputs/eng-capture/fidelity/user/click-script.json --roll-click-script outputs/eng-capture/roll-clicks/user/roll-click-script.json --candidate 1`；暂定读数另由零模型 `replay rescore --run-dir <输出目录>` 生成。
- 运行代码：提交 `a1e4eb7`（回放引擎、新臂、评分在其后未改；之后的 `2d12c50` 只加零模型 `rescore` 与测试夹具修正）。启动时 `git status --porcelain` 为空（`outputs/eng-capture/replay/candidate1-launch.txt`）。
- 产物（mini 本机，不入仓）：`outputs/eng-capture/replay/candidate1-20261010T013055Z/`；sha256：`replay-report.json` 9272d32d…、`new-arm.json` 4fb216a9…、`baseline-arm.json` 962d2a2b…、`new-arm-tm_inputs.jsonl` 5e623f2e…、`input-check.json` a71d61ba…、`provisional-readings.json` 04a77b65…（完整值 `shasum -a 256` 现算）。
- 资源：本次加载 1、推理 3,962 帧（原始 829 × 2 策略 = 1,658 + 合成两臂 2,304）、墙钟 137.7 s。此前 01:28:31Z 一次启动加载在 ultralytics 内被拒（规格 JSON 当权重，`TypeError`，未得模型、推理 0），按「尝试即记」已计；候选 1 回放加载累计 **2/2**，本候选不再有回放加载余额。

### 候选1 0. 前置（启动前均已核过，任一不符即拒绝启动）

| 前置 | 结果 |
|---|---|
| AC-27 保真确认 | 确认文件 6 张样帧 sha 现核一致（用户 `consistent`，账本 2026-10-10 条） |
| AC-17 剧本 | `click-script.json` sha256 956a387f…，与确认记录及账本一致；static_car 243 帧、red_car 557 帧 |
| AC-28 六基剧本 | `roll-click-script.json` sha256 4ca6eae2…，plan_sha256 5d40e321…，与账本 2026-10-10 条一致；按规则现算的六基 k = 26、44、63、547、566、584，点击帧 k−1 字节 sha 逐个与原帧现算值一致 |
| S-A-INPUT | 1,659 个文件（829 jpg + 829 json + 真值）现算 sha 与 `SHA256SUMS` 全部一致，帧旁车 `frame_id`/`simulation_time_s` 与真值 829 行全部对齐（`input-check.json` `ok: true`） |
| 账本余额 | 启动前逐维核过（回放加载、推理帧、磁盘）；墙钟另记 |
| 基线源 | 接受裁定提交 `controller/` 与 F18 Play 代码提交逐字节等价（运行时 git 解析，`replay-report.json` `baseline_source`） |

### 候选1 1. AC-17 基线臂与现象门

基线臂（导出的基线源、`per_class` + `pose`，点击点在 k 帧包含框作 `designate` 输入，检测来自本次 per_class 缓存）：243 帧 static_car → BOUND（库键 3）；557 帧 red_car → BOUND（库键 11）。558–560 指针 ok，**561–566 指针非 ok（`bound_track_unmatched`）**。

现象门（559–565 内至少一帧指针非 ok 且真值可见）：命中 561、562、563、564、565 → **reproduced = true**，不触发 S-A-REPRO。

### 候选1 2. AC-17 新臂逐帧判据

新臂（`unify_vehicle` + `pose-center` + 目标管理器，同一剧本）：243 帧 static_car → BOUND（库键 3，episode 1）；557 帧 red_car → BOUND（库键 11，episode 2，USER_RESELECT）。

**判据结果：PASS**。557–600 真值可见帧 44 帧全部 OBSERVED 且绑定框与真值 IoU ≥ 0.5（最小 IoU 0.761）；TENTATIVE 窗口帧 0、BROKEN 0、误绑 0。

**须接受角色裁定的读法（实现读法 RR-1，见交接证据 §5）**：557 帧是 red_car 点击的提交帧（管理器置 t0 = 557、OBSERVED）。本轮在正式回放前修正了新臂逐帧记录——点击提交帧的记录取提交后的帧末状态，提交前状态存 `pre_click`。若按修正前的记录（提交前状态）判 557 帧，该帧是旧 episode 的静止车观测（库键 3，OBSERVED/SUPPORTED），与红车真值 IoU < 0.5 → 记误绑 1 帧，AC-17 为 FAIL。558–600 两种读法相同（43 帧全部通过）。

### 候选1 3. AC-17 另报暂定读数（不是门；占位参数下，均带 n）

| 读数 | 值 |
|---|---|
| R-1 生存下界 | ≥ 2 帧（暂定，n = 2 个可评缺口：m=1 预测框对下一观测 IoU 0.869、m=2 IoU 0.858；m=4、m=6 不可评，见 §4） |
| 两种量测点水平残差（557–600 OBSERVED 且本帧观测效果的帧，n = 43） | 云台瞄准点 P_center：中位 0.043 m、均值 0.376 m、最大 2.319 m；框底中点射线 ∩ 地面：中位 2.224 m、均值 2.214 m、最大 2.263 m（真值 = `m3_body_truth` 目标世界位置，只进 `score_`） |
| 误 TENTATIVE | 全程进入 TENTATIVE 1 次（602 帧，其后 606 帧 BROKEN），进入帧真值框不可见 → 误 TENTATIVE 0（n = 1 次进入）；557–600 窗口内 TENTATIVE 帧 0（n = 44） |

口径定义见 `tools/eng_capture/replay.py::score_provisional_readings`（本轮补，零模型读已落盘记录；口径属实现读法 RR-3，见交接证据 §5）。

### 候选1 4. AC-18 故障注入（新臂检测缓存，零推理）

| 注入 | 行 7 成立帧 / 均有预测 look_at | IoU 判定 | 修复 | 报告（`no_new_observation`）/ BROKEN |
|---|---|---|---|---|
| 删红车检测 m=1（auto_repair on） | [561] / 是 | **PASS**（IoU 0.869，下一观测 562） | 无（原 ID 562 回 SUPPORTED） | 无本窗口报告（604 / 606 在 602 起红车真值不可见之后） |
| m=1 auto_repair off | 同上 | PASS（0.869） | — | 同上 |
| m=2 on | [561, 562] / 是 | **PASS**（0.858，下一观测 563） | 无 | 同上 |
| m=2 off | 同上 | PASS（0.858） | — | 同上 |
| m=4 on | [561–564] / 是 | **NOT_EVALUABLE**（缺口后 T_repair 内无真实观测） | 无 | 563（age 3 = T_report）/ 565（age 5 = T_repair） |
| m=4 off | 同上 | NOT_EVALUABLE | — | 同上 |
| m=6 on | [561–564] / 是 | **NOT_EVALUABLE** | 无 | 563 / 565 |
| m=6 off | 同上 | NOT_EVALUABLE | — | 同上 |
| 强制对目标开新轨迹（561–562 排除原键 11） | [561] / 是 | **PASS**（0.975，下一观测 564） | 562、564（CONTINUITY_REPAIR） | 无本窗口报告 |

- m=4、m=6 不可评的机制：原检测最早在 565 帧回来，此时 age = 5 = T_repair，到期先于同帧证据（§3.3 ②），原 ID 不续跟、BROKEN；这同时满足「age ≥ T_repair 后原 ID 重现不续跟」。T_report/T_repair 均准时（563、565）。按 AC-18 原文 NOT_EVALUABLE 不计通过。
- 强制开新轨迹（IR-8）：**注入成立**（`INJECTED`）——561、562 两帧原键 11 状态 lost、同帧 prior 在；原匹配检测（索引 0）由新库键 13 接走，13 随后成为活跃 tracked；注入退出后不再排除。
- auto_repair off 对照：m=1/2/4/6 四种删检测注入在 on 臂也未发生修复（原 ID 回来或到期），故 on/off 读数相同；只报告不修复的对照成立。

### 候选1 5. AC-19 合成滚转（AC-28 六基预登记点击）

六基 k = 26、44、63、547、566、584（点击帧 25、43、62、546、565、583，用户本人登记；两臂、每基 12 种滚转复用同一点）。72 序列 × 两臂，每臂 1,152 推理帧；每格分母 = 热身与旋转首帧均未删失的序列数（本次 72 个序列全部可评，每格 n = 12）。

| ω（°/帧） | Θ | 基线臂断轨 / n（率，Wilson 95%） | 新臂断轨 / n（率，Wilson 95%） | 新 ≤ 基线 |
|---|---|---|---|---|
| 15 | 60° | 3/12（0.25，0.089–0.532） | 2/12（0.167，0.047–0.448） | 是 |
| 15 | 120° | 6/12（0.50，0.254–0.746） | 3/12（0.25，0.089–0.532） | 是 |
| 20 | 60° | 5/12（0.417，0.193–0.680） | 2/12（0.167，0.047–0.448） | 是 |
| 20 | 120° | 8/12（0.667，0.391–0.862） | 3/12（0.25，0.089–0.532） | 是 |
| 25 | 60° | 4/12（0.333，0.138–0.609） | 2/12（0.167，0.047–0.448） | 是 |
| 25 | 120° | 8/12（0.667，0.391–0.862） | 3/12（0.25，0.089–0.532） | 是 |

- 判据（非劣化，只作非劣化、不声称阈值）：**六格新臂断轨率均 ≤ 基线臂**。区间均重叠，n = 12，不作优于主张。
- 误跟（计入断轨、单列）：基线臂 16 序列，新臂 12 序列；右删失缺口：基线 14、新臂 19。
- 按基分（基线 / 新臂断轨序列数，每基 12）：26 → 12 / 12；44 → 6 / 0；63 → 4 / 0；547 → 8 / 0；566 → 0 / 0；584 → 4 / 3（合计 34 / 15）。
- 评分口径冻结在 AC-19 原文：真值中心 = H(真值框中心)、真值多边形 = 四角经 H、画内面积 < 50% 删失、断轨 = 未删失帧上连续 ≥ T_repair 帧无有效观测或任一有效观测帧不在目标上。真值只进 `score_` 函数与基帧选择，不生成选择输入（AC-16/28）。
- 设备说明：原始帧缓存在 MPS 上推理（规格 `device_policy` 首选 mps）；合成帧 live 推理经同一已加载模型，两臂相同。

### 候选1 6. 限制

- 全部读数只说明本仿真、5 Hz、现行检测器与 BoT-SORT 冻结参数、本组占位参数（T_pred 4、T_repair 5 等待标定值）下的工程行为；单次回放，不是统计结论。
- 不读旧会话日志、`frames.jsonl`、RECHARTER 导出或其读数；准入原件只作本项离线回归夹具。
