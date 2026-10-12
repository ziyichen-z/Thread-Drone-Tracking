# P1-ENG-JET-001 K1K3K4 交接（Implementation，Claude Opus 子代理，2026-10-02；含 K1K3K4补跑、K1K3K4补跑B、K1K3K4补跑C、K1K3K4补跑D、K1K3K4补跑E、K1K3K4补跑F、K1K3K4全套、K1K3K4全套CPU1、K1K3K4证据整理1A、K1K3K4C1返工、K1K3K4R1注记修补、K1K3K4全套SUB6）

工作项：`P1-ENG-JET-001`（`Workflow: engineering-v1`，D2 接受裁定生效；单候选停点 `K1K3K4`，提案 §7.1）。
合同：`docs/proposals/P1-ENG-JET-001-jetson-onboard-feasibility-probe.md`（§0、§2、§3、§4 AC-1…AC-15、§5、§6、§7 与决策记录）。
执行信封：`docs/authorizations.md` 2026-09-28「P1-ENG-JET-001 — 用户签发 §5 阶段 A 执行信封并答复 §7 (h)(n)…」；
派发前提：同文件 2026-09-29、2026-10-02 两条同项条目。派发：Dispatch-Id `P1-ENG-JET-001-K1K3K4-20261002T190933Z-10df`；
补跑：Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑-20261002T210313Z-98bc`（登记轮次 `K1K3K4补跑`，执行机 Mac mini）；
补跑B：Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑B-20261002T225511Z-8bf6`（登记轮次 `K1K3K4补跑B`，执行机 Mac mini）；
补跑C：Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑C-20261002T233110Z-f493`（登记轮次 `K1K3K4补跑C`，执行机 Mac mini）；
补跑D：Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑D-20261003T001556Z-7e7a`（登记轮次 `K1K3K4补跑D`，执行机 Mac mini，计算在板上）；
补跑E：Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑E-20261003T044648Z-4cdc`（登记轮次 `K1K3K4补跑E`，执行机 Mac mini，计算在板上，经有线 ssh）；
补跑F：Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑F-20261003T161148Z-3166`（登记轮次 `K1K3K4补跑F`，执行机 Mac mini，计算在板上，经有线 ssh 与有线中继）；
全套：Dispatch-Id `P1-ENG-JET-001-K1K3K4全套-20261003T181204Z-f491`（登记轮次 `K1K3K4全套`，执行机 Mac mini，只做离线证据整理与全套跑前核对，零上板）；
全套CPU1：Dispatch-Id `P1-ENG-JET-001-K1K3K4全套CPU1-20261003T205839Z-8433`（登记轮次 `K1K3K4全套CPU1`，执行机 Mac mini，CPU-1 测试改动 + 一次停点全套，零上板）；
证据整理1A：Dispatch-Id `P1-ENG-JET-001-K1K3K4证据整理1A-20261003T213957Z-f760`（登记轮次 `K1K3K4证据整理1A`，执行机 Mac mini，只整理证据、冻结候选、重判自证；零测试、零模型、零上板）。
C1返工：Dispatch-Id `P1-ENG-JET-001-K1K3K4C1返工-20261003T222529Z-257e`（登记轮次 `K1K3K4C1返工`，Opus 子代理，只修报告现状/历史分列、重冻结候选、重判自证；零测试、零模型、零上板）。
R1注记修补：Dispatch-Id `P1-ENG-JET-001-K1K3K4R1注记修补-20261004T005403Z-afd4`（登记轮次 `K1K3K4R1注记修补`，Opus 子代理，落实 R1-1…4 + 零模型 focused + 列精确缺额；零全套、零模型、零回放、零上板；见文末同名节）。
全套SUB6：Dispatch-Id `P1-ENG-JET-001-K1K3K4全套SUB6-20261004T015221Z-e7f4`（登记轮次 `K1K3K4全套SUB6`，Opus 子代理，Mac mini 本机按 SUB:6 跑新候选停点全套 1 次 + 计账 + 重判四项；零上板、零 SR；见文末同名节）。

**派生标识一律运行时解析（不写死）：**

```bash
# 本轮基线 = 本轮实现角色开工提交的父提交（S0 与 SR 冒烟均在本轮任何提交之前执行，执行时 HEAD = 该基线）
BASE=$(git rev-parse "$(git log --format=%H --grep='^P1-ENG-JET-001 K1K3K4 开工')^")
# 补跑基线 = 补跑开工提交的父提交（补跑上板前已提交开工改动，上板运行的代码 = 开工提交）
BASE_RERUN=$(git rev-parse "$(git log --format=%H --grep='^P1-ENG-JET-001 K1K3K4补跑 开工')^")
# 补跑B基线 = 补跑B开工提交的父提交（上板代码 = 补跑B开工提交）
BASE_RERUN_B=$(git rev-parse "$(git log --format=%H --grep='^P1-ENG-JET-001 K1K3K4补跑B 开工')^")
# 补跑C基线 = 补跑C开工提交的父提交（上板代码 = 补跑C开工提交）
BASE_RERUN_C=$(git rev-parse "$(git log --format=%H --grep='^P1-ENG-JET-001 K1K3K4补跑C 开工')^")
# 补跑D基线 = 补跑D 首个提交的父提交（补跑D 无代码上板：板上 S1/S2 运行件与该基线逐文件 sha 一致，见 -assets.json round_d_pre_use_check）
BASE_RERUN_D=$(git rev-parse "$(git log --reverse --format=%H --grep='^P1-ENG-JET-001 K1K3K4补跑D 收工' | head -n 1)^")
# 补跑E基线 = 补跑E 首个收工提交的父提交（补跑E 无代码上板：只下发两个运行脚本；板上运行件与该基线逐文件 sha 一致，见 -assets.json round_e_pre_use_check）
BASE_RERUN_E=$(git rev-parse "$(git log --reverse --format=%H --grep='^P1-ENG-JET-001 K1K3K4补跑E 收工' | head -n 1)^")
# 补跑F基线 = 补跑F 开工提交的父提交（上板代码 = 补跑F 开工提交；返工提交只改桌面机侧 DesktopRelay 与测试，板侧中继/应答器类不变）
BASE_RERUN_F=$(git rev-parse "$(git log --format=%H --grep='^P1-ENG-JET-001 K1K3K4补跑F 开工')^")
# 旧候选规则（K1K3K4全套CPU1 及以前各轮使用，保留原文；送 C1/R1 的停点候选改用下行）= 本文件最后一次提交所在的 main 提交
# CAND=$(git log -1 --format=%H -- docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md)
# 停点候选（K1K3K4证据整理1A 起，提案「1A落实与证据整理」步骤 5）：唯一收工提交；须仅一条、触及本文件、已推送且为 origin/main 祖先
CAND=$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4证据整理1A 收工')
# 全套执行起始版本 = CPU1 开工提交；ledger 机器字段另从 JSON 读取（取样时点不同，见「K1K3K4证据整理1A」版本节）
START_CPU1=$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4全套CPU1 开工')
LEDGER_HEAD=$(python3 -c "import json;print(json.load(open('docs/evidence/P1-ENG-JET-001-ledger.json'))['git_diff_assets_controller_config']['head_at_build'])")
git diff --name-only "$BASE".."$CAND"            # 完整候选文件集
git diff "$BASE".."$CAND"                         # 完整候选 diff
git diff --stat "$BASE".."$CAND" -- Assets controller config   # AC-10：应为空
```

## 状态与结论（先读）

**K1K3K4证据整理1A（2026-10-03，Mac mini，零测试/零模型/零回放/零上板；用户裁定「1A，2环境分列」、接受落实 AC-10 修订 8 / AC-13 修订 3 后）**：按提案「1A落实与证据整理」步骤 1–6 只整理证据：同步 Carrier 不一致索引读法（update 条目从 0 起的索引 `[2, 4, 5, 6, 8, 12, 17, 18, 19, 20]`，索引 2 = `frame_id=3`；仅该条已知 state/reason 同、宽差约 4.8e-8，其余 9 条形态未知，比较后断言未执行）、执行版本两个取样来源、7/18/30 分列及导入错误区分；冻结完整候选范围并按 `--grep` 规则运行时解析基线/候选；在「K1K3K4证据整理1A：候选冻结与停点自证」按 AC 逐条附指针、重判四项。四项**成立**（第 2 项为用户具名例外 + scene006 环境覆盖限制，**不记测试通过**）→ 交接受 `C1@K1K3K4`；C1/R1 结论、AC-14 `UNITY_NA` 附议均未预签，复核可判阻断。原失败、日志、ledger 原字段与计账不改；全套 1/1、det-assoc 2/2、部分回放 2/2 无余额。

**K1K3K4全套CPU1（2026-10-03，Mac mini 离线，零上板；用户选 CPU-1、接受落实 AC-10 修订 6 后）**：`CarrierSelfTest` 两例改为 `DetAssocTracker(spec_path=SPEC, device="cpu")`（静态 AST 核对仅两例构造与导入变化），ledger 补 SUB:5 具名计账；跑前只读核对预计全部在 SUB:2 + SUB:5 A 内，**停点全套已跑一次**：`Ran 2136` / `failures=27, errors=10, skipped=56`。相对 R7 基线：已有 7 条仍在（导入错误 5：四个 eng_sft 报 `tests.fixtures` 缺失、language_k_binding 报 `tests.test_language_selector` 缺失；CSRT 2），18 条未出现（R7 旧 loopback 绑定拒绝 12 条、有缺归档 skip 门 6 条；无逐名 skip 日志，不称修复/通过）；**新增 30 条**：`CarrierSelfTest` 首例 CPU 逐帧比较对 MPS 参考 767 个 update 条目中 10 个不完全相等（证据整理1A 读法：索引 2 = `frame_id=3` 的首个不一致 box 宽差约 4.8e-8、state/reason 同，只适用于该条；其余 9 条形态未知），以及 `test_scene006_probe` 29 条（读码归因本机主树缺 re-anchor/NanoTrack 权重 → `FAIL_WEIGHT_HASH`，相关代码零 diff）。计账：全套 1/1，det-assoc 2/2，部分回放 2/2，NanoTrack 2（上界、读权重 0）/CSRT 2（实例 0）/YOLOE 0/DINOv2 0，`within_envelope: true`。自证第 2 项不成立 → **不交 `C1@K1K3K4`**，交接受角色裁定 IR-24/25 后转用户。详见「K1K3K4全套CPU1执行记录与停点自证」。下文各节保留原文。

**K1K3K4全套（2026-10-03，Mac mini 离线，零上板；用户签 SUB:2、接受落实后）**：按提案「SUB:2 落实：§5 Mac 与 IR-9」执行范围 1 完成证据同步——`-assets.json` 按 IR-21/22 把具名两条控制协议内容命中与真正隔离违规分列（原 `violations`、`true_violation_count = 2`、`ac12_clean: false` 原样），`-relay.json` 按 AC-4 修订 2 / AC-5 修订 1 补链路事件分列与分母，`-ledger.json` 补 SUB:2 具名记录；S1/S2 `STOP`、SR 双标与 IR-20 限制不变。**停点全套未运行**：跑前只读核对发现按合同指定的数据根 `.venv-yoloe` 跑全套时，`tests/test_det_assoc_carrier.py::CarrierSelfTest` 两例会真实加载 SUB:2 未列名的 det-assoc 冻结检测器 2 次（四种具名模型预计均 0），按「预计超任一额度即不跑」停下，一次全套额度未消费、四种模型加载 0。自证第 2 项不成立 → **不交 `C1@K1K3K4`**，交接受角色裁定读法并转用户（「待裁定（K1K3K4全套）」「待用户（K1K3K4全套）」）。详见「K1K3K4全套执行记录与停点自证」。下文各节保留原文。

**K1K3K4补跑F（2026-10-03，Mac mini 派发，计算在 Jetson 板上；用户选 S2 处置 (α′) 后准备 SR (b) 并经有线跑正式 SR）**：新增 SR (b) 真实应答器（真实 `TrackLoop` + 补跑D 方形 TRT FP16 插件；init 框 = 板上首帧检测器自身 target 类最高分框；引擎身份运行时从 `-fastlayer.json`「S1.engines.640」解析、板上复核）与断链分析；正式 SR 4 轮（5 / 5 轮耗尽）：f1-echo **`STOP(RELAY_INTEGRITY)`**（桌面机残留旧会话指针，返工 + 回归测试后重跑），f2-echo / f3-track forward **100% / 0 / 0**，f4 断链轮 10 s / 60 s 两侧不崩溃、零写桥、不补发、0.13 s / 1.94 s 回稳，真实 TrackLoop 在第一次重连以 `GAP` 终止 → **SR = `PASS`**（标 `RESUMED_AFTER_USER_RULING(S1)` + `(S2)`；S1/S2 `STOP` 保留）。AC-12：真实 TrackLoop 的 `gimbal_command.json`（`target_world_m`）命中内容禁键，记 2 条真正违规交 IR-22；逐帧记录键改名交 IR-21。停点全套仍因 SUB:2 未签不能跑 → **不交 `C1@K1K3K4`**。详见「K1K3K4补跑F执行记录」。下文各节保留原文。

**K1K3K4补跑E（2026-10-03，Mac mini 派发，计算在 Jetson 板上，经有线 ssh；用户题 7 选 (α) 后续跑 S2）**：S1 保持 `STOP(FP16_BOX_DIVERGENCE)`、
不重跑；复用补跑D 方形 FP16 引擎（sha 运行时从 `-fastlayer.json`「S1.engines.640」解析并板上复核一致），在 AC-16 环境（`MPLCONFIGDIR` 等）下跑
S2 15 Hz / 30 min，标 `RESUMED_AFTER_USER_RULING(S1)`（账本 2026-10-03「P1-ENG-JET-001 — 用户选题 7 (α)…」）。**S2 = `STOP(FRAME_DROP)`**：
六格 p95 66.99–67.45 ms，末/首比 1.0021（过），热降频 0（频率上限全程不变，tj 最高 51.5 °C），**丢帧 218**（首次 init 冷启动 50 + 每周期固定两帧共 168）。
按 §2.1 停全部后续：SR、S3–S5 记 `NOT_RUN(S2 STOP FRAME_DROP)`，SR (b) 未准备。IR-19 条件满足，已删容器 venv（101,751,706 B）。
一条 TensorRT `[W]` 级引擎计划跨设备告警（补跑D 无，板子两轮间重启过）交接受角色裁定读法（IR-20）。零下载、零安装、零引擎导出。
**不交 `C1@K1K3K4`**；交接受角色记录 S2 STOP 后转用户。详见「K1K3K4补跑E执行记录」。下文各节保留原文。

**K1K3K4补跑D（2026-10-03，Mac mini 派发，计算在 Jetson 板上；系统栈按 AC-2 修订 6 跑 S1）**：IR-16 (c) 环境变量就位、IR-16 (d) 装后清理
（删 `wheels/sub1` 23 个已装轮子 2,836,341,094 B，未动 sysvenv）后，从冻结 `.pt`（导出前后 sha 一致）导出两版 TRT FP16 引擎（方形 640 / 矩形
480×640，各约 6.2 min），a7 前 320 帧计时与 frozen-V 比对，并跑 `trtexec`。全程无 `no kernel image` 等不兼容报错。**S1 = `STOP(FP16_BOX_DIVERGENCE)`**：
方形引擎 `update` p95 59.29 ms（n = 320，≤ 200 ms 门过；`within_50ms = false`），一致性不过（帧 0…49 计数不一致 3、帧 1…320 配对最大差 0.0992 > 1e-3、
两侧未配对 66）。按 §2.1 停止总则，S2、SR、S3–S5 记 `NOT_RUN(S1 STOP FP16_BOX_DIVERGENCE)`，S2 未回放；零下载、零安装、零到板传输。
**不交 `C1@K1K3K4`**；交接受角色记录 STOP 并转用户二选一 (α)/(β)（「待用户（补跑D）」1），新读法 IR-17…19 见「待裁定（补跑D）」。详见
「K1K3K4补跑D执行记录」。下文各节保留原文。

**K1K3K4补跑C（2026-10-02，Mac mini；系统栈补装 + 装后验证）**：按「SUB:3 落实」方式补装成功——21 个依赖逐个 `pip download --no-deps`
（sha256 锁定，21/21 一致，2,316,069,213 B），复用留存的官方 cu130 torch/torchvision，`--no-index --find-links` 离线安装；既有 4 包离线
`--no-deps` 重装，新增 onnx/protobuf（AC-10 修订 2）。**装后验证未过**：`torch.cuda.get_arch_list()` = sm_80/90/100/110/120 + compute_120，
**不含 `sm_87`**；CUDA matmul 读回、torch 与系统 TensorRT 10.16 同进程/干净进程建引擎三项通过。按题 4「任一失败即停下回用户改来源，
不在信封内换源」**停在 S1 之前**：引擎导出 0 次，S1/S2 仍 `NOT_RUN(PATH_UNAVAILABLE(system-torch))`（形状待 IR-16 确认）。STOP 码未命中。
附加只读诊断（cuDNN 卷积、CUDA nms）均通过，只供裁定。**不交 `C1@K1K3K4`**；读法交接受角色（「待裁定（补跑C）」IR-16），是否接受
sm_80 同主版本兼容读法或改来源交用户（「待用户（补跑C）」）。详见「K1K3K4补跑C执行记录」。下文各节保留原文。

**K1K3K4补跑B（2026-10-02，Mac mini；系统栈 + SUB:1）**：在板上建好 `--system-site-packages` venv `~/eng-jet/sysvenv`，按题 4 从官方
cu130 索引取回 torch 2.9.1+cu130 / torchvision 0.24.1（sha 一致）；但用 pip 24.0 `install --dry-run --report --no-cache-dir` 解析依赖时，
pip 把 22 个依赖轮子体（2,318,455,950 B）完整取回后丢弃。SUB:1 已计下载 = 轮子 2,838,727,831 B / 保守收包 3,093,609,695 B（上限 3.5 GB），
补齐安装还需再取回 2,316,069,213 B，必超上限 → **按「任一上限将超即停」停在安装前**：torch 未装、题 4 安装后验证未执行、S1/S2 仍
`NOT_RUN(PATH_UNAVAILABLE(system-torch))`，未换源、未 `--no-deps` 变通、未 sudo/apt。STOP 码未命中。**不交 `C1@K1K3K4`**；交用户扩 SUB:1
下载上限（「待用户（补跑B）」），读法交接受角色（「待裁定（补跑B）」）。详见「K1K3K4补跑B执行记录」。下文各节保留原文。


**K1K3K4补跑（2026-10-02，Mac mini）**：用户所选容器路径（提案「S1/S2 容器栈落实」）**在本板走不通**——容器内 torch CUDA 可用、
冻结 `.pt` → ONNX 成功，但镜像自带 TensorRT 10.13.2.6 建 FP16 引擎报 `Target GPU SM 87 is not supported by this TensorRT release`
（容器 `trtexec --fp16` 复证同错）。按 §2.1「不自行修复环境」与派发「不变通」，S1/S2 记
`NOT_RUN(PATH_UNAVAILABLE(container-tensorrt-sm87))`，未换镜像、未拼接宿主 TensorRT 10.16、未装合同外系统包；矩形引擎未尝试（同一限制）。
STOP 码未命中。**仍不交 `C1@K1K3K4`**：S1/S2 无读数、正式 SR 待 (h)、停点全套待额度。详见「K1K3K4补跑执行记录」「待裁定（补跑）」
「待用户（补跑更新）」。下文「首派」各节保留原文。

**首派（原文）：**

- **本轮不交 `C1@K1K3K4`**，交接受角色裁定后转用户：S0 `PASS`；**S1/S2 无法按合同路径执行**——板上系统 Python 没有 torch
  （合同 §3.1/§5 假设 `--system-site-packages` 复用 NVIDIA torch），信封又写明「不重装 torch」、pip ≤ 300 MB，板上唯一 torch 在
  未经合同授权的 Docker 镜像内且属另一套 CUDA/TensorRT。按 §2.1「不自行修复环境」记 `NOT_RUN(PATH_UNAVAILABLE(system-torch))`（IR-3），
  路径选择交用户（IR-4、待用户 1）。SR 正式轮 `NOT_RUN(待用户 (h))`（有线未接）；1 轮 `TAILSCALE_SMOKE` 已跑（回声应答，非结论）。
  S3–S5 `NOT_RUN(阶段 B 信封未签)`。
- 冒烟发现一处中继实现缺陷（桌面机对时在链路停顿后请求/应答永久错位），已修复并附红绿回归（「冒烟发现与修复」）。
- 停点全套 Python 测试**未跑**：全套会在本机加载 NanoTrack/YOLOE/DINOv2/CSRT 模型（FRAME-001 先例须用户具名额度），与本信封
  「Mac 零模型」冲突（IR-9、待用户 2）；本轮只跑 `tests/test_eng_jet_*.py` focused（36/36 通过）。
- §4.3.1 四项条件因此**不全成立**（见「停点自证」），候选不送核对轮；裁定落实后由下一实现派发补跑 S1/S2（及正式 SR，若链路已接）再自证。

## 每步执行记录（AC-14）

| 步 | 机器 | 时间（UTC） | 执行时 `git rev-parse HEAD` | 命令/原始记录 |
|---|---|---|---|---|
| frozen-V 复制 | Mac mini → 本机（只读 scp；mini 未运行任何程序） | 2026-10-02 19:12 前后 | `$BASE` | `scp macmini:TetheredDroneTracking/outputs/eng-det/dets/frozen-V.jsonl.gz outputs/eng-det/dets/`；sha 与 `docs/evidence/P1-ENG-ACQ-001-assets.json` 一致后 `chmod 444` |
| S0 | Jetson（`ssh Jetson`，Tailscale）；判定在桌面机（用户 MacBook Air） | 19:13:17–19:22:32（`tegrastats` 19:16:15–19:21:15） | `$BASE` | `python -m tools.eng_jet.env_probe collect / tegrastats-fetch / build`；原文 `outputs/eng-jet/P1-ENG-JET-001/s0/`，板上副本 `~/eng-jet/logs/` |
| S1 / S2 | — | 未运行 | — | `NOT_RUN(PATH_UNAVAILABLE(system-torch))` |
| SR 冒烟 | 桌面机（回放器 + 桌面中继）↔ Jetson（板侧中继 + 回声） | 19:32:48–19:44:36（数据流 19:32:59–19:40:01） | `$BASE`（运行的是当时未提交工作树代码，代码束 sha 见 `-relay.json` `tailscale_smoke.code_at_smoke`） | 命令逐字见 `-relay.json` `tailscale_smoke.commands`；原始收据 `outputs/eng-jet/P1-ENG-JET-001/sr/tailscale-smoke-1/{desktop,board}/` |
| S3–S5 | — | 未运行 | — | `NOT_RUN(阶段 B 信封未签)` |
| 补跑：开工改动提交 | Mac mini | 21:12 前后 | `$BASE_RERUN` → 开工提交 | `git log --grep='^P1-ENG-JET-001 K1K3K4补跑 开工'` |
| 补跑：S1/S2 容器路径（状态核验、pip、到板件、导出 1 次失败、trtexec 复证、栈读数、清单） | Jetson（`ssh Jetson`，Tailscale）；桌面端 Mac mini | 21:05:16–21:17:53、21:19:09–21:19:40、21:20:46–21:20:48 | 开工提交（`$BASE_RERUN` 的子提交） | 见「K1K3K4补跑执行记录」；原始日志 `outputs/eng-jet/P1-ENG-JET-001/s1s2/`，板上副本 `~/eng-jet/logs/s1s2/` |
| 补跑B：只读核验、系统 venv、SUB:1 取回 torch/torchvision、依赖干跑（停于额度将超）、sha 复核、清单 | Jetson（`ssh Jetson`，Tailscale）；桌面端 Mac mini | 22:58:22–23:00:25、23:04:47–23:04:54、23:05:04–23:05:27、23:05:33–23:07:08、23:08:07–23:08:09、23:08:47–23:08:49、23:09:27–23:09:28 | 22:58–23:00 只读核验时为 `$BASE_RERUN_B`；其后为补跑B开工提交 | 见「K1K3K4补跑B执行记录」；原始日志 `outputs/eng-jet/P1-ENG-JET-001/s1s2-system/`，板上副本 `~/eng-jet/logs/s1s2-system/` |
| 补跑D：只读核验、资产使用前 sha 复核、`wheels/sub1` 清理、两版引擎导出、S1 方形/矩形、`trtexec` ×2、读数取回、清单扫描 | Jetson（`ssh Jetson`，Tailscale）；桌面端 Mac mini | 00:17:50–00:35:25（2026-10-03；导出 00:20:11–00:32:50，S1 00:32:53–00:34:04） | `$BASE_RERUN_D`（无代码上板；板上运行件与之逐文件 sha 一致） | 见「K1K3K4补跑D执行记录」；原始日志 `outputs/eng-jet/P1-ENG-JET-001/s1s2-system-d/`，板上副本 `~/eng-jet/logs/s1s2-system-d/` |
| 补跑E：只读核验、资产/引擎使用前 sha 复核、两个运行脚本下发、S2 15 Hz/30 min、外部写入核查、TRT 告警只读诊断、容器 venv 删除（IR-19）、清单扫描、读数取回 | Jetson（`ssh jetson@192.168.8.2` 有线，`StrictHostKeyChecking=yes`）；桌面端 Mac mini | 04:48:25–05:21:28（2026-10-03；S2 04:50:25–05:20:34） | `$BASE_RERUN_E`（无代码上板；板上运行件与之逐文件 sha 一致） | 见「K1K3K4补跑E执行记录」；原始日志 `outputs/eng-jet/P1-ENG-JET-001/s2-system-e/`，板上副本 `~/eng-jet/logs/s2-system-e/` |
| 补跑F：只读核验、SR 到板件上传与使用前 30 件 sha 复核（含方形引擎）、应答器预检、正式 SR 4 轮（f1-echo 返工轮、f2-echo、f3-track、f4-track-drops）、读数取回、清单扫描、对时只读查询 | Jetson（`ssh jetson@192.168.8.2` 有线，`StrictHostKeyChecking=yes`）；桌面端 Mac mini（回放器 + 桌面机中继，有线 192.168.8.1） | 16:16:04–17:02:23（2026-10-03；SR 数据窗 16:29:48–17:00:05） | `$BASE_RERUN_F` 的子提交（开工提交；f2 起桌面机侧为返工提交） | 见「K1K3K4补跑F执行记录」；原始日志 `outputs/eng-jet/P1-ENG-JET-001/sr-f/`，板上副本 `~/eng-jet/logs/sr-f/` |
| 全套：只读额度核对（解释器/模型文件/数据根门/输出余量）、证据同步（`evidence sync-full-suite`、`ledger add`/`build`）、focused `test_eng_jet_*` | Mac mini 本机（零上板、零 ssh） | 18:13–18:24（2026-10-03；跑前核对记录 18:21:21Z） | 本轮开工时 HEAD = supervisor 派发登记提交（`git log --grep='^P1-ENG-JET-001 K1K3K4全套 supervisor 派发登记'` 运行时解析）；证据同步代码 = 本轮收工提交 | 见「K1K3K4全套执行记录与停点自证」；跑前核对原文 `outputs/eng-jet/P1-ENG-JET-001/ledger-events.jsonl`（`mac_full_suite_precheck`），已汇入 `-ledger.json`「dimensions.mac.sub2.prechecks」 |
| 全套CPU1：CPU-1 两处测试改动与 AST 静态核对、跑前只读核对（`ledger add mac_full_suite_precheck`）、开工提交、**一次停点全套**、计账（`ledger add`/`build`） | Mac mini 本机（零上板、零 ssh） | 21:00–21:20（2026-10-03；跑前核对记录 21:06:33Z；全套 21:06:48–21:10:46Z） | 执行起始版本 = 本轮开工提交（`$START_CPU1`，按主题运行时解析）；ledger `full_suite_run_items[].tested_head` / `git_diff_assets_controller_config.head_at_build`（`$LEDGER_HEAD`）为另一取样时点（其提交时间在全套窗口内，不是跑前 HEAD 采样），两者 tests/tools/controller/Assets/config 零 diff（证据整理1A 读法，见同名节） | 见「K1K3K4全套CPU1执行记录与停点自证」；日志 `docs/evidence/P1-ENG-JET-001-full-suite.log` |
| 证据整理1A：只读核对日志/JSON/git/关联代码、改交接与报告叙述/索引、状态板交接行 | Mac mini 本机（零测试、零模型、零回放、零上板、零 ssh） | 21:40–22:10 前后（2026-10-03） | 开工时 HEAD = supervisor 派发登记 requested 提交（`git log --format=%H --grep='^P1-ENG-JET-001 K1K3K4证据整理1A supervisor 派发登记：requested'` 运行时解析；其后 started 登记提交只改派发登记）；产物 = 收工提交（`$CAND`） | 见「K1K3K4证据整理1A：候选冻结与停点自证」 |
| 补跑C：只读核验、代码更新件上板、SUB:1 依赖逐个取回、onnx/protobuf 取回、离线安装、verify（未过→停）、附加诊断、读数取回、清单 | Jetson（`ssh Jetson`，Tailscale）；桌面端 Mac mini | 23:33:29–23:33:30、23:37:18–23:44:16、23:44:24–23:44:27 | 23:33 只读核验时为 `$BASE_RERUN_C`；其后为补跑C开工提交 | 见「K1K3K4补跑C执行记录」；原始日志 `outputs/eng-jet/P1-ENG-JET-001/s1s2-system-c/`，板上副本 `~/eng-jet/logs/s1s2-system-c/` |

板上占用墙钟合计 1,263 s（首派）+ 790 s（补跑）+ 253 s（补跑B）+ 422 s（补跑C）+ 1,055 s（补跑D，首末连续计时含间隙）+ 1,983 s（补跑E，同口径）+ 2,779 s（补跑F，同口径）= 8,545 s（`-ledger.json` `board_wall_clock`）。首派收工时板上无本轮进程（19:44Z）；补跑收工时板上无本项容器（`docker ps -a` 空）、无 tegrastats 进程（21:19:34Z）。

## AC-n 逐条证据指针（自证）

| AC | 自证 | 证据指针 |
|---|---|---|
| AC-1 | 满足（待 IR-1、IR-2 两条读数来源等价性裁定） | artifact: `docs/evidence/P1-ENG-JET-001-env.json`（`checks` 6 项全过 → `PASS`；`readings` 15 条原文含 `nvpmodel_q`、`nv_boot_control`、`gpu_devfreq`、`cpu_cpufreq`、`default_target`、`display_manager`、`dmesg_nvmap`、`free_m`、`swap`、`disk`、`nvcc_version`、`python_import_tensorrt_torch`；`tegrastats_idle` n = 298；`not_executed` 列 `nvpmodel -m`/`systemctl isolate`/`jetson_clocks`/sudo）；test: `tests/test_eng_jet_bench.py` `S0Verdict`、`tests/test_eng_jet_guards.py` `NoSystemSettingChanges` |
| AC-2 | **不满足**（补跑E：S1 保持 `STOP`、未重跑，用户题 7 选 (α) 只放行后续步骤、不改 S1 verdict；补跑D：系统栈实跑，S1 = `STOP(FP16_BOX_DIVERGENCE)`——两版引擎 sha/导出参数/TRT 10.16.2.10、320 帧四分项、`within_50ms`、IoU 分布、逐帧最大差直方图、不一致帧清单均已留证，但 verdict 非 `PASS`，AC-2 记不满足、待用户 (α)/(β)；补跑C：torch 栈已装，装后验证 arch list 不含 sm_87 → 停在 S1 前，`NOT_RUN(PATH_UNAVAILABLE(system-torch))`，引擎导出 0；补跑B：S1 `NOT_RUN(PATH_UNAVAILABLE(system-torch))`，SUB:1 下载额度将超、torch 未装成；补跑为 `container-tensorrt-sm87`；按 §2.1 不得记满足） | artifact: `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1」（补跑D：`engines.640` / `engines.480x640` 的 `export`、`s1`、`trtexec`；`tegrastats_s1_window`；前轮在 `history`；`export_attempts`、`tensorrt_cross_check`、`container_setup`）与 `docs/evidence/P1-ENG-JET-001-env.json`「s1s2_container_stack」；cmd: `python -m tools.eng_jet.fastlayer_bench --out /work/results export --imgsz 640`（容器内）；test: `tests/test_eng_jet_bench.py` `S1Comparison`、`InjectionOnly`、`TrtexecParse` |
| AC-3 | **不满足**（补跑E：S2 已实跑，六个 5 min 格 p50/p95/max、GPU/CPU 频率上限与当前频率、温度、丢帧数、tegrastats 功耗与 verdict 齐全（`-fastlayer.json`「S2.runs.15hz.bins」「tegrastats_bins」），标 `RESUMED_AFTER_USER_RULING(S1)`；但 verdict = `STOP(FRAME_DROP)`（丢帧 218），STOP 步骤不记满足；30 Hz 未测（S1 p95 59.29 > 33 ms，`plan.add_30hz=false`）；补跑D：S2 `NOT_RUN(S1 STOP FP16_BOX_DIVERGENCE)`，未回放；补跑C/补跑B：S2 `NOT_RUN(PATH_UNAVAILABLE(system-torch))`；补跑为 `container-tensorrt-sm87`） | artifact: 同上「S2」；test: `tests/test_eng_jet_bench.py` `S2Pieces`（AC-3 修订 1 读法） |
| AC-4 | 补跑F：正式 forward 两轮（f2-echo、f3-track，各 1,500 包、全程零链路事件）完整率 100%、顺序违反 0、指向不完整包 0，到达时延与对时偏差中位/漂移已报告，SR forward `PASS`；f1-echo 返工轮 `STOP(RELAY_INTEGRITY)` 原样分列；冒烟只在 tailscale_smoke。是否满足由核对/复核判定。以下为补跑E 原文：`NOT_RUN(S2 STOP FRAME_DROP)`（补跑E；不记满足。§7 (h) 已于 10-03 接好有线直连；此前 `NOT_RUN(待用户 (h))` 为当时记录） | artifact: `docs/evidence/P1-ENG-JET-001-relay.json`「forward」「rework_rounds」；冒烟只在「tailscale_smoke」；test: `tests/test_eng_jet_relay.py::LoopbackTwoProcess::test_atomic_publish_order`、`DesktopStalePointer`；`tests/test_eng_jet_track_responder.py::SrForwardLine` |
| AC-5 | 补跑F：回声（f2，n = 1,500）与真实 TrackLoop（f3，回程 n = 29）两模式回程 p50/p95/max、端到端、`capture_age_s`/`load_elapsed` 对照 `T_STALL_S`/`T_pub`、真实 `frame_age_ms` 分布与超 `T_stall` 比例（0）均已报告；init 框来源 = 板上首帧检测器 target 类最高分框（`return.track.init_detection`）。是否满足由核对/复核判定。补跑E 原文：`NOT_RUN(S2 STOP FRAME_DROP)`（SR (b) 真实应答器未准备；此前 `NOT_RUN(待用户 (h))`） | artifact: 同上「return」；cmd: `python -m tools.eng_jet.track_responder`（板上）、`tools/eng_jet/relay.py` `EchoResponder`；test: `ReplayAndEcho`、`tests/test_eng_jet_track_responder.py`（`SelectInitBox`、`ResponderInProcess`） |
| AC-6 | 补跑F：f4 软件定时断链 10 s、60 s 各一次（IR-8 / D5；双通道与对时同断），两侧存活（退出码全 0）、断链期间板侧写桥 0、恢复后缺口 49 / 299、latest 帧差 50 / 300、TrackLoop 第一次重连 `GAP` 终止（不重播种、继续存活）、回稳 0.134 / 1.940 s（预注册读法 `relay.RECOVERY_*`）。是否满足由核对/复核判定。补跑E 原文：`NOT_RUN(S2 STOP FRAME_DROP)`（此前 `NOT_RUN(待用户 (h))`） | artifact: 同上「disconnect」；重连/不补发实现：`DesktopRelay`；test: `DesktopNoBacklog`、`test_clock_sync_recovers_after_stall`、`tests/test_eng_jet_track_responder.py`（`LoopbackTrackWithDrop`、`RecoveryRule`、`ResponderInProcess.test_gap_terminates_without_reseed`） |
| AC-7 | `NOT_RUN(阶段 B 信封未签)` | artifact: `docs/evidence/P1-ENG-JET-001-vlm.json` |
| AC-8 | `NOT_RUN(阶段 B 信封未签)` | artifact: `docs/evidence/P1-ENG-JET-001-quant-equivalence.json` |
| AC-9 | `NOT_RUN(阶段 B 信封未签)` | artifact: `docs/evidence/P1-ENG-JET-001-coresidency.json` |
| AC-10 | 满足（累计，补跑F后：板上墙钟 8,545 s ≤ 28,800 s、SR 5 / 5 轮（冒烟 1 + 正式 4，每轮 ≤ 61,704,978 B ≤ 100 MB；**轮数已耗尽**）、到板 18,870,709 B（本轮 554,765 B）、引擎导出 3 次（本轮 0）、板上 pip 7 包不变、SUB:1 不变、板上磁盘 5,163,883,873 B ≤ 13 GB、模型下载 0、VLM 查询 0、Mac pip/模型 0（outputs 70,218,799 B）、`git diff` 对 Assets/controller/config 为空；补跑E后原文：板上墙钟 5,766 s ≤ 28,800 s、到板 18,315,944 B（本轮 1,469 B 运行脚本）、引擎导出 3 次（本轮 0）、板上 pip 7 包 / 242,752,639 B（不变）、SUB:1 23 包 / 下载 5,616,357,711 B（不回退）/ 新增盘重计 4,829,972,625 B ≤ 8 GB、板上磁盘 5,070,463,807 B ≤ 13 GB（容器 venv 已删）、SR 1/5 轮、模型下载 0、Mac pip/模型 0（outputs 49,668,939 B）、`git diff` 对 Assets/controller/config 为空；补跑D后原文：板上墙钟 3,783 s、引擎导出 3 次（容器轮 1 + 本轮 2，本轮 375.4 s / 367.9 s ≤ 20 min）、到板 18,314,475 B（本轮 0）、板上 pip 7 包 / 242,752,639 B、SUB:1 23 包 / 下载 5,616,357,711 B（不回退）/ 新增盘按 IR-16 (d) 清理后重计 4,925,758,840 B ≤ 8 GB、板上磁盘 5,166,250,549 B ≤ 13 GB、模型下载 0、Mac pip/模型 0、`git diff` 对 Assets/controller/config 为空；补跑C后原文：板上墙钟 2,728 s、到板 18,314,475 B、板上 pip 7 包 / 242,752,639 B（含 onnx/protobuf，AC-10 修订 2）、板上磁盘 7,783,123,942 B ≤ 13 GB、SUB:1 23 包 / 下载保守 5,616,357,711 B ≤ 6.5 GB / 新增盘 7,542,632,760 B ≤ 8 GB、引擎导出 0、模型下载 0、Mac pip/模型 0，`git diff` 对 Assets/controller/config 为空；补跑B后原文：板上墙钟 2,306 s、到板 18,114,560 B、板上磁盘 774,399,627 B ≤ 13 GB 生效值、SUB:1 23 包 / 下载保守 3,093,609,695 B ≤ 3.5 GB / 新增盘 533,908,445 B，见 `dimensions.sub1_torch`；以下为补跑时原文） | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`（`within_envelope: true`；模型下载 0、板上 pip 5 包 202,869,979 B（保守口径，逐轮子 sha）、量化主机 0、到板 17,920,000 B、SR 1 轮（TAILSCALE_SMOKE）、板上墙钟 2,053 s、引擎导出 1 次 9.7 s、VLM 查询 0、板上磁盘 240,491,182 B、Mac pip/模型 0；`git_diff_assets_controller_config.empty: true`，基线取首派 `4cbd7bd`）；cmd: `git diff --stat "$BASE".."$CAND" -- Assets controller config` |
| AC-11 | 满足（补跑F 使用前板上 30/30 一致：SR 到板件 27 件对开工提交、last.pt/freeze 2 件、方形引擎对 `-fastlayer.json`「S1.engines.640.export.sha256」（运行时解析），`-assets.json`「round_f_pre_use_check」；应答器每轮开跑前再核引擎 sha；SR 回放帧四轮逐帧对 FAST-002 参照一致，`round_f_sr_frames`；补跑E 使用前板上逐文件复核 335/335 一致：13 件对本机 HEAD、a7 帧 0..320、方形引擎对 `-fastlayer.json`「S1.engines.640.export.sha256」，`-assets.json`「round_e_pre_use_check」；补跑D 使用前板上逐文件复核 334/334 一致：S1/S2 用到的 13 件对本机 HEAD、a7 帧 0..320 对 dataset-frames 参照，`-assets.json`「round_d_pre_use_check」；阶段 A 实际使用的资产；补跑在 mini 重核） | artifact: `docs/evidence/P1-ENG-JET-001-assets.json`（`bundle_s1s2` 逐文件 sha；`.pt`、`freeze.json`、`frozen-V.jsonl.gz` sha/体积全一致；a7 帧 0..320 共 321 帧与 0..1499 共 1,500 帧逐帧对 FAST-002 dataset-frames 参照 sha 全一致；阶段 B 资产 `NOT_USED(阶段 B 信封未签)`，未读未上板） |
| AC-12 | 按 AC-12 修订 2 分列（补跑F 后重扫：37,714 文件，机械违规 3 = `home/cuda-cache/index`（具名驱动缓存，IR-17 单列）+ **内容禁键 2 条**（`runtime/sr-f/{f3-track,f4-track-drops}/gimbal_command.json` 的冻结控制协议字段 `target_world_m`，真实 TrackLoop 写出，非真值）→ 真正违规 2，读法交 IR-22；`ac12_clean: false` 原样；本轮受保护根零写入；补跑E 后重扫：33,345 文件，机械违规 1 = `home/cuda-cache/index`（具名驱动缓存文件名命中，IR-17 单列）、真正违规 0、内容禁键命中 0；`ac12_clean: false` 原样保留，分列见 `-assets.json`「board_manifest.ac12_split」，原扫描指针 `board_manifest_previous_round`；本轮受保护根零写入；AC-12 是否满足由复核判定；以下补跑D原文：**待裁定（IR-17）**（补跑D后重扫：35,102 文件，机械扫描违规 1 = `home/cuda-cache/index` 路径名命中——CUDA 驱动 JIT 缓存的二进制索引文件，由 IR-16 (c) 把 `CUDA_CACHE_PATH` 指到 `~/eng-jet/home/` 产生，非本项工件、无 JSON 内容；内容禁键命中 0；`ac12_clean: false` 原样保留，读法交 IR-17；`~/eng-jet` 之外新写 `~/.cache/matplotlib/fontlist-v330.json` 见 IR-18；补跑C后重扫：32,642 文件、违规 0；`sysvenv/`、`venv/` 第三方包树在证据中按前缀汇总、全量清单原文另存 outputs 记 sha；本轮受保护根零写入；`~/eng-jet` 之外的两处运行时缓存写入见「K1K3K4补跑C执行记录」；补跑B后原文：3,968 文件、违规 0、`sysvenv/` 第三方包名命中单列；本轮受保护根零写入；以下为补跑时原文） | artifact: `docs/evidence/P1-ENG-JET-001-assets.json`「board_manifest」（2,937 文件、违规 0、`ac12_clean: true`；`venv/` 第三方包名命中 16 条单列 `third_party_name_hits`，见 IR-12）与「protected_roots_zero_write」（补跑派发时刻 21:03:13Z 起主树 `runtime/` 与 mini 数据根修改均 0）；test: `tests/test_eng_jet_guards.py` |
| AC-13 | 补跑F：报告 §1 SR 行记 `PASS` 并标 `RESUMED_AFTER_USER_RULING(S1)`/`(S2)` 各指账本，S3–S5 现行 `NOT_RUN(阶段 B 信封未签)`、旧原因留作历史，§2f 列 SR 读数与返工轮，§3 Q4/§4 建议/§6 待用户现状已同步；补跑E 原文：满足（补跑E：报告 §1 记 S2 `STOP(FRAME_DROP)` 并标 `RESUMED_AFTER_USER_RULING(S1)`、指向账本条目标题，SR/S3–S5 `NOT_RUN(S2 STOP FRAME_DROP)`，§2e 列读数，链路现状已同步；补跑D：报告 §1 verdict 表记 S1 `STOP(FP16_BOX_DIVERGENCE)` 与后续 `NOT_RUN(S1 STOP …)`，§2d 列读数与差异证据，未标 `RESUMED_AFTER_USER_RULING`；报告如实给出 NOT_RUN 与无数字项） | artifact: `docs/evidence/P1-ENG-JET-001-report.md` |
| AC-14 | 执行记录已写（上节，含补跑D、补跑E 行）；`UNITY_NA` 申请待复核角色附议 | artifact: `docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md`「每步执行记录」「K1K3K4补跑执行记录」；理由：零 Play、Unity 零改动，硬件证据即板上实测文件 |
| AC-15 | 满足（补跑F：`pending_user.h` effect 同步为正式 SR 已在有线链路执行，旧状态留作历史） | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`「pending_user」：(h) answered（09-28、10-02、10-03 有线直连成功、10-03 known_hosts 授权四条标题）、(n) answered（09-28）、(i)(j)(k)(l)(m) unanswered 且对应动作零执行 |
| AC-16 | 满足（补跑F：四轮板上 Python 进程（中继/回声/真实应答器）启动前 env.sh 设定，`env-actual.txt` 四轮 MPLCONFIGDIR/YOLO_*/CUDA_CACHE_PATH 一致、LD_LIBRARY_PATH unset；marker 后 `~/eng-jet` 外新写入仅 `~/.local/state/wireplumber/restore-stream`（ssh 登录会话服务，IR-18 同源，非本项进程）；`-env.json`「sr_system_stack_f.ac16」；补跑E 起执行：`MPLCONFIGDIR=/home/jetson/eng-jet/home/mpl` 与 `YOLO_CONFIG_DIR`/`CUDA_CACHE_PATH`、`YOLO_AUTOINSTALL=false YOLO_OFFLINE=true`、unset `LD_LIBRARY_PATH` 实际环境记录；S2 启动前 marker 之后 `~/eng-jet` 外新写入 0；既有外部缓存未删） | artifact: `docs/evidence/P1-ENG-JET-001-env.json`「s2_system_stack_e.env.ac16」「outside_eng_jet」；`outputs/eng-jet/P1-ENG-JET-001/s2-system-e/env-actual.txt`、`outside-newer.txt` |

## 停点自证（workflow §4.3.1 四项）

1. 实现范围与接口冻结：阶段 A 代码（`tools/eng_jet/` 七个模块）已齐；但 S1/S2 的执行路径待裁定，候选证据不完整 → **不成立**。
2. 相称测试：focused `tests/test_eng_jet_*.py` 36/36 通过（`docs/evidence/P1-ENG-JET-001-focused-tests.log`）；停点全套未跑（IR-9）→ **不成立**。
3. 已知 Unity 失败：不适用（零 Unity）。
4. 复核范围、状态板、候选提交与未验证风险：已更新（本文件、状态板交接行）。

结论：不送 `C1@K1K3K4`；回接受角色裁定 IR 并转用户（待用户 1、2）。

**补跑后重判**：1 不成立（S1/S2 在已授权的两条执行栈上都无读数，SR (b) 真实应答器依赖 S1 引擎仍未实现）；2 不成立（focused
`tests/test_eng_jet_*.py` 41/41 通过，`docs/evidence/P1-ENG-JET-001-focused-tests.log`；停点全套仍待用户额度，IR-9）；3 不适用；4 已更新。
不送 C1。

## 冒烟发现与修复

- **缺陷**：桌面机 UDP 对时在链路停顿后，板侧迟到的旧应答滞留在接收队列，旧实现每次只收一个并比对 `seq`，从此请求/应答
  永久错位、不再产生有效样本（冒烟：开始后约 34 s 后无样本）。
- **修复**：`tools/eng_jet/relay.py` `recv_matching`（丢弃旧应答直至 `seq` 匹配或超时），`DesktopRelay.sync_loop` 改用之；
  板侧 `BoardRelay`/`EchoResponder`、消息帧与 `common.py` 未改（diff 对象：冒烟代码束内 `tools/eng_jet/relay.py` 与候选同名文件）。
- **红绿**：`LoopbackTwoProcess.test_clock_sync_recovers_after_stall`（板侧进程 SIGSTOP 4 s 后恢复，要求恢复后 ≥ 3 个有效对时）——
  对冒烟时版本（从代码束解出）**红**（恢复后有效对时 0）；修复后**绿**。另加 `SyncReplyMatching` 两例单元测试。
- 冒烟读数按冒烟时版本保留，不重跑（Tailscale 冒烟额度 1/1 已用）。

## 待裁定（实现读法，交接受角色；实现角色对提案只读，故写在此处）

- **IR-1（AC-1，`dmesg | grep -i nvmap`）**：`kernel.dmesg_restrict = 1`、无免密 sudo，非 root `dmesg` 被拒（原文保留）。改取 adm 组可读的
  `journalctl -k -b 0 | grep -i nvmap`（本次启动全部内核日志，1,136 行），另记 `/var/log/kern.log` 命中 81 行。读作等价。
  若不等价：请用户在板上执行一次 `sudo dmesg | grep -i nvmap` 并回传原文（只读）。
- **IR-2（AC-1，`sudo nvpmodel -q`）**：以非 root `nvpmodel -q`（只读查询）取当前模式。读作等价。
- **IR-3（S1/S2 verdict 形式）**：板上系统 Python 无 torch，合同执行路径不存在。闭集里没有对应的 STOP 原因码，取 NOT_RUN 闭集的
  `PATH_UNAVAILABLE(system-torch)`；`NOT_RUN` 不停后续步骤，故照常跑了只依赖中继、不依赖 S1 产物的 SR 冒烟（回声应答）。
  请裁定该形式与「继续冒烟」是否成立。
- **IR-4（S1/S2 执行路径，须用户定）**：见「待用户 1」。合同 §6「本栈（JP7.2/CUDA 13.2/TRT 10.16）」与 §5「复用 NVIDIA torch」两处
  字面需随用户选择作 CLARIFY。
- **IR-5（S1「同一 init 框」）**：读作 `docs/evidence/P1-ENG-FAST-002-latency.json` `frames.init_box`（G-7 当时取自真值索引的框），
  经命令行参数传入，板上不放任何真值文件。若应改用检测器自身 `target` 类最高分框（同 SR (b)），请裁定。
- **IR-6（S1 帧与比对窗口）**：init 于 a7 帧 0，计时帧 1..320 的 `update`（n = 320，同 G-7）；检测级比对覆盖帧 0..320（超集）；
  「前 50 帧」= 帧 0..49（同 G-7 `images[:50]`）；配对 = 同类贪心 IoU ≥ 0.5，最大差取配对框四坐标归一化绝对差的最大值，未配对计入
  不一致帧清单。
- **IR-7（S2）**：「频率无降频」读作上限频率（GPU devfreq `max_freq`、各核 `scaling_max_freq`）低于首样本或任一 cooling device
  `cur_state` 由 0 变非 0；DVFS 下 `cur_freq` 随负载变化不算降频。末/首 5 min p95 比值超 1.2 在 STOP 列无原因码，线束记
  `UNRESOLVED(P95_RATIO_OVER)` 待裁定，不自造码。
- **IR-8（SR 完整率分母与断链方式）**：冒烟中真实链路停顿使 12 包在途整包丢失（板上零成员、零发布；「不缓存补发」的直接后果），
  完整率 1,413/1,425。请裁定正式 forward 轮的完整率是否扣除已检测断链窗口内的在途整包丢失（另计入 disconnect），抑或正式 forward
  轮要求全程零链路事件；AC-6 两次断链用物理拔线还是 `relay.py desktop --drops`（软件断链，双通道与对时同断）。
- **IR-9（停点全套 vs「Mac 零模型」）**：全套会构造 NanoTrack/YOLOE/DINOv2/CSRT（FRAME-001 2026-10-01 曾为一次全套另签具名额度），
  与本信封「Mac：零 pip、零模型」冲突，本轮未跑全套。请裁定：测试夹具内的模型加载是否不计入「Mac 零模型」，或由用户为停点全套
  签具名额度（待用户 2）。
- **IR-10（S0 空闲 RAM 单位）**：1.2 GB 读作 tegrastats 原文单位 1,200 MB；实测 max 725 MB，任一读法均过线。

## 待用户（needs_user；推荐项只供选择，未执行）

1. **S1/S2 的 torch 路径**（`request_id` 仅在选 B 时生效：`P1-ENG-JET-001:b0a5f79c:SUB:1`，维度 = 板上 torch/torchvision 轮子下载与安装，
   数量待选定来源后填，理由 = 合同路径不存在）。选项：
   - **A（推荐）**：用板上已有的 NGC 容器 `nvcr.io/nvidia/pytorch:25.08-py3`（torch 2.8.0a0、CUDA 13.0、TensorRT 10.13.2.6）跑 S1/S2，
     容器内只装 `ultralytics==8.4.104` 与 `lap`（在既有 pip ≤ 8 包/300 MB 内），零模型下载；读数标注为容器栈。理由：零下载、立即可做，
     用户此前已在板上验证过 PyTorch CUDA。代价：测的不是 JP7.2 系统 TensorRT 10.16，§6「本栈」须改述。
   - B：在主机系统装与 JP7.2/CUDA 13.2 匹配的 NVIDIA torch 轮子（新增下载额度，可能超 300 MB），保持系统栈一致。
   - C：用户自行在板上装好 torch 后告知，再派发 S1/S2。
2. **停点全套的 Mac 模型额度**（`P1-ENG-JET-001:b0a5f79c:SUB:2`）：维度 = 本机 CPU 一次全套内的模型加载；数量参照 FRAME-001 先例
   （NanoTrack ≤ 4、YOLOE ≤ 2、DINOv2 ≤ 2、CSRT ≤ 2，一次全套）；理由 = IR-9。推荐在 S1/S2 补跑后的真正停点签发。
3. （既有，非新增）§7 (h) 有线直连与固定 IP 接好后告知，正式 SR 在阶段 A 剩余 4 轮内执行。

## 改动文件

`git diff --name-only "$BASE".."$CAND"` 解析为准；本轮新增/修改：
- 代码：`tools/eng_jet/__init__.py`、`common.py`、`env_probe.py`、`fastlayer_bench.py`、`replay_publish.py`、`relay.py`、`assets.py`、
  `ledger.py`、`evidence.py`；`.gitignore`（`/outputs/eng-jet/`）。
- 测试：`tests/test_eng_jet_relay.py`、`tests/test_eng_jet_guards.py`、`tests/test_eng_jet_bench.py`。
- 证据：`docs/evidence/P1-ENG-JET-001-{env,fastlayer,relay,vlm,quant-equivalence,coresidency,assets,ledger}.json`、`-report.md`、
  本文件、`-focused-tests.log`。
- 状态板：`docs/current-status.md`（本项 Gate 行与交接行、Log）。
- 未改：`Assets/`、`controller/`、`config/`、`runtime/`、提案、账本、复核与设计文件、工作流基础设施。

## 测试

- focused：`YOLO_OFFLINE=true YOLO_AUTOINSTALL=false .venv-yoloe/bin/python -m unittest discover -s tests -p 'test_eng_jet_*.py'`
  → 36 例全过（`docs/evidence/P1-ENG-JET-001-focused-tests.log`）；本机 loopback 绑定未被拒绝，双进程回环实际运行。
  补跑后同命令 41 例全过（同一日志文件已覆盖为补跑结果）。
- 红绿：见「冒烟发现与修复」。
- 全套：未跑（IR-9）；基线失败/新增失败分列留待真正停点。

## 未验证项与已知限制

- S1/S2 线束（引擎导出、TRT 计时分项、GMC 计时包装、`trtexec` 用的元数据剥离、热稳态采样）只经注入单测，从未在板上运行；
  ultralytics 引擎导出参数（`simplify=False` 以免 onnxslim 依赖、`workspace=None`）尚未实测。
- SR (b) 真实 `TrackLoop` + TRT 插件应答器**尚未实现**（依赖 S1 引擎与 IR-4 的 torch 路径；正式 SR 前补齐，属同一停点范围）。
- 冒烟对时只覆盖约 34 s；冒烟到达时延 p95 受 Tailscale/WiFi 抖动主导，不代表任何正式链路。
- 板上无 swap/zram。

## K1K3K4补跑执行记录（2026-10-02，Mac mini 桌面端；Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑-20261002T210313Z-98bc`）

| 时间（UTC） | 动作 | 结果 / 证据 |
|---|---|---|
| 21:05:16 | 板上只读核验：`nvpmodel -q` = MAXN_SUPER、磁盘、镜像在、docker 缺省 runtime = nvidia、cooling device 清单 | 无改动 |
| 21:07–21:08 | 容器只读探测（`--user 1000:1000` + video/render 组）：torch 2.8.0a0 CUDA 可用（Orin）、TensorRT 10.13.2.6、onnx 1.18.0；无 cv2/lap/ultralytics；`pip install --dry-run` 解析为 4 包 | 干跑下载的轮子进 pip 缓存，随后复用、21:17 删除 |
| 21:12 | 开工提交（线束按 IR-5/6/7、AC-2 修订 1/2、AC-3 修订 1 改读；S1/S2 到板件） | 上板代码 = 开工提交 |
| 21:13:35 | 到板件 `eng-jet-s1s2.tar` 17,858,560 B（sha `f4c0c8e3…51dc`），板上解包并核 `last.pt`/frozen-V/规格/freeze sha 一致、321 帧 | `-assets.json`「bundle_s1s2」 |
| 21:14 | 容器 venv（`--system-site-packages`，复用镜像 torch/TensorRT，未重装 torch）安装 ultralytics 8.4.104、lap 0.5.13、ultralytics-thop 2.2.2、opencv-python 4.11.0.86（`-c numpy==1.26.4` 防升级） | `import cv2` 失败：容器无 `libGL.so.1` |
| 21:14 | 卸 opencv-python，`--no-deps` 装同版本 opencv-python-headless 4.11.0.86 | imports 全通过（IR-11） |
| 21:15:36 | 首次启动导出：`ModuleNotFoundError: tools.eng_jet`（镜像 nvfuser egg 自带顶层 `tools` 包遮蔽） | 板上加 0 字节 `code/tools/__init__.py`（仅板上，IR-12） |
| 21:16:24–21:16:34 | 方形 `imgsz=640` FP16 导出：ONNX 成功（`last.onnx` 10,565,785 B，sha `5d0d1548…938f`）；TensorRT 建引擎 `Error Code 9: Target GPU SM 87 is not supported by this TensorRT release` | `-fastlayer.json`「S1.export_attempts」；`.pt` sha 不变 |
| 21:17:15 | 同一 ONNX 用容器 `/opt/tensorrt/bin/trtexec --fp16 --skipInference` 复证：`Compute Capability: 8.7`、同一 Error 9、`FAILED` | 「S1.tensorrt_cross_check」 |
| 21:17:25 | 删除 pip 缓存（重复副本）；取回日志 | `outputs/eng-jet/P1-ENG-JET-001/s1s2/` |
| 21:19:10 | 容器实跑栈读数 `fastlayer_bench stack`；镜像摘要 `sha256:ace9a848…c50fb` | `-env.json`「s1s2_container_stack」 |
| 21:20:46 | 板上清单只读扫描 | `-assets.json`「board_manifest」 |

未执行：矩形引擎导出、S1 320 帧计时与比对、trtexec 计时、S2 热稳态（均因方形引擎无法产出）；SR (b) 实现与任何 SR 轮；停点全套；
任何 sudo / `nvpmodel -m` / `jetson_clocks` / `systemctl isolate` / 换镜像 / apt。板上保留 `~/eng-jet/venv`（101,751,706 B）与
`~/eng-jet/wheels`（5 个轮子）供后续路径复用或用户清理，均计入板上磁盘。

### 补跑代码改动（开工提交 + 收工提交）

- `tools/eng_jet/fastlayer_bench.py`：判门窗口帧 1…320、计数窗口帧 0…49、两侧未配对即一致性不通过、帧 0 框差另报（AC-2 修订 1 / IR-6）；
  S2 末/首 p95 比值超线 → `STOP(LATENCY_OVER)`，降频只认上限频率下降与 `cpufreq-cpu*`/`devfreq-*.gpu`/`cpu-`/`gpu-throttle-alert`，
  风扇只报告、其余告警非零或频率读数缺失时 verdict 留空并列 `ruling_needed`（AC-3 修订 1 / IR-7）；`runtime_stack()` 容器实跑读数
  （AC-2 修订 2）；`trtexec` 子命令与摘要解析；矩形引擎 `imgsz` 线束改写（`TimedModel.imgsz_override`，IR-13）；S1 逐帧行键名
  `state` → `plugin_state`（IR-12）；去掉容器内不可用的 `start_tegrastats`（tegrastats 改在宿主侧采集）。
- `tools/eng_jet/assets.py`：S1/S2 到板件；板上允许前缀加 `frames/`、`venv/`、`wheels/`、`home/`；`venv/` 第三方包名命中单列（IR-12）。
- `tools/eng_jet/ledger.py`：`engine_export` 事件与每次 ≤ 20 min 机检。`tools/eng_jet/evidence.py`：容器路径 `-fastlayer.json`、
  `-env.json`「s1s2_container_stack」、`-assets.json`「bundle_s1s2」。
- 测试：`tests/test_eng_jet_bench.py`（窗口/未配对/IR-7/trtexec/imgsz 改写）、`tests/test_eng_jet_guards.py`（第三方包名单列；原
  「允许前缀之外」夹具 `home/other.txt` 因 `home/` 已成容器 HOME 前缀改为 `misc/other.txt`，判据不变）。focused 41/41。

## 待裁定（补跑；实现读法，交接受角色）

- **IR-11（pip 包替换）**：ultralytics 声明依赖 `opencv-python`，但该轮子在容器内因缺 `libGL.so.1` 无法 import；改装同版本
  `opencv-python-headless`（无 GUI 构建，`imread`/光流同源）。读作 §5「`ultralytics`、`lap`、`onnx`/导出依赖等」的 pip 维度内操作
  （5 包 ≤ 8、202.9 MB ≤ 300 MB 保守口径，未用 apt/sudo），不是合同外步骤。若不认可，该包在后续路径中不再使用。本轮 S1 未产出读数，
  此读法不影响任何数字。
- **IR-12（板上运行件）**：(a) 板上 0 字节 `code/tools/__init__.py` 只为解除镜像 nvfuser egg 的 `tools` 包遮蔽，仓库未改；
  (b) AC-12 扫描对 `venv/` 下第三方包文件名命中（pip 自带 `index` 模块 16 个）单列、不记违规，内容禁键命中仍记违规；
  (c) S1 逐帧输出键名 `plugin_state`（合同 §3.1 写 `state`），避免与 AC-12 禁键 `"state"`（smoke 真值字段）混淆，语义不变。
- **IR-13（矩形引擎 imgsz）**：静态引擎只接受导出形状，插件按冻结规格每次传 `imgsz=640`；矩形引擎在线束层改写为 `[480, 640]`
  并记入证据，规格与插件不改。本轮未运行（方形引擎已失败）。

## 待用户（补跑更新；推荐项只供选择，未执行）

1. **S1/S2 执行栈（原题 1 的选项 A 实测不可行）**——用户所选 NGC 容器 `pytorch:25.08-py3` 的 TensorRT 不支持 Orin SM 87。选项：
   - **B（推荐）**：在板上系统 Python 安装与 JP7.2 / CUDA 13.2 匹配的 NVIDIA torch（及 torchvision）轮子，使用 S0 已核验的系统
     TensorRT 10.16（`request_id` `P1-ENG-JET-001:b0a5f79c:SUB:1`，维度 = 板上 torch/torchvision 轮子下载与安装，数量待选定来源后填，
     可能超出现 pip ≤ 300 MB）。理由：回到合同原始执行栈，§6「本栈」主张无需改述；系统 TensorRT 是 JetPack 随附件。
   - A2：改用面向 Jetson/iGPU 的容器镜像（需新镜像下载额度，具体 tag 与是否支持 JP7.2 须先核实）。
   - C：用户自行在板上装好可用的 torch + TensorRT 栈后告知（实际栈以实跑为准）。
   任一选项都需用户逐字入账并由接受角色落实合同后再派实现；本项不自行选择。
2. **停点全套的 Mac 模型额度**（`P1-ENG-JET-001:b0a5f79c:SUB:2`）：不变，仍推荐在 S1/S2 有读数后的真正停点签发。
3. （既有）§7 (h) 有线直连与固定 IP 接好后告知，正式 SR 在阶段 A 剩余 4 轮内执行。

## K1K3K4补跑B执行记录（2026-10-02，Mac mini 桌面端；Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑B-20261002T225511Z-8bf6`）

| 时间（UTC） | 动作 | 结果 / 证据 |
|---|---|---|
| 22:58–23:00 | 板上只读核验：MAXN_SUPER、根分区可用 170.6 GB、`~/eng-jet` 240,491,182 B；系统 Python 3.12.3 + pip 24.0；`LD_LIBRARY_PATH` 空；系统包可见性（numpy 1.26.4、cv2 4.8.0、tensorrt 10.16.2.10、PIL、yaml、matplotlib、scipy、sympy 1.12 等；缺 torch/onnx/protobuf/filelock/networkx/fsspec/psutil/polars/pynvml）；ultralytics 8.4.104 轮子源码只读检查（导出须 `onnx`；JetPack 7 上 `check_tensorrt("10.15")` 在 `YOLO_AUTOINSTALL=false` 时只返回 False、不安装） | `-env.json`「s1s2_system_stack.system_packages_visible」 |
| 23:04:16 | 开工提交（verify 子命令、SUB:1 计数、`sysvenv/` 前缀） | `git log --grep='^P1-ENG-JET-001 K1K3K4补跑B 开工'` |
| 23:04:47 | 代码更新件 `eng-jet-s1s2-code.tar` 194,560 B（sha `12f4c3d0…515c`）上板；基线：`/proc/net/dev`、`ldconfig -p` 无 cuDSS、`ldd trtexec`、dpkg python3.12 = 3.12.3-1ubuntu0.17、df/du；`python3 -m venv --system-site-packages ~/eng-jet/sysvenv` | 板上 11 文件 sha 全一致（`-assets.json`「bundle_s1s2_code_round_b」） |
| 23:05:04–23:05:27 | SUB:1：`pip download --no-deps --index-url https://download.pytorch.org/whl/cu130 torch==2.9.1+cu130 torchvision==0.24.1` | torch 512,448,274 B（sha `6e7f84cb…fe04051f`）、torchvision 7,823,607 B（sha `89743dce…97586fec`），与题 4 一致；留存 `~/eng-jet/wheels/sub1/`；收包 568,663,496 B |
| 23:05:33–23:07:08 | SUB:1 依赖解析：`pip install --dry-run --report --no-cache-dir --index-url https://pypi.org/simple --find-links wheels/sub1 torch==2.9.1+cu130 torchvision==0.24.1` | 解析 23 包（torch + 21 依赖与题 4 清单一致；`nvidia-nvshmem-cu13` 3.3.24；未需 cuDSS；`mpmath` 1.3.0；**torchvision 被解析为 PyPI 同名不同 sha 版**）；pip 24.0 干跑把 22 个轮子体完整取回到临时目录后删除（2,318,455,950 B，收包 2,524,864,120 B） |
| 23:08:07 | 核实无轮子留存（无 pip 缓存、无临时残留）；netdev/df/du：`~/eng-jet` 774,399,627 B | **停止**：再取回 21 个依赖需 2,316,069,213 B，SUB:1 下载累计将约 5.4 GB（收包约 5.6 GB）> 3.5 GB |
| 23:08:47–23:08:49 | 代码更新件板上逐文件 sha 复核；板上清单扫描（AC-12） | 11/11 一致；3,968 文件、违规 0 |
| 23:09:27 | 取回 `sysvenv/pyvenv.cfg`（只读） | `include-system-site-packages = true` |

未执行：torch/torchvision 及依赖安装、题 4 安装后验证（`fastlayer_bench verify`）、onnx/ultralytics 等在系统 venv 的安装、S1 两版引擎导出与
320 帧计时比对、`trtexec` 计时、S2 热稳态、SR (b) 与任何 SR 轮、停点全套；任何 sudo / apt / `nvpmodel -m` / `jetson_clocks` /
`systemctl isolate` / 换源 / `--no-deps` 装 torch。板上保留 `~/eng-jet/sysvenv`（13,271,416 B，空 venv）与 `~/eng-jet/wheels/sub1`
（两枚官方轮子，供补装复用）；容器 venv 与 `wheels/` 五枚轮子按「S1/S2 系统栈落实（B）」继续保留至系统栈 S1/S2 有读数。

**本轮消耗（累计口径见 `-ledger.json`）**：SUB:1 23 包（distinct；torchvision 取回两版）/ 轮子字节 2,838,727,831 B / 保守收包
3,093,609,695 B（≤ 3.5 GB）/ 新增磁盘 533,908,445 B（≤ 8 GB）；到板 +194,560 B（累计 18,114,560 B）；板上墙钟 +253 s（累计 2,306 s）；
既有 pip 维度 0 新增（仍 5 包 / 202,869,979 B）；模型下载 0；Mac pip/模型 0；Unity/Play 0。

**成因与教训（如实）**：我为了逐项记账，先用 `--dry-run --report` 求依赖清单再逐个 `pip download`；pip 24.0 的干跑并不只取元数据，
会把轮子体完整下载后丢弃，且 `--no-cache-dir` 使其不留存。这是实现方法失误，不是合同或环境问题。补装时改为：对已知清单逐个
`pip download --no-deps <name>==<ver>`（字节与 sha 直接落盘可记）→ `pip install --no-index --find-links wheels/sub1 <torch 文件> <torchvision 文件>`
（按文件路径锁定官方 cu130 轮子，避免解析器取 PyPI 同名 torchvision），不再干跑。

### 补跑B代码改动（开工提交 + 收工提交）

- `tools/eng_jet/fastlayer_bench.py`：`verify` 子命令（题 4：`get_arch_list()` 含 `sm_87`、CUDA matmul 读回核对、torch 与系统 TensorRT
  同进程建小引擎并推理、无 torch 干净子进程建引擎、`/proc/self/maps` 库来源分 venv/系统）；`runtime_stack()` 加 venv 构造方式、
  模块文件路径、arch 列表（AC-2 修订 5）；`trtexec` 缺省改系统 `/usr/src/tensorrt/bin/trtexec`。
- `tools/eng_jet/ledger.py`：SUB:1 维度（distinct 包数；下载字节取轮子合计与网卡收包增量之大；新增磁盘取最近一次记录）；SUB:1 使用后
  板上磁盘生效值 13 GB。`tools/eng_jet/common.py`：SUB:1 常量与系统 venv/trtexec 路径。
- `tools/eng_jet/assets.py`：`sysvenv/` 允许前缀与第三方包名单列；代码更新件与板上逐文件 sha 复核。`tools/eng_jet/evidence.py`：
  `system-stack`、`fastlayer-system`（前轮原文进 `history`）、`assets-b`。
- 测试：`tests/test_eng_jet_bench.py` `TorchVerifyPieces`（3 例）、`tests/test_eng_jet_guards.py` 系统 venv 前缀与 `LedgerSub1`。focused 46/46
  （`docs/evidence/P1-ENG-JET-001-focused-tests.log`，已覆盖为本轮结果）。`verify` 的板上执行件（matmul/TRT）只经语法与纯函数单测，未上板运行。

### 补跑B后重判（停点自证）

1 不成立（S1/S2 仍无读数，SR (b) 未实现）；2 不成立（focused 46/46；停点全套待用户额度，IR-9）；3 不适用；4 已更新。不送 C1。

## 待裁定（补跑B；实现读法，交接受角色）

- **IR-14（S1/S2 verdict 形式）**：本轮停因是 SUB:1 下载额度将超、系统 torch 未装成。读作沿用 IR-3 已接受的
  `NOT_RUN(PATH_UNAVAILABLE(system-torch))`（系统栈 torch 仍不可用；不属 STOP 闭集，不自造码）。若应另记，请裁定形状。
- **IR-15（系统 venv 中 ultralytics 依赖，下轮执行前请裁定）**：ultralytics 8.4.104 声明依赖里系统缺 `psutil`、`polars`、`nvidia-ml-py`、
  `opencv-python`（系统有 apt 版 cv2 4.8.0）；按 §5 既有 pip ≤ 8 包维度（已用 5）全装会超。读法：ultralytics、lap、ultralytics-thop、
  opencv-python-headless 4.11.0.86 从 `~/eng-jet/wheels` 以 `--no-deps` 同版本重装（不新增计数）；只新增导出必需的 `onnx==1.18.0`
  （与容器轮同版，避免 1.19+ 的 `ml_dtypes`）及其依赖 `protobuf`（2 包，合计 7 ≤ 8，预计 ≈ 16 MB，累计 ≈ 219 MB ≤ 300 MB）；不装
  psutil/polars/nvidia-ml-py——本轮只读核查 ultralytics 源码，顶层导入只有系统已有的 PIL 与 torch 依赖 filelock，三者都是函数内惰性导入，
  S1/S2 路径不触达。所有板上运行设 `YOLO_AUTOINSTALL=false YOLO_OFFLINE=true`（JetPack 7 上 ultralytics 会 `check_tensorrt("10.15")`
  试装 `tensorrt-cu13`，关自动安装后只返回 False，仍用系统 TensorRT 10.16）。若不认可，S1 前停下另议。

## 待用户（补跑B；推荐项只供选择，未执行）

1. **SUB:1 下载上限追加**（`request_id` `P1-ENG-JET-001:b0a5f79c:SUB:3`；维度 = SUB:1「下载字节」；数量 = 由 ≤ 3.5 GB 提到 **≤ 6.5 GB**
   （+3.0 GB）；包数 ≤ 32、新增磁盘 ≤ 8 GB、板上磁盘 ≤ 13 GB、来源与 pin 均不变）。理由：已计 3,093,609,695 B（保守收包）；补装需再取回
   21 个依赖 2,316,069,213 B（收包约 2.52 GB）→ 约 5.6 GB；余量 ≈ 0.9 GB 留给一次最大轮子（nvidia-cublas 539,001,158 B）中断重取。
   - **A（推荐）**：按上值追加；下轮按「成因与教训」的取回方式（逐个 `pip download --no-deps` + 离线按文件安装，不干跑）补装 → 题 4 先验证 →
     S1/S2。理由：来源与依赖清单已实测确定，只差字节额度；方法改正后不会重复取回。
   - B：用户自行在板上按同一清单装好 torch/torchvision（代理侧零新增下载）后告知，再派验证与 S1/S2（同原题 1′ 的 C）。
   - C：暂不追加，S1/S2 继续 `NOT_RUN`。
2. **停点全套的 Mac 模型额度**（`P1-ENG-JET-001:b0a5f79c:SUB:2`）：不变，仍推荐在 S1/S2 有读数后的真正停点签发。
3. （既有）§7 (h) 有线直连与固定 IP 接好后告知，正式 SR 在阶段 A 剩余 4 轮内执行。

## K1K3K4补跑C执行记录（2026-10-02，Mac mini 桌面端；Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑C-20261002T233110Z-f493`）

| 时间（UTC） | 动作 | 结果 / 证据 |
|---|---|---|
| 23:33:29 | 板上只读核验：MAXN_SUPER、`~/eng-jet` 774,399,677 B、`wheels/sub1` 两枚官方轮子在、无 pip 缓存、无本项进程 | 无改动 |
| 23:34–23:37 | 开工提交（SUB:1 下载上限常量按 SUB:3 改 6.5 GB 与单测）；代码更新件 `eng-jet-s1s2-code-c.tar` 194,560 B（sha `3f75d3a1…eeea`）上板，板上 11 文件 sha 全一致 | `git log --grep='^P1-ENG-JET-001 K1K3K4补跑C 开工'`；`-assets.json`「bundle_s1s2_code_round_c」 |
| 23:37 | 本机生成代码更新件时误覆盖本地补跑B 的 `bundle/eng-jet-s1s2-code.tar`；从板上副本只读取回，sha `12f4c3d0…515c` 与补跑B 记录一致，已复原 | 本机 outputs，不涉证据数字 |
| 23:38:17–23:40:14 | SUB:1：21 个依赖逐个 `pip download --no-deps --only-binary=:all: --no-cache-dir`（单包 `--hash=sha256` 锁定；每包取回前按 6.5 GB 上限预检） | 21/21 sha 与字节一致，合计 2,316,069,213 B；网卡收包 2,522,169,434 B；`s1s2-system-c/sub1-fetch.log` |
| 23:40:24–23:40:27 | onnx 1.18.0（17,421,291 B）+ protobuf 6.31.1（322,115 B）`pip download --no-deps` 哈希锁定（PyPI JSON 元数据先取 sha） | 计入既有 pip 维度（AC-10 修订 2）；装后 RECORD 37,570,547 / 2,312,113 B |
| 23:40:36–23:41:50 | 离线安装：`pip install --no-index --find-links wheels/sub1 <torch 文件> <torchvision 文件>`（23 包）；既有 4 包 `--no-index --no-deps` 重装；onnx+protobuf `--no-index --find-links wheels` | `pip check` 只报 IR-15 已接受的 4 个未装声明依赖与系统 pynacl→cffi |
| 23:42:01–23:43:07 | `fastlayer_bench verify`（`YOLO_AUTOINSTALL=false YOLO_OFFLINE=true`，未设 `LD_LIBRARY_PATH`） | **未过**：arch list 不含 sm_87；其余三项过；`-env.json`「s1s2_system_stack_c.verify」 |
| 23:43:44–23:43:50 | 附加只读诊断：cuDNN conv2d fp32/fp16、torchvision CUDA nms、归约 | 均通过；只供裁定，不改变 verify 结论 |
| 23:44 | 读数取回（netdev/du/df、`~/eng-jet` 之外写入核查）；板上清单扫描；受保护根零写入核查 | 32,642 文件、违规 0；主树 `runtime/` 与 mini 数据根修改 0 |

未执行：S1 两版引擎导出与 320 帧计时比对、`trtexec`、S2 热稳态、SR 任何轮、停点全套；容器 venv 删除（「S1/S2 系统栈落实（B）」以系统栈
S1/S2 有读数为删除条件，未满足，保留）；任何 sudo / apt / `nvpmodel -m` / `jetson_clocks` / `systemctl isolate` / 换源 / 干跑。

**`~/eng-jet` 之外的写入（如实）**：verify 进程 `import ultralytics` 新建 `~/.config/Ultralytics/settings.json`（482 B，sha `f9c2e7ca…1dd1`）；
CUDA 驱动 JIT 缓存 `~/.nv/ComputeCache` 新增 545 文件（26,215,934 B）。二者不含本项数据或真值，保留未删；下一轮建议以
`YOLO_CONFIG_DIR`、`CUDA_CACHE_PATH` 指到 `~/eng-jet/home/` 下（IR-16 (c)）。

**本轮消耗（累计口径见 `-ledger.json`）**：SUB:1 包数 23（不变）/ 轮子字节累计 5,154,797,044 B / 保守收包累计 5,616,357,711 B（≤ 6.5 GB）/
新增磁盘 7,542,632,760 B（≤ 8 GB，保守口径含既有 pip 维度件与日志）；板上 pip 7 包 / 242,752,639 B（≤ 8 包 / 300 MB）；到板 +199,915 B
（累计 18,314,475 B）；板上墙钟 +422 s（累计 2,728 s）；板上磁盘 7,783,123,942 B（≤ 13 GB）；引擎导出 0；模型下载 0；Mac pip/模型 0；Unity/Play 0。

### 补跑C代码改动（开工提交 + 收工提交）

- `tools/eng_jet/common.py`：SUB:1 下载上限常量 3.5 GB → 6.5 GB（SUB:3），留存上限沿革与 SUB:3 账本标题。
- `tools/eng_jet/evidence.py`：`system-stack-c`（`-env.json`「s1s2_system_stack_c」：安装记录、verify、实跑栈、库来源、附加诊断、`~/eng-jet` 之外写入）、
  `fastlayer-system-c`（前轮原文进 `history`）、`assets-c` 与 `compact_listing`（第三方包树按前缀汇总入证据，全量清单原文另存记 sha）。
- 测试：`tests/test_eng_jet_guards.py` `LedgerSub1`（6.5 GB 边界）、`CompactListing`。focused 47/47（`docs/evidence/P1-ENG-JET-001-focused-tests.log`）。
- 板上运行件 `fastlayer_bench.py` 未改（与补跑B 开工提交一致）。

### 补跑C后重判（停点自证）

1 不成立（S1/S2 仍无读数；装后验证未过待裁定；SR (b) 未实现）；2 不成立（focused 47/47；停点全套待用户额度，IR-9）；3 不适用；4 已更新。
不送 C1。

## 待裁定（补跑C；实现读法，交接受角色）

- **IR-16（装后验证未过的记法与后续读法）**：(a) S1/S2 记法：torch 已装但题 4 第一项（arch list 含 sm_87）未过，读作沿用 IR-3/IR-14 已接受的
  `NOT_RUN(PATH_UNAVAILABLE(system-torch))`（该路径对 S1/S2 的前置验证不成立；不属 STOP 闭集，不自造码）；若应另记（如
  `PATH_UNAVAILABLE(system-torch-sm87)`），请裁定形状。(b) 若用户选「待用户（补跑C）」1 的 A，请写明题 4 第一项的替代判据（建议：arch list
  含同主版本、算力不高于 8.7 的 `sm_8x` SASS，且装后 matmul/TensorRT 共存三项与 cuDNN 卷积、CUDA nms 冒烟全过），作为 AC-2 修订；本角色
  不自行放宽。(c) `~/eng-jet` 之外两处运行时缓存写入（Ultralytics settings、CUDA ComputeCache）不在 AC-12 板上清单对象内；读作如实记录、
  保留不删，下一轮用环境变量把二者指到 `~/eng-jet/home/`；若需删除或另记，请裁定。(d) 磁盘：`wheels/sub1` 依赖轮子 2,836,341,094 B 留存
  （SUB:1 新增磁盘保守口径 7.54 GB ≤ 8 GB）；容器 venv 按「系统栈落实（B）」条件保留。若需装后即清依赖轮子以腾出新增磁盘余量，请裁定。

## 待用户（补跑C；推荐项只供选择，未执行）

1. **装后验证第一项未过（官方 cu130 轮子不含 sm_87 SASS）**——是否继续 S1/S2：
   - **A（推荐）**：接受「同主版本二进制兼容」读法：保留已装栈，经接受角色写 AC-2 修订后，下一派发直接导出引擎跑 S1/S2，零新增下载。
     理由：实测 matmul、cuDNN 卷积、CUDA nms 在本板结果正确；S1/S2 的检测推理走系统 TensorRT 10.16（原生支持 SM 87），torch 只做导出与
     前后处理；S1 自带对 frozen-V 的逐帧一致性比对（1e-3 线不改），数值问题会在读数中暴露。
   - B：改来源（换含 sm_87 的 Jetson 专用 torch 构建）。须用户指定来源并签新下载额度（建议 `request_id` `P1-ENG-JET-001:b0a5f79c:SUB:4`，
     维度 = 板上 torch/torchvision 轮子下载与安装，数量待来源确定）；已知 jetson-ai-lab SBSA 索引有第三方 `no kernel image` 报告，须先核实。
   - C：暂停 S1/S2。
2. **停点全套的 Mac 模型额度**（`P1-ENG-JET-001:b0a5f79c:SUB:2`）：不变，仍推荐在 S1/S2 有读数后的真正停点签发。
3. （既有）§7 (h) 有线直连与固定 IP 接好后告知，正式 SR 在阶段 A 剩余 4 轮内执行。

## K1K3K4补跑D执行记录（2026-10-03，Mac mini 派发、计算在 Jetson 板上；Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑D-20261003T001556Z-7e7a`）

| 时间（UTC，10-03） | 动作 | 结果 / 证据 |
|---|---|---|
| 00:17:50 | 板上只读核验：MAXN_SUPER、`~/eng-jet` 7,783,130,141 B、`wheels/sub1` 23 枚轮子在、无本项进程 | 无改动 |
| 00:18 前后 | 板上代码镜像逐文件对本机 HEAD：S1/S2 用到的件全一致（`relay.py` 为冒烟时旧版，S1/S2 不用）；资产使用前复核 334/334 一致 | `-assets.json`「round_d_pre_use_check」；无代码上板（到板 0 B） |
| 00:19:33 | 开轮读数：du/df/netdev、`~/eng-jet` 之外两处缓存基线、`nvpmodel -q` | `s1s2-system-d/{du-0,df-0,netdev-0,outside-baseline,nvpmodel-q}.txt` |
| 00:19:59–00:20:01 | IR-16 (d)：删 `wheels/sub1` 23 个已装轮子（2,836,341,094 B，清单 `cleanup-sub1-list.tsv`），只删文件、未动 sysvenv；du 7,783,134,099 → 4,946,793,035 B | `-env.json`「s1s2_system_stack_d.wheels_sub1_cleanup」；ledger `board_cleanup` |
| 00:20:11–00:32:50 | 导出：`env.sh`（`unset LD_LIBRARY_PATH`、`YOLO_AUTOINSTALL=false YOLO_OFFLINE=true`、`YOLO_CONFIG_DIR`/`CUDA_CACHE_PATH` 指 `~/eng-jet/home/`）下 `fastlayer_bench export --imgsz 640` 与 `--imgsz 480,640` | 两次 rc=0、375.4 s / 367.9 s；`.pt` sha 前后一致；`-fastlayer.json` `S1.engines.*.export` |
| 00:32:53–00:34:04 | S1：方形、矩形各一次（init 帧 0、update 帧 1…320、frozen-V 比对），`tegrastats` 1 s 采样 | 方形 `STOP(FP16_BOX_DIVERGENCE)`；矩形同口径单列；`S1.engines.*.s1` |
| 00:34:04 前 | `trtexec --loadEngine`（剥 ultralytics 元数据后的 plan）×2 | rc=0；GPU Compute 中位 4.74 / 3.92 ms |
| 00:34:37 | 收尾读数：du/df/netdev、`~/eng-jet` 之外新写入（`find ~ -newer marker`） | `outside-after.txt`、`outside-newer.txt`；外网接口收包增量 1,330,606 B（仅 ssh/scp） |
| 00:35:18–00:35:25 | 板上清单扫描（AC-12）、受保护根零写入核查 | 35,102 文件、机械违规 1（IR-17）；主树 `runtime/` 与 mini 数据根修改 0 |

**S1 读数（AC-2 修订 6 标注：官方 cu130 torch 2.9.1 无 sm_87 原生 SASS，按同主版本二进制兼容（sm_80 cubin）运行；检测推理走系统 TensorRT 10.16）**：
方形引擎 `update` p50 33.65 / p95 59.29 / max 116.59 ms（n = 320），检测 p95 22.87、GMC p95 39.02、关联器 p95 2.67 ms，trtexec GPU 中位 4.74 ms，
CPU 81.5%、RSS 1,726.9 MB；一致性：帧 0…49 计数不一致 3、帧 1…320 配对最大差 0.0992、未配对 66（引擎 21 / 参照 45）、不一致帧 284/321。
矩形引擎（不进 verdict）：`update` p95 58.95 ms；计数不一致 0、未配对 0、最大差 0.0259、超 1e-3 帧 17。完整读数与差异证据见 `-report.md` §2d。

**未执行**：S2（停止总则，`NOT_RUN(S1 STOP FP16_BOX_DIVERGENCE)`）、SR 任何轮、S3–S5、正式 SR 与 SR (b)（待 §7 (h)）、停点全套（IR-9）；
容器 venv 删除（见 IR-19）；任何下载 / 安装 / sudo / apt / `nvpmodel -m` / `jetson_clocks` / `systemctl isolate` / 换源 / 改阈值 / 换引擎重测。

**本轮消耗（累计口径见 `-ledger.json`）**：板上墙钟 +1,055 s（累计 3,783 s ≤ 8 h）；引擎导出 2 次（各 ≤ 20 min）；SUB:1 下载与包数不变（5,616,357,711 B / 23 包），
新增磁盘按 IR-16 (d) 重计 4,925,758,840 B ≤ 8 GB；板上磁盘 5,166,250,549 B ≤ 13 GB；到板 0；板上 pip 不变；模型下载 0；Mac pip/模型 0；Unity/Play 0。

### 补跑D代码改动（收工提交）

- `tools/eng_jet/evidence.py`：`fastlayer-system-d`（`-fastlayer.json` 本轮读数，前轮原文进 `history`）、`system-stack-d`（`-env.json`「s1s2_system_stack_d」）、
  `assets-d`（`-assets.json` 板上清单与使用前复核；CUDA JIT 缓存树按前缀汇总、全量清单原文另存记 sha）；纯函数 `tegrastats_ram`、`s2_plan`、`s2_overall`。
- 测试：`tests/test_eng_jet_bench.py` `RoundDEvidence` 3 例；focused 50/50（`docs/evidence/P1-ENG-JET-001-focused-tests.log`）。
- 板上运行件 `fastlayer_bench.py` 未改（与补跑C 一致），本轮无代码上板。

### 补跑D后重判（停点自证）

1 不成立（S1 `STOP`，后续步骤待用户 (α)/(β)；SR (b) 未实现；正式 SR 待 (h)）；2 不成立（focused 50/50；停点全套待用户额度，IR-9）；3 不适用；4 已更新。
不送 C1。

## 待裁定（补跑D；实现读法，交接受角色）

- **IR-17（AC-12，CUDA 驱动缓存文件名命中）**：按 IR-16 (c) 把 `CUDA_CACHE_PATH` 指到 `~/eng-jet/home/cuda-cache` 后，驱动 JIT 缓存自带的二进制索引
  文件 `home/cuda-cache/index`（38,800 B）命中禁项路径名 `index`。读作与 IR-12 (b) 同类的非本项工件文件名命中（单列、不记违规；内容禁键命中仍记违规，
  本轮 0）；证据中 `ac12_clean: false` 原样保留，未删除缓存。请裁定是否接受该读法（或要求改 `CUDA_CACHE_PATH` 子目录名 / 扫描规则另列）。
- **IR-18（`~/eng-jet` 之外写入）**：本轮新写 `~/.cache/matplotlib/fontlist-v330.json`（140,106 B，00:20:15Z，导出进程 import ultralytics→matplotlib 时生成，
  不含本项数据或真值）；`~/.local/state/wireplumber/restore-stream` 为 ssh 登录启动的用户会话服务 wireplumber（00:34:29Z）所写，非本项进程。读作同 IR-16 (c)：
  如实记录、保留不删；下一派发起加 `MPLCONFIGDIR=~/eng-jet/home/mpl`。Ultralytics settings 与 ComputeCache 两处既有文件本轮未变（`outside-after.txt`）。
- **IR-19（容器 venv 删除时机）**：决策记录「S1/S2 系统栈落实（B）」以「系统栈 S1/S2 有读数后」为删除条件；本轮 S1 有读数、S2 按停止总则无读数，读作条件未全满足、
  保留 `~/eng-jet/venv`（101,751,706 B，继续计入板上磁盘）。若应读作「S1 有读数即删」，请裁定，下一派发执行。

## 待用户（补跑D；推荐项只供选择，未执行）

1. **S1 `STOP(FP16_BOX_DIVERGENCE)` 的处置（§2.1，用户二选一；不在 supervisor 代拍闭集内，裁定须逐字入账）**：
   - **(α)（推荐）**：记录偏差、以该方形 FP16 引擎继续（S1 保持 `STOP`，后续 S2/SR 标 `RESUMED_AFTER_USER_RULING(S1)`，阈值与引擎精度不改）。
     理由：时延分量远低于 200 ms 门（p95 59.29 ms）；S2/SR 测的是热稳态与跨机中继，不依赖与 MPS 缓存的逐框一致；偏差形态（帧 0 即差 2.2e-3、
     而输入形状与参照一致的矩形引擎无计数不一致与未配对）提示主因可能是方形引擎的 640×640 填充而非 FP16 数值崩坏（未验证，见 `-report.md` §2d）。
   - (β)：关闭本项。
   - 说明：改用矩形引擎作 verdict 对象或改 1e-3 线属合同变更（不在 §2.1 二选一内），本角色不提出也不执行。
2. **停点全套的 Mac 模型额度**（`P1-ENG-JET-001:b0a5f79c:SUB:2`）：不变，仍推荐在 S1/S2 有可交复核读数后的真正停点签发。
3. （既有）§7 (h) 有线直连与固定 IP 接好后告知，正式 SR 在阶段 A 剩余 4 轮内执行（须先有 (α)）。

## K1K3K4补跑E执行记录（2026-10-03，Mac mini 派发、计算在 Jetson 板上；Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑E-20261003T044648Z-4cdc`）

依据：账本 2026-10-03「P1-ENG-JET-001 — 用户选题 7 (α)：S1 STOP 记录偏差、以方形 FP16 引擎继续（supervisor 会话代录）」与同日「…用户授权把 Jetson 有线地址主机密钥写入…」，
提案决策记录「题 7 选 (α) 落实」。上板前按 `-ledger.json`「dimensions」核对余额：墙钟余 25,017 s（S2 需 1,800 s）、到板余 81,685,525 B、板上磁盘余 7,833,749,451 B、
SUB:1 新增盘余 3,074,241,160 B，均足。ssh 一律 `jetson@192.168.8.2`（有线）+ `BatchMode=yes` + `StrictHostKeyChecking=yes`；未改 `~/.ssh/*`。

| 时间（UTC，10-03） | 动作 | 结果 / 证据 |
|---|---|---|
| 04:48:26 | 板上只读核验：MAXN_SUPER、无本项进程、`~/eng-jet` 5,166,250,549 B、引擎目录在 | 板子在补跑D 之后重启过（`uptime -s` 板本地 22:50:43 = 10-03 02:50:43Z）；`uptime.txt` |
| 04:49:53–04:50:04 | 开轮读数（nvpmodel、uptime、du、df、netdev、`~/eng-jet` 外缓存基线）；使用前 sha 复核 335/335 一致（13 件对本机 HEAD、a7 帧 0..320、方形引擎 `5e45529a…` 对 `-fastlayer.json`「S1.engines.640.export.sha256」） | `s2-system-e/{nvpmodel-q,uptime,du-0,df-0,netdev-0,outside-baseline}.txt`、`board-sha-e.json`；`-assets.json`「round_e_pre_use_check」 |
| 04:50:15 | 经 ssh 标准输入下发 `env.sh`（275 B）与 `run-s2.sh`（1,194 B）到 `~/eng-jet/logs/s2-system-e/`，sha 两端一致 | 到板 1,469 B（ledger `to_board_transfer`）；无代码、无资产上板 |
| 04:50:25–05:20:34 | `touch marker-start` 后 `setsid nohup bash run-s2.sh 15`：记实际环境（AC-16）、开跑前引擎 sha、`tegrastats --interval 1000`、`fastlayer_bench s2 --hz 15 --minutes 30`（方形引擎、a7 帧 0..320 循环、init 框同 S1） | rc=0；`STOP(FRAME_DROP)`；`results-e/s2-det-assoc-v1-fp16-640-15hz{,-summary}.json`、`s2-15hz.log`、`s2-15hz-tegrastats.log` |
| 05:20:48 | 收尾读数：`~/eng-jet` 外缓存、marker 之后外部新写入（`find ~ -path ~/eng-jet -prune -o -newer marker`）、du/df/netdev | 外部新写入 0；`outside-after.txt`、`outside-newer.txt`（空）；外网接口本轮收包增量 enP8p1s0 375,640 B / wlP1p1s0 178,039 B（仅 ssh） |
| 05:20:58–05:21:01 | TRT 告警只读诊断（AC-16 环境下一个 Python 进程读 torch 设备属性、`/proc/meminfo`、GPU devfreq） | `trt-warning-diag.json`；见 IR-20 |
| 05:21:11 | IR-19：S1、S2 均有读数 → 删除容器 `~/eng-jet/venv`（先确认 `pyvenv.cfg`、存清单）；sysvenv 未动 | 1,796 文件 / 283 目录 / 4 链接、101,751,706 B；du 5,172,051,851 → 5,070,463,807 B；`container-venv-delete.json`、`venv-listing.tsv` |
| 05:21:19–05:21:28 | 板上清单扫描（AC-12）、读数 scp 取回 | 33,345 文件，机械违规 1（`home/cuda-cache/index`，IR-17 单列）、真正违规 0；主树 `runtime/` 与 mini 数据根修改 0 |

**S2 读数（`RESUMED_AFTER_USER_RULING(S1)`；AC-2 修订 6 标注：官方 cu130 torch 2.9.1 无 sm_87 原生 SASS，按同主版本二进制兼容（sm_80 cubin）运行；检测推理走系统 TensorRT 10.16.2.10）**：

| 5 min 格 | `update` n | p50 ms | p95 ms | max ms | 丢帧 | GPU 上限 | CPU 上限 | tj 最高 °C | VDD_IN p50/max mW |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 4,407 | 40.75 | 66.99 | 126.74 | 78 | 1,020 MHz | 1,728 MHz | 50.97 | 6,379 / 6,658 |
| 1 | 4,458 | 40.72 | 67.15 | 127.74 | 28 | 1,020 MHz | 1,728 MHz | 51.16 | 6,379 / 6,618 |
| 2 | 4,458 | 40.86 | 67.17 | 126.82 | 28 | 1,020 MHz | 1,728 MHz | 51.34 | 6,379 / 6,618 |
| 3 | 4,458 | 40.75 | 67.45 | 129.00 | 28 | 1,020 MHz | 1,728 MHz | 51.31 | 6,379 / 6,658 |
| 4 | 4,458 | 40.79 | 67.16 | 126.64 | 28 | 1,020 MHz | 1,728 MHz | 51.34 | 6,379 / 6,738 |
| 5 | 4,458 | 40.69 | 67.13 | 126.51 | 28 | 1,020 MHz | 1,728 MHz | 51.47 | 6,379 / 6,767 |

verdict（AC-3 修订 1 三项合取）：热降频事件 0（频率上限全程不变，13 个 cooling device 全程 0）；末/首 p95 = 1.0021 ≤ 1.2；丢帧 218 ≠ 0 → **`STOP(FRAME_DROP)`**。
丢帧分布（描述，不改 verdict）：第一次 init 含冷启动 3,452.8 ms → 丢 50；其后 84 个回放周期每周期固定两处（init 后约 19.0 s）各丢 1，前一次 `update` 约 101 / 126 ms。
数值全文见 `-fastlayer.json`「S2」（`runs.15hz.bins`、`tegrastats_bins`、`verdict`），报告 §2e。

**未执行**：SR 任何轮与 SR (b) 准备（S2 STOP，§2.1 停全部后续，`NOT_RUN(S2 STOP FRAME_DROP)`）、S3–S5、30 Hz（未达加测条件）、停点全套（SUB:2 未签，IR-9）；
任何下载 / 安装 / 引擎导出 / sudo / apt / `nvpmodel -m` / `jetson_clocks` / `systemctl isolate` / 换源 / 改阈值 / 重跑 S1 / 换矩形引擎；外部缓存与 `wheels` 未删。

**本轮消耗（累计口径见 `-ledger.json`）**：板上墙钟 +1,983 s（累计 5,766 s ≤ 8 h）；到板 +1,469 B（累计 18,315,944 B）；引擎导出 0；SUB:1 下载与包数不变；
新增盘重计 4,829,972,625 B ≤ 8 GB；板上磁盘 5,070,463,807 B ≤ 13 GB；板上 pip 不变；模型下载 0；SR 轮 0；Mac pip/模型 0；Unity/Play 0。

### 补跑E代码改动（收工提交）

- `tools/eng_jet/evidence.py`：`fastlayer-system-e`（`-fastlayer.json`：S1 保持补跑D 读数并加 `kept_note`，S2 本轮读数 + `RESUMED_AFTER_USER_RULING(S1)` 与账本标题、引擎身份复核、TRT 告警行；前轮 S2 进 `history`）、
  `system-stack-e`（`-env.json`「s2_system_stack_e」：AC-16、外部写入、容器 venv 删除、网卡/磁盘、TRT 告警诊断）、`assets-e`（`-assets.json`：清单 + `ac12_split`、`round_e_pre_use_check`）；
  纯函数 `parse_utc_offset`、`tegrastats_bins`、`ac12_split`、`netdev_rx`。
- `tools/eng_jet/ledger.py`：`PENDING_USER["h"]` 同步 10-03 有线就绪与两条账本标题（历史事实保留在 effect 末句）。
- 测试：`tests/test_eng_jet_bench.py` `RoundEEvidence` 4 例；focused 54/54（`docs/evidence/P1-ENG-JET-001-focused-tests.log`）。
- 板上运行件 `fastlayer_bench.py` 未改（与补跑C/D 一致）。

### 补跑E后重判（停点自证）

1 不成立（S2 `STOP(FRAME_DROP)`，后续步骤待用户裁定；SR (b) 未实现、正式 SR 未跑）；2 不成立（focused 54/54；停点全套待 SUB:2，IR-9）；3 不适用；4 已更新。不送 C1。

## 待裁定（补跑E；实现读法，交接受角色）

- **IR-20（TensorRT 引擎计划跨设备告警）**：S2 加载补跑D 方形引擎时打出 `[TRT] [W] Using an engine plan file across different models of devices is not supported and is likely to affect performance or even cause errors or deadlock.`；
  补跑D S1 加载同一引擎（导出后同次开机）无此行；两轮之间板子重启过。引擎 sha 开跑前复核一致、同一块板（设备 `Orin`、SM 8.7、8 SM），告警为 `[W]` 级、非 CUDA/TRT 错误，
  推理全程正常、无 `no kernel image`。本角色读作：非「题 6 选 A 落实」所称的「`no kernel image` 或其他 CUDA 不兼容报错」，故未停跑、未重导出（重导出亦超本派发范围）；S2 读数如实保留。
  请裁定该读法；若应视为不兼容报错，请写明处置（例如本轮 S2 读数如何标注）。证据：`-fastlayer.json`「S2.trt_log_warnings」、`-env.json`「s2_system_stack_e.trt_plan_device_warning」。
- **wheels 处置（IR-19 既定交接受角色补记录）**：容器 venv 已删；`~/eng-jet/wheels`（92,632,836 B）保留，处置请补一行。

## 待用户（补跑E；推荐项只供选择，未执行）

1. **S2 `STOP(FRAME_DROP)` 的处置（§2.1 停止总则；不在 supervisor 代拍闭集内，须逐字入账，由接受角色先记录后转用户）**：
   - **(α′)（推荐）**：记录偏差并继续——S2 保持 `STOP`，后续 SR 标 `RESUMED_AFTER_USER_RULING(S2)`，阈值不改；下一实现派发准备 SR (b) 并做正式 SR。
     理由：热与时延比值两项都过（无降频、p95 比 1.0021），丢帧来自首次 init 冷启动（50）与每回放周期固定两帧（168）；15 Hz 只是板上压力档，运行时合同为 5 Hz（周期 200 ms，
     本轮单次 `update` 最大 129 ms，未经 5 Hz 实测）；SR 测跨机中继，不依赖 15 Hz 丢帧结论。
   - (β′)：关闭本项。
   - 说明：改丢帧判据（如剔除冷启动）、改帧率或改阈值属合同变更，本角色不提出也不执行。
2. **停点全套的 Mac 模型额度**（`P1-ENG-JET-001:b0a5f79c:SUB:2`）：不变，仍推荐在有可交复核读数的真正停点签发。

## K1K3K4补跑F执行记录（2026-10-03，Mac mini 派发、计算在 Jetson 板上；Dispatch-Id `P1-ENG-JET-001-K1K3K4补跑F-20261003T161148Z-3166`）

依据：账本 2026-10-03「P1-ENG-JET-001 — 用户选 S2 STOP 处置 (α′)：S2 记录偏差并继续，做原范围正式 SR（supervisor 会话代录）」、同日「…用户选题 7 (α)…」「…用户授权把 Jetson 有线地址主机密钥写入…」、
2026-10-02「P1-ENG-JET-001 — supervisor 代拍：IR-8 断链手段代选软件定时断链（10 s、60 s，双通道与对时同断）」；提案决策记录「S2 处置选 (α′) 落实」。
SR 证据/报告同时标 `RESUMED_AFTER_USER_RULING(S1)`（指题 7 (α) 条目）与 `RESUMED_AFTER_USER_RULING(S2)`（指 (α′) 条目）。ssh 一律 `jetson@192.168.8.2` + `BatchMode=yes` + `StrictHostKeyChecking=yes`；未改 `~/.ssh/*`、网络或隐私设置；未启动 Unity；主树 `runtime/` 与数据根零写入。

**余额先行**（每次上板/正式轮前按最新 `-ledger.json` 与事件流核对；不足即停）：开工时墙钟已用 5,766 / 28,800 s、SR 1 / 5 轮、到板 18,315,944 / 100,000,000 B、板上磁盘约 5,070,464,279 / 13,000,000,000 B、Mac outputs 50,226,974 / 2,000,000,000 B；
计划 3 个正式轮（回声、真实、断链）+ 1 轮余量，每轮预计约 60 MB ≤ 100 MB。f1 返工后余 3 轮恰好够用（无余量），各轮前复核仍足；收工时 SR 5 / 5 耗尽，其余维度见 AC-10 行。

| 时间（UTC，10-03） | 动作 | 结果 / 证据 |
|---|---|---|
| 16:16:04 | 板上只读核验（有线 ssh）：MAXN_SUPER、无本项进程、`~/eng-jet` 5,070,464,279 B、代码镜像缺 TrackLoop 导入链 | 无改动 |
| 16:28:32 | 开工提交：`tools/eng_jet/track_responder.py`（SR (b)）、`relay.analyze` 回程/断链分析、SR 到板件、有线 ssh 选项；focused 66/66 | 上板代码 = 开工提交 |
| 16:29:00–16:29:07 | 上传前板上 27 件 sha 快照（14 件不存在）；上传 `eng-jet-sr-code-f.tar`（552,960 B）与 `env.sh`/`run-sr.sh`（1,805 B） | `sr-f/board-sha-before-upload.txt`；到板 554,765 B |
| 16:29 前后 | 使用前复核：30 件（27 到板件 + last.pt/freeze + 方形引擎，引擎 sha 运行时从 `-fastlayer.json` 解析）全一致 | `-assets.json`「round_f_pre_use_check」 |
| 16:29:24–16:29:31 | 应答器预检（AC-16 环境；引擎身份复核 + 加载，无帧 4 s） | `engine_identity_ok`、`model_load_s` 5.338、`NO_FRAME`（预期） |
| 16:29:39–16:36:20 | **正式轮 f1-echo**（回声）：桌面机运行目录残留 10-02 冒烟会话 `latest.json`（frame 1499），中继启动即转发，板侧发布后本会话帧全部按顺序违反被拒 → **`STOP(RELAY_INTEGRITY)`** | `sr-f/f1-echo/`；`-relay.json`「rework_rounds」 |
| 16:37:27 | 返工提交：`DesktopRelay` 跳过发布时刻早于本进程启动 5 s 以上的指针；回归 `DesktopStalePointer` 修前红/修后绿（`sr-f/rework-{red,green}.log`）；编排改为启动中继前清空运行目录 | focused 67/67；板侧代码不变 |
| 16:37:56–16:44:36 | **正式轮 f2-echo**（回声，全程零链路事件）：1,500 / 1,500 完整、顺序 0、不完整 0 | `sr-f/f2-echo/` |
| 16:45:03–16:52:04 | **正式轮 f3-track**（真实 TrackLoop + 方形 FP16，全程零链路事件）：1,500 / 1,500 完整；init 框 = 首帧检测器 target 类最高分框 | `sr-f/f3-track/` |
| 16:52:11–16:52:14 | （意外）板侧 `enP8p1s0` 物理链路 down/up 一次，同时段一次 ssh 连接超时；不在任何 SR 数据窗内，原因未查明 | `sr-f/board-link-events.txt` |
| 16:54:22–17:01:23 | **正式轮 f4-track-drops**（真实 TrackLoop；`--drops 60:10,160:60` 软件定时断链，双通道与对时同断）：1,152 / 1,152 完整，两次断链均回稳 | `sr-f/f4-track-drops/` |
| 17:01:23–17:02:23 | 读数取回、板上清单扫描（AC-12）、受保护根零写入核查、`timedatectl` 只读 | `board-manifest-sr-f.json`、`zero-write-sr-f.json`、`sr-f/board-timesync.txt` |

**SR 读数**（`RESUMED_AFTER_USER_RULING(S1)` + `(S2)`；AC-2 修订 6 标注：官方 cu130 torch 2.9.1 无 sm_87 原生 SASS，按同主版本二进制兼容（sm_80 cubin）运行；检测走系统 TensorRT 10.16；IR-20 / AC-2 修订 7：每次加载方形引擎各 1 条 TRT `[W]` 跨设备告警，原因与影响未核实）——全文见 `-report.md` §2f 与 `-relay.json`：

- forward：f2-echo / f3-track 各 1,500 包，完整率 100%、顺序违反 0、指向不完整包 0；到达时延（偏差校正）p50 / p95 / max = 11.919 / 16.245 / 17.364 ms 与 12.753 / 16.690 / 25.707 ms（n = 1,500）；偏差（板 − 桌面）中位 8.909 / 7.851 ms（n = 328），漂移 −2.45 ppm，RTT 中位约 0.9–1.0 ms。
- return：回声回程 p50 / p95 / max 3.393 / 5.644 / 6.371 ms（n = 1,500），端到端 p95 23.783 ms；真实回程 2.804 / 6.117 / 6.156 ms（n = 29），端到端 p95 239.633 ms；`capture_age_s` p95 0.0298 / 0.0291 s（超 3.0 s 0）；`load_elapsed_s` p95 0.00306 / 0.0549 s（超 0.4 s 0）；真实 `frame_age_ms` p95 124.94 ms（n = 1,500，超 `T_stall` 0）。真实模式插件第 30 帧起丢失且不改绑（compat 语义），故回程 n 仅 29。
- disconnect（f4）：10 s / 60 s 实测 10.004 / 60.001 s；断链期间板侧写桥（成员 / latest / 回程 / 应答器）全 0；恢复后缺口 49 / 299、latest 帧差 50 / 300；只发重连时当前 latest（不补发）；回稳 0.134 / 1.940 s（阈值 16.203 / 15.340 ms，基线 n 283 / 300）；真实 TrackLoop 第一次重连即 `GAP`（`retained_intermediate_frame_missing`）终止，应答器不重播种、继续存活至时长结束；中继、应答器、回放器退出码全 0。
- verdict：**SR = `PASS`**（forward 与 disconnect 均过 §2.1 线）；f1-echo 的 `STOP(RELAY_INTEGRITY)` 原样保留为返工史。

**未执行**：重跑 S1/S2、重导出或换矩形引擎、改阈值、任何下载/安装/sudo/apt、`nvpmodel -m`/`jetson_clocks`/`systemctl isolate`、S3–S5（阶段 B 未签）、停点全套（SUB:2 未签，IR-9）、任何新增清理（sysvenv、wheels、外部缓存与本轮板上运行目录均保留）。

**已知限制（补跑F）**：板侧中继只修剪「当前连接内收到且已发布后」的旧帧（重连时清空成员表），故 f1（全部被拒发布）与 f4（断链前帧）在板上镜像目录留下多于 retain 128 的帧文件，计入板上磁盘（本轮未清理，属新增清理范围外）；不影响完整性/顺序判定。真实模式回程 n = 29，统计力弱。16:52Z 链路抖动原因未查明。

### 补跑F代码改动（开工提交 + 返工提交 + 收工提交）

- `tools/eng_jet/track_responder.py`（新）：SR (b) 真实应答器（见上）；`tools/eng_jet/relay.py`：`analyze` 增真实模式回程、偏差校正 `capture_age_s`/`frame_age_ms`、`disconnect_analysis` 与预注册回稳读法 `RECOVERY_*`；
  返工：`DesktopRelay` 旧会话指针守卫（`STALE_POINTER_GRACE_S`）；收工：`latest.json` 指向不完整包的复算改为「同号帧任一早于该次发布的成员到达」（f1 旧会话同号帧误判修正，只影响分析）。
- `tools/eng_jet/assets.py` / `common.py`：SR 到板件（`SR_CODE_FILES`）、有线 ssh 选项 `SSH_OPTS`、`--host`。`tools/eng_jet/evidence.py`：`relay-f`、`system-stack-f`、`assets-f`（`tailscale_smoke` 原件逐字保留）。`tools/eng_jet/ledger.py`：`pending_user.h` 现状同步。
- 测试：`tests/test_eng_jet_track_responder.py`（新，14 例：init 框选择、引擎身份、真实 TrackLoop 绑定写桥、GAP 终止不重播种、进程内回环 + 软件断链、回稳读法、forward 通过线、到板件覆盖导入链）；`tests/test_eng_jet_relay.py` `DesktopStalePointer`。focused `test_eng_jet_*` 69/69（`docs/evidence/P1-ENG-JET-001-focused-tests.log`）。
- 未改：`Assets/`、`controller/`、`config/`、冻结规格/权重、帧与控制协议、目标身份/重播种逻辑、发布门与采样。

### 补跑F后重判（停点自证，workflow §4.3.1）

1. 实现范围与接口冻结：阶段 A 全部步骤已有读数（S0 `PASS`；S1/S2 `STOP` 经用户裁定续跑；SR `PASS`），SR (b) 已实现；但 IR-21、IR-22 待接受角色裁定 → **暂不成立**（裁定前候选可能改动）。
2. 相称测试：focused 69/69；停点全套仍未跑（SUB:2 未签，IR-9）→ **不成立**。
3. 已知 Unity 失败：不适用（零 Unity）。
4. 复核范围、状态板、候选提交与未验证风险：已更新（本文件、状态板交接行）。

结论：**不送 `C1@K1K3K4`**。下一步 owner：接受角色（裁定 IR-21/IR-22 并在决策记录补 f1 返工归因行）→ 用户（SUB:2）；二者齐后由实现角色跑停点全套并重判自证。

## 待裁定（补跑F；实现读法，交接受角色）

- **IR-21（AC-12 / 真实 TrackLoop 逐帧记录键名）**：真实 `TrackLoop` 的逐帧记录含键 `state`（`TRACKING`/`LOST`/`ERROR_REINIT_REQUIRED`），会命中 AC-12 内容禁键 `"state"`。本角色经构造注入的记录器（`track_responder.RecordSink`）把该键改名 `loop_state` 写入 `track-records.jsonl`，其余键与值原样，`controller/` 零改动；读法同 IR-12 (c)（S1 逐帧 `state` → `plugin_state`）先例。请裁定是否接受（或要求改用 `controller.run_log.RunLogger` 原样落盘并另定扫描读法）。
- **IR-22（AC-12 / 真实控制命令文件的内容禁键命中）**：真实 TrackLoop（condition follow）经 `controller/gimbal_entry.look_at` 写出的 `gimbal_command.json` 含冻结控制协议字段 `target_world_m`（look-at 世界点，由检测框与帧位姿几何求得，非真值），命中 AC-12 内容禁键 `target_*`（f3、f4 板上运行目录各 1 个，最终版本）。按 IR-17「内容禁键命中仍记违规」，本轮记为 2 条真正违规、`ac12_clean: false` 原样，**未删除、未改名、未改扫描规则**。本角色读作：该字段是冻结控制协议的一部分，不属本项要隔离的真值（smoke `target_*` 字段）；请裁定是否按具名路径/字段（`runtime/**/gimbal_command.json` 的 `command.target_world_m`）单列，或给出其他处置（删除板上该文件属新增清理，本角色未做）。
- **f1-echo 返工归因（提示，非新读法）**：§2.1 SR 行「`RELAY_INTEGRITY` 返工后在 §5 轮数内重跑，接受角色在决策记录记一行归因」——请补该行（返工内容与回归测试见上；f1 计入轮数，SR 5 / 5 已耗尽）。

## 待用户（补跑F；推荐项只供选择，未执行）

1. **停点全套的 Mac 模型额度**（`P1-ENG-JET-001:b0a5f79c:SUB:2`）：不变；阶段 A 读数现已齐（S0–S2 + SR），推荐在 IR-21/IR-22 裁定后签发，以便跑停点全套并送 `C1@K1K3K4`。理由：focused 不能替代停点全套（IR-9），未签则自证第 2 项永不成立。
2. （告知，非请求）阶段 A SR 轮数已用尽（5 / 5，含冒烟 1、返工 1）；如复核要求再跑任何 SR 轮，须用户另签。

## K1K3K4全套执行记录与停点自证（2026-10-03，Mac mini 离线；Dispatch-Id `P1-ENG-JET-001-K1K3K4全套-20261003T181204Z-f491`）

依据：提案决策记录「SUB:2 落实：§5 Mac 与 IR-9（2026-10-03，CLARIFY）」（执行范围 1–3）、「SR 与补跑F记录核对（2026-10-03）」（AC-4 修订 2、AC-5 修订 1）、「待裁定」IR-21 / IR-22（AC-12 修订 3 / 4）、IR-9；账本 2026-10-03「P1-ENG-JET-001 — 用户按推荐签发 SUB:2：停点全套的 Mac 本机 CPU 模型额度（一次全套）（supervisor 会话代录）」授权范围 (1)。本轮未启动 Unity、未 ssh 上板、未重跑 S1/S2/SR、未写主树 `runtime/` 与数据根、零 pip、零下载、零新增模型。

### 额度先行：SUB:2 跑前只读核对（结论：不跑）

只读核对（未调用任何模型构造器、推理或 `unittest discover`）；原文为 `outputs/eng-jet/P1-ENG-JET-001/ledger-events.jsonl` 的 `mac_full_suite_precheck` 一条，已汇入 `-ledger.json`「dimensions.mac.sub2.prechecks」：

- **测试树**：沿用 FRAME-001 R7 全 tests 树闭集审计（`docs/evidence/P1-ENG-FRAME-001-R7-full-suite-preparation.md`）；自 R7 全套提交（`git log -1 --format=%H -- docs/evidence/P1-ENG-FRAME-001-R7-full-suite.log` 运行时解析）以来 `tests/`、`controller/`、`tools/*.py` 只新增本项四个 `tests/test_eng_jet_*.py`（假插件/假工厂，无真实加载器）。
- **解释器**：合同指定需 `lap` 的测试只读用数据根 `~/TetheredDroneTracking-full/.venv-yoloe`（Python 3.12.14，lap 0.5.13、ultralytics 8.4.104、torch 2.13.0、opencv 5.0.0）；仓库 `.venv-yoloe` 缺 `lap`。
- **四种具名模型预计**：NanoTrack 0（主树 `runtime/models/nanotrack-v2/` 不存在：两条 pinned NanoTrack 用例 skip，`test_preflight_reanchor_env` 两条真实 CLI 子进程在 `_verify_model_file` 构造前失败）；YOLOE 0、DINOv2 0（主树模型文件不存在，且构造顺序在 Nano 之后）；CSRT 至多 2 次尝试、真实实例 0（opencv 5.0.0 无 `TrackerCSRT_create`）。均在额度内。
- **额度外（停因）**：数据根解释器下 `tests/test_det_assoc_carrier.py::CarrierSelfTest` 的 `_ready()` 成立（有 ultralytics+lap+cv2，冻结规格与 `outputs/eng-det/runs/run-1/weights/last.pt` 在主树，数据根帧存在），两例各经 `create_tracker("det-assoc-v1")` → `_default_model_loader` → `ultralytics.YOLO(last.pt)` 真实加载 det-assoc 冻结检测器，共 **2 次**（首例另在 CPU 推理 768 帧）。该模型不在 SUB:2 四种具名模型内，按 AC-10 修订 3 / IR-9 未列名额度为 0。FRAME-001 R7 在 Air 上因数据根缺失而 skip 这两例，故当时的数量参照未包含它。
- **另记**：同文件 `ResidentCarrierReplay` 零模型（缓存检测替身、只读数据根），但其文档写明每次运行计入 `P1-ENG-ACQ-001` 消耗账本 2 次部分序列回放（该项 `PAUSED_BY_USER`），本信封未覆盖该维度。
- Mac `outputs/eng-jet/` 跑前 70,218,799 B ≤ 2 GB（余量充足，不是停因）。
- **结论**：按「预计超任一额度即不跑、停下回用户」**未运行停点全套**；SUB:2 一次全套额度未消费（`full_suite_runs = 0`），四种模型实际加载 0 / 0 / 0 / 0。未改 skip、未改环境变量绕门、未隐藏模型、未用 focused 替代全套。

### 证据同步（执行范围 1，零消耗）

- `-assets.json`「board_manifest.ac12_split.ir21_ir22_reading」：IR-22 具名两条（`./runtime/sr-f/{f3-track,f4-track-drops}/gimbal_command.json`，字段 `command.target_world_m`，路径从 `true_violations` 运行时解析）单列，扣除后真正隔离违规 0；`kept_original` 记原 `true_violation_count = 2`、`ac12_clean = false` 与原扫描指针，原 `violations`、`true_violations` 列表不改。IR-21：本机取回的 f3/f4 `track-records.jsonl`（1,500 / 284 行）全部为 `loop_state`、内容禁键命中 0。不宣称 AC-12 已验收。
- `-relay.json`「contract_readings_full_suite」：AC-4 修订 2 链路事件分列（f2/f3 各启动 connect 1、收工 disconnect 1、传输中 0；末送包与收工时刻；轮间板侧物理链路事件原因未明、不外推长期稳定）；AC-5 修订 1 分母分列（回声 1,500；真实回程/端到端 29、`frame_age_ms` 1,500、`capture_age_s` 1,498、`load_elapsed_s` 28）；`kept` 记 S1/S2 `STOP`、SR `PASS`、双 `RESUMED_AFTER_USER_RULING` 与账本标题、IR-20。原 forward/return/disconnect 小节与 verdict 不改。
- `-ledger.json`：`envelope.sub2` 与 `dimensions.mac.sub2`（request_id、授权标题、已签范围、四种模型累计加载、全套次数、跑前核对）；`dimensions.mac.models = 0`；`pending_user` (h)–(n) 原样（(n) 仍只签阶段 A，SUB:2 不是阶段 B）；`within_envelope: true`、Assets/controller/config diff 为空。
- `-report.md` §2g 与 §6 现状行。代码：`tools/eng_jet/common.py`（SUB:2 常量）、`ledger.py`（`sub2_dimension` 与三类事件）、`evidence.py`（`sync-full-suite` 子命令）；测试：`tests/test_eng_jet_guards.py` 新增 `LedgerSub2`、`ContractSyncFullSuite`。focused `test_eng_jet_*` 72/72（`docs/evidence/P1-ENG-JET-001-focused-tests.log`）。

### AC 逐条指针（K1K3K4全套）

| AC | 本轮状态 | 指针 |
|---|---|---|
| AC-1 | 不变（S0 `PASS`） | artifact: `docs/evidence/P1-ENG-JET-001-env.json`；test: `tests/test_eng_jet_bench.py`（`S0Verdict`）、`tests/test_eng_jet_guards.py`（`NoSystemSettingChanges`） |
| AC-2 | 不变：S1 `STOP(FP16_BOX_DIVERGENCE)`，不记满足 | artifact: `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1」；cmd: `python -m tools.eng_jet.fastlayer_bench`；test: `tests/test_eng_jet_bench.py`（`S1Comparison`、`InjectionOnly`、`TrtexecParse`） |
| AC-3 | 不变：S2 `STOP(FRAME_DROP)`，不记满足 | artifact: `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S2」；test: `tests/test_eng_jet_bench.py`（`S2Pieces`） |
| AC-4 | 读数不变，按修订 2 补分列；是否满足由核对/复核判定 | artifact: `docs/evidence/P1-ENG-JET-001-relay.json`「forward」「contract_readings_full_suite.ac4_rev2」；test: `tests/test_eng_jet_relay.py::LoopbackTwoProcess::test_atomic_publish_order`、`DesktopStalePointer`、`tests/test_eng_jet_guards.py::ContractSyncFullSuite::test_link_event_split_keeps_startup_and_shutdown` |
| AC-5 | 读数不变，按修订 1 补分母；是否满足由核对/复核判定 | artifact: 同上「return」「contract_readings_full_suite.ac5_rev1」；test: `tests/test_eng_jet_track_responder.py`（`SelectInitBox`、`ResponderInProcess`） |
| AC-6 | 不变；是否满足由核对/复核判定 | artifact: 同上「disconnect」；test: `tests/test_eng_jet_track_responder.py`（`LoopbackTrackWithDrop`、`RecoveryRule`） |
| AC-7/8/9 | `NOT_RUN(阶段 B 信封未签)` | artifact: `docs/evidence/P1-ENG-JET-001-{vlm,quant-equivalence,coresidency}.json` |
| AC-10 | 账本已补 SUB:2；`within_envelope: true`、diff 空；全套 0 次、四种模型 0 | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`「envelope.sub2」「dimensions.mac.sub2」；cmd: `python -m tools.eng_jet.ledger build --base "$BASE" --board-disk-bytes 5163883873`、`git diff --stat "$BASE".."$CAND" -- Assets controller config`；test: `tests/test_eng_jet_guards.py::LedgerSub1`、`LedgerSub2` |
| AC-11 | 不变 | artifact: `docs/evidence/P1-ENG-JET-001-assets.json`「round_f_pre_use_check」「round_f_sr_frames」 |
| AC-12 | 按 IR-21/22 分列：具名协议内容命中 2、扣除后真正隔离违规 0；原 `true_violation_count = 2`、`ac12_clean: false` 保留；是否满足由核对/复核判定 | artifact: `docs/evidence/P1-ENG-JET-001-assets.json`「board_manifest.ac12_split.ir21_ir22_reading」；cmd: `python -m tools.eng_jet.evidence sync-full-suite`；test: `tests/test_eng_jet_guards.py`（`ContractSyncFullSuite::test_ir22_split_is_named_only`、`ProtectedWrites`） |
| AC-13 | 报告 §2g / §6 已同步 | artifact: `docs/evidence/P1-ENG-JET-001-report.md` |
| AC-14 | 执行记录已补本轮行；`UNITY_NA` 待复核附议 | artifact: 本文件「每步执行记录（AC-14）」 |
| AC-15 | 不变（(h)(n) answered、(i)–(m) unanswered 且零执行） | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`「pending_user」 |
| AC-16 | 不变（本轮零上板） | artifact: `docs/evidence/P1-ENG-JET-001-env.json`「sr_system_stack_f.ac16」 |

### 停点自证（K1K3K4全套，workflow §4.3.1 四项）

1. 实现范围与接口冻结：阶段 A 读数齐（S0 `PASS`、S1/S2 `STOP` 经用户裁定续跑、SR `PASS`），IR-21/22 已裁并按裁定分列；本轮代码只改证据生成与账本工具。但全套未跑，若全套出现本批新增失败仍可能改动候选 → **暂不成立（待全套）**。
2. 相称测试：focused `test_eng_jet_*` 72/72；**停点全套未运行**（跑前核对预计超 SUB:2，见上）→ **不成立**。
3. 已知 Unity 失败：不适用（零 Unity；不替代 AC-14 的复核 `UNITY_NA` 附议）。
4. 复核范围、状态板、候选提交与未验证风险：本节、状态板交接行已更新；候选 = 本文件最后一次提交所在的 main 提交（运行时解析）。

结论：**不交 `C1@K1K3K4`**；Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不变。下一步 owner：接受角色（裁定下节读法并把额度请求原样转用户）→ 用户 → 实现角色在新口径下跑一次全套并重判。

### 待裁定（K1K3K4全套；实现读法，交接受角色）

- **IR-23（停点全套的解释器与额度口径）**：合同执行范围 2 写明「需 `lap` 的跟踪器测试只读使用数据根 `.venv-yoloe`」，而在该解释器下 `CarrierSelfTest` 会真实加载 SUB:2 未列名的 det-assoc 冻结检测器 2 次、`ResidentCarrierReplay` 计 ACQ-001 两次部分序列回放。本角色读作：两者都不在 SUB:2 内，须用户另签或由接受角色给出不加载它们的合规跑法后才能跑；本角色未自行改 skip、改环境变量或换解释器。请裁定采用下节哪一项（或其他），并写清全套命令与计数口径。

### 待用户（K1K3K4全套；推荐项只供选择，未执行）

1. **停点全套追加额度**（建议 `request_id` `P1-ENG-JET-001:b0a5f79c:SUB:5`；SUB:4 曾在补跑C 中被建议用于另一用途且未签，为免混淆不复用）：
   - **A（推荐）**：在同一次（仍只一次）停点全套内，追加 Mac mini 本机 CPU 的 det-assoc 冻结检测器（`last.pt`，ultralytics YOLO）加载 ≤ 2 次，并同意 `ResidentCarrierReplay` 的 2 次零模型部分序列回放计入本项而非 ACQ-001；其余（SUB:2 四种模型上限、零 pip、零下载）不变。理由：按合同原样用数据根解释器跑、不动任何 skip 门，覆盖最全；增量只是 5.4 MB 小模型的 2 次 CPU 加载。
   - B：不追加额度，由接受角色 CLARIFY 改用仓库 `.venv-yoloe`（无 `lap`）跑一次全套：所有需 `lap` 的测试会 skip（含上述两类），模型加载 0；代价是需 `lap` 的测试本次不执行、与 R7 基线可比性下降。
   - 若都不选：全套继续不跑，自证第 2 项不成立，不能送 `C1@K1K3K4`。

## K1K3K4全套CPU1执行记录与停点自证（2026-10-03，Mac mini 离线；Dispatch-Id `P1-ENG-JET-001-K1K3K4全套CPU1-20261003T205839Z-8433`）

依据：提案决策记录「CPU-1 落实与下一实现范围（2026-10-03，CLARIFY）」步骤 1–5（AC-10 修订 6）、「SUB:5 A 落实与 CPU 执行方案核对」（AC-10 修订 5）、「SUB:2 落实：§5 Mac 与 IR-9」；账本 2026-10-03「…用户选 SUB:5 CPU 执行方案 CPU-1…」「…用户选 SUB:5 方案 A…」「…用户按推荐签发 SUB:2…」「…用户授权本次破例并行…」（本轮属线 A）。本轮未启动 Unity、未 ssh 上板、未重跑 S1/S2/SR、未写主树 `runtime/` 与数据根、零 pip、零下载、零新增模型、未设任何环境变量。

### 步骤 1：CPU-1 测试改动与静态核对

- 改动（开工提交，`git log --format=%H --grep='^P1-ENG-JET-001 K1K3K4全套CPU1 开工'` 运行时解析）：`tests/test_det_assoc_carrier.py:CarrierSelfTest` 两例的 `create_tracker("det-assoc-v1")` → `DetAssocTracker(spec_path=SPEC, device="cpu")`；首例导入增 `controller.det_assoc_tracker.DetAssocTracker`、`controller.trackers` 导入去掉 `create_tracker`（保留 `clip_box_norm`），次例导入改为 `DetAssocTracker`。默认 compat、真实默认加载器/关联器，未传替身、未关版本核验。
- 静态核对（`ast` 逐节点对比 HEAD 与工作树，未导入测试模块、未加载模型）：顶层节点 33 / 33；差异只有上述两例的导入语句与两处构造调用；`CarrierSelfTest` 内 `assert*` 调用 16 / 16；类级 `skipUnless(_ready(), …)` 不变；其余语句 AST 完全相同。原文见 `-ledger.json`「dimensions.mac.sub2.prechecks」本轮条目 `static_test_change_check`。未在全套外跑这两例。

### 步骤 2：跑前只读核对（结论：可跑）

原文为 `outputs/eng-jet/P1-ENG-JET-001/ledger-events.jsonl` 的 `mac_full_suite_precheck`（`round = K1K3K4全套CPU1`，记录于全套启动前），已汇入 `-ledger.json`「dimensions.mac.sub2.prechecks」（原 K1K3K4全套条目保留不改）。

- **测试树闭集**：以 FRAME-001 R7 全 tests 树闭集审计为底（`docs/evidence/P1-ENG-FRAME-001-R7-full-suite-preparation.md`）；自 R7 全套提交以来 `tests/`、`controller/`、`tools/` 只新增 `tools/eng_jet/*` 与四个 `tests/test_eng_jet_*.py`（假插件/假工厂/注入 `yolo_factory`，无真实加载器）及本轮两处构造改动。另核本机（mini）环境门与 R7（Air）的差异：数据根存在（Carrier/Resident 门成立）；数据根解释器有 `tokenizers`/`huggingface_hub` 但无 `transformers`，eng_sft 测试替换 `_load_tokenizer`、`FakeEngine.ensure_base` 返回本地目录，`tokenizer_files` 不走 `hf_hub_download`。
- **预计（上界）**：det-assoc 2（SUB:5 A ≤ 2）；NanoTrack 构造尝试 ≤ 2、真实权重读取 0（主树 `runtime/models/nanotrack-v2/` 不存在：pinned 两例 skip，`test_preflight_reanchor_env` 两条真实 CLI 子进程在 `_verify_model_file` 读权重前失败；SUB:2 ≤ 4）；YOLOE 0、DINOv2 0（主树无文件且构造在 Nano 之后）；CSRT 尝试 ≤ 2、真实实例 0（opencv 5.0.0 无 `TrackerCSRT_create`）；其他模型 0。`ResidentCarrierReplay` 零模型、2 次部分回放（各 60 帧）归本项。
- **执行设备**：Carrier 两例显式 `cpu`（跳过 `_resolve_device`）；Resident 为显式 `cpu` + 缓存替身；本机 MPS 可用，但全套内无走 `_resolve_device` 的真实推理。
- **自动安装分支**：`last.pt` 的 `data.pkl` 以 `pickletools` 列出的 GLOBAL 模块（torch.* 与 `ultralytics.nn.{tasks,modules.block,modules.conv,modules.head}`）在数据根 site-packages 全部可定位，不触发 `torch_safe_load` 的 `ModuleNotFoundError` → 自动安装分支（未反序列化）。
- **Mac outputs**：跑前 70,222,459 B ≤ 2 GB。
- **无法消除、已披露的副作用**：合同禁止附加离线变量，故未设 `YOLO_OFFLINE`；ultralytics 导入时对 one.one.one.one / dns.google 做 DNS 解析，本机 Ultralytics `settings.json` 的 `sync = True`，predict 起始回调可能发匿名 usage 事件。非下载、非安装；未监测流量，不能断言外联为 0。全套日志无下载/安装行。

### 步骤 3：一次全套（已执行，不重跑）

- 命令（仓库根目录，逐字，未加 `-v`、未附加环境变量）：`~/TetheredDroneTracking-full/.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-JET-001-full-suite.log 2>&1`
- 2026-10-03T21:06:48Z–21:10:46Z，执行时 HEAD = 开工提交（同上运行时解析），工作树只有本轮无关的线 B 提案未提交编辑（不在 tests 读取范围）。退出码 1。
  - **证据整理1A 读法纠正（AC-13/14）**：上句「执行时 HEAD」是执行起始版本，沿开工主题解析（`$START_CPU1`）；ledger `full_suite_run_items[].tested_head` 与 `git_diff_assets_controller_config.head_at_build`（`$LEDGER_HEAD`）是另一标识，其所在提交为线 B 的 supervisor 核销提交、提交时间在全套窗口内，**不能称跑前 HEAD 采样**。两者间 tests/tools/controller/Assets/config 零 diff（`git diff --stat "$START_CPU1" "$LEDGER_HEAD" -- tests tools controller Assets config` 为空），只证明本次运行代码相同，不补造当时采样；原机器字段不改写。
- 摘要：**`Ran 2136 tests in 235.682s` / `FAILED (failures=27, errors=10, skipped=56)`**；失败+错误 37 个名称（含子测试）。日志 `docs/evidence/P1-ENG-JET-001-full-suite.log`（550 行）。

### 步骤 4：基线已有失败与本批新增失败分列

基线 = FRAME-001 R7 全套（`docs/evidence/P1-ENG-FRAME-001-R7-full-suite-result.json`「current_failure_names」，25 名；R7 日志 `git log -1 --format=%H -- docs/evidence/P1-ENG-FRAME-001-R7-full-suite.log` 运行时解析）。R7 与本轮的环境差异：R7 在 MacBook Air、仓库 `.venv-yoloe`（3.12.13）、受限沙箱拒绝 loopback 绑定、设四个离线变量、无数据根、主树有 YOLOE/DINOv2 权重；本轮在 Mac mini、数据根 `.venv-yoloe`（3.12.14）、loopback 可绑定、无离线变量、有数据根、主树 `runtime/` 只有 README。

| 分类 | 数 | 名称与原因 |
|---|---:|---|
| 基线已有、本轮仍在 | 7 | `test_eng_sft_{audit,build,cloud,evaluate}`、`test_language_k_binding` 五个模块导入失败（site-packages 同名 `tests` 包遮蔽；证据整理1A 区分：四个 eng_sft 报 `No module named 'tests.fixtures'`，language_k_binding 报 `No module named 'tests.test_language_selector'`）；`test_trackers…test_pinned_opencv_csrt_initializes_and_updates`（ERROR）与 `test_track_loop…test_cli_runs_pinned_csrt_to_a_versioned_summary`（FAIL）：opencv 5.0.0 无 `TrackerCSRT_create` |
| 基线有、本轮未出现 | 18 | 12 条 loopback `socket.bind` EPERM（R7 沙箱所致，本机可绑定；证据整理1A 读法：无逐名记录，只记「未出现于失败列表」，不称修复/通过）；`test_dist_data_round4` 3 条、`test_dist_data_round8` 2 条、`test_rate3_protocol…test_archived_decision_a_recomputes_identically` 1 条（主树缺归档 → 本机按各自 skip 门跳过，**不是修复**；无 `-v` 不能逐名区分跳过与通过） |
| **本批新增：CPU-1 直接相关** | 1 | **`test_det_assoc_carrier.CarrierSelfTest.test_carrier_matches_caliber_b_from_first_update`（FAIL）**：逐帧 `(state, box, reason)` 与口径 B 参考（参考 `plugin_manifest.device = mps`）不完全相等，`mismatches = [2, 4, 5, 6, 8, 12, 17, 18, 19, 20]`（767 个 update 帧中 10 帧）；首个不一致为帧 2（**证据整理1A 纠正**：`mismatches` 是 update 条目从 0 起的索引，carrier 源于 `records[1:]`、update 从帧 1 起，索引 2 对应 `frame_id=3`，不可写作帧 2；下列形态只适用于该条）：state/reason 相同，box 宽 0.09842786788940433（CPU）vs 0.09842791557312008（参考），差约 4.8e-8，其余三分量逐位相同。其余 9 帧的差异形态日志未打印、未核实（不重跑）。之前的断言（权重 sha、init 帧、`library_frame_id`、长度）均已通过；比较后的 confidence_source、观测桥字段集、临时目录外写入比较**未执行**（证据整理1A 补记）。次例 `test_init_false_uses_existing_failure_path` 未出现在失败列表（结合共用类级门与无方法 skip，可读作执行通过；不恢复真实工厂集成覆盖）。按合同如实保留，不换基线、不放宽断言、不改数、不重跑 |
| **本批新增（相对 R7）：环境差异，非本批改动** | 29 | `test_scene006_probe` 的 29 个测试/子测试（`Scene006ProbeTests`、`Scene006CandidateManifestTests`、`Scene006CandidateManifestP2Tests`、`Scene006AppearanceToleranceTests`、`Scene006StrictJsonTests`；FAIL 为 `tool_state 'FAIL' != 'AWAITING_EMBEDDING_FEASIBILITY_REVIEW'` 等，ERROR 为 `result["recall"]` 为 `None`）。静态归因：`tools/run_scene006_probe.py` 冻结处置链第 1 步「权重哈希绑定」读取 `config/detector-reanchor.models.json` 指向的主树 `runtime/yoloe/…`、`runtime/models/dinov2/…` 与 NanoTrack ONNX，本机主树均不存在 → `FAIL_WEIGHT_HASH`、无 recall；R7 在主树有这些文件的 Air 上通过。`tests/test_scene006_probe.py`、`tools/run_scene006_probe.py`、`controller/reanchor_models.py` 自 R7 全套提交以来零 diff。该归因为读码所得，未在补齐资产的环境验证。**证据整理1A（AC-13 修订 3，用户选环境分列）**：25 FAIL + 4 ERROR，按类 Probe 10 / CandidateManifest 1 / CandidateManifestP2 7 / AppearanceTolerance 10 / StrictJson 1；这些调用只注入 proposer/embedder、未传 `path_resolver`，`run_probe` 先走 `verify_weight_binding`，由 `controller/reanchor.py:verify_file` 检查主树 YOLOE 权重，**首个 YOLOE 检查即拒绝**（之后的 DINOv2/NanoTrack 检查未到达）；`controller/reanchor.py`、`config/detector-reanchor.models.json` 自 R7 全套提交亦零 diff。仍为相对 R7 新增 29 条、不记通过，后续断言行为未验证 |

skip 56（R7 19）：增量来自本机主树缺归档/模型资产与冻结资产的各类 skip 门；无 `-v`，日志不列 skip 名，不能逐名对照（证据整理1A：只有聚合可比，上表「6 条转 skip」是静态门归因，不是逐名记录）。

**计账（AC-10 修订 5/6，唯一 `docs/evidence/P1-ENG-JET-001-ledger.json`）**：`dimensions.mac.sub2.full_suite_runs = 1`（≤ 1，SUB:5 共用）；SUB:2 四种：NanoTrack 2（保守上界，构造尝试、真实权重读取 0）/ YOLOE 0 / DINOv2 0 / CSRT 2（失败、实例 0），`other_model_loads = {}`；`dimensions.mac.sub5`：det-assoc 加载 2（≤ 2，均构造成功，CPU）、具名部分回放 2（≤ 2，各 60 帧，零模型，不扣 ACQ-001）；`dimensions.mac.models = 6`（回放不计）；Mac outputs 70,231,574 B；`within_envelope: true`；Assets/controller/config diff 空。各模型计数未插桩，NanoTrack/CSRT 为静态上界，det-assoc 与回放按门成立与失败列表读出。**一次全套额度已用尽**，再跑须用户另签。

### AC 逐条指针（K1K3K4全套CPU1）

| AC | 本轮状态 | 指针 |
|---|---|---|
| AC-1…AC-9、AC-11…AC-13、AC-15、AC-16 | 读数与上轮相同（本轮零上板）；是否满足由核对/复核判定 | 见上节「K1K3K4全套执行记录与停点自证」的「AC 逐条指针」同名行；artifact: `docs/evidence/P1-ENG-JET-001-report.md` §2h |
| AC-10 | 全套 1/1、SUB:2 与 SUB:5 计数如上、`within_envelope: true`、diff 空 | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`「envelope.sub5」「dimensions.mac.sub2」「dimensions.mac.sub5」；cmd: `python -m tools.eng_jet.ledger build --base "$BASE" --board-disk-bytes 5163883873`、`git diff --stat "$BASE".."$CAND" -- Assets controller config`；test: `tests/test_eng_jet_guards.py::LedgerSub2`（`sub5_dimension` 无专门单测，见下「未验证」） |
| AC-14 | 执行记录见本节步骤 3；`UNITY_NA` 待复核附议 | artifact: 本文件本节；`docs/reviews/P1-ENG-JET-001.md`（附议，未开） |
| 全套（workflow §4.3.1 第 2 项） | 已跑 1 次，新增失败 30 名（CPU-1 相关 1 + 环境差异 29） | artifact: `docs/evidence/P1-ENG-JET-001-full-suite.log`；test: `tests/test_det_assoc_carrier.py::CarrierSelfTest` |

### 停点自证（K1K3K4全套CPU1，workflow §4.3.1 四项）

1. 实现范围与接口冻结：本轮代码只改 CarrierSelfTest 两处构造与 ledger SUB:5 计账；阶段 A 读数不变。但 Carrier CPU 比较新增失败的处置未定，候选可能再变 → **暂不成立（待裁定）**。
2. 相称测试：全套已跑一次，但有本批新增失败（Carrier CPU 逐帧比较 1 条；scene006 29 条相对 R7 为新增、读码归因环境差异）→ **不成立**。
3. 已知 Unity 失败：不适用（零 Unity；不替代 AC-14 复核附议）。
4. 复核范围、状态板、候选提交与未验证风险：本节、报告 §2h、ledger、状态板交接行已更新；候选 = 本文件最后一次提交所在 main 提交（运行时解析）。

结论：**不交 `C1@K1K3K4`**；Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不变。下一步 owner：接受角色（裁定下节读法）→ 用户。

### 未验证项与限制（本轮）

- `tools/eng_jet/ledger.py:sub5_dimension` 与 `common.ENVELOPE_SUB5` 为本轮新增，派发禁止改其他测试，故无专门单测；全套覆盖既有 `LedgerSub2` 未回归，`sub5` 的上限判定只做过开发期手工调用（det-assoc 3 或第二次全套 → `within: false`）。
- Carrier 其余 9 个不一致帧的差异形态、Resident 是否真实执行（vs 跳过）、NanoTrack/CSRT 实际尝试次数均未插桩、未重跑核实。
- 未设 `YOLO_OFFLINE`：DNS 探测与匿名 usage 事件可能发生，未监测。

### 待裁定（K1K3K4全套CPU1；实现读法，交接受角色）

> 证据整理1A 注：IR-24/25 已由接受答复（提案「待裁定」IR-24/25 与「K1K3K4全套CPU1记录核对」），用户 10-03 裁定「1A，2环境分列」（账本「P1-ENG-JET-001 — 用户裁定线 A 全套结果…」），接受落实为 AC-10 修订 8 / AC-13 修订 3（提案「1A落实与证据整理」）。下两条与下节为裁定前原文，现行读法见「K1K3K4证据整理1A：候选冻结与停点自证」。

- **IR-24（Carrier CPU 逐帧比较失败的读法）**：CPU-1 下首例在 767 帧中 10 帧与 MPS 参考不完全相等（首帧差约 4.8e-8、state/reason 相同）。本角色读作：按 AC-10 修订 6「失败如实保留并停下」，自证第 2 项不成立；是否以「已知设备差异、记录不通过」放行 C1，或需用户另定（见下「待用户」1），请裁定。本角色未改断言、未换基线、未重跑。
- **IR-25（scene006 29 条的基线归属）**：相对 R7 为新增名称，但读码归因为本机主树缺 re-anchor/NanoTrack 权重（`FAIL_WEIGHT_HASH`），本批未触及相关代码。本角色读作：记为「本机环境基线失败」，不是本批引入；请裁定能否按此分列（复核可核实读码归因）。本角色不向主树 `runtime/` 补资产（合同禁止写主树 `runtime/`）。

### 待用户（K1K3K4全套CPU1；推荐项只供选择，未执行）

> 证据整理1A 注：两项均已由用户裁定（1A、2 环境分列）。A 项理由中的「差异在 1e-7 量级、不涉及状态/原因」「其余流程断言均通过」只是裁定前表述：已核实的仅索引 2（`frame_id=3`）一条，其余 9 条形态未知，比较后断言未执行；不再作为现行读法。

1. **Carrier CPU 比较失败的处置**（经接受角色 IR-24 读法后转用户）：
   - **A（推荐）**：接受「CPU 与 MPS 参考存在浮点级差异、该例记为已知失败」，不改断言/基线，候选以此进 C1/R1，失败与差异作为未闭限制随候选交复核。理由：差异在 1e-7 量级、不涉及状态/原因，且其余流程断言均通过；再改测试或换设备都要新授权与第二次全套。
   - B：签发新口径（例如 CPU 参考重算或 MPS 推理）后再跑一次全套：需新的模型/设备/全套额度，并改变测试基线或执行设备。
2. **scene006 29 条**：按 IR-25 读作环境基线（推荐，理由：相关代码零 diff，失败发生在冻结处置链第 1 步权重哈希绑定）；若要求在本机实测通过，须另行授权把 re-anchor/NanoTrack 权重放入主树 `runtime/`（本项不做）并另签一次全套。

## K1K3K4证据整理1A：候选冻结与停点自证（2026-10-03，Mac mini，零消耗；Dispatch-Id `P1-ENG-JET-001-K1K3K4证据整理1A-20261003T213957Z-f760`）

依据：提案决策记录「1A落实与证据整理（2026-10-03，CLARIFY）」步骤 1–6（AC-10 修订 8、AC-13 修订 3）、「K1K3K4全套CPU1记录核对」、「待裁定」IR-24/25、§3.4、§7.1；账本 2026-10-03「P1-ENG-JET-001 — 用户裁定线 A 全套结果：Carrier CPU 失败选 A（具名例外进 C1/R1）、scene006 29 条按环境原因分列（supervisor 会话代录）」授权范围 (1)–(3)，及同日 CPU-1、SUB:5 A、SUB:2、破例并行（本轮属线 A）条目。本轮**未跑任何测试**、未构造/加载模型、未推理、未回放、未上板/ssh、未下载安装、未设或改 skip/环境变量；运行时代码、测试、工具、配置、原始日志与 JSON 原字段零改动；只改本文件与报告的叙述/索引、状态板本项交接行（及本项 Log 条目、Gate 行证据指针）。

### 1. 现行读法同步（步骤 1、3）

- **Carrier（AC-10 修订 8，用户具名例外）**：`tests/test_det_assoc_carrier.py::CarrierSelfTest::test_carrier_matches_caliber_b_from_first_update` 失败如实保留。日志 `AssertionError: Lists differ: [2, 4, 5, 6, 8, 12, 17, 18, 19, 20] != []` 是 767 个 update 条目（参考 `docs/evidence/P1-ENG-FAST-002-replay.json`「carrier_reference」：帧 768、`per_frame` 767、`plugin_manifest.device = mps`）中从 0 起的索引；测试以 `enumerate(zip(carrier, plugin))` 比较、carrier 源于 `records[1:]`、update 从帧 1 起，故**索引 2 = `frame_id=3`**（不是帧 2）。日志只打印该条：state `TRACKING`/reason `None` 两侧相同，box 宽 0.09842786788940433（CPU）vs 0.09842791557312008（参考），差约 4.8e-8，其余三分量相同；**其余 9 条形态未知**，不能推广为全体差异在 1e-7 级或 state/reason 全同。比较前四类断言（权重 sha、init、`library_frame_id`、长度）已执行通过；比较后的 confidence_source、观测桥字段集、临时目录外写入比较**未执行**。次例无失败记录，可读作执行通过，但不恢复真实工厂（`create_tracker`）集成覆盖。用户例外只覆盖本停点 workflow §4.3.1 第 2 项的这一具名用例：**不记测试通过**、不改断言/基线/参考/设备/阈值/AC 判据，不预定 C1/R1 结论，复核可判阻断；不扩大到其他未披露失败。
- **全套分列（相对 FRAME-001 R7 `current_failure_names` 25 名；本轮从原日志提取 FAIL/ERROR 37 名做集合比较复核一致）**：已有仍在 **7** = 五个导入错误（`test_eng_sft_{audit,build,cloud,evaluate}` 四个报 `No module named 'tests.fixtures'`；`test_language_k_binding` 报 `No module named 'tests.test_language_selector'`）+ CSRT 两入口（opencv 5.0.0 无 `TrackerCSRT_create`）；未出现 **18** = 12 条 R7 旧 loopback 绑定拒绝 + 6 条有缺归档静态 skip 门（无逐名 skip 日志，**不称修复/通过**）；新增 **30** = Carrier 1 + scene006 环境 29。skip 19→56 只有聚合可比，不能逐名对照。
- **scene006（AC-13 修订 3，用户选环境分列）**：29 条 = 25 FAIL + 4 ERROR（Probe 10 / CandidateManifest 1 / CandidateManifestP2 7 / AppearanceTolerance 10 / StrictJson 1，本轮按日志复数）；仍为**相对 R7 新增**，不改作 R7 原有失败、不记通过。静态归因：调用只注入 proposer/embedder、未传 `path_resolver`，`tools/run_scene006_probe.py:run_probe` 先走 `verify_weight_binding`，`controller/reanchor.py:verify_file` 检查主树 YOLOE 权重即拒绝 → `FAIL_WEIGHT_HASH`、recall 缺省 None，解释状态不符与 None 下标错误；`tests/test_scene006_probe.py`、`tools/run_scene006_probe.py`、`controller/reanchor.py`、`controller/reanchor_models.py`、`config/detector-reanchor.models.json` 自 R7 全套提交零 diff（`git diff --stat "$(git log -1 --format=%H -- docs/evidence/P1-ENG-FRAME-001-R7-full-suite.log)" "$START_CPU1" -- <上列路径>` 为空）。读码归因、未在补齐资产环境验证，后续断言行为未验证；不向主树 `runtime/` 放资产。
- **保持不变**：S0 `PASS`、S1 `STOP(FP16_BOX_DIVERGENCE)`、S2 `STOP(FRAME_DROP)`、SR `PASS`（`RESUMED_AFTER_USER_RULING(S1)` + `(S2)`，SR 5/5 用尽）、S3–S5 `NOT_RUN(阶段 B 信封未签)` 及各自主张上限与 IR-20 限制；计账（全套 1/1、det-assoc 2/2、部分回放 2/2、NanoTrack 2 上界/读权重 0、CSRT 2/实例 0、YOLOE 0、DINOv2 0、`within_envelope: true`）原样。

### 2. 执行版本与取样来源（步骤 2，不手抄 SHA）

- **执行起始版本** = `$START_CPU1`（主题 `^P1-ENG-JET-001 K1K3K4全套CPU1 开工`，`git log main` 仅返回一条）：该提交时间早于全套开始（21:06:48Z）。
- **ledger 机器字段** = `-ledger.json`「dimensions.mac.sub2.full_suite_run_items[].tested_head」与「git_diff_assets_controller_config.head_at_build」（两字段同值，`$LEDGER_HEAD`）：所在提交为线 B「阶段B签发包刷新」的 supervisor 核销提交，提交时间在全套窗口（21:06:48Z–21:10:46Z）内，记录时刻 `recorded_utc` 晚于全套结束——**是另一取样时点，不能称跑前 HEAD 采样**。
- **代码相同的支撑**：`$START_CPU1` 是 `$LEDGER_HEAD` 的祖先，其间只有线 B 两笔提交（提案与派发登记）；`git diff --stat "$START_CPU1" "$LEDGER_HEAD" -- tests tools controller Assets config` 为空。只证明本次运行的代码与两版本一致，不补造当时采样；原字段不改写。
- **全套后至候选的代码**：`git diff --stat "$START_CPU1" "$CAND" -- tests tools controller Assets config .gitignore` 应为空（提交前对工作树与索引核实为空；本轮只改文档）。

### 3. 完整候选范围（步骤 4，冻结）

当前已实现范围的完整声明（不授权新增实现，不删减 §7.1 合同范围；AC-7/8/9 的 S3–S5 未实现、`NOT_RUN`）：

- 忽略规则：`.gitignore`（`/outputs/eng-jet/`）。
- 代码：`tools/eng_jet/{__init__,common,env_probe,fastlayer_bench,replay_publish,relay,track_responder,assets,ledger,evidence}.py`（10 个）。
- 测试：`tests/test_eng_jet_{bench,guards,relay,track_responder}.py`；CPU-1 的 `tests/test_det_assoc_carrier.py`（仅 `CarrierSelfTest` 两处构造与必要导入）。
- §3.4 证据：`docs/evidence/P1-ENG-JET-001-{env,fastlayer,relay,vlm,quant-equivalence,coresidency,assets,ledger}.json`（8 个）、`-report.md`、本文件、`-focused-tests.log`、`-full-suite.log`。
- 混入总 diff、同样列入（不按实现声明排除，由 C1/复核检查）：提案 `docs/proposals/P1-ENG-JET-001-jetson-onboard-feasibility-probe.md`、账本 `docs/authorizations.md`、状态板 `docs/current-status.md`、派发登记 `docs/evidence/supervisor-dispatch.jsonl`、发令表 `docs/evidence/COORD-015-codex-launch-form.md`（COORD-015 Kimi 回退前提补记，非本项）。
- 合计 33 个路径；`Assets/`、`controller/`、`config/`、`runtime/`、工作流基础设施（`AGENTS.md`、`CLAUDE.md`、`docs/*workflow*.md`、`.claude/`、`.cursor/`、`docs/roles/`、`tools/check_*.py`、`tools/githooks/`）、复核与设计文件不在 diff 内。

### 4. 基线/候选解析与 diff 核实（步骤 5）

```bash
BASE=$(git rev-parse "$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4 开工')^")   # 主题仅一条；与 -ledger.json「git_diff_assets_controller_config.base」相同
CAND=$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4证据整理1A 收工')             # 必须仅一条、触及本文件、已推送且为 origin/main 祖先；不用当前 HEAD 替代
git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4证据整理1A 收工' | wc -l           # 应为 1
git diff --name-only "$CAND"^ "$CAND" | grep -x 'docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md'
git merge-base --is-ancestor "$CAND" origin/main && echo ancestor
git diff --name-only "$BASE".."$CAND"                                # 应为上节 33 个路径
git diff "$BASE".."$CAND"                                            # 完整候选 diff（C1/独立复核检查）
git diff --stat "$BASE".."$CAND" -- Assets controller config         # 应为空
```

提交前核实（索引即收工提交的树）：`git diff --cached --name-only "$BASE"` 与上节 33 个路径逐一相同；`-- Assets controller config` 的 stat 为空；diff 中无非预期治理代码。提交后复算结果写在本轮接力报告；若 `pull --rebase` 使线 B 提交落在收工提交之前，其路径以运行时 `git diff --name-only` 为准（线 B 只写提案与派发登记，均已在上表）。

### 5. AC 逐条指针（K1K3K4证据整理1A；冻结候选）

| AC | 本停点状态（不预签 C1/R1） | 指针 |
|---|---|---|
| AC-1 | S0 `PASS`；按 AC-1 修订 1（IR-1/2/10）读法自证满足 | artifact: `docs/evidence/P1-ENG-JET-001-env.json`（`checks`、`readings`、`tegrastats_idle`、`not_executed`）；cmd: `python -m tools.eng_jet.env_probe collect` / `build`；test: `tests/test_eng_jet_bench.py::S0Verdict`、`tests/test_eng_jet_guards.py::NoSystemSettingChanges` |
| AC-2 | 证据项齐（两版引擎 sha/导出参数/TRT 版本、320 帧四分项、`within_50ms`、比对与直方图、不一致帧清单）；verdict `STOP(FP16_BOX_DIVERGENCE)`，用户 (α) 续跑；既往自证不记满足，由 C1/R1 判定 | artifact: `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1」（`engines.640`、`engines.480x640`）、报告 §2d；cmd: `python -m tools.eng_jet.fastlayer_bench`；test: `tests/test_eng_jet_bench.py`（`S1Comparison`、`InjectionOnly`、`TrtexecParse`） |
| AC-3 | 六格读数齐；verdict `STOP(FRAME_DROP)`，用户 (α′) 续跑；30 Hz 未触发；不记满足，由 C1/R1 判定 | artifact: `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S2」、报告 §2e；test: `tests/test_eng_jet_bench.py::S2Pieces` |
| AC-4 | forward 两轮 100% / 0 / 0，修订 1/2 分母与链路事件分列；由 C1/R1 判定 | artifact: `docs/evidence/P1-ENG-JET-001-relay.json`「forward」「rework_rounds」「contract_readings_full_suite.ac4_rev2」；cmd: `python -m tools.eng_jet.relay`（命令逐字见该 JSON）；test: `tests/test_eng_jet_relay.py::LoopbackTwoProcess::test_atomic_publish_order`、`DesktopStalePointer`、`tests/test_eng_jet_guards.py::ContractSyncFullSuite::test_link_event_split_keeps_startup_and_shutdown`、`tests/test_eng_jet_track_responder.py::SrForwardLine` |
| AC-5 | 回声 n=1,500 / 真实回程 n=29 等分母按修订 1 分列；init 框来源检测器；由 C1/R1 判定 | artifact: 同上「return」「contract_readings_full_suite.ac5_rev1」；cmd: `python -m tools.eng_jet.track_responder`（板上）；test: `tests/test_eng_jet_track_responder.py`（`SelectInitBox`、`ResponderInProcess`）、`tests/test_eng_jet_relay.py::ReplayAndEcho` |
| AC-6 | 10 s / 60 s 断链各一次、全字段；由 C1/R1 判定 | artifact: 同上「disconnect」；test: `tests/test_eng_jet_relay.py`（`DesktopNoBacklog`、`LoopbackTwoProcess::test_clock_sync_recovers_after_stall`）、`tests/test_eng_jet_track_responder.py`（`LoopbackTrackWithDrop`、`RecoveryRule`、`ResponderInProcess::test_gap_terminates_without_reseed`） |
| AC-7 | `NOT_RUN(阶段 B 信封未签)`，不声称满足 | artifact: `docs/evidence/P1-ENG-JET-001-vlm.json` |
| AC-8 | `NOT_RUN(阶段 B 信封未签)`，不声称满足 | artifact: `docs/evidence/P1-ENG-JET-001-quant-equivalence.json` |
| AC-9 | `NOT_RUN(阶段 B 信封未签)`，不声称满足 | artifact: `docs/evidence/P1-ENG-JET-001-coresidency.json` |
| AC-10 | 修订 5/6/8：全套 1/1、det-assoc 2/2、部分回放 2/2、`within_envelope: true`、Assets/controller/config diff 空；本轮零消耗、无新额度；`sub5_dimension` 无专门单测 | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`「envelope.sub2」「envelope.sub5」「dimensions.mac.sub2」「dimensions.mac.sub5」「git_diff_assets_controller_config」；cmd: `git diff --stat "$BASE".."$CAND" -- Assets controller config`；test: `tests/test_eng_jet_guards.py`（`LedgerSub1`、`LedgerSub2`）；本停点测试条件 2 的 Carrier 具名例外见上 §1 |
| AC-11 | 各轮使用前 sha 复核一致；阶段 B 资产 `NOT_USED` | artifact: `docs/evidence/P1-ENG-JET-001-assets.json`「round_d_pre_use_check」「round_e_pre_use_check」「round_f_pre_use_check」「round_f_sr_frames」「bundle_s1s2」 |
| AC-12 | 按修订 2/3/4 分列：具名协议内容命中 2 单列、扣除后真正隔离违规 0；原 `true_violation_count = 2`、`ac12_clean: false` 保留；由 C1/R1 判定 | artifact: `docs/evidence/P1-ENG-JET-001-assets.json`「board_manifest.ac12_split」「board_manifest.ac12_split.ir21_ir22_reading」「protected_roots_zero_write」；cmd: `python -m tools.eng_jet.evidence sync-full-suite`；test: `tests/test_eng_jet_guards.py`（`ContractSyncFullSuite::test_ir22_split_is_named_only`、`ProtectedWrites`） |
| AC-13 | 报告 verdict 表/Q1–Q4/建议/不可推出齐；修订 3：scene006 环境分列、版本读法、§2h 已同步 | artifact: `docs/evidence/P1-ENG-JET-001-report.md`（§1、§2h、§3–§6） |
| AC-14 | 每步执行机器/时间/HEAD 已记（含本轮行与版本读法纠正）；`UNITY_NA` **待复核附议**（未开复核文件） | artifact: 本文件「每步执行记录（AC-14）」与本节 §2；`docs/reviews/P1-ENG-JET-001.md`（复核角色新建，实现不写） |
| AC-15 | (h)(n) answered、(i)–(m) unanswered 且对应动作零执行 | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`「pending_user」 |
| AC-16 | 补跑E/F 板上进程启动前环境与外部新写核查已记；CPU1 与本轮零上板 | artifact: `docs/evidence/P1-ENG-JET-001-env.json`「s2_system_stack_e.env.ac16」「sr_system_stack_f.ac16」 |
| §4.3.1 第 2 项 | 全套 1 次：2136 / F27 / E10 / S56；新增 30 = Carrier 具名例外 1 + scene006 环境 29；`test_eng_jet_*` 在全套中无失败（focused 日志 72/72 早于 CPU1 的 SUB:5 计账改动，现行代码以全套为准） | artifact: `docs/evidence/P1-ENG-JET-001-full-suite.log`、`docs/evidence/P1-ENG-JET-001-focused-tests.log`；cmd: `~/TetheredDroneTracking-full/.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-JET-001-full-suite.log 2>&1`（已执行，不重跑）；test: `tests/test_det_assoc_carrier.py::CarrierSelfTest`、`tests/test_scene006_probe.py` |

### 6. 停点自证（workflow §4.3.1 四项，K1K3K4证据整理1A 重判）

1. **实现范围与接口冻结 —— 成立。** 全套后 tests/tools/controller/Assets/config 零变化（§2），完整候选范围按 §3 冻结；IR-1…25 均已答复，IR-24/25 经用户裁定落实为 AC-10 修订 8 / AC-13 修订 3，不再改候选或执行方法。阶段 B（线 B，未签）若日后加代码属另一候选，不在本停点。
2. **相称测试 —— 在用户具名例外下成立（不记通过）。** 停点全套跑一次（2136 / F27 / E10 / S56），基线已有 7 与新增 30 已分列；新增中 Carrier 1 条按 AC-10 修订 8 作本停点具名例外携带进 C1/R1，scene006 29 条按 AC-13 修订 3 作环境覆盖限制携带；其余失败、skip 聚合与未验证项一并披露（§1、§8）。例外明确适用于 `C1@K1K3K4` 与独立 `R1@K1K3K4`（账本授权范围 (1)），复核可判阻断。
3. **已知 Unity 失败 —— 不适用。** 零 Play、Unity 零改动；AC-14 `UNITY_NA` 仍待复核附议，本项不替代附议。
4. **复核范围、状态板、候选提交与未验证风险 —— 成立。** 本节给出候选解析规则与完整范围、AC 指针、复核范围（§7）与未验证风险（§8）；状态板交接行已改为交接受；复核文件 `docs/reviews/P1-ENG-JET-001.md` 由复核角色新建（实现角色不写复核文件，workflow 条件 4 中「复核文件」按此读）。

**结论：四项成立 → 交接受角色 `C1@K1K3K4`**（只读完整候选、AC 与直接关联代码、零测试）；核对后才交新鲜上下文独立 `R1@K1K3K4` 与 AC-14 `UNITY_NA` 附议。Overall 保持 `IMPLEMENTING`（账本破例并行条目 (4)「Gate 行 Overall/Lifecycle 两线均不改」），Lifecycle `ACTIVE` 不变；不记 `DONE`。

### 7. 复核范围（供 C1/R1）

- 候选：§4 规则解析的 `$BASE..$CAND` 完整 diff（§3 的 33 个路径）。
- 重点：Carrier 具名例外的边界（只此一例、9 条未知、比较后断言未执行、工厂覆盖损失）；scene006 静态归因（YOLOE 首检拒绝链）；执行版本两个取样时点；`tools/eng_jet/relay.py` / `track_responder.py` 的 K1 语义（不补发、缺口即 `GAP`、两机时间语义只测量）；`ledger.py` 计账（`sub5_dimension` 无专门单测）；AC-12 具名分列；S1/S2 `STOP` 与续跑标记；AC-14 `UNITY_NA` 附议。
- 重跑额度：全套、det-assoc、部分回放、SR 均无余额；复核如需任何真实模型/回放/全套/SR 重跑，须另申请后才能执行（AC-10 修订 8）。

### 8. 未验证项与已知限制（汇总）

- Carrier：其余 9 个差异条目形态未知；比较后三类断言未执行；两例不经 `create_tracker` 工厂；CPU 结果对 MPS 参考的差异未做成因验证。
- scene006：读码归因，未在补齐 re-anchor/NanoTrack 权重的环境验证，后续断言行为未知。
- 未出现 18 条与 skip 19→56：无逐名记录，不能区分通过与跳过；`ResidentCarrierReplay` 实际执行/跳过未知（门成立后保守计 2 次）；NanoTrack/CSRT 尝试数为静态上界、未插桩。
- 网络：未设 `YOLO_OFFLINE`，DNS 探测与可能的匿名 usage 事件未监测；日志无下载/安装行不证明外联为 0，「离线」仅指任务性质。
- SUB:5：`common.ENVELOPE_SUB5`、`ledger.sub5_dimension` 无专门单测，既有 `LedgerSub2` 无失败不替代 SUB:5 自动覆盖；`within_envelope` 主要比较累计数量，不证明设备/具名范围/网络经运行时检测。
- 继承：S1/S2 `STOP` 原文与主张上限、IR-20 告警影响未明、SR 只代表 mini ↔ Jetson 有线直连且真实回程 n=29、16:52Z 链路抖动原因未明、S3–S5 `NOT_RUN`；板上无 swap/zram。

## K1K3K4C1返工：报告现状/历史分列与候选重冻结（2026-10-03，零消耗；Dispatch-Id `P1-ENG-JET-001-K1K3K4C1返工-20261003T222529Z-257e`）

依据：提案「Contract conformance（核对表）」`C1@K1K3K4` 的 AC-13 行与「C1-AC13-1 与返工边界」「后续复核范围与未决关注项」、决策记录「C1@K1K3K4 核对退回（2026-10-03）」与「1A落实与证据整理（2026-10-03，CLARIFY）」。本轮**未跑任何测试**、未构造/加载模型、未推理、未回放、未上板/ssh、未下载安装；运行时代码、测试、工具、配置、原始日志、JSON 原字段与 verdict 零改动，负结果与原文全部保留；只改报告叙述标注、本文件与状态板本项交接行/Log。

### 1. C1-AC13-1 → 修改位置

| 退回项/同类 | 原表述问题 | 修改（`docs/evidence/P1-ENG-JET-001-report.md`） |
|---|---|---|
| C1-AC13-1（核对点名） | §5 第二条「任何 VLM、共驻、中继正式轮结论（SR、S3–S5 未运行）」无历史标注，与现行 SR `PASS` 冲突，并与其后现行 S2 限制混在一条 | §5 拆为三条：①「（现行）」S3–S5 `NOT_RUN(阶段 B 信封未签)`、SR 已于补跑F 运行 `PASS` 且可推出范围只限上一条；②「（补跑E 原文，补跑E 收工时点）」原句逐字保留并注明「SR 未运行」只代表当时状态（`git log -S` 核实该句由补跑E 收工提交引入）；③「（现行限制，照旧）」S2 读数范围原文不变。S1/S2 `STOP`、IR-20 等限制不动 |
| 同类 1（只读通查发现） | §2g「SUB:2 与停点全套」条写「全套未运行」，节标题只标轮次、无「当时」标注，与现行全套已跑一次冲突 | 条末加「（以上为 K1K3K4全套 收工时状态…本条『全套未运行』不是现状）」，原句不改 |
| 同类 2 | §2h 末条「实现角色已冻结完整候选并重判四项成立，交接受 `C1@K1K3K4`」现已被核对退回取代 | 条末加「（以上为 K1K3K4证据整理1A 收工时状态。）」，另起一条「核对退回后（K1K3K4C1返工，现行）」 |
| 同类 3 | §6 三条以「现状（K1K3K4全套 / 全套CPU1 / 证据整理1A）」开头，字面读作现状但内容（全套未运行、待裁定 IR-24/25、已交 C1）均已被后续轮次取代 | 前缀改为「<轮次> 当时现状（…非现状）」，正文不改；末条前新增「现状（K1K3K4C1返工，现行）」一条 |
| 文首 | 轮次列表 | 标题加「+ K1K3K4C1返工」 |

其余通查（§1 verdict 表与各 `STOP` 段、§2a–§2f、§3 Q1–Q4、§4 建议、§5 其余条、§6 其余条）已带「原文/前轮历史/当时」标注或本身即现行表述，未见同类冲突，未改。

### 2. 候选重冻结与解析规则（BASE 规则不变，不手抄 SHA）

```bash
BASE=$(git rev-parse "$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4 开工')^")   # 不变；主题仅一条，与 -ledger.json「git_diff_assets_controller_config.base」相同
CAND=$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4C1返工 收工')               # 新候选 = 本轮收工提交：必须仅一条、触及本文件、已推送且为 origin/main 祖先；不用当前 HEAD 替代
git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4C1返工 收工' | wc -l             # 应为 1（同轮 supervisor 派发登记提交主题不含「收工」，不命中）
git diff --name-only "$CAND"^ "$CAND" | grep -x 'docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md'
git merge-base --is-ancestor "$CAND" origin/main && echo ancestor
git diff --name-only "$BASE".."$CAND"                                # 复核范围路径（如实列出，不按线 B/治理文件名排除）
git diff "$BASE".."$CAND"                                            # 完整候选 diff
git diff --stat "$BASE".."$CAND" -- Assets controller config         # 应为空
git diff --name-only "$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4证据整理1A 收工')".."$CAND"   # 本次返工增量（含期间 C1/派发登记/账本提交）
```

上一候选（`K1K3K4证据整理1A 收工`）作废为历史候选，其解析规则与 33 路径记录保留在上节「K1K3K4证据整理1A：候选冻结与停点自证」§4，不回改。

### 3. 复核范围（`$BASE..$CAND`）

= 原 33 路径 + 本次返工增量。提交前核实：1A 收工提交之后到本轮开工的提交（C1 派发登记/退回/核销、FRAME-001 补测核销、并行授权代录、本轮派发登记）只触及 `docs/authorizations.md`、`docs/current-status.md`、`docs/evidence/supervisor-dispatch.jsonl`、提案；本轮改 `docs/evidence/P1-ENG-JET-001-report.md`、本文件、`docs/current-status.md`——全部已在原 33 路径内，预计路径数仍为 **33**、无新增路径；实际以提交后运行时 `git diff --name-only "$BASE".."$CAND"` 为准，复算结果写入本轮接力报告。若 `pull --rebase` 使其他会话提交落在收工提交之前，其路径同样计入、不排除。重点与重跑额度同上节 §7（全套、det-assoc、部分回放、SR 均无余额，复核如需重跑须另申请）；本次返工增量只需核对报告分列是否消除 C1-AC13-1 与上表同类冲突。

### 4. AC 指针变化

仅 AC-13：artifact `docs/evidence/P1-ENG-JET-001-report.md`（§5 三条分列、§2g/§2h 时点标注、§6 现状/当时现状分列）；其余 AC-1…16 指针与状态同上节 §5，不变，不预签 C2/R1。

### 5. 停点自证（workflow §4.3.1 四项，K1K3K4C1返工 重判）

1. **实现范围与接口冻结 —— 成立。** 本轮只改文档；`git diff --stat` 自 1A 候选至本轮工作树对 tests/tools/controller/Assets/config/.gitignore 为空；完整范围仍按上节 §3 声明，无新增实现。
2. **相称测试 —— 在用户具名例外下成立（不记通过），照旧携带。** 全套 1 次（2136 / F27 / E10 / S56）读数不变；Carrier 具名例外（AC-10 修订 8）与 scene006 环境覆盖限制（AC-13 修订 3）照旧携带进 `C2@K1K3K4` 与独立 `R1@K1K3K4`，**不记通过**，复核可判阻断；纯文档返工无需也未跑测试（无额度）。
3. **已知 Unity 失败 —— 不适用。** 零 Play、Unity 零改动；AC-14 `UNITY_NA` 仍待复核附议。
4. **复核范围、状态板、候选提交与未验证风险 —— 成立。** 本节给出新候选解析规则、返工增量与复核范围；未验证风险同上节 §8 不变；状态板交接行改为交接受 `C2@K1K3K4`；复核文件由复核角色新建（实现不写）。

**结论：四项成立 → 交接受 `C2@K1K3K4`**（本停点核对退回已用 1 次，C2 不再退回，照交独立 `R1@K1K3K4` 并携带核对表与未决项）。Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不改；不记 `DONE`。

## K1K3K4R1注记修补：R1-1…R1-4 零消耗落实、focused 与精确缺额（2026-10-04，Mac mini，零模型；Dispatch-Id `P1-ENG-JET-001-K1K3K4R1注记修补-20261004T005403Z-afd4`）

依据：复核 `docs/reviews/P1-ENG-JET-001.md`「R1@K1K3K4」§3 R1-1…R1-4 原文与具名补丁；提案决策记录「R1消费：阶段 A 候选通过与剩余路径（2026-10-03）」补丁表、开轮裁定与 A补丁:2；账本 2026-10-04「P1-ENG-JET-001 — 用户选线 A 先做零消耗修补（A补丁:2 推荐路径）」（**不签任何额度**，原 Carrier/scene006 用户例外不自动延长）。本轮**未跑全套**、未加载/构造任何真实模型、未推理、未回放、未上板/ssh、未下载安装（含 pip）、未设或改 skip/环境变量；`Assets/`、`controller/`、`config/`、冻结规格/权重、帧与控制协议零改动；原始收据、`-relay.json`/`-assets.json`/`-ledger.json` 原字段与全部历史判定不改写、不重算（本轮未运行 `evidence`/`ledger build`/`relay analyze` 的写证据命令），f4 等历史读数**不是**补丁后实测。

### 1. 本轮修改（逐注记）

| 注记（依据） | 修改 | 覆盖（零模型） |
|---|---|---|
| R1-1（`BC-6`→AC-6） | `tools/eng_jet/relay.py`：`BoardRelay.run` 接受新连接改调新方法 `adopt_link`（关闭旧连接、`members.clear()` 后**加 `_last_return.clear()`**，即复核具名补丁）；回程一轮提为 `return_once()`（`return_watch` 循环调用，判据与收据不变）。重连后每个回程文件的当前版本重发一次，仍只发当前版本、不补发历史版本（§3.2）。 | `tests/test_eng_jet_relay.py::BoardRelayInProcess::test_reconnect_resends_current_return_version`（`FakeLink` 模拟两次连接；同连接内去重、新连接一轮内重发）。红：把 `adopt_link` 换回不清 `_last_return` 的旧语义后本例 FAIL（开发期一次性核对） |
| R1-2（`BC-4`→AC-4 修订 2） | `relay.analyze`：去掉 `link_events` 的 `[:50]` 截断，另给 `link_events_total`；`evidence._forward_section` 在分析结果含该键时带出；`evidence._link_event_split(events, total=None)` 读全量列表，新增 `raw_count`/`declared_total`/`truncated`：声明总数大于列表、或无总数且长度达旧截断长度 50（`LEGACY_LINK_EVENTS_CAP`）时 `in_transfer_event_count = None`（不从可能截断的列表派生计数）；`contract_readings_relay` 传入 `link_events_total`。历史 f2/f3 各 2 条，按新函数仍为 `truncated=False`、传输中 0，原 JSON 不重算。 | `tests/test_eng_jet_relay.py::AnalyzeLinkEventsFull`（合成 61 条收据，`analyze` 全量保留；旧截断语义下 ERROR）；`tests/test_eng_jet_guards.py::ContractSyncFullSuite::test_link_event_split_reads_full_list_and_refuses_truncated` |
| R1-3（`BC-12`→AC-11/12） | `tools/eng_jet/assets.py`：新增纯参照 `docs/evidence/P1-ENG-JET-001-a7-frame-sha256.jsonl.gz`（每行只有 `frame_id`、`sha256`，由 `python -m tools.eng_jet.assets derive-frame-reference` 从 `P1-ENG-FAST-002-dataset-frames.jsonl.gz` 投影，gzip `mtime=0` 确定性字节）；`frame_reference()` 改读纯参照，读取方逐行拒绝多余键/非 64 位十六进制 sha/非 a7 前缀；原读法保留为 `legacy_frame_reference()`，`LEGACY_REFERENCE_NOTE` 标明「原参照含标签字段（positives、target_visible_flag、ignores 等）、仅投影 sha、不上板/不进插件」；`verify_frames` 今后输出 `reference`（纯参照）、`reference_keys`、`reference_derived_from`、`reference_note`。原文件只读、未改；纯参照不在任何到板代码束内（`BUNDLE_FILES` 不变）。历史 `-assets.json.frames[].reference` 仍指向原文件（历史运行确实用了原文件），不改写；「仅投影 sha」的注明见本节与代码常量。 | `tests/test_eng_jet_guards.py::PureFrameReference`（投影丢弃标签键与冲突拒绝；派生文件仅两键、来源 sha 不变、两次派生字节相同；读取方拒绝含 `positives` 的行；已提交纯参照与原文件投影逐项相等） |
| R1-4（`BC-10`→AC-10） | `tools/eng_jet/evidence.py`：`relay_doc_f` 内 `disconnect_ok` 合成式提为具名纯函数 `disconnect_pass(drops, exit_codes)`（判据逐字不变；缺 `disconnects` 键时判假而非抛错）。`tools/eng_jet/ledger.py`：`mac.pip` 与 `system_settings.changed` 仍为写定常量，`build` 输出逐字附 `pip_basis`/`basis`（「常量断言（未测量）…不是动态检测」），并新增 `within_envelope_basis`（只比较已记账事件累计数量，不检测执行设备、具名范围、网络外联或系统设置）。 | `tests/test_eng_jet_guards.py::LedgerSub5`（det-assoc ≤ 2、部分回放 ≤ 2、与 SUB:2 共用全套 ≤ 1、各越界为假、det-assoc 不进 `sub2.other_model_loads`；常量字段带断言标注）；`::DisconnectPass`（通过线每个条件单独证伪） |

纯参照派生核验（工程轨道 §7：计数、哈希、来源指针）：来源 43,535 行 → a7 前缀 3,168 帧、无冲突；纯参照 61,905 B；来源与输出 sha 均运行时复算（`python -m tools.eng_jet.assets derive-frame-reference` 打印 `source_sha256`/`out_sha256`，确定性可复现；本文件不手抄）。`test_committed_pure_reference_matches_legacy_projection` 断言纯参照与原文件投影逐项相等。

### 2. focused 结果（零模型）

- 命令（仓库根，未加 `-v`、未附加环境变量）：`.venv-yoloe/bin/python -m unittest discover -s tests -p 'test_eng_jet_*.py' > docs/evidence/P1-ENG-JET-001-R1notes-focused-tests.log 2>&1`（仓库 `.venv-yoloe`，Python 3.12.14；2026-10-04 约 01:00Z，Mac mini）。
- 摘要：**`Ran 82 tests` / `OK`**（原 72 + 本轮新增 10）。日志：`docs/evidence/P1-ENG-JET-001-R1notes-focused-tests.log`；原 72/72 日志 `-focused-tests.log` 保留不覆盖。
- 零模型说明：`InjectionOnly` 只导入 ultralytics、以假 `yolo_factory` 构造（读冻结权重文件算 sha，非模型加载）；新增用例只用合成收据/假连接/临时 gzip 与只读 `git diff`。开发期另跑过同命令一次（输出写 scratchpad，同为 82/OK）及上表两条红核对（进程内替换旧语义，不改仓库文件）。

### 3. 新候选解析与复核范围（不手抄 SHA）

```bash
CAND=$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4R1注记修补 收工')                # 须仅一条、触及本文件、已推送且为 origin/main 祖先
PASSED=$(sed -n 's/^passed_candidate: \([0-9a-f]\{40\}\)$/\1/p' docs/reviews/P1-ENG-JET-001.md | tail -n 1)   # R1 通过候选
git diff --name-only "$PASSED".."$CAND"                                           # 补丁增量（含期间他人提交，如实列出）
git diff "$PASSED".."$CAND" -- tools/eng_jet tests                                # 代码/测试增量：6 个文件
git diff --stat "$PASSED".."$CAND" -- Assets controller config                    # 应为空
```

- 代码/测试增量：`tools/eng_jet/{relay,evidence,assets,ledger}.py`、`tests/test_eng_jet_{relay,guards}.py`；新增证据：`docs/evidence/P1-ENG-JET-001-a7-frame-sha256.jsonl.gz`、`-R1notes-focused-tests.log`；本文件与状态板。PLAY_GOVERNING diff 非空（`tools/`、`tests/`），按「R1消费」开轮裁定须：四项自证成立 → 接受只读核对 → 独立 `R2@K1K3K4`（R1 只覆盖原候选；本停点核对退回已用 1 次不重置）。
- 复核重点：`adopt_link` 原子性（同锁内替换连接与清空两表）与 `return_once` 抽取未改回程判据；`_link_event_split` 的 `None` 读法；纯参照派生与读取方拒绝规则；`disconnect_pass` 与原合成式逐项等价；ledger 常量标注未改数值。补丁代码**未上板运行**（板上 `~/eng-jet/code` 仍为补跑F 代码束），R1-1 重连行为只有进程内零模型验证；AC-14 `UNITY_NA` 的 R1 附议仅覆盖原候选，新候选须 R2 另行附议。

### 4. 精确缺额（needs_user；不签、不借任何额度）

新候选满足 workflow §4.3.1 第 2 项需要一次新的停点全套；原全套 1/1、det-assoc 2/2、部分回放 2/2、SR 5/5 已耗尽，不重跑。预计依据：自 `$START_CPU1` 至 HEAD，`tests/`、`controller/`、`tools/`、`config/`、`Assets/` 已提交 diff 为空，本轮工作树只改上表 6 个 eng_jet 文件（无真实加载器）；执行机、数据根解释器、数据根与主树 `runtime/`（仅 README）与 CPU1 跑前核对时相同，故沿用该核对的逐种读法：

| 维度（request_id `P1-ENG-JET-001:b0a5f79c:SUB:6`，申请值） | 预计 | 依据 |
|---|---|---|
| Mac mini 本机停点全套 | **1 次** | §4.3.1 第 2 项；与 SUB:2/SUB:5 同样「一次」，失败/重试计入 |
| det-assoc 冻结检测器加载/构造（本机 CPU） | **2**（`CarrierSelfTest` 两例显式 `device="cpu"`；数据根门成立） | CPU1 实测 2；SUB:5 A 形状 |
| NanoTrack 构造尝试 | **≤ 2**（真实权重读取 0：主树无 `runtime/models/nanotrack-v2/`） | CPU1 静态上界；SUB:2 曾给 ≤ 4 |
| CSRT 构造尝试 | **≤ 2**（实例 0：opencv 5.0.0 无 `TrackerCSRT_create`） | 同上；SUB:2 ≤ 2 |
| YOLOE / DINOv2 | **0 / 0**（主树无文件） | 同上；SUB:2 曾给各 ≤ 2 |
| 其他模型 | **0** | 本轮新增用例无真实加载器 |
| 具名零模型部分回放（`ResidentCarrierReplay`） | **2**（各 60 帧，归本项、不扣 ACQ-001） | SUB:5 A 形状 |
| Mac `outputs/eng-jet/` | 现 70,231,574 B；上次全套增量约 9.1 KB，预计 < 0.1 MB；上限 2 GB 不变 | `common.disk_usage_bytes` 读法 |
| 预计墙钟 | 全套约 4 min（上次 235.7 s）+ 跑前只读核对约 10 min，合计 ≤ 15 min | CPU1 记录 |
| 零 pip、零下载、零新增模型、零上板、零 SR | 0 | 不变 |

- **可预见结果**：代码/环境不变时，Carrier 首例 CPU 对 MPS 参考的逐帧比较失败与 scene006 29 条环境失败预计再现（相对 R7 新增 30）。原 AC-10 修订 8 / AC-13 修订 3 的用户具名例外**只覆盖原候选、不自动延长**；新候选若不由用户**重新具名这两项例外**，第 2 项仍不成立。
- 选项（推荐项只供选择，未执行）：**(a，推荐)** 签 SUB:6 上表额度 + 为新候选重新具名 Carrier/scene006 两项例外，跑一次全套后整理候选交接受核对 → R2；若用户近期会签线 B 阶段 B，建议把本全套并入阶段 B 合并候选只跑一次（supervisor 10-04 选项说明同此）。理由：合规路径、成本极低（约 15 min、2 次 CPU 检测器构造），又不把旧例外外推。(b) 用户明确具名测试例外：以本轮 focused 82/82 代替新候选全套（补丁增量只在 `tools/eng_jet/` 与 `tests/test_eng_jet_*`，focused 覆盖全部改动；代价是全套层面的回归未验证）。(c) 停止补丁候选，R1-1…4 交未来获批工作承接（与 A收口:1 合并决定）。

### 5. 停点自证（workflow §4.3.1 四项，K1K3K4R1注记修补 现状）

1. **实现范围与接口冻结 —— 成立（限 R1-1…4）。** 只改上表 6 个文件与新增两份证据；补丁范围按「R1消费」表，不改帧/控制协议、冻结规格/权重、`Assets/controller/config`；IR-26/27（下节）为实现读法披露，不改合同。
2. **相称测试 —— 不成立。** 新候选未跑停点全套（无额度）；focused 82/82 不替代全套；原用户例外不延长（§4）。
3. **已知 Unity 失败 —— 不适用。** 零 Play；`UNITY_NA` 须 R2 另行附议。
4. **复核范围、状态板、候选提交与未验证风险 —— 成立。** §3 给出解析规则与复核范围，§1/§4 披露未验证项；状态板交接行改为等用户签缺额。

**结论：第 2 项不成立 → 不交接受核对、不开 R2**；交用户裁定 §4 缺额（owner = 用户）。Gate 行 Overall `REVIEW_PASSED`、Lifecycle `ACTIVE` 不改（R1消费 已把本补丁指派为该状态下的下一实现提交；是否改 `IMPLEMENTING` 由接受角色随新候选核对处理）；不记 `DONE`。

### 6. 待裁定（实现读法，交接受角色；实现对提案只读）

- **IR-26（R1-3 派生数据文件）**：本角色把「纯 `frame_id/sha256` 参照」实现为新增派生证据文件 `docs/evidence/P1-ENG-JET-001-a7-frame-sha256.jsonl.gz`（a7 全部 3,168 帧，含未用于本项的 1,500…3,167 帧，以保持与原文件同一前缀闭集），并让 `verify_frames` 今后输出新增参照键；历史 `-assets.json` 不改写。请确认此读法（或指定只保留实际使用的 0…1,499 帧）。
- **IR-27（R1-2/R1-4 失败闭合读法）**：`_link_event_split` 在可能截断时把传输中计数记 `None`（而非从截断列表计数）；`disconnect_pass` 对缺 `disconnects` 键判假（原合成式会抛 `KeyError`）。两者只在补丁后新生成证据时生效，历史读数不变。请确认。

### 7. 未验证项与限制（本轮）

- 补丁代码未上板、未在真实断链/重连下运行；f4 回程读数仍是补丁前代码的历史实测。
- 新候选未跑全套；Carrier/scene006 失败预计再现但未实测；NanoTrack/CSRT 次数仍为静态上界。
- focused 运行时未设 `YOLO_OFFLINE`：`InjectionOnly` 导入 ultralytics 时的 DNS/匿名事件未监测（与此前各轮相同）。

## K1K3K4全套SUB6：新候选停点全套一次、计账与停点自证（2026-10-04，Mac mini 本机；Dispatch-Id `P1-ENG-JET-001-K1K3K4全套SUB6-20261004T015221Z-e7f4`）

依据：提案决策记录「SUB:6 落实与新候选两项例外（2026-10-04，CLARIFY）」的「下一 Implementation 派发」步骤 1–5（AC-10 修订 9/10、AC-13 修订 4）及「待裁定」IR-26/27 接受裁定；账本 2026-10-04「P1-ENG-JET-001 — 用户签发 SUB:6（新候选停点全套，方案 (a)）并为新候选重新具名 Carrier/scene006 两项例外（supervisor 会话代录）」授权范围 (1)–(3)，`request_id` `P1-ENG-JET-001:b0a5f79c:SUB:6`。本轮**未改**代码、测试、工具、配置、`Assets/`、冻结规格/权重、skip 门与环境变量；未上板/ssh、未 SR、未 pip/下载/安装、未 MPS 推理、未在全套外跑 focused 或探测；全套只跑 1 次（不重跑）。原全套日志 `docs/evidence/P1-ENG-JET-001-full-suite.log`、原收据与 `-ledger.json` 既有字段均未改写。

### 1. 跑前只读核对（步骤 1；结论：可跑）

逐维度按 AC-10 修订 9 重新核对（不沿用 CPU1 旧 prechecks）；原文为 `outputs/eng-jet/P1-ENG-JET-001/ledger-events.jsonl` 的 `note` 事件 `event = mac_full_suite_precheck_sub6`（全套启动前写入），已汇入 `-ledger.json`「dimensions.mac.sub6.items」。核对开始 2026-10-04T01:54:09Z，执行机 `zc5s-Mac-mini.local`。

| 维度 | 核对 | 预计（SUB:6 上限） |
|---|---|---|
| 测试树与加载器 | `git diff --stat "$START_CPU1" HEAD -- tests controller tools config Assets .gitignore` 只有 R1-1…4 的 6 个文件（`tools/eng_jet/{assets,evidence,ledger,relay}.py`、`tests/test_eng_jet_{guards,relay}.py`），新增行 grep（YOLO/torch/create_tracker/DetAssoc/cv2/onnx/subprocess）无真实加载器或子进程模型加载；其余 `DetAssocTracker(` 构造（`tests/test_det_assoc_tracker.py` 四处）均注入 `model_loader` | — |
| det-assoc（CPU） | `CarrierSelfTest` 两例 `DetAssocTracker(spec_path=SPEC, device="cpu")` 走真实默认加载器；门 `_ready` 成立：`outputs/eng-det/runs/run-1/weights/last.pt` 存在且 sha256 与 `config/det-assoc-v1.models.json` 冻结值一致、数据根帧存在 | 2（≤ 2） |
| 自动安装分支 | `last.pt` 内 `data.pkl` 的 GLOBAL/STACK_GLOBAL 模块（torch.*、`ultralytics.nn.{tasks,modules.block,modules.conv,modules.head}`、`collections`；`__builtin__` 为 pickle 兼容映射）在数据根解释器 `find_spec` 全部可定位，不触发 `torch_safe_load` 的自动安装（未反序列化） | pip/下载 0 |
| NanoTrack | 主树 `runtime/` 只有 `README.md`，无 `runtime/models/nanotrack-v2/` → pinned 例 skip、两条 CLI 子进程在读权重前失败 | 构造尝试 ≤ 2、读权重 0 |
| CSRT | 数据根解释器 `cv2 5.0.0`，无 `TrackerCSRT_create`、无 `cv2.legacy` | 构造尝试 ≤ 2、实例 0 |
| YOLOE / DINOv2 / 其他 | 主树无 `runtime/yoloe`、`runtime/models`；scene006 首检 YOLOE 权重哈希即拒绝 | 0 / 0 / 0 |
| 部分回放 | `ResidentCarrierReplay` 门 `_acq_ready` 成立（数据根 scout-1 帧目录存在），缓存检测替身零推理，测试文档记每次运行 2 次各 60 帧 | 2（≤ 2，归本项、不扣 ACQ-001） |
| 设备 | Carrier/Resident 显式 `cpu`；全套内无走 `_resolve_device` 的真实推理；本机 MPS 可用但不用 | MPS 推理 0 |
| 解释器与环境 | `~/TetheredDroneTracking-full/.venv-yoloe/bin/python` 3.12.14；torch 2.13.0；ultralytics 8.4.104；未设 `ENG_DET_DATA_ROOT`/`YOLO_OFFLINE`；会话环境原有 `PYTHONDONTWRITEBYTECODE=1`（非本轮设置，披露） | 不附加环境变量 |
| Mac outputs | 跑前 `outputs/eng-jet` 70,231,574 B（`common.disk_usage_bytes`）；主树 `outputs/` 全部 1,139,564,987 B | 增量 < 0.1 MB；总量 ≤ 2 GB |
| 墙钟 | 全套约 4 min + 核对约 1 min | ≤ 15 min |

核对用的只读命令中，`import ultralytics` 打印版本一次（只导入、不构造模型；导入时的 DNS 探测同既往披露，未监测）。

### 2. 一次全套（步骤 2；已执行，不重跑）

- 命令（仓库根，逐字，无 `-v`、无附加环境变量）：`~/TetheredDroneTracking-full/.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-JET-001-SUB6-full-suite.log 2>&1`
- 2026-10-04T01:55:20Z–01:59:14Z，后台运行并等待完成；退出码 1。执行时 HEAD = 本轮 supervisor 派发登记 `started` 提交（`git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4全套SUB6 supervisor 派发登记：started'` 运行时解析），工作树干净；该提交与新候选代码（`K1K3K4R1注记修补 收工`）之间 `tests tools controller Assets config .gitignore` 零 diff，只多文档提交（账本、状态板、派发登记、提案）。
- 摘要：**`Ran 2146 tests in 231.849s` / `FAILED (failures=27, errors=10, skipped=56)`**；日志 550 行。2146 = CPU1 的 2136 + R1 补丁新增 10 例；skip 56 与 CPU1 相同，新增 10 例无失败记录（与 skip 数不变合读为执行通过；无 `-v` 不逐名）。

### 3. 计账（步骤 3；唯一 `-ledger.json`）

记于 `docs/evidence/P1-ENG-JET-001-ledger.json`「envelope.sub6」（request_id、完整授权标题、生效值与范围）与「dimensions.mac.sub6」（实际累计、两条事件原文、`within`）。SUB:2/SUB:5 已用计数、`mac.models`、顶层 `within_envelope` 与其余字段**逐字未改**（追加 151 行、删除 0 行）；SUB:6 不并入顶层合计，不重复扣账。

| SUB:6 维度 | 已用 / 上限 | 读法 |
|---|---:|---|
| 新候选停点全套 | 1 / 1（耗尽） | 一次、未重跑 |
| det-assoc 冻结检测器 CPU 加载 | 2 / 2（耗尽） | 两例均构造成功（首例失败点在构造之后的逐帧比较，次例无失败） |
| NanoTrack 构造尝试 / 读权重 | 2（静态上界）/ 0 | 未插桩 |
| CSRT 构造尝试 / 实例 | 2（静态上界）/ 0 | 两入口均以无 `TrackerCSRT_create` 失败 |
| YOLOE / DINOv2 / 其他模型 | 0 / 0 / 0 | — |
| 零模型部分回放（各 60 帧） | 2 / 2（耗尽，保守读数） | 门成立、无失败记录；未插桩 |
| Mac outputs | `outputs/eng-jet` 70,231,574 → 70,235,427 B（+3,853 B，全部是本轮两条 SUB:6 记账事件行；全套本身对主树 `outputs/` 增量 0 B）；主树 `outputs/` 1,139,567,380 B ≤ 2 GB | 增量 < 0.1 MB |
| 墙钟 | 核对开始 01:54:09Z → 全套结束 01:59:14Z 305 s；→ 记账事件 01:59:58Z 349 s | ≤ 900 s |
| pip / 下载 / 上板 / SR / MPS 推理 | 0 | — |

**限制**：`tools/eng_jet/ledger.py` 无 SUB:6 维度（本轮禁止改代码），SUB:6 两条事件用既有 `note` 类型记入事件文件、`-ledger.json` 的 SUB:6 块为本轮手工追加且未运行 `ledger build`；日后若重跑 `ledger build` 会丢弃该块，须先补代码支持。`dimensions.mac.sub6.within = true` 只是记账数量与上限的比较，不是设备、外联或系统设置的动态测量。

### 4. 失败分列与两项例外边界（步骤 4）

本轮 FAIL/ERROR 37 名（按日志 `FAIL:`/`ERROR:` 行全文作名，含子测试），与 R7 基线（`docs/evidence/P1-ENG-FRAME-001-R7-full-suite-result.json`「current_failure_names」25 名）及 CPU1 原日志做集合比较：

| 分类 | 数 | 名称与原因 |
|---|---:|---|
| R7 基线已有、本轮仍在 | 7 | `test_eng_sft_{audit,build,cloud,evaluate}`（`No module named 'tests.fixtures'`）、`test_language_k_binding`（`No module named 'tests.test_language_selector'`）五个导入错误；CSRT 两入口 `test_trackers…test_pinned_opencv_csrt_initializes_and_updates`（ERROR）与 `test_track_loop…test_cli_runs_pinned_csrt_to_a_versioned_summary`（FAIL），opencv 5.0.0 无 `TrackerCSRT_create` |
| R7 有、本轮未出现 | 18 | 同 CPU1：12 条 R7 沙箱 loopback 绑定拒绝 + 6 条有缺归档静态 skip 门；无逐名 skip 记录，**不称修复/通过** |
| 相对 R7 新增 | 30 | Carrier 1 + scene006 29（下两行） |
| ├ Carrier（AC-10 修订 10 具名例外） | 1 | `test_det_assoc_carrier.CarrierSelfTest.test_carrier_matches_caliber_b_from_first_update` **FAIL**，`AssertionError: Lists differ: [2, 4, 5, 6, 8, 12, 17, 18, 19, 20] != []`（同一断言行 141）。**与原记录同名同类**：失败类型、位置与不一致索引集合逐项相同；索引 2 = `frame_id=3` 的首个宽差只说明该条，其余 9 条形态未知，比较后 confidence_source/观测桥字段集/临时目录外写入断言**未执行**；两例不经真实工厂的覆盖损失保留。不记通过 |
| └ scene006（AC-13 修订 4 具名例外） | 29 | `tests/test_scene006_probe.py` 25 FAIL + 4 ERROR，类分布 Probe 10 / CandidateManifest 1 / CandidateManifestP2 7 / AppearanceTolerance 10 / StrictJson 1；**与原记录逐名、逐 FAIL/ERROR 类型相同**，失败细节文本相同。仍按本机缺 re-anchor/NanoTrack 权重的静态归因（首项 YOLOE 权重哈希绑定拒绝、后续行为未验证），保留为相对 R7 新增，不改作旧失败或通过；未向主树 `runtime/` 补资产 |
| 相对 CPU1 变化 | 0 | 新增名 0、消失名 0、类型变化 0；两份日志的 `======` 至 `Ran` 失败详情段除 `Ran` 行（2136→2146、耗时）外逐字相同；全文差异仅 `Ran` 行与三行进度/ResourceWarning 临时路径 |
| 例外以外的新增失败 | **0** | — |

skip 56（R7 19）聚合限制照旧：无 `-v` 不能逐名对照；未出现 18 条不能区分通过与跳过；`ResidentCarrierReplay` 实际执行/跳过未插桩（门成立且无失败，保守计 2 次回放）。

### 5. AC 逐条指针（K1K3K4全套SUB6；新候选）

| AC | 本停点状态（不预签核对/R2） | 指针 |
|---|---|---|
| AC-1 | 同上节「K1K3K4证据整理1A」§5，读数不变 | artifact: `docs/evidence/P1-ENG-JET-001-env.json`；test: `tests/test_eng_jet_bench.py::S0Verdict`、`tests/test_eng_jet_guards.py::NoSystemSettingChanges` |
| AC-2 / AC-3 | S1 `STOP(FP16_BOX_DIVERGENCE)`、S2 `STOP(FRAME_DROP)` 与 (α)/(α′) 续跑标记原样；不记满足 | artifact: `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1」「S2」、报告 §2d/§2e |
| AC-4（修订 3，IR-27） | 历史 forward 读数不变；补丁后 `_link_event_split` 读全量、可能截断时 `in_transfer_event_count = None`（只对新生成证据生效） | artifact: `docs/evidence/P1-ENG-JET-001-relay.json`「forward」「contract_readings_full_suite.ac4_rev2」；test: `tests/test_eng_jet_relay.py::AnalyzeLinkEventsFull`、`tests/test_eng_jet_guards.py::ContractSyncFullSuite::test_link_event_split_reads_full_list_and_refuses_truncated` |
| AC-5 | 读数不变 | artifact: 同上「return」「contract_readings_full_suite.ac5_rev1」；test: `tests/test_eng_jet_track_responder.py`（`SelectInitBox`、`ResponderInProcess`） |
| AC-6（修订 2，IR-27） | f4 断链读数为补丁前历史实测；R1-1 `adopt_link` 清回程去重只经进程内零模型验证、未上板；`disconnect_pass` 缺键判假 | artifact: 同上「disconnect」；test: `tests/test_eng_jet_relay.py::BoardRelayInProcess::test_reconnect_resends_current_return_version`、`tests/test_eng_jet_guards.py::DisconnectPass` |
| AC-7 / AC-8 / AC-9 | `NOT_RUN(阶段 B 信封未签)`，不声称满足 | artifact: `docs/evidence/P1-ENG-JET-001-{vlm,quant-equivalence,coresidency}.json` |
| AC-10（修订 9/10） | SUB:6 全套 1/1、det-assoc 2/2、回放 2/2、NanoTrack 2 上界/读权重 0、CSRT 2 上界/实例 0、其余 0、outputs +3,853 B、墙钟 349 s、`dimensions.mac.sub6.within = true`（数量比较）；Carrier 具名例外边界见 §4 | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`「envelope.sub6」「dimensions.mac.sub6」；cmd: §2 命令；test: `tests/test_eng_jet_guards.py`（`LedgerSub2`、`LedgerSub5`）、`tests/test_det_assoc_carrier.py::CarrierSelfTest` |
| AC-11（修订 1，IR-26） | 纯 `frame_id/sha256` 参照（a7 全部 3,168 帧）只作今后参照，历史 `-assets.json` 不改写 | artifact: `docs/evidence/P1-ENG-JET-001-a7-frame-sha256.jsonl.gz`、`docs/evidence/P1-ENG-JET-001-assets.json`；test: `tests/test_eng_jet_guards.py::PureFrameReference` |
| AC-12 | 分列读法不变 | artifact: `docs/evidence/P1-ENG-JET-001-assets.json`「board_manifest.ac12_split」「protected_roots_zero_write」；test: `tests/test_eng_jet_guards.py`（`ContractSyncFullSuite::test_ir22_split_is_named_only`、`ProtectedWrites`） |
| AC-13（修订 4） | 报告已同步本轮读数与现状/历史分列；scene006 环境分列 | artifact: `docs/evidence/P1-ENG-JET-001-report.md` §2i、§6 |
| AC-14 | 本轮执行机/时间/版本见 §1–§2；`UNITY_NA` 的 R1 附议只覆盖原候选，**新候选须 R2 另行附议** | artifact: 本节；`docs/reviews/P1-ENG-JET-001.md`（复核角色写） |
| AC-15 | (h)(n) answered、(i)–(m) unanswered 且零执行，不变 | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`「pending_user」 |
| AC-16 | 本轮零上板，记录不变 | artifact: `docs/evidence/P1-ENG-JET-001-env.json`「s2_system_stack_e.env.ac16」「sr_system_stack_f.ac16」 |
| §4.3.1 第 2 项 | 全套 1 次：2146 / F27 / E10 / S56；新增 30 = Carrier 1 + scene006 29，全部在两项具名例外的同名同类边界内；例外外新增 0 | artifact: `docs/evidence/P1-ENG-JET-001-SUB6-full-suite.log`、`docs/evidence/P1-ENG-JET-001-R1notes-focused-tests.log` |

### 6. 候选解析与完整范围（不手抄 SHA）

```bash
BASE=$(git rev-parse "$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4 开工')^")          # 不变
CAND=$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4全套SUB6 收工')                     # 新候选 = 本轮收工提交：须仅一条、触及本文件、已推送且为 origin/main 祖先
PASSED=$(sed -n 's/^passed_candidate: \([0-9a-f]\{40\}\)$/\1/p' docs/reviews/P1-ENG-JET-001.md | tail -n 1)   # R1 通过候选
CODE=$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4R1注记修补 收工')                  # 新候选代码版本
git diff --stat "$CODE" "$CAND" -- tests tools controller Assets config .gitignore                # 应为空（本轮无代码改动）
git diff --name-only "$PASSED".."$CAND"                                                          # R2 增量范围（如实列出，含期间他人文档提交）
git diff "$PASSED".."$CAND" -- tools/eng_jet tests                                               # 代码/测试增量：6 个文件
git diff --name-only "$BASE".."$CAND"                                                            # 完整候选路径
git diff --stat "$BASE".."$CAND" -- Assets controller config                                     # 应为空
```

完整候选 = 「K1K3K4证据整理1A」§3 的 33 路径 + R1 补丁新增证据 `docs/evidence/P1-ENG-JET-001-a7-frame-sha256.jsonl.gz`、`-R1notes-focused-tests.log` + 本轮 `-SUB6-full-suite.log`（实际以运行时 `git diff --name-only "$BASE".."$CAND"` 为准）。本轮只新增全套日志并改 `-ledger.json`（追加）、报告、本文件与状态板。

### 7. 停点自证（workflow §4.3.1 四项，K1K3K4全套SUB6 重判）

1. **实现范围与接口冻结 —— 成立。** 新候选代码 = R1-1…4 补丁（`K1K3K4R1注记修补 收工`），至本轮收工 tests/tools/controller/Assets/config/.gitignore 零 diff；IR-26/27 已由接受裁定（AC-11 修订 1、AC-4 修订 3、AC-6 修订 2），无未答实现读法；阶段 B 若日后加代码属另一候选。
2. **相称测试 —— 在用户具名例外下成立（不记通过）。** 新候选停点全套跑 1 次（2146 / F27 / E10 / S56）；R7 已有 7、相对 R7 新增 30 已分列；新增 30 全部落在 AC-10 修订 10（Carrier 1）与 AC-13 修订 4（scene006 29）的同名同类边界内，相对 CPU1 无任何变化，例外以外新增 0；R1 补丁 10 例在全套中无失败。两项失败**不记通过**，未知/未执行断言、skip 聚合与未验证项照旧携带，复核可判阻断。
3. **已知 Unity 失败 —— 不适用。** 零 Play、Unity 零改动；AC-14 `UNITY_NA` 须 R2 对新候选另行附议。
4. **复核范围、状态板、候选提交与未验证风险 —— 成立。** §6 给出候选解析与 R2 增量范围，§8 列未验证风险；状态板交接行改为交接受只读核对；复核文件由复核角色写（实现不写）。

**结论：四项成立 → 交接受只读核对（之后独立 `R2@K1K3K4`）。** 本停点核对退回已用 1 次，不重置；Overall `REVIEW_PASSED`、Lifecycle `ACTIVE` 不改；不记 `DONE`。SUB:6 全套、det-assoc、回放额度均已耗尽；核对或复核若需任何真实模型/回放/全套重跑，须另申请。

### 8. 未验证项与限制（本轮）

- Carrier 其余 9 个差异条目形态未知、比较后三类断言未执行、两例不经工厂；CPU 对 MPS 参考差异成因未验证。
- scene006 归因为读码所得，未在补齐 re-anchor/NanoTrack 权重的环境验证。
- NanoTrack/CSRT 尝试数为静态上界；`ResidentCarrierReplay` 执行/跳过未插桩；未出现 18 条与 skip 56 无逐名记录。
- 未设 `YOLO_OFFLINE`：ultralytics 导入时 DNS 探测与可能的匿名 usage 事件未监测，日志无下载/安装行不证明外联为 0。
- SUB:6 块为手工追加，`ledger.py` 无对应维度（§3 限制）。
- R1 补丁未上板、未在真实断链/重连下运行；f4 为补丁前历史实测；S1/S2 `STOP`、SR 5/5 用尽、AC-7/8/9 未运行、R1-5/6 两条 OPEN 债照旧。

## K1K3K4R2返工：R2-1 窄修、红绿与全套义务缺额（2026-10-04，Mac mini，零模型；Dispatch-Id `P1-ENG-JET-001-K1K3K4R2返工-20261004T022842Z-54f6`）

依据：复核 `docs/reviews/P1-ENG-JET-001.md`「R2@K1K3K4」§3 R2-1（CLASS_2，`BC-6`）闭合要求与 §6 needs_user；engineering-workflow §5（复核返工直回复核，不经核对轮）。本轮**零消耗**：未跑全套、未加载/构造任何真实模型、未推理、未回放、未上板/ssh、未下载安装、未跑 SR、未设或改 skip/环境变量；`Assets/`、`controller/`、`config/`、冻结规格/权重、帧与控制协议、`-ledger.json` 及全部历史证据零改动；`outputs/eng-jet/` 仍为 70,235,427 B（`common.disk_usage_bytes`，与 SUB:6 计账后相同）。

### 1. 修改位置（只 2 个文件）

| 文件 | 修改 |
|---|---|
| `tools/eng_jet/relay.py::BoardRelay.return_once` | 采用复核闭合要求 (a)：`link.send` 返回后，在 `_link_lock` 内判断 `self.link is link`；仍是本轮快照的连接才写 `_last_return[name] = digest`。已被替换时不写回（旧轮次 digest 不落进新连接去重状态），该次发送已 `sendall` 入旧连接，照常计入 `returns_sent` 与 `send_return` 收据，并在收据上加 `link_replaced: true`，随即结束本轮（下一轮按新连接与已清空的去重状态发当前版本）。未替换时行为、收据字段与补丁前逐字相同。docstring 写明 R2-1。 |
| `tools/eng_jet/relay.py::BoardRelay.adopt_link` | 只改 docstring：注明与 `return_once` 写回同锁、清空不会被旧轮次写回覆盖（代码不变：锁内关旧连接、换 `self.link`、`members.clear()`、`_last_return.clear()`）。 |
| `tests/test_eng_jet_relay.py::BoardRelayInProcess::test_adopt_during_return_send_keeps_new_link_dedup_clean` | 新增绑定 R2-1 的回归：真实 `BoardRelay` 运行目录 + `write_bytes` 写回程文件（同既有用例口径）；连接替身 `AdoptOnSendLink` 在 `send` 返回前调用 `board.adopt_link(new)`，确定化「send 返回 → 换连接清表 → 写回」交错。断言：第一轮旧连接发 1；旧连接已关、`board.link is new`；`_last_return` 不含旧连接写回；第二轮新连接一轮内收到当前版本（路径与字节）且写入新 digest；第三轮 0；收据两条 `send_return` 的 `link_replaced` 依次为 `True`/`False`。 |

`analyze` 只按 `ev == "send_return"` 计数，新加的可选键不改任何分析读数；历史收据无此键。

### 2. 红绿与 focused（零模型、进程内）

- **修前红**（先加测试、未改 `relay.py` 时，一次）：`.venv-yoloe/bin/python -m unittest discover -s tests -p 'test_eng_jet_relay.py' -k test_adopt_during_return_send` → `FAILED (failures=1)`，`AssertionError: 'tracking_observation.json' unexpectedly found in {'tracking_observation.json': '5275e4bc…'}`（即旧连接 digest 覆盖了 `adopt_link` 的清空，与复核探针一致）。输出在会话暂存目录，不入仓。
- **修后绿**：同命令 → `Ran 1 test` / `OK`。
- **focused**（仓库根，`.venv-yoloe`，Python 3.12.14，未加 `-v`、未附加环境变量）：`.venv-yoloe/bin/python -m unittest discover -s tests -p 'test_eng_jet_*.py' > docs/evidence/P1-ENG-JET-001-R2rework-focused-tests.log 2>&1` → **`Ran 83 tests` / `OK`**（原 82 + 本轮 1，无 skip；R1-1 顺序回归 `test_reconnect_resends_current_return_version` 仍绿）。零模型口径同「K1K3K4R1注记修补」§2（`InjectionOnly` 只读权重文件算 sha、不构造模型）。

### 3. 新候选解析与 R3 复核增量范围（不手抄 SHA）

```bash
BASE=$(git rev-parse "$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4 开工')^")          # 不变
CAND=$(git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4R2返工 收工')                       # 新候选 = 本轮收工提交：须仅一条、触及本文件、已推送且为 origin/main 祖先
PREV=$(sed -n 's/^.*round_candidate: \([0-9a-f]\{40\}\).*$/\1/p' docs/reviews/P1-ENG-JET-001.md | tail -n 1)   # R2 轮候选（修复触及行基线）
PASSED=$(sed -n 's/^passed_candidate: \([0-9a-f]\{40\}\)$/\1/p' docs/reviews/P1-ENG-JET-001.md | tail -n 1)       # 上一通过候选（R1）
git diff "$PREV".."$CAND" -- tools tests controller Assets config                                 # 修复触及行：仅 relay.py 与 test_eng_jet_relay.py
git diff --name-only "$PREV".."$CAND"                                                             # R3 增量路径（含期间他人文档/派发登记提交，如实列出）
git diff --stat "$BASE".."$CAND" -- Assets controller config                                      # 应为空
```

- R3 增量 = 上述两文件代码/测试 diff + 本节 + `-R2rework-focused-tests.log` + 状态板 + 期间 supervisor 派发登记与复核文件提交；全量范围沿「K1K3K4全套SUB6」§6（以运行时 `git diff --name-only "$BASE".."$CAND"` 为准）。
- 复核重点：写回判定与 `adopt_link` 同锁、`self.link is link` 判据；替换时计数/收据口径（计入 + `link_replaced`，随即 `break`）；读去重表仍在锁外（快照后若已换连接，`send` 因 `alive=False` 抛错 → break，不写回）；新回归在修前必红。PLAY_GOVERNING（`tools/`、`tests/`）diff 非空，按 workflow §4.4 开轮资格开 `R3@K1K3K4`；不触及 Play 治理门。

### 4. workflow §4.3.1 四项现状（K1K3K4R2返工）

1. **实现范围与接口冻结 —— 成立。** 只改 `return_once` 写回判定与 docstring + 1 条回归；帧/控制协议、回程判据（只发当前版本、按内容去重）、`analyze` 读数不变；无新实现读法待裁定。
2. **相称测试 —— 待用户决定（现不成立）。** focused 83/83 与 R2-1 修前红/修后绿已完成；新候选停点全套无额度（SUB:6 全套 1/1、det-assoc 2/2、回放 2/2、SR 5/5 均耗尽），SUB:6 两项具名例外只覆盖「K1K3K4R1注记修补 起」的候选、本角色不推定其延长到本候选。选项见 §5。
3. **已知 Unity 失败 —— 不适用。** 零 Play、Unity 零改动；R2 §4 已附议新候选范围 `UNITY_NA`，本修复仍在 `tools/eng_jet/`、`tests/` 内，R3 可沿用或另议。
4. **复核范围、状态板、候选提交与未验证风险 —— 成立。** §3 解析规则与增量范围、§6 未验证项；状态板交接行 owner = 用户。

**结论：第 2 项待用户决定。** 用户选定后经接受角色落实，再交复核 `R3@K1K3K4`（复核返工不经核对轮）。Overall `REVIEW_PASSED`、Lifecycle `ACTIVE` 不改；不记 `DONE`。本停点 `REWORK_REQUIRED` 已计 1/2。

### 5. 第 2 项缺额（needs_user；不预签、不借任何额度）

- **(a，推荐)** 用户具名：本窄修候选（`K1K3K4R2返工 收工`）以 focused 83/83 + R2-1 修前红/修后绿代替停点全套，SUB:6 授权范围 (2) 的 Carrier/scene006 两项例外读法沿用到本候选（仍不记通过、复核可判阻断）。缺额 = 0 额度，只缺用户对「代替全套」与「例外沿用」的逐字具名（账本一条）。理由：改动只在 `BoardRelay.return_once` 写回判定（无任何真实加载器，全套里的 Carrier/scene006 路径与本改动无交集），focused 覆盖全部改动；与 R2 §6 推荐同形。代价：全套层面回归本候选未实测。
- **(b)** 另签一次全套，`request_id` `P1-ENG-JET-001:b0a5f79c:SUB:7`，按 SUB:6 同形申请值：Mac mini 本机、本候选停点全套 **1 次**；det-assoc 冻结检测器 CPU 加载 **≤ 2**；NanoTrack 构造尝试 **≤ 2**（读权重 0）；CSRT 构造尝试 **≤ 2**（实例 0）；YOLOE/DINOv2/其他模型 **0**；零模型部分回放（`ResidentCarrierReplay`）**≤ 2**（各 60 帧，计入本项、不扣 ACQ-001）；Mac `outputs/eng-jet/` 增量 **< 0.1 MB**（现 70,235,427 B；SUB:6 实测 +3,853 B）且总量 ≤ 2 GB；墙钟 **≤ 15 min**（SUB:6 实测 349 s）；pip/下载/上板/SR **0**；成功、失败、重试全部计入，耗尽即停回用户。并须同时为本候选重新具名两项例外（范围同 SUB:6 授权范围 (2)），否则 Carrier/scene006 预计再现（相对 R7 新增 30）时第 2 项仍不成立。理由：合规全形，成本约 15 min；若线 B 阶段 B 近期签发，可并入阶段 B 合并候选只跑一次。
- (c) 不选 (a)/(b)：本候选停在 R3 之前，与 A收口:1 一并决定。

### 6. 未验证项与限制（本轮）

- 修复未上板、未在真实断链/重连下运行；交错只由进程内连接替身确定化验证，真实线程调度下的窗口未实测；f4 仍是补丁前历史实测。
- 读去重表（`_last_return.get`）仍在锁外：已推演为安全（换连接后旧轮次的发送必因旧连接关闭而失败），未另写交错用例覆盖该分支。
- 替换时的那次发送是否到达桌面不可知（与补丁前「`send_return` 表示已 `sendall`」口径相同，R2 §5 已注）。
- 新候选未跑全套；Carrier/scene006、NanoTrack/CSRT 上界、skip 聚合、`YOLO_OFFLINE` 未设、SUB:6 块手工追加等「K1K3K4全套SUB6」§8 限制照旧携带；S1/S2 `STOP`、AC-7/8/9 `NOT_RUN`、R1-5/6 OPEN 债不变。
