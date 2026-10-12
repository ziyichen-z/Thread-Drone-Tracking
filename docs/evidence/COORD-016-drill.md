# COORD-016 A4 夹具演练证据（2026-09-26，协调落地批次）

**合成演练，不构成任何真实 D/C/R 轮次、代拍或门决定。** 夹具内的信封、代拍条目、接受裁定、复核 verdict 与
「回用户」都是合成的；未签任何真实信封、未触碰真实账本、状态板、`P1-*` 提案或暂停项。

授权：账本 2026-09-26「COORD-016 — 用户授权零消耗协调落地批次：按提案 §3–4 与 BC-1…6 执行；U1=A…U3=A…U4=B…」。
执行：supervisor 委托的协调批次子代理（Claude Code，Opus 5.5），零消耗。

## 0. 环境与方法

- 夹具：`python3 tools/make_supervisor_drill.py --dest <scratchpad>/drill16`（会话临时目录，初始提交 `b8bb371`；
  夹具提案已含本批新增的 `d7_range:`/`d7_recommend:` 样例行）。演练结束时夹具 HEAD `109a748`，共 17 个提交。
  以下短 SHA 均为**夹具仓库**内的提交，不在本仓库。
- 驱动脚本在会话临时目录（未入库）：按段写合成提案/复核文件/账本条目，每条代拍条目暂存后运行
  `python3 tools/check_ledger.py --root <夹具>`（本批工作树版本，即 pre-commit 视图）；exit 0 才提交，提交后再跑一次
  （历史复判视图）；exit ≠ 0 即撤回条目、不提交，记「停下交用户」。
- 代拍条目 `precheck_head` 取当时夹具 HEAD；D 类均带 `veto_until`。D2b 开轮资格按 workflow §4.4 的 PLAY_GOVERNING 定义
  （`controller/`、`Assets/`、`tools/`、`tests/`、`config/`、`ProjectSettings/`、`Packages/packages-lock.json`）对
  `git diff --name-only <上一通过候选>..<返工候选>` 取交集。
- 信封：① 用夹具自带决策信封 `classes: [D1, D4, D5, D6]`；②–④ 先合成「用户新签」决策信封 `classes: [D2b, D7]`
  （BC-4：D2b 须新签且含 `D2b` 的信封；§2.2：D7 须信封逐字含 `D7`）。

## 1. 逐段结果

### ① D1：持平残留代拍通过，第 4 次停下（A1/BC-1）

- 夹具提案补 `### D3`–`### D5` 节，`inject_open_items(PROP, ["AR-1","AR-2"], n)` 对 n = 1…5 各插入一行（本批修复后按
  `### D<n>` 节末插入，COORD-015 R2-1），r(1…5) = 2（持平）。
- D2、D3、D4 三轮各一条 D1 代拍（`open_items_now: 2`、`open_items_prev: 2`）：`check_ledger` 预提交视图 exit 0，
  分别提交 `82b1c37`、`82cabb4`、`945d6a5`，每次提交后复判 exit 0。**pass**（修前规则「严格递减」会拒绝持平）
- D5 第 4 条（r 仍持平）：exit 1，「D1 代拍超每提案累计上限 3（DRILL-001 第 4 条）」→ 撤回、停下交用户。**pass**

### ② D7：一题按推荐入账，一题值出区间停下（A2/BC-2/BC-3）

- 合成接受提交把夹具提案 `Status:` 改为 `ACCEPTED`，BC-1 条款格 `d7_range: gate1 in [0.50, 0.80] kind=门值 bc=BC-1`，
  新增 BC-3 条款格 `d7_range: tol1 in [0.05, 0.10] kind=容差 bc=BC-3`；「待裁定」节（非 `### D<n>`）写
  `d7_recommend: gate1 = 0.70`、`d7_recommend: tol1 = 0.20`。该提交先于代拍条目（同源已提交快照）。
- gate1：条目 `decision: 0.70`、`range` 逐字复制片段、`counter_key: DRILL-001:D7:gate1` → exit 0，提交 `914bb41`，
  提交后复判 exit 0。**pass**
- tol1：0.20 ∉ [0.05, 0.10] → exit 1，「D7 推荐值出区间（0.20 ∉ [0.05, 0.10]）」→ 撤回、停下交用户。**pass**

### ③ D2b 路径 (i)：有资格开 R4 通过（BC-4）

- 停点 K4：上一通过候选 `921e979`；合成复核文件 R1、R2@K4 `REWORK_REQUIRED`（冻结集 {F1, F2}）、R3@K4 未通过
  （轮 3 终局，D2b 在效 → 回 supervisor）。
- D2b 条目（`counter_key: DRILL-001:K4:D2b`，定向返工限冻结集 F2）→ exit 0，提交 `98057eb`，复判 exit 0。**pass**
- 返工候选 `e1f0b84` 改 `controller/drill_stub.py`：`git diff --name-only 921e979..e1f0b84` ∩ PLAY_GOVERNING =
  `[controller/drill_stub.py]` 非空 → 有资格，开 R4@K4；R4 写 `round_candidate`/`passed_candidate` = `e1f0b84`
  （≠ 复核提交自身），verdict PASS（轮 4 终局：通过）。**pass**
- 同停点第 2 次 D2b 申请 → exit 1，「counter_key 超该类次数上限（DRILL-001:K4:D2b 重复）」→ 回用户。**pass**

### ④ D2b 路径 (ii)：无资格走回归通道，一条 finding 未闭 → 回用户（BC-4）

- 停点 K3：上一通过候选 `07a44d7`；R1、R2@K3 `REWORK_REQUIRED`（冻结集 {F3, F4}）、R3@K3 未通过。
- D2b 条目（`counter_key: DRILL-001:K3:D2b`）→ exit 0，提交 `e6c8273`，复判 exit 0。**pass**
- 返工候选 `81589d3` 只改 `docs/DRILL-001-ops.md`：∩ PLAY_GOVERNING = `[]` → 无资格，不开 R4、不新编轮号；复核在同一
  复核文件写「回归核实（R3@K3 冻结集，D2b 路径 (ii)）」小节：F3 修前红/修后绿闭合，F4 修后仍红未闭 → 终局
  `REWORK_REQUIRED`，不写 `passed_candidate`（K3 段 `passed_candidate` 0 行、`## R4@K3` 0 节）→ 回用户终局。**pass**
- 终局后再申请 D2b → exit 1，「counter_key 超该类次数上限（DRILL-001:K3:D2b 重复）」→ 不可再代拍。**pass**

**四段适用项全 pass。** D2b 的开轮资格与回归核实判定目前无专用机检（`check_ledger` 只管条目结构、信封类与计数键），
本演练以 `git diff --name-only` 交集与复核文件小节计数演示判定过程。
