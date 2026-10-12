# P1-ENG-ACQ-001 — K1K3 停点自证（candidates 后端接线 B1–B3 窄修）

派发：`P1-ENG-ACQ-001-K1K3-20260929T215535Z-0636`（Implementation，Opus 子代理，2026-09-29）。
依据：提案「candidates 后端接线窄范围修复 CLARIFY（2026-09-29）」（AC-21、AC-18 修订 3）；`docs/evidence/P1-ENG-ACQ-001-play-d1.md` §0（B1–B3）；
账本 2026-09-29「用户授权窄范围代码修复（`candidates` 后端接线 B1–B3）…」。B4/B5 按裁定**不并入**。

候选：本轮主题以 `P1-ENG-ACQ-001 K1K3 candidates 后端接线 B1–B3 窄修` 开头的代码提交（SHA 运行时解析：
`git log --format=%H --grep='^P1-ENG-ACQ-001 K1K3 candidates 后端接线' -1`，不手写）。上一复核轮候选见
`docs/reviews/P1-ENG-ACQ-001.md`「R3@K1K2K3」§0 的 `round_candidate`。完整候选 diff：
`git diff <R3 round_candidate>..<本候选> -- controller/ tests/ tools/`（本批只改 5 个文件，见「复核范围」）。

## 自证四项（workflow §4.3.1）

1. **范围与接口已冻结**：只做 AC-21 的 B1/B2/B3；接口 = `run` CLI 的 `--backend`/`--model-form` 闭集与缺省、K 收据
   `candidates` 单宿主校验、结果 `model` 块闭集配对、零消耗预检命令 `tools/eng_acq/candidates_preflight.py`。未改 Unity 场景/`Assets/`、
   `config/`、Play D1 信封数值；未改会话状态机、`LanguageWorker`、预览/采集/保存路径与候选选框规则。
2. **实现者测试通过**：B1/B2/B3 各有具名 focused 测试，逐缺陷修前红/修后绿（见「测试与红绿」）；`.venv-language` 语言/桥/收据/伺服
   六模块 324 通过；停点全套本批新增失败 0。
3. **已知 Unity 失败**：本批无 Unity 运行（信封 Play = 0）；AC-18 仍 `NOT_RUN`。正式收据须用户在 Unity 主机按操作单 §2.7 生成，
   本机只用临时目录合成夹具做测试，**未生成任何正式收据**。
4. **复核文件、状态板、候选与风险**：候选已提交推送；状态板交接行改交 Acceptance `C1@K1K3`；复核范围与未验证风险见下文。

## 逐 AC 证据

| AC | 结论（实现者自评，非复核） | 证据指针 |
|---|---|---|
| AC-21 B1 | `run --backend candidates` 进 CLI 闭集（`bridge.BACKENDS`）；`_build_adapter` 构造真实 `CandidatesBackend`；省略 `--model-form` 取 `detector-tracks`（`resolve_model_form`），显式 `detector-tracks` 亦可；`candidates`×VLM 形态、VLM 后端×`detector-tracks`、`candidates` 缺 `--resident` 或跟踪器非 `det-assoc-v1` 均在读收据/建适配器/建会话目录前 `CONFIG_MISMATCH` | test: `tests/test_language_loop.py::CandidatesBackendWiringTests::test_b1_run_cli_candidates_builds_real_candidates_backend`；`::test_b1_cross_forms_and_missing_resident_refused_before_session`；cmd: `.venv-language/bin/python -m unittest tests.test_language_loop.CandidatesBackendWiringTests` |
| AC-21 B2 | `validate_measurement_sources` 对 `candidates` 走 `_validate_candidates_source` 单宿主分支：收据 `host=mac`、`model_identity` 逐字等于三字段 `CANDIDATES_IDENTITY`（多出 `weights_sha256` 等即拒）、`source_reports` 恰一份 `mac`；报告字节 SHA、`host=mac`、`verdict=OK`、`machine_name` = 本机 `platform.node()`、`backend/model_form/model_identity/hz/retained_frame_count/p95_s` 与收据逐项相等、`p95_s` 有限 ≥0、`none`/`tracked` 两组各 ≥100 样本且组 p95 可由原始样本按最近秩复算、`p95_s` = 两组较大值、资格式成立；任一不符 `CONFIG_MISMATCH`（在建会话目录前）。生效场景 R/hz 与收据不符由既有检查点拒绝（在任何桥写入/会话锁前）。`KReceipt.from_document` 拒绝交叉形态与 `candidates` 的非有限/负 p95。VLM 双报告与 `replay` 路径不变 | test: `::test_b2_single_mac_report_validates_and_vlm_two_report_path_unchanged`；`::test_b2_receipt_or_report_mismatch_refused_before_session`（17 个子例：5060 宿主、权重身份、source 改变、双报告、收据 R/hz/p95、报告 FAIL/http/他机、不合格、样本不足、本机名不同、NaN、交叉形态、报告 SHA、收据 R=1500 对生效 R=128）；test: `tests/test_language_k_binding.py`（VLM 双报告回归，全过）；artifact: `tools/eng_acq/candidates_preflight.py`（预检与收据生成器） |
| AC-21 B3 | `bridge.require_backend_model_form`：`candidates` ⇔ `detector-tracks` 成对，原三后端×三 VLM 形态合法组合保持；`_validate_model_block`（写 `result_payload` 与读 `read_result` 共用）据此 fail-closed。真实 `LanguageSession`（`CandidatesBackend` + 单宿主收据 + `FakeResident`/真 `ResidentCore`）走 `ask`→`LanguageWorker`→`_emit_result` 写 `results.jsonl` 与桥结果→`read_result` 读回→预览→`confirm(1)`→`BOUND`，候选框逐一等于查询帧 N 的 `tracked` 历史（面积降序）；`CandidatesBackend.calls` = worker `calls_started` = 1 | test: `tests/test_language_loop.py::CandidatesBackendWiringTests::test_b3_session_ask_writes_candidates_model_block_readable_and_confirmable`；test: `tests/test_language_bridge.py::ResultBridgeTests::test_b3_candidates_model_block_pairs_only_with_detector_tracks` |
| AC-21 零消耗/夹具 | 测试夹具由生产预检工具在临时目录生成（合成历史行、合成 `frame_<id>.jpg`，不读图），无权重/检测/VLM/序列回放；不以夹具宣称就绪 | artifact: `docs/evidence/P1-ENG-ACQ-001-K1K3-redgreen.log`；cmd: 见「测试与红绿」 |
| AC-18 修订 3（本批相关部分） | 只做就绪前置的**文档与工具**：操作单新增 §2.7「`candidates` K 收据本地预检」逐字命令（用户在 Unity 主机执行；零消耗）与预期/硬停止；§4 T1 行填入 `--backend candidates` 与收据路径；§0/§3 注明新候选须 `R1@K1K3` 通过、新 `passed_candidate` 才能放行。B4/B5 未并入。Play 未运行，AC-18 `NOT_RUN` | artifact: `docs/evidence/P1-ENG-ACQ-001-play-d1.md` §0「K1K3 修订」、§2.7、§3、§4 T1 |

## 测试与红绿

- **修前红/修后绿**（`docs/evidence/P1-ENG-ACQ-001-K1K3-redgreen.log`，`.venv-language` 3.12）：在最终候选副本上逐一撤销单个缺陷的修复——
  - `minusB1`（撤 CLI 闭集/缺省/`resolve_model_form`/`_build_adapter` 分支）：两条 B1 测试红（`invalid choice: 'candidates'`；VLM 后端配
    `detector-tracks` 时未在校验前拒绝）；B2/B3 测试绿。
  - `minusB2`（撤单宿主分支）：两条 B2 测试红（`both source reports are required` 取代机器名/SHA/R 的具体拒绝）；依赖收据的 B1 CLI 与 B3 会话测试随之红。
  - `minusB3`（`model` 块退回旧闭集）：两条 B3 测试红（`backend must be one of ('local-hf', 'http', 'replay'); received 'candidates'`，
    会话测试红在 `ask` 后的结果写盘处）；B1/B2 测试绿。
  - `head`（HEAD 控制器 + 本批测试/工具）：6 条全红；`full`（最终候选）：6 条全绿。
- **停点全套**：`python3 -m unittest discover -s tests > docs/evidence/P1-ENG-ACQ-001-K1K3-tests.log 2>&1`（系统 python3 3.9.6）：Ran 1642，
  `FAILED (errors=82, skipped=79)`；82 个 error 的测试名集合与上一停点全套 `docs/evidence/P1-ENG-ACQ-001-tests.log`（Ran 1641）**逐一相同**
  （3.9 不支持的注解语法与缺依赖；`test_language_loop` 在 3.9 下整模块导入失败，本批新增的 5 例因此不计入该数）；+1 例为
  `test_language_bridge` 的 B3 新测试（通过）。**本批新增失败 0。**
- **解释器分组 focused**（`docs/evidence/P1-ENG-ACQ-001-K1K3-focused-venv-tests.log`）：`.venv-language` 的 `test_language_loop`
  `test_language_bridge` `test_language_k_binding` `test_language_selector` `test_gated_publisher_slew` `test_track_loop` 共 324 通过（4 跳过）。
- **未跑**：数据根 `.venv-yoloe` 的跟踪器/载体用例。本批未改 `controller/det_assoc_tracker.py`、`resident_core.py`、`trackers.py`、`track_loop.py`；
  且该环境下 `test_det_assoc_carrier.CarrierSelfTest` 会做真实检测推理、`ResidentCarrierReplay` 计序列回放，本信封两项均为 0，故不运行。

## 承接声明（AC-10 / AC-17 口径）

- **预览/采集/保存路径**：未触及。`render_preview`、帧环快照、`FrameRepository`、归档与 `GatedPublisher` 未改；`_emit_result` 未改，
  只是其调用的 `bridge.result_payload` 的 `model` 块校验闭集扩为成对的 `candidates`/`detector-tracks`。AC-17 样帧前置结论不受影响。
- **`LanguageWorker`/延迟排队域**：未触及（`LanguageWorker`、`_submit_query`、`_poll_worker`、确认时效与 T_ret/T_conf/K_pub 检查点未改）。
  B3 会话测试经由真实 worker 路径（`inline_spawn`）执行。
- 会话状态机、`designate` 解析器、候选选框规则（`CandidatesBackend.predict_one`）未改；`CandidatesBackend.identity` 改为引用同值常量
  `CANDIDATES_IDENTITY`（内容逐字不变）。

## 实现读法（CLARIFY 未逐字规定处；如有异议请接受角色裁定，本批未扩大范围）

1. 「机器名」= `platform.node()` 逐字相等；预检工具把它写进报告 `machine_name`，会话启动时比对本机同一函数。
2. 「报告写明样本数、两组 p95」：报告保存两组原始样本（各 ≥100，缺省 200），校验按最近秩（`sorted[ceil(0.95n)-1]`）复算组 p95；
   `p95_s` 须等于两组较大值。
3. 资格式不成立：预检工具报告 `verdict=FAIL`、不写收据（退出码 6）；若仍被拿来启动，校验 `CONFIG_MISMATCH`。非 macOS 上预检同样 `FAIL`。
4. 收据 `model_identity` 须**逐字等于**三字段身份（多出 `weights_sha256`/`device` 等即拒），以落实「不伪造 VLM 权重身份」。
5. `results.jsonl` 的 `model` 块沿用既有固定字段（`backend`/`model_form`，其余为 null）；`source` 字段只在启动时与收据身份比对，不写进结果行。
6. 生效场景 R/hz 与收据不符沿用既有检查点：它位于建会话目录之后、任何桥写入与会话锁之前（本批未挪动该检查点）；收据与报告之间的
   R/hz/身份/SHA 不符在建目录前拒绝。

## 复核范围（修复触及的函数；上一轮候选见 `docs/reviews/P1-ENG-ACQ-001.md`「R3@K1K2K3」§0）

- `controller/language_bridge.py`：`BACKENDS`/`MODEL_FORMS` 闭集、`CANDIDATES_BACKEND`/`CANDIDATES_MODEL_FORM`、新增
  `require_backend_model_form`、`_validate_model_block`（`result_payload` 与 `read_result` 共用）。
- `controller/language_loop.py`：`KReceipt.from_document`（配对与 candidates p95 检查）、新增 `CANDIDATES_IDENTITY`/`CANDIDATES_MIN_SAMPLES`/
  `CANDIDATES_TRACKER`/`nearest_rank_p95`/`machine_name`、`CandidatesBackend.__init__`（identity 引用常量）、新增 `_validate_candidates_source`、
  `validate_measurement_sources`（新分支与 `current_machine` 参数）、`_build_adapter`（candidates 分支）、新增 `resolve_model_form`、
  `_run_session`（首行调用）、`build_parser`（`--model-form` 缺省 None）。
- `tools/eng_acq/candidates_preflight.py`（新）：`measure_group`、`build_report`、`build_receipt`、`run`、`main`。
- `tests/test_language_loop.py`：`Harness`（新增可选 `adapter`/`receipt` 参数，缺省行为不变）、`CandidatesBackendWiringTests` 5 例与辅助函数；
  `tests/test_language_bridge.py::ResultBridgeTests::test_b3_candidates_model_block_pairs_only_with_detector_tracks`。
- PLAY_GOVERNING：会话启动门（CLI、收据校验）与结果 schema（非空）。K1：收据与生效 R/hz、截止预算的绑定；K3：后端模型决策与结果身份。

## 消耗

Consuming = no。scenario/session/run ID 0、Unity Play 0、模型 API/VLM 0、训练 GPU·h 0、检测推理与 YOLO 权重加载 0、下载/pip 0、
5060 与其他远端访问（含 Unity 主机）0、序列回放 0。本机 CPU：全套两次各约 126 s、focused 约 13–18 s × 数次、红绿变体 < 1 s × 5。

## 未验证项与已知限制

- 正式 `candidates` 收据只能由用户在 Unity 主机按操作单 §2.7 生成；本机夹具不代表该机的 p95 或就绪状态。
- 预检 p95 只覆盖适配器转换，不是在线检测或整体 Play 时延，也不保证确认时效内成功；4 s 人工等待仍可能 `stale_rejected`（CLARIFY 原文）。
- `.venv-yoloe` 跟踪器/载体用例本批未运行（理由见上）；R1-4 `SCOPE_GAP`/`OPEN` 不在本批范围。
