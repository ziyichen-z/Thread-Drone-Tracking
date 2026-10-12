# A3｜Jetson Orin Nano 8GB（Super）上快层 + 小 VLM：部署可行性与妥协清单

> 调研日期 2026-09-28；纯只读调研，未在任何设备上运行任何东西。对象：用户板 Orin Nano 8GB Devkit（Super），JetPack 7.2 / L4T R39.2 / CUDA 13.2 / TRT 10.16。
> 来源等级：**[公开实测]** 第三方公开实测；**[厂商标称]** NVIDIA / Ultralytics / Qwen 等官方发布（含其自测基准表）；**[估计]** 本文推算，写明依据；另加 **[项目实测]** 本仓库证据（给路径代替 URL）。方括号编号（如 [T1]）见文末「来源」。

## 0. 会改变方案选择的结论（先读这一节）

1. **快层上板没有算力问题**：YOLO11n TRT FP16 引擎 4.53 ms [厂商标称][U1]，Python `model(frame)` 端到端约 16 ms（JP6.2、25W）[公开实测][U4]；现桥接 5 Hz、G-7 门 200 ms [项目实测]（`docs/evidence/P1-ENG-FAST-002-latency.json`）。风险在 JP7.2 生态与功耗模式，不在算力。
2. **Orin Nano 没有 DLA、没有视觉加速器（PVA）、没有 NVENC** [厂商标称][N1][N3][N4]：检测器与 VLM 只能抢同一块 1024 核 GPU，不能像 Orin NX/AGX 那样把检测器挪到 DLA。
3. **JP7.2 已有同栈官方 Qwen3-VL-2B 数字**（此前「Orin Nano 上 Qwen3-VL 类公开实测全是 JP6.2.x」的判断需更新）：TensorRT Edge-LLM 0.10.0 在 Orin Nano 8GB / JP7.2 上，INT4 AWQ + FP16 ViT：ViT 141.3 ms（265 图像 token）、prefill 167.2 ms（292 token）、解码 36.1 tok/s、峰值 4,486 MB [厂商标称][T1]。
4. **常被引用的「图像 TTFT 75–114 ms」是同图缓存命中**：原始数据里同一张图连发 5 次，第 1 次 vLLM 585 ms、llama.cpp 2,287 ms，第 2–5 次才是 75 / 114 ms；预热只发了文本 "hi" [公开实测][H2][H3][H5]。闭环每次都是新帧，不能用 75–114 ms 做预算。
5. **JP7.2 的 ISO 安装常把 Super 板装成非 Super 配置**：只剩 7W/15W，GPU 上限 624.75 MHz（Super 应为 1020 MHz）、CPU 1.51 GHz（应为 1.7 GHz）[公开实测][F2][N2]。上板第一步必须核验，否则所有 Super 数字失效；NVIDIA 官方 Orin Nano 表的解码速率恰好像非 Super 带宽（见 §3.2）。
6. **我们的单次指定是「解码主导」**：输出 gold p50 31–32 token、max 89 [项目实测]；按 [T1]/[H4] 速率外推，板上单次 ≈0.95–1.45 s，其中解码占约 55–65% [估计]，与 5060 HF p50 1,615 ms [项目实测] 同量级。降输入分辨率省得少且伤小目标；缩短输出才是大头。
7. **8 GB 共驻**：2B INT4（4.3–4.5 GB）+ 快层只有 headless 才装得下，余量 <1–2 GB [估计]；4B（Orin NX 上已 6,023 MB）[厂商标称][T1]、vLLM（峰值 6.9 GB）[公开实测][H1]、bf16（权重 4.255 GB + 运行开销）[厂商标称][Q3] 均不能与快层共驻。
8. **系留机天然适合「板上只跑快层 + 地面站跑 VLM」**：商用系留缆可带光纤数据链（例：TCOM 称单模光纤最高 100 Gbps）[厂商标称][K2]；本项目设计文档未规定缆内数据链，需用户确认。该方案免重新量化 SFT 模型、免 GPU 争用与内存回收卡顿，时延与板上 INT4 同量级。建议作主方案，板上 VLM 作 P2 选项。

## 1. 可行性矩阵（组件 × 运行时 × JetPack 7 状态 × 时延 × 内存 × 来源）

| 组件 | 运行时 | JP7.2 / CUDA 13 支持状态 | 时延 | 内存 | 来源等级 |
|---|---|---|---|---|---|
| YOLO11n 640 | TRT FP16（ultralytics 导出，板上建引擎） | Ultralytics 文档把 Orin Nano 标为支持 JP7 并有「Run on JetPack 7.2」节，但 JP7.2 只在 AGX Thor / AGX Orin 64GB 实测，Orin Nano Super 基准是 JP6.1 [U3]；用户此前自述已在本板建出 TRT FP16 引擎 | 引擎 4.53 ms [U1]；端到端 ~16 ms [U4]；**JP7.2 数字未查到** | 引擎 8.2 MB [U1]；进程 0.5–1.5 GB [估计] | 厂商标称 / 公开实测 / 估计 |
| YOLO11n | TRT INT8 | 同上 | 3.70 ms，mAP50-95 0.5061→0.4825 [U1]；更早一版表 INT8 mAP 仅 0.318（校准翻车）[U2] | 引擎 5.4 MB [U1] | 厂商标称 |
| YOLO11n | DLA | **不可用**（Orin Nano 无 DLA）[N1][N3] | — | — | 厂商标称 |
| ByteTrack 关联 | C++ | 与 JP 无关 | update 0.007–0.009 ms（Orin Nano Super，JP6.2）[E1] | 可忽略 | 公开实测 |
| ByteTrack / BoT-SORT 关联 | ultralytics Python | numpy + lap，与 JP 无关；但 ultralytics 包依赖 torch | **Orin 未查到**；0.5–2 ms/帧 | — | 估计 |
| BoT-SORT GMC（sparseOptFlow） | OpenCV CPU | 与 JP 无关 | **Orin 未查到**；官方只说关掉可省「几 ms/帧」[U5]；3–10 ms/帧 | — | 厂商标称 / 估计 |
| NanoTrack-v2（SOT 兜底） | CPU（ONNX/NCNN/OpenCV） | 与 JP 无关 | V1/V2 在 M1 CPU >200 FPS（作者标称）[NT]；**Orin 未查到**，估计 ≥60 FPS | 2.0 MB、84.6M FLOPs [NT] | 厂商标称 / 估计 |
| Qwen3-VL-2B | TensorRT Edge-LLM，INT4 AWQ + FP16 ViT | **官方支持**：Orin 仅 JP7.2，精度限 FP16/INT8/INT4 [T2]；需 x86 Linux GPU 主机量化、板上源码编译并建引擎 [T3][T4] | JP7.2：ViT 141.3 ms/265 tok + prefill 167.2 ms/292 tok + 解码 36.1 tok/s [T1]；JP6.2.2 MAXN_SUPER：ViT 208 ms/494 tok + prefill 211 ms/512 tok + 59.8 tok/s [H4] | 峰值 4,486 MB [T1] / 4,343 MB [H4] | 厂商标称 / 公开实测 |
| Qwen3-VL-2B | llama.cpp CUDA，Q4_K_M + mmproj | 预编译件（Ollama）不含 sm_87、回退 CPU [F4]；须源码编 sm_87；JP7.2 上文本模型可用（Qwen2.5-3B Q4_K_M ~23 tok/s）[F3]；**JP7.2 图像路径未查到**；Tegra 上 CUDA VMM 池致图像请求崩溃的 issue 仍 open [L1] | 解码 38 tok/s；新图首 TTFT 2,287 ms，同图重复 114 ms（JP6.2.2）[H2]；15W 模式解码 19.7 tok/s [C1] | 文件 1.107 + 0.819 GB [Q2]；运行峰值**未公开** | 公开实测 / 厂商标称 |
| Qwen3-VL-2B | vLLM W4A16 | JP7.2 可跑上游 `vllm/vllm-openai:v0.22.0-ubuntu2404`（NVIDIA 示例模型是 gemma-3-1b）[F1]；官方轮子 Marlin 不含 sm_87（0.17 时）[V1]，新版**未查到** | 解码 56 tok/s [H1]（原始文件 52 [H3]）；新图首 TTFT 585 ms，同图 75 ms [H3] | 峰值 6.9 GB [H1] | 公开实测 |
| Qwen3-VL-2B | HF transformers bf16 | torch 的 sm_87 覆盖有冲突报告（cu130 失败、cu132 预发布可用 [P1]；cu126 可用 [F3]）；用户板已验证 torch CUDA | **Orin Nano 未查到** | 权重 4.255 GB [Q3]；论坛称「几乎吃满内存」[F5] | 厂商标称 / 公开实测 |
| Qwen3-VL-4B | TensorRT Edge-LLM INT4 | NVIDIA Orin Nano 表**未收录**（Orin 只跑「各内存目标支持的子集」）[T1] | Orin NX 16GB：ViT 77.4 ms、prefill 217.2 ms/292 tok、31.7 tok/s [T1] | Orin NX 上 6,023 MB [T1] | 厂商标称 |
| Qwen3-VL-4B | vLLM | Jetson AI Lab 标了 Orin 8GB，但写明该模块无命令 [V3] | — | bf16 权重 8.876 GB [Q4] | 厂商标称 |
| Qwen2.5-VL-3B | llama.cpp Q4_K_M | JP 版本未披露 | 预处理 1,701 + prefill 2,461 ms ≈ TTFT 4.2 s [S1] | 峰值 5,060 MB [S1]；许可 qwen-research [Q5] | 公开实测 / 厂商标称 |
| 任意 Qwen-VL | MLC | 对 Qwen-VL 系列的支持**未查到**（2024 年 VL 支持请求已关闭、无维护者答复 [M1]）；文本 LLM 上 MLC 约为 llama.cpp 的 2 倍（Qwen2.5-1.5B：60.6 vs 32.0 tok/s）[S1] | — | — | 公开实测 / 未查到 |
| 容器生态 | jetson-containers / Ollama 预编译 | JP7.2 构建问题 issue open [J1]；社区称「崩溃或静默回退 CPU」[F3] | — | — | 公开实测 |

## 2. J1 检测器与关联

**2.1 检测器时延与内存**
- 官方基准只测引擎推理：YOLO11n@640 FP32 7.44 / FP16 4.53 / INT8 3.70 ms（Ultralytics 8.3.157、JP6.1）[厂商标称][U1]。Python `model(frame)` 计时 1000 次得 FP16 约 16 ms（JP6.2、25W）[公开实测][U4]——前后处理与 Python 开销约为引擎的 2.5 倍。
- C++/CUDA 全流程（零拷贝采集 + TRT YOLOv8n FP16 + ByteTrack）1280×720 端到端均值 12.5–15 ms、p99 约 16 ms（headless）[公开实测][E1]：若将来要进一步压时延，C++ 化比 INT8 更有效。
- **DLA 不可用**：NVIDIA 规格页 Orin Nano 的 DL Accelerator 一栏为「–」[厂商标称][N1]；Ultralytics 的 DLA 设备表也只有 AGX Orin / Orin NX [U3]。
- **矩形导出**：帧是 640×480，按 640×640 letterbox 有 25% 像素是填充；导出 imgsz=(480,640) 可省约 25% 检测计算且不损精度 [估计]（需确认 TRT 静态形状与本项目预处理一致）。
- **INT8 不值得**：只快 0.83 ms（−18%），mAP50-95 降 2.4 pt [厂商标称][U1]，且早一版表出现过 INT8 mAP 0.318 的校准失败 [厂商标称][U2]；我们 H 上目标 S 层召回 0.879 [项目实测]（`docs/evidence/P1-ENG-FAST-002-report.md` AC-3 表），小目标最怕量化。

**2.2 关联层在 ARM CPU 上的成本**
- ByteTrack 本体极轻：C++ 实现在 Orin Nano Super 上每次 update 0.007–0.009 ms [公开实测][E1]。ultralytics Python 版（numpy + lap）**未查到 Orin 实测**，估计 0.5–2 ms/帧 [估计]。
- BoT-SORT 的 GMC（ultralytics 8.4.104 源码 `trackers/utils/gmc.py`）：灰度 → 2 倍降采样到 320×240 → 每帧 `goodFeaturesToTrack`（最多 1000 角点）→ `calcOpticalFlowPyrLK` → 逐点 Python 循环 → `estimateAffinePartial2D` RANSAC。**Orin 未查到实测**；Cortex-A78AE 1.7 GHz 上估计 3–10 ms/帧 [估计]；Ultralytics 只说静态相机关掉可省「几 ms/帧」[厂商标称][U5]；BoT-SORT 论文称 GMC 相对检测器可忽略（桌面 CPU 语境）[B1]。
- 合计快层（Python、TRT FP16、BoT-SORT+GMC）单帧 p50 约 20–30 ms [估计]，对照 Mac CPU p95 48.4 ms、MPS p95 31.9 ms [项目实测]（`docs/evidence/P1-ENG-FAST-002-latency.json`）。

**2.3 去掉 GMC，改用云台角速度 / 角度补偿**
- 原理可行：BoT-SORT 论文明确把图像配准当作「缺少导航/IMU 数据或相机内参时」的近似 [B1]。我们有云台角与（仿真）内参，纯旋转时像面运动是单应 H = K·R_Δ·K⁻¹，与景深无关，计算量微秒级 [估计]。
- 接口可插：ultralytics 8.4.104 `trackers/byte_tracker.py:357-362` 在 update 内调用 `self.gmc.apply(img, dets)` 取 2×3 矩阵再 `multi_gmc` 到轨迹；替换 `self.gmc` 为读云台角差的对象即可，不改库 [估计，按源码读取]。
- 两个误差源 [估计，设 f≈500 px]：(a) 机身平移视差 ≈ f·v·Δt/Z，v=5 m/s、Z=40 m 时 5 Hz 约 12 px、30 Hz 约 2 px；(b) 云台角与曝光时刻不同步，60°/s 下 20 ms 误差约 10 px。所以「去 GMC」要与「上板后提帧率 + 时间戳对齐」一起做。
- 值多少：V 序列 13 s 保持率 BoT-SORT 0.419 vs ByteTrack 0.369 [项目实测]（`docs/evidence/P1-ENG-FAST-002-report.md:30`），GMC（连同卡尔曼状态差异）上界约 5 pp——只能替换，不能直接删。
- 顺带收益：同一旋转单应可把 VLM 查询帧上的框投到当前帧，服务「重新指定 → 追平 → 云台转向新目标」这一步（任务 (2)）[估计]。

## 3. J2 小 VLM（Qwen3-VL-2B / 4B、Qwen2.5-VL-3B）

**3.1 我们一次指定查询的构成** [项目实测]
- 图像：训练/推理网格固定 `[1,30,40]`（`docs/reviews/P1-ENG-SFT-002.md:499`），即 16 px patch、2×2 合并后 300 个图像 token；Qwen3-VL 每 token 覆盖 32×32 px [厂商标称][Q1]。
- 文本：固定提示 1,217 字符（G4 为 1,412）（`tools/eng_sft/prompt_v2.py` 的 `fixed_prompt_chars`）→ 约 300–350 token [估计]；prefill 合计约 600–700 token [估计]。
- 输出：gold token p50 31–32、max 89（`docs/evidence/P1-ENG-SFT-002-data-report.md:165-170`）。

**3.2 板上单次时延估计（新帧、batch 1）**

| 场景 | ViT（300 tok） | prefill（~650 tok） | 解码（33 tok） | 合计 | 依据 |
|---|---|---|---|---|---|
| TRT Edge-LLM，按 JP7.2 官方表速率 | ~160 ms | ~0.37 s | ~0.91 s | **~1.45 s** | [T1] 线性外推 [估计] |
| TRT Edge-LLM，按 JP6.2.2 MAXN_SUPER 速率 | ~126 ms | ~0.27 s | ~0.55 s | **~0.95 s** | [H4] 线性外推 [估计] |
| llama.cpp Q4_K_M | 新图未知（首图 TTFT 2,287 ms 含冷启动 [H2]） | 同左 | ~0.87 s（38 tok/s [H1]） | 1.2–3.2 s | [估计] |
| 参照：5060 Laptop，HF eager 零样本 | — | — | — | p50 1,615 / p95 1,956 ms | [项目实测] `docs/unity-test-log.md:101` |
| 参照：5090，HF 未合并 LoRA（C2） | — | — | — | p50 1,427 ms | [项目实测] `docs/evidence/P1-ENG-SFT-002-train-summary.json:271` |

- 最长输出 89 token 时，解码按 36 tok/s 约 2.5 s，单次约 3 s [估计]。
- **核实记忆中的「INT4 38–60 tok/s」**：38 / 56 / 60 tok/s 分别是 llama.cpp / vLLM / TRT Edge-LLM，均出自 [H1]（JP6.2.2、MAXN_SUPER、Cosmos-Reason2-2B，即 Qwen3-VL-2B 架构）[公开实测]；JP7.2 官方表是 36.1–36.9 tok/s（v0.8–v0.10）[厂商标称][T1]。
- **36 vs 60 tok/s 差距的一个吻合假设**：带宽同为约 102 GB/s 的 Orin NX 16GB [N1] 官方解码 58.5 tok/s [T1]；Orin Nano 表 36.1/58.5 = 0.62，接近非 Super 带宽比 68/102 = 0.67 [N2]；官方页未标功耗模式、只写「默认设置」[T1]。推测官方 Orin Nano 表不是 MAXN_SUPER [估计]——实测前按 36–60 tok/s 区间做预算。
- 投机解码（EAGLE3/MTP）在 Orin Nano 官方表只有文本 Qwen3-1.7B 行（解码 36.3→48.7 tok/s，v0.8）[厂商标称][T1]，**Qwen3-VL-2B 无 Orin Nano 数据**，且需另训 draft。
- 若将来可换模型：官方表 Qwen3.5-0.8B（VLM 形态）在 Orin Nano 上 59.0 tok/s、2,760 MB [厂商标称][T1]——解码减半、省 1.7 GB，但要重训，属模型层决策。

**3.3 运行时逐项**
- **TensorRT Edge-LLM（首选板上 INT4 路径）**：官方把 Jetson Orin + JP7.2 列为 Official 级 [T2]。代价：① AWQ 量化要在 x86 Ubuntu 22.04/24.04、算力 ≥8.0 的 GPU 主机做，推荐 24 GB+ 显存 [T3]——5060 是 Windows 8 GB，要么 WSL2 试、要么租云（可行性**未查到**）；② LoRA 须先合并再量化再导出 [T6]；③ 板上 CMake 源码编译并建引擎，引擎与 GPU/TRT 版本绑定 [T3]；④ OpenAI 兼容服务端仍是 Experimental，一次只收一个请求 [T5]——与我们的 single-flight worker 相容。JP6.2.2 上曾需内核 `cma=950M` + ONNX 改写才建得出引擎 [H1]，JP7.2 上是否仍需**未查到**。
- **llama.cpp**：smoke-pack 的 03 脚本即此路。风险：Tegra 上 CUDA VMM 池各保留 32 GB 虚拟地址、致多模态请求 OOM 的 issue 仍 open（报告于 AGX Orin 64GB / JP6 大模型；报告人靠二进制补丁绕过，另提到编译选项 `GGML_CUDA_NO_VMM`，未见验证）[L1]；AGX Orin 用户报 Qwen3-VL-4B Q4_K_M 图像编码 4,079 ms [公开实测][L2]。**注意 smoke 集 32 行只有 25 张不同帧**，重复帧会命中服务端提示缓存，测时须关 `cache_prompt` 并分开报告首见帧。
- **vLLM**：JP7.2 能跑上游容器 [F1]，但 8 GB 上无余量：NVIDIA/HF 在 Orin Super Nano（JP6）的配置把 `--max-model-len` 压到 256、`--gpu-memory-utilization` 0.65、`max_pixels` 150,528 [厂商标称][V2]——我们 640×480 = 307,200 像素，超出该上限。只适合单独对照测量。
- **HF bf16**：权重 4.255 GB [Q3]；论坛用户在 Orin Nano 上跑 Qwen3-VL-2B FP16「几乎吃满内存」[F5]。只能 headless 单独跑，作为量化对照。
- **MLC**：Qwen-VL 支持未查到 [M1]。**jetson-containers**：JP7.2 构建 issue 未关 [J1]。

**3.4 量化与功耗对行为的影响**
- 视觉编码器 F16→Q8 无精度变化；Q8→Q4 在 BLINK/CV-Bench 上降 1.8–2.4 pt（Cosmos-Reason2-2B、llama.cpp、Orin Nano 15W）[公开实测][C1]。
- INT4 AWQ 对**框定位与三态（给框 / none / 歧义）**的影响：**未查到**任何公开结果——必须用 609 行评估集复算（§6 第 4 步）。
- 15W 模式下 llama.cpp 解码 19.7 tok/s [C1]，约为 MAXN_SUPER 38 tok/s [H1] 的一半 [公开实测，不同实验]。
- 4B 不建议：内存不够（§4），且小目标瓶颈是 32 px/token 网格——G1 S 层 36.7%（M 81.1%、L 85.9%）[项目实测]（`docs/reviews/P1-ENG-SFT-002-stage-summary.md:54`），4B 同网格。Qwen2.5-VL-3B 不建议：TTFT 约 4.2 s [S1] 且为研究许可 [Q5]。

## 4. J3 8 GB 统一内存共驻预算

| 项 | 数值 | 来源 |
|---|---|---|
| Linux 可见总量 | ≈7.4 GiB（607 MiB 空闲 + 6.8 GiB 可用） | [估计]，由 [R1] 推得 |
| 系统空闲（headless） | 0.6–0.7 GiB [R1]；另一实测「系统+守护进程」约 1.2 GB [R2] | 公开实测（JP7.2） |
| 桌面额外占用 | 未登录 +0.2 GiB [R1]；登录 GNOME +1.6 GB [R2]；Ultralytics 称关桌面省约 865 MB [U3] | 公开实测 / 厂商标称 |
| 快层进程 | 0.5–1.5 GB（TRT 引擎 8 MB + CUDA/TRT 库 + ultralytics/torch + OpenCV + 帧缓冲）；无懒加载时 CUDA 库加载可 >600 MB [F7] | 估计 / 厂商标称 |
| VLM：2B TRT Edge-LLM INT4 | 4.3–4.5 GB 峰值 | [T1][H4] |
| VLM：2B llama.cpp Q4_K_M（ctx 4096） | 2.5–3.5 GB（文件 1.93 GB [Q2] + KV 0.47 GB：28 层 × 8 KV 头 × 128 维 × K/V × 2 B ≈ 112 KiB/token [Q3 config] + 计算缓冲） | 估计 |
| 合计：2B TRT + 快层 + headless | 5.4–7.2 GB vs 7.4 GiB → 余量约 0.2–2 GB（GB/GiB 混用，按保守口径） | 估计 |
| 合计：2B TRT + 快层 + 桌面登录 | 7.0–8.8 GB → 大概率超 | 估计 |
| 合计：4B TRT（6.0 GB）+ 快层 + headless | 7.1–8.7 GB → 不可行 | 估计 |

- **换页救不了 GPU**：论坛资深成员指出 GPU 只能用物理内存；NVIDIA 工作人员称内存将尽时分配要等回收/换出，可能耗时数秒（Xavier NX 语境，同为统一内存架构）[厂商标称][F6]。JP7.2 默认带一个磁盘 swap 文件 [R2]，它只能缓解 CPU 页，还会把跟踪器/GMC 这类 CPU 任务拖出尖峰。
- **常驻 vs 唤醒**：唤醒要重新载入 2–3 GB 引擎/权重并付首请求冷启动 0.5–3 s [公开实测][H1]，引擎加载时间**未查到**，估计每次指定多 2–6 s [估计]；更糟的是载入会触发内存回收，可能让快层卡顿数秒 [F6]。结论：**要么常驻（仅 headless 下的 2B INT4），要么放地面站**；不做唤醒式。
- **降内存手段**：headless；TRT Edge-LLM 的 `maxInputLen`/`maxKVCacheCapacity` 按我们约 650 token 的提示收到 1024 左右（官方对 Orin Nano 的 4B 文本模型示例用 512/1024 [T3]）；llama.cpp 用 Q8 mmproj（0.445 GB [Q2]，F16→Q8 无精度损失 [C1]）；快层去 torch（TensorRT Python + numpy 跟踪器）约省 0.5–1 GB [估计]；给快层 `oom_score_adj=-1000`、给 VLM 服务设 systemd `MemoryMax` [估计]。

## 5. J4 妥协清单（对第一层 = 居中/迁移、第二层 = 语言指定 的影响）

| 妥协 | 省什么 | 对第一层 | 对第二层 | 建议 |
|---|---|---|---|---|
| 检测器 INT8 | −0.83 ms/帧 [U1] | 小目标召回风险（mAP −2.4 pt [U1]，校准可翻车 [U2]），居中连续性受损 | 无 | 不做，FP16 足够 |
| 480×640 矩形导出 | 约 25% 检测计算 [估计] | 无损 | 无 | 做 |
| 缩 imgsz（<480） | 计算约随像素数下降 [估计] | S 目标漏检上升（H 上 S 召回 0.879 [项目实测]） | 无 | 不做 |
| 降帧率 | GPU/CPU 时间 | 帧间位移变大 → 关联更难、更依赖 GMC；迁移阶段最需要连续跟踪 | 给 VLM 让 GPU | 反向操作：上板后提到 15–30 Hz；只在 VLM 解码期短暂降到 ≥10 Hz [估计] |
| 去 GMC → 云台/机身角速度补偿 | 3–10 ms CPU/帧 [估计] | 同步好时更准、不受纹理影响；不同步 20 ms 约 10 px 误差 [估计]；GMC 值约 5 pp 上界 [项目实测] | 可把查询帧的框投到当前帧，帮助追平 | 推荐；先在仿真用真云台角实现并在 V 序列对照 |
| VLM 降输入分辨率（max_pixels） | 300→约 80 图像 token，ViT+prefill 约省 0.25 s（≈17%）[估计] | 无 | S 层已 36.7% [项目实测]，会更差；训练网格固定 `[1,30,40]`，偏离需重训 | 不做 |
| VLM 缩短输出 / 改「检测器出候选、VLM 选编号」 | 解码 33→约 5–15 token，省 0.5–0.8 s [估计] | 无 | 需改协议与重训；候选式还绕开 32 px 网格的小目标上限 | 值得作为模型层候选（不是部署决定） |
| VLM 放地面站（缆内链路或 Tailscale） | 板上省 4.3–4.5 GB 与 GPU 争用 | 快层独占 GPU；链路断了照样跟 | 往返 = 上传一张 JPEG（约 30–80 KB [估计]）+ RTT + 服务端 1.4–1.6 s [项目实测]；Tailscale 官方只说直连最低、DERP 中继更慢，未给数字 [K1] | **主方案**；上板前核验 `tailscale status` 为 direct |
| 混合：板上快层 + 远程 VLM + 板上常驻备用 2B | 断链时仍可指定 | 备用 VLM 常驻占 4.3 GB，只在 headless 可行 | 可降级自治 | 只在必须断链自治时做；不做唤醒式备份 [F6] |
| 15W 功耗档 | 功耗 | 检测器变慢（JP7.2 数字未查到） | 解码约减半（19.7 vs 38 tok/s）[C1][H1] | 只作功耗试验档 |
| 换 4B / Qwen2.5-VL-3B | — | 挤掉快层内存 | 4B 同网格不解决小目标；2.5-VL-3B 慢且研究许可 [S1][Q5] | 不做 |

- 板上无 NVENC：地面站若还要看实时视频，只能软件编码（1080p30 需 1–2 个 CPU 核）[厂商标称][N4]；指定查询只发单帧 JPEG，不受影响。
- 板上 VLM 路线的隐性成本：INT4 量化需要 x86 Linux GPU 主机 [T3]，量化后必须复算 609 行三态行为；地面站路线直接复用已评估的 bf16 C2。

## 6. J5 最小实测协议（只写协议，不执行）

执行前提：按设计基线 §8 与 COORD-010，须新立工作项写明设备与额度（下载：GGUF 约 1.93 GB 或 base 4.255 GB [Q2][Q3]；x86 量化主机时长）并获用户授权；本文件不构成授权。全程只用录制帧回放，零 Play。顺序 0 → 1 → 2 →（选地面站则 6）→ 3 → 4 → 5；任一步不过即停，记录后回用户，不自行升级。

0. **环境核验（只读、零模型）**：`sudo nvpmodel -q`；`cat /etc/nv_boot_control.conf`（应含 `devkit-super`）；GPU/CPU 最高频率；headless 下 `tegrastats` 空闲 5 min；`dmesg | grep -i nvmap`。
   通过：MAXN_SUPER 可选，GPU 上限 1020 MHz、CPU 1.7 GHz [N2]；headless 空闲 ≤1.2 GB [R1][R2]。不过：停，走 [F2] 的重刷路径（需用户在 Linux 主机操作）。
1. **快层单测**：用冻结 `det-assoc-v1` 权重在板上导出 TRT FP16 两版（640 方形、480×640 矩形）；V 序列 320 帧回放（同 FAST-002 G-7 口径）；分项记录 trtexec GPU 时间、update p50/p95、GMC 单独、跟踪器单独、CPU 占用。
   通过：update p95 ≤50 ms（≈Mac CPU p95 48.4 ms [项目实测]）且 ≤ G-7 门 200 ms；前 50 帧检测数零不一致、框归一化差 ≤1e-3（沿用 FAST-002 `cpu_vs_mps` 限值 [项目实测]）；FP16 超限则报 IoU 分布回用户。
2. **快层热稳态**：以 15–30 Hz 循环回放 30 min。通过：最后 5 min p95 ≤ 首 5 min 的 1.2 倍；`tegrastats` 无降频；无丢帧。
3. **VLM 单测（快层不开）**：3a（可选对照）HF bf16，headless 装不下就记 OOM 即止；3b llama.cpp Q4_K_M + mmproj（smoke-pack 03 脚本，请求关 `cache_prompt`，只用互不相同的帧，首见帧与稳态分开报）；3c TRT Edge-LLM INT4（需先在 x86 主机合并并量化 C2，另授权）。分项记录 ViT / prefill / 解码（TRT 用 `--dumpProfile`）、峰值统一内存、首请求冷启动、引擎加载时间。
   通过：新帧 p50 ≤1.6 s（不劣于 5060 HF p50 1,615 ms [项目实测]）、p95 ≤2.5 s；峰值 ≤4.6 GB；32 行冒烟解析失败 0。
4. **量化等价（决定板上 VLM 能否成立的核心）**：用同一量化产物跑 609 行评估（可在桌面跑，省板上时间），出表 G 各组相对 bf16 C2 的差值、三态混淆（none / 歧义 / 给框）、解析失败数。建议通过线（阈值须接受角色定）：每组 ≤3 pp，G5 硬给框率不上升。
5. **共驻**：快层按第 2 步帧率运行，同时每 10 s 用新帧查询一次 VLM，持续 30 min。通过：快层 p95 ≤ 第 1 步的 2 倍且 ≤100 ms、无连续 >2 帧丢帧；VLM p95 ≤ 第 3 步的 1.3 倍；峰值 RAM ≤7.0 GiB；`dmesg` 无 NvMap/OOM；swap 使用 0。
6. **地面站 VLM（若选主方案）**：`tailscale status` 显示 direct（或走缆内链路）；30–80 KB JPEG 往返 p95 ≤100 ms；端到端 p95 ≤ 地面站本机 p95 + 0.3 s；断链测试：快层时延不变，VLM 请求在超时内报 timeout 并进入「VLM 不可用」状态。

## 7. 查不到 / 未适配清单

- JP7.2 上 Orin Nano 的 YOLO11n TRT 公开时延：**未查到**（公开数字都是 JP6.1/6.2）。
- BoT-SORT GMC（sparseOptFlow）与 ultralytics Python 跟踪器在 Orin CPU 上的单帧成本：**未查到**。
- 检测器与 VLM 在 Orin Nano 上并发时的 GPU 争用实测：**未查到**（第 5 步要测）。
- llama.cpp 的 Qwen3-VL 图像路径在 JP7.2 / CUDA 13.2 上的表现：**未查到**；Tegra VMM issue **未修** [L1]。
- 上游 vLLM 新版对 sm_87 Marlin 的覆盖：**未查到**（0.17 时不含 [V1]）。
- TRT Edge-LLM：引擎加载 / 冷启动时间、官方 Orin Nano 表所用功耗模式、JP7.2 上建引擎是否仍需 `cma` 调参：**未查到 / 未标注**。
- Qwen3-VL-4B 在 Orin Nano 上的官方数据：**未收录** [T1]。
- INT4 AWQ 对 Qwen3-VL-2B 框定位与三态行为的影响：**未查到**。
- 用 5060（Windows、8 GB）做 TRT Edge-LLM 量化是否可行：**未查到**。
- Tailscale DERP 中继的额外时延：官方**未给数字** [K1]。
- MLC 对 Qwen-VL 系列的支持：**未查到** [M1]。
- 未适配：Ollama 预编译件（无 sm_87）[F4]、jetson-containers（JP7.2 构建 issue 未关）[J1]、Orin Nano 的 DLA/PVA/NVENC（硬件不存在）[N1][N3][N4]。

## 来源

- [U1] Ultralytics Jetson 指南 v8.3.200（YOLO11n Orin Nano Super 表，8.3.157 基准）：https://github.com/ultralytics/ultralytics/blob/v8.3.200/docs/en/guides/nvidia-jetson.md
- [U2] 同指南 v8.3.150（8.3.51 基准，INT8 mAP 0.318）：https://github.com/ultralytics/ultralytics/blob/v8.3.150/docs/en/guides/nvidia-jetson.md
- [U3] Ultralytics Jetson 指南当前版（JP 支持表、JP7.2 节、DLA 表、省内存表）：https://docs.ultralytics.com/guides/nvidia-jetson
- [U4] Ultralytics issue #22479（Orin Nano Super 实测 16 ms vs 4.53 ms）：https://github.com/ultralytics/ultralytics/issues/22479
- [U5] Ultralytics 跟踪文档（gmc_method）：https://docs.ultralytics.com/modes/track
- [N1] NVIDIA Jetson Orin 规格页：https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/ ；Orin Nano Super 套件页：https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/
- [N2] NVIDIA「Super Boost」技术博客（GPU 635→1020 MHz、68→102 GB/s）：https://developer.nvidia.com/blog/nvidia-jetson-orin-nano-developer-kit-gets-a-super-boost/
- [N3] JetsonHacks Orin Nano 评测（无 DLA、无视觉加速器、无硬件编码器）：https://jetsonhacks.com/2023/03/22/nvidia-jetson-orin-nano-developer-kit-the-perfect-solution-for-makers-and-developers-a-review/
- [N4] NVIDIA Jetson Linux「Software Encode in Orin Nano」：https://docs.nvidia.com/jetson/archives/r35.3.1/DeveloperGuide/text/SD/Multimedia/SoftwareEncodeInOrinNano.html
- [F1] NVIDIA 论坛 JP7.2 Orin Nano 入门与反馈帖：https://forums.developer.nvidia.com/t/jetpack-7-2-jetson-linux-r39-2-on-jetson-orin-nano-developer-kit-getting-started-and-feedback-thread/372151
- [F2] 同帖第 2 页（非 Super 配置、624.75 MHz）：https://forums.developer.nvidia.com/t/jetpack-7-2-jetson-linux-r39-2-on-jetson-orin-nano-developer-kit-getting-started-and-feedback-thread/372151?page=2
- [F3] NVIDIA 论坛 JP7.2 Orin Nano Super 实用指南（2026-06）：https://forums.developer.nvidia.com/t/setting-up-the-nvidia-jetson-orin-nano-super-dev-kit-on-jetpack-7-2-a-practical-guide-june-2026/372490
- [F4] NVIDIA 论坛 JP7.2 GPU 加速问题（预编译件缺 sm_87）：https://forums.developer.nvidia.com/t/jetpack-7-2-gpu-acceleration-issue/372521
- [F5] NVIDIA 论坛 Orin Nano 跑 Qwen3-VL-4B：https://forums.developer.nvidia.com/t/orin-nano-qwen3-vl-4b/348122
- [F6] NVIDIA 论坛统一内存与 swap：https://forums.developer.nvidia.com/t/unified-memory-allocation-and-swap/358234
- [F7] NVIDIA 论坛小模型 TRT 高内存（CUDA 库加载 >600 MB）：https://forums.developer.nvidia.com/t/tensorrt-small-model-high-ram-consumption-during-inference-problem/307373
- [T1] TensorRT Edge-LLM 性能基准（v0.8–v0.10，JP7.2）：https://nvidia.github.io/TensorRT-Edge-LLM/latest/user_guide/performance/performance-benchmarks.html
- [T2] TensorRT Edge-LLM 官方支持矩阵：https://nvidia.github.io/TensorRT-Edge-LLM/latest/user_guide/getting_started/support-matrix.html
- [T3] Jetson AI Lab TensorRT Edge-LLM 教程：https://www.jetson-ai-lab.com/tutorials/tensorrt-edge-llm/
- [T4] TensorRT Edge-LLM 快速上手：https://nvidia.github.io/TensorRT-Edge-LLM/latest/user_guide/getting_started/quick-start-guide.html
- [T5] TensorRT Edge-LLM 实验性服务端：https://nvidia.github.io/TensorRT-Edge-LLM/latest/user_guide/examples/experimental-server.html
- [T6] TensorRT Edge-LLM LoRA：https://nvidia.github.io/TensorRT-Edge-LLM/latest/user_guide/features/lora.html
- [H1] hokwangchoi Orin Nano 基准 README（JP6.2.2、MAXN_SUPER）：https://github.com/hokwangchoi/jetson-orin-nano-benchmarks
- [H2] 同仓 llama.cpp 原始结果：https://github.com/hokwangchoi/jetson-orin-nano-benchmarks/blob/master/vlm-benchmarks/assets/results/llamacpp/llamacpp_cosmos_q4km_20260418_233102_streaming.json
- [H3] 同仓 vLLM 原始结果：https://github.com/hokwangchoi/jetson-orin-nano-benchmarks/blob/master/vlm-benchmarks/assets/results/vllm/vllm_cosmos_w4a16_20260418_235455_streaming.json
- [H4] 同仓 TRT Edge-LLM profile：https://github.com/hokwangchoi/jetson-orin-nano-benchmarks/blob/master/vlm-benchmarks/assets/results/trt/trt_profile_image_5x_20260419_013103.json
- [H5] 同仓 bench_vllm.py（预热只发文本）：https://github.com/hokwangchoi/jetson-orin-nano-benchmarks/blob/master/vlm-benchmarks/benchmarks/bench_vllm.py
- [S1] sudongtan Jetson 多模态基准：https://github.com/sudongtan/jetson-multimodal-benchmark
- [C1] Chiaki-Shen 视觉编码器量化研究（Orin Nano 15W）：https://github.com/Chiaki-Shen/ias-vlm-quantization-edge
- [L1] llama.cpp issue #29142（Tegra VMM 池）：https://github.com/ggml-org/llama.cpp/issues/29142
- [L2] llama.cpp discussion #17732（AGX Orin Qwen3-VL 慢）：https://github.com/ggml-org/llama.cpp/discussions/17732
- [V1] thehighnotes vLLM Orin 轮子 README（Marlin 不含 sm_87）：https://huggingface.co/thehighnotes/vllm-jetson-orin/blob/main/README.md
- [V2] NVIDIA/HF「在 Jetson 部署 VLM」博客：https://huggingface.co/blog/nvidia/cosmos-on-jetson
- [V3] Jetson AI Lab Qwen3 VL 4B 页：https://www.jetson-ai-lab.com/models/qwen3-vl-4b/
- [M1] MLC-LLM VL 支持 issue #1709：https://github.com/mlc-ai/mlc-llm/issues/1709
- [J1] jetson-containers issue #1736（JP7.2/CUDA 13.2 构建）：https://github.com/dusty-nv/jetson-containers/issues/1736
- [P1] iuliaferoli JP7.2 安装记录（torch 轮子与 sm_87）：https://github.com/iuliaferoli/jetson-jp7.2-install
- [E1] edge-tracking（C++ TRT + ByteTrack，Orin Nano Super）：https://github.com/Manishnayak234/edge-tracking
- [B1] BoT-SORT 论文：https://arxiv.org/abs/2206.14651
- [NT] NanoTrack V1–V3 说明（HonglinChu/SiamTrackers）：https://github.com/HonglinChu/SiamTrackers/tree/master/NanoTrack
- [Q1] Qwen3-VL README（32 px/token）：https://github.com/QwenLM/Qwen3-VL
- [Q2] Qwen3-VL-2B-Instruct-GGUF 文件：https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct-GGUF/tree/main
- [Q3] Qwen3-VL-2B-Instruct 文件与 config：https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct/tree/main
- [Q4] Qwen3-VL-4B-Instruct 文件：https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/tree/main
- [Q5] Qwen2.5-VL-3B 许可：https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct/blob/main/LICENSE
- [R1] dev.to：JP7.2 Orin Nano headless 省内存：https://dev.to/shaifurcodes/squeezing-every-megabyte-optimizing-an-8gb-nvidia-jetson-orin-nano-for-headless-ros-2-and-edge-ai-3cch
- [R2] toptechboy：JP7.2 Orin Nano headless：https://toptechboy.com/running-headless-on-the-nvidia-jetson-orin-nano-on-jetpack-7-2-run-big-local-llms-like-a-boss/
- [K1] Tailscale 连接类型文档：https://tailscale.com/docs/reference/connection-types
- [K2] TCOM 系留无人机（缆内光纤数据链）：https://tcomlp.com/aerospace-platforms/tethered-drones/
