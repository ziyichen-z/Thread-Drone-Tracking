# P1-M3-BODY-001 arm B trial 2 证据（操作单 revision 21）

**范围**：用户 2026-08-14 批量授权的 B2–B5 四次 Play 中的**第一次**（B2；批量 GO
「照跑 B2–B5，饱和作具名限制」，接受轮 61 入账 `docs/authorizations.md`）。执行合同 =
`docs/evidence/P1-M3-BODY-001-1c-preflight.md` **revision 21**。采集 ID
`p1-m3-body-001-arm-b-trial-2`（canonical slot 即其自身，从未消耗，**无替代 ID、无
predecessor 门**），配对搭档 A2（`p1-m3-body-001-arm-a-trial-2-attempt-2`）。
**批量授权不改变逐次纪律**：每次仍走完整 §2.0 (a)–(d) 与各自核对节，**任何 void
终态立即中止该授权并回用户**。

**状态**：§A 已完成（§2.17 归档 + §2.18 九项 + §2.0 (b) + §3 步骤 0/0′ 第 1 步，
**零 Play、零采集 ID、零代码**）；§2.0 (c) 记录归接受角色，(d) 与 §3 步骤 1 之后
各节待 Play 时/后填写。

---

# A. B2 的 Play 前置（§2.17 归档 + §2.18 核对 + §2.0 (b) + §3 步骤 0/0′ 第 1 步）

日期 2026-08-14，实现角色。交接来源：接受轮 60（B1 判有效、发 revision 20 归档合同）
与接受轮 61（批量 GO 入账、饱和限制预登记、发 revision 21）。**零 Play、零采集 ID
创建/消耗、零代码/测试/config/scenario/model 改动、零操作单改动（BC-BODY1-21/-22）。**
批次开始与结束时 `git status --porcelain` 均为空（`runtime/` 全程在 `.gitignore` 内）。

## A.1 §2.17 —— B1 的 post-run 归档：**24 条机械核对，24 PASS / 0 FAIL**

destination `runtime/test-results/p1-m3-body-001-arm-b-trial-1-post-run/` 移动前实测
**不存在**；六项逐个 `os.rename`，**每次移动前复查 destination 不存在**（零覆盖证明），
零删除、零分析。

**移动前实测 = 接受轮 60 钉住表 = 移动后实测**（逐项相等）：

| 项 | 计数/行数/字节 | SHA-256（前 = 钉住 = 后） |
|---|---|---|
| `frames/` | **257** 项 | 聚合 `09f1ac615777a313109c1ed7feac2ec792de7d01951e56a4f90ec780428b524c` |
| `m3_body_truth.jsonl` | **858** 行 / 919046 B | `6addcf08d9fec807c21e7daff5300d885aa63deda5d3d26061eecfe10057935e` |
| `metrics.json` | 61 行 / 2057 B | `528ab2b925abd547108e88e04fbd04eb77f6bf6b117330218b98a53a6759b6ba` |
| `body_command.json` | **15 行 / 329 B** | `b0e36adb0f4782a24e988658a752cb8f8262f5e9afc07f6c64a411912335456c` |
| `gimbal_command.json` | 15 行 / 341 B | `90fc33fef3919c5ccdd0445f09d1a99909b11d915a857fa9272b8c35e21bf55d` |
| `tracking_observation.json` | 18 行 / 438 B | `924728703d9664c8293d3baf89fc38eb7f84e63c1d1cdced91667455a5026e8c` |

`body_command.json` 的 **15 行 / 329 字节**与臂 A 五次的 10 行 / 207–208 字节不同——
臂 B 的指令包多出 `velocity_world_mps` 子对象，属设计使然（§2.17 已预先写明，本轮实测
与之相符）。

移动后现场（逐项实测）：`runtime/frames/` **重建为空（0 项）**、六个 shared 文件
**全部不存在**（含 `scenario_config.json`，批次期间不恢复）、**未预建任何 run 目录**
（`…-arm-b-trial-2/` 实测不存在）、**B1 的 run 目录未动（11 份）**、destination 恰
**6 项**。

**归档后复跑六个 `--verify`，全部退出 0 且逐字复现**：

```text
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214, "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783243208518966, "run_id": "p1-m3-body-001-arm-a-trial-5", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-1", "verified": true, "window_c_track_given_geom": 1.0}
```

**六份证据到此全部归档完毕、全部可复算**（B1 的 shared 侧归档使其与臂 A 五次同构）。

## A.2 §2.18 —— B2 的 Play 前只读核对：**126 条机械核对，126 PASS / 0 FAIL**

期望值取自 §1（corridor 钉住行）、§2.5 第 4–7 项原表、§2.8 十文件 hold 与三钉住 SHA、
`…-arm-a-trial-1.md` §B/§F.1/§H.1/§I.1/§N.1，以及 §2.9/§2.11/§2.13/§2.15/**§2.17**
五份归档钉住表。核对脚本只做 `open(..., 'rb')`/`stat`/`iterdir`，落在会话 scratchpad。

| §2.18 项 | 核对内容 | 结果 |
|---|---|---|
| 1 | 六个 shared 文件 | 均**不存在** ✓（6/6） |
| 2 | `runtime/frames/` 存在且为空 | 存在、**0 项** ✓（2/2，由 §2.17 重建） |
| 3 | 四处旧 hold | **257 / 93 / 109 / 257** + 全部 SHA；attempt-3 run hold 仍恰两文件 ✓（26/26） |
| 4 | **六个正式 run 目录** | A1…A5 + **B1** 各**恰 11 份**且各含 `m3_body_analysis.json` ✓（12/12）；六条 `--verify` 见 §A.1 |
| 5 | **六处 post-run 归档** | 各**恰 6 项**、`frames/` 各 **257** 项、六个聚合 SHA 依次 `ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` / `9dc67a76…a62b` / **`09f1ac61…524c`** ✓；六组各五个单文件的行数/字节/SHA 逐项等于各自钉住表 ✓（48/48） |
| 6 | 活动标记 + attempt-1 void hold | 八个具名标记均不存在；void hold 仍**恰 10 份**、文件名集合等于冻结十项、**零隐藏项**、三钉住 SHA 相等 ✓（14/14） |
| 7 | **B2 create-once 前置** | `runtime/runs/p1-m3-body-001-arm-b-trial-2/` **不存在** ✓（1/1） |
| 8 | **臂 B 专属：corridor 工件** | 实测 SHA = config pin = §1 钉住值 `9e2956ad…c800` ✓、`instance_count` **779** 且工件实际条目 **779** ✓、**`policy.tether_corridor_check` 仍为 `true`** ✓（6/6） |
| 9 | **臂 B 专属：臂位机械复核** | `_expected_policy('…-arm-b-trial-2')` = `threshold` ✓；`POLICY_PLANNER['threshold']` = `threshold-corridor-v1` ✓；**`expected_acquisition_ids('b')[1]`** 逐字相等 ✓；`canonical_trial_id()` 返回同名 ✓；`…-attempt-1`/`…-attempt-2`/`…-trial-6` 在**两个**函数上均抛 `run_id_not_frozen_trial` ✓（11/11） |

分项计数：1: 6/6、2: 2/2、3: 26/26、4: 12/12、5: 48/48、6: 14/14、7: 1/1、8: 6/6、
9: 11/11。第 8 项的 `tether_corridor_check` 是本轮**新加的自查项**（B1 轮由读码确认，
本轮改为机械断言）：它为真，corridor 哈希门在臂 B 才真正是启动门。

## A.3 §2.0 (b) 报告（测量时点）

```text
$ git rev-parse HEAD
d48cd25a2166a057bdb79ecc5b73a93df702cbee

$ git status --porcelain
（空输出）

$ grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md | tail -1
passed_candidate: 408acd7b39054e0a92eb3f0f9df5d4713b16f34a
```

`<BASE>` = **`408acd7`**（复核轮 9 的通过候选，运行时现取，未手写）。

```bash
$ git diff --name-only 408acd7..HEAD
docs/authorizations.md
docs/current-status.md
docs/evidence/P1-M3-BODY-001-1c-preflight.md
docs/evidence/P1-M3-BODY-001-arm-a-trial-2.md
docs/evidence/P1-M3-BODY-001-arm-b-trial-1.md
docs/implementation-status.md
docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md
docs/reviews/P1-M3-BODY-001.md
docs/unity-test-log.md
```

**九个路径，全部是文档**（比 B1 轮多两条：B1 的证据文件与 Unity 日志——后者是接受轮
59 的 (c) 记录与轮 60/61 的代录，已由 `d48cd25` 提交，故本轮工作树是干净的）。区间内
13 条提交，含 B1 的执行批次 `eb6c96a`。**本轮归因现算，不套用任何历史例示。**

**测量侧逐字节相同**：

```bash
$ git diff --name-only 408acd7..HEAD -- controller/ Assets/ config/ \
    ProjectSettings/ Packages/packages-lock.json tools/ tests/
（空输出）
```

**A1…A5 与 B1 六次采集、以及即将进行的 B2，全部跑在同一份已复核代码上。**

**PLAY_GOVERNING 子集 = 恰 1 条**：操作单，现为 **revision 21**。**CLI 块差异本角色
亲自复算（不转抄抬头）**：

| 比较对象 | 块行数 | 差异 |
|---|---|---|
| 已复核候选 `408acd7`（臂 A trial 5 版本） | 19 / 19 | **恰 2 行**：`--run-id …-arm-a-trial-5` → `…-arm-b-trial-2`；`--body-policy hold` → `threshold` |
| B1 轮（revision 19/20） | 19 / 19 | **恰 1 行**：`--run-id …-arm-b-trial-1` → `…-arm-b-trial-2` |

即 revision 21 抬头 A 点的两个基准数字实测成立。**(b) 的归因按对已复核候选的 2 行写**
——把「1 行」填进归因会低报差异。具名 disposition 由接受角色给出，本角色只报事实。

## A.4 §3 步骤 0 环境预检与步骤 0′ 第 1 步

```bash
.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json
```

**退出码 `0`**，`status = "PASS"`，`side_effect_identity.unchanged = true`，`before` 与
`after` 两块实测完全相等。stderr 仅有既有依赖噪声（OpenCV `setPreferableTarget` WARN、
`tifffile` 提示、DINOv2 三条 xFormers `UserWarning`），共 9 行，不影响退出码与 JSON。

**与 B1 轮记录的预检 JSON 逐字段机械比对**：**唯一差异**是
`side_effect_identity` 前后两块的 `run_directories` 各新增 `p1-m3-body-001-arm-b-trial-1`
（**32 → 33**，即 B1 那次 Play 建的 run 目录），其余字段全部相同；
**`p1-m3-body-001-arm-b-trial-2` 不在其中**，与 §2.18 第 7 项一致。

**步骤 0′ 第 1 步** —— `interpreter.executable` 逐字值：

```text
~/TetheredDroneTracking/.venv-yoloe/bin/python
```

**步骤 0′ 第 2 步与门 4 尚未执行**（本批不启动 tracker）：启动时命令行首必须与上值
字符串逐字相等，且回车前须把实际命令行原文落盘并核对含 `--body-policy threshold` 与
`--run-id p1-m3-body-001-arm-b-trial-2`。

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
        "p1-m3-body-001-arm-b-trial-1",
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
        "p1-m3-body-001-arm-b-trial-1",
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

## A.5 交回接受角色 / 未验证项

1. **§2.0 (c) 是接受角色的动作**（本角色对 Unity 日志只读）。**测量时点 HEAD ≠ 发令
   时点 HEAD**：本批（本文件 + 状态板）须在 (c) 之前提交，(c) 的 HEAD/status 必须由
   接受角色在写入时点自取；**§2.18 需在发令时刻复查**（前几轮均因新提交而重跑过）。
2. **PLAY_GOVERNING 恰 1 条 = 操作单 revision 21**，差异实测见 §A.3。
   **revisions 19/20/21 与接受轮 58 自查采纳的 20 处修复仍未被任何复核轮覆盖**
   （鉴 8→56→9 只闭合了 revisions 13–18，`passed_candidate` 仍是 `408acd7`）；本角色
   如实登记，不判定是否阻断。
3. **B2 无前驱门**：ID 从未创建或消耗，两个 `_check_a*_predecessor_hold` 都不触发，
   receipt 不会有 predecessor/attempt 字段。
4. **批量授权的边界**：B2–B5 一次性授权，但**每次各走完整 §2.0 (a)–(d)**；**任何 void
   终态立即中止该授权**并回用户（臂 B 无替代 ID，post-tracker 作废即烧 slot）。
   `--compare` 仍需十次齐备并单独授权。
5. **两条预登记限制随本轮继续生效**：H2-CEILING（`H2_SUPPORTED` 算术不可达，上限
   `THRESHOLD_ALLOCATION_PARTIAL`）与**处理臂饱和**（B1 的 `C_geom = 1.0` /
   `SCENE_DEGENERATE`，效应量只能报下界）。**一个数都不得据以调参**（BC-BODY1-15 (d)）。
6. **本批不产生 Unity 用例**，不申领 `UNITY_NA`。

## A.6 §A 批次边界声明

- **零 Play、零采集 ID 创建/消耗**；`runs/…-arm-b-trial-2/` 未预建（预检 33 项
  `run_directories` 中亦无该名）。
- `runtime/` 侧写入仅限 §2.17 授权的**移动**（六项 `os.rename`）与重建**空**
  `runtime/frames/`：零删除、零覆盖、零分析；其余全部只读
  （`open(..., 'rb')`/`stat`/`iterdir`、六条 `--verify`、预检自证 `unchanged = true`）。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单
  （BC-BODY1-21/-22）、提案、正式设计、`docs/reviews/`；对 `docs/unity-test-log.md`
  与 `docs/authorizations.md` 只读。
- 本批写入仅两个仓库路径：本证据文件与 `docs/current-status.md`。
- 复核范围：§A.1 的归档前后逐项相等与六条 `--verify` 逐字输出、§A.2 的 126 条核对
  （可由 `runtime/`+`config/` 直接复算）、§A.3 的基线派生与 CLI 块差异复算、§A.4 的
  预检 JSON。

---

# B. B2 的 Play 与三个独立硬门（§3 步骤 1–2，**启动 tracker 之前**落盘）

日期 2026-08-14。用户按接受轮 62 的 §2.0 (c) 记录（`docs/unity-test-log.md`，
write-time HEAD `ae140cecd3079dab86b697857ba6987531cc2f2a`）进入 Play **恰一次**。
采集 ID `p1-m3-body-001-arm-b-trial-2`（自身即 canonical slot，从未被消耗，
**本轮无前驱门参与**）。本次是臂 B 的第 2 次，也是**批量授权 B2–B5 的第一次**。

发令时刻三项复核（用户进 Play 之前实测）：

- **§2.0 (d)**：`git diff --name-only` 逐字只有 `docs/unity-test-log.md` ✓
- **§3 步骤 0 预检（命令时刻复跑）**：退出 0、`status=PASS`、
  `side_effect_identity.unchanged=true`，stdout 与 §A.4 记录的那份**逐字节相同** ✓
- **§2.18 九项复跑**：**126/126 PASS**（接受轮 62 的提交把 HEAD 推到 `ae140ce`，
  按 §A.5 第 1 条重取，结论不变）✓

## B.1 用户进入 Play 并暂停（口报如实记录，**不作判据**）

用户报告逐字：**「已暂停」**——未报时刻（本载体无计时 HUD）。

## B.2 门 1 —— 暂停窗口（`2.000000 <= reported_sim_t < 10.000000`）

**导出命令原文**（只读；只解析保留帧元数据 JSON，不读任何真值文件）：与 §B.2 of
`…-arm-b-trial-1.md` 逐字同一条命令（取保留帧中最大 `simulation_time_s`）。

**逐字输出**：

```text
directory entries: 55
retained metadata files: 27
frame_id range: min = 0  max = 26  contiguous = True
max simulation_time_s = 5.383171
min simulation_time_s = 0.187632
  frame 24: 4.983144283294678  (frame_0000000024.json)
  frame 25: 5.1884379386901855  (frame_0000000025.json)
  frame 26: 5.3831706047058105  (frame_0000000026.json)
GATE1 2.000000 <= 5.383171 < 10.000000 -> True
GATE2 lowest retained frame == 0 -> True
latest.json frame_id = 26
reported_sim_t (verbatim) = 5.3831706047058105
```

| 要求（revision 12 记录型条款） | 值 |
|---|---|
| 导出命令原文 | 见上 |
| 保留帧编号范围 | `frame_id` **0–26**，连续，27 份元数据（目录共 55 项；`latest.json` 的 `frame_id` = **26**，与最大保留帧一致） |
| 导出的数值 | `reported_sim_t` = **`5.3831706047058105`** |

**门 1 PASS**：两侧余量约 `3.383 s` 与 `4.617 s`（相邻帧约 `0.200 s`）。**披露不变**：
该值是暂停真实时刻的**下界**（COORD-007 §4.1，R10 未授权），冻结窗口本轮不调整。

## B.3 门 2 —— 最低保留帧必须恰为 `0`

最小 `frame_id` = **`0`** ✓，**门 2 PASS**。

## B.4 门 3 —— 冻结框匹配（用户目检）

`--dump-frame 0` 导出退出码 0，图 **640×480**；scratchpad 内叠加**已冻结**像素框
`(177, 195, 77, 73)`（`min_side = 73 px`）供目检——未重新框选、未重新估框、未做
六位小数化、未读任何真值；叠加图不进仓库、不进 `runtime/`。

**用户目检结论（逐字）**：「**匹配**」→ **门 3 PASS**。现场未做任何调整。
**三门全部 PASS**，互不覆盖。

## B.5 门 4 —— 启动前命令行核对 + §3 步骤 0′ 第 2 步

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
  --run-id p1-m3-body-001-arm-b-trial-2 \
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

机械核对逐字输出（本轮**多查两条否定项**：不得含 B1 的 run-id、不得含任何臂 A 串——
接受轮 62 的 (c) 点名的两个失手模式就是沿用 B1 的 `--run-id` 与写错 `--body-policy`）：

```text
GATE4 contains '--body-policy threshold' -> True
GATE4 contains '--run-id p1-m3-body-001-arm-b-trial-2' -> True
GATE4 must NOT contain '--body-policy hold' -> True
GATE4 must NOT contain '-attempt-' -> True
GATE4 must NOT contain 'arm-b-trial-1' -> True
GATE4 must NOT contain 'arm-a-' -> True
STEP0'-2 head      = ~/TetheredDroneTracking/.venv-yoloe/bin/python
STEP0'-2 preflight = ~/TetheredDroneTracking/.venv-yoloe/bin/python
STEP0'-2 逐字相等 -> True
runbook block lines = 19  my lines = 19
differing lines: [1]
  line 1: runbook='.venv-yoloe/bin/python -m controller.track_loop \\'
           mine   ='~/TetheredDroneTracking/.venv-yoloe/bin/python -m controller.track_loop \\'
```

- **门 4 PASS**；**步骤 0′ 第 2 步 PASS**（命令行首与命令时刻预检 JSON 的
  `interpreter.executable` 字符串逐字相等）。
- **与操作单 §4 CLI 块逐行比对：19 行中唯一不同的是第 1 行**（相对写法 → 步骤 0′
  要求的绝对路径，§X.1 先例）；**18 个 `--` 参数全部逐字节相同**。

---

# C. B2：tracker、完成握手与绑定分析（§3 步骤 2 末段–步骤 6）

## C.1 启动成功（保持暂停下）

进程存活；`runtime/runs/p1-m3-body-001-arm-b-trial-2/` 由 `RunLogger` **create-once
新建**（证明 §2.18 第 7 项在启动时点仍成立），启动后立即含 `frames.jsonl` /
`manifest.json`，**corridor 启动门无 `ValueError` 通过**。确认后才请用户恢复 Play；
恢复后未再暂停、未中途退出。**本轮无前驱门**，receipt 的 predecessor/attempt 键为
空集（实测：无任何该类键）。**采集 ID 自 run 目录建成起即已消耗。**

## C.2 完成握手（§3 步骤 4 的三项 AND 门）

| # | 要求 | 实测 |
|---|---|---|
| 1 | 自然退出码 `0` | 后台通知 `completed (exit code 0)`；`pgrep -f "controller.track_loop"` 无命中 |
| 2 | stdout final JSON 指向同一采集 ID 的 `summary.json` | `{"qualification_metrics_error": null, "records": 652, "run_id": "p1-m3-body-001-arm-b-trial-2", "state": "TRACKING", "summary": "~/TetheredDroneTracking/runtime/runs/p1-m3-body-001-arm-b-trial-2/summary.json"}` |
| 3 | run 内 `metrics.final.json` 与 `summary.json` 均存在 | 两者均存在 |

`--validate-completion`（`--tracker-exit-code 0` + 上行 final JSON 原文）stdout 逐字
`TRACKER_AUTO_COMPLETE_CONFIRMED`，退出码 **0**。按 BC-BODY1-29，产生确认词后的下一个
动作即请用户退出；本节以下内容全部写于用户退出**之后**。用户逐字报告：
**「已退出，没有报错」**——**Console 无报错**。

## C.3 §3 步骤 5 绑定分析 —— **PASS**

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-b-trial-2
```

退出码 **0**，stderr 空，stdout 逐字：

```json
{"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-2", "verified": false, "window_c_track_given_geom": 1.0}
```

绑定核对全过；**臂身份三层核对通过**（`receipt.body_policy = threshold`、
`body_planner_name = threshold-corridor-v1`、逐帧 planner 名一致）——门 4 的目的在此
得到事后确认。五类冻结工件 SHA 与臂 A/B1 各轮逐字相同（`scenario` `f9c92052…`、
`margin` `c72c9407…`、`visible_arc` `4fe2eea5…`、`tracker_model_spec` `43c81ad9…`）。
`--verify` 只读复算退出 **0** 并逐字复现同一 JSON（`verified: true`）。

## C.4 §3 步骤 6 记录（主结果 + BC-BODY1-30 + 臂 B 专属 (iii)(iv)）

**主结果（只记录，不判定）**：

| 量 | 值 |
|---|---|
| `h1.full_loop_c_geom` | **`1.0`** |
| `h1.disposition` | **`SCENE_DEGENERATE`**（`ceiling = 0.95`） |
| `window.c_track_given_geom` | `1.0`（`c_track` 同为 `1.0`） |
| 参考量（非门） | `online_aggregate_c_geom_reference = 1.0`，`online_sensor_frames_reference = 655` |

**BC-BODY1-30 披露（只记录、不判定）**：

| 项 | 值 |
|---|---|
| tracker 最后一帧 `simulation_time_s` | `130.3805694580078`（652 条帧记录） |
| Play 最后一条 truth `simulation_time_s` | `159.9828338623047`（**800** 条） |
| **post-tracker 停留** | **`29.602264 s`** |
| 实测圈数 | `321.5560791080673 / 212.97056274847716` = **`1.509862`** |

两条域完整性门零触发；`loop_frame_count` **530**、`window_frame_count` **155**、
`h2_grid_points` **125**，与冻结口径一致（三项与 B1 逐字相同）。

**臂 B 专属 (iii) —— 机体运动（第二次非零）**：

| 量 | B2 | B1 | 臂 A 五次 |
|---|---|---|---|
| `cost.body_motion_effort_m` | **`75.26945194958653`** | `88.645…` | `0` |
| `cost.body_path_length_m` | **`49.16248028068326`** | `61.423…` | `0` |
| `cost.planner_switch_count` | **`11`** | `11` | `0` |

**revision 19 披露 2 的退化分支不触发**（effort 非零）。BC-BODY1-15 (d)：这些量
**只记录、不据以调参**。

**臂 B 专属 (iv) —— 逐帧 `body_planner.reason` 直方图**（622 条 decision 帧，planner
名全为 `threshold-corridor-v1`）：

| reason | B2 帧数 | B1 帧数 |
|---|---|---|
| `margin_below_trigger+corridor_blocked` | **339** | 324 |
| `within_hysteresis_band` | 109 | 116 |
| `margin_below_trigger` | 93 | 95 |
| `margin_above_release` | 75 | 82 |
| `margin_below_trigger+corridor_shortened` | 6 | 6 |

- **`no_observation` / `no_platform_state` / `no_estimate` / `planner_exception` 四项
  均为 0 帧**；**`publish_failure_fallback` 帧数 = 0**。
- `compute_stage`：**恰 1 条 init** + **651 条 update**（622 decision + 29 catch-up），
  另有 128 条 event 行。

**其余复算量（如实抄录，不解释）**：

| 组 | B2 | B1 |
|---|---|---|
| `c_quality` | `min_side_ge20_share = 1.0`、`area_median_px = 2266.76895012115`、`center_error_median_px = 34.09173583984375` | `1.0` / `2261.030…` / `33.578…` |
| `tails` | `p90 = 50.40125656127928`、`max = 106.08397674560547` | `50.376…` / `106.197…` |
| `saturation` | 整圈 gimbal `0.5262237721449315` / tether `0.4744974155990803`；窗口 gimbal `0.0` / tether `0.215428507472982` | `0.5059` / `0.4747`；`0.0` / `0.2230` |
| `estimator` | `nees_median = 5.2993597343857255`、`nis_median = 0.02469417347467501`、`fused = 621`、`rms_px = 4.509920092877978`、`ratio = 1.5735323995984727` | `5.068` / `0.0255` / `622` / `4.230` / `1.476` |

## C.5 现场清点与既有证据不受影响

- 本次 run 目录 **11 份文件**（含 `m3_body_analysis.json`），与前六次同构。
- **前六个 run 一字节未动**：Play 后**七条 `--verify` 全部退出 0 并逐字复现**
  （A1…A5 五个 `WITHIN_RANGE` 冻结值 + B1 与 B2 各 `SCENE_DEGENERATE / 1.0 / 1.0`）。
- 六处 post-run 归档、四处旧 hold 与十文件 void hold 本轮全程只读。
- **本轮不做 post-run 归档**：B2 的归档合同须由接受角色在归因之后另发修订冻结，
  shared 槽位现仍是 B2 这次 Play 的产物。

## C.6 交回接受角色（**本角色不自判 trial 有效性**）

1. **B2 的 `h1.disposition = SCENE_DEGENERATE`（`full_loop_c_geom = 1.0`）与 B1 同值**，
   需接受角色归因。机械事实同 B1：BC-BODY1-15 (c) 三分支已由 A1 放电且不重新武装，
   分析器写 disposition 但从不据此抛错，**本次未触发任何 void 终态，绑定分析 PASS**。
2. **饱和预登记（限制 #2）在 n=2 上得到第二个同向数据点**：臂 B 两次整圈 `C_geom`
   均为 `1.0`，`min_side_ge20_share` 两次均为 `1.0`。**本节不作统计主张**：H1/H2 的
   正式比较必须等十次齐备后由 `--compare` 产出，而它无 GO。效应量按预登记只能报**下界**。
3. **可对比的差异（只记录）**：B2 的 effort/path 比 B1 低约 `15%`/`20%`，切换次数
   同为 `11`，`corridor_blocked` 帧数 `339` vs `324`——两次都以 corridor 受阻为主导
   reason。**不得据此调参**（BC-BODY1-15 (d)）。
4. **批量授权仍在**：B2 未作废，故 B3–B5 的授权**未被中止**；但每次仍须走完整
   §2.0 (a)–(d) 与各自核对节，且下一次的前置是 **B2 的 post-run 归档合同**（接受角色
   另发修订）。`--compare` 仍需十次齐备并单独授权。
5. **本批不产生 Unity 用例结论**，不申领 `UNITY_NA`；用户 Unity 反馈（「已退出，
   没有报错」）须由接受/辅助角色代录——本角色对该文件只读。

## C.7 §B–§C 批次边界声明

- **恰一次 Play，恰一个采集 ID**（`p1-m3-body-001-arm-b-trial-2`，已消耗）；无重进、
  无第二次启动、无 `-attempt-N` 变体。
- **零代码/测试/config/scenario/model/阈值/指标/CLI 改动**；未修改操作单
  （BC-BODY1-21/-22 全程遵守）、提案、正式设计、`docs/reviews/`；对
  `docs/unity-test-log.md` 与 `docs/authorizations.md` 只读。
- `runtime/` 侧写入全部由 tracker 与分析器在授权范围内产生；未做任何 `mv`/`rm`，
  未预建任何 run 目录，未触碰既有六处现场。
- 本批写入仅两个仓库路径：本证据文件与 `docs/current-status.md`。
- 复核范围：§B.2–§B.5 的三门与门 4 逐字记录、§C.2 的握手与 validator 输出、§C.3 的
  绑定分析与 `--verify`、§C.4 全部抄录量（可由 run 目录直接复算）。

**收工自检（如实报告，含一项未通过，与 B1 轮同因）**：

- `python3 tools/check_docs.py` **通过**。
- `python3 tools/check_role_writes.py --role implementation` **未通过 1 项**：
  `docs/unity-test-log.md`——**不是本角色的写入**，而是接受轮 62 按 §2.0 (c) 写入、按
  (d) 刻意保持未提交的发令前置记录（`git diff --stat` 实测 **355 行纯新增、零删除**）。
  本角色对该文件全程只读，**既不提交也不回滚**；Play 已结束，(d) 的保持未提交理由
  随之消失，该记录应由接受角色在归因批次中一并提交，届时本项自检自然转为通过。

---

# D. §2.19 —— B2（有效 trial）的 post-run 归档（操作单 revision 22，实现角色）

日期 2026-08-14。交接来源：接受轮 63（B2 判为**有效 trial**，臂 B **2/5**；发出
revision 22，§2.19 为本轮第一步）。**零 Play、零采集 ID 创建/消耗、零代码/测试/
config/scenario/model 改动、零操作单改动。** 批次开始与结束时
`git status --porcelain` 均为空（`runtime/` 在 `.gitignore` 内）。

## D.1 归档执行：**24 条机械核对，24 PASS / 0 FAIL**

destination `runtime/test-results/p1-m3-body-001-arm-b-trial-2-post-run/` 移动前实测
**不存在**；六项逐个 `os.rename`，**每次移动前复查 destination 不存在**（零覆盖证明），
零删除、零分析。**移动前实测 = 接受轮 63 钉住表 = 移动后实测**：

| 项 | 计数/行数/字节 | SHA-256（前 = 钉住 = 后） |
|---|---|---|
| `frames/` | **257** 项 | 聚合 `71f65dca666cc37d91569a9b2b3893c0721e436a1b09756f5e644c0052a20f85` |
| `m3_body_truth.jsonl` | **800** 行 / 862952 B | `c2c985feed5d09bb7991fba6d3d28aadf2e0dfb90d3c63fba06b6fd551454df3` |
| `metrics.json` | 61 行 / 2057 B | `c60939ac59086b065fff39362a46b05bf745acf3b872b8946112b67e677e640e` |
| `body_command.json` | 15 行 / **328** B | `d066e0b1a8d7103a62dc152440a6630d83b4445713b45183f5d074da45448fa5` |
| `gimbal_command.json` | 15 行 / 341 B | `516c2820e4b7623e8a2a8a8938a8b78495975e89b0beb8907b24288b2356d990` |
| `tracking_observation.json` | 18 行 / **458** B | `82ffa1b52f714e325941290c5bca772b985b27cfa0e73210a94d8f0bcdf99463` |

（`body_command.json` 328 B vs B1 的 329、`tracking_observation.json` 458 vs 438：§2.19
已写明是包内数值位数不同，**判据是移动前后逐项相等**，本轮逐项相等成立。）

移动后现场（逐项实测）：`runtime/frames/` **重建为空（0 项）**、六个 shared 文件
**全部不存在**、**未预建任何 run 目录**（`…-arm-b-trial-3/` 实测不存在）、**B2 的
run 目录未动（11 份）**、destination 恰 **6 项**（其中 `frames/` **257** 项）。

## D.2 归档后七条 `--verify` 复跑（§2.19 要求）

全部退出 **0** 且逐字复现各自冻结值：

```text
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783188398250908, "run_id": "p1-m3-body-001-arm-a-trial-2-attempt-2", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.597146417669116, "run_id": "p1-m3-body-001-arm-a-trial-3", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783206310103214, "run_id": "p1-m3-body-001-arm-a-trial-4", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5783243208518966, "run_id": "p1-m3-body-001-arm-a-trial-5", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-1", "verified": true, "window_c_track_given_geom": 1.0}
exit=0  {"disposition": "SCENE_DEGENERATE", "full_loop_c_geom": 1.0, "run_id": "p1-m3-body-001-arm-b-trial-2", "verified": true, "window_c_track_given_geom": 1.0}
```

**七份证据（臂 A 五份 + B1 + B2）至此全部归档完毕、全部可复算。**

## D.3 披露：一次重复调用（fail-closed，零副作用，如实登记）

归档脚本在成功执行**之后**被本角色**误重复调用一次**。该次调用在「移动前实测」阶段
即 fail closed：`runtime/frames/` 实测 0 项（与钉住的 257 不符，报 FAIL），随后在读取
已被移走的 `m3_body_truth.jsonl` 时抛 `FileNotFoundError` 退出——**中止点位于移动段
之前**，故**未发生任何第二次移动**。

事后逐项复核证明零副作用：destination 仍**恰 6 项**（`frames/` **257** 项）、
`runtime/test-results/*arm-b-trial-2*` 只有**一个**目录、`runtime/frames/` 仍 0 项、
六个 shared 文件仍全部不存在、`runtime/runs/` 仍 **34** 个目录且无 `…-arm-b-trial-3/`、
七条 `--verify` 全部逐字复现（见 §D.2，该复跑在误调用之后执行）。

**登记原因**：脚本的守卫按设计生效（先比对钉住值再移动），但它的失败路径是抛异常而
非有序退出；这是本角色的操作失误，不是合同或工具缺陷，**不改变任何门、不申请任何
例外**，一并交复核角色核对。

## D.4 交回接受角色 / 边界

- **本节不释放任何 Play**：B3 的前置是 **§2.20 九项核对 + §2.0 (b)/(c)/(d)**，其中
  (c) 归接受角色；B3–B5 虽在批量授权内，仍须逐次走完整 §2.0 (a)–(d)，**任何 void
  终态立即中止该授权**。`--compare` 需十次齐备并单独授权。
- **两条预登记限制继续生效**（H2-CEILING、处理臂饱和）；BC-BODY1-15 (d) 禁止据任何
  已见数值调参。
- 本批写入仅两个仓库路径：本证据文件与 `docs/current-status.md`；`runtime/` 侧只有
  §2.19 授权的六次移动与重建空 `frames/`。
- 复核范围：§D.1 的归档前后逐项相等、§D.2 的七条逐字输出、§D.3 的零副作用复核。
