# P1-M3-BODY-001 预检返工 r8 证据（round 20 §B → round 21 §B → round 22 §C）

**范围**：Acceptance round 22 §C 的失败路径返工（在 round 20/21 已通过项
之上）。**零 Play、零 run ID、零指标、零发布**；void 现场未移动一个字节。

历史候选 `8d5a923`（round 21 退修）与 `78d8f91`（round 22 退修）保留在
历史中可追溯，未重写历史。

## 0. round 22 §C 失败路径返工（本轮新增）

### 0.1 缺陷

`run_preflight` 原本只在 `_construct` **正常返回后**计算 `after`
fingerprint。任何 loader/构造器「先改写受保护 runtime、再抛异常」时，
`PreflightError` 直接向外传播，**后置比较根本不执行**，操作者只看到构造
失败，不知道现场已被污染。round 21 的 31 个测试只覆盖「改写后正常返回」，
因此漏掉该分支。

### 0.2 修复（§C.1/§C.2 按字面）

`before` 取得后，无论 `_construct` 正常返回还是以普通异常失败，
`after = side_effect_fingerprint(...)` **恰好执行一次**并比较：

- fingerprint 有差异 → 抛 `PreflightError`，消息**必含**
  `_describe_fingerprint_delta` 的具名差异；若同时有构造异常，其**类型与
  消息**作为 `secondary context` 保留在同一条错误里（并以 `from primary`
  保留异常链）。副作用差异**不因已有构造错误被跳过或降级**。
- 无差异但有构造异常 → 原样重抛该异常。
- **只有**「无主异常且 fingerprint 相等」才生成 PASS。
- **不删除、不回写**任何受保护工件来掩盖现场。

### 0.3 实测：复现 Acceptance 的注入

在临时目录中令 `DinoV2Embedder` factory 先把已有 `metrics.json` 由
`before` 改写为 `after!` 再抛 `RuntimeError("injected")`，实际错误逐字为：

> `preflight changed protected runtime state — it must create no run ID, run
> directory, metric or publication: runtime/metrics.json changed bytes
> (6→6, 6db7d803e74f1ffa…→f778dacc09a32699…); construction also failed and is
> retained as secondary context (PreflightError: DinoV2Embedder construction
> failed (RuntimeError: injected))`

两个具名同时出现；`metrics.json` 磁盘内容仍为 `after!`（**现场保留，未被
清理**）。注意该例 **字节数相同（6→6）**，仅 SHA-256 不同——只比大小的
实现会漏掉它。

### 0.4 新增反例（§C.3，全部通过）

| 用例 | 断言 |
|---|---|
| 已有 `metrics.json` 改写后 factory 抛异常 | 同时具名 `runtime/metrics.json` + `changed bytes` + `secondary context` + 原异常类型/消息；磁盘保留污染值 |
| 创建正式样式 run 子目录后 factory 抛异常 | 同时具名 `run directories created` + `p1-m3-body-001-arm-a-trial-1` + `secondary context` + 原异常；泄漏目录**保留未清理** |
| 无污染的普通构造失败 | 只报构造错误，**不得**出现 delta 子句或 `secondary context` |
| **后置 fingerprint 恰好执行一次** | 计数包装证明成功路径与失败路径都是 before+after 共 2 次调用——不以「反正退出码非零」替代比较 |
| loader（非 factory）先污染再抛 | 同样具名 delta + secondary context，证明防护覆盖整条构造链 |

### 0.5 本轮回归

| 命令 | 结果 |
|---|---|
| `.venv-track/bin/python -m unittest tests.test_preflight_reanchor_env` | **36 ran / OK（1 skipped）** |
| `.venv-yoloe/bin/python tests/test_preflight_reanchor_env.py` | **36 ran / OK（1 skipped）** |
| `.venv-track/bin/python -m unittest discover -s tests` | **488 ran / OK（1 skipped，零失败）** |
| 真实 `.venv-yoloe` 预检 | `PASS`，退出 0，`side_effect_identity.unchanged = true` |
| 真实 `.venv-track` 预检 | 退出 1，**stdout 0 字节** |

round 21 已通过的全部测试保留（31 → 36，新增 5 条失败路径用例）。本轮
改动路径仅 `tools/preflight_reanchor_env.py`、
`tests/test_preflight_reanchor_env.py`、本证据与状态板；**未再碰
`tools/check_*.py`，操作单命令无需改动**。

以下 §1–§5 为 round 21 轮次的记录，其结论经 round 22 §A 确认成立，予以保留。

## 1. round 21 §B 逐条对照

| 要求 | 落点 | 状态 |
|---|---|---|
| B.1 `tools/check_track_env.py` 逐字节恢复为 `34c1ec1`；不改任何 `tools/check_*.py`；不顺手修审计器漂移 | 见 §3.1 | **DONE** |
| B.2 迁到 `tools/preflight_reanchor_env.py` + `tests/test_preflight_reanchor_env.py`；CLI 只接受且必须提供 `--reanchor-config PATH`；操作单 step 0 换新命令；恢复文件内无代理/导入/兼容分支 | 新工具与测试；操作单 revision 9 | **DONE** |
| B.3 cv2/torch/torchvision/ultralytics 原始 `__version__` 与 pin 逐字相等，不规范化/截断/剥 `+local`；测试证明 `2.13.0+cpu` fail closed | `compare_raw_version`；`RawVersionLiteralityTest` | **DONE** |
| B.4 机械副作用恒等：`runtime/runs/` 直接子目录名集合 + 四文件（三发布 + `metrics.json`）的 present/size/SHA-256；反例含「原地改字节仍存在」与 metrics 创建/改写 | `side_effect_fingerprint`；`SideEffectIdentityTest` | **DONE** |
| B.5 成功时 stdout 只有一个可直接 `json.loads` 的 JSON；真实子进程锁定；继续覆盖缺包/raw pin 不等/schema/模型/哈希/构造失败；证据记 focused、full、真实 PASS/FAIL 与恢复字节恒等 | `SubprocessContractTest`；本文件 §3 | **DONE** |
| B.6 范围冻结 | §5 | **DONE** |

## 2. cv2 pin 的读法（round 22 §A.2 已确认为 binding clarification）

§B.3 要求 cv2 也「直接比较原始 `__version__` 与配置 pin」，但 cv2 在配置里
有两个候选字段：

- `opencv.tested_version = "5.0.0"` —— 与 `cv2.__version__` 同形，**可能相等**；
- `opencv.package_pin = "opencv-contrib-python==5.0.0.93"` —— requirement
  specifier，**永远不可能**等于 `__version__`。

唯一自洽的读法是取 `tested_version`，这也与生产 `NanoTrackV2Tracker` 的
OpenCV 版本门一致（`controller/trackers.py:401-407`）。实现按此执行并在
报告 `packages.cv2.pin_source` 中逐字写明来源。

**round 22 §A.2 已把该读法确认为 binding clarification**：cv2 raw pin 取
`config/nanotrack-v2.models.json` 的 `opencv.tested_version`；`package_pin`
是发行包 requirement（含包名与 build revision），不是可与 `cv2.__version__`
逐字比较的版本串。此项不再是待确认事项。

## 3. 实测结果

### 3.1 受保护路径已恢复（B.1）

| 检查 | 结果 |
|---|---|
| `git show 34c1ec1:tools/check_track_env.py \| shasum -a 256` | `09e3b27e827eb319ac2c85a6468c07c89652900439c9bb14120c0d84bce73237` |
| `shasum -a 256 tools/check_track_env.py` | `09e3b27e827eb319ac2c85a6468c07c89652900439c9bb14120c0d84bce73237` —— **相等** |
| `git diff 34c1ec1 -- tools/check_track_env.py` | **0 行** |
| `grep -n "preflight_reanchor\|reanchor" tools/check_track_env.py` | **无命中**（无代理/导入/兼容分支） |
| 无参数运行（`.venv-track`） | 退出 0，四字段 `opencv_version`/`constructor`/`tracker_type`/`environment` 与基线一致 |
| `tests/test_check_track_env.py` | 已删除（属被退修批次新增，不在 §B.6 允许路径内） |

`tools/check_docs.py`、`tools/check_role_writes.py`、`tools/rotate_docs.py`、
`tools/githooks/` 本批**零改动**；round 21 §A.1 指出的审计器模式漂移
（`INFRA_PATTERNS` 只列两个具体 `check_` 文件，而 `AGENTS.md:118` 写的是
`tools/check_*.py` 通配）**按 §B.1 未修**，留给协调批次。

### 3.2 真实预检 PASS（`.venv-yoloe`，退出码 0）

```bash
.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json
```

stdout 直接 `json.load` 成功（无切片、无过滤）：

| 字段 | 实测值 |
|---|---|
| `status` | `PASS` |
| `interpreter.executable` / `prefix` | `~/TetheredDroneTracking/.venv-yoloe/bin/python` / `…/.venv-yoloe` |
| `packages.cv2` | raw `5.0.0` = pin `5.0.0`（`nanotrack spec opencv.tested_version`） |
| `packages.torch` | raw `2.13.0` = pin `2.13.0` |
| `packages.torchvision` | raw `0.28.0` = pin `0.28.0` |
| `packages.ultralytics` | raw `8.4.104` = pin `8.4.104` |
| `reanchor_config.sha256` | `593734d67ada73a0304d67d27c6ae536be616d2180f744336b85ff6e0ac706d2` |
| `nanotrack.model_sha256.backbone` | `530bdd0cd00f19afab79a863e71ba71e3312395a5dc9151af675082bdaaa2fc4` |
| `nanotrack.model_sha256.neckhead` | `0d8c0637be849f092cc7236cae02e55c8b9455ebe37ba50601d6115db4247cd9` |
| `constructors` | `controller.reanchor_models.YoloeProposer`、`controller.reanchor_models.DinoV2Embedder`、`controller.trackers.NanoTrackV2Tracker` |
| `side_effect_identity.unchanged` | `true`；`checked` 逐条列出 runs 目录名集合与四个文件的 present/size/sha256 |

四个 raw 版本串与各自 pin **逐字相等**，未做任何规范化。

### 3.3 真实反例：造成作废的解释器（`.venv-track`）

**退出码 1**，**stdout 0 字节**，stderr 为 JSON `status = FAIL`，`reason`
逐字：

> `package 'torch' could not be imported in this interpreter
> (ModuleNotFoundError: No module named 'torch'); the re-anchor carrier
> cannot be constructed here`

即本工具若在 2026-08-09 尝试 1 之前存在，会在进 Play 之前拦下该次失败。

### 3.4 自动测试

> 下表是 round 21 轮次的数字（focused 31、full 483）。**本轮 round 22 已增
> 至 focused 36、full 488**，最新结果见 §0.5；两轮的 skip 结构与结论一致。

| 命令 | round 21 结果 |
|---|---|
| `.venv-track/bin/python -m unittest tests.test_preflight_reanchor_env` | **31 ran / OK（1 skipped）** |
| `.venv-yoloe/bin/python tests/test_preflight_reanchor_env.py` | **31 ran / OK（1 skipped）** |
| `.venv-track/bin/python -m unittest discover -s tests` | **483 ran / OK（1 skipped，零失败）** |

**两个 skip 互补，合起来无覆盖缺口**：`.venv-track` 缺 re-anchor 栈，跳过
「真实栈成功路径」而执行「真实栈失败路径」；`.venv-yoloe` 满足栈，跳过失败
路径而执行成功路径。两个解释器各跑一次，两条都被真实子进程覆盖。此外
`test_success_path_stdout_purity_in_any_interpreter` **不依赖重模型**：它用
真实子进程注入两个会向 stdout 打印（`Could not import tifffile`、
`xFormers is not available`）的构造器，断言 `json.loads(stdout)` 直接成功
且噪声出现在 stderr，因此**在任何解释器下都锁定 §B.5 的单一 JSON 合同**。

反例覆盖（全部要求 `PreflightError` 或非零退出）：

- **raw 版本字面性**：四个包各自带 `+cpu`/`+dirty`/`+local` 后缀 → fail；
  四个包各自普通版本不等 → fail；四个包各自缺失 → fail；缺 `__version__` → fail。
- **副作用恒等**：已有发布文件**原地改字节但仍存在** → fail；**同字节数
  不同内容** → fail；`metrics.json` 创建 → fail；`metrics.json` 改写 → fail；
  发布文件被删除 → fail；创建 run 目录 → fail；未触碰 runtime 时 PASS 且
  before/after 相等；fingerprint 确实记录 size 与 64 位 SHA-256。
- **构造链**：config schema 失败、NanoTrack spec 失败、config 路径不存在、
  模型哈希失败、身份不符、只给一个模型哈希、`YoloeProposer` 构造失败、
  `DinoV2Embedder` 构造失败，以及**「四个包全部 import 成功但构造器失败
  → 不得 PASS」**专项用例。
- **CLI/stdout 合同**（真实子进程）：缺 `--reanchor-config` → 非零；未知参数
  → 非零；失败时 stdout 为空且 JSON 只在 stderr；config 不存在 → 非零且
  stdout 为空。

> 全套从 `475` 变为 `483`：删除 `tests/test_check_track_env.py`（23 条）、
> 新增 `tests/test_preflight_reanchor_env.py`（31 条）。基线 452 + 31 = 483。

## 4. 未验证项与已知限制

- 预检**不做推理**：证明模型能构造与加载，不证明检测/嵌入的数值行为。
- 报告只陈述**实际执行的检查**：`side_effect_identity.checked` 列出的就是
  比对项本身。本轮不再出现「不联网/不读帧」这类未测量声明——工具确实不读帧、
  不推理、不取远端工件，但那是代码路径的性质，未作为结论写进 PASS 报告。
- 预检不校验 Unity 侧状态，也不替代 §2/§2.1 的隔离与树状态记录。
- 本批未运行 Unity Edit Mode（零 C# 改动，无相关面）。
- `.venv-yoloe` 下 `python -m unittest tests.<mod>` 无法解析 `tests` 命名空间
  包（virtualenv 的 sys.path 处理差异），故该解释器改用直接运行测试文件；
  这是环境调用方式差异，非测试内容差异。

## 5. 范围冻结（round 21 §B.6）

| 路径 | 性质 |
|---|---|
| `tools/check_track_env.py` | **恢复**为 `34c1ec1`（字节恒等，见 §3.1） |
| `tests/test_check_track_env.py` | **删除**（被退修批次新增） |
| `tools/preflight_reanchor_env.py` | 新增（普通实现工具，非 `check_*`） |
| `tests/test_preflight_reanchor_env.py` | 新增（31 用例） |
| `docs/evidence/P1-M3-BODY-001-1c-preflight.md` | 操作单 revision 9 |
| `docs/evidence/P1-M3-BODY-001-preflight-r8.md` | 本文件 |
| `docs/current-status.md` | 状态板 |

**零 `controller/`、零 C#、零 config/scenario 字节、零模型字节、零
`tools/analyze_m3_body.py`、零研究口径改动；零 Play、零 run ID/指标，
void 现场工件未创建、未移动、未删除。** 不重开 `e438b97` 的独立 Review。

**人工归因说明**：`tools/check_role_writes.py` 对 `tools/check_*.py` 存在
已知漏检（round 21 §A.1），因此本批不以该工具的 PASS 作为基础设施合规
凭据；上表由人工逐路径核对，并以 §3.1 的字节恒等证明受保护文件未被改动。

下一步由 Acceptance 核验 diff 与真实 `.venv-yoloe` 预检，**通过后才可向
用户申请新的单次 Play GO**；本批不代为申请。
