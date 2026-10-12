# VLM 线诊断道独立状态板（COORD-VLM-DIAG-2026-10-10）

本板只记 VLM 线在立正式工作项之前的诊断道进度，与主线 `docs/current-status.md` 隔离（用户 2026-10-10 同意，账本同日「全局 — 用户直接授权协调批次 COORD-019：双路并发…并同意 VLM 线先按诊断道开」条 (2)）。
先例：2026-10-09 共驻诊断 `docs/evidence/COORD-CORES-DIAG-2026-10-09/status.md` 与离线回放。
本道的结果只作诊断（`diagnostic_only`、`gate_evidence=false`），不进任何 P1-* 门证据、不形成 verdict、无独立复核；要写进简历或提案主张时只能称「探针/审计读数」。
任何消耗（Mac/5060/板上推理、下载、Play）须用户另签信封后才可派发；本板开板时已签额度为 0。
写入者：supervisor 会话。派发事件仍按全局规则记在 `docs/evidence/supervisor-dispatch.jsonl`。

## 依据

- 主线判据：`docs/project-background.md` §3（VLM 是主角；接口 B 允许作为探针对照；分类器作快路径与基线，账本 2026-10-10「属性分类器」条）。
- 下一轮 VLM 工作项的硬要求：含跨场景测试（账本 2026-10-10「属性分类器」条效力段）。
- 路线评估与排序（本会话 2026-10-10 聊天结论，摘要见 `eval-set-audit-prelim-2026-10-10.md` §3）：审计 → 接口 B 零训练探针 → 必要性基线与跨场景 → 训练；解冻 ViT、换模型、高分辨率采集后置。
- 双路并发：VLM 线归 `vlm` 路（AGENTS.md「执行轨道纪律」，COORD-019）；本诊断道不是 Active handoffs 行，立正式工作项时再入交接表。

## 当前状态

| 项 | 内容 |
|---|---|
| 阶段 0 评估集审计 | `DIAG_DONE`（2026-10-11，派发 `COORD-VLM-DIAG-2026-10-10-阶段0审计-20261011T001529Z-e5e7`，零消耗，约 8 min）；摘要 `stage0-audit-summary-2026-10-11.md`，原始输出在 mini 仓库外 `~/vlm-diag/COORD-VLM-DIAG-2026-10-10/stage0-20261011/`；任务定义两道待用户裁定题：远处小目标补采集用户 2026-10-11 按推荐「先不补」；部分可见对象 gold 定义用户同日按推荐「沿用可见框、按可见比例分档报告」（账本 2026-10-11 本道两条） |
| 阶段 1 接口 B 零训练探针 | `DIAG_DONE`（2026-10-11，信封 `VLM-DIAG:B:1` 及两次追加，Jetson 基座 Q4 与 BF16 × P-draw/P-text 四臂，537 推理行；查询 2,228 / 2,600、实际推理 2,856.8 s）；摘要 `stage1-interface-b-summary-2026-10-11.md`，原始输出在 mini 仓库外 `~/vlm-diag/COORD-VLM-DIAG-2026-10-10/stage1-20261011T004632Z/results/`；要点：单目标 BF16 draw 50.4%、Q4 draw 36.3%（C2 接口 A 参照 77.2%，不同任务），失败以答 none 为主，歧义报告近 0；5060 对比为方向、未签 |
| 阶段 2 必要性基线与跨场景 | 依赖快层重训带出的属性分类器与 `P1-ENG-SFT-003`（SynDrone，暂停中）；未排期 |
| 阶段 3 训练 | 2026-10-11 用户选做**个人实验**（不走角色流程、无提案与信封，结果只作诊断，先例 2026-09-12 用户自跑零样本探针）：接口 B「选编号」LoRA，用户自己租卡；分工「混合」（训练循环、LoRA 配置、损失与 label mask 用户自写，数据构造、环境、合并转换、板上评测由 Claude 写并讲解）；交接说明在仓库外 `~/sft-lab/HANDOFF.md`，在新的普通会话中进行；结果交回 supervisor 代录为用户实测记录 |
| FASTFIX-MINI-MUTEX（R1） | 2026-10-11T21:47:44Z fast 路 supervisor 登记 `state=ready`（phase=R1，host=Mac mini）：vlm 侧由用户当场确认代 vlm 路 supervisor（账本同日「用户代 vlm 侧确认 R1 的 FASTFIX-MINI-MUTEX 窗口 ready」）；窗口期间本道不在 mini 写入；2026-10-11T22:03:07Z fast 路登记 `state=released`（R1 复核收工、静止已核，墙钟 903 s，D 最大 341 MB），本道恢复 |
| FASTFIX-MINI-MUTEX（实现窗口） | 2026-10-12T01:03:15Z fast 路 supervisor 登记 `state=ready`（phase=impl-R1-1，host=Mac mini）：vlm 侧由用户当场确认（账本同日「用户代 vlm 侧确认实现窗口」）；窗口期间本道与个人实验不在 mini 写入；2026-10-12T01:11:04Z fast 路登记 `state=released`（墙钟 463 s，D 最大 3.5 MB），本道恢复 |
| FASTFIX-MINI-MUTEX（R2 窗口） | 2026-10-12T02:11:42Z fast 路 supervisor 登记 `state=ready`（phase=R2，host=Mac mini）：vlm 侧由用户当场确认（账本同日「用户代 vlm 侧确认 R2 窗口」）；窗口期间本道与个人实验不在 mini 写入；2026-10-12T02:25:46Z fast 路登记 `state=released`（墙钟 826 s，D 最大 94 MB），本道恢复 |
| 主线索引 | `docs/current-status.md` Immediate next actions 一句指针；Log 2026-10-10 COORD-019 条 |

## 阶段 0 审计任务定义（零消耗，待派发）

输入：`outputs/eng-sft/P1-ENG-SFT-002/data/eval.jsonl`（609 行，含 gold 框、`stratum`、`group`）、同目录 `select-eval.jsonl`、C2 与零样本预测文件（路径与 sha 见 `docs/evidence/P1-ENG-SFT-002-eval-summary.json`）、S4 归档对象真值（每帧全部对象）。
输出（写本目录，机读 JSON + 一页摘要）：
1. 每行贴边标记（gold 任一边 ≤ 3‰ 画幅）与可见比例（裁剪框面积 / amodal 框面积，需从对象真值重算 amodal 框）。
2. 每帧对象数与候选数分布（决定接口 B 一次放几个候选、ROI 预算是否够）。
3. 按可见框重算 S/M/L 分层，与现行分层交叉表。
4. 按「贴边 × 现行分层 × 失败类型（none / 框落别处 / 框偏 / 歧义）」重算 C2 与零样本的失败构成。
5. 远处小目标子集（不贴边且可见短边 < 32 px）的行数与成功率。
待用户裁定（审计后）：部分可见对象的 gold 定义（可见框 / amodal 框 / 可见比例阈值以下记 none 或剔除）；若远处小目标子集太小，是否补一次斜视或高悬停采集（属场景改动项）。

## 给 Mac mini 会话的接力（2026-10-10，Air supervisor 会话写；只是接力，不是账本授权）

用户 2026-10-10 决定本人在 Mac mini 开 supervisor 会话推进本道（原话「我自己在上面跑，不用你来」）。Air 会话只读核过以下事实：

1. **mini 仓库状态**：`~/TetheredDroneTracking` 在 `49dc161`，落后 origin/main 一个提交（`3c41cac`，COORD-019 双路并发）；工作树有 2 个未提交条目，应是 `P1-ENG-FASTFIX-001` A实现 子代理（派发 `P1-ENG-FASTFIX-001-A实现-20261010T233353Z-dc6c`，日志里只有 `requested`）正在写。开工先 `git pull --ff-only`；拉不动就等该子代理收工，不要 stash 或覆盖别人的改动。
2. **审计输入不在 mini**：mini 的 `outputs/eng-sft/P1-ENG-SFT-002/` 为空。四个小文件在 Air（合计约 1.7 MB），由用户自行传输（沿 FASTFIX「需要传输的文件我去传输」先例，传入后登记来源与 sha 再用）：`data/eval.jsonl`（634,764 B）、`data/select-eval.jsonl`（341,500 B）、`returned/sft-20260918T223245Z-bd1f5ebb/predictions/eval-adapter.jsonl`（339,567 B，sha256 前缀 `0ccb4f1e262f5fc5`）、`logs/job-a-live-20260918T2134Z/returned/sft-20260918T202551Z-bd1f5ebb/predictions/zero-shot.jsonl`（347,122 B，前缀 `f6e31c386949fa64`）。只凭这四个文件能做任务定义第 3、4、5 项和第 1 项的贴边标记；第 1 项可见比例与第 2 项每帧对象数需要对象真值，在 Air 的 `runtime/test-results/p1-vlm-survey*/`（S3/S4 归档）与 T7 上，mini 没有，可先出前一半、后一半另定执行机。
3. **派发规则现状**：细则「唯一执行」「启动前登记与全局去重 (i)」与 engineering §8 仍是全局单写者，任一 work_id 有未终结 `requested` 就不派发。**用户 2026-10-10 选 (a)，已作 COORD-019 补充同步落地**（账本同日「全局 — 用户选 (a)：单写者规则改按路…」）：每路至多 1 个写仓库角色、两路可并行；派发去重与重启对账只看本路，另一路的未终结派发只记检查点摘要；`requested` 事件写 `lane: vlm`。mini 会话因此可在 FASTFIX A实现 未收工时派发本道子代理，但共享文件只做追加或锚点增量、只 `git add` 本路具名文件、推送前 `git fetch` 变基、不动另一路的未提交改动。
4. **子代理设计**沿回放与共驻先例：脚本与输出放 mini 的 `outputs/eng-vlm-diag/<批次>/`（不入仓），不改 `tools/`、不跑模型、零下载；结果摘要由 supervisor 照录回本目录；派发事件记全局 `docs/evidence/supervisor-dispatch.jsonl`。
5. **给 FASTFIX 一路的提醒**：其子代理收工推送时要变基到 `3c41cac` 之后；交接表每行多了 `Lane` 列（FASTFIX 行已填 `fast`），新加或改写的行都要带 `Lane` 值，否则新检查器拒绝提交。

## 日志（新在上）

### 2026-10-11 — 用户选个人微调实验（mini supervisor 会话）

用户问是否租卡重新微调，supervisor 推荐接口 B「选编号」LoRA 并按工程轨道立项；用户改为「这次我想试试，从代码开始体验一下微调过程」，选择题选「混合」分工与「你个人的实验（推荐）」。supervisor 写仓库外交接说明 `~/sft-lab/HANDOFF.md`，不派发、零消耗。

### 2026-10-11 — 阶段 1 完成：BF16 重跑核销、写摘要（mini supervisor 会话）

BF16 一次跑通（查询 1,114、实际推理 1,632.4 s，最低可用内存约 0.74 GiB、swap 0）；四臂计分完成。F4/F5 通过。摘要 `stage1-interface-b-summary-2026-10-11.md`。阶段 1 `DIAG_DONE`；信封未用余量（查询 372、推理时间约 2.7 h、回传约 88 MB）不转用。

### 2026-10-11 — 用户准 BF16 重跑、墙钟按实际推理时间（mini supervisor 会话）

用户「清标记重跑」；因原墙钟读法已于 09:58:34Z 到期，supervisor 转呈计量口径，用户「按实际推理时间算」。照录账本、设计加修订 2，登记 BF16 重跑派发。

### 2026-10-11 — 正式板上运行核销：Q4 完成、BF16 假阳性停（mini supervisor 会话）

Q4 两种呈现 1,074 条正式 + 40 条冒烟完成，无 stop_reason；单目标 Q4 成功率 P-draw 36.3%、P-text 24.6%（C2 接口 A 参照 77.2%，不同任务），失败以答 none 为主。BF16 未启动：子代理启动命令含 llama-server 字样被 runner 误判为其他作业。F4/F5 通过；supervisor 结束子代理残留的 3 个轮询循环。待用户定是否清标记重跑 BF16（runner 墙钟上限 09:58:34Z）。读数只作诊断。

### 2026-10-11 — 登记 mini 互斥释放、派正式板上运行（mini supervisor 会话）

fast 路 supervisor 通知 `FASTFIX-MINI-MUTEX state=released`（06:25:14Z，`78c4f9f`）；本会话核实该 finished note、mini 无 window_meter/unittest/eng_fastfix 进程、主树干净后登记同一凭据，按原信封恢复调度，登记派发 2（正式板上运行）。

### 2026-10-11 — 准备（修订 1）核销；登记 mini 互斥 ready（mini supervisor 会话）

子代理 13 min 完成：sentencepiece 0.2.2（1.35 MB）只装进工作目录、`.venv-language` 前后不变；BF16 GGUF 3.45 GB 转换 27 s；上传 3.58 GB（890 文件，板上 sha 全一致）；推理行 537（零候选 14 行全在 G5），正式请求 2,148 + 冒烟 80；板上只读 precheck 通过。F4/F5 通过。依账本 6e44ea9「FASTFIX-MINI-MUTEX」登记 `state=ready`（2026-10-11T06:02:12Z），通知 fast 路 supervisor；正式板上运行待其 released。

### 2026-10-11 — 三题按推荐、设计修订 1、重派准备（mini supervisor 会话）

用户「不用了，三个都按推荐走吧」：不改板子系统设置；信封追加 sentencepiece 下载安装 1 次（≤ 10 MB，只装进工作目录）、候选去掉完全被遮挡的车、零候选行单列。设计文末加「修订 1」，重派准备（零模型运行）。

### 2026-10-11 — 阶段 1 准备派发核销：停于 BF16 转换缺依赖（mini supervisor 会话）

子代理 13 min 完成不依赖 BF16 的准备（547/551 行候选映射成功，正式请求 2,188 + 冒烟 80，空跑发送 0），BF16 转换因 sentencepiece 缺失按信封第 9 项停下；上传 0、板上写入 0、回传约 2 MB。F4/F5 通过。三题（sentencepiece、4 行零候选、完全遮挡候选）转呈用户。工作目录 `~/vlm-diag/COORD-VLM-DIAG-2026-10-10/stage1-20261011T004632Z/`。

### 2026-10-11 — 签发 VLM-DIAG:B:1、写阶段 1 设计、派发准备（mini supervisor 会话）

用户「按草案签发」：阶段 1 在 Jetson 上评估，基座 Q4 与 BF16 两种精度；「5060 可用了补一次对比」记为方向。supervisor 写测试设计（551 计分行 × 2 精度 × 2 呈现 = 2,204 次正式查询），登记派发 1（准备：脚本、呈现图、BF16 转换、上传核 sha、空跑，不加载模型）。

### 2026-10-11 — 用户答完两道审计后裁定题、指定阶段 1 本机运行（mini supervisor 会话，第二个会话）

用户「二按推荐先不补，3任务优先在本机上运行」，照录账本。第 1 题（gold 定义）用户先问术语，解释后答「1按推荐走」：沿用可见框，按可见比例四档报告。阶段 1 信封各维度未签、额度仍 0。另：本日 mini 曾并开两个 vlm 路 supervisor 会话，本会话发现 e5e7 已由另一会话登记后未重复派发，该会话已收工。

### 2026-10-11 — 阶段 0 审计完成并核销（mini supervisor 会话）

子代理 8 分钟跑完，零消耗；609 行、448 帧对象真值全覆盖（S3 目录 `runtime/dist-data/frames_catalog/attempt-2/`）。supervisor 核查输出 sha 与关键计数后照录摘要（子代理写 `.md` 被钩子拒）。要点：现行 gold 已是可见框口径；C2 失败集中在截断行（答 none 30 行中 25 行）与选到别的车（25/30）；amodal 重分层使 S 层 43 行只剩 22；远处小目标仅 13 行（含 G4 32 行）。两道待用户裁定题已在会话转呈。

### 2026-10-11 — 阶段 0 审计派发（mini supervisor 会话）

用户在 mini 会话指示按 COORD-019 双路执行。核实：接力第 2 条「审计输入不在 mini」只对主树成立——四个输入文件在 mini 数据根 `~/TetheredDroneTracking-full/outputs/eng-sft/P1-ENG-SFT-002/`，大小与 sha256 前缀与接力所列一致，无需用户传输；S3/S4 归档 `p1-vlm-survey/` 8 个会话也在数据根，其他 family 真值覆盖由审计报告。fast 路实现子代理正写主树，vlm 路 supervisor 改用独立本地克隆 `~/TetheredDroneTracking-vlm` 提交；审计输出放仓库外 `~/vlm-diag/COORD-VLM-DIAG-2026-10-10/stage0-20261011/`（仓库内 `outputs/eng-vlm-diag/` 未被 gitignore，supervisor 不改 .gitignore）。零消耗，不跑模型。

### 2026-10-10 — 接力给 mini 会话

用户改由本人在 mini 开 supervisor 推进；Air 会话核清 mini 仓库状态、输入文件去向与派发规则阻点，写成上节，不派发、零消耗。

### 2026-10-10 — 开板

依用户同意开板；阶段 0 任务定义落盘；初步读数文件同目录。未派发、零消耗。
