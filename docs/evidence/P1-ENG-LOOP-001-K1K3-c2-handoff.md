# P1-ENG-LOOP-001 — K1K3 第二次候选交接（C2@K1K3 → R3@K1K3）：runInBackground 单字段与操作单 C 冻结集

Owner: Implementation（Claude Code `/implement`），2026-09-22。轨道 `engineering-v1`，停点 `K1K3`。
输入：同名提案 Pending rulings R-B1…4、AC-4 修订3、AC-12 修订3；授权 `docs/authorizations.md` 2026-09-22
「单字段后台运行设置与追加两次诊断」。按 AC-12 修订3，本批**不是** R2 的 `REWORK_REQUIRED` 修复，先过
C2@K1K3 再交 R3@K1K3；C/R 计数沿用 1/2，不重置。本批零消耗：零 Play、零模型启动/查询、零 ID、零 5060 传输。

## 1. 候选与完整 diff

- **候选** = 首次加入本文件的提交（运行时解析：`git log --diff-filter=A --format=%H -- docs/evidence/P1-ENG-LOOP-001-K1K3-c2-handoff.md`）。
- **全量 diff 基线** = R2 轮 `passed_candidate`（写本文件时复核文件的最后一条；R3 写入新行后改取倒数第二条）。
  完整候选 diff：`git diff <R2 passed_candidate> <候选>`。按来源分四类如下（`--name-status` 全表可由该命令复现）：

| 类 | 路径 | 说明 |
|---|---|---|
| A 本批 PLAY_GOVERNING | `ProjectSettings/ProjectSettings.asset` | 1 行：`runInBackground: 0` → `1`（AC-4 修订3） |
| A 本批冻结操作单（PLAY_GOVERNING，R-B1 点名） | `docs/evidence/P1-ENG-LOOP-001-operations-c.md`、`-operator.sh`、`-operator-watch.py`、`-5060-runner-b.py` | 四个文件在 R2 之后才加入（阶段 B 准备批次），相对 R2 为**整文件新增**，复核按整文件读；本批相对上一版的改动见 §3 |
| B 本批证据 | `docs/evidence/P1-ENG-LOOP-001-K1K3-c2-handoff.md`（本文件）、`-c2-carrier-selftest.py`、`-c2-carrier-selftest.log`、`-tests-c2.log`；`-stage-b-prep.md` §7 | 自证、自测与全套日志 |
| B 阶段 B 准备与诊断记录（R2 之后、本批之前，实现角色） | `-build-stage-b-manifest.py`、`-transfer-manifest-5060-stage-b.json`、`-service-5060-b.log`、`-stage-b-prep.md`、`-tests-client-env.log` | 未改动（清单将在 R3 通过后按新候选重建，见操作单 §1） |
| C COORD-013/014 协调批次（用户直接授权，账本 2026-09-21/22 同名条目） | `tools/check_docs.py`、`tools/check_role_writes.py`、`tests/test_check_docs.py`、`tests/test_check_role_writes.py`（均属 PLAY_GOVERNING 的 `tools/`/`tests/`）；`AGENTS.md`、`.claude/commands/{chore,implement}.md`、`.cursor/commands/coding.md`、`docs/{collaboration,engineering}-workflow.md`、`docs/roles/*`、`docs/workflow-changelog.md`、`docs/parked-status.md`、`docs/proposals/COORD-013-*`、`docs/evidence/COORD-013-*` | 非本 work item 实现；按 R-B1 裁定如实列为独立协调批次，**不冒称白名单文档**；运行时不导入 |
| D 其他角色文档 | `docs/{authorizations,current-status,implementation-status,phase1-single-drone-design,unity-test-log}.md`、同名提案、`docs/reviews/P1-ENG-LOOP-001.md` | 接受/复核/辅助角色写入 |

**零改动核对（相对 R2，命令输出见 `-c2-carrier-selftest.log` 第 1 节）**：`controller/`、`Assets/`、`config/`、
`Packages/`（含 `packages-lock.json`）、`tools/eng_sft/`、`tools/language_serve.py`、`tools/language_latency.py`、
`tools/requirements-language.txt` 均 `git diff --quiet` 退出码 0；`ProjectSettings/` 只有上表 1 行（`--numstat` = `1 1`，
同文件其他字段与 `ProjectSettings/` 其他文件零差异）。

## 2. workflow §4.3.1 四项自证

1. **范围与接口冻结**：本批只落实 R-B1…4 点名范围——`runInBackground` 单字段、操作单 C 与三个具名执行载体，
   外加证据文件。帧/控制协议、坐标时间语义、K 收据（`K_ret`/`K_conf`/`K_pub`）、`T_pub`/`T_stall`、跟踪核心、
   模型决策、客户端解释器与 5060 服务形态/端点/权重身份全部不变（§1 零改动核对）。
2. **相称的实现者测试**：停点全套一次 `docs/evidence/P1-ENG-LOOP-001-tests-c2.log`（系统 `python3`）：
   `Ran 1524`，`FAILED (failures=1, errors=9, skipped=24)`。9 项 errors 与 K1K3 R1 修复批基线
   （`-tests-r1-fix.log`，`Ran 1515`，errors=9）逐名相同（缺 cv2 的既有导入错误等）；测试数 +9 来自 COORD-013/014 的
   检查器测试。**新增 1 项 failure** `test_dist_data_round4.RealArchiveClosureTest.test_zero_unmatched_and_zero_multi_matched_jpg`
   为环境所致：该测试只读枚举 `runtime/` 下全部 JPG，当前 404 个未匹配文件全部是阶段 B 诊断 Play 的帧
   （`runtime/frames/` 128 个为诊断 2 残留、`runtime/hold-diag-loopb-2/frames` 148 个、`runtime/hold-diag-loopb-2b/frames`
   128 个），均在基线运行之后产生；本批未改任何被测代码。因本批不做槽位隔离（禁止触碰共享槽），残留保留原样，
   下次 Play 前按操作单 §2 第 3 步移入 hold 目录。本批代码导致的新增失败：0。
   执行载体另有离线自测 `-c2-carrier-selftest.py`（21 项全 `ok`；对 R2 之后、本批之前的旧版两个载体跑同一自测为红，
   说明断言不空转）与 `lc_check`/`lc_run` 的 zsh、bash 负向运行（均拒绝、退出码 1/2），输出见 `-c2-carrier-selftest.log`。
   `controller/` 未改，K1K3 的语言 focused 与客户端环境证据（`-tests-r1-fix-focused.log`、`-tests-client-env.log`）仍对应同一字节。
3. **已知 Unity 失败**：唯一已知问题是 `runInBackground: 0` 导致失焦停帧（prep §4.3），本批按裁定改设置；
   **修改是否生效未验证**，只有 R3 通过后的新增诊断能证实（操作单 §4 第 2 步），不以字段已改推定生效。
   首批追平与人眼保真检查同样未完成。无待修的代码类 Unity 失败。
4. **复核文件、状态板、候选 commit、未验证风险**：候选提交与本文件同批；状态板交接行转 Acceptance（C2@K1K3），
   只写本文件指针；未验证风险见 §4；复核范围见 §5。

## 3. 逐 AC 证据指针

| AC | 结论（实现者自证，非独立复核） | 证据指针 |
|---|---|---|
| AC-4 修订3 | `runInBackground` 0→1 为唯一 Unity 侧改动，由实现角色提交；其余具名路径零改动；效果待诊断核实 | cmd:`git diff --numstat <R2> <候选> -- ProjectSettings` = `1 1`；cmd:`git diff --quiet <R2> <候选> -- Assets config tools/eng_sft Packages`；artifact:`-c2-carrier-selftest.log` §1；artifact:`-stage-b-prep.md` §7 |
| AC-12 修订3（额度） | 旧诊断 3/2（超用 1）单列、新增 0/2，会话号 `diag-loopb-3`/`-4`；启动 ≤10、查询 ≤400/每次 ≤40、正式额度不增；5060 服务 `amend` 后冻结旧诊断会话、新诊断 ≤2，`serve` 未 `amend` 拒绝启动 | artifact:`-operations-c.md` §0/§1；artifact:`-5060-runner-b.py`（`DIAG_AMENDMENT`、`diag_amendment_record`、`session_refusal`、`amend`/`serve` 块）；test:`-c2-carrier-selftest.py`（runner 15 项） |
| AC-12 修订3（顺序） | 新候选通过前不开任何 Play；R3 通过后才用新增诊断；诊断先核实持续供帧，再首批追平与人眼检查；发布门失败或无收据即停正式 | artifact:`-operations-c.md` 文首状态、§2 第 6 步、§4 |
| AC-12 修订3（对应性） | 采集候选 = 最新 `passed_candidate`（运行时解析）；Python worktree HEAD 对齐且干净；主工作树 `Assets/config/ProjectSettings/Packages` 与四个冻结文件相对候选零差异、无未跟踪（含 `_Recovery`）；检查在 Unity 打开之后、Play 之前；`lc_run` 未过检查拒绝启动；操作者脚本与 watch 从采集 worktree 运行 | artifact:`-operator.sh`（`_lc_candidate`、`_lc_check_body`、`lc_check`、`lc_run` 门）；artifact:`-operations-c.md` §1/§2/§3；artifact:`-c2-carrier-selftest.log` §3（负向运行） |
| AC-12 修订3（5060） | Python 未改须按新旧两条 `passed_candidate` 核对字节相同后复用；清单按新候选重建、runner 与新候选逐字比对后传输；不把混用版本称为一个 checkout | artifact:`-operations-c.md` §1「5060 服务」1–4 |
| R-B4（持续供帧观测） | watch 记录最前台 App 切换、Unity 不在最前台时到达的帧数、≥2 s 帧停滞告警与停滞时长；只作诊断观测，不作门证据 | artifact:`-operator-watch.py`（`frontmost_app`、`on_focus`、`on_frame_supply`）；test:`-c2-carrier-selftest.py`（watch 6 项） |
| AC-5 修订1 相关的预览可见性（操作层） | 预览打开时另发系统通知并打印 `file://` 路径；看不到可点路径；不改预览生成/确认门 | artifact:`-operator-watch.py`（`open_preview`）；artifact:`-operations-c.md` §3/§4 第 3 步 |
| AC-1…12/16/17 其余 | 运行时代码零改动，沿用 R2 `PASS_WITH_NOTES` 的原候选证据 | cmd:`git diff --quiet <R2> <候选> -- controller tools/language_serve.py tools/eng_sft` |
| AC-13…15 | 待阶段 B 正式 Play；不申请 UNITY_NA | — |

## 4. 未验证项与已知限制

- **后台运行效果未验证**：Unity 编辑器在失焦时是否仍按 5 Hz 供帧（`runInBackground` 之外还可能受 macOS 节能或编辑器节流影响）只能由诊断证实；若 watch 报「帧停滞」，按操作单 §0 硬停止上报，不再用余下诊断重试同一操作。
- **首批追平、确认延迟、人眼保真检查**：均未取得（诊断 1/2 均无数据）。
- **预览可见性**：通知与路径打印是新增的操作辅助，用户能否及时看到只有诊断能证实。
- **5060 端**：`amend` 尚未在 F 盘账本执行；新 runner 与按新候选重建的清单尚未传输（均在 R3 通过后，按操作单 §1）。清单生成脚本从工作树读 runner，操作单 §1 第 1 步先核对工作树 runner 与新候选相同。
- **watch 的前台 App 读数**依赖 macOS `lsappinfo`（无需额外权限，本机实测可读；Unity 的显示名为 `Unity`，取自其 `Info.plist`），每秒轮询一次，`unfocused_frames` 的计数边界有 ≤1 s 的粒度误差；读不到时记 `None`，不影响任何门。
- **自测的范围**：runner 的服务主体在导入时即执行（F 盘、CUDA），自测只以 `ast` 抽取预算定义与 `amend`/`serve` 两个顶层块单独执行；watch 用归档真实帧元数据（`runtime/frames.1b-diagnostic-hold`，只读复制）与脚本化时钟/前台序列驱动。
- **全套新增 1 项 failure** 为环境（§2 第 2 条）；该测试在阶段 B 诊断残留与 hold 目录存在期间会持续失败，是否把 `runtime/hold-diag-loopb-*` 列入其枚举排除属另一 work item 的测试范围，本批不改。
- 注记沿用：R1/R2 复核注记与 F3 `SCOPE_GAP` OPEN 不变；操作单 §8 按接受裁定解释。

## 5. 给复核角色的范围（R3@K1K3）

- 全量 diff `git diff <R2 passed_candidate> <候选>` 于 PLAY_GOVERNING 非空：`ProjectSettings/ProjectSettings.asset`（1 行）、四个冻结操作单文件（整文件）、COORD-013/014 的 `tools/check_*.py` 与 `tests/test_check_*.py`（独立协调批次，由复核决定处置口径）。
- 重点：单字段之外零改动；`lc_check` 的每一项是否真能挡住 AC-12 修订3 列举的不对应情形（HEAD、未提交/未跟踪、`_Recovery`、冻结文件漂移、Unity 未打开、槽位残留）；runner 预算逻辑（旧诊断冻结、新诊断 ≤2、其余上限不变、`serve` 门）；watch 是否只读（不写 `runtime/`）；操作单顺序（先 Unity 后检查、先持续供帧后 ask、硬停止）与信封/裁定是否一致。
