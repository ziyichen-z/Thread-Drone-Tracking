# COORD-019 落地记录：双路并发（2026-10-10，supervisor 会话一轮落地）

授权：`docs/authorizations.md` 2026-10-10「全局 — 用户直接授权协调批次 COORD-019：双路并发（Active handoffs 加 `Lane` 列，`fast`/`vlm` 每路 1 消耗 + 2 零消耗），并同意 VLM 线先按诊断道开」。
性质：零消耗协调批次，不经构思/接受轮（先例 COORD-013/017）；合规凭据为提交信息引用上述账本条目，常规角色写入检查不适用（AGENTS.md「角色边界」/ workflow §7 规则 7）。
执行会话：supervisor（Claude Code，Fable 5.1，MacBook Air）。落地期间另一 supervisor 会话正在同一仓库推进 `P1-ENG-FASTFIX-001`（d26d894 等），本批所有改动按磁盘最新内容做锚点增量修改，未整文件覆盖。

## 1. 规则改动（一句话）

Active handoffs 由全局「1 条消耗性 + 2 条零消耗」改为分两路（新增 `Lane` 列，闭集 `fast` / `vlm`），每路各自「1 条消耗性 + 2 条零消耗」。消耗性定义、Gate-echo、`PAUSED_*` 表示法、共享槽位互斥、信封来源红线不变。不拆第二个状态板文件。

归路判据（AGENTS.md「执行轨道纪律」原文为准）：`fast` = 快层、闭环、场景、机身与云台、采集与操作流程，执行机 Air/Unity 主机；`vlm` = 语义层（VLM 数据、训练、探针、板端 VLM 部署与 Jetson 探测），执行机 Mac mini、5060、Jetson、云 GPU。归路由写行角色判断、接受角色可更正；零消耗协调项按其服务的一路归入，两路都涉及的归 `fast`；两路信封分别签、同机互斥由用户在信封写明。

## 2. 改动文件

| 文件 | 改动 |
|---|---|
| `AGENTS.md` | 「工作流轨道路由」红线句改为每路上限；「执行轨道纪律」首段改写：双路、`Lane` 列、归路判据、信封分签 |
| `docs/collaboration-workflow.md` | §7 规则 0 两处改为分两路、每路 1+2 |
| `docs/engineering-workflow.md` | §8 第一条改为每路 1+2，`Lane` 列逐行声明 |
| `docs/roles/acceptance.md`、`docs/roles/implementation.md`、`docs/proposals/README.md` | 复述句同步为每路 1+2 |
| `tools/check_docs.py` | 新增 `LANE_COLUMN`/`LANE_VALUES`；`handoff_activity` 返回按路字典，`Lane` 缺列或非闭集值 fail-closed；`check_track_discipline` 按路计数；`check_consuming_gate_blocks` 汇总各路消耗性行；模块文档第 2 条更新 |
| `tests/test_check_docs.py` | 夹具加 `Lane` 列；原上限用例改为同路超限；新增 `test_consuming_cap_is_per_lane`、`test_zero_consumption_cap_is_per_lane`、`test_lane_column_is_required_and_validated`；`without_lifecycle_column` 改为只替换 Gate board 表头+分隔行 |
| `docs/current-status.md` | 交接表加 `Lane` 列并逐行归路（下表）；交接节说明段改双路；Immediate next actions 的当前计数改按路并加 VLM 诊断道指针；Log 一条 |
| `docs/workflow-changelog.md` | §1 批次索引加 COORD-019；§2.1 执行轨道纪律、§2.2 规则 0、§2.3 §8 各加来历 |
| `docs/authorizations.md` | 上述授权条目（用户原话逐字） |
| `docs/evidence/COORD-VLM-DIAG-2026-10-10/` | VLM 线诊断道独立状态板 `status.md` 与评估集 S 层初步读数 |

## 3. 交接行归路

| Work ID | Lane | 依据 |
|---|---|---|
| `P1-ENG-FASTFIX-001` | fast | 快层发布降级与重捕 |
| `P1-ENG-ACQ-001` | fast | 指针式快层与换目标捕获 |
| `P1-ENG-LOOP-002` | fast | 闭环及 Ops |
| `P1-SCENE-005` + `P1-SCENE-007` | fast | 场景 |
| `P1-ENG-JET-001` | vlm | 板端 VLM 部署与 Jetson 探测 |
| `COORD-018` | vlm | 服务对象为 JET-001 板端环境操作 |
| `P1-ENG-SFT-003`、`P1-VLM-SCOPE-001/002`、`P1-VLM-CAL-001` | vlm | 语义层 |

落地时各路活跃计数：`fast` 0 消耗性 / 1 零消耗（FASTFIX-001），`vlm` 0 消耗性 / 1 零消耗（JET-001）；其余行均 `PAUSED_*`。

## 4. 检查

| 检查 | 结果 |
|---|---|
| `python3 -m unittest tests.test_check_docs` | 38 个用例全部通过（含 3 个新增） |
| `python3 tools/check_docs.py`（工作树） | 通过：分节上限、执行轨道纪律（双路）、Gate-echo、复核文件、消耗性门、DONE 双证据、Log 可压池、字节上限、commit 引用、Last updated、hooksPath |
| `python3 tools/check_ledger.py`（暂存账本） | 通过 |
| `python3 tools/check_role_writes.py --role supervisor` | 报 8 个白名单外路径（AGENTS、两份 workflow、三份角色/README、`tools/check_docs.py`、`tests/test_check_docs.py`），均为本协调批次授权范围，按规则不适用 |

未跑全套 `unittest discover`：本批只改 `tools/check_docs.py` 与其测试，其余测试模块不依赖该文件（COORD-009 测试输出纪律，核对/窄修以 focused 代替全套）。

## 5. 未做与后续

- 未拆第二个状态板文件；按路阅读只靠 `Lane` 列与 work ID 过滤，未新增按路分节或按路 Log，Log「新在上」插入点仍是两路共用，两机并行提交时须先拉后写。
- `COORD-018` 现状不变（D1 退修、D2 待作者会话）；本批占用 COORD 节流窗口，下一个 supervisor 提出的 COORD 批次最早 2026-10-15（上一批 COORD-017 2026-10-04）。
- `outputs/project-workflow-kit/` 下的规则参考副本不在版本控制内，未同步。
- VLM 诊断道阶段 0 审计待派发（零消耗）；探针等任何消耗须用户另签信封。

## 6. 补充同步（同日，用户选 (a)）

授权：账本 2026-10-10「全局 — 用户选 (a)：单写者规则改按路…」。
改动：`docs/roles/supervisor.md`「唯一执行」「派发登记」「启动前登记与全局去重」「重启后对账」「并发/消耗纪律与会话卫生」；`AGENTS.md` 角色边界 supervisor 条；workflow §1.1 池表；engineering §8；`.claude/commands/supervisor.md` 与 `.agents/skills/supervisor/SKILL.md` 第 1、2 条。
语义：每路至多 1 个写仓库角色、两路可并行；派发去重与重启对账只看本路，另一路未终结派发只记摘要；`requested` 新增 `lane`（闭集 fast/vlm，旧事件无此字段时按交接表 `Lane` 列归路）；并行期间共享文件只追加或锚点增量、只 add 本路具名文件、推送前 fetch 变基、不动另一路未提交改动。
未改：`tools/check_docs.py`（不检查派发日志）；`tools/make_supervisor_drill.py`（`lane` 为可选字段，演练脚本不受影响）。
检查：`check_role_writes --role supervisor` 报白名单外路径均在本批授权范围；`check_docs`、`check_ledger` 以提交钩子结果为准（见提交信息）。
