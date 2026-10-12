# P1-ENG-LOOP-002 诊断冒烟操作步骤

> **仅诊断；不进证据链；不作任何门判定；未经核对/独立复核，不得用于正式运行。**
>
> 依据：同名提案「诊断冒烟授权落实（2026-10-07，Acceptance）」§1–5；授权 = `docs/authorizations.md` 同日「用户要求放宽粒度、先跑再查错」条。本页由实现角色写（轮次 `诊断操作步骤`），角色不代跑任何一步。轮次 `身份修复K1K3`（2026-10-07）只改附录 1 `gen` 的版本解析（同名提案「R4消费与诊断故障裁定」§3 AC-7 修订 5 / AC-16 修订 1，与 `tools/language_serve.py::parse_runtime_build` 同一语义），见 `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md`；本页其余步骤未改，修复未在真实板条件下验证，续试与否只按同名裁定 §6 由用户决定。正式运行只用 `docs/evidence/P1-ENG-LOOP-002-play-ops.md`（正式操作单）及其门与账；本页的诊断输入、读数与余量都不能转用到正式线。

> **OPS操作增量实现（2026-10-08，Implementation，零消耗；同名提案「OPS九题答复落实」§3 诊断页行）**：
> - **四次诊断已结束、旧的全部一次许可耗尽**；不得沿旧模板的 3 h / 5 Play / 3 启动或第四次的 1800 s 余量重开（余量已作废）。`P1-ENG-LOOP-002:9bac8fd0:SUB:3` 也已于 `20261008T155230Z` 用尽（历史，工具无条件拒续）。**现行唯一已签条目是 `P1-ENG-LOOP-002:DIAG:RETRY:1`（整批 1 次、剧本 P1 固定），只经下方「现行 DIAG:RETRY:1」的工具入口执行**，且须先满足该节全部执行前提（已签不等于放行）；正式与诊断目的须显式选择，诊断原件不转正式证据。
> - **新分工与入口**：机械核对、板服务前台生命周期与身份核对、收据输入、调度、停止/释放、日志与 runtime 归位由代理/脚本执行；本人 Play/停止、发令前对每条 ask/respecify 点「发送/跳过（不在画面）」、候选「确认序号/拒绝」都在本机操作网页 `tools/eng_loop2/operator_web.py`（由 `tools/eng_loop2/play_ops.py` 启动）。现行唯一可执行入口见下方「现行 DIAG:RETRY:1」；本页第 1–7 步的手工命令只作该入口的逐步对照与历史依据，不再手工执行。
> - 因此本页第 6.2 节的 T3 短命令（`L confirm/reject`、`preview` 切窗、经聊天转交确认）与附录 6 **已停用、不再是可执行入口**，仅保留为第一至四次的历史依据；`confirm-lost`/`dismiss` 不再执行，只记录 `SUSPECTED`/`LOST` 与原显式报告（OPS:SUSPECT:5）。
> - 诊断收尾摘要只用 `tools/eng_loop2/summarize_ops.py --mode diagnostic`（只读会话原流与操作原流；不调用正式评分、不判门）；四类诊断 STOP、`budget=None`、十旗标/300 s 就绪/版本/env 清理与有限输入均保持；新桌面工具、评分器与真值不进部署清单。

## 现行 DIAG:RETRY:1（同名提案「诊断绑定方案答复」BIND-1…6、AC-10 修订 9；轮次 `诊断绑定实现` 落实）

> **诊断；不进证据链；不作任何门判定。** 签发来源：`docs/authorizations.md` 2026-10-08「用户按推荐签发新全套 42979c14:SUB:1 与新诊断 DIAG:RETRY:1」条中的 `P1-ENG-LOOP-002:DIAG:RETRY:1`：独立一次、**整批 1 次、剧本 P1 固定**；维度按「SUB3核清与评分上限落实」§5 申请表原样，与工具 `DIAG_LIMITS` 逐项相同（主连接 ≤ 2、板服务启动 ≤ 1 / GGUF 加载 ≤ 1 / 故障重启 0、YOLO 加载 ≤ 1、本人 Play ≤ 1、会话 ≤ 1、measure ≤ 1、k-receipt ≤ 1、墙钟 ≤ 2700 s、Air 新增 ≤ 250,000,000 B、板新增 ≤ 200,000,000 B；表列 0 项全 0）。**已签不等于放行**：工具闭表中 status=signed 只表示资源已签，不是执行许可；本条目在下列前提齐备前不得执行。

**执行前提（逐项；缺一不执行）**：

1. **工具建根前机械核**（拒启时不建 Air 根、不写粗账、不消耗）：`--request-id` 逐字为 `P1-ENG-LOOP-002:DIAG:RETRY:1`（其他 id `request_id_unknown`；旧 `P1-ENG-LOOP-002:9bac8fd0:SUB:3` 一律 `request_exhausted`，代码级无条件拒续，不看 `outputs/` 里有无旧账）；`--playbook P1`（P2/P3 `playbook_not_signed`）；`outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/*/ops-diagnostic-ledger.json` 全部可读且身份明确（任一读不出、非法 JSON、非对象、缺 `request_id` 或其非字符串即 `diag_ledger_unreadable`，不猜是旧账而跳过）；无同 id 已用粗账（同 id 只有 `consumed` 为字面 `false` 视为未用；缺键/null/0/空串/其他非布尔/true 均 `request_consumed`）。身份可读的其他 id 粗账（含旧 SUB:3 已耗尽账）不占本 id 次数。
2. **工具建根后、首个受限动作前机械核**（拒启时只留下 `consumed=false` 的粗账，不消耗）：放行核对全部（执行检出 HEAD = 复核文件最新有效 `passed_candidate`、相对发布引用 PLAY_GOVERNING 与三份操作单空 diff、整树干净、无 `Assets/_Recovery`、全局消耗性 blocks 均已 release、文档检出位于发布引用且自检通过、账本 1.5 命中签发标题片段与完整 id）；**账本唯一条目绑定**：发布引用上的 `docs/authorizations.md` 按 `## ` 二级标题分条，标题含上述签发标题片段的恰一条（0 条 `ledger_entry_missing`、多条 `ledger_entry_ambiguous`），且该条正文含反引号包住的完整 id（标题在一条、id 在另一条，只有 `…:WINDOW` 等前缀扩展，未加反引号，均 `ledger_request_id_missing`；读取失败 `ledger_unreadable`）；**机读放行行**：同名提案在发布引用上含严格格式 `diag_release: <request_id> <40 位小写 sha>` 的行，其中 id 为完整本 id、sha 等于门核得到的最新有效 `passed_candidate`（提案读取失败 `diag_release_unreadable`；无本 id 合法行 `diag_release_missing`；有本 id 合法行但无一等于 passed `diag_release_mismatch`；大写/短 sha、他 id、前缀扩展、旧 `sub3_release:` 行与本页/合同中的格式示例一律不计，也不得把发布引用本身的 sha 当 passed）。该行**只由接受角色**在消费本绑定候选的有效独立通过之后，于同名提案新具名节从复核文件机读来源运行时解析、程序写入；实现/脚本不自签，一行匹配不替代其余门，也不转正式 G4。Air 本机工具/环境/det-assoc 资产/烟测 32 行齐。
3. **工具不能代核、执行时现核**：接受按最新账本核清新 id 未被撤回/否决且尚未消耗；现场核（Air↔板认证/HTTP、端口/残留、板身份/资源、前台中断/同会话释放、共享槽及短临时件归属/峰值映射），按原有限动作与已签整批墙钟记账，不在等待窗口时另行探测；**用户本人另给新在线窗口**（`P1-ENG-LOOP-002:DIAG:RETRY:1:WINDOW`，当前未给）。窗口不替代现场核与执行树门。

**唯一命令**（Air，本仓库根，Unity 已打开本仓库闭环场景、**不要先按 Play**；`<文档检出>` 为位于发布引用的另一检出；以下尖括号均为占位符）：

```bash
.venv-yoloe/bin/python -m tools.eng_loop2.play_ops --docwt <文档检出> --mode diagnostic diag \
  --request-id P1-ENG-LOOP-002:DIAG:RETRY:1 --playbook P1 --p2-object <red_car|B|C>
```

`--p2-object` 只保留既有冻结计划输入用途（冻结计划需要该参数），不许可改 P1 对象池、采样或指令，也不按诊断表现换剧本。

**拒启与用尽**：建根前拒启不建根、不写粗账；建根后的前提拒启只留下 `consumed=false` 粗账；两者都不消耗。首个受限动作（主连接尝试）之前粗账 `consumed` 置 true，此后成功、失败、中止都用尽本 id 的这一次，不续试，不靠删除粗账或缺账重开。旧粗账（含 `20261008T155230Z` 的旧 SUB:3 账）不删改、不改 id、不移根；旧手工无粗账目录不补造。工具的机器承诺只限当前粗账扫描域与旧 id 硬拒，操作者若删除新账，工具无法恢复耗用事实，故执行前由接受核新 id 尚未消耗、执行后粗账保留。共享槽与单写者约定不变，不引入跨进程并发执行许可。

**身份记录**：新粗账的 `request_id` 与 `entry_binding`（id、status、签发标题片段与账本标题行原文/行号、`release_key`、放行行行号/值、门核 `passed_candidate`/`rel`）、`NOTES.md` 页首注释、`ops-events.jsonl` 的 `diag_start`/`diag_entry_binding` 事件、`play/play-record.json` 都写本 id；实际 id 以这些 Air 原件为准（附录 3 板上横幅与拒绝文案中的 `SUB:3` 字样是历史标签，见附录 3 说明）。

**工具步骤、本人动作、STOP 与故障、原件与证据边界**：与下方历史 SUB:3 节的「工具按序做」表（步 1–8）及「本人要做的只有」「STOP 与故障」「原件与证据边界」各段相同（同一入口实现；剧本固定 P1，第 6 步只有 P1），本节不另复述；历史节中的签发来源、执行前提与唯一命令三段只属已耗尽的 SUB:3，不适用本条目。诊断原件不转正式证据。未在真实 OpenSSH/板/Unity 条件下验证（本机仅替身与 AF_UNIX）。

## 历史 SUB:3（原「现行 SUB:3」节，已耗尽；IR-OPS-5；同名提案「OPS验证额度落实与IR裁定」§2/§4；轮次 `OPS裁定落实与停点验证` 落实）

> **历史 / 已耗尽（轮次 `诊断绑定实现`，同名提案「诊断绑定方案答复」BIND-1/5）**：本节以下为原「现行 SUB:3」节原文，只作历史与工具步骤对照。`P1-ENG-LOOP-002:9bac8fd0:SUB:3` 已用尽，本节唯一命令现由工具在建根前以 `request_exhausted` 无条件拒续；旧放行键 `sub3_release` 与旧签发条目只属该 id，不适用新条目。现行入口见上节。

> **评分诊断合批修复（2026-10-08，Implementation，零消耗；同名提案「SUB3核清与评分上限落实」§2，AC-10 修订 8）**：`P1-ENG-LOOP-002:9bac8fd0:SUB:3` 已于 `20261008T155230Z` 用尽（主连接 d1 因控制套接字路径过长 rc 255，`DIAG_FAULT`）；下方唯一命令对该 request_id 仍按已消耗粗账拒启，本修复**不**使其可再次执行，新诊断须用户另签（同名提案同节 §5，未签 0）。工具现把每条诊断主连接的 ControlPath 放在**本次进程新建的短私有临时目录**（缺省父目录 = 本用户 `$TMPDIR`，`mkdtemp`，0700/本用户/非链接，d1、d2 各用独立名字，每批新建、不复用），占额前按编码后实际路径 + OpenSSH 17 字节临时后缀核本机 AF_UNIX 上限并实测 bind；建不成即 `DIAG_REFUSED control_path_*`（未消耗）。主连接创建、`-O check`、通道 `-S`、`-O exit` 都用同一路径；失效不直连/不重新认证/不重试，失败照原账计次。收尾在主连接全部退出之后释放：只删本次所建的空目录，残留套接字不删、不复用，记 UNKNOWN 与路径指针（粗账 `control_dir`、`ops-events.jsonl` 的 `diag_control_dir`/`diag_control_dir_release`、`ssh/d*.tsv` 的 `control_path` 行）；该目录内各项字节计入 Air 读数。不改全局 SSH 配置、仓库路径、诊断/正式输出根或放行判据。未在真实 OpenSSH/板条件下验证（本机仅 AF_UNIX bind 与替身）。

> **诊断；不进证据链；不作任何门判定。** 签发来源：`docs/authorizations.md`「用户按申请签发 OPS 验证额度 SUB:1/SUB:2/SUB:3…」条中的 `P1-ENG-LOOP-002:9bac8fd0:SUB:3`，**整批 1 次**（失败、拒启后的中止也用掉这一次）。旧模板的 3 h / 5 Play / 3 启动 / 1 故障重启、T3 短命令与附录 6 只是第一至四次的历史，不是本入口的额度或步骤。

**执行前提（工具机械核，缺一即 `DIAG_REFUSED`，此时未消耗任何受限维度）**：执行检出 HEAD = 复核文件最新有效 `passed_candidate`（新 Ops 范围已独立通过）、相对发布引用 PLAY_GOVERNING 空 diff、整树干净、无 `Assets/_Recovery`、三份操作单为通过版本、全局消耗性 blocks 均已 release、文档检出位于发布引用且自检通过；发布引用上的账本含本签发条目与完整 request_id；同名提案含接受写的机读放行行 `sub3_release: <passed_candidate 40 位 sha>`（IR-OPS-7 已裁定，同名提案「OPS基线与IR78裁定」§2：只由接受在消费 Ops 通过轮后于「OpsK1K2K3K4通过消费与SUB:3放行」节写入，值须等于门核得到的最新有效 `passed_candidate`；提案在发布引用上读取失败、缺行或值不匹配均 `DIAG_REFUSED`；合同里的格式示例不是放行行，脚本/实现不自签）；此前没有已消耗的同 request_id 诊断粗账；Air 本机工具/环境/det-assoc 资产/烟测 32 行齐。开跑前由**本人**选定唯一一个剧本 P1/P2/P3 并冻结（命令行参数，运行中不可换）。

**唯一命令**（Air，本仓库根，Unity 已打开本仓库闭环场景、**不要先按 Play**；`<文档检出>` 为位于发布引用的另一检出）：

```bash
.venv-yoloe/bin/python -m tools.eng_loop2.play_ops --docwt <文档检出> --mode diagnostic diag \
  --request-id P1-ENG-LOOP-002:9bac8fd0:SUB:3 --playbook <P1|P2|P3> --p2-object <red_car|B|C>
```

**工具按序做（每个受限动作之前先查额/先记占额；本页第 1–7 步与附录的对应关系）**：

| 步 | 工具动作 | 对应本页 | 上限/边界 |
|---|---|---|---|
| 1 | 新建 Air 根 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/<UTC>/`（已存在即拒）、写 `NOTES.md`（附录 0）、开始计时；放行核对；离线冻结所选剧本计划（`plan/ops-plan.json`，只文字/intent/Δ/时长）；Air 现场核 | 第 1、2 步（Air 部分） | 无 SSH；失败即拒启 |
| 2 | 附录 1 `resolve` 解析三文件期望；**占额**后开主连接 #1：附录 2 板上只读核（诊断根不存在、三文件 sha/版本、端口、残留）→ 附录 1 `gen` → 16 路径源码 tar 同步到新建板根 `/home/jetson/eng-loop2-diag/<同一 UTC>/code` 并逐文件核 sha → 附录 3/4 与 `serve-diag.env`/`expect-assets.json` 放入 `run/` → 关主连接 #1 | 第 2、3 步 | 主连接 ≤ 2（尝试即计）；不传模型/GGUF/mmproj/二进制/库/轮子；不碰正式 `/home/jetson/eng-loop2` 与 JET 根 |
| 3 | 主连接 #2：可见前台 `ssh -tt` 交互 bash 中运行 `bash --noprofile --norc <板根>/run/serve-diag.sh 1`（**只许编号 1**）；只认 `DIAG language-serve listening on http://<BOARD_TS>:18082` 行 | 第 4 步 T1 | 服务启动 1（含拒启）、故障重启 0、板 GGUF 加载 ≤ 1；不复用正式第 4 节启动块 |
| 4 | `/status` 恰一次 + 附录 5 判据（六键身份、部署摘要与 Air 重算一致、**无** `http_budget`；错接正式服务即故障） | 第 4 步 T2 | — |
| 5 | 写 `runtime/scenario_config.json` 覆盖；生产 `measure` ≤ 1 → 仅 rc 0 才 `k-receipt` ≤ 1；只写诊断根 `receipt/` | 第 5 步 | 不重测、不手造输入；非合格不进 Play |
| 6 | 起本机操作网页（页首显示「诊断；不进证据链；不作任何门判定」）→ 等**本人按 Play（仅此一次）** → `controller.language_loop run --diagnostic`（`diag-loop2-<HHMMSS>`，`--session-root`/`--diagnostics-root` 均在诊断根）→ 本人逐步「发送/跳过」与候选「确认序号/拒绝」→ 计划末 stop → **本人在 Unity 按停止** → 帧环与真值文件只移动到 `play/<SID>/` | 第 6 步（6.2 T3 停用，改网页） | Unity Play ≤ 1、YOLO 加载 ≤ 1；Air 根 ≤ 250 MB、板根 ≤ 200 MB（Play 期间两端轮询，达 90% 即 STOP1 收尾）；墙钟只剩收尾预留即 STOP1 |
| 7 | 收尾：停会话 → 本人停 Play → Ctrl-C 等服务退出 → **同一会话**按附录 7 核端口/本次进程释放 → 有限日志回传（不含缓存）→ 关主连接 #2 → 释放本次私有 ControlPath 目录（空才删；残留记 UNKNOWN、不删）→ 覆盖文件移入 `hold/overlay-diag.json`、开工前残留归位 → 结束计时 | 第 7 步 | 不杀未知进程；不能核清释放 → UNKNOWN + STOP3 交回 |
| 8 | 独立进程 `summarize_ops --mode diagnostic`（只读本次会话/操作原流；不评分、不读真值/四表）；本人可在网页点「通过/失败/受阻」（不判门） | 第 7 步第 5 条 | 等待受 45 min 总墙钟约束 |

**本人要做的只有**：开跑前选剧本；Unity 按 Play / 停止各一次；网页上每条指令看实时画面点「发送」或「跳过（不在画面）」、候选恰一个符合预登记描述点该序号否则「拒绝」；需要中止时网页「停止会话」或终端 Ctrl-C（= STOP4）；按钮起止时刻请自行可靠记录（工具记 UNKNOWN，不以出帧/网页时间冒充）。

**STOP 与故障**：STOP1 下一动作会越 §2 任一已签维度（主连接第 3 次、第 2 次启动/任何故障重启、第 2 次 Play、45 min 墙钟、250/200 MB）；STOP2 需下载/安装/编译/新设备或模型/库传板；STOP3 真值泄漏、身份/时间/控制安全旁路、失控或释放不能安全核清；STOP4 本人决定停。普通缺库/HTTP/解析/收据/启动错误/UNKNOWN 只记 `DIAG_FAULT` 与原 rc，不套正式 11 码、不改成 STOP；之后只做同一次内不依赖失败结果的安全收尾，不重启、不重测、不新开连接或 Play。工具非 0 退出时列出未执行阶段/步骤。Play 中一旦 STOP/故障/Ctrl-C（或到时），工具立即**不可逆封住**本会话的业务动作（计划不再推进；网页发送/跳过/确认/拒绝一律拒绝，只剩「停止会话」与状态读取），沿共享通道只发一次原 stop（结果未知不重发、不换 id），等会话退出后照常收尾；迟到的回执或 TERMINAL 只记录、不恢复任何动作（轮次 `OPSC6返工`，C6-1）。

**原件与证据边界**：Air 根内 `ops-diagnostic-ledger.json`（粗账：用途、request_id、起止 UTC/epoch、完整 elapsed、主连接尝试、服务启动/重启/GGUF 加载、Play/会话/YOLO 加载、两端字节读数与峰值及来源、STOP/故障/UNKNOWN/未执行、收尾释放）、`ops-events.jsonl`、`play/ops-web.jsonl`、`NOTES.md`、`raw/` 子进程原流、`board/` 板侧原流与日志 tar 同根保留；板根保留不删。诊断原件/报告/K 输入**不进** `docs/evidence/`、正式 assets/收据/ledger/四数字或 Unity 验收日志，不能写 G4 放行或 AC-14/15/16/18 已满足。

## 0. 先读这几条（第一至四次的历史手工流程；现行入口见上节）

- **执行人**：你本人，在 MacBook Air 上。Unity 由你按 Play/停止；板上服务由你经既有 `Host Jetson` SSH 在前台启动、Ctrl-C 停止。没有后台服务、没有自动重启。
- **只记三个粗维度**（第 1 步生成的手记表 `NOTES.md`）：总墙钟 ≤ 3 h（从第 1 步开始计，含 SSH、同步、冷加载、等待、Play 与收尾，暂停不清零）；Unity Play ≤ 5 次（进入 Play 就计 1 次，失败也计）；板服务启动 ≤ 3 次，其中故障重启 ≤ 1 次。HTTP 条数、字节、SSH 次数都不计。
- **一律为 0**：5060、云、外部 API、下载、`pip`/安装/编译、往板上传模型/二进制/库、新 scenario/run ID、改系统/SSH/沙箱设置。
- **三个终端**：T1 = 板服务（SSH 前台）；T2 = Air 准备与会话进程；T3 = 操作者指令。每个终端开头都先执行：

  ```bash
  cd ~/TetheredDroneTracking && exec bash --noprofile --norc
  ```

  （Air 默认是 zsh，本页命令按 bash 写。）T1/T3 开头再加载第 1 步生成的环境：`. "$(ls -d outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/2*/ | tail -n 1)diag.env"`
- **故障 ≠ STOP**：命令报错、HTTP/解析失败、收据或会话拒启都先记进手记表「现象」，不当场改源码或参数；能做的其他安全诊断照做，做不了就收尾（第 7 步）。真正的 STOP 只有第 7 步四类。
- 不要在诊断期间 `git pull`/切分支/改任何已跟踪文件：会话会核对 HEAD 与工作树干净。

## 1. 开工：建诊断目录、开始计时（T2）

```bash
set -o pipefail
D="$PWD/outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$D"/prep "$D"/board "$D"/receipt "$D"/sessions "$D"/segments "$D"/hold "$D"/play || echo "DIAG_FAULT mkdir"
date +%s > "$D/clock-start.epoch"; date -u +%FT%TZ > "$D/clock-start.utc"
{ printf 'export REPO=%q DIAG_D=%q PY=%q\n' "$PWD" "$D" "$PWD/.venv-yoloe/bin/python"
  printf 'export BOARD_TS=%q BOARD_DIAG=%q\n' "$(ssh -G Jetson | awk '/^hostname /{print $2}')" "/home/jetson/eng-loop2-diag/${D##*/}"
  cat <<'EOF'
echo "=== P1-ENG-LOOP-002 诊断；不进证据链；不作任何门判定 ==="
elapsed() { echo "已用 $(( ($(date +%s) - $(cat "$DIAG_D/clock-start.epoch")) / 60 )) / 180 分钟"; }
extract() { awk -v h="$1" 'index($0,h)==1{f=1;next} f&&/^```/{if(g)exit; g=1; next} g' "$REPO/docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md"; }
EOF
} > "$D/diag.env"
. "$D/diag.env"; head -n 2 "$DIAG_D/diag.env"
extract '### 附录 0 ' > "$DIAG_D/NOTES.md"; elapsed
```

`ssh -G` 只读本机 SSH 配置，不连接。之后每完成一步都可敲 `elapsed` 看已用时间；**建议到 150 分钟不再开新的 Play，留出收尾时间**。手记表用任意编辑器打开 `$DIAG_D/NOTES.md` 边做边填。

## 2. 现场核查清单（未核环境；先 Air 本机，再板上只读）

先打开 Unity（本仓库、平时做闭环 Play 的同一场景），**不要按 Play**，再在 T2 执行：

```bash
git status --porcelain --untracked-files=normal; echo "dirty_lines=$(git status --porcelain --untracked-files=normal | wc -l)"   # 必须是 0
git rev-parse HEAD | tee "$DIAG_D/prep/air-head.txt"
ssh -G Jetson | grep -E '^(hostname|user) '; for t in ssh tar shasum curl; do command -v "$t" >/dev/null || echo "DIAG_FAULT tool_missing $t"; done
"$PY" -c 'import numpy, cv2, lap, PIL, torch, ultralytics; print("ultralytics", ultralytics.__version__, "(det-assoc-v1 要 8.4.104) torch", torch.__version__, "mps", torch.backends.mps.is_available())'
"$PY" -I - <<'PY'
import hashlib, json
d = json.load(open("config/det-assoc-v1.models.json"))
for k in ("weights", "freeze"):
    p = d[k]["path"]
    try:
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        print(k, p, "OK" if h == d[k]["sha256"] else "DIAG_FAULT sha_mismatch")
    except OSError as e:
        print(k, p, "DIAG_FAULT", e)
PY
"$PY" -I -c 'import sys; sys.path.insert(0, "."); from tools.language_latency import read_smoke_rows; r = read_smoke_rows("outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl", "outputs/eng-sft/P1-ENG-SFT-002/upload"); print("SMOKE_OK", len(r))' || echo "DIAG_FAULT smoke_set"
for x in scenario_config.json frames m3_body_truth.jsonl; do [ -e "runtime/$x" ] && mv -n "runtime/$x" "$DIAG_D/hold/" && echo "held runtime/$x"; done   # 诊断前残留只移走，收尾时放回
elapsed
```

- 判读：`dirty_lines` 非 0（含 Unity 打开后改了已跟踪文件）→ 会话必拒启，记现象后收尾；缺 Python 包、权重/冻结文件不符或 smoke 不齐 → 记现象；**补齐要下载/安装/搬资产的，是第 7 步 STOP 2**。
- 端口与共享槽：不碰 46273；不清理任何未知进程；runtime 槽若被别的会话占着（会话报 `SESSION_SLOT_BUSY`），不删锁文件，记现象。

**板上三文件与端口（只读，T2）**——路径与期望 sha 从 `docs/evidence/P1-ENG-LOOP-002-precheck.md`「Mac mini只读补核原始读数与逐维度用量」R02 原流运行时解析（不手抄），在板上重算 sha、读构建号：

```bash
extract '### 附录 1 ' > "$DIAG_D/prep/diag-assets.py"
"$PY" -I -B "$DIAG_D/prep/diag-assets.py" resolve > "$DIAG_D/prep/assets-src.env"; tail -n 1 "$DIAG_D/prep/assets-src.env"   # 须为 # DIAG_RESOLVE_OK
set -a; . "$DIAG_D/prep/assets-src.env"; set +a
extract '### 附录 2 ' > "$DIAG_D/prep/board-check.body.sh"
{ printf 'W=%q M=%q B=%q R=%q\n' "$WEIGHTS" "$MMPROJ" "$LLAMA_BIN" "$BOARD_DIAG"; cat "$DIAG_D/prep/board-check.body.sh"; } > "$DIAG_D/prep/board-check.sh"
ssh Jetson 'bash -s' < "$DIAG_D/prep/board-check.sh" 2>&1 | tee "$DIAG_D/board/check.txt"
grep -E '^(DIAG_FAULT|BOARD_CHECK_DONE)' "$DIAG_D/board/check.txt"
"$PY" -I -B "$DIAG_D/prep/diag-assets.py" gen "$DIAG_D/board/check.txt" "$DIAG_D/board/expect-assets.json"   # 末行须 DIAG_ASSETS_OK
elapsed
```

- 有 `DIAG_FAULT`（三文件缺失/是链接/sha 不符、端口 18081/18082 被占、已有残留进程、诊断根已存在）或末行不是 `DIAG_ASSETS_OK` → 服务起不来，记现象后收尾。三文件要重新下载或传板才能解决的 → STOP 2。
- `expect-assets.json` 只是现有启动入口身份检查的**诊断输入**，不是 AC-16 资产证据，不复制进 `docs/evidence/`。
- 版本行（`身份修复K1K3`）：`--version` 原流里行首 `version:` 必须恰好一行——旧整数 `version: <整数> …` 取该整数，语义版本 `version: <语义版本> (build <整数>, commit <文本>)` 取括号内 build（本板原样输出得 `b0`，commit `unknown` 不作源码认证）；缺行、重复或冲突、缺 build、构建号超出 7 位或 `version_rc` 非 0 → `DIAG_FAULT version_unparsed_duplicate_or_nonzero`。原样版本行另记在 `expect-assets.json` 的 `runtime_version_line`，板上 `llama_preflight` 按同一语义自核。

## 3. 代码同步到独立诊断源码根（T2）

只同步 `config/p1-eng-loop-002-board-deploy.json` 所列 16 个纯源码/配置路径（清单含它自己），从 Air 当前干净检出，经既有 SSH 的 tar 流放到板上 `$BOARD_DIAG/code`；不传模型/权重/mmproj/二进制/库/轮子，不碰 `~/eng-jet/` 与正式根 `/home/jetson/eng-loop2`，不 `git` 拉网、不装包。

```bash
PATHS=$("$PY" -c 'import json; print("\n".join(json.load(open("config/p1-eng-loop-002-board-deploy.json"))["paths"]))'); echo "$PATHS" | wc -l   # 应为 16
COPYFILE_DISABLE=1 tar -cf "$DIAG_D/board/code.tar" $PATHS && shasum -a 256 $PATHS > "$DIAG_D/board/air.sha"
ssh Jetson "mkdir -p -m 700 /home/jetson/eng-loop2-diag && mkdir -m 700 '$BOARD_DIAG' '$BOARD_DIAG/code' '$BOARD_DIAG/logs' '$BOARD_DIAG/run' && tar -xf - -C '$BOARD_DIAG/code' && echo CODE_SYNC_OK" < "$DIAG_D/board/code.tar"
ssh Jetson "cd '$BOARD_DIAG/code' && sha256sum -- $(printf '%q ' $PATHS)" > "$DIAG_D/board/board.sha"
diff "$DIAG_D/board/air.sha" "$DIAG_D/board/board.sha" && echo CODE_SHA_MATCH
"$PY" -m tools.eng_loop2.deploy_digest --root . > "$DIAG_D/board/air-deploy-digest.json"; grep serve_code_sha256 "$DIAG_D/board/air-deploy-digest.json"
# 启动块与诊断输入放到 $BOARD_DIAG/run（诊断根内，不进 code/，不是 tools/ 入口）
extract '### 附录 3 ' > "$DIAG_D/board/serve-diag.sh"; extract '### 附录 4 ' > "$DIAG_D/board/serve-diag.py"
for k in BOARD_DIAG WEIGHTS MMPROJ LLAMA_BIN BOARD_TS; do [ -n "${!k:-}" ] || echo "DIAG_FAULT missing_input $k"; done   # 有任一行 → 记现象后收尾
printf 'export BOARD_DIAG=%q WEIGHTS=%q MMPROJ=%q DIAG_LLAMA_BIN=%q BOARD_TS=%q\n' "$BOARD_DIAG" "$WEIGHTS" "$MMPROJ" "$LLAMA_BIN" "$BOARD_TS" > "$DIAG_D/board/serve-diag.env"
COPYFILE_DISABLE=1 tar -cf - -C "$DIAG_D/board" expect-assets.json serve-diag.env serve-diag.sh serve-diag.py | ssh Jetson "tar -xf - -C '$BOARD_DIAG/run' && echo RUN_FILES_OK"
elapsed
```

没有 `CODE_SYNC_OK`、`CODE_SHA_MATCH`、`RUN_FILES_OK` 任一，或出现 `DIAG_FAULT missing_input` → 记现象后收尾（若是要装工具才能传，STOP 2）。`serve-diag.env` 里 llama 二进制路径的值仍是第 2 步 `resolve` 解析出的 `LLAMA_BIN`，但写成独立名 `DIAG_LLAMA_BIN`：附录 3 会清掉所有继承的 `LLAMA_*` 等覆盖变量，用诊断名传递才不会被一并清掉（`诊断页修复交付`，DIAG-ENV-2）。GNU tar 对 macOS 扩展头的 `Ignoring unknown extended header` 警告可忽略。

## 4. 起板服务（T1 前台）与身份核对（T2）

T1（加载环境后）：

```bash
ssh -t Jetson "bash --noprofile --norc '$BOARD_DIAG/run/serve-diag.sh' 1"     # 第 2、3 次启动把末尾 1 改成 2、3
```

- 启动脚本（附录 3）先载入 `serve-diag.env`，查端口/残留、清掉会影响 llama 的继承环境变量（`LLAMA_*`/`GGML_*`/`MTMD_*`/`HF_*`/`HUGGINGFACE_*`/`*_proxy`），再核五项诊断输入 `BOARD_DIAG`、`WEIGHTS`、`MMPROJ`、`DIAG_LLAMA_BIN`、`BOARD_TS` 均非空（附录 4 使用前再核一次）：载入失败或缺项 → 打印 `DIAG_FAULT …`、非零退出，停在生产 `llama_preflight` 与子进程创建之前（未加载模型，但照样占这次启动编号）；之后以 `budget=None` 运行一次性 Python 启动块（附录 4）：复用现有 `llama_preflight`（三文件 sha、构建号、量化、部署闭集摘要，不符即拒启、不加载）、`llama_server_command`（十项资源旗标原样）、`_wait_llama_ready(..., budget=None)`（300 s / 0.25 s 原样）、`SingleFlightRuntime`、`build_server(..., budget=None, long_poll=True)`；不调用 `_main_llama`，不建 `HttpBudgetLedger`，不用 `--http-ledger`/`--non-inference-reserve`/`--non-inference-limit`/`--inference-limit`（本路径不适用，不是 0 上限）。
- 看到 `DIAG language-serve listening on …` 才算就绪（冷加载可能要几分钟）。**每运行一次脚本就占一个启动编号（含拒启），手记表里记编号、起止时刻与 `serve_rc`**；上一次异常退出（rc 3/4/5 或其他非 0，不含你按 Ctrl-C 的 0）之后再起就是「故障重启」，至多 1 次，且只在上次进程已退出、端口已释放后。
- 停止：T1 里按 Ctrl-C，等出现 `serve_rc=` 行。别关掉终端窗口代替 Ctrl-C。

T2（服务就绪后）：

```bash
curl -s --noproxy '*' --max-time 5 "http://$BOARD_TS:18082/status" > "$DIAG_D/board/status-1.json"; echo "curl_rc=$?"
extract '### 附录 5 ' > "$DIAG_D/prep/status-check.py"; "$PY" -I -B "$DIAG_D/prep/status-check.py" "$DIAG_D/board/status-1.json"   # 末行须 DIAG_STATUS_OK
```

`DIAG_STATUS_OK` 表示：六键 llama 身份齐、板上 `serve_code_sha256` 与 Air 重算一致、回包**没有** `http_budget`（确认连的是 budget=None 诊断服务，不是守正式账的服务）。不符 → 记现象；身份/部署不一致无法在本页修，收尾。

## 5. 诊断收据输入（T2；只服务现有入口的身份/时效检查）

会话入口必须有 K 收据，所以用现有生产命令在诊断目录里生成一份**诊断输入**（不是 AC-15 收据、不进证据、不判门）。先写场景覆盖文件（Unity 与会话都读它），再测量、出收据：

```bash
"$PY" -c "import json;d=json.load(open('config/scenario.untethered.json'));d['sensor']['retained_frame_count']=1500;open('runtime/scenario_config.json','w').write(json.dumps(d,indent=2)+'\n')"
shasum -a 256 runtime/scenario_config.json | tee "$DIAG_D/prep/overlay.sha"
"$PY" -m tools.language_latency measure --host jetson --backend http --server-url "http://$BOARD_TS:18082" \
  --model-form c2-merged --smoke outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl \
  --package-root outputs/eng-sft/P1-ENG-SFT-002/upload --runtime runtime \
  --out "$DIAG_D/receipt/jetson-report.json" > "$DIAG_D/receipt/measure.stdout" 2> "$DIAG_D/receipt/measure.stderr"
echo "measure_rc=$?"; cat "$DIAG_D/receipt/measure.stdout"; elapsed
```

只有 `measure_rc=0` 才执行下一条（不要用 `;` 串在一起）：

```bash
"$PY" -m tools.language_latency k-receipt --single-host jetson --report "$DIAG_D/receipt/jetson-report.json" \
  --runtime runtime --out "$DIAG_D/receipt/jetson-k-receipt.json" > "$DIAG_D/receipt/k-receipt.stdout" 2> "$DIAG_D/receipt/k-receipt.stderr"
echo "k_receipt_rc=$?"
```

- `measure` 是单轮 3 预热 + 32 计时、首个失败即停（现有代码行为，不改）。非 0：看 `measure.stderr` 与报告里第一个失败原因，记现象。若是板服务已退出（T1 出现 `serve_rc=4/5`），可用那 1 次故障重启后照原命令再测一次；同一现象再出现就别再试，收尾。
- `k_receipt_rc` 非 0（6 = 报告不全/身份不符，8 = 不满足 K 资格式）→ 会话无法启动，记现象后收尾。不改参数、不换样本、不拿诊断数字去调任何东西。

## 6. 每次 Play（≤ 5 次）

**6.1 进 Play、起会话（T2）**：Unity 里按 Play，手记表记「第 n/5 次、进入时刻」。等几秒、Unity 开始出帧后：

```bash
F0=$("$PY" -c 'import json; print(json.load(open("runtime/frames/latest.json"))["frame_id"])'); T_SESS=$("$PY" -c "print(round(min(290, (1490 - $F0) / 5), 1))"); echo "f0=$F0 T_sess=$T_SESS"
SID="diag-loop2-$(date -u +%H%M%S)"; echo "$SID" > "$DIAG_D/play/current-sid"
"$PY" -m controller.language_loop run --diagnostic --session-id "$SID" \
  --session-root "$DIAG_D/sessions" --diagnostics-root "$DIAG_D/segments" \
  --runtime runtime --allow-shared-runtime --backend http --server-url "http://$BOARD_TS:18082" \
  --model-form c2-merged --k-receipt "$DIAG_D/receipt/jetson-k-receipt.json" \
  --tracker det-assoc-v1 --resident --condition follow --ground-plane-y-m 0.2 \
  --body-policy standoff --body-planner-config config/p1-eng-frame-001-body.json \
  --body-scenario-config runtime/scenario_config.json --scenario-id deterministic-loop-untethered \
  --planned-duration-s "$T_SESS" 2>&1 | tee "$DIAG_D/play/$SID.session.log"
```

- `--diagnostic`、`--session-root`、`--diagnostics-root` 三项缺一不可：`diag-` 前缀只是进程/锁/目录的诊断标签，不是新 ID；会话目录与段日志都落在诊断目录，不写 `runtime/runs/`。场景标识沿用既有的 `deterministic-loop-untethered`。
- `T_sess` ≤ 0（Play 开太久了）→ 先在 Unity 停止 Play（这一次照计），下次进 Play 后马上起会话。
- 启动即报 `CONFIG_MISMATCH`/`SESSION_SLOT_BUSY` → 记原文，在 Unity 停止 Play，按 6.4 归位；能判明原因又不用改代码/资产的才再试下一次 Play。

**6.2 操作者指令（T3）**（**已停用**：见页首 OPS 增量；以下仅为第一至四次的历史依据，不再执行）：每次新 Play 起会话后，在 T3 重新加载一次：

```bash
extract '### 附录 6 ' > "$DIAG_D/prep/ops.sh"; . "$DIAG_D/prep/ops.sh"
```

之后用短命令：`st` 看状态与最近结果；`preview` 打开候选预览图；`L <动作> …` 发指令。建议顺序（每条前先在 Unity 画面里确认意图对象在画面内，不在就不发，记 `SKIPPED_NOT_IN_VIEW`）：

| 目的 | 命令 | 目检要点（记进手记表） |
|---|---|---|
| 语言指定 | `L ask "the red car"`，然后反复 `st` 直到 `last_result` 出现 designate 结果 | 多久出结果；三态是 unique / ambiguous / none 哪个 |
| 预览/确认 | `preview` 看图；恰一个候选是你要的 → `L confirm <序号> --token "$(designate_token)"`；零个或多个相符 → `L reject --token "$(designate_token)"` | 框是否落在对的车上；无预览图（`preview_path` 空）记现象且不 confirm |
| 跟随 | 确认后看 Unity ≥ 20 s，期间 `st` | 状态是否到 `TRACKING`；无人机是否转向、保持目标在画面内 |
| 换目标 | `L ask "the taxi"`（或先 `L release --token "$(pointer_token)"` 再 ask），确认同上 | 是否切到新目标、旧目标是否释放 |
| 歧义报告 | `L ask "the car"` | 是否给出多个候选而不是乱选一个；按上面规则 reject 或 confirm |
| 丢失报告 | 跟随中若 `st` 显示 `SUSPECTED`：目标确实丢了/跟错 → `L confirm-lost --token "$(suspect_token)"`；其实还在 → `L dismiss --token "$(suspect_token)"` | 系统是否主动报出可疑/丢失，而不是悄悄跟错；报得对不对 |
| 结束本次 | `L stop` | 会话进程（T2）退出时打印的结局 |

- 选候选只凭实时画面与预览图，不看任何真值文件或评分输出（红线，见第 7 步 STOP 3）。车辆描述与「两辆 SUV 时 the suv 只能 reject」的已知风险见正式操作单第 7–8 节，照用不改。
- 指令文法受限：沿用正式操作单用过的 `the suv` / `the taxi` / `the red car` / `the car`；报 `instruction_unsupported` 记现象，不即兴换说法反复试。
- 回执不对（`REQUEST_INVALID…`、`token_mismatch` 等）照记原文；`backend_fatal`、超时、拒收都是**诊断现象**，不是门判定。

**6.3 结束本次 Play**：`L stop` 后（或会话自己到时/出错结束后），在 Unity 按停止，手记表记「停止时刻、会话结局（T2 末尾的 TERMINAL 原因）」。

**6.4 归位（T2，每次 Play 后）**：把本次帧环与 Unity 真值文件移进诊断目录（只移动不删除；Unity 下次 Play 会自己重建 `runtime/frames`）：

```bash
SID=$(cat "$DIAG_D/play/current-sid"); mkdir -p "$DIAG_D/play/$SID"
for x in frames m3_body_truth.jsonl; do [ -e "runtime/$x" ] && mv -n "runtime/$x" "$DIAG_D/play/$SID/"; done
du -sh "$DIAG_D/play/$SID"; elapsed
```

还要再 Play 就回 6.1（`runtime/scenario_config.json` 保留不动）；Play 已 5 次、时间不够或已无可做的事 → 第 7 步收尾。

## 7. STOP（只有四类）与收尾

| 类 | 何时 | 怎么做 |
|---|---|---|
| 1 越出粗维度 | 下一步会超过总 3 h、第 6 次 Play、第 4 次启动或第 2 次故障重启，或要动用任何「一律为 0」项 | 不再开始新动作，直接收尾；剩余额度不转给正式线 |
| 2 需要下载/安装/新设备 | 缺件只能靠下载、安装、编译、往板上传模型/二进制/库或新设备解决 | 停在该动作之前，手记表写清缺件名、在哪台机器、打算怎么补；收尾后交回，由 supervisor 按同名提案 `P1-ENG-LOOP-002:DIAG:ENV:1` 条件题原样转呈你决定，不当场补 |
| 3 安全/红线 | 真值进入决策（例如照着真值文件选候选）、身份/帧时间语义或控制安全被绕过、无人机行为失控、板上端口/进程冲突无法安全解除 | 立即停相关执行（`L stop`、Unity 停止、T1 Ctrl-C），收尾；问题走正常返工 |
| 4 你决定停 | 任何时候 | 收尾，保留已有现象与粗用量 |

缺库、HTTP/解析失败、收据生成失败、代码启动报错、未知（UNKNOWN）都**不是** STOP：记下来，能继续的安全诊断照做，否则收尾。

**收尾（顺序做完）**：

1. T3：会话还活着就 `L stop`；Unity 停止 Play；若刚结束一次 Play，先做 6.4 归位。
2. T1：Ctrl-C 停板服务，记 `serve_rc` 与时刻。
3. T2 核板上释放并取回板上日志（不取缓存）：

   ```bash
   extract '### 附录 7 ' > "$DIAG_D/prep/closeout.body.sh"
   { printf 'R=%q\n' "$BOARD_DIAG"; cat "$DIAG_D/prep/closeout.body.sh"; } | ssh Jetson 'bash -s' 2>&1 | tee "$DIAG_D/board/closeout.txt"
   ssh Jetson "tar -cf - -C '$BOARD_DIAG' --exclude=logs/cache --exclude=logs/tmp --exclude=logs/scratch logs run" > "$DIAG_D/board/board-logs.tar"; echo "logs_rc=$?"
   ```

   须见 `PORTS_RELEASED` 与 `NO_RESIDUAL_PROCESS`。若仍有监听/进程：只处理命令行里含 `$BOARD_DIAG` 或 `--port 18081` 的本次进程（`ssh Jetson 'kill -TERM <pid>'` 一次后重跑上面核对）；其他进程一律不动，记 UNKNOWN。仍释放不了 → 按 STOP 3 记录。
4. T2 把 runtime 恢复到诊断前：

   ```bash
   [ -e runtime/scenario_config.json ] && mv -n runtime/scenario_config.json "$DIAG_D/hold/overlay-diag.json"
   for x in scenario_config.json frames m3_body_truth.jsonl; do [ -e "$DIAG_D/hold/$x" ] && [ ! -e "runtime/$x" ] && mv -n "$DIAG_D/hold/$x" runtime/ && echo "restored runtime/$x"; done
   git status --porcelain --untracked-files=normal | wc -l; date -u +%FT%TZ | tee "$DIAG_D/clock-end.utc"; elapsed
   ```

5. 填完 `NOTES.md` 的粗维度与收尾核对，把诊断目录路径（`echo "$DIAG_D"`）告诉 supervisor。诊断目录与板上 `$BOARD_DIAG` 都保留，本页不做任何删除；诊断记录不复制进 `docs/evidence/`，不登记 Unity 正式日志。需要改代码的问题由角色走正常返工渠道。

## 附录（第 1–7 步用 `extract` 原样取出；不要手抄）

### 附录 0 手记表模板

```text
# P1-ENG-LOOP-002 诊断冒烟手记 —— 诊断；不进证据链；不作任何门判定

开始（clock-start.utc）：            结束（clock-end.utc）：

## 粗维度
| 维度 | 上限 | 实际 |
|---|---|---|
| 总墙钟（第 1 步 → 收尾完成） | ≤ 180 min | |
| Unity Play 次数（进入即计） | ≤ 5 | |
| 板服务启动编号（含拒启） / 其中故障重启 | ≤ 3 / ≤ 1 | |

## 板服务启动
| 编号 | 起（UTC） | 止（UTC） | serve_rc | 正常 / 故障重启 | 备注 |
|---|---|---|---|---|---|

## Play
| 序号 | SID | 进入 Play | 停止 Play | 会话结局（TERMINAL 原因） | 备注 |
|---|---|---|---|---|---|

## 现象（每条：时刻、在做什么、看到什么、相关文件）

## 目检（语言指定 / 预览确认 / 跟随 / 换目标 / 歧义报告 / 丢失报告，各写一两句）

## STOP（若有：第几类、时刻、已做的收尾）

## 收尾核对（PORTS_RELEASED、NO_RESIDUAL_PROCESS、runtime 已恢复、工作树行数）
```

### 附录 1 diag-assets.py（Air；`resolve` 解析期望，`gen` 生成诊断用 expect-assets）

```python
import json, os, re, shlex, sys

def fault(msg):
    print("DIAG_FAULT " + msg); sys.exit(3)

if sys.argv[1:2] == ["resolve"]:
    text = open("docs/evidence/P1-ENG-LOOP-002-precheck.md", encoding="utf-8").read()
    start = text.find("\n## Mac mini只读补核原始读数与逐维度用量")
    if start < 0:
        fault("precheck_mini_section_missing")
    end = text.find("\n## ", start + 1)
    section = text[start:end if end > 0 else len(text)]
    out = {}
    for tag, var in (("Q4", "WEIGHTS"), ("MMPROJ", "MMPROJ"), ("SERVER", "LLAMA_BIN")):
        m = re.search(r"^=== R02-%s .*?$(.*?)(?=^=== )" % tag, section, re.S | re.M)
        if m is None:
            fault("R02_%s_missing" % tag)
        body = m.group(1)
        first = body.strip().splitlines()[0].split("|")
        shas = re.findall(r"^([0-9a-f]{64})  (/\S.*)$", body, re.M)
        if (len(first) < 5 or first[1] != "regular file" or len(shas) != 1 or shas[0][1] != first[0]
                or re.search(r"^sha_match=yes$", body, re.M) is None):
            fault("R02_%s_unparsed" % tag)
        out[var], out["EXP_%s_SHA" % var], out["EXP_%s_BYTES" % var] = first[0], shas[0][0], first[4]
    for key, value in out.items():
        print("%s=%s" % (key, shlex.quote(value)))
    print("# DIAG_RESOLVE_OK")
elif sys.argv[1:2] == ["gen"] and len(sys.argv) == 4:
    raw = open(sys.argv[2], encoding="utf-8", errors="replace").read()
    names = ("WEIGHTS", "MMPROJ", "LLAMA_BIN")
    sha = {path: digest for digest, path in re.findall(r"^([0-9a-f]{64})  (/.+)$", raw, re.M)}
    got = tuple(sha.get(os.environ[n]) for n in names)
    want = tuple(os.environ["EXP_%s_SHA" % n] for n in names)
    if got != want or re.search(r"^sha_rc=0$", raw, re.M) is None:
        fault("asset_sha_mismatch_or_missing board=%s expected=%s" % (got, want))
    # AC-7 修订 5 / AC-16 修订 1：与 tools/language_serve.py::parse_runtime_build 同一语义（行首 `version:` 恰一行；
    # 旧整数格式取该整数，语义版本 `(build <整数>, commit <文本>)` 整行取 build；其余一律 fault，无缺省值）
    lines = [l for l in raw.splitlines() if l.startswith("version:")]
    version = None
    if len(lines) == 1:
        version = re.match(r"^version: (\d+) ", lines[0]) or re.match(
            r"^version: [0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)? "
            r"\(build ([0-9]+), commit [^\s(),]+\)\Z", lines[0])
    if (version is None or re.match(r"^[0-9]{1,7}$", version.group(1)) is None
            or re.search(r"^version_rc=0$", raw, re.M) is None):
        fault("version_unparsed_duplicate_or_nonzero")
    doc = {
        "work_id": "P1-ENG-LOOP-002",
        "artifact": "DIAGNOSTIC ONLY --expect-assets input; not AC-16 evidence; no gate decision",
        "weights_sha256": got[0], "mmproj_sha256": got[1], "runtime_binary_sha256": got[2],
        "runtime_build": "b" + version.group(1), "runtime_version_line": lines[0], "quantization": "Q4_K_M",
        "expected_source": "docs/evidence/P1-ENG-LOOP-002-precheck.md Mac mini R02 raw lines",
        "raw_source": sys.argv[2],
    }
    with open(sys.argv[3], "w", encoding="utf-8") as handle:
        handle.write(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    print("DIAG_ASSETS_OK")
else:
    fault("usage: diag-assets.py resolve | gen <board-check.txt> <out.json>")
```

### 附录 2 board-check.body.sh（板上只读；经 `ssh Jetson 'bash -s'` 的 stdin 送入，不落板）

```bash
set -u
echo "=== P1-ENG-LOOP-002 诊断；不进证据链；不作任何门判定（board check）==="
date -u +%FT%TZ; printf 'hostname=%s arch=%s user=%s\n' "$(hostname)" "$(uname -m)" "$(id -un)"
if [ -e "$R" ] || [ -L "$R" ]; then echo "DIAG_FAULT diag_root_exists $R"; else echo "diag_root_absent $R"; fi
for f in "$W" "$M" "$B"; do
  [ -L "$f" ] && echo "DIAG_FAULT asset_is_link $f"
  stat -c '%n|%F|%s' -- "$f" 2>&1 || echo "DIAG_FAULT asset_missing $f"
done
sha256sum -- "$W" "$M" "$B" 2>&1; echo "sha_rc=$?"
"$B" --version 2>&1; echo "version_rc=$?"
SS=$(ss -ltn 2>&1); echo "ss_rc=$?"
printf '%s\n' "$SS" | awk '$4 ~ /:(18081|18082)$/ {print "DIAG_FAULT port_busy " $4}'
pgrep -a -f 'llama-server|language_serve|serve-diag\.py'; r=$?; echo "pgrep_rc=$r"
[ "$r" -eq 1 ] || echo "DIAG_FAULT residual_or_pgrep_rc=$r (do not kill unknown processes)"
/usr/bin/python3 --version 2>&1; df -B1 /home/jetson 2>&1; free -b 2>&1
echo BOARD_CHECK_DONE
```

### 附录 3 serve-diag.sh（板上；现行 DIAG:RETRY:1（及历史 SUB:3）由 `play_ops --mode diagnostic diag` 在可见前台 SSH 交互 bash 中以 `bash --noprofile --norc <诊断根>/run/serve-diag.sh 1` 运行；只许启动编号 1，历史编号 2/3 不可执行）

> **BIND-Q1 选 A（围栏块零改）**：下方围栏内的 `SUB:3` 字样（`DIAG_FAULT SUB:3 allows start number 1 only…` 拒绝文案与日志横幅 `board start $N/1，SUB:3`）是历史标签，板上输入字节不变；「只许启动编号 1」与 DIAG:RETRY:1 已签的板服务启动 ≤ 1 一致。实际 request_id 以 Air 新粗账、`NOTES.md` 与 `ops-events.jsonl` 为准，不以板上横幅判定。若以后要改板输入，先具名回合同，不顺带实现。

```bash
set -o pipefail
N=${1:-}
case "$N" in 1) ;; *) echo "DIAG_FAULT SUB:3 allows start number 1 only; historical numbers 2/3 are not executable (got '$N')"; exit 97 ;; esac
. "$(dirname "$0")/serve-diag.env" || { echo "DIAG_FAULT serve-diag.env failed to load (no preflight, no load)"; exit 97; }
[ -n "${BOARD_DIAG:-}" ] || { echo "DIAG_FAULT missing_input BOARD_DIAG (no preflight, no load)"; exit 97; }
LOG="$BOARD_DIAG/logs/serve-$N.log"
[ -e "$LOG" ] && { echo "DIAG_FAULT start $N already used ($LOG exists)"; exit 97; }
echo "=== P1-ENG-LOOP-002 诊断；不进证据链；不作任何门判定（board start $N/1，SUB:3）===" | tee "$LOG"
date -u +%FT%TZ | tee -a "$LOG"
cd "$BOARD_DIAG/code" || exit 97
SS=$(ss -ltn 2>&1) || { echo "DIAG_FAULT ss_failed" | tee -a "$LOG"; exit 97; }
printf '%s\n' "$SS" | awk '$4 ~ /:(18081|18082)$/ {print "DIAG_FAULT port_busy " $4; f=1} END {exit f}' | tee -a "$LOG"
[ "${PIPESTATUS[1]}" -eq 0 ] || exit 97
pgrep -a -f 'llama-server|language_serve|serve-diag\.py'; r=$?
[ "$r" -eq 1 ] || { echo "DIAG_FAULT residual_or_pgrep_rc=$r (do not kill unknown processes)" | tee -a "$LOG"; exit 97; }
for v in $(env | sed -nE 's/^((LLAMA_|GGML_|MTMD_|HF_|HUGGINGFACE_)[A-Za-z0-9_]*|[A-Za-z0-9_]*_(proxy|PROXY))=.*/\1/p'); do
  echo "unset $v" | tee -a "$LOG"; unset "$v"
done
for k in BOARD_DIAG WEIGHTS MMPROJ DIAG_LLAMA_BIN BOARD_TS; do
  [ -n "${!k:-}" ] || { echo "DIAG_FAULT missing_input $k (no preflight, no load)" | tee -a "$LOG"; exit 97; }
done
mkdir -p "$BOARD_DIAG/logs/tmp" "$BOARD_DIAG/logs/cache/llama" "$BOARD_DIAG/logs/cache/cuda" "$BOARD_DIAG/logs/scratch" || exit 97
umask 077
env TMPDIR="$BOARD_DIAG/logs/tmp" XDG_CACHE_HOME="$BOARD_DIAG/logs/cache" LLAMA_CACHE="$BOARD_DIAG/logs/cache/llama" \
    CUDA_CACHE_PATH="$BOARD_DIAG/logs/cache/cuda" CUDA_CACHE_MAXSIZE=134217728 \
    /usr/bin/python3 -I -S -B "$BOARD_DIAG/run/serve-diag.py" 2>&1 | tee -i -a "$LOG"
echo "serve_rc=${PIPESTATUS[0]}" | tee -a "$LOG"; date -u +%FT%TZ | tee -a "$LOG"
```

### 附录 4 serve-diag.py（板上；budget=None 一次性启动块，只复用现有函数）

```python
"""P1-ENG-LOOP-002 diagnostic-only startup block (budget=None). Not evidence; no gate decision."""
import argparse
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile

MISSING = [k for k in ("BOARD_DIAG", "WEIGHTS", "MMPROJ", "DIAG_LLAMA_BIN", "BOARD_TS") if not os.environ.get(k)]
if MISSING:
    print(f"DIAG_FAULT missing_input {' '.join(MISSING)} (no preflight, no load)", flush=True)
    print("DIAG serve_rc=97", flush=True)
    sys.exit(97)
ROOT = Path(os.environ["BOARD_DIAG"])
CODE, LOGS, RUN = ROOT / "code", ROOT / "logs", ROOT / "run"
sys.path.insert(0, str(CODE))
from tools import language_serve as ls  # noqa: E402
from tools.eng_loop2 import llama_adapter  # noqa: E402

if Path(ls.__file__).resolve().parents[1] != CODE.resolve():
    print(f"DIAG_FAULT language_serve imported from outside the diagnostic code root: {ls.__file__}", flush=True)
    sys.exit(ls.EXIT_REFUSED)
print("DIAGNOSTIC ONLY - not evidence - no gate decision; budget=None, no HttpBudgetLedger", flush=True)
LLAMA_PORT, SERVE_PORT, HOST = 18081, 18082, os.environ["BOARD_TS"]
args = argparse.Namespace(
    llama_bin=Path(os.environ["DIAG_LLAMA_BIN"]), weights=Path(os.environ["WEIGHTS"]), mmproj=Path(os.environ["MMPROJ"]),
    expect_assets=RUN / "expect-assets.json", llama_port=LLAMA_PORT,
    llama_request_timeout_s=llama_adapter.DEFAULT_REQUEST_TIMEOUT_S,
)
try:
    preflight = ls.llama_preflight(args)
except ls.StartRefused as exc:
    print(f"DIAG refused to start (no GGUF load): {exc}", flush=True)
    print(f"DIAG serve_rc={ls.EXIT_REFUSED}", flush=True)
    sys.exit(ls.EXIT_REFUSED)
print(f"DIAG preflight ok serve_code_sha256={preflight.serve_code_sha256} machine={preflight.machine}", flush=True)
(LOGS / "scratch").mkdir(parents=True, exist_ok=True)
images = Path(tempfile.mkdtemp(prefix="language-serve-images-", dir=str(LOGS / "scratch")))
child = server = None
rc = 0
previous = {s: signal.signal(s, ls._raise_terminate) for s in (signal.SIGTERM, signal.SIGHUP)}
try:
    print("DIAG_LOAD_START llama-server child (GGUF load)", flush=True)
    child = subprocess.Popen(
        ls.llama_server_command(args.llama_bin, args.weights, args.mmproj, LLAMA_PORT), stdin=subprocess.DEVNULL
    )
    try:
        ls._wait_llama_ready(child, f"http://127.0.0.1:{LLAMA_PORT}", ls.DEFAULT_LLAMA_READY_TIMEOUT_S, budget=None)
    except ls.ReadyFailure as failure:
        print(f"DIAG load_failure: {failure.reason}", flush=True)
        rc = ls.EXIT_LOAD_FAILURE
    else:
        runtime = ls.SingleFlightRuntime(
            preflight.adapter, scratch_directory=images, t_hard_s=ls.DEFAULT_T_HARD_S, delete_images_after_run=True
        )
        server = ls.build_server(
            runtime, host=HOST, port=SERVE_PORT,
            extra_reply_fields={"serve_code_sha256": preflight.serve_code_sha256, "machine": preflight.machine},
            access_log=LOGS / "access-observe.jsonl", budget=None, long_poll=True,
        )
        server.timeout = 0.5
        print(f"DIAG language-serve listening on http://{HOST}:{server.server_port} "
              f"(llama-server pid {child.pid} on 127.0.0.1:{LLAMA_PORT}); Ctrl-C to stop", flush=True)
        while True:
            if child.poll() is not None:
                print(f"DIAG llama-server exited with {child.returncode} while serving", flush=True)
                rc = ls.EXIT_LLAMA_EXITED
                break
            server.handle_request()
except (KeyboardInterrupt, ls._Terminate):
    rc = 0
except Exception as exc:  # noqa: BLE001 - diagnostic: report and clean up
    print(f"DIAG_FAULT {type(exc).__name__}: {exc}", flush=True)
    rc = 1
finally:
    if server is not None:
        server.server_close()
    if child is not None:
        ls._stop_child(child)
    shutil.rmtree(images, ignore_errors=True)
    for sig, handler in previous.items():
        signal.signal(sig, handler)
print(f"DIAG serve_rc={rc}", flush=True)
sys.exit(rc)
```

`access-observe.jsonl` 只是现有逐请求字节观察日志，不求和、不守限，不是正式 ledger。

### 附录 5 status-check.py（Air；核 /status）

```python
import json, os, sys
from pathlib import Path

REPO = Path(os.environ["REPO"])
sys.path.insert(0, str(REPO))
from controller import language_bridge as bridge  # noqa: E402
from tools.eng_loop2 import deploy_digest  # noqa: E402

status = json.load(open(sys.argv[1], encoding="utf-8"))
bad = []
try:
    if not bridge.validate_llama_identity(status.get("model_identity") or {}):
        bad.append("model_identity lacks the six llama keys")
except Exception as exc:  # noqa: BLE001
    bad.append(f"model_identity invalid: {exc}")
local = deploy_digest.desktop_identity_digests(REPO)["serve_code_sha256"]
if status.get("serve_code_sha256") != local:
    bad.append(f"serve_code_sha256 board={status.get('serve_code_sha256')} air={local}")
if "http_budget" in status:
    bad.append("http_budget present: this is not the budget=None diagnostic server")
print(f"state={status.get('state')} machine={status.get('machine')} serve_code_sha256={status.get('serve_code_sha256')}")
print("\n".join("DIAG_FAULT " + item for item in bad) if bad else "DIAG_STATUS_OK")
```

### 附录 6 ops.sh（T3 操作者短命令；每次新 Play 起会话后重新加载；**已停用**，见页首 OPS 增量）

```bash
SID=$(cat "$DIAG_D/play/current-sid"); echo "当前会话 $SID（诊断；不进证据链）"
L() { local action=$1; shift; "$PY" -m controller.language_loop "$action" "$@" --session-id "$SID" --runtime runtime --allow-shared-runtime; }
status_json() { "$PY" -m controller.language_loop status --runtime runtime; }
st() { status_json | "$PY" -c 'import json,sys
d=json.load(sys.stdin); t=(d.get("tracker_state") or {}).get("tracker_state") or {}; r=(d.get("last_result") or {}).get("result") or {}
print("state=%s track=%s suspect=%s/%s reason=%s" % (t.get("state"), t.get("track_id"), t.get("suspect_kind"), t.get("suspect_id"), t.get("reason")))
print("last_result: %s %s candidates=%d preview=%s" % (r.get("purpose"), r.get("status"), len(r.get("candidates") or []), r.get("preview_path")))
print("last_request:", json.dumps(t.get("last_request"), ensure_ascii=False))'; }
designate_token() { status_json | "$PY" -c 'import json,sys; r=json.load(sys.stdin)["last_result"]["result"]; assert r["purpose"]=="designate" and r["status"] in ("unique","ambiguous"), (r["purpose"], r["status"]); print(r["result_id"])'; }
pointer_token() { status_json | "$PY" -c 'import json,sys; t=json.load(sys.stdin)["tracker_state"]["tracker_state"]; assert t["state"]=="TRACKING" and t["track_id"], (t["state"], t["track_id"]); print(t["track_id"])'; }
suspect_token() { status_json | "$PY" -c 'import json,sys; t=json.load(sys.stdin)["tracker_state"]["tracker_state"]; assert t["state"]=="SUSPECTED" and t["suspect_id"], (t["state"], t.get("suspect_id")); print(t["suspect_id"])'; }
preview() { local p; p=$(status_json | "$PY" -c 'import json,sys; print(((json.load(sys.stdin).get("last_result") or {}).get("result") or {}).get("preview_path") or "")'); if [ -n "$p" ]; then open "$p"; else echo "没有预览图（preview_path 为空）：记现象，不 confirm"; fi; }
```

### 附录 7 closeout.body.sh（板上只读收尾核对；经 stdin 送入）

```bash
echo "=== P1-ENG-LOOP-002 诊断收尾核对 ==="; date -u +%FT%TZ
SS=$(ss -ltn 2>&1); echo "ss_rc=$?"
printf '%s\n' "$SS" | awk '$4 ~ /:(18081|18082)$/ {print "STILL_LISTENING " $4; f=1} END {if (!f) print "PORTS_RELEASED"}'
pgrep -a -f 'llama-server|language_serve|serve-diag\.py'; r=$?; echo "pgrep_rc=$r"
[ "$r" -eq 1 ] && echo NO_RESIDUAL_PROCESS
du -sb "$R" 2>&1; df -B1 /home/jetson 2>&1
```
