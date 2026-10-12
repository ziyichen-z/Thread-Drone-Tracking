# P1-ENG-JET-001 阶段B核验执行：META-VERIFY（31 件轮子 `.metadata`）

轮次：`阶段B核验执行`（实现角色，Mac mini，Consuming=no）；Dispatch-Id `P1-ENG-JET-001-阶段B核验执行-20261004T151615Z-7f87`。合同：同名提案「阶段B核验授权落实（2026-10-04，CLARIFY）」§2、§4 与 AC-10 修订 21；授权：`docs/authorizations.md` 2026-10-04「用户签 B-METADATA-VERIFY（按推荐）…」(a)(e)。机读证据：`docs/evidence/P1-ENG-JET-001-stageb-metadata-verify.json`（由输出目录内 `meta_verify.py report` 生成；实际目录名、执行前 git 凭据、URL、期望与实际 sha256 只在该 JSON 与目录原件内，不抄入本文）。

## 1. 执行方式与原件

- 输出目录：JSON `output_dir_repo_relative`（`stageb-metadata-verify-<UTC>`，本轮新建）。内含脚本 `meta_verify.py`、执行前 git 凭据 `pre_git.json`、离线计划 `plan.json`、请求账 `requests.jsonl`（每请求发出前先写 start 行并 fsync，完成后写 end 行）、`raw/`（31 份哈希一致的原始 METADATA）、`quarantine/`（空）、离线解析 `analysis.json`。
- 目录以 Write 写入脚本时创建；脚本 `prep` 守卫目录内除脚本外无任何内容才继续，`fetch` 遇已有请求账即拒绝，保证只取一次。
- 只以 `python3 <该目录绝对路径>/meta_verify.py prep|fetch|analyze|report` 运行；会话沙箱未关闭；未遇权限分类器或沙箱拒绝。旧 `stageb-metadata.json/.md` 与旧输出目录只读（`plan.json` 记旧 JSON sha256 与每份版本 JSON 原件的记录/实测 sha、字节）。
- 离线计划（发请求前）：31 件均从旧 JSON `META-DEP.projects` 与 `proposed_pins_for_acceptance` 逐项对上（project/version/filename/size/轮子 sha），按 `version_json_request_n` 定位旧原件并核 sha 与字节，在 `urls[]` 唯一匹配选定文件名，URL 与轮子 sha 与旧记录一致；期望值只取该项 `core-metadata.sha256`。31 个 URL 互异，均为 https、主机 `files.pythonhosted.org`、无账号/端口/查询。发请求前 UNKNOWN 0 件。

## 2. 计数（本项独立计账，不借旧批余额）

| 维度 | 已用 | 上限 |
|---|---|---|
| GET | 31 | 31 |
| 响应正文累计字节 | 433,453 | 32,505,856 |
| 单件最大字节 | 110,178 | 1,048,576 |
| 单请求最长耗时 | 0.211 s | 30 s（看门狗含连接至正文关闭） |
| 跳转 / 重试 / 轮子内容下载 | 0 / 0 / 0 | 0 / 0 / 0 |

31 件全部 HTTP 200、`Accept-Encoding: identity`、正文完整、sha256 与 `core-metadata.sha256` 一致（JSON `objects[].sha256_match`）；未发出 0、在途未闭 0、隔离 0。

## 3. 离线闭集重判（目标 Linux/aarch64、CPython 3.12.3、glibc 2.39）

- 解析：本机 `pip._vendor.packaging` 只作 PEP 440/508 解析，METADATA 头用标准库 `email.parser`；未跑解析器/干跑、未安装。marker 环境取旧 JSON `target.marker_env`；`platform_release/version` 规定 UNKNOWN（本次命中 0）。
- 身份：31 件 Name/Version 与 pin 一致，Requires-Python 对 3.12.3 全部满足，文件标签全部兼容目标（W 为 `cp312-cp312-manylinux_2_39_aarch64`）。
- 图：从旧 JSON 8 个种子与 W 基础+`server` 出发，只在 31 个既定 pin 上遍历：31 件全部可达；新项目 0、版本冲突 0、未提供 extra 0、未知 marker 0、直接 URL 0、系统 TRT 边 0。活跃边集合与旧批 release 级 JSON 算出的完全相同（54/54，排除边 315/315，JSON `closure_rejudge.active_edges_vs_release_json`）。
- 旧批 13 个 release 级 Requires-Dist 为 null 的项目：哈希一致的 METADATA 均无 Requires-Dist（JSON `requires_dist_vs_release_json` 的 `release_json_null__metadata_has_0`），即「无依赖」得到逐文件复证。另 10 件原文逐字相同；8 件文本有差异，经 PEP 508 规范化后一致（引号/空格写法）。
- **未闭（按合同「动态元数据留未闭边」）**：5 件 METADATA 声明与依赖相关的 `Dynamic` 字段——`cuda-python`、`huggingface-hub`（requires-dist/provides-extra，后者另含 requires-python）及 `certifi`、`h11`、`pyyaml`（仅 requires-python）。其 Requires-Dist/Requires-Python 已按哈希一致的轮子 METADATA 原文遍历并核满足，但按合同不据此宣称闭合（JSON `open_edges`）。另有多件只声明 `license-file` 等与依赖无关的 Dynamic，记于 `analysis.json` 各节点 `dynamic_fields_all`，不计未闭。

## 4. 结论边界与交接受核清

- `static_file_closure_claimable: false`，唯一原因是上述 5 件 Dynamic 声明；除此之外未闭边 0。是否把轮子 METADATA 中的 Dynamic 声明视为已静态确定（wheel 内容即安装所用元数据），交 Acceptance 核清裁定；本角色不自行解释。
- needs_user：无（未出现新项目或新增 extra，不需另授权对象）。
- 本项不含任何安装、下载轮子内容、上板、构建或运行许可；结果只交 Acceptance 核清。
