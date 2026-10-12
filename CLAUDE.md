# TetheredDroneTracking

系留无人机追踪地面车辆的研究项目（Unity 6000.4.1f1 仿真 + Python 外部
控制器）。所有 Claude 角色首先读取 `AGENTS.md`、`docs/current-status.md`
和 `docs/collaboration-workflow.md`；工作项走工程轨道时另读
`docs/engineering-workflow.md`（判据见 AGENTS.md「工作流轨道路由」）。
聊天上下文不是共享事实源。

## 事实源与角色纪律

角色分工为构思/接受/实现/复核（另有无门权限的辅助角色，以及 COORD-015
的 supervisor 调度/事实核查/有界代拍角色），细则与模型池映射见
`docs/roles/` 和 workflow §1.1；历史记录中的 Fable/Codex/
Sonnet 指当时的同名分工，不回改。

- `docs/phase1-single-drone-design.md`：已接受的设计基线（当前 v0.3）。
- `docs/proposals/`：尚未接受的构思。构思角色在此提出方案，不把
  `PROPOSED` 当成正式设计或已完成工作。
- `docs/current-status.md`：所有角色共享的当前状态、责任人、状态门和交接。
- `docs/implementation-status.md`：里程碑证据账本与「范围外已知缺陷」账本
  （`SCOPE_GAP` 记债，COORD-009）；无可复现证据不打勾。
- `docs/reviews/`：复核角色对真实代码的独立复核记录（最强池，档位不得
  低于实现者）。
- `docs/design-reviews/`：M2、M5、投稿前的新鲜上下文设计审查记录。
- `docs/unity-test-log.md`：用户 Unity 实测证据，可由接受/辅助角色代录。
- `docs/authorizations.md`：用户关键授权的逐字账本；账本没有的授权视为
  未发生（2026-07-30 起）。
- `docs/collaboration-workflow.md`：研究轨道（缺省）的完整流程规则。
- `docs/engineering-workflow.md`：工程轨道 `engineering-v1` 的任务合同
  （AC-n 验收项）、K1–K5 必经停点与复核收敛规则。

流程是双轨的，**缺省仍走旧流程**：只有提案抬头逐字写 `Workflow: engineering-v1`
的工程提案及其派生 work item 走 `docs/engineering-workflow.md`，其余一律走
`docs/collaboration-workflow.md`。判据、回落范围、两轨共同红线（并发上限与
Gate-echo、角色写权限、`DONE` 三证据、授权信封来源、`CLOSED_*` 语义）以
AGENTS.md「工作流轨道路由」一节为准，本文件不复述。

接受角色可以在用户已确定的 Phase 1 范围和 v0.3 基线内审查提案，实现
角色落实代码；若提案会改变核心研究主张、阶段边界、主指标、硬件目标或
显著扩大范围，必须先由用户确认。实现者不能给自己的代码签发独立复核
通过；复核角色只在一次性 worktree 接触实现代码，发现缺陷只写复核文件，
一行也不许修。每个角色收工提交前运行
`python3 tools/check_role_writes.py --role <role>` 核对写入白名单。

运行时功能的 `IMPLEMENTED` 不等于 `DONE`；只有实现者证据、独立复核和
用户 Unity 验证都满足验收条件后才可关闭。
M2、M5 和投稿前还必须由非提案作者、非主要接受/实现者完成新鲜上下文设计
审查，专门检查指标天花板、信息公平和实验归因。

## 工程约定

- Unity 工程：不要随意手工编辑 `*.meta`；`Library/`、`Temp/`、`Logs/`、
  `UserSettings/` 是生成物，不纳入版本控制。
- 场景默认配置是 `config/scenario.default.json`，运行时可被
  `runtime/scenario_config.json` 覆盖。
- 文件桥全部位于 `runtime/`：帧包 `frames/latest.json`（两个成员文件落盘
  后原子发布）、`tracking_observation.json`（按 `frame_id` 绑定）、
  `body_command.json`、`gimbal_command.json`、`metrics.json`。
- Python 测试（COORD-009 测试输出纪律）：开发期只跑 focused，例如
  `python3 -m unittest tests.test_<模块>`；停点全套跑一次并写文件、只回显摘要：
  `python3 -m unittest discover -s tests > docs/evidence/<work-id>-tests.log 2>&1; tail -n 3 docs/evidence/<work-id>-tests.log`；
  不带 `-v`。核对轮不跑测试。
- Unity 真值只允许进入 `CoverageEvaluator`，严禁进入控制器、感知输入或
  对外传感器元数据。
- 只修改当前工作 ID 的范围；发现需要扩大范围时先更新交接并请求对应决策。

## 沟通

- 用户使用中文交流。
- 状态必须如实：失败附结果，跳过明确写出，环境阻塞不伪装成实现缺陷。
- 开工与交付前都重新读取磁盘上的 `docs/current-status.md`，不得用旧对话
  整文件覆盖其他角色的新内容。
