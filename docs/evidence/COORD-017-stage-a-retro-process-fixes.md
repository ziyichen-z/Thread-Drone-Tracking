# COORD-017 — P1-ENG-JET-001 阶段 A 复盘的流程修订：取证与改动清单

授权：`docs/authorizations.md` 2026-10-04「全局 — 用户授权协调批次：按 JET-001 阶段 A
复盘修改七处流程文件…」与同日「全局 — 用户确认 COORD-017 草案并指示现在落地…」（用户
过目逐句改动后确认）。零消耗，不经接受轮。本文是批次记录，不是规则；规则以各规则
文件现行正文为准，来历见 `docs/workflow-changelog.md`。

## 1. 取证口径与数字

- **派发次数**：`docs/evidence/supervisor-dispatch.jsonl` 中含 `P1-ENG-JET-001` 的行按
  `dispatch_id` 去重，按 ID 内 UTC 日期分组：09-28 5、09-29 2、10-02 11、10-03 23、
  10-04 9，共 50 次；10-02…10-04 三天 43 次。角色分布：接受 29、实现 14、复核 3、
  构思 2、未标 2。
- **用户入账次数**：`docs/authorizations.md` 标题含 `P1-ENG-JET-001`、日期 10-02…10-04
  的条目 23 条，扣 1 条 supervisor 代拍为 22 条。按标题人工归类：装 torch 6（路径 A、
  sudo 装 pip/venv、改选系统栈与 cu130 源、SUB:1、SUB:3、题 6）；停点全套 6（SUB:2、
  SUB:5 A、CPU-1、1A 与环境分列、SUB:6、R2-1 窄修选 (a)）；硬件读数处置 2（题 7 α、
  S2 α′）；设备与链路 4；流程破例与路径选择 4。
- **停点全套**：`docs/evidence/P1-ENG-JET-001-full-suite.log` 末行 `Ran 2136 tests in
  235.682s`。与全套有关的派发 12 次：落实SUB2、全套（未跑）、全套待裁定、落实SUB5、
  落实CPU1、全套CPU1、全套CPU1待裁定、落实1A、证据整理1A、落实SUB6、全套SUB6、
  落实R2例外（状态板 Log 同名条目）。
- **装栈**：S1 首次实跑前的实现派发 首派、补跑、补跑B、补跑C，后三次未产出 S1 读数；
  补跑B 因依赖干跑多取回 2,318,455,950 B。
- **停止处置**：S1、S2 两次 `STOP` 各经「待裁定」「落实」两次接受派发后才续跑。
- **不可重跑消耗**：SR 轮 5/5 用尽后，`R1@K1K3K4`、`R2@K1K3K4` 才发现回程去重缺陷
  R1-1、R2-1；补丁未上板。
- **F3a**：交接行缺登记轮次字面的核查失败见状态板 Log 2026-09-29 三条（ACQ-001 的
  K1K2K3样帧、K1K3操作页返工、R2 处置派发）与 2026-10-03 一条（JET-001
  `R1@K1K3K4`），另 `docs/status-history.md` 记有 2026-09-28 一次；各角色细则与入口
  文件此前均无「交接行含登记轮次」一句（`grep Progress` 为空）。
- **提案体量**：`wc -c` 与按 `## ` 一级标题分段求和。JET-001 提案 290,547 B：决策记录
  143,920 B、待裁定 82,012 B、正文 §0–§8 51,173 B；交接文件 190,809 B。

## 2. 改动清单

| # | 文件 | 新增内容 | 对应的阶段 A 代价 |
|---|---|---|---|
| 1 | `docs/proposals/README.md` 工程模板；`docs/engineering-workflow.md` §6；`docs/roles/implementation.md` 工程轨道 | 信封默认含「每个候选 1 次、至多 N 个候选」停点全套的本机模型加载/回放额度；只改具名文件的窄修可用 focused 加修前红/修后绿代替全套，复核可要求全套 | 全套相关 12 次派发、6 次用户表态 |
| 2 | `docs/roles/acceptance.md` 工程轨道；`.claude/commands/accept.md` 指针句 | 通过线写出处与比较基线；厂商标称或移植来的线只作描述、不作停止条件；判定取运行时合同条件，压力档与冷启动单列；每个 `STOP` 写缺省处置并随信封交用户确认；已接受而信封未签的阶段补核 | S1、S2 两次停止 |
| 3 | `docs/engineering-workflow.md` §9 | 端侧环境事实先有只读预检读数；未核实的标为假设，依赖它的额度维度不申请签发 | 装栈 3 次实现派发、6 次用户表态 |
| 4 | `docs/engineering-workflow.md` §4；`docs/roles/implementation.md` 工程轨道指针 | 候选含不可重跑的消耗步骤时，其代码先过一次停点再消耗 | SR 额度用尽后才发现缺陷 |
| 5 | `docs/roles/` 五个角色细则、`.claude/commands/` 五个入口、`.agents/skills/` 四个入口的「被 supervisor 拉起时」；`docs/roles/supervisor.md` 复核固定模板 | 交接行 Status 或 Progress 逐字含 `requested.round` | F3a 至少 5 次失败，各需用户裁定不退回 |
| 6 | `docs/roles/implementation.md` 职责 | 下载额度纪律：先固定清单，禁止会取回依赖体的干跑，逐个取回核 sha，离线安装 | 多取回 2.3 GB、追加 SUB:3 |

另：`docs/workflow-changelog.md` 加批次索引一行与 §2.3 三条来历。

## 3. 未落地与边界

- 原列第七项（提案文件字节上限、已答复的裁定只留一行指针）与
  `docs/roles/acceptance.md` 工程轨道「答复只能追加…原文不覆盖、不删除」冲突，本批不做，
  未改 `tools/check_docs.py` 与任何测试。替代的「现行条款索引」方案用户未答复，不做。
- 「复核后重跑预留」不在授权的七处之内，未写入。
- 仓库外 `~/.codex/prompts/codex.md` 未改：该入口写明以 `docs/roles/acceptance.md` 为准。
- `.agents/skills/` 四个入口不在首条授权列举的连带文件内，已由同日确认条目一并覆盖。
- COORD 节流：上一批协调批次为 2026-10-02；用户在知悉 5 天窗口最早为 2026-10-07 后
  直接指示现在落地（确认条目授权范围 (2)）。
- 新句对落地之后签发的信封、接受的提案与阶段生效；已签信封与已有 verdict 不回溯。

## 4. 核验（草案 worktree 与落地前主树各一次，结果相同）

- `python3 tools/check_docs.py`、`python3 tools/check_ledger.py`：通过。
- `python3 tools/check_route_text.py --spec docs/evidence/COORD-016-route-spec.json`：
  70/70，被监控句未触及。
- `python3 -m unittest tests.test_check_docs tests.test_check_ledger
  tests.test_check_role_writes tests.test_check_route_text`：151 例 OK。
