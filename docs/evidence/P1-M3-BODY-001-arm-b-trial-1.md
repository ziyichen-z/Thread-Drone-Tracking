# P1-M3-BODY-001 arm B trial 1 证据（操作单 revision 19 / 首次跨臂轮换）

**范围**：用户 2026-08-14 授权的**恰好一次** arm B trial 1
（GO「1 + 3 合并执行，明确拒绝 2」，接受轮 58 入账 `docs/authorizations.md`）。
执行合同 = `docs/evidence/P1-M3-BODY-001-1c-preflight.md` **revision 19**。
采集 ID `p1-m3-body-001-arm-b-trial-1`（canonical slot 即其自身，从未消耗，
**无替代 ID、无 predecessor 门**），配对搭档 A1
（`p1-m3-body-001-arm-a-trial-1-attempt-4`）。

**状态**：§A 已完成（§2.16 九项 + §2.0 (b) + §3 步骤 0/0′ 第 1 步，
**零 Play、零采集 ID、零 `runtime/` 写入**）；§2.0 (c) 记录归接受角色，
(d) 与 §3 步骤 1 之后各节待 Play 时/后填写。

---

# A. B1 的 Play 前置（§2.16 核对 + §2.0 (b) + §3 步骤 0/0′ 第 1 步）

日期 2026-08-14，实现角色。交接来源：接受轮 58（B1 GO 入账、发出 revision 19、
预登记 H2-CEILING）。**本轮没有前置归档**——§2.15 已于 2026-08-14 由 `e68827d`
执行完毕。**零 Play、零采集 ID 创建/消耗、零 `runtime/` 写入、零代码/测试/
config/scenario/model 改动、零操作单改动（BC-BODY1-21/-22）。** 批次开始与结束时
`git status --porcelain` 均为空。

## A.1 §2.16 九项 Play 前只读核对：**115 条机械核对，115 PASS / 0 FAIL**

期望值取自操作单 §1（corridor 钉住行）、§2.5 第 4–7 项原表、§2.8 的十文件 hold
集合与三钉住 SHA、`…-arm-a-trial-1.md` §B/§F.1/§H.1/§I.1/§N.1，以及
§2.9/§2.11/§2.13/§2.15 四份归档钉住表。核对脚本只做
`open(..., 'rb')`/`stat`/`iterdir`，落在会话 scratchpad，不在仓库内。

| §2.16 项 | 核对内容 | 结果 |
|---|---|---|
| 1 | 六个 shared 文件 | 均**不存在** ✓（6/6；含 `scenario_config.json`——SCENE-004 override 全批次保持移开） |
| 2 | `runtime/frames/` 存在且为空 | 存在、**0 项** ✓（2/2，由 §2.15 重建） |
| 3 | 四处旧 hold | 帧计数 **257 / 93 / 109 / 257** ✓；1b 五个 SHA、attempt-1/-2 truth（46 / 54 行）与 metrics、attempt-3 的 truth（627 行）/metrics/三个发布 hold 全部相等 ✓；attempt-3 的 run hold 仍**恰两文件**（`frames.jsonl` 755 行 `8f9f3551…`、`manifest.json` 207 行 `e5caa982…`）✓（26/26） |
| 4 | **五个正式 run 目录** | A1…A5 各**恰 11 份**且各含 `m3_body_analysis.json` ✓（10/10）；五条 `--verify` 见 §A.2 |
| 5 | **五处 post-run 归档** | 各**恰 6 项**、`frames/` 各 **257** 项、五个聚合 SHA-256 依次为 `ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` / `9dc67a76…a62b` ✓；五组各五个单文件的行数/字节/SHA-256 逐项等于各自钉住表 ✓（40/40） |
| 6 | 活动标记 + attempt-1 void hold | 八个具名标记均不存在 ✓；void hold 仍**恰 10 份**、文件名集合逐字等于 §2.8 冻结十项、**零隐藏项**、三钉住 SHA 相等 ✓（14/14） |
| 7 | **B1 create-once 前置** | `runtime/runs/p1-m3-body-001-arm-b-trial-1/` **不存在** ✓（1/1） |
| 8 | **臂 B 专属：corridor 工件** | 实测 SHA-256 = config `artifact_sha256` = §1 钉住值 `9e2956ad…c800` ✓；`instance_count` **779** ✓，且工件内实际棱柱条目数也是 **779** ✓（5/5） |
| 9 | **臂 B 专属：臂位机械复核** | `_expected_policy('…-arm-b-trial-1')` = `threshold` ✓；`POLICY_PLANNER['threshold']` = `threshold-corridor-v1` ✓；`expected_acquisition_ids('b')` 五槽且 `[0]` 逐字相等 ✓；`canonical_trial_id()` 返回同名 ✓；`…-attempt-1`/`…-attempt-2`/`…-trial-6` 三个变体在 `canonical_trial_id()` 与 `_expected_policy()` 两处**均**抛 `run_id_not_frozen_trial:<id>` ✓（11/11） |

分项计数：1: 6/6、2: 2/2、3: 26/26、4: 10/10、5: 40/40、6: 14/14、7: 1/1、
8: 5/5、9: 11/11。本节与接受轮 58 的独立实跑**互为独立复算**，结论一致。

**第 8 项的机制自查（读码确认，非新增门）**：`controller/track_loop.py` 的
`elif policy_name == "threshold":` 分支在 `policy.get("tether_corridor_check")`
为真时才比对该哈希，不符即 `raise ValueError("corridor artifact hash does not
match the config")`。冻结配置 `config/p1-m3-body-001.json` 的
`policy.tether_corridor_check` 实测为 **`true`**，故该启动门在本轮**确实会触发**
——这是操作单 §1「臂 B 专属启动门」说法成立的前提，本角色亲自读码确认。

## A.2 五条只读 `--verify` 复算（§2.16 第 4 项）

五条命令逐条执行，**全部退出码 0**，stdout 逐字复现各自冻结值：

```text
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214, "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783243208518966, "run_id": "p1-m3-body-001-arm-a-trial-5", "verified": true, "window_c_track_given_geom": 1.0}
```

A1 与 A2 两条各另读 run 目录之外的 predecessor hold（BC-BODY1-27），两个前驱门
都在 `if verify:` 之前无条件执行；A3/A4/A5 三条只读各自 run 目录，receipt 不含
predecessor 字段。**臂 A 五份证据在本轮仍全部可复算，一个字节未动。**

## A.3 §2.16 第 8/9 项命令块（逐字执行，逐字输出）

按操作单 §2.16 的命令块原文执行（只读，不写任何文件），退出码 **0**：

```text
corridor sha256 = 9e2956ad93a4a81cf638a913b9c806e1a316616bf090b125641d3f5c0b7fc800
pin             = 9e2956ad93a4a81cf638a913b9c806e1a316616bf090b125641d3f5c0b7fc800
instance_count  = 779
_expected_policy = threshold
planner name     = threshold-corridor-v1
ids(b)[0]        = p1-m3-body-001-arm-b-trial-1
```

前两行逐字相等且等于 §1 的 `9e2956ad…c800`，`instance_count` 为 779；后三行依次
为 `threshold` / `threshold-corridor-v1` / `p1-m3-body-001-arm-b-trial-1`——与
操作单写死的期望**逐字一致**。

## A.4 §2.0 (b) 报告（测量时点）

```text
$ git rev-parse HEAD
03cb2b58f88acc3cfd8370ff02c7696e99b23afe

$ git status --porcelain
（空输出）
```

基线运行时解析（COORD-007 R7「可派生标识禁手写」，例示按复核轮 8 F4 更正后的
形式取**文件末行 = 最新一行**）：

```bash
$ grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md | tail -1
passed_candidate: 408acd7b39054e0a92eb3f0f9df5d4713b16f34a
```

故 `<BASE>` = **`408acd7b39054e0a92eb3f0f9df5d4713b16f34a`**（复核轮 9 的通过候选）。

```bash
$ git diff --name-only 408acd7..HEAD
docs/authorizations.md
docs/current-status.md
docs/evidence/P1-M3-BODY-001-1c-preflight.md
docs/evidence/P1-M3-BODY-001-arm-a-trial-2.md
docs/implementation-status.md
docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md
docs/reviews/P1-M3-BODY-001.md
```

**七个路径，全部是文档**，由区间内四条提交产生：`8af1d37`（复核轮 9）、
`e68827d`（§2.15 A5 归档）、`195f2c2`（接受轮 57）、`03cb2b5`（接受轮 58）。
**本轮的路径集合与计数与历次都不同**，§2.0 (b) 注中 trial 2 的「七个路径 +
inert 归因」是历史例示，按该注的明文要求**不套用**，本节现算。

**测量侧逐字节相同**：

```bash
$ git diff --name-only 408acd7..HEAD -- controller/ Assets/ config/ \
    ProjectSettings/ Packages/packages-lock.json tools/ tests/
（空输出）
```

自复核轮 9 的通过候选起，代码与配置侧**一个字节未动**；再往前推，臂 A 五次采集
自 Review round 7 的 `07bb8a4` 起也跑在同一份已复核代码上，故 **B1 与 A1…A5 将
运行在同一份测量侧字节上**——这正是 A/B 配对成立所要求的。

**PLAY_GOVERNING 子集 = 恰 1 条**：操作单
`docs/evidence/P1-M3-BODY-001-1c-preflight.md`，现为 **revision 19**（跨臂轮换）。
其具名归因已由接受轮 58 在操作单 §2.0 (b) 注内给出——
`RUNBOOK_DELTA_ARM_ROTATION_A_TO_B_SEMANTIC_BY_DESIGN_UNDER_GO_NO_GATE_RELAXATION_REVIEW_DEBT_REGISTERED`
——本角色**如实报告、不自行判定**，也不套用已被该注明文禁止的
`NO_SEMANTIC_CHANGE` 旧名。

## A.5 §3 步骤 0 环境预检

命令（§1 冻结的唯一合法解释器）：

```bash
.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json
```

**退出码 `0`**，stdout `status = "PASS"`，`side_effect_identity.unchanged = true`，
且 `before` 与 `after` 两块实测**完全相等**。stdout 可直接 `json.loads` 为**单个**
JSON 对象（已实跑确认）。stderr 有与前几轮同类的依赖噪声（OpenCV
`setPreferableTarget` 两行 WARN、`tifffile` 缺失提示、DINOv2 三条 xFormers
`UserWarning`），不影响退出码与 JSON；如实记录。

**与 A5 那轮记录的预检 JSON（`docs/evidence/P1-M3-BODY-001-arm-a-trial-2.md`
§V.3）逐字段机械比对**：**唯一差异**是
`side_effect_identity` 前后两块的 `run_directories` 各新增
`p1-m3-body-001-arm-a-trial-5`（**31 → 32**），其余字段全部相同；
**`p1-m3-body-001-arm-b-trial-1` 不在其中**，与 §2.16 第 7 项一致。
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
        "p1-m3-body-001-arm-a-trial-5",
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
        "p1-m3-body-001-arm-a-trial-5",
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

## A.6 §3 步骤 0′ 第 1 步 —— 解释器绑定值落盘

按 revision 19 的 E 点更正，本值落盘于**本轮采集的证据文件**（即本文件）。
取自 §A.5 预检 stdout 的 `interpreter.executable` 逐字值：

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python
```

**步骤 0′ 第 2 步尚未执行**（本批不启动 tracker）：启动时命令行首的解释器路径
必须与上值**字符串逐字相等**，并把实际执行的完整命令行原文一并记入本文件；
不等即 fail closed 回接受角色。**门 4（revision 19 新增）与本条同一时点执行**：
回车之前把实际命令行原文落盘，并逐字核对同时含 `--body-policy threshold` 与
`--run-id p1-m3-body-001-arm-b-trial-1`。

## A.7 交回接受角色 / 未验证项

1. **§2.0 (c) 是接受角色的动作**，本角色对 `docs/unity-test-log.md` 只读。
   **测量时点 HEAD ≠ 发令时点 HEAD**：本批（本文件 + 状态板）须在 (c) 之前
   提交，(c) 的 HEAD/status 必须由接受角色在写入时点自取。本批只动两个文档
   路径，均**不在** PLAY_GOVERNING 集合内。
2. **§2.16 需在发令时刻复查**（前几轮均因接受角色的新提交而重跑过；本批提交
   本身也会改变 HEAD）。
3. **PLAY_GOVERNING 恰 1 条 = 操作单 revision 19 自身**，归因见 §A.4。
   revisions 13–18 的复核债已由复核轮 8 逐 hunk 覆盖、轮 9 定点复看闭合
   （`passed_candidate: 408acd7…`）；**尚未被任何复核轮覆盖的是 revision 19
   本身与接受轮 58 自查采纳的 20 处修复**——两者都成文于轮 9 的候选之后，
   接受轮 58 已自行登记该复核债。本角色只报告，不判定其是否阻断。
4. **B1 无前驱门**：`p1-m3-body-001-arm-b-trial-1` 从未创建或消耗，两个
   `_check_a*_predecessor_hold` 都不触发，receipt 不会有 predecessor 字段
   （§A.1 第 9 项已机械确认该 ID 与其 `-attempt-N` 变体的判定）。
5. **臂 B 零作废容错**：只有 A1/A2 有过替代 ID，臂 B 没有替代 ID 机制；
   post-tracker 终态一旦作废即烧掉 canonical slot。pre-tracker 的三个硬门与
   启动期失败**不消耗采集 ID**（只消耗一次 one-Play GO）——该区分是操作单
   revision 19 披露 1 的原文，本角色照字面执行。
6. **本批不产生 Unity 用例**，不申领 `UNITY_NA`。
7. **H2-CEILING 已由接受轮 58 预登记**（`H2_SUPPORTED` 算术不可达，上限
   `THRESHOLD_ALLOCATION_PARTIAL`），用户对修改统计量的 NO-GO 已入账；本批次
   不触碰任何统计量、阈值或指标口径。臂 B trial 2–5 与 `--compare` 仍无 GO。

## A.8 §A 批次边界声明

- **零 Play、零采集 ID 创建/消耗**；`runs/p1-m3-body-001-arm-b-trial-1/` 未预建
  （批次结束后复测仍不存在，预检 `run_directories` 32 项中亦无该名）。
- **零 `runtime/` 写入**：本批只做只读读取（`open(..., 'rb')`/`stat`/`iterdir`）、
  五条 `--verify`（写盘前返回）、§2.16 第 8/9 项命令块与预检（自证
  `unchanged = true`）；无 `mv`/`rm`/`mkdir`/重定向写入/`--finalize`。批次结束后
  复测：`runtime/frames/` 仍 **0 项**、六个 shared 文件仍全部不存在、
  `runtime/runs/` 仍 **32** 个直接子目录。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单
  （BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`；对
  `docs/unity-test-log.md` 与 `docs/authorizations.md` 只读。
- 本批写入仅两个路径：**本证据文件**与 `docs/current-status.md`。
- `git status --porcelain` 在预检、五条 `--verify`、核对脚本**之前与之后**均为空。
- 复核范围：§A.1–§A.3 的 `runtime/`+`config/` 现场事实（可由磁盘直接复算）、
  七条只读命令的逐字输出、§A.4 的基线派生与归因、§A.5 的预检 JSON。

---

# B. B1 的 Play 与三个独立硬门（§3 步骤 1–2，**启动 tracker 之前**落盘）

日期 2026-08-14。用户按接受轮 59 的 §2.0 (c) 记录（`docs/unity-test-log.md`，
write-time HEAD `f3a150bfec9d469ee85165d77639b7b532229b61`）进入 Play **恰一次**。
采集 ID `p1-m3-body-001-arm-b-trial-1`（自身即 canonical slot，从未被消耗，
**本轮无前驱门参与**）。**本次是臂 B 的第 1 次，也是本项目第一次让机体真的动。**

发令时刻三项复核（用户进 Play 之前实测）：

- **§2.0 (d)**：`git diff --name-only` 逐字只有 `docs/unity-test-log.md` ✓
- **§3 步骤 0 预检（命令时刻复跑）**：退出 0、`status=PASS`、
  `side_effect_identity.unchanged=true`，stdout 与 §A.5 记录的那份**逐字节相同**
  （5415 B，含尾换行），`run_directories` 32 项且不含 B1 ✓
- **§2.16 九项复跑**：**115/115 PASS**（接受轮 59 的提交把 HEAD 推到 `f3a150b`，
  按 §A.7 第 2 条重取，结论不变）✓

## B.1 用户进入 Play 并暂停（口报如实记录，**不作判据**）

用户报告逐字：**「已暂停」**——未报时刻（本载体无计时 HUD，§1 激活方式行已披露）。

## B.2 门 1 —— 暂停窗口（`2.000000 <= reported_sim_t < 10.000000`）

**导出命令原文**（只读；只解析保留帧元数据 JSON，不读任何真值文件）：

```bash
.venv-yoloe/bin/python - <<'PYEOF'
import json, pathlib
frames = pathlib.Path("runtime/frames")
entries = sorted(frames.iterdir())
records = []
for p in sorted(frames.glob("frame_*.json")):
    d = json.loads(p.read_text())
    records.append((d["frame_id"], d["simulation_time_s"], p.name))
ids = [r[0] for r in records]
print("directory entries:", len(entries))
print("retained metadata files:", len(records))
print("frame_id range: min =", min(ids), " max =", max(ids),
      " contiguous =", ids == list(range(min(ids), max(ids)+1)))
print("max simulation_time_s = %.6f" % max(r[1] for r in records))
print("min simulation_time_s = %.6f" % min(r[1] for r in records))
for fid, t, name in records[-3:]:
    print(f"  frame {fid}: {t}  ({name})")
mx = max(r[1] for r in records)
print("GATE1 2.000000 <= %.6f < 10.000000 ->" % mx, 2.0 <= mx < 10.0)
print("GATE2 lowest retained frame == 0 ->", min(ids) == 0)
latest = json.loads((frames / "latest.json").read_text())
print("latest.json frame_id =", latest["frame_id"])
print("reported_sim_t (verbatim) =", repr(mx))
PYEOF
```

**逐字输出**：

```text
directory entries: 55
retained metadata files: 27
frame_id range: min = 0  max = 26  contiguous = True
max simulation_time_s = 5.383974
min simulation_time_s = 0.184209
  frame 24: 4.982699871063232  (frame_0000000024.json)
  frame 25: 5.1834259033203125  (frame_0000000025.json)
  frame 26: 5.383973598480225  (frame_0000000026.json)
GATE1 2.000000 <= 5.383974 < 10.000000 -> True
GATE2 lowest retained frame == 0 -> True
latest.json frame_id = 26
reported_sim_t (verbatim) = 5.383973598480225
```

| 要求（revision 12 记录型条款） | 值 |
|---|---|
| 导出命令原文 | 见上 |
| 保留帧编号范围 | `frame_id` **0–26**，连续，27 份元数据（目录共 55 项；`latest.json` 的 `frame_id` = **26**，与最大保留帧一致） |
| 导出的数值 | `reported_sim_t` = **`5.383973598480225`** |

**门 1 PASS**：两侧余量约 `3.384 s` 与 `4.616 s`（相邻帧约 `0.200 s`）。口报时刻未
提供，本判据从不取口报值。**披露不变**：该值是暂停真实时刻的**下界**
（COORD-007 §4.1，R10 未授权），冻结窗口 `[2.000000, 10.000000)` 本轮不调整。

## B.3 门 2 —— 最低保留帧必须恰为 `0`

最小 `frame_id` = **`0`** ✓，**门 2 PASS**。

## B.4 门 3 —— 冻结框匹配（用户目检）

```bash
.venv-yoloe/bin/python -m controller.track_loop --dump-frame 0 --output <scratch>/b1_frame0_raw.jpg
```

退出码 0，导出图 **640×480**；随后在 scratchpad 内叠加**已冻结**像素框
`(177, 195, 77, 73)`（`min_side = 73 px`）供目检——未重新框选、未重新估框、
未做六位小数化、未读任何真值；叠加图只落在会话 scratchpad，不进仓库、不进
`runtime/`。

**用户目检结论（逐字）**：「**匹配**」→ **门 3 PASS**。现场未做任何调整。

**三门全部 PASS**，互不覆盖。

## B.5 门 4 —— 启动前命令行核对（revision 19 新增）+ §3 步骤 0′ 第 2 步

**实际将要执行的完整命令行原文**（回车之前落盘）：

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
  --run-id p1-m3-body-001-arm-b-trial-1 \
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

机械核对逐字输出：

```text
GATE4 contains '--body-policy threshold' -> True
GATE4 contains '--run-id p1-m3-body-001-arm-b-trial-1' -> True
GATE4 must NOT contain '--body-policy hold' -> True
GATE4 must NOT contain '-attempt-' -> True
STEP0'-2 head      = ~/TetheredDroneTracking/.venv-yoloe/bin/python
STEP0'-2 preflight = ~/TetheredDroneTracking/.venv-yoloe/bin/python
STEP0'-2 逐字相等 -> True
runbook block lines = 19  my lines = 19
differing lines: [1]
  line 1: runbook='.venv-yoloe/bin/python -m controller.track_loop \\'
           mine   ='~/TetheredDroneTracking/.venv-yoloe/bin/python -m controller.track_loop \\'
```

- **门 4 PASS**：两个 token 序列均在，且**不含** `--body-policy hold` 与任何
  `-attempt-` 后缀（臂 B 无替代 ID）。
- **步骤 0′ 第 2 步 PASS**：命令行首与命令时刻预检 JSON 的
  `interpreter.executable` **字符串逐字相等**。
- **与操作单 §4 CLI 块逐行比对：19 行中唯一不同的是第 1 行**——把 §4 的相对写法
  `.venv-yoloe/bin/python` 写成步骤 0′ 第 2 步要求逐字相等的绝对路径（§X.1 先例）；
  **18 个 `--` 参数全部逐字节相同，未改、未加、未减**，其中 `--run-id` 与
  `--body-policy` 两行即 revision 19 的跨臂轮换值。

---

# C. B1：tracker、完成握手与绑定分析（§3 步骤 2 末段–步骤 6）

## C.1 启动成功（保持暂停下）

进程存活；`runtime/runs/p1-m3-body-001-arm-b-trial-1/` 由 `RunLogger`
**create-once 新建**（证明 §2.16 第 7 项在启动时点仍成立），启动后立即含
`frames.jsonl` / `manifest.json`。**臂 B 专属的 corridor 启动门实弹通过**：
`policy_name == "threshold"` 分支加载 779 条棱柱并比对哈希，不符即启动期
`ValueError`——未触发。确认后才请用户恢复 Play；恢复后未再暂停、未中途退出。
**本轮无前驱门**（ID 从未消耗），receipt 的 predecessor/attempt 键为空集。
**采集 ID 自 run 目录 create-once 建成起即已消耗。**

## C.2 完成握手（§3 步骤 4 的三项 AND 门）

| # | 要求 | 实测 |
|---|---|---|
| 1 | 自然退出码 `0` | 后台通知逐字 `Background command "Start the B1 tracker (arm B, threshold policy)" completed (exit code 0)`；`pgrep -f "controller.track_loop"` 无命中（非信号终止、非人工终止） |
| 2 | stdout final JSON 指向同一采集 ID 的 `summary.json` | `{"qualification_metrics_error": null, "records": 651, "run_id": "p1-m3-body-001-arm-b-trial-1", "state": "TRACKING", "summary": "~/TetheredDroneTracking/runtime/runs/p1-m3-body-001-arm-b-trial-1/summary.json"}` |
| 3 | run 内 `metrics.final.json` 与 `summary.json` 均存在 | 两者均存在 |

**确认词由机械来源产生**（round 30 §C.4，非人工复述）：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --validate-completion \
  --runtime runtime --run-id p1-m3-body-001-arm-b-trial-1 \
  --tracker-exit-code 0 --tracker-final-json '<上表第 2 行原文>'
```

stdout 逐字 `TRACKER_AUTO_COMPLETE_CONFIRMED`，退出码 **0**。按 BC-BODY1-29，
产生确认词后的**下一个动作**即请用户退出 Play；本节以下全部内容都在用户退出
**之后**写。用户逐字报告：**「已退出，没有报错」**——**Console 无报错**。

## C.3 §3 步骤 5 绑定分析 —— **PASS**

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-b-trial-1
```

退出码 **0**，stderr 空，stdout 逐字：

```json
{"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-1", "verified": false, "window_c_track_given_geom": 1.0}
```

绑定核对全过（run_id / manifest schema / scenario 哈希 / **arm 身份三层核对** /
tracker 身份与双模型 SHA / re-anchor 身份 / condition・track / 地平面 / 初始框 /
truth 逐帧绑定 / 首末帧 / 样本数 / run-bound 输入 SHA-256 / 闭环恰一次 / 窗口与
整圈定义域），receipt 已 create-once 写入 run 目录。**臂身份三层核对通过**即
CLI `--body-policy threshold`、manifest policy/planner 与逐帧
`body_planner.name` 三者一致——门 4 的目的在此得到事后确认：
`receipt.body_policy = threshold`、`receipt.body_planner_name =
threshold-corridor-v1`。

`--verify` 只读复算退出 **0** 并逐字复现同一 JSON（`verified: true`）。

## C.4 §3 步骤 6 记录（主结果 + BC-BODY1-30 + 臂 B 专属 (iii)(iv)）

**主结果（只记录，不判定）**：

| 量 | 值 |
|---|---|
| `h1.full_loop_c_geom` | **`1.0`** |
| `h1.disposition` | **`SCENE_DEGENERATE`**（`ceiling = 0.95`，`lower_bound = 0.5645`） |
| `window.c_track_given_geom` | `1.0`（`c_track` 同为 `1.0`，`tracking_iou_threshold = 0.3`） |
| 参考量（非门） | `online_aggregate_c_geom_reference = 1.0`，`online_sensor_frames_reference = 650` |

**BC-BODY1-30 披露（只记录、不判定）**：

| 项 | 值 |
|---|---|
| tracker 最后一帧 `simulation_time_s` | `130.19036865234375`（`frame_id 650`，651 条帧记录） |
| Play 最后一条 truth `simulation_time_s` | `171.58016967773438`（**858** 条） |
| **post-tracker 停留** | **`41.389801 s`** |
| 实测圈数 | `344.7301208561142 / 212.97056274847716` = **`1.618675`** |

两条域完整性门零触发；`loop_frame_count` **530**、`window_frame_count` **155**、
`h2_grid_points` **125**，与冻结口径一致。

**臂 B 专属 (iii) —— 本项目历史上第一次非零机体运动**：

| 量 | B1 | 臂 A 五次 |
|---|---|---|
| `cost.body_motion_effort_m` | **`88.64522663177961`** | `0` |
| `cost.body_path_length_m` | **`61.42306359956821`** | `0` |
| `cost.planner_switch_count` | **`11`** | `0` |

**故 revision 19 披露 2 的退化分支（`body_motion_effort_m == 0`）不触发**，
机体在整圈定义域 `[0, P)` 内确实动了。按 BC-BODY1-15 (d)，这三个第一次出现的
非零量**只记录、不据以调参**。

**臂 B 专属 (iv) —— 逐帧 `body_planner.reason` 直方图**（623 条 decision 帧，
planner 名全为 `threshold-corridor-v1`）：

| reason | 帧数 |
|---|---|
| `margin_below_trigger+corridor_blocked` | **324** |
| `within_hysteresis_band` | 116 |
| `margin_below_trigger` | 95 |
| `margin_above_release` | 82 |
| `margin_below_trigger+corridor_shortened` | 6 |

- **`no_observation` / `no_platform_state` / `no_estimate` / `planner_exception`
  四项均为 0 帧**——规划器每一帧都拿到了观测、平台状态与估计，无异常路径。
- **`publish_failure_fallback` 帧数 = 0**。
- `compute_stage` 机械划分：**恰 1 条 init** + **650 条 update**；update 中
  623 条 decision（带 planner）+ 27 条 catch-up（`skipped_count=1`，合法地不带
  planner）；另有 131 条 event 行（含 `REANCHOR_CHANNEL_SUMMARY`）。

**其余复算量（如实抄录，不解释）**：

| 组 | 值 |
|---|---|
| `c_quality` | `min_side_ge20_share = 1.0`、`area_median_px = 2261.0301433554923`、`center_error_median_px = 33.5783576965332` |
| `tails` | `center_error_p90_px = 50.37639999389646`、`center_error_max_px = 106.1969985961914` |
| `saturation` | 整圈 gimbal `0.5058692662045972` / tether `0.47467114786459996`；窗口 gimbal `0.0` / tether `0.2229517822265625` |
| `estimator` | `nees_median = 5.067625439804517`、`nis_median = 0.025532533112029368`、`fused_frame_count = 622`、`box_center_residual_rms_px = 4.230190577403941`、`box_center_residual_ratio = 1.4759334517994902`、`sigma_px_frozen = 2.866112` |

## C.5 现场清点与臂 A 五次不受影响

- 本次 run 目录 **11 份文件**（含 `m3_body_analysis.json`），与臂 A 五次同构。
- **臂 A 五个 run 一字节未动**：Play 后五条 `--verify` 各退出 0 并逐字复现
  `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` /
  `0.5783206310103214` / `0.5783243208518966`，全部仍 `WITHIN_RANGE`、窗口 `1.0`。
- 五处 post-run 归档、四处旧 hold 与十文件 void hold 本轮全程只读，未移动、未覆盖。
- **本轮不做 post-run 归档**：§2.15 是 A5 的合同，B1 的归档合同须由接受角色在
  归因之后另发修订冻结（沿 §2.9/§2.11/§2.13/§2.15 先例）。shared 槽位因此仍是
  B1 这次 Play 的产物，**不得**被下一次采集覆盖。

## C.6 交回接受角色（**本角色不自判 trial 有效性**）

1. **`h1.disposition = SCENE_DEGENERATE`（`full_loop_c_geom = 1.0`）需要接受角色
   归因。** 机械事实（读操作单 §5 revision 19 注与代码确认）：BC-BODY1-15 (c)
   的三分支绑定「批次 1c 的**第一次** Play」，已由 A1 放电且**不为 B1 重新武装**；
   分析器为臂 B 的 run 照常写出 `h1.disposition` 字符串但**从不据此抛错**，H1 也
   只遍历臂 A。**故本次没有触发任何 void 终态，绑定分析 PASS**——但「B1 是否
   有效 trial」是接受角色的判定，本角色不代判。
2. **该值同时是指标天花板事件**：臂 B 单次整圈 `C_geom` 落在分析器的
   `ceiling = 0.95` 之上（实测 `1.0`），而臂 A 五次为 `0.578–0.597`。**本节不作
   任何统计主张、不作因果归因**：H1/H2 的正式比较必须等十次齐备后由 `--compare`
   产出，而臂 B 余下四次与 `--compare` 均**无 GO**。
3. **与预登记 H2-CEILING 的关系（如实登记，不据此调参）**：B1 的
   `c_quality.min_side_ge20_share` 实测为 **`1.0`**。接受轮 57 的反事实正是以
   「臂 B 即使满分」为前提推出 `H2_SUPPORTED` 不可达；本次是**第一份**与该前提
   同向的实测数据，但它是窗口份额、不是公共格点上的配对中位数，**不足以单独
   证实或证伪**该预登记结论。
4. **估计器量级与臂 A 差异极大**（`nees_median` `5.068` vs 臂 A `832–1017`，
   `nis_median` `0.0255` vs `0.0047–0.110`）。**登记给臂 B 后续与 M5 设计审查**，
   BC-BODY1-15 (d) 禁止据此调参。
5. **协议合格 ≠ 已获 GO**：本轮 GO 只覆盖 B1 一次 Play，已用尽。臂 B trial 2–5
   与 `--compare` 仍需用户逐次逐字授权。
6. **本批不产生 Unity 用例结论**，不申领 `UNITY_NA`；用户 Unity 反馈（「已退出，
   没有报错」）须由接受/辅助角色代录进 `docs/unity-test-log.md`——本角色只读。

## C.7 §B–§C 批次边界声明

- **恰一次 Play，恰一个采集 ID**（`p1-m3-body-001-arm-b-trial-1`，已消耗）；无
  重进、无第二次启动、无 `-attempt-N` 变体。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单
  （BC-BODY1-21/-22 全程遵守）、提案、正式设计、`docs/reviews/`；对
  `docs/unity-test-log.md` 与 `docs/authorizations.md` 只读。
- `runtime/` 侧写入全部由 tracker 与分析器在授权范围内产生；本角色未做任何
  `mv`/`rm`，未预建任何 run 目录，未触碰臂 A 现场。
- 本批写入仅两个仓库路径：本证据文件与 `docs/current-status.md`。
- 复核范围：§B.2–§B.5 的三门与门 4 逐字记录、§C.2 的握手与 validator 输出、
  §C.3 的绑定分析与 `--verify` 复算、§C.4 全部抄录量（可由 run 目录直接复算）。

**收工自检（如实报告，含一项未通过）**：

- `python3 tools/check_docs.py` **通过**。
- `python3 tools/check_role_writes.py --role implementation` **未通过 1 项**：
  `docs/unity-test-log.md`。该文件的未提交改动**不是本角色的写入**——它是接受轮 59
  按 §2.0 (c) 写入、并按 (d) **刻意保持未提交**的发令前置记录（`git diff --stat`
  实测 **376 行纯新增、零删除**，内容即那条 `PRE_PLAY_RELEASED` 条目；本角色对该
  文件全程只读，Play 前的 (d) 核对读到的就是它）。**本角色既不提交也不回滚它**：
  提交属越权（实现角色对信任根只读），回滚会毁掉接受角色的发令记录。Play 已结束，
  (d) 的保持未提交理由随之消失，该记录应由接受角色在归因批次中一并提交，届时本项
  自检自然转为通过。
