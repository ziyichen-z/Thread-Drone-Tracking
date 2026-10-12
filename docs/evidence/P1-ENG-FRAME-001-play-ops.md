# P1-ENG-FRAME-001 Play 操作单（AC-20 / AC-21 / AC-23；§3.11 入口 5）

**状态：第二次 Play 已结束；AC-23安全/来源满足，AC-21的R7输出和用户目检未闭（2026-10-01）。** 放行记录见 `docs/unity-test-log.md`「UT-P1-ENG-FRAME-001-D1」；完整命令及预检工件见同名 `-play.md` / `-preflight.json`。 原「R1@K2 通过」前置由同停点最终通过轮 R2 承接，
解释见提案「R2@K2 通过轮消费」；R1 的 REWORK_REQUIRED 原 verdict 保留。本单 §0–§3 可先做零消耗预检，§4 仅在接受角色
按 workflow §4.5 核对 Unity 主机 HEAD/工作树与通过候选并放行后执行；K2 候选阶段 Play 次数为 0（提案 §5「已签执行合同」）。执行时由当轮发令角色逐步记录，结果写入
`docs/evidence/P1-ENG-FRAME-001-play.md`，用户反馈由接受/辅助角色代录进 `docs/unity-test-log.md`
`UT-P1-ENG-FRAME-001-D1`。

## 0. 信封与约束（逐字取自提案 §5「已签执行合同」Unity 证据列）

- Consuming = yes；scenario ID 0（复用 `deterministic-loop-untethered`，不得新建）；session ID 0；
  run ID ≤ 2（正式 1 + 环境性失败重试 1；作废 ID 保留、不复用）。
- Unity Play ≤ 2 次，每次墙钟 ≤ 330 s；仅首个机身命令之前的环境性失败（初始化失败、崩溃、配置拒绝）
  可重试，且两次之间代码和参数不变。
- 权重加载：NanoTrack-v2 每次尝试 1 次、总计 ≤ 2；YOLO/VLM 0；GPU·h / 付费 API / 下载 / 远端 0。
- run ID 预定：正式 `p1-eng-frame-001-play-1`；仅当触发上述重试条件时用 `p1-eng-frame-001-play-2`。
- Play 后不得据结果改参（改参 = 新 D 轮，提案 §3.9）。读数一律是描述量，不设门（提案 §3.10）。
- 解释器：`.venv-yoloe/bin/python`（下文记作 `<PY>`，执行前记录其 `--version` 与 `which` 输出）。

### 0.1 Unity 主机零消耗预检与职责（R2@K2消费）

用户在将执行 Play 的主机同步本轮已推送的 main 后，在同一个项目根完成 §1–§3，回传机器名、项目绝对路径和命令原始输出。
接受角色可在该主机只读核验并整理实际命令；supervisor 只转交与调度。预检不打开 Play、不实例化 tracker、不加载权重、不创建
scenario/session/run ID 或 run 目录；`--print-only` 仅打印预定 run ID，不占用它。Unity 场景/版本须与 §4 一致，Python 与 Unity
必须共用这个项目的 `runtime/`，无其他采集/控制进程占槽。检查预定两次 run 目录均不存在；已有即停回接受角色，不清理或复用。

```bash
hostname
pwd
command -v <PY>
<PY> --version
<PY> -c "import sys,cv2,numpy; print('python',sys.executable); print('cv2',cv2.__version__,'numpy',numpy.__version__); print('TrackerNano_create',callable(getattr(cv2,'TrackerNano_create',None)),'TrackerNano_Params',callable(getattr(cv2,'TrackerNano_Params',None)))"
ls -ld runtime/runs/p1-eng-frame-001-play-1 runtime/runs/p1-eng-frame-001-play-2
ls -l runtime/models/nanotrack-v2/*.onnx
shasum -a 256 runtime/models/nanotrack-v2/*.onnx
cat config/nanotrack-v2.models.json
```

run 目录的两条「不存在」是预期；解释器能导入 cv2/numpy、两项 Nano API 为 True，模型文件的名称/大小/sha 必须与模型说明一致。
本项使用 NanoTrack-v2，不以本机 CSRT 基线缺失或 `lap` 测试环境替代上述检查；不调用 `TrackerNano_create` 做试加载，
不借用权重额度。缺依赖/模型或输出不符先回接受角色，安装/下载/远端仍为 0，不现场补包。

预检输出先由接受/辅助角色记录为 `UT-P1-ENG-FRAME-001-D1` 的「零消耗预检」（不是 Unity verdict）；接受角色在发令前重新核对
§1 的主机 HEAD/status、§2 覆盖缺席与共享槽位、§3 哈希和完整命令及未用信封余额，把 HEAD/status 原始输出写入同条目，
逐路径核验通过候选到 HEAD 的差异只有本项/调度的白名单文档。仅全就绪后写明放行并将交接改为用户 Play、`Consuming=yes`；
下一接手人仍未达到这些条件时不得按 §4 执行。放行后代码/参数、主机/项目、覆盖状态或槽位变化须返回接受角色重新核对。
tracker 的启动和产物收集由当轮接受发令角色在 Unity 主机操作，用户只执行 Unity Play/暂停/恢复/退出与目检。

## 1. 放行前核对（接受角色，workflow §4.5）

```bash
git rev-parse HEAD
git status --porcelain
grep '^passed_candidate:' docs/reviews/P1-ENG-FRAME-001.md | tail -1
git diff --name-only "$(grep '^passed_candidate:' docs/reviews/P1-ENG-FRAME-001.md | tail -1 | awk '{print $2}')"..HEAD
```

HEAD 必须等于通过候选，或区间内只有白名单文档差异；否则不放行。通过候选与 HEAD 一律运行时解析，
本文件不写死。

本轮消费时本机主树干净，至通过候选仅有状态板、复核文件与派发日志文档差异；这只说明本机代码一致性，
不是另一台 Unity 主机的 §4.5 放行记录。采集发令必须重新取得目标主机结果。

## 2. 共享槽位核对与 ACQ 残留处置（§3.11 入口 4；提案 §9.1）

本项 Play **要求 `runtime/scenario_config.json` 不存在**：入口 1 转缺省后，Unity 无覆盖即加载
`config/scenario.untethered.json`；本项不生成任何覆盖文件。

1. 记录现状（只读）：

   ```bash
   ls -la runtime/
   test -e runtime/scenario_config.json && shasum -a 256 runtime/scenario_config.json || echo "scenario_config.json absent"
   ```

2. 若 `runtime/scenario_config.json` 存在（`P1-ENG-ACQ-001` Play D1 的残留副本，系留开启、
   `deterministic-loop-default`），**只移入 hold，不删除、不覆盖**（hold 目录名一次性，已存在即停下回接受角色）：

   ```bash
   test ! -e runtime/hold-frame-001-acq-scenario-override || { echo "hold exists: stop"; exit 1; }
   mkdir runtime/hold-frame-001-acq-scenario-override
   shasum -a 256 runtime/scenario_config.json
   mv runtime/scenario_config.json runtime/hold-frame-001-acq-scenario-override/scenario_config.json
   shasum -a 256 runtime/hold-frame-001-acq-scenario-override/scenario_config.json
   test ! -e runtime/scenario_config.json && echo "override absent"
   ```

   移动前后 sha256 必须相等；该动作由接受角色在 Play 核对时确认（提案 §9.1）。若接受角色另行裁定处置方式，以裁定为准。

3. 若未移开就进入 Play，三道 fail-closed 各自独立生效（提案 §9.1）：Unity 覆盖优先会加载残留副本；
   `track_loop` 首帧 `scenario_id` 校验拒绝；standoff 构造器因生效场景与 body 场景不等而拒绝。

4. 发令前及退出 Play 后再次记录 `test ! -e runtime/scenario_config.json` 的退出码；从预检完成至收集结束，
   不生成、不恢复该覆盖，不并行运行会写共享槽位的其他操作单。用户回传全程缺席确认。
   R2 §5 已说明：即便覆盖与 body 场景逐值相等，只要字节不同，manifest 两个 sha 不同，分析会 fail-closed；
   本项不使用这种覆盖、不改文件使两 sha 凑相等。覆盖缺席才满足 AC-23；发现存在即停回接受角色。

## 3. 冻结配置与命令（§3.11 入口 2 + 入口 3）

1. 配置哈希按运行时解析并记入 play.md（本文件不写死）：

   ```bash
   shasum -a 256 config/p1-eng-frame-001-body.json config/scenario.untethered.json
   ```

   run 结束后 manifest `body_planner.config_sha256` / `scenario_config_sha256` 必须与此处输出相等。

2. **入口 2**：以线束**缺省场景**（不传 `--scenario-config`）打印基础命令：

   ```bash
   <PY> tools/run_track_experiment.py --print-only \
     --tracker nanotrack-v2 \
     --init-frame 0 \
     --init-box 0.2765625 0.40625 0.1203125 0.15208333333333332 \
     --track-id target-0 \
     --condition follow \
     --ground-plane-y-m 0.2 \
     --run-id p1-eng-frame-001-play-1
   ```

   输出 JSON 必须满足：`scenario_id` = `deterministic-loop-untethered`；`scenario_config_sha256` 等于第 1 步
   `config/scenario.untethered.json` 的输出；`planned_duration_s` = 两圈 + 60 s（约 273 s）。任一不符即停。

3. **完整命令** = 第 2 步输出的 `command` 数组原样（逐 token，不重敲），再在末尾**逐字追加**以下三个 body 参数
   （线束不透传 body 参数；三个参数均无缺省，缺任一 `track_loop` 以 `parser.error` 拒绝）：

   ```text
   --body-policy standoff --body-planner-config config/p1-eng-frame-001-body.json --body-scenario-config config/scenario.untethered.json
   ```

   按下回车**之前**把实际完整命令行原文记入 play.md，并核对：含 `--scenario-id deterministic-loop-untethered`、
   `--run-id p1-eng-frame-001-play-1`、`--body-policy standoff`；不含 `scenario.default.json`、`--body-policy threshold`、
   `--body-policy hold`。不符即不得启动。

## 4. Play 步骤（用户执行 Play；发令角色操作 tracker）

沿用 BODY-001 臂 B 的帧 0 启动法（冻结初始框只对 frame 0 有效，保留帧缺省 128）：

1. 用户在 Unity 6000.4.1f1 打开
   `Assets/SimplePoly City - Low Poly Assets/Demo/SimplePoly City - Low Poly Assets_Demo Scene.unity`，
   Game 视图激活，进入 Play（计 1 次 Play），尽早暂停并报告「已暂停」。
2. **Unity 日志 source_path 核对（AC-23 T 行）**：Console 必须出现

   ```text
   Loaded tethered scenario 'deterministic-loop-untethered' from <项目根>/config/scenario.untethered.json
   ```

   出现其他 scenario 或来源（例如 `runtime/scenario_config.json`、`scenario.default.json`）即退出 Play、
   计环境性失败（配置拒绝）并回接受角色。
3. 发令角色核对保留帧：最小保留帧号必须为 `0`；帧 0 元数据 `scenario_id` = `deterministic-loop-untethered`：

   ```bash
   ls runtime/frames/ | head -3
   <PY> -c "import json;print(json.load(open('runtime/frames/frame_0000000000.json'))['scenario_id'])"
   ```

   用 `<PY> -m controller.track_loop --runtime runtime --dump-frame 0 --output <scratchpad>/frame0.jpg` 导出帧 0，
   叠加冻结像素框 `(177,195,77,73)`，用户只做匹配/不匹配目检（不重新框选）。不匹配即停，回接受角色。
4. 保持暂停，按第 3 节命令启动 tracker；随后恢复 Play，不再暂停。
5. tracker 到 `--planned-duration-s` 自然退出（退出码 0、final JSON 指向同一 run ID 的 `summary.json`、
   run 目录内 `summary.json` 与 `metrics.final.json` 均存在）后，请用户退出 Play，并报告 Console 有无报错、
   **目检观感（机身是否持续跟随、有无起停）**。单次 Play 墙钟上限 330 s。

## 5. 收集与读数（AC-21 / AC-23；不设门）

用户退出 Play 后，先把共享文件复制进 run 目录（create-once，已存在即停）：

```bash
RUN=runtime/runs/p1-eng-frame-001-play-1
test ! -e "$RUN/m3_body_truth.jsonl" && cp runtime/m3_body_truth.jsonl "$RUN/m3_body_truth.jsonl"
test ! -e "$RUN/metrics.json" && cp runtime/metrics.json "$RUN/metrics.json"
<PY> tools/frame_follow_replay.py --analyze-run "$RUN" \
  --truth "$RUN/m3_body_truth.jsonl" --metrics "$RUN/metrics.json" \
  --scenario config/scenario.untethered.json \
  --output "$RUN/frame_follow_analysis.json"
```

`docs/evidence/P1-ENG-FRAME-001-play.md` 按下列结构填写：

- 「安全读数」§T：机身水平位置出围栏帧数（`T_fence_violation_frames`）、高度偏离初始 ± 0.05 m 帧数、
  `tether_saturated` 为真帧数、机身距锚点超过 35 m 的帧数（如实报告，**不断言**）、
  `runtime/scenario_config.json` 全程缺席、Unity 日志 source_path 原文、帧元数据 `scenario_id`。
- 「安全读数」§P：命令水平速度最大值（≤ 4.0 m/s）、`vy` 绝对值最大值（= 0）、主标记与修饰计数。
- R-1…R-7 描述读数（`read_outs.all` 与 `read_outs.loop2`；R-7 `C_track` 评估器原样，不与 BODY-001 臂 B 比较）。
- 命令行原文、配置哈希运行时输出、HEAD/`git status --porcelain`、用户目检原话（由代录角色转写）。

**AC-23 平台量来源核对（沿用 R1 §5 P-3，不增验收项/阈值）**：§T 的全程平台位置、高度及饱和量、运动描述读数的实际速度从同一 Play 的
评估器旁车 `m3_body_truth.jsonl` 中 `body_world_*` / `applied_velocity_*` / `gimbal_saturated` / `tether_saturated` 读取；
这些是已发布平台量的同源记录（SensorCamera 相对机身位置为零、饱和标记读同一对象），不是运行时控制器读取目标真值。
收集时将现有保留帧元数据复制到该 run 目录的未用子目录（只复制、不改变原 128 保留上限），在 play.md 写来源说明，并按
`scenario_id` + `frame_id` 抽查元数据 `camera_position_world_m` 与旁车 `body_world_x/y/z_m`、两项饱和标记的同帧一致性，
记录帧号、两侧原值及结论；缺同帧记录或不一致回接受角色，不宣称 AC-23 通过。§P 的命令限速/`vy` 仍取 run 命令记录，
实际速度不能替代命令速度。保留分析输出 `scenario_binding`，确认所用场景 sha 同时等于 manifest 两 sha，来源路径原样记录；
跨机重算不要求绝对路径字符串相等，字节绑定仍必需。既有安全要求与 R-1…R-7 读数算法不变。

## 6. 失败分支（提案 §6 预注册失败模式）

**本次用户例外（2026-10-01）：** 账本「用户授权操作失误后再开一次 Play」原话“再开一次”，允许首轮未暂停提前退出、未启动 tracker 后重试一次。总 Play 仍≤2（已用1），单次≤330 s，代码/参数/模型不变；原件保留、共享残留已按机器记录保留式移动。两预定 run 均未创建，首次实际 tracker 仍用未用的正式 run 1。下列原环境性失败分支为历史约束，第二次 Play 后没有第三次 Play 额度，不得按环境性分支再开；AC 与其他额度不变。现行放行见 Unity 日志「操作失误重试授权与第二次放行」及 `P1-ENG-FRAME-001-retry-preflight.json`。


**本次墙钟例外与结果（2026-10-01）：** 用户先逐字授权“仅本次延长至420秒”，后授权“仅本次延长至480秒”，均在越界前入账；只替换当前第二次总墙钟上限，不改约273秒仿真计划或其他维度。tracker已自然结束0、Unity已退出；累计Play2/加载1/run1。实测465.024116s是首末capture跨度，完整按钮墙钟未独立取得，不冒充精确在限。AC-21 R7=null及用户看不到机身的目检缺口见 `play.md`；实现只修既有R7义务并用保存run零消耗重分析，无第三次Play授权。前文§0及本节330秒值是原合同/当轮历史值，当前例外仅此一次。


- NanoTrack 帧 0 初始化失败、Unity 崩溃、配置拒绝（含第 4 节第 2 步 source_path 不符）且发生在首个机身命令之前：
  计环境性失败，作废 run ID 保留、不复用，代码与参数不变，以 `p1-eng-frame-001-play-2` 重试一次；仍失败回接受角色。
- 首个机身命令之后的任何失败：不重试，如实记录，回接受角色。
- `fallback_margin`、`hold_estimate_*` 占比高或出现触边/避障修饰：如实报告，不改参。
