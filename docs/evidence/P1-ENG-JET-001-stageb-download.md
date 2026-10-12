# P1-ENG-JET-001 阶段B下载执行证据（机器生成）

由 `outputs/eng-jet/P1-ENG-JET-001/stageb-download-20261004T170131Z/dl.py report` 生成；机读详情见 `docs/evidence/P1-ENG-JET-001-stageb-download.json`。

- 轮次：`阶段B下载执行`；Dispatch-Id：`P1-ENG-JET-001-阶段B下载执行-20261004T165837Z-54e5`
- 合同：docs/proposals/P1-ENG-JET-001-jetson-onboard-feasibility-probe.md#阶段B下载授权落实（2026-10-04，CLARIFY） §1-4; AC-10 修订 24; AC-11 修订 3
- 批次目录：`outputs/eng-jet/P1-ENG-JET-001/stageb-download-20261004T170131Z`（请求账 `requests.jsonl`、计划 `plan.json`、调用 `invocations.jsonl`，均为本地 gitignored）
- 执行前 HEAD/状态：见 JSON `git_pre`

## 数字摘要

| 项 | 用量 | 上限 |
|---|---|---|
| 下载件（成功/尝试） | 31 / 33 | 33 |
| 字节（全部已读正文） | 516,980,330 | 2,443,785,130 |
| 其中轮子 / GGUF | 516,980,330 / 0 | 516,980,330 / 1,926,804,800 |
| HTTP GET（发起） | 33（轮子 31 / GGUF 初始 2 / 单跳 0） | 35（31/2/2） |
| 墙钟（自建目录起，报告时） | 195.6 s | 3,600 s |
| 本批目录占用（报告时，逻辑/分配） | 517,145,247 / 524,570,624 B | 10,000,000,000 B（含证据，见 JSON disk） |
| 重试 / HEAD·Range·补查 / 源码新增 | 0 / 0 / 0 | 0 / 0 / 0 |

## 失败、未执行与未知

- `Qwen3VL-2B-Instruct-Q4_K_M.gguf`：{"verdict": "FAILED", "reason": "Location host 'us.aws.cdn.hf.co' not an allowed candidate (or has port/userinfo)"}
- `mmproj-Qwen3VL-2B-Instruct-F16.gguf`：{"verdict": "FAILED", "reason": "Location host 'us.aws.cdn.hf.co' not an allowed candidate (or has port/userinfo)"}

停止原因：无（全部对象按序完成）

两件 GGUF 的初始 `/resolve/` 请求均为 302、Location 唯一，但目标主机是 `us.aws.cdn.hf.co`，不在合同 §2 的四个候选主机内，按合同停该对象：未访问目标、未读正文（GGUF 正文 0 B），未发第二个请求，无 `.part`/隔离件。302 响应头 `X-Repo-Commit` 等于固定 revision，`X-Linked-Size` 分别等于两件期望字节，`X-Xet-Hash` 等于页面 xet hash（只是响应头事实，不是内容 sha，不代替下载核验）。完整签名 Location 只留在本地请求账，JSON 中只记主机/路径/参数名与整串 sha256。两件各 1/1 次尝试已用完，重试 0；未用额度（GGUF 1,926,804,800 B、单跳 GET 2）不转给新对象。

## needs_user（交接受核清后转用户）

- GGUF 两件是否另行取回：推荐 (a) 由用户本人把精确主机 `us.aws.cdn.hf.co` 加入本机沙箱放行（不加通配符），并另签两件 GGUF 各 1 次新尝试（≤ 1,926,804,800 B、GET ≤ 4、重试 0），由接受角色把该主机追加进合同候选主机闭集后再派实现。理由：本次实际跳转目标已由响应头给出，候选闭集是凭知识列的、未覆盖该主机；现有尝试额度已按合同用尽，不能自行补取。

## 主张上限

byte count and content sha256 match the fixed identities for the OK objects only; nothing about install/compatibility/board behaviour；downloads kept only in this output dir (gitignored); not unpacked/installed/copied into repo/transferred to board; no cloud。
