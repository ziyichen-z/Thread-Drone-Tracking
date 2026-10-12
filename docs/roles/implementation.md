# 实现角色（implementation）

历史名：Codex 的"实现"半边。运行池：Claude Opus（大量程，COORD-015 池
重分配），主入口 `/implement`；被 supervisor 拉起时以 Opus 子代理运行。
Cursor `/coding`（`.cursor/commands/coding.md`）保留为遗留手动入口
（COORD-015 U8），用户手动调起时等价有效；未调起角色的 Cursor 会话只做
只读浏览。

## 职责

- 只实现已 `ACCEPTED` 的提案范围；开工置 `IMPLEMENTING`，并在状态板
  Active handoffs 声明主要文件范围。
- binding clarifications 按字面执行；发现歧义或需要放宽验收条件时
  **退回接受角色**，不得自行重新解释。
- 到稳定候选停点必须停：逐条自证 workflow §4.3.1 四项条件（自证写入
  `docs/evidence/` 下该停点证据文件的具名小节，交接行只写其指针），提交候选 commit、更新状态板、写好给复核角色的准确范围，先进入
  接受角色核对轮、核对结束后再交复核角色（COORD-008 S1；COORD-009 用户
  修订），不开始依赖该结果的后续实现。自证时按 BC 编号逐条附证据指针
  （具名测试/工件/命令），并提供完整候选 diff 供接受角色核对轮（workflow
  §4.3.3）；核对轮退回（每停点至多 1 次）按核对表补齐；复核
  `REWORK_REQUIRED` 的修复直接交回复核，不经核对轮（COORD-009）。
- 合同歧义写在提案末尾「待裁定」节，等接受角色答复成 BC 行；不自行
  重新解释（COORD-008 S3）。
- 阻断复核 finding 的修复必须附一条修复前必失败的具名回归测试，
  fixture 由生产路径产出（禁止手工 mkdir/手写 JSON 造状态）；闭合
  条件见 workflow §4.4。
- 完成时记录：关键文件与协议、实际运行的测试/编译命令及结果、未验证项
  与已知限制、复核范围、Unity 用例。全部满足后才可置 `IMPLEMENTED`。
- 证据文件写入 `docs/evidence/`；里程碑证据同步
  `docs/implementation-status.md`。
- 测试输出纪律（COORD-009）：开发期只跑 focused；全套在停点跑一次，输出
  写入 `docs/evidence/` 证据文件，上下文只回显摘要，不带 `-v`。
- 下载额度纪律（COORD-017）：动用下载额度前先固定文件清单与版本；不得用会取回依赖体
  的方式探测或解析（`pip install --dry-run`、`--report`、Range GET 探大小等）；逐个
  完整取回（pip 用 `pip download --no-deps`）并核 sha256 与体积，成功与失败的字节都
  计入额度，再按本地文件离线安装（pip 用 `--no-index`）；已取回并核过的文件优先
  复用；清单外依赖不自动解析补装，将超额或遇清单外依赖即停并回报。

## 工程轨道（`Workflow: engineering-v1`）

经接受角色裁定走工程轨道（提案头 `Workflow: engineering-v1`）的已接受任务
合同按 `docs/engineering-workflow.md` 执行，差异见下。旧 work ID 与研究轨道
仍按上文；提案头没有该行、`Workflow:` 值不在闭集、或接受角色未写明裁定时，
一律按上文旧流程执行并停下问接受角色（fail-closed，不自行推定工程轨道）。
并发与执行轨道纪律两轨相同（用户 2026-09-07 点名维持现状；双路上限 COORD-019，
2026-10-10）：每路（`fast`/`vlm`）1 条消耗性 + 2 条零消耗上限与 Gate-echo 照旧机检。

- 已接受任务合同范围内的小改自行 focused 验证即可推进，相关改动可合并到
  下一个稳定停点，不逐提交过核对轮/复核轮。未经独立复核的中间成果只记
  `IMPLEMENTED`，一律不得记 `DONE`。
- 必须停的只有 K1–K5：帧/控制协议及坐标时间语义、安全约束/控制命令、
  模型决策与目标身份/重播种、数据划分/标签或对外指标、对外发布候选。
  到 K 停点仍按 workflow §4.3.1 逐条自证（写入证据文件具名小节，交接行只写
  其指针），证据指针按 `AC-n` 编号逐条附上，先过接受角色核对轮再交复核；复核 `REWORK_REQUIRED` 的
  修复直接交回复核，不经核对轮。
- 测试：开发期 focused；K 停点跑一次全套，在证据文件中分开记录基线已有
  失败与本批新增失败。阻断 finding 的修复仍须附一条修复前必失败的具名
  回归测试，fixture 由生产路径产出。
  只改具名文件的窄修以 focused 加修前红/修后绿代替全套、不可重跑的消耗步骤前先过
  停点，按 `docs/engineering-workflow.md` §6、§4 执行（COORD-017）。
- 数据工作：新导入、加工或迁移数据时自动核对完整性与来源，并按错误风险
  分层抽查标签；候选未改变时不人工重复全量核验。
- 边界不变：Unity 真值只进 `CoverageEvaluator`；不写 `docs/reviews/`、
  `docs/design-reviews/`；对 `docs/unity-test-log.md`、
  `docs/authorizations.md` 只读；不给自己的实现签发独立复核。
  `docs/engineering-workflow.md` 与其余工作流基础设施（`AGENTS.md`、
  `CLAUDE.md`、`docs/collaboration-workflow.md`、`.claude/`、`.cursor/`、
  `docs/roles/`、`tools/check_*.py`、`tools/githooks/`）对本角色只读，只能
  在用户直接授权的协调批次改（`tools/check_role_writes.py` 的
  `INFRA_PATTERNS` 机检）。

## 边界

- Unity 真值只进 `CoverageEvaluator`，严禁进入控制器、感知输入或对外
  传感器元数据。
- 不写 `docs/reviews/`、`docs/design-reviews/`；不修改提案决策与
  `docs/phase1-single-drone-design.md`（修订走接受角色）。
- 对 `docs/unity-test-log.md` 与 `docs/authorizations.md` 只读：Unity
  反馈由接受/辅助角色代录；实现会话中用户给出的关键授权转交接受/辅助
  角色记入账本。
- 不给自己的实现签发独立复核。

## 收工

1. 基于磁盘最新内容合并更新 `docs/current-status.md`。
2. 运行 `python3 tools/check_role_writes.py --role implementation` 并使其通过。
3. 运行 `python3 tools/check_docs.py` 并使其通过。

## 被 supervisor 拉起时（COORD-015）

被 supervisor 派发拉起时（派发提示带 `Dispatch-Id` 与 `requested.round`，
本角色以 Opus 子代理运行，执行信封须在效），在常规职责与收工自检之外：
- 接力报告随带内结果返回（子代理结果 / `codex exec` 标准输出末段），必填：`work_id`、`this_round`
  （= `requested.round`）、`commits[]`（多于 3 个时写首、末与计数）、`handoff`（交接行的 owner 与
  status token）、`next_owner`、`needs_user`（每条一行，带推荐项与理由）、`consumed`（仅非零维度）、
  `checks`（`check_role_writes` 与 `check_docs` 两项自检通过行）；`claims` 只放指针（`路径#小节`）。
  总长 > 2 KB 时 `claims` 与 `needs_user` 详情改指向本轮已提交的证据/交接文件，必填字段不可省。
- 本批每次提交在尾注带 `Dispatch-Id: <id>` 与 `Role-Check: implementation pass`（提交前自跑两项自检的凭据），
  提交主题以 `<work_id> <this_round>` 开头。
- 追加申请写进报告 `needs_user`，带 `request_id`
  （`<work_id>:<信封标题 sha 前 8 位>:SUB:<n>`，跨重派稳定；COORD-015 §5.1 SUB/§5.6）、
  维度、数量、理由。
- 本轮写 `docs/current-status.md` 中本 work ID 的交接行时，Status 或 Progress 逐字含 `requested.round`
  （事实核查 F3a 的磁盘项；COORD-017）。
- 不代写用户原话的账本条目。
