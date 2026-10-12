# P1-M3-BODY-001 arm A trial 2 证据（操作单 revision 12）

本文件记录实现角色在**最终干净 HEAD** 上执行的两项 Play 前只读工作：
操作单 `docs/evidence/P1-M3-BODY-001-1c-preflight.md` 的 **§2.0 step (b)**
报告与 **§2.6** 只读状态核对（交接行：Acceptance round 39 §E）。

**零 Play、零采集 ID 创建/消耗、零 `runtime/` 写入、零 `controller/`、
零 `Assets/`、零 `config/`、零 `tools/`、零 `tests/` 改动。** 本批**不进入
Play**，也不启动 tracker；§2.0 (c)（Acceptance 写 `docs/unity-test-log.md`）
与 (d)（发令时刻工作树只允许该一份未提交差异）不属本批。

日期：2026-08-13。执行角色：实现（implementation）。

## A. §2.0 step (b) 报告

### A.1 HEAD 与工作树状态

```text
$ git rev-parse HEAD
cc600bd49b3b05ad6c68f081f18540ba8652254c

$ git status --porcelain
（空输出）
```

本批全部命令**执行前与执行后**的 `git status --porcelain` 均为空
（只读性证明见 §B.4）。

### A.2 基线 delta 的路径归因

基线按操作单 §2.0 (b) 取**上一个通过独立 Review 的候选** `6019f33`
（`docs/reviews/P1-M3-BODY-001.md` round 6 `PASS_WITH_NOTES`）。

`git diff --name-only 6019f33..HEAD` = **26 个路径**，区间共 27 个 commit。
逐类归因（`(A)` = 新增，`(D)` = 删除，其余为修改）：

| # | 类别 | 路径 | 归属 |
|---|---|---|---|
| 1 | COORD-007 工作流基础设施 | `AGENTS.md`、`docs/collaboration-workflow.md`、`docs/roles/{acceptance,chore,ideation,implementation,review}.md`、`.claude/commands/{accept,chore}.md`（9 条） | COORD-007 第一批 R1–R9 协调批次 + R5 例外修正 + N12 裁定措辞同步（授权：`docs/authorizations.md` 2026-08-12/2026-08-13 COORD-007 条目） |
| 2 | COORD-007 文档自检工具与测试 | `tools/check_docs.py`、`tools/check_role_writes.py`、`tools/rotate_docs.py` (D)、`tests/test_check_docs.py`、`tests/test_check_role_writes.py`、`tests/test_rotate_docs.py` (D)（6 条） | 同上协调批次 + 两次 `--infra-fix`（F4/F5 与 N12 落地）；**这 6 条即接受轮 39 §F 判定的 inert delta** |
| 3 | COORD-007 提案与复核记录 | `docs/proposals/COORD-007-process-overhead-reduction.md` (A)、`docs/reviews/COORD-007.md` (A)（2 条） | 接受轮 1–5 与复核轮 1–3 的记录 |
| 4 | `P1-M3-BODY-001` 轮次记录 | `docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md`、`docs/reviews/P1-M3-BODY-001.md`、`docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md`、`docs/evidence/P1-M3-BODY-001-1c-preflight.md`（4 条） | 复核轮 6、接受轮 33–39（含 §M/§N 归档转录与**操作单 revision 12**） |
| 5 | 共享账本与状态 | `docs/current-status.md`、`docs/implementation-status.md`、`docs/authorizations.md`、`docs/unity-test-log.md`、`docs/archive/current-status-2026-08.md`（5 条） | 状态板、里程碑账本、授权账本（含 trial 2 GO）、Unity 日志、Log 归档 |

合计 9 + 6 + 2 + 4 + 5 = **26** ✓。

自接受轮 39 §F 的测量时点 `643bc2f` 起，`643bc2f..HEAD` 只有一条路径
（`docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md`，即 §G
诊断记录本身），无任何代码/配置变化。

### A.3 PLAY_GOVERNING 子集 —— 实测 7 条，与 §F「恰六个路径」不一致（**交回接受角色**）

workflow §4.4 的唯一权威定义 = `controller/`、`Assets/`、`tools/`、
`tests/`、`config/`、`ProjectSettings/`、`Packages/packages-lock.json`，
**加上「该 work item 冻结集点名的操作单文件」**。该末句存在两种读法，
实测结果随读法不同：

- **读法 1（操作单文件本身入集）**：子集 = **7 条** —— §A.2 第 2 类的 6 条，
  **加** `docs/evidence/P1-M3-BODY-001-1c-preflight.md`。第 7 条即接受轮 39
  §B 依授权撰写的 **revision 12**，也就是本批正在执行的指令本身，不是
  未归因的意外改动；但按此读法，§F「在 PLAY_GOVERNING 上非空，**恰六个
  路径**」的计数句漏了它。
- **读法 2（「冻结集点名的文件」= §1 钉住表点名的工件）**：子集 = **6 条**，
  与 §F 逐字一致；§1 点名的两个工件（`config/scenario.default.json`、
  `docs/evidence/P1-M3-BODY-001-scene-body-margin.json`）本轮实测**逐字节
  未变**（§D）。

**实现角色不自行裁定该定义**（AGENTS.md：歧义退回接受角色）。据实报告：
若采读法 1，§F 的计数句需要由接受角色更正并为 revision 12 这条补一句
归因；若采读法 2，§F 计数成立、无需改动。**两种读法下 §A.4 的测量侧
逐字节相同都成立**，故本批按 §2.0 (b) 的注（"报告该归因即可，不必为此
停摆"）继续执行 §2.6，未就此停摆，也未自行放宽任何条件。

### A.4 测量侧逐字节相同（§F inert 归因的前提，本轮复验成立）

```text
$ git diff --name-only 6019f33..HEAD -- controller/ Assets/ config/ \
    ProjectSettings/ Packages/packages-lock.json \
    tools/analyze_m3_body.py tools/preflight_reanchor_env.py
（空输出）
```

即 tracker、planner、estimator、评估器、场景/模型/re-anchor 配置、分析器
与预检工具在 HEAD 上与被复核通过的候选 `6019f33` **逐字节相同**。操作单
§2.0 (b) 注规定的归因失效条件（"Play 之前上述测量侧路径出现任何字节改动"）
**未触发**。

### A.5 §3 步骤 0 环境预检

命令（§1 钉住的唯一形式）：

```bash
.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json
```

**退出码 `0`**，stdout `status` = `"PASS"`。stderr 有依赖噪声
（OpenCV `setPreferableTarget` 两行 WARN、`tifffile` 缺失提示、DINOv2 的
三条 xFormers `UserWarning`），不影响退出码与 JSON；如实记录。

完整 stdout JSON（逐字）：

```json
{
  "constructors": {
    "dinov2_embedder": "controller.reanchor_models.DinoV2Embedder",
    "nanotrack_tracker": "controller.trackers.NanoTrackV2Tracker",
    "yoloe_proposer": "controller.reanchor_models.YoloeProposer"
  },
  "interpreter": {
    "executable": "~/TetheredDroneTracking/.venv-yoloe/bin/python",
    "prefix": "~/TetheredDroneTracking/.venv-yoloe",
    "python_version": "3.12.13"
  },
  "mode": "reanchor-preflight",
  "nanotrack": {
    "backend": "opencv-dnn-default/cpu",
    "model_sha256": {
      "backbone": "530bdd0cd00f19afab79a863e71ba71e3312395a5dc9151af675082bdaaa2fc4",
      "neckhead": "0d8c0637be849f092cc7236cae02e55c8b9455ebe37ba50601d6115db4247cd9"
    },
    "name": "nanotrack-v2",
    "opencv_package_pin": "opencv-contrib-python==5.0.0.93",
    "opencv_version": "5.0.0",
    "preprocessing_id": "opencv-tracker-nano-5.0.0-default-v1"
  },
  "packages": {
    "cv2": {
      "pin": "5.0.0",
      "pin_source": "nanotrack spec opencv.tested_version",
      "raw": "5.0.0"
    },
    "torch": {
      "pin": "2.13.0",
      "pin_source": "reanchor config runtime.torch_pin",
      "raw": "2.13.0"
    },
    "torchvision": {
      "pin": "0.28.0",
      "pin_source": "reanchor config runtime.torchvision_pin",
      "raw": "0.28.0"
    },
    "ultralytics": {
      "pin": "8.4.104",
      "pin_source": "reanchor config runtime.ultralytics_pin",
      "raw": "8.4.104"
    }
  },
  "reanchor_config": {
    "carrier": "minimal-triple-gated-re-anchor",
    "device": "cpu",
    "path": "config/detector-reanchor.models.json",
    "schema_version": "tethered-detector-reanchor/v1",
    "sha256": "593734d67ada73a0304d67d27c6ae536be616d2180f744336b85ff6e0ac706d2"
  },
  "side_effect_identity": {
    "after": {
      "guarded_files": {
        "runtime/body_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/gimbal_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/metrics.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/tracking_observation.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        }
      },
      "run_directories": [
        "p1-detect-001-qual-1",
        "p1-detect-001-qual-2",
        "p1-detect-001-qual-3",
        "p1-m3-body-001-arm-a-trial-1-attempt-4",
        "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold",
        "p1-track-follow",
        "p1-track-follow-attempt1",
        "p1-track-nadir",
        "p1-track-occlusion",
        "rate20-calib",
        "rate20-follow-r1",
        "rate20-follow-r2",
        "rate20-follow-r3",
        "rate20-nadir-r1",
        "rate20-nadir-r2",
        "rate20-nadir-r3",
        "rate5-calib",
        "rate5-follow-r1",
        "rate5-follow-r2",
        "rate5-follow-r3",
        "rate5-nadir-r1",
        "rate5-nadir-r2",
        "rate5-nadir-r3",
        "rs2-pilot",
        "rs2-r20-follow-1",
        "rs2-r20-follow-2",
        "rs2-r20-follow-3"
      ]
    },
    "before": {
      "guarded_files": {
        "runtime/body_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/gimbal_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/metrics.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/tracking_observation.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        }
      },
      "run_directories": [
        "p1-detect-001-qual-1",
        "p1-detect-001-qual-2",
        "p1-detect-001-qual-3",
        "p1-m3-body-001-arm-a-trial-1-attempt-4",
        "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold",
        "p1-track-follow",
        "p1-track-follow-attempt1",
        "p1-track-nadir",
        "p1-track-occlusion",
        "rate20-calib",
        "rate20-follow-r1",
        "rate20-follow-r2",
        "rate20-follow-r3",
        "rate20-nadir-r1",
        "rate20-nadir-r2",
        "rate20-nadir-r3",
        "rate5-calib",
        "rate5-follow-r1",
        "rate5-follow-r2",
        "rate5-follow-r3",
        "rate5-nadir-r1",
        "rate5-nadir-r2",
        "rate5-nadir-r3",
        "rs2-pilot",
        "rs2-r20-follow-1",
        "rs2-r20-follow-2",
        "rs2-r20-follow-3"
      ]
    },
    "checked": [
      "runtime/runs direct child directory names",
      "runtime/body_command.json present/size/sha256",
      "runtime/gimbal_command.json present/size/sha256",
      "runtime/tracking_observation.json present/size/sha256",
      "runtime/metrics.json present/size/sha256"
    ],
    "unchanged": true
  },
  "status": "PASS"
}
```

要点：`side_effect_identity.unchanged = true`（预检自身对 `runtime/runs/`
子目录集合与四个受护文件零副作用）；`run_directories` 中**不含**
`p1-m3-body-001-arm-a-trial-2`，与 §B 第 7 项独立一致。

### A.6 测量时点 HEAD ≠ 发令时点 HEAD（本批必须先提交）

§2.0 (d) 要求发令时刻工作树**只允许** `docs/unity-test-log.md` 一份未提交
差异，因此本批（本证据 + 状态板）必须在 (c) 之前提交——与 arm A trial 1
证据 §A 同一先例。所以：

- **§A.1 记录的是测量时点的 HEAD**（`cc600bd…`，当时工作树为空），
  不是发令时点的 HEAD。
- 本批只动**两个文档路径**：`docs/evidence/P1-M3-BODY-001-arm-a-trial-2.md`
  （新增）与 `docs/current-status.md`。二者在 §A.3 的**两种读法下都不属
  PLAY_GOVERNING**；本批提交后复验，`6019f33..HEAD` 的测量侧 diff **仍为
  空**，PLAY_GOVERNING 子集**仍是同样那 6（或含操作单则 7）条**，未新增。
- 按 COORD-007 R7（可派生标识禁手写），本文件**不写死**本批提交后的 HEAD：
  **§2.0 (c) 的权威 Play 前记录必须由接受角色在写入时点自行运行
  `git rev-parse HEAD` 与 `git status --porcelain` 取值**，不得复制 §A.1
  的测量时点值。若 (c) 之后、Play 之前又产生任何新提交，(c) 的记录同样
  失效并须重取。

## B. §2.6 Play 前只读状态核对（本轮唯一待执行的 §2 动作）

七项**全部通过**，展开为 **67 条机械核对，67 PASS / 0 FAIL**。期望值一律
取自 §2.5 第 4–7 项原表与 `docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md`
§B / §F.1 / §H.1 / §I.1 / §N.1，未在本文件重抄哈希做二次转写。

### B.1 逐项结果

| §2.6 项 | 核对内容 | 结果 |
|---|---|---|
| 1 | `runtime/` 下 `body_command.json`、`gimbal_command.json`、`tracking_observation.json`、`metrics.json`、`m3_body_truth.jsonl`、`scenario_config.json` | 六项**均不存在** ✓（6/6） |
| 2 | `runtime/frames/` 存在且为空 | 存在、**0 项** ✓（2/2） |
| 3 | 1b / attempt-1 / attempt-2 / attempt-3 四处 hold 逐项等于 §2.5 第 4–7 项原表 | 帧计数 **257 / 93 / 109 / 257** ✓；1b 五个 SHA-256 ✓；attempt-1 truth 46 行 + SHA、metrics SHA ✓；attempt-2 truth 54 行 + SHA、metrics SHA ✓；attempt-3 run hold 恰 2 文件（`frames.jsonl` 755 行、`manifest.json` 207 行，两 SHA 相符）+ truth 627 行 + metrics + 三个发布 hold SHA ✓（27/27） |
| 4 | A1 正式 run 目录存在且恰 11 份文件；只读 `--verify` 退出码 0 且逐字返回冻结 JSON | **11 份** ✓；目录聚合 SHA-256 与 §N.1 的 `7c3af28e…cda79` 相等 ✓；`--verify` 见 §B.2 ✓（3/3） |
| 5 | A1 post-run 归档存在且恰 6 项，逐项计数/SHA-256 按 §N.1 原表 | 6 项且名称相符 ✓；`frames/` **257** 项且聚合 SHA-256 = `ea9ba050…2fb3` ✓；其余五个文件的行数/字节/SHA-256 全部相等 ✓（20/20） |
| 6 | 无 release pointer、无 scouting session / qualification 标记 | 八个具名标记**均不存在** ✓（8/8） |
| 7 | A2 create-once 前置：`runtime/runs/p1-m3-body-001-arm-a-trial-2/` 不存在 | **不存在** ✓（1/1） |

第 4 项与第 5 项的 A1 现场（正式 run 目录、post-run 归档）本轮全程作为
**只读保全对象**：未移动、未覆盖、未删除，也未作为 trial 2 的任何输入。

### B.2 第 4 项的只读复算（`--verify`）

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify \
  --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
```

**退出码 `0`**，stderr 为空，stdout 与操作单 §2.6 写死的期望行经 `cmp`
**逐字节相同**（`BYTE_IDENTICAL=YES`）：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
```

### B.3 目录聚合 SHA-256 的口径（复现说明）

§N.1 的两个"目录聚合 SHA-256"未在任何文件写明算法。本轮以穷举复现确定其
唯一口径：**对目录内每个文件取 SHA-256，组成 `<sha256>  <目录内相对路径>\n`
的行（两个空格，`shasum -a 256` 格式），按行整体排序后拼接，再对该文本取
SHA-256**（等价于 `cd <dir> && shasum -a 256 * | sort | shasum -a 256`）。
该口径同时复现 §N.1 记录的**两个**已知值——post-run `frames/` 的
`ea9ba050…2fb3`（257 文件）与 A1 run 目录的 `7c3af28e…cda79`（11 文件），
故认定为原口径。它只依赖目录内相对路径，因此对目录整体移动稳定，与 §N.1
"移动前后相等"的记法自洽。**本节只是复现说明，不新增任何门。**

### B.4 只读性证明

- 本批未执行任何 `mv`、`rm`、`mkdir`、重定向写入或 `--finalize`；核对脚本
  只做 `open(..., 'rb')` 读取与 `stat`，写出的中间文件全部落在会话
  scratchpad，不在仓库内。
- `git status --porcelain` 在预检、`--verify`、核对脚本**之前与之后**均为
  **空**。
- 预检自身的 `side_effect_identity.unchanged = true`（§A.5）。
- `--verify` 走的是写盘前返回的只读路径（`analyze_m3_body.py:1368-1373`）。
- 三条命令全部跑完后重新确认：`runtime/frames/` 仍为 0 项，六个 shared
  文件仍不存在，`runtime/runs/p1-m3-body-001-arm-a-trial-2/` 仍不存在。

## C. §3 步骤 0′ 第 1 步：解释器逐字值落盘

按操作单 §3 步骤 0′ 第 1 步，从 §A.5 预检 stdout JSON 取
`interpreter.executable` 的**逐字值**记入本证据文件：

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python
```

与 §1 冻结的唯一合法入口 `.venv-yoloe/bin/python -m controller.track_loop`
的解释器部分一致（前者是后者的绝对路径形式，`prefix` =
`~/TetheredDroneTracking/.venv-yoloe`）。

**尚未执行**：步骤 0′ 第 2 步（启动 tracker 时命令行首解释器路径与该值
字符串逐字相等，并把实际命令行原文记入证据）——本批不启动 tracker，该步
在获授权的那次 Play 中执行并追记入本文件。

## D. §1 钉住工件的补充复验（超出 §2.6 七项，只读）

§2.6 未要求，但本轮顺带机械复验 §1 钉住表中与本次采集直接相关的工件，
全部相符；四者也都**不在** §A.2 的基线 delta 内：

| 工件 | 实测 SHA-256 | §1 / 预检钉住值 |
|---|---|---|
| `config/scenario.default.json` | `f9c9205249aacf7487579ca42f727c766800cc329d0523ec82a96140564a2ce3` | 相等 ✓ |
| `docs/evidence/P1-M3-BODY-001-scene-body-margin.json` | `c72c940736da9bb1d2924e0d8349f8cfeb08cfb06013e656b72793155f89576d` | `c72c9407…576d` ✓ |
| 上文件内 `visible_arc.sha256` | `4fe2eea5e831301be8fea76e4757e151113dcd0251941e88a2c21b1e1a6bdf55` | `4fe2eea5…df55` ✓ |
| `config/detector-reanchor.models.json` | `593734d67ada73a0304d67d27c6ae536be616d2180f744336b85ff6e0ac706d2` | 与预检 `reanchor_config.sha256` 相等 ✓ |

## E. 未验证项、已知限制与交回接受角色的事项

1. **PLAY_GOVERNING 计数（§A.3）**：实测 7 条 vs 接受轮 39 §F 的"恰六个
   路径"，差异源于 workflow §4.4 末句的两种读法。**由接受角色裁定**；
   实现角色未自行取舍，也未据此停摆（§2.0 (b) 注明确"报告即可"）。
2. **全套自动测试本批未重跑**。本批零代码/测试改动（§A.4 逐字节证明），
   不是稳定候选停点，且在 Play 前刻意不触碰工作树。当前权威记录是接受轮
   39 §G 的诊断运行：`518 ran，1 failure + 1 error + 1 skipped`，两条不
   通过同源于 `.venv-yoloe` 的 cv2 未装 `opencv-contrib` 的 CSRT 组件，
   属 `P1-TRACK-001` 旧基线追踪器，不在 trial 2 的采集/控制/指标路径上。
   **如实声明为"本批未验证"，不代表已验证。**
3. **COORD-007 §4.1 的一帧下界缺口仍敞开**：`reported_sim_t` 由保留帧
   导出只是暂停真实时刻的**下界**，"末帧 `9.97` 通过门 1 而真实暂停在
   `10.03`"今天仍可逐字重演。revision 12 的记录型条款未消除它，本批也
   不消除；消除需 R10（未授权、属代码）。
4. **A1 post-run 归档的位置风险未处置**：该归档位于
   `runtime/test-results/`（Unity Edit Mode 日志/XML 的累积输出地）。
   操作单 §2.6 注已登记该风险并明确本轮**不移动**；本批遵此，仅只读核对。
5. **本批未执行 §2.0 (c)/(d)**：Unity 日志对实现角色只读，(c) 由接受
   角色在用户进 Play 前写入；(d) 的"唯一未提交差异 = `docs/unity-test-log.md`"
   在发令时刻由发令方核对。本批产出的两个文件（本证据 + 状态板）应在
   (c) 之前提交，以免污染 (d) 的判据。
6. **§3 步骤 0′ 第 2 步、门 1 的 `reported_sim_t` 落盘、门 2/门 3** 均属
   Play 当场动作，本批未执行。

## G. Play 与三个独立硬门（§3 步骤 1–2，本段在**启动 tracker 之前**落盘）

发令时刻实测（本段写入之前）：`git diff --name-only` **逐字只有**
`docs/unity-test-log.md`（§2.0 (d) 成立），HEAD `f194e969…`；§3 步骤 0 预检
在该 HEAD 上**重跑**通过（退出码 0、`status="PASS"`、
`side_effect_identity.unchanged=true`）；§2.6 关键状态复认不变。
round 40 的 BC-BODY1-21/-22 已知悉并遵守：本次 Play 期间不修改操作单。

### G.1 用户进入 Play 并暂停（口报如实记录，**不作判据**）

用户逐字报告：「**已暂停，我看不到HUD的时间但预估在5S**」。按 revision 12
门 1 的记录型条款，`reported_sim_t` **不得**取该口报值，必须由保留帧机械
导出（见 §G.2）。口报仅作时序记录。

### G.2 门 1 —— 暂停窗口（`2.000000 <= reported_sim_t < 10.000000`）

**导出命令原文**（只读，`simulation_time_s` 由 `SensorFrameWriter.cs:261`
写入）：

```bash
.venv-yoloe/bin/python -c "
import glob, json, os
paths = sorted(glob.glob('runtime/frames/frame_*.json'))
ids = [int(os.path.basename(p)[6:-5]) for p in paths]
recs = [(int(json.load(open(p))['frame_id']), json.load(open(p))['simulation_time_s']) for p in paths]
recs.sort()
print('retained_json_files =', len(paths))
print('frame_id_range      =', min(ids), '..', max(ids))
print('contiguous          =', ids == list(range(min(ids), max(ids)+1)))
print('lowest_frame_id     =', recs[0][0])
print('max_frame_id        =', recs[-1][0])
print('reported_sim_t      =', repr(max(t for _, t in recs)))
print('argmax_frame_id     =', max(recs, key=lambda r: r[1])[0])
print('first_sim_t         =', repr(recs[0][1]))
print('mean_s_per_frame    =', repr((recs[-1][1]-recs[0][1])/(len(recs)-1)))
"
```

**输出（逐字）**：

```text
retained_json_files = 27
frame_id_range      = 0 .. 26
contiguous          = True
lowest_frame_id     = 0
max_frame_id        = 26
reported_sim_t      = 5.383249759674072
argmax_frame_id     = 26
first_sim_t         = 0.18436971306800842
mean_s_per_frame    = 0.19995692486946398
```

- **保留帧编号范围**：`0`–`26`（27 个 json + 27 个 jpg + `latest.json` =
  55 项），编号连续无缺口。
- **导出的 `reported_sim_t`**：`5.383249759674072`，取自保留帧中最大
  `simulation_time_s`（frame `26`）。
- **判定**：`2.000000 <= 5.383249759674072 < 10.000000` → **门 1 PASS**。
- 口报「预估 5S」与导出值同量级但不相等，判据以导出值为准（与 attempt 4
  的「5S 左右」vs `6.381126` 同一处置）。
- **披露不变**：该值是暂停真实时刻的**下界**（本轮实测均值
  `0.19995692486946398 s/帧`，末帧之后到暂停生效的不足一帧不可见）。
  COORD-007 §4.1 的缺口仍敞开，本轮不因此调整冻结窗口。

### G.3 门 2 —— 最低保留帧必须恰为 `0`

`lowest_frame_id = 0`（见 §G.2 同一次导出）→ **门 2 PASS**。

### G.4 门 3 —— 冻结框匹配（用户目检）

导出命令（唯一合法入口，输出落在会话临时目录，**不写仓库、不写
`runtime/`**）：

```bash
.venv-yoloe/bin/python -m controller.track_loop --dump-frame 0 --output <scratch>/trial2_frame0.jpg
```

退出码 0，导出图 `640×480`。叠加的是**已冻结**像素框
`(177, 195, 77, 73)`，未重新框选、未重新估框、未做六位小数化，也未读取
`runtime/m3_body_truth.jsonl` 或任何真值。用户只做**匹配/不匹配**目检。

**用户目检结论（逐字）**：「**匹配**」→ **门 3 PASS**。现场未做任何调整。

`git status --porcelain` 在 §G.2/§G.4 两次导出前后不变（仍只有
`docs/unity-test-log.md` 与本证据文件），`runtime/frames/` 仍为 55 项。

**三门全部 PASS**（门 1 `5.383249759674072` ∈ `[2,10)`、门 2 最低帧 `0`、
门 3 用户目检匹配），互不覆盖，故按 §3 步骤 2 末段在**保持暂停**下启动
tracker。

### G.5 §3 步骤 0′ 第 2 步 —— 解释器绑定与实际命令行（启动前落盘）

**实际执行的完整命令行原文**（工作目录 = 仓库根）：

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
  --run-id p1-m3-body-001-arm-a-trial-2 \
  --init-frame 0 \
  --init-box 0.2765625 0.40625 0.1203125 0.15208333333333332 \
  --planned-duration-s 130.0 \
  --maximum-ground-range-m 1000.0 \
  --expires-after-s 1.0 \
  --poll-interval-s 0.02 \
  --body-policy hold \
  --body-planner-config config/p1-m3-body-001.json \
  --body-scenario-config config/scenario.default.json
```

**逐字相等核对**：命令行首的解释器路径
`~/TetheredDroneTracking/.venv-yoloe/bin/python` 与 §A.5 预检 JSON
的 `interpreter.executable` **字符串逐字相等** → 步骤 0′ 第 2 步 PASS。

**披露（拼写选择，零语义改动）**：§4 把唯一合法入口写成**相对**形式
`.venv-yoloe/bin/python -m controller.track_loop`，而步骤 0′ 第 2 步要求与
预检输出的**绝对**值字符串逐字相等。两条同时满足的唯一写法就是把**同一个
解释器**按绝对路径拼写，本轮即如此执行；机械证据：`[ <绝对路径> -ef
.venv-yoloe/bin/python ]` 为真（同一文件，二者均为指向
`…/cpython-3.12-macos-aarch64-none/bin/python3.12` 的同一 symlink），
且该绝对路径下 `sys.executable` 打印值与预检值逐字相同。**§4 的三条禁令
（裸 `python3`、`.venv-track/bin/python`、直接文件入口）一条也未触碰，
`-m controller.track_loop` 模块入口未变，18 个参数逐字未改、未加、未减，
`--run-id` 即 revision 12 冻结的 A2。** 未修改操作单（BC-BODY1-21），本条
仅作披露，供接受角色事后统一措辞。

## H. tracker 启动、运行与完成握手（§3 步骤 2 末段–步骤 4）

### H.1 启动成功（保持暂停下，非 `TRIAL_VOID_TRACKER_STARTUP_FAILURE`）

启动后在**保持暂停**状态下机械确认：进程存活并越过
`TrackLoop.initialize`；`runtime/runs/p1-m3-body-001-arm-a-trial-2/`
create-once 成功，含 `manifest.json` 与 `frames.jsonl`；已追平全部 27 个
保留帧（1 条 `compute_stage=init` @ frame 0 + 26 条 update @ frames 1–26，
全程 `state=TRACKING`），并另有 3 条 `record_kind=event` 的重锚轮记录
（与 A1 的 133 条同型）；`tracking_observation.json`、`body_command.json`、
`gimbal_command.json` 均已发布。stderr 仅有既有依赖噪声（OpenCV
`setPreferableTarget` WARN、DINOv2 xFormers `UserWarning`）。

manifest 身份（本轮实读）：`run_id = p1-m3-body-001-arm-a-trial-2`、
`body_planner.policy = hold` / `.planner = hold-v1`、`condition = follow`、
`init = {frame_id: 0, box_norm: [0.2765625, 0.40625, 0.1203125,
0.15208333333333332]}`、`scenario_config_sha256 = f9c92052…4a2ce3`、
`body_planner.config_sha256 = 3d1c4b54…7f9ae`。

确认启动成功后才请用户恢复 Play（§3 步骤 3），此后未再暂停。

### H.2 运行结束时的机械事实

- **tracker 自然退出码 `0`**（后台任务完成通知逐字为
  `Background command "Start the arm A trial 2 tracker (frozen CLI)"
  completed (exit code 0)`）；随后 `pgrep -f "controller.track_loop"`
  无命中，非信号终止、非人工终止。
- **stdout 最后一行 JSON（逐字）**：

  ```json
  {"qualification_metrics_error": null, "records": 652, "run_id": "p1-m3-body-001-arm-a-trial-2", "state": "TRACKING", "summary": "~/TetheredDroneTracking/runtime/runs/p1-m3-body-001-arm-a-trial-2/summary.json"}
  ```

  同一 stdout 在该行之前另有依赖噪声一行
  `Could not import \`tifffile\`, TIFFImageDataDecoder will be disabled`
  （与 A1 相同，如实保留；validator 取最后一行 JSON）。
- run 目录现有四份文件：`frames.jsonl`、`manifest.json`、
  **`metrics.final.json`**、**`summary.json`**。
- 记录构成：783 行 = **652 条帧记录**（1 init + 651 update，全部
  `state=TRACKING`，`frame_id` 0–651 连续）+ 131 条 event 记录；
  帧记录 `simulation_time_s` 覆盖 `0.18436971306800842` –
  `130.38473510742188`。
- `summary.json`：`actual_duration_s = 130.20036539435387`（≥ 冻结
  watchdog `130.0`）、`metrics_snapshot_present = true`。
- `runtime/frames/` 由 55 项增至 **257** 项。

### H.3 确认词的唯一机械来源（§3 步骤 4，只读）

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --validate-completion \
  --runtime runtime \
  --run-id p1-m3-body-001-arm-a-trial-2 \
  --tracker-exit-code 0 \
  --tracker-final-json "$FINAL"
```

（`$FINAL` = 上面 stdout 最后一行 JSON 原文，由
`tail -n 1` 取得，未人工改写。）

**stdout 逐字：`TRACKER_AUTO_COMPLETE_CONFIRMED`；退出码 `0`。**
该命令只读、不写文件、不调用 `finalize_run`。确认词由此产生，非人工复述；
在**请用户退出 Play 之前**执行。

### H.4 用户退出后的 Console 报告

在 §H.3 的确认词产生之后，Implementation 请用户退出 Play；用户逐字报告：
「**已经退出，没有报错**」。即 Console 无报错。

## I. §3 步骤 5 绑定分析 —— **fail-closed**，trial 不计入

### I.1 命令与逐字输出

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-a-trial-2
```

**退出码 `2`**；stdout 为空；stderr 逐字：

```text
ANALYSIS_FAIL_CLOSED:trial_invalid_no_single_loop:769.393
```

对应 `tools/analyze_m3_body.py:1034-1038` 的整圈定义域硬门：

```python
final_mileage = max(unwrapped)
if final_mileage < perimeter or final_mileage >= 2.0 * perimeter:
    raise AnalysisError(f"trial_invalid_no_single_loop:{final_mileage:.3f}")
```

周长 `P = 212.9706 m`，`2P = 425.9412 m`；实测 `final_mileage = 769.393 m`
**≥ 2P**，即**多于两圈**（不是"不足一圈"）。按 §1「整圈定义域」与 §5
「绑定工具 fail-closed」，**trial 不以任何形式计入，现场保留，回
Acceptance 归因**。

**该门之前的检查全部通过**（它们在代码里都排在 1034 行之前）：run 绑定与
run_id/manifest schema、scenario 与哈希、arm policy↔planner 三层身份、
tracker 身份与双模型 SHA、re-anchor 身份、condition/track、地平面、初始框、
truth 逐条 `scenario_id` 与逐帧 capture 绑定（≤1e-9 s）、run-bound 输入
SHA-256、`compute_stage` 恰一条 init（`frame_id` 等于 manifest `init.frame_id`）
与其余全部 update、decision/catch-up 分类且至少一条 decision
（`no_decision_update_frame` 未触发）、`truth_off_route`（未触发，目标全程
在路线容差内）、`trial_not_started_at_route_zero`（未触发，起点在 route 零点）。
**失败点唯一，就是整圈定义域。**

### I.2 现场保全清点（零删除、零覆盖、零移动、零重跑）

分析器在硬门之前已按设计把五类原始字节 create-once 收进 run 目录，随后
fail-closed 退出，**`m3_body_analysis.json` 不存在**。run 目录现有 **10 份
文件**（下表为保全记录，SHA-256 取前 16 位）：

| 文件 | 字节 | SHA-256 |
|---|---|---|
| `frames.jsonl` | 993748 | `a7939b7ce0a54a52…` |
| `manifest.json` | 7858 | `d9774905aab324ac…` |
| `metrics.final.json` | 1885 | `ad424dd0d1fe3be5…` |
| `summary.json` | 2442 | `12d05ec0e87e0467…` |
| `m3_body_truth.jsonl` | 1967851 | `6f3e5238ef005725…` |
| `scenario.json` | 3257 | `f9c9205249aacf74…` |
| `margin.json` | 6624 | `c72c940736da9bb1…` |
| `body_config.json` | 3045 | `3d1c4b54d1525205…` |
| `reanchor_config.json` | 3444 | `593734d67ada73a0…` |
| `tracker_model_spec.json` | 1956 | `43c81ad9128cfb78…` |

`scenario.json`/`margin.json`/`reanchor_config.json`/`body_config.json` 的
SHA-256 与 §1、§D 钉住值逐字相等（`f9c92052…`、`c72c9407…`、`593734d6…`、
`3d1c4b54…`），证明 run-bound 输入就是冻结件。

共享现场（**原地保留，未移动、未改名**）：`m3_body_truth.jsonl` 1914 行
`6f3e5238…`、`metrics.json` 61 行 `854271a0…`、`body_command.json` 10 行
`259ba716…`、`gimbal_command.json` 15 行 `d17120c8…`、
`tracking_observation.json` 18 行 `20027c52…`、`frames/` **257** 项、
`scenario_config.json` 仍不存在。

**A1 现场一字节未动**：正式 run 目录仍 **11** 份文件，post-run 归档仍 **6**
项，全程只读。

### I.3 归因材料（**标注为诊断**，非指标、不进门、不作任何判据）

以下量只用纯运动学（相邻 truth 记录的世界系弦长与仿真时间差），**不做
路线投影、不算可见性、不算任何 H1/H2 或 `C_*` 指标**——对一个已 fail-closed
的 trial 计算指标是被禁止的。

| 事实 | 实测 |
|---|---|
| 目标速度 | **全程恒定 `≈2.0 m/s`**（十分位抽样 `1.9995`–`2.0001`），与冻结协议一致，**场景/plant 无异常** |
| tracker 帧记录跨度 | `sim_t 0.18436971` – `130.38473511`，652 条，`frame_id` 0–651 |
| truth 流跨度 | `sim_t 0.18436971` – **`382.78329468`**，**1914** 条，`frame_id` **0–1913** |
| tracker 结束时刻的路径长度 | `260.120 m` = **`1.2214` 圈** → 若当时结束 Play，落在 `[P, 2P)` **本会有效** |
| 越过 `2P` 的时刻 | `sim_t 213.582`（`frame_id 1067`），即 tracker 退出后仅 **`83.197 s`** 仿真时间 |
| Play 实际结束 | `sim_t 382.783` → `3.5884` 圈 → 触发本门 |

**机制（实现角色的归因主张，裁定权在接受角色）**：
`truth_records = _read_truth(...)`（`analyze_m3_body.py:891`）读取**整份**
truth 流且**不按 tracker 窗口过滤**，而 `runtime/m3_body_truth.jsonl` 由
Unity 在**整个 Play 期间**逐帧写入（每次 Play 截断重写）。因此整圈定义域
硬门衡量的是**整个 Play 的里程**，而冻结的 `--planned-duration-s 130.0`
watchdog 只约束 **tracker**，不约束 **Play**。§3 步骤 4（round 29 §C.3
为修 attempt 3 早退而设）**要求**用户在 tracker 退出后继续保持 Play，直到
Implementation 跑完 `--validate-completion` 并明确请其退出；而冻结合同里
**没有任何条款限定这段 post-tracker 停留时长**。在 `2.0 m/s` 下该预算只有
`(2P − 260.120)/2.0 ≈ 83.2 s` 仿真时间。本轮该段耗时约 `252 s`
（tracker 退出 → 记录/校验/通知 → 用户退出），因而越界。

**实现角色自身的耗时占比（如实披露，供接受角色权衡"缺陷 vs 操作节奏"）**：
tracker 退出后本角色的动作顺序是「读 run 记录 → 跑 `--validate-completion`
→ 把 §H 写进证据 → 通知用户退出」。**把 §H 落盘放在通知用户之前是本角色的
选择**，操作单未要求该顺序（它只要求确认词在请用户退出之前由 validator
产生）。若改为「validator 通过即刻请用户退出、事后再写 §H」，post-tracker
停留会显著缩短。因此本轮越界既有**协议不设上限**的成分，也有**本角色顺序
选择**的成分，二者的权重由接受角色裁定；但即便最快的人工顺序也仍受
`83.197 s` 这一**固定且未在合同中写明**的预算约束，缺陷本身不因此消失。

**A1 为何未撞上**：A1 通过了同一硬门，故其 `final_mileage ∈ [P, 2P)`；
§N.1 记录 A1 的 truth 为 **1027 行**，按本轮实测 `≈0.2 s/条` 折合
`≈205 s` 仿真时间、`≈410 m ≈ 1.93 圈`——**距 2P 仅剩约 15 s 余量**。
（该推算只用已记录的行数与本轮 cadence，**未读取 A1 的任何字节**。）
即：这是一个**既存的协议交互缺陷**，A1 侥幸擦边通过，trial 2 撞上。

### I.4 实现角色已做与未做

- **未做**：不 `--finalize`、不重跑分析器、不重进 Play、不移动/改名/删除
  任何字节、不调参、不改阈值/窗口/载体、不改操作单（BC-BODY1-21/-22）、
  不自行命名终态、不申请新 GO、不做 compare。
- **已做**：按 §3 步骤 1–5 逐条执行并落盘；fail-closed 后立即停止并保全，
  只补充**只读**归因材料。
- **已消耗**：采集 ID `p1-m3-body-001-arm-a-trial-2` 已被 `RunLogger`
  create-once 创建并消耗；本轮**一次性 GO 已消耗**。按 §5 post-tracker 段
  的先例，下一次采集须由接受角色另行冻结新的采集 ID，并需用户新的逐字 GO。

### I.5 交回接受角色的裁定项（实现角色不自行取舍）

1. **具名终态**：本次不匹配 §5 已有的三个具名终态（暂停窗越界、tracker
   启动失败、post-tracker 早退——本轮 tracker 自然完成、Console 无报错），
   落在 §5「绑定工具 fail-closed」的通用条款下。终态名由接受角色裁定。
2. **现场保全形式**：是否按 `*-void-…-hold` 命名规律移动、如何命名，由
   接受角色裁定后再由实现角色执行；在此之前原地不动。
3. **协议缺陷的处置**：§3 步骤 4 的强制 post-tracker 停留与 §1 整圈定义域
   `< 2P` 硬门之间只有 `≈83 s` 预算，这是**冻结合同自身的交互缺陷**，
   不是操作失误、不是场景/plant 缺陷（速度全程 `2.0 m/s`）。修法（例如把
   truth 按 tracker 窗口截断、或在 tracker 完成后立刻停止 truth 写入、或
   改 watchdog/定义域）**全部涉及冻结值或代码**，超出实现角色权限，也受
   BC-BODY1-15 (d) 反调参纪律约束——**必须由接受角色裁定后另行授权**。

## J. 边界声明（分批声明）

**§A–§E（Play 前只读批次）**：零 Play、零采集 ID 创建/消耗、零 `runtime/`
写入、零代码/测试/config/scenario/model 改动；未修改操作单、提案、正式
设计、`docs/reviews/`、`docs/unity-test-log.md` 与 `docs/authorizations.md`。

**§G–§I（Play 批次）**：

- 本批**消耗了**用户授权的**唯一一次** Play 与采集 ID
  `p1-m3-body-001-arm-a-trial-2`；其余 8 次 Play、任何重试、重进、调参
  **仍未授权**，本批也**不申请**。
- 本批**零阈值、零指标、零 CLI 参数、零协议、零代码/测试/config/scenario/
  model 改动**；tracker CLI 除 revision 12 冻结的 `--run-id` 外 18 个参数
  逐字未改（解释器拼写的绝对/相对差异见 §G.5 披露）。
- 本批**未对 A1 现场做任何写操作**：正式 run 目录 11 份、post-run 归档
  6 项，全程只读。
- 本批**未产生任何 `C_*` / H1 / H2 指标**：分析器 fail-closed，
  `m3_body_analysis.json` 不存在；§I.3 只有纯运动学的诊断量。
- 本批**未修改**操作单（BC-BODY1-21）、提案、正式设计、`docs/reviews/`、
  `docs/unity-test-log.md`、`docs/authorizations.md`。

**§K（现场保全批次）**：声明见 §K.7。

---

# K. §2.8 attempt-1 void 现场保全（BC-BODY1-28 第 5 步）

执行时间 2026-08-13，实现角色。合同来自操作单 revision 13 §2.8（= 接受轮 42
§C 冻结的七组 source→destination）与 BC-BODY1-33 门排练。**零 Play、零采集 ID
创建/消耗、零代码/测试/config/scenario/model 改动、零操作单改动**；被保全的
十个文件一字节未动。执行前 `git rev-parse HEAD` = `c968f1ca9625e7b9d167115fe40a67654f6da89a`，
`git status --porcelain` 为空（`runtime/*` 在 `.gitignore` 内，故本节的移动
零 Git 改动）。

## K.1 零覆盖前提（移动前实测）

七个 destination 在移动前**逐项经 `Path.exists()` 确认不存在**，且脚本在每次
`os.rename` 之前**再查一次**该 destination（`dst.exists() or dst.is_symlink()`
即中止）；`os.rename` 只在同一文件系统内改名，不复制、不删除、不截断。移动后
逐项确认 source 路径已不存在（`runtime/frames/` 除外，见 §K.2 第 8 行）。

## K.2 七组移动：移动前 = 移动后（计数/行数/字节/SHA-256）

目录用**目录聚合 SHA-256**（口径见 §B.3：`shasum -a 256 *` 逐行排序后再取
SHA-256，只依赖目录内相对路径，故对整目录移动稳定）。

| # | Source → Destination | 前 = 后 |
|---|---|---|
| 1 | `runs/p1-m3-body-001-arm-a-trial-2/` → `runs/p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold/` | **10 个文件**；聚合 `b290ab264f4b6e51d6805aa3dcbdcd10f206afca2863791441a4a955d36d8dfd` ✓；文件名集合逐字相同 ✓ |
| 2 | `frames/` → `frames.arm-a-trial-2-void-attempt-1-hold/` | **257 项**（128 帧 ×2 + `latest.json`）；聚合 `bc4bdb5ad9d92c7074f04dd3a9c0bd521832cd548b06a6c020991b1d16822229` ✓ |
| 3 | `m3_body_truth.jsonl` → `m3_body_truth.arm-a-trial-2-void-attempt-1-hold.jsonl` | **1914 行 / 1967851 B**；`6f3e5238ef0057253f1228ec4aa9fdd53c2557dd00bc01d2df1782e90635f095` ✓ |
| 4 | `metrics.json` → `metrics.arm-a-trial-2-void-attempt-1-hold.json` | **61 行 / 2104 B**；`854271a029292b14b95d77ffdf63f6de52efd252887878c85dedee216ac3fa3a` ✓ |
| 5 | `body_command.json` → `body_command.arm-a-trial-2-void-attempt-1-hold.json` | **10 行 / 208 B**；`259ba7167c6e8564f0ce2553f056c51f519bc37bde0875bf5eb1634b657a10b1` ✓ |
| 6 | `gimbal_command.json` → `gimbal_command.arm-a-trial-2-void-attempt-1-hold.json` | **15 行 / 339 B**；`d17120c80a2109d8a606f805d22741b5f0df20c105ba258e8c39a41c8a4a4dd5` ✓ |
| 7 | `tracking_observation.json` → `tracking_observation.arm-a-trial-2-void-attempt-1-hold.json` | **18 行 / 456 B**；`20027c5251c313ccb76ca7f8877d5bf94729f2c0dc95b5b450780aed54d97e0c` ✓ |

七项的移动前值与 §I.2 的保全清点（run 目录 10 份、truth 1914 行 `6f3e5238…`、
metrics `854271a0…`、`259ba716…`、`d17120c8…`、`20027c52…`、frames 257 项）
**逐项相等**，即 fail-closed 之后到本次移动之前现场未被动过。

移动后**只新建空 `runtime/frames/`**（实测 0 项），未预建任何 run 目录：
`runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2/` 实测**不存在**。
`runtime/runs/` 直接子目录数 28 → 28（`-arm-a-trial-2` 改名为
`-arm-a-trial-2-void-attempt-1-hold`，无增无减）。六个 shared 文件
（`body_command.json`、`gimbal_command.json`、`tracking_observation.json`、
`metrics.json`、`m3_body_truth.jsonl`、`scenario_config.json`）移动后**均不
存在**。全仓 `m3_body_analysis.json` 命中集合移动前后相同，仍只有 A1 一处。

## K.3 hold 的十文件精确集合与隐藏文件核对（N27，移动后立即执行）

`runs/p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold/` 实测 **10 个条目、
10 个常规文件、0 个子目录、0 个隐藏条目**；文件名集合与 §2.8 表列的十个
**逐字相等**（也就是 `_check_a2_predecessor_hold` 的判等对象）：

| 文件 | 字节 | SHA-256 |
|---|---|---|
| `body_config.json` | 3045 | `3d1c4b54d1525205…` |
| `frames.jsonl` | 993748 | `a7939b7ce0a54a52…` |
| `m3_body_truth.jsonl` | 1967851 | `6f3e5238ef005725…` |
| `manifest.json` | 7858 | `d9774905aab324ac…` |
| `margin.json` | 6624 | `c72c940736da9bb1…` |
| `metrics.final.json` | 1885 | `ad424dd0d1fe3be5…` |
| `reanchor_config.json` | 3444 | `593734d67ada73a0…` |
| `scenario.json` | 3257 | `f9c9205249aacf74…` |
| `summary.json` | 2442 | `12d05ec0e87e0467…` |
| `tracker_model_spec.json` | 1956 | `43c81ad9128cfb78…` |

三个钉住 SHA-256 移动后**逐字相等**（字节不随路径变）：

- `frames.jsonl` = `a7939b7ce0a54a52487859b3ed1e12d3f0b6526759ab5e77925c49980309fc54`（993748 B）
- `manifest.json` = `d9774905aab324acf05c7616d0bf9e8a0ccf8f10c3855dd5c8c4ff1f9ea4a50c`（7858 B）
- `m3_body_truth.jsonl` = `6f3e5238ef0057253f1228ec4aa9fdd53c2557dd00bc01d2df1782e90635f095`（1967851 B）

**未删除任何隐藏文件**——本次核对时 hold 内一个都没有。**风险不是理论的**：
本机 Finder 确实在产 `.DS_Store`，`find runtime -name .DS_Store` 现有三处
（`runtime/.DS_Store`、`runtime/p1-scene-004-scouting/.DS_Store`、
`runtime/p1-scene-004-scouting/p1-scene-004-scout-4/.DS_Store`），只是都不在
hold 内。故 §2.7 第 7 项在发令前的**再查一次**仍然必要，本节不替代它。

## K.4 A1 现场与四处旧 hold 不变（只读证明）

移动前后两份全量快照逐字段比对，下列对象**完全相等**（含每个文件的字节数与
SHA-256）：

| 对象 | 实测 |
|---|---|
| A1 正式 run 目录 | **11 份文件**，聚合 `7c3af28e3adbc3bdd72cc54e24002fd1c3e5eaa8628e76ba364442df093cda79` = §N.1 记录值 ✓ |
| A1 post-run 归档 | **6 项**，`frames/` **257** 项聚合 `ea9ba0505e1be7e0ce17c5420e5a13c96a3a756c541ff1293bf78ed8018b2fb3` = §N.1 记录值 ✓；其余五个文件行数/字节/SHA-256 全等 ✓ |
| A1 predecessor hold（attempt-3 run） | 恰 **2 个文件** `frames.jsonl`/`manifest.json`，前后相等 ✓ |
| 1b / attempt-1 / attempt-2 / attempt-3 四处 frames hold | **257 / 93 / 109 / 257** 项，四个聚合 SHA-256 前后相等 ✓ |
| 上述四处 hold 的 14 个单文件（1b 五个、attempt-1 两个、attempt-2 两个、attempt-3 五个） | **14/14** 行数/字节/SHA-256 前后相等 ✓ |
| 八个活动标记（四个 release pointer + 四个 scouting/qualification 标记） | 前后均**不存在** ✓ |

**移动后 A1 `--verify` 复跑**（只读，写盘前返回）：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify \
  --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
```

退出码 **0**，stdout 与操作单 §2.7 写死的期望行经 `cmp` **逐字节相同**
（`BYTE_IDENTICAL=YES`）：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
```

## K.5 BC-BODY1-33 门排练（真实 hold，只读、零 ID、零写盘）

**(1) 直接调用 `_check_a2_predecessor_hold`（本条即 BC-BODY1-33 的执行）**：

```bash
.venv-yoloe/bin/python -c "
import sys; from pathlib import Path
sys.path.insert(0, 'tools')
import analyze_m3_body as analyze
print(analyze.A2_PREDECESSOR_HOLD_DIR_NAME)
print(repr(analyze._check_a2_predecessor_hold(Path('runtime'))))
"
```

逐字输出（退出码 0）：

```
p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold
None
```

即真实 hold 上**十文件集合判等 + 三个 SHA-256 判等全部通过**（该函数只在失败时
抛 `AnalysisError`，通过即返回 `None`）。同一次调用另打印了三项身份确认，与操作
单 §1 的 A2 钉住行逐字相符：`canonical_trial_id()` = `p1-m3-body-001-arm-a-trial-2`、
`_expected_policy()` = `hold`、`expected_acquisition_ids('a')[1]` =
`p1-m3-body-001-arm-a-trial-2-attempt-2`。

**(2) BC-BODY1-33 括注里的 CLI 变体（实测与括注描述不符，交回接受角色，见 §K.6）**：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-a-trial-2-attempt-2
```

逐字 stderr（退出码 2）：

```
ANALYSIS_FAIL_CLOSED:missing_run_directory:~/TetheredDroneTracking/runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2
```

该命令**零写盘**（跑完复查：`runtime/frames/` 仍 0 项、
`runs/…-attempt-2/` 仍不存在、hold 仍 10 份文件）。

**(3) 补充负向探针（非合同要求，只为证明本次通过不是空转）**：在 scratchpad
里造一个 shadow runtime 根，其 `runs/<hold 名>/` 内是指向真实十个文件的**符号
链接**（`entry.is_file()` 跟随符号链接，故门读到的就是真实字节；**真实 hold
零写入**）。对照组 `_check_a2_predecessor_hold(shadow)` 返回 `None` 通过；随后
只在 shadow 里落一个 `.DS_Store`，同一调用即 fail closed：

```
AnalysisError: a2_predecessor_hold_file_set_mismatch:['.DS_Store', 'body_config.json', 'frames…
```

失败名 `a2_predecessor_hold_file_set_mismatch` 与 §2.7 第 7 项、N27 所述一致。

## K.6 测试记录与交回接受角色的事项

**测试（BC-BODY1-34 口径，钉住解释器 `.venv-yoloe/bin/python`）**——本批零
代码/测试字节改动，跑测试是为了证明移动没有改变依赖真实 `runtime/` 字节的用例
（`ArchivedRunLoopDomainTests` 读 A1 run 与 A1 predecessor hold）：

| 命令 | 结果 |
|---|---|
| `.venv-yoloe/bin/python -m unittest discover -s tests -p "test_analyze_m3_body.py"` | **Ran 67 — OK**（67/67） |
| `.venv-yoloe/bin/python -m unittest discover -s tests` | **Ran 535 — failures=1, errors=1, skipped=1** |

535 的两条不通过仍是既有的 `test_trackers…test_pinned_opencv_csrt_initializes_and_updates`
与 `test_track_loop…test_cli_runs_pinned_csrt_to_a_versioned_summary`（`.venv-yoloe`
的 cv2 缺 opencv-contrib CSRT 组件，`P1-TRACK-001` 旧基线，不在采集/控制/指标
路径上），与接受轮 44 §D.4 记录**同一对**；**零新增失败**。

**交回接受角色（实现角色不自行改文字）**：

1. **BC-BODY1-33 括注与代码实际顺序不符**。括注写「或跑
   `--run-id …-attempt-2` 观察它**越过前驱门后**停在 `missing_run_directory`」，
   操作单 §2.8 同句照抄。实测顺序相反：`analyze_trial` 先查 run 目录
   （`missing_run_directory`）**再**按 `run_id` 触发 `_check_a2_predecessor_hold`，
   故该 CLI 变体**根本没走到前驱门**，不能充当排练。本角色按「或」的第一支执行
   （直接调用），BC-BODY1-33 的实体要求已满足；建议接受角色在下一次修订里删掉
   或改写该括注，以免后来者以为跑一次 CLI 就算排练过。**本角色未改操作单
   （BC-BODY1-21/-22）。**
2. **§2.7 八项本批未执行**，也不得视作已放电：它是发令前的核对（§2.0 四步顺序
   之后、GO 消耗之前）。本节的 §K.2–§K.4 与 §2.7 第 1/2/3/4/5/6/7/8 项在**内容**
   上多有重叠且当前全部处于期望状态，但**时点不同**——Play 前必须由实现角色按
   §2.7 重跑一遍并落盘。
3. **本批未产生 Unity 用例**（零 `Assets/`、零 `ProjectSettings/`、零 `config/`
   字节，无 C# 面）。这**不是** `UNITY_NA` 申领。

## K.7 §K 批次边界声明

- **零 Play、零采集 ID 创建/消耗**；`…-arm-a-trial-2-attempt-2` 的 run 目录未
  预建，其 GO（§G3）仍未答复，本批也**不申请**。
- **零删除、零覆盖、零截断、零分析**：只有 7 次 `os.rename` 与 1 次
  `mkdir runtime/frames`；被保全的十个文件与四处旧 hold 一字节未动；未对任何
  void 工件计算指标，`m3_body_analysis.json` 仍只存在于 A1 run 目录。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单
  （BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`、`docs/unity-test-log.md`
  与 `docs/authorizations.md`。
- 本批写入仅两个路径：本证据文件与 `docs/current-status.md`。
- 复核范围（供下一轮复核）：本节 §K.1–§K.6 的 `runtime/` 现场事实
  （可由 `runtime/` 直接复算，全部是未跟踪生成物）、门排练的三条命令与逐字输出、
  以及 §K.6 第 1 条的顺序事实（`analyze_m3_body.analyze_trial` 中
  `missing_run_directory` 与 `_check_a2_predecessor_hold` 的先后）。

---

# L. §2.0 step (b) 报告与 §2.7 Play 前只读核对（A2 attempt-2，操作单 revision 13）

执行时间 2026-08-13，实现角色。交接来源：Acceptance 在用户 GO 入账
（commit `12cedf5`）后发出的 §2.0 (b) + §2.7 执行位。**零 Play、零采集 ID
创建/消耗、零 `runtime/` 写入、零 `controller/`/`Assets/`/`config/`/`tools/`/
`tests/` 改动。** 本批不进入 Play、不启动 tracker；§2.0 (c)（接受角色写
`docs/unity-test-log.md`）与 (d)（发令时刻唯一未提交差异）不属本批。

## L.1 HEAD 与工作树状态（测量时点）

```text
$ git rev-parse HEAD
12cedf56bd27a92db8af56fb080348c65a90e592

$ git status --porcelain
（空输出）
```

本批全部命令**执行前与执行后**的 `git status --porcelain` 均为空（只读性
证明见 §L.5）。测量时点 HEAD **不是**发令时点 HEAD，见 §L.6 第 2 条。

## L.2 基线 delta 的路径归因（`<BASE>` 运行时解析）

按 revision 13 的 §2.0 (b)（N26 闭合，COORD-007 R7「可派生标识禁手写」），
基线不手写，执行时现取：

```bash
$ grep -m1 '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md
passed_candidate: 07bb8a47a9e41581c1450a7b0335e501ffdaaec9
```

`git diff --name-only 07bb8a47a9e41581c1450a7b0335e501ffdaaec9..HEAD` =
**6 个路径**，区间共 3 个 commit（`9e1cbb5`、`e488411`、`12cedf5`）。逐条归因：

| # | 路径 | 归属 | PLAY_GOVERNING |
|---|---|---|---|
| 1 | `docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md` | 接受轮 45（消费 Review round 7 + 发出 revision 13） | 否 |
| 2 | `docs/reviews/P1-M3-BODY-001.md` | Review round 7 记录与 `passed_candidate` 机读行 | 否 |
| 3 | `docs/evidence/P1-M3-BODY-001-1c-preflight.md` | **操作单 revision 13**（接受轮 45 §B 撰写） | **是** |
| 4 | `docs/evidence/P1-M3-BODY-001-arm-a-trial-2.md` | 本文件 §K（第 5 步现场保全证据） | 否 |
| 5 | `docs/authorizations.md` | 用户 §G3 GO 入账（接受角色代录，`12cedf5`） | 否 |
| 6 | `docs/current-status.md` | 状态板（第 5 步、失效文字更正、GO 后的门与交接） | 否 |

**测量侧逐字节相同**（§2.0 (b) 注的 inert 前提，本轮以最强形式成立）：

```bash
$ git diff --name-only 07bb8a4..HEAD -- controller/ Assets/ config/ \
    ProjectSettings/ Packages/packages-lock.json tools/ tests/
（空输出）
```

即自 Review round 7 通过的候选起，`controller/`、`Assets/`、`config/`、
`ProjectSettings/`、`Packages/packages-lock.json`、`tools/`（含
`analyze_m3_body.py`、`preflight_reanchor_env.py`）与 `tests/` **一个字节
都没动**。上一轮 §F 判为 inert 的那六条 COORD-007 工具/测试路径已经落在
候选之内，本轮 delta 里**不再出现**。

**PLAY_GOVERNING 子集（读法 1，接受轮 40 裁定：操作单文件入集）= 恰 1 条**，
即第 3 条操作单 revision 13 本身，也就是本批正在执行的指令。**该条的独立
复核状态见 §L.6 第 1 条（交回接受角色，本角色不自行判定）。**

## L.3 §3 步骤 0 环境预检

命令（§1 钉住的唯一形式）：

```bash
.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json
```

**退出码 `0`**，stdout `status` = `"PASS"`，`side_effect_identity.unchanged`
= `true`。stderr 有与上一轮同类的依赖噪声（OpenCV `setPreferableTarget` 两行
WARN、`tifffile` 缺失提示、DINOv2 三条 xFormers `UserWarning`），不影响退出码
与 JSON；如实记录。完整 stdout JSON（逐字）：

```json
{
  "constructors": {
    "dinov2_embedder": "controller.reanchor_models.DinoV2Embedder",
    "nanotrack_tracker": "controller.trackers.NanoTrackV2Tracker",
    "yoloe_proposer": "controller.reanchor_models.YoloeProposer"
  },
  "interpreter": {
    "executable": "~/TetheredDroneTracking/.venv-yoloe/bin/python",
    "prefix": "~/TetheredDroneTracking/.venv-yoloe",
    "python_version": "3.12.13"
  },
  "mode": "reanchor-preflight",
  "nanotrack": {
    "backend": "opencv-dnn-default/cpu",
    "model_sha256": {
      "backbone": "530bdd0cd00f19afab79a863e71ba71e3312395a5dc9151af675082bdaaa2fc4",
      "neckhead": "0d8c0637be849f092cc7236cae02e55c8b9455ebe37ba50601d6115db4247cd9"
    },
    "name": "nanotrack-v2",
    "opencv_package_pin": "opencv-contrib-python==5.0.0.93",
    "opencv_version": "5.0.0",
    "preprocessing_id": "opencv-tracker-nano-5.0.0-default-v1"
  },
  "packages": {
    "cv2": {
      "pin": "5.0.0",
      "pin_source": "nanotrack spec opencv.tested_version",
      "raw": "5.0.0"
    },
    "torch": {
      "pin": "2.13.0",
      "pin_source": "reanchor config runtime.torch_pin",
      "raw": "2.13.0"
    },
    "torchvision": {
      "pin": "0.28.0",
      "pin_source": "reanchor config runtime.torchvision_pin",
      "raw": "0.28.0"
    },
    "ultralytics": {
      "pin": "8.4.104",
      "pin_source": "reanchor config runtime.ultralytics_pin",
      "raw": "8.4.104"
    }
  },
  "reanchor_config": {
    "carrier": "minimal-triple-gated-re-anchor",
    "device": "cpu",
    "path": "config/detector-reanchor.models.json",
    "schema_version": "tethered-detector-reanchor/v1",
    "sha256": "593734d67ada73a0304d67d27c6ae536be616d2180f744336b85ff6e0ac706d2"
  },
  "side_effect_identity": {
    "after": {
      "guarded_files": {
        "runtime/body_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/gimbal_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/metrics.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/tracking_observation.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        }
      },
      "run_directories": [
        "p1-detect-001-qual-1",
        "p1-detect-001-qual-2",
        "p1-detect-001-qual-3",
        "p1-m3-body-001-arm-a-trial-1-attempt-4",
        "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold",
        "p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold",
        "p1-track-follow",
        "p1-track-follow-attempt1",
        "p1-track-nadir",
        "p1-track-occlusion",
        "rate20-calib",
        "rate20-follow-r1",
        "rate20-follow-r2",
        "rate20-follow-r3",
        "rate20-nadir-r1",
        "rate20-nadir-r2",
        "rate20-nadir-r3",
        "rate5-calib",
        "rate5-follow-r1",
        "rate5-follow-r2",
        "rate5-follow-r3",
        "rate5-nadir-r1",
        "rate5-nadir-r2",
        "rate5-nadir-r3",
        "rs2-pilot",
        "rs2-r20-follow-1",
        "rs2-r20-follow-2",
        "rs2-r20-follow-3"
      ]
    },
    "before": {
      "guarded_files": {
        "runtime/body_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/gimbal_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/metrics.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/tracking_observation.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        }
      },
      "run_directories": [
        "p1-detect-001-qual-1",
        "p1-detect-001-qual-2",
        "p1-detect-001-qual-3",
        "p1-m3-body-001-arm-a-trial-1-attempt-4",
        "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold",
        "p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold",
        "p1-track-follow",
        "p1-track-follow-attempt1",
        "p1-track-nadir",
        "p1-track-occlusion",
        "rate20-calib",
        "rate20-follow-r1",
        "rate20-follow-r2",
        "rate20-follow-r3",
        "rate20-nadir-r1",
        "rate20-nadir-r2",
        "rate20-nadir-r3",
        "rate5-calib",
        "rate5-follow-r1",
        "rate5-follow-r2",
        "rate5-follow-r3",
        "rate5-nadir-r1",
        "rate5-nadir-r2",
        "rate5-nadir-r3",
        "rs2-pilot",
        "rs2-r20-follow-1",
        "rs2-r20-follow-2",
        "rs2-r20-follow-3"
      ]
    },
    "checked": [
      "runtime/runs direct child directory names",
      "runtime/body_command.json present/size/sha256",
      "runtime/gimbal_command.json present/size/sha256",
      "runtime/tracking_observation.json present/size/sha256",
      "runtime/metrics.json present/size/sha256"
    ],
    "unchanged": true
  },
  "status": "PASS"
}
```

`side_effect_identity` 的 `run_directories` 前后两份完全相同，且逐字反映
第 5 步之后的现实：`p1-m3-body-001-arm-a-trial-2` 已不在其中，
`…-arm-a-trial-2-void-attempt-1-hold` 在其中，`…-arm-a-trial-2-attempt-2`
**不存在**。

## L.4 §3 步骤 0′ 第 1 步：解释器逐字值落盘

取自 §L.3 预检 stdout JSON 的 `interpreter.executable`：

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python
```

与 §1 冻结的唯一合法入口 `.venv-yoloe/bin/python -m controller.track_loop`
的解释器部分一致（前者是后者的绝对路径形式，`prefix` =
`~/TetheredDroneTracking/.venv-yoloe`，`python_version` `3.12.13`）。
**步骤 0′ 第 2 步尚未执行**（本批不启动 tracker），须在获授权的那次 Play 中
执行并追记。

## L.5 §2.7 八项 Play 前只读核对：**54 条机械核对，54 PASS / 0 FAIL**

期望值一律取自 §2.5 第 4–7 项原表、`docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md`
§B/§F.1/§H.1/§I.1/§N.1 与操作单 §2.8 的十文件集合与三个钉住 SHA；本节不重抄
哈希做二次转写。

| §2.7 项 | 核对内容 | 结果 |
|---|---|---|
| 1 | 六个 shared 文件（`body_command.json`/`gimbal_command.json`/`tracking_observation.json`/`metrics.json`/`m3_body_truth.jsonl`/`scenario_config.json`） | 均**不存在** ✓（6/6） |
| 2 | `runtime/frames/` 存在且为空 | 存在、**0 项** ✓（2/2） |
| 3 | 1b / attempt-1 / attempt-2 / attempt-3 四处旧 hold | 帧计数 **257 / 93 / 109 / 257** ✓；1b 五个 SHA ✓；attempt-1 truth 46 行 + SHA、metrics SHA ✓；attempt-2 truth 54 行 + SHA、metrics SHA ✓；attempt-3 run hold 恰 2 文件（755/207 行，两 SHA）+ truth 627 行 + metrics + 三个发布 hold ✓（21/21） |
| 4 | A1 正式 run 目录恰 11 份 + 只读 `--verify` | **11 份**、聚合 `7c3af28e…cda79` = §N.1 值 ✓；`--verify` 见下 ✓（2/2 + verify） |
| 5 | A1 post-run 归档恰 6 项 | 6 项名称相符 ✓；`frames/` **257** 项聚合 `ea9ba050…2fb3` ✓；其余五个文件行数/字节/SHA 全等 ✓（8/8） |
| 6 | 无 release pointer、无 scouting/qualification 标记 | 八个具名标记**均不存在** ✓（8/8） |
| 7 | **attempt-1 void hold（N27 前移）** | 目录存在；直接文件名集合**恰为 §2.8 十个** ✓；条目总数 10、**零隐藏文件/零子目录** ✓；三个钉住 SHA-256 与字节数逐字相等 ✓（6/6） |
| 8 | **attempt-2 create-once 前置** | `runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2/` **不存在** ✓（1/1） |

第 4 项的只读复算：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify \
  --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
```

**退出码 `0`**，stderr 为空，stdout 与操作单 §2.7 写死的期望行经 `cmp`
**逐字节相同**（`BYTE_IDENTICAL=YES`）：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
```

**只读性证明**：本批只执行 `git` 只读查询、预检、`--verify` 与核对脚本
（只做 `open(..., 'rb')` 与 `stat`，中间文件全部落在会话 scratchpad）；
无 `mv`/`rm`/`mkdir`/重定向写入。三条命令跑完后复查：`git status --porcelain`
仍为空、`runtime/frames/` 仍 0 项、`…-attempt-2/` 仍不存在、hold 仍 10 份文件、
预检自身 `side_effect_identity.unchanged = true`。

## L.6 交回接受角色 / 未验证项

1. **本轮 PLAY_GOVERNING 恰 1 条 = 操作单 revision 13 自身，其独立复核仍欠。**
   Review round 7 覆盖到 revision 12 与轮 35/39–42 的操作单改动；revision 13 由
   接受轮 45 在 round 7 **之后**撰写，按 BC-BODY1-28 的既定顺序（第 3 步复核 →
   第 4 步 revision 13）**必然**未经复核。上一轮同形情形由接受轮 40 单独定名为
   `RUNBOOK_DELTA_AUTHORED_UNDER_GO_NO_SEMANTIC_CHANGE_REVIEW_DEBT_REGISTERED`
   （不阻断 Play，复核债挂下一轮）。**本角色不把该裁定自行外推到 revision 13**，
   如实报告，处置权在接受角色；(c) 记录写入前需要一句明确 disposition。
2. **测量时点 HEAD ≠ 发令时点 HEAD**（§A.6 同一先例）：§2.0 (d) 要求发令时刻
   工作树只允许 `docs/unity-test-log.md` 一份未提交差异，故本批（本节 + 状态板）
   必须在 (c) 之前提交，HEAD 随之前移。**(c) 的权威值必须由接受角色在写入时点
   自行运行 `git rev-parse HEAD` 与 `git status --porcelain`**，不得复制 §L.1。
   本批只动两个文档路径（本证据文件、`docs/current-status.md`），两者都**不在**
   PLAY_GOVERNING，提交后测量侧 diff 仍为空、PLAY_GOVERNING 子集仍是同样 1 条。
3. **§K.6 第 1 条仍未处置**：BC-BODY1-33 括注（操作单 §2.8 照抄）称 CLI 变体
   「越过前驱门后停在 `missing_run_directory`」，实测顺序相反。本批顺带发现该
   说法也被抄进状态板交接行的 Progress 栏，已按 AGENTS.md「交接文字必须与现实
   一致」就地更正为实测顺序（只改事实描述，未改任何 verdict/门结论），并在此
   披露；操作单原文**未动**（BC-BODY1-21/-22），仍待接受角色修订。
4. **未验证项**：§3 步骤 0′ 第 2 步（tracker 命令行首解释器逐字相等）、§3 步骤
   1–6 的全部 Play 内动作、§2.7 在**发令时刻**的复查——若 (c) 之后到发令之间
   又出现新提交或任何 `runtime/` 变化，本节结论即失效，须重取。
5. **本批不产生 Unity 用例**，也**不申领** `UNITY_NA`。

---

# M. A2 attempt-2 的 Play 与三个独立硬门（§3 步骤 1–2，本段在**启动 tracker 之前**落盘）

日期 2026-08-13。用户按 §2.0 (c) 记录（`docs/unity-test-log.md`
`PRE_PLAY_RELEASED` 条，HEAD `8dfadb4`）进入 Play **恰一次**。发令时刻的三项
复核由实现角色在用户进 Play 之前实测：

- **§2.0 (d)**：`git diff --name-only` 逐字只有 `docs/unity-test-log.md` ✓
- **§3 步骤 0 预检（命令时刻复跑）**：退出 0、`status=PASS`、
  `side_effect_identity.unchanged=true`，stdout JSON 与 §L.3 记录的那份
  **逐字节相同** ✓
- **§2.7 八项复跑**：**54/54 PASS**（round 46 的提交改变了 HEAD，故按 §L.6
  第 4 条重取，结论不变）✓

## M.1 用户进入 Play 并暂停（口报如实记录，**不作判据**）

用户报告逐字：**「已暂停，我看不见HUD」**——即本轮**没有** HUD 口报时刻。
这不影响门 1：revision 12 的记录型条款明文规定 `reported_sim_t` **不得**取
用户口报的 HUD 时刻，必须由实现角色从**保留帧**机械导出。本轮因此只有磁盘
实测值，不存在可与之矛盾的口报值。

**披露（非缺陷主张，归因权在接受角色）**：本次采集的载体是
`config/scenario.default.json`（§1 钉住，无 runtime override），与带计时 HUD
的 SCENE-004 override 不是同一份场景配置；用户看不到 HUD 是否属预期，由接受
角色裁定。**它不是门，也未被用作任何判据，本轮未因此调整任何值。**

## M.2 门 1 —— 暂停窗口（`2.000000 <= reported_sim_t < 10.000000`）

**导出命令原文**（只读；只解析保留帧的元数据 JSON，不读任何真值文件）：

```bash
.venv-yoloe/bin/python - <<'PYEOF'
import json, pathlib
frames = pathlib.Path("runtime/frames")
records = []
for p in sorted(frames.glob("frame_*.json")):
    d = json.loads(p.read_text())
    records.append((d["frame_id"], d["simulation_time_s"], p.name))
ids = [r[0] for r in records]
print("retained metadata files:", len(records))
print("frame_id range: min =", min(ids), " max =", max(ids),
      " contiguous =", ids == list(range(min(ids), max(ids)+1)))
print("max simulation_time_s = %.6f" % max(r[1] for r in records))
PYEOF
```

**逐字输出**：

```text
retained metadata files: 22
frame_id range: min = 0  max = 21  contiguous = True
max simulation_time_s = 4.384412
min simulation_time_s = 0.183284
  frame 19: 3.9824376106262207  (frame_0000000019.json)
  frame 20: 4.180592060089111  (frame_0000000020.json)
  frame 21: 4.3844122886657715  (frame_0000000021.json)
GATE1 2.000000 <= 4.384412 < 10.000000 -> True
GATE2 lowest retained frame == 0 -> True
```

三项落盘要求逐条满足：

| 要求 | 值 |
|---|---|
| 导出命令原文 | 见上（本节代码块） |
| 保留帧编号范围 | `frame_id` **0–21**，连续，22 份元数据（目录共 45 项 = 22 json + 22 jpg + `latest.json`；`latest.json` 的 `frame_id` = **21**，与最大保留帧一致） |
| 导出的数值 | `reported_sim_t` = **`4.3844122886657715`**（保留帧中最大 `simulation_time_s`，字段由 `SensorFrameWriter` 写入） |

**门 1 PASS**：`2.000000 <= 4.3844122886657715 < 10.000000`，两侧余量分别约
`2.384 s` 与 `5.616 s`。

**披露（COORD-007 §4.1 缺口未消除）**：该值是真实暂停时刻的**下界**——末帧
写盘之后、暂停生效之前的不足一帧时间不可见（本轮相邻帧间隔约 `0.198 s`）。
本轮两侧余量都远大于一帧，故该缺口对本次判定无实际影响；消除它仍需 R10
（未授权、属代码）。

## M.3 门 2 —— 最低保留帧必须恰为 `0`

保留帧 `frame_id` 最小值 = **`0`** ✓（见 §M.2 逐字输出），**门 2 PASS**。

## M.4 门 3 —— 冻结框匹配（用户目检）

导出命令（唯一合法入口；输出落在会话临时目录，**不写仓库、不写 `runtime/`**）：

```bash
.venv-yoloe/bin/python -m controller.track_loop --dump-frame 0 --output <scratch>/a2attempt2_frame0.jpg
```

退出码 0，导出图 **640×480**。叠加的是**已冻结**像素框 `(177, 195, 77, 73)`
（`min_side = 73 px`），未重新框选、未重新估框、未做六位小数化，也未读取
`runtime/m3_body_truth.jsonl` 或任何真值。用户只做**匹配 / 不匹配**目检。

**用户目检结论（逐字）**：「**匹配**」→ **门 3 PASS**。现场未做任何调整。

**三门全部 PASS**，互不覆盖（门 1 `4.3844122886657715` ∈ `[2,10)`、门 2 最低
帧 `0`、门 3 用户目检匹配），故按 §3 步骤 2 末段在**保持暂停**下启动 tracker。

---

# N. tracker、完成握手与绑定分析（§3 步骤 2 末段–步骤 6）

## N.1 §3 步骤 0′ 第 2 步 —— 解释器绑定与实际命令行（**启动前**核对）

**实际执行的完整命令行原文**（工作目录 = 仓库根）：

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
  --run-id p1-m3-body-001-arm-a-trial-2-attempt-2 \
  --init-frame 0 \
  --init-box 0.2765625 0.40625 0.1203125 0.15208333333333332 \
  --planned-duration-s 130.0 \
  --maximum-ground-range-m 1000.0 \
  --expires-after-s 1.0 \
  --poll-interval-s 0.02 \
  --body-policy hold \
  --body-planner-config config/p1-m3-body-001.json \
  --body-scenario-config config/scenario.default.json
```

**逐字相等核对**：命令行首的解释器路径
`~/TetheredDroneTracking/.venv-yoloe/bin/python` 与 §L.3 / 命令时刻
复跑预检 JSON 的 `interpreter.executable` **字符串逐字相等** → 步骤 0′ 第 2 步
**PASS**。机械佐证：`[ <绝对路径> -ef .venv-yoloe/bin/python ]` 为真（同一
symlink，均指向 `…/cpython-3.12-macos-aarch64-none/bin/python3.12`），该绝对
路径下 `sys.executable` 打印值与预检值逐字相同。

**披露（拼写选择，零语义改动，沿用 §G.5 同一处置）**：§4 把唯一合法入口写成
**相对**形式，步骤 0′ 第 2 步要求与预检输出的**绝对**值逐字相等；两条同时满足
的唯一写法就是把同一解释器按绝对路径拼写。§4 的三条禁令（裸 `python3`、
`.venv-track/bin/python`、直接文件入口）一条未碰，`-m controller.track_loop`
模块入口未变，**18 个参数逐字未改、未加、未减**，`--run-id` 即 BC-BODY1-26
冻结的 A2 attempt-2 采集 ID。操作单未修改（BC-BODY1-21）。

## N.2 启动成功（保持暂停下，非 `TRIAL_VOID_TRACKER_STARTUP_FAILURE`）

在用户**保持暂停**期间启动。启动后机械确认：进程存活（`pgrep -f
"controller.track_loop"` 命中）；`runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2/`
**由 `RunLogger` create-once 新建**（`mkdir(exist_ok=False)` 未抛错，证明
§2.7 第 8 项的前置在启动时点仍然成立），目录内已出现 `frames.jsonl` 与
`manifest.json`，即 tracker 已越过 `TrackLoop.initialize` 并开始追平保留帧。
stderr 只有与预检同类的依赖噪声（xFormers/tifffile/OpenCV WARN），无异常。

确认启动成功后才请用户**恢复 Play**；恢复后用户未再暂停、未中途退出。

## N.3 运行结束时的机械事实（§3 步骤 4 的三项 AND 门）

| # | 要求 | 实测 |
|---|---|---|
| 1 | tracker **自然退出码 `0`**（非信号、非人工终止） | 后台任务完成通知逐字为 `Background command "Start the attempt-2 tracker" completed (exit code 0)`；随后 `pgrep -f "controller.track_loop"` **无命中** |
| 2 | stdout final JSON 指向**同一采集 ID** 的 `summary.json` | 见下方逐字原文，`run_id` 与 `summary` 路径均为 `…-arm-a-trial-2-attempt-2` |
| 3 | run 目录内 `metrics.final.json` 与 `summary.json` **均存在** | `ls` 实测两者均在（连同 `frames.jsonl`、`manifest.json`） |

**stdout final JSON 逐字原文**：

```json
{"qualification_metrics_error": null, "records": 651, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "state": "TRACKING", "summary": "~/TetheredDroneTracking/runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2/summary.json"}
```

## N.4 确认词的唯一机械来源（§3 步骤 4，只读）

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --validate-completion \
  --runtime runtime \
  --run-id p1-m3-body-001-arm-a-trial-2-attempt-2 \
  --tracker-exit-code 0 \
  --tracker-final-json '<上节 final JSON 原文>'
```

**退出码 `0`**，stdout 逐字为：

```text
TRACKER_AUTO_COMPLETE_CONFIRMED
```

该模式只读、不写任何文件、不调用 `finalize_run`；AND 门（exit code、final JSON
的 `run_id`、`summary` 解析、manifest 同 ID、两文件存在、
`metrics_snapshot_present`、`actual_duration_s >= 130.0`）全部满足。确认词由
工具产生，非人工复述。

## N.5 BC-BODY1-29 顺序遵从（F4，本轮的核心行为差异）

确认词产生后，实现角色的**下一个动作就是请用户退出 Play**——本节及其后所有
证据/状态写入都发生在用户退出**之后**。用户随即退出并报告：**Console 无报错**。

对照 attempt 1（作废那次）：当时的顺序是「读 run 记录 → validator → 写 §H →
通知退出」，post-tracker 停留 `252.399 s`；本轮改为 validator 通过即刻通知，
停留降到 **`24.422043 s`**（§N.7）。

## N.6 §3 步骤 5 绑定分析 —— **PASS**

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-a-trial-2-attempt-2
```

**退出码 `0`**，stderr 为空，stdout 逐字：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": false, "window_c_track_given_geom": 1.0}
```

工具先把 truth 流与五类配置原始字节 create-once 收进 run 目录，再机械核对全部
run 绑定、闭环恰好一次、窗口与整圈定义域，最后 create-once 写出
`m3_body_analysis.json`。**本轮所有硬门（含 revision 13 新增的两条域完整性门与
A2 前驱字节门）全部通过**，故 trial 有效。

**只读复算**（`--verify`）退出 `0`，stdout 与上面逐字相同（仅 `verified` 变
`true`）：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
```

**A2 前驱门实弹通过**：receipt 记录的三个 predecessor SHA 与 BC-BODY1-27 冻结
表逐字相等——`a7939b7c…fc54` / `d9774905…a50c` / `6f3e5238…f095`，即分析确实
绑定在 §K 保全的真实 void hold 上（§K.5 的排练在本次实跑中得到印证）。

## N.7 §3 步骤 6 记录（主结果 + BC-BODY1-30 披露）

**主结果（H1，唯一被门约束的量）**：

| 量 | 值 |
|---|---|
| `h1.full_loop_c_geom` | **`0.5783188398250908`** |
| `h1.disposition` | **`WITHIN_RANGE`**（`lower_bound 0.5645` / `ceiling 0.95`） |
| `window.c_track_given_geom` | `1.0`（`c_track` 同为 `1.0`，IoU 门 `0.3`） |
| 参考量（非门） | `online_aggregate_c_geom_reference = 0.6076499819755554`，`online_sensor_frames_reference = 650` |

对照 A1 的 `0.5784550773737355`：两次臂 A 的整圈 `C_geom` 差
`0.000136…`，量级与同臂重复一致（**仅陈述事实，不构成任何判定**；H1/H2 的
正式比较要等十次 trial 齐备后由 `--compare` 产出）。

**BC-BODY1-30 披露（只记录、不判定，本轮不构成任何门）**：

| 项 | 值 |
|---|---|
| tracker 最后一帧 `simulation_time_s` | `130.1835479736328`（`frame_id 650`，共 651 条帧记录 + 132 条 event） |
| Play 最后一条 truth `simulation_time_s` | `154.6055908203125`（共 **773** 条，`frame_id` 0–772） |
| **post-tracker 停留** | **`24.422043 s`**（仿真时间） |
| 实测圈数 = `final_unwrapped_mileage_m / route_perimeter_m` | `310.6273498589363 / 212.97056274847716` = **`1.458546`** |

即整个 Play 的里程落在 `[P, 2P)` 内。**按 revision 13 的准入判据这一点已不再
影响 trial 有效性**（`>= 2P` 上界已由接受轮 42 §A 撤下，「恰好一个闭环」由
`[0, P)` 样本域承担）；此处仅按 BC-BODY1-30 如实记录。两条域完整性门
（`unwrapped` 非递减、闭环后无 `< P` 样本）在本轮实跑中**未触发任何 fail
closed**。

**其余复算量**（`domains`）：`loop_frame_count 530`、`window_frame_count 155`、
`h2_grid_points 125`、`h2_grid_spacing_m 0.5`、`measurement_window_m [0.0, 62.5]`、
`route_perimeter_m 212.97056274847716`——全部与冻结口径一致。

## N.8 现场清点（Play 之后，零删除、零移动）

- **本次 run 目录**：`runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2/` 共
  **11 份文件**（十份 run-bound 输入/产物 + `m3_body_analysis.json`）。
  `scenario.json`/`margin.json`/`reanchor_config.json`/`body_config.json` 的
  SHA-256 与 §1 钉住值逐字相等（`f9c92052…`/`c72c9407…`/`593734d6…`/`3d1c4b54…`）。
- **共享槽位**（Unity 本次 Play 的产物，原地保留、未移动、未改名）：
  `m3_body_truth.jsonl` 773 行 `79378d22…`、`metrics.json` 61 行 `194eebd7…`、
  `body_command.json` `223e7daf…`、`gimbal_command.json` `35c2f343…`、
  `tracking_observation.json` `44f789e5…`、`frames/` **257** 项；
  `scenario_config.json` 仍不存在（回退项目默认，与 §1 激活方式一致）。
- **attempt-1 void hold 一字节未动**：仍恰 **10** 份文件。
- **A1 现场一字节未动**：正式 run 目录仍 **11** 份、post-run 归档仍 **6** 项；
  Play 之后复跑 A1 `--verify` 仍退出 0 并逐字返回其冻结 JSON
  （`0.5784550773737355`）。

## N.9 边界声明（§M–§N 批次）

- 本批**消耗了**用户授权的**唯一一次** Play 与采集 ID
  `p1-m3-body-001-arm-a-trial-2-attempt-2`；**其余 8 次 Play、任何重试、重进、
  调参仍未授权**，本批也不申请。
- **零阈值、零指标口径、零 CLI 参数、零协议、零代码/测试/config/scenario/model
  改动**；未修改操作单（BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`。
- 对 `docs/unity-test-log.md` 与 `docs/authorizations.md` **只读**：本会话未
  新增、未删除、未改写其中任何一行；接受角色在 Play 前写入的 §2.0 (c) 记录
  按先例（`8dbe9f9`）在 Play 结束后由本会话**零字节改动代录入库**。
- 本批未做 `--compare`、未对 void 工件计算任何指标、未动 A1 现场。
- **交回接受角色**：trial 2（attempt 2）的 disposition 归属与是否据此释放其余
  Play，由接受角色裁定；§M.1 的「HUD 不可见」披露同样待裁定。BC-BODY1-15 (d)
  的反调参纪律继续适用——本角色未依据 `0.5783188398250908` 调整任何参数。

---

# O. A3 的 Play 前置（§2.9 归档 + §2.10 核对 + §2.0 (b)，操作单 revision 14）

日期 2026-08-13，实现角色。交接来源：接受轮 48 §C 的四项发令前置，第 1–3 项
归本角色（第 4 项 (c) 是接受角色）。**零 Play、零采集 ID 创建/消耗、零代码/
测试/config/scenario/model 改动、零操作单改动；A2 的正式 run 目录一字节未动。**
批次开始时 `git status --porcelain` 为空。

## O.1 §2.9 A2 post-run 归档（有效 trial 命名空间）

destination `runtime/test-results/p1-m3-body-001-arm-a-trial-2-attempt-2-post-run/`
移动前经 `Path.exists()` 确认**不存在**，由本批新建；六项逐一 `os.rename`，
每次改名前再查一次目标不存在（零覆盖证明），移动后逐项确认源已不存在。

**移动前实测 = 接受轮 48 §2.9 钉住表（6/6 相符）= 移动后实测**：

| 项 | 计数 / 行数 / 字节 | SHA-256（前 = 钉住 = 后） |
|---|---|---|
| `frames/` | **257** 项（0 隐藏） | 聚合 `5af3b4d392cf08dd50fe188587f5b0b42015f63244cf47c3a0332bf2c4c76882` |
| `m3_body_truth.jsonl` | 773 行 / 796951 B | `79378d22cc8d05d3ccd9d6d6493551d3c27e7833e776b30c21ccfec31db0c2f6` |
| `metrics.json` | 61 行 / 2105 B | `194eebd71e029660fbbed8acdf50c0c57b2d1d650523be6611f53f0db6a55a8e` |
| `body_command.json` | 10 行 / 207 B | `223e7daf8ce2d7d19d01905f56757def8cbee248b9005d28f2a0919cfd1b5618` |
| `gimbal_command.json` | 15 行 / 340 B | `35c2f343763954ebd8b1d06f8c5c8345f6e7f84ff25682545cff7f2f07adccfd` |
| `tracking_observation.json` | 18 行 / 456 B | `44f789e57d9e282127e64eeb169e2e66d07980787297491d3f13ca07a6d4863d` |

- 归档目录内**恰 6 项**，名称与 §2.9 表逐字相符；移动后只新建**空**
  `runtime/frames/`（0 项），未预建任何 run 目录。
- **A2 正式 run 目录一字节未动**：仍 **11** 份文件（含 `m3_body_analysis.json`），
  目录聚合 SHA-256 移动前后相等。
- **归档后 A2 `--verify` 复跑**：退出 0，stdout 与 A2 冻结 JSON 经 `cmp`
  **逐字节相同**（`BYTE_IDENTICAL=YES`）——run 目录自包含，归档 shared 侧未影响它：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
```

- 位置风险沿 §2.6/§2.9 注登记，本批**不另择路径、不新增动作**。

## O.2 §2.10 八项 Play 前只读核对：**57 条机械核对，57 PASS / 0 FAIL**

| §2.10 项 | 核对内容 | 结果 |
|---|---|---|
| 1 | 六个 shared 文件 | 均**不存在** ✓（6/6） |
| 2 | `runtime/frames/` 存在且为空 | 存在、**0 项** ✓（2/2） |
| 3 | 1b / attempt-1 / attempt-2 / attempt-3 四处旧 hold | 帧计数 **257 / 93 / 109 / 257** + 全部 SHA-256 ✓（21/21） |
| 4 | A1 正式 run 目录 | **11** 份 + 聚合 `7c3af28e…cda79` ✓；`--verify` 退出 0 且与冻结 JSON `cmp` 逐字节相同（`0.5784550773737355`）✓ |
| 5 | A2 正式 run 目录 | **11** 份且含 `m3_body_analysis.json` ✓；`--verify` 见 §O.1 ✓ |
| 6 | 两处 post-run 归档 | A1 **6** 项（`frames/` 257，聚合 `ea9ba050…2fb3`）✓；A2 **6** 项且逐项等于 §2.9 钉住值 ✓（11/11） |
| 7 | 八个活动标记 + attempt-1 void hold | 标记均不存在 ✓；hold 仍**恰 10 份文件、零隐藏项**、三个钉住 SHA 相等 ✓（12/12） |
| 8 | **A3 create-once 前置** | `runtime/runs/p1-m3-body-001-arm-a-trial-3/` **不存在** ✓（1/1） |

## O.3 §2.0 (b) 报告（测量时点）

```text
$ git rev-parse HEAD
70f788b6e0b473ab4e37e8f0ac053df12c639d91

$ git status --porcelain
（空输出）
```

基线运行时解析（N26 / COORD-007 R7）：

```bash
$ grep -m1 '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md
passed_candidate: 07bb8a47a9e41581c1450a7b0335e501ffdaaec9
```

`git diff --name-only 07bb8a47…c9..HEAD` = **8 个路径**，区间 5 个 commit。逐条归因：

| # | 路径 | 归属 | PLAY_GOVERNING |
|---|---|---|---|
| 1 | `docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md` | 接受轮 45/46/47/48 | 否 |
| 2 | `docs/reviews/P1-M3-BODY-001.md` | Review round 7 与 `passed_candidate` 机读行 | 否 |
| 3 | `docs/evidence/P1-M3-BODY-001-1c-preflight.md` | 操作单 **revision 13 → 14**（接受角色撰写） | **是** |
| 4 | `docs/evidence/P1-M3-BODY-001-arm-a-trial-2.md` | 本文件 §K/§L/§M/§N（第 5 步保全、Play 前报告、A2 采集） | 否 |
| 5 | `docs/implementation-status.md` | 接受轮 47 把 A2 记入里程碑账本 | 否 |
| 6 | `docs/authorizations.md` | A2 attempt-2 与 trial 3 两次 GO 入账（接受角色代录） | 否 |
| 7 | `docs/unity-test-log.md` | 接受轮 46 的 §2.0 (c) 记录（本角色只读，零改动代录入库） | 否 |
| 8 | `docs/current-status.md` | 状态板 | 否 |

**测量侧逐字节相同**（最强形式）：

```bash
$ git diff --name-only 07bb8a4..HEAD -- controller/ Assets/ config/ \
    ProjectSettings/ Packages/packages-lock.json tools/ tests/
（空输出）
```

自 Review round 7 通过的候选起，`controller/`、`Assets/`、`config/`、
`ProjectSettings/`、`Packages/packages-lock.json`、`tools/`（含
`analyze_m3_body.py`、`preflight_reanchor_env.py`）与 `tests/` **一个字节未动**——
A2 的采集与分析全程都跑在这份已复核的代码上。

**PLAY_GOVERNING 子集（读法 1，接受轮 40 裁定）= 恰 1 条**，即第 3 条操作单，
现为 **revision 14**。**该条的复核状态见 §O.5 第 1 条。**

## O.4 §3 步骤 0 环境预检与步骤 0′ 第 1 步

```bash
.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json
```

**退出码 `0`**，`status = "PASS"`，`side_effect_identity.unchanged = true`。与 §L.3
记录的那份相比，**唯一差异**是 `side_effect_identity` 前后两份
`run_directories` 各多出一个条目 `p1-m3-body-001-arm-a-trial-2-attempt-2`
（A2 采集的产物，28 → 29），其余字段逐字相同；`p1-m3-body-001-arm-a-trial-3`
**不在**其中，与 §2.10 第 8 项一致。完整 stdout JSON（逐字）：

```json
{
  "constructors": {
    "dinov2_embedder": "controller.reanchor_models.DinoV2Embedder",
    "nanotrack_tracker": "controller.trackers.NanoTrackV2Tracker",
    "yoloe_proposer": "controller.reanchor_models.YoloeProposer"
  },
  "interpreter": {
    "executable": "~/TetheredDroneTracking/.venv-yoloe/bin/python",
    "prefix": "~/TetheredDroneTracking/.venv-yoloe",
    "python_version": "3.12.13"
  },
  "mode": "reanchor-preflight",
  "nanotrack": {
    "backend": "opencv-dnn-default/cpu",
    "model_sha256": {
      "backbone": "530bdd0cd00f19afab79a863e71ba71e3312395a5dc9151af675082bdaaa2fc4",
      "neckhead": "0d8c0637be849f092cc7236cae02e55c8b9455ebe37ba50601d6115db4247cd9"
    },
    "name": "nanotrack-v2",
    "opencv_package_pin": "opencv-contrib-python==5.0.0.93",
    "opencv_version": "5.0.0",
    "preprocessing_id": "opencv-tracker-nano-5.0.0-default-v1"
  },
  "packages": {
    "cv2": {
      "pin": "5.0.0",
      "pin_source": "nanotrack spec opencv.tested_version",
      "raw": "5.0.0"
    },
    "torch": {
      "pin": "2.13.0",
      "pin_source": "reanchor config runtime.torch_pin",
      "raw": "2.13.0"
    },
    "torchvision": {
      "pin": "0.28.0",
      "pin_source": "reanchor config runtime.torchvision_pin",
      "raw": "0.28.0"
    },
    "ultralytics": {
      "pin": "8.4.104",
      "pin_source": "reanchor config runtime.ultralytics_pin",
      "raw": "8.4.104"
    }
  },
  "reanchor_config": {
    "carrier": "minimal-triple-gated-re-anchor",
    "device": "cpu",
    "path": "config/detector-reanchor.models.json",
    "schema_version": "tethered-detector-reanchor/v1",
    "sha256": "593734d67ada73a0304d67d27c6ae536be616d2180f744336b85ff6e0ac706d2"
  },
  "side_effect_identity": {
    "after": {
      "guarded_files": {
        "runtime/body_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/gimbal_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/metrics.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/tracking_observation.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        }
      },
      "run_directories": [
        "p1-detect-001-qual-1",
        "p1-detect-001-qual-2",
        "p1-detect-001-qual-3",
        "p1-m3-body-001-arm-a-trial-1-attempt-4",
        "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold",
        "p1-m3-body-001-arm-a-trial-2-attempt-2",
        "p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold",
        "p1-track-follow",
        "p1-track-follow-attempt1",
        "p1-track-nadir",
        "p1-track-occlusion",
        "rate20-calib",
        "rate20-follow-r1",
        "rate20-follow-r2",
        "rate20-follow-r3",
        "rate20-nadir-r1",
        "rate20-nadir-r2",
        "rate20-nadir-r3",
        "rate5-calib",
        "rate5-follow-r1",
        "rate5-follow-r2",
        "rate5-follow-r3",
        "rate5-nadir-r1",
        "rate5-nadir-r2",
        "rate5-nadir-r3",
        "rs2-pilot",
        "rs2-r20-follow-1",
        "rs2-r20-follow-2",
        "rs2-r20-follow-3"
      ]
    },
    "before": {
      "guarded_files": {
        "runtime/body_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/gimbal_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/metrics.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/tracking_observation.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        }
      },
      "run_directories": [
        "p1-detect-001-qual-1",
        "p1-detect-001-qual-2",
        "p1-detect-001-qual-3",
        "p1-m3-body-001-arm-a-trial-1-attempt-4",
        "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold",
        "p1-m3-body-001-arm-a-trial-2-attempt-2",
        "p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold",
        "p1-track-follow",
        "p1-track-follow-attempt1",
        "p1-track-nadir",
        "p1-track-occlusion",
        "rate20-calib",
        "rate20-follow-r1",
        "rate20-follow-r2",
        "rate20-follow-r3",
        "rate20-nadir-r1",
        "rate20-nadir-r2",
        "rate20-nadir-r3",
        "rate5-calib",
        "rate5-follow-r1",
        "rate5-follow-r2",
        "rate5-follow-r3",
        "rate5-nadir-r1",
        "rate5-nadir-r2",
        "rate5-nadir-r3",
        "rs2-pilot",
        "rs2-r20-follow-1",
        "rs2-r20-follow-2",
        "rs2-r20-follow-3"
      ]
    },
    "checked": [
      "runtime/runs direct child directory names",
      "runtime/body_command.json present/size/sha256",
      "runtime/gimbal_command.json present/size/sha256",
      "runtime/tracking_observation.json present/size/sha256",
      "runtime/metrics.json present/size/sha256"
    ],
    "unchanged": true
  },
  "status": "PASS"
}
```

**步骤 0′ 第 1 步**：`interpreter.executable` 逐字值落盘

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python
```

（`prefix` = `~/TetheredDroneTracking/.venv-yoloe`，`python_version`
`3.12.13`，与 §1 冻结入口一致。）**步骤 0′ 第 2 步尚未执行**——本批不启动
tracker，该步在获授权的那次 Play 中执行并追记。

## O.5 交回接受角色 / 未验证项

1. **PLAY_GOVERNING 恰 1 条 = 操作单 revision 14 自身，其独立复核仍欠。**
   与上一轮同构（revision 13 由接受轮 46 单独定名处置）。**接受轮 48 §D 已把
   「revision 14 与轮 47 的操作单更正」登记为下一轮复核债**，但**未**像轮 46
   那样给出具名 disposition token；本角色不自行判定该缺失是否需要补，如实报告，
   请接受角色在 (c) 记录中一并处理。
2. **测量时点 HEAD ≠ 发令时点 HEAD**：§2.0 (d) 要求发令时刻只允许
   `docs/unity-test-log.md` 一份未提交差异，故本批（本节 + 状态板）必须在 (c)
   之前提交，HEAD 随之前移。**(c) 的权威值必须由接受角色在写入时点自行运行
   `git rev-parse HEAD` 与 `git status --porcelain`**，不得复制 §O.3。本批只动
   两个文档路径，均**不在** PLAY_GOVERNING，提交后测量侧 diff 仍为空。
3. **§2.10 需在发令时刻复查**：若 (c) 之后到发令之间出现新提交或任何 `runtime/`
   变化，本节结论即失效，须重取（上一轮即因轮 46 的提交而重跑过一次）。
4. **本批不产生 Unity 用例**，也不申领 `UNITY_NA`。
5. **未验证项**：步骤 0′ 第 2 步、§3 步骤 1–6 的全部 Play 内动作。A3 的采集 ID
   `p1-m3-body-001-arm-a-trial-3` 从未被创建或消耗，故本轮**无前驱门**参与
   （`_check_a1/_a2_predecessor_hold` 都只对各自采集触发）。

## O.6 §O 批次边界声明

- **零 Play、零采集 ID 创建/消耗**；`runs/p1-m3-body-001-arm-a-trial-3/` 未预建。
- **零删除、零覆盖、零分析**：只有 1 次 `mkdir`（归档目录）、6 次 `os.rename`、
  1 次 `mkdir runtime/frames`；A1/A2 的正式 run 目录、两处 post-run 归档、四处旧
  hold 与 attempt-1 void hold 全部字节不变。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单
  （BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`；对
  `docs/unity-test-log.md` 与 `docs/authorizations.md` 只读。
- 本批写入仅两个路径：本证据文件与 `docs/current-status.md`。
- 复核范围：§O.1–§O.4 的 `runtime/` 现场事实（可由 `runtime/` 直接复算）、
  三条只读命令的逐字输出、以及 §O.3 的基线归因。

---

# P. arm A trial 3 的 Play 与三个独立硬门（§3 步骤 1–2，**启动 tracker 之前**落盘）

日期 2026-08-13。用户按接受轮 49 的 §2.0 (c) 记录（`docs/unity-test-log.md`，
HEAD `0c428f6`）进入 Play **恰一次**。采集 ID `p1-m3-body-001-arm-a-trial-3`
（自身即 canonical slot，从未被消耗，**本轮无前驱门参与**）。

发令时刻三项复核（实现角色在用户进 Play 之前实测）：

- **§2.0 (d)**：`git diff --name-only` 逐字只有 `docs/unity-test-log.md` ✓
- **§3 步骤 0 预检（命令时刻复跑）**：退出 0、`status=PASS`、
  `side_effect_identity.unchanged=true`，stdout JSON 与 §O.4 记录的那份**逐字节
  相同** ✓
- **§2.10 八项复跑**：**57/57 PASS**（轮 49 的提交改变了 HEAD，故按 §O.5 第 3 条
  重取，结论不变）✓

## P.1 用户进入 Play 并暂停（口报如实记录，**不作判据**）

用户报告逐字：**「已暂停」**——未报时刻（本载体无计时 HUD，见 §M.1 的既有披露，
本轮无新增情况）。门 1 判据一律由保留帧机械导出，不取口报值。

## P.2 门 1 —— 暂停窗口（`2.000000 <= reported_sim_t < 10.000000`）

**导出命令原文**（只读；只解析保留帧的元数据 JSON，不读任何真值文件）：

```bash
.venv-yoloe/bin/python - <<'PYEOF'
import json, pathlib
frames = pathlib.Path("runtime/frames")
records = []
for p in sorted(frames.glob("frame_*.json")):
    d = json.loads(p.read_text())
    records.append((d["frame_id"], d["simulation_time_s"], p.name))
ids = [r[0] for r in records]
print("retained metadata files:", len(records))
print("frame_id range: min =", min(ids), " max =", max(ids),
      " contiguous =", ids == list(range(min(ids), max(ids)+1)))
print("max simulation_time_s = %.6f" % max(r[1] for r in records))
PYEOF
```

**逐字输出**：

```text
directory entries: 43
retained metadata files: 21
frame_id range: min = 0  max = 20  contiguous = True
max simulation_time_s = 4.183153
min simulation_time_s = 0.186579
  frame 18: 3.786721706390381  (frame_0000000018.json)
  frame 19: 3.986103057861328  (frame_0000000019.json)
  frame 20: 4.183152675628662  (frame_0000000020.json)
GATE1 2.000000 <= 4.183153 < 10.000000 -> True
GATE2 lowest retained frame == 0 -> True
latest.json frame_id = 20
```

| 要求 | 值 |
|---|---|
| 导出命令原文 | 见上 |
| 保留帧编号范围 | `frame_id` **0–20**，连续，21 份元数据（目录共 43 项 = 21 json + 21 jpg + `latest.json`；`latest.json` 的 `frame_id` = **20**，与最大保留帧一致） |
| 导出的数值 | `reported_sim_t` = **`4.183152675628662`** |

**门 1 PASS**：两侧余量约 `2.183 s` 与 `5.817 s`，远大于一帧（本轮相邻帧约
`0.199 s`），故 COORD-007 §4.1 的一帧下界缺口对本次判定无实际影响（缺口本身
仍未消除，需 R10）。

## P.3 门 2 —— 最低保留帧必须恰为 `0`

最小 `frame_id` = **`0`** ✓（见上），**门 2 PASS**。

## P.4 门 3 —— 冻结框匹配（用户目检）

```bash
.venv-yoloe/bin/python -m controller.track_loop --dump-frame 0 --output <scratch>/a3_frame0.jpg
```

退出码 0，导出图 **640×480**，叠加**已冻结**像素框 `(177, 195, 77, 73)`
（`min_side = 73 px`）——未重新框选、未重新估框、未做六位小数化、未读任何真值。

**用户目检结论（逐字）**：「**匹配**」→ **门 3 PASS**。现场未做任何调整。

**三门全部 PASS**，互不覆盖，故按 §3 步骤 2 末段在**保持暂停**下启动 tracker。

---

# Q. arm A trial 3：tracker、完成握手与绑定分析（§3 步骤 2 末段–步骤 6）

## Q.1 §3 步骤 0′ 第 2 步 —— 解释器绑定与实际命令行（**启动前**核对）

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
  --run-id p1-m3-body-001-arm-a-trial-3 \
  --init-frame 0 \
  --init-box 0.2765625 0.40625 0.1203125 0.15208333333333332 \
  --planned-duration-s 130.0 \
  --maximum-ground-range-m 1000.0 \
  --expires-after-s 1.0 \
  --poll-interval-s 0.02 \
  --body-policy hold \
  --body-planner-config config/p1-m3-body-001.json \
  --body-scenario-config config/scenario.default.json
```

命令行首 `~/TetheredDroneTracking/.venv-yoloe/bin/python` 与命令时刻预检
JSON 的 `interpreter.executable` **字符串逐字相等** → 步骤 0′ 第 2 步 **PASS**
（`-ef` 同文件佐证同 §N.1）。**除 `--run-id` 外 18 个参数逐字未改、未加、未减**；
绝对/相对拼写的处置沿用 §G.5/§N.1 的既有披露，操作单未修改。

## Q.2 启动成功（保持暂停下）

用户保持暂停期间启动：进程存活；`runtime/runs/p1-m3-body-001-arm-a-trial-3/`
由 `RunLogger` **create-once 新建**（`mkdir(exist_ok=False)` 未抛错，证明 §2.10
第 8 项在启动时点仍成立），已出现 `frames.jsonl` 与 `manifest.json`。stderr 仅
依赖噪声。确认成功后才请用户恢复 Play；恢复后未再暂停、未中途退出。

**本轮无前驱门**：采集 ID `p1-m3-body-001-arm-a-trial-3` 自身即 canonical slot、
从未被消耗，`_check_a1/_a2_predecessor_hold` 都只对各自采集触发，故 receipt 中
**不含**任何 predecessor 字段（实测 `predecessor`/`attempt` 键为空集）——与 A1/A2
的差异是设计使然，不是缺失。

## Q.3 完成握手（§3 步骤 4 的三项 AND 门）

| # | 要求 | 实测 |
|---|---|---|
| 1 | 自然退出码 `0` | 后台通知逐字 `Background command "Start the trial-3 tracker" completed (exit code 0)`；随后 `pgrep` 无命中 |
| 2 | final JSON 指向同一采集 ID 的 `summary.json` | 见下 |
| 3 | `metrics.final.json` 与 `summary.json` 均存在 | `ls` 实测均在 |

```json
{"qualification_metrics_error": null, "records": 652, "run_id": "p1-m3-body-001-arm-a-trial-3", "state": "TRACKING", "summary": "~/TetheredDroneTracking/runtime/runs/p1-m3-body-001-arm-a-trial-3/summary.json"}
```

**确认词的唯一机械来源**（只读，不写文件、不 finalize）：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --validate-completion \
  --runtime runtime --run-id p1-m3-body-001-arm-a-trial-3 \
  --tracker-exit-code 0 --tracker-final-json '<上面的 final JSON 原文>'
```

退出码 **0**，stdout 逐字 `TRACKER_AUTO_COMPLETE_CONFIRMED`。

**BC-BODY1-29 顺序遵从**：确认词产生后的下一个动作即请用户退出；本节及其后所有
写入都在用户退出之后。用户退出并报告：**Console 无报错**。

## Q.4 §3 步骤 5 绑定分析 —— **PASS**

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-a-trial-3
```

退出码 **0**，stderr 为空：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": false, "window_c_track_given_geom": 1.0}
```

只读复算 `--verify` 退出 **0**，逐字相同（仅 `verified` 为 `true`）。全部硬门
（含两条域完整性门）通过，`m3_body_analysis.json` create-once 写出。

## Q.5 §3 步骤 6 记录（主结果 + BC-BODY1-30 披露）

| 量 | 值 |
|---|---|
| `h1.full_loop_c_geom` | **`0.597146417669116`** |
| `h1.disposition` | **`WITHIN_RANGE`**（`0.5645` / `0.95`） |
| `window.c_track_given_geom` | `1.0`（`c_track` 同为 `1.0`） |
| 参考量（非门） | `online_aggregate_c_geom_reference = 0.6215202808380127`，`online_sensor_frames_reference = 650` |

臂 A 三次整圈 `C_geom`：A1 `0.5784550773737355`、A2 `0.5783188398250908`、
A3 `0.597146417669116`。**仅陈述，不构成任何判定**——H1/H2 的正式比较要等十次
trial 齐备后由 `--compare` 产出，n=3 不支持任何主张。

**BC-BODY1-30 披露（只记录、不判定）**：

| 项 | 值 |
|---|---|
| tracker 最后一帧 `simulation_time_s` | `130.38656616210938`（`frame_id 651`，652 条帧记录） |
| Play 最后一条 truth `simulation_time_s` | `150.18692016601562`（**751** 条） |
| **post-tracker 停留** | **`19.800354 s`**（A2 为 `24.422043 s`） |
| 实测圈数 | `301.80870056694414 / 212.97056274847716` = **`1.417138`** |

`domains` 其余量：`loop_frame_count 529`、`window_frame_count 155`、
`h2_grid_points 125`、`h2_grid_spacing_m 0.5`、`measurement_window_m [0.0, 62.5]`
——与冻结口径一致；两条域完整性门零触发。

## Q.6 现场清点

- 本次 run 目录 **11 份文件**（含 `m3_body_analysis.json`）；`scenario.json` /
  `margin.json` / `reanchor_config.json` / `body_config.json` 的 SHA-256 与 §1 钉住
  值逐字相等，`visible_arc_sha256` = `4fe2eea5…df55`。
- 共享槽位为本次 Play 的产物，**原地保留、未移动**（下一次 trial 前的归档属
  下一轮接受角色的合同）。
- **A1/A2 现场与所有 hold 一字节未动**；两处 post-run 归档仍各 6 项。

## Q.7 边界声明（§P–§Q 批次）

- 本批**消耗了**用户授权的唯一一次 Play 与采集 ID `p1-m3-body-001-arm-a-trial-3`；
  **arm A trial 4/5 与 arm B 五次仍未授权**，本批不申请，也未跑 `--compare`。
- **零阈值/指标口径/CLI/协议/代码/config/scenario/model 改动**；未修改操作单
  （BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`；对 `docs/unity-test-log.md`
  与 `docs/authorizations.md` 只读（接受角色的 (c) 记录在 Play 后零字节代录入库）。
- BC-BODY1-15 (d) 反调参纪律：未依据 `0.597146417669116` 调整任何参数。
- **交回接受角色**：trial 3 的 disposition 归属、里程碑账本记录，以及是否释放后续
  Play。

---

# R. A4 的 Play 前置（§2.11 归档 + §2.12 核对 + §2.0 (b)，操作单 revision 15）

日期 2026-08-13，实现角色。交接来源：接受轮 50（A3 判为有效、trial 4 GO 入账、
操作单 revision 15）。**零 Play、零采集 ID 创建/消耗、零代码/测试/config/scenario/
model 改动、零操作单改动；三个有效 run 目录一个都没动。** 批次开始时
`git status --porcelain` 为空。

## R.1 §2.11 A3 post-run 归档

destination `runtime/test-results/p1-m3-body-001-arm-a-trial-3-post-run/` 移动前经
`Path.exists()` 确认**不存在**，由本批新建；六项逐一 `os.rename`，每次改名前再查
一次目标不存在（零覆盖证明），移动后逐项确认源已不存在。

**移动前实测 = 接受轮 50 §2.11 钉住表（6/6 相符）= 移动后实测**：

| 项 | 计数 / 行数 / 字节 | SHA-256（前 = 钉住 = 后） |
|---|---|---|
| `frames/` | **257** 项（0 隐藏） | 聚合 `505b94df06bc001fcd491b197199a9ecc79ab7313e2d93b4078311431bf35956` |
| `m3_body_truth.jsonl` | 751 行 / 774681 B | `3b38520f7a5c86e2a46c9f691c76d86b1220872206932eea0ef4c5bd966cee4e` |
| `metrics.json` | 61 行 / 2106 B | `b5cfca6d6f251de87829cff383a9deb1cb7c2ec4e11307912dff43e90a26c335` |
| `body_command.json` | 10 行 / 207 B | `48692462e9cc758b9c90ef3084c441a1c2b7d971c2a684ecb17406ac33d51eae` |
| `gimbal_command.json` | 15 行 / 341 B | `fe132ccdaeb09f4a8a7516802e9a20339f3cb59fd216cfe5e46d3917588705d0` |
| `tracking_observation.json` | 18 行 / 455 B | `02dc84ddf5055961031a0f886eb6f4c4aa0d0317d3dc9235ebc406ce694c5d0b` |

- 归档目录内**恰 6 项**，名称与 §2.11 表逐字相符；移动后只新建**空**
  `runtime/frames/`（0 项），未预建任何 run 目录。
- **A3 正式 run 目录一字节未动**：仍 **11** 份文件（含 `m3_body_analysis.json`），
  目录聚合 SHA-256 移动前后相等。
- **归档后 A3 `--verify` 复跑**：退出 0，逐字返回

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
```

- 位置风险沿 §2.9/§2.11 登记，本批不另择路径、不新增动作。

## R.2 §2.12 七项 Play 前只读核对：**67 条机械核对，67 PASS / 0 FAIL**

| §2.12 项 | 核对内容 | 结果 |
|---|---|---|
| 1 | 六个 shared 文件 | 均**不存在** ✓（6/6） |
| 2 | `runtime/frames/` 存在且为空 | 存在、**0 项** ✓（2/2） |
| 3 | 四处旧 hold | **257 / 93 / 109 / 257** + 全部 SHA-256 ✓（21/21） |
| 4 | **三个正式 run 目录** | A1/A2/A3 各**恰 11 份**且各含 `m3_body_analysis.json` ✓；三条 `--verify` 各退出 0 并逐字返回 `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` ✓（6/6 + 三条 verify） |
| 5 | **三处 post-run 归档** | A1 **6** 项（`frames/` 257，聚合 `ea9ba050…2fb3`）、A2 **6** 项（聚合 `5af3b4d3…`、五文件全等）、A3 **6** 项（聚合 `505b94df…`、五文件逐项等于 §2.11 钉住值）✓（19/19） |
| 6 | 活动标记 + attempt-1 void hold | 八个标记均不存在；hold 仍**恰 10 份、零隐藏项**、三钉住 SHA 相等 ✓（12/12） |
| 7 | **A4 create-once 前置** | `runtime/runs/p1-m3-body-001-arm-a-trial-4/` **不存在** ✓（1/1） |

## R.3 §2.0 (b) 报告（测量时点）

```text
$ git rev-parse HEAD
e4fc625dc46bff32454db52238e4438a6f1e3f58

$ git status --porcelain
（空输出）
```

基线运行时解析：`grep -m1 '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md` →
**`07bb8a47a9e41581c1450a7b0335e501ffdaaec9`**。
`git diff --name-only 07bb8a4..HEAD` = **8 个路径**，与 §O.3 **同一集合**（提案、
复核、操作单、本证据文件、里程碑账本、授权账本、Unity 日志、状态板），只是内容
随轮 47–50 与本轮 trial 3 记录增长；无新增路径类别。

**测量侧逐字节相同**：

```bash
$ git diff --name-only 07bb8a4..HEAD -- controller/ Assets/ config/ \
    ProjectSettings/ Packages/packages-lock.json tools/ tests/
（空输出）
```

**PLAY_GOVERNING 子集 = 恰 1 条**：操作单，现为 **revision 15**。其复核状态
见 §R.5 第 1 条。

## R.4 §3 步骤 0 环境预检与步骤 0′ 第 1 步

退出码 **0**，`status = "PASS"`，`side_effect_identity.unchanged = true`。与 §O.4
记录的那份逐字段比对：**除 `side_effect_identity` 前后两份 `run_directories` 各
新增 `p1-m3-body-001-arm-a-trial-3`（29 → 30）外，其余字段完全相同**；
`p1-m3-body-001-arm-a-trial-4` **不在**其中，与 §2.12 第 7 项一致。完整 stdout
JSON（逐字）：

```json
{
  "constructors": {
    "dinov2_embedder": "controller.reanchor_models.DinoV2Embedder",
    "nanotrack_tracker": "controller.trackers.NanoTrackV2Tracker",
    "yoloe_proposer": "controller.reanchor_models.YoloeProposer"
  },
  "interpreter": {
    "executable": "~/TetheredDroneTracking/.venv-yoloe/bin/python",
    "prefix": "~/TetheredDroneTracking/.venv-yoloe",
    "python_version": "3.12.13"
  },
  "mode": "reanchor-preflight",
  "nanotrack": {
    "backend": "opencv-dnn-default/cpu",
    "model_sha256": {
      "backbone": "530bdd0cd00f19afab79a863e71ba71e3312395a5dc9151af675082bdaaa2fc4",
      "neckhead": "0d8c0637be849f092cc7236cae02e55c8b9455ebe37ba50601d6115db4247cd9"
    },
    "name": "nanotrack-v2",
    "opencv_package_pin": "opencv-contrib-python==5.0.0.93",
    "opencv_version": "5.0.0",
    "preprocessing_id": "opencv-tracker-nano-5.0.0-default-v1"
  },
  "packages": {
    "cv2": {
      "pin": "5.0.0",
      "pin_source": "nanotrack spec opencv.tested_version",
      "raw": "5.0.0"
    },
    "torch": {
      "pin": "2.13.0",
      "pin_source": "reanchor config runtime.torch_pin",
      "raw": "2.13.0"
    },
    "torchvision": {
      "pin": "0.28.0",
      "pin_source": "reanchor config runtime.torchvision_pin",
      "raw": "0.28.0"
    },
    "ultralytics": {
      "pin": "8.4.104",
      "pin_source": "reanchor config runtime.ultralytics_pin",
      "raw": "8.4.104"
    }
  },
  "reanchor_config": {
    "carrier": "minimal-triple-gated-re-anchor",
    "device": "cpu",
    "path": "config/detector-reanchor.models.json",
    "schema_version": "tethered-detector-reanchor/v1",
    "sha256": "593734d67ada73a0304d67d27c6ae536be616d2180f744336b85ff6e0ac706d2"
  },
  "side_effect_identity": {
    "after": {
      "guarded_files": {
        "runtime/body_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/gimbal_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/metrics.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/tracking_observation.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        }
      },
      "run_directories": [
        "p1-detect-001-qual-1",
        "p1-detect-001-qual-2",
        "p1-detect-001-qual-3",
        "p1-m3-body-001-arm-a-trial-1-attempt-4",
        "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold",
        "p1-m3-body-001-arm-a-trial-2-attempt-2",
        "p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold",
        "p1-m3-body-001-arm-a-trial-3",
        "p1-track-follow",
        "p1-track-follow-attempt1",
        "p1-track-nadir",
        "p1-track-occlusion",
        "rate20-calib",
        "rate20-follow-r1",
        "rate20-follow-r2",
        "rate20-follow-r3",
        "rate20-nadir-r1",
        "rate20-nadir-r2",
        "rate20-nadir-r3",
        "rate5-calib",
        "rate5-follow-r1",
        "rate5-follow-r2",
        "rate5-follow-r3",
        "rate5-nadir-r1",
        "rate5-nadir-r2",
        "rate5-nadir-r3",
        "rs2-pilot",
        "rs2-r20-follow-1",
        "rs2-r20-follow-2",
        "rs2-r20-follow-3"
      ]
    },
    "before": {
      "guarded_files": {
        "runtime/body_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/gimbal_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/metrics.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/tracking_observation.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        }
      },
      "run_directories": [
        "p1-detect-001-qual-1",
        "p1-detect-001-qual-2",
        "p1-detect-001-qual-3",
        "p1-m3-body-001-arm-a-trial-1-attempt-4",
        "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold",
        "p1-m3-body-001-arm-a-trial-2-attempt-2",
        "p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold",
        "p1-m3-body-001-arm-a-trial-3",
        "p1-track-follow",
        "p1-track-follow-attempt1",
        "p1-track-nadir",
        "p1-track-occlusion",
        "rate20-calib",
        "rate20-follow-r1",
        "rate20-follow-r2",
        "rate20-follow-r3",
        "rate20-nadir-r1",
        "rate20-nadir-r2",
        "rate20-nadir-r3",
        "rate5-calib",
        "rate5-follow-r1",
        "rate5-follow-r2",
        "rate5-follow-r3",
        "rate5-nadir-r1",
        "rate5-nadir-r2",
        "rate5-nadir-r3",
        "rs2-pilot",
        "rs2-r20-follow-1",
        "rs2-r20-follow-2",
        "rs2-r20-follow-3"
      ]
    },
    "checked": [
      "runtime/runs direct child directory names",
      "runtime/body_command.json present/size/sha256",
      "runtime/gimbal_command.json present/size/sha256",
      "runtime/tracking_observation.json present/size/sha256",
      "runtime/metrics.json present/size/sha256"
    ],
    "unchanged": true
  },
  "status": "PASS"
}
```

**步骤 0′ 第 1 步**：`interpreter.executable` 逐字值

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python
```

**步骤 0′ 第 2 步尚未执行**（本批不启动 tracker）。

## R.5 交回接受角色 / 未验证项

1. **PLAY_GOVERNING 恰 1 条 = 操作单 revision 15 自身**，与前两轮同构。轮 50 是否
   已按轮 46/49 的方式给出具名 disposition，由接受角色在 (c) 记录中确认；本角色
   如实报告，不自行判定。
2. **测量时点 HEAD ≠ 发令时点 HEAD**：本批（本节 + 状态板）须在 (c) 之前提交，
   **(c) 的 HEAD/status 必须由接受角色在写入时点自取**。本批只动两个文档路径，
   均不在 PLAY_GOVERNING。
3. **§2.12 需在发令时刻复查**（前两轮均因接受角色的新提交而重跑过）。
4. **A4 无前驱门**：`p1-m3-body-001-arm-a-trial-4` 从未创建或消耗，两个
   `_check_a*_predecessor_hold` 都不触发，receipt 不会有 predecessor 字段。
5. **本批不产生 Unity 用例**，不申领 `UNITY_NA`。

## R.6 §R 批次边界声明

- **零 Play、零采集 ID 创建/消耗**；`runs/p1-m3-body-001-arm-a-trial-4/` 未预建。
- **零删除、零覆盖、零分析**：1 次 `mkdir`（归档目录）、6 次 `os.rename`、1 次
  `mkdir runtime/frames`；三个有效 run 目录、三处 post-run 归档、四处旧 hold 与
  attempt-1 void hold 全部字节不变。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单
  （BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`；对 `docs/unity-test-log.md`
  与 `docs/authorizations.md` 只读。
- 本批写入仅两个路径：本证据文件与 `docs/current-status.md`。
- 复核范围：§R.1–§R.4 的 `runtime/` 现场事实、四条只读命令的逐字输出、§R.3 的
  基线归因。

---

# S. arm A trial 4 的 Play 与三个独立硬门（§3 步骤 1–2，**启动 tracker 之前**落盘）

日期 2026-08-13。用户按接受轮 50/51 的 §2.0 (c) 记录（`docs/unity-test-log.md`，
HEAD `d8762f6`）进入 Play **恰一次**。采集 ID `p1-m3-body-001-arm-a-trial-4`
（自身即 canonical slot，从未被消耗，**本轮无前驱门参与**）。

发令时刻三项复核（用户进 Play 之前实测）：

- **§2.0 (d)**：`git diff --name-only` 逐字只有 `docs/unity-test-log.md` ✓
- **§3 步骤 0 预检（命令时刻复跑）**：退出 0、`status=PASS`、
  `side_effect_identity.unchanged=true`，stdout JSON 与 §R.4 记录的那份**逐字节
  相同** ✓
- **§2.12 七项复跑**：**67/67 PASS**（轮 51 的两个提交改变了 HEAD，按 §R.5 第 3 条
  重取，结论不变）✓

## S.1 用户进入 Play 并暂停（口报如实记录，**不作判据**）

用户报告逐字：**「已暂停」**——未报时刻（本载体无计时 HUD，§M.1 已披露）。门 1
判据一律由保留帧机械导出。

## S.2 门 1 —— 暂停窗口（`2.000000 <= reported_sim_t < 10.000000`）

**导出命令原文**（只读；只解析保留帧元数据 JSON，不读任何真值文件）：

```bash
.venv-yoloe/bin/python - <<'PYEOF'
import json, pathlib
frames = pathlib.Path("runtime/frames")
records = []
for p in sorted(frames.glob("frame_*.json")):
    d = json.loads(p.read_text())
    records.append((d["frame_id"], d["simulation_time_s"], p.name))
ids = [r[0] for r in records]
print("retained metadata files:", len(records))
print("frame_id range: min =", min(ids), " max =", max(ids),
      " contiguous =", ids == list(range(min(ids), max(ids)+1)))
print("max simulation_time_s = %.6f" % max(r[1] for r in records))
PYEOF
```

**逐字输出**：

```text
directory entries: 57
retained metadata files: 28
frame_id range: min = 0  max = 27  contiguous = True
max simulation_time_s = 5.582825
min simulation_time_s = 0.182637
  frame 25: 5.1842474937438965  (frame_0000000025.json)
  frame 26: 5.382990837097168  (frame_0000000026.json)
  frame 27: 5.582825183868408  (frame_0000000027.json)
GATE1 2.000000 <= 5.582825 < 10.000000 -> True
GATE2 lowest retained frame == 0 -> True
latest.json frame_id = 27
```

| 要求 | 值 |
|---|---|
| 导出命令原文 | 见上 |
| 保留帧编号范围 | `frame_id` **0–27**，连续，28 份元数据（目录共 57 项 = 28 json + 28 jpg + `latest.json`；`latest.json` 的 `frame_id` = **27**，与最大保留帧一致） |
| 导出的数值 | `reported_sim_t` = **`5.582825183868408`** |

**门 1 PASS**：两侧余量约 `3.583 s` 与 `4.417 s`（本轮相邻帧约 `0.199 s`，故
COORD-007 §4.1 的一帧下界缺口对本次判定无实际影响；缺口本身仍需 R10 才能消除）。

## S.3 门 2 —— 最低保留帧必须恰为 `0`

最小 `frame_id` = **`0`** ✓，**门 2 PASS**。

## S.4 门 3 —— 冻结框匹配（用户目检）

```bash
.venv-yoloe/bin/python -m controller.track_loop --dump-frame 0 --output <scratch>/a4_frame0.jpg
```

退出码 0，导出图 **640×480**，叠加**已冻结**像素框 `(177, 195, 77, 73)`
（`min_side = 73 px`）——未重新框选、未重新估框、未做六位小数化、未读任何真值。

**用户目检结论（逐字）**：「**匹配**」→ **门 3 PASS**。现场未做任何调整。

**三门全部 PASS**，互不覆盖，故按 §3 步骤 2 末段在**保持暂停**下启动 tracker。

---

# T. arm A trial 4：tracker、完成握手与绑定分析（§3 步骤 2 末段–步骤 6）

## T.1 §3 步骤 0′ 第 2 步 —— 解释器绑定与实际命令行（**启动前**核对）

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
  --run-id p1-m3-body-001-arm-a-trial-4 \
  --init-frame 0 \
  --init-box 0.2765625 0.40625 0.1203125 0.15208333333333332 \
  --planned-duration-s 130.0 \
  --maximum-ground-range-m 1000.0 \
  --expires-after-s 1.0 \
  --poll-interval-s 0.02 \
  --body-policy hold \
  --body-planner-config config/p1-m3-body-001.json \
  --body-scenario-config config/scenario.default.json
```

命令行首 `~/TetheredDroneTracking/.venv-yoloe/bin/python` 与命令时刻预检
JSON 的 `interpreter.executable` **字符串逐字相等** → 步骤 0′ 第 2 步 **PASS**
（`-ef` 同文件佐证）。**除 `--run-id` 外 18 个参数逐字未改、未加、未减**；绝对/
相对拼写沿用 §G.5/§N.1 的既有披露，操作单未修改。

## T.2 启动成功（保持暂停下）

用户保持暂停期间启动：进程存活；`runtime/runs/p1-m3-body-001-arm-a-trial-4/`
由 `RunLogger` **create-once 新建**（证明 §2.12 第 7 项在启动时点仍成立），已出现
`frames.jsonl` 与 `manifest.json`。确认成功后才请用户恢复 Play；恢复后未再暂停、
未中途退出。**本轮无前驱门**（采集 ID 从未消耗），receipt 的 predecessor/attempt
键为空集，与 A3 同构。

## T.3 完成握手（§3 步骤 4 的三项 AND 门）

| # | 要求 | 实测 |
|---|---|---|
| 1 | 自然退出码 `0` | 后台通知逐字 `Background command "Start the trial-4 tracker" completed (exit code 0)`；`pgrep` 无命中 |
| 2 | final JSON 指向同一采集 ID 的 `summary.json` | 见下 |
| 3 | `metrics.final.json` 与 `summary.json` 均存在 | `ls` 实测均在 |

```json
{"qualification_metrics_error": null, "records": 652, "run_id": "p1-m3-body-001-arm-a-trial-4", "state": "TRACKING", "summary": "~/TetheredDroneTracking/runtime/runs/p1-m3-body-001-arm-a-trial-4/summary.json"}
```

**确认词的唯一机械来源**（只读）：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --validate-completion \
  --runtime runtime --run-id p1-m3-body-001-arm-a-trial-4 \
  --tracker-exit-code 0 --tracker-final-json '<上面的 final JSON 原文>'
```

退出码 **0**，stdout 逐字 `TRACKER_AUTO_COMPLETE_CONFIRMED`。

**BC-BODY1-29 顺序遵从**：确认词产生后的下一个动作即请用户退出；本节及其后所有
写入都在用户退出之后。用户退出并报告：**Console 无报错**。

## T.4 §3 步骤 5 绑定分析 —— **PASS**

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-a-trial-4
```

退出码 **0**，stderr 为空：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214, "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": false, "window_c_track_given_geom": 1.0}
```

只读复算 `--verify` 退出 **0**，逐字相同（仅 `verified` 为 `true`）。

## T.5 §3 步骤 6 记录（主结果 + BC-BODY1-30 披露）

| 量 | 值 |
|---|---|
| `h1.full_loop_c_geom` | **`0.5783206310103214`** |
| `h1.disposition` | **`WITHIN_RANGE`** |
| `window.c_track_given_geom` | `1.0`（`c_track` 同为 `1.0`） |
| 参考量（非门） | `online_aggregate_c_geom_reference = 0.6076419353485107`，`online_sensor_frames_reference = 650` |

臂 A 四次整圈 `C_geom`：A1 `0.5784550773737355`、A2 `0.5783188398250908`、
A3 `0.597146417669116`、A4 `0.5783206310103214`。**仅陈述，不构成任何判定**；
`--compare` 未跑、未授权，n=4 不支持任何主张。

**BC-BODY1-30 披露（只记录、不判定）**：

| 项 | 值 |
|---|---|
| tracker 最后一帧 `simulation_time_s` | `130.3839569091797`（`frame_id 651`，652 条帧记录） |
| Play 最后一条 truth `simulation_time_s` | `343.58197021484375`（**1718** 条） |
| **post-tracker 停留** | **`213.198013 s`** |
| 实测圈数 | `690.7031448290135 / 212.97056274847716` = **`3.243186`** |

**本轮是 F2 修法的第一例实弹承重（如实记录，归因权在接受角色）**：`3.243186` 圈
远超已撤下的 `>= 2P` 上界——在 revision 12 及更早的判据下，本次 Play 会与 trial 2
attempt 1（`3.6127` 圈）一样被判 `TRIAL_VOID_LOOP_DOMAIN_UPPER_BOUND_VIOLATION_
POST_TRACKER_DWELL`。接受轮 42 §A 撤下该上界并代之以两条域完整性门之后，
「恰好一个闭环」由 `[0, P)` 样本域承担：本轮两条门**零触发**（`unwrapped` 非递减、
闭环后无 `< P` 样本），`loop_frame_count` 仍是 **530**（与 A2 的 530、A3 的 529
同量级），`full_loop_c_geom` 与 A2 相差 `1.79e-6`。**本节不主张该修法因此被验证**
——那是接受角色与 M5 设计审查的判断；此处只登记事实。

`domains` 其余量：`window_frame_count 155`、`h2_grid_points 125`、
`h2_grid_spacing_m 0.5`、`measurement_window_m [0.0, 62.5]`，与冻结口径一致。

## T.6 现场清点

- 本次 run 目录 **11 份文件**（含 `m3_body_analysis.json`）。
- **A1/A2/A3 的正式 run 目录一字节未动**：Play 后三条 `--verify` 仍各自逐字返回
  `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116`；三处 post-run
  归档仍各 **6** 项；attempt-1 void hold 仍 **10** 份。
- 共享槽位为本次 Play 的产物，**原地保留、未移动**（下一次 trial 前的归档合同属
  下一轮接受角色）。

## T.7 边界声明（§S–§T 批次）

- 本批**消耗了**用户授权的唯一一次 Play 与采集 ID `p1-m3-body-001-arm-a-trial-4`；
  **arm A trial 5 与 arm B 五次仍未授权**，本批不申请，也未跑 `--compare`。
- **零阈值/指标口径/CLI/协议/代码/config/scenario/model 改动**；未修改操作单
  （BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`；对 `docs/unity-test-log.md`
  与 `docs/authorizations.md` 只读（(c) 记录在 Play 后零字节代录入库）。
- BC-BODY1-15 (d)：未依据 `0.5783206310103214` 调整任何参数。
- **交回接受角色**：trial 4 的 disposition 归属与里程碑账本记录；§T.5 的
  `213.198013 s` / `3.243186` 圈这一例是否需要在 M5 设计审查里与轮 50 的 decile
  观察合并处理。

---

# U. §2.13 A4 post-run 归档（操作单 revision 16，实现角色执行）

日期 2026-08-13。交接来源：接受轮 52（A4 判为有效、发出 revision 16 的 §2.13
归档合同）。**零 Play、零采集 ID 创建/消耗、零代码/测试/config/scenario/model
改动、零操作单改动；四个有效 run 目录一个都没动。** 批次开始时
`git status --porcelain` 为空。**本节不释放任何 Play。**

## U.1 归档执行

destination `runtime/test-results/p1-m3-body-001-arm-a-trial-4-post-run/` 移动前经
`Path.exists()` 确认**不存在**，由本批新建；六项逐一 `os.rename`，每次改名前再查
一次目标不存在（零覆盖证明），移动后逐项确认源已不存在。

**移动前实测 = 接受轮 52 §2.13 钉住表（6/6 相符）= 移动后实测**：

| 项 | 计数 / 行数 / 字节 | SHA-256（前 = 钉住 = 后） |
|---|---|---|
| `frames/` | **257** 项（0 隐藏） | 聚合 `281bb6d8f5b3657c203079654559d26cbb810c7eb231f8559b9120073d8a3b2c` |
| `m3_body_truth.jsonl` | **1718** 行 / 1755300 B | `f9c1a4889c0ba41f3058a8e8421b9961fda7084499e418eb5b7ba5a9a2c0e360` |
| `metrics.json` | 61 行 / 2085 B | `e5f547b71121b2a4e75a251003dfdc5880fc360648d8d4dd3bb4f82b5b116adf` |
| `body_command.json` | 10 行 / 207 B | `c1e5bf897cbd8a888773abb5ffc3c8463be0fee47d5b3fdff879192e8e0e3082` |
| `gimbal_command.json` | 15 行 / 341 B | `fc23a656f13c99da6bd96ab34ea9f38c5cb1a81b4190166a39350068b3cce62b` |
| `tracking_observation.json` | 18 行 / 454 B | `17d41cef97be83fbf0f319f390d92f2e8afa4cbe023357621d13faa5f1deecd6` |

- 归档目录内**恰 6 项**，名称与 §2.13 表逐字相符。
- 移动后只新建**空** `runtime/frames/`（实测 0 项），**未预建任何 run 目录**——
  `runtime/runs/p1-m3-body-001-arm-a-trial-5/` 实测**不存在**。
- **A4 正式 run 目录一字节未动**：仍 **11** 份文件（含 `m3_body_analysis.json`），
  目录聚合 SHA-256 移动前后相等。
- 位置风险沿 §2.9 登记，本批不另择路径、不新增动作。

## U.2 四个有效 run 的 `--verify` 复跑（§2.13 要求）

四条命令各退出 **0**，stdout 逐字：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214, "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
```

四个 run 目录自包含，归档 shared 侧对它们零影响。

## U.3 归档后的现场清点

| 对象 | 实测 |
|---|---|
| `runtime/frames/` | 存在且**空**（0 项） |
| 六个 shared 文件 | **全部不存在**（含 `scenario_config.json`，回退项目默认） |
| 四处 post-run 归档 | A1 / A2 / A3 / A4 各**恰 6 项** |
| attempt-1 void hold | 仍**恰 10 份文件** |
| 四个有效 run 目录 | 各 **11** 份，四条 `--verify` 见 §U.2 |
| `runs/p1-m3-body-001-arm-a-trial-5/` | **不存在**（下一轮 create-once 前置已就位，但**本节不释放任何 Play**） |

## U.4 边界声明（§U 批次）

- **零 Play、零采集 ID 创建/消耗**；arm A trial 5 与臂 B 五次仍需用户逐字 GO，
  本批不申请，也未做槽位轮换（那属下一次修订与 §2.0 四步）。
- **零删除、零覆盖、零分析**：1 次 `mkdir`（归档目录）、6 次 `os.rename`、1 次
  `mkdir runtime/frames`。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单
  （BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`；对 `docs/unity-test-log.md`
  与 `docs/authorizations.md` 只读。
- 本批写入仅两个路径：本证据文件与 `docs/current-status.md`。
- 复核范围：§U.1–§U.3 的 `runtime/` 现场事实（可由 `runtime/` 直接复算）与四条
  `--verify` 的逐字输出。

---

# V. A5 的 Play 前置（§2.14 核对 + §2.0 (b)，操作单 revision 17）

日期 2026-08-13，实现角色。交接来源：接受轮 53（trial 5 GO 入账、发出 revision 17）。
**本轮没有前置归档**——§2.13 已在上一批执行完毕（§U）。**零 Play、零采集 ID 创建/
消耗、零 `runtime/` 写入、零代码/测试/config/scenario/model 改动、零操作单改动。**
批次开始与结束时 `git status --porcelain` 均为空。

## V.1 §2.14 七项 Play 前只读核对：**77 条机械核对，77 PASS / 0 FAIL**

期望值取自 §2.5 第 4–7 项原表、`…-arm-a-trial-1.md` §B/§F.1/§H.1/§I.1/§N.1、
§2.8 的十文件 hold 集合与三钉住 SHA，以及 §2.9/§2.11/§2.13 三份归档钉住表。

| §2.14 项 | 核对内容 | 结果 |
|---|---|---|
| 1 | 六个 shared 文件 | 均**不存在** ✓（6/6） |
| 2 | `runtime/frames/` 存在且为空 | 存在、**0 项** ✓（2/2） |
| 3 | 四处旧 hold | **257 / 93 / 109 / 257** + 全部 SHA-256；attempt-3 run hold 仍恰两文件 ✓（21/21） |
| 4 | **四个正式 run 目录** | A1/A2/A3/A4 各**恰 11 份**且各含 `m3_body_analysis.json` ✓；四条 `--verify` 各退出 0 并逐字返回 `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` / `0.5783206310103214` ✓（8/8 + 四条 verify） |
| 5 | **四处 post-run 归档** | 各**恰 6 项**、`frames/` 各 **257** 项，四个聚合 SHA-256 依次为 `ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` ✓；A2/A3/A4 的五个单文件逐项等于各自钉住表 ✓（27/27） |
| 6 | 活动标记 + attempt-1 void hold | 八个标记均不存在；hold 仍**恰 10 份、零隐藏项**、三钉住 SHA 相等 ✓（12/12） |
| 7 | **A5 create-once 前置** | `runtime/runs/p1-m3-body-001-arm-a-trial-5/` **不存在** ✓（1/1） |

本节与接受轮 53 §B 的 58 条实测**互为独立复算**，结论一致。

## V.2 §2.0 (b) 报告（测量时点）

```text
$ git rev-parse HEAD
cd66f855046b8b3a5675cb23a89c41ebf0cf96f7

$ git status --porcelain
（空输出）
```

基线运行时解析：`grep -m1 '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md` →
**`07bb8a47a9e41581c1450a7b0335e501ffdaaec9`**。
`git diff --name-only 07bb8a4..HEAD` = **8 个路径**，与 §O.3/§R.3 **同一集合**
（提案、复核、操作单、本证据文件、里程碑账本、授权账本、Unity 日志、状态板），
只是内容随轮 52/53 与 A4 记录增长；无新增路径类别。

**测量侧逐字节相同**：

```bash
$ git diff --name-only 07bb8a4..HEAD -- controller/ Assets/ config/ \
    ProjectSettings/ Packages/packages-lock.json tools/ tests/
（空输出）
```

自 Review round 7 的候选起，代码与配置侧**一个字节未动**——A1…A4 四次采集与本轮
即将进行的 A5 全部跑在同一份已复核代码上。

**PLAY_GOVERNING 子集 = 恰 1 条**：操作单，现为 **revision 17**（见 §V.4 第 1 条）。

## V.3 §3 步骤 0 环境预检与步骤 0′ 第 1 步

退出码 **0**，`status = "PASS"`，`side_effect_identity.unchanged = true`。与 §R.4
记录的那份逐字段比对：**唯一差异**是 `side_effect_identity` 前后两份
`run_directories` 各新增 `p1-m3-body-001-arm-a-trial-4`（30 → 31），其余字段完全
相同；`p1-m3-body-001-arm-a-trial-5` **不在**其中，与 §2.14 第 7 项一致。
完整 stdout JSON（逐字）：

```json
{
  "constructors": {
    "dinov2_embedder": "controller.reanchor_models.DinoV2Embedder",
    "nanotrack_tracker": "controller.trackers.NanoTrackV2Tracker",
    "yoloe_proposer": "controller.reanchor_models.YoloeProposer"
  },
  "interpreter": {
    "executable": "~/TetheredDroneTracking/.venv-yoloe/bin/python",
    "prefix": "~/TetheredDroneTracking/.venv-yoloe",
    "python_version": "3.12.13"
  },
  "mode": "reanchor-preflight",
  "nanotrack": {
    "backend": "opencv-dnn-default/cpu",
    "model_sha256": {
      "backbone": "530bdd0cd00f19afab79a863e71ba71e3312395a5dc9151af675082bdaaa2fc4",
      "neckhead": "0d8c0637be849f092cc7236cae02e55c8b9455ebe37ba50601d6115db4247cd9"
    },
    "name": "nanotrack-v2",
    "opencv_package_pin": "opencv-contrib-python==5.0.0.93",
    "opencv_version": "5.0.0",
    "preprocessing_id": "opencv-tracker-nano-5.0.0-default-v1"
  },
  "packages": {
    "cv2": {
      "pin": "5.0.0",
      "pin_source": "nanotrack spec opencv.tested_version",
      "raw": "5.0.0"
    },
    "torch": {
      "pin": "2.13.0",
      "pin_source": "reanchor config runtime.torch_pin",
      "raw": "2.13.0"
    },
    "torchvision": {
      "pin": "0.28.0",
      "pin_source": "reanchor config runtime.torchvision_pin",
      "raw": "0.28.0"
    },
    "ultralytics": {
      "pin": "8.4.104",
      "pin_source": "reanchor config runtime.ultralytics_pin",
      "raw": "8.4.104"
    }
  },
  "reanchor_config": {
    "carrier": "minimal-triple-gated-re-anchor",
    "device": "cpu",
    "path": "config/detector-reanchor.models.json",
    "schema_version": "tethered-detector-reanchor/v1",
    "sha256": "593734d67ada73a0304d67d27c6ae536be616d2180f744336b85ff6e0ac706d2"
  },
  "side_effect_identity": {
    "after": {
      "guarded_files": {
        "runtime/body_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/gimbal_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/metrics.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/tracking_observation.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        }
      },
      "run_directories": [
        "p1-detect-001-qual-1",
        "p1-detect-001-qual-2",
        "p1-detect-001-qual-3",
        "p1-m3-body-001-arm-a-trial-1-attempt-4",
        "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold",
        "p1-m3-body-001-arm-a-trial-2-attempt-2",
        "p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold",
        "p1-m3-body-001-arm-a-trial-3",
        "p1-m3-body-001-arm-a-trial-4",
        "p1-track-follow",
        "p1-track-follow-attempt1",
        "p1-track-nadir",
        "p1-track-occlusion",
        "rate20-calib",
        "rate20-follow-r1",
        "rate20-follow-r2",
        "rate20-follow-r3",
        "rate20-nadir-r1",
        "rate20-nadir-r2",
        "rate20-nadir-r3",
        "rate5-calib",
        "rate5-follow-r1",
        "rate5-follow-r2",
        "rate5-follow-r3",
        "rate5-nadir-r1",
        "rate5-nadir-r2",
        "rate5-nadir-r3",
        "rs2-pilot",
        "rs2-r20-follow-1",
        "rs2-r20-follow-2",
        "rs2-r20-follow-3"
      ]
    },
    "before": {
      "guarded_files": {
        "runtime/body_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/gimbal_command.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/metrics.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        },
        "runtime/tracking_observation.json": {
          "present": false,
          "sha256": null,
          "size_bytes": null
        }
      },
      "run_directories": [
        "p1-detect-001-qual-1",
        "p1-detect-001-qual-2",
        "p1-detect-001-qual-3",
        "p1-m3-body-001-arm-a-trial-1-attempt-4",
        "p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold",
        "p1-m3-body-001-arm-a-trial-2-attempt-2",
        "p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold",
        "p1-m3-body-001-arm-a-trial-3",
        "p1-m3-body-001-arm-a-trial-4",
        "p1-track-follow",
        "p1-track-follow-attempt1",
        "p1-track-nadir",
        "p1-track-occlusion",
        "rate20-calib",
        "rate20-follow-r1",
        "rate20-follow-r2",
        "rate20-follow-r3",
        "rate20-nadir-r1",
        "rate20-nadir-r2",
        "rate20-nadir-r3",
        "rate5-calib",
        "rate5-follow-r1",
        "rate5-follow-r2",
        "rate5-follow-r3",
        "rate5-nadir-r1",
        "rate5-nadir-r2",
        "rate5-nadir-r3",
        "rs2-pilot",
        "rs2-r20-follow-1",
        "rs2-r20-follow-2",
        "rs2-r20-follow-3"
      ]
    },
    "checked": [
      "runtime/runs direct child directory names",
      "runtime/body_command.json present/size/sha256",
      "runtime/gimbal_command.json present/size/sha256",
      "runtime/tracking_observation.json present/size/sha256",
      "runtime/metrics.json present/size/sha256"
    ],
    "unchanged": true
  },
  "status": "PASS"
}
```

**步骤 0′ 第 1 步**：`interpreter.executable` 逐字值

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python
```

**步骤 0′ 第 2 步尚未执行**（本批不启动 tracker）。

## V.4 交回接受角色 / 未验证项

1. **PLAY_GOVERNING 恰 1 条 = 操作单 revision 17 自身**，与前几轮同构；其具名
   disposition 由接受角色在 (c) 记录中确认，本角色如实报告、不自行判定。
   revisions 13–17 与轮 47/50/52/53 的操作单改动**仍欠一轮逐文件复核**。
2. **测量时点 HEAD ≠ 发令时点 HEAD**：本批（本节 + 状态板）须在 (c) 之前提交，
   **(c) 的 HEAD/status 必须由接受角色在写入时点自取**。本批只动两个文档路径，
   均不在 PLAY_GOVERNING。
3. **§2.14 需在发令时刻复查**（前几轮均因接受角色的新提交而重跑过）。
4. **A5 无前驱门**：`p1-m3-body-001-arm-a-trial-5` 从未创建或消耗，两个
   `_check_a*_predecessor_hold` 都不触发，receipt 不会有 predecessor 字段。
5. **本批不产生 Unity 用例**，不申领 `UNITY_NA`。
6. **A5 是臂 A 的最后一次**：跑完后臂 A 5/5，但 `--compare` 仍需十次齐备与单独
   授权，臂 B 五次一次都未获 GO。

## V.5 §V 批次边界声明

- **零 Play、零采集 ID 创建/消耗**；`runs/p1-m3-body-001-arm-a-trial-5/` 未预建。
- **零 `runtime/` 写入**：本批只做只读读取（`open(..., 'rb')`/`stat`）、四条
  `--verify`（写盘前返回）与预检（自证 `unchanged=true`）；无 `mv`/`rm`/`mkdir`。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单
  （BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`；对 `docs/unity-test-log.md`
  与 `docs/authorizations.md` 只读。
- 本批写入仅两个路径：本证据文件与 `docs/current-status.md`。
- 复核范围：§V.1–§V.3 的 `runtime/` 现场事实、五条只读命令的逐字输出、§V.2 的
  基线归因。

---

# W. arm A trial 5 的 Play 与三个独立硬门（§3 步骤 1–2，**启动 tracker 之前**落盘）

日期 2026-08-13。用户按接受轮 53/54 的 §2.0 (c) 记录（`docs/unity-test-log.md`，
HEAD `0c514f7`）进入 Play **恰一次**。采集 ID `p1-m3-body-001-arm-a-trial-5`
（自身即 canonical slot，从未被消耗，**本轮无前驱门参与**）。**本次是臂 A 的
第 5 次，也是最后一次。**

发令时刻三项复核（用户进 Play 之前实测）：

- **§2.0 (d)**：`git diff --name-only` 逐字只有 `docs/unity-test-log.md` ✓
- **§3 步骤 0 预检（命令时刻复跑）**：退出 0、`status=PASS`、
  `side_effect_identity.unchanged=true`，stdout JSON 与 §V.3 记录的那份**逐字节
  相同** ✓
- **§2.14 七项复跑**：**77/77 PASS**（轮 54 的提交改变了 HEAD，按 §V.4 第 3 条
  重取，结论不变）✓

## W.1 用户进入 Play 并暂停（口报如实记录，**不作判据**）

用户报告逐字：**「已暂停」**——未报时刻（本载体无计时 HUD，§M.1 已披露）。

## W.2 门 1 —— 暂停窗口（`2.000000 <= reported_sim_t < 10.000000`）

**导出命令原文**（只读；只解析保留帧元数据 JSON，不读任何真值文件）：

```bash
.venv-yoloe/bin/python - <<'PYEOF'
import json, pathlib
frames = pathlib.Path("runtime/frames")
records = []
for p in sorted(frames.glob("frame_*.json")):
    d = json.loads(p.read_text())
    records.append((d["frame_id"], d["simulation_time_s"], p.name))
ids = [r[0] for r in records]
print("retained metadata files:", len(records))
print("frame_id range: min =", min(ids), " max =", max(ids),
      " contiguous =", ids == list(range(min(ids), max(ids)+1)))
print("max simulation_time_s = %.6f" % max(r[1] for r in records))
PYEOF
```

**逐字输出**：

```text
directory entries: 57
retained metadata files: 28
frame_id range: min = 0  max = 27  contiguous = True
max simulation_time_s = 5.582473
min simulation_time_s = 0.184249
  frame 25: 5.180578708648682  (frame_0000000025.json)
  frame 26: 5.383277416229248  (frame_0000000026.json)
  frame 27: 5.582472801208496  (frame_0000000027.json)
GATE1 2.000000 <= 5.582473 < 10.000000 -> True
GATE2 lowest retained frame == 0 -> True
latest.json frame_id = 27
```

| 要求 | 值 |
|---|---|
| 导出命令原文 | 见上 |
| 保留帧编号范围 | `frame_id` **0–27**，连续，28 份元数据（目录共 57 项；`latest.json` 的 `frame_id` = **27**，与最大保留帧一致） |
| 导出的数值 | `reported_sim_t` = **`5.582472801208496`** |

**门 1 PASS**：两侧余量约 `3.582 s` 与 `4.418 s`（相邻帧约 `0.199 s`）。

## W.3 门 2 —— 最低保留帧必须恰为 `0`

最小 `frame_id` = **`0`** ✓，**门 2 PASS**。

## W.4 门 3 —— 冻结框匹配（用户目检）

```bash
.venv-yoloe/bin/python -m controller.track_loop --dump-frame 0 --output <scratch>/a5_frame0.jpg
```

退出码 0，导出图 **640×480**，叠加**已冻结**像素框 `(177, 195, 77, 73)`
（`min_side = 73 px`）——未重新框选、未重新估框、未做六位小数化、未读任何真值。

**用户目检结论（逐字）**：「**匹配**」→ **门 3 PASS**。现场未做任何调整。

**三门全部 PASS**，互不覆盖，故按 §3 步骤 2 末段在**保持暂停**下启动 tracker。

---

# X. arm A trial 5：tracker、完成握手与绑定分析（§3 步骤 2 末段–步骤 6）

## X.1 §3 步骤 0′ 第 2 步 —— 解释器绑定与实际命令行（**启动前**核对）

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
  --run-id p1-m3-body-001-arm-a-trial-5 \
  --init-frame 0 \
  --init-box 0.2765625 0.40625 0.1203125 0.15208333333333332 \
  --planned-duration-s 130.0 \
  --maximum-ground-range-m 1000.0 \
  --expires-after-s 1.0 \
  --poll-interval-s 0.02 \
  --body-policy hold \
  --body-planner-config config/p1-m3-body-001.json \
  --body-scenario-config config/scenario.default.json
```

命令行首 `~/TetheredDroneTracking/.venv-yoloe/bin/python` 与命令时刻预检
JSON 的 `interpreter.executable` **逐字相等** → 步骤 0′ 第 2 步 **PASS**。
**除 `--run-id` 外 18 个参数逐字未改、未加、未减**；拼写处置沿用 §G.5/§N.1 披露。

## X.2 启动成功（保持暂停下）

进程存活；`runtime/runs/p1-m3-body-001-arm-a-trial-5/` 由 `RunLogger` **create-once
新建**（证明 §2.14 第 7 项在启动时点仍成立）。确认后才请用户恢复 Play；恢复后未再
暂停、未中途退出。**本轮无前驱门**（ID 从未消耗），receipt 的 predecessor/attempt
键为空集。

## X.3 完成握手（§3 步骤 4 的三项 AND 门）

| # | 要求 | 实测 |
|---|---|---|
| 1 | 自然退出码 `0` | 后台通知逐字 `Background command "Start the trial-5 tracker" completed (exit code 0)`；`pgrep` 无命中 |
| 2 | final JSON 指向同一采集 ID 的 `summary.json` | 见下 |
| 3 | `metrics.final.json` 与 `summary.json` 均存在 | `ls` 实测均在 |

```json
{"qualification_metrics_error": null, "records": 652, "run_id": "p1-m3-body-001-arm-a-trial-5", "state": "TRACKING", "summary": "~/TetheredDroneTracking/runtime/runs/p1-m3-body-001-arm-a-trial-5/summary.json"}
```

**确认词的唯一机械来源**（只读）：`--validate-completion --runtime runtime --run-id
p1-m3-body-001-arm-a-trial-5 --tracker-exit-code 0 --tracker-final-json '<上面原文>'`
→ 退出码 **0**，stdout 逐字 `TRACKER_AUTO_COMPLETE_CONFIRMED`。

**BC-BODY1-29 顺序遵从**：确认词产生后的下一个动作即请用户退出；证据在用户退出
之后才写。用户退出并报告：**Console 无报错**。

## X.4 §3 步骤 5 绑定分析 —— **PASS**

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-a-trial-5
```

退出码 **0**，stderr 为空：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783243208518966, "run_id": "p1-m3-body-001-arm-a-trial-5", "verified": false, "window_c_track_given_geom": 1.0}
```

只读复算 `--verify` 退出 **0**，逐字相同（仅 `verified` 为 `true`）。

## X.5 §3 步骤 6 记录（主结果 + BC-BODY1-30 披露）

| 量 | 值 |
|---|---|
| `h1.full_loop_c_geom` | **`0.5783243208518966`** |
| `h1.disposition` | **`WITHIN_RANGE`** |
| `window.c_track_given_geom` | `1.0`（`c_track` 同为 `1.0`） |
| 参考量（非门） | `online_aggregate_c_geom_reference = 0.6076168417930603`，`online_sensor_frames_reference = 650` |

**BC-BODY1-30 披露（只记录、不判定）**：

| 项 | 值 |
|---|---|
| tracker 最后一帧 `simulation_time_s` | `130.38314819335938`（`frame_id 651`，652 条帧记录） |
| Play 最后一条 truth `simulation_time_s` | `146.18345642089844`（**731** 条） |
| **post-tracker 停留** | **`15.800308 s`** |
| 实测圈数 | `293.7980499321785 / 212.97056274847716` = **`1.379524`** |

两条域完整性门零触发；`loop_frame_count` **530**、`window_frame_count` **155**，
与冻结口径一致。

## X.6 臂 A 五次全部就位（**只陈述事实，不构成任何判定**）

本次是臂 A 的第 5 次，臂 A 因此 **5/5 完成**。Play 后五条 `--verify` 各退出 0 并
逐字复现：

| canonical slot | 采集 ID | `full_loop_c_geom` |
|---|---|---|
| trial 1 | `…-arm-a-trial-1-attempt-4` | `0.5784550773737355` |
| trial 2 | `…-arm-a-trial-2-attempt-2` | `0.5783188398250908` |
| trial 3 | `…-arm-a-trial-3` | `0.597146417669116` |
| trial 4 | `…-arm-a-trial-4` | `0.5783206310103214` |
| trial 5 | `…-arm-a-trial-5` | `0.5783243208518966` |

五次全部 `WITHIN_RANGE`、窗口 `C_track|geom` 全为 `1.0`。**观察（如实登记，不作
主张、不作归因）**：四次落在 `0.57832–0.57846` 的 `1.4e-4` 带内，A3 高出约
`0.019`——与接受轮 50 已登记的「差异集中在单一遮挡边界十分位」是同一现象的第五个
数据点。**本节不对该现象作任何解释或统计推断**；H1/H2 的正式比较必须等十次
（含臂 B 五次）齐备后由 `--compare` 产出，且 `--compare` 尚未授权。
BC-BODY1-15 (d) 的反调参纪律继续适用：不得据此调整任何参数、阈值、窗口或载体。

## X.7 现场清点

- 本次 run 目录 **11 份文件**（含 `m3_body_analysis.json`）。
- **A1–A4 的正式 run 目录一字节未动**（Play 后五条 `--verify` 见 §X.6）；四处
  post-run 归档仍各 **6** 项；attempt-1 void hold 仍 **10** 份。
- A5 的共享槽位为本次 Play 的产物，**原地保留、未移动**——归档合同属下一轮接受
  角色（先例 §2.9/§2.11/§2.13）。

## X.8 边界声明（§W–§X 批次）

- 本批**消耗了**用户授权的唯一一次 Play 与采集 ID `p1-m3-body-001-arm-a-trial-5`；
  **臂 B 五次仍全部未授权**，本批不申请，也未跑 `--compare`。
- **零阈值/指标口径/CLI/协议/代码/config/scenario/model 改动**；未修改操作单
  （BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`；对 `docs/unity-test-log.md`
  与 `docs/authorizations.md` 只读（(c) 记录在 Play 后零字节代录入库）。
- **交回接受角色**：trial 5 的 disposition 归属与里程碑账本记录（臂 A 5/5）、
  A5 shared 槽位的归档合同，以及臂 A 完成后的下一步（臂 B 首次采集需用户新 GO；
  `--compare` 需十次齐备且单独授权）。§X.6 的五点分布是否并入 M5 设计审查登记项，
  同样由接受角色裁定。

---

# Y. §2.15 A5 post-run 归档（操作单 revision 18，实现角色执行）

日期 2026-08-13。交接来源：接受轮 55（A5 判为有效、臂 A 5/5、发出 revision 18 的
§2.15 归档合同）。**零 Play、零采集 ID 创建/消耗、零代码/测试/config/scenario/
model 改动、零操作单改动；五个有效 run 目录一个都没动。** 批次开始时
`git status --porcelain` 为空。**本节不释放任何 Play。**

## Y.1 归档执行

destination `runtime/test-results/p1-m3-body-001-arm-a-trial-5-post-run/` 移动前经
`Path.exists()` 确认**不存在**（与轮 55 实测一致），由本批新建；六项逐一
`os.rename`，每次改名前再查一次目标不存在（零覆盖证明），移动后逐项确认源已不存在。

**移动前实测 = 接受轮 55 §2.15 钉住表（6/6 相符）= 移动后实测**：

| 项 | 计数 / 行数 / 字节 | SHA-256（前 = 钉住 = 后） |
|---|---|---|
| `frames/` | **257** 项（0 隐藏） | 聚合 `9dc67a7613201329b038ba6e425bc2e7aaa4ec7c9d196b09391c71624481a62b` |
| `m3_body_truth.jsonl` | **731** 行 / 751891 B | `a93ca5e0b2f67d164d8bfd079826ebef4d5328bb8e165e5362fe73f6c7bc80eb` |
| `metrics.json` | 61 行 / 2101 B | `1804dd6fb281e0a81bb2ace43886884b83861e2f324f3c20d4b2600ac50d4aa5` |
| `body_command.json` | 10 行 / 208 B | `c98b0b758935e7d0189614e5206713691d34123ab68a1f4af86388f100744256` |
| `gimbal_command.json` | 15 行 / 339 B | `02a3299abd8a862cbbc6d56a3e1f67b4529c8cf794a1e94fc988bb137146c5e6` |
| `tracking_observation.json` | 18 行 / 447 B | `215549ce0f94a859c548778fa3068a2e607aaac7176944d32d88a351b22f0649` |

- 归档目录内**恰 6 项**，名称与 §2.15 表逐字相符。
- 移动后只新建**空** `runtime/frames/`（实测 0 项），**未预建任何 run 目录**——
  `runtime/runs/p1-m3-body-001-arm-b-trial-1/` 实测**不存在**。
- **A5 正式 run 目录一字节未动**：仍 **11** 份文件（含 `m3_body_analysis.json`），
  目录聚合 SHA-256 移动前后相等。
- `runtime/scenario_config.json` 全程不存在，无需处理（与 §2.15 注一致）。

## Y.2 五个有效 run 的 `--verify` 复跑（§2.15 要求）

五条命令各退出 **0**，stdout 逐字返回各自冻结值：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214, "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783243208518966, "run_id": "p1-m3-body-001-arm-a-trial-5", "verified": true, "window_c_track_given_geom": 1.0}
```

五个 run 目录自包含，归档 shared 侧对它们零影响。**臂 A 的五份证据到此全部
归档完毕、全部可复算。**

## Y.3 归档后的现场清点

| 对象 | 实测 |
|---|---|
| `runtime/frames/` | 存在且**空**（0 项） |
| 六个 shared 文件 | **全部不存在**（含 `scenario_config.json`） |
| 五处 post-run 归档 | A1 / A2 / A3 / A4 / A5 各**恰 6 项** |
| attempt-1 void hold | 仍**恰 10 份文件** |
| 五个有效 run 目录 | 各 **11** 份，五条 `--verify` 见 §Y.2 |
| `runs/p1-m3-body-001-arm-b-trial-1/` | **不存在**（**本节不释放任何 Play**） |

## Y.4 边界声明（§Y 批次）

- **零 Play、零采集 ID 创建/消耗**；臂 B 五次仍需用户逐字 GO，本批不申请，也未做
  槽位或 `--body-policy` 轮换（那属下一次修订与 §2.0 四步）；`--compare` 需十次
  齐备并单独授权，本批未跑。
- **零删除、零覆盖、零分析**：1 次 `mkdir`（归档目录）、6 次 `os.rename`、1 次
  `mkdir runtime/frames`。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单
  （BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`；对 `docs/unity-test-log.md`
  与 `docs/authorizations.md` 只读。
- 本批写入仅两个路径：本证据文件与 `docs/current-status.md`。
- 复核范围：§Y.1–§Y.3 的 `runtime/` 现场事实与五条 `--verify` 的逐字输出。
