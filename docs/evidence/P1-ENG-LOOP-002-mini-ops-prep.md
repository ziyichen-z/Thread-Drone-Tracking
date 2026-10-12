# P1-ENG-LOOP-002 — mini操作单准备（停点候选证据；Implementation，Mac mini，零消耗）

- 登记轮次：`mini操作单准备`（Implementation，Opus 子代理，supervisor 派发；Dispatch-Id `P1-ENG-LOOP-002-mini操作单准备-20261007T055142Z-574a`；派发 base_head 为 `Mac mini四题答复落实` 收工提交）。
- 机器：`zc5s-Mac-mini.local`（Mac mini）；只读本机已存来源、依赖清单与真实源码，写文档。
- 合同：同名提案「Mac mini四题答复落实」§1–4（特别是 §3 第一段、「操作单须落实 AC-10 的既有义务」段、§3 步骤 1/4、§4 `B-main:FACT:2`/`ENV:2`），及「B-pre答复落实」「B0a核清」「Mac mini补核核清」完整合同。
- 信封：零消耗（Consuming no）；不 SSH、不复制、不 import 部署包、不跑模型/测试/回放、不碰板/Unity/runtime；B-main 任何维度消耗 0。

## 状态与结论

**本轮产出 PLAY_GOVERNING 候选：只改 `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（操作单），另加本证据文件与状态板；零代码/配置/测试改动。** 操作单落实 AC-10 既有义务（逐项映射见第 4 节），但**仍不可执行**：(1) 待裁定 IR-M1…M8（第 8 节）中 IR-M1（`llama-server` 以缺省旗标启动，既有原读数只覆盖显式旗标执行栈）与 IR-M2（`GET /result` 轮询是否计入 ≤200 非推理 HTTP）直接决定首次服务能否在已签额度内成立，IR-M1 若裁为改代码须另出代码候选回 K1/K3 停点；(2) `SLOT:FACT:1` 窗口互斥待用户确认；(3) Air 缺 JET C2 来源链原件（被忽略的 `outputs/`），须用户对齐（`FACT:2`），否则 STOP；(4) 准备 SSH 读数待用户执行、接受核清放行。

事实缺口判断：Python 下层 C 模块中，llama-server 分支模块级闭包必需而既有板上原读数**未覆盖**的只有 `_posixsubprocess`、`fcntl`（及可选回退的 `_opcode`），可用 `readelf --dyn-syms`/lib-dynload 静态读补齐，**判断不需要 ENV:2**；仅当静态读无法分类（`.dynsym` 无 `PyInit_` 符号且无扩展文件）时才触发第 3 节条件性草案。`llama-server` 缺省旗标行为无法静态读出（`--help` 不在已签用途），只能经 IR-M1 裁定或首次服务核验。

## 1. 事实缺口表

### 1.1 分支分界（真实源码，`git show HEAD:<path>` 同内容）

| 分支 | 入口与触达 | 本项是否触达 |
|---|---|---|
| llama-server（板服务唯一路径） | `tools/language_serve.py::main` 在 `--backend llama-server` 时直接 `return _main_llama(...)`；其惰性导入只有 `controller.language_bridge`（`QUANTIZATIONS`）、`tools.eng_loop2.{deploy_digest,llama_adapter}`；运行期 `controller.language_selector.interpret` → `tools.eng_sft.parse`、`_prompt_identity` → `tools.eng_sft.prompt_v2`，均在 16 路径清单内 | **必需**（模块级闭包 14 文件 + 上述惰性 3 文件，全在清单内；外部仅标准库） |
| local-hf | `main` 的其余分支 → `load_local_adapter` → `language_selector.inference_engine`（惰性 `resource`/`types`/`tools.eng_sft.train_lora` → torch/transformers/peft/PIL） | 不触达（A2(e) 禁止项只在此分支） |
| 跟踪器工厂 | `controller/trackers.py:174/391` 的 `cv2`、`:525` 的 `det_assoc_tracker`→`pose_gmc`/ultralytics/numpy，只在构造跟踪器时 | 不触达（板服务只取类型/纯函数，不调工厂；同名提案「Mac mini补核核清」§2 已裁定读法） |

### 1.2 缺口逐项

| # | 对象（llama 分支必需） | 既有原读数（来源） | 能否覆盖本项真实执行栈 | 缺口 / 补齐方式 |
|---|---|---|---|---|
| F-1 | 解释器 `/usr/bin/python3` → `python3.12`、3.12.3、标准库 .py/包文件 | B0a R02、mini R08 | 版本/路径/文件在盘：是；可 import：否（静态） | 架构/ELF 头、NEEDED 未读 → 准备 SSH P03 |
| F-2 | 标准库 C 级模块（第 1.3 节 A）：必需 `_posixsubprocess` `fcntl` `select` `_socket` `math` `binascii` `_struct` `_random`；可选回退 `_json` `_datetime` `_bisect` `_hashlib` `_sha2` `array` `zlib` `_heapq` `_opcode` `_ssl` | JET C2 诊断板步 `011-worker.block`：同板 `python3 -I -S -B` 导入 `sys os re json hashlib base64 time urllib.request urllib.error` 后跑完 609 行（`outputs/eng-jet/…/stageb-c2-diagnostic/steps/<board 步>/raw/`，mini 本机原件） | 该原读数的闭包覆盖除 `_posixsubprocess`、`fcntl`、`_opcode`（及永远内建的 `_ast` `_imp` `marshal` `_signal` `_tokenize` `_typing` `_frozen_importlib*`）外的全部 C 级模块（第 1.3 节 B 差集）；它是 JET 诊断，不作本项证据，只作「目标条件已有原读数」来源 | `_posixsubprocess`/`fcntl`/`_opcode` 内建或扩展、扩展架构与依赖未读 → 准备 SSH P04；必需项静态不可分类 → 第 3 节 ENV:2 草案 |
| F-3 | site 钩子：`dist-packages`/用户 site 的 `.pth`、`sitecustomize` | 无 | 否 | 板端调用改 `-I -S -B`（IR-M5）后不加载；仍读出存档 → P05 |
| F-4 | Python 包版本（`python3.12`、`libpython3.12-*`） | 无 | 否 | 可选 `dpkg-query` 静态读 → P06（工具缺失照记 UNKNOWN，不阻断） |
| F-5 | `llama-server` 三文件身份、ELF、20 实体 ldd 闭包 | mini R02–R07（三文件 sha 符合来源期望；闭包无 not found） | 文件身份：是（时点快照）；运行时 dlopen（libcuda）：否 | 三文件身份在 SSH#2 由 AC-16 正式重核；P02 只做 stat 变化检测；L4T/驱动库记录 → P06 |
| F-6 | `llama-server` 执行栈（同二进制 + 同 GGUF + 同 mmproj + CUDA 13.2） | JET C2 诊断板步 `008-server.block/.stderr`、`010-monitor.stdout`：显式 `--parallel 1 --ctx-size 2048 --n-gpu-layers 99 --fit off --no-warmup --no-webui --no-cache-prompt --cache-ram 0 --cache-reuse 0 --offline`，2.48 s 就绪，RSS 约 3.0–3.16 GB，MemAvailable 约 3.7 GB | **否**：`language_serve.llama_server_command` 只传 `-m --mmproj --host --port`，用二进制缺省值；源码归档缺省（第 1.3 节 D，构建链未认证、仅指示）为 `n_ctx=0`（=训练上下文）、`n_parallel=-1`（server 自动）、`n_gpu_layers=-1`（自动）、`fit_params=true`、`warmup=true`、`cache_ram_mib=8192`；C2 GGUF 头 `context_length=262144`、28 层、8 KV 头、128 维（第 1.3 节 C）→ f16 KV 全上下文约 30,064,771,072 B，远超板总内存 7,849,054,208 B，实际取决于自动 fit | 静态不可补（`--help` 不在已签用途）→ **IR-M1**；不预判可达/通过，不新增内存/性能 STOP |
| F-7 | `response_format`（json schema）被 b11381 接受 | JET C2 JSON 诊断：attempt-1 `STOPPED INPUT_CHANGED`，板请求 0 | 否 | 只能首次收据核验（`S-RECEIPT`），同名提案已定 |
| F-8 | 非推理 HTTP 计量 | 源码：`HttpAdapter.poll_interval_s=0.2`，每次推理 = `POST /query` + 至 done 的 `GET /result/<id>` 轮询；JET 每请求约 1.7–2.0 s → 约 8–10 次轮询/推理；`_wait_llama_ready` 每 0.25 s 一次 loopback `/health`，无访问日志 | 否 | **IR-M2**（口径）、**IR-M7**（loopback 上界与就绪等待值） |
| F-9 | 板工具：`tar` `mkdir` `du` `awk` `sort`（B0b/收尾所需） | B0a/mini R01 只核了读命令 | 部分 | P01 存在性 |
| F-10 | 计划根、端口、残留进程、磁盘/内存 | mini R09–R12（时点） | 时点快照 | P07–P08 现场重读（启动前在 SSH#2 再核一次） |
| F-11 | Air：JET C2 来源链原件、`.venv-yoloe`、`ssh -G Jetson`、Unity 工作树干净 | 无（Air 不可从 mini 读） | 否 | 第 2.1 节 Air 本机前置；原件缺失即 STOP（用户 `FACT:2` 对齐） |
| F-12 | 链路 | B0a ping（N-2 账）、mini S1 4.489 s | 时点 | 不另测（ping 0）；连接失败计次 |

### 1.3 本机静态读取原流（mini；系统/uv 解释器只做 AST/字节读取，不 import 被分析模块、不加载模型）

**A. llama 分支模块级闭包的标准库 C 级模块**（代理标准库 = mini 本机 uv CPython 3.12.14 源码树，版本与板 3.12.3 不同；脚本见附录 C1；`cmods.py` sha256 `3a0469553d5d34a00395abdffcc994a598ec2b1a15b12226bebd66d5543f4d3d`，输出 sha256 `f973f7fdb8ff9ae647cba493f9784cb1743206b3c7defd7525d50f4253564e76`；根 = mini deps.py A 段 27 个顶层 + 5 子模块）：

```
py_modules_reached 107 unconditional 90
REQ: _ast _imp _io _operator _random _signal _socket _sre _string _struct _thread _tokenize _typing _warnings _weakref binascii builtins errno itertools marshal math os.path select sys time
OPT(try/except/if): _abc _bisect _bz2 _codecs _collections _datetime _frozen_importlib _frozen_importlib_external _functools _hashlib _json _locale _lzma _opcode _posixsubprocess _scproxy _sha2 _ssl _stat _winapi _wmi array fcntl msvcrt nt posix winreg zlib
```

注：`_posixsubprocess`/`fcntl`/`posix` 在 `if _mswindows: … else:` 分支，Linux 上必需；`_winapi`/`_wmi`/`msvcrt`/`nt`/`winreg`/`_scproxy` 为其他平台。

**B. 与 JET 板上 worker 原读数闭包的差集**（同脚本，根 = `sys,os,re,json,hashlib,base64,time,urllib.request,urllib.error`；输出 sha256 `3d5ed8c1d2ea1d4afc11f8a557af24491fba644eb65952e7cb759c275e6592b7`）：LOOP 闭包多出 `_ast _frozen_importlib _frozen_importlib_external _imp _opcode _posixsubprocess _signal _tokenize _typing _wmi fcntl marshal msvcrt winreg`。去掉恒内建（核心/引导）与其他平台项，剩 **`_posixsubprocess`、`fcntl`、`_opcode`**。

**C. C2 Q4 GGUF 头元数据**（`gguf_kv.py` 只读头部 5,934,285 B，不读张量；附录 C2；输出 sha256 `4f412d347cb6b74cbc54852bd6e50eb1cbe9d03596b81f466434f8aba77dee87`）：

```
magic b'GGUF' version 3 n_tensors 310 n_kv 33
KV general.architecture = qwen3vl
KV qwen3vl.block_count = 28
KV qwen3vl.context_length = 262144
KV qwen3vl.embedding_length = 2048
KV qwen3vl.attention.head_count = 16
KV qwen3vl.attention.head_count_kv = 8
KV qwen3vl.attention.key_length = 128
KV qwen3vl.attention.value_length = 128
KV general.file_type = 15
header_bytes_read 5934285 file_bytes 1107409952
```

f16 KV 每 token = 28 × 8 × (128 + 128) × 2 B = 114,688 B；× 262,144 = 30,064,771,072 B；× 2,048（JET 显式值）= 234,881,024 B。

**D. llama.cpp 源码归档缺省值**（JET 源码归档 `stageb-source-archive-*/archive.tar.gz`，`tar -xzOf` 到标准输出只读、不解包落盘；该归档与板上二进制的构建关系未认证，只作指示；输出 sha256 `54817faf45e166b11378864137d959164af8d4d18a46b224b55d0129de4e3fdc`）：

```
caf971165313952eb4222c4b4a0ee77e5bec79f496d73d6d5a0be8b7d3c87669  outputs/eng-jet/P1-ENG-JET-001/stageb-source-archive-20261004T152331Z/archive.tar.gz
== common/common.h
455:    int32_t n_ctx                 =     0; // context size, 0 == context the model was trained with
460:    int32_t n_parallel            =     1; // number of parallel sequences to decode
478:    int32_t n_gpu_layers       = -1;    // number of layers to store in VRAM, -1 is auto, <= -2 is all
481:    bool    fit_params         = true;  // whether to fit unset model/context parameters to free device memory
578:    bool kv_unified        = false; // enable unified KV cache
584:    bool warmup            = true;  // warmup run
632:    bool    cache_prompt        = true;  // whether to enable prompt caching
637:    int32_t cache_ram_mib       = 8192;  // -1 = no limit, 0 - disable, 1 = 1 MiB, etc.
== common/arg.cpp (server example overrides)
    } else if (ex == LLAMA_EXAMPLE_SERVER) {
        params.n_parallel = -1;     // auto by default
```

**E. 既有板上原读数的定位（mini 本机原件，只读）**：JET C2 诊断板步 `raw/008-server.block`（显式旗标）、`raw/008-server.stderr` 首段（`model loaded` 2.48 s、`n_slots = 1, n_ctx_slot = 2048`）、`raw/010-monitor.stdout`（`rss_kB` 3,044,352→3,164,072，`memavail_kB` 约 3.73–3.82 M）、`raw/011-worker.block`（`exec python3 -I -S -B -c 'import sys, os, re, json, hashlib, base64, time, urllib.request, urllib.error …'`）、`receipt.json`（`rows_done_ok` 609、`health.http` 200）。全部是 JET 诊断，不进本项证据、不追认通过。

## 2. 准备 SSH 逐字命令与计量清单（用户在 Air 经既有 `Host Jetson` 执行；计次单元 #1；G1–G3 后才可执行）

> **已被替代（2026-10-07 `R3答复后新候选`）**：本节第 2.1–2.4 节的 Air 前置、读脚本与直接 `Popen ssh` 发起块不再是执行文本；现行准备单元按操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md` 第 0.5 节主连接/通道协议、第 2 节与附录 P 执行（AC-10 修订 1(a)、O-2/PR-10/PR-12）。原文保留为本轮候选的历史记录。

> **OPS操作增量实现（2026-10-08）**：本节准备 SSH 的现行执行入口是正式操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md` 第 0A 节的 `play_ops prep`（读脚本以该单附录 P 为准）；本节保留为历史来源。来源核对入口为 `play_ops source`（只核 Air 现有原件，缺件即停，不跨机复制）。**OPS裁定落实与停点验证（2026-10-08）**：IR-OPS-5 诊断模式（`play_ops --mode diagnostic diag`，SUB:3）**不使用**本证据的附录 A/B：其三文件期望只按诊断页附录 1 从本项 precheck 的 Mac mini R02 原流运行时解析，资产 JSON 只是诊断输入、写在诊断根，不写正式 assets；本证据的附录 A/B 仍只供正式 `source`/`prep`/`receipt`/`play` 原样取用，字节来源与静态闭集不变。

### 2.1 Air 本机零消耗前置（不连接；任一失败即停，不开 SSH）

```bash
cd <Air 仓库根>; OUT=outputs/eng-loop2/P1-ENG-LOOP-002; PY=.venv-yoloe/bin/python; mkdir -p "$OUT/prep"
date -u +%FT%TZ; hostname; sw_vers 2>/dev/null; "$PY" --version
ssh -G Jetson | grep -E '^(hostname|user|port|batchmode|connecttimeout) '      # 不读私钥、不连接
command -v ssh tar shasum curl du                                             # 缺任一即停
git status --porcelain --untracked-files=normal; git rev-parse HEAD            # 第 1 节放行另做；此处只记录
ls Assets/_Recovery 2>/dev/null; test ! -e runtime/scenario_config.json && echo NO_RESIDUAL_OVERLAY
cat ProjectSettings/ProjectVersion.txt
# 附录 A 存为 "$OUT/prep/resolve-src.py"，附录 B 存为 "$OUT/prep/assets-gen.py"，第 2.2 节存为 "$OUT/prep/prep-read.body.sh"
"$PY" -I -B "$OUT/prep/resolve-src.py" > "$OUT/prep/source.env"; tail -n 1 "$OUT/prep/source.env"   # 须为 RESOLVE_OK，否则 STOP
EXP_HOST=$(sed -n '/^## Mac mini只读补核原始读数与逐维度用量/,$p' docs/evidence/P1-ENG-LOOP-002-precheck.md | grep -m1 '^hostname=' | cut -d= -f2)
{ printf 'EXP_HOST=%q\n' "$EXP_HOST"; grep -E '^(WEIGHTS|MMPROJ|LLAMA_BIN|EXP_[A-Z_]*_BYTES)=' "$OUT/prep/source.env"; cat "$OUT/prep/prep-read.body.sh"; } > "$OUT/prep/prep-read.sh"
bash -n "$OUT/prep/prep-read.sh" && shasum -a 256 "$OUT/prep/prep-read.sh"
```

### 2.2 板端读脚本正文（逐字；经 stdin 送入，不落板文件；fail-fast，命中 STOP 即退出 3）

本机 `bash -n` 语法检查通过（rc 0）；正文 sha256 `949c63d7feec1d61cb057ba642aa08f245f0fb7ca587f040b98839092079388c`。

```bash
set -u
STOP() { printf '\nSTOP %s\n' "$1"; date -u +%FT%TZ; printf 'remote_elapsed_s=%s\n' "$SECONDS"; exit 3; }
sec() { printf '\n=== %s\n' "$1"; }
rc() { printf 'rc=%s\n' "$1"; }
sec "P00 device"; date -u +%FT%TZ; H=$(hostname); printf 'hostname=%s\n' "$H"; uname -srm; id -un
[ "$H" = "$EXP_HOST" ] || STOP "HOST_MISMATCH"
[ "$(uname -m)" = aarch64 ] || STOP "ARCH_MISMATCH"
sec "P01 tools (required; presence only)"
for t in date hostname uname id stat readlink ls readelf ldd df free ss pgrep timeout grep cat tar mkdir du awk sort; do
  p=$(command -v "$t") || STOP "TOOL_MISSING $t"; printf '%s|%s\n' "$t" "$p"
done
for t in dpkg-query ldconfig; do printf '%s|%s\n' "$t" "$(command -v "$t" || echo ABSENT_optional)"; done
sec "P02 three files (stat only; sha is AC-16 in SSH#2)"
for f in "$WEIGHTS" "$MMPROJ" "$LLAMA_BIN"; do
  [ -L "$f" ] && STOP "ASSET_IS_LINK $f"
  s=$(stat -c '%F|%s' -- "$f" 2>&1) || STOP "ASSET_STAT_FAIL $f"; printf '%s|%s\n' "$f" "$s"
done
[ "$(stat -c %s -- "$WEIGHTS")" = "$EXP_WEIGHTS_BYTES" ] || STOP "WEIGHTS_BYTES_CHANGED"
[ "$(stat -c %s -- "$MMPROJ")" = "$EXP_MMPROJ_BYTES" ] || STOP "MMPROJ_BYTES_CHANGED"
[ "$(stat -c %s -- "$LLAMA_BIN")" = "$EXP_LLAMA_BIN_BYTES" ] || STOP "LLAMA_BIN_BYTES_CHANGED"
sec "P03 interpreter ELF"
PYR=$(readlink -f -- /usr/bin/python3); printf 'python3_realpath=%s\n' "$PYR"
[ "$PYR" = /usr/bin/python3.12 ] || STOP "PY_REALPATH_CHANGED"
/usr/bin/python3 --version 2>&1; rc $?
readelf -h -- "$PYR" | grep -E 'Class:|Type:|Machine:'; rc $?
readelf -d -- "$PYR" | grep -E 'NEEDED|RUNPATH|RPATH'; rc $?
sec "P04 C-level stdlib modules: builtin (PyInit_ in .dynsym) or lib-dynload ext"
DYN=/usr/lib/python3.12/lib-dynload
SYMS=$(readelf -W --dyn-syms -- "$PYR" 2>/dev/null | awk '{print $NF}' | grep -E '^PyInit_' | sort -u)
NSYM=$(printf '%s\n' "$SYMS" | grep -c '^PyInit_'); printf 'pyinit_dynsym_count=%s\n' "$NSYM"
REQ_MISS=; OPT_MISS=
for m in _posixsubprocess fcntl select _socket math binascii _struct _random _json _datetime _bisect _hashlib _sha2 array zlib _heapq _opcode _ssl; do
  case "$m" in _posixsubprocess|fcntl|select|_socket|math|binascii|_struct|_random) cls=REQ;; *) cls=OPT;; esac
  if printf '%s\n' "$SYMS" | grep -qx "PyInit_$m"; then printf '%s|%s|builtin_dynsym\n' "$cls" "$m"; continue; fi
  set -- "$DYN/$m".cpython-312-*.so
  if [ -e "$1" ]; then
    printf '%s|%s|ext|%s\n' "$cls" "$m" "$1"
    readelf -h -- "$1" | grep 'Machine:'
    readelf -d -- "$1" | grep 'NEEDED'
    L=$(ldd -- "$1" 2>&1); printf '%s\n' "$L"
    printf '%s\n' "$L" | grep -q 'not found' && STOP "EXT_DEP_NOT_FOUND $m"
  else
    printf '%s|%s|NOT_FOUND\n' "$cls" "$m"
    if [ "$cls" = REQ ]; then REQ_MISS="$REQ_MISS $m"; else OPT_MISS="$OPT_MISS $m"; fi
  fi
done
printf 'opt_not_found=%s\n' "${OPT_MISS:-none}"
[ -z "$REQ_MISS" ] || STOP "REQ_CMOD_UNRESOLVED:$REQ_MISS(pyinit_dynsym_count=$NSYM)"
sec "P05 site hooks (recorded; board runs -I -S -B per IR-M5)"
for d in /usr/lib/python3/dist-packages /usr/local/lib/python3.12/dist-packages "$HOME/.local/lib/python3.12/site-packages"; do
  printf '[%s]\n' "$d"; ls -la -- "$d"/*.pth 2>&1
done
ls -la -- /usr/lib/python3.12/sitecustomize.py /etc/python3.12/sitecustomize.py 2>&1
sec "P06 package versions / L4T / CUDA driver (static records)"
if command -v dpkg-query >/dev/null; then dpkg-query -W -f='${Package}|${Version}|${Architecture}\n' python3.12 python3.12-minimal libpython3.12-minimal libpython3.12-stdlib 2>&1; rc $?; fi
cat /etc/nv_tegra_release 2>&1; rc $?
if command -v ldconfig >/dev/null; then ldconfig -p 2>/dev/null | grep -E 'libcuda\.so'; rc $?; fi
sec "P07 planned root (must be absent; read-only)"
for d in /home/jetson/eng-loop2 /home/jetson/eng-loop2/code /home/jetson/eng-loop2/logs; do
  if [ -e "$d" ] || [ -L "$d" ]; then stat -c '%n|%F|%a|%U:%G' -- "$d"; STOP "PLANNED_ROOT_EXISTS $d"; else printf '%s|ABSENT\n' "$d"; fi
done
df -B1 / /home/jetson 2>&1; rc $?; free -b 2>&1; rc $?
sec "P08 ports / residual processes"
SS=$(ss -ltn 2>&1); r=$?; printf '%s\nrc=%s\n' "$SS" "$r"; [ $r -eq 0 ] || STOP "SS_FAIL"
printf '%s\n' "$SS" | awk '{print $4}' | grep -qE ':(18081|18082)$' && STOP "PORT_OCCUPIED"
pgrep -a -f llama-server 2>&1 && STOP "RESIDUAL_LLAMA"
pgrep -a -f language_serve 2>&1 && STOP "RESIDUAL_LANGUAGE_SERVE"
sec "P99 end"; date -u +%FT%TZ; printf 'remote_elapsed_s=%s\nfinal=NO_STOP\n' "$SECONDS"
exit 0
```

命令闭集说明：沿用原只读补核已核清的 `date hostname uname id command test stat readlink ls readelf ldd python3 --version df free ss pgrep timeout` 与有限 shell；**新增**只读工具 `grep awk sort cat`（文本过滤）、`dpkg-query -W`（读包数据库）、`ldconfig -p`（读链接器缓存），以及对 `/etc/nv_tegra_release` 的 `cat`；`tar mkdir du` 只核存在性、不执行。新增项需接受在核对轮确认属「非特权静态读」；若不确认，删去 P05/P06 不影响 STOP 闭集。`ldd` 只用于已定位的标准库扩展文件（与原 server 依赖读取同类）。46273 不再读归属（用户已答）。

### 2.3 Air 发起与限时（逐字；本机无 GNU `timeout`，用标准库子进程组守护）

```bash
"$PY" -I -B - "$OUT/prep" <<'EOF'
import os, signal, subprocess, sys, time
d = sys.argv[1]; t0 = time.time(); m0 = time.monotonic()
with open(os.path.join(d, "prep-read.sh"), "rb") as fin, open(os.path.join(d, "prep.stdout"), "wb") as fo, open(os.path.join(d, "prep.stderr"), "wb") as fe:
    p = subprocess.Popen(["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", "Jetson", "timeout -k 5 900 bash -s"],
                         stdin=fin, stdout=fo, stderr=fe, start_new_session=True)
    try:
        rc = p.wait(timeout=1200)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL); p.wait(); rc = "LOCAL_LIMIT_KILLED"
t1 = time.time()
print("epoch_start %.6f epoch_end %.6f wall_s %.3f mono_s %.3f ssh_rc %s" % (t0, t1, t1 - t0, time.monotonic() - m0, rc))
EOF
wc -c "$OUT/prep/prep.stdout" "$OUT/prep/prep.stderr"; shasum -a 256 "$OUT/prep/prep.stdout" "$OUT/prep/prep.stderr"
grep -E '^(STOP |final=)' "$OUT/prep/prep.stdout"
```

本单元上限 3,600 s；脚本远端 900 s、本机 1,200 s 硬限，余量用于收尾。一次连接尝试（成功或失败）即用掉准备 1/1，**不重试**。

### 2.4 停止闭集（命中即停，保存已得原流，交接受；不追加连接、不清进程、不建根）

Air 前置任一失败；`HOST_MISMATCH`、`ARCH_MISMATCH`、`TOOL_MISSING`、`ASSET_IS_LINK`、`ASSET_STAT_FAIL`、`*_BYTES_CHANGED`、`PY_REALPATH_CHANGED`、`EXT_DEP_NOT_FOUND`、`REQ_CMOD_UNRESOLVED`、`PLANNED_ROOT_EXISTS`、`SS_FAIL`、`PORT_OCCUPIED`、`RESIDUAL_LLAMA`、`RESIDUAL_LANGUAGE_SERVE`；SSH 连接/认证失败；本机限时触发；脚本末行不是 `final=NO_STOP`；任何合同疑义。`REQ_CMOD_UNRESOLVED` 且 `pyinit_dynsym_count=0` 表示静态无法分类 → 只能转第 3 节 ENV:2（另签）。

### 2.5 计量清单（写入 `-ledger.json` 准备单元行与本项证据）

| 维度 | 计量 | 预期 |
|---|---|---|
| SSH 次数 / 墙钟 | 第 2.3 节打印的本机 epoch 始末、wall/mono、`ssh_rc` | 1/3；≤3,600 s（实际预计 < 30 s） |
| 远端耗时 | `remote_elapsed_s` | 仅辅助，不替代本机墙钟 |
| 板写入 / 文件传输 | stdin 脚本与 stdout/stderr 为 SSH 记录 | 0 / 0 批 |
| `--version` / GGUF 加载 / 推理 / HTTP / ping | — | 各 0 |
| 原流 | stdout/stderr 字节与 sha256（运行时算，写原流节） | 全量保留 |
| 附带披露 | 登录日志/访问时间等系统行为 | 不计部署写入 |

## 3. `B-main:ENV:2` 无模型预检子合同草案（条件性；**未执行、未授权、不预定数值生效**）

**触发条件**：仅当第 2 节读数命中 `REQ_CMOD_UNRESOLVED` 且 `pyinit_dynsym_count=0`（静态无法区分内建与缺失），或接受核清认定 F-1/F-2 仍有必需事实 UNKNOWN。未触发则不提请。

| 项 | 草案 |
|---|---|
| 机器 / 执行人 | MacBook Air → 同一 Jetson 既有 `Host Jetson`；用户本人发起 |
| 次数 / 墙钟 | 独立 SSH 1 次（不占 B-main 3 次），≤600 s，重试 0；失败计次 |
| 逐字命令 | `/usr/bin/python3 -I -S -B -c 'import sys; print(sorted(sys.builtin_module_names))'`；`/usr/bin/python3 -I -S -B -c 'import _posixsubprocess, fcntl, select, _socket, math, binascii, _struct, _random; print("REQ_IMPORT_OK")'`；`/usr/bin/python3 -I -S -B -c 'import subprocess, http.server, socketserver, dataclasses, argparse, platform, tempfile, shutil, signal, threading, typing, pathlib, json, hashlib, base64, urllib.request, http.client; print("STDLIB_CLOSURE_IMPORT_OK")'` |
| 不做 | 部署包 import、写板、文件传输、模型/llama-server 执行（含 `--version`/`--help`）、HTTP、ping、sudo、设置修改 |
| 写入 / 传输 | 板写入 0（`-B` 不落字节码）；传输 0 |
| STOP 闭集 | 连接/认证失败、任一命令非 0、输出缺 `*_OK`、限时触发、合同疑义 → 停，交接受/用户；不为补齐继续 |
| 产出 | `-precheck.md` 新具名节原流（命令、rc、起止 epoch、stdout/stderr） |
| 结论上限 | 只证明标准库在 `-I -S -B` 下可导入，不证明部署包、服务、HTTP 或性能 |

## 4. 操作单修订：合同映射（义务 → 操作单节）

| 义务（出处） | 落点 |
|---|---|
| 已签/暂锁维度分列（四题落实 §2、§3 AC-10 段） | 第 0.4 节表（已签上限 / 当前可执行 0 / 解锁门） |
| 单主臂、本人启动、(h)(j)(k)（B-pre §1–2） | 第 0.1 节；第 4、13 节 |
| 独立 `/home/jetson/eng-loop2/code` 与 `logs`、不覆盖同名既存根、不与 JET 根混写（B0a核清 §2 BOARD_ROOT；四题 §3） | 第 0.1、3.3 节；读脚本 P07 |
| 仅 `127.0.0.1:18081` 与 Tailscale `:18082`（B0a核清 §2 46273 行） | 第 0.1、4 节；P08 |
| 三文件与库披露（四题 §1 LIB） | 第 3.4 节 `library_disclosure`；第 11 节模板行；附录 B |
| 准备 1 + 服务 2 的 SSH/墙钟/传输/驻留计账（四题 §2–3） | 第 0.5、14 节；第 11 节模板 |
| 故障重启 0、收据重测 0（四题 §1 N-3、§2） | 第 0.4、4、5 节 |
| 十一 STOP 现行处置（授权边界修订 2） | 第 13 节（替换旧缺省列） |
| 首次服务/HTTP 失败停全部（四题 §1 末段） | 第 4、10、13 节 |
| 删除 `/status` 不可达环境重试分支（B0a核清回填 session 行） | 第 10 节 |
| runtime 残留仅移动、逐 session 布局归档（H-8；§3.6） | 第 3.1、12 节（`mv -n`，无删除） |
| 异常 HTTP 字节计量、采样峰值限制（§5.2；S-ARCHIVE） | 第 11 节 HTTP 行与磁盘行 |
| HEAD/status 采集门按严格合同（四题 §3 步骤 4） | 第 1 节（HEAD = `passed_candidate`、全树干净；取值来源改 `origin/main` 属 IR-M4 待裁定） |
| §3.6 节闭集与 B/C 派生、只凭预览规则（AC-10） | 第 7–9 节原文保留（只把 `docs/evidence` 写入改到批后） |
| 事实缺口与用户命令（四题 §3 步骤 2、§4 FACT:2/ENV:2） | 操作单第 0.3、2 节指向本文件第 1–3 节 |

改动性质：第 7–9 节命令、第 12 节评分额度、§3.5 输入与 AC 均未改；会话/剧本参数未改；未新增 AC、采样或额度。

## 5. 完整候选 diff 解析式（运行时解析，不手抄 SHA）

```bash
REVIEW=docs/reviews/P1-ENG-LOOP-002.md
PASS=$(grep -E '^passed_candidate: [0-9a-f]{40}$' "$REVIEW" | tail -n 1 | awk '{print $2}')        # 最近通过候选（R2）
CAND=$(git log origin/main --format=%H -n 1 --grep='^P1-ENG-LOOP-002 mini操作单准备' -- docs/evidence/P1-ENG-LOOP-002-play-ops.md)
git diff --name-only "$PASS".."$CAND"                                   # 完整候选 diff（含期间各角色文档提交）
git diff --name-only "$PASS".."$CAND" -- ':!docs/'                      # 须为空：无代码/配置/测试
git diff "$PASS".."$CAND" -- docs/evidence/P1-ENG-LOOP-002-play-ops.md  # PLAY_GOVERNING 唯一改动文件（开轮资格非空）
git diff "$CAND"^.."$CAND" --stat                                       # 本轮唯一提交：play-ops、本文件、状态板
```

开工时（本轮提交前）`git diff --name-only $PASS..HEAD` 只有 9 个 `docs/` 路径（授权账本、状态板、precheck、派发日志、implementation-status、parked-status、正式设计、提案、复核文件），无 PLAY_GOVERNING 变化。下一实际轮号由实际记录解析：`grep -ohE '\b[CR][0-9]+@K1K2K3K4' docs/reviews/P1-ENG-LOOP-002.md docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md | sort -u` 现有 C1/C2、R1/R2 → 下一实际为 `C3@K1K2K3K4`、`R3@K1K2K3K4`（不照抄 AC-18 历史 C2/R2 字样）。

## 6. 稳定候选四条件自证（workflow §4.3.1）

1. **范围与接口冻结**：本候选只改操作单（PLAY_GOVERNING）与文档；代码、配置、测试、接口、AC、采样、算法 diff 为空（第 5 节第 2 条命令）。操作单本身按本版冻结交核对；**限制**：IR-M1/M2/M3/M4/M7/M8 的裁定可能要求操作单返工或新代码候选（IR-M1），届时形成新候选回同一停点，本版不预设裁定结果。
2. **相称测试/编译**：见第 7 节——无代码改动、无测试读取该文件，故无适用测试；未跑全套、不记全套通过。本轮对操作单内嵌脚本只做本机 `bash -n`（读脚本）与 `ast.parse`（附录 A/B/C 四段 Python）语法检查，及附录 A 对 mini 本机原件只读执行一次（`RESOLVE_OK`，值未写入文档）。
3. **已知 Unity 失败**：本轮未运行 Unity；无已知 Unity 失败。Unity 编辑器打开后可能改动已跟踪文件 → 第 1.2 节现场判据与第 9 节风险。
4. **复核范围/状态板/候选/未验证风险已更新**：候选为本轮唯一收工提交（第 5 节解析式）；状态板交接行与 Log 已更新；复核范围第 10 节；风险第 9 节。

## 7. 相称验证适用性（engineering §6 / workflow §4.3.1）

- 改动文件闭集：`docs/evidence/P1-ENG-LOOP-002-play-ops.md`（M）、`docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md`（N）、`docs/current-status.md`（M）。
- `grep -rl 'P1-ENG-LOOP-002-play-ops' tests tools controller` 无命中（唯一读 play-ops 的测试 `tests/test_frame_follow_replay.py` 读的是 FRAME-001 的操作单）；`tests/test_loop2_freeze.py` 只核代码/配置冻结集。故无 focused 套件覆盖本改动，engineering §6 的「窄修 focused + 红绿」亦不适用（无 finding、无代码）。
- 既有代码证据随候选携带：R2@K1K2K3K4 副本内 focused 454 OK（4 skip）与 R1-1 红绿、C1 返工停点全套（`-tests-rework1.log`），代码相对通过候选零 diff；本轮未重跑（零消耗信封）；N-1 全套累计 2/3、本轮未跑，余 1 不是本派发的测试许可，不重置或挪用（2026-10-07 `R3答复后新候选` 依 R3 派发 O-6 / C3 PR-13 更正原「已用尽」误记）。
- 操作单命令的真实执行验证全部留在 B-main 放行后的首次合同核验；本轮不声称任何命令已在 Air/板上跑通。

## 8. 待裁定（实现角色对提案只读，写在此处交接受；未裁定前操作单相应节不可执行）

| 编号 | 问题 | 事实依据 | 实现推荐（非裁定） |
|---|---|---|---|
| **IR-M1** | `llama_server_command` 只传 `-m --mmproj --host --port`，用 b11381 缺省（自动上下文 = 训练值 262,144、自动并行/层数、`fit_params` 开、`warmup` 开、`cache_ram_mib` 8192）；唯一既有板上原读数是显式 `--parallel 1 --ctx-size 2048 --n-gpu-layers 99 --fit off --cache-ram 0 …`。缺省执行栈的内存/就绪时间/并行槽无任何原读数，首次启动失败即停全部、故障重启 0 | 第 1.2 节 F-6；第 1.3 节 C/D | 推荐改代码：显式固定与唯一原读数相同的旗标（至少 `--ctx-size 2048 --parallel 1 --n-gpu-layers 99 --fit off --cache-ram 0`，`--no-webui`/`--no-warmup`/`--offline` 由接受定），形成新代码候选回 K1/K3（AC-7 测试同步），经核对与独立复核；理由：不把首次 GGUF 加载当未知环境探针（四题 §2 明文禁止）。备选：保持代码、首启即核验并接受失败停全部的风险。实现未改代码 |
| **IR-M2** | 每次推理 = `POST /query` + 每 0.2 s 一次 `GET /result/<id>` 至 done（约 8–10 次）；335 推理约 2,700–3,400 次轮询。若轮询计入「非推理 HTTP ≤200」则任何读法下都超限 | 第 1.2 节 F-8；`controller/language_selector.py::HttpAdapter` | 推荐裁定：一次「推理请求」= 被受理的 `POST /query` 及其 `GET /result` 轮询与板内 loopback chat 请求；「非推理 HTTP」= `GET /status`、`GET /health`（Air→板）与 loopback 就绪 `/health`；访问日志逐行字节全部计入 60 MB 有效载荷。轮询响应使有效载荷增加（估计数 MB 级，未实测），仍在 60 MB 内的余量未核 |
| **IR-M3** | SSH 计次：部署 tar、交互前台服务、日志回传需各自通道；按「每次 `ssh` 调用 = 1 次」则 ≤3 次不可行 | 第 0.5 节；§5.2「≤3批」与「≤3次」 | 推荐：每计次单元一条 `ControlMaster` 主连接，单元内复用会话不另计；墙钟 = 主连接起止。`-o` 选项不写配置。备选：接受另定口径或回用户改额度（CHANGE:1） |
| **IR-M4** | 原 §1.1 读工作树复核文件且要求 HEAD = `passed_candidate`：通过候选提交不可能含写它的复核提交，结构上永不满足；且采集期需写 Unity 日志/证据 | 第 1 节 | 推荐：取值改读 `git fetch` 后 `origin/main` 的复核文件与账本，Air 分离检出到 `PASSED`，HEAD 等值与全树干净不放宽；分离期间不写已跟踪路径，Unity 日志条目在 `main` 上写后回到分离再核。若接受认为属 AC-6/AC-10 解释修订，按 engineering §2 追加 |
| **IR-M5** | 板端解释器调用由 `$BOARD_PY tools/language_serve.py` 改为 `/usr/bin/python3 -I -S -B …` | F-2/F-3；JET worker 同模式原读数 | 推荐采纳：与唯一既有板上 Python 原读数同模式、隔离 site/.pth/sitecustomize 第三方导入（A2(e) 闭集）、不落 `__pycache__`；`language_serve` 自行把源码根插入 `sys.path`，`-I`/`-S` 不影响清单内导入（未运行验证） |
| **IR-M6** | 原 §3.3 要求 B0b 在板端跑 `deploy_digest` 求摘要（Python 动态执行）；本版改为板端逐文件 `sha256sum` 与 Air `shasum` 逐行比对，板端摘要由服务 `/status` 自算并在收据比较（退出码 6） | 第 3.5 节 | 推荐采纳：B0b 不新增板上 Python 执行，比较链（A2(a)/§3.2）不变 |
| **IR-M7** | `_wait_llama_ready` 每 0.25 s 一次 loopback `/health`，无日志；就绪等待缺省 300 s → 单次启动最多约 1,201 次，两次启动可超 ≤200 | 第 1.2 节 F-8 | 推荐：按 IR-M1 结果定 `--llama-ready-timeout-s`（显式旗标下原读数 2.48 s 就绪，例如 20 s → 每启动 ≤81 次）；计量按「服务进程启动至打印 listening 的秒数 / 0.25 + 1」上界计入非推理 HTTP。若不改代码则只能上界估计，不能逐次计 |
| **IR-M8** | 「准备 1」用于第 2 节事实读取后，B0b 部署/资产核实并入收据单元 #2；原计划中「准备」含部署 | 四题 §3 步骤 2–3；第 14 节 | 推荐确认此分配属原签用途（3 次总数、3 批传输、`--version` 3 次均不变）；否则回用户 |

## 9. 未核风险与已知限制

- 第 1.3 节 A/B 用 3.12.14 源码树代理板 3.12.3；导入差异未逐版本核对。C/D 为指示性：源码归档与板上二进制的构建关系未认证（「Mac mini补核核清」§2）。
- JET 诊断原读数（F-2/F-6）是 10-06 时点、JET 合同下的诊断，不进本项证据；本项首次服务仍是正式核验。
- 内存：显式旗标下 RSS 约 3.16 GB、可用约 3.7 GB 只覆盖该配置；缺省旗标（IR-M1 备选）下未知。
- 有效载荷：原 §5.2 投影按 base64 估算推理请求体，而 Air→板为 multipart 原始 JPEG；`/result` 轮询响应字节未计入原投影；60 MB 余量未实测。
- Air 侧事实（来源链原件、`.venv-yoloe`、`ssh -G`、Unity 版本、编辑器是否改动已跟踪文件）全部未核（mini 不能读 Air）。
- 操作单内嵌命令只做了语法检查与 mini 本机只读执行（附录 A），未在 Air/板上执行；`ControlMaster` 复用、`tar` 管道、`-t` 交互会话下 Ctrl-C 传递均未运行验证。
- 板端会话变量需用户逐个 export；输入错误由 3/4 退出码或身份核对兜底，但会消耗该单元。

## 10. 复核范围（下一实际 `C3@K1K2K3K4` 只读核对 → 新鲜上下文 `R3@K1K2K3K4`）

- 完整候选 diff：第 5 节解析式；PLAY_GOVERNING 只有 `-play-ops.md`（相对最近通过候选非空 → 开 R 轮）。
- 核对重点：第 4 节映射逐项、第 13 节与「授权边界修订 2」逐码一致、第 0.4 节与四题 §2 表逐维度一致、第 1 节严格门、第 8 节待裁定是否应先于 R3 裁定（实现推荐：C3 内先裁 IR-M1…M8，再交 R3 复核终版）。
- 不含：代码复核（零 diff，R2 结论随候选携带）、运行验证（零消耗）。

## 11. 本轮用量

consumed：零。SSH 0、ping 0、复制 0、部署包 import 0、模型加载 0、测试/回放 0、板/Unity/runtime 操作 0；B-main 各维度 0；N-1/N-2/mini 子范围原账不变。本机只读：JSON/源码/GGUF 头部字节/源码归档流读取，scratchpad 写临时脚本与输出。

## 附录 A 来源解析块（Air 存为 `$OUT/prep/resolve-src.py`；仓库根运行；mini 本机只读执行 1 次 rc 0、末行 `RESOLVE_OK`）

`play_ops`（`source`/`prep`/`receipt`/`play` 阶段）按本标题前缀「## 附录 A 来源解析块」原样取出下块执行（OPS操作增量实现；原字节来源与静态闭集不变）；标题前缀与块正文任何改动都改变 PLAY_GOVERNING。

```python
import json, os, shlex, sys
J = "outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic"
def stop(code):
    print("STOP " + code); sys.exit(3)
for f in ("state.json", "budget.jsonl", "checkpoint.json"):
    if not os.path.isfile(os.path.join(J, f)):
        stop("SOURCE_ORIGINAL_MISSING " + f)
st = json.load(open(os.path.join(J, "state.json")))
step = st.get("board", {}).get("step")
if not step or not os.path.isfile(os.path.join(step, "receipt.json")):
    stop("BOARD_RECEIPT_MISSING")
rc = json.load(open(os.path.join(step, "receipt.json")))
q = st["q4"]
adm = rc["transfer"]["admitted"].split("|")
argv = rc["server"]["argv"]
weights = argv[argv.index("--model") + 1]
if adm[0] != weights or os.path.basename(weights) != q["basename"] or int(adm[2]) != int(q["bytes"]):
    stop("Q4_CHAIN_MISMATCH")
tr = json.load(open("docs/evidence/P1-ENG-JET-001-stageb-transfer.json"))
mm = [o for o in tr["objects"] if o.get("cls") == "G" and o.get("basename", "").startswith("mmproj-")]
if len(mm) != 1 or mm[0]["board_final"] != rc["board_paths"]["mmproj"] or argv[argv.index("--mmproj") + 1] != rc["board_paths"]["mmproj"]:
    stop("MMPROJ_CHAIN_MISMATCH")
br = json.load(open("docs/evidence/P1-ENG-JET-001-stageb-build-rerun.json"))
server = rc["board_paths"]["server"]
if argv[0] != server or br["board_batch_dir"]["path"].rstrip("/") + "/build/bin/llama-server" != server:
    stop("SERVER_CHAIN_MISMATCH")
sraw = br["products"]["llama_server_stat_raw"].split("|")
sha_now = rc["server_sha256_now"]
if len(sha_now) != 64:
    stop("SERVER_SHA_SOURCE_INVALID")
out = {
    "WEIGHTS": weights, "EXP_WEIGHTS_SHA": q["sha256"], "EXP_WEIGHTS_BYTES": str(q["bytes"]),
    "MMPROJ": mm[0]["board_final"], "EXP_MMPROJ_SHA": mm[0]["expected_sha256"], "EXP_MMPROJ_BYTES": str(mm[0]["expected_bytes"]),
    "LLAMA_BIN": server, "EXP_LLAMA_BIN_SHA": sha_now, "EXP_LLAMA_BIN_BYTES": sraw[2],
}
for k, v in out.items():
    print("%s=%s" % (k, shlex.quote(v)))
print("RESOLVE_OK")
```

## 附录 B 资产 JSON 生成块（Air 存为 `$OUT/prep/assets-gen.py`；调用见操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md` 第 3 节第 4 步：先该单第 0.3 节来源加载块 `src_load` 打印 `SOURCE_LOAD_OK`（有界普通 env 文件，AC-10 修订 2；不再用 `. <(…)`），再 `GEN=$("$PY" -I -B "$OUT/prep/assets-gen.py" "$OUT/b0b/assets-raw.txt" "$OUT/b0b/assets.json"); gen_rc=$?`，须 `gen_rc=0` 且末行 `ASSETS_OK`；版本解析按 AC-7 修订 5 / AC-16 修订 1（`身份修复K1K3`，2026-10-07）；只对离线夹具执行过，见 `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md` 第 3 节，未对真实板原流执行）

`play_ops receipt` 按本标题前缀「## 附录 B 资产 JSON 生成块」原样取出下块执行（OPS操作增量实现）；标题前缀与块正文任何改动都改变 PLAY_GOVERNING。

```python
import json, os, re, sys
raw_path, out_path = sys.argv[1], sys.argv[2]
raw = open(raw_path, encoding="utf-8", errors="replace").read()
env = os.environ
need = ("WEIGHTS", "MMPROJ", "LLAMA_BIN", "EXP_WEIGHTS_SHA", "EXP_MMPROJ_SHA", "EXP_LLAMA_BIN_SHA")
if any(not env.get(n) for n in need):
    print("STOP S-PRECHECK source_vars_missing"); sys.exit(3)
sha = {}
for line in raw.splitlines():
    m = re.match(r"^([0-9a-f]{64})  (.+)$", line)
    if m:
        sha[m.group(2)] = m.group(1)
got = (sha.get(env["WEIGHTS"]), sha.get(env["MMPROJ"]), sha.get(env["LLAMA_BIN"]))
if got != (env["EXP_WEIGHTS_SHA"], env["EXP_MMPROJ_SHA"], env["EXP_LLAMA_BIN_SHA"]):
    print("STOP S-IDENTITY asset_sha_mismatch_or_missing"); sys.exit(3)
# AC-7 修订 5：与 tools/language_serve.py::parse_runtime_build 同一语义——行首 `version:` 恰一行；
# 旧整数 `version: <整数> …` 取该整数，语义版本 `version: <语义版本> (build <整数>, commit <文本>)` 整行取 build；
# 缺行/重复冲突/缺 build/超出 ^b[0-9]{1,7}$/rc 非 0 一律 STOP，无缺省值。
lines = [l for l in raw.splitlines() if l.startswith("version:")]
m = None
if len(lines) == 1:
    m = re.match(r"^version: (\d+) ", lines[0]) or re.match(
        r"^version: [0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)? "
        r"\(build ([0-9]+), commit [^\s(),]+\)\Z", lines[0])
if m is None or re.match(r"^[0-9]{1,7}$", m.group(1)) is None or re.search(r"^rc=0$", raw, re.M) is None:
    print("STOP S-IDENTITY version_unparsed_duplicate_or_nonzero"); sys.exit(3)
doc = {
    "work_id": "P1-ENG-LOOP-002",
    "artifact": "AC-16 board assets (--expect-assets input)",
    "weights_sha256": got[0],
    "mmproj_sha256": got[1],
    "runtime_binary_sha256": got[2],
    "runtime_build": "b" + m.group(1),
    "runtime_version_line": lines[0],
    "quantization": "Q4_K_M",
    "raw_source": raw_path,
    "library_disclosure": (
        "Three-file identity only (LIB:FACT:1). Shared-library snapshot: "
        "docs/evidence/P1-ENG-LOOP-002-precheck.md, Mac mini R05-R07 (20 ldd entities, "
        "first snapshot, no historical sha expectation); NEEDED/ldd do not cover runtime "
        "dlopen (incl. libcuda); runtime_binary_sha256 is not a whole-stack identity."
    ),
}
with open(out_path, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(doc, indent=2, sort_keys=True) + "\n")
print("ASSETS_OK")
```

## 附录 C 本机静态分析脚本（mini scratchpad 运行；只读；正文逐字，sha 见第 1.3 节）

C1 `cmods.py`：`<uv 3.12 解释器> -I -B cmods.py <uv 3.12 标准库目录> <逗号分隔根>`。对代理标准库源码做 AST 遍历，跟随模块级 `import`/`from`（`try`/`if` 内标为可选），不跟随函数内导入；无 `.py`/包源码的模块记为 C 级模块。

```python
"""Static (AST-only, no import of analysed modules) stdlib closure for the
P1-ENG-LOOP-002 llama-server branch roots.  Stdlib source tree of a local
CPython 3.12 is used as a PROXY for the board's 3.12.3 (version differs).
Outputs C-level modules (no .py source) reached by module-level imports,
split into unconditional vs optional (inside try/except ImportError or if).
"""
import ast, sys, os, hashlib, time
print("epoch_start", repr(time.time()))
STD = sys.argv[1]
ROOTS = sys.argv[2].split(",")
print("proxy_stdlib", STD)

def locate(mod):
    parts = mod.split(".")
    p = os.path.join(STD, *parts)
    if os.path.isfile(p + ".py"):
        return p + ".py"
    if os.path.isfile(os.path.join(p, "__init__.py")):
        return os.path.join(p, "__init__.py")
    return None

def imports_of(path, mod):
    tree = ast.parse(open(path, "rb").read(), path)
    pkg = mod if path.endswith("__init__.py") else mod.rpartition(".")[0]
    out = []
    def visit(body, cond):
        for node in body:
            if isinstance(node, ast.Import):
                for a in node.names:
                    out.append((a.name, cond))
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = pkg
                    for _ in range(node.level - 1):
                        base = base.rpartition(".")[0]
                    m = base + ("." + node.module if node.module else "")
                else:
                    m = node.module
                out.append((m, cond))
                for a in node.names:  # from pkg import submodule
                    out.append((m + "." + a.name, cond + "|fromname"))
            elif isinstance(node, ast.Try):
                visit(node.body, "try")
                for h in node.handlers:
                    visit(h.body, "except")
                visit(node.orelse, cond); visit(node.finalbody, cond)
            elif isinstance(node, ast.If):
                visit(node.body, "if"); visit(node.orelse, "if")
            elif isinstance(node, (ast.With,)):
                visit(node.body, cond)
    visit(tree.body, "")
    return out

seen = {}
cmods = {}
queue = [(r, "", "ROOT") for r in ROOTS]
while queue:
    mod, cond, frm = queue.pop()
    if not mod:
        continue
    strict = cond == ""
    path = locate(mod)
    if path is None:
        if cond.endswith("|fromname") or "|fromname" in cond:
            continue  # name imported from module, not a submodule
        top = mod
        # parent packages must exist as source to count a C submodule; skip names
        prev = cmods.get(top)
        if prev is None or (strict and not prev[0]):
            cmods[top] = (strict, frm)
        continue
    key = mod
    if key in seen and (seen[key] or not strict):
        continue
    seen[key] = strict
    # parent packages are imported too
    if "." in mod:
        queue.append((mod.rpartition(".")[0], cond.replace("|fromname", ""), frm))
    for m, c in imports_of(path, mod):
        cc = "" if (c in ("", "|fromname") and strict) else (c or "cond")
        if c == "|fromname" and strict:
            cc = "|fromname"
        queue.append((m, cc, mod))

print("py_modules_reached", len(seen), "unconditional", sum(1 for v in seen.values() if v))
print("== C-level modules (no .py in proxy stdlib), unconditional (module-level, not under try/if):")
for k in sorted(c for c, v in cmods.items() if v[0]):
    print("  REQ", k, "<-", cmods[k][1])
print("== C-level modules reached only via try/except/if (optional or platform-guarded):")
for k in sorted(c for c, v in cmods.items() if not v[0]):
    print("  OPT", k, "<-", cmods[k][1])
print("epoch_end", repr(time.time()))
```

C2 `gguf_kv.py`：`/usr/bin/python3 -I -B gguf_kv.py <gguf>`。`struct` 解析 GGUF v3 头部 KV，读到张量信息前停止，不读张量数据。

```python
"""Read-only GGUF header KV dump (stdlib struct only; reads header bytes,
never tensor data; no model loading).  Prints selected scalar keys."""
import struct, sys, time, os
print("epoch_start", repr(time.time()))
path = sys.argv[1]
WANT = ("general.architecture", "general.name", "general.file_type",
        "context_length", "block_count", "embedding_length",
        "attention.head_count", "attention.head_count_kv",
        "attention.key_length", "attention.value_length", "rope.dimension_sections")
T = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i", 6: "<f", 7: "<?",
     10: "<Q", 11: "<q", 12: "<d"}
with open(path, "rb") as f:
    def rd(fmt):
        n = struct.calcsize(fmt); return struct.unpack(fmt, f.read(n))[0]
    def rstr():
        n = rd("<Q"); return f.read(n).decode("utf-8", "replace")
    def rval(t):
        if t in T: return rd(T[t])
        if t == 8: return rstr()
        if t == 9:
            et = rd("<I"); n = rd("<Q")
            if et == 8:
                return ("array<str>", n, [rstr() for _ in range(n)][:0])
            vals = [rval(et) for _ in range(n)]
            return ("array", n, vals[:8])
        raise ValueError(t)
    magic = f.read(4); ver = rd("<I"); nt = rd("<Q"); nkv = rd("<Q")
    print("magic", magic, "version", ver, "n_tensors", nt, "n_kv", nkv)
    for _ in range(nkv):
        k = rstr(); t = rd("<I"); v = rval(t)
        if any(k == w or k.endswith("." + w) for w in WANT):
            print("KV", k, "=", v)
    print("header_bytes_read", f.tell(), "file_bytes", os.path.getsize(path))
print("epoch_end", repr(time.time()))
```
