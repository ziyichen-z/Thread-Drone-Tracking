# P1-ENG-LOOP-001 — C5@K1K2K3 退回后的修复候选，交 C6@K1K2K3

Owner：实现角色（Claude Code `/implement`），2026-09-23。
输入：提案「Contract conformance」C5@K1K2K3 首次退回（AC-13 修订2 不满足：窗口末帧延迟可漏算、坏日志被静默跳过）及预复核关注
C5-1…3；状态板交接行「按提案 Contract conformance C5 修 … 补具名反证；整理稳定候选与自证后交 C6@K1K2K3」。
零消耗：零 Play、零模型/5060 服务、零 ID、零下载、零传输；未写真实 `runtime/`。本文件是实现者自证，不是独立复核结论。

## 1. 候选与复核范围

- 本候选 = 首次加入本文件的提交，运行时解析：`git log -1 --diff-filter=A --format=%H -- docs/evidence/P1-ENG-LOOP-001-K1K2K3-c5-fix.md`。
- C5 所核对候选 = 首次加入 `docs/evidence/P1-ENG-LOOP-001-K1K2K3-handoff.md` 的提交。本批修复触及：`git diff <C5 所核对候选> <本候选>`；
  其间另有接受角色 C5 核对提交（只改提案、状态板、implementation-status）。完整候选 diff 仍以复核文件最后一条 `passed_candidate`（R6）为基线。
- 触及文件：`docs/evidence/P1-ENG-LOOP-001-lap-samples.py`、`-frame-keeper.py`、`-operations-c.md`（§5 冻结取样规则同步）、
  `-c2-carrier-selftest.py`（具名反证 6 项）；新证据：本文件、`-k1k2k3-c5-fix-selftest.log`、`-tests-k1k2k3-c5-fix.log`；状态板。
- 零改动（机检见 `-k1k2k3-c5-fix-selftest.log` §1）：`controller/`、`tests/`、`tools/`、`config/`、`Assets/`、`ProjectSettings/`、
  `Packages/`、watch、operator.sh、清单脚本、5060 runner、操作页。

## 2. 退回事项的修复

1. **窗口末帧延迟不再漏算**（`-lap-samples.py` `analyse`）：窗口归属不再用源帧采集墙钟。带帧号的收据按该帧仿真时刻是否落在
   [t0, t0 + 106.5 s]；不带帧号的记录（状态、退役、安全 hold、无关联拒收、意外段终止）从 t0 观测收据起，到**第一次只处理窗口之后帧**
   的 `frames_processed` 为止都算窗口内；找不到这样一次处理即 `window_not_fully_processed`，其后记录全部计入（fail-closed）。
2. **必需日志 fail-closed**：发布收据、会话日志、保存帧索引、段运行日志四个文件缺失 → `missing_log:<文件>`；任一行不可解析或
   不是对象 → `corrupt_log:<文件>:line<n>`；索引重复帧号 → `corrupt_log:…duplicate_frame_<n>`。都进入机械失败，不跳过。

## 3. 预复核关注 C5-1…3 的处理（实现取保守读法，未扩 AC；请 C6/R7 核对）

- **C5-1「对应观测」**：取样帧必须有**自己**的该段 `WRITTEN` 观测收据，否则 `NO_WRITTEN_OBSERVATION`；仍只取最近保存帧，不换帧。
  代价核实：诊断 5 首批追平之后 350 帧只有紧随首批的 1 帧没有写出观测，严格读法几乎不影响通过率。
- **C5-2 ≤220 s 观察窗**：窗口末 t0 + 106.5 s 须 ≤ 220 s 仿真时间，否则 `lap_window_beyond_220s`；操作单 §5 第 1 步改为用第 1 入画窗
  （t0 ≤ 113.5 s）。此处把「观察窗 ≤220 s」读作以 Play 起点计的仿真时间；若接受角色另有起点，请裁定。
- **C5-3 帧包身份**：保存侧每帧复制后回读核对 sha256，不符即删除并记 `copy_verify_failed` 缺口；取样侧逐帧核对保存 JPEG 与索引行、
  并与该观测收据里跟踪器加载时的 `snapshot_sha256` 三者一致，否则 `KEPT_FRAME_IDENTITY_MISMATCH`——证明取样图就是跟踪器处理过的那一帧字节。

## 4. 具名反证与证据

| 检查名（逐字，`-c2-carrier-selftest.py`） | 对应 | 修前（C5 所核对候选的载体） |
|---|---|---|
| `lap: a rejection raised while the last window frame is processed late is still counted (C5)` | 退回 1；夹具经生产路径：真实 `LanguageSession` + 冻结规划器，窗口末帧晚处理、其发布门判 `publish_expired` | 红（探针：旧脚本判 `OK []`，§4） |
| `lap: a corrupt or missing required log fails closed (C5 fail-closed)` | 退回 2（会话日志末行半截写入；缺发布收据文件） | 红 |
| `lap: a sample frame without its own WRITTEN observation is NO_WRITTEN_OBSERVATION (C5-1)` | C5-1 | 红 |
| `lap: a lap window ending after the 220 s observation window is rejected (C5-2)` | C5-2（夹具仿真时钟从 120 s 起） | 红 |
| `lap: a kept frame that is not the tracker's load snapshot is KEPT_FRAME_IDENTITY_MISMATCH (C5-3)` | C5-3 取样侧 | 红 |
| `keeper: a copy that does not read back byte for byte is removed and recorded as a gap (C5-3)` | C5-3 保存侧 | 红 |

- 修后：`.venv-loop-client` 载体自测 117/117；系统 python3 116 ok + 1 行显式 skip（无 Pillow 的渲染项）（`-k1k2k3-c5-fix-selftest.log` §2）。
- 修前：同一自测指向 C5 所核对候选的 lap 脚本红 6 项、keeper 红 1 项（§3）；正向运行项在旧脚本上也红，仅因旧报告没有新增的哈希字段。
- 探针（§4）：窗口末帧晚处理并被门拒收的真实会话，旧脚本 `OK []`，修后 `FAIL`（五条原因）。
- 故障注入说明：坏日志、错图两项在通过会话输出的**副本**上人为制造（截断末行、换 JPEG 与索引哈希），用来模拟崩溃写入与复制出错；
  其余夹具均由生产写者产出。
- 停点全套（隔离副本，系统 python3）：`Ran 1534`、failures 0、9 个 `ERROR:` 与 `-tests-k1k2k3.log` 逐名相同、skip 清单相同 →
  新增失败 0（`-tests-k1k2k3-c5-fix.log`；本批未改被测树，日志首行列树哈希）。

## 5. workflow §4.3.1 四项自证

1. **范围冻结**：只动 C5 点名的取样判定与保全载体、操作单 §5 同步文字（§1）；合同、运行时、规划器、协议零改动。
2. **相称测试**：六项具名反证修前红/修后绿（§4），全套新增失败 0。
3. **已知 Unity 失败**：无；真实 Play 仍待 C6/R7 通过后的获准诊断与正式运行。
4. **状态板、候选提交、复核范围**：交接行转接受角色 C6@K1K2K3，只写本文件指针；K1K2K3 其余自证与 AC 指针沿用
   `-K1K2K3-handoff.md` §2…§6（运行时部分未变）。C6 后照交新鲜上下文 R7@K1K2K3。

## 6. 未验证项与已知限制

- 「观察窗 ≤220 s」的起点按 Play 起点的仿真时间实现（§3），第 1 入画窗较短（约 0–12 s），操作者须在这段内完成指定与确认；
  只能在诊断 6 中实际演练。
- 故障注入副本之外，末帧晚处理的其他失败形态（例如身份更换发生在窗口末帧）走同一归属规则，未逐一另写用例。
