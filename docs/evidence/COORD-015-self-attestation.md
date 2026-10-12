# COORD-015 落地停点自证（C1@落地 退回项修复后，交 C2@落地）

执行者：用户直接指挥的 supervisor 协调批次（2026-09-25），授权 = 账本 2026-09-25「用户授权协调落地：§9.2/§12 落地批次（U1–U9 按缺省；不含 CLI 下载、信封与首次启用）」，本批为其 `C1@落地` 退回项修复，范围不扩大。研究轨道；本文件是实现侧自证，不是独立复核，也不替代接受核对轮。

**候选**：本批提交（主题以 `COORD-015 C1@落地 退回项修复` 开头）。**完整候选 diff**：`git diff bcc2c68..<本批提交>`，即 C1 核对范围 `bcc2c68..c2681ce`，加接受 `9dc2f3d`（正式设计 §1 同步）、构思 `134a241`（提案 §3.2 尾注文本侧），再加本批。

## 本批改动（C1@落地 退回项逐条）

| C1 退回项 | 处置 | 指针 |
|---|---|---|
| BC-1 尾注格式冲突 | 文本侧已由构思 `134a241` 统一为 `Role-Check: <role> pass`；工具侧 `commit_trailers()` 改为输出同一形态，测试改为整串相等断言 | `tools/make_supervisor_drill.py` `commit_trailers()`；test:`tests.test_supervisor_drill` `test_commit_subject_and_trailers` |
| BC-3/A3 证据缺失 | 新增路径核查：§9.3 映射 26/26 pass，§4 九个反例判失败、三个通过例判通过，12/12 pass | cmd:`docs/evidence/COORD-015-route-check.log`（头部命令，脚本全文附于文末） |
| BC-5/6/12 聚焦输出缺失 | 聚焦测试输出入库：Ran 82 OK | cmd:`docs/evidence/COORD-015-focused-tests.log` |
| BC-8 红绿未入库、缺 A8a | A1 红绿原始输出合并入库，并从 git 历史复现到相同计数；A8a 10/10 pass | artifact:`docs/evidence/COORD-015-A1-redgreen.log`；cmd:`docs/evidence/COORD-015-A8a.log` |
| 预复核关注项 `parse_datetime()` | `at:`/`veto_until` 只收 `Z` 或 `+00:00` 后缀，其他偏移、`+0000` 和无时区一律失败关闭 | `tools/check_ledger.py` `parse_datetime()`；test:`tests.test_check_ledger` `StructuralTests.test_non_utc_offset_at_rejected` |
| 预复核关注项 `board_expired()` | Active handoffs 节或表格缺失、Status 列缺失时判为到期（失败关闭），不再判为未到期 | `tools/check_ledger.py` `board_expired()`；test:`tests.test_check_ledger` `BoardExpiredFailClosedTests`（5 例，含真实 pre-commit 路径） |
| 停点自证缺口 | 本文件 | — |

两项 `check_ledger` 修复先写测试再改代码：修复前 7 个失败（3 个偏移子用例，4 个表头缺失用例），修复后 46 例全部通过。红绿摘要附在 `docs/evidence/COORD-015-focused-tests.log` 末尾。真实账本机检 `python3 tools/check_ledger.py` 在修复后仍然通过。

## §4.3.1 四项自证

1. **实现范围和接口已冻结**：已满足。§9.2 闭集文件都已在 `9c8a86b`/`ee8f08b` 落地；此后只有修订 4 的恢复（`c04c8b9`）和 C1 退回项修复。本批只改 `tools/make_supervisor_drill.py` 的 `commit_trailers()` 和 `tools/check_ledger.py` 的 `parse_datetime()`/`board_expired()`，外加对应测试与证据。本批没有新增接口、机读字段或 BC 行。
2. **相称的实现者测试通过**：已满足。聚焦测试 `python3 -m unittest tests.test_check_ledger tests.test_check_role_writes tests.test_supervisor_drill` 为 Ran 82 OK（`docs/evidence/COORD-015-focused-tests.log`）。A1 与本批两项修复都有“修复前必失败”的红绿记录。全套测试 `docs/evidence/COORD-015-tests.log`（本批停点重跑一次）结果为 Ran 1640、`FAILED (failures=1, errors=9, skipped=27)`，失败名单与落地批次（Ran 1634）逐名相同，归因见下节。
3. **已知 Unity 失败**：不适用（`N/A`）。本项是工作流基础设施，不涉及 Unity、Play 或运行时代码（提案 §9.1）。本文件不签发任何 `UNITY_NA` 关闭结论。
4. **复核文件、状态板、候选和未验证风险已更新**：已满足。状态板交接行改为 Acceptance `AWAITING_C2_LANDING`，并写入完整候选 diff 范围；Log 同批新增一条。复核文件留待 `R1@落地` 由复核角色创建，本批不写。未验证风险见最后一节。

## BC-1…13 逐条指针

| BC | 自证 | 指针 |
|---|---|---|
| BC-1 | 单写者、未终结派发与结束凭据的规则由 A5 ②③⑤⑥ 合成演练覆盖。尾注形态现已统一：提案 §3.2/§3.8、角色细则、入口与工具输出都是 `Role-Check: <role> pass`；A3 的 F1 反例在同一形态下判失败 | artifact:`docs/evidence/COORD-015-drill.md` §1②③⑤⑥；test:`tests.test_supervisor_drill`；cmd:`docs/evidence/COORD-015-route-check.log`（反例 6） |
| BC-2 | 候选按 `finished` → `reconciled` 顺序解析；复核提示固定，且不含 claims | artifact:`docs/evidence/COORD-015-drill.md` §1③；cmd:`docs/evidence/COORD-015-route-check.log`（反例 3，F9） |
| BC-3 | 按 F1–F10 适用矩阵核查：九个反例各自只让目标项判失败，其余项判 pass 或 N/A；三个通过例（接受 D1 换角色、实现 `IMPLEMENTING`→`IMPLEMENTED`、构思 `PROPOSED_D3`）的适用项全部 pass | cmd:`docs/evidence/COORD-015-route-check.log` (b)；artifact:`docs/evidence/COORD-015-drill.md` A7 |
| BC-4 | 代拍类闭集、D2a/D2b/D3 默认禁用、永不代拍事项直达用户；信封尚未签发 | artifact:`docs/roles/supervisor.md`「代拍类表」「永不代拍」；artifact:`docs/evidence/COORD-015-drill.md` §1① |
| BC-5 | 按 §5.4/5.5 失败关闭清单、`at:` 全序、撤销与到期规则判定；`at:` 现在只收 UTC | test:`tests.test_check_ledger` `StructuralTests`；cmd:`docs/evidence/COORD-015-focused-tests.log` |
| BC-6 | X 的判定按 §5.6（S 处初态、虚拟提交、提交后等价，含 AD5-1 三例）；表头或 Status 列缺失时失败关闭为 X | test:`tests.test_check_ledger` `PrecommitViewTests`、`BoardExpiredFailClosedTests`；cmd:`docs/evidence/COORD-015-focused-tests.log` |
| BC-7 | 派发守卫：主题提示命中但 X 不存在时停下，不代拍 | artifact:`docs/evidence/COORD-015-drill.md` §1⑤ |
| BC-8 | supervisor 白名单 allow/deny 与 A1 六例（红绿都有）；A8a 表明非本项的 Gate 行、交接行、Log、parked 内容和授权原话零改动 | test:`tests.test_check_role_writes` `SupervisorRoleTests`；artifact:`docs/evidence/COORD-015-A1-redgreen.log`；cmd:`docs/evidence/COORD-015-A8a.log` |
| BC-9 | 六个入口的报告段和尾注经 A4 grep 核对；A6 五子项 pass，附两条约束（`--sandbox danger-full-access`，以及退出码不反映带内成败） | cmd:`docs/evidence/COORD-015-A4-grep.log`；artifact:`docs/evidence/COORD-015-codex-exec.md` |
| BC-10 | A5/A7 只在隔离夹具内进行并标注为合成；未发生真实首签、启用或派发 | artifact:`docs/evidence/COORD-015-drill.md` 开头与 §1；artifact:`docs/authorizations.md`（无信封条目） |
| BC-11 | COORD 节流规则（五天窗口、打包、emergency）已写入细则；A10 待运行期扫描 | artifact:`docs/roles/supervisor.md`「COORD 节流」；A10 未闭（见风险） |
| BC-12 | D1 按严格递减判定，含四类用例；夹具 ① 覆盖递减代拍和持平停下两种情况 | test:`tests.test_check_ledger` `D1Tests`；cmd:`docs/evidence/COORD-015-focused-tests.log`；artifact:`docs/evidence/COORD-015-drill.md` §1① |
| BC-13 | 修订 4 已撤销修订 2/3，恢复 D6 的 Opus/U4=A；BC-13 保留撤销注记 | artifact:`docs/proposals/COORD-015-supervisor-role-record.md`「回应索引」修订 4 行、BC-13；A3 (a) 第 1 行各位置的新句命中 |

## 全套测试 10 项失败的归因

失败都来自环境，与本项无关。它们都不导入 `tools/check_ledger.py`、`tools/check_role_writes.py`、`tools/make_supervisor_drill.py`，也不导入 §9.2 改动过的任何文件。

- **9 个 ERROR（导入失败）**：系统解释器 Python 3.14.6 没有安装 `cv2` 和 `numpy`（本批已复测：`import cv2` 和 `import numpy` 都报 ModuleNotFoundError）。涉及 `test_benchmark_reanchor`（numpy）、`test_detector_scouting`、`test_rate2_protocol`、`test_rate3_difficulty_audit`、`test_rate3_protocol.Rate3GuardTests.test_rate3_reanchor_clock_mismatch_raises_defensively`、`test_rate_study`、`test_scene004_gate0_probe`、`test_scene004_scouting`、`test_scene006_probe`（均为 cv2）。
- **1 个 FAIL**：`test_dist_data_round4.RealArchiveClosureTest.test_zero_unmatched_and_zero_multi_matched_jpg`。主工作树 `runtime/frames/` 下有 257 个已被 gitignore 的诊断帧（例如 `frame_0000000984.jpg`，时间戳 2026-09-23 18:23，来自 LOOP-001 阶段 B Play），归档闭合断言因此数到未匹配帧。一次性复核副本里没有这些残留，这个测试会 skip。
- 与落地批次（`ee8f08b`，Ran 1634）的失败名单逐名相同；Ran 数多出的 6 例就是本批新增的 1 + 5 例。

## 未验证风险

- **没有真实运行**：两类信封都未签发，supervisor 未启用，也从未发生真实派发。A5/A7/A3(b) 全部是合成夹具结果，不能证明真实会话里的接力、回调和凭据取得。
- **A3(b) 的 F 核查是临时实现**：`docs/evidence/COORD-015-route-check.log` 附带的脚本只按 §4 表逐项实现，用来证明规则在反例和通过例上可判、有区分力；仓库里没有随落地提供的 F 核查工具，运行时仍由 supervisor 按细则执行。复核应自行判断这个脚本是否忠实于 §4（例如 F4 只查反引号内的 `docs/` 路径，F5 只查 `Ran N` 形态的数字）。
- **A3(a) 有一处按句级比对**：AGENTS 原 L227「视为 0；任何越界回到用户。」这句逐字保留，但 §9.2 授权的红线句追加在同一物理行的行尾，所以不是整行逐字相同。日志逐字列出了追加内容，由接受或复核判断是否符合 §9.3「不改」。
- **仓库外文件**：`~/.codex/prompts/codex.md` 由用户手动同步，只由 A4 grep 核对，不在候选 diff 内。
- **A6 的两条约束**：`codex exec` 必须用 `--sandbox danger-full-access` 才能提交；退出码不反映带内任务成败。首次启用时要照此执行。
- **A9 与 A10**：A9 是 30 天非门报告，A10 需要运行期授权日期扫描，均未闭。
- **协调批次不跑角色写入检查**（`docs/roles/supervisor.md`，合规凭据是提交信息引用的账本条目）。本批 `check_role_writes --role supervisor` 的结果在提交信息中如实披露。
