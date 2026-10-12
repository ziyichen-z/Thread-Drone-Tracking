# P1-ENG-LOOP-001 — 阶段 A 可访问机器实测报告

Owner: Implementation（Cursor）
Date: 2026-09-20
Status: STABLE_CANDIDATE_AT_K1K3；阶段 A 实测与运行时绑定修复齐备，交 Acceptance C1@K1K3，再交独立 Review；不声明 DONE，阶段 B 未授权。

## 1. 最终结果

| 交付 | 本批结果 | 证据 |
|---|---|---|
| 操作单 A/B | 已交；Mac T7、5060 用户指定 F 盘；含依赖、计数、回退和复现脚本 | `-operations.md` |
| Mac 合并 | 2 次尝试耗尽，无成功产物，回退 c2-adapter | `-merge-mac.log`、`-merge-mac-attempt2.log`、`-merge-mac.json` |
| 5060 合并等价（AC-9） | 第一次 CPU 合并成功；32 行比较中 2 行不等价，最终回退 c2-adapter；64 条原始输出完整 | `-merge-5060.json`、`-merge-equivalence.json` |
| Mac MPS 时延（AC-10） | 一轮 OK，3 预热 + 32 计时，失败 0，p95 8.756297875 s，B 档 | `-latency-mac.json` |
| 5060 HTTP 时延（AC-10） | 一轮 OK，3 预热 + 32 计时，失败 0，p95 5.429160667 s，A 档 | `-latency-5060.json`、`-http-memory-5060.json` |
| K 测量收据 | 决策 5060/http/c2-adapter，30/50/2，82≤120；源报告 SHA 绑定与逐字段复算通过。运行时绑定修复与真实服务正反例通过；独立验收仍待 C/R，见 §8 | `-k-receipt.json`、`-measurement-verification.json` |
| 两机 pip check（AC-12） | 均 No broken requirements found. | `-pip-check-mac.log`、`-pip-check-5060.log`；完整版本 `-environment-{mac,5060}.txt` |
| 聚焦测试与预览（AC-5/11） | 257 项 OK，0 skip，含 Pillow、Windows 导入兼容与 K 绑定回归 | `-tests-language-final.log` |
| 停点全套（AC-11） | 1504 项，0 failures、9 项既有 cv2 环境 ERROR、24 skip；新增 suite 失败 0。T7 exFAT 失败轮完整保留，见 §7 | `-tests.log`、`-tests-exfat-environment.log` |
| K 运行时身份缺口修复 | 修前反例失败、修后拒绝；13 项绑定测试通过；真实 5060 匹配收据可构造 IDLE、错误身份被拒，额外模型查询 0 | `-tests-k-binding-{before.log,log}`、`-k-binding-after.json`、`-live-binding-5060.json`、§8 |

本表中 `-xxx` 路径均为 `docs/evidence/P1-ENG-LOOP-001-xxx`。
本批没有 Unity、Play、正式 scenario/session/run ID、外部模型 API、训练或云端执行。

## 2. Mac 实测数字

平台：Mac M4 / 16 GiB，macOS 26.6.2 arm64，Python 3.12.13，torch 2.11.0、
transformers 5.17.0、peft 0.21.0；完整安装版本见环境文件。使用冻结 C2 adapter 与
原 base revision，哈希由训练摘要与下载 metadata 核对；本批不重跑 609 行评估。

| 项目 | 实测/计算 |
|---|---:|
| 模型形态 / 后端 | c2-adapter / local-hf / MPS |
| 预热（单列） / 计时样本 | 3 / 32 |
| p50 | 4.403572125 s |
| p95（升序第 31 个） | 8.756297875 s |
| max | 8.858217125 s |
| 查询失败 | 0 |
| 分档 / 保留窗资格 | B / true |
| capture_hz / retained_frame_count | 5 / 128 |
| K_ret / K_conf / K_pub | 46 / 50 / 2 |
| 预算核对 | 46 + 50 + 2 = 98 ≤ 128 − 8 = 120 |
| 进程峰值 RSS | 462,061,568 B |
| MPS 已分配内存采样峰值 | 4,696,117,248 B（约 4.37 GiB） |

边界是生产 `InferenceAdapter.predict_one` 调用到返回，含图像读取/编码/生成。
MPS 没有这里可用的峰值 API，20 ms 采样的最大分配量是**下界**，不称精确峰值；
RSS 不包括全部设备分配。时延、输出、finish_reason、token 数、逐行 ID、smoke SHA、
模型身份和环境均留在 JSON。预热不进 p50/p95/max。
资格只证明模型时延与保留窗预算相容，不证明追平、发布最终门或真实 Play 通过。
本机 K 数字只是候选宿主计算；最终两机决策选 5060，见 §6。

## 3. 两次合并与 T7 环境处理

1. 第一次 Mac/MPS 合并已经登记 1 次合并、1 次加载。日志停在权重加载完成，
   后续检查进程已不存在，没有合并产物或最终收据；原因未确认，不写成功。
2. 用户要求改用 T7 后，迁移模型/下载中间件，41 个文件逐个 SHA 相同后才删除
   内置盘副本；迁移新环境 site-packages，31,163 个正文文件逐个 SHA 相同。
   `outputs/eng-loop/P1-ENG-LOOP-001` 和 `.venv-language/lib/python3.12/site-packages`
   只在本地保留链接。未改既有两个环境。
3. 第二次 Mac/CPU 合并在 Transformers 导入阶段发生 UnicodeDecodeError：
   exFAT 上的 AppleDouble `._*.py` 被动态导入结构枚举成源码。失败收据保留，
   合并与加载照计；未产生第三次合并尝试。
4. 只清理本次 T7 专属目录中的 34,478 个 AppleDouble 旁文件；不删其他 T7 数据。
   后续复制用 `shutil.copyfile` 避免复制 resource fork，枚举排除 `._*`。真实导入
   与 MPS 预检随后通过。回退 C2 adapter 的 MPS 实测完成，不改变模型或钉版。

外盘根为 `/Volumes/T7/TetheredDroneTracking/P1-ENG-LOOP-001`：模型、依赖大目录、
HF/pip 缓存、临时夹具、查询中间件均在此。仓库保留代码、小型证据、执行脚本和必要
环境入口；`.gitignore` 排除本项输出，模型不入库。后续执行须保持 T7 挂载。
合并失败和回退归因交接受角色在提案决策记录消费，不自行签发范围裁定。

## 4. 测量路径修正与验证

本批执行前后发现并修正的实际问题均在既有 AC-8/9/10 范围内：

| 问题 | 修正与具名回归 |
|---|---|
| 真实 smoke 使用 sample_id，旧读取器只读 row_id | 兼容冻结 sample_id，校验图像 frame_sha256；`test_smoke_accepts_frozen_sample_ids_and_checks_source_bytes` |
| 合并模型的 weights_sha256 为空，且外盘旁文件可能冒充权重分片 | 对实际 safetensors 内容建立身份，排除隐藏旁文件；单文件直接 SHA、多片按有序名称/SHA 映射哈希；`test_merged_identity_tracks_the_actual_weight_bytes` |
| 等价 CLI 同时驻留两份模型 | 顺序运行两形态，释放第一份后加载第二份；保留 64 条原始输出，错误行按 query_id 对齐；`test_equivalence_releases_first_model_before_loading_second`、`test_equivalence_rejects_a_short_smoke_before_loading` |
| 缺测报告被当作 FAIL，可错误冻结 K | 明确 MEASUREMENT_INCOMPLETE、退出码 6，不生成 k_ret；`test_missing_host_report_cannot_freeze_a_receipt` |
| HTTP 测量缺省等待 12 s；本地返回超 60 s 仍可进有效分位数 | 测量等待缺省 60 s；本地返回超过 60 s 判 INVALID；`test_a_late_local_return_is_not_a_valid_latency_sample` |
| 原时延报告缺逐行输出与输入/收据来源绑定，MPS 内存只是结束时瞬值 | 保留样本与预热原始输出、smoke SHA/行序、K 源报告 SHA；MPS 20 ms 采样并注明下界，实际本轮逐行证据可复算 |

原始失败不覆盖：沙箱测试 241 项/9 errors 全为 loopback socket.bind 被禁止（
`-tests-language-sandbox.log`）；第一次 T7 环境测试 242 项/1 failure 是旁文件参与
权重哈希（`-tests-language-before-exfat-fix.log`）。修复后相同聚焦路径加 1 条
60 s 回归，243 项 OK，零 skip。没有用缺依赖 skip 冒充 AC-5。

边界：本地 GPU 查询无法强制中断时，测量器在调用返回后检查 60 s；本次所有计时
均低于 9 s，未触发该出口，不声称验证了卡死 GPU 的硬中断。5060 已真实顺序完成 64 行等价和 HTTP 35 行；服务端 CUDA 峰值与 PID/查询账本已核对。

## 5. 信封累计与执行偏差

| 计数 | Mac 已用 / 上限 | 5060 已用 / 上限 |
|---|---|---|
| 合并尝试 | 2 / 2（无成功产物） | 1 / 2（成功） |
| 模型加载/启动 | 3 / 6 | 6 / 6（合并 1、等价 2、失败服务启动 1、两次有效服务 2） |
| 查询行 | 35 / 70 | 134 / 134（等价 64 + 修前 HTTP 35 + 修后 HTTP 35） |
| base 下载 | 1 / 1 | 0，只读复用既有冻结缓存 |

计数见 `-execution-ledger.json`（Mac）与 `-execution-ledger-5060.json`；成功、失败、
预热均计。正式 scenario/session/run ID、Unity/Play、外部模型 API、训练、云端均为 0。
测量行标签与夹具标签不注册正式 ID。

5060 连接恢复后发现未挂载 T7；用户选择 F 盘，并进一步逐字授权约 73.6 MB 完整
测试包传输。授权均由辅助角色记入账本。F 盘根为
`F:\TetheredDroneTracking\P1-ENG-LOOP-001`，下载/环境/tmp/合并/中间件全在该根；
结束时 F 盘剩余约 587.5 GiB。Mac 大文件仍在 T7（约 793 GiB 空闲）。

环境安装外壳退出码非零，日志末尾却为安装成功；随后独立 pip check、版本/CUDA/资产
预检通过。第一次无模型预检因 Unix resource 导入失败，未扣模型或查询；生产 selector
增加 Windows 兼容入口（不改变冻结训练代码），不可用 RSS 抛 OSError，不伪造零内存。
修后 Windows 实机预检及具名测试均通过；Mac 分支不变，无需重复已有效 MPS 测量。

一次 Start-Process 服务启动随后进程消失，stdout/stderr 均空，未生成 preflight/启动
收据、无查询；原因未确认。为避免漏计，保守补扣一次启动，改为保持 SSH 的前台服务。
第二次成功，并记录独立 PID/启动/显存收据；有效测量结束后按任务命令行核验并停止
服务和虚拟环境启动器，最终该任务服务进程 0、8760 监听 0。原失败记录未覆盖。

修后 HTTP 元数据与查询身份守卫变化，按原信封用最后一次启动/35 查询重测；修前有效报告与收据以 `-before-binding-*` 保留，修后独立计算、不合并样本。5060 启动和查询已耗尽，剩余合并计数不抵扣启动额度，不再实测。失败/回退及修后 supersession 归因交接受角色消费，不自行签发范围或预算裁定。

## 6. 5060 等价、HTTP 时延与 K 收据

等价：同一 RTX 5060 Laptop GPU、CUDA、greedy、同顺序 32 行。先 merged 32 行，释放
模型并清 CUDA 缓存，再 adapter 32 行。全部输出成功解析；30 行通过、2 行不等价：
`unique_iou` 一行、`ambiguous_match` 一行，逐行 ID/原始输出/身份见等价 JSON。
这是否定合并等价的结果，不作精度改善或完整评估主张；依合同自动回退 c2-adapter。

| 项目 | 5060 实测/计算 |
|---|---:|
| 后端 / 最终形态 | Mac 客户端 → 5060 HTTP / c2-adapter |
| 传输 | direct HTTP over Tailscale，端点见 JSON |
| Python / torch | 3.13.0 / 2.11.0+cu128 |
| 预热 / 计时 | 修后 3 / 32，一轮；修前一轮另存 |
| p50 | 4.177721458 s |
| p95（升序第 31 个） | 5.429160667 s |
| max | 7.194030416 s |
| 每 token ms 的样本中位数 | 123.469654045 ms |
| 查询失败 | 0 |
| CUDA 峰值 allocated / reserved | 4,525,176,832 / 4,620,025,856 B |
| 分档 / 保留窗资格 | A / true |
| hz / R | 5 / 128 |
| K_ret / K_conf / K_pub | 30 / 50 / 2 |
| T_ret / T_conf / T_pub | 6.0 / 10 / 0.4 s |
| 资格核对 | 30 + 50 + 2 = 82 ≤ 128 − 8 = 120 |

边界为 Mac 的 predict_one 调用到返回，含图像读取、编码、上传、生成与轮询。
CUDA 峰值来自实际服务进程 API；Mac 客户端环境/内存另列，Windows RSS 不可用为 null。
启动收据与显存收据 PID 一致，最后 query_id 和修后 35 个 HTTP 扣额事件与客户端逐一
相符。测量器的 60 s 等待不等于正式运行时的 6.0 s 返回预算；max 高于 T_ret 如实保留，
不承诺每次查询都在 K 窗内返回，运行时仍应按时间门拒绝迟到结果。

Mac B、5060 A，合同决策为 **5060/http/c2-adapter**。K JSON 绑定模型、prompt、base、
hz/R、两份测量报告的路径和 SHA；旧 `-k-receipt-status.json` 只保留先前缺测历史。
`-verify-measurements.py` 无模型复算 32 行顺序、p50/p95/max、K、资格、等价逐行判定、
服务 PID/查询账本和源报告 SHA，输出 `-measurement-verification.json` 为 verified=true。

## 7. 测试报告与代码身份

- 聚焦：`.venv-language/bin/python -m unittest tests.test_language_bridge
  tests.test_language_selector tests.test_language_loop tests.test_language_k_binding`，257 项 OK、0 skip；小型 POSIX 临时夹具使用 /private/tmp。
- 全套首轮：T7 exFAT 的 AppleDouble/权限/链接语义导致大量旧夹具异常，1491 项、
  failures=40/errors=279/skipped=24。完整保留 `-tests-exfat-environment.log`，不能算通过。
- 同代码环境复测：`TMPDIR=/private/tmp python3 -m unittest discover -s tests`，
  修前 1491 项、failures=0/errors=9/skipped=24；修后停点全套再跑一次为 1504 项、failures=0/errors=9/skipped=24。9 个 ERROR 名称逐项与此前离线基线相同，
  均缺 cv2；新增 suite 失败 0。只有需 POSIX 语义的小型临时夹具用内置临时目录，
  下载、模型、依赖与大文件仍留 T7；临时夹具随测试清理。
- 系统解释器没有 Pillow 的 3 个语言预览/replay skip 不作满足证据，已由上面的
  有 Pillow 257 项零 skip 覆盖。其余 21 个 skip 沿用既有基线。
- 身份缺口的具名红绿：同一 `ReceiptBindingTests.test_changed_weights_refused_before_creating_session` 在修前真实源码快照失败（ConfigMismatch not raised），修后通过；13 项新测试覆盖来源哈希、宿主/backend/形态/prompt/base/device、HTTP端点、握手、服务切换与执行中身份变化。

5060 等价及修前实跑源清单为 `-transfer-manifest-5060.json`，修后为 `-transfer-manifest-5060-binding.json`，各启动收据对其 SHA 绑定；Mac 原清单为 `-measurement-manifest.json`。修前汇总 `-completion-manifest.json` 是历史快照；最终源码、基线与证据哈希见 `-candidate-manifest.json`。
入库证据统一 LF 换行，报告引用的 SHA 针对入库字节重算；原始 Windows 字节完整保留在 T7 的 evidence-return-5060.tar 与 evidence-return-binding-5060.tar，归档 SHA 见清单。本批 Windows 导入兼容与 K 身份/来源守卫均限本项代码；`Assets/`、`config/`、`tools/eng_sft/` 与既有
跟踪/协议实现零改动。服务端运行代码与所记录传输清单逐文件一致。

## 8. K 绑定修复、稳定候选与交接

先前零模型诊断证实“换权重身份仍可构造 IDLE”，原始 `-k-binding-diagnostic.json`
保留。用户指示继续剩余任务后，按已接受 AC-10 修订 1 补齐以下实现，未改变合同常数：

1. KReceipt 保留来源报告；真实后端启动前校验两份源文件 SHA、完整宿主结果、重新计算
   宿主决策，并比较所选报告的 backend/形态/模型身份/hz/R/p95；K_pub 不得覆盖冻结常数。
2. CLI 在加载前拒绝不同 backend/形态/HTTP 端点/本地设备；LanguageSession 再核实实际
   adapter 身份与 HTTP 端点，拒绝发生在创建会话目录、锁或桥文件前。
3. HTTP 通过真实 GET /status 绑定服务身份；每个回包携带并核对身份。POST 带期望身份，
   服务在写图与启动推理前比较；服务换模型时零推理拒绝，执行中变化则客户端拒收并进入
   既有 worker_stuck/backend_fatal 路径，不新增桥文件原因枚举。
4. 13 项具名回归全部通过；修前源码的同一回归确实转红。真实 5060 最后 35 次查询使用
   修后守卫并全部完成；最终 K 又在该真实服务上做正/反验证：匹配可构造 IDLE，错误权重
   触发 MODEL_IDENTITY_MISMATCH/fatal。只有两次 GET /status、零额外模型查询，见
   `-live-binding-5060.json`。结束后服务与启动器均停止，8760 零监听（`-cleanup-5060.json`）。

阶段 A 现已整理为 **STABLE_CANDIDATE_AT_K1K3**，四项自证和逐 AC 指针在
`P1-ENG-LOOP-001-K1K3-handoff.md`。进入 Acceptance C1@K1K3，再交独立 Review
R1@K1K3；实现者不签发独立复核。当前 C/R=0/0，AC-13…15 的 Play 证据仍属于未授权
阶段 B，不能由本次时延资格或夹具测试替代，不标工作项 DONE。

限制保持：本次是固定 32 行、两台既定机器/环境和同一路径的工程时延，p95 并不保证
每次返回均在 T_ret 内；max 原样保留。修前/修后各自报告，不把非受控两轮视作性能
提升或回归实验。MPS 内存为采样下界；Windows RSS 不可用但 CUDA 峰值真实。
真实 Play 的保留窗、追平、人工确认与告警链路仍须 C/R 后按独立 B 信封验证。
