# COORD-015 A6 — Codex CLI 装后实测（2026-09-25，协调批次）

授权：账本 2026-09-25「用户授权 Codex CLI 下载/安装与 A6 装后实测（协调批次执行）」
（用户原话「跟我一起玩场CLI和A6的验收」）。范围 = 提案 §12 第 5 步：安装 + A6 实测；
不含信封首签、首次启用、A5/A7。

## 环境事实

- 安装：`npm install -g @openai/codex` → `codex-cli 0.157.0`，`/opt/homebrew/bin/codex`
  （npm 全局前缀 `/opt/homebrew`）。
- 认证：`codex login status` → `Logged in using ChatGPT`，与桌面应用共用
  `~/.codex/auth.json` 与 `config.toml`（`model = "gpt-6-sol"`），未重新登录。
- 夹具：`python3 tools/make_supervisor_drill.py` 生成于
  `/private/var/folders/…/T/supervisor-drill-uwqz2x4x`（临时目录，合成标注，
  不构成任何真实 D/C/R 轮次或门决定），初始终态提交 `0c9ced1`（夹具内）。

## 三次运行（原始输出：`a6-codex-exec-run1.log` / `run2.log` / `neg.log`，本目录）

| 运行 | 命令要点 | 退出码 | 结果 |
|---|---|---|---|
| run1 | `codex exec --sandbox workspace-write -c approval_policy="never"` + 接受入口合成 D1 提示 | 0 | 读夹具、改提案（写入 `Decision: ACCEPTED（合成）` 与 `open_items: none`）、输出接力报告；**git 提交失败**：`无法创建 .git/index.lock：Operation not permitted` |
| run2 | `codex exec --sandbox danger-full-access -c approval_policy="never"` + 提交收尾提示 | 0 | 核对工作区后按指定主题与两行尾注提交，夹具内提交 `564b27f3334a1f25a5798dbe498a46addbdb21ab`，提交后工作区干净，报告字段齐全 |
| neg | `codex exec -m no-such-model-xyz "hi"` | 1 | stderr 报 `invalid_request_error`（模型不支持），非零退出 |

## A6 逐项判定（提案 §10 A6 五子项）

| 子项 | 判定 | 依据 |
|---|---|---|
| 能读夹具仓库 | pass | run1 裁定原文引用提案与 `docs/current-status.md` Gate board 行 |
| 能写 `docs/` | pass | run1 修改 `docs/proposals/DRILL-001-synthetic-drill.md`（diff 见 run1 日志末段） |
| 不弹审批 | pass | 两轮均 `-c approval_policy="never"`，非交互一次跑完、无挂起无审批等待（run1 45 s、run2 31 s 墙钟） |
| 退出码可判 | pass（带约束） | 进程级成败可判：成功 0、失败 1（neg 例）。**约束**：退出码不反映带内任务成败——run1 提交失败仍 exit 0，任务成败须从带内报告/磁盘事实判读 |
| 按提示完成一次合成接受轮 | pass（带配置约束） | 合成 D1 裁定 + `open_items: none` 落盘，接力报告字段齐全；**提交环节仅在 `--sandbox danger-full-access` 下完成**（见下） |

## 关键发现（首次启用与 BC-9 核对必读）

1. **`workspace-write` 沙箱硬阻 `.git` 写**。codex-cli 0.157.0 的
   `sandbox_workspace_write` 配置表只有 `writable_roots` / `network_access` /
   `exclude_tmpdir_env_var` / `exclude_slash_tmp` 四个键（`--strict-config` 拒绝
   `allow_git_writes`：`unknown configuration field`），无放行 `.git` 的选项。
   需要角色自行提交的派发（接受/复核的提交尾注协议）只能用
   `--sandbox danger-full-access`，或改由派发方代为提交（后者是设计变更，不在本批范围）。
2. **退出码 ≠ 任务成败**。`codex exec` 进程正常结束即 exit 0，即使角色报告失败
   （run1：提交失败、报告 `git_commit: failed`，exit 仍为 0）。supervisor 核销不能
   只看退出码，须按提案 §3.4/§3.8 读带内报告与磁盘凭据。
3. 派发调用形态（实测通过）：`codex exec --sandbox danger-full-access -c
   approval_policy="never" "<接受入口提示>"`，cwd = 目标仓库；报告在 stdout 末段。
4. 合成接受轮中 codex 按提示输出了全部必填报告字段（`work_id`/`this_round`/
   `commits[]`/`handoff`/`next_owner`/`needs_user`/`checks`），并在提交前自行核对
   工作区改动范围。

## 结论

按 A6 字面五子项均 pass（提交能力在 `danger-full-access` 配置下验证），本批不触发
`DEGRADED_MANUAL_ACCEPTANCE`；上述 1、2 两条约束须随首次启用生效。BC-9 的正式
符合性裁定归接受角色在首次无人值守拉起前核对，本文件为 A6 实测事实记录。

本批未触碰真实状态板/账本/暂停项之外的内容；夹具内一切结果均为合成。两类信封首签、
首次启用 supervisor、A5/A7 演练仍未授权。
