# P1-M3-BODY-001 arm B trial 3 证据（操作单 revision 22）

**范围**：用户 2026-08-14 批量授权 B2–B5 中的**第二次**（B3）。执行合同 =
`docs/evidence/P1-M3-BODY-001-1c-preflight.md` **revision 22**。采集 ID
`p1-m3-body-001-arm-b-trial-3`（canonical slot 即其自身，从未消耗，**无替代 ID、无
predecessor 门**），配对搭档 A3（`p1-m3-body-001-arm-a-trial-3`）。**批量授权不改变
逐次纪律**：每次仍走完整 §2.0 (a)–(d)，**任何 void 终态立即中止该授权并回用户**。

**状态**：§A 已完成（2026-08-14：§2.20 九项 + §2.0 (b) + §3 步骤 0/0′ 第 1 步，**零 Play、
零采集 ID、零代码**）；§B 已完成（2026-08-16，在 `d278ef2`）；**§C 已完成**（2026-08-16，
在 `67b2ac7`——接受轮 66 自述为 (c) 之前的最后一个接受批次）。三节均零 Play、零采集 ID、
零 `runtime/` 写入、零代码。**现行 (b) 报告是 §C**，§B 的 (b) 已随 HEAD 前移过期（时间
边界见 §B 抬头）。§A.6 第 1 条（F7）由接受轮 64 修复、复核轮 11 闭合；**§B.6 第 1 条
登记的归因指令缺陷由接受轮 66 修复**（五处，多于本角色枚举的三处，自查更正见 §C.4）。
§2.0 (c) 记录归接受角色，(d) 与 §3 步骤 1 之后各节待 Play 时/后填写。

---

# A. B3 的 Play 前置（§2.20 核对 + §2.0 (b) + §3 步骤 0/0′ 第 1 步）

日期 2026-08-14，实现角色。交接来源：接受轮 63（B2 判有效、发 revision 22）。
**本轮无归档待办**——§2.19 已于同日执行完毕（证据 `…-arm-b-trial-2.md` §D）。
**零 Play、零采集 ID 创建/消耗、零代码/测试/config/scenario/model 改动、零操作单
改动（BC-BODY1-21/-22）。** 批次开始与结束时 `git status --porcelain` 均为空。

## A.1 §2.20 九项 Play 前只读核对：**136 条机械核对，136 PASS / 0 FAIL**

| §2.20 项 | 核对内容 | 结果 |
|---|---|---|
| 1 | 六个 shared 文件 | 均**不存在** ✓（6/6） |
| 2 | `runtime/frames/` 存在且为空 | 存在、**0 项** ✓（2/2，由 §2.19 重建） |
| 3 | 四处旧 hold | **257 / 93 / 109 / 257** + 全部 SHA；attempt-3 run hold 恰两文件 ✓（26/26） |
| 4 | **七个正式 run 目录** | A1…A5 + B1 + B2 各**恰 11 份**且各含 `m3_body_analysis.json` ✓（14/14）；七条 `--verify` 见 §A.2 |
| 5 | **七处 post-run 归档** | 各**恰 6 项**、`frames/` 各 **257** 项、七个聚合 SHA 与各自钉住表相等 ✓；七组各五个单文件的行数/字节/SHA 逐项相等 ✓（56/56） |
| 6 | 活动标记 + attempt-1 void hold | 八个标记均不存在；void hold 仍**恰 10 份**、文件名集合等于冻结十项、**零隐藏项**、三钉住 SHA 相等 ✓（14/14） |
| 7 | **B3 create-once 前置** | `runtime/runs/p1-m3-body-001-arm-b-trial-3/` **不存在** ✓（1/1） |
| 8 | **臂 B 专属：corridor 工件** | 实测 SHA = config pin = `9e2956ad…c800` ✓、`instance_count` **779** 且工件实际条目 **779** ✓、`policy.tether_corridor_check` = `true` ✓（6/6） |
| 9 | **臂 B 专属：臂位机械复核** | `_expected_policy('…-arm-b-trial-3')` = `threshold` ✓；planner = `threshold-corridor-v1` ✓；**`expected_acquisition_ids('b')[2]`** 逐字相等 ✓；`canonical_trial_id()` 返回同名 ✓；`…-attempt-1`/`…-attempt-2`/`…-trial-6` 在**两个**函数上均抛 `run_id_not_frozen_trial` ✓（11/11） |

分项计数：1: 6/6、2: 2/2、3: 26/26、4: 14/14、5: 56/56、6: 14/14、7: 1/1、8: 6/6、
9: 11/11。第 5 项的 B2 一组按 **§2.19 的 64 位全值**核对（见 §A.6 第 1 条的缺陷登记）。

## A.2 七条只读 `--verify`（§2.20 第 4 项）

全部退出 **0** 且逐字复现：五个臂 A `WITHIN_RANGE`
（`0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` /
`0.5783206310103214` / `0.5783243208518966`）、**B1 与 B2 均
`SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`**。七份证据全部可复算，一个字节未动。

## A.3 §2.0 (b) 报告（测量时点）

```text
$ git rev-parse HEAD
29e903a4176bd6679ac60336cdfef65867ac0460

$ git status --porcelain
（空输出）

$ grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md | tail -1
passed_candidate: 408acd7b39054e0a92eb3f0f9df5d4713b16f34a
```

`<BASE>` = **`408acd7`**（复核轮 9 的通过候选，运行时现取）。
`git diff --name-only 408acd7..HEAD` = **10 个路径，全部是文档**（比 B2 轮多 B2 的证据
文件），由区间内 **18 条**提交产生。**测量侧 diff 为空**（`controller/ Assets/ config/
ProjectSettings/ Packages/packages-lock.json tools/ tests/`）——A1…A5、B1、B2 与即将
进行的 B3 全部跑在同一份已复核代码上。

**PLAY_GOVERNING 子集 = 恰 1 条**：操作单，现为 **revision 22**。**CLI 块差异本角色
亲自复算**：

| 比较对象 | 块行数 | 差异 |
|---|---|---|
| 已复核候选 `408acd7` | 19 / 19 | **恰 2 行**（`--run-id …-arm-a-trial-5` → `…-arm-b-trial-3`；`--body-policy hold` → `threshold`） |
| B2 轮（revision 21） | 19 / 19 | **恰 1 行**（`--run-id`） |

**(b) 的归因按对已复核候选的 2 行写**（同 B2 轮，revision 21/22 抬头均已警告不得填
「1 行」）。具名 disposition 由接受角色给出。

## A.4 §3 步骤 0 环境预检

退出码 **0**，`status = "PASS"`，`side_effect_identity.unchanged = true`，`before` 与
`after` 完全相等。**与 B2 轮记录的预检 JSON 逐字段比对**：**唯一差异**是
`run_directories` 各新增 `p1-m3-body-001-arm-b-trial-2`（**33 → 34**），
**`p1-m3-body-001-arm-b-trial-3` 不在其中**，与 §2.20 第 7 项一致。

## A.5 §3 步骤 0′ 第 1 步

`interpreter.executable` 逐字值：

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python
```

**步骤 0′ 第 2 步与门 4 尚未执行**（本批不启动 tracker）：启动时命令行首必须与上值
逐字相等，回车前须把实际命令行原文落盘并核对含 `--body-policy threshold` 与
`--run-id p1-m3-body-001-arm-b-trial-3`（并同 B2 轮加查否定项：不得含前几轮的 run-id、
不得含 `arm-a-` 串）。

## A.6 交回接受角色 / 未验证项

1. **操作单文字缺陷（发令前须由接受角色处置，本角色不自行修正）**：§2.20 第 5 项把
   B2 归档的 `frames/` 聚合缩写成 **`71f65dca…3a85`**，而 §2.19 的 64 位钉住值是
   `71f65dca666cc37d91569a9b2b3893c0721e436a1b09756f5e644c0052a20f85`，**磁盘实测亦
   等于该全值**，正确缩写应为 **`71f65dca…0f85`**。两处对同一工件给出**互相矛盾**的
   末四位：照 §2.20 字面核对会在一个**真实且完好**的工件上判出不符，进而触发「停止
   并回 Acceptance」。本角色按 §2.19 全值完成核对并通过，**但不修改操作单**
   （BC-BODY1-21/-22 + 越权）；建议接受角色在 (c) 之前更正该缩写。
2. **§2.0 (c) 是接受角色的动作**；**测量时点 HEAD ≠ 发令时点 HEAD**，(c) 须在写入时点
   自取 HEAD/status，**§2.20 需在发令时刻复查**。
3. **PLAY_GOVERNING 恰 1 条 = revision 22**；**revisions 19/20/21/22 与接受轮 58 的
   20 处自查修复仍未被任何复核轮覆盖**（`passed_candidate` 仍是 `408acd7`）。
4. **B3 无前驱门**；ID 从未创建或消耗，receipt 不会有 predecessor/attempt 字段。
5. **批量授权边界**：B3–B5 仍各走完整 §2.0 (a)–(d)，**任何 void 终态立即中止授权**；
   `--compare` 需十次齐备并单独授权。两条预登记限制（H2-CEILING、处理臂饱和）继续
   生效，BC-BODY1-15 (d) 禁止据任何已见数值调参。
6. **本批不产生 Unity 用例**，不申领 `UNITY_NA`。

## A.7 §A 批次边界声明

- **零 Play、零采集 ID 创建/消耗**；`runs/…-arm-b-trial-3/` 未预建（预检 34 项
  `run_directories` 中亦无该名）。
- **零 `runtime/` 写入**：只做只读读取、七条 `--verify`（写盘前返回）与预检
  （自证 `unchanged = true`）；无 `mv`/`rm`/`mkdir`。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单、提案、
  正式设计、`docs/reviews/`；对 `docs/unity-test-log.md` 与 `docs/authorizations.md` 只读。
- 本批写入仅两个仓库路径：本证据文件与 `docs/current-status.md`。
- 复核范围：§A.1 的 136 条核对、§A.2 的七条逐字输出、§A.3 的基线派生与 CLI 复算、
  §A.4 的预检比对、§A.6 第 1 条的缺陷登记（可由 §2.19/§2.20 两处文字直接复看）。

---

# B. 第一次发令时刻复查（§2.20 九项 + §2.0 (b) 在 `d278ef2`）

> **时间边界（§C 加注）**：本节起草时 `d278ef2` 是最终 HEAD，抬头原写「在最终
> HEAD」。此后 `1b3cbd1`（本节自身）、`6269b2c`、`67b2ac7` 三条提交落地，**本节的
> (b) 报告随之过期**，现行 (b) 以 **§C** 为准；§B.1/§B.2 的核对结论仍成立（§C 逐项
> 复现）。这正是 §B.6 第 3 条预写的分支实际触发。

日期 2026-08-16，实现角色。交接来源：状态板 Active handoffs 行 1 —— 接受轮 65 落地
复核轮 12 的 F11 返工后，把 §2.20 与 §2.0 (b) 的**最终 HEAD 复查**交回本角色。
**零 Play、零采集 ID 创建/消耗、零代码/测试/config/scenario/model 改动、零操作单
改动（BC-BODY1-21/-22）。** 批次开始与结束时 `git status --porcelain` 均为空。

**为什么必须复查**：§A 的测量时点 HEAD 是 `29e903a`（记录批次 `9cadebd`）。此后
**六条提交**落地（`f2ac95a` 复核轮 10、`6e81bc2` 接受轮 64 主批、`1528288` 复核轮 11、
`a5fc735` 接受轮 64 续批、`8caa44d` 复核轮 12、`d278ef2` 接受轮 65），其中复核轮 11
`PASS_WITH_NOTES` 使 `passed_candidate` 前移 —— 而 `<BASE>`/「已复核候选」按 §2.0 (b)
是**运行时现取**的量，§A 的 (b) 归因随之全部失效，必须重报。（状态板行 1 原写「四条
接受提交」，实测是六条提交、其中接受批次三条；本轮同批就地更正。）

## B.1 §2.20 九项复查：**136 条机械核对，136 PASS / 0 FAIL**（与 §A 同一分项结构）

核对脚本只做 `open(..., 'rb')`/`stat`/`iterdir`/`rglob`，落在会话 scratchpad，不入库。
期望值出处与 §A 相同：§1 corridor 钉住行、§2.5 第 4–7 项原表、§2.8 十文件 hold 与三钉住
SHA、`…-arm-a-trial-1.md` §B/§F.1/§H.1/§I.1，以及**七处归档的钉住表**——A1 在
`…-arm-a-trial-1.md` **§N.1**，其余六处在 §2.9/§2.11/§2.13/§2.15/§2.17/§2.19。
第 5 项的 B2 一组按 §2.19 的 **64 位全值**核对。

| §2.20 项 | 核对内容 | 结果 |
|---|---|---|
| 1 | 六个 shared 文件 | 均**不存在** ✓（6/6） |
| 2 | `runtime/frames/` 存在且为空 | 存在、**0 项** ✓（2/2） |
| 3 | 四处旧 hold | **257 / 93 / 109 / 257** + 全部 SHA；attempt-3 run hold 恰两文件 ✓（26/26） |
| 4 | **七个正式 run 目录** | A1…A5 + B1 + B2 各**恰 11 份**且各含 `m3_body_analysis.json` ✓（14/14）；七条 `--verify` 见 §B.2 |
| 5 | **七处 post-run 归档** | 各**恰 6 项**、`frames/` 各 **257** 项、七个聚合 SHA（§B.3 口径亲自重算）与各自钉住表相等 ✓；七组各五个单文件的行数/字节/SHA 逐项相等 ✓（56/56） |
| 6 | 活动标记 + attempt-1 void hold | 八个标记均不存在；void hold 仍**恰 10 份**、文件名集合等于冻结十项、**零隐藏项**、三钉住 SHA 相等 ✓（14/14） |
| 7 | **B3 create-once 前置** | `runtime/runs/p1-m3-body-001-arm-b-trial-3/` **不存在** ✓（1/1） |
| 8 | **臂 B 专属：corridor 工件** | 实测 SHA = config pin = §1 钉住值 `9e2956ad…c800` ✓、`instance_count` **779** 且工件实际条目 **779** ✓、`policy.tether_corridor_check` = `true` ✓（6/6） |
| 9 | **臂 B 专属：臂位机械复核** | `_expected_policy('…-arm-b-trial-3')` = `threshold` ✓；planner = `threshold-corridor-v1` ✓；`expected_acquisition_ids('b')` 长度 5、**`[2]`** 逐字相等 ✓；`canonical_trial_id()` 返回同名 ✓；`…-attempt-1`/`…-attempt-2`/`…-trial-6` 在**两个**函数上均抛 `run_id_not_frozen_trial` ✓（11/11） |

分项计数：1: 6/6、2: 2/2、3: 26/26、4: 14/14、5: 56/56、6: 14/14、7: 1/1、8: 6/6、
9: 11/11 —— **与 §A 的分项计数逐项相同**。

> **§C 自查更正（不静默改，原句留档）**：本句原写「磁盘状态自 §A 起**一字节未变**」，
> 属过强。§2.20 覆盖面内确实逐项相等，但**覆盖面本身不是全字节**：七个 run 目录只核
> 「恰 11 份 + 含 `m3_body_analysis.json`」，不逐文件取哈希。其中 10 份由 `--verify`
> 反向绑住——它按 run 目录字节重算整份分析并要求与在盘 `m3_body_analysis.json`
> **逐字节相同**（否则 `verify_rerun_not_byte_identical`），`input_sha256` 覆盖
> `manifest.json`/`frames.jsonl`/`m3_body_truth.jsonl`/`metrics.final.json` 与四份
> config——**唯独 `summary.json` 既不在 `input_sha256` 内、也不被重算**，故每个 run
> 目录有 1 份、七个共 **7 份**文件本轮只受计数约束。四处旧 hold、十文件 void hold、
> 七处归档与 corridor 工件则全部是哈希绑定。准确表述见 §C.1。
**全套核对跑了两遍**：七条 `--verify` **之前**一遍、**之后**一遍，两遍均 136/136，
即 `--verify` 对现场零副作用（该性质此前只由工具自述承担，本轮改为实测）。

## B.2 七条只读 `--verify`（§2.20 第 4 项，本轮实跑）

全部退出 **0** 且逐字复现，与 §A.2、与各自冻结值相同：

```text
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214, "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783243208518966, "run_id": "p1-m3-body-001-arm-a-trial-5", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-1", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-2", "verified": true, "window_c_track_given_geom": 1.0}
```

七份证据仍全部可复算，一个字节未动。

## B.3 §2.0 (b) 复报（本轮测量时点）

```text
$ git rev-parse HEAD
d278ef2c581ac27211b755c2d3f41e895fa59e27

$ git status --porcelain
（空输出）

$ grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md | tail -1
passed_candidate: 6e81bc23fab417813e2761755b3b122b4d01c970
```

`<BASE>` = **`6e81bc2`**（**复核轮 11** 的通过候选，运行时现取、未手写；§A 那次取到的
`408acd7` 是复核轮 9 的，已被前移取代）。

```bash
$ git diff --name-only 6e81bc2..HEAD
docs/current-status.md
docs/evidence/P1-M3-BODY-001-1c-preflight.md
docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md
docs/reviews/P1-M3-BODY-001.md
```

**四个路径，全部是文档**（区间内 **4 条**提交：`1528288` 复核轮 11、`a5fc735` 接受轮 64
续批、`8caa44d` 复核轮 12、`d278ef2` 接受轮 65）。比 §A 的十个路径少，纯粹是基线前移
所致，**不是有东西被撤掉**。

**测量侧逐字节相同**：

```bash
$ git diff --name-only 6e81bc2..HEAD -- controller/ Assets/ config/ \
    ProjectSettings/ Packages/packages-lock.json tools/ tests/
（空输出）
```

**A1…A5、B1、B2 七次采集与即将进行的 B3 全部跑在同一份已复核代码上**——配对成立的
前提继续成立。

**PLAY_GOVERNING 子集 = 恰 1 条**：操作单（仍是 revision 22，抬头未再轮换）。其自
`6e81bc2` 起的改动**全部是文字**，共三处：§3 步骤 0′ 第 1 步 / 门 1 的落盘地指针改为
「当轮 §2.x 核对节节首具名者」（撤回对臂 A 为假的去前缀导出规则）、§5 现行执行前提的
排除项**来源拆分**（复核轮 12 F11 的返工）、§6 抬头写入 N36。**未新增/放宽任何门，未
改任何冻结值。**

**CLI 块差异本角色亲自复算**（整块 19 行，从 §4 抬头之后的第一个 bash 代码围栏取出块体，
逐行比对并对整块另取一次 SHA-256）：

| 比较对象 | 块行数 | 差异 |
|---|---|---|
| **已复核候选 `6e81bc2`**（本轮 `<BASE>`） | 19 / 19 | **0 行**——整块 SHA-256 `fd832df1…55dd`，**逐字节相同** |
| `a5fc735`（接受轮 64 续批） | 19 / 19 | **0 行**（同一 SHA） |
| `9cadebd`（§A 的记录批次） | 19 / 19 | **0 行**（同一 SHA） |
| （历史）旧候选 `408acd7` | 19 / 19 | 恰 2 行：`--run-id …-arm-a-trial-5` → `…-arm-b-trial-3`；`--body-policy hold` → `threshold` |

**归因**：本轮 (b) 的 CLI 块对已复核候选是 **0 行不同**。操作单三处仍写着「按对已复核
候选的 **2 行**写」并把已复核候选写死成 `408acd7`——该指令在本轮 HEAD 上已不成立，
**本角色不照抄、不自行改单**，按事实报 0 行并登记（§B.6 第 1 条）。具名 disposition
仍由接受角色给出。

## B.4 §3 步骤 0 环境预检（本轮实跑）

```bash
.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json
```

**退出码 `0`**，`status = "PASS"`，`side_effect_identity.unchanged = true`，`before` 与
`after` 两块实测完全相等；四个 guarded 文件（`body_command` / `gimbal_command` /
`tracking_observation` / `metrics`）前后均 `present = false`。`reanchor_config.sha256`
= `593734d6…06d2`，`nanotrack` 两个模型 SHA、四个包 pin（cv2 5.0.0 / torch 2.13.0 /
torchvision 0.28.0 / ultralytics 8.4.104）与既往记录一致。stderr 仅既有依赖噪声
（OpenCV `setPreferableTarget` WARN ×2、`tifffile` 提示、DINOv2 三条 xFormers
`UserWarning`），不影响退出码与 JSON。完整 JSON 落在会话 scratchpad，可由上面这条
命令原样复现。

**与 §A.4 记录逐字段比对：零差异**——`run_directories` 仍是**同样 34 项**，
**`p1-m3-body-001-arm-b-trial-3` 不在其中**，与 §2.20 第 7 项一致。

## B.5 §3 步骤 0′ 第 1 步（复取）

`interpreter.executable` 逐字值，与 §A.5 相同：

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python
```

**步骤 0′ 第 2 步与门 4 仍未执行**（本批不启动 tracker）。落盘地按操作单现行条文
= 当轮 §2.x 核对节节首具名者 = §2.20 具名的**本文件**，与本节所在位置一致。

## B.6 交回接受角色 / 未验证项

1. **新登记的操作单文字缺陷（本角色不自行修正）**：操作单**至少三处**（**本条枚举不
   完整——见 §C.4 第 2 条的自查更正：实为五处**）把「已复核候选」写死为
   `408acd7` 并据此规定 (b) 的归因数字——
   - revision 22 抬头 A 点：「**对已复核候选 `408acd7` 仍是 2 行不同**……**(b) 归因按
     对已复核候选的 2 行写**」；
   - §4 抬头段：「**对已复核候选 `408acd7` 换掉 2 个**，故对该基准未变**参数** 16 个、
     未变**行** 17 行……**§2.0 (b) 归因按对已复核候选的 2 行写**」；
   - §4 末段：「其余 17 行与已复核候选 `408acd7` 逐字节相同」。

   复核轮 11 把 `passed_candidate` 前移到 `6e81bc2`，而该候选**已经包含 revision 22 的
   CLI 块**，故本轮实测**对已复核候选 0 行不同、整块同 SHA**（§B.3）。照字面执行会把
   **2 行**填进一份实际为 **0 行**的归因；改按字面取 `408acd7` 又违反 §2.0 (b) 自己
   「`<BASE>` 运行时现取、禁手写」的规定与 COORD-007 R7。两条路都不自洽，**故本轮
   fail-closed 上报**：与 F7/F8/F9/F10 同族（写死可派生标识，一次轮换/一次通过之后
   失效），但这次失效的触发源不是轮换而是**复核通过本身**。**处置属接受角色**；本
   角色对操作单零改动（BC-BODY1-21/-22 + 越权）。
2. **§A.6 第 1 条已闭合**：§2.20 第 5 项的 B2 聚合已改为 64 位全值
   `71f65dca…0f85`（接受轮 64 落地、复核轮 11 闭合），本轮按全值核对通过，全仓
   `3a85` 错值零残留于任何现行断言。
3. **§2.0 (c) 仍是接受角色的动作**；**本轮测量时点 HEAD ≠ 发令时点 HEAD**，(c) 须在
   写入时点自取 HEAD/status。若 (c) 之前又有提交落地，**§2.20 与 (b) 需再复查一次**。
4. **B3 无前驱门**；ID 从未创建或消耗，receipt 不会有 predecessor/attempt 字段。
5. **批量授权边界不变**：B3–B5 仍各走完整 §2.0 (a)–(d)，**任何 void 终态立即中止
   授权**；`--compare` 需十次齐备并单独授权。两条预登记限制（H2-CEILING、处理臂
   饱和）继续生效，BC-BODY1-15 (d) 禁止据任何已见数值调参。
6. **本批不产生 Unity 用例**，不申领 `UNITY_NA`。**本轮未跑自动测试套件**：测量侧对
   已复核候选逐字节为空（§B.3），无回归面。

## B.7 §B 批次边界声明

- **零 Play、零采集 ID 创建/消耗**；`runs/…-arm-b-trial-3/` 未预建（预检 34 项
  `run_directories` 中亦无该名）。
- **零 `runtime/` 写入**：只做只读读取、七条 `--verify`（写盘前返回）与预检
  （自证 `unchanged = true`）；无 `mv`/`rm`/`mkdir`。**核对在 `--verify` 前后各跑一遍、
  结果相同**，是该性质的实测证据。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单、提案、
  正式设计、`docs/reviews/`；对 `docs/unity-test-log.md` 与 `docs/authorizations.md` 只读。
- 本批写入仅两个仓库路径：本证据文件与 `docs/current-status.md`。
- 复核范围：§B.1 的 136 条核对、§B.2 的七条逐字输出、§B.3 的基线派生 / 路径归因 /
  CLI 块 SHA 复算、§B.4 的预检与 §A.4 的逐字段比对、§B.6 第 1 条的缺陷登记
  （可由操作单抬头 A 点、§4 两段与 `docs/reviews/P1-M3-BODY-001.md` 末行
  `passed_candidate:` 直接复看）。

---

# C. 最后一次发令时刻复查（§2.20 + §2.0 (b) 在 `67b2ac7`）+ 对 §B 的自查更正

日期 2026-08-16，实现角色。交接来源：**接受轮 66**——它消费了 §B 登记的归因指令缺陷、
在操作单**五处**做了去写死更正，并自述「本轮是 (c) 之前的最后一个接受批次：本提交再改
HEAD，故 §2.20 与 (b) 需由实现角色再复查一次；此后本角色不再提交，直接写 (c)」。
本节即该次复查，**同时对 §B 做对抗式自查**（见 §C.4）。
**零 Play、零采集 ID 创建/消耗、零 `runtime/` 写入、零代码/测试/config/scenario/model
改动、零操作单改动。** 批次开始与结束时 `git status --porcelain` 均为空。

## C.1 §2.20 九项：**136/136 PASS**，仍跑两遍

分项计数 1: 6/6、2: 2/2、3: 26/26、4: 14/14、5: 56/56、6: 14/14、7: 1/1、8: 6/6、
9: 11/11 —— 与 §A、§B 逐项相同。**七条 `--verify` 前后各跑一遍，两遍均 136/136。**

**本轮把「未变」的覆盖面写清楚（§B 该句过强，见 §C.4 第 1 条）**：

| 对象 | 本轮约束强度 |
|---|---|
| 六个 shared 文件、`runtime/frames/`、B3 run 目录 | 存在性 / 计数（对象本身应当为空或缺席） |
| 四处旧 hold、十文件 void hold、corridor 工件 | **SHA-256 逐项相等**（含目录计数与行数） |
| 七处 post-run 归档 | **SHA-256 逐项相等**：目录聚合 + 五个单文件的行/字节/SHA |
| 七个正式 run 目录 | 计数 **11 份** + 含 `m3_body_analysis.json`；其中 **10 份**由 `--verify` 反向字节绑定（重算整份分析并要求与在盘 `m3_body_analysis.json` 逐字节相同，`input_sha256` 覆盖 `manifest.json`/`frames.jsonl`/`m3_body_truth.jsonl`/`metrics.final.json` 与四份 config）；**`summary.json` 不在其内，七个 run 各 1 份、共 7 份文件本轮只受计数约束** |

该表是**披露，不是新门**：`summary.json` 不进任何指标路径，§2.20 原文也只要求「恰 11
份」。写下来是为了让「未变」这个词在本文件里有确定的射程。

## C.2 七条只读 `--verify`：全部退出 0 且逐字复现

与 §B.2 逐字相同（臂 A 五个 `WITHIN_RANGE` `0.5784550773737355` /
`0.5783188398250908` / `0.597146417669116` / `0.5783206310103214` /
`0.5783243208518966`；B1、B2 均 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`）。
接受轮 66 自述亲自复跑过同样七条，两边结论一致。

## C.3 §2.0 (b) 复报（本轮测量时点 = 现行）

```text
$ git rev-parse HEAD
67b2ac7ebdd590ff94589e5b1b8028ea12d8dc28

$ git status --porcelain
（空输出）

$ grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md | tail -1
passed_candidate: 6e81bc23fab417813e2761755b3b122b4d01c970
```

`<BASE>` = **`6e81bc2`**（未变——本区间没有新的复核通过轮）。

```bash
$ git diff --name-only 6e81bc2..HEAD
docs/current-status.md
docs/evidence/P1-M3-BODY-001-1c-preflight.md
docs/evidence/P1-M3-BODY-001-arm-b-trial-3.md
docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md
docs/reviews/P1-M3-BODY-001.md
```

**五个路径，全部是文档**（区间内 **7 条**提交：复核轮 11、接受轮 64 续批、复核轮 12、
接受轮 65、本证据的 §B 批次 `1b3cbd1`、chore 压缩 `6269b2c`、接受轮 66）。比 §B 多出的
第五个路径就是**本证据文件自身**。**测量侧 diff 为空**（`controller/ Assets/ config/
ProjectSettings/ Packages/packages-lock.json tools/ tests/`）——七次采集与 B3 仍跑在
同一份已复核代码上。

**PLAY_GOVERNING 子集 = 恰 1 条**：操作单（仍 revision 22，未再轮换）。自 `6e81bc2`
起其改动全部是文字：§3 步骤 0′ 指针、§5 来源拆分、§6 N36 抬头，**外加接受轮 66 的五处
去写死更正**。零门变动、零冻结值改动。

**CLI 块差异本角色亲自复算**（19 行整块另取 SHA-256）：

| 比较对象 | 块行数 | 差异 |
|---|---|---|
| **已复核候选 `6e81bc2`**（本轮 `<BASE>`） | 19 / 19 | **0 行**——整块 SHA-256 `fd832df1…55dd`，逐字节相同 |
| `d278ef2` / `1b3cbd1` / `67b2ac7` | 19 / 19 | **0 行**（同一 SHA；接受轮 66 未触碰 CLI 块） |
| （历史）`408acd7` | 19 / 19 | 2 行（`--run-id` + `--body-policy`） |

**归因按实测写：对现行已复核候选 0 行不同。** 操作单经接受轮 66 更正后**不再写死任何
行数**（改为「运行时现取、实测几行报几行」），故本轮报 0 行**不与任何在盘指令冲突**
——§B 登记的那个两难已消除。接受轮 66 也**没有**把「0 行」写进文档，理由与本角色一致：
写死 0 只是把同一个错推迟到下一次通过。具名 disposition 仍由接受角色给出。

## C.4 对 §B 的对抗式自查：**两处自造问题，均已在本批更正**

1. **过强断言**：§B.1 写「磁盘状态自 §A 起**一字节未变**」。实测覆盖面不支持该词——
   七个 run 目录的 `summary.json`（共 7 份）本轮只受计数约束，未取哈希。已在 §B.1
   就地加注（原句留档）并由 §C.1 给出准确表述。**结论方向不变**：所有哈希绑定对象
   逐项相等，`--verify` 七条逐字复现。
2. **枚举不完整**：§B.6 第 1 条把缺陷写成「操作单**三处**」并逐条列出。实测本角色
   交付时（`1b3cbd1`）操作单内 `408acd7` 共 **6 处**，其中需更正的活跃指令 **5 处**
   ——本角色漏掉 revision 21 抬头的「两个基准」句与 §6 的 revision 19 条目，接受轮 66
   五处全数改到（第 6 处是 §2.0 (b) 的历史例示段，属真历史，轮 66 保留未动）。
   **方法教训与 N37 同源**：本角色是「读到哪几处就列哪几处」，而正确做法是先对写死的
   标识做一次全文 sweep（`grep -c 408acd7` 立刻返回 6）。已在 §B.6 第 1 条标注不完整
   并指向本条。**危害有限**（登记的是缺陷本身而非清单，接受角色独立复查后找齐），
   但「把不完整枚举写成看似完整的清单」正是本项目反复栽的那一类。
3. 其余 §B 断言逐条复算**属实**：§A 测量时点 `29e903a`、其后六条提交、§A 分项计数
   6/2/26/14/56/14/1/6/11、CLI 块 SHA `fd832df1…55dd`、预检 34 项且无 B3、
   `3a85` 仅存于 finding 转述（复核轮 11 已独立同结论）。**本轮预检 JSON 与 §B 那次
   整份逐字段相等**（不只是「唯一差异」级别的比对）。

## C.5 §3 步骤 0 预检与步骤 0′ 第 1 步

退出码 **0**，`status = "PASS"`，`side_effect_identity.unchanged = true`，`before`
与 `after` 相等，`run_directories` **34** 项且不含 B3。**整份 JSON 与 §B.4 那次逐字段
完全相等**。`interpreter.executable` 仍为
`~/TetheredDroneTracking/.venv-yoloe/bin/python`。步骤 0′ 第 2 步与门 4 仍未
执行（本批不启动 tracker）。

## C.6 交回接受角色

1. **B3 的 Play 前置至此全部就绪且在现行 HEAD 上成立**：§2.19 归档、§2.20 九项、
   §2.0 (b)、步骤 0/0′ 第 1 步。**§B 登记的缺陷已由接受轮 66 关闭**，本角色复看其五处
   改法：均为「去写死 + 加时间边界」，未放宽任何门、未改冻结值、未触碰 CLI 块。
2. **(c) 可在本 HEAD 起草**——前提是接受轮 66 的承诺成立（此后不再提交）。**若 (c)
   之前又有任何提交落地，§2.20 与 (b) 必须再复查一次**：本文件已经连续两轮撞上这条，
   §B → §C 就是第二次。
3. **一处措辞按字面不可满足，请接受角色按实质读（本角色只登记，不改他人文字）**：
   状态板行 1 现写「(c) 记录必须点名 (b) 报告的**同一个** HEAD」。但**记录批次自身
   必然改 HEAD**——(b) 在干净 HEAD 上测量，其报告落盘再提交就产生新 HEAD，§A
   （测 `29e903a` → 记 `9cadebd`）与 §B（测 `d278ef2` → 记 `1b3cbd1`）都是如此，
   本节亦然。**照字面读是无穷回退，任何角色都无法满足。** 操作单 §2.0 自己的写法
   才是可执行的：§A.6 第 2 条「测量时点 HEAD ≠ 发令时点 HEAD，(c) 须在写入时点自取
   HEAD/status」。**实质判据应是「(b) 与 (c) 之间无 PLAY_GOVERNING 改动」**，本轮
   实测成立：记录批次相对 `67b2ac7` 恰 **2 个路径**（本证据文件 + 状态板），
   **PLAY_GOVERNING 为空、测量侧为空**。建议 (c) 直接自取写入时点 HEAD 并援引本条。
4. **CLASS_3 P7/P8/P9 的复判**仍在接受角色手上（本角色不判级）。
5. **本批（§C）与 §B 均未经独立复核**；两节合起来的复核范围见 §C.7。
6. 批量授权边界不变：B3–B5 各走完整 §2.0 (a)–(d)，**任何 void 终态立即中止授权**；
   `--compare` 需十次齐备并单独授权；两条预登记限制继续生效，BC-BODY1-15 (d) 禁止
   据任何已见数值调参。**本批不产生 Unity 用例**，不申领 `UNITY_NA`。

## C.7 §C 批次边界声明

- **零 Play、零采集 ID 创建/消耗、零 `runtime/` 写入**（只读读取 + 七条 `--verify` +
  预检；无 `mv`/`rm`/`mkdir`）；核对在 `--verify` 前后各跑一遍、结果相同。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单、提案、
  正式设计、`docs/reviews/`；对 `docs/unity-test-log.md` 与 `docs/authorizations.md` 只读。
- 本批写入仅两个仓库路径：本证据文件与 `docs/current-status.md`。**对 §B 的两处更正
  是就地加注 + 原句留档，不删除、不改写既有结论。**
- 复核范围：§C.1 的 136 条核对与覆盖面表、§C.2 的七条逐字输出、§C.3 的基线派生 /
  五路径归因 / CLI 块 SHA 三态复算、§C.4 的两条自查更正（可由 `git show
  1b3cbd1:docs/evidence/P1-M3-BODY-001-1c-preflight.md | grep -c 408acd7` 与
  `analyze_m3_body.py` 的 `verify_rerun_not_byte_identical` 分支直接复看）、
  §C.5 的预检整份相等。

---

# D. B3 执行：四门（**启动 tracker 前落盘**）

日期 2026-08-17，实现角色。发令依据：§2.0 (a) 批量 GO（账本 2026-08-14）+ (b) §C +
(c) `docs/unity-test-log.md` 的 `PRE_PLAY_RELEASED` 条（点名 HEAD `6b138ea`）+ (d)
发令时刻 `git diff --name-only` **逐字只有** `docs/unity-test-log.md`、无未跟踪文件。
**发令时刻另复查**：§2.20 九项 **136/136**、预检退 0 `PASS` 且整份 JSON 与 §C 那次
逐字段相等、`run_directories` 34 项无 B3、`runtime/scenario_config.json` 缺席。
用户已进 Play 恰一次并保持暂停。**本节四项在启动 tracker 之前写入。**

## D.1 门 1 —— 暂停窗口（`2.000000 <= reported_sim_t < 10.000000`）

**导出命令原文**（只读；只解析保留帧元数据 JSON，不读任何真值文件）：与
`…-arm-b-trial-1.md` §B.2 **逐字同一条命令**（取保留帧中最大 `simulation_time_s`）。

**逐字输出**：

```text
directory entries: 51
retained metadata files: 25
frame_id range: min = 0  max = 24  contiguous = True
max simulation_time_s = 4.980351
min simulation_time_s = 0.181483
  frame 22: 4.58462381362915  (frame_0000000022.json)
  frame 23: 4.785099506378174  (frame_0000000023.json)
  frame 24: 4.980350971221924  (frame_0000000024.json)
GATE1 2.000000 <= 4.980351 < 10.000000 -> True
GATE2 lowest retained frame == 0 -> True
latest.json frame_id = 24
reported_sim_t (verbatim) = 4.980350971221924
```

| 要求（revision 12 记录型条款） | 值 |
|---|---|
| 导出命令原文 | 见上（引 B1 §B.2 同一条） |
| 保留帧编号范围 | `frame_id` **0–24**，连续，25 份元数据（目录共 51 项；`latest.json` 的 `frame_id` = **24**，与最大保留帧一致） |
| 导出的数值 | `reported_sim_t` = **`4.980350971221924`** |

**门 1 PASS**：两侧余量约 `2.980 s` 与 `5.020 s`（相邻帧约 `0.20 s`），不贴边。
**披露不变**：该值是真实暂停时刻的**下界**（COORD-007 §4.1，R10 未授权未开工），
冻结窗口本轮**不调整**（BC-BODY1-15 (d)）。口报不作判据，本轮用户亦未报时刻。

## D.2 门 2 —— 最低保留帧

最低保留帧恰为 **`0`** → **门 2 PASS**（见 §D.1 逐字输出同一次导出）。

## D.3 门 3 —— 冻结框匹配（用户目检）

`--dump-frame 0` 导出退出码 **0**，图 **640×480**；scratchpad 内叠加**已冻结**像素框
`(177, 195, 77, 73)`（`min_side = 73 px`）供目检——**未重新框选、未重新估框、未做
六位小数化、未读任何真值**；叠加图只落在会话 scratchpad，不进仓库、不进 `runtime/`。

**用户目检结论（逐字）**：「**匹配**」→ **门 3 PASS**。现场未做任何调整。
**三门全部 PASS，互不覆盖。**

## D.4 门 4 —— 启动前命令行核对 + §3 步骤 0′ 第 2 步

**实际将要执行的完整命令行原文**（SHA-256
`b1690a3be642076824c24b2fd99c76cea541e04ce11beabd3ab069bf3c6cb6bd`）：

```bash
~/TetheredDroneTracking/.venv-yoloe/bin/python -m controller.track_loop \
  --tracker nanotrack-v2 \
  --tracker-model-dir runtime/models/nanotrack-v2 \
  --tracker-model-spec config/nanotrack-v2.models.json \
  --reanchor-config config/detector-reanchor.models.json \
  --condition follow \
  --track-id target-0 \
  --scenario-id deterministic-loop-default \
  --ground-plane-y-m 0.2 \
  --run-id p1-m3-body-001-arm-b-trial-3 \
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

**该命令行由操作单 §4 的 19 行块机械取出**，只改第 1 行为绝对解释器路径；
**其余 18 行与操作单逐字节相同**（实测差异恰 1 行），未凭记忆重敲。

| 核对项 | 结果 |
|---|---|
| 含 `--body-policy threshold` | **True** |
| 含 `--run-id p1-m3-body-001-arm-b-trial-3` | **True** |
| 否定项：`arm-a-` / `arm-b-trial-1` / `-2` / `-4` / `-5` / `-attempt-` / `--body-policy hold` / `--compare` | **全部 False** |
| 禁用入口：裸 `python3` / `.venv-track` / 直接文件入口 | **全部 False** |

**§3 步骤 0′ 第 2 步**：命令行首解释器
`~/TetheredDroneTracking/.venv-yoloe/bin/python` 与本轮预检 stdout 的
`interpreter.executable` **字符串逐字相等**（实测 `True`）。

**门 4 PASS。四门齐备，下一步在保持暂停下启动 tracker**；corridor 启动门（臂 B 专属，
哈希不符即启动期 `ValueError`）在启动时实弹。

## D.5 tracker 执行与完成握手

corridor 启动门**无 `ValueError` 通过**（臂 B 专属，实弹）。tracker **自然退出码 0**，
stderr 仅 8 行既有依赖噪声（OpenCV `setPreferableTarget` ×2、`tifffile`、DINOv2 三条
xFormers `UserWarning`），无异常。

**stdout 末行 JSON 逐字**：

```text
{"qualification_metrics_error": null, "records": 651, "run_id": "p1-m3-body-001-arm-b-trial-3", "state": "TRACKING", "summary": "~/TetheredDroneTracking/runtime/runs/p1-m3-body-001-arm-b-trial-3/summary.json"}
```

**完成握手三项齐备**：自然退出 0 ✓；末行 JSON 指向**同一采集 ID**的 `summary.json` ✓；
run 内 `metrics.final.json` 与 `summary.json` 均存在 ✓。随后机械产出确认词：

```text
$ .venv-yoloe/bin/python tools/analyze_m3_body.py --validate-completion \
    --runtime runtime --run-id p1-m3-body-001-arm-b-trial-3 \
    --tracker-exit-code 0 --tracker-final-json '<上面的末行 JSON 原文>'
TRACKER_AUTO_COMPLETE_CONFIRMED
（退出码 0）
```

**依 BC-BODY1-29，本角色随即请用户退出**。用户答复逐字：「**已退出，没有报错**」
——**Console 无报错**。（本角色对 `docs/unity-test-log.md` 只读，该逐字答复请接受/
辅助角色代录。）

## D.6 绑定分析

```text
$ .venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-b-trial-3
{"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-3", "verified": false, "window_c_track_given_geom": 1.0}
（退出码 0，stderr 为空）
```

run 目录 create-once 建成、**恰 11 份**（五类配置原始字节 + truth + 分析 receipt 已收进）。

**臂身份三层核对通过**：`body_policy = threshold`、`body_planner_name =
threshold-corridor-v1`，与冻结 ID 推导的期望臂逐项相等。**无 predecessor / attempt
字段**——B3 的 ID 从未被消耗，两个前驱门都不触发（与 §1、§2.20 第 9 项预写一致）。

**准入与两条域完整性门**（接受轮 42 §A 取代 `>= 2P` 上界的那两条）：三条判据在
`analyze_m3_body.py:1117/1142/1148` 都是主路径上的无条件 `raise`，**退出 0 即三条全过**。
下界实测 `final_unwrapped = 415.9308532790733 m >= P = 212.97056274847716 m` ✓。

**八条 `--verify` 全部退出 0 且逐字复现**（A1…A5 + B1 + B2 + **B3**）：臂 A 五个
`WITHIN_RANGE`（`0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` /
`0.5783206310103214` / `0.5783243208518966`），**B1、B2、B3 均 `SCENE_DEGENERATE` /
`1.0` / 窗口 `1.0`**。前七个 run 一字节未动。

## D.7 主结果与机体运动（**归因归接受角色，本节只报事实**）

| 项 | B1 | B2 | **B3** |
|---|---|---|---|
| `full_loop_c_geom` | `1.0` | `1.0` | **`1.0`** |
| `h1.disposition` | `SCENE_DEGENERATE` | `SCENE_DEGENERATE` | **`SCENE_DEGENERATE`**（天花板 `0.95`） |
| 窗口 `C_track|geom` | `1.0` | `1.0` | **`1.0`** |
| `body_motion_effort_m` | `88.64522663177961` | `75.26945194958653` | **`91.174630127364`** |
| `body_path_length_m` | `61.42306359956821` | `49.16248028068326` | **`64.4545385428812`** |
| `planner_switch_count` | `11` | `11` | **`11`** |
| `nees_median` | `5.067625439804517` | `5.2993597343857255` | **`5.196313303659595`** |
| `min_side_ge20_share` | `1.0` | `1.0` | **`1.0`** |
| 停留 / 圈数 | `41.389801 s` / `1.618675` | `29.602264 s` / `1.509862` | **`76.803711 s` / `1.952997`** |

**reason 直方图（626 decision 帧）**：`margin_below_trigger+corridor_blocked` **319**、
`within_hysteresis_band` **121**、`margin_below_trigger` **95**、`margin_above_release`
**85**、`margin_below_trigger+corridor_shortened` **6**。
**`no_observation` / `no_platform_state` / `no_estimate` / `planner_exception` 与
`publish_failure_fallback` 全 0 帧。** `frames.jsonl` 共 782 行。

> **直方图与停留/圈数的派生口径本轮先校准再用**：同一段代码对 B1 复出 623 =
> 324/116/95/82/6、对 B2 复出 622 = 339/109/93/75/6，与两轮已发布数字逐项相等；
> 停留同法复出 B1 `41.389801` / B2 `29.602264`，圈数复出 `1.618675` / `1.509862`。
> 故 B3 的三个数与前两轮同底。

`body_motion_effort_m > 0`，不触发 revision 19 §3 步骤 6 的「零位移即停」分支。
其余披露：`loop_gimbal_saturated_share = 0.5002466820299678`、
`loop_tether_saturated_share = 0.4688021583864506`、窗口内云台饱和 `0.0`、
系留饱和 `0.21545593569013038`；`center_error_median_px = 34.60271072387695`、
`p90 = 44.789591217041014`、`max = 106.28694152832031`。

## D.8 登记的观察与交回接受角色

**以下全部只登记、不作统计主张、不得据以调参**（BC-BODY1-15 (d)；`--compare` 需十次
齐备并单独授权，至今无 GO）：

1. **饱和预登记在 n=3 上得到第三个同向数据点**：`C_geom` 三次都是 `1.0`。结论口径
   不变——只能报「臂 B 达到 100 % 几何可见，效应量为**下界**」。
2. **H2-CEILING 第三次实测确认**：`min_side_ge20_share` 三次都是 `1.0`（125/125）。
3. **`planner_switch_count` 连续第三次恰为 `11`**——三次 Play 完全一致，登记备查。
4. **n=2 时登记的那条方向性观察在 n=3 上不成立**：轮 63 记过「`corridor_blocked`
   324 → 339 帧而位移下降」；B3 是 **319 帧（三次最少）配 `91.175 m`（三次最多）**。
   三点合起来反而是「阻塞越少、位移越大」的同向关系。**这正说明 n=2 的方向性读法
   不可靠**，本条按原则只登记。
5. **操作性发现（无门，但下轮要改做法）**：本轮 post-tracker 停留 **`76.803711 s`**，
   接近 B1 的两倍、B2 的 2.6 倍，圈数因此到 **`1.952997`**——距 `2P = 425.9411254969543 m`
   仅 **`10.01 m`**。`>= 2P` 上界已由接受轮 42 §A **撤下**，故**本轮不受任何影响**，
   两条域完整性门也未触发；但若该上界仍在，这次会擦边。**建议 B4/B5 在确认词产出后
   更快请用户退出**（BC-BODY1-29 本来就要求「随即」），把停留压回 30–40 s 量级。

**交回事项**：

- **B3 的归因归接受角色**（本角色不判 valid/void）。若判有效，臂 B 将是 **3/5**。
- **B4 不得在两件事落地前开工**：B3 的归因，以及 B3 的 post-run 归档合同——**shared
  槽位现在压着 B3 的产物**（`runtime/frames/`、truth、metrics 与三个发布文件）。
- 用户逐字答复「已退出，没有报错」待接受/辅助角色代录进 `docs/unity-test-log.md`；
  该文件的 (c) 条目仍未提交，随本轮归因批次一并入库。
- **零 void 终态**，故 2026-08-14 的 B2–B5 批量授权**继续有效**（是否成立由接受角色
  按 §5 四种终态逐条对照后认定）。
- 本节与 §B/§C 一样**未经独立复核**。

## D.9 §D 批次边界声明

- **恰一次 Play**，采集 ID `p1-m3-body-001-arm-b-trial-3` **已消耗**；未重进、未重试。
- 零代码/测试/config/scenario/model/阈值/指标/CLI 改动；**未修改操作单**
  （BC-BODY1-21/-22 全程遵守）、提案、正式设计、`docs/reviews/`；对
  `docs/unity-test-log.md` 与 `docs/authorizations.md` 只读。
- `runtime/` 写入全部由 Unity 与 tracker/分析器的正常产出造成；本角色未做任何
  `mv`/`rm`/`mkdir`，未预建 run 目录（create-once 由 `RunLogger` 完成）。
- 门 3 的目检图只落在会话 scratchpad，不进仓库、不进 `runtime/`。
- 本批写入仓库路径：本证据文件与 `docs/current-status.md`。
- 复核范围：§D.1–§D.4 四门（导出命令、保留帧范围、`reported_sim_t`、命令行原文与
  其 SHA-256 均已落盘）、§D.5 握手三项与确认词、§D.6 绑定分析与八条 `--verify`、
  §D.7 各量（直方图/停留/圈数的派生口径可用 B1/B2 已发布值直接校准复看）、
  §D.8 第 4/5 条两条登记。
