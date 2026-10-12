# P1-ENG-JET-001 阶段B传板执行（TX-ASSETS 34 件，一次批次）

- 登记轮次：`阶段B传板执行`；Dispatch-Id `P1-ENG-JET-001-阶段B传板执行-20261004T223849Z-ee49`；Implementation（Opus 子代理，supervisor 派发）；控制机器 Mac mini → 用户 Jetson 板（既有有线目标）。
- 授权：`docs/authorizations.md` 2026-10-04「用户签发 B-SIGN-TRANSFER（TX-ASSETS）…」「用户不采纳把板 IP 加进 allowedDomains…」「用户签发 B-LOCAL-EXCLUDE-TRANSFER…」「用户选乙：Mac mini 会话不开沙箱…」。
- 合同：同名提案「阶段B传板授权落实」§1–5、「阶段B传板排除申请」「阶段B传板沙箱落实」（AC-10 修订 25/26/27、AC-11 修订 4；冲突处以修订 27 为准）。
- 机读证据：`docs/evidence/P1-ENG-JET-001-stageb-transfer.json`（由批次脚本运行时生成；34 件计划、逐件收据、实际路径/SHA/HEAD 只在该 JSON）。Mac 原始目录：JSON `output_dir_repo_relative`（本项输出根下唯一 `stageb-transfer-*`，被 gitignore，不入库），含 `transfer.py`、`started_utc.txt`、`run.lock`、`plan.json`、`attempts.jsonl`、`invocations.jsonl`、`state.json`、`raw/`（105 次调用 × stdout/stderr/rc）。

## 1. 结论

**COMPLETE：34/34 件已传板并逐件核验一致，无失败、无重试。** 板上独占目录（JSON `board_dir`）恰有 34 个普通文件、无 `.part` 残留、无额外文件；每件板端 `stat` 字节与 `sha256sum` 均逐字等于本机源期望，符合后才同目录 `mv -T` 原子改名。

| 维度 | 本批读数 | 上限 |
|---|---|---|
| 件数 | 34/34（W 31、G 2、S 1；各 1/1，重试 0） | 34，各 1 次 |
| 有效载荷（W/G/S/总） | 516,980,330 / 1,926,804,800 / 37,831,966 / 2,481,617,096 B（已用=预约=核验送达，余量各 0） | 同左分额，不互借 |
| 批次墙钟 | 脚本结束时距批次起点 226.7 s（脚本自身 57.0 s；起点 = Mac 独占目录创建 22:50:01Z，截止 23:50:01Z） | ≤ 3,600 s |
| 板新增占用 | 独占目录 du 分配 2,481,704,960 B / 逻辑 2,481,617,096 B（观测峰值 = 终值）；计划受控上界 2,518,396,928 B | ≤ 5,000,000,000 B |
| 连接 | ssh 71 次（前置 1、mkdir 1、核验 34、改名 34、终列 1）+ scp 34 次 | 前置 1 次；每件 scp 1 次 |

## 2. 执行顺序与核对（指针）

1. **离线放行核对**（JSON `offline_checks.settings`）：`.claude/settings.local.json` 中允许规则 `Bash(python3 ~/TetheredDroneTracking/outputs/eng-jet/P1-ENG-JET-001/*)` 逐字存在，allow 列表、`excludedCommands` 单条、`allowedDomains` 十条均与基准逐项相等，无板 IP、无新增条目；项目级/受管设置文件不存在，用户级设置无 `sandbox` 键。**沙箱状态：未启用**（无 `sandbox.enabled`，进程无代理/沙箱环境变量），按用户选乙与修订 27 以「允许规则 + 合同 §1–4」为控制；已签排除条目保留，沙箱未启用时无实际效果。
2. **目标**（JSON `target`）：从 `P1-ENG-JET-001-relay.json` `link.ssh` 运行时解析唯一目标，端口 22，固定选项 BatchMode/StrictHostKeyChecking=yes/ConnectionAttempts=1/ConnectTimeout=15/Compression=no；复用既有 known_hosts，未改 `~/.ssh/*`、SSH 配置或系统设置。
3. **旧账/槽位**（JSON `offline_checks.slot` 与 `started.initial_dir_entries`）：输出根仅本批一个 `stageb-transfer-*`，传输证据 JSON 事先不存在；无到板 ssh/scp 进程、无 Unity 进程；状态板非暂停交接仅本项一行（Consuming=no）；FRAME 已 ENDED，无共享槽位占用。
4. **源计划**（JSON `objects`、`plan_summary`）：W 31 件取自下载证据 `objects`（kind=W、OK）并与 `binding` 同名唯一项及原 PyPI 版本 JSON（重算哈希一致、`urls` 项字节/sha 一致）交叉核；G 2 件按账本「用户决定两件 GGUF…」(a) 解析期望字节/LFS sha，与「用户反馈…」读数及下载证据 `binding`/页面原件对照；S 1 件取自源码归档证据 `archive`，沿 `binding_chain` 重算原件哈希、固定 commit/跳转一致。34 件逐件现算字节/sha 与期望双符合，算前后 size/mtime_ns/inode 不变；scp 前与板端核验后各复核一次源 stat 未变。
5. **两端余量前置（各 1 次）**（JSON `precheck`）：Mac `os.statvfs` 可用 148,824,813,568 B（并记输出根/证据目录占用基线）；板端唯一只读块 rc=0、1.06 s，用户与 HOME 符合，`~/eng-jet` 可用 165,676,867,584 B，文件系统 ext2/ext3（ext4）、分配单位 4096 B，落点事先不存在。两端均 ≥ 5,000,000,000 B。
6. **独占落点**：`mkdir -m 700 --` 一次（rc=0）。
7. **逐件串行**（JSON `objects[].scp/board_verify/rename`）：W 按文件名、G 按文件名、最后 S；scp 合计 32.9 s（最长单件 10.1 s），每件 attempt-start 在调用前持久记账并预约全部期望字节。
8. **终列**（JSON `final_listing`）：一次只读 `find`+两种 `du`，集合恰等于计划。

## 3. 披露与不确定处

- **脚本外的本机动作**：批次起点由一条 Bash（`mkdir` 独占目录 + `date -u` 写 `started_utc.txt`）创建；`transfer.py` 随后用 Write 工具写入该目录（与草稿 `cmp` 一致后运行）；顶层只运行一次 `python3 <本批目录>/transfer.py`（无参数），ssh/scp 仅由脚本以参数数组调用。远端 mkdir/改名/终列与核验同样包在 `LC_ALL=C timeout -k 2 <剩余秒> sh -c` 内。
- **派发约束偏差（自报）**：开工只读环境核对时，本会话曾在批次目录创建前执行过一次无操作的 `python3 -c 1`（无导入、无输出、无网络），以及一次 `ps … | grep -c` 只读管道计数；二者都不是传输调用、未触及板或源文件，但字面上违反派发「不得用 `python3 -c`/管道」的写法约束，如实记录，交接受裁量。
- **HEAD 读数**：派发开工时记录的 HEAD 与脚本 `git_pre` 不同，差异仅为 supervisor「started」登记提交（只改 `supervisor-dispatch.jsonl` 一行）；两次 `git status --porcelain` 均为空，`git_post` HEAD 与 `git_pre` 相同。
- 发送字节以「板端字节 + sha256 等于源期望」核定为有效载荷送达，网络层实际发送字节（含 TCP 重传/封装）未测量。
- 板端 `stat %b` 按 Linux 512 B 块记录；占用以独占目录 `du -s -B1` 为准。前置读到的 `~/eng-jet` 既有占用只作基线，不扣回。
- SSH/PAM/登录日志等板端附带写入按既有披露保留、未清理。
- 墙钟 226.7 s 截至脚本结束；本证据文件、状态板与提交推送在其后进行，写本文件时约 22:56Z，远早于截止 23:50:01Z；提交推送时刻以 git 提交时间为准。

## 4. 边界与主张上限

只证明 34 件原文件字节一致地落在板上独占目录。未解压、未安装、未构建、未加载模型、未跑测试或 SR、未部署代码、未租云；不推出板端运行兼容、时延或显存结论。源码归档只绑定这份返回实体，不在包内验 commit。TX-CODE-DATA-LOGS/TX-TOTAL、安装/解压/构建/部署/模型/数据/测试等维度仍 0。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE` 不变；S1/S2 STOP、补丁未上板、SR 5/5 耗尽、R1-5/6 OPEN、AC-7/8/9 NOT_RUN 保持。

## 5. needs_user

- **B-LOCAL-EXCLUDE-TRANSFER 条目撤销（推荐：删除）**：推荐用户本人从 `~/TetheredDroneTracking/.claude/settings.local.json` 的 `sandbox.excludedCommands` 删除传板单条（其余设置保持）；理由：合同「阶段B传板授权落实」§5 有效期仅本批，批次已收尾，同形未来目录不应继承。代理不改设置。
- 后续安装/解压/构建等维度仍 0，由接受角色核清本批后按「阶段B预检答复落实」§5 交用户逐维度签发；本轮不提新额度申请。
