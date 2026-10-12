# P1-ENG-CAPTURE-001 — 阶段 B 唯一一次 Play 操作单（AC-21；代码停点已通过消费，B 已签，发令前置待完成）

> **当前效力：CAPTURE:PLAY:1 与 B 类 STOP 已由用户签发并经 Acceptance 落实；代码停点通过轮已消费、§1 Air 预检已核清，§2 现场前置仍待完成。旧 runtime 残留处置已由 Acceptance 核清满足（§2.1；提案「发令前置核清」）；现场复取、用量/收尾预留及执行分工仍待完成，满足 §2 全部前置才可启动。** 唯一 B 来源为 `docs/authorizations.md` 2026-10-10「P1-ENG-CAPTURE-001 — 用户签发阶段 B 额度 CAPTURE:PLAY:1 并确认 B 类 STOP 处置（supervisor 会话代录）」；处置裁定与待用户项见同名提案 Contract conformance「B信封落实」。签额不跳过停点或现场前置。一次 Play、失败不重试。真值只进 `tools/eng_capture/analyze_play.py` 的 `score_` 函数。

合同来源：`docs/proposals/P1-ENG-CAPTURE-001-moving-target-capture-round1.md` §5.2、§6、§8.2、AC-21…26，「终局裁定（第三次，依用户 (a)）」AR1-6 拆分表，「信封落实（2026-10-09，Acceptance）」U-3。

## 0. 阶段 B 额度与守账（CAPTURE:PLAY:1 已签；本轮落实未动用）

| 维度（§5.2 申请值） | 已签 | 本单守账方式 |
|---|---|---|
| Unity Play | 正式 1、诊断 0、失败不重试 | 发令前核 CAPTURE:PLAY:1 账本条目逐字存在，否则 S-B-PRE |
| scenario / session / run ID | 0 / 1 / ≤ 3 | 只复用现有场景配置；session `capture-play-1`；run = 常驻段 1 + 现行重建上限 2 |
| 会话 YOLO 加载 | ≤ 1，重建复用缓存 | 段日志 `model_cache.json` 的 `model_loads` 记实 |
| 按钮墙钟 / `T_sess` | ≤ 420 s；`T_sess` ≤ min(290 s, (1490 − f₀)/5) | 等待 Play 起计时；同时按 §2 扣已用准备 93 s，累计到 420 s 未静止即 S-B-WALL |
| Air 新增磁盘 | ≤ 1 GB | 覆盖、日志、归档、哈希、评分、收尾共账，启动前预留、归档后 `du -sk` 记实；mini 无 B 磁盘额度（缺项 0），评分与产物留 Air |
| 板上、VLM/API、云 GPU、下载/安装 | 0 | 不适用 |

收尾预留（AR1-6）：Z-B（停会话/Unity、串行 HOLD、未决请求记 UNKNOWN、封存原件与哈希清单、零模型评分）的写入与墙钟同在上表共账，启动前留余量；不给 420 s 外隐含宽限。

## 1. Air 只读预检（§8.2；U-3：阶段 B 准备时由用户在 Air 开会话执行；mini 不代证）

只读、零消耗、不加载模型、不 Play、不安装、不写共享 `runtime/`。原始读数逐项贴入下表（版本差异逐项核可用性；无法确认即 S-B-PRE）。

| 项 | 命令 / 方法 | 原始读数（Air 会话填写） |
|---|---|---|
| HEAD 与工作树 | `git rev-parse HEAD`；`git status --porcelain` | 2026-10-10T19:46:18Z 读：`156365556520eb9b1ebe84c1b0833e5f74560a06`；porcelain 空（0 行）；本地 `origin/main` 与 `git ls-remote origin refs/heads/main` 均同该值。复核 `passed_candidate`（运行时解析）为该 HEAD 祖先，`git diff <passed_candidate>..HEAD -- controller tools tests config Assets ProjectSettings Packages` 0 行。发令时须按 §2 重取，本读数不代替 |
| 解释器 | `.venv-yoloe/bin/python --version` | `Python 3.12.13`（符号链接至 `~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12`）。与 mini §8.1 的 3.12.14 差一个补丁号；可用性：本机同一解释器已承载 ACQ-001 D1、FRAME-001、LOOP-002 诊断 Play（`docs/unity-test-log.md` 及 `docs/evidence/P1-ENG-ACQ-001-play-d1.md` 记 3.12.13），只读核不能证明两机数值逐位一致，本单 B 读数只在 Air 产生、不与 mini 回放逐位比对 |
| 包版本 | `.venv-yoloe/bin/python -c "import importlib.metadata as m;[print(p,m.version(p)) for p in ('ultralytics','torch','lap','numpy','opencv-python')]"`（须与 mini §8.1 一致或逐项说明） | `ultralytics 8.4.104` / `torch 2.13.0` / `lap 0.5.13` / `numpy 2.5.1` / `opencv-python 5.0.0.93`（exit 0；未 import torch/ultralytics）。与 §8.1 逐项：ultralytics、torch、lap、opencv-python 一致，且 ultralytics = 冻结配置 `ultralytics_version` 8.4.104；**numpy 2.5.1 ≠ mini 2.5.3**（同次版本内补丁差）。可用性：Air 既往 Play 环境记录即 numpy 2.5.1（`docs/unity-test-log.md` §2.2 Python 环境），本轮不装包、不升级；数值逐位等同无法只读确认，按上格同一边界 |
| 权重 | `shasum -a 256 outputs/eng-det/runs/run-1/weights/last.pt`（须 = 冻结规格 sha） | `d6a0d6a9cdee06a0790f5d9812a1fe98db033520981c0ffafe786c3cbbe059c9`，5,458,330 B；= `config/det-assoc-v1.models.json` 的 `weights.sha256`/`size_bytes` 逐字；该配置 `freeze.sha256` 与 `docs/evidence/P1-ENG-FAST-002-freeze.json` 现算 sha 亦一致 |
| 可用磁盘 | `df -h .`（≥ 1 GB） | `/dev/disk3s5 228Gi 187Gi 12Gi 94% … /System/Volumes/Data`：可用 12 GiB ≥ 1 GB（容量已用 94%，发令前宜再读一次） |
| Unity 能打开工程 | 用户现有界面/日志事实（静态版本号不冒充打开实测） | 日志事实（未启动/未操作 Unity）：`~/Library/Logs/Unity/Editor.log`（mtime 2026-10-10 15:16 本地）首行 `Unity Editor version: 6000.4.1f1 (336a400b9ea2)`、`Date: 2026-10-08T21:37:21Z`、`Successfully changed project path to: ~/TetheredDroneTracking`、`Mono: successfully reloaded assembly`、`Loaded scene 'Assets/SimplePoly City - Low Poly Assets/Demo/SimplePoly City - Low Poly Assets_Demo Scene.unity'`，全文 `error CS` 0 条；`pgrep` 现见编辑器进程 `…/6000.4.1f1/Unity.app/Contents/MacOS/Unity -projectpath ~/TetheredDroneTracking …` 在运行；该日志起点后 `Assets`/`ProjectSettings`/`Packages` 无新提交。日志事实足以表明该编辑器版本已打开本工程；Play 前界面状态由用户现场确认 |
| 覆盖文件可生成 | 只读核下列生成命令可执行（实际生成属已签 B 准备） | `config/scenario.untethered.json` 存在（3,377 B，sha256 `962764bc0fd47cd3e51253ce19ecabb369c23e0261393419ac38ba059cd16d87`），`sensor.retained_frame_count` 键存在（现值 128，§3 覆盖为 1500）；解释器可用（同上，只读解析 JSON 成功）；`test -w runtime` = 0（可写）；`test ! -e runtime/scenario_config.json` = 0（不存在、无残留）；该路径被 `.gitignore:30 /runtime/*` 忽略。**未生成覆盖文件、未写 `runtime/`** |
| 点击页端口空闲 | `lsof -nP -iTCP:8774 -sTCP:LISTEN`（无输出 = 空闲） | 无输出，exit 1（空闲）；`lsof -nP -iTCP:8774` 亦无输出 |
| Air→mini 局域网拷贝 | 只读核路径可达（拷贝不是下载许可，也不豁免磁盘） | `~/.ssh/config` 有 `Host macmini`（Tailscale 地址、`User zc5`、密钥登录）；`ssh -o BatchMode=yes -o ConnectTimeout=5 macmini true` exit 0；远端只读 `test -d` 见 `~/TetheredDroneTracking` 与其 `outputs/` 存在；`tailscale ping` 直连（非中继）10 ms；本机 `rsync`/`scp` 在。是否同一物理局域网未证（经 Tailscale 直连）。**未拷贝、未在 mini 写入**；B 无 mini 磁盘额度，按 §0 评分与产物留 Air，本路径非必需 |
| 未核假设 | 会话 tick 间隔 ≤ 1 帧（AC-22 e2e 前提）；`send_request` 进程内往返时延 | 由 Play 日志实测，不预填 |

**Air预检结论（2026-10-10，实现角色，supervisor 派发 `Air预检`；零消耗）：全部核过。** 上表九项均有原始读数；与 mini §8.1 的两处版本差（Python 3.12.13 / numpy 2.5.1，均补丁号）已逐项说明可用性，不构成 S-B-PRE 缺项；未核假设两项照原样留 Play 实测。本结论只解除 §5.2 的「§8.2 Air 预检」前置，不签发也不放行 CAPTURE:PLAY:1 或 B 类 STOP（仍未签 = 0）；§2 发令前记录须在发令时重做。

以上为 Air预检当轮快照；现行 B 已签效力见 §0/§6，发令前置仍须 §2 全部现场核验。

观察（非 §1 表项，不改预检结论；已由同名提案「B信封落实」及本单 §2 承接处置裁定）：`runtime/frames/`（257 项，`latest.json` 2026-10-04）与 `runtime/m3_body_truth.jsonl`（1,543,923 B，2026-10-04）为既往 Play 残留，现位于 §7.1 归档 `mv -n` 的源路径与 §4 f₀ 读取路径上；本轮未移动、未删除。

## 2. 发令前记录（AGENTS.md 完成规则）

现行裁定见同名提案「发令前置核清（2026-10-10，Acceptance）」。执行者待用户 CAPTURE-PLAY-EXECUTOR 选择：推荐用户在 Air 开 Implementation 陪同会话，由实现执行终端命令/记录/监控/评分，用户执行 Unity 与点击/目检；也可用户照单全部执行。supervisor 常规接力在用户设备/Play 节点停下，不能自动派发；用户直接指示有界陪同派发才可执行。以下每项在 Air 发令现场核验，不以 §1 或接受核清的旧读数代填；任一不符停报。顺序 = 先完成残留授权/保全核验 → 候选、共享槽位和环境复核 → §3 覆盖及 sha → 用户唯一一次 Play → 本次新鲜 f₀ / T_sess → §4 会话和点击页。

1. **RUNTIME-ARCHIVE 已获准、已执行，Acceptance 本轮核清满足；执行记录见 §2.1，现行判定见提案「发令前置核清」§1。处置约束保持。** B 账本条自身不授权删除或移动；本项已另由 RUNTIME-ARCHIVE 独立入账并交 Air Implementation 执行：Unity 非 Play、相关写者静止，两个旧对象以同卷无覆盖 rename 完整移入 `outputs/eng-capture/preexisting-runtime/` 当场排他创建的唯一目录，路径运行时生成/记录；逐文件数量、字节和 sha 清单移前后相等，不删除/复制后删源/跨卷/覆盖、不动其他 runtime 文件。目录冲突、源变化、核验不符或部分完成即停报，保留现场，不盲目重试/回迁。零模型/Play/正式 ID，新增清单/目录元数据实测计 B 磁盘、准备墙钟单列并保守与后续起停/Play/收尾合计核 420 s，不另给额外时间窗口；未授权前不得开始本次会话/模型/Play/ID。旧原件不进本次归档与评分。
2. 发令角色重取 `git rev-parse HEAD` / `git status --porcelain`，运行时解析同名复核最近 `passed_candidate`，核祖先及仅文档白名单差异，写本单 §9 与 `docs/unity-test-log.md`（接受/辅助代录）。全局 `blocks_consuming_gate` 无未 release 行、轨道及共享槽位互斥通过。
3. 复读 `df -h .`（§1 原值 12 GiB / 94%，此时仍须 ≥ 1 GB且可预留本次产物/收尾）；复核 8774 空闲、用户现场 Unity 工程与非 Play 状态、操作单/配置/冻结权重身份无漂移。逐维用量/余额可核、Z-B 预留足，UNKNOWN 不推余额；不够即 S-B-PRE/S-B-BUDGET。94% 不是新停止阈值，可用磁盘不是新增额度。
4. 旧 `runtime/frames/` 与 `runtime/m3_body_truth.jsonl` 的处置核验已完成、源路径已挪开；`runtime/scenario_config.json` 无残留（存在即停回接受，不删除）；本次 session、日志、§7.1 归档目标无已有同名对象（有即停，不覆盖/换 ID）。按 §3 生成覆盖、确认 1500 与参数逐值一致、现场 sha 写 §9；生成失败即停。
5. 残留保全准备 93 s 已计入总上限 420 s，后续执行准备、等待/起停/Play/Z-B 合计最多 327 s（重叠不重复；新增准备再扣，须预留收尾），不足即停报。T_sess 原上限不变、不能自动取 290 s。用户等待并进入唯一一次正式 Play，本次按钮墙钟从等待起计，与已用准备共账；累计到 420 s 未静止即 S-B-WALL；**首次新鲜 latest/帧旁车出现后、起会话之前**才取 f₀，核本次身份/新鲜性/配置、计算正且合法的 T_sess 写 §9，再执行 §4。无新帧不读旧 latest、不默认 f₀=0、不另开一次 Play；Unity 未进入按 S-B-UNITY 计本次已用。该顺序只落实原 AC-21 的“起会话前 f₀”，不增加试跑或重试。

### 2.1 残留保全执行记录（2026-10-10，Implementation，supervisor 派发 `残留保全`；MacBook Air）

授权：`docs/authorizations.md` 2026-10-10「P1-ENG-CAPTURE-001 — 用户同意 RUNTIME-ARCHIVE：旧 runtime 残留同卷无覆盖挪走保全，并确认现场无写者」；读法 = 同名提案「B信封落实」之「runtime 残留的唯一处置读法」。只做本项，未做 §2 其余前置。

| 步骤 | 读数 |
|---|---|
| 现场只读复核（20:01:41Z 起） | `lsof -nP -iTCP:8774 -sTCP:LISTEN` 无输出（exit 1）；`pgrep -fl language_loop` 及 `controller.`/`operator`/`eng_capture` 进程均无；`lsof +D runtime/frames`、`lsof runtime/m3_body_truth.jsonl` 均无打开者（exit 1）；Unity 6000.4.1f1 编辑器进程（`-projectpath` 本工程）在、非 Play 由用户确认。源清单（类型/字节/mtime）间隔 5 s 两次逐字相同，生成移前清单后第三次仍相同 → 静止 |
| 源对象 | `runtime/frames/`：目录 1 个，常规文件 257 个（无子目录/链接，`latest.json` mtime 2026-10-04）；`runtime/m3_body_truth.jsonl` 1,543,923 B；合计文件 258 个、8,748,594 B |
| 同卷 | `stat -f %d`：`runtime`、两源对象、`outputs`、目标目录均 = 16777231 |
| 保全目录（运行时生成，不是 scenario/session/run ID） | `outputs/eng-capture/preexisting-runtime/20261010T200242Z-e094bd/`（父级 `outputs/eng-capture/preexisting-runtime` 原不存在，`mkdir -p` 建父级；最后一级 `mkdir` 不带 `-p` 排他创建成功）；被 `.gitignore` `/outputs/eng-capture/` 忽略，不入仓 |
| 移动 | `mv -n runtime/frames <目录>/frames`（exit 0）→ 核源不存在、目标存在；`mv -n runtime/m3_body_truth.jsonl <目录>/m3_body_truth.jsonl`（exit 0）→ 同核；无跳过、无部分移动。整目录 rename，未复制、未删除、未改内容；其他 `runtime/` 路径（含各 `*-hold` 对象）未动 |
| 清单核验 | 目录内 `manifest-pre.tsv`（移前，相对 `runtime/`）、`manifest-post.tsv`（移后，相对保全目录）、`compare.txt`；格式 `相对路径<TAB>字节<TAB>SHA-256`，`LC_ALL=C` 排序。两份均 258 行、8,748,594 B，清单 sha256 均 = `e8fa45c76ab318c0de88cebd27514a2d74db62eb4f07e8104b3282aa2743c29a`（逐字节相同）；`compare.txt` sha256 `114f4be50046ee1c9168f696e8a16847ac7c5f50342ccb943605e5f14c56a663`。**结论：数量/字节/SHA-256 全等（IDENTICAL）** |
| 准备墙钟 | 20:01:41Z（现场复核起）→ 20:03:14Z（比对写完）= 93 s；单列，按「B信封落实」保守与后续起停/Play/收尾合计核 420 s 由 Acceptance 判读 |
| 新增磁盘实测 | rename 不新增数据（`du -sk outputs/eng-capture` 移入后、写清单前 = 9144 KiB，即被挪原件）；写入清单/比对后 = 9204 KiB → **新增 60 KiB（du 块计）**，逻辑字节 51,811 B（25,525 + 25,525 + 761）；新建 3 级目录元数据含在 du 内。`df` 已用量同期受系统其他写入影响，不作计量依据 |

B 守账（§0「Air 新增磁盘 ≤ 1 GB」）：本项计 60 KiB（61,440 B，du 块计）；本轮证据/状态板提交的 git 对象字节另见交接，未测部分记 UNKNOWN、不假记 0。模型/推理/Play/API/scenario/session/run ID 均 0。`runtime/scenario_config.json` 仍不存在（未生成覆盖）。

## 3. 覆盖文件（`retained_frame_count` 1500）

```bash
PY=.venv-yoloe/bin/python
"$PY" -c "import json;d=json.load(open('config/scenario.untethered.json'));d['sensor']['retained_frame_count']=1500;open('runtime/scenario_config.json','w').write(json.dumps(d,indent=2)+'\n')"
shasum -a 256 runtime/scenario_config.json    # 原样记入 §9；会话 --body-scenario-config 逐值核对
```

## 4. 会话与点击页命令（捕获模式）

```bash
SID=capture-play-1; OUT=outputs/eng-capture/play
# 仅在 §2 全部前置通过、用户进入本次唯一 Play 后取其新鲜 latest；旧残留/缺帧禁止用作 f0
# f0 = 起会话前本次 runtime/frames/latest.json 的 frame_id；T_sess = min(290, (1490 − f0)/5) 秒（须 > 0）
"$PY" -m controller.language_loop run --language off --session-id $SID --session-root $OUT/sessions \
  --runtime runtime --allow-shared-runtime --tracker det-assoc-v1 --resident \
  --ground-plane-y-m 0.2 --body-policy standoff --body-planner-config config/p1-eng-frame-001-body.json \
  --body-scenario-config runtime/scenario_config.json --scenario-id deterministic-loop-untethered \
  --planned-duration-s <T_sess> 2>&1 | tee $OUT/$SID.session-process.log
"$PY" -m tools.eng_capture.click_web live --runtime runtime --session-id $SID --log $OUT/$SID.click-web.jsonl --port 8774
```

点击页只监听 127.0.0.1；按钮闭集 = 点击图像、「停止会话」；无确认、无自由文本、无语言按钮。点击经 `Submitter`（单在途）+ `InProcessSend`（进程内 `send_request`）；结果未知即封住本会话业务动作，只放行 stop 至多一次。

## 5. 点击剧本（AC-21；全部点击计入 AC-22 分母）

| 步 | 动作 | 判据 / 记录 |
|---|---|---|
| S1 | 点一辆静止车 | 绑定（INITIAL）或拒绝原因照记 |
| S2 | 红车入画、操作者判断其远于静止车时点红车 | USER_RESELECT；提交时真值水平距离 d₀ 由评分取（AC-25） |
| S3 | 跟随红车 ≥ 1 圈 | 丢失/修复/准时报告逐次照记（AC-23/24） |
| S4 | 点静止车，再点回红车 | 两次换目标的 e2e 计入 AC-22；换回后转向不丢或窗口内修复/报告 |
| 结束 | `T_sess` 到点（`duration_reached`）或「停止会话」 | 一次 Play，失败不重试 |

## 6. STOP 码（12 个；A 类随 CAPTURE:A:1、B 类随 CAPTURE:PLAY:1 已确认）

确认来源：A 类 = `docs/authorizations.md` 2026-10-09「用户签发第一轮阶段 A 额度 CAPTURE:A:1 并确认阶段 A STOP 处置…」；B 类 = `docs/authorizations.md` 2026-10-10「P1-ENG-CAPTURE-001 — 用户签发阶段 B 额度 CAPTURE:PLAY:1 并确认 B 类 STOP 处置（supervisor 会话代录）」（已确认；仅对应已签余额足/前置独立时“可继续”，零模型收尾共账 B 磁盘/墙钟，停止/撤权义务不等待新授权）。处置原文 = 终局裁定 AR1-6 拆分表。

| 码 | 阶段 | 确认来源 | 必停依赖 | Z 收尾 | 可继续（仅确认后、对应信封已签/余额足/前置独立） |
|---|---|---|---|---|---|
| S-A-BUDGET | A | CAPTURE:A:1 | 将越界维度及其依赖 | Z-A；未知用量记 UNKNOWN | 不继续模型/全套/回放；回用户 |
| S-A-INPUT | A | CAPTURE:A:1 | 本候选 AC-17/18/19 全部回放 | Z-A | 独立全套 F；不读坏准入文件的合成/替身 focused |
| S-A-FIDELITY | A | CAPTURE:A:1 | 正式回放及受影响呈现冻结 | Z-A | 闭集内修管线、零推理样帧重做保真；确认后按原余额首次正式回放 |
| S-A-REPRO | A | CAPTURE:A:1 | 新臂评分与 AC-17/18/19 读数作废 | Z-A | 不补跑、不换门/剧本/参数；回接受与用户 |
| S-A-CRASH | A | CAPTURE:A:1 | 同候选回放，第 3 次加载禁止 | Z-A | 不继续该候选回放 |
| S-A-LOADER | A | CAPTURE:A:1 | 启动超清单构造前拦截并停本次全套 | Z-A | 无同次重跑；AC-20 `NOT_RUN`；回用户 |
| S-B-PRE | B | CAPTURE:PLAY:1 | 不启动会话/Play/模型，不分配 ID | 只记不符及交接 | 仅获准 Air 只读复核 |
| S-B-UNITY | B | CAPTURE:PLAY:1 | 本次 Play 计已用，不再尝试 | Z-B | 仅零模型分析已得文件（B 磁盘/墙钟） |
| S-B-TERM | B | CAPTURE:PLAY:1 | 剩余剧本 | Z-B | 同上；无会话重启/重建 |
| S-B-WALL | B | CAPTURE:PLAY:1 | 剩余剧本，立即停止 | Z-B | 不启动额外运行；收尾墙钟照记 |
| S-B-UNSAFE | B | CAPTURE:PLAY:1 | 立即「停止会话」，剩余剧本 | Z-B；AC-25 FAIL | 仅零模型分析；不追认不安全命令 |
| S-B-BUDGET | B | CAPTURE:PLAY:1 | 将越界维度及其依赖 | Z-B | 只有未越界且已预留的零模型收尾写入/分析；回用户 |

## 7. 归档与评分（零模型；产物留 Air）

> R2文档闭合（2026-10-10，实现角色）：本节按同名提案「Contract conformance」之「R2冻结裁定」R2-1 路径 (ii) 与「IR-R1-3答复落实」AC-22 修订 1 改写为两次调用与 AC-22 分列取读，只写未来操作说明；**本次未执行任何评分、重放或 Play，B 未签 = 0**。原阈值、参数、剧本与真值隔离不变，不改 `tools/`、`controller/`。此句为 R2文档闭合当轮未签快照，现行已签状态以 §0/§6 为准，本轮 B信封落实亦未执行。

### 7.1 归档与两次评分调用（命令顺序固定）

仅归档 §2 隔离完成后**本次**产生的源文件；旧保全目录不混入、不进评分。收尾先按 §8 静止全部写者，再核三个源对象属本次、目标无同名项，才执行下列 `mv -n`；逐项确认源已移离且清单数量/字节/sha 相符。`mv -n` 不覆盖但可能跳过对象，返回成功不等于归档齐全；任何冲突/缺件/部分移动停报，保留所有对象，不删目标、不重试 Play、不拿旧真值顶替。所有写入/零模型评分共账 §0，余量不足先安全撤权并回报实际耗用/UNKNOWN。

```bash
mkdir -p $OUT/$SID/unity-runtime && mv -n runtime/frames runtime/m3_body_truth.jsonl runtime/scenario_config.json $OUT/$SID/unity-runtime/
shasum -a 256 $(find $OUT/$SID -type f) > $OUT/$SID/SHA256SUMS; du -sk $OUT/$SID
# 先按 §7.2 第 1 步核定 <S2序号>、<S4首次序号>、<换回序号>（均为未剔除的原全行序），不硬填示例序号
# 第一调用：S2 红车段 + S4 首次点击（AC-22 全会话、AC-23 第一段、AC-24、AC-25 只取本次）
"$PY" -m tools.eng_capture.analyze_play --session-dir $OUT/sessions/$SID --click-log $OUT/$SID.click-web.jsonl \
  --truth $OUT/$SID/unity-runtime/m3_body_truth.jsonl --s2-click <S2序号> --s4-click <S4首次序号> --output $OUT/$SID/play-readings.json
# 第二调用：同一 session-dir/click-log/truth，--s2-click 取 S4 换回红车且已绑定的那次点击，不带 --s4-click，输出另存（只取其 AC-23）
"$PY" -m tools.eng_capture.analyze_play --session-dir $OUT/sessions/$SID --click-log $OUT/$SID.click-web.jsonl \
  --truth $OUT/$SID/unity-runtime/m3_body_truth.jsonl --s2-click <换回序号> --output $OUT/$SID/play-readings-return.json
"$PY" -m controller.target_manager replay $OUT/sessions/$SID/tm_inputs.jsonl config/p1-eng-capture-001.json > $OUT/$SID/replayed-events.jsonl
```

### 7.2 点击序号核定（两次调用共用）

1. `--s2-click`/`--s4-click` 是点击日志中点击行（`kind` ∈ {`click_received`, `click_refused`}）按文件实际行序的序号（1 起）；页面拒收行（含未发送的畸形 `click_refused`）仍占工具序号，按 `click_id` 配对。只读列出：
   `"$PY" -c "import json,sys;rows=[r for r in (json.loads(l) for l in open(sys.argv[1]) if l.strip()) if r.get('kind') in ('click_received','click_refused')];[print(i,r.get('kind'),r.get('click_id'),r.get('reason')) for i,r in enumerate(rows,1)]" $OUT/$SID.click-web.jsonl`
2. `<S2序号>` = S2 点红车的那次点击；`<S4首次序号>` = S4 第一次点击（点静止车）；`<换回序号>` = S4 点回红车的那次点击。点哪辆车、是否已绑定须从现场记录与提交/授权日志（第一调用输出 `AC-22.rows[*].bound`/`commit_event_seq`、会话日志 `binding_committed`）核实，**不由序号推断目标身份**；序号不按 AC-22 合同分母重编号，也不改工具输入。

### 7.3 AC-23（两段同时取读）

1. **第一段** = 第一调用输出 `AC-23`：段 = [S2 提交事件后首个新绑定授权帧, S4 首次点击帧)。
2. **换回段** = 第二调用输出 `AC-23`：段 = [换回提交事件后首个新绑定授权帧, 会话末)（`segment` 末端为 `null` = 不限）。
3. 两段各照列 `losses`（逐次修复/准时报告；段末未结束的失观测 `ended_at = null`，截止落在段内未发生记不准时、落在段外记 `null`）、`all_losses_on_time`、`supported_frames_not_red_car_count`（=0 只是本次样本观察，不作风险上界）及原合同其余读数。
4. **AC-23 结论须同时覆盖两段修复/准时报告与原合同其余读数**：换回失败或缺段记失败/证据缺失，不能以首段通过代替。不得把未绑定（输出 `verdict = NOT_EVALUABLE`、`reason = S2 not bound`）、无授权帧（`frames_in_segment = 0`）或缺必需日志当作通过。
5. 第二调用输出中 `AC-23` 以外各项不采用：其 `AC-25` 不采用（AC-25 只用第一调用原 S2→S4 保持窗）；其 `AC-22` 与第一调用为同一点击流，不再计一次（AC-22 全会话只统计一次，两次 S4 点击均已在第一调用全会话内）。

### 7.4 AC-22（原日志对照，合同分母与工具读数分列）

1. 保留第一调用完整输出及原点击日志；原样单列工具较大口径的 `AC-22.denominator`、`AC-22.verdict`、`acceptance_subsegment_all_le_1` 与 `AC-22.rows` 逐行记录，标为「含未发送畸形拒收的工具读数，非 AC-22 合同判定」。
2. 按 §7.2 第 1 步列出的原日志实际全行序（1 起）与 `click_id`，逐行对照输出 `rows[*].index`/`rows[*].click_id`。**仅剔除原日志明确为 `kind = click_refused` 且 `reason = malformed_click` 的未发送行**，逐行列其原序号、`click_id`、拒收原因，另列畸形行数。不凭 `refused = true`、`request_id = null` 或 `verdict = FAIL` 一概剔除；其余被拒、超时、UNKNOWN、未绑定行全部保留。
3. 合同分母 = 工具行数 − 上述已核未发送畸形行数；另列保留行的原序号/`click_id`、`bound`、`e2e_frames`、`acceptance_subsegment_frames`（受理子段）、`wall_s`（墙钟，描述）及 PASS/FAIL 数。非空合同分母下，保留行全部已绑定且 `e2e_frames` ≤ 1 才是 AC-22 PASS；任一保留行未绑定或 `e2e_frames` > 1 为 FAIL。无发出点击记 NOT_EVALUABLE、不计通过；日志缺失、身份或行数无法对应记 EVIDENCE_MISSING、不计通过，不借剔除减少未知分母。原始工具总 FAIL 不直接等同合同 FAIL。
4. 若逐行输出与原日志不能支持上述分列，停报（不改 `analyze_play`、不过滤输入、不另跑评分）。

读数写入 `docs/evidence/P1-ENG-CAPTURE-001-play.md` §1–4（AC-22…25）；AC-26 用户目检由接受/辅助角色代录进 `docs/unity-test-log.md`。

## 8. 安全收尾（任何 STOP）

串行写 HOLD（会话 `stop` 先写显式 hold，`operator_stop` 收据）→ 停会话 → 用户停 Unity → 未决请求记 UNKNOWN → 归档 + 哈希清单。不删除任何工件。

## 9. 发令记录（执行时填写）

| 项 | 读数 |
|---|---|
| Air `git rev-parse HEAD` / `git status --porcelain` | 现场自动解析 `2beb08b1af5b14b53c0f23b9bdcaa2d1705f154a`；porcelain 空；Unity日志UT-P1-ENG-CAPTURE-001-PLAY1快照后仅日志/状态白名单文档提交，PLAY_GOVERNING空diff |
| 残留处置授权/执行者/运行时生成的保全路径与清单核验 | 账本 2026-10-10 RUNTIME-ARCHIVE 条；Air Implementation（残留保全）；路径/清单见 §2.1，Acceptance「发令前置核清」判处置满足；发令时核仍无旧源/写者 |
| 发令前 df / 端口 / 共享槽位 / 全局 blocks 检查 | 20:27:07Z现场：可用14,336,294,912 B；8774/runtime lsof无打开者；无会话/页面；blocks={}，轨道1消耗+1零消耗 |
| 终端执行者 / 用户现场窗口（选择后填写） | Air Implementation陪同；用户本会话确认本工程/非Play/当前可配合；B-HISTORIC-AUX-UNKNOWN已入账落实 |
| 已签逐维实际用量/收尾预留（UNKNOWN 单列） | 旧附属峰值UNKNOWN保留；已知清单+git/docs/script保守8 MB；后续250 MB采集+50 MB收尾+500 MB客户端预留，808 MB < 1 GB；基线原始文件prelaunch.json，后续峰值监控，新UNKNOWN仍停 |
| 覆盖文件 sha256 | 现场自动现算 `387ea2668f5b415fd48cfed5a2eb1d0f23c18dfa2ead2c4fd4688324e3608e60`；retained_frame_count=1500、其余配置逐值同源 |
| f₀、`T_sess` | |
| 准备已用 / 后续准备 / 按钮起止 / Z-B / 累计墙钟 | 原93 s；后续准备起 2026-10-10T20:29:08.238028+00:00，当前执行区间连续计时；会话≤230 s且依新f0/实际余量缩短，预留≥45 s收尾；尚未Play |
| STOP 码（如有） | |

## 10. 本人授权重开：第二次现场发令记录

授权与采集前对应见Unity日志UT-P1-ENG-CAPTURE-001-PLAY1第二attempt及账本两条直接授权。第一Play已用、139文件已同卷无覆盖保全，68帧不进新评分；会话/模型/正式ID此前均0。

| 项 | 第二次现场读数 |
|---|---|
| HEAD/porcelain | 自动现取 `24003b0fe6a588b19c718d3ab646bd95c5c32727`，porcelain空；最新passed_candidate祖先、PLAY_GOVERNING无差异，之后仅本操作单/状态白名单文档 |
| 覆盖 | 自动现算 `387ea2668f5b415fd48cfed5a2eb1d0f23c18dfa2ead2c4fd4688324e3608e60`；1500，其余配置同源逐值相等 |
| B预算 | 已核旧209.723 s及UNKNOWN保留；第二次≤420 s、B≤840 s；仅再Play1累计≤2，模型/session/run原未用额度，磁盘共账1 GB；已知B保守60 MB+后续250/50/500 MB预留=860 MB |
| 第二次准备基线 | 2026-10-10T20:36:26.568991+00:00；完整机器基线attempt-2-control/prelaunch.json；准备至收尾连续计时，新UNKNOWN停 |
| 运行窗口 | 新帧等候最多90 s，T_sess≤min(230,(1490-f0)/5,实际余量-55 s)；新鲜bundle场景/640×480/frame_id/时间核符才起会话；保留至少45 s收尾 |
| f0/T_sess/实际结果 | f0=0/T_sess=230 s；新帧0…902，用户手动停；12自由点击/11绑定，未核S2/S4/完整一圈；operator_stop APPLIED，服务退出0；机器launch/process-end与同名play.md§0–6 |
| 收尾/偏差 | 同卷归档1809文件/50,887,855 B，SHA全等；执行封口438.978 s，单attempt超18.978 s；已知磁盘保守291,059,456 B/旧UNKNOWN保留；无评分/重放，不重开；后续文档核清耗用不假记0 |

## 11. 用户授权正式测评：第三次 Play 新窗口

Owner: Air Implementation陪同；用户按Play/四次点车/一圈与目检。新信封逐字签发见账本同日正式测评条与提案对应落实；旧结果/耗用/超时/UNKNOWN不删除、不追认。预登记UT-FORMAL1在Unity日志；本批不改运行时代码。

新计量基线与完整元数据在 `outputs/eng-capture/formal/control/prelaunch.json`，准备到归档/两次评分/证据提交≤900 s，新基线新增≤1 GB；Play新增1、scenario0/session1/run≤3/YOLO加载≤1。新ID仅在本次新鲜帧核符后运行时生成，不覆旧目录。磁盘预留250 MB采集/归档+50 MB评分哈希+500 MB客户端/文档；到850 MB停止，保留收尾。等待新帧最多90 s；T_sess=min(270,(1490−f0)/5,实际余量−240 s)，且现场必须足以容纳剧本，否则停。保留至少240 s收尾；270 s墙钟护栏串行有效stop，不能依重建延长采集。

准备快照HEAD/空porcelain机器现取记在下表；之后本单/状态文档提交不递归Unity日志，发令时最终HEAD/porcelain写launch.json。全局blocks门/轨道check_docs通过；8774与旧会话进程只读均空；df可用13,643,468 KiB；三源无旧件。覆盖1500，其余值同源，SHA现场计算。四步点车语义由用户每次回复核定并与原click_id日志配对；不靠序号猜身份。新原件独立存formal目录，旧play不混评分；评分两次与replay顺序沿§7。

| 项 | 实测 |
|---|---|
| 准备HEAD/porcelain | 自动现取 `88240136a4a9bd5cc9c9795d2235ef5710465b03`；porcelain空 |
| 新基线 | 2026-10-10T21:01:08.423515+00:00；原件prelaunch.json |
| 覆盖 | `387ea2668f5b415fd48cfed5a2eb1d0f23c18dfa2ead2c4fd4688324e3608e60`；retained_frame_count=1500，其他值逐项同源 |
| 新鲜f0/T_sess/结果 | f0=0/T270；rebuild_limit/S-B-TERM提前终止，1332采集帧/717处理帧；原5点击/4绑定，AC22 FAIL；S2身份未知/一圈与S4未齐；同名formal-play.md§0–4 |

## 12. 正式重做：第四次 Play 独立新窗口

Owner: Air Implementation；用户自行完成四点击及红车完整一圈，仅提示开始/结束/异常。授权与UT-FORMAL2预登记已由Acceptance入账。旧失败、超时、UNKNOWN和原件保持，本批不改运行时代码。

新基线 2026-10-10T21:13:59.252429+00:00；原始计量 `outputs/eng-capture/formal-redo/control/prelaunch.json`。Play1/模型≤1/session1/run≤3/900s/新增≤1GB，仅Air；准备、采集≤290s、归档、两次评分、证据提交共账。250/50/500MB预留，到850MB停，收尾预留240s。每10s采样磁盘增量，保留采样盲区限制，不将未知追认为0。

现场准备HEAD `c91efa669a02a12490cdbf33916ead7ed79c376c`，porcelain 空；passed_candidate运行时解析，祖先成立，PLAY_GOVERNING零diff。8774无监听、旧控制/页面进程无、三源无旧件；df可用13,378,976KiB。覆盖retained_frame_count1500，其余配置同源逐项相等，SHA现场现算 `387ea2668f5b415fd48cfed5a2eb1d0f23c18dfa2ead2c4fd4688324e3608e60`。发令最终HEAD/porcelain/f0/T_sess在launch.json机器记录；等待新帧≤90s，T=min(290,(1490−f0)/5,余量−240s)，不足150s停。原件独立formal-redo目录；只有终场确认实际四次身份及完整一圈后，才按§7两次调用实际序号。旧页面须在新服务启动后刷新。

实际：f0=0/T290；4点击全部绑定，独立AC22读数PASS；publish_expired/catchup_stale后operator_stop，控制/页面exit0。监控晚停约13s、停止后误触新0…2混存，标准两次main/真值评分未跑；3009文件/71,686,913B移前后SHA全等。资源与未齐自证见同名formal-redo.md§0–3，未新验收通过。
