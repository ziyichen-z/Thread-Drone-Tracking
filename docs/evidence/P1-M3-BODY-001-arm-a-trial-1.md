# P1-M3-BODY-001 arm A trial 1 证据（操作单 revision 7 / BC-BODY1-15）

**范围**：用户 2026-08-09 授权的**恰好一次** arm A trial 1
（`docs/authorizations.md`）。执行合同 =
`docs/evidence/P1-M3-BODY-001-1c-preflight.md` revision 7。

**状态**：§A/§B 已完成（零 Play、零 run ID、零指标）；§C 待用户执行
Play；§D/§E 待 Play 后填写。

## A. Play 前树状态记录（操作单 §2 第一段）

操作单 §2 要求 Play 时 `git status --porcelain` 为空，因此本批次（§A–§C
的证据与状态板）必须先提交；**权威 Play 前记录取在本批次提交之后的
HEAD 上**，见下表第二段。

| 项 | 实测值 |
|---|---|
| 本批次基线 HEAD | `caf02fb29fe6bb592ed2151e6e087dea828887f2`（`git status --porcelain` 空） |
| 已复核候选 | `e438b97`（Review round 4 `PASS_WITH_NOTES`） |
| `git diff --name-only e438b97..caf02fb` | 7 个路径，**零实现路径**：`docs/archive/current-status-2026-08.md`、`docs/authorizations.md`、`docs/current-status.md`、`docs/implementation-status.md`、`docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md`、`docs/reviews/P1-M3-BODY-001.md`、`tests/test_check_docs.py`（COORD-006 协调批次，仅测试夹具） |
| **权威 Play 前 HEAD** | `e33e36bc07d564d9a54a6ea4519a688e9198d1e3`（`git status --porcelain` 空；`e438b97..e33e36b` 共 8 个路径，**实现路径 0 个**） |

本批次只增 `docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md` 与
`docs/current-status.md`，二者都不是实现路径，因此提交后
`e438b97..HEAD` 仍为**零实现路径**；Play 时的实现字节与已复核 `e438b97`
**相等**，差异全部落在文档与 COORD-006 授权的测试夹具内，被 Attribution
覆盖。

> 写入边界：实现角色对 `docs/unity-test-log.md` 只读（角色白名单）。
> 上表由接受/辅助角色逐字代录进 Unity 日志条目；授权账本亦指定 Play 前
> 树状态由发令（接受）角色记录。本文件是实测来源。

## B. Play 前隔离（操作单 §2，移动不删除，逐项记录）

移动前后 SHA-256 逐一比对，全部相等（零字节改动，零删除）。

| # | 源 | 目标 | SHA-256（移动前 = 移动后） |
|---|---|---|---|
| 1 | `runtime/frames/`（1b 诊断帧，257 项 = 128 帧 ×2 + `latest.json`） | `runtime/frames.1b-diagnostic-hold/` | 目录整体移动；移动后计数 257 ✓，新建空 `runtime/frames/`（计数 0 ✓） |
| 2 | `runtime/metrics.json`（1b 诊断遗留，schema 无 `run_id`） | `runtime/metrics.1b-diagnostic-hold.json` | `c901b88e559ff926c77b9e7bda69e91b2009714ea880cadf4c26cd8a2e70b1af` |
| 3 | `runtime/m3_body_truth.jsonl` | — | **不存在**（操作单「若存在」分支未触发），无动作 |
| 4 | `runtime/scenario_config.json`（SCENE-004 override） | `runtime/scenario_config.p1-scene-004.hold.json` | `00c8802aaacfe9732b7128f6a143895f088a8e9a3f44fb2eb39f2eed7bb8b514` = 操作单 §1 钉住的 `00c8802a…b514` ✓ |
| 5a | `runtime/body_command.json` | `runtime/body_command.1b-diagnostic-hold.json` | `920a6e40a93ebbfbd1d9a3ea8a7d461fe8a2da3ce59eae4af258e784ab39cf10` |
| 5b | `runtime/gimbal_command.json` | `runtime/gimbal_command.1b-diagnostic-hold.json` | `302c325d6a938be296c47b62fcb51b9e4c53b76b217b7e8c8faccc16bd325edf` |
| 5c | `runtime/tracking_observation.json` | `runtime/tracking_observation.1b-diagnostic-hold.json` | `178b72ecdf923bf1e01ae9157fe614c0cd7356204d2d93bc3a199fc0d03c2c1f` |

命名依第 2/3/4 项在操作单中的显式样例统一取 `<stem>.<tag>.<ext>`。

第 6 项核对（全部通过）：

- 无 release pointer：`release_command.accepted.json`、`release_ack.json`、
  `p1_detect_qualification_release.json`、`qualification-release-ready.json`
  在 `runtime/` 根下均不存在。
- 无活动 qualification/scouting 标记：`p1_detect_scouting_session.json`、
  `p1_scene_004_scouting_session.json`、`scouting_qualification.json`、
  `rate3_scouting_qualification.json` 均不存在（`runtime/p1-detect-scouting/`
  等目录只是历史产物，非活动标记，未移动）。
- `runtime/runs/p1-m3-body-001-arm-a-trial-1/` **不存在**（本批次不创建）。

隔离后 `runtime/` 根内容已记录；`runtime/*` 在 `.gitignore` 内（仅
`runtime/README.md` 入版本控制），故本节零 Git 改动。

## C. 钉住项复验（操作单 §1，Play 前）

| 钉住项 | 冻结值 | 实测 |
|---|---|---|
| 载体 scenario | `f9c92052…2ce3` | `f9c9205249aacf7487579ca42f727c766800cc329d0523ec82a96140564a2ce3` ✓ |
| `scenario_id` | `deterministic-loop-default` | 一致 ✓ |
| 激活方式 | 无 runtime override → `ScenarioConfig.Load()` 回退项目默认 | override 已移开（§B.4）；`ScenarioConfig.cs:142-147` 的 `File.Exists(runtimeOverride) ? … : projectDefault` 分支确认回退 ✓ |
| 随机种子 | `random_seed: 0` | 一致 ✓ |
| 起点 | `route[0] = (125.5, 0.2, 117.5)` | `config/scenario.default.json:31` 一致 ✓ |
| 目标速度 | `2.0 m/s` | 一致 ✓ |
| 可见弧工件 | `c72c9407…576d` / 弧 `4fe2eea5…df55` | `docs/evidence/P1-M3-BODY-001-scene-body-margin.json` = `c72c940736da9bb1d2924e0d8349f8cfeb08cfb06013e656b72793155f89576d` ✓；两值与 `config/p1-m3-body-001.json` 的 `measurement_window` 两个 pin 逐字相等 ✓（F1 硬门的两侧来源） |
| tracker | `nanotrack-v2` | `runtime/models/nanotrack-v2`（backbone/head onnx）与 `config/nanotrack-v2.models.json` 均在位 ✓ |
| 重锚定 | `config/detector-reanchor.models.json` | 在位 ✓ |
| corridor 实例数 | `779` | `config/p1-m3-body-001.json` `corridor.instance_count = 779` ✓ |
| 分析工具健康 | — | `.venv-track/bin/python -m unittest tests.test_analyze_m3_body` → **28/28 OK** ✓ |

## D. Play 尝试 1：tracker 启动失败，trial 作废

**终态：`TRIAL_VOID_TRACKER_STARTUP_FAILURE`。零 run ID、零指标、零发布。**

### D.1 实际发生的步骤

1. 用户进入 Play 恰好一次，在计时器 `[2,10) s` 内暂停并报告（保留帧
   0–45，`latest.frame_id = 45`，frame 0 `simulation_time_s = 0.180357`）。
2. Implementation 取**保留的最低 frame_id = 0**，`--dump-frame 0` 导出图像
   并叠框；框由**图像本身**导出（HSV 红色掩膜最大连通域；另一处 71 px
   红点位于左上路灯附近，已排除），**未读取 `runtime/m3_body_truth.jsonl`
   或任何真值**。
3. 用户确认初始框：像素 `(177, 195, 77, 73)`，`min_side = 73 px`。
4. **归一化精度校正（已向用户披露并按其确认的像素框执行）**：先前展示的
   6 位小数值经 `norm_to_csrt_pixels`（`controller/trackers.py:93-105`，
   左/上 `floor`、右/下 `ceil`）反算为 `(176,195,78,73)`，与确认框差 1 px。
   改用项目自身 `pixels_to_norm` 的精确分数
   **`0.2765625 0.40625 0.1203125 0.15208333333333332`**，往返复算
   `(177,195,77,73)` **逐值相等**。
5. 在**保持暂停**下启动 tracker → **进程异常退出（exit 1）**。
6. 用户退出 Play，**Console 无报错**（用户报告）。未恢复 Play，帧数停在
   46 条（0–45），与暂停时一致。

### D.2 失败与根因

```
File "controller/reanchor_runtime.py", line 54, in __init__
    self.proposer = proposer or YoloeProposer(config)
File "controller/reanchor_models.py", line 151, in __init__
    import ultralytics
ModuleNotFoundError: No module named 'ultralytics'
```

**根因 = 实现角色选错解释器**，不是代码缺陷、不是环境退化、与已复核候选
`e438b97` 无关：

| 解释器 | cv2 | torch | ultralytics | 能否跑 re-anchor carrier |
|---|---|---|---|---|
| `.venv-track`（本次误用） | 5.0.0 | **缺** | **缺** | **否** |
| `.venv-yoloe` | 5.0.0 | 2.13.0 | 8.4.104 | 是 |

`config/detector-reanchor.models.json` `runtime` 三个 pin 为 torch
`2.13.0` / torchvision `0.28.0` / ultralytics `8.4.104`；`.venv-yoloe`
**三项全等**，且 `cv2.TrackerNano` 存在、`controller.track_loop` 导入正常
（只读 import 验证，未触碰运行时）。

**代码行为正确**：`YoloeProposer.__init__` 先 `verify_file` 校验权重再
`import ultralytics`，失败点在**加载任何帧之前、`TrackLoop.initialize`
之前、创建 run 目录之前、任何发布之前**，因此没有留下半启动的正式 trial。

### D.3 暴露的协议/工具缺口（非代码缺陷，交接受角色）

1. **操作单 §4 未钉解释器**；其字面命令 `python3 controller/track_loop.py`
   自 `5340cf6`/`a234270` 落地相对导入（`controller/track_loop.py:15`）后
   **无法执行**（`ImportError`）。本次实际使用 `-m controller.track_loop`
   模块形式（参数逐字未改），该形式是 Unity 日志 `:1490`/`:1634` 记录过的
   真实形式。建议 revision 8 逐字钉死 `.venv-yoloe/bin/python -m
   controller.track_loop`。
2. **`--reanchor-config` 的真实启动从未进过 Unity 日志**，该路径的运行
   环境从无有记录的验证。
3. **`tools/check_track_env.py` 只检查 cv2/CSRT**（TRACK-001 时代），
   不覆盖 torch/ultralytics/YOLOE 权重，任何预检都拦不下本次失败。

### D.4 §5 适用与现场保留

操作单 §5 写死「Play 中途任何 … **tracker 异常退出** … trial 不以任何
形式计入，现场保留，回 Acceptance 归因，**不得用旧文件或就地重跑顶替**」。
实现角色按**字面**执行：未重启 tracker、未在同一 Play 内重试、未安装任何
依赖、未清理现场。「零产出的启动前失败是否构成一次 trial」属于放宽验收
条件的判断，**留给接受角色**。

现场按原样保留（`runtime/*` 在 `.gitignore` 内，本节零 Git 改动）：

| 项 | 状态 |
|---|---|
| `runtime/runs/p1-m3-body-001-arm-a-trial-1/` | **不存在**（run ID 未创建） |
| `runtime/body_command.json` / `gimbal_command.json` / `tracking_observation.json` | **不存在**（零发布） |
| `runtime/frames/` | 46 帧（0–45），`latest.frame_id = 45`，为本次 Play 产物，原样保留 |
| `runtime/m3_body_truth.jsonl` | 46 行，SHA-256 `64be7f8542461cc9709d5b80cab0c2d7b5ad661e51763c7185dd8b6fb6fa39f2`（Unity 写入） |
| `runtime/metrics.json` | SHA-256 `d31af400306e40bf68ef242b6d819979ede9d49bedfc606904eac63c76e92e7e`（Unity `CoverageEvaluator` 在 Play 中写入，**非** tracker 产物） |
| §B 七个隔离 hold | 全部完好未动 |

Play 期间与退出时 **Console 无报错**（用户报告）；`git status --porcelain`
在整个 Play 期间保持为空，HEAD 保持 `e33e36b`。

## E. 分析与 BC-BODY1-15 分支：未触发

`tools/analyze_m3_body.py` **未运行**——没有 run 目录可绑定。因此
`h1.full_loop_c_geom` 与 `h1.disposition` **不存在**，BC-BODY1-15 的三分支
（`<0.5645` / `>=0.95` / `[0.5645,0.95)`）**一条都未触发**，其余 9 次 Play
的释放申请无从谈起。

**回接受角色的待决事项**：

1. 本次零产出的启动前失败是否消耗「恰好一次 arm A trial 1」授权，以及
   arm A trial 1 是否仍可用同一冻结初始框重跑（需用户新 GO）。
2. 操作单 revision 8：钉死解释器（`.venv-yoloe`）、修正 §4 无法执行的
   命令形式、把 §3 步骤 2 的归一化精度要求写明（用 `pixels_to_norm` 的
   精确分数，禁止 6 位小数四舍五入）。
3. `tools/check_track_env.py` 是否扩展为覆盖 re-anchor 依赖栈的 Play 前
   预检（工具改动需接受角色定范围）。

**冻结初始框已取得且可复用**（若接受角色允许）：init frame `0`，像素
`(177,195,77,73)`，归一化 `0.2765625 0.40625 0.1203125 0.15208333333333332`，
由用户在暂停中确认，无真值来源。

---

# Attempt 2（2026-08-10 新 GO，操作单 revision 9）

新授权见 `docs/authorizations.md`「2026-08-10 P1-M3-BODY-001 — 授权 arm A
trial 1 的一次新 Play（attempt 2）」，用户原话"好的，我授权进行go"。旧的
2026-08-09 GO 已消耗，本次是独立新授权。

## F. 强制前置（授权条目「强制前置」四项）

### F.1 §2.1 void 现场隔离（移动，不删除）

attempt 1 的 void 工件按操作单 §2.1 移入具名 hold，移动前后逐项相等：

| # | 源 | 目标 | 计数 / SHA-256（移动前 = 移动后） |
|---|---|---|---|
| 1 | `runtime/frames/` | `runtime/frames.arm-a-trial-1-void-attempt-1-hold/` | **93 项**（46 json + 46 jpg + `latest.json`），帧号 `frame_0000000000`–`frame_0000000045`；移动后仍 93 ✓，新建空 `runtime/frames/`（0 项 ✓） |
| 2 | `runtime/m3_body_truth.jsonl` | `runtime/m3_body_truth.arm-a-trial-1-void-attempt-1-hold.jsonl` | `64be7f8542461cc9709d5b80cab0c2d7b5ad661e51763c7185dd8b6fb6fa39f2`；**46 行**（前后相同） |
| 3 | `runtime/metrics.json` | `runtime/metrics.arm-a-trial-1-void-attempt-1-hold.json` | `d31af400306e40bf68ef242b6d819979ede9d49bedfc606904eac63c76e92e7e` |

三个目标路径移动前均不存在（无碰撞）；**零删除、零覆盖**，void 工件未进入
任何分析器输入。

**1b diagnostic holds 一字节未动**（移动前后 SHA-256 全等）：
`metrics.1b-diagnostic-hold.json` `c901b88e…`、
`scenario_config.p1-scene-004.hold.json` `00c8802a…`、
`body_command.1b-diagnostic-hold.json` `920a6e40…`、
`gimbal_command.1b-diagnostic-hold.json` `302c325d…`、
`tracking_observation.1b-diagnostic-hold.json` `178b72ec…`；
`frames.1b-diagnostic-hold/` 前后均 **257 项**。

### F.2 §2 六项隔离状态

attempt 1 已完成的隔离仍然成立，本轮逐项复核（全部**不存在** = 已隔离）：
`metrics.json`、`m3_body_truth.jsonl`、`scenario_config.json`、
`body_command.json`、`gimbal_command.json`、`tracking_observation.json`。
`runtime/frames/` 为新建空目录。

第 6 项核对全部通过（均不存在）：`release_command.accepted.json`、
`release_ack.json`、`p1_detect_qualification_release.json`、
`qualification-release-ready.json`、`p1_detect_scouting_session.json`、
`p1_scene_004_scouting_session.json`、`scouting_qualification.json`、
`rate3_scouting_qualification.json`、
**`runtime/runs/p1-m3-body-001-arm-a-trial-1/`**（该 ID 至今未创建）。

### F.3 钉住项复验

`config/scenario.default.json` = `f9c9205249aacf7487579ca42f727c766800cc329d0523ec82a96140564a2ce3` ✓
（与 §1 冻结值相等）；
`docs/evidence/P1-M3-BODY-001-scene-body-margin.json` = `c72c940736da9bb1d2924e0d8349f8cfeb08cfb06013e656b72793155f89576d` ✓。
冻结初始框沿用 round 20 §A.4：init frame `0`、px `(177,195,77,73)`、
normalized `0.2765625 0.40625 0.1203125 0.15208333333333332`——**不重新框选**。

### F.4 Play 前树状态与归因

与 attempt 1 同理，本批证据必须先提交才能满足「`git status --porcelain`
为空」，故权威记录取在本批提交之后（见下表）。

| 项 | 实测值 |
|---|---|
| 已复核 runtime 候选 | `e438b97`（Review round 4 `PASS_WITH_NOTES`，round 23 确认继续有效） |
| `git diff --name-only e438b97..HEAD` | 14 个路径；**controller/ 、Assets/、config/ 改动数为 0**，非 docs/tests/tools 路径数为 0 |
| 归因 | 差异全部为文档、COORD-006 测试夹具、以及 round 23 已接受的预检工具/测试（`tools/preflight_reanchor_env.py`、`tests/test_preflight_reanchor_env.py`）——**零 runtime 实现字节** |
| **权威 Play 前 HEAD** | 见 §F.6（本批提交后实测） |

### F.5 step-0 预检

见 §F.6，与树状态记录同批实测。

## F.6 权威 Play 前记录 —— **未按要求落盘（round 24 §A.2 阻断项）**

**这一节在 attempt 2 的 Play 期间逐字停留在「待本批提交后实测填入」。**
实现角色确实在提交 `0cf88f3` 之后、Play 之前实测了 HEAD、空树与 step-0
预检，但**只在会话消息里报告，没有写进本证据文件，也没有进
`docs/unity-test-log.md`**。因此当时状态板「四项前置全部通过」的主张
**没有权威记录支撑**。

按 round 24 §A.3，Acceptance 不接受用 Play 开始后的 HEAD/干净树或补跑
预检来追认「采集开始前」的事实；workflow §4.5 要求采集开始前把
HEAD/status 写入 Unity 日志，该时序证据**不可事后重建**。下列数值仅作
事实记录，**不构成**对当时缺失记录的补正：

| 项 | 实测值（Play 前于会话中报告，未落盘） |
|---|---|
| HEAD | `0cf88f362de57b649b1e6a1e7dd92d4b1cfbe916` |
| `git status --porcelain` | 空 |
| `e438b97..HEAD` 的 controller/Assets/config 路径数 | 0 |
| step-0 预检（`.venv-yoloe`） | `PASS`，退出 0，`side_effect_identity.unchanged = true` |

**归因：实现角色的记录时序错误。** 为保持 Play 时工作树干净而把落盘推迟
到 Play 之后，等于让强制前置在采集开始时不存在于任何权威文件。attempt 3
必须在发令前先把该记录落盘并提交（见 round 24 §B.5 / revision 10）。

## G. Attempt 2 终态：协议偏差，tracker 启动前作废

**终态：`TRIAL_VOID_PROTOCOL_DEVIATION_PRE_TRACKER`（不计数）。**
Acceptance round 24 **REJECTED** 本次 Play 继续，两条阻断：

1. **暂停超窗**：`sim_t = 10.854 s` 超出 revision 9 §3 step 2 的 `[2,10) s`。
   round 24 §B.1 裁定该窗口是本次 GO 逐字绑定的操作步骤；step 2 后面两条
   具名 fail-closed（最低帧、框覆盖）**只约束它们自己，不撤销暂停窗口**，
   里程口径也不能反向扩大已授权的操作范围。实现角色当时未自行放宽，而是
   停在启动 tracker 之前上报——该处置被 round 24 采纳。
2. **缺事前身份/预检记录**（独立且决定性）：见 §F.6。

### G.1 现场清点（保留 + 哈希，零删除零覆盖零分析）

| 项 | 实测 |
|---|---|
| `runtime/frames/` | **109 项** = 54 json + 54 jpg + `latest.json`；帧号 `frame_0000000000`–`frame_0000000053` 连续；`latest.frame_id = 53` |
| `runtime/m3_body_truth.jsonl` | **54 行**，SHA-256 `7acd7a76f7791aa2b4f685cd0e8c8e4c23b66b14d274a7db9380ed51e31ea64a` |
| `runtime/metrics.json` | SHA-256 `f12ec0930382372dfc5e3b82251695fdca02ce0e7e307ed7343e49cd39922bbe` |
| 首末帧 `simulation_time_s` | frame 0 = `0.256520`；frame 53 = `10.854090` |

**确认 tracker 从未启动**（全部不存在）：
`runtime/runs/p1-m3-body-001-arm-a-trial-1/`、`runtime/body_command.json`、
`runtime/gimbal_command.json`、`runtime/tracking_observation.json`；
全仓 `find runtime -name m3_body_analysis.json` **零命中**（未产出任何分析）；
无 `controller.track_loop` 进程残留。**零 run ID、零指标、零发布、零分析。**

用户报告：已退出 Play，**Console 无报错**。

### G.2 既有 hold 全部完好

- attempt-1 void holds：truth `64be7f85…`、metrics `d31af400…`、
  `frames.arm-a-trial-1-void-attempt-1-hold/` **93 项** —— 与 §F.1 记录相等。
- 1b diagnostic holds：五个文件 SHA-256 全等
  （`c901b88e…`/`00c8802a…`/`920a6e40…`/`302c325d…`/`178b72ec…`），
  `frames.1b-diagnostic-hold/` **257 项**。

attempt 2 的现场按原样保留，**未移动**（§2.1 只规定 attempt 1 的工件；
attempt 3 的隔离合同由 revision 10 定义）。禁止删除、覆盖、分析、重进或
就地重跑，本条均已遵守。

### G.3 授权状态

2026-08-10 的 one-Play GO **已因进入 Play 消耗**；arm A trial 1 的下一次
Play 与其余 9 次**全部未授权**。run ID `p1-m3-body-001-arm-a-trial-1`
**至今未创建**，仍可在未来新 GO 下首次合法使用。attempt 3 需先有
revision 10（写死暂停超窗的机械终态、要求 Play 前记录发令前落盘）、
Acceptance 重新核验与用户新的逐字 GO。


---

# H. Revision 10 返工批次（Acceptance round 25 §B）

**零 Play、零 run ID、零指标、零发布、零分析。** 本批只保全现场并改操作单
文档，未触碰任何 runtime/config/tool/test 路径。

## H.1 B.1 — attempt 2 现场保全（移动，不删除）

三个目标移动前均**不存在**；移动前后计数/SHA-256 与 §G 清点**逐项相等**：

| 源 | 目标 | 前 = 后 |
|---|---|---|
| `runtime/frames/` | `runtime/frames.arm-a-trial-1-void-attempt-2-hold/` | **109 项**（54 json + 54 jpg + `latest.json`）→ 109 ✓；新建空 `runtime/frames/`（0 项 ✓） |
| `runtime/m3_body_truth.jsonl` | `runtime/m3_body_truth.arm-a-trial-1-void-attempt-2-hold.jsonl` | **54 行** ✓；`7acd7a76f7791aa2b4f685cd0e8c8e4c23b66b14d274a7db9380ed51e31ea64a` ✓ |
| `runtime/metrics.json` | `runtime/metrics.arm-a-trial-1-void-attempt-2-hold.json` | `f12ec0930382372dfc5e3b82251695fdca02ce0e7e307ed7343e49cd39922bbe` ✓ |

**零覆盖证明**：三个目标路径在移动前经 `-e` 逐项确认不存在，故 `mv` 不可能
覆盖任何既有字节；移动后的 SHA-256 与移动前逐字相等，证明内容未被改写。
**零删除、零分析**：未执行任何 `rm`，未对 void 工件运行 `analyze_m3_body.py`。

## H.2 既有 hold 逐项复核不变

- attempt-1 void holds：truth `64be7f85…`、metrics `d31af400…`、
  `frames.arm-a-trial-1-void-attempt-1-hold/` **93 项** —— 与 §F.1 相等。
- 1b diagnostic holds：`c901b88e…`/`00c8802a…`/`920a6e40…`/`302c325d…`/
  `178b72ec…` 五个 SHA-256 全等；`frames.1b-diagnostic-hold/` **257 项**。

## H.3 正式工件仍不存在

`runtime/runs/p1-m3-body-001-arm-a-trial-1/`、`runtime/body_command.json`、
`runtime/gimbal_command.json`、`runtime/tracking_observation.json`、
`runtime/metrics.json`、`runtime/m3_body_truth.jsonl` **均不存在**；
`find runtime -name m3_body_analysis.json` **零命中**。
零 run ID、零 tracker 指标、零发布、零分析。

## H.4 B.2 — 暂停窗口成为独立硬门

操作单 §3 步骤 2 重写为**三个互不覆盖的独立硬门**，门 1 逐字定义

```text
2.000000 <= reported_sim_t < 10.000000
```

越界终态 **`TRIAL_VOID_PAUSE_WINDOW_VIOLATION`**：保持暂停、不启动 tracker、
不恢复 Play、退出并保全现场、回 Acceptance。文中逐字写明门 2/门 3 通过或
「里程测量窗不受影响」**都不得覆盖该终态**，且**运行中不得申请例外**，并
引用 attempt 2 的 `10.854090` 作先例。§1 新增同名钉住项，§5 新增 tracker
启动前两个具名终态的对照表。

## H.5 B.3 — Play 前记录时序自引用消除

操作单新增 §2.0，逐字规定四步顺序：(a) 新 GO 由 Acceptance 入账并**提交**；
(b) Implementation 在最终干净 HEAD `H` 上实测并报告 `git rev-parse HEAD`、
空 `git status --porcelain`、`e438b97..H` 归因、step-0 的**退出码与完整
JSON**；(c) **Acceptance**（实现角色对 Unity 日志只读）在用户进 Play 前把
这些值写入 `docs/unity-test-log.md`；(d) 发令时 `git diff --name-only`
**逐字只有** `docs/unity-test-log.md` 这一条未提交差异（workflow §4.5 允许
该白名单文档差异）。明文**禁止**以「保持工作树完全干净」为由把记录延迟到
Play 之后；§F.6 只**链接**该事前日志，不另造第二个身份来源。

## H.6 B.4 — 冻结语义逐字未变

revision 9 的唯一解释器/CLI（`.venv-yoloe/bin/python -m controller.track_loop`
及全部参数）、run ID、init frame `0`、像素框 `(177,195,77,73)` 与 normalized
box、planner/arm、`--planned-duration-s 130.0`、分析器、阈值、测量窗
（里程 `[0, 62.5 m]`）、§5 退化三分支与反调参纪律**全部逐字保留**。

## H.7 范围（round 25 §B.5）

本批改动路径：`docs/evidence/P1-M3-BODY-001-1c-preflight.md`（revision 10）、
`docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md`（本节）、
`docs/current-status.md`（+ 机械归档）。

**零 `controller/`、零 Assets/C#、零 config、零 models、零 tools、零 tests、
零指标算法、零 Review、零正式设计、零 Unity 日志、零授权账本改动**；未进入
Play，未创建正式 ID 或指标。

---

# I. Revision 11 返工批次（Acceptance round 29 §C）

**零 Play、零新 ID、零指标、零发布、零分析。** 未运行 `--finalize`、
未分析任何 void 工件。

## I.1 C1 — attempt 3 现场保全（七组移动，零删除零覆盖）

七个目标移动前经 `-e` 逐项确认**不存在**（零覆盖证明）；移动前后逐项相等：

| 源 → 目标 | 前 = 后 |
|---|---|
| `runs/p1-m3-body-001-arm-a-trial-1/` → `…-void-attempt-3-hold/` | **2 个文件**；`frames.jsonl` 755 行 / 951704 B / `8f9f355186cf06d83dd30956552b9687cd4992454090f89ecc307f2b986016b5`；`manifest.json` 207 行 / 7857 B / `e5caa98276a48413f3d78d34228d8c41d8ad0b9e8b438c070d4925c4f14e8a65` |
| `frames/` → `frames.arm-a-trial-1-void-attempt-3-hold/` | **257 个文件** |
| `m3_body_truth.jsonl` → `…-void-attempt-3-hold.jsonl` | 627 行 / 641080 B / `6e273895c66e403b0da7049aa1885a09970a618465995eb7c1b3765f4be9af50` |
| `metrics.json` → `metrics.arm-a-trial-1-void-attempt-3-hold.json` | 61 行 / 2084 B / `59085980051fee71160dd592028fce06e191ebeb0ad4453d92bfe9843dbfefd2` |
| `body_command.json` → `…-void-attempt-3-hold.json` | 10 行 / 207 B / `71fa80359486db7c8793ee5ebc26b88bae2e89a3b92e1b5f9460a41dce5e0686` |
| `gimbal_command.json` → `…-void-attempt-3-hold.json` | 15 行 / 341 B / `372e6007f89543a4f92fa8f88da9b1ab9f81e669603ea571227afd642c5b455d` |
| `tracking_observation.json` → `…-void-attempt-3-hold.json` | 18 行 / 459 B / `b0dda5b065faf481a7cb9479ad374dc1de6d869a5ec772c399b4237f040826c4` |

移动后只新建空 `runtime/frames/`（0 项）；**attempt-4 run 目录未预建**
（实测不存在）。既有 hold 逐项复核不变：attempt-1 truth `64be7f85…` /
metrics `d31af400…` / frames **93**；attempt-2 truth `7acd7a76…` /
metrics `f12ec093…` / frames **109**；1b 五个 SHA 全等 / frames **257**。

## I.2 C2 — 唯一替代采集 ID（`tools/analyze_m3_body.py`）

新增冻结常量：`A1_ACQUISITION_RUN_ID = "p1-m3-body-001-arm-a-trial-1-attempt-4"`、
`A1_CANONICAL_TRIAL_ID = "p1-m3-body-001-arm-a-trial-1"`、
`A1_ATTEMPT_NUMBER = 4`、`A1_PREDECESSOR_VOID_MANIFEST_SHA256 = e5caa982…8a65`、
`A1_PREDECESSOR_VOID_FRAMES_SHA256 = 8f9f3551…16b5`。

- `canonical_trial_id()`：采集 ID → canonical slot。旧 A1 ID 具名拒绝
  `run_id_void_consumed`；任何其他 attempt 后缀拒绝 `run_id_not_frozen_trial`；
  其余九个 ID 映射到自身。
- `expected_acquisition_ids(arm)`：A 臂序列首位换成采集 ID，其余逐字不变；
  B 臂完全不变。
- `_expected_policy()` 改为先取 canonical 再定臂，三层臂身份语义不变。
- `compare_arms()`：期望序列改用 `expected_acquisition_ids`，并新增
  **canonical slot 去重**（`duplicate_canonical_trial_slot`），使不同采集 ID
  无法冒充两个不同 slot；重复/缺号/错臂/错序的原有拒绝全部保留。
- A1 receipt 新增五个绑定字段；compare 逐字核对
  （`a1_attempt_binding_mismatch:<key>`）。这五个键**故意不进
  `identity_keys`**——round 29 §C.2 明确不把它们要求为其余九个 run 的共同值。

**披露的读法**：§C.2 只要求「compare 机械核对这些 A1 专属字段」，未要求
禁止其余九个 run 携带同名字段。实现按字面执行：只在 A1 上核对，不对其余
九个施加额外要求；测试另证 A2 不会被写入这些字段。若 Acceptance 本意是
「其余九个必须不得携带」，请在下一轮指明。

## I.3 C3/C4 — 完成握手与异常终态（操作单 revision 11）

§3 步骤 4 改为逐字握手：用户**继续保持 Play 不得自行退出**；
Implementation 必须同时观察到 (1) tracker **自然退出码 0**、(2) stdout final
JSON 指向**同一采集 ID** 的 `summary.json`、(3) run 内 `metrics.final.json`
与 `summary.json` **均存在**，才可报 `TRACKER_AUTO_COMPLETE_CONFIRMED` 并请
用户退出。§1 增两条钉住项；§5 增
`TRIAL_VOID_PROTOCOL_DEVIATION_POST_TRACKER_EARLY_EXIT` 终态与「不 finalize、
不分析、不重进、墙钟不得替代仿真时间」的处置，并记明此类 void **消耗该次
采集 ID**。

## I.4 C6 — 机械反例与回归

新增 `AttemptIdentityBindingTests` 六个用例：采集 ID→canonical 映射；
旧 void ID 永久拒绝（含 `_expected_policy` 路径）；四个其他 attempt 后缀
（A1-attempt-3/5、A2-attempt-4、B1-attempt-4）全部拒绝；其余九个 ID 映射
自身；期望序列只在 A1 位替换且不含旧 ID；A1 receipt 携带五字段而 A2
（同臂同策略）**不携带**。原有 28 个用例全部保留并通过（夹具改用新采集 ID）。

| 命令 | 结果 |
|---|---|
| `.venv-track/bin/python -m unittest tests.test_analyze_m3_body` | **34/34 OK** |

## I.5 C5 范围与 C6 停点

改动路径：`tools/analyze_m3_body.py`、`tests/test_analyze_m3_body.py`、
`docs/evidence/P1-M3-BODY-001-1c-preflight.md`（revision 11）、本文件、
`docs/current-status.md`。**零 `controller/`、零 Assets/C#、零 config、
零 models、零 scenario、零 tools/check_*.py、零指标算法/阈值/窗口/planner/
130 s 改动**；未以 attempt-3 内容调参。

本轮改变了正式 run 绑定协议，按 §C.6 **停在稳定候选**：交 Acceptance 按
workflow §4.3.1 归因并送**独立 Review**；Review verdict 与用户新的逐字
one-Play GO 之前，**不得执行 attempt 4**。本批不申请 GO。

---

# J. Revision 11 round 2（Acceptance round 30 §C）

**零 Play、零新 ID、零指标、零发布、零分析、零 finalize。**

## J.1 B1/B2 — 操作接口与文字矛盾

| 项 | 修法 |
|---|---|
| §3 step 5 分析命令 | 改为 `--run-id p1-m3-body-001-arm-a-trial-1-attempt-4`（原文调用被拒 ID，照做必然作废成功的 attempt 4） |
| analyzer 模块说明 + Usage | 改成「十个 canonical slots 由十个 acquisition IDs 采集」；单-run 与 compare A 臂首项都用采集 ID |
| §1 ID 行 | 拆成两行：**canonical slots**（只作 receipt 的 `canonical_trial_id`，不作目录/CLI/compare 输入）与 **acquisition IDs**（A1 = attempt-4，其余九个等于 canonical；create-once 施加于采集目录） |
| §4 | 改为「**仅 `--run-id` 按 C2 替换**，其余参数一个不改一个不加」 |
| §5 | 前两种 pre-tracker void **未创建/未消耗采集 ID**；第三种 post-tracker void **已消耗采集 ID**，下次须由 Acceptance 冻结新采集 ID。三种都各消耗一次 one-Play GO。**更正**：round-2 只改了这段散文，标题与表格仍把三者混在一起，round 31 §B6 判为未分段；实际分段在 round 3 完成（§K） |

## J.2 B3 — predecessor 真实字节绑定

新增 `_check_a1_predecessor_hold()`，在 A1 的 `analyze_trial` **执行任何
create-once 收集或写入之前**运行：hold 目录必须存在；直接文件集合必须**恰为**
`frames.jsonl` + `manifest.json`；两者 SHA-256 必须分别等于 round-29 常量。
具名失败：`a1_predecessor_hold_missing`、
`a1_predecessor_hold_file_set_mismatch`、
`a1_predecessor_void_frames_sha256_mismatch`、
`a1_predecessor_void_manifest_sha256_mismatch`。

该门**只枚举文件名并对原始字节取 SHA**，不解析 void 内容、不计算任何指标，
因此不违反「禁止分析 void 工件」。反例六条（缺目录、多一个文件、少一个文件、
frames 字节篡改、manifest 字节篡改、A2 不受该门约束），每条都另断言失败时
**未在 attempt-4 run 内新建任何收集输入或 `m3_body_analysis.json`**。
另有一条测试断言**出厂常量本身**仍是 attempt-3 的真实 SHA（夹具只在临时目录
内 patch 期望值，出厂值不被测试掩盖）。

## J.3 B4 — 完成握手的机械 AND 门

新增只读模式 `--validate-completion`（`validate_completion()`），CLI 逐字冻结
在操作单 §3 步骤 4。AND 条件：exit code 恰 `0`；final JSON 为对象且 `run_id`
等于采集 ID；其 `summary` 解析到该 run 的 `summary.json`；manifest 同 ID；
`summary.json` 与 `metrics.final.json` 均存在；`metrics_snapshot_present`
为 `true`；`actual_duration_s >= 130.0`。**不调用 `finalize_run`、不写任何
文件。**

真实子进程实测：

| 场景 | 结果 |
|---|---|
| 全部满足 | 退出 **0**，stdout **仅** `TRACKER_AUTO_COMPLETE_CONFIRMED` |
| exit code = 1 | 退出 2，stdout 空，`ANALYSIS_FAIL_CLOSED:completion_tracker_exit_code_nonzero:1` |
| `actual_duration_s = 125.3803`（attempt 3 实际值） | 退出 2，`completion_duration_below_watchdog:125.3803` |

反例覆盖每个 AND 条件：非零 exit、畸形 JSON、非对象 JSON、错 run ID、
错 summary path、逃逸到 run 目录外的 summary path、manifest 错 ID、
`summary.json` 缺失、`metrics.final.json` 缺失、
`metrics_snapshot_present` 为 `False`/`None`/字符串 `"true"`、duration
`< 130.0`、duration 非数值；另一条**证明 PASS 路径零写入**（目录清单与
每个文件 SHA-256 前后相等，且未生成 `m3_body_analysis.json`）。

操作单 §3 步骤 4 已写明：确认词**只能**由该命令 PASS 产生，**不得人工复述**。

## J.4 B5 — 单一 main guard

删除文件中间的第一个 `if __name__ == "__main__":`，`AttemptIdentityBindingTests`
及新增两个测试类现在都在**唯一的末尾 guard 之前**。两个入口计数一致：

| 命令 | 结果 |
|---|---|
| `.venv-track/bin/python -m unittest tests.test_analyze_m3_body` | **50/50 OK** |
| `.venv-track/bin/python tests/test_analyze_m3_body.py` | **50/50 OK** |
| `.venv-track/bin/python -m unittest discover -s tests` | **510/510 OK（1 skip）** |

## J.5 范围与停点

改动路径：`tools/analyze_m3_body.py`、`tests/test_analyze_m3_body.py`、
`docs/evidence/P1-M3-BODY-001-1c-preflight.md`、本文件、
`docs/current-status.md`。**零 `controller/`、零 Assets/C#、零 config、
零 models、零 scenario、零 `tools/check_*.py`、零指标算法/阈值/窗口/planner/
130 s 改动。**

按 round 30 §C.6 **再次停在候选**：不自行送独立 Review、不申请 GO。


---

# K. Revision 11 round 3（Acceptance round 31 §C，仅文档）

**零代码、零测试、零 Play、零新 ID、零指标。** 本轮只改操作单 §5 的分段与
两份文档的措辞，未触及 `tools/`、`tests/` 或任何运行/指标语义。

## K.1 B6 — §5 真正分段

round 31 §B6 属实：round-2 只改写了 ID 消耗那段散文，**标题
「tracker 启动前的具名终态」与同一张表仍把三种终态混在一起**，第三行自身
却写着 tracker 已启动。执行者按标题分类与按行分类会得到相反结论，直接影响
「run 目录/采集 ID 是否已消耗」。我的 J.1 声称「§5 分开」属于**overclaim**，
上表已就地更正。

现在 §5 是两个并列段落，各自独立标题与表格：

| 段落 | 表内终态 | 结论 |
|---|---|---|
| **pre-tracker 具名终态**（tracker 尚未启动） | `TRIAL_VOID_PAUSE_WINDOW_VIOLATION`、`TRIAL_VOID_TRACKER_STARTUP_FAILURE` | run 目录**未创建**，采集 ID **未被消耗**，未来新 GO 下可首次合法使用 |
| **post-tracker 具名终态**（tracker 已启动） | `TRIAL_VOID_PROTOCOL_DEVIATION_POST_TRACKER_EARLY_EXIT` | run 目录**已创建**，采集 ID **已被消耗**；保留「不 `--finalize`、不分析、不重进」，墙钟不得替代仿真时间 |

第三条独立条目写明三种终态**每种各消耗一次 one-Play GO**。
**终态名、触发条件与任何运行/指标语义均未改动。**

## K.2 范围

改动路径：`docs/evidence/P1-M3-BODY-001-1c-preflight.md`（§5）、本文件
（J.1 更正 + 本节）、`docs/current-status.md`。**零 `tools/`、零 `tests/`、
零 `controller/`、零 Assets/config/models/scenario。** 按 round 31 §C.3
再次停在候选：不自行送 Review、不申请 GO、不进入 Play。

---

# L. Revision 11 round 4（Acceptance round 33 §B，仅文档）

闭合独立 Review round 5 的阻断项 **F3**。**零移动、零删除、零覆盖、零重算
现场；零代码、零测试、零 Play、零新采集 ID、零指标、零分析。**

## L.1 F3 四条事实已逐条对磁盘复核（实现角色确认属实）

| F3 分项 | 复核结果 |
|---|---|
| §2.2 与代码冲突 | 属实：操作单写「冻结 ID 只能在新 GO 后由该次正式运行创建」，而 `canonical_trial_id()` 对同一串抛 `run_id_void_consumed` |
| §2.2 写成待执行、实则已完成 | 属实：三个目标 hold 全部已存在，§2.3/§2.4 标了「已执行」而 §2.2 没有 |
| §2.1 六项已不可执行 | 属实：六个源全部不存在、目标全部已存在；逐字执行会卡在第 1 项 |
| §2.1 第 6 项核对错目录 | 属实：核对的是被消耗的 canonical ID；attempt 4 的真前置是 `…-attempt-4/` 不存在（`controller/run_log.py:508` 为 `mkdir(exist_ok=False)`） |

## L.2 B1/B2 — §2.1/§2.2 转为已执行历史

- **§2.1** 改标题为「1b 诊断现场隔离（**已执行**，2026-08-09）」，正文改为
  过去时的六项记录，删去「任一项与预期不符即停」这类现在时指令；第 3 项
  如实写明当时 `m3_body_truth.jsonl` 不存在、「若存在」分支未触发；原第 6 项
  对旧 canonical 目录的核对以引用块保留为**历史**，并指向 §2.4/§2.5。
- **§2.2** 改标题为「attempt 1 现场保全（round 20 §B.3，**已执行**，
  2026-08-10）」，删去「返工期一律不执行本节移动／只有在用户新 GO 之后…
  执行下列移动」的现在时指令，保留 source→hold、计数与两个 SHA-256 及
  零删除/零覆盖/零分析结论。
- **旧 canonical ID 的时间边界（B2）**：明写 attempt 1 保全当时它尚未被创建
  或消耗，原表述**只适用于当时**；attempt 3 已创建并消耗该 ID 且已移入
  `…-void-attempt-3-hold/`，**当前与未来一律不得再作为 acquisition ID 或
  run 目录被创建**，与 §1 acquisition-IDs 行、§5 post-tracker 段和
  `run_id_void_consumed` 三处对齐。A1 唯一 acquisition ID 仍是 attempt-4。

## L.3 B3 — 新增 §2.5：attempt 4 的只读 Play 前状态核对

§2.5 是 §2 中**唯一待执行**的动作，且**只读**、不移动不清理。九项核对与
实测结果（本批次实跑，零写入）：

| # | 核对项 | 期望 | 实测 |
|---|---|---|---|
| 1 | 三个发布文件 | 均不存在 | ✓ 全部 absent |
| 2 | `metrics.json` / `m3_body_truth.jsonl` / `scenario_config.json` | 均不存在 | ✓ 全部 absent |
| 3 | `runtime/frames/` | 存在且为空 | ✓ 存在，0 项 |
| 4 | 1b hold | frames **257**，五个 SHA 与 §B 相等 | ✓ 257 |
| 5 | attempt-1 hold | frames **93**，truth/metrics SHA 与 §F.1 相等 | ✓ 93 |
| 6 | attempt-2 hold | frames **109**，SHA 与 §H.1 相等 | ✓ 109 |
| 7 | attempt-3 hold | run hold 恰两文件 + frames **257**，SHA 与 §I.1 相等 | ✓ `frames.jsonl` + `manifest.json`，frames 257 |
| 8 | 活动 release/qualification/scouting 标记 | 无 | ✓ 无 |
| 9 | `runs/…-attempt-4/` | 不存在 | ✓ absent |

任一项不符即停止回 Acceptance、禁止就地修正后继续。第 9 项写明它才是
attempt 4 的真 create-once 前置，并禁止改用旧 canonical 目录作核对对象。

## L.4 B4/B5 — 两处与实现/时序不符的文字

- **B4**：§1「真值载体」行与 §3 step 5 原称 `--verify`「只读 run 目录」。
  与已发布实现不符——`_check_a1_predecessor_hold()` 在 `--verify` 路径同样
  先于任何读取执行，因此 **A1 的 attempt-4 verify 会另读 run 目录之外的
  attempt-3 predecessor hold**。两处均已改写为：A1 读两处并逐字节核对，
  其余九个 run 仍只读各自 run 目录；并注明该门只枚举文件名与取原始字节
  SHA-256，不解析 void 内容、不算 void 指标。**只改文字，未动 predecessor 门。**
- **B5**：§6 的 revision-10 历史句原写「`p1-m3-body-001-arm-a-trial-1` 仍未
  创建」，与当前 §1/§2.4/§5 相反。已改为有时间边界的记录：该修订完成时
  尚未创建，此后 attempt 3 已创建/消耗并移入 hold，当前与未来不得再创建。
  revision-8 句同样加了「此后已在 attempt 2 之前执行完毕」的时间标注。

## L.5 范围（B6）

改动路径：`docs/evidence/P1-M3-BODY-001-1c-preflight.md`、本文件、
`docs/current-status.md`（+ 机械归档）。**零 `tools/`、零 `tests/`、零
`controller/`、零 Assets/config/model/scenario**；未真正移动、删除、覆盖
或重算任何现场工件。Review round 5 已 `CONFIRMED` 的四项新门与其
50/50、36/36、510 全套结论不受本轮影响。

再次停在候选：不自行送 Review、不申请 GO、不进入 Play。

---

# M. N24 基线指针更新（Acceptance round 35 §C.2，单行机械更新）

**零代码、零测试、零 Play、零采集 ID、零指标、零分析、零现场改动。**

操作单 §2.0 **(b)** 的归因基线由 `git diff --name-only e438b97..H` 逐字改为
`git diff --name-only 6019f33..H`，并注明基线是**上一个通过独立 Review 的
候选** `6019f33`（Review round 6 `PASS_WITH_NOTES`），`e438b97` 已过期。

依据：round 33 §C.3 曾要求「只能在新候选获得独立 Review PASS 并有确切
commit 后更新，Implementation 不得预猜未来 PASS 哈希」——该确切哈希现已
由 Review round 6 给出；round 35 §C.2 因该行位于 `docs/evidence/`（接受角色
机械白名单不允许直接改）而指派给 Implementation，并写明按字面修改不需新一轮
Review。

**未触及**：`tools/`、`tests/`、`controller/`、Assets、config、model、
scenario，以及任何其他操作语义——§2.0 的四步顺序、(a)/(c)/(d) 三步、§2.5
九项核对、§3 各步骤、§4 CLI、§5 终态表全部逐字未改。

本轮不申请 GO：用户 2026-08-10 的授权仍为 `CONDITIONAL_NOT_YET_EFFECTIVE`，
其「确认无误后」的条件由 Acceptance 判定；N22 的 GO 前只读核对已由
Acceptance 于 round 35 §B.1 闭合。

---

# N. Attempt 4 归档与 live 握手逐字转录（Acceptance round 37 §C）

**零代码/测试/config/scenario/model/协议改动；零新 Play/ID；零指标重算。**
正式 run 目录十一份文件与 predecessor hold **一字节未动**。

## N.1 §C.2 归档（移动，不删除）

目标 `runtime/test-results/p1-m3-body-001-arm-a-trial-1-attempt-4-post-run/`
移动前不存在。移动前后逐项相等：

| 源 | 计数/行数/字节 | SHA-256（前 = 后） |
|---|---|---|
| `runtime/frames/` → `…/frames/` | **257** 项 | 目录聚合 `ea9ba0505e1be7e0ce17c5420e5a13c96a3a756c541ff1293bf78ed8018b2fb3` |
| `m3_body_truth.jsonl` | 1027 行 / 1050207 B | `46e1f20b5d35c3e3c89dda7798749632d578f60e132dc0cafce9c71c2064aeb8` |
| `metrics.json` | 61 行 / 2059 B | `bfeaff08a18f19062ab5cf44ebab877575e0b5f0245a948c6abf016d25a9e6bd` |
| `body_command.json` | 10 行 / 207 B | `a2ae5fea538d56462102bcad274eefd5d0a35caacf164f8bc3bdae5aa33e3144` |
| `gimbal_command.json` | 15 行 / 340 B | `c0713abdf1f5dd5fcded356f630fecbad4cd1311659ca6894972ae53c9297c7a` |
| `tracking_observation.json` | 18 行 / 459 B | `fd1f95005237cd64ef035a35ee1ae9126cd47792b2d193695b78cc20750fbe1c` |

移动后重建空 `runtime/frames/`（0 项）。**未移动、未改写**正式 run 目录
（聚合 SHA-256 `7c3af28e3adbc3bdd72cc54e24002fd1c3e5eaa8628e76ba364442df093cda79`
前后相同）与 attempt-3 predecessor hold（`8f9f3551…` / `e5caa982…` 未变）。

**移动后 `--verify` 复跑 PASS**，逐字相同：
`{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355,
"run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true,
"window_c_track_given_geom": 1.0}`，退出码 0。

## N.2 §C.3 live 握手四项逐字转录

来源：本实现会话的实际输出，非事后重建、非合成。

**(1) tracker 自然退出码：`0`**
后台任务完成通知逐字为 `Background command "Start the attempt-4 tracker"
completed (exit code 0)`；随后 `pgrep -f "controller.track_loop"` 无命中，
进程已自然退出（非信号终止、非人工终止）。

**(2) tracker stdout 最后一行 JSON（逐字）**

```json
{"qualification_metrics_error": null, "records": 651, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "state": "TRACKING", "summary": "~/TetheredDroneTracking/runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4/summary.json"}
```

> 同一 stdout 在该行之前另有依赖噪声一行
> `Could not import \`tifffile\`, TIFFImageDataDecoder will be disabled`
> （ultralytics/PIL 导入期打印）。转录如实保留该事实；validator 取的是
> 最后一行 JSON。

**(3) validator 实际调用与输出**

命令（`--tracker-final-json` 传入的即上面那一行原文）：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --validate-completion \
  --runtime runtime \
  --run-id p1-m3-body-001-arm-a-trial-1-attempt-4 \
  --tracker-exit-code 0 \
  --tracker-final-json "$FINAL"
```

stdout 逐字：`TRACKER_AUTO_COMPLETE_CONFIRMED`；**退出码 `0`**。
该命令在**用户退出 Play 之前**执行，确认词是其输出而非人工复述。

**(4) 用户退出后的 Console 报告（逐字）**：「**已经退出，没有报错**」。

四项**均可恢复，无 `UNAVAILABLE`**。

## N.3 时序（如实，含一处未逐字记录项）

用户在本会话逐字报告为「我已经进行play，同时已经暂停5S左右」——含
「5S 左右」的口头时刻，但**不是 HUD displayed-time 的逐字原话**；机械判据
取自磁盘：保留帧 0–31，`reported_sim_t = 6.381126`（frame 31），落在
`[2.000000, 10.000000)`，门 1 PASS。round 37 §A.3 对该披露的记载一致。

## N.4 边界

本批未运行 `--finalize`，未重跑 Play，未重算任何指标，未触碰 run 目录或
predecessor hold。A1 是否计为有效 trial、其余九次是否释放，均由 Acceptance
在收到本转录后裁定；**本批不申请 GO**。
