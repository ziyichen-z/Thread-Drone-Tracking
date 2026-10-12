# A2 外部成熟方案调研：慢层 VLM 出「旧帧框」时，快层如何配合「保持居中」与「换目标迁移并跟上」

- 日期 2026-09-28。性质：只读外部调研（未改仓库、未运行任何模型/Unity/训练）；仓库内只读了设计文档 §3（含 §3.6）、§4、§5 与 `controller/trackers.py`。
- 来源标注：`[公开资料 URL]` = 可点开核对的公开网页/论文/代码；`[估计]` = 本文推算或判断（关键推导见附录 A）；`[项目背景]` = 任务说明给定的项目读数；`[设计 §x]` = `docs/phase1-single-drone-design.md` 对应节。查不到写「未查到」。
- 术语：「旧帧框」= VLM 返回的 (box_k, frame_id=k)，到达时已是 t_k + 约 1.4–1.7 s（桌面 GPU p50）[项目背景]；「指针」= 快层内部「当前被跟目标 = 某条轨迹 ID」的引用。

## 0. 结论先行（按「会不会改变方案选择」排序）

1. 成熟系统把「旧帧上的指定」接到「当前活目标」上有三种标准做法：①**同帧历史匹配**（在按帧保存的全体轨迹历史里、于帧 k 上匹配旧框得到轨迹 ID，即 OOSM/回溯关联）；②**旧帧起跟 + 缓存帧回放追平**（Sightline Precision Acquisition、SAM 2 指定帧传播、robot_localization 回滚重放）；③**世界点线索 + 转向—搜索—锁定**（slew-to-cue、MAVLink ROI）。三者互补，优先级宜为 ①→②→③（见 §2、§4、§5）[估计]。
2. 做法①要求快层对画面内**所有车**持续维护轨迹。det-assoc-v1 内部的 BoT-SORT 已在做全画面关联 [项目背景]，缺的只是「按 frame_id 的全轨迹历史可查」和「可改绑的指针语义」——改动最小、收益最大 [估计]。
3. 开源飞控生态的图像跟踪命令（MAVLink `CAMERA_TRACK_POINT/RECTANGLE`）参数只有归一化坐标，未见帧时间戳 [公开资料 https://ardupilot.org/dev/docs/mavlink-camera.html]；专业云台跟踪器 Sightline 则用 MISB 时间戳在历史帧上起跟再追平 [公开资料 https://knowledge.sightlineintelligence.com/wp-content/uploads/EAN-Target-Tracking.pdf]。接口 A（框 + frame_id）属于后者这一更严谨的类别，方向正确 [估计]。
4. UAV 强自运动数据上，CMC 让 IDF1 提升 3.8–7.7、IDSW 约减半 [公开资料 https://arxiv.org/html/2603.05970]，原版不含 CMC 的 ByteTrack/OC-SORT 比 BoT-SORT/Deep OC-SORT 低约 6–9 HOTA [估计：由同文表格相减]；而 5 Hz 下 IoU 关联对相机自运动更敏感：按 ultralytics 默认门限折算，补偿后残余位移须 ≲0.43–0.67 个框宽/帧；在 60° 水平视场假设下，未补偿时云台只能以约 4–17°/s 转动而不断关联。要在转向中保住指针，必须做自运动补偿，且宜直接用云台/机身姿态（传感器口径）算单应；ultralytics 的 BoT-SORT 没有外部 warp 输入口，需自接 [估计，附录 A1–A2]。
5. 「把旧框按相机运动平移后在当前帧初始化 SOT」对运动目标基本不可行：1.7 s 内 2–8 m/s 的车走 3.4–13.6 m，50 m 处约 0.75–3 个车长框，超出 NanoTrack 类跟踪器的搜索与惩罚窗；应改为「在帧 k 上初始化 + 回放缓存帧」[估计，附录 A3]。
6. 远小目标的瓶颈更可能在慢层：Qwen3-VL 每个视觉 token 覆盖 32×32 px [公开资料 https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct/raw/main/config.json]，640×480 全图约 300 token，65 m 处车宽约 15 px（约半个 token）。远目标要么在慢层内部裁剪放大（坐标仍回写到帧 k，符合接口 A），要么靠转云台/变焦拉近，要么显式报告「过远」[估计，附录 A4]。
7. 失败语义的行业通行做法是**有限闭集 + 分原因 + 低置信时请人工确认**（DJI ActiveTrack、MAVLink 状态与结果枚举）；SOT 本身（OpenCV TrackerNano）的 `update()` 恒返回成功，不能充当失败信号（§7）[公开资料 https://developer.dji.com/api-reference/android-api/Components/Missions/DJIActiveTrackTrackingState.html] [公开资料 https://raw.githubusercontent.com/opencv/opencv/4.x/modules/video/src/tracking/tracker_nano.cpp]。
8. 公开基准没有现成的「换目标捕获」指标，需组合 VOT-LT 再检测实验、主动跟踪 SR/TR/EL、IDF1/HOTA 与带延迟的流式评测自行定义；最大的坑是离线评测忽略延迟（PVT++ 报告在线评测下最多约 70% 的性能下降 [公开资料 https://ar5iv.labs.arxiv.org/html/2211.11629]）和只对成功样本统计时间（§8）[估计]。

## 1. 项目约束速览（判断适配性用）

- 文件桥 5 Hz，帧包原子发布、观测按 frame_id 绑定；帧 640×480；接口 A 已定；VLM p50 1.4–1.7 s [项目背景]。
- 快层插件单目标接口 `init(image, box_norm)->bool`、`update(image)->TrackerResult`（失败为 `ok=False` + `reason`）[仓库 controller/trackers.py]；det-assoc-v1 对外单框、一次绑定不改绑，演示路线 8 s 后绑定轨迹被移除、其后全 MISS；关联层 13 s 保持率演示 0.815、留出 0.411；Mac update p95 CPU 48 ms / MPS 32 ms [项目背景]。
- 设计：冲突时不单帧重播种，需 N-of-M + 运动一致 + 身份裕度 [设计 §3.3]；LOS pointing + 像素残差、45° 限位与限速、估计传播与云台角速率 50 Hz，图像回路 5 Hz 起步、20 Hz 为已登记运行点 [设计 §3.6]；机身 ≤4 m/s、高度 8–32 m、缆长 ≤35 m [设计 §4.1]；L1 惯性滑行（云台跟随纯预测）[设计 §5]；运动目标速度档 D1 2.0 m/s、D2 8.0 m/s（合成速度压力档）[设计 §3.6 RATE-003]。
- 红线：Unity 真值只进 evaluator [项目背景]。若用姿态做自运动补偿，须确认帧包元数据中已有与采集时刻对齐、按传感器口径（带噪声/延迟）提供的云台/机身姿态，而非真值直通——本文未核实 [估计]。

## 2. T1 慢感知与快跟踪的异步融合（晚到关联 / OOSM）

### 2.1 是什么与成熟度
- **OOSM 理论（论文，成熟）**：多传感器系统中量测晚到需做「负时间更新」；Bar-Shalom 2002 给出精确解并与两种次优算法在含 GMTI 雷达的例子上比较 [公开资料 https://ieeexplore.ieee.org/iel5/7/22279/01039398.pdf]。
- **缓存—回滚—重放（库，成熟）**：robot_localization 的 `smooth_lagged_data` 收到滞后量测时回到其前状态再处理到当前，`history_length`（秒）须不小于滞后 [公开资料 https://github.com/cra-ros-pkg/robot_localization/blob/ros2/doc/state_estimation_nodes.rst]；赛车多目标跟踪栈用有序表 B_PSM 存历史状态/量测，OOSM 到来即回滚到其前快照并按序重处理 [公开资料 https://arxiv.org/html/2505.20043v2]。
- **按时间回溯坐标（库，成熟）**：tf2「时间旅行」以（目标帧, 目标时刻, 源帧, 源时刻, 固定帧）把过去时刻的数据经固定世界帧变换到现在 [公开资料 https://docs.ros.org/en/humble/Tutorials/Intermediate/Tf2/Time-Travel-With-Tf2-Cpp.html]。本项目对应：旧框底中心 × 帧 k 的相机位姿 × 地平面 → 世界点 [估计]。
- **多路不同延迟输入（自动驾驶栈，成熟）**：Autoware multi_object_tracker 支持最多 12 路检测输入，每路声明是否可信存在概率/尺寸/类别/朝向，缓存里程计处理乱序，输出延迟补偿分 none/publish_delay/odometry/full 四档 [公开资料 https://autowarefoundation.github.io/autoware_universe/main/perception/autoware_multi_object_tracker/]。可借鉴为：VLM 是一路「可信身份、不可信框紧致度」的慢输入 [估计]。
- **隔帧检测 + 视觉跟踪补帧（NVIDIA 产品栈，含 Jetson，成熟）**：DeepStream nvtracker 在检测器 `interval>0` 时由 NvDCF 在无检测帧继续跟踪；试用期（probationAge 默认 5 帧）内的输出作为 past-frame data 暂存、确认后补报 [公开资料 https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvtracker.html]。
- **云台跟踪产品（产品，成熟）**：Sightline 的 Precision Acquisition 保存最长 20 s 历史帧，操作者在过去帧（按 MISB Precision Time Stamp 定位）上起跟，系统「跟过排队帧直到追平当前」再正常跟踪；其文档把「用户看到目标到命令抵达跟踪器之间目标已移动」列为起跟框落在边缘、随后跟错的典型原因（Case 1）；Detection Track Cueing 允许在已有检测轨迹 nearVal 半径内（示例 200 px）点击即把该轨迹设为主跟踪 [公开资料 https://knowledge.sightlineintelligence.com/wp-content/uploads/EAN-Target-Tracking.pdf]。
- **双系统/VLM 先例（研究与产品）**：Figure Helix 的 S2（VLM）7–9 Hz、S1 200 Hz，训练时把两者输入的时间偏移校准为部署推理延迟差 [公开资料 https://www.figure.ai/news/helix]；DualVLN（ICLR 2026）慢系统给像素目标、快系统异步执行 [公开资料 https://openreview.net/forum?id=GK4rznYwhn]；无人机 CloudTrack：云端 Grounding DINO + VLM 核验，机载 OpenCV nano 跟踪（Orin NX 66 FPS），论文未讨论云端结果与当前帧的时差，重初始化选「位置与尺寸最接近上一框」的检测 [公开资料 https://arxiv.org/html/2409.16111]。
- **流式评测（研究）**：Li 等指出算法算完一帧时世界已变，「异步跟踪 + 前向预测」是流式感知的自然解 [公开资料 https://arxiv.org/abs/2005.10420]。

### 2.2 「旧帧框 → 当前活轨迹」的标准解析流程（据上述各家整理）
1. 快层对每个已处理帧 k 记录 `{track_id: box, score, cls, state}` 环形历史（与 DeepStream past-frame、Sightline 历史帧、B_PSM 同构）[估计]。
2. VLM 返回 (box_k, k)：k 不在历史中（过旧或该帧未被快层处理）→ `FRAME_NOT_IN_HISTORY`，拒绝并重查 [估计]。
3. 在**同一帧 k** 上算 box_k 与各轨迹框的 IoU——同帧比较不含运动误差，门限按「是否同一物体」取：CLEAR MOT 判同一目标用 IoU 0.5 [公开资料 https://ar5iv.labs.arxiv.org/html/1603.00831]；另设次佳裕度（如 best−second ≥ 0.2）防歧义；VLM 框偏松/amodal 时加「轨迹框中心落在 box_k 内」备用判据；τ 与裕度用 VLM 离线评估集的「VLM 框 vs 真值框」IoU 分布标定 [估计]。
4. 命中轨迹现仍存活 → `BOUND`（指针改绑）；命中轨迹已被移除 → `TRACK_ENDED`（转 §5 世界点搜索）；无轨迹过门 → `NO_TRACK_AT_K`（转 §4 回放）；多条过门 → `AMBIGUOUS`（转人工确认或再问 VLM）[估计]。
5. 改绑遵守 §3.3 门控：解析结果是「身份证据」，不单帧覆盖正在跟踪的框 [设计 §3.3] [估计]。
- **可容忍延迟的量级**：由历史长度与轨迹 ID 连续性决定，与目标位移无关。Sightline 历史最长 20 s [公开资料 同上 Sightline]；robot_localization 要求历史 ≥ 滞后 [公开资料 同上]。以 13 s 保持率按常数风险粗算，1.7 s 内指针不断的概率约 0.97（演示）/ 0.89（留出），3 s 约 0.95 / 0.81 [估计，附录 A5]。
- **适配性**：文件桥已按 frame_id 绑定观测 [项目背景]，历史缓冲天然贴合；每帧几十条轨迹 × 数个字段，内存与算力可忽略，Jetson 同样 [估计]。实机上帧与姿态的时间同步是前提（Sightline 用 MISB 时间戳、Autoware 缓存里程计即为此）[估计]。
- **建议：采用**，作为第二层解析器主路径；调参与评测按部署延迟分布（p50/p95）注入延迟（Helix 的训练做法）[估计]。

## 3. T2 检测 + 多目标关联作底座，被跟目标只是指针

### 3.1 现成库事实（与大相机运动相关）
| 件 | 事实 | 来源 |
|---|---|---|
| ultralytics 8.4.104 BoT-SORT | 默认 track_high 0.25 / low 0.1 / new 0.25，track_buffer 30，match_thresh 0.8，fuse_score True，gmc sparseOptFlow，with_reid False | [公开资料 https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.104/ultralytics/cfg/trackers/botsort.yaml] |
| 同上 | `max_frames_lost = args.track_buffer`，**不按帧率换算**；二次关联 IoU-only 门 0.5，未确认轨迹门 0.7；丢失轨迹重激活保留原 ID；关联不看类别，`cls` 随匹配检测直接覆盖 | [公开资料 https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.104/ultralytics/trackers/byte_tracker.py] |
| 同上 | `fuse_score`：相似度 = IoU × 检测分，cost = 1 − 相似度，cost ≤ match_thresh 才可匹配 | [公开资料 https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.104/ultralytics/trackers/utils/matching.py] |
| 同上 | GMC：sparseOptFlow（maxCorners 1000，降采样 2）+ `estimateAffinePartial2D`/RANSAC，输出 2×3，作用于 strack_pool 与 unconfirmed；`BOTSORT.__init__(args)` 只按方法名建 GMC，**无外部 warp 输入** | [公开资料 https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.104/ultralytics/trackers/utils/gmc.py] [公开资料 https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.104/ultralytics/trackers/bot_sort.py] |
| OpenCV | `estimateAffinePartial2D` 只有 4 自由度（旋转、等比缩放、平移），表达不了大角度摇头/俯仰的透视成分 | [公开资料 https://docs.opencv.org/4.13.0/d9/d0c/group__calib3d.html] |
| BoT-SORT 论文 | CMC 仿 OpenCV videostab（关键点 + 稀疏光流 + RANSAC 仿射）；MOT17 val 加 CMC：MOTA +0.64、IDF1 +1.62、HOTA +0.94；GMC 耗时相对检测可忽略；丢失轨迹留 30 帧 | [公开资料 https://ar5iv.labs.arxiv.org/html/2206.14651] |
| ByteTrack 论文 | 高分阈 0.6；IoU<0.2 拒绝匹配；丢失轨迹留 30 帧；低分框用于找回遮挡目标 | [公开资料 https://ar5iv.labs.arxiv.org/html/2110.06864] |
| roboflow trackers | Apache-2.0；SORT/ByteTrack/OC-SORT/BoT-SORT/C-BIoU/McByte；调参后 MOT17 HOTA：BoT-SORT 63.8、OC-SORT 62.0、ByteTrack 60.5，SportsMOT：74.1/74.0/73.3；文档建议强相机运动（含无人机视频）用 BoT-SORT | [公开资料 https://github.com/roboflow/trackers] [公开资料 https://trackers.roboflow.com/latest/trackers/comparison/] |
| BoxMOT | BoTSORT/ByteTrack/OCSort/StrongSORT/DeepOCSORT/BoostTrack/HybridSORT/SFSort/OccluBoost；AGPL-3.0；可选 C++ 后端；README 报 MOT17 消融、SportsMOT 验证与 MMOT（无人机多光谱、OBB）测试结果，本文未取到其逐跟踪器 MMOT 数字 | [公开资料 https://github.com/mikel-brostrom/boxmot] [公开资料 https://arxiv.org/abs/2510.12565] |
| Norfair | BSD-3；`Tracker.update(detections, coord_transformations=...)` 可传外部坐标变换（平移/单应） | [公开资料 https://tryolabs.github.io/norfair/2.2/reference/camera_motion/] [公开资料 https://github.com/tryolabs/norfair] |
- UAV 强自运动下的同检测器对照（DynUAV，2026：DJI Mini 4 Pro 于 80–120 m 航拍、1080p，统一 YOLO11 检测器），HOTA/IDF1/IDSW：ByteTrack 53.59/60.78/3136，OC-SORT 51.73/58.12/1660，BoT-SORT 59.86/68.81/1274，StrongSORT 60.87/71.21/1394，Deep OC-SORT 61.09/72.25/567，TrackTrack 62.74/74.81/256；CMC 消融：AdapTrack IDF1 65.53→73.26、IDSW 1123→583，TrackTrack IDF1 71.04→74.81、IDSW 439→256，作者结论是 CMC 主要提升关联而非检测 [公开资料 https://arxiv.org/html/2603.05970]。据此：原版不含 CMC 的 ByteTrack/OC-SORT 比 BoT-SORT 低 6.3–8.1 HOTA；CMC 在 UAV 上的收益（IDF1 +3.8～+7.7、IDSW 约减半）远大于 MOT17 上的 +1.62 [估计：由上列数字相减]。该数据集帧率：未查到。

### 3.2 UAV 大相机运动与姿态补偿
- 问题公认：UAV 视频的不规则相机运动与三维视角变化使常规 MOT 表现差（UAVMOT, CVPR 2022）[公开资料 https://openaccess.thecvf.com/content/CVPR2022/papers/Liu_Multi-Object_Tracking_Meets_Moving_UAV_CVPR_2022_paper.pdf]；HomView-MOT 用快速单应把不同帧的框映射到公共视平面再算 IoU [公开资料 https://arxiv.org/abs/2403.10830]；JitTrack（2026）专攻敏捷无人机视角抖动导致的跨帧大位移 [公开资料 https://arxiv.org/abs/2608.10485]。
- 用相机参数与地平面而非逐帧配准：UCMCTrack（AAAI 2024）在地平面上做卡尔曼、以 Mapped Mahalanobis Distance 替代 IoU，并对整段视频用统一补偿参数 [公开资料 https://arxiv.org/abs/2312.08952]。
- 用惯性/姿态：陀螺给出的帧间旋转作 KLT 初始 warp，对快速自转更稳（Hwangbo/Kim/Kanade，IROS 2009；IJRR 2011 含 GPU 实现）[公开资料 http://www.cs.cmu.edu/~myung/publication/iros09.pdf] [公开资料 https://journals.sagepub.com/doi/abs/10.1177/0278364911416391]；Sea You Later 用 GPS/高度/相机朝向元数据把短轨迹并成长轨迹（SeaDronesSee 测试 HOTA 69.5、IDF1 85.9）[公开资料 https://arxiv.org/abs/2311.03561]；ArduPilot 视觉跟随提案：伴飞计算机给像素位置与表观尺寸，飞控用机位、云台姿态、视场（含变焦）估计地理位置再喂 Follow 模式（issue 仍开放）[公开资料 https://github.com/ArduPilot/ardupilot/issues/23349]。
- 几何依据：平面诱导单应 H = R − t nᵀ/d（归一化坐标）[公开资料 https://en.wikipedia.org/wiki/Homography_(computer_vision)]；纯转动（t=0）时像素域为 K R K⁻¹、与景深无关 → 云台转动可按姿态精确补偿，机身平移对地面目标可用地平面单应补偿 [估计：由前式代入]。
- 成熟度判断：图像法 GMC 已进主流库；姿态法在工程系统常见，但未查到 UAV-MOT 上「姿态法 vs 图像法」的公开定量对比（公开 UAV MOT 基准多不带同步遥测）[估计]。

### 3.3 帧率与参数经验值
- 低帧率显著削弱关联（FAPS, IJCV；ColTrack, ICCV 2023；APPTracker）[公开资料 https://arxiv.org/abs/2209.11404] [公开资料 https://arxiv.org/abs/2308.05911] [公开资料 https://infzhou.github.io/appTracker/index.html]；OC-SORT 指出线性运动近似依赖高帧率 [公开资料 https://ar5iv.labs.arxiv.org/html/2203.14360]。
- 丢失轨迹寿命的行业取值换算成时间多在 1–1.5 s：ByteTrack/BoT-SORT 30 帧、Sightline Max Missed Frames 默认 45（其文档注明为 30 Hz 下 1.5 s）、DeepStream maxShadowTrackingAge 默认 38 帧 [公开资料 上列 ByteTrack/BoT-SORT/Sightline/DeepStream URL]；按 30 fps 折算为本文推断 [估计]。
- ultralytics 的 buffer 不随帧率缩放 → 5 Hz 下默认 30 帧 = 6 s；其 yaml 注释亦提示 buffer 越大 ID 互换风险越高 [公开资料 botsort.yaml URL 同上] [估计：换算]。建议按秒定义：5 Hz 取 5–15 帧（1–3 s）起调；15–30 Hz 下默认 30 帧（1–2 s）即常规区间 [估计]。
- 门限的位移容限：等大框沿运动方向错开 d 时 IoU=(w−d)/(w+d)；match_thresh 0.8 + fuse_score 意味着 IoU×score ≥ 0.2 → 检测分 1.0 时 d ≤ 0.67w，0.5 时 d ≤ 0.43w [估计，附录 A1]。15–30 Hz 下帧间位移只有 5 Hz 的 1/3–1/6，默认值通常够用；5 Hz 下须先补偿再比 IoU，或改用地面距离门 [估计]。

### 3.4 适配性与建议
- 5 Hz 文件桥：底座可用，关键在自运动补偿与按秒定参 [估计]。Jetson：YOLO26n 在 Orin Nano Super 上 TensorRT FP16 4.57 ms/张（ultralytics 8.4.33、JetPack 6.1）[公开资料 https://docs.ultralytics.com/guides/nvidia-jetson/]，YOLO11n 应同量级（未查到同板同版本数字）[估计]；DeepStream NvDCF/NvSORT 可作 Jetson 原生替代 [公开资料 DeepStream URL 同上] [估计]。
- **建议：采用** det-assoc-v1 内的 BoT-SORT 作底座，不换库；GMC 改为「姿态单应为主、图像光流交叉校验」（替换 `gmc.apply` 的返回或在关联前把预测框映射到当前帧）；对外暴露全轨迹历史；ReID 可选（`with_reid` + `model: auto` 复用检测器特征）[公开资料 https://docs.ultralytics.com/modes/track/] [估计]。若自接姿态 CMC 后 IDSW 仍高，首个替换候选是 Deep OC-SORT（CMC + 自适应 ReID；DynUAV 上 IDSW 567 对 BoT-SORT 1274，BoxMOT 有实现、AGPL-3.0）[公开资料 https://arxiv.org/html/2603.05970] [公开资料 https://github.com/mikel-brostrom/boxmot]；地平面关联（UCMCTrack 式）作为留出域保持率仍低时的另一备选；纯 ByteTrack/OC-SORT 不宜作底座 [估计]。

## 4. T3 类别无关 SOT 兜底

- **在「按相机运动平移过的旧框」上于当前帧初始化：不建议。**
  - OpenCV TrackerNano（项目 nanotrack-v2 所用 API）：模板 127、搜索 255、context 0.5、余弦窗权重 0.455，搜索区边长约为带上下文模板的 2 倍（255/127）、偏离中心受罚；`update()` 恒返回 true [公开资料 https://raw.githubusercontent.com/opencv/opencv/4.x/modules/video/src/tracking/tracker_nano.cpp]。
  - 学界标准的初始化扰动测试（OTB SRE）只到目标尺寸 10% 的平移与 0.8–1.2 缩放 [公开资料 https://ar5iv.labs.arxiv.org/html/1609.06141]；Sightline 最佳实践是框包住整车并留约 10% 背景，偏到边缘就会跟边缘或背景 [公开资料 Sightline URL 同上]。
  - 相机自运动可按姿态补偿，但目标在延迟内的自身位移补不了（附录 A3：约 0.75–3 个车长框）[估计]。
- **在帧 k 上初始化 + 回放缓存帧追平：建议作兜底。**
  - 先例：Sightline Precision Acquisition（§2.1）；SAM 2 视频预测器支持 `add_new_points_or_box(frame_idx=…)` 与 `propagate_in_video(start_frame_idx, reverse)`，但 `init_state` 面向整段视频加载帧（离线形态），流式需社区改造（如 segment-anything-2-real-time，以首帧起算，质量未核实）[公开资料 https://raw.githubusercontent.com/facebookresearch/sam2/main/sam2/sam2_video_predictor.py] [公开资料 https://github.com/Gy920/segment-anything-2-real-time]。
  - 代价：5 Hz × 5 s ≈ 25 帧 × 0.92 MB ≈ 23 MB 帧缓存；每次回放 8–15 帧 [估计，附录 A4]。
- **速率量级（桌面 / 边缘）**

| 候选 | 桌面 | 边缘 | 来源 |
|---|---|---|---|
| NanoTrack v1/v2 | Apple M1 CPU >200 FPS | OpenCV nano：Orin NX 66 FPS、树莓派 4 约 29 FPS | [公开资料 https://github.com/HonglinChu/SiamTrackers/tree/master/NanoTrack] [公开资料 https://arxiv.org/html/2409.16111] |
| HiT | — | Jetson AGX（摘要未写全型号）61 fps；LaSOT AUC 64.6% | [公开资料 https://arxiv.org/abs/2308.06904] |
| LiteTrack | B9：2080Ti 171 fps | B4：Orin NX（ONNX）>100 fps | [公开资料 https://arxiv.org/abs/2309.09249] |
| MixFormerV2 | B：GPU 165 FPS、LaSOT AUC 70.6% | S：摘要只称「实时 CPU」，未给数 | [公开资料 https://arxiv.org/abs/2305.15896] |
| SAM 2.1 tiny/small/b+/large | A100：91.2/84.8/64.1/39.5 FPS | SAM2-base 于 Orin Nano 8GB（TensorRT FP16）4.4→6.3 FPS（Super 模式）；是否含视频记忆传播未查到 | [公开资料 https://github.com/facebookresearch/sam2] [公开资料 https://developer.nvidia.com/blog/nvidia-jetpack-6-2-brings-super-mode-to-nvidia-jetson-orin-nano-and-jetson-orin-nx-modules/] |
| EdgeTAM | — | iPhone 15 Pro Max 16 FPS | [公开资料 https://arxiv.org/abs/2501.07256] |

- 回放 15 帧耗时：NanoTrack 在 M1 <0.1 s、在 Orin NX 级约 0.23 s；SAM 2 在 Orin Nano 约 2.4 s，不宜在线 [估计，由上表速率]。
- **适配性**：回放只依赖帧缓存与现有插件接口（`init` 用帧 k 图像、`update` 逐帧喂缓存），5 Hz 文件桥下可离线完成、不占实时回路；Jetson 上 NanoTrack 量级足够 [估计]。
- **建议**：兜底用已冻结的 nanotrack-v2 做「帧 k 起跟 + 回放」，CSRT 保留对照；因 SOT 不给失败信号，回放结束后须被检测轨迹「收养」（N-of-M、与检测框 IoU 过门）才转 `BOUND`，否则报 `SOT_UNCONFIRMED`；SAM 2 维持离线参照（与设计 §3.4 表一致）；HiT/LiteTrack 仅在回放漂移成主因时再考虑 [估计]。

## 5. T4 捕获与转向

- **范式（论文，成熟）**：IBVS（误差在像平面）与 PBVS（估计目标位姿）[公开资料 https://faculty.cc.gatech.edu/~seth/ResPages/pdfs/ChaHut06.pdf]；早期视觉系统「先看后动」开环交替，「visual servoing」一词即为区分闭环 [公开资料 https://masters.donntu.ru/2012/etf/nikitin/library/article10.htm]。设计 §3.6 的「世界点前馈 + 像素残差小增益」属混合型，恰好适合迁移：先有世界点、后有像素 [设计 §3.6] [估计]。
- **经世界点指向（协议，成熟）**：MAVLink `DO_SET_ROI_LOCATION` 由云台管理器换算为姿态，`DO_SET_ROI_SYSID` 跟随另一系统，`DO_SET_ROI_NONE` 退回手动/中立 [公开资料 https://mavlink.io/en/services/gimbal_v2.html]；ArduPilot 在 GPS Point / SysID 模式下偏航轴强制为地球系 [公开资料 https://ardupilot.org/copter/docs/common-mount-targeting.html]。
- **图像内目标跟踪命令（协议）**：`MAV_CMD_CAMERA_TRACK_POINT/RECTANGLE` 取 0..1 归一化坐标，`STOP_TRACKING` 停止，状态经 `CAMERA_TRACKING_IMAGE_STATUS/GEO_STATUS` 回报 [公开资料 https://ardupilot.org/dev/docs/mavlink-camera.html] [公开资料 https://mavlink.io/en/services/camera.html]；参数中无帧时间戳，协议层不处理指定延迟 [估计]。
- **slew-to-cue（安防/军用产品，成熟）**：由线索地理位置定视线轴 A 与误差区 B，相机转向后沿 A 在 B 内扫描，找到即锁定自主跟踪，找不到则向外扩展扫描，并按目标尺寸定最佳变焦 [公开资料 https://patents.google.com/patent/US8929603B1/en] [公开资料 https://www.infinitioptics.com/glossary/slew-to-cue-auto-tracking]；主从相机需标定「主相机像素 ↔ PTZ 角」映射 [公开资料 https://pmc.ncbi.nlm.nih.gov/articles/PMC3960552/]。
- **产品行为**：DJI ActiveTrack 的 `ONLY_CAMERA_FOLLOWING` = 飞机悬停、用云台俯仰 + 机体偏航跟随 [公开资料 https://developer.dji.com/api-reference/android-api/Components/Missions/DJIActiveTrackMissionOperator.html]；DJI H30 Smart Track 锁定后自动转云台把目标置中并调焦距 [公开资料 https://www.heliguy.com/blogs/posts/dji-h30-vehicle-tracking/]；Sightline 跟踪器能跟住慢速变焦/旋转，快速变化需准确配准估计，大幅变焦跳变后可能需按估计位置/尺寸重新指定 [公开资料 Sightline URL 同上]；专业跟踪器以 30–60 Hz 运行（Sightline 称最高 60 Hz）[公开资料 https://sightlineintelligence.com/detection-tracking/]。
- **「换目标」的公开做法**：DJI 以拖框或点击识别到的主体图标选目标，丢失后悬停；跟车建议车辆慢速匀速 [公开资料 https://support.dji.com/help/content?customId=en-us03400006832&spaceId=34&re=US&lang=en&documentType=artical&paperDocType=paper] [公开资料 https://support.dji.com/help/content?customId=en-us03400006813&spaceId=34&re=US&lang=en&documentType=artical&paperDocType=paper]；Skydio X10 Shadow 对人/车保持视觉锁定并称有「预测性再捕获」（仅 release notes 摘要级）[公开资料 https://support.skydio.com/hc/en-us/articles/47694908030491-Skydio-X10-Cayley-v43-147-11-March-2026]；PX4 Follow Me 只跟随 `FOLLOW_TARGET` 位置消息、不含视觉 [公开资料 https://docs.px4.io/main/en/flight_modes_mc/follow_me.html]；ArduPilot Follow 按 `FOLL_SYSID`（0=首个）选目标，超出 `FOLL_DIST_MAX` 或 `FOLL_TIMEOUT` 内无消息即放弃并悬停，`FOLL_OPTIONS` bit0 让云台指向目标 [公开资料 https://ardupilot.org/copter/docs/follow-mode.html]。DJI/Skydio 换目标的内部算法：未查到。开源飞控的「换目标」= 重新下发目标 ID 或图像矩形，未见公开的延迟补偿/迁移算法 [估计]。
- **对本项目的做法**
  - 连续伺服（首选）：转向中快层继续跑检测 + 关联，补偿后残差不超门限即可保住指针；允许的云台角速率约 ω_max ≈ 帧率 × k·w_px /（每度像素数）/ ε，其中 k 为 0.43–0.67、ε 为补偿后残余比例（未补偿 ε=1）[估计，附录 A2]。
  - look-then-move（大角度/需机身动作）：所需转角接近 45° 限位或目标已出画时，按世界点转向或机身偏航/移动（设计 §4 P2），期间指针进入 coast（§5 L1），到位后在世界点投影附近做 N-of-M 确认（DeepStream probationAge 默认 5 帧可作量级参照）[公开资料 DeepStream URL 同上] [设计 §3.3/§5]。
  - 到位门控：云台角速率低于阈值且预测投影连续若干帧落在画面内才开门，避免残余位移与运动模糊造成误绑 [估计]。
- **适配性**：5 Hz 下连续伺服的角速率受上式约束；若需更快转向，可评估「捕获阶段临时提帧」（设计已登记 20 Hz 运行点，但跨帧率效应未测，须用户裁定）[设计 §3.6] [估计]。Jetson 无额外算力问题，实机关键是姿态与帧的时间对齐 [估计]。
- **建议：采用**「连续伺服为主、look-then-move 为辅」+ 到位门控；世界点来源优先取指针轨迹的当前框（经地平面），无轨迹时取帧 k 旧框经帧 k 位姿换算 [估计]。

## 6. T5 新目标远且小

- 切片推理 SAHI（库，成熟）：VisDrone/xView 上仅推理即令 FCOS/VFNet/TOOD 的 AP +6.8/+5.1/+5.3，加切片微调累计 +12.7/+13.4/+14.5 [公开资料 https://arxiv.org/abs/2202.06934]；代价随切片数增长，ROI 门控版在稀疏场景最高 6.90× 提速（COCO128 验证，非航拍）[公开资料 https://arxiv.org/html/2608.23923]。
- 粗到细（论文/产品）：ClusDet 先预测目标聚集区再尺度归一化裁剪检测，显著减少切片数 [公开资料 https://arxiv.org/abs/1904.08008]；产品侧为「先转云台置中再变焦」（DJI Smart Track 自动调焦距；slew-to-cue 专利按目标尺寸算最佳变焦）[公开资料 heliguy URL 同上] [公开资料 US8929603 URL 同上]。
- 像素下限：Johnson 判据下 50% 概率的探测/识别/辨认需跨关键尺寸 1.0/4/6.4 线对 [公开资料 https://en.wikipedia.org/wiki/Johnson's_criteria]，按 1 线对≈2 px 约为 2/8/13 px [估计]。
- 慢层分辨率：Qwen3-VL-2B 视觉 patch 16、空间合并 2 → 每 token 32×32 px [公开资料 https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct/raw/main/config.json]；MLLM 精度对被问对象尺寸很敏感，但注意力「知道看哪」，免训练裁剪可显著提升 [公开资料 https://arxiv.org/abs/2502.17422]。
- 本项目推算：640×480 → 300 token；60° HFOV 假设下 65 m 处车宽约 15 px、车长约 38 px（约 0.5–1.2 token）；320 切片、0.2 重叠时 SAHI = 6 切片 + 全图 ≈ 7 次推理，桌面按 MPS p95 32 ms 约 0.22 s，超 5 Hz 预算；Jetson 按 4.6 ms/次约 32 ms [估计，附录 A4；32 ms 为项目背景读数]。
- **适配性**：640×480 原生分辨率不大，检测器在 imgsz 640 已看到全部像素，切片只起「等效放大」作用；系留机身水平活动受 35 m 缆长约束 [设计 §4.1]，远目标难靠机身拉近，转云台置中/变焦更现实 [估计]。
- **建议**：检测器远目标召回已达 0.904（≥65 m，演示路线）[项目背景]，SAHI 优先级低，只在捕获阶段对预测区域事件触发；优先在慢层内部做「粗定位 → 裁剪放大再问」（坐标回写帧 k，仍是接口 A；代价是多一次 VLM 延迟）；对「过远/过小」显式报告；**是否允许相机变焦（Unity 相机 FOV 可调）**会显著改变方案，需用户裁定 [估计]。

## 7. T6 失败语义：显式闭集与操作者确认

- DJI ActiveTrack（产品 SDK，成熟）：目标状态闭集 `TRACKING_WITH_HIGH_CONFIDENCE / TRACKING_WITH_LOW_CONFIDENCE / WAITING_FOR_CONFIRMATION / CANNOT_CONFIRM / UNKNOWN`；不能确认原因闭集 `UNSTABLE_TARGET, TARGET_TOO_HIGH, BLOCKED_BY_OBSTACLE, GIMBAL_ATTITUDE_ERROR, TARGET_TOO_FAR, TARGET_TOO_CLOSE, AIRCRAFT_TOO_HIGH, AIRCRAFT_TOO_LOW, OBSTACLE_SENSOR_ERROR, UNKNOWN`（另有 NONE）；`targetRect` 归一化到 [0,1]；目标类型 HUMAN/CAR/VAN/BIKE/BOAT/UNKNOWN [公开资料 https://developer.dji.com/api-reference/android-api/Components/Missions/DJIActiveTrackTrackingState.html]；高置信直接进入跟随，否则 `WAITING_FOR_CONFIRMATION` 等用户 `acceptConfirmation`，框色区分状态 [公开资料 https://developer.dji.com/mobile-sdk/documentation/android-tutorials/P4MissionsDemo.html]。
- MAVLink（协议，成熟）：跟踪状态 `IDLE/ACTIVE/ERROR`、模式 `NONE/POINT/RECTANGLE` [公开资料 https://xmavlink-util.hexdocs.pm/Common.Types.html]；命令应答 `MAV_RESULT` 含 ACCEPTED、IN_PROGRESS（带 0–100 进度）、TEMPORARILY_REJECTED、FAILED、CANCELLED、COMMAND_UNSUPPORTED 等 [公开资料 https://mavlink.io/en/services/command.html]。
- 语言指定（论文）：GRES/GREC 把「无目标」「多目标」表达列为一等类别 [公开资料 https://arxiv.org/abs/2306.00968] [公开资料 https://arxiv.org/abs/2308.16182]；MLLM 因训练缺负样本常对不存在对象幻觉出框 [公开资料 https://arxiv.org/abs/2608.04698]；TrackVLA 的 EVT-Bench 专设「干扰」「歧义」子任务 [公开资料 https://arxiv.org/html/2505.23189]。
- 跟踪器（基准/产品）：VOT 长时协议要求输出置信度，低于阈值即视为报告「目标不在」，以 Pr/Re/F 评价 [公开资料 https://ar5iv.labs.arxiv.org/html/1906.08675]；Sightline 用遥测置信度最高位标记 coasting，并提醒不能靠硬编码置信阈值判断 [公开资料 Sightline URL 同上]；OpenCV TrackerNano `update()` 恒 true [公开资料 tracker_nano.cpp URL 同上]。
- **适配性**：闭集结果可直接作为观测文件/运行日志中的状态字段，与 frame_id 绑定；与 Jetson 无关 [估计]。
- **建议：采用**两个有限闭集（慢→快交接结果、捕获过程状态，见 §9 表），每个非成功结果带原因；只有「高置信 + 无歧义」自动执行，其余进操作者确认——与项目「重新播种走人工确认路径」一致 [项目背景] [估计]。

## 8. T7 「发现目标 → 跟上」的指标与常见坑

- 可借用的公开定义（成熟度：基准）：
  - VOT-LT 再检测实验：把目标反复移到新位置，统计「成功再检测所需帧数」，检验全图搜索能力 [公开资料 https://ar5iv.labs.arxiv.org/html/1906.08675]。
  - 主动跟踪：UnrealCV 的 EL（目标连续 50 步不在视野即提前结束）与 SR（跟满 500 步的比例）；DAT（24 个城市级场景、空对地）TSR 以 1500 步计，GC-VAT 仿真 TSR≈72% [公开资料 https://arxiv.org/html/2604.21453v1] [公开资料 https://arxiv.org/abs/2412.00744]；EVT-Bench：SR = 结束时朝向目标且距离 1–3 m，TR = 成功跟踪步数占比，CR = 因碰撞结束的比例 [公开资料 https://arxiv.org/html/2505.23189]。
  - 身份：IDF1（ID 精确率/召回率）[公开资料 https://arxiv.org/abs/1609.01775]；HOTA 平衡检测、关联与定位，并指出旧指标偏重其一 [公开资料 https://arxiv.org/abs/2009.07736]。
  - 延迟：流式评测把延迟计入 [公开资料 https://arxiv.org/abs/2005.10420]；PVT++ 报告在线（机载延迟）评测下部分跟踪器最多约 70% 的性能下降，其方法最多约 60% 提升（Jetson AGX Xavier）[公开资料 https://arxiv.org/abs/2211.11629] [公开资料 https://ar5iv.labs.arxiv.org/html/2211.11629]。
- 建议本项目自定义（均只在 evaluator 用真值）[估计]：
  - **捕获成功率**：指令发出后 T_max 内「指针绑定真目标，且目标中心距画面中心 < r 连续 N 帧」的试次比例；按指令时刻目标的**偏轴角**（视场内偏心 / 出视场但在 45° 限位内 / 需机身动作）与**斜距**（如 <35 / 35–65 / ≥65 m）分桶，另按「最近同类车像素距离」分干扰密度层。
  - **time-to-bind / time-to-center**：t_bound − t_cmd、t_centered − t_cmd，含 VLM 延迟；报告「T 内成功率曲线」或 Kaplan–Meier 中位数。
  - **误锁率**：绑定到非目标车的试次比例与误锁时长；捕获后按目标专属的绑定精确率/召回率（目标版 IDF1/TR）计。
  - **分段归因**：VLM 框@k 是否对 → 解析出的 ID 是否对 → 转向是否到位 → 捕获后是否丢失，逐段计数。
- 常见坑：离线评测忽略延迟（见 PVT++）；只对成功样本统计时间（右删失）；用全局 MOT 指标（所有车的 IDF1）代替「目标绑定」指标；「捕获」定义（IoU 还是中心误差、单帧还是连续 N 帧）事后才定；不按干扰/歧义分层（EVT-Bench 把两者作为独立难度轴）[公开资料 TrackVLA URL 同上]；每桶样本过少、未做同初始条件的配对比较 [估计]。
- **适配性**：Unity evaluator 已有真值通道，可实现上述指标；Jetson 实机无真值，只能靠人工标注或操作者确认计数 [估计]。

## 附录 A 关键估算推导（均为 [估计]）

- **A1 IoU 门**：等大框沿运动方向错开 d，IoU = (w−d)/(w+d)。ultralytics 首轮关联要求 IoU × score ≥ 1 − 0.8 = 0.2：score = 1 → d ≤ 2w/3 ≈ 0.67w；score = 0.5 → IoU ≥ 0.4 → d ≤ 3w/7 ≈ 0.43w。
- **A2 云台转速**：f = (W/2)/tan(HFOV/2)；W = 640、HFOV = 60°（假设值，需代入项目相机参数）→ f ≈ 554 px，约 9.7 px/°。50 m 处车宽 1.8 m ≈ 20 px、车长 4.5 m ≈ 50 px。按 0.43w 容限，未补偿每帧可转 0.9–2.2°（×5 Hz = 4.4–11°/s）；按 0.67w 为 1.4–3.4°/帧（6.9–17°/s）。补偿后残余为 ε 时上限约乘 1/ε。
- **A3 延迟内目标位移**：1.7 s × 2 / 8 m/s = 3.4 / 13.6 m；50 m 处约 11.1 px/m → 38 / 151 px，约为 0.75 / 3 个车长框（50 px）。
- **A4 慢层与缓存**：640/32 × 480/32 = 20 × 15 = 300 token；65 m 处约 8.5 px/m → 车宽 ≈ 15 px、车长 ≈ 38 px。SAHI：步长 256，x 起点 0/256/320、y 起点 0/160 → 6 切片 + 全图 = 7 次推理。帧缓存 640 × 480 × 3 B ≈ 0.92 MB/帧。
- **A5 指针存活**：p₁₃ = 0.815 → λ = −ln(0.815)/13 ≈ 0.0157/s → e^(−1.7λ) ≈ 0.97、e^(−3λ) ≈ 0.95；p₁₃ = 0.411 → λ ≈ 0.0684/s → 0.89、0.81。假设风险率恒定，且「13 s 保持率」即 13 s 内绑定不断的比例；真实丢失常成簇（遮挡、转向），只作量级参考。

## 9. 推荐组合（接口 A 下）

> 「第一层 / 第二层」按用户两项目标理解：第一层 = 常态「保持居中」（感知底座 + 伺服）；第二层 = 「换目标迁移并跟上」（旧帧框解析 + 捕获 + 兜底）。若按「底座 / 兜底」理解，底座即第一层的 MOT 指针，兜底即第二层的 SOT 回放与世界点搜索。

**第一层：检测 + 全画面多目标关联底座，目标 = 轨迹指针；LOS 前馈 + 像素残差伺服**
- 用什么：det-assoc-v1 的在域 YOLO11n + ultralytics BoT-SORT（不换库）；新增 ① 按 frame_id 的全轨迹历史（长度 ≥ VLM p99 延迟 + 1 s，初值 5 s/25 帧）；② 姿态单应 GMC（云台转动 K R K⁻¹、机身平移用地平面单应），图像光流只作校验；③ track_buffer 按秒定义（5 Hz 下 5–15 帧起调）；④ 指针可改绑但只经门控；伺服沿用设计 §3.6 [估计]。
- 为什么：过去帧查表是晚到量测的标准解，对 1–3 s 延迟不敏感（§2）；底座已在仓库内，改动集中在「暴露历史 + 补偿接口」；roboflow 文档把 BoT-SORT 列为移动相机（含无人机视频）首选 [公开资料 https://trackers.roboflow.com/latest/trackers/comparison/]，DynUAV 上 BoT-SORT 虽低于 Deep OC-SORT/TrackTrack，但比原版不含 CMC 的 ByteTrack/OC-SORT 高 6–8 HOTA [公开资料 https://arxiv.org/html/2603.05970] [估计]。

**第二层：解析器 + 三级兜底 + 闭集语义**

| 结果/状态 | 条件 | 动作 | 外部对应 |
|---|---|---|---|
| `BOUND` | 帧 k 上 IoU ≥ τ 且裕度 ≥ m，轨迹现存活 | 改绑指针；连续伺服置中（限速见附录 A2）；可选居中后再问一次 VLM 复核 | DJI 高置信直接跟随；Sightline nearVal 设主跟踪 |
| `AMBIGUOUS` | ≥2 条轨迹过门、裕度不足 | 不改绑；人工确认或带消歧提示再问 VLM | DJI `WAITING_FOR_CONFIRMATION`；GREC 多目标 |
| `NO_TRACK_AT_K` | 帧 k 无轨迹过门（漏检/类别外） | nanotrack-v2 于帧 k 起跟并回放追平；被检测轨迹收养后转 `BOUND`，否则 `SOT_UNCONFIRMED` | Sightline Precision Acquisition；SAM 2 指定帧传播 |
| `TRACK_ENDED` | 帧 k 命中但轨迹现已移除 | 世界点线索（帧 k 位姿 + 地平面）→ 限速转向/机身动作 → 误差区搜索 → 候选须确认 | slew-to-cue；tf2 时间旅行 |
| `FRAME_NOT_IN_HISTORY` | k 超出历史或该帧未处理 | 拒绝并重新查询 | 超出 Sightline Max Pause Time 即不可用 |
| `VLM_NO_TARGET` / `VLM_MULTI` | VLM 自报 | 上报操作者，不动作 | GREC 无目标/多目标 |
| 捕获态 `SLEWING→ACQUIRING(N-of-M)→CENTERED`、`COASTING`、`LOST(原因)` | 见 §5 | 与设计 §5 L0–L4 对齐 | DJI 状态与原因、MAVLink `IDLE/ACTIVE/ERROR`、Sightline coasting 位 |

- 为什么：三级兜底分别对应三种公开成熟做法（过去帧查表 / 旧帧起跟回放 / slew-to-cue），覆盖「检测漏检或类别外目标」与「轨迹已死或目标出画」两类缺口；闭集 + 人工确认是产品通行做法 [估计]。

**最大的不确定点**
1. **指针在「VLM 延迟 + 转向」叠加下的存活率（首要）**：留出域 13 s 保持率仅 0.411 [项目背景]；公开证据是图像法 CMC 在行人数据上 IDF1 +1.62 [公开资料 https://ar5iv.labs.arxiv.org/html/2206.14651]、在 UAV 强自运动数据上 IDF1 +3.8～+7.7 且 IDSW 约减半 [公开资料 https://arxiv.org/html/2603.05970]，均为原生帧率下的图像法；姿态单应在 5 Hz 刻意转向下的收益没有公开定量，只能在本项目回放/仿真中实测 [估计]。
2. **VLM 框在帧 k 上的可解析性**：偏松/amodal 框、歧义与远小目标会压低 `BOUND` 比例；需用离线评估集标定 τ/裕度，并确认「无目标/多目标」输出是否可靠（缺负样本训练时 MLLM 会幻觉出框）[公开资料 https://arxiv.org/abs/2608.04698] [估计]。
3. **姿态量的口径**：姿态单应与世界点线索都要用云台/机身姿态，须确认其以传感器口径进入快层而非 Unity 真值直通 [项目背景] [估计]。
4. Jetson：快层各件速率均有余量（检测约 5 ms 量级、NanoTrack 回放 <0.3 s）；SAM 2 类不宜在线；若 VLM 上板后延迟变长，历史长度随 p99 放大即可 [公开资料 §3.4/§4 所列 URL] [估计]。
