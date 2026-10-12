# P1-ENG-JET-001 阶段B安装执行：31件全部装上，装后 pip check 不过（STATIC_CHECK_FAILED）

登记轮次 `阶段B安装执行`；Dispatch-Id `P1-ENG-JET-001-阶段B安装执行-20261005T051427Z-c14d`；Implementation（Opus 子代理），Mac mini。
合同：同名提案「阶段B安装合同准备（2026-10-05，Acceptance / CLARIFY；执行待用户签数值）」§1–7，执行效力见「阶段B安装授权落实（2026-10-05，Acceptance / CLARIFY）」。信封：`docs/authorizations.md`「2026-10-05 P1-ENG-JET-001 — 用户签发 INSTALL-W：W31 独立 venv 离线逐文件安装 1 批、重试 0，墙钟 ≤3,600 s，板新增占用 ≤5,000,000,000 B（supervisor 会话代录）」(a)–(g)。

## 1. 结论

**STOPPED，停止原因 `STATIC_CHECK_FAILED`（合同 §6 具名原因）。** 前置一次全部满足；独立 venv 创建 1 次成功；31 个固定轮子按 §1 顺序逐文件各装 1 次，rc 全为 0；`pip list --local --format=json` 1 次与计划 31 项名称/版本逐项一致（另有种子 pip 24.0 单列）；静态读取核对（pyvenv.cfg、本地 dist-info、TRT 来源、sysvenv 不在路径）8/8 通过。随后 `pip check` 1 次 rc=1，输出两行，都是系统 site（`--system-site-packages` 可见）里的 apt 包，不是 W31 本身：

```
pynacl 1.5.0 requires cffi, which is not installed.
scipy 1.11.4 has requirement numpy<1.28.0,>=1.21.6, but you have numpy 2.2.6.
```

按 §5“系统 site 可见的其他包若产生冲突，保留完整输出、记静态核对失败并停，不以旧冲突自动豁免”处置：pip check 是最后一步，之后没有剩余安装/核对步骤；没有删系统包、没有补装 cffi、没有换 numpy、没有重试。venv 与板上批次目录原样保留。由 Acceptance 核清、用户决定。

## 2. 指针

- 机读证据：`docs/evidence/P1-ENG-JET-001-stageb-install.json`（驱动生成）。主要字段：`outcome`、`authorization`、`input_binding`、`files`（31 件顺序/期望字节与 sha/ZIP 解压字节与成员数/板上重核/attempt/rc/状态/发令前占用推算）、`precheck.items`、`startup_hooks`、`w31_recheck`、`steps`（逐次 argv 等价命令、内外层超时、发令时剩余秒、rc、stdout/stderr 尾部）、`venv_seed`、`venv_static_post_create`、`pip_list_compare`、`post_static_reads`、`pip_check`、`monitor_samples`、`occupancy`、`old_snapshot_pre/post`、`old_inputs_unchanged`、`counts`、`wallclock`、`git_pre/git_post`、`claim_ceiling`。
- 本机批次目录（gitignored）：JSON `output_dir_repo_relative`，含 `install.py`、`started_utc.txt`、`run.lock`、`invocations.jsonl`、`state.json`、`raw/`（74 次 ssh 调用的 stdout/stderr/rc 原件）。驱动 sha256 见 JSON `script.sha256`。
- 板上批次目录与 W venv：JSON `board_paths`（批次目录含 `raw/`、`tmp/`、`home/`、`cache/`、`install-plan.tsv`；`raw/` 内每步 `.stdout/.stderr/.rc/.pids` 原件与 `monitor.log`），按合同保留、未清理。

## 3. 执行形式

沿用构建批先例：本批 Mac 目录内驱动 `python3 <本批目录>/install.py` 作唯一顶层命令（命中允许规则 `Bash(python3 ~/TetheredDroneTracking/outputs/eng-jet/P1-ENG-JET-001/*)`），后台运行；`caffeinate -i -w <脚本pid>` 防空闲睡眠，随脚本退出，未改设置（JSON `mac_idle_sleep_assertion`）。SSH 目标从 `relay.json` `link.ssh` 运行时解析，BatchMode/StrictHostKeyChecking/ConnectionAttempts=1/ConnectTimeout=15。每次板端调用外层包 `LC_ALL=C timeout -k 2 <剩余秒> sh -c`；venv 创建、31 次 pip install、pip list、pip check 都是合同 §2/§5 固定命令原文（内层 `LC_ALL=C timeout -k 2 <剩余秒> env HOME/TMPDIR/XDG_CACHE_HOME=<批次>… PIP_CONFIG_FILE=/dev/null PIP_CACHE_DIR=<批次>/cache/pip`），在板上后台起、记 pid，供监测越界时终止该 timeout 进程组；本批未触发终止。

需要 Acceptance 知悉的执行细节（均不改变参数或预算）：

1. 前置里 Python 读数是一次 `/usr/bin/python3.12 -I -S -B -c`，同时打印版本和 `importlib.util.find_spec('venv'/'ensurepip')` 是否存在（只查找、不导入这两个模块），用于“缺种子即停”。
2. 静态启动钩子核对按 site.py 语义扫描 5 个系统路径的 `.pth` 与 sitecustomize/usercustomize。可执行行只按预先写死的闭集放行（setuptools distutils-precedence、setuptools nspkg 命名空间补丁、Ubuntu apport 异常钩子），其余一律前置失败。本次实际只有三项：`distutils-precedence.pth`、`matplotlib-3.6.3-nspkg.pth`（各 1 行可执行，命中闭集）与 `/usr/lib/python3.12/sitecustomize.py`（链到 `/etc/python3.12/sitecustomize.py`，apport 钩子原文）；被引用的 `_distutils_hack/__init__.py`、`apport_python_hook.py` 文本只记录，不作判定依据。原文见 JSON `startup_hooks`。
3. 计划表 `install-plan.tsv`（31 行，sha 与 JSON `plan_tsv_sha256` 一致）随 mkdir 写入板上批次目录。
4. 装后静态读取用 coreutils（cat/ls/head/grep）读 venv 文件，没有额外运行 Python。
5. 每个文件的发令前占用推算 = 当前新增占用 + 2U_i + C_i + 2×成员数×分配单元 + 1 亿 B 日志预留，最大一次（tensorrt-edgellm 之前）为 3,257,261,523 B，低于 5,000,000,000 B。

## 4. 读数摘要

| 项 | 读数 |
|---|---|
| 离线放行 | 账本条目与合同标记逐字存在；允许规则逐字存在、allowedDomains 无板 IP；传板专用 excludedCommands 条目只记录、不沿用；非暂停交接仅本项（Consuming=no）；Mac 上无其他板连接进程 |
| 输入绑定 | transfer.json（W/OK）= download.json（W/OK）= META-DEP 选定 pin，恰 31 件、无重复；板目录取自 transfer `board_dir`；本机原件 sha/字节一致；ZIP 静态合计 C 516,980,330 B / U 1,456,516,225 B / 3,119 成员，与合同 §3 表一致 |
| 前置（1 次 ssh） | 用户 jetson、HOME /home/jetson、aarch64、glibc 2.39、Python 3.12.3、venv/ensurepip 模块在、种子 pip 轮子在；dpkg：python3.12-venv 3.12.3-1ubuntu0.17、python3-pip 24.0+dfsg-1ubuntu1.3、python3-libnvinfer 10.16.2.10-1+cuda13.2 均 ii（python3-numpy 1:1.26.4+ds-6ubuntu1 记录）；系统 TRT 目录在；W31 板上 31/31 普通文件、字节与 sha 一致；venv 与批次目录事先不存在；df 可用 162,773,491,712 B（/dev/nvme0n1p1，/）；分配单元 4096 B；启动钩子全部放行 |
| venv | 创建 1 次 rc=0（5.3 s）；种子只有 pip；种子阶段 venv 占用 16,072,704 B（≤250,000,000）；pyvenv.cfg：home=/usr/bin、include-system-site-packages=true、version=3.12.3 |
| 31 次 pip install | 全部 rc=0，stderr 全空；单件约 1.1–1.8 s，tensorrt-edgellm 9.0 s |
| pip list | rc=0；32 项 = 31 项计划名称/版本全对 + pip 24.0；无计划外条目 |
| 静态读取 | numpy 2.2.6 在 W venv 本地；venv 本地无 tensorrt 目录/dist-info；系统 `/usr/lib/python3.12/dist-packages/tensorrt` 在；venv 本地无 `.pth`；venv 内无 sysvenv 引用 |
| pip check | rc=1，见 §1 两行 |
| 旧环境只读快照 | sysvenv（目录/pyvenv.cfg/site-packages stat 与 cfg sha）、各构建目录：前后一致。传板目录比较字段为 false，唯一差异是 `ls -la` 的 `..` 行（即 `~/eng-jet` 因新建两个目录而改变链接数/mtime），传板目录本身与其中全部文件前后一致；`~/eng-jet` 列表只多出 `edgellm-venv` 和本批次目录 |

## 5. 消耗与上限

| 维度 | 本批 | 上限 |
|---|---|---|
| INSTALL-W 批次 | 1（mkdir 前预约） | 1，重试 0 |
| venv 创建 | 1 | 1 |
| 各 W 文件 attempt | 31 件各 1；OK 31 / FAILED 0 / UNKNOWN 0 / NOT_RUN 0 | 各 ≤1 |
| pip list / pip check | 1 / 1 | 各 1 |
| 整批墙钟 | 67.523 s（起点 = 批次目录创建与 started 较早者，至脚本结束） | 3,600 s |
| 板新增占用观测峰值 / 终值（双根，各取 du -sb 与 du -s -B1 较大者相加） | 1,482,055,680 B / 1,482,055,680 B（venv 1,481,605,120 + 批次目录 450,560） | 5,000,000,000 B |
| df 可用最低 | 161,291,104,256 B | 停止线 1,000,000,000 B |
| 板上原输出/监测/收据最大 | 13,977 B（`raw/` du -sb） | 100,000,000 B；单次调用两流 ≤16 MiB |
| ssh / scp / 重试 | 74 / 0 / 0 | — |
| 联网取包、索引、依赖解析、import W 包、加载模型、运行产物/entrypoint、测试、部署、云 | 0 | 0 |

峰值是 35 个采样（每步前后与 60 s 周期）的最大值，采样之间的瞬时峰值 UNKNOWN；终值采样在最后一笔日志之后、且本次采样不追加日志。git：`git_pre` 与 `git_post` 的 HEAD 相同、porcelain 均为空。

## 6. 主张上限

只到：固定 W31 在本板独立 W venv 里由 pip 离线逐文件装上，pip list 名称/版本与计划一致，静态路径核对通过；pip check 因系统 site 两个既有包不满足而 rc=1。不证明任何包可导入/可运行，不证明系统 TRT 绑定在 W venv 里可加载或二进制兼容，不涉及模型、GGUF、llama-server、性能或时延；AC-7/8/9 仍 NOT_RUN。Overall `REVIEW_PASSED` / Lifecycle `ACTIVE` 不变，不消费 verdict、不签 DONE；S1/S2 STOP、补丁未上板、SR 5/5 耗尽、R1-5/6 OPEN 维持。

## 7. needs_user

- **P1-ENG-JET-001:INSTALL-W:PIP-CHECK**（经 Acceptance 核清后交用户）：怎么看待 pip check 的两条系统包冲突。推荐：先由 Acceptance 核清后，用户把本批记为“W31 安装与 pip list 静态核对完成、pip check 未过（原因是系统 site 的 pynacl→cffi 缺失、scipy 1.11.4 对 numpy<1.28 的要求与 W venv 的 numpy 2.2.6 冲突，二者都不在 W31 静态闭集内）”，本信封内不做修补（不删系统包、不补 cffi、不降 numpy、不重装）；只有在后续独立签发的实测发现 W 路径确实会导入 scipy 或 nacl 时，再另报具名处置。理由：合同明确不自动豁免旧冲突、也不许在本批里补包或改环境；INSTALL-W 已用尽（1/1、重试 0），任何后续动作都需要新签发。
- 延续条目（非本轮新增）：B-LOCAL-EXCLUDE-TRANSFER 排除条目仍推荐用户本人删除（代理不改设置）。
