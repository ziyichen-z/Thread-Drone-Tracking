# P1-M3-BODY-001 arm B trial 4 证据（操作单 revision 25）

**范围**：用户 2026-08-14 批量授权 B2–B5 中的**第三次**（B4）。执行合同 =
`docs/evidence/P1-M3-BODY-001-1c-preflight.md` **revision 25**。采集 ID
`p1-m3-body-001-arm-b-trial-4`（canonical slot 即其自身，从未消耗，**无替代 ID、无
predecessor 门**），配对搭档 A4（`p1-m3-body-001-arm-a-trial-4`）。

**状态**：**§A 已完成**（2026-08-20，实现角色）——§2.21 现场按来源分离保全；复核轮 14
`PASS_WITH_NOTES` on `fcb22a7`（F12/F13 关闭），接受轮 70 消费 verdict 并发 revision 26。
**§B 已完成**（2026-08-20，实现角色）——§2.22 十项 **156/156**、§2.0 (b)、§3 步骤 0 与
0′ 第 1 步。两节均**零 Play、零采集 ID 创建/消耗、零代码/测试/config/scenario/model 改动、
零操作单改动**（BC-BODY1-21/-22）。**其后待办**：§2.0 **(c) 由接受角色**写入
`docs/unity-test-log.md`（实现角色对该文件只读），然后 **(d)** 发令时刻核对，然后用户进
Play。§3 步骤 0′ 第 2 步、门 1/2/3/4 与其后各节在那次 Play 时/后追记入本文件。

---

# A. §2.21 现场按来源分离保全（**已执行**，2026-08-20，实现角色）

交接来源：接受轮 69（revision 25——复核轮 13 F12/F13 的返工 + P10 应用）。
**本节是本轮唯一被授权执行的动作**；执行完即停。

**批次时点**：`git rev-parse HEAD` = `c776f8b22ce690a8fb5facaad10e7524bbb3bc9d`
（接受轮 69 的提交），批次开始与结束时 `git status --porcelain` 均为**空输出**。
`runtime/` 全域在 `.gitignore:30`（`/runtime/*`）之内，故本节的七次移动在仓库侧
**零 diff**。**这不是 §2.0 (b) 的执行**——(b) 与 (c) 仍在放行条件之后，此处只是据实
记录测量时点。

## A.1 移动前两道 fail-closed 门：**38 条机械核对，38 PASS / 0 FAIL**

两道门按 revision 25 §2.21「移动前必须做的两件事」执行，**顺序为先测后动**，任一不符
即停止并回 Acceptance。脚本只做 `open(..., 'rb')` 读取与 `stat`，无 `mv`/`rm`/`mkdir`。

**门 2 —— 归属复核（复核 N43，本轮新增）**：聚合相等证明不了归属，故按 frame id 段与
包内 `capture_unix_s` 独立复核两组划分。

| 核对 | 实测 | 期望 | 结果 |
|---|---|---|---|
| `runtime/frames/` 项数 | **315** | 315 | ✓ |
| 非 `frame_*` 条目 | 恰 `latest.json` 一项 | 同 | ✓ |
| A 段 id | 恰 `[0, 28]` 全 **29** 个 | 同 | ✓ |
| B 段 id | 恰 `[907, 1034]` 全 **128** 个 | 同 | ✓ |
| **两段之间的文件** | **无**（`28 < id < 907` 为空集） | 空 | ✓ |
| 第三段 / 越界 id | **无** | 空 | ✓ |
| 每个 id 的成员 | 全部恰 `jpg`+`json` 两份 | 同 | ✓ |
| `frame_0000001034.json` 的 `capture_unix_s` | **`1786939588.328`** | 同 | ✓ |
| `frame_0000000028.json` 的 `capture_unix_s` | **`1787250613.018`** | 同 | ✓ |
| `latest.json` 的 `frame_id` | **28** | 28 | ✓ |

两个时戳换算到本机时区（EDT，`date +%Z%z` = `EDT-0400`）分别是 **2026-08-17 00:06:28**
与 **2026-08-20 14:30:13**——与 F12 的机制陈述（B 段是 B3 的保留帧尾、A 段是 08-20 那次
未放行 Play 的产物）逐项自洽。**本角色未对该机制另作推断，只据实复核归属**。

**门 1 —— 重测七项钉住值（全 64 位）**：七项全部与接受轮 69 §2.21 两张表逐项相等。

| 项 | 实测计数/行数 | 实测字节 | 实测 SHA-256（全 64 位） | 与钉住值 |
|---|---|---|---|---|
| B 组 `frames/` id 907…1034 | **256** 项 | **5513679** | `568b6b984376211b430ce1c016607e3cda3c3ba26c1ac43ef3ec4a1060d9a815` | 相等 |
| `runtime/body_command.json` | **15** 行 | **331** | `f79bc73dc313debc2933cc457b1528c7e98e96e7f97d44adcb38ec9d79b05b84` | 相等 |
| `runtime/gimbal_command.json` | **15** 行 | **341** | `6f9358d255f96b51ef91d9662f746616e4e1f8c457a8115ba7b9442cb2294bae` | 相等 |
| `runtime/tracking_observation.json` | **18** 行 | **454** | `3c677ab693076af5c4c97eeff3786e743f583f0bd44141a7bc3a5bf056266bf4` | 相等 |
| A 组 `frames/` id 0…28 + `latest.json` | **59** 项 | **939238** | `39698be45e69d7d0c8cb1632f58f39cdf8972f5b1085a0031b1a65f5244d9a7f` | 相等 |
| `runtime/m3_body_truth.jsonl` | **29** 行 | **30300** | `7c6eb5f744f3c45e088e0e3322e2363193a557cae7bc1518537495bd90c3c75c` | 相等 |
| `runtime/metrics.json` | **61** 行 | **2020** | `c3bb6f6da39953d1f3dbdfd0d4de8a926c11281bdfc970427f44a27c0b0d4a6d` | 相等 |

两个「聚合」按 `…-arm-a-trial-2.md` §B.3 的口径计算（目录内每文件
`<sha256>  <相对路径>\n` 行、整体排序后拼接再取 SHA-256，等价于
`cd <dir> && shasum -a 256 * | sort | shasum -a 256`）。**移动前两组文件尚同处
`runtime/frames/`，故按各自的文件名集合分别计算**——该口径只依赖目录内相对路径，
对整体移动稳定，正是「移动前后相等」得以成立的原因。
行数一律 `wc -l` 口径（`\n` 计数）。

**七个 destination 移动前均不存在** ✓（7/7，含在上述 38 条内）。

## A.2 移动执行：**先 B 组（不可再生），后 A 组**

移动**不删除、不覆盖、不改名以外的任何操作**；全部用 `mv`。两个 destination 目录在其
组的移动动作内新建（源是同一目录的子集，无法先移后建）。

**B 组 —— B3 的 shared 侧残留（4 个 destination）**

| Source | Destination |
|---|---|
| `runtime/frames/` 内 id 907…1034 的 256 份 | `runtime/frames.arm-b-trial-3-shared-residue-hold/` |
| `runtime/body_command.json` | `runtime/body_command.arm-b-trial-3-shared-residue-hold.json` |
| `runtime/gimbal_command.json` | `runtime/gimbal_command.arm-b-trial-3-shared-residue-hold.json` |
| `runtime/tracking_observation.json` | `runtime/tracking_observation.arm-b-trial-3-shared-residue-hold.json` |

B 组移动完毕时实测：hold **256** 项，`runtime/frames/` 剩 **59** 项。

**A 组 —— 2026-08-20 那次未放行 Play 的产物（3 个 destination）**

| Source | Destination |
|---|---|
| `runtime/frames/` 内 id 0…28 的 58 份 + `latest.json` | `runtime/frames.unreleased-play-20260820-hold/` |
| `runtime/m3_body_truth.jsonl` | `runtime/m3_body_truth.unreleased-play-20260820-hold.jsonl` |
| `runtime/metrics.json` | `runtime/metrics.unreleased-play-20260820-hold.json` |

A 组移动完毕时实测：hold **59** 项，`runtime/frames/` 剩 **0** 项。

命名与四处既有 void hold 完全同构的平铺形式（接受轮 69 §D / 复核 N42），**不进
`runtime/test-results/`**，故不可能被点成第八处 post-run 归档；名字里**没有** `3of6`
一类会随认识变化而失效的数字。

## A.3 移动后核对：**36 条机械核对，36 PASS / 0 FAIL**

| 核对 | 实测 | 结果 |
|---|---|---|
| `runtime/frames/` 目录仍存在（未删除、未新建） | 是 | ✓ |
| `runtime/frames/` 项数 | **恰 0**（315 = 256 + 59 全部移出） | ✓ |
| B hold 项数 / `bytes_total` / 聚合 | **256** / **5513679** / `568b6b98…a815` | ✓ 等于钉住表 |
| B hold id 段 | 恰 `[907, 1034]` 全 128 个，无非 `frame_*` 条目 | ✓ 与移动前一致 |
| A hold 项数 / `bytes_total` / 聚合 | **59** / **939238** / `39698be4…9a7f` | ✓ 等于钉住表 |
| A hold id 段 | 恰 `[0, 28]` 全 29 个 + `latest.json` | ✓ 与移动前一致 |
| 五个平铺 destination 的行数/字节/SHA-256 | 逐项等于钉住表（全 64 位见 §A.1） | ✓ |
| 五个 shared 槽位已腾空 | `body_command.json` / `gimbal_command.json` / `tracking_observation.json` / `m3_body_truth.jsonl` / `metrics.json` 均**不存在** | ✓ |
| 归属复核重做（移动后） | B hold `frame_…1034.json` = `1786939588.328`；A hold `frame_…0028.json` = `1787250613.018`；A hold `latest.json` 的 `frame_id` = 28；两 hold id 段**无交叉** | ✓ |

七个 destination 逐项等于 §2.21 两张表，两个目录的 id 段与移动前一致。

## A.4 承重核对：**八条 `--verify` 全部退出 0 且逐字复现**

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id <ID>
```

```text
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214, "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783243208518966, "run_id": "p1-m3-body-001-arm-a-trial-5", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-1", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
```

八条逐字等于各自冻结值（臂 A 五个 `WITHIN_RANGE`；B1/B2/B3 均 `SCENE_DEGENERATE` /
`1.0` / 窗口 `1.0`）。**这是本节的承重核对**：它证明七次移动没有碰到任何已判定 run
的字节。

**§A.3 的 36 条在八条 `--verify` 之后又跑了一遍，仍 36/36**——即 `--verify` 对本轮
两个新 hold 零副作用，该性质实测而非假定（沿 §2.20 的做法）。

## A.5 附加自查（**非 §2.21 规定项**，不构成任何门）

为佐证「只动了该动的七项」，另行只读复算了七处 post-run 归档与既有 hold。**七处归档
全部完好**：各恰 **6** 项、`frames/` 各 **257** 项，七个聚合与 §2.20 第 5 项的钉住值
相等（B2 一组按 64 位全值 `71f65dca…0f85` 核对，其余六组按 `<前 8>…<后 4>` 缩写口径
核对）：

`ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` /
`9dc67a76…a62b` / `09f1ac61…524c` / `71f65dca666cc37d91569a9b2b3893c0721e436a1b09756f5e644c0052a20f85`

既有 hold 的当轮实测（**登记用，本轮未与任何钉住表比对，不作证据主张**）：
`frames.1b-diagnostic-hold` 257 项、`frames.arm-a-trial-1-void-attempt-1-hold` 93 项、
`…-attempt-2-hold` 109 项、`…-attempt-3-hold` 257 项、
`frames.arm-a-trial-2-void-attempt-1-hold` 257 项、`frames.qual3-leftover-hold` 8193 项。
四处 void hold 的计数与 §2.20 第 3 项记载的 **257 / 93 / 109 / 257** 一致。

## A.6 非门事实登记（§2.21「其他约束」第 2 条）

`runtime/road_scene_audit.json` 与 `runtime/route_corridor_audit.json` 的 mtime 实测
同为 **2026-08-20 14:30:06**（本机 EDT），与 §2.21 记载相符。**本节未触碰这两个文件**；
两者从不属于六项 shared 成员、从未进过任何归档、每次 Play 都会被重写，故其 mtime
**不得**被读作批次期间存在额外 Play 的证据。

## A.7 边界与未执行项（据实）

- **零 Play、零采集 ID 创建/消耗、零 API/配额消耗、零分析、零 `--finalize`、零 trial
  计入**。A 组的产物**永不**作为任何 run 的输入；B 组是 B3 的残留，B3 已由接受轮 67
  判定有效，**保全不改变任何已判结果**，也**永远不会**补齐为一份完整归档
  （`m3_body_truth.jsonl` 与 `metrics.json` 已永久覆盖）。
- 归档仍为 **7 处 < 有效 run 8 次**，与 revision 25 抬头 C 条一致；本节不改变该结论。
- **未执行**：§2.22 的十项、§2.0 (b)/(c)/(d)、§3 任何步骤、任何 `--compare`、任何调参。
  §2.22 与 (b)/(c) 依用户 2026-08-20 的放行条件等复核结论；F12/F13 的闭合是复核角色的
  定点复看，本角色不自判闭合。
- **操作单 `…-1c-preflight.md` 本批次一字未改**：§2.21 的「待执行 / 已执行」标注属修订级
  改动，由接受角色在下一次修订抬头里轮换，本角色不代劳。
- **本节未经独立复核**。按 AGENTS.md「完成规则」，本文件只是实现者证据。

## A.8 复核范围（给复核角色）

- 本文件 §A 全文；对照 `…-1c-preflight.md` revision 25 §2.21 的两张钉住表与两道门。
- 实测复算建议：`runtime/frames/` 为 0 项且目录存在；两个新 hold 的项数/`bytes_total`/
  聚合（口径见 `…-arm-a-trial-2.md` §B.3）；五个平铺 destination 的行数/字节/SHA-256；
  两个 hold 的 id 段不重叠且分别为 `[907,1034]` / `[0,28]`；三个包内时戳/`frame_id`；
  八条 `--verify` 逐字复现。
- 一并待闭合：**F12（CLASS_1）与 F13（CLASS_2）** 由定点再检查闭合
  （`NOT_MECHANIZABLE`）；CLASS_3 **P7/P10** 随 (c) 批次。

---

# B. B4 的 Play 前置（§2.22 十项 + §2.0 (b) + §3 步骤 0 / 0′ 第 1 步）

日期 2026-08-20，实现角色。交接来源：接受轮 70（消费复核轮 14 的 `PASS_WITH_NOTES`、
应用 P11/P7、发 revision 26、§2.0 (a) 成立）。**零 Play、零采集 ID 创建/消耗、零
`runtime/` 写入、零代码/测试/config/scenario/model 改动、零操作单改动。** 批次开始与
结束时 `git status --porcelain` 均为空。

**放行依据（§2.0 (a)）**：用户 2026-08-20 逐字授权「执行，授权执行play」
（`docs/authorizations.md` 同日条目，接受角色代录）。该条解除的是用户自己 2026-08-20
加的复核前置；**B4 的额度仍是恰一次 Play**，本就在 2026-08-14 批量 GO 之内。**B5、
重试、调参、`--compare` 均未授权**；**任何 void 终态仍立即中止批量授权并回用户**。

## B.1 §2.22 十项 Play 前只读核对：**156 条机械核对，156 PASS / 0 FAIL**

| §2.22 项 | 核对内容 | 结果 |
|---|---|---|
| 1 | 六个 shared **文件** | `body_command` / `gimbal_command` / `tracking_observation` / `metrics.json` / `m3_body_truth.jsonl` / `scenario_config.json` 均**不存在** ✓（6/6） |
| 2 | `runtime/frames/` | **存在且恰 0 项**（§2.21 移出的 315 项，目录未删未建）✓（2/2） |
| 3 | 四处旧 hold | 帧计数 **257 / 93 / 109 / 257**；1b 五个 SHA、attempt-1/2 的 truth 行数+SHA 与 metrics SHA、attempt-3 run hold **恰两文件**及其 `frames.jsonl`（755 行 / 951704 B）与 `manifest.json`（207 行 / 7857 B）行数/字节/SHA、truth（627 行 / 641080 B）与 metrics（61 行 / 2084 B）全部与 §2.5 第 4–7 项原表相等 ✓（28/28） |
| 4 | **八个正式 run 目录** | A1…A5 + B1 + B2 + **B3** 各**恰 11 份**且各含 `m3_body_analysis.json` ✓；**八条 `--verify` 各退出 0 并逐字返回冻结值** ✓（48/48，原文见 §B.2） |
| 5 | **七处 post-run 归档** | 各**恰 6 项**、`frames/` 各 **257** 项、七个聚合与钉住值相等 ✓（21/21）。归档 **7 处 < 有效 run 8 次**，差额恒为 B3——**不是缺项，不据此判不符** |
| 6 | 活动标记 + attempt-1 void hold | 八个具名标记均**不存在** ✓；void hold **恰 10 份**、文件名集合等于冻结十项、**零隐藏项**、三个钉住 SHA 相等 ✓（14/14） |
| 7 | **unreleased hold（§2.21 A 组）** | `frames.unreleased-play-20260820-hold/` **恰 59** 项、id 段 `[0,28]` + `latest.json`、聚合 `39698be4…9a7f`；truth **29** 行 / **30300** B、metrics **61** 行 / **2020** B，SHA 均等 ✓。**并集等式（N45）**：本项与第 10 项两目录合并后的聚合 = **`274e9804098c337d02245c64780c349c5c886c6633e4d8e7e1364d8da3e52d4c`** = §2.21 执行前整目录聚合 ✓（11/11） |
| 8 | **B4 create-once 前置** | `runtime/runs/p1-m3-body-001-arm-b-trial-4/` **不存在** ✓（1/1；预检 JSON 的 35 个 `run_directories` 中同样无此名） |
| 9 | **臂 B 专属** | corridor 实测 SHA = config `artifact_sha256` = §1 钉住 `9e2956ad…c800` ✓、`prisms` 实际 **779** 条 = `instance_count` ✓、`tether_corridor_check` = `true` ✓；`_expected_policy('…-arm-b-trial-4')` = `threshold` ✓、`POLICY_PLANNER['threshold']` = `threshold-corridor-v1` ✓、`expected_acquisition_ids('b')[3]` 逐字相等 ✓、`-attempt-1`/`-attempt-2` 在 `_expected_policy` 与 `canonical_trial_id` **两个**函数上均抛 `run_id_not_frozen_trial` ✓（12/12） |
| 10 | **B3 shared 残留 hold（§2.21 B 组）** | `frames.arm-b-trial-3-shared-residue-hold/` **恰 256** 项、id 段 `[907,1034]`、**无 `latest.json`**、聚合 `568b6b98…a815`；三个平铺发布件 hold 的 15/331、15/341、18/454 与三个 SHA 全等 ✓（13/13）。四者**都不是 post-run 归档**，不计入第 5 项的 7 处 |

分项计数：1: 6/6、2: 2/2、3: 28/28、4: 48/48、5: 21/21、6: 14/14、7: 11/11、8: 1/1、
9: 12/12、10: 13/13。**全套核对跑了两遍**——§B.3 预检**之前**一遍、**之后**一遍，两遍
均 156/156，即预检对现场零副作用（该性质除预检自证的 `unchanged = true` 外另有实测）。

> **口径注（revision 26 C 条 / 复核 N44）**：第 1 项的「六个 shared **文件**」含
> `scenario_config.json` 而不含 `frames/`；§2.21 与第 5 项的「六项 shared **成员**」
> 相反。`frames/` 在本表由第 2 项单列，两处口径本就一致，无操作歧义。

## B.2 八条只读 `--verify`：全部退出 0 且逐字复现

```text
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214, "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783243208518966, "run_id": "p1-m3-body-001-arm-a-trial-5", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-1", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
```

**本轮采集 `…-arm-b-trial-4` 尚不存在，第 4 项不对它跑 `--verify`**；它由第 8 项核对为
「run 目录不存在」。

## B.3 §3 步骤 0 环境预检：**退出码 0，`status = "PASS"`**

```bash
.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json
```

退出码 **0**；stdout 单个 JSON 对象，要点逐字如下（完整 JSON 已在本批次运行时产出，
下列字段逐字取自该输出）：

- `status` = **`PASS`**
- `interpreter.executable` = `~/TetheredDroneTracking/.venv-yoloe/bin/python`，
  `prefix` = `~/TetheredDroneTracking/.venv-yoloe`，`python_version` = `3.12.13`
- `packages`：`cv2` raw `5.0.0` = pin `5.0.0`（pin 源 `nanotrack spec opencv.tested_version`）、
  `torch` `2.13.0`、`torchvision` `0.28.0`、`ultralytics` `8.4.104`，四者 raw 与 pin **逐字相等**
- `nanotrack`：`nanotrack-v2` / `opencv-dnn-default/cpu` / `opencv_version` `5.0.0` /
  `preprocessing_id` `opencv-tracker-nano-5.0.0-default-v1`；backbone
  `530bdd0cd00f19afab79a863e71ba71e3312395a5dc9151af675082bdaaa2fc4`、neckhead
  `0d8c0637be849f092cc7236cae02e55c8b9455ebe37ba50601d6115db4247cd9`
- `reanchor_config.sha256` =
  `593734d67ada73a0304d67d27c6ae536be616d2180f744336b85ff6e0ac706d2`，
  `schema_version` `tethered-detector-reanchor/v1`，`carrier`
  `minimal-triple-gated-re-anchor`，`device` `cpu`
- `constructors`：`YoloeProposer`、`DinoV2Embedder`、`NanoTrackV2Tracker` 三者**实际构造**成功
- `side_effect_identity.unchanged` = **`true`**；`before` 与 `after` 的
  `run_directories` **逐项相等，共 35 个**，其中**无** `p1-m3-body-001-arm-b-trial-4`；
  四个 guarded file 前后均 `present: false`

stderr 只有第三方库的告警（OpenCV graph-engine target、`tifffile` 缺失、xFormers 不可用
三类），**不影响退出码与 `status`**，据实登记。

## B.4 §3 步骤 0′ 第 1 步：解释器逐字值落盘

按 §2.22 抬头具名的落盘地即本文件，从 §B.3 预检 stdout JSON 取 `interpreter.executable`
的**逐字值**记入：

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python
```

与 §1 冻结的唯一合法入口 `.venv-yoloe/bin/python -m controller.track_loop` 的解释器部分
一致（前者是后者的绝对路径形式）。

**尚未执行**：步骤 0′ 第 2 步（启动 tracker 时命令行首解释器路径与该值字符串逐字相等，
并把实际命令行原文记入本文件）——本批不启动 tracker，该步在获授权的那次 Play 中执行。

## B.5 §2.0 (b) 报告（本批次测量时点）

```text
$ git rev-parse HEAD
62339fbc260ed8f539ad4ff114fc2a63ed0f7057

$ git status --porcelain
（空输出）

$ grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md | tail -1
passed_candidate: fcb22a75b3b7c83fb8b31e527683d1467df6cb1f
```

`<BASE>` = **`fcb22a7`**（**复核轮 14** 的通过候选，运行时现取、未手写；较上一轮的
`6e81bc2` 前移了两轮——`fcb22a7` 正是本文件 §A 那批 §2.21 的候选）。

```bash
$ git diff --name-only fcb22a7..HEAD
docs/authorizations.md
docs/current-status.md
docs/evidence/P1-M3-BODY-001-1c-preflight.md
docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md
docs/reviews/P1-M3-BODY-001.md
```

**五个路径，全部是文档**，由区间内 **2 条**提交产生（复核轮 14、接受轮 70）。
**测量侧 diff 为空**——`controller/ Assets/ config/ ProjectSettings/
Packages/packages-lock.json tools/ tests/` 对 `fcb22a7` 零改动，故八次已判定采集与
即将进行的 B4 跑在同一份已复核代码上。

**PLAY_GOVERNING 子集 = 恰 1 条**：操作单 `docs/evidence/P1-M3-BODY-001-1c-preflight.md`
（round 40 裁定其本身为 PLAY_GOVERNING 成员），现为 **revision 26**，纯文本修订。
**§4 CLI 块差异本角色亲自复算**（不采信抬头自述）：抽出两侧 `## 4.` 下的 bash 块，

```text
base(fcb22a7) 19 行  SHA-256 154b06a6353249d5a192b5b8464aaaa8a0002b51cd7a948c69b89f3abf9dee2f
HEAD          19 行  SHA-256 154b06a6353249d5a192b5b8464aaaa8a0002b51cd7a948c69b89f3abf9dee2f
diff = 0 行
```

**逐字节相同**，与 revision 26 抬头「§4 CLI 对 revision 23/24/25 一行不差」相符。
revision 26 只应用两条 CLASS_3 补丁（P11 时态、P7 引用精度）并加两处注解（N44/N45），
**零门、零数值、零 ID、零 disposition、零槽位改动**，方向只增澄清不放宽。

> **本 (b) 报告绑定测量时点的 HEAD `62339fb`。** 本批次落盘并提交后 HEAD 会前移，
> 该报告即过期（先例：`…-arm-b-trial-3.md` §B → §C 因同样原因复报两次）。
> **(c) 之前若 HEAD 再动，必须由本角色重取 (b)**；(d) 的「唯一未提交差异 =
> `docs/unity-test-log.md`」不放宽。BC-BODY1-21 自 (c) 写入起冻结操作单。

## B.6 边界与未执行项（据实）

- **零 Play、零采集 ID 创建/消耗、零 `runtime/` 写入**：本节只做只读读取（`open('rb')`
  / `stat` / `listdir`）、八条 `--verify`（写盘前返回的只读路径）与预检（自证
  `unchanged = true`，另经 156/156 前后两遍实测佐证）；无 `mv`/`rm`/`mkdir`/重定向写入。
- **未执行**：§2.0 **(c)**（归接受角色，实现角色对 `docs/unity-test-log.md` 只读）、
  **(d)**、§3 步骤 0′ 第 2 步及其后所有步骤、门 1/2/3/4、tracker、`--finalize`、
  `--compare`、任何调参。
- **本批未经独立复核**。按 AGENTS.md「完成规则」，本文件只是实现者证据。

## B.7 复核范围（给复核角色）

- 本文件 §B 全文；对照操作单 revision 26 §2.22 的十项期望、§2.0 四步与 §3 步骤 0/0′。
- 实测复算建议：十项的 156 条（第 3 项按 §2.5 第 4–7 项原表、第 7/10 项按 §2.21 两张
  钉住表、第 5 项按 §2.20 第 5 项聚合表）、并集等式 `274e9804…2d4c`、八条 `--verify`、
  预检退出码/`status`/`unchanged`/`run_directories` 无 B4、§4 CLI 块两侧 SHA 相等。
- 本轮无新增 CLASS_3 待办：接受轮 70 已把 P11/P7 应用完毕。

---

# C. B4 的 Play：四门 + tracker（**执行中**，2026-08-20，实现角色）

§2.0 四步全部成立：(a) 用户 2026-08-20 逐字授权（账本已提交）、(b) 本文件 §B.5 于
`62339fb` 并由接受角色在 `667fbe2` 复算、(c) 接受角色写入 `docs/unity-test-log.md`
（`PRE_PLAY_RELEASED`，点名 HEAD `667fbe2`，留未提交）、**(d) 发令时刻实测**
`git diff --name-only` **逐字只有** `docs/unity-test-log.md` 且零未跟踪文件。
**发令时刻另复查 §2.22 十项，仍 156/156。** 用户随后进 Play **恰一次**并尽早暂停，
报告「已暂停」。

## C.1 门 1 —— 暂停窗口（**启动 tracker 之前落盘**，revision 12 记录型条款）

**导出命令原文**（在将驱动 tracker 的同一解释器下，只读）：

```bash
.venv-yoloe/bin/python - <<'PY'
import json, pathlib, re
d = pathlib.Path("runtime/frames")
rx = re.compile(r"^frame_(\d{10})\.json$")
recs = []
for p in sorted(d.glob("frame_*.json")):
    m = rx.match(p.name)
    if not m: continue
    j = json.loads(p.read_text())
    recs.append((int(m.group(1)), j.get("simulation_time_s"), j.get("frame_id")))
ids = [r[0] for r in recs]
mx = max(recs, key=lambda r: r[1])
PY
```

**保留帧编号范围**：`0 … 30`，共 **31** 份元数据（现场 63 项 = 31 帧 ×2 +
`latest.json`）；编号**连续无缺口**，每份的 `frame_id` 与文件名逐项一致，
`simulation_time_s` 随编号**单调不减**。

**导出的数值本身**：

```text
reported_sim_t = max(simulation_time_s) = 6.184971809387207   （来自 frame 30）
```

判据 `2.000000 <= 6.184971809387207 < 10.000000` **成立** → **门 1 PASS**。
两侧余量 `4.184972 s` / `3.815028 s`。**该值由保留帧机械导出，未取用户口报**
（冻结载体无计时 HUD，用户只报「已暂停」——接受轮 47 更正）。
**披露照旧**：该值是暂停真实时刻的**下界**（末帧写盘后、暂停生效前不足一帧不可见），
COORD-007 §4.1 的缺口未被本条款消除，本轮**不**因此调整阈值（BC-BODY1-15 (d)）。

## C.2 门 2 —— 最低保留帧

最低保留帧编号恰为 **`0`**（与 §C.1 同一次导出的逐字输出）→ **门 2 PASS**。
`latest.json` 的 `frame_id` = `30`，与保留帧上界一致。

## C.3 门 3 —— 冻结框匹配（用户目检）

`--dump-frame 0` 导出退出码 **0**，图 **640×480**；scratchpad 内叠加**已冻结**像素框
`(177, 195, 77, 73)`（`min_side = 73 px`）供目检——**未重新框选、未重新估框、未做
六位小数化、未读任何真值**；叠加图只落在会话 scratchpad，不进仓库、不进 `runtime/`。

**用户目检结论（逐字）**：「**匹配**」→ **门 3 PASS**。现场未做任何调整。
**三门全部 PASS，互不覆盖。**

## C.4 门 4 —— 启动前命令行核对 + §3 步骤 0′ 第 2 步

命令行由操作单 §4 的 bash 块**机械取出**（`awk` 抽取，非手抄），**只把第 1 行的解释器
换成预检 JSON 的绝对路径**，其余 **18 行与 §4 逐字节相同**（`diff` 实测仅第 1 行）。

**实际将要执行的完整命令行原文**（19 行，SHA-256
`b764fc6c39e0160cd904f4b8b9d8bc316bbb728daf7751ac3282beb54c062ded`）：

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python -m controller.track_loop \
  --tracker nanotrack-v2 \
  --tracker-model-dir runtime/models/nanotrack-v2 \
  --tracker-model-spec config/nanotrack-v2.models.json \
  --reanchor-config config/detector-reanchor.models.json \
  --condition follow \
  --track-id target-0 \
  --scenario-id deterministic-loop-default \
  --ground-plane-y-m 0.2 \
  --run-id p1-m3-body-001-arm-b-trial-4 \
  --init-frame 0 \
  --init-box 0.2765625 0.40625 0.1203125 0.15208333333333332 \
  --planned-duration-s 130.0 \
  --maximum-ground-range-m 1000.0 \
  --expires-after-s 1.0 \
  --poll-interval-s 0.02 \
  --body-policy threshold \
  --body-planner-config config/p1-m3-body-001.json \
  --body-scenario-config config/scenario.default.json
```

**肯定项（两条，逐字包含）**：`--body-policy threshold` **True**、
`--run-id p1-m3-body-001-arm-b-trial-4` **True**。

**否定项（全须 False）**：`arm-a-` **False**、前几轮 run-id（`arm-b-trial-1/2/3`）
**False**、`-attempt-` **False**、hold **False**、`--compare` **False**。

> **口径披露（本轮自查，据实登记，不改判据）**：`hold` 一项若按**裸子串**判会
> **假阳性**——`threshold` 字面含 `hold`，而 `--body-policy threshold` 正是本门**要求
> 存在**的肯定项。本角色改按 hold 的**命名规约**判定（token 含 `-hold`，或以 `hold`
> 结尾且不等于 `threshold`）：命令行 42 个 token 中含 `hold` 子串的**只有 `threshold`
> 一个**，符合规约者 **0 个**，故该否定项为 **False**。这是核对实现的精确化，
> **不放宽任何判据**——真出现 `*-hold` 的 run-id 或路径仍会被抓到。B3 轮同样报
> `hold` False，与本口径一致。

**§3 步骤 0′ 第 2 步**：命令行首解释器路径
`~/TetheredDroneTracking/.venv-yoloe/bin/python` 与步骤 0 预检 JSON 的
`interpreter.executable` **字符串逐字相等**（§B.4 已落盘该值）。

**门 4 PASS。** 四门全部落盘于本节，**均在启动 tracker 之前**。

## C.5 完成握手（§3 步骤 4，逐字执行）

**三项同时观察到**：

1. tracker 进程**自然退出码 `0`**（非信号终止、非人工终止）；
2. stdout final JSON 指向**同一采集 ID** 的 `summary.json`：
   `{"qualification_metrics_error": null, "records": 651, "run_id":
   "p1-m3-body-001-arm-b-trial-4", "state": "TRACKING", "summary":
   ".../runtime/runs/p1-m3-body-001-arm-b-trial-4/summary.json"}`；
3. run 目录内 `metrics.final.json` 与 `summary.json` **均已存在**。

**确认词由只读命令机械产出，未人工复述**：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --validate-completion \
  --runtime runtime --run-id p1-m3-body-001-arm-b-trial-4 \
  --tracker-exit-code 0 --tracker-final-json '<track_loop 最后一行 JSON 原文>'
```

退出 **0**，输出逐字 **`TRACKER_AUTO_COMPLETE_CONFIRMED`**。

**BC-BODY1-29 遵守**：确认词产生后本角色的**下一个动作**就是请用户退出 Play——读 run
记录、写本节、写状态板全部在用户退出**之后**。**用户报告（逐字）**：「**已退出，无报错**」
→ Console 清洁（**待接受/辅助角色代录进 `docs/unity-test-log.md`**，本角色对该文件只读）。

## C.6 绑定分析：退出 0，臂身份三层核对通过

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-b-trial-4
```

退出 **0**；run 目录由 4 份增至 **11 份**（含 create-once 的 `m3_body_analysis.json`）。

**臂身份三层核对通过**：`receipt.body_policy` = **`threshold`**、
`receipt.body_planner_name` = **`threshold-corridor-v1`**，与冻结 ID 推导的期望臂逐项
相等。**无 predecessor / attempt 字段**——B4 的 ID 从未被消耗，两个前驱门都不触发
（与 §1、§2.22 第 8 项预写一致）。`frame_record_count` **651**、`truth_record_count`
**852**、首末帧 `0` / `851`。

**准入与两条域完整性门**：三条判据在主路径上都是无条件 `raise`，**退出 0 即三条全过**。
下界实测 `final_unwrapped = 342.4017822330673 m >= P = 212.97056274847716 m` ✓。

**九条 `--verify` 全部退出 0 且逐字复现**（A1…A5 + B1 + B2 + B3 + **B4**）：臂 A 五个
`WITHIN_RANGE`，**B1/B2/B3/B4 均 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`**。
**前八个 run 一字节未动。**

## C.7 主结果与机体运动（**归因归接受角色，本节只报事实**）

| 项 | B1 | B2 | B3 | **B4** |
|---|---|---|---|---|
| `full_loop_c_geom` | `1.0` | `1.0` | `1.0` | **`1.0`** |
| `h1.disposition` | `SCENE_DEGENERATE` | 同 | 同 | **`SCENE_DEGENERATE`**（天花板 `0.95`，第四次） |
| 窗口 `C_track|geom` | `1.0` | `1.0` | `1.0` | **`1.0`** |
| `body_motion_effort_m` | `88.64522663177961` | `75.26945194958653` | `91.174630127364` | **`88.72384065309268`** |
| `body_path_length_m` | `61.42306359956821` | `49.16248028068326` | `64.4545385428812` | **`61.40687110469029`** |
| `planner_switch_count` | `11` | `11` | `11` | **`11`** |
| `nees_median` | `5.067625439804517` | `5.2993597343857255` | `5.196313303659595` | **`5.244988577303893`** |
| `min_side_ge20_share` | `1.0` | `1.0` | `1.0` | **`1.0`** |
| 停留 / 圈数 | `41.389801 s` / `1.618675` | `29.602264 s` / `1.509862` | `76.803711 s` / `1.952997` | **`40.197784 s` / `1.607742`** |

**(iv) reason 直方图（621 decision 帧）**：`margin_below_trigger+corridor_blocked`
**324**、`within_hysteresis_band` **118**、`margin_below_trigger` **95**、
`margin_above_release` **78**、`margin_below_trigger+corridor_shortened` **6**。
**`no_observation` / `no_platform_state` / `no_estimate` / `planner_exception` 与
`publish_failure_fallback` 全 0 帧。** 不带 planner 的行 161（追平期 catch-up，合法）。
`frames.jsonl` 共 **782** 行。

> **派生口径本轮先校准再用**（沿 §D.7 先例）：同一段代码对 B1 复出 623 =
> 324/116/95/82/6、B2 复出 622 = 339/109/93/75/6、B3 复出 626 = 319/121/95/85/6，
> 圈数复出 `1.618675` / `1.509862` / `1.952997`——与三轮已发布数字**逐项相等**。
> 故 B4 的三个数与前三轮同底。

**(iii) `body_motion_effort_m > 0`**，**不触发**「整圈定义域内零位移即停」分支
（§3 步骤 6 臂 B 专属条件）。**(i) post-tracker 停留**：tracker 最后一帧
`130.185546875 s`、Play 最后一条 truth `170.38333129882812 s`，差
**`40.197784423828125 s`**——较 B3 的 `76.803711 s` **减半**，落回轮 67 建议的
30–40 s 区间。**(ii) 圈数** `342.4017822330673 / 212.97056274847716` =
**`1.607742299284109`**。**(i)(ii) 均不构成任何门**（BC-BODY1-30）。

其余披露：`loop_gimbal_saturated_share = 0.5037742601351012`、
`loop_tether_saturated_share = 0.10164893814661166`、窗口内云台饱和 **`0.0`**、
窗口内系绳饱和 `0.2230185546875`；`loop_frame_count` 530 / `window_frame_count` 155；
`h1.ceiling` `0.95` / `lower_bound` `0.5645`。

**只登记、不调参（BC-BODY1-15 (d)）**：两条预登记限制各得**第四次**确认
（`C_geom` 四次 `1.0`；`min_side_ge20_share` 四次 `1.0`）。`planner_switch_count`
连续**四次**恰 `11`。n=3 时已撤下的方向性读法**仍不重提**：B4 阻塞 324（居中）配位移
`88.724`（居中），四点仍不支持任何单调读法。

## C.8 边界与未执行项（据实）

- **恰一次 Play**，采集 ID `p1-m3-body-001-arm-b-trial-4` **已消耗**；**零 void 终态**
  （终态对照由接受角色认定），故 2026-08-14 的批量授权就此不被中止。
- 零代码/测试/config/scenario/model/阈值/CLI 改动；**零操作单改动**（BC-BODY1-21 全程
  遵守——(c) 写入后本文件一字未动）。
- **§2.21 的两处保全 hold 未被本次 Play 触及**：B3 的 256 份帧在 `runtime/frames/` 之外，
  写盘器的按 id 淘汰够不到它们。
- **未执行**：`--finalize`、`--compare`（须十次齐备并单独授权）、任何调参、B5 的那次
  Play（仍在批量 GO 内，须各走自己的 §2.0 (a)–(d)）。
- **`docs/unity-test-log.md` 的 (c) 条目保持未提交**，按其自述随接受角色的归因批次入库
  （先例 B1 `4b76b64`、B2 `0af7344`、B3 `8820678`）——实现角色对该文件只读，从不提交。
- **本批未经独立复核**；主结果的归因（`B4_VALID_TRIAL` 与否）归接受角色。

## C.9 复核范围（给复核角色）

- 本文件 §C 全文；对照操作单 revision 26 §3 步骤 0′/1–6、四门判据与 §5 四种 void 终态。
- 实测复算建议：门 1 的保留帧导出（0–30，`6.184971809387207`）、门 4 命令行 SHA
  `b764fc6c…2ded` 与 §4 块的 18 行相等、握手三项与确认词、九条 `--verify`、直方图/停留/
  圈数的派生口径校准（对 B1/B2/B3 复出已发布值）、`body_motion_effort_m > 0`。
- **门 4 `hold` 否定项的口径精确化已在 §C.4 披露**，请一并复核该判定是否放宽了判据
  （本角色认为没有：42 个 token 中含 `hold` 子串者只有 `threshold`）。
