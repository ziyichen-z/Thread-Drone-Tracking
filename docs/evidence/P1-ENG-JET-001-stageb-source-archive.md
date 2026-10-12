# P1-ENG-JET-001 阶段B核验执行：SRC-ARCHIVE（llama.cpp b11381 源码归档）

轮次：`阶段B核验执行`（实现角色，Mac mini，Consuming=no）；Dispatch-Id `P1-ENG-JET-001-阶段B核验执行-20261004T151615Z-7f87`。合同：同名提案「阶段B核验授权落实（2026-10-04，CLARIFY）」§3、§4 与 AC-10 修订 22；授权：`docs/authorizations.md` 2026-10-04「用户签 B-METADATA-VERIFY（按推荐）并授权在 Mac mini 下载 1 次 llama.cpp b11381 源码归档…」(b)(e)。机读证据：`docs/evidence/P1-ENG-JET-001-stageb-source-archive.json`（由输出目录内 `src_archive.py report` 生成；fixed commit、请求 URL、Location、实际字节与 sha256、目录名只在该 JSON 与目录原件内，不抄入本文）。本项在 META-VERIFY 完成后串行执行。

## 1. 绑定链（离线，发请求前）

- fixed commit 从旧 `stageb-metadata.json` 的 `META-LLAMA.fixed_commit` 运行时读取，并与两份只读原件交叉一致：release JSON 原件的 `target_commitish`、release 页原件中唯一的 commit 链接（两份原件的记录/实测 sha 与字节一致，见 JSON `binding_chain.originals`）。
- 实际请求为 API `tarball/<fixed_commit>`；tag 形式 URL 只记录、未请求（JSON `tag_tarball_url_not_requested`）。允许的 Location 只有同 commit 的 codeload `legacy.tar.gz` / `tar.gz` 两种精确形式。

## 2. 执行与计数

| 维度 | 已用 | 上限 |
|---|---|---|
| 下载尝试 | 1（首 GET 前登记） | 1 |
| HTTP GET | 2（API 1 + codeload 1） | 2 |
| 全部响应正文字节 | 等于归档字节（302 正文 0 B） | 500,000,000 |
| 重试 / 额外跳转 | 0 / 0 | 0 / 0 |

- GET 1：HTTP 302，未自动跟随；Location 与合同允许的 `legacy.tar.gz/<fixed_commit>` 逐字一致、无查询/端口/账号（JSON `binding_chain.redirect.location_matches_contract: true`）。
- GET 2：仅访问该 Location 一次，HTTP 200、无再跳转、`Content-Encoding` 未出现（identity）、分块传输正常结束，流式写入 `.part`；完整后核 gzip 魔数并原子改名为 `archive.tar.gz`。
- 实际完整字节与 sha256：见 JSON `archive.bytes` / `archive.sha256`（流式 sha 与落盘复算一致，`streamed_sha256_equals_file_sha256: true`）。
- 只以 `python3 <该目录绝对路径>/src_archive.py prep|fetch|report` 运行；会话沙箱未关闭；未遇权限分类器或沙箱拒绝。

## 3. 读数边界

- sha256 绑定的是「GitHub 对已核 fixed commit 在本次请求返回的归档」；未从归档内部独立验 commit，不是远端公布的校验和；自动生成归档的字节可能随时间变化，只能复用本次保留的同 sha 副本，不声称任何 b11381 归档都同 sha。release 的 `prerelease: true` 标记照旧只记录，不认证兼容或性能。
- 未解压、未列 tar、未构建、未传板、未复制进仓库/数据根/云；归档只保留在本次输出目录。
- 未捕获：`Content-Disposition`（脚本头部白名单按大小写精确匹配，本次记录的响应头中没有该键；是缺失还是大小写不同为 UNKNOWN）。合同只把它当辅助字段，不影响字节/sha 读数；ETag 等其余头部原样记于 JSON `requests[].headers`。
- 后续预算与引用只从本次原件运行时取；删除该归档后若需重取须另授权。交 Acceptance 核清。
