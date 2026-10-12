# 共驻诊断独立状态板（JET:CORES-DIAG:1）

本板只记板上共驻诊断的进度，与主线 `docs/current-status.md` 隔离（用户 2026-10-09 要求，账本同日条）。
主线状态板不再为本诊断改交接行；`P1-ENG-JET-001` 的门、Lifecycle、S1/S2 STOP、AC-7/8/9 `NOT_RUN` 均不受影响。
本诊断结果只作诊断（`diagnostic_only`、`gate_evidence=false`），不进 `docs/evidence/P1-ENG-JET-001-*`。
写入者：supervisor 会话。派发事件仍按全局规则记在 `docs/evidence/supervisor-dispatch.jsonl`（全局去重的唯一事实源）。

## 依据

- 账本 2026-10-09「P1-ENG-JET-001 — 用户方向：先做共驻诊断…签发 JET:CORES-DIAG:1」：范围、顺序、读数、停止条件、信封。
- 账本 2026-10-09「P1-ENG-JET-001 — 用户选择：JET:CORES-DIAG:1 改为独立目录执行…」：执行路径。
- 账本 2026-10-09「COORD-CORES-DIAG-2026-10-09 — 用户要求：共驻诊断用独立状态板…」：本板。
- 测试设计：`cores-diag-test-design-2026-10-09.md`（同目录）。

## 当前状态

| 项 | 内容 |
|---|---|
| 状态 | `DONE_AWAITING_USER_READ`：诊断已全部跑完，没有触发停止条件；结果待用户阅读 |
| 派发 | `P1-ENG-JET-001-共驻诊断执行-20261009T185616Z-77fa`，已核销（callback → finished），实现轮无提交 |
| 结果 | `cores-diag-results-2026-10-09.md`（同目录；§0 是 supervisor 核查，§1 是诊断读法） |
| 运行目录 | Mac `outputs/eng-jet/cores-diag/20261009T185849Z/`（不入仓），板上 `~/eng-jet/cores-diag/20261009T185849Z/`（13.7 MB，保留） |
| 信封用量 | 板上墙钟 4405/10800 s，VLM 加载 2/3，VLM 查询 366/400，PyTorch 加载 2/3，TensorRT 反序列化 1/3，其余维度 0 或远低于上限；余额作废、不转用 |
| 待用户 | 读结果；是否以及如何用到主线（例如快层选 PyTorch 还是 TensorRT），由用户另定，本板不代定 |

## 日志（新在上）

### 2026-10-09 — 执行完成并核销

三臂全部跑完，没有触发停止条件，信封在上限内。supervisor 用原件复算检测器延迟、丢帧、VLM 读数与一致性，结果与报告一致。结果照录在 `cores-diag-results-2026-10-09.md`。

### 2026-10-09 — 建立独立状态板

用户要求隔离、不影响主线任务。主线 `P1-ENG-JET-001` 交接行恢复为共驻诊断之前的原文（`AWAITING_USER_JET_DIRECTION`）。

### 2026-10-09 — 测试设计入仓并派发执行

用户选「独立目录，照回放先例」；测试设计入仓（`ead16f9`），派发登记（`ccdf2c3`），实现子代理在 mini 执行，不提交仓库。
