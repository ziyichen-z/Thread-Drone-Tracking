# P1-SCENE-006 batch 2 — 工具阶段证据（`C_b2tool`，无 config / 无 T1′ 工件）

Work ID: `P1-SCENE-006`（§30 batch-2 GO，BC-B2-1/2 工具阶段）
日期: 2026-08-04
角色: 实现（implementation）
依据: `docs/proposals/P1-SCENE-006-post-v2-anchor-route-amendment.md`
§30 BC-B2-1–8；审计基线 `d21aafc`（BC-B2-1）。工作树父提交为
`4d116ce`（Acceptance 的授权记录提交，不属于本实现批次；Acceptance 以
`d21aafc` 为 base 审计时应把该提交的 proposal/authorizations/status 路径
归因到已记录的 2026-08-04 Acceptance 批次）。

## 1. 零 diff 判定（BC-B2-1 的第一问）

`d21aafc`（含已复核 `C_1c = 3d6f0dc` 非 squash ancestry）上的已复核工具
路径集**不能**零 diff 执行正式候选 T1′，共四条独立障碍：

1. 唯一探针渲染入口 `RenderProbeFrames` 硬绑定冻结默认配置
   （`Scene006SceneRig.LoadFrozenScenario`）、基线 probe id
   `baseline-vfov60-selfcheck`、基线输出目录与 `s_init = 0`；不存在能
   加载 `config/scenario.p1-scene-006.json` 的入口。
2. 冻结工具集中没有把候选 config 与 BC-B2-3/4 冻结字段和已复核 P3 身份
   （`s_init` / trace 哈希 / `k*`）fail-closed 绑定的组件；缺它则错误
   config 字节可静默进入正式帧。
3. v1 manifest（`p1-scene-006-probe-manifest/v1`）没有 BC-B2-5 要求的
   身份字段（`capture_commit`、`tool_commit`、旧默认配置 SHA-256、空
   porcelain 证明等），正式 T1′ 工件无法记录要求的身份链。
4. Python 消费端 `tools/run_scene006_probe.py` 的 `_validate_manifest`
   只接受 v1 schema，任何新 manifest 需显式支持并逐字段校验。

**结论：按 BC-B2-2 形成 `C_b2tool`。本批次不写任何 config、不渲染任何
正式帧、不产生任何 T1′ 门值；`RunCandidateProbe` 从未被执行。**

## 2. C_b2tool 内容（全部在 BC-B2-2 白名单路径内）

### 2.1 新增

- `Assets/TetheredTracking/Editor/Scene006/Scene006CandidateProbe.cs` —
  候选配置 fail-closed 绑定加载器 `LoadAndBind`：P3 工件必须
  `P3_OK`（schema/selection/t6 缺一即拒）；`scenario_id` 必须
  `p1-scene-006-difficult-v1`；anchor x/z 精确 197.0/30.0，anchor y 与
  冻结支撑高 `0.0000013113417480781209` 差 ≤1e-9（P1 实测值的 JSON
  打印与工件打印相差一个 float32 ULP）；高度/vfov 必须等于 P3 决赛点
  （16.0/40.0），且 P3 决赛点自身必须是 BC-B2-3 点；路线逐顶点等于冻结
  族 B `(+60,-60)` 平移；scene_adjustments 恰为 §3.3.2 五行授权
  relocation（prefab+原 xz 匹配、落点/容差 0.1 对账、
  `mark_as_distractor`/`remove_from_scene` 全 false、
  `expected_distractor_count = 0`，BC-B2-4）；BC-B2-3 未列字段逐项等于
  冻结默认配置（drone/gimbal/sensor/target/evaluation/corridor/
  random_seed/road_data_sha256）。任一不符抛出，不产工件。
- `Assets/TetheredTracking/Tests/EditMode/Scene006CandidateProbeEditModeTests.cs`
  — 3 项测试：合成默认+合成候选的 happy path（绑定出 P3 身份四元组）；
  10 类逐项违规拒绝（scenario_id、anchor y、高度、vfov、路线顶点、
  relocation 落点、distractor 旗标、distractor 计数、capture_hz、
  corridor 字段）；缺 relocation 行与非 `P3_OK` 工件拒绝。

### 2.2 修改

- `Assets/TetheredTracking/Editor/Scene006/Scene006EvidenceGenerator.cs`
  — 新增 `RunCandidateProbe` 入口（仅工具能力，本批次未运行）：干净
  porcelain 前置（非空即抛）、场景文件哈希前后比对（零写合同）、重生成
  trace 与 P3 `finalist_trace_sha256` 不符即抛、候选 probe id/目录与
  基线隔离；`PrepareProbeDirectory` 参数化 probe id（基线调用点传原
  常量，行为不变）。`SceneFileHash`/`RunGit` 逐字复制已复核
  `Scene006CandidateGenerator` 的既有模式。
- `Assets/TetheredTracking/Editor/Scene006/Scene006ProbeRenderer.cs` —
  `Render` 参数化 `probeId`（基线调用点传原常量 `ProbeId`，v1 路径字节
  语义不变）+ 可选 `CandidateExtras`；`extras != null` 时发现的 `k*`
  必须等于 P3 绑定的 `ExpectedKStar`，否则在写 manifest 前抛出
  （`prompt_k_star_mismatch`）；写出 v2 manifest
  （`p1-scene-006-probe-manifest/v2` = v1 全字段 + BC-B2-5 绑定：旧默认
  SHA-256、候选 config 路径、`expected_k_star`、P3 工件路径+SHA-256、
  `capture_commit`/`tool_commit`/`git_status_porcelain`）。`Manifest`
  类解除 `sealed` 以允许 `CandidateManifest` 继承（见 §4 缺陷 1）；
  `created_by` 在 v2 构造函数中改为 `RunCandidateProbe` 身份。
- `tools/run_scene006_probe.py` — `_validate_manifest` 接受 v1/v2 两种
  schema；v2 逐字段校验：`baseline_scenario_sha256` 64-hex、
  `candidate_config_path`/`k_star_binding_artifact` 非空、
  `expected_k_star` 为 int（拒 bool）且等于发现的 `k_star`、
  `k_star_binding_artifact_sha256` 64-hex、`capture_commit`/
  `tool_commit` 40 字符、`git_status_porcelain` 必须为空串。v1 语义
  未动；result 工件经既有 `manifest_sha256` 绑定 manifest，身份链闭合。
- `tests/test_scene006_probe.py` — 新增 `Scene006CandidateManifestTests`
  2 项：v2 happy path 到 `AWAITING_EMBEDDING_FEASIBILITY_REVIEW`；
  11 个违规子用例（缺/短 baseline SHA、空路径、`k*` 失配、bool `k*`、
  缺/空工件绑定、39 字符 commit ×2、脏/缺 porcelain）逐一 fail-closed。

### 2.3 基线行为不变声明

基线探针路径（`RenderProbeFrames` → v1 manifest）只做了参数化重构，
两个调用点传入与原硬编码相同的常量；v1 manifest/truth 字节语义与
`d21aafc` 一致。既有 216 项 EditMode 与 324 项 Python 测试全部保持
原结果（见 §3），是该声明的回归证据。

## 3. 实际运行的命令与结果

- Unity EditMode（6000.4.1f1，无头）：**219/219 通过**（216 既有 +
  3 新增）。
  `runtime/test-results/p1-scene-006-editmode-b2tool.{xml,log}`。
  命令同 batch-1 证据 §3.1（`-testFilter TetheredTracking.Tests`，
  结果/日志文件名换 `-b2tool`）。
- Python：`.venv-track/bin/python -m unittest discover -s tests`
  **326 项，1 失败 = 既有 F3**（`test_check_docs` 基底破损，批次 1c
  已归因协调批次 `902a72c`，与本批无关）；
  `tests.test_scene006_probe` 单独 13/13。
- `python3 tools/check_role_writes.py --role implementation`：通过
  （最终未提交改动 11 个路径，全在白名单；含 Unity 在 EditMode 运行时
  为两个新 .cs 自动生成的 `.meta`、本证据文件、状态板与机械滚动归档）。
- **未运行** `RunCandidateProbe`；`config/` 无新文件；
  `runtime/p1-scene-006/` 只有已复核基线目录，无候选目录（BC-B2-8）。

## 4. 会话续接与缺陷修复记录

本批次跨两个实现会话：上一会话在完成主体实现后 token 耗尽中断，**未
运行任何测试、未写证据**。本会话（Claude Code `/implement` 备用入口）
重读全部改动后发现并修复三项，均在同一白名单路径集内：

1. **编译错误（阻断）**：`Scene006ProbeRenderer.Manifest` 声明为
   `sealed`，而新增 `CandidateManifest : Manifest` 继承之（CS0509，
   EditMode 套件必然无法编译）。修复：`Manifest` 解除 `sealed`，其余
   不动。修复后 EditMode 219/219 是编译与行为双重证据。
2. **v2 manifest 身份错误**：`CandidateManifest.created_by` 继承基线
   默认值 `…RenderProbeFrames`。修复：v2 构造函数写入
   `…RunCandidateProbe`。
3. **Python v2 校验零测试**：上一会话给 `_validate_manifest` 加了 v2
   分支但未加任何测试（套件仍是 1c 基线 324 项）。修复：补
   `Scene006CandidateManifestTests`（§2.2），套件 324 → 326。

## 5. 实现语义解释记录（交复核核对，非门变更）

1. **anchor y 容差 1e-9**：BC-B2-3 的 anchor y 字面值经 float32 存储后
   与 P1 工件打印相差一个 ULP（≈1.2e-13），1e-9 覆盖该差异且远小于任何
   几何意义量级；x/z 用精确相等。
2. **k\* 绑定是渲染期前置**：发现的采集帧 ≠ P3 绑定值即抛出，发生在
   manifest 写出之前——错误 k\* 不产生任何可误用的工件。
3. **v2 是 v1 超集**：消费端对 v2 只增不改，v1 校验语义逐字保留；
   result 经 `manifest_sha256` 绑定 manifest，BC-B2-5 的身份链
   （commit/config SHA/旧默认 SHA/porcelain）在 manifest 层记录。
4. **`LoadAndBind` 双向核对决赛点**：既检查候选 config 等于 P3 决赛
   点，也检查 P3 决赛点本身是 BC-B2-3 点——防御被替换的 P3 工件。
5. **零运行边界**：`RunCandidateProbe` 是为 config 阶段后的正式 T1′
   预置的工具能力；BC-B2-2 明令 `C_b2tool` 复核通过前不得运行，本批次
   遵守（§3 末条是实证）。

## 6. 未验证项与已知限制

- `RunCandidateProbe` 全链路（含 v2 manifest 落盘、场景哈希比对、
  porcelain 前置在 Unity 进程内的行为）**未端到端执行**——按 BC-B2-2/8
  它只能在 config 阶段与复核之后运行。当前覆盖面：加载器有 EditMode
  测试，v2 manifest 契约有 Python 消费端测试，渲染器 extras 分支只有
  代码审查面。
- `capture_commit`/`tool_commit` 只校验长度 40，不校验 hex 字符集。
- `RunGit`/`SceneFileHash` 与 `Scene006CandidateGenerator` 存在有意的
  模式重复（保持已复核模式逐字不变优先于去重）。
- EditMode 违规用例覆盖 10 类代表性字段，未穷举 BC-B2-3 冻结清单的
  每一个标量（清单本身由 `LoadAndBind` 逐项 `Require` 强制）。

## 7. 复核范围（给 Acceptance 写入审计与独立 Review）

- 候选：`C_b2tool = c0091d1`（用户 2026-08-04 授权提交；本行与状态板
  哈希指针由候选后的同批次记录提交回填，代码内容以 `c0091d1` 为准）；
  审计基线 `d21aafc`（BC-B2-1），diff 中 `4d116ce` 的
  proposal/authorizations/status 路径归因到 2026-08-04 Acceptance 批次。
- 实现批次逐文件清单（11 路径）：§2.1 新增 2 个 .cs 及其 Unity 自动
  生成的 2 个 `.meta` + §2.2 修改 4 + 本证据文件 +
  `docs/current-status.md` 状态板更新 + `docs/archive/
  current-status-2026-08.md`（`rotate_docs.py` 机械归档）。
- 复核重点建议：`LoadAndBind` 对 BC-B2-3/4 的逐字面核对是否有漏项；
  v2 manifest 字段集与 BC-B2-5 要求的对应；基线路径字节语义不变声明
  （§2.3）；`RunCandidateProbe` 的零写/身份前置顺序。

## 8. Unity 用例

无用户 Play 用例（BC-B2-8 零 Play 边界持续生效）。复现自动证据：
§3 的两条命令。

---

## 9. Review round 6 返工（F16/F17/F18，同一 BC-B2-2 工具停点）

依据 `docs/reviews/P1-SCENE-006.md` round 6 `REWORK_REQUIRED`（候选
`c0091d1`，端点 `d21aafc..c0091d1`）。本轮改动 6 个路径，全部在冻结工具
路径集内：三个 `Editor/Scene006/*.cs`、SCENE-006 的 EditMode 测试、
`tools/run_scene006_probe.py`、`tests/test_scene006_probe.py`。仍**未**写
`config/`、未渲染任何正式帧、未产生任何 T1′ 门值，`RunCandidateProbe`
仍从未运行（BC-B2-2/8）。冻结工具路径集本身**未增删**——本轮只是把
batch-1b 停点记录已声明的集合写进代码。

### 9.1 F16（阻断）：`tool_commit` 按 §5.6 推导，不再盖 capture HEAD

- `Scene006CandidateProbe.FrozenToolPaths` = batch-1b 停点记录
  （`docs/evidence/P1-SCENE-006-batch1b.md` §1）逐条声明的 9 条路径；
  记录写作 `dir/**`，代码用覆盖面相同的目录 pathspec。
- `ResolveToolCommit(runGit, captureCommit)`：
  `git log -1 --format=%H <capture> -- <冻结路径集>` 沿实际采集历史推导
  最后一个在冻结路径集中引入变更的 commit；必须是 40-hex，否则抛。与
  `capture_commit` 不等时再跑
  `git diff --name-only <tool>..<capture> -- <冻结路径集>`，非空即抛——
  §5.6 的零 diff 证明在进程内完成，推导若错则 fail closed，不可能静默
  产出身份。`RunCandidateProbe` 改用该结果（生产重载走真 git）。
- v2 manifest 增记 `frozen_tool_paths` 与 `tool_path_zero_diff_verified`；
  Python 消费端强制前者为非空字符串列表、后者严格为 `true`
  （`1` 与 `"true"` 均拒），并把 commit 字段从"长度 40"收紧为 40-hex
  正则（round-6 F19b）。
- **真实历史取证**（非测试断言）：在 `capture = dae3dec`（Acceptance 的
  文档提交）上推导得 `tool = c0091d1`，二者不等；`tool..capture` 冻结
  路径零 diff，其后无任何提交触碰冻结路径。这正是 F16 指出的合法
  formal-T1′ 执行形态，现在给出 §5.6 要求的身份而不是 capture HEAD。
- 测试：EditMode 新增 5 项 + 1 项集合钉死（桩 git 记录每次调用参数）：
  推导值不等于 capture HEAD 且两次 git 调用都带全部 9 条 pathspec；
  tool = capture 时只调用一次、无需零 diff 证明；零 diff 非空即拒；
  空输出/39 位/非 hex/多行输出/非 commit 的 capture id 逐一 fail closed；
  `FrozenToolPaths` 与 batch-1b 记录逐条相等。另加一项**真实仓库**用例：
  9 条 pathspec 是以单个参数字符串交给 git 的，若参数切分把它们并成一条
  pathspec，git 将无匹配、推导必须 fail closed——该用例用真 git 验证这一端，
  并用另一套 plumbing（`show --name-only` + `log <tool>..<head>`）复核
  "该 commit 自己改了冻结路径、其后没有任何提交改过"这一 §5.6 定义。
- **变异验证**（证明用例真的钉住语义）：把返回值改回 `captureCommit`
  后 `ToolCommitIsTheLastToolPathCommitNotTheCaptureHead` 失败
  （`Expected "2222…" But was "1111…"`）；变异已撤回，最终代码 SHA-256
  与变异前逐字节相同。

### 9.2 F17：BC-B2-3 未列字段的冻结扫描补齐三项

`LoadAndBind` 增加 `schema_version`、`route_corridor.
enable_dynamic_intersection_audit`、`route_corridor.enable_jump_diagnostic`
三项与冻结默认配置的相等比较，EditMode 违规用例 10 → 13 类。该用例同时
从"首个失败即中止"改为累计所有**未被拒绝**的违规名再断言为空，回归时
一次看全。**变异验证**：删掉两个 corridor bool 比较后该用例报
`binding accepted violations: 2 < "corridor-intersection-audit-flag",
"corridor-jump-diagnostic-flag" >`；单独删掉 `schema_version` 比较后报
`schema-version`。三项均为 load-bearing。

### 9.3 F18：零写比对移到 manifest 写出之前

`Scene006ProbeRenderer.Render` 的 v2 分支在构造/写出 manifest **之前**
取场景文件哈希并与 `SceneFileSha256Before` 比对，不等即抛——与已复核的
`StampAndWrite` 次序一致，零写违规不再留下一个成形可消费的探针目录。
比对通过后把 `scene_file_sha256_before/after` 记入 v2 manifest，消费端
校验两者均为 64-hex 且相等。`RunCandidateProbe` 中原先位于 `Render`
之后的比对随之删除（不是保留两处）。同一 v2 分支还新增两项写前前置：
缺场景哈希探针、或 `tool_path_zero_diff_verified` 不为真，一律抛出。

### 9.4 F19 处分（可选项，逐条说明做与不做）

- **(b) 已做**：commit 字段收紧为 40-hex 正则（消费端）；C# 侧推导也用
  同口径 `IsCommitHash`。
- **(c) 已做**：`P3ArtifactSha256` 改为对 `File.ReadAllBytes` 的原始字节
  取哈希（与 config SHA 同口径），不再对 `ReadAllText` 重新编码的文本
  取哈希。
- **(d) 部分做**：按 F18 把场景文件哈希前后值折进 v2 manifest；
  `scene_state_sha256` **未**加——它在本阶段没有可比对的参照值，且需要把
  第二个哈希助手复制进渲染器；已应用场景的身份现由 `capture_commit` +
  空 porcelain + 候选 config SHA 钉住。若 Review 认为仍需 parity，回到
  本停点再加。
- **(a) 未做**（有意）：路线顶点仍用 Unity `Vector3 ==`。理由是探针期的
  trace 哈希已按 float32 位模式把这条带宽闭合到 bit 级；而把加载器改成
  逐分量精确相等，会让下一阶段写 config 的十进制打印必须逐位 round-trip，
  给尚未开工的 BC-B2-3 配置阶段引入一个本轮无义务承担的失败面。
- **(e)**：无代码项，配置阶段操作注记照旧（探针产物未跟踪，跑完会弄脏
  下一次运行的 porcelain）。

### 9.5 本轮实际运行的命令与结果

- Unity EditMode（6000.4.1f1，无头，命令同 §3 但结果文件为
  `-b2tool-r2`）：**225/225 通过**（219 + 本轮 6 项）。
- `.venv-track/bin/python -m unittest discover -s tests`：**326 项，
  1 失败 = 既有 F3**（`test_check_docs.test_compliant_minimal_status_passes`，
  协调基线破损，与本批无关）；`tests.test_scene006_probe` 单独 **13/13**。
- 逐条违规取证：对 `_validate_manifest` 直接注入 13 组 v2 违规，
  每组报出的 `ValueError` 都是本轮新增校验的那一条（含
  `tool_path_zero_diff_verified` 拒 `1`/`"true"`/缺字段、
  before≠after 的零写漂移）。
- `python3 tools/check_role_writes.py --role implementation`：通过。

### 9.6 未验证项与已知限制（在 §6 之上新增/更新）

- `RunCandidateProbe` 端到端仍**未执行**（BC-B2-2/8 明令，复核通过并由
  Acceptance 开放配置阶段前不得运行）。因此 v2 manifest 落盘、场景哈希
  前后值、真 git 推导在**该入口内**的联合行为仍只有代码审查面；其组成
  部分分别有 EditMode（推导与 fail-closed 语义、真仓库 plumbing）与
  Python（manifest 契约）覆盖。
- 真实仓库用例依赖工作目录处于 git 仓库中（一次性 worktree 同样成立）；
  它断言的是结构性质（40-hex、零 diff、定义复核），不绑定具体 commit。
- `Scene006CandidateProbe.RunGit` 是已复核 `RunGit` 模式的第三份逐字
  副本（与 §6 同一取舍：冻结工具保持已复核模式不变优先于去重）。

### 9.7 复核范围（本轮）

- 候选：**`C_b2tool′ = b85f461`**（本行哈希指针由候选后的记录提交回填，
  代码内容以 `b85f461` 为准）；审计基线仍为 `d21aafc`（BC-B2-1），
  独立复核端点 **`d21aafc..b85f461`**。
- 写入审计预演（Acceptance 复跑同一命令即可）：
  `check_role_writes --role implementation --base d21aafc` 列出 4 个
  非实现路径，逐路径 `git log` 全部归因到非实现提交——
  `docs/authorizations.md` 与 `docs/phase1-single-drone-design.md` →
  `4d116ce`；提案 → `4d116ce` + `7372be0`；`docs/reviews/P1-SCENE-006.md`
  → `dae3dec`（round-6 复核记录）。以 `--base dae3dec`（即本候选单独）
  运行同一检查**通过**，9 个路径全部在实现白名单内，无未归因项。
- 本轮逐文件清单（6 个代码/测试路径 + 本证据文件 + 状态板 +
  机械归档）：`Scene006CandidateProbe.cs`、`Scene006EvidenceGenerator.cs`、
  `Scene006ProbeRenderer.cs`、`Scene006CandidateProbeEditModeTests.cs`、
  `tools/run_scene006_probe.py`、`tests/test_scene006_probe.py`。
- 复核重点建议：`ResolveToolCommit` 的推导+零 diff 是否逐字满足 §5.6
  （含 `FrozenToolPaths` 与 batch-1b 记录的一致性）；v2 manifest 新增
  四个字段与消费端校验的对应；F18 次序是否确实先比对后写；F19(a)/(d)
  两项未做的取舍是否可接受。
