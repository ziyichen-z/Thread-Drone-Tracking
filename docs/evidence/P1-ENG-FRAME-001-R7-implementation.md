# P1-ENG-FRAME-001 — R7 离线字段路径窄修（Implementation，2026-10-01）

Status: **IMPLEMENTED_R7_AWAITING_ACCEPTANCE**。本轮用户授权范围已完成：R7 字段路径窄修、focused 红绿与旧真实 run 保留式复算。不是独立复核通过或 Unity PASS/DONE；新代码尚无通过凭据，补测仍不得启动。全套含实际模型加载，与本轮不启动 tracker/不载模型的明确范围冲突，未执行；当前不是自证完整的稳定停点候选。

## 范围与候选关系

依据：`docs/evidence/P1-ENG-FRAME-001-supplement-ops.md`「实现角色的具体交接」1–5；提案已接受 D2 / engineering-v1，既有 AC-21 与 §3.10 R-7，及账本 2026-10-01「用户授权实现子代理与本次补测480秒上限」。现有明确人类答复已限定需求，不另改合同、参数或额度。

- `tools/frame_follow_replay.py::analyze_run` 只增加 `aggregate.c_track` 后备读取。原 `top-level c_track` 优先，随后 `summary.c_track`；只有两处都无该键才读 aggregate。原空值、零值、缺失值、六位舍入与 CLI 显式 metrics 路径行为保留；不重算评估器指标、不改时间窗/阈值。
- `tests/test_frame_follow_replay.py::AnalyzeRunTests` 增三条具名测试及共用 helper；生产 `RunLogger` / `_build_body_runtime` 构造既有临时测试 run，不启动 tracker/模型。故障输入为真实评估器原始字节；兼容格式测试是明确的合成输入。
- `tests/fixtures/frame_follow_metrics_unity.json` 是原 `metrics.json` 的完整字节副本，未经加工。来源路径与 sha/大小由机器记录动态解析并核对，见下方复算记录 `fixture`；测试不依赖本机 runtime 归档存在。
- 本批其余变更只为 evidence 与当前状态。`controller/`、Unity、配置、冻结选参/回放证据、正式设计、合同、review、账本与 Unity 日志没有修改；R1-3 `SCOPE_GAP`/OPEN 不变。

完整候选 diff 在提交后读取本批 commit 的 `git show --stat --patch <candidate>`；候选由 `git log -1 --format=%H -- tools/frame_follow_replay.py` 解析，不手写候选 SHA。机器记录 `docs/evidence/P1-ENG-FRAME-001-R7-recompute.json` 保存开工基线、旧通过候选（从复核文件解析）、基线/修后工具 hash 与测试/fixture hash，绑定本轮输出；不把旧 R2@K2 `passed_candidate` 解释为新工具已获复核。

## focused 红绿证据（AC-21）

实际解释器为仓库 `.venv-yoloe/bin/python`，机器记录含 sys.executable/version。本机不存在约定的 `~/TetheredDroneTracking-full/.venv-yoloe`；首次该路径启动失败留在 `P1-ENG-FRAME-001-R7-environment.log`，不是测试红证据。接受角色已明确可只读使用既有仓库解释器执行纯离线测试，未安装包。`PYTHONPATH=tests` 避开该环境内同名 site-packages tests 包。

| AC/证明方式 | 命令与结果 | 日志 |
|---|---|---|
| AC-21 / test: `test_frame_follow_replay.AnalyzeRunTests.test_r7_reads_archived_unity_aggregate_c_track` | 修前 `PYTHONPATH=tests .venv-yoloe/bin/python -m unittest test_frame_follow_replay.AnalyzeRunTests.test_r7_reads_archived_unity_aggregate_c_track`：Ran 1 / failures=1，`None != 0.91899` | `docs/evidence/P1-ENG-FRAME-001-R7-red-tests.log` |
| AC-21 / test: `test_frame_follow_replay.AnalyzeRunTests` | 修后 `PYTHONPATH=tests .venv-yoloe/bin/python -m unittest test_frame_follow_replay.AnalyzeRunTests`：Ran 5 / OK | `docs/evidence/P1-ENG-FRAME-001-R7-green-tests.log` |

五条包括既有场景双 SHA 绑定拒绝/接受与原 read-outs 用例。新增真实 schema 回归消费 preserved metrics 字节，断言 R7 等于 aggregate.c_track 的原舍入值且不等于 c_track_given_geom；兼容测试 9 个 subTest 核 top-level/summary 优先、两处 null/0、aggregate 0、空 aggregate/全部缺失；最后一条确保未传 metrics 时不会从旁边 metrics.final 推断读数。测试 helper 放置另一个 metrics.final 文件，旧格式优先级用例能检出偷偷切换端点。

## 真实旧 run 复算与原件完整性（AC-21 / artifact）

唯一定位事实源为 `docs/evidence/P1-ENG-FRAME-001-play-result.json` 的 `run_directory` / `run_file_integrity` 与真实 manifest。路径、完整 sha、命令 token、代码 hash 及结果由本轮实际运行生成在 `docs/evidence/P1-ENG-FRAME-001-R7-recompute.json`。未手工回填 analysis。

1. 修前原工具 CLI 接收 `--metrics <run>/metrics.json`、`--truth <run>/m3_body_truth.jsonl`、manifest 的 `scenario_config_path`，写入先确认未用的 `frame_follow_analysis.r7-before.json`。退出码 0、R7=null，产物逐字段等于原 analysis。
2. 同一命令仅 output 换未用 `frame_follow_analysis.r7-recomputed.json`，用修后工具复算，退出码 0、R7=**0.918990**；输入 `metrics.json` raw `aggregate.c_track`=**0.9189902544021606**（Unity 退出端点）。与原 analysis 比较只有 `R7_c_track` 改变，所有 R1–R6/窗口/场景绑定/身份/安全读数均逐字段相等。
3. 仅作端点忠实性验证，显式另传 `metrics.final.json` 并写入另一未用文件 `frame_follow_analysis.r7-tracker-finish.json`，退出码 0、R7=**0.994950**；raw=**0.9949501752853394**（tracker 自然结束端点）。它是单独具名的显式输入，不替代第 2 条或原退出端点。
4. 修改前后 metrics、metrics.final、truth、summary、原 analysis、frames、manifest 七份核心原件完整 sha/大小均逐一等于 play-result 原记录；全部 **138** 份该记录原件亦核到不变。三个新输出只追加到已存在旧 run，不新建/消耗正式 run/scenario/session ID。

复算三个输出的文件完整 hash 和工具 hash 对应本轮源码（不是原采集代码）；原采集 manifest/summary/history 的候选身份不改绑。新复算修复工具输出缺口，不替代未完成的用户机身跟随/起停目检或完整按钮墙钟，不宣称 AC-21 整体满足。

## 停点与 PLAY_GOVERNING 适用核查

按已接受合同 §7，本轮不改变 K1 协议/坐标时间、K2 安全/控制、K3 模型决策、K4 划分/标签/对外指标或 K5 发布；R-7 是既有内部描述读数，主指标定义不变。但 tools/tests 属 workflow §4.4 的 PLAY_GOVERNING，且相对复核文件最近 passed_candidate 的 diff 非空；新增 fixture 也在 tests。因而新工具不能以旧 R2 凭据通过 workflow §4.5 的工作树检查；接受须先核验适用后续候选/复核路径，Play 保持未放行。实现不自行命名新 C/R 轮、派发 review 或回写历史 verdict。

若作为 K2 后续稳定候选，workflow §4.3.1 四项自证当前状态如下（不是全满足声明）：

| 条件 | 证据/状态 |
|---|---|
| 1 范围/接口冻结 | 满足于本次已授权窄修：原 AC-21 / §3.10 / supplement-ops 1–5，未改合同或 CLI |
| 2 相称测试/编译 | focused 5/5、真实 CLI 两端点与全原件核验满足。本轮未跑 AC-24 停点全套，不能借旧全套证明新候选；完整停点义务未完成，需先处理下节资源冲突 |
| 3 已知 Unity 失败 | R7 字段缺口经真实归档 red→green 修复；机身目检与按钮墙钟仍缺证，不由实现签 Unity；本轮无 Unity 代码变化、不开 Unity |
| 4 候选/文档/风险 | 本报告、机器记录、状态板随本批候选提交/推送，旧 review 原文不改。新工具尚无独立通过轮；因条件 2 未全，交接受处理，不能直接宣称 REVIEW_READY |

本批不重跑 Edit Mode：相对最近通过候选，`Assets/`、`ProjectSettings/`、`Packages/packages-lock.json` diff 为空（机器记录）；旧真实 Unity/Edit Mode 证据只保留为旧路径凭据，不冒充新离线工具通过。

## AC-24 全套待执行的资源边界（只读源码核查）

本轮明确不载模型、不启动 tracker，故未执行 `.venv-yoloe/bin/python -m unittest discover -s tests`；没有通过修改 skip 条件、搬走模型或偷偷筛去真实单测来冒称全套。旧 `P1-ENG-FRAME-001-tests.log` 的 2061 tests / failures=4、errors=9、skipped=19 仅是旧候选基线；本轮新增失败在 focused 中为 0，全套新增失败情况未验证。

| 已知会动用真实对象的用例 | 单次全套中具名路径的上限 | 资源性质 |
|---|---|---|
| `tests/test_trackers.py::TrackerAdapterTests.test_pinned_opencv_nanotrack_initializes_and_updates` | 1 次 NanoTrack 实例/加载（backbone+head 两文件） | 本地 CPU，真实 init/update，无正式采集 |
| `tests/test_track_loop.py::TrackLoopTests.test_cli_nanotrack_manifest_contains_frozen_identity` | 1 次 NanoTrack 实例/加载（两文件） | 临时 synthetic runtime 的真实 tracker loop，非正式 run |
| 上述两条合计 | **最多 2 次 NanoTrack 实例/加载、4 次权重文件加载**；当前模型文件存在，正常执行会进入，不应当成 skip | 本次信封模型 0，未执行；不能借补测 Nano 剩余额度转给单测 |
| `tests/test_trackers.py::TrackerAdapterTests.test_pinned_opencv_csrt_initializes_and_updates` 与 `tests/test_track_loop.py::TrackLoopTests.test_cli_runs_pinned_csrt_to_a_versioned_summary` | 各至多 1 个 CSRT 实例，无神经权重 | 本地 CPU，真实 tracker（现安装 OpenCV 的该既有路径失败不免 startup 边界） |
| `tests/test_det_assoc_carrier.py::CarrierSelfTest.test_carrier_matches_caliber_b_from_first_update` / `test_init_false_uses_existing_failure_path` | 条件满足时各 1 次 YOLO 检测器加载，合计最多 2；现缺默认数据根，所以当前条件不满足 | 必须另核 `ENG_DET_DATA_ROOT` / `_ready()`；不授权补齐数据或让其启动 |

该表是具名源码路径静态计数，不是全树所有未来配置的无条件上限或实际消耗。上述 Nano/CSRT 只用本地既有文件/临时测试帧，不请求 Unity Play、正式 ID、付费 API 或下载；可选 YOLO 真实路径也不能用「是单测」免除模型/GPU/依赖边界。全树其他用例含临时 ID 字符串/mock/API本地server，不等于正式 ID/API；若用户允许一次全套，发令角色仍须按当时环境确认真实 loader 与其他消耗上限，不能从此静态表推断新增资源授权。当前运行总消耗 **Play/正式ID/模型加载/API/GPU/下载安装全为0**。

## 交接受的下一动作

接受只读核本批完整 diff、AC-21 focused/原件/复算来源及 new-tool hash，裁定后续候选检查/复核路径与全套资源冲突如何处理；不得据旧 R2 或旧全套放行新工具对应的补测。完成必要停点自证与独立凭据后再处理补测放行。用户跟随/起停目检与完整墙钟仍未闭，480 秒与额外 Play 只用于已授权本次补测，不在本实现中使用。实现任务到此停止。

收工自检：`python3 tools/check_role_writes.py --role implementation` 与 `python3 tools/check_docs.py` 均通过；提交前再核未提交写入范围。未被 supervisor 派发，本轮无 Dispatch-Id，不虚构派发凭据。
