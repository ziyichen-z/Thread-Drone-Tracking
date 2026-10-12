# P1-ENG-FRAME-001 — R7 后续全套预检（Implementation，2026-10-01）

Status: **READY_FOR_FULL_SUITE_SELF_PROOF**（用户本轮已确认数量调整；以下为原静态预检记录，当前交接见末节）。用户已允许一次全套的单列准备信封，但本机静态审计发现两条额外真实 re-anchor 构造路径超过 Nano≤2 / YOLO=0，按授权「环境中若出现新真实loader/越界条件则停止」未启动全套。没有改 skip、删用例、隐藏模型或更改既有实现。一次全套额度未消费；稳定候选四项自证仍未完整，不直接交 C3/R3 或放行 Play。

## 本次依据与实际检查

依据为 `docs/authorizations.md` 2026-10-01「用户允许开始三项补测前置准备」及 `docs/evidence/P1-ENG-FRAME-001-supplement-ops.md`「当前前置与下一角色」。只读使用现有仓库 `.venv-yoloe/bin/python`（3.12.13）；没有安装依赖。状态板开工为 1 条消耗性/1 条零消耗；发现越界后交接受处理零消耗，结束为 0 条消耗性/2 条零消耗。

机器证据：`docs/evidence/P1-ENG-FRAME-001-R7-full-preflight.json`。实际记录开工 HEAD/status、未改三个窄修路径与冻结文件 hash、Nano 模型身份、解释器和依赖存在性、额外构造路径与源码 hash。运行了只读依赖版本检查、严格配置解析及模型文件完整哈希校验；没有调用任何模型构造器、推理或 tracker。没有执行 unittest discover，也没有重跑已完成 focused 或真实复算。

- `ENG_DET_DATA_ROOT` 不存在，默认 `~/TetheredDroneTracking-full` 不存在，故原两条 optional det-assoc carrier 真 YOLO 用例的 `_ready()` 为不满足；不主动补齐环境。
- 现解释器 `cv2=5.0.0`、`torch=2.13.0`、`torchvision=0.28.0`、`ultralytics=8.4.104` **逐字匹配 re-anchor 四个版本门**；numpy/cv2/lap/ultralytics 可用，peft/transformers/timm 不存在，CUDA 不可用。缺 timm/transformers 不位于以下 Nano/YOLOE 构造之前，不能据此说 loader 不会进入。
- `load_reanchor_config()` 严格解析通过，纯配置路径不构造模型。实际 YOLOE 文件 27,803,986 B 与 DINOv2 权重 88,283,115 B 均存在，完整 sha 与冻结配置匹配，不能以缺文件推断它们会在 Nano 之前拒绝。
- 其他 Nano/CSRT adapter 用例为注入假后端或坏身份拒绝；re-anchor 单元预检 `_run()` 注入 fake 工厂，Scene004/Scene006 probe 显式传 stub proposer/embedder，local-HF 测试 patch `load_model`，det-assoc 单元/常驻回放用 scripted loader，HTTP用例是临时 loopback/mock 服务。这些不消耗正式模型/API/ID，不能据此遗漏下列真实 CLI 分支。

## 两条额外真实加载的具体路径

`tests/test_preflight_reanchor_env.py::SubprocessContractTest` 的：

1. `test_failure_leaves_stdout_empty_and_exits_nonzero`（当前约 513 行）；
2. `test_successful_stdout_is_exactly_one_json_document`（当前约 531 行）。

两者均在检查返回码或调用 `self.skipTest` **之前**，通过 `_run_tool()` 调用真实子进程 `.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json`。这里没有构造前的 skip 装饰器。

生产 `tools/preflight_reanchor_env.py::_construct` 顺序：严格配置/规格 → 四项版本门（当前都通过）→ `_default_nanotrack_factory` / `NanoTrackV2Tracker`（约 250–257 行）→ `_default_yoloe_factory` / `YoloeProposer`（约 276 行）→ `_default_dinov2_factory` / `DinoV2Embedder`（约 283 行）。`controller/reanchor_models.py::YoloeProposer` 先核现有匹配文件，再 `YOLOE(str(path))`；DINO则经源文件核验后本地 `pretrained=False` + `torch.load(..., map_location="cpu")`。即使 DINO后续因依赖拒绝，前面的额外 Nano/YOLOE 已经会发生。

| 单次原样全套的具名真实路径 | 当前审计后的最大实例/模型加载计数 | 与本次信封 |
|---|---:|---|
| 两条既有 Nano单测（见 R7-implementation「AC-24全套待执行的资源边界」） | Nano 2、权重文件4 | 已授权部分 |
| 上述两条 re-anchor CLI 单测 | 额外 Nano 2/权重文件4、YOLOE最多2、DINOv2最多2（后者取决于构造完成） | 未授权部分；无需等到实际加载才停止 |
| 合计具名可达路径 | **Nano最多4/权重文件8、YOLOE最多2、DINOv2最多2** | 超过 Nano2 / YOLO-VLM0 |
| 两条既有 CSRT真实测试 | CSRT最多2（无神经权重） | 原授权部分 |
| optional det-assoc carrier两条 | 当前默认环境skip；环境补齐时另有YOLO最多2 | 本次不改变环境，不启动 |

此计数是具名可达路径的静态上限，非实际消耗结果；原先只列 Nano2 的预估被本次审计纠正，不把原13失败/19skip断言回溯成现机器不会进入loader。生产层模型分支指向既有本地文件与CPU，DINO是否成功构造本次没有试跑；第三方库网络/自动安装的实际风险另列下节。任何新增授权须接受/用户明确，不能转用正式补测剩余加载1/run1/Play1或默认占用YOLO/DINO额度。

## 全 tests 树闭集审计与第三方库边界

对当前 **93 份 tests Python文件（含fixtures）** 做静态语法/调用引用核查，完整路径、字节sha与组合树hash在机器记录；没有通过discover导入/执行测试。并核生产模型加载端点与具名测试调用关系：

| 类别 | 当前全套真实模型闭集/排除理由 |
|---|---|
| Nano/CSRT | 上表6条具名测试入口；其他 `test_trackers` adapter为假工厂/假cv2或错误身份，track_loop/rate协议失败入口在构造前拒绝或patch create_tracker；body wiring只建规划器/parse CLI。benchmark两模块仅测percentile与_frame |
| YOLOE/DINO | 上述2条真实CLI；Scene004 scouting/Gate0/Scene006所有probe调用传stub proposer/embedder，ReanchorRuntime单元及rate-clock注入对象，不调用默认生产模型。`preflight`其他用例及stdout purity子进程注入fake工厂 |
| det-assoc YOLO / level2 Nano | 当前CarrierSelfTest两条受缺数据根_gate整体skip；ResidentCarrierReplay也不满足数据门且生产loader被cached fake替换。det-assoc其余测试显式scripted model/假工厂/假associator，resident level2为scripted tracker；不真实装载det-assoc YOLO或额外Nano |
| Qwen/SFT/HF/tokenizer | eng_sft_train纯函数，eng_sft_build/_cloud precheck替换_load_tokenizer，cloud jobs传FakeEngine；TorchEngine仅错误参数构造，不调用load/train；language local adapter测试注入对象/patch predict_rows和load_model，延迟测试ScriptedAdapter，replay frozen资产只读。不进入HuggingFace真实loader、VLM推理/训练或CUDA |
| 远程模型/API/实验launch | eng_fast/eng_det测试为解析、选择、评分和聚合，不调用train/evaluate真实backend或vlm_remote模型构造；rate study subprocess launch被mock，track experiment只构命令/print-only；web/selector HTTP使用临时loopback/mock服务，无外部付费API或正式采集 |

闭集条件为当前tests源码/fixture hash、现有环境门不变，原样完整discover一次；新增代码/数据根/环境安装会使该闭集失效。缺依赖的既有导入失败仍按实际全套结果归因，不补包、不改skip。尚未执行，无法证明具体失败/skip总数或实际CPU用时、峰值内存；也不能用静态穷举形式证明Python动态反序列化内所有间接行为。

**生产与已安装第三方库的顺序/联网核查：**

- `NanoTrackV2Tracker`先核两文件大小/hash及OpenCV契约，再本地`TrackerNano_create`，CPU；缺文件/hash不符在加载之前拒绝，无下载分支。
- YOLOE生产封装先核明确本地path的大小/hash；缺文件或不符在该YOLOE加载前拒绝，但此前Nano已经构造。已装Ultralytics的`Model._load → load_checkpoint → torch_safe_load → attempt_download_asset`对现有明确路径直接返回本地文件，无需下载；当前checkpoint zip的data.pkl只用`pickletools`检查GLOBAL（未反序列化），模块引用闭集为torch/ultralytics基础模型类，未见clip/mobileclip globals。**仍存在** `torch_safe_load` 捕获 `ModuleNotFoundError` 后 `check_requirements` 自动安装路径，AUTOINSTALL缺省true；无法仅凭完整文件hash保证不会走到该异常。不能授权网络/安装兜底。
- DINO封装依次核archive/extracted source/license/weights，再import本地backbones/data.transforms，`pretrained=False`明确避开源库的pretrained下载分支，再`torch.load(... map_location="cpu", weights_only=True)`/`model.eval().to("cpu")`。本次archive/extracted-source逐文件字节一致检查通过。缺归档/源/许可/权重会在DINO加载前失败，但此前Nano/YOLOE已经构造；缺任何后续依赖会直接失败，生产层没有安装兜底。
- 缺 `clip/mobileclip/timm/omegaconf/xformers/transformers/peft`。YOLOE文本特征`get_text_pe/build_text_model`未被本次构造链调用，不为它们设置额度；Ultralytics的text_model导入自身带clip自动安装与文本权重下载分支，任何意外进入都必须fail closed，不能说“现有pt完整”就豁免。DINO构造是否因缺依赖失败未试跑，不许以缺包理由允许前面的未授权加载。
- Ultralytics `utils.__init__` 的 `ONLINE=is_online()` 在默认导入时可能用 `socket.getaddrinfo(one.one.one.one / dns.google)`作DNS探测，除非`YOLO_OFFLINE`启用。本次版本只读检查已经导入该已安装包；未监测实际流量，**不能断言外部DNS为0**。没有调用模型/推理/付费API、下载安装或正式ID。此可预见导入副作用在本次审计披露，后续建议显式关闭离线探测，不把它默认为许可。

以上第三方库来源都从本机安装文件读取（不浏览/下载）：`ultralytics/engine/model.py`、`nn/tasks.py`、`utils/downloads.py`、`utils/checks.py`、`utils/__init__.py`、`nn/text_model.py`，DINO的本地`hub/backbones.py`。原测试模块抬头“heavy real models never built here”与其两条真实子进程路径冲突，仅记录事实，不修无关文档/测试。

## 一次性可执行新信封建议（尚未签发）

建议接受统一向用户明确而不是拆分追加：完整Python全套**1次**，仅现仓库环境/本地CPU/临时测试数据；**Nano实例最多4（两文件合计8次模型权重加载）、CSRT实例最多2、YOLOE实例最多2、DINOv2实例最多2**。CLIP/MobileCLIP/Qwen/其他VLM、det-assoc YOLO、其他模型新增均0；GPU、外部API、下载安装/远端、Unity/Play/正式scenario/session/run ID均0，正式补测余额完全不动。上述上限计尝试，不因失败回补重试。

还需明确仅为强制离线/禁止安装设置 `YOLO_OFFLINE=true`、`YOLO_AUTOINSTALL=false`、`HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`（当前未设置/未执行）。这不改变测试skip、不替换工厂、不隐藏模型；依赖无法满足则真实失败，日志保留。允许测试固有loopback HTTP/mock服务，禁止外部DNS/HTTP/下载；执行时保留环境和文件hash门，任何新的真实loader、自动下载/安装、GPU或外部服务路径出现就中止，不默许扩大闭集。普通第三方离线变量不能证明所有动态外部网络行为，发令前须确认已有执行环境的外网限制与子进程继承；不能在无法确认时称“无网络完整全套”。

该建议仅是实现者静态审计后的请求，不首签信封、也不预先授权下一次加载；接受/用户决定后才可执行并记录真实消耗。全套失败集与旧基线逐名比较仍待实际运行；全套1次未用，独立复核也尚未启动。

## K2 后续自证状态与下一动作

| 条件 / 关联AC | 当前状态与依据 |
|---|---|
| 1 范围与接口冻结 / AC-21 | 满足。原三路径窄修不变；完整候选 diff 由最近 `tools/frame_follow_replay.py` 变更 commit 解析，与旧通过候选比对。提案/CLI/指标/端点/参数不改 |
| 2 相称实现者测试 / AC-21、AC-24 | focused红→绿5/5、原run复算/138原件不变仍成立，见 R7-implementation 与 R7-recompute。**全套未运行**，未与旧13FAIL/ERROR做实际逐名比较，不能签AC-24/稳定候选自证完整 |
| 3 已知Unity问题 / AC-21、AC-23 | R7工具缺口已修；机身跟随/起停目检与完整按钮墙钟仍缺证，后续补测未运行。不以旧安全读数替代本次用户目检，不签Unity通过 |
| 4 候选/状态/风险 / AC-25、AC-26 | 本轮只补预检证据/状态，不改实现；角色/docs自检后提交推送。本候选尚无独立通过轮，当前只能交接受解决额外真实loader范围，不能按READY_FOR_REVIEW交未全自证候选 |

AC-25 范围围栏：`tools/frame_follow_replay.py`、`tests/test_frame_follow_replay.py` 与新fixture仍为原窄修，`controller/`、`Assets/`、`config/`、`ProjectSettings/`、`Packages/packages-lock.json` 相对最近通过候选零diff；本轮仅evidence/状态改动。AC-1…20/22/27…29 未触及部分沿原 `K2-handoff` / R2证据，不冒充本轮重跑；AC-19/20冻结选参/回放hash本次不变。Edit Mode不重跑：Unity/plant/配置代码零改动，旧284/284仅作未触及路径既有依据；本轮不给新离线工具独立签通过。

收工交接受处理新资源事实与用户决策，修订原先Nano2估计及补测前置；全套/四项自证/ C3@K2 / R3@K2依次完成后才可恢复补测发令。尚未开始全套，单列额外模型额度与补测余额均未消耗；独立复核子代理也不由实现自行派发。

## 接受侧收工代录与当前裁定（2026-10-01）

实现子代理已完成上述静态审计和机器记录，收工前被接受侧中断，未执行全套或新增实现改动；接受重读本报告全文、机器记录657行及两条真实子进程/生产构造链，按自己的写权限代录本批事实与状态并提交。接受自检用acceptance，不冒称实现子代理本批已提交或通过收工检查。本轮不是C3/独立R3，不消耗C退回或R轮数。

用户“可以开始做准备工作了”对应已签Nano≤2/CSRT≤2及YOLO/DINO0，本次审计发现的Nano4/YOLOE2/DINO2未被旧范围覆盖。已形成一次本地CPU全套、Nano≤4（权重8次）/YOLOE≤2/DINOv2≤2/CSRT≤2的具名调整选项待用户；其余模型、GPU/付费API/正式ID/Unity/下载/安装新增0，不挪补测余额。执行准备包含仅本轮进程YOLO_OFFLINE=true、YOLO_AUTOINSTALL=false、HF_HUB_OFFLINE=1、TRANSFORMERS_OFFLINE=1，限制外部联网/自动安装，保留loopback测试服务器与实际用例/既有skip逻辑；当前未启动该测试进程。库导入存在DNS初始化可能、当时无流量测量，不能追认外部DNS为0；未载模型/未发付费API/未下载安装与全套次数0可由本轮命令记录支持。

整体继续未放行；同源核对例外与一个独立复核子代理授权保留，仍须先全套/停点自证，再C3@K2、R3@K2及消费。新额度确认前下一接手为用户/接受；额外Play1/模型1/run1/480秒均未消费，旧原件、原合同、人眼条件、R1-3债不变。

## 本轮具名全套授权落实（2026-10-01，接受角色）

用户直接指示“继续吧，你来调用子进程”，在已列明一次全套Nano4/YOLOE2/DINOv2 2/CSRT2的上下文中确认继续；逐字入账 `docs/authorizations.md` 同日「用户确认一次完整测试的具名模型额度并调用原子代理」。替代本次全套原Nano2/YOLO-DINO0上限，其余边界与复核/仅R7同源许可不变。原额外loader范围阻塞已解除；全套当前仍0次，C3/R3未开、Play未放行，不追认历史DNS无流量。

原实现子代理执行原样完整discover一次，在受限网络环境内继承YOLO_OFFLINE=true、YOLO_AUTOINSTALL=false、HF_HUB_OFFLINE=1、TRANSFORMERS_OFFLINE=1；保留固有loopback/mock服务，不补包/补数据根、不隐藏模型/改skip，任何新增真实loader或越界即停。构造/加载尝试以具名上限记账、失败仍计，不自动重试。日志落文件、仅回显摘要；逐名比较原失败基线，按实际环境证据归因并补全四项停点自证，不改无关实现/合同或假报全套通过。提交推送后交接受，只读C3与新鲜独立R3仍待办理。正式补测额度不动。

## 本轮执行完成指针（Implementation，2026-10-01）

上述授权已执行一次原样全套；实际2064项/4败21错19跳，旧13保留、新增12条本地监听被受限环境拒绝，未提权重跑。当前完整候选、自证、资源未知与交接受见 `docs/evidence/P1-ENG-FRAME-001-R7-full-suite-handoff.md`；机器比较见同名full-suite-result.json。本文件前述未执行/阻断叙述为历史预检事实，不能作当前全套次数。
