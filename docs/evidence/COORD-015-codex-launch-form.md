# COORD-015 证据：supervisor 拉起 `codex exec` 的命令形式与权限分类器（两机实测）

日期：2026-09-27。核查者：用户直接指挥的 Claude Code 会话（本机 MacBook Air，用户 zc）；
Mac mini（Tailscale `macmini`，用户 zc5）经 SSH 只读读取。依据账本同日「用户授权协调批次：
明确 supervisor 拉起 codex exec 的命令形式与每台机器前提」。

## 方法

遍历两机 `~/.claude/projects/*TetheredDroneTracking*/*.jsonl` 会话记录，取所有 Bash 工具
调用中含 `codex exec` 实际启动的命令及其 tool_result，并统计全部「auto mode classifier」
拒绝。两机 Claude 桌面应用同版本（2.9939.2），supervisor 会话均为 `permissionMode: auto`。

## 启动调用逐条结果

| 机器/日期 | 会话 | 命令形状 | 结果 |
|---|---|---|---|
| 本机 09-26 | 87f4330b | `SP=… && nohup codex exec …`（组合） | 拒：Create Unsafe Agents |
| 本机 09-26 | 598fd10b | 单条 `codex exec -C … -o last.md - < prompt > log 2>&1` | 2/2 成功 |
| mini 09-27 | d2b2aad7 | `git push -q origin main && SP=… && nohup codex exec …`（组合） | 拒：Create Unsafe Agents |
| mini 09-27 | a76189e6 | 单条（同上形式） | 5/5 成功，进程 exit 0 |
| mini 09-27 | eb95ae88 | `SP=… && codex exec … "$(cat …)"`（组合） | 拒：Create Unsafe Agents |

调度日志 `docs/evidence/supervisor-dispatch.jsonl`（HEAD aada593）中 `runtime: codex exec` 的
派发共 10 条：7 条 `finished`、3 条 `aborted(launch_failed)`（3e6d、0d69、b6f5），proof 均为
分类器拒绝原文；另有 3 条未登记的启动/登记命令被拒（mini d2b2aad7 18:40、eb95ae88 23:25 与
23:38，后两条理由升为 Auto-Mode Bypass）。单条形式 7/7 放行，组合形式 0/4 放行。

## 连带现象

被拒会话随后的登记（python 追加 + git）与只读核查（`git status`、`tail` 调度日志、`pgrep`/`ps`）
也被拒（理由 Create Unsafe Agents / Auto-Mode Bypass / Instruction Poisoning），只能重开会话。
mini 上 eb95ae88 会话写入 memory 索引行亦被拒，故其记忆文件 `acceptance-dispatch-wrapper.md`
未入 MEMORY.md 索引。

## 权限配置事实

- 本机：项目级 `.claude/settings.local.json`（gitignore）含 `Bash(codex exec *)`；无 pgrep/ps 规则。
- mini：用户级 `~/.claude/settings.json` 含 `Bash(codex exec:*)`、`Bash(pgrep:*)`、`Bash(ps -o lstart=:*)`、
  `Bash(bash ~/local/bin/dispatch-acceptance.sh:*)`；项目级只含 git 规则。包装脚本
  `dispatch-acceptance.sh`（09-27 19:51 建）至今未被调用，写死 openai/gpt-6-sol，无 Kimi 回退。
- 允许规则为命令开头前缀匹配；命中即不经分类器（Claude Code 设置 `autoMode.classifyAllShell`
  缺省 false）。

## 推理强度事实（续批，用户问「extra 和 high 选哪个」后核查）

| 机器 | `~/.codex/config.toml` model | model_reasoning_effort |
|---|---|---|
| 本机 | gpt-6-sol | high |
| Mac mini | gpt-6-astra | medium |

启动命令此前只显式指定 `-m`，未指定强度，接受角色的实际推理强度随派发机器的本地配置走。
本机用只记录请求体的本地 HTTP 服务（自定义 provider，`wire_api = "responses"`，假 key）实测：
`-c model_reasoning_effort="high"` 下 codex 对 gpt-6-sol 发送 `reasoning: {"effort":"high","context":"all_turns"}`，
对 k3-256k 发送 `reasoning: {"effort":"high","summary":"auto"}`，即该参数两条路径都会真正发给服务端。
本机 `~/.codex/sessions` 中 2026-09-25 三次 k3-256k 运行（A5/A7 夹具演练）记录的 effort 均为 `medium`
且正常完成；`high` 在 Kimi 端未验证。据此细则模板：openai 路径显式 `high`，Kimi 路径显式 `medium`。

2026-10-02 补测（supervisor，本机 MacBook Air，非派发、未触仓库；账本同日「全局 — 用户指示：接受角色 Kimi 回退推理强度改 high」）：
`codex exec -C <scratchpad 空目录> --skip-git-repo-check -c model_provider="kimi" -m "k3-256k" -c model_reasoning_effort=<medium|high> -c 'notify=[]' --sandbox read-only`，
提示「只回复 OK，不要调用任何工具。」经 `- <` 读入。两次均回显 `provider: kimi`、`model: k3-256k` 与所设强度，返回 OK、无错误；
仅有 codex 警告「Model metadata for `k3-256k` not found. Defaulting to fallback metadata」，不影响调用。用户随后指示 Kimi 路径改 `high`，细则模板同批改为两条路径均 `high`。

2026-10-02 mini 补测（用户直接指挥的 Claude Code 会话，Mac mini，Opus 5.5；非派发、未触仓库）：PATH 上 `codex`（`~/local/bin/codex`，codex-cli 0.160.0），
同上命令取 `model_reasoning_effort="high"`。回显 `provider: kimi`、`model: k3-256k`、`reasoning effort: high`，返回 OK、无错误；
同样仅有上述 fallback metadata 警告；`tokens used` 54,898（codex 自带系统提示为主）。

## `KIMI_API_KEY` 事实

- mini：login shell、`~/.zshenv`/`~/.zprofile`/`~/.zshrc`、`launchctl getenv` 均无。
- 本机：`~/.zshrc` 有 export，但 Claude Code Bash 工具进程（`/bin/zsh -c`，login、非交互，
  只读 `~/.zshenv`/`~/.zprofile`）看不到；shell 快照亦不含。
- codex 读取 `$CODEX_HOME/.env`：临时 CODEX_HOME 实测，无 `.env` 时报
  `Missing environment variable: KIMI_API_KEY`，有 `.env` 时该错误消失（端点为本机死端口，仅验证读取）。
- 2026-10-02 本机：用户自行把 `~/.zshrc` 中的密钥写入 `~/.codex/.env`（单行、权限 600，supervisor 未经手密钥值）；
  细则规定的探测返回 `kimi_key=0`，上节补测真实端点通过。mini 未核查。
- 2026-10-02 mini：此前无 `~/.codex/.env`，`~/.codex/config.toml` 已有 `[model_providers.kimi]`（`env_key = "KIMI_API_KEY"`）。
  用户在自己的终端以不回显输入写入 `~/.codex/.env`（单行 `KIMI_API_KEY=…`、权限 600，会话未经手密钥值）；
  细则规定的探测返回 `kimi_key=0`，上节 mini 补测真实端点通过。两机 Kimi 回退前提均已满足。

## gpt-6.1-sol 切换（2026-10-01，supervisor 本机实测）

依据：账本 2026-10-01「全局 — 用户指示：接受角色模型切换为 gpt-6.1-sol；本机探测未通过，待升级 codex CLI 后复测」。
三次探测均为同一提示（只回复 OK）、ChatGPT 登录、`-m "gpt-6.1-sol" -c model_reasoning_effort="high"`、只读沙箱、空目录，非派发、未触仓库：

| 时刻（UTC） | codex 可执行文件 | 版本 | 结果 |
|---|---|---|---|
| 16:47:46 | `/opt/homebrew/bin/codex`（npm 全局） | 0.157.0 | 400：`The 'gpt-6.1-sol' model is not supported when using Codex with a ChatGPT account.`；models_cache 无该型号 |
| 16:56:37 | ChatGPT 应用自带 `codex-cli/bin/codex` | 0.159.2 | 通过，回复 OK，2,667 tokens |
| 17:00:29 | `/opt/homebrew/bin/codex`（用户 `npm install -g @openai/codex@latest` 后） | 0.159.3 | 通过，回复 OK，2,680 tokens；models_cache 列出 gpt-6.1-sol，支持 low…ultra，含 high |

结论：该型号需 codex-cli ≥ 0.159；派发只能用 PATH 上的 `codex`（允许规则按 `codex exec` 前缀匹配），应用自带副本不可替代。另一台机器（mini）切换前同样须先升级 CLI 并按本节复测。

### 主观对比（用户要求；单样本、非权威，不是门证据）

同一 K2 候选（快照 = 正式 `C1@K2` 开工时 HEAD，克隆后删去全部引用、看不到正式核对提交；codex 记忆功能关闭），同一份 `C1@K2` 任务提示；gpt-6-sol 为正式派发（边核对边写提案、提交），gpt-6.1-sol 为只读影子（结论只输出到消息）。

| 项 | gpt-6-sol（正式 C1@K2） | gpt-6.1-sol（影子） |
|---|---|---|
| 用时 / tokens / 执行命令数 | 约 7.5 min / 214,764 / 50（含写文件与提交） | 约 10.5 min / 289,414 / 31 |
| 总结论 | 首退 | 首退 |
| 核对表计数 | 满足 26、不满足 1、证据缺失 2 | 满足 24、不满足 3、证据缺失 2 |
| 不满足项 | AC-1（显式非法围栏被当缺省） | AC-11、AC-19、AC-22（AC-1 判满足，围栏问题记在 IR-13 与返工要点 1） |
| IR 裁定 | 采纳 11；不采纳 IR-10、IR-13 | 采纳 12；不采纳 IR-13（IR-10 采纳并注明不豁免 §3.1） |

- 共同点：都独立抓到 K2补跑 引入的「全 NaN 围栏一律视同缺省」问题，并都否掉 IR-13；都确认回放仍选 C3。
- 归因差异：6-sol 把它记在 AC-1，返工要点更贴合合同条款；6.1-sol 认为 AC-1 的闭集夹具本身成立，把问题挂在 IR-13 上，修复方向相同。
- 6.1-sol 多报三项，均附具体代码行与反例：`standoff_planner.py` `_position_sigma` 对极大有限协方差平方溢出（AC-11，静态反例、未执行）；`frame_follow_replay.py` `analyze_run` 未按 §3.11 入口 8 读取并核对 manifest 场景来源/SHA（AC-19）；`track_loop.py` standoff 构造路径读取 `target.route_world_m`（AC-22）。supervisor 只核实了所引代码行存在，未判断是否构成缺陷；是否成立由后续 `C2@K2`/`R1@K2` 按各自规则裁定，本节不作为输入。
- 主观印象：6.1-sol 更宽、更激进，理由写得更具体（行号链接、构造反例），代价是多约 35% tokens、多约 40% 时间；6-sol 更收敛，只抓到最直接的一处。多报项若被复核确认，则 6.1-sol 能把问题前移到核对轮；若多为误报，会增加返工轮次——需后续轮次的裁定才能下结论。
