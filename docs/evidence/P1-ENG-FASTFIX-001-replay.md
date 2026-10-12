# P1-ENG-FASTFIX-001 离线重捕回放（AC-7）与有限复演（AC-8）

执行：Implementation（Opus 子代理，Mac mini），Dispatch-Id `P1-ENG-FASTFIX-001-A实现-20261010T233353Z-dc6c`，FASTFIX:A:1 内。
代码 = 候选 1（本文件同批提交的父链上「A实现 候选1代码」提交；可派生标识以 git 运行时解析为准，不手抄）。解释器 = 数据根
`~/TetheredDroneTracking-full/.venv-yoloe/bin/python`（3.12.14，只读使用、未安装）；权重
`~/TetheredDroneTracking/outputs/eng-det/runs/run-1/weights/last.pt`（sha `d6a0d6a9…` 与规格一致，加载前现核）；
输入根 `~/TetheredDroneTracking/outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261008T213653Z/`（USER-4A，七题答复 SOURCE
限用途扩至本项 AC-7）；输出 `~/TetheredDroneTracking/outputs/eng-fastfix/replay/candidate1-20261011T001829Z/`（不入仓）。

## 1. 输入与剧本（运行前已提交）

| 项 | 读数 |
|---|---|
| 准入帧核对（S-ORIG） | `tools/eng_fastfix/replay.py run` 启动前现算 1,658 个帧文件（829 jpg + 829 json）对 `replay-transfer/SHA256SUMS` 全部一致，0 不符（真值文件不在本模块核对范围，只在 `score.py` 读） |
| 剧本 | `docs/evidence/P1-ENG-FASTFIX-001-ac7-script.json`，sha256 `7d4fdaedf4119891717f8fe3a7b3352b5135569174cf5a02305c4af2003c9eac`；由实现角色只看原始帧像素登记（红色像素扫描 + 5 帧目检），点击 = 第 530 帧 (230, 415) 红车车身，帧字节 sha 与原件一致；注入步长 20、至多 12 次、重建跳 3 帧、热身 10 帧、提交后跟 10 帧 |
| 账本前置 | `docs/evidence/P1-ENG-FASTFIX-001-ledger-A.json` `check_launch(yolo_loads=1, wall_s=600)` 通过后才加载 |
| 配置 | 捕获 `config/p1-eng-capture-001.json` sha `c15c3c3c…`（diff 为空）；FASTFIX `config/p1-eng-fastfix-001.json` sha `aab52b63…`（0.4 s/2 帧、N_drop=3、T_reacq=10、on） |

## 2. 运行与结果（候选 1 唯一一次 live 推理建缓存）

运行：真实构造 **1**（`CountingModel.loads`），live 推理 **309 帧**（第 520–828 帧，捕获策略 `unify_vehicle`），其后全部注入从缓存取
（`CachedOrLiveModel(live=None)`，缓存命中 3,765 次、未命中 0）。工具内计时 10.985 s；外层执行区间 11.6 s（入账）。输出 116,361 B
（`detections.json` sha `d4ddcfa7…`、`replay-output.json` sha `f5544fc0…`、`score.json` sha `3ff8c26c…`）。

绑定：第 530 帧点击提交成功（键 3）。注入帧 550, 570, …, 770（12 个，均 ≤ 828）。

| 注入帧 | on 臂 | off 臂 |
|---|---|---|
| 550 | committed：f_last 550、就绪 554、提交 556（新键 1），证据帧 [555, 556]，用时 6 帧（自升级）/ 2 帧（自就绪） | skipped(auto_reacquire_off)，窗口长度内自动提交 0 |
| 570 | committed：提交 576（新键 1），证据 [575, 576]，用时 6 / 2 帧 | skipped(auto_reacquire_off)，自动提交 0 |
| 590 | committed：提交 596（新键 3），证据 [595, 596]，用时 6 / 2 帧 | skipped(auto_reacquire_off)，自动提交 0 |
| 610–770（9 个） | not_applicable（注入帧管理器无绑定或非 OBSERVED；红车约第 600 帧后出画，基线已不在跟） | 同左 |

缺失证据项：3 次提交窗口内合成先验均有效（`missing_evidence` 为空），无 invalid_input。

**评分（`tools/eng_fastfix/score.py::score_ac7`，真值只在此读）**：on 臂 n_committed = **3**，提交帧被跟实例与真值 IoU = 0.926 / 0.943 / 0.815，
全部 ≥ 0.5；off 臂自动提交 0；其后 10 帧 IoU ≥ 0.5 比例 10/10、10/10、4/4（第 590 注入后真值可见只剩 4 帧）。**AC-7 判据（n_committed ≥ 1
且全部提交 IoU ≥ 0.5）满足**；误绑 0 只是 n = 3 的样本观察，不推误重捕率、不推板端或在线能力（提案 §6）。成功率与用时只作读数：
on 臂可适用注入 3/3 提交、提交用时 6 帧（含模拟重建 4 帧）。

限制（如实）：回放时钟取帧元数据 `capture_monotonic_s`（处理零延迟等价），每帧视为本批最新帧且无发布门（提示候选按 PUBLISHED 记），
重建以「跳过 3 帧」模拟；不代表在线会话的时序、积压或真实重建耗时。可适用注入只覆盖红车可见的 530–600 区间。

## 3. AC-8 有限复演

**`NOT_RUN`**：可选 TX 未签（TX = 0），且第 648–650 帧缺同一原会话处理记录（「D2预检核清」§1 差异 4）。本轮未传输、未读 formal-redo 原件，
不计验收。
