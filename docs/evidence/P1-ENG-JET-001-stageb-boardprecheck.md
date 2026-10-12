# P1-ENG-JET-001 阶段B板端预检（一次只读 board 预检）

- 登记轮次：`阶段B板端预检`；Dispatch-Id `P1-ENG-JET-001-阶段B板端预检-20261004T062706Z-5aef`；Implementation（Opus 子代理）。
- 授权：`docs/authorizations.md`「2026-10-04 P1-ENG-JET-001 — 用户答复「阶段B准备审核」§5：选择类全部按推荐、授权一次只读预检，推进至云量化之前（不含云；supervisor 会话代录）」第 (1) 项。
- 执行合同：同名提案「阶段B预检答复落实（2026-10-04，CLARIFY）」§2–3；唯一发令：同名提案「阶段B补写核清（2026-10-04，CLARIFY）」§3 代码块 `python3 -I -S -B - board` 版本（逐字取出，不改参数）。

## 1. 执行前记录

- 状态：**已开始，1/1**（本节写于启动前；从首次启动完整 board 块即计 1，无论结果不再执行）。
- 执行机器：Mac mini（`zc5s-Mac-mini.local`），主树根 `~/TetheredDroneTracking`；本机 `python3` = `/usr/bin/python3`（3.9.6）。
- 共享槽位：执行前只读核对，本机无 Unity/控制器/采集进程、无既有到板 SSH 进程；`runtime/` 只有 `README.md`；`P1-ENG-FRAME-001` 交接为 `WAITING_FOR_USER_READY`（尚未 Play），槽位空闲，无需等待。
- 执行时 git 状态凭据（写本文件之前）：`git rev-parse HEAD` = `0e6a6709d0bfa714080bcf15a919b23cc23fd4ef`；`git status --porcelain` 输出为空。
- 唯一命令取出方式：从提案该节 ```` ```sh ```` 代码块按行原样抽出（122 行，sha256 `95c1fb47e4d23275340758dcb987d4635171fae64228f8f679a0210615f133fb`），在主树根以 `/bin/sh` 执行该文本；执行前仅做 Python 语法编译检查（未运行）。目标主机由该块在运行时从 `docs/evidence/P1-ENG-JET-001-relay.json` 解析。

## 2. 执行结果

- 状态：**已执行，1/1；重试 0**。不再执行；后续缺读数只记 UNKNOWN，交接受核清。
- 执行方式：本会话一次 Bash 调用，在主树根以 `/bin/sh` 运行上述抽出文本（为免本机工具沙箱拦截到板网络，该次调用关闭了会话沙箱；未改 SSH 键/配置，未追加任何其他登录或探测命令）。
- 开始/结束（块内记录，UTC）：`started_utc` 2026-10-04T06:29:21.29Z，`ended_utc` 2026-10-04T06:29:22.33Z，`elapsed_s` ≈ 1.05 s（≤ 300 s 全程上限）；外层 shell 墙钟 06:29:21Z–06:29:22Z。
- 原始输出目录指针（Mac mini 本机，`/outputs/eng-jet/` 被 `.gitignore` 排除、不入库）：`outputs/eng-jet/P1-ENG-JET-001/stageb-boardprecheck-<UTC>/`，本次实际（唯一一个）：`outputs/eng-jet/P1-ENG-JET-001/stageb-boardprecheck-20261004T062921Z/`（只记于本证据，不抄入合同）。文件：`started_utc`、`ended_utc`、`elapsed_s`、`precheck.stdout`（6182 B）、`precheck.stderr`（0 B）、`precheck.rc`；无 `local-error.txt`。各文件 sha256：
  - `precheck.stdout` `8c58fe4f9274faccad8ddf798779b37a77a22018a2d831696294f7af1f0d0ef1`
  - `precheck.stderr` `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
  - `precheck.rc` `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865`
  - `started_utc` `62e43df3ca2bb375702caa56f132d165d4a80c43761e06f992d8d268dbb03f62`
  - `ended_utc` `d57fd403ea33acb7884bba5f6d330bb3fa9477765bd90442437e035d9fc94f13`
  - `elapsed_s` `2ddef61f976ac35fccf695b9812f1ab024c3dc1227ac719e140e7114397815f9`
- 返回码：`precheck.rc` = 1，外层 shell rc = 1；无本机异常、无超时（未出现 rc 124/137）；SSH 已连上并跑完至 `### end`。整体 rc=1 来自下列单项非 0（块内 `missing=1`），不是连接失败。
- 逐项 rc（块内顺序，共 26 项 + `### end`；读数原文只在上述原始输出，不抄入本文件或合同）：

| 项 | rc | 标记 |
|---|---|---|
| user / os / l4t / glibc | 0 | — |
| tools | 0 | 块内字段 `cmake: MISSING`、`ninja: MISSING` → 按合同逐字段记 UNKNOWN（tools 项 rc=0 不代表完整） |
| cmake_v | 127 | `UNKNOWN=cmake_v` |
| gcc_v / gxx_v / nvcc_v | 0 | — |
| dpkg | 1 | `UNKNOWN=dpkg`（stdout 有三条 `no packages found` 行，其余包行有输出） |
| trt_headers | 0 | — |
| cuda_dirs | 2 | `UNKNOWN=cuda_dirs`（三路径之一不可访问） |
| sys_py_pkgs / sysvenv_cfg | 0 | — |
| sysvenv_numpy | 2 | `UNKNOWN=sysvenv_numpy` |
| py_sys / py_venv / nproc / mem / swap / df / du / addr / route4 / route6 | 0 | `swap` 项 rc=0 但无输出行，由接受按原文核 |

- 未执行项：无（单项超时 0）。
- 不下结论：本证据不对读数下 PASS、兼容性或性能结论，不做闭集推断，不由路径存在推断 import/运行兼容；“不需要”与“必需但缺失”的区分、U1/U2/工具链/glibc/系统 TRT 绑定/RAM/swap/盘/路由的核清，按提案「阶段B预检答复落实」§3 交 Acceptance。
- 边界核对：未下载/安装/sudo/交互；未加载模型、未构建、未传输资产、未回放、未跑 SR/测试；未租云；未改代码/配置/测试/工具、SSH 键或配置；主树 `runtime/` 与数据根零写入（本机写入仅上述原始输出目录与本证据文件）；板端附带写入（SSH/PAM/登录日志等）按合同已获用户接受。
- consumed：board 只读预检 1/1，块内实测约 1.05 s。其余维度 0。
