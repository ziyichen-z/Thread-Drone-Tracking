# P1-ENG-JET-001 阶段B元数据（META-BATCH-1，原批 + 续跑）

轮次：`阶段B元数据续跑`（实现角色，Mac mini，Consuming=no）。合同：同名提案「阶段B元数据授权落实（2026-10-04，CLARIFY）」§2–4 与「阶段B元数据续跑落实（2026-10-04，CLARIFY）」§1–4。机读证据：`docs/evidence/P1-ENG-JET-001-stageb-metadata.json`（由输出目录内 `resume_meta.py report` 生成；实际目录名、原件 sha256、固定 revision/commit 等可派生标识只在该 JSON 内，不抄入本文）。

## 1. 来源与原件保护

- 输出目录：由 `docs/evidence/supervisor-dispatch.jsonl` 中原批 Dispatch-Id `P1-ENG-JET-001-阶段B元数据查询-20261004T065447Z-7720` 的 `finished` 记录定位（JSON 字段 `output_dir_repo_relative`）；本机唯一、复用。
- 原账 `ledger.json` 与 `raw/001–004.body` 只读：续跑前后两次核对 4 条记录、字节数与 sha256 全部一致（JSON `original_ledger_check.problems` 为空）；未改不删。
- 续跑新增：`resume-requests.jsonl`（每请求发出前先写 start 行：编号/URL/对象/开始时刻；完成后写 end 行：状态/字节/哈希）、`raw/005–061.body`、脚本 `resume_meta.py`、`env_check.py` 与执行前 git 记录 `resume_pre_git.txt`。
- 执行方式：全部脚本位于该目录，仅以 `python3 <该目录绝对路径>/<脚本>.py` 运行；会话沙箱未关闭，网络经本机已放行域名；本轮未遇到权限分类器或沙箱拒绝。
- 离线解析器：本机 Python 3.9.6 无独立 `packaging`，使用本机已存在的 `pip._vendor.packaging` 21.0，只作 PEP 440/508 解析（版本、约束、marker、需求串）；未运行 pip 解析器或干跑，未安装任何东西。marker 按目标 Linux/aarch64、CPython 3.12.3 显式环境求值，未用 Mac 平台标记；含 `platform_release`/`platform_version` 的 marker 规定记 UNKNOWN（本批实际为 0 条）。

## 2. 计数（累计 = 原账 4 + 续跑 57）

| 维度 | 已用 | 上限 | 剩余 |
|---|---|---|---|
| HTTP 总请求 | 61 | 86 | 25 |
| META-LLAMA | 2（原账；续跑 0） | 2 | 0 |
| META-GGUF | 4（原账 2 main 页 + 续跑 2 固定页） | 4 | 0 |
| META-DEP（含 META-W） | 55（全部续跑） | 80 | 25 |
| 规范化项目（含 W） | 31 | 40 | 9 |

失败 0、重试 0、重复 URL 0、3xx 0；全部 HTTP 200。asset/文件 URL 只记录未访问；无 HEAD、Range、HF API、raw 源码、内容下载。逐请求账见 JSON `requests`（含 `source` 列区分 `ledger.json` 与 `resume-requests.jsonl`）。

## 3. 已核（字段来源见 JSON 对应对象）

- **META-LLAMA**（只离线解析原账两份原件）：tag `b11381`；固定 commit 由 release JSON `target_commitish` 与 release 页唯一 commit 链接一致得出。release 无主源码类 asset（全部为二进制包/UI/xcframework），归档按合同取自动生成的 `tarball_url`（tar.gz，不选 zip）。release JSON 标记 `prerelease: true`（如实记录，交接受判断是否影响选型）。
- **META-GGUF**：两件 main 页各自唯一 commit 链接为同一完整 revision；随后两件固定 revision blob 页各取 1 次。固定页 revision 字段即该 revision，页面 `SHA256:` 与 Xet hash 和 main 页一致（JSON `main_vs_fixed_sha_xet_consistent: true`）；存储类型为 Xet。
- **META-W**：PyPI 0.11.0 版本 JSON 中唯一匹配 `cp312-cp312-manylinux_2_39_aarch64` 的 `bdist_wheel`；精确 size、sha256、requires_python、yanked、release 级 Requires-Dist 原文均已记录；按合同只激活 `server` extra（`server-tools`/`export`/`tools`/`native-build` 边记为排除，`transformers` 未纳入）。W 不经 PyPI 依赖 `tensorrt`，系统 TRT 复用边 0 条。
- **META-DEP**：从 8 个直接种子与 W 的基础+server 边出发，按项目名字典序遍历：31 个项目全部得到具体版本与唯一选定轮子（固定版本 7 个，区间按「最高稳定且有目标兼容非 yanked 轮子」选 24 个，选择时约束与 UTC 已记；24 个区间项的项目 JSON 与版本 JSON 选中文件一致）；冲突 0、无法静态解释的边 0、被 40 项目上限截断 0。拟 pin 清单见 JSON `META-DEP.proposed_pins_for_acceptance`；选定轮子 size 合计只作事实字段记录，不是下载额度。

## 4. 未核 / UNKNOWN

- llama 归档：文件名、精确字节、sha256 均 UNKNOWN（自动生成归档无 size 字段，`assets[].size` 不适用；按合同未访问归档/codeload/Content-Length）。
- GGUF 两件：页面只给舍入体积（1.11 GB / 819 MB），精确字节 UNKNOWN，未换算。
- 13 个项目的 release 级 Requires-Dist 为 null（JSON `closure.projects_with_null_requires_dist`）：无法静态区分「无依赖」与「元数据缺失」。
- 全部 Requires-Dist 均为 PyPI release 级字段，不是逐轮子 METADATA 复证。

## 5. 闭集结论（仅限完整性）

依赖图在上限内遍历完毕、31 项全部解析且无冲突/未闭边，但因 §4 后两条，**不宣称已核的静态文件闭集**（JSON `closure.static_file_closure_claimable: false`）。本文不给任何下载/安装/传输/磁盘额度，不改运行环境或验收。

## 6. 交接受核清事项

1. 核清来源字段、拟 pin、计次（61/86、31/40）与原件哈希；判断 llama `prerelease: true` 与自动生成归档无精确字节、GGUF 只有舍入体积时可否形成可核申请，或须具名交用户提供事实。
2. 判断 13 个 null Requires-Dist 项与 release 级字段能否满足闭集核清；若须逐轮子 METADATA 复证，属于新的取回维度，须用户另行授权（本批剩余 25 次请求不可挪用于取内容）。
3. 本批剩余 25 次/9 项目不自动使用；是否作废或保留由接受/用户裁定。
