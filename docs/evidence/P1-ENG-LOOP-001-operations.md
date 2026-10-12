# P1-ENG-LOOP-001 — 阶段 A 实测操作单 A/B

Owner: Implementation（Cursor）
Date: 2026-09-20
合同：D4、AC-1…17、八行首次释义及十行实现期修订。执行与 T7 存储指令见
`docs/authorizations.md` 2026-09-20 两条；本单取代旧报告 §6/§7 的草稿命令。

## 0. 执行次序与记账

先核资产和环境 → 各机合并 → **5060 同设备 32 行两形态等价** → 确定最终形态
（等价通过用 `c2-merged`，不等价或合并失败回 `c2-adapter`）→ 各机 3 预热 + 32
计时 → 两份报告齐全后生成 K 收据。5060 未连通时 Mac 可先测合并形态，但报告
只能是待等价核实的测量；若后续回退，必须在原额度内改测最终形态。

| 资源 | Mac 上限 | 5060 上限 |
|---|---:|---:|
| 合并尝试（失败也计） | 2 | 2 |
| 模型加载/启动（合并加载也保守计入） | 6 | 6 |
| 查询行（含失败、预热） | 70 | 134 |
| base 下载 | 1（仅校验失败可重试 1 次） | 0，使用原有缓存 |

5060 等价占 64 行，HTTP 测量每轮占 35 行；不额外先跑本地时延再跑 HTTP。
测量 CLI 最多自动执行两轮，**不得在它失败后再手动重启整个两轮命令**。
启动前登记预留、结束后按原始查询日志核销；中断的尝试照计，不抹掉日志。
正式 ID、Unity/Play、外部模型 API、训练、Jetson、云端均为 0。
本单不使用 `--allow-shared-runtime`；现有 runtime 只读生效配置。

## A. Mac

在仓库根执行。T7 未挂载即停，不能让 `/Volumes/T7` 成为内置盘上的普通目录。

```bash
mount | grep '/Volumes/T7 '
export LOOP_T7=/Volumes/T7/TetheredDroneTracking/P1-ENG-LOOP-001
export HF_HOME="$LOOP_T7/hf-cache"
export PIP_CACHE_DIR="$LOOP_T7/pip-cache"
export TMPDIR="$LOOP_T7/tmp"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

本次已建 `.venv-language`（Python 3.12.13），已安装原钉版；第三方包目录放 T7，
本地只留解释器/脚本入口和链接。模型与中间件入口
`outputs/eng-loop/P1-ENG-LOOP-001` 链接到 T7 的 `artifacts`。两处链接所指外盘均
须可用。后续首次安装只用 `tools/requirements-language.txt`，缓存和临时文件同上；
不可改 `.venv-track`/`.venv-yoloe`，不可自行替换版本。

```bash
.venv-language/bin/python -m pip check
.venv-language/bin/python -m pip freeze
.venv-language/bin/python -m unittest discover -s tests -p 'test_language_*.py' \
  > docs/evidence/P1-ENG-LOOP-001-tests-language.log 2>&1
```

HTTP 测试要能绑定本机 loopback；受沙箱禁止的运行保留为环境失败记录，并在允许
loopback 的环境重跑。聚焦套件已包含真实 Pillow 预览与确认用例，不需再重复执行。
全套留到候选证据齐备的 K1K3 停点一次运行。

base 已按 `train_lora.BASE_REVISION` 下载完成，迁移校验后复用，**不要再次下载**。
首次下载操作须使用 `snapshot_download(..., local_dir=T7路径)`，revision 从冻结
`tools.eng_sft.train_lora.BASE_REVISION` 读取；文件 SHA 与下载 metadata 的 etag
逐一核对。C2 adapter 从训练摘要的 `adapter_manifest.adapter_sha256` 匹配
`returned/*/runs/C2/adapter/adapter_model.safetensors`，不手写 run 目录名。
smoke 使用原 `data/smoke.jsonl` 的 **32 个 sample_id**，图像按 `frame_sha256` 核实；
不得把含 gold 的完整行交给推理，测量器只投影 ID/图像/surface/g4。

T7 为 exFAT：迁移依赖使用字节复制（`shutil.copyfile`），不复制 xattr/resource fork。
本次 `copy2` 产生的 `._*.py` 被 Transformers 扫成源码，已仅在本任务目录清理。
任何目录枚举排除 `._*`，不能把它们当查询行或权重分片。

合并：`train_lora.load_model(base, device="cpu", adapter_dir=已核对的C2目录)`，
随后 `merge_and_unload()`、`save_pretrained(T7合并目录, max_shard_size="5GB")`，
保存 processor。CPU 仅用于同台 Mac 的权重合并以降低 MPS 内存压力；时延仍用 MPS。
每次合并前扣合并和加载各 1 次；失败也保留原始异常与收据，不重用产物。

**当前 Mac 合并额度已用完（2/2）**：第一次中断无完成收据，第二次导入失败。
不得再执行合并；以下合并形态命令仅为原流程说明，本轮实际使用未合并回退。
本次可复现执行脚本为 `P1-ENG-LOOP-001-measure-mac.py`（原信封内预留/结算，
使用 `c2-adapter`）。该脚本同样不可不看剩余额度而重复运行。

```bash
.venv-language/bin/python tools/language_latency.py measure \
  --host mac --backend local-hf --model-form c2-merged \
  --merged-source outputs/eng-loop/P1-ENG-LOOP-001/model/c2-merged \
  --smoke outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl \
  --package-root outputs/eng-sft/P1-ENG-SFT-002/upload \
  --scratch outputs/eng-loop/P1-ENG-LOOP-001/scratch-mac \
  --device mps --t-ret-s 60 --t-hard-s 60 \
  --out docs/evidence/P1-ENG-LOOP-001-latency-mac.json
```

若最终回退，用 `--model-form c2-adapter --model-source <T7 base目录>
--adapter-dir <已核对的C2目录>`，省去 `--merged-source`，保留先前报告并在独立路径
记录新报告。只有最终形态报告可进入 K 收据。

## B. 5060（已实测的 F 盘布局）

SSH 别名 `win5060`，Tailscale 地址 `100.100.100.100`；用户已明确授权完整代码、
C2 与 smoke 图像包传输。Windows 没有挂载 T7，用户选择 F 盘：
`F:\TetheredDroneTracking\P1-ENG-LOOP-001`。新环境、pip/HF 缓存、tmp、
合并产物、查询中间件与日志均在该根。只读复用原 C 盘 HF 缓存中的冻结 base，
不另下载或改写。Python 为既有 3.13.0，新隔离环境不修改其他环境。

依赖固定 torch 2.11.0+cu128、torchvision 0.26.0+cu128，其余沿用
`tools/requirements-language.txt`；完整依赖解析后 `pip check` 通过。安装日志的
PowerShell NativeCommandError 包含 pip stderr 提示，独立 pip check 与版本预检
确认包安装完整，不把安装外壳的退出码当作环境检查通过。

将 `P1-ENG-LOOP-001-5060-runner.py` 作为 `repo/operations_5060.py`，运行目录
为 `repo`。脚本检查逐文件清单、base/C2 SHA、32 行 smoke、CUDA/5060 后才记账执行。
Windows 无 Unix `resource`，生产 selector 的 `inference_engine()` 兼容导入明确
将不可用 RSS 查询抛错；不伪造 0 B。GPU 显存使用真实 CUDA API，冻结训练代码不改。

```powershell
$loopRoot = 'F:\TetheredDroneTracking\P1-ENG-LOOP-001'
$env:TEMP = "$loopRoot\tmp"
$env:TMP = "$loopRoot\tmp"
$env:PIP_CACHE_DIR = "$loopRoot\pip-cache"
$env:HF_HOME = "$loopRoot\hf-cache"
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONPATH = "$loopRoot\repo"
Set-Location "$loopRoot\repo"
$taskPython = "$loopRoot\.venv-language\Scripts\python.exe"
# 从既有 snapshot 读取 base；目录尾为冻结 train_lora.BASE_REVISION。
# $base 必须指向预检已核对的现有路径，不能用下载代替。
& $taskPython operations_5060.py preflight --root $loopRoot --base $base
& $taskPython operations_5060.py merge --root $loopRoot --base $base
& $taskPython operations_5060.py equivalence --root $loopRoot --base $base
& $taskPython operations_5060.py serve --root $loopRoot --base $base
```

以上是阶段顺序，不是无条件重跑指令。每步成功后才进下一步，先读
`receipts/execution-ledger.json`；脚本在动作前扣额并即时持久化，不能删除账本
恢复额度。合并目录已存在会拒绝覆盖。等价顺序加载两形态，释放首份后再加载第二份，
共 64 查询；结果 `selected_model_form` 决定服务形态。

Mac 客户端使用 `P1-ENG-LOOP-001-5060-client.py --startup <下载的服务启动收据>
--url <实际HTTP端点> --transport <实际传输方式>`。客户端核对 GPU、权重身份与
smoke SHA，3 预热 + 32 计时，HTTP 边界含上传和轮询；最多两轮，60 s 等待。
直连 `/status` 不通时可用私有 SSH 转发到同一服务；实际路径必须写入报告。

服务端 `http-memory.json` 提供 `torch.cuda.max_memory_allocated()`、PID、末条查询
与计数。结束后核对其 PID 与启动收据相同、查询账本与客户端样本一一对应，再并入
报告；Mac 客户端内存另列。仅停止本次启动并核验命令行的服务 PID。

## C. 两机证据与 K 收据

核实最终形态、权重身份、32 行顺序、hz/R、两轮上限及失败记录后才执行：

```bash
.venv-language/bin/python tools/language_latency.py k-receipt \
  --mac docs/evidence/P1-ENG-LOOP-001-latency-mac.json \
  --gpu docs/evidence/P1-ENG-LOOP-001-latency-5060.json \
  --out outputs/eng-loop/P1-ENG-LOOP-001/k-receipt.json
```

缺报告写 `MEASUREMENT_INCOMPLETE`，不将不可访问机器当 FAIL；两台实测均不合格
才是合同 `HOST_UNDECIDED`。两者均不能冻结运行收据。报告关联原始文件 SHA，
不要把外盘路径当唯一证据。阶段 B 操作单与真实 Play 等独立复核和单独 B 信封。

## D. 本轮完成后的固定状态

最终收据选择 5060/http/c2-adapter，K_ret/K_conf/K_pub=30/50/2。运行入口现在强制
核对两份测量报告 SHA、宿主/端点、形态和模型身份；报告相对路径按仓库根解析。
不要删除所引用的两份报告，也不要把旧收据用于不同权重、端点、hz/R 或测量来源。
HTTP 在启动时做真实身份握手，查询带期望身份，服务与客户端双向拒绝不符。

5060 模型启动 6/6、查询 134/134 已耗尽，服务已停止；上面的命令仅供复现审核，
不得在原 A 信封内重跑。Mac 合并 2/2 已耗尽，启动3/6、查询35/70。大文件保持 Mac T7、
5060 F盘布局。下一步为 C1@K1K3 → R1@K1K3；阶段 B 与正式 Play 仍须单独签发。
