# P1-M3-BODY-001 arm B trial 5 证据（操作单 revision 27）

**范围**：用户 2026-08-14 批量授权 B2–B5 中的**第四次**（B5）。执行合同 =
`docs/evidence/P1-M3-BODY-001-1c-preflight.md` **revision 27**。

**状态**：**§A 已完成**（2026-08-20，实现角色）——§2.23 B4 的 post-run 归档。
**B5 的槽位轮换与 Play 前核对尚未起草**：接受轮 71 §G 把「B5 之前是否再走一轮独立
复核」留给用户决定，另发修订后才有 §2.x 核对节。**在此之前不得进入任何 Play。**
本文件按 §2.19 先例（在下一 trial 的预备批次执行、落盘于下一 trial 的证据文件）
承载 §2.23 的结果；B5 自身的前置与执行记录将来追加于此。

---

# A. §2.23 B4（有效 trial）的 post-run 归档（**已执行**，2026-08-20，实现角色）

交接来源：接受轮 71（B4 判为 `B4_VALID_TRIAL`，臂 B **4/5**；发 revision 27）。
**零 Play、零采集 ID 创建/消耗、零分析、零代码/测试/config/scenario/model 改动、
零操作单改动。** `runtime/` 在 `.gitignore` 内，六次移动仓库侧零 diff；批次开始与
结束时 `git status --porcelain` 均为空。

**紧迫性（revision 27 A 条）**：shared 槽位此前装着 B4 的产物，而 B3 的教训是一次误入
的 Play 会当场覆盖 truth 与 metrics 且**不可恢复**。本节因此先于任何 B5 动作执行。

## A.1 移动前只读核对：**24 条机械核对，24 PASS / 0 FAIL**

六项钉住值（接受轮 71 移动前实测）逐项相等，全 64 位：

| 项 | 实测计数/行数 | 实测字节 | 实测 SHA-256 | 与钉住值 |
|---|---|---|---|---|
| `frames/` | **257** 项，id 段 `[724, 851]` 全 128 个 ×2 + `latest.json` | — | 聚合 `5ed64cf58350926ee1d2e6edf0b0a04300d7d6595865d38b40fec1be86597ebf` | 相等 |
| `m3_body_truth.jsonl` | **852** 行 | **914667** | `c6218bdefe3b0fc362af8543cecbfcc3bc838f7c4f615b384150f8af8f3d09d3` | 相等 |
| `metrics.json` | **61** 行 | **2054** | `43a5db7db4c758ed775ebdd9a45236fe4d75781cb498a6337dfb97ee34704b74` | 相等 |
| `body_command.json` | **15** 行 | **328** | `5a13b98671b2b34f858572ad455bd6a16ffdc60492ad0f74ff55efc894f80044` | 相等 |
| `gimbal_command.json` | **15** 行 | **342** | `90ae396176c385e352881e028ce5a5ed6a8d2e14562a4fa13a5ef7726836cd19` | 相等 |
| `tracking_observation.json` | **18** 行 | **459** | `e583a0d0cfa8842a071605fa8d039f5aa28c668b7403363f6a4fb94985b277d9` | 相等 |

另核对：**destination 移动前不存在** ✓、B4 run 目录 **11 份**（绝对不动）✓、
§2.21 两处保全 hold **256 / 59** 项 ✓、既有 post-run 归档 **7** 处 ✓。
聚合口径见 `…-arm-a-trial-2.md` §B.3；行数一律 `wc -l`（`\n` 计数）。

## A.2 移动执行

六项 shared 侧工件移入
`runtime/test-results/p1-m3-body-001-arm-b-trial-4-post-run/`（`mv`，零删除、零覆盖、
零分析）；移动后**只新建空 `runtime/frames/`**，**未预建任何 run 目录**。
**B4 的 run 目录 `runtime/runs/p1-m3-body-001-arm-b-trial-4/` 一字节未动。**

| Source | Destination |
|---|---|
| `runtime/frames/` | `…-post-run/frames/` |
| `runtime/m3_body_truth.jsonl` | `…-post-run/m3_body_truth.jsonl` |
| `runtime/metrics.json` | `…-post-run/metrics.json` |
| `runtime/body_command.json` | `…-post-run/body_command.json` |
| `runtime/gimbal_command.json` | `…-post-run/gimbal_command.json` |
| `runtime/tracking_observation.json` | `…-post-run/tracking_observation.json` |

## A.3 移动后核对：**36 条机械核对，36 PASS / 0 FAIL**

- 归档目录**恰 6 项**，文件名集合等于上表六项；`frames/` **257** 项、id 段 `[724, 851]`
  含 `latest.json`、聚合等于钉住值；五个单文件的行数/字节/SHA-256 **逐项等于移动前**
  （字节不随路径变）。
- `runtime/frames/` **存在且恰 0 项**（新建空目录）；五个 shared 槽位已腾空；
  `runtime/scenario_config.json` **仍不存在**（批次期间不恢复）。
- **B4 run 目录仍 11 份**；**§2.21 两处保全 hold 未被触碰**——B hold 仍 **256** 项且
  聚合仍 `568b6b98…a815`，A hold 仍 **59** 项且聚合仍 `39698be4…9a7f`。
- post-run 归档处数由 7 增至 **8**；`runtime/runs/p1-m3-body-001-arm-b-trial-5/`
  **不存在**（未预建）。

## A.4 承重核对：**九个 `--verify` 全部退出 0 且逐字复现**

```text
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214, "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783243208518966, "run_id": "p1-m3-body-001-arm-a-trial-5", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-1", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
```

**B4 的 `--verify` 在其 shared 侧被归档之后仍逐字复现**——run 目录自包含，这正是
create-once 存档的设计意图。**§A.3 的 36 条在九个 `--verify` 之后又跑一遍，仍 36/36**
（零副作用实测而非假定）。

## A.5 归档处数与差额（§2.23 明文，防误判）

归档 **8** 处 < 有效 run **9** 次，**差额恒为 B3**：其 `m3_body_truth.jsonl` 与
`metrics.json` 被 2026-08-20 那次未放行 Play 永久覆盖，完整六项归档永久不可能。
§2.21 的两处保全 hold **不是** post-run 归档、**不计入这 8 处**。
**这不是缺项，不得据此判不符。**

## A.6 边界与未执行项（据实）

- **零 Play、零采集 ID、零分析、零 `--finalize`、零 `--compare`、零调参。**
- **未执行**：B5 的槽位轮换与 Play 前核对（revision 27 C 条明写本轮不起草，待用户就
  「B5 之前是否再走一轮独立复核」给出指示后另发修订）、任何 Play。
- `--compare` 现为 **9/10**，仍需十次齐备并单独授权。
- **本批未经独立复核。**

## A.7 复核范围（给复核角色）

- 本文件 §A 全文；对照 revision 27 §2.23 的六项钉住表。
- 实测复算建议：归档目录 6 项 / `frames/` 257 项 id `[724,851]` / 聚合
  `5ed64cf5…7ebf`；五个单文件行数/字节/SHA；`runtime/frames/` 存在且 0 项；
  §2.21 两处 hold 的项数与聚合未变；B4 run 目录 11 份；九个 `--verify` 逐字复现。

---

# B. B5 的 Play 前置（§2.24 十一项 + §2.0 (b) + §3 步骤 0 / 0′ 第 1 步）

日期 2026-08-21，实现角色。交接来源：接受轮 73（消费复核轮 16 `PASS_WITH_NOTES` on
`02c7c88`、F14 闭合、轮换 B5、发 revision 28）。**零 Play、零采集 ID 创建/消耗、零
`runtime/` 写入、零代码/测试/config/scenario/model 改动、零操作单改动**
（BC-BODY1-21/-22）。批次开始与结束时 `git status --porcelain` 均为空。

**放行前置（revision 28 A 条）**：§2.0 (a) 由 **2026-08-14 批量 GO** 自身满足（该条逐
trial 枚举 B2–B5 各一次 Play，无需新 GO）；用户 2026-08-20 另加的「先复核再放行 B5」
已落账并已由**复核轮 15 → 接受轮 72 → 复核轮 16** 走完。**B5 是本批次最后一次采集**；
**任何 void 终态立即中止批量授权**并回用户（臂 B 无替代 ID）。

## B.1 §2.24 十一项 Play 前只读核对：**155 条机械核对，155 PASS / 0 FAIL**

| §2.24 项 | 核对内容 | 结果 |
|---|---|---|
| 1 | 六个 shared **文件** | 均**不存在**（§2.23 之后；`scenario_config.json` 批次期间不恢复）✓ 6/6 |
| 2 | `runtime/frames/` | **存在且恰 0 项**（由 §2.23 重建为空）✓ 2/2 |
| 3 | 四处旧 hold | **257 / 93 / 109 / 257**；1b 五个 SHA、attempt-1/2 的 truth 行数+SHA 与 metrics SHA、attempt-3 run hold **恰两文件**及四个文件的行数/字节/SHA 全部等于 §2.5 第 4–7 项原表 ✓ 24/24 |
| 4 | **九个正式 run 目录** | A1…A5 + B1…B4 各**恰 11 份**且各含 `m3_body_analysis.json`；**九条 `--verify` 各退出 0 并逐字返回冻结值** ✓ 54/54（原文见 §B.2） |
| 5 | **八处 post-run 归档** | 归档处数 **8**；各**恰 6 项**、`frames/` 各 **257** 项、八个聚合与钉住值相等（含 B4 的 `5ed64cf5…7ebf`）✓ 25/25 |
| 6 | 活动标记 + attempt-1 void hold | 八个具名标记均**不存在**；void hold **恰 10 份**、文件名集合等于冻结十项、**零隐藏项**、三钉住 SHA 相等 ✓ 14/14 |
| 7 | **§2.21 A 组** | `frames.unreleased-play-20260820-hold/` **恰 59** 项、id 段 `[0,28]` + `latest.json`、`bytes_total` **939238**、聚合 `39698be4…9a7f`；truth **29** 行 / **30300** B、metrics **61** 行 / **2020** B ✓ 7/7 |
| 8 | **§2.21 B 组** | `frames.arm-b-trial-3-shared-residue-hold/` **恰 256** 项、id 段 `[907,1034]`、**无 `latest.json`**、`bytes_total` **5513679**、聚合 `568b6b98…a815`；三个平铺件 **15/331**、**15/341**、**18/454** B ✓ 8/8 |
| 9 | **并集等式（N45）** | 第 7、8 项两目录的 `shasum` 行合并排序后取 SHA = **`274e9804098c337d02245c64780c349c5c886c6633e4d8e7e1364d8da3e52d4c`** ✓ 1/1。**只证 (SHA, 文件名) 多重集不变，不证分组**——分组由第 7/8 项的 id 段与各自聚合承担 |
| 10 | **B5 create-once 前置** | `runtime/runs/p1-m3-body-001-arm-b-trial-5/` **不存在** ✓ 1/1（预检 JSON 的 36 个 `run_directories` 中同样无此名） |
| 11 | **臂 B 专属** | corridor 实测 SHA = config `artifact_sha256` = §1 钉住 `9e2956ad…c800`、`prisms` 实际 **779** 条 = `instance_count`、`tether_corridor_check` = `true`；`canonical_trial_id('…-arm-b-trial-5')` 返回自身、`_expected_policy` = `threshold`、`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`、`expected_acquisition_ids('b')[4]` 逐字相等；`…-trial-5-attempt-1` 与 `…-trial-6` 在 `_expected_policy` 与 `canonical_trial_id` **两个**函数上均抛 `run_id_not_frozen_trial` ✓ 13/13 |

分项：1: 6/6、2: 2/2、3: 24/24、4: 54/54、5: 25/25、6: 14/14、7: 7/7、8: 8/8、9: 1/1、
10: 1/1、11: 13/13。**全套核对跑了两遍**——§B.3 预检**之前**一遍、**之后**一遍，两遍均
**155/155**，即预检对现场零副作用（除预检自证的 `unchanged = true` 外另有实测）。

**归档 8 处 < 有效 run 9 次，差额恒为 B3**（两项永久覆盖）；§2.21 的**七处保全 hold
都不是归档**，不计入第 5 项的 8 处。**这不是缺项，未据此判不符**（§2.24 第 5/8 项明文）。

## B.2 九条只读 `--verify`：全部退出 0 且逐字复现

```text
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214, "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783243208518966, "run_id": "p1-m3-body-001-arm-a-trial-5", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-1", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
```

**本轮采集 `…-arm-b-trial-5` 尚不存在，第 4 项不对它跑 `--verify`**；它由第 10 项核对为
「run 目录不存在」。

## B.3 §3 步骤 0 环境预检：**退出码 0，`status = "PASS"`**

```bash
.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json
```

退出码 **0**；stdout 单个 JSON 对象，**5735 字节**。要点逐字：

- `status` = **`PASS`**；`side_effect_identity.unchanged` = **`true`**
- `interpreter.executable` = `~/TetheredDroneTracking/.venv-yoloe/bin/python`
- `packages` 四项 raw 与 pin **逐字相等**：`cv2` `5.0.0`（pin 源 nanotrack spec
  `opencv.tested_version`）、`torch` `2.13.0`、`torchvision` `0.28.0`、
  `ultralytics` `8.4.104`
- `constructors`：`YoloeProposer`、`DinoV2Embedder`、`NanoTrackV2Tracker` 三者**实际
  构造**成功
- `run_directories` 前后**逐项相等，共 36 个**（较 B4 轮多 B4 自身），其中**无**
  `p1-m3-body-001-arm-b-trial-5`；四个 guarded file 前后均 `present: false`

stderr 只有第三方库告警（OpenCV graph-engine target、`tifffile` 缺失、xFormers 不可用），
不影响退出码与 `status`，据实登记。

## B.4 §3 步骤 0′ 第 1 步：解释器逐字值落盘

按 §2.24 抬头具名的落盘地即本文件，从 §B.3 预检 stdout JSON 取 `interpreter.executable`
的**逐字值**记入：

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python
```

与 §1 冻结的唯一合法入口 `.venv-yoloe/bin/python -m controller.track_loop` 的解释器部分
一致。**尚未执行**：步骤 0′ 第 2 步（启动 tracker 时命令行首解释器路径与该值逐字相等，
命令行原文记入本文件）——本批不启动 tracker。

## B.5 §2.0 (b) 报告（本批次测量时点）

```text
$ git rev-parse HEAD
c1c53d3e36b74f5ac5dae806b7f4d0301a1863f4

$ git status --porcelain
（空输出）

$ grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md | tail -1
passed_candidate: 02c7c888b5c217127a61590524c09966ae0c26c3
```

`<BASE>` = **`02c7c88`**（**复核轮 16** 的通过候选，运行时现取、未手写；较上一轮的
`fcb22a7` 前移了两轮）。

```bash
$ git diff --name-only 02c7c88..HEAD
docs/current-status.md
docs/evidence/P1-M3-BODY-001-1c-preflight.md
docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md
docs/reviews/P1-M3-BODY-001.md
```

**四个路径，全部是文档**，由区间内 **2 条**提交产生（复核轮 16 `dce7970`、接受轮 73
`c1c53d3`）。**测量侧 diff 为空**——`controller/ Assets/ config/ ProjectSettings/
Packages/packages-lock.json tools/ tests/` 对 `02c7c88` 零改动，故九次已判定采集与即将
进行的 B5 跑在同一份已复核代码上。

**PLAY_GOVERNING 子集 = 恰 1 条**：操作单，现为 **revision 28**。
**§4 CLI 块差异本角色亲自复算**（不采信抬头自述）：

```text
base(02c7c88) 19 行  SHA-256 154b06a6353249d5a192b5b8464aaaa8a0002b51cd7a948c69b89f3abf9dee2f
HEAD          19 行  SHA-256 cfab349401447fd4f43039792b5c963d03e1fa2e514473369a7975dfa772d149
diff = 恰 1 行：  --run-id p1-m3-body-001-arm-b-trial-4  →  --run-id p1-m3-body-001-arm-b-trial-5
```

**与 revision 28「同臂轮换、§4 CLI 恰 1 行不同」相符**：`--body-policy threshold` **未动**
（同臂），其余 17 个参数逐字不变。**归因**：本修订是**同臂槽位轮换**——与 revision 19
的跨臂轮换不同，第二参数未变，无 planner 类切换，故不适用其
`ARM_ROTATION_A_TO_B_SEMANTIC_BY_DESIGN` 名目；轮换本身是本次授权的目的（批量 GO 逐
trial 枚举 B5），冻结值 token 零丢失、不放宽任何门、不新设任何数值门。
**最终归因归接受角色。**

> **本 (b) 报告绑定测量时点的 HEAD `c1c53d3`。** 本批次落盘并提交后 HEAD 会前移，
> 该报告即过期（先例：B3 §B → §C、B4 §B.5 → 接受角色复算）。**(c) 之前若 HEAD 再动，
> 须由本角色做发令时刻复查重取**；(d) 的「唯一未提交差异 = `docs/unity-test-log.md`」
> 不放宽。BC-BODY1-21 自 (c) 写入起冻结操作单。

## B.6 边界与未执行项（据实）

- **零 Play、零采集 ID 创建/消耗、零 `runtime/` 写入**：只做只读读取、九条 `--verify`
  （写盘前返回）与预检（自证 `unchanged = true`，另经 155/155 前后两遍实测佐证）；
  无 `mv`/`rm`/`mkdir`/重定向写入。
- **未执行**：§2.0 **(c)**（归接受角色，实现角色对 `docs/unity-test-log.md` 只读）、
  **(d)**、§3 步骤 0′ 第 2 步及其后所有步骤、门 1/2/3/4、tracker、`--finalize`、
  `--compare`、任何调参。
- **`--compare` 仍未授权**：本轮跑完即十次齐备，但 revision 28 C 条明写仍须**单独授权**。
- **本批未经独立复核。**

## B.7 复核范围（给复核角色）

- 本文件 §B 全文；对照 revision 28 §2.24 的十一项期望、§2.0 四步与 §3 步骤 0/0′。
- 实测复算建议：十一项的 155 条、并集等式 `274e9804…2d4c`、九条 `--verify`、预检
  退出码/`status`/`unchanged`/36 个 `run_directories` 无 B5、§4 CLI 块两侧 SHA 与
  **恰 1 行**差异（`--run-id`，`--body-policy` 未动）。

---

# C. B5 的 Play：四门 + tracker（**执行中**，2026-08-21，实现角色）

§2.0 四步全部成立：(a) 2026-08-14 批量 GO（复核前置已由轮 15 → 16 走完）、(b) 本文件
§B.5 于 `c1c53d3` 并由接受角色在 `993520a` 复算、(c) 接受角色写入
`docs/unity-test-log.md`（`PRE_PLAY_RELEASED`，**点名 HEAD `993520a` = 发令时刻 HEAD**，
留未提交）、**(d) 发令时刻实测** `git diff --name-only` **逐字只有**
`docs/unity-test-log.md` 且零未跟踪文件。**发令时刻另复查 §2.24 十一项，仍 155/155。**
用户随后进 Play **恰一次**并尽早暂停，报告「已暂停」。

**B5 是本批次最后一次采集**；臂 B 无替代 ID，**任何 void 终态立即中止 2026-08-14 的批量
授权**并回用户。

## C.1 门 1 —— 暂停窗口（**启动 tracker 之前落盘**，revision 12 记录型条款）

**导出命令原文**（在将驱动 tracker 的同一解释器下，只读；与 B4 §C.1 同一段代码）：

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

**保留帧编号范围**：`0 … 28`，共 **29** 份元数据（现场 59 项 = 29 帧 ×2 +
`latest.json`）；编号**连续无缺口**，每份的 `frame_id` 与文件名逐项一致，
`simulation_time_s` 随编号**单调不减**。

**导出的数值本身**：

```text
reported_sim_t = max(simulation_time_s) = 5.7835187911987305   （来自 frame 28）
```

判据 `2.000000 <= 5.7835187911987305 < 10.000000` **成立** → **门 1 PASS**。
两侧余量 `3.783519 s` / `4.216481 s`。**该值由保留帧机械导出，未取用户口报**
（冻结载体无计时 HUD，用户只报「已暂停」——接受轮 47 更正）。
**披露照旧**：该值是暂停真实时刻的**下界**（末帧写盘后、暂停生效前不足一帧不可见），
COORD-007 §4.1 的缺口未被本条款消除，本轮**不**因此调整阈值（BC-BODY1-15 (d)）。

> **不重复 B4 的 F14 错误**：本节**不**主张「某编号之后已无 `simulation_time_s`」。
> 保留帧集为 `0…28` 这一事实由门 2 的同一次导出承载；轮 72 已把「断言某字段不存在必须
> 按行枚举并显示分组依据」收窄为自律，本节据此不作该类旁证。

## C.2 门 2 —— 最低保留帧

最低保留帧编号恰为 **`0`**（与 §C.1 同一次导出的逐字输出）→ **门 2 PASS**。
`latest.json` 的 `frame_id` = `28`，与保留帧上界一致。

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
`df9a4aa0de7be545f97fc51169fef44cff00c3249cdc9915a0a8f7527b984608`）：

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
  --run-id p1-m3-body-001-arm-b-trial-5 \
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
`--run-id p1-m3-body-001-arm-b-trial-5` **True**。

**否定项（五条，revision 27 已收编进门 4，全须 False）**：`arm-a-` **False**、
前几轮 run-id（`arm-b-trial-1/2/3/4`）**False**、`-attempt-` **False**、
**hold（按 revision 27 的命名规约判：token 含 `-hold`，或以 `hold` 结尾且不等于
`threshold`）False**、`--compare` **False**。

> **登记**：命令行 42 个 token 中含 `hold` 子串者仍**只有 `threshold` 一个**——即 B4 轮
> 披露、revision 27 裁定并写死的那条规约在本轮按操作单原文直接适用，**不再临场推导**。

**§3 步骤 0′ 第 2 步**：命令行首解释器路径
`~/TetheredDroneTracking/.venv-yoloe/bin/python` 与步骤 0 预检 JSON 的
`interpreter.executable` **字符串逐字相等**（§B.4 已落盘该值）。

**门 4 PASS。** 四门全部落盘于本节，**均在启动 tracker 之前**。

## C.5 完成握手（§3 步骤 4，逐字执行）

**三项同时观察到**：

1. tracker 进程**自然退出码 `0`**（非信号终止、非人工终止）；
2. stdout final JSON 指向**同一采集 ID** 的 `summary.json`：
   `{"qualification_metrics_error": null, "records": 651, "run_id":
   "p1-m3-body-001-arm-b-trial-5", "state": "TRACKING", "summary":
   ".../runtime/runs/p1-m3-body-001-arm-b-trial-5/summary.json"}`；
3. run 目录内 `metrics.final.json` 与 `summary.json` **均已存在**（启动后 4 份）。

**确认词由只读命令机械产出，未人工复述**：`--validate-completion --runtime runtime
--run-id p1-m3-body-001-arm-b-trial-5 --tracker-exit-code 0 --tracker-final-json '<原文>'`
退出 **0**，输出逐字 **`TRACKER_AUTO_COMPLETE_CONFIRMED`**。

**BC-BODY1-29 遵守**：确认词产生后本角色的**下一个动作**就是请用户退出 Play——读 run
记录、跑绑定分析、写本节全部在用户退出**之后**。**用户报告（逐字）**：
「**已退出，没有报错**」→ Console 清洁（**待接受/辅助角色代录进
`docs/unity-test-log.md`**，本角色对该文件只读）。

## C.6 绑定分析：退出 0，臂身份三层核对通过

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-b-trial-5
```

退出 **0**；run 目录由 4 份增至 **11 份**（含 create-once 的 `m3_body_analysis.json`）。

**臂身份三层核对通过**：`receipt.body_policy` = **`threshold`**、
`receipt.body_planner_name` = **`threshold-corridor-v1`**，与冻结 ID 推导的期望臂逐项相等。
**无 predecessor / attempt 键**——B5 的 ID 从未被消耗，两个前驱门都不触发。
`frame_record_count` **651**、`truth_record_count` **742**、首末帧 `0` / `741`。

**准入与两条域完整性门**：三条判据在主路径上都是无条件 `raise`，**退出 0 即三条全过**。
下界实测 `final_unwrapped = 298.19364929741283 m >= P = 212.97056274847716 m` ✓。

**十条 `--verify` 全部退出 0 且逐字复现**（A1…A5 + B1…B5）：臂 A 五个 `WITHIN_RANGE`，
**B1/B2/B3/B4/B5 均 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`**。**前九个 run 一字节未动。**

## C.7 主结果与机体运动（**归因归接受角色，本节只报事实**）

| 项 | B1 | B2 | B3 | B4 | **B5** |
|---|---|---|---|---|---|
| `full_loop_c_geom` | `1.0` | `1.0` | `1.0` | `1.0` | **`1.0`** |
| `h1.disposition` | `SCENE_DEGENERATE` | 同 | 同 | 同 | **同（天花板 `0.95`，第五次）** |
| 窗口 `C_track|geom` | `1.0` | `1.0` | `1.0` | `1.0` | **`1.0`** |
| `body_motion_effort_m` | `88.64522663177961` | `75.26945194958653` | `91.174630127364` | `88.72384065309268` | **`90.18617697302953`** |
| `body_path_length_m` | `61.42306359956821` | `49.16248028068326` | `64.4545385428812` | `61.40687110469029` | **`62.887483690312656`** |
| `planner_switch_count` | `11` | `11` | `11` | `11` | **`11`** |
| `nees_median` | `5.067625439804517` | `5.2993597343857255` | `5.196313303659595` | `5.244988577303893` | **`4.762136507763351`** |
| `min_side_ge20_share` | `1.0` | `1.0` | `1.0` | `1.0` | **`1.0`** |
| 停留 / 圈数 | `41.390 s` / `1.618675` | `29.602 s` / `1.509862` | `76.804 s` / `1.952997` | `40.198 s` / `1.607742` | **`18.201736 s` / `1.400164`** |

**(iv) reason 直方图（623 decision 帧）**：`margin_below_trigger+corridor_blocked`
**322**、`within_hysteresis_band` **121**、`margin_below_trigger` **95**、
`margin_above_release` **79**、`margin_below_trigger+corridor_shortened` **6**。
**`no_observation` / `no_platform_state` / `no_estimate` / `planner_exception` 与
`publish_failure_fallback` 全 0 帧。** 不带 planner 的行 159（追平期 catch-up，合法）。
`frames.jsonl` 共 **782** 行。

> **派生口径本轮先校准再用**：同一段代码对 **B1/B2/B3/B4** 复出 623 = 324/116/95/82/6、
> 622 = 339/109/93/75/6、626 = 319/121/95/85/6、621 = 324/118/95/78/6，圈数复出
> `1.618675` / `1.509862` / `1.952997` / `1.607742`——与四轮已发布数字**逐项相等**。
> 故 B5 的三个数与前四轮同底。

**(iii) `body_motion_effort_m > 0`**，**不触发**「整圈定义域内零位移即停」分支。
**(i) post-tracker 停留**：tracker 末帧 `130.18399047851562 s`、Play 末条 truth
`148.38572692871094 s`，差 **`18.201736450195312 s`**——**五轮最短**（前四轮 `41.390` /
`29.602` / `76.804` / `40.198`），BC-BODY1-29 的「确认词后即请退出」执行到位。
**(ii) 圈数** `298.19364929741283 / 212.97056274847716` = **`1.4001636913998579`**。
**(i)(ii) 均不构成任何门**（BC-BODY1-30）。

其余披露：`loop_gimbal_saturated_share = 0.5040472725879599`、
`loop_tether_saturated_share = 0.3239487920812843`、窗口内云台饱和 **`0.0`**、
窗口内系绳饱和 `0.22300390625`；`loop_frame_count` 530 / `window_frame_count` 155。

**只登记、不调参（BC-BODY1-15 (d)）**：两条预登记限制各得**第五次**确认
（`C_geom` 五次 `1.0`；`min_side_ge20_share` 五次 `1.0`）。`planner_switch_count`
连续**五次**恰 `11`。n=3 撤下的方向性读法**仍不重提**：五点中 B5 阻塞 322（居中）
配位移 `90.186`（次高），单调读法在 n=5 上同样不成立。`nees_median` 首次跌破 5
（`4.762`），仍在臂 B 的 `4.7–5.3` 带内、与臂 A 的 `832–1017` 差两个数量级——
**只登记，属既有注册发现 (a) 的第五个数据点，不新增主张**。

## C.8 边界与未执行项（据实）

- **恰一次 Play**，采集 ID `p1-m3-body-001-arm-b-trial-5` **已消耗**；**零 void 终态**
  （终态对照由接受角色认定）。**臂 B 至此 5/5，本批次十次采集全部执行完毕。**
- 零代码/测试/config/scenario/model/阈值/CLI 改动；**零操作单改动**（BC-BODY1-21 全程
  遵守——(c) 写入后本文件一字未动）。
- **§2.21 的七处保全 hold 与八处 post-run 归档未被本次 Play 触及**。
- **未执行**：`--finalize`、**`--compare`**、任何调参。**`--compare` 现已十次齐备，但
  revision 28 C 条明写仍须单独授权，不在批量 GO 内——本角色不得以「十次已齐」自行
  启动**，等用户授权与接受角色的合同。B5 的 post-run 归档合同亦尚未起草。
- **`docs/unity-test-log.md` 的 (c) 条目保持未提交**，随接受角色的归因批次入库
  （先例 B1–B4）——实现角色对该文件只读，从不提交。
- **本批未经独立复核**；主结果的归因（`B5_VALID_TRIAL` 与否）归接受角色。

## C.9 复核范围（给复核角色）

- 本文件 §C 全文；对照 revision 28 §3 步骤 0′/1–6、四门判据与 §5 四种 void 终态。
- 实测复算建议：门 1 的保留帧导出（0–28，`5.7835187911987305`）、门 4 命令行 SHA
  `df9a4aa0…4608` 与 §4 块的 18 行相等及五条否定项（`hold` 按 revision 27 规约）、
  握手三项与确认词、**十条 `--verify`**、直方图/停留/圈数的派生口径校准（对 B1–B4
  复出已发布值）、`body_motion_effort_m > 0`、下界 `298.194 >= 212.971`。

---

# D. §2.25 B5（有效 trial）的 post-run 归档（**已执行**，2026-08-21，实现角色）

交接来源：接受轮 74（B5 判为 `B5_VALID_TRIAL`，**臂 B 收于 5/5，十次采集全部完成**；发
revision 29）。**零 Play、零采集 ID、零分析、零 `--finalize`、零 `--compare`、零调参、
零代码/测试/config/scenario/model 改动、零操作单改动。** `runtime/` 在 `.gitignore` 内，
六次移动仓库侧零 diff；批次前后 `git status --porcelain` 均为空。

> **落盘地在本轮改变（revision 29 B 条，逐字执行）**：前几轮的归档都落在「下一 trial 的
> 证据文件」（§2.19 先例），但**本轮没有下一 trial**，故 §2.25 落盘于 B5 自己的证据文件
> §D。**该先例在此自然终止**，此注写明以免下一个接手的角色照抄。

**为什么仍要先做**：shared 槽位此前装着 B5 的产物。**「这是最后一次采集」不使 B3 的教训
失效**——一次误入的 Play 会当场覆盖 truth 与 metrics 且不可恢复。

## D.1 移动前只读核对：**24 条机械核对，24 PASS / 0 FAIL**

六项钉住值（接受轮 74 移动前实测）逐项相等，全 64 位：

| 项 | 实测计数/行数 | 实测字节 | 实测 SHA-256 | 与钉住值 |
|---|---|---|---|---|
| `frames/` | **257** 项，id 段 `[614, 741]` 全 128 个 ×2 + `latest.json` | — | 聚合 `dcabe43b43b2366d898be70c94a64eef01788c55a73fc9e4b4b6e1c7d680b814` | 相等 |
| `m3_body_truth.jsonl` | **742** 行 | **806547** | `6ea05d88c83cfaac13fe9af7b92a0fb5eb5c868a592104057c8151f037da11bd` | 相等 |
| `metrics.json` | **61** 行 | **2057** | `024acc1349245a2ad0e32653401123197ba140702206f3852fb117b1a622b3ec` | 相等 |
| `body_command.json` | **15** 行 | **329** | `8d95690b572895a49460ed9527992dbbacb192895b12181b04d8eace7fd87006` | 相等 |
| `gimbal_command.json` | **15** 行 | **342** | `b19644e915e8b8f842aa0097d4bab0689ed63c0f45fbae4d3520d848bd440637` | 相等 |
| `tracking_observation.json` | **18** 行 | **458** | `70f7c699e9e9f100b3263fc078253dd41418bc8b8fac1651703041de579933f2` | 相等 |

另核对：**destination 移动前不存在** ✓、B5 run 目录 **11 份**（绝对不动）✓、
§2.21 两处保全 hold **256 / 59** 项 ✓、既有 post-run 归档 **8** 处 ✓。
聚合口径见 `…-arm-a-trial-2.md` §B.3；行数一律 `wc -l`。

## D.2 移动执行

六项 shared 侧工件移入
`runtime/test-results/p1-m3-body-001-arm-b-trial-5-post-run/`（`mv`，零删除、零覆盖、
零分析）；移动后**只新建空 `runtime/frames/`**，**未预建任何 run 目录**。
**B5 的 run 目录一字节未动。**

## D.3 移动后核对：**36 条机械核对，36 PASS / 0 FAIL**

- 归档目录**恰 6 项**，文件名集合等于六项；`frames/` **257** 项、id 段 `[614, 741]` 含
  `latest.json`、聚合等于钉住值；五个单文件的行数/字节/SHA-256 **逐项等于移动前**。
- `runtime/frames/` **存在且恰 0 项**（新建空目录）；五个 shared 槽位已腾空；
  `runtime/scenario_config.json` **仍不存在**。
- **B5 run 目录仍 11 份**；**§2.21 两处保全 hold 未被触碰**——B hold 仍 **256** 项且聚合仍
  `568b6b98…a815`，A hold 仍 **59** 项且聚合仍 `39698be4…9a7f`。
- post-run 归档处数由 8 增至 **9**；未预建任何新 run 目录（无 `…-trial-6`）。

## D.4 承重核对：**十个 `--verify` 全部退出 0 且逐字复现**

A1…A5 五个 `WITHIN_RANGE`（`0.5784550773737355` / `0.5783188398250908` /
`0.597146417669116` / `0.5783206310103214` / `0.5783243208518966`），
**B1…B5 五个 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`**。
**B5 的 `--verify` 在其 shared 侧被归档之后仍逐字复现**——run 目录自包含，正是 create-once
存档的设计意图。**§D.3 的 36 条在十个 `--verify` 之后又跑一遍，仍 36/36**（零副作用实测）。

## D.5 归档处数与差额（§2.25 明文，防误判）

归档 **9** 处 < 有效 run **10** 次，**差额恒为 B3**：其 `m3_body_truth.jsonl` 与
`metrics.json` 被 2026-08-20 那次未放行 Play 永久覆盖，完整六项归档永久不可能。
§2.21 的七处保全 hold **不是** post-run 归档、**不计入这 9 处**。
**这不是缺项，不得据此判不符。**

## D.6 边界与未执行项（据实）

- **零 Play、零采集 ID、零分析、零 `--finalize`、零调参。**
- **`--compare` 未执行、且本角色不得启动**：revision 29 C 条与接受轮 75 入账的用户裁定
  （逐字「归档 + 复核后再授权（推荐）」）都写明——**十次齐备只是必要条件之一，不是
  授权**。放行次序为 **§2.25 归档 → 独立复核 → 用户另行逐字授权 → 接受角色落账并起草
  比较合同 → 才谈执行**。**本节是该次序的第一步，执行完即停。**
- §3 的采集步骤自 revision 29 起**不再有下一次执行对象**（十次已满）。
- **M3′ batch 1 的关闭未被主张**，需接受角色的判断加用户授权。
- **本批未经独立复核。**

## D.7 复核范围（给复核角色）

- 本文件 §D 全文；对照 revision 29 §2.25 的六项钉住表。
- 实测复算建议：归档目录 6 项 / `frames/` 257 项 id `[614,741]` / 聚合 `dcabe43b…b814`；
  五个单文件行数/字节/SHA；`runtime/frames/` 存在且 0 项；§2.21 两处 hold 的项数与聚合
  未变；B5 run 目录 11 份；**十个 `--verify` 逐字复现**；归档 9 < 有效 run 10。
- 本轮复核范围另含 **B5 的执行批次（§C）、接受轮 74 与 revision 29**——按用户 2026-08-21
  的放行次序，这一轮复核是 `--compare` 授权的前置。
