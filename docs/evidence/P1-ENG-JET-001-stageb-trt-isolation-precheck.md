# P1-ENG-JET-001 阶段B TRT 隔离只读预检（B-W-TRT-PRECHECK）

- 登记轮次：`阶段BTRT预检执行`；Dispatch-Id `P1-ENG-JET-001-阶段BTRT预检执行-20261005T185107Z-1c56`；Implementation（Opus 子代理，supervisor 派发）。
- 执行合同：同名提案「阶段B隔离修补合同准备（2026-10-05，Acceptance；执行草案未签）」§4；执行效力：同名提案「阶段BTRT预检授权落实（2026-10-05，Acceptance / CLARIFY）」§1–2。
- 信封：`docs/authorizations.md`「2026-10-05 P1-ENG-JET-001 — 用户选 B-W-ISO-PLAN I 并签发 B-W-TRT-PRECHECK：一批、一次 SSH、重试 0，墙钟 ≤300 s，板新增 0 B、Mac 新增 ≤10,000,000 B（supervisor 会话代录）」(b)；(c) 未签的安装/链接/运行维度保持 0。
- 机器证据：同名 `.json`（由驱动生成，与本机批次目录 `state.json` 字节相同）。本机原件目录取 JSON `output_dir_repo_relative`（`outputs/` 不入库，只在 Mac mini）。本文件只给摘要与指针，数字以 JSON 具名字段为准。

## 1. 结论

`outcome.verdict = COMPLETE`，无停止标签。B-W-TRT-PRECHECK 一批已用尽：SSH 预约 1/1、发出 1/1、重试 0、scp 0。§4 编号 1–5 的只读块全部执行到 `### end`，各块 rc=0。只记静态事实，不下 import、可加载、ABI 或兼容结论；最小链接闭集由 Acceptance 依原件冻结或具名退回用户。

## 2. 执行形式、前置与绑定

- 唯一顶层命令：`python3 <本批目录>/trt_precheck.py`，命中允许规则 `Bash(python3 ~/TetheredDroneTracking/outputs/eng-jet/P1-ENG-JET-001/*)`，后台运行；沿先例由驱动临时起 `caffeinate -i -w <脚本pid>`，随脚本退出，未改任何设置（JSON `mac_idle_sleep_assertion`）。驱动只用标准库，sha 见 JSON `script.sha256`。
- 本机前置（全部通过，JSON `authorization` / `settings_record` / `target` / `input_binding` / `slot`）：提案四个合同锚点存在；账本标题唯一、(b)(c) 关键句在；允许规则在、allowedDomains 不含板地址；目标从 `relay.json` `link.ssh` 运行时解析为唯一一个；输入 JSON（安装证据）记录的 W venv、sysvenv、系统 TRT 两根、python3-libnvinfer 版本与 glibc 均与驱动常量一致；状态板只有本项一条非暂停交接（Consuming=no），本机没有连到板的 ssh/scp/rsync 进程；本批 Mac 目录是唯一 `stageb-trt-precheck-*` 目录，且是新目录。git 前后 HEAD 一致、porcelain 为空（JSON `git_pre`/`git_post`，标识不手抄）。
- SSH 形式：`ssh -p 22 -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectionAttempts=1 -o ConnectTimeout=15 -o Compression=no <目标> 'LC_ALL=C timeout -k 2 210 sh -s'`，只读块经 stdin 送入（原样留在 `raw/board_block.sh`，sha 记在 JSON `ssh_invocation.stdin_block_sha256`）。`-p 22`、`Compression=no` 沿用安装批先例（不改参数和预算）。远端超时 210 s 来自 `min(剩余−60 s 收尾预留, 300−30−60)`，本机等待上限 220 s，同一截止。
- 块内实现说明（不改合同参数）：整块包在 `main(){…}` 内、以 `main </dev/null` 调用，防止块里的命令读走 stdin 上的脚本；每段在 stdout/stderr 各打段标记，便于两流分段；没有 heredoc、sort 或临时文件；路径并集用 awk 在内存去重。上板前只在本机 scratchpad 用假目录树和 GNU 风格替身命令，以 dash 干跑过块与解析器（正常路径，加路径超限、版本变化、ELF 超限、文本总量超限四个停止路径）；干跑没有碰板，也不计入批次。

## 3. 计次、上限与占用

| 维度 | 实测（JSON 字段） | 上限 |
|---|---|---|
| 批次 / SSH / 重试 | 1 / 1（`counts.ssh_reserved`=`ssh_issued`=1）/ 0 | 1 / 1 / 0 |
| 整批墙钟 | 起点 = min(目录 birthtime, `started_utc.txt`) = 19:06:46Z（`started.start_utc`）；证据 JSON 写完时 4.321 s（本机 `wallclock_end.json` `batch_elapsed_at_end_s`，该文件 mtime 与之一致）；SSH 本身 0.934 s | ≤300 s |
| 两流 | stdout 194,632 B + stderr 366 B = 194,998 B，未截断（`ssh_invocation.streams_total_B`） | ≤2,097,152 B |
| 路径并集 | dpkg+树 45，加库链 49；深度达到 8 的目录 0（`board_steps` trt_inventory） | ≤256、深度 ≤8 |
| 文本 | 17 件、167,085 B，单件最大 37,956 B；17/17 板端 sha 与 Mac 现算 sha 一致 | 累计 ≤1,048,576、单件 ≤262,144 |
| ELF | 4 个对象、输出共 10,904 B，单件最大 2,835 B | ≤64、单件 ≤16,384 |
| 板新增文件 | 0（块内无 scp、mkdir、写文件、tmp 或日志） | 0 B |
| Mac 新增 | 采样峰值 299,008 B（start/after_ssh/final_pre_evidence，`mac_occupancy`）；写入证据 JSON 后 499,712 B（`wallclock_end.json`，含批次目录及仓库证据 JSON 各一份）；另有本 md 与 305 B 的 `wallclock_end.json` | ≤10,000,000 B |

atime、SSH/PAM 等系统附带写入没有观测，记 UNKNOWN；采样之间的瞬时 Mac 峰值也记 UNKNOWN。本 md 和提交/推送不在批次墙钟内。

## 4. 读数摘要（原文在原件；JSON `board_steps` / `inventory` / `text_reads` / `elf_reads` / `startup_hooks`）

1. **身份/底座/余量/路径**：用户 jetson，HOME=/home/jetson，aarch64，glibc 2.39。dpkg：python3.12-venv 3.12.3-1ubuntu0.17、python3-pip 24.0+dfsg-1ubuntu1.3，python3-libnvinfer、python3-libnvinfer-dev、libnvinfer-dev、libnvinfer-plugin-dev 均为 10.16.2.10-1+cuda13.2，状态均 ii。eng-jet 所在 /dev/nvme0n1p1 的 Available 为 161,290,993,664 B，分配单元 4096。eng-jet 是普通目录；原 W cfg（195 B）和 sysvenv cfg（187 B）都是普通文件，readlink -f 指向自身；新落点 `edgellm-isolated-venv` 不存在（stat rc=1）。
2. **dpkg 清单 / TRT 树**：python3-libnvinfer 列 30 条路径，正好是 TRT 两根的全部对象，外加 doc 两件，以及 `LICENSE.txt` 和 `zip-safe`。python3-libnvinfer-dev 只有 doc。libnvinfer-dev 列出 `libnvinfer_static.a`、`libtensorrt_shim.so`（普通文件）和 `libnvinfer.so`（链接）。libnvinfer-plugin-dev 列出 `libnvinfer_plugin_static.a` 和 `libnvinfer_plugin.so`（链接）。树（`find -P`，不跟随链接）中，tensorrt 根有 13 项：`__init__.py`、`tensorrt.so`（5,760,928 B），以及 plugin 子包 9 个 .py；dist-info 根有 7 项。两根内都没有符号链接。库链都在同一目录内：`libnvinfer.so → libnvinfer.so.10 → libnvinfer.so.10.16.2`（普通文件），`libnvinfer_plugin.so → .10 → .10.16.2`（普通文件）。`.so.10` 和 `.so.10.16.2` 不在这四个包的清单里，归哪个包没有读。
3. **文本/静态导入**：METADATA 为 Name tensorrt、Version 10.16.2.10，Requires-Dist 只有 `numpy; extra == "numpy"`，没有 Requires-Python。WHEEL 为 `Root-Is-Purelib: true`，`Tag: cp312-none-linux_aarch64`。top_level.txt 为 `tensorrt`。RECORD 16 行，列出全部包文件。`__init__.py` 在 try 中可选导入 `tensorrt_libs`（ImportError 时跳过），按 PATH 和 `tensorrt.libs` 找 DLL、做 `ctypes.CDLL` 的代码只在 Windows 分支，随后 `from .tensorrt import *`；numpy 只在 `nptype()` 函数内导入。plugin 子包的模块在模块级导入 numpy 和 tensorrt，`_lib.py` 在函数内导入 triton。`__init__.py` 没有静态导入 plugin。LICENSE.txt 和 zip-safe 不在 §4 具名文本集内，没有读。
4. **ELF（readelf -h -d -W）**：4 个对象都是 ELF64、AArch64、DYN。`tensorrt.so` 的 NEEDED 为 `libnvonnxparser.so.10`、`libnvinfer_plugin.so.10`、`libnvinfer.so.10` 及 libstdc++/libgcc_s/libc/ld-linux；RUNPATH 原文为 `$ORIGIN:$ORIGIN/../_libs)`（右括号是原输出字面）。`libnvinfer.so.10.16.2`（SONAME `libnvinfer.so.10`）只依赖 libstdc++/libm/libgcc_s/libc/ld-linux。`libnvinfer_plugin.so.10.16.2`（SONAME `libnvinfer_plugin.so.10`）依赖 `libnvinfer.so.10`、librt 及上述系统库。`libtensorrt_shim.so` 只依赖系统 C/C++ 运行库。四者都没有 RPATH；三个系统库都没有 RUNPATH。
5. **启动钩子**：`/usr/lib/python3.12/sitecustomize.py` 是符号链接，指向 `/etc/python3.12/sitecustomize.py`（155 B），内容是在 try 中导入 `apport_python_hook`，ImportError 时 pass。`site.py` 23,903 B、`apport_python_hook.py` 8,695 B 全文已读，原件中的偏移和 sha 见 JSON；导入行和定位行已静态提取（`text_reads[].imports` / `locator_lines`），没有执行。

## 5. UNKNOWN、未覆盖与主张上限

- `libnvonnxparser.so.10`（tensorrt.so 的 NEEDED）不在 §4 闭集内，按合同没有搜索，其位置、所属包和 ELF 均为 UNKNOWN。`libnvinfer.so.10`、`.10.16.2` 及 plugin 对应文件的所属包没有读。RUNPATH 中的 `$ORIGIN/../_libs)` 目录是否存在，没有查。`tensorrt_libs` 在无 system-site 环境下是否可见、要不要它，都是 UNKNOWN。缺输出不推出“无依赖”。
- 关闭 system-site 后，sitecustomize→apport 这一路径会走到哪个分支、site.py 的 Debian dist-packages 逻辑如何作用，只有静态文本，运行行为 UNKNOWN。
- 本批不证 import、动态加载、ABI、CUDA、numpy 2.2.6 与 TRT 绑定兼容，也不证模型或性能，AC-7/8/9 不因此满足。原 W 现场与 `STATIC_CHECK_FAILED`、INSTALL-W 用尽、S1/S2 STOP、SR5/5 耗尽、补丁未上板、R1-5/6 OPEN 都保持；Overall `REVIEW_PASSED` / Lifecycle `ACTIVE` 只属于 A 候选。
- 没有做：下载、联网取元数据、传板、安装、建 venv、建链接、pip/pip check、python/import/ldd、模型、建引擎、测试、云、部署、sudo/apt，也没有改系统/SSH/沙箱/Claude 设置，没有删除任何文件，没有扫描整个系统 site 或 sysvenv。
- 回交：Acceptance 核清本原件，冻结 §3 白名单或具名退回用户。本轮 needs_user=none。
