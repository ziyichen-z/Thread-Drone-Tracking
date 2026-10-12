# P1-ENG-JET-001 阶段 A 报告（K1K3K4 首派 + K1K3K4补跑 + K1K3K4补跑B + K1K3K4补跑C + K1K3K4补跑D + K1K3K4补跑E + K1K3K4补跑F + K1K3K4全套 + K1K3K4全套CPU1 + K1K3K4证据整理1A + K1K3K4C1返工 + K1K3K4全套SUB6；AC-13）

工作项：`P1-ENG-JET-001`（`Workflow: engineering-v1`）。合同：`docs/proposals/P1-ENG-JET-001-jetson-onboard-feasibility-probe.md`
§2.1 / §3 / §4 与决策记录「§5 阶段 A 信封与 §7 (h)(n) 答复落实」。执行信封：`docs/authorizations.md` 2026-09-28
「P1-ENG-JET-001 — 用户签发 §5 阶段 A 执行信封并答复 §7 (h)(n)…」，派发前提 2026-10-02 同项条目；K1K3K4补跑（S1/S2 容器路径）
依据提案决策记录「S1/S2 容器栈落实」与账本 2026-10-02「用户选 torch 路径 A…」；K1K3K4补跑B（S1/S2 系统栈）依据决策记录
「S1/S2 系统栈落实（B）」、提案「needs_user」题 4（CLARIFY-B2）与账本 2026-10-02「用户按申请值签发 torch/torchvision 下载与安装额度（官方 cu130 源；SUB:1…）」；
K1K3K4补跑C（补装 torch 栈、先验证）另依据决策记录「SUB:3 落实与安装方式合同解释」与账本 2026-10-02「用户按推荐签发 SUB:3…」；K1K3K4补跑D（S1 实跑）依据决策记录「题 6 选 A 落实：装后验证第一项替代判据（AC-2 修订 6）」、「待裁定」IR-16 与账本 2026-10-02「用户选题 6 A…」；K1K3K4补跑E（S2 续跑）依据决策记录「题 7 选 (α) 落实」与账本 2026-10-03「P1-ENG-JET-001 — 用户选题 7 (α)：S1 STOP 记录偏差、以方形 FP16 引擎继续（supervisor 会话代录）」，后续步骤标 `RESUMED_AFTER_USER_RULING(S1)`；K1K3K4补跑F（SR (b) 准备与有线正式 SR）依据决策记录「S2 处置选 (α′) 落实」与账本 2026-10-03「P1-ENG-JET-001 — 用户选 S2 STOP 处置 (α′)：S2 记录偏差并继续，做原范围正式 SR（supervisor 会话代录）」，SR 同时标 `RESUMED_AFTER_USER_RULING(S1)`（指上述题 7 (α) 条目）与 `RESUMED_AFTER_USER_RULING(S2)`（指本条），两者不互相替代；断链手段依账本 2026-10-02「P1-ENG-JET-001 — supervisor 代拍：IR-8 断链手段代选软件定时断链（10 s、60 s，双通道与对时同断）」。

**verdict 是读数，不是验收。** 本报告不含任何验收通过、研究资格或 Jetson 性能主张；所有数字取自下列 JSON，
`TAILSCALE_SMOKE` 读数只作中继实现验证，不进任何结论。

## 1. 每步 verdict（§2.1 闭集）

| 步 | verdict | 证据 |
|---|---|---|
| S0 环境核验 | `PASS` | `docs/evidence/P1-ENG-JET-001-env.json`（`checks`、`readings`、`tegrastats_idle`） |
| S1 快层单测 | **`STOP(FP16_BOX_DIVERGENCE)`**（K1K3K4补跑D，系统栈实跑：方形引擎时延分量过、一致性分量不过；torch 无 sm_87 原生 SASS、按二进制兼容运行，AC-2 修订 6）。前轮历史：补跑C `NOT_RUN(PATH_UNAVAILABLE(system-torch))`（装后验证当时字面未过，IR-16 (a)）；补跑B 同形状（SUB:1 额度将超）；补跑 `NOT_RUN(PATH_UNAVAILABLE(container-tensorrt-sm87))`；首派 `NOT_RUN(PATH_UNAVAILABLE(system-torch))` | `docs/evidence/P1-ENG-JET-001-fastlayer.json`「S1」与 `history` |
| S2 快层热稳态 | **`STOP(FRAME_DROP)`**，`RESUMED_AFTER_USER_RULING(S1)`（账本 2026-10-03「P1-ENG-JET-001 — 用户选题 7 (α)：S1 STOP 记录偏差、以方形 FP16 引擎继续（supervisor 会话代录）」；K1K3K4补跑E，方形 FP16 引擎 15 Hz / 30 min：热降频 0、末/首 p95 比 1.0021 过、丢帧 218 不过）。前轮历史：补跑D `NOT_RUN(S1 STOP FP16_BOX_DIVERGENCE)`（用户裁定前，未回放） | 同上「S2」与 `history` |
| SR 中继（正式 forward/return/disconnect） | **`PASS`**，`RESUMED_AFTER_USER_RULING(S1)` + `RESUMED_AFTER_USER_RULING(S2)`（K1K3K4补跑F，有线 mini 192.168.8.1 ↔ Jetson 192.168.8.2；forward 两轮 100% / 0 / 0，断链轮两次均 60 s 内回稳、无不完整包、两侧不崩溃；读数见 §2f）。返工史：正式轮 f1-echo `STOP(RELAY_INTEGRITY)`（桌面机运行目录残留旧会话指针，返工后在剩余轮数内重跑，§2f）。前轮记录 `NOT_RUN(待用户 (h))`、`NOT_RUN(S1 STOP FP16_BOX_DIVERGENCE)`、`NOT_RUN(S2 STOP FRAME_DROP)` 为当时状态，保留 | `docs/evidence/P1-ENG-JET-001-relay.json`（`forward`/`return`/`disconnect`） |
| SR `TAILSCALE_SMOKE`（非结论，1/1 轮） | 已跑，非结论 | 同上「tailscale_smoke」 |
| S3 VLM 单测 | `NOT_RUN(阶段 B 信封未签)`（现行：用户 (α′) 只放行 SR，阶段 B 全部维度 0；历史：补跑E 时记 `NOT_RUN(S2 STOP FRAME_DROP)`，补跑D 时记 `NOT_RUN(S1 STOP FP16_BOX_DIVERGENCE)`） | `docs/evidence/P1-ENG-JET-001-vlm.json` |
| S4 量化等价 | `NOT_RUN(阶段 B 信封未签)`（现行：用户 (α′) 只放行 SR，阶段 B 全部维度 0；历史：补跑E 时记 `NOT_RUN(S2 STOP FRAME_DROP)`，补跑D 时记 `NOT_RUN(S1 STOP FP16_BOX_DIVERGENCE)`） | `docs/evidence/P1-ENG-JET-001-quant-equivalence.json` |
| S5 共驻 | `NOT_RUN(阶段 B 信封未签)`（现行：用户 (α′) 只放行 SR，阶段 B 全部维度 0；历史：补跑E 时记 `NOT_RUN(S2 STOP FRAME_DROP)`，补跑D 时记 `NOT_RUN(S1 STOP FP16_BOX_DIVERGENCE)`） | `docs/evidence/P1-ENG-JET-001-coresidency.json` |

**SR（K1K3K4补跑F）**：用户选 S2 处置 (α′) 后准备 SR (b) 真实应答器并经有线跑正式 SR；S1、S2 原 verdict 与负结果保留、未重跑。SR 读数是中继的描述性数字与通过线判定，不是验收，也不推出 5 Hz 运行时合同或部署通过。

**S2 `STOP(FRAME_DROP)`（K1K3K4补跑E 原文）**：用户题 7 选 (α) 后续跑 S2（S1 保持 `STOP`、不重跑）；S2 命中 `FRAME_DROP`，按 §2.1 停止全部后续步骤（SR、S3–S5 记 `NOT_RUN(S2 STOP FRAME_DROP)`），写完证据后回接受角色→用户；不借 S1 裁定越过 S2 STOP。

**S1 `STOP(FP16_BOX_DIVERGENCE)`（K1K3K4补跑D）**：按 §2.1 停止全部后续步骤，交接受角色→用户二选一 (α)/(β)（不在 supervisor 代拍闭集内）；无 `RESUMED_AFTER_USER_RULING`（补跑D 当时原文；用户已于 10-03 选 (α)，见上）。以下为前轮原文：首派 S1/S2 的原因形式已由 IR-3 接受；补跑沿用同型 `PATH_UNAVAILABLE(<路径名>)`
（`docs/evidence/P1-ENG-JET-001-K1K3K4-handoff.md`「K1K3K4补跑执行记录」）；补跑B 的原因形式（额度将超致系统 torch 未装成，仍取
`PATH_UNAVAILABLE(system-torch)`）已由 IR-14 接受；补跑C 的停因（装后验证未过）沿用同一形状，是否另记待接受角色确认，见交接「待裁定（补跑C）」IR-16。

## 2. S0 读数要点（`-env.json`）

- 板型/栈：`NVIDIA Jetson Orin Nano Engineering Reference Developer Kit Super`；L4T R39.2；`nvidia-l4t-core 39.2.0`；
  CUDA `13.2.78`（`nvcc`）；TensorRT `10.16.2.10`；Python 3.12.3。
- Super：`/etc/nv_boot_control.conf` 的 `TNSPEC`/`COMPATIBLE_SPEC` 均含 `jetson-orin-nano-devkit-super`。
- 功耗模式：`nvpmodel -q` 当前 = `MAXN_SUPER`（模式号 2；非 root 查询，IR-2）。
- 频率上限：GPU devfreq `max_freq` = 1,020,000,000 Hz（可用最高档同值，调速器 `nvhost_podgov`）；6 核在线，
  `scaling_max_freq` = `cpuinfo_max_freq` = 1,728,000 kHz（`schedutil`）。
- headless：`systemctl get-default` = `multi-user.target`；`display-manager` `inactive`（unit not-found），gdm/gdm3/lightdm/sddm
  均 `inactive`，图形进程 0。
- 空闲 RAM（headless，`tegrastats` 每秒 1 样本、5 min，n = 298）：used max 725 MB / p50 718 MB（总 7,485 MB），线 1,200 MB；
  GR3D 0%；温度 cpu p50 48.41 °C、gpu p50 47.84 °C、tj max 49.12 °C。
- 其他：`free -m` used 805 / available 6,679 MB；**swap 0（无 swap、无 zram）**；根分区可用 170,874,687,488 B；
  NvMap：非 root `dmesg` 被拒，`journalctl -k -b 0` 命中 5 行（均为启动初始化行，含 page pool 935 MB 与一条 ivc-queue property not found 信息行；无 OOM/分配失败行；IR-1）。
- **torch**：系统 `python3 -c "import tensorrt, torch"` → `ModuleNotFoundError: No module named 'torch'`；系统 Python 无 pip；
  板上唯一 torch 在 Docker 镜像 `nvcr.io/nvidia/pytorch:25.08-py3`（33.9 GB；镜像元数据：CUDA 13.0.0、TensorRT 10.13.2.6、
  PyTorch 2.8.0a0），与 JP7.2 系统栈不同。

## 2a. S1/S2 容器栈读数（K1K3K4补跑；`-env.json`「s1s2_container_stack」，与上节 S0 系统栈分列，AC-2 修订 2）

- 镜像 `nvcr.io/nvidia/pytorch:25.08-py3`（`sha256:ace9a848…c50fb`）；容器内实跑：Python 3.12.3、torch `2.8.0a0+34c6371d24.nv25.08`、
  torch CUDA `13.0`、cuDNN 91200、`torch.cuda.is_available()` = True（设备 `Orin`）、TensorRT `10.13.2.6`、ultralytics 8.4.104、
  lap 0.5.13、cv2 4.11.0（headless）、numpy 1.26.4、onnx 1.18.0。
- **容器内 TensorRT 10.13.2.6 不支持 Orin 的 SM 87**：冻结 `.pt` → ONNX 成功（opset 17，10,565,785 B），建 FP16 引擎报
  `Error Code 9: Target GPU SM 87 is not supported by this TensorRT release`；同一 ONNX 用容器 `trtexec --fp16` 复证同错
  （`Compute Capability: 8.7`）。导出前后 `.pt` sha 不变。

## 2b. S1/S2 系统栈安装记录（K1K3K4补跑B；`-env.json`「s1s2_system_stack」，AC-2 修订 5）

- venv：`python3 -m venv --system-site-packages ~/eng-jet/sysvenv`（`include-system-site-packages = true`，Python 3.12.3；dpkg 现为
  `3.12.3-1ubuntu0.17`，S0 记录为 0.15，变化来自用户 10-02 sudo apt，见账本同日条目授权范围 (b)；S0 原文不改写）；`LD_LIBRARY_PATH` 空；
  安装前 `ldconfig -p` 无 cuDSS。
- SUB:1 已取回并留存：官方 cu130 索引 `torch-2.9.1+cu130`（512,448,274 B）与 `torchvision-0.24.1`（7,823,607 B），sha 与题 4 一致。
- 依赖解析（PyPI）共 23 包（torch、torchvision + 21 依赖，与题 4 清单一致，`nvidia-nvshmem-cu13` 解析为 3.3.24、未需 cuDSS），但 pip 24.0
  `install --dry-run --report --no-cache-dir` 把 22 个轮子体完整取回后丢弃（2,318,455,950 B）。SUB:1 已计下载：轮子字节 2,838,727,831 B；
  保守收包口径 3,093,609,695 B（上限 3.5 GB）。补齐安装尚需再取回 2,316,069,213 B → 必超上限，按「任一上限将超即停」停在安装前。
- 因此 torch 未安装：题 4 的安装后验证（`get_arch_list()` 含 sm_87、CUDA matmul 读回、与系统 TensorRT 共存）**未执行**，SM 87 可用性未知。

## 2c. S1/S2 系统栈补装与装后验证（K1K3K4补跑C；`-env.json`「s1s2_system_stack_c」，AC-2 修订 5）

- 安装方式按「SUB:3 落实」：21 个依赖逐个 `pip download --no-deps --only-binary=:all: --no-cache-dir`（单包 `--hash=sha256` 锁定，取回前按
  6.5 GB 上限预检），21/21 sha 与字节一致、合计 2,316,069,213 B；复用留存的官方 cu130 torch/torchvision 轮子；`pip install --no-index
  --find-links` 离线安装 23 包；既有 4 包（ultralytics、lap、ultralytics-thop、opencv-python-headless）离线 `--no-deps` 同版本重装；
  新增 `onnx 1.18.0` + `protobuf 6.31.1`（AC-10 修订 2）。未干跑、未换源、未 sudo/apt。
- 实跑栈（verify 进程内）：Python 3.12.3、torch `2.9.1+cu130`（torch CUDA 13.0、cuDNN 91300）、torchvision 0.24.1、TensorRT `10.16.2.10`
  （系统 `/usr/lib/python3.12/dist-packages`）、设备 `Orin` 算力 (8, 7)；venv `--system-site-packages`，`LD_LIBRARY_PATH` 未设。
- **装后验证（题 4 四项）**：`get_arch_list()` = `sm_80, sm_90, sm_100, sm_110, sm_120, compute_120`，**不含 `sm_87` → 不通过**；
  CUDA matmul 读回（fp32 相对差 2.8e-7、fp16 4.4e-4、全 1 精确）通过；torch 与系统 TensorRT 同进程建小引擎并推理通过；无 torch 干净进程
  建引擎通过。库来源：torch 进程的 CUDA 数学库来自 venv 内 pip 轮子，TensorRT 与驱动来自系统库，无串扰迹象。
- 按合同「任一失败即停下回用户改来源，不在信封内换源」停在 S1 之前：引擎导出 0 次。附加只读诊断（cuDNN conv2d fp32/fp16、torchvision
  CUDA nms、归约）均通过——只供裁定参考，不等于验证通过。
- 消耗（累计见 `-ledger.json`）：SUB:1 23 包、下载保守口径 5,616,357,711 B ≤ 6.5 GB、新增磁盘 7,542,632,760 B ≤ 8 GB；板上 pip 维度 7 包 /
  242,752,639 B ≤ 8 包 / 300 MB；板上磁盘 7,783,123,942 B ≤ 13 GB。

## 2d. S1 系统栈实跑读数（K1K3K4补跑D；`-fastlayer.json`「S1」、`-env.json`「s1s2_system_stack_d」，AC-2 修订 5/6）

- **读数标注（AC-2 修订 6）**：官方 cu130 torch 2.9.1 无 sm_87 原生 SASS，按同主版本二进制兼容（sm_80 cubin）运行；检测推理走原生支持 SM 87
  的系统 TensorRT 10.16。全程无 `no kernel image` 或其他 CUDA 不兼容报错（导出、S1、trtexec 日志逐一检索）。
- 实跑栈（S1 进程内）：Python 3.12.3、torch `2.9.1+cu130`（CUDA 13.0、cuDNN 91300）、torchvision 0.24.1、TensorRT `10.16.2.10`（系统）、
  ultralytics 8.4.104、cv2 4.11.0、numpy 1.26.4、设备 `Orin` (8, 7)；venv `~/eng-jet/sysvenv`（`--system-site-packages`）。环境：运行前 `unset
  LD_LIBRARY_PATH`、`YOLO_AUTOINSTALL=false YOLO_OFFLINE=true`、`YOLO_CONFIG_DIR`/`CUDA_CACHE_PATH` 指 `~/eng-jet/home/` 下（IR-16 (c)）；
  进程内 `LD_LIBRARY_PATH` 由 cv2 轮子 import 时自设为其 `lib64`（如实记录）。
- 装后清理（IR-16 (d)）：导出前删除 `wheels/sub1` 23 个已装轮子 2,836,341,094 B（只删轮子、未动 sysvenv）。
- 引擎（导出前后 `.pt` sha 一致 `d6a0d6a9…`；`half=True`、`dynamic=False`、`workspace=None`、`simplify=False`）：方形 640 sha `5e45529a…`
  8,459,869 B、导出 375.4 s；矩形 480×640 sha `c047cc34…` 8,379,885 B、导出 367.9 s（各 ≤ 20 min）。
- **方形引擎（verdict 对象，n = 320）**：`update` p50 33.65 / **p95 59.29** / max 116.59 ms → 时延分量过（≤ 200 ms），`within_50ms = false`；
  分项：检测 p50 16.16 / p95 22.87 ms，GMC p50 12.24 / p95 39.02 / max 95.13 ms，关联器 p50 1.94 / p95 2.67 ms；`trtexec` GPU Compute
  中位 4.74 / p95 4.75 ms；CPU 占用 81.5%（一核 = 100%）；RSS 1,726.9 MB；`tegrastats` RAM used max 2,730 MB（两次 S1 窗口，n = 47）。
- **方形引擎一致性（对 frozen-V，MPS）**：帧 0…49 检测数不一致 **3** 帧；帧 1…320 配对框归一化最大差 **0.0992**（限 1e-3）；两侧未配对
  **66**（引擎 21、参照 45；配对 710；IoU 最小 0.639）；321 帧中不一致帧 284（清单、IoU 直方图、逐帧最大差直方图见 `-fastlayer.json`
  `S1.engines.640.s1.comparison`）→ 一致性分量不过 → **`STOP(FP16_BOX_DIVERGENCE)`**。
- 矩形引擎（同口径单独报告，不进 verdict）：`update` p50 34.49 / p95 58.95 ms；检测 p95 19.91 ms；GMC p95 40.04 ms；`trtexec` 中位 3.92 ms；
  一致性：帧 0…49 计数不一致 0（全 321 帧亦 0）、未配对 0、配对最大差 0.0259、超 1e-3 的帧 17 → 同样未达 1e-3 线。
- 插件状态（两引擎同）：ok 29 / lost 291（init 框为 G-7 离线用户框替身，IR-5；不作捕获或身份主张）。
- **差异来源的可能解释（未验证、不改 verdict、不改阈值）**：帧 0（init 帧）方形引擎与参照已差 2.2e-3，矩形引擎仅 6.5e-5。frozen-V 头部为
  `device mps`、`imgsz 640`，由 `.pt` 经 ultralytics 推理产生；ultralytics 对 `.pt` 推理 640×480 帧时按最小填充的矩形 letterbox，而静态方形
  引擎填充到 640×640——输入形状不同可能是方形引擎偏差（含未配对与计数不一致）的主因；矩形引擎形状一致后残余差（最大 0.026）则属 FP16/TRT
  对 MPS 的数值差异。本轮未做任何额外运行验证该解释。
- 消耗（累计见 `-ledger.json`）：板上墙钟 3,783 s ≤ 8 h；引擎导出 2 次（本轮）；SUB:1 下载 5,616,357,711 B（不回退）、新增磁盘按清理后重计
  4,925,758,840 B ≤ 8 GB；板上磁盘 5,166,250,549 B ≤ 13 GB；本轮零下载、零安装、零到板传输；Mac 零 pip、零模型。

## 2e. S2 系统栈热稳态（K1K3K4补跑E；`-fastlayer.json`「S2」、`-env.json`「s2_system_stack_e」；`RESUMED_AFTER_USER_RULING(S1)`）

- **续跑依据**：账本 2026-10-03「P1-ENG-JET-001 — 用户选题 7 (α)：S1 STOP 记录偏差、以方形 FP16 引擎继续（supervisor 会话代录）」与决策记录「题 7 选 (α) 落实」；S1 保持 `STOP(FP16_BOX_DIVERGENCE)`，本轮不重跑 S1、不重导出、不换矩形引擎。S1 方形 p95 59.29 ms > 33 ms → 只测 15 Hz（`S2.plan.add_30hz = false`）。
- **读数标注（AC-2 修订 6）**：官方 cu130 torch 2.9.1 无 sm_87 原生 SASS，按同主版本二进制兼容（sm_80 cubin）运行；检测推理走系统 TensorRT 10.16（实跑 `10.16.2.10`，设备 `Orin` (8, 7)）。日志无 `no kernel image`、无 CUDA 报错。
- **引擎**：补跑D 方形 FP16 引擎，sha 运行时从 `-fastlayer.json`「S1.engines.640.export.sha256」解析，开跑前板上复核一致（`S2.engine_identity_check`、`S2.engine_sha_at_start`）；使用前复核 335/335 一致（`-assets.json`「round_e_pre_use_check」）。
- **TRT 告警（如实记录，交接受角色裁定读法，见交接 IR-20）**：加载引擎时 TensorRT 打出一条 `[W]` 级告警「Using an engine plan file across different models of devices is not supported…」，补跑D 同一引擎加载时无此行；板子在两轮之间重启过。同板、同引擎 sha、`[W]` 级而非错误，推理全程正常；只读诊断（设备名 `Orin`、SM 8.7、8 SM、`total_memory` 7,849,054,208 B）见 `-env.json`「s2_system_stack_e.trt_plan_device_warning」。本角色未据此停跑、未重导出。
- **六个 5 min 格**（`update` n / p50 / p95 / max ms，丢帧；GPU 上限 / CPU 上限；tj 最高温；VDD_IN p50/max mW）：

| 格 | n | p50 | p95 | max | 丢帧 | GPU 上限 MHz | CPU 上限 MHz | tj 最高 °C | VDD_IN p50 / max mW |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 4407 | 40.746 | 66.993 | 126.739 | 78 | 1020 | 1728 | 50.968 | 6379 / 6658 |
| 1 | 4458 | 40.724 | 67.148 | 127.744 | 28 | 1020 | 1728 | 51.156 | 6379 / 6618 |
| 2 | 4458 | 40.855 | 67.169 | 126.824 | 28 | 1020 | 1728 | 51.343 | 6379 / 6618 |
| 3 | 4458 | 40.749 | 67.453 | 129.004 | 28 | 1020 | 1728 | 51.312 | 6379 / 6658 |
| 4 | 4458 | 40.791 | 67.158 | 126.642 | 28 | 1020 | 1728 | 51.343 | 6379 / 6738 |
| 5 | 4458 | 40.687 | 67.131 | 126.511 | 28 | 1020 | 1728 | 51.468 | 6379 / 6767 |

- **verdict = `STOP(FRAME_DROP)`**（AC-3 修订 1 三项合取）：热降频事件 0（GPU `max_freq` 全程 1,020 MHz、6 核 `scaling_max_freq` 全程 1,728 MHz、CPU/GPU 热限频 cooling 状态全程 0，风扇及其余告警 cooling 状态亦全程 0；频率读数无缺失）；末/首 5 min p95 67.131 / 66.993 = 1.0021 ≤ 1.2；**丢帧 218 ≠ 0**。共 26,697 次 `update`、85 次周期 init（0 拒绝），Sampler 1,778 样本，tegrastats 1,797 行（RAM used p50 2,090 / max 2,125 MB，总 7,485 MB）。
- **丢帧分布（描述，不改 verdict、不改判据）**：50 帧来自第一次 init（含进程冷启动，3,452.8 ms）；其余 168 帧在 84 个后续回放周期（每周期 321 帧）内固定两处（周期内 init 后约 19.0 s）各丢 1 帧，前一次 `update` 约 101 ms / 126 ms。即便不计冷启动，丢帧仍非 0。另：`update` 超过 15 Hz 节拍（66.7 ms）但未落后满一帧（按线束 `count_drops` 口径不计丢）的有 1,529 次（n = 26,697）。
- AC-16：本项 Python 进程启动前 `MPLCONFIGDIR=/home/jetson/eng-jet/home/mpl`（实际环境记录 `env-actual.txt`），字体缓存落在 `~/eng-jet/home/mpl/fontlist-v330.json`；`YOLO_CONFIG_DIR`/`CUDA_CACHE_PATH` 继续指 `~/eng-jet/home/`，`LD_LIBRARY_PATH` 运行前 unset；S2 启动前 marker 之后 `~/eng-jet` 外新写入 0（`outside_eng_jet.newer_than_marker` 为空；既有外部缓存未变、未删）。
- 清理（IR-19）：S1、S2 均有读数后删除容器 `~/eng-jet/venv`（1,796 文件 / 101,751,706 B，`du -sb ~/eng-jet` 5,172,051,851 → 5,070,463,807），未动 sysvenv；pip 包数与下载字节不回退；`wheels` 保留待接受角色补记录。
- 消耗（累计见 `-ledger.json`）：板上墙钟本轮 +1,983 s（累计 5,766 s ≤ 8 h）；到板 1,469 B（两个运行脚本，累计 18,315,944 B）；引擎导出 0；零下载、零安装；板上磁盘 5,070,463,807 B；SUB:1 新增磁盘重计 4,829,972,625 B ≤ 8 GB；Mac 零 pip、零模型。

## 2f. 正式 SR（K1K3K4补跑F；`-relay.json`「forward」「return」「disconnect」「rework_rounds」，`-env.json`「sr_system_stack_f」；`RESUMED_AFTER_USER_RULING(S1)` + `RESUMED_AFTER_USER_RULING(S2)`）

- **链路与执行**：桌面端 Mac mini（只跑 5 Hz 回放器与中继，零模型、零 pip）↔ Jetson 有线直连，板侧中继 bind 192.168.8.2:47811；ssh 一律 `jetson@192.168.8.2` + `BatchMode=yes` + `StrictHostKeyChecking=yes`，未改 `~/.ssh/*` 与网络/隐私设置。每轮回放 a7 帧 0…1,499（1,500 帧，发布字节逐帧对 FAST-002 参照一致，`-assets.json`「round_f_sr_frames」）。板上中继与两种应答器均以 `~/eng-jet/sysvenv` Python 运行，AC-16 环境四轮全部符合（`sr_system_stack_f.ac16`）。
- **SR (b) 真实应答器**（`tools/eng_jet/track_responder.py`）：真实 `TrackLoop`（`controller/` 零改动，condition follow、ground plane 0.2）+ 补跑D 方形 TRT FP16 插件；引擎路径/sha 运行时从 `-fastlayer.json`「S1.engines.640.export」解析，板上使用前 30 件复核全一致（`-assets.json`「round_f_pre_use_check」）且每轮开跑前应答器再核一次（`engine_identity_ok`）。**init 框 = 板上首帧（frame 0）检测器自身 target 类最高分框** `[0.4432617, 0.7078776, 0.0578613, 0.1536458]`（score 0.94854，该帧检测 2 个、target 类 1 个），不读真值、不用离线用户框替身。
- **读数标注**：AC-2 修订 6（官方 cu130 torch 2.9.1 无 sm_87 原生 SASS，按同主版本二进制兼容（sm_80 cubin）运行；检测走系统 TensorRT 10.16）；IR-20 / AC-2 修订 7：每次加载方形引擎仍各出现 1 条 TRT `[W]` 引擎计划跨设备告警，原因与影响未核实，不宣称无影响；全程无 CUDA/TRT 不兼容错误、反序列化/推理失败或身份不符。
- **返工轮 f1-echo = `STOP(RELAY_INTEGRITY)`**：桌面机运行目录残留 10-02 冒烟会话的 `latest.json`（frame 1499），桌面机中继启动即转发；板侧发布后本会话帧 0…1499 全部按顺序违反被拒（板侧顺序与不完整包守卫按设计生效）。返工：桌面机中继跳过发布时刻早于本进程启动 5 s 以上的指针（回归测试修前红、修后绿），编排在启动中继前清空运行目录。该轮计入 SR 轮数，原始收据保留在 `-relay.json`「rework_rounds」。
- **forward（全程零链路事件轮，分母 = 发送端实际送出包数）**：

| 轮 | 应答器 | 送出 | 板上完整发布（sha 一致） | 顺序违反 | 指向不完整包 | 到达时延（偏差校正）p50 / p95 / max ms（n） | 未校正 p50 / p95 ms | 偏差 板−桌面 中位 ms（n） | 漂移 ppm | RTT 中位 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| f2-echo | 回声 | 1,500 | 1,500（100%） | 0 | 0 | 11.919 / 16.245 / 17.364（1,500） | 20.802 / 25.162 | 8.909（328） | −2.454 | 0.913 |
| f3-track | 真实 TrackLoop | 1,500 | 1,500（100%） | 0 | 0 | 12.753 / 16.690 / 25.707（1,500） | 20.560 / 24.535 | 7.851（328） | −2.437 | 0.983 |

- **return**（nearest-rank，附 n）：

| 模式 | 回程时延 p50 / p95 / max ms（n） | 端到端 p50 / p95 / max ms（n） | `capture_age_s` p50 / p95 / max（n；超 `T_STALL_S` 3.0） | 偏差校正后 p95 | `load_elapsed_s` p50 / p95 / max（n；超 `T_pub` 0.4） |
|---|---|---|---|---|---|
| 回声（f2） | 3.393 / 5.644 / 6.371（1,500） | 18.661 / 23.783 / 29.207（1,500） | 0.0251 / 0.0298 / 0.0325（1,500；0） | 0.0209 | 0.00191 / 0.00306 / 0.00948（1,500；0） |
| 真实（f3） | 2.804 / 6.117 / 6.156（29） | 65.583 / 239.633 / 593.341（29） | 0.0250 / 0.0291 / 0.1948（1,498；0） | 0.0213 | 0.04616 / 0.0549 / 0.05547（28；0） |

  真实模式 TrackLoop 逐帧 `frame_age_ms`（板墙钟 − `capture_unix_s`）p50 78.714 / p95 124.94 / max 604.211 ms（n = 1,500），超 `T_stall` 0（比例 0.0）；偏差校正后 p95 117.219 ms。真实模式插件第 0…29 帧 `TRACKING`，第 30 帧起 `bound_track_unmatched` → `bound_track_removed`，compat 模式不改绑，故回程观测只有 29 个（统计力弱，只作描述）；端到端含 init 冷启动后的追帧（`batches_over_1` = 1）。
- **disconnect（f4，真实 TrackLoop；软件定时断链，双通道与对时同断，IR-8 / D5）**：本轮送出 1,152 包、板上完整发布 1,152（分列、不进 forward 结论），顺序违反 0、指向不完整包 0、sha 不符 0，两侧进程与应答器全部正常结束（退出码 0）。

| 断链 | 实测时长 s | 断链期间板侧写桥（成员 / latest / 回程 / 应答器写） | 恢复后 frame_id 缺口 | latest 帧差 | 不补发过期帧 | 稳态阈值 ms（基线 n） | 回稳 s（≤ 60） | TrackLoop |
|---|---|---|---|---|---|---|---|---|
| 10 s（60 s 处） | 10.004 | 0 / 0 / 0 / 0 | 49 | 50 | 是（只发重连时当前 latest 332） | 16.203（283） | 0.134 | 重连后第一帧即 `GAP`（`retained_intermediate_frame_missing`）终止；应答器不重播种、继续存活（之后记到达新帧 868 次） |
| 60 s（160 s 处） | 60.001 | 0 / 0 / 0 / 0 | 299 | 300 | 是（只发 1082） | 15.340（300） | 1.940 | 已于第一次断链后终止，保持终止 |

  回稳读法在正式断链轮运行前写定于 `tools/eng_jet/relay.py` `RECOVERY_*`（基线 = 断链前 60 s 偏差校正到达时延 p95；连续 10 帧 ≤ 阈值即回稳）。
- **意外链路事件（如实记录）**：板侧内核日志 16:52:11–16:52:14Z `enP8p1s0` 物理链路 down/up 一次（f3 板侧中继 16:52:04Z 结束之后、f4 开始之前，不在任何 SR 数据窗内），同时段一次 ssh 连接超时；原因未查明，未改任何网络设置。板上 NTP 已同步（`timedatectl`），无 chrony。
- **AC-12**：真实 TrackLoop 写出的 `gimbal_command.json`（冻结控制协议字段 `target_world_m`，由检测框几何求得的 look-at 世界点，非真值）命中内容禁键 `target_*`，按 IR-17 现行读法记 2 条真正违规（f3、f4 运行目录各 1），未删除、未改名绕扫描，读法交 IR-22；`ac12_clean: false` 原样。受保护根（主树 `runtime/`、mini 数据根）本轮零写入。
- 消耗（累计见 `-ledger.json`）：板上墙钟本轮 +2,779 s（累计 8,545 s ≤ 8 h）；SR 轮 4（累计 5 / 5，**已耗尽**；每轮 ≤ 61,704,978 B ≤ 100 MB）；到板 554,765 B（累计 18,870,709 B）；零下载、零安装、零引擎导出；板上磁盘 5,163,883,873 B；Mac 零 pip、零模型（outputs 70,218,799 B）。

## 2g. 合同读法同步与停点全套跑前核对（K1K3K4全套；Mac mini 离线，零上板）

依据提案决策记录「SR 与补跑F记录核对（2026-10-03）」（AC-4 修订 2、AC-5 修订 1）、「待裁定」IR-21 / IR-22（AC-12 修订 3 / 4）与「SUB:2 落实：§5 Mac 与 IR-9（2026-10-03，CLARIFY）」；账本 2026-10-03「P1-ENG-JET-001 — 用户按推荐签发 SUB:2：停点全套的 Mac 本机 CPU 模型额度（一次全套）（supervisor 会话代录）」。本轮不重跑 S1/S2/SR、不上板、不新增清理；S1 `STOP(FP16_BOX_DIVERGENCE)`、S2 `STOP(FRAME_DROP)`、SR `PASS` 及其 `RESUMED_AFTER_USER_RULING(S1)` / `(S2)` 双标与 IR-20 告警影响未明的限制全部不变。

- **AC-12（IR-21/22 分列，`-assets.json`「board_manifest.ac12_split.ir21_ir22_reading」）**：原扫描 `violations`（3 条）、`true_violation_count = 2`、`ac12_clean: false` 与原扫描指针原样保留；从 `true_violations` 运行时解析出具名两条控制协议内容命中（f3-track、f4-track-drops 板上运行目录的 `gimbal_command.json`，字段 `command.target_world_m`，真实 TrackLoop 的 look-at 控制输出、非 smoke 真值）单列，扣除后真正隔离违规 0 条。真实应答器逐帧记录（本机取回副本 f3 1,500 行、f4 284 行）键均为 `loop_state`、AC-12 内容禁键命中 0（IR-21）。**本分列不宣称 AC-12 已验收**，是否满足由核对/独立复核判定，复核仍须核实来源。
- **AC-4 修订 2（`-relay.json`「contract_readings_full_suite.ac4_rev2」）**：f2-echo / f3-track 收据各 1 次启动 connect 与 1 次收工 disconnect（OSError / TimeoutError）原样保留，传输中事件 0；末次送包 16:43:08 / 16:50:19Z、收工断开 16:43:35 / 16:50:49Z，1,500 个送包全部计数、计数窗不缩短。16:52:11–16:52:14Z 板侧物理链路 down/up 在 f3 结束后、f4 开始前，原因未明，**不能据 SR `PASS` 外推链路长期稳定**。
- **AC-5 修订 1（同上「ac5_rev1」）**：分母分列——回声回程/端到端/`capture_age_s`/`load_elapsed_s` 均 n = 1,500；真实回程与端到端 n = 29，逐帧 `frame_age_ms` n = 1,500，`capture_age_s` n = 1,498，`load_elapsed_s` n = 28，`processing_elapsed_s` n = 1,498。n = 29 源于第 30 帧起绑定目标丢失且 compat 不改绑，回程不含 init 帧；init 为首帧检测器自身 target 类最高分框、非真值。不把 n = 29 当成长段统计或持续跟踪通过。
- **SUB:2 与停点全套（`-ledger.json`「envelope.sub2」「dimensions.mac.sub2」）**：已按授权标题与 request_id `P1-ENG-JET-001:b0a5f79c:SUB:2` 入账；跑前只读核对（`dimensions.mac.sub2.prechecks`）预计按合同指定的数据根 `.venv-yoloe` 跑全套时，四种具名模型加载均为 0（主树无 NanoTrack/YOLOE/DINOv2 模型文件，opencv 5.0.0 无 CSRT 构造函数），但 `tests/test_det_assoc_carrier.py::CarrierSelfTest` 两例会真实加载 det-assoc 冻结检测器（ultralytics YOLO `last.pt`）共 2 次——不在 SUB:2 四种具名模型内（未列名额度 0）。按「预计超任一额度即不跑」**全套未运行**（一次全套额度未消费），四种模型实际加载 0 / 0 / 0 / 0，Mac pip 0、下载 0。另：同文件 `ResidentCarrierReplay` 为零模型但其文档写明计入 `P1-ENG-ACQ-001` 消耗账本 2 次部分序列回放，一并交用户。（以上为 K1K3K4全套 收工时状态；其后用户签 SUB:5 A 并选 CPU-1，停点全套已于 K1K3K4全套CPU1 运行一次，见 §2h——本条「全套未运行」不是现状。）

## 2h. CPU-1 测试改动与停点全套一次（K1K3K4全套CPU1；Mac mini 离线，零上板）

依据提案决策记录「CPU-1 落实与下一实现范围（2026-10-03，CLARIFY）」（AC-10 修订 6）与「SUB:5 A 落实与 CPU 执行方案核对」（AC-10 修订 5）；账本 2026-10-03「P1-ENG-JET-001 — 用户选 SUB:5 CPU 执行方案 CPU-1…」「…用户选 SUB:5 方案 A…」「…用户按推荐签发 SUB:2…」。S0 `PASS`、S1 `STOP(FP16_BOX_DIVERGENCE)`、S2 `STOP(FRAME_DROP)`、SR `PASS`（双 `RESUMED_AFTER_USER_RULING`）与 IR-20 限制不变；本节是仓库回归测试读数，不是 Jetson 性能读数。

- **测试改动**：仅 `tests/test_det_assoc_carrier.py:CarrierSelfTest` 两例改用既存 `DetAssocTracker(spec_path=SPEC, device="cpu")` 与必要导入（静态 AST 核对：其余流程、16 个断言调用与 skip 门不变）。两例因此不再经过 `create_tracker` 工厂（用户已认可的覆盖损失）。
- **一次全套**（数据根 `.venv-yoloe`，无 `-v`、无附加环境变量，不重跑）：`Ran 2136 tests in 235.682s`，`FAILED (failures=27, errors=10, skipped=56)`（`docs/evidence/P1-ENG-JET-001-full-suite.log`）。相对 FRAME-001 R7 基线：已有 7 条仍在（导入错误 5：四个 eng_sft 报 `tests.fixtures` 缺失、language_k_binding 报 `tests.test_language_selector` 缺失；CSRT 2），18 条未出现（12 条为 R7 沙箱 loopback 拒绝、6 条有缺归档静态 skip 门——「转为 skip」是静态门归因，无逐名 skip 日志，不称修复/通过；skip 19→56 只有聚合可比），**新增 30 条**——`CarrierSelfTest` 首例 CPU 与 MPS 参考逐帧比较在 767 个 update 条目中 10 个不完全相等（不一致索引从 0 计 `[2, 4, 5, 6, 8, 12, 17, 18, 19, 20]`；索引 2 = `frame_id=3` 的首个差异为 box 宽约 4.8e-8、state/reason 相同，只适用于该条，其余 9 条形态未知；比较后的 confidence_source、观测桥字段集、临时目录外写入断言未执行），以及 `test_scene006_probe` 29 条（25 FAIL + 4 ERROR；读码归因本机主树缺 re-anchor/NanoTrack 权重，冻结处置链在首个 YOLOE 权重哈希检查即拒绝 → `FAIL_WEIGHT_HASH`，相关代码相对 R7 零 diff；未在补齐资产环境验证）。逐名分列见交接「K1K3K4全套CPU1执行记录与停点自证」。
- **消耗（`-ledger.json`「dimensions.mac.sub2」「dimensions.mac.sub5」）**：全套 1 / 1；det-assoc 冻结检测器加载 2 / 2（CPU）；具名零模型部分回放 2 / 2（归本项、不扣 ACQ-001）；NanoTrack 2（构造尝试上界、读权重 0）、CSRT 2（实例 0）、YOLOE 0、DINOv2 0；其他模型 0；Mac pip 0、下载 0；`within_envelope: true`。
- 停点自证第 2 项不成立（本批新增失败），**未送 `C1@K1K3K4`**；处置读法交接受（IR-24/25）后转用户。（以上为 K1K3K4全套CPU1 收工时原文。）
- **执行版本读法（K1K3K4证据整理1A，AC-13/14）**：执行起始版本沿主题 `^P1-ENG-JET-001 K1K3K4全套CPU1 开工` 解析；`-ledger.json` 的 `full_suite_run_items[].tested_head` / `git_diff_assets_controller_config.head_at_build` 所在提交时间在全套窗口内，是另一取样时点、不是跑前 HEAD 采样；两者 tests/tools/controller/Assets/config 零 diff，只证明运行代码相同。原字段不改写。
- **用户裁定后（K1K3K4证据整理1A）**：用户 10-03「1A，2环境分列」，接受落实为 AC-10 修订 8 / AC-13 修订 3：Carrier 该例作本停点测试条件的**具名例外**携带进 `C1@K1K3K4` / `R1@K1K3K4`，scene006 29 条按本机环境原因分列、仍记相对 R7 新增；均**不记测试通过**，复核可判阻断，不新增任何额度、不重跑。实现角色已冻结完整候选并重判四项成立，交接受 `C1@K1K3K4`；见交接「K1K3K4证据整理1A：候选冻结与停点自证」。本节是仓库回归测试读数，不是 Jetson 性能读数。（以上为 K1K3K4证据整理1A 收工时状态。）
- **核对退回后（K1K3K4C1返工，现行）**：`C1@K1K3K4` 首次退回唯一项 C1-AC13-1（§5 现状/历史歧义）；本轮只做报告现状/历史分列（§5、§2g、本节、§6），不改测试读数、例外读法或计账；候选按交接「K1K3K4C1返工：报告现状/历史分列与候选重冻结」重冻结并交 `C2@K1K3K4`。

## 2i. 新候选停点全套一次（K1K3K4全套SUB6；Mac mini 本机，零上板）

依据提案决策记录「SUB:6 落实与新候选两项例外（2026-10-04，CLARIFY）」（AC-10 修订 9/10、AC-13 修订 4）与账本 2026-10-04「P1-ENG-JET-001 — 用户签发 SUB:6…」。新候选 = R1-1…4 补丁（`K1K3K4R1注记修补`），补丁未上板；本节是仓库回归测试读数，不是 Jetson 性能读数，S0/S1/S2/SR 读数与 `STOP` 标记不变。

- **一次全套**（数据根 `.venv-yoloe`，无 `-v`、无附加环境变量，不重跑；2026-10-04T01:55:20Z–01:59:14Z）：`Ran 2146 tests in 231.849s`，`FAILED (failures=27, errors=10, skipped=56)`（`docs/evidence/P1-ENG-JET-001-SUB6-full-suite.log`）。相对 R7：已有 7 仍在、18 未出现（不称修复/通过）、新增 30 = Carrier 1 + scene006 29；相对 CPU1 全套：失败名、类型与失败详情逐项相同，新增 10 例（R1 补丁）无失败。两项新增均在用户为新候选重新具名的例外（Carrier AC-10 修订 10、scene006 AC-13 修订 4）同名同类边界内，**不记通过**；例外外新增 0。
- **消耗（`-ledger.json`「dimensions.mac.sub6」）**：全套 1/1；det-assoc CPU 加载 2/2；部分回放 2/2（各 60 帧，零模型，归本项）；NanoTrack 2 上界/读权重 0；CSRT 2 上界/实例 0；YOLOE/DINOv2/其他 0；`outputs/eng-jet` +3,853 B（仅记账事件，全套本身 0 B）；墙钟 349 s；pip/下载/上板/SR 0。SUB:2/SUB:5 原计数不变。
- 实现角色重判四项成立，交接受只读核对，之后独立 `R2@K1K3K4`；见交接「K1K3K4全套SUB6：新候选停点全套一次、计账与停点自证」。

## 3. Q1–Q4

- **Q1 快层（补跑E 热稳态）**：用户选 (α) 后，方形 FP16 引擎 15 Hz / 30 min 下六格 p95 66.99–67.45 ms、末/首比 1.0021、无热降频（频率上限全程不变，tj 最高约 51.5 °C，VDD_IN p50 约 6.4 W），但丢帧 218 → S2 `STOP(FRAME_DROP)`；丢帧集中在首次 init 冷启动与每回放周期内固定两帧（§2e）。
- **Q1 快层**（K1K3K4补跑D 原文）：系统栈方形 TRT FP16 引擎 `update` p95 59.29 ms（门 200 ms 过、50 ms 参考线未过），GMC 是最大分项（p95 39.02 ms），GPU 推理本身（trtexec 中位 4.74 ms）很小；但对 frozen-V 的一致性不过（计数不一致 3、最大差 0.0992、未配对 66），S1 记 `STOP(FP16_BOX_DIVERGENCE)`，S2 未运行，无热稳态数字。前四轮无数字的原因见 §2a–§2c。
- **Q2 VLM**：无数字（阶段 B 未签）。
- **Q3 共驻**：无数字（阶段 B 未签）。
- **Q4 中继（K1K3K4补跑F，有线正式轮，`RESUMED_AFTER_USER_RULING(S1)` + `(S2)`）**：mini ↔ Jetson 有线下 forward 两轮完整率 100%、顺序违反 0、指向不完整包 0；到达时延（偏差校正）p95 约 16.2–16.7 ms（n = 1,500 ×2）；两机墙钟偏差（板 − 桌面）中位 7.9–8.9 ms、漂移约 −2.4 ppm、RTT 中位约 1 ms；回程 p95 回声 5.6 ms（n = 1,500）/ 真实 6.1 ms（n = 29）；端到端 p95 回声 23.8 ms / 真实 239.6 ms（n = 29，含 init 后追帧）；`capture_age_s` p95 约 0.03 s ≪ `T_STALL_S` 3.0，`load_elapsed` p95 回声 3 ms / 真实 55 ms ≪ `T_pub` 0.4 s，真实 `frame_age_ms` p95 124.9 ms、超 `T_stall` 0；10 s / 60 s 断链期间板侧零写桥、不补发过期帧，恢复后 0.13 s / 1.94 s 回稳，真实 TrackLoop 在第一次重连时以 `GAP` 终止（§2f）。只代表 mini ↔ Jetson 有线直连。
- **Q4 中继（冒烟原文）**：正式轮无数字（链路未接，`NOT_RUN(待用户 (h))`）。冒烟读数（Tailscale/WiFi，1,500 帧回放、回声应答，**非结论**）
  见 `-relay.json`「tailscale_smoke.analysis」：发出 1,425 包、板上完整发布 1,413、在途整包丢失 12（真实链路停顿约 33–42 s）、
  顺序违反 0、`latest.json` 指向不完整包 0、sha 不符 0；两机墙钟偏差（板 − 桌面）中位 89.1 ms（n = 32，样本跨度 34.2 s）；
  到达时延（偏差校正）p50 69.4 / p95 613.0 / max 4,337.3 ms（n = 1,413）；回声回程 p50 36.5 / p95 79.3 ms；端到端 p50 110.9 /
  p95 716.1 ms；`capture_age_s` p95 0.703 s、超 `T_STALL_S 3.0` 1 次；`load_elapsed` p95 2.9 ms、超 `T_pub` 0 次。

## 4. 建议（只依据已测读数）

1. **板上 VLM 可否成立 / 哪条运行时**：仍无任何板端 VLM 读数（阶段 B 未签），不给结论；快层已有 S1/S2 读数（均 `STOP`，§2d/§2e）与 SR 真实模式读数（§2f）。按 §5 / §7 (n)，阶段 B 申请的前提（S0–S2 `PASS`）未满足（S1、S2 为 `STOP`、经用户裁定续跑）；是否仍申请阶段 B 属用户决定，本报告不代拟。
1a. （补跑E 前原文）**板上 VLM 可否成立 / 哪条运行时**：本轮无任何板端 VLM 或快层读数，不给结论；阶段 B 申请的前提（S0–S2 `PASS`）尚未满足。
2. **S2 `STOP(FRAME_DROP)` 的处置**：用户已于 10-03 选 (α′)（账本见文首），S2 保持 `STOP`，SR 已按放行范围执行（§2f）。以下为补跑E 原文——按 §2.1 停全部后续、回接受角色→用户；§2.1 S2 行只预注册 STOP 处置，本报告不自行给出继续或放宽。读数侧事实：热与时延比值两项都过，丢帧来自首次 init 冷启动（50）与每周期固定两帧（168），15 Hz 节拍下 p95 约 67 ms 已贴近 66.7 ms 帧周期。
2a. **S1 一致性 STOP 的处置（补跑D 原文；用户已于 10-03 选 (α)）**：(α) 记录偏差、以该 FP16 方形引擎继续（S1 保持 `STOP`，后续标 `RESUMED_AFTER_USER_RULING(S1)`，阈值与引擎精度不改）；(β) 关闭本项。读数侧可供参考的事实：时延分量远低于 200 ms 门；矩形引擎（与参照输入形状一致）无计数不一致、无未配对，最大差 0.026；方形引擎偏差可能主要来自输入形状而非 FP16（§2d 解释，未验证）。本项不自行放行、不换引擎、不改阈值。
3. **交 `P1-ENG-ACQ-001` 的接口发现（K1，正式轮读数）**：(a) 有线 mini ↔ Jetson 两机墙钟偏差中位仅约 8–9 ms（板上 NTP 同步），`capture_age_s` p95 约 0.03 s，门 ⑤ 的跨机偏差在本链路下远小于 `T_stall`；但偏差大小取决于两机对时，冒烟（Tailscale）曾见约 89 ms 且链路停顿时单帧达数秒，新鲜度门是否改为「中继到达相对年龄」仍属 ACQ-001 K1。(b) 中继按合同「不补发过期帧」，而 compat `TrackLoop` 要求帧号连续——**任一次断链（≥ 1 帧缺口）都会使 TrackLoop 以 `GAP` 终止**，需人工重新初始化；ACQ-001 若沿用中继，须在其 K1/K3 决定缺口语义（本项不改）。(c) 真实模式下 compat 插件在 a7 第 30 帧后丢失且不改绑（与 ACQ-001 立项动机一致，非本项结论）。以下为候选原文——跨机后门 ⑤ 的 `capture_age_s` 直接含两机墙钟偏差
   （冒烟中位约 89 ms，链路停顿时单帧可达数秒），新鲜度门是否改为「中继到达相对年龄」属 ACQ-001 K1；本项不改门。
   板上快层若走控制器常驻进程同样依赖 torch/ultralytics，路径选择会传导到 ACQ-001 的上板形态。
4. 板上无 swap/zram：S5「swap 使用 0」天然满足，但 8 GB 上 OOM 无缓冲，S5 前宜知悉（不改系统设置）。

## 5. 不可推出

- （补跑F）SR 读数只代表 mini ↔ Jetson 有线直连、本板本栈、a7 帧 0…1,499 的 5 Hz 回放与本次两种应答器；不能推出 Unity Play 下的门通过率、缆内链路或其他网络的时延/完整率，也不能推出 5 Hz 运行时合同下快层无丢帧或部署通过；真实模式回程 n = 29，不能推出更长跟踪段的回程分布；SR `PASS` 不改写 S1/S2 的 `STOP`；回稳读法是本轮预注册的描述口径，不是合同新阈值；16:52Z 链路抖动原因未查明，不能推出链路稳定性结论；
- （现行，K1K3K4C1返工 分列）任何 VLM、共驻结论：S3–S5 现为 `NOT_RUN(阶段 B 信封未签)`，无板端 VLM/量化等价/共驻读数；中继 SR 已于补跑F 运行并记 `PASS`，其可推出范围只限上条所列（不推出部署通过、Unity Play 门通过率或其他链路结论）；
- （补跑E 原文，补跑E 收工时点：当时 SR 与 S3–S5 均记 `NOT_RUN(S2 STOP FRAME_DROP)`；该时点之后 SR 已于补跑F 运行 `PASS`，本条括号内「SR 未运行」只代表当时状态、不是现状）任何 VLM、共驻、中继正式轮结论（SR、S3–S5 未运行）；
- （现行限制，照旧）S2 读数只代表本板本栈、方形 FP16 引擎、a7 前 321 帧循环回放、15 Hz 单进程、MAXN_SUPER 缺省调频与当日室温，不能推出 5 Hz 运行时合同、其他帧序列或真机航拍下的丢帧/热行为；丢帧分布的描述（冷启动与周期内固定两帧）未经额外运行验证成因；
- （补跑D 原文）任何 Jetson 热稳态、VLM、共驻结论（S2–S5 未运行）；S1 读数只代表本板本栈（JP7.2 / 系统 TensorRT 10.16 / 官方 cu130 torch 二进制兼容）、a7 前 320 帧、离线 init 框替身的单进程回放；
- S1 的「可能解释」（输入形状）未经验证，不能据此推出矩形引擎或任何其他引擎会通过 1e-3 线，也不能推出 FP16 本身无偏差；
- 补跑B 未装成 torch，不能推出官方 cu130 轮子在本板可用或不可用（SM 87 内核与 TensorRT 共存均未验证）；
- 补跑C 的 matmul/卷积/nms 冒烟通过，不能推出 torch 全部算子在本板可用，也不能推出 S1 导出、计时或一致性会通过；arch list 不含 sm_87 是读数，不是「不可用」的证明；
- 「容器 TensorRT 不支持 SM 87」只针对该镜像（`pytorch:25.08-py3`，TensorRT 10.13.2.6），不能推出系统 TensorRT 10.16 或其他镜像在本板不可用；
- `TAILSCALE_SMOKE` 读数不能推出任何链路（含有线直连、缆内链路）的时延或完整率，也不支撑 AC-4…6；
- S0 `PASS` 不能推出 S1–S5 会通过；冒烟中的门 ⑤ 统计不能推出 Unity Play 下的门通过率；
- 冒烟对时样本只覆盖开始后约 34 s（冒烟发现的对时缺陷，已修复，见交接文件），漂移 −39.5 ppm 不可作为两机时钟漂移结论。

## 6. 待用户现状（AC-15 同步，K1K3K4补跑F）

- §7 (h)：已答复且有线链路已接好（账本 09-28、10-02、10-03 有线直连成功、10-03 known_hosts 授权四条，`-ledger.json`「pending_user.h」），正式 SR 已在该链路执行；§7 (n)：只签阶段 A，阶段 B 全部维度 0；§7 (i)–(m)：未答复，对应动作零执行（未租云/WSL2、未跑 3a 或下载 base、未重刷、未 `systemctl isolate`、未 `nvpmodel -m`）。
- S1 `STOP` 的 (α)、S2 `STOP` 的 (α′) 均已由用户答复并入账（文首）；本轮之后无新的 STOP 待用户二选一。
- （补跑F 原文）仍待用户：停点全套的 Mac 模型额度 SUB:2（`P1-ENG-JET-001:b0a5f79c:SUB:2`，IR-9）——未签则停点全套无法运行、自证第 2 项不成立、不能送 `C1@K1K3K4`。
- K1K3K4全套 当时现状（已被下列轮次取代，非现状）：SUB:2 已由用户签发并经接受落实、已入 `-ledger.json`；但跑前核对预计全套会额外加载 SUB:2 未列名的 det-assoc 冻结检测器 2 次，全套未运行，自证第 2 项仍不成立、不送 `C1@K1K3K4`。新的待用户/待裁定项见交接「K1K3K4全套执行记录与停点自证」中「待用户（K1K3K4全套）」。
- K1K3K4全套CPU1 当时现状（已被下列轮次取代，非现状）：用户已签 SUB:5 A 并选 CPU-1，停点全套已跑一次（额度用尽）；本批新增失败（Carrier CPU 比较 1 条、scene006 环境差异 29 条）使自证第 2 项不成立，待接受裁定 IR-24/25 后转用户（交接「待用户（K1K3K4全套CPU1）」）。
- K1K3K4证据整理1A 当时现状（交 C1 后已被核对退回取代，非现状）：Carrier 处置（1A）与 scene006 环境分列已由用户裁定并经接受落实，本线 A 当前无待用户项；候选已冻结并交接受 `C1@K1K3K4`（C1/R1 结论与 `UNITY_NA` 附议未预签）。阶段 B 全部维度仍 0（线 B 的待用户项见提案「阶段B签发包刷新」，不在本报告范围）。
- K1K3K4C1返工 当时现状（已被 C2/R1/R1消费/R1注记修补/K1K3K4全套SUB6 取代，非现状）：`C1@K1K3K4` 已首次退回（C1-AC13-1，报告现状/历史分列），本轮仅修文档并重冻结候选，交接受 `C2@K1K3K4`（本停点核对退回已用 1 次，C2 后照交独立 `R1@K1K3K4`）；本线 A 无待用户项。全套 1/1 已用、S1/S2 `STOP` 与 SR `PASS` 原样、S3–S5 `NOT_RUN(阶段 B 信封未签)`，阶段 B 全部维度仍 0。
- 现状（K1K3K4全套SUB6，现行）：`R1@K1K3K4` 已通过并消费（Overall `REVIEW_PASSED`）；R1-1…4 补丁成新候选，用户签 SUB:6 并为新候选重新具名 Carrier/scene006 两项例外，新候选停点全套已跑 1 次（SUB:6 全套、det-assoc、回放额度均耗尽），四项自证成立、交接受只读核对后独立 `R2@K1K3K4`；本线 A 无新的待用户额度项（A收口:1 与线 B 阶段B:1–8 仍由用户另行决定，本报告不答）。S1/S2 `STOP`、SR `PASS`、S3–S5 `NOT_RUN(阶段 B 信封未签)`，阶段 B 全部维度仍 0。
- 阶段 A SR 轮数已用 5 / 5（含冒烟 1、返工 1），再需任何 SR 轮均须用户另签。
