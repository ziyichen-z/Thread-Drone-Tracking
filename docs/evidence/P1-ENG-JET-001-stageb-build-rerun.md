# P1-ENG-JET-001 阶段B构建重跑执行：构建完成（llama-server 产物存在）

登记轮次 `阶段B构建重跑执行`；Dispatch-Id `P1-ENG-JET-001-阶段B构建重跑执行-20261005T033036Z-4c27`；Implementation（Opus 子代理），Mac mini。
合同：同名提案「阶段B构建授权落实（2026-10-04，CLARIFY）」§1–7（AC-10 修订 28），经「阶段B构建前置停止核清（2026-10-04，Acceptance / CLARIFY）」§1–3（AC-10 修订 29，唯一差异闭集）解释；信封：`docs/authorizations.md`「2026-10-04 P1-ENG-JET-001 — 用户签发 BUILD-LLAMA：板上离线构建 llama.cpp 1 次、重试 0，墙钟 ≤2 h，板新增占用 ≤5 GB（supervisor 会话代录）」(a)–(f)。

## 1. 结论

**COMPLETE。** 本批是修订 29 允许的唯一一次新独占批次：§4 前置全部满足（含修正后的 `tools_in_usr_bin`：三行依次为 `/usr/bin/gcc`、`/usr/bin/g++`、`/usr/bin/make`），§1 S sha256 板上重算与期望逐字一致；随后进入 cmake 配置 1 次（rc=0），按 §2 固定参数构建 `llama-server` 目标（rc=0），产物 `build/bin/llama-server` 是非空普通文件。没有越界、没有重试、没有出现外联行为。

## 2. 指针（JSON 与原件）

- 机读证据：`docs/evidence/P1-ENG-JET-001-stageb-build-rerun.json`（驱动生成；字段 `outcome`、`first_batch`、`caps`、`precheck.items`、`unpack`、`cmake`、`steps`、`monitor_samples`、`occupancy`、`products`、`counts`、`counts_invocations`、`wallclock`、`git_pre`、`git_post`）。
- 本机批次目录（gitignored）：`outputs/eng-jet/P1-ENG-JET-001/stageb-build-20261005T033318Z/`，含 `build.py`、`started_utc.txt`、`run.lock`、`invocations.jsonl`、`state.json`、`raw/`（37 次 ssh 调用的 stdout/stderr/rc 原件）。驱动 sha256 见 JSON `script.sha256`。
- 板上批次目录：`/home/jetson/eng-jet/stageb-build-20261005T033318Z/`（`src/`、`build/`、`raw/`，其中 `raw/monitor.log`、`raw/cmake-configure.*`、`raw/cmake-build.*` 是完整日志原件），按合同 §3 整体保留，未清理。
- 第一批账（只读、未改动）：`docs/evidence/P1-ENG-JET-001-stageb-build.json/.md` 与 `outputs/eng-jet/P1-ENG-JET-001/stageb-build-20261005T032116Z/`；本批运行时从第一批 JSON `output_dir_repo_relative` 解析旧目录并确认与新目录不同，三者 sha256 记于本批 JSON `first_batch`，收工时重算与之一致。

## 3. 与第一批驱动的差异（只在修订 29 闭集内）

1. **D-1**：tools 采集改为 `command -v gcc && command -v g++ && command -v make`；三行 `/usr/bin` 逐字判据不变。rc 字段映射等其他判据未改（因此 `precheck.items` 中部分 `rc` 仍显示 null，原 rc 以 raw 原输出为准）。
2. **命名与绑定**：round/Dispatch 改为本轮；证据写 `stageb-build-rerun.json`（JSON 或 MD 已存在即停）；Mac 端批次目录检查改为"恰好是第一批旧目录加本批新目录"；提案标记检查追加修订 29 的三处字面。
3. **墙钟**：读第一批 `wallclock.batch_elapsed_at_script_end_s`=3.766，向上取整扣 4 s，新批上限 7,196 s（与合同数不一致即停）。
4. **占用**：第一批工件按控制流记 0 B（第一批 steps 只有 precheck，未 mkdir），本批上限 = 5,000,000,000 − 0；监测口径（`du -sb` 与 `du -s -B1` 取较大值）不变。

cmake 参数、生成器、`-j 4`、执行栈、监测间隔与停止规则一律沿用第一批驱动原文。

## 4. 读数摘要

| 项 | 读数 |
|---|---|
| 前置 | 全部满足；df 可用 163,185,582,080 B；cmake 3.28.3；nvcc release 13.2；gcc/g++ 13.3.0；GNU Make 4.3；`/usr/local/cuda` → `/etc/alternatives/cuda`；sbsa-linux 存在；S 普通文件 37,831,966 B，sha256 与运行时解析的期望一致；新板目录事先不存在，`stageb-build-*` 无匹配（ls rc=2） |
| 解压 | `tar -xzf` rc=0；单一顶层目录 `ggml-org-llama.cpp-836d571` |
| cmake 配置 | rc=0，12.2 s；命令逐字见 JSON `cmake.configure_command`（10 个 `-D` 与合同 §2 顺序、取值一致） |
| 构建 | `cmake --build <build> --config Release -j 4 --target llama-server`，rc=0，1,724.422 s |
| 产物（只做 stat/ls） | `build/bin/llama-server` 普通文件 72,424 B（动态链接，同目录有 `libggml-cuda.so.0.25.3` 61,451,472 B、`libllama.so`、`libllama-server-impl.so`、`libmtmd.so` 等，见 JSON `products.bin_ls`）；从未执行 |
| 外联检查 | 配置/构建日志强模式命中 0；弱模式 3 行均非外联：编译 `common/download.cpp` 源文件的进度行，以及 CMake 提示"未嵌入 UI、离线环境可手动下载"的警告文本（含 URL，无下载动作）；31 次采样 `ss` 均无构建进程连接 |
| 内存 | 采样 MemAvailable 最低 4,539,972 kB，无 OOM 迹象 |

## 5. 消耗与上限

| 维度 | 本批 | 两批合计 | 上限 |
|---|---|---|---|
| BUILD-LLAMA 次数 | 1（03:33:24Z 进入配置时记账） | 1（第一批 0） | 1，重试 0 |
| 墙钟 | 1,743.223 s（批次目录 03:33:18Z → 脚本 04:02:21Z） | 1,746.989 s（含第一批 3.766 s） | 新批 7,196 s；合计 7,200 s |
| 板新增占用峰值 / 终值（`du -sb`） | 393,323,276 B / 393,323,276 B | 同（第一批 0 B） | 5,000,000,000 B |
| 板新增占用峰值 / 终值（`du -s -B1` 分配量，取较大口径） | 411,414,528 B / 411,414,528 B | 同 | 5,000,000,000 B |
| df 可用最低 | 162,773,512,192 B | — | 停止线 1,000,000,000 B |
| ssh / scp / 重试 | 37 / 0 / 0 | — | — |
| 网络下载、安装（INSTALL-W）、运行产物、加载模型、测试、云 | 0 | 0 | 0 |

峰值是 60 s 采样的最大值，采样之间的瞬时峰值 UNKNOWN。git 凭据：`git_pre` 与 `git_post` 的 HEAD 相同，porcelain 均为空。驱动沿用第一批执行形式：目录脚本 `python3 <本批目录>/build.py` 作唯一顶层命令、后台运行，板端每次调用包 `LC_ALL=C timeout -k 2 <剩余秒>`；本机临时起 `caffeinate -i -w <脚本pid>` 防空闲睡眠，随脚本退出，没有改任何设置（JSON `mac_idle_sleep_assertion`）。

## 6. 主张上限与 needs_user

主张只到：固定 b11381 源码副本 S 按合同 §2 固定参数，可以在本板构建出 `llama-server`。不证明它能运行，也不涉及兼容性、性能、时延、内存/显存结论，更不推出 GGUF 可以运行；网络检查只是日志模式扫描加 60 s 一次的 `ss` 采样，采样之间的短连接 UNKNOWN。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE` 不变，不消费 verdict、不签 DONE；S1/S2 STOP、补丁未上板、SR 5/5 耗尽、R1-5/6 OPEN、AC-7/8/9 `NOT_RUN` 维持原状。

- 本轮无新增 needs_user。BUILD-LLAMA 已用尽（1/1）；产物的任何使用（G2 服务冒烟/运行等）须另签维度，INSTALL-W 仍为 0。
- 延续条目（不是本轮新增）：B-LOCAL-EXCLUDE-TRANSFER 排除条目仍推荐用户本人删除（代理不改设置）。
