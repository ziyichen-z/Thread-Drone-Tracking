# P1-ENG-ACQ-001 — Play D1 操作单（在 Unity 主机上执行）

初稿：`PlayD1准备` 派发 `P1-ENG-ACQ-001-PlayD1准备-20260929T212906Z-d1a8`（Implementation，Opus 子代理，2026-09-29）；后续追加 R1@K1K3 消费后的预检报告 HEAD 回传与核对，本版同步 R3@K1K3 消费及 attempt 2 号段。
**本单是操作说明，不是证据。**每次正式尝试的结论只认接受/辅助角色代录进 `docs/unity-test-log.md`「`UT-P1-ENG-ACQ-001-D1`」的条目。

依据：提案 `docs/proposals/P1-ENG-ACQ-001-pointer-fast-layer-target-switch-acquisition.md` §3.10、§5「Play D1」列、决策记录
「Play D1 信封与 AC-17 样帧核对落实（2026-09-29；CLARIFY）」（AC-17/AC-18 修订 2）；账本 `docs/authorizations.md` 2026-09-29
「用户确认 AC-17 三张预览样帧并签发 Play D1 信封…」与「用户指示：Unity 不在本机运行，Play D1 在另一台 Mac 上执行」。

> **当前结论：K1K3 操作页停点已通过，attempt 2 仍须前置放行。**操作页的 `R3@K1K3` 已获 `PASS_WITH_NOTES`，最新通过候选按复核文件 §7 机读行运行时解析；§2 就绪和 §2.7 单宿主收据由用户在 Unity 主机重新生成并原样回传，再由 Acceptance 按 §3 / workflow §4.5 核对。放行前不开正式尝试；AC-18 仍 `NOT_RUN`。
> §0 保存 PlayD1准备 时的阻断调查，K1K3 当前复核结论以同名复核「R3@K1K3」及提案「R3@K1K3 通过轮消费与 attempt 2 归因」为准。

## 0. 可执行性与阻断项（本轮只读核实；零 Play、零 ID、零推理）

| 编号 | 事实（代码指针） | 本机干跑证据 | 影响 |
|---|---|---|---|
| B1 | `controller/language_bridge.py` 的 `BACKENDS = ("local-hf", "http", "replay")` 不含 `candidates`；`controller/language_loop.py::build_parser` 的 `run --backend` 取值来自这个闭集；`_build_adapter` 也没有构造 `CandidatesBackend` 的分支。提案 IR-17 已记为「CLI 未接线，列为 Play D1 准备项」 | `python -m controller.language_loop run … --backend candidates` 被 argparse 拒绝，报 `invalid choice: 'candidates' (choose from local-hf, http, replay)`，退出码 2 | §3.10 要求的后端无法从 CLI 启动 |
| B2 | `run` 要求 `--k-receipt`。`LanguageSession.__init__` 与 `_run_session` 要求收据的 `backend`/`model_form`/`model_identity` 与适配器身份逐项相等；`validate_measurement_sources` 对非 `replay` 后端要求 mac/5060 两份实测报告；生效场景的 `retained_frame_count` 必须等于收据的 `retained_frame_count`。仓库里唯一可用的收据是 `docs/evidence/P1-ENG-LOOP-001-k-receipt.json`（`http`/5060/`c2-adapter`，R = 128） | 只读查看了该收据的字段；本单 §2.6 的覆盖把 R 设为 1500，与收据 R = 128 必然 `CONFIG_MISMATCH` | 对非 VLM 后端，收据的宿主、时延与 R 如何绑定，合同尚未定义（handoff「待裁定」IR-17 原文即此） |
| B3 | `CandidatesBackend.identity = {"backend": "candidates", "model_form": "detector-tracks"}`；会话写结果时经 `language_bridge.result_payload → _validate_model_block` 校验，`backend`、`model_form` 都必须属于闭集 | 直接调用 `_validate_model_block({"backend": "candidates", "model_form": "detector-tracks"})`，抛出 `LanguageBridgeError: backend must be one of ('local-hf', 'http', 'replay')` | 即使补上 CLI 接线，第一次 `ask` 的结果写入也会失败。现有单测 `test_designate_while_tracking_candidates_backend_matches_vlm_contract` 只测 `predict_one` 加 `interpret`，没有走会话写结果这条路 |
| B4（非阻断） | 操作者 CLI（`ask`/`confirm`/…）没有「注入人工延迟」的参数（全仓 grep 无此功能） | — | §3.10 的可选项 {0, 4} s 只能靠人工计时等待来实现（§5）。这种读法是否满足可选项，由接受角色裁定 |
| B5（非阻断） | 「四类描述数字」（time-to-bind、time-to-center、偏轴/斜距分桶成功率、误锁）没有现成的离线计算脚本（全仓 grep `time_to_bind`/`time_to_center` 无结果） | — | 用人工从日志读数，还是另写零消耗分析脚本（需要代码范围授权），由接受角色裁定。§6 已列出每个数字的来源文件 |

**K1K3 修订（2026-09-29）**：B1–B3 已按提案「candidates 后端接线窄范围修复 CLARIFY」在 `K1K3` 候选修复——`run --backend candidates`
（省略 `--model-form` 即 `detector-tracks`，须配 `--tracker det-assoc-v1 --resident`）构造 `CandidatesBackend`；收据改为 Unity 主机本地单宿主
`mac` 预检（§2.7）；结果 schema 收 `candidates`/`detector-tracks` 且只能成对。B4/B5 按裁定不并入（§5 人工计时、§6 人工/离线读数）。
下段为修复前（PlayD1准备 派发时）的原文，保留不改。

**B1–B3 的处置不在本角色权限内**：修复需要改 `controller/`，签发的 Play D1 信封明确写「未授权代码改动」；而且改动后
工作树不再等于 R3 `passed_candidate`，§3 的 workflow §4.5 核对会失败。建议路径见交接行与 `needs_user`：由用户授权一个窄范围的代码批次，
接受角色先为 `candidates` 后端的收据与确认时效语义写 CLARIFY/AC 修订，实现后经复核得到新的 `passed_candidate`，再回到本单。
**不得绕行**：用 `replay`/`http`/`local-hf` 后端代替，候选就来自 VLM 或回放，违反 §3.10「候选来自快层检测 track」；
手工造收据、在 `docs/evidence/` 写启动脚本绕开 CLI，都等于未经复核的代码改动。

## 1. 分工、信封与停止条件

| 角色 | 在本单里做什么 |
|---|---|
| 用户（Unity 主机上） | 拉取仓库，按 §2 做就绪检查并回传输出；按 §3 回传核对输出；打开 Unity、Play、退出 Play；**亲自操作**（`ask`/`confirm`/选车/等待）；观察实时预览与同帧 Unity 画面；**只有用户能提起重试** |
| Acceptance（由 supervisor 派发） | **每次正式尝试前**按 §3 做 workflow §4.5 核对，并把核对结果、后端、保留帧配置写进该次 Unity 日志条目；任何一项不满足就不放行 |
| 接受/辅助 | 代录用户反馈进 `UT-P1-ENG-ACQ-001-D1`；正式 verdict 取用户指定的那次，未指定取最后一次；前次记录不覆盖、不合并 |
| 实现 | 远程访问 Unity 主机 = 0；不替用户做任何确认类决定；只处理用户回传文本中的问题 |

**信封（账本逐字条目为准，本表只作提示）**：Consuming = yes（Play 开始前由 Acceptance 改交接行）。每次正式尝试 ≤ 3 分钟；
**重试不限次数，但只能由用户提起**，任何角色不得自行重试或加开尝试。每次尝试各产生 1 个 session ID，各加载 YOLO 权重 1 次，
各归档约 1,500 帧 / 90 MB，`retained_frame_count` ≥ 1500。Play 期间 Unity 主机 MPS/CPU 在线检测不计次。
新 scenario/run ID = 0；API/VLM = 0；训练 GPU·h = 0；下载/pip = 0/0；5060 与其他远端访问 = 0。
执行信封子额度块（SUB）不启用。任何越界都回到用户。

**硬停止（出现任一项即停止本次尝试，如实记录，不在同一次里反复试到成功）**：需要改 `controller/`、`tools/`、`tests/`、
`config/`、`Assets/`、`ProjectSettings/`；需要下载或 pip；§2 资产的散列不符；会话以 `CONFIG_MISMATCH` 拒绝启动；
单次尝试到 3 分钟（到点即 `stop`，把本次记为「截止未完成」）。
`catchup_stale` **不是**硬停止（接受裁定 IR-23 是具名残余边界）：只记录次数与上下文；之后是否再试由用户决定。

## 2. Unity 主机就绪清单（每次开新一天或拉取新提交后做一次；输出原样回传）

下文 `<REPO>` 指 Unity 主机上的仓库根目录，`<PY>` 指该机跑跟踪器的 Python 解释器。本机路径（例如
`~/TetheredDroneTracking-full/.venv-yoloe`）**不假定该机也有**，两个占位由用户填写并确认。所有命令都在 `<REPO>` 下执行。

### 2.1 仓库与提交

```bash
cd <REPO>
git fetch origin && git checkout main && git pull --ff-only
git rev-parse HEAD
git log -1 --format='%h %s'
```

预期：拉取成功，无冲突。这台机器 HEAD 应处的提交由 Acceptance 在 §3 核对时对照复核文件机读行裁定；本单不手写提交号。

### 2.2 Python 环境（只查，不装）

```bash
<PY> --version
<PY> -c "import importlib.metadata as m
for p in ['ultralytics','torch','lap','numpy','Pillow','opencv-python','opencv-contrib-python']:
    try: print(p, m.version(p))
    except Exception: print(p, 'MISSING')"
<PY> -c "import torch, cv2; print('mps', torch.backends.mps.is_available()); print('cv2', cv2.__version__, 'TrackerNano', hasattr(cv2, 'TrackerNano'))"
<PY> -m controller.language_loop run --help | head -5
```

预期：`ultralytics` 与 `config/det-assoc-v1.models.json` 的 `ultralytics_version` 字段一致；`lap`、`torch`、`numpy`、`Pillow` 有版本号；
`opencv-python` 或 `opencv-contrib-python` 至少一个有版本号，且 `TrackerNano True`；`mps True`（为 False 时按规格回落 CPU，照记）；
`run --help` 能打印用法。本机参考环境是 ultralytics 8.4.104、torch 2.13.0、lap 0.5.13、opencv-python 5.0.0.93、numpy 2.5.1、Pillow 12.3.0、
Python 3.12（只作对照）。**任何一项 `MISSING` 都停下回报**：信封 pip = 0，装包需要用户另外授权。

### 2.3 资产（被 git 忽略，必须已经在这台机器上）

```bash
<PY> - <<'EOF'
import hashlib, json, pathlib
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
spec = json.load(open("config/det-assoc-v1.models.json"))
for label, entry in (("weights", spec["weights"]), ("freeze", spec["freeze"])):
    p = pathlib.Path(entry["path"])
    print(label, p, "exists" if p.is_file() else "MISSING",
          "sha_ok" if p.is_file() and sha(p) == entry["sha256"] else "SHA_MISMATCH_OR_MISSING")
nano = json.load(open("config/nanotrack-v2.models.json"))
for name, m in nano["models"].items():
    p = pathlib.Path("runtime/models/nanotrack-v2") / m["filename"]
    print("nanotrack", name, "exists" if p.is_file() else "MISSING",
          "sha_ok" if p.is_file() and sha(p) == m["sha256"] else "SHA_MISMATCH_OR_MISSING")
EOF
```

预期：四行都是 `exists sha_ok`。这里只算文件散列，不加载权重，不计入「YOLO 权重加载」。
YOLO 权重在 `outputs/eng-det/runs/run-1/weights/last.pt`，NanoTrack 两个 onnx 在 `runtime/models/nanotrack-v2/`，
都被 git 忽略，`git pull` 不会带过来。**缺失就停下回报**：从本机拷贝过去属于跨机传输，不在 Play D1 信封内；
从网上重新获取属于下载（= 0）。两者都需要用户另外授权。
Play 本身不读数据根；静止车 B/C 的离线复算（§3.10 `tools/dist_data/project_boxes.py`）在哪台机器做，另行裁定，不在本单范围。

### 2.4 Unity 工程与场景

先在 Unity 6000.4.1f1 中打开 `<REPO>`，载入场景
`Assets/SimplePoly City - Low Poly Assets/Demo/SimplePoly City - Low Poly Assets_Demo Scene.unity`，**不要按 Play**。
Unity 窗口不要全屏，终端要能和它并排看到。然后执行：

```bash
grep -n "runInBackground" ProjectSettings/ProjectSettings.asset
git status --porcelain --untracked-files=all -- Assets ProjectSettings Packages config
ls -d Assets/_Recovery 2>/dev/null || echo "no _Recovery"
```

预期：`runInBackground: 1`；第二条无输出；第三条输出 `no _Recovery`。顺序固定为「先打开 Unity 再检查」，
因为 Unity 异常退出后生成的 `Assets/_Recovery/` 要在打开之后才看得到。

### 2.5 槽位清空（只移动，不删除）

```bash
LABEL=pre-acq-d1-$(date +%Y%m%dT%H%M%S)
mkdir -p runtime/hold-$LABEL
for f in frames runs metrics.json tracking_observation.json body_command.json gimbal_command.json \
         language_request.json language_result.json tracker_state.json m3_body_truth.jsonl scenario_config.json; do
  [ -e runtime/$f ] && mv runtime/$f runtime/hold-$LABEL/
done
mkdir -p runtime/frames
ls -A runtime/frames | wc -l
```

预期：最后输出 `0`。`runtime/models/` 不动。如果某次 Play 之前 `runtime/hold-*` 已经存在，保留原样，不清理。

### 2.6 保留帧配置 `runtime/scenario_config.json`（只在 Unity 主机上生成）

覆盖机制（只读核实）：Unity 端 `Assets/TetheredTracking/Scripts/ScenarioConfig.cs::Load` 的逻辑是，`runtime/scenario_config.json`
存在就**整份**使用它，否则使用 `config/scenario.default.json`，不做逐字段合并。取值被 `Normalize` 限制在 4…10000。
Python 端 `controller/language_loop.py::effective_scenario_document` 采用同一规则。
因此覆盖文件必须是缺省配置的完整副本，只改一个字段。`scenario_id` 保持 `deterministic-loop-default`，所以不产生新的 scenario ID。
这份文件被 git 忽略（`.gitignore` 的 `/runtime/*`），不改 `config/`，也不改 Unity。

```bash
sed 's/"retained_frame_count": 128$/"retained_frame_count": 1500/' config/scenario.default.json > runtime/scenario_config.json
diff config/scenario.default.json runtime/scenario_config.json
shasum -a 256 config/scenario.default.json runtime/scenario_config.json
sed 's/"retained_frame_count": 128$/"retained_frame_count": 1500/' config/scenario.default.json | shasum -a 256
<PY> -c "from pathlib import Path; from controller.language_loop import read_scenario; print(read_scenario(Path('runtime')))"
```

预期：
- `diff` 恰好一处：第 25 行 `128` 改成 `1500`。
- 第四条命令算出的散列等于 `runtime/scenario_config.json` 的散列（可复现核对）。
- 最后一条打印 `{'scenario_id': 'deterministic-loop-default', 'capture_hz': 5.0, 'retained_frame_count': 1500}`。

本机已在会话暂存目录用同一条 `sed` 干跑（没写 `runtime/`）：`diff` 只有这一行，`read_scenario` 输出与上面一致。
散列值属于可派生标识，本单不手写，每次尝试把第三条命令的输出抄进 §6。
1500 帧在 5 Hz 下约 300 s，覆盖 ≤ 3 min 的尝试还有余量。
**必须在按 Play 之前就位**：Unity 在场景启动时读取一次配置。
会话启动时，`--body-scenario-config` 必须指向这份文件（§4）：`bind_body_runtime` 要求规划器场景与生效场景逐字相等。
Play D1 全部结束后，把它移进 `runtime/hold-<标签>/`（不删除），之后的会话才会回到缺省 R = 128。

### 2.7 `candidates` K 收据本地预检（K1K3 修订；§2.6 之后做；只在 Unity 主机上、由用户本人执行）

依据：提案「candidates 后端接线窄范围修复 CLARIFY」（AC-21、AC-18 修订 3）及「R1@K1K3 通过轮消费」。
预检只对适配器 `CandidatesBackend.predict_one` 用合成历史行（`none` 与 8 个 `tracked`）各做 ≥ 100 次无模型调用，帧名是合成的
`frame_<id>.jpg`，**不读图、不读取或回放序列、不启动 Unity/会话、不建任何 ID、不加载 YOLO 权重、不调检测器/VLM**，零消耗。
`hz` 与 `retained_frame_count` 取 `runtime/` 下实际生效的配置，所以**必须先完成 §2.6**。报告记录本机机器名；会话启动时与本机机器名
逐字比对，所以**报告与收据只能在这台 Unity 主机上生成，不得复制别处（包括开发机）的收据或只改 JSON 字段**。
§2.6 的 R/hz、拉取了新提交、或换了解释器，都要重新做一次本节并回传。

```bash
cd <REPO>
<PY> -c "import platform; print('machine:', platform.node())"
<PY> -m tools.eng_acq.candidates_preflight --runtime runtime --out-dir outputs/eng-acq/P1-ENG-ACQ-001/play-d1/k-receipt; echo "exit: $?"
shasum -a 256 outputs/eng-acq/P1-ENG-ACQ-001/play-d1/k-receipt/candidates-mac-report.json outputs/eng-acq/P1-ENG-ACQ-001/play-d1/k-receipt/candidates-k-receipt.json
<PY> -c "import json; d=json.load(open('outputs/eng-acq/P1-ENG-ACQ-001/play-d1/k-receipt/candidates-k-receipt.json')); print({k: d[k] for k in ('host','backend','model_form','hz','retained_frame_count','p95_s','k_ret','k_conf','k_pub','qualifies')})"
<PY> -c "import json; print('report git_head:', json.load(open('outputs/eng-acq/P1-ENG-ACQ-001/play-d1/k-receipt/candidates-mac-report.json'))['environment']['git_head'])"
```

预期：
- `exit: 0`；打印的摘要里 `machine_name` 与第一行 `machine:` 相同，`hz` 为 `5.0`，`retained_frame_count` 为 `1500`，`verdict` 为 `OK`，
  `qualifies` 为 `true`，`group_p95_s` 有 `none`、`tracked` 两组。
- 收据字段：`host=mac`、`backend=candidates`、`model_form=detector-tracks`、`retained_frame_count=1500`。
- `report git_head:` 应与 §2.1 / §3 回传的 `git rev-parse HEAD` 相同；Acceptance 在放行前逐字核对，不复用旧报告。
- 目录里已有旧报告/收据时，工具先把它们改名为 `*.superseded-<时间戳>`（不删除）再写新的。
- `exit: 6`（报告 `FAIL`、未写收据）或任何报错：**硬停止**，把整段输出原样回传，不重试、不手改文件。

`p95_s` 只是适配器转换耗时，**不是**在线检测或整个 Play 的时延，也不是成功保证。散列值属于可派生标识，不手写进本单；每次尝试把
第三条命令的输出抄进 §6；连同新增的 `report git_head:` 输出原样回传。收据路径在 §4 的 T1 行里用到。

## 3. 每次正式尝试前的 workflow §4.5 核对（插入点：§2 完成、Unity 已打开未 Play、会话进程未启动）

用户在 Unity 主机上运行下面的命令，把**整段输出**原样贴回对话：

```bash
cd <REPO>
echo "== attempt: <n>  host: $(hostname -s)  at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "== HEAD";            git rev-parse HEAD
echo "== status";          git status --porcelain
echo "== status-untracked"; git status --porcelain --untracked-files=all -- Assets ProjectSettings Packages config controller tools
echo "== scenario";        shasum -a 256 runtime/scenario_config.json; grep -n '"retained_frame_count"' runtime/scenario_config.json
echo "== frames-empty";    ls -A runtime/frames | wc -l
echo "== runInBackground"; grep -n "runInBackground" ProjectSettings/ProjectSettings.asset
echo "== recovery";        ls -d Assets/_Recovery 2>/dev/null || echo "no _Recovery"
```

Acceptance 裁定这段输出时，通过候选**运行时解析**（`grep -E '^passed_candidate:' docs/reviews/P1-ENG-ACQ-001.md | tail -1`），
不手抄。要满足的条件：实现代码与通过候选一致，只允许白名单文档差异；`status` 在代码路径上为空；
`retained_frame_count` 为 1500；`frames-empty` 为 `0`；`runInBackground: 1`；没有 `_Recovery`。
Acceptance 把核对结果、后端（`candidates`）与保留帧配置写进该次 `UT-P1-ENG-ACQ-001-D1` 条目，并写明放行或不放行，之后用户才能进入 §4。
（K1K3 修订：操作页修复候选已经 `R3@K1K3` 通过；旧 `R1@K1K3` 与 `R3@K1K2K3` 的机读行只证明旧代码，不能用来放行。
§2.7 的收据须由本机在当前 HEAD 下生成；其报告 `environment.git_head` 要与本节 HEAD 逐字相等，`retained_frame_count` 与本节 `scenario` 输出一致。不同即不放行，重新在当前 HEAD 运行 §2.7 并回传。）

## 4. 启动顺序与命令（Unity 主机）

**本地操作页（可选；提案「Play D1 本地操作页窄范围代码批次 CLARIFY」AC-22…24）。**页面文件 `docs/evidence/P1-ENG-ACQ-001-operator-web.py`（旧 LOOP-001 页面不用于本项），只监听 127.0.0.1，只读 `runtime/` 桥文件与本会话目录；每个按钮只调用一次下表 T3 同一条 `controller.language_loop` CLI（同一 `$PY`、本仓库为工作目录），不写桥文件、请求或锁，不自动确认、不自动重发、不自动 stop。
**放行前不可用**：本批操作页 K1K3 候选已经 `C3@K1K3` 核对、`R3@K1K3` 独立复核通过；attempt 2 仍须按 §2.7/§3 重新预检并由 Acceptance 放行；页面**不替代 §3 放行**，不生成 verdict，不替代会话 JSONL 或 Unity 日志。

用法：T1 已启动（T1 输出出现会话启动）之后、按 Unity Play 之前，在 T4 执行 `$PY docs/evidence/P1-ENG-ACQ-001-operator-web.py --sid $SID --open`（缺省端口 8772；收据缺省读 §2.7 生成的 `outputs/eng-acq/P1-ENG-ACQ-001/play-d1/k-receipt/candidates-k-receipt.json`，runtime 缺省 `runtime/`，会话目录 `outputs/eng-acq/P1-ENG-ACQ-001/play-d1/sessions/$SID`；`--help` 列出全部参数）。

- **同号**：`acq-d1-1` 以及任何已用号（会话目录已有结束记录或重复启动、目录在但没有这个号的活会话、已有 `outputs/eng-acq/P1-ENG-ACQ-001/play-d1/$SID/unity-runtime` 归档）页面拒绝启动并报「同号不可复用」，不清理、不覆写旧目录；运行中出现第二个 `session_started`、同号归档或结束后又有活动，全部按钮（含「标记 Play 开始」与「用同一 request_id 重试」）立即停用，停止与计时改用 T3 `stop` 与 T2 手工计时。换新号须回到 §3 重新放行。
- **收据**：页面显示收据绑定结果（host/backend/model_form/hz/R/k_ret/k_conf/T_ret/T_conf 与报告 `git_head`），与本次 `session_started`、§2.7 报告或生效 R/hz 任一不符即停用确认并写明原因；时效数值只取自该收据。
- **确认**：只有预览图显示并解码成功、三门时效（查询起 T_ret+T_conf、结果出现起 T_conf、帧差 ≤ k_ret+k_conf，取先到者）未到时，「确认候选 i」才可点；按钮编号 = 预览框上的 index。页面倒计时只是提示，会话检查为准；过期不自动重发。`APPLIED` 只表示受理，是否绑定看页面「最近指定」结果与状态。
- **状态**：`ACQUIRING`（`TRACK_ENDED` 后的自动转向重捕）只有「停止会话」；其成败（`TRACKING` 或 `LOST(acquire_failed)`）只显示，不代人再次指定。
- **Play 计时**：用户在按下 Unity Play 的同时点「标记 Play 开始」（只能标记一次，写入操作日志；刷新或重启页面不重置）。页面显示已过/剩余 180 s，到 3 min 只提示，**不会自动 stop**，仍由用户点「停止会话」或用 T3 `stop`。页面启动或会话启动时刻都不算 Play 开始；页面提示无法可靠读取起点或计时标记已停用（同号不可复用、读不到会话状态）时，按 T2 的 `date` 手工计时。
- **日志**：`outputs/eng-acq/P1-ENG-ACQ-001/play-d1/$SID/operator/operator-web.jsonl` 逐条记录点击、拒绝、结果未知、同 request_id 重试、计时标记/到点提示与 CLI 回执；§7 归档时保留该目录；页面不改会话 JSONL。
- **CLI 回退**：页面故障、卡住、按钮停用或数据过期时，直接用下表 T3 命令，剧本照常进行（页面不持有写者锁，CLI 随时可用）。页面上显示「结果未知」的请求，先看 T2 状态再决定是否在页面用同一 request_id 重试，不要在终端另发同一动作；页面只在状态、画面令牌与动作闭集仍与原请求一致（确认还须未过时效、预览未换）时放行重试，否则重试按钮停用并写明原因，此时按新画面操作或用 T3。

会话号：每次尝试一个新号 `acq-d1-<n>`，`<n>` 为本次正式尝试序号；attempt 1 的 `acq-d1-1` 已用，登记外运行也复用了该号且已作废。用户已提起的 attempt 2 **只能用 `acq-d1-2`**；同号不复用，中止的尝试也占号。下文 `<SID>` 即该号。若发现 `acq-d1-2` 已有会话目录、启动记录或归档，先停下回报，不另选号自行继续。
每个终端先执行：

```bash
cd <REPO>; export SID=acq-d1-<n>; export PY=<PY>
```

**顺序**：§2 → §3 放行 → T1 起会话 →（可选）T4 起操作页 → 用户在 Unity 按 Play（同时在页面标记 Play 开始）→ T2 监视 → T3 或 T4 操作。
**结束**：T3 或 T4 `stop` → 用户退出 Play → T1 进程退出 → T2、T4 Ctrl-C → §7 归档。

| 终端 | 命令 | 说明 |
|---|---|---|
| T1 会话 | ⛔ **attempt 2 按 §2.7/§3 重新预检并获 Acceptance 放行前不可执行**（K1K3 操作页候选已获 `R3@K1K3` 通过；后端与收据按已复核 CLI 填入）：<br>`$PY -m controller.language_loop run --session-id $SID --session-root outputs/eng-acq/P1-ENG-ACQ-001/play-d1/sessions --runtime runtime --allow-shared-runtime --k-receipt outputs/eng-acq/P1-ENG-ACQ-001/play-d1/k-receipt/candidates-k-receipt.json --backend candidates --tracker det-assoc-v1 --resident --condition follow --ground-plane-y-m 0.2 --planned-duration-s 180 --body-scenario-config runtime/scenario_config.json 2>&1 \| tee outputs/eng-acq/P1-ENG-ACQ-001/play-d1/$SID.session-process.log` | 省略 `--model-form` 即取 `detector-tracks`；显式写其他形态、缺 `--resident` 或换跟踪器都会在启动前 `CONFIG_MISMATCH`。收据与本机机器名、生效 R/hz 不符同样在启动前 `CONFIG_MISMATCH`（硬停止，回 §2.7 重做预检）。`--resident` 必须和 `--tracker det-assoc-v1` 一起用。`--allow-shared-runtime`：`--runtime runtime` 解析到共享槽，缺这个开关时 CLI 退出码 2 拒绝。YOLO 权重在常驻载体建立时加载 1 次，只在 Unity 开始出帧后发生 |
| T2 监视 | `while true; do clear; date; $PY -m controller.language_loop status --runtime runtime \| head -60; sleep 1; done` | 只读，不写 `runtime/`。看 `tracker_state.state`、`last_result.status`、`last_result.result_id`、`last_result.preview_path`、候选个数 |
| T3 操作 | `$PY -m controller.language_loop ask --session-id $SID --runtime runtime --allow-shared-runtime "the car"` | 指令必须属于闭集文法（`the <class>` / `the <color> <class>` / 左右关系）。`the car`、`the red car` 已干跑解析通过，`the vehicle` 会被拒。`candidates` 后端忽略指令内容，候选取查询帧上全部 `tracked` 轨迹（按面积排序，最多 8 个） |
| T3 | `open "<last_result.preview_path>"` | 在 macOS 上打开候选预览，图中每个框标有 index |
| T3 | `$PY -m controller.language_loop confirm --session-id $SID --runtime runtime --allow-shared-runtime --token <last_result.result_id> <index>` | `--token` 是当次候选结果的 `result_id`，`index` 是预览上的整数编号。回执 `APPLIED` 只表示受理；是否绑定，看 `designation` 事件与状态变化 |
| T3 | `$PY -m controller.language_loop reject --session-id $SID --runtime runtime --allow-shared-runtime --token <result_id>` | 驳回当前候选 |
| T3 | `$PY -m controller.language_loop release --session-id $SID --runtime runtime --allow-shared-runtime --token <track_id>` | 释放当前指针（剧本不必需） |
| T3 | `$PY -m controller.language_loop stop --session-id $SID --runtime runtime --allow-shared-runtime` | 结束会话 |
| T4 操作页（可选） | `$PY docs/evidence/P1-ENG-ACQ-001-operator-web.py --sid $SID --open` | 见上「本地操作页」；T1 启动后、按 Play 前启动；T1 退出后 Ctrl-C 结束。页面故障时回退到 T3，不影响会话 |

退出码：`4` = `WRITER_BUSY`，另一个 CLI 正持有写者锁，稍后再发；`5` = 没有回执，先看 T2 再决定；
`2` = 被拒，包括指令超出文法、共享槽缺开关。

## 5. §3.10 剧本（每次尝试完整执行；≤ 3 min）

每一步记下墙钟时刻（T2 的 `date` 行），表格见 §6。候选只来自快层检测轨迹，**不得用真值投影**。

1. **S0**：T1 已启动 → 用户按 Play，记下 Play 开始时刻 → 会话目录 `language-session.jsonl` 出现 `resident_loop_started` 事件后开始（T1 输出同样可见）。
2. **S1 选红车**：T3 `ask "the car"` → 打开预览 → 找到框住红车的 index → `confirm`。记录 ask、预览出现、confirm 三个时刻，以及结果（六值之一）。
   **同时对照 Unity 画面**，记下预览所框对象的颜色和身份是否与同一时刻 Unity 画面一致（如实填写，不预设「一致」）。
3. **S2 跟红车 ≥ 20 s**：不操作；记下 `TRACKING` 持续时长，以及有无 `catchup_stale`、`REINIT_REQUIRED`。
4. **S3 → 静止车 B**：`ask` → 在预览中选一辆静止车记为 B（写下颜色和车型）→ `confirm`。记录结果，以及到绑定、到居中的时刻。
5. **S4 → 静止车 C**：同上，选另一辆静止车记为 C。
6. **S5 切回红车**：`ask` → 红车在候选中就选它、`confirm`。多半会出现 `TRACK_ENDED` → `ACQUIRING`（转向通道）→ 收养或 `LOST(acquire_failed)`。
   红车不在候选中（结果为 `none` 或候选中没有它）时，如实记「红车不在候选」，**不要用其他方式指定**。
7. **S6 结束**：T3 `stop` → 退出 Play。

**人工延迟 {0, 4} s（可选，B4）**：工具里没有注入参数。采用延迟 4 s 时，用户在预览出现后按 T2 的 `date` 数满 4 s 再发 `confirm`；
每次指定都记下所用延迟（0 或 4）。「人工计时」能否作为 §3.10 的可选项，由接受角色裁定；裁定之前一律用 0。
**确认时效**：由修复后的收据合同确定（B2），本单暂不写数值；超时被拒（`stale_rejected`）就如实记录，不补发。

## 6. 每次尝试记录模板（留空；用户与代录角色填写，不预填结论）

```text
尝试 n = ___   会话号 = acq-d1-___   发起 = 首次 / 用户提起的重试（用户原话：________）
§3 核对：Unity 日志条目指针 ________   放行人 ________   scenario_config sha256（§2.6 第三条输出）________
Play 开始（墙钟）______  Play 结束 ______  会话进程退出码 ______  是否 3 min 截止 ______

| 步 | 目标 | 延迟 s | ask 时刻 | 预览出现 | confirm 时刻 | 六值 / ACQUIRE_FAILED / none | 到绑定 | 到居中 | 实时预览与同帧 Unity 画面一致？（对象/颜色/身份，用户观察原话） |
|----|------|-------|---------|---------|-------------|-------------------------------|-------|-------|----------------------------------------------------------|
| S1 | 红车 |       |         |         |             |                               |       |       |                                                          |
| S3 | B：  |       |         |         |             |                               |       |       |                                                          |
| S4 | C：  |       |         |         |             |                               |       |       |                                                          |
| S5 | 红车 |       |         |         |             |                               |       |       |                                                          |

六值 + ACQUIRE_FAILED 分布（BOUND / BOUND_COASTING / TRACK_ENDED / NO_TRACK_AT_K / AMBIGUOUS / FRAME_NOT_IN_HISTORY / ACQUIRE_FAILED）：____
显式报告比例（上述七类占指定次数）：____
catchup_stale 次数 ____；每次上下文（时刻、状态、帧号、前后动作）：____
误锁（次数 / 时长）：____
偏轴角桶（画内 / 出画但在 45° 内 / 需机身）× 斜距桶的成败：____
用户对本次的判断（PASS / FAIL / BLOCKED，或「不作正式 verdict」）：____
用户是否指定本次为正式 verdict：____
```

四类描述数字的来源（离线读取，不设门，B5）：
- **time-to-bind**：会话目录 `language-session.jsonl` 中 `confirm` 回执到 `designation` 事件（`BOUND`/`BOUND_COASTING`）的时差；走转向通道时到收养事件为止。
- **time-to-center**：`runtime/runs/<SID>-resident<k>/` 的逐帧记录里，指针框中心到画面中心 < 64 px 连续 5 帧的首帧时刻，减去 confirm 时刻。
- **分桶成功率**：每次指定的结果按偏轴角与斜距分桶。偏轴角由该帧 sidecar 位姿与指针框计算；静止车 B/C 的成败用归档帧离线复算，或人工目检。`metrics.json` 只对红车有效。
- **误锁次数与时长**：离线目检归档帧，或对照复算框。

## 7. 每次尝试之后：归档与大小核对（只移动，不删除）

```bash
A=outputs/eng-acq/P1-ENG-ACQ-001/play-d1/$SID
mkdir -p $A/unity-runtime
for f in frames runs metrics.json tracking_observation.json body_command.json gimbal_command.json \
         language_request.json language_result.json tracker_state.json m3_body_truth.jsonl; do
  [ -e runtime/$f ] && mv runtime/$f $A/unity-runtime/
done
mkdir -p runtime/frames
ls $A/unity-runtime/frames | grep -c '\.jpg$'
du -sh $A/unity-runtime/frames outputs/eng-acq/P1-ENG-ACQ-001/play-d1/sessions/$SID
ls outputs/eng-acq/P1-ENG-ACQ-001/play-d1/sessions/$SID
```

预期：JPEG 数 ≤ 1500（约等于 Play 秒数 × 5）；`unity-runtime/frames` 约 ≤ 90 MB。会话目录里还有一份帧环副本，容量同为 R，同样按实测记录。
超出「约 1,500 帧 / 90 MB」较多时停下回报，不再开下一次。
`runtime/scenario_config.json` 在尝试之间保留；全部尝试结束后按 §2.6 末段移走。
归档目录被 git 忽略，不入库；代录角色只在 Unity 日志中引用路径与计数。
用户把 §6 模板、上面三条计数输出、T1 日志末尾 20 行贴回对话，由接受/辅助角色代录。
