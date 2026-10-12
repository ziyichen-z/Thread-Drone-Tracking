# 快层配合方案调研：三份子代理提示词（2026-09-28，接口 A 已定）

每份提示词 = 【共用背景】+【共用硬性约束】+ 各自的【任务】。直接整段复制给 Opus 即可。

---

## 共用背景

- 仓库：~/TetheredDroneTracking，系留无人机（缆长上限 35 m）追踪地面车辆的研究项目：Unity 6000.4.1f1 仿真 + Python 外部控制器。Python 与 Unity 之间是文件桥（runtime/：frames/latest.json 帧包原子发布、tracking_observation.json 按 frame_id 绑定、body_command.json、gimbal_command.json、metrics.json），设计预算 5 Hz。相机帧 640×480。
- 双层架构：慢层 VLM（小模型，Qwen3-VL-2B 级，已做过一次 SFT，工作项 P1-ENG-SFT-002）用受限语言指令指定目标，输出该帧上的一个框；快层负责逐帧跟踪并驱动云台/机身。用户 2026-09-28 已定接口 A：VLM 输出「框 + 该框所在的 frame_id」，不改成让 VLM 选候选 ID。VLM 单次查询在桌面 GPU 上 p50 约 1.4–1.7 s，框到手时已经是旧帧的。
- 用户对快层任务的重申（要点）：(1) 保持居中追踪，最基础；(2) 重新指定目标时能完成目标迁移并跟上新目标，新目标肯定不在画面中间，需要算法以及无人机变向移动，进阶；(3) 最后若可行再考虑嵌入式 Jetson 部署：硬件算法 + VLM 能不能运行、硬件算法要做什么妥协。用户原话：「整个项目的难点不应该是保持追踪而是发现目标-跟上这个过程」。
- 现有快层资产：controller/trackers.py 的 TrackerPlugin 单目标接口（init(image, box_norm)->bool，update(image)->TrackerResult 单框）；已注册插件 csrt、nanotrack-v2（冻结、类别无关 SOT）、scripted，以及 P1-ENG-FAST-002 新增的 det-assoc-v1（controller/det_assoc_tracker.py：在域微调的 YOLO11n 两类检测器 vehicle/target + ultralytics 8.4.104 内置 BoT-SORT，内部对全画面所有车做多目标关联，但对外只暴露一个绑定 ID 的框，绑定轨迹被库移除后只报 lost、不改绑）。
- 已有离线读数（docs/evidence/P1-ENG-FAST-002-report.md）：在域检测器 H 域目标召回 S/M/L 0.879/0.987/0.731（@IoU0.3 时 L 0.927）、车辆 0.949/0.906/0.952、FP/帧 0.154；演示路线目标 ≥65 m 召回 0.904（零训练探针时仅 2.2%）；Mac 上 update p95 CPU 48 ms / MPS 32 ms；关联层 13 s 保持率 scout-1 0.815、H 合并 0.411；插件「一次绑定不改绑」口径在 scout-1 上 8 s 后绑定轨迹被移除、其后全部 MISS。
- 其他相关资产：controller/geolocate.py、world_estimate.py（世界系估计与视线落地点，M2a 口径，需显式地平面标定参数，禁止从真值推断）；controller/body_planner.py（P1-M3-BODY-001 阈值规划器）；controller/reanchor*.py（P1-DETECT-001 检测器再锚定载体，已暂停）；controller/language_loop.py、language_selector.py、language_bridge.py（P1-ENG-LOOP-001 受限语言闭环，现已暂停；其中重新播种走人工确认路径）；设计基线 docs/phase1-single-drone-design.md v0.3（§3 SOT+YOLOE 双通道、§3.5 世界系状态估计、§3.6 云台控制 LOS pointing + 像素残差修正、§4 机身规划、§5 丢失升级阶梯、§8 Orin Nano 8GB）。
- Unity 场景：93 辆静止布局车 + 1 辆运动目标车（演示目标为红立方体）；Unity 真值只允许进入 CoverageEvaluator，严禁进入控制器、感知输入或传感器元数据。离线数据：S3 帧目录 runtime/dist-data/frames_catalog/attempt-2（43,535 帧，逐对象 object_id、可见框、状态、深度），catalog-sim-times 可按仿真时间回放。
- 用户硬件：Jetson Orin Nano 8GB Developer Kit（Super 模式），JetPack 7.2 / L4T R39.2 / CUDA 13.2 / TensorRT 10.16，256 GB NVMe，PyTorch CUDA 已验证；另有 RTX 5060 Laptop 8 GB 与 Apple Silicon Mac（本机）。

## 共用硬性约束

- 只读仓库：不得修改、新增或删除仓库内任何文件，不做 git 操作，不安装任何包，不运行任何模型/训练/Unity/Play，不下载模型。
- 唯一允许写入的位置：/private/tmp/claude-501/-Users-zc5-TetheredDroneTracking/3c97521f-aca3-4514-867e-634223ec0493/scratchpad/research/<指定文件名>（目录不存在先 mkdir -p）。
- 全文中文（路径、命令、标识符、英文术语可保留）。每条事实标注来源等级：[仓库核实 file:line] / [公开资料 URL] / [估计]。不确定就写不确定，不要编造数字或 URL。
- 输出要服务于设计决策：优先写「会改变方案选择」的信息，少写教科书式泛泛内容。行数上限见各自任务。
- 完成后在最终回复里给出文件路径和 10 行以内的要点摘要。

---

## 任务 A1：仓库事实核查，为接口 A 下的快层设计打底

你是只读的仓库调研员。目标：把设计「目标指针 + 陈旧指定框回溯解析 + 转向捕获」所需的仓库事实全部核实清楚，产出事实表与集成点清单，供后续提案使用。

必读（按需扩展）：controller/trackers.py、track_loop.py、tracking_entry.py、language_loop.py、language_selector.py、language_bridge.py、det_assoc_tracker.py、geolocate.py、world_estimate.py、reanchor.py、reanchor_models.py、reanchor_runtime.py、body_planner.py、body_entry.py、gimbal_entry.py、gated_publisher.py、protocol.py、sensor_protocol.py；runtime/README.md；config/scenario.default.json；Assets/TetheredTracking/Scripts/GimbalCommandReceiver.cs、BodyCommandReceiver.cs、LoopTargetVehicle.cs（以及相机/云台参数所在的脚本或场景配置，自行定位）；docs/phase1-single-drone-design.md §2、§3（尤其 3.1、3.3、3.5、3.6）、§4、§5、§8；docs/proposals/P1-ENG-LOOP-001-language-select-closed-loop-integration.md（指定路径、K_pub/T_pub/T_catchup、SUSPECTED、「定局 ④」）；docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md（再锚定载体做什么、为何暂停）；docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md（阈值规划器）；docs/evidence/P1-ENG-FAST-002-report.md；docs/engineering-workflow.md（K1–K5 停点定义）。

逐项回答（每项给 file:line）：
- Q1 帧与时序：桥的实际帧率与 frame_id 分配；控制器是否保留帧或位姿历史；K_pub/T_pub/T_catchup 的含义与当前值；diag-loopb-6 的 catchup_stale 硬停止到底是什么。
- Q2 现在的指定路径：VLM 的框如何进入跟踪（哪个模块调 tracker.init，用的是哪一帧的图像）；VLM 看到的是哪个 frame_id，框到手时通常旧了多少；若新目标不在画面中央，现有代码会发生什么；SUSPECTED / 人工确认 / 重新播种路径的触发与解除；「定局 ④」逐字。
- Q3 插件接口改造：要支持 (a) 输出全部 track、(b) 按 frame_id 查历史、(c) designate(box, frame_id) 返回闭集结果 SWITCHED/NO_MATCH/AMBIGUOUS/TRACK_DIED、(d) 指针切换，需要改哪些文件的哪些函数；tracking_observation.json schema 能否不变；按 engineering-workflow 这会触发 K1/K2/K3 中的哪些停点。
- Q4 云台控制：§3.6 LOS pointing + 像素残差修正是否已实现、在哪；gimbal_command.json 的语义（角度还是角速度、限幅、Unity 侧限速）；相机 FOV 与分辨率；控制器能否拿到「已下发的云台运动量」用于对 track 预测做自运动前馈补偿（ego-motion compensation）。
- Q5 机身规划：BODY-001 规划器的输入输出、阈值与缆长工作空间约束；给它一个远离中心的新目标时的行为与限制（速度、35 m）。
- Q6 世界系：geolocate.py / world_estimate.py 的视线落地点计算需要什么输入；能否为「旧帧 t0 上的框」算世界点（需要 t0 时刻相机位姿，位姿历史是否保留）。
- Q7 再锚定：reanchor*.py（DETECT-001）做什么、门控是什么、能否复用为「转向到位后的重捕」；暂停原因。
- Q8 场景与注入：能否在不动 VLM 的情况下脚本化注入一次「指定静止车 B」（用于第二层的 Unity 诊断）；93 辆静止车 + 1 辆运动车这一布局对第二层测试的可用性。
- Q9 离线实验资产：S3 逐帧 object_id/可见框/仿真时间；det-assoc-v1 内部 BoT-SORT 的 track 状态可否导出；SFT-002 在 609 行评估集上的逐行预测是否在磁盘上（查 docs/evidence/P1-ENG-SFT-002-eval-*.json 与 outputs/），若在给路径与字段；据此判断「零训练零 Play 的陈旧指定回溯解析实验」能否直接搭起来，缺什么。

输出文件：.../scratchpad/research/A1-repo-facts.md，≤400 行。结构：1) 事实表（编号、事实、file:line）；2) 三层任务各自的集成点（改哪里、动哪个停点）；3) 尚不存在的东西；4) 风险与未知。

---

## 任务 A2：外部成熟方案调研（慢层 VLM 出旧帧框，快层如何配合完成「保持居中」与「换目标迁移并跟上」）

你是技术调研员，使用 WebSearch/WebFetch 查公开资料。可以只读仓库里的 docs/phase1-single-drone-design.md §3、§3.6、§4、§5 与 controller/trackers.py 以理解约束，不要读更多。

要回答的主题（每个主题：是什么、成熟度[库/论文/产品]、对本项目 5 Hz 文件桥 Unity 仿真与后续 Jetson 的适配性、采用/不采用建议、URL）：
- T1 慢感知与快跟踪的异步融合：按时间戳回溯关联（late association / out-of-sequence measurement）在跟踪与机器人栈里的标准做法；「旧帧上的框 → 当前活 track」的标准解析流程、匹配阈值与容忍延迟的量级；自动驾驶/ROS/无人机栈的公开实践。
- T2 检测 + 多目标关联作为底座、被跟目标只是一个指针：ultralytics track、BoxMOT（ByteTrack/BoT-SORT/OC-SORT/StrongSORT/DeepOCSORT 等）对大幅相机运动的鲁棒性比较；GMC 选项；用 IMU/云台角速度做相机自运动补偿的 UAV 跟踪方法（论文/实现）；5 Hz 与 15–30 Hz 下 track_buffer、match 阈值的经验取值。
- T3 类别无关 SOT 兜底：在按已知相机运动平移过的旧框上初始化 SOT（NanoTrack/HiT/MixFormer 轻量版/SAM 2 视频从旧帧提示向前传播）是否可行、误差容忍；各自在桌面与 Jetson 上的速率量级。
- T4 捕获与转向：云台 + 机身的图像视觉伺服（IBVS）、look-then-move 与连续伺服、限速转向使逐帧位移可关联、经世界点的 ROI 指向（MAVLink DO_SET_ROI 类）、转向到位后的重捕门控；DJI ActiveTrack / Skydio / PX4 与 ArduPilot follow 模式在「换目标」上的公开做法（仅公开资料）。
- T5 新目标远且小时：先转云台再检测、粗定位后裁剪放大再检测（coarse-to-fine）、切片推理（SAHI）等做法在无人机上的标准实践与代价。
- T6 失败语义：显式结果闭集（无匹配/歧义/轨迹已死）与操作者确认的通行做法。
- T7 「发现目标→跟上」的指标：文献中的 time-to-acquire、捕获成功率按偏角/距离分桶、ID 一致性等定义与常见坑。

输出文件：.../scratchpad/research/A2-external-survey.md，≤400 行。结尾给一个「推荐组合」：在接口 A 下，第一层与第二层各用什么件、为什么、最大的不确定点是什么。所有外部数字必须带 URL；查不到就写「未查到」。

---

## 任务 A3：Jetson Orin Nano 8GB（Super）上快层 + 小 VLM 的部署可行性与妥协清单

你是嵌入式部署调研员，使用 WebSearch/WebFetch 查公开资料；可只读仓库 docs/phase1-single-drone-design.md §8。不要在任何机器上运行东西。

板子事实（用户已核实）：Jetson Orin Nano 8GB Developer Kit，Super 模式；JetPack 7.2 / L4T R39.2 / CUDA 13.2 / TensorRT 10.16；256 GB NVMe；PyTorch CUDA 已验证。注意 JetPack 7 很新，很多生态（jetson-containers、llama.cpp、MLC、TensorRT-LLM、vLLM、ultralytics 的 Jetson 指南）可能尚未适配 CUDA 13 / R39，必须核查版本支持状态并标注。

要回答：
- J1 检测器：YOLO11n（640 输入）在 Orin Nano Super 上 TensorRT FP16/INT8 的公开时延与内存（ultralytics 官方 Jetson 基准、NVIDIA 资料、社区实测），DLA 是否可用；ByteTrack/BoT-SORT（含 GMC 稀疏光流）在 Orin 的 ARM CPU 上每帧成本量级；去掉 GMC 改用云台角速度补偿的可行性。
- J2 小 VLM：Qwen3-VL-2B / 4B、Qwen2.5-VL-3B 在 Orin Nano 8GB 上的公开实测：运行时选项（llama.cpp CUDA、MLC、TensorRT-LLM 对 VL 的 Jetson 支持、vLLM/jetson-containers、NVIDIA Jetson AI Lab 的 VLM 基准如 VILA/NanoVLM），INT4/INT8 权重 + 视觉编码器 + KV 的内存占用，单张 640×480 图的 prefill 时间（这才是单次指定查询的真实时延，比 tok/s 更重要），tok/s；已知公开数字：Orin Nano Super 上小模型 INT4 约 38–60 tok/s（需核实来源）。
- J3 共驻预算：8 GB 统一内存：OS + 桌面 + 检测器 TRT + VLM 的加总；2B 与 4B 各自能否与检测器共驻；VLM 只在指定时唤醒 vs 常驻的取舍；换页/OOM 风险。
- J4 妥协清单：INT8 检测器、降帧率、缩 imgsz、去 GMC、VLM 降输入分辨率（min_pixels）以缩 prefill、VLM 放地面站经 Tailscale 远程而板上只跑快层（往返时延预算）、或只在板上跑快层 + 远程 VLM 的混合方案；每项妥协对第一层/第二层任务的影响。
- J5 最小实测协议：若用户之后决定上板，先测什么、顺序如何、每步的通过标准（只写协议，不执行）。已知用户桌面有一个 jetson-smoke-pack（smoke 32 行 + 冻结代码 + bf16/llama.cpp 脚本）的既有思路，可参考但不必依赖。

输出文件：.../scratchpad/research/A3-jetson-feasibility.md，≤300 行。含一张可行性矩阵（组件 × 运行时 × JetPack 7 支持状态 × 时延 × 内存 × 来源等级），每个数字带 URL 并标 [公开实测]/[厂商标称]/[估计]；明确列出「查不到/未适配」的项。
