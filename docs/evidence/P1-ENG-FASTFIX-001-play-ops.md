# P1-ENG-FASTFIX-001 操作单（AC-15）：B 冒烟 FASTFIX:SMOKE:1 与 C 正式 FASTFIX:PLAY:1

> **状态**：阶段 A 只**准备**本单（同名提案「A首签落实」§3 第 3 步）；B/C 均**未签、额度 0**，本单不授权任何 Play、ID、模型加载、
> runtime 清槽或保全迁移。B 只在「D2预检核清」§3 的 SMOKE 前置齐全且用户首签后执行；C 另须冒烟报告核清、必要返工经代码停点、
> C 首签。两份各一次，失败不重试、不追加。机器：MacBook Air（七题答复 MACHINE）。仓库内命令均在 Air 仓库根执行。
> 数值出处四类（信封＝用户签；合同继承；设计预算；实测）逐行标注；本单不内置未签数字为已签。

## 0. 阶段计时起点与两份共同的发令前登记（每份各做一次，原样写进当次证据）

**阶段墙钟从本节第一条命令起算**（续修C1 / C1-4，首次接受释义 5）：预检、§2 保全、模型加载、Play、离线评分、证据写作、
提交/推送与计量终读全部在同一阶段区间内共账（B ≤ 3600 s、C ≤ 5400 s，信封待签）；收尾预留 R_close = 600 s（设计预算：
计量终读、`git add/commit/push`、账本记账），即 **最晚 T_stage − R_close 停止一切新消耗步骤**，余量只供收尾。
计量（§4）在任何预检读数/保全/写入之前启动，阶段 t0 快照先于第一笔阶段写入。

```bash
STAGE_T0=$(python3 -c "import time;print(time.time())"); echo "stage_t0_unix=$STAGE_T0"   # 阶段墙钟起点（记入证据）
# 先按 §4 第 1 步取 t0 快照并启动两路计量，再继续本节读数
git rev-parse HEAD; git status --porcelain          # 须为已过 K1K2K3K4 复核并经接受消费的候选（或其后经停点的窄修）
.venv-yoloe/bin/python -c "import sys,ultralytics,torch,numpy,lap;print(sys.version,ultralytics.__version__,torch.__version__,numpy.__version__)"
shasum -a 256 outputs/eng-det/runs/run-1/weights/last.pt config/det-assoc-v1.models.json config/p1-eng-fastfix-001.json config/p1-eng-capture-001.json
df -k /System/Volumes/Data; pgrep -fl -i "unity|python"; lsof +D runtime 2>/dev/null | head
```

记录项：HEAD、工作树（须空）、解释器与包版本、权重/配置 sha（权重须 = `d6a0d6a9…`，配置以 git 运行时解析为准）、磁盘余量、写者进程
（须无 Unity Play/会话/点击页/其他 Python 写者）、`runtime/` 现场清单。任一不符或读不到 → **S-PRE**，本阶段一切消耗不启动。

## 1. 路径闭集与旧残留（AC-15 修订 1；「D2预检核清」§2）

本阶段实际读取、写入或归档的路径闭集：

| 类 | 路径 | 读/写 | 执行前要求 |
|---|---|---|---|
| 帧桥 | `runtime/frames/`（含 `latest.json`） | Unity 写、会话读 | 不存在（或已按 §2 保全移走）；首帧由本次 Play 生成 |
| 场景覆盖 | `runtime/scenario_config.json` | 本阶段生成 | 不存在；按 §3 生成并记 sha |
| 8 个桥文件 | `runtime/{body_command,gimbal_command,tracking_observation,metrics,tracker_state,language_request,road_scene_audit,route_corridor_audit}.json` | 会话/Unity 写读 | 执行前不得存在旧内容（按 §2 保全） |
| 运行目录 | `runtime/runs/` | 会话写 | 旧完整目录按 §2 保全；新目录由本次会话生成 |
| 会话输出 | `outputs/eng-fastfix/<smoke\|formal>/` | 会话/计量写 | 不存在（排他创建） |
| 真值输出 | Unity CoverageEvaluator 的 `runtime/m3_body_truth.jsonl` | Unity 写；只进离线 `score_` | 不存在（旧文件按 §2 保全） |
| 计量输出 | `outputs/eng-fastfix/<stage>/meter.jsonl`、`STOP`、`ALERT` | 计量写 | 不存在 |

其余历史 hold 目录/文件**只在本表证明不被读取、覆盖或归档时**原地保留；路径归属或写者判不清即 **S-PRE**，计量不能闭合即 **S-UNKNOWN**。
首次 Play 前现场再核：无 Unity Play、会话、点击页、其他写者及锁冲突（不沿用静态读数）。

## 2. 旧残留同卷保全（只在 B/C 首签明确允许时执行；旧许可不转用）

```bash
STAMP=$(date -u +%Y%m%dT%H%M%SZ)-$(openssl rand -hex 3); DEST=outputs/eng-fastfix/preexisting-runtime/$STAMP
mkdir -p outputs/eng-fastfix/preexisting-runtime && mkdir "$DEST"        # 最后一级排他创建
stat -f %d runtime outputs "$DEST"                                         # 须同卷
# 清单逐文件三列：相对路径、字节数（stat -f %z）、sha256；末行汇总文件数与总字节（C1-4：数量/字节/sha 三项都核，不只 sha）
manifest() { ( cd "$1" && LC_ALL=C find "${@:2}" -type f -print0 | sort -z | while IFS= read -r -d '' f; do
  printf '%s\t%s\t%s\n' "$f" "$(stat -f %z "$f")" "$(shasum -a 256 "$f" | cut -d' ' -f1)"; done ) | tee /dev/stderr \
  | awk -F'\t' '{print} {n++; b+=$2} END {printf "#count\t%d\t#bytes\t%d\n", n, b}'; }
manifest runtime <源清单> > "$DEST.manifest-pre.tsv"
mv -n runtime/<源对象> "$DEST/"                                           # 逐项；rename，无覆盖、不删除、不复制后删源
manifest "$DEST" <同一清单> > "$DEST.manifest-post.tsv"
cmp "$DEST.manifest-pre.tsv" "$DEST.manifest-post.tsv"                     # 逐文件路径/字节/sha 及汇总数量/总字节逐字节一致
```

源闭集：B = 上表 8 个桥文件 + `runtime/runs/` 完整旧目录（及现场发现的旧 `runtime/frames/`、`runtime/m3_body_truth.jsonl`，若存在先停报、
由接受核清后才可列入）；C = B 阶段本项产物（C 首签前由接受落实具体源闭集）。迁后复核 §1 满足才加载模型/按 Play；异常停报、不追加额度。
保全目录与清单字节计入当阶段磁盘峰值与阶段墙钟（AC-19 修订 1）。

## 3. 场景覆盖文件

```bash
PY=.venv-yoloe/bin/python
"$PY" -c "import json;d=json.load(open('config/scenario.untethered.json'));d['sensor']['retained_frame_count']=1500;open('runtime/scenario_config.json','w').write(json.dumps(d,indent=2)+'\n')"
shasum -a 256 runtime/scenario_config.json
```

## 4. 计量（续修C1 / C1-4：整窗累计上界 + 声明根小计；两路均在 §0 第一条读数之前启动）

**第 1 步：阶段 t0 快照（先于任何阶段写入）与整窗累计计量** `tools/eng_fastfix/window_meter.py`：

```bash
OUT=outputs/eng-fastfix/<smoke|formal>; mkdir "$OUT"                     # 排他创建；此后一切阶段写入都在计量窗口内
# 具名执行者：Claude.app（若由 Claude 会话驱动）、Unity Editor、运行会话/点击页的终端；各取其进程所在资源联盟
/usr/bin/python3 tools/eng_fastfix/window_meter.py snapshot --pid <Claude.app pid> --pid <Unity pid> --pid <终端 pid> \
  --out $OUT/stage-t0.json                                                 # 读失败 → S-UNKNOWN，不启动阶段
nohup /usr/bin/python3 tools/eng_fastfix/window_meter.py --t0-json $OUT/stage-t0.json --out $OUT/window-meter.jsonl \
  --flag-dir $OUT/flags --stop-file $OUT/STOP --ext-pid <其余已见外部写者 pid…> \
  --stop-at 900000000 --limit 1000000000 --interval 0.4 > $OUT/window-meter.stderr 2>&1 &
```

- **U(t) = C + E + R**（与「续做计量预检」同式）：C = 各执行者联盟自阶段 t0 的 `byteswritten + logical_{immediate,deferred,metadata}_writes`
  累计增量（含已退出成员、延迟写与映射写，覆盖采样间瞬时建删）；E = 联盟外已见写者的进程终身写量 + 其联盟自首读增量；
  R = 数据卷 APFS 容器占用自首读的已见最大新增（全部声明根与 TMP、测试临时目录、证据、`.git`、客户端日志/缓存、swap 同容器，精确去重）。
  允许重复覆盖而偏大，不做扣减；节拍 0.4 s。
- 旗标：U ≥ 900,000,000 B（1 GB × 0.9，S-DISK）/ ≥ 1,000,000,000 B（S-BUDGET）/ 读取失败·联盟变更·计数回退（S-UNKNOWN）写入 `$OUT/flags/`；
  操作员与执行者每步启动前、Play 中每 ≤ 30 s 看旗标与末行 U，任一旗标出现即按 §7 停。每步启动前核
  `U + 该步保守需求 + 收尾预留（200 MB，设计预算：提交/推送与计量终读）< 900,000,000`，不足即拒启（S-DISK 不靠「收尾」越线）。
- 已知偏大：执行者联盟含 Claude.app 其他会话与客户端后台写入；若阶段启动前即判定 U 的背景速率使 1 GB 不足以完成阶段，
  停报 S-BUDGET 交 Acceptance/用户，不换计法、不扣减。

**第 2 步：声明根小计** `tools/eng_fastfix/meter.py`（只作分项核对；任一根/条目不可读、采样或输出故障、采样线程失联
→ `stop_condition` S-UNKNOWN 并停令，见 `tests/test_fastfix_meter.py` C1-4 用例）：

```bash
nice -n 10 "$PY" -m tools.eng_fastfix.meter --root session=$OUT --root frames=runtime/frames --root runs=runtime/runs \
  --root truth_dir=runtime --root git=.git --root tmp="$TMPDIR" --root claude_client="$HOME/Library/Application Support/Claude" \
  --root claude_logs="$HOME/Library/Logs/Claude" --root claude_projects="$HOME/.claude/projects" \
  --output $OUT/meter.jsonl --interval-s 10 --stop-file $OUT/STOP --alert-file $OUT/ALERT \
  --disk-limit-bytes 1000000000 --disk-stop-fraction 0.9 --wall-limit-s <剩余阶段秒 = T_stage − (now − STAGE_T0)> &
shasum -a 256 tools/eng_fastfix/meter.py tools/eng_fastfix/window_meter.py $OUT/stage-t0.json   # 工具与起点 sha 记入证据
```

数值出处：1 GB、阶段墙钟 60/90 min = 信封（待用户签）；0.9 = S-DISK 收尾预留（信封口径）；R_close 600 s、收尾磁盘预留 200 MB、
10 s/0.4 s 间隔与输出上限 = 设计预算。`--root truth_dir=runtime` 只 `lstat` 取大小、不读内容。计量进程崩溃、停令检查失联、
`meter_truncated` 或 S-UNKNOWN → **S-METER/S-UNKNOWN**（停 Play，不无计量继续）。两路计量一直运行到 §8 提交/推送完成后的终读，
**终读之后才** `touch $OUT/STOP`；终读与停令文件本身的字节计入（偏大）。

## 5. 会话与点击页（捕获模式，FASTFIX 参数）

```bash
SID=fastfix-<smoke|formal>-1
# f0 = 起会话前本次 runtime/frames/latest.json 的 frame_id；T_sess = min(270, (1490 − f0)/5) 秒（须 > 0；续修C1：与 §6 第 270 s 停令一致）
"$PY" -m controller.language_loop run --language off --session-id $SID --session-root $OUT/sessions \
  --runtime runtime --allow-shared-runtime --tracker det-assoc-v1 --resident \
  --ground-plane-y-m 0.2 --body-policy standoff --body-planner-config config/p1-eng-frame-001-body.json \
  --body-scenario-config runtime/scenario_config.json --scenario-id deterministic-loop-untethered \
  --fastfix-config config/p1-eng-fastfix-001.json --planned-duration-s <T_sess> 2>&1 | tee $OUT/$SID.session-process.log
"$PY" -m tools.eng_capture.click_web live --runtime runtime --session-id $SID --log $OUT/$SID.click-web.jsonl --port 8774
```

C 若用户另签 0.6 s/3 帧：先改 `config/p1-eng-fastfix-001.json` 的 `t_pub_s`/`k_pub` 并回代码停点复核、经接受消费后才进 C；未签保持 0.4 s/2 帧。
会话 JSONL 另含本项事件：`publish_dropped`、`publish_escalated`、`frame_timing`、`reacquire_*`；收据另含 `PUBLISH_DROPPED`。

## 6. 剧本（AC-15；两份相同，各一次）

| 步 | 动作 | 记录 |
|---|---|---|
| S1 | 点一辆静止车 | 绑定或拒绝原因照记 |
| S2 | 点红车并跟随 ≥ 1 圈（含 CAPTURE 丢失拐角） | 降级（`TRACKING/publish_degraded`）、升级、重建后重捕（`REINIT_REQUIRED/reacquiring` → `TRACKING/rebuild_reacquired` 或 `reacquire_failed`/`reacquire_ambiguous`）逐次照记 |
| S3 | 点静止车，再点回红车 | 两次换目标照记；重捕窗口内点击 = 取消提示并执行点击 |
| 结束 | `T_sess` 到点或点击页「停止会话」 | Play 计 1，失败不重试 |

**Play 墙钟登记（C1-4）**：按下 Play 的同时记 `play_start_unix`（`date +%s.%N`，操作员口令后执行者立即记）；
**停令在 Play 第 270 s 发出**（设计预算：留 30 s 给会话 stop、Unity 停 Play 与落盘），按下 Stop/Play 键使 Unity 实际退出 Play 时记
`play_stop_unix`；证据写 `play_stop_unix − play_start_unix`（实际 Play 墙钟），> 300 s 即记偏差停报，不以发令时刻代替实际停止。
`T_sess ≤ 270 s` 与此一致。

操作员目视：拐角处跟住，或丢失/降级/重捕失败有可见报告（`tracker_state` 原因）；「无报告的主动撤权悬停」照实记录（AC-18 由用户目检、代录）。

## 7. STOP 表（同名提案 §6；处置随 B/C 信封交用户确认，未确认的处置不生效、照旧停报）

| 码 | 触发 | 停什么 | 零消耗安全收尾 | 耗用与 UNKNOWN |
|---|---|---|---|---|
| S-PRE | §0/§1 不符或读不到 | 本阶段全部消耗不启动 | 记读数、提交预检证据 | 0；未读到即 UNKNOWN |
| S-BUDGET | 启动前余额不足或运行中将达上限 | 拒启/到限即停该步 | 保存已得产物、写资源记录、提交 | 已耗入账不返还 |
| S-UNKNOWN | 计量缺失/账本损坏/耗用不可得 | 一切后续消耗 | 同上 | 记 UNKNOWN，回用户 |
| S-LOADER | （全套）真实构造超 F12 闭集 | 该次全套 | 保存日志、提交 | 已构造入账 |
| S-ORIG | 原件/准入集 sha 不符 | 依赖该输入的步骤 | 原件不动、记差异 | 0 |
| S-TRUTH | 真值进入运行时迹象 | 全部运行与 Play | 保存证据，按 RED_LINE 报 | 已耗入账 |
| S-PLAY-WALL | Play 段到 300 s | 操作员按停、会话 stop | 计量收尾、原件归档、离线评分（零模型） | Play 计 1 |
| S-DISK | 计量新增磁盘达上限 90% | 立即停 Play/回放 | 同上，不删原件 | 记峰值 |
| S-METER | 计量崩溃/停令检查失联/输出截断 | 停 Play | 同上 | Play 计 1 |
| S-REBUILD | 会话 `rebuild_limit` 终止 | 结束本次 Play，不重开 | 同上 | Play 计 1 |
| S-SAFETY | 操作员目视机身/系留异常 | 立即停 | 同上 | Play 计 1 |
| S-OPS | 误触、额外 Play 或未登记组件启动 | 立即停，不补跑 | 同上并如实登记 | 实际次数入账，超出回用户 |

## 8. 收尾与产物

```bash
# 1) 离线评分/证据写作/账本记账（零模型；同一阶段计时与计量窗口内）
# 2) 提交并推送（git fetch → 仅快进/变基到 origin/main → push），记 push 完成时刻
git rev-parse HEAD; git status --porcelain       # 与 §0 比对
# 3) 子进程静止后终读：两路计量末行（U、旗标、根小计）与阶段终点
python3 -c "import time;print(time.time())"      # stage_end_unix；阶段墙钟 = stage_end_unix − STAGE_T0（≤ 信封，含收尾）
tail -1 $OUT/window-meter.jsonl; tail -1 $OUT/meter.jsonl; ls $OUT/flags
touch $OUT/STOP                                  # 终读之后才停计量（停令延迟 ≤ 1 s）
```

终读结果（U 终值、峰值、旗标、阶段起止、实际 Play 起止）在下一次提交写入证据；该次提交的字节已在 U 的收尾预留内（偏大计入）。

- **B（冒烟，AC-20）**：实现角色按 §3.4/§3.5 由会话 `frame_timing`/`publish_dropped`/`publish_escalated` 与计量采样区间算读数并按预登记
  规则机械给出分流建议，写 `docs/evidence/P1-ENG-FASTFIX-001-smoke.md`；不进验收门、不定 verdict。
- **C（正式，AC-16/17/18）**：离线 `score_`（真值只在 `tools/eng_fastfix/score.py`）逐项分母写 `docs/evidence/P1-ENG-FASTFIX-001-play.md`
  §1–3；缺日志/缺真值/未满一圈 → `INCOMPLETE`；AC-18 由用户目检、接受或辅助角色代录。
- 原件只读归档到 `$OUT`，不移动/覆盖其他原件；产物字节、墙钟按 AC-19 入当阶段账本（`tools/eng_fastfix/ledger.py`，`wall_s` 记
  `[STAGE_T0, stage_end_unix]` 区间并集、`disk_peak_bytes` 记**阶段 t0 起累计 U(t) 的已见最大**（不是每步差值的 max）、
  `unity_play`/`session_ids`/`run_ids` 尝试即记）；启动核对另用 `ledger.check_disk_window`（90% 停止线与收尾预留）。
