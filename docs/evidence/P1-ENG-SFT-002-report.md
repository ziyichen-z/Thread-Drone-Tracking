# P1-ENG-SFT-002 K3 报告（候选 2：LoRA 训练与云端执行）

Status: K3 停点候选（`STABLE_CANDIDATE_AT_K3`）；`C1@K3` 退回的 C1-K3-1…4 已修正（§8），送 `C2@K3`；自证见 §7。接受侧 2026-09-18 已答复 P-K3-1…5（提案「待裁定」：AC-10 修订 1…3、AC-13 修订 1、
AC-7 修订 2），并要求执行前落实 K3-P1（预算与销毁截止）、K3-P2（自检受限安装与读取域）、K3-P3（实测边界）；本版已按此
修正代码、测试与操作单。5060 诊断已完成（§2.3，非证据）。云端作业 A/B 均已完成并回传、实例已销毁（账单 $1.72）；本地选优选中 C2
（§6.1），正式评估：功能门 `GATE_NOT_MET`、词表非劣 `NON_INFERIOR`、跨环境 `NOT_RUN(SFT_003_NOT_DONE)`（§6.2）。三项执行偏差已入账并经接受侧裁定（§6.1.4）。

工作项合同：`docs/proposals/P1-ENG-SFT-002-lora-training-and-cloud-execution.md`（AC-7…13 + 首次接受释义 + 待裁定修订）。
信封：`docs/authorizations.md` 2026-09-18「签发候选 2（K3）执行信封：5090、8 GPU·h、6美元」与同日「补录实现会话：Vast.ai、
A→B保持运行与5060诊断专用信封」。本文件同时是用户操作单（§2、§3）。候选、代码束与收据的哈希一律运行时解析，本文不手写。
文中所有耗时都是**估算（未实测）**，不作为任何守卫或验收依据（K3-P3）。

## 0. 当前状态与下一步

| 顺序 | 谁 | 做什么 | 状态 |
|---|---|---|---|
| 1 | 实现 | 源码 + 无 GPU 测试 + 代码束 + 操作单 | 已交付；K3-P1…3 修正已落实（§5） |
| 2 | 接受 | 答复 P-K3-1…5、补账 5060 诊断信封 | 已完成（2026-09-18） |
| 3 | 用户 | 5060 自检（§2），把 `selfcheck.json` 交给实现角色 | 已完成（第 1 次即成功，1/3） |
| 4 | 实现 | 解读自检结果（接口、显存、速度、版本差异） | 已完成（§2.3） |
| 5 | 用户 | 租机前按报价算预算（§3.0），再跑作业 A（§3.1–§3.4） | 已完成（2026-09-18，`complete`，启动 5/8；偏差见 §6.1.4） |
| 6 | 实现 | 回传校验 + 本地选优，给出作业 B 命令（§3.5） | 已完成（§6.1：选中 C2） |
| 7 | 用户 | 作业 B → 回传 → 销毁实例 → 报账单（§3.6–§3.7） | 已完成（作业 B `complete`；实例已销毁；账单 $1.72） |
| 8 | 实现 | 三份摘要、本报告 §6、停点全套测试与自证，交 `C1@K3` | 已完成（§6.2、§7） |
| 9 | 接受 | `C1@K3` 只读核对 | 已完成：退回 C1-K3-1…4（提案核对表） |
| 10 | 实现 | 修正 C1-K3-1…4、focused 与停点全套、自证 | 已完成（§7、§8） |
| 11 | 接受 → 复核 | `C2@K3`（不再退回，附关注项）→ `R<n>@K3` 独立复核与 `UNITY_NA` 附议 | **下一步** |

## 1. 交付物与写入分层

| 类别 | 路径 | 说明 |
|---|---|---|
| A1 源码 | `tools/eng_sft/train_lora.py` | 表 H 配方常量、批计划/学习率调度、assistant-only 损失掩码、冒烟判定、选优、tokenizer 复核、网格断言、训练与推理（GPU 栈延迟导入）；显存不够时同一步折半 micro-batch 重做并记录 |
| A1 源码 | `tools/eng_sft/cloud_runner.py` | `bundle`（本地）、`selfcheck-pack`（本地）、`budget-plan`（租机前）、`verify`、`budget-init`、`job-a`、`job-b`、`selfcheck`、`status`；实例启动账、计算层预算守卫与后台看门狗 |
| A1 源码 | `tools/eng_sft/verify_return.py` | 回传校验、本地选优、三份摘要；跨环境分支记 `NOT_RUN(SFT_003_NOT_DONE)` |
| A1 依赖 | `tools/requirements-eng-sft.txt` | torch 2.11.0+cu128 / torchvision 0.26.0+cu128 / transformers 5.17.0 / peft 0.21.0 / accelerate 1.15.0 / pillow 12.3.0 / tokenizers 0.23.2 / huggingface-hub 1.30.0 / safetensors 0.8.0 |
| A1 测试 | `tests/test_eng_sft_train.py`、`tests/test_eng_sft_cloud.py` | 无 GPU；云端编排用 `FakeEngine`（继承真实引擎，只换模型调用），夹具由 K4 生产链 + `bundle` 产出 |
| A2 本地 | `outputs/eng-sft/P1-ENG-SFT-002/upload/code/`、`upload/code-manifest.json`、`receipts/bundle-receipt.json` | K3 代码束；K4 数据包与其清单不改 |

版本选择：torch 与 transformers 取用户 5060 零样本探针当时的版本（`UT-OFFLINE-PROBE-2026-09-12`：torch 2.11.0+cu128、
transformers 5.17.0）；peft 0.21.0 与 accelerate 1.15.0 发布在 transformers 5.17.0 之后；tokenizers 0.23.2 与本地预检同版。
这只说明选版依据：**5090 上钉版本能否装上、能否跑通，以作业 A 实际安装与运行为准**；5060 自检记录的是诊断机自己的版本，
不证明云端同版已验证（K3-P2）。

## 2. 操作单 A：5060 笔记本自检（诊断，不是证据）

信封（账本 2026-09-18 补录）：只用 `smoke.jsonl`（32 条训练域样本）及其帧；每次 ≤ 4 行零样本、≤ 5 步训练、≤ 4 行 adapter
推理；累计 ≤ 3 次（含失败，不能换目录或清账重置）；只加装 peft 与 accelerate；复用探针环境与已有同版权重，不下载权重；
T7 或局域网运输，不上传公网；结果不进证据链，不占云端信封。

**2.1 在 Mac 上生成自检运输副本（只含代码束、清单与 smoke 及其帧）**

```bash
python3 -B -m tools.eng_sft.cloud_runner selfcheck-pack --out ~/Desktop/sft-selfcheck.tar
```

它先按自检子集把包核对一遍，再只打进 `data/smoke.jsonl`、它引用的帧、`manifests/`、两份清单和代码束；训练、选层、评估文件
和其余帧都不在里面，原 K4 包不改。把 `sft-selfcheck.tar` 用 T7 或局域网拷到笔记本。

**2.2 在笔记本上（PowerShell，先进入跑探针时用的那个 Python 环境）**

受限安装，先看 pip 打算装什么：

```powershell
python -m pip install --dry-run peft==0.21.0 accelerate==1.15.0
```

输出的 `Would install` 那一行**只能**有 `accelerate-1.15.0` 和 `peft-0.21.0`。多出任何别的包（或 pip 太旧不认 `--dry-run`），
就停下，把输出发给实现角色，不要装。只有这两个时再装，并确认没有缺依赖：

```powershell
python -m pip install --no-deps peft==0.21.0 accelerate==1.15.0
python -m pip check
```

`pip check` 应输出 `No broken requirements found.`，否则停下把输出发给实现角色。然后解包并运行（盘符按实际改）：

```powershell
mkdir D:\sft
tar -xf E:\sft-selfcheck.tar -C D:\sft
$env:PYTHONPATH = "D:\sft\upload\code"
$env:PYTHONDONTWRITEBYTECODE = "1"
cd D:\sft
python -B -m tools.eng_sft.cloud_runner selfcheck --package D:\sft\upload --work D:\sft\selfcheck-work
```

- 每次都用同一个 `--work D:\sft\selfcheck-work`，计次记在里面。
- 权重若不在 HuggingFace 缓存里、而是某个目录，末尾加 `--model <权重目录>`。命令只读本机（`local_files_only`），找不到就拒绝，不联网下载。
- 开跑前会先查：缺模块、没有 CUDA、本机没有同版权重 → 直接拒绝，**不计次**、不碰数据与模型；缺的东西不要去装，发给实现角色。
- 结束后把 `D:\sft\selfcheck-work\selfcheck-<时间>\selfcheck.json` 发给实现角色；失败也发（里面有报错）。
- 报「自检已运行 3 次」即信封用完，停。

**2.3 自检结果解读（2026-09-18，诊断，不是证据；不计入任何 AC 或冒烟门）**

用户第 1 次运行即成功（累计 1/3 次）；原件在本地 `outputs/eng-sft/P1-ENG-SFT-002/selfcheck/sft-selfcheck-work-20260918/`
（git 忽略，用户放在仓库根后由实现角色原样移入，避免未跟踪目录影响其他角色的写入检查）。

| 项 | 观察 | 说明 |
|---|---|---|
| 信封 | dry-run 只列出 `peft-0.21.0`（accelerate 已在环境中）；`--no-deps` 只装了 peft；`pip check` 无问题；权重取自本机 HF 缓存同版 revision；4 行 + 5 步 + 4 行 | 与账本诊断信封相符 |
| 环境 | RTX 5060 Laptop 8 GB（sm_120）、Windows 11、Python 3.13.0、torch 2.11.0+cu128；与钉版本相比只有 huggingface-hub 1.31.0 ≠ 1.30.0 | 诊断机记录，**不证明**云端 5090 上钉版本可装可跑 |
| 包与冻结链 | smoke 子集 30 个数据成员 + 10 个代码成员核对通过，冻结链 OK；Windows 上从包内 `code/` 运行 | 只对诊断有效，云端仍须全包校验 |
| tokenizer | 本机缓存 tokenizer 四文件 SHA 与本地预检收据一致；smoke 32 条 gold 重算与收据逐项相等 | 云端作业 A 对 train+smoke 另做一次 |
| 图像网格 | 25 张 smoke 帧全部 `[1, 30, 40]` | 与表 B 一致 |
| LoRA | 挂在 196 个模块（28 层 × 7），ViT 上 0 个；可训练参数 17.4 M；adapter 文件 69.8 MB（fp32） | 与表 H 一致；3 个 adapter 约 210 MB，在回传 512 MB 以内 |
| 训练 | micro-batch 1、有效批 16、5 步用时 72 s；loss 0.97 → 0.51；每步 453–590 个 assistant token（逐条核对 gold+1 未报错）；峰值显存 5.07 GB；未触发显存回退 | 只说明训练路径能跑、掩码数量对；**不说明** 60 步冒烟能否 < 0.05，也不能推算 5090 / micro-batch 8 的速度与显存 |
| 推理 | 零样本 4 行：约 0.6–3.1 s/行、14–98 个生成 token，输出带 ``` 代码块与缩进；5 步 adapter 重新加载后 4 行：约 4.9–17 s/行，已改为紧凑的 gold 格式、不再带代码块 | adapter 推理在该机上每 token 慢约 3–4 倍；推测与 Windows 下 196 个未合并 fp32 LoRA 层的逐层小核开销有关（未验证）。本合同不改为合并推理；若云端也明显变慢，由预算守卫兜底，并在报告中如实记录时长 |
| 解析 | 两次都有 1 行 `SCHEMA_ERROR`：模型在歧义候选里多写了 `label` 字段；冻结解析器按表 B 拒收 | 这是既定口径（候选只允许 `bbox_2d`），不改解析器；零样本对照会因此在歧义行上吃亏，报告按实际披露 |

结论：接口、加载、LoRA 挂载、损失掩码、adapter 存读与 Windows 兼容这几条路径在真实库上跑通；尚未验证的仍是云端 5090
上的安装、60 步冒烟收敛、micro-batch 8 的显存与各阶段真实耗时（K3-P3）。自检信封余 2 次，无需再用。

## 3. 操作单 B：vast.ai 云端作业

**先记住三件事：**
1. 计费从实例创建开始，到你在控制台**销毁**实例为止；装环境、下载、网格预检、等本地选优、处理报错的时间全部计入。
2. `budget-init` 会算出一个**销毁截止时刻**。无论当时在做什么（跑作业、等回传、等实现角色答复、看报错），到截止前都要把回传下载好并销毁实例。
3. 运行器里的预算守卫和看门狗**只能结束运行器进程**，不能停止实例计费，也不会替你销毁实例。它们按保守计时工作，不等于供应商的精确账单。

**3.0 租机前：按报价算预算（Mac 上即可，不写任何文件）**

从候选报价的详情里读出四项费率：GPU 小时价、存储小时价（按 20 GB 磁盘；若只给 $/GB/月，则用「单价 × 20 ÷ 720」折成小时价）、
入站流量 $/TB、出站流量 $/TB。免费的项填 0，但要在报价上确认确实免费；**哪一项读不出来，就不租这个报价**。

```bash
python3 -B -m tools.eng_sft.cloud_runner budget-plan --gpu-usd-per-hour <GPU小时价> --storage-usd-per-hour <存储小时价> --inbound-usd-per-tb <入站$/TB> --outbound-usd-per-tb <出站$/TB>
```

它先从 6 美元里扣掉流量预留（缺省按入站 12 GB、出站 1 GB 估算），剩下的按「GPU + 存储」小时价折成小时，再与 8 GPU·h 取小，
给出 `absolute_cap_hours`（最多可开多久）与 `guard_stop_hours`（运行器守卫停下的时刻，比前者早 6 分钟）。
`estimate_fits` 为 `false` 表示守卫时长短于全流程估算（约 4.5 h，未实测），建议换更便宜的报价。

**3.1 租机**

- 筛选：RTX 5090 × **1**、按需（不要选可中断/竞价实例）、驱动支持 CUDA ≥ 12.8；就用 §3.0 算过的那个报价。
- 镜像：带 Python 3.10–3.13 的 CUDA 12.8 镜像（vast.ai 模板列表里标 CUDA 12.8 的即可，镜像自带的 torch 版本无所谓）。
- 磁盘：分配 20 GB（信封上限）。

**3.2 登录后先做这几步**

```bash
nvidia-smi
df -h ~
```

`nvidia-smi` 应显示一张 RTX 5090；`df` 显示的可用空间要 ≥ 14 GB（估算：依赖约 5 GB + 权重 4.4 GB + 数据与回传约 1 GB）。
不满足就立刻销毁实例，把输出发给实现角色。

在 Mac 上打包并上传（端口与 IP 看 vast.ai 的 SSH 连接信息）：

```bash
COPYFILE_DISABLE=1 tar -cf ~/Desktop/sft-upload.tar -C outputs/eng-sft/P1-ENG-SFT-002 upload
scp -P <端口> ~/Desktop/sft-upload.tar root@<IP>:~/
```

`COPYFILE_DISABLE=1` 防止 macOS 往包里塞 `._*` 附属文件（`verify` 会把它们当成多出来的文件拒绝）。回到实例，
用 §3.0 的**同一组费率**加上控制台显示的「已运行分钟数」初始化预算：

```bash
mkdir -p ~/sft/work && tar -xf ~/sft-upload.tar -C ~/sft && rm ~/sft-upload.tar
cd ~/sft
PYTHONPATH=$HOME/sft/upload/code python3 -B -m tools.eng_sft.cloud_runner budget-init --work $HOME/sft/work --minutes-since-start <已运行分钟数> --gpu-usd-per-hour <GPU小时价> --storage-usd-per-hour <存储小时价> --inbound-usd-per-tb <入站$/TB> --outbound-usd-per-tb <出站$/TB>
```

最后一行会打印 `实例最迟在 <UTC 时刻>（本机时区 …）之前由你在 vast.ai 控制台销毁`。**把这个时刻记下来，在手机上设一个
「截止前 45 分钟」和一个「截止前 15 分钟」的闹钟。** `budget-init` 只能运行一次（再运行会被拒绝）。

**3.3 装环境并核对包**

```bash
python3 -m venv ~/sft/venv
source ~/sft/venv/bin/activate
pip install --no-cache-dir -r ~/sft/upload/code/tools/requirements-eng-sft.txt
export PYTHONPATH=$HOME/sft/upload/code PYTHONDONTWRITEBYTECODE=1
cd ~/sft
python -B -m tools.eng_sft.cloud_runner verify --package $HOME/sft/upload
```

- `python3 -m venv` 报缺模块时先 `apt-get install -y python3-venv`。
- `verify` 打印 `"frozen_chain": "OK"` 且 `"full": true` 才继续；否则把输出发给实现角色。
- 一律用 `python -B`，工作目录留在 `~/sft`（不要 `cd` 进 `upload/`）。

**3.4 作业 A（估算约 3–4 小时；放进 tmux，断线不影响）**

```bash
tmux new -s sft
source ~/sft/venv/bin/activate
export PYTHONPATH=$HOME/sft/upload/code PYTHONDONTWRITEBYTECODE=1
cd ~/sft
python -B -m tools.eng_sft.cloud_runner job-a --package $HOME/sft/upload --work $HOME/sft/work 2>&1 | tee -a $HOME/sft/work/job-a.log
```

顺序：包校验 → 下载 base 权重（只这一次）→ tokenizer 复核 → 图像网格预检 → 零样本（609 行）→ 冒烟（60 步 + 32 行）
→ C1、C2、C3 训练，每个训练完在选层子集上预测 441 行。断线后用 `tmux attach -t sft` 回来看。随时可在另一个窗口看账：

```bash
python -B -m tools.eng_sft.cloud_runner status --work $HOME/sft/work
```

结束时会写 `作业 A <job_id> 结束：complete`，并再次提示销毁截止时刻。打包回传（`<job_id>` 换成实际值）：

```bash
tar -cf ~/sft/jobA.tar -C ~/sft/work/returned <job_id>
```

在 Mac 上：

```bash
scp -P <端口> root@<IP>:~/sft/jobA.tar ~/Downloads/
mkdir -p outputs/eng-sft/P1-ENG-SFT-002/returned
tar -xf ~/Downloads/jobA.tar -C outputs/eng-sft/P1-ENG-SFT-002/returned
```

实例在余额内保持运行（用户 2026-09-18 选择），告诉实现角色「作业 A 回传好了」。

**3.5 本地选优（实现角色做，估算几分钟）**

实现角色运行 `verify_return verify` 与 `verify_return select`，把作业 B 的完整命令（含 `--from-job` 与 `--adapter`）交给用户。
选层集 gold 只在本机，按合同永不上云，所以这一步只能在本地做。**等待有硬截止**：到「截止前 45 分钟」闹钟响时还没拿到作业 B 命令，
就不再等——回传已下载好的话直接销毁实例，作业 B 另行向用户申请（重新下载权重超出本信封）。

**3.6 作业 B（估算约 20–30 分钟）**

在实例的 tmux 里运行实现角色给出的命令，形如：

```bash
python -B -m tools.eng_sft.cloud_runner job-b --package $HOME/sft/upload --work $HOME/sft/work --from-job <作业A的job_id> --adapter <C1|C2|C3> 2>&1 | tee -a $HOME/sft/work/job-b.log
```

结束后同 §3.4 打包 `~/sft/work/returned/<作业B的job_id>` 下载到同一个本地 `returned/` 目录，再运行一次 `status` 把输出存下来。

**3.7 收尾**

1. 确认回传目录都已下载到 Mac 后，在 vast.ai 控制台**销毁**实例（不是停止：停止后存储仍计费）。最迟不晚于销毁截止时刻。
2. 从 vast.ai 账单页记下本次实例的计费时长与总费用（美元，分 GPU/存储/流量），连同 `status` 输出发给实现角色；云端运行事实
   由接受/辅助角色代录 `docs/unity-test-log.md` 条目 `UT-P1-ENG-SFT-002-cloud-runs`。

**出错怎么办（一律受销毁截止约束）**

| 现象 | 含义 | 怎么做 |
|---|---|---|
| `拒绝启动：…`（退出码 2） | 信封之外：启动次数用完、不是单张 5090、版本不符、权重需要重下、预算已到；续跑或作业 B 时包身份/环境与已记录的不同、自检参数越界（C1@K3 修正后） | 不重试，把输出发给实现角色；这些都要回用户决定 |
| `预算守卫停止：…`（退出码 3） | 已到守卫时刻（截止前 6 分钟） | 立刻下载已有回传目录，销毁实例，告诉实现角色 |
| `预算看门狗：到达守卫时刻，运行器已停`（退出码 3） | 某一步或下载卡住，看门狗按时结束了运行器 | 同上 |
| `失败（SMOKE_FAILED）` | 冒烟没过（表 H 规则） | 下载回传目录、销毁实例；按合同回接受角色，不自行调参 |
| `失败（TOKENIZER_MISMATCH / IMAGE_GRID_MISMATCH / PACKAGE_INCOMPLETE / FROZEN_SET_MISMATCH）` | 合同的 fail-closed 检查拦住了 | 不重试，把输出发给实现角色 |
| Python 报错栈（Traceback） | 代码或环境问题 | 把 `job-a.log` 最后 80 行发给实现角色；实例最多保留到「截止前 15 分钟」闹钟，到时还没有答复就下载回传、销毁实例。按答复续跑用 `--resume <job_id>`（只重跑没完成的阶段，仍计次） |

## 4. AC-7…13 证据指针（现状）

| 编号 | 证据 | 现状 |
|---|---|---|
| AC-7（含修订 1/2） | `test:tests.test_eng_sft_cloud.PackageTests.test_missing_or_extra_member_in_either_manifest_refuses_run`；`test:tests.test_eng_sft_cloud.PackageTests.test_code_manifest_lists_every_bundle_member_except_itself`；`test:tests.test_eng_sft_cloud.FreezeTests.test_mismatched_manifest_or_receipt_refuses_run`；`test:tests.test_eng_sft_cloud.FreezeTests.test_frozen_files_and_data_package_untouched_by_candidate_2`；C1-K3-1：`test:tests.test_eng_sft_cloud.JobTests.test_resume_with_changed_bundle_or_environment_is_refused_before_any_write`、`test:tests.test_eng_sft_cloud.JobTests.test_job_b_refuses_job_a_from_another_bundle_before_creating_job`；另 `ReturnTests.test_returned_manifest_must_match_local_package_and_bundle`、`FreezeTests.test_real_frozen_set_still_matches_local_freeze_receipt`、`SelfcheckTests.test_selfcheck_pack_carries_only_smoke_code_and_manifests` | focused 通过；云端全包 `verify` 在作业 A 实跑通过（`frozen_chain` OK、`full` true）；两次回传本地 `verify` 通过（§6.1.1、§6.2.1） |
| AC-8 | `test:tests.test_eng_sft_train.PrecheckTests.test_overflow_fails_closed_without_truncation`；`test:tests.test_eng_sft_train.PrecheckTests.test_cloud_recount_mismatch_stops`；`test:tests.test_eng_sft_train.GridTests.test_grid_assertion_is_per_dataset`；另 `JobTests.test_tokenizer_file_mismatch_stops_before_inference`；`artifact:docs/evidence/P1-ENG-SFT-002-train-summary.json` | 测试通过；云端 tokenizer 复核与本地预检收据一致（train 4,907 行、smoke 32 行，max 87 ≤ 152），网格 2,327 张 `[1,30,40]` 零不符（train-summary） |
| AC-9 | `artifact:docs/evidence/P1-ENG-SFT-002-zero-shot-v2-summary.json`；`artifact:outputs/eng-sft/P1-ENG-SFT-002/returned/<job_id>/job-receipt.json` | 已产出：609 行，本地评分，含表 F 指标、分层与 v1 诊断附表（§6.2.4） |
| AC-10（含修订 1/2/3） | `test:tests.test_eng_sft_train.TemplateTests.test_assistant_only_loss_mask`；`test:tests.test_eng_sft_train.ConfigTests.test_only_three_candidates_in_order`；`test:tests.test_eng_sft_train.SelectionTests.test_tie_break_prefers_fewer_epochs_then_lower_lr`；`test:tests.test_eng_sft_train.ScheduleTests.test_smoke_runs_exactly_sixty_steps_on_thirty_two_rows`；`test:tests.test_eng_sft_train.SmokeTests.test_smoke_needs_low_last_loss_and_all_states_correct`；另 `ScheduleTests.test_multiset_expansion_batches_and_schedule_are_deterministic`、`SelectionTests.test_selection_score_is_macro_over_three_gold_states`、`JobTests.test_job_a_resume_skips_finished_stages_and_counts_retry`；`artifact:docs/evidence/P1-ENG-SFT-002-train-summary.json`；`artifact:outputs/eng-sft/P1-ENG-SFT-002/receipts/selection-<job_id>.json` | 已产出：冒烟通过，三 run 完成，选中 C2（§6.1.2）；train-summary 含 adapter manifest 与各阶段账目 |
| AC-11 | `test:tests.test_eng_sft_cloud.ReturnTests.test_return_hash_mismatch_refuses_scoring`；C1-K3-2：`test:tests.test_eng_sft_cloud.ReturnTests.test_summarise_refuses_selection_not_bound_to_current_job_a`；另 `ReturnTests.test_end_to_end_select_job_b_and_summaries`；`artifact:docs/evidence/P1-ENG-SFT-002-eval-summary.json`；`cmd:python3 tools/eng_sft/evaluate.py --verdict docs/evidence/P1-ENG-SFT-002-eval-summary.json` | 已产出：`GATE_NOT_MET` / `NON_INFERIOR`，失败分析见 §6.2.6 |
| AC-12 | `test:tests.test_eng_sft_cloud.TransferTests.test_syndrone_frames_never_in_training_package`；`test:tests.test_eng_sft_cloud.TransferTests.test_incompatible_schema_yields_not_run`；`test:tests.test_eng_sft_evaluate.TransferTests.test_transfer_verdict_is_mechanical_with_na_rule`（K4 已交）；`artifact:docs/evidence/P1-ENG-SFT-002-eval-summary.json` | 签发日终态 `NOT_RUN(SFT_003_NOT_DONE)`：代码束 `transfer_branch` 固定该值、SynDrone 成员 0；eval-summary 的 `verdict.transfer` 已写同值 |
| AC-13（含修订 1） | `test:tests.test_eng_sft_cloud.WriteBoundaryTests.test_no_controller_imports_and_forbidden_roots`；`test:tests.test_eng_sft_cloud.LedgerTests`（启动账、预算上限含存储/流量、看门狗、看门狗停机记录）；C1-K3-3：`test:tests.test_eng_sft_cloud.SelfcheckTests.test_selfcheck_rejects_out_of_range_values_before_counting`；另 `WriteBoundaryTests.test_bundle_modules_import_only_bundled_code`、`SetupStopTests.test_budget_stop_during_setup_leaves_stop_receipt`、`JobTests.test_job_refuses_wrong_gpu_or_version_drift`（含命令行无绕过开关）；`artifact:docs/evidence/P1-ENG-SFT-002-report.md` §3/§5 | 已完成：§6.2 三问答复、表 G、分层、失败案例（`ReturnTests.test_end_to_end_select_job_b_and_summaries` 覆盖提取）、来源与许可、账目对信封（账单 $1.72）；云端磁盘偏差 D-1 已入账并经接受侧裁定为该实例单次例外（§6.1.4） |

## 5. 接受侧答复落实与已知限制

接受侧 2026-09-18 已把 P-K3-1…5 转入提案「待裁定」并答复为 AC-10 修订 1…3、AC-13 修订 1、AC-7 修订 2（新 AC = 0）。
原提请表保留在下方作为来历；现行口径以提案为准。训练/冒烟/选优/代码束的取法按原样接受；报告不再笼统称整套实现等于
HF Trainer 缺省，只以表中逐项列出的具体参数为准（AC-10 修订 2）。

| 编号 | 合同缺口 | 实现取法（已接受，见提案对应修订） |
|---|---|---|
| P-K3-1 | 表 H 冒烟只写「32 条、≤ 60 步、末步 loss < 0.05、32/32 状态正确」，未写学习率、步数构成与判据口径 | lr 取 C1 的 1e-4；32 条不按 `oversample_copies` 展开，有效批 16 → 每 epoch 2 步 × 30 epoch = 60 步；warmup ⌈3% × 60⌉ = 2 步 + cosine 到 0，调度在更新后推进；「末步 loss」= 第 60 步有效批 assistant token 平均交叉熵（该步更新前的前向）；末步更新后的权重用于 32 行 greedy 预测，经冻结 `parse.py` 解析后 `status_pred == state` 才算对，解析失败记错；冒烟 adapter 不参与选优，记 SHA 后删除。60 步内压不到 0.05 即按表 H 原规则 `SMOKE_FAILED` 停止回接受角色 |
| P-K3-2 | 表 H 固定项未写优化器、裁剪、批切分、洗牌与损失归一 | AdamW（β 0.9/0.999、ε 1e-8、wd 0）、梯度裁剪 1.0；每 epoch 步数 = ⌈多重集行数 / 16⌉，末批保留（N = 5318：C1/C3 666 步、C2 999 步）；warmup = ⌈3% × 总步数⌉；每 epoch（从 0 起）用 `random.Random(f"{seed}:{epoch}")` 洗牌；有效批 16 = micro-batch × 梯度累积（5090 初值 8 × 2），损失 = 有效批全部 assistant token 交叉熵之和 / token 数；micro-batch 只影响显存，不改步数与归一分母，但不保证与其他切分逐位相同（dropout / 浮点顺序），实际值逐步记录；assistant token = gold + `<|im_end|>`（不含其后换行），逐条核对模板内打标签的 token 数 = gold 独立计数 + 1，不等 → `TOKENIZER_MISMATCH`；LoRA 参数 fp32、base bf16、SDPA 注意力；LoRA 用正则只挂 LLM 各层 7 个投影，挂载后核对数量 = 层数 × 7 且 ViT 上为 0 |
| P-K3-3 | 表 H 选优「三态状态级 macro 准确率」未定义到公式 | (acc_unique + acc_ambiguous + acc_none) / 3，每类按冻结 441 行选层集的 gold 状态分组，分子为解析成功且状态正确的行数（不看框）；并列集合 = 与最高分差 ≤ 0.5 pp（有理数精确比较，不是传递式两两并列）的全部候选 → epoch 少 → lr 低 |
| P-K3-4 | 账本「8 GPU·h 与 6 美元先达即停」的执行口径 | 接受启动账、失败计次、提前 6 分钟余量与 `stopped_budget`；**不接受**把逐行/逐步检查称为实例停费——落实见下表 K3-P1 |
| P-K3-5 | 表 K 代码束形态的两处细节 | (a) `bundle` 生成空的 `code/tools/__init__.py`，code-manifest 记 `source: null`、生成说明、字节与 SHA；(b) 一律 `python -B`、工作目录在包外；正式云端 `__pycache__` 没有例外；5060 的 smoke 子集校验只对诊断有效 |

**执行前修正的落实（提案「执行前修正与验证边界」K3-P1…3）：**

| 项 | 落实 | 证据指针 |
|---|---|---|
| K3-P1 预算及停费 | (1) `budget-plan`：租机前按报价的 GPU、存储小时价与进/出流量 $/TB 算上限，先从 6 美元扣流量预留，再与 8 GPU·h 取小；任一费率缺失/为负即拒绝（费用不明不租）。(2) `budget-init` 写出**绝对销毁截止时刻**与守卫时刻（早 6 分钟），打印 UTC 与本机时间。(3) 守卫除阶段入口与逐行/逐步外，下载前、网格预检前与网格预检逐张都检查；阶段外被停也写 `stop` 收据。(4) 后台看门狗从作业前置检查通过起全程运行，到守卫时刻即尽力记账（进行中阶段记 `stopped_budget_watchdog`、写 `watchdog-stop.json` 与作业收据）后 `os._exit(3)`，不依赖下一次 callback，单步或下载卡住也照停。(5) 操作单 §3 写明：运行器不销毁实例、不停止计费；截止时刻、两个闹钟、A→B 等待与报错等待的硬截止、销毁（不是停止）动作与账单分项回报。(6) 命令行删除 `--allow-version-drift`；版本漂移、非单张 5090、权重重下、次数上限都没有绕过开关 | `test:tests.test_eng_sft_cloud.LedgerTests.test_budget_plan_reserves_storage_and_transfer_inside_six_dollars`；`test:tests.test_eng_sft_cloud.LedgerTests.test_budget_guard_caps_hours_and_dollars`；`test:tests.test_eng_sft_cloud.LedgerTests.test_watchdog_fires_without_waiting_for_a_step_callback`；`test:tests.test_eng_sft_cloud.LedgerTests.test_watchdog_exit_records_stop_before_exiting`；`test:tests.test_eng_sft_cloud.SetupStopTests.test_budget_stop_during_setup_leaves_stop_receipt`；`test:tests.test_eng_sft_cloud.JobTests.test_job_refuses_wrong_gpu_or_version_drift`；§3 |
| K3-P2 自检信封落实 | (1) 受限安装：先 `pip install --dry-run` 只允许出现 peft/accelerate，再 `--no-deps` 安装并 `pip check`；多出任何包即停。(2) `selfcheck` 开跑前先做**不计次**前置：缺模块（只查不装）、无 CUDA、本机没有同版权重 → 拒绝，此时未碰数据与模型；通过后才计次，失败也计。(3) `selfcheck-pack` 只把代码束、两份清单、`manifests/`、`smoke.jsonl` 及其帧装进运输副本，训练/选层/评估文件不出本机，原 K4 包不改。(4) 自检报告的版本差异只作诊断记录，实现角色解读时逐项说明，不称云端同版已验证 | `test:tests.test_eng_sft_cloud.SelfcheckTests.test_selfcheck_pack_carries_only_smoke_code_and_manifests`；`test:tests.test_eng_sft_cloud.SelfcheckTests.test_selfcheck_runs_on_transport_copy_and_counts_runs`；`test:tests.test_eng_sft_cloud.SelfcheckTests.test_selfcheck_preflight_refusal_is_not_counted`；§2 |
| K3-P3 实测边界 | 见下方「已知限制」；训练循环在显存不足时同一步折半 micro-batch 重做（有效批 16 与数据不变），初值、终值与每次变化写入 run 结果与逐步日志，不另开免费探测 | `test:tests.test_eng_sft_train.ScheduleTests.test_multiset_expansion_batches_and_schedule_are_deterministic`（`next_micro_batch`）；`artifact:docs/evidence/P1-ENG-SFT-002-train-summary.json`（回传后） |

已知限制（K3-P3）：

- 45 项无 GPU 测试覆盖纯函数与 `FakeEngine` 编排，**不执行**真实 `load_model`、PEFT 前向/反向、processor 或 CUDA。
- 5060 自检最多 5 步、micro-batch 1：能检查接口、LoRA 挂载、adapter 存读和诊断机上的显存/速度，**不能**证明云端 60 步冒烟达标，
  也不能证明 5090 上 micro-batch 8 可用；冒烟收敛与选优只能在作业 A 中第一次实跑。
- `_assistant_loss_sum` 先产出整段序列的 logits 再挑 assistant 位置，所以峰值显存不能从 LoRA 参数量推断；实际峰值与耗时以诊断
  与正式作业的记录为准。
- 文中所有耗时（全流程约 4.5 h、作业 A 3–4 h、作业 B 20–30 min、自检几分钟）都是估算；`ESTIMATED_NEED_HOURS` 只用于租机前
  提示，不参与守卫。
- vast.ai 分配的磁盘是否把镜像本身算进去，本会话无法核实；§3.2 的 `df` 检查兜底。
- 预算计时从 `budget-init` 回推的开机时刻起算，开机到登录的分钟数由用户按控制台补记；这是保守计时，实际费用以 vast.ai 账单为准，由用户分项回填。

## 6. 结果（回传后填写）

### 6.1 作业 A 回传、本地校验与选优（实现侧 2026-09-18；中间结果，不是 K3 结论）

作业 A 的 job_id、收据与 adapter 的 SHA 一律从 `outputs/eng-sft/P1-ENG-SFT-002/returned/` 下唯一的作业 A 目录及其
`job-receipt.json` 运行时解析，本文不手写。

**6.1.1 回传与校验。** 用户按 §3.4 下载作业 A 回传（outcome `complete`），实例侧与本机侧逐文件 SHA 清单（`logs/jobA-instance.sha256`、
`logs/jobA-local-after-download.sha256`，各 21 行）哈希集合一致。实现侧运行
`python3 -B -m tools.eng_sft.verify_return verify --job <作业A回传目录>`：退出码 0；`complete: true`；收据外 20 个工件逐一
与收据的字节数与 SHA 相符，无缺失、无多出；上传清单与代码清单 SHA 与本地 package/bundle 收据一致，job_id 带冻结收据前缀；
回传合计 211.0 MB（≤ 512 MB），三个 adapter 各 69.8 MB（≤ 200 MB）。输出存 `logs/jobA-verify-return-rerun.out`。

**6.1.2 选优（表 H，AC-10 修订 3 公式）。** `python3 -B -m tools.eng_sft.verify_return select --job-a <作业A回传目录>`：退出码 0，
本地 `select-eval.jsonl` 先核对冻结收据 SHA 后评分；收据 `receipts/selection-<job_id>.json`，输出存 `logs/jobA-select-rerun.out`。
同目录 `logs/selection-prior-20260918T222431Z.json` 是 3 分钟前另一次同命令运行的收据副本，除 `utc` 外逐字段相同。

| 候选 | epoch / lr | unique（300） | ambiguous（41） | none（100） | macro（精确分数） |
|---|---|---|---|---|---|
| C1 | 2 / 1e-4 | 265（88.33%） | 34（82.93%） | 59（59.00%） | 0.76753（14161/18450） |
| **C2** | 3 / 1e-4 | 267（89.00%） | 35（85.37%） | 67（67.00%） | **0.80455（2474/3075）** |
| C3 | 2 / 5e-5 | 254（84.67%） | 7（17.07%） | 54（54.00%） | 0.51913（4789/9225） |

C2 比次高的 C1 高 3.70 pp（> 0.5 pp），并列集合只有 C2，按「最高 macro」选中 C2，未用到 epoch/lr 次序。这是 441 行盲选层子集上
的选优分数，只用于选 adapter，不是评估集结果，也不作任何对外指标。三个 run 的 micro-batch 都是 8 → 8、无折半；峰值 GPU 显存
各 8.80 GB（8,796,921,344 B）；LoRA 196 模块、ViT 0；三份选层预测各 441 行。

**6.1.3 作业 B 命令（已交用户）。** 在实例 tmux 内，按 §3.6 形式运行，`--from-job` 为上述作业 A 的 job_id，`--adapter C2`：

```bash
python -B -m tools.eng_sft.cloud_runner job-b --package $HOME/sft/upload --work $HOME/sft/work --from-job <作业A的job_id> --adapter C2 2>&1 | tee -a $HOME/sft/work/job-b.log
```

作业 B 在实例上重新核对 C2 adapter 的 SHA 与作业 A 收据、要求实例上的 `base/` 完整（不重下权重），然后在 609 行盲评估集上预测一次。
计次：总启动 6/8、正式评估 1/2；Unity 推理行累计将为 609 + 32 + 3 × 441 + 609 = 2,573（≤ 4,264）。耗时按作业 A 实测单行
延迟 p50 约 1.43 s 推算约 15–20 分钟（估算）。

**6.1.4 执行偏差（如实记录；用户原话已由辅助角色逐字入账，接受侧已在 C1@K3 裁定；实现角色对账本只读）。**

| # | 偏差 | 与信封/操作单的关系 | 现状 |
|---|---|---|---|
| D-1 | 实例磁盘 32 GB | 超出账本 2026-09-18 签发条目「云端磁盘≤20 GB」与 §3.1「分配 20 GB」 | 已入账（账本 2026-09-18「补录顾问会话（云端作业 A/B）」）。接受侧 C1@K3 裁定：用户在被告知 32 GB 并给出 A/B 选择后回「继续」，接受为**仅该已租实例**的知情继续及 32 GB 单次例外；≤ 20 GB 一般上限与 6 美元/8 GPU·h 等边界不变 |
| D-2 | `budget-init` 参数口径与租前核价 | 「已运行分钟数」按保守 30 分钟填写；费率以合计价 0.596 美元/时填入 GPU 项（含 32 GB 盘，存储项填 0）；进/出流量价 16.0 / 17.334 美元/TB 沿用预览报价，**租前未对这台机器核实**，与 §3.0「哪一项读不出来，就不租」不符 | 已发生的流程偏差，如实披露；接受侧裁定没有对应的用户原话可作核价证据。账单（§6.2.9）流量单价 $3/TB、$4/TB 低于沿用值，只证明本次费用未超限，不能补成「租前已核实」，也不豁免 AC-13 修订 1；不要求重租 |
| D-3 | 实际机器与租前预览不一致 | 实际为 Machine ID 49260 / 实例 51480628，不是租机前看过明细的那台（m:43438）；§3.0 要求「就用算过的那个报价」 | 已入账；接受侧与 D-1 一并裁定为该实例的知情继续。单张 RTX 5090 与 CUDA 由作业 A 的前置检查实测通过（`env.json`） |

作业 A 结束时收据的保守计时为 2.42 h、估算 1.65 美元（不是账单）；销毁截止 UTC 2026-09-19 03:52（EDT 23:52），守卫时刻早 6 分钟；
按 §3.5，作业 B 的等待硬截止为销毁截止前 45 分钟（UTC 03:07 / EDT 23:07）。

### 6.2 作业 B 回传、正式评估与判定（实现侧 2026-09-18）

两次作业的 job_id、收据与预测 SHA 从 `returned/` 下两个作业目录的 `job-receipt.json` 运行时解析，并已写入三份摘要；本文不手写。

**6.2.1 回传、校验与评分命令。** 作业 B `complete`（总启动 6/8，正式评估 1/2），实例侧与本机侧 SHA 清单（`logs/jobB-*.sha256`，
各 3 行）一致。本地依次运行，退出码全为 0：

| 命令 | 结果 |
|---|---|
| `python3 -B -m tools.eng_sft.verify_return verify --job <作业B回传目录>` | 2 个工件 + 收据相符，与本地 package/bundle 收据绑定；两次回传合计 211.3 MB（≤ 512 MB） |
| `python3 -B -m tools.eng_sft.verify_return summarise --job-a <作业A回传目录> --job-b <作业B回传目录>` | 写出三份摘要：`docs/evidence/P1-ENG-SFT-002-{zero-shot-v2-summary,train-summary,eval-summary}.json`（各 ≤ 2 MB）；核对作业 B 的 adapter = 本地选优结果（C2、SHA、来源作业 A）、预测 `model_id` = 该 adapter；本地 `eval.jsonl` 先核对冻结收据 SHA；本地全目录 440 MB（≤ 0.9 GB）；峰值 RSS 0.99 GB |
| `python3 tools/eng_sft/evaluate.py --verdict docs/evidence/P1-ENG-SFT-002-eval-summary.json`（AC-11） | 读出下表判定，与 summarise 一致 |

评分只在本机用冻结 `evaluate.py` 完成；609 行预测完整，解析失败 0。eval-summary 另含 AC-13 失败案例（§6.2.7，
由 `verify_return.failure_cases` 生成，见 §7）。

**6.2.2 三个问题的直接回答（提案 §1）。**

- **(a) 微调能否让模型输出三态协议：部分做到，功能门 `GATE_NOT_MET`。** 格式层面达成：609 行解析失败 0、各组无效率 0（prompt v2
  零样本有 103 行解析失败：`TRUNCATED` 31、`SCHEMA_ERROR` 72）。表 G 五项检查通过 1 项：G1∪G2 误报歧义率 2.3%（≤ 10%）；未达 4 项：
  G3 报告率 39.6%（≥ 70%）、G3 严格成功 25.0%（≥ 50%）、G1∪G2 误报 none 率 11.6%（≤ 5%）、G5 none 率 79.0%（≥ 80%，差 1 行）。
- **(b) 词表只靠 prompt 时选框是否不退化：`NON_INFERIOR`。** G1∪G2 同一 259 行配对差（微调 − prompt v2 零样本）点估计 +26.6 pp，
  bootstrap CI [+20.5, +32.8]（2,000 次、seed 20260912，只披露），阈值 −2.0 pp。**解读限制**：对照是合同指定的 prompt v2 零样本，
  它本身有 103 行解析失败；v1 诊断附表（只报告）在 345 行可比行上：旧探针 v1 输出 252 行成功（73.0%）、v2 零样本 139 行（40.3%）、
  微调 272 行（78.8%）。所以 +26.6 pp 里有相当部分来自格式遵从，不能读成「定位能力提高 26.6 pp」。
- **(c) 跨环境迁移：`NOT_RUN(SFT_003_NOT_DONE)`。** 签发日一次性判定的终态（AC-12）；SynDrone 帧、推理与额度均为 0，不推断可迁移性。

**6.2.3 表 G 判定表。**

| 层 | 结果 | 依据 |
|---|---|---|
| 功能门 | **`GATE_NOT_MET`** | (a) G3 报告率 0.396 < 0.70、严格成功 0.250 < 0.50；(b) 误报歧义 0.023 ≤ 0.10 通过，误报 none 0.116 > 0.05；(c) G5 none 0.790 < 0.80 |
| 词表非劣（退化监测） | **`NON_INFERIOR`** | (d) +26.6 pp ≥ −2.0 pp；CI [+20.5, +32.8] 只披露 |
| 目标车子组与增量 | 描述性 | G1t / G2t +26.1 pp [8.7, 43.5]；G3t 报告率 +41.7 pp、严格成功 +0.0 pp（见 §6.2.4） |
| 跨环境（表 L） | **`NOT_RUN(SFT_003_NOT_DONE)`** | 前置不成立（003 未 DONE），签发日终态；m1–m6、迁移比均不计算 |
| 完成状态 | 未 `DONE` | 须独立复核 + `UNITY_NA` 附议；`GATE_NOT_MET` 是评估事实，不阻止 DONE，也不授权追加 run 或调参 |

零样本摘要的功能门同为 `GATE_NOT_MET`（G3 报告率 0、严格成功 0、误报 none 30.1%、G5 none 76.0%；误报歧义 0 通过）；按合同零样本不做非劣判定。

**6.2.4 分组指标（prompt v2 零样本 → 微调 C2；百分比；配对差 = 同行微调 − 零样本，CI 只披露）。**

| 组 | 行 | 主指标 | 零样本 | 微调 | 配对差 pp [CI] | 误报 none | 误报歧义 | 无效 |
|---|---|---|---|---|---|---|---|---|
| G1 | 210 | Success | 51.4 | 76.7 | +25.2 [18.1, 31.9] | 29.5 → 13.3 | 0.0 → 2.9 | 10.0 → 0.0 |
| G2 | 49 | Success | 49.0 | 81.6 | +32.7 [16.3, 49.0] | 32.7 → 4.1 | 0.0 → 0.0 | 12.2 → 0.0 |
| G1∪G2 | 259 | Success | 51.0 | 77.6 | +26.6 [20.5, 32.8] | 30.1 → 11.6 | 0.0 → 2.3 | 10.4 → 0.0 |
| G3 | 48 | 报告率 / 严格成功 / macro F1 | 0.0 / 0.0 / 0.0 | 39.6 / 25.0 / 35.4 | 报告 +39.6 [25.0, 54.2]；严格 +25.0 [12.5, 37.5] | 12.5 → 0.0 | — | 16.7 → 0.0 |
| G4 | 86 | Success | 8.1 | 82.6 | +74.4 [64.0, 83.7] | 44.2 → 4.7 | 0.0 → 0.0 | 46.5 → 0.0 |
| G5 | 100 | none 率 | 76.0 | 79.0 | +3.0 [−6.0, 12.0] | — | 0.0 → 0.0 | 4.0 → 0.0 |
| G1t | 23 | Success | 39.1 | 65.2 | +26.1 [8.7, 43.5] | 39.1 → 13.0 | 0.0 → 0.0 | 8.7 → 0.0 |
| G2t | 23 | Success | 39.1 | 65.2 | +26.1 [8.7, 43.5] | 17.4 → 4.3 | 0.0 → 0.0 | 0.0 → 0.0 |
| G3t | 12 | 报告率 / 严格成功 / macro F1 | 0.0 / 0.0 / 0.0 | 41.7 / 0.0 / 23.3 | 报告 +41.7 [16.7, 66.7]；严格 +0.0 [0.0, 0.0] | 0.0 → 0.0 | — | 75.0 → 0.0 |
| G3′（诊断） | 50 | 报告率 / unique 行命中任一 M | 0.0 / 69.6（23 行） | 26.0 / 84.8（33 行） | 不入门 | 28.0 → 8.0 | — | 26.0 → 0.0 |

G3 的 TP/FP/FN：零样本 0/34/103 → 微调 36/31/67。G1t 与 G2t 同帧同层（提案 §6），Success 相同。t 子组不与 G1/G2/G3 混算。

**6.2.5 分层（微调；括号内为零样本；百分比，行数在前）。**

| 维度 | G1 Success | G2 Success | G3 严格成功 | G4 Success | G5 none 率 |
|---|---|---|---|---|---|
| S | 30：36.7（6.7） | 13：61.5（15.4） | 21：14.3（0.0） | 22：72.7（4.5） | — |
| M | 95：81.1（45.3） | 18：83.3（38.9） | 14：42.9（0.0） | 38：86.8（2.6） | — |
| L | 85：85.9（74.1） | 18：94.4（83.3） | 13：23.1（0.0） | 26：84.6（19.2） | — |
| NA | — | — | — | — | 100：79.0（76.0） |
| seen | 180：73.3（52.2） | 49：81.6（49.0） | 44：27.3（0.0） | 79：81.0（8.9） | — |
| unseen | 30：96.7（46.7） | — | 4：0.0（0.0） | 7：100.0（0.0） | — |

按类别（微调，括号内零样本）：

- G1：ambulance 12：83.3（83.3）、bus 29：86.2（69.0）、car 20：35.0（30.0）、container truck 39：79.5（69.2）、pickup truck 25：52.0（24.0）、
  police car 6：100.0（50.0）、suv 31：93.5（16.1）、taxi 29：93.1（69.0）、truck 19：68.4（57.9）。
- G2：car 5：40.0（60.0）、container truck 38：84.2（44.7）、suv 6：100.0（66.7）。
- G3 严格成功：bus 8：37.5、car 1：0.0、container truck 13：7.7、pickup truck 5：0.0、police car 4：50.0、suv 4：0.0、taxi 9：33.3、truck 4：75.0（零样本全为 0）。
- G4：ambulance 1：100.0（100.0）、bus 12：66.7（25.0）、car 7：42.9（0.0）、container truck 4：75.0（0.0）、pickup truck 9：77.8（0.0）、
  police car 5：100.0（20.0）、suv 20：95.0（0.0）、taxi 23：87.0（8.7）、truck 5：100.0（0.0）。
- G5 none 率：ambulance 12：83.3（100.0）、bus 12：91.7（100.0）、car 9：55.6（44.4）、container truck 12：100.0（75.0）、pickup truck 12：58.3（50.0）、
  police car 12：66.7（83.3）、suv 9：88.9（88.9）、taxi 10：100.0（90.0）、truck 12：66.7（50.0）。

分母小（unseen 30/4/7 行、G3 各类 ≤ 13 行），且 5 Hz 近重复帧多，行级比例只作描述；unseen 高于 seen 不作解释。

**6.2.6 失败分析（AC-11：`GATE_NOT_MET` 时必写；只描述，不追加 run、不调参）。**

1. **G3 歧义大多没有报告出来。** 48 行里 29 行输出 `unique`，其中 25 行的框与某个 gold 成员 IoU ≥ 0.5：模型挑了一个候选，没有报告歧义。
   报告了歧义的 19 行**全部恰好给 2 个候选**：gold 为 2 个的 14 行中严格成功 12 行，gold 为 3 个的 5 行全部少报一个。训练集歧义样本
   411 条里 401 条是 2 个候选、10 条是 3 个（只是观察，不作因果结论）。G3t 12 行：7 行 `unique`（都命中成员），5 行报告歧义，严格成功 0。
2. **误报 none 集中在贴边框。** G1∪G2 的 30 行误报 none 中，25 行的 gold 框贴画面边缘：贴边 134 行中漏报 25 行（18.7%），不贴边 125 行中
   漏报 5 行（4.0%）。gold 是 amodal 投影 AABB（框 `UNVERIFIED`），贴边对象在画面里可能只露出一部分；本报告不据此判断是 gold 错还是模型错。
3. **错框。** G1 有 15 行输出 `unique` 但 IoU < 0.5（其中 11 行 IoU < 0.1，框落在目标之外，逐行见 §6.2.7）；G2 7 行；G4 11 行。
4. **G5 误报。** 100 行中 21 行输出 `unique`：pickup truck 5、police car 4、car 4、truck 4、ambulance 2、bus 1、suv 1。与零样本逐行比，
   只有微调答对 12 行、只有零样本答对 9 行；police car、ambulance 的 none 率低于零样本。G5 none 率 79.0% 与门槛差 1 行。
5. **弱项。** car 类（G1 35.0%、G2 40.0%、G4 42.9%）和 S 层（G1 36.7%、G3 14.3%）最弱。

处置：按表 G / AC-11，`GATE_NOT_MET` 只记为评估事实，不在本信封内追加训练或重评、不调参；是否另立后续工作（例如歧义候选数、贴边对象）
由用户决定，本报告不提出新范围。

**6.2.7 失败案例（AC-13：每个判定组 min(10, 失败数) 条，按 `row_id` 升序，不挑选）。** 数据源 = eval-summary 的
`failure_cases`；框为 0–1000 坐标 `[x1,y1,x2,y2]`；「原图」是 `frame_id` 去掉前缀 `runtime/test-results/` 后的路径，包内副本路径见
摘要字段 `image`（相对 `outputs/eng-sft/P1-ENG-SFT-002/`）。G3′ 是诊断组，没有失败定义，不列。

**G1**（210 行，失败 49，列 10）

| row_id | 指令 | 层/类 | gold | 预测 | IoU | 原图（`frame_id` 去前缀） |
|---|---|---|---|---|---|---|
| `G1-02b8dd9fe39373e0` | the car | M/car | unique [492,3,609,115] | unique [878,0,983,60] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000000788.jpg` |
| `G1-06ef63081fe8de22` | the truck | S/truck | unique [262,0,316,28] | none | — | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001578.jpg` |
| `G1-0d653d35e1c785e0` | the bus | M/bus | unique [672,10,736,105] | ambiguous [661,13,733,107] [602,831,661,875] | — | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002679.jpg` |
| `G1-119a51b1bfcca9a2` | the truck | M/truck | unique [731,0,813,81] | none | — | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000002517.jpg` |
| `G1-12c700cd076872d4` | the car | L/car | unique [648,0,826,323] | none | — | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000000265.jpg` |
| `G1-1c5c86d5533a95b0` | the truck | S/truck | unique [130,0,197,32] | none | — | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000002328.jpg` |
| `G1-2d96da73b5cdd59b` | the pickup truck | L/pickup truck | unique [517,842,623,1000] | none | — | `p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000001513.jpg` |
| `G1-3540b95a5c2ba2a2` | the bus | S/bus | unique [792,0,869,39] | none | — | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002505.jpg` |
| `G1-3948ac2bac124479` | the container truck | S/container truck | unique [594,0,640,48] | none | — | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000002092.jpg` |
| `G1-3fe7d7ca3fa51802` | the suv | M/suv | unique [252,0,415,112] | unique [298,0,372,98] | 0.40 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001369.jpg` |

**G1t**（23 行，失败 8，列 8）

| row_id | 指令 | 层/类 | gold | 预测 | IoU | 原图（`frame_id` 去前缀） |
|---|---|---|---|---|---|---|
| `G1t-17d1a8342dd719a6` | the car | S/car | unique [0,216,1,347] | unique [0,239,127,575] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000000387.jpg` |
| `G1t-401a79b1b1eb2bbc` | the car | L/car | unique [432,403,567,577] | unique [473,427,526,554] | 0.29 | `p1-scene-004-scout-4-closed-exchange/frames/frame_0000000254.jpg` |
| `G1t-51db34f3023f8004` | the car | S/car | unique [604,955,747,1000] | unique [847,958,975,1000] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000001130.jpg` |
| `G1t-6b77e289933336b3` | the car | S/car | unique [0,261,18,400] | unique [588,70,612,126] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000001351.jpg` |
| `G1t-c18782cf9fcb3aa2` | the car | S/car | unique [0,995,67,1000] | none | — | `p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000000295.jpg` |
| `G1t-c8708a6b8cd7c7f6` | the car | S/car | unique [987,829,1000,1000] | unique [977,915,1000,1000] | 0.36 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000002409.jpg` |
| `G1t-f77c8a1dde576ec3` | the car | S/car | unique [988,270,1000,413] | none | — | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001149.jpg` |
| `G1t-fc235c45cb8c7fb0` | the car | S/car | unique [0,213,24,477] | none | — | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000000304.jpg` |

**G2**（49 行，失败 9，列 9）

| row_id | 指令 | 层/类 | gold | 预测 | IoU | 原图（`frame_id` 去前缀） |
|---|---|---|---|---|---|---|
| `G2-05e07d53740981ec` | the red container truck | S/container truck | unique [767,0,917,38] | unique [830,0,983,32] | 0.36 | `p1-scene-004-scout-4-closed-exchange/frames/frame_0000001173.jpg` |
| `G2-39117c48623d6ecd` | the red container truck | S/container truck | unique [767,0,917,38] | unique [820,0,983,40] | 0.43 | `p1-scene-004-scout-4-closed-exchange/frames/frame_0000001778.jpg` |
| `G2-4d9c9e559e74cbd8` | the red container truck | S/container truck | unique [966,0,1000,99] | unique [158,708,266,849] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000001951.jpg` |
| `G2-99e5d1275fac2c78` | the red container truck | L/container truck | unique [168,639,822,986] | none | — | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000000110.jpg` |
| `G2-b630ff74446ae3d7` | the green container truck | M/container truck | unique [919,73,1000,326] | none | — | `p1-scene-004-scout-4-closed-exchange/frames/frame_0000000146.jpg` |
| `G2-c00e960e0e1115cb` | the gray car | M/car | unique [266,2,341,180] | unique [80,805,217,895] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000002562.jpg` |
| `G2-e7996b0ccd008e97` | the gray car | S/car | unique [572,165,620,252] | unique [740,651,841,723] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002679.jpg` |
| `G2-e8e91dc6bf30bd2c` | the gray car | M/car | unique [365,0,432,89] | unique [403,618,594,765] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000000167.jpg` |
| `G2-fd983f2ae693dd10` | the red container truck | S/container truck | unique [767,0,917,38] | unique [830,0,983,32] | 0.36 | `p1-scene-004-scout-4-closed-exchange/frames/frame_0000000568.jpg` |

**G2t**（23 行，失败 8，列 8）

| row_id | 指令 | 层/类 | gold | 预测 | IoU | 原图（`frame_id` 去前缀） |
|---|---|---|---|---|---|---|
| `G2t-0f3c2319a750d322` | the red car | S/car | unique [988,270,1000,413] | unique [978,254,1000,363] | 0.38 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001149.jpg` |
| `G2t-1a15dcfda08b4eaa` | the red car | S/car | unique [0,216,1,347] | unique [0,259,126,576] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000000387.jpg` |
| `G2t-34bb74af37e133b6` | the red car | S/car | unique [604,955,747,1000] | unique [602,958,678,1000] | 0.48 | `p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000001130.jpg` |
| `G2t-675b4662b59a4627` | the red car | L/car | unique [432,403,567,577] | unique [473,427,526,554] | 0.29 | `p1-scene-004-scout-4-closed-exchange/frames/frame_0000000254.jpg` |
| `G2t-b304df7818955dc1` | the red car | S/car | unique [0,213,24,477] | unique [0,284,28,373] | 0.32 | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000000304.jpg` |
| `G2t-d1b1ac75299ad82a` | the red car | S/car | unique [0,261,18,400] | unique [643,718,670,762] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000001351.jpg` |
| `G2t-da8ba54db6a4ddbc` | the red car | S/car | unique [987,829,1000,1000] | unique [978,915,1000,1000] | 0.37 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000002409.jpg` |
| `G2t-e705f91ed2b235d4` | the red car | S/car | unique [0,995,67,1000] | none | — | `p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000000295.jpg` |

**G3**（48 行，失败 36，列 10）

| row_id | 指令 | 层/类 | gold | 预测 | TP/FP/FN | 原图（`frame_id` 去前缀） |
|---|---|---|---|---|---|---|
| `G3-0116591d5f30e396` | the taxi | S/taxi | ambiguous [537,76,607,127] [539,102,613,156] [758,257,875,329] | ambiguous [538,72,612,170] [754,248,878,344] | 2/0/1 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001788.jpg` |
| `G3-09ca830b126ee9d5` | the container truck | L/container truck | ambiguous [179,96,468,406] [854,215,1000,631] | unique [194,90,466,400] | 0/1/2 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000001146.jpg` |
| `G3-0eddbeba3ce1676d` | the police car | S/police car | ambiguous [210,107,296,160] [507,0,534,26] | unique [213,105,292,164] | 0/1/2 | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000002142.jpg` |
| `G3-16852b94c620e0b3` | the container truck | S/container truck | ambiguous [480,59,523,175] [653,22,759,97] | unique [653,15,775,99] | 0/1/2 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001730.jpg` |
| `G3-19674f1b27d58831` | the bus | L/bus | ambiguous [287,0,391,174] [615,770,791,1000] | unique [282,0,384,173] | 0/1/2 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000002201.jpg` |
| `G3-2387bb7376fdbc9b` | the container truck | S/container truck | ambiguous [699,80,871,276] [771,0,922,40] | unique [833,0,933,40] | 0/1/2 | `p1-scene-004-scout-4-closed-exchange/frames/frame_0000001779.jpg` |
| `G3-3f4b2cabf7c55f46` | the suv | M/suv | ambiguous [45,88,117,155] [773,916,1000,1000] | unique [48,89,120,161] | 0/1/2 | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000002325.jpg` |
| `G3-4113e4ae07394a70` | the container truck | L/container truck | ambiguous [0,493,255,852] [583,760,915,1000] | unique [582,752,898,1000] | 0/1/2 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002582.jpg` |
| `G3-49e42113164cef2f` | the bus | M/bus | ambiguous [193,914,512,1000] [748,78,878,154] [925,512,1000,657] | unique [749,78,878,164] | 0/1/3 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001968.jpg` |
| `G3-58ab3b73e1f10af1` | the container truck | S/container truck | ambiguous [696,78,867,275] [767,0,917,38] | unique [830,0,983,40] | 0/1/2 | `p1-scene-004-scout-4-closed-exchange/frames/frame_0000000568.jpg` |

**G3t**（12 行，失败 12，列 10）

| row_id | 指令 | 层/类 | gold | 预测 | TP/FP/FN | 原图（`frame_id` 去前缀） |
|---|---|---|---|---|---|---|
| `G3t-03cfb28e0ff1f31b` | the car | S/car | ambiguous [572,165,620,252] [742,651,857,728] | ambiguous [741,650,843,727] [621,77,662,137] | 1/1/1 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002680.jpg` |
| `G3t-1adcd769afb51c9b` | the car | S/car | ambiguous [537,506,621,572] [930,140,1000,221] | ambiguous [537,506,619,575] [677,124,762,181] | 1/1/1 | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000002268.jpg` |
| `G3t-323fdca535a2a7ae` | the car | M/car | ambiguous [365,0,432,89] [407,624,593,771] | unique [403,618,598,765] | 0/1/2 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000000170.jpg` |
| `G3t-3a63d180debac38c` | the car | S/car | ambiguous [739,104,826,154] [826,686,928,827] | ambiguous [337,130,421,215] [827,684,930,827] | 1/1/1 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000001975.jpg` |
| `G3t-4051ec289b6f6992` | the car | M/car | ambiguous [0,541,118,659] [657,703,733,860] | unique [657,701,735,861] | 0/1/2 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001716.jpg` |
| `G3t-6851b3af0101096e` | the car | M/car | ambiguous [186,190,290,284] [602,929,743,1000] [840,309,944,432] | unique [597,932,720,1000] | 0/1/3 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000001572.jpg` |
| `G3t-6aa17babc11d2e9b` | the car | M/car | ambiguous [444,597,629,752] [548,3,627,131] | unique [441,590,627,748] | 0/1/2 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000000119.jpg` |
| `G3t-7565e10efb3f4228` | the car | M/car | ambiguous [233,676,343,755] [806,198,888,291] | unique [234,675,344,754] | 0/1/2 | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000002455.jpg` |
| `G3t-83451f237401605d` | the car | M/car | ambiguous [15,162,123,248] [208,788,320,959] [599,267,696,379] | unique [200,784,320,971] | 0/1/3 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002145.jpg` |
| `G3t-9d72eb13f10cba33` | the car | M/car | ambiguous [358,113,438,190] [804,605,923,737] [935,204,1000,301] | ambiguous [358,111,438,191] [802,602,917,742] | 2/0/1 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000001784.jpg` |

**G4**（86 行，失败 15，列 10）

| row_id | 指令 | 层/类 | gold | 预测 | IoU | 原图（`frame_id` 去前缀） |
|---|---|---|---|---|---|---|
| `G4-030eec470ab4d94a` | the car to the viewer's right of the bus | L/car | unique [707,462,834,628] | unique [934,0,1000,43] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002325.jpg` |
| `G4-07bc6dac7c6f7edc` | the gray car to the viewer's right of the red container truck | M/car | unique [720,171,803,260] | unique [488,515,584,638] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000001965.jpg` |
| `G4-08f5f5443c106b1c` | the suv to the viewer's right of the container truck | S/suv | unique [450,7,480,60] | unique [196,251,298,331] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000001581.jpg` |
| `G4-092720ae949bf3d8` | the container truck to the viewer's left of the truck | M/container truck | unique [11,0,130,83] | unique [855,0,938,66] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001587.jpg` |
| `G4-25d657d23406ea0e` | the bus to the viewer's right of the taxi | L/bus | unique [632,512,789,879] | none | — | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001693.jpg` |
| `G4-3c338d17ae587c77` | the bus to the viewer's right of the ambulance | S/bus | unique [274,0,371,59] | none | — | `p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000001569.jpg` |
| `G4-5b5d6953b6782335` | the pickup truck to the viewer's right of the ambulance | S/pickup truck | unique [730,100,813,152] | unique [810,38,865,109] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001578.jpg` |
| `G4-5df1ba9f7e558606` | the bus to the viewer's right of the ambulance | S/bus | unique [264,31,361,93] | none | — | `p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000000556.jpg` |
| `G4-67676fc97e5aca82` | the taxi to the viewer's right of the truck | L/taxi | unique [781,509,957,695] | unique [730,178,837,305] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000002517.jpg` |
| `G4-8afa90a550054313` | the taxi to the viewer's right of the ambulance | S/taxi | unique [438,0,494,32] | unique [89,526,266,643] | 0.00 | `p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000001176.jpg` |

**G5**（100 行，失败 21，列 10）

| row_id | 指令 | 层/类 | gold | 预测 | IoU | 原图（`frame_id` 去前缀） |
|---|---|---|---|---|---|---|
| `G5-0002667231994bbd` | the police car | NA/police car | none | unique [964,53,1000,122] | — | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000001501.jpg` |
| `G5-000edbdee0ef4834` | the pickup truck | NA/pickup truck | none | unique [975,249,1000,323] | — | `runtime/frames.arm-b-trial-3-shared-residue-hold/frame_0000000962.jpg` |
| `G5-0020b9a2e1c6b880` | the ambulance | NA/ambulance | none | unique [0,13,103,88] | — | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000000400.jpg` |
| `G5-0023efd8e7972b31` | the pickup truck | NA/pickup truck | none | unique [743,151,878,314] | — | `p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000000987.jpg` |
| `G5-002965e368d1b0b6` | the police car | NA/police car | none | unique [0,88,98,210] | — | `p1-scene-004-scout-4-closed-exchange/frames/frame_0000001742.jpg` |
| `G5-002cc167ef837596` | the police car | NA/police car | none | unique [652,0,700,60] | — | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000000527.jpg` |
| `G5-00390517c4f42e40` | the car | NA/car | none | unique [733,299,1000,709] | — | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000000883.jpg` |
| `G5-0051e8f02d1b772d` | the truck | NA/truck | none | unique [227,412,405,742] | — | `p1-m3-body-001-arm-b-trial-2-post-run/frames/frame_0000000746.jpg` |
| `G5-005b5cd748c5a667` | the pickup truck | NA/pickup truck | none | unique [937,503,1000,643] | — | `p1-scene-004-scout-4-closed-exchange/frames/frame_0000001022.jpg` |
| `G5-0064e6e54c4476fc` | the police car | NA/police car | none | unique [558,315,680,423] | — | `p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000002634.jpg` |

**6.2.8 模型、数据来源与许可。** base = `Qwen/Qwen3-VL-2B-Instruct` revision `8964…4203`（Apache-2.0），云端下载一次；LoRA 只挂 LLM
28 层 × 7 投影 = 196 模块，ViT 0，可训练 17.4 M 参数。被选 adapter C2（69.8 MB）与全部预测只在本机 `outputs/eng-sft/`（git 忽略），
**不入仓库、不发布**；训练与评估数据是本仓库 Unity 仿真帧（S4 split），不发布；选层/评估 gold 从未上云。

**6.2.9 执行账目对信封（账本 2026-09-18 签发条目）。**

| 项 | 信封 | 实耗 | 结论 |
|---|---|---|---|
| 设备 | 云端单张 RTX 5090 | 1 × RTX 5090（32 GB，`env.json` `gpu_count` 1，驱动 580.159.03，torch 2.11.0+cu128，钉版本无漂移） | 符合 |
| 启动次数 | 零样本 ≤ 2、冒烟 ≤ 2、训练 ≤ 4、正式评估 ≤ 2，总 ≤ 8 | 1 / 1 / 3 / 1，总 6，全部 `succeeded`，无重试、无 micro-batch 折半 | 符合 |
| 冒烟门 | 末步 loss < 0.05 且 32/32 | 60 步，末步 loss 0.0133，32/32 | 通过 |
| GPU·h | ≤ 8 | 供应商计费 GPU·h 与控制台销毁时刻均无证据（账单不显示时长）。可给出的时间：各阶段计算时长合计 7,463.6 s（作业 A 6,683.6 s + 作业 B 780.0 s；B 在 22:32:45Z–22:45:49Z）；作业 B 收据保守计时 2.89 h；22:48:01Z 最后一次 `status` 2.925 h（销毁前快照，不是整个租期）；按 budget.json 保守起点 19:52:32Z 至用户 22:52:57Z 确认销毁，覆盖约 **3.01 h** | 符合（保守覆盖 3.01 h ≤ 8） |
| 租金 | ≤ 6 美元（含存储/流量） | **vast.ai 账单：实例 51480628 合计 $1.72**（GPU $1.67、Storage $0.03、Download 7.9 GB × $0.003/GB = $0.02、Upload 0.2 GB × $0.004/GB < $0.01）；运行器估算 $1.95 | 符合 |
| Unity 推理行 | ≤ 4,264 | 609 + 32 + 3 × 441 + 609 = 2,573 | 符合 |
| 下载 | base 权重一次 + pip 依赖 | 权重一次（约 40 s）+ 钉版本 pip；账单下行 7.9 GB | 符合 |
| 上传 | ≤ 0.3 GB，私有 | `upload/` 约 120 MB，经 scp 传到用户租用的实例，未公开 | 符合 |
| 云端磁盘 | ≤ 20 GB | **32 GB** | **偏差 D-1**，用户知情后回「继续」，已入账并经接受侧裁定为该实例单次例外（§6.1.4） |
| 本地目录 | `returned/` ≤ 512 MB（adapter ≤ 200 MB）、全目录 ≤ 0.9 GB | 211.3 MB（adapter 各 69.8 MB）、440 MB | 符合 |
| SynDrone / API / Play / 正式 ID / 发布 | 0 | 0 | 符合 |
| 实例 | 截止前销毁 | 用户 22:51:24Z 称实例「已经暂停」、22:52:57Z 确认「已经销毁」并附账单（顾问会话，辅助角色代录 `UT-P1-ENG-SFT-002-cloud-runs`）；本会话随后再次确认。均早于销毁截止 UTC 03:52:32Z；具体控制台操作时刻未知 | 符合 |

账单的流量单价（下行 $3/TB、上行 $4/TB）低于 budget-init 沿用的 16.0 / 17.334 美元/TB（偏差 D-2），当时的流量预留偏保守；账单上
storage 单列 $0.03，而 budget-init 把合计价 0.596 美元/时全部填在 GPU 项、存储项填 0（D-2）。账单行的日期列显示 Sep 17, 2026，与作业收据的
UTC 2026-09-18 不一致，本报告按收据时间记录，不解释该显示差异。

## 7. K3 停点：测试、候选范围与自证（C1@K3 退回修正后，2026-09-18；送 C2@K3）

**7.1 测试（COORD-009）。** 开发期只跑 focused：eng_sft 七个模块 **91/91**（K4 46 + K3 45；C1@K3 修正新增 4 条，见 §8）。
停点全套跑一次，输出 `docs/evidence/P1-ENG-SFT-002-tests.log`（末尾区块为对照）：**Ran 1247，errors=9，skipped=21；新增失败 0**。
基线 = K4 通过候选（复核文件 R2@K4 的 `passed_candidate`，运行时解析）提交内的同名日志：Ran 1202，errors=9，skipped=21。9 项 errors
两侧逐项同名同因，均为系统 python3 3.14.6 导入期缺依赖（numpy 1 + cv2 8），范围外不修。多出的 45 条 = `tests/test_eng_sft_train.py` 14 +
`tests/test_eng_sft_cloud.py` 31，全部通过、零 skip。C1 停点那次全套（Ran 1243）的原始输出由 git 历史保留。

**7.2 回传后的代码改动。** (a) C1 停点前：`verify_return.failure_cases()`（AC-13 失败案例；冻结 `evaluate.score_rows` 的逐行结果，判定组
G1/G1t/G2/G2t/G4/G3/G3t/G5，集合组以严格成功、其余以 Success/none 定失败，每组按 `row_id` 升序取 min(10, 失败数)），写进 eval-summary 的
`failure_cases`，断言在 `ReturnTests.test_end_to_end_select_job_b_and_summaries`。(b) C1@K3 退回后：续跑与 A→B 的包身份绑定、选优收据
新鲜度、自检数值下界三处失败路径（§8）。两批都不改冻结闭集、不改 K4 数据包、不重评分；修后用真实回传以不写文件方式重算三份摘要，
与已提交摘要逐字段相同。

**7.3 候选范围与历史实跑代码的区分。** 相对 K4 通过候选的完整 diff：实现者写入只有 A1（`tools/eng_sft/{train_lora,cloud_runner,verify_return}.py`、
`tools/requirements-eng-sft.txt`、`tests/test_eng_sft_{train,cloud}.py`、本报告）与 A2（三份摘要、`P1-ENG-SFT-002-tests.log`），以及按角色权限
更新的 `docs/current-status.md`；其余差异文件（账本、Unity 日志、`implementation-status.md`、设计、提案、复核文件）是接受/辅助/复核角色的提交。
冻结闭集 8 文件相对 K4 通过候选 diff 为 0 行；K4 数据包未改。
**云端实际运行的是历史代码束**：本地 `upload/code/` 与 `upload/code-manifest.json`、`receipts/bundle-receipt.json` 未重打，两次回传收据记录的代码清单 SHA
= 本地 bundle 收据（`verify_return verify` 核对），来源提交记在 `code-manifest.json`（运行时解析）。本批修改的 `cloud_runner.py` **没有打进任何代码束、
没有在云端运行**；历史代码束 10 个成员中 8 个仍与当前源码逐字节相同，`cloud_runner.py` 不同（本批修正），`code/tools/__init__.py` 为 bundle 生成的空文件
（AC-7 修订 2）。修正只约束将来的续跑/作业 B。本次 A/B 在历史代码下没有续跑：启动账 6 次均为各阶段首次启动且成功，无失败记录；按修后规则核对，
真实作业 A 与作业 B 收据的 6 个包身份字段逐一相等、无缺项，选优收据绑定当前作业 A（§8 C1-K3-1/2）。不 import `controller.*`，不改运行时文件，零 Unity/Play。

**7.4 §4.3.1 自证。**

1. **范围与接口已冻结**：AC-7…13 落实，§4 表逐条有证据指针，C1-K3-1…4 逐条回证见 §8；冻结闭集与 K4 数据包未改；AC-12 为签发日终态 `NOT_RUN`。
2. **相称的测试通过**：focused 91/91；停点全套 1247 / errors 9（与基线同名同因）/ 新增失败 0（7.1）；C1 退回的三处失败路径各有修前红、修后绿的具名测试（§8）。
3. **Unity**：本候选零 Unity 运行，纯离线训练与评估，不改运行时行为；申请 `UNITY_NA`，须复核角色在复核文件附议。
4. **状态板、候选 commit、未验证风险已更新**：状态板本批次同步；候选 commit = 本批次提交后的 HEAD（运行时解析，不手写）；风险见 7.6。

**7.5 给复核角色的范围（`R<n>@K3`）。** 相对 K4 通过候选的 A1 源码与测试（上列 6 个文件）；重点：`train_lora.py` 的配方/调度/掩码/
选优与冒烟判定对表 H 与 AC-10 修订 1…3；`cloud_runner.py` 的包校验、启动账、预算守卫与看门狗对 AC-7/AC-13 修订 1 与 K3-P1…3，以及本批
`package_identity` / `require_same_package` / `_prepare` 续跑与 A→B 分支、`_whole_number_between` 数值边界；`verify_return.py` 的回传绑定、
选优、选优收据新鲜度、摘要与 `failure_cases`。接受侧预复核关注：三处失败路径修复、历史证据与修后代码的版本区分（7.3）、D-2 既有流程偏差。
三份摘要可用 `verify_return summarise --job-a … --job-b …`（零 GPU，约 1 分钟，本地需有两个回传目录）复算，并用 AC-11 命令读判定。
GPU 部分（真实 `load_model`、PEFT 前反向、生成）只有云端这一次实跑，复核无法重跑。

**7.6 未验证项与已知限制。**

- 供应商计费 GPU·h 与控制台销毁时刻无证据；保守覆盖约 3.01 h（19:52:32Z 起至用户 22:52:57Z 确认销毁），费用以账单 $1.72 为准（§6.2.9）。
- D-2：租前未核实这台机器的流量报价，是已发生的流程偏差，只披露、不补证（§6.1.4）。D-1/D-3 已入账并经接受侧裁定为该实例的知情继续。
- 修后的 `cloud_runner.py` 没有在真实 GPU 上运行过；它只改变续跑/作业 B/自检参数的拒绝路径，由 FakeEngine 与纯参数测试覆盖。
- 选优只基于一次种子、441 行选层子集；正式评估每组一次 greedy，未做重复运行；行级 CI 在 5 Hz 近重复帧上只是描述性区间。
- 词表非劣的对照基线（prompt v2 零样本）有 103 行解析失败，+26.6 pp 不等于定位能力提升（§6.2.2 (b)）。
- gold 是 amodal 投影 AABB（`UNVERIFIED`）；贴边对象的漏报（§6.2.6 第 2 条）不判定是 gold 还是模型的问题。
- 作业过程快照与 loss 曲线（`logs/job-a-live-20260918T2134Z/`）是非证据的中间快照；逐步训练日志只在回传目录，按 SHA 绑定在 train-summary。
- F2/F3（K4 SCOPE_GAP）仍 OPEN，本候选不处理。

## 8. C1@K3 退回项的逐条回证（2026-09-18）

来源：提案「Contract conformance（核对表）」C1@K3 的 C1-K3-1…4。只落实既有合同，不新增 AC；修前红、修后绿的原始输出未入仓，
红/绿均为同一 focused 命令（下列 5 条测试一次运行），修前：3 条 FAIL + 1 条 ERROR（`KeyError: 'resumes'`）+ 自检用例 4 个子测试 FAIL；修后 5/5 OK。

| 编号 | 落实 | 具名测试（修前 → 修后） |
|---|---|---|
| C1-K3-1（AC-7） | `cloud_runner.package_identity()` 取全包校验的 6 个身份字段（上传/代码清单、冻结与预检收据、prompt 模板、词表 SHA）；`require_same_package()` 缺字段或不等即 `LaunchRefused`。`_prepare`：作业 B 在建目录前核对作业 A 收据记录的包身份；续跑时在任何写入前核对旧收据的包身份、`env.json` 环境与已装版本（JSON 往返同形比较），不再改写首跑的 `package`/`pins`/`env.json`，只追加一条 `resumes`。拒绝发生在跳过旧阶段、改旧收据、消费 A 的 adapter 之前，不计启动次数 | `JobTests.test_resume_with_changed_bundle_or_environment_is_refused_before_any_write`（生产路径：改受束源文件→提交→重打合法新代码束；另测环境变化；断言旧回传目录逐文件不变、启动账不变、不重训）FAIL → OK；`JobTests.test_job_b_refuses_job_a_from_another_bundle_before_creating_job`（断言不新建作业 B 目录、eval 计次 0）FAIL → OK；同包续跑成功路径 `JobTests.test_job_a_resume_skips_finished_stages_and_counts_retry` 追加断言（`resumes` 1 条、包身份不变）ERROR → OK |
| C1-K3-2（AC-10/11） | `verify_return.summarise` 读选优收据后要求其 `job_id` 与 `job_receipt_sha256` 等于当前作业 A 回传，否则 `RETURN_HASH_MISMATCH`，须在当前回传上重新 `select`；`select` 本身不改 | `ReturnTests.test_summarise_refuses_selection_not_bound_to_current_job_a`（A 部分完成→select→A 续跑完成→带回→摘要拒绝→重新 select→通过）FAIL → OK。真实回传：当前选优收据绑定当前作业 A（核对为真），按修后代码重算三份摘要与已提交逐字段相同 |
| C1-K3-3（AC-13 修订 1 / 5060 诊断信封） | `run_selfcheck` 在计次与任何模型调用前要求 `rows` ∈ [1, 4]、`steps` ∈ [1, 5]、`micro_batch` ≥ 1，且为真整数（不收 bool）；`TorchEngine` 构造时要求 `micro_batch` ≥ 1（作业 A/B 与自检同一入口，CLI 以「拒绝启动」退出码 2 结束）。不增加任何诊断额度 | `SelfcheckTests.test_selfcheck_rejects_out_of_range_values_before_counting`（rows −1/0/5、steps −1/0/6、micro_batch 0/−2、rows=True，及 `TorchEngine(micro_batch=0/−1)`；断言计次文件不存在、模型零调用）FAIL → OK。真实 5060 自检用的是合法值，其「非证据」身份不变 |
| C1-K3-4（AC-13） | §6.1.4 改为已入账与接受侧裁定；§6.2.9 与 §7.6 区分 A/B 阶段时间、作业 B 收据 2.89 h、22:48:01Z 最后一次 status 2.925 h、保守覆盖至用户确认销毁约 3.01 h、账单 $1.72；D-2 写成已发生的流程偏差，不称租前已核实 | 文档项，无测试 |

## 9. F6（CLASS_3）补丁应用记录（2026-09-19）

来源：`docs/reviews/P1-ENG-SFT-002.md` R1@K3 §3 F6（依据 `BC-13`，AC-13）。按状态板交接行由实现角色应用，逐字替换以下四处；
不改任何数字判据、哈希、ID、disposition，不重跑任何入口，不开新 C/R 轮：

1. 抬头段：「三项执行偏差待接受/辅助角色入账，接受侧已裁定（§6.1.4）」→「三项执行偏差已入账并经接受侧裁定（§6.1.4）」。
2. §4 表 AC-13 行末：「云端磁盘偏差 D-1 待入账」→「云端磁盘偏差 D-1 已入账并经接受侧裁定为该实例单次例外（§6.1.4）」。
3. §5「已知限制」首条：「41 项无 GPU 测试」→「45 项无 GPU 测试」。
4. §6.2.9 表「云端磁盘」行：「用户口头选择继续，待入账（§6.1.4）」→「用户知情后回「继续」，已入账并经接受侧裁定为该实例单次例外（§6.1.4）」。

抬头 Status 行保留 K3 停点候选提交时的措辞；工作项 `DONE` 的裁定在提案复判节与 `docs/implementation-status.md` 同名节，本文不改写。
