# P1-M3-BODY-001 证据批次 1b（Acceptance round 9 §C）

批次性质：**诊断/证据批次，零正式消耗**——不创建、不消耗任何
scenario/session/run/qual ID，不计入 10 个正式 trial，不产出可用于
H1/H2 的指标，不动配额/API。本批次不写新功能，不改变候选 `61ea20b`
的实现语义。

执行合同：`docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md`
Acceptance round 9 §C 六条，逐条对应本文件 §1–§6。

## §C-1 候选身份（开工记录）

- `git rev-parse HEAD` → `16a4da71583708a20a6892e15ade90afe7b1a052`
  （= `origin/main`，已推送主线；`git branch -r --contains 61ea20b`
  含 `origin/main`，复核候选在主线祖先链上）。
- `git status --porcelain` → **空**（开工时工作树干净）。
- `git diff 61ea20b..HEAD --name-only` → 仅 6 个 docs 路径
  （archive/current-status/authorizations/implementation-status/proposal/
  review），**零 C#/Python/controller/config/scenario 差异**：实现字节与
  已复核候选 `61ea20b` 相同。无语义差异，无需退回 Acceptance。

## §C-2 道路/走廊审计重跑（真实场景 + `config/scenario.default.json`）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `…/6000.4.1f1/Unity.app/Contents/MacOS/Unity -batchmode -nographics -projectPath ~/TetheredDroneTracking -executeMethod TetheredTracking.Editor.P1M3BodySceneGeometryGenerator.Generate -quit -logFile runtime/test-results/p1-m3-body-001-1b-scene-geometry.log` | 0 | 日志：`896 roots, 117 road surfaces, 779 obstacle instances (…, 6 vehicles relocated); road audit CLEAR with 779 audited obstacles.` |
| `python3 tools/check_scene_body_margin.py` | 0 | 重写出工件与盘上逐字节相同（`git status` 对 `config/`、`Assets/` 为空）；输出 `C_geom upper=1.000000 lower=0.565728 (arm B lower=0.584507)`、可见弧 `[155.0, 275.5] wraps`、测量窗 `[0.0, 62.5]` 与既有 pins 一致 |
| `python3 tools/build_m3_corridor.py --check` | 0 | `corridor check OK: 779 prisms, sha256=9e2956ad93a4a81cf638a913b9c806e1a316616bf090b125641d3f5c0b7fc800`（与批次 1a-β 钉值不变） |

- 重生成后 `git status --porcelain -- config/ Assets/` → **空**：版本化
  几何/走廊/边界证据与已复核 pins **字节一致**。
- 四项硬条件同时满足：road audit `CLEAR`、779 审计障碍、corridor
  `--check` 通过、工具 2 通过。未改任何场景、参数、阈值或工件。

## §C-3 COORD-005 人眼保真检查（诊断 Play）

**状态：完成——诊断 Play 已执行，两张样帧用户逐张 `PASS`。**

诊断 Play 准备（实现角色已执行，均为可逆移动，无删除）：

- `runtime/frames/` 残留 qual-3（2026-07-31，已关闭归档）帧 8,193 个
  文件（frame_id 至 9295）→ 移至 `runtime/frames.qual3-leftover-hold/`。
  必须腾空：`SensorFrameWriter` 每次 Play 的 `frameIndex` 从 0 重计，
  会覆盖/混淆残留文件，导致样帧无法归因到本次 Play。
- `runtime/scenario_config.json` 原为 SCENE-004 冻结配置（SHA-256
  `00c8802a…b514`，与 `config/scenario.p1-scene-004.json` 逐字节相同）
  → 移至 `runtime/scenario_config.p1-scene-004.hold.json`。原因：
  `ScenarioConfig.Load()` 优先读 runtime override，不移除则 Play 会以
  SCENE-004 场景身份运行，而 M3′ 批次 1 生产链载体是主环线
  `config/scenario.default.json`（`ScenarioConfig.Load` 回退到项目
  默认即该文件）。
- 无正式身份占用：无 release pointer、无活动 qualification/scouting
  标记。

诊断 Play 操作（用户执行，明确标注为诊断）：

1. 在 Unity Editor 6000.4.1f1 中打开
   `Assets/SimplePoly City - Low Poly Assets/Demo/SimplePoly City - Low Poly Assets_Demo Scene.unity`。
2. Game 视图激活，进入 Play 一次；不启动任何 Python 控制器/跟踪器。
3. 让仿真计时器走过约 15–20 s（5 Hz 约 75–100 帧），期间红色目标车
   `TargetVehicle_Red` 沿主环线正常行驶、传感器帧持续写入
   `runtime/frames/`。
4. 退出 Play，报告 Console 有无报错。

诊断 Play 执行（用户，2026-08-08，明确标注为诊断）：按上述步骤进入
Play 一次、约 28 s（5 Hz，frame_id 0–139，保留窗 128 帧），退出后报告
**Console 无报错**。帧元数据确认 `scenario_id=deterministic-loop-default`
（即 `config/scenario.default.json` 生产载体）、640×480、
`tethered-sensor-frame/v3`。样帧来自实际 runtime target（生产
`SensorFrameWriter` 写入 `runtime/frames/`），非 probe/替身。

样帧确认表（用户逐张确认，2026-08-08）：

| 样帧相对路径 | SHA-256 | frame_id | 确认人 | 逐张结论 |
|---|---|---|---|---|
| `docs/evidence/P1-M3-BODY-001-1b/frame_0000000012.jpg` | `a1dfa201e2f6e2be68cb9256ddf0b075da6f56212ae9ad9dccbe5f6a24d4f5c4` | 12（sim 2.580 s） | 用户 | **PASS**：红色运行时目标、非灰色替身、语义与批次跟踪对象一致 |
| `docs/evidence/P1-M3-BODY-001-1b/frame_0000000030.jpg` | `ceedad4d8ea919b7ca6e588b074d5df6eecf4bac91512d65f1f2568c5fd39a9a` | 30（sim 6.181 s） | 用户 | **PASS**：红色运行时目标、非灰色替身、语义与批次跟踪对象一致 |

两张样帧 frame_id 不同（12 ≠ 30），对应元数据 JSON 同目录留存
（`frame_0000000012.json` / `frame_0000000030.json`，SHA-256
`77cb459c…25834` / `6e31bc8a…ebc5a`）。

诊断后现场恢复：`runtime/scenario_config.p1-scene-004.hold.json` 已移回
`runtime/scenario_config.json`，SHA-256 `00c8802a…b514` 与移动前逐字节
相同。qual-3 残留帧保留在 `runtime/frames.qual3-leftover-hold/`（未删除，
用户可处置）；本次诊断帧留存于 `runtime/frames/`（frame_id 12–139，
1c 的准备协议按自身要求清空）。

## §C-4 证据可复核

- 样帧存入 `docs/evidence/P1-M3-BODY-001-1b/`（本文件同名单目录）。
- 本文件记录：审计命令/结果（§C-2）、开工 HEAD/clean 状态与实现字节
  等价结论（§C-1）、样帧相对路径/SHA-256/frame_id/确认人/逐张结论
  （§C-3 表）、收工 `git status`（§C-6）。

## §C-5 零正式消耗声明

- 诊断 Play 不创建/消耗任何 scenario/session/run/qual ID，不计入 10 个
  正式 trial，不产出可用于 H1/H2 的指标，不动配额/API。
- 未根据样帧或审计数字调整任何参数、阈值、测量窗或载体。

## §C-6 回交门（收工记录）

道路/走廊审计全部通过（§C-2），两张样帧用户逐张 `PASS`（§C-3）：

- 收工 `git status --porcelain` → 仅
  `M docs/current-status.md`（状态板本批次更新）、
  `M docs/archive/current-status-2026-08.md`（`rotate_docs.py` 机械淘汰
  一条旧实现批次日志）、
  `?? docs/evidence/P1-M3-BODY-001-1b.md` 与
  `?? docs/evidence/P1-M3-BODY-001-1b/`（本证据文件与样帧）；
  **零实现文件改动**，`Assets/`、`controller/`、`config/`、`tools/`、
  `tests/` 全部干净。
- 收工 HEAD 不变：`16a4da71583708a20a6892e15ade90afe7b1a052`
  （= `origin/main`）。
- `python3 tools/check_docs.py` 与
  `python3 tools/check_role_writes.py --role implementation` 均通过。
- 状态翻转：`P1-M3-BODY-001` →
  **`IMPLEMENTED_1B_AWAITING_ACCEPTANCE_CONFIRMATION`**，返回 Acceptance。
  Acceptance 消费 1b 之前不启动 1c；1c 首次 Play 仍必须是 BC-BODY1-15
  的臂 A trial 1，门序、冻结数值与终态规则一字不变。
