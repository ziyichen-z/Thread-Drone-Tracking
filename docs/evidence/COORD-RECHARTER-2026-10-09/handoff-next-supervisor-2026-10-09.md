# 交接：下一 supervisor 会话的任务 = 回放测试设计（2026-10-09）

## 你是谁、能做什么

supervisor 角色（`docs/roles/supervisor.md`）。写入白名单只有 `docs/current-status.md`、`docs/authorizations.md`、`docs/unity-test-log.md`、`docs/evidence/COORD-*`、`docs/evidence/supervisor-dispatch.jsonl`、`docs/project-background.md`、`docs/workflow-changelog.md`、`docs/proposals/COORD-*.md`。**不写 tools/、tests/、controller/，不跑模型，不加载 YOLO，不 Play，不连板。** 本任务零消耗。

用户 2026-10-09 已明示：六项待决（主线文字入账、第一轮额度、第二轮额度、场景改动项、属性分类器、共驻表述）**先不定，等数据**。不要再追问这六项。你的产出是让那一次数据采集可以一签就跑。

## 任务

写 `replay-test-design-2026-10-xx.md`（放本目录），内容：

1. **R-1 到 R-5 的逐项设计**（定义见 `architecture-skeleton-v3-2026-10-09.md` §9，修正见 `v3.1-revision-items-2026-10-09.md` A4/A7/A8/A13/C1/C2/C4）：输入帧集合、读取的文件与字段、历史重建方式、每个参数的估计式、删失处理、输出表、暂定值的样本量标注。
2. **导出规格**：v3.1 §D 的汇总清单落成字段表与文件名；合成转向帧（C2）的变换参数、位姿改写方式与边界处理写明。
3. **额度申请草案**（只起草，不签）：一次 YOLO 加载、推理帧数、零 Play、墙钟、Air 新增磁盘、零板上动作、零下载；按 `docs/authorizations.md` 信封格式写，供用户签。
4. **代码事实核清**（只读）：ultralytics 8.4.104 BoT-SORT GMC 对状态均值与协方差的变换契约（决定位姿补偿怎么替换）；`controller/resident_core.py::designate` 拆成纯解析与 `follow()` 要动哪几行；lost 池预测框逐帧可读性；`controller/det_assoc_tracker.py` 的 `_step` 能否拿到未关联原始检测。结果写进设计文档「代码事实」节，附文件与行号。

## 输入在哪里

- 10-08 诊断根（本机 Air）：`outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261008T213653Z/`
  - 帧与位姿：`play/diag-loop2-214005/frames/frame_<N>.jpg|.json`（540–600 连续，更早的 epoch 1、2 静止目标段也在，可作对照）
  - 会话流：`play/sessions/diag-loop2-214005/language-session.jsonl`（第 580 行 designation、619 行 suspect_raised）
  - 常驻快层逐帧：`segments/diag-loop2-214005/runs/diag-loop2-214005-resident1/frames.jsonl`（只有指针框，无全部轨迹行，这正是要重放的原因）
  - 真值（只用于离线评分）：`play/diag-loop2-214005/m3_body_truth.jsonl`
  - 板上时延：`board/serve-channel-1.log`（prompt eval 0.78 s / decode 0.9 s）
- 冻结快层规格：`config/det-assoc-v1.models.json`、`docs/evidence/P1-ENG-FAST-002-freeze.json`、权重 `outputs/eng-det/runs/run-1/weights/last.pt`
- 相机：fx = fy = 415.692，cx 320，cy 240，640×480，垂直视场 60°
- 已核事实：`README.md`「代码事实」段；standoff 距离为水平距离。

## 边界

- 设计文档里的数值一律标「占位」或「暂定（n=…）」。
- 不改 v3 正文；需要改口径写进设计文档「对 v3.1 的追加」节。
- 完成后：状态板 Log 一条（≤600 B）、交接行改为等待用户签回放额度；`python3 tools/check_docs.py`、`check_ledger.py`、`check_role_writes.py --role supervisor` 通过后提交推送。
