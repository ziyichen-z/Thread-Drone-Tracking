# P1-ENG-LOOP-002 — OPS操作增量验证清单（OPS:VALIDATION:7；Implementation，MacBook Air，零消耗）

- 登记轮次：`OPS操作增量实现`（Implementation，Opus 子代理，supervisor 派发；Dispatch-Id `P1-ENG-LOOP-002-OPS操作增量实现-20261008T003015Z-a43a`）。
- 合同：同名提案「OPS九题答复落实（2026-10-07，Acceptance）」§2 AC-13 修订 1、§5「新验证清单（VALIDATION:7）」行：**先列清单再首签**；用户尚未签的各维度一律 0。
- 本文件只列清单与申请，**不是授权、不预签任何次数**。授权须由用户在会话中逐字给出、入账后由接受落实。
- 申请信封标题（`request_id` 前缀据此派生，跨重派稳定）：`P1-ENG-LOOP-002 OPS操作增量验证信封（OpsK1K2K3K4）`，标题 sha256 前 8 位 `9bac8fd0` → `request_id` = `P1-ENG-LOOP-002:9bac8fd0:SUB:<n>`。

## 1. 本轮已在零消耗信封内执行的项（记录，非申请）

| 项 | 目的 / AC | 执行机 / 解释器 | 命令 / 套件 | 模型加载 | 真实归档回放 | 次数 | 墙钟 / 新增磁盘 | 网络 / 设备 / Play / 正式 ID |
|---|---|---|---|---|---|---|---|---|
| F-1 focused | AC-5/8/9/10/11/13/14/15/16/18 修订的相称零模型验证 | Air；系统 `python3` 3.14.6 | `python3 -m unittest tests.test_eng_loop2_operator_web tests.test_eng_loop2_play_ops tests.test_eng_loop2_summarize_ops tests.test_loop2_isolation tests.test_language_loop tests.test_eng_loop2_analyze`（输出 `docs/evidence/P1-ENG-LOOP-002-ops-focused-tests.log`） | 0（无模型文件加载；2 例按既有条件跳过） | 0（`test_eng_loop2_analyze` 只用临时目录合成夹具） | 开发期多次（focused，不计停点全套） | 约 40 s/次；临时目录自动清理，入仓日志 < 2 KB | 0 / 0 / 0 / 0（假 `ssh`/`curl`/Python 替身与本机 git 临时仓库） |
| F-2 网页本机探针 | W1–W4 实际浏览器行为（预览解码后才可确认、点击不被轮询重绘吞掉、跳过、计划末 stop、反馈） | Air；系统 `python3` + 内置浏览器面板 | scratchpad 探针（真实 `App`/`PlanScheduler`/`Submitter` + 替身会话写生产格式桥文件；`127.0.0.1:8779`） | 0 | 0 | 1 | 约 3 min；scratchpad，不入仓 | 仅 127.0.0.1 / 0 / 0 / 0 |
| F-3 保真页工具探针 | `operator_web fidelity` 只读页本身可用（浏览器自算 sha 一致） | 同上 | 两张**合成** PNG（scratchpad；不是 AC-11 所需的人眼核对） | 0 | 0 | 1 | < 1 min | 仅 127.0.0.1 / 0 / 0 / 0 |
| F-4 来源只读核 | SOURCE:2：Air 现有 JET C2 来源原件可解析 | Air；`.venv-yoloe/bin/python`（只读） | `python3 -m tools.eng_loop2.play_ops --out <scratchpad>/srccheck --python .venv-yoloe/bin/python source` → `SOURCE_LOAD_OK`，rc 0；`source.env` sha256 `6d26872fd7323c2f5d56fa432dd6e5f56b0a84c74f65ff02c26149e78311c2a8` | 0 | 0 | 1 | < 5 s；scratchpad | 0 / 0 / 0 / 0 |
| F-5 计划冻结探针 | `plan` 阶段与操作单第 7 节读数逐字一致 | Air；`.venv-yoloe/bin/python` 跑原 `analyze_play derive-bc`（离线几何，零模型） | `python3 -m tools.eng_loop2.play_ops --out <scratchpad>/planprobe --python .venv-yoloe/bin/python plan --p2-object red_car` → `PLAN_FROZEN`，rc 0（探针计划只在 scratchpad，**不是正式预登记**） | 0 | 0 | 1 | < 10 s；scratchpad | 0 / 0 / 0 / 0 |

本轮 SSH/Jetson/板服务、Unity/Play、真实模型加载、归档回放、全套测试、5060/云/API、下载/安装、实际 `runtime/` 桥/帧/锁写入、正式 ID：**全部 0**。

## 2. 新停点 `OpsK1K2K3K4` 稳定条件所需、超出本信封的验证项（申请；未签 = 0）

| request_id | 项 / 目的 / 覆盖 AC | 执行机 / 解释器 | 命令 / 套件 | 模型（零模型或真实加载器）及计数 | 数据 / 真实归档回放 | 每候选次数 / 最多候选数 | 墙钟 / 新增磁盘 | 预览样图来源 / 人眼执行人 | 网络 / 设备 / Play / 正式 ID | 未核事实 |
|---|---|---|---|---|---|---|---|---|---|---|
| `P1-ENG-LOOP-002:9bac8fd0:SUB:1` | 停点全套一次（AC-13 修订 1：基线失败与新增失败分列；稳定条件②） | MacBook Air；系统 `python3`（与 N-1 三次全套同口径）；不装包 | `/usr/bin/time -l python3 -m unittest discover -s tests > docs/evidence/P1-ENG-LOOP-002-ops-tests.log 2>&1; tail -n 3 docs/evidence/P1-ENG-LOOP-002-ops-tests.log`（不带 `-v`） | 新增三份测试与隔离追加 = 0；既有部分沿 N-1 静态清单为 NanoTrack-v2 真实 ONNX 构造 2、CSRT 构造尝试 2（实例 0）、det-assoc/YOLOE/DINOv2/VLM/HF 0——**该清单是 2026-10-06 的旧静态读，不假定今日全套一致：每次全套内真实模型加载数 UNKNOWN**，签发前可先由实现做一次零消耗静态复核 | 0（不读正式/旧真实归档） | 每候选 1 次；最多 3 个候选（稳定候选 + 至多 2 次返工） | 每次 ≤ 15 min（N-1 三次实测约 187–207 s real）；证据日志 ≤ 2 MB，临时目录自动清理 | — / — | 0 / 本机 / 0 / 0 | 既有 13 个基线失败（4 failure + 9 error，N-1 三份日志）是否不变：UNKNOWN |
| `P1-ENG-LOOP-002:9bac8fd0:SUB:2` | 离线样帧人眼保真核对一次（AC-11 修订 1 / OPS:PREVIEW:6；稳定条件之一，须入新候选证据） | MacBook Air；系统 `python3` + 本机浏览器 | `python3 -m tools.eng_loop2.operator_web fidelity <≥2 张 PNG>`（只读页，`127.0.0.1:8773`；与操作页候选预览同一 `<img>` 呈现，浏览器自算收到字节 sha256 并解码；结论由执行人写入新候选证据：样帧路径、确认人、外观语义结论） | 0（零模型） | 0（只读既有离线 PNG，不评分、不回放） | 每候选 1 次（候选间网页呈现代码不变则不重做）；最多 3 | ≤ 15 min；0 B（不复制样图） | 推荐 Air 现有诊断原件中的候选预览 PNG（只读、不转证据）：`outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261007T234520Z/sessions/diag-loop2-234800/previews/` 与 `.../20261007T231337Z/sessions/diag-loop2-231911/previews/` 各取 1 张；**人眼执行人：用户或当轮发令角色（须由用户指定）** | 仅 127.0.0.1 / 本机 / 0 / 0 | 样图是否仍在盘、是否被视为可用作外观样本：未核（文件存在已只读确认） |
| `P1-ENG-LOOP-002:9bac8fd0:SUB:3`（可选，推荐先签） | 入口实跑诊断一次：在真实板与 Unity 上先验证 `play_ops` 的前台 SSH 监督（`-tt` 交互 bash、Ctrl-C 中断、同会话释放核对）、监听行识别、`/status` 身份与网页确认流，避免正式 B-main 首用即失败烧掉单元/服务额度（故障重启 0） | Air + Jetson Orin Nano 8GB Super（既有 `Host Jetson`） | 先由接受裁定诊断模式合同（IR-OPS-5），再按其执行；本工具现对诊断模式拒启 | 板端 GGUF 加载 1（服务启动 1，故障重启 0）；Unity 主机 YOLO 加载 ≤ 1 | 0 | 1 次（不是每候选） | 完整墙钟 ≤ 45 min（含 SSH、同步、冷加载、等待、Play 与收尾）；板端新增磁盘 ≤ 200 MB（诊断独立根）；Air 诊断目录 ≤ 250 MB | 本人 Play/停止、发送/跳过与候选选择 | SSH 主连接 ≤ 2；Unity Play ≤ 1；正式 ID 0（诊断标签，不进证据） | 诊断模式的独立目录/粗账/四类 STOP 在新工具中的落法未定（IR-OPS-5）；Air↔板链路现状 UNKNOWN |

其余维度（5060、云/外部模型 API、另列 GPU·h、下载、pip/安装/编译、模型或库传板、跨机代理复制、系统/SSH/沙箱设置修改、Unity 代码变更、新 scenario/run ID）：**0**，本清单不申请。正式 B-main 既有逐维度信封不增不减，本清单不借用其任何额度；N-1 全套 3/3 已用尽，不预签第 4 次。

## 3. 不在本清单内、后置到正式证据停点的项（照原合同）

- 正式 B-main 三单元、Play 3 + 环境性重试、收据、日志回传、正式归档评分（实现 ≤ 2 次）与 AC-18 独立复核重放（≤ 1 次）：仍按原签信封与 G1–G5，候选未经新范围独立通过前可执行值 0。
- 独立复核 `R1@OpsK1K2K3K4` 在一次性 worktree 的验证由复核角色自定，不在本清单。

## 4. 待裁定（实现角色对提案只读；交接受，未裁定前相应路径 fail-closed）

| 编号 | 问题与现状 | 实现的现行读法（fail-closed） | 需要的裁定 |
|---|---|---|---|
| IR-OPS-1 | G4「接受核清并明确放行」没有机读字段，`play_ops` 无法机械判定 | 要求发布引用上的同名提案含行首 `g4_release: <prep.stdout 的 sha256>`（可带列表记号/反引号）；缺即 `STOP S-PRECHECK g4_release_missing`，`receipt`/`play` 不开单元 | 采纳该行格式与写入位置，或给出替代机读形式 |
| IR-OPS-2 | 第 1.6 节「Unity 日志登记现场原流后再核」没有可机读的登记绑定 | 要求发布引用上的 `docs/unity-test-log.md` 含 `release_raw_sha256=<登记的第 1 节原流文件 sha256>`，且重跑的 1.1–1.4 段与登记文件逐行相同；缺即停 | 采纳或给替代；登记仍由当轮发令角色写 |
| IR-OPS-3 | O3/STOP:9 的 `S-REBUILD`「仅机械证明属于原允许闭集才可继续下一既定剧本」没有可机读的证明判据 | 一律按 UNKNOWN 停全部、交接受（不继续下一剧本） | 给出机读判据（例如哪些段事件/原因码组合算「A5 非主臂帧/发布段限制」），或确认保持一律停 |
| IR-OPS-4 | 原第 10 节环境性重试（Unity 未进 Play、运行时锁冲突；全局 ≤ 2、每剧本 ≤ 1）在新入口没有触发路径：W1 按钮闭集无重试按钮，AC-14 修订 1 不自动重试 | 环境性失败按停止处理、保留原流、单元收尾，交用户/接受；即不在同一单元内重试 | 是否允许在 `play` 之外以显式 CLI 参数（由本人发起、非自动）在同一单元内执行一次环境性重试；或确认在新入口下环境性重试不可用 |
| IR-OPS-5 | 诊断模式（诊断页「代理/脚本持有前台服务」「独立目录/粗账/四类 STOP」）在新工具中的启动、目录与粗账合同未定 | `--mode diagnostic` 一律拒启 | 若用户另签诊断（见 SUB:3），给出新工具的诊断模式合同（目录、粗维度记账、STOP 分流、服务启动块来源） |
| IR-OPS-6 | 原第 9 节「观察 ≥ 15 s」写在 confirm/reject 之后；新调度对 none/失败（`NO_CANDIDATE`）、无选择到截止（`NO_DECISION`）与跳过（`SKIPPED_NOT_IN_VIEW`）不再等待观察窗而直接进入下一步待本人发送/跳过 | 如左；观察/跟随计时只在 confirm/reject 受理后开始；锚点为选择回执的会话写盘时刻，红车跟随从其后首次 TRACKING 状态事件起（未进入则从选择时刻起并记未验证） | 确认该读法，或规定这些分支也须等待原观察时长 |

## 5. 稳定候选判断

稳定条件②（停点全套，SUB:1）与 AC-11 修订 1 的人眼保真（SUB:2）均未在本信封内完成，故**本轮不交稳定候选、不写 `-OpsK1K2K3K4-handoff.md`、不交 `C6@OpsK1K2K3K4`**；进度、逐 AC 证据与缺口见 `docs/evidence/P1-ENG-LOOP-002-ops-progress.md`。
