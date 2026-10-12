# P1-ENG-LOOP-002 — 阶段 B 操作单（§3.6；PLAY_GOVERNING；**当前不可执行**）

> **修订记录**：阶段 A 随附版本为最近通过候选（`R2@K1K2K3K4` `passed_candidate`）中的本文件；`mini操作单准备` 版（2026-10-07）经 C3 核对、R3 派发 `REVIEW_BLOCKED`（未开轮）。`R3答复后新候选` 版（2026-10-07，中间提交，非稳定）落实同名提案「R3六题答复落实」§2 的 AC-7 修订 2(a)(b)、AC-10 修订 1(a)(b) 与 O-1…O-6、PR-8…14，停在 IR-N1/IR-N2。**本版是登记轮次 `稳定候选`（2026-10-07，Implementation，MacBook Air，零消耗）**：再合并「IR-N裁定」§2 的 AC-15 修订 1（jetson 单轮、首失败停、本单第 5 节逐步检查退出码）与「CHANGE5答复落实」§2 的 AC-7 修订 3（有界长轮询），按「IR-N裁定」§1 纠正旧版第 0.6 节把投影称为必然的读法并重算有限路径/预留（第 0.6 节），去掉第 4 节 `<n>`/`<R_n>` 占位。逐项落点与四条件自证见 `docs/evidence/P1-ENG-LOOP-002-stable-candidate.md`。该版经 C4 核对、独立 `R3@K1K2K3K4` `REWORK_REQUIRED`（2/2，冻结集 R3-1…3）。**本版是登记轮次 `R3返工`（2026-10-07，Implementation，MacBook Air，零消耗）**：按同名提案「R3冻结集裁定」§1–2 只改三处——第 0.6 节与 AC-7 修订 4 逐字对齐（R3-1，代码/测试不改）、第 1.0 节放行门（R3-3）、第 4 节启动块 `ss` 失败即停（R3-2）；落点与四条件自证见 `docs/evidence/P1-ENG-LOOP-002-r3rework.md`。该版经 `R4@K1K2K3K4` 终局 `PASS`（已消费）。**本版是登记轮次 `身份修复K1K3`（2026-10-07，Implementation，MacBook Air，零消耗）**：按同名提案「R4消费与诊断故障裁定」§3–5 只改来源加载与版本解析说明——第 0.3 节改为有界普通 env 文件的「来源加载块」（AC-10 修订 2：解析/过滤生成/加载三步各核退出状态与 `RESOLVE_OK`、必需变量逐值一致，失败即 STOP），第 2 节与第 3 节第 4 步改调该块，第 3 节第 4 步的附录 B 改用 AC-7 修订 5 / AC-16 修订 1 的版本解析；落点与四条件自证见 `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md`。本版未经复核，不预签通过；修复未在真实板条件下验证。**本版是登记轮次 `OPS操作增量实现`（2026-10-08，Implementation，MacBook Air，零消耗）**：按同名提案「OPS九题答复落实」§1–6（W1–W5、O1–O4、十条 AC 修订）把各节的人工执行改为单入口 `tools/eng_loop2/play_ops.py` 分阶段执行与本机操作网页 `tools/eng_loop2/operator_web.py`（见新增第 0A 节与各节「OPS 增量」段）；ask/respecify 每条仍由本人看实时画面点「发送」或「跳过（不在画面）」（N-5 保持），候选确认/拒绝与收尾「通过/失败/受阻」反馈都在网页；G1–G5、原资源上限、原因码与 STOP 处置不变，正式采集仍后置。本版未经复核、未在真实板/Unity 条件下运行；验证清单与待裁定见 `docs/evidence/P1-ENG-LOOP-002-ops-validation-plan.md`，进度与缺口见 `docs/evidence/P1-ENG-LOOP-002-ops-progress.md`。**本版另含登记轮次 `OPS裁定落实与停点验证`（2026-10-08，Implementation，MacBook Air）**：按同名提案「OPS验证额度落实与IR裁定」§3–5 把 IR-OPS-1…6 的裁定写入第 0A 节、第 1 节、第 9 节、第 10 节、第 13 节对应 OPS 增量段（G4/登记机读行已采纳、`S-REBUILD` 一律 UNKNOWN 停全部、新入口无环境性重试、观察/跟随只锚定会话原流），诊断改为独立 `diag` 模式（不属本正式单）；落点与停点验证见 `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md`。**本版另含登记轮次 `OPS稳定候选`（2026-10-08，Implementation，MacBook Air，零消耗）**：按同名提案「OPS基线与IR78裁定」§3 只改第 0.2 节 `$OUT` 行与第 1 节 1.2 的忽略说明措辞（仓库 `.gitignore` 精确一行 `/outputs/eng-loop2/`，不泛化忽略 `outputs/`），命令与判据不变；验证见同一交接文件第 10 节。**本版另含登记轮次 `OPSC6返工`（2026-10-08，Implementation，MacBook Air，零消耗）**：按 `docs/evidence/P1-ENG-LOOP-002-C6-OpsK1K2K3K4.md` §2 只改第 9 节与第 13 节 OPS 增量段的失败路径说明（STOP/故障/中断后封住业务、失败也走安全收尾、尝试记录完整保留；工具截止不因等待 Play 延长），原命令、原因码与处置不变；落点见同一交接文件第 11 节。
>
> **全部命令块在 `bash` 中执行**（O-4）：Air 缺省登录 shell 是 zsh，开工先在终端执行 `exec bash --noprofile --norc`，再 `set -o pipefail`；本单的未加引号分词（`$PATHS`）、数组与 `${PIPESTATUS[0]}` 均按 bash 语义写，不在 zsh 中执行。本单**不用进程替换加载来源**：Air `/bin/bash` 3.2 下 `. <(…)` 不读入任何变量且退出状态为 0（AC-10 修订 2 的离线探针，见 `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md` 第 3 节），一律用第 0.3 节来源加载块。板端交互会话同为 bash（`ssh … -t Jetson` 后先 `exec bash --noprofile --norc`）。
>
> **执行门（全部满足前一律不做，任何一步都不预授权）**：(G1) 本版（或其返工版）经接受下一实际 C 轮核对、独立 R 轮通过，复核文件写出新的 `passed_candidate`，且第 1.0 节严格门在固定发布引用上成立；(G2) `SLOT:FACT:1` 窗口互斥已由用户确认（账本 2026-10-07「用户答 R3 阻断消费六题…」，同名提案「R3六题答复落实」§3）；执行前仍按第 2、4 节核当前端口/残留，不从一次确认推断现场已满足；(G3) 合同答复已落实（同名提案「R3六题答复落实」§2、「IR-N裁定」§2、「CHANGE5答复落实」§2、「R3冻结集裁定」§2），且落实它们的本版代码/操作单已是新通过候选（即 G1 的同一候选）；(G4) 第 2 节准备读数由接受核清、逐维度确认原签上限与已核合同相符并**明确放行**（若必需事实仍 UNKNOWN 而需 `B-main:ENV:2`，先由用户另签其子合同并执行、核清）；(G5) Air 来源对齐（第 0.3 节，用户 `FACT:2` A：新候选通过后本人从 mini 对齐）通过。**门与单元的对应**（PR-12，消除门循环）：准备单元 #1 只要求 G1、G2、G3、G5；收据单元 #2 与 Play 单元 #3 另要求 G4。B-main 上限已由用户签发（账本 2026-10-07），但依赖未核环境事实的服务/GGUF、推理、HTTP、二进制执行与下游 Play 维度在相应门前**可执行值 0**。可派生标识（HEAD、`passed_candidate`、发布引用、sha、带 UTC 的目录名）一律运行时解析，不在本单手抄。

## 0A. 单入口阶段与本机操作网页（OPS操作增量；「OPS九题答复落实」§2 AC-10 修订 3、§3）

正式执行由执行检出根的 `"$PY" -m tools.eng_loop2.play_ops`（`$PY` 同第 0.2 节）分阶段推进；它只组合本单各节**原命令**与原判据（附录 P、mini 证据附录 A/B 由工具按标题前缀原样取出执行），每阶段先自动重跑第 1 节机械核对，前置门缺具名有效放行或任一检查非 0 即停（打印 `STOP <原因码> …`、退出码 3），不自动重试、不跨维度借余额。下列每条命令前都是同一前缀 `"$PY" -m tools.eng_loop2.play_ops --docwt "$DOCWT"`：

| 阶段（子命令） | 对应本单节 | 前置门（工具机读） | 产出 / 停点 |
|---|---|---|---|
| `plan --p2-object <red_car\|B\|C>` | 第 7、9 节 | 无 SSH；Play 前离线 | 以独立进程跑原 `analyze_play derive-bc`，逐字核对第 7 节 B/C 读数，写冻结计划 `$OUT/plan/ops-plan.json`（只含文字/intent/Δ/观察时长；不覆盖既有冻结计划）；不符或 < 2 辆即停回接受 |
| `gate` | 第 1 节 1.0–1.5 | — | 原流 `$OUT/release/<UTC>-*.txt`；末行 `RELEASE_GATE_OK` 才算过；1.1 的 `git checkout --detach` 仍由操作者关闭 Unity 后执行，工具只核 |
| `source` | 第 0.3 节 | — | SOURCE:2：只核 Air 现有原件（缺件即 `S-PRECHECK`），不复制、不替本人 mini 对齐 |
| `prep --registered-release <文件>` | 第 2 节（单元 #1） | G1/G2/G3（第 1 节）+ 1.6 登记 + G5（`source`） | 读齐即停：打印 `NEXT_GATE G4 prep_stdout_sha256=<sha>`，交接受核清；工具不自签 G4 |
| `receipt --registered-release <文件>` | 第 3、4、5 节（单元 #2） | 另要求 G4 机读放行行 | 建根→资产→部署（批次 1）→前台服务→身份→measure→k-receipt→停止与释放→日志（批次 2）；`k_receipt_rc=0` 才打印 `RECEIPT_OK` |
| `play --registered-release <文件> [--playbooks P1 P2 P3] [--port 8772]` | 第 4、6、8–13 节（单元 #3） | 另要求单元 #2 收据退出 0 与冻结计划 | 本机操作网页 `http://127.0.0.1:<port>/`；每剧本等待本人 Play→起会话→本人逐步发送/跳过与候选选择→本人停 Play→归档；全部剧本后停止服务、核释放、日志（批次 3）；随后以独立进程调用 `tools/eng_loop2/summarize_ops.py` 生成收尾摘要，本人在网页对每次尝试点「通过/失败/受阻」（最多等 `--feedback-wait-s`，缺省 1800 s，板已释放；缺失记「未反馈」，不默认通过） |

- **1.6 登记与 G4 的机读形式（IR-OPS-1/2 已采纳，同名提案「OPS验证额度落实与IR裁定」§3）**：`--registered-release` 指向已交当轮发令角色登记的第 1 节原流文件；当轮发令角色在 `docs/unity-test-log.md` 本次正式运行条目写独立行 `release_raw_sha256=<登记原流文件 64 位小写 sha256>`（同时保留原流路径、实际 HEAD/status 与场景/配置等原要求）并推送，工具从固定发布引用核此行，且重跑的 1.1–1.4 段须与登记文件逐行相同；G4 由接受核清后**只**在同名提案具名「G4准备核清与放行」节写独立行 `g4_release: <prep.stdout 的 64 位小写 sha256>`（可带列表记号/反引号），工具从发布引用取。该 sha 运行时求、不手抄；格式示例、摘要/计划值或旧条目都不能代替现场登记；匹配只证明该原流已获 G4，不代 G1/G2/G3/G5/当前候选与现场再核。缺行、不匹配或读取失败 → `S-PRECHECK`，`receipt`/`play` 不开单元；脚本不自签任何门。
- **运行中只有一个写者**：`play` 运行期间所有 ask/respecify/confirm/reject/release/stop 只经网页与工具共用的一次提交记录发出（W4）；本单第 9 节逐字命令是工具展开执行的原命令，**运行中不得手工在终端执行**（会形成第二写者）；手工 CLI 仅限 `status` 只读与工具停止后的诊断后备，且不得绕过一次提交记录。
- **诊断模式与正式模式独立路由（IR-OPS-5）**：本单各阶段只在正式模式（缺省）运行；`--mode diagnostic` 只运行 `diag` 阶段（合同见同名提案「OPS验证额度落实与IR裁定」§4，操作见 `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` 页首「现行 SUB:3」），独立 Air/板根与粗账，不写本单的 `$OUT`、assets、收据、`ops-ledger.json` 或正式 ID，不作任何门判定，诊断读数不能转为本单的门或证据。`diag` 在正式模式拒启，正式阶段在诊断模式拒启。

## 0. 分工、记号、已签/暂锁维度与计账单位

### 0.1 分工（(h)(j)(k) 已答，不重问）

- **单主臂**：只用同一 Jetson Orin Nano 8GB Super；5060 备用臂不启用、各维度 0（用户 (j)）。主臂任何失败不转臂、不重启（第 13 节）。
- **用户本人**：在 MacBook Air（Unity 主机）按 Unity Play/停止按钮；在本机操作网页凭实时画面对每条 ask/respecify 点「发送」或「跳过（不在画面）」、凭候选预览与第 7 节预登记描述点「确认序号」或「拒绝」、必要时点「停止会话」（安全中止，不代按 Unity 停止）；收尾摘要就绪后对每次尝试点「通过/失败/受阻」并可附文字（正式用户验证，(h)，AC-14 修订 1）。
- **代理/脚本（OPS:ACTOR:1，仅覆盖原本人专属执行人限制）**：由 `play_ops` 持有正式板服务与收据的**可见前台 SSH 子进程**（第 4 节命令在 `serve` 通道的交互 bash 中逐行键入；正常 Ctrl-C 中断、等待退出、同会话核端口/进程释放），以及机械核对、收据、调度、停止与归档；不后台驻留、不探测 46273、不清未知进程，原三单元/有限通道/守账及故障重启 0 保持。方向不等于现在启板：G1–G5 未齐一律不开单元。
- **板上目录**：本项独立根 `$BOARD_ROOT=/home/jetson/eng-loop2`，源码 `$BOARD_CODE=$BOARD_ROOT/code`，日志/缓存/临时 `$BOARD_LOGS=$BOARD_ROOT/logs`；**同名根已存在即 STOP `S-PRECHECK`，不覆盖**；不写 JET 的 `~/eng-jet/` 任何路径（只读使用其中已核的三文件与库），不复制模型/库。
- **端口闭集**：`llama-server` 只绑 `127.0.0.1:18081`；`language_serve` 只绑板 Tailscale 地址 `:18082`。不连接、不清理 46273。

### 0.2 记号（运行时解析）

| 记号 | 定义 |
|---|---|
| `$PY` | Air 执行检出根 `.venv-yoloe/bin/python`（只读使用，不装包） |
| 板端解释器 | `/usr/bin/python3`（B0a/mini R08：→ `/usr/bin/python3.12`，3.12.3）；一律 `-I -S -B` 调用（IR-M5 已采纳；只接受隔离意图，不声称板上 import 已证） |
| `$BOARD_TS` | `ssh -G Jetson \| awk '/^hostname /{print $2}'`（只读本机配置，不连接） |
| `$WEIGHTS` `$MMPROJ` `$LLAMA_BIN` 及 `EXP_*` | 第 0.3 节来源解析块输出（C2 Q4、mmproj、llama-server 的板端路径、期望字节与 sha） |
| `$EXP_HOST` | `sed -n '/^## Mac mini只读补核原始读数与逐维度用量/,$p' docs/evidence/P1-ENG-LOOP-002-precheck.md \| grep -m1 '^hostname=' \| cut -d= -f2` |
| `$OUT` | Air 本项输出根（执行检出内被忽略路径）`outputs/eng-loop2/P1-ENG-LOOP-002`，不进工作树 dirty 判据（IR-OPS-8：由仓库 `.gitignore` 精确一行 `/outputs/eng-loop2/` 忽略，同名提案「OPS基线与IR78裁定」§3） |
| `$UNIT` / `$CM` | SSH 计次单元号（1 准备 / 2 收据 / 3 Play）；该单元唯一主连接的控制套接字 `$OUT/ssh/cm-$UNIT`（第 0.5 节） |
| `$REL` / `$PASSED` | 第 1.0 节：固定已推送发布引用（40 位 SHA）/ 其上最新有效 `passed_candidate` |
| `$DOCWT` | 独立文档检出（`git worktree`，位于执行检出之外，第 1 节） |

### 0.3 Air 来源对齐（零消耗，本人执行；缺件即停）

Air 必须有与 Mac mini 相同的 JET C2 来源链原件；用户 `FACT:2` 已选 A：**新候选通过后**由本人从 mini 对齐（保持原字节与相对引用，附来源/完整性记录；角色不复制、不搬模型/库、不重跑诊断，该操作不扣 B-main Jetson 传输额度）。必要原件闭集（同名提案「R3六题答复落实」§3）：`outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/` 的 `state.json`、`budget.jsonl`、`checkpoint.json`，由 `state.board.step` 运行时定位的板步 `receipt.json` 及其所引原始 server/worker/monitor 流；已版本化的 `docs/evidence/P1-ENG-JET-001-stageb-transfer.json` 与 `-stageb-build-rerun.json` 随仓库到达。**缺任一即 STOP `S-PRECHECK`**。

解析块（执行检出根；标准库读 JSON，不 import 部署包）：附录 A 原样存为 `$OUT/prep/resolve-src.py`（正文逐字见 `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md`「附录 A 来源解析块」，本版未改），由下面的**来源加载块**（AC-10 修订 2）解析并加载：`src_resolve` 运行附录 A 写 `$OUT/prep/source.env`，须退出码 0、恰 10 行且末行 `RESOLVE_OK`；`src_load` 把其余 9 行过滤成有界普通文件 `$OUT/prep/source.vars`（过滤退出码 0；加载前逐行核闭集变量名各恰一次、值非空且逐字等于 `shlex.quote` 形式、总长 ≤ 8,192 B），先 `unset` 九个变量再 `set -a; . "$OUT/prep/source.vars"` 并核该 `.` 的退出码（`set +a` 不作加载成功凭据），加载后逐个核九个变量与文件值逐字一致。每步失败都打印 `STOP S-PRECHECK …` 并返回非 0，**不进入其后的任何 SSH、资产生成或服务**；合法来源的输出字节与变量值不变，来源选择不变。

来源加载块（逐字；在本单每个用到它的 bash 里先原样定义一次）：

```bash
SRC_NAMES="WEIGHTS EXP_WEIGHTS_SHA EXP_WEIGHTS_BYTES MMPROJ EXP_MMPROJ_SHA EXP_MMPROJ_BYTES LLAMA_BIN EXP_LLAMA_BIN_SHA EXP_LLAMA_BIN_BYTES"
src_check() {   # $1 = pre（加载前只核普通文件）| post（另核已加载变量与文件逐值一致）
  "$PY" -I -B -c '
import os, shlex, sys
mode, path, names = sys.argv[1], sys.argv[2], sys.argv[3].split()
data = open(path, "rb").read()
if not data or len(data) > 8192:
    sys.exit("STOP S-PRECHECK source_vars_size=%d" % len(data))
vals = {}
for line in data.decode("utf-8").splitlines():
    key, sep, raw = line.partition("=")
    try:
        tokens = shlex.split(raw)
    except ValueError:
        tokens = []
    if not sep or key not in names or key in vals or len(tokens) != 1 or not tokens[0] or raw != shlex.quote(tokens[0]):
        sys.exit("STOP S-PRECHECK source_vars_bad_line %r" % key)
    vals[key] = tokens[0]
missing = [n for n in names if n not in vals]
if missing:
    sys.exit("STOP S-PRECHECK source_vars_missing " + " ".join(missing))
if mode == "post":
    bad = [n for n in names if os.environ.get(n) != vals[n]]
    if bad:
        sys.exit("STOP S-PRECHECK source_load_mismatch " + " ".join(bad))
print("SOURCE_VARS_%s_OK" % mode.upper())
' "$1" "$OUT/prep/source.vars" "$SRC_NAMES"
}
src_resolve() {   # 解析：附录 A 退出码 0、恰 10 行、末行 RESOLVE_OK
  local rc n last
  "$PY" -I -B "$OUT/prep/resolve-src.py" > "$OUT/prep/source.env"; rc=$?
  n=$(wc -l < "$OUT/prep/source.env"); last=$(tail -n 1 "$OUT/prep/source.env")
  [ "$rc" -eq 0 ] && [ "$n" -eq 10 ] && [ "$last" = RESOLVE_OK ] \
    || { echo "STOP S-PRECHECK source_resolve rc=$rc lines=$n last=$last"; return 97; }
  echo SOURCE_RESOLVE_OK
}
src_load() {   # 过滤成有界普通文件 → 加载 → 逐值核一致；任一步失败即 STOP
  local rc n last
  n=$(wc -l < "$OUT/prep/source.env") && last=$(tail -n 1 "$OUT/prep/source.env") \
    && [ "$n" -eq 10 ] && [ "$last" = RESOLVE_OK ] \
    || { echo "STOP S-PRECHECK source_env_invalid lines=$n last=$last"; return 97; }
  grep -v '^RESOLVE_OK$' "$OUT/prep/source.env" > "$OUT/prep/source.vars"; rc=$?
  [ "$rc" -eq 0 ] || { echo "STOP S-PRECHECK source_filter rc=$rc"; return 97; }
  src_check pre || { echo "STOP S-PRECHECK source_vars_invalid"; return 97; }
  unset $SRC_NAMES
  set -a; . "$OUT/prep/source.vars"; rc=$?; set +a
  [ "$rc" -eq 0 ] || { echo "STOP S-PRECHECK source_load rc=$rc"; return 97; }
  src_check post || { echo "STOP S-PRECHECK source_load_inconsistent"; return 97; }
  echo SOURCE_LOAD_OK
}
```

**OPS 增量（SOURCE:2）**：本节机械核对由 `play_ops source`（以及 `prep`/`receipt`/`play` 开头）自动执行——取 mini 证据附录 A 原文运行、核退出码/恰 10 行/末行 `RESOLVE_OK`，再按 `src_check` 同一判据核 9 个变量；缺件或不符即 `STOP S-PRECHECK`，不复制、不替本人从 mini 对齐（`FACT:2` 本人对齐承诺不变；若需代理复制须先列原字节闭集/源与目的地/额度交用户签发）。下列手工块保留为同一判据的原文。

调用（本节；Air 本机零消耗）：`src_resolve && src_load; echo "source_rc=$?"`——须依次打印 `SOURCE_RESOLVE_OK`、`SOURCE_VARS_PRE_OK`、`SOURCE_VARS_POST_OK`、`SOURCE_LOAD_OK` 且 `source_rc=0`；否则按打印的 STOP 码停。该块逐项核 state.q4 → 板步收据 admitted → `server.argv --model`、transfer 清单 cls=G mmproj（唯一）→ 收据 `board_paths.mmproj` → `--mmproj`、build-rerun 批次目录 → 收据 `board_paths.server` → `argv[0]`；不按文件名/字节/mtime 猜双 Q4。

### 0.4 已签上限 / 当前可执行值 / 解锁门（逐维度；来源：账本 2026-10-07 完整 B-main 签发 + 同名提案「Mac mini四题答复落实」§2 表 + 「R3六题答复落实」§1–2；成功、失败、重试共账，耗尽即停）

| 维度 | 已签上限 | 当前可执行 | 解锁门 / 本单落点 |
|---|---|---|---|
| SSH 认证主连接 / 墙钟 | ≤3 条（准备 1、收据 1、Play 1；AC-10 修订 1(a)），每单元从主连接尝试前至全部通道及主连接关闭后 ≤3,600 s，累计 ≤10,800 s；失败尝试计次、不重试 | 0 | #1：G1、G2、G3、G5 后第 2 节；#2/#3：另加 G4 后第 3–5、9 节；通道闭集第 0.5 节 |
| ping | 0 | 0 | 不测网络 |
| session / 段重建 / 新 run ID | session ≤5（P1/P2/P3 各 1 + 环境性重试全局 ≤2、每剧本 ≤1，仅 Unity 未进 Play / 运行时锁冲突）；段重建每 session ≤2；新 run ID 0 | 0 | 第 10 节 |
| Play / 按钮墙钟 / `T_sess` | ≤5 次，每次 ≤420 s、累计 ≤2,100 s；`T_sess` ≤290 s 且守帧起点式 | 0 | 第 6、10、11 节 |
| 桌面 YOLO 加载 | 每 session ≤1、总 ≤5；段重建不新增 | 0 | 第 6 节 |
| 板服务启动 = GGUF 加载 | ≤2（收据 1；收据批次正常结束后 Play 批次 1）；**故障重启 0** | 0 | 第 4 节；第二次额度不是修故障重开 |
| 板推理尝试 | ≤335（收据 35 + 每 session ≤60 × 5）；**收据重测 0**；`POST /query` 每次计 1（含被拒/失败/超时），与其板内 chat 关联为同一次 | 0 | 第 5、9 节；代码计量见第 0.6 节 |
| 非推理 HTTP | ≤200，**两服务批次同一累计账**：每次 Air→板 `/status`、`/result/*`（含长轮询，每次计 1）及其他非推理请求、每次板内 loopback `/health`，成功与失败均计（AC-7 修订 2(b)、修订 3(b)） | 0 | 第 0.6 节分配与代码守账；就绪等待上限 300 s、间隔 0.25 s（现行值，预算可使其更早停止）；`/result` 长轮询每次 ≤4 s、每 query ≤16 次 |
| 板墙钟 / 服务驻留 | 累计 ≤10,800 s（准备与运行共账）；每次驻留 ≤3,600 s、被该单元完整覆盖、单元结束前必停 | 0 | 第 4、14 节 |
| 板新增峰值磁盘 | ≤200,000,000 B（`$BOARD_ROOT` 内 code/logs/可归属 cache、tmp）；不复制模型/库、不删件抵扣 | 0 | 第 3、4 节 `du -sb` 采样 |
| SSH 文件传输 | 双向 ≤20,000,000 B、≤3 批（部署 1、日志回传 ≤2）；stdin 读脚本与终端回显不计文件传输 | 0 | 第 3.5、4 节 |
| HTTP 有效载荷 | Air↔板 `language_serve` 请求体 + 响应体 ≤60,000,000 B，按访问日志逐行求和（含 result/status/异常/不完整）；loopback 不重复计为 Air 传输；不计 TCP/Tailscale 封装 | 0 | 第 11 节 |
| Air 归档 / 峰值 | 帧环 ≤140,000,000 B、会话目录 ≤85,000,000 B、每 Play ≤225,000,000 B；全批 ≤1,200,000,000 B；已归档 + 当前 runtime ≤1,450,000,000 B | 0 | 第 12 节；只移动不复制 |
| 正式归档零模型回放 | 实现**全批实际调用总上限 ≤3**（AC-10 修订 7 / B-main 评分资源修订 1 `SCORE:CHANGE:1`，替代原 ≤2；不是每归档/每摘要 3，成功/失败/超时/中止共账、调用前扣次、原账继承不重置）、独立复核 AC-18 ≤1；只读、不写 runtime | 0 | 第 12 节 |
| runtime 写入 | 覆盖文件生成 ≤5（每 session 1）、既有残留移动 ≤1；**无删除许可** | 0 | 第 3.1–3.2 节 |
| `--version` / 身份 | 资产核实 1 + 两次正常启动自核，共 ≤3；不含 `--help` | 0 | 第 3.4、4 节 |
| 其余 | 5060、外部模型 API、另列 GPU·h、云、下载、pip/安装/编译、模型或额外图像文件传板、新 scenario/run ID 各 0；系统/SSH/沙箱设置不改 | 0 | — |

### 0.5 SSH 计次单位与单元协议（AC-10 修订 1(a)；准备、收据、Play 三单元同一套函数，O-2/PR-10）

- **一次 SSH = 一条认证主连接**；准备、收据、Play 各 1 条，共 ≤3。单元内只经该主连接的控制套接字复用下表列齐的有限通道；**不允许任何单元另开直连 `ssh`**（原 mini 准备发起块的直接 `Popen ssh` 已废止，第 2 节改用本协议）。
- **禁止自动第四连接**：每个通道前先 `ssh -S "$CM" -O check Jetson`（只查本机控制套接字，不连板）；套接字缺失/失效即 `STOP S-SSH`（停全部后续，回接受/用户），不回退新认证、不重试。通道调用另加失败闭合选项：若套接字在检查后、调用前失效，ssh 的直连回退只能指向本机 `127.0.0.1:1`（`-o HostName=127.0.0.1 -o Port=1 -o ProxyCommand=none -o ProxyJump=none -o BatchMode=yes -o ConnectTimeout=3`）而被拒，不对板认证。**该回退闭合行为未运行验证**（本轮 SSH 0）；即使发生，也按实际新连接扣原账并停。
- **计时**：单元墙钟 = 主连接尝试前本机 epoch 至 `-O exit` 返回后本机 epoch；主连接建立失败也计 1 次、不重试。`-o` 只作用于本次调用，不写 SSH 配置；无后台推理服务（主连接是本机 ssh 客户端进程，不是板服务）。

逐字函数（每个单元开始时在 Air 的 bash 里定义一次；`$UNIT` 先设为 1/2/3）：

```bash
mkdir -p "$OUT/ssh" && chmod 700 "$OUT/ssh"
CM="$OUT/ssh/cm-$UNIT"; TALLY="$OUT/ssh/unit-$UNIT.tsv"
epoch() { "$PY" -c 'import time; print(f"{time.time():.6f}")'; }
unit_open() {
  test ! -e "$CM" || { echo "STOP S-PRECHECK stale_control_socket"; return 99; }
  printf 'unit\t%s\tmaster_attempt_epoch\t%s\n' "$UNIT" "$(epoch)" >> "$TALLY"
  ssh -o ControlMaster=yes -o ControlPath="$CM" -o ControlPersist=no \
      -o BatchMode=yes -o ConnectTimeout=20 -fN Jetson
  local rc=$?
  printf 'unit\t%s\tmaster_rc\t%s\tepoch\t%s\n' "$UNIT" "$rc" "$(epoch)" >> "$TALLY"
  [ "$rc" -eq 0 ] || { echo "STOP S-PRECHECK ssh_master_failed rc=$rc (counted, no retry)"; return 99; }
}
chan() {   # 用法：chan <通道名> [ssh 参数…] -- <远端命令>；stdin/stdout 原样透传
  local name=$1; shift
  ssh -S "$CM" -O check Jetson 2>>"$OUT/ssh/unit-$UNIT.check.log" \
    || { echo "STOP S-SSH control_socket_unavailable before $name"; return 99; }
  printf 'unit\t%s\tchannel\t%s\tstart\t%s\n' "$UNIT" "$name" "$(epoch)" >> "$TALLY"
  ssh -S "$CM" -o ControlMaster=no -o HostName=127.0.0.1 -o Port=1 -o ProxyCommand=none \
      -o ProxyJump=none -o BatchMode=yes -o ConnectTimeout=3 "$@"
  local rc=$?
  printf 'unit\t%s\tchannel\t%s\trc\t%s\tend\t%s\n' "$UNIT" "$name" "$rc" "$(epoch)" >> "$TALLY"
  return $rc
}
unit_close() {
  ssh -S "$CM" -O exit Jetson; local rc=$?
  printf 'unit\t%s\tmaster_exit_rc\t%s\tepoch\t%s\n' "$UNIT" "$rc" "$(epoch)" >> "$TALLY"
}
```

`chan` 的用法是 `chan <名> [-T|-t] Jetson '<远端命令>'`（`Jetson` 只用于匹配本机 `Host` 段，实际流量走 `$CM`）。**通道闭集**（名称、次数；表外通道一律不发）：

| 单元 | 通道（顺序；每个恰 1 次） | 合计 |
|---|---|---|
| #1 准备 | `prep-read`（第 2 节读脚本经 stdin，`-T`） | 1 |
| #2 收据 | `root-create`（3.3）→ `assets`（3.4）→ `deploy-tar`（3.5，传输批次 1）→ `deploy-expect`（3.5，同批次 1）→ `deploy-verify`（3.5–3.6）→ `serve`（第 4 节交互前台，`-t`）→ `logs-2`（传输批次 2） | 7 |
| #3 Play | `serve`（第 4 节交互前台，`-t`）→ `logs-3`（传输批次 3） | 2 |

单元结束前（`unit_close` 之前）必须已在 `serve` 通道内完成：服务已停、`ss -ltn` 证明 18081/18082 未监听、两模式 `pgrep` 均无匹配（rc=1；rc≥2 照记 UNKNOWN 并按 `S-SERVICE`）、`du -sb "$BOARD_ROOT"` 与 `df -B1 /home/jetson` 各一次；未释放或后台驻留 → `S-SERVICE`。

### 0.6 非推理 HTTP 与推理尝试的代码守账（AC-7 修订 2(b)、修订 3、修订 4）

**计量来源是代码，不是估算**：板端 `language_serve --backend llama-server` 必带 `--http-ledger "$BOARD_LOGS/http-ledger.jsonl"`（两批同一文件）与 `--non-inference-reserve <本批预留>`（第 4 节按单元固定为 25 / 11）。服务启动读入既有账行累计（上一批次的全部计数带入），写一行 `batch_start`；此后：

- 每次 loopback `/health` 尝试**发出前**核「已用 + 1 + 本批预留 ≤ 200」，不足即停、不发（退出码 6 = `S-ENVELOPE`）；每次尝试结束记一行结局（HTTP 码 / `error:` / `timeout:`）。起 `llama-server`（GGUF 加载）前若已无一次健康轮询的余量，直接退出 6、不加载。
- Air→板每个请求到达即入账（`POST /query` = 推理尝试；`GET /status`、`GET /result/<id>?wait_s=<w>` 与其他一切 = 非推理），行在请求结束时落盘，带 HTTP 码、错误与字节；`/result` 账行的 `query_id` 去掉查询串，与其 `POST /query` 按同一 `query_id` 关联。每个回包附 `http_budget` 快照（已含本次）。
- **`/result` 有界长轮询（AC-7 修订 3；其 (c) 现行读法为修订 4）**：只在已绑定六键 llama 身份的 `HttpAdapter` 与本服务 llama 分支之间使用。客户端每次发 `GET /result/<query_id>?wait_s=<w>`，`w = min(4 s, 本次 T_ret 剩余, 本次 T_hard 剩余)`（截到整毫秒；无正剩余即停、不发）；服务端同 query_id 完成/失败/stuck 时立即回、仍 pending/busy 则在 w 到期回，回包回显 `wait_s`（不回显即客户端判失败、不回退短轮询）。客户端不 sleep；每 query **至多 16 次** result 尝试（失败也计），任何时间、次数、预算边界先到即停，禁止第 17 次、HTTP 错误重试或回退短轮询。
- **截止与结果接纳（AC-7 修订 4；同名提案「R3冻结集裁定」§2 选 (i)，只替代修订 3(c) 的 I/O 读法及其证明方式对应文字，修订 3(a)(b)(d) 不变）**。修订 3(c) 现行逐字澄清文本：
  > 保持5s单次I/O上限，I/O随T_hard剩余收缩，即传给opener的timeout参数为min(5s, 本次T_hard剩余)；w随T_ret与T_hard两种剩余收缩，仍按修订3(a)取值。T_ret不作为在途单次I/O的timeout参数；回包后重新核T_ret/T_hard，不接纳逾期done。测量沿现行60s截止；Play的T_ret仍来自实际收据k_ret/hz，K派生式与原检查点/起点不改，不固定成4s或60s。健康300s/0.25s不改。4s及16次是已选执行边界，非目标设备性能通过线；ceil(min(T_ret,T_hard)/4)不是实际计量或完成保证。
  
  代码与具名测试（未改）：`controller/language_selector.py::HttpAdapter._long_poll_result` 以 `remaining_hard()` 调 `_call`，`_call` 传给 opener 的 timeout 为 `min(HTTP_IO_DEADLINE_S, deadline_s)`（5 s 与本次 T_hard 剩余取小）；`w` 同时受 T_ret 与 T_hard 剩余收缩；`tests/test_llama_server_adapter.py::LongPollClientTests.test_wait_is_min_of_4s_and_both_remaining_deadlines_and_io_tracks_t_hard` 断言 `w` 随两种剩余、I/O 随 T_hard。按同节裁定 (i) 的说明：若服务/链路不按 `w` 返回，软截止后仍可能在现行 I/O 窗口中等待，不承诺 T_ret 时刻立即返回；硬剩余与 `w` 相等时也不承诺消除网络竞速；原硬截止/fatal 与 HTTP 失败映射照旧。
- Air 客户端（`HttpAdapter`）每个请求**发出前**按最近快照核：`/result` 轮询与恢复用 `/status`（业务性）须「已用 + 1 + 预留 ≤ 200」；启动身份 `/status`（必需，由预留覆盖）须「已用 + 1 ≤ 200」；`POST /query` 须推理「已用 + 1 ≤ 335」且至少还能发一次业务轮询。不足即 `worker_stuck: S_ENVELOPE…` 并置 fatal、此后不发任何请求（会话按 `backend_fatal` 终止，原因文字含 `S_ENVELOPE` → 第 13 节 `S-ENVELOPE`；收据测量则按第 5 节非 0 即停）。服务端对越界请求另有同判据的 429 `S_ENVELOPE` 兜底（该请求已到达，照计）。
- 两批交接：批次 #2 结束、日志回传后，`http-ledger.jsonl` 留在 `$BOARD_LOGS`，批次 #3 以同一路径启动即继承累计；回传的副本用于 `-ledger.json` 汇总。不另给类别、次数或超时。

**各路径的有限次数与预留来源**（次数上界来自代码与已签上限；实耗以账行为准；表中没有任何一行是已核的目标设备最低或最坏事实）：

| 路径 | 批次 #2（收据） | 批次 #3（Play） | 次数上界的来源 |
|---|---|---|---|
| loopback `/health`（业务性） | `H2` = 就绪前实际尝试数 | `H3` 同口径 | 就绪等待上限 300 s 与间隔 0.25 s 只给时间边界；每次健康尝试另受 I/O 耗时与「已用 + 1 + 本批预留 ≤ 200」守账截断，**不把 300 s 读成 1,201 次，也不把旧规划 11 次当最低或最坏值** |
| 必需 `/status` | 操作者身份 `curl` 1 + 测量探针 `status_document` 1 + 测量适配器 `bind_identity` 1 = **3** | 操作者身份 `curl` 1 + 每 session（`bind_identity` 1 + `validate_jetson_session` 的 `status_document` 1）× ≤5 = **≤11** | 代码路径逐个列出（`tools/language_latency.py::jetson_adapter_factory`；`controller/language_loop.py::LanguageSession.__init__`、`validate_jetson_session`） |
| `POST /query`（推理） | ≤35（3 预热 + 32 计时，单轮；首个测量失败即停，第 5 节） | ≤60 × 实际 session 数，且两批合计 ≤335 | 已签上限；AC-15 修订 1；客户端发 POST 前守账 |
| `GET /result/<id>?wait_s=<w>`（业务性） | 每次推理 1…16 次；35 次推理的代码上界 16 × 35 = 560 | 每次推理 1…16 次；代码上界 16 × 实际推理数（Play 至多 16 × 300 = 4,800） | AC-7 修订 3(b)；两批上界都**远超总 200**，实际由每次请求前的 200 守账先截断 |
| 恢复用 `/status`（业务性） | **0**：第一次测量失败即停本轮，不再调用 `predict_one`（AC-15 修订 1(b)） | 每次 `predict_one` 调用至多 1 次（仅上一查询被放弃后、确认 idle 之前） | `HttpAdapter.predict_one`（`awaiting_idle` 分支） |
| 收尾 | 0（停止与释放核验走 SSH `serve` 通道的 `ss`/`pgrep`，不发 HTTP） | 0 | 第 4 节 |

**预留（`--non-inference-reserve`）的来源**：批次 #2 = **25** = 本批必需 `/status` 3 + 批次 #3 必需 `/status` 上界 11 + 批次 #3 健康轮询的规划分配 11；批次 #3 = **11** = 本批必需 `/status` 上界。两值沿用前版，不减少、不改健康节奏（「IR-N裁定」§1 末行）。其中「批次 #3 健康 11」只是分配给下一批的规划值，**不保证下一批能在 11 次内就绪**；代码不因本批必需 `/status` 已发生而递减预留（本批末尾因此多留至多 3 次）。

**两批实际守账式**：`H2 + H3 + status + result + 其他已发生非推理 ≤ 200`，每个请求前另守当时预留；先不足即 `S-ENVELOPE`，停全部新增业务动作、仅已签安全收尾，重测 0、重启 0。

**投影的更正（「IR-N裁定」§1；替代前版本节「现行轮询节奏下的投影」段）**：前版写「每次推理约 9–10 次 `/result`」「约 16–17 次推理即 `S-ENVELOPE`」「收据 35 次推理不能在 ≤200 内完成」与「35 × 6 = 210 已超过 200」——前三者是以未核实的 JET 旧时延（1.7–2.0 s，本机缺原件、未独立核实）推出的**投影**，不是已证事实或实测结论；第四条把 35 个 POST（推理账）与 175 个 GET（非推理账）加进同一个 200 分母，是混账，撤回。旧 0.2 s 节奏下按「首 GET 立即、I/O 忽略、完成时间恰为 L」的轮询数是 `1 + ceil(L/0.2)`，第几次 STOP 取决于逐行耗时/失败/预算快照。已证的只是**资源风险与已签停止要求**，不是本项不可执行的结论。本版改用长轮询后同样**不保证 35 次收据或 300 次 Play 请求全部做完**（上表第 4 行上界远超 200）；4 s 与 16 次是已选执行边界，不是目标设备性能通过线，`ceil(min(T_ret, T_hard)/4)` 不是实际计量或完成保证。若需按假设做条件算术，只按同名提案「IR-N裁定」§3「仅作条件算术」段解读，不作余额承诺，不借首次加载试探环境。

## 1. 接受放行核对（Air；严格双来源，AC-10 修订 1(b)；每个 SSH 单元前与每次 Play 前各做一次）

**OPS 增量（GATE:8）**：1.0–1.5 的机械部分由 `play_ops gate` 执行，并在每个单元开始前自动重跑（原流写 `$OUT/release/`）；脚本只做机械核对，不签接受/复核/权限门：1.1 的 checkout 仍由操作者关闭 Unity 后执行，1.6 的登记仍由当轮发令角色写 Unity 日志（机读行见第 0A 节，IR-OPS-2 已采纳），G4 仍须接受只读核清并在提案具名节写放行行（IR-OPS-1 已采纳）。

**两个检出**：执行检出 = Air 仓库主目录（Unity 打开的就是它），分离到 `$PASSED`、整树干净；文档检出 `$DOCWT` = 同一仓库的独立 `git worktree`，位于执行检出目录之外（例如仓库父目录下 `TetheredDroneTracking-docs`），只用于读取发布证据和登记 Unity 日志。复核文件与账本**只从固定发布引用读**，不读执行检出的工作树。

**1.0 解析并固定发布引用**（执行检出根；先 `git fetch origin`；本节输出全部原样存 `$OUT/release/<UTC>.txt`）。本块不以 `exit` 结束操作者 shell：任一判据不过即打印 `STOP S-PRECHECK …` 并置 `GATE=1`，末行只在 `GATE` 为 0 时打印 `RELEASE_GATE_OK`（R3-3）：

```bash
GATE=0; gate_stop() { echo "STOP S-PRECHECK $*"; GATE=1; }
[ -n "$OUT" ] && [ -x "$PY" ] || gate_stop out_or_py_unset   # $OUT/$PY 按第 0.2 节与第 2 节前置块先定义
mkdir -p "$OUT/release" || gate_stop release_dir_failed
git fetch origin
REL=$(git rev-parse origin/main)            # 固定为 40 位 SHA；本轮此后一律用 $REL，不再读 origin/main
REVIEW_TXT=$(git show "$REL":docs/reviews/P1-ENG-LOOP-002.md) || gate_stop review_file_unreadable
# 机读行真实写法：R1/R2/R3 §0 为「- `round_candidate: <sha>`（…）」，通过行为行首「passed_candidate: <sha>」；
# 两者都只认行首（可带 -/* 列表记号与反引号）的「键: 40 位小写十六进制」，正文里引用的键名不算
MR='^[[:space:]]*([-*][[:space:]]+)?`?'
LAST_ROUND=$(printf '%s\n' "$REVIEW_TXT" | grep -nE "${MR}round_candidate: [0-9a-f]{40}"'(`|[[:space:]]|$)' | tail -n 1)
LAST_PASS=$(printf '%s\n' "$REVIEW_TXT" | grep -nE "${MR}passed_candidate: [0-9a-f]{40}"'(`|[[:space:]]|$)' | tail -n 1)
LAST_ROUND_LINE=${LAST_ROUND%%:*}; PASS_LINE=${LAST_PASS%%:*}
LAST_ROUND_SHA=$(printf '%s\n' "$LAST_ROUND" | sed -nE 's/.*round_candidate: ([0-9a-f]{40}).*/\1/p')
PASSED=$(printf '%s\n' "$LAST_PASS" | sed -nE 's/.*passed_candidate: ([0-9a-f]{40}).*/\1/p')
printf 'rel=%s last_round_line=%s last_round_candidate=%s pass_line=%s passed_candidate=%s\n' \
  "$REL" "$LAST_ROUND_LINE" "$LAST_ROUND_SHA" "$PASS_LINE" "$PASSED"
[ -n "$LAST_ROUND_LINE" ] && [ -n "$LAST_ROUND_SHA" ] || gate_stop no_valid_round_candidate_line
[ -n "$PASS_LINE" ] && [ -n "$PASSED" ] || gate_stop no_valid_passed_candidate_line
[ -n "$LAST_ROUND_LINE" ] && [ -n "$PASS_LINE" ] && [ "$PASS_LINE" -gt "$LAST_ROUND_LINE" ] \
  || gate_stop "latest_round_not_passed last_round_line=$LAST_ROUND_LINE pass_line=$PASS_LINE"   # 最新一轮之后无通过行 = 后续未通过
[ -n "$PASSED" ] && git merge-base --is-ancestor "$PASSED" "$REL" || gate_stop passed_not_ancestor_of_rel
[ "$GATE" -eq 0 ] && echo RELEASE_REF_OK
# PLAY_GOVERNING 唯一定义见 workflow §4.4；下列路径是其逐项展开（含本项操作单），先核展开与 $REL 上的定义一致：
PG=(controller/ Assets/ tools/ tests/ config/ ProjectSettings/ Packages/packages-lock.json)
DEF=$(git show "$REL":docs/collaboration-workflow.md | grep -A2 '唯一权威定义')
for p in "${PG[@]}"; do printf '%s' "$DEF" | grep -qF "\`$p\`" || gate_stop "pg_definition_drift $p"; done
PG_DIFF=$(git diff --name-only "$PASSED" "$REL" -- "${PG[@]}" docs/evidence/P1-ENG-LOOP-002-play-ops.md); pg_rc=$?
printf 'pg_diff_rc=%s pg_diff_passed_to_rel=[%s]\n' "$pg_rc" "$PG_DIFF"
if [ "$pg_rc" -ne 0 ]; then gate_stop "pg_diff_failed rc=$pg_rc"; elif [ -z "$PG_DIFF" ]; then echo PG_DIFF_EMPTY_OK; else gate_stop play_governing_changed_after_pass; fi
git diff --name-only "$PASSED" "$REL"        # 其余差异原样记录（只应是规则许可的非 PLAY_GOVERNING 文档）
# 消耗性门状态（workflow §4.4；规则即 $REL 上 tools/check_docs.py 第 9 项的两个函数，从 $REL 导出原文件调用、不改工具）：
# 全部 docs/reviews/*.md（排除 README.md、*-prescreen.md、围栏代码块）按文件顺序配对 blocks/releases，
# 再按 finding-id 扣除账本「范围外已知缺陷」状态 RELEASED_SCOPE_GAP 的行；剩余任一未 release 的 block 即 STOP
CG_RC=99   # 导出失败时保持非 0
if CGT=$(mktemp -d "$OUT/release/cg-tree.XXXXXX") \
   && git archive "$REL" docs/reviews docs/implementation-status.md tools/check_docs.py | tar -xf - -C "$CGT"; then
"$PY" -I -B - "$CGT" <<'PYCG'
import importlib.util, json, sys
from pathlib import Path
root = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("rel_check_docs", root / "tools" / "check_docs.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
open_blocks = mod.open_consuming_gate_blocks(root / "docs" / "reviews")
released = mod.ledger_released_findings(root / "docs" / "implementation-status.md")
remaining = {}
for name, ids in open_blocks.items():   # 与 check_docs.py::check_consuming_gate_blocks 的账本扣除同式
    left = [f for f in ids if f not in released.get(name[: -len(".md")], set())]
    if left:
        remaining[name] = left
print("consuming_gate_open_blocks_by_file_order=" + json.dumps(open_blocks, ensure_ascii=False, sort_keys=True))
print("ledger_released_scope_gap=" + json.dumps({k: sorted(v) for k, v in released.items()}, ensure_ascii=False, sort_keys=True))
print("consuming_gate_unreleased=" + json.dumps(remaining, ensure_ascii=False, sort_keys=True))
sys.exit(4 if remaining else 0)
PYCG
CG_RC=$?
else gate_stop cg_export_failed; fi
case "$CG_RC" in 0) echo CONSUMING_GATE_OK ;; 4) gate_stop consuming_gate_blocked ;; *) gate_stop "consuming_gate_check_failed rc=$CG_RC" ;; esac   # 4 = 有未 release 的 block；其他非 0 = 导出/读取/解析失败，同样不放行
[ "$GATE" -eq 0 ] && echo RELEASE_GATE_OK || echo "STOP S-PRECHECK release_gate GATE=$GATE"
```

只有末行打印 `RELEASE_GATE_OK`（此前已分别打印 `RELEASE_REF_OK`、`PG_DIFF_EMPTY_OK`、`CONSUMING_GATE_OK`）、且整段无任何 `STOP` 行才继续；缺有效 `round_candidate`/`passed_candidate` 行、最新一轮之后没有通过行、通过候选不是 `$REL` 祖先、PLAY_GOVERNING 有差异，或消耗性门有未 release 的 block（含读取/解析失败）任一出现即不放行（O-1/PR-8：通过候选之后**任何** PLAY_GOVERNING 变化——含本操作单——都使旧通过行不能放行新版本；不再用 `grep -v '^docs/'` 过滤全部文档）。`grep -m1` 取首条通过候选会拿到旧候选，不得使用。消耗性门这一步与第 1.5 步的 `check_docs.py` 互不替代：后者只在状态板有未暂停 `Consuming=yes` 交接时才因未 release 的 block 拒绝，本步不看交接状态、直接按同一规则判门；`$CGT` 是 `$OUT` 下的导出副本，只读、不删。

| 步 | 命令 / 判据（执行检出根，除注明外） | 记录 |
|---|---|---|
| 1.1 | 关闭 Unity 编辑器后 `git checkout --detach "$PASSED"`；`git rev-parse HEAD` 原样输出，`test "$(git rev-parse HEAD)" = "$PASSED" && echo HEAD_EQ_PASSED_OK` | 原流存 `$OUT/release/` |
| 1.2 | `git status --porcelain --untracked-files=normal` 原样输出且为空（整个工作树、无路径过滤，含未跟踪；只有 `.gitignore` 忽略的路径不进该输出——`runtime/` 下除 `README.md` 外的产物与 `outputs/` 下逐个具名的工具输出根（本单 `$OUT` 所在 `/outputs/eng-loop2/`、诊断根所在 `/outputs/eng-loop/` 等），**没有**泛化忽略 `outputs/`，其他未跟踪路径照报 dirty（IR-OPS-8）；与会话/收据 `dirty` 判据同口径）；打开 Unity 后再核一次，Unity 改动任何已跟踪文件或产生未跟踪文件即停回接受 | 同上 |
| 1.3 | `if [ -e Assets/_Recovery ] || [ -L Assets/_Recovery ]; then echo "STOP S-PRECHECK unity_recovery_present"; else echo NO_UNITY_RECOVERY; fi`（PR-12：判存在性，不以 `ls` 无输出代替） | 同上 |
| 1.4 | 操作单与通过候选对应：`git show "$PASSED":docs/evidence/P1-ENG-LOOP-002-play-ops.md \| shasum -a 256` 与 `shasum -a 256 docs/evidence/P1-ENG-LOOP-002-play-ops.md` 相等（执行检出读到的就是通过版本） | 两行 sha |
| 1.5 | 账本条目在发布引用上存在：`git show "$REL":docs/authorizations.md \| grep -F '用户答 Mac mini 补核核清四题'`（B-main 完整信封与 N-3 十一码）与 `git show "$REL":docs/authorizations.md \| grep -F 'SLOT:FACT:1'`（窗口互斥确认）各命中；在 `$DOCWT`（检出 `$REL`）内 `python3 tools/check_ledger.py` 与 `python3 tools/check_docs.py` 通过 | 命中行与自检输出 |
| 1.6 | **Unity 日志登记（现场原流先于登记）**：把 1.0–1.5 的原流（含 1.1 的实际 `HEAD` 与 1.2 的实际 `status`，不是计划值）交当轮发令角色，在 `$DOCWT` 内（`git -C "$DOCWT" switch main && git -C "$DOCWT" pull --ff-only`）写入 `docs/unity-test-log.md` 本轮条目、提交并推送；该提交只增添规则许可文档。随后回执行检出**重做 1.1–1.4**，输出须与登记的原流逐行相同，否则停回接受 | 条目标题与推送后 SHA |

任一不过 → 不开 SSH/Play，回接受。日志提交之后若 `origin/main` 上出现影响有效通过行、其后门状态或 PLAY_GOVERNING 的变化，下一次单元/Play 前重新从 1.0 解析，不沿用旧 `$REL` 默示放行。**执行检出期间不写任何已跟踪路径**：全部原流、`-play.md` 草稿、资产与收据先落 `$OUT`（被忽略），整批结束（或 STOP 收尾）后在 `$DOCWT` 复制进 `docs/evidence/` 提交；否则会话/收据的 `dirty` 判据与 1.2 立即失效。

## 2. 准备 SSH（计次单元 #1；只读事实，零写板/零执行模型或部署代码）

- 前提：G1、G2、G3、G5；第 1 节放行核对通过。用途：补齐 `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` 第 1.2 节「事实缺口表」中可静态读取的缺口（Python 下层 C 模块内建/扩展与架构、扩展依赖库、site 钩子、包版本、L4T/驱动库记录、三文件现状、计划根、端口/残留进程、磁盘/内存）。只用非特权静态读命令；不 `sudo`、不改设置、不 import、不执行 `llama-server`（含 `--version`/`--help`）、不 HTTP、不写板、不传文件。
- **Air 本机零消耗前置**（不连接；任一失败即停，不开 SSH）：

```bash
OUT=outputs/eng-loop2/P1-ENG-LOOP-002; PY=.venv-yoloe/bin/python; mkdir -p "$OUT/prep"
date -u +%FT%TZ; hostname; sw_vers 2>/dev/null; "$PY" --version
ssh -G Jetson | grep -E '^(hostname|user|port|batchmode|connecttimeout|controlmaster|controlpath) '   # 不读私钥、不连接
for t in ssh tar shasum curl du git; do command -v "$t" >/dev/null || { echo "STOP S-PRECHECK tool_missing $t"; break; }; done
test ! -e runtime/scenario_config.json && echo NO_RESIDUAL_OVERLAY || echo RESIDUAL_OVERLAY_PRESENT   # 只记录；移动在 3.1
cat ProjectSettings/ProjectVersion.txt
"$PY" -I -c 'import sys; sys.path.insert(0, "."); from tools.language_latency import read_smoke_rows; r = read_smoke_rows("outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl", "outputs/eng-sft/P1-ENG-SFT-002/upload"); assert len(r) == 32, len(r); print("SMOKE_OK", len(r))' || echo "STOP S-PRECHECK smoke_set"   # 第 5 节收据输入；生产读取函数逐图核 frame_sha256，零模型
# 附录 A 存为 "$OUT/prep/resolve-src.py"（第 0.3 节），附录 B 存为 "$OUT/prep/assets-gen.py"（第 3.4 节），本单附录 P 存为 "$OUT/prep/prep-read.body.sh"
# 先原样定义第 0.3 节来源加载块（SRC_NAMES、src_check、src_resolve、src_load），再：
src_resolve && src_load; echo "source_rc=$?"   # 须 SOURCE_LOAD_OK 且 source_rc=0；否则 STOP，不生成 prep-read.sh、不开 SSH
EXP_HOST=$(sed -n '/^## Mac mini只读补核原始读数与逐维度用量/,$p' docs/evidence/P1-ENG-LOOP-002-precheck.md | grep -m1 '^hostname=' | cut -d= -f2)
{ printf 'EXP_HOST=%q\n' "$EXP_HOST"; grep -E '^(WEIGHTS|MMPROJ|LLAMA_BIN|EXP_[A-Z_]*_BYTES)=' "$OUT/prep/source.env"; cat "$OUT/prep/prep-read.body.sh"; } > "$OUT/prep/prep-read.sh"
bash -n "$OUT/prep/prep-read.sh" && shasum -a 256 "$OUT/prep/prep-read.sh"
```

- **单元 #1 发起**（第 0.5 节函数，`UNIT=1`；远端 900 s 限时；本机不另设限时进程，单元上限 3,600 s 由 `$TALLY` 起止 epoch 记账，超限照记 `S-ENVELOPE` 并按 STOP 收尾）：

```bash
UNIT=1   # 然后定义第 0.5 节函数
unit_open || exit 99
chan prep-read -T Jetson 'timeout -k 5 900 bash -s' < "$OUT/prep/prep-read.sh" > "$OUT/prep/prep.stdout" 2> "$OUT/prep/prep.stderr"
echo "prep_rc=$?"
unit_close
wc -c "$OUT/prep/prep.stdout" "$OUT/prep/prep.stderr"; shasum -a 256 "$OUT/prep/prep.stdout" "$OUT/prep/prep.stderr" "$TALLY"
grep -E '^(STOP |final=)' "$OUT/prep/prep.stdout"
```

- 读脚本正文逐字见本单**附录 P**（替代 mini 证据第 2.2 节旧版；PR-12：`readelf`/`ldd` 失败即停、扩展 `Machine` 须为 AArch64、`pgrep` 区分 rc 0/1/≥2）。命中 STOP 即刻结束本单元（脚本 fail-fast），保存已得原流；连接/认证失败计 1 次、不重试。
- **OPS 增量**：本节由 `play_ops prep` 执行（Air 前置、读脚本拼接、`bash -n`、单元 #1 主连接、`prep-read` 通道、关闭）；板端读脚本仍是附录 P 原文，命中 `STOP` 即停。
- 读齐也**在此停止**：交接受核清 → G4 放行；需动态无模型探测时只走另签的 `B-main:ENV:2`（草案见 mini 证据第 3 节），不挪用本单元或后续单元。
- 既有读数引用（不重读、不升级）：B0a（`-precheck.md`「B0a原始读数与逐维度用量」）、Mac mini 补核（同文件「Mac mini只读补核原始读数与逐维度用量」）。

## 3. B0b 准备（计次单元 #2「收据」内、启动服务之前；写入类）

**OPS 增量**：第 3–5 节由 `play_ops receipt` 在单元 #2 内按下列顺序执行（各步原命令、原判据与原因码不变；任一失败按第 13 节停，服务已启动则先按第 4 节停止与核释放、回传日志再关单元）。

先 `UNIT=2`、定义第 0.5 节函数、`unit_open || exit 99`；以下每个板端动作都经 `chan`（通道闭集第 0.5 节表），任何 `chan` 返回非 0 即按第 13 节停并 `unit_close`。

1. **H-8 残留（Air）**：`test ! -e runtime/scenario_config.json`；若存在 → `mkdir -p runtime/hold-acq-d1 && mv -n runtime/scenario_config.json runtime/hold-acq-d1/`（只移动、`-n` 不覆盖；计「残留移动」1/1；`hold-acq-d1/` 内已有同名文件即停回接受）。无删除许可。
2. **覆盖文件生成（Air；每 session 1 次，≤5）**：`"$PY" -c "import json;d=json.load(open('config/scenario.untethered.json'));d['sensor']['retained_frame_count']=1500;open('runtime/scenario_config.json','w').write(json.dumps(d,indent=2)+'\n')"`；`shasum -a 256 runtime/scenario_config.json` 原样记录。会话 `--body-scenario-config runtime/scenario_config.json` 逐值核对，缺失即 `ConfigMismatch`。
3. **计划根前提（通道 `root-create`；变量在 Air 展开）**：`chan root-create -T Jetson "test ! -e '$BOARD_ROOT' && test ! -L '$BOARD_ROOT' && mkdir -m 700 '$BOARD_ROOT' '$BOARD_CODE' '$BOARD_LOGS' && echo ROOT_CREATED"`；未打印 `ROOT_CREATED`（含已存在）→ `S-PRECHECK`（不覆盖、不删）。
4. **AC-16 板端资产核实（通道 `assets`；`--version` 1/3）**：先在本 bash 原样定义第 0.3 节来源加载块并 `src_load; echo "source_rc=$?"`（不重跑解析；须 `SOURCE_LOAD_OK` 且 `source_rc=0`，否则 `S-PRECHECK`：按第 13 节停并 `unit_close`，**不发 `chan assets`、不生成资产**）；再 `mkdir -p "$OUT/b0b"` 与 `chan assets -T Jetson "sha256sum -- '$WEIGHTS' '$MMPROJ' '$LLAMA_BIN'; '$LLAMA_BIN' --version 2>&1; echo rc=\$?" > "$OUT/b0b/assets-raw.txt"`；Air 由附录 B（mini 证据「附录 B 资产 JSON 生成块」，本版按 AC-7 修订 5 / AC-16 修订 1 改版本解析）生成 `$OUT/b0b/assets.json`：`GEN=$("$PY" -I -B "$OUT/prep/assets-gen.py" "$OUT/b0b/assets-raw.txt" "$OUT/b0b/assets.json"); gen_rc=$?; printf '%s\ngen_rc=%s\n' "$GEN" "$gen_rc"`，须 `gen_rc=0` 且末行 `ASSETS_OK`（三 sha 不等；版本身份行缺失、重复/冲突、两种格式都不符、缺明确 build、构建号超出 `^b[0-9]{1,7}$` 或 `rc` 非 0 → `S-IDENTITY`；来源变量缺失 → `S-PRECHECK`）。版本行两种格式：旧整数 `version: <整数> …` 取该整数；语义版本 `version: <语义版本> (build <整数>, commit <文本>)` 取括号内 build（本板现行原样输出得 `b0`；commit `unknown` 不作源码认证）。原样版本行随 `assets.json` 的 `runtime_version_line` 与原流 `assets-raw.txt`（含 `rc=`）保留，不进 `model_identity`。批次结束后才在 `$DOCWT` 复制为 `docs/evidence/P1-ENG-LOOP-002-assets.json`；JET 诊断读数不作 AC-16 证据。
5. **部署闭集传输（传输批次 1/3；通道 `deploy-tar` 与 `deploy-expect` 同批）**：执行检出根（HEAD = `$PASSED`、全树干净）
   `PATHS=$("$PY" -c "import json;print('\n'.join(json.load(open('config/p1-eng-loop-002-board-deploy.json'))['paths']))")`；
   `tar -cf "$OUT/b0b/deploy.tar" $PATHS && cp "$OUT/b0b/assets.json" "$OUT/b0b/expect-assets.json"`；记 `wc -c` 两文件；
   `chan deploy-tar -T Jetson "tar -xf - -C '$BOARD_CODE'" < "$OUT/b0b/deploy.tar"`；`chan deploy-expect -T Jetson "cat > '$BOARD_LOGS/expect-assets.json'" < "$OUT/b0b/expect-assets.json"`（同一批次计字节）。
   完整性（通道 `deploy-verify`，IR-M6 已采纳）：Air `shasum -a 256 $PATHS > "$OUT/b0b/air.sha"`；`chan deploy-verify -T Jetson "cd '$BOARD_CODE' || exit 97; sha256sum -- $(printf '%q ' $PATHS); du -sb '$BOARD_ROOT'; df -B1 /home/jetson" > "$OUT/b0b/board-verify.txt"`；两者 sha 行逐行相等（不等 → `S-IDENTITY`）。桌面 `"$PY" -m tools.eng_loop2.deploy_digest --root .` 记 `serve_code_sha256`（板端值由服务 `/status` 自算，在第 5 节收据比较）。
6. 第 3.5 步 `deploy-verify` 输出即本步的 `du -sb "$BOARD_ROOT"`、`df -B1 /home/jetson` 采样。

## 4. 板上服务启动、身份核对与停止（代理/脚本经 `play_ops` 持有的可见前台 SSH 子进程，OPS:ACTOR:1；单元 #2 与 #3 的 `serve` 通道各 1 次 = GGUF 加载 ≤2，故障重启 0）

**OPS 增量**：`play_ops` 在 `serve` 通道开交互 bash（`-tt`，`exec bash --noprofile --norc -i`），逐行键入下块（`PS1=; PS2=` 只关提示符；服务命令与 `echo "serve_rc=…"` 在同一行），从输出流识别 `language-serve listening on http://$BOARD_TS:18082` 后做身份核对；停止时发送一次 Ctrl-C（`\x03`），读到 `serve_rc=` 后在同一会话键入释放核对（`ss`/两次 `pgrep`/`du`/`df`），再 `exit`。早退按下文退出码分流；监听端点不符按 `S-IDENTITY`；释放不可证明按 `S-SERVICE`（不清未知进程）。**该前台监督未在真实板上运行验证。**

**启动前提**：G1–G5 全过。`llama-server` 的十项资源旗标由代码逐字固定（AC-7 修订 2(a)），本单不另加旗标；`/result` 长轮询由本服务 llama 分支自动启用（AC-7 修订 3），本单不另加参数。

```bash
# 用户在 Air：chan serve -t Jetson     （复用本单元主连接的交互会话）；进入后先：
exec bash --noprofile --norc
set -o pipefail
N=2        # 单元 #2（收据）写 2；单元 #3（Play）写 3。下一行把预留固定为第 0.6 节的值，其余输入一律 STOP
case "$N" in 2) R_N=25 ;; 3) R_N=11 ;; *) echo "STOP S-PRECHECK bad_unit N=$N"; exit 97 ;; esac
cd /home/jetson/eng-loop2/code || exit 97          # O-5：cd 失败立即结束会话，不在错误目录继续
umask 077; date -u +%FT%TZ; echo "unit=$N reserve=$R_N"
# 逐个 export 第 0.2–0.3 节解析值：BOARD_ROOT BOARD_CODE BOARD_LOGS BOARD_TS WEIGHTS MMPROJ LLAMA_BIN（只读赋值，不落脚本文件）
mkdir -p "$BOARD_LOGS/tmp" "$BOARD_LOGS/cache/llama" "$BOARD_LOGS/cache/cuda" "$BOARD_LOGS/scratch" || exit 97
SS=$(ss -ltn 2>&1); ss_rc=$?; printf '%s\nss_rc=%s\n' "$SS" "$ss_rc"   # R3-2：先捕获 ss 输出与退出状态
[ "$ss_rc" -eq 0 ] && [ -n "$SS" ] || { echo "STOP S-PRECHECK ss_failed rc=$ss_rc"; exit 97; }   # ss 非 0 或无输出 → 停在服务启动前
PORTS=$(printf '%s\n' "$SS" | awk '$4 ~ /:(18081|18082)$/ {print $4; f=1} END {exit f ? 0 : 1}'); port_rc=$?   # 0 占用 / 1 空闲 / 其余 awk 失败
case "$port_rc" in 0) echo "STOP S-PRECHECK port_occupied $PORTS"; exit 97 ;; 1) echo PORTS_FREE_OK ;; *) echo "STOP S-PRECHECK port_check_failed rc=$port_rc"; exit 97 ;; esac
pgrep -a -f llama-server; r1=$?; pgrep -a -f language_serve; r2=$?
[ "$r1" -eq 1 ] && [ "$r2" -eq 1 ] || { echo "STOP S-PRECHECK residual_or_pgrep_rc=$r1/$r2"; exit 97; }
env | grep -E '^(LLAMA_|GGML_|MTMD_|HF_|HUGGINGFACE_)|_proxy=|_PROXY='     # 原样记录；每个命中名写成 -u <名> 组成 UNSETS（无命中则为空）
env $UNSETS \
   TMPDIR="$BOARD_LOGS/tmp" XDG_CACHE_HOME="$BOARD_LOGS/cache" LLAMA_CACHE="$BOARD_LOGS/cache/llama" \
   CUDA_CACHE_PATH="$BOARD_LOGS/cache/cuda" CUDA_CACHE_MAXSIZE=134217728 \
   /usr/bin/python3 -I -S -B tools/language_serve.py --backend llama-server \
   --llama-bin "$LLAMA_BIN" --weights "$WEIGHTS" --mmproj "$MMPROJ" --llama-port 18081 \
   --expect-assets "$BOARD_LOGS/expect-assets.json" --access-log "$BOARD_LOGS/access-$N.jsonl" \
   --http-ledger "$BOARD_LOGS/http-ledger.jsonl" --non-inference-reserve "$R_N" \
   --scratch "$BOARD_LOGS/scratch" --llama-ready-timeout-s 300 \
   --host "$BOARD_TS" --port 18082 2>&1 | tee -i "$BOARD_LOGS/serve-$N.log"
echo "serve_rc=${PIPESTATUS[0]}"; date -u +%FT%TZ          # 服务退出码取管道首段，不取 tee 的
```

`N` 只取 2 或 3（`case` 之外即 STOP），`R_N` 由 `N` 机械派生（第 0.6 节「预留的来源」：25 / 11），不手填。就绪等待用现行上限 300 s（`DEFAULT_LLAMA_READY_TIMEOUT_S`）与 0.25 s 间隔；预算不足会更早以退出码 6 停止，300 s 不等于可发 1,201 次请求。下文 Air 侧命令用本单元的 `$UNIT`（2 或 3；与板端 `N` 相同）。

- 退出码：3 = 资产/构建号/量化/部署闭集不符或 `--http-ledger` 不可读/损坏/与前一批上限不一致 → `S-IDENTITY`；**4（未就绪）/5（服务期间 llama-server 退出）= 首次主臂失败 → 停全部后续、回用户，故障重启 0**，不以缺 `backend_fatal` 事件继续；**6 = 非推理 HTTP 预算不足 → `S-ENVELOPE`**（停新增动作，按已签收尾）。
- **身份核对（Air，必需 `/status` 计 1）**：`curl -s --noproxy '*' --max-time 5 "http://$BOARD_TS:18082/status" | tee "$OUT/status-$UNIT.json"`；`model_identity` 六键齐、`serve_code_sha256` 等于第 3.5 步桌面值、`machine` 原样记录、`http_budget` 原样记录（`batch` 应为 `$UNIT − 1`，即第一次启动为 1、第二次为 2）；不可达/不符 → 停全部（HTTP 不可达不作环境性重试理由）。
- **停止与释放（同一交互会话）**：前台 Ctrl-C；`ss -ltn`（18081/18082 均不在）、`pgrep -a -f llama-server; echo rc=$?; pgrep -a -f language_serve; echo rc=$?`（均须 rc=1；rc≥2 记 UNKNOWN 并按 `S-SERVICE`）、`du -sb "$BOARD_ROOT"`、`df -B1 /home/jetson`、`date -u +%FT%TZ`；服务起止时刻逐次记录，单次驻留 ≤3,600 s 且在本单元结束前。未释放/后台驻留 → `S-SERVICE`（本人在已签前台收尾范围内停止并核端口，不新开服务、不清未知进程，释放不可核照记 UNKNOWN）。然后 `exit` 结束 `serve` 通道。
- **日志回传（通道 `logs-$UNIT`；传输批次 2 或 3）**：服务停止后 `chan "logs-$UNIT" -T Jetson "tar -cf - -C '$BOARD_LOGS' access-$UNIT.jsonl serve-$UNIT.log http-ledger.jsonl expect-assets.json" > "$OUT/board-logs-$UNIT.tar"`；记字节。随后 `unit_close`。
- 第二次启动（单元 #3）只在单元 #2 收据退出码 0 且服务正常停止、释放已核后使用；不是失败后重开。

## 5. K 收据（AC-15 及修订 1；单元 #2 内服务就绪后；生产路径生成，不手写 JSON；收据重测 0）

**逐步检查退出码**（AC-15 修订 1(c)）：`measure` 非 0 即停，不执行 `k-receipt`、不开 Play；只有 `measure` 为 0 才执行 `k-receipt`，后者 0/6/8 原语义。两条命令不得用 `;`/`&&` 串成一行无条件续跑。

```bash
mkdir -p "$OUT/k-receipt" || exit 97
"$PY" -m tools.language_latency measure --host jetson --backend http --server-url "http://$BOARD_TS:18082" \
  --model-form c2-merged --smoke outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl \
  --package-root outputs/eng-sft/P1-ENG-SFT-002/upload --runtime runtime \
  --out "$OUT/k-receipt/jetson-report.json" > "$OUT/k-receipt/measure.stdout" 2> "$OUT/k-receipt/measure.stderr"
MEASURE_RC=$?; echo "measure_rc=$MEASURE_RC"
if [ "$MEASURE_RC" -ne 0 ]; then
  echo "STOP measure_rc=$MEASURE_RC: no k-receipt, no Play (report/stdout/stderr kept as is)"
  "$PY" -c 'import json,sys; r=json.load(open(sys.argv[1])); f=[x for rd in r.get("rounds",[]) for x in rd.get("failures",[])]; print("verdict=%s load_error=%s first_failure=%s" % (r.get("verdict"), r.get("load_error"), json.dumps(f[:1])))' "$OUT/k-receipt/jetson-report.json"
else
  "$PY" -m tools.language_latency k-receipt --single-host jetson \
    --report "$OUT/k-receipt/jetson-report.json" --runtime runtime \
    --out "$OUT/k-receipt/jetson-k-receipt.json" > "$OUT/k-receipt/k-receipt.stdout" 2> "$OUT/k-receipt/k-receipt.stderr"
  KRECEIPT_RC=$?; echo "k_receipt_rc=$KRECEIPT_RC"
fi
```

- **smoke 集**：与 LOOP-001 K 收据同一份 32 行 smoke（`outputs/eng-sft/P1-ENG-SFT-002/data/smoke.jsonl`，图像根 `outputs/eng-sft/P1-ENG-SFT-002/upload`；执行检出内被忽略路径，不进 dirty 判据），即提案 §3.2「现行同口径」；`read_smoke_rows` 按行内 `frame_sha256` 逐图核实；第 2 节 Air 前置已用同一函数核过一次（缺件或不符 → `S-PRECHECK`，回接受，不另选样本）；此处若仍报错退出（非 0、非 7）按下条停全部。报告原样记 `smoke_sha256` 与 32 个 `row_id`。
- **`measure` 单轮**（AC-15 修订 1(a)(b)）：jetson 生产入口 `max_rounds=1`，正常轮 3 预热 + 32 计时 = 35 次推理；首轮 `INVALID`/`FAIL` 不自动新建第二轮适配器、不再 bind/`/status`、不再推理；首个测量失败（`SelectorError` 或固定 60 s 测量截止）后停止本轮剩余调用，报告保留已得原样本与失败原因、记 `not_attempted` 与 `stopped_after_first_failure`，不足 32 个计时样本不出 p95；`/status` 身份探针失败同样落 `FAIL` 报告、零推理。正常返回的三态/`parse_error` 照记，不是失败、不另设 STOP 线。
- **`measure` 非 0 的分流**（不得写成 `k-receipt` 退出 6）：退出 7（报告 `verdict` 非 OK）→ 首个失败的 `detail` 以 `S_ENVELOPE` 开头 → 第 13 节 `S-ENVELOPE`；其余（`timeout`/`worker_died`/`worker_stuck`/`load_failure` 等）→ 第 13 节「首次服务/HTTP 失败停全部」（回用户，重测 0、故障重启 0）。退出码既非 0 也非 7（例如报告未写出）→ 同样停全部、回用户，原样保存 stdout/stderr。实际少于 35 的失败批如实记账，不填补、不过滤失败行，不生成合格 p95/收据。
- **`k-receipt`**：退出 0 才可进 Play；6（报告缺失/不全/身份或部署摘要与重算不符）或 8（`K_ret + K_conf + K_pub > R − 8`）、或 `response_format` 被服务拒绝 → `S-RECEIPT`：停全部后续、回用户；**重测 0、5060 分支 0**。
- 本批请求的次数上界与守账见第 0.6 节（长轮询每次推理 1…16 次 `/result`，不保证 35 次全部做完）。任何失败行/`S_ENVELOPE` 照记不过滤。批次结束后才在 `$DOCWT` 把收据与报告复制为 `docs/evidence/P1-ENG-LOOP-002-k-receipt-jetson.json` + 报告。无论成功或停止，随后都按第 4 节停服务、核释放、回传日志、`unit_close` 结束单元 #2；只有 `k_receipt_rc=0` 才在其后开单元 #3。

## 6. 会话命令与 `T_sess`（单元 #3 内，服务再次就绪并通过第 4 节身份核对后）

```
SID=<loop2-p1|loop2-p2|loop2-p3>[-r1]
$PY -m controller.language_loop run --session-id $SID \
  --session-root $OUT/play/sessions --runtime runtime --allow-shared-runtime \
  --backend http --server-url http://$BOARD_TS:18082 --model-form c2-merged \
  --k-receipt $OUT/k-receipt/jetson-k-receipt.json \
  --tracker det-assoc-v1 --resident --condition follow --ground-plane-y-m 0.2 \
  --body-policy standoff --body-planner-config config/p1-eng-frame-001-body.json \
  --body-scenario-config runtime/scenario_config.json --scenario-id deterministic-loop-untethered \
  --planned-duration-s <T_sess> 2>&1 | tee $OUT/play/$SID.session-process.log
```

- **OPS 增量**：`play_ops play` 在本人按 Play 后、以 `latest.json` 指向帧旁车 `capture_unix_s` 晚于等待起点判定开始出帧（120 s 内未出帧 → 记 Unity 未进 Play 的环境性原因并停，不自动重试），读 f₀、按下式算 `T_sess` 后以上述原命令起会话（前台子进程，输出写 `$OUT/play/$SID.session-process.log`）。出帧/会话 TERMINAL/网页时刻都不冒充 Unity 按钮时刻（按钮起止无可靠来源记 UNKNOWN）。**工具截止 = 开始等待本人 Play 的时刻 + 420 s**（等待 Play 不延长按钮墙钟；轮次 `OPSC6返工`）：截止时会话仍在运行、或会话结束后出帧仍未静止 → `S-WALL`（按钮起止 UNKNOWN，不能证明 ≤ 420 s，fail-closed）。
- `T_sess ≤ (1490 − f₀)/5` s（f₀ = 会话起点 Unity 帧号，起会话前读 `runtime/frames/latest.json` 的 `frame_id`），且 ≤ 290 s。
- 会话启动校验（§3.2）任何不符 → `ConfigMismatch` 拒启（host/sha/`transport`/端点/身份六键/`scenario_id`/hz/R/`git_head`/整个工作树干净/`machine`/部署摘要/`response_format`/`decode`/`prompt`）→ `S-IDENTITY`。
- 会话 `TERMINAL` 原因闭集：`operator_stop` / `duration_reached` / `backend_fatal`（`S-BACKEND`，**首次即停本次及全部后续**）/ `rebuild_limit`（`S-REBUILD`）。**会话 `TERMINAL` 不等于 Unity 已退出 Play**：操作者按停止按钮并记时刻。
- 单加载：每个段目录 `model_cache.json` 的 `model_loads` 必须为 1（> 1 → `S-LOAD`）。
- 会话 `TERMINAL(backend_fatal)` 且原因文字含 `S_ENVELOPE`（客户端预算守账或服务端 429 兜底）→ 第 13 节 `S-ENVELOPE`；其余 `backend_fatal` → `S-BACKEND`。两者都停本次及全部后续新增动作。

## 7. B/C 派生输出与预登记文字描述（§3.6）

由 `$PY -m tools.eng_loop2.analyze_play derive-bc` 运行时计算（几何文件 `group == "vehicle"`、锚点 xz 40 m 内、从 Play 起始位姿合成居中相机时离天底角 ≤ `gimbal.maximum_off_nadir_deg` 且全几何投影状态 `OK`、按 xz 距离升序取前两辆）；**得 < 2 辆即停并回接受**。阶段 A 运行结果见下节「阶段 A 派生读数」（逐字取自命令输出）。

### 阶段 A 派生读数（`derive-bc` 输出逐字摘录；退出码 0，status `OK`）

起始相机位置 [132.0, 25.2, 117.0]（锚点 + `drone.initial_altitude_m` 25.0 m）；池半径 40.0 m；离天底角上限 45.0°。

| scene_object_name | xz 距离 m | 离天底角 ° | 全几何投影 | 入选资格 |
|---|---|---|---|---|
| `Vehicle_SUV_color01 (1)` | 6.711 | 15.58 | OK | 是 |
| `Vehicle_Taxi (2)` | 9.344 | 21.29 | OK | 是 |
| `Vehicle_Container_color02 (2)` | 26.611 | 49.01 | OK | 否 |
| `Vehicle_SUV_color01 (4)` | 35.947 | 56.19 | OK | 否 |
| `Vehicle_Container_color01` | 36.862 | 57.9 | OK | 否 |
| `Vehicle_Car_color01` | 37.09 | 56.98 | OK | 否 |

- **B** = `Vehicle_SUV_color01 (1)`，预登记描述 **"the suv"**；**C** = `Vehicle_Taxi (2)`，预登记描述 **"the taxi"**（描述只由对象名派生：去掉 `Vehicle_` 与 `colorNN` 变体编号；`colorNN` 不是颜色，派生不出颜色词）。
- Play 前须在 Unity 主机重跑同一命令并逐字核对上表；得 < 2 辆 → 停并回接受。**OPS 增量**：由 `play_ops plan` 执行（独立进程跑原 `derive-bc`，与本节上方两行 B/C 读数逐字比较，冻结计划只取对象名与描述文字；几何结果不进任何在线判断）。
- **已知选择风险（如实保留，不改规则）**：池内另有 `Vehicle_SUV_color01 (4)`（同为 SUV），P1 中 "the suv" 的候选预览若出现两个相符对象，按第 8 节规则只能 `reject`；该次照记、不重问、不改描述。

## 8. 只凭运行时画面的操作者规则（§3.6，AR1-1；N-5 已批）

- 每次 `ask`/`respecify` 前，操作者只看网页「实时画面」确认意图对象在画面内：在 → 点「发送」；不在 → 点「跳过（不在画面）」，记 `SKIPPED_NOT_IN_VIEW`（不发请求、不成样本，自动摘要逐次列出）。不点不发：程序、检测器或真值不代人判断可见性，无点击只等原截止/安全收尾（OPS:SAMPLING:3）。
- 候选选择只看网页「候选预览」（绑定源帧原图字节）与第 7 节预登记文字描述：恰一个候选相符 → 点「确认序号 <i>」；零个或多个 → 点「拒绝」。预览须浏览器实际显示成功才可确认；截止过后只禁确认（不自动拒绝、不重问）。不提供数字键/R/聊天转交确认路线。
- 疑似/丢失（OPS:SUSPECT:5）：只自动记录 `SUSPECTED`/`LOST` 与原显式报告，不提供也不自动发 `confirm-lost`/`dismiss`，不为制造丢失新增遮挡/搜索/重问。
- 离线真值与 IoU 只在评分脚本内使用，不得用于任何 Play 中的人工决定。
- 采样批准来源：账本 2026-10-06「P1-ENG-LOOP-002 — 用户就 D3 退修选 U-D3 (a) 继续修订，并批准 N-5 D3 的 P1 采样顺序」；限制原样保留（不外推、数字只描述）。

## 9. 三剧本逐字命令（每条命令前按第 8 节判定；全部参数逐字写出，令牌运行时解析、不手抄）

**OPS 增量（O2）**：下列命令是 `play_ops` 冻结计划逐字展开的原命令，运行中**只由工具/网页发出**（一次提交记录，不手工另开终端执行）：每条 ask/respecify 等本人「发送/跳过」；`confirm`/`reject` 的令牌取当时呈现结果的 `result_id`（网页绑定）；「观察 ≥ 15 s」与红车「跟 ≥ 20 s」按会话原流事件锚点计时（IR-OPS-6 已采纳：仅 confirm/reject 受理后观察，锚点是该 request_id 的会话 receipt 写盘时刻；跟随从该选择之后**同纪元**首个 TRACKING 状态事件起，未进入则从选择时刻起并记跟随未验证；拒绝、带拒收细节的 confirm（未播种）与旧纪元 TRACKING 不算新指定已跟随；原流 5 s 内不可绑定即 UNKNOWN 停依赖，**不以 CLI 返回、网页点击或轮询发现时刻补值**；`NO_CANDIDATE`/`NO_DECISION`/`SKIPPED_NOT_IN_VIEW` 不开观察窗，直接列下一既定步骤待本人发送/跳过）；P3 的 `release` 只在 TRACKING 且 `track_id` 仍等于该步确认后建立的那个时才发，否则记未发与原因；剧本末 `stop` 与网页「停止会话」合计每会话至多一次。模型 none/错误/本人拒绝/未 TRACKING 一律记实际结局、不追加请求；结果未知（超时/WRITER_BUSY/缺回执）即停依赖推进、不换 id 重发。

在 Unity 主机仓库根、与第 6 节会话同一 `$PY`/`$SID` 的另一终端执行。先定义三个只读取值函数（逐字）：

```bash
OPS=(--session-id "$SID" --runtime runtime --allow-shared-runtime)
status_json() { "$PY" -m controller.language_loop status --runtime runtime; }
designate_token() { status_json | "$PY" -c 'import json,sys; r=json.load(sys.stdin)["last_result"]["result"]; assert r["purpose"]=="designate" and r["status"] in ("unique","ambiguous"), (r["purpose"], r["status"]); print(r["result_id"])'; }
pointer_token() { status_json | "$PY" -c 'import json,sys; t=json.load(sys.stdin)["tracker_state"]["tracker_state"]; assert t["state"]=="TRACKING" and t["track_id"], (t["state"], t["track_id"]); print(t["track_id"])'; }
```

- `designate_token`：当前呈现中的指定结果 `result_id`（`confirm`/`reject` 的 `--token`）；断言不成立即不发命令，照记。
- `pointer_token`：当前指针 `track_id`（`release` 的 `--token`）。
- `<i>`：候选预览图上按第 8 节规则选中的候选序号（0 起）；`<B>`/`<C>` 与描述取第 7 节运行时派生输出（阶段 A 读数：`Vehicle_SUV_color01 (1)` "the suv"、`Vehicle_Taxi (2)` "the taxi"；Play 前重跑核对）。
- 每条命令的回执（`status_json` 的 `tracker_state.last_request`）与 `SKIPPED_NOT_IN_VIEW` 判定逐条记入第 11 节模板。（`status_json` 读本机 runtime，不是板端 HTTP。）

**P1（B→C→red→B；N-5 已批采样顺序）**：

```bash
"$PY" -m controller.language_loop ask "the suv" --intent "Vehicle_SUV_color01 (1)" "${OPS[@]}"
"$PY" -m controller.language_loop confirm <i> --token "$(designate_token)" "${OPS[@]}"   # 或零个/多个相符：
"$PY" -m controller.language_loop reject --token "$(designate_token)" "${OPS[@]}"
# 观察 ≥ 15 s
"$PY" -m controller.language_loop ask "the taxi" --intent "Vehicle_Taxi (2)" "${OPS[@]}"
"$PY" -m controller.language_loop confirm <i> --token "$(designate_token)" "${OPS[@]}"   # 或 reject（同上）
# 观察 ≥ 15 s
"$PY" -m controller.language_loop ask "the red car" --intent red_car "${OPS[@]}"
"$PY" -m controller.language_loop confirm <i> --token "$(designate_token)" "${OPS[@]}"   # 或 reject（同上）
# 跟 ≥ 20 s
"$PY" -m controller.language_loop ask "the suv" --intent "Vehicle_SUV_color01 (1)" "${OPS[@]}"   # 不在画面 → 不发，记 SKIPPED_NOT_IN_VIEW
"$PY" -m controller.language_loop confirm <i> --token "$(designate_token)" "${OPS[@]}"   # 或 reject（同上）
# 观察捕获 ≥ 15 s（记录实际结局，不预设 TRACK_ENDED）
"$PY" -m controller.language_loop stop "${OPS[@]}"
```

**P2（含混指令）**（`<P2 对象>` = Play 前在 `-play.md` 预登记的对象名，取 `red_car` 或第 7 节派生的 B/C 之一，登记后不改）：

```bash
"$PY" -m controller.language_loop ask "the car" --intent "<P2 对象>" "${OPS[@]}"
# 记录实际 VLM 三态与候选（status_json 的 last_result）；有候选时按第 8 节二选一：
"$PY" -m controller.language_loop confirm <i> --token "$(designate_token)" "${OPS[@]}"
"$PY" -m controller.language_loop reject --token "$(designate_token)" "${OPS[@]}"
# 无候选（none/失败）时不发 confirm/reject，直接下一条
"$PY" -m controller.language_loop respecify "the red car" --intent red_car "${OPS[@]}"
"$PY" -m controller.language_loop confirm <i> --token "$(designate_token)" "${OPS[@]}"   # 或 reject（同上）
# 观察 ≥ 15 s
"$PY" -m controller.language_loop stop "${OPS[@]}"
```

**P3（逐次延迟，同一 Play；Δ 依次 0 / 2 / 4 s）**：

```bash
"$PY" -m controller.language_loop ask "the red car" --intent red_car --delay-s 0 "${OPS[@]}"
"$PY" -m controller.language_loop confirm <i> --token "$(designate_token)" "${OPS[@]}"   # 或 reject（同上）
# 观察 ≥ 15 s
"$PY" -m controller.language_loop release --token "$(pointer_token)" "${OPS[@]}"   # 未处于 TRACKING 时不发，照记
"$PY" -m controller.language_loop ask "the red car" --intent red_car --delay-s 2 "${OPS[@]}"
"$PY" -m controller.language_loop confirm <i> --token "$(designate_token)" "${OPS[@]}"   # 或 reject（同上）
# 观察 ≥ 15 s
"$PY" -m controller.language_loop release --token "$(pointer_token)" "${OPS[@]}"
"$PY" -m controller.language_loop ask "the red car" --intent red_car --delay-s 4 "${OPS[@]}"
"$PY" -m controller.language_loop confirm <i> --token "$(designate_token)" "${OPS[@]}"   # 或 reject（同上）
# 观察 ≥ 15 s
"$PY" -m controller.language_loop stop "${OPS[@]}"
```

注：Δ > 0 时结果到达后挂起 Δ 才呈现，呈现前 `designate_token` 的断言不成立（`last_result` 仍是上一结果或为空），等呈现后再取；`confirm` 在挂起中按现行回执 `REQUEST_INVALID(confirm_in_QUERYING)`。`--delay-s` 域 [0, 8] s，越界 CLI 直接拒绝；`--intent` 只写回执日志（不进查询/prompt/决策）。上列命令只是剧本既有命令的逐字展开，不新增采样或操作。

三剧本在单元 #3 同一次服务驻留内顺序进行（服务驻留 ≤3,600 s；预计 3 × ≤420 s 按钮墙钟 + 准备/切换余量）；驻留将到上限而剧本未完 → 先停剧本（记 `S-ENVELOPE`）再停服务收尾，不另开服务。

## 10. 计次与重试

**OPS 增量（STOP:9、AC-14 修订 1/2；IR-OPS-4 已裁定）**：新入口下环境性重试**不可用**——不加 CLI 参数、网页重试按钮或同单元重试路径；Unity 未进 Play/运行时锁冲突保留原流与失败/实账，单元收尾交用户/接受，不开下一单元，也不得用人工 CLI 绕过新入口。上表全局 ≤ 2/每剧本 ≤ 1 只是已签上限，不是必须用完或故障自动恢复许可；余额不作废、不移用，欲启新路径须先具名待裁定。主臂失败/HTTP 不可达不改成环境性原因。

正式 Play 恰 3 次（P1/P2/P3 各 1）；环境性重试**全局 ≤ 2、每剧本 ≤ 1**，只限首个机身命令前且原因 ∈ {Unity 未进 Play、运行时锁冲突}（**删除原「`/status` 不可达」分支**：服务/HTTP 不可达属首次主臂失败，停全部），两次之间代码与参数不变；重试与原始失败都保留并计入 Play/session 账；合计 session ≤ 5。主臂失败（服务未就绪/退出码 4/5、`backend_fatal`、HTTP 不可达、身份不符）一律不重试。

## 11. 每次尝试记录模板（写入 `-play.md`；`-ledger.json` 逐维度汇总第 0.4 节全部维度）

**OPS 增量**：机械/计量字段由工具原流填写（`$OUT/ops/<阶段>-<UTC>/play-ops.jsonl` 逐命令、`$OUT/ops-ledger.json` 逐维度、`$OUT/ssh/unit-*.tsv`、`$OUT/play/play-record.json`、`$OUT/play/ops-web.jsonl` 的呈现快照/显示成功/点击/argv/回执/跳过与未执行原因、`$OUT/play/ops-summary.{json,md}`）；本人「通过/失败/受阻」按钮与补充文字、点击时刻与尝试身份在 `$OUT/play/feedback.jsonl` 单列（缺失写「未反馈」，不默认通过；不等于 DONE 或门通过）。Unity 按钮起止无可靠来源照记 UNKNOWN。

| 字段 | 值 |
|---|---|
| SID / 剧本 / 第几次 / 是否重试（原因） | |
| 放行核对 1.0–1.6 输出（固定 `$REL`、`$PASSED`、实际 HEAD/status 原流、Unity 日志条目推送后 SHA） | |
| SSH 计次单元编号（#1/#2/#3）、`$TALLY` 原样（主连接尝试/rc/关闭 epoch、逐通道名与起止/rc）、单元墙钟、通道数是否 ≤ 第 0.5 节闭集 | |
| 覆盖文件 sha（运行时 `shasum`） | |
| f₀、`T_sess` 计算式 | |
| Play 按钮按下时刻 / 停止时刻 / 按钮墙钟（s，≤ 420） | |
| 会话 `TERMINAL` 时刻与原因 | |
| Unity 末帧号（≥ 1500 → `S-RING` 照记、不停） | |
| 逐命令记录（命令、回执 outcome、`SKIPPED_NOT_IN_VIEW` 与理由、候选选择依据） | |
| `model_cache.json` 的 `model_loads`（每段） | |
| 板端服务起止（`date -u`）、驻留秒数、`ss -ltn` 与 `pgrep` 释放证明、`--version` 次数累计 | |
| 归档体积（Unity 帧环 ≤ 140 MB、会话目录 ≤ 85 MB、合计 ≤ 225 MB） | |
| 峰值磁盘：`du -sk` 归档根与 `runtime/`（≤ 1,450,000,000 B）；板端 `du -sb "$BOARD_ROOT"` 各采样值与最大值（≤ 200,000,000 B；**采样最大不是连续峰值证明**）与 `df` | |
| HTTP 有效载荷：板端 `access-2.jsonl` 与 `access-3.jsonl` 逐行（每个请求一行，含坏请求行/未支持方法/提前拒绝/异常）`request_body_bytes + response_body_bytes` 合计（全项 ≤ 60,000,000 B）；另列 `request_body_complete == false` 与 `error` 非空的行数（实际字节已计入，不以声明长度补）；loopback 不计入 | |
| HTTP 次数：回传的 `http-ledger.jsonl` 逐行汇总——`loopback_health`（按结局 200/非 200/`error:`/`timeout:` 分列）、`status`、`result`、`other` 合计 = 非推理（两批累计 ≤ 200）；`query` = 推理尝试（≤ 335，含被拒/失败）；`allowed=false` 行（429 兜底）与 `over_limit=true` 行各列行数（须为 0，否则照记越界）；每个 `batch_start` 行的预留与前批累计 | |
| SSH 传输字节（批次编号、方向、`wc -c`） | |
| 三文件与库披露（AC-16 `-assets.json` 指针；库限制原文指针） | |
| STOP 触发（原因码、处置、收尾动作） | |

## 12. 归档（只移动不删除）

**OPS 增量**：由 `play_ops play` 在出帧停止后只用改名移动（目标已存在即 `S-ARCHIVE`，不读被移动文件内容）；收尾以独立进程调用 `tools/eng_loop2/summarize_ops.py --mode formal`，它对每个有归档的尝试至多调用一次下述原评分命令（已有输出不重跑），且**每次调用之前**按已签「实现自证对正式归档全批实际调用总上限 ≤ 3 次」守账（AC-10 修订 7，轮次 `评分诊断合批修复`；原 ≤ 2 与 R1-4「每归档/总次数」待裁定已由同名提案「SUB3核清与评分上限落实」§3 定为总次数 3；`$OUT/play/score-ledger.json` 持久计数：账本文件不存在时首次从 0 建立；已存在的账本不可读/缺计数键/计数非法即拒评，原账继承不重置（C8-1 纠正，轮次 `C8退回纠正`）；成功/失败/超时/中止共账、先扣后调，没有免费重评；三归档各首次成功合计 3，第 4 次实际调用在调用前拒）——下一次会越界即不调用、照记 `S-ENVELOPE`、`play` 非 0 退出；评分非 0 退出同样使摘要与 `play` 非 0 退出（R1-3），摘要只引用其漏斗与四表原值，并列计划—实际（发送/跳过/未执行/拒收）、客观事件与一致性核对；评分输出不回流在线工具。

每次 Play 结束、用户按停止后：`mkdir -p $OUT/play/$SID/unity-runtime`；把本次 Unity 帧环（`runtime/frames/` 的 JPEG + 旁车 + `retained_frame_metadata/`）、`runtime/m3_body_truth.jsonl`、段目录 `runtime/runs/$SID-resident*/` 与 **`runtime/scenario_config.json`（布局绑定副本，§3.5.1）** 移入（`mv -n`，逐 session 布局归档）；会话目录已在 `--session-root` 下。`du -sk` 记体积；> 225 MB 或副本缺失 → `S-ARCHIVE`（保留超限/身份/layout 异常事实，不删、不筛工件续跑）。评分：`$PY -m tools.eng_loop2.analyze_play score …`（实现自证对正式归档全批实际调用总上限 ≤ 3 次（AC-10 修订 7）、复核证据核实 ≤ 1 次；只读归档，不写 `runtime/`）；`frame_identity_mismatch` 或 `layout_unbound` 出现在正式证据 → `S-ARCHIVE`。

## 13. STOP 表（§6.2 原判定 + 「授权边界修订 2」逐码现行处置；用户已逐码采纳 N-3，账本 2026-10-07）

| 原因码 | 判定（原样；本版补的触发源在括号内） | 现行处置 |
|---|---|---|
| `S-PRECHECK` | 板不可达、部署文件缺失、残留服务占端口（含第 0.3、1、2 节前提/读脚本命中；SSH 主连接建立失败） | 停全部后续，回接受；不修前提/试连/换臂续行。计划新根创建前不存在不是部署缺失；必需身份、链接、归属未核仍停报未知 |
| `S-RECEIPT` | 收据退出码 6/8，或 `response_format` 请求被服务拒绝（`measure` 非 0 不在此码，按第 5 节分流） | 停全部后续，回用户；收据重测 0、5060 分支 0，保留 6/8 或 schema 拒绝 |
| `S-IDENTITY` | 资产 sha、构建号、`/status` 身份、部署摘要、`git_head` 任一不符（含服务退出码 3） | 停全部后续，回接受；不覆盖期望、换 base、重建补包或扩大三文件身份继续 |
| `S-ENVELOPE` | 任一维度达上限（含服务退出码 6、客户端/服务端 `S_ENVELOPE`——收据测量里表现为 `measure` 退出 7 且首个失败 `detail` 以 `S_ENVELOPE` 开头——单元墙钟或驻留到上限） | 停新增动作，预留已签安全收尾后回用户；不跨维度借余额 |
| `S-LOAD` | 任一 session YOLO 加载 > 1 | 停全部后续，回实现/复核，修复候选回停点；不增候选/测试额度 |
| `S-BACKEND` | `backend_fatal`（原因文字不含 `S_ENVELOPE`） | **首次即停本次及全部后续**，回用户；故障重启 0 |
| `S-REBUILD` | `TERMINAL(rebuild_limit)` | 停本次并计账；仅确认 A5 非主臂帧/发布段限制时下一既定剧本可继续；主臂失败或不能判明 → 停全部回用户/接受；不重跑本次、不加剧本/改参数 |
| `S-WALL` | 按钮墙钟 > 420 s | 停本次及全部后续，回用户；420 s 是资源上限非性能线 |
| `S-ARCHIVE` | 每 Play 归档 > 225 MB，或正式归档 `frame_identity_mismatch`，或场景副本缺失/不符（`layout_unbound`） | 停全部后续，回用户；保留超限/H-2 身份/layout 异常，不删筛工件续跑；采样最大不称连续峰值证明 |
| `S-SERVICE` | SSH 单元结束时服务仍在监听或发现后台驻留（含 `pgrep` rc≥2 无法判明） | 停全部后续，回用户；本人在已签前台收尾范围内停止并核端口，不新开服务/清未知进程；释放不可核照记 UNKNOWN |
| `S-RING` | Play 末帧号 ≥ 1500 | 不停；静止车相应帧 `NO_POSE` 照记；不扩帧环、补采或改指标 |

- **OPS 增量（O3；IR-OPS-3 已裁定保持 fail-closed）**：`play_ops` 按本表原码分流；目前没有已冻结且可机械证明 A5「非主臂帧/发布段限制」的事件组合，`TERMINAL(rebuild_limit)` 一律 `S-REBUILD` 并标 UNKNOWN、停全部后续、安全收尾交接受（不以 reason 字符串/主观判断/余额续下一剧本；原唯一允许继续分支保留为条件合同，但本新入口不可用）；`S-RING` 原不停不变；会话 `backend_fatal` 原因文字含 `S_ENVELOPE` → `S-ENVELOPE`，其余 → `S-BACKEND`；计划因结果未知停止推进 → 停全部交接受。
- **OPS 增量（失败路径安全收尾；轮次 `OPSC6返工`，C6-1/2/3）**：任一 STOP、Ctrl-C 或不明异常（后两者记 `UNKNOWN`、停全部交接受）一发生即**不可逆封住**本会话业务动作（共享提交通道：工具与网页都不再发送/跳过/确认/拒绝/release，计划末 stop 以外不推进；迟到回执或 TERMINAL 只记录、不恢复）；随后同一路径依次：沿共享通道发原 stop（每会话至多一次，结果未知不重发）→ 等会话进程自行退出（到时仍在运行照记 UNKNOWN，不杀进程）→ 末次读原流并逐步记录 → 提示本人停 Play、等出帧静止 → 读加载计数 → 只移动归档（会话或 Unity 未确认停止则不移动、照记）→ 原因码分流；之后再停服务并核释放、回传日志、关单元、写 `play-record.json`、独立进程摘要、反馈窗口、关闭本地网页。每步独立记录在 `closeout`，一步失败不跳过其余；尝试记录（实际步骤/request_id/rc/终止原因/可得时刻/加载/归档指针/全部 STOP）在任何退出路径都保留，已受理而被封住的步骤记 `HALTED`（仍是样本），确实未执行与记录未知分列。
- **`S-SSH`（第 0.5 节控制套接字缺失/失效）不是新原因码**：按 `S-PRECHECK` 处置（停全部后续、回接受），并在记录中标明是单元内套接字失效；不新建认证连接、不重试。
- **首次服务/HTTP 失败停全部**：服务未就绪（退出码 4）、服务期间 `llama-server` 退出（5）、`/status` 或收据/会话 HTTP 不可达、收据 `measure` 非 0（非 `S_ENVELOPE` 原因，第 5 节），均属首次主臂失败 → 停全部、回用户、故障重启 0，不以缺 `backend_fatal` 事件继续。长轮询的正常 pending 到期不是 HTTP 失败。
- `none`/`ambiguous`/正常解析失败按原漏斗及内置尝试共账，不新增性能 STOP；`frame_stall`、`PUBLISH_REJECTED`、`catchup_stale` 等现行硬停止按 A5 重建分类处理并照记；移植/申请值（提案 §3.5.6 表）一律不作 STOP。
- STOP 后只允许已签范围内：本人停止前台服务、核端口释放、记账、保留工件、`unit_close` 与必要安全收尾；没有新加载、动态诊断或删除许可。任何不能判明是否主臂失败的情况先停，记录歧义回接受。

## 14. SSH 计次单元总账（准备 1 + 收据 1 + Play 1；与第 0.4–0.5 节同口径）

| 单元 | 内容（顺序） | 通道数 | 板写入 | 传输批次 | `--version` | GGUF 加载 | 推理尝试 / 非推理 HTTP | 驻留 |
|---|---|---|---|---|---|---|---|---|
| #1 准备 | 第 2 节只读读脚本（stdin，不落板） | 1 | 0 | 0 | 0 | 0 | 0 / 0 | 0 |
| #2 收据 | 3.3 建根 → 3.4 资产核实 → 3.5 部署 + expect-assets（批次 1）与逐文件核对 → 第 4 节启动 → `/status` → 第 5 节收据 → 停止与释放 → 日志回传（批次 2）→ `unit_close` | 7 | 根内 | 2 | 2（3.4 + 启动自核） | 1 | 35 / 账行实计（第 0.6 节） | ≤3,600 s |
| #3 Play | 第 4 节启动 → `/status` → 第 6、9 节三剧本 → 停止与释放 → 日志回传（批次 3）→ `unit_close` | 2 | 根内日志 | 1 | 1 | 1 | ≤300 / 账行实计 | ≤3,600 s |

三单元墙钟累计 ≤10,800 s。顺序与用途按 IR-M8 已采纳：准备 #1 只读必需事实、接受核清（G4）后，部署与资产核实在收据 #2 首次启动前，#2 正常结束才开 #3。

**单元级停止与剧本级继续的区分**（O-3）：第 13 节除 `S-RING`（不停）与 `S-REBUILD` 的「确认 A5 非主臂帧/发布段限制」分支外，任何 STOP 都是**单元级停止**——本单元只做已签收尾后 `unit_close`，其余单元不再开启。`S-REBUILD` 的该分支是单元 #3 **内**的剧本级继续：只停本次剧本并计账，同一服务驻留内按既定顺序进行下一个剧本；它不是「单元提前 STOP」，不新开单元、不重跑本次、不启用新单元作重试。`S-REBUILD` 主臂失败或原因不能判明时按单元级停止处理。

## 附录 P 准备读脚本正文（`$OUT/prep/prep-read.body.sh`；经通道 `prep-read` 的 stdin 送入、不落板；fail-fast，命中 STOP 即退出 3；替代 mini 证据第 2.2 节旧版）

本轮只做了本机 `bash -n` 语法检查（见证据文件），未在板上执行。`play_ops prep` 按本标题前缀原样取出下块（标题前缀与块正文改动即改变 PLAY_GOVERNING，须重过停点）。相对旧版的改动（PR-12）：`readelf` 读解释器与扩展失败即停；扩展 `Machine` 须为 `AArch64`；`ldd` 失败即停；`pgrep` rc 0 → 残留 STOP、rc 1 → 无匹配、rc≥2 → `PGREP_FAIL` STOP。

```bash
set -u
STOP() { printf '\nSTOP %s\n' "$1"; date -u +%FT%TZ; printf 'remote_elapsed_s=%s\n' "$SECONDS"; exit 3; }
sec() { printf '\n=== %s\n' "$1"; }
sec "P00 device"; date -u +%FT%TZ; H=$(hostname); printf 'hostname=%s\n' "$H"; uname -srm; id -un
[ "$H" = "$EXP_HOST" ] || STOP "HOST_MISMATCH"
[ "$(uname -m)" = aarch64 ] || STOP "ARCH_MISMATCH"
sec "P01 tools (required; presence only)"
for t in date hostname uname id stat readlink ls readelf ldd df free ss pgrep timeout grep cat tar mkdir du awk sort sha256sum; do
  p=$(command -v "$t") || STOP "TOOL_MISSING $t"; printf '%s|%s\n' "$t" "$p"
done
for t in dpkg-query ldconfig; do printf '%s|%s\n' "$t" "$(command -v "$t" || echo ABSENT_optional)"; done
sec "P02 three files (stat only; sha is AC-16 in unit #2)"
for f in "$WEIGHTS" "$MMPROJ" "$LLAMA_BIN"; do
  [ -L "$f" ] && STOP "ASSET_IS_LINK $f"
  s=$(stat -c '%F|%s' -- "$f" 2>&1) || STOP "ASSET_STAT_FAIL $f"; printf '%s|%s\n' "$f" "$s"
done
[ "$(stat -c %s -- "$WEIGHTS")" = "$EXP_WEIGHTS_BYTES" ] || STOP "WEIGHTS_BYTES_CHANGED"
[ "$(stat -c %s -- "$MMPROJ")" = "$EXP_MMPROJ_BYTES" ] || STOP "MMPROJ_BYTES_CHANGED"
[ "$(stat -c %s -- "$LLAMA_BIN")" = "$EXP_LLAMA_BIN_BYTES" ] || STOP "LLAMA_BIN_BYTES_CHANGED"
sec "P03 interpreter ELF"
PYR=$(readlink -f -- /usr/bin/python3) || STOP "PY_READLINK_FAIL"; printf 'python3_realpath=%s\n' "$PYR"
[ "$PYR" = /usr/bin/python3.12 ] || STOP "PY_REALPATH_CHANGED"
V=$(/usr/bin/python3 --version 2>&1) || STOP "PY_VERSION_FAIL"; printf '%s\n' "$V"
HDR=$(readelf -h -- "$PYR" 2>&1) || STOP "PY_READELF_H_FAIL"; printf '%s\n' "$HDR" | grep -E 'Class:|Type:|Machine:'
printf '%s\n' "$HDR" | grep -qE 'Machine:[[:space:]]+AArch64' || STOP "PY_MACHINE_NOT_AARCH64"
DYNH=$(readelf -d -- "$PYR" 2>&1) || STOP "PY_READELF_D_FAIL"; printf '%s\n' "$DYNH" | grep -E 'NEEDED|RUNPATH|RPATH'
sec "P04 C-level stdlib modules: builtin (PyInit_ in .dynsym) or lib-dynload ext"
DYN=/usr/lib/python3.12/lib-dynload
DSYM=$(readelf -W --dyn-syms -- "$PYR" 2>&1) || STOP "PY_READELF_DYNSYM_FAIL"
SYMS=$(printf '%s\n' "$DSYM" | awk '{print $NF}' | grep -E '^PyInit_' | sort -u)
NSYM=$(printf '%s\n' "$SYMS" | grep -c '^PyInit_'); printf 'pyinit_dynsym_count=%s\n' "$NSYM"
REQ_MISS=; OPT_MISS=
for m in _posixsubprocess fcntl select _socket math binascii _struct _random _json _datetime _bisect _hashlib _sha2 array zlib _heapq _opcode _ssl; do
  case "$m" in _posixsubprocess|fcntl|select|_socket|math|binascii|_struct|_random) cls=REQ;; *) cls=OPT;; esac
  if printf '%s\n' "$SYMS" | grep -qx "PyInit_$m"; then printf '%s|%s|builtin_dynsym\n' "$cls" "$m"; continue; fi
  set -- "$DYN/$m".cpython-312-*.so
  if [ -e "$1" ]; then
    printf '%s|%s|ext|%s\n' "$cls" "$m" "$1"
    EH=$(readelf -h -- "$1" 2>&1) || STOP "EXT_READELF_H_FAIL $m"
    printf '%s\n' "$EH" | grep 'Machine:'
    printf '%s\n' "$EH" | grep -qE 'Machine:[[:space:]]+AArch64' || STOP "EXT_MACHINE_NOT_AARCH64 $m"
    ED=$(readelf -d -- "$1" 2>&1) || STOP "EXT_READELF_D_FAIL $m"; printf '%s\n' "$ED" | grep 'NEEDED'
    L=$(ldd -- "$1" 2>&1) || STOP "EXT_LDD_FAIL $m"; printf '%s\n' "$L"
    printf '%s\n' "$L" | grep -q 'not found' && STOP "EXT_DEP_NOT_FOUND $m"
  else
    printf '%s|%s|NOT_FOUND\n' "$cls" "$m"
    if [ "$cls" = REQ ]; then REQ_MISS="$REQ_MISS $m"; else OPT_MISS="$OPT_MISS $m"; fi
  fi
done
printf 'opt_not_found=%s\n' "${OPT_MISS:-none}"
[ -z "$REQ_MISS" ] || STOP "REQ_CMOD_UNRESOLVED:$REQ_MISS(pyinit_dynsym_count=$NSYM)"
sec "P05 site hooks (recorded only; board runs -I -S -B per IR-M5)"
for d in /usr/lib/python3/dist-packages /usr/local/lib/python3.12/dist-packages "$HOME/.local/lib/python3.12/site-packages"; do
  printf '[%s]\n' "$d"; ls -la -- "$d"/*.pth 2>&1
done
ls -la -- /usr/lib/python3.12/sitecustomize.py /etc/python3.12/sitecustomize.py 2>&1
sec "P06 package versions / L4T / CUDA driver (static records; optional tools)"
if command -v dpkg-query >/dev/null; then dpkg-query -W -f='${Package}|${Version}|${Architecture}\n' python3.12 python3.12-minimal libpython3.12-minimal libpython3.12-stdlib 2>&1; printf 'rc=%s\n' "$?"; fi
cat /etc/nv_tegra_release 2>&1; printf 'rc=%s\n' "$?"
if command -v ldconfig >/dev/null; then ldconfig -p 2>/dev/null | grep -E 'libcuda\.so'; printf 'rc=%s\n' "$?"; fi
sec "P07 planned root (must be absent; read-only)"
for d in /home/jetson/eng-loop2 /home/jetson/eng-loop2/code /home/jetson/eng-loop2/logs; do
  if [ -e "$d" ] || [ -L "$d" ]; then stat -c '%n|%F|%a|%U:%G' -- "$d"; STOP "PLANNED_ROOT_EXISTS $d"; else printf '%s|ABSENT\n' "$d"; fi
done
df -B1 / /home/jetson 2>&1 || STOP "DF_FAIL"; free -b 2>&1 || STOP "FREE_FAIL"
sec "P08 ports / residual processes"
SS=$(ss -ltn 2>&1); r=$?; printf '%s\nrc=%s\n' "$SS" "$r"; [ $r -eq 0 ] || STOP "SS_FAIL"
printf '%s\n' "$SS" | awk '{print $4}' | grep -qE ':(18081|18082)$' && STOP "PORT_OCCUPIED"
for pat in llama-server language_serve; do
  out=$(pgrep -a -f "$pat" 2>&1); r=$?; printf '[pgrep %s] rc=%s\n%s\n' "$pat" "$r" "$out"
  case "$r" in 0) STOP "RESIDUAL $pat";; 1) ;; *) STOP "PGREP_FAIL $pat rc=$r";; esac
done
sec "P99 end"; date -u +%FT%TZ; printf 'remote_elapsed_s=%s\nfinal=NO_STOP\n' "$SECONDS"
exit 0
```

停止闭集（命中即停，保存已得原流，交接受；不追加连接、不清进程、不建根）：Air 前置任一失败；`HOST_MISMATCH`、`ARCH_MISMATCH`、`TOOL_MISSING`、`ASSET_IS_LINK`、`ASSET_STAT_FAIL`、`*_BYTES_CHANGED`、`PY_READLINK_FAIL`、`PY_REALPATH_CHANGED`、`PY_VERSION_FAIL`、`PY_READELF_*_FAIL`、`PY_MACHINE_NOT_AARCH64`、`EXT_READELF_*_FAIL`、`EXT_MACHINE_NOT_AARCH64`、`EXT_LDD_FAIL`、`EXT_DEP_NOT_FOUND`、`REQ_CMOD_UNRESOLVED`、`PLANNED_ROOT_EXISTS`、`DF_FAIL`、`FREE_FAIL`、`SS_FAIL`、`PORT_OCCUPIED`、`RESIDUAL *`、`PGREP_FAIL *`；主连接/认证失败；套接字失效（`S-SSH`）；脚本末行不是 `final=NO_STOP`；任何合同疑义。`REQ_CMOD_UNRESOLVED` 且 `pyinit_dynsym_count=0` 表示静态无法分类 → 只能转 `B-main:ENV:2`（另签）。

命令闭集说明：沿用原只读补核已核清的 `date hostname uname id command test stat readlink ls readelf ldd python3 --version df free ss pgrep timeout` 与有限 shell；`grep awk sort cat`（文本过滤）、`dpkg-query -W`、`ldconfig -p`、`cat /etc/nv_tegra_release` 为只读静态读（mini 版已列、C3 未提异议，仍待接受在下一实际 C 轮确认属「非特权静态读」）；`tar mkdir du sha256sum` 只核存在性、本单元不执行。
