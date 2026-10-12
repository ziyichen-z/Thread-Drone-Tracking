# P1-ENG-JET-001 — Jetson Orin Nano 8GB（Super、headless）板端可行性探测：环境核验 + 快层 TRT FP16 单测/热稳态 + VLM 单测（llama.cpp → TRT Edge-LLM）+ 609 行量化等价 + 共驻实测 + 桌面机 ↔ Jetson 中继测试

Status: ACCEPTED（D2，2026-09-28；`Workflow: engineering-v1` 已由接受角色裁定生效；阶段 A 已签；阶段 B 预检/元数据/METADATA/源码核验已收束、GGUF用户精确字节已落实；B-SIGN-DOWNLOAD一次批次已执行并核清，轮子31件已取回；原批GGUF按合同停对象，归因见「阶段B下载核清」；用户自下2件已只读核清，见「阶段B用户GGUF核清」，TX-ASSETS一次批次34/34已传板并核清，见「阶段B传板授权落实」「阶段B传板核清」；其余未签维度0、不含云，原阶段 A 合同/负结果保留；BUILD-LLAMA 已签（构建 1 次、重试 0、≤2 h、板新增 ≤5 GB）；两批已执行并核清、构建1/1用尽；原停止/修订29保持，见「阶段B构建核清」；其余未签维度0、不含云，原阶段 A 合同/负结果保留）
Workflow: engineering-v1
Author/role: 构思角色 / design ideation（supervisor 无人值守派发的 Fable 子代理；D1 Dispatch-Id `P1-ENG-JET-001-D1-20260928T204201Z-5bf2`；D2 Dispatch-Id `P1-ENG-JET-001-D2-20260928T212546Z-fa00`）
Created: 2026-09-28
Last updated: 2026-10-06

现行诊断追加：2026-10-06「阶段B基座提示调试资源核清」已核资源账；C2合同见「阶段BC2本机量化诊断授权落实」「阶段BC2工具缺项落实」，执行账/配对身份与停止边界偏差已核，见「阶段BC2诊断核清」；结果仅诊断，B-C2-RESULT已答落实；JSON诊断核清见「阶段BC2JSON诊断核清」，C2JSON-DRIVER_SELF_CHECK_STOP已答结束并落实，剩余义务与方向推荐见「阶段BC2JSON诊断答复落实」，不改正式门，云端已答结束、不租云。

现行阶段 B 合同：决策记录「阶段B答复落实」「阶段B准备审核」「阶段B补写核清」及追加「阶段B预检答复落实」。§5选择类已按推荐落实；一次board预检已执行1/1、原读数核清见§8.2，用户cmake反馈及一次元数据批次合同见「阶段B元数据授权落实」；META-BATCH-1累计61/86、31/40项目已核，条件拟pin/未闭事实及余额作废见「阶段B元数据核清」；META-VERIFY/SRC-ARCHIVE已执行并核清，31件固定轮子METADATA静态闭集与归档事实见「阶段B核验核清」；GGUF用户精确字节事实见「阶段BGGUF事实落实」，已重算文件输入推荐，未核执行维度0；TX-ASSETS一次传板合同见「阶段B传板授权落实」，34/34已传板并核清见「阶段B传板核清」；BUILD-LLAMA 板上离线构建执行合同见「阶段B构建授权落实」（已用1/1、两批核清见「阶段B构建核清」；首批停止/新批差异见「阶段B构建前置停止核清」）。本次终点不含云；**现行事实/额度待决唯一入口为「阶段B预检答复落实」§5**，旧清单保留作来源，不重问已答选择。BP-1…5静态材料义务已核清，U1必需cmake已按用户反馈核清（不证构建成功），U2包/头文件静态事实已核、W不需源码构建；其余未知按§8.2保留，不称完整可执行闭集。

> **来历**：用户 2026-09-28 裁定部署拓扑（`docs/authorizations.md` 同日「全局 — 用户裁定：VLM 与快层部署到 Jetson Orin Nano、Unity 留桌面机、板子 headless 运行」，下称「账本 09-28 拓扑」）并按推荐入账新工作项（同日「全局 — 用户按推荐入账：主线目标锚定…」D.8，下称「账本 09-28」）：本项 = Jetson 探测（A3 实测协议第 0–5 步 + 桌面机 ↔ Jetson 中继测试；设备与额度另签）。决策信封见同日「P1-ENG-JET-001 — 用户签发 supervisor 决策信封…」（D1/D4/D5/D6，至 2026-10-10）。
> **方案输入**（不是合同、不是证据；AC-n 以本提案为准）：`docs/evidence/fast-layer-research-2026-09-28/A3-jetson-feasibility.md`（§0、§4、§6、§7）及同目录 `fast-layer-plan-2026-09-28.md` §2.4/§2.5、`A1-repo-facts.md`「层 3」、`A2-external-survey.md`。A3 引用的公开数字（[厂商标称]/[公开实测]/[估计]）本提案一律只作预算依据，**不作为任何 Jetson 主张**；仓库事实由 D1 会话在 HEAD `c168b46` 只读复核（§0），D2 补充的 smoke/评估集/a7 数字由 D2 会话在数据根只读复核（§0 事实 9、§8）。
> **立项依据**：设计 `docs/phase1-single-drone-design.md` §8（Jetson 探测须独立立项、写明设备与额度；桌面量化不能替代板端实测）、`docs/engineering-workflow.md` §9、AGENTS.md「工作流轨道路由」末段（新增设备/额度/消耗类别不由既有信封覆盖）。`P1-M7-DEPLOY-001` 不激活。
> **与 `P1-ENG-ACQ-001` 的关系**：只有接口依赖（§3.5），零范围重叠；本项不做指针、解析器、状态机或伺服。
> **D2 修订依据**：接受角色「D1 接受裁定（2026-09-28）」对 §7 (a)–(g) 的结论已作为修订依据写入正文（§7「接受侧已裁定的设计取向」），AR1-1…3 的落实位置见「决策记录」D2 行；该裁定节原文未改。

## 0. 现状与只读事实（只读核实；符号名以 HEAD `c168b46` 为准；零模型运行、零上板、零下载、零写入 `runtime/` 与数据根）

| # | 事实 | 来源 |
|---|---|---|
| 1 | 目标板：用户的 Jetson Orin Nano 8GB Developer Kit（Super），JetPack 7.2 / L4T R39.2 / CUDA 13.2 / TensorRT 10.16；VLM 与快层（含 Python 控制器）上板，Unity、`CoverageEvaluator` 与 `metrics.json` 留桌面机，Unity 侧文件桥零改动，板子 headless；该条**不签发任何执行额度** | 账本 09-28 拓扑 1–3 与「信封」段 |
| 2 | 仓库内没有任何 Jetson / TensorRT 实测；Jetson 工作被正式放在未激活的 `P1-M7-DEPLOY-001`；COORD-010 已批准小规模探测前移，但须独立立项、设备与额度为零直至另签 | `docs/phase1-single-drone-design.md` §8；`docs/implementation-status.md`（M0 与 YOLOE 条目）；`docs/parked-status.md`「常设指针」 |
| 3 | 快层插件 `det-assoc-v1`：`DetAssocTracker.__init__` 接受注入 `model_loader`、`tracker_factory`、`device`（给定 `device` 时跳过 `_resolve_device`）；`_validate_spec` 把 `device_policy.preferred` 锁在 `{mps, cpu}`、`fallback` 锁 `cpu`；推理调用 `self._model.predict(source, imgsz, conf, iou, device, verbose=False)`；冻结规格 BoT-SORT `gmc_method sparseOptFlow`、`track_buffer 30`、`match_thresh 0.7`、`conf 0.25`、`imgsz 640`、ultralytics 8.4.104；权重 `outputs/eng-det/runs/run-1/weights/last.pt` sha256 `d6a0d6a9…059c9`、5,458,330 B；`docs/evidence/P1-ENG-FAST-002-freeze.json` sha256 `f231e450…c93c` | `controller/det_assoc_tracker.py`（`__init__`、`_validate_spec`、`_resolve_device`、`_step`）；`config/det-assoc-v1.models.json` |
| 4 | 快层桌面基线（G-7 口径，a7 前 320 帧、同一 init 框、单进程离线）：CPU p50 43.7 / p95 48.4 ms，MPS p50 19.8 / p95 31.9 ms，门 200 ms；`cpu_vs_mps` 限值 1e-3、前 50 帧检测数不一致 0、框最大差 2e-7；注明「不推断 Play 机或 Jetson」 | `docs/evidence/P1-ENG-FAST-002-latency.json` |
| 5 | 冻结检测缓存 `outputs/eng-det/dets/frozen-V.jsonl.gz`（130,702 B）：a7 3,168 帧，头部 `device mps`、`conf 0.25`、`imgsz 640`、`weights_sha256` 与事实 3 一致；主树 `.gitignore` 排除 `outputs/eng-det/` | 本机只读解析 |
| 6 | a7 帧在数据根 `~/TetheredDroneTracking-full/runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/`：3,168 帧（6,337 个文件，152 MB）；前 320 帧 JPEG 合计 11.8 MB；主树 `runtime/` 无该序列；帧 `frame_0000000000/100/200.jpg` 各 31,993 / 31,601 / 33,925 B，三帧均**不在** smoke 25 帧集合内（smoke 的 a7 帧索引为 57, 260, 530, 1137, 1528, 1801, 2302, 2339） | 本机 `ls`/`du`/只读求和（D2 补充三帧） |
| 7 | VLM：base `Qwen/Qwen3-VL-2B-Instruct` revision `89644892e4d85e24eaac8bacfd4f463576704203`（`BASE_REVISION`）；选中 C2 = LoRA r16 未合并 adapter，`adapter_bytes 69,788,264`、sha256 `4044dd4f…2d37`，只在本机/数据根 `outputs/eng-sft/`；609 行评估集 `data/eval.jsonl` sha256 `5d86013f…3dbb`、盲文件 `eval.blind.jsonl` sha256 `876c9dbe…dca8`、绑定帧包 448 张 19,757,920 B（manifest `frames.binding`）；609 行按 `frame_sha256` 去重为 **392 张互异帧**（D2 只读核实）；C2 bf16 逐行预测 `returned/sft-20260918T223245Z-bd1f5ebb/predictions/eval-adapter.jsonl`；表 G：解析失败 0、G1∪G2 77.6%、G3 报告 39.6% / 严格 25.0%、G1∪G2 误报 none 11.6%、G5 none 79.0%（硬给框 21 行）、`GATE_NOT_MET` | `tools/eng_sft/train_lora.py`；`docs/evidence/P1-ENG-SFT-002-train-summary.json`；`-eval-manifest.json`；`docs/reviews/P1-ENG-SFT-002-stage-summary.md` §4；数据根 `data/eval.jsonl` 只读解析 |
| 8 | 评分器 `tools/eng_sft/evaluate.py`（`--manifest/--predictions/--baseline/--out/--verdict`）与严格解析器 `tools/eng_sft/parse.py`、prompt v2（`prompt_v2.py`）现成；训练/推理网格固定 `[1,30,40]`（640×480 → 300 图像 token） | `tools/eng_sft/`；`docs/reviews/P1-ENG-SFT-002.md`（R1@K3） |
| 9 | 闭环 VLM 宿主实测（32 行 smoke、3 预热不计入 p50/p95）：5060 HTTP p50 4.178 / p95 5.429 / max 7.194 s；Mac MPS p50 4.404 / p95 8.756 s。**smoke 组成（D2 只读核实，AR1-1）**：`outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl` 32 行，`frame_id` 去重 25 张；按行序，每个 `frame_id` 的首次出现共 25 行（下称**首见行**），第二次出现共 7 行（行索引 0 起：8, 9, 10, 12, 18, 20, 22，下称**重复行**；每个重复帧恰出现 2 次，第二次换 surface，如 `the car`→`the red car`、`the truck`→`the gray truck`）；split dev 23 / train 9；state unique 16 / ambiguous 8 / none 8；family a7 9 / a1 9 / a2 9 / rate 4 / m3-armA 1；25 帧经数据根 `frame_id` 路径全部存在、sha256 与行内 `frame_sha256` 全部一致、合计 1,255,506 B；25 帧与 609 行评估集的 392 张互异帧**交集为 0** | `docs/evidence/P1-ENG-LOOP-001-measurement-report.md`；数据根只读解析 |
| 10 | VLM 薄 HTTP 服务 `tools/language_serve.py`：单工提交/轮询（`POST /query` multipart JPEG + `surface` + `g4` + `query_id`；`GET /status`；`GET /result/<id>`），`--device` 缺省 `cuda`，推理走同一 `InferenceAdapter`（`controller/language_selector.py` 的 `LocalHfAdapter`/`HttpAdapter`）；会话侧 `K_ret = k_ret_of(p95, hz)`、`K_PUB 2`、`T_STALL_S 3.0`、`T_CONF_S 10.0` | `tools/language_serve.py`；`controller/language_loop.py`；`controller/language_selector.py` |
| 11 | 文件桥：`runtime/frames/frame_<id>.jpg/.json`（`tethered-sensor-frame/v3`，`capture_unix_s`、`capture_monotonic_s`、`capture_monotonic_clock_id=system-stopwatch/v1`）+ 原子发布的 `frames/latest.json`；回程 `tracking_observation.json`、`gimbal_command.json`、`body_command.json`、`tracker_state.json`、`language_result.json`；请求槽 `language_request.json` + 本机 O_EXCL `language_request.lock` | `runtime/README.md`；`Assets/TetheredTracking/Scripts/SensorFrameWriter.cs` |
| 12 | 发布最终门第 ⑤ 项用**两种时钟**：`T_pub` 用本机 monotonic 相对 `load_monotonic_s`（加载时刻，本机），`T_stall` 用本机 Unix 墙钟相对 `capture_unix_s`（采集机墙钟）——跨机后后者取决于两机墙钟偏差；`TrackLoop` 观测记录的 `frame_age_ms` 同样是 `time.time() − capture_unix_s` | `controller/gated_publisher.py`（`_gate` ①–⑤）；`controller/track_loop.py`（`frame_age_ms`） |
| 13 | Unity 侧无命令时的行为（静态读码）：机身命令带 `expires_after_s`，过期即忽略；云台 `RotateTowards` 120°/s、离底 ≤ 45°、过期不回中 | `Assets/TetheredTracking/Scripts/BodyCommandReceiver.cs`；`TetheredGimbal.cs`；`config/scenario.default.json`（`sensor 640×480、capture_hz 5、jpeg_quality 85、retained_frame_count 128`） |
| 14 | 5060 与 Jetson 的 SSH 走 Tailscale（历史操作记录）；桌面机 = 运行 Unity 的用户 Mac；两机之间目前没有有线直连记录 | `docs/evidence/P1-ENG-LOOP-001-operations.md`；`docs/authorizations.md` 09-19…09-24 各条 |

## 1. 目的与价值

主线目标（`docs/project-background.md` §3，逐字）：

> 做一个闭环系统：语言指定目标，快层跟上并保持居中，换目标时能迁移并跟上新目标，丢失与歧义显式报告。VLM 是主角（接口 A：输出框 + 所在 frame_id）；快层是非变量，但必须能换目标。部署目标是 VLM 与快层跑在 Jetson Orin Nano 8GB（headless），Unity 留桌面机。项目的难点是「发现目标 → 跟上」，不是保持跟踪。验证只看四类数字：陈旧指定解析成功率随延迟、转向存活率、捕获时间与成功率按偏角/距离分桶、误锁率与显式报告比例。不作为目标：单目标稳态保持率不设资格门；不做 ReID、SAM 2 在线、更大模型、INT8、SAHI、Unity 场景改动；不为快层做研究主张；VLM 剪枝等优化只在闭环跑通且曲线证明延迟重要之后。

本项落实主线目标中的**部署目标**一句，回答四个只能靠板端实测回答的问题，产出**描述性数字 + 一份建议**，不产生任何研究主张、不做优化：

- **Q1 快层**：冻结的 `det-assoc-v1`（权重、规格、关联参数一字不改）在板上以 TRT FP16 运行，单帧时延、与桌面检测结果的一致性、30 min 热稳态各是多少。
- **Q2 VLM**：C2（Qwen3-VL-2B + LoRA）在板上能否以 INT4 常驻运行（先 llama.cpp 冒烟、后 TRT Edge-LLM 正式路径）；单次指定 p50/p95、峰值内存；**INT4 量化是否改变 609 行评估集上的三态行为**（这是「板上 VLM 能否成立」的核心判据，也是接受裁定 (b) 把 K3 纳入停点的原因）。
- **Q3 共驻**：快层 + VLM 在 8 GB headless 上同时运行时，快层 p95 是否仍在预算内、峰值内存、是否 OOM。
- **Q4 中继**：Unity 留桌面机、控制器上板后，帧到达抖动、命令回程时延、两机墙钟偏差对发布门 ⑤ 的影响、断链/恢复行为各是多少与怎样。

三层任务对应：层 1/2 归 `P1-ENG-ACQ-001`；本项是层 3「嵌入式 Jetson 部署问题（硬件算法 + VLM 能不能运行，硬件算法要做什么妥协）」（账本 09-28 用户原话 3）。本项**不做任何妥协**，只测量并把「需要妥协的地方」以数字交回用户。

## 2. 范围与不做的事

### 2.1 步骤（顺序 S0 → S1 → S2 → SR → S3 → S4 → S5，接受裁定 (f)）

**verdict 三值与处置总则（AR1-2）**：每步产出 `PASS` / `STOP(<原因码>)` / `NOT_RUN(<原因>)` 三值之一，写入证据文件；**verdict 是读数，不是本项验收**（验收见 §4）。

- `STOP(<原因码>)`：该步未过预注册线或遇到本项不得自行处理的环境问题。原因码闭集：`NOT_SUPER`、`FREQ_CAPPED`、`NOT_HEADLESS`、`POWER_MODE_NOT_MAXN_SUPER`、`IDLE_RAM_OVER`、`LATENCY_OVER`、`FP16_BOX_DIVERGENCE`、`THERMAL_THROTTLE`、`FRAME_DROP`、`RELAY_INTEGRITY`、`KERNEL_PARAM_REQUIRED`、`VLM_OVER_LINE`、`QUANT_NOT_EQUIVALENT`、`CORESIDENCY_OVER`。任一步 `STOP` 即**停止全部后续步骤**（后续步骤记 `NOT_RUN(S<k> STOP <原因码>)`），实现角色写完该步证据与 §3.4 报告后回接受角色→用户；除 `RELAY_INTEGRITY`（§2.1 SR 行：中继实现缺陷，在 §5 SR 轮数内由实现角色返工重跑，接受角色在决策记录记一行归因）外，本项**不自行升级、不自行修复环境、不改阈值**。
- 用户对某个 `STOP` 作出「记录偏差并继续」的裁定后（逐字入账 `docs/authorizations.md`，接受角色在决策记录记一行），该步 verdict **保持 `STOP`**、不改写，其后各步在证据与报告里标 `RESUMED_AFTER_USER_RULING(S<k>)`；用户未裁定前后续步骤保持 `NOT_RUN`。
- `NOT_RUN(<原因>)` 原因闭集：`S<k> STOP <原因码>`、`待用户 (x)`（x ∈ h…n，§7）、`阶段 B 信封未签`、`GRID_MISMATCH`、`PATH_UNAVAILABLE(<路径名>)`（如 3b 图像路径在 JP7.2 不可用）。`NOT_RUN` 的步骤对应的 AC 一律**不得记为满足**。
- 分位数一律 nearest-rank（p95 = 升序第 ⌈0.95·n⌉ 个值），每个分位数旁写分母 n。

| 步 | 内容 | 通过线（预注册） | STOP / NOT_RUN 时的处置 |
|---|---|---|---|
| **S0 环境核验**（只读、零模型） | `sudo nvpmodel -q`；`cat /etc/nv_boot_control.conf`；GPU/CPU 最高频率（devfreq/cpufreq sysfs）；`systemctl get-default` 与 display-manager 状态；headless 空闲 `tegrastats` 5 min；`dmesg \| grep -i nvmap`；`free -m`、swap 配置、磁盘余量；`nvcc --version`、`python3 -c "import tensorrt, torch"` 版本 | `nv_boot_control.conf` 含 `super`；`nvpmodel -q` **当前模式 = MAXN_SUPER**（AR1-3：仅「可选未选」不算过）；GPU 上限 1020 MHz、CPU 1.7 GHz；`systemctl get-default` = `multi-user.target` 且 display-manager `inactive`；headless 空闲 RAM ≤ 1.2 GB | 非 Super → `STOP(NOT_SUPER)`（重刷/固件属用户在 Linux 主机的操作，§7 (k)）；频率封顶 → `STOP(FREQ_CAPPED)`；MAXN_SUPER 可选未选 → `STOP(POWER_MODE_NOT_MAXN_SUPER)`，交用户 (m)，本项不执行 `nvpmodel -m`；非 headless → `STOP(NOT_HEADLESS)`，交用户 (l)，**未授权不执行 `systemctl isolate`**；空闲 RAM 超 → `STOP(IDLE_RAM_OVER)`。以上任一 STOP 时 S1–S5 与 SR 全部 `NOT_RUN(S0 STOP …)` |
| **S1 快层单测** | 板上从冻结 `.pt`（sha 核对）导出 TRT FP16 两版：方形 `imgsz=640` 与矩形 `imgsz=(480,640)`；a7 前 320 帧回放（事实 4 口径、同一 init 框）；分项记 `trtexec` GPU 时间、插件 `update` p50/p95、GMC 单独、关联器单独、CPU 占用、进程 RSS/统一内存；检测级与 `frozen-V` 缓存（MPS）逐帧比对 | **两个分量、同为 verdict 条件**（AR1-2）：**时延** = 方形引擎 `update` p95（n = 320）≤ 200 ms（门；50 ms 只是参考线，另记布尔 `within_50ms`，不影响 verdict）；**一致性** = 方形引擎前 50 帧检测数不一致帧数 = 0 **且** 320 帧框归一化最大差 ≤ 1e-3（沿用事实 4 限值，不改）。两分量都过才 `PASS`；矩形引擎同口径单独报告，不进 verdict | 时延超 → `STOP(LATENCY_OVER)`；一致性超 → `STOP(FP16_BOX_DIVERGENCE)`，证据附 IoU 分布、逐帧最大差直方图、不一致帧清单（帧号、两侧检测数、最大差），**不得记 `PASS`、不得静默继续**；S2、SR、S3–S5 均 `NOT_RUN(S1 STOP FP16_BOX_DIVERGENCE)`，报告交接受角色→用户二选一：(α) 记录偏差、以该 FP16 引擎继续（S1 保持 `STOP`，后续标 `RESUMED_AFTER_USER_RULING(S1)`，阈值与引擎精度不改）；(β) 关闭本项。该裁定涉及硬件读数取舍，不在 supervisor D4/D5/D6 代拍闭集内 |
| **S2 快层热稳态** | 方形引擎 + 插件以申请 15 Hz（若 S1 p95 ≤ 33 ms 则加测 30 Hz）循环回放 30 min；每 5 min 一格记 p50/p95、`tegrastats` GPU/CPU 频率与温度、丢帧数（处理落后于回放节拍即计丢） | 最后 5 min p95 ≤ 首 5 min 的 1.2 倍；频率无降频；丢帧 0 | 降频 → `STOP(THERMAL_THROTTLE)`，附温度曲线；丢帧 → `STOP(FRAME_DROP)` |
| **SR 中继测试**（零 Play、零 Unity；桌面机回放录制帧） | §3.2 的 `tools/eng_jet/relay.py`：桌面机以 5 Hz 把 a7（≥ 1,500 帧）按 v3 合同重发布到独立运行目录，中继推到板上镜像目录并原子发布；板侧两种应答器：(a) 回声（零模型，收到即写绑定同 `frame_id` 的 `tracking_observation.json`）；(b) 真实 `TrackLoop` + S1 的 TRT 插件（init 框取首帧检测器自身 `target` 类最高分框，**不用真值**）。每 1 s 一次四时戳对时估计两机 Unix 偏差；断链两次（10 s、60 s） | 包完整率 100%（sha 一致）、顺序零违反、`latest.json` 在板上从不指向不完整包；到达时延与回程时延 p50/p95/max 报告；`capture_age_s`（板侧墙钟 − `capture_unix_s`）分布对照 `T_STALL_S 3.0`、`load_elapsed` 对照 `T_pub 0.4 s`；断链：两侧不崩溃、无不完整包、恢复后 60 s 内到达时延回到稳态。**正式轮只在 §7 (h) 已答复的链路上跑**；答复前只允许 ≤ 1 轮 `TAILSCALE_SMOKE`（用于验证中继实现，读数只写 `-relay.json`「tailscale_smoke」小节，不进 forward/return/disconnect 结论，AC-4…6 记 `NOT_RUN(待用户 (h))`） | 完整率 < 100% 或不完整包出现 → `STOP(RELAY_INTEGRITY)`：中继实现缺陷，实现角色返工后在 §5 轮数内重跑，不上板继续其他步骤；墙钟偏差使 `capture_age_s` p95 > `T_stall` → 不 STOP，作为 K1 接口发现交 ACQ-001（§3.5）；(h) 未答复 → 正式轮 `NOT_RUN(待用户 (h))`，S3 起照常按顺序（SR 不阻塞 S3 的前提只在 (h) 未答复这一种情形） |
| **S3 VLM 单测**（快层不开；阶段 B） | 3a（可选，§7 (j)）HF bf16 + C2 未合并 adapter：装不下即记 OOM 即止；3b llama.cpp（板上源码编译 `-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=87`）：先官方 base GGUF Q4_K_M + mmproj F16 冒烟（验证 JP7.2 图像路径），再 C2 合并后自转 GGUF Q4_K_M；3c TRT Edge-LLM INT4 AWQ + FP16 ViT（C2 先合并、在 §7 (i) 答复指定的 x86 Linux GPU 主机量化，板上源码编译并建引擎）。**样本与分母（AR1-1）**：每条路径先做 **3 次预热**：帧 = a7 `frame_0000000000/100/200.jpg`（阶段 A 已在板上；事实 6 核实不在 smoke 帧集合内），surface 固定 `the car`，输出不进任何统计；预热第 1 次的端到端时延单独记为 **冷启动**，引擎/权重加载时间单独记。随后按 `smoke.jsonl` **行序**逐行各请求一次（32 次），`cache_prompt` 关，每行记 `first_seen`（该 `frame_id` 首次出现）：**首见行 25** = 新帧时延集合（唯一帧，分母 25）；**重复行 7**（行索引 8, 9, 10, 12, 18, 20, 22）另列 `repeat` 组（p50/max，只作缓存核查：若 `repeat` 中位 < 首见行中位的 0.5 倍则标 `CACHE_SUSPECT`，该路径读数作废、修正后重跑，重跑计入 §5 查询上限）。解析失败分母 = 32 行全部（首见 + 重复），经冻结解析器；核对图像 token 数 = 300 | **新帧**（首见行 25）p50 ≤ 1.6 s、p95 ≤ 2.5 s（nearest-rank，n = 25 → p95 = 第 24 个）；峰值统一内存 ≤ 4.6 GB；解析失败 0/32；重复行与冷启动不入通过线、只报告 | 3b 图像路径在 JP7.2 不可用 → 3b 记 `NOT_RUN(PATH_UNAVAILABLE(llama.cpp-vision))`，继续 3c；3c 建引擎需改内核参数（如 `cma`）→ `STOP(KERNEL_PARAM_REQUIRED)`（系统设置属用户）；所有已运行路径都不过线 → `STOP(VLM_OVER_LINE)`；(i) 未答复 → 3c、3b 的 C2 自转 GGUF 及二者的 S4 记 `NOT_RUN(待用户 (i))`（官方 base GGUF 冒烟不依赖 (i)）；(j) 未答复 → 3a `NOT_RUN(待用户 (j))`，不下载 base；阶段 B 信封未签 → S3 整步 `NOT_RUN(阶段 B 信封未签)` |
| **S4 量化等价**（核心；阶段 B） | 在板上用 S3 过线的量化 C2 产物跑 609 行（`eval.blind.jsonl`，gold 不上板），桌面机以 `evaluate.py --baseline` 对 C2 bf16 预测评分：表 G 各组差值、三态混淆（none / 歧义 / 给框）、解析失败数；两条路径都过线则各跑一次；可选 S4-a：官方 base GGUF vs base bf16 零样本预测，用于隔离「合并+转换」与「量化」两种误差源 | **预注册探测阈值（接受裁定 (c)，不是研究资格门）**：各组 \|Δ\| ≤ 3 pp；G5 硬给框率不高于 bf16 C2（21/100）；解析失败 0/609。报告必须列出每组原始分母 n、bf16 与量化两侧的原始计数与逐组差值，**不得写成「研究资格通过」** | 不过线 → `STOP(QUANT_NOT_EQUIVALENT)`，报告两条路径差值表 + 建议（§6 失败模式 (v)）；图像 token ≠ 300 → 该路径 `NOT_RUN(GRID_MISMATCH)` |
| **S5 共驻**（阶段 B） | 快层按 S2 帧率回放 + 每 10 s 用一张新帧向板上 VLM 服务（`language_serve.py` + §3.3 适配器）查询一次，持续 30 min（180 次）；帧 = `eval.blind.jsonl` 行序中首次出现的前 180 个互异 `frame_sha256`（事实 7：392 张可选），surface 取该行；记快层 p95、连续丢帧、VLM p95、峰值 RAM、`dmesg` NvMap/OOM、swap 使用 | 快层 p95 ≤ S1 的 2 倍且 ≤ 100 ms；无连续 > 2 帧丢帧；VLM p95（n = 180）≤ S3 新帧 p95 的 1.3 倍；峰值 RAM ≤ 7.0 GiB；`dmesg` 无 NvMap/OOM；swap 使用 0 | 不过线 → `STOP(CORESIDENCY_OVER)`，报告峰值与时序图 + 建议（§6 失败模式 (vi)） |

SR 排在 S3 之前的理由：SR 只依赖 S1 产物、不依赖任何模型下载，能在信封阶段 A 内先把拓扑风险测清（§5）；接受裁定 (f) 同意该顺序，实际运行仍受各步 STOP 与用户信封约束。

### 2.2 前提

- **headless 为前提**：S0 不满足即 `STOP(NOT_HEADLESS)`，不进入 S1；所有内存读数都在 headless 下取；本项不执行 `systemctl isolate`，除非用户对 §7 (l) 的允许已逐字入账。
- **零 Play、零 Unity 改动**：帧全部来自数据根已归档的 a7、smoke 与评估帧；`Assets/` 与 `controller/` 的 git diff 为空（AC-10）。
- **冻结资产一字不改**：权重、`freeze.json`、`det-assoc-v1.models.json`、C2 adapter、prompt v2、解析器、609 行评估集与其 gold、`smoke.jsonl`；板上运行只经构造函数注入（事实 3）与外部线束。
- **真值隔离**：板上只收 `eval.blind.jsonl` 与帧 JPEG/元数据 sidecar；gold、真值 sidecar、索引不上板；SR 不镜像任何 `truth/` 路径；`smoke.jsonl` 上板前剥去 `target_*`/`state` 字段，只留 `sample_id`、`frame_id`、`frame_sha256`、`surface`、`g4` 所需字段。
- **§7 (h)–(n) 答复前的缺省是「不做」**：不接线以外的正式链路结论、不租云、不做 WSL2 量化、不跑 3a、不重刷、不 `systemctl isolate`、不 `nvpmodel -m`、不推定阶段 B 已签；细则见 §7「待用户」。

### 2.3 明确不做

不做优化、不做剪枝、不做 INT8（检测器与 VLM 都不做）、不做投机解码、不换模型（4B / Qwen2.5-VL-3B / 0.8B 均不试）、不重训检测器、不改 VLM 任务形式（接口 A：出框 + `frame_id`，不改选候选 ID）、不改 prompt 与网格；不把 Unity 搬上板、不改 Unity 场景/脚本/文件桥；不改 `controller/`、不改冻结规格（`device_policy` 扩展留给 ACQ-001 K3 或后续立项）；不做 vLLM / MLC / jetson-containers / DeepStream / C++ 化；不做唤醒式 VLM（只测常驻）；不改内核参数、不改默认 target、不改功耗模式（`nvpmodel -m` 属用户或另授权，§7 (m)）、不 `jetson_clocks` 锁频（按 MAXN_SUPER 缺省调频测）；不做 Tailscale 作为正式链路的时延主张（只作冒烟）、不做缆内链路硬件；不改运行时帧率合同（5 Hz 不变；S2/S5 的 15–30 Hz 只是板上回放压力档）；不改发布门语义（跨机时钟只测量、不改 `T_stall`/`K_pub`）；不做 Unity-in-the-loop 的中继测试（属 ACQ-001 Play 或后续另签）；不为部署做研究主张；不把板上读数外推到真机航拍或系留缆链路；不改 S1 的 1e-3 限值与 S4 的探测阈值。

## 3. 接口与数据契约

### 3.1 板上快层线束（`tools/eng_jet/fastlayer_bench.py`）

- 构造 `DetAssocTracker(spec=config/det-assoc-v1.models.json, model_loader=<载入 .engine 的 ultralytics YOLO>, device="cuda:0")`：规格文件不改（`device_policy` 仍是 `mps→cpu`，因显式传 `device` 而不经 `_resolve_device`）；`manifest_identity()` 照常报告 `.pt` 的 sha；引擎的 sha、`trtexec`/TensorRT 版本、导出参数（`half=True`、`imgsz`、`dynamic=False`、`workspace`）另记 `-fastlayer.json`，**不改插件身份**。
- 引擎在板上从冻结 `.pt` 导出（`ultralytics` `export(format="engine", half=True, imgsz=…)`），导出前后核对 `.pt` sha；两版引擎各记 sha。
- 回放：a7 前 320 帧（事实 6）按 G-7 口径逐帧 `update`；输出每帧 `(state, box, reason, t_update_ms, t_detect_ms, t_gmc_ms, t_assoc_ms)` JSONL 与检测级行 `[x,y,w,h,conf,cls]`，与 `frozen-V` 前 320 帧逐帧比对（计数不一致帧数、最大归一化差、IoU 直方图、逐帧最大差直方图、不一致帧清单——后两项在 `FP16_BOX_DIVERGENCE` 时为必填）。
- 若 ACQ-001 的常驻协议（`step(image, frame_id, metadata)`）已落地，线束改调 `step`，读数口径不变；不依赖 ACQ-001 落地。

### 3.2 中继（`tools/eng_jet/relay.py`，两端各一进程，纯标准库）

- **文件字段零改动，但属 K1 检查对象（接受裁定 (e)）**：Unity 侧文件桥与控制器侧文件的字段、命名与原子发布语义都不变；中继是两者之外的搬运者。但中继引入了新的 TCP 搬运通道与两机时间语义（到达时延、墙钟偏差、`capture_age_s`），**这些进 K1**，本项不再表述为「不需 K1 的纯搬运」。前向：桌面机监视 `<runtime>/frames/latest.json`，仅当指针更新且两成员文件齐全时，按「先成员、后 `latest.json`」的顺序把 `frame_<id>.jpg`、`frame_<id>.json`、`latest.json` 推到板上镜像 `<runtime>`，板侧写临时文件后 `rename` 原子发布。回程：板侧监视 `tracking_observation.json`、`gimbal_command.json`、`body_command.json`、`tracker_state.json`、`language_result.json`，逐文件原子推回桌面机。**不中继** `language_request.json` 与其 O_EXCL 锁（锁是本机语义；操作者请求应在会话所在机器写入，属 ACQ-001/K1 接口事项，§3.5）。
- **传输**：TCP 长度前缀消息，每条含路径、字节、sha256、发送端 `unix`/`monotonic` 时戳；接收端记到达时戳；所有收据写 `relay-receipts.jsonl`。断链：发送端阻塞重连（指数退避 ≤ 2 s），**不缓存补发**过期帧（只补发当前 `latest.json` 指向的包），回程文件同理；恢复后行为如实记录。
- **对时**：每 1 s 一次四时戳往返（NTP 式）估计两机 Unix 偏差与 RTT；报告偏差中位/漂移；若板上配置了 chrony，另附 `chronyc tracking`。到达时延 = 板侧到达 unix − 桌面发布 unix − 偏差估计。
- **运行目录**：桌面机 `outputs/eng-jet/runtime-desktop/`，板上 `~/eng-jet/runtime/`；主树 `runtime/` 零写入。回放器 `tools/eng_jet/replay_publish.py` 以 5 Hz 重写 a7 帧为 v3 合同（`frame_id` 递增、`capture_unix_s`/`capture_monotonic_s` 取桌面机当下时钟、`clock_id` 逐字沿用），JPEG 字节不改。
- **链路**：正式轮的链路由用户答复 §7 (h) 决定（推荐有线直连或同一交换机）；答复前无正式链路，只允许 ≤ 1 轮 `TAILSCALE_SMOKE`，其读数单独小节、不进结论表、不支撑 AC-4…6。

### 3.3 板上 VLM 服务

- 复用 `tools/language_serve.py`（单工提交/轮询）；为两条运行时各写一个 `InferenceAdapter`（放 `tools/eng_jet/adapters.py`，不进 `controller/`）：llama.cpp 走 `llama-server` 的 OpenAI 兼容口（`cache_prompt=false`、`temperature 0`、`max_tokens 160`），TRT Edge-LLM 走其实验性服务端或 Python 绑定。两者都输出原始文本，经冻结 `tools/eng_sft/parse.py` 解析；prompt v2 逐字不改；图像 640×480 原样送入，核对图像 token = 300（网格 `[1,30,40]` 等价），不等价即在报告标 `GRID_MISMATCH` 并停用该路径的 S4。
- **S3 请求序（AR1-1）**：预热 3 次（a7 帧 0/100/200，surface `the car`）→ `smoke.jsonl` 32 行按行序各 1 次；线束按 `frame_id` 首次出现计算 `first_seen`，逐行输出 `{sample_id, frame_sha256, first_seen, t_total_ms, t_vit_ms?, t_prefill_ms?, t_decode_ms?, parsed_ok}`；预热与冷启动行单列、不混入 32 行。
- **量化产物**：(i) 官方 base GGUF Q4_K_M + mmproj F16（冒烟与 S4-a）；(ii) C2 合并（`merge_and_unload`）→ bf16 → `convert_hf_to_gguf.py` → `llama-quantize Q4_K_M`；(iii) C2 合并 → AWQ INT4（TRT Edge-LLM 官方流程，在 §7 (i) 指定的 x86 Linux GPU 主机）→ 板上建引擎（`maxInputLen`/`maxKVCacheCapacity` 申请 1024）。每个产物记来源、命令、sha256、体积。(ii)/(iii) 的合并与量化都在 §7 (i) 答复并签阶段 B 之后才执行。
- 对 ACQ-001 的接口：板上 `LanguageSession.HttpAdapter` 指向 `http://127.0.0.1:<port>`（同机），零代码改动；`K_ret` 由本项报告的板上 p95 经 `k_ret_of(p95, hz)` 派生，本项只给 p95 不定 K。

### 3.4 证据文件（全部 `docs/evidence/P1-ENG-JET-001-*`）

`-env.json`（S0）、`-fastlayer.json`（S1/S2）、`-relay.json`（SR：`forward`/`return`/`disconnect` 三个结论小节 + `tailscale_smoke` 非结论小节）、`-vlm.json`（S3：每路径 `warmup`/`cold_start`/`first_seen`/`repeat`/`parse` 五组）、`-quant-equivalence.json`（S4，含 `evaluate.py` 摘要、每组原始分母与三态混淆）、`-coresidency.json`（S5）、`-assets.json`（AC-11）、`-ledger.json`（AC-10；含 `pending_user` 小节，AC-15）、`-report.md`（AC-13）、`-K1K3K4-handoff.md`（停点自证）。原始日志（`tegrastats`、`dmesg` 摘录、`trtexec` profile、`relay-receipts.jsonl`、逐行预测）放 `outputs/eng-jet/P1-ENG-JET-001/`（`.gitignore` 追加，接受裁定 (g)）并在板上 `~/eng-jet/` 留副本，报告只引用 sha。

### 3.5 对 `P1-ENG-ACQ-001` 的接口依赖（只列依赖，不重复其范围）

| 方向 | 内容 |
|---|---|
| JET → ACQ | 板上快层单帧 p50/p95（S1）、GMC 光流单独成本（供 ACQ-001 §3.3 位姿单应替换的权衡）、共驻下快层 p95（S5）、VLM 板上 p95（S3，供 `K_ret` 派生）、两机墙钟偏差与 `capture_age_s` 分布（SR，供其 K1 决定新鲜度门是否改为「中继到达相对年龄」——本项不改门） |
| ACQ → JET | 若常驻协议 `step(image, frame_id, metadata)` 先落地，S1/SR (b) 改调 `step`；`language_request` 锁的跨机语义由 ACQ-001 K1 定，本项不中继该槽 |
| 共同不变项 | 5 Hz 合同、`K_pub 2`、`T_pub 0.4 s`、`T_stall 3 s`、接口 A、冻结检测器规格与权重、prompt v2 与 609 行评估集 |

## 4. 验收项（AC 表）

停点短名按接受裁定 (b) 为 `K1K3K4`（§7）。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-1 | S0 证据含 §2.1 列出的每项读数原文（`nvpmodel -q` 当前模式、`nv_boot_control.conf`、GPU/CPU 上限频率、默认 target 与 display-manager 状态、5 min 空闲 `tegrastats`、`dmesg nvmap`、内存/swap/磁盘、CUDA/TRT/torch 版本）与按预注册线给出的 verdict；缺任一读数、verdict 与读数不符、把「MAXN_SUPER 可选未选」或「非 headless」记为 `PASS`、或证据显示本项执行了 `systemctl isolate`/`nvpmodel -m` 而账本无 §7 (l)/(m) 答复即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-env.json` | K1K3K4 | |
| AC-2 | S1 证据含两版引擎（sha、导出参数、TRT 版本）、320 帧逐帧计时四分项、`within_50ms` 布尔、检测级比对（计数不一致帧数、最大归一化差、IoU 直方图）及**两分量 verdict**；一致性超线时须含逐帧最大差直方图与不一致帧清单且 verdict = `STOP(FP16_BOX_DIVERGENCE)`；引擎不是从 sha 核对过的冻结 `.pt` 导出、规格/权重/关联参数任一被改、缺比对、超线记 `PASS`、或超线后 S2–S5 未记 `NOT_RUN`/`RESUMED_AFTER_USER_RULING(S1)` 即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1」；cmd: `tools/eng_jet/fastlayer_bench.py` | K1K3K4 | |
| AC-3 | S2 证据含 30 min 每 5 min 一格的 p50/p95、频率、温度、丢帧数与 verdict（15 Hz 必有；30 Hz 按 §2.1 条件）；缺格或未记录频率/温度即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S2」 | K1K3K4 | |
| AC-4 | SR 完整性：≥ 1,500 帧经 §7 (h) 答复链路中继后板上包完整率、顺序违反数、`latest.json` 指向不完整包的次数三项均有计数，且中继成功要求三项分别为 100% / 0 / 0；到达时延 p50/p95/max 与对时偏差中位/漂移已报告；(h) 答复前本条 `NOT_RUN(待用户 (h))`；任一计数缺失、成功声明与计数矛盾、或 `TAILSCALE_SMOKE` 读数被写进 `forward` 小节即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-relay.json`「forward」；test: `tests/test_eng_jet_relay.py::test_atomic_publish_order`（本机双进程回环，零硬件） | K1K3K4 | |
| AC-5 | SR 回程：回声与真实 `TrackLoop` 两种应答器各报回程时延 p50/p95/max、端到端 p95、`capture_age_s` 与 `load_elapsed` 分布对照 `T_STALL_S`/`T_pub`、真实模式下观测记录的 `frame_age_ms` 分布与超 `T_stall` 比例；init 框来源记录为检测器输出（任何真值来源即不满足）；(h) 答复前 `NOT_RUN(待用户 (h))`；缺任一模式或混入 `TAILSCALE_SMOKE` 读数即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-relay.json`「return」 | K1K3K4 | |
| AC-6 | SR 断链：10 s 与 60 s 各一次，记录两侧进程存活、断链期间板侧写桥次数、恢复后 `frame_id` 缺口、`latest.json` 帧差、`TrackLoop` 终止/继续语义、回到稳态到达时延所需时间；(h) 答复前 `NOT_RUN(待用户 (h))`；未做两次或缺任一字段即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-relay.json`「disconnect」 | K1K3K4 | |
| AC-7 | S3 每条已运行路径（3a 可选、3b 两个 GGUF、3c）证据含：预热 3 次（帧 = a7 0/100/200，输出不入统计）、冷启动（预热第 1 次）、加载时间；32 行按 `smoke.jsonl` 行序逐行 `first_seen` 标记；**首见行 25** 的 p50/p95/max（n = 25，nearest-rank）作为新帧读数与 verdict 依据；**重复行 7**（行索引 8, 9, 10, 12, 18, 20, 22）单列 `repeat` 组 p50/max 与 `CACHE_SUSPECT` 判定；解析失败数分母 32；分项时延（运行时可暴露者）、峰值统一内存、图像 token 数与 verdict。`cache_prompt` 未关、首见/重复行混算、预热或冷启动混入 32 行、分母不是 25/32、token 数未核、或用 `NOT_RUN` 路径记满足即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-vlm.json` | K1K3K4 | |
| AC-8 | S4 对每个过线产物：609 行板上预测（盲文件）由桌面机 `evaluate.py --baseline <C2 bf16>` 评分，证据含每组原始分母 n、两侧原始计数、逐组 Δ、三态混淆矩阵、解析失败数、按 §2.1 预注册探测阈值的 verdict；评估集与 gold 的 sha 与事实 7 一致；任何行被剔除、重标、gold 上板、缺原始分母、或把 verdict 写成「研究资格通过」即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-quant-equivalence.json`；cmd: `python3 -m tools.eng_sft.evaluate --manifest … --predictions … --baseline … --out …` | K1K3K4 | |
| AC-9 | S5 证据含 30 min 内快层 p95、最长连续丢帧、VLM 180 次的 p95（帧 = `eval.blind.jsonl` 行序前 180 个互异 `frame_sha256`，互异性以 sha 核对）、峰值 RAM、`dmesg` 摘录、swap 使用与 verdict；未同时运行（时间戳不重叠）或缺项即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-coresidency.json` | K1K3K4 | |
| AC-10 | 消耗账本：§5 每一维度都有计数（下载：条目、字节、sha；pip：机器、包、版本；云：GPU·h、美元、实例 ID；板上编译/占用墙钟；传输字节；VLM 查询次数含预热与重跑）且 ≤ 已签发信封，未签发维度为 0；`git diff` 对 `Assets/`、`controller/`、`config/` 为空；Play/scenario/session/run ID/训练 = 0。任一超限或 diff 非空即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`；cmd: `git diff --stat <base>..<candidate> -- Assets controller config` | K1K3K4 | |
| AC-11 | 资产核实：使用前记录并核对 `.pt`、`freeze.json`、`frozen-V.jsonl.gz`、a7 前 320 帧、`smoke.jsonl` 与其 25 帧（sha 与行内 `frame_sha256` 逐帧一致）、C2 adapter、base 各分片、`eval.jsonl`/`eval.blind.jsonl`、C2 bf16 预测、官方 GGUF、每个自产量化产物的 sha256 与体积；任一不一致而未 STOP 即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-assets.json` | K1K3K4 | |
| AC-12 | 隔离：板上文件清单（`find ~/eng-jet`）不含 gold、`truth/`、索引、`smoke.jsonl` 的 `target_*`/`state` 字段或数据根其他内容；数据根零写入；主树 `runtime/` 零写入；受保护写入断言存在。清单含上述任一路径/字段或断言缺失即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-assets.json`「board_manifest」；test: `tests/test_eng_jet_guards.py` | K1K3K4 | |
| AC-13 | 报告：每步 verdict 表（`PASS`/`STOP(<原因码>)`/`NOT_RUN(<原因>)`，闭集见 §2.1；`RESUMED_AFTER_USER_RULING(S<k>)` 标记须指向账本条目标题）、Q1–Q4 的数字答案、一份建议（板上 VLM 可否成立、哪条运行时、ACQ-001 需承接的接口发现）、「不可推出」清单；每个数字可追溯到 §3.4 某个 JSON；出现未测量的 Jetson 性能主张、把 verdict 写成「验收通过」、把 `STOP` 改写成 `PASS`、或把 §7 未答复项对应的步骤写成已通过即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-report.md` | K1K3K4 | |
| AC-14 | Unity/硬件：本项零 Play、不改 Unity 运行行为，申请 `UNITY_NA`（理由：硬件证据即板上实测文件，Unity 侧零改动）并须复核角色在复核文件附议；候选自证小节写明每步的执行机器、时间与 `git rev-parse HEAD`；缺附议或缺执行记录即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md`；`docs/reviews/P1-ENG-JET-001.md`（附议） | K1K3K4 | |
| AC-15 | 待用户项缺省（AR1-3）：`-ledger.json`「pending_user」对 §7 (h)–(n) 逐项记 `answered(<账本条目标题>)` 或 `unanswered`；`unanswered` 项对应的动作零执行（(h) 正式 SR 轮、(i) 租云/WSL2 量化与 3c、(j) 3a 与 base 下载、(k) 重刷、(l) `systemctl isolate`、(m) `nvpmodel -m`、(n) 阶段 B 任一维度）且对应步骤记 `NOT_RUN(待用户 (x))`/`NOT_RUN(阶段 B 信封未签)`；任一 `unanswered` 项的动作被执行、`answered` 项无账本条目、或其对应 AC 在答复前被记为满足即不满足 | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`「pending_user」 | K1K3K4 | |
| AC-16 | 新增义务（来源：实现待裁定 IR-18）：下一实现派发起，板上本项 Python 进程启动前显式设 `MPLCONFIGDIR=$HOME/eng-jet/home/mpl`，证据记录实际环境值与 `~/eng-jet` 外的新写入核查；既有 `YOLO_CONFIG_DIR`、`CUDA_CACHE_PATH` 重定向继续执行。缺 MPLCONFIGDIR 记录、路径不符或缺外部写入核查即不满足；既有外部缓存不删除，受保护根零写入要求不变 | artifact: `docs/evidence/P1-ENG-JET-001-env.json`（后续环境变量与外部写入核查）；`docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md`（后续执行记录） | K1K3K4 | 2026-10-03 |

## 5. 预算信封（申请值；**用户逐字签发前各维度均为 0，任何下载、安装、传输、上板运行、租云均不得开始**；账本没有即视为未发生；新设备、新额度、新消耗类别须由用户另签，不由 `P1-ENG-ACQ-001`、`P1-ENG-FAST-001` 或任何既有信封覆盖；签发后成功、失败、重试全部计入同一上限，耗尽即停；接受裁定 (d)：两阶段形状可向用户提交，接受侧不签发任一维度）

分两阶段申请，建议先签阶段 A；阶段 B 须在 S0–S2 `PASS` 后**另行签发**，阶段 A 的签发不含、也不推定阶段 B（§7 (n)）；(h)–(m) 中任一项未答复不阻止签阶段 A，只使对应动作保持 0。

| 维度 | 阶段 A：S0–S2 + SR | 阶段 B：S3–S5 |
|---|---|---|
| Consuming | no（无 scenario/session/run ID、无 Play、无 API 预算） | 走租云则 yes（云 GPU·h 与美元），走本地则 no |
| 设备 | 用户 Jetson Orin Nano 8GB Devkit Super（JP7.2）；桌面机 = 用户 Mac（Unity 宿主，只跑回放器与中继，零模型）；正式链路按 §7 (h) 答复（推荐有线直连或同交换机）；Tailscale 仅 ≤ 1 轮冒烟 | 同左 + 量化主机按 §7 (i) 答复（推荐租 x86 Linux GPU ≥ 24 GB 显存，同 SFT-002 的 vast.ai 类；5060 WSL2 不推荐） |
| 模型下载 | 0 | ≤ 4 条、≤ 7 GB：base `Qwen3-VL-2B-Instruct@8964…`（≈ 4.26 GB，仅当 (j) 答复为跑 3a 或量化主机需要且本地/T7 无副本）、官方 GGUF Q4_K_M（≈ 1.11 GB）+ mmproj F16（≈ 0.82 GB）+ 可选 mmproj Q8_0（≈ 0.45 GB）；每条记 sha |
| pip / 源码编译（板上） | ≤ 8 包、≤ 300 MB（`ultralytics`、`lap`、`onnx`/导出依赖等，`--system-site-packages` 复用 NVIDIA torch/TensorRT）；不重装 torch | ≤ 6 包；llama.cpp 源码编译 ≤ 1 h；TRT Edge-LLM 源码编译 + 建引擎 ≤ 3 h |
| 量化主机 | 0 | 租云 ≤ 2 GPU·h、≤ 4 美元（合并 + AWQ + GGUF 转换在同一实例）；或 WSL2 ≤ 4 h 墙钟；(i) 未答复 → 0 |
| 传输 | 到板 ≤ 100 MB（权重 5.5 MB、a7 前 320 帧 11.8 MB + sidecar、`frozen-V` 0.13 MB、代码束）；SR 每轮 ≤ 100 MB × ≤ 5 轮（含 ≤ 1 轮 Tailscale 冒烟） | 到板 ≤ 10 GB（合并 bf16 ≈ 4.3 GB 或量化产物、smoke 25 帧 1.26 MB + 剥字段后的 `smoke.jsonl`、448 张评估帧 19.8 MB、盲文件）；云 ↔ 本机 ≤ 10 GB |
| 板上占用墙钟 | ≤ 8 h（含两次引擎导出各 ≤ 20 min、S2 30 min、SR ≤ 5 轮） | ≤ 16 h（S3 各路径、S4 ≤ 3 × 609 行、S5 30 min） |
| 板上 VLM 查询 | 0 | ≤ 2,500 次（本地，不计 API；S3 每路径 35 = 3 预热 + 32，`CACHE_SUSPECT` 重跑同计） |
| 板上磁盘 | ≤ 5 GB（`~/eng-jet/`） | ≤ 40 GB |
| Mac | 零 pip、零模型；`outputs/eng-jet/` ≤ 2 GB | 评分与可选 GGUF 转换若在 Mac 做：pip ≤ 2（`gguf`、llama.cpp 构建依赖）；零 VLM 推理 |
| 系统设置（板上） | 只读核验；`systemctl isolate multi-user.target` 仅在 §7 (l) 答复允许后、会话级；`nvpmodel -m` 不做（§7 (m)）；(l)/(m) 未答复 → 0 | 同左；不改内核参数 |
| Unity Play / scenario·session·run ID / 训练 GPU·h / 模型 API / 对外发布 | 0 / 0 / 0 / 0 / 否 | 0 / 0 / 0 / 0 / 否 |

信封内的工程性重试（引擎重导、编译重试、SR 重跑、`RELAY_INTEGRITY` 返工、`CACHE_SUSPECT` 重跑）不需新授权，由接受角色在决策记录写一行归因；任何越界（第 5 轮 SR、第 3 GPU·h、第 5 条下载、换模型、Play、改系统设置）回用户。

## 6. 限制、不承诺与失败模式

- **不承诺**：任何研究主张；任何 Jetson 性能结论超出本板、本栈（JP7.2/CUDA 13.2/TRT 10.16）、本冻结资产与本回放序列；量化后模型在真实航拍或其他场景的行为；中继读数对系留缆链路的代表性（有线直连 ≠ 缆内链路；Tailscale 冒烟不代表任何链路）；Unity-in-the-loop 的行为（SR 零 Unity）；S2/S5 压力帧率对运行时 5 Hz 合同的任何改动。
- **已知生态风险（A3 §7 查不到清单，实测才知道）**：JP7.2 上 llama.cpp 的 Qwen3-VL 图像路径与 Tegra VMM issue；TRT Edge-LLM 在 JP7.2 建引擎是否仍需 `cma`；5060 WSL2 做 AWQ 是否可行；Orin Nano 无 DLA/NVENC，检测器与 VLM 抢同一 GPU。
- **数据限制**：a7 是脚本扫视采集；609 行评估帧曾被旧探针读取过（SFT-002 摘要 §6 已声明）；smoke 32 行只有 25 张互异帧（新帧分母 25，p95 = 第 24 个有序值，统计力弱，只作描述）；smoke 为 dev 23 / train 9 混合，不是评估集，不产生任何指标主张。
- **失败模式与预注册处置**：(i) S0 非 Super/非 headless/非 MAXN_SUPER → `STOP(NOT_SUPER | NOT_HEADLESS | POWER_MODE_NOT_MAXN_SUPER)`，重刷、切 target、切功耗模式都属用户；(ii) S1 FP16 一致性超线 → `STOP(FP16_BOX_DIVERGENCE)`，附 IoU 分布与逐帧差直方图回用户二选一（§2.1），不改阈值、不改引擎精度、不静默继续；(iii) SR 完整率 < 100% → `STOP(RELAY_INTEGRITY)`，中继返工（实现缺陷，不上板继续其他步骤）；(iv) SR 墙钟偏差使 `capture_age_s` 超 `T_stall` → 记为 K1 接口发现交 ACQ-001，本项不改门；(v) S4 不过线（三态行为被量化改变）→ `STOP(QUANT_NOT_EQUIVALENT)`，报告两条路径的差值表，建议由用户在「板上 VLM 不成立 → VLM 留桌面机/地面站」与「另立项试其他量化配方」间裁定，本项不代裁；(vi) S5 OOM 或快层 p95 超线 → `STOP(CORESIDENCY_OVER)`，报告峰值与时序图，同 (v) 交用户；(vii) 任一路径的图像 token ≠ 300 → 该路径 S4 `NOT_RUN(GRID_MISMATCH)`；(viii) S3 `repeat` 组中位 < 首见行中位的 0.5 倍 → `CACHE_SUSPECT`，该路径读数作废、修正后重跑。
- **不可推出**：S3/S5 时延不能推出闭环端到端指定时延（含人工确认）；S4 等价不能推出量化模型在线捕获成功率；SR 数字不能推出 Unity Play 下的门通过率；`TAILSCALE_SMOKE` 不能推出任何链路的时延。

## 7. 必经停点与提请裁定

### 7.1 停点（接受裁定 (b)）

- **`K1K3K4` 合并单候选**：K1 = 中继把帧/控制文件桥跨机搬运并引入新 TCP 搬运通道与两机时间语义（文件字段不改、语义只测量，但进 K1 检查，接受裁定 (e)）；K3 = 量化后 C2 在 609 行上的三态决策变化是模型决策检查对象（量化产物只作探测对象，不进闭环、不改插件身份与冻结规格）；K4 = 609 行量化等价与板上时延/内存作为对外报告的指标。**不触发 K2**（不改控制命令、不改安全约束）、**不触发 K5**。候选 = `tools/eng_jet/` + `tests/test_eng_jet_*.py` + §3.4 证据；一次 `C1@K1K3K4` → 新鲜上下文 `R1@K1K3K4`。
- **申请 `UNITY_NA`**（AC-14）：零 Play、Unity 零改动；硬件证据是本项自己的板上实测。

### 7.2 接受侧已裁定的设计取向（D1 裁定 (a)–(g)，作为 D2 修订依据；原文见「D1 接受裁定」）

(a) `Workflow: engineering-v1` 申请符合工程任务类型，待合同闭合并 `ACCEPTED` 时才逐字生效（本轮仍为申请）；(b) 停点 `K1K3K4`，已落实到 §7.1、§3.4、AC 表停点列与 AC-14 指针；(c) S4 阈值只是预注册探测阈值，报告须列原始分母与逐组差值，不称研究资格通过——已落实到 §2.1 S4 与 AC-8；(d) 两阶段信封形状可向用户提交，接受侧不签发任一维度——§5；(e) 新 TCP 搬运与两机时间语义进 K1——§3.2、§7.1；(f) 顺序 S0→S1→S2→SR→S3→S4→S5——§2.1；(g) 证据文件命名与 `outputs/eng-jet/` 忽略——§3.4。本节只复述裁定取向，不构成 AC/BC，也不构成任何执行授权。

### 7.3 待用户（AR1-3；**答复前的缺省一律是「不做」**，推荐项只供用户选择、不按推荐先执行；用户答复由当场会话逐字入账 `docs/authorizations.md`，接受角色在决策记录记一行后对应步骤才可在下一派发执行；七项都涉及设备、链路、主机、额度或系统设置，**均不在 supervisor D4/D5/D6 代拍闭集内**）

| 项 | 推荐项（供选择） | 答复前缺省 | 恢复条件 |
|---|---|---|---|
| (h) 中继正式链路 | 两机有线以太网直连或同一交换机（需用户接线并给板子固定 IP） | 无正式链路：SR 正式轮 `NOT_RUN(待用户 (h))`，AC-4…6 不记满足；只允许 ≤ 1 轮 `TAILSCALE_SMOKE`（阶段 A 信封已签且含该项时），读数只进非结论小节 | 用户答复链路并接好、板子可达；账本入账后 SR 正式轮在阶段 A 剩余轮数内执行 |
| (i) 量化主机 | 租云 x86 Linux GPU ≤ 2 GPU·h / ≤ 4 美元（同 SFT-002 供应商）；不推荐 5060 WSL2（8 GB 显存低于 TRT Edge-LLM 建议、可行性未查到） | 不租云、不 WSL2、不合并 C2：3c 与其 S4 `NOT_RUN(待用户 (i))`；3b 的 C2 自转 GGUF 需合并 bf16，同样等 (i)（合并在哪台机器做由 (i) 决定） | 用户指定主机并签阶段 B 对应维度 |
| (j) S3a HF bf16 对照 | 仅在板上已有 base 副本时跑，否则跳过 | 3a `NOT_RUN(待用户 (j))`，不为 3a 下载 base | 用户答复「跑」且阶段 B 下载维度已签 |
| (k) S0 非 Super 配置 | `STOP(NOT_SUPER)` 后由用户在 Linux 主机重刷，本项不做 | 停在 S0，全部后续 `NOT_RUN(S0 STOP NOT_SUPER)` | 用户告知重刷完成并入账；S0 重跑（只读，计入阶段 A 板上墙钟） |
| (l) 会话级 `sudo systemctl isolate multi-user.target` | 允许实现角色在板上会话级执行（不改默认 target） | **不执行**；S0 发现非 headless 即 `STOP(NOT_HEADLESS)`，后续 `NOT_RUN` | 用户自行切到 headless，或逐字授权会话级 isolate 并入账；S0 重跑 |
| (m) 功耗模式 | 用户在 S0 前自行设 MAXN_SUPER（`nvpmodel -m`），本项不改 | 不执行 `nvpmodel -m`；S0 发现当前非 MAXN_SUPER 即 `STOP(POWER_MODE_NOT_MAXN_SUPER)`，后续 `NOT_RUN` | 用户自行设定，或逐字授权本项执行一次 `nvpmodel -m <MAXN_SUPER>` 并入账；S0 重跑 |
| (n) 信封签发方式 | 先签阶段 A；S0–S2 `PASS` 后再签阶段 B | 未签任一阶段 → 全部维度 0，不上板；只签阶段 A → S3–S5 `NOT_RUN(阶段 B 信封未签)`，S0–S2 `PASS` 是申请阶段 B 的前提而不是签发 | 用户逐字签发对应阶段（账本条目标题写入 `-ledger.json`「pending_user」） |

### 7.4 推进方式

轮次由 supervisor 无人值守派发（决策信封 D1/D4/D5/D6，至 2026-10-10）；§5 信封首签、模型下载、量化、上板运行、系统设置、Play 归用户；D4 只可在已签信封内为已列步骤排序，不得据此推定 (h)–(n) 已答复。

## 8. 只读试读与试运行数字

### 8.1 本机只读试读（2026-09-28；零训练、零推理、零上板、零写入）

- **快层资产**：`.pt` 5,458,330 B（sha 与 `freeze.json` 一致）；`frozen-V.jsonl.gz` 130,702 B、3,168 行、头部 `device mps`；a7 前 320 帧 JPEG 11.8 MB（3,168 帧全序列 152 MB，在数据根，主树无）；预热三帧 a7 0/100/200 合计 97,519 B。
- **VLM 资产**：C2 adapter 69,788,264 B；base revision `8964…4203`（A3 [Q3] 称 `model.safetensors` 4.255 GB，未本机核实）；官方 GGUF Q4_K_M ≈ 1.107 GB + mmproj F16 ≈ 0.819 GB（A3 [Q2]，未本机核实）；评估集 609 行、392 张互异帧、绑定帧包 448 张 19,757,920 B（manifest）；smoke 32 行 / 25 张互异帧 / 7 重复行 / 25 帧 1,255,506 B、sha 逐帧核对一致、与评估帧交集 0（D2 本机核实，事实 9）。
- **桌面基线**：快层 CPU p95 48.4 ms / MPS p95 31.9 ms（事实 4）；VLM 5060 HTTP p50 4.18 s / p95 5.43 s（事实 9）；发布门 `K_pub 2`、`T_pub 0.4 s`、`T_stall 3.0 s`（事实 10/12）。
- **传输投影**：SR 每轮 1,500 帧 × ≈ 37 KB ≈ 55 MB + sidecar；S3 每路径 35 次查询（3 预热 + 32）；S4 每产物 609 行 × ≈ 1.5 s（A3 [估计]）≈ 15 min 板上时间。
- **A3 预算依据（[厂商标称]/[公开实测]/[估计]，非证据）**：YOLO11n TRT FP16 引擎 4.53 ms、端到端 ≈ 16 ms；Qwen3-VL-2B INT4 TRT Edge-LLM 在 JP7.2 官方 ViT 141 ms / prefill 167 ms / 解码 36.1 tok/s / 峰值 4,486 MB；2B INT4 + 快层 + headless 合计 5.4–7.2 GB vs 可见 ≈ 7.4 GiB；JP7.2 ISO 常装成非 Super（GPU 上限 624.75 MHz）——这些数字决定了 §5 的时长与 §2.1 的通过线，**本项实测后全部以证据文件为准**。
- **未试读**：板子当前是否开机/可达、当前功耗模式、是否 headless、磁盘余量（S0 才知道）；两机有线直连是否可用。

### 8.2 阶段B预检读数核清（2026-10-04，Acceptance；只读本机原输出）

登记轮次 `阶段B预检读数核清`；Dispatch-Id `P1-ENG-JET-001-阶段B预检读数核清-20261004T063127Z-9d72`。按 engineering §9 及「阶段B预检答复落实」§3核清，非D/C/R轮、不新增或改写AC、不签兼容性/性能/验收结论。本轮未执行预检或任何板端操作，consumed=none。

**来源与完整性。** 读取 `docs/evidence/P1-ENG-JET-001-stageb-boardprecheck.md` §1–2；从本机 `outputs/eng-jet/P1-ENG-JET-001/` 运行时解析唯一 `stageb-boardprecheck-*` 目录（唯一性已核，不抄实际目录名/工件SHA进合同）。六文件 `started_utc`、`ended_utc`、`elapsed_s`、`precheck.stdout`、`precheck.stderr`、`precheck.rc` 的sha256逐一现算，**6/6与证据§2一致**；stdout 6182 B、stderr 0 B、无local-error.txt。原始文件只读、不改删；下表来源均为该stdout具名块，错误原文仍在原件。

执行快照：2026-10-04T06:29:21.290265+00:00至06:29:22.334926+00:00，elapsed_s=`1.045510875`；已用1/1、重试0。整体rc=1，26项均执行到`### end`，无超时；非连接失败。四个块标记UNKNOWN（cmake_v/dpkg/cuda_dirs/sysvenv_numpy）、tools两字段MISSING继续保留；聚合错误不抹掉同块中成功的逐字段读数。

| 维度 / 原块 | 原读数 | 核清与限制 |
|---|---|---|
| user / os / l4t / glibc | 用户jetson；Ubuntu 24.04.4 LTS/noble；L4T `R39`、`REVISION: 2.0`、`EABI: aarch64`；`glibc 2.39`；各rc=0 | 系统文字身份/glibc已核；与W的cp312/manylinux_2_39_aarch64及Orin JP7.2载荷条件文字相符。当前未查内核/驱动/功耗/headless/频率，不把历史S0或标签当本轮重测；W实际文件、载荷选择/新算子兼容仍UNKNOWN。 |
| U1 tools / cmake_v | `cmake: MISSING`、`ninja: MISSING`；gcc/g++/cc/c++/make/git/curl、aarch64-linux-gnu-gcc/g++均在/usr/bin；nvcc=/usr/local/cuda/bin/nvcc；python3/python3.12在/usr/bin。tools rc=0；cmake_v原错`No such file or directory`、rc=127/UNKNOWN | cmake必需但缺失，版本UNKNOWN，U1未闭；ninja本路径不需要（已有make，采用Unix Makefiles），不申请安装。工具路径只证明command-v结果，不证明构建成功；cc/c++/交叉编译器/curl的独立版本未读，保持UNKNOWN、不补跑。 |
| gcc_v / gxx_v / nvcc_v | gcc与g++均`13.3.0-6ubuntu2~24.04.1` / 13.3.0；nvcc release13.2、V13.2.78，build cuda_13.2.r13.2/compiler.37668154_0；rc=0 | C/C++/CUDA编译器版本有原读数；不外推llama b11381构建或运行兼容。gcc/g++的dpkg元包版本与可执行文件版本分列。 |
| dpkg：缺包 | `no packages found matching cmake`、`ninja-build`、`libssl-dev`；整体rc=1/UNKNOWN | cmake双来源确认缺失；ninja-build不需，libssl-dev在LLAMA_OPENSSL=OFF下不需（BP-2/AC-7修订2），不照教程整串安装。该UNKNOWN指聚合块，不能将其余已装包也写成未知。 |
| dpkg：基础工具 | `build-essential 12.10ubuntu1`；`gcc`与`g++ 4:13.2.0-7ubuntu1`；`make 4.3-4.1build2`；`git 1:2.43.0-1ubuntu7.3`，均ii | 已装，无本轮补装/升级必要。make/git可执行版本命令未跑，只报dpkg包版本；U1剩余cmake走下述B-APT。 |
| dpkg：CUDA/TRT（U2） | `cuda-toolkit-13-2 13.2.1-1`；`tensorrt`、`libnvinfer-dev`、`libnvinfer-headers-dev`、`libnvinfer-plugin-dev`、`libnvonnxparsers-dev`、`python3-libnvinfer`、`python3-libnvinfer-dev`均`10.16.2.10-1+cuda13.2`，均ii | U2所列apt前置的包状态/版本已核。所选W不编译Edge源码、不需为它补TRT开发包；已有开发包也不证明绑定/插件/运行兼容，不切回S源码。 |
| dpkg：Python底座 | `python3-numpy 1:1.26.4+ds-6ubuntu1`；`python3-pip 24.0+dfsg-1ubuntu1.3`；`python3.12-venv 3.12.3-1ubuntu0.17`，均ii | 系统包版本已核，pip/venv不重装；不能用系统numpy 1.26.4满足W独立venv的numpy 2.2.6合同。 |
| trt_headers / sys_py_pkgs | NvInfer.h 437348 B、NvInferVersion.h 1840 B、NvOnnxParser.h 25865 B均位于/usr/include/aarch64-linux-gnu；目录/usr/lib/python3.12/dist-packages/tensorrt与/usr/lib/python3/dist-packages/numpy；rc=0 | 头文件/目录静态存在。系统TRT Python来源由python3-libnvinfer包及该目录定位；未读本轮模块版本/import，不由ls推兼容，未来W独立venv暴露系统TRT仍须已签装后核验。 |
| cuda_dirs | /usr/local/cuda指向/etc/alternatives/cuda；targets/sbsa-linux目录存在；targets/aarch64-linux原错不存在；rc=2/UNKNOWN | 不把三路径整体判不存在。固定tag CUDA≥13工具链使用sbsa-linux（BP-2），aarch64-linux替代目录缺失本路径不需补；实际头/库完整性、编译链接仍UNKNOWN，禁止造软链/补装绕过。 |
| sysvenv_cfg / sysvenv_numpy | cfg：home=/usr/bin、include-system-site-packages=true、version=3.12.3、executable=/usr/bin/python3.12；sysvenv本地site-packages/numpy*原错无匹配，rc=2/UNKNOWN | 本地numpy目录不存在不等于sysvenv运行缺numpy；系统包/目录已核。只读对照阶段A `-env.json.s1s2_system_stack_c.runtime_stack`及其raw指向的pip-list.txt（现算哈希匹配）：历史numpy1.26.4来自系统目录、TRT10.16.2.10来自系统绑定。本轮有效import/新venv兼容UNKNOWN，保留sysvenv不动；未来numpy2.2.6仅装W独立venv，不由本错误要求重装。 |
| py_sys / py_venv | 都为Python3.12.3（Aug31 2026、GCC13.3.0）；系统prefix=/usr；venv命令输出prefix/base_prefix=`/usr /usr`；rc=0 | 仅-I -S -B标准库读数。Python3.12的-S不运行site初始化，不能用这个prefix组合认定venv损坏/未启用；以cfg定位既有venv，不把本次命令称正常site下import验证。 |
| nproc / mem | nproc=6；free -b：RAM total=7849054208、used=999383040、free=4390739968、shared=2502656、buff/cache=2698194944、available=6849671168 B；rc=0 | 单时点字节读数，有效余量已核；不是五分钟空闲峰值/进程RSS/GPU统一内存/共驻峰值，不以available或总RAM证明7.0GiB描述线/模型可容。 |
| mem Swap / swap | free -b的Swap total/used/free均0 B；swapon --show --bytes在`### swap`与`### rc=0`之间**无输出行** | 零行是该成功命令未列活动swap，不是缺输出失败；与free一致，仅该时点活动swap=0。持久配置、zram策略及未来是否仍0 UNKNOWN，未读fstab/改swap，不补跑。 |
| df / du | /和用户home同为/dev/nvme0n1p1：1B-blocks=249326301184、Used=70855335936、Available=165731360768、Use%=30%；du -sb用户eng-jet=5163883873 B；rc=0 | 两df行同一文件系统，不相加；当前盘余量/项目占用已核，非llama构建/W解压/下载/临时件峰值，不据此签40GB或把du快照写回旧A账本。 |
| addr / route4 / route6 | 有线enP8p1s0 UP且192.168.8.0/24直连路由metric100；wlP1p1s0 UP，IPv4 default走该口metric600；另l4tbr0 default为linkdown、metric32766；IPv6 default经wlP1p1s0的link-local网关metric600。tailscale0也列出；docker/l4tbr/usb/can的DOWN或linkdown原文保留；rc=0 | 本次原件确实SSH成功，有线/无线/双栈路由存在；只读内核表不证明DNS/外网/下载端点可达，不将wl口视为资产取回许可。选定Mac取回后有线传板，不依赖板外网；不改地址/路由/SSH。 |

**缺项处置（具名操作唯一用户入口仍是「阶段B预检答复落实」§5 B-APT）。** 本路径必需但缺失的系统包仅cmake，版本最低3.18来自固定b11381 CUDA子目录（BP-2）；已装build-essential等复用。ninja-build、libssl-dev、CUDA旧aarch64-linux目录不需；W不取Edge源码/子模块，TRT dev已装不升级。用户尚未反馈安装结果，不能写“已装”或关闭U1；缺读数继续UNKNOWN，不请求重跑预检或追加SSH。

U3的llama精确归档字节/未读外联分支、U5的W固定平台逐文件元数据/传递闭集、U8的官方两件固定页身份/精确字节仍未核；U10采样规则和U11基准选择已定，但派生128件/隔离/609基准身份尚未在本轮重新核验；U12候选未冻结。U9产物峰值/U13实际兼容仍待未来已签有界实测；本次C2/云路径不执行。以上不要求先有成功实测，也不把缺假设输入的下载/安装/构建/模型额度拿来试错，当前相关维度0。

本次核清不消费新verdict，不重算S0–S2/SR或旧A账；S1/S2 STOP、SR5/5耗尽、补丁未上板、R1-5/6 OPEN、AC-7/8/9未运行、Overall REVIEW_PASSED/Lifecycle ACTIVE不变，不签DONE。已核环境事实供§5逐维度待签使用，推荐不授额。

## Contract conformance（核对表）

### C3@K1K3K4（2026-10-04，Acceptance）

**核对结论：携 AC-6 未满足主张、AC-14 附议缺口及预复核关注项，照交独立 `R2@K1K3K4`。** SUB:6 账载各维度未越界，新增失败均在两项重新具名例外内；这不等于全套通过。**本停点核对退回已用 1 次**，依 engineering-workflow §4/§5 与 workflow §4.3.3 不再退回，由复核裁决未决主张。本轮不新增/改写 AC、不定 finding 分级或依据值、不签独立 verdict、`DONE` 或新候选 `UNITY_NA` 附议。

**候选与读取范围。** 沿 `docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md`「K1K3K4全套SUB6：新候选停点全套一次、计账与停点自证」§6 运行时解析 BASE/CAND/PASSED/CODE；各具名主题唯一，CAND 触及交接文件、为 origin/main 祖先，BASE 与 ledger 基线一致。完整 BASE..CAND 为 38 路径（含期间治理/他人文档，不排除）；相对 R1 的 PASSED..CAND 完整增量为 18 路径，代码/测试仅 6 件：`tools/eng_jet/{assets,evidence,ledger,relay}.py` 与 `tests/test_eng_jet_{guards,relay}.py`。已重读该完整增量、AC-1…16 及修订、用户 SUB:6 授权、交接 §5–§8、R1 全轮及直接关联代码；BASE..CAND 的 Assets/controller/config diff 空，CODE..CAND 与 CODE..全套执行 started 提交的 tests/tools/controller/Assets/config/.gitignore diff 均空。候选不以本轮接受提交或当前 HEAD 替代，不手抄 SHA。

未变化的 S0/S1/S2/SR 与隔离证据继续按 R1 已核实的范围解读：env/assets/fastlayer/relay/vlm/quant-equivalence/coresidency 七份 JSON 相对 PASSED 逐字零 diff，不声称本轮重新上板或重算实测。ledger 去掉新增 envelope.sub6 与 dimensions.mac.sub6 后，完整旧 JSON 树与 PASSED 相等。新的纯参照以标准库只读解析全部 3,168 行，与原含标签来源的 a7 frame_id→sha256 投影逐项相等，每行恰两键且 sha 形状有效；未执行项目测试、模型或生成证据命令。

| AC | 核对结果 | 候选与合同/证据对照 |
|---|---|---|
| AC-1 | 满足 | `-env.json` checks/readings/tegrastats_idle 与 R1 §2 原核实一致，S0 PASS；修订 1 的非 root 查询与 journalctl 替代保留，新候选未增加环境/系统动作。 |
| AC-2 | 不满足 | S1 保持 STOP(FP16_BOX_DIVERGENCE)，不记步骤满足；`-fastlayer.json` S1 与报告 §2d 的两引擎身份、320 帧四分项、检测比对/差异清单等证据义务不变。修订 1…7 与 α 续跑读法沿 R1，不把旧读数当补丁后实测。 |
| AC-3 | 不满足 | S2 保持 STOP(FRAME_DROP)，不记步骤满足；`-fastlayer.json` S2/报告 §2e 六格与频温/丢帧证据义务不变；α′只放行原范围 SR。 |
| AC-4 | 满足 | `-relay.json` forward/contract_readings_full_suite.ac4_rev2 原读数不改；`relay.analyze` 去截断并给 link_events_total，`evidence._forward_section/contract_readings_relay` 传递总数。修订 3 的可能截断→None 由 `AnalyzeLinkEventsFull` 与 `ContractSyncFullSuite::test_link_event_split_reads_full_list_and_refuses_truncated` 对准，未由 None 推出 0。 |
| AC-5 | 满足 | 描述性证据；`-relay.json` return 与 ac5_rev1 分母、init 来源沿 R1，不变；真实回程 n=29，不推出持续跟踪/Unity 门通过。补丁未改应答器、初始化或控制器。 |
| AC-6 | 不满足 | 历史 `-relay.json` disconnect 的两次断链/存活/写桥/缺口/回稳记录齐，修订 2 缺 disconnects 判假已落实。新 `BoardRelay.adopt_link/return_once` 对回程去重的跨连接状态缺少共同同步：旧连接发送返回后、写 digest 前可被新连接 clear，随后旧发送写回 digest，使新连接跳过当前文件；与 §3.2 重连只发当前版本的义务存在偏差主张（C3-P1，交复核核实）。顺序 FakeLink 回归未覆盖该交错；f4 为补丁前历史实测。 |
| AC-7 | 不满足 | `-vlm.json` NOT_RUN(阶段 B 信封未签)，无板上 VLM 数据；阶段 B 仍未签，本轮不答其题目。 |
| AC-8 | 不满足 | `-quant-equivalence.json` 同上，无 609 行板端量化等价证据。 |
| AC-9 | 不满足 | `-coresidency.json` 同上，无共驻证据。 |
| AC-10 | 满足 | 仅账载范围/额度核对。修订 9：SUB:6 全套1/1、det-assoc CPU2/2、NanoTrack尝试2上界/读权重0、CSRT尝试2上界/实例0、YOLOE/DINOv2/其他0、各60帧零模型回放2/2、outputs增量3853 B<100000 B、总量<2 GB、墙钟349 s≤900 s、pip/下载/上板/SR/MPS/重跑0。两条事件与原事件文件逐项一致，旧SUB:2/SUB:5计数及mac.models不回退/重复扣账；Assets/controller/config diff空。修订10仅同名同类Carrier失败，未知/未执行断言保留。`within`为数量比较，SUB:6手工块与外联/设备非动态测量限制见下。 |
| AC-11 | 满足 | 原 `-assets.json` 资产使用前核对与阶段B NOT_USED沿R1；修订1允许完整a7纯sha参照。新增 `-a7-frame-sha256.jsonl.gz` 全部3168行只含frame_id/sha256，与原投影逐项相等；`assets.frame_reference/load_pure_reference/verify_frames` 与 `PureFrameReference` 对准；历史参照字段不回填，不扩上板/回放额度。 |
| AC-12 | 满足 | 原 `-assets.json` board_manifest/protected_roots_zero_write及修订1…4具名分列沿R1；原ac12_clean=false/违规列表保留。新增参照无标签字段、BUNDLE_FILES未改，未进控制器/到板负载；原含标签来源仅投影sha的历史事实仍披露。不把路径分列泛化为内容豁免。 |
| AC-13 | 满足 | 报告§2i/§6与新日志/ledger相符；逐名逐类型比较37条失败与CPU1相同，完整失败详情段逐字相同，R7已有7/未出现18/新增30=Carrier1+scene00629。AC-10修订10/AC-13修订4同名同类边界内，例外外新增0；不称失败通过、18未出现不称修复，skip56仅聚合。旧S1/S2 STOP、SR PASS与现状/历史分列保持，无新Jetson主张。 |
| AC-14 | 证据缺失 | 交接SUB6§1–§2/§6有本机、时间与执行版本解析，代码一致性已核；零Play/Unity零改动理由成立。R1§4附议及passed_candidate仅覆盖原候选，新候选须R2另行附议，尚缺；接受角色不代签。 |
| AC-15 | 满足 | `-ledger.json` pending_user/stage_b旧字段未变：h/n answered，i…m unanswered且对应动作0，阶段B signed=false/all_dimensions=0。A收口:1与线B阶段B:1–8本轮不裁定。 |
| AC-16 | 满足 | `-env.json` s2_system_stack_e.env.ac16/sr_system_stack_f.ac16原环境与外部写入核查沿R1；补丁与SUB6零上板，未新增板上Python进程或改重定向。 |

### 停点自证与 SUB:6 例外核对

交接SUB6§7四项作为进入独立复核的主张：①范围冻结、IR-26/27已裁定且执行/候选代码相同；②82例focused/一次2146例全套已有证据，37条失败详情与CPU1相同，只有两项重新具名例外，例外外新增0，第2项可按授权边界评估，**不签全套通过**；③零Unity，新候选UNITY_NA待R2；④候选已推送、解析/范围/风险齐。C3发现的代码主张随候选交R2，不另退回、不替复核判REVIEW_BLOCKED或verdict。

Carrier仍为同一首例同一断言失败，不一致索引2/4/5/6/8/12/17/18/19/20相同；仅索引2对应frame3的首个宽差已知，其余9条形态未知，比较后confidence_source/观测桥字段集/临时目录外写入断言未执行，两例不经真实工厂。scene006仍29条（25 FAIL+4 ERROR），逐名/类型/详情一致；静态缺权重归因与后续行为未验证同时保留。R1-5/6两条OPEN债不销账。

SUB:6全套/det-assoc/回放耗尽；NanoTrack/CSRT为尝试数静态上界，回放为保守计账，未插桩/无逐名skip。主树outputs全量1139567380 B是全套结束后、第二条记账事件前的快照；再加该事件1460 B仍<2 GB，eng-jet计账后增量3853 B。`tools/eng_jet/ledger.py`无SUB:6维度，现有JSON块手工追加且未运行build，重跑build会丢块；新增R1-4常量basis代码也不表示历史JSON已被重建。`within`与日志无下载行不证明设备/外联/系统设置动态测量为0；DNS/usage外联未监测的限制保留。

### 后续复核范围与未决关注项

交 Review 的 `R2@K1K3K4`：按交接SUB6§6解析CAND与复核文件最近passed_candidate/上一轮round_candidate，两基线当前同源R1；PASSED..CAND全量增量18路径，PLAY_GOVERNING非空（上述6代码/测试件），有开轮资格。原BASE..CAND完整38路径清单仍按运行时解析核实，不以实现声明或线B/治理名称排除；未变动部分沿既有R1，按workflow§4.4的增量阻断边界处理。复核在同名 `docs/reviews/P1-ENG-JET-001.md`记录R2，核对以下待核实主张并对新候选另议UNITY_NA；接受角色不预定分级/依据/结果。

- **C3-P1（AC-6/§3.2）**：`tools/eng_jet/relay.py::BoardRelay.return_once` 的link快照与send后 `_last_return[name]=digest` 均不持 `_link_lock`；`adopt_link`只在换连接/clear时持该锁。旧send成功→线程切换→adopt_link关闭旧连接并clear→旧return_once写digest→新连接同digest被跳过，是读码可达交错主张。`Link.send`自己的锁不覆盖adopt_link/全局digest写回；`tests/test_eng_jet_relay.py::BoardRelayInProcess::test_reconnect_resends_current_return_version`只有顺序调用，不能证明此边界闭合。请R2在零模型范围核实，不以补丁前f4读数或focused总数替代。
- **C3-P2（失败路径）**：`tools/eng_jet/evidence.py::disconnect_pass`声称四进程退出/三方stop，却对 `exit_codes.values()` 与 `process_stops.values()`用all；空/缺项字典可能空真，`DisconnectPass::test_each_condition_falsifies`只覆盖存在键的坏值及缺disconnects。`relay_doc_f/sr_round_f`正常生产路径生成具名键，IR-27不声称任意畸形输入都判假；请复核核实该函数的可达输入/边界，不由本轮扩AC或自定finding等级。
- **C3-P3（证据持续性）**：`tools/eng_jet/ledger.py::build`没有SUB:6聚合，`-ledger.json`的envelope.sub6/dimensions.mac.sub6为手工追加；已用两事件属于note，重建会丢块。请核实披露与原计数不覆盖、不重复扣账的主张，R1-4新增常量标注仅对今后输出生效；不得自行重建覆盖当前账本。
- 例外边界、未知/未执行断言、外联未监测、scene006静态归因、IR-20告警、真实回程n=29与补丁未上板限制照旧携带。零模型focused由复核按现行纪律安排；若需任何真实模型/回放/全套/SR/上板重跑，须另申请，不能借旧额度或自动扩SUB:6。

## 决策记录

### 阶段B预检答复落实（2026-10-04，CLARIFY）

登记轮次 `阶段B预检答复落实`；Dispatch-Id `P1-ENG-JET-001-阶段B预检答复落实-20261004T061709Z-3870`；Acceptance，本轮只落实答复、裁预检轨道与交接，不执行预检。依据 `docs/authorizations.md`「2026-10-04 P1-ENG-JET-001 — 用户答复「阶段B准备审核」§5：选择类全部按推荐、授权一次只读预检，推进至云量化之前（不含云；supervisor 会话代录）」授权范围(1)–(5)。原AC/决策/推荐保留；以下追加解释只作用于未来阶段B。§5已答选择不再待决；B-CLOUD/B-CLOUDDEP未答，不代选。除一次board预检外未授任何额度，B-SIGN只确定核清后逐维度签发的方法。

#### 1. 选择类落实与追加 AC 修订

| 编号 | 现行合同与归因 | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 16 | CLARIFY（解释修订15、§5；B-PRECHECK）：仅授权§2所定Mac mini→Jetson有线board预检一次、全程≤300 s、无重试；输出只落Mac，接受SSH/PAM/登录日志/wireplumber等附带写入，不声称板端绝对零写。预检独立计次，不借A余量；不含安装/下载/传输资产/模型/回放。 | cmd: 「阶段B补写核清」§3 board版；artifact: 本节§2–3及上述账本(1)(5) | K1K3K4 | 2026-10-04 |
| AC-10 修订 17 | CLARIFY（解释修订13–15、§5；B-APT/B-DLLOC/B-SIGN及终点）：缺项经预检核清后仅用户本人装具名必需缺包并反馈版本，代理sudo/apt0；W不需Edge源码/子模块/TRT dev构建，llama仍需cmake/build-essential，W仍需系统TRT绑定/venv，不按教程整串升级。取回地点选Mac mini，拟取llama b11381归档1、官方GGUF两件、板W轮子及传递包，核身份后有线传板；不依赖板外网/git。下载前固定来源/身份/精确字节与闭集；未核维度不申请，数值由用户另签。B-CLOUD/B-CLOUDDEP未答，本次云租用/先导/依赖/合并/转换/量化/校准/云传输全部0，I-A未来路线不改，本次范围按§4。 | artifact: 上述账本(2)–(4)、本节§4–5；准备审核§3/5、补写核清§1–2 | K1K3K4 | 2026-10-04 |
| AC-8 修订 4 | CLARIFY（解释修订3、AC-12；B-CALIB）：选本域train派生128张、batch1、不截断、固定tag Python API本地(image,question)生成器；先依准备补写BP-4按sha去重/最小sample_id及固定排序，再按准备审核§5推荐排除eval/select-eval/smoke25张、a7预热/前320帧以及与保护集相连的既有近重复原子组。无组关系时用同family/station_key且frame_index距任一保护帧≤30的代理排除；完成上述排除后从剩余固定排序取前128，缺字段/不足128回用户，不补保护帧，不称近重复完全隔离。Mac仅在另签加工额度后生成剥字段派生件；约6MB是估算、不是传输额度；本次不上传、不做AWQ前向、不用HF缺省数据集。 | artifact: 上述账本(2)、准备审核§5 B-CALIB、准备补写BP-4、未来-assets.json | K1K3K4 | 2026-10-04 |
| AC-8 修订 5 | CLARIFY（解释修订2、AC-11；B-S4A）：选复用已复核SFT作业A609行base bf16原预测，由zero-shot-v2/eval摘要运行时核逐行身份、prompt/grid/解析；官方base只对base bf16，G5取其原计数，不借C2的21/100。Mac零新基准推理；5090 HF与板端运行时/转换/量化差异混合披露，不作因果分解。609次板端推理仍须另签，基准未核或份额0时不运行。 | artifact: 上述账本(2)、准备审核§2/5 B-S4A、未来-quant-equivalence.json | K1K3K4 | 2026-10-04 |
| AC-7 修订 4 | CLARIFY（解释修订3，关联AC-8/9；B-CACHE）：用户具名接受v0.11.0视觉编码缓存例外，文本KV仍关。未来S3/S5每个计时段前重启常驻服务清视觉缓存，启动/加载单列并计额度，每段只加载一次；首见25/共驻180互异帧单图请求不得有命中INFO，原始INFO逐请求绑定。重复7行预期命中单列，保留0.5倍比值并标CACHE_SUSPECT，不自动作废无命中的首见统计。S4保持609行、披露重复帧缓存影响、不删行。INFO或实际预处理出口不足不认证新帧时延，token=300仍须实际grid/merge证据；不换低层入口/逐请求CLI。例外已答不再默认3c不执行，但加载/重启/查询/缓存磁盘仍0，C2服务本次因缺云产物不执行。 | artifact: 上述账本(2)、准备审核§5 B-CACHE、未来-vlm.json/-coresidency.json | K1K3K4 | 2026-10-04 |
| AC-14 修订 3 | CLARIFY（解释修订1–2、AC-10/13；B-EXC）：用户为B1/B2各具名重新沿用Carrier CPU失败、9处未知、后置断言未执行和scene006新增29条缺权重静态归因，仅原同名同类；原三授权来源及枚举见准备补写BP-5，不把失败当通过，其他新增失败阻断，独立复核仍可阻断。例外选择已生效、测试额度未签；B1/B2停点及全套加载/回放仍按§5逐维度另签，不以旧SUB:6或例外替授额度。 | artifact: 上述账本(2)、准备补写BP-5、未来-K1K3K4-handoff.md | K1K3K4 | 2026-10-04 |
| AC-9 修订 3 | CLARIFY（解释修订1–2；B-PRESSURE）：15 Hz额外压力档本次0、暂不追加；未来先取得已定5 Hz运行合同读数，首次init冷启动单列。追加压力需另签墙钟/查询/样本且仅描述、不改5 Hz门；本次S5不执行。 | artifact: 上述账本(2)、阶段B答复落实§1–2、未来-coresidency.json | K1K3K4 | 2026-10-04 |
| AC-13 修订 7 | CLARIFY（解释修订6、AC-7/8/9；B-LINES与14个B-STOP-*）：用户已确认保持S3时延/4.6GB、S4 3pp、S5 1.3倍/7.0GiB的描述性分类，数值出处/比较基线/运行条件沿「阶段B答复落实」§2，不将公开/移植线超线转STOP；改变须目标真实试读与新裁定。逐码缺省处置现按下表生效，只有真实合同触发才按处置停止；继续已签步骤不授新额度。 | artifact: 上述账本(2)、本节逐码表、阶段B答复落实§2、未来-report.md | K1K3K4 | 2026-10-04 |

AC-13修订7的逐码闭集（对应§5的14个B-STOP-*，不改变原触发条件）：

| 原因码 | 已确认的阶段B缺省处置 |
|---|---|
| NOT_SUPER | 设备合同不符：停全部B后续回用户，不自行重刷。 |
| FREQ_CAPPED | 实际环境不符报STOP：停全部回用户；纯厂商频率参照偏离只描述、继续已签步骤，不锁频。 |
| NOT_HEADLESS | 停全部后续回用户，不isolate/改默认target。 |
| POWER_MODE_NOT_MAXN_SUPER | 停全部后续回用户，不改功耗模式。 |
| IDLE_RAM_OVER | 只超旧1.2GB公开参照：记录并继续已签步骤；实际资源不可用报STOP：停全部回用户。 |
| LATENCY_OVER | 合同失败确已报STOP：停全部回用户；移植速度超线只描述、不触发此码，不换基准。 |
| FP16_BOX_DIVERGENCE | 新STOP停全部回用户；历史S1仅依α/N-A继承，不改旧STOP、不授权新偏差续跑。 |
| THERMAL_THROTTLE | 确证热降频：停全部回用户；动态频率不冒充热降频，不锁频/改散热。 |
| FRAME_DROP | 新STOP停全部回用户；α′不覆盖新STOP，S5稳态失败仍用CORESIDENCY_OVER，不改S2。 |
| RELAY_INTEGRITY | 停全部回用户；SR追加0，补丁未上板、真实重连未验证，不重跑SR。 |
| KERNEL_PARAM_REQUIRED | 停全部后续（包括其他路径）回用户；不改cma/系统、不换栈规避。 |
| VLM_OVER_LINE | 所选路径全部合同不可用：停S4/S5回用户；单路径PATH_UNAVAILABLE沿原合同继续3c，速度/4.6GB描述超线不触发。 |
| QUANT_NOT_EQUIVALENT | G5/解析合同失败：停剩余S4/S5回用户，不改配方；3pp描述超线不触发。 |
| CORESIDENCY_OVER | 快层公式/稳态连续丢帧/NvMap-OOM/swap合同失败：停全部追加尝试回用户，不换产物/帧率、不加压力档；1.3倍/7GiB描述超线不触发。 |

归因：8条AC修订均来自本次账本用户答复、解释既有条款；新增AC=0，非C轮读码增项，不改历史候选或verdict。S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN不变，AC-7/8/9仍未运行；Overall REVIEW_PASSED / Lifecycle ACTIVE只覆盖阶段A通过候选，不签DONE。

#### 2. 单次 board 预检执行合同

- 执行角色：下一派发Implementation；控制/落盘机器为Mac mini主树根，读取机器为用户既有Jetson Orin Nano 8GB Super（系统栈B、有线）。唯一发令是「阶段B补写核清」§3完整代码块的 `python3 -I -S -B - board` 版本；不改参数、不跑cloud模板/旧RP-1，不追加第二次登录或探测命令，不改SSH键/配置。目标从既有relay证据运行时解析，不手抄地址。板端普通用户，无sudo/交互/第三方import/模型/回放/安装/下载/编译/服务重启/系统改动。
- 全程≤300s（包含Mac取Host/目录/ssh/记录），单项与全程超时及杀本次SSH进程组/远端timeout收尾按该块；超时后不重连核存活。执行前确认共享槽位空闲，若FRAME正在Play/采集，等待该次操作退出槽位，不能改其交接或抢槽；等待不是预检运行计时。
- 计次上限1、重试0；从首次启动完整board块即计1（本机前置/认证/网络/缺工具/超时失败也计），不能因SSH未成功退回计数。执行前在本项预检证据记录“已开始，1/1”，收工补实际结局；若已有本次started记录或已计尝试则只整理原输出，不再次执行。不得用旧阶段A余额或其他信封再登录。
- Mac原始输出仅在命令运行时生成的 `outputs/eng-jet/P1-ENG-JET-001/stageb-boardprecheck-<UTC>/`，这只是原始输出目录、不是正式run ID。保留started_utc/ended_utc/elapsed_s、precheck.stdout/precheck.stderr/precheck.rc及有则local-error.txt，不手抄实际目录名进合同。板端不写本项工件，SSH/PAM/登录日志/wireplumber/atime附带写入已获用户接受；不删历史缓存。元数据输出不属于资产传输额度，禁止借本次SSH搬模型/代码/帧。
- 记录落点：Implementation在 `docs/evidence/P1-ENG-JET-001-stageb-boardprecheck.md` 记执行机器、唯一命令出处、开始/结束、实际原始输出目录指针、计次1/1与返回码/错误/逐项UNKNOWN，以及执行时git状态凭据（实际值写证据，不抄回手维护合同）。不重建ledger，不跑实现测试；本轮没有B1/B2消费，不给预检PASS或性能结论。主树runtime/数据根零写入。
- 失败处置：整体非0或本机前置失败保留错误；单项超时立即停止、未执行项UNKNOWN；普通缺包/权限错误仅按唯一块在同一次扫描内继续，不能另补命令。rc=0也须逐字段核MISSING/缺metadata，不能推出完整闭集。执行收工交Acceptance核清；失败/缺读数不自动sudo、重试或申请后续运行。

#### 3. 轨道裁定与读数回来后的核清路径

**裁定Consuming=no。** AGENTS.md「执行轨道纪律」、workflow§7规则0和engineering§8以创建/消耗scenario/session/run ID、Play或API预算定义消耗性交接。本次只读取系统事实、Mac保存文本，以上三类均0、GPU模型工作0；300s有界硬件访问虽须独立授权（engineering§9），不因SSH附带写入或输出UTC目录变成正式ID/Play/API消费。授权账本(1)已给这一次访问，因此现行轨道可执行，无须破例。

当前FRAME是唯一yes交接、JET为一条no交接，1+2上限内；本预检与FRAME交接可以并存、无需等待其消耗轨道释放。实际执行遵守engineering§8单写者与现有共享槽位互斥：supervisor串派写仓库角色，FRAME正在使用共享槽位时等空闲后再启动。B:8/AC-10修订13明确针对租云执行等待FRAME自身释放，本次不租云且属零消耗，不是撤销B:8；未来云仍等待释放，不改FRAME交接、不引用10-03已结束的并行破例。本裁定不提前为后续板运行或下载作并发放行。

Implementation只做§2一次预检、保存证据后立即交Acceptance，不顺带下载/装包/模型/构建。Acceptance随后将原读数按engineering§9写入本提案§8「只读试读」，逐项核U1/U2/工具链/glibc/系统TRT绑定的静态来源、RAM/swap/盘/路由；禁止由路径存在推断import/运行兼容。缺项区分“不需要”与“必需但缺失”，给B-APT具名用户操作及版本反馈要求；缺读数保留UNKNOWN，不要求代理重试。另核Mac静态包/模型来源和字节、校准隔离/基准、候选消费清单。只有核清的子范围交§5用户签数字，未知0；不能把返回0当B-SIGN已签。既有A证据/计数不重算，U9/U13在未来已签有界实测再核、U12在候选冻结再核。

#### 4. “做到云量化之前”的步骤边界

本次推进范围为**云前独立子范围**，不是阶段B整包授权，更不是VLM训练授权。以下“范围内”只表示可准备/在另签额度且相关消费前代码停点C/R通过后执行，当前下一派发唯一非零许可仍是§2预检：

| 步骤 | 本次终点内 / 不在本次范围 |
|---|---|
| 环境与合同 | 范围内：单次board预检；接受核清；缺包由用户本人具名安装/反馈；Mac静态闭集、资产与预算准备。不能以预检额度安装或再上板。 |
| Mac云前准备 | 范围内：另签后取llama归档/官方GGUF两件/板W与闭集轮子、核sha/来源、剥字段盲材料、有线传板、在Mac准备128张train校准派生件与复用base bf16的609原预测、评分；云上传0，Mac合并/转换/量化/基准推理0。 |
| 板端准备 | 范围内：另签后离线装闭集W/独立venv（不改sysvenv numpy）、构建llama-server与已复核的本项云前线束部署；不取Edge源码/子模块。旧R1补丁不得借预检上板，具体代码束与次数须在后续合同/额度核清，仍如实记此前未上板。 |
| 不依赖云的官方base路径 | 范围内：具名另签后官方base 3b GGUF+F16 mmproj的3预热/32行冒烟、token/解析/缓存核验；可在该路径合同有效且609查询另签后做官方base S4-a并在Mac对所选base bf16评分。保持原3b路径失败处置，不把“继续3c”解释为本次能绕过云边界；此时只能记录3c未执行并交接受/用户。 |
| 云及C2量化路径 | 不在范围：云控制台/租用/先导SSH/依赖安装/云盘或流量、C2合并、GGUF转换/量化与自产mmproj、AWQ校准前向/量化；不改到Mac或其他机器绕过终点。B-CLOUD/B-CLOUDDEP未答、对应维度0。 |
| C2板端与共驻 | 不在范围：C2 GGUF/AWQ传板、3c检查点首建LLM/visual及加载/缓存重启、C2 S3/S4两路与S5共驻；缺云产物不虚构满足，不借官方base替代C2跑S5。B-CACHE已定只是未来合同，不授这些动作。 |
| 历史或额外步骤 | S0–S2/SR不重跑、3a/J-A不做、15Hz额外压力档0、训练/Play/正式ID/API/发布0；停止于上述云前子范围后交用户，不自动恢复云。 |

B1消费前代码与B2消费后证据仍按AC-14修订1–3分停点，不将A候选通过延及B。云前子范围可先形成相称候选，但不得把云入口/其他尚未实现范围写成B1整体完成；含不可重跑消费的依赖代码须先C/R。若拆分导致候选数或消费上界改变，先回接受核范围并回用户签额度，不从原“两候选”自动增支。

#### 5. needs_user（阶段B预检答复落实，现行事实/额度唯一入口）

**阶段B传板核清后（2026-10-04）：34件已传板并核清。** 31轮子与用户自下2件GGUF均已取回并核清；原B-SIGN-DOWNLOAD批次与GGUF停止归因保持，见「阶段B下载核清」；两件用户本人操作及字节/sha逐项比对见「阶段B用户GGUF核清」。用户决定自行下载、不另签代理重取，B-LOCAL-ALLOW-DOWNLOAD/B-SIGN-GGUF-RETRY不再待答，代理新尝试0；原计次/未用字节不转用。已答选择、GGUF事实、cmake、METADATA/源码及既有放行不重问。TX-ASSETS一次批次已执行并核清：34件各1次、重试0、整批墙钟226.7 s≤1 h、板新增占用2,481,704,960 B≤5 GB，逐件板端stat/sha256sum与源期望双符合，见「阶段B传板核清」；板上独占目录 `~/eng-jet/stageb-transfer-20261004T225001Z/` 的34件（W31/G2/S1）为后续维度已核输入。BUILD-LLAMA已用1/1并核清，见「阶段B构建核清」；安装/部署/运行等其他未签维度0、不含云；依engineering§9，其他依赖未核事实的维度保持0，核齐后才交用户具名签发。

**出处与已完成事实（只读保留，不是新授权）：**

- **G（B-FACTS-GGUF）**：`docs/authorizations.md`「2026-10-04 P1-ENG-JET-001 — 用户提供 B-FACTS-GGUF：两件 GGUF 精确字节与 LFS sha256（supervisor 会话代录）」的“用户提供的核查结果”：Qwen3VL-2B-Instruct-Q4_K_M.gguf **1,107,409,952 B**；mmproj-Qwen3VL-2B-Instruct-F16.gguf **819,394,848 B**；合计 **1,926,804,800 B**。身份来自 `docs/evidence/P1-ENG-JET-001-stageb-metadata.json` META-GGUF；revision/页面SHA/Xet值运行时解析，不手抄。此出处足以形成本次预算推荐，不称远端整数size已独立核验；用户本人取回的两件现算字节/sha与该账本期望及用户反馈均符合，见「阶段B用户GGUF核清」；只复用已核件，不重取，内容改变或不符不得使用。
- **W（B-METADATA-VERIFY）**：同名metadata.json META-DEP的31个选定轮子size重加 **516,980,330 B**（W本体447,070,745 B+其他30件69,909,585 B）；pin/filename/URL/sha运行时解析。静态声明闭集（含5件Dynamic）裁定见「阶段B核验核清」§1/AC-10修订23与 `docs/evidence/P1-ENG-JET-001-stageb-metadata-verify.md` §3–4及同名JSON；本次下载31件完整实体已取回，接受现算字节/sha与固定元数据双符合，见「阶段B下载核清」§1及同名stageb-download.json objects/binding；本机路径由该JSON解析。未认证隐式运行依赖、安装或板端兼容。
- **S（B-FACTS-LLAMA）**：已保留源码归档 **37,831,966 B**，同sha副本/完整commit响应链裁定见「阶段B核验核清」§2与 `docs/evidence/P1-ENG-JET-001-stageb-source-archive.md` §1–3及同名JSON archive/binding_chain；新增源码下载0。Content-Disposition未捕获仅限制辅助文件名，未内部验commit；自动归档可能改变，只复用保留副本，使用/构建/传板仍须另签。
- **E（环境/历史核验）**：提案§8.2原预检读数、账本cmake 3.28.3及cmake/cmake-data 3.28.3-1build7/ii反馈、元数据授权落实§1。U1必需cmake缺项闭合，不证构建成功/其他包未变化。一次预检1/1、META-BATCH-1用61/86（LLAMA2+GGUF4+DEP55）/31项目，余25次/9项目作废；META-VERIFY用31/31 GET、433,453 B；SRC-ARCHIVE用1/1尝试、2/2 GET。已完成本机域名/目录脚本放行不再待答；出处为原执行md/JSON与supervisor-dispatch.jsonl。原账/原件不改不删，核验执行方法偏差保留见「阶段B核验核清」§3。

**字节重算（单位均B，文件有效载荷，不含网络封装/协议开销）：** 原代理下载批次实际W31为516,980,330、G正文0，原账不变；用户自下G2另计1,926,804,800，不计入代理下载额度。Mac现已保留并核清W31+G2+S1共34件 **2,481,617,096**，下一步原文件输入新增下载推荐0。资产单程传板推荐34件 **≤2,481,617,096**；每端一份输入为2,481,617,096，两端共4,963,234,192，相对当前Mac完整既存件未来仅板输入新增2,481,617,096，不重算Mac已存件。板既有A/wheels/其他占用不归零；输入不是磁盘峰值或整项传输总量，代码/盲材料/帧/回传日志未核，完整双向传输仍UNKNOWN/0。

| needs_user / 维度（下载/TX-ASSETS/BUILD-LLAMA已签；其他未签0） | 已签上限或具名推荐 / 理由 | 重试 | 出处 | 当前状态 / 仍缺前提 |
|---|---|---|---|---|
| B-SIGN-DOWNLOAD / DL-WHEELS | 原已签：31件各1次、累计≤516,980,330 B；固定文件 | 0 | W；原下载账本(a)；「阶段B下载核清」§1 | 已取回31/31，现算字节/内容sha双符合；累计516,980,330 B；原尝试已用，不重取 |
| B-SIGN-DOWNLOAD / DL-GGUF | 原代理2件各1次已用尽；用户自下2件，不计代理额度，新尝试0 | 0 | G；账本用户自行下载/反馈两条；「阶段B用户GGUF核清」 | 用户自下且已核清：字节/LFS sha与期望及用户读数双符合；原批302停止/正文0/计次不变；不符不得使用 |
| B-SIGN-DOWNLOAD / DL-SOURCE | 新增0件/0 B；复用保留副本，不重取 | 0 | S；同下载账本(a)；TX-ASSETS账本(a) | 源码不重下载；传板与BUILD-LLAMA已执行并核清，构建1/1用尽；产物运行/其他使用0 |
| B-SIGN-DOWNLOAD / DL-TOTAL | 原已签：33件≤2,443,785,130 B、整批≤1 h、本次Mac新增占用≤10 GB；分额共账 | 0 | 原下载账本(a)–(e)；「阶段B下载核清」§1 | 一次批次收束：成功31/尝试33，GET33/35、正文516,980,330 B；计时/占用均在限内，其他维度0 |
| B-LOCAL-ALLOW-DOWNLOAD / 本机前提 | 用户已选择本人自行下载，无需新增代理主机放行 | 0 | 账本用户自行下载(b)；「阶段B用户GGUF核清」 | 不再待答；不改本机设置或原合同候选闭集 |
| B-SIGN-GGUF-RETRY / GGUF另取 | 用户已决定不另签代理重取；推荐只复用已核清G2，新尝试0 | 0 | 账本用户自行下载(b)；「阶段B用户GGUF核清」 | 不再待答；旧尝试不回退，用户操作不计代理额度 |
| B-SIGN-TRANSFER / TX-WHEELS | 已签Mac→板单程31件/≤516,980,330 B，各1次；复用W固定原文件 | 0 | W、下载核清§1、TX-ASSETS账本(a)–(e)、「阶段B传板核清」 | 已传并核清31/31：板端字节/sha与源期望双符合、重试0、占用/墙钟在限内；板上独占目录已核输入 |
| B-SIGN-TRANSFER / TX-GGUF | 已签Mac→板单程2件/≤1,926,804,800 B，各1次；复用用户自下已核G2 | 0 | G、用户GGUF核清、TX-ASSETS账本(a)–(e)、「阶段B传板核清」 | 已传并核清2/2：同上双符合；不新增代理下载尝试 |
| B-SIGN-TRANSFER / TX-SOURCE | 已签Mac→板单程1件/≤37,831,966 B，1次；仅保留同sha副本 | 0 | S、TX-ASSETS账本(a)–(e)、「阶段B传板核清」 | 已传并核清1/1：同上双符合；后续解压/构建已由BUILD-LLAMA独立计账核清 |
| B-SIGN-TRANSFER / TX-ASSETS | 已签上述单程34件/≤2,481,617,096 B；各1次、分额共账，整批≤1 h、板新增占用≤5 GB | 0 | W+G+S、TX-ASSETS账本(a)–(e)、传板授权落实§1–5、「阶段B传板核清」 | 已传并核清34/34：墙钟226.7 s/3,600、板新增2,481,704,960 B/5,000,000,000、重试0；仅资产落盘、无代码/材料/日志 |
| B-SIGN-TRANSFER / TX-CODE-DATA-LOGS / TX-TOTAL | 冻结代码束、盲材料/帧、回传日志各精确B及次数UNKNOWN；完整双向总B UNKNOWN，推荐保持0 | 0 | BP-4、§4云前边界、§8.2；TX-ASSETS只算34件资产 | 代码束/盲材料未冻结、数据基准/隔离未复证、日志尚无实测体积；不以旧≤10GB补未知 |
| B-SIGN-STORAGE-TIME / INPUT-MAC | Mac已存34件输入2,481,617,096 B；原文件新增下载推荐0 | 0 | W+G+S；上式；用户GGUF核清/下载核清 | 输入完整已核；完整加工/评分峰值UNKNOWN/0；旧A/元数据另列，用户自下不套代理下载封顶 |
| B-SIGN-STORAGE-TIME / INPUT-BOARD / INPUT-BOTH | 已签传板输入34件/≤2,481,617,096 B；两端各一份输入投影4,963,234,192 B；Mac既存件不重算 | 0 | W+G+S、TX-ASSETS账本(a)(c)、传板授权落实§2–4、「阶段B传板核清」 | 板端输入34件已落独占目录并核清2,481,617,096 B（du分配2,481,704,960 B）；旧板占用不扣回；构建峰值见「阶段B构建核清」；安装/完整加工峰值UNKNOWN/0 |
| B-SIGN-STORAGE-TIME / DISK-PEAK-MAC / DISK-PEAK-BOARD | 下载/传板/构建历史信封不变；INSTALL-W安装子范围接受推荐板新增≤5,000,000,000 B（venv/解压/缓存/暂存/日志/失败保留件），未签；其他峰值UNKNOWN/0 | 0 | 原下载/TX-ASSETS/BUILD-LLAMA账本、「阶段B传板核清」「阶段B构建核清」「阶段B安装合同准备」§3–4 | 安装预算由W31 ZIP静态尺寸及受控暂存/余量推导，合同已准备，待用户签数值；实际瞬时峰值UNKNOWN，完整加工/运行峰值未核、不申请 |
| B-SIGN-STORAGE-TIME / TIME-MAC / TIME-BOARD | 下载/传板/构建历史信封不变；INSTALL-W安装子范围接受推荐整批≤3,600 s，未签；其余加工/部署/加载/查询墙钟UNKNOWN/0 | 0 | 原下载/TX-ASSETS/BUILD-LLAMA账本、「阶段B传板核清」「阶段B构建核清」「阶段B安装合同准备」§3–4 | 安装合同已准备，待用户签数值；含前置/sha/venv/31次pip/静态核对/监测与收尾的强制截止，非成功时长预测；其他墙钟未核、不申请 |
| B-SIGN-INSTALL-BUILD / INSTALL-W | 接受推荐固定31个distribution离线逐文件安装1批、各至多1次、重试0；系统TRT复用，numpy2.2.6仅独立W环境，sysvenv不重装 | 0 | W、「阶段B下载核清」§1、「阶段B传板核清」、E、BP-2、「阶段B安装合同准备」§1–7 | 合同已准备，待用户签数值；已核输入与系统底座，不需额外板访问准备；未来信封内前置失败即停；运行兼容UNKNOWN且不在本次安装范围，不以安装代替实测 |
| B-SIGN-INSTALL-BUILD / BUILD-LLAMA | 已签1次/重试0、两批合计≤7,200 s/板新增≤5 GB；固定参数沿构建合同 | 0 | BUILD-LLAMA账本(a)–(f)、AC-10修订28–29、「阶段B构建核清」§1–3 | 已执行并核清：1/1用尽，两批1,746.989 s、采样峰值411,414,528 B；只证可构建，产物未运行，外联归属/瞬时峰值UNKNOWN；剩余时间/磁盘不转用 |
| B-SIGN-INSTALL-BUILD / DEPLOY-CODE | 冻结代码束次数/精确B UNKNOWN，推荐保持0；补丁未上板 | 0 | §4、AC-14修订1–3及B1/B2 | U12候选/代码束未冻结、未过相称消费前C/R；部署墙钟/占用UNKNOWN |
| B-SIGN-DATA / DATA-CALIB / REUSE-BASE / SCORE-BASE | 条件推荐train派生1批/128张、base bf16原预测复用1次/609行、官方base评分1次/609行，数据根零写；数量承接已答选择 | 0 | AC-8修订4–5、BP-4 | 保护字段/原子组或代理排除、基准身份未复证，派生/输出精确B与峰值/墙钟UNKNOWN，维度0；约6MB不作精确B |
| B-SIGN-BOARD-MODEL / BASE-LOAD / BASE-SMOKE / BASE-S4A | 条件推荐官方base 3b服务加载/启动1次；3预热+32请求=35次；S4-a另609次，共644次；无额外预热/重启 | 0 | 已核W31/G2、§2.1、AC-7/8、已答B-S4A | W31/G2已核清并已传板；llama构建已核清；实际token出口/解析、基准身份、消费前代码C/R未齐；运行峰值/墙钟UNKNOWN，维度0；不由本轮来源事实认证运行兼容 |
| B-SIGN-TEST / TEST-B1 / TEST-B2 | 条件计数推荐Mac mini至多2候选，每候选全套1、det-assoc CPU加载≤2、NanoTrack尝试≤2/读权重0、CSRT尝试≤2/实例0、零模型回放≤2×60帧；总全套≤2、CPU≤4、两类尝试各≤4、回放≤4×60帧，候选间不可互借 | 0 | 准备审核§3、BP-5、AC-14修订3 | U12候选/冻结树/跑前只读计数未齐；测试墙钟、outputs/日志实际增长及峰值UNKNOWN，维度0；旧<0.1MB/候选是移植参考、不作本次已核字节；例外选择不授额度 |
| B-SIGN-REVIEW / REVIEW-REAL-CONSUMPTION | 推荐新增真实模型/回放/上板/SR各0；需要时具名另申请 | 0 | 准备审核§3、BP-5 | focused/红绿不豁免真实计次，不能借已耗尽SUB:6/SR |
| 不追加维度 | 系统设置/sudo/代理apt/重装torch/新容器/SSH变更、3a/base下载、15Hz压力档、S0–S2/SR重跑、Play/正式ID/训练GPU·h/API/发布均0 | 0 | §5、准备审核§5、账本本次云前边界 | 不在本次签发范围；用户本人B-APT操作不授权代理操作 |

**原入口快照（保留原文）：其中B-LOCAL-ALLOW-TRANSFER推荐已撤回、用户不采纳；现行本机申请见下段及「阶段B传板授权落实」§5。**

**原needs_user快照（保留原文；B-LOCAL-ALLOW-TRANSFER已撤回、TX-ASSETS已执行并核清，现行条目见末段）：逐维度签发入口。** TX-ASSETS数值已签，不重问；下一步B-LOCAL-ALLOW-TRANSFER推荐用户本人仅放行板目标192.168.8.2的SSH/SFTP TCP22、保留执行会话沙箱及目录python3窄规则并反馈，理由是当前静态网络列表无板目标，历史关闭沙箱不可沿用；完整出处/边界见「阶段B传板授权落实」§5。完成后交Implementation先离线核放行/旧账/槽位，再按合同一次核两端余量与并存上界，满足才传34件，失败停整批、不重传；尚未执行。INSTALL-W推荐已核31轮子离线安装1次，BUILD-LLAMA推荐保留源码离线构建1次并供已核2 GGUF后续使用；二者须分别先核解压/venv/构建峰值、墙钟与执行合同，生效仍0。DISK-PEAK/TIME、TX-CODE-DATA-LOGS、DEPLOY-CODE及DATA/BOARD-MODEL/TEST等未知维度推荐保持0，逐行缺前提见上表，未核不申请；REVIEW真实消耗和不追加维度继续0。用户后续签发只作用于具名已核维度，不默认包办其他行，不含云。已存W/G/S不再申请下载，不重问GGUF另取/主机放行或B-CLOUD/CLOUDDEP。S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN与AC-7/8/9 NOT_RUN保持。

**原needs_user / B-LOCAL-EXCLUDE-TRANSFER（已签、已执行完毕，保留原文）**：推荐用户签「阶段B传板授权落实」§5的具名排除条目、本人修改本机设置后反馈；理由是SSH子进程需随该顶层目录脚本在沙箱外运行，来源域名放行与Bash允许规则保持现状。依据账本2026-10-04「用户不采纳把板 IP 加进 allowedDomains：维持现有沙箱放行，SSH 到板走 excludedCommands 具名单独申请（supervisor 会话代录）」(a)–(d)。该条尚未签，不执行传板；TX-ASSETS已签数值、上表其他未签维度与未知前提不变，不选B加IP或C关沙箱。用户签发/本人改设置并反馈后才交Implementation，先离线核§5前提，未齐不试连。

前轮预检/来源核验/下载许可均已执行并收束，原证据保留作当轮快照；上述两段为执行前快照（TX-ASSETS当时待执行前提），现行条目见下段。

**原needs_user快照（阶段B传板核清后，2026-10-04，保留原文；BUILD-LLAMA 已由用户签发并落实合同，现行条目见下段）：**

- **B-LOCAL-EXCLUDE-TRANSFER 条目撤销（推荐：用户本人删除）**：推荐用户本人从 `~/TetheredDroneTracking/.claude/settings.local.json` 的 `sandbox.excludedCommands` 删除传板单条（其余设置保持）；理由：合同「阶段B传板授权落实」§5有效期仅本批、批次已收尾，同形未来目录不应继承；代理不改设置。
- **TX-ASSETS已传并核清，不重问**；板上34件（W31/G2/S1，独占目录 `~/eng-jet/stageb-transfer-20261004T225001Z/`）为后续维度已核输入，读数与上限符合判定见「阶段B传板核清」。
- **INSTALL-W（推荐值，生效仍0）**：31个distribution离线安装1次，只复用板上已核清的固定轮子；仍缺前提：解压/venv峰值、墙钟、venv/离线安装执行合同与未来有界兼容实测；由用户具名签发，不含云。
- **BUILD-LLAMA（推荐值，生效仍0）**：板上保留S副本离线构建1次并供已核G2后续使用；仍缺前提：解压/构建峰值、墙钟、构建执行合同；不取Edge源码/子模块；由用户具名签发，不含云。
- **其余维度**：DEPLOY-CODE、DATA-CALIB/REUSE-BASE/SCORE-BASE、BASE-LOAD/BASE-SMOKE/BASE-S4A、TEST-B1/B2、REVIEW真实消耗及不追加维度推荐保持0或条件值不变，逐行缺前提见上表，未核不申请；用户签发只作用于具名维度，不默认包办其他行。S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN与AC-7/8/9 NOT_RUN保持。

**原needs_user快照（阶段B构建授权落实后，2026-10-04，保留原文；现行条目见下段）：**

- **B-LOCAL-EXCLUDE-TRANSFER 条目撤销（推荐：用户本人删除）**：同上段快照第一条，推荐用户本人从 `.claude/settings.local.json` 的 `sandbox.excludedCommands` 删除传板单条（其余设置保持）；理由不变：合同「阶段B传板授权落实」§5有效期仅本批、批次已收尾，同形未来目录不应继承；代理不改设置。
- **BUILD-LLAMA（已签、合同已落实、待实现执行）**：用户已签发（账本 2026-10-04「用户签发 BUILD-LLAMA…」(a)–(f)）：板上离线构建 1 次、重试 0、墙钟 ≤2 h、板新增占用 ≤5 GB；执行合同见「阶段B构建授权落实」（输入 S 重核 sha、参数沿 AC-7 修订 2/3、前置/监测/越界处置/证据字段已定）；交 Implementation 执行，完成或中断回 Acceptance 核清。
- **INSTALL-W（推荐值，生效仍0）**：31个distribution离线安装1次，只复用板上已核清的固定轮子；仍缺前提：解压/venv峰值、墙钟、venv/离线安装执行合同与未来有界兼容实测；由用户具名签发，不含云。
- **其余维度**：同快照末条，推荐保持0或条件值不变，未核不申请；用户签发只作用于具名维度，不默认包办其他行。S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN与AC-7/8/9 NOT_RUN保持。


**原needs_user / 执行状态快照（阶段B构建前置停止核清后，2026-10-04；保留原文，现行见下段）：**

- **B-LOCAL-EXCLUDE-TRANSFER 条目撤销（推荐：用户本人删除）**：同上段快照第一条，推荐用户本人从 `.claude/settings.local.json` 的 `sandbox.excludedCommands` 删除传板单条（其余设置保持）；理由不变：合同「阶段B传板授权落实」§5有效期仅本批、批次已收尾，同形未来目录不应继承；代理不改设置。
- **BUILD-LLAMA / B-BUILD-RERUN（已签信封内，接受已裁定，无需新签）**：首批 `PRECHECK_FAILED` 已核清，构建0/1、重试0、执行墙钟3.766 s、批次工件板新增0 B。现行差异仅见「阶段B构建前置停止核清」§3/AC-10修订29；新批只修D-1，重做前置和S sha重核，满足后按原§2构建1次；两批执行墙钟合计≤7,200 s、新批保守≤7,196 s、板新增合计≤5 GB，原证据保留。交Implementation由supervisor派发，完成或中断回Acceptance核清。
- **INSTALL-W / 其余维度**：同上段现行前身的推荐与缺前提，生效仍0、不含云；未核不申请，不包办其他维度。S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN与AC-7/8/9 NOT_RUN保持。

**原needs_user / 执行状态快照（阶段B安装合同准备后，2026-10-05；保留原文，现行见下段）：**

- **B-LOCAL-EXCLUDE-TRANSFER 条目撤销（推荐：用户本人删除）**：同上段快照第一条，推荐用户本人从 `.claude/settings.local.json` 的 `sandbox.excludedCommands` 删除传板单条（其余设置保持）；理由不变：合同「阶段B传板授权落实」§5有效期仅本批、批次已收尾，同形未来目录不应继承；代理不改设置。
- **BUILD-LLAMA / B-BUILD-RERUN（已执行并核清，不再待答）**：构建1/1用尽、重试0，原前置停止与修订29归因保持；两批执行墙钟1,746.989 s≤7,200 s、板新增采样较大口径411,414,528 B≤5e9 B。只证固定S/参数在本板可构建，产物未运行；未知与证据边界见「阶段B构建核清」。不续建、不转用未用墙钟/磁盘，不以本项授权运行产物。
- **INSTALL-W / TIME-BOARD / DISK-PEAK-BOARD（安装子范围；合同已准备，待用户签数值，生效仍0）**：依据账本2026-10-05「用户答复阶段B构建核清后待决：INSTALL-W先准备离线合同再安装，其余未签维度保持0」(a)–(d)，离线合同及预算推导见「阶段B安装合同准备」§1–7。接受推荐：固定W31整批安装1次、重试0、整批墙钟≤3,600 s、板新增占用≤5,000,000,000 B；本机已核轮子ZIP静态解压字节，系统底座沿§8.2，实际安装时长/瞬时峰值/运行兼容仍UNKNOWN。推荐为有停止保护的执行上限，不保证完成，不预先申请运行兼容探测；本轮无需额外板访问，未来安装信封内先做具名前置，失败即停。**用户可直接回复的签发原文（接受推荐，非已签授权）**：「签发INSTALL-W：仅板上已核W31在独立W venv离线逐文件安装，安装1批（31文件各至多1次），重试0；整批墙钟≤3,600秒，板新增占用≤5,000,000,000字节（含venv、解压、pip缓存/暂存、日志与失败保留件）。按『阶段B安装合同准备』合同执行，含前置只读核对和装后pip list/pip check各1次静态核对，越界或失败即停、保留现场、不重试，回交Acceptance由用户决定；其余未签维度保持0，不运行模型/构建产物，不部署、不加载/查询/冒烟/测试，不含云、不改系统/SSH设置。」次数、重试、墙钟、板新增占用须逐维度签发入账；账本(b)的安装意向不代替签数值。
- **DEPLOY-CODE / TX-CODE-DATA-LOGS（推荐保持0）**：代码束/精确B与U12冻结、消费前相称C/R仍缺；构建成功不放行阶段B线束或旧补丁上板。**DATA-CALIB / REUSE-BASE / SCORE-BASE（推荐保持0）**：原子隔离/基准身份及派生体积、峰值/墙钟未核。理由与逐行缺前提沿上表，不代签。
- **BASE-LOAD / BASE-SMOKE / BASE-S4A、TEST-B1/B2、REVIEW真实消耗（推荐保持0）**：llama构建前提已核，但运行兼容、token/解析、运行峰值/墙钟、基准身份和消费前代码停点仍未齐；35/609/644次等仅保留条件推荐，不授一次启动或试跑。可回复原文（建议，非用户授权）：「其余未签维度保持0；不运行产物、不部署、不加载/查询/测试、不含云。」已答选择及B-CLOUD/CLOUDDEP未答现状不重问；S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN及AC-7/8/9 NOT_RUN保持。

**原needs_user / 执行状态快照（阶段B安装授权落实后，2026-10-05；保留原文，现行见下段）：**

- **INSTALL-W / TIME-BOARD / DISK-PEAK-BOARD（安装子范围；已签、合同生效、待实现执行）**：依据账本2026-10-05「P1-ENG-JET-001 — 用户签发 INSTALL-W：W31 独立 venv 离线逐文件安装 1 批、重试 0，墙钟 ≤3,600 s，板新增占用 ≤5,000,000,000 B（supervisor 会话代录）」(a)–(g)，用户原话与上段签发原文逐字一致；逐维度核对及执行效力结论见「阶段B安装授权落实」。仅按「阶段B安装合同准备」§1–7执行：板上已核W31、独立W venv、离线逐文件安装1批（31文件各至多1次）、重试0、整批≤3,600 s、板新增≤5,000,000,000 B；含具名前置与装后pip list/pip check各1次静态核对，失败/越界即停整批、保留现场、不重试，回交Acceptance由用户决定。交Implementation由supervisor派发；尚未安装，本轮consumed=none。
- **其他现行项**：前段B-LOCAL-EXCLUDE-TRANSFER用户本人删除建议、BUILD-LLAMA已执行并核清及不转用限制原文保留；其余未签维度保持0，不运行模型/构建产物、不部署、不加载/查询/冒烟/测试、不含云、不改系统/SSH设置。实际安装时长/瞬时峰值/运行兼容仍UNKNOWN；原STOP/未上板/OPEN债及AC-7/8/9 NOT_RUN保持。本轮授权核对needs_user=none，不重问已签INSTALL-W。

**原needs_user / 执行状态快照（阶段B隔离修补合同准备后，2026-10-05；现行见本节末段）：** B-INSTALL-RESULT=A、B-INSTALL-NEXT=B已按账本2026-10-05「用户答复阶段B安装核清…」(a)–(c)落实，不重问。安装原件/归因见「阶段B安装核清」§1–3，本批记账及方案/合同草案见「阶段B隔离修补合同准备」§1–5。INSTALL-W已用尽1/1、31件各1次、重试0，剩余墙钟/磁盘不转用；现场与`STATIC_CHECK_FAILED`保留，不豁免、不修补。以下新决策均为接受推荐、非已签授权；B-CLOUD/CLOUDDEP未答及不含云边界保持。

- **B-INSTALL-RESULT / 本批记账：用户已选 A、已落实**。成功子事实与pip check失败并列；严格脚本退出墙钟/瞬时峰值UNKNOWN保留，不记兼容或模型通过。账本(a)原文落实见「阶段B隔离修补合同准备」首段，不再请用户选择A/B。
- **B-INSTALL-NEXT / 后续路径：用户已选 B、已落实**。本机原件比较与合同草案已完成，见「阶段B隔离修补合同准备」§1–5；本轮consumed=none。用户只授权零消耗准备，未签任何板操作/安装/运行额度。
- **B-W-ISO-PLAN / 方案原则（接受推荐：I，非已签）**：I=保留原W失败现场，另建关闭系统site的独立W环境，只按预检后核定的具名链接暴露系统TRT；P=保留system-site并另核cffi/scipy补包闭集。推荐I，理由：W声明路径不需这两包，能避免为无关系统包扩大下载与安装；系统TRT结构/依赖未知先核，不宣称隔离即可运行。比较/条件草案见下节§2–3。**可回复原文**：「选B-W-ISO-PLAN I：保留原W现场与STATIC_CHECK_FAILED，后续准备另建关闭系统site、只暴露具名系统TRT的W环境；numpy固定2.2.6，具体链接闭集待预检核清。此次只选方案原则，不签安装或运行，其余未签维度保持0、不含云。」
- **B-W-TRT-PRECHECK / 具名有界预检（接受推荐：按下节§4签，非已签）**：只读核TRT包结构、METADATA/静态导入、链接/ELF依赖及路径/余量；Mac mini→同一Jetson，一批/一次SSH、重试0、整批≤300 s、代理板新增文件占用0 B、Mac新增≤10,000,000 B，stdout/stderr合计≤2,097,152 B；下载/资产传板/安装/import/模型/测试/云0。理由：现有ls只证TRT目录在，缺少能冻结最小暴露闭集的事实，engineering§9禁止先签依赖未知事实的安装。**可回复原文**：「签发B-W-TRT-PRECHECK：按『阶段B隔离修补合同准备』§4只读核TRT具名材料，Mac mini到既有Jetson一批、一次SSH、重试0，整批墙钟≤300秒，代理板新增文件占用0字节、Mac新增占用≤10,000,000字节，两流合计≤2,097,152字节；超限/失败/缺材料即停、保存已获原件回Acceptance，不修补或追加操作。下载/资产传板/安装/import第三方包/模型运行/测试/云为0，不改系统/SSH/沙箱设置。原W现场与失败保留，其余未签维度保持0。」
- **B-W-ISO-INSTALL / 后续安装维度（接受推荐：待预检核清再签，当前0）**：条件草案为新环境1次、W31各1次、重试0、统一≤3,600 s、板新增≤5,000,000,000 B、Mac新增≤100,000,000 B；下载/资产传板0，pip list/check各1次仅静态元数据核对。数值推导及尚缺输入见下节§3；TRT链接/依赖闭集未核，本轮不请签安装、不以方案/预检签发代签安装，更不授import/运行。
- **B-LOCAL-EXCLUDE-TRANSFER 条目撤销（推荐：用户本人删除）**：同上段快照第一条，推荐用户本人从 `.claude/settings.local.json` 的 `sandbox.excludedCommands` 删除传板单条（其余设置保持）；理由不变：合同「阶段B传板授权落实」§5有效期仅本批、批次已收尾，同形未来目录不应继承；代理不改设置。
- **其他未签维度（推荐维持0，不重问已答项）**：DEPLOY-CODE、TX-CODE-DATA-LOGS、DATA-CALIB/REUSE-BASE/SCORE-BASE、BASE-LOAD/BASE-SMOKE/BASE-S4A、TEST-B1/B2、REVIEW真实消耗与其余未签维度保持0；INSTALL-W事实不补齐这些合同/代码停点/实际token解析/运行峰值墙钟前提。BUILD-LLAMA已用尽、不转用；S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN及AC-7/8/9 NOT_RUN保持。可回复原文：「其余未签维度保持0；不运行产物、不部署、不加载/查询/冒烟/测试、不含云。」

**原执行状态快照（阶段BTRT预检授权落实后，2026-10-05；上段原文保留，现行见下段）：**

- **B-W-ISO-PLAN = I（用户已选、接受已落实）**：按账本2026-10-05「用户选 B-W-ISO-PLAN I 并签发 B-W-TRT-PRECHECK…」(a)落实方案原则；保留原W现场与STATIC_CHECK_FAILED，numpy固定2.2.6，后续准备关闭系统site、只暴露具名系统TRT的新W环境，链接闭集待预检核清。方案选择不签安装、链接或运行。
- **B-W-TRT-PRECHECK（用户已签、合同生效、待实现执行）**：账本同条(b)–(d)与「阶段B隔离修补合同准备」§4逐维度一致，核对见「阶段BTRT预检授权落实」§1–2。仅交Implementation由supervisor派发执行该§4一次有界只读预检，完成或停止即回Acceptance核清；本轮未执行，consumed=none。本轮授权核对needs_user=none，不重问已选方案/已签预检。

B-W-ISO-INSTALL及安装/链接/运行等其余未签维度仍0，不含云；上段其他现行项、用户本人撤销传板排除条目的建议与历史限制保持。这里仅追加替代上段两项“非已签”状态，原推荐和可回复原文作为授权对应来源保留。

**原needs_user / 执行状态快照（阶段BTRT预检核清后，2026-10-05；现行见本节末段）：** 方案I已选；B-W-TRT-PRECHECK已执行、批次/SSH均1/1用尽、重试0，不重问、不转用。原件核清及执行偏差见「阶段BTRT预检核清」§1–2；可核静态事实保留，不能记严格全合同符合。§3最小暴露/链接闭集尚不能冻结，安装/链接/静态核对及运行仍0；numpy固定2.2.6，原W现场与STATIC_CHECK_FAILED保留。以下为**接受推荐、非已签**，不代写用户账本：

- **B-W-TRT-RESULT / 偏差与证据处置（推荐：保留静态读数及限制，不追认全符合）**：主批数值读数在限内；自报本机假目录干跑在批次之外、无本轮收据，端口为固定22而非从relay解析，最后监督退出/完整本机增长未闭。推荐保留这些事实并停止依赖推进，避免用COMPLETE遮蔽边界缺口；不增加一次SSH、不补测。**可回复原文**：「B-W-TRT-RESULT：保留本批已核静态读数及执行方法偏差；批次和SSH均记1/1用尽、不转用，不追认为严格全合同符合。保留批外干跑计时/占用、完整监督退出与瞬时峰值UNKNOWN，不豁免原STATIC_CHECK_FAILED，不签安装、链接、运行或补测额度。」
- **B-W-TRT-SUPPLEMENT / 具名补充静态预检（推荐：按『阶段BTRT预检核清』§4另签）**：仅补libnvonnxparser及具名NEEDED映射/包归属、RUNPATH字面目录和可选模块位置，不重跑原五块，不动态加载；这些板事实阻塞安装输入冻结。推荐Mac mini→既有Jetson一批/一次SSH、重试0、统一≤300 s、代理板新增0 B、Mac新增≤10,000,000 B、两流≤1,048,576 B；详细操作/硬界/推导/停止与证据字段见该§4。**可回复原文**：「签发B-W-TRT-SUPPLEMENT：按『阶段BTRT预检核清』§4的具名闭集、命令形式、读取硬界和停止处置，仅Mac mini到既有Jetson一批、一次SSH、重试0，整批墙钟≤300秒，代理板新增文件占用0字节、Mac新增占用≤10,000,000字节、两流合计≤1,048,576字节；超限、失败、材料缺失或新闭集外依赖即停，保留原件回Acceptance，不追查、不修补、不追加。下载、资产传板、安装、创建链接、Python/pip/import/ldd/动态加载、模型、测试、云为0，不改系统/SSH/沙箱设置；原W现场及失败保持，其余未签维度保持0。接受核对本授权与合同一致后才交实现。」可选择暂不签；暂不签即保持停止，不自动换P/U方案。
- **B-W-ISO-INSTALL / 安装、链接、静态核对（推荐：暂不签，保持0）**：§3条件预算仍仅草案；libnvonnxparser位置/包/依赖、库搜索映射未核，不能形成可签安装闭集。推荐先补静态事实，不将TRT可选numpy元数据解释成可降numpy，不将plugin函数内triton变成自动补包。**可回复原文**：「B-W-ISO-INSTALL保持0；先核清具名补充预检，再由接受准备安装、链接和静态核对合同，不授import或运行。」
- **B-LOCAL-EXCLUDE-TRANSFER / 原临时条目撤销（推荐：用户本人删除，仍未获反馈）**：旧传板单条已过有效期，代理不改设置；它也不是本次或未来补充预检的权限来源。**可回复原文**：「我已本人删除settings.local.json中原stageb-transfer-*的sandbox.excludedCommands单条，其余设置保持。」只有用户实际完成后才反馈，不把此推荐当已删除或执行前置。
- **其他未签维度（推荐：维持0，沿缺省无需重答）**：部署、代码/数据/日志传输、加工/评分、产物运行/加载/冒烟/查询、测试/真实复核消耗仍缺各自合同与停点，不因预检读数补齐。**可回复原文**：「其余未签维度保持0；不运行产物、不部署、不加载/查询/测试、不含云。」BUILD-LLAMA/INSTALL-W用尽；B-CLOUD/CLOUDDEP未答；既答选择/事实/放行不重问，S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN及AC-7/8/9 NOT_RUN保持。

**原needs_user / 执行状态快照（阶段B3b诊断冒烟授权落实后，2026-10-05；现行见本节末段）：** 依据账本同日「用户签发官方 base 3b 诊断冒烟：llama-server 加载 ≤3、请求 ≤60、墙钟 ≤1 h、板新增 ≤1 GB，缺图可经有线传 ≤10 张/≤20 MB，结果只作诊断不进证据；3c 停在补充预检之前」用户原话；supervisor (a)–(h) 是读法，与原话有出入一律以原话为准。执行合同只见下节§1–7。

- **B-SIGN-BOARD-MODEL / BASE-LOAD / BASE-SMOKE（仅诊断子范围已签、合同已落实）**：一次官方base 3b诊断批；加载≤3、请求≤60（含预热/健康/失败预约）、统一≤3,600 s、板新增≤1,000,000,000 B；无可用本项图片时才准既有有线传≤10张/≤20,000,000 B。下一实现按下节较窄固定计划执行，不把上表正式35/609/644次推荐转为许可。本轮只核授权/写合同，consumed=none；交Implementation由supervisor派发，结束即回Acceptance核计次收据，不交正式S3证据或verdict。
- **3c（W/TensorRT）停点：停在B-W-TRT-SUPPLEMENT之前，等用户云端决定**。补充预检不签、当前0；B-W-ISO-INSTALL及安装/链接/运行保持0，不按原推荐先补预检。方案I已选和原预检1/1/偏差/UNKNOWN、W现场与STATIC_CHECK_FAILED保持；不重问已答事项。
- **B-W-TRT-RESULT仍未答**：推荐保留已核静态读数及执行偏差，不追认严格全合同符合；理由及可回复原文沿上段同名项。**B-LOCAL-EXCLUDE-TRANSFER仍未答/未获实际删除反馈**：推荐用户本人删除过期传板单条；理由及可回复原文沿上段同名项。较早账本「稍后我会删掉」不是完成反馈，本次3b原话也没有答复这两项；它们不阻塞3b，不由代理改设置。本轮不再呈现补充预检/隔离安装签发题。
- **其余未签维度0**：下载、安装、import第三方包、C2、BASE-S4A/S4-a、S5、测试、部署、云（B-CLOUD/CLOUDDEP未答）、Play/API/正式ID/发布均0。原§5表/历史快照中的“运行全0”仅在本次具名诊断子范围被上述授权替代，不是正式S3/S4许可；S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN、AC-7/8/9 NOT_RUN及REVIEW_PASSED/ACTIVE保持。

**现行needs_user / 执行状态（阶段B偏差处置落实后，2026-10-05）：** 本批诊断执行及计次已核，逐维度账、原件一致性勘误与执行形式偏差只见「阶段B3b诊断冒烟核清」§1–3。已用加载1/3、请求预约/送出7/60、传图0；SSH实际14次（原汇总漏计两条流式连接），重试0。统一可核墙钟至尾文件135.672 s，最终监督退出尾差及批外准备时长UNKNOWN；板新增较大采样口径36,864 B，瞬时峰值/不可归属系统增长UNKNOWN。不追认严格全合同符合，不提升为AC-7/S3满足、性能读数或verdict。B-3B-RESULT与B-W-TRT-RESULT已答，指代核对及落实见「阶段B偏差处置落实」§1–2；其他推荐仍非已签决定/授权：

- **B-3B-RESULT / 本批记账与偏差处置（用户已选推荐、已落实；不再待答）**：理由是加载/请求预约可逐条绑定送出与原文，偏差不应退回计次，完整墙钟与监测边界又未闭。以下保留推荐及**原可回复原文（对应来源，不冒充用户逐字答复）**：「B-3B-RESULT：保留本批诊断原件及已核资源账，加载记1次、请求记7次、传图0、SSH记14次、重试0；保留执行形式偏差、批外准备时长和最终退出尾差及瞬时占用UNKNOWN，不追认为严格全合同符合，不进证据、不记AC-7/S3或门满足。本批未用额度作废、不转用，不追加诊断或补测。」这不是请用户给已发生动作补签额度。
- **B-W-TRT-RESULT / 偏差与证据处置（用户已选推荐、已落实；不再待答）**：保留已核静态读数及执行方法偏差，批次/SSH均1/1用尽、不转用，不追认严格全合同符合；原STATIC_CHECK_FAILED及批外干跑计时/占用、完整监督退出/瞬时峰值UNKNOWN保持。推荐理由与原可回复原文保留在本节「阶段BTRT预检核清后」快照，仅作本次短答的对应来源；不签安装、链接、运行或补测额度。两项偏差均只作事实记录，不追加独立finding/SCOPE_GAP/返工或返工计数，不改既有派发报告与原件，落实见「阶段B偏差处置落实」§2。
- **B-3B-NEXT / C2云端下一步（推荐：3b到此，先只准备云端合同，执行维度0）**：现有诊断只能保留具名服务/HTTP执行事实，缺正式token/grid、解析、基准与消费前停点，不足以选择C2产物或授正式S3；C2产物尚缺云合并/转换/量化。推荐不继续base调参或追加3b，沿用户已选I-A只做本机零消耗的C2云端预检/依赖申请准备，再由用户决定云端执行；不重问已定I-A、J-B、方案I或缓存等选择。**可回复原文**：「3b诊断到此，不追加加载、请求或补测；下一步只在Mac mini本机零消耗准备C2云端预检与依赖申请合同，列明未知事实和逐维度额度，待我另定。此次不签云租用、SSH、下载、安装、合并、转换、量化、校准、传输或模型运行；3c仍停在补充预检之前。」B-CLOUD/B-CLOUDDEP依然未答，此推荐不自动启动准备派发或执行。
- **3c停点及B-LOCAL-EXCLUDE-TRANSFER未答保持**：B-W-TRT-SUPPLEMENT之前停止，安装/链接/运行0，等用户云端决定；不再呈现补充预检/隔离安装签发题。**B-LOCAL-EXCLUDE-TRANSFER**仍未答/未获实际删除反馈，推荐用户本人删除过期单条；理由与可回复原文沿本节「阶段BTRT预检核清后」快照，不由本次偏差处置代答或代理改设置。
- **其他边界**：本批≤3/≤60/≤1 h/≤1 GB及条件传图额度收束，不作为下一批余额；所有后续未签维度0、不含云。已答事实/选择/既有放行不重问；S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN、AC-7/8/9 NOT_RUN及REVIEW_PASSED/ACTIVE保持。

**现行needs_user / 执行状态（阶段B基座提示调试授权落实后，2026-10-05）：** B-3B-NEXT已由用户答复（未取推荐项）：继续官方base 3b，在板上做基座测试与提示迭代，诊断额度一次签发、交互式执行，合同见「阶段B基座提示调试授权落实」§1–6；上段B-3B-NEXT的推荐与可回复原文只保留为当轮快照，不再待答，C2云端准备不启动。3c仍停在B-W-TRT-SUPPLEMENT之前；B-CLOUD/B-CLOUDDEP与B-LOCAL-EXCLUDE-TRANSFER仍未答，推荐与原文沿上段。本次已签诊断额度之外的维度仍为0、不含云；诊断结果不进证据，AC-7/8/9 NOT_RUN及S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN保持。

**现行needs_user / 执行状态（阶段BC2JSON诊断答复落实后，2026-10-06；替代此前推进状态，历史原文留作快照）：** 依据账本同日「用户答复 B-C2-RESULT 按推荐；签发『C2 Q4 加 JSON 约束』板上 609 行诊断…」(a)–(e)、「用户答复待决项：B-CLOUD/B-CLOUDDEP 结束…」(a)–(e)及「用户答复 C2JSON-DRIVER_SELF_CHECK_STOP：JSON 约束诊断到此结束（按接受推荐；supervisor 会话代录）」落实如下；不代写用户原话、不补签既往动作。

- **B-C2-RESULT = 按推荐（用户已答、已落实，不再待答）**：保留本批C2诊断原件、已核配对身份与资源账；保留合并核验停止后自行续行的越界、工具计量/执行形式偏差及UNKNOWN，不追认为严格全合同符合，不进证据、不记AC-7/8/9或门满足。本批未用额度作废、不转用，不以旧批余额追加诊断、加工、传输或补测；偏差只作事实记录，不追加独立finding或返工计数。核清来源仍为「阶段BC2诊断核清」§1–4；账本(a)所引接受推荐原文是本次采纳的对应来源，不冒充用户逐字原话。
- **C2 Q4 加 JSON 约束 / C2JSON-DRIVER_SELF_CHECK_STOP（用户已答结束、已落实，不再待答）**：本诊断到此结束，attempt-1失败原件、已核资源账、驱动自检误报、监督/计时偏差及UNKNOWN保留，不追认严格全合同符合，不进证据、不记AC-7/8/9或门满足；本诊断信封未用余额作废、不转用，不追加驱动修复、加载、请求、传输或补测。3c仍停、S5推后未签保持。落实及推荐项原文见「阶段BC2JSON诊断答复落实」§1；身份/账与执行边界仍见「阶段BC2JSON诊断核清」§1–4，其§5两项为答复前快照，不再发令或请用户重选；挪用第2加载的另一项未获采纳，旧越界/UNKNOWN不被追认。
- **B-CLOUD/B-CLOUDDEP = 结束、不租云；B-LOCAL-EXCLUDE-TRANSFER = 用户本人已删除、已核实**：不再待答，不启动云端准备/租用、不恢复过期排除条目。**3c = 条件提升点**：若llama.cpp路径性能不够好时再考虑，触发判据待闭环曲线；当前仍停在B-W-TRT-SUPPLEMENT之前，补充预检/安装/链接/运行未签0。**P2**不采用、不另立项，原读数仅作面试应用验证诊断、不进证据。
- **S5共驻 = 推后到快层调好之后、未签**：保持NOT_RUN，不重问此顺序决定，不由本次JSON诊断签发推定任何快层/共驻额度。
- **其他边界保持**：已答事实/选择/既有放行不重问；其余未签0，REVIEW_PASSED/ACTIVE、AC-7/8/9 NOT_RUN、S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN保持。已签范围内无可执行动作，**等待用户另定方向**；未闭义务及唯一新方向题JET-NEXT-DIRECTION的接受推荐、理由与可回复原文只见「阶段BC2JSON诊断答复落实」§2–3，推荐非已签，不自行收口、暂停、修复或签额。

open_items: none

### 阶段B3b诊断冒烟授权落实（2026-10-05，Acceptance；诊断执行合同）

登记轮次 `阶段B3b诊断冒烟授权落实`；Dispatch-Id `P1-ENG-JET-001-阶段B3b诊断冒烟授权落实-20261005T213257Z-5840`。本轮零消耗、只读本机保留材料并写文档，不是D/C/R轮，不签额、不代写账本、不消费verdict。本节把上述具名授权落实为一批合同；事实/待决入口仍只在「阶段B预检答复落实」§5现行段。新增AC/AC修订=0：这是用户明确的非证据诊断子范围，不改变正式验收项。

#### 1. 授权逐维度核对与适用边界

| 维度 | 原话、supervisor读法与既有条款核对 / 本批落实 |
|---|---|
| 路径/设备 | 原话“官方base的3b”按§2.1 S3及构建/传板核清唯一对应本用户Jetson系统栈B、b11381现有llama-server与官方G2（Q4_K_M模型+F16 mmproj）；(a)一致。无C2/转换/量化/合并、新编译、W调用或换服务，快层不开。 |
| 加载/请求 | ≤3/≤60与(b)一致；§3逐次预约，健康、预热、失败都计入。正式AC-7的3预热+32行、25/7分组及正式缓存重跑不是本次执行序；只按§4固定的小计划，不用额度追试数。 |
| 墙钟/板占用/图片 | ≤1 h=3,600 s；1 GB按十进制1,000,000,000 B、20 MB按20,000,000 B（从严取小），≤10张是同批总计，(b)(c)一致。全程含前置/可选传图/加载/监测/请求/终止/收据收尾，不给每启动重置上限。 |
| 绑定/缓存/超时 | AC-7修订2–3的本地具名模型、仅loopback、禁hub/URL、固定构建及常驻口径继续适用；§3.3的cache_prompt=false、temperature=0、max_tokens=160、原图和prompt v2保持。§4明确端口及请求超时；AC-7修订4的视觉缓存例外针对3c，不移植为3b豁免。诊断不认证token=300/无缓存性能，缺出口记UNKNOWN。 |
| 诊断不进证据 | 原话及(e)一致：不写-vlm/-report/-assets/-ledger或其他docs/evidence证据工件；不记AC-7/S3满足、不形成PASS/STOP/NOT_RUN新verdict、不形成门值/性能/显存读数、不消费复核。§7独立诊断原件仅核资源使用和执行事实，不能转贴成验收依据。 |
| 禁止与3c | 不改系统设置与(d)一致；(f)列举的未签动作依缺项0适用，不从诊断推测试/部署等授权；(g)一致，3c停在补充预检之前，隔离安装0，等云端决定，两项未答仍未答。 |
| 执行效力 | (h)是按先例的接受落实前置，不是用户额外签发。本节完成核对后合同可交实现；未知运行兼容正是有界诊断所探的问题，不由构建成功推为已知兼容，不先申请正式证据运行。 |

没有发现原话与(a)–(h)的实质冲突；“授权范围”只作supervisor解释，**用户原话优先**，本节不追签其未说的额度。原正式S3消费前B1代码C/R义务未解除；本次直接用具名既有服务的诊断不部署阶段B适配器、不调用旧未上板补丁、不形成候选消费或B1通过，不能据此绕过未来正式停点。

**本次交接Consuming=no**：按AGENTS/workflow§7规则0与engineering§8定义，本批不创建/消耗scenario/session/run ID、不Play、不动模型API预算/云；localhost llama-server HTTP调用是§5原表已区分的本地查询，计入用户本次诊断请求额度，不能伪称零模型运行。板端加载/占用/有线传图仍须且仅用本次engineering§9独立授权。输出UTC目录只是诊断工件命名，不是正式run ID。当前JET+COORD-018两条no交接在上限内；实际由supervisor单写者串派、共享槽位空闲才执行，不使用任何旧并行破例。

#### 2. 输入闭集与具名路径（运行时解析，不抄可派生目录或SHA）

| 输入 | 唯一来源/解析规则与前置 |
|---|---|
| SERVER | `docs/evidence/P1-ENG-JET-001-stageb-build-rerun.json`的`products.llama_server_stat_raw`首个竖线前路径，必须等于该JSON的`board_batch_dir.path`下`build/bin/llama-server`；对应原stat为72,424 B普通可执行文件。同目录动态库按`products.bin_ls`具名文件/链接集合只读核类型、大小、链接终点与父路径，不改LD_LIBRARY_PATH/系统库/链接；缺项、大小/类型/来源改变即停，不运行--help/--version试探，不另找二进制。路径来源、构建参数与只证构建的边界见「阶段B构建核清」§1–3。 |
| MODEL / MMPROJ | `docs/evidence/P1-ENG-JET-001-stageb-transfer.json`的`objects`中kind=G且basename分别为`Qwen3VL-2B-Instruct-Q4_K_M.gguf`、`mmproj-Qwen3VL-2B-Instruct-F16.gguf`的唯一`board_final`；两者必须同属该JSON独占板目录。板上普通非链接，stat字节分别1,107,409,952/819,394,848；sha256sum与JSON期望、用户GGUF账本及本机已核绑定链逐字比对。sha运行时解析；不符/缺项立即停，不重取/替换原件。 |
| 板已有图片 | 只查`~/eng-jet/frames/a7/`中`frame_0000000000.jpg`至`frame_0000000319.jpg`这320个具名成员；来源为`-assets.json`的`board_manifest.listing`相对路径及阶段A已传a7，期望哈希取`docs/evidence/P1-ENG-JET-001-a7-frame-sha256.jsonl.gz`的frame_id/sha纯参照。禁止读sidecar/gold/索引。可用=普通非链接、非空、字节/sha与对应源/参照一致，JPEG原图640×480（用标准库只读JPEG SOF尺寸核实，不解码/重采样）。存在但坏哈希/坏格式/尺寸不符是INPUT_CHANGED，停整批，不能谎称“缺图”再传。缺文件可记ABSENT。 |
| 板图选取 | 先取a7帧0、100、200中的可用者，若不足3张，再按其余0…319帧号升序补到3张；总使用n=1…3张，不读其他目录或随意选图。只要闭集内存在可用图就用已有图，传图0；已有图不足3张也不补传。本轮未接板，当前存在/可用性是历史来源加执行前核验，不能写为本轮已实测。 |
| 仅无可用板图时传板 | 320成员全部ABSENT才触发；Mac只读数据根`~/TetheredDroneTracking-full/runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/`的上述帧0/100/200三件，按此顺序选现存可用者≤3张，合计≤97,519 B且必须≤20,000,000 B、累计件数≤10。使用同一纯参照/字节/640×480核验；源缺失全部或不符即停，不搜其他数据/扩选10张、不从网络取图。只传JPEG原字节；不传JSON/prompt/标签/清单/脚本/包/模型/代码束。 |

解析歧义、上游原件绑定失败、文件变化一律停，保留来源，回接受/用户；只读本机材料准备与板前置都记在本批，不做批外假树/干跑/测试。原件的历史SHA从JSON绑定链现算比较，不手抄进合同；SERVER没有历史二进制hash则只记录本次hash并注明历史内容身份未独立hash验证，不补造旧期望。

#### 3. 预算、计次与单批目录

- **硬上限**：加载≤3次、请求≤60次、统一墙钟≤3,600 s、板新增占用≤1,000,000,000 B、条件传图≤10件/≤20,000,000 B。本合同固定计划只启动1次、最多7个HTTP请求；不把未用2次加载/53次请求视为自动重试许可。成功/失败/超时/拒绝/崩溃的预约不退回。
- **加载口径**：发出llama-server启动前先落预约+1（同时加载两件算1次服务启动），启动失败/加载不完也计1；重新exec/崩溃重启/后台自动拉起都算新次。禁逐请求CLI、--help/--version额外执行、自动重启与失败重试。`--no-warmup`关内部空推理预热；若仍发现额外内部预热/推理，按一次请求从严记账并停，不把未记内部调用算0。
- **请求口径**：向该服务发任何HTTP尝试前先预约+1，含GET健康、POST图像、预热、重复图、连接失败/无响应/HTTP错误；不按模型实际完成数回退，不把同图缓存命中免计。原始系统调用收据与唯一递增序号对应，预约后未能确认送出也保留已用；没有重定向/客户端重试、探测轮询或自动客户端连接重试。工具/SSH调用次数另记，不冒充模型请求。
- **墙钟**：本机第一次批次目录创建与started记录较早者起，UTC及monotonic双记，同一绝对截止覆盖准备、所有前置/连接/传图/加载/健康/请求、监测、服务停止、收据保存及监督退出；不能到首次加载才起算。预留60 s收尾，剩余≤60 s不发新动作；每个命令/连接/请求用统一剩余再取较小超时，强杀时间也在余额内。最后监督自身写入尾差不能核实时标UNKNOWN，不声称完整计时。
- **目录/占用**：Mac新建唯一`outputs/eng-jet/P1-ENG-JET-001/stageb-3b-diagnostic-<UTC>/`，板新建唯一`~/eng-jet/stageb-3b-diagnostic-<UTC>/`（下称DIAG），都须事先不存在且非链接，mkdir 700、umask 077；时间戳由执行期生成，不进正式ID。板所有本批新文件含images/.part/缓存/tmp/错误保留件及目录元数据共账；双du表观与分配取大，基线先记`~/eng-jet`与DIAG不存在，随后取DIAG双du及eng-jet同口径正增长的较大值，不能靠删旧件/外部下降抵销。既有模型/库/图片不重算新增、不复制G2。SSH/PAM/atime及不可归属的系统增长另列UNKNOWN，不声称板物理零外写；发现本项向受保护根写入即停。
- **条件传图计量**：每件scp前预约一件及源stat全文B，失败/部分字节从严按整件预约计入总数/20,000,000 B；每件仅1次、重试0，.part也计板占用。原许可10张/20MB不含其他资产传板；板本地读取原图片/loopback内base64不是Mac→板资产传输。

#### 4. 命令形式、请求内容与固定执行顺序

**依据只读本机保留源码**：从`stageb-source-archive.json`的归档路径解析保留b11381副本，只读归档内`common/arg.cpp`、`tools/server/README.md`及`server-context.cpp`，已核下列flags、data URI/health/chat端点和cache开关定义。没有联网/解压落盘/执行产物；源码接口文字不证本板运行兼容。

**链路/执行工具**：只Mac mini↔原Jetson有线。目标运行时取`docs/evidence/P1-ENG-JET-001-relay.json`的`link.ssh`首段；端口固定既有22（不声称JSON有port字段）。SSH固定`-T -p 22 -o BatchMode=yes -o StrictHostKeyChecking=yes -o UpdateHostKeys=no -o ConnectionAttempts=1 -o ConnectTimeout=15 -o Compression=no -o ControlMaster=no -o ControlPath=none -o ForwardAgent=no -o ClearAllForwardings=yes`。条件scp用`-P 22`及同组适用选项，每件至新DIAG/images/<basename>.part，核stat/sha后同目录改名；失败不再登录兜底/重传，严禁rsync/替代链路/放宽键检查。SSH身份/尺寸/哈希/余量、进程监督与请求可用现有sh、timeout、curl、base64、stat/du/df/ss、sha256sum及系统Python的`-I -S -B`纯标准库（JPEG头、JSON、内存计次/监督），不import项目包/第三方包，不写板端脚本或部署代码。窄Mac驱动只落DIAG对应本机目录；无批外scratchpad或合成执行验证。

1. 先完成§5前置和§2选图/必要传图，冻结n张图片及顺序；准备prompt v2文本，surface逐字`the car`、g4=false、vocab=`unity-v2`。本机只读`tools/eng_sft/prompt_v2.py`的HEAD/VOCAB/COORD/REPLY字面常量，按原build_prompt规则换surface并以换行连接，不import模块/不改段文字；将原文与现算hash记诊断请求收据，图像不加标签/真值/时间字段。请求在板内内存组装，不将prompt文件/代码束传板。
2. 一个受同一远端进程组监督的常驻服务，固定如下argv；SERVER/MODEL/MMPROJ按§2解析成绝对路径，不能在脚本中猜目录。工作目录DIAG，stdout/stderr直接流回Mac诊断原件，不写既有构建目录；禁止后台脱离监督。服务最长加载准备300 s，未在日志确认ready即停止，不循环发健康探测。

   ```sh
   "$SERVER" --model "$MODEL" --mmproj "$MMPROJ" \
     --host 127.0.0.1 --port 18081 --parallel 1 --ctx-size 2048 \
     --n-gpu-layers 99 --fit off --no-warmup --no-webui \
     --no-cache-prompt --cache-ram 0 --cache-reuse 0 --offline
   ```

   仅进程环境设`TMPDIR=DIAG/tmp`、`XDG_CACHE_HOME=DIAG/cache`、`XDG_CONFIG_HOME=DIAG/config`、`LLAMA_CACHE=DIAG/cache/llama`、`HF_HOME=DIAG/cache/hf`、`CUDA_CACHE_PATH=DIAG/cache/cuda`、`CUDA_CACHE_MAXSIZE=134217728`、`YOLO_CONFIG_DIR=DIAG/config/yolo`、`MPLCONFIGDIR=DIAG/config/mpl`；禁继承`LLAMA_ARG_*`/`MTMD_BACKEND_DEVICE`等自动模型/服务覆盖变量及代理变量；不改HOME或持久环境/配置。对子进程`ulimit -c 0`禁core文件，只限本进程，不改系统设置；旧缓存不删。CUDA缓存限值是进程保护，实际遵守程度/瞬时峰值未证，不能只由环境值认证磁盘满足。
3. ready日志及ss确认仅127.0.0.1:18081属于本批PID后，**GET /health恰1次**；`curl --noproxy '*' --retry 0 --connect-timeout 5 --max-time 10 --max-redirs 0 http://127.0.0.1:18081/health`，预约后发出。HTTP非200/缺ready/加载超时/端口不符即停，不用503轮询或改端口。无浏览器/UI、/models、tokenize或metrics探测。
4. n张图按冻结顺序各一次预热，再同顺序各一次诊断（重复图只注明重复，不给缓存统计/verdict），串行、无历史对话、无并发。POST仅`http://127.0.0.1:18081/v1/chat/completions`，JSON为`{"model":"<MODEL basename>","messages":[{"role":"user","content":[{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,<原图字节>"}},{"type":"text","text":"<上项冻结prompt v2>"}]}],"temperature":0,"max_tokens":160,"stream":false,"cache_prompt":false}`。无远程/文件URL、无图片resize/图像容量强设为300。curl用`--noproxy '*' --retry 0 --connect-timeout 5 --max-time 120 --max-redirs 0 -H 'Content-Type: application/json' --data-binary @-`，总timeout再受剩余墙钟约束。每请求响应≤1,048,576 B，正文/HTTP码/curl rc原样保存；超时、HTTP非200、服务错误/空生成/崩溃即停止整批，不重复该请求、不换参数/路径。任务文本只作诊断原文，不评分/运行正式解析器或609行评估；若图像/token出口不足只记UNKNOWN，不额外查询取证。实际日志显示缓存命中/图像处理异常则记录并停，不改开关重跑。
5. 计划上界`1+2n≤7`个请求、1次加载，完成即§6收尾。原≤60/≤3未用额度不转为下一批、不用于CACHE_SUSPECT重跑/3c/S4/S5。

#### 5. 前置与监测（均在本批统一计时内）

执行前本机核账本入账/本合同及来源绑定、单写者/共享槽位空闲、已有窄权限可执行；任何权限拒绝即停，不改Claude/沙箱/SSH设置，不继承过期传板排除条目作为许可。未来若实际环境必须用户新增设置/补包才能执行，回§5入口具名请求，未答0；不在本轮预签假设变更。

板只读核id/HOME/aarch64及已有工具、输入/动态库/图片、DIAG不存在，`systemctl get-default`与display-manager状态只读确认headless（不sudo、不isolate）、`ss -ltnp`确认18081空闲/不存在其他本项模型服务、free/df和两种du基线。剩余磁盘须≥1,000,000,000 B加100,000,000 B收尾余量；余量不足、headless不符、已有模型并驻、工具缺失、未知进程占端口或输入不符即停，不杀其他进程、不尝试其他端口/文件/栈。不重跑S0/功耗/频率5min测量或改nvpmodel。

在途本机监督每≤1 s检查同一截止、加载/请求预约、两流增长/rc和服务进程组；板同一监督每≤1 s核DIAG表观/分配与eng-jet正增长、df余量及服务存活，每个新受控文件写入/预约请求前再核余额。服务日志/收据两流合计技术限64 MiB、本批图片≤20MB、请求/响应单份≤1MiB、CUDA缓存过程限128MiB；写入前按已知最大增量投影占用，达到700,000,000 B提前停止，为强杀/日志收尾留300,000,000 B。不无限增长日志、不truncate/丢尾以伪造在限内。无法执行监测/投影即停；采样不是瞬时峰值证明，缓存或SSH系统附带写入不可归属时明确UNKNOWN，不宣称绝对零外写/精确峰值。进程日志异常、外联/自动下载征兆、OOM/崩溃、请求失败、磁盘保护或时间保护触发都立刻停止后续动作；保留已获原文。

#### 6. 停止、清理与返回

所有失败/超限停止整批，保留已用预约及原件；**本批不重试、不换图/源/模型/端口/栈，不自动进3c**。远端监督以统一剩余的`timeout -k 2`约束进程组，本机外层同一绝对截止并预留清理；无须以“还有加载额度”拉起服务。终止时仅对本批PID/其受控进程组TERM，最多等5 s再KILL，均在预留余额；禁pkill全名或杀其他服务。正常完成也停止服务，wait取退出码并ss核18081释放；连接已断且远端结束不能证明时记UNKNOWN，不二次登录找进程，不将仅断SSH称服务已停，交用户具名处置。

只可处理DIAG内本批新建、清单有归属的临时请求/缓存/tmp及条件传图.part；先记录路径、字节/hash、处置和删除前后du，失败原件/计次收据保留。诊断收据优先落Mac，板未复制请求文件则无需删除；条件传图和故障.partial默认保留供核计量。不得删除/覆盖/移动既有板文件、G2/源码/构建产物/库/原W/sysvenv/旧图片/旧缓存，不能为满足磁盘上限清旧件。本合同不要求删除整个DIAG或追清系统副作用；删本批临时件释放占用不回退请求/加载/图片传输计次，采样峰值和失败保留值仍如实报告。本批终止/收尾后立即交Acceptance核资源收据，3c及其余未签动作保持停点。

#### 7. 诊断原件与可核字段（不进入证据链）

只在本机上述新诊断目录保留`plan.json`、`receipt.json`、`calls.jsonl`、`budget.jsonl`、每调用stdout/stderr/rc、原始响应与服务日志；板DIAG保留本批新文件归属/缓存/条件图片，不写`docs/evidence/`，不覆盖任何历史JSON/原件。机器收据须含`purpose: diagnostic_only`、`gate_evidence: false`、work/round/dispatch/授权条目/合同指针、运行时git HEAD/porcelain及源JSON/原件hash绑定、解析出的SERVER/G2/库路径与stat/hash限制、图片来源/板可用判定320成员ABSENT或校验/选取顺序及未传原因、条件传图预约/载荷/核验/部分文件、prompt原文/hash、完整启动argv/进程环境/PID/绑定地址、每加载/HTTP预约与送出起止/分类/图片hash/HTTP码/rc/超时/原响应、额外内部预热发现、统一UTC/monotonic/截止/余额/最后监督尾差、双du基线/每次采样/较大占用/受控投影/外部增长UNKNOWN、技术日志限、失败原因/未执行动作、TERM/KILL/wait/端口释放及清理归属。不得写passed_candidate/verdict或AC满足字段；完成/失败仅用描述性`diagnostic_outcome`记录执行事实。

Implementation交接仅给该目录/receipt指针与实际资源计数，状态板Log只可记“诊断执行及计次待核/已核”指针，**不写性能数值/正式门读数**。接受核的是授权内资源账与原件留存，不能将诊断结果提升为S3/AC-7或正式报告；未来要正式证据须另有合同/额度/停点，诊断不得在正式运行间用于调参试数。

本轮合同可执行，无新增必需用户决策；并行未答B-W-TRT-RESULT/B-LOCAL-EXCLUDE-TRANSFER仅在§5保留推荐/原文，不阻塞本批，也不代表用户已同意。Overall REVIEW_PASSED/Lifecycle ACTIVE与全部历史限制保持；本轮consumed=none。

open_items: none

### 阶段B3b诊断冒烟核清（2026-10-05，Acceptance；资源收据核清）

登记轮次 `阶段B3b诊断冒烟核清`；Dispatch-Id `P1-ENG-JET-001-阶段B3b诊断冒烟核清-20261005T220518Z-28b5`。owner=Acceptance，范围仅本机保留原件只读核清与提案/状态板增量写入；不联网核资料、不SSH/触板、不import包、不运行diag.py或测试。授权依据为账本同日「用户签发官方 base 3b 诊断冒烟…；3c 停在补充预检之前」用户原话及上述合同§1–7。本轮不是D/C/R轮，不签额度、不代录用户原话、不签独立verdict、不改AC。本轮consumed=none；下面数值只核资源使用，不是性能/验收证据。

#### 1. 原件闭集与一致性

本机诊断目录运行时由实现派发 `finished.report` 的claims定位（`docs/evidence/supervisor-dispatch.jsonl` 中 round=阶段B3b诊断冒烟执行），以下相对文件均在该目录，实际路径不另抄为手维护标识：`receipt.json`、`wallclock_end.json`、`plan.json`、`calls.jsonl`、`budget.jsonl`、`raw/`、`diag.py`、`started_utc.txt`与`run.lock`。未改这些原件，也未搬入git或docs/evidence。

- 现算receipt SHA与wallclock_end的receipt_sha256相同；现算脚本/计划SHA与receipt的script/plan字段相同。input_binding的构建/传板/assets/a7纯参照/源码归档JSON、归档实体，authorization的账本/提案及prompt/relay来源现算SHA均匹配对应收据。SHA保留在机器原件、运行时解析，不手抄进本节。git_pre/post HEAD一致、porcelain均空；实现提交由上述finished记录解析，其diff只改状态板，未写docs/evidence。
- calls为28行、14个start与14个end，一一按seq配对；14组stdout/stderr现算字节/SHA与end记录符合，12个非流式调用的rc文件与记录符合，两个流式退出码由end及cleanup相互印证，全部rc=0。流式调用没有单独.rc文件，原件形式据实保留，不补造。全部raw两流合计112,178 B；服务两流6,393 B≤64 MiB，各响应及POST正文均≤1 MiB。
- budget为9行（caps+1加载+7请求），bseq递增；加载预约与server.load_reserve、7请求预约与requests逐条相等，均早于对应calls.start及送出。plan的n≤3/1加载/1+2n≤7与冻结n=3、执行顺序符合，未见重试/重定向/额外HTTP或内部预热调用。receipt的purpose=diagnostic_only、gate_evidence=false、diagnostic_outcome仅描述执行；无passed_candidate/verdict/AC满足字段。
- **唯一计数不一致勘误**：receipt.counts.ssh_invocations=12与实现报告相同，但calls还有seq3 server、seq4 boardmon两条ssh-stream，argv均为/usr/bin/ssh，实际共14次。diag.py的_start_call仅kind=ssh递增ssh_n，漏了ssh-stream；本节记账采用14，不改原件/派发报告。它不增加加载/HTTP/传图计数；本批合同未设SSH次数封顶，也不借预检一次SSH额度，因此不是新增资源类别越界，但不记收据所有字段完全一致。

#### 2. 逐维度资源账与执行边界

| 维度 / 合同 | 已核事实、已用与未用 / 限制 |
|---|---|
| 加载≤3 / 固定计划1 | budget在server启动前预约1；仅1个server会话与同一PID，加载1/3，不见重exec/自动重启。未用2次随本批结束不可执行/转用；不得以启动成功回退计次。 |
| 请求≤60 / 固定1+2n≤7 | 健康GET1、预热POST3、诊断POST3，共预约7、可核curl送出7；顺序0/100/200后同序重复，重复指向请求2/3/4。7次HTTP200、curl rc0，6次正文非空/finish_reason=stop仅作执行事实；不调用正式解析器/评分。不见内部预热，服务日志恰6个图像task；未用53次不转成重试或下一批。 |
| 统一墙钟≤3,600 s | 起点取目录birthtime与started文件较早者22:01:21Z，脚本到22:03:08才启动，准备阶段约107 s没有从首次加载重置。receipt记录135.669 s，wallclock_end至22:03:36.671854Z为135.672 s，双记录相符；可核余额3,464.328 s。UTC起点映射到monotonic绝对截止、请求/连接受同一余额限制，收尾预留60 s。本机最后fsync/驱动及caffeinate退出在尾文件之后，完整退出尾差UNKNOWN；批外准备无计时，故不能把135.672 s称完整全流程墙钟或严格上限已证。余额不续用。 |
| 板新增≤1,000,000,000 B / 双du取大 | eng-jet基线表观9,508,662,094 B、分配9,662,615,552 B；DIAG事先不存在。mkdir/26个在途样本/最终样本的DIAG表观均0、分配均36,864 B，eng-jet表观正增长0、分配正增长36,864 B；按合同四者取大，采样较大口径及终值36,864 B。9个空目录各4096 B/8块、权限700，未见本批文件/缓存/.part。原表观0按原文保留，不据此排除目录元数据，较大分配口径覆盖本次目录占用。最大受控投影134,254,592 B<700,000,000 B，df全程远高于1.1 GB前置/1 GB保护；未见越限样本。相对上限的采样余量999,963,136 B不是瞬时峰值或可转用额度；CUDA限制遵守程度、采样间增长和DIAG/eng-jet外SSH/PAM/atime/journal等不可归属增长UNKNOWN，不声称板物理总增长已封顶。 |
| 条件传图≤10件/≤20,000,000 B | raw前置320个具名a7成员逐项为普通非链接、非空、read_bytes=size、640×480，哈希逐项与a7纯参照符合，选0/100/200；原件未读sidecar/gold。已有图可用，条件未触发：图片预约0、实传0件/0 B、scp0；未用10件/20MB随本批结束作废，不含模型/代码/盲材料传输。板内base64/data URI不冒充Mac传板。 |
| SSH / 重试 / 前置 | SSH实际14（12普通+2流式），scp0、重试0；14组固定SSH选项/既有有线目标与plan/relay来源一致，固定22符合合同。headless、18081空闲/无并驻本项模型、工具/余量/输入前置在raw001可核；SERVER类型/72,424 B及同目录库/链接符合构建JSON，G2字节/sha与传板及账本绑定符合。SERVER历史二进制无hash，现hash仅本次事实，不补称历史内容身份已证。共享槽位快照无yes行，单写者派发日志可核；本机权限沿既有窄规则，不以过期transfer排除条目授权本次。 |
| 命令、argv / 环境 / 输入 | plan、calls完整argv、raw005的cmdline/cwd/environ及父timeout逐字相合：固定loopback18081、parallel1/ctx2048/gpu99/fit off/no-warmup/no-webui/no-cache-prompt/cache-ram0/cache-reuse0/offline；九项进程环境及CUDA128MiB符合，未改HOME/LD_LIBRARY_PATH/系统设置。板Python用-I -S -B纯标准库在内存组装原JPEG+prompt，prompt字面来源/现hash/传送后hash相同，surface=the car、g4=false、unity-v2；temperature0/max_tokens160/stream=false/cache_prompt=false，curl禁代理/重试/重定向。额外-s/-S/-o/-w/--max-filesize仅捕获与封顶输出，属于合同允许的原文保留形式，不改请求语义。 |
| 停止 / 收尾 / 删除 | 固定计划结束即TERM仅本批PID，raw013记约1 s退出、未用KILL；server/boardmon会话wait rc0，raw014 pid alive=0、ss18081空、端口释放；未断连后重新兜底登录。DIAG只留下9个目录，无删除/移动/覆盖既有件命令；旧G2/构建/库/W/sysvenv/图片/缓存不动，没靠清旧件抵销。原件/脚本及实现diff未见docs/evidence写入。最终驱动退出尾差仍按上行UNKNOWN，不把服务已停等同全部监督已闭。 |

记账结论：**加载/请求/传图已用可核，板占用与墙钟仅在上述可核采样/尾文件范围内未见越限；不追认严格全合同符合。** 全部未用加载/请求/墙钟/占用/条件传图许可随固定单批计划完成收束、作废且不转用；不能据未知量把已用退回，也不能把未知量当0、续跑补测或迁移到3c/C2/S4/S5。没有发现额外板运行/安装/下载/部署/系统设置消耗；此结论限本机保留调用原件与实现自报，不是假称重新访问板端。

#### 3. 自报偏差逐条归因及记账影响

1. **监测间隔：口径勘误兼执行形式偏差。** 自报最长1.014 s、19/25超过1 s来自receipt.occupancy.mac_receive_gap_s，diag.py用Mac收取样本monotonic算差；不是板采样间隔。raw004的26个板UTC重算25个间隔最长0.955984131 s、0个>1 s；板在途相邻采样本身未见超1 s。Mac接收确有超过1 s，且mkdir基线至首在途板样本间隔1.327063369 s，启动衔接没有证明全程每≤1 s；驱动容许采样陈旧3/5 s的保护也不等同合同≤1 s。归为监测执行形式偏差，不增加加载/请求次数，不可据“均很小/未报警”豁免或证明瞬时占用封顶；资源原读数照记、全程监测严格符合不成立，未来要重跑须新合同/额度。
2. **批外本机只读：超出合同规定的批内准备/具名读取形式。** 开批前python3 --version/which/git check-ignore、Mac a7目录ls及8件额外源码tar -xzOf（server.cpp、server-http.cpp、clip.cpp、mtmd.cpp、common.cpp、log.cpp、server-task.cpp、server-common.cpp）均未触板、未改设置、未解压落盘，性质属本机只读准备；但合同§2/§5要求准备计入本批，§4源码依据只具名三件，不能按自报将批外动作排除后声称全合同符合。额外源码读取超出具名读取闭集、计时/收据形式偏离；未发现越用户设备/模型额度或新增消费类别。无批外原始起止收据，不造时间/字节0，批外准备时长UNKNOWN；加载/请求/传图已用保持，不补跑。目录建立后启动前改diag.py匹配式落在约107 s批内准备中，现脚本hash为改后并匹配，未改服务argv/参数且未运行假树/测试；属窄驱动准备，不是额外模型尝试。运行中/完成后只读calls/tail/receipt是观察及交接汇总，不新增HTTP/SSH；运行中含在统一窗口，完成后汇总不伪作新诊断，最终监督退出UNKNOWN仍保留。以上批外动作范围来自finished.report自报，现脚本hash不反证其发生或完整性。
3. **日志警告：原参数执行下的诊断事实，非自行扩大范围。** Qwen-VL建议image-min-tokens1024、无API key/CORS全开均原样保留；未加token参数/键/外部绑定，不因URL文字认定外联。raw005只证本次127.0.0.1绑定，不能推广到其他场景。raw003另有control-looking token、cache-idle-slots禁用与退出时CUDA compute buffer期望不一致警告，一并保留，不将“只有两条警告”作为结论。未见额外内部预热、下载、cache命中或服务错误调用；graphs reused文字本身不等于图像/文本缓存命中。没有完整实际grid/merge/image-token出口，不认证token=300或无缓存性能，不改参数追试；请求仍7、加载仍1，HTTP非空不等于正确定位/正式解析通过。

上述归因为本轮资源合同核清，**不是复核finding、CLASS分级或既有返工度量**，不新增AC/BC/SCOPE_GAP或blocks/release，不改R1-5/6 OPEN、历史STOP或门值。下一步及用户具名决定、推荐理由/可回复原文只见「阶段B预检答复落实」§5现行段；B-W-TRT-RESULT/B-LOCAL-EXCLUDE-TRANSFER仍未答，3c仍停在补充预检前。诊断原件不得转贴为AC-7/S3、B1/B2通过或任何正式性能/门证据。

open_items: none

### 阶段B偏差处置落实（2026-10-05，Acceptance；零消耗文档落实）

登记轮次 `阶段B偏差处置落实`；Dispatch-Id `P1-ENG-JET-001-阶段B偏差处置落实-20261005T221622Z-4dcb`。依据 `docs/authorizations.md`「2026-10-05 P1-ENG-JET-001 — 用户答复偏差处置按推荐：B-3B-RESULT 与 B-W-TRT-RESULT 保留数据与偏差、不追认全符合、不追责（supervisor 会话代录）」用户原话、上文语境及(a)–(d)；读法与原话有出入以原话为准。本轮只读本机文档并增量写提案/状态板，不是D/C/R轮，不签额度、不代写用户原话账本、不跑测试或包代码、不联网取证、不SSH/触板。按派发要求提交/推送；consumed=none。

#### 1. 短答指代核对

用户短答为「偏差处置按推荐，保留数据不追人」，不是§5可回复原文的逐字复述。账本记录的上文同时列出B-3B-RESULT、B-3B-NEXT及仍未答的B-W-TRT-RESULT/B-LOCAL-EXCLUDE-TRANSFER；其中以“偏差处置”为事项的恰为两个RESULT，NEXT是下一步，LOCAL是设置撤销。§5两项RESULT推荐均为保留数据/资源账、偏差与UNKNOWN，不追认全合同符合；与“保留数据”一致，没有互斥推荐。因此可无歧义对应B-3B-RESULT和B-W-TRT-RESULT的推荐，接受该两项；不把“按推荐”扩大为所有未答事项。无新增指代歧义决策项。

“不追人”的本次落实口径与「阶段B3b诊断冒烟核清」§3末段及「阶段BTRT预检核清」§2本机假目录干跑项一致：偏差保留为事实/合同记录，不对这两批追加独立finding、CLASS分级、SCOPE_GAP、返工或返工计数，不改既有派发报告与原件。该口径限本次两项偏差，不抹去原事实、原失败或既有R1-5/6 OPEN债，不给未来执行一般豁免。

#### 2. 两项推荐已落实

- **B-3B-RESULT：用户已选推荐、已落实。** 采用「阶段B3b诊断冒烟核清」§1–3的既有资源账：加载1次、请求7次、传图0、SSH14次、重试0；原汇总漏计与监测口径勘误仍按该节记录，不回写原收据。原件、执行形式偏差、批外准备时长/最终监督退出尾差/瞬时占用等UNKNOWN保留。不追认为严格全合同符合，不进证据，不记AC-7/S3或门满足；已用计次不退回，单批未用额度作废、不转用，不追加诊断或补测。
- **B-W-TRT-RESULT：用户已选推荐、已落实。** 采用「阶段BTRT预检核清」§1–2的已核静态读数，整批/SSH均1/1用尽、重试0，未用额度作废、不转用；原COMPLETE仅保留当时执行状态，不追认为严格全合同符合。固定端口、批外干跑、单目录落盘等执行偏差及计量UNKNOWN保留，原W现场与STATIC_CHECK_FAILED不豁免；不记安装闭集冻结、运行通过或门满足，不追加SSH或补测。

两项仅按用户选择落实既有推荐及事实记录，不新增AC/AC修订、finding/SCOPE_GAP、返工/计数或blocks/release，不改任何原件、派发报告、既有verdict或门。§5原推荐/可回复原文保留为指代来源，已答两项不再呈交用户重答；核清节中“仍未答”是当轮快照，现行状态以§5和本节为准。

#### 3. 保留待决与停点

B-3B-NEXT、B-LOCAL-EXCLUDE-TRANSFER、B-CLOUD/B-CLOUDDEP仍未答；推荐、理由与可回复原文唯一入口为「阶段B预检答复落实」§5（云题沿其所指「阶段B准备审核」§5）。不因本条启动C2准备派发、云作业或删除设置；3c仍停在B-W-TRT-SUPPLEMENT之前，安装/链接/运行0，等用户云端决定。未签维度均0，本轮不签任何额度。REVIEW_PASSED/ACTIVE、S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN及AC-7/8/9 NOT_RUN保持；不是阶段B验收、B1/B2通过或DONE。

open_items: none

### 阶段B基座提示调试资源核清（2026-10-06，Acceptance）

本轮为用户直接指定的资源账审核与新诊断合同落实，不是 D/C/R 轮，不跑测试、不签独立复核。完整读取累计账全部 3,763 条，逐批对照 9 份 receipt、plan、calls、请求/原始响应及清理原文；原件只在 `outputs/eng-jet/P1-ENG-JET-001/stageb-base-prompt/`，不入证据链。本节核资源及可核执行事实，不复算或认可 conclusion 的性能/采用建议。

#### 1. 累计账与批次收据

| 维度 | 核实值 / 原签上限 | 核清依据与限制 |
|---|---|---|
| 传板 | 714 件 / 800；36,973,077 B / 45,000,000 B | prep 的 8 个 tx 预约与 8 次 scp 均一致、rc=0；收据板端 admitted 共 714，missing_or_bad 为空。本机两盲文件与 dataset-manifest 字节/hash/行数一致；714 JPEG 全部现算 hash 等于文件名，DEV 322 与 HOLD 392 张无交集。 |
| 加载 | 8 / 15 | 8 条 load 预约与 8 次 server 启动调用一致；首批 ready 核验前因日志告警停，仍计 1 次，不因 receipt.server 尚未填充而免计。其余 7 批各 1 次，无崩溃续跑。 |
| 请求 | 3,430 / 10,000 | 7 个健康 + 3,423 行预测：5×441 DEV + 2×609 HOLD；每批 seq 连续。7 批 rows、outputs 与 raw/responses 的行序、row_id、seq、正文身份一致，HTTP 均 200；首停批请求 0。 |
| 板端累计墙钟 | 账面 8,254.1 s / 43,200 s | 从全部 batch_start/batch_end 现算 8,254.097 s，逐批累计快照一致；结束早于合同截止。但目录先创建再取 t0，最后一次 receipt 保存又在 batch_end 后，创建/最终写盘尾差未计且原件不能补证，**完整墙钟 UNKNOWN**，不认证严格全程符合。 |
| 板新增占用 | 可核采样累计 38,846,464 B / 1,000,000,000 B | frame/root 38,551,552 B + 8 个服务 DIAG 各 36,864 B；9 批是 1 prep + 8 run，并非 9 个独立服务 DIAG。全部末采样与累计快照一致；相邻占用采样最大间隔 30.478 s，低于 60 s。瞬时峰值/不可归属系统外写 UNKNOWN。 |
| 提示与确认 | 新版本 P1/P2 共 2 / 8；HOLD P0 与 P2 各 1 次 | plan 与 receipt 同值、提示文件现算 hash 与预约一致；7 批完整行序匹配各自盲文件。加载/参数组合变化已记账，没有重复 HOLD 版本。 |
| 收尾 | 8 次服务均已停、18081 释放 | 8 份 cleanup 的 pidcheck=alive=0、port_released=true，原 final-check 对应；全部 calls 的结束 rc=0。prep 不启服务。删除声明 none，末清单只含本批目录；不能由窄目录清单推出全板严格零写入。 |

前置、frames-check、stdin worker 原件及固定五个盲字段支持本次输入隔离；gold 只在 Mac 评分。独立现算的累计项与各份 tally_after 无冲突，不改原账、receipt、summary 或 conclusion；没有发现**已记录维度**超额。资源核清不等于全合同符合，不回退首停批加载计次。

#### 2. 偏差与确认集纪律

- 首停批把 GitHub 文档链接告警当成 NET；现 driver 把普通 URL 单列 net_weak，真正下载/外联征兆仍停。原首批与后七批 script 身份不同且首批停止保留，属于诊断驱动修正，消耗不退回；只凭日志不足以独立证明全程无外联。未留存旧驱动完整副本，不能把 script hash 差异称为已核完整 diff。
- P0 HOLD 在 P1 后、后续 DEV 调参前执行；后来的 JSON/image-min/P2 调整仍在 DEV，HOLD 只再确认 P2 一次。原件能核次数/顺序，不能独立证明每次同意及改法从未参考 HOLD 汇总；这些仅有实现 conclusion 自报，**不追认确认集完全未受影响**。本次只核账，不采纳或转用提示。
- P2 只允许 unique/none，区别于正式三态 prompt v2；不得据其诊断收益静默改变正式协议。conclusion 的“量化与上板不改主指标”不经本轮核账升级为等价性或门结论。
- 用户已要求收尾，旧批停止推进；未用加载/请求/传板/版本/确认名额不覆盖下面 C2 追加。Overall REVIEW_PASSED / ACTIVE、AC-7/8/9 NOT_RUN、3c 停点与两条 OPEN 债保持。

### 阶段BC2JSON诊断答复落实（2026-10-06，Acceptance；零消耗）

登记轮次 `阶段BC2JSON诊断答复落实`；Dispatch-Id `P1-ENG-JET-001-阶段BC2JSON诊断答复落实-20261006T221619Z-5eb6`。唯一答复依据为 `docs/authorizations.md` 2026-10-06「P1-ENG-JET-001 — 用户答复 C2JSON-DRIVER_SELF_CHECK_STOP：JSON 约束诊断到此结束（按接受推荐；supervisor 会话代录）」：用户以短答采纳「阶段BC2JSON诊断核清」§5推荐项；账本区分用户原话与接受拟稿，本节不代写账本或冒充逐字原话。仅落实答复与盘点，不是D/C/R轮，不消费新verdict、不新增AC或修订、不签额度、不更新里程碑证据；不联网取证、SSH、触板、下载、安装、模型/第三方包运行或测试。consumed=none；仓库pull/rebase及push仅按本轮派发的提交同步要求执行。

#### 1. C2JSON-DRIVER_SELF_CHECK_STOP：已答结束的落实

**采纳并落实的推荐项原文（接受拟稿，用户已采纳；不是用户逐字原话）：**

> C2JSON-DRIVER_SELF_CHECK_STOP：本次JSON约束诊断到此结束；保留attempt-1失败原件、已核资源账、驱动自检误报、监督/计时偏差及UNKNOWN，不追认严格全合同符合，不进证据、不记AC-7/8/9或门满足；未用余额作废、不转用，不追加驱动修复、加载、请求、传输或补测。3c仍停，S5推后未签保持。

本诊断信封全部未用余额现依用户答复作废；不把失败已用计数退回、不转到其他诊断/正式范围，不挪用第2加载。原件及已核账沿「阶段BC2JSON诊断核清」§1–4保存，本轮不改driver、plan、checkpoint、收据、占位评分或任何outputs原件；占位NOT_RUN不能成为JSON效果结果。旧C2越界、其他诊断偏差及UNKNOWN继续保留，不以本次结束追认或补签。该答复只结束本次JSON诊断，不结束整个JET工作项；Overall `REVIEW_PASSED` / Lifecycle `ACTIVE`保持。

#### 2. 现行未闭义务与保留限制（接受处置推荐，非新授权）

以下是尚未完成或未来复用前必须承接的义务，不是本轮待执行清单。每条处置推荐均**非已签的新决定**；可回复原文只供用户另定方向时选用，不重问已定的3c/S5顺序、云结束、RESULT记账或临时条目删除。

| 未闭义务 / 来源 | 接受推荐与理由（非已签） | 可回复原文（接受拟稿，非已签；无需逐条重答） |
|---|---|---|
| 正式AC-7/8/9仍NOT_RUN；阶段B消费前代码与消费后证据的B1/B2相称停点未完成；来源：§4、AC-14修订1–3及「阶段B预检答复落实」§4–5 | 暂不推进正式验收，保留未完成项；诊断明确不进证据，A候选的R3/UNITY_NA只覆盖A，不能替代B的实现自证、C/R与板端证据。部署代码束、盲材料/基准与隔离、完整传输/加工/评分峰值墙钟及真实测试/复核消耗仍缺合同或事实，未签保持0。 | 「保留AC-7/8/9未完成及阶段B停点义务；正式验收、部署、数据加工/评分、传输、测试和真实复核消耗暂不推进，后续范围与额度另定。」 |
| 补丁未上板、未在真实断链/重连下验证；S1/S2 STOP、SR额度耗尽、原全套与窄修替代覆盖限制；来源：「R3消费：新候选通过与用户剩余路径」 | 保留负结果及未实测限制，不把独立代码复核当补丁后板端验证；不借SR或测试旧余额重跑。未来重建ledger前须先由获批实现补SUB:6保留支持，该节非finding观察也随复用携带。 | 「保留S1/S2 STOP、补丁未上板和测试覆盖限制；不追加SR/全套，不重建ledger；日后复用前按获批合同承接R3消费节的限制。」 |
| R1-5 OPEN：Carrier跨CPU/MPS差异、未知差异形态、比较后未执行断言与真实工厂覆盖；唯一债入口：`docs/implementation-status.md`「范围外已知缺陷」R1-5 | 保持OPEN，未来验证跨设备一致性或复用工厂覆盖前具名承接；本项合同未覆盖这些差异，不能以JSON诊断结束销账。 | 「R1-5保持OPEN；未来跨设备/工厂覆盖验证先纳入获批合同，本轮不补测、不销账。」 |
| R1-6 OPEN：scene006资产绑定失败后的行为未验证；唯一债入口：同上R1-6 | 保持OPEN，未来获批环境验证承接资产绑定及后续断言；不向主树补资产或借本项重跑全套。 | 「R1-6保持OPEN；未来环境验证承接资产绑定与后续断言，本轮不补资产、不重跑全套、不销账。」 |
| 3c条件提升点：TRT最小闭集/库映射未冻结、W现场STATIC_CHECK_FAILED与系统site/numpy冲突未修；S5推后到快层调好之后；来源：「阶段BTRT预检核清」「阶段B安装核清」及现行预检答复§5 | 沿已答安排继续停在补充预检之前，安装/链接/运行0；S5保持NOT_RUN/未签。3c触发判据须待后续闭环曲线再定，S5须先有快层条件与独立具名合同/额度；本轮不再呈现预检、安装或共驻签发题。 | 「3c条件提升停点、W失败现场与未冻闭集保留；S5按既定顺序推后未签，不追加预检、安装、链接、运行或共驻。」 |
| 各诊断/静态批次原账、停止越界/执行偏差/UNKNOWN与原件保留义务；来源：预检答复§5指向的各具名核清节，JSON为「阶段BC2JSON诊断核清」§1–4 | 保留而不追认全合同符合；完整监督/收尾计时、瞬时占用等UNKNOWN不补0，不为消除UNKNOWN补测。BUILD-LLAMA/INSTALL-W及已收束诊断额度不转用；未来若另开诊断，其驱动自检、加载期监督、采样周期、累计计时与收尾计量须在新具名合同核清，不能沿本信封续修。 | 「原件、原账、越界/偏差及UNKNOWN原样保留，不追认、不转证据、不转余额；新诊断若需另开，先定范围和保护合同，再另签额度。」 |

未新增finding、返工计数或债条目，未改已有复核结论/归因/两条OPEN债。B-CLOUD/B-CLOUDDEP结束、不租云及B-LOCAL-EXCLUDE-TRANSFER本人删除已核实；B-C2-RESULT和本次C2JSON结束均已答落实，P2不采用/不另立项，以上全部不再待答。

#### 3. JET-NEXT-DIRECTION：等待用户另定方向

**已签范围内已无可执行动作，等待用户另定方向。** 当前没有尚未落实的旧用户答复；唯一新待决事项是整个JET工作项接下来如何安排，不能把本次诊断结束推为整个任务收口或新额度。现行用户入口仍为「阶段B预检答复落实」§5对本节的指针；owner/status只写状态板交接行。

**接受推荐（非已签）：暂时暂停JET工作项，保留全部原件、负结果、未完成验收与复用义务，待快层条件或新的具名范围明确后由用户决定恢复。** 理由：没有可用执行许可；3c/S5已明确推后，继续挂实现动作会误导接手者，尚未收到整个JET工作项的终止指示；暂停与保留后续探测安排相符。暂停只冻结推进，既有verdict/门与债不变；本轮不自行改Overall/Lifecycle或暂停交接。若用户更希望终止，可另定部分交付收口，不能记DONE；若用户需要新的JSON诊断，应先另定同时覆盖已知保护缺口的具名范围/合同，再逐维度签发，不借已作废余额。

**唯一需用户的新决定及可回复原文（接受推荐、非已签）：** 「暂停P1-ENG-JET-001，保留既有候选复核、原件与资源账、历史STOP、所有偏差/UNKNOWN、AC-7/8/9未完成、补丁未上板、R1-5/6 OPEN及未来复用义务；3c和S5沿已答停点与顺序保持。此次不收口、不签新额度、不恢复诊断或板操作；待我另定具名方向再决定恢复。」此拟稿只提请任务安排，不重新请用户回答已结束的C2JSON、云、3c或S5选择；答复入账并由接受落实前，门与Lifecycle均维持原值。

open_items: none

### 阶段BC2JSON诊断核清（2026-10-06，Acceptance；零消耗）

登记轮次 `阶段BC2JSON诊断核清`；Dispatch-Id `P1-ENG-JET-001-阶段BC2JSON诊断核清-20261006T213555Z-2777`。本轮合同为「阶段BC2JSON诊断授权落实」§1–6，授权为账本2026-10-06「用户答复 B-C2-RESULT 按推荐；签发『C2 Q4 加 JSON 约束』板上 609 行诊断…」(b)(c)(e)。只读本机原件，以系统Python标准库读取JSON/AST及计算hash，不执行或import `c2json.py`，不联网取证/SSH/触板/下载/安装/模型或第三方包/测试。consumed=none；不是D/C/R、不签独立verdict、不新增AC或修订、不签额度、不代写用户原话。

#### 1. 原件与逐项身份

原件根NEW=`outputs/eng-jet/P1-ENG-JET-001/stageb-c2-json-diagnostic/`，批目录BATCH从NEW/checkpoint.json的batch唯一解析；以下路径相对NEW或BATCH，不手抄UTC目录或派生SHA。核读summary.md（含实现补记）、checkpoint.json的stop_attribution/needs_user、budget.jsonl、c2json.py、BATCH/plan.json、steps/0-MAC_BIND/receipt.json、attempt-1/attempt-receipt.json、attempt-1/steps/{1-BOARD_VERIFY,2-DIAG_SETUP,3-LOAD_AND_QUERY,4-STOP_AND_RELEASE}/receipt.json、attempt-1/calls.jsonl与raw原文、steps/{5-MAC_PAIR_SCORE,6-REPORT}/receipt.json及占位评分文件。实现报告来源为 `docs/evidence/supervisor-dispatch.jsonl` 中派发 `P1-ENG-JET-001-阶段BC2JSON诊断执行-20261006T211656Z-a2d6` 的finished.report；报告仅是核对入口，以下结论来自原件。

plan bindings与MAC_BIND收据bindings相同；plan现算hash与MAC_BIND plan_sha256相同，驱动现算hash与七份步骤收据driver_sha256相同。BOARD_VERIFY逐项核清如下，不能把其diagnostic_outcome=DONE泛化为整批符合或模型可用：

| §1对象/前置 | 本轮核清与原文指针 |
|---|---|
| OUT、旧服务收尾 | bindings.old沿旧state.board.step及唯一SCORED收据解析；旧outputs/predictions现算hash与bindings及旧score inputs一致，旧服务停止/释放链保持。旧件只读，旧余额不并入。 |
| MODEL | BOARD_VERIFY precheck.blocks.model普通文件/字节/hash与plan bindings.model、旧state.q4、旧board server.argv/transfer链相符；model_real=realpath_same，本机Q4现算hash相同，不是官方base Q4。 |
| MMPROJ | precheck.blocks.mmproj原文与bindings.mmproj.old_precheck_out相同，字节/hash及路径与stageb-transfer唯一官方F16对象、旧board路径/argv双解析一致；mmproj_real=realpath_same。 |
| SERVER与库 | SERVER普通文件/字节/hash与bindings.server及旧board server_sha256_now、build-rerun stat一致；server_real=realpath_same。bindir文件名/类型/大小/链接及bindir_resolve排序后与旧原文相同。库没有历史hash，只核这组元数据与链接终点，不补造库内容未变的证明。 |
| HOLD盲行与392帧 | MAC_BIND盲文件现算字节/hash与dataset-manifest、旧state一致，严格五字段、609唯一原序。raw/002-precheck.stdout有392件HOLD及3件预热帧：HOLD逐件普通非link、realpath_same、640×480，hash=文件名=Mac upload原件现算hash，字节也与Mac原件相同；frames_real=realpath_same，缺失/坏件0。板复用帧；本次worker停止前未收到新盲行/schema/template stdin，不能称已完成线上载荷发送。 |
| C2 bf16、gold、旧无约束Q4 | MAC_BIND绑定同一C2 train-summary selection与eval-summary selected_adapter/job_b；本机bf16、gold及旧Q4预测/outputs现算hash相符。blind/gold/bf16/旧Q4与本次占位预测/同行表均609唯一同序；不使用base bf16，不重跑评分。 |
| prompt、schema、评分器 | 仅AST取prompt_v2固定段重建模板，模板/文件hash与bindings相符；plan的609 expect_text_sha链沿旧outputs。S1 schema原文字节/hash与bindings相同，结构与先前两份S1 plan相同；固定temperature/max_tokens/stream/cache_prompt/response_format语义与冻结规范hash一致。score inputs引用冻结parse/evaluate口径，未改冻结文件。 |
| 板身份与环境 | precheck id为原SSH用户、UID1000、原HOME、aarch64；multi-user.target、display-manager=inactive、gui_procs=0；具名12工具有路径，无MISSING。ss无18081、modelprocs为空；df/free与eng-jet双du有原文，新根/批目录ABSENT。BOARD_VERIFY的问题集为空。随后新目录权限700，服务PID/argv/回环端口/cwd核验相符。 |

#### 2. 资源账（失败共账；余额不是续跑许可）

budget.jsonl有11条reserve及11条settle，一一对应、无悬空/重复/孤儿结算；10次SSH动作（7次call、3次长会话）的命令/stdin预约均早于calls start/spawn，另1条为启动前加载预约。加载即使本次确认行全部未运行也不退款；worker失败的命令字节照计。各步骤tally_before/after到attempt收据、checkpoint及REPORT相接；MAC_BIND和MAC评分/报告不增加板账，不用旧账或维间抵扣。

| 维度 | 已用 / 硬上限 | 余额与核算边界 |
|---|---|---|
| 板加载 | 1 / 2次 | 1次；加载预约在server spawn之前，ready与原stderr相符。剩余第2次原只供§5服务故障回退；本停止不适用，当前不可动用。 |
| 板HTTP请求 | 0 / 1,300次 | 1,300次；无请求reserve、worker stdin实际0 B、无请求原响应/行送出。请求0不免掉加载/命令消耗。 |
| 板累计墙钟 | 账内11.827 s（收据四舍五入11.8） / 5,400 s | 账面5,388.2 s；epoch与monotonic差均11.827 s。board_phase_end之后attempt收据/checkpoint写盘和监督退出尾差UNKNOWN，因此完整已用=账内时长+未核尾差，完整可执行余额尚未核清，不能拿5,388.2 s当严格可用余额。 |
| 板新增占用 | 可归属累计采样45,056 / 100,000,000 B | 账面99,954,944 B。写前eng-jet基线、mkdir投影200,000 B、加载投影24,777,216 B均在动作前；四次occ均45,056 B，分配du与eng-jet正增长一致、没有下降抵扣。末次本批表观du原文为0、分配du为45,056，按较大口径保留，不由0推断无写入；瞬时峰值/eng-jet外不可归属写入UNKNOWN。 |
| Mac→板 | 实际61,666 / 10,000,000 B | 9,938,334 B。10次tx预约总326,839 B；worker先预约268,493 B，实际仅命令3,320 B+stdin0 B，失败后有确证结算，未送出的stdin不假计为已传、未退款已传失败字节。其他会话/命令逐笔加和符合收据。SSH/TCP物理封装UNKNOWN。 |
| 板→Mac（另记） | 123,819 B | budget.rx总和=raw全部stdout/stderr现算字节总和；不占单向Mac→板额度、不抵扣它。 |

新增板目录保留；以上是已核计次/有效载荷/采样口径，未见可核的数值额度超限，**不据此追认完整计量或保护符合**。完整墙钟/瞬时占用UNKNOWN及下一节执行偏差保持。云/下载/pip/构建/模型加工/模型帧重传/快层共驻/正式ID/API/Play为0。

#### 3. 停止归因、释放与执行偏差

**首行误报属实，实际归因为驱动自检执行错误。** c2json.py的cmd_bind用params_for(S1)插入序生成首行，再由write_json(sort_keys=True)落plan；start_worker重读plan.request_params后以stdin_line缺省键序重建，逐字节sha不再相同。标准库只读重建两份首行都是2,447 B，bind顺序重建hash符合plan.payload.worker_first_message_sha256，重读顺序重建hash不符合；两个JSON对象相等，规范化sort_keys/紧凑分隔sha相同且符合plan.request_params_sha256。模板和schema原文字节/hash未变。不是板模型、schema或HOLD发生INPUT_CHANGED；保留原停止码，不改原收据。

**0请求有执行链支持：** start_worker在send_raw(first_msg)之前抛STOP；STOP_AND_RELEASE sessions.worker的in_B=0、out_B=0，raw/008-worker.stderr为首个sys.stdin.readline空串的JSONDecodeError、worker_rc=1；HTTP仅可能在成功读取首行后再读命令的循环里执行。本批无健康、预热或609确认请求，无请求reserve；server原stderr只有ready/listening与退出、无请求记录。609占位均exec_status/parse_error=NOT_RUN、status_pred/raw_output=null，原序保留。评分里的零成功/配对差仅为未执行占位的算术结果，**不构成JSON约束的效果、解析成功率或Jetson性能结果**；34条旧SCHEMA_ERROR本次均未测。

**服务释放有原文：** raw/009-stop-server.stdout核comm=llama-server和本attempt cwd后TERM，term_rc=0、still_alive=0，无KILL实际触发；raw/010-final-check.stdout的ss18081为空且rc=0、pidcheck alive=0且rc=0，服务/monitor SSH会话均rc0；不是凭SSH断开推定释放。七份收据驱动hash与当前副本相同，只有一次board_phase_start/一次加载，attempt-2不存在，未改驱动、未续跑。

**停止路径正确，整批执行形式不全符合。** §5将其他执行/核验错误也列为整批停止原因，因此误报码并不授权修脚本续行；实际3停止→4释放→5占位评分→6报告符合失败闭集。不是服务加载超时/退出或确认期间非OOM崩溃，不能套C2JSON_SERVICE_RETRY1。未见停止后自行续行、第二加载或资源数值越界；另有以下具名偏差/限制，不签独立finding、分级或返工计数：

- **监督覆盖/频率不满足§3：** start_server加载后才在load_and_query启动start_monitor，加载等待只查PID/日志/截止，不做周期du/df/增长核；加载至ready这段长动作无所要求的全维监督。两条monitor原board_utc相差1.439742 s，收据1.44 s，超过≤1 s；把sleep设为1 s再叠du/df耗时不能证明周期≤1 s。原summary称“1 s采样峰值”不代表满足频率。
- **完整计时缺尾差、未来计时读法偏差：** board_phase_end先于attempt收据/checkpoint写盘及锁释放/监督退出；原件已标尾差UNKNOWN，不能机械补0。tally用last−first而非分阶段求和、cmd_board以首次epoch+5,400为所有尝试固定截止；本次只有一次尝试不改变已核账内11.827 s，但隔次恢复会误计阶段外间隔，唯一读法见§4。
- **收据/摘要时点：** REPORT收据execution=REPORTED；summary生成时表中6-REPORT仍None，此为生成顺序快照。其summary_sha256只对应后来“停止原因与归因（实现补记）”之前的原生成前缀，现全文hash不同；现算前缀仍符合原hash，支持“随后追加补记”，不称REPORT哈希绑定当前补记全文。原件不回改。
- **既有文件保护：** 10份raw/*.block只含读取、创建本批目录、启动/监督和归属核验后TERM；无删除/移动/覆盖旧板模型/mmproj/库/帧/缓存命令，最终清单仅本批11个目录。驱动唯一unlink是释放本次新建的Mac run.lock，不是删除既有资产；summary追加补记及本批checkpoint状态写入不是旧资产删除。可核执行闭集内未删除既有文件，不能由局部清单证明全板/全磁盘没有无关写入；后者保留UNKNOWN。

#### 4. 墙钟合同问题的唯一读法（解释既有§3，不签新额度）

「阶段BC2JSON诊断授权落实」§3原文是“板端累计墙钟”“两尝试相加不重置”，并要求每板阶段至最终收据写完/监督退出止、Mac阶段耗时另列。唯一读法是：**已用各板阶段完整时长累计 + 新尝试完整板阶段时长 ≤5,400 s**；不按首次板阶段开始+5,400 s建立跨用户等待/已结束Mac阶段的绝对到期时刻。新尝试开始前扣除已用（包括第一次失败及收尾尾差），以剩余量约束该尝试UTC/monotonic截止，不能重开5,400 s。板阶段仍开放时等待Mac、连接/传送/核验/加载/查询/监督/收尾均计入；只有服务/端口/最终收据及监督均结束后，独立Mac评分和用户待决间隔才不计板阶段。边界不可核的间隔不能自行扣除。

实现提出的11.8 s vs首次起绝对截止二选一：选**累计已用+新尝试**，但11.8是四舍五入的已知部分，并非完整已用；尾差未核清前不能给出严格新截止或宣告余额足够。现驱动的绝对截止与last−first跨尝试算法不是合同解释，未来若恢复须先核其符合上述口径；本裁定不自动授权改驱动、恢复或用第二加载。

#### 5. C2JSON-DRIVER_SELF_CHECK_STOP（用户具名决策，非已签）

**答复后索引（2026-10-06）：本节为核清当轮决策快照。用户已采纳结束推荐，落实见「阶段BC2JSON诊断答复落实」§1；以下拟稿/另一项条件说明保留作来源，不再作为现行待答或运行许可。**

**问题：** 是否允许只把首行自检改为规范化比较后，在本次已签五维信封余额内挪用第2次加载，完整重跑一次C2JSON-S1的609行，或本诊断到此结束？第2次加载原为§5服务故障回退所签，本次驱动故障不适用；挪用须用户明确同意，Acceptance/supervisor不得代拍。接受推荐与实现checkpoint的“推荐允许”不同，不改checkpoint原文。

**接受推荐：诊断到此结束，保留失败原件与已核账/偏差/UNKNOWN；未用余额作废、不转用。** 理由：自检误报原因和0请求虽已核实，现驱动还有加载期监督缺口、实际周期>1 s、最终尾差未核及跨尝试计时算法问题；“只修首行自检”不能闭合这些已有合同要求。当前只剩一次加载，直接花掉它不能保证完整尝试，也没有JSON效果结果可保留；不建议把资源余额当修复全部保护的授权。本推荐尚未被用户签发，不自行结束整个JET工作项或作废余额。

**推荐项可回复原文（接受拟稿，非用户已签）：** “C2JSON-DRIVER_SELF_CHECK_STOP：本次JSON约束诊断到此结束；保留attempt-1失败原件、已核资源账、驱动自检误报、监督/计时偏差及UNKNOWN，不追认严格全合同符合，不进证据、不记AC-7/8/9或门满足；未用余额作废、不转用，不追加驱动修复、加载、请求、传输或补测。3c仍停，S5推后未签保持。”

**另一项可回复原文（非推荐、非已签）：** “C2JSON-DRIVER_SELF_CHECK_STOP：同意挪用原为服务故障回退签发的第2次加载，在原五维信封已核余额内完整重跑一次C2JSON-S1的609行；只允许首行自检改为规范化比较，模型/mmproj/帧/prompt/schema/推理参数与评分口径不改。先由实现准备本机静态材料，Acceptance零消耗核清后才可上板；若既有监督/计时/尾差问题不能在此改动闭集内满足原合同，继续停止、回我另定，不扩大改动或信封。”

若用户选择另一项，唯一推理驱动改动闭集为首行template+params的JSON规范化比较及对应新首行规范hash/字节绑定；不能删除输入核验、把INPUT_CHANGED改为警告、改schema/prompt/模型/请求或HTTP失败继续规则。更改累计计时算法/监督启动与周期/收尾计量**不包含**在“只修首行自检”里，不得悄悄搭载；当前已知这些问题须一并解释给用户，需超闭集修复时先另定范围，不能以零消耗准备授权当消耗放行。

用户允许运行的原话入账并经接受落实以后，由Implementation先只在NEW下保留原driver、产出新副本/定点diff、plan派生绑定与累计账预案；Acceptance用系统标准库零消耗静态核验首行落盘/重读规范hash、模板/参数原文未变、监督/计时/收尾保护和完整余额，未核清即停、不上板。若可放行，Mac及板均在原BATCH下新建不存在/非link的attempt-2，原plan/attempt-1及占位评分不覆盖；新plan/driver绑定另存于attempt-2，budget.jsonl追加原账，不重开批零起账。逐步重做1→2→3→4（含健康1、可用预热≤3、609行原序各1次）再5→6；先预约第二加载、≤613请求、全有效载荷/正增长及收尾时间，两尝试分别保留收据/原响应/失败或未执行占位/609分母配对评分，禁止拼接择优；第二加载后无第三次回退，任何停止仍回用户。本段是用户另一项的条件说明，不是已获运行许可或新的执行合同。

现行待决入口「阶段B预检答复落实」§5已更新为本项指针。Overall REVIEW_PASSED / Lifecycle ACTIVE及正式AC-7/8/9 NOT_RUN保持；原S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN、旧诊断停止归因、3c条件提升停点和S5推后未签不变。不更新里程碑证据，不自动转正式证据。

open_items: none

### 阶段BC2JSON诊断授权落实（2026-10-06，Acceptance；诊断执行合同）

登记轮次 `阶段BC2JSON诊断授权落实`；Dispatch-Id `P1-ENG-JET-001-阶段BC2JSON诊断授权落实-20261006T210832Z-c0d9`。依据账本2026-10-06「用户答复 B-C2-RESULT 按推荐；签发『C2 Q4 加 JSON 约束』板上 609 行诊断…」(b)(c)(e)逐维度落实，用户原话优先。本轮只读本机原件、系统Python标准库核身份，未联网/SSH/触板、未import或运行模型/第三方包、未跑测试；consumed=none。不是D/C/R，不新增AC/修订、不签额度或verdict。B-C2-RESULT、S5及已答旧项唯一现行入口为「阶段B预检答复落实」§5；本节仅是新签诊断合同，不重开旧批，不以新签额度追认旧越界。

#### 1. 范围、来源与执行前身份核验

唯一设备沿本项Mac mini与用户Jetson Orin Nano 8GB Super、有线SSH/known_hosts。只复用板上阶段BC2的C2 Q4_K_M、官方F16 mmproj、既有b11381 llama-server和HOLD 392帧，Mac只作配对评分；不合并/转换/量化、不传模型或帧、不另编译/安装。上次核清是历史事实，**本轮未确认板上产物仍存在**；实现先执行本节具名前置，任何缺失、来源歧义、类型/字节/hash不符或身份不可核，立即停、回用户，不自批重传/重建/重新量化。

运行时从以下原件解析路径和期望SHA，禁止把派生SHA/UTC目录/HEAD抄入手维护文档：

| 输入 | 唯一解析与核验链 |
|---|---|
| 上轮原件OUT | `outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/`的state.json、budget.jsonl及steps各收据；board步骤由state.board.step解析，必须有609行原outputs/predictions、服务已停与端口已释放的收据。score步骤从收据step=score且diagnostic_outcome.execution=SCORED唯一解析，不用模糊glob首项；歧义即停。原件不改不删。 |
| 板MODEL | state.q4的basename/bytes/sha256与board receipt的server.argv中--model路径、transfer.admitted/board_verify三方核；本机state.q4.path现算字节/hash一致后，板上同路径stat与sha256sum须逐字符合上一轮「阶段BC2诊断核清」§2所核链。普通非链接且父目录不经链接，不允许另找同名文件或用官方base Q4替代。 |
| 板MMPROJ/SERVER/库 | MMPROJ由board receipt.board_paths.mmproj与stageb-transfer.json唯一官方F16对象board_final双解析，板现算字节/hash须与transfer期望及上一轮precheck.blocks.mmproj原文相同。SERVER由board_paths.server与stageb-build-rerun.json products.llama_server_stat_raw/board_batch_dir双解析，板现算hash须等于上轮server_sha256_now，类型/字节/库名称、大小及链接终点须与上轮precheck.blocks.bindir/bindir_resolve一致；库无旧hash时注明该历史限制，不补造旧期望、不运行--help/--version探测。 |
| HOLD盲文件/帧 | state.inputs.hold.blind及blind_meta与SFT-002 dataset-manifest.json files同名项双核字节/hash/609行；每行严格五字段row_id/frame_path/surface/g4/vocab，row_id唯一且顺序不变。解析实际引用的392件JPEG，Mac upload源逐件hash=文件名且640×480；板帧根取board_paths.hold_frames，每件普通非链接/相同原字节/hash/尺寸。缺一件即停，不补传、不替图、不重采样。只用这609行，不用DEV或manifest较大帧全集替代。 |
| C2 bf16、gold、无约束Q4 | bf16由SFT-002 eval-summary的job_b解析eval-adapter预测，selected_adapter及hash须绑定同一train-summary selection C2；与state.inputs.baseline path/sha双核。gold与state.inputs.hold.gold_meta相符，仅Mac读。上轮Q4用board步骤predictions.jsonl、outputs.jsonl及唯一score.json inputs.predictions_board_sha256互核；blind/gold/bf16/Q4均609唯一且同row_id顺序，原失败行保留。不复用base bf16。 |
| prompt/schema/评分器 | prompt_v2.py按上轮receipt.prompt.prompt_v2_py_sha256核原文身份，并核609个已存text_sha及固定模板；冻结parse.py/evaluate.py仅Mac标准库路径评分，不改冻结文件/判据。schema取本机stageb-base-prompt/schemas/S1-three-state.json，须与先前S1三态plan/receipt里的request_params.response_format.schema（或params同字段）JSON结构一致。S2两态/P2不得借用。 |

本次接受侧只读核算支持：本机Q4现算与state/旧板核验相符；blind/gold/bf16/旧Q4预测hash链及609唯一同序成立，盲文件实际引用392帧；S1原件与两份先前计划结构相同。此为本机合同输入核实，不是板上新核验或评分重跑。板端任何核验失败不得先改核验脚本再继续消耗；发现合同歧义回Acceptance，需新增操作/资源回用户。

#### 2. 新解码条件与固定请求

本次具名新条件为 **C2JSON-S1：C2 Q4 + prompt v2 + S1三态JSON约束**。沿上轮同模型、mmproj、HOLD、prompt文本及服务推理参数，只在请求加 `response_format={"type":"json_object","schema":<S1-three-state.json内容>}`；保存完整schema原文/现算hash及每次实际发出的参数。`temperature=0`、`max_tokens=160`、`stream=false`、`cache_prompt=false`不变；无历史对话、串行、图像data URI来自板已有原JPEG。不能换为json_schema/grammar兜底、改prompt/ctx/image-min-tokens/帧或根据HOLD结果改schema。

schema字段闭集与冻结parse.py一致：anyOf三支，unique仅status+bbox_2d；ambiguous仅status+candidates，2…8个候选且各仅bbox_2d；none仅status。各层additionalProperties=false，框恰4个0…1000整数。schema不证明x1<x2/y1<y2，坐标顺序与截断/finish_reason仍由冻结解析器判定；SCHEMA_ERROR、JSON_ERROR、RANGE_ERROR、ORDER_ERROR、TRUNCATED均按原口径计，不能因声明加约束就视为可解析。

参照LOOP-002「D1 接受裁定」§7(d)，JSON约束登记为新的推理/解码条件，不回改SFT-002冻结prompt/parse或历史结果，也不接管LOOP-002合同/额度/K3。本项诊断可用性不能自动作为未来闭环或正式K停点通过。

线上数据载荷闭集仍为盲行五字段；此外明确允许诊断封装：固定v2模板、固定请求参数/S1 schema、row序号、期望帧hash与timeout控制信息，不含标签/逐图标注分支。驱动纯标准库，经stdin/SSH执行并在板内渲染文本和读JPEG；不将gold、sidecar、truth、训练/评分文件送板。Mac先生成每行prompt期望hash，回传的实际text_sha须相同。此为新合同明列封装，不追认上轮“五字段”执行形式偏差。

#### 3. 已签独立信封、预约与保护

唯一新累计账为 `outputs/eng-jet/P1-ENG-JET-001/stageb-c2-json-diagnostic/budget.jsonl`（追加式），零起账；不使用旧C2/tool/base-prompt余额，旧账只读。成功、失败、重试同账，维间不抵扣，删除不返还计次/正增长。每动作先预约、后结算，不能确认送出或失败部分时从严保留预约，不先做后补账。

| 维度 | 账本硬上限与本批计量 |
|---|---|
| 板服务加载 | ≤2次；每个llama-server启动前+1，失败/未ready也计。1次正常执行，另1次仅用于§5唯一具名失败回退；不是跑满许可。 |
| 板请求 | ≤1,300次；健康/预热/确认/失败/超时/未确认送出均计，禁自动HTTP重试/重定向/health轮询。每尝试计划健康1+a7预热≤3+确认609≤613，至多两尝试≤1,226；余量不用于补行/新变体或额外探测。板loopback调用不计外部模型API。 |
| 板端累计墙钟 | ≤5,400 s；本批首次板阶段前置之前起UTC+monotonic，至服务停止、端口核验、最终收据写完及监督退出止；两尝试相加不重置。期间连接/传送schema驱动/加载/请求/监测/收尾均在账，Mac阶段耗时另列，板阶段等待Mac也不扣除；最终尾差不可核则UNKNOWN。预留≥60 s收尾，余额≤60 s不启动新动作；命令/加载/请求超时再取剩余较小者。 |
| 板新增占用 | ≤100,000,000 B（十进制）；本批目录、schema/驱动若落盘、cache/tmp/日志/失败保留件与目录元数据共账。首次板写入前记录eng-jet双du基线与新目录不存在；表观/分配取大，并与eng-jet可归属正增长交叉核，各次正增长累计，外部下降不抵扣。既存模型/mmproj/帧只读不复制、不借旧cache写入。 |
| Mac→板传输 | ≤10,000,000 B（十进制）；只传schema与本次纯标准库驱动改动及其必要盲行/模板/参数/控制封装，不传模型、不传帧、不传gold。含SSH命令/stdin、任何上传文件与失败/重传有效载荷，逐动作按实际字节及最坏上界先预约，批前核总投影。板→Mac原响应/日志另记实际B，不把单向额度改成双向或抵扣；SSH/TCP物理封装UNKNOWN。 |
| 其余维度 | 云/GPU租用/外部模型API、下载、pip/新环境、构建、合并/转换/量化、Mac模型推理、快层/共驻、3c、Play/scenario/session/run正式ID、发布均0；系统/SSH/沙箱设置不改。Mac标准库解析/评分及必要诊断原件写入沿账本“Mac评分零消耗”，不调用模型、不申请额外额度。 |

板监督至少每≤1 s检查同一截止、受控进程存活、du/df与本批增长，每个新受控写入/请求前再核余额；长动作同样监测，采样间瞬时峰值与不可归属系统增长不能证实则UNKNOWN，不凭采样低于上限声称严格全量在限。缓存/tmp只进新目录；仅本进程CUDA_CACHE_MAXSIZE封顶16,777,216 B并记与上轮环境的保护差异（不改推理参数、不把时延差纯归因JSON），不沿上轮128MiB缓存上限越过本次100MB。受控日志/单响应限沿冒烟合同（单响应≤1MiB、流量有界）；预留本批日志收尾，已记新增达60,000,000 B或下一动作最坏投影不能在100,000,000 B内完成即停，不能清旧件腾额。读盘余量须≥本批剩余新增预约+100,000,000 B；无法核预算/实施保护即停、回用户。

#### 4. 步骤闭集、顺序与逐步收据

原件新根NEW为 `outputs/eng-jet/P1-ENG-JET-001/stageb-c2-json-diagnostic/`；每批在NEW下新建运行时UTC子目录，每尝试另建attempt-1或attempt-2，板对应 `~/eng-jet/stageb-c2-json-diagnostic/<运行时UTC>/attempt-<序号>/`。新批/新尝试目录须不存在、非链接、umask077/mkdir700；回退时只复用可核归属本批的父目录，新建attempt-2，不覆盖attempt-1、不重置累计账。UTC只是诊断目录，非正式run ID。窄驱动只写NEW，不改仓库运行时代码/配置/测试/工具或数据根；不得直接运行旧c2.py（含工具下载/模型加工/传板步骤）。

每步收据共同字段：purpose=diagnostic_only、gate_evidence=false、work/round/执行Dispatch-Id、授权条目/合同指针、运行时git HEAD/porcelain、输入来源/现算hash、argv/局部环境、UTC/monotonic起止与timeout/rc、预约/实际/累计/余量、原stdout/stderr路径与字节、diagnostic_outcome/stop_code、未执行项与UNKNOWN。各步另具名如下：

| 顺序/步骤 | 动作闭集与新增收据字段 |
|---|---|
| 0 MAC_BIND | 只读核§1原件/旧账及S1完整性、609行序/392帧；冻结plan（单一C2JSON-S1、尝试序、schema/驱动/盲载荷字节与SHA、全量上传投影、清理保护）。字段：逐项binding结果、旧Q4/bf16/gold来源、代码/评分器身份、计划失败保留规则；失败不连板。 |
| 1 BOARD_VERIFY | 在累计计时内首次连接，用旧合同具名SSH选项（BatchMode/StrictHostKeyChecking/ConnectionAttempts=1等）、原有线目标，不改权限。纯只读核headless/id/aarch64/工具、18081空闲且无模型并驻、df/free/双du基线、§1全部板输入。字段：原stat/hash/链接/392件清单核验与缺失项、旧期望对照、端口/进程归属、可用空间；失败即停，不用其他路径。 |
| 2 DIAG_SETUP | 仅新目录及必要schema/驱动封装（可全stdin，不强制板落脚本）；五字段盲载荷按原序发送。字段：上传逐件/命令/stdin预约及实际B、路径归属、新目录/局部cache环境、只读旧件声明与监测起止。不得传模型/帧，不安装、不import板项目/第三方包；板系统Python用-I -S -B。 |
| 3 LOAD_AND_QUERY | 沿上轮server.argv，MODEL/MMPROJ/SERVER保持已核原路径，仅工作目录和局部cache/tmp环境改至本批新尝试目录；推理参数完全沿上轮：127.0.0.1:18081、parallel1、ctx2048、n-gpu-layers99、fit off/no-warmup/no-webui/no-cache-prompt/cache-ram0/cache-reuse0/offline；只加§2请求response_format。加载ready最长300 s；确认本批PID/回环后GET /health恰1次（≤10 s），a7帧0/100/200各1次预热（the car、g4=false、vocab=unity-v2，先核既有帧身份，ABSENT则记未做不补选/传图），然后609行原序各1次POST /v1/chat/completions（每次≤120 s且受总余额限制）。字段：PID/argv/环境/ready/绑定、每HTTP序号/分类/row_id/帧hash/text_sha/实际参数、送出状态、HTTP码/rc/原响应/content/finish_reason/usage/timings、失败/未执行行及内存/时延/cache描述或UNKNOWN。 |
| 4 STOP_AND_RELEASE | 正常/错误都在剩余时间内仅TERM本批PID/进程组，wait≤5 s后必要KILL并wait，核18081释放；同步停止监测并保存末次双du/df/累计账。字段：TERM/KILL/wait rc、PID不存活/ss原文、清理归属/失败保留件、截止与最终写盘/监督尾差。SSH断开不当作服务已停；无法确认终止/释放则UNKNOWN并停，回用户，不二次登录盲杀、不杀其他服务、不换端口。 |
| 5 MAC_PAIR_SCORE | 服务已停且释放可核后，Mac按§6逐尝试生成609行预测/评分与同行对照，不跑模型/测试，不改原件。字段：blind/gold/bf16/旧无约束Q4/新原响应及预测hash、唯一同序/分母核验、解析失败与未执行计数、评分器/算法身份、输出路径、限制。完整性失败停、不删行或修源文件。 |
| 6 REPORT | NEW内summary/checkpoint写最后完成步骤、各维预约/实际/累计/余量及未测UNKNOWN、原件索引、偏差/回退及旧限制承接、服务/端口状态；交Acceptance核同一资源账和配对身份，不续跑正式阶段B或共驻。 |

失败优先跳到4保存/停服务（未启动则明确加载0、服务不存在），再5（输入身份仍有效时仅对已获原件及609个失败/未执行占位评分）与6。唯一允许的再执行分支见§5；除此不增加步骤、工具探测、请求、补测或自设“复查通过后续行”。

#### 5. 出错即停与唯一具名回退

**停整批并回用户**：INPUT_MISSING/INPUT_CHANGED/IDENTITY_UNKNOWN、schema/服务不支持（含HTTP拒绝response_format）、OOM、权限拒绝、外联/下载迹象、缓存异常、任一资源将越界/计量不可核、未能停止服务/释放端口、其他执行/核验错误或需用户判断。预算是上限，不是失败后继续的权限；不重传、不量化、不切grammar/两态schema/参数/模型/栈。已签旧路线/已答旧项不重问。

唯一回退 **C2JSON_SERVICE_RETRY1**，仅落实账本所选“1正式+1失败重试”：首次服务在加载阶段非OOM超时/退出，或确认期间服务非OOM崩溃/退出时，立即停本尝试并先完成4；若服务终止/端口释放、输入身份、失败原因排除OOM/外联/预算/权限/核验异常及全部剩余额度可核，允许同参数重启1次（回到1→2→3→4，再5→6）。不对单行超时/HTTP错误/解析失败触发此回退，不用它修驱动或补签未知故障。重启前预约第二加载及整轮≤613请求、全载荷/占用投影与收尾时间，任何不足即停、回用户；第二次服务故障直接停，不再回退。

回退重新跑609行完整同序尝试，不拼接第一尝试成功行，不覆盖第一尝试原响应/失败/未执行占位，不因失败退款；两尝试均逐行/逐维留账、评分和对照，汇总标明尝试序与完整性，不按分数择优。本次schema解析失败是测量对象，保留该行并继续原定后续行，**不属可修复的执行错误**；schema可能消掉格式失败只是待测假设。健康/预热失败（非上述已证服务退出）、单HTTP传输/响应失败或输入/hash不符立即停止剩余查询，保留未完成行；不存在“连续5次才停”的放宽。

#### 6. Mac评分、原件清单与实现交接字段

Mac冻结parse_prediction与evaluate既有评分口径：保留原finish_reason（含length截断），不清洗/重写原输出；新预测、旧无约束Q4、C2 bf16、gold和blind row_id均唯一609且同原序。请求失败/未执行行用status_pred=null、空框及具名REQUEST_FAILED/NOT_RUN执行状态占位，不伪造模型三态/原响应；解析失败原样保留。每个尝试分母始终609，各组分母取同一gold全部行，不剔除失败、不补跑、美化或混用两尝试。旧c2_score.py会写入传入board目录的predictions，不能以旧board步骤作为写目标；本批封装只写NEW，评分/gray参照仅Mac只读。

每行同行列出：row_id、group/gold（只在Mac）、旧Q4/本尝试JSON-Q4/bf16的status_pred、parse_error、原finish_reason、框/既有成功判定、执行状态。汇总沿旧score.json现有口径并列SCHEMA_ERROR及其他解析错误行数、三态混淆（invalid另列）、逐行状态配对一致、逐组计数/分母、G1∪G2成功率与配对差/既有bootstrap描述区间、G3上报率/严格成功及G3t、G5等既有分组；JSON-Q4对bf16与对旧Q4各自同row配对，不把组分母与全体609混为一谈。时延/内存/token/cache/grid沿原件可得值描述，未知写UNKNOWN，不另请求取证；受局部缓存保护等运行差异影响的时延不作纯解码因果主张。评分摘要去除evaluate的verdict块，不写AC满足/通过结论；无约束Q4对bf16的历史总差异仍不能归为纯量化损失。

NEW不入git的原件闭集：plan.json、schema原文/驱动副本与hash绑定、budget.jsonl、每步/每尝试receipt.json、calls.jsonl、原始stdout/stderr/响应与服务/监测日志、outputs/failed/predictions.jsonl（含未执行占位）、逐行同行paired-rows.jsonl、各尝试score.json与comparison.json、summary.md、checkpoint.json及板新文件归属/清理清单。板只保留新目录本批受控文件，旧Q4/mmproj/库/帧/旧缓存不覆盖/移动/删除；异常原件默认保留。全部标purpose=diagnostic_only/gate_evidence=false，不写docs/evidence正式工件或-vlm/-quant-equivalence/-report/-ledger正式JSON，不入里程碑证据、不提升为verdict/AC-7/8/9或门读数。

实现报告必须含work_id、this_round、执行Dispatch-Id、合同/授权指针、完成步骤/具名停止原因、原件根与唯一账/收据/评分指针、各五维预约/实际/累计/余量、尝试与回退归因、MODEL/MMPROJ/SERVER/HOLD/prompt/schema/bf16/旧Q4身份核验状态、609同序/失败保留、板服务停止及端口释放凭据、偏差/UNKNOWN/未执行项、具名needs_user及下一owner=Acceptance。状态板只写指针/执行事实，不写性能数值或正式门读数。核账后用户看诊断，不自动转正式证据；原STOP/未上板/OPEN债/3c停点与S5推后未签均保持。

合同完成可交Implementation；**本轮needs_user=none**。执行未来出现必需用户决定时，NEW checkpoint先写具名`C2JSON-<原因>`、接受推荐/理由/可回复原文且标“非已签”，回Acceptance→用户，不自行签额或恢复。Consuming=no沿现行本地诊断分类（正式ID/Play/API/云均0），不表示执行期没有板加载/请求消耗。依账本10-06一次性并行破例，本接受轮只本地提交、不拉取/推送；后续执行仍须supervisor恢复常规单写者/共享槽位互斥，不继承该一次性破例。

open_items: none

### 阶段BC2诊断核清（2026-10-06，Acceptance；零消耗资源与身份核对）

登记轮次 `阶段BC2诊断核清`；Dispatch-Id `P1-ENG-JET-001-阶段BC2诊断核清-20261006T180616Z-0c7b`。依据账本2026-10-06「用户签发 Mac 合并量化 C2 与板端 609 行配对诊断；接受角色核 base prompt 资源账」及「用户签发 C2 工具缺项…（supervisor 会话代录）」逐字原话，对照下两节合同§1–3/§1–4。只读本机保留原件与驱动源码，以系统Python标准库核JSON、字节/hash、归档与wheel METADATA；未执行c2脚本、模型、第三方import、测试、联网取证或板操作。本轮consumed=none；不是D/C/R，不签额度、verdict或AC修订；仅按本派发要求在提交后推送origin/main。

原件根（下称OUT）为 `outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/`，仅本机、不在git：`summary.md`、`budget.jsonl`、`state.json`、`checkpoint.json`、16份`steps/*/receipt.json`（含4份STOPPED）及`c2*.py`；评分仅`steps/score-*/score.json`。执行报告源为 `docs/evidence/supervisor-dispatch.jsonl` 中轮次「阶段BC2诊断执行」的finished.report；对应实现提交从该行commits运行时解析，提交只改状态板，不是诊断驱动或独立复核候选。以下记录核清结论，不复制性能读数、原件或评分为正式证据。

#### 1. 十维账与收尾

独立重加：701条reserve与701条settle一一对应，无重复/悬空/孤儿结算；预约used_before+amount均未过各自cap。16份receipt按started_utc排序，tally_before逐份接上一份tally_after，末份与checkpoint一致；state的已完成指针均可找到收据。4次STOPPED不删、不清账；转换尝试事件2条，合并1次、语义复查3次，不伪增/退回加载或构建计次。维间无抵扣，旧base-prompt/板BUILD-LLAMA余额未挪入。

| 维度 | 原账已记录 | 签发上限 | 账面未用（只作差额，不是执行许可） | 核算来源/限制 |
|---|---:|---:|---:|---|
| 工具下载 B | 186,850,452 | 1,000,000,000 | 813,149,548 | cmake元数据1,717,623＋cmake轮子54,404,900＋回退元数据11,766,293＋26轮子118,961,636；均独立预约/结算。pip隐藏重试字节不能由实体尺寸补证，见§3。 |
| 隔离环境 个 | 1 | 1 | 0 | tool-get唯一创建，fallback装入同一tool-env，未另建。 |
| Mac CPU构建 次 | 1 | 3 | 2 | build的configure与llama-quantize target均rc=0，同一预约；其依赖库属目标闭集，Metal/CUDA/Vulkan关闭，Accelerate为CPU系统框架；不构建server。 |
| Mac工具磁盘 B | 1,116,995,584 | 5,000,000,000 | 3,883,004,416（完整实际余量UNKNOWN） | 原账是tooling+tool-env双口径较大值之和的采样峰值；现存漏计日志与监测边界见下段，不认定为完整已用。 |
| base下载 B | 4,266,640,306 | 4,500,000,000 | 233,359,694 | 10件必需文件每件一次，收据下载正文/状态与现算字节/hash匹配；无README、其他格式或重取。 |
| Mac↔板有效载荷 B | 1,108,997,496 | 1,200,000,000 | 91,002,504 | Q4一次scp 1,107,409,952＋SSH命令/stdin/两流1,587,544；13条TX预约含3条长连接，原流文件/结算与calls相符。健康/图像loopback不重复算链路字节；SSH/TCP封装UNKNOWN符合原计量口径。 |
| 板服务加载 次 | 1 | 6 | 5 | server唯一启动预约；ready及server_stop支持启动/退出，Mac加工不借板计次。 |
| 板请求 次 | 613 | 2,000 | 1,387 | health1＋指定a7预热3＋确认609；全部先预约，响应原流相符，无补行/第二轮。 |
| 板墙钟 s | 1,055.2 | 10,800 | 9,744.8（按原账精度） | batch_start→batch_end为1,055.188 s（epoch）；receipt始末及monotonic elapsed在0.1 s精度相符。计时在首次板访问前启动，覆盖清理/最终板检查；batch_end后最终receipt写盘尾差未独立实测，完整严格墙钟UNKNOWN。 |
| 板新增占用 B | 1,107,460,096 | 2,000,000,000 | 892,539,904（采样差额） | 37条occ取本批双du与eng-jet正增长较大值，单调不减；最大间隔30.427 s。既存mmproj/HOLD只读不复制，末清单保留Q4/cache/tmp；采样间峰值及不可归属系统增长UNKNOWN。 |

**工具磁盘勘误与边界**：43条tool_disk采样单调不减，故其正增长重加与原峰值一致；但驱动只统计tooling/tool-env，工具步骤日志/receipt实际写在steps而非合同要求的tooling，且未做C2全目录可归属增长交叉核。现算五个工具步骤目录双口径较大值合计323,584 B，均不在原tool磁盘账；与现存工具两目录合计至少 **1,117,319,168 B**，这是现存可归属下界、不是历史峰值或完整实际已用。fallback-meta来源查询未逐动作做磁盘预约；26轮子下载/安装主要只有前后核实，长动作持续监测不足，不能把采样低于5 GB升级为严格在限。原账不改、不以删除抵扣；完整用量/实际余量UNKNOWN。

模型工作集另列不借工具5 GB：base文件4,266,640,306 B、merged文件4,266,640,448 B、bf16 GGUF 3,447,350,304 B、Q4 1,107,409,952 B，四项逻辑本体共13,088,041,010 B；不含目录/日志/tmp/swap，不能称全盘峰值。加工各步pre/receipt及time-l记录体积、墙钟/RSS和全盘余量，合并后的swap增长保留；原merge核验停止路径未写merged_usage，只在后续state/文件身份补到最终体积，未独立连续测总磁盘/系统内存峰值。该必要加工属于已签用途，计量不足是执行偏差，不把模型本体误列成工具额度越界，也不据无OOM推为8GB稳定部署结论。

收尾原件支持本批server session_rc=0、still_alive=0、pidcheck=alive=0、18081已释放；不删除旧件或覆写输入。没有发现**原账已记录值**超上限；缺测/漏计不能宣称完整实际全部在限。失败动作及违规续行的实际支出均照记，不退款、不回退预约。此次具名链已结束，余量不授权另一次加工、下载、加载/609轮或其他范围，当前停止、不转用；建议用户以B-C2-RESULT确认未用额度作废，不冒充已经签发的用户处置。

#### 2. 来源与609行配对身份

- **base/C2**：train_lora.py BASE_REPO/BASE_REVISION、train-summary base及adapter_manifest base相符；init inputs又绑定selection.job_id对应job-receipt必需10文件。selection chosen=C2、chosen_adapter_sha256与adapter_manifest及现算adapter权重字节/hash相同；adapter_config身份可核、392个LoRA键只在语言层的原核验结果保持。base10件、merged10件、两GGUF、量化器、adapter与源码归档现算均符合state/来源期望，未手抄派生SHA或run名。
- **源码/工具**：source-archive.json的archive/binding_chain与init inputs、build extract一致；保留tar内3,684个普通文件与解出的工作副本逐件比对零差异，4,061成员/无跳过链接沿build收据。构建命令只选固定源码的llama-quantize；二进制版本横幅的build/短commit不当作来源凭据，绑定以归档/工作副本/命令/产物hash为准，不认证横幅就是该源码commit。
- **视觉/mmproj**：merge verify-result与相应核验代码逐键检查名称/shape/dtype/值，315视觉键（含24 merger键）全部相同，114非目标键相同，196目标模块合并容差内；这只是原实现核验的可核记录，本轮未重算张量/跑模型。三次cfgcheck及最新语义差为空可解释序列化差异，不能解除原STOP。官方mmproj本机hash、transfer.json期望与板前置原文stat/hash一致；convert2/quantize inspect支持projection_dim/embedding_length、deepstack数一致，文本张量名/shape、核心超参与分词器表匹配官方对照。inspect另有tokenizer.ggml.add_eos_token=false与官方缺字段的非核心差异，保留、不认定全部KV相同；没有mmproj逐张量对base视觉塔再导出比较，不扩大为全栈数值等价。
- **板端输入**：Q4本机现算与state、传板后verify-q4原stdout三方一致，一次传输，官方文本Q4未冒充C2。盲文件字节/hash/609行与dataset-manifest files相同；其实际引用392帧（不以manifest frame_binding.eval全集448替代本次392），本机upload帧逐件hash符合；板预检原stdout的392件全部regular/非link、640×480且hash匹配同一文件名，bad=0，只读复用原HOLD。
- **盲字段/prompt**：盲文件只含row_id/frame_path/surface/g4/vocab，gold/sidecar/truth不在输入代码通路或传输清单；worker在板以固定模板渲染。本轮仅AST读取prompt_v2常量、按其固定段顺序核609份text_sha，全部相同；原prompt收据/文件hash亦匹配。stdin还带模板/固定params及op/seq/expect_sha/timeout控制字段，严格“五字段且只送”字面未完全落实，见§3，不据五字段源文件就称线上只含五键。
- **评分配对**：eval-summary selected_adapter=C2且hash绑定同一selection，baseline仅其job_b eval-adapter，不使用base bf16；现算预测hash与predictions_sha256一致。blind、gold、bf16、板outputs、板predictions的row_id均609唯一且同原顺序；score输入hash及609分母、各组总数、三态混淆/状态配对总数相符。34条SCHEMA_ERROR保留在板predictions和609分母，未剔除；原脚本对失败/未执行也按全盲行生成无效预测，未补跑或美化。仅核身份/完整性和评分路径，不重跑评分或签性能值。

#### 3. summary「偏差与披露」逐项裁定及补充

| 项 | 裁定 | 依据与影响 |
|---|---|---|
| 1 合并核验停止后续行 | **违反停止边界，属于执行授权顺序越界**，不只是形式偏差 | 工具合同§4与用户「任何…核验失败…都停下」明确覆盖自设核验失败；MERGE_VERIFY_FAILED后应停依赖加工等用户。3次merge-recheck自加/反复修脚本及第三次后继续转换→板端不属于首次转换例外；零新增下载/加载不能解除停止。张量/语义检查支持保留可解释产物，但不追认续行合规或把STOPPED改成PASS；此后消耗照记。 |
| 2 转换回退/26包 | **具名回退次数、pin、必需闭集符合；下载保护另有偏差** | 首次现有5.17因sentencepiece缺失失败，再装4.57.6重试一次成功，未重做合并。源码顶层torch和requirements具名torch2.11.0/numpy~=2.2.6/sentencepiece范围为4根；其余22包均有Darwin/arm64/Python3.12、无extra的必需Requires-Dist链（torch→sympy/networkx/jinja2等、transformers→hub/tokenizers/requests等），不是全量requirements或新增模型栈。27个轮子（含cmake）现算字节/hash匹配官方冻结值，ZIP METADATA支持依赖闭集/pin；tokenizers依赖字符串仅顺序不同、语义相同。版本优先现语言环境兼容版、否则兼容正式轮子属实现选取，合同未另限定依赖版本；显式pins均遵守。protobuf为未走的懒导入路径、gguf来自源码，未装符合最小闭集；不采用requirements的extra-index。 |
| 3 处理器复制/outtype auto | **合同内的保存/格式选择** | 合同未指定processor.save_pretrained或必须F16；7件processor/tokenizer按base字节保存且逐件一致，避免新序列化。固定转换器缺省auto，inspect实际为BF16/F32，再Q4_K_M符合链条，不宣称中间纯F16。 |
| 4 板prompt渲染 | **文本语义符合；stdin封装有执行形式偏差** | 原文固定v2、609逐行text_sha同一；模板/params与4个控制键无gold/标签、未见泄漏通路，但超出“只允许stdin五字段”的字面形式。保留偏差，不暗改原合同放宽以后通路。 |
| 5 传输计量 | **合同内有效载荷口径** | scp文件本体与SSH命令/stdin/stdout/stderr共账，协议封装UNKNOWN正是合同要求；不能声称精确物理网字节或把loopback体积加成Mac↔板。 |
| 6 图像网格差异 | **合同内披露，不强制消除** | 授权诊断合同§3(4)要求披露grid/token/栈差异，不强设或回流HOLD调参；两侧实际网格不能由JPEG相同或mmproj静态超参推为相同。 |
| 7 Mac工具/工作集 | **用途分列符合；漏计、日志位置与监测不足为执行偏差，完整上限符合性未证** | §1十维账所列下界/UNKNOWN保持，模型加工不借工具额度；现存漏计日志及fallback查询磁盘未预约、长动作缺持续采样不以较小原峰值遮蔽。没有已证数值超5GB，但不能追认全计量纪律符合。 |
| 8 总差异归因 | **合同内主张上限** | 仅能描述合并＋格式转换＋Q4＋llama.cpp/Jetson相对C2 bf16的总差异；无中间bf16/GGUF对照推理，不能称纯量化损失。 |

**补充下载保护偏差**：tool-get/fallback-get的27个pip download均有精确官方文件URL/hash、逐包先预约、--no-deps/--no-cache-dir；安装只用已核文件、--no-index/--no-deps，26件一次本地列表安装没有隐式解依赖。没有干跑/Range、无extra_files，stderr无重试记录；但命令未传--retries 0，clean_env去掉PIP_*、--isolated忽略环境选项，本机保留pip 25.0.1的cmdoptions.py静态默认retries=5，**未落实“禁自动重试”**。原日志只支持可见27件实体各一次，潜在额外取回字节UNKNOWN，不能据最终实体大小证明下载绝对完整精确；本轮不追加尝试、不补探网络。上述均为本轮合同核清归因，不是独立复核finding/CLASS或AC缺债，不改既有返工计数、R1-5/6或blocks/release。

#### 4. 结果可用性与交接

可保留来源绑定、板服务/请求原件、609全行配对的描述性诊断，附本节停止边界越界及计量/封装限制；**不追认严格全合同符合，不消费verdict、不提升AC-7/8/9或正式门**，不作为B1/B2/K停点通过或DONE。原STOPPED、后续成功收据及checkpoint最新SCORED并存，最新汇总不能覆盖失败历史。本次结束后不启动依赖步骤、不回退实际支出、不签新额。

下一交用户仅决策 **B-C2-RESULT**：推荐、理由和可回复原文唯一落点为「阶段B预检答复落实」§5现行段。用户未答前不把旧批“不追人”处置推广到本次续行，也不以接受建议冒充追认；3c/云/过期排除条目仍沿原未答状态，已答C2路线/额度不重问。Overall REVIEW_PASSED / Lifecycle ACTIVE、历史S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN、AC-7/8/9 NOT_RUN保持。无新增AC/修订、门/里程碑证据变化，不改implementation-status或正式设计。

open_items: B-C2-RESULT

### 阶段BC2工具缺项落实（2026-10-06，Acceptance；CLARIFY）

登记轮次 `阶段BC2工具缺项落实`；Dispatch-Id `P1-ENG-JET-001-阶段BC2工具缺项落实-20261006T045805Z-2d63`。依据 `docs/authorizations.md` 最新「2026-10-06 P1-ENG-JET-001 — 用户签发 C2 工具缺项：工具/依赖下载 ≤1 GB、outputs 下 1 个隔离环境、Mac CPU 构建 llama-quantize ≤3 次、Mac 新增磁盘 ≤5 GB；转换先用现有环境、失败再装 pin；今晚无人值守跑到底、出错即停（supervisor 会话代录）」的用户原话及三个所选选项全文，**原话优先**。已对照该入账提交与原工具缺项交接：指代正是下节「阶段BC2本机量化诊断授权落实」§4 的 Mac cmake/llama-quantize 与转换依赖缺项，范围、路线、设备与上限清楚，无需用户补答。

本节只追加该诊断合同的工具解释及执行纪律：下节§4「工具缺项未签、先准备再回用户」与§2工具下载/安装为0的限制，仅在本节闭集内被本次签发替代；下节§1–3其余合同继续有效。新增 AC/AC 修订 = 0，不扩大原六维任一额度、不改正式门、不消费 verdict；本轮零消耗、只写文档，consumed=none。

#### 1. 工具闭集、隔离与来源

- 唯一用途闭集为：官方 PyPI 的 cmake 轮子；固定保留源码 HF→GGUF 转换实际必需的 Python 包及其必需依赖；该保留源码的 CPU `llama-quantize` 目标。先只读核现有包、源码内 `gguf-py` 与 requirements，逐包列出名称、精确版本、用途/直接需求链、文件来源、预期字节与 sha256；只下载/安装缺失或不满足本次路线的必需项。不全量安装 requirements，不加无关开发包、其他模型或源码；不能由「必需」扩成换栈。
- 官方 PyPI 仅使用 `https://pypi.org` 的项目/文件元数据及其 `https://files.pythonhosted.org` 官方文件；不加 extra-index/镜像/git URL，不作干跑（含 `pip install --dry-run`）、不作 Range GET 试探。下载前由官方文件元数据冻结文件闭集、精确字节和 sha256，先预约再逐包 `pip download --no-deps`（禁隐式取依赖/自动重试），取回后先核 sha256/字节符合，再以已核本地文件 `pip install --no-index --no-deps` 离线安装。依赖须逐项显式核入同一闭集与预算；平台/版本/哈希/体积不符即停，未知体积不能先下载再补账。
- 在 `outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/tool-env/` 新建 **1 个**隔离环境，创建前确认不存在且路径不经符号链接指向外部；以既有解释器创建，不下载解释器、不创建第二个环境。只装进该环境，不改 `.venv-language`、系统 Python、Homebrew 或系统设置。已有语言环境仅只读复用；可用源码内 `gguf-py` 时以本次进程局部路径使用，不往已有环境装包。
- 工具下载暂存/cache、源码工作副本、构建目录与工具日志全部放上述 C2 诊断目录的 `tooling/` 下；设置进程局部 cache/TMPDIR 与禁写字节码，禁写用户全局 pip cache、源码保留原件或主树。新包本地离线安装不得拉取构建依赖；需要额外工具、外部源码或系统改动即停。

#### 2. CPU 构建与转换路线

- 源码身份运行时从 `docs/evidence/P1-ENG-JET-001-stageb-source-archive.json` 的 `archive` 与 `binding_chain` 解析，保留归档先核字节/sha256，工作副本与之绑定；不手写派生 SHA、不重新下载、不换 tag/commit。既有编译器只读复用；Mac mini 仅 CPU 构建 `llama-quantize` 及源码内该目标必需库，显式关闭 Metal/CUDA及其他 GPU 后端，不构建 server/其他无关目标、不 FetchContent/联网取依赖。缺现有编译器或需系统安装即停。
- 构建累计 **≤3 次（成功/失败都计）**；每次从 configure 开始到该目标构建结束记1次，configure 失败也计。先预约，保存参数、工具版本、stdout/stderr、退出码、起止与产物字节/sha256；上限不是要求跑满，也不豁免§4出错即停纪律。
- 合并沿下节§1使用现有语言环境；转换 **先用现有 transformers 5.17 环境试1次**，使用固定源码转换器与已核源码内 gguf，不改变现有安装。仅转换报错或该次转换核验不过时，按用户明确的回退选择，在上述唯一隔离环境装 **transformers 4.57.6 及该源码 requirements 中本次转换必需 pin**（必需依赖逐项核入§1闭集；不全量装 requirements），再转换 **重试1次**。不先装 pin、不在现有环境降级、不借回退重做合并或换模型/mmproj；第二次失败、源身份/输入核验失败或 OOM 即停止。转换回退是用户明确签发的具名例外，不推广为其他失败重试权。

#### 3. 独立维度与同账计量

工具账与原六维共用唯一追加式 `outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/budget.jsonl`，不得另开工具余额账或与 base-prompt 共账。新增维度各自预约/实际/累计/余量，成功与失败共账，原六维单列，维度之间不抵扣、不转用；每条带对象、用途、来源/身份、开始/结束与收据指针。

| 新签工具维度 | 上限与计量口径 |
|---|---|
| 工具/依赖下载 | 合计 ≤1,000,000,000 B（十进制）；cmake及转换依赖的实体、失败部分、重取字节与来源查询响应均累计，不借base下载额度；文件实体先按官方字节预约，失败/不确定取回量按预约全额保留，不能退回计次或隐藏pip自动取回件。 |
| 隔离环境 | 新建1个，上述 `tool-env/` 唯一位置；失败创建也占1，不删后另建绕过。 |
| Mac CPU 构建 | ≤3次，计次按§2；不借板BUILD-LLAMA额度，板端编译仍0。 |
| Mac 新增工具磁盘 | ≤5,000,000,000 B；工具轮子、暂存/.part、隔离环境、cache/tmp、源码工作副本、构建产物及失败保留件均计，基线在首次工具动作前取。分别取逻辑字节与实际占用并取大，交叉核C2目录的可归属正增长；逐动作前预约、后核实，长动作持续监测峰值，累计保留正增长，删除不抵扣；采样间未能证实的峰值写UNKNOWN。 |

Mac磁盘维度按账本仅计新增工具/环境/构建，不把既有base下载及合并/转换/量化模型产物算作工具额度；这些模型产物仍按下节§1逐件记体积/峰值/墙钟，另行报总工作集与全盘余量，不能藉分列隐藏总盘风险。执行前核Mac盘余量足够工具预约与必要模型加工工作集；任何一维不足/无法核定则停，不清旧件腾空间。原六维上限、计量与失败共账规则逐字沿下节§2。

#### 4. 无人值守顺序、停止与收尾

用户已同意今晚由supervisor无人值守按序拉起 **接受落实 → 实现执行 → 接受核资源与配对身份**；无需重复确认已签路线/额度。Implementation按本节工具闭集 → 下节base下载 → 合并/转换/量化 → 传板 → 固定prompt v2的609行配对 → Mac对C2 bf16评分执行；每步先核前置/来源/余量，不把本节签发当成工具已安装或模型已可运行。

**出错即停**：除§2用户明确签发的首次转换回退1次外，执行错误、核验失败、OOM、权限拒绝、任一维将越界或需要用户判断，立即停止依赖步骤；本次纪律优先于下节§3原单请求失败后继续的执行安排，不用剩余构建/加载额度自动恢复。不改系统/SSH/沙箱设置、不sudo/apt、不连云、不动外部模型API、Play/正式ID；3c仍停在补充预检前，B-CLOUD/CLOUDDEP与其他未答项不被代答。

正常或失败都在已签时间与保留清理余量内终止本批服务、wait并核端口释放，不回退预约。工具与全流程原件/日志/summary仅放C2诊断outputs目录；异常保留失败件，写检查点摘要（最后完成步骤、具名原因、账余量、UNKNOWN与推荐下一动作），等用户明早看。收工交Acceptance核同一budget.jsonl、收据、来源与609行配对身份，随后交用户；只作诊断、不进正式证据、不更新AC-7/8/9。Consuming=no沿原本地诊断分类，不表示执行期无硬件消耗。

open_items: none

### 阶段BC2本机量化诊断授权落实（2026-10-06，Acceptance；执行有前置）

依据账本 2026-10-06「用户签发 Mac 合并量化 C2 与板端 609 行配对诊断；接受角色核 base prompt 资源账」逐字授权，**接受本次具名诊断范围与六维额度**。本节是现行 C2 诊断唯一合同；旧云端 C2 路径不执行的描述仅是当轮快照，现仅对本节 Mac 路线被替代；B-CLOUD/CLOUDDEP、B-LOCAL-EXCLUDE-TRANSFER 及正式阶段 B 其余未答项仍留「阶段B预检答复落实」§5。本轮无新 AC/修订、不改变正式验收合同、不视为 B1/B2 或 K1K3K4 通过。

#### 1. 范围、输入与资产裁定

- Mac = 既有 Mac mini，板 = 本项用户 Jetson Orin Nano 8GB Super，沿现有有线 SSH/known_hosts；不恢复其他工作项。官方 base 只取 Qwen/Qwen3-VL-2B-Instruct **训练同 revision**，期望从 `tools/eng_sft/train_lora.py:BASE_REVISION` 与 `docs/evidence/P1-ENG-SFT-002-train-summary.json` base 双解析，必须相同；下载只限该 revision 的模型权重、config、tokenizer/processor 必需文件，排除其他权重格式/模型/GGUF/源码/轮子。不用 main/latest、不覆盖已有 base 副本，逐文件预约字节、记录官方来源与 SHA；失败字节计入 4.5 GB，不能循环重取完整权重。
- C2 原件由训练摘要 selection.job_id → 数据根 `outputs/eng-sft/P1-ENG-SFT-002/returned/<运行时解析>/runs/C2/adapter/`；权重 bytes/hash 与 selection、adapter_manifest 双核。C2 bf16 基线由 `-eval-summary.json` job_b → 对应 `predictions/eval-adapter.jsonl`，hash 与 predictions_sha256 一致；gold、基线与训练数据不上板。
- 本会话已现算 C2 adapter bytes/hash 与训练摘要一致，392 个张量键均为 language_model.layers 的 LoRA，无视觉键；adapter_config 的 target_modules 只匹配语言层、modules_to_save=null。**裁定可按用户要求复用既有官方 F16 mmproj**，条件是加工时核实 base 绑定，合并前后视觉塔及 merger 的名称/shape/dtype/张量值一致，mmproj 身份仍与 stageb-transfer.json 相符，配置/图像接口兼容。核验失败即停止，不重导/换 mmproj、不从文本层无视觉键直接推为已核加工正确。
- 模型步骤只在 Mac：base bf16 + C2 → merge_and_unload → 保存合并模型/处理器 → 固定已保留 llama.cpp 源码的 convert_hf_to_gguf.py → llama-quantize Q4_K_M。源码身份从 `docs/evidence/P1-ENG-JET-001-stageb-source-archive.json` 绑定解析；不换 tag，不用 imatrix/校准，不重训、不作 Mac VLM 推理。合并/转换必要本机模型载入和临时产物属于用户点名加工动作；逐件记体积/峰值/墙钟，不把它扩为其他加载或新安装额度。
- 板 SERVER / 官方 MMPROJ 沿冒烟合同 §2 的 build-rerun/transfer JSON 唯一解析，源字节/hash/动态库具名检查保持；仅 MODEL 换成本次已核 C2 Q4_K_M，不能继续用官方 base 文本 GGUF冒充 C2。
- HOLD 仍是同一 609 行 eval.blind.jsonl / 392 张 640×480 JPEG；源与 dataset-manifest 逐文件核实。板只读复用 base prompt 批已经传板的 HOLD 帧，每件核 hash；帧缺失可在新传输预算内传原 JPEG，存在但不符则停。只允许 stdin 五字段 row_id/frame_path/surface/g4/vocab，gold、sidecar、truth 不上板；数据根与主树 runtime 零写入。

#### 2. 独立资源账与硬上限

| 维度 | 用户已签上限 / 计量 |
|---|---|
| 官方 base 下载 | 4,500,000,000 B 累计；模型与必需元数据实体/失败部分均计，已签 base 类不含工具/依赖下载 |
| Mac↔板传输 | 1,200,000,000 B 累计双向有效载荷：Q4、缺失帧、stdin 盲请求、回传响应/日志/收据均计；协议封装与 SSH 系统开销另标 UNKNOWN，不声称物理网络精确计量 |
| 板加载 | 6 次；每次 server 启动预约 1，含失败/重启；Mac 合并载入单列，不借 6 次做桌面推理 |
| 板请求 | 2,000 次；所有健康/预热/确认/失败/超时都先预约，含未能确认送出的请求；loopback 本地调用，不消耗外部模型 API |
| 板端累计墙钟 | 10,800 s；从首次板端阶段前置开始到服务终止/最终收据写完，跨批相加且每动作以剩余时间设超时，保留清理余量；Mac 下载/合并耗时另记，不隐藏为板端实测 |
| 板新增占用 | 2,000,000,000 B；本批模型、.part、帧、缓存、日志/失败件累计；双 du 取大及 eng-jet 正增长交叉核对；既有 G2/帧不复制不重算，删旧件不能抵扣 |

新累计账只放 `outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/budget.jsonl`，逐操作预约、逐批收据，不与 stageb-base-prompt 共账。Mac 与板另建该子目录下运行时 UTC 目录（非正式 run ID），不得覆盖旧原件/既有 GGUF。传板前核实际 Q4 字节加盲请求/回传上界 ≤ 剩余额度；单个约 1.1 GB 模型一旦重复全量传输会越 1.2 GB，不自动重传。缺项维度仍 0，不能新增 pip/工具下载/系统包、板端编译、云、API、Play/正式 ID 或改系统/SSH/沙箱设置。

#### 3. 固定板端执行与配对输出

1. 沿基座提示合同 §5 的单写者、headless、槽位/18081 空闲、盘余量、来源核对与进程环境；仅换本批目录/模型，不改服务或系统。板新增 ≤2 GB，监测每 ≤60 s，传输与每100请求前再核预算；余量不足或将超即停止，清理只终止本批 PID，不杀其他服务或删旧件。
2. 使用既有 llama-server，沿冒烟合同 §4 的仅 127.0.0.1:18081、offline、parallel=1、ctx=2048、n-gpu-layers=99、禁缓存/自动预热/外联的启动参数。固定 prompt_v2.py 原文按盲行 surface/g4/vocab 构造，temperature=0、max_tokens=160、stream=false、cache_prompt=false；不加 P1/P2、JSON schema/image-min-tokens 变体，不调参/改帧/筛行。
3. ready 后 GET /health 1 次；既有 a7 0/100/200 三帧可核时各 1 次预热（the car，不入确认统计）；然后按 609 盲行原序各 1 次，计划 ≤613 请求/1 加载。预热不可用则记录未做，不另选图。无 smoke 或其他集诊断。本次确认只一次；单请求失败记该行失败继续，连续5次失败、服务崩溃/OOM、输入不符、外联迹象、权限拒绝或预算保护则停止整批，保留未完成行；不因剩余加载额度启动新的完整确认轮。
4. 原始响应/逐行预测流回 Mac；沿冻结 parse.py 与 evaluate.py 评分，基线**仅 C2 bf16**，核同一 row_id 顺序/609 分母；错误/未完成行不得剔除或补跑以美化分母。输出每组两侧原始分母/计数/差值、三态混淆、逐行状态一致及解析失败；运行时能暴露的实际图像 token、缓存命中、冷启动/时延、内存另记描述或 UNKNOWN。图像网格/运行时差异明确披露，不以人为强设1024/300或回流 HOLD 调参来消除。
5. 比较测到的是**合并+格式转换+量化+推理栈/设备的总差异**；没有中间合并 bf16/GGUF 对照推理就不能归因成纯量化损失。正式3 pp/G5/解析线仅可作描述，不形成新 PASS/STOP/verdict，不更新 AC-7/8/9；无共驻、3c/AWQ、云或闭环。
6. 正常/失败均在统一剩余时间内停服务、wait、核端口释放，预约不回退。receipt 含来源绑定、工具身份/命令/环境、加载/请求/传输预约、UTC/monotonic与最终尾差、占用/保护、故障/清理。原件/summary 只在上述 outputs，不写 docs/evidence 正式工件；结束后交 Acceptance 核资源与配对身份，再交用户。

#### 4. 工具前置与当前交接效力

本会话仅静态核实：Mac 主树 `.venv-language` 已有 peft 0.21.0、torch 2.11.0、transformers 5.17.0、safetensors 0.8.0；现 PATH 及常用位置未找到 cmake/llama-quantize，安装元数据未见 gguf/sentencepiece/protobuf。保留源码转换 requirements 另要求 transformers 4.57.6、numpy约2.2.6等，与现语言环境不同；不是已证兼容，也不能直接全量装 requirements 覆盖环境。

因此**先交实现角色零模型、零下载/安装的工具闭集准备**：只读确认可复用转换依赖/量化器、已有源码内 gguf、必要版本及 Mac 磁盘/内存工作集；可复用的现有工具经核实足够时才进入已签本节步骤。若必须新增依赖/工具下载、安装或另编译，写具名最小方案（来源、pin、字节、设备、次数/墙钟/磁盘与现环境隔离），回接受→用户签缺项；不得借 base 4.5 GB、旧 pip 或板 BUILD-LLAMA 额度补齐。**当前不是整条流水线已可执行**；用户无需再确认已签的模型路线/六维额度。本轮 consumed=none，正式门与3c停点保持；Consuming=no 沿已有本地诊断分类（零正式 ID/Play/模型 API/云），不伪称执行期零硬件消耗。

open_items: none

### 阶段B基座提示调试授权落实（2026-10-05，Acceptance；诊断执行合同）

本节由用户直接调起的接受会话写（Claude Code `/accept`，非 supervisor 派发，无 Dispatch-Id）；零消耗、只读本机材料并写文档，不是 D/C/R 轮，不签额、不消费 verdict。依据 `docs/authorizations.md`「2026-10-05 P1-ENG-JET-001 — 用户签发基座板上测试与提示迭代（诊断）：传板 ≤800 张/≤45 MB、加载 ≤15、请求 ≤10,000、板上累计运行 ≤12 h（3 天内）、板新增 ≤1 GB、提示版本 ≤8，交互式执行，不进证据；3c 仍停（接受角色会话代录）」的用户原话与所选选项全文，**原话优先**。新增 AC/AC 修订 = 0：这是用户明确的非证据诊断子范围（同冒烟先例），不改变正式验收项；交接 Consuming=no（不创建或消耗 scenario/session/run ID、Play、API 预算、云）。未写明处一律沿「阶段B3b诊断冒烟授权落实」（下称冒烟合同）§2–§7，下面只写差异。

#### 1. 已签额度与记账

| 维度 | 上限与口径 |
|---|---|
| 传板 | ≤ 800 件、≤ 45,000,000 B；只传 §2 的 JPEG 帧原字节，每件 1 次、重试 0，失败件按整件计 |
| 加载 | ≤ 15 次；每次 llama-server 启动计 1，失败也计 |
| 请求 | ≤ 10,000 次；健康、预热、失败、超时都计，不因缓存或失败退回 |
| 板上累计运行 | ≤ 43,200 s；各批从本机批次目录创建到该批收据写完的墙钟之和；截止 2026-10-09T04:00:00Z（「3 天内」读作本地 2026-10-08 日终；接受读法，用户可更正） |
| 板新增占用 | ≤ 1,000,000,000 B，各批累计（帧、输出、缓存、失败保留件），不靠删件抵扣 |
| 提示版本 | ≤ 8 个（P1…P8）；现行 v2 为基线 P0，不计 |
| 确认集 | P0 与 ≤ 2 个入选版本各恰 1 次 |

跨批唯一累计账 `outputs/eng-jet/P1-ENG-JET-001/stageb-base-prompt/budget.jsonl`（追加式，先预约后执行）；任何一维将超即停并回用户，不借其他维度或旧批余额。每批另建本机 `…/stageb-base-prompt/<UTC>/` 与板上 `~/eng-jet/stageb-base-prompt/<UTC>/`（用法同冒烟合同的 DIAG），存该批计划、调用账、原始响应、预测与评分。

#### 2. 数据与隔离

- **调试集 DEV**：`select-eval.blind.jsonl`，441 行、322 帧（19,746,850 B）。**确认集 HOLD**：`eval.blind.jsonl`，609 行、392 帧（17,226,227 B）。来源 `~/TetheredDroneTracking-full/outputs/eng-sft/P1-ENG-SFT-002/`：盲文件在 `data/`，帧为 `upload/frames/<sha256>.jpg`（盲行 `frame_path` 相对 `upload/`）。使用前核对：盲文件行数/字节/sha256 等于 `docs/evidence/P1-ENG-SFT-002-dataset-manifest.json` 的 `files` 同名项；每帧 sha256 等于其文件名。数据根只读、零写入；不符即停。
- **上板的只有**上述帧文件与盲行五个字段（`row_id`、`frame_path`、`surface`、`g4`、`vocab`；经 stdin 送入，不落成板端文件）。`select-eval.jsonl`、`eval.jsonl`、`train.jsonl`、`smoke.jsonl`、任何含 `state`/`target_*`/`gold_*` 的内容、sidecar 与 truth 不上板、不进请求（AC-12 不变）。
- 板上帧落点：新建 `~/eng-jet/stageb-base-prompt/frames/`（首次传板前须不存在、非链接，mkdir 700）；后续批只读复用，使用前按文件名核 sha。HOLD 帧可与 DEV 一并传，也可到确认前再传，都计入同一传板额度。
- **确认集纪律**：HOLD 只跑 P0 与 ≤ 2 个入选版本，各 1 次；任何 HOLD 结果出来后不得据此再改提示或参数。要继续改只能回 DEV；新版本若要上 HOLD，占用上述「≤ 2」。

#### 3. 可调与不可调

- **提示文字**：每个版本是一份完整模板，存本机 `…/stageb-base-prompt/prompts/P<k>.txt` 并记 sha256；`tools/eng_sft/prompt_v2.py` 不改。P0 = 该文件现行构造规则产出的原文（`g4=true` 的行含 g4 段）。版本可改措辞、顺序、示例与三态说明；`g4=true` 行如何拼接须在模板中写明，未另行设计时沿用 v2 的 g4 段原文（DEV 无此类行，只在 HOLD 出现）。不得写入任何来自标注的逐图信息，除盲行五个字段外不得按行分支。
- **请求参数**：可加 llama-server 的 JSON 约束输出（`response_format`/`json_schema` 或 grammar）；`max_tokens` ≤ 256；`temperature` 0、`stream` false、`cache_prompt` false 不变。
- **服务参数**：可设 `--image-min-tokens`（至多 2 个取值），并相应把 `--ctx-size` 调到 ≤ 4096；其余启动参数、进程环境、模型与 mmproj、仅回环 `127.0.0.1:18081`、`--offline` 沿冒烟合同 §4 第 2 项。
- 每次运行的（提示版本、请求参数、服务参数、数据集）组合写入该批计划；同一组合在 DEV 上可重跑，请求照计。
- 板端逻辑仍经 stdin 送入系统 Python（`-I -S -B`，纯标准库）执行，一条 SSH 可连续处理多行；不写板端脚本文件、不部署项目代码。
- 不做：C2/适配器/合并/转换/量化、3c/W/TensorRT、下载/安装/联网、快层、正式 S3/S4/S5、Play、改系统/SSH/沙箱设置。

#### 4. 执行方式与评分

- 用户直接开 `/implement` 交互会话执行，supervisor 不派发。顺序：前置与传板 → DEV 上跑 P0 基线 → 把分数与失败样例给用户看 → 改法经用户同意后跑下一版本 → 用户点名入选版本后跑 HOLD。实现角色可以提出改法，但每个新版本开跑前须有用户在该会话的同意；该同意不是新额度。
- 评分只在 Mac，解析与判据沿仓库现有口径、不改文件：`tools/eng_sft/parse.py` 的 `parse_prediction`（含去围栏）；单目标成功 = 预测 `unique` 且与标注框 IoU ≥ `tools/eng_sft/evaluate.py` 的 `IOU_THRESHOLD`。DEV 至少报：三种状态各自命中率、单目标成功率（按 S/M/L 与 class/color 分列）、有目标误答 none 率、无效输出率、歧义上报率。HOLD 用 `python -m tools.eng_sft.evaluate --manifest <eval.jsonl> --predictions <该版本板上预测> --baseline <P0 板上预测> --out <本批目录下摘要>`。封装脚本放本项 outputs 目录；解释器须 ≥ 3.10（数据根 `.venv-yoloe` 只读使用、不装包）。
- 另记每次运行的时延分布（服务端 timings 与往返）和板上最低可用内存，作诊断读数。

#### 5. 前置、监测与停止（相对冒烟合同的放宽与保留）

- 前置、链路与 SSH 选项、输入解析与校验、禁止项沿冒烟合同 §2、§4、§5。每批开始前核：本合同与账本条目在位、单写者与共享槽位空闲、18081 空闲且无其他模型服务并驻、板可用盘 ≥ 剩余占用额度 + 100,000,000 B。
- 监测放宽为每 ≤ 60 s 采一次（板占用、df、服务存活、可用内存），每次传板与每 100 个请求前另核各维余额；板新增累计达到 900,000,000 B 即停。
- 单个请求超时、HTTP 非 200 或输出无法解析：记为该行失败并继续（解析失败本身就是被测对象）。**停整批**的情形：服务退出或崩溃、OOM、连续 5 个请求失败、任一额度或截止将超、输入校验不符、出现外联或下载迹象、权限被拒。服务崩溃后可在加载额度内重启 1 次并从未完成行续跑；同一批第 2 次崩溃即停、回用户。
- 每批结束（含失败）都停服务、核端口释放、写收据；不删除、不覆盖、不移动任何既有板文件，不清旧件腾空间。

#### 6. 原件、汇报与收尾

- 原件只落 `outputs/eng-jet/P1-ENG-JET-001/stageb-base-prompt/`（不在 git）：各批计划、调用账、原始响应、预测 jsonl、评分 json、提示文本、累计账，以及一份随进度更新的 `summary.md`（各版本对比表、关键失败样例、时延与内存）。不写 `docs/evidence/` 证据工件，不更新 AC-7/8/9 及 `-vlm`/`-quant-equivalence`/`-report`/`-ledger` 等正式 JSON，不形成 PASS/STOP verdict 或门值；状态板只记指针，不记性能数值。汇总是否入仓、调出的提示是否另立项采用，由用户看过结果后定。
- 中间不设接受核清。实现会话每次收工更新交接行 Progress（已用额度的指针）；额度用尽、到截止或用户说结束时，交 Acceptance 核一次资源账（累计账对各批收据、隔离与确认集纪律），随后回用户。
- 3c 仍停在 B-W-TRT-SUPPLEMENT 之前；B-CLOUD/B-CLOUDDEP、B-LOCAL-EXCLUDE-TRANSFER 仍未答。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE` 仅属阶段 A 候选；S1/S2 STOP、补丁未上板、SR 5/5 耗尽、R1-5/6 OPEN、AC-7/8/9 `NOT_RUN` 保持。

open_items: none

### 阶段B传板授权落实（2026-10-04，CLARIFY）

登记轮次 `阶段B传板授权落实`；Dispatch-Id `P1-ENG-JET-001-阶段B传板授权落实-20261004T202332Z-edf4`；Acceptance，Mac mini。依据账本2026-10-04「用户签发 B-SIGN-TRANSFER（TX-ASSETS）：Mac→板 34 件 ≤2,481,617,096 B，各 1 次、重试 0，墙钟 ≤1 h，板新增占用 ≤5 GB（supervisor 会话代录）」(a)–(e)，追加传输合同；不代签额度、不覆盖原AC/原账。本轮consumed=none，未取网络证据、ssh、上板、传输、下载、测试、加载、安装或租云；收工仅按派发要求推送文档提交。

#### 1. 追加 AC 修订与对象闭集

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 25 | CLARIFY（解释AC-10、修订14/15/17/24及§5）：Implementation仅在Mac mini按本节§1–5经既有有线传34件原文件到板，每件1次、重试0；W/G/S分额与总≤2,481,617,096 B共账，整批≤3,600 s、板新增占用含暂存/部分/失败保留件≤5,000,000,000 B。两端余量前置只读核对各1次；任一失败/不足/超时/越限停整批，计次不退回。保持沙箱，目录脚本窄调用，拒绝即停派发；不解压/安装/构建/部署代码/加载/测试，不含云，其他未签维度0。 | artifact: 上述TX-ASSETS账本(a)–(e)、本节§1–5；未来 `docs/evidence/P1-ENG-JET-001-stageb-transfer.json/.md` | K1K3K4 | 2026-10-04 |
| AC-11 修订 4 | CLARIFY（解释AC-11及修订3，关联AC-10/12）：34件身份/字节/sha按本节§1运行时取；传前源文件逐件核字节/sha与绑定链，传后板上逐件stat/sha256sum与源期望双比对，符合才同目录原子改名；不符/缺读数即停整批、保留现场、不重传。只有保留源码副本可复用，不重取自动归档；原件/原下载失败账不改，输出脚本/计划/日志/标签/代码束不上板。 | artifact: 原 `stageb-download.json` objects/binding、`stageb-source-archive.json` archive/binding_chain及GGUF具名账本；未来同名stageb-transfer.json/.md；cmd: 本节§3板端逐件核验形式 | K1K3K4 | 2026-10-04 |

归因：用户具名TX-ASSETS授权及既有AC-10/11/12资产/信封义务的执行解释，新增AC=0；非C轮读码增项，不变目标/模型/协议/STOP线，不消费新verdict。只迁移已核资源，不修改模型决策或部署运行代码，不签B1代码停点完成；未来不可重跑模型/板端实测仍须依赖代码先C/R。

- **TX-WHEELS**：仅 `docs/evidence/P1-ENG-JET-001-stageb-download.json` `objects` 中kind=W且outcome.verdict=OK的31件；取project/version/filename/file/expected_bytes/expected_sha256/actual_bytes/actual_sha256，与binding同filename唯一项及原metadata固定身份交叉核。该JSON `output_dir_repo_relative` 须等于本项输出根唯一 `stageb-download-*` 目录；31件file须为该目录直接子普通文件、非符号链接。每件期望/原实际B及sha须一致，重加516,980,330 B。不能把原批两件GGUF失败项或脚本/请求账当输入。
- **TX-GGUF**：仅 `outputs/eng-jet/P1-ENG-JET-001/stageb-gguf-user/` 两件 `Qwen3VL-2B-Instruct-Q4_K_M.gguf`、`mmproj-Qwen3VL-2B-Instruct-F16.gguf`；按filename从账本「用户决定两件 GGUF 由本人在 Mac mini 自行下载」(a)解析期望B/LFS内容sha，与「用户反馈两件 GGUF 已本人下载」读数及metadata固定身份对照。期望各1,107,409,952/819,394,848 B，合计1,926,804,800 B；只复用「阶段B用户GGUF核清」两件，不新下载、不用原批失败结果代替。
- **TX-SOURCE**：仅 `docs/evidence/P1-ENG-JET-001-stageb-source-archive.json` `archive.file/bytes/sha256` 指向的保留普通文件1件、37,831,966 B；沿binding_chain核固定commit/原响应与归档身份，不抄sha/实际批次目录名进合同、不重取、不解压内部验commit。继续披露自动归档可能变化及只绑定这份返回实体的主张上限。
- 三类共34个互异安全basename，源路径必须落在上述已核目录、非链接，不含标签/真值/盲材料/帧/代码。Implementation离线机器生成计划并逐件现算源B/sha，核算前后size/mtime_ns/inode不变，与上述期望双符合；缺项/多件/歧义/变化即在连板前停回Acceptance，不联网补查、不替换源文件。实际SHA/路径/HEAD只在机读执行证据运行时生成；既存来源快照不因账本新增条目而重写。

#### 2. 前提、两端余量与独占落点

- 执行角色Implementation、控制机器Mac mini；板为本项既有用户Jetson Orin Nano 8GB Super。目标从 `docs/evidence/P1-ENG-JET-001-relay.json` `link.ssh` 运行时解析唯一SSH目标，当前证据为 `jetson@192.168.8.2`（有线，端口22），与§8.2/已授权有线地址存键核对；无新的Host别名，不转Tailscale/公网/其他设备。复用已有known_hosts、`BatchMode=yes`、`StrictHostKeyChecking=yes`、`ConnectionAttempts=1`、`ConnectTimeout=15`、`Compression=no`；不keyscan/TOFU/忽略键、不改 `~/.ssh/*`、系统/网络设置。
- 批次启动前先离线核本节§5放行、源计划、原started/attempt账、共享槽位及单写者；FRAME在Play/采集占槽时等退出，不抢槽、不改其他交接。Mac仅新建 `outputs/eng-jet/P1-ENG-JET-001/stageb-transfer-<UTC>/`（已存在即停），放脚本/计划/原始收据/日志；不复制34件源文件，不打包。UTC目录不是正式ID。创建即持久记录started_utc/deadline，继承整批1 h计时，不从脚本或scp启动重新算。
- **传输前余量只读核对各一次**，计入本批墙钟，不借已耗尽B-PRECHECK：Mac用标准库 `os.statvfs(<本批目录>)` 的f_bavail×f_frsize读可用B并记录现有输出/证据占用基线；板端唯一前置只读命令形式为 `ssh <固定选项> <目标> 'LC_ALL=C timeout -k 2 <剩余秒> sh -c <只读块>'`，块内容限 `id -un; printf "%s\n" "$HOME"; test -d "$HOME/eng-jet"; test ! -L "$HOME/eng-jet"; df -B1 --output=avail,target "$HOME/eng-jet"; stat -f -c "%S %T" "$HOME/eng-jet"; du -s -B1 "$HOME/eng-jet"; du -sb "$HOME/eng-jet"; test ! -e "$HOME/eng-jet/stageb-transfer-<UTC>"; test ! -L "$HOME/eng-jet/stageb-transfer-<UTC>"`（Implementation令各子命令失败即返回非0，UTC段仅由本批计划展开；不运行本段文本于本轮）。原stdout/stderr/rc保存在Mac，板落点绝对路径只从本次HOME读数展开、核用户为既有jetson；板不写工件，SSH/PAM/登录服务附带写入按本项既有披露保留、不清理。
- 两端各自可用B均须≥5,000,000,000 B，才能容纳本批板新增占用封顶及Mac仅记录的保守余量要求；这不是新Mac加工/复制额度。缺工具/余量未知/不足/目标已存在/用户或目录不符即停、不传，不删除旧件腾额度、不另跑前置核查。历史151GB/板快照不代替执行读数。
- 板上落点为既有 `~/eng-jet/` 下新建独占 `stageb-transfer-<同一UTC>/`；前置通过后普通用户一次 `mkdir -m 700 -- <展开的绝对落点>`，不得mkdir -p复用/覆盖旧目录，不动旧A/wheels/sysvenv/runtime/缓存。不新建板端脚本/manifest/log；本次板新增是该目录文件与目录元数据，既有占用不扣回。记录计划峰值：串行单份存储，34件各按板文件系统分配单位向上取整，加目录/元数据保守增长余量，须有受控上界≤5GB；无法证明（文件系统分配行为未知等）即停。逻辑B/分配B分列，取较大口径保护，不把输入总B当实际峰值。

#### 3. 传输与板端核验命令形式（仅未来由目录脚本调用）

- 本机唯一入口 `python3 <本批输出目录>/<脚本>.py`，保持会话沙箱启用。Implementation只在该目录写标准库驱动脚本，以subprocess参数数组调用ssh/scp，远端路径按shell安全引用；不用内联Python、本机其他入口、curl/SDK/rsync/sshpass/关沙箱/备用通道。命令中的basename/UTC/绝对路径必须来自§1闭集与§2新目录，不执行来源任意字段。
- CLARIFY（AC-10修订26，解释上行）：脚本名固定为 `transfer.py`；顶层发令文本为 `python3 ~/TetheredDroneTracking/outputs/eng-jet/P1-ENG-JET-001/stageb-transfer-<本批UTC>/transfer.py`，不带参数、包装器、内联代码或复合命令，UTC由§2本批目录运行时解析。**会话沙箱启用；仅用户具名放行的该excludedCommands条目对应的目录脚本调用在沙箱外运行**，其ssh/scp子进程随之在沙箱外；具体申请与执行前核对见§5。本解释不改变§1–4对象、路径生成、传输/核验方法、前置、计次、截止、越界处置或已签数值。
- 逐件串行（W按filename排序、G按filename排序、最后S）：形式 `scp -B -P 22 -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectionAttempts=1 -o ConnectTimeout=15 -o Compression=no <已核源绝对路径> <目标>:<独占落点>/<basename>.part`，单源单目标、每件一次；不递归/通配符/并行/重试/续传/重发。只传原文件有效载荷，不传本机脚本/计划/代码/数据/日志；SSH命令与小型核验stdout是传输控制/收据，不是TX-CODE-DATA-LOGS部署资产。
- 每件scp成功返回后，立即一次只读 `ssh <固定选项> <目标> 'LC_ALL=C timeout -k 2 <剩余秒> sh -c <核验块>'`：核验块仅 `stat -c "%s %b" -- <该.part>; sha256sum -- <该.part>; du -s -B1 <独占目录>; du -sb <独占目录>`，子命令失败非0。板端现算整数B与sha均须逐字等于§1本机源期望；本机复核源size/mtime_ns/inode仍未变，保存原输出/rc。符合且占用未越限后才一次同目录 `mv -T -- <该.part> <basename>`（先确保最终文件不存在），原子改名、不复制第二份；核验不符/缺读数/rename失败立即停整批、不再下一件。
- 34件完成后一次只读列出独占目录普通文件与逻辑/分配占用，核集合恰等于计划、无残留.part或额外文件；逐件核验收据须34/34，无sha未知项，不能凭scp rc=0声明成功。原件、失败.part与板现场均保留；不解压、不安装、不构建、不加载模型、不跑测试或硬件性能探测、不部署已复核补丁。

#### 4. 计次、截止、占用与异常

- 一次整批，前置板余量读取只执行1次且启动前记已预约；拒绝/连接/认证/超时亦用尽该前置，不用新派发重试。每件scp调用前在Mac持久记attempt-start并占1/1，保守预约该件全部期望B，同时累计W/G/S与TX-ASSETS；成功、部分/短传、权限/沙箱/网络拒绝及sha失败均计已用，预约不撤销。未调用件NOT_RUN、在途/实际发出未知件UNKNOWN；不能把未发出写成已传，也不能因未知/失败归零或另开目录续跑。
- 有效载荷W≤516,980,330 B、G≤1,926,804,800 B、S≤37,831,966 B、总≤2,481,617,096 B共账，分额不能互借。按一次scp最多发送一个固定源的全部内容保守占额；传前/后源未变，禁自动应用级重发。网络封装/底层TCP重传不是另一件有效载荷；无法核实际发送B时明确UNKNOWN，保守预约不冒充实测B，不只加成功件。
- 1 h=3,600 s，5 GB=5,000,000,000 B。整批从Mac独占目录创建至停止/收尾，包含脚本准备、前置、源哈希、连接/传输、板哈希、证据写出；保持同一UTC截止与单调耗时，不能重新计时。每步前核剩余时间，为强杀/收尾预留余量；本机脚本对scp/ssh进程组设剩余预算，远端核验/mv也加不超过剩余预算的timeout（预留-k 2），到截止终止本批进程、不后台脱离、不再连接。收尾推送超出截止须如实记录，不宣称全程合规。
- 板占用不超过5GB：scp直接写唯一.part、同目录rename，无解压/缓存/第二份。每次传前以已核目录逻辑/分配占用加本件按分配单位取整及保守元数据余量预留，传后核实际占用、记录峰值；预留不足即在下一scp前停。板初始余量≥5GB仍不证明其他进程不会占盘，ENOSPC/外部占用影响如实失败即停。保留件仍计占用与预约传输量，禁止删除腾额度。结束/失败时用最近可靠读数，截止/失联/拒绝后不另登板补证，未核现场/峰值列UNKNOWN，不以最终成功文件替代历史峰值。
- **任何一次失败停整个批次并回交**（含连接中断、超时、权限/沙箱拒绝、sha不符、目录/余量/占用/字节越界、源变化、证据无法持久写出）；保留原stderr/rc、已用/预约量、最后读数和部分件，不重传/续传/换源/换机器/另会话，不修SSH或系统设置。用户新授权前不可继续，失败对象尝试不退回；未执行对象也不能由新派发自动续跑。

#### 5. 本机放行、证据、轨道与回交

原只读设置快照（保留）：已有 `Bash(python3 ~/TetheredDroneTracking/outputs/eng-jet/P1-ENG-JET-001/:*)` 窄规则；sandbox.network.allowedDomains仅来源网站/HF候选，**没有192.168.8.2**。此前board预检证据§2记载关闭会话沙箱，本次禁止沿用，不把历史连通/SSH存键当沙箱放行。本轮不改设置、不试连、不做权限拒绝探测。

**原needs_user B-LOCAL-ALLOW-TRANSFER已撤回（用户不采纳，原文保留在下一段，不再构成推荐或执行条件）。** 出处为账本2026-10-04「用户不采纳把板 IP 加进 allowedDomains：维持现有沙箱放行，SSH 到板走 excludedCommands 具名单独申请（supervisor 会话代录）」(a)–(d)；现行申请为下列B-LOCAL-EXCLUDE-TRANSFER。

**needs_user / B-LOCAL-ALLOW-TRANSFER**：推荐用户本人在Mac mini的执行会话沙箱中仅放行既有板目标192.168.8.2的SSH/SFTP（TCP22），保留沙箱启用及已有目录python3窄规则，并反馈已完成；理由是当前静态放行未齐，传板授权不允许代理改设置或关闭沙箱。无需重新签TX-ASSETS数值、不问已答GGUF/下载主机；不推荐通配符、关闭沙箱或改SSH/系统设置。放行能力不支持该窄目标时保持待用户，不让代理换通道。用户完成后交Implementation，先离线核当时设置/调用权限、旧账和共享槽位；再仅按本合同做一次两端余量前置，齐全才传。任何权限分类器/沙箱拒绝即停整个派发，原错误保留、计数不归零、不用新写法或会话重试。

**阶段B传板排除申请（2026-10-04，Acceptance，CLARIFY）**；Dispatch-Id `P1-ENG-JET-001-阶段B传板排除申请-20261004T212243Z-714e`。本轮只读本机设置，确认上述allow规则/来源域名仍存在，板IP未加入、excludedCommands条目尚不存在；只起草申请，不签本机排除许可或额度，不联网核文档、不ssh/传输/下载/测试/加载/安装/租云，Git同步与文档提交推送按派发收工要求执行。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 26 | CLARIFY（解释修订25的沙箱/目录脚本前提、§3/§5；来源为上述用户不采纳B的账本(a)–(d)）：会话沙箱启用；仅用户另行签发的B-LOCAL-EXCLUDE-TRANSFER条目对应的顶层目录脚本调用在沙箱外运行，权限规则仍适用。Implementation执行前只读核账本签发/用户本人设置反馈、§5条目逐字存在且生效、allowedDomains未加板IP及既有allow规则未变；未齐即停，不试连、不替换调用规避拒绝。§1–4与TX-ASSETS已签数值不变；本条不授排除许可或新增额度。 | artifact: 上述账本(a)–(d)、本节B-LOCAL-EXCLUDE-TRANSFER申请；未来 `docs/evidence/P1-ENG-JET-001-stageb-transfer.json/.md` 的离线放行核对 | K1K3K4 | 2026-10-04 |

归因：原接受侧将代理域名放行误用为SSH放行，依据用户账本改为具名排除申请与既有AC-10执行前提解释；新增AC=0、AC修订1，不是复核finding、不改原finding归因或R1-5/6 OPEN。原AC-10修订25和上述旧推荐原文保留，沙箱前提以修订26为准；§1–4仅追加§3发令解释，数值/前置/计次/越界规则不变。

**文档判断与不确定处。** 判断依据为[Claude Code官方Sandboxing文档](https://code.claude.com/docs/en/sandboxing)的已知内容，本轮按派发要求未访问页面，不能声称核验了2026-10-04最新页面或本机匹配实现。接受侧判断：allowedDomains约束代理承载的HTTP/HTTPS，不能给普通SSH/SCP的直接TCP连接放行；沙箱内脚本的子进程继承沙箱，所以只排除脚本内部的ssh文本不能解决该顶层调用。excludedCommands匹配顶层Bash命令文本，被匹配的命令及其子进程在沙箱外运行，仍须通过权限规则；排除整个驱动脚本也意味着其本机文件操作失去该次沙箱隔离，并非只解除TCP22限制。以下按已知命令模式的 `*` 通配语法起草，不套用permissions的 `:*` 写法；本机版本的模式匹配/上层设置是否覆盖尚未动态验证，需执行前离线核生效来源，不能用试连补证。

**needs_user / B-LOCAL-EXCLUDE-TRANSFER（待签；推荐项与理由）：** 推荐用户仅签发下列单条原文；固定解释器、绝对输出根、批次前缀及脚本名，只让本次资产传板驱动调用退出沙箱，其他前提沿用§1–4，不扩大传板授权。

```json
"python3 ~/TetheredDroneTracking/outputs/eng-jet/P1-ENG-JET-001/stageb-transfer-*/transfer.py"
```

- **设置位置/本人操作**：Mac mini仓库的 `~/TetheredDroneTracking/.claude/settings.local.json`，由用户本人在 `sandbox.excludedCommands` 数组中追加这一条字符串（保留其他设置与已有条目），并反馈具名签发及修改完成；代理只读，不代改。本申请不是要求覆盖整个JSON，也不授予自动批准所有命令。
- **最窄可行覆盖**：因§2批次UTC目录必须运行时生成，模式只在 `stageb-transfer-` 与 `/transfer.py` 之间使用 `*`；不排除通用 `python3`、`ssh`、`scp` 或本项整个输出根。匹配的是§3所定**顶层完整调用文本**，不是脚本内的ssh/scp文本；不要加 `Bash(...)` 包装。技术模式本身不能识别“本次”或验证脚本内容，未来同形目录/尾部路径也可能匹配；合同只准本批新目录内标准库驱动、无命令参数或复合命令，并须离线核脚本普通文件/非链接/真实路径及内容仅含本节授权动作。脚本内读源/记账/ssh/scp均在该次沙箱外执行，子进程不是单独保留在沙箱内。
- **与现状的关系**：`permissions.allow` 中已有 `Bash(python3 ~/TetheredDroneTracking/outputs/eng-jet/P1-ENG-JET-001/:*)` 原文保持，仍负责调用权限；excludedCommands仅决定该调用是否沙箱隔离，不代替allow或推翻deny/其他权限判定。`sandbox.network.allowedDomains` 现有来源网站条目保持，不添加 `192.168.8.2`、其他板地址或通配域名；会话沙箱保持启用，不临时关闭，不添加任意unsandboxed回退许可。
- **有效期/撤销建议**：仅本次TX-ASSETS批次的准备、一次前置/传输/核验与收尾；推荐本批成功、失败或中断收尾后由用户本人立即删除此单条（其余设置保持）。未签或撤销后无执行许可；同形未来目录不继承许可。超期、路径/入口更改、重试/续跑均回用户具名决定，不由排除条目持续存在推定授权。
- **不选B/C的理由**：账本(a)已不采纳加板IP，(c)已不采纳关沙箱；B不能为普通SSH提供代理连接能力，C会扩大整个调用/会话的隔离例外。具名排除是账本(b)要求的独立申请，当前仍待用户签，不以TX-ASSETS数值已签或本申请推荐代替决定。

**执行前只读核对与停下条件（Implementation）：** 用户签发须由当场会话逐字入账，且本人改设置并反馈后才接手。离线读取上述设置文件，确认excludedCommands数组中字符串逐字存在、既有Bash允许规则逐字保留、allowedDomains未加板IP且原来源条目未变；同时只读核实际执行会话沙箱启用、加载该本地文件且条目未被更高优先级/受管设置忽略，及本机离线可用配置说明是否支持该命令模式。任一缺失/不符/生效未知/权限拒绝即停派发、保留原错误回用户或Acceptance，不发SSH/SCP或连通测试，不改模式/关沙箱/换通道。核齐后仍先按§2离线核源计划/旧账/共享槽位，再启动一次两端余量前置，满足才传；本机核对不消耗板连接尝试，已启动的批次/前置/逐件尝试一律按§4计次，不归零。执行证据记录条目原文、实际顶层命令、设置来源/离线核对结果与不确定处；后续失败保留证据并停整批，34件未传事实及其他未签维度0保持。

**阶段B传板沙箱落实（2026-10-04，Acceptance，CLARIFY）**；Dispatch-Id `P1-ENG-JET-001-阶段B传板沙箱落实-20261004T223202Z-6d16`。登记轮次 `阶段B传板沙箱落实`，Mac mini，零消耗：本轮未联网、未ssh/上板/传输/下载/测试/加载/安装/租云，未修改任何 `.claude/` 设置文件（仅只读核对）。依据账本2026-10-04「用户选乙：Mac mini 会话不开沙箱、合同 §5 改以权限允许规则加合同约束为控制；允许规则去冒号为用户本人有意修改（supervisor 会话代录）」(a)–(c)及同日「用户签发 B-LOCAL-EXCLUDE-TRANSFER：同意传板具名 excludedCommands 单条，按「阶段B传板授权落实」§5 执行（supervisor 会话代录）」。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 27 | CLARIFY（解释修订25/26的沙箱与排除前提、§3/§5；来源为上述两条账本）：本次传板在Mac mini执行时会话沙箱未启用（用户选乙）；控制手段为权限允许规则 `Bash(python3 ~/TetheredDroneTracking/outputs/eng-jet/P1-ENG-JET-001/*)`（新的逐字基准，去冒号为用户本人有意修改）加合同§1–4约束（对象闭集、单一顶层发令 `python3 <本批目录>/transfer.py`、前置、计次、截止、越界处置不变）。已签B-LOCAL-EXCLUDE-TRANSFER条目保留、不再作执行前提，沙箱未启用时其无实际效果，如实写明。修订25「保持沙箱」与修订26「会话沙箱启用」「排除条目逐字存在且生效」等冲突前提以本条为准，原文保留。§1–4与TX-ASSETS已签数值不变；本条不授新额度。 | artifact: 上述两条账本、本节沙箱落实块；未来 `docs/evidence/P1-ENG-JET-001-stageb-transfer.json/.md` 的离线放行核对 | K1K3K4 | 2026-10-04 |

归因：原排除申请前提随用户选乙改为「权限允许规则+合同约束」控制与修订25/26执行前提解释；新增AC=0、AC修订1，不是复核finding、不改原finding归因或R1-5/6 OPEN，不放宽§1–4对象、前置、计次、截止、越界处置。

**改写执行前只读核对与停下条件（Implementation，自本修订起生效，上方旧段落中冲突部分以本段为准）：** 离线读取 `~/TetheredDroneTracking/.claude/settings.local.json`，确认 `permissions.allow` 中 `Bash(python3 ~/TetheredDroneTracking/outputs/eng-jet/P1-ENG-JET-001/*)` 逐字存在、`sandbox.network.allowedDomains` 未加板IP且原来源条目未变、未新增其他排除或放行条目；沙箱状态如实记录（预期未启用），不得以开/关沙箱或改设置规避，代理不改任何设置文件。任一缺失/不符/权限分类器拒绝即停派发、保留原错误回Acceptance或用户，计数不归零，不发SSH/SCP或连通测试，不换通道。核齐后仍先按§2离线核源计划/旧账/共享槽位，再启动一次两端余量前置，满足才传；本机核对不消耗板连接尝试，已启动的批次/前置/逐件尝试一律按§4计次，不归零。执行证据记录允许规则原文、实际顶层命令、设置来源/离线核对结果、沙箱状态与不确定处；后续失败保留证据并停整批，34件未传事实及其他未签维度0保持。

**needs_user 更新：** B-LOCAL-EXCLUDE-TRANSFER已签（账本同日条目）、沙箱路径已按用户选乙改为权限允许规则加合同约束；本节上文「待签」表述以本条为准，不再构成待决项。执行前提已齐，交Implementation按§1–5与AC-10修订27执行传板（Owner=Implementation），完成或中断立即回Acceptance核清。本轮needs_user: none。

open_items: none

未来由Implementation生成 `docs/evidence/P1-ENG-JET-001-stageb-transfer.json` 与同名 `.md`（本轮不预写结果）：JSON含来源文件绑定/授权标题、34件机器生成计划、目标/独占路径、脚本调用与机器、执行前后git凭据、离线放行/槽位、前置两端可用B/基线/rc、started/deadline/UTC/单调耗时、逐件attempt和scp start/end/实际发出或UNKNOWN、期望/板端实际B/sha/原输出/rename、W/G/S与总已用/预约/余量、逻辑/分配占用及受控峰值、成功/失败/.part/NOT_RUN/UNKNOWN和停止原因。Mac保留原始计划/调用/收据账；MD只写JSON/原始目录指针、数字摘要、边界和needs_user，不回写旧下载/source-archive/元数据快照或重建A账本。完成或中断立即交Acceptance核清，不自行继续安装/构建等后续。

Consuming=no：本次资产迁移不创建/消耗正式ID、Play或模型API预算，独占UTC目录不是run ID；传输/时间/磁盘仍独立计账、不借SR/FRAME/旧批额度。当前Overall REVIEW_PASSED / Lifecycle ACTIVE保持；不消费新复核verdict、不签DONE、不推出板端运行兼容/时延/显存结论。S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN与AC-7/8/9 NOT_RUN保持。TX-CODE-DATA-LOGS/TX-TOTAL、安装/解压/构建/部署/模型/数据/测试及其加工峰值/墙钟仍0、不含云；完整双向总量与后续执行事实UNKNOWN，不以本次封顶补未知。

open_items: none

### 阶段B传板核清（2026-10-04，Acceptance）

登记轮次 `阶段B传板核清`；Dispatch-Id `P1-ENG-JET-001-阶段B传板核清-20261004T225627Z-007b`。Mac mini，零消耗只读核清；不属D/C/R轮、不新增AC或修订、不签额度/DONE/兼容性结论。本轮只读 `docs/evidence/P1-ENG-JET-001-stageb-transfer.md/.json` 与本机批次目录（输出根下唯一 `stageb-transfer-*` 运行时解析为 `stageb-transfer-20261004T225001Z`，与JSON `output_dir_repo_relative` 一致；原始 plan.json/attempts.jsonl/invocations.jsonl/state.json/raw/ 不改不删）；未发网络请求、未ssh/上板/传输/下载/测试/加载/安装/构建/租云，未修改任何 `.claude/` 设置文件（仅只读比对）。consumed=none。

#### 1. 计划闭集与源双比对（通过）

- 批次目录唯一；盘上 plan.json 与证据JSON objects 逐件一致：34件、34个互异安全basename，W31/G2/S1，顺序W按文件名、G按文件名、S最后，seq 1–34。
- W31：与 `docs/evidence/P1-ENG-JET-001-stageb-download.json` objects（kind=W、verdict OK）逐件expected/actual字节+sha一致，合计516,980,330 B；源路径均落在该JSON解析的唯一下载批次目录、普通文件非链接。
- G2：与账本「用户决定两件 GGUF…」(a)期望字节/LFS sha一致（1,107,409,952/819,394,848 B；089d75…/c3d5af…），合计1,926,804,800 B；源在 `stageb-gguf-user/`。
- S1：与 `docs/evidence/P1-ENG-JET-001-stageb-source-archive.json` archive bytes/sha256一致（37,831,966 B）。
- 逐件执行记录：源离线现算字节/sha=期望、算前后size/mtime_ns/inode不变；scp前与板端核验后两次restat全等；attempt均1/1、status OK；sent=reserved=expected。

#### 2. 板端原输出、改名与终列（通过）

- 独立重解析 raw/ 下34份板端核验stdout（与JSON镜像逐字相等）：`stat %s`=源期望字节、`sha256sum`=源期望sha、对象为.part、du路径为独占目录；du分配随串行单调不减。
- 34次 `mv -T -- <.part> <final>` 全rc=0、stderr空；终列 `find` 恰34个普通文件、集合=计划basename集、无.part/额外文件；终值du分配2,481,704,960 B/逻辑2,481,617,096 B=载荷总量。
- 105次调用argv逐一符合合同§2–§3形式（ssh固定选项+唯一既有目标；前置只读块逐片在；`mkdir -m 700 --`一次；核验/改名/终列形式；全部 `LC_ALL=C timeout -k 2 <剩余秒>` 包裹且≤3,600）；scp argv逐字符合§3；无rsync/curl/备用通道；105次全rc=0、无超时；ssh 71+scp 34、重试0。
- 计次：attempts.jsonl=前置预约1/1+34×(start/scp_end/ok)，无重试；state.json outcome COMPLETE；脚本sha256与盘上transfer.py实算一致；git_pre=git_post、porcelain均空。

#### 3. 上限符合与前置读数（通过）

| 维度 | 读数 | 用户签发上限 | 判定 |
|---|---|---|---|
| 件数/计次 | 34/34（W31、G2、S1各1/1），重试0 | 34、各1次、重试0 | 符合 |
| 有效载荷W/G/S/总 | 516,980,330 / 1,926,804,800 / 37,831,966 / 2,481,617,096 B（已用=预约=核验送达） | 同左分额共账 | 符合 |
| 批次墙钟 | 226.666 s（started_utc.txt 22:50:01Z目录创建→脚本结束22:53:47Z；截止23:50:01Z） | ≤3,600 s | 符合 |
| 板新增占用 | du分配2,481,704,960 B（观测峰值=终值）；计划受控上界2,518,396,928 B | ≤5,000,000,000 B | 符合 |
| 前置两端余量 | Mac statvfs可用148,824,813,568 B（f_bavail×f_frsize重算一致）；板df可用165,676,867,584 B | 各≥5,000,000,000 B | 符合 |

- 前置板端块rc=0、user jetson、HOME /home/jetson、落点事先不存在非链接；mkdir rc=0。离线放行核对：允许规则逐字存在、excludedCommands单条、allowedDomains十条无板IP、无sandbox.enabled、沙箱未启用按修订27控制；当前 `.claude/settings.local.json` 与运行时记录sha256逐字相等（本批未改）。

#### 4. 自报偏差裁定（证据md §3）

实现自报：批次目录创建前，开工只读环境核对时执行过一次无操作 `python3 -c 1` 与一次 `ps … | grep -c` 只读管道。二者不在invocations.jsonl的105次调用内、不是传输调用、未触板/源文件/网络。裁定：违反的是派发写法约束字面（合同内顶层发令与105次调用形式本身全部符合§1–4），**记实现执行方法错误/写法不遵从1次**（先例：「阶段B核验核清」对同类 `python3 -c 1` 自报的归因）；不占任何已签维度计次、不返工、不回退计次、不新增资源。本批34件有效性由板端独立stat/sha256sum原始输出与本机源期望双比对及完整收据链支撑，与该两次本机只读动作无因果关系，**不影响本批结果效力**。不冒签复核finding/RED_LINE，不给新通道许可；偏差记录保留供用户知悉，后续派发仍须严格遵守写法约束。

#### 5. 结论与needs_user

**B-SIGN-TRANSFER/TX-ASSETS：已传并核清。** 34/34件原文件字节一致落在板上独占目录，全部维度在用户签发上限内；执行与合同§1–5及AC-10修订25/26/27、AC-11修订4相符。主张上限：只证明落盘字节一致；未解压/安装/构建/加载/测试/部署/租云，不推出板端运行兼容、时延或显存结论；TX-CODE-DATA-LOGS/TX-TOTAL及其余未签维度仍0、不含云。

needs_user（现行条目见「阶段B预检答复落实」§5现行段）：①推荐用户本人删除B-LOCAL-EXCLUDE-TRANSFER排除条目（理由：合同「阶段B传板授权落实」§5有效期仅本批、批次已收尾、同形未来目录不应继承；代理不改设置）；②后续INSTALL-W/BUILD-LLAMA等维度引用板上已核清34件、逐行给推荐值与仍缺前提，生效仍0、不含云，由用户逐维度具名签发。Overall REVIEW_PASSED / Lifecycle ACTIVE保持，不消费新verdict、不签DONE；S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN与AC-7/8/9 NOT_RUN保持。

### 阶段B构建核清（2026-10-05，Acceptance）

登记轮次 `阶段B构建核清`；Dispatch-Id `P1-ENG-JET-001-阶段B构建核清-20261005T040434Z-67f7`。本轮只读本机证据/原件及git历史，不执行驱动、不ssh/触板、不联网取证、不运行产物/模型/测试、不签新额度、不写授权账本；consumed=none。不属新C/R轮，不新增AC或修订，不签独立verdict。

#### 1. 原件与修订29差异核清

入口：`docs/evidence/P1-ENG-JET-001-stageb-build-rerun.md` §1–6及同名JSON；第一批 `docs/evidence/P1-ENG-JET-001-stageb-build.md/.json`。两批本机原件目录分别从JSON `output_dir_repo_relative`解析，不手抄目录名/SHA/HEAD。

- 两批`build.py`现算sha与各JSON `script.sha256`一致，`state.json`与各证据JSON字节完全一致。新批调用账74行=37对start/end；原批2行=1对前置。逐对seq/label、stdout/stderr字节与现算sha、raw rc均与收据一致；无未闭调用，ssh rc均0，无本地超时；端口/严格键/BatchMode等参数与唯一relay目标一致。新批恰为前置、mkdir、解压、配置、构建、产物各1次及采样31次，无scp/重试/产物执行调用。
- 第一批JSON、MD、驱动现算sha与新JSON `first_batch`绑定值一致，原state及原stdout/stderr/rc与原账一致，原件未发现变动。原批仍是PRECHECK_FAILED、仅precheck；0 B为未进入mkdir/解压/构建的控制流事实，非du实测，不把SSH附带写入称0。未删原件。
- 读取两份驱动的完整文本diff，差异仅属于修订29§3闭集：D-1拆为三次`command -v`且三行判据不变；round/Dispatch/新证据名/新旧独占目录校验及旧批只读绑定；累计墙钟扣ceil(3.766)=4 s；累计占用保护。注释/schema、旧批绑定与cap字段均属上述命名/累计记账；固定构建参数、执行栈、监测/失败判据未改。
- 按各JSON `git_pre`运行时解析历史提案/账本，现算历史sha与执行快照一致；当前重跑绑定的提案/账本亦匹配。第一批绑定的是修订29前版本，不能因当前提案/账本sha不同改判原件变动。两批执行前后各自HEAD相同、porcelain为空，只证明当时快照；本轮不改写这些值。
- transfer/source-archive/relay JSON现算sha与新批绑定一致；S期望字节/sha、板端s_stat/s_sha原输出、保留本机归档现算字节/sha交叉符合。只绑定保留自动归档返回实体；内部commit未核边界保持。

#### 2. 步骤、监测与外联证据核清

| 核清项 | 读数与判断 |
|---|---|
| 前置与S重核 | ssh rc=0、单调0.742 s（含S sha，不另造独立sha耗时）；原stdout各必需块rc=0，prior_builds无匹配rc=2仅信息。df可用163,185,582,080 B；cmake3.28.3、nvcc13.2/V13.2.78、gcc/g++13.3.0、Make4.3；tools三行逐字为/usr/bin/gcc、g++、make；cuda链接/sbsa目录、新目录absent及S非链接普通文件37,831,966 B、sha均符合。JSON派生rc=null仍保留，核清采用原块rc，不由整体exit0推出满足。 |
| 解压/结构 | mkdir rc=0/0.233 s；tar与ssh rc=0/1.634 s，原top/types确认单一普通顶层目录；解压只写新src，不改传板S。实际顶层名与src路径由unpack解析。 |
| 参数 | 从原合同§2解析两行命令，以JSON路径替换占位，argv逐项对比：生成器、10个-D的顺序/逐字值（包括空CCCL值）、nvcc路径、Release/-j4/llama-server目标全部一致，无追加定义；引号仅shell表示差异。调用账远端block含同一命令。 |
| 配置/构建 | 配置ssh/步骤rc均0，单调12.200 s；构建ssh/步骤rc均0，单调1,724.422 s。raw与JSON尾段/强弱扫描一致；产品ls显示板日志大小均小于1 MiB抓取上限，本次尾段覆盖该日志全文。配置有非git归档的fatal/warning文字、编译有UI未嵌入警告，原文保留，未改判为构建失败。CMake工具链探测不作为项目测试或运行兼容证据。 |
| 采样/停止 | 31次=基线1+解压后1+periodic28+终值1，各采样原行/rc与JSON一致；循环每60 s后调用，周期完成UTC间隔60.309–60.373 s，含采集开销。双du、df及ss各项读数保留；无缺采样/超限/kill或重试记录。所有远端调用按累计余额以LC_ALL=C timeout -k 2包裹，未重置成7,200 s。 |
| 占用/余量 | 基线du -sb=0 B、du -s -B1=16,384 B；du -sb为逻辑/表观字节，不能称分配量。峰值/终值分别393,323,276 B与411,414,528 B，取较大口径保护5e9 B；第一批工件0 B，累计采样峰值411,414,528 B。最低df余量162,773,512,192 B≥1e9；MemAvailable最低4,539,972 kB只作采样读数、不证运行显存。监测写log在du读取后，终值亦非整个后续保留期的最终磁盘量；瞬时峰值UNKNOWN。 |
| 产物边界 | 产物调用仅stat/ls，原rc均0；llama-server非空普通文件72,424 B，旁有动态库；原账与驱动未调用产物、不加载G2、不推理/冒烟/项目测试/安装W/部署。只证明产物存在，不证动态链接可加载或可运行。 |

**外联判据须保留限制。** 逐一重读/重算配置与构建日志扫描：强模式闭集（Performing download step、Cloning into、-- Populating、file(DOWNLOAD、-- Downloading、Downloading+URL、Could not resolve host、curl错误）命中0；弱模式（URL/download/fetch）3行：download.cpp编译进度1行、离线UI可手工下载的警告2行，均不是下载动作。没有主动下载/子模块调用或正向外联日志证据。

31次ss rc=0、`ss_owned_lines`/`ss_flagged_build_process_lines`均空，但**原ss不是空连接表**：基线在配置前已有SSH、UDP及80/443连接；原件未带`users:((`进程信息，驱动`parse_ss`跳过无归属行。故只能说采样未识别出构建进程连接，不能由空数组证明没有构建外联，也不能断言所有未归属连接均与构建无关；归属UNKNOWN、采样间短连接UNKNOWN、未读子目录潜在外联点UNKNOWN保持。实现MD“没有出现外联行为”及Log“外联0”的绝对表述，当前主张以本节收窄；不覆盖原始快照，不虚构已知外联违规，也不重试取证。

#### 3. 计账、结论与主张上限

进入配置前记BUILD-LLAMA=1，配置/构建各1次；第一批0，合计1/1、重试0。新批从较早的Mac目录/started时间起算（含前置、sha、解压和收尾），脚本终点墙钟1,743.223 s≤7,196 s；第一批3.766 s，合计**1,746.989 s≤7,200 s**。实际开始/终点UTC重算符合三位小数计账；脚本单调1,740.474 s是子区间，不替代整批。构建步骤UTC差1,724.360776 s与单调1,724.422 s略不同，原因未核，不混用或改写原数。修订29规定两批间已停的文档核清/等待及提交不拼接为构建时间，本轮亦非续跑。

**核清结论：已核固定S、原§2参数在本板完成配置/llama-server构建；已记录步骤、累计墙钟与采样占用满足修订28–29及BUILD-LLAMA(a)–(f)的对应判据。** 构建额度已用尽、不转用；外联只到§2的有限证据，绝对零外联未证实。没有新正向违界事实，不另签重试或补核访问。

主张只证可构建，**不证运行、安装/运行兼容、性能/时延、内存/显存或GGUF可运行**；未知不补成通过，不签B1完成/新verdict/DONE/M7关闭。下一批逐维度推荐、未核前提及可回复原文唯一见「阶段B预检答复落实」§5现行段；INSTALL-W与其他未签维度0、不含云。排除条目待用户本人删原样保留。Overall REVIEW_PASSED/Lifecycle ACTIVE、S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN及AC-7/8/9 NOT_RUN保持。

### 阶段B安装合同准备（2026-10-05，Acceptance / CLARIFY；执行待用户签数值）

登记轮次 `阶段B安装合同准备`；Dispatch-Id `P1-ENG-JET-001-阶段B安装合同准备-20261005T043739Z-59b5`。依据账本2026-10-05「P1-ENG-JET-001 — 用户答复阶段B构建核清后待决：INSTALL-W 先准备离线合同再安装，其余未签维度保持 0（supervisor 会话代录）」(a)–(d)，解释既有AC-10/11、AC-7修订2–3、固定W/base+server与IR-14/15安装纪律；本轮不新增AC/修订、不改变目标/协议/验收线。只读本机保留证据与W轮子静态ZIP目录/METADATA，不解压落盘、不执行包代码、不联网、不ssh/触板、不安装、不跑测试，不代写用户原话/签额，consumed=none。

**执行效力：未生效。** 安装意向不含数值，INSTALL-W/TIME-BOARD/DISK-PEAK-BOARD安装子范围现为0。用户须按「阶段B预检答复落实」§5现行段逐维度签数值并入账，Acceptance核对入账与本合同一致后方交Implementation；不得仅凭本节或账本(a)派安装。以下命令是未来执行合同，不是本轮已执行记录。

#### 1. 输入闭集与逐文件离线顺序

- **唯一输入W31**：已传板独占目录 `~/eng-jet/stageb-transfer-20261004T225001Z/` 中31件固定wheel，压缩总字节516,980,330 B。从 `docs/evidence/P1-ENG-JET-001-stageb-transfer.json` 的 `objects` 选择 `cls=W/status=OK`，与 `docs/evidence/P1-ENG-JET-001-stageb-download.json` 的 `objects(kind=W/outcome.verdict=OK)`、metadata.json `META-DEP` 的选定文件交叉绑定。project/version/basename/expected_bytes/expected_sha256与文件集合逐字一致、无重复、恰31件才生成安装计划；sha及实际路径运行时解析，不手抄。原传板目录从transfer JSON `board_dir`解析并核对上述落点；不得按最新目录猜选。板上安装前**31件全量重核**普通非链接文件、字节与sha256；任一不符/缺失即停整批，不能先装其余件。输入只读引用，不复制、移动、改名、覆盖或删除；同目录G2/S1不使用。
- 不联网取包、不使用索引、不解析/补齐依赖，不跑 `pip download`、resolver、`pip install --dry-run`/`--report`，不从目录glob一把装、不重取旧件、不换pin/平台。已核METADATA静态闭集沿「阶段B核验核清」§1；本节不重新求依赖图，不激活server-tools/export/tools/native-build或其他extra，不装PyPI tensorrt/torch/transformers。
- **顺序闭集**（下列名称各恰一次；version/filename仍从上述JSON解析，各行从左至右逐文件安装）：

| 顺序段 | project顺序 | 理由 |
|---|---|---|
| 1（17件） | annotated-doc、annotated-types、av、certifi、click、cuda-pathfinder、filelock、fsspec、h11、hf-xet、idna、numpy、packaging、python-multipart、pyyaml、tqdm、typing-extensions | 目标Python3.12/Linux/aarch64、既定extra下无有效Requires-Dist边的叶节点；numpy固定2.2.6先进入独立W环境 |
| 2（6件） | anyio、cuda-bindings、httpcore、pydantic-core、typing-inspection、uvicorn | 依赖已在段1；不安装其可选extra |
| 3（4件） | cuda-core、httpx、pydantic、starlette | 所需numpy/anyio/httpcore/pydantic-core等已在段1–2 |
| 4（3件） | cuda-python、fastapi、huggingface-hub | cuda-core/bindings、HTTP及schema依赖已在前段 |
| 5（1件） | tensorrt-edgellm | W本体最后；base+server声明依赖已先装；不用extra表达式让pip求依赖 |

顺序依据已核目标marker/extra依赖图与本机固定wheel METADATA静态对照（无新resolver或网络）。这不保证运行隐式依赖已齐，安装中不import探明缺项。

#### 2. 独立环境与固定命令形式

- W环境固定 `~/eng-jet/edgellm-venv`，须事先不存在且父目录普通非链接；本批只新建一次，不复用/重建旧W环境、不碰 `~/eng-jet/sysvenv` 或旧wheels/构建目录。底座以§8.2为准：`/usr/bin/python3.12`、Python3.12.3、aarch64/glibc2.39、已装python3.12-venv与系统pip24.0。未来创建命令：`/usr/bin/python3.12 -I -B -m venv --system-site-packages --symlinks <W-venv>`。只用已装venv模块及系统随附ensurepip离线种子，不 `--upgrade-deps`、不升级pip、不补装setuptools/apt；种子缺失即停。
- `--system-site-packages`复用已核 `/usr/lib/python3.12/dist-packages/tensorrt` / python3-libnvinfer 10.16.2.10绑定；系统TRT/系统numpy1.26.4只读，W本地numpy2.2.6优先。系统site可见不等于与sysvenv合并：不激活sysvenv、不加其site-packages/PYTHONPATH、不运行快层。以 `pyvenv.cfg`、本地dist-info与来源路径静态核隔离；TRT import/加载/二进制兼容不在本批，不称已证。
- 新板批次目录 `~/eng-jet/stageb-install-<UTC时间戳>/`（`mkdir -m 700`，事先不存在、非链接），含 `raw/`、`tmp/`、`home/`、`cache/`、安装计划/逐次收据/监测账。venv使用上述固定独立位置，**新增占用同时计批次目录与venv，两者不重叠**。Mac原始目录为 `outputs/eng-jet/P1-ENG-JET-001/stageb-install-<UTC时间戳>/`，记录完整原输出；实际目录写机器证据，不写手维护SHA/HEAD。
- 逐个轮子的命令固定为以下形式（占位由计划/截止时刻解析，不本轮执行）：

```sh
LC_ALL=C timeout -k 2 <剩余秒> env \
  HOME=<批次>/home TMPDIR=<批次>/tmp XDG_CACHE_HOME=<批次>/cache \
  PIP_CONFIG_FILE=/dev/null PIP_CACHE_DIR=<批次>/cache/pip \
  <W-venv>/bin/python -I -B -m pip --disable-pip-version-check \
  --require-virtualenv install --no-index --no-deps --no-cache-dir \
  --no-compile --ignore-installed <板上固定轮子绝对路径>
```

`--no-deps`不遍历依赖；`--ignore-installed`保证该固定文件装入全新W venv的本地site，而不是因系统同名包跳过；它不卸载/重装系统包或sysvenv。不得加 `--user`、`--target`、`--prefix`、`--upgrade`、`--force-reinstall`、find-links或URL。禁编译pyc、禁运行生成的console entrypoint、禁构建sdist/执行setup.py。普通用户，无sudo/apt、系统/SSH/路由/沙箱设置改动。上述HOME/TMP/cache约束同样用于venv离线种子和装后pip；Python `-I -B`避免用户site/PYTHONPATH与字节码写入。pip/ensurepip及其打包库是具名安装基础设施运行，不是模型运行授权。

#### 3. 推荐预算与已核推导（接受推荐，全部未签）

**本机静态尺寸核对（本轮只读）：** 从download JSON逐件定位31原件，sha/字节与期望一致后用标准库 `zipfile.ZipFile.infolist()`读取中央目录的file_size/compress_size；只读取METADATA/WHEEL文本，不解压实体、不加载.so。目录中未见绝对路径/`..`/符号链接成员，W31内 `.pth` 文件0；不认证包代码安全或运行兼容。可重复方法：运行时解析相同31件，对每件 `sum(info.file_size)`/成员计数，结果绑定原wheel期望sha，不抄hash。

| 类型 / 工件 | 压缩B | ZIP声明解压B | 件数 / ZIP成员数 | 解压/文件字节比 |
|---|---:|---:|---:|---:|
| pure（py3-none-any） | 2,977,502 | 11,301,333 | 23 / 883 | 3.796 |
| native（aarch64/abi3/cp312等平台轮子） | 514,002,828 | 1,445,214,892 | 8 / 2,236 | 2.812 |
| W31合计C / U | 516,980,330 | 1,456,516,225 | 31 / 3,119 | 2.817 |
| 其中tensorrt-edgellm | 447,070,745 | 1,225,712,989 | 1 / 495 | 2.742 |

native八件为av、cuda-bindings、cuda-core、hf-xet、numpy、pydantic-core、pyyaml、tensorrt-edgellm。压缩比并非统一2倍：单件av约2.902、numpy3.456、cuda-bindings4.429；BP-2旧x86资格轮子的约1.92倍及size_budget压缩/解压上限只作历史参考，**不拿来替代本次aarch64固定原件**。ZIP声明长度只界定文件内容，不等于板分配占用/实际峰值。

| 维度 | 推荐上限 | 推导、控制与未核部分 |
|---|---|---|
| INSTALL-W | 1批；31文件各至多1次；重试0 | 第一次venv创建命令发出前预约并记批次1/1；进入前置失败记0/1，但已耗墙钟/日志照计且不自动重开。安装批含venv种子与31次pip，不把31条命令说成31批。失败已发文件计1次，未发NOT_RUN；无换环境/换pin/接着补装许可 |
| TIME-BOARD（本安装整批） | 3,600 s（1 h） | 规划分配：前置/31sha180 s、venv120 s、31文件×90 s=2,790 s、静态核对180 s、监测/终止/证据收尾330 s，共3,600。分配是保守工程余量，不是板实测逐包时长、不作为逐步独立额度；共享绝对截止强制停止。已有板37.8MB源码sha的整段前置0.742 s、传板226.666 s、构建1,746.989 s仅证底座/链路可操作，不推出W安装吞吐。实际安装成功所需时间UNKNOWN，超时允许失败后回用户 |
| DISK-PEAK-BOARD（本安装新增） | 5,000,000,000 B（5 GB十进制） | 保守计划2U+C+250,000,000（venv/离线种子）+500,000,000（分配取整/目录/脚本/RECORD等）+100,000,000（原输出/监测/失败账）=4,280,012,780 B；距5GB留719,987,220 B。2U预留已装全量加全量解压暂存，不假设仅最大单件暂存；C再留完整压缩副本/缓存上界，实际不复制输入且禁pip缓存。失败现场不另加一份，计入同一2U+C与余量、不删后重来。板分配单元在未来前置核≤65,536 B：2×3,119×65,536=408,813,568 B的每成员取整过量上界落在500MB项内，目录/元数据另用剩余及719MB余量。venv种子/日志均设子上限，超限停，不把估计当实测 |

磁盘出处：§8.2同一盘Available=165,731,360,768 B；「阶段B构建核清」前置163,185,582,080 B、最低采样余量162,773,512,192 B，均远高于本计划5GB+1GB保护。旧传板2,481,704,960 B与构建采样峰值411,414,528 B已在既有占用，不扣回/重计本次，不借其余额。**本推荐是已核输入、已核系统底座下可停止的预算上限，不是未经实测保证的物理峰值或成功时长。** 实际venv种子尺寸、filesystem分配单元、本次实时余量在已签安装前置内核；不符就停止，不授权探测性安装/重试。目录项/日志间隔增长、实际瞬时峰值、所需完成时长、系统TRT可加载与新CUDA算子兼容仍UNKNOWN，如实记录。

#### 4. 未来前置、监测与记账（全计入本安装批）

1. **先离线放行**：Implementation在Mac mini核用户逐维度安装签发已入账、本合同版本、31件来源链、共享槽位无其他板作业；沿「阶段B传板授权落实」§5修订27的现行权限允许规则加合同约束，只读核 `.claude/settings.local.json` 的 `Bash(python3 ~/TetheredDroneTracking/outputs/eng-jet/P1-ENG-JET-001/*)`，不继承仅传板批有效的excludedCommands单条。不改设置/启停沙箱；权限拒绝即停，无试连/换通道。单一顶层发令为本批目录内安装驱动；驱动仅落实本合同，不部署项目代码到板。SSH目标/端口从relay.json `link.ssh`解析，沿既有有线/known_hosts、BatchMode/StrictHostKeyChecking/ConnectionAttempts=1/ConnectTimeout=15，不取公网资料/包或加新Host。
2. **计时与前置**：以Mac批次目录创建与started中较早者为整批起点，记UTC/单调时刻与started+3,600 s绝对截止；含本机准备、登录、板sha、venv、全部pip、监测与机器证据收尾。一次具名只读前置块查板用户/home/arch/glibc、`/usr/bin/python3.12 -I -S -B`标准库版本、dpkg的venv/pip/python3-libnvinfer版本/ii及系统TRT目录、eng-jet/输入路径非链接与W31重核、W-venv/新批次目录absent；不以import读取版本。核系统site启动钩子（.pth/sitecustomize）静态文本；存在会启动模型/外联或无法静态核清的执行钩子即前置失败，不用import探明。核实际安装两落点同§8.2文件系统，`df -B1`可用≥6,000,000,000 B（5GB预算+1GB保护）、`stat -f`分配单元≤65,536 B；不符、缺命令/种子、版本变化、权限/输出UNKNOWN均停并交Acceptance，不补装/修配置。前置不创建venv，失败不用完次数也不自动重试。
3. **超时包裹**：板前置/创建/每次pip/静态核对/采样均 `LC_ALL=C timeout -k 2 <剩余秒>`；剩余从统一截止减当前墙钟再预留2 s强杀与收尾运行时计算，≤0不发令，不给每文件重置3,600 s。Mac等待同样受截止；板端安装进程与监测使用受控进程组，超时/监测STOP终止整组及后代，记录kill/rc；不能只杀SSH客户端留下板上pip继续。每次发令前核尚有本步/终止与收尾余额，不足即停；超时/截止已到只允许终止在途和保存失败收据，不继续安装/核对。
4. **新增占用保护**：基线记录两新路径不存在、板df以及旧输入/旧环境只读快照；创建后同时采 `du -sb`逻辑/表观量、`du -s -B1`分配量（venv symlink不跟随，不把系统Python/TRT计入新复制），两根分别取较大值再相加。种子阶段venv新增≤250,000,000 B，否则即停。每次安装前/后及中间每60 s采df、双du、UTC/单调/已耗墙钟；最早失败立即停剩余文件。当前占用加下一文件的保守2U_i+C_i及该文件双份取整、全部未用日志/目录预留若将超5GB，不发该文件。采样任一新增>5GB或df<1,000,000,000 B即停止整组；剩余空间不通过删除旧文件腾出。
5. **日志与峰值边界**：stdout/stderr受控保存（每次调用两流合计≤16MiB，板/Mac各自原账写明；板本批原输出/监测/收据合计≤100,000,000 B，任何即将超过则停止并保留已收到字节/截断标记）；临时/缓存只在本批路径，不写用户全局cache，禁pyc。日志也计du并在收尾最后一笔日志之后复采终值，记录其采样时刻；不能把du -sb称分配量，采样最大只称观测峰值，60 s间瞬时峰值仍UNKNOWN。发现控制流有未受控写路径即停。成功/失败均保留venv、tmp/cache、原输出/账，不清理、不删原件、不安装第二次；保留期后续增长不冒称已测。

#### 5. 单列装后静态核对与明确不做

推荐纳入**同一安装合同**的装后项：31命令全部成功且时间/占用余额足够时，`<W-venv>/bin/python -I -B -m pip --disable-pip-version-check list --local --format=json` **1次**，`... -m pip --disable-pip-version-check check` **1次**，沿§2的HOME/TMP/config/cache环境与§4的timeout。list读本地distribution元数据，对31个Name/Version与计划逐项核对，再标准库只读本地dist-info/pyvenv.cfg/source路径：numpy2.2.6在W、TRT来源系统、sysvenv不在路径；venv自带pip种子单列、不算W31新增distribution。pip check只做已装元数据Requires-Dist一致性核对，不解析取包，不import31包；它未覆盖extra/动态库/模型行为，server闭集依原静态声明核清。系统site可见的其他包若产生冲突，保留完整输出、记静态核对失败并停，不删系统包、不加依赖、不以“旧冲突”自动豁免。

上述属于**安装工具的运行与元数据静态核对**，计入INSTALL-W批次及时间/磁盘，不计一次模型启动/推理/冒烟/项目测试；本轮没有执行。任何非零rc、31项不符/缺项/来源不符即停止，现场回Acceptance。全成功也仅记安装命令和静态核对完成，不据此签兼容性/模型可运行/AC-7/8/9满足。

**不做闭集**：不import numpy/torch/tensorrt/tensorrt_edgellm或其他W包作验证；不加载GGUF/检查点/引擎，不执行llama-server/构建产物/生成的server entrypoint，不推理/查询/预热/冒烟/测试，不建引擎，不部署代码/上旧补丁，不加工数据/校准/量化，不下载/云端操作，不sudo/apt/系统或SSH改动，不动sysvenv。BP-2首建/可选server-tools隐式运行依赖未知留给未来独立签发，不在安装里探明；BASE-LOAD/BASE-SMOKE/BASE-S4A、TEST-B1/B2、REVIEW真实消耗、DEPLOY-CODE/TX-CODE-DATA-LOGS、DATA等其余未签维度全部0，已答选择不重问。

#### 6. 停止、失败与needs_user

具名停止原因：`PRECHECK_FAILED`（含输入不符/环境变化/余量或控制前提未齐）、`INSTALL_FAILED`（venv/任何pip非零）、`STATIC_CHECK_FAILED`、`TIME_LIMIT`、`DISK_LIMIT`、`DF_RESERVE`、`LOG_LIMIT`、`OUT_OF_SCOPE`（含需联网/补包/改环境/模型运行）。任一即停**全部剩余步骤**、终止在途进程组、保留现场与失败收据/已耗维度、不重试/重建/换pin/接着装，立即回交Acceptance核清，由用户决定。该处置随§5签发原文一并交用户确认；未签之前不执行。

本轮needs_user仅INSTALL-W四维数值签发（推荐与可回复原文唯一见「阶段B预检答复落实」§5）；本节已用本机保留原件静态尺寸与§8.2/构建核清事实形成可停止上限，**无需另报额外板访问/运行探测**。实际完成时间/瞬时峰值/运行兼容仍UNKNOWN，不假充闭合。未来若前置失败后需要补核板事实，按账本(c)另报具名操作/次数/墙钟/新增占用（没有的维度0），不得借已用预检、传板或BUILD-LLAMA继续探测；本节不预签这种补核。

#### 7. 未来证据字段与主张上限

Implementation生成 `docs/evidence/P1-ENG-JET-001-stageb-install.json` 与同名 `.md`（本轮不预写安装结果）。JSON至少含：schema/work_id/round/dispatch_id；用户**未来数值签发**标题/逐维度caps及准备授权(a)–(d)的区分；contract/来源JSON与脚本绑定（sha运行时派生）；31件project/version/file/期望B/sha/ZIP解压B/成员数/顺序；板重核原输出/rc、前置每项读数/UNKNOWN与静态启动钩子核对；target/允许规则/槽位；Mac/板批次路径及W-venv/pyvenv.cfg；安装前后git凭据（HEAD/porcelain）与旧sysvenv/输入只读基线；逐次argv/UTC/剩余秒/start/end/rc/stdout/stderr/截断/进程组终止；started/deadline/单调与整批UTC墙钟；双根双du/df基线、采样时刻/观测峰值/终值/最低df、预留与子上限；venv次数、各W文件attempt/OK/失败/NOT_RUN、pip list/check各0或1与输出/元数据比对；成功/失败/停止原因、INSTALL-W已用0或1、重试0、墙钟/新增占用共账、UNKNOWN、retention/claim_ceiling/needs_user。原始计划、调用与监测账只追加，不改旧下载/transfer/build/A账本或复核文件。

MD只放JSON/原始目录指针、数字摘要、停止/未执行/未知、预算符合性及需要用户决定的具名项。完成/中断立即交Acceptance，不自行继续模型或其他维度。当前Overall `REVIEW_PASSED` / Lifecycle `ACTIVE`、S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN与AC-7/8/9 NOT_RUN保持；不消费新verdict、不签B1完成/DONE/M7关闭。当前文档准备consumed=none、Consuming=no；未来安装独占UTC批次不是正式run ID，也不耗Play/API，但墙钟/安装/磁盘仍须上述独立签发并计账。

open_items: none

### 阶段B安装授权落实（2026-10-05，Acceptance / CLARIFY）

登记轮次 `阶段B安装授权落实`；Dispatch-Id `P1-ENG-JET-001-阶段B安装授权落实-20261005T050857Z-afaf`。依据 `docs/authorizations.md`「2026-10-05 P1-ENG-JET-001 — 用户签发 INSTALL-W：W31 独立 venv 离线逐文件安装 1 批、重试 0，墙钟 ≤3,600 s，板新增占用 ≤5,000,000,000 B（supervisor 会话代录）」用户原话及(a)–(g)，核对「阶段B安装合同准备」§1–7与「阶段B预检答复落实」§5安装合同准备后的签发原文。本轮仅零消耗文档CLARIFY，不联网取证、不ssh/触板、不安装、不跑测试，不代签额度、不代写账本；consumed=none。

#### 1. 用户原话与合同逐维度核对

本机文本逐字比较确认：账本用户原话与§5「用户可直接回复的签发原文」完全相同。逐项核对以用户原话为授权来源，账本(a)–(g)均与之相符：

| 维度 | 用户已签与合同核对 | 结论 |
|---|---|---|
| 对象、环境与安装次数 | (a)仅板上已核W31、独立W venv、离线逐文件安装1批、31文件各至多1次；合同§1固定来源/顺序、§2固定 `~/eng-jet/edgellm-venv` 与命令、§3批次预约一致 | 一致 |
| 重试 | (b)重试0；合同§3/§6不重试、重建、换pin或接着补装，前置失败不自动重开 | 一致 |
| 整批墙钟 | (c)≤3,600 s；合同§3–4统一起点/绝对截止，包含前置、venv、全部pip、静态核对、监测/终止/证据收尾，不逐文件重置 | 一致 |
| 板新增占用 | (d)≤5,000,000,000 B，含venv、解压、pip缓存/暂存、日志与失败保留件；合同§2–4双根共账、预留/子上限/余量监测及失败现场计入同一预算一致 | 一致 |
| 前置与装后静态核对 | (e)按合同§1–7，含前置只读核对及pip list/pip check各1次；合同§4前置、§5全部安装成功且余额足够才做两项静态核对，失败/超时不继续，不import包或运行模型 | 一致 |
| 停止处置 | (e)越界或失败即停、保留现场、不重试，回Acceptance由用户决定；合同§6八个具名原因均停全部剩余步骤、终止在途进程组、保留收据与已耗维度，未签补核不执行 | 一致 |
| 其余维度与禁止项 | (f)其余未签0，不运行模型/构建产物、不部署、不加载/查询/冒烟/测试、不含云、不改系统/SSH设置；合同§1–2/§5–7的闭集与主张上限一致，不借下载/传板/BUILD-LLAMA旧余额 | 一致 |
| 执行效力条件 | (g)用户按§5逐维度签发已入账，本轮Acceptance核对一致后才交Implementation；满足合同「执行效力」句要求 | 已满足 |

#### 2. 执行效力、归因与交接

**结论：INSTALL-W安装子范围已签、合同生效、待实现执行。**「阶段B安装合同准备」中的“未生效/全部未签/未来数值签发”保留为准备时快照，其执行效力条件现已由上述用户具名数值授权与本轮一致性核对满足；执行正文仍逐字沿该节§1–7，不改任何数值、命令、禁止项、前置、停止处置或证据字段。§5现行INSTALL-W状态已追加更新，旧签发推荐及原文保留。

归因：本轮只落实用户已签INSTALL-W及既有AC-10/11、AC-7修订2–3的合同执行效力，新增AC/修订=0；不签新额度、不扩设备/目标/协议/验收、不作C轮或独立复核。安装实际时长、瞬时峰值与运行兼容仍UNKNOWN；预算推导是可停止的上限，不保证安装完成或兼容。

交Implementation由supervisor派发，先按合同离线核放行/来源/槽位，再执行信封内前置与安装；完成或中断立即回Acceptance核清，后续步骤不自动放行。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE`及原负结果/未闭义务保持，不签B1完成、DONE或M7关闭。本轮授权一致性核对 `needs_user: none`；既有设置删除建议及其他未签维度只见「阶段B预检答复落实」§5，保留而不重问已签值。

open_items: none

### 阶段B安装核清（2026-10-05，Acceptance；零消耗原件核清）

登记轮次 `阶段B安装核清`；Dispatch-Id `P1-ENG-JET-001-阶段B安装核清-20261005T053128Z-3b80`。依据「阶段B安装合同准备」§1–7、「阶段B安装授权落实」及账本2026-10-05「用户签发 INSTALL-W：W31 独立 venv 离线逐文件安装 1 批、重试 0，墙钟 ≤3,600 s，板新增占用 ≤5,000,000,000 B」(a)–(g)。本轮只读本机保留JSON/原件与文档，不执行安装驱动、不联网取证、不ssh/触板、不import包、不跑测试；仅按派发收工推送文档。consumed=none，新增AC/修订=0；不是C轮、独立复核或新运行验收，不代写用户账本、不签额。

#### 1. 原件、前置、逐文件安装与静态元数据核清

入口为 `docs/evidence/P1-ENG-JET-001-stageb-install.md` §1–7及同名JSON。原件目录由JSON `output_dir_repo_relative`解析，驱动只读。现算 `install.py` sha与JSON `script.sha256`一致，`state.json`与证据JSON字节相同；本轮编辑前授权账本/执行时提案、transfer/download/metadata来源JSON现算sha均匹配记录（提案随后追加本轮文档，不回改执行时绑定）。`invocations.jsonl`有连续74个seq、各一对start/end；222个本机raw stdout/stderr/rc文件的字节、sha、rc逐一与end收据相符，无重复/缺件、截断或本机超时。以下逐项核清不是复跑板操作。

| 对照项 | 原件核清与边界 |
|---|---|
| 放行与槽位 | 执行记录只有本项非暂停交接、Consuming=no，无其他板连接进程；目录Bash允许规则与只读settings记录匹配，relay取目标/既有SSH参数。传板排除条目不沿用，未改设置。进程扫描只证扫描时刻，不是整批网络审计。 |
| 输入/顺序 | transfer的W/OK、download的W/OK、META-DEP选定pin与安装files四集合逐字一致且恰31项；顺序与合同17+6+4+3+1一致。现算31件本机原wheel字节/sha及ZIP目录长度符合：C=516,980,330 B、U=1,456,516,225 B、3,119成员。原precheck W31块62行逐件regular file/字节/sha符合，全部先核后装；不是由pip成功反推文件身份。 |
| 前置原输出 | 用户/home/aarch64/glibc2.39/Python3.12.3、venv/ensurepip可查找、venv/pip/libnvinfer具名版本及ii、系统TRT目录/命令、普通非链接路径、新落点absent符合；df同盘Available=162,773,491,712 B≥6e9、分配单元4096 B≤65536。`seed_wheels`的ls rc=2仅因另一候选`ensurepip/_bundled`目录不存在，`/usr/share/python-wheels/pip-24.0-py3-none-any.whl`实际列出，故“种子存在”成立；`prior_installs` rc=2为无旧安装目录。不能把前置各诊断rc概称全0，也不把缺失可选种子目录当本合同必需缺包。 |
| 启动钩子 | 原precheck完整文本含两条.pth（setuptools distutils与matplotlib命名空间）、Ubuntu apport sitecustomize链接及两份被引用模块文本；与驱动静态闭集匹配，没有需放行的未知执行行。JSON将.pth长行缩为400字符，核清采用raw完整569 B文本，不依截短摘要；不认证第三方代码整体安全或外联绝对为0。 |
| 预约/venv | mkdir发令前已预约INSTALL-W 1/1；mkdir中的计划表sha与按files重构值/JSON一致。venv创建1次rc=0；原post-venv-static只见pip及pip-24.0.dist-info，系统离线种子，无新setuptools；占用16,072,704 B≤250MB。cfg为home=/usr/bin、3.12.3、system-site=true，解释器symlink系统Python；独立于sysvenv，但不是隔离整个系统site。 |
| 31文件收据 | 31个pip步各恰一次、内外层timeout与统一剩余秒记录一致；原argv含合同HOME/TMP/cache及全部固定pip参数、指定单文件，未用索引/依赖解析/升级或替换pin。原step rc均0，Successfully installed名称/版本逐项符合、stderr均空；stdout/stderr字节大小证明捕获的tail是完整两流，无靠尾部遗漏错误的主张。 |
| pip list / 路径读取 | pip list 1次rc=0，原JSON数组恰32项：31计划名称/版本全对+pip24.0，无其他本地distribution。原post-static支持8/8记录：numpy2.2.6本地、无本地TRT、系统TRT目录/dist-info可见、无本地.pth、cfg/.pth中未找到sysvenv引用。grep rc=1和缺本地TRT/.pth的ls rc=2是预期缺项；没有实际读取sys.path或import TRT，不证运行解析/可加载。 |
| pip check / 停止 | 1次rc=1，原两流130 B/0 B完整，仅两条冲突（§3）；之后仅旧快照与最终占用收尾，无追加安装、修补、重试或运行。按合同§5–6保留`STOPPED / STATIC_CHECK_FAILED`，停止处置成立，不能改记静态核对全通过。 |

#### 2. 占用、墙钟、旧快照与UNKNOWN

- **占用**：35笔监测原行逐一匹配JSON、rc均0，含baseline/种子/31个装后/一次60s periodic/final；发令前用上次样本及下一文件保守增量保护，现算最大投影3,257,261,523 B≤5e9。每根取du表观/分配较大值再相加的现算观测峰值及终值均1,482,055,680 B（venv 1,481,605,120 + 批次450,560），df最低161,291,104,256 B≥1e9；种子/日志观测子上限在限内。板raw最大13,977 B；Mac raw实体合计53,051 B、最大单调用两流27,343 B≤16MiB，JSON `mac_raw_capture_B=53,495`是驱动每调用加8 B收据预留的计数，不是实体文件字节。final采样不追加monitor.log，且在最后板快照后，无后续板写入命令。采样之间瞬时峰值、保留期后续增长及SSH/PAM等批次双根之外附带写入不由双du证明；原账不清零、不称物理峰值已核。
- **计时读数与限度**：started原件与目录birthtime较早值为统一起点；按JSON UTC重算`wallclock.batch_elapsed_at_script_end_s=67.523`，剩余秒/内外timeout未逐步重置。核读驱动 `finalize()`可见`script_end_utc`实际在git_post和最后state/evidence JSON写入**之前**采样，故“完整脚本退出墙钟67.523 s”措辞不成立。git_post原UTC折算约67.585 s，本机保留state文件mtime约67.588 s；这些已捕获收尾点均远低于3,600 s，未发现时间/占用触限记录。精确脚本退出及完整最终收尾墙钟未单列，保持UNKNOWN，不补测、不把67.523改造为完整实测；原JSON/MD保留。文档/commit/push后续不冒称计入该读数。
- **旧快照解释成立，但只到所列属性**：pre/post原输出与JSON一致，sysvenv目录/cfg/site目录stat及cfg sha、各构建根目录stat相同。old_transfer文本唯一差异是`..`行链接数13→15及mtime；传板目录`.`及全部34文件列表相同，父eng-jet仅新增W venv与本批目录（自身total/stat相应变化），符合新建两目录，不能把false当传板文件被改的证据；也不修改原false。装前31轮子内容sha已核，装后快照仅ls属性，不是34文件逐件内容sha重核；sysvenv/构建同样未递归比内容，**所有旧文件内容完全未变的强主张UNKNOWN**。
- **主张上限**：固定W31离线逐文件安装命令成功，本地名称/版本及具名静态路径事实符合；pip check依赖元数据不一致。未证import、隐式/extra运行依赖完整、系统TRT可加载或二进制兼容、CUDA算子、模型可运行、token/解析、性能/时延或AC-7/8/9满足。原git_pre/post HEAD一致、porcelain为空只用于当时代码状态，不手抄标识。INSTALL-W 1/1/重试0已用尽，不借剩余时间/磁盘修补；原STOP、补丁未上板、SR5/5耗尽、两条OPEN债保持，Overall REVIEW_PASSED/ACTIVE仅属A候选，不签B1完成、DONE/M7关闭。

#### 3. pip check性质裁定与归因

原输出逐字为：

```text
pynacl 1.5.0 requires cffi, which is not installed.
scipy 1.11.4 has requirement numpy<1.28.0,>=1.21.6, but you have numpy 2.2.6.
```

1. **不属W31安装文件失败，但属当前W可见依赖图失败**：pynacl/scipy/cffi不在W31或pip list本地闭集中；cfg明确system-site=true，pip check仍见两项，可归于系统site可见集合（绝对dist-info来源/二者dpkg归属未单独捕获，不独立认证“均为apt包”）。本次无W31具名冲突输出不等于W运行依赖已齐，pip check也不证明server extra或动态库行为。31命令成功和整批STATIC_CHECK_FAILED同时成立。
2. **pynacl→cffi**：可见pynacl的声明依赖无可满足的cffi distribution元数据；属于继承可见性带入的未满足依赖。未做装前pip check，不将它追认为已实测的“装前旧冲突”；模块能否导入、该路径是否实际需要nacl/cffi仍UNKNOWN。本批不新增pynacl，不因此自动豁免。
3. **scipy→numpy**：W本地numpy2.2.6确实超出系统scipy1.11.4声明的[1.21.6,1.28.0)范围；合同已选择W本地numpy优先，故这是**系统scipy与新W numpy组合的冲突**，不能称与W安装无关的两条旧系统问题。若后续在W导入scipy，按该路径配置会接触系统scipy与本地numpy的不兼容声明组合，存在导入/ABI/数值行为失败的实质风险；本轮没有运行这种import，实际失败形态UNKNOWN。W本体固定wheel METADATA要求numpy>=2.2.6,<3（server钉2.2.6），不能随手降numpy消警。本机只读该wheel全部.py未见scipy/nacl/cffi文本引用，只是静态检索，不排除传递包、动态导入、可选路径或二进制依赖。
4. **归因与处置**：现有收据支持实现按已签固定命令执行并在失败处停止；不据此记为W31安装实现错误。风险来源是为复用系统TRT而接受的`--system-site-packages`设计同时暴露其他系统包，且W numpy形成跨环境约束冲突；这是后续环境合同需要承接的问题。本轮不是复核finding，不新造SCOPE_GAP/改原债务或归因计数；合同§5不允许自动豁免，本轮也不豁免或修补。INSTALL-W已用尽，不可补cffi、删系统包、换scipy/numpy、重建venv或重跑pip check。用户具名结果记账和后续路径的推荐/可回复原文**仅在「阶段B预检答复落实」§5现行段**；依engineering§9，未知板事实不得先签依赖它的执行维度。

open_items: none

### 阶段BTRT预检授权落实（2026-10-05，Acceptance / CLARIFY）

登记轮次 `阶段BTRT预检授权落实`；Dispatch-Id `P1-ENG-JET-001-阶段BTRT预检授权落实-20261005T142736Z-5eff`。依据 `docs/authorizations.md`「2026-10-05 P1-ENG-JET-001 — 用户选 B-W-ISO-PLAN I 并签发 B-W-TRT-PRECHECK：一批、一次 SSH、重试 0，墙钟 ≤300 s，板新增 0 B、Mac 新增 ≤10,000,000 B（supervisor 会话代录）」(a)–(d)，仅核对授权指代并落实既有合同；本轮只读文档、追加文档与交接，未联网取证、ssh、触板、执行预检或运行任何载荷/测试，consumed=none。收工文档自检与按派发要求git提交/推送不属预检执行。本节不代写账本、不代签额度，不是C/R轮，不新增或修改AC。

#### 1. 短答指代与逐维度核对

**核对结论：一致，指代足以无歧义落实。** 用户原话为「选1，签预检」，不是两段推荐原文的逐字复述。账本上文语境明确列出「1. 方案原则：推荐 I」与「2. 签一次 TensorRT 只读预检：推荐签」，各附「阶段B预检答复落实」§5当时现行段的可回复原文；其中方案选择只有第1条推荐I，具名预检只有第2条B-W-TRT-PRECHECK。故“选1”对应第1条方案I，“签预检”对应第2条按所附原文签发，不存在另一项预检、不同推荐数值或安装签发可与这句短答竞争对应。账本(a)(b)忠实转写这两项引用，(c)(d)保留合同分步签发与接受核对前置；不把简短答复扩大为其他阶段B授权。

| 核对维度 | §5两条可回复原文、账本(a)–(d)与隔离修补合同§4的对应结论 |
|---|---|
| 方案原则 | B-W-ISO-PLAN=I；原W现场/STATIC_CHECK_FAILED保留、关闭系统site的新W只拟暴露具名系统TRT，numpy固定2.2.6；链接闭集待核。只选择方案原则，不签安装/链接/运行。 |
| 设备、次数与重试 | Mac mini→既有Jetson，一批、一次SSH、重试0；各具名读数块至多一次、readelf每对象至多一次。发SSH前预约1/1，连接/前置失败不补跑，未发也保留已耗墙钟/本机日志；旧board预检/INSTALL-W不转用。 |
| 墙钟与新增占用 | 全批≤300 s，同一截止，起止及终止/原件收尾口径沿§4；代理板新增文件占用0 B、Mac新增≤10,000,000 B。板0 B限定代理可控文件占用，atime/SSH/PAM附带写入保持UNKNOWN；不宣称物理零写。 |
| 两流与读取硬界 | stdout+stderr全批≤2,097,152 B；树/dpkg/额外具名库清单≤256互异路径、深度≤8；文本累计≤1,048,576 B、单件≤262,144 B；ELF≤64对象、每份输出≤16,384 B。§5按§4签发、账本(b)按§5及§4签发，故这些闭集与硬界完整被引用，不因账本简写而省略。 |
| 读取闭集与禁止项 | 只取§4编号1–5的身份/底座/余量/路径、具名dpkg/TRT树与文本、静态ELF、具名stdlib启动钩子；不扫整系统site/sysvenv，不追查闭集外依赖或递归跟随新根，不执行Python/pip/import/ldd或动态加载，不读大型.so正文/hash。既有SSH/known_hosts及目录规则沿§4，不改系统/SSH/沙箱、不换通道或扩大读取。 |
| 停止与回交 | 超限/失败/缺材料即停，保留已获原件/失败/UNKNOWN、无重试/补核/修补/追加操作，回Acceptance；§4的PRECHECK_FAILED/INPUT_CHANGED/READ_LIMIT/TIME_LIMIT/DISK_LIMIT/LOG_LIMIT/OUT_OF_SCOPE任一停止全部剩余读取、终止在途并保存收据，缺输出不推“无依赖”。 |
| 其余维度 | 下载/新元数据联网/资产传板/安装/链接创建/import第三方/模型/建引擎/测试/云/部署/系统或SSH或沙箱改动/Play/API/正式ID全部0。B-W-ISO-INSTALL未签；其他未签维度保持0。 |

#### 2. 执行效力、交接与主张上限

**接受核对前置已满足：「阶段B隔离修补合同准备」§4 B-W-TRT-PRECHECK自本次落实获得执行效力。** 合同正文、全部数值/闭集/禁止项/停止处置原文不改；该节标题与“未签”文字保留为准备时快照，其授权状态仅由本节和「阶段B预检答复落实」§5追加现行状态替代。这项效力仅来自上述用户账本(b)，不是接受角色签额。B-W-ISO-PLAN=I依账本(a)落实为已选方案原则；§3离线安装仍是条件草案，预检结果核清、最小链接闭集冻结且用户另签安装/链接/静态核对数值前不得执行。

下一派发由supervisor交Implementation，仅执行原§4一批预检并按该节字段保存新的 `docs/evidence/P1-ENG-JET-001-stageb-trt-isolation-precheck.md/.json`，完成或停止立即回Acceptance核清，不接续创建venv/链接/安装/pip check/TRT import。执行前仍须满足单写者、共享槽位、目录/权限及输入JSON前置；权限拒绝或输入变化按原合同停止，不绕过、不自动重开。

交接Consuming=no：本次不创建/消耗scenario/session/run ID、Play或API预算，原始输出目录不属正式ID；有界板访问额度仍需按上述用户信封独立计账。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE`保持，仅属阶段A候选；原STATIC_CHECK_FAILED/严格退出墙钟与瞬时峰值UNKNOWN、S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN及AC-7/8/9 NOT_RUN保持，不消费verdict、不签B1完成/DONE或兼容/性能结论。本轮授权核对needs_user=none；其他既存待决仍只见§5唯一入口。

open_items: none

### 阶段BTRT预检核清（2026-10-05，Acceptance；零消耗原件核清）

登记轮次 `阶段BTRT预检核清`；Dispatch-Id `P1-ENG-JET-001-阶段BTRT预检核清-20261005T191007Z-41bc`。依据「阶段B隔离修补合同准备」§3–5、「阶段BTRT预检授权落实」§1–2、账本2026-10-05「用户选 B-W-ISO-PLAN I 并签发 B-W-TRT-PRECHECK：一批、一次 SSH、重试 0，墙钟 ≤300 s，板新增 0 B、Mac 新增 ≤10,000,000 B（supervisor 会话代录）」(a)–(d)及「阶段B安装核清」。只读本机原件/驱动文本与机器JSON，未执行驱动/包/干跑/测试、联网取证、ssh、触板、安装或import第三方；consumed=none。收工文档自检与按派发提交/推送不属板取证。本轮非C/R轮、新增AC/修订0、不代签、不代写用户账本、不消费verdict。

#### 1. 原件、逐维度执行与记账

证据入口 `docs/evidence/P1-ENG-JET-001-stageb-trt-isolation-precheck.md` §1–5及同名JSON；本机目录由JSON `output_dir_repo_relative`解析。原state与仓库JSON字节相同，驱动/只读块/两流现算sha、原rc文件与JSON收据一致；编辑本轮文档前，账本/提案/install/relay绑定sha全部相符。17件文本逐件按raw_offset/received_B重取、现算sha与板端/JSON一致；四份ELF原文与JSON raw_output逐字一致，机器字段/MD具名读数相符，无截断/解析错误。未改机器原件或把缺失事实补成读数。

| 合同§4维度 | 核清结论与限制 |
|---|---|
| 次数/SSH/重试 | invocations只有reserve、seq1 start、seq1 end；先预约后发，SSH1/1、整批1/1、重试/scp0，rc0，原两流均到end。13个分段各一次、四个ELF对象各一次，覆盖合同编号1–5。dpkg_w内对python3-libnvinfer另读一次版本作比较，并非第二个读数块/SSH，但JSON摘要不代表每条底层命令恰一次。 |
| 墙钟/超时 | 起点取目录birthtime与started较早者（本件为started），统一截止300s；SSH实测0.934s，远端210s、本机等待220s，均从同一余额减收尾预留、不重置。JSON写完后尾点4.321s；见§2，不能称完整监督退出已核。 |
| 两流/文本/ELF硬界 | raw stdout194,632B+stderr366B=194,998B≤2,097,152B；文本17件167,085B，单件最大37,956B，各sha rc0；ELF4份共10,904B、最大2,835B，各readelf rc0。均在1MiB/256KiB/64对象/16KiB界内。readelf -W只控制列宽，另readelf --version一行是具名工具身份读取，未新增ELF对象。 |
| 树/路径闭集 | dpkg+树45、库链后49互异路径，深度8处目录0；仅两个TRT根find -P、四包dpkg清单及已列库的同目录链、具名stdlib钩子。doc/.a只stat，LICENSE/zip-safe未读正文，无大.so正文/hash，无整system-site/sysvenv扫描，未知libnvonnxparser未追查。49不包含身份/旧cfg/钩子路径，不误称整个SSH只碰49路径。 |
| 前置/底座/余量 | user/HOME/aarch64/glibc、六包版本/ii、eng-jet普通目录、两旧cfg普通文件、拟新venv不存在均与合同吻合；df Available161,290,993,664B、分配单元4096B。新落点stat rc1/相应stderr是预期不存在，分段paths rc0不代表内部stat全部0。槽位/权限/输入记录具备；ps只证采样时无其他板连接，不是整批网络审计。 |
| 板新增/禁止项 | 板块只经stdin供sh，未建目录/脚本/tmp/日志、链接或修改文件；代理可控新增0B成立。没有sudo、Python/pip/import/ldd/模型/引擎/测试/下载/资产传板/部署/设置改动。atime/SSH/PAM附带写入UNKNOWN，不能据命令只读宣称全盘物理0写。 |
| Mac占用/输出归属 | 原采样峰值299,008B，JSON双份写后499,712B；本轮只读现算批次全部普通文件+仓库JSON+原MD合计表观476,734B、分配516,096B（文件和目录分配口径分开），可核保留件远低于10MB。不是执行期间瞬时峰值；JSON写到仓库证据路径而非全部在新批次目录，违反§4单目录落盘形式，但已显式双根计数，不能漏计双份。批外干跑生成物不在此数，见§2。 |
| 停止/回交 | 主批没有触限/STOP，原COMPLETE仅表示块执行到end。没有在同次派发接续venv/安装/链接/pip check/import。驱动对缺文本/部分内部rc有记录后继续而非统一失败即停的形式，当前原件必需材料无此缺失；其失败保护未在真实条件下验证，合成干跑不能替代。 |

**记账结论**：B-W-TRT-PRECHECK一批及SSH均已用尽1/1、重试0；未用时间/磁盘/读取额度不转用。已获静态读数与计次成立；原COMPLETE保留，不等于“严格全合同符合”、安装闭集冻结或运行通过。§2具名偏差及UNKNOWN保留，不伪造新增额度或清零；用户偏差处置入口仅「阶段B预检答复落实」§5 B-W-TRT-RESULT。

#### 2. 执行形式偏差与计量上限

- **SSH参数**：BatchMode/StrictHostKeyChecking/ConnectionAttempts=1/ConnectTimeout=15与合同一致；目标确从relay解析，既有known_hosts使用未改变。relay的link.ssh并无端口字段；驱动PORT固定22，并非合同所称“目标/端口从relay运行时解析”。显式-p22与旧安装使用的默认22一致、Compression=no只关闭传输压缩，未改SSH设置/设备/登录次数，但这属于执行形式偏差，不能写“两项均由relay解析”或用先例代替合同。下次端口依据须具名核清，不能尝试新端口；无必要为此再SSH取证。
- **main包装**：main(){…}; main </dev/null只令块内命令不吞脚本stdin，不执行额外载荷、不增加板写或访问次数；date/段标记/内存awk去重计入实际两流，set -f抑制glob。此形式等价满足stdin只读块目的，未扩大读根。readelf -W/版本一行的差异及重复版本读取已在§1逐项列出，不概称逐字原命令。
- **本机假目录干跑**：MD§2自报用dash/GNU替身执行正常及四个停止分支；这是本机合成验证，不能称板运行/模型测试，也不计成第二次SSH；但合同只准窄目录驱动/静态读取、测试维度0，不能用“不计入批次”豁免它。原JSON/本批目录没有该干跑的路径、argv、起止/字节/增长/保留收据，本轮也不执行或全盘寻找。记**实现执行方法偏差**：批外验证的授权覆盖、计时、占用及禁止项符合性未获证明；不认证合成分支通过或整次实施全量在信封内。这里只作事实/合同归因，不新签独立finding、SCOPE_GAP或改变既有返工计数；是否保留有限读数按§5具名交用户，不追认未记账活动为0。
- **结束/占用口径**：只读finalize()可见4.321s尾点在state/仓库JSON写完后，但在mac_occupancy、wallclock_end.json原子写入、最后stdout与脚本返回之前；没有监督父进程退出收据。wallclock_end文件mtime约4.321176s仍远小于300s，只证该写盘点，不把mtime当退出；严格完整退出/收尾墙钟UNKNOWN。原499,712B同样在wallclock_end写入前、未含原MD与序列化临时双份峰值；现算保留件未见越限，不反推瞬时/批外总占用在限。三次采样是驱动自算表观/st_blocks，不是合同文字的两次du调用；用于同等保守取大读数可成立，不能说已执行双du。远端timeout限制板进程，本机killpg只处理本次SSH组；未触发时不认证已实测远端异常清理。**已核数值在限、完整口径UNKNOWN、形式偏差**三者分别记录，原MD/JSON不覆盖。

#### 3. 方案I冻结裁定（最小暴露/链接闭集：未冻结）

| 具名项 | 本机静态核清与本轮裁定 |
|---|---|
| libnvonnxparser.so.10 | tensorrt.so真实NEEDED含此项，前合同禁止追查；位置/类型/终点/包/版本/ELF依赖均UNKNOWN，是必要原生库，不因Python METADATA无声明边而豁免。须补具名静态映射，不允许安装或拷库兜底。 |
| 已读nvinfer/plugin库 | SONAME/机器与同目录链已核，两者依赖系统C/C++底座；运行文件所属包未读。系统底座NEEDED不是要求复制入venv，但需具名系统搜索映射，不从“板上装过TRT”推完整解析。 |
| RUNPATH | 原文逐字`$ORIGIN:$ORIGIN/../_libs)`；末尾右括号属于目录字面，不擅改成_libs或认定打印错误。具名原目录存在性未读，symlink加载时ORIGIN实际取何路径未实测；不改RPATH、LD_LIBRARY_PATH、系统缓存或批量链接库。补静态目录/缓存映射仅能冻结静态来源，不能证明加载行为。 |
| tensorrt_libs | __init__.py的try导入只捕ImportError/ModuleNotFoundError，Linux不走后面的Windows DLL/CDLL定位分支；未导入成功并不阻止随后from .tensorrt import *。因此不自动将tensorrt_libs列必装项，也不能认定它在隔离环境必定不可见/永远不需。候选只暴露tensorrt与其dist-info、不链接tensorrt_libs；需核具名位置及系统NEEDED，运行分支/隐式依赖仍UNKNOWN，不运行其初始化文本。 |
| numpy/插件 | METADATA仅numpy extra条件边，不代表numpy不可达；nptype()函数内导入numpy，plugin多个模块在模块级导入numpy，plugin/__init__.py还动态枚举子模块。必须保留本地numpy2.2.6，不降版、不借系统numpy/scipy。根__init__.py未静态导入plugin，只支持顶层静态路径判断；链接整个tensorrt会使plugin可见，不能声称移除或已验证plugin。_lib.py函数内triton/triton.language是可选调用路径，未来出现即具名停回接受/用户，当前不补triton、不授权plugin调用或TRT import。 |
| sitecustomize/apport | 原链接→/etc/python3.12/sitecustomize.py，try导入apport_python_hook，成功才install()。原site.py的venv()在cfg=false时PREFIXES=[sys.prefix]且ENABLE_USER_SITE=False，main仍execsitecustomize()；Debian dist-packages候选是venv前缀下，并不自动引入系统前缀。故关闭system-site不等于关闭stdlib sitecustomize；**条件静态推断**：新环境无apport链接、无整系统根路径时应走ImportError/pass，不自动复制钩子。未来实际sys.path/导入分支/钩子效应仍UNKNOWN，不能记已实测关闭。创建venv的系统解释器阶段本来仍可能执行系统钩子，沿已读文本约束、不改钩子。 |

**不能冻结/不请签B-W-ISO-INSTALL。** 两个顶层TRT对象可作候选，尚非完整最小闭集：必要parser及系统解析映射未核。新venv不存在，实际import/ORIGIN/ABI/钩子分支未知不会靠静态预检变成运行通过；未来安装合同只能承担“静态来源与依赖元数据”的主张，运行探针须独立另签。现阶段不把运行未知偷换成已知来源，也不要求通过先装新venv来取事实。

「阶段B隔离修补合同准备」§3仍是条件草案，推荐新venv1/W31各1/链接具名对象各1/pip list及check各≤1、重试0，统一3600s/板新增5GB/Mac新增100MB的原推导仅在闭集齐全后重核；本轮不批准其数值适用、不增加链接数、不变numpy2.2.6。若补充静态事实仍不齐或需闭集外新包/新根，回用户具名选继续准备/停止；原P/U方案不自动启用。当前可交签的仅下节新预检；决策推荐/可回复原文唯一在§5入口。

#### 4. B-W-TRT-SUPPLEMENT：有界补充静态预检申请（未签，当前0）

**目的/输入/前置**：仅补§3的必要库来源与路径，复用原JSON/两流而非重跑五块。Mac mini、同一用户Jetson/有线/known_hosts；一次授权入账并由Acceptance核对本节后才交Implementation，单写者/共享槽位空闲、目录窄规则及旧输入绑定具备。原块/文本sha从证据运行时派生，旧W/sysvenv/资产/构建只读。relay目标运行时取；**端口明确为既有默认22，不声称relay有端口字段**，不试新目标/端口，Compression=no写入新命令形式。不得继承传板排除条目或改系统/SSH/沙箱。运行前具名本机静态读数计划落同一新批次目录；不做批外合成执行/假树/测试。

**读取闭集与顺序（只读sh，签后才执行；不搜全盘/不递归拓扑）：**

1. 身份仅id -un/HOME/uname -m/getconf GNU_LIBC_VERSION，与原值比较；stat eng-jet及拟新venv不存在、df -B1/stat -f余量/分配单元，各一次。只对原两个TRT根内的METADATA、tensorrt/__init__.py及site.py、sitecustomize目标、apport五件具名文本stat后sha256sum，各≤1次；路径由原JSON逐件取且必须对应上述名字。大小/链接终点先与原记录一致才hash（累计40,040B、单件最大23,903B），不cat或回传正文、不find原树；任一改变停止INPUT_CHANGED，不重新解释原文本。
2. `/sbin/ldconfig -p`**只读缓存**一次（缺工具即停，不安装、无参数更新缓存禁止）；仅输出以下9个soname的精确匹配：libnvonnxparser.so.10、libnvinfer.so.10、libnvinfer_plugin.so.10、libstdc++.so.6、libgcc_s.so.1、libc.so.6、libm.so.6、librt.so.1、ld-linux-aarch64.so.1。完整缓存仅流经内存过滤，不留无关条目；匹配0、多个架构/多候选歧义或路径不在下述闭集即停，记录全部已获候选、不猜选。额外允许stat/readlink核`/lib`→`/usr/lib`具名别名；没有该关系则不能把两根视同。
3. 路径只限上述精确命中位于`/usr/lib/aarch64-linux-gnu/`或`/lib/aarch64-linux-gnu/`的文件，以及已核nvinfer/plugin两条真实链；另允许`/usr/lib/aarch64-linux-gnu/libnvonnxparser.so.10`具名stat/readlink用于与缓存交叉核（不存在不搜替代）。每条链同目录≤8跳，总互异路径≤64，含具名父路径/钩子/候选位置共账；相对终点规范化且仍同目录才跟，跨目录/未知/循环即OUT_OF_SCOPE/INCOMPLETE。stat/readlink逐路径各≤1，已读链接结果复用；不hash/cat大ELF。`dpkg-query -S -- <精确文件路径>`逐件≤1，归属仅取精确输出，不用通配查询；对唯一归属包`dpkg-query -W`Version/Status各≤1（至多16包），不运行-L全包树；无法归属/非ii/版本冲突停止，不补包。
4. 对精确映射的ELF普通终点`readelf -h -d -W`各≤1，总≤16对象，每份≤16,384B；记录机器/SONAME/全部NEEDED/RPATH/RUNPATH。parser或其他新增ELF出现9个soname与原已核NEEDED集合外的名字即记UNKNOWN/INCOMPLETE、停止剩余，不在同次缓存再追新名。工具缺失或rc非0即停；禁止ldd/动态加载、执行二进制、CUDA调用。
5. 只stat/readlink具名字面目录`/usr/lib/python3.12/dist-packages/_libs)`（不替换右括号）、`/usr/lib/python3.12/dist-packages/tensorrt`（复用前置）、以及两个系统根`/usr/lib/python3.12/dist-packages/`和`/usr/lib/python3/dist-packages/`下的`tensorrt_libs`、`tensorrt_libs.py`、`apport_python_hook.py`候选；父目录只核类型不枚举。可选项不存在记ABSENT并继续，必要库/工具缺失则停止；存在可选对象只记位置/类型/终点，不读其包树/执行或自动加入未来暴露集，闭集外链接不跟。这里不能验证新环境实际分支，新落点下不创建目录取读数。

**命令形式**：新批次窄目录顶层本机驱动，唯一`ssh -p 22 -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectionAttempts=1 -o ConnectTimeout=15 -o Compression=no <relay解析目标> 'LC_ALL=C timeout -k 2 <统一剩余秒> sh -s'`；stdin送具名只读块，可用main </dev/null包装。块只含上述命令及printf/date/内存awk精确过滤/去重与界检查；没有scp/sudo/板mkdir/tmp/脚本/日志/文件修改、Python/pip/import或包运行。SSH前预约1/1，即使认证失败也用尽；后续不得再登录补核存活。

| 维度 | 接受推荐上限与推导（全部未签=0） |
|---|---|
| 操作/次数 | 新B-W-TRT-SUPPLEMENT一批/一次SSH、重试0；各具名块≤1，缓存≤1，ELF每对象≤1；不是旧预检重试，不借余额。没有安装/链接/list/check/import次数。 |
| 整批墙钟 | ≤300s：本机计划/前置30+连接/身份30+缓存/路径/包归属90+ELF/具名位置90+终止/监督原件收尾60。目录创建与started较早者起，UTC/单调双记，同一绝对截止；预留强杀与最后写盘，不保证完成、不用原0.934s预测上界。 |
| 板新增占用 | 代理可控文件0B；仅stdin/内存/读缓存，无板工件。附带atime/SSH/PAM系统写入继续UNKNOWN，不扩成物理0写保证。 |
| Mac新增占用 | ≤10,000,000B；单一新批次目录内驱动/计划/账/机器证据原件≤4MB，两流≤1MiB，序列化双份/分配/失败保留余量≤约4.95MB。文档发布JSON是后续副本，发生于同一次计时内则双根共账；原件全部先落批次、禁止批外scratchpad。元数据/目录分配也计，序列化发起前保守投影。 |
| 两流/读硬界 | stdout+stderr累计≤1,048,576B（16份ELF至多262,144B，64路径stat/readlink/dpkg及缓存精确输出预留≤262,144B，其余身份/标记/错误余量≤524,288B）；64互异路径/链≤8跳/16ELF/16包为硬界，每个读取前检查剩余。前置五件sha实际读取文本累计≤40,040B、单件≤23,903B，逐件必须等于原size；新正文取回0B，不能借hash取新文本或大ELF。 |
| 其他 | 下载/联网元数据/资产传板/venv/安装/链接/系统缓存更新/Python或包运行/import/ldd/模型/引擎/测试/部署/云/Play/API/正式ID=0；静态映射不授运行探针。 |

**监测/停止/证据**：本机按表观/分配取大（双du或可核lstat等价读数，注明实际方法）监测单根及发生时的证据副本，逐块及每≤1s在途检查增长/两流/统一剩余；写每份计划/输出前做保守增量保护，不在最后写盘后才判断限额。板所有命令同一timeout，Mac监督统一截止，保留远端timeout与本地终止结果，不仅断SSH；异常清理未能证明则UNKNOWN不重连。TIME_LIMIT/DISK_LIMIT/LOG_LIMIT/READ_LIMIT/PRECHECK_FAILED/INPUT_CHANGED/OUT_OF_SCOPE/INCOMPLETE任一停止全部剩余（具名可选ABSENT除外）、终止在途、保留现场/已耗/原件，无重试/新依赖追查/修补，回Acceptance→用户。缺省停止处置随签发原文引用，不代签。

未来证据 `docs/evidence/P1-ENG-JET-001-stageb-trt-supplement.md/.json`：work/round/dispatch/新授权及caps、运行时git/来源绑定、原件目录、精确白名单、预约/一次argv与stdin sha、每步起止/余额/rc/两流/截断、缓存9名匹配/缺项/歧义、路径类型/字节/链/包Version/Status、ELF全文与字段、可选位置ABSENT/UNKNOWN、前置sha比较、双端占用/样本/生成投影、停止/NOT_RUN/终止/保留。结束尾点由独立监督在子进程退出且机器原件写完后记；监督自身最后写入无法精确纳入时另列UNKNOWN，不标“完整实测”。回接受仅冻结静态安装输入或具名退回；不随签预检自动执行安装，不声称原生加载/ABI/numpy兼容/钩子分支或模型/性能通过。

#### 5. 本轮停点与交接

交用户的具名项/推荐/可回复原文只在「阶段B预检答复落实」§5现行段；方案I、原预检授权、记账A/准备B、既答事实不重问。当前不派后续板操作，补充预检未签=0、安装/链接/静态核对/运行均0、不含云；原W现场及STATIC_CHECK_FAILED保持。Overall REVIEW_PASSED / Lifecycle ACTIVE仍仅属A候选，S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN、AC-7/8/9 NOT_RUN与原严格计时/瞬时峰值UNKNOWN不变。不签B1完成、独立复核/DONE/M7关闭或兼容性主张。

open_items: none

### 阶段B隔离修补合同准备（2026-10-05，Acceptance；执行草案未签）

依据 `docs/authorizations.md`「2026-10-05 P1-ENG-JET-001 — 用户答复阶段B安装核清：B-INSTALL-RESULT 选 A、B-INSTALL-NEXT 选 B（supervisor 会话代录）」(a)，本批记账口径逐字落实为：「本批记为W31安装与pip list核对完成、pip check未过（系统site的pynacl缺cffi、scipy 1.11.4与W本地numpy 2.2.6冲突）；保留STATIC_CHECK_FAILED、计时与峰值的UNKNOWN，不记兼容或模型通过。INSTALL-W已用尽、不转用，现场保留，不豁免、不修补。」该选择已落实，不再待用户答复；成功子事实不覆盖整批停止。

登记轮次 `阶段B隔离修补合同准备`；Dispatch-Id `P1-ENG-JET-001-阶段B隔离修补合同准备-20261005T055312Z-0981`。同账本(b)只授权本机原件零消耗方案/合同准备，(c)不签新额度。本轮只读固定wheel ZIP/METADATA/Python文本及原安装输出/JSON，未执行其中代码，未联网取证、ssh/触板、安装、import第三方包、运行模型或测试，consumed=none；收工文档检查与用户要求的git提交/推送不作取证或板端执行。新增AC/修订=0，不是C/R轮；下面是接受推荐，须用户具名选择/签发且Acceptance落实后才具执行效力，不修改固定numpy2.2.6或原安装合同/结果。

#### 1. 已核输入、用途与证据边界

入口为「阶段B安装核清」§1–3、`docs/evidence/P1-ENG-JET-001-stageb-install.md`及同名JSON（含 `input_binding/files/post_static_reads/pip_check/occupancy/wallclock`）；本机原件目录从 `output_dir_repo_relative` 解析。本轮只读确认state.json与证据JSON字节相同、raw中pip-check收据rc=1、两条冲突完整；31原wheel由download JSON定位，逐件现算字节/sha符合固定期望，ZIP C=516,980,330 B、U=1,456,516,225 B、3,119成员、.pth=0，与安装证据一致。旧原件/账本均未改删，实际目录名/sha不手抄。

| 用途/事实 | 本轮核对与可成立的结论 | 未覆盖/不能推出 |
|---|---|---|
| W METADATA声明闭集 | 沿「阶段B核验核清」§1/AC-10修订23及metadata-verify JSON；本轮重读31件METADATA，无scipy/pynacl/cffi声明边；httpx的brotlicffi属于非CPython的可选brotli extra，未激活。所选为W base+server，不启server-tools/export/tools/native-build | 5件Dynamic的历史裁定边界保留；METADATA静态声明闭集不等于隐式运行依赖闭集，系统TRT本来没有Requires-Dist边 |
| W31 Python文本 | 逐件ZIP内.py全文检索scipy/nacl/pynacl/cffi，并按行匹配import/from；命中导入仅numpy随机数的2个示例/2个测试中的cffi，W本体未见上述引用；其他scipy字样为numpy文档/构建信息等 | 文本检索不是完整调用图，不能排除动态导入、二进制依赖或可选分支。没有执行示例/测试，不能声称W所有路径永不使用这些包 |
| 既有S3/S4路径 | 3b为已建llama-server+官方G2，运行本身不经W Python；3c为W常驻server/本地检查点首建LLM+visual（BP-2、AC-7修订2–3），固定接口未要求scipy或pynacl；S4板查询沿服务，Mac评分沿原冻结评分器，不借W安装授Mac依赖 | W不为3b承担模型加载；3c/C2仍依赖未签云产物，S4 token/基准/代码停点等未齐；不因无scipy依赖就放行3c/S4，S5快层另用原sysvenv，不把两环境混合 |
| W对TRT的实际需求 | 保留wheel `tensorrt_edgellm/_native/dependencies.py` 文本中require_tensorrt()调用importlib导入tensorrt，并用ctypes.CDLL加载libnvinfer主版本soname，失败才查tensorrt_libs；server/runtime/engine_build.py引用该入口 | 仅目录可见不足；此调用在本轮未运行。系统绑定的内部导入、相对库定位、原生加载/ABI是否适配新链接仍UNKNOWN，不能加PyPI tensorrt来兜底 |
| 系统底座/原W | §8.2及install前置：Python3.12.3/aarch64/glibc2.39、python3-libnvinfer 10.16.2.10-1+cuda13.2/ii；原post-static列出系统tensorrt目录和tensorrt-10.16.2.10.dist-info，W本地numpy2.2.6、无本地TRT/.pth；system-site=true | 未保留系统TRT包树、METADATA/RECORD内容、内部链接/相对依赖；pynacl/scipy绝对distribution位置与dpkg归属未单独捕获，不能笼统认证两者为apt包 |

**用途判断**：已核声明与指定S3/S4路径没有需要scipy/pynacl的证据，故不推荐为了全局pip check补无关系统包。约束“不导入scipy/nacl、不运行numpy示例/测试、不开额外extra”可写入未来W使用合同；它只是减少可达范围，无法改变当前system-site依赖图或使pip check转绿，不足以解除原STATIC_CHECK_FAILED/允许W运行。若今后真实签发路径发现需要它们，停下具名报依赖，不自动补包。

#### 2. 零消耗方案比较与推荐

| 方案 | 来源/pin与需要的维度 | 利弊、证据边界及合同影响 |
|---|---|---|
| P1：保持system-site，只在W补cffi | 需先核现有pynacl METADATA/Requires-Dist；新增cffi及其有效传递依赖（如pycparser）只取官方PyPI项目的固定版本/文件元数据，正文沿files.pythonhosted.org固定wheel；必须cp312/aarch64/glibc兼容、精确sha/size。现无保留候选元数据，**pin/件数/字节UNKNOWN，下载/传板/安装/时间/占用均0**，不选未核版本、不用apt | 只可能闭合pynacl→cffi，scipy→numpy仍失败；保留其他系统包可见性。安装成功也不证cffi原生扩展可用；单独此方案不能形成完整修补合同，不推荐 |
| P2：保持system-site，补cffi并在W遮蔽系统scipy | scipy同样需官方PyPI固定元数据/平台wheel；候选METADATA须明确接受numpy2.2.6及Python3.12，禁止改numpy；cffi/pycparser等有效闭集同P1。pin均UNKNOWN；逐件精确下载B、Mac/板传输B、ZIP U/成员/安装次数、暂存/日志/墙钟峰值须另核，**当前全0** | 有望消除两条声明冲突，仍暴露其余系统site且增加不属于W的原生包。需静态METADATA核清后才申请下载，不能先下载探大小；安装后pip check与未来有界ABI/导入检查分开，不保证数值/运行兼容。不推荐当前选它；若用户选P，先回接受准备元数据/板事实核验，不直接签安装 |
| P3：保持system-site，但屏蔽系统scipy | 不删/改系统模块或dist-info，不改系统路径；单纯不导入或用import拦截不隐藏pip check的distribution。要按路径排除整个系统site并只暴露TRT实际上转为I；全目录.pth/运行时meta_path钩子不属原固定安装合同 | 不能用删元数据/忽略pip check伪造绿色；拦截器增加运行语义与执行钩子，还留下pynacl→cffi，不推荐。任何屏蔽实现/重测须独立合同，当前0 |
| I：另建无system-site的W，只暴露系统TRT（推荐） | 复用板上W31固定pin（W0.11.0、numpy2.2.6及其余29件按来源JSON）；TRT只用系统10.16.2.10，不下载/重装。优先新venv本地site中的**具名package与dist-info符号链接**；精确来源/内部依赖待§4预检。下载/资产传板推荐0；安装/链接/静态核对需新额度 | 隔离其他系统distribution及其.pth，原失败现场可保留；会失去原来自动暴露的系统包，系统TRT内部可能依赖其他具名模块/库。必须先核最小闭集，不能假定只一目录足够；改变原W固定环境/暴露方式须用户选择并由接受追加落实，不自行改AC或原合同 |
| I的.pth/路径白名单变体 | 可在新批次trt-bridge目录仅放具名TRT链接，venv内纯路径.pth指向bridge；或具名启动器设置窄搜索路径。不得将/usr/lib/python3.12/dist-packages或/usr/lib/python3/dist-packages整目录写.pth/PYTHONPATH | 整系统根路径会重新暴露冲突，直接指tensorrt包目录又不等于暴露其父目录下的顶层包；bridge多一个写根/启动扫描，启动器须未来代码停点，-I忽略PYTHONPATH。首选直接链接，避免可执行.pth；没有板实测不能认定哪种链接能满足TRT相对库定位 |
| U：原W保持system-site，只约束不导入scipy/pynacl | 无新下载/安装；使用约束本身也不授一次运行。固定W声明路径的“不需”仅为§1静态判断，隐式依赖未知 | 最少改动，但原图仍不一致，pip check失败保持。若用户决定带失败继续，须另签具名例外/有界实测合同；本次(a)明确不豁免，不推荐将U作为修补完成 |

**接受推荐I，并先签§4的具名只读预检。** 保留原W venv/原日志，不改pyvenv.cfg、不移走系统包；新环境未来固定拟落点 `~/eng-jet/edgellm-isolated-venv`（须不存在）与新批次目录共账。只推荐方案原则，尚未判“可执行/兼容”；若预检发现TRT需要闭集外Python依赖、跨目录链接或缺库，停止并回用户选替代，不在已签只读操作内补齐。新路径和无system-site方式仅为草案，用户选择、预检核清、接受落实及独立安装签发四者齐全前原AC-7/10/11合同不变。

#### 3. I的后续离线执行合同草案与条件预算（安装未可签，维度0）

**现行核清（2026-10-05）**：原B-W-TRT-PRECHECK已用尽1/1；「阶段BTRT预检核清」§3裁定必要libnvonnxparser及系统库映射未核，最小闭集**未冻结**。本节原条件草案/推导保留，不升级为可签安装包；具名补充申请见该§4，用户决策仅「阶段B预检答复落实」§5。已选I不重问，固定numpy2.2.6不变，安装/链接/静态核对0。

**目的/范围**：形成W31与具名系统TRT的隔离静态环境，保持原失败证据；不证明可导入、载荷选择、模型/引擎可运行，不扩展S3–S5额度。**接口/输入闭集**：W31严格按「阶段B安装合同准备」§1的三JSON交叉绑定和17+6+4+3+1顺序，31固定pin/文件各一次；TRT来源限定§4核清后生成的非递归猜测白名单（顶层package及dist-info、必要兄弟模块如有必须逐项裁定）。名称/来源路径/类型/链接终点/size/sha及版本写机器计划，使用前重核，不手抄SHA。所有旧W/sysvenv/传板/构建根只读，不克隆旧W、不从sysvenv拷包、G2/S1不使用。

**前置**：用户已选I且授权账本签发安装数值；§4每项核清/最小链接闭集冻结，无UNKNOWN必需依赖、无闭集外链接；离线种子/底座版本与旧证据一致，输入31件全量重核通过、新venv/新批目录不存在且父路径非链接；旧W/sysvenv/输入快照有来源。新venv只用系统Python/标准库/离线pip种子，静态检查本地启动钩子；stdlib路径sitecustomize可能仍执行，不能声称无系统钩子，须按§4原文核清。槽位、目录允许规则、known_hosts/既有目标沿原安装合同§4，不沿用传板excludedCommands；权限拒绝即停、不改沙箱或换通道。

**未来命令形式**（未执行；占位由冻结计划解析）：

```sh
/usr/bin/python3.12 -I -B -m venv --symlinks <新W-venv>
ln -s -- <白名单系统TRT顶层对象绝对路径> <新W-site>/<核定对象名>
LC_ALL=C timeout -k 2 <统一剩余秒> env \
  HOME=<新批次>/home TMPDIR=<新批次>/tmp XDG_CACHE_HOME=<新批次>/cache \
  PIP_CONFIG_FILE=/dev/null PIP_CACHE_DIR=<新批次>/cache/pip \
  <新W-venv>/bin/python -I -B -m pip --disable-pip-version-check \
  --require-virtualenv install --no-index --no-deps --no-cache-dir \
  --no-compile --ignore-installed <板上固定单wheel绝对路径>
```

创建、链接及所有读取也必须包统一timeout/HOME/TMP/cache约束；`ln`逐名，目标不得已存在、不用-f或目录glob、不创建整系统根链接。dist-info与package同时具名暴露用于静态依赖核对，但不把链接记新下载/新TRT安装；记录链接数/创建次数，pip list本地项与链接来源单列。31安装均成功且有余额才用同一环境跑pip list（`list --local --format=json`）/pip check（`check`）各1次，参数沿原安装合同§5；W31+pip种子逐项核，无计划外本地包；list --local是否包含链接TRT按原输出单列、不预设，核定TRT另读链接METADATA核身份/依赖。新cfg的system-site=false、numpy本地2.2.6、TRT链接真实来源、无scipy/pynacl/cffi distribution/模块链接、无sysvenv/整个系统site引用、无可执行.pth均做静态核对，不运行import。任一新pip check非零即新批STATIC_CHECK_FAILED，不过滤两条警告或改原批结果。

| 维度 | 条件推荐与推导（预检核清前不申请签发） |
|---|---|
| 新取回/资产传板 | 0件/0 B；W31已在板，TRT只引用已装系统对象。新包/新元数据网络/资产复制不在I内；控制命令经既有SSH发出，不把它计成资产传板，也不声称网络总字节0 |
| INSTALL-W-ISO / LINK-TRT / 静态核对 | 新venv创建1、31文件各1、TRT白名单顶层对象各链接1、整批1、重试0；pip list/check各≤1。旧INSTALL-W仍1/1用尽，不扣回；这是新增类别而非旧信封重试/余额 |
| 整批TIME-BOARD/TIME-MAC | 共用3,600 s绝对截止，不是各一小时可相加。前置/31sha180、venv120、31×90=2,790、链接/静态核对180、监测/终止/收尾330，共3,600；原67.523 s读数只作参考，完整退出时长UNKNOWN，超时可失败，不保证成功 |
| DISK-PEAK-BOARD新增 | 条件推荐5,000,000,000 B。复用原2U+C+250MB种子+500MB取整/目录/记录+100MB日志=4,280,012,780 B；TRT不复制，若预检白名单树≤256项、分配单元≤65,536 B，双份256项取整再预留33,554,432 B，总4,313,567,212 B，留686,432,788 B。原W约1.482GB及旧输入/构建已存在、不扣回，不算“零成本重建”。链接跟随不计复制占用，但链接自身/日志全计；所需闭集超过该界先回接受重算 |
| DISK-PEAK-MAC新增 | 条件推荐100,000,000 B；只驱动/计划/raw/机器证据（原安装raw约53KB仅参考），不复制W或下载；驱动/计划/账/JSON≤10MB、两流及监测累计≤80MB、收尾/元数据10MB，生成下一笔前保护。实体、失败保留件和所有计时内输出共账，不把git包/长期文档占用宣称纳入该值 |
| 其他维度 | 新TRT/torch/scipy/cffi安装、import/运行探针、模型/产物/entrypoint/加载/建引擎/查询/测试/部署/数据/云/系统设置/Play/API/正式ID=0；TRT可加载与隔离后的W载荷选择须未来另报具名有界实测，不从静态核对“各1次”推运行次数 |

**监测/停止/证据**：沿原安装合同§4–7的双根（新venv+新批次，symlink不跟随）双du/df、逐步前后+60s采样、种子≤250MB、板日志≤100MB、每次两流≤16MiB、未发下一件保守投影、TIME/DISK/DF保护及受控进程组终止；可用盘前置≥6GB、运行中df<1GB停止。Mac新增单独监测，剩余秒统一扣终止/收尾预留；最终墙钟应由Mac监督进程在子进程退出且最后机器证据写完后记尾点，监督输出/自身末次写入若不能纳入精确退出值则单列UNKNOWN，不复用原67.523作完整读数。采样峰值与瞬时UNKNOWN分列。原因PRECHECK_FAILED/INSTALL_FAILED/STATIC_CHECK_FAILED/TIME_LIMIT/DISK_LIMIT/DF_RESERVE/LOG_LIMIT/OUT_OF_SCOPE任一停止全部剩余步骤，终止在途、留现场/已耗、无重试/补包/换方案，回Acceptance→用户；须随安装信封确认。

未来新证据 `docs/evidence/P1-ENG-JET-001-stageb-w-isolation.md/.json`，不覆盖原install：绑定新用户签发/合同/预检材料/旧证据、运行时git凭据/原件sha、W31计划/板重核、TRT白名单与dist-info依赖/链接来源、cfg/启动钩子、每次argv/UTC/单调/剩余秒/rc/完整两流/截断、旧W/sysvenv/资产快照、新安装/链接/list/check计次、双端新增占用/df/采样/终值/墙钟结束口径、停止/终止/UNKNOWN/失败保留/主张上限与needs_user。只可记新静态环境事实；旧STATIC_CHECK_FAILED不release、不记AC-7/8/9满足或B1/DONE。**本节缺TRT事实故尚非可签安装包**，§4回来后由接受冻结对象及是否仍适用上述上限，再在唯一§5入口给用户安装签发原文；本轮不以数字存在即请求越过engineering§9。

#### 4. B-W-TRT-PRECHECK：现在可交用户签的有界只读申请（未签）

**缺事实与目的**：系统TRT内部布局、dist-info声明、静态导入、相对共享库/兄弟Python包、链接终点及stdlib启动钩子决定§3最小暴露输入；已有§8.2/install的ls与版本无法补出它们。预检只取下列静态材料，不尝试验证import/ABI，不重复S0、W安装或原pip check；它是新的一次具名预检，旧board预检1/1与INSTALL-W不转用。设备仍同一Jetson，发令机Mac mini。

**闭集与命令形式**（未来一条SSH内的只读sh块，未执行）：

1. `id -un`、`printf`打印实际HOME、`uname -m`、`getconf GNU_LIBC_VERSION`；`dpkg-query -W`只读python3.12-venv/python3-pip/python3-libnvinfer/python3-libnvinfer-dev/libnvinfer-dev/libnvinfer-plugin-dev的Version/Status；`df -B1`/`stat -f`只核eng-jet同盘余量/分配单元；`stat`/`readlink -f`核eng-jet、原W/sysvenv cfg、新拟落点不存在。不运行Python/pip/import。HOME只读不重赋值。
2. `dpkg-query -L python3-libnvinfer`/`python3-libnvinfer-dev`/`libnvinfer-dev`/`libnvinfer-plugin-dev`文件清单（均为§8.2已核包）；系统TRT已知根 `/usr/lib/python3.12/dist-packages/tensorrt`、`tensorrt-10.16.2.10.dist-info` 使用不跟随链接的 `find -P`/`stat` 取树/类型/字节/链接字面与真实终点；树、dpkg与额外具名库清单合计≤256互异路径，目录深度≤8，超出即INCOMPLETE/停止、不取其余。只允许这两个TRT根、dpkg列出的TRT对象与下条具名标准库钩子；不能扫描整系统site或sysvenv包树。
3. 对上述TRT根内METADATA/WHEEL/top_level.txt/RECORD、package内.py逐件只读 `cat`/`sha256sum`（单文件≤262,144 B、文本累计≤1,048,576 B）；静态记录Requires-Dist/Requires-Python、顶层名、绝对/相对导入与库路径定位表达式。不执行.py或动态求其依赖。内部symlink只读readlink，不递归跟随到新根；依赖闭集外模块/路径只记录UNKNOWN，不追查/补包。
4. TRT根内.so及dpkg列出的libnvinfer.so.10/实际版本、libnvinfer_plugin.so.10等具名TRT库：仅对清单已有普通文件/已核链接终点 `stat`/`readlink`、`readelf -h -d`静态读ELF机器/NEEDED/RPATH/RUNPATH（至多64对象，每份ELF输出≤16,384 B）。readelf先command-v，缺失记UNKNOWN，不安装/改用ldd或加载动态库；未知NEEDED只记录，不全盘搜库或扩大白名单。
5. 只读原已核 `/usr/lib/python3.12/sitecustomize.py`及其 `/etc/python3.12/sitecustomize.py` 目标、`/usr/lib/python3.12/site.py`、`/usr/lib/python3/dist-packages/apport_python_hook.py`（同文本大小/总量界），核无system-site时仍可执行的stdlib初始化及apport回退文本；不执行它们。已核其他系统site.pth不重新开放，不遍历查新包。未能静态核清的执行行为记UNKNOWN回接受。

顶层仍为现行窄目录规则下本机驱动，只生成Mac批次raw/收据；SSH目标/端口从relay JSON运行时解析，BatchMode/StrictHostKeyChecking/ConnectionAttempts=1/ConnectTimeout=15，沿既有有线/known_hosts，不用公网/新Host或传板专用排除条目。未来形式 `ssh <既有参数与目标> 'LC_ALL=C timeout -k 2 <统一剩余秒> sh -s'`，通过stdin给上述只读块，**无scp、板mkdir/写脚本/tmp/日志/改配置、无sudo**。静态读文件可能更新atime、SSH/PAM可能产生系统日志，这些系统附带写入未观测、保持UNKNOWN；“板新增0 B”限定代理不创建/修改文件的可控占用，不声称全盘物理写入绝对0。

| 可签维度 | 接受推荐数值/推导（当前未签=0） |
|---|---|
| 操作/次数 | B-W-TRT-PRECHECK一批/一次SSH，重试0；各具名读数块至多一次，readelf每对象至多一次；连接/前置失败后也不补跑。发SSH前预约1/1，未发也保留已耗墙钟/本机日志、不自动重开 |
| 整批墙钟 | ≤300 s：本机离线前提/计划30、连接与身份/余量30、TRT清单/文本120、ELF/启动钩子60、终止/原件收尾60，共300；可停止预算，不保证完成。Mac创建批次与started较早者起至监督收尾，UTC/单调双记，一个截止，不逐命令重置；截止前预留强杀与收尾，剩余不够不发下一步 |
| 板/本机新增占用 | 代理板新增文件0 B；Mac新增≤10,000,000 B（raw两流≤2MiB、计划/驱动/JSON/收据≤4MB、临时序列化双份/分配/失败保留余量约3.9MB），所有本机生成物同一新批次目录共账、不拷W31、全程增长保护，不在板缓存原件 |
| 原输出/读取界 | stdout+stderr全批≤2,097,152 B；以上树256/深度8、文本1MiB/单件256KiB、ELF64/每件16KiB各为硬界，下一项将超限即停止，原件标INCOMPLETE/截断，不把缺输出当“没有依赖”。只读清单不逐件读大型.so正文/hash |
| 其余 | 下载/新元数据联网/资产传板/安装/链接创建/import第三方/模型/建引擎/测试/云/部署/系统或SSH/沙箱设置改动/Play/API/正式ID均0 |

**前置/监测/停止**：账本逐维度签发入账且Acceptance核对本节、单写者与板槽位/目录规则/输入JSON具备，才发一次SSH；权限拒绝不绕过。Mac驱动监控统一剩余秒、双du取大本批目录占用、双流字节和清单/文本/ELF界；板timeout与Mac等待均受同一截止，终止在途进程组并保存收据，不能只断SSH留下读数进程。原因PRECHECK_FAILED/INPUT_CHANGED/READ_LIMIT/TIME_LIMIT/DISK_LIMIT/LOG_LIMIT/OUT_OF_SCOPE任一停止全部剩余读取、留已获原件和失败/UNKNOWN、无重试/补核/修补，回Acceptance；上述缺省处置随§5可回复原文一起签，未签不执行。

**证据字段/回来后动作**：新 `docs/evidence/P1-ENG-JET-001-stageb-trt-isolation-precheck.md/.json`；至少包含work_id/round/dispatch/授权标题caps、脚本/来源机器绑定、运行时git凭据、target/规则/槽位、一次attempt、每项命令/读文件白名单/类型/size/链接终点/静态sha、dpkg版本/清单、原文本与METADATA/导入/ELF字段、每步UTC/剩余/rc/完整两流/截断、启动钩子读数、df/分配单元、新落点状态、started/deadline/结束口径/单调、Mac新增观测峰值/终值/采样/日志计数、停止/NOT_RUN/UNKNOWN/retention/claims。Acceptance只据原件冻结§3白名单或具名退回用户；即使预检全齐，也不得在同次派发创建新venv/链接/安装/跑pip check或TRT import。签预检不签方案原则或安装，三者分别记账。

#### 5. 决策入口与本轮结论

本轮B-INSTALL-RESULT=A与B-INSTALL-NEXT=B已落实，needs_user的新具名项与推荐/可回复原文**只在「阶段B预检答复落实」§5现行段**：B-W-ISO-PLAN推荐I；B-W-TRT-PRECHECK推荐按§4签有界只读操作。B-W-ISO-INSTALL维度先保持0，预检核清前不申请签发；P方案未核pin/字节的下载/传板/补包也0。排除条目待用户本人删除的原建议原样保留；其余未签维度0、不含云，已答选择不重问。

本轮仅接受文档准备，不消费verdict、不修改AC、不签任何额度或独立复核/DONE/B1完成。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE`仅属A候选；AC-7/8/9 NOT_RUN、S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN以及旧严格退出墙钟/瞬时峰值UNKNOWN保持。交用户决定方案原则/预检；任何新板事实必须按具名另签操作取得，不能为使合同“完整”先碰板/取新包。

open_items: none

### 阶段B构建前置停止核清（2026-10-04，Acceptance / CLARIFY）

登记轮次 `阶段B构建前置停止核清`；Dispatch-Id `P1-ENG-JET-001-阶段B构建前置停止核清-20261005T032412Z-173e`。本轮仅本机只读证据核清与文档裁定，不跑测试、不执行驱动、不ssh/触板/构建、不取网络证据、不签额度、不代写用户原话；consumed=none。依据「阶段B构建授权落实」§1–7/AC-10修订28及账本2026-10-04「用户签发 BUILD-LLAMA：板上离线构建 llama.cpp 1 次、重试 0，墙钟 ≤2 h，板新增占用 ≤5 GB」(a)–(f)。

#### 1. 原件、前置与S核清

证据入口：`docs/evidence/P1-ENG-JET-001-stageb-build.md` §1–6与同名JSON。从JSON `output_dir_repo_relative` 解析原批目录；不手抄实际批次目录名、SHA或HEAD。现算 `build.py` sha与JSON `script.sha256`一致；`state.json`与证据JSON字节完全一致；`raw/001-precheck.stdout` 1036 B与JSON `steps.precheck.stdout`逐字一致，stdout/stderr现算sha与`invocations.jsonl` end收据一致，stderr 0 B、原rc=0。调用账恰为seq=1/label=precheck的start/end一对，无第二次调用。

| 前置 / 原stdout块 | 核清读数与结论 |
|---|---|
| id/home/arch/engjet | jetson、/home/jetson、aarch64、/home/jetson/eng-jet存在且非链接；逐块rc=0，符合目标/落点。 |
| df/cmake | 可用163,185,614,848 B≥5e9；/usr/bin/cmake、3.28.3≥3.18；逐块rc=0，符合。 |
| nvcc/gcc/gxx/make | 固定nvcc可执行，release13.2/V13.2.78；gcc/g++各13.3.0；GNU Make4.3；逐块rc=0，版本/可调用性符合，不证明g++/make位置。 |
| tools | 仅/usr/bin/gcc一行、rc=0；g++/make的/usr/bin位置UNKNOWN，tools_in_usr_bin不满足，不能改标前置通过。 |
| cuda_link/sbsa | /etc/alternatives/cuda、sbsa-linux存在；逐块rc=0，符合。 |
| s_stat/s_sha | S为非链接普通文件、37,831,966 B；sha原输出路径与JSON所绑板上S一致；逐块rc=0，字节与sha均符合。 |
| batch_absent/prior_builds | 新板目录absent、rc=0；prior_builds无匹配、rc=2，为信息读数，不是新增阻断。 |
| SSH/本机离线 | relay.json现算sha匹配，唯一目标与invocations参数数组一致，端口22、既有严格键/BatchMode等固定选项；执行前后HEAD相同且porcelain均空。按JSON git_pre的HEAD读取git中提案/账本版本，sha均与当时快照一致；授权(a)–(f)本轮逐条人工核清。槽位与设置记录只证明当时本机快照，不替代下一批前提。 |

S绑定：现算transfer/source-archive两份JSON sha与`input_binding`一致，transfer中archive.tar.gz唯一S项为OK、批次COMPLETE；该项期望字节/sha、source.archive、build.input_binding与板端s_stat/s_sha原读数交叉一致。本机保留归档重新计算字节/sha也符合；这是核对已有板端重核结果，本轮未重新上板求sha。身份链仍仅绑定保留自动归档返回实体，未内部验commit，不扩大来源主张。

JSON若干派生项`rc=null`源于`need()`用验收项名取原块名，实际判据另用`rc0(原块名)`；逐块原rc核清如表，null不当成0，也不改原JSON。整体ssh rc=0来自块尾`exit 0`，不表示全部前置通过。

#### 2. D-1归因、计账与主张上限

只读驱动`step_precheck`：tools块实际为`command -v gcc g++ make`，随后要求三行精确等于三个/usr/bin路径；原调用与原输出证实这次sh仅返回首名。该行为足以解释因少两行而停止；与实现自报dash行为相符，**D-1归因为实现方法缺陷成立**。原件没有`/bin/sh`链接或dash版本读数，本轮未运行dash行为实验，故不把“所有dash版本都只处理首名”或“板上确为dash”写成新核实事实。也不从该缺陷反推两条UNKNOWN路径实际符合，不能据此断言板端没有其他环境问题。

驱动`run()`在`step_precheck`抛Stop后直接收尾，未进入`step_mkdir_unpack/step_build`；构建计次只在`step_build`进入配置前写1，JSON只有precheck步骤，与调用账一致。因此构建0/1、重试0成立。开始/停止UTC差3.765754 s，按证据三位小数3.766 s计账；单调脚本耗时0.854 s与ssh0.788 s是子区间，不替代整批。第一批无板工作目录创建/解压/构建，**批次工件新增0 B**为控制流与调用账推得；occupancy采样全null、monitor_samples为空，不声称有du测量峰值0或整板无附带写入（SSH/PAM/登录服务附带写入未测）。无配置/编译/产物/监测证据，不能记构建成功。

主张仅限当时工具版本可调用、磁盘余量、S字节/sha重核符合及前置停止事实；不证明构建、运行兼容、GGUF可运行、性能、时延、内存或显存；JSON中“if COMPLETE”模板不适用本批。原失败读数及证据不覆盖。

#### 3. B-BUILD-RERUN裁定与执行合同差异

**裁定：落在已签BUILD-LLAMA信封与合同内，交实现，不需用户新增签发。** 原§3明确“一次构建”从进入cmake配置起算、前置与sha不计次数；原§4前置失败先保留回交，并限定“不重试前置以外的任何步骤”。本批已经回交，既未越界也未进入配置/编译，故不触发原§6“越界或构建失败…由用户决定”；账本(a)构建1/重试0尚未消耗。(e)授权接受落实执行合同，engineering§8允许信封内工程性修正及归因，但不扩大任何数值。下列是一次有界前置采集修正后的首次构建，不是第二次构建或构建失败重试；(b)(c)从严跨批合计，(d)(f)设备/范围及交接要求保持。

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 29 | CLARIFY（解释AC-10修订28及「阶段B构建授权落实」§1/3/4/7，来源为实现stageb-build.md §5 D-1与§6 B-BUILD-RERUN）：仅允许一次新独占批次，只修D-1的多名command-v采集，重做原§4前置及§1 S sha；全部满足后首次进入原§2配置/构建1次，构建重试0。两批执行墙钟合计≤7,200 s，新批保守≤7,196 s，板新增工件占用含两批失败保留件合计≤5e9 B。新批/证据命名与累计计账按本节；前置再失败即停回交，不自行开第三批；原§2参数、§5禁止项、§6越界/构建失败回用户及其他未签维度0不变。 | artifact: 原stageb-build.json/.md与账本BUILD-LLAMA(a)–(f)；本节§1–3；未来 `docs/evidence/P1-ENG-JET-001-stageb-build-rerun.json/.md` | K1K3K4 | 2026-10-04 |

唯一差异闭集：

1. **D-1**：新驱动tools采集拆为`command -v gcc && command -v g++ && command -v make`，三个单名调用、任一非0不掩盖；保留三行/usr/bin路径逐字判据，未知/不符即失败。不顺便改rc字段映射、其他判据、构建参数或执行栈；原驱动只读保留。
2. **新批与证据命名**：Mac与板继续原`stageb-build-<新UTC>/`独占规则，旧目录不复用；原JSON运行时解析旧目录并确认新旧不同。新驱动的批次/round/Dispatch及证据输出绑定新派发，写上述`stageb-build-rerun.json/.md`（已有即停、不覆盖），链接原stageb-build.json/.md及原件作为第一批账。第一批源码副本、脚本、state、调用账、JSON/MD均不动；新批继续只读复用传板S，不下载/传新源。
3. **墙钟合计**：运行时读取第一批`wallclock.batch_elapsed_at_script_end_s`（已核3.766），为保护舍入向上取整扣4 s，新批上限7,196 s；新批仍从目录创建起含离线核对/前置/sha/解压到命令结束或停止，新截止=新started+7,196 s，timeout/监测均按此余额，不能重置成7,200。新JSON分别记录首批读数、保守扣除、新批用时与合计；两批间已停止的文档核清/提交/等待不算构建执行时间，不把第一批计次/用时归零。
4. **占用合计**：首批工件0 B但原件不清理；新批按原监测取逻辑/分配两口径较大者保护5 GB上限，保留采样与瞬时峰值UNKNOWN限制；不借TX-ASSETS额度、不删除旧文件腾空间。其他监测、前提与停止规则原样执行，完成/停止立即回Acceptance核清。

归因：实现方法缺陷D-1导致首批前置采集不完整；本轮追加AC修订1、新AC=0，不是独立复核finding，不改既有返工度量。只核清并解释既有信封，未首签或扩大额度；不签B1代码停点完成/新verdict/DONE。Overall REVIEW_PASSED / Lifecycle ACTIVE、S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN及AC-7/8/9 NOT_RUN保持。B-BUILD-RERUN不再列为用户待决；B-LOCAL-EXCLUDE-TRANSFER保留用户本人删除条目，唯一现行用户入口仍「阶段B预检答复落实」§5。

open_items: none

### 阶段B构建授权落实（2026-10-04，CLARIFY）

登记轮次 `阶段B构建授权落实`；Dispatch-Id `P1-ENG-JET-001-阶段B构建授权落实-20261005T025948Z-75a3`；Acceptance，Mac mini。依据 `docs/authorizations.md`「2026-10-04 P1-ENG-JET-001 — 用户签发 BUILD-LLAMA：板上离线构建 llama.cpp 1 次、重试 0，墙钟 ≤2 h，板新增占用 ≤5 GB（supervisor 会话代录）」授权范围 (a)–(f)，追加板上离线构建执行合同；不代签额度、不覆盖原AC/原账。本轮consumed=none：未联网、未ssh/上板、未执行构建/解压/安装/加载/测试、未租云；仅文档落实。

#### 1. 追加 AC 修订与输入闭集

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 28 | CLARIFY（解释AC-10、修订17/25及AC-7修订2/3；来源为上述BUILD-LLAMA账本(a)–(f)）：Implementation仅在板上用已传板并核清的保留源码副本S离线构建llama.cpp固定b11381的llama-server目标1次，重试0；整批墙钟（含解压）≤7,200 s，板新增占用（解压、构建目录、暂存、失败保留件）≤5,000,000,000 B；构建参数逐字沿本节§2，不得新增/更改。前置（本节§4）任一不满足即停、不计构建次数；任一越界或构建失败即停、保留现场与日志、不重试，交回Acceptance核清后由用户决定。只构建：不联网取源/子模块、不加载模型、不推理/冒烟/测试、不安装31轮子、不部署、不改SSH/系统设置、不含云；其余维度0。 | artifact: 上述BUILD-LLAMA账本(a)–(f)、本节§1–7、AC-7修订2/3、§8.2、「阶段B传板核清」；未来 `docs/evidence/P1-ENG-JET-001-stageb-build.json/.md` | K1K3K4 | 2026-10-04 |

归因：用户具名BUILD-LLAMA授权及既定AC-7修订2/3构建参数、AC-10资产/信封义务的执行解释；新增AC=0、AC修订1，不是复核finding，不变目标/模型/协议/STOP线，不消费新verdict。INSTALL-W及其余未签维度仍0、不含云。

- **输入（唯一）**：板上独占目录 `~/eng-jet/stageb-transfer-20261004T225001Z/` 中的保留源码副本 S，具名文件 `archive.tar.gz`（37,831,966 B；身份=llama.cpp固定b11381完整commit的GitHub codeload自动归档，链与字节/sha已核，见「阶段B核验核清」§2与「阶段B传板核清」§1–3）。期望 sha256 一律从 `docs/evidence/P1-ENG-JET-001-stageb-transfer.json` objects 中该 basename 项及 `docs/evidence/P1-ENG-JET-001-stageb-source-archive.json` `archive` 运行时解析，两处逐字一致才采用，禁止手抄进命令或证据。构建前在板上对该文件重算 sha256 与期望逐字比对，不符即停（属前置，不计构建次数）；只复用该副本，不重取、不换源、不解压内部验commit，归档原件只读引用、不改不删。
- **W31/G2**：同目录其余33件本轮不使用、不移动、不改名；INSTALL-W仍0。

#### 2. 构建参数（沿既定合同逐项固定，不得新增未经合同的参数）

逐字沿 AC-7 修订 2/3 与「阶段B依赖闭集准备」BP-2 已核固定项：

```sh
cmake -S <src> -B <build> -G "Unix Makefiles" \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES=87 \
  -DGGML_CUDA_NO_VMM=ON \
  -DLLAMA_OPENSSL=OFF \
  -DLLAMA_BUILD_UI=OFF \
  -DLLAMA_USE_PREBUILT_UI=OFF \
  -DGGML_CUDA_CCCL_VERSION= \
  -DLLAMA_LLGUIDANCE=OFF \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc
cmake --build <build> --config Release -j 4 --target llama-server
```

- 生成器固定 `Unix Makefiles`：ninja 板上缺失且不需（§8.2 U1 tools 行），不安装 ninja。
- `LLAMA_CURL` 已弃用、不进命令（AC-7 修订 2）；`GGML_CUDA_CCCL_VERSION` 固定为空、UI 两项 OFF、`LLAMA_LLGUIDANCE=OFF` 后 BP-2 已核闭集内无其余 `FetchContent`/`ExternalProject`/`file(DOWNLOAD)` 触发点；未逐一读的子目录残留 UNKNOWN，构建过程一旦出现外联行为即失败并停（§6），不绕道。
- `-j 4` 为本次固定的并行度（板 6 核、统一内存约 7.3 GiB、swap 0，§8.2 nproc/mem 行；取保守值防 OOM），属执行细节固定项，不构成新构建配置；出现 OOM 迹象按构建失败处置，不调参重来。
- 解压：S 副本以 `tar -xzf` 解入本节§3工作目录 `src/`；归档实际顶层目录名运行时记录进证据，`<src>` 指向该顶层目录；若归档不含单一顶层目录即停（前置/结构不符，不计构建次数）。
- 不改变上述任一开关取值、不追加 cmake 定义；需要变更即越界，停回用户。

#### 3. 预算、监测与记账

- **计次**：构建 1 次、重试 0；「一次构建」= 进入 cmake 配置步骤起算。前置检查与 sha 重核不计构建次数，但计入整批墙钟。
- **墙钟**：整批（自批次目录创建/解压开始至构建命令结束或停止）≤ 7,200 s；批次启动即记 `started_utc` 与绝对截止（started+7,200 s），全部板端调用以 `LC_ALL=C timeout -k 2 <剩余秒>` 包裹，剩余秒运行时由截止时刻计算。
- **板新增占用**：≤ 5,000,000,000 B，含解压产物、构建目录、暂存与失败保留件；口径 = 本轮新建批次目录的 `du -sb` 分配量，峰值按采样最大值记。传板批次的 34 件占用属 TX-ASSETS 已结批次，不计入本轮；本轮不得写入传板目录。
- **工作目录**：板上 `~/eng-jet/` 下新建独占批次目录 `stageb-build-<UTC时间戳>/`（`mkdir -m 700`），内含 `src/`、`build/`、`raw/`（日志原件）；构建前确认该目录事先不存在、非链接。
- **监测方式**：构建前记录板 `df -B1 /` 可用字节与批次目录 du 基线（=0）；构建期间每 60 s 采样一次 `df -B1 /` 与 `du -sb <批次目录>` 及已耗墙钟，逐行追加进 `raw/monitor.log`；构建结束或停止后记录终值与峰值。判越界：任一采样 `du -sb` > 5,000,000,000 B，或采样墙钟 > 7,200 s，或 `df` 可用 < 1,000,000,000 B（保护余量，防占满整盘），立即按 §6 停止。
- **清理/保留**：成功时批次目录（含 `src/`、`build/`、`raw/`）整体保留在板上供后续已签维度复用（G2 服务另签后才可消费产物），本轮不清理；失败时现场与日志原样保留、计入 5 GB 上限，由用户决定后续处置；本轮不删除任何板端文件。

#### 4. 前置检查（只读；任一不满足即停、不算一次构建）

以「阶段B预检答复落实」及 §8.2 已核事实为准，构建前逐项重读：

- 磁盘：板 `df -B1 /` 可用 ≥ 5,000,000,000 B（§8.2 df 行已读 165,731,360,768 B 可用，构建前重读确认）。
- cmake：`cmake --version` ≥ 3.18（用户已反馈本人安装 cmake 3.28.3 / cmake-data 3.28.3-1build7 且 dpkg ii，见账本 2026-10-04「用户反馈cmake已装…」与「阶段B元数据授权落实」§1 B-APT 核清；§8.2 U1 已按该反馈闭合，不证构建成功）。
- 工具链：`/usr/local/cuda/bin/nvcc` 存在（§8.2：nvcc release 13.2）；gcc/g++ 13.3.0 与 make 在 `/usr/bin`；`/usr/local/cuda` 指向 `/etc/alternatives/cuda` 且 `targets/sbsa-linux` 存在（§8.2 cuda_dirs 行）；不造软链、不补装。
- 输入 S：§1 的 sha 重核符合；批次目录事先不存在。
- 链路与目标：SSH 目标从 `docs/evidence/P1-ENG-JET-001-relay.json` `link.ssh` 运行时解析唯一目标（当前证据 `jetson@192.168.8.2`，有线端口 22），沿用传板合同既定形式（既有 known_hosts、`BatchMode=yes`、`StrictHostKeyChecking=yes`），不改 SSH/系统设置、不新增 Host 别名、不转其他通道；权限分类器或沙箱拒绝即停派发。
- 前置全部满足才进入构建；前置阶段失败保留读数并回交，不重试前置以外的任何步骤。

#### 5. 明确不做

不联网（不取源/子模块/任何下载）；不加载模型、不运行 llama-server 或任何构建产物（产物只允许 stat/ls 级存在性核对）；不跑推理/冒烟/测试；不安装 31 轮子（INSTALL-W 仍 0）；不部署代码；不改 SSH/系统/沙箱设置；不取 Edge 源码/子模块；不含云；其余维度全部 0。

#### 6. 越界与失败处置

任一越界——墙钟超 7,200 s、板新增占用超 5,000,000,000 B、构建过程需联网或出现外联行为、需更改 §2 任一参数、cmake 配置或编译失败/OOM——即停：终止在途命令（timeout 包裹保证）、保留现场与全部日志、不重试、不调参、不换源，交回 Acceptance 核清后由用户决定。构建成功也只证明「固定 b11381 + §2 固定参数在本板可构建出 llama-server」，不签兼容性/性能/时延/显存/验收结论，不推出 GGUF 可运行。

#### 7. 执行凭据与证据

Implementation 生成 `docs/evidence/P1-ENG-JET-001-stageb-build.json` 与同名 `.md`（本轮不预写结果）：JSON 含授权条目绑定（上述账本标题与 (a)–(f)）、S 输入绑定链与构建前重核 sha 原输出、§4 前置逐项读数/rc、批次目录名/创建时间、逐次调用 argv 与 timeout 剩余秒、started/deadline/UTC 与单调耗时、monitor.log 采样（df/du/墙钟）基线/峰值/终值、§2 cmake 配置行与构建命令逐字、各步 rc/stderr、llama-server 产物 stat 读数、执行前后 git 凭据（`git rev-parse HEAD` 与 `git status --porcelain`）、成功/失败/NOT_RUN/UNKNOWN 与停止原因；消耗记账：BUILD-LLAMA 已用次数（0 或 1）、整批墙钟、板新增占用峰值/终值。MD 只写 JSON 与原始目录指针、数字摘要、边界与 needs_user，不回写旧证据快照。完成或中断立即交 Acceptance 核清，不自行继续 INSTALL-W 或任何后续步骤。

Consuming=no：本次落实轮为纯文档；未来构建执行不创建/消耗正式 ID、Play 或模型 API 预算，独占 UTC 批次目录不是 run ID；构建墙钟与板端磁盘独立计账、不借旧批额度。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE` 保持；不消费新复核 verdict、不签 DONE。S1/S2 STOP、补丁未上板、SR 5/5 耗尽、R1-5/6 OPEN 与 AC-7/8/9 `NOT_RUN` 保持。needs_user 现行条目见「阶段B预检答复落实」§5 末段；B-LOCAL-EXCLUDE-TRANSFER 排除条目仍推荐用户本人删除（代理不改设置）。

open_items: none

### 阶段B用户GGUF核清（2026-10-04，Acceptance）

登记轮次 `阶段B用户GGUF核清`；Dispatch-Id `P1-ENG-JET-001-阶段B用户GGUF核清-20261004T201423Z-139d`。机器Mac mini，零消耗只读核清；不属D/C/R轮、不新增AC或修订。

**出处：** `docs/authorizations.md`「2026-10-04 P1-ENG-JET-001 — 用户决定两件 GGUF 由本人在 Mac mini 自行下载（不另签代理重取；supervisor 会话代录）」(a)给期望字节/LFS sha256、(b)规定代理新尝试0、(c)要求接受只读核清、不符不得使用、(d)保留其他维度0；同日「用户反馈两件 GGUF 已本人下载：落点与本机字节/sha256 读数（supervisor 会话代录）」给用户本人操作确认、指定落点和读数。下表期望/用户值从这两条运行时解析，实际字节由本轮stat读取、SHA256由标准库流式现算后逐字比较；sha只从账本运行时解析，不抄入手维护合同。

**结论：两件均符合。** 只读遍历 `outputs/eng-jet/P1-ENG-JET-001/stageb-gguf-user/`，恰有下列两件普通文件，无其他文件、子目录或符号链接；合计1,926,804,800 B。核算前后size/mtime_ns/inode一致；未改、删、移动、解压文件。

| 文件 | 账本期望B | 用户读数B | 本轮现算B | 本轮现算SHA256 | 对账本期望字节/LFS sha | 对用户字节/sha读数 |
|---|---|---|---|---|---|---|
| Qwen3VL-2B-Instruct-Q4_K_M.gguf | 1,107,409,952 | 1,107,409,952 | 1,107,409,952 | 现算64位值与两条账本逐字一致（不抄SHA） | 字节与sha均符合 | 字节与sha均符合 |
| mmproj-Qwen3VL-2B-Instruct-F16.gguf | 819,394,848 | 819,394,848 | 819,394,848 | 现算64位值与两条账本逐字一致（不抄SHA） | 字节与sha均符合 | 字节与sha均符合 |

两件属用户本人下载，不计入代理下载额度；代理侧GGUF新尝试仍0、无需再问us.aws.cdn.hf.co放行或代理重取。原「阶段B下载核清」的两次302停对象/正文0 B/各1次尝试用尽及接受侧候选主机遗漏归因不变，不追认原批成功、不回退计次、不重写原证据。用户自下件已核清只证明字节完整与固定内容身份，不证明安装、板端运行兼容、时延或显存。

后续各维度推荐与仍缺前提唯一见「阶段B预检答复落实」§5：复用已取回并核清的31轮子、2 GGUF及保留源码，传输/传板、安装、解压/构建、部署、模型/数据/测试等仍0、不含云，由用户逐维度签。Overall REVIEW_PASSED / Lifecycle ACTIVE保持，不消费新verdict、不签额度或DONE；S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN与AC-7/8/9 NOT_RUN保持。consumed=none；核清过程中无网络请求、下载、ssh、上板、传输、测试、模型加载、安装、构建或租云。

### 阶段B下载核清（2026-10-04，Acceptance）

本节保留原代理批次核清快照及归因；其后用户本人取回与当前交接以「阶段B用户GGUF核清」和「阶段B预检答复落实」§5为准，下述原批未取回/另取推荐不再是当前待决。

登记轮次 `阶段B下载核清`；Dispatch-Id `P1-ENG-JET-001-阶段B下载核清-20261004T170626Z-ad47`。Mac mini，只读核清原下载md/JSON及本地批次；批次从本项输出根唯一 `stageb-download-*` 与JSON `output_dir_repo_relative` 交叉解析，未运行下载脚本、未改/删/解压原件。本轮consumed=none，无网络取证、下载、ssh、上板、测试、模型加载、安装或云操作，不写复核文件/授权账本。

#### 1. 原件、请求账与上限核清

依据：`docs/evidence/P1-ENG-JET-001-stageb-download.md`「数字摘要」「失败、未执行与未知」与同名JSON `binding/objects/requests/counts/started/wallclock/disk`；本地 `plan.json/started.json/requests.jsonl/invocations.jsonl`。来源metadata/source-archive/授权账本当前哈希与JSON记录一致，下载脚本哈希一致；完整签名Location只在本地读取核对，不抄回文档。

| 核清项 | 结果与限额 | 证据边界 |
|---|---|---|
| 轮子31件 | 逐件重新流式计算磁盘字节与SHA256，31/31与META-DEP固定file、plan、objects的期望/实际值一致；合计516,980,330 B，等于W分额；成功文件恰31件 | 固定pin/filename/URL/sha运行时解析；仅证明文件完整与身份，不证安装/隐式依赖/板端兼容 |
| 请求/计次 | 原账33个attempt_start/end、33个get_start/end逐一闭合；各对象1/1。全部33个原get_end与JSON对应请求一致（Location脱敏后）；GET33/35 = W31/31 + G_INIT2/2 + G_HOP0/2；实际发出主机仅files.pythonhosted.org×31、huggingface.co×2 | sent=yes；无未闭在途/额外调用；重试、HEAD/Range/补查、源码新增均0；分项不互借 |
| 正文 | W516,980,330 B、G0 B、总516,980,330 B ≤ 2,443,785,130 B | 两件302的Content-Length是未读跳转正文长度，不计作已下载GGUF或内容核验 |
| 墙钟 | started至报告195.6 s；本地report_done含证据写出195.7 s。运行时解析原下载收工提交时刻距started239 s；supervisor-dispatch.jsonl同派发end_confirmed(callback)距started293 s，可作包含提交推送/收尾的保守结束上界；均≤3,600 s | 不拿fetch单调24.086 s替代全批；本轮核清时间不拼接成原下载续跑；没有新fetch调用 |
| Mac新增占用 | 前余量151,187,775,488 B；计划并存上界2,493,973,546 B≤10,000,000,000 B。fetch原峰值逻辑517,141,710/分配524,570,624 B，含增长保护estimate524,832,259 B；最小余量150,663,106,560 B。report_done新增上界524,685,830 B | 原报告占用在证据/最后调用账追加之前；不冒充最终峰值。现算最终批次37文件逻辑517,145,594/分配517,234,688 B，下载md+JSON逻辑116,456/分配118,784 B，按两处较大口径相加517,353,472 B；原峰值加当前证据和后续调用账增长仍<525,000,000 B≤10 GB。分配量与历史读数不同，历史不覆盖，逻辑与分配分列 |
| GGUF停止 | 两件首GET均302、唯一Location精确主机us.aws.cdn.hf.co，不在合同§2四候选；原账无目标GET，正文读/存均0，无GGUF/.part/隔离文件 | 响应头X-Repo-Commit与固定revision、X-Linked-Size与两件期望B、X-Xet-Hash与页面对象hash吻合，只是头事实；GGUF内容SHA未核，实际文件未取回 |

结论：AC-10修订24/AC-11修订3的本次下载执行与停止/计账条件满足；交付是轮子31件取回、GGUF2件未取回。原33件尝试均已占用，各GGUF1/1用尽，未用G字节1,926,804,800 B及单跳GET2不用于继续/换对象/新会话，不追认为成功。

#### 2. GGUF归因与后续边界

**归因：接受侧合同候选闭集遗漏1项（us.aws.cdn.hf.co）。** 「阶段B下载授权落实」§2已明确四候选来自通常交付知识、没有实际Location；本次真实302表明该知识推定未覆盖实际主机。实现按字面停对象，未跟随/重试/越界，不计实现错误。不标 `上游漏检`：workflow §4.4该依据专指核对轮放过字面不符，本次没有这一事实；亦非 `上轮漏检`、RED_LINE或已有复核finding。这里只作合同准备归因，不自签finding分级/独立verdict，不改R3归因计数或SCOPE_GAP账本，不添新AC/修订。

GGUF另取涉及新增网络主机与新尝试，接受/supervisor不得代定。现行needs_user及完整具名推荐只在「阶段B预检答复落实」§5 B-LOCAL-ALLOW-DOWNLOAD/B-SIGN-GGUF-RETRY；用户答复前新尝试、传输、解压/安装/构建、测试/模型与板端执行各维度0，不含云。不追加新主机进现行合同、不修改本机设置；原§2与失败证据保留，用户授权后接受只能追加解释、再交实现。

Overall REVIEW_PASSED / Lifecycle ACTIVE保持；这次资源核清不消费新复核verdict、不签B1完成或DONE，不产生Jetson兼容/性能结论。S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN与AC-7/8/9 NOT_RUN原样携带；用户交接的owner/status只在状态板交接行维护。

### 阶段B下载授权落实（2026-10-04，CLARIFY）

登记轮次 `阶段B下载授权落实`；Dispatch-Id `P1-ENG-JET-001-阶段B下载授权落实-20261004T162647Z-6da4`；Acceptance，Mac mini。本轮只读本机合同/原件/设置，不发来源请求、不下载/ssh/上板/跑测试/加载/安装/租云；consumed=none。依据账本2026-10-04「用户签发 B-SIGN-DOWNLOAD：Mac mini 下载 33 件（31 轮子 + 2 GGUF），墙钟 ≤ 1 h、Mac 占用 ≤ 10 GB（supervisor 会话代录）」(a)–(e)，将用户已签额度落实为以下执行合同；不是接受角色签额，不扩大阶段B边界。原AC/历史读数/授权/机读快照不覆盖。

#### 1. 追加 AC 修订、对象与归因

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 24 | CLARIFY（解释修订14/15/17/20、§5）：只由Mac mini Implementation按本节§1–4下载31固定轮子+2固定GGUF，各1次、重试0、源码新增0；分额与累计≤2,443,785,130 B共账，整批≤3,600 s、本次新增占用含暂存/.part/失败保留件≤10,000,000,000 B、执行前后核查。单跳/本机域名/目录脚本/拒绝停派发及计次规则逐项记录；其他未签维度0、不含云，任一越界停整批回用户。 | artifact: 上述B-SIGN-DOWNLOAD账本(a)–(e)、本节§1–4；未来 `docs/evidence/P1-ENG-JET-001-stageb-download.json/.md` | K1K3K4 | 2026-10-04 |
| AC-11 修订 3 | CLARIFY（解释AC-11及修订2，关联AC-10/12）：本次33件身份/期望字节/内容sha按本节§1从既存META-DEP/META-GGUF与B-FACTS-GGUF账本运行时解析；核原件绑定后下载，完整实体须字节与sha双符合方可转为成功文件。sha不符停该对象并隔离、重取0；不能用Xet hash/舍入size代替内容sha/整数B，未完成或不符件不用于资产/安装/运行。 | artifact: `docs/evidence/P1-ENG-JET-001-stageb-metadata.json` META-DEP/META-GGUF、B-FACTS-GGUF账本原表；未来同名stageb-download.json/.md | K1K3K4 | 2026-10-04 |

归因：来自本次用户具名下载授权及此前§5固定身份/核验合同，追加既有AC解释2条、新AC=0；非C轮增项，不改目标/模型/协议/STOP线或独立verdict。这里只下载资源，不签B1代码停点完成；未来不可重跑的板端/模型消费仍须其依赖代码先C/R，下载不授这些消费。

- **DL-WHEELS闭集**：metadata.json `META-DEP.projects` 的31个 `file`，逐项与 `proposed_pins_for_acceptance` 对齐；取 `name/version/file.filename/file.url_not_opened/file.size/file.sha256`。沿 `version_json_request_n`、`requests[].file`、`output_dir_repo_relative` 定位已存版本JSON，核原件字节/sha、urls[]唯一选定文件及project/version/filename/URL/size/digests.sha256一致；不查询新版本。31件期望size重加须等于516,980,330 B。静态声明闭集沿「阶段B核验核清」§1，只允许这些已建轮子，不用pip resolver/干跑/SDK/换源/换pin或sdist。
- **DL-GGUF闭集**：仅META-GGUF.files中的 `Qwen3VL-2B-Instruct-Q4_K_M.gguf` 与 `mmproj-Qwen3VL-2B-Instruct-F16.gguf`；repo/fixed_revision/filename/blob_url_fixed/页面SHA从该JSON运行时解析，同revision须与revision_plan.revision及已存固定页一致。期望整数B与LFS内容sha从账本「用户提供 B-FACTS-GGUF…」原表按filename唯一匹配，sha须与META-GGUF.sha256/fixed_page.sha256一致；期望分别1,107,409,952 B与819,394,848 B，合计1,926,804,800 B。不手抄revision/sha，不拿Xet对象hash代内容sha，不改取main/Q8_0/base。
- **DL-SOURCE=0**：只保留既有37,831,966 B副本，定位/sha沿source-archive.json原件解析，不复制、不重取；源码复用不增加下载件数，解压/构建/传板仍0。输入身份、原件或额度不一致/缺项/歧义时在请求前停止整批回接受，不网络补查。

#### 2. 请求 URL 与跳转合同

- **轮子每件**：唯一URL就是该file.url_not_opened，形式 `https://files.pythonhosted.org/packages/<既存路径>/<固定filename>.whl`，逐字复用、不加`.metadata`。仅HTTPS、精确host `files.pythonhosted.org`、无账号密码/非标准端口/fragment；**跳转0**，禁自动follow，3xx只记状态/Location、不访问并停该对象。
- **GGUF每件**：由固定blob URL只将路径段 `/blob/` 换为 `/resolve/`，即 `https://huggingface.co/<repo>/resolve/<fixed_revision>/<filename>`；不请求blob/main/HF API/树/HEAD/Range或连通页，不附加随机query。固定revision/filename均取§1来源。
- 已存四份GGUF页面标为 `Xet Pointer Details`，原件只给HF固定身份，**没有实际resolve响应/Location或可验证的CDN目标主机**；本轮不联网探查。依据通常的HF LFS/Xet文件交付知识，候选主机闭集为 `cas-bridge.xethub.hf.co`（Xet桥的整件HTTP交付）、`cdn-lfs.hf.co`、`cdn-lfs-us-1.hf.co`、`cdn-lfs-eu-1.hf.co`（LFS/区域CDN）；这些是待用户放行的候选，不称本文件一定跳到其中某一个，不启用hf-xet分块协议或访问CAS重建/鉴权端点。
- **GGUF执行时只允许一次跳转，Location主机须在用户本机已放行的域名内，否则停该对象**。进一步限定Location为上述四个精确候选之一、HTTPS、无账号密码/非标准端口/fragment；签名query可原样使用、不改签名、不另请求刷新。仅301/302/303/307/308、Location唯一且能解析时手动发目标一次GET；最终须200且不再跳转。初始resolve直接200可接收，无须补CDN请求。缺Location、未放行/非候选host、第二跳、非200、质询、非identity编码或截断均关闭响应、停对象并隔离，不调用另一URL/SDK规避。禁止自动follow/重试/续传、多连接/分块/并行下载与抓子资源。
- 每件1次指一次下载尝试，GGUF的许可单跳属于同件交付、不构成重试：轮子GET≤31，GGUF初始GET≤2、经校验目标GET≤2，**HTTP GET总≤35**；分项不能互借，实际请求全部记账，未用不转给新对象。重取/HEAD/Range/补查为0。3xx不读取正文，关闭后记已实际读取的正文B（若有），不能凭Location再下载另一个对象；最终内容由固定期望字节与内容sha双核约束。

#### 3. 计次、墙钟、磁盘与失败处置

- **落点**：Implementation在Mac mini运行时独占创建 `outputs/eng-jet/P1-ENG-JET-001/stageb-download-<UTC>/`，已存在即停，不覆盖旧目录/原件。这是本地输出目录，不是scenario/session/run ID；只放本次脚本、离线对象计划、持久请求/对象账、下载原件、`.part`、隔离件及本次日志。不向数据根/runtime/板/云写；不按header任意路径命名文件，filename须为闭集安全basename。成功完整体核B/sha后同目录原子改名，不复制第二份；失败件同目录改名隔离、先记账保留，不删失败件腾额度或作安装输入。
- **一次批次**：先离线核用户域名/目录调用放行、全部来源/限额、旧本批started账与可用余量；已有批次启动/对象计次时只整理原账，不用新目录/新会话重置。整批计时从首次创建本批独占输出目录开始，覆盖脚本准备、计划/离线核查、请求、核sha、证据及收尾；目录创建时持久记started_utc与截止时间，唯一执行脚本继承该截止时间并记录单调耗时，不能从脚本启动另算1 h。硬截止≤3,600 s，每次连接/流式读取/哈希前核剩余时间，超时关闭响应、终止本批活动操作、不再发下一件。批次不后台脱离会话无限运行、不另开续跑。超时/磁盘/累计字节等全局限额触发即停整批回用户。
- **计次**：每对象首次GET前持久登记attempt-start并占1/1，逐GET在发出前登记序号/UTC/对象/URL；成功、HTTP错误、认证/网络失败、权限拒绝、部分响应/sha不符均不回退。权限在GET前拒绝则记已预约attempt及request-start为未发出/UNKNOWN，不冒称HTTP已发出，但预约不得回收重取；不能把失败改为另会话首次。未发出/未尝试对象单列NOT_RUN，未闭在途记UNKNOWN；本轮尚无下载尝试。
- **字节保护**：identity响应实体流式落盘/计sha，不整件读入内存、不HTTP自动解码/解压。每件实际完整B须等于§1期望，超期望B即关闭中止；读取缓冲与写盘先受对象/分项/总量剩余限制，Content-Length若大于期望/剩余则提前拒收，缺失时仍逐块防越界、不以header替代实测。达到期望后如仍有响应数据即判超量，不保存额外正文；记录可得超量迹象及实际已读取/已保存B，所有失败/部分/跳转或错误响应的已读正文也计对应分额与总额。W≤516,980,330 B、G≤1,926,804,800 B、总≤2,443,785,130 B共账；不能只加成功件或删除失败后归零。若实际超界，保留事实、停整批回用户，不宣称合规。
- **完整性失败**：HTTP/网络/sha不符或短于期望均停该对象、隔离，重试0；sha仅对完整实体与期望内容sha比较，不符即不得列成功资产。可在全局前提/限额仍满足时继续其余未尝试的固定独立对象；超期望B或全局边界失败停整批。用户决定之前不重取/替换失败件、不解压/安装/传板。
- **占用核查**：10 GB按十进制=10,000,000,000 B，约束本次Mac新增占用，含脚本/计划/证据/日志、HTTP暂存、`.part`与隔离/失败保留件，而非仅33件成功大小。执行前记录目标文件系统可用B与本项既存目录/证据占用基线；新增源码下载0、原件不删除扣账。无解压/缓存/复制、串行单份原子改名，先按33件总B+本次脚本/日志/证据受控增长作并存上界，须证明≤10 GB且目标可用余量足够；不能用账本约151,938,785,280 B快照代执行读数。下载中在每块写盘前核剩余额度与可用B，保留本次峰值（逻辑B与分配占用分列并以较大口径保护），脚本/日志增长也受同一封顶；无法可靠核查/余量不足即停整批。结束/异常路径都记录同口径占用、峰值和可用B，与执行前基线对比，禁止仅事后查成功文件。墙钟封顶/新增占用只用于本批下载，不授其他Mac加工或板端占用。

#### 4. 本机前提、证据与回交

只读 `.claude/settings.local.json` 的sandbox.network.allowedDomains与permissions.allow：已有 `files.pythonhosted.org`、`huggingface.co` 及本项输出目录python3规则；上述四个CDN候选均未列入，四份原页也未证实际Location。本轮不代改设置、不发连接测试。**交用户先落实§5 B-LOCAL-ALLOW-DOWNLOAD**；用户本人放行并反馈后，下一Implementation派发仍先离线核当时设置、目录脚本窄规则与§3余量/计次前提，齐全才按合同执行，未齐先回交而非试请求。

保持会话沙箱启用，脚本仅置于本次新输出目录，**仅以 `python3 <目录>/<脚本>.py` 运行**；不使用内联python、curl/WebFetch/SDK/关沙箱/改设置或其他通道。被权限分类器/沙箱拒绝即停整个派发（不再下载下一件），保存原错误与已计账，计数不归零、不换会话/写法重试。遵守supervisor单写者与现有共享槽位互斥；不改其他工作项。

Implementation生成 `docs/evidence/P1-ENG-JET-001-stageb-download.json` 与同名 `.md`（本轮不预写执行结果）：JSON记录来源指针/原件绑定、33件机器生成计划、机器/脚本调用、执行前后git状态、离线放行核查、尝试与逐GET start/end/实际发出或未知、URL/Location链/状态、期望与实际B/sha、分项/累计/剩余、UTC/墙钟、占用基线/前后/峰值、隔离/未执行/未闭在途及停止原因；MD只放原始目录/请求账/JSON指针、数字摘要、未知/失败与needs_user。实际目录、revision/sha/HEAD运行时生成到机读证据，不手抄回合同；旧metadata/source-archive/ledger原件不改不删，不重建A账本。完成或中断立即交Acceptance核清，不自行安装/解压/传板/模型加载/数据加工/测试/租云。

**轨道**：仅本次33件Mac公开文件下载，无正式ID/Play/模型API预算，Consuming=no；HTTP/字节/时间/磁盘额度仍独立计账，不借FRAME或旧批余额，不把UTC目录当正式ID。其余维度0、不含云；Overall REVIEW_PASSED / Lifecycle ACTIVE保持，S1/S2 STOP、补丁未上板、SR5/5耗尽、R1-5/6 OPEN及AC-7/8/9 NOT_RUN原样保留，不签DONE、不推出板端兼容/性能结论。

open_items: none

### 阶段BGGUF事实落实（2026-10-04，Acceptance）

登记轮次 `阶段BGGUF事实落实`；Dispatch-Id `P1-ENG-JET-001-阶段BGGUF事实落实-20261004T161000Z-e830`。依据账本2026-10-04「用户提供 B-FACTS-GGUF：两件 GGUF 精确字节与 LFS sha256（supervisor 会话代录）」，仅Mac mini只读核对，不联网补查/下载/ssh/上板/运行测试/加载模型/安装/租云；不是C/R轮、不签独立verdict。本轮不修改机读证据/原件/授权账本。

**核清：** 从账本原表解析两件整数B与sha；逐件filename和sha与metadata.json META-GGUF.files（main_page/fixed_page/顶层sha256）逐字一致。两件fixed_revision与revision_plan.revision一致，固定blob URL的revision/filename及固定页page_revision_fields一致；从JSON输出根与requests[].file解析原请求3/4/5/6的本机页面原件，四份字节/sha均复算相符，文本所含filename/完整revision/页面SHA与JSON一致。用户未另写revision，以filename+内容SHA对应已核同revision的两件固定身份；不把用户sha套给Xet hash，也不由舍入1.11GB/819MB换算整数B。具体SHA/revision/目录仍由账本及JSON运行时解析，不抄入手维护正文。

**出处充分性裁定：足够用于本次精确字节预算推荐。** 出处明确标为“用户提供的核查结果”，可追溯至具名账本原表；与已核固定身份的内容SHA逐件一致，足以绑定本次条件字节推荐，无须再问已答提供方式或索取另一出处。不声称用户提供了页面URL、固定revision原话或本地测量原件，也不声称原页面整数size已核/模型内容已下载复证。原metadata.json exact_bytes=UNKNOWN保留为元数据执行时快照，不回填；用户来源事实与该快照的区别如实披露。未来经另签取回须记录实际整数B/sha并与两来源逐项核，不符即停该对象、失败重取0，交接受/用户。

**重算与边界：** 重加31轮子size、用户两件B与已核源码archive.bytes，所得33件新增下载、34件单程资产传板、每端输入/两端输入及相对既存源码新增值只见「阶段B预检答复落实」§5；该节仍是唯一用户待决入口。旧轮次中的GGUF待提供/总量UNKNOWN是当轮快照，本次只替代文件字节未知，完整双向总量、峰值/余量/墙钟/代码束/日志仍UNKNOWN、生效0。本轮新增AC/修订=0，仅落实事实/刷新推荐，不扩目标、合同STOP或信封。Overall REVIEW_PASSED / Lifecycle ACTIVE保持；S1/S2 STOP、补丁未上板、SR5/5耗尽、AC-7/8/9 NOT_RUN、R1-5/6 OPEN不变，不消费verdict、不签DONE；consumed=none。

open_items: none

### 阶段B元数据授权落实（2026-10-04，CLARIFY）

登记轮次 `阶段B元数据授权落实`；Dispatch-Id `P1-ENG-JET-001-阶段B元数据授权落实-20261004T064743Z-ebd9`。依据 `docs/authorizations.md`「2026-10-04 P1-ENG-JET-001 — 用户反馈 B-APT 已在板上自装 cmake 3.28.3，并授权代理只读查询 B-FACTS 来源元数据（supervisor 会话代录）」(a)–(c)。本轮仅接受合同落实，未查询网络、未ssh/上板、未跑实现测试；consumed=none。原AC/预检快照保留；本节覆盖旧JB-6/B-FACTS的板相关元数据禁用解释，云相关禁用仍有效。

#### 1. B-APT核清与追加解释

用户粘贴的 `cmake --version` 为3.28.3，`dpkg-query` 中cmake与cmake-data均3.28.3-1build7、ii；3.28.3≥固定b11381 CUDA构建最低3.18。结合§8.2已有build-essential/gcc/g++/make/git/nvcc读数，**U1必需工具缺项按用户反馈闭合**，不宣称本轮代理独立板端复证或构建通过。apt安装原命令/成功输出、实际新增升级其他包仍UNKNOWN；**不补问**：本次核清对象是所需cmake版本/包状态，用户已给两项直接读数，完整apt事务不影响仅查来源元数据的下一动作。未来若构建/环境裁定依赖其他包变更，须具名核该事实，不能把UNKNOWN当未变；不要求重跑预检。用户安装不计代理额度，代理sudo/apt仍0。

| 编号 | 追加合同解释 | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 18 | CLARIFY（解释修订15/17、§5；B-APT/B-FACTS）：按上述账本(a)核清U1的cmake缺项；仅依(b)由Mac mini实现角色执行本节§2–4一次板相关元数据查询批次，上界为86个HTTP请求、无重试，失败/未核字段UNKNOWN；不得借此下载、安装、上板、查云或扩大其他维度。结果交接受核清，不由实现自行授下载/安装额。 | artifact: 上述账本(a)–(c)、本节§1–4及未来docs/evidence/P1-ENG-JET-001-stageb-metadata.md | K1K3K4 | 2026-10-04 |

此行只解释已授权的来源事实通道，不新增验收目标、STOP线或信封。本轮不改变S1/S2 STOP、补丁未上板、AC-7/8/9 NOT_RUN、R1-5/6 OPEN；Overall REVIEW_PASSED / Lifecycle ACTIVE保持，不签DONE。

#### 2. 一次元数据批次对象与端点合同

执行角色Implementation，唯一机器本机Mac mini，板端零操作。本批只读公开来源元数据；下表之外无对象/端点许可。HTTP GET仅可取下表JSON/HTML文本；asset/file URL只记录、不访问。不用HEAD、Range GET、HF API、raw源码或pip解析器/干跑，不下载内容来读METADATA或测大小。

| 对象ID / 闭集 | 具体URL形式或解析法 | 必记事实与单对象上限 |
|---|---|---|
| META-LLAMA：ggml-org/llama.cpp b11381唯一主源码tar.gz归档；不取Edge源码/子模块 | `https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/b11381`（release元数据）及 `https://github.com/ggml-org/llama.cpp/releases/tag/b11381`（release页面），各一次。解析tag、归档链接及commit链接；固定commit从这两份文本运行时解析，不另访问提交/归档/codeload。归档选择唯一tar.gz，不同时选zip；如果release有明确同tag主源码asset，按唯一身份记录；不混入二进制发布包。 | 仓库/tag、归档URL/文件名、页面可证的固定commit、精确字节及其字段来源。`assets[].size`只属于该asset，不可套给自动生成的`tarball_url`；元数据没给该归档精确字节/commit或身份不唯一则UNKNOWN，禁止取归档内容/HTTP Content-Length冒充归档字节。≤2请求。 |
| META-W：tensorrt-edgellm 0.11.0，板cp312/aarch64/glibc2.39；extras仅server | `https://pypi.org/pypi/tensorrt-edgellm/0.11.0/json`；从`urls`唯一匹配`bdist_wheel`、版本0.11.0及`cp312-cp312-manylinux_2_39_aarch64`文件名（名称规范化比较）。解析出的完整文件名是固定身份，不能自行猜填；0个或多个匹配停该对象。 | 精确文件名、URL（不打开）、size整数B、digests.sha256、requires_python、yanked、info.requires_dist原文、Python/ABI/平台标签；release级Requires-Dist非轮子内逐文件复证，动态/缺失/差异不明则UNKNOWN。固定版本≤1请求，不取x86轮子或sdist。 |
| META-DEP：板W八个直接项与递归传递依赖；含W共≤40个规范化项目 | 直接种子：tensorrt-edgellm==0.11.0、cuda-python>=12.6,<14、fastapi==0.139.2、uvicorn==0.51.0、huggingface-hub>=1.5.0,<2.0、av==17.1.0、numpy==2.2.6、python-multipart==0.0.32。固定版本用`https://pypi.org/pypi/<规范化项目>/<固定版本>/json`一次；范围版本先`https://pypi.org/pypi/<规范化项目>/json`一次，按§3解析唯一具体版本，再版本JSON一次。新对象只能来自上述种子或已读Requires-Dist的有效边；对象表逐项展开。 | 每依赖固定版本、约束/父边、激活extra/marker、Requires-Dist原文、selected filename/URL/平台标签/精确size/sha256/Requires-Python及字段来源；排除边也记录原因。系统TRT来自§8.2已装绑定，只列复用、不查/下载PyPI tensorrt。transformers==5.14.1是旧server-tools条件UNKNOWN，不能自动激活该extra；仅当server有效依赖边要求它才纳入，否则保留必需性未知。每项目≤2请求，全体含W≤80请求。 |
| META-GGUF：Qwen/Qwen3-VL-2B-Instruct-GGUF中且仅Qwen3VL-2B-Instruct-Q4_K_M.gguf与mmproj-Qwen3VL-2B-Instruct-F16.gguf | 每文件先`https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct-GGUF/blob/main/<文件名>`一次；从文件页解析仓库commit链接的完整revision，再同一文件`.../blob/<revision>/<文件名>`一次固定身份。两件须同revision；可复用已读页解析revision，不另请求树/历史/API。 | 仓库、固定revision、精确文件名、blob URL、页面SHA256/LFS或Xet身份字段的原标签及精确字节；两件各≤2请求。舍入1.11GB/819MB不换算精确B；页若无整数size或两件不能固定同revision，缺字段UNKNOWN，不改用resolve链接、API、HEAD或内容取回。 |

#### 3. 板W逐依赖解析及有界失败规则

只在Mac离线静态解析已取JSON，以目标Linux/aarch64、CPython3.12.3、glibc2.39评价Requires-Python与PEP 508 marker；不能用Mac的sys_platform/machine决定板依赖。从W基础+server与具名种子开始，规范化项目去重，按项目名字典序处理待定边；传递extra只按有效Requires-Dist显式传入。已固定pin不改；范围项按查询时项目JSON中满足全部已知约束、Python条件且有目标兼容非yanked非预发布轮子的最高稳定版本选一次，立即记精确版本、选择时约束与UTC。兼容wheel可为cp312或适配cp312的abi3、py3通用轮子，平台可为any或glibc要求≤2.39的aarch64标签；禁止Mac/x86、sdist或源码构建。多个兼容文件时优先cp312-cp312，再兼容abi3，再通用Python；平台优先适配的最高manylinux下限，再any；仍有歧义记UNKNOWN，不猜选。

后续边与已选pin冲突、marker/版本/tag无法可靠静态解释、缺Requires-Dist或需要动态构建元数据时，停止该依赖分支，保留未闭边与UNKNOWN；不换版本回溯、不启动pip resolver、不换源或下载探明。无需安装解析工具：只用本机已有离线能力，缺工具则停并报告，不新增pip。全图遍历到闭集且每有效边/文件均已核才可报告静态文件闭集；被40项目上界截断时不能说已闭合。查询结果是待接受核清的拟pin，不更改运行环境/验收或直接进入安装。

具名上限 **META-BATCH-1：一次批次，HTTP请求总≤86 = META-LLAMA≤2 + META-DEP（含META-W）≤80 + META-GGUF≤4；项目≤40**。依据为上述账本(b)明确委托接受角色落实查询方式/次数：给每项目至多一份版本选择JSON和一份固定版本JSON，40项目只是覆盖8直接项及至多32传递项目的扫描截断上限，**不是已知依赖数、不是下载/包数额度，也不保证核齐**；两个GH端点与两件HF各主分支/固定页各一次有明示目的。无失败重试、重复端点重取或第二批，未用数不转给其他对象/机器/云。每实际发出的HTTP请求（含失败）计1；禁自动跳转/重试、页面子资源抓取/预取/自动翻页，3xx/4xx/5xx、超时、断网、质询/验证码均保存可得元数据状态并停该对象，不跟Location换端点；质询对象不再经另一端点探取同材料。每请求超时≤30s，到达次数/项目上界立即停；允许继续尚未失败的独立对象，禁止替换失败对象。越界/补查询回用户，不把本批上限记成接受签发的执行信封。

#### 4. 输出落点、回交与禁止项

原JSON/HTML响应、HTTP状态、UTC、实际请求URL、对象/计次/异常、响应原件sha256与字节数仅落本机 `outputs/eng-jet/P1-ENG-JET-001/` 下运行时创建的唯一`stageb-metadata-<UTC>`目录（已存在即停，不手抄实际目录名/sha进手维护文档）。新增 `docs/evidence/P1-ENG-JET-001-stageb-metadata.json` 记录逐对象/逐项目元数据字段、固定身份、父边及UNKNOWN、实际请求账/上限/剩余；`docs/evidence/P1-ENG-JET-001-stageb-metadata.md` 指向原件和JSON并分列已核/未核、拟闭集与后续needs_user。不覆盖旧资产/账本、不写数据根、主树runtime或板端。不为只有舍入体积的归档/模型制造精确字节；原件SHA仅在机读证据中生成。

本批Implementation完成后立即交Acceptance核清来源、pin与计次并重算可核的申请；缺来源事实由接受具名交用户提供或另授权，下载/安装/传输/磁盘峰值等仍0、不先签。下一owner/status只在状态板维护。

**逐字执行边界：只此一批META-BATCH-1，Mac mini实现角色，只查上述板相关来源元数据，≤86请求/≤40项目、无重试；不下载任何文件内容（含轮子/归档/模型及Range GET取内容）、不登录、不绕过质询/验证码、不查云端依赖；不ssh/上板、不下载安装/构建/加载模型/回放/测试/租云。其余执行维度0、本次不含云。** 本批不创建scenario/session/run ID、不用Play或推理API预算；PyPI JSON/GitHub release元数据仅是用户具名允许的公开元数据通道，判为Consuming=no，不借FRAME的消耗轨道。网络本轮未执行，未来查询不新增硬件性能/兼容证据。

open_items: none

### 阶段B元数据续跑落实（2026-10-04，CLARIFY）

登记轮次 `阶段B元数据续跑落实`；Dispatch-Id `P1-ENG-JET-001-阶段B元数据续跑落实-20261004T074412Z-17de`。依据 `docs/authorizations.md`「2026-10-04 P1-ENG-JET-001 — 用户追认 META-BATCH-1 前 4 次请求，并放行续跑同一批（supervisor 会话代录）」(a)–(c)，并承接同日「用户确认元数据查询次数上限按推荐」。本节只追加解释AC-10修订18及「阶段B元数据授权落实」§2–4，不另签额度、不开启第二批；原条款保留，以本节具名续跑例外为准。

#### 1. 中断事实与追认归属

只读依据为 `docs/evidence/supervisor-dispatch.jsonl` 中 Dispatch-Id `P1-ENG-JET-001-阶段B元数据查询-20261004T065447Z-7720` 的 `finished` 记录及该记录定位的本机唯一输出目录内 `ledger.json`、`raw/001.body`至`raw/004.body`。账内4次GET均为合同具名端点、HTTP 200；4份原件字节数及sha256与原账一致。本轮只核原件与计次，不解析来源字段或签拟pin/闭集，所需字段仍UNKNOWN。

前4次在关闭会话沙箱下发出，随后本机权限分类器拒绝离线解析，原派发中断、无提交，元数据证据JSON/MD未产出。用户已追认这4次及其发出方式，原件可采信复用，**全部计入META-BATCH-1，不能清零、作未用或重取**；用户本人已加本机沙箱网络放行及该目录python3规则是账本所记事实，本轮未试网、未验证设置。该追认不许可续跑关闭沙箱。

#### 2. 同批续计与剩余闭集

| 计数维度 | 已用 | 续跑最多可用 | 原批上限 |
|---|---|---|---|
| HTTP总请求 | 4 | 82 | 86 |
| META-LLAMA | 2 | 0；只离线解析已取release JSON/页 | 2 |
| META-GGUF | 2（两件main blob页各1） | 2（仅两件同revision固定blob页各至多1） | 4 |
| META-DEP（含META-W） | 0 | 80 | 80 |
| 规范化依赖项目（含W） | 0 | 40 | 40 |

本批失败0、重试0；续跑**剩余≤82请求/≤40项目，重试0**，上述分项不得互借。从原账4/86续计，每实际发出请求（含失败）计1，编号从原账末项运行时派生；已取4个URL禁止重复请求，META-LLAMA不再联网。先离线解析两份main页，只有可按原§2证明同一完整revision时才访问两件固定页；否则该分支UNKNOWN并停，不补取main/树/API/内容。META-DEP沿原§2–3的种子、有效边、版本/轮子选择及目标平台规则，仍以含W的40项目截断，无回溯、重试或第二批；任何不足/未核按原失败规则回交，不用余额替换对象或扩大端点。

#### 3. 原目录续用例外与原件保护

选择**复用已存在输出目录与4份原件**，依据上述用户授权(b)明确放行同批续跑并将目录解释交接受裁定，(a)要求复用不重取；新开批目录会割裂已用计数。本例外仅限§1具名`finished`记录定位的本批目录：实现从该记录运行时解析实际目录，核对原账/4份原件/计数后续用；不手抄实际目录名或SHA进手维护文档，不以“最新目录”或通配匹配代替本批身份。原§4「已存在即停」对其他目录/批次继续有效，不能借例外创建新批、重新从0起账或覆盖旧资产。

原`ledger.json`、4份响应原件及原派发文件只读、不改不删。续跑仅在该目录增写解析脚本、新响应原件和`resume-requests.jsonl`追加请求记录；每次新增请求先落编号/URL/对象/开始时刻，完成后补状态、字节及哈希，证据总账合并原账4条与续跑记录，分别保留来源、累计/分项/剩余计数，不把原账改写为新账。新响应编号接原末项，不能覆盖`raw/001–004.body`；目标新文件已存在、原目录不唯一、原账/原件缺失或核验不符、出现无法核清的在途请求时停交接受，禁止重取补齐、清理或重启归零。

#### 4. 沙箱、输出与回交

**续跑不得关闭会话沙箱**，不得用关闭/绕过标志或改设置绕过拒绝。离线解析脚本须置于上述输出目录内，以 **`python3 <该目录>/<脚本>`** 运行（实际路径运行时解析）；不改用目录外脚本、`python3 -c`或stdin临时脚本绕过本机窄规则。若本机权限分类器/网络规则仍拒绝，保存已有账与原件并停下交接受/用户，不能把已加放行理解为禁用保护；本轮接受不改设置、不试探通道。

其余对象、端点、解析/有界失败规则、禁止项、输出根及证据文件逐字沿「阶段B元数据授权落实」§2–4。新增原件只落原目录，最终仍交 `docs/evidence/P1-ENG-JET-001-stageb-metadata.json`（含累计请求账、原件指针/机读SHA、已核/UNKNOWN）及同名`.md`；只解析/取具名JSON/HTML元数据，不下载文件内容、不登录/绕质询、不查云、不ssh/上板、不安装/构建/加载模型/回放/测试/租云。实现完成或遇阻即交接受核清来源、pin、计次及可核申请，不自动启动下载/安装。

本批不创建scenario/session/run ID、不用Play或推理API预算，沿原§4判为Consuming=no；其余执行维度0、不含云。本轮只读本机事实并落实合同，consumed=none；S1/S2 STOP、补丁未上板、AC-7/8/9 NOT_RUN及R1-5/6 OPEN保持，Overall REVIEW_PASSED / Lifecycle ACTIVE不变，不签DONE、不消费新verdict。

| 编号 | 追加合同解释 | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 19 | CLARIFY（解释修订18及元数据授权§2–4）：依上述追认/续跑账本计入已用4/86，仅同批续跑剩余≤82请求/≤40项目、重试0；按本节§3复用原目录与原件且保留原账，不重取/归零，按§4保留沙箱并在该目录内用python3执行解析脚本；其余通道/输出/禁止项沿原合同，完成或拒绝即回交接受，其他维度0。 | artifact: 上述账本(a)–(c)、§1具名finished记录与原账/原件、本节§1–4及未来docs/evidence/P1-ENG-JET-001-stageb-metadata.json/.md | K1K3K4 | 2026-10-04 |

open_items: none

### 阶段B元数据核清（2026-10-04，CLARIFY）

登记轮次 `阶段B元数据核清`；Dispatch-Id `P1-ENG-JET-001-阶段B元数据核清-20261004T080315Z-dba1`。Acceptance仅在Mac mini只读核清 `docs/evidence/P1-ENG-JET-001-stageb-metadata.md` §1–6、同名JSON全部对象及本机原件；不联网/抓取/ssh/上板/测试/模型/下载安装，不消费本批余额。以下是来源/合同裁定，不是C轮候选核对或独立复核；用户待决只在「阶段B预检答复落实」§5，不新增另一入口。

#### 1. 原件、来源与计次核清

从 `docs/evidence/supervisor-dispatch.jsonl` 中原批 Dispatch-Id `P1-ENG-JET-001-阶段B元数据查询-20261004T065447Z-7720` 的唯一finished报告运行时解析输出目录，与metadata.json `output_dir_repo_relative`一致；没有按最新目录猜选。读取原`ledger.json`与4份原件、`resume-requests.jsonl`及新增57份原件：原账4条、续跑57对start/end、编号连续、无未闭在途，61个URL互异；逐条对照机读requests的对象/URL/GET/UTC/状态/字节/sha字段，**61/61响应字节与sha256一致**，全200、失败/重试/3xx0。只读保留原账与原件，不重建账、不复制可派生目录名或SHA到手维护文档；这些值仍从JSON/原件运行时取。

累计61/86 = LLAMA2/2 + GGUF4/4 + DEP含W55/80；依赖项目31/40（7固定版本、24区间选择，每项目1或2请求）。未用25次/9项目的处置见§3，JSON的remaining保留执行时算术快照。原4次的追认仍依原授权，计数不清零。原件哈希只证明本机响应与记录一致，不证明远端模型/轮子内容已取回验证。

#### 2. 逐对象身份、拟pin与字段核对

- **META-LLAMA**：raw请求1 JSON的tag/target_commitish与请求2 release页唯一完整commit链接一致，metadata.json fixed_commit可作为b11381的固定源码身份。draft=false、prerelease=true、35个asset名称及tarball_url与原件逐字段一致；asset全为二进制/UI/xcframework，无主源码asset，选择唯一自动tar.gz沿原合同，不能用asset字节替它。归档文件名/整数B/sha仍UNKNOWN，未访问lazy资产子页或归档。prerelease不使已核身份失效；保留既有tag及其固定commit，标签仅描述、不认证构建或板端运行。
- **META-GGUF**：请求3/4的main页与5/6固定页逐件对照：两件同一完整revision、filename、页面SHA256与Xet hash一致，固定页revision一致；完整值从JSON解析，不抄。两件体积字段仍仅1.11GB/819MB，未换算整数B；页面哈希不是本轮对模型文件内容做sha核验。
- **META-W/META-DEP**：逐项目重读所指版本JSON的info.version/requires_python/requires_dist与唯一urls[]轮子；核filename/URL/size/digests.sha256/yanked与目标Python3.12.3、ABI/glibc≤2.39/aarch64或any标签。24区间项另从其项目JSON独立枚举最高稳定、非yanked且目标兼容版本，按合同标签优先级唯一选文件，项目JSON与版本JSON选中文件一致；7固定项版本不变。逐项核最终所有父约束，不仅选择时约束：有后到父边的项目也满足；按目标Linux/aarch64环境与每项激活extra重算有效/排除Requires-Dist边，均与JSON相符，无冲突/截断。只用本机已有pip._vendor.packaging解析文本，不调用pip resolver/dry-run，不安装工具。

下表**接受为条件拟pin**（文件固定身份、URL、sha与字段来源以metadata.json `META-DEP.projects`/`proposed_pins_for_acceptance`为准），不签安装锁或认证完整闭集。来源编号为本批raw请求号；两号项前者项目JSON、后者版本JSON。每项选中文件字段及全部最终约束已核；末列限制仍逐项携带。

| 项目 | 拟pin版本 | 选中轮子整数B | 来源请求号 | Requires-Dist结论 |
|---|---|---|---|---|
| annotated-doc | 0.0.5 | 5302 | 17,18 | UNKNOWN（null） |
| annotated-types | 0.8.0 | 13427 | 46,47 | UNKNOWN（null） |
| anyio | 4.15.1 | 132079 | 31,32 | release级；未逐文件复证 |
| av | 17.1.0 | 33224427 | 7 | UNKNOWN（null） |
| certifi | 2026.7.22 | 136983 | 33,34 | UNKNOWN（null） |
| click | 8.5.0 | 125251 | 21,22 | UNKNOWN（null） |
| cuda-bindings | 13.4.3 | 6488226 | 10,11 | release级；未逐文件复证 |
| cuda-core | 1.2.1 | 6211542 | 12,13 | release级；未逐文件复证 |
| cuda-pathfinder | 1.8.3 | 62561 | 14,15 | UNKNOWN（null） |
| cuda-python | 13.4.1 | 7594 | 8,9 | release级；未逐文件复证 |
| fastapi | 0.139.2 | 130234 | 16 | release级；未逐文件复证 |
| filelock | 4.0.10 | 111193 | 23,24 | UNKNOWN（null） |
| fsspec | 2026.9.0 | 221738 | 25,26 | release级；未逐文件复证 |
| h11 | 0.16.0 | 37515 | 37,38 | UNKNOWN（null） |
| hf-xet | 1.6.0 | 4262538 | 27,28 | release级；未逐文件复证 |
| httpcore | 1.0.9 | 78784 | 35,36 | release级；未逐文件复证 |
| httpx | 0.28.1 | 73517 | 29,30 | release级；未逐文件复证 |
| huggingface-hub | 1.33.0 | 846435 | 19,20 | release级；未逐文件复证 |
| idna | 3.20 | 69583 | 39,40 | release级；未逐文件复证 |
| numpy | 2.2.6 | 14018462 | 41 | UNKNOWN（null） |
| packaging | 26.3 | 129956 | 42,43 | UNKNOWN（null） |
| pydantic | 2.13.5 | 472589 | 44,45 | release级；未逐文件复证 |
| pydantic-core | 2.46.5 | 1951772 | 48 | release级；未逐文件复证 |
| python-multipart | 0.0.32 | 30042 | 49 | UNKNOWN（null） |
| pyyaml | 6.0.3 | 775116 | 50,51 | UNKNOWN（null） |
| starlette | 1.7.0 | 78980 | 52,53 | release级；未逐文件复证 |
| tensorrt-edgellm | 0.11.0 | 447070745 | 54 | release级；未逐文件复证 |
| tqdm | 4.70.1 | 80199 | 55,56 | release级；未逐文件复证 |
| typing-extensions | 4.16.0 | 45571 | 57,58 | UNKNOWN（null） |
| typing-inspection | 0.4.4 | 14750 | 59,60 | release级；未逐文件复证 |
| uvicorn | 0.51.0 | 73219 | 61 | release级；未逐文件复证 |

31件合计**516,980,330B** = W **447,070,745B** + 其他30件 **69,909,585B**（重加各原件size，匹配JSON总和）。这是文件取回成本的已核部分，不是下载授权，不含解压/缓存/构建。W仅激活base+server，server-tools/export/tools/native-build排除；release依赖图无transformers或PyPI tensorrt有效边，系统TRT复用，不据此断言实验性本地首建绝不需要其他包。cuda-python13.4.1及其13.4系列绑定满足已定区间，不由版本约束推定与本板CUDA13.2的新算子兼容；运行时风险仍留给未来具名实测。

**新增只读事实**：31份版本JSON选中文件均有`core-metadata`对象及64位`sha256`。这只是逐文件复证可用的来源线索，本轮未取侧文件，未把其hash与轮子hash混同；原值从各原件urls[]按已选filename解析。据此给§5 B-METADATA-VERIFY的新通道推荐，不借META-BATCH-1 JSON/HTML通道取内容。

#### 3. metadata.md §6三项裁定与合同归因

1. **来源身份可核，完整下载申请不可核**。llama prerelease保持如实记录，固定b11381/commit沿已选合同；源码归档字节/文件名/sha未知，GGUF两件整数B未知，故34件计划无法形成总下载/传输申请。不拿35个asset size或舍入GB、旧500MB/7GB封顶补事实。具名交用户B-FACTS-LLAMA/B-FACTS-GGUF，推荐与需提供字段/理由只见唯一入口§5。
2. **闭集不成立**。13个null为annotated-doc、annotated-types、av、certifi、click、cuda-pathfinder、filelock、h11、numpy、packaging、python-multipart、pyyaml、typing-extensions；不得解释为无依赖。其余18个release级字段也不能证明各选定轮子的METADATA，已遍历图不等于已核文件闭集。需要31件逐文件复证，属新取回维度；§5 B-METADATA-VERIFY推荐以原件core-metadata哈希绑定文本侧文件，或用户提供相同文本。待授权后另写合同，当前维度0；不要求下载全部轮子来核依赖，也不利用本批余额越界。
3. **本批剩余25请求/9项目作废**。接受裁定本批已回交收束，无待执行合规URL：LLAMA/GGUF分额均用尽，已知release图在31项目内遍历完；新逐文件维度不属原闭集。作废避免将剩余当补取内容许可，不需用户再答余额。本机原账/JSON remaining不回写，历史上限/已用保留，本批可继续执行余量=0。未来有新项目、来源变更或新方法须具名另授权，不复活/转用本批。

| 编号 | 追加合同解释 | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 20 | CLARIFY（解释修订18–19、§5）：META-BATCH-1已用61/86、31/40项目按本节核清；剩余25次/9项目作废，只保留执行时账和原件，不再请求。31拟pin仅接受来源/选择与约束；完整闭集及源码/模型精确字节未核，相关执行维度仍0，新的逐文件METADATA通道须用户另签后再落实，不借本批余额。 | artifact: docs/evidence/P1-ENG-JET-001-stageb-metadata.md §1–6、同名JSON requests/META-*、本节§1–3及「阶段B预检答复落实」§5 | K1K3K4 | 2026-10-04 |

归因：解释已授权批次的回交结果与余额处置，新增AC=0；只列条件推荐，不授新额度。阶段B通过线/STOP仍依已确认AC-13修订7与「阶段B答复落实」§2，不以来源元数据替目标条件真实读数。S1/S2 STOP、补丁未上板、SR5/5耗尽、AC-7/8/9 NOT_RUN、R1-5/6 OPEN保持；不消费新verdict、不签DONE，Overall REVIEW_PASSED / Lifecycle ACTIVE保持。下一动作/Owner仅由状态板交接行维护，本轮consumed=none。

open_items: none

### 阶段B核验核清（2026-10-04，CLARIFY）

登记轮次 `阶段B核验核清`；Dispatch-Id `P1-ENG-JET-001-阶段B核验核清-20261004T152721Z-95f6`。Acceptance在Mac mini仅读两项md/JSON与本机原件，不联网取证、不执行原抓取脚本、不解压/列tar、不ssh/上板/跑测试/安装/加载模型。本节是来源与合同裁定，不是C/R轮或独立复核；用户事实与逐维度签发只在「阶段B预检答复落实」§5。本轮consumed=none；两项历史计数不回退/转用、原件不改不删。

#### 1. META-VERIFY：原件与静态声明闭集裁定

从metadata-verify.json `output_dir_repo_relative`定位唯一目录，并与plan/pre_git/requests/analysis交叉，不按最新目录猜选。旧metadata JSON哈希、31件所指版本JSON原件哈希/字节均复算相符；urls[]逐文件唯一匹配pin/filename/size/轮子sha，METADATA期望sha逐项来自core-metadata.sha256。31对start/end的GET号/URL/UTC/状态/完整性/字节/sha与JSON一致，无未闭在途；31/31实体sha符合期望、累计433,453B、最大110,178B、最长0.211s，均在合同限额内，隔离空、跳转/重试/轮子内容0。执行前git凭据与原pre_git一致，实际值仍由原件运行时解析，不抄SHA/目录。

独立离线以标准库email读取31份METADATA、本机已有packaging仅解析PEP440/508；不调用resolver/干跑。按目标Linux/aarch64、CPython3.12.3/glibc2.39生成兼容标签并核全部Name/Version/Requires-Python，目标marker与W base+server显式遍历：31项全部可达，47条非seed声明+8条seed=55条记录、315条排除；按parent/child/约束/extras规范化为54个关系（W→cuda-python基础与server约束相同合并），与旧图54/54一致，故实现md的54是规范化关系数，不是55条记录被漏算。新项目/冲突/未提供extra/未知marker/直接URL/系统TRT有效边均0。13个release null逐文件复证无Requires-Dist；8件文本差异仅规范化写法，不变边集。

**裁定：5件Dynamic可视为本次固定wheel的静态声明，不再构成该闭集的未闭边。** Core Metadata的Dynamic描述sdist→wheel构建间可变字段，不能将其在已建成wheel侧文件中的出现理解为安装时会重新生成依赖；本次对象是固定filename/轮子sha且core-metadata.sha256绑定的wheel METADATA，不是待构建sdist。cuda-python的requires-dist/provides-extra、huggingface-hub的这两项及requires-python均已按实际文本遍历/核满足；certifi/h11/pyyaml仅requires-python且分别≥3.7/≥3.8/≥3.8，均满足目标，无Requires-Dist。记录Dynamic保留，不删字段、不换pin；无需为此新增事实/下载授权。

规范语义参考：[Core Metadata规范Dynamic条款](https://packaging.python.org/en/latest/specifications/core-metadata/#dynamic-multiple-use)及[PEP643](https://peps.python.org/pep-0643/)；本轮遵守禁止网络请求，未访问网页，裁定结合已存文件与wheel/sdist语义，不把这些链接称为本轮新取证。接受结论限为**31件固定轮子的METADATA声明静态闭集已核**；实现JSON的static_file_closure_claimable=false/open_edges5保留为执行时保守快照，由本裁定解释，不回写机器证据。未来取轮子仍须另签、核固定sha/身份；不适用于重新构建、换文件/extra/目标环境，不认证未取回的轮子内容、隐式运行依赖、安装峰值或CUDA/TRT板端兼容。

| 编号 | 追加合同解释 | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 23 | CLARIFY（解释修订21「动态元数据留未闭边」；来源：实现metadata-verify.md §3–4交接受裁定）：本节31件固定wheel及既定目标/extra下，哈希绑定METADATA的Dynamic不表示安装时重新构建或变更字段；按实际Requires-Dist/Requires-Python/Provides-Extra核静态闭集，5件已核，不推广到sdist/换pin/构建/新extra。原JSON未闭标记保留为执行快照，不改变用户额度或安装/运行验收条件。 | artifact: docs/evidence/P1-ENG-JET-001-stageb-metadata-verify.md §3–4、同名JSON objects/closure_rejudge、原plan/analysis及本节§1 | K1K3K4 | 2026-10-04 |

#### 2. SRC-ARCHIVE：绑定、字节与缺字段影响

从source-archive.json解析目录、文件与fixed_commit；复算旧metadata JSON及两份release原件哈希/字节，与记录一致。release JSON tag=b11381/target_commitish与release页唯一完整commit链接及已核fixed_commit一致；请求账恰1对attempt-start/end、2对GET-start/end，与JSON requests一致。首GET为该完整commit的API URL，302正文0B，Location严格等于允许的同commit codeload legacy.tar.gz；只跟一次，第二GET200/完整/identity、无再跳转。归档只读流式复算为**37,831,966B**，sha256与streamed/落盘/JSON一致、gzip魔数一致；未解压/列tar或内部验commit，不执行源码。GET2/2与尝试1/1已用尽，字节小于500,000,000B保护上限。

**B-FACTS-LLAMA已核**，只认证“GitHub对本次已核固定commit返回的保留归档”的链与字节/sha；不是远端公布校验和、不是内部独立commit认证，自动归档可能随时间变，后续只复用同sha副本。Content-Disposition未捕获（header不存在或大小写过滤原因UNKNOWN）不影响已完整实体的实测B/sha、URL/Location完整commit链；仅不能声称远端建议文件名或短commit头已核，无须为辅助字段重取/另探端点。原文件名与sha由JSON运行时解析，不能按header重命名或额外下载。

源码已取回，新增下载不再计源码：31轮子516,980,330B+GGUF2件=33件，总B UNKNOWN；源码+轮子作为后续单程输入32件/554,812,296B，两端各一份压缩输入1,109,624,592B只是条件输入占用，不含GGUF/解压/构建/代码/数据/日志峰值。上述可算具名推荐与仍未核维度逐项列§5，全部生效0；本次核验许可禁止源码作他用，后续复用/构建/传板仍需用户另签，不以已下载追认使用。

#### 3. 执行方法偏差与交接边界

实现finished报告（supervisor-dispatch.jsonl中`阶段B核验执行`的同Dispatch-Id记录）自报一次`python3 -c 1`空操作：不在合同§4仅目录脚本调用的允许写法内，**记为实现执行方法错误/合同不遵从1次**；不是合规调用，未被分类器拒绝也不使之获得授权。无网络/写入是实现自报、不是本轮动态监控结论；没有拒绝后绕行的报告，也无证据显示它参与GET/解析/写原件，原件链独立核齐，因此不据此作废两项事实、退回取证或新增资源计次。不冒签复核finding/RED_LINE，不给任何新通道许可；无需另问追认，偏差记录保留供用户知悉，未来仍遵守目录脚本写法、遇拒绝即停。

本轮仅追加AC-10修订23解释实现具名疑问，新AC=0；不签额、不代写用户账本、不消费新verdict。S1/S2 STOP、SR5/5耗尽、补丁未上板、AC-7/8/9 NOT_RUN、R1-5/6 OPEN与Overall REVIEW_PASSED / Lifecycle ACTIVE保持，不签DONE。交用户仅剩GGUF两件整数B及出处、§5逐维度决定；未知/依赖未核项仍0，云未答且范围外。§5是唯一needs_user入口，本节不另起待答清单。

open_items: none

### 阶段B核验授权落实（2026-10-04，CLARIFY）

登记轮次 `阶段B核验授权落实`；Dispatch-Id `P1-ENG-JET-001-阶段B核验授权落实-20261004T145803Z-acce`。依据 `docs/authorizations.md`「2026-10-04 P1-ENG-JET-001 — 用户签 B-METADATA-VERIFY（按推荐）并授权在 Mac mini 下载 1 次 llama.cpp b11381 源码归档用于核验；GGUF 精确字节由用户稍后提供（supervisor 会话代录）」(a)–(e)，承接「阶段B元数据核清」及「阶段B预检答复落实」§5。本节只把用户已签额度落实成执行合同；不是接受侧签额、C轮或独立复核。本轮只读本机资料并修改文档，未发核验网络请求、未下载/运行抓取脚本/ssh/上板/测试/安装/加载模型/租云。

#### 1. 追加 AC 修订与归因

| 编号 | 验收项（可证伪） | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-10 修订 21 | CLARIFY（解释修订17–20、§5；META-VERIFY）：Implementation仅在Mac mini按本节§2/4取31件选定轮子METADATA侧文件；GET≤31、每件≤1,048,576 B、正文累计≤32,505,856 B、单请求全程≤30 s、跳转/重试/轮子内容0；原件core-metadata.sha256绑定，失败/超限/不符停该对象记UNKNOWN。离线重判闭集，新增项目不追查，写needs_user后交接受核清。 | artifact: 上述账本(a)(e)、本节§2/4；未来docs/evidence/P1-ENG-JET-001-stageb-metadata-verify.json/.md | K1K3K4 | 2026-10-04 |
| AC-10 修订 22 | CLARIFY（解释修订14/17/20、§5；SRC-ARCHIVE）：Implementation仅在Mac mini按本节§3/4下载与已核b11381固定commit绑定的唯一主源码tar.gz 1次、重试0、≤500,000,000 B；只算实际完整字节与sha256，最多一次同commit的GitHub→codeload跳转。未完成/绑定不符即UNKNOWN，不解压/构建/传板/作他用。 | artifact: 上述账本(b)(d)(e)、本节§3/4；未来docs/evidence/P1-ENG-JET-001-stageb-source-archive.json/.md | K1K3K4 | 2026-10-04 |

归因：两项均为用户本次授权对既有取回/核清条款的有界解释，AC修订2、新AC=0；不是核对读码新增义务。META-BATCH-1已用61/86及作废25次/9项目不变，不挪余额、不归零；以下两项独立计账。S1/S2 STOP、SR5/5耗尽、补丁未上板、AC-7/8/9 NOT_RUN、R1-5/6 OPEN保持；Overall REVIEW_PASSED / Lifecycle ACTIVE仍只覆盖A候选，不签DONE、不宣称B或Jetson运行通过。

#### 2. META-VERIFY 执行合同

- **角色/机器/对象**：Implementation，Mac mini；闭集严格为 `docs/evidence/P1-ENG-JET-001-stageb-metadata.json` 的 `META-DEP.projects` 中31件既选轮子，与 `proposed_pins_for_acceptance` 逐项一致。使用 `version_json_request_n` 沿该JSON requests及 `output_dir_repo_relative` 定位本机已存版本JSON原件，再按选定filename在urls[]唯一匹配；核project/version/filename/URL/轮子sha与既有记录一致，期望METADATA哈希只取该项 `core-metadata.sha256`，不拿轮子 `digests.sha256` 代替。缺项/歧义/原件绑定不符在发请求前记UNKNOWN，停该对象，不再查询PyPI。
- **URL与跳转裁定**：从上述选中文件的完整URL逐字追加 `.metadata`，仅允许HTTPS、host严格为 `files.pythonhosted.org`、无账号密码/非标准端口；先离线列出31个互异URL及其期望sha，禁止猜轮子名/换源/换版本。**跳转0**，禁自动follow；3xx保存状态/Location但不访问，停该对象记UNKNOWN。依据为账本(a)按推荐签发、其语境明确跳转0；文件URL已精确固定，没有绕去第二来源的必要，也不以跳转暗增GET。
- **计次/限额**：最多31次实际GET，每对象一次；发出前原子登记start及该对象占用1次，4xx/5xx/超时/断网/质询/sha不符亦计，重试0，不作HEAD/Range/连通性探测/预取/子资源/新端点。单请求从发出至正文关闭全程≤30 s（含连接、TLS、首字节与流式读取，不是仅socket空闲超时）。响应按原始实体字节保存/计数/sha，要求identity、不自动解压HTTP内容；每件≤1 MiB=1,048,576 B、全批响应正文累计≤31 MiB=32,505,856 B，含失败/部分响应，不只计成功。读取前按对象及累计剩余限额约束缓冲；Content-Length只作提前拒收线，不替代实测字节。超限立即关闭该对象响应，停止取该对象、计已收字节，正文/结论记UNKNOWN；累计额度耗尽则全批停止，未取对象UNKNOWN，不以中止免计或重新运行重取。
- **失败处置**：HTTP非200、正文不完整/异常编码、超时、大小超限、sha256不符、质询均停该对象、原件隔离且不用于依赖判定；可继续尚未失败且未计次的独立既定对象，不能替换失败对象。权限分类器或沙箱拒绝按§4停止整个派发，不切通道；已计对象不能在同次或新会话补取。
- **离线闭集重判**：只解析成功且sha匹配的31份原始METADATA，核Name/Version/Requires-Python身份，保存全部Requires-Dist原文及激活/排除边。按既有种子、W base+server、有效边显式传递extra及metadata.json目标marker_env（Linux/aarch64、CPython3.12.3、glibc2.39）重遍历；禁用Mac默认marker，platform_release/version等未知条件仍UNKNOWN。哈希及身份均通过的完整METADATA无Requires-Dist才可当该文件无依赖，不能把旧release null当无依赖。保持31个既定pin，逐有效边核版本约束/extra/文件兼容性；原件差异、冲突、未知marker或动态元数据留未闭边，不回溯换pin、不调用pip resolver/干跑、不安装解析器（只用本机已有离线能力，缺工具即停解析）。出现新项目不再网络追查；新增extra超出既核图/冲突等影响范围时也写needs_user，推荐另授权具名对象元数据核清，理由为本信封只含31个固定侧文件。只有全部必要文件/有效边静态核齐才能提出闭集结论，结果仍交Acceptance核清，不自授安装/下载/运行许可。
- **落点/证据**：运行时独占创建 `outputs/eng-jet/P1-ENG-JET-001/stageb-metadata-verify-<UTC>/`，已有即停；只放本次脚本、raw侧文件、请求账及离线解析输出。新增 `docs/evidence/P1-ENG-JET-001-stageb-metadata-verify.json` 记录对象映射、输入原件绑定、URL/期望与实际sha、实际字节/累计/UTC/状态/UNKNOWN、start/end/未发出/未闭在途、目标环境与逐边重判；同名 `.md` 指向机器生成目录/原件/JSON，分列已核、未核、差异与needs_user。实际目录名/sha运行时生成，不手抄到合同；不覆盖旧metadata.json/.md或原账/原件。此项轮子内容下载0。

#### 3. SRC-ARCHIVE 执行合同

- **角色/机器/对象**：Implementation，Mac mini；仅 `ggml-org/llama.cpp` b11381已核唯一主源码tar.gz，非35个release资产/zip/Edge源码/子模块。从原metadata.json `META-LLAMA.fixed_commit` 运行时读取完整40位commit，与原release JSON target_commitish及release页唯一commit链接离线交叉一致；不手抄SHA、不联网刷新tag/release。
- **使用URL及绑定**：原JSON的 `https://api.github.com/repos/ggml-org/llama.cpp/tarball/b11381` 会跳转到 `codeload.github.com`，但tag可移动且本授权禁止为绑定另查来源，因此**实际请求**固定为 `https://api.github.com/repos/ggml-org/llama.cpp/tarball/<fixed_commit>`（仅以已核commit替换末段b11381，不请求tag URL）。禁自动follow；只允许首响应一次3xx（301/302/303/307/308）且Location精确为 `https://codeload.github.com/ggml-org/llama.cpp/legacy.tar.gz/<fixed_commit>` 或 `https://codeload.github.com/ggml-org/llama.cpp/tar.gz/<fixed_commit>`，无query/fragment/账号密码/非标准端口。校验后只发该目标一次GET，必须200且不再跳转；Location缺失/不符、另一commit或域名、第二次跳转即停记UNKNOWN。初始API若直接200，仅在同一固定commit请求下记录其无跳转事实，不另访问codeload。
- **跳转依据/限额语义**：账本(b)明确交接受落实跳转；采用GitHub官方归档服务同仓库同commit的单跳，只解决该一次下载的交付，不追第二对象。**下载尝试≤1（从首GET发出前登记1/1，包括失败），HTTP最多2次GET（初始API≤1、通过Location校验的codeload≤1），重试0**；无HEAD/Range/备用URL/请求release/commit/tag等补查。META-VERIFY的31次GET不借给本项，旧批余额不用。权限拒绝/失败不归零、不改成直接codeload再试。
- **字节与sha**：500 MB按十进制解释为500,000,000 B保护上限，不是已核归档大小；各响应实际正文（含失败/中止）累计也不得突破该值。流式落盘，禁止整件读入内存；identity、无HTTP自动解码，仅对完整tar.gz响应实体计算整数B及sha256，不解压、列tar、执行源码或构建。Content-Length/Content-Disposition仅记作辅助字段，不冒充完整实际字节/哈希；超限立即关闭并中止、留实际已收计账，完整文件精确B/sha记UNKNOWN。网络/HTTP错误、质询、截断、磁盘不足或绑定缺失亦停，无重试；本机前提/权限拒绝按§4停整个派发。
- **绑定凭据及主张上限**：机读证据记录原tag→fixed_commit的两份来源指针及原件哈希、实际commit URL、3xx/Location/最终URL、响应状态与取得UTC、完整实体字节/sha。这条链将所得sha绑定到“GitHub对已核固定commit返回的归档”；不是从归档内部独立验commit、不是远端公布sha认证，自动生成归档字节可能变，未来只复用本次保留的同sha副本，不声称任何b11381归档都同sha。绑定链失败则不得报已核归档身份，更不以Content-Disposition短SHA代替固定commit。
- **落点/保留/清理**：独占创建 `outputs/eng-jet/P1-ENG-JET-001/stageb-source-archive-<UTC>/`；脚本、请求账、HTTP头、`.part`及唯一完整 `archive.tar.gz` 仅在此目录。响应建议文件名仅记录到机读证据，不能按任意header路径写盘；成功完整体核完后原子改名，保留一份归档，不复制到repo/数据根/板/云，不解压。失败部分文件隔离，先记字节/sha/错误，接受核清前保留、不自动删；以后清理只能针对本次自有目录并先保留证据/记清理事实，不动旧原件或缓存，若删除完整归档需重新取回也必须另授权。新增 `docs/evidence/P1-ENG-JET-001-stageb-source-archive.json` 和同名 `.md`：前者机器生成绑定链、实际目录/文件名/字节/sha、逐请求与尝试账、失败/UNKNOWN/保留清理状态；后者只写指针与读数边界。不回写旧metadata.json的UNKNOWN快照；源事实核清后未来预算从这次原件运行时取，不能重取当未消费。

#### 4. 本机执行前提、回交与现行用户入口

两项都必须保持会话沙箱启用；脚本仅写在各自新输出目录，**仅以 `python3 <目录>/<脚本>.py` 运行**，不得改用内联抓取、curl、WebFetch、关沙箱或设置绕行。本机网络前提按账本(e)：用户本人先在Mac mini沙箱放行 `files.pythonhosted.org` 与 `codeload.github.com`；本轮未核其已放行，不能以普通网络可达或旧四域名放行推定就绪，未放行时执行会被拒、即停。API源域名沿已有放行，不为探连通性额外GET；输出目录python3调用若被分类器拒绝也立即停并记原错误，不代改用户设置、不换会话重试。先做本机离线源/额度/放行与目录前提检查；缺条件先回交，不以执行探测放行。共享槽位空闲后按单写者串行执行两项，首项权限拒绝后不得启动第二项。执行前保存git状态凭据到本次证据，不手抄HEAD到合同。

两项都不创建/消耗scenario/session/run ID、Play或模型API预算，输出UTC目录不是正式ID；依据轨道定义及先前元数据裁定，交接仍Consuming=no，用户具名HTTP/字节限额仍逐项计账，不意味着免费下载。只准这两项新维度；其余下载（GGUF/轮子内容等）、安装、板构建/传输/部署、上板、模型/回放/测试/SR/加工/评分/云全部0。不在Mac执行量化或源码他用，不替代engineering§9板端运行实测；阶段B闭集/来源事实完成或失败即交Acceptance核清，不能自行进入下一步或签DONE。

用户事实/额度唯一入口仍为「阶段B预检答复落实」§5：B-METADATA-VERIFY/B-FACTS-LLAMA现为用户已签、执行待本机放行且结果未核；B-FACTS-GGUF按用户选择“稍后自己提供”，不改成新端点查询。该入口新增B-LOCAL-ALLOW前提：推荐用户本人添加上述两域名放行，理由为账本(e)所列沙箱限制；不向用户重问已签两项或已答路线，不替用户提供GGUF数值。本轮consumed=none，无新硬件/测试/复核证据。

open_items: none

### 阶段B准备审核（2026-10-04，CLARIFY）

登记轮次 `阶段B准备审核`；Dispatch-Id `P1-ENG-JET-001-阶段B准备审核-20261004T050903Z-a01a`；Acceptance，本轮仅合同解释、准备稿审核与本项状态指针。**结论：保留可证部分，退回构思补写 BP-1…5，再交接受核清后交用户；尚非可执行闭集。** 本轮不是 D/C/R 轮，不重开 D2，不改变已接受设计与阶段 A verdict；Overall `REVIEW_PASSED` / Lifecycle `ACTIVE` 保持。阶段 B 全部生效值仍 0；S1/S2 `STOP`、补丁未上板、SR 5/5 耗尽、R1-5/6 OPEN 保持，不签 DONE、不代用户答复或记账。

#### 1. 审核依据与边界

对照「阶段B答复落实」§2–4 及 §3 五条标准，读本项 AC、准备稿、设计 §8、engineering §9、工程继承清单、SFT-002/LOOP-001 parked 入口与 SFT-002 复核 F7/F8。已有分机直接清单、环境快照、资产来源、候选消费表与云预算债计划；传递闭集、固定 tag 的构建/服务/校准入口仍缺，约36个直接条目不等于安装闭集。

本轮另只读官方 release 与固定 tag 的源码文本：

- [llama.cpp b11381 release](https://github.com/ggml-org/llama.cpp/releases/tag/b11381)（官方列表显示2026-10-03）；[顶层 CMake](https://raw.githubusercontent.com/ggml-org/llama.cpp/b11381/CMakeLists.txt)、[ggml CMake](https://raw.githubusercontent.com/ggml-org/llama.cpp/b11381/ggml/CMakeLists.txt)、[CUDA CMake](https://raw.githubusercontent.com/ggml-org/llama.cpp/b11381/ggml/src/ggml-cuda/CMakeLists.txt)：NO_VMM有效，CUDA子目录最低CMake 3.18；顶层HTTPS选项为LLAMA_OPENSSL，无LLAMA_CURL定义。构建可能由CCCL/预建UI入口外联，须关闭或列闭集。
- [Edge-LLM v0.11.0 release](https://github.com/NVIDIA/TensorRT-Edge-LLM/releases/tag/v0.11.0)（2026-09-29）；固定tag的.gitmodules/pyproject.toml及服务页文本读取未成功，不据latest/main声称依赖/子模块/服务/Orin支持已核。

未取回模型/源码归档/轮子，未做HEAD/Range GET/HF API/pip解析/干跑、ssh/RP-1、安装/编译/租云/登录/模型/回放/SR/实现测试；仅收工自检。公开文本属出处(3)，非板端兼容性实证；不抄可派生SHA。

#### 2. 接受侧合同解释（追加 AC 修订）

固定准备稿 #### 9 的接受侧事项；路径选择不签额度，事实未核继续阻塞。原条款不覆盖、不删除。五条修订均解释既有条款，来源是本次用户指定的审核及构思 #### 9 请求；新增AC=0，非核对轮读码新增义务。

| 编号 | 现行解释与归因 | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-7 修订 2 | CLARIFY（解释AC-7、§2.1 S3、§3.3）：llama.cpp固定b11381，板/云转换同tag；Edge固定v0.11.0，不随main/latest滚动。3b CUDA arch=87、Release、GGML_CUDA_NO_VMM=ON固定，不作开关A/B试跑、不声称已修JP7.2崩溃。LLAMA_CURL=OFF不进本tag命令（未定义）；固定LLAMA_OPENSSL=OFF、LLAMA_BUILD_UI=OFF、LLAMA_USE_PREBUILT_UI=OFF、GGML_CUDA_CCCL_VERSION为空，复用系统CUDA；其余隐式下载由BP-2核清。只用本地模型路径、服务仅loopback、禁hub/URL自动取模型；HTTPS关闭不等于全部禁网。3c选独立 ~/eng-jet/edgellm-venv 的v0.11.0常驻实验性Python server，消费本地板建LLM/视觉组件，不往sysvenv装其numpy，不逐请求起llm_inference。分发/绑定、本地加载、文本及视觉缓存关闭实际入口须BP-2核清，不可自行换服务/容器；每路径在加载/预热前启动，加载/冷启动单列，不逐请求重载。token=300、prompt/解析/max_tokens=160/temperature=0保持。 | artifact: 本节§1/4、准备稿####1/9；未来同名-vlm.json | K1K3K4 | 2026-10-04 |
| AC-10 修订 14 | CLARIFY（解释修订13、§5、§3.3）：取回形式为版本化主源码归档+必需子模块/外部构建输入逐条归档清单，每项运行时解析tag/gitlink，来源/字节/sha分列，不把多个取回藏成一条。禁板/云构建时自动submodule/FetchContent/补包下载；签后按清单预取、核验、离线构建。取回机器仍B-DLLOC待用户。云合并固定venv-merge、现有requirements-eng-sft pin的merge_and_unload，不用Edge merge-lora；GGUF/AWQ各隔离，以固定tag依赖为准，ABI/CUDA变体未知不补装。云控制选tools/eng_jet/另写本项最小入口，不调用/复制带债SFT runner；借鉴模式须覆盖F7负值拒绝与F8收据并发/原子写入风险，只验证新入口、不修或销SFT债。板/云pip均固定闭集逐包--no-deps取回核sha、离线按文件安装，不以未知环境先真实解析安装发现闭集；全部机器失败/重取字节与包/源码数累计计账，上限不自扩，推荐修正见§3。 | artifact: 本节§3/4、准备稿####2/8；未来同名-ledger.json | K1K3K4 | 2026-10-04 |
| AC-11 修订 2 | CLARIFY（解释AC-11、§3.3，关联AC-12）：C2 Q4_K_M不用imatrix、不建该类校准；官方配方未知披露，不称同量化处理。C2 mmproj默认由合并产物按同tag自产F16，不直接复用官方件；若拟复用，须已签云操作内核合并前后视觉/投影张量、处理器/转换规格一致性及完整来源后回接受，不能由target_modules推定字节相同。自产件列体积/峰值/传输，不算外部模型下载；官方件用于官方base，各自绑定来源/sha，.cache/AppleDouble/gold排除。归因为原资产身份与自产产物核验解释。 | artifact: 准备稿####5/6、本节§4；未来同名-assets.json | K1K3K4 | 2026-10-04 |
| AC-8 修订 2 | CLARIFY（解释修订1、§2.1 S4）：S4-a基准仍B-S4A待用户，609份额0。若选SFT作业A，官方base只对该base bf16，先核逐行身份/prompt/grid/解析一致性；G5取该基准原计数，不用C2的21/100。差值含运行时/转换/量化条件，不能单独隔离合并、转换或量化误差，不作因果分解。AWQ划分/样本数/序列长未定，不把未知工具缺省当合同，评估/gold/smoke不回流。 | artifact: 准备稿####5/6、本节§5；未来同名-quant-equivalence.json | K1K3K4 | 2026-10-04 |
| AC-14 修订 2 | CLARIFY（解释修订1、§7.1）：B1消费前代码/B2消费后证据停点保持；B1含本项服务、资产隔离、量化作业控制、固定依赖/预算守卫、SUB:6保留及评分。代码仍tools/eng_jet/和tests/test_eng_jet_*.py，不加SFT runner修债。新测试用替身不豁免既有全套加载/回放计数；四项自证→C→独立R不替用户签消费，全套有本项具名信封，B2候选须对应证据，A例外/轮号不延长。未核依赖/实际候选不预签可跑或自证成立。 | artifact: 准备稿####7/8、本节§3–5；未来同名-K1K3K4-handoff.md | K1K3K4 | 2026-10-04 |

#### 3. 原 §4 推荐值的适用性修正（仅建议，生效全0）

追加替代「阶段B答复落实」§4以下行的未来推荐读法，旧值留作来源；其余仍是未核估算封顶，不因此可签。U9产物体积/U13实际兼容只能执行才知：在来源、环境与逐步封顶合同核清后可作有界尝试，不要求成功实测先存在；超额预测或实际不兼容仍先停，不以未知为由先授额。

| 原行 | 本轮推荐修正 / 待核 |
|---|---|
| 板pip≤6包/≤1 GB | W路线固定直接8项（不装server-tools），尚不含传递；旧6包已不相容。aarch64实际字节UNKNOWN，官方size_budget压缩≤2,684,354,560 B/解压≤5,100,273,664 B仅包装上限，不是实际字节；仅该轮子的公开包装上限已超1GB、实际值仍UNKNOWN，旧1GB无法证明容得下，撤下旧1GB，不以x86资格轮子替代aarch64。B-CLOUDDEP供固定平台版本/元数据后重算，当前不报新总额度。 |
| 源码≤2归档/≤500 MB | 按AC-7修订3选W，Edge主源码/子模块/构建隔离不取回；llama板/云同tag复用1份版本归档，源码实际字节/未读外联分支仍UNKNOWN，不将500MB认成已核。3b仍需预检cmake/gcc；云还需CPU llama-quantize工具链。Mac取回/磁盘/到板传输单列。 |
| 云≤20 GB/≤12包/≤3 GB | 旧12包/3GB撤下。原三venv直接36项，采用树内gguf-py后减1个pip直接项；不把该算术数当传递闭集/新增安装数。x86 Edge资格压缩2,067,563,217 B/解压3,969,749,991 B、base本机4,266,647,442 B只是已知部分；torch/CUDA轮子与三venv/合并bf16/GGUF中间件/AWQ/临时件未齐。服务路线不导ONNX；20GB未证足够，不扩大估算。B-CLOUD/B-CLOUDDEP原读数及逐文件元数据回来后重算。 |
| 传输两维/板盘/Mac中转/16 h | W轮子压缩件+解压venv、官方/C2各两GGUF件、AWQ检查点、板内首建LLM/visual及引擎缓存/临时件均须计峰值；缓存默认50GiB不可直接沿用，按已签板盘份额显式封顶。云上传base+adapter+128帧派生校准约6MB，回传C2 GGUF/mmproj+AWQ/日志，不回传合并bf16/中间件且云不导ONNX；云↔Mac≈6.2GB+AWQ仅估。两向传输/板盘40GB/Mac12GB/墙钟16h仍未证可容，不申请；首建在板墙钟内，云校准前向在GPU·h内。 |
| 全套与伴随模型/回放 | 静态推荐B1/B2至多2候选，各全套1次；每候选CPU det-assoc≤2加载、NanoTrack≤2尝试/读权重0、CSRT≤2尝试/实例0、零模型回放≤2×60帧、墙钟≤15 min、outputs增量<0.1 MB。两候选合计全套≤2、det-assoc≤4、两类构造各≤4、回放≤4×60帧、墙钟≤30 min、增量<0.2 MB；各候选不可借超额。VLM/YOLOE/DINOv2/MPS/新增模型下载均0。冻结后按实际树/环境只读核可达计数，相异先回用户，不自动继承skip。B-EXC另裁；focused/红绿真实消费也不豁免，当前推荐0，有具体需要另申请。 |

B-CLOUDDEP(a)在未知镜像先真实解析安装再freeze，与engineering§9及原逐包安装纪律不相容，本轮不推荐、不放行。推荐(b)先固定tag/镜像元数据的静态闭集。确需云原读数，按§9设备暂不可达通道单列“租后第一步只读预检”，报价后只申请可封顶的先导子范围，不捆绑未知pip/AWQ/转换；须用户另签，计入同项总封顶和消耗轨道。云预检不导入模型/写缓存/安装；镜像不符停下保留错误，由用户销毁实例。当前没有先导额度。

#### 4. 准备稿差异与构思补写闭集

U1–U13保留UNKNOWN/对应0维度；本轮仅部分闭合U3/U4的tag及U3开关。下一构思仅读本机既有文本/公开官方文档源码文本，不ssh/上板、不取回归档/模型/轮子、不解析安装/租云/查询、不写代码测试工具/AC/账本。在原准备节追加逐项来源/答复，不覆盖本裁定；新待用户事实只汇入§5，不另建并列清单。

| ID | 必须补写的差异 | 对应未知/前置 |
|---|---|---|
| BP-1 | RP-1现命令不可执行：5 min只有文字，无全程超时/取消/远端存活收尾；ip -br addr不核外网路由；sysvenv import numpy会执行site/.pth，PYTHONDONTWRITEBYTECODE不保证无其他缓存/模型加载。给一份完整可审阅命令：普通用户无sudo/交互/下载、全程≤300 s与命令级超时、超时停止/不重试并保留原始输出与返回码；补只读路由，解释器用禁止site初始化的标准库读数，numpy优先读既有dist-info/归档pip文本，不import包/TRT/torch；列Mac/板机器、输出路径。SSH仍BatchMode/StrictHostKeyChecking，不改键/配置，不把历史存键当新额度。SSH/PAM/日志及已知wireplumber写入是附带副作用，必须在B-PRECHECK明示，不声称板端绝对零写；IR-18仅历史披露，不授权未来登录。缺读数/权限记UNKNOWN，不sudo兜底。 | U1/U2/链路；B-PRECHECK前置 |
| BP-2 | 按固定tag补直接/传递pin、子模块/gitlink、构建输入/隐式外联与离线组装；未知及0继续保留，不用main/master表代替。列Edge server真实CLI/绑定入口、aarch64/cp312分发与系统TRT绑定、本地板建LLM/ViT加载、文本/视觉缓存关闭、token读数出口；所选server不支持则具名回接受，不换逐请求CLI。补Orin arch/视觉建引擎命令，不把ENABLE_CUTE_DSL=ALL/教程当固定tag已核。同步llama构建/转换要求及CURL弃用；tag文本不可取列路径/UNKNOWN，不下载源码补缺。 | U3/U4/U5；板pip/源码/3c |
| BP-3 | 固定tag依赖与镜像事实分开，按三venv逐包列平台/来源/已装或新增/传递闭集；镜像等B-CLOUD提供，未知受影响行0。重算12包/3 GB/20 GB推荐，补先导只读云预检完整命令、报价封顶/销毁责任；真实安装不能替代装前环境核验。 | U6/U7；云租用/依赖 |
| BP-4 | 核固定tag AWQ校准字段/工具样本数与序列长，列train确定性选择规则及按SFT报告排除eval/select-eval/smoke的frame_sha/近重复泄漏约束供用户定，不实际采样/下载。本域(a)意味着train帧+surface到云：原“云端零评估/smoke/gold数据”保持，另列仅用户选(a)并签传输才可传的train派生清单；原“云上无推理”须区分无正式评估推理与AWQ校准前向计算。评估/smoke/gold永不传云。官方GGUF文件名/公开LFS字节身份须下载申请前固定，不按U8先签再读来源；公开元数据不可取则用户提供，不用HF API/HEAD/Range GET。补自产mmproj、双向传输和临时/保留件峰值、FP16视觉塔校准/导出需要，不由名称推定。 | U8/U9/U10/U11；校准/模型/传输 |
| BP-5 | 候选消费表对齐B1/B2范围和§3合计；列新云入口F7/F8风险的真正执行focused回归、SUB:6保留与两项例外确切来源，不加SFT修债。新测试替身≠全套零加载；冻结后跑前核查实际树/可达次数。U12未冻结继续UNKNOWN，U13只待实测，实际不兼容/需系统变更即停、系统0，不要求预先证明性能。 | U12/U13；B1/EXC/SIGN |

以上都是零消耗材料补写，不要求构思现在核掉不可达设备UNKNOWN。材料齐且仅剩需用户事实/授权的UNKNOWN即可交用户，不以“所有U先成功实测”阻断engineering§9的第一步预检通道。

#### 5. needs_user（阶段B准备审核，现行唯一用户待决入口）

合并准备稿####10八项与前次B-SIGN/B-PRESSURE/B-LINES及14个B-STOP-*，原两清单仅历史来源；B:1–8已答复，不重问。本表尚无答复，推荐不是授权；BP-1…5经「阶段B补写核清」§1/3勘误已闭合静态材料义务，现交用户；下一Owner只在状态板。先后：B-PRECHECK/环境事实→缺包时B-APT及B-DLLOC/B-CLOUD/B-CLOUDDEP/B-CALIB/B-S4A/B-CACHE→固定依赖/预算→B-SIGN+B-EXC+B-LINES/STOP确认→B1 C/R通过→已签消费。先导云预检按§3独立申请，不等于整个B；租云仍等待FRAME自身释放轨道。方向可先答，未知维度不签，生效值全0。

| needs_user | 推荐项与理由 | 依赖 |
|---|---|---|
| B-PRECHECK | 推荐明确授权一次Mac mini→Jetson有线只读预检≤300s，唯一命令为「阶段B补写核清」§3 board版；无重试/sudo/安装/下载/模型，Mac唯一落盘，明示接受SSH/PAM/日志及wireplumber附带写入；或用户本机代读同组只读读数。理由：engineering§9先核工具/系统TRT绑定/余量，历史存键不构成新登录额度。 | 「阶段B补写核清」§3；板相关签前 |
| B-APT | 推荐更正版预检确证缺项后用户本人只装具名必需缺包并反馈原读数/版本；W不需Edge CMake/子模块/TRT dev构建，3b仍需cmake/build-essential、W仍需系统TRT Python绑定/venv。理由：不按P8整串升级CUDA/TRT；代理sudo/apt0，缺读数不推定要安装。 | 更正版预检；缺项才给具体操作 |
| B-DLLOC | 推荐Mac mini取回llama同tag归档1、官方GGUF两件及板W轮子/传递包，核身份后有线传板；W无Edge源码/子模块取回。理由：板不依赖外网/git。签下载前须固定官方文件页来源/身份与精确字节（公开页只给舍入值，缺失由用户提供）；W各平台文件元数据见B-CLOUDDEP。Mac下载/占用与到板双向另列，未核不签、不得签后取回探大小。 | BP-2/4、U3/U8/B-CLOUDDEP；下载签前 |
| B-CLOUD | 推荐用户提供x86 GPU≥24GB精确镜像标识、OS/glibc/Python ABI/驱动CUDA/预装、存储流量全价与可信SSH目标/端口/已核指纹文件；我方不登录控制台。租前无原读数仅考虑「阶段B补写核清」§3 cloud版先导（≤600s无重试）；报价后单独确认≤0.5h计费形状、GPU·h/总费/具体销毁UTC与用户责任，计入本项≤2GPU·h/≤4美元总封顶建议，未知安装不捆签。理由：镜像标签不证依赖，未签主案/不符即销毁；须等待FRAME释放轨道。 | BP-3/核清§3；报价、指纹、销毁UTC与轨道 |
| B-CLOUDDEP | 推荐原(b)：先用户提供固定ABI/版本的包文件名/平台标签/Requires-Dist/精确字节与来源（板W和三云venv均含），或具名无质询的官方公开文本来源，接受核清后按平台标记静态闭集。理由：网页质询不绕过、不改取PyPI JSON；范围pin须先落具体版本，原(a)先安装发现闭集不推荐。旧6包/1GB及12包/3GB均撤下；用户若选规则例外须另明确有界范围，不据“按推荐”放行。 | JB-6；B-CLOUD ABI/板cp312-glibc；安装签前 |
| B-CALIB | 推荐本域train派生128张、batch1、无截断、固定tag Python API本地(image,question)生成器；按####11 BP-4的sha去重/最小sample_id及固定排序选取，排除eval/select-eval/smoke（25张全在train）及a7预热/前320帧。另建议在Mac按既有近重复原子组排除与保护集相连的组；无组关系时以同family/station_key且frame_index距任一保护帧≤30的明确代理排除，缺字段/不足128回用户，不偷补保护帧、不声称近重复已完全隔离。须用户明确选择该采样/排除规则；帧+剥字段清单约6MB仅估，核真实字节后另签train到云，校准前向计GPU·h。理由：不新增外部下载、smoke不是校准；旧sha不交证明不能代替近重复约束，结果只称本域校准AWQ。 | BP-4/AC-8修订3；用户定采样/排除与传输 |
| B-S4A | 推荐复用已复核SFT作业A609行base bf16原预测，运行时由zero-shot-v2/eval摘要核身份、prompt/grid/解析；理由：零新基准推理。披露5090 HF与板端运行时/转换/量化的混合差异；跳过则609份额0，另跑另签。 | BP-4；S4-a签前 |
| B-EXC | 推荐随B1/B2各具名重新沿用Carrier CPU失败/9处未知/后置断言未执行与scene006新增29条缺权重静态归因，仅原同名同类；三条原授权的确切来源见####11 BP-5。理由：旧例外不延长、不把失败当通过，其他新增失败阻断，复核仍可阻断。 | BP-5来源；同B-SIGN |
| B-CACHE | 推荐保持v0.11.0服务端并由用户具名接受视觉编码缓存例外：文本KV仍关；S3/S5每个计时段前重启该常驻服务清空视觉缓存，启动/加载单列且计额度，随后每段只加载一次。首见25/共驻180互异帧单图请求不得有命中INFO，原始INFO逐请求绑定；7重复行单列预期命中，保留原0.5倍比值并标CACHE_SUSPECT，不用其自动作废无命中的首见统计。S4仍保留609行，重复帧缓存影响披露，不能借缓存删行；若INFO或实际预处理出口不足则不认证新帧时延。理由：缓存不可关闭，改变读数排除口径须用户明确同意，不能拿公文档当无缓存实证。备选维持无缓存合同、3c不执行并记PATH_UNAVAILABLE；未答缺省后一种（仍不关闭范围/不改AC-7），不绕去低层入口或逐请求CLI。 | JB-2；B1口径/重新加载次数/板盘缓存峰值须核后B-SIGN |
| B-SIGN | 推荐按§3与「阶段B补写核清」逐维度核清后只签已核行，未知0；W轮子/板venv峰值、Mac取回、train校准上传、板首建/缓存均须单列。B1/B2至多2候选各全套1次，每候选及总加载/回放闭集见####11 BP-5；冻结后实际树差异回用户。理由：旧包数/字节不能容所选路径，先导与主信封分开，资源签发不回答B-CACHE/采样/STOP。 | 本节前列事实/例外；B-CACHE与逐码STOP |
| B-PRESSURE | 推荐15 Hz额外档本次0、暂不追加；理由：先取得已定5 Hz运行合同读数。追加另签墙钟/查询/样本，压力档仅描述、不改5 Hz门。 | 信封前可选 |
| B-LINES | 推荐保留前次§2的S3时延/4.6 GB、S4 3 pp、S5 1.3倍/7.0 GiB描述性分类；理由：公开/移植来源无目标条件停止依据。欲改STOP先目标试读/新裁定，资源签发不转线；B:2连续线/B:3公式已定不重问。 | 随信封 |
| B-STOP-NOT_SUPER | 推荐停全部B后续回用户；理由：设备合同不符，不自行重刷。 | 随信封逐码确认 |
| B-STOP-FREQ_CAPPED | 推荐实际环境不符报STOP停全部回用户，纯厂商频率参照偏离只描述并继续已签步骤；理由：公开数字不是停止线、无锁频权限。 | 同上 |
| B-STOP-NOT_HEADLESS | 推荐停全部后续回用户；理由：运行合同不符、isolate/默认target未授权。 | 同上 |
| B-STOP-POWER_MODE_NOT_MAXN_SUPER | 推荐停全部后续回用户；理由：指定模式不符，不自行改功耗。 | 同上 |
| B-STOP-IDLE_RAM_OVER | 推荐只超旧1.2 GB参照记录并继续已签B步骤，实际资源不可用报STOP停全部回用户；理由：旧公开数字不是B停止线。 | 同上 |
| B-STOP-LATENCY_OVER | 推荐合同失败确已报STOP停全部回用户；理由：不自动换基准、移植速度超线仅描述不触发此码。 | 同上 |
| B-STOP-FP16_BOX_DIVERGENCE | 推荐新STOP停全部回用户；理由：α/N-A只继承历史S1负结果，不是新偏差续跑许可。 | 同上 |
| B-STOP-THERMAL_THROTTLE | 推荐确证热降频停全部回用户；理由：动态频率不等于热降频，不自行锁频/改散热。 | 同上 |
| B-STOP-FRAME_DROP | 推荐新STOP停全部回用户；理由：α′不覆盖新STOP，S5失败归CORESIDENCY_OVER，S2不重判。 | 同上 |
| B-STOP-RELAY_INTEGRITY | 推荐停全部回用户、SR追加0；理由：5/5用尽，旧SR不验未上板补丁。 | 同上 |
| B-STOP-KERNEL_PARAM_REQUIRED | 推荐停全部后续含其他路径回用户；理由：cma等系统参数未授权，不能自行换栈。 | 同上 |
| B-STOP-VLM_OVER_LINE | 推荐所有所选路径合同不可用停S4/S5回用户；理由：无有效对象；速度/4.6 GB描述超线不触发，单路径PATH_UNAVAILABLE沿原合同继续3c，不扩静默越STOP许可。 | 同上 |
| B-STOP-QUANT_NOT_EQUIVALENT | 推荐合同G5/解析失败停剩余S4/S5回用户；理由：行为/格式退化须用户取舍，3 pp仅描述，不改配方。 | 同上 |
| B-STOP-CORESIDENCY_OVER | 推荐合同快层/连续丢帧/NvMap-OOM/swap失败停全部追加尝试回用户；理由：不自行换产物/帧率/加压力档，1.3倍/7 GiB超线仅描述。 | 同上 |

STOP处置推荐均未确认，沿AC-13修订6与原总则：真实STOP→停全部后续→回用户；本表不替原触发条件。校准/主机/下载地点/例外/额度未代答，本轮无账本新条目。

open_items: BP-1,BP-2,BP-3,BP-4,BP-5

### 阶段B依赖闭集准备（2026-10-04）

登记轮次 `阶段B依赖准备`；Dispatch-Id `P1-ENG-JET-001-阶段B依赖准备-20261004T045326Z-98f7`；构思角色（工程轨道 Opus 子代理）按「阶段B答复落实」§3 第 1–5 条执行的**零消耗静态准备**。本节不是 CLARIFY、AC 修订、信封签发、C/R 轮或 `ACCEPTED`；AC、门值、§2 分类与 §4 推荐值原文不改，下文对 §4 的「不相容/不申请」只是交接受角色审核的准备结论。

**本轮实际动作与边界。** 只读：本仓库证据（`-env.json`、`-assets.json`、`-relay.json`、`-ledger.json`、`-K1K3K4-handoff.md`、SFT-002 三份摘要）、主树 `outputs/eng-jet/P1-ENG-JET-001/` 下既有原始读数（如 `s1s2-system-c/pip-list.txt`）、数据根目录清单与 JSON/配置文本（不算哈希、不加载模型）、仓库源码静态读码，以及下表 [P1]–[P12] 公开文档/源码文本页面（2026-10-04 读取；`main`/`master` 为移动分支，读到的 pin 不等于将来固定 tag 的内容）。**未做**：任何下载、HEAD/HF API/Range GET、pip 解析或 dry-run、ssh/上板、租云/登录、编译/合并/量化/模型加载、回放、测试或 SR、模型/API 查询；未写数据根、主树 `runtime/` 或板端。出处标签：〔证〕既有取证原文；〔本机〕本轮本机只读；〔公〕公开文档（出处类别 (3)，不是目标条件实测）；〔码〕静态读码推定、未实测；`UNKNOWN` = 未核实，不以估算代替。

| 编号 | 公开来源（2026-10-04 读取） | 读到的要点 |
|---|---|---|
| P1 | https://nvidia.github.io/TensorRT-Edge-LLM/latest/user_guide/getting_started/installation.html | 文档版本 **0.11.0**（A3 引用的官方数字出自 0.8–0.10）；x86 主机 Ubuntu 22.04/24.04、CC≥8.0、CUDA 12.x/13.x、Python≥3.10、GPU 显存≈FP16 checkpoint、CPU 内存 1.5×checkpoint；`pip3 install -e ".[export]"`/`".[tools]"`；Orin 仅 JetPack 7.2，Orin 不支持 FP8/FP4 类精度；推理前至少 2 GB 空闲设备内存 |
| P2 | 同站 `getting_started/support-matrix.html` | Jetson Orin = Official / JetPack 7.2 / CUDA 13.2 / JetPack 自带 TRT / FP16、INT8、INT4 |
| P3 | 同站 `getting_started/supported-models.html` | `Qwen/Qwen3-VL-2B-Instruct` 列为受支持（qwen3_vl）；无逐模型精度/平台细注 |
| P4 | 同站 `features/quantization.html` | 后端方法含 `int4_awq`；VLM 视觉塔用多模态校准集（`--image_dataset mmmu`）；未给 int4_awq 完整命令与样本数缺省 |
| P5 | 同站 `developer_guide/customization/calibration-datasets.html` | 内置校准集**缺省从 Hugging Face Hub 取**：文本 `cnn_dailymail`（3.0.0 train）、图像 `lmms-lab/MMMU`（validation）；可用环境变量 `EDGELLM_QUANT_DATASET_<NAME>` 指向本地 JSON/JSONL/`save_to_disk` 目录；样本数与序列长缺省未写 |
| P6 | 同站 `features/lora.html` | 静态合并先于量化：`tensorrt-edgellm-merge-lora --model_dir … --lora_dir … --output_dir …`；未述 Qwen3-VL LoRA |
| P7 | 同站 `examples/experimental-server.html` | Python 服务 `tensorrt-edgellm[server]==0.11.0` 已发布轮子（aarch64/Jetson 可得性未写）；缺省一次只收一个请求；多模态 checkpoint 自动建视觉组件；`--cache-dir` 经 huggingface-hub 下载 |
| P8 | https://www.jetson-ai-lab.com/tutorials/tensorrt-edge-llm/ | Orin 构建前置 `sudo apt install -y cmake build-essential git cuda-toolkit-13-2 libnvinfer-headers-dev libnvinfer-dev libnvonnxparsers-dev`；cmake `-DEMBEDDED_TARGET=jetson-orin -DCUDA_CTK_VERSION=13.2 -DTRT_PACKAGE_DIR=/usr …`；Orin Nano OOM 时降 `maxInputLen`/`maxKVCacheCapacity` 或 `sudo sysctl -w vm.drop_caches=3`；未写 tag |
| P9 | https://raw.githubusercontent.com/NVIDIA/TensorRT-Edge-LLM/main/pyproject.toml | 基础依赖 `cuda-python>=12.6,<14`、`numpy>=2.2.6,<3`；`export`/`tools` extras 的逐包 pin（见 §2） |
| P10 | https://raw.githubusercontent.com/ggml-org/llama.cpp/master/docs/build.md | `cmake -B build -DGGML_CUDA=ON [-DCMAKE_CUDA_ARCHITECTURES=…]`、`cmake --build build --config Release`；CUDA 节未写最低 CMake、未提 Jetson/VMM/libcurl |
| P11 | 同仓 `requirements/requirements-convert_hf_to_gguf.txt` 与 `requirements-convert_legacy_llama.txt`（master） | `torch==2.11.0`（CPU 索引）、`numpy~=2.2.6`、`sentencepiece>=0.1.98,<0.3.0`、`transformers==4.57.6`、`gguf>=0.1.0`、`protobuf>=4.21.0,<5.0.0` |
| P12 | https://github.com/ggml-org/llama.cpp/issues/29142 | 仍 open、无修复 PR；Tegra 多模态双 VMM 池崩溃，报告人提到 `GGML_CUDA_NO_VMM` 但未在 JP7.x 验证 |

#### 1. 板端依赖闭集（Jetson Orin Nano Super，系统栈 B）

| 项 | 包名 / pin | 平台 / ABI | 来源 | 已装 / 拟新增 | 下载地点 | 已知体积及出处 |
|---|---|---|---|---|---|---|
| 系统底座 | L4T R39.2、内核 6.8.12-1021-tegra、`python3.12` 3.12.3（apt 补丁级见证据）、`cuda-toolkit-13-2` 13.2.1-1（nvcc V13.2.78）、`tensorrt` 10.16.2.10-1+cuda13.2 及 Python 绑定 | aarch64 / sm_87 | JetPack 7.2 | 已装〔证〕`-env.json`「readings.platform/nvcc_version」「s1s2_system_stack.python312_patch_change」 | — | 不适用 |
| 快层 sysvenv（`~/eng-jet/sysvenv`，`--system-site-packages`） | torch 2.9.1+cu130、torchvision 0.24.1、triton 3.5.1、nvidia-* cu13 共 15 包、ultralytics 8.4.104、lap 0.5.13、opencv-python-headless 4.11.0.86、onnx 1.18.0、protobuf 6.31.1；系统 numpy 1.26.4、pillow 10.2.0、pip 24.0 | cp312 / manylinux aarch64 | PyPI / PyTorch cu130 / Ubuntu | 已装、S5 快层复用、**不重装**〔证〕主树 `outputs/eng-jet/P1-ENG-JET-001/s1s2-system-c/pip-list.txt`（其 sha 见 `-env.json`「s1s2_system_stack_c.raw」）与「installed_*」 | — | sysvenv 4,687,931,480 B〔证〕`s1s2_system_stack_d.du` |
| 3b/S3–S5 板侧 Python（`language_serve.py` + 拟 `adapters.py` 的 llama-server HTTP 适配） | 新增 0 | — | 仓库代码 | 拟新增 0〔码〕`tools/language_serve.py`、`controller/language_selector.py`、`tools/eng_sft/{parse,prompt_v2}.py` 顶层只用标准库，`controller.trackers` 用已装 numpy；**未实测 import** | — | — |
| llama.cpp 源码 | `ggml-org/llama.cpp`，tag/commit **UNKNOWN**（未固定） | 源码 | GitHub | 拟新增 | **UNKNOWN**（见 B-DLLOC） | **UNKNOWN** |
| llama.cpp 构建 | `cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=87` + `cmake --build build --config Release -j <n>`〔§2.1〕〔公 P10〕；候选附加旗标 `-DGGML_CUDA_NO_VMM=ON`（P12 open）、`-DLLAMA_CURL=OFF`（运行时不得联网取模型；该旗标缺省与 libcurl 依赖在 P10 未写）**待接受固定** | aarch64 + CUDA 13.2 | — | 工具链 cmake/gcc/g++/make 是否存在及版本 **UNKNOWN**（无原读数） | — | 构建墙钟 **UNKNOWN**（§4 ≤1 h 为估算） |
| TRT Edge-LLM 源码 | `NVIDIA/TensorRT-Edge-LLM`，文档版本 0.11.0〔公 P1〕；对应 git tag 名 **UNKNOWN**；`git submodule update --init --recursive` 必需〔公 P1/P8〕，子模块集合 **UNKNOWN** | 源码 | GitHub | 拟新增 | **UNKNOWN**（见 B-DLLOC） | **UNKNOWN**（§4「≤2 归档/≤500 MB」未覆盖递归子模块，不能视为已核） |
| TRT Edge-LLM apt 前置 | `cmake build-essential git cuda-toolkit-13-2 libnvinfer-headers-dev libnvinfer-dev libnvonnxparsers-dev`〔公 P8〕 | arm64 deb | Ubuntu/JetPack apt | 仅 `cuda-toolkit-13-2` 有已装原读数；其余 **UNKNOWN**；缺则需 sudo apt，而 §4 系统设置/apt = 0 → 见 B-APT | — | **UNKNOWN** |
| TRT Edge-LLM 构建/建引擎 | `cmake .. -DCMAKE_BUILD_TYPE=Release -DTRT_PACKAGE_DIR=/usr -DCMAKE_TOOLCHAIN_FILE=cmake/aarch64_linux_toolchain.cmake -DEMBEDDED_TARGET=jetson-orin -DCUDA_CTK_VERSION=13.2 -DENABLE_CUTE_DSL=ALL` + `make -j$(nproc)`；`llm_build … --maxBatchSize 1 --maxInputLen ≤1024 --maxKVCacheCapacity 1024`〔公 P8〕〔§3.3〕；运行时 `EDGELLM_PLUGIN_PATH` | aarch64 / TRT 10.16 | — | `EMBEDDED_TARGET=jetson-orin` 是否即 arch 87、Qwen3-VL **视觉引擎构建命令**（VLM 示例页 404）**UNKNOWN**；P8 的 `vm.drop_caches` 需 sudo → 0 | — | 墙钟 **UNKNOWN**（§4 ≤3 h 为估算） |
| TRT Edge-LLM 板端服务 | `tensorrt-edgellm[server]==0.11.0`〔公 P7〕，基础依赖 `cuda-python>=12.6,<14`、`numpy>=2.2.6,<3`〔公 P9 main〕 | aarch64 轮子可得性 **UNKNOWN** | PyPI（未核） | 拟新增；与 sysvenv 的系统 numpy 1.26.4 不相容，须**独立 venv**（拟 `~/eng-jet/edgellm-venv`），其 TRT 绑定来源、离线按本地目录加载（不经 hub 下载）**UNKNOWN** | **UNKNOWN** | **UNKNOWN** |
| 3a（HF bf16） | — | — | — | 用户 J-A 不做：0 | — | — |

#### 2. 云端依赖闭集（I-A：x86 Linux GPU ≥24 GB；三套互斥环境）

| 环境 | 直接依赖 pin（逐字） | 来源 | 已装 / 拟新增 | 已知体积及出处 |
|---|---|---|---|---|
| 实例底座 | OS/驱动/CUDA/Python/预装包/盘/现价全部 **UNKNOWN**（未租）；〔公 P1〕要求见上表 P1 行 | 供应商镜像 | 未定（见 B-CLOUD） | **UNKNOWN** |
| venv-merge（§3.3 `merge_and_unload`） | `tools/requirements-eng-sft.txt`：torch 2.11.0+cu128、torchvision 0.26.0+cu128、transformers 5.17.0、peft 0.21.0、accelerate 1.15.0、pillow 12.3.0、tokenizers 0.23.2、huggingface-hub 1.30.0、safetensors 0.8.0（9 个，`--extra-index-url …/cu128`） | 仓库已复核 pin；SFT-002 在 5090 上实装〔证〕`P1-ENG-SFT-002-train-summary.json`「pins」 | 拟新增；传递闭集 **UNKNOWN** | **UNKNOWN** |
| venv-gguf（C2 自转 GGUF） | `torch==2.11.0`（CPU 索引）、`numpy~=2.2.6`、`sentencepiece>=0.1.98,<0.3.0`、`transformers==4.57.6`、`gguf>=0.1.0`、`protobuf>=4.21.0,<5.0.0`（6 个，master）〔公 P11〕；另需云端构建 llama.cpp 取 `llama-quantize`（云端 cmake/gcc **UNKNOWN**） | llama.cpp 固定 tag 时重读 | 拟新增；tag 版 pin 与传递闭集 **UNKNOWN** | **UNKNOWN** |
| venv-awq（AWQ + ONNX 导出） | `tensorrt-edgellm[tools]`（含 export）〔公 P9 main〕：`cuda-python>=12.6,<14`、`numpy>=2.2.6,<3`；`torch==2.13.0`、`transformers==5.14.1`、`huggingface-hub>=1.5.0,<2.0`、`onnx==1.19.0`、`onnxscript==0.7.1`、`safetensors==0.8.0`、`numpy==2.2.6`、`onnx-graphsurgeon==0.6.1`；`nvidia-modelopt==0.45.0`、`datasets==5.0.0`、`tqdm==4.69.0`、`einops==0.8.2`、`peft==0.19.1`、`soundfile==0.14.0`、`librosa==0.11.0`、`tiktoken==0.13.0`、`torchvision==0.28.0`、`backoff`、`httpx>=0.27.0,<1`（约 21 个） | Edge-LLM 固定 tag 时重读 | 拟新增；torch CUDA 变体、x86 是否需 TensorRT Python 包、传递闭集 **UNKNOWN** | **UNKNOWN** |
| 校准数据 | 内置缺省 `cnn_dailymail` + `lmms-lab/MMMU` 从 HF Hub 取〔公 P5〕——§4 没有此下载类别 | 见 B-CALIB | 未定 | **UNKNOWN** |

结论：三套环境 torch（2.11/2.13）、transformers（5.17.0/4.57.6/5.14.1）、numpy 互斥，直接 pin 合计约 36 个，已超过 §4「云磁盘/依赖」行推荐的「新增 pip 含传递 ≤12 包/下载 ≤3 GB」；该推荐值与公开 pin 不相容，须在镜像与 tag 固定后重算，**本行不申请签发**。C2 adapter 由 peft 0.21.0 保存〔本机〕`adapter_config.json`「peft_version」，Edge-LLM `tools` 钉 peft 0.19.1，故按 §3.3 在 venv-merge 合并，不用 `tensorrt-edgellm-merge-lora`（兼容性 **UNKNOWN**）。

#### 3. 环境事实核对（§3 第 2 条；engineering §9）

| 事实 | 现有原读数（快照，发令前运行时重取） | 出处 | 状态 |
|---|---|---|---|
| 板解释器/venv | 系统 Python 3.12.3；sysvenv `include-system-site-packages = true` | `-env.json`「s1s2_system_stack_c.runtime_stack」 | 已核 |
| CUDA / 驱动 | nvcc 13.2；libcuda 取 `/opt/nvidia/l4t-gpu-libs` | 同上「coexistence」 | 已核 |
| 系统 TRT 对 sm_87 | 系统 TRT 10.16 已在本板建出 S1 方形 FP16 引擎；Edge-LLM 插件/新算子 **UNKNOWN** | `-fastlayer.json`「S1」 | 部分 |
| torch 无 sm_87 原生 SASS | 只对已实跑算子核过兼容；3b/3c 板侧不用 torch，3a 不做 | 「题 6 选 A 落实」 | 与阶段 B 路径无关 |
| 编译工具链 cmake/gcc/g++/make/git | 无任何原读数 | — | **假设/UNKNOWN** |
| TRT 开发头与 ONNX parser 开发包 | 无原读数（`ldd-trtexec` 只列 C 运行库） | `s1s2-system/ldd-trtexec.txt` | **UNKNOWN** |
| CPU / RAM / swap | 6 核在线、1.728 GHz；`free -m` total 7485、S0 空闲窗口最高 725 MB、S2 最高 2,125 MB；swap 无；无任何 VLM/共驻读数 | `-env.json`「readings」「tegrastats_idle」；`-fastlayer.json` | 已核（非共驻保证） |
| 磁盘 | SR 收尾物理可用 165,474,566,144 B；`~/eng-jet` 占用见 `-ledger.json`「dimensions.board_disk.bytes」 | `outputs/eng-jet/P1-ENG-JET-001/sr-f/board-post.txt` | 快照 |
| 链路 | Mac mini 192.168.8.1 ↔ Jetson 192.168.8.2 有线；板端外网出口曾经 `wlP1p1s0`（阶段 A 取轮子），现状 **UNKNOWN** | `-relay.json`「link」；`-env.json`「s1s2_system_stack_c.network_rx_wlP1p1s0」 | 部分 |
| Mac mini | 数据根解释器 3.12.14；阶段 B 新增 pip/模型加载 0；`evaluate.py` 只用标准库与仓库模块〔码〕 | `-K1K3K4-handoff.md`「K1K3K4全套SUB6」§1 | 已核/静态 |
| 云实例 | 全部 **UNKNOWN** | — | 未租 |

#### 4. 未知项阻塞表（未知闭合前，受影响的 §4 维度保持 0、不申请签发）

| # | 未知 | 受影响 §4 维度 | 闭合方式 |
|---|---|---|---|
| U1 | 板上 cmake/gcc/g++/make/git 存在与版本 | 板上源码取回/构建、板端墙钟 | 只读预检 RP-1（B-PRECHECK） |
| U2 | Edge-LLM apt 前置（TRT dev 头、ONNX parser dev 等）是否已装 | 板上源码/构建（3c）；系统设置 | RP-1；缺则 B-APT |
| U3 | llama.cpp tag/commit、源码体积、`LLAMA_CURL`/`GGML_CUDA_NO_VMM` 实际缺省 | 板上源码取回/构建、到板传输、源码下载地点 | 接受固定 tag 后零消耗读该 tag 的 `CMakeLists.txt`/文档文本 |
| U4 | Edge-LLM tag 名、递归子模块集与体积、`jetson-orin` 目标的 arch、Qwen3-VL 视觉引擎构建命令 | 同 U3 + 板端墙钟 | 同上（读该 tag 的 `cmake/`、`examples/` 文本） |
| U5 | Edge-LLM 板端服务轮子 aarch64 可得性、独立 venv 闭集、离线本地加载 | 板上 pip 下载/安装、板上磁盘、3c 份额的板端 VLM 查询 | 零消耗读 tag 源码/文档 + 接受裁定服务路径 |
| U6 | 云镜像/驱动/CUDA/Python/预装/盘与现价 | 云 GPU 时间/总费用、云磁盘/依赖、云↔Mac 传输 | B-CLOUD；租后首步只读核对（计入 GPU·h） |
| U7 | 三套云环境的传递闭集与下载字节 | 云磁盘/依赖 | B-CLOUDDEP |
| U8 | 官方 GGUF Q4_K_M + mmproj F16 文件名/体积/LFS sha（A3 [Q2] 约 1.107/0.819 GB，类别 (3) 未核） | 模型下载 | 签发后的执行派发读文件页记录期望值再取回 |
| U9 | 合并 bf16、C2 GGUF/mmproj、AWQ checkpoint/ONNX、引擎实际体积 | 传输两维、Mac outputs、板上/云磁盘 | 只能执行后实测；§4 上限仍为估算封顶 |
| U10 | AWQ 校准闭集 | 云 GPU·h（AWQ 部分）、云下载（数据集）；属 K4 | B-CALIB |
| U11 | S4-a 的 base bf16 基准 | 板端 VLM 查询中 S4-a 的 609 份额 | B-S4A |
| U12 | 阶段 B 候选测试树与可达真实加载器 | 实现停点全套、伴随模型/回放 | 候选冻结后跑前只读核对（§7） |
| U13 | JP7.2 上 Edge-LLM 建引擎是否需 `cma`（P1/P8 未提） | 非签发维度；触发即 `STOP(KERNEL_PARAM_REQUIRED)` | 只能实测 |

**RP-1（只读远端预检，本轮未执行；须 B-PRECHECK 授权后由下一派发执行）。** 机器：Mac mini → Jetson，经既有有线链路与已授权存键，Host 按 `-relay.json`「link.ssh」与 Mac mini `~/.ssh/config` 运行时解析；权限：普通用户、无 sudo、无交互；零副作用边界：不安装、不下载、除 ssh 本身外无外联、板上零写入（ssh 登录触发的 `~/.local/state/wireplumber/restore-stream` 会话写入为既有已知现象，照 IR-18 披露），输出只回到 Mac mini 由执行角色写进证据；板端墙钟 ≤5 min。命令（逐字）：

```sh
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes <有线Host> 'export LC_ALL=C PYTHONDONTWRITEBYTECODE=1; for b in cmake gcc g++ cc c++ make ninja git curl; do printf "%s: " "$b"; command -v "$b" || echo MISSING; done; cmake --version 2>&1 | head -1; gcc --version 2>&1 | head -1; g++ --version 2>&1 | head -1; git --version 2>&1; dpkg-query -W -f="\${Package} \${Version} \${db:Status-Abbrev}\n" cmake build-essential gcc g++ make ninja-build git libcurl4-openssl-dev libssl-dev cuda-toolkit-13-2 tensorrt libnvinfer-dev libnvinfer-headers-dev libnvinfer-plugin-dev libnvonnxparsers-dev 2>&1; ls -l /usr/include/aarch64-linux-gnu/NvInfer.h /usr/include/aarch64-linux-gnu/NvOnnxParser.h 2>&1; nproc; free -b; swapon --show --bytes; df -B1 / "$HOME"; du -sb "$HOME/eng-jet"; ip -br addr; "$HOME/eng-jet/sysvenv/bin/python" -c "import sys, numpy; print(sys.version); print(numpy.__version__, numpy.__file__)"'
```

云端无法在租用前预检；签发后云作业第一步固定为只读 `nvidia-smi; cat /etc/os-release; python3 -V; nvcc --version; df -B1; python3 -m pip list`，与 B-CLOUD 所报不符即停回用户（耗时计入 GPU·h）。

#### 5. 资产来源与元数据核对计划（§3 第 3 条；sha 一律使用前运行时解析，不抄）

| 资产 | 本机位置（解析法） | 期望身份来源 | 核对方法 | 去向 |
|---|---|---|---|---|
| base（3a 不做，仅供云端合并） | 数据根 `outputs/eng-loop/P1-ENG-LOOP-001/model/base/`：12 个模型文件，`model.safetensors` 4,255,140,312 B〔本机 ls〕；另有 `.cache/huggingface/` | 同目录 `.cache/huggingface/trees/<rev>.json`，文件名 revision 须等于 `tools/eng_sft/train_lora.py:BASE_REVISION`；其中逐文件 `size`/`blob_id` 与 `model.safetensors` 的 `lfs_sha256`；`download/*.metadata` 首行 revision | `model.safetensors` 现算 sha256 = `lfs_sha256`，小文件 git-blob sha1 = `blob_id`，字节逐个相等；该 tree 记录是下载时的本地来源记录、不是独立复检；T7 未挂载，不扫描 | 云（venv-merge）；不上板；`.cache/` 锁文件不传 |
| C2 adapter | 首选 SFT-002 回传原件：`docs/evidence/P1-ENG-SFT-002-train-summary.json`「selection.job_id」→ 数据根 `outputs/eng-sft/P1-ENG-SFT-002/returned/<job_id>/runs/C2/adapter/`；备份副本 `outputs/eng-loop/P1-ENG-LOOP-001/model/c2-adapter/`（含 3 个 AppleDouble `._*` 文件） | 同摘要「selection.chosen_adapter_sha256」「adapter_manifest.adapter_bytes」 | 现算 sha/字节；配置〔本机〕r=16、alpha=32、`target_modules` 只匹配 `model.language_model.layers.*` 的 q/k/v/o 与 gate/up/down；备份副本只在 sha 相同时可替代；`._*` 一律排除 | 云 |
| C2 bf16 预测（S4 基线） | `-eval-summary.json`「job_b」→ `returned/<job_b>/predictions/eval-adapter.jsonl` | 同摘要「predictions_sha256」与事实 7 | 现算 sha | 只留 Mac mini |
| base bf16 零样本预测（S4-a 候选基线） | `-zero-shot-v2-summary.json`「job_id」→ `returned/<job_id>/predictions/zero-shot.jsonl`（609 行、prompt v2） | 同摘要「predictions_sha256」= `-eval-summary.json`「baseline_predictions_sha256」 | 现算 sha；待 B-S4A | 只留 Mac mini |
| 评估集 / 盲文件 / 绑定帧 | 数据根 SFT-002 `data/`，按 `-eval-manifest.json` | 事实 7 与 manifest | 逐文件 sha、帧绑定计数 | 盲文件+帧上板；gold 只留 Mac mini |
| smoke 32 行 + 25 帧 | 数据根 SFT-002 `data/smoke.jsonl`（事实 9） | 行内 `frame_sha256` | 逐帧 sha；剥字段只留 `sample_id/frame_id/frame_sha256/surface/g4`，剥后文件记来源 sha 与派生 sha | 剥字段件+帧上板 |
| 官方 GGUF Q4_K_M + mmproj F16 | 无本地副本 | HF `Qwen/Qwen3-VL-2B-Instruct-GGUF` 文件页公开 LFS sha256/字节（执行派发读取并记录） | 完整取回后核 sha/字节，失败字节计入 | 板（下载地点见 B-DLLOC） |
| 自产产物（合并 bf16、C2 GGUF/mmproj、AWQ checkpoint、ONNX、板上引擎） | 不存在 | 生成时记命令、工具 tag/commit、sha、字节 | — | 云→Mac mini→板；引擎只在板上生成 |
| 源码（llama.cpp、Edge-LLM+子模块）与代码束 | 不存在 | 固定 tag 的 commit（运行时解析）+ 归档 sha | 取回后核 sha | 板（与云按需） |

搬运清单约束（本轮不传输）：云端**零评估/smoke/gold 数据**（云上无推理）；gold、`truth/`、索引永不离开 Mac mini；AC-12 板上清单检查沿用；不写数据根、主树 `runtime/`。C2 合并后视觉塔是否与 base 逐字节相同（adapter 不含视觉模块），可否直接用官方 mmproj F16，留接受裁定，合并后按张量核对前不推定。

#### 6. AWQ 校准与 S4-a 基准（§3 第 4 条）

- 合同（§2.1、§3.3、AC-8）没有已接受的校准闭集。公开流程缺省会从 HF Hub 取 `cnn_dailymail` 与 `lmms-lab/MMMU`〔公 P5〕，这是 §4 未列的新下载类别；本地覆盖格式只写到「JSON/JSONL/`save_to_disk`」，MMMU 生成器要求的字段与样本数/序列长缺省 **UNKNOWN**。609 行评估集、gold、select-eval 与 smoke 一律不作校准或调参。决定交 **B-CALIB**。
- llama.cpp C2 `Q4_K_M`：`llama-quantize` 不用 imatrix 时无需校准数据；官方 GGUF 是否用 imatrix **UNKNOWN**。拟按不用 imatrix 交接受固定，用则回到 B-CALIB。
- S4-a：本项尚无已接受的 base bf16 基准。可用候选是 SFT-002 作业 A 的 609 行零样本预测（prompt v2、HF bf16、已经 R1@K3 复核），身份见 §5 表；决定交 **B-S4A**。

#### 7. 逐候选静态消费清单（B-CAND-2：B1 = 消费前代码停点，B2 = 消费后证据停点）

依据 `-K1K3K4-handoff.md`「K1K3K4全套SUB6」§1/§3 的跑前核对与实际计账，按现测试树同构推定（静态上界，候选冻结后跑前只读核对必须重算）：

| 维度（每候选） | B1 | B2 | 说明 |
|---|---|---|---|
| Mac mini 停点全套 | 1 | 1 | 数据根解释器只读使用、不装包；无 `-v`、不重跑 |
| det-assoc 冻结检测器 CPU 加载 | ≤2 | ≤2 | `CarrierSelfTest` 两例 |
| NanoTrack 构造尝试 / 读权重 | ≤2 / 0 | ≤2 / 0 | 主树无 `runtime/models/nanotrack-v2/` |
| CSRT 构造尝试 / 实例 | ≤2 / 0 | ≤2 / 0 | cv2 5.0.0 无 `TrackerCSRT_create` |
| 零模型部分回放（各 60 帧） | ≤2 | ≤2 | `ResidentCarrierReplay` |
| YOLOE / DINOv2 / llama.cpp / TRT Edge-LLM / HF VLM / MPS | 0 | 0 | **阶段 B 新测试只许替身**；跑前核对发现可达真实 VLM/GGUF/TRT 加载即停回用户 |
| 墙钟 / Mac outputs 增量 | ≤15 min / <0.1 MB | 同左 | SUB:6 实测 349 s、+3,853 B |

继承限制（不自动沿用旧例外）：既有导入错误 `test_eng_sft_{audit,build,cloud,evaluate}` 与 `test_language_k_binding`（`tests.fixtures`/`tests.test_language_selector` 缺失）、CSRT 两例、Carrier 1 例与 scene006 29 条照记；后两类每个新候选都须用户重新具名（B-EXC），R1-5/6 OPEN 保持。`ledger build` 重跑前须先补 SUB:6 保留支持（R2/R3 §5 观察）。复核新增实测/模型/回放/SR 推荐 0。

#### 8. 云作业控制承接与代码停点（§3 第 5 条）

- `tools/eng_sft/cloud_runner.py` 的子命令（bundle/verify/job-a/job-b/selfcheck）专为 SFT-002；可复用的只有 `budget_plan`/`init_budget`/`BudgetGuard`/`Watchdog`/`StageLedger` 模式，且上限常量按 SFT-002 的 8 GPU·h/6 美元写定。复用前须先承接 `docs/implementation-status.md` 账本 **F7**（`--inbound-gb`/`--outbound-gb` 负值可抬高上限→改为 `LaunchRefused` 拒绝，`LedgerTests.test_budget_plan_reserves_storage_and_transfer_inside_six_dollars` 追加断言）与 **F8**（看门狗与主线程并发写 `job-receipt.json.tmp`→进程内锁或唯一临时名，`LedgerTests.test_watchdog_exit_records_stop_before_exiting` 并发写断言），并把上限参数化到本项已签值。注意：Mac mini 全套中 `test_eng_sft_cloud` 现为导入错误不执行，修复回归必须真正执行才算。不借 SFT-002 余额（随其 DONE 作废），不运行有债的预算/看门狗。复用-修债或在 `tools/eng_jet/` 另写最小作业控制，二者都属 B1 代码，交接受裁定；实例销毁仍由用户在截止前执行。
- 源码/证据边界：代码 `tools/eng_jet/` + `tests/test_eng_jet_*.py`（选修债路线则加 `tools/eng_sft/cloud_runner.py` 与对应测试）；证据 §3.4 文件；原始件 `outputs/eng-jet/`；`Assets/`、`controller/`、`config/` diff 为空。
- **不可重跑消费前的代码停点 B1** 至少含：S3/S4/S5 板侧线束与 `adapters.py`（llama-server 与 Edge-LLM 两路，`cache_prompt=false`、首见/重复、`CACHE_SUSPECT`、token=300、冷启动单列、S5 稳态连续丢帧与快层 p95 公式）；搬运/剥字段/资产核对/板上清单守卫；云作业脚本与预算/看门狗/依赖安装纪律；校准集转换（若 B-CALIB 选本域，属 K4）；账本对阶段 B 维度与 SUB:6 块的保留支持；评分封装。B1 经四项自证→C→独立 R 通过且用户签发后才可消费；产出证据另为 B2 走 C→R。SR 追加 0、R1 补丁仍未上板，旧 SR 不能验证补丁。

#### 9. 闭集判定与交接受审核的接受侧事项

**判定：未闭。** 可证部分：板端既有栈复用清单、资产身份与搬运计划、阶段 B 候选静态消费清单、三套云环境的直接 pin。U1–U13 未闭，故 §4 中板上 pip、板上源码/构建、云 GPU 时间/总费用、云磁盘/依赖、模型下载、传输两维、板端墙钟、Mac 中转和板端 VLM 查询（S4-a 份额）各行**本轮均不申请签发**；全零行（系统设置、Play/ID/训练/API/发布、复核新增）不受影响；「实现停点全套」与「伴随模型/回放」可按 §7 静态上界申请，但以候选冻结后的跑前核对为生效条件，由接受角色判定。不称「完整可执行」。

交接受角色在合同解释内固定（非用户事项）：llama.cpp 与 Edge-LLM 的 tag 与取回形式；`GGML_CUDA_NO_VMM`、`LLAMA_CURL=OFF` 是否进构建命令；Edge-LLM 板端服务路径（§3.3 已许「实验性服务端或 Python 绑定」；推荐独立 venv 的 `tensorrt-edgellm[server]`，逐请求起 C++ `llm_inference` 会每次重载引擎、破坏首见时延口径，不推荐）；合并走 venv-merge；C2 GGUF 不用 imatrix；官方 mmproj 能否复用；云作业控制复用-修债还是另写。

#### 10. needs_user（阶段B依赖准备，2026-10-04；均未答复，答复前按缺省 0）

现行入口已收拢至「阶段B准备审核」§5；以下原清单保留作来源，不再单独发令或并列发问。

- **B-PRECHECK**：是否授权执行一次本节 #### 4 的 RP-1（Mac mini→Jetson 有线、≤5 min、无 sudo/安装/下载/写入）。推荐授权：engineering §9 要求先有原始读数再签发，这是闭合 U1/U2 与板端外网出口现状的最低成本办法；阶段 A 余额不转用，故须单列。
- **B-APT**：若 RP-1 显示 Edge-LLM/llama.cpp 构建前置包缺失：(a) 用户本人按 P8 逐字包名 `sudo apt install` 并入账（同 10-02 装 pip/venv 的先例）/(b) 放弃 3c、只做 3b/(c) 授权代理 sudo。推荐 (a)：系统包属用户操作，代理 sudo 保持 0，且保留 C2 AWQ 路径（Q2 核心）。
- **B-DLLOC**：源码（含 Edge-LLM 递归子模块）与官方 GGUF 的取回地点：(a) Mac mini 取回固定 tag、核 sha 后经有线传板/(b) 板上直接取回。推荐 (a)：只有一份核过 sha 的副本，板上不依赖外网出口与 git，失败字节在 Mac 侧计账；代价是 Mac 下载与到板传输两维都要列额度。
- **B-CLOUD**：云实例镜像与现价由用户在供应商控制台查后提供（我方不登录）。推荐 Ubuntu 22.04/24.04、驱动支持 cu128 与 torch 2.13 的 CUDA 12.x/13.x、显存 ≥24 GB 的 x86 实例，报价须含存储与流量：P1 只给最低要求，现价与镜像决定 GPU·h/费用/磁盘能否封顶在 ≤4 美元。
- **B-CLOUDDEP**：云端三套环境的依赖闭集取法：(a) 镜像固定后，在一次性实例内按固定直接 pin 真实安装（非 dry-run），装后记录 `pip freeze` 与实际下载字节，受包数/字节上限约束、计入 GPU·h/费用/传输/磁盘/依赖/下载维度/(b) 再开一轮零消耗准备，按镜像 Python 逐包读 PyPI 公开元数据做静态传递闭集。推荐 (a)：传递闭集依赖尚未确定的镜像 Python 与平台标记，静态推演有数十包且仍不可实证；实例用完即销毁，越界成本受费用上限封顶。这放宽了板端 SUB:3「逐包 `--no-deps`」做法，只限云端，须用户明示。
- **B-CALIB**：AWQ 校准数据：(a) 本域：只取 SFT-002 train 划分的帧与 surface（排除 select-eval、eval、smoke 帧），经 `EDGELLM_QUANT_DATASET_<NAME>` 指向本地 JSONL，样本数取工具缺省；作为 K4 数据条件写进 B1/(b) 官方缺省 `cnn_dailymail`+MMMU 在云端从 HF 取，须新增数据集下载维度、体积 UNKNOWN/(c) 不做 3c，只做 3b。推荐 (a)：不新增外部下载类别；SFT-002 泄漏报告已把 train 与 eval 隔离；激活分布与部署一致。代价：覆盖格式与字段须先静态核实（U5 同轮），且结果只代表「本域校准的 AWQ」，不代表官方缺省配方。
- **B-S4A**：S4-a 的 base bf16 基准：(a) 复用 SFT-002 作业 A 的 609 行零样本预测（§5 表解析）/(b) 不做 S4-a/(c) 另跑 base bf16，须新增 GPU 消耗。推荐 (a)：零新消耗；行、prompt v2 与解析器都相同，且已经独立复核。须注明它出自 5090 HF bf16 运行时，S4-a 差值同时含「转换+量化」与运行时差异。
- **B-EXC**：B1/B2 两个新候选的停点全套是否随签发重新具名 Carrier/scene006 两项例外（仅同名同类）。推荐签发时一并具名：两者是本机环境的已知失败，不具名则新候选第 2 项自证无法成立；例外不自动延长，其他新增失败照常阻断。

以上新增事项与「needs_user（阶段B答复落实，2026-10-04）」的 B-SIGN/B-PRESSURE/B-LINES/B-STOP-* 并列，**不替代、不回答**这些事项；B-SIGN 逐维度签发应在本节 U 项闭合后进行。下一 owner/status 只在状态板交接行维护。

#### 11. 阶段B准备补写（2026-10-04，「阶段B准备审核」§4 BP-1…BP-5）

登记轮次 `阶段B准备补写`；Dispatch-Id `P1-ENG-JET-001-阶段B准备补写-20261004T052357Z-f694`；构思角色（工程轨道 Opus 子代理）。以「阶段B准备审核」§2 的 AC-7 修订 2、AC-10 修订 14、AC-11 修订 2、AC-8 修订 2、AC-14 修订 2 为准逐条补写；只追加，不覆盖接受裁定，#### 1–10 原文不改，需修正处写「更正」并给出处。**本节不是 CLARIFY、AC 修订、信封签发或 `ACCEPTED`；阶段 B 全部生效值仍 0。** 本轮只读：本机既有证据、数据根 SFT-002 `data/*.jsonl` 字段（不算哈希、不读帧字节）、`model/base/` 目录 `ls` 体积，以及下表固定 tag 公开源码/文档文本页（2026-10-04）。未做：归档/轮子/模型取回、HEAD/HF API/Range GET、pip 解析或干跑、ssh/上板/RP-1、租云/登录、编译/合并/量化/模型加载/回放/测试/SR/查询。PyPI 项目文件页返回浏览器质询，**未绕过、未改用 JSON 接口**，故轮子文件名与字节未从 PyPI 读得。标签同前；另〔估〕= 量级推算，只作合算提示，不作额度依据。

| 编号 | 公开来源（固定 tag，HTML/原始文本页） | 用于 |
|---|---|---|
| Q1 | `NVIDIA/TensorRT-Edge-LLM` tag `v0.11.0`：`.gitmodules`、`pyproject.toml`、`requirements{,-server}.txt`、`CMakeLists.txt`、`cpp/CMakeLists.txt`、`cmake/{aarch64_linux_toolchain,CuteDsl,GuidedDecoding,FindTensorRT}.cmake`、`3rdParty/` 与 `kernelSrcs/cuteDSLPrebuilt/` 目录页 | BP-2/3 |
| Q2 | 同 tag `docs/source/user_guide/getting_started/{installation,support-matrix,direct-engine-builder}.md` | BP-2/3 |
| Q3 | 同 tag `docs/source/user_guide/examples/experimental-server.md`、`features/{kv-cache-reuse,quantization}.md`、`developer_guide/customization/calibration-datasets.md` | BP-2/4 |
| Q4 | 同 tag 源码 `experimental/server/{cli,config}.py`、`experimental/server/runtime/{engine,engine_build}.py`、`tensorrt_edgellm/scripts/quantize.py`、`tensorrt_edgellm/quantization/{quantize,quantization_configs}.py`、`quantization/datasets/__init__.py` | BP-2/4 |
| Q5 | 同 tag `packaging/{size_budget,variants}.toml` | BP-2/3 |
| Q6 | `ggml-org/llama.cpp` tag `b11381`：`.gitmodules`、`CMakeLists.txt`、`ggml/CMakeLists.txt`、`ggml/src/ggml-cuda/CMakeLists.txt`、`common/CMakeLists.txt`、`tools/CMakeLists.txt`、`tools/{server,mtmd,ui}/CMakeLists.txt`、`vendor/CMakeLists.txt`、`vendor/cpp-httplib/CMakeLists.txt`、`scripts/ui-assets.cmake`、`requirements/requirements-convert_{hf_to_gguf,legacy_llama}.txt`、`convert_hf_to_gguf.py`、`conversion/` 目录页 | BP-2/3 |
| Q7 | `huggingface.co/Qwen/Qwen3-VL-2B-Instruct-GGUF` 公开 tree/blob 页（HTML，非 API） | BP-4 |
| Q8 | GNU coreutils 手册「timeout invocation」 | BP-1 |

##### BP-1 只读预检完整命令（本轮未执行）

**更正**：#### 4 的 RP-1 原命令不再作为待授权命令（缺全程/命令级超时、路由读数与无 site 解释器，见「阶段B准备审核」§4 BP-1）；B-PRECHECK 只指向下列版本。

- **机器/权限**：Mac mini 发起并唯一落盘 → Jetson 只读；有线链路；`user@host` 运行时取 `-relay.json`「link.ssh」首段（不手抄）。普通用户、无 sudo、无 TTY、无交互；保持 `BatchMode=yes`/`StrictHostKeyChecking=yes`，另加 `UpdateHostKeys=no`、`ControlMaster=no`/`ControlPath=none`，Mac 侧不改 `known_hosts`、不建控制套接字、不改 `~/.ssh/config`。存键许可与 IR-18 披露不构成本次登录额度，额度只来自 B-PRECHECK。
- **超时/收尾**：Mac 侧 `perl alarm 300` 包住 ssh（全程 ≤ 300 s，超时 rc 142）；远端整体 `timeout -k 5 270`（非 `--foreground` 时子进程一并计时〔公 Q8〕，远端最迟约 275 s 结束，即远端收尾依据）；逐条读数 `timeout -k 2 8`（`dpkg-query` 20 s、`du` 60 s，最坏合计 264 s）。超时或失败**不重试**、不二次登录核查残留；stdout/stderr/返回码原样保留。
- **读数口径**：Python 只用 `-I -S -B`（不跑 site/.pth、不写字节码），只读 `sys.version`/前缀，不 import numpy/TRT/torch；numpy 以 `dpkg-query python3-numpy` 与 sysvenv 目录名为准，可对照阶段 A 原件 `s1s2-system-c/pip-list.txt`。比原 RP-1 新增：glibc（Edge 轮子平台标签 `manylinux_2_39_aarch64`〔公 Q5〕）、`/usr/local/cuda/targets/sbsa-linux`（Edge 工具链对 CUDA ≥ 13 的固定路径〔码 Q1〕）、`/usr/bin/aarch64-linux-gnu-g{cc,++}`（同一工具链硬编码）、`python3-libnvinfer`/`python3.12-venv`、IPv4/IPv6 路由表（`ip route show` 只读内核表、不发包）。
- **输出**：主树 `outputs/eng-jet/P1-ENG-JET-001/stageb-precheck-<UTC 时间戳>/`（目录名运行时生成，已存在即停）内 `rp1.stdout`、`rp1.stderr`、`rp1.rc`、`started_utc`、`ended_utc`；`-env.json` 新块与 sha 由执行派发运行时写。
- **附带副作用（须在 B-PRECHECK 明示，不称板端绝对零写）**：sshd/PAM 认证与会话日志（journald、`auth.log`、`wtmp`/`lastlog`）；logind 用户会话及已知 `~/.local/state/wireplumber/restore-stream` 写入（IR-18 同类）；被读文件 atime（relatime）。命令本身不建文件、不装包、不下载，除 ssh 外无外联。
- **失败处置**：rc 255（连不上/拒键）、124/137（远端超时）、142（Mac 超时）或单项 rc ≠ 0 → 记原文与 `UNKNOWN`，停回接受/用户；不 sudo 兜底、不改参数重跑。

```sh
cd "$(git rev-parse --show-toplevel)" || exit 1   # Mac mini 主树根
HOST="$(python3 -c 'import json;print(json.load(open("docs/evidence/P1-ENG-JET-001-relay.json"))["link"]["ssh"].split("，")[0].strip())')"
OUT="outputs/eng-jet/P1-ENG-JET-001/stageb-precheck-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "$OUT" || exit 1
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/started_utc"
/usr/bin/perl -e 'alarm 300; exec @ARGV or die "exec failed: $!\n"' \
  /usr/bin/ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o UpdateHostKeys=no \
  -o ConnectTimeout=15 -o ServerAliveInterval=10 -o ServerAliveCountMax=3 \
  -o ControlMaster=no -o ControlPath=none -o ForwardAgent=no -o ClearAllForwardings=yes \
  "$HOST" '/usr/bin/timeout -k 5 270 /bin/sh -s' \
  > "$OUT/rp1.stdout" 2> "$OUT/rp1.stderr" <<'RP1'
export LC_ALL=C PATH=/usr/local/cuda/bin:/usr/sbin:/usr/bin:/sbin:/bin
r() { t=$1; l=$2; shift 2; printf '### %s\n' "$l"; timeout -k 2 "$t" "$@" 2>&1; printf '### rc=%s\n' "$?"; }
r 8 user id -un
r 8 os cat /etc/os-release
r 8 l4t head -n 1 /etc/nv_tegra_release
r 8 glibc getconf GNU_LIBC_VERSION
r 8 tools sh -c 'for b in cmake gcc g++ cc c++ make ninja git curl aarch64-linux-gnu-gcc aarch64-linux-gnu-g++ nvcc python3 python3.12; do printf "%s: " "$b"; command -v "$b" || echo MISSING; done'
r 8 cmake_v cmake --version
r 8 gcc_v gcc --version
r 8 gxx_v g++ --version
r 8 nvcc_v nvcc --version
r 20 dpkg dpkg-query -W -f='${Package} ${Version} ${db:Status-Abbrev}\n' cmake build-essential gcc g++ make ninja-build git libssl-dev cuda-toolkit-13-2 tensorrt libnvinfer-dev libnvinfer-headers-dev libnvinfer-plugin-dev libnvonnxparsers-dev python3-libnvinfer python3-libnvinfer-dev python3.12-venv python3-numpy python3-pip
r 8 trt_headers ls -l /usr/include/aarch64-linux-gnu/NvInfer.h /usr/include/aarch64-linux-gnu/NvInferVersion.h /usr/include/aarch64-linux-gnu/NvOnnxParser.h
r 8 cuda_dirs ls -ld /usr/local/cuda /usr/local/cuda/targets/sbsa-linux /usr/local/cuda/targets/aarch64-linux
r 8 sys_py_pkgs ls -d /usr/lib/python3.12/dist-packages/tensorrt /usr/lib/python3/dist-packages/numpy
r 8 sysvenv_cfg cat "$HOME/eng-jet/sysvenv/pyvenv.cfg"
r 8 sysvenv_numpy sh -c 'ls -d "$HOME"/eng-jet/sysvenv/lib/python3.12/site-packages/numpy* 2>&1'
r 8 py_sys /usr/bin/python3 -I -S -B -c 'import sys; print(sys.version); print(sys.prefix)'
r 8 py_venv "$HOME/eng-jet/sysvenv/bin/python" -I -S -B -c 'import sys; print(sys.version); print(sys.prefix, sys.base_prefix)'
r 8 nproc nproc
r 8 mem free -b
r 8 swap swapon --show --bytes
r 8 df df -B1 / "$HOME"
r 60 du du -sb "$HOME/eng-jet"
r 8 addr ip -br addr
r 8 route4 ip -4 route show
r 8 route6 ip -6 route show
printf '### end\n'
RP1
echo "$?" > "$OUT/rp1.rc"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/ended_utc"
```

##### BP-2 板端固定 tag 闭集（llama.cpp `b11381`、Edge-LLM `v0.11.0`）

| 项 | 固定 tag 读数 | 出处 / 状态 |
|---|---|---|
| llama.cpp 子模块 | `.gitmodules` 为空 → 子模块 0；`vendor/`（含 cpp-httplib）在树内 | 〔公 Q6〕；取回 = 1 个版本化主源码归档 |
| llama.cpp 隐式外联点 | (i) `GGML_CUDA_CCCL_VERSION` 非空才 `FetchContent` CCCL → 已固定为空；(ii) UI：`LLAMA_BUILD_UI=ON` 才 npm、`LLAMA_USE_PREBUILT_UI=ON` 才从 HF bucket 下载 → 两者固定 OFF 时只告警「无内嵌 UI」继续构建；(iii) `LLAMA_LLGUIDANCE=ON` 才 `ExternalProject` 拉 llguidance，缺省 OFF → 建议命令显式 `-DLLAMA_LLGUIDANCE=OFF`（待接受固定）；(iv) `LLAMA_CURL` 已弃用（`llama_option_depr`，传入只告警并忽略），按 AC-7 修订 2 不进命令；(v) `vendor/cpp-httplib`：`LLAMA_BUILD_BORINGSSL`/`LLAMA_BUILD_LIBRESSL` 显式为真才 `FetchContent` BoringSSL/LibreSSL（未定义即关）→ 不传；(vi) build-info 有 `.git` 才读提交号，归档无 `.git` → 提交号以归档身份记 | 〔码 Q6〕；Q6 所列 CMake 文件内无其他 `FetchContent`/`ExternalProject`/`file(DOWNLOAD)`；未逐一读的其余子目录残留 `UNKNOWN`，离线构建若外联即失败并停 |
| llama.cpp 构建要求 | 顶层 CMake ≥ 3.14、`ggml-cuda` ≥ 3.18；C/C++ 编译器与 make（或 ninja）；所读 CMake 文件未见 Python 需求；`LLAMA_OPENSSL=OFF` 后不再 `find_package(OpenSSL)`；非登录 ssh 的 PATH 不含 `/usr/local/cuda/bin`〔证 `-env.json`「readings.nvcc_version.source_note」〕 | 〔码 Q6〕；工具链存在性 = U1（BP-1） |
| llama.cpp 板上命令（候选，待接受固定） | `cmake -S <src> -B <build> -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=87 -DGGML_CUDA_NO_VMM=ON -DLLAMA_OPENSSL=OFF -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF -DGGML_CUDA_CCCL_VERSION= -DLLAMA_LLGUIDANCE=OFF -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc` + `cmake --build <build> --config Release -j <n> --target llama-server` | AC-7 修订 2 固定项 + 本行新增两项（LLGUIDANCE、CUDA 编译器绝对路径）与只建 `llama-server` 目标，均交接受 |
| llama.cpp 转换（云，C2 GGUF） | 同 tag `convert_hf_to_gguf.py`：缺省插入树内 `gguf-py`（未设 `NO_LOCAL_GGUF`）；`conversion/qwen3vl.py` 存在；`--mmproj` 导出投影器；`--outtype` ∈ f32/f16/bf16/q8_0/tq1_0/tq2_0/auto；`--remote` 会经 hub 取文件 → 禁用，只给本地目录；pin：`torch==2.11.0`（CPU 索引）、`numpy~=2.2.6`、`sentencepiece>=0.1.98,<0.3.0`、`transformers==4.57.6`、`gguf>=0.1.0`、`protobuf>=4.21.0,<5.0.0` | 〔公/码 Q6〕；与 #### 0 表 P11（master）逐行相同；用树内 gguf-py 时 pip `gguf` 可不装（交接受） |
| Edge-LLM 子模块 | 4 个：googletest、nlohmannJson、NVTX、xgrammar，各带 `revision` 字段（取回时按 `.gitmodules` 与 gitlink 运行时解析，不抄）；xgrammar 另有嵌套子模块 dlpack（`cmake/GuidedDecoding.cmake` 探针缺即 FATAL）；`3rdParty/{inja,miniaudio,stb}` 在树内 | 〔公/码 Q1〕；只在源码路线 S 需要 |
| Edge-LLM Orin arch | `EMBEDDED_TARGET=jetson-orin` → `CMAKE_CUDA_ARCHITECTURES 87`；CUDA ≥ 13 时 `CUDA_DIR=/usr/local/cuda/targets/sbsa-linux`；工具链硬编码 `/usr/bin/aarch64-linux-gnu-g{cc,++}` 与 `/usr/local/cuda/bin/nvcc`；构建需 Python3 解释器（插件 JIT 源嵌入） | 〔码 Q1〕；U4 arch 部分闭合，路径存在性归 BP-1 |
| `ENABLE_CUTE_DSL` | **更正**（#### 1「TRT Edge-LLM 构建/建引擎」行只引教程 P8）：固定 tag CMake 缺省 `fmha`；同 tag 安装文档 JetPack 7.2 Orin 平台命令用 `ALL`；直接构建器（服务端内部所用）文档写明需 `ALL`；发布轮子 Orin 载荷行 `cmake_args` 亦为 `ALL`。CuTe 产物取树内 `kernelSrcs/cuteDSLPrebuilt/cutedsl_aarch64_sm_87_cuda13.tar.gz`（同目录有 `.sha256`，非 LFS，构建期不联网）；该包实际含哪些组 `UNKNOWN` | 〔公/码 Q1/Q2/Q5〕 |
| 3c 分发二选一（交接受） | **W 发布轮子**：`tensorrt-edgellm[server]==0.11.0`，aarch64 cp312 `manylinux_2_39_aarch64`；载荷行 `jetson-orin-jp72-cu13-sm87`（L4T 探针 R39.2、`libcudart.so.13`、`libnvinfer.so.10`、SM87、CTK 13.2）与本板 R39.2 / TRT 10.16.2.10 / CUDA 13.2 文字相符〔证 `-env.json`「readings.platform」〕，实际选中只能由装后 `runtime.load()` 判定（U13 类）；TRT Python 绑定用系统 `/usr/lib/python3.12/dist-packages/tensorrt` 10.16.2.10〔证 `s1s2_system_stack_c.runtime_stack`〕经 `--system-site-packages` 暴露，venv 内 numpy 2.2.6 遮蔽系统 1.26.4，sysvenv 不动；无源码/子模块/CMake。**S 源码**：递归子模块 + `BUILD_PYTHON_BINDINGS=ON` + `pybind11==3.0.4` + `pip install -e ".[server,server-tools]"`，后者在构建隔离下另取 `scikit-build-core>=0.11,<0.12`、`wheel>=0.45`、`cmake>=3.20,<4`、`ninja>=1.5,<2`（隐式下载，须 `--no-build-isolation` 加预取或另列）；另需 TRT dev 头（`libnvinfer-dev`/`-headers-dev`），ONNX parser dev 是否必需 `UNKNOWN`。构思推荐 W：不需板上编译 Edge、无子模块与构建隔离外联，且有与本板同号的官方载荷行；代价见下「体积」 | 〔公/码 Q1/Q2/Q5〕；AC-7 修订 2「分发/绑定」由接受裁定 |
| 3c 轮子体积 | aarch64 实际字节 `UNKNOWN`（PyPI 页未读得）；`size_budget.toml` 上限压缩 2,684,354,560 B / 解压 5,100,273,664 B；x86_64 cp312 资格轮子 2026-08-12 实测压缩 2,067,563,217 B / 解压 3,969,749,991 B（注明 aarch64 载荷行更少） | 〔公 Q5〕；仅此一件即可能超原「板 pip ≤ 1 GB」 |
| 3c 服务入口（固定 tag） | `tensorrt-edgellm-serve <本地检查点目录>`：`model` 为已存在目录时 `resolve_model_dir` 直接返回、不导入 hub〔码 Q4〕，另设 `HF_HUB_OFFLINE=1` 兜底；**缺省 `--host 0.0.0.0`，须显式 `--host 127.0.0.1`**；`--cache-dir` 设在 `~/eng-jet/` 内，`--engine-cache-max-size-gb` 缺省 50 GiB 须按板盘份额设小；`--max-input-len 1024 --max-kv-cache-capacity 1024 --max-batch-size 1`；不加 `--enable-context-reuse`/`--enable-in-flight-batching`/`--speculative-config`；缺省一次只收一个请求；请求走 `/v1/chat/completions`，图像用 data URL（或 `--allowed-local-media-path` 指向 `~/eng-jet` 子目录），`temperature 0`、`max_tokens 160`、`stream false`、逐请求 `reuse_context:false` | 〔公/码 Q3/Q4〕；`XDG_CACHE_HOME`/`HF_HOME` 等重定向到 `~/eng-jet/home/` 沿 AC-16 做法，外部写入照核 |
| 3c 本地板建组件 | 服务端**只收检查点、拒收引擎/ONNX 路径**；缓存未命中时内部跑直接构建器 `--components all`，VLM = LLM + visual，写 `llm.engine`、`visual/visual.engine`；首次启动的构建时长与盘占用落在「加载/冷启动」单列；直接构建器标「实验性」，其中 INT4 AWQ 与 visual 组件为「已实现、CI 未覆盖」 | 〔公 Q2/Q3〕→ JB-1 |
| 3c 缓存 | 文本 KV 复用缺省关闭，逐请求 `reuse_context:false` 双保险；**视觉编码嵌入缓存缺省开（256 MiB，按解码后图像字节哈希命中即跳过 ViT），v0.11.0 服务端与 Python API 不提供预算/关闭入口（文档原句；CLI 参数表亦无）**；只有「全部媒体命中」的 INFO 日志 | 〔公/码 Q3/Q4〕→ JB-2 |
| 3c token 读数 | 响应 `usage.prompt_tokens`/`completion_tokens` 取自原生结果；`/v1/messages/count_tokens` 给输入总数；无逐图 token 字段，图像 token = 300 的核对出口 `UNKNOWN` | 〔公/码 Q3/Q4〕→ JB-3 |
| 3c 依赖（W，直接） | `tensorrt-edgellm==0.11.0`、`cuda-python>=12.6,<14`、`fastapi==0.139.2`、`uvicorn==0.51.0`、`huggingface-hub>=1.5.0,<2.0`、`av==17.1.0`、`numpy==2.2.6`、`python-multipart==0.0.32`（8 个）；条件项 `transformers==5.14.1`（`server-tools`）：`requirements-server.txt` 注释写「从检查点建引擎时装」，安装文档又写其为「可选参考/工具环境」→ 必需性 `UNKNOWN` | 〔公 Q1/Q2〕→ JB-4；传递闭集 `UNKNOWN`（静态读取方法见 JB-6） |

**更正**：#### 1「TRT Edge-LLM 板端服务」行的「aarch64 轮子可得性 UNKNOWN」→ 固定 tag 文档写明发布 aarch64 cp310–312 轮子并含 Orin JP7.2 载荷行；实际文件与字节仍 `UNKNOWN`。#### 4 U4「Qwen3-VL 视觉引擎构建命令（404）」→ 服务端路线由其内部直接构建器建 visual；C++ 路线另有 `examples/multimodal/visual_build`（`--onnxDir --engineDir --minImageTokens --maxImageTokens --maxImageTokensPerImage`），需 ONNX，服务端路线不用。

##### BP-3 云端：固定 tag 依赖与镜像事实分列

镜像事实（OS/驱动/CUDA/Python/预装/盘/现价）全部待 B-CLOUD，**下表只写 tag 侧直接依赖；受镜像影响的维度保持 0**。真实安装不能代替装前环境核验。

| venv | 直接依赖（逐字） | 平台 / 来源 | 已装 / 新增；传递闭集 |
|---|---|---|---|
| venv-merge | `tools/requirements-eng-sft.txt` 9 个（torch/torchvision 带 `+cu128`，`--extra-index-url …/cu128`） | x86_64，cp 版本依镜像；PyPI + PyTorch cu128 索引 | 新增（镜像预装可能部分重合，`UNKNOWN`）；传递 `UNKNOWN`（SFT-002 当时是解析器安装，无逐包清单〔证 train-summary 只记 pins〕） |
| venv-gguf | Q6 那 6 个（`gguf` 可改树内） | x86_64；PyPI + PyTorch CPU 索引 | 新增；传递 `UNKNOWN`；另需云端 `llama-quantize`：可用 CPU 后端构建（`-DGGML_CUDA=OFF`），云端 cmake/gcc `UNKNOWN`（可选读法：改在板上用已建的 llama.cpp 做 Q4_K_M，须接受另裁、计板端墙钟） |
| venv-awq | `tensorrt-edgellm==0.11.0` + 基础 `cuda-python>=12.6,<14`、`numpy>=2.2.6,<3` + `[tools]` 19 个（同 #### 2 表，与固定 tag `pyproject.toml` 逐项相同；numpy 两处计一次，合 21 个） | x86_64 轮子（资格轮子实测 2,067,563,217 B，含全部 x86 载荷）或源码检出走 `EDGELLM_PYTHON_ONLY_WHEEL=ON`（需构建隔离四件，见 BP-2）；量化只要 GPU，`--dtype` 只接受 fp16 | 新增；量化是否需 x86 TensorRT Python 包 `UNKNOWN`；传递 `UNKNOWN` |

**更正**：#### 2 venv-awq「AWQ + ONNX 导出」→ 若接受选服务端路线（AC-7 修订 2），交付物只是 `tensorrt-edgellm-quantize` 产出的统一 HF 式检查点，ONNX 导出不执行；`[tools]` 仍是量化所需（含 export 依赖）。

- **重算推荐**：直接依赖合计 9 + 6 + 21 = 36 个（跨 venv 同名包分计，不含镜像预装重合）。已知硬数仅 base 本机约 4.27 GB（`model/base/` 11 个文件 `ls` 合计 4,266,647,442 B，不含 `.cache`）与 x86 Edge 轮子（压缩约 2.07 GB、解压约 3.97 GB，若用轮子）；两项已逾 10 GB，torch 2.13（CUDA 默认轮子）与 torch 2.11+cu128 及其 nvidia-* 依赖体积 `UNKNOWN`，合并 bf16（≈ base）、F16/BF16 GGUF 中间件（≈ 4 GB）、Q4_K_M（≈ 1.1 GB）、mmproj（≈ 0.82 GB）为〔估〕，AWQ 检查点 `UNKNOWN`。故 20 GB **未证足够也未证不足**，不报新数；新推荐 = 镜像固定后，按每 venv「逐包固定版本 × 公开文件字节」之和 + 失败重取预留，另加模型/中间件峰值，由接受换算后交 B-SIGN。
- **先导只读云预检**（B-CLOUD 选「租后第一步」时才用；计入 GPU·h/费用/消耗轨道；须用户另签，不等于整个 B）：用户在控制台按 B-CLOUD 所报规格创建实例并提供 SSH 目标/端口/主机指纹核对方式；Mac mini 执行，`UserKnownHostsFile` 指向本次输出目录，不改 `~/.ssh`；整体 ≤ 600 s，结束即停：

```sh
OUT="outputs/eng-jet/P1-ENG-JET-001/stageb-cloudprecheck-$(date -u +%Y%m%dT%H%M%SZ)"; mkdir "$OUT" || exit 1
/usr/bin/perl -e 'alarm 600; exec @ARGV or die "exec failed: $!\n"' \
  /usr/bin/ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$OUT/known_hosts" \
  -o ConnectTimeout=20 -o ServerAliveInterval=10 -o ServerAliveCountMax=3 -o ControlMaster=no -o ControlPath=none \
  -p <用户提供端口> <用户提供目标> '/usr/bin/timeout -k 5 540 /bin/sh -s' > "$OUT/cp.stdout" 2> "$OUT/cp.stderr" <<'CP'
export LC_ALL=C
r() { t=$1; l=$2; shift 2; printf '### %s\n' "$l"; timeout -k 2 "$t" "$@" 2>&1; printf '### rc=%s\n' "$?"; }
r 8 os cat /etc/os-release
r 8 kernel uname -srm
r 8 glibc getconf GNU_LIBC_VERSION
r 30 gpu nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv
r 30 smi nvidia-smi
r 8 nvcc sh -c 'command -v nvcc || ls -d /usr/local/cuda*/bin/nvcc; nvcc --version || /usr/local/cuda/bin/nvcc --version'
r 8 pythons sh -c 'for p in python3 python3.10 python3.11 python3.12 python3.13; do printf "%s: " "$p"; command -v "$p" || echo MISSING; done'
r 8 py python3 -I -S -B -c 'import sys; print(sys.version); print(sys.prefix)'
r 60 dists sh -c 'ls -1d /usr/lib/python3*/dist-packages/*info /usr/local/lib/python3*/dist-packages/*info /usr/local/lib/python3*/site-packages/*info /opt/conda/lib/python3*/site-packages/*info 2>/dev/null | sed "s#.*/##" | sort'
r 8 container sh -c 'cat /proc/1/cgroup; ls -la /.dockerenv'
r 8 tools sh -c 'for b in cmake gcc g++ make ninja git; do printf "%s: " "$b"; command -v "$b" || echo MISSING; done'
r 8 trt sh -c 'ls -1 /usr/lib/x86_64-linux-gnu/libnvinfer.so*'
r 8 nproc nproc
r 8 mem free -b
r 8 df df -B1 / "$HOME"
r 8 addr ip -br addr
printf '### end\n'
CP
echo "$?" > "$OUT/cp.rc"
```

不跑 pip（避免版本自检外联与缓存写入）、不导入模型、不写缓存、不安装。预检与 B-CLOUD 所报不符 → 停、保留原文、由用户销毁实例；相符但阶段 B 主信封未在预检结束前签发 → 同样由用户销毁，不留待复用。**先导封顶形状**（数值待报价后由接受换算，现不申请）：计费时长 ≤ 0.5 h × 报价时价 + 存储最小计费单位 + 流量（预检出流量仅 KB 级）；销毁截止 = 预检输出返回后由用户在约定分钟内执行并回报；超出即停。

##### BP-4 AWQ 校准、官方 GGUF 身份与传输/峰值

- **固定 tag 校准事实**〔码 Q4〕：`--quantization int4_awq` → ModelOpt `INT4_AWQ_CFG`（awq_lite）；模型有视觉模块且算法非 `max` 时 `_is_image_blind_calibration` 为真，**自动走多模态校准**：图像集生成器逐条产 `(image, question)`（image 可为 PIL/本地路径），经处理器 `apply_chat_template`（单条 user 消息：先图后文，`add_generation_prompt=True`），**样本数 = min(`--num_samples` 缺省 512, 128) = 128、batch 1、按生成器顺序（无 shuffle）、该分支不截断**（文本 `max_length 512` 只用于纯文本分支）；文本集在此分支不使用。`--visual_quantization` 只有 fp8（Orin 不跑 fp8），不设即视觉塔保持 FP16 —— **FP16 视觉塔无单独校准或导出步骤**，图像只用于标定 LLM 的 AWQ 缩放；量化器 `--dtype` 只接受 fp16，C2 合并 bf16 以 fp16 载入标定。自定义数据不需改包：Python API `quantize_and_export(..., quantization="int4_awq", image_dataset=<生成器>)` 直接接受可调用对象〔码 Q4〕。**更正** #### 6「MMMU 字段与样本数/序列长 UNKNOWN」→ 字段/样本数/批次如上已核；序列长 = 处理器输出长度（不截断）：640×480 帧在 SFT-002 处理器下网格 `[1,30,40]`〔证 `-train-summary.json`「image_grid」2,327 帧 0 不符〕，即 300 图像 token + prompt v2 文本；量化 venv 的 transformers 5.14.1 处理器是否同网格 `UNKNOWN`（装后核，不符即停）。prompt v2 的 `build_prompt` 本身就是「单条 user：图 + 文」〔码 `tools/eng_sft/prompt_v2.py`〕，与校准消息结构一致。
- **train 确定性选择规则（供用户定，B-CALIB；本轮未采样）**：候选 = 数据根 SFT-002 `data/train.jsonl`（4,907 行 / 3,198 个 `frame_id` / 1,613 个互异 `frame_sha256`〔本机，字段计数〕）；排除 `frame_sha256` ∈ smoke（25 张，**全部落在 train 内**〔本机〕）∪ eval（交集 0）∪ select-eval（交集 0）；按 `frame_sha256` 去重，每图取 `sample_id` 最小的一行的 `surface`；推荐另排除 a7 预热帧 `frame_0000000000/100/200`（train 含其中 0 号帧〔本机〕）及 a7 前 320 帧（快层回放窗口，train 含 100 张〔本机〕），属清洁性而非评估泄漏；按 `sha256("p1-eng-jet-001-calib-v1" ‖ frame_sha256)` 升序取前 128；question = `build_prompt(path, surface, g4)["text"]`（g4 取法同 SFT-002 训练行）。近重复约束沿 SFT-002：train/select 与 test、unassigned 不交且与 eval 按 sha 不交〔证 `-leakage-report.json`「assertions」〕；同会话近邻帧不额外剔除（会话级划分已隔离 eval）——若用户要更严，可再按 `family` 排除 eval 所在会话族。只传 128 帧 JPEG + 剥字段清单（`frame_sha256`、`surface`、`g4`；无 `target_*`/`state`/gold），帧约 6.0 MB〔估：train 帧绑定 150,188,287 B / 3,198 × 128〕。评估/smoke/gold 永不上云；原「云端零评估/smoke/gold 数据」保持；「云上无推理」**区分**：无正式评估推理，但 AWQ 校准对 128 条本域样本做前向计算（属 K4，计 GPU·h）。官方 `cnn_dailymail`/MMMU = 新下载类别，不推荐。
- **官方 GGUF 身份（下载申请前固定）**〔公 Q7，HTML 页面〕：文件名 `Qwen3VL-2B-Instruct-Q4_K_M.gguf`、`mmproj-Qwen3VL-2B-Instruct-F16.gguf`（同仓另有 F16/Q8_0 主体与 Q8_0 mmproj，不申请）；blob 页显示 SHA256 字段与四舍五入体积（1.11 GB / 819 MB）；仓库许可 Apache-2.0；存储为 Xet。**精确字节在页文本中未给出**，且固定修订须取页面最新提交 → 执行前由执行派发在 blob 页（固定到当时提交的 `blob/<提交>/<文件>` URL）读 SHA256 写入 `-assets.json` 期望值；字节以完整取回后实测为准、失败字节计入；若用户要求申请前已知精确字节，则由用户提供（不用 HF API/HEAD/Range GET）。
- **自产 mmproj**：按 AC-11 修订 2 缺省由合并产物同 tag `convert_hf_to_gguf.py --mmproj` 自产 F16，≈ 0.82 GB〔估，同架构官方件〕；计体积/峰值/传输，不算外部下载。
- **双向传输与峰值（〔估〕，不作额度）**：Mac→云：base ≈ 4.27 GB + adapter 69,788,264 B〔证 train-summary〕+ 校准 ≈ 6 MB + 代码束；云→Mac：C2 Q4_K_M ≈ 1.1 GB + 自产 mmproj ≈ 0.82 GB + AWQ 检查点 `UNKNOWN` + 收据/日志；合并 bf16 与 GGUF 中间件留云随销毁（如要回传另加 ≈ 4.3 GB）。故云↔Mac 双向 ≈ 6.2 GB + AWQ 检查点，能否容入 10 GB 取决于后者。Mac→板：官方 GGUF 两件 ≈ 1.93 GB、C2 两件 ≈ 1.9 GB、AWQ 检查点、llama.cpp 归档 `UNKNOWN`、W 路线轮子（≤ 2.68 GB 上限）及其依赖、盲文件与帧（eval 帧绑定 19,757,920 B〔证 dataset-manifest〕）。峰值：云盘见 BP-3；板盘 = 既有 `~/eng-jet` + edgellm-venv（解压 ≤ 5.1 GB 上限）+ llama.cpp 源码/构建 + 4 件 GGUF + AWQ 检查点 + 服务端引擎缓存（由 `--engine-cache-max-size-gb` 封顶）；Mac = 回传件 + Mac 侧取回件（若 B-DLLOC 选 Mac）。

##### BP-5 候选消费表对齐与回归/例外来源

| 维度 | 每候选（B1、B2 各） | 两候选合计 | 说明 |
|---|---|---|---|
| Mac mini 停点全套 | 1 | ≤ 2 | 不可互借；额外候选 0 |
| det-assoc CPU 加载 | ≤ 2 | ≤ 4 | `CarrierSelfTest` 两例 |
| NanoTrack 构造尝试 / 读权重 | ≤ 2 / 0 | ≤ 4 / 0 | |
| CSRT 构造尝试 / 实例 | ≤ 2 / 0 | ≤ 4 / 0 | |
| 零模型部分回放 | ≤ 2 × 60 帧 | ≤ 4 × 60 帧 | `ResidentCarrierReplay` |
| 墙钟 / outputs 增量 | ≤ 15 min / < 0.1 MB | ≤ 30 min / < 0.2 MB | |
| VLM/YOLOE/DINOv2/MPS/新增模型下载 | 0 | 0 | 新测试只许替身；替身 ≠ 全套零加载 |
| focused / 红绿的真实消费 | 0（推荐） | 0 | 不豁免计数；有具体需要另申请 |

**更正**：#### 7 表只列每候选上界，缺合计与「不可互借」；以上表为准（与「阶段B准备审核」§3 末行同值）。

- **新云入口 F7/F8 回归**（AC-10 修订 14：`tools/eng_jet/` 另写最小入口，不调用/复制 SFT runner、不修 SFT 债）：focused 须**真正执行**——模块不得导入 `tools.eng_sft.*`、`tests.fixtures` 或 `tests.test_language_selector`（这些在 Mac mini 全套中致 `test_eng_sft_{audit,build,cloud,evaluate}`、`test_language_k_binding` 导入错误〔证 #### 7〕），运行日志须列出这些用例为已执行（非 skip/非导入错误）。覆盖：F7 —— 入/出流量 GB、存储与时长参数为负、NaN、inf 时启动前拒绝（固定退出码、不建实例、不联网），上限常量参数化到本项已签值而非 SFT 的 8 GPU·h/6 美元；F8 —— 看门狗与主线程并发写收据用进程内锁或唯一临时名 + 原子替换，测试用线程屏障强制交错并断言最终收据可解析且含停止记录。新入口无「修前」版本，红绿改为**负对照**：同一测试对一个故意不加锁的替身写入器须判失败，证明检出力。
- **SUB:6 保留**：`tools/eng_jet/ledger.py` 无 SUB:6 维度（`docs/reviews/P1-ENG-JET-001.md`「R2@K1K3K4」§5 / C3-P3）→ 阶段 B 任何 `ledger build` 重跑前，B1 须先补 SUB:6 块与阶段 B 新维度的保留支持并有回归。
- **两项例外的确切来源**：账本 2026-10-03「P1-ENG-JET-001 — 用户裁定线 A 全套结果：Carrier CPU 失败选 A（具名例外进 C1/R1）、scene006 29 条按环境原因分列（supervisor 会话代录）」授权范围 (1)(2)；对 SUB:6 新候选由账本 2026-10-04「P1-ENG-JET-001 — 用户签发 SUB:6（新候选停点全套，方案 (a)）并为新候选重新具名 Carrier/scene006 两项例外（supervisor 会话代录）」(2) 重新具名；对 R2-1 窄修候选由账本 2026-10-04「P1-ENG-JET-001 — 用户选 (a)：R2-1 窄修候选以 focused 加 R2-1 修前红/修后绿代替停点全套、SUB:6 两项例外读法沿用（supervisor 会话代录）」(2) 沿用。三条均不延及 B1/B2 → B-EXC；仅同名同类，其他新增失败阻断，复核可判阻断。
- **U12/U13**：U12 候选未冻结，保持 `UNKNOWN`；冻结后跑前按实际树只读核可达加载/回放/构造次数，相异先回用户、不继承 skip。U13（含 W 路线 `runtime.load()` 载荷选中、服务端首建引擎、`cma`）只能实测；实际不兼容或需系统变更即停，系统设置 0，不要求预先证明性能。

##### 补写判定与交接受事项

**判定：BP-1…5 材料已补齐；仍非可执行闭集。** 剩余 `UNKNOWN` 分四类：(a) 需用户事实/授权 —— U1/U2/glibc/路由（B-PRECHECK）、U6（B-CLOUD）、U7（B-CLOUDDEP，另见 JB-6）、U8 精确字节（执行时读页或用户提供）、U10（B-CALIB）、U11（B-S4A）；(b) 只能实测 —— U9、U13、服务端首建时长、轮子实际字节（取回时）；(c) 候选冻结后 —— U12；(d) 接受合同解释 —— 下列 JB。U3 闭合（tag、开关、子模块 0、外联点）；U4 闭合 arch/子模块集/视觉构建方式，子模块字节 `UNKNOWN`（仅 S 路线）；U5 部分闭合（分发形式、本地加载、入口），留 JB-1…4。

| JB | 具名回接受（不自行换服务/容器/逐请求 CLI） |
|---|---|
| JB-1 | 服务端只收检查点、自行在板上建 LLM+visual：AC-7 修订 2「消费本地板建 LLM/视觉组件」是否读作「服务端内部直接构建器在 `--cache-dir` 内首建并单列冷启动」；云交付物随之改为 AWQ 统一检查点（不导出 ONNX）。 |
| JB-2 | 视觉编码嵌入缓存在 v0.11.0 服务端不可关闭：与「视觉缓存关闭」不相容。可选读法（不代选）：(i) 保持服务端，按 INFO 命中日志判 `CACHE_SUSPECT`，首见 25 行与 S5 180 帧本就互异，重复 7 行只作缓存核查且预期命中；(ii) 3c 记 `NOT_RUN(PATH_UNAVAILABLE)` 回用户；(iii) 改低层 Python 运行时入口——是否暴露预算 `UNKNOWN`，需再读。 |
| JB-3 | 图像 token = 300 的核对出口：无逐图字段；候选读法为「同 prompt 有图/无图 `count_tokens` 之差减视觉起止特殊 token」或读服务端写出的 `visual/preprocessor_config.json` 与 `--max-image-tokens` 约束，需接受定口径。 |
| JB-4 | `server-tools`（`transformers==5.14.1` 及其传递依赖）是否进板端闭集。 |
| JB-5 | 3c 分发：W 发布轮子（推荐）或 S 源码；S 时构建隔离四件与 `--no-build-isolation` 处理。 |
| JB-6 | 传递闭集取数方法：PyPI 网页有浏览器质询，未绕过；是否允许零消耗只读 PyPI JSON 元数据（不取文件、不跑解析器）按固定版本逐包列 `Requires-Dist` 与文件字节，或改由用户提供。 |

接受核清更正：上述“U3闭合”仅指tag/开关/子模块，不含源码精确字节与未读外联分支；U8不能先签下载再取回探大小。JB与本节命令的现行裁定见追加「阶段B补写核清」，用户入口仍仅「阶段B准备审核」§5。

用户待决仍只在「阶段B准备审核」§5；本节对其各行只补材料、不改推荐：B-PRECHECK ← BP-1 命令与副作用清单；B-APT ← W 路线下仅 llama.cpp 需 `cmake`/`build-essential`，S 路线另加 TRT dev 包；B-DLLOC ← 取回项 = llama.cpp 归档 1 + 官方 GGUF 2 + 板端轮子（W）及其依赖，取回地点含板端轮子；B-CLOUD ← BP-3 先导命令与封顶形状；B-CLOUDDEP ← BP-3 每 venv 直接清单与 JB-6；B-CALIB ← BP-4 规则（128 张、排除集、≈ 6 MB 上云）；B-SIGN ← BP-2/3/4 体积与计数重算说明。**无 §5 未覆盖的新用户事项。**

### 阶段B补写核清（2026-10-04，CLARIFY）

登记轮次 `阶段B补写核清`；Dispatch-Id `P1-ENG-JET-001-阶段B补写核清-20261004T054439Z-7c75`；Acceptance，仅核清「阶段B依赖闭集准备」#### 11 与合同/推荐。**结论：BP-1…5 经下列文档勘误已完成本轮静态材料义务，交用户「阶段B准备审核」§5；仍非完整可执行闭集。** 不再退构思一轮，不重开 D2/C/R；未知环境/元数据须用户提供或另签先导核验，U9/U13 待已签有界实测、U12 待候选冻结，不要求预先成功实测。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE` 保持；B全部生效值0、S1/S2 STOP、SR5/5耗尽、补丁未上板、R1-5/6 OPEN、AC-7/8/9未运行保持，不签DONE。

#### 1. BP逐条核清与勘误

| ID | 核清结果及差异闭合 | 保留限制 / 材料指针 |
|---|---|---|
| BP-1 | 满足（采用本节§3更正版）。####11已列机器/路由/无site解释器/副作用/单项与远端截止；但原r函数丢弃返回码且超时后继续，Mac alarm只包ssh、取Host的Python仍跑site。§3用本机标准库统一全程计时/取Host/收尾，单项超时立即退出，普通缺项保留UNKNOWN后继续同一次只读扫描，原命令不再发令。 | U1/U2/glibc/路由尚无新读数；缺项及其后未执行项UNKNOWN，不sudo/重试/再登录；B-PRECHECK。 |
| BP-2 | 满足静态材料义务。固定tag子模块/外联点/Orin载荷、服务入口与不可关缓存均已具名；JB-1/3/4/5见§2，JB-2不能由解释改为可忽略。未取回的逐文件元数据仍UNKNOWN，不称完整依赖闭集。 | ####11 BP-2；W不取Edge源码/子模块，llama未读分支仅离线失败即停；板下载/安装0。 |
| BP-3 | 满足（采用§3更正版云预检）。三venv直接依赖与镜像事实已分列，36是原清单计数、不是最终安装数；原云命令known_hosts未填且r函数超时继续，现由用户提供已核指纹文件、全程计时与失败收尾。20GB未证足够，12包/3GB撤下。 | ####11 BP-3；镜像/报价/ABI/传递pin未核，先导仍须明确价格、计费最小单位、截止与销毁责任，云主案0。 |
| BP-4 | 满足材料义务；128张/单批/不截断/本地生成器、自产mmproj与峰值已列。更正“签后才读官方身份/字节”：签下载前固定页上身份，精确字节缺失由用户提供，不能由取回后实测替代签前事实。sha不交不等于近重复隔离，SFT泄漏报告仅证sha/划分断言，不证“会话已隔离eval”；B-CALIB供用户定近邻排除规则。 | ####11 BP-4；smoke25张全在train，必须显式排除；评估/select-eval/smoke/gold永不上云；U8/U10/U11未闭。 |
| BP-5 | 满足。B1/B2每候选与合计吻合§3；新入口F7/F8 focused真正执行、无锁负对照/SUB:6保留回归与三条例外来源齐。 | ####11 BP-5；不签测试通过；冻结后只读核真实加载/回放计数，差异先回用户，旧例外不延长。 |

本轮仅读已有提案/账本/工程继承清单、缺陷账本、SFT-002复核F7/F8、数据/泄漏摘要与设计§8；未采样、未重新算帧或模型哈希。另读取固定tag[服务文档](https://raw.githubusercontent.com/NVIDIA/TensorRT-Edge-LLM/v0.11.0/docs/source/user_guide/examples/experimental-server.md)、[安装文档](https://raw.githubusercontent.com/NVIDIA/TensorRT-Edge-LLM/v0.11.0/docs/source/user_guide/getting_started/installation.md)与[官方GGUF文件页](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct-GGUF/blob/main/Qwen3VL-2B-Instruct-Q4_K_M.gguf)。公开文档支持检查点直建、W/可选server-tools；轮子size_budget与部分源码本轮网页未取到，仅沿####11 Q1…Q5的已提交准备读数，不宣称独立复证。GGUF页只有舍入体积，U8精确字节仍UNKNOWN。无API/HEAD/Range GET/质询绕过、无任何取回/预检/ssh/安装/租云/模型/回放/SR/实现测试；仅收工自检。

#### 2. JB裁定与追加合同解释

| JB | 裁定 / 归因 | 唯一后续入口 |
|---|---|---|
| JB-1 | 合同解释：服务首启在板内cache-dir直接建LLM+visual即“本地板建”，权重从本地AWQ统一检查点加载；云不导出ONNX，不传已有引擎。构建/冷启动与加载单列、失败不宣称Orin已兼容。 | AC-7修订3；§3推荐重算与B-SIGN |
| JB-2 | 视觉编码缓存不可关与现行无缓存合同不相容；INFO只能证明单图全部命中，不能将其写成关闭证据。保留服务并允许有界缓存属于取样/读数合同例外，不能自行CLARIFY放宽。推荐及不答缺省并入B-CACHE，不选择低层绑定或逐请求CLI。 | 「阶段B准备审核」§5 B-CACHE |
| JB-3 | 不接受“有图/无图count_tokens差减未知特殊token数”或仅max-image-tokens上限作为300的证明。要求实际预处理grid与merge规格可追溯，配置/入口只是约束；缺运行时出口则token UNKNOWN，不把usage总token当图像token、不许该路径进S4。 | AC-7修订3；可测未知U5/U13，B1须先给可核的出口；不改变grid |
| JB-4 | W路线不安装server-tools/transformers：固定tag安装文档将其列为可选参考工具，W server入口不需PyTorch/ONNX exporter。本地检查点直建缺能力则PATH_UNAVAILABLE并回接受，不补包发现依赖、不改用源码。 | AC-7修订3；板端直接8项仍需传递闭集 |
| JB-5 | 选择W发布轮子（解释现有分发/绑定），独立venv暴露系统TRT、numpy遮蔽仅限该venv；S源码不选，板端Edge源码/子模块/构建隔离取回0。不以W资格行代替装后载荷选择实测。 | AC-7修订3；B-DLLOC/B-SIGN，资源仍须用户签 |
| JB-6 | 未授权改取PyPI JSON；遇网页质询不绕过、不改端点探取同一受限材料。本轮不将其判为可执行元数据路径；需用户提供固定版本平台文件/Requires-Dist/字节身份，或用户具名其他无质询的官方公开文本来源，由接受核清后静态闭集。 | 合入B-CLOUDDEP（同时含板W闭集）；不是另建清单 |

| 编号 | 现行解释与归因 | 证据指针 | 停点 | 日期 |
|---|---|---|---|---|
| AC-7 修订 3 | CLARIFY（解释修订2、§3.3；来源构思JB-1/3/4/5及BP-2）：3c固定W、tensorrt-edgellm[server]==0.11.0、独立edgellm-venv用系统TRT，不装server-tools/torch/export、不取Edge源码；loopback本地检查点常驻服务在cache-dir内首建LLM+visual，cloud仅交AWQ统一检查点，建引擎计板端墙钟/峰值并冷启动单列。缓存例外未答前不得以该服务签无缓存有效读数。图像300须实际grid[1,30,40]及spatial_merge_size=2/等价原生预处理证据，不用总usage差或容量上限冒充；无出口保持UNKNOWN，S4不执行，已证非300沿GRID_MISMATCH。3b增加LLAMA_LLGUIDANCE=OFF及CMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc，只建llama-server；云同tag CPU建llama-quantize，转换用树内gguf-py不另装pip gguf，其余tag转换依赖仍须闭集。 | artifact: 准备稿####11 BP-2/JB、本节§1–2；未来-vlm.json/-env.json | K1K3K4 | 2026-10-04 |
| AC-10 修订 15 | CLARIFY（解释修订14、§5；来源BP-1/3及JB-6）：未来只读先导只用本节§3更正版，不执行准备稿旧RP-1/云块；一次预检的失败/超时不重试，原输出/单项rc/整体rc保留，缺或未执行项UNKNOWN，不import第三方、不改系统。用户签前元数据不足的下载/安装/传输维度0；公开舍入体积/size_budget不是实际文件字节，不先签下载再取回探大小。Mac取回、板离线安装、云每venv安装数、唯一取回件及失败重取字节分别累计；W只撤Edge源码，不撤llama与云CPU构建工具前置。 | artifact: 本节§1/3、「阶段B准备审核」§3/5；未来-ledger.json/-assets.json | K1K3K4 | 2026-10-04 |
| AC-8 修订 3 | CLARIFY（解释修订2及AC-12；来源BP-4）：AWQ校准在云按fp16加载C2合并bf16作前向标定，仅本地派生生成器，不取缺省HF数据集；选本域仍待B-CALIB确定128张/选择和隔离规则并签train传输。无独立FP16视觉塔校准/ONNX导出，不将“云上无正式评估推理”误写为无校准计算。eval/select-eval/smoke/gold不得校准或传云；SFT旧sha不交证明不升级为近重复/会话隔离证明。 | artifact: 准备稿####11 BP-4、SFT-002-leakage-report.json；未来-assets.json | K1K3K4 | 2026-10-04 |

归因：3条追加修订均解释已有AC，来源为本轮指定BP核清与构思JB请求；新增AC=0，不是C轮读码增项。JB-2缓存例外、校准选择、元数据访问/用户事实及全部资源额度未由接受代定。

#### 3. 只读预检文档命令更正版（尚未授权、从未执行）

本块替代####11 BP-1与BP-3两块发令文本；只在未来具名签发后执行。Mac mini全程板≤300s/云≤600s，计时包含取Host、目录、ssh和记录；本机超时杀本次SSH进程组、远端timeout自行收尾（板连接最多15s+远端270s+强杀5s≤290s；云15+540+5≤560s），不二次登录验证。单项超时保存rc立即结束，其后未执行项UNKNOWN；普通缺包/权限/路径错误保存rc及UNKNOWN后继续同一次只读扫描、不重试，末尾整体rc非0。命令返回0也不证所有事实已核，tools块的MISSING与缺metadata等必须逐字段标UNKNOWN。stdout/stderr不混入摘要、整体rc与本机异常另存；没有timeout/Python/权限则原错返回，不安装补足。Mac只读标准库、禁止site/.pth；SSH/PAM/日志/wireplumber/atime副作用按BP-1披露。目录仅在Mac、UTC名运行时生成，已有即停。云目标/端口/已核主机指纹文件由用户提供，文件只复制入本项输出目录；无可信文件则不登录，不做keyscan或TOFU。

```sh
# Mac mini 主树根；板端用 board。云端同一模板把参数改为：
# cloud '<用户提供SSH目标>' '<用户提供端口>' '<用户核过指纹的known_hosts文件>'
# 不执行模板；仅在对应用户授权入账且接受落实后由下一派发执行。
python3 -I -S -B - board <<'LOCAL_PRECHECK'
import datetime, json, os, pathlib, signal, subprocess, sys, time
started = time.monotonic()
mode = sys.argv[1]
if mode not in ("board", "cloud"):
    raise SystemExit("invalid mode")
limit, ssh_budget, remote_limit = (300, 285, 270) if mode == "board" else (600, 575, 540)
proc = None
out = None
rc = 1
def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
def expired(signum, frame):
    raise TimeoutError("whole-precheck deadline")
signal.signal(signal.SIGALRM, expired)
signal.alarm(limit - 5)
BOARD_READINGS = r'''export LC_ALL=C PATH=/usr/local/cuda/bin:/usr/sbin:/usr/bin:/sbin:/bin
r() { t=$1; l=$2; shift 2; printf '### %s\n' "$l"; timeout -k 2 "$t" "$@" 2>&1; rc=$?; printf '### rc=%s\n' "$rc"; case "$rc" in 124|137) exit "$rc" ;; 0) : ;; *) missing=1; printf '### UNKNOWN=%s\n' "$l" ;; esac; }
r 8 user id -un
r 8 os cat /etc/os-release
r 8 l4t head -n 1 /etc/nv_tegra_release
r 8 glibc getconf GNU_LIBC_VERSION
r 8 tools sh -c 'for b in cmake gcc g++ cc c++ make ninja git curl aarch64-linux-gnu-gcc aarch64-linux-gnu-g++ nvcc python3 python3.12; do printf "%s: " "$b"; command -v "$b" || echo MISSING; done'
r 8 cmake_v cmake --version
r 8 gcc_v gcc --version
r 8 gxx_v g++ --version
r 8 nvcc_v nvcc --version
r 20 dpkg dpkg-query -W -f='${Package} ${Version} ${db:Status-Abbrev}\n' cmake build-essential gcc g++ make ninja-build git libssl-dev cuda-toolkit-13-2 tensorrt libnvinfer-dev libnvinfer-headers-dev libnvinfer-plugin-dev libnvonnxparsers-dev python3-libnvinfer python3-libnvinfer-dev python3.12-venv python3-numpy python3-pip
r 8 trt_headers ls -l /usr/include/aarch64-linux-gnu/NvInfer.h /usr/include/aarch64-linux-gnu/NvInferVersion.h /usr/include/aarch64-linux-gnu/NvOnnxParser.h
r 8 cuda_dirs ls -ld /usr/local/cuda /usr/local/cuda/targets/sbsa-linux /usr/local/cuda/targets/aarch64-linux
r 8 sys_py_pkgs ls -d /usr/lib/python3.12/dist-packages/tensorrt /usr/lib/python3/dist-packages/numpy
r 8 sysvenv_cfg cat "$HOME/eng-jet/sysvenv/pyvenv.cfg"
r 8 sysvenv_numpy sh -c 'ls -d "$HOME"/eng-jet/sysvenv/lib/python3.12/site-packages/numpy* 2>&1'
r 8 py_sys /usr/bin/python3 -I -S -B -c 'import sys; print(sys.version); print(sys.prefix)'
r 8 py_venv "$HOME/eng-jet/sysvenv/bin/python" -I -S -B -c 'import sys; print(sys.version); print(sys.prefix, sys.base_prefix)'
r 8 nproc nproc
r 8 mem free -b
r 8 swap swapon --show --bytes
r 8 df df -B1 / "$HOME"
r 60 du du -sb "$HOME/eng-jet"
r 8 addr ip -br addr
r 8 route4 ip -4 route show
r 8 route6 ip -6 route show
printf '### end\n'
exit "${missing:-0}"
'''
CLOUD_READINGS = r'''export LC_ALL=C
r() { t=$1; l=$2; shift 2; printf '### %s\n' "$l"; timeout -k 2 "$t" "$@" 2>&1; rc=$?; printf '### rc=%s\n' "$rc"; case "$rc" in 124|137) exit "$rc" ;; 0) : ;; *) missing=1; printf '### UNKNOWN=%s\n' "$l" ;; esac; }
r 8 os cat /etc/os-release
r 8 kernel uname -srm
r 8 glibc getconf GNU_LIBC_VERSION
r 30 gpu nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv
r 30 smi nvidia-smi
r 8 nvcc sh -c 'command -v nvcc || ls -d /usr/local/cuda*/bin/nvcc; nvcc --version || /usr/local/cuda/bin/nvcc --version'
r 8 pythons sh -c 'for p in python3 python3.10 python3.11 python3.12 python3.13; do printf "%s: " "$p"; command -v "$p" || echo MISSING; done'
r 8 py python3 -I -S -B -c 'import sys; print(sys.version); print(sys.prefix)'
r 60 dists sh -c 'ls -1d /usr/lib/python3*/dist-packages/*info /usr/local/lib/python3*/dist-packages/*info /usr/local/lib/python3*/site-packages/*info /opt/conda/lib/python3*/site-packages/*info 2>/dev/null | sed "s#.*/##" | sort'
r 8 container sh -c 'cat /proc/1/cgroup; ls -la /.dockerenv'
r 8 tools sh -c 'for b in cmake gcc g++ make ninja git; do printf "%s: " "$b"; command -v "$b" || echo MISSING; done'
r 8 trt sh -c 'ls -1 /usr/lib/x86_64-linux-gnu/libnvinfer.so*'
r 8 nproc nproc
r 8 mem free -b
r 8 df df -B1 / "$HOME"
r 8 addr ip -br addr
printf '### end\n'
exit "${missing:-0}"
'''
try:
    planned = pathlib.Path("outputs/eng-jet/P1-ENG-JET-001") / ("stageb-" + mode + "precheck-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    planned.mkdir(exist_ok=False)
    out = planned
    (out / "started_utc").write_text(utc() + "\n")
    args = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", "UpdateHostKeys=no", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=10",
            "-o", "ServerAliveCountMax=3", "-o", "ControlMaster=no", "-o", "ControlPath=none",
            "-o", "ForwardAgent=no", "-o", "ClearAllForwardings=yes"]
    if mode == "board":
        if len(sys.argv) != 2:
            raise ValueError("board takes no target override")
        host = json.loads(pathlib.Path("docs/evidence/P1-ENG-JET-001-relay.json").read_text())["link"]["ssh"].split("，")[0].strip()
        remote = BOARD_READINGS
    else:
        if len(sys.argv) != 5:
            raise ValueError("cloud needs target, port, trusted host-key file")
        host, port, trusted = sys.argv[2:]
        if not port.isdecimal() or not 1 <= int(port) <= 65535:
            raise ValueError("invalid port")
        # 用户须已核此文件与云控制台指纹相符；不做keyscan、不改~/.ssh。
        (out / "known_hosts").write_bytes(pathlib.Path(trusted).read_bytes())
        args += ["-p", port, "-o", "UserKnownHostsFile=" + str(out / "known_hosts")]
        remote = CLOUD_READINGS
    if not host or host.startswith("-") or any(c.isspace() for c in host):
        raise ValueError("invalid SSH target")
    args += [host, "/usr/bin/timeout -k 5 " + str(remote_limit) + " /bin/sh -s"]
    remaining = ssh_budget - (time.monotonic() - started)
    if remaining <= 0:
        raise TimeoutError("no SSH time remaining")
    with (out / "precheck.stdout").open("wb") as stdout, (out / "precheck.stderr").open("wb") as stderr:
        proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, start_new_session=True)
        proc.communicate(remote.encode(), timeout=remaining)
        rc = proc.returncode
except (TimeoutError, subprocess.TimeoutExpired) as error:
    rc = 124
    if out is not None:
        (out / "local-error.txt").write_text(str(error) + "\n")
except Exception as error:
    if out is not None:
        (out / "local-error.txt").write_text(type(error).__name__ + ": " + str(error) + "\n")
finally:
    if proc is not None and proc.poll() is None:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=3)
    if out is not None:
        (out / "precheck.rc").write_text(str(rc) + "\n")
        (out / "ended_utc").write_text(utc() + "\n")
        (out / "elapsed_s").write_text(str(time.monotonic() - started) + "\n")
    signal.alarm(0)
raise SystemExit(rc)
LOCAL_PRECHECK
```

先导云实例计费从用户创建到销毁（不只600s命令）：报价后总先导≤0.5h形状与本项总≤2GPU·h/≤4美元封顶合算，并含存储最小计费单位/流量；用户必须给具体销毁截止UTC/负责回报。超额预测不创建；读数不符或结束时主信封仍未签则用户销毁，不等待审批保留实例。源模板不含租用/销毁操作、不授权任何额度。

#### 4. 交接判定

原BP材料义务已闭合，本轮纠正的命令/推荐差异不需再让构思重复；尚缺环境读数、精确元数据、校准及缓存例外均已具名在「阶段B准备审核」§5。该表可先交用户选择与提供事实，随后接受逐项落实；**不能把“交用户”解释为签发整阶段B**。保留U3源码体积/未读隐式入口、U4/W文件身份、U5传递pin与token出口、U6/U7镜像依赖、U8下载身份精确字节、U9产物实测、U10校准、U11基准、U12候选、U13兼容；无来源事实不签相关维度。先导B-PRECHECK/B-CLOUD仅为engineering§9第一步通道，后续消费仍要B1 C/R与已签逐维度额度，租云仍等待FRAME自身释放轨道。

open_items: none

### 阶段B答复落实（2026-10-04，CLARIFY）

登记轮次 `阶段B答复落实`；Dispatch-Id `P1-ENG-JET-001-阶段B答复落实-20261004T044015Z-148b`。这是用户答复的合同落实及 COORD-017 补核，不是 D/C/R 轮或信封签发。依据 `docs/authorizations.md` 2026-10-04「P1-ENG-JET-001 — 用户答复阶段B:1–8：阶段B:2 改为 S5 判定档 5 Hz，其余按推荐（不签任何额度；本会话代录）」及「P1-ENG-JET-001 — 用户确认阶段B:2「冷启动单列」成立（本会话代录）」。原 AC、决策和申请保留；本节追加解释有冲突时仅约束未来阶段 B，不回改阶段 A 读数或 verdict。

#### 1. 八题落实与 AC 修订

| 原题 | 当前合同与归因 | 证明指针 / 停点 |
|---|---|---|
| B:1 = N-A | **AC-15 修订 1（CLARIFY，解释 AC-15、§5/§7(n)，关联 AC-13）**：认可带 S1/S2 双 `RESUMED_AFTER_USER_RULING` 申请阶段 B，具名替代「S0–S2 全 PASS」的申请前提。保留 S1 `STOP(FP16_BOX_DIVERGENCE)`、S2 `STOP(FRAME_DROP)`、原阈值/读数及 α/α′ 的各自授权边界；N-A 只解除申请前提，不放行执行。A收口:1 不适用，用户选择继续阶段 B；不关闭/暂停本项。 | artifact: 上述两条账本及本节；后续 `docs/evidence/P1-ENG-JET-001-ledger.json`「pending_user」 / K1K3K4 |
| B:2 = 5 Hz、首次 init 冷启动丢帧单列 | **AC-9 修订 1（CLARIFY，解释 AC-9、§2.1 S5，关联 AC-3/13）**：S5 快层判定档为运行时合同档 **5 Hz、640×480 帧、S1 同一方形 FP16 引擎、既有循环回放/丢帧算法**，持续 30 min。首次 init 的冷启动时长和丢帧独立报告，不进「无连续 >2 帧丢帧」线；从首次 init 完成后的稳态节拍计算该线，后续周期边界、update 或再次初始化造成的丢帧不得借首次冷启动豁免。分列冷启动丢帧、稳态总丢帧与稳态最长连续丢帧及起止时间；不凭总丢帧反推最长连续数。只排除首次 init 丢帧，不额外改写 update p95 取样口径。S2 15 Hz 原件不剔除冷启动、不改 STOP；S2 与新 S5 条件不同，禁止作同帧率热稳态改善结论。15 Hz 描述性压力读数是否另跑仍未定，该额外档的执行额度为 0。 | artifact: `docs/evidence/P1-ENG-JET-001-coresidency.json`（未来分列）；原 `-fastlayer.json`「S2」 / K1K3K4 |
| B:3 = 原 S1 方形基准 | 同 **AC-9 修订 1**：快层 p95 比较基准唯一为 `-fastlayer.json`「S1.square.latency.update_p95_ms」（n=320，原读数，不重新选基准），公式保留 **≤2×该基准且≤100 ms**；不取矩形或 S2 最好格。公式由用户 B:3 具名确认，基准来自本板同引擎真实单测；S1 的一致性 STOP 不抹掉此时延读数，亦不变为 PASS。 | artifact: `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1.square」及未来 `-coresidency.json` / K1K3K4 |
| B:4 = I-A | **AC-10 修订 13（CLARIFY，解释 AC-10、§5、§7(i)，关联 AC-11/15）**：量化主机路线选 x86 Linux GPU 租云（同 SFT-002 的 vast.ai 类、建议显存≥24 GB），在同一实例合并 C2、转 GGUF、做 AWQ；实例/软件环境与现价未核，主机选择不是租赁/安装授权。阶段 B 申请主案采用本节 §4 的逐维度清单，全部生效值仍 0；不复用其他 work item 信封。 | artifact: 本节 §4；未来 `docs/evidence/P1-ENG-JET-001-ledger.json` / K1K3K4 |
| B:5 = J-A | 同 **AC-15 修订 1**：§7(j) 已答复为跳过 S3a，不为 3a 下载或传 base 上板，记 `NOT_RUN(待用户 (j))` 时须补充「已答复 J-A，选择不做」而不能写仍未答复；AC-7 中该路径不记满足。本机 base 仅供选定量化主机在签额度后核身份使用；base 下载=0、Mac 合并/转换/模型加载=0。 | artifact: 账本 B:5、本节；未来 `-vlm.json` 与 `-ledger.json.pending_user` / K1K3K4 |
| B:6 = 先零消耗准备，再逐维度签主案 | 同 **AC-10 修订 13**：按 §3 完成依赖闭集准备，接受角色复核申请后交用户逐维度签发 §4；估算不是额度，依赖未核实的维度不申请签发。下载/安装/传输/上板/租云/模型查询此时全部禁止；不借阶段 A 余量，不重建或改写 ledger，SUB:6 保留支持限制照旧。 | artifact: 本节 §3–4；构思准备写本提案具名小节 / K1K3K4 |
| B:7 = B-CAND-2 | **AC-14 修订 1（CLARIFY，解释 AC-14、§7.1，关联 AC-10/13）**：阶段 A 新候选的 C→R 路径已由 R3 通过及接受消费走完，阶段 B 另起稳定停点，不能以 A 候选通过验 B。按 engineering-workflow §4，含不可重跑消耗的代码先整理 K1K3K4 候选→四项自证→接受 C→独立 R，再作已签消耗；消耗产出证据另过 K1K3K4。新 C/R 轮号由既有记录运行时顺序确定，禁止重置或预签。各候选停点全套/模型/回放与复核额外实测额度待签，原具名全套替代与失败例外不自动延长；AC-14 `UNITY_NA` 须新候选复核附议。 | artifact: `docs/reviews/P1-ENG-JET-001.md`「R3@K1K3K4」、本节；未来同名 K1K3K4-handoff / K1K3K4 |
| B:8 = 等待 FRAME 释放消耗轨道 | 同 **AC-10 修订 13**：即使零消耗准备完成且用户签阶段 B，租云执行仍须等待 FRAME-001 的消耗轨道由其自身交接释放；不暂停/核销 FRAME、不推定并行破例仍有效。零消耗准备现在可交构思，不占第二条消耗轨道。 | artifact: `docs/current-status.md`「Active handoffs」 / K1K3K4 |

**AC-7 修订 1、AC-8 修订 1、AC-9 修订 2（CLARIFY，分别解释 AC-7/8/9 与 §2.1 S3/S4/S5）**：未来阶段 B 的线分类、比较对象及 STOP 触发按 §2 补核表；数值一律保留，不用描述性超线停止后续，不把描述性超线记通过。停止线的数值来源与运行条件不得被编译压力、厂商基准或冷启动替代。证据指针仍分别为 `artifact:docs/evidence/P1-ENG-JET-001-vlm.json`、`-quant-equivalence.json`、`-coresidency.json`，停点 K1K3K4。

**AC-13 修订 6（CLARIFY，解释 AC-13、§2.1 停止总则，关联 AC-7/8/9/15）**：报告逐线注明出处类别、对象/单位/分母、描述性超线与合同停止触发；现行与历史分列。每个 STOP 的阶段 B 缺省处置按 §2 表申请用户随信封确认；**未确认处置不生效，发生 STOP 仍沿原总则停止全部后续并回用户**，不自行改为记录后续跑。既有阶段 A STOP/恢复授权不回溯套用本次分类；S3–S5 当前仍 `NOT_RUN(阶段 B 信封未签)`、AC-7/8/9 不满足。证明：`artifact:docs/evidence/P1-ENG-JET-001-report.md`（未来）；停点 K1K3K4。

归因：8 个追加 AC 修订（AC-7/8/9 两条/10/13/14/15），均源于用户八题答复或其要求的 COORD-017 阶段 B 补核，非读码新增义务；新增 AC=0。本轮不写代码/测试/复核/账本，不跑实现测试或模型，不消耗任何维度，不改历史证据。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE` 保持，门只覆盖前一候选，不签 DONE。

#### 2. 阶段 B 通过线与 STOP 四项补核

出处闭集逐字采用 acceptance 角色细则：(1) 合同或物理硬约束；(2) 目标设备或目标数据上的真实试读；(3) 厂商标称或公开数字；(4) 移植自其他条件的既有限值。A3 估算/建议仅为来源链，不能由「曾写进 AC」就转成目标机实证；没有目标条件读数的 (3)/(4) 线在本次登记为描述性。下表约束未来阶段 B，不回改阶段 A 历史判定。

| 线 / 数值与比较基线 | 数值出处与类别 | 描述性 / 停止线；运行条件与处置 |
|---|---|---|
| S3 首见 p50≤1.6 s / p95≤2.5 s | (4)：A3 §3.2/§6 第3步，p50 对照 5060 HF eager 零样本 1,615 ms；p95 是同节探测建议，未找到本板 C2 目标条件试读。当前 smoke HTTP/MPS 读数与其条件也不一致。 | **描述性**；新帧首见25行、nearest-rank（p95第24个），每路径分别报告超线，不据此触发 VLM_OVER_LINE 或筛掉 S4/S5 对象。 |
| S3 峰值统一内存≤4.6 GB | (3)：A3 §1/§4 的官方 TRT 4,486 MB 等公开数字及 §6 第3步估算留量；token/输入/产物与本项不同，无本板 VLM 读数。 | **描述性**；GB十进制，实测峰值单位/范围要注明。超4.6 GB不单独 STOP；实际 OOM/无法完成推理仍属于不可执行。 |
| S3 解析失败0/32、图像token=300、cache_prompt=false | (1)：AC-7、§3.3 冻结解析/prompt/grid；(2)：§0事实8/9 的本机数据试读确定32行/25首见/7重复、640×480与[1,30,40]。 | **合同条件**；解析0/32用于可用路径判定；token不等于300则该路径 S4 `NOT_RUN(GRID_MISMATCH)`，不借压力档改网格。 |
| 3预热；第1次冷启动、加载时间；repeat中位<首见中位×0.5 | (1)：D2 AR1-1、AC-7/§3.3 的缓存排除取样合同，A3 §0/§3 的缓存风险输入；0.5是排除可疑缓存的合同判据，不是性能门。 | 冷启动/加载/repeat只描述。CACHE_SUSPECT 是读数无效标记，不能合入首见统计；修正重跑须在已签次数内，余量为0则回用户，不新增STOP码或静默跳过。 |
| S4 609行，各组\|Δ\|≤3 pp | 样本 (2)：§0事实7/§8，评估集609行/392互异sha；3 pp (4)：A3 §6 第4步的建议容差，被 D2 选作探测线，尚无本板量化真实差值。 | 609行是**合同条件**、不剔除行；3 pp 为**描述性比较线**，逐组计数/分母/差值保留，单凭此超线不触发 QUANT_NOT_EQUIVALENT，不记研究资格。 |
| S4 G5硬给框率不高于对应bf16；解析失败0/609 | (1)：AC-8 的三态行为/格式不退化合同；(2)：本项 C2 bf16 目标数据基准，§0事实7，G5原21/100。 | **合同停止线**；C2量化只对C2 bf16，官方base只对base bf16，后者未核基准时不得借C2代替。逐组分母/原始计数齐；任一此线失败→QUANT_NOT_EQUIVALENT。 |
| S4可执行对象 / S5对象 | (1)：§2.1/AC-8/9；S3同一产物/运行时可完整运行、解析过线、token=300、无缓存嫌疑；S4尚受自身STOP约束。 | 「S3过线」只读作有效的合同判定，不再含上述描述性速度/内存线；没有有效对象则NOT_RUN并给具体原因，不静默换产物。 |
| S5快层5 Hz、首次init丢帧单列；无连续>2帧稳态丢帧 | (1)：用户 B:2 与冷启动确认、AC-9 修订1，运行时5 Hz合同；640×480帧、同方形引擎。 | **合同停止线**；只排首次init冷启动丢帧，稳态连续>2帧→CORESIDENCY_OVER。15 Hz是待选描述性压力档，未签不跑；S2的218丢帧不能当S5连续数。 |
| S5快层p95≤2×S1方形原p95且≤100 ms | (1)：用户 B:3 逐字选定的公式；(2)：`-fastlayer.json.S1.square.latency.update_p95_ms`、n=320、本板同引擎实际基准；A3 §6 第5步是公式最初建议出处。 | **用户确认的合同停止线**；取交集、n与取样窗口单列。5 Hz共驻同引擎测量，不能称与S2压力档同条件；超线→CORESIDENCY_OVER。 |
| S5 VLM p95≤同一S3首见p95×1.3 | (4)：A3 §6 第5步的共驻容差建议，无本板同产物S3或S5读数；S3基准本身尚未实测。 | **描述性**；未来同一产物/运行时S3首见25行对S5前180互异sha，不跨产物借基准，不因倍率超线STOP。拿到S3读数不自动把1.3转成停止线。 |
| S5 30 min、每10 s一次、180互异sha | (1)：AC-9/§2.1 的共驻采样合同；(2)：§0事实7/§8 的392互异帧足够覆盖。 | **合同条件**；冷启动单列、稳态时间窗/计数可追溯；VLM冷启动不得混入180次分位数，次数仍计信封。快层首次init update取样按修订1，不自行剔除。 |
| S5峰值RAM≤7.0 GiB | (3)/(4)：A3 §4 总量投影与可见约7.4 GiB、§6 第5步留量建议；本板 `-env.json`「readings.free_m」只核可见总量/空闲，不是共驻试读。 | **描述性**；GiB=2^30 B，总RAM/进程RSS/统一内存分列；超7.0 GiB只记，不据此STOP或预签无OOM。 |
| S5无NvMap/OOM、swap使用0 | (1)：AC-9/§2.2 不改系统与共驻不得靠swap的合同约束；实际是否发生须目标板本轮证据。 | **合同停止线**→CORESIDENCY_OVER；dmesg须取得实际原文，IR-1的S0替代不自动推广；证据缺失停下回用户补录，不能当无OOM、不能自行sudo。 |
| 重入阶段B的环境/资产/隔离 | (1)：§2.2、AC-10/11/12/16、用户部署设备合同；(2)：既有S0/系统栈B只读与实跑快照，未验证的新工具/算子仍是假设。 | 环境事实不靠3预热或已装torch推定；不重跑S0–S2/SR，不以阶段B额度修环境。资产不符、泄漏、实际CUDA/TRT不兼容、缺权限/额度时立即停回用户，保留原错误，不新造STOP码。 |

**每个 STOP 原因码的缺省处置申请（随阶段 B 信封逐码确认）。** 下表写清「停止全部后续」或「继续哪些」，全部推荐前者，以避免未经验证的路径跨门；没有一种「超描述性线就STOP」的触发。阶段 A 已发生 STOP 不重判；阶段 B 环境检查遇到历史码时也不能自行重刷/重装/重跑。

| 原因码 | 阶段 B 触发边界 | 推荐缺省处置（待用户确认） |
|---|---|---|
| NOT_SUPER | 指定设备/配置不符（不据公开频率数字反推） | 停止全部阶段 B 后续；回用户核设备/重刷，不自行操作。 |
| FREQ_CAPPED | 指定Super环境发生实际封顶，旧1020 MHz/1.7 GHz出处A3 [N2]仅厂商参照，读数偏离本身描述 | 环境不符才停止全部后续回用户；纯厂商频率参照超线记录后继续，不自行锁频。 |
| NOT_HEADLESS | 运行时headless合同不成立 | 停止全部后续回用户；不执行isolate/改默认target。 |
| POWER_MODE_NOT_MAXN_SUPER | 指定功耗模式合同不成立 | 停止全部后续回用户；不改nvpmodel。 |
| IDLE_RAM_OVER | 旧1.2 GB来自A3 [R1/R2]公开其他条件；阶段B没有单独停止触发 | 只超旧参考线记录后继续阶段B已签步骤；若实际资源不可用而已报STOP，停止全部后续回用户。 |
| LATENCY_OVER | 历史S1/S2码不回改；阶段B不据移植速度参考线触发 | 如其他合同约束确已触发该STOP，停止全部后续回用户，不自行选更佳基准/改帧率。 |
| FP16_BOX_DIVERGENCE | 既有S1一致性STOP继承，不重测、不新触发 | 新STOP停止全部后续回用户；历史STOP只按已签α及B:1的N-A申请例外继承。 |
| THERMAL_THROTTLE | 历史S2码继承；阶段B若确证实际热降频而非正常动态频率 | 停止全部后续回用户；不锁频/改散热/重跑压力档。 |
| FRAME_DROP | 历史S2码保留；S5按修订1的稳态连续线失败归CORESIDENCY_OVER | 新STOP停止全部后续回用户；不得将α′当新STOP续跑授权。 |
| RELAY_INTEGRITY | 资产搬运/发布完整性真的失败；不扩大为新的SR运行 | 停止全部后续回用户；SR5/5耗尽，原「信封内返工重跑」无余额，不自行重跑或传补丁上板。 |
| KERNEL_PARAM_REQUIRED | 3c必须改cma等内核参数才可运行 | 停止全部后续（含其他路径/S4/S5）回用户；不改内核、swap、系统栈。 |
| VLM_OVER_LINE | S3所有已选路径均无法有效完成合同推理（解析失败/真实OOM等）；p50/p95/4.6 GB参考超线不触发 | 停止全部后续S4/S5回用户；个别图像路径不可用沿原PATH_UNAVAILABLE记NOT_RUN继续3c，不泛化成静默越过STOP。 |
| QUANT_NOT_EQUIVALENT | S4对应bf16的G5硬给框率增加或解析非0/609；单凭3 pp不触发 | 停止全部后续（含剩余S4路径/S5）回用户，附各路径已得差值，不另配方/调参。 |
| CORESIDENCY_OVER | S5快层公式、稳态连续丢帧、实际NvMap/OOM或swap合同线失败；1.3倍/7.0 GiB不单独触发 | 停止全部后续/追加尝试回用户，写峰值和时序图；不自动跑15 Hz或换产物。 |

比较线分类是按现行规则的合同补核；用户若希望把描述性线改成STOP，先需目标条件真实读数及新的明确裁定，不能只签一个数值。阶段 B 不把「通过描述性参考」称验收；所有额外步骤、失败/重试仍需非零信封。缺证/实际不兼容/资产不符等沿AC与原错误记录停下，不扩STOP闭集。

#### 3. B:6 零消耗依赖闭集准备与交接

**下一 Owner = Ideation（构思角色），范围仅本提案追加「阶段B依赖闭集准备」及本项状态板，零消耗。** 使用现有本机文件/账本/证据与只读公开官方文档作静态准备，交接受角色审合同/申请；不标ACCEPTED、不改AC或门值、不写实现代码/测试/工具。不得同时派写仓库角色；本轮不拉起子代理，由supervisor接力派发。

1. 为llama.cpp/Edge-LLM逐项列来源、版本/tag、构建命令、CUDA arch=87、系统Python/TRT/CUDA/torch复用项；按板端与云端分列**直接及传递依赖闭集**（包名/pin、平台/ABI、来源、已装/拟新增、下载地点、已知体积及出处；未知写UNKNOWN，不用估算冒充核实）。网络只允许读公开文档/源码文本及供应商公开说明，禁止模型/源码归档/轮子下载、HEAD/HF API/Range GET探大小、pip dry-run/report或依赖解析取回；不登录/创建云实例，不ssh取证或上板。
2. 沿既有 `-env.json`/`-assets.json`/`-relay.json` 核解释器、工具链、版本/架构支持、磁盘/RAM与链路事实。cmake/编译器等未有原读数则列为假设；云GPU/现价/预装环境未核，不把厂商推荐当实测。按engineering §9标出每个未知影响的维度，**未知闭合前相应维度不申请签发**；如需新只读远端预检，先列精确命令、机器、权限及零副作用边界交接受/用户安排，本次准备不执行它。
3. 固定官方base GGUF+mmproj F16、C2本机base/adapter来源与元数据核对计划；使用前sha从资产/来源运行时解析，不抄进手维护文档。不为base或Q8_0申请下载，不编译、不合并、不量化、不构造/加载模型、不回放、不运行测试/SR、无模型/API查询。仅拟字段剥离/搬运清单，不传输、不写数据根/主树runtime/板端目录。
4. AWQ校准输入与工具流程、base bf16的S4-a基准来源必须列清；不能把609评估/gold改作校准调参。若没有已接受的校准/基准闭集，列具体needs_user（推荐及理由），不自行采样/划分或新增AC。准备本机全套/模型/回放的逐候选静态消费清单，继承Carrier/scene006覆盖限制而不自动沿用旧例外。
5. 云作业控制入口若拟复用SFT-002，先读工程继承清单、该项parked台账与F7/F8债及原复核，列承接计划；不运行有债的预算/看门狗，不据同供应商借余额。明确阶段B源码/证据边界及不可重跑消费前的代码停点，SR追加0、补丁未上板，不能用旧SR验证补丁。

准备完成的闭集标准：上面列名的板端/云端依赖、工具链、下载/传输/占用、校准/基准及候选测试清单逐项有来源；缺项保留UNKNOWN和受影响的0额度，不称「完整可执行」。准备可先交可证部分及阻塞表→Acceptance→用户补事实/签发；不能为了写成闭集启动下载、安装、传输、上板、租云或查询。用户B:6授权的是静态准备，实际核未知设备事实与所有消费另按明确范围放行。

#### 4. 待用户逐维度签发的阶段 B 信封清单（推荐值与出处；生效均0）

清单承接10-03刷新包§4、用户B:4/5/6；每行独立签发，成功/失败/重试累计，GB十进制。估算仅为建议上限，闭集或目标环境假设未核的行保持**不申请签发**；本表没有授额。设备路线/准备方向已定，不代表设备使用或消费许可。

| 维度 | 推荐申请值 | 出处 / 签发前依赖 |
|---|---|---|
| 设备/阶段/Consuming | 阶段B S3–S5；同Jetson系统栈B+Mac mini+I-A x86 Linux GPU≥24 GB；租云yes，执行等待FRAME释放 | B:1/4/8、刷新包§4/5；板端/云端环境假设按§3先核。 |
| 模型下载（含失败重取） | ≤4条/≤7 GB，仅官方base Q4_K_M+mmproj F16；base与Q8_0=0 | §5原案、刷新包§4/6与J-A；文件身份/来源/已核体积先固定。 |
| 板上pip下载/安装 | 新增≤6包、累计下载≤1 GB，复用sysvenv torch/系统TRT；sudo/apt/重装torch/新容器=0 | 刷新包§4估算封顶；aarch64/Python3.12依赖闭集/工具链未核，当前不申请签发。 |
| 板上源码取回/构建 | ≤2归档/≤500 MB累计；llama.cpp编译≤1 h；Edge-LLM编译+建引擎≤3 h | §5/刷新包§4；tag、工具链与JP7.2兼容未核，当前不申请签发。 |
| 云GPU时间/总费用 | ≤2 GPU·h/≤4美元（含租金/存储/传输）；GPU工作=合并/AWQ/转换，训练=0 | §5/刷新包§4/5；现价/预装环境未知，推荐只在总费用可封顶时申请；不以旧报价租。 |
| 云磁盘/依赖 | 本项目录峰值≤20 GB；新增pip含传递≤12包/下载≤3 GB；额外源码下载0，复用已核归档 | 刷新包§4估算；云基线盘另列，pin/占用/安装闭集未核，当前不申请签发。 |
| 传输两维 | 到板累计双向≤10 GB；云↔Mac mini累计双向≤10 GB；SR追加0 | §5/刷新包§4，按具名清单核实际体积；3a不做，不传bf16 base上板；保留盲文件/剥字段隔离。 |
| 板端阶段B墙钟 | ≤16 h，编译/预检/失败/重试/取证/S3–S5全部计入，不加阶段A余额 | §5/刷新包§4；依赖清单与耗时计划先核。 |
| 板端VLM查询 | ≤2,500次，含预热/失败/重跑；默认3路径105+最多3×609+S5 180=2112，余388；15 Hz额外查询0待定 | §5、刷新包§4、J-A；校准/基准未知，2500只是申请上限，不保证全部对象可执行；S5 VLM额外预热若需须纳入余量。 |
| 板端磁盘 | `~/eng-jet/` A+B累计≤40 GB，非新增40 GB；不删保留件/外部缓存 | 刷新包§3/4与B:6；现有占用由最新证据运行时取，不抄余量作额度，预检核物理余量。 |
| Mac mini中转/评分 | `outputs/eng-jet/` A+B累计≤12 GB；B新增pip/模型加载/合并/转换/VLM推理=0 | 刷新包§4估算；目录/体积闭集先核，数据根只读；与停点测试维度分开，不借SUB:2/5/6。 |
| 实现停点全套（机器/候选） | 推荐Mac mini至多2候选，各全套1次（消费前代码、消费后证据）；额外候选0 | B-CAND-2、COORD-017/engineering§4/6；最终candidate范围与测试清单未核，当前不申请签发。窄修替代仅按规则/具名证据，旧例外不延长。 |
| 全套伴随模型加载/回放 | 当前推荐0，先准备逐模型/设备/次数与帧数闭集，再给非零推荐申请，计入本项 | engineering§6要求随候选签发；旧SUB:6仅旧候选且已用尽，新路径用mock不证明全套0消费。清单未知时全套不能启动。 |
| 复核新增真实实测/模型/回放/SR | 推荐0；复核若有确切需要再逐维度申请 | B-CAND-2、workflow§4.4；focused/红绿测试不豁免消费计数。 |
| 系统设置 | cma/swap/isolate/默认target/功耗/锁频/SSH网络隐私变更=0 | §2.3/§5/刷新包§4；原(k)(l)(m)未答复动作继续0，不靠环境现状推定许可。 |
| Play/正式scenario·session·run ID/训练GPU·h/模型API/发布 | 0/0/0/0/否 | §5原案、刷新包§4；云账单实例ID只作计账，不扩正式ID许可。 |

包/模型/源码取回仍按固定清单、逐包 `pip download --no-deps` 核sha、本地文件 `--no-index` 离线安装；禁dry-run/report取依赖、Range GET探大小。**只有用户逐字签发且接受落实后的下一执行派发才能做这些动作**，本次准备也不得开始。

### R3消费：新候选通过与用户剩余路径（2026-10-04）

登记轮次 `R3消费`，Dispatch-Id `P1-ENG-JET-001-R3消费-20261004T025239Z-e8a7`。接受角色零消耗消费 `docs/reviews/P1-ENG-JET-001.md`「R3@K1K3K4」`PASS_WITH_NOTES`，不重做常规候选核对、不跑实现测试。候选从该节 `passed_candidate` 运行时派生，与同节 `round_candidate` 及交接「K1K3K4R2返工：R2-1 窄修、红绿与全套义务缺额」§3 唯一收工候选一致；已核触及交接文件、为 `origin/main` 祖先，候选至本轮开工 HEAD 的 workflow §4.4 PLAY_GOVERNING diff 为空。不手抄候选 SHA，不把本次接受提交当实现候选；本次纯消费不另开 C/R 轮。

**当前门与验收边界。** 新候选（R1 补丁 + SUB:6 证据 + R2-1 窄修）已过独立复核，Overall 保持 `REVIEW_PASSED`、Lifecycle 保持 `ACTIVE`，仅表示候选通过；**不是阶段 A 探测验收、不是 `DONE`**。R3 §4 已附议本候选 AC-14 `UNITY_NA`，理由是 Unity/文件桥协议零改动，R2-1 修复触及行仅改板侧回程工具及测试；不代替未完成的硬件验收。S0/SR `PASS`、S1 `STOP(FP16_BOX_DIVERGENCE)`、S2 `STOP(FRAME_DROP)` 及 α/α′ 的恢复标记保持；AC-2/3 的证据义务成立不等于 STOP 步骤满足。AC-7/8/9 不满足，S3–S5 `NOT_RUN(阶段 B 信封未签)`，阶段 B 全部维度仍 0。补丁未上板、未在真实断链/重连下验证，f4 仍为补丁前实测；不关闭 M7、不产生部署研究主张。

**归因与闭合。** R2-1 `BC-6`（读作 AC-6）→ 实现错误 1 条（阻断 CLASS_2，R3 修前红/修后绿及四条闭合条件已核实）；R1-1 随其闭合，R1-2/3/4 已在 R2 闭合，不重复新增 finding。累计实现错误 5 条（R1 非阻断 4 + R2 阻断 1）；R1-5/6 `SCOPE_GAP` → BC 缺失 2 条，账本 `OPEN` 不变；其余依据类别及 RED_LINE 均 0。R3 无新 finding、无 CLASS_3 补丁、无 blocks 行，不重新分级。归因与证据汇总见 `docs/implementation-status.md`「P1-ENG-JET-001 — R3消费与新候选停点边界」；债的唯一待办入口仍为该文件「范围外已知缺陷」。

**§5 非 finding 观察处置（沿 R1/R2/R3，不新增 AC、不改标 SCOPE_GAP）。**

| 观察来源 | 当前处置与后续边界 |
|---|---|
| R3 §5：锁外读取去重表 | 按独立复核结论保留首发最多迟一个轮询（≤5 ms）的边界，无版本丢失、无错误计数；不升格为新的板端时延实测或新 finding。 |
| R3 §5 / R2 §5：替换连接时计数与收据 | `send_return` / `returns_sent` 表示已 `sendall`，不证明对端收到；`link_replaced` 注明替换，接收计数仍以桌面 `recv_return` 为准。旧收据/读数不改。 |
| R2 §5：C3-P2 / C3-P3 | 空真只在手写输入域可达，保留非 finding；日后触及该判定时可顺带补具名键断言。SUB:6 块手工追加已与事件逐键核实；**任何日后重跑 `ledger build` 前须先由获批实现补 SUB:6 保留支持**，否则会丢块，不能把当前核实当重建安全证明。本轮不重建账本、不发起实现。 |
| R2/R3 §5：补丁与全套限制 | 进程内替身红绿不是板端实测。SUB:6 全套失败/Carrier/scene006 具名例外不记通过；本窄修候选依用户授权以 focused 83/83 + R2-1 红绿替代停点全套，不记全套已跑。复核副本 83 例中 1 skip 是冻结权重缺失，保持该覆盖限制。 |
| R1/R2/R3 §5：其余观察 | 输入形状解释未验证、冷启动计丢与节拍口径、回稳读法与确认时刻、真实回程 n=29/链路偏差及抖动、GAP 终止、TRT 告警原因未核、NanoTrack/CSRT 构造上界、skip 聚合/未出现项无逐名记录、全套未设 YOLO_OFFLINE/外联未监测、前向连接尾包可被拒与旧 link_events 的保守未知读法均照旧携带；只按既有报告/复核边界复用，不推出未测性能或覆盖。 |

**信封与度量。** R1 补丁停点全套由用户另签 SUB:6，已耗尽；R2-1 窄修按用户 10-04 具名例外（本提案「R2-1 窄修候选例外落实与 R3 交接」）以 focused + 红绿替代全套、沿用两项例外，不借任何旧余额。原全套、SUB:6 全套/模型/回放及 SR 均无追加额度，本轮消耗为 0。K1K3K4 核对共 C3、退回 1 次（C1 不满足）；独立复核共 R3，`REWORK_REQUIRED` 终计 1/2，未触发冻结集。本轮新增 AC/修订 0、研究 BC 新增 0。

**剩余路径与 needs_user（未答复，不执行推荐）。** A补丁:2 及其缺额路径已依 SUB:6、R2-1 例外与 R3 走完，不再作为待用户题。仅余以下用户决定，交接 owner/status 与下一动作统一见状态板交接行：

- **A收口:1（用户不签阶段 B 时）**：沿「R1消费：阶段 A 候选通过与剩余路径」同题，**推荐 A-END**（`CLOSED_PARTIAL_DELIVERY_ENGINEERING_HANDOFF` / `ENDED`）：若不继续，保留描述性交付与未完成验收，避免长期悬挂；现 R1-1…4/R2-1 已闭合，但补丁未上板与两条 OPEN 债必须保留。A-PAUSE/A-NEW 仍可选，本轮不关闭、不暂停、不替用户定范围；与线 B 的 N-B/另立项合为一次一致决定。
- **阶段B:1–8**：各自推荐项、理由与选项完整沿「阶段B签发包刷新（2026-10-03，线 B）」§8「needs_user汇总」，不改线 B 申请或其裁定权限；分别为 N-A、15 Hz 同引擎同计数、S1 原方形读数、完整探测 I-A、J-A、前提/主机裁定后逐维度签刷新主案并先固定依赖、B-CAND-2、等待消耗轨道释放。R3 已完成前一候选 C→R 路径，仅更新其事实前置，不自动选择 B-CAND-2、不改变 §7.1 单候选边界、不指定阶段 B 新 C/R 轮号。用户逐字决定入账并经接受落实前，阶段 B 所有维度保持 0。

### R2-1 窄修候选例外落实与 R3 交接（2026-10-04，CLARIFY）

登记轮次 `K1K3K4落实R2例外`；接受角色只读落实用户已选授权，不是 C 轮，不改核对表、不签独立复核。唯一依据为 `docs/authorizations.md` 条目「2026-10-04 P1-ENG-JET-001 — 用户选 (a)：R2-1 窄修候选以 focused 加 R2-1 修前红/修后绿代替停点全套、SUB:6 两项例外读法沿用（supervisor 会话代录）」授权范围 (1)(2)(3)。适用候选仅为 `K1K3K4R2返工` 收工候选，按 `docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md`「K1K3K4R2返工：R2-1 窄修、红绿与全套义务缺额」§3 运行时解析（唯一收工主题、触及交接文件、已推送且为 origin/main 祖先），不把本次接受提交当实现候选、不手抄 SHA。该节 §4–5 的“待用户决定／例外不推定延长”是授权落实前快照，现由本节在具名范围内替代；原文与历史证据保留。

**AC-10 修订 11（CLARIFY，解释修订 9，关联 AC-13/14、§7.1）**：授权范围 (1) 对上述 R2-1 窄修候选（代码/测试仅 `tools/eng_jet/relay.py` 与 `tests/test_eng_jet_relay.py`）具名：以零模型 focused（`test_eng_jet_*.py` 83/83）加 R2-1 绑定回归修前红/修后绿，代替该候选 workflow §4.3.1 第 2 项的停点全套。证据为 `artifact:docs/evidence/P1-ENG-JET-001-R2rework-focused-tests.log` 与交接同节 §2；绑定回归为 `test:tests/test_eng_jet_relay.py::BoardRelayInProcess::test_adopt_during_return_send_keeps_new_link_dedup_clean`。不记该候选全套已跑，不把 focused 通过外推为全套通过或修复独立复核通过；复核可判阻断。此例外不自动覆盖后续候选。

**AC-10 修订 12（CLARIFY，解释修订 10，关联修订 11、AC-13/14）**：授权范围 (2) 将 SUB:6 授权范围 (2) 的 Carrier 具名例外沿用到上述候选，测试名仍为 `tests/test_det_assoc_carrier.py::CarrierSelfTest::test_carrier_matches_caliber_b_from_first_update`。CPU 逐帧比较已知失败、其余 9 个差异形态未知、比较后 confidence_source／观测桥字段集／临时目录外写入断言未执行，以及两例不经真实工厂的覆盖损失均保留。仅原记录同名同类失败；不改断言、基线、参考、设备或阈值，不记失败为通过，不预定 R3 结论。

**AC-13 修订 5（CLARIFY，解释修订 4，关联 AC-10 修订 11/12、AC-14）**：同一授权沿用 scene006 具名例外：`tests/test_scene006_probe.py` 原记录 29 条（25 FAIL + 4 ERROR）仍按本机缺 re-anchor/NanoTrack 权重作静态环境归因，首项 YOLOE 权重哈希绑定拒绝、后续行为未验证；保留相对 R7 新增，不改作旧失败或通过，不补主树 `runtime/` 资产。两项例外名称/类型闭集及边界完整沿「SUB:6 落实与新候选两项例外」AC-10 修订 10 / AC-13 修订 4 与其原日志指针；**仅同名同类失败，其他新增失败（含同名但不同失败类型/原因）不在例外内**，仍按停点规则处理，复核可判阻断。例外沿用不表示本候选已重跑这两组测试。

**授权范围 (3) 与只读判定**：不签任何额度（SUB:7、全套、模型、回放、上板、SR 均不追加），不签阶段 B、不答 A收口:1 与线 B 阶段B:1–8；既有计数不回退或转用。已只读核实唯一候选满足 §3 解析约束，相对 R2 `round_candidate` 的代码/测试 diff 仅上述两文件，至本轮开工 HEAD 无代码/测试变化；focused 原日志 `Ran 83 tests / OK`，交接 §2 记录绑定回归修前红/修后绿。故 workflow §4.3.1 **第 2 项在用户具名例外下成立**，全套层面回归未实测的限制仍携带。本轮未跑实现测试或重算实测读数；R2-1 闭合须由复核角色红绿核实。

交 Review `R3@K1K3K4`，按 engineering-workflow §5 复核返工直接回复核，**不经核对轮**。候选、上一轮/上一通过候选与 R3 增量范围沿上述交接 §3 的 `CAND/PREV/PASSED` 解析：修复触及行是 `PREV..CAND`，全量 diff 另按上一通过候选核实；R3 增量为两文件代码/测试、返工交接与 focused 日志、状态板及期间文档/派发登记，逐路径以运行时 diff 为准。重点为同锁连接身份写回、替换时计数/收据与 break、锁外读取分支、新绑定回归红绿；未验证项沿 §6。PLAY_GOVERNING diff 非空，具备开轮资格，具体复核结论由 Review 签发。本停点 `REWORK_REQUIRED` 仍计 1/2；Overall `REVIEW_PASSED`、Lifecycle `ACTIVE` 保持，原 R1 门、R1-5/6 OPEN 债、S1/S2 STOP、AC-7/8/9 NOT_RUN 与历史主张上限不变，不记新候选通过或 DONE。

### C3@K1K3K4 核对与 R2 交接（2026-10-04）

登记轮次 `C3@K1K3K4`，Dispatch-Id `P1-ENG-JET-001-C3@K1K3K4-20261004T020334Z-a2da`。SUB:6维度与两项具名例外边界已核；最新核对表、完整范围解析、AC-6回程并发偏差主张与R2关注项见「Contract conformance（核对表）」。本停点核对退回已用1次，按workflow§4.3.3照交Review/`WAITING_REVIEW_R2_K1K3K4`，不再退回；R1通过/附议只覆盖原候选，Overall REVIEW_PASSED、Lifecycle ACTIVE保持，不预签新候选通过。阶段B=0，不答A收口:1或阶段B:1–8；本轮零实现测试/模型/回放/上板/下载/安装，只改本提案核对/决策与本项状态板，不写复核或授权账本。

### SUB:6 落实与新候选两项例外（2026-10-04，CLARIFY）

登记轮次 `K1K3K4落实SUB6`；接受角色零消耗落实合同，不是 C 轮，不改核对表、不签独立复核。唯一签发依据为 `docs/authorizations.md` 条目「2026-10-04 P1-ENG-JET-001 — 用户签发 SUB:6（新候选停点全套，方案 (a)）并为新候选重新具名 Carrier/scene006 两项例外（supervisor 会话代录）」授权范围 (1)(2)(3)，`request_id` = `P1-ENG-JET-001:b0a5f79c:SUB:6`。用户直接签发，不是 supervisor SUB 代拍，子额度块未签状态不变。交接「K1K3K4R1注记修补：…」§4–5 的未签／例外不延长是签前快照；本节仅落实新签的具名额度与例外，旧合同、计数与失败原文保留。

**§5 Mac 生效值、AC-10 修订 9（CLARIFY，解释修订 3/5/6，关联 AC-13/14、§7.1）**：授权范围 (1) 逐字转写：

> Mac mini 本机、新候选（K1K3K4R1注记修补 起）停点全套 1 次；det-assoc 冻结检测器 CPU 加载 ≤ 2；NanoTrack 构造尝试 ≤ 2（读权重 0）；CSRT 构造尝试 ≤ 2（实例 0）；YOLOE/DINOv2/其他模型 0；零模型部分回放 ≤ 2（各 60 帧，计入本项、不扣 ACQ-001）；Mac outputs 增量 < 0.1 MB 且总量 ≤ 2 GB；墙钟 ≤ 15 min；pip/下载/上板/SR 0；成功、失败、重试全部计入，耗尽即停回用户；不授权第二次全套、MPS 推理、改 skip/环境变量。

这是新候选的一次具名增量信封，不回退原 SUB:2/SUB:5 的全套 1/1、det-assoc 2/2、回放 2/2 或 SR 5/5，也不将旧上限（如 NanoTrack ≤ 4、YOLOE/DINOv2 各 ≤ 2）转用到 SUB:6。每个维度独立累计，构造失败与重试同样扣账，不互相转用；缺项为 0。沿 CPU-1 已实现的两处显式 CPU 构造及其默认真实加载器/关联器运行，保持断言、基线、冻结规格/权重与解释器；不授权新的设备/方法/skip 改动。额度耗尽不妨碍记录已执行结果、整理证据并按下述具名例外交接，但任何再次消耗必须停下回用户。

**AC-10 修订 10（CLARIFY，解释修订 8，关联修订 9、AC-13/14）**：授权范围 (2) 为新候选重新具名 `tests/test_det_assoc_carrier.py::CarrierSelfTest::test_carrier_matches_caliber_b_from_first_update` 的 CPU 逐帧比较已知失败（含其余 9 个差异帧形态未知、比较后 confidence_source／观测桥字段集／临时目录外写入断言未执行），作为新候选 workflow §4.3.1 第 2 项的具名例外进入接受核对与独立 `R2@K1K3K4`。原记录索引 2 对应 frame_id=3 的首个宽差仅说明该条，其余差异不推定同形；两例不经真实工厂的覆盖损失仍保留。不改断言、不换基线、不重算参考、不改设备、不记测试通过、不预定核对/复核结论，复核可判阻断。

**AC-13 修订 4（CLARIFY，解释修订 3，关联 AC-10 修订 10、AC-14）**：同一授权重新具名 `tests/test_scene006_probe.py` 原记录 29 条（25 FAIL + 4 ERROR）本机环境失败，仍按本机缺 re-anchor/NanoTrack 权重的静态归因分列，首项 YOLOE 权重哈希绑定拒绝、后续行为未验证；保留为相对 R7 新增，不改作旧失败或通过，不向主树 `runtime/` 补资产。两项例外的名称/类型闭集沿 `docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md`「K1K3K4全套CPU1执行记录与停点自证」步骤 4 及原 `docs/evidence/P1-ENG-JET-001-full-suite.log` 的失败列表核对；**仅限原记录同名同类失败，其他新增失败（含同名但不同失败类型/原因）不在例外内**，必须如实报告并按停点规则处理，不能自行扩例外或签第二次全套。

**下一 Implementation 派发（Mac mini；授权范围 (3) 的接受前置现已落实，按顺序执行）**：

1. 跑前只读核对最新环境与全 tests 的可达真实加载器（含子进程、失败构造尝试）、实际 CPU 设备、具名 `ResidentCarrierReplay` 两次各 60 帧零模型回放归属、已有包/权重、Mac outputs 当前总量与预计增量、包含跑前核对的墙钟。逐维度按修订 9 核对，不能直接沿用 CPU1 的旧 prechecks；预计超限、缺资产/包需安装下载、NanoTrack 将读权重或 CSRT 将成功实例化时不跑，保留核查结果回用户，不改 skip/环境变量绕门，不在全套外另跑真实 focused/探测。
2. 跑前核对满足后，从仓库根用既有数据根解释器仅执行一次全套（只读使用、不装包），输出到新具名证据文件，保留原全套日志，不带 `-v`、不附加环境变量、不删用例、不因失败重跑：

   ```sh
   ~/TetheredDroneTracking-full/.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-JET-001-SUB6-full-suite.log 2>&1
   ```

3. 沿唯一 `docs/evidence/P1-ENG-JET-001-ledger.json` 补 SUB:6 request_id、完整授权标题、生效范围、当前跑前核查与实际各维度累计（成功/失败/重试均计入，静态上界须标明）。SUB:6 单列新候选全套次数与具名模型/回放，不覆盖原 SUB:2/SUB:5 已用计数、不另立账、不重复扣模型合计；记录 outputs 跑前/跑后、增量及墙钟，不能把 `within_envelope` 常量/数量比较当作设备或外联动态测量。原收据、历史读数与失败日志不改写。
4. 对 R7 基线已有失败、本候选相对 R7 新增失败、相对 CPU1 变化分别列名/原因/证据，运行时解析版本，不换基线；逐名核对两项例外同名同类边界，原未知/未执行断言与 skip 聚合限制仍携带，不把失败/skip 记通过。例外以外的新增失败不预签自证成立；保留结果并按停点规则处理，所需任何追加消耗回用户。
5. 同步报告现状与历史，沿 AC-1…16 连同修订逐条附指针，在同名 `K1K3K4-handoff.md` 新具名小节重判 workflow §4.3.1 四项，记录执行机器/时间与版本解析、精确完整候选范围、未验证项，提交推送稳定候选。第 2 项可在上述用户具名例外边界内评估，不能把额度落实当作测试已跑或自证成立；四项成立才交接受只读核对 → 独立 `R2@K1K3K4`。本停点核对退回已用 1 次不重置，R1 的通过与 AC-14 `UNITY_NA` 附议只覆盖原候选，新候选须 R2 另行附议。R1 补丁未上板、f4 是补丁前实测，均继续披露。

本批只更新合同与本项状态交接；IR-26/27 裁定见「待裁定」。S1/S2 STOP、SR PASS/双 RESUMED、SR 耗尽、两条 OPEN 债与 AC-7/8/9 未运行保持；阶段 B 全部维度仍 0，不答 A收口:1 或线 B 阶段B:1–8，不签 DONE。`Consuming=no` 仅指无正式 scenario/session/run ID、Play 或 API 预算，本机模型/回放仍须按 SUB:6 计账；Overall `REVIEW_PASSED`、Lifecycle `ACTIVE` 不改。信封归因：新候选 R1-1…4 补丁的停点全套由用户直接另签 SUB:6，不借旧余额，不将原例外自动延长。

### R1消费：阶段 A 候选通过与剩余路径（2026-10-03）

登记轮次 `R1消费`，Dispatch-Id `P1-ENG-JET-001-R1消费-20261003T225447Z-54b2`；接受角色零消耗消费独立 `R1@K1K3K4`，不重做候选核对、不跑测试。运行时从复核文件解析 `passed_candidate` 与 `round_candidate`，与交接「K1K3K4C1返工：报告现状/历史分列与候选重冻结」§2 唯一收工候选比对，三者一致；候选触及交接文件、为 origin/main 祖先，候选至本轮开工 HEAD 的 PLAY_GOVERNING diff 为空。verdict 为 `PASS_WITH_NOTES`，无阻断 finding、无 blocks 行；AC-14 的 `UNITY_NA` 已由复核 §4 附议，仅覆盖该阶段 A 候选。

**门与验收边界。** Overall 设 `REVIEW_PASSED`、Lifecycle 保持 `ACTIVE`，仅表示阶段 A 的 `K1K3K4` 候选已独立复核；不是阶段 A 探测验收，更不是整项 `DONE`。S0/SR `PASS`、S1 `STOP(FP16_BOX_DIVERGENCE)`、S2 `STOP(FRAME_DROP)` 与用户 α/α′ 的恢复标记全部保留；AC-2/3 证据义务成立不等于 STOP 步骤满足。AC-7/8/9 仍不满足，S3–S5 `NOT_RUN(阶段 B 信封未签)`；`UNITY_NA` 不代替未完成的硬件验收。里程碑证据、归因与未闭债入口见 `docs/implementation-status.md`「P1-ENG-JET-001 — R1消费与阶段 A 停点边界」及「范围外已知缺陷」。不关闭 M7、不扩大本板本栈本资产本序列的描述性读数主张。

**R1 注记交实现下一提交。** 按复核依据列机械归因：R1-1 `BC-6`、R1-2 `BC-4`、R1-3 `BC-12`、R1-4 `BC-10` → 实现错误 4 条（非阻断 CLASS_3）；R1-5/6 `SCOPE_GAP` → BC 缺失 2 条，均记 `OPEN`，不要求本项补资产或修 CPU/MPS 一致性。保持复核分级与 verdict，本轮不发起复判、不新增 AC。

| 注记 | 下一实现提交范围（原文及细节以复核 §3 为准） |
|---|---|
| R1-1 | 按复核具名补丁在新连接清空回程去重状态，并补零模型重连回归；不得把 f4 历史读数改为补丁后实测。 |
| R1-2 | 去除链路事件截断，或保留全量计数供分列函数读取；补纯函数覆盖，保留原收据与历史判定。 |
| R1-3 | 实现纯 `frame_id/sha256` 参照并标明原参照仅投影 sha；不得把含标签的原文件上板、写入插件或改原始资产。 |
| R1-4 | 补 SUB:5 共用全套次数及越界覆盖、具名断链判定纯函数与覆盖；计账常量仍须标为断言/限制，不将其宣称为设备、外联或系统设置的动态测量。 |

**开轮裁定。** 本次仅消费文档，PLAY_GOVERNING diff 为空，禁止为本次消费开轮。上述实现补丁会修改 `tools/`、`tests/`，相对复核文件最新 `passed_candidate` 的 PLAY_GOVERNING diff 非空，须新的 `R2@K1K3K4`，不能套用纯文字 CLASS_3「不开轮」通道来放行代码补丁。R1 为通过轮，不是 `REWORK_REQUIRED` 返工；R1-1 改恢复行为，补丁稳定候选仍须四项自证 → 接受侧只读核对 → 独立 R2，不借返工直回复核豁免核对，也不重置本停点已用 1 次核对退回。仅落实不驱动动作的文档注记且代码/测试无 diff 时不开轮；已有 R1 只覆盖原候选。实现先做零模型 focused 验证并整理精确范围；全套 1/1、det-assoc 2/2、部分回放 2/2、SR 5/5 已耗尽，不重跑。补丁候选需要新的停点全套及相称模型/回放额度时须用户另签，或用户明确新的具名例外；本轮不签额度、不预判新候选自证或 `UNITY_NA`。

**剩余路径与 needs_user（线 A，阶段 B 不签时的收口）。** 阶段 B 仍由用户在线 B 裁定，沿「阶段B签发包刷新（2026-10-03，线 B）」与其 needs_user 节；本轮不答阶段B:1–8、不改 §5/§7.1 单候选安排或线 B 文字。若用户签阶段 B，须先落实阶段边界、信封与候选安排，再实现 S3–S5，最终候选自证/核对/独立复核后由接受角色按完整合同判定；S1/S2 STOP 不因签发消失，不能预定 DONE。

- **A收口:1（条件：用户不签阶段 B）**：A-END = 用户明确停止剩余探测，以 `CLOSED_PARTIAL_DELIVERY_ENGINEERING_HANDOFF` / `ENDED` 收口，保留双 STOP、AC-7/8/9 未运行、R1 注记及两条 OPEN 债，明确注记是先修后收或具名交未来获批工作承接；A-PAUSE = 用户决定暂停、等待以后阶段 B，保留全部义务；A-NEW = 用户另立后续项，明确继承清单与独立信封。**推荐 A-END**：不再继续该范围时，描述性阶段 A 交付与未完成验收可清楚并存，避免长期悬挂；CLOSED 仅停止范围，不冒充通过。此题改变范围/Lifecycle，整题由用户定，未答前维持 ACTIVE，本轮不实施任何收口或暂停。与线 B 的 N-B/另立项选项合并作一次用户决定，不另立冲突裁定。
- **A补丁:2（条件：继续补丁候选过门）**：另签具名最终全套及相称模型/回放额度 / 用户明确具名测试例外 / 用户决定停止并交后续承接。**推荐先由实现完成零消耗补丁与 focused、列精确缺额再请用户签发**：原全套不覆盖新代码且余额已耗尽，不能猜模型次数、借阶段 B 或其他信封，也不能把原用户例外自动延长到新候选；未签不跑全套或任何真实模型/回放/SR。

账本 2026-10-03「用户处置 R1@K1K3K4 复核派发核查：F3a 字面不一致不退回」已准本次继续；本轮交接 Progress 明写 `R1消费`，不改复核文件、不补写用户原话。交接 owner/status 与具体下一动作只在状态板交接行维护。

### C2@K1K3K4 核对收束与复核交接（2026-10-03）

登记轮次 `C2@K1K3K4`，Dispatch-Id `P1-ENG-JET-001-C2@K1K3K4-20261003T222937Z-03cf`。C1-AC13-1 已按边界收束；新候选唯一解析、已推送祖先、BASE 与 ledger 一致、完整 33 路径及 6 路径文档增量均核实。最新逐 AC 核对表、继承的 C1 限制、Carrier（AC-10 修订 8）/scene006（AC-13 修订 3）与 R1 范围、未验证项及无重跑余额见「Contract conformance（核对表）」。本停点核对退回计数仍 = 1，本轮照交 Review / `WAITING_REVIEW_R1_K1K3K4`，不再退回；AC-7/8/9 未运行、AC-14 `UNITY_NA` 附议仍缺，复核可独立判阻断。Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 保持（既有并行授权限制），不改阶段 B 合同/申请，不签 verdict/`DONE`。本轮零测试、零模型/推理/回放/上板/下载安装、零新消耗；只改提案核对/决策与本项状态板，不写证据、复核文件或授权账本。

open_items: AC-7-NOT_RUN,AC-8-NOT_RUN,AC-9-NOT_RUN,AC-14-UNITY_NA

### C1@K1K3K4 核对退回（2026-10-03）

登记轮次 `C1@K1K3K4`，Dispatch-Id `P1-ENG-JET-001-C1@K1K3K4-20261003T221030Z-9c99`。只读异源核对结论为**退回**：`C1-AC13-1` 仅要求消除报告§5当前SR已运行与未标历史的“SR未运行”冲突；逐AC结果、候选解析/完整33路径、授权例外、返工边界及后续复核关注项见「Contract conformance（核对表）」。本停点核对退回计数=1，后续C2必须交独立复核，不再第二次退回。阶段B合同/申请不变，Carrier与scene006例外不预定复核结果。交接Implementation，状态 `WAITING_IMPLEMENTATION_C1_REPORT_FIX`；Overall `IMPLEMENTING`、Lifecycle `ACTIVE`保持；UNITY_NA附议仍缺。本轮不跑测试、不改实现/证据、不认领新消耗、不签任何额度或verdict。

open_items: C1-AC13-1


### §5 阶段 A 信封与 §7 (h)(n) 答复落实（2026-09-28，CLARIFY）

依据 `docs/authorizations.md` 同日「P1-ENG-JET-001 — 用户签发 §5 阶段 A 执行信封并答复 §7 (h)(n)，(i)–(m) 暂不答复（supervisor 会话代录）」（含 (h) 当场澄清），用户已按 §5「阶段 A：S0–S2 + SR」申请值逐字签发本项独立信封；此行落实 §7.3 的接受侧决策记录门。阶段 A 生效值如下，成功、失败和信封内重试共同计数：

| 维度 | 阶段 A 生效值 |
|---|---|
| Consuming | no（无 scenario/session/run ID、无 Play、无 API 预算） |
| 设备 | 用户 Jetson Orin Nano 8GB Devkit Super（JP7.2）；桌面机 = 用户 Mac（Unity 宿主，只跑回放器与中继，零模型）；正式链路按 §7 (h) 答复（两机有线以太网直连或同一交换机，用户接线并给板子固定 IP）；Tailscale 仅 ≤ 1 轮冒烟 |
| 模型下载 | 0 |
| pip / 源码编译（板上） | ≤ 8 包、≤ 300 MB（`ultralytics`、`lap`、`onnx`/导出依赖等，`--system-site-packages` 复用 NVIDIA torch/TensorRT）；不重装 torch |
| 量化主机 | 0 |
| 传输 | 到板 ≤ 100 MB（权重 5.5 MB、a7 前 320 帧 11.8 MB + sidecar、`frozen-V` 0.13 MB、代码束）；SR 每轮 ≤ 100 MB × ≤ 5 轮（含 ≤ 1 轮 Tailscale 冒烟） |
| 板上占用墙钟 | ≤ 8 h（含两次引擎导出各 ≤ 20 min、S2 30 min、SR ≤ 5 轮） |
| 板上 VLM 查询 | 0 |
| 板上磁盘 | ≤ 5 GB（`~/eng-jet/`） |
| Mac | 零 pip、零模型；`outputs/eng-jet/` ≤ 2 GB |
| 系统设置（板上） | 只读核验；`systemctl isolate multi-user.target` 与 `nvpmodel -m` 均不做（§7 (l)/(m) 未答复） |
| Unity Play / scenario·session·run ID / 训练 GPU·h / 模型 API / 对外发布 | 0 / 0 / 0 / 0 / 否 |

§7 (h) 用户当场澄清为「按推荐：接线+固定 IP（推荐）」：正式链路取两机有线以太网直连或同一交换机，由用户接线并给板子固定 IP；**接好且板子可达前，SR 正式轮保持 `NOT_RUN`，AC-4…6 不记满足**。至多一轮 Tailscale 冒烟只按 §2.1/§3.2 进入非结论小节。链路准备好后，正式 SR 可在阶段 A 剩余轮数内于下一实现派发执行，不因本记录推定设备前提已满足。

§7 (i)–(m) 用户暂不答复，逐项沿 §7.3 缺省「不做」：不租云或用 WSL2 量化、不跑 3a 或为其下载 base、不重刷、不执行 `systemctl isolate`、不执行 `nvpmodel -m`。§7 (n) 用户答复「先签阶段 A」；**阶段 B 所有维度仍为 0**，S3–S5 `NOT_RUN(阶段 B 信封未签)`，S0–S2 `PASS` 后仍须用户另签阶段 B。AC-1、AC-4…6、AC-10、AC-15 继续按现有字面和 §7.3 核对，本次答复不改写 AC 条款。信封内引擎重导、编译重试、SR 重跑或 `RELAY_INTEGRITY` 返工仅在上述累计上限内可行，发生时按 §5 在决策记录补记归因；本行没有认领任何实际消耗。

### S1/S2 容器栈落实（2026-10-02，CLARIFY）

依据 `docs/authorizations.md` 2026-10-02「P1-ENG-JET-001 — 用户选 torch 路径 A（板上现有 NGC 容器）并暂停一切 codex 派发至用户告知额度更新」授权范围 (a)：用户逐字同意 S1/S2 在板上现有 NGC 容器栈执行，读数按实跑的容器栈标注。本节落实该裁定，「待裁定」IR-4 的「退回用户选择」随之关闭；不改阈值、不改 AC 判据数值、不改其他信封维度，阶段 B 仍全部为 0。

- **执行栈**：S1/S2 在板上现有 NGC 容器 `nvcr.io/nvidia/pytorch:25.08-py3` 内执行。§5 阶段 A「pip / 源码编译（板上）」行「`--system-site-packages` 复用 NVIDIA torch/TensorRT；不重装 torch」的现行字面改述为：torch/TensorRT 由该容器栈自带，板上系统 Python 仍不安装 torch；容器内新增 pip 包及其依赖（`ultralytics==8.4.104`、`lap` 及其实际拉入的传递依赖）累计仍在阶段 A ≤ 8 包 / ≤ 300 MB 内，板上磁盘仍 ≤ 5 GB（`~/eng-jet/`；既有镜像本体不计入本轮新增），模型下载仍为 0。任一维度将超限即停下回用户，不自行扩额。
- **AC-2 修订 2（关联 AC-3、AC-13）**：S1/S2 证据中的引擎/TRT/torch/CUDA 版本与执行环境字段一律记容器内实跑读数（实跑时记录 `torch.__version__`、`tensorrt.__version__`、CUDA 版本与镜像 tag），以实跑记录为准，不以镜像元数据代替实跑证明；S0 系统栈读数（JP7.2 / CUDA 13.2 / TensorRT 10.16）与 S1/S2 容器栈读数分列、不混记。原条款不覆盖。
- **主张边界**：§6「不承诺」行「本栈（JP7.2/CUDA 13.2/TRT 10.16）」对 S1/S2 及其派生读数改读为「容器实跑栈（以实跑时记录的版本为准）」；S1/S2 读数不代表 JP7.2 系统 TensorRT 10.16 栈，其余步骤与主张边界不变。
- 容器栈字面以本节与「CLARIFY 表」2026-10-02 新行为准；原 §5 申请表与 09-28 生效表原文保留、不覆盖。

### S1/S2 系统栈落实（B）（2026-10-02，CLARIFY）

依据 `docs/authorizations.md` 2026-10-02「P1-ENG-JET-001 — 用户选执行栈 B 的前置：经 Mac mini ssh 在板上 sudo 安装 python3-pip/python3-venv（用户输入密码；supervisor 会话代录）」授权范围 (a)：用户逐字选择题 1′ 的 **B**（板上系统 Python + 系统 TensorRT 10.16 栈）。本节落实该裁定，本轮登记轮次 `CLARIFY-B`；不改阈值、不改 AC 判据数值、不改其他信封维度，阶段 B 仍全部为 0。

- **执行栈**：S1/S2 改在板上系统 Python 执行——以 `--system-site-packages` venv（或等价方式）复用 S0 已核验的系统 TensorRT 10.16，torch/torchvision 经 pip 轮子安装进该 venv。同日「S1/S2 容器栈落实」节与「CLARIFY 表」容器行对 S1/S2 的**执行栈部分**由本节与「CLARIFY 表」系统栈新行替代；两节原文保留、不删除，容器 `NOT_RUN(container-tensorrt-sm87)` 记录保留为历史。§5 阶段 A「pip / 源码编译（板上）」行的现行字面改述为：回到「`--system-site-packages` 复用系统 TensorRT」的合同原始执行栈，torch/torchvision 轮子及其 pip 传递依赖的下载与安装属新增额度 SUB:1（`P1-ENG-JET-001:b0a5f79c:SUB:1`，申请值与来源见「needs_user」题 4），**用户逐字签发前该额度为 0、不派实现安装 torch**。
- **AC-2 修订 5（关联 AC-3、AC-13）**：S1/S2 证据中的引擎/TRT/torch/CUDA 版本与执行环境字段一律记系统 venv 内实跑读数（实跑时记录 `torch.__version__`、`tensorrt.__version__`、CUDA 版本与 venv 构造方式），以实跑记录为准；AC-2 修订 2 的容器实跑读数规则对系统栈补跑不适用（容器轮无读数，不产生冲突）。S0 系统栈读数与 S1/S2 实跑读数分列、不混记。原条款不覆盖。
- **主张边界**：§6「不承诺」行「本栈（JP7.2/CUDA 13.2/TRT 10.16）」对 S1/S2 **恢复原字面**（版本以实跑记录为准）；同日容器 CLARIFY 的「容器实跑栈」改述随容器路径弃用而失效，原文保留。
- **容器 venv 与 wheels 的处置**：板上 `~/eng-jet/venv`（容器 venv，101,751,706 B）与 `~/eng-jet/wheels`（5 个轮子）**保留**至系统栈 S1/S2 补跑完成：wheels 供系统 venv 免下载重装 ultralytics/lap 等同版本包，venv 保留作回退。系统栈 S1/S2 有读数后由实现角色在同一派发内删除容器 venv（回退价值消失）并在证据与 ledger 如实记录；届时 wheels 是否保留由接受角色在决策记录补一行。计数口径：容器内已装 5 包的 pip 计数（包数 5、字节 202,869,979 B，含已卸载的 opencv-python，IR-11 保守口径）**不回退、继续计入**阶段 A pip 维度（§5 表头「签发后成功、失败、重试全部计入同一上限」）；磁盘占用继续计入板上磁盘维度直至实际删除。
- **既有依赖在系统 venv 的重装计数（信封内归因行）**：ultralytics、lap、ultralytics-thop、opencv-python-headless 在系统 venv 的**同版本**重装属 §5 信封内工程性重试，本行即归因记录：优先用 `~/eng-jet/wheels` 已有轮子离线安装（新增下载 0、包数不新增）；仅当板上轮子缺失/损坏需重新下载同版本轮子时，下载字节继续计入既有 ≤ 8 包 / ≤ 300 MB 维度，**不并入 SUB:1**。
- **给实现角色的提示（S0 证据口径；本批次不改证据文件）**：用户在板上 sudo 执行的 apt 操作（账本同日条目）把 python3.12 由 3.12.3-1ubuntu0.15 升至 0.17（新装 python3-pip/python3-venv 等 6 包、升级 7 包、下载 17.9 MB、磁盘 +10.1 MB）。S0 证据（`docs/evidence/P1-ENG-JET-001-env.json`）记录的是升级前读数。系统栈补跑时实现角色须在当轮证据（如 `-env.json` 补记段或当轮 fastlayer 证据）注明该补丁版本变化及来源（账本同日条目授权范围 (b)），不重写 S0 原文读数。

### SUB:3 落实与安装方式合同解释（2026-10-02，CLARIFY）

依据 `docs/authorizations.md` 2026-10-02「P1-ENG-JET-001 — 用户按申请值签发 torch/torchvision 下载与安装额度（官方 cu130 源；SUB:1…）」与同日「P1-ENG-JET-001 — 用户按推荐签发 SUB:3：torch 依赖下载上限 3.5 GB → 6.5 GB」两条目（只指针到账本条目，用户原话不复述）。本节落实签发结果，本轮登记轮次 `K1K3K4补跑B待裁定`；不改阈值、不改 AC 判据数值，其余信封维度不变，阶段 B 仍全部为 0。

- **SUB:1 现行生效值**：下载字节上限由 ≤ 3.5 GB 改为 **≤ 6.5 GB**（含已计 3,093,609,695 B；签发后成功、失败、重试全部计入同一上限，耗尽即停回用户）；包数 ≤ 32、安装后新增磁盘 ≤ 8 GB、板上磁盘维度 ≤ 13 GB、来源 `https://download.pytorch.org/whl/cu130` 与 pin（`torch==2.9.1` + `torchvision==0.24.1`）均不变。用户直接签发，不是 supervisor SUB 代拍，SUB 子额度块仍未签。
- **干跑下载归因（信封内归因行）**：K1K3K4补跑B 以 `pip install --dry-run --report --no-cache-dir` 求依赖清单，pip 24.0 把 22 个轮子体完整取回后丢弃（2,318,455,950 B）——属**实现方法失误**，不是合同或环境问题；已计入 SUB:1 已用量（`-ledger.json` `dimensions.sub1_torch`：轮子字节 2,838,727,831 B / 保守收包 3,093,609,695 B），不以未留存为由回退计数。
- **安装方式（合同解释，绑定补装派发）**：**禁止 `pip install --dry-run` / `--report` 等会把轮子体取回的解析方式**；按补跑B 已实测确定的依赖清单（`-env.json`「s1s2_system_stack」`sub1_install.dry_run_resolution`）逐个 `pip download --no-deps <name>==<ver>` 取回并逐包核对 sha256（torchvision 按本地 cu130 轮子，不取 PyPI 同名不同 sha 版），再按本地文件离线安装（`pip install --no-index --find-links <轮子目录>`，torch/torchvision 以文件路径锁定官方 cu130 轮子）；已取回留存的 torch/torchvision 两枚官方轮子（`~/eng-jet/wheels/sub1`，sha 与题 4 一致）复用、不重下。任一维度将超限即停回用户。
- **装后顺序（落实题 4 已定核对点）**：先 `fastlayer_bench verify`（`get_arch_list()` 含 `sm_87`、板上 CUDA matmul 读回核对、与系统 TensorRT 10.16 共存核对点），不可用即停回用户、不在信封内换源；通过后才跑 S1/S2。

### 题 6 选 A 落实：装后验证第一项替代判据（AC-2 修订 6）（2026-10-02，CLARIFY）

依据 `docs/authorizations.md` 2026-10-02「P1-ENG-JET-001 — 用户选题 6 A：官方 torch 无 sm_87 时接受同主版本二进制兼容读法继续 S1/S2（supervisor 会话代录）」授权范围（只指针到账本条目，用户原话不复述）。本节落实该裁定，本轮登记轮次 `K1K3K4补跑C待裁定`；不改其他 AC、不改阈值（含 S1 一致性 1e-3 线、50 ms 参考线与 200 ms STOP 门）、不改信封维度，阶段 B 仍全部为 0；零新增下载，不签 SUB:4。

- **AC-2 修订 6（关联 AC-3、AC-13）**：「needs_user」题 4（CLARIFY-B2 版）装后验证第一项「`torch.cuda.get_arch_list()` 输出含 `sm_87`」**由本修订替代执行**（原字面保留不删）：替代判据 = arch list 含至少一个与本板同主版本（compute capability 8.x）、算力不高于 8.7 的 `sm_8x` SASS 条目，且下列装后冒烟**全部**通过方算验证通过：(i) 板上 CUDA matmul 读回核对（fp32/fp16 相对差在题 4 原定限内、全 1 精确）；(ii) torch 与系统 TensorRT 10.16 同进程建引擎并推理；(iii) 无 torch 干净进程建引擎；(iv) 附加只读诊断 cuDNN conv2d fp32/fp16、torchvision CUDA nms、归约（作为二进制兼容佐证纳入判据，须全过）。任一失败即停下回用户改来源，**不在信封内换源**（沿题 4 原纪律）。
- **本次实测（逐项指向 `docs/evidence/P1-ENG-JET-001-env.json`「s1s2_system_stack_c」）**：替代判据第一项——arch list = sm_80/90/100/110/120 + compute_120，含 `sm_80`（同主版本 8、算力 8.0 ≤ 8.7）→ 满足（`verify.arch_list`）；(i) matmul fp32 相对差 2.79e-7 / fp16 4.35e-4、全 1 精确 → 通过（`verify.matmul`）；(ii) 同进程建引擎并推理、max_abs_diff 0.0 → 通过（`coexistence.trt_with_torch`）；(iii) 无 torch 干净进程建引擎 → 通过（`coexistence.trt_clean_process`）；(iv) cuDNN conv2d fp32/fp16、torchvision CUDA nms、归约全 `ok` → 通过（`diagnostic_sm80_compat.checks`）。**按修订后判据装后验证通过**，S1/S2 可在下一派发执行；原第一项判据下 verify `pass: false` 的证据原文保留、不改写。
- **读数标注**：S1/S2 全部证据与报告中 torch 相关读数须注明「官方 cu130 torch 2.9.1 无 sm_87 原生 SASS，按同主版本二进制兼容（sm_80 cubin）运行」；检测推理走原生支持 SM 87 的系统 TensorRT 10.16；S1 自带 frozen-V 1e-3 一致性比对不变，数值异常仍按原 STOP 判据处置。
- **不兼容报错处置**：S1/S2 及后续任一运行环节（引擎导出、推理、前后处理）出现 `no kernel image` 或其他 CUDA 不兼容报错，立即停止该路径并回用户，不换源、不做任何变通。

### S1 STOP 与补跑D记录核对（2026-10-03）

本轮登记轮次 `K1K3K4补跑D待裁定`，是实现期合同裁定，不是 C 轮。记录 **S1 `STOP(FP16_BOX_DIVERGENCE)`**：方形 FP16 引擎时延分量过门、一致性分量不过；读数与差异证据仅指向 `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1.square」「S1.engines.640.s1.comparison」及 `docs/evidence/P1-ENG-JET-001-report.md` §2d，矩形读数单列、不改 verdict 对象。按 §2.1 停止总则，**S2、SR、S3–S5 全部 `NOT_RUN(S1 STOP FP16_BOX_DIVERGENCE)`**；此为本节裁定时、题 7 答复前的执行状态，当时不作 `RESUMED_AFTER_USER_RULING(S1)` 标记、不放行后续；现行续跑范围见下节「题 7 选 (α) 落实」。

合同核对：交接「K1K3K4补跑D执行记录」、报告 §2d 与 `-fastlayer.json`「S1」「S2」一致：计时/比对窗口沿 AC-2 修订 1，方形两分量沿 AC-2；`-fastlayer.json`「S1.binary_compat_note」与 `-env.json`「s1s2_system_stack_d.note」保留 AC-2 修订 6 的 torch 无 sm_87 原生 SASS、sm_80 cubin 二进制兼容标注，系统 TensorRT 检测路径与实跑版本分列（AC-2 修订 5）。未发现停止总则或修订 6 标注需要更改的合同字面，不新增该两项义务、不改阈值。资产使用前核对指向 `-assets.json`「round_d_pre_use_check」；清理与累计信封读数指向 `-env.json`「s1s2_system_stack_d.wheels_sub1_cleanup」和 `-ledger.json`「dimensions」。两版引擎导出与装后轮子清理属既有阶段 A / IR-16 (d) 范围内执行，本行记录归因，下载/包数不回退；本轮接受裁定零消耗。IR-17…19 答复见「待裁定」，仅新增源于 IR-18 的 AC-16，不放宽其他 AC 或信封。

§7 (h) 用户 10-03 已答复链路接好（192.168.8.1 ↔ 192.168.8.2；账本同日「P1-ENG-JET-001 — 用户告知 Mac mini ↔ Jetson 有线直连成功（§7 (h) 答复；supervisor 会话代录）」）。本节裁定时 mini 代理报 `No route to host`；此阻塞现已排除，依据状态板 Log 2026-10-03「P1-ENG-JET-001 mini 代理经有线地址可达（supervisor）」。报告 §1、交接执行记录与 `-ledger.json.pending_user.h` 中「尚未接好/待 (h)」为答复前记录；下一实现派发同步现状与账本指针，保留原执行事实，本轮不改证据。正式 SR 的次序、SSH 边界与余额按下节执行；自证第 1、2 项仍不成立，不开 C1，不签独立复核或 UNITY_NA 附议，Overall/Lifecycle 保持原值。

### 题 7 选 (α) 落实（2026-10-03）

依据 `docs/authorizations.md` 2026-10-03「P1-ENG-JET-001 — 用户选题 7 (α)：S1 STOP 记录偏差、以方形 FP16 引擎继续（supervisor 会话代录）」授权范围；本轮登记轮次 `K1K3K4补跑D选α落实`，只落实该裁定，零消耗、不是 C 轮，不改 AC 或核对表。

- **下一实现派发**：由 supervisor 在 Mac mini 派发 Implementation，计算在 Jetson 板上；复用补跑D 方形 TRT FP16 引擎，身份、路径与 sha 运行时从 `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1.engines.640」解析并核对，不手写可派生标识。S1 保持 `STOP(FP16_BOX_DIVERGENCE)`；只续跑 S2 **15 Hz / 30 min**（S1 p95 未达 ≤33 ms 加测条件，不测 30 Hz），沿 AC-3 及其修订 1 记录六个 5 min 格与 verdict。后续证据/报告标 `RESUMED_AFTER_USER_RULING(S1)` 并指向上述账本条目；保留 AC-2 修订 6 的 torch 无 sm_87 原生 SASS、sm_80 cubin 二进制兼容标注与系统 TensorRT 检测路径分列，遇不兼容报错仍停回用户。
- **隔离与清理**：执行 IR-17 / AC-12 修订 2，将具名驱动缓存文件名命中与真正违规分列、保留原扫描指针，不改写原 `ac12_clean: false`、不改缓存子目录名绕扫描、不删缓存。板上本项 Python 进程启动前落实 AC-16 的 `MPLCONFIGDIR` 到 `~/eng-jet/home/mpl`，继续 `YOLO_CONFIG_DIR` / `CUDA_CACHE_PATH` 重定向，记录实际环境和外部新写入。IR-19 只在系统栈 S1 与 S2 均已实跑有读数后，才于同一实现派发内删除容器 `~/eng-jet/venv`，记清单/字节和前后占用，不动 sysvenv；下载与包数不回退，既有 wheels 与外部缓存/会话文件继续保留，wheels 后续处置仍交接受角色补记录。
- **停止与 SR 次序**：S2 再 `STOP` 即停全部后续，按 §2.1 记录 `NOT_RUN(S2 STOP <原因码>)`、写完证据/报告回接受角色→用户；不得借本次 S1 裁定继续越过 S2 STOP。只有 S2 按原判据可继续后才准备原范围 SR (b) 真实 `TrackLoop` 应答器（初始化框只取首帧检测器自身 target 类最高分框，不用离线用户框替身或真值），再按原 AC-4…6 及修订 1 做正式 SR：回声/真实两模式、完整性与时延、10 s/60 s 断链，forward 无有意断链轮与断链轮分列；冒烟读数不混入正式结论。
- **有线与 SSH（后续主机密钥授权前记录；现行见补跑E有线 SSH 行）**：mini 代理经 192.168.8.2 已可达，依据状态板上述 supervisor Log（ping 3/3、22 端口通，ED25519 指纹与已存 Tailscale 主机密钥一致、借该键登录成功）。本机 `~/.ssh/known_hosts` 无此有线地址条目，用户未授权改 `~/.ssh/*`。正式 SR 如需有线 ssh，实现须采用不落盘方式，例如 `-o HostKeyAlias=<已存 Tailscale 地址> -o StrictHostKeyChecking=yes -o UpdateHostKeys=no` 复用已存键，别名运行时从现有配置/键记录只读解析并核对；不得追加 known_hosts、改 config、放宽主机密钥检查或改隐私/网络设置。若既有键无法验证或连接确需配置更改，写 `needs_user` 并停对应动作，不自行改动。
- **阶段 A 余额核对与归因**：本次续跑是用户对 S1 STOP 的记录偏差并继续裁定，S2/SR、隔离记录更新和条件性清理全部计入既有阶段 A，不新增额度。按 `docs/evidence/P1-ENG-JET-001-ledger.json`「dimensions」及已签 SUB:1/SUB:3：板上墙钟已用 3,783 / 28,800 s，余 **25,017 s**（S2 需 1,800 s）；SR 已用 1 / 5 轮，余 **4 轮**、每轮 ≤100 MB，Tailscale 冒烟 1/1 已耗尽；到板已用 18,314,475 / 100,000,000 B，余 **81,685,525 B**；板上磁盘已用 5,166,250,549 / 13,000,000,000 B，余 **7,833,749,451 B**；SUB:1 新增磁盘已用 4,925,758,840 / 8,000,000,000 B，余 **3,074,241,160 B**；Mac outputs 已用 39,119,677 / 2,000,000,000 B，余 **1,960,880,323 B**。板上既有 pip 余 1 包 / 57,247,361 B，SUB:1 下载余 883,642,289 B、包数余 9；本派发复用现有栈与引擎，不需新下载/安装。余额足以交实现续跑 S2 并在其可继续后准备正式 SR；每次上板/SR 前按最新累计账核对拟用墙钟、轮数、传输与磁盘，预留写证据的空间和时间，余额不足即停并写 `needs_user`、不启动该动作。成功、失败和重试累计，阶段 B、Mac 模型额度不由这些余额覆盖。
- **边界与停点**：不重跑 S1、不换矩形引擎作 verdict 对象、不改阈值、不新增额度；S3–S5 仍受未签阶段 B（全部维度 0）约束。SUB:2 未签前不跑全套，focused 不替代停点全套；未满足 workflow §4.3.1 四项停点自证前不送 C1。下一实现须同步旧证据中的待用户/链路现状与账本指针、保留历史执行事实。本记录只落实继续运行范围，不认定实现/独立复核/UNITY_NA 通过，Overall 仍 `IMPLEMENTING`，Lifecycle 仍 `ACTIVE`。

### S2 STOP 与补跑E记录核对（2026-10-03）

本轮登记轮次 `K1K3K4补跑E待裁定`，是实现期合同裁定、零消耗，不是 C 轮。记录 **S2 `STOP(FRAME_DROP)`**；读数仅指向 `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S2.runs.15hz.bins」「S2.runs.15hz.tegrastats_bins」「S2.runs.15hz.verdict」与 `docs/evidence/P1-ENG-JET-001-report.md` §2e。交接「K1K3K4补跑E执行记录」、报告 §1/§2e 与 S2 JSON 一致：方形引擎 15 Hz / 30 min、六个 5 min 格齐，按 §2.1 / AC-3 修订 1 三项合取，无确认热降频、末/首 p95 比值过线、丢帧非零，故 STOP；未达到 30 Hz 加测条件。冷启动和周期内丢帧仍全计，不剔除、不改阈值；分布描述不等于已验证成因。

S1 保持 `STOP(FP16_BOX_DIVERGENCE)`；S2 的 `RESUMED_AFTER_USER_RULING(S1)` 与 `resumed_ledger_title` 正确指向账本 2026-10-03「P1-ENG-JET-001 — 用户选题 7 (α)：S1 STOP 记录偏差、以方形 FP16 引擎继续（supervisor 会话代录）」，不是 S2 的继续授权。按停止总则，**SR（含 (b) 准备）、S3–S5 `NOT_RUN(S2 STOP FRAME_DROP)`**；此为用户 S2 答复前的记录，现行 SR 放行见「S2 处置选 (α′) 落实」，S3–S5 仍受未签阶段 B 约束；不借 S1 授权越过 S2 STOP。上述停止判据与标注无合同字面冲突，不新增义务；IR-20 的既有条款解释按「待裁定」AC-2 修订 7 追加。

隔离与清理核对：`-assets.json`「round_e_pre_use_check」记录使用前一致；「board_manifest.ac12_split」沿 AC-12 修订 2 分列具名驱动缓存文件名命中与真正违规，保留原扫描及 `ac12_clean: false`，不能据此宣称 AC-12 已验收。`-env.json`「s2_system_stack_e.env」「outside_eng_jet」记录 AC-16 三处重定向与 marker 后外部新写入核查；「container_venv_delete」与 `-ledger.json`「dimensions.board_disk.cleanups」记录 S1/S2 均有读数后的条件性删除，不动 sysvenv、下载/包数不回退。该删除是 IR-19 / 阶段 A 既有范围内执行，本行记归因。**wheels 处置：保留 `~/eng-jet/wheels` 既有轮子**（占用指向上述 env 的 `du`），供同版本离线复用，继续计入板上磁盘；本轮不授权删除、不重下、不重装，外部缓存/会话文件继续保留。

文档一致性缺口：报告 §3 Q4 的「链路未接」和 §4 建议 1 的「无任何…快层读数」未同步，与 §1/§2e 现状不符；`-relay.json` 正式小节仍为答复前 `NOT_RUN(待用户 (h))`，S3–S5 专项 JSON 仍记阶段 B 未签，现行停止原因由报告 §1 和本节给出，不能把这些旧原因当成当前放行依据。下一实现派发按**既有 AC-13/AC-15 文档一致性义务**同步当前状态和账本指针、明确保留历史记录（S3–S5 另仍受阶段 B 未签约束）；不是新 AC / NEW_OBLIGATION，本角色不改证据。停点自证第 1、2 项仍不成立，不送 C1，不签独立复核或 UNITY_NA 附议；Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不变。当前交接见「needs_user（补跑E；当前用户交接，2026-10-03）」。

### S2 处置选 (α′) 落实（2026-10-03）

依据 `docs/authorizations.md` 2026-10-03「P1-ENG-JET-001 — 用户选 S2 STOP 处置 (α′)：S2 记录偏差并继续，做原范围正式 SR（supervisor 会话代录）」授权范围；本轮登记轮次 `K1K3K4补跑E选α′落实`，零消耗、不是 C 轮，不改 AC 或核对表。本节将「needs_user（补跑E）」原条件计划转为**下一实现派发的放行范围**；用户原话只在账本，本轮不代写。

- **派发与 SR (b) 准备**：由 supervisor 在 Mac mini 派发 Implementation，模型计算在 Jetson 板上，桌面端只做回放与中继、零模型。准备原 §2.1 SR (b) 的真实 `TrackLoop` + 补跑D 既有方形 TRT FP16 插件；init 框只取首帧检测器自身 `target` 类最高分框，不借 S1/S2 离线用户框替身、不读或传输真值。引擎身份、路径与 sha 运行时从 `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1.engines.640」解析并沿 AC-11 核对实跑栈。为补齐该应答器、测量/记录与合同要求的断链路径，允许实现角色在 `tools/eng_jet/` 修改线束及相应 `tests/test_eng_jet_*.py` focused 测试、更新本项证据；这些属于本次已放行的原范围实现，不改变 `controller/`、`Assets/`、`config/`、冻结规格/权重、帧与控制协议、目标身份/重播种逻辑、发布门或采样。缺依赖/无法按原范围实现时回报，不自行加包、换栈或优化。
- **有线正式 SR**：只走 Mac mini **192.168.8.1 ↔ Jetson 192.168.8.2**；沿 §2.1、§3.2、AC-4…6 及 AC-4/6 修订 1，以 **5 Hz、≥1,500 帧**回放，做回声与真实两模式。forward 按全程零链路事件准备，与有意断链轮分列；完整率分母为发送端实际送出包数，分子为板端完整发布且 sha 一致的对应包数，不扣在途整包丢失、不选好区间补 PASS。记录完整率/顺序违反/指向不完整包计数（成功线 100%/0/0）、到达与两模式回程 p50/p95/max、端到端 p95；分位数沿 nearest-rank 且附 n。每 1 s 四时戳对时，报告两机偏差中位/漂移、`capture_age_s` 对照 `T_STALL_S=3.0`、`load_elapsed` 对照 `T_pub=0.4 s`，真实观测 `frame_age_ms` 分布及超线比例。10 s/60 s 断链各一次，记录两侧存活、板侧写桥次数、恢复帧缺口、latest 帧差、真实 TrackLoop 终止/继续语义与回稳时间（原线恢复后 60 s 内）；不补发过期帧。断链手段沿 IR-8 两案与既有 D5 路由，不以停回放、暂停应答或杀进程替代断链。`tailscale_smoke` 原件保留且只作非结论小节，1/1 已耗尽，不重跑、不混入正式 forward/return/disconnect。
- **两次 STOP 与 IR-20 限制并存**：S1 `STOP(FP16_BOX_DIVERGENCE)`、S2 `STOP(FRAME_DROP)` 原 verdict 与负结果均保留；SR 证据/报告新增 `RESUMED_AFTER_USER_RULING(S2)` 指向本节所引账本条目，同时保留 `RESUMED_AFTER_USER_RULING(S1)` 及账本「用户选题 7 (α)…」续跑来源，两者不互相替代。带入 IR-20 / AC-2 修订 7 的原 TRT 计划跨设备告警与影响未核实限制，继续标注官方 cu130 torch 2.9.1 无 sm_87 原生 SASS、sm_80 cubin 二进制兼容与系统 TensorRT 检测路径；重启不是已证明成因，不宣称告警无影响或引擎可跨设备。实际 CUDA/TRT 不兼容错误、无法反序列化/推理、身份不符仍立即停对应路径回用户，不换源、不变通。不据 15 Hz 读数或最大 update 推定 5 Hz 无丢帧、合同或部署通过。
- **隔离与连接**：执行 AC-12 修订 2，具名 `home/cuda-cache/index` 文件名命中与真正违规分列，原扫描及 `ac12_clean: false` 保留；内容禁键仍违规，不改缓存目录名绕扫描。执行 AC-16：板上本项 Python 进程启动前设 `MPLCONFIGDIR` 到 `~/eng-jet/home/mpl`，继续 `YOLO_CONFIG_DIR` / `CUDA_CACHE_PATH` 重定向，记录实际值与外部新写入核查；主树 `runtime/`、数据根等受保护根零写入。sysvenv、既有 wheels、外部缓存/会话文件保留，不新增清理。SSH 复用已授权存好的有线地址键，先只读核验，沿 `BatchMode=yes`、`StrictHostKeyChecking=yes`；不得改 `~/.ssh/*`、放宽主机密钥检查或改网络/隐私设置，无法验证即停对应动作回用户。
- **阶段 A 余额复核与归因**：按最新 `docs/evidence/P1-ENG-JET-001-ledger.json`「dimensions」复算：墙钟已用 5,766/28,800 s，余 **23,034 s**；SR 已用 1/5，余 **4 轮**（每轮 ≤100,000,000 B）；到板已用 18,315,944/100,000,000 B，余 **81,684,056 B**；板上磁盘已用 5,070,463,807/13,000,000,000 B，余 **7,929,536,193 B**；SUB:1 新增盘已用 4,829,972,625/8,000,000,000 B，余 **3,170,027,375 B**；Mac outputs 已用 49,668,939/2,000,000,000 B，余 **1,950,331,061 B**。板上既有 pip 余 1 包/57,247,361 B、SUB:1 下载余 883,642,289 B/包数余 9，但本派发新增下载/安装 **0**，不动用这些余额。当前余额允许交实现准备与正式 SR；每次上板/正式轮前从最新账核对拟用墙钟、轮数、到板与每轮字节、两侧磁盘及证据余量，不足即写 `needs_user` 并停该动作、不得放行或借其他项额度。准备、成功、失败、重试与取证全部累计阶段 A；本行仅记录用户 STOP 后继续的范围归因，无新增消耗/额度。`STOP(RELAY_INTEGRITY)` 仍只允许中继实现返工并在既有剩余轮数内重跑，发生后接受角色补归因，耗尽即回用户；其他 STOP 沿停止总则，不自动越过。
- **现状同步与停点**：下一实现沿 AC-13/15 同步报告 Q4/建议、relay 正式小节及 ledger 待用户现状，保留补跑E及更早的未运行原因作为历史，不把有线未接或旧 S2 待裁定当现行门。不得重跑 S1/S2、重导出/换矩形引擎、改阈值或新增额度/下载。S3–S5 阶段 B 仍未签、全部维度 0，不得启动；SUB:2 未签不跑全套，focused 不替代停点全套，自证四项未齐不送 C1。正式 SR 当前尚未执行、AC-4…6 不记满足；本记录不签实现/独立复核/UNITY_NA 通过，Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不变。

### SR 与补跑F记录核对（2026-10-03）

登记轮次 `K1K3K4补跑F待裁定`；实现期合同裁定、零消耗，不是 C 轮，不改核对表。按账本 2026-10-03「P1-ENG-JET-001 — 用户选 S2 STOP 处置 (α′)：S2 记录偏差并继续，做原范围正式 SR（supervisor 会话代录）」逐字范围核对：补跑F只准备原范围 SR (b)，在 mini↔Jetson 有线做正式 SR；S1 `STOP(FP16_BOX_DIVERGENCE)`、S2 `STOP(FRAME_DROP)` 均保留。SR 的 `RESUMED_AFTER_USER_RULING(S1)` 指题 7 (α) 账本、`RESUMED_AFTER_USER_RULING(S2)` 指 (α′) 账本，双标不互相替代。未重跑 S1/S2、换引擎、下载/安装、改 SSH/网络设置或启动 S3–S5；阶段 B 全部维度仍 0。本节认可记录读法，不签发实现验收或独立复核通过。

**AC-4/6 及修订 1**：`docs/evidence/P1-ENG-JET-001-relay.json`「forward」f2/f3 各送出并完整发布 1,500 包（sha 一致），完整率/顺序违反/不完整指针为 100%/0/0，偏差校正到达 p95 16.245/16.690 ms，偏差中位 8.909/7.851 ms、漂移分列；不扣在途丢失。f4 的 1,152/1,152 单列「disconnect」，不凑入 forward 或 ≥1,500 帧分母。10/60 s 断链实测 10.004/60.001 s，板侧成员/latest/回程/应答器写均 0，恢复缺口 49/299、latest 帧差 50/300；TrackLoop 首次重连以 GAP 终止、不重播种，应答器及两侧中继存活正常结束。两次回稳 0.134/1.940 s，均在原 60 s 线内。回稳读法在开工提交（以 git 主题「K1K3K4补跑F 开工：SR (b) 真实 TrackLoop 应答器、断链分析与有线 SSH 选项」运行时定位）的 `relay.RECOVERY_*` 事先写定：断链前 60 s 偏差校正 p95、剔除更早断链扰动窗、连续 10 帧不超基线；所报时间为合格连续段首帧相对重连的时间，不冒充第 10 帧确认时间，不作合同新阈值或事后调参。

**AC-4 修订 2（CLARIFY，解释修订 1，关联 AC-13）**：「零链路事件轮」不表示原始收据没有任何 connect/disconnect 行。补跑F f2/f3 收据各有启动 connect 和收工 disconnect（OSError/TimeoutError），必须原样保留；本次逐轮仅一次连接、无中途重连/link_down/send_fail，所有 1,500 个送包与对应发布全部计数。末帧送出为 16:43:08/16:50:19Z，收工断开为 16:43:35/16:50:49Z，计数窗不缩短、不挑好区间。本解释仅区分启动/结束与传输中断，任何传输中意外事件仍按修订 1 原样报告、完整率不足仍 STOP。来源：`-relay.json.forward.rounds.*.link_events`、原始 `sr-f/{f2-echo,f3-track}/desktop/relay-receipts.jsonl` 的 start/send_bundle/disconnect/stop 及板侧收据；`relay.DesktopRelay.run/return_loop`。16:52:11–16:52:14Z 板侧物理 down/up 及 ssh 超时在 f3 板侧 16:52:04Z 结束后、f4 开始前，故不是从正式窗内剔除的坏区间；`-env.json.sr_system_stack_f.board_link_events` 与报告 §2f 保留，原因未明，不能据 SR PASS 外推链路长期稳定。

**AC-5 修订 1（CLARIFY，关联 AC-13）**：回程观测时延与逐帧年龄分别带真实分母；原条款「真实模式下观测记录的 frame_age_ms」按真实 TrackLoop 的逐帧观测/状态记录报告，不能把全帧年龄 n 当作成功写桥的 n。`-relay.json.return` 回声回程/端到端 n=1,500；真实回程与端到端 n=29（p95 6.117/239.633 ms），因第 0…29 帧 TRACKING、第 30 帧起绑定目标丢失且 compat 不改绑，回程观测不含 init 帧。真实逐帧 frame_age_ms n=1,500（p95 124.940 ms、超 T_stall 比例 0），capture_age_s n=1,498、load_elapsed n=28；各自分列，与 3.0 s/0.4 s 对照不变。init 为首帧检测器自身 target 类最高分框，不是真值；端到端包含 init 后追帧。原 AC-5 没有回程观测 ≥1,500 的门，不新增样本门、不把 n=29 包装成长段统计或持续跟踪通过。该解释源于补跑F交接/报告 §2f 的读法，不新增义务。正式数据不混入 Tailscale 冒烟。

**使用前与隔离**：`-assets.json.round_f_pre_use_check` 30/30 一致；真实应答器各轮再核方形引擎。`-env.json.sr_system_stack_f` 保留 AC-2 修订 6 二进制兼容与 IR-20/TRT 告警影响未明标注，AC-16 三处重定向各轮满足、外部会话服务写入按 IR-18 单列；受保护根零写入记录保留。AC-12 两条内容禁键命中与具名驱动缓存文件名单列的现状按下方 IR-21/22 追加解释，不改任何原扫描或证据文件。本轮没有 NEW_OBLIGATION/新 AC；其他 AC、阈值、停止总则及信封不放宽。

**f1-echo 信封内返工归因**：`STOP(RELAY_INTEGRITY)` 源于桌面机中继转发残留旧会话 latest 指针，属于 §2.1 SR / AC-4 中继实现缺陷；返工提交以 git 主题「P1-ENG-JET-001 K1K3K4补跑F 返工（RELAY_INTEGRITY）：桌面机中继不转发启动前残留的旧会话 latest.json」运行时解析（已核实本轮指定提交），增加旧指针守卫，编排先清空桌面运行目录；`tests/test_eng_jet_relay.py::DesktopStalePointer.test_stale_pointer_from_previous_session_not_forwarded` 的既有 `sr-f/rework-red.log`/`rework-green.log` 记录修前失败 1/修后通过 1，返工 focused 67/67，收工 focused 69/69（只读已有日志，不重跑），板侧代码不变；f1及重跑全部计入阶段 A，失败原文与 `rework_rounds` 保留，不签修复正确性通过、不回退消耗、不增加轮数。

**阶段 A 与停点自证现状（补跑F裁定时快照；SUB:2 现状见下一节落实）**：S0–S2 与 SR 均已有读数，不等于阶段 A 验收通过；累计以 `-ledger.json.dimensions` 为准：SR **5/5 已耗尽**（冒烟 1、返工 1、成功正式 3），每轮最高 61,704,978 B ≤100 MB；墙钟 8,545/28,800 s、到板 18,870,709/100,000,000 B、板上盘 5,163,883,873/13,000,000,000 B、Mac outputs 70,218,799/2,000,000,000 B，Mac 模型/pip 仍 0。四项分别为：(1) IR-21/22 合同歧义现已闭合，须实现角色按裁定更新分列与风险后重判冻结自证，不由接受角色替签；(2) focused 69/69 已有，停点全套未跑、SUB:2 未签，**不成立**；(3) 零 Unity、无已知 Unity 失败，记 N/A，不能替代 AC-14 的独立复核 UNITY_NA 附议；(4) 实现交接已更新范围/状态/候选提交/风险，后续仍须把本轮裁定带入停点证据、准备准确候选范围，复核文件与附议尚未产生。四项未齐，**不送 C1、不启动依赖结果的后续实现**；Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不变。当前用户项与签发后条件计划见「needs_user（补跑F；当前用户交接，2026-10-03）」。

### SUB:2 落实：§5 Mac 与 IR-9（2026-10-03，CLARIFY）

登记轮次 `K1K3K4落实SUB2`；本轮为已签授权的合同落实，不是 C 轮，不改核对表。依据 `docs/authorizations.md` 2026-10-03「P1-ENG-JET-001 — 用户按推荐签发 SUB:2：停点全套的 Mac 本机 CPU 模型额度（一次全套）（supervisor 会话代录）」授权范围 (1)，`request_id` = `P1-ENG-JET-001:b0a5f79c:SUB:2` 已由用户直接签发；不是 supervisor SUB 代拍，执行信封子额度块仍未签。本节落实接受合同门，之后可由 supervisor 在 Mac mini 派实现执行以下范围。

**§5 阶段 A Mac 生效值与 AC-10 修订 3（CLARIFY，续答 IR-9，关联 AC-13 修订 1）**：原 §5 申请表、09-28 生效表及 10-02 Mac mini CLARIFY 的「零模型」原文保留；仅停点全套一次内的模型加载由本节已签额度替代，其余场景仍为零模型。授权范围逐字转写为：**Mac mini 本机 CPU、停点全套一次内的模型加载 NanoTrack ≤ 4、YOLOE ≤ 2、DINOv2 ≤ 2、CSRT ≤ 2；零 pip、零下载、零新增模型；成功、失败、重试全部计入，耗尽即停回用户。** 不覆盖 SR 重跑、阶段 B 或 §7 (i)–(m)；S3–S5 仍不放行。Mac `outputs/eng-jet/` ≤ 2 GB 及其他 AC、阈值、信封维度均不变。测试夹具的真实模型加载仍按 IR-9 计入，各模型额度分别核对，不以失败或重试回退、不相互转用；一次全套不授权第二次全套。缺少既有包/模型、预计次数超限或无法在既有环境完成时，停下保留结果回报，不安装、下载或自行扩大范围。

**实现证据 ledger 的读法（AC-10/15）**：事实源为 §3.4 定义的 `docs/evidence/P1-ENG-JET-001-ledger.json`，派发所称 `-K1K3K4-ledger.json` 不存在，不新建第二份账。当前 `dimensions.mac.models=0` 与 `pip=0` 是截至补跑F的实际消耗，不是 SUB:2 的现行额度上限；`pending_user` 目前只有 (h)–(n)，尚无 SUB:2 已签记录。下一实现沿既有账本补入具名 request_id、上述授权标题与已签范围，分别记录四种模型加载的累计次数及一次全套使用情况，实际消耗按成功/失败/重试全部计入；保留 (h)–(n) 原记录，尤其 (n) 仍是仅签阶段 A，不能把 SUB:2 读成阶段 B 已签。交接「待用户（补跑F）」及更早证据中的 SUB:2 未签原文是当时快照，下一实现同步当前状态并保留历史。本轮接受角色不改证据文件、不认领任何模型消耗。

**下一实现派发的可执行范围（Mac mini）**：

1. 按 IR-21 / AC-12 修订 3 与 IR-22 / AC-12 修订 4 更新证据读法与具名命中分列，保留原扫描 `violations`、`true_violation_count=2`、`ac12_clean=false` 及原扫描指针；仅将具名两份控制协议内容命中与真正隔离违规分列，不改原扫描、不泛化豁免、不宣称 AC-12 已验收。沿 AC-4 修订 2 / AC-5 修订 1 同步统计、分母与风险：保留收据启动/收工事件和轮间物理链路异常，回程 n=29 与逐帧年龄 n=1,500 分列，不称长期链路稳定或持续跟踪通过。保持 S1 `STOP(FP16_BOX_DIVERGENCE)`、S2 `STOP(FRAME_DROP)` 及 SR 的 S1/S2 双 `RESUMED_AFTER_USER_RULING` 标记与各自账本指针，保留 IR-20 告警影响未明等限制。
2. 先按最新 ledger 与既有环境只读核对 SUB:2 预计模型加载次数、已有模型与 Mac 输出余量；在本节额度内跑停点全套一次。输出写 `docs/evidence/` 下本项证据文件，只回显摘要、不带 `-v`，区分基线已有失败与本批新增失败；需 `lap` 的跟踪器测试只读使用数据根 `~/TetheredDroneTracking-full/.venv-yoloe`，不装包。失败不得掩盖或改为通过，新增失败按既有停点规则先处理；超额动作、再次全套或新环境需求回用户，不凭 focused 替代全套。本派发只做 Mac 离线测试与证据整理，不重跑 S1/S2/SR、不上板改动、不新增清理。
3. 沿 AC 逐条补证，在 `docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md` 的具名停点自证小节重判 workflow §4.3.1 四项：(1) 范围/接口冻结；(2) 相称测试/编译通过；(3) 已知 Unity 失败已修复或注明不适用；(4) 复核范围、状态板、候选提交与未验证风险已更新。整理冻结候选与完整准确范围、提交推送；四项成立才交接受 `C1@K1K3K4`，之后才交新鲜上下文独立 `R1@K1K3K4` 与 AC-14 `UNITY_NA` 附议。当前全套未跑、自证未齐，本记录不替实现自证、不签独立复核、不推定 `DONE`；Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不变。

**交接 Consuming 判据**：按 engineering §8 引用的 AGENTS.md / workflow §5、§7 规则 0，`Consuming=no`（本派发无 scenario/session/run ID、无 Play、无 API 预算）；SUB:2 本机 CPU 模型加载是须累计入账的已签信封维度，不能把轨道「零消耗」读作无需模型额度。现有消耗性轨道及其他工作项均不改动。

### K1K3K4全套记录核对（2026-10-03）

登记轮次 `K1K3K4全套待裁定`；本轮只核对跑前事实和合同读法，零消耗，不是 C 轮，不改核对表。完整读取交接「K1K3K4全套执行记录与停点自证」及其 AC 指针、自证、待裁定/待用户，核对 `-ledger.json.envelope.sub2`、`dimensions.mac.sub2`（含 prechecks）、报告 §2g、`-assets.json.board_manifest.ac12_split.ir21_ir22_reading` 与 `-relay.json.contract_readings_full_suite`。

- **真实加载路径成立，次数是跑前预计而非实际消耗**：`tests/test_det_assoc_carrier.py:CarrierSelfTest` 的两例各调用一次 `create_tracker("det-assoc-v1")`；`controller/trackers.py:create_tracker` 的 compat 分支不注入替身，`DetAssocTracker.__init__` 先核权重/冻结文件及库版本，再调用 `_default_model_loader` → `ultralytics.YOLO`。第二例的 init=False 在构造之后，不能免计加载；首例引用帧共 768 张，另一个基线载体使用 ScriptedTracker、不增加真实加载。只读核实主树冻结规格、权重、冻结文件及前两帧存在，权重大小 5,458,330 B、权重/冻结文件哈希与规格一致；数据根解释器可定位 ultralytics/lap/cv2。因此预计两次真实 det-assoc 加载有依据，未列名模型不能归为 SUB:2 的 YOLOE。
- **CPU 推理读法须纠正**：上述两例没有显式 device 参数；冻结 `device_policy.preferred=mps`、fallback=cpu，`_resolve_device` 在 MPS 可用时返回 mps，`_detect` 原样传给 predict。本轮以数据根解释器 `python -B` 只读查询 torch 2.13.0 的 `torch.backends.mps.is_available()` 得 True（未构造模型、未推理、未跑测试）。所以 prechecks/交接所称首例“在 CPU 推理 768 帧”不能成立；当前原样全套会选择 MPS。SUB:2 及申请 A 的本机 CPU 字面均不授权 MPS 推理，本轮不扩大任何设备/计算维度。
- **部分回放归属成立**：`ResidentCarrierReplay` 的 `_acq_ready()` 所需数据根 scout-1 目录存在；测试先调用 `tools.eng_acq.e2.replay_segment`，再以 CachedModel 和 `model_loader=lambda path: model` 驱动 resident 载体，各回放 60 帧，真实模型加载为 0，合计两次部分序列回放。其 AC-6 来源与类注释的“本项消耗账本”均归 ACQ-001，不是本项；ACQ-001 合同「§5 阶段 1+2 信封」有序列回放/CPU 墙钟上限，但暂停节明确恢复前不放行其他消耗。不能消费其余额，也不能自动改记本项；归属变更须用户签发。
- **证据同步已记录，不等于验收**：IR-21/22 分列仍保留原 `true_violation_count=2`、`ac12_clean=false` 与扫描指针；具名协议内容命中 2、扣除后隔离违规 0；AC-4 启动/收工事件、轮间异常与 AC-5 回程 n=29/逐帧年龄 n=1,500 分列，S1/S2 STOP、SR PASS 及双 RESUMED 标记保留。本轮仅核对读法，不签这些 AC 满足或独立复核通过。

`dimensions.mac.sub2` 的全套次数 0、四种模型实际加载均 0、other_model_loads 空，与“跑前即停”记录一致，不能把预计 2 次记作已用。Mac 输出当前账本 70,222,459 B（跑前 70,218,799 B）仍在 2 GB 内。focused 72/72 是既有记录，本轮未重跑；全套未跑，自证第 2 项仍不成立，第 1 项待实现重判，不能送 C1。IR-23 现行解释与未签 SUB:5 见「待裁定」及「needs_user（K1K3K4全套；当前用户交接，2026-10-03）」；原 SUB:2 落实中的下一实现范围受本次停因约束，不能继续派发全套。Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不变。

### SUB:5 A 落实与 CPU 执行方案核对（2026-10-03，CLARIFY）

登记轮次 `K1K3K4落实SUB5`；本轮为合同落实与只读执行方案核对，不是 C 轮，不改核对表。依据 `docs/authorizations.md` 2026-10-03「P1-ENG-JET-001 — 用户选 SUB:5 方案 A：停点全套内追加 det-assoc 检测器加载 ≤ 2 次、两次零模型部分回放归本项（supervisor 会话代录）」授权范围，用户已直接签发 `P1-ENG-JET-001:b0a5f79c:SUB:5` 的 A；不是 supervisor SUB 代拍，SUB 子额度块仍未签。上节、IR-23 修订 4 及原 A/B 请求中的“未签”是签发前快照，现行合同以本节追加修订为准。

**§5 Mac 生效值、AC-10 修订 5（CLARIFY，解释修订 3/4，续答 IR-9/23，关联 AC-13 修订 1）**：授权范围逐字转写如下：

> (1) 在 SUB:2 已签的同一次（仍只一次）停点全套内，追加 Mac mini 本机 CPU 的 det-assoc 冻结检测器加载 ≤ 2 次（成功、失败、重试全部计入，耗尽即停回用户）；(2) `ResidentCarrierReplay` 的 2 次零模型部分序列回放计入本项，不计入、不消费已暂停的 `P1-ENG-ACQ-001` 信封，ACQ-001 暂停状态不变。其余逐字不变：SUB:2 四种模型上限、零 pip、零下载、零新增模型、Mac outputs ≤ 2 GB；不覆盖 SR 重跑、阶段 B、§7 (i)–(m)，S3–S5 不放行。本条只签「本机 CPU」：不授权 MPS 推理，不授权改测试执行设备/方法、改 skip 门或设环境变量绕门；须先由接受角色落实 AC-10/§5 与计账口径并核对 CPU 执行方案，方案需上述任何变化时列明再交用户，落实前全套保持 0 次。

SUB:2 四种分列上限仍是 **NanoTrack ≤ 4、YOLOE ≤ 2、DINOv2 ≤ 2、CSRT ≤ 2**。det-assoc 指 `config/det-assoc-v1.models.json` 定义的冻结 `last.pt` / ultralytics YOLO，不并入 YOLOE，不与四种额度转用；除本次全套的具名例外外，其他未列名模型及其他场景模型额度仍 0。两次加载包含随后两例的 CPU 推理，不能把加载时 CPU 反序列化当作授权随后 MPS 推理，也不授权另跑两例或第二次全套。回放例外只覆盖该次全套 `ResidentCarrierReplay.test_resident_carrier_matches_replay` 的线束与缓存载体各一次部分回放（各 60 帧），不恢复 ACQ-001，不继承其 CPU 墙钟/回放余额，不扩大为任意序列回放。成功、失败、重试均累计；预计超额即不启动，耗尽即停回用户。

**ledger 计账口径（下一 Implementation 才写证据）**：沿用唯一 `docs/evidence/P1-ENG-JET-001-ledger.json`，在既有账补 SUB:5 具名 request_id、上述完整授权标题与生效范围（可分列 `envelope.sub5` / `dimensions.mac.sub5`）；`envelope.sub2` 的四种上限保留，原 `other_models_max=0` 仅由修订 5 对具名 det-assoc 作例外，其他模型仍 0。分别累计 det-assoc 加载/构造尝试（≤2，成功/失败/重试含在内）与具名零模型部分回放（≤2），并计入 `dimensions.mac.models` 的模型总数，回放不计模型加载；不得与 `sub2.other_model_loads` 重复扣账。一次全套仍用同一 `dimensions.mac.sub2.full_suite_runs` 总计（≤1），SUB:5 不产生第二个全套额度；保留加载明细、结果、执行设备、两种回放归属与原 prechecks，不将预计次数记作已用。账本目前 `full_suite_runs=0`、四种加载全 0、`other_model_loads={}`，尚无 SUB:5 实际执行记录；授权追加不是消耗。原 prechecks 的“CPU 推理”已由上节纠正，下一实现补当前读法、保留原记录。`pending_user` (h)–(n) 不改读成阶段 B 已签。接受角色本轮不改 ledger/交接证据，不运行生成工具。

**只读核对结果：当前不存在符合已签字面的 CPU 全套跑法，全套不放行。** 核对出处如下：

| 路径 | 既存依据与本轮结果 | 是否改变测试设备/方法 |
|---|---|---|
| 原样 Carrier 两例 | `tests/test_det_assoc_carrier.py:CarrierSelfTest` 两例只调用 `create_tracker("det-assoc-v1")`，无设备 CLI/配置入口；`controller/trackers.py:create_tracker` compat 分支只传 spec。`**resident_options` 在 `resident=False` 时拒绝，不能借该参数传 device，也不能改成 resident（不同接口）。 | 原样没有变化，但会选 MPS，不符合授权。 |
| 冻结策略自动回退 | `config/det-assoc-v1.models.json.device_policy` = preferred mps / fallback cpu；`_resolve_device` 只有 MPS 不可用/探测异常才返回 CPU，`_detect` 将结果显式传给 predict；`_default_model_loader` 只构造 YOLO，没有全套设备配置入口。 | 真实 MPS 不可用时的自然回退本身无变化；当前条件不成立，不能诱造异常或屏蔽 MPS。 |
| 构造器显式 CPU | `controller/det_assoc_tracker.py:DetAssocTracker.__init__(device="cpu")` 是既存参数，给定时跳过探测；同文件 resident 缓存回放已显式使用，但真实 Carrier 两例没有调用此参数。 | 把两例接到该参数需改测试调用/执行方法；参数既存不等于本次获准改变调用。 |
| 换规格/解释器/进程注入 | Carrier 的 SPEC 固定主树规格；唯一数据根环境变量 `ENG_DET_DATA_ROOT` 不选设备，只会影响帧与 skip 条件。unittest discover 不给两例传 device；wrapper/monkeypatch、强制设备探测、改 preferred 或换环境均改变方法/规格/门或计算路径。 | 均需用户另定，不能作为 SUB:5 内的现成跑法。 |

本轮只读命令为数据根解释器 `python -B` 导入 torch 并查询 `torch.__version__` / `torch.backends.mps.is_available()`、用 `importlib.util.find_spec` 定位三库及只读 JSON：torch **2.13.0**、MPS **True**、ultralytics/lap/cv2 均可定位，冻结 preferred **mps** / fallback **cpu**。未导入测试模块、未构造模型、未推理、未跑测试、未设置环境变量。这与上轮相同；自然 CPU 回退不成立。原候选全套命令仍不可执行；只签 A 不能解决这一冲突。全套仍 0 次，自证第 2 项不成立，第 1 项待实现重判，不送 C1。Owner = `用户`、Status = `WAITING_FOR_USER_RULING`；Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不变。具体选项见「needs_user（SUB:5 CPU 执行方案；当前用户交接，2026-10-03）」。

### CPU-1 落实与下一实现范围（2026-10-03，CLARIFY）

登记轮次 `K1K3K4落实CPU1`；本轮只落实线 A 已签授权，不是 C 轮，不改核对表。依据 `docs/authorizations.md` 2026-10-03「P1-ENG-JET-001 — 用户选 SUB:5 CPU 执行方案 CPU-1：CarrierSelfTest 两例改用既存显式 CPU 构造参数（supervisor 会话代录）」授权范围，以及同日 SUB:5 A、SUB:2 条目。用户已选 CPU-1，原话后半关于 S3–S5 的提问不是阶段 B 签发。本节追加解释替代先前修订 5、IR-23 与 needs_user 中“CPU 方案待用户／全套不放行”的当前执行前置，签前原文保留；当前等待实现改测试并完成跑前核查，满足下述条件才跑一次全套。

**AC-10 修订 6（CLARIFY，解释修订 5，续答 IR-9/23，关联 AC-13 修订 1）**：仅授权 Implementation 将 `tests/test_det_assoc_carrier.py:CarrierSelfTest` 的 `test_carrier_matches_caliber_b_from_first_update`、`test_init_false_uses_existing_failure_path` 两处 `create_tracker("det-assoc-v1")` 构造调用改为既存 `DetAssocTracker(spec_path=SPEC, device="cpu")`，并作两处所需的导入替换。使用默认 compat、真实默认模型加载器及关联器，不传替身、不关闭版本核验；保留两例其余流程、断言、原 skip、冻结规格/权重和数据根解释器，不改 controller/config。只读代码依据：显式 `device` 分支跳过 `_resolve_device`，`_detect` 将该值传入 predict；`_default_model_loader` 仍构造真实 `ultralytics.YOLO`。这是本项 AC-10／K1K3K4 候选范围内的测试执行设备与方法改动；AC-10 对 `Assets/`、`controller/`、`config/` 的空 diff 要求原样保留，`tests/` 的具名改动不构成该要求的豁免，不授权修改工厂或冻结规格。

用户已认可真实工厂集成覆盖损失：两例不再经过 `create_tracker`；既有 `tests/test_det_assoc_tracker.py:test_factory_registers_det_assoc_and_cli_default_unchanged` 替身测试仍在全套，不能当作真实工厂集成覆盖。CPU 与原口径 B 逐帧完全相等的断言可能失败；失败如实保留并停下回报，不换基线、不放宽断言、不根据结果改数。此修订不预签测试通过或停点自证成立，不新增 AC。

**下一 Implementation 派发（Mac mini；按顺序执行）**：

1. 先完成上述两处具名测试改动及必要导入，以静态 diff／AST 等不加载真实模型的核查确认仅两例构造方式变化，其他流程、断言和 skip 保留；不在全套外再跑 Carrier 两例，不用真实 focused／探测消耗加载额度。
2. 跑前按最新 `docs/evidence/P1-ENG-JET-001-ledger.json` 只读核对全 tests 的所有可达真实加载器（含子进程及构造失败尝试）、实际执行设备（两例必须 CPU）、回放归属、已有包/模型及 Mac `outputs/eng-jet/` 余量。不能只核这两例，不能把旧 prechecks 当作本次最新核查。SUB:2 仍为 NanoTrack ≤4、YOLOE ≤2、DINOv2 ≤2、CSRT ≤2；SUB:5 A 为 det-assoc 冻结检测器加载 ≤2、具名 `ResidentCarrierReplay` 两次零模型部分回放（各 60 帧）归本项，不扣 ACQ-001。一次全套总计 ≤1，Mac outputs ≤2 GB；成功、失败、重试累计，各模型额度不转用，其他未列名模型仍 0。任何预计超额、需要 MPS／改设备探测／改 skip／设环境变量、缺包或需下载安装：不跑，保留核查结果回用户。
3. 两处改动与跑前核查均满足后，仅在 SUB:2 + SUB:5 A 余额内，从仓库根目录用数据根既有解释器执行以下一次完整全套；不删用例、不加 `-v`，不附加设备／离线环境变量，不在失败后重跑。输出写本项证据文件，只回显摘要：

   ```sh
   ~/TetheredDroneTracking-full/.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-JET-001-full-suite.log 2>&1
   ```

4. 基线已有失败与本批新增失败分列，记录 skip／缺依赖及与 FRAME-001 R7 基线的环境、覆盖差异；基线候选与日志来源运行时解析，不换基线、不将 skip 或失败记通过。两例 CPU 比较等新增失败如实保留并停下回报，不为消除结果而改数、放宽断言或自行重跑。沿唯一 ledger 补 SUB:5 的具名 request_id、完整授权标题、生效范围及 CPU-1 授权/合同指针；按修订 5 分列加载／构造尝试（≤2）与部分回放（≤2），模型合计不重复扣账，原 prechecks 保留并补当前读法，全套次数仍共用 `dimensions.mac.sub2.full_suite_runs`（≤1），不另立账或第二个全套额度。
5. 沿 AC 补证并同步报告/状态，在 `docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md` 具名小节按 AC 编号附指针，重判 workflow §4.3.1 四项：范围/接口冻结、相称测试/编译通过、已知 Unity 失败已修复或不适用、复核范围/状态板/候选提交/未验证风险齐备。整理准确完整候选范围、提交推送；四项成立才交 `C1@K1K3K4`，再独立 R1 与 AC-14 `UNITY_NA` 附议。全套仍未跑、自证第 2 项仍不成立，本轮不替实现自证、不签独立复核或 DONE。若后续线 B 给候选加代码，是否需要再跑全套由届时接受裁定，本轮不预设、不签追加额度。

仅 Mac 离线测试及证据整理，不重跑 S1/S2/SR、不上板改动、不清理、不改 SSH。S1/S2 STOP、SR PASS/双 RESUMED、IR-20 限制、SR 5/5 耗尽、阶段 B 全部维度 0 与 ACQ-001 暂停不变。`Consuming=no`：无正式 scenario/session/run ID、Play 或 API 预算；临时测试夹具标识不作为正式采集 ID，模型加载与两次部分回放仍按已签信封如实计账，轨道“零消耗”不豁免资源额度。交接 Owner = Implementation，Status = `WAITING_IMPLEMENTATION_CPU1_AND_FULL_SUITE`，Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不变。

### K1K3K4全套CPU1记录核对（2026-10-03）

登记轮次 `K1K3K4全套CPU1待裁定`；线 A 接受侧零消耗记录核对与合同答复，不是 C 轮，不改核对表、不签独立复核。依据交接「K1K3K4全套CPU1执行记录与停点自证」全节、全套日志、报告 §2h、唯一 ledger 的 `envelope.sub5` / `dimensions.mac.sub2` / `dimensions.mac.sub5`、FRAME-001 R7 全套交接及 result.json，以及账本 10-03 CPU-1、SUB:5 A、SUB:2 条目；已读 CPU1 开工与收工两提交完整增量（提交由具名主题运行时解析）及直接关联代码。

- **日志与比较成立**：`Ran 2136 tests in 235.682s`，`FAILED (failures=27, errors=10, skipped=56)`，退出 1；从原日志提取 FAIL/ERROR 名称，与 R7 `current_failure_names` 做集合比较，仍在/未出现/新增 = **7/18/30**。仍在的 7 条是五个导入错误及 CSRT 两入口；四个 eng_sft 模块报 `tests.fixtures` 缺失，language_k_binding 实际报 `tests.test_language_selector` 缺失，不能把五条异常逐字都写作前者。未出现的 18 条中，12 条为旧 loopback 绑定拒绝，6 条有缺归档 skip 门；无逐名 skip 日志，不把“未出现”一律称修复/通过。skip **19→56** 只有聚合可比，不能逐名对照，报告 §2h 的“6 条转为 skip”应读作静态门归因。
- **Carrier 首例确实失败**：767 个 update 条目的 10 个不一致索引为 `[2, 4, 5, 6, 8, 12, 17, 18, 19, 20]`。日志只显示首个索引 2 的 `(state, box, reason)`：state/reason 相同，宽差约 4.8e-8，另外三分量相同；其余 9 个形态未知，不能推广为全体差异均在 1e-7 或全体 state/reason 不变。`tests/test_det_assoc_carrier.py:CarrierSelfTest` 使用 `enumerate(zip(carrier, plugin))` 比较（carrier 源于 `records[1:]`），索引从 0 计；按本线束 update 从帧 1 起的映射，索引 2 对应 `frame_id=3`，原交接“帧 2”须区分索引与帧标识。权重、init、library_frame_id、长度断言在失败前通过；该断言之后的 confidence_source、观测桥字段集、临时目录外写入比较未执行到，不能以“其余流程断言均通过”概括。次例无失败记录，结合共用类级门与无方法 skip 的代码，可读作执行通过；不恢复真实工厂集成覆盖。
- **scene006 的 29 条可静态分列**：25 FAIL + 4 ERROR；按类为 Probe 10、CandidateManifest 1、CandidateManifestP2 7、AppearanceTolerance 10、StrictJson 1。这些调用只注入 proposer/embedder，没有传 `path_resolver`；`tools/run_scene006_probe.py:run_probe` 仍先走 `verify_weight_binding`，由 `controller/reanchor.py:verify_file` 检查主树 YOLOE 权重，然后才核 DINOv2 来源/权重与 NanoTrack ONNX。当前具名路径缺失，首个 YOLOE 检查即拒绝 → `FAIL_WEIGHT_HASH`、recall 默认 None，解释日志的状态不符和 None 下标错误。相关测试、处置链、配置相对 R7 全套零 diff；这是读码归因，未在补齐资产环境验证，不外推这些用例后续断言正确。
- **计账读法与已签范围一致**：全套 **1/1**（SUB:2、SUB:5 共用）；det-assoc **2/2 CPU**；具名 Resident 部分回放 **2/2**、各 60 帧，归本项、不扣 ACQ-001，但属于门成立后的保守计账，聚合日志不证明逐名实际执行。NanoTrack 2 是构造尝试上界、真实权重读取 0；CSRT 两入口失败、真实实例 0；YOLOE/DINOv2 0、其他模型空，模型合计 6 不含回放。Mac outputs 70,231,574 B≤2 GB，Assets/controller/config 空 diff，ledger `within_envelope: true`。全套、det-assoc、回放额度均用尽；四种余额不能脱离同一次全套另用，**不放行第二次全套**。
- **覆盖与网络限制保留**：开工新增 `common.ENVELOPE_SUB5` / `ledger.sub5_dimension` 无专门单测；既有 LedgerSub2 本次无失败记录，不是 SUB:5 自动回归证明。开发期手工越界调用仅是实现披露，本轮不执行、不签为独立核实；计账函数主要比较累计数量，`within_envelope` 不证明设备/具名范围/网络均经运行时检测。未设 `YOLO_OFFLINE` 的 DNS 探测及可能匿名 usage 事件已披露；无流量监测，日志无下载/安装行不能推出外联 0，“离线”仅指任务性质，不代表实测断网。
- **执行版本读法纠正（CLARIFY，解释 AC-13/14）**：交接所称执行 HEAD 为开工提交，与 ledger 的 `full_suite_run_items[].tested_head` / `git_diff_assets_controller_config.head_at_build` 并非同一标识；后者所在提交时间在全套窗口内，按现有记录不能把它当作跑前 HEAD 采样。两者间 tests/tools/controller/Assets/config 零 diff，只证明本次运行代码相同；起始版本沿开工主题解析，机器字段沿 ledger 解析，保留两个取样时点及此限制，不手抄 SHA、不改写原证据。下一零消耗证据整理沿既有 AC-13/14 纠正该读法。

**停点与下一动作**：第 1 项暂不成立（Carrier 处置尚待用户，可能改变候选/执行方法）；第 2 项不成立（Carrier 比较失败，scene006 仅静态归因），本轮不靠 R7 先例预签成立。R7 针对窄修把具名 loopback 环境拒绝列作局限，并未证明本次 CPU-1 比较通过。IR-24/25 答复见「待裁定」，用户选项原文与条件派发见「needs_user（K1K3K4全套CPU1；当前用户交接，2026-10-03）」。当前不交 C1，Owner=用户、Status=`WAITING_USER_CARRIER_SCENE006_RULING`；Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不变。本轮只追加既有条款 CLARIFY，无 NEW_OBLIGATION/新 AC，无额度签发。

### 1A落实与证据整理（2026-10-03，CLARIFY）

登记轮次 `K1K3K4落实1A`；线 A 接受侧落实合同，不是 C 轮，不改核对表、不签独立复核。唯一授权依据为 `docs/authorizations.md` 2026-10-03「P1-ENG-JET-001 — 用户裁定线 A 全套结果：Carrier CPU 失败选 A（具名例外进 C1/R1）、scene006 29 条按环境原因分列（supervisor 会话代录）」的授权范围 (1)–(3)。此前「K1K3K4全套CPU1记录核对」、IR-24/25 与末节用户选项保留为裁定前快照；当前交接按本节执行。

**AC-10 修订 8（CLARIFY，解释修订 6/7；续答 IR-24，关联 AC-13/14、§7.1）**：用户明确许可携带 `tests/test_det_assoc_carrier.py::CarrierSelfTest::test_carrier_matches_caliber_b_from_first_update` 的 CPU 逐帧比较已知失败、其余 9 个差异帧形态未知及该例比较后断言未执行，作为**本次 K1K3K4 停点 workflow §4.3.1 第 2 项的具名例外**进入 `C1@K1K3K4` 与独立 `R1@K1K3K4`。修订 7 的等待用户约束仅在此具名范围由本修订落实，不记测试通过、不预定 C1/R1 结论，复核可判阻断。不改断言、不换基线、不重算参考、不改设备，不改阈值或 AC 判据。全套 1/1、det-assoc 2/2、部分回放 2/2 不回退；不新增任何额度，不放行第二次全套或任何真实模型/回放/SR 重跑，复核需要上述重跑时另申请后才能执行。

**AC-13 修订 3（CLARIFY，解释修订 2；续答 IR-25，关联 AC-10/14）**：用户已选 scene006 29 条按本机环境原因分列；仍保留为**相对 R7 新增 29 条（25 FAIL + 4 ERROR）**。静态归因是主树缺 re-anchor/NanoTrack 权重，实际处置链先在 YOLOE 权重哈希绑定拒绝，相关代码相对 R7 零 diff；这是读码归因、未在补齐资产环境验证，后续行为未验证。不改作 R7 原有失败、不记通过，不向主树 `runtime/` 放资产、不签第二次全套。按此携带环境覆盖限制交核对/复核判断，不扩大 Carrier 具名例外到其他未披露失败。

**下一 Implementation 派发（Mac mini，仅整理证据、零消耗）**：允许更新 `docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md`、`docs/evidence/P1-ENG-JET-001-report.md` 的叙述/索引与本项状态板；只读既有日志、JSON、git 和关联代码，不改运行时代码、测试、工具、配置或原始测量记录。不得跑测试、构造/加载真实模型或推理、回放、上板/ssh、下载安装，不改 skip/环境变量诱发绕门。具体顺序：

1. 将本节现行读法同步到交接「状态与结论」、CPU1 执行记录/自证与报告 §2h；原失败、日志与计账保持。Carrier 不一致集合是 update 条目从 0 起的索引 `[2, 4, 5, 6, 8, 12, 17, 18, 19, 20]`，索引 2 对应 `frame_id=3`，不可写作帧 2。首个差异约 4.8e-8、state/reason 同只能用于该条；其余 9 条未知。比较前四类断言已执行，比较后的 confidence_source、观测桥字段集、临时目录外写入比较未执行；次例无失败记录不恢复真实工厂覆盖。
2. 执行起始版本沿唯一主题 `^P1-ENG-JET-001 K1K3K4全套CPU1 开工` 运行时解析；ledger `full_suite_run_items[].tested_head` 与 `git_diff_assets_controller_config.head_at_build` 从现有 JSON 读取。分别注明记录来源与取样时点：后者对应提交在运行窗口内，不能称跑前 HEAD 采样；只读比较两版本的 tests/tools/controller/Assets/config 空 diff 支持代码相同，不能补造当时采样。保留原机器字段，不手抄 SHA，不改写原证据。
3. 分列已有/未出现/新增 = 7/18/30，新增按 Carrier 1 + scene006 环境 29；五个导入错误区分四个 `tests.fixtures` 与 language_k_binding 的 `tests.test_language_selector`。18 个未出现不可一律称修复：12 个旧 loopback 拒绝与 6 个缺归档静态 skip 门分别注明；skip 19→56 只有聚合记录、不能逐名比对。保留 Resident 实际执行/跳过未知、NanoTrack/CSRT 尝试数为静态上界、未监测 DNS/可能匿名 usage、日志无下载安装不证明外联 0、SUB:5 `ENVELOPE_SUB5`/`sub5_dimension` 无专门单测等未验证项。既有 LedgerSub2 无失败不能替代 SUB:5 自动覆盖。S1/S2 STOP、SR 5/5 用尽与 S3–S5 NOT_RUN 原文/主张上限保留。
4. 按 §7.1 与 AC-10 修订 6 冻结完整候选范围：`.gitignore` 的本项 outputs 排除；`tools/eng_jet/{__init__,common,env_probe,fastlayer_bench,replay_publish,relay,track_responder,assets,ledger,evidence}.py`；`tests/test_eng_jet_{bench,guards,relay,track_responder}.py`；CPU-1 的 `tests/test_det_assoc_carrier.py` 两处构造与必要导入；§3.4 的八个 JSON、report、handoff、focused-tests.log 与 full-suite.log。这是当前已实现范围的完整声明，不授权新增实现或删减 §7.1 的合同范围；AC-1…16 连同修订逐条附证据，未运行项保留 NOT_RUN，不声称满足。提案、账本、状态板、派发登记、发令表等混入总 diff 的文件同样列入清单，不能按实现声明自行排除；完整 diff 留给 C1/独立复核检查。
5. 基线从唯一主题 `^P1-ENG-JET-001 K1K3K4 开工` 的父提交解析；下一实现登记轮次建议为 `K1K3K4证据整理1A`，收工提交主题固定以 `P1-ENG-JET-001 K1K3K4证据整理1A 收工` 开头。候选以 `git log main --format=%H --grep='^P1-ENG-JET-001 K1K3K4证据整理1A 收工'` 运行时解析，必须仅返回一条、实际触及 handoff，且已推送并为 origin/main 祖先；交接写该解析规则，不手抄 SHA、不用当前 HEAD 替代。提交后以 `git diff --name-only <base>..<candidate>` 与完整 `git diff <base>..<candidate>` 核实全部范围；`git diff --stat <base>..<candidate> -- Assets controller config` 应为空。遇主题歧义、非预期治理代码变化或范围未冻结，停下回报，不挑选文件拼候选；收工角色写入检查与 docs 自检照常执行，不代替功能测试证据。
6. 在 handoff 具名小节按 AC 编号逐条附指针，重判 workflow §4.3.1 四项：①范围/接口冻结；②相称测试如实保留失败，明确本次 Carrier 用户具名例外与 scene006 环境覆盖限制，其余失败/skip 限制一并披露，不涂成“通过”；③零 Unity、不适用已知 Unity 失败，AC-14 `UNITY_NA` 仍待复核附议；④准确候选/范围、状态板、未验证风险与后续复核文件入口齐备（实现不得写复核文件）。四项成立且例外明确适用于 C1/R1 才交 Acceptance 的 `C1@K1K3K4`；任一仍缺即保持实现交接并回报具体缺口，不自动开 C/R。

当前 Owner = Implementation，Status = `WAITING_IMPLEMENTATION_EVIDENCE_SELF_PROOF`；本轮尚未重判自证或交 C1，Overall `IMPLEMENTING`、Lifecycle `ACTIVE` 不变。无新 AC/NEW_OBLIGATION，无额度签发；C1 只读完整候选/AC/直接关联代码、零测试，独立 R1 的结论与 `UNITY_NA` 附议均未预签。

### CLARIFY 表

只追加解释与已授权变更；原 §5 申请表及 09-28 生效表保留，设备现行字面以本表为准。

| 解释条款 | CLARIFY | 依据 | 日期 |
|---|---|---|---|
| §5 阶段 A「设备」、§7 (h)、AC-4…6/10/15 | 桌面机改为用户 **Mac mini**，只跑回放器与中继、零模型；Mac 维度生效值仍为零 pip、零模型、`outputs/eng-jet/` ≤ 2 GB。正式链路为 **Mac mini ↔ Jetson 有线以太网直连或同一交换机**，用户接线并设固定 IP、确认可达后执行。时延与时钟读数仅代表 mini↔Jetson；中继正确性与断链判据不变，不外推 Air/Unity 宿主。其余阶段 A 信封维度不变，阶段 B 全部维度仍为 0；已有 Air 冒烟原文保留、不改写机器或转作 mini 证据。 | `docs/authorizations.md` 2026-10-02「P1-ENG-JET-001 — 用户选 B：SR 桌面端改为 Mac mini、本项派发移到 mini，MacBook Air 只做需 Unity 才能验证的任务」授权范围 (a) | 2026-10-02 |
| §5 阶段 A「pip / 源码编译（板上）」、§6「本栈」、AC-2/3/13 | S1/S2 在板上现有 NGC 容器 `nvcr.io/nvidia/pytorch:25.08-py3` 内执行；§5「复用 NVIDIA torch、不重装 torch」与 §6「本栈」的现行字面改述为容器实跑栈（版本以实跑时记录为准，不以镜像元数据代替实跑证明），主张不代表 JP7.2 系统 TensorRT 10.16 栈。容器内新增 pip 及其依赖累计仍在阶段 A ≤ 8 包/300 MB 内、板上磁盘 ≤ 5 GB、模型下载 0；任一维度将超限即停下回用户，不自行扩额。落实全文与 AC-2 修订 2（关联 AC-3/13）见「S1/S2 容器栈落实」。 | `docs/authorizations.md` 2026-10-02「P1-ENG-JET-001 — 用户选 torch 路径 A（板上现有 NGC 容器）并暂停一切 codex 派发至用户告知额度更新」授权范围 (a) | 2026-10-02 |
| §5 阶段 A「pip / 源码编译（板上）」、§6「本栈」、AC-2/3/13 | S1/S2 改在板上系统 Python 执行（`--system-site-packages` venv 或等价方式复用系统 TensorRT 10.16）；上一行（容器栈）对 S1/S2 的执行栈部分由本行替代，原文保留、不删除。§6「本栈」对 S1/S2 恢复原字面（JP7.2/CUDA 13.2/TRT 10.16，版本以实跑记录为准）。torch/torchvision 轮子及其 pip 传递依赖的下载与安装属新增额度 SUB:1（`P1-ENG-JET-001:b0a5f79c:SUB:1`，申请值见「needs_user」题 4），用户逐字签发前为 0、不派实现安装。ultralytics/lap 等既有 5 包在系统 venv 的同版本重装属信封内工程性重试、不并入 SUB:1；容器 venv 与 wheels 的保留/清理及计数口径、AC-2 修订 5（关联 AC-3/13）、python3.12 0.15→0.17 给实现角色的提示见「S1/S2 系统栈落实（B）」。AC 判据与阈值不变，模型下载 0，阶段 B 全部维度仍 0。 | `docs/authorizations.md` 2026-10-02「P1-ENG-JET-001 — 用户选执行栈 B 的前置：经 Mac mini ssh 在板上 sudo 安装 python3-pip/python3-venv（用户输入密码；supervisor 会话代录）」授权范围 (a)(c) | 2026-10-02 |
| §5 阶段 A 执行信封追加（SUB:1）与 SUB:3、AC-10 | SUB:1 经用户逐字签发，并经 SUB:3 把下载字节上限由 ≤ 3.5 GB 改为现行生效值 **≤ 6.5 GB**（含已计 3,093,609,695 B），包数 ≤ 32、安装后新增磁盘 ≤ 8 GB、板上磁盘维度 ≤ 13 GB、来源与 pin 不变。安装方式合同解释：禁止 `pip install --dry-run`/`--report` 类取回轮子体的解析方式；按已实测依赖清单逐个 `pip download --no-deps`（核 sha256）后 `pip install --no-index --find-links` 离线按文件安装，已取回的官方 cu130 torch/torchvision 轮子复用不重下；2,318,455,950 B 干跑取回属实现方法失误，计入 SUB:1 已用量不回退。装后先验证 SM 87 与共存再跑 S1/S2。落实全文见「SUB:3 落实与安装方式合同解释」。 | `docs/authorizations.md` 2026-10-02「用户按申请值签发 torch/torchvision 下载与安装额度（官方 cu130 源；SUB:1…）」与「用户按推荐签发 SUB:3：torch 依赖下载上限 3.5 GB → 6.5 GB」 | 2026-10-02 |
| §5 阶段 A「Mac / 设备」、IR-9、AC-10 修订 3（关联 AC-13 修订 1） | 用户已签 SUB:2；仅 Mac mini 本机 CPU 停点全套一次内加载 NanoTrack ≤ 4、YOLOE ≤ 2、DINOv2 ≤ 2、CSRT ≤ 2；零 pip、零下载、零新增模型，成功/失败/重试累计、耗尽回用户；其他场景仍零模型，Mac outputs ≤ 2 GB 不变。不覆盖 SR 重跑、阶段 B、§7 (i)–(m)，S3–S5 不放行。IR-9 不豁免加载计数与全套义务；原未签文字保留为历史，现行范围与 ledger 读法见「SUB:2 落实：§5 Mac 与 IR-9」。 | `docs/authorizations.md` 2026-10-03「P1-ENG-JET-001 — 用户按推荐签发 SUB:2：停点全套的 Mac 本机 CPU 模型额度（一次全套）（supervisor 会话代录）」授权范围 (1) | 2026-10-03 |
| §5 Mac、IR-9/23、AC-10 修订 4（关联 AC-13 修订 1） | 未列名 det-assoc 加载仍 0；ACQ-001 暂停项回放不得借用/自行改归属；本机 CPU 不涵盖 MPS。当前数据根原样全套无合同内放行读法，SUB:5 的 A/B 均须用户裁定后落实，未裁定不换解释器、不改 skip 或环境变量绕门；详见「待裁定」IR-23。 | SUB:2 账本授权范围 (1)、交接 IR-23、ACQ-001 暂停节；「K1K3K4全套记录核对」 | 2026-10-03 |
| §5 Mac、IR-9/23、AC-10 修订 5（解释修订 3/4，关联 AC-13 修订 1） | 用户已签 SUB:5 A：同一次（仍只一次）停点全套追加 Mac mini 本机 CPU det-assoc 冻结检测器加载≤2，成功/失败/重试累计、耗尽回用户；ResidentCarrierReplay 两次零模型部分回放归本项、不扣 ACQ-001，暂停不变。SUB:2 四种上限、零 pip/下载/新增模型、Mac outputs≤2 GB 与其余边界不变；不授权 MPS、改测试设备/方法、改 skip 或环境变量绕门。额度与计账已落实，但当前无合规 CPU 跑法，全套不放行，交用户定方案；全文见「SUB:5 A 落实与 CPU 执行方案核对」。 | `docs/authorizations.md` 2026-10-03「P1-ENG-JET-001 — 用户选 SUB:5 方案 A：停点全套内追加 det-assoc 检测器加载 ≤ 2 次、两次零模型部分回放归本项（supervisor 会话代录）」授权范围 | 2026-10-03 |
| §5 Mac、IR-9/23、AC-10 修订 6（解释修订 5，关联 AC-13 修订 1） | 用户已选 CPU-1：仅 CarrierSelfTest 两处构造及必要导入改为既存 `DetAssocTracker(spec_path=SPEC, device="cpu")`，默认 compat、真实默认加载器/关联器；其余流程/断言/skip、冻结规格/权重、数据根解释器保留，controller/config 空 diff 不变。具名测试改动属本项候选范围；用户已认可真实工厂覆盖损失与 CPU 比较失败风险，失败保留并停下、不换基线/放宽断言/改数。SUB:2 + SUB:5 A 上限及一次全套不变，改动完成且跑前核查满足才执行；全文、条件命令与计账见「CPU-1 落实与下一实现范围」。 | `docs/authorizations.md` 2026-10-03「P1-ENG-JET-001 — 用户选 SUB:5 CPU 执行方案 CPU-1：CarrierSelfTest 两例改用既存显式 CPU 构造参数（supervisor 会话代录）」授权范围；同日 SUB:5 A、SUB:2 | 2026-10-03 |

| 题 4 装后验证第一项、AC-2/3/13 | 题 6 选 A 落实：装后验证第一项「arch list 含 sm_87」由 **AC-2 修订 6** 替换为「arch list 含同主版本（8.x）、算力 ≤ 8.7 的 `sm_8x` SASS（本板实测为 sm_80），且装后 matmul/TRT 共存三项与 cuDNN 卷积、CUDA nms、归约诊断全过」；本次实测逐项满足（`docs/evidence/P1-ENG-JET-001-env.json`「s1s2_system_stack_c」），S1/S2 续跑；S1/S2 读数注明 torch 无 sm_87 原生 SASS、按二进制兼容运行；出现 `no kernel image` 等不兼容报错即停回用户，不换源、不变通。其余 AC、阈值、信封维度不变；零新增下载，不签 SUB:4。落实全文见决策记录「题 6 选 A 落实：装后验证第一项替代判据（AC-2 修订 6）」。 | `docs/authorizations.md` 2026-10-02「P1-ENG-JET-001 — 用户选题 6 A：官方 torch 无 sm_87 时接受同主版本二进制兼容读法继续 S1/S2（supervisor 会话代录）」授权范围 | 2026-10-02 |
| AC-10 修订 7（解释修订 6；IR-24） | CPU-1 风险获认可不等于比较通过或失败后自动可进 C1。已失败仍保留并停下，用户明确裁定前不进 C1/R1；全套 1/1 用尽、断言/基线/设备/信封不变。详见「待裁定」IR-24。 | CPU-1 账本授权范围、修订 6、交接 IR-24 | 2026-10-03 |
| AC-13 修订 2（解释修订 1，关联 AC-10/14；IR-25） | 保留相对 R7 新增 29 条，同时分列为本机缺权重环境失败（静态归因、未补资产验证）；不替换 R7 基线、不记通过。索引/帧号、聚合 skip、断言执行范围及版本取样时点按「K1K3K4全套CPU1记录核对」准确披露；无新 AC/新增验证额度。 | 交接 IR-25、原日志、R7 result.json、run_probe/verify_weight_binding；本轮记录核对 | 2026-10-03 |
| AC-10 修订 8（解释修订 6/7；IR-24，关联 AC-13/14、§7.1） | 用户已选 1A：Carrier 首例 CPU 比较已知失败、其余 9 个差异未知、比较后断言未执行，作为本次停点条件 2 具名例外可进 C1/R1；不记通过、不预定结论、复核可阻断。不改断言/基线/设备/阈值/AC 判据，不新增额度、不重跑；仅整理证据并重判四项，成立才交 C1。详见「1A落实与证据整理」。 | 账本 2026-10-03「P1-ENG-JET-001 — 用户裁定线 A 全套结果…」授权范围 (1)(3) | 2026-10-03 |
| AC-13 修订 3（解释修订 2；IR-25，关联 AC-10/14） | 用户已选环境分列；scene006 29 条仍为相对 R7 新增，静态缺权重归因与后续行为未验证同时保留；不记通过、不补主树资产。证据同步、索引/版本解析、完整候选冻结与未验证项按「1A落实与证据整理」执行；零测试/真实加载/回放/上板。 | 同一账本授权范围 (2)(3)，IR-25 与「K1K3K4全套CPU1记录核对」 | 2026-10-03 |
| §5 Mac、AC-10 修订 9（解释修订 3/5/6，关联 AC-13/14） | 用户直接签 SUB:6 (a)，新候选全套 1 次及所有分列额度、耗尽即停与唯一 ledger 计账见「SUB:6 落实与新候选两项例外」；旧已用计数不回退、不转用，阶段 B 仍 0。 | 账本 2026-10-04「P1-ENG-JET-001 — 用户签发 SUB:6…」授权范围 (1)(3) | 2026-10-04 |
| AC-10 修订 10（解释修订 8）、AC-13 修订 4（解释修订 3） | 为新候选重新具名 Carrier/scene006 两项例外，仅原记录同名同类失败；未知/未执行断言、相对 R7 新增与静态环境归因保留，不记通过、复核可阻断；其他新增失败不在例外内。完整边界见同节。 | 同一账本授权范围 (2)，原 10-03 全套结果条目 (1)(2) | 2026-10-04 |
| AC-10 修订 11（解释修订 9，关联 AC-13/14、§7.1） | 仅 K1K3K4R2返工 候选以零模型 focused 83/83 + R2-1 修前红/修后绿代替停点全套；候选解析、证据与只读第 2 项判定见「R2-1 窄修候选例外落实与 R3 交接」。不记全套已跑或通过，不签额度，返工直接交 R3。 | 账本 2026-10-04「P1-ENG-JET-001 — 用户选 (a)：R2-1 窄修候选以 focused…」授权范围 (1)(3) | 2026-10-04 |
| AC-10 修订 12（解释修订 10）、AC-13 修订 5（解释修订 4） | SUB:6 Carrier/scene006 两项具名例外沿用到同一窄修候选，仅同名同类失败、边界不变；失败/未知/未执行与环境分列保留，不记通过、复核可阻断；其他新增失败不在例外内。完整边界见同节。 | 同一账本授权范围 (2)；SUB:6 授权范围 (2) | 2026-10-04 |
| AC-11 修订 1（解释 AC-11，关联 AC-12；IR-26） | 接受全部 a7 3,168 帧两键哈希参照，不扩回放/评估/上板帧或额度，新增来源注明只用于今后证据，历史不改；理由见「待裁定」IR-26。 | R1-3、交接「K1K3K4R1注记修补：…」§6 | 2026-10-04 |
| AC-4 修订 3（解释修订 2）、AC-6 修订 2（解释修订 1；IR-27） | 可能截断的传输中事件计数 None=未知，不是 0；缺 disconnects 判假，原完整输入通过线与历史读数不变；理由见「待裁定」IR-27。 | R1-2/R1-4、同一交接 §6 | 2026-10-04 |

- 2026-09-28 · D1 · `PROPOSED`（构思角色，supervisor 派发 `P1-ENG-JET-001-D1-20260928T204201Z-5bf2`）· 依据账本 09-28 拓扑 1–3、账本 09-28 D.8 与设计 §8 / engineering §9；范围 = A3 §6 第 0–5 步 + 中继测试，不做优化/剪枝/INT8、不改接口 A、不重训、不搬 Unity；零消耗、零代码；`Workflow: engineering-v1` 为申请，待接受角色裁定；§5 各维度签发前为 0。
- 2026-09-28 · D1 · `REVISION_REQUESTED`（接受角色，设计退修 1）· AR1-1…3 与 (a)–(n) 见下节「D1 接受裁定」。
- 2026-09-28 · D2 · `PROPOSED`（构思角色，supervisor 派发 `P1-ENG-JET-001-D2-20260928T212546Z-fa00`；回应 AR1-1…3，设计退修计数 1）· AR1-1 → §0 事实 6/9（smoke 组成、首见/重复行索引、预热三帧只读核实）、§2.1 S3（预热 3 次 / 首见行 25 / 重复行 7 / 解析分母 32 / `CACHE_SUSPECT`）、§3.3「S3 请求序」、§3.4、AC-7、AC-11/12（smoke 上板与剥字段）、§5（查询计数）、§6 数据限制、§8；AR1-2 → §2.1「verdict 三值与处置总则」（原因码闭集、`STOP` 停全部后续、`RESUMED_AFTER_USER_RULING`）、§2.1 S1（两分量 verdict、`FP16_BOX_DIVERGENCE`、用户二选一）、§3.1、AC-2、AC-13、§6 (ii)；AR1-3 → §7.3 表（(h)–(n) 推荐/缺省/恢复条件）、§2.1 S0/SR/S3 行、§2.2、§3.2 链路、§5 表头与设备/量化主机/传输/系统设置行、§7.4、AC-1/AC-4…6/AC-15（新增）。D1 裁定 (a)–(g) 作为修订依据写入 §7.2 与对应节（(b) `K1K3K4`、(c) 探测阈值口径、(e) 中继进 K1）。主线判据（§1 逐字引用）、接口 A、Unity 零改动、不优化/不剪枝/不 INT8/不换模型、§5 签发前为 0 均不变；零消耗、零代码；`engineering-v1` 仍为申请，(h)–(n) 仍待用户，接受裁定节原文未改。

### D1 接受裁定（2026-09-28）

**REVISION_REQUESTED**。§1 已逐字引用 `docs/project-background.md` §3，独立立项、拓扑和接口依赖符合账本 09-28 拓扑及 D.8；INT4 是对既定 2B 模型的板端可行性探测，未触及 v1 明禁的 INT8、更大模型或剪枝。退修原因是下列可执行合同与未授权选项的默认动作尚不闭合；工程轨道申请在 `ACCEPTED` 前**不生效**，§5 仅为申请值，所有维度仍为 0，不得派实现或动用设备/下载/量化/云资源。

| ID | 必须由构思角色在 D2 修订的事项 | 核对依据 |
|---|---|
| AR1-1 | 闭合 S3/AC-7 的烟测样本与分母：§0 事实 9、§8 均写 32 行仅 25 张不同帧，但 AC-7 又规定“帧不互异”即不满足。明确 32 行解析失败统计、新帧 p50/p95 的唯一帧集合、重复帧及首见/稳态的归类；若改用其他已归档帧，列出来源、选择规则与只读核验数字，并同步 §2.1、AC-7 和预算估算。不得以缓存命中的重复帧充当新帧延迟。 | 提案 §0 事实 9、§2.1 S3、§4 AC-7、§8；A3 §3.3/§6 步骤 3。 |
| AR1-2 | 闭合 S1 框差超 1e-3 的三态 verdict：§2.1 一面将其列为通过线，一面规定“不 STOP”，而全协议只有 `PASS`/`STOP`/`NOT_RUN(<原因>)`。写清超线时究竟给哪一态、是否停后续 S2–S5、何时交用户，不得把超线记 `PASS` 或静默继续。同步 AC-2/AC-13 的证据与报告口径。 | 提案 §2.1 S1 与步骤总则、§4 AC-2/AC-13；A3 §6 步骤 1。 |
| AR1-3 | 将 §7 (h)–(n) 的“按推荐执行并标待用户确认”改为逐项未答复时的缺省停止/跳过和恢复条件，并同步 §2.1、§5、§6 的冲突叙述。特别是 (l) 未授权不得 `systemctl isolate`，S0 非 headless 须先停；(i)/(n) 未签阶段 B 不租云/量化/上板 S3–S5；(h) 未有正式链路不得给 SR 正式结论。不得把推荐项写成用户裁定。 | 提案 §7 待用户段、§2.1 S0、§5；账本 09-28 拓扑信封及 D.8。 |

§7 (a)–(g) 接受侧裁定：**(a)** 新 ID 的 `Workflow: engineering-v1` 申请符合工程任务类型，待 D2 合同闭合并 `ACCEPTED` 时才可逐字生效；**(b)** 选 `K1K3K4` 合并单候选，量化后的 C2 三态决策变化是 K3 的检查对象，K1 涵盖跨机时间/中继语义，K4 涵盖 609 行指标；K2/K5 当前不触发；**(c)** S4 的各组绝对差 ≤3 pp、G5 硬给框不上升、解析失败 0 可作预注册探测阈值，报告仍须列出原始分母和逐组差值，不得称研究资格通过；**(d)** 两阶段申请形状可向用户提交，接受侧不签发任一维度；**(e)** 现有文件帧/控制字段不改，但新 TCP 搬运及两机时间语义须进 K1，不得表述为不需 K1 的“纯搬运”；**(f)** 同意 S0→S1→S2→SR→S3→S4→S5 的依赖顺序，实际运行仍受各步 STOP 和用户信封约束；**(g)** 同意 §3.4 的证据文件规划与 `outputs/eng-jet/` 忽略规划，候选停点名随 (b) 改为 `K1K3K4`。本段仅裁定设计取向，未形成 AC/BC，也未授权执行。

§7 (h)–(n) 仍**待用户**，本轮不代选。未答复及 §5 未逐字签发时全部执行额度为 0；即使将来某阶段有签发，也不能据本轮推荐擅自接线/租云/运行可选 S3a/重刷/执行 `systemctl isolate`/切换功耗模式或推定下一阶段已获签发。构思角色按 AR1-3 把每项默认处置写成可核对合同；需要选择设备、链路、主机或额度的事项继续交用户。与 `P1-ENG-ACQ-001` 保持 §3.5 的接口依赖，本轮不修改其合同或状态。

open_items: AR1-1,AR1-2,AR1-3

### D2 接受裁定（2026-09-28）

**ACCEPTED**。逐项核对 D1 退修：

| D1 项 | D2 核对与关闭依据 |
|---|---|
| AR1-1 | **关闭**。§0 事实 6/9 与 §8 给出只读来源及 32 行、25 个互异 `frame_id`、7 个重复行（索引 8/9/10/12/18/20/22）；§2.1 S3、§3.3 与 AC-7 把 a7 三帧预热排除，首见 25 行计新帧 p50/p95，重复 7 行单列缓存核查，32 行计解析失败；§5 按每路径 35 次计预算。没有把重复请求算作新帧。 |
| AR1-2 | **关闭**。§2.1 总则与 S1 把一致性超线定为 `STOP(FP16_BOX_DIVERGENCE)`，S2、SR、S3–S5 均 `NOT_RUN`；AC-2/AC-13 要求差值证据、原 verdict 与用户恢复裁定指针。只有用户逐字裁定后才可标 `RESUMED_AFTER_USER_RULING(S1)`，不得把 STOP 改 PASS。 |
| AR1-3 | **关闭**。§7.3 (h)–(n) 逐项列推荐、未答复缺省与恢复条件；§2.1 S0/SR/S3、§2.2、§5 与 AC-1/4–6/15 同步禁用正式链路结论、量化、S3a、重刷、`systemctl isolate`、`nvpmodel -m` 和未签阶段 B。推荐项尚非用户裁定。 |

**轨道与范围裁定。** 提案头逐字申请 `Workflow: engineering-v1`；本项是用户 2026-09-28 账本 D.8 点名的独立板端工程探测，六项任务合同（§1–§6）齐备，现逐字裁定 **`Workflow: engineering-v1` 生效**。§1 逐字引用 `docs/project-background.md` §3；§2.3 禁止优化、剪枝、INT8、换更大模型、Unity 上板、接口 A 改型及部署研究主张。A3 §6 的 0–5 步由 §2.1 的可证伪读数执行；S1 的 50 ms 是报告参考线、200 ms 是本工程探测的 STOP 门，二者均在 AC-2 留证，不产生快层研究资格主张。SR 只新增跨机搬运与时间测量，不修改 Unity 文件桥、控制协议和 ACQ-001 的状态机/解析器/伺服。§7 (a)–(g) 维持 D1 已裁定的取向：`K1K3K4` 合并单候选，S4 阈值只作探测判断，中继纳入 K1，证据命名与顺序按 §7.1/§7.2 执行；K2/K5 当前不触发。候选须先 `C1@K1K3K4`，再独立 `R1@K1K3K4`。`UNITY_NA` 只是申请，须复核角色附议与板上硬件证据后才能收尾。

**接受侧 AC 核对矩阵。** §4 的 AC-1…15 是唯一验收条款；本矩阵补足复核项、证明方式和标签，逐项索引原条款，不新增或覆盖义务。`BASE` 指 D2 接受时的基线，日期均为 2026-09-28。

| AC | 复核项 | 证明方式 | 标签 | 日期 |
|---|---|---|---|---|
| AC-1 | 边界失败/文档一致 | artifact: `docs/evidence/P1-ENG-JET-001-env.json` | BASE | 2026-09-28 |
| AC-2 | 行为/边界失败 | artifact: `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1」 | BASE | 2026-09-28 |
| AC-3 | 行为/测试覆盖 | artifact: `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S2」 | BASE | 2026-09-28 |
| AC-4 | 几何时序/测试覆盖 | artifact: `docs/evidence/P1-ENG-JET-001-relay.json`「forward」 | BASE | 2026-09-28 |
| AC-5 | 几何时序/边界失败 | artifact: `docs/evidence/P1-ENG-JET-001-relay.json`「return」 | BASE | 2026-09-28 |
| AC-6 | 行为/边界失败 | artifact: `docs/evidence/P1-ENG-JET-001-relay.json`「disconnect」 | BASE | 2026-09-28 |
| AC-7 | 行为/测试覆盖 | artifact: `docs/evidence/P1-ENG-JET-001-vlm.json` | BASE | 2026-09-28 |
| AC-8 | 行为/文档一致 | artifact: `docs/evidence/P1-ENG-JET-001-quant-equivalence.json` | BASE | 2026-09-28 |
| AC-9 | 行为/测试覆盖 | artifact: `docs/evidence/P1-ENG-JET-001-coresidency.json` | BASE | 2026-09-28 |
| AC-10 | 边界失败/文档一致 | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json` | BASE | 2026-09-28 |
| AC-11 | 边界失败/文档一致 | artifact: `docs/evidence/P1-ENG-JET-001-assets.json` | BASE | 2026-09-28 |
| AC-12 | 边界失败/测试覆盖 | artifact: `docs/evidence/P1-ENG-JET-001-assets.json`「board_manifest」 | BASE | 2026-09-28 |
| AC-13 | 文档一致 | artifact: `docs/evidence/P1-ENG-JET-001-report.md` | BASE | 2026-09-28 |
| AC-14 | 测试覆盖/文档一致 | artifact: `docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md` | BASE | 2026-09-28 |
| AC-15 | 边界失败/文档一致 | artifact: `docs/evidence/P1-ENG-JET-001-ledger.json`「pending_user」 | BASE | 2026-09-28 |

**待用户与执行门。** §7 (h)–(n) 均未答复，按 §7.3 各行的「不做」缺省执行；这些选项涉及链路/设备/主机/系统设置/信封，不能交 supervisor 代拍。§5 两阶段数字仅是申请值，现有执行额度仍全为 0；用户须先逐字签发独立的阶段 A 设备与额度信封，方可派实现和开始任何下载、传输或上板运行。推荐先签阶段 A；S0–S2 通过后再单独决定阶段 B。阶段 A 签发也不自动授权 §7 (h)–(m) 的任选动作；未答复的 SR 正式轮及对应 AC-4…6 不能记满足。没有实现者证据、独立复核与相应硬件证据前不记 `DONE`。

open_items: none

### 阶段B签发包刷新（2026-10-03，线 B）

登记轮次 `阶段B签发包刷新`；Owner = `用户`，Status = `WAITING_USER_STAGEB_RULING`。本节是零消耗的申请与用户选项包，不是签发、AC 修订、C 轮或独立复核。依据账本 2026-10-03「P1-ENG-JET-001 — 用户授权本次破例并行…」范围 (1)–(5)，仅维护线 B；§5、§7 及既有决策原文保留。阶段 B 全部维度仍为 0，(i)(j) 未答复，(n) 仅答「先签阶段 A」；下列推荐均须用户另定、逐字入账并由接受角色落实后才有执行效力。本轮未联网核价/查依赖、未 ssh，以下硬件事实均为既有取证快照。

#### 1. 自 D2 以来的新事实（指针 + 一句结论）

| 指针 | 影响阶段 B 的结论 |
|---|---|
| `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1.square」；`-report.md` §2d；本提案「题 7 选 (α) 落实」 | S1 保留 `STOP(FP16_BOX_DIVERGENCE)`，用户 (α) 只放行既有方形 FP16 引擎续跑，不把一致性失败改为 PASS。 |
| `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S2.runs.15hz」；`-report.md` §2e；本提案「S2 处置选 (α′) 落实」 | S2 保留 `STOP(FRAME_DROP)`（15 Hz、218 丢帧），用户 (α′) 放行原范围正式 SR，不签阶段 B。 |
| `docs/evidence/P1-ENG-JET-001-relay.json`「verdict」「forward」「return」「disconnect」「rework_rounds」；`-ledger.json.dimensions.sr_rounds` | 正式 SR 读数 PASS，冒烟/返工/成功轮累计 5/5 耗尽，双 RESUMED 标记与失败史保留；这不是独立复核或阶段 A 验收。 |
| 本提案「S1/S2 系统栈落实（B）」「SUB:3 落实与安装方式合同解释」「题 6 选 A 落实」；`docs/evidence/P1-ENG-JET-001-relay.json.environment.runtime_stack` | 实跑为无容器系统 Python 3.12.3、系统 TensorRT 10.16.2.10、官方 cu130 torch 2.9.1，torch 无 sm_87 原生 SASS，兼容核验只覆盖已实跑算子。 |
| `docs/evidence/P1-ENG-JET-001-env.json`「sr_system_stack_f.board_post」「readings.free_m」「tegrastats_idle」；`-fastlayer.json.S2.runs.15hz.tegrastats`；`-ledger.json.dimensions.board_disk` | SR收尾磁盘可用 165,474,566,144 B，本项盘占用 5,163,883,873 B；可见 RAM 7,485（原命令 MB 单位）、空闲窗口最高 725 MB、S2 最高 2,125 MB，尚无 VLM/共驻内存证据。 |
| 本提案「CLARIFY 表」Mac mini 行；账本 10-02「用户选 B：SR 桌面端改为 Mac mini…」；`docs/evidence/P1-ENG-JET-001-relay.json.link` | 桌面端现为 Mac mini，有线 192.168.8.1 ↔ Jetson 192.168.8.2，正式读数不代表 Air/Unity 宿主或缆内链路。 |
| `docs/evidence/P1-ENG-JET-001-ledger.json.dimensions`；本提案「SUB:2 落实：§5 Mac 与 IR-9」「SUB:5 A 落实与 CPU 执行方案核对」 | 阶段 A 余额与 Mac 的具名例外均不转用给阶段 B，SR 剩余轮数为 0，其他余额见下方快照。 |
| `docs/evidence/P1-ENG-JET-001-vlm.json`、`-quant-equivalence.json`、`-coresidency.json` | S3–S5 均 `NOT_RUN(阶段 B 信封未签)`，没有板端 VLM、等价或共驻结论。 |

阶段 A 余额快照仅为本申请的依据，发令前必须从最新 ledger 重算：板上墙钟余 **20,255 s**（8,545/28,800）；到板余 **81,129,291 B**；板上盘在阶段 A 13 GB 上限下余 **7,836,116,127 B**；既有 pip 余 **1 包 / 57,247,361 B**；SUB:1 下载余 **883,642,289 B**、包数余 **9**、新增盘余 **3,170,027,375 B**；Mac outputs 快照余 **1,929,777,541 B**。这些是不同维度，不相互抵扣，不覆盖 VLM 下载/量化/查询。SUB:2/SUB:5 仅限其具名用途，不讨论或处理线 A 的执行进度。

#### 2. §5 / §7 (n) 字面前提缺口

「S0–S2 PASS 后再签阶段 B」尚不成立：S0 PASS，S1/S2 STOP；§2.1 的 RESUMED 规则只说明用户允许哪些后续动作，不会把 STOP 变为 PASS。账本 (α) 与 (α′) 的范围均明确阶段 B 未签，不能合并推定阶段 B 已获准。

| 用户读法 | 代价与推荐 |
|---|---|
| **N-A：认可带 S1/S2 双 `RESUMED_AFTER_USER_RULING` 申请阶段 B，保留 STOP、原阈值与负结果** | **推荐**：可继续回答 Q2/Q3；这是申请前提的具名阶段边界例外，须另签完整阶段 B 信封，并明确 S5 基准，不等于部署通过。 |
| N-B：维持 S0–S2 全 PASS 的字面，本项止于阶段 A | 不启动 S3–S5，无法回答 Q2/Q3；停止范围的收口由用户另定，不以 CLOSED 冒充验收，不自行清理板子。 |
| N-C：用户另给读法/另立后续工作项 | 可拆开阶段或改探测目标，但须明确合同、设备、预算及继承限制，准备成本增加；本轮不拟定放宽阈值的替代合同。 |

此题列为 **阶段B:1**。N-A 的推荐理由是已有时延/热稳态描述性读数可供共驻比较，继续 VLM 探测有价值；一致性与丢帧负结果不会因此消失。

#### 3. S3–S5 合同逐点核对

| 点 | 分类 | 字面核对与后续动作 |
|---|---|---|
| S5「快层按 S2 帧率回放」 | **需用户定**（阶段B:2） | S2 实际只有 15 Hz，30 Hz 条件未达；推荐仍用 **15 Hz、同方形引擎/同循环回放与丢帧计数**，不降到 5 Hz、不剔除冷启动/周期丢帧。S2 FRAME_DROP 表明共驻可能失败，不能把 α′ 当成放行 S5 或改压力档。选择另一帧率须明确改合同与可比性代价。 |
| S5「快层 p95 ≤ S1 的 2 倍且 ≤100 ms」 | **需用户定**（阶段B:3） | 推荐以 S1 **方形** `S1.square.latency.update_p95_ms`（n=320，59.2934 ms）为基准，照原公式取两线交集（2倍约118.5868 ms，故100 ms 更严）；保留 S1 STOP，不取矩形、不取 S2 最好格、不改门。用户也可选择不认可该 STOP 读数为基准而暂不跑 S5，或提出新的基准合同（另裁）。 |
| S3 3b 编译/依赖 | **接受可在 CLARIFY 内定**（仅既有路径解释） | §2.1 已定板上 llama.cpp CUDA 构建、arch=87，无容器是系统栈 B 的自然落点；复用系统 CUDA/工具链、将源码/构建/运行件放 `~/eng-jet/`，按 AC-16 重定向缓存。已安装 torch 并不证明 vision 可用；当前未查到板上 cmake/编译器、llama.cpp 源码版本与完整依赖清单。选定并签额度后接受侧可固定来源/构建命令和依赖闭集；缺工具、需 apt/sudo/新容器/换栈或超6包即回用户，不能在 CLARIFY 内扩额。 |
| S3 3c 编译/依赖 | **接受可在 CLARIFY 内定**（仅既有路径解释） | 继续「指定 x86 Linux GPU 合并/AWQ → 板上系统 TensorRT 建引擎」，不借用失效容器 TRT 10.13 栈、不复制 x86 引擎作板端证明。TRT Edge-LLM/绑定在该 sysvenv 的依赖兼容与完整清单未查到；已有 torch 冒烟不证明新算子支持。需要内核参数仍 STOP(KERNEL_PARAM_REQUIRED)，需要换系统栈/安装系统包仍交用户（阶段B:4/6）。 |
| S3 样本与通过线 | **无影响** | 每路径3预热(a7 0/100/200)+32行；首见25行 p50≤1.6 s、p95≤2.5 s，repeat7行单列，解析0/32、图像token=300、峰值≤4.6 GB；原 nearest-rank、CACHE_SUSPECT、GRID_MISMATCH 与停止规则均能作为未来实测判据，现无可执行/过线证据。 |
| S4 样本与通过线 | **无影响** | 仍609行盲文件、gold留 Mac mini，C2量化对C2 bf16逐组差≤3 pp/G5硬给框不增/解析0/609；S4-a只能对官方base与base bf16，不能充当C2等价。AWQ校准输入/工具版本在现有证据中未查到，不得擅取gold、改划分或把评分609行改作调参；若准备时需新数据/采样合同，先交用户。 |
| S5 VLM样本与相对时延线 | **无影响** | 按盲文件行序首180个互异sha，每10 s一次、30 min，p95(n=180)≤该**同一产物/运行时**S3首见p95的1.3倍；不跨base/C2或不同量化路径借基准。S3没有过线产物就无可执行的S5对象，不能跳过STOP静默运行。 |
| 板上盘≤40 GB | **需用户定**（阶段B:6） | 推荐40 GB为 `~/eng-jet/` **A+B累计实际占用上限**，含已装sysvenv/缓存/既有运行目录，不另给40 GB增量；当前约5.164 GB，申请口径余34,836,116,127 B。df物理余量不能代签额度。 |
| 峰值RAM≤7.0 GiB | **接受可在 CLARIFY 内定**（取证单位解释，不改门） | RAM 7,485原命令单位与7.0 GiB门不能直接作十进制减法；未来沿原取证口径注明单位、总RAM/进程RSS/统一内存分列。S2最高2,125 MB及S1窗口2,730 MB不是共驻保证；峰值≤7.0 GiB、无NvMap/OOM、swap=0均不变。 |
| S5连续丢帧与OOM取证 | **接受可在 CLARIFY 内定**（解释既有计数/来源） | 保留无连续>2帧丢帧的原门，明确init也计入，不以平均丢帧或S2总丢218替代连续数。IR-1只接受S0的journalctl替代，未推广S5；若无权限取得原要求的dmesg/OOM证据，停下回报用户补录，不能自行sudo或预签无OOM。 |

本表不新增AC、不改通过线。用户选择N-A、阶段B:2/3后才追加具名合同落实；其余「可在CLARIFY内定」只是接受侧边界说明，不授权实施、取证或安装。

#### 4. 刷新后的阶段 B 申请表（仍全部未签）

下表以完整C2探测的租云推荐路径为申请主案；不设主机的缩减案见下一节。GB为十进制字节额度，GiB仅用于原内存门；成功/失败/重试共同计入。无来源/数量的维度仍0，不能借阶段A剩余额度。

| §5维度 | D2原申请 → 刷新申请值与理由 |
|---|---|
| Consuming | 租云yes/本地no → **不变**；租云为yes，当前 `P1-ENG-FRAME-001` 有未暂停Consuming=yes交接，1消耗上限不容第二条。用户须选择等其释放轨道后再租云，或由用户决定暂停/保留哪条；**推荐等待释放**，本轮不改该交接。 |
| 设备 | 原Jetson+用户Mac(Unity宿主)+按(i)量化主机 → Jetson同板同系统栈B + **Mac mini** + 用户所选(i)主机；正式链路复用现有有线，不把Mac mini当Unity宿主，不改SSH/网络设置。 |
| 模型下载 | ≤4条/≤7 GB(base按需、Q4_K_M、mmproj F16、可选Q8_0) → 上限**不变**，推荐本次内容收窄为官方base Q4_K_M≈1.11 GB与mmproj F16≈0.82 GB；base复用下节本机副本、base下载0、Q8_0不申请，其余条目/字节仅供这些具名文件失败重取、不转用。成功/失败/重试共同占≤4条/≤7 GB；不因副本缺损自动下载base或改变产物。C2自转产物走传输。 |
| 板上pip/源码编译 | ≤6包、llama.cpp≤1 h、TRT Edge-LLM编译+建引擎≤3 h → 包数/时长**不变**，复用现有sysvenv torch/系统TRT，不重装torch；补充申请板上pip下载累计≤1 GB、源码归档≤2条/累计≤500 MB（含重取，**预算估算封顶，非已查到的依赖体积**）。源码tag/依赖闭集尚须零消耗准备固定；超限或缺系统工具即停，sudo/apt/新容器0。 |
| 量化主机 | 云≤2 GPU·h/≤4美元，或WSL2≤4 h → 时长/费用**不变**；推荐云x86 Linux GPU≥24 GB、同SFT-002供应商类；4美元作租金/存储/传输等总费用上限，实际价格未查，不能按旧估算直接租。补充申请云端本项工作目录峰值≤20 GB（base/合并副本/量化产物与临时件的估算封顶，实例预装环境另列基线），优先复用预装依赖；新增pip包（含传递依赖）≤12包、下载累计≤3 GB、源码复用同批已核归档（额外源码下载0）。具体pin/清单/安装后占用未查到，必须先固定，超限回用户，不以GPU额度涵盖任意安装。无训练/额外模型API；AWQ校准与量化计入GPU·h。 |
| 传输 | 到板≤10 GB、云↔本机≤10 GB → **不变**且各自按累计双向实传字节计；含base/C2/量化产物、剥字段smoke与评估盲文件/帧、代码源码件，复用阶段A已在板资产；推荐3a不跑时不传bf16 base上板。下载与中继轮数不混算；SR追加轮0。 |
| 板上墙钟 | ≤16 h → **不变**（阶段B独立计，含编译/建引擎、预检、失败/重试、取证及S3–S5）；不自动叠加阶段A余20,255 s。 |
| 板上VLM查询 | ≤2,500次 → **不变**，各路径35次含预热、S4≤3×609、S5 180及CACHE_SUSPECT重跑全部累计；预算不授权越过STOP、不保证能把所有重试跑完。默认跳过3a时3条路径105+1827+180=2112次，余388次；35×4+1827+180=2147是用户选3a时上限规划，非本轮申请执行。 |
| 板上磁盘 | ≤40 GB → 数值**不变**，申请明确为 `~/eng-jet/` A+B累计实际占用≤40 GB（含既有约5.164 GB）；不在阶段A13 GB之上再加40 GB，不授权清理保留件/外部缓存。 |
| Mac | 评分/可选GGUF转换pip≤2，零VLM推理 → **Mac mini仅评分与传输，阶段B新增pip=0、模型加载/合并/转换=0、VLM推理=0**，GGUF转换随(i)放量化主机；追加申请 `outputs/eng-jet/` A+B总占用≤12 GB（原阶段A≤2 GB不变，签B后才替代累计占用上限）：合并bf16约4.3 GB、GGUF+mmproj约1.93 GB、AWQ/临时件及日志余量的估算封顶，未测实际体积。base等既存副本只读、不写数据根；模型中转只落此目录，不借SUB:2/SUB:5覆盖阶段B。 |
| 系统设置 | 只读/按(l)(m)答复，不改内核 → **不变**，(k)(l)(m)未答复的动作仍0；已headless/MAXN_SUPER不意味代理可再次设置。cma、swap、默认target、功耗、锁频、SSH/网络/隐私改动均不申请。 |
| Play/ID/训练/API/发布 | 0/0/0/0/否 → **不变**；此处ID指正式scenario/session/run ID，云账单实例标识按AC-10记录，不据供应商实例ID扩大正式ID范围。 |

**安装与取回方式沿用「SUB:3 落实与安装方式合同解释」**：既有已核sha包/资产优先复用；新pip包按已固定清单逐包 `pip download --no-deps` 核sha，再按本地文件 `--no-index` 离线安装，禁干跑/`--report`取回依赖体，**禁Range GET探大小**；模型/源码同样完整取回、逐条核sha/体积并累计失败字节。清单、pin、下载地点及来源在执行前固定，未知依赖不自动解析/补装。本轮没有进行HEAD/HF API/下载/安装。上表新字节上限为提交用户的申请，绝不从SUB:1余量或用户先前「官方源」授权推导阶段B权限。量化主机磁盘/依赖与Mac中转占用已列新增申请；仍未列数值的维度为0，未查到的清单/兼容性须完成准备，不把本表视为整套路径已可直接执行。

#### 5. §7 (i) 量化主机选项刷新

| 选项 | 覆盖范围 | Consuming与额度量级 | 已知风险与推荐 |
|---|---|---|---|
| **I-A：租云x86 Linux GPU（同SFT-002 vast.ai类，≥24 GB显存）** | 可申请C2 bf16合并→自转GGUF的3b-C2/S4-C2，以及AWQ的3c/S4-C2；官方base 3b/S4-a独立可跑；S5须用本轮S3过线的同一产物；3a仍按(j)。 | **yes**；≤2 GPU·h/总费用≤4美元，云↔本机≤10 GB，板端依上表；未核现价、预装环境/磁盘/依赖仍须准备，不继承SFT-002余额。 | **推荐完整探测选I-A**：已有方案来源明确要求x86 Linux GPU做AWQ，覆盖Q2的C2核心问题；成本/轨道等待、依赖缺项、JP7.2图像路径/内核参数及token=300等风险仍在，不能承诺成功。 |
| I-B：5060 WSL2 | 可申请合并/自转GGUF；3c AWQ只有WSL2实测可用才可跑，不能把5060旧HTTP推理证明当AWQ证明；S4与S5仍受S3过线条件。 | **no**（无Play/正式ID/API），但新增设备使用仍用户定；WSL2≤4 h墙钟、零云；Windows/WSL2安装、依赖/磁盘维度未查到，未签为0。 | 既有方案指5060为8 GB、低于24 GB建议；WSL2 AWQ可行性未查到，可能安装/显存受阻；不推荐先选，不ssh核机器，不继承FAST/LOOP额度。 |
| I-C：不设量化主机，只做官方base GGUF冒烟与S4-a | 3b只官方base，S4-a只base对base bf16；**3c与C2自转GGUF及其S4均 `NOT_RUN(待用户 (i))`**。S5若用户同意以过线base为对象，只是base共驻，不能回答C2共驻/等价。 | **no**；量化主机0/合并0，官方模型下载/板上编译/查询仍须签，不是零设备消耗；建议按实际选择收窄上表，去掉TRT编译和云传输。 | 无租云轨道冲突，最少主机准备；**覆盖不足**，Q2核心C2无法回答。用户若只要先核图像路径可选本案，不能将部分结果当完整探测通过。 |

非GPU合并/转换的证据边界：§3.3列 `merge_and_unload`→bf16→`convert_hf_to_gguf.py`→`llama-quantize`，§5曾申请可选Mac GGUF转换；仓库 `tools/eng_sft/train_lora.py:load_model` 支持将模型移到给定device，但**没有查到本模型在非GPU主机完整合并bf16并转Qwen3-VL视觉GGUF的实跑/兼容/峰值内存证据**。不能把“可选Mac转换”推定为CPU合并已可行，不能擅自指定Mac合并或构造模型验证。现有A3 §3.3仅为方案输入，AWQ主机要求仍按合同x86 Linux GPU；本轮不联网更新厂商结论。复用SFT-002云预算/看门狗工具前，须沿 `docs/implementation-status.md` SCOPE_GAP账本F7/F8处理其负值/并发写入债，不能因同供应商直接复用有缺陷入口。此题 **阶段B:4**。

#### 6. §7 (j) S3a本机副本只读核对与选项

- 本轮对主树及 `~/TetheredDroneTracking-full` 以包含ignored/hidden文件的清单检索：**主树未找到base权重；数据根有** `outputs/eng-loop/P1-ENG-LOOP-001/model/base/`，`model.safetensors` 4,255,140,312 B，config/tokenizer/preprocessor/chat_template等同目录存在；本地HF下载metadata的revision与 `tools/eng_sft/train_lora.py:BASE_REVISION` 一致（按文件读取，标识不手抄）。这是副本存在/元数据一致，不是本轮逐字节完整性验证；使用前按AC-11对全部文件核sha并绑定原来源，不能以metadata代替实测sha。
- `/Volumes` 本轮仅见Claude与Macintosh HD，**T7未挂载**，不据此宣称T7无副本，不挂载、不扫描未接设备。
- 板上不ssh：`docs/evidence/P1-ENG-JET-001-assets.json.stage_b_assets` 的base为NOT_USED、uploaded=false；既有board_manifest没有base副本记录，ledger模型下载0。**未查到板上已有base的证据**，不作板上绝对不存在的断言。

| 用户选项 | 代价与推荐 |
|---|---|
| **J-A：跳过3a，不为3a传base上板** | **推荐**：板上无已证副本，bf16是可选对照，既有RAM读数不保证容纳；本机base留给用户所选量化主机，零base下载，优先测两条量化路径。3a保留NOT_RUN，不能将其AC记满足。 |
| J-B：复用本机base，核完整性后传板跑3a（OOM即止） | 需要用户明确改变“仅板上已有base才跑”的原推荐选择并签到板字节、磁盘、依赖与35查询/失败尝试；约4.26 GB权重+伴随文件，不用新base下载，不把4.6 GB统一内存门放宽。 |
| J-C：等用户提供/确认板上或T7副本 | 等待更长；核身份与字节后再申请，仍不依据口头“有模型”直接跑、仍须阶段B签发。 |

题号 **阶段B:5**。用户选择(j)与选择(i)分开入账，本机有base既不答复(j)，也不签量化主机/传输。

#### 7. 阶段 B 候选与停点安排（关系选项，未改§7.1）

阶段 B 预计新增§3.3的 `tools/eng_jet/adapters.py`、S3–S5线束与对应测试/证据，触及K3量化决策及K4报告指标，相关跨机接口仍须K1核对；不改controller/Assets/config或冻结资产。相对候选、HEAD与上一通过指针均运行时由git/复核机读行解析，不手抄。以下只列关系选项，不预设另一候选的测试、C/R结论或调度动作。

| 选项 | 代价与推荐 |
|---|---|
| B-CAND-1：用户许可并入同一K1K3K4合并候选 | 阶段B新增代码使原全套证据不覆盖最终代码，须另签最终候选一次全套及相称模型/回放额度；若C/R已启动或已通过，按新diff重新核对/复核，可能多一轮，不能拿旧结果验新实现。会与冻结/停点安排相互等待，须用户明确范围边界。 |
| **B-CAND-2：前一候选先完成其C→R路径，阶段B另起稳定停点** | **推荐**：阶段B执行先等待前一候选独立复核的实际处置；若不通过，用户先决定阻断处置，不推定可启动依赖实现。阶段B最终代码另做四项自证、全套→接受C→独立R，需另签具名全套模型/回放额度；S1/S2 STOP与SR既有证据只按原边界继承，SR5/5不重跑。额外停点/复核成本明确，可避免混淆两组证据范围。 |
| B-CAND-3：阶段B另立work item/止于阶段A | 要新提案、继承清单与独立信封；现项AC-7…9未运行不能写满足，最终范围/关闭由用户决定，准备成本最大。 |

题号 **阶段B:7**。B-CAND-2涉及现§7.1单候选边界与用户已签的单候选安排，用户选定前不变更停点、不指定新的C/R轮号，不启动阶段B依赖实现。本节不签一次全套或复核重跑额度；未来复核需新增硬件/VLM查询/SR轮时仍须用户单独签。

#### 8. needs_user汇总（每条整题交用户）

下列事项含设备/链路/主机/额度/系统设置/阶段边界或采样、验收/候选范围变化，均不在supervisor D4/D5/D6代拍闭集内；本轮不借D7定数。未答复时保持阶段B=0与既有STOP/NOT_RUN。

- **阶段B:1** — (n)前提：N-A带双RESUMED申请 / N-B止于阶段A / N-C另给读法；**推荐N-A**，可取得Q2/Q3而保留负结果；只能用户定，因改变阶段B申请的已签前提。
- **阶段B:2** — S5快层压力档：沿S2实际15 Hz / 暂不跑S5 / 另提帧率合同；**推荐15 Hz同引擎同计数**，保证可比性、不藏丢帧；只能用户定，因STOP后的硬件压力条件与阶段放行。
- **阶段B:3** — S5快层相对基准：S1方形n=320原p95及2倍∩100 ms / 暂不认可并跳过S5 / 另提基准；**推荐原方形读数**，保持已测对象与阈值；只能用户定，因需认可STOP读数用于后阶段通过线。
- **阶段B:4** — (i)主机：I-A租云 / I-B 5060 WSL2 / I-C无主机只base；**推荐完整探测选I-A**，已有方案路径覆盖C2的GGUF与AWQ；只能用户定，因设备、GPU·h、费用与新主机依赖，未查到部分可行性。
- **阶段B:5** — (j)3a：J-A跳过 / J-B核本机副本后传板跑 / J-C等用户副本；**推荐J-A**，板上无已证副本、bf16可选且RAM风险未实测；只能用户定，因可选设备运行与传输/模型额度。
- **阶段B:6** — 阶段B执行信封：逐行签§4刷新主案 / 选I-C后收窄再签 / 暂不签；**推荐主机/前提裁定后逐维度签主案并先完成依赖闭集准备**，下载内容收窄、系统栈复用、40 GB累计口径清楚；只能用户定，因首签/额度/磁盘口径，含新增板上pip/源码下载、云目录20 GB/12包/3 GB、Mac中转累计12 GB申请；这些是封顶估算，兼容/清单仍须核，不凭本表启动。
- **阶段B:7** — 候选关系：B-CAND-1并入 / B-CAND-2前一候选处置后另起停点 / B-CAND-3另立项或止于A；**推荐B-CAND-2**，最终代码有独立证据范围；只能用户定，因改变单候选阶段边界，需另签全套及模型/回放/复核重跑额度。
- **阶段B:8** — 租云轨道冲突：等待FRAME-001释放 / 用户指定暂停并切轨道 / 改I-C本地部分探测；**推荐等待释放**，遵守1消耗上限并保留现有交接；只能用户定，因保留/暂停轨道及破例并行授权边界；本轮不暂停、核销或改写任何消耗性交接。

## 待裁定

本节答复 `docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md`「待裁定」IR-1…IR-10（2026-10-02）。本轮登记轮次为 `K1K3K4待裁定`，是实现期合同解释，**不是 C 轮**，不改核对表；自证第 1、2 项仍不成立。以下接受只指读法，不核验实现通过，不签独立复核或 `UNITY_NA` 附议。工程合同解释按 `AC-n 修订 1` 追加，原条款不覆盖；设备变更见决策记录「CLARIFY 表」。

| ID | 裁定与追加解释 | 依据 |
|---|---|---|
| IR-1 | **接受（限 S0）**；**AC-1 修订 1**：无权限读取 dmesg 时，可保留拒绝原文并以同次启动 `journalctl -k -b 0` 的内核日志 NvMap 摘录作该读数来源，记录命令、启动范围与来源限制；不以跨启动 `/var/log/kern.log` 命中数替代本次启动原文。现有原文有启动内核首行与 5 条 NvMap 初始化行，支持本次 S0 的来源替代；不由 1,136 行数或无命中推定日志绝对完整，更不推广到 S5 的 OOM 检查。若后续发现本次启动范围不符、来源遗漏或复核不认可等价性，保留实现角色请求「请用户在板上执行一次 `sudo dmesg \| grep -i nvmap` 并回传原文（只读）」为条件性待用户项，见下节；本轮不代用户授权 sudo。 | §2.1 S0、AC-1；`-env.json` `readings.dmesg_nvmap` 的拒绝原文、本次启动参数、内核首行和 NvMap 摘录。 |
| IR-2 | **接受**；同 **AC-1 修订 1**：成功返回当前模式的非 root `nvpmodel -q` 可替代 `sudo nvpmodel -q`，仍须保留原文，不授权 `-m` 或其他设置。 | AC-1 要求的是当前 MAXN_SUPER；`-env.json` `readings.nvpmodel_q` rc=0，原文 `NV Power Mode: MAXN_SUPER`。 |
| IR-3 | **接受，但不接受“任一 NOT_RUN 均可继续后续步骤”的泛化**；**AC-13 修订 1（关联 AC-2/3/15）**：缺少系统 torch 的 S1/S2 可用既有原因形状 `NOT_RUN(PATH_UNAVAILABLE(system-torch))`，不自造 STOP 码、不自行安装；AC-2/3 不满足。已跑的 SR 回声冒烟不依赖 S1 引擎，且 10-02「用户告知 Jetson 配置完成…」明确允许至多一次，故本次继续冒烟成立；真实 SR (b) 仍须 S1 引擎，阶段 B 仍须单独签发及其前提。 | §2.1 NOT_RUN 闭集含 `PATH_UNAVAILABLE(<路径名>)`；§7.3；账本 09-28 阶段 A、10-02 配置完成条目 (c)；`-fastlayer.json` 与 `-relay.json` 回声模式；`-ledger.json` 冒烟 1/1。 |
| IR-4 | **退回用户选择；本轮不选路径**。§5「复用 NVIDIA torch、不重装 torch」和 §6「本栈」的解释取决于待用户 1 的 A/B/C。A 改变执行栈与主张边界，B 需新安装/下载额度，C 须用户给出装好后的实际栈；选定并逐字入账后再由接受角色追加合同/信封落实，之后才派实现。S0 系统栈与容器元数据分列，不将已有镜像元数据当成容器实跑证明。 | §5、§6、engineering §9；`-env.json` `readings.python_import_tensorrt_torch` / `torch_availability`；待用户 1。 |
| IR-5 | **接受（限离线 S1/S2 固定输入）**；**AC-2 修订 1**：同一 init 框取旧 `P1-ENG-FAST-002-latency.json` 的 `frames.init_box`，作为已归档、固定的初始化框数值经参数传入；来源须如实标为 G-7 的离线用户框替身，不能改称检测器产出。本项不读取/传输真值索引或随帧真值、不用真值重绑、选帧或调参；这个时延基准不能证明自动捕获/身份正确性。SR (b)/AC-5 继续只用首帧检测器自身 `target` 类最高分框，严禁借用该框。 | §0 事实 4、§2.1 S1「同一 init 框」、§2.2/AC-12 真值隔离；旧 FAST-002 §3.4.1/AR2-2 的离线初始化与载体边界、`-latency.json` `frames`；旧项收口读数仅描述性，见 `docs/parked-status.md` 同名节。 |
| IR-6 | **改读，明确分母**；同 **AC-2 修订 1**：init 帧 0，计时 update 帧 1…320（n=320，不剔除预热）；「前 50 帧」检测数检查为 0…49，沿 G-7 `images[:50]`。320 帧最大归一化差的判门窗口为 1…320；帧 0 的检测差可另报，不把 321 帧写成 n=320。接受同类贪心 IoU≥0.5 配对，但两侧未配对检测都须保留于不一致清单，不得仅在成功配对框上声称一致性 PASS；任一未配对使一致性分量不通过。 | §2.1 S1 两分量、§3.1、AC-2；旧 `tools/eng_det/latency.py:measure` 的 init、`images[1:]` 与 `images[:50]`；`-fastlayer.json` `planned_protocol`。 |
| IR-7 | **改读**；**AC-3 修订 1（关联 AC-13）**：正常 DVFS 的当前频率变化不单独记热降频；结合 GPU/CPU 频率上限相对首样本下降、明确对应 CPU/GPU 热限频的 cooling 状态与温度原文判定，不能将任意 cooling device（如风扇）的非零状态一概记为降频。确认热限频用原 `STOP(THERMAL_THROTTLE)`。末/首 5 min p95 比值 >1.2 是预注册时延线未过，使用已有 `STOP(LATENCY_OVER)`，停全部后续；禁止 `UNRESOLVED(P95_RATIO_OVER)` 作为步骤 verdict。不能确认的频率证据不得据此宣称 S2 PASS，交回裁定，不改阈值或锁频。 | §2.1 S2 的三项合取、STOP 闭集与停止总则；§2.3 禁止 `jetson_clocks`；AC-3/13。 |
| IR-8 | **改读，不扣除在途整包丢失**；**AC-4 修订 1、AC-6 修订 1**：正式 forward 完整率分母为该计数窗口发送端实际送出的包数，分子为板端完整发布且 sha 一致的对应包数，≥1,500 帧要求保留；不从分母扣除检测到断链前/期间的在途包。forward 轮按全程零链路事件准备，与有意断链轮分开报告；意外事件仍原样报告，完整率不足继续按 `STOP(RELAY_INTEGRITY)` 处置，不挑选好区间补成 PASS。断链轮另列 frame_id 缺口、不完整包/发布、进程与真实 TrackLoop 语义、恢复时间，不能用缺口抵消损坏包。10 s/60 s 的物理拔线或双通道连同对时的完整软件断链，均可作 AC-6 注入手段（不能仅停回放、暂停应答或杀进程代替断链）；二者实施方案须满足同一判据与既有总轮数/字节/墙钟。手段选择属 D5，交 supervisor 代选，推荐软件定时断链，理由见下节。 | §2.1 SR、§3.2 不补发过期帧、AC-4/6；`-relay.json` `bundles_sent=1425`、`bundles_complete_on_board=1413`，12 包早于检测事件丢失；冒烟仅非结论，不重算其 1,413/1,425。 |
| IR-9 | **退回用户签额度，拒绝豁免模型加载**；同 **AC-13 修订 1（关联 AC-10）**：测试夹具加载真实模型也计入 Mac 模型使用，「零模型」没有测试例外；停点全套义务仍有效，focused 不能替代。用户具名签发一次停点全套的模型额度并入账、落实后才跑，不能借 FRAME-001 额度或把 SUB 请求当批准。 | §5 Mac 生效值、AC-10、engineering §6、workflow §4.3.1 条件 2；交接「停点自证」与待用户 2。 |
| IR-10 | **接受**；同 **AC-1 修订 1**：S0 的 1.2 GB 读作 tegrastats 原文单位 1,200 MB，报告保留原文单位；不用该写法推定其他 RAM/GiB 门的换算。725 MB 为该 5 min 样本最大值，S0 读数过线不代表 AC-1 完整性或后续模型可运行已验收。 | §2.1 S0；`-env.json` `tegrastats_idle.ram_used_mb`、`checks` RAM 行；不改已有阈值数值。 |

**信封内返工归因**：冒烟发现的桌面侧对时旧应答错位属于 SR 中继实现缺陷；交接「冒烟发现与修复」记录一次修复和具名红绿，板侧与消息帧未改，未重跑已耗尽的冒烟轮。认可该修复落在阶段 A 工程性返工范围内，不签其正确性通过、不追加轮数；正式轮累计仍受 §5 与 `-ledger.json` 限制。

**非权威核查提示**：交接「AC-n 逐条证据指针（自证）」的 AC-14 行缺 `artifact:` 前缀，实现角色送停点前须补；本角色未改该证据文件。`UNITY_NA` 附议仍缺，SR (b) 真实应答器尚未实现，S1/S2 与正式 SR、全套均待完成，不以本节裁定视作候选自证或阶段 A 验收。

本节续答同一交接文件「待裁定（补跑）」IR-11…IR-13 及补跑 verdict 读法（2026-10-02）。本轮登记轮次为 `K1K3K4补跑待裁定`，仍是实现期合同解释、不是 C 轮，不改核对表；补跑后自证第 1、2 项仍不成立。以下接受只指读法，不核验实现通过，不签独立复核或 `UNITY_NA` 附议；合同解释按 `AC-n 修订 m` 追加，原条款不覆盖。

| ID | 裁定与追加解释 | 依据 |
|---|---|---|
| IR-11 | **接受**；**AC-10 修订 1（关联 AC-13）**：容器内以同版本 `opencv-python-headless` 4.11.0.86 `--no-deps` 替换 `opencv-python` 属 §5 阶段 A「pip / 源码编译（板上）」维度内操作——`ultralytics` 声明依赖的 GUI 构建在容器内因缺 `libGL.so.1` 无法 import，headless 为同源同版本的无 GUI 构建，本项用到的 `imread`/光流等 API 相同。装后卸载的 `opencv-python` 按实现的保守口径计入 pip 维度（包数 5 ≤ 8、字节 202,869,979 ≤ 300 MB 均含该已卸载包）：§5 表头「签发后成功、失败、重试全部计入同一上限，耗尽即停」，不以卸载为由回退计数。未用 apt/sudo，模型下载仍 0；本轮 S1 未产出读数，此读法不影响任何数字。 | §5 阶段 A pip 行与表头；账本 2026-10-02「用户选 torch 路径 A…」授权范围 (a)；`-ledger.json` `dimensions.board_pip`、`-fastlayer.json` S1 `container_setup.pip`、`-env.json`「s1s2_container_stack」；交接 IR-11。 |
| IR-12 | **接受三项**：(a) 板上 0 字节 `~/eng-jet/code/tools/__init__.py` 读作板上运行件（解除镜像 nvfuser egg 顶层 `tools` 包对仓库命名空间包的遮蔽），仓库候选零改动、不计入候选 diff，计入板上磁盘维度并在证据如实记录；换栈或清理时随 `~/eng-jet/` 一并处置，不升格为仓库合同内容。(b) **AC-12 修订 1**：扫描对 `venv/` 等允许前缀下第三方包自身文件名命中禁键的，单列 `third_party_name_hits`、不记违规；文件内容禁键命中仍记违规——AC-12 的对象是本项工件与真值隔离，第三方轮子自带文件名不属本项工件。(c) **AC-2 修订 3（§3.1 改读）**：S1 逐帧输出键名 `state` 改为 `plugin_state`，§3.1 回放输出行字面相应改读；语义不变，理由是避免与 AC-12 禁键 `"state"`（smoke 真值字段）在扫描与人工核对中混淆；接口字面变化记录于此并经本裁定确认。 | §3.1、AC-12；`-assets.json`「board_manifest」（`third_party_name_hits` 16 条、`ac12_clean: true`）、`-fastlayer.json` S1 `container_setup.board_only_shim`；test: `tests/test_eng_jet_guards.py` 第三方包名单列例；交接 IR-12。 |
| IR-13 | **接受（本轮未运行，不预签读数）**；**AC-2 修订 4（§3.1 改读）**：静态形状引擎只接受导出形状，矩形引擎 `imgsz=(480,640)` 时线束层（`TimedModel.imgsz_override`）把插件每次传入的 `imgsz=640` 改写为 `[480, 640]`，改写逐次记入 `-fastlayer.json`；冻结规格与插件不改，不构成对插件身份或一致性判据的改动。矩形引擎读数按 §2.1 S1「同口径单独报告，不进 verdict」处理。本轮因方形引擎未产出而未运行，本裁定只对读法，不视为矩形引擎已验。 | §2.1 S1、§3.1；`-fastlayer.json` S1 `rect_engine`；test: `tests/test_eng_jet_bench.py` imgsz 改写例；交接 IR-13。 |
| NOT_RUN 读法（补跑） | **接受**。`NOT_RUN(PATH_UNAVAILABLE(container-tensorrt-sm87))` 沿用上表 IR-3 已接受的原因形状（§2.1 NOT_RUN 闭集含 `PATH_UNAVAILABLE(<路径名>)`）：用户选定的容器路径存在，但其 TensorRT 10.13.2.6 不能为本板 SM 87 建引擎，该路径对 S1/S2 要求的操作不可用；这不是「跑了但未过预注册线」，不属 STOP 原因码闭集任何一码，禁止自造 STOP 码（同 IR-3）。未换镜像、未拼接宿主 TensorRT 10.16 的处置**成立**：§2.1「不自行升级、不自行修复环境、不改阈值」与派发「不变通」；拼接宿主 TRT 或换镜像都是环境修复/新栈，须先由用户选定、接受角色落实合同后才可执行。该 verdict 下 AC-2/AC-3 不记满足（§2.1：NOT_RUN 步骤对应 AC 一律不得记为满足）；矩形引擎因同一限制未尝试、记 `NOT_RUN` 同样成立。 | §2.1 verdict 总则与 NOT_RUN 闭集、上表 IR-3 行；`-env.json`「s1s2_container_stack」`tensorrt_sm87`（`supported: false`）、`-fastlayer.json` S1 `export_attempts` 与 `tensorrt_cross_check`、S2 `verdict`；`-report.md` §2a。 |

本节续答同一交接文件「待裁定（补跑B）」IR-14…IR-15（2026-10-02）。本轮登记轮次为 `K1K3K4补跑B待裁定`，仍是实现期合同解释、不是 C 轮，不改核对表；补跑B 后自证第 1、2 项仍不成立（S1/S2 无读数、停点全套额度仍待用户），不送 C1。以下接受只指读法，不核验实现通过，不签独立复核或 `UNITY_NA` 附议；合同解释按 `AC-n 修订 m` 追加，原条款不覆盖。

| ID | 裁定与追加解释 | 依据 |
|---|---|---|
| IR-14 | **接受**；停因沿用 `NOT_RUN(PATH_UNAVAILABLE(system-torch))`，不另记形状、不新增 AC 修订。本行是上表 IR-3（**AC-13 修订 1**）已接受形状的再次适用：系统栈 torch 仍不可用——本轮因 SUB:1 下载额度将超而停在安装前，torch/torchvision 未安装，该路径对 S1/S2 要求的操作不可用；这不是「跑了但未过预注册线」，不属 STOP 原因码闭集任何一码，禁止自造 STOP 码。证据把该 verdict 形状与本轮具体停因（SUB:1 下载额度将超、停在安装前）并列如实记录；该 verdict 下 AC-2/AC-3 不记满足（§2.1：NOT_RUN 步骤对应 AC 一律不得记为满足）。 | §2.1 verdict 总则与 NOT_RUN 闭集、上表 IR-3 行（AC-13 修订 1）；`-env.json`「s1s2_system_stack」`note` 与 `sub1_install`、`-report.md` §2b、`-ledger.json` `dimensions.sub1_torch`；交接 IR-14。 |
| IR-15 | **接受**；**AC-10 修订 2（关联 AC-2/13）**：系统 venv 中 ultralytics、lap、ultralytics-thop、opencv-python-headless 4.11.0.86 从板上 `~/eng-jet/wheels` 已有轮子以 `--no-deps` 同版本重装，按「S1/S2 系统栈落实（B）」归因行不新增计数（新增下载 0、包数不新增）；只新增导出必需的 `onnx==1.18.0`（与容器轮同版，避开 1.19+ 的 `ml_dtypes`）及其依赖 `protobuf` 两包，计入 §5 阶段 A 既有 pip 维度（5 + 2 = 7 ≤ 8 包；202,869,979 + ≈16 MB ≈ 219 MB ≤ 300 MB）；不装 psutil / polars / nvidia-ml-py——实现角色对 ultralytics 8.4.104 轮子的只读源码核查称三者均为函数内惰性导入、S1/S2 路径不触达，该读法成立但须复核轮核对。板上一切 ultralytics 运行一律设 `YOLO_AUTOINSTALL=false YOLO_OFFLINE=true`（JetPack 7 上 `check_tensorrt("10.15")` 在关自动安装后只返回 False，继续用系统 TensorRT 10.16，不试装 `tensorrt-cu13`）。装后实测若该读法不成立（顶层导入缺包、导出路径触达未装包），停下回报接受角色，不自行加包、不自行扩额。 | §5 阶段 A pip 行与表头；决策记录「S1/S2 系统栈落实（B）」既有依赖重装计数归因行；`-ledger.json` `dimensions.board_pip`、`-env.json`「s1s2_system_stack」`system_packages_visible` 与 ultralytics 轮子源码只读核查；交接 IR-15。 |

本节续答同一交接文件「待裁定（补跑C）」IR-16（2026-10-02）。本轮登记轮次为 `K1K3K4补跑C待裁定`，仍是实现期合同解释、不是 C 轮，不改核对表；补跑C 后自证第 1、2 项仍不成立（S1/S2 无读数、停点全套额度仍待用户），不送 C1。以下接受只指读法，不核验实现通过，不签独立复核或 `UNITY_NA` 附议；合同解释按 `AC-n 修订 m` 追加，原条款不覆盖。

| ID | 裁定与追加解释 | 依据 |
|---|---|---|
| IR-16 (a) | **接受沿用既有形状**。补跑C 停在 S1 前的记法沿用 IR-3/IR-14 已接受的 `NOT_RUN(PATH_UNAVAILABLE(system-torch))`，不另造 `system-torch-sm87` 等新形状：当时合同字面（题 4 装后验证第一项）未过，系统 torch 路径在该合同下对 S1/S2 不可用；不属 STOP 原因码闭集，禁止自造 STOP 码。该 NOT_RUN 是补跑C 当时状态的历史记录，不改写；用户题 6 选 A 与 AC-2 修订 6 生效后该不可用状态解除，S1/S2 实跑后以实跑读数为准。补跑C 下 AC-2/AC-3 不记满足（§2.1：NOT_RUN 步骤对应 AC 一律不得记为满足）。 | §2.1 verdict 总则与 NOT_RUN 闭集、上表 IR-3/IR-14 行；`docs/evidence/P1-ENG-JET-001-env.json`「s1s2_system_stack_c」`verify`、`-report.md` §2c；交接 IR-16 (a)。 |
| IR-16 (b) | **接受并已落实**。题 4 装后验证第一项的替代判据按用户题 6 选 A 写为 **AC-2 修订 6**，全文见决策记录「题 6 选 A 落实：装后验证第一项替代判据（AC-2 修订 6）」：arch list 含同主版本（8.x）、算力 ≤ 8.7 的 `sm_8x` SASS（本板实测为 sm_80），且装后 matmul/TRT 共存三项与 cuDNN 卷积、CUDA nms、归约诊断全过；本次实测逐项满足（逐项指针见该节），S1/S2 按修订后判据可续跑；读数注明 torch 无 sm_87 原生 SASS、按二进制兼容运行；出现 `no kernel image` 等不兼容报错即停回用户，不换源、不变通。其余 AC、阈值、信封维度不变；零新增下载，不签 SUB:4。 | `docs/authorizations.md` 2026-10-02「P1-ENG-JET-001 — 用户选题 6 A：官方 torch 无 sm_87 时接受同主版本二进制兼容读法继续 S1/S2」授权范围；决策记录同名单节；`docs/evidence/P1-ENG-JET-001-env.json`「s1s2_system_stack_c」；交接 IR-16 (b)。 |
| IR-16 (c) | **接受实现读法**。`~/eng-jet` 之外两处运行时缓存（`~/.config/Ultralytics/settings.json` 482 B、`~/.nv/ComputeCache` 545 文件 26,215,934 B）不含本项数据或真值，非 AC-12 板上清单对象（清单对象为 `~/eng-jet`），读作如实记录、不记违规、**保留不删**（已在 `-env.json`「s1s2_system_stack_c」`outside_eng_jet_writes` 记录）。下一派发起以环境变量 `YOLO_CONFIG_DIR`、`CUDA_CACHE_PATH` 把二者指到 `~/eng-jet/home/` 下并在证据如实记录；既有两处文件仍不删（删除属板上系统环境处置，未授权、也不需要）。 | AC-12 及其修订 1（对象与单列先例）；`docs/evidence/P1-ENG-JET-001-env.json`「s1s2_system_stack_c」`outside_eng_jet_writes`；交接 IR-16 (c)。 |
| IR-16 (d) | **允许装后清理已装依赖轮子，并明口径**。允许实现角色在下一派发内、S1 引擎导出前删除 `~/eng-jet/wheels/sub1/` 下全部已安装轮子的文件（21 个依赖轮子 + 官方 cu130 torch/torchvision 两枚，合计 2,836,341,094 B），以腾出 SUB:1 新增磁盘余量（现计 7,542,632,760 B / ≤ 8 GB；S1 两版引擎导出与 S2 还会产生占用）；**清理只删轮子文件，不得改动已安装的 sysvenv**（不 `pip uninstall`、不动 site-packages）；删除清单与字节、删除前后 `du` 实测记入证据与 ledger。计账口径：SUB:1「安装后新增磁盘」按删除后 `du -sb ~/eng-jet` 相对同一基线实测重计——磁盘是占用维度，删除即释放，沿「S1/S2 系统栈落实（B）」容器 venv「计入直至实际删除」先例；下载字节与包数维度**不回退**（§5 表头：签发后成功、失败、重试全部计入同一上限）；删除后任何原因需重装同一版本的，重新下载字节照计 SUB:1 下载上限（现行 ≤ 6.5 GB），耗尽即停回用户。容器 venv 与 `~/eng-jet/wheels` 既有轮子的处置不变，仍按「S1/S2 系统栈落实（B）」既定条件执行。 | §5 表头与题 4「安装后新增磁盘 ≤ 8 GB」；决策记录「S1/S2 系统栈落实（B）」容器 venv/wheels 处置行；`docs/evidence/P1-ENG-JET-001-ledger.json` `dimensions.sub1_torch`（`new_disk_bytes` 7,542,632,760）与 `-env.json`「s1s2_system_stack_c」`disk.du_after`；交接 IR-16 (d)。 |

本节续答同一交接文件「待裁定（补跑D；实现读法，交接受角色）」IR-17…19（2026-10-03）。登记轮次 `K1K3K4补跑D待裁定`；工程轨道按 `AC-n 修订 m` 追加解释、按新 AC 追加新增义务，原文不覆盖，不作候选通过结论。

| ID | 裁定与追加解释 | 依据 |
|---|---|---|
| IR-17 | **接受，限具名驱动缓存路径的文件名读法；AC-12 修订 2**：`home/cuda-cache/index` 是 IR-16 (c) 重定向后 CUDA 驱动 JIT 缓存自生的二进制索引，按 IR-12 (b) 的非本项工件文件名先例单列、不记真值隔离违规。例外只覆盖此缓存路径的文件名，不覆盖数据集/真值索引、不泛化为整个 `home/` 豁免；内容禁键命中仍记违规。`-assets.json` 原扫描 `violations` 与 `ac12_clean: false` 保留，不能直接改写为 true 或据本裁定宣称 AC-12 已验收；下一证据更新将具名驱动缓存文件名命中与真正违规分列并引用本裁定，保留原扫描指针。不改 `CUDA_CACHE_PATH` 子目录名来绕过扫描、不删缓存。 | AC-12、AC-12 修订 1 / IR-12 (b)、IR-16 (c)；`docs/evidence/P1-ENG-JET-001-assets.json`「board_manifest」（原扫描唯一 forbidden_path、内容禁键命中 0）、交接 IR-17；`-env.json`「s1s2_system_stack_d.env」「outside_eng_jet」。 |
| IR-18 | **接受当前记法，保留不删**：`~/.cache/matplotlib/fontlist-v330.json` 为导出进程生成的字体缓存，无本项数据或真值；`~/.local/state/wireplumber/restore-stream` 按实现来源记录为 ssh 登录用户会话服务写入，非本项进程。二者在 `~/eng-jet` 外，沿 IR-16 (c) 如实记录、不记本项 AC-12 清单违规，不因此豁免受保护根零写入。**下一派发加 MPLCONFIGDIR：新增 AC-16**（来源仅为实现 IR-18），把本项 Python 进程字体缓存指到 `~/eng-jet/home/mpl` 并记录实际环境与外部新写入；此为追加的目录约束，不伪装成已被 IR-16 (c) 点名的既有变量义务。原两处 Ultralytics/ComputeCache 文件本轮未变、继续保留；不授权清理外部缓存/会话服务文件，不改系统设置，不新增安装/下载额度。 | AC-12、IR-16 (c)；`docs/evidence/P1-ENG-JET-001-env.json`「s1s2_system_stack_d.outside_eng_jet」（baseline/after/newer_than_marker）、交接 IR-18；新 AC-16 见 §4。 |
| IR-19 | **接受条件尚未全满足的读法**：决策记录「S1/S2 系统栈落实（B）」的「系统栈 S1/S2 有读数后」指 S1 与 S2 均已实跑并有读数，不要求两步都 PASS，也不改读成仅 S1 有读数即可删除。本轮 S2 未运行，容器 `~/eng-jet/venv` 继续保留、继续计入板上磁盘；只有用户选 (α) 后 S2 实跑有读数，才按原条件在该实现派发内删除容器 venv，证据/ledger 如实记删除与前后占用，pip 包数/下载字节不回退，不动系统 sysvenv。`~/eng-jet/wheels` 既有轮子仍保留，本轮不授权删除；届时处置仍按原记录交接受角色补一行。若用户选 (β)，本裁定不触发板上清理。 | 决策记录「S1/S2 系统栈落实（B）」容器 venv/wheels 处置、IR-16 (d)、AC-10；`docs/evidence/P1-ENG-JET-001-env.json`「s1s2_system_stack_d.container_venv_delete」、`-ledger.json`「dimensions.board_disk」；交接 IR-19。 |

本节续答同一交接文件「待裁定（补跑E；实现读法，交接受角色）」IR-20（2026-10-03）。登记轮次 `K1K3K4补跑E待裁定`；仅追加 CLARIFY，不新增义务、不放宽其他 AC、阈值或信封。

| ID | 裁定与追加解释 | 依据 |
|---|---|---|
| IR-20 | **接受本次未据告警停跑的读法；AC-2 修订 7（解释修订 6「不兼容报错」，关联 AC-3/13）**：本次 TRT 引擎计划跨设备 `[W]` 告警，结合使用前同板同引擎身份复核、系统栈实跑、全程推理完成且无已记录 CUDA/TRT 不兼容错误，不等同于题 6 选 A 的 `no kernel image` 或其他 CUDA 不兼容报错；不单凭 `[W]` 等级泛化为告警一律可忽略。S2 保留带该告警的描述性读数及 `STOP(FRAME_DROP)`，不作废、不改 PASS、不新增 STOP 码。告警原因及对性能/丢帧的影响未核实，不能把两轮间重启当已证明成因，也不能声称引擎已证跨设备可移植或告警无影响。下一派发前将本裁定与原告警、上述限制列入交接；用户若选 (α′)，运行前沿 AC-11 复核既有方形引擎身份及实跑栈，沿 AC-13 保留告警标注与读数限制。无须为此重跑 S1/S2、重导出或换引擎；本裁定不授权这些动作。任一后续环节出现实际 CUDA/TRT 不兼容错误、无法反序列化/推理或身份不符，仍立即停止该路径回用户，不换源、不变通。S2 STOP 的继续取舍另由用户裁定。 | 题 6 选 A / AC-2 修订 6；AC-3/11/13；`docs/evidence/P1-ENG-JET-001-fastlayer.json`「S2.trt_log_warnings」「S2.engine_identity_check」「S2.no_kernel_image」「S2.runs.15hz.runtime_stack」；`-env.json`「s2_system_stack_e.trt_plan_device_warning」；交接 IR-20。 |

本节续答「待裁定（补跑F；实现读法，交接受角色）」IR-21/22（2026-10-03）。登记轮次 `K1K3K4补跑F待裁定`；只追加既有 AC-12 的 CLARIFY，原文与修订 1/2 不覆盖，不新增义务。

| ID | 裁定与追加解释 | 依据 |
|---|---|---|
| IR-21 | **接受；AC-12 修订 3（关联 AC-5/13）**：SR 真实 TrackLoop 的逐帧 `track-records.jsonl` 经注入的 `track_responder.RecordSink` 将 `state` 改名 `loop_state`，仅此键改名、其他键值原样，语义不变；同 IR-12 (c) 的 plugin_state 先例，避免把跟踪状态与 smoke 真值 state 混淆。无需改用 RunLogger 原样落盘，不改 controller、控制/帧协议或目标身份/重播种；不豁免其他文件的 state 或真值字段。 | AC-12、IR-12 (c) / AC-2 修订 3；交接 IR-21；`tools/eng_jet/track_responder.py:RecordSink.append`、`-relay.json.return.track.loop_states`。 |
| IR-22 | **接受具名内容命中单列读法；AC-12 修订 4（解释修订 2，关联 AC-5/13）**：只覆盖 `-assets.json.board_manifest.ac12_split.true_violations` 枚举的本轮板上两份 `gimbal_command.json` 的 `command.target_world_m`（具名路径运行时从该清单解析；字段为冻结 look_at_world 协议的有限 x/y/z）。来源是本轮真实 TrackLoop 根据检测框、帧位姿和显式地平面调用 `box_ground_intersection`→`BridgePublisher.look_at`→`gimbal_entry.look_at` 生成的 look-at 点，属于控制输出、非 smoke target_* 真值，不改冻结协议字段、不删除文件、不改名绕扫描。下一实现证据更新须将这两条具名协议内容命中与真正隔离违规分列，保留原 violations、true_violation_count=2 和 ac12_clean=false 的扫描及指针；本轮不把 ac12_clean 改为 true、不宣称 AC-12 已验收。修订 1/2 的其他内容禁键仍按违规处理，不泛化为 runtime/**、gimbal 文件全内容或全部 target_* 豁免；来源/路径/字段不符、真值或来源未明命中仍违规。隔离红线与受保护根零写入不变，独立复核仍须核实来源。 | AC-12 及修订 1/2 / IR-17；交接 IR-22、`-assets.json.board_manifest.ac12_split`；`controller/track_loop.py:_publish_latest`、`controller/gimbal_entry.py:look_at`；下一实现沿既有 AC-12/13 证据一致性更新，不是新增 AC。 |

本节续答交接「待裁定（K1K3K4全套）」IR-23（2026-10-03）；登记轮次 `K1K3K4全套待裁定`，只解释既有合同，不签任何额度。

| ID | 裁定与追加解释 | 依据 |
|---|---|---|
| IR-23 | **认可预计两次未列名加载及两次部分回放的停因，纠正 CPU 推理读法；AC-10 修订 4（解释修订 3，关联 AC-13 修订 1）**：SUB:2 是 NanoTrack/YOLOE/DINOv2/CSRT 四种模型的分列上限，det-assoc 冻结检测器不属于 YOLOE，额度仍为 0，不转用余量、不豁免测试加载。ResidentCarrierReplay 虽零模型，仍是 ACQ-001 来源的两次部分回放；暂停信封不得消费，改记本项是用户授权事项。本机 CPU 不含 MPS；当前真实 Carrier 两例默认选 MPS，不能以加载文件在 CPU 上反序列化推定随后 CPU 推理。按当前环境与合同指定的数据根解释器，未找到既不新增额度/改归属、又不改 skip/环境变量绕门的完整全套跑法。B 更换解释器并使需 lap 用例自然 skip，改变现行执行/覆盖口径，须用户明确选择后才追加落实，不能由接受角色本轮自行放行。A 新额度同样仅用户可签；单签其 CPU 加载/回放请求不豁免当前 MPS 冲突。全套继续 0 次，不送 C1，不新增 AC，不改任何上限；条件命令与计账见下一用户交接。 | §5、IR-9、AC-10 修订 3、SUB:2 账本授权范围 (1)、SUB:2 落实执行范围 2、§7.1；交接 IR-23、tests/test_det_assoc_carrier.py、controller/trackers.py:create_tracker、controller/det_assoc_tracker.py:_resolve_device/_default_model_loader；ACQ-001 暂停节；「K1K3K4全套记录核对」。 |

本节续答 IR-23（登记轮次 `K1K3K4落实SUB5`）：用户已签 SUB:5 A，**AC-10 修订 5（CLARIFY）** 全文与 ledger 计账口径见决策记录「SUB:5 A 落实与 CPU 执行方案核对」。修订 4 中 det-assoc 零额度/不得改归属的签前约束仅在本次具名额度与回放上由修订 5 替代，原文保留；CPU/MPS 边界未被替代。只读核对当前无授权内 CPU 跑法，仍不放行全套；用户执行方案选项见本提案末节。本答复落实用户已签范围，不新增 AC，不签独立复核。

本节续答 IR-23（登记轮次 `K1K3K4落实CPU1`）：用户已选 CPU-1，**AC-10 修订 6（CLARIFY）** 的测试变更范围、controller/config 空 diff 关系、风险、一次全套条件命令与计账见决策记录「CPU-1 落实与下一实现范围」。修订 5 的设备/方法禁令仅对用户具名授权的两处构造与必要导入替换作例外，原文保留；MPS、探测、skip、环境变量与额度边界不变。当前交 Implementation 改测试并完成跑前核查，不再请求用户重选 CPU 方案，不预签自证成立。

本节续答交接「待裁定（K1K3K4全套CPU1）」IR-24/25（登记轮次 `K1K3K4全套CPU1待裁定`，2026-10-03）；只追加 CLARIFY，不改原合同判据，不新增义务。

| ID | 裁定与追加解释 | 依据 |
|---|---|---|
| IR-24 | **须用户裁定，接受角色不自行以“已知设备差异”放行；AC-10 修订 7（解释修订 6）**。真实比较失败保留，首个差异支持设备差异假设，不能证明其余 9 个只差浮点。自证第 1 项暂不成立、第 2 项不成立。用户曾认可失败风险，未授权失败后自动继续 C1/R1；若选 A，须明确许可携带该例失败及未知/未执行断言进入 C1/R1，作为本次停点测试条件的具名例外，不把失败改 PASS、不放宽断言/AC。仅记录失败不足以恢复自证；选 B 则先冻结新口径与单独签足设备/加载/全套额度。本轮不放行第二次全套。 | CPU-1 授权范围及 AC-10 修订 6；workflow §4.3.1 条件 1/2；日志 Carrier FAIL、CarrierSelfTest:141–147；本轮记录核对。 |
| IR-25 | **接受具名环境原因分列；AC-13 修订 2（解释修订 1，关联 AC-10/14）**。29 条同时保留“相对 R7 新增”与“本机缺权重环境失败，静态归因”两列，不能改为 R7 原有或已经通过。读码显示第 1 步权重绑定在替身推理前拒绝，相关代码零 diff，允许携带覆盖限制供核对/复核判断；缺资产不要求本项自行补主树 runtime。此分列本身不改变范围/接口，不阻断第 1 项冻结；第 2 项就该组可按环境限制评估，仍无该组通过证据，且不解除 Carrier 的阻断。若用户要求本机通过，资产写入及第二次全套均须另签。 | engineering §6、AC-12/13；tests/test_scene006_probe.py 五类调用、run_probe:987–1001、verify_weight_binding、reanchor.verify_file；R7 两份全套记录与本轮原日志。 |

本节续答 IR-24/25（登记轮次 `K1K3K4落实1A`）：用户 10-03 已逐字入账「1A，2环境分列」，依该条授权范围追加 AC-10 修订 8、AC-13 修订 3，全文与下一实现零消耗范围见决策记录「1A落实与证据整理」。前表保留裁定前读法；IR-24 等待用户条件现已获具名例外落实，IR-25 环境分列已获用户确认，测试仍失败、后续行为仍未验证，不预签自证成立或 C/R 结论。

本节续答交接「K1K3K4R1注记修补：…」§6 的 IR-26/27（登记轮次 `K1K3K4落实SUB6`，2026-10-04）；以下为既有条款追加解释，不新增 AC，不认定补丁已独立复核或新候选实测通过。

| ID | 裁定与追加解释 | 依据与理由 |
|---|---|---|
| IR-26 | **接受全部 a7 3,168 帧的纯参照读法；AC-11 修订 1（CLARIFY，解释 AC-11，关联 AC-12）**：保留派生 `docs/evidence/P1-ENG-JET-001-a7-frame-sha256.jsonl.gz`，每行仅 `frame_id/sha256`，含未用于本项的 1,500…3,167 帧；这是同一 a7 前缀的哈希参照闭集，不新增回放、评估、上板帧或资产使用额度。允许 `verify_frames` 今后新增参照键/来源注明；原含标签来源与历史 `-assets.json` 不改写，历史参照仅投影 sha、不上板、不进插件/控制器的事实继续披露。 | R1-3 与提案「R1消费」具名范围；交接 §1/§6；`tools/eng_jet/assets.py:project_frame_sha/derive_pure_reference/load_pure_reference/frame_reference/verify_frames` 只读核对。完整前缀投影保持来源可逐项对照，每行两键、拒绝额外键/冲突及 sha 形状错误有已记录 focused 覆盖；保留更多哈希不等于使用更多帧，不扩大 AC-11/12 语义。 |
| IR-27 | **接受证据不足时不判通过的读法；AC-4 修订 3（CLARIFY，解释修订 2）及 AC-6 修订 2（CLARIFY，解释修订 1，关联 AC-10/13）**：`_link_event_split` 对列表短于声明总数，或无总数且长度达到旧截断长度 50 的可能截断情形，将 `in_transfer_event_count` 记 `None`（未知，不是 0），同时披露 raw_count/declared_total/truncated，不由局部列表推定全程无事件；`disconnect_pass` 缺 `disconnects` 键判假，不能记断链通过。只对补丁后新生成证据生效，历史读数/判定不改写；不启动 SR 或重算历史实测。 | R1-2/R1-4 与「R1消费」范围；交接 §1/§6；`tools/eng_jet/evidence.py:_link_event_split/disconnect_pass` 只读核对。完整性未知不能推出精确计数，缺断链列表不能证明恰两次断链；完整输入的原通过线保留。此裁定不声称任意畸形/缺其他键都能返回假，既有其他失败路径仍由新候选核对/复核核实。 |

### needs_user（原请求与接受推荐）

以下 1–3 原样转录交接「待用户」；推荐不授权执行。整题 1 涉及合同/执行栈/信封，整题 2 涉及信封，题 3 涉及链路设备前提，IR-1 的条件请求涉及用户特权操作，均交用户，不交 D5。

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


接受角色推荐与理由（2026-10-02）：

- **1 / IR-4：推荐 A，但待用户决定**。复用已有 NGC 容器避免 torch 新下载；模型下载仍为 0。接受该选项必须显式同意容器栈，§6 主张只能对应实跑版本；容器新增 pip 及其导出依赖也必须累计在原 ≤8 包/300 MB 内，不推定只装两包就足够；挂载与新增磁盘须满足原 ≤5 GB、隔离要求。B 的来源/数量未填、C 的实际安装结果未知，均不得先派执行。`P1-ENG-JET-001:b0a5f79c:SUB:1` 仅是待请求标识，SUB 未启用，未批。
- **2 / IR-9：推荐在 S1/S2 补跑后的真正停点签具名一次全套额度**，按原请求 NanoTrack≤4、YOLOE≤2、DINOv2≤2、CSRT≤2、本机 CPU 一次全套；需用户批准并保留 Mac 零 pip，理由是满足停点全套义务且只动用一次相称额度。`P1-ENG-JET-001:b0a5f79c:SUB:2` 未批，不借其他工作项信封；本轮不签发。
- **3 / §7 (h)：推荐用户接好 Mac mini↔Jetson 网线、设固定 IP 并确认可达后告知**，理由是正式 SR 只在已定的有线链路成立；维持剩余最多 4 轮（最终按最新 ledger 解析），冒烟已 1/1 不再跑，不把链路答复当作已接好。
- **IR-1（条件项，原请求）**：「若不等价：请用户在板上执行一次 `sudo dmesg | grep -i nvmap` 并回传原文（只读）。」推荐当前接受 journalctl 替代、不追加 sudo；仅在上述来源条件不成立或复核不认可时由用户决定是否只读补录，理由是保留原读数要求且不修改日志权限/内核参数。本轮未触发、未执行该请求。
- **D5 / IR-8（交 supervisor）**：选项 = 物理拔线 / 双通道及对时同时软件断链；推荐软件定时 10 s、60 s，理由是重复性好且便于记录断链起止。两案均维持合同/AC、信封、帧集/采样及 Lifecycle，不触发 D3；上述同一判据是固定条件，不随代选放宽。supervisor 仅可代选手段并入账，不可替用户接线就绪、追加轮数或改变完整率分母；本轮未代选。

下一步仅见状态板交接行；用户选择 torch 路径后先入账并交接受角色落实，再由 supervisor 在 mini 派实现补跑 S1/S2、补 SR (b) 与链路就绪后的正式 SR；全套须等用户额度，重新自证成立后才交 C1。阶段 B、(i)–(m) 的缺省不做与既有停点继续有效。

（2026-10-02 更新：题 1 用户已选 A 并逐字入账，合同落实见决策记录「S1/S2 容器栈落实」；题 2（停点全套 Mac 模型额度）与题 3（§7 (h) 有线就绪）用户尚未答复，原样保留、不代为裁定。）

（2026-10-02 补跑更新：题 1 重开——用户所选路径 A 实测不可行：容器 `pytorch:25.08-py3` 的 TensorRT 10.13.2.6 不支持 Orin SM 87（容器 `trtexec --fp16` 复证同错，`-env.json`「s1s2_container_stack」`tensorrt_sm87`），S1/S2 记 `NOT_RUN(PATH_UNAVAILABLE(container-tensorrt-sm87))`。实现角色提出的执行栈新选项原样转录为下题 1′；题 2、3 原样保留。任何选项都触及信封/额度或设备操作，属用户决定，不交 supervisor 代拍，接受角色不替选、不按推荐先执行。）

1′. **S1/S2 执行栈重选**（原题 1 路径 A 实测不可行）：
   - **B（接受角色推荐）**：在板上系统 Python 安装与 JP7.2 / CUDA 13.2 匹配的 NVIDIA torch（及 torchvision）轮子，使用 S0 已核验的系统 TensorRT 10.16（`request_id` `P1-ENG-JET-001:b0a5f79c:SUB:1`，维度 = 板上 torch/torchvision 轮子下载与安装，数量待选定来源后填，可能超出现 pip ≤ 300 MB）。推荐理由：回到合同原始执行栈，§6「本栈」主张无需再改述；系统 TensorRT 是 JetPack 随附件、S0 已实测存在。触及信封：板上 pip/下载属新增额度——包数 +2（与 ultralytics/lap 等合并重算后须在 ≤ 8 内），torch aarch64 轮子字节预计超现 ≤ 300 MB，**须用户逐字签发扩额后生效**（SUB:1 仅选 B 时生效，当前未批）；选 B 后由接受角色追加 CLARIFY——S1/S2 回到系统栈执行，已入账的容器栈 CLARIFY 与容器 NOT_RUN 记录保留为历史、不改写，§5 pip 行字面相应落实；模型下载 0、阶段 B 全部维度 0、阈值与判据不变。
   - A2：改用面向 Jetson/iGPU 的容器镜像（需新镜像下载额度，具体 tag 与是否支持 JP7.2 须先核实）。触及信封：新镜像下载属新增额度（镜像 GB 级），**须用户逐字签发**；已入账的容器栈 CLARIFY 需改镜像 tag 后由接受角色重新落实；§6「本栈」沿用「容器实跑栈」改述即可，无需再改；容器内新增 pip 仍受 ≤ 8 包/300 MB。
   - C：用户自行在板上装好可用的 torch + TensorRT 栈后告知（实际栈以实跑为准）。触及信封：代理侧零新增下载额度；装好后的实际栈由接受角色按实跑记录落实合同（系统栈则 §6 无需再改；另一容器或其他栈则按 A2 同路径落实 CLARIFY）；用户操作本身不耗信封。
   任一选项都需用户逐字入账并由接受角色落实合同后，再由 supervisor 在 Mac mini 派实现；本轮不自行选择。
2. **停点全套的 Mac 模型额度**（`P1-ENG-JET-001:b0a5f79c:SUB:2`）：原样保留、不变，仍推荐在 S1/S2 有读数后的真正停点签发。
3. （既有，原样保留）§7 (h) 有线直连与固定 IP 接好后告知，正式 SR 在阶段 A 剩余轮内执行（轮数最终按最新 `-ledger.json` 解析）。

（2026-10-02 CLARIFY-B 更新：题 1′ 用户已选 **B** 并逐字入账（账本同日「P1-ENG-JET-001 — 用户选执行栈 B 的前置：经 Mac mini ssh 在板上 sudo 安装 python3-pip/python3-venv…」授权范围 (a)），合同落实见决策记录「S1/S2 系统栈落实（B）」与「CLARIFY 表」系统栈行；同日容器栈落实的执行栈部分随之失效、原文保留。torch/torchvision 轮子下载与安装额度（SUB:1）尚未签发，申请值与来源建议为下题 4；题 2、3 原样保留、不代为裁定。）

4. **torch/torchvision 轮子下载与安装额度（2026-10-02 CLARIFY-B2 重算：PyTorch 官方 cu130 源）**（`request_id` `P1-ENG-JET-001:b0a5f79c:SUB:1`；SUB 子额度块未签，按执行信封追加由用户直接逐字签发；用户 2026-10-02「走B，用官方源」选定来源（账本同日「P1-ENG-JET-001 — 用户确认走 B 并选 PyTorch 官方 cu130 源作 torch 来源…」授权范围 (b)(c)），原 jetson-ai-lab 主来源版申请值已被替代、原文保留于本题末。本轮数值来自本角色 2026-10-02 第二轮只读网络元数据查询——索引页 HTML、PyPI JSON API `size` 字段与纯 HEAD `content-length`，**本轮未取回任何轮子体**）。
   - **措辞更正（落实 supervisor 核查观察）**：本题上一版写「未下载任何轮子」不准确——上一轮查询时 jetson-ai-lab devpi 服务器忽略 Range 头，torch 2.9.1 与 2.11.0 两个轮子体（约 232 / 297 MB）曾在 Mac mini 上被完整流式取至 /dev/null（未落盘、未安装，当轮报告已披露传输量）。
   - **来源与 pin**：`https://download.pytorch.org/whl/cu130`。pin `torch==2.9.1` + `torchvision==0.24.1`；对应轮子 `torch-2.9.1+cu130-cp312-cp312-manylinux_2_28_aarch64.whl`（HEAD content-length = 512,448,274 B，索引页附 sha256 `6e7f84cb…fe04051f`）与 `torchvision-0.24.1-cp312-cp312-manylinux_2_28_aarch64.whl`（7,823,607 B，索引页附 sha256 `89743dce…97586fec`）。选版理由：(a) 同型板（Orin Nano Super / JP7.2 R39.2 / Python 3.12.3）第三方实测可用报告（libreyolo）对应的正是该索引的 torch 2.9.1+cu130 aarch64 轮子；(b) pytorch/pytorch#174358 记录 torch 2.9.1+cu130 在 aarch64 Ubuntu 24.04 / Python 3.12.3（与板上解释器同版）的真实安装与完整 pip 依赖清单，其打印的算力支持范围 (8.0)–(12.0) 覆盖 Orin SM 87（8.7）；(c) Thor 社区报告 2.10.0+cu130 aarch64 的 cuBLAS matmul 有上游缺陷（sm_110 实测），2.9.1 避开该版本；(d) 与上一轮 jetson-ai-lab 版 pin 同版，S1/S2 读数跨来源可比。
   - **pip 传递依赖（torch/torchvision 自官方 cu130 索引解析；以下全部依赖实际从 PyPI 解析，aarch64（cp312）或 py3-none-any 轮子字节逐项经 PyPI JSON `size` 字段核实）**：nvidia-cublas 13.0.0.19（539,001,158 B）、nvidia-cudnn-cu13 9.13.0.50（412,337,597 B）、nvidia-cusparselt-cu13 0.8.0（220,791,277 B）、nvidia-cufft 12.0.0.15（214,053,580 B）、nvidia-nccl-cu13 2.27.7（194,014,855 B）、nvidia-cusolver 12.0.3.29（193,104,180 B）、triton 3.5.1（159,940,689 B）、nvidia-cusparse 12.6.2.49（155,888,587 B）、nvidia-curand 10.4.0.35（61,962,106 B）、nvidia-cuda-nvrtc 13.0.48（43,013,627 B）、nvidia-nvjitlink 13.0.39（38,767,126 B）、numpy 2.3.5（14,250,702 B）、nvidia-cuda-cupti 13.0.48（10,171,189 B）、sympy 1.14.0（6,299,353 B）、pillow 12.3.0（6,266,838 B）、nvidia-cuda-runtime 13.0.48（2,260,687 B）、networkx 3.7（2,142,205 B）、setuptools 84.0.0（818,216 B）、mpmath 1.4.1（567,787 B）、fsspec 2026.9.0（221,738 B）、nvidia-nvtx 13.0.39（148,037 B）、jinja2 3.1.6（134,899 B）、filelock 4.0.9（110,368 B）、typing-extensions 4.16.0（45,571 B）、markupsafe 3.0.3（24,332 B）——以上 25 项依赖清单与 #174358 的 aarch64 实装记录一致；或然依赖（torch 轮子声明依平台/版本而定、pip 实际解析时才计入）：nvidia-nvshmem-cu13 3.3.20（55,864,769 B）、nvidia-cudss-cu13 0.8.0.10（80,481,232 B）、nvidia-cufile 1.15.0.42（1,136,527 B）。
   - **申请值（签发后成功、失败、重试全部计入同一上限，耗尽即停）**：
     - **包数 ≤ 32**：torch、torchvision + 上述 25 项确定依赖 + 3 项或然依赖 + 2 包解析余量；
     - **下载字节 ≤ 3.5 GB**：确定依赖与或然依赖合计 2,934,281,215 B（≈ 2.93 GB，逐项见上）；余量依据 = 一次工程性重试的最坏情形，取两者之大——(i) pip 不支持断点续传，中断/校验失败后整轮重取最大单轮 nvidia-cublas（539,001,158 B）；(ii) 同维度内更换 torch 小版本至 2.11.0+cu130（轮子 420,247,044 B）+ torchvision 0.26.0+cu130（轮子 7,768,006 B）（HEAD 实测）；(i) 较大，加索引/元数据开销后上限取 3.5 GB；
     - **安装后新增磁盘 ≤ 8 GB**（轮子以 .so 为主、解压约 2–2.5 倍，安装稳态估 6–7 GB；若保留 pip 缓存，安装期间峰值另 +约 2.9 GB，建议实现以 `--no-cache-dir` 或装后清缓存控制峰值）。计入板上磁盘维度：阶段 A「板上磁盘」生效值相应申请由 ≤ 5 GB（`~/eng-jet/`）调整为 **≤ 13 GB**（既有 5 GB + 本项新增 8 GB；板上 `df` 实测可用 170.9 GB，见 `docs/evidence/P1-ENG-JET-001-env.json` disk 读数，物理余量充足，调整属合同口径）。
   - **SM 87 可用性：已知证据与安装后先验证**：已知证据均为第三方/间接——同型板正面报告（libreyolo，官方 cu130 索引轮子）与 #174358 的算力范围 (8.0)–(12.0)（覆盖 8.7）；PyTorch 官方未逐轮子声明 aarch64 构建含 sm_87 内核，`no kernel image` 风险仍存在。安装后、跑 S1/S2 前必须先验证：`torch.cuda.get_arch_list()` 输出含 `sm_87`；再做一次板上 CUDA matmul 冒烟（GPU 张量相乘并读回结果核对）——`torch.cuda.is_available()` 为 True 不算通过（Thor 报告证实其可能误报）。任一失败即停下回用户改来源，**不在信封内换源**。
   - **官方轮子自带 CUDA 13.0 运行库与系统 CUDA 13.2 / TensorRT 10.16 共存的风险与核对点**：(i) 前向兼容：JP7.2 驱动/系统 CUDA 13.2 ≥ pip 侧运行库 13.0.48，无驱动降级风险。(ii) **库路径串扰**（主要风险）：pip `nvidia-*`（含 cu13 后缀与无后缀两系）装入系统 venv 的 `site-packages/nvidia/*/lib`，torch 经 RUNPATH 自取；若 `LD_LIBRARY_PATH` 把 venv 的 nvidia 库目录置于系统库之前，S1/S2 的系统 TensorRT 10.16 / trtexec 可能误载 pip 版库（版本错位）；反向顺序则 torch 可能误载系统库（LightNav 的 Thor 文档记载 nvJitLink 符号未定义崩溃实例）。核对点：`import torch` 与 TRT 引擎构建各自在不设 `LD_LIBRARY_PATH` 的干净环境下通过；必要时以 `ldd` 核实 TRT 进程解析到 `/usr/local/cuda` 系统库。(iii) cuDSS：官方 cu130 轮子运行期链接 `libcudss.so.0`（Thor 论坛实例，该机用 apt 补装）；核对点：安装前 `ldconfig -p | grep cudss` 记录基线——板上 JP7.2 完整 CUDA 13.2 若已含 cuDSS 则由系统满足，缺失时由或然包 nvidia-cudss-cu13 0.8.0.10 补齐（已计入申请值）。(iv) cuDNN 双份（pip nvidia-cudnn-cu13 9.13 仅供 torch；TRT 10.16 用系统 cuDNN）按进程隔离，互不声明兼容。
   - **计数口径**：ultralytics / lap / ultralytics-thop / opencv-python-headless 等既有 5 包在系统 venv 的同版本重装**不并入**本额度，沿用「S1/S2 系统栈落实（B）」已定写法（既有 ≤ 8 包 / 300 MB 维度与信封内重试归因）；模型下载仍 0；阶段 B 全部维度仍 0。

   **原申请值（2026-10-02 CLARIFY-B，主来源 jetson-ai-lab；已被用户选择替代，原文保留）：**

   - **推荐来源（主）**：`https://pypi.jetson-ai-lab.io/sbsa/cu130`（NVIDIA Jetson AI Lab 维护的 Jetson pip 索引；与 JP7.2 / CUDA 13.x / Python 3.12 / aarch64 匹配：cp312 `linux_aarch64` 轮子，torch 2.9.0 / 2.9.1 / 2.10.0 / 2.11.0、torchvision 0.24.1 / 0.25.0，索引页逐轮子附 sha256）。建议 pin `torch==2.9.1` + `torchvision==0.24.1`（元数据实测：torch 2.9.1 轮子 232,390,136 B、torchvision 0.24.1 轮子 2,026,208 B）。
   - **已知风险（如实告知；安装后先验证再跑 S1/S2）**：该 SBSA 索引面向 ARM SBSA 用户态（JP7 统一工具链；Orin 自 CUDA 13.2 起并入）。第三方证据相互矛盾：libreyolo.com/docs/export/jetson（2026-07-27，同型板 Orin Nano Super / JP7.2 R39.2 / Python 3.12.3 实测）与 github.com/straga/jetson-jp7-onnxruntime 指 SBSA 系构建只含服务器 ARM GPU（sm_90/100/110）内核、在 Orin SM 87 上 `no kernel image`；wiki.juxitech.com 的 JP7.2 Orin 教程则称即用该索引。本角色只读查询无法裁决。实现安装后须先以 `torch.cuda.get_arch_list()` 与一次板上 CUDA matmul 冒烟核实 SM 87 可用性；不可用即停下回用户改来源，**不在信封内换源**。另：该索引 torch 轮子链接 NVPL/cuDSS 但未声明依赖（github.com/pollen-robotics/microduck_rl issues#38），故 nvpl-blas / nvpl-lapack / nvidia-cudss-cu13 计入申请包数与字节（PyPI aarch64 元数据 ≈ 2.1 + 33.3 + 80.5 MB）。
   - **申请值（签发后成功、失败、重试全部计入同一上限，耗尽即停）**：
     - **包数 ≤ 16**：torch、torchvision 及其 pip 传递依赖（filelock、typing-extensions、sympy、mpmath、networkx、jinja2、markupsafe、fsspec、pillow、numpy）与 nvpl-blas、nvpl-lapack、nvidia-cudss-cu13；
     - **下载字节 ≤ 900 MB**（主力组合元数据合计 ≈ 386 MB：torch 2.9.1 232.4 MB + torchvision 0.24.1 2.0 MB + nvpl 三包 ≈ 116 MB + 纯 Python 传递依赖 ≤ 35 MB；上限含至多一次同维度内更换 torch 小版本——如 2.11.0、轮子 296.9 MB——的工程性重试）；
     - **安装后新增磁盘 ≤ 3 GB**，计入板上磁盘维度：阶段 A「板上磁盘」生效值相应申请由 ≤ 5 GB（`~/eng-jet/`）调整为 ≤ 8 GB（含容器 venv/wheels 保留量与轮子下载落盘）。
   - **计数口径**：ultralytics / lap / ultralytics-thop / opencv-python-headless 等既有 5 包在系统 venv 的同版本重装**不并入**本额度，按既有 ≤ 8 包 / 300 MB 维度与信封内重试归因（决策记录「S1/S2 系统栈落实（B）」）；模型下载仍 0；阶段 B 全部维度仍 0。
   - **备选（须用户明示选择，本角色不代选）**：(i) 改用 PyTorch 官方索引 `https://download.pytorch.org/whl/cu130`——非 NVIDIA 域名，超出「NVIDIA 官方或 NVIDIA 维护的 Jetson 索引」口径，但 NVIDIA 论坛官方 moderator 曾对 JP7 aarch64 设备推荐（forums.developer.nvidia.com「Pytorch install broken on Jetson Thor」，AastaLLL），且 libreyolo 同型板实测可用的正是该索引轮子（torch 2.9.1+cu130 aarch64 轮子 512,448,274 B，另需 nvidia-cudnn/nccl/cusparselt/nvshmem-cu13 系库，下载量更大，**若选此项上述申请值须相应扩额重签**）；(ii) **来源待用户提供**（例如用户已验证可用的轮子或索引），签发时写明来源与数量。

（2026-10-02 更新：题 4 已经用户逐字签发（账本同日「用户按申请值签发 torch/torchvision 下载与安装额度（官方 cu130 源；SUB:1…）」），并按推荐签发 SUB:3（账本同日「用户按推荐签发 SUB:3：torch 依赖下载上限 3.5 GB → 6.5 GB」）——SUB:1 下载字节上限现行生效值 ≤ 6.5 GB，其余维度不变；合同落实见决策记录「SUB:3 落实与安装方式合同解释」与「CLARIFY 表」新行。IR-14/15 裁定见「待裁定」。题 2（停点全套 Mac 模型额度）、题 3（§7 (h) 有线就绪）原样保留、不代为裁定。）
（2026-10-02 更新：交接「待用户（补跑C）」题 1（即题 6）用户已选 **A** 并逐字入账（账本同日「P1-ENG-JET-001 — 用户选题 6 A：官方 torch 无 sm_87 时接受同主版本二进制兼容读法继续 S1/S2…」）——题 4 装后验证第一项由决策记录「题 6 选 A 落实：装后验证第一项替代判据（AC-2 修订 6）」替代，IR-16 (a)–(d) 裁定见「待裁定」；S1/S2 由 supervisor 在 Mac mini 派实现续跑。题 2（停点全套 Mac 模型额度）、题 3（§7 (h) 有线就绪）原样保留、不代为裁定。）


### needs_user（补跑D；当前用户交接，2026-10-03）

本节保留补跑D交接记录：第 1 项已由用户选 (α) 并入账落实，第 2 项仍未决；第 3 项 SSH 前提已被同日后续主机密钥授权替代，原文仅为授权前记录。当前用户交接与下一派发范围见「needs_user（补跑F；当前用户交接，2026-10-03）」；前面的历史请求/已答复记录保留。第 1 项是用户直接裁定的硬件读数取舍，不是 supervisor 代拍；第 2 项信封未签仍为 0，不跑全套。

1. **已答复：S1 `STOP(FP16_BOX_DIVERGENCE)` 的处置——用户题 7 选 (α)**；见账本 2026-10-03「P1-ENG-JET-001 — 用户选题 7 (α)：S1 STOP 记录偏差、以方形 FP16 引擎继续（supervisor 会话代录）」与决策记录「题 7 选 (α) 落实」。以下保留原二选一及理由：
   - **(α)（推荐）**：记录偏差、以该方形 FP16 引擎继续（S1 保持 `STOP`，后续 S2/SR 标 `RESUMED_AFTER_USER_RULING(S1)`，阈值与引擎精度不改）。
     理由：时延分量远低于 200 ms 门（p95 59.29 ms）；S2/SR 测的是热稳态与跨机中继，不依赖与 MPS 缓存的逐框一致；偏差形态（帧 0 即差 2.2e-3、
     而输入形状与参照一致的矩形引擎无计数不一致与未配对）提示主因可能是方形引擎的 640×640 填充而非 FP16 数值崩坏（未验证，见 `-report.md` §2d）。
   - (β)：关闭本项。
   - 说明：改用矩形引擎作 verdict 对象或改 1e-3 线属合同变更（不在 §2.1 二选一内），本角色不提出也不执行。
2. **停点全套的 Mac 模型额度**（`P1-ENG-JET-001:b0a5f79c:SUB:2`）：不变，仍推荐在 S1/S2 有可交复核读数后的真正停点签发。
3. §7 (h) 有线已接好（Mac mini 192.168.8.1 ↔ Jetson 192.168.8.2），且 mini 代理经有线地址已可达，原 `No route to host` 已排除；依据账本同日「P1-ENG-JET-001 — 用户告知 Mac mini ↔ Jetson 有线直连成功（§7 (h) 答复；supervisor 会话代录）」与状态板 Log「P1-ENG-JET-001 mini 代理经有线地址可达（supervisor）」。正式 SR 须在已落实 (α) 且 S2 可继续之后、阶段 A 剩余 4 轮内执行。现有 known_hosts 无有线地址条目，正式 SR 如需有线 ssh 须按决策记录复用已存 Tailscale 主机密钥、不落盘；无法验证则写 needs_user，不自行改 `~/.ssh/*` 或 macOS 隐私/网络设置。

接受角色意见：推荐 (α)，理由是可在保留 S1 负结果与既有阈值的前提下，继续取得热稳态和中继的描述性读数；一致性差异与失锁读数不支持身份/捕获正确性，输入形状解释尚未验证，不能作为已证明的偏差归因。

- **选 (α) 后（已入账并落实，现行派发细则见决策记录「题 7 选 (α) 落实」）**：supervisor 可在 Mac mini 派实现：复用本轮方形 FP16 引擎（运行时由证据解析身份）、保持 S1 STOP，续跑 S2 15 Hz / 30 min（未达 ≤33 ms 加测条件，不测 30 Hz），后续证据/报告标 `RESUMED_AFTER_USER_RULING(S1)` 并指到账本；执行 IR-17 分列、AC-16 缓存重定向和 IR-19 条件性清理，更新证据现状。S2 再 STOP 时仍停全部后续；S2 可继续后，准备原范围 SR (b) 真实应答器、先核验 mini 代理有线可达，再按原 AC-4…6 执行正式 SR。均计入阶段 A 现有余额，不重跑 S1、不换矩形引擎作对象、不改阈值、不新增额度；S3–S5 仍受未签阶段 B 约束，SUB:2 未签前不跑全套，未满足停点自证前不送 C1。
- **选 (β) 后**：用户关闭决定逐字入账后，由接受角色按终止规则将本项收为 `CLOSED_NEGATIVE_RESULT` / `ENDED`，整行与停点/未闭义务移至 `docs/parked-status.md`，保留 S0/S1 描述性读数、S1 STOP 和未运行项、证据与信封累计账；移除活跃交接，剩余额度不继续执行。关闭不等于验收通过，不追认独立复核/UNITY_NA，不产生 M7/部署通过主张，不自行清理板子文件。

### needs_user（补跑E；当前用户交接，2026-10-03）

以下保留交接「待用户（补跑E）」原选项；当前交接见「needs_user（补跑F；当前用户交接，2026-10-03）」。第 1 项已由用户选 (α′) 并入账、落实；第 2 项（SUB:2）原样保留，仍未签，改变 Mac 模型信封须用户逐字入账，不在 supervisor 代拍闭集内。

1. **已答复：S2 `STOP(FRAME_DROP)` 的处置，用户选 (α′)**：依据账本 2026-10-03「P1-ENG-JET-001 — 用户选 S2 STOP 处置 (α′)：S2 记录偏差并继续，做原范围正式 SR（supervisor 会话代录）」；放行与边界见决策记录「S2 处置选 (α′) 落实」。以下原选项保留为历史：
   - **(α′)（推荐）**：记录偏差并继续——S2 保持 `STOP`，后续 SR 标 `RESUMED_AFTER_USER_RULING(S2)`，阈值不改；下一实现派发准备 SR (b) 并做正式 SR。
     理由：热与时延比值两项都过（无降频、p95 比 1.0021），丢帧来自首次 init 冷启动（50）与每回放周期固定两帧（168）；15 Hz 只是板上压力档，运行时合同为 5 Hz（周期 200 ms，
     本轮单次 `update` 最大 129 ms，未经 5 Hz 实测）；SR 测跨机中继，不依赖 15 Hz 丢帧结论。
   - (β′)：关闭本项。
   - 说明：改丢帧判据（如剔除冷启动）、改帧率或改阈值属合同变更，本角色不提出也不执行。
2. **停点全套的 Mac 模型额度**（`P1-ENG-JET-001:b0a5f79c:SUB:2`）：不变，仍推荐在有可交复核读数的真正停点签发。

接受角色意见：推荐 (α′)，可在保留 S1/S2 STOP 与原阈值的前提下取得正式中继的描述性读数；15 Hz 的负结果、未经验证的丢帧成因与 IR-20 告警限制全部随交接，不据最大 update 时延推定 5 Hz 无丢帧，不推定 5 Hz 合同或部署已通过。SUB:2 保持第 2 项原请求，仍未签。

- **选 (α′) 后的下一派发（已落实）**：原条件计划已按上述用户账本转为决策记录「S2 处置选 (α′) 落实」的正式放行范围与边界；实现只依该节推进。
- **阶段 A 余额核对（补跑E收尾；不是追加额度）**：以 `-ledger.json`「dimensions」为源，板上墙钟余 **23,034 s**（5,766/28,800）；SR 余 **4 轮**，每轮 ≤100 MB，冒烟 1/1 已耗尽；到板余 **81,684,056 B**；板上磁盘余 **7,929,536,193 B**（上限 13 GB）；SUB:1 新增盘余 **3,170,027,375 B**；Mac outputs 余 **1,950,331,061 B**。板上既有 pip 余 1 包 / 57,247,361 B，SUB:1 下载余 883,642,289 B、包数余 9，但 SR 准备/正式轮复用已装栈，计划新增下载/安装 0。每次上板或正式 SR 前从最新账重新核对预计墙钟、轮数、传输、磁盘及证据余量；成功/失败/重试累计，不足即停回用户，不从其他项借额度。
- **有线 SSH 现状**：账本 2026-10-03「P1-ENG-JET-001 — 用户授权把 Jetson 有线地址主机密钥写入 Mac mini `~/.ssh/known_hosts`，并指示接受收工后直接派实现跑 S2（supervisor 会话代录）」仅授权的三键追加已完成；补跑E已用 `ssh jetson@192.168.8.2`、`BatchMode=yes`、`StrictHostKeyChecking=yes` 成功。本项后续可直接复用已存有线地址键；旧「题 7 选 (α) 落实」及补跑D交接的「无此地址条目」事实前提已失效，不再要求借 Tailscale 别名。下一派发先只读核验连接；不得再改 `~/.ssh/*`、放宽主机密钥检查或改网络/隐私设置，无法验证即停对应动作回用户。该主机密钥账本只放行已执行的 S2；S2 STOP 后的 SR 现由本节第 1 项新账本及「S2 处置选 (α′) 落实」放行。
- **选 (β′) 后的收口**：关闭决定逐字入账后，由接受角色收为 `CLOSED_NEGATIVE_RESULT` / `ENDED`，Gate 整行及停点/未闭义务同批移入 `docs/parked-status.md`，移除活跃交接；保留 S0、S1/S2 描述性读数与两次 STOP、IR-20 限制、全部未运行项、证据及信封累计账，剩余额度停止执行。不作 DONE、不追认独立复核/UNITY_NA，不产生 M7/部署通过主张，不自行清理板子文件。

### needs_user（补跑F；当前用户交接，2026-10-03）

**现状更新（K1K3K4全套待裁定）**：第 1 项已由用户逐字签发并完成接受侧合同落实；实现跑前核对因未列名 det-assoc/暂停项回放未签而停，全套仍 0 次，现行停因与 CPU 偏差见「K1K3K4全套记录核对」及 IR-23，当前用户请求见下一节 SUB:5。下列请求、推荐与签后条件计划保留为签发前原文，其 SUB:2 用户签发/接受落实前置已满足；第 2 项再跑 SR 的边界仍有效，当前不申请追加轮。

1. **原请求原样转用户：停点全套的 Mac 模型额度**（`P1-ENG-JET-001:b0a5f79c:SUB:2`）：维度 = 本机 CPU 一次全套内的模型加载；数量参照 FRAME-001 先例（NanoTrack ≤ 4、YOLOE ≤ 2、DINOv2 ≤ 2、CSRT ≤ 2，一次全套）；理由 = IR-9。未签仍为 0，保留 Mac 零 pip，不能借其他项信封；这是用户签发执行信封追加，不是 supervisor 子额度审批或代拍题。
   - **实现推荐**（交接「待用户（补跑F）」）：IR-21/22 裁定后签发，以便跑停点全套并送 C1；阶段 A 读数现已齐，focused 不能替代全套，未签自证第 2 项不能成立。
   - **接受推荐**：现在按上述原额度签发一次停点全套；本轮合同读法已闭合，补齐全套是下一稳定停点的明确缺口，额度限原模型次数、本机 CPU、一次全套，不含新包、下载、额外模型、SR 重跑或阶段 B。若不签则继续等待，不凭超时或推荐执行。
   - **签发后的下一派发（条件计划，尚未放行）**：用户逐字入账后先由接受角色落实 §5 Mac/IR-9 合同，再由 supervisor 在 Mac mini 派 Implementation：按 IR-21/22 更新具名命中分列与原扫描指针，沿 AC-4 修订 2 / AC-5 修订 1 同步统计与风险，保持 S1/S2 STOP、SR 双标与所有限制；仅在具名额度内用既有环境跑停点全套一次，输出写证据、区分基线失败与新增失败，跟踪器相关需 lap 的测试只读用数据根 `.venv-yoloe`，不装包。随后按 AC 逐条补证、重判四项自证、整理冻结候选与准确范围、提交推送；成立后才交接受 `C1@K1K3K4`，再由新鲜上下文独立 `R1@K1K3K4` 核实及 AC-14 UNITY_NA 附议。本计划不放行 S3–S5、不推定 DONE。
2. **再跑 SR 的授权边界（告知，当前不申请新轮）**：SR 5/5、冒烟 1/1 已耗尽；若独立复核需要再跑任意正式/冒烟 SR，须用户另签具名轮数、链路/设备、每轮字节及相应墙钟/磁盘/模型维度并由接受落实后才派执行，不能以其余阶段 A 余额或 SUB:2 覆盖。新增额度与阶段 B 首签均不在 supervisor 代拍闭集内；阶段 B 与 §7 (i)–(m) 仍按未签/未答复缺省不做。


### needs_user（K1K3K4全套；当前用户交接，2026-10-03）

以下为交接「待用户（K1K3K4全套）」签发前请求与条件计划原文，执行仍未发生。**现状更新（K1K3K4落实SUB5）**：用户已签 A、接受已落实额度与回放归属；选 A 计划中的入账/合同落实前置已完成，但 CPU 路径核对未通过，不可派全套。当前用户项只在末节「needs_user（SUB:5 CPU 执行方案；当前用户交接，2026-10-03）」；原推荐与两方案共同边界保留为历史/后续条件，不再请求重签 SUB:5 A。本轮不代写授权账本。

1. **停点全套追加额度**（建议 `request_id` `P1-ENG-JET-001:b0a5f79c:SUB:5`；SUB:4 曾在补跑C 中被建议用于另一用途且未签，为免混淆不复用）：
   - **A（推荐）**：在同一次（仍只一次）停点全套内，追加 Mac mini 本机 CPU 的 det-assoc 冻结检测器（`last.pt`，ultralytics YOLO）加载 ≤ 2 次，并同意 `ResidentCarrierReplay` 的 2 次零模型部分序列回放计入本项而非 ACQ-001；其余（SUB:2 四种模型上限、零 pip、零下载）不变。理由：按合同原样用数据根解释器跑、不动任何 skip 门，覆盖最全；增量只是 5.4 MB 小模型的 2 次 CPU 加载。
   - B：不追加额度，由接受角色 CLARIFY 改用仓库 `.venv-yoloe`（无 `lap`）跑一次全套：所有需 `lap` 的测试会 skip（含上述两类），模型加载 0；代价是需 `lap` 的测试本次不执行、与 R7 基线可比性下降。
   - 若都不选：全套继续不跑，自证第 2 项不成立，不能送 `C1@K1K3K4`。

**实现角色推荐：A**，理由见原文：数据根环境覆盖最全，不改 skip，增加两次小模型 CPU 加载。

**接受角色推荐：B**，理由：在坚持零新增额度和本机 CPU 边界下，用户明确认可环境/覆盖变化后，仓库既有无 lap 环境可自然跳过两类受门控测试，不借暂停项余额；也避开当前真实 Carrier 的 MPS 路径。代价须保留为覆盖缺口，不把 skip 记为通过、不把四项自证预签成立。本轮只读核对仓库解释器 lap 不可定位、cv2 5.0.0 无 CSRT 构造器；原 B 的“模型加载 0”只指预计真实加载，CSRT 构造尝试仍须计数，失败不能回退。若用户更重视这些用例的实际覆盖而选 A，原样请求保留，但 **A 的“CPU 原样跑”前提在当前环境不成立**，不能把选择 A 解释为授权 MPS 或改测试绕门。

**签发/选择后的下一派发（条件计划，当前均未放行）**：

- **选 A**：用户所在会话逐字入账 SUB:5 的两次 det-assoc CPU 加载及两次零模型部分回放归本项；下一派发先交接受角色落实 AC-10/§5 与 ledger 计数口径，保持四种模型上限、一次全套、零 pip/下载/新增模型及 ACQ-001 暂停不变。计账为本项 det-assoc 加载 ≤2（含成功/失败/重试）、ResidentCarrierReplay 部分回放 ≤2，不扣 ACQ-001；首例 768 帧推理不能被“两次加载”豁免 CPU 限制。候选原样命令为 `~/TetheredDroneTracking-full/.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-JET-001-full-suite.log 2>&1`，但当前 `_resolve_device` 会选 MPS，**此命令尚不可派执行**。先由接受角色核对用户明确认可的 CPU 执行方案；如需改测试执行设备/方法或增加 MPS 维度，列明变化再交用户，不能靠单签本请求放宽、不自行 patch 设备探测/冻结规格或设环境变量绕门。CPU 路径与合同未落实前保持全套 0 次，只派零消耗核对。
- **选 B**：用户明确选择并逐字入账后，下一派发交接受角色追加 §5 Mac/IR-23 的解释器 CLARIFY，限本项一次停点全套使用仓库 `.venv-yoloe/bin/python`，取代该次全套执行范围 2 的数据根解释器要求，其他 focused/复核重跑的全局数据根规则不变；接受落实后才由 supervisor 在 mini 派实现。条件命令为 `.venv-yoloe/bin/python -m unittest discover -s tests > docs/evidence/P1-ENG-JET-001-full-suite.log 2>&1`；原样全 tests 一次，不删用例、不改 skip、不隐藏模型/改数据根、不装 lap，不设环境变量诱发 skip。记录各跳过及缺依赖原因与 R7 基线差异；det-assoc 真实加载/这两次 resident 回放均为 0，四种具名模型各按实际加载/构造尝试核账，非零新路径或预计超额即停，不自重跑全套。
- **两方案共同**：实施前按已签字面重新只读核对环境、所有可达真实加载器、计算设备、回放归属、最新 ledger 与 Mac outputs ≤2 GB；保留零下载安装和外部模型/API边界，不以离线保护变量改变 skip 门。实施后同步报告/证据，区分基线已有失败和本批新增失败、如实保留覆盖缺口；沿 AC 逐条补证、由实现重判四项自证，成立后才提交推送候选交 C1→独立 R1 及 AC-14 UNITY_NA 附议。保持 S1/S2 STOP、SR PASS 与双 RESUMED/IR-20 限制；不重跑 S1/S2/SR，不上板、清理、改 SSH，SR 5/5 耗尽、阶段 B 全部维度 0，S3–S5 不放行。未选则停点全套继续不跑。

### needs_user（SUB:5 CPU 执行方案；当前用户交接，2026-10-03）

**现状更新（K1K3K4落实CPU1）**：用户已逐字授权 CPU-1，接受侧已落实 AC-10 修订 6，当前无待用户的 CPU 选项；交 Implementation 改两处测试并完成跑前核查，满足后在已签额度内跑一次全套。现行计划及条件命令见「CPU-1 落实与下一实现范围」。下表及“选择后的条件计划（尚未放行）”均保留为选择前原文，不再以其未授权/Owner 用户文字发令；实际测试仍未改、全套仍 0 次。CPU-1 两项风险已经用户认可，其他选项未授权。

**需用户决定的唯一题：Carrier 两例如何执行。** SUB:5 A 的额度/回放归属已落实，不需重签；它明确排除了以下执行变化，故不能由接受角色或 supervisor D5 代拍。全套继续 0 次，Owner `用户` / Status `WAITING_FOR_USER_RULING`。各项均为待授权方案，本轮未实施，不提供已放行命令。

| 选项 | 需用户明确授权的具体变化 | 影响与风险 | 推荐与理由 |
|---|---|---|---|
| CPU-1：两例显式 CPU | 仅改 `tests/test_det_assoc_carrier.py:CarrierSelfTest` 两处构造调用，使用既存 `DetAssocTracker(spec_path=SPEC, device="cpu")`（默认 compat、真实默认加载器/关联器）；保留两例其余流程/断言、原 skip、冻结规格/权重与数据根解释器，不改 controller/config。授权这种测试执行设备/方法变化后，由接受追加合同解释，Implementation 改测试。 | 保持两次真实加载及帧回放覆盖，不靠探测或环境变量绕门；这两例不再经过 `create_tracker` 工厂，工厂注册的既有替身测试 `tests/test_det_assoc_tracker.py:test_factory_registers_det_assoc_and_cli_default_unchanged` 仍在全套中，但不能当作真实工厂集成覆盖。CPU 对原口径 B 的逐帧完全相等断言可能失败；不换基线、不放宽断言，不根据结果改数，失败如实保留并停下。 | **推荐 CPU-1**：尊重用户已选 A 的实际覆盖与 CPU 目标，变更集中在两例调用，保持运行时代码/冻结规格和资源边界。接受上述真实工厂覆盖损失与 CPU 比较风险后才授权；不是本轮既有授权。 |
| MPS-2：原样两例使用 MPS | 仅将本次两例 det-assoc 推理设备授权扩为当前冻结策略实际选择的 Mac mini MPS（同一次全套、加载≤2、回放≤2）；须用户明确修订本机 CPU 字面、签具名 MPS 计算维度与上限（建议限本次两例原有帧/调用：首例≤768次、第二例≤1次逐帧 predict，合计≤769次，不另加预热/推理重试），接受落实后才可派发。SUB:2 其他四种仍 CPU，不扩为全模型 MPS。 | 无测试/代码/规格/skip 变化，保留真实工厂路径及全部门控覆盖；新增 MPS 计算授权，结果只属 Mac mini MPS，不能称 CPU 或 Jetson 证据，仍可能存在库版本/基线差异。 | 不优先推荐：较少代码变化，但需改变用户刚签的 CPU 资源边界；若用户优先保留原样工厂覆盖，可选此项。未签 MPS 维度/额度即 0。 |
| SKIP-3：选择原 B 的仓库解释器 | 用户明确许可本项一次全套改用仓库 `.venv-yoloe/bin/python`，替代该次需 lap 用例的数据根执行口径；不改全局 focused/复核规则、不装 lap、不改 skip 或设环境变量。已签 SUB:5 不消费、不转用。 | 缺 lap 自然跳过 Carrier/ResidentCarrierReplay 及其他需 lap 用例，det-assoc/该两次回放均0；覆盖缺口增多、R7 可比性下降。CSRT 构造尝试照计，不把 skip/失败记通过；实现仍须重判停点自证，不能预签成立。 | 不优先推荐：可避免 MPS 路径，但不能满足用户选 A 希望实际覆盖的两例 CPU 推理。只有用户认可覆盖变化后可落实。 |
| SPEC-4：改冻结 preferred 为 CPU | 改主树 `config/det-assoc-v1.models.json.device_policy.preferred` 为 cpu，并由用户重定冻结规格/来源哈希合同与 AC-2、AC-10/11 的不改配置边界；不能偷偷另造 CPU spec 替换固定 SPEC。 | 影响所有按默认规格构造的消费者与冻结身份，超出两例测试；原冻结证据不能直接继承，新候选需重新核对/复核，成本与混淆风险最大。 | 不推荐：扩大运行时语义和冻结边界，CPU-1 的既存构造参数可把影响局限于测试。 |

若暂不选任何变化，保持当前交接和全套 0 次，不送 C1；“等待”不等于通过。禁把 `torch.backends.mps.is_available` monkeypatch 为 False、注入异常、隐藏模型/帧、改 `ENG_DET_DATA_ROOT` 或设置设备/离线环境变量包装原全套当作现成 CPU 方案：它们改变设备探测、方法或 skip 门，SUB:5 明确不授权，且弱化原真实路径，均不推荐。本轮也不批准扩展 compat 工厂传 device：那会改 controller，触及 AC-10 的空 diff 与更广接口范围。

**选择后的条件计划（尚未放行）**：用户所在会话先逐字入账选项及具体变化；接受角色按所选范围追加合同解释，再交 Implementation。CPU-1 先完成具名测试改动及不加载真实模型的核查，不在全套外再跑 Carrier 两例；MPS-2 须先签/核对具名 MPS 计算维度与上限；其他项按表处理覆盖或冻结合同。原 A/B「两方案共同」边界继续有效：跑前核所有可达真实加载器/设备、最新 ledger 和 outputs 余量，跑后基线/新增失败分列、同步证据、沿 AC 补证并由实现重判四项；成立才交 C1→独立 R1/UNITY_NA 附议。仍只一次全套，成功/失败/重试计入既有各上限；任何额外真实 focused/返工加载、回放或再次全套不能凭本计划自动放行，超额回用户。S1/S2 STOP、SR PASS/双 RESUMED、IR-20 限制、SR 5/5 耗尽、阶段 B=0 和 ACQ-001 暂停不变。

### needs_user（K1K3K4全套CPU1；当前用户交接，2026-10-03）

本节两项已由账本 2026-10-03「P1-ENG-JET-001 — 用户裁定线 A 全套结果…」裁定为 1A、2环境分列，并由 `K1K3K4落实1A` 落实；当前交 Implementation 零消耗整理证据、重判自证，见决策记录「1A落实与证据整理」。以下原请求/推荐与条件计划保留为裁定前原文，不再是当前用户等待；此前 CPU-1 节的执行前快照亦不代表当前已用额度。不代写用户账本，不预签 C/R 结论。

1. **Carrier CPU 比较失败的处置**（经接受角色 IR-24 读法后转用户）：
   - **A（推荐）**：接受「CPU 与 MPS 参考存在浮点级差异、该例记为已知失败」，不改断言/基线，候选以此进 C1/R1，失败与差异作为未闭限制随候选交复核。理由：差异在 1e-7 量级、不涉及状态/原因，且其余流程断言均通过；再改测试或换设备都要新授权与第二次全套。
   - B：签发新口径（例如 CPU 参考重算或 MPS 推理）后再跑一次全套：需新的模型/设备/全套额度，并改变测试基线或执行设备。
2. **scene006 29 条**：按 IR-25 读作环境基线（推荐，理由：相关代码零 diff，失败发生在冻结处置链第 1 步权重哈希绑定）；若要求在本机实测通过，须另行授权把 re-anchor/NanoTrack 权重放入主树 `runtime/`（本项不做）并另签一次全套。

**双方推荐与证据限制**：第 1 项实现推荐 A，理由原文如上；**接受也推荐 A，但必须连同以下限制一起决定**：只有首个索引的差异量级/state/reason 已打印，其余 9 个未知，比较后的断言未执行，故不认可原文把这些性质推广至全部差异或全部流程。推荐原因是保留用户已选 CPU-1 的真实失败与冻结判据，先由异源核对/独立复核判断影响，避免在未明差异上重算参考或更换设备造成归因混淆；不是确信失败无影响。用户须明确许可“携带 Carrier 已知失败、其余 9 个差异未知及后续断言未执行，作为本次停点测试条件具名例外进入 C1/R1”；仍不记测试通过、不预定复核 verdict。第 2 项**实现与接受均推荐按 IR-25 分列环境失败**；理由是处置链在推理前检查缺资产、相关代码零 diff，保持主树隔离且不为旧用例补资产；仍保留相对 R7 新增 29 条及未验证后续行为。

**选择后的下一派发（条件计划，未放行）**：

- 第 1 项 A + 第 2 项环境分列：用户所在会话先逐字入账上述具名例外及选项；下一派发给 Acceptance 零消耗落实用户裁定（不签新额度、不改断言/阈值/AC 判据），再给 Implementation 仅整理证据：同步本节读法、准确版本取样/索引、保留失败/skip/网络/SUB:5 单测缺口，冻结完整候选并重判四项。第 1 项须恢复为冻结；第 2 项如实记录测试失败及用户例外，不能涂成“通过”。其余稳定条件具备且具名例外明确适用于 C1/R1 后才交 `C1@K1K3K4`，C1 完整读候选/AC/关联代码、零测试；后续独立 R1 可判阻断，不以用户继续决定预签通过。真实模型/回放/SR 复核重跑无余额，需另申请后才能执行，不能借 A 自动消耗。
- 第 1 项 B：下一派发只给 Acceptance 零消耗固定新口径与逐维申请（设备、测试基线/方法、参考重算/推理次数、模型加载、全套次数、回放、输出及所需时长等；缺项=0），交用户逐字签发后才给 Implementation。当前 B 是方向选项，未列足额度，不是执行授权；旧比较失败/全套 1 次不删除，不保证新口径通过。
- 第 2 项要求本机实测通过：下一派发只给 Acceptance 零消耗准备主树 `runtime/` 写入例外、资产闭集/来源/传输与占用、所需模型/设备及第二次全套额度申请；用户签足并落实 AC-12 具名变更后才给 Implementation，保留旧失败和读码归因。现行合同禁止主树写入，不能先放资产；与第 1 项 B 并选时共列预算、不重复签或自动多跑。
- 任一项未裁定，当前等待与自证第 1/2 项状态维持，不派 C1、不重跑。新增额度、基线/设备变化、主树资产例外，以及携带已知失败越过现行停点条件均须用户决定；不交 supervisor D5/SUB 代拍。全套 1/1、det-assoc 2/2、部分回放 2/2 均不回退；本轮零正式 ID/Play/API，未动任何计算/下载资源。

### needs_user（阶段B；线 B 用户交接，2026-10-03）

详见本提案「阶段B签发包刷新（2026-10-03，线 B）」§8 needs_user汇总：阶段B:1、阶段B:2、阶段B:3、阶段B:4、阶段B:5、阶段B:6、阶段B:7、阶段B:8。

### needs_user（阶段B答复落实，2026-10-04）

现行入口已收拢至「阶段B准备审核」§5；以下原清单保留作来源，不再单独发令或并列发问。

B:1–8 已答复并落实，A收口:1 不适用，不重复提问。以下才是现行未定项；额度/系统/设备/采样/阶段及 STOP 缺省处置不代拍。可先完成零消耗准备，不等待这些答复；消耗动作仍不能开始。完整出处、机器与逐维度建议见「阶段B答复落实」§2–4。

- **B-SIGN（B:6的后续签发）**：准备经接受核对后由用户逐行签 §4，推荐按核实的刷新主案上限，理由是各维度分列可约束失败/重试及实际占用；依赖未核的行推荐保持0/不签，理由是engineering§9先核事实。候选全套伴随模型/回放清单仍须准备后另列非零申请，不能用全套次数涵盖未列加载。此轮全部未签。
- **B-PRESSURE（15 Hz）**：是否另跑描述性压力读数未定；推荐本次暂不追加（该档0），理由是用户已定5 Hz运行时判定，应先得到该档共驻读数；若用户选追加，另列墙钟/查询与样本上限入信封。此推荐不当答复，未答复不跑。
- **B-LINES（补核分类）**：推荐保留 §2 的S3时延/4.6 GB、S4的3 pp、S5的1.3倍/7.0 GiB为描述性，理由是来源移植/公开估算且无目标条件真实读数；不把签发预算当这些线转STOP的确认。用户若要停止线，推荐先另明确目标条件试读与新判据再裁，不事后按已得读数挑门。B:3公式和B:2稳态连续线已按明确用户合同落实，无须重问。

**逐码处置待用户随信封确认（每条推荐与理由如下；未确认仍按原总则 STOP→停全部后续→回用户）：**

- **B-STOP-NOT_SUPER**：推荐停全部阶段B后续回用户；理由是目标设备合同不符，重刷不在代理权限内。
- **B-STOP-FREQ_CAPPED**：推荐环境实际不符报STOP后停全部回用户，纯厂商频率参照偏离只记录继续已签步骤；理由是公开数字不能单独触发STOP，不自行锁频。
- **B-STOP-NOT_HEADLESS**：推荐停全部后续回用户；理由是headless是运行合同，isolate/默认target未授额。
- **B-STOP-POWER_MODE_NOT_MAXN_SUPER**：推荐停全部后续回用户；理由是指定模式不符，本项不得自行改功耗。
- **B-STOP-IDLE_RAM_OVER**：推荐只超1.2 GB公开参照时记录后继续已签步骤，实际资源不可用已报STOP时停全部回用户；理由是旧数字来自其他条件，不能作为B停止线。
- **B-STOP-LATENCY_OVER**：推荐如合同失败确已报STOP则停全部后续回用户；理由是不得自动换基准，移植速度超线只描述，不触发该码。
- **B-STOP-FP16_BOX_DIVERGENCE**：推荐新STOP停全部后续回用户；理由是α/B:1只具名继承历史S1负结果，不授权新的偏差续跑。
- **B-STOP-THERMAL_THROTTLE**：推荐确证热降频后停全部后续回用户；理由是动态频率不能冒充热降频，本项不能锁频/改散热。
- **B-STOP-FRAME_DROP**：推荐新STOP停全部后续回用户；理由是α′不覆盖新STOP，S5稳态丢帧沿CORESIDENCY_OVER码，不改S2历史。
- **B-STOP-RELAY_INTEGRITY**：推荐停全部后续回用户，不重跑SR；理由是SR5/5已耗尽，板上补丁与真实重连未验证。
- **B-STOP-KERNEL_PARAM_REQUIRED**：推荐停全部后续（包括其他路径）回用户；理由是cma等系统参数未授权，不能自动换栈规避。
- **B-STOP-VLM_OVER_LINE**：推荐所有已选路径合同不可用时停S4/S5回用户；理由是无有效对象，描述性速度/4.6 GB超线不触发停止；单路径PATH_UNAVAILABLE仍按合同继续3c。
- **B-STOP-QUANT_NOT_EQUIVALENT**：推荐合同G5/解析失败时停剩余S4/S5回用户；理由是三态/格式退化须用户取舍，3 pp参考超线仅描述，不自行改配方。
- **B-STOP-CORESIDENCY_OVER**：推荐合同快层/稳态连续丢帧/NvMap-OOM/swap失败时停所有追加尝试回用户；理由是共驻失败不能自行改帧率、换产物或加压力档。

准备若发现校准数据/划分、S4-a基准、环境或依赖新增缺口，构思逐项追加带推荐/理由的needs_user并交接受，不能擅定；当前未核项见本轮 §3，未给未核维度签发许可。**下一owner/status只在状态板交接行维护**。
