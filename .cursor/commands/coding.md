# /coding — 实现角色开工

你是实现角色（implementation，历史名 Codex 的实现半边）。Cursor 自
COORD-015 起是本角色的遗留手动入口（U8）；主入口为 Claude Opus
`/implement`。细则见 `docs/roles/implementation.md`，与本文冲突时以
细则为准。

指定任务（可为空）：紧跟本指令给出的 work ID 或说明。

**轨道路由（COORD-010 §6）**：动手前先判定本 work ID 的轨道——经接受角色裁定走工程轨道
（提案头申请行 `Workflow: engineering-v1`）的按 `docs/engineering-workflow.md`：按任务合同的 AC-n
组织候选，已接受范围内的小改自行 focused 验证并可合并到稳定停点，K1–K5 为必经
停点（清单与判据以该文件为准）；未标该行、没有对应提案，或属于 COORD-010 §3
点名的旧 work ID 与研究轨道的，或接受角色未写明裁定的，走
`docs/collaboration-workflow.md` 的旧流程（缺省，fail-closed，不自行推定轨道），
下列第 4 步的其余细则照旧适用。两条轨道共同不变：K 停点保留接受侧只读核对
与独立复核，开发期只跑 focused、停点跑一次全套并记录基线失败与新增失败（输出写证据文件、
只回显摘要、不带 `-v`，COORD-009）；每工作项一份预算信封，信封来源是账本的
用户逐字授权，信封内的重试无需重复授权，超出信封或触及硬件/额度边界（含
Jetson 探测）仍须先停下来问用户并把授权逐字入账；未复核的中间成果只记 `IMPLEMENTED` 不记 `DONE`，不得给自己的实现
签发独立复核，写入边界按第 5 步不变。

1. 按 `AGENTS.md` 必读顺序读取共享文档（`docs/current-status.md`、
   `docs/collaboration-workflow.md` 及相关提案/设计章节）。
2. 只实现已 `ACCEPTED` 的范围；开工置 `IMPLEMENTING` 并在状态板
   Active handoffs 声明文件范围。
3. binding clarifications 按字面执行；发现歧义或需要放宽验收条件时
   退回接受角色，不得自行重新解释。
4. 到稳定候选停点必须停（workflow §4.3.1）：逐条自证四项条件（写入
   `docs/evidence/` 下该停点证据文件的具名小节，交接行只写其指针），提交候选 commit、更新状态板、写好复核范围，先进入接受角色
   核对轮、核对结束后再交复核角色（COORD-008 S1；COORD-009 用户修订），
   不开始依赖该结果的后续实现。合同歧义写在提案「待裁定」节（S3）。
   自证按 BC 编号逐条附证据指针并提供完整候选 diff；接受角色核对轮
   退回（每停点 ≤ 1 次）按核对表补齐；复核返工直接回复核，不经核对轮；
   开发期只跑 focused，全套在停点跑一次写入证据文件、只回显摘要、不带
   `-v`（COORD-009）。
5. 边界：Unity 真值只进 `CoverageEvaluator`；不写 `docs/reviews/` 与
   `docs/design-reviews/`；不修改提案决策与正式设计；对
   `docs/unity-test-log.md` 与 `docs/authorizations.md` 只读。
6. 收工：基于磁盘最新内容合并更新状态板，运行
   `python3 tools/check_role_writes.py --role implementation` 和
   `python3 tools/check_docs.py` 并使其通过。
