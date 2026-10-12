# P1-ENG-LOOP-002 诊断页修复交付（DIAG-ENV-2）— 零消耗修复说明与离线桩探针记录

> **仅诊断页修复记录；不进证据链；不作任何门判定；未在真实板条件下验证。** 不是 K 停点候选、不是 C/R 轮，不签独立 PASS 或真实板通过。

- 轮次：`诊断页修复交付`；Dispatch-Id `P1-ENG-LOOP-002-诊断页修复交付-20261007T223935Z-8088`；实现角色（Opus 子代理，supervisor 派发）。
- 依据：同名提案「诊断故障2裁定（2026-10-07，Acceptance）」§1–3、§5（a2aad8e）；补丁唯一来源为 `docs/reviews/P1-ENG-LOOP-002.md`「R1@K1K3」§3 K1K3-R1-1 逐字替换补丁。
- 轨道：D4 `engineering-v1` 保持；按裁定 §3 沿原诊断授权 (d) 的精简通道交付，不新增 K 停点/C/R。
- 消耗：0（SSH、复制、板、Jetson、Unity/Play、5060、模型加载、下载、pip、runtime、全套测试均 0）。本机 MacBook Air 仅用 `/bin/bash` 3.2、`/usr/bin/python3` 3.9 跑零模型桩探针。

## 1. 先后与写入闭集

| 序 | 闭集项（裁定 §3） | 本轮写入 |
|---|---|---|
| ① | `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md` §4 AC-7 行 | 按复核补丁逐字把 `` `tests/test_llama_server_adapter.py::SemverVersionPreflightTests`（4 例） `` 改为 `` …（5 例） ``；`git diff` 只此一处 1+/1−，未改其他字符。不另开复核轮、不宣称已闭合（由 Acceptance 核清）。 |
| ② | `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` §3 env 生成 / 附录 3–4 / 直接对应的 §4 说明 | 见 §2。 |
| ③ | 同名前缀修复说明/离线探针记录 | 本文件。 |
| ④ | 本项交接行 | `docs/current-status.md` Implementation 行与 Log。 |

未写：controller/Assets/tools/tests/config、正式操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md`、mini-ops-prep、JET 来源、`docs/reviews/`、`docs/design-reviews/`、`docs/proposals/`、授权账本。诊断原件（`outputs/eng-loop/…/diagnostics/` 第二次目录）本轮未读、未复制。

## 2. 诊断页改动（最小路径，裁定 §3「选定最小路径」）

1. **§3 env 生成**：Air 已解析的来源值 `$LLAMA_BIN` 不变，写入 `serve-diag.env` 时改用独立名 `DIAG_LLAMA_BIN`；生成前对五项来源值（`BOARD_DIAG WEIGHTS MMPROJ LLAMA_BIN BOARD_TS`）逐项非空检查，空则打印 `DIAG_FAULT missing_input <名>`（记现象后收尾）；§3 末段说明补一句改名原因与 `DIAG_FAULT missing_input` 的处理。
2. **附录 3**：`serve-diag.env` 载入失败改为打印 `DIAG_FAULT serve-diag.env failed to load …` 后 `exit 97`；`BOARD_DIAG` 为空在建 LOG 前 `DIAG_FAULT missing_input BOARD_DIAG` + `exit 97`；继承覆盖清理循环**原样保留**（`LLAMA_|GGML_|MTMD_|HF_|HUGGINGFACE_` 前缀与 `*_proxy/_PROXY`，未给 `LLAMA_BIN` 开白名单、未重新 source）；清理之后、建缓存目录与启动 Python 之前，核五项诊断输入 `BOARD_DIAG WEIGHTS MMPROJ DIAG_LLAMA_BIN BOARD_TS` 非空，缺项 `DIAG_FAULT missing_input <名>`（写 LOG）+ `exit 97`。
3. **附录 4**：模块顶部、导入 `tools` 与任何使用之前，核同五项非空，缺项 `DIAG_FAULT missing_input …` + `DIAG serve_rc=97` + `sys.exit(97)`；`args.llama_bin` 改读 `os.environ["DIAG_LLAMA_BIN"]`。其余逐字未动。
4. **§4 说明**：启动脚本说明补载入/清理范围/五项校验与「停在生产 `llama_preflight` 与子进程创建之前，照样占启动编号」。

保持不变（逐行 diff 只有上列行）：显式缓存设置（`TMPDIR/XDG_CACHE_HOME/LLAMA_CACHE/CUDA_CACHE_*`）、三文件身份/部署摘要（`llama_preflight`）、十旗标（`llama_server_command`）、`budget=None`、就绪/截止（`_wait_llama_ready` 300 s/0.25 s）、起停释放、粗计次口径、prompt/schema/decode、时间/控制安全/指标/采样/阈值。页首依据段（「本页其余步骤未改」指 `身份修复K1K3` 轮）不在闭集②内，本轮未改；本轮改动以本文件与 §3 末段标注为准。

## 3. 零模型离线桩探针（Air；原块消费，不手写替代）

- **命令**：`/bin/bash probe.sh <page.md> <label>`，分别以 `git show HEAD:docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`（修前，HEAD=ee34777，页 sha256 `c2810b6e…`）与修后工作树页（sha256 `0d364a10…`）运行。脚本在会话暂存目录，不入仓。
- **消费方式**：用页内 `diag.env` 的 `extract` awk（仅文件路径参数化）取页 §3 代码块中从 `extract '### 附录 3 '` 行到 RUN_FILES tar 行之前的生成段原样执行（产出 `serve-diag.sh/.py/.env`），再以页 §4 的 `bash --noprofile --norc …/serve-diag.sh 1` 启动。SSH/tar 传板换成本地 `cp` 到桩根 `run/`。
- **桩范围**：只桩 `ss`（打印表头、rc 0）、`pgrep`（rc 1）与桩根 `code/tools/language_serve.py`（`llama_preflight` 写下 `args.llama_bin/weights/mmproj` 与子进程环境中残留的覆盖键后抛 `StartRefused`）、`tools/eng_loop2/llama_adapter.py`（一个常量）。无真实 llama 二进制/GGUF/模型/网络；`/usr/bin/python3 -I -S -B` 为 Air 系统 3.9。
- **注入的继承覆盖**：`LLAMA_BIN=/wrong/inherited/llama-server LLAMA_ARG_THREADS GGML_CUDA_X MTMD_X HF_HOME HUGGINGFACE_HUB_CACHE https_proxy NO_PROXY`。

| 用例 | 修前（原块） | 修后（新块） |
|---|---|---|
| valid（五项齐） | `unset LLAMA_BIN` 后附录 4 第 23 行 `KeyError: 'LLAMA_BIN'`，`serve_rc=1`，未到 preflight —— **重现 DIAG-ENV-2** | 8 个继承覆盖全部 `unset`（含继承的 `LLAMA_BIN`）；到达桩 preflight，`llama_bin` = 来源值 `/opt/llama/bin/llama-server`（非继承值），子进程覆盖键仅剩块内显式设置的 `LLAMA_CACHE`；桩拒启 `serve_rc=3` |
| BOARD_DIAG 空 | `tee /logs/serve-1.log` 失败、`cd /code` 失败、exit 97，无 DIAG_FAULT | Air 侧 `DIAG_FAULT missing_input BOARD_DIAG`；板侧建 LOG 前 `DIAG_FAULT missing_input BOARD_DIAG`，exit 97，未到 preflight |
| WEIGHTS / MMPROJ / LLAMA_BIN / BOARD_TS 各空（4 例） | 均被 `KeyError: 'LLAMA_BIN'` 掩盖，`serve_rc=1`，无缺项判读 | Air 侧各报 `DIAG_FAULT missing_input <名>`；板侧各报 `DIAG_FAULT missing_input WEIGHTS/MMPROJ/DIAG_LLAMA_BIN/BOARD_TS`，exit 97，未到 preflight |
| serve-diag.env 缺失 | bash 报文件不存在、exit 97，无 DIAG_FAULT | `DIAG_FAULT serve-diag.env failed to load …`，exit 97，未到 preflight |
| 板上陈旧 env（旧名 `LLAMA_BIN=`） | `KeyError: 'LLAMA_BIN'`，`serve_rc=1` | `DIAG_FAULT missing_input DIAG_LLAMA_BIN`，exit 97，未到 preflight |
| 附录 4 直接运行、WEIGHTS 空 | 无检查，`weights="."` 进入桩 preflight（`serve_rc=3`） | `DIAG_FAULT missing_input WEIGHTS` + `DIAG serve_rc=97`，exit 97，未导入 tools、未到 preflight |

另：修后附录 3 `bash -n` 通过；附录 4 `ast.parse` 通过；仓库内无测试/工具引用本页（`grep -rl diagnostic-smoke-ops tests tools` 为空），未跑 focused/全套测试（本轮不改代码）。

## 4. 限制

- **未在真实板条件下验证**：真实 Jetson bash/`ss`/`pgrep`、真实 `llama_preflight`（三文件 sha/构建号/部署摘要）、GGUF 加载、就绪/HTTP/闭环均未运行；探针只证明诊断输入传递、覆盖清理与缺项拒启这三点在桩条件下成立。
- 不是独立复核，不签 PASS；交 Acceptance 只读核清闭集、补丁、输入传递和本记录。第三次诊断执行仍须 `DIAG:RESUME:2` 由用户另签并经接受落实（本角色不处理）。
