# 板上共驻诊断测试设计（JET:CORES-DIAG:1，2026-10-09，supervisor 会话）

性质：**诊断，不是提案、不是证据、不是新授权。** 执行范围与额度只来自账本 2026-10-09 两条：
「P1-ENG-JET-001 — 用户方向：先做共驻诊断…签发 JET:CORES-DIAG:1」（范围、顺序、读数、停止条件、信封）与
「P1-ENG-JET-001 — 用户选择：JET:CORES-DIAG:1 改为独立目录执行…」（执行路径）。本文与账本冲突时以账本原话为准。
结果不进 `docs/evidence/P1-ENG-JET-001-*`，不形成 S5/AC-9 verdict，不改 S1/S2 STOP；`P1-ENG-JET-001` 门与 Lifecycle 不动。
所有产物标 `purpose=diagnostic_only`、`gate_evidence=false`。

## 1. 要回答的问题

1. 检测器（PyTorch CUDA，后 TensorRT FP16）和 C2 VLM 服务同时在 Orin Nano 8GB 上跑 30 min，资源够不够、各自慢多少。
2. S1 的 FP16 框偏差是不是 TensorRT 特有：同一冻结 `.pt` 用 PyTorch 在板上推理，对 frozen-V（Mac MPS）逐帧比对。

## 2. 输入与身份（运行时从原件解析，不手抄派生值）

| 输入 | 来源与核验 |
|---|---|
| 冻结检测器 `.pt` | sha256 `d6a0d6a9cdee06a0790f5d9812a1fe98db033520981c0ffafe786c3cbbe059c9`；板上路径从 `outputs/eng-jet/P1-ENG-JET-001/` 下 S1/S2 板清单（`board-manifest-s1s2-system-d.json` 等）解析，板上现算 sha 必须一致 |
| 方形 FP16 引擎（A2 用） | `/home/jetson/eng-jet/results/d/engines/det-assoc-v1-fp16-640.engine`，sha256 `5e45529a76fabb5282a5b6a1108e78f60a4200554e74eb6cee8194663f494963`（`docs/evidence/P1-ENG-JET-001-fastlayer.json` S1/S2）；缺失或 sha 不符 → A2 停报，**不重建** |
| 快层 Python 环境 | 板上 `~/eng-jet/sysvenv`（S1/S2 已装，torch 2.9.1+cu130、ultralytics 8.4.104、lap 等）；缺包即停报，不装 |
| a7 前 320 帧与 frozen-V 缓存 | 沿 S1 所用回放序列与 frozen-V 缓存（S1 板清单与 `-fastlayer.json`「S1」解析）；板上逐件核 sha（`P1-ENG-JET-001-a7-frame-sha256.jsonl.gz`） |
| 插件 | 现行 `controller/det_assoc_tracker.py`（BoT-SORT 关联，冻结规格不改）；以本仓库当前 HEAD 打代码束上板，束内文件 sha 入 manifest |
| VLM：C2 Q4_K_M、F16 mmproj、llama-server | 沿 10-06「阶段BC2 诊断」（无 JSON 约束那一次）原件 `outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/` 的 state/收据解析板上路径、sha 与 `server.argv`；板上现算 sha 一致才用，不用官方 base 替代 |
| VLM 查询帧 | HOLD 盲文件行序中首次出现的前 180 个互异 `frame_sha256`，`surface` 取该行（S5 帧取法）；板上帧根沿 C2 诊断 `board_paths.hold_frames`，逐件核 sha；外加 3 张预热帧（沿 C2 诊断预热取法） |
| VLM 请求体 | 沿 C2 诊断（无约束）同一 prompt 与推理参数，不加 `response_format` |
| VLM 单跑基线 | 不重测：从 C2 诊断原件 calls 计算往返 p50/p95（n 注明） |
| 板与链路 | 用户 Jetson Orin Nano 8GB Super；执行机 Mac mini 经有线链路，SSH 目标与选项沿 C2 诊断/SR 正式轮收据；**不用 Tailscale 别名 `Jetson`** |

## 3. 步骤

全程一个运行目录：Mac mini `outputs/eng-jet/cores-diag/<UTC>/`（已被 `/outputs/eng-jet/` 忽略），板上 `~/eng-jet/cores-diag/<UTC>/`。
所有板上新文件只在该目录；旧引擎、权重、帧、服务二进制、旧运行目录只读。

- **P0 预检（只读）**：连板；记 `nvpmodel -q`、headless、`free -m`、swap、`df`、`dmesg` 基线（行数与末行）、devfreq/cpufreq `max_freq`；核第 2 节全部输入；核 VLM 端口空闲、无其他模型服务常驻（被占即停报，不杀他人进程、不换端口）；核 sysvenv 能 `import torch, ultralytics, tensorrt` 且 `torch.cuda.is_available()`。任一不符即停。
- **传代码束**（≤ 50 MB）：独立诊断脚本 + 当前 `controller/` 所需文件；权重与帧不传，只核 sha。
- **A0 单跑基线（≤ 5 min）**：PyTorch CUDA 检测器 + 插件，a7 前 320 帧按 5 Hz 节拍循环。VLM 不起。
- **A1 PyTorch 臂（30 min）**：
  1. 起 llama-server（加载计 1 次），健康检查后发 3 张预热。
  2. 检测器按 5 Hz 墙钟节拍循环回放 320 帧（第 i 帧计划时刻 `t0 + 0.2·i`；处理完成晚于下一节拍即计丢帧，跳到当前应处理的帧）。
  3. 同时每 10 s 向服务发 1 张新帧，共 180 次；两路时间戳须重叠。
  4. 一致性：首轮 320 帧的 PyTorch 原始检测对 frozen-V 逐帧比对，口径同 S1（前 50 帧检测数不一致帧数；320 帧框归一化最大差；附 IoU 分布）。只报告，不判过线。
  5. 停服务（TERM → 必要时 KILL），核端口释放。
- **A2 TensorRT 臂（30 min）**：重启 llama-server（加载计 1 次，清视觉缓存），检测器换方形 FP16 引擎（反序列化计 1 次），其余同 A1 第 1–3、5 步；框偏差已知，照记不阻断。
- **收尾**：停全部本批进程、核端口与 GPU 内存释放、保存 tegrastats/dmesg 尾件；拉回板上原件到 Mac；Mac 汇总两臂对照表。

监测（A0/A1/A2 全程）：`tegrastats --interval 1000` 落文件；每秒采系统已用内存、各进程 RSS、`/proc/meminfo` swap；每臂结束 `dmesg` 与基线做差。

## 4. 读数（两臂同口径）

检测器每帧 p50/p95/max（n 注明，首次 init 冷启动单列）、稳态总丢帧与最长连续丢帧（起止时刻）；VLM 往返 p50/p95（n=180，预热不计入）、失败/超时数；tegrastats GPU/CPU 频率与温度（最小/中位/最大）；峰值 RAM（系统已用、进程 RSS 分列，GiB = 2^30 B）；swap 使用；`dmesg` NvMap/OOM 行。
参考列（只对照、不判过线）：检测 p95 ≤ 100 ms；VLM p95 ≤ 单跑 p95 × 1.3；峰值 RAM ≤ 7.0 GiB；swap 0。

## 5. 停止

**立即停**（账本原文）：`dmesg` 出现 OOM/NvMap 错误；板失联；降频持续 > 60 s。另按本设计停：输入缺失或 sha 不符、缺包、端口被占、任一信封维度将越界或无法计量。
「降频」= devfreq/cpufreq 的 `max_freq` 低于 P0 记录值，或内核出现 thermal 节流记录；工作负载引起的正常调频不算。
停下时：先停本批服务并核端口释放、保存已有原件；**不重跑该臂，也不自动进入下一臂**，报回用户。

## 6. 信封（逐字取账本，计数写 `budget.jsonl`）

板上占用墙钟 ≤ 3 h；VLM 服务加载 ≤ 3 次；VLM 查询 ≤ 400 次；检测器加载 PyTorch ≤ 3 次；TensorRT 引擎反序列化 ≤ 3 次；引擎重建 0；
下载 0；pip/编译/安装 0；传输到板 ≤ 50 MB；板上新增磁盘 ≤ 2 GB；Mac mini 新增磁盘 ≤ 1 GB；Unity/Play 0；scenario·session·run ID 0；云 GPU 0；模型 API 0；系统设置改动 0。
越界任一维即停报用户；未用额度不转用。不做 `nvpmodel -m`、`jetson_clocks`、`systemctl isolate`。

## 7. 产物与交接

运行目录内：`manifest.json`（输入/代码束/脚本 sha、git HEAD、SSH 目标）、`budget.jsonl`、逐臂 `detector-frames.jsonl`、`vlm-calls.jsonl`、`consistency.json`（A1）、tegrastats/内存/dmesg 原件、`summary.json`（两臂对照表 + 第 4 节全部读数 + 偏差/UNKNOWN + 停止原因）。
实现子代理不提交仓库；supervisor 把 `summary.json` 照录为本目录 `cores-diag-results-2026-10-09.md` 并在 §0 写核查。
