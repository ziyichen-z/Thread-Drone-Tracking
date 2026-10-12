# P1-ENG-LOOP-002 — `K1K3` 身份修复稳定候选（Implementation；登记轮次 `身份修复K1K3`）

- 派发：Dispatch-Id `P1-ENG-LOOP-002-身份修复K1K3-20261007T210446Z-6f01`（`requested.round` = `身份修复K1K3`；Opus 子代理，单写者，supervisor 派发）。
- 机器：MacBook Air（Unity 主机）；focused 用系统 `python3`；操作块探针里的 `$PY` = 仓库 `.venv-yoloe/bin/python`（只读，不装包）；shell = Air `/bin/bash` 3.2.57。
- 合同：同名提案「R4消费与诊断故障裁定（2026-10-07，Acceptance）」§2–5：DIAG-VERSION-1（AC-7 修订 5、AC-16 修订 1）与 OPS-SOURCE-1（AC-10 修订 2）；新停点 `K1K3`（K1 字段来源/一致性链，K3 VLM 身份拒启），不是旧冻结集的 R5。
- 执行信封：零消耗。SSH、复制、板、Jetson、Unity/Play、5060、模型加载、下载、pip、runtime、全套测试本轮都是 0；N-1 全套 3/3 已用尽，本轮**没有跑全套**（engineering §6 窄修路径，见 §6）。**修复未在真实板条件下验证。**

## 0. 派生标识与完整候选 diff 解析式（运行时解析，不手抄）

```bash
PASSED=$(grep -oE '^passed_candidate: [0-9a-f]{40}' docs/reviews/P1-ENG-LOOP-002.md | tail -n 1 | awk '{print $2}')   # R4 终局通过候选 = 全量基线
DISPATCH=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 身份修复K1K3 supervisor 派发登记')   # 本轮派发 base（= 修前）
FIX=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 身份修复K1K3 修复候选')                  # 代码/测试/操作单提交
CAND=$(git log main --format=%H --grep='^P1-ENG-LOOP-002 身份修复K1K3 收工')                      # 本停点稳定候选（交 C5@K1K3）
git diff "$PASSED".."$CAND"                       # 完整候选 diff（相对最新 passed_candidate）
git diff --name-only "$PASSED".."$CAND"           # 路径闭集（含 R4 之后其他角色的 docs 提交，见 §5）
git diff "$PASSED".."$CAND" -- controller Assets tools tests config ProjectSettings Packages/packages-lock.json docs/evidence/P1-ENG-LOOP-002-play-ops.md   # PLAY_GOVERNING：非空（tools/tests/操作单）→ R1@K1K3 有开轮资格
git diff "$DISPATCH".."$FIX"                      # 本轮全部实现改动（5 个具名文件）
git diff --stat "$FIX".."$CAND"                   # 其后只有本证据与状态板
```

## 1. 状态与结论

- **本提交是新停点 `K1K3` 的身份修复稳定候选**，交接受 `C5@K1K3` 只读核对，核对后交新鲜独立 `R1@K1K3`。只记 `IMPLEMENTED`（未复核），不记 `DONE`；Gate board Overall/Lifecycle 不由本角色改（仍 `REWORK_REQUIRED`/`ACTIVE`）。
- 改动闭集恰为裁定 §5 的五个具名文件（cmd: `git diff --name-only "$DISPATCH".."$FIX"`）：`tools/language_serve.py`（只版本解析/拒启）、`tests/test_llama_server_adapter.py`、`docs/evidence/P1-ENG-LOOP-002-play-ops.md`、`docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md`、`docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`；另加本证据与状态板。没动 GGUF 加载器、`llama_adapter` 推理/prompt/schema/decode、controller、模型身份字段表、冻结件、指标、采样、K 值/时间、安全或守账、JET 源文件、部署闭集清单与第三方依赖。
- `tools/language_serve.py` 在部署闭集内，故板端 `serve_code_sha256` 随之改变；该值一律运行时由 `deploy_digest` 自算（操作单第 3.5 步与 `/status`），没有手写期望值需要同步。

## 2. 稳定候选四条件自证（workflow §4.3.1；按 AC-n 附指针）

1. **实现范围与接口已冻结：成立。** 只改上述五个具名文件。接口：新增纯函数 `tools/language_serve.py::parse_runtime_build(output) -> str`（失败抛 `StartRefused`）；`read_runtime_build` 签名、`VERSION_PATTERN`（旧整数式原样）、`EXPECT_ASSET_KEYS`、`llama_preflight` 比较链与六键 `model_identity` 均不变。操作单新增「来源加载块」（`SRC_NAMES`/`src_check`/`src_resolve`/`src_load`）只替换原加载命令，来源选择与附录 A 不变。实现读法见 §8（交 C5 确认，非阻断）。
2. **相称测试/验证通过：成立（窄修路径，没跑全套）。** (a) focused：`python3 -m unittest tests.test_llama_server_adapter tests.test_loop2_isolation tests.test_loop2_freeze tests.test_language_latency tests.test_language_selector tests.test_eng_acq_guards` → `Ran 170 tests … OK (skipped=1)`（跳过 1 = `ReplayDemoTests.test_demo_covers_every_path`，本解释器无 Pillow，基线同样跳过）；修前同一六模块（修前测试文件）`Ran 163 … OK (skipped=2)`。(b) 修前红/修后绿见 §3.1。(c) 操作块探针见 §3.2–3.3。
3. **已知 Unity 失败：不适用。** 本轮零 Unity、零 Play。
4. **复核范围、状态板、候选提交与未验证风险已更新：成立。** §7 复核范围，§9 未验证项；状态板交接行（Owner Acceptance，Progress 含 `身份修复K1K3`）、`$FIX` 与 `$CAND` 已推送 `origin/main`。

## 3. 修前红 / 修后绿与离线探针

### 3.1 生产 preflight（DIAG-VERSION-1；test:）

夹具 `SEMVER_VERSION_BYTES` = 诊断 `board/check.txt` 原样两行（裁定 §2 引文逐字）`version: 0.5.0-dev (build 0, commit unknown)` + `built with GNU 13.3.0 for Linux aarch64`；假 `llama-bin` 输出字节与夹具逐字节相等由 `test_fake_binary_emits_the_verbatim_fixture_bytes` 断言。

| 具名测试（`tests/test_llama_server_adapter.py`） | 修前（`$DISPATCH` 的 `language_serve.py` + 本候选测试文件，一次性 worktree） | 修后 |
|---|---|---|
| `SemverVersionPreflightTests.test_semver_bytes_with_b0_assets_serve_identity_runtime_build_b0`（`main`→`llama_preflight`→`/status` 身份 `runtime_build=b0`） | FAIL：`language_serve exited early (3): refused to start: … --version output has no '^version: <n> ' line`（即诊断原故障） | OK |
| `SemverVersionPreflightTests.test_semver_bytes_with_mismatched_expected_build_refuse_before_loading`（期望 `b11381`/`b00` → 退出码 3、`runtime_build mismatch: computed 'b0'`、未起 llama-server） | FAIL ×2（拒启原因是版本行不可解析，不是错配） | OK |
| `SemverVersionPreflightTests.test_fake_binary_emits_the_verbatim_fixture_bytes` | ERROR：`StartRefused … no '^version: <n> ' line` | OK |
| `SemverVersionParseTests.*`（2 例，19 个子用例：两种格式取值；缺行/空/缺 build/build 非整数/缺 commit/行尾多余/非语义版本/无空格/旧格式超域/语义版本超域/非 ASCII 数字/重复相同/格式冲突/build 冲突一律拒） | ERROR ×19（修前无 `parse_runtime_build`） | OK |
| `SemverVersionPreflightTests.test_semver_refusal_branches_on_the_production_path`（缺 build、缺行、重复、冲突、超域、非 0 退出；生产路径退出码 3、未起子进程、端口未开） | OK（修前也拒，作回归） | OK |
| `SemverVersionPreflightTests.test_timeout_or_oserror_refuse` | OK（回归） | OK |
| 旧格式回归：`StartupRefusalTests.*`（5 例，含 `test_version_build_is_parsed_from_multiline_output` 取 `b11381`、`test_unparseable_or_failing_version_refuses`、`test_all_assets_match_serves_status_with_digest_machine_and_six_key_identity`） | OK | OK |

cmd（修前）：`git worktree add --detach <临时目录> "$DISPATCH"`，把本候选测试文件复制进去，`python3 -m unittest tests.test_llama_server_adapter.SemverVersionParseTests tests.test_llama_server_adapter.SemverVersionPreflightTests tests.test_llama_server_adapter.StartupRefusalTests` → `Ran 12 … FAILED (failures=3, errors=20)`；修后同命令 → `Ran 12 … OK`。临时 worktree 已删除。

### 3.2 来源加载（OPS-SOURCE-1；Air `/bin/bash` 3.2 一次性副本；cmd:）

探针脚本逐字见附录 X（会话临时目录运行，sha256 `7e5fde48f01b8d555c219046e72e1ae2cebc157d09d435c0483ceeee43ba5ac7`；`python3 ops_probe.py <仓库根> "$DISPATCH" <临时目录>`）。它从**候选工作树**逐字抽出操作单第 0.3 节「来源加载块」，从 `$DISPATCH` 逐字取修前命令 `set -a; . <(grep -v '^RESOLVE_OK$' "$OUT/prep/source.env"); set +a`（同时断言它在修前操作单与 mini 附录 B 中逐字存在、候选操作单不再含进程替换）；附录 A 由打印同格式（`shlex.quote`）九行 + `RESOLVE_OK` 的替身代替（Air 尚未对齐 JET 来源原件，真实附录 A 本轮未执行）。每例在 `/bin/bash --noprofile --norc` + `set -o pipefail` 下运行，末尾打印是否到达下一动作及五个变量。

| 例 | 修前块 | 候选块 |
|---|---|---|
| 合法来源 | **到达下一动作**，`load_rc=0`，九个变量**全部未设**（bash 3.2 下 `. <(…)` 静默不读入；复现故障） | `SOURCE_RESOLVE_OK`→`SOURCE_VARS_PRE_OK`→`SOURCE_VARS_POST_OK`→`SOURCE_LOAD_OK`，`source_rc=0`，值与替身逐字一致（含带空格路径） |
| 预置陈旧导出 `WEIGHTS=/stale/w.gguf` | 到达下一动作，`WEIGHTS` 仍为陈旧值 | 先 `unset` 后加载，`WEIGHTS` 为来源值，`SOURCE_LOAD_OK` |
| 解析失败（替身打印 `STOP Q4_CHAIN_MISMATCH`、退出 3） | 打印 STOP 后**仍到达下一动作**（无退出码检查） | `STOP S-PRECHECK source_resolve rc=3 …`，`source_rc=97`，未到下一动作 |
| 生成失败（`source.vars` 位置被目录占用，重定向失败） | —（修前无该步） | `STOP S-PRECHECK source_filter rc=1`，`source_rc=97` |
| 加载失败（`EXP_LLAMA_BIN_BYTES` 为只读变量，`.` 退出 1） | — | `STOP S-PRECHECK source_load rc=1`，`source_rc=97` |
| 非 `shlex.quote` 形式行（`WEIGHTS=$(echo injected)`） | — | 加载前 `source_vars_bad_line 'WEIGHTS'` → `STOP S-PRECHECK source_vars_invalid`，未执行该行（无 `injected` 输出），`source_rc=97` |

### 3.3 两条 gen（AC-7 修订 5 / AC-16 修订 1；cmd:）

同一探针从修前（`$DISPATCH`）与候选逐字抽出 mini 附录 B（`assets-gen.py`）与诊断页附录 1（`diag-assets.py gen`），对 8 种版本原流（`semver_verbatim`、`legacy`、`missing_build`、`missing_line`、`duplicate`、`conflicting`、`out_of_domain`、`nonzero_rc`；sha 行与期望一致）各跑一次；候选侧先经候选加载块加载来源变量再跑 gen（与操作单第 3 节第 4 步同序），修前侧把变量直接注入环境（只核修前 gen 自身的解析）。每例另以 `tools.language_serve.parse_runtime_build` 求同一原流的结果作对照。

| 原流 | `parse_runtime_build` | 修前两条 gen | 候选两条 gen |
|---|---|---|---|
| `semver_verbatim`（原样两行） | `b0` | rc 3，`STOP S-IDENTITY version_unparsed_or_nonzero` / `DIAG_FAULT …`（复现） | rc 0，`ASSETS_OK` / `DIAG_ASSETS_OK`，`runtime_build=b0` |
| `legacy` `version: 11381 (deadbeef)` | `b11381` | rc 0，`b11381` | rc 0，`b11381` |
| `conflicting`（旧整数行 + 语义版本行） | 拒 | rc 0，**`b11381`**（取首行，与生产不一致） | rc 3，STOP/FAULT |
| 其余 5 种 | 拒 | rc 3 | rc 3，`STOP S-IDENTITY version_unparsed_duplicate_or_nonzero` / `DIAG_FAULT version_unparsed_duplicate_or_nonzero` |

16/16 例候选 gen 与 `parse_runtime_build` 结论一致（取值相同或同为拒绝）。不启动真实二进制/模型，不读真实板原流。

## 4. AC-n 证据指针（本候选；没改的 AC 结论随 R4 通过候选携带）

| AC | 结论 | 证据指针 |
|---|---|---|
| AC-7（修订 5；解释 A2(a)(d)、AC-6/7） | 自证满足：两种格式各取明确 build；缺行/重复冲突/缺 build/非法域/非 0/超时/OSError 拒启；三 sha 与 `runtime_build` 逐键不等仍在加载前拒启 | test: `tests/test_llama_server_adapter.py::SemverVersionPreflightTests`（5 例）、`::SemverVersionParseTests`（2 例）、`::StartupRefusalTests`（5 例旧格式回归）；artifact: `tools/language_serve.py::parse_runtime_build`；cmd: §3.1 修前红/修后绿 |
| AC-16（修订 1；资产原流与 `runtime_build` 来源） | 代码/文本自证满足；**板端 `NOT_RUN`** | artifact: mini 附录 B、诊断页附录 1 两条 gen（同一语义；原样版本行另记 `runtime_version_line`，不进 `model_identity`）；cmd: §3.3 |
| AC-10（修订 2；来源前置的操作员路径） | 自证满足（Air bash 3.2 离线），待 C5/R1 定点复看 | artifact: 操作单第 0.3 节来源加载块、第 2 节、第 3 节第 4 步、mini 附录 B 抬头；cmd: §3.2 |
| AC-1…6、8、9、11…13、15（代码）、17 | 携带（R4 终局 PASS 范围；对应文件除 `tools/language_serve.py` 版本解析外零 diff） | cmd: `git diff --stat "$PASSED".."$CAND" -- controller config Assets` 为空；test: `tests.test_loop2_freeze`、`tests.test_loop2_isolation` 在 §2(a) focused 内 OK |
| AC-14 / AC-18、AC-15 板端、AC-16 板端 | `NOT_RUN` | 阶段 B 运行未放行；不申请 `UNITY_NA` |

## 5. 改动文件闭集

- **本角色本轮**：`$FIX` 的五个具名文件；`$CAND` 的本文件与 `docs/current-status.md`（交接行、Gate board 本项实现列、Log 一条）。
- **`$PASSED`..`$DISPATCH` 之间其他角色的提交**（按真实 diff，本表不豁免）：复核（`docs/reviews/P1-ENG-LOOP-002.md` R4 节）、接受（提案「诊断冒烟授权落实」「R4消费与诊断故障裁定」、`docs/implementation-status.md`、`docs/phase1-single-drone-design.md`）、实现（`docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` 首版，轮次 `诊断操作步骤`，未经核对/复核）、supervisor（`docs/evidence/supervisor-dispatch.jsonl`、`docs/authorizations.md` 代录）、状态板。

## 6. 验证用量与没跑的部分

- 停点全套：**没跑**（N-1 3/3 已用尽；改动不触及真实模型加载器、数据划分或对外指标路径，按 engineering §6 与裁定 §5 以覆盖改动文件的 focused + 修前红/修后绿 + 操作块探针代替；不记全套通过）。复核若判替代不足，须先回用户另签新增验证信封，不跑第 4 次。
- focused 与修前红输出写在会话临时目录，只回显摘要，不带 `-v`。
- consumed = none（零 ID/Play/API/GPU/下载/pip/SSH/板/复制/runtime/模型/回放）。

## 7. 复核范围（`C5@K1K3` 只读核对 → 新鲜 `R1@K1K3`）

- 全量基线 `$PASSED`（R4 通过指针派生）；真实全量 diff 见 §0，PLAY_GOVERNING 增量 = `tools/language_serve.py`、`tests/test_llama_server_adapter.py`、操作单。
- 原生产 preflight：`parse_runtime_build` ↔ `read_runtime_build` ↔ `llama_preflight` 比较链；`^b[0-9]{1,7}$` 与 `controller/language_bridge.py::_RUNTIME_BUILD` 同域。
- 两条 gen：mini 附录 B 与诊断页附录 1 的版本解析与 `parse_runtime_build` 同一语义（§3.3 对照）；停止方向（S-IDENTITY / DIAG_FAULT；来源变量缺失 S-PRECHECK）。
- 普通文件加载闭环：操作单第 0.3 节来源加载块在第 0.3 节、第 2 节、第 3 节第 4 步的调用与失败方向（停在 SSH/资产生成/服务之前）；裁定 §4 要求复核不得只签语法通过——§3.2 探针可原样重跑。
- `RED_LINE`：真值隔离与导入闭包（`tests.test_loop2_isolation`、`TruthIsolationTests` 在 focused 内 OK）。

## 8. 待裁定（实现读法 IR-K1…K6；推荐均为按本候选确认，交 C5 一并核对；不阻断交接）

| 编号 | 读法 | 依据 | 推荐 |
|---|---|---|---|
| IR-K1 | 「唯一有效版本身份行」= 行首 `version:` 的行恰一条；两条逐字相同也按「重复」拒启 | 修订 5「缺行/重复或冲突行…一律StartRefused」 | 确认 |
| IR-K2 | 语义版本形式 = `[0-9]+.[0-9]+.[0-9]+` 加可选 `-预发布`/`+构建元数据`（字符集 `[0-9A-Za-z.-]`），其后恰为 ` (build <ASCII 整数>, commit <无空白/括号/逗号的非空记号>)` 并到行尾；不容忍行尾空白或附加文本 | 修订 5「以原始行及明确build字段为界，不泛化」 | 确认（原样两行在界内） |
| IR-K3 | 构建号值域在解析时即核 1–7 位 ASCII 数字（两种格式同），超出即拒启，不等到身份校验；不去前导零（`build 007` → `b007`，原文不改写） | 修订 5「build域合法才可取值」；`^b[0-9]{1,7}$` | 确认 |
| IR-K4 | 正式操作单第 2 节原有的解析行（只 `tail` 目视、无退出码检查）同改为调用来源加载块（同一文件、同一 AC-10 修订 2 义务；裁定 §4 只点名第 0.3 节与第 3 节第 4 步） | 修订 2「来源解析…三步分别核退出状态」 | 确认 |
| IR-K5 | 第 3 节第 4 步把重新加载放到 `chan assets` **之前**（原文在其后、`assets-gen` 之前），使该 SSH 通道用到的路径变量也经本 shell 校验；加载失败时不发 `chan assets` | 裁定 §4「失败须STOP停在资产生成/SSH/服务之前」 | 确认 |
| IR-K6 | 两条 gen 生成的 JSON 增加审计键 `runtime_version_line`（原样版本行）；`--expect-assets` 只读 `EXPECT_ASSET_KEYS` 五键，该键不进 `model_identity`、不改 AC-6 值域；mini gen 另加来源变量缺失即 `STOP S-PRECHECK`（原来会以 Python `KeyError` 失败、无 `ASSETS_OK`） | AC-16 修订 1「完整原样version文本与退出码留资产原流及派生文档」「raw version为审计元数据」 | 确认 |

诊断页自身的加载（`. "$DIAG_D/prep/assets-src.env"`，已是普通文件）不在裁定 §4 点名处，本轮未改、未探针；诊断续试与否只按裁定 §6 `DIAG:RESUME:1` 由用户决定，本候选不发令诊断。

## 9. 未验证项与已知限制

- **修复未在真实板条件下验证**：没有对真实 `llama-server` 二进制执行 `--version`，原样版本行只来自用户诊断 `check.txt`（裁定 §2 引文）；板端 `/usr/bin/python3` 3.12.3 运行 `parse_runtime_build` 未验证（本机 focused 用 Python 3.14）。
- 真实附录 A 未执行（Air 尚未按 `FACT:2` A 对齐 JET 来源原件）；§3.2 用同格式替身。来源加载块只在 macOS `/bin/bash` 3.2 + BSD `wc`/`grep` 上探针过；它只在 Air 运行。
- 操作单其余节（第 1.0 节放行门、第 4 节启动块等）未改，结论随 R4 携带；其余未验证项照 `docs/evidence/P1-ENG-LOOP-002-stable-candidate.md` §9。
- 诊断页（`docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`）首版在 R4 通过候选之后加入、从未经核对/复核；本轮只改其附录 1 gen 与两处说明。

## 附录 X 操作块离线探针（逐字；会话临时目录运行，不入仓执行）

```python
"""P1-ENG-LOOP-002 身份修复K1K3 离线操作块探针（零模型/零 SSH/零板；/bin/bash 3.2 一次性副本）。

用法：python3 ops_probe.py <仓库根> <修前 git 引用> <一次性工作目录>
从候选工作树与修前引用逐字抽取：操作单第 0.3 节来源加载块、附录 B 与诊断附录 1 的 gen 块，以及修前
`. <(…)` 加载命令；附录 A 由打印同格式（shlex.quote）九行 + RESOLVE_OK 的替身代替（Air 未对齐来源原件）。
"""
import json, os, re, shlex, subprocess, sys
from pathlib import Path

REPO, OLD, WORK = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
PY = str(REPO / ".venv-yoloe" / "bin" / "python")
BASH = "/bin/bash"
OPS, MINI, DIAG = ("docs/evidence/P1-ENG-LOOP-002-play-ops.md", "docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md",
                   "docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md")
sys.path.insert(0, str(REPO))
from tools.language_serve import StartRefused, parse_runtime_build  # noqa: E402


def new_text(rel): return (REPO / rel).read_text(encoding="utf-8")
def old_text(rel): return subprocess.run(["git", "-C", str(REPO), "show", f"{OLD}:{rel}"], capture_output=True, text=True, check=True).stdout


def fenced_after(text, marker, lang):
    start = text.index(marker)
    m = re.compile(r"^```%s\n(.*?)^```" % lang, re.S | re.M).search(text, start)
    return m.group(1)


VALUES = {"WEIGHTS": "/home/jetson/eng-jet/q4 dir/c2-q4_k_m.gguf", "EXP_WEIGHTS_SHA": "a" * 64, "EXP_WEIGHTS_BYTES": "1000",
          "MMPROJ": "/home/jetson/eng-jet/mmproj-c2.gguf", "EXP_MMPROJ_SHA": "b" * 64, "EXP_MMPROJ_BYTES": "2000",
          "LLAMA_BIN": "/home/jetson/eng-jet/build/bin/llama-server", "EXP_LLAMA_BIN_SHA": "c" * 64, "EXP_LLAMA_BIN_BYTES": "3000"}
STUB_OK = "import shlex\nV = %r\nfor k, v in V.items():\n    print('%%s=%%s' %% (k, shlex.quote(v)))\nprint('RESOLVE_OK')\n" % VALUES
STUB_FAIL = "print('STOP Q4_CHAIN_MISMATCH'); raise SystemExit(3)\n"
ECHO = 'for n in WEIGHTS EXP_WEIGHTS_SHA MMPROJ LLAMA_BIN EXP_LLAMA_BIN_BYTES; do eval "printf \'%s=[%s]\\n\' $n \\"\\${$n-UNSET}\\""; done\n'


def run(case, script, stub=STUB_OK, pre=""):
    out = WORK / case
    (out / "prep").mkdir(parents=True, exist_ok=True)
    (out / "prep" / "resolve-src.py").write_text(stub, encoding="utf-8")
    body = f"set -o pipefail\nOUT={shlex.quote(str(out))}; PY={shlex.quote(PY)}\n{pre}{script}"
    (out / "run.sh").write_text(body, encoding="utf-8")
    r = subprocess.run([BASH, "--noprofile", "--norc", str(out / "run.sh")], capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout + r.stderr


results = {"bash": subprocess.run([BASH, "--version"], capture_output=True, text=True).stdout.splitlines()[0]}
LOADER = fenced_after(new_text(OPS), "来源加载块（逐字", "bash")
OLD_LOAD = "set -a; . <(grep -v '^RESOLVE_OK$' \"$OUT/prep/source.env\"); set +a"
assert OLD_LOAD in old_text(OPS) and OLD_LOAD in old_text(MINI), "old load command not found verbatim"
assert "<(" not in new_text(OPS).replace("`. <(…)`", "") , "process substitution left in candidate ops"
OLD_RESOLVE = '"$PY" -I -B "$OUT/prep/resolve-src.py" > "$OUT/prep/source.env"; tail -n 1 "$OUT/prep/source.env"\n'
GATE = 'echo "next_step_reached load_rc=$?"\n'

# --- 加载：修前块（bash 3.2）与候选块 ---
cases = {}
cases["old_ok"] = run("old_ok", OLD_RESOLVE + OLD_LOAD + "\n" + GATE + ECHO)
cases["old_stale"] = run("old_stale", OLD_RESOLVE + OLD_LOAD + "\n" + GATE + ECHO, pre="export WEIGHTS=/stale/w.gguf\n")
cases["old_resolve_fail"] = run("old_resolve_fail", OLD_RESOLVE + OLD_LOAD + "\n" + GATE + ECHO, stub=STUB_FAIL)
NEW_CALL = LOADER + 'src_resolve && src_load && echo next_step_reached; echo "source_rc=$?"\n' + ECHO
cases["new_ok"] = run("new_ok", NEW_CALL)
cases["new_stale"] = run("new_stale", NEW_CALL, pre="export WEIGHTS=/stale/w.gguf\n")
cases["new_resolve_fail"] = run("new_resolve_fail", NEW_CALL, stub=STUB_FAIL)
cases["new_filter_fail"] = run("new_filter_fail", NEW_CALL, pre='mkdir -p "$OUT/prep/source.vars"\n')
cases["new_load_fail"] = run("new_load_fail", NEW_CALL, pre="readonly EXP_LLAMA_BIN_BYTES=999\n")
cases["new_bad_line"] = run("new_bad_line", LOADER + 'src_resolve && printf "%s\\n" "WEIGHTS=\\$(echo injected)" > "$OUT/prep/x" && '
                            '{ grep -v WEIGHTS= "$OUT/prep/source.env" > "$OUT/prep/y"; cat "$OUT/prep/x" "$OUT/prep/y" > "$OUT/prep/source.env"; } '
                            '&& src_load && echo next_step_reached; echo "source_rc=$?"\n' + ECHO)
results["load"] = {k: {"rc": v[0], "out": v[1]} for k, v in cases.items()}

# --- gen：修前/候选两条 gen，与 parse_runtime_build 同语义 ---
SEMVER = "version: 0.5.0-dev (build 0, commit unknown)\nbuilt with GNU 13.3.0 for Linux aarch64\n"
VERS = {"semver_verbatim": (SEMVER, 0), "legacy": ("version: 11381 (deadbeef)\nbuilt with gcc\n", 0),
        "missing_build": ("version: 0.5.0-dev (commit unknown)\n", 0), "missing_line": ("built with GNU 13.3.0\n", 0),
        "duplicate": (SEMVER + SEMVER, 0), "conflicting": ("version: 11381 (deadbeef)\n" + SEMVER, 0),
        "out_of_domain": ("version: 0.5.0-dev (build 12345678, commit unknown)\n", 0), "nonzero_rc": (SEMVER, 1)}
GENS = {"mini_B": (MINI, "## 附录 B 资产 JSON 生成块", "rc"), "diag_1": (DIAG, "### 附录 1 diag-assets.py", "version_rc")}
gen_res = {}
for gname, (rel, marker, rck) in GENS.items():
    for ver_name, (vtext, vrc) in VERS.items():
        shas = "".join("%s  %s\n" % (VALUES["EXP_%s_SHA" % n], VALUES[n]) for n in ("WEIGHTS", "MMPROJ", "LLAMA_BIN"))
        raw = shas + ("sha_rc=0\n" if gname == "diag_1" else "") + vtext + "%s=%d\n" % (rck, vrc)
        try:
            tool = parse_runtime_build(vtext) if vrc == 0 else "StartRefused"
        except StartRefused:
            tool = "StartRefused"
        row = {"tool": tool}
        for side, text in (("old", old_text(rel)), ("new", new_text(rel))):
            case = f"gen_{gname}_{ver_name}_{side}"
            out = WORK / case
            out.mkdir(parents=True, exist_ok=True)
            (out / "gen.py").write_text(fenced_after(text, marker, "python"), encoding="utf-8")
            (out / "raw.txt").write_text(raw, encoding="utf-8")
            args = ["gen", str(out / "raw.txt"), str(out / "out.json")] if gname == "diag_1" else [str(out / "raw.txt"), str(out / "out.json")]
            if side == "new":   # 候选：变量经候选加载块加载后再跑 gen（与操作单第 3 节第 4 步同序）
                rc, text_out = run(case, LOADER + "src_resolve >/dev/null && src_load >/dev/null || exit 97\n"
                                   + " ".join(['"$PY"', "-I", "-B", shlex.quote(str(out / "gen.py"))] + [shlex.quote(a) for a in args]) + "\n")
            else:   # 修前：变量直接注入环境（修前加载块在 bash 3.2 下不加载，见上；这里只核修前 gen 本身的解析）
                env = dict(os.environ, **VALUES)
                r = subprocess.run([PY, "-I", "-B", str(out / "gen.py"), *args], capture_output=True, text=True, env=env, timeout=60)
                rc, text_out = r.returncode, r.stdout + r.stderr
            last = text_out.strip().splitlines()[-1] if text_out.strip() else ""
            build = json.loads((out / "out.json").read_text())["runtime_build"] if (out / "out.json").exists() else None
            row[side] = {"rc": rc, "last": last, "runtime_build": build}
        gen_res[f"{gname}/{ver_name}"] = row
results["gen"] = gen_res
print(json.dumps(results, ensure_ascii=False, indent=1))
```
