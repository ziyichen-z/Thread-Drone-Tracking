# P1-ENG-JET-001 阶段B构建执行：前置停止（构建未开始）

登记轮次 `阶段B构建执行`；Dispatch-Id `P1-ENG-JET-001-阶段B构建执行-20261005T031100Z-5666`；Implementation（Opus 子代理），Mac mini。
合同：同名提案「阶段B构建授权落实（2026-10-04，CLARIFY）」§1–7、AC-10 修订 28；信封：`docs/authorizations.md`「2026-10-04 P1-ENG-JET-001 — 用户签发 BUILD-LLAMA：板上离线构建 llama.cpp 1 次、重试 0，墙钟 ≤2 h，板新增占用 ≤5 GB（supervisor 会话代录）」(a)–(f)。

## 1. 结论

**STOPPED / `PRECHECK_FAILED`（§4 前置未全部满足，构建未开始）。** 失败项只有一项 `tools_in_usr_bin`，原因是**实现驱动脚本的缺陷**，不是板端环境缺件：脚本把 `command -v gcc g++ make` 写成一条命令，板端 `sh`（dash）的 `command -v` 只处理第一个参数，原输出只有 `/usr/bin/gcc` 一行（rc=0），脚本要求三行，于是判为不满足。g++、make 是否位于 `/usr/bin`，本次**未读到**（UNKNOWN）；同一批次中 `g++ -dumpfullversion`=13.3.0、`make --version`=GNU Make 4.3 都已成功执行，说明两者在 PATH 上，但不能替代 §4 的位置判据。

按 §4「任一不满足即停、不算一次构建；前置阶段失败保留读数并回交」，本轮已停止并回交：没有重跑前置，没有改脚本后再跑，没有进入 mkdir、解压或 cmake。

## 2. 指针（JSON 与原件）

- 机读证据：`docs/evidence/P1-ENG-JET-001-stageb-build.json`（脚本生成；字段 `outcome`、`precheck.items`、`input_binding`、`started`、`wallclock`、`counts`、`counts_invocations`、`git_pre`、`git_post`、`steps.precheck`）。
- 本机批次目录（gitignored）：`outputs/eng-jet/P1-ENG-JET-001/stageb-build-20261005T032116Z/`，含 `build.py`、`started_utc.txt`、`run.lock`、`invocations.jsonl`、`state.json`、`raw/001-precheck.{stdout,stderr,rc}`，均原样保留。
- 原件 sha256：`raw/001-precheck.stdout` `7ad514e78e201db57f58ee87489b7a9b71e24fa72d279fcd151bef9ee265f2be`；`.stderr` 0 B；`.rc`=0（ssh 整体）。驱动脚本 sha256 见 JSON `script.sha256`。

## 3. §4 前置逐项读数（一次只读 ssh，板端 `LC_ALL=C timeout -k 2 300 sh -c <只读块>`）

| 项 | 读数 | 判定 |
|---|---|---|
| 用户 / HOME / `~/eng-jet` | jetson / /home/jetson / 目录存在且不是链接 | 符合 |
| 磁盘 `df -B1 /` 可用 | 163,185,614,848 B | ≥5,000,000,000 B，符合 |
| cmake | `/usr/bin/cmake`，3.28.3 | ≥3.18，符合 |
| nvcc | `/usr/local/cuda/bin/nvcc` 可执行，release 13.2，V13.2.78 | 符合 |
| gcc / g++ 版本 | 13.3.0 / 13.3.0 | 符合 |
| make | GNU Make 4.3 | 存在 |
| gcc、g++、make 位于 /usr/bin | 只读到 `/usr/bin/gcc`（驱动缺陷，见 §1） | **不满足（g++、make 位置 UNKNOWN）** |
| `/usr/local/cuda` 链接 | `/etc/alternatives/cuda` | 符合 |
| `targets/sbsa-linux` | 存在 | 符合 |
| 输入 S 文件 | 普通文件，37,831,966 B | 符合 |
| §1 重算 sha256 | `caf971165313952eb4222c4b4a0ee77e5bec79f496d73d6d5a0be8b7d3c87669`，与运行时解析的期望逐字一致（`stageb-transfer.json` objects 中 archive.tar.gz 项与 `stageb-source-archive.json` `archive` 两处一致后才采用） | 符合 |
| 板上批次目录 `~/eng-jet/stageb-build-20261005T032116Z` | 事先不存在（`absent`）；`stageb-build-*` 无匹配（ls rc=2） | 符合 |
| SSH 目标 | `relay.json` `link.ssh` 解析出唯一目标 `jetson@192.168.8.2`，端口 22，使用既有 known_hosts，`BatchMode=yes`、`StrictHostKeyChecking=yes` | 符合 |
| 本机离线核对 | 账本标题逐字唯一且含 (a)–(d) 原文；提案标记与 §2 十个 `-D` 逐字存在；Active handoffs 中未暂停的只有本项（Consuming=no）；本机无连向板的进程 | 符合 |

JSON 中 `precheck.items` 有几项的 `rc` 显示为 null，原因是检查项名和原输出块名不同（例如 `df_avail_ge_5e9` 对应 `df` 块），这只是字段映射问题；原 rc 以 `raw/001-precheck.stdout` 的 `### rc=` 行为准，除 `prior_builds`（预期 rc=2）外均为 0。

## 4. 消耗与上限

| 维度 | 读数 | 上限 |
|---|---|---|
| BUILD-LLAMA 次数 | **0**（未进入 cmake 配置） | 1，重试 0 |
| 整批墙钟 | 3.766 s（Mac 批次目录 03:21:16Z 创建 → 脚本 03:21:19.77Z 结束；截止 05:21:16Z） | ≤7,200 s |
| 板新增占用 | **0 B**（未 mkdir，板端只执行了只读命令） | ≤5,000,000,000 B |
| SSH 调用 | 1 次（前置），scp 0 | — |
| 网络、下载、安装、运行产物、模型、测试、云 | 0 | 0 |

git 凭据：`git_pre` 与 `git_post` 的 HEAD 相同，porcelain 均为空（见 JSON）。本机驱动另外起了 `caffeinate -i -w <脚本pid>`，作用是防止本机在构建期间进入空闲睡眠，随脚本结束一起退出，没有改任何设置；已在 JSON `mac_idle_sleep_assertion` 中披露。

## 5. 偏差自报（实现方法错误）

- **D-1 驱动缺陷**：前置块把三个名字写进一次 `command -v`，dash 只输出第一个名字。这是实现侧的写法错误，导致前置项假阴性，本次构建因此没有执行。修正方法很直接：拆成三次 `command -v gcc`、`command -v g++`、`command -v make`。但是否允许另起新批次、用修正后的驱动重跑前置并构建，属于合同 §4「回交」之后的决定，本轮不自行重跑。
- 执行形式：沿用传板先例，用目录脚本 `python3 <本批目录>/build.py`（命中既有允许规则）作为唯一的顶层命令，在后台运行；板端调用逐次按合同包了 `LC_ALL=C timeout -k 2 <剩余秒>`。合同 §2 的参数没有被使用（构建未开始），也没有被更改。

## 6. needs_user / 回交事项

- **B-BUILD-RERUN（先交 Acceptance 裁定，超出接受权限时交用户）**：推荐由 Acceptance 记一行归因，允许 Implementation 新建一个独占批次（Mac 和板上各一个新的 UTC 目录），用只修 D-1（三次 `command -v`）的驱动重做 §4 前置和 §1 sha 重核，满足后按 §2 构建 1 次。理由：本次构建次数仍是 0/1，重试 0 没有动用，板新增 0 B，墙钟只用了 3.8 s，失败原因是实现侧写法，环境读数其余全部符合。推荐的保守口径：两批墙钟合计 ≤7,200 s（新批上限 7,196 s），板新增占用仍按 5 GB 封顶；新证据另起文件名，本文件和 JSON 保留为第一批的原始记录，不覆盖。其余维度仍 0、不含云，INSTALL-W 仍 0。
- 延续条目（不是本轮新增）：B-LOCAL-EXCLUDE-TRANSFER 排除条目仍推荐用户本人删除（代理不改设置）。

主张上限：本轮只证明以下几点：S 副本在板上的 sha256 与期望一致；cmake 3.28.3、nvcc 13.2、gcc/g++ 13.3.0、make 4.3 可以调用；磁盘余量足够。不证明可以构建，也不涉及运行、兼容性、性能或显存结论。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE` 不变；不消费 verdict，不签 DONE；S1/S2 STOP、SR 5/5 耗尽、R1-5/6 OPEN、AC-7/8/9 `NOT_RUN` 维持原状。
