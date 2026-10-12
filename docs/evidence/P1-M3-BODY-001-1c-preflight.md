# P1-M3-BODY-001 1c 操作单（revision 29，臂 B 5/5 —— 十次采集全部完成）

**revision 29（2026-08-21，接受轮 74）**：B5 已判为**有效 trial**，**臂 B 收于 5/5，本批次
十次采集全部执行完毕**。本修订新增 **§2.25**（B5 的 post-run 归档合同）并把 §2.24 转历史。
**槽位不轮换**（`…-arm-b-trial-5` 已消耗，此后无下一 trial），**§4 CLI 一行不动**，
零指标、零阈值、零冻结值、零 disposition 改动。

- **A. §2.25 仍须先做**：shared 槽位此刻装着 B5 的产物。**「最后一次采集」不使 B3 的教训
  失效**——一次误入的 Play 照样会当场覆盖 truth 与 metrics。钉住值由本角色**移动前实测、
  全 64 位落表**。**归档执行前不得进入任何 Play。**
- **B. 落盘地在此改变**：前几轮的归档都落在「下一 trial 的证据文件」（§2.19 先例），
  但**本轮没有下一 trial**，故 §2.25 落盘于 B5 自己的 `…-arm-b-trial-5.md` §D。
  该先例在此自然终止，**已逐字写明以免下一个接手的角色照抄**。
- **C. `--compare` 仍无 GO，且不因十次齐备而自动获得**：2026-08-14 批量 GO **明确不覆盖**
  它（原文「不覆盖 `--compare`（需十次齐备并单独授权）」）。十次齐备只是**必要条件之一**
  达成，**不是授权**。接受角色已就此单独请示用户；**在用户逐字授权并由接受角色落账、
  起草比较合同之前，任何角色不得启动 `--compare`**。
- **D. 其余条款逐字不变**：§2.0 四步、门 1/2/3/4、握手、BC-BODY1-21/-22/-29/-30、
  §5 四种 void 终态、§2.21 七处保全 hold 与 §2.23 的归档结果。**§3 的采集步骤自本修订起
  不再有下一次执行对象**（十次已满）。

## 历史抬头：P1-M3-BODY-001 1c 操作单（revision 28，臂 B trial 5 —— 本批次最后一次采集）

**revision 28（2026-08-21，接受轮 73）**：轮换到 **`p1-m3-body-001-arm-b-trial-5`** 并新增
**§2.24**（B5 的 Play 前核对，**十一项**）。§2.23 转历史。**同臂轮换，§4 CLI 恰 1 行不同**
（`--run-id`；`--body-policy threshold` 不动），**零指标、零阈值、零冻结值、零 disposition
改动**。

- **A. 放行前置已全部满足**：§2.0 (a) 由 **2026-08-14 批量 GO** 自身满足（该条逐 trial
  枚举 B2–B5 各一次 Play，**无需新 GO**）；用户 2026-08-20 另加的「**先复核再放行 B5**」
  已落账（账本同日，**转述条目 + 用户逐字确认**）并**已由复核轮 15 → 16 走完**
  （轮 15 `REWORK_REQUIRED` F14 → 接受轮 72 返工 → 轮 16 `PASS_WITH_NOTES`，
  `passed_candidate` 前移至 `02c7c88`）。接受轮 72 自设的「F14 闭合后才放行」条件
  **随轮 16 满足**。
- **B. 机械确认（接受轮 73 实跑）**：`canonical_trial_id()` 返回同名、
  `_expected_policy()` = **`threshold`**、`POLICY_PLANNER['threshold']` =
  `threshold-corridor-v1`、`expected_acquisition_ids('b')[4]` 逐字相等、
  `…-trial-5-attempt-1` 与 `…-trial-6` 均被 `run_id_not_frozen_trial` 拒绝、
  run 目录不存在。配对搭档 **A5**。
- **C. 批量授权的边界照旧**：本次 Play 仍走完整 §2.0 (a)–(d)；**任何 void 终态立即中止
  该授权**并回用户重新决定（臂 B 无替代 ID，post-tracker 作废即烧掉 canonical slot）；
  **`--compare` 不在覆盖内**——跑完本轮十次齐备，但仍须**单独授权**。
- **D. 两条预登记限制各已获四次实测确认**（B1–B4 均 `C_geom = 1.0`、min_side 均
  125/125），结论口径不变——效应量**只能报下界**；**一个数都不得据以调参**
  （BC-BODY1-15 (d)）。预期本轮出现**第五次** `SCENE_DEGENERATE`，那是**事前登记的具名
  限制，不是 void、不是新门**。
- **E. 操作纪律（非门）**：确认词产出后**随即**请用户退出（BC-BODY1-29）。四轮停留依次
  `41.390` / `29.602` / `76.804` / `40.198 s`——目标仍是 30–40 s 量级；**但不得提前退出**
  （`…POST_TRACKER_EARLY_EXIT` 仍生效且会烧掉 slot）。
- **F. 其余条款逐字不变**：§2.0 四步、门 1/2/3/4（含 revision 27 收编的五条否定项与
  `hold` 命名规约判据）、握手、BC-BODY1-21/-22/-29/-30、§5 四种 void 终态、
  §2.21 的七处保全 hold 与 §2.23 的归档结果。

## 历史抬头：P1-M3-BODY-001 1c 操作单（revision 27，臂 B trial 4 已完成）

**revision 27（2026-08-20，接受轮 71）**：B4 已判为**有效 trial**（臂 B **4/5**）。
本修订做两件事：新增 **§2.23**（B4 的 post-run 归档合同）与把门 4 的**否定项收编进
操作单**。**槽位不轮换**（仍是 `…-arm-b-trial-4`，该 ID 已消耗），**§4 CLI 一行不动**，
零指标、零阈值、零冻结值、零 disposition 改动。

- **A. §2.23 现在就起草的理由**：shared 槽位此刻装着 B4 的产物。B3 的教训是一次误入
  的 Play 会当场覆盖 truth 与 metrics 且不可恢复（B3 的 256 份帧只是侥幸躲过按 id
  淘汰）。钉住值由本角色**移动前实测、全 64 位落表**。**归档执行前不得进入任何 Play。**
- **B. 门 4 否定项收编（只增停条件）**：自 B2 起 Implementation 每轮自愿多跑一组否定
  核对，四轮全过，但**操作单从未写过它们**——所以每轮都在临场重新推导判据，B4 那轮
  就撞上了 `threshold` 含 `hold` 的裸子串陷阱。本修订把五条否定项写进门 4，并**裁定
  `hold` 必须按命名规约判**（含 `-hold`，或以 `hold` 结尾且不等于 `threshold`）。
  **这是追认既有做法并消除歧义，不放宽任何判据**：门 4 原文只要求两条肯定项，
  否定项本就在门之上，B4 的门 4 按原文**本身就已通过**。
- **C. 不轮换到 B5**：B5 仍在 2026-08-14 批量 GO 内（其 §2.0 (a) 由该条自身满足，
  无需新 GO），但槽位轮换与 B5 的 Play 前核对**本轮不起草**——先请用户就「B5 之前
  是否再走一轮独立复核」给出指示（接受轮 71 §G）。
- **D. 其余条款逐字不变**：§2.0 四步、门 1/2/3 判据、握手、BC-BODY1-21/-22/-29/-30、
  §5 四种 void 终态、§2.21 的两处保全 hold。

## 历史抬头：P1-M3-BODY-001 1c 操作单（revision 26，臂 B trial 4）

**revision 26（2026-08-20，接受轮 70）**：消费复核轮 14 的 `PASS_WITH_NOTES`。
**只应用两条 CLASS_3 补丁并加两处注解，零门、零数值、零 ID、零 disposition、零槽位
改动**，§4 CLI 对 revision 23/24/25 **一行不差**；§2.21 已执行的**结果**一字未动。

- **A. P11（CLASS_3）复判同意并逐字应用**：§2.21 抬头由「本轮第一步，待执行」改为
  「**已执行**，2026-08-20」。属**已执行步骤的时态**，在 §4.4 的 CLASS_3 闭集内；
  方向 fail-closed（照字面重跑会在「destination 移动前必须不存在」当场停住，源也已
  不存在）。**不按 §2.20 先例把 `38/38 + 36/36` 写进抬头**——执行计数的一手来源是
  `…-arm-b-trial-4.md` §A.1/§A.3，抬头再抄一份只会多一个需要同步的副本。
- **B. P7（CLASS_3，自复核轮 11 起挂「随 (c) 批次复判」，本轮即该批次）复判同意并
  逐字应用**：§2.19 历史注的一手来源由 `…-arm-b-trial-3.md` §A 改为
  `…-arm-b-trial-2.md` §D。**本角色实测核对**：24/24 机械核对与七条 `--verify` 的
  一手执行报告确在 trial-2 §D.1/§D.2，trial-3 §A 是 §2.20 时点的复验。纯引用精度。
- **C. N44 采纳（消歧，不改判据）**：§2.22 第 1 项写明其「六个 shared **文件**」
  与 §2.21 / 第 5 项的「六项 shared **成员**」**不是同一集合**（前者含
  `scenario_config.json` 不含 `frames/`，后者相反；`frames/` 由第 2 项单列）。
  两处口径本就一致且无操作歧义，本条只把差别写在明面上。
- **D. N45 采纳（加固，不新设门）**：§2.22 第 7 项补记并集等式的出处
  `274e9804…2d4c`，并按复核轮 14 收工补记 3 写明**该等式与分组无关**——分组正确性
  由两个分组聚合与 id 段 / mtime / 包内 `capture_unix_s` 支撑。
- **E. 放行状态**：用户 2026-08-20 逐字授权「执行，授权执行play」（账本同日条目），
  **复核前置解除**，§2.0 (a) 就此成立。此后 **§2.22（十项）→ §2.0 (b) → (c) → (d)**
  一项不豁免；**BC-BODY1-21 自 (c) 写入起冻结本文件**，故本修订必须落在 (c) 之前。
- **F. 其余条款逐字不变**：§2.0 四步、门 1/2/3/4、握手、BC-BODY1-21/-22/-29/-30、
  §5 四种 void 终态、§2.21 的执行结果、B4 槽位与配对搭档 **A4**。

## 历史抬头：P1-M3-BODY-001 1c 操作单（revision 25，臂 B trial 4）

**revision 25（2026-08-20，接受轮 69）**：**复核轮 13 `REWORK_REQUIRED` 的返工**。
仍只改 §2.21 与 §2.22，槽位不动（`p1-m3-body-001-arm-b-trial-4`），**§4 CLI 对
revision 23/24 一行不差**，**零 Play、零指标、零代码、零阈值、零冻结值改动**。

- **A. F12（CLASS_1）——归属改正，本角色照单接受**：`runtime/frames/` 的 **315 项是
  两次 Play 叠加**，不是一次的产物。**256 项是 B3 的保留帧**（id **907…1034**，
  mtime 2026-08-17，128 帧 ×2），**59 项是 08-20 那次未放行 Play 的**（id **0…28**
  的 58 份 + `latest.json`）。机制：`SensorFrameWriter.cs:212` 的
  `DeleteExpiredFrame(…, publishedFrameId − retainedFrameCount)` **按 frame id 淘汰、
  不按 mtime**（`retainedFrameCount = 128`），新 Play 从 id 0 起算，淘汰窗口够不到
  907 以上，故 B3 的帧原地幸存。算术闭合：`(1034 − 650) / 5 Hz = 76.8 s` = B3 的
  dwell `76.803711 s`——907…1034 正是 B3 收尾停留期的保留帧尾。**本角色已逐条独立
  复算（逐文件 mtime 二分 256/59 无交叉、id 段不重叠、包内 `capture_unix_s`
  `1786939588.328` vs `1787250613.018`、写盘器源码），F12 成立。**
- **B. 我的根因（据实写明）**：revision 24 起草时只读了 `runtime/frames/` 的**目录
  mtime**（= 其最新条目时间），未做逐文件 mtime / frame id 分布核对，也未把「Unity 侧
  只追加、按 id 淘汰」的机制纳入推理。**与 revision 24 纠正 revision 23 的方式同型
  的漏推**。我加的「移动前重测六项」门**挡不住它**：六个钉住值实测全相符，门全过而
  归属照错——**该门防的是「现场又被写过」，不防「归属判错」**（复核 N43）。
- **C. 据实的损失范围（第三次收窄，此后不再有）**：**两项全损**
  （`m3_body_truth.jsonl`、`metrics.json`）、**`frames/` 只损 `latest.json` 一项**
  （257 之 1，256 份帧完好）、**三个发布文件完好**。轮 67 记 6/6、轮 68 记 3/6
  **均为高估**。**结论层仍不翻案**：`m3_body_truth.jsonl` 与 `metrics.json` 确已永久
  覆盖 → **B3 的完整 post-run 归档（六项）永久不可能**、归档 7 处 < 有效 run 8 次
  成立；B3 的有效性与绑定证据不受任何影响。
- **D. 落点改回既有惯例（复核 N42）**：撤销 revision 24 把 B 组放进
  `runtime/test-results/` 的做法——七处 post-run 归档正住在那里，靠目录名回避误计
  是**缓解**而非**消除**。改用与四处既有 hold **完全同构**的平铺命名
  `runtime/<name>.arm-b-trial-3-shared-residue-hold.<ext>`，**从根上不可能被点成第八处
  归档**；`3of6` 这个会随认识变化而失效的数字**从名字里彻底去掉**，精确构成改由
  §2.21 表与 §2.22 第 10 项钉住。
- **E. F13（CLASS_2）——§2.21 补具名落盘地**：定为
  **`docs/evidence/P1-M3-BODY-001-arm-b-trial-4.md`**，依据是 §2.19 的先例（在 B3 的
  预备批次执行、落盘于 `…-arm-b-trial-3.md`），且与 §2.22 同一文件，使「六项前后
  相等」与「十项核对」由接受角色在一处读完。
- **F. P10（CLASS_3）**：本角色独立复判**同意 CLASS_3**（缺失交叉引用，不涉数值、
  阈值、ID、判据、执行顺序、终态名），**逐字应用**，无任何数值/哈希/ID/disposition
  改动。**P7 仍随 (c) 批次复判。**
- **G. 其余条款逐字不变**：§2.0 四步、门 1/2/3/4、握手、BC-BODY1-21/-22/-29/-30、
  §5 四种 void 终态、B4 槽位与配对搭档 **A4**、用户 2026-08-20 的放行条件
  （§2.22 与 (b)/(c) 等复核结论）。

## 历史抬头：P1-M3-BODY-001 1c 操作单（revision 24，臂 B trial 4）

> **已被 revision 25 取代（复核轮 13 F12）**：本抬头 C 条的 A/B 划分与 D 条的
> `test-results/…-shared-residue-3of6/` 落点**均不再有效**——`runtime/frames/` 的
> 315 项是两次 Play 叠加（256 项属 B3），损失范围也不是 3/6。**现行划分、落点与
> 钉住值一律以 revision 25 抬头与 §2.21 为准**；本节只作历史记录，不得执行。

**revision 24（2026-08-20，接受轮 68）**：**只改 §2.21 与 §2.22 两节，槽位不动**
（仍是 `p1-m3-body-001-arm-b-trial-4`），**零 Play、零指标、零代码、零阈值、零冻结值
改动**，§4 CLI **对 revision 23 一行不差**。改写的唯一原因是接受轮 68 的一次实测更正：

- **A. 事实更正**：2026-08-20 那次未放行的 Play **只覆盖了六项 shared 成员中的三项**。
  tracker 从未启动，**三个发布文件因此从头到尾没有被写过**——`body_command.json` /
  `gimbal_command.json` / `tracking_observation.json` 的 mtime 均为 **2026-08-17
  00:05:11**，`issued_unix_s = 1786939511.56761` 换算即该时刻，与 B3 run 目录内
  `metrics.final.json` / `summary.json` 的 00:05 一致，且三者 SHA-256 与 B2 归档的
  三份**全不相同**（B2 的 `issued_unix_s = 1786749649.460062`）。**它们是 B3 收尾的
  发布字节，是 B3 shared 侧仅存的三项。** 轮 67 §C「三个发布文件现在装的是今日这次的
  字节」据此更正。
- **B. 结论未变的部分**：`frames/`、`m3_body_truth.jsonl`、`metrics.json` 三项确已被
  覆盖，故 **B3 的完整 post-run 归档（六项）永久不可能**，归档处数（7）仍少于有效 run
  数（8）。**永久损失是六项中的三项，不是六项**——轮 67 高估了范围，本修订据实收窄。
- **C. §2.21 按来源拆成两组**：A 组（该次 Play 的产物）进 `…unreleased-play-20260820`
  hold；B 组（B3 的残留三项）进 **`p1-m3-body-001-arm-b-trial-3-shared-residue-3of6/`**。
  revision 23 把六项一并塞进 08-20 的 hold，**会给 B3 仅存的字节贴上错误标签**，且那是
  最后一次能给它们贴正确标签的机会。
- **D. 钉住值改回接受角色预先钉住**：现场自 08-20 14:30 起静止，接受轮 68 已逐项实测并
  写进 §2.21 两张表（**全 64 位，不用缩写**，轮 10 F7 的规矩）。**revision 23 的
  D 条偏离（改由实现角色事后钉）就此取消**；Implementation 在移动前必须重新实测，
  **任一项与表不等即停止回 Acceptance**（不等即意味着现场又被写过，属新事件）。
- **E. §2.22 增至十项**：第 7 项改为 A 组三个 destination，新增第 **10** 项核对 B 组
  目录；第 5 项的七处完整归档与七个聚合值**一字未动**，只把差额注解指向 B 组目录。
- **F. 其余条款逐字不变**：§2.0 四步、门 1/2/3/4、握手、BC-BODY1-21/-22/-29/-30、
  §5 四种 void 终态、B4 的槽位与配对搭档 **A4**。

## 历史抬头：P1-M3-BODY-001 1c 操作单（revision 23，臂 B trial 4）

**revision 23（2026-08-20，接受轮 67）**：B3 已判为**有效 trial**（臂 B **3/5**）。
本修订轮换到 **`p1-m3-body-001-arm-b-trial-4`**（批量授权已覆盖，无需新 GO），并新增
**§2.21**（2026-08-20 那次**未放行** Play 的现场保全）与 **§2.22**（B4 的 Play 前
核对）。§2.19/§2.20 转历史。**零 Play、零指标、零代码、零阈值、零冻结值改动。**

- **A. 同臂轮换，只改一行**：`--body-policy threshold` 不动，CLI 对上一修订恰 1 行
  （`--run-id`）。**对已复核候选的差异行数不写死**——`<BASE>` 按 §2.0 (b) 运行时现取，
  实测几行报几行（轮 66 定的规矩）。
- **B. 机械确认（接受轮 67 实跑）**：`canonical_trial_id()` 返回同名、
  `_expected_policy()` = **`threshold`**、`expected_acquisition_ids('b')[3]` 逐字相等、
  `-attempt-N` 被 `run_id_not_frozen_trial` 拒绝、run 目录不存在。配对搭档 **A4**。
- **C. B3 无归档合同，且此后也不会有**：2026-08-20 那次未放行的 Play 覆盖了 shared
  槽位，**B3 的 post-run 归档源已不存在**（接受轮 67 §C）。**不为它起草合同**——写一份
  不可执行的合同只会多一个失效指针。故自本修订起 **归档处数（7）少于有效 run 数（8）**，
  差额恒为 B3 一处，§2.22 第 5 项据此写死。
- **D. §2.21 的钉住值由实现角色实测**：起草本修订时用户仍在那次 Play 中，退出可能有
  末次 flush，接受角色**无法预先钉住**——此处偏离「接受角色移动前钉住」的惯例，
  逐字披露；改为实现角色移动前实测落盘、接受角色事后逐项复核。
- **E. 其余条款逐字不变**：§2.0 四步、门 1/2/3/4、握手、BC-BODY1-21/-22/-29/-30、
  §5 四种 void 终态。**BC-BODY1-29 的「随即」按轮 67 §B 强调执行**：确认词产出后更快
  请用户退出，把 post-tracker 停留压回 30–40 s 量级（操作纪律，非新门）。

## 历史抬头：P1-M3-BODY-001 1c 操作单（revision 22，臂 B trial 3）

**revision 22（2026-08-14，接受轮 63）**：B2 已由接受轮 63 判为**有效 trial**
（臂 B **2/5**）。本修订做两件事，**均在 2026-08-14 批量授权（B2–B5）覆盖之内，
无需新 GO**：新增 **§2.19**（B2 的 post-run 归档合同）与 **§2.20**（B3 的 Play 前
核对），并把槽位轮换到 **`p1-m3-body-001-arm-b-trial-3`**。§2.18 转历史。
**零 Play、零指标、零代码、零阈值、零冻结值改动。**

- **A. 同臂轮换，只改一行**：`--body-policy threshold` 不动，故 §4 CLI 对上一修订
  **恰 1 行不同**（`--run-id`）。**对已复核候选的差异行数不在本文件写死**（接受轮 66
  按实现角色登记的缺陷更正）：`<BASE>` 按 §2.0 (b) **运行时现取**（COORD-007 R7
  「可派生标识禁手写」），差异由 **(b) 执行时实测几行就报几行**——复核通过会前移
  `passed_candidate`，任何写死的行数都会在下一次通过时变成虚假归因。
  **历史事实（不再作为归因指令）**：起草 revision 22 时的已复核候选是 `408acd7`
  （臂 A trial 5 的版本），对它本块是 2 行不同。
- **B. 机械确认（接受轮 63 实跑）**：`canonical_trial_id()` 返回同名（**从未消耗，
  无需替代 ID，两个 predecessor 门都不触发**）、`_expected_policy()` = **`threshold`**、
  `expected_acquisition_ids('b')[2]` 相等、`-attempt-N` 被 `run_id_not_frozen_trial`
  拒绝、run 目录不存在。配对搭档 **A3**。
- **C. 批量授权的边界照旧**：每次 Play 仍各走完整 §2.0 (a)–(d) 与各自核对节；
  **任何 void 终态立即中止该授权**并回用户重新决定；`--compare` 不在覆盖内。
- **D. 两条预登记限制各已获两次实测确认**（B1/B2 均 `C_geom = 1.0`、min_side 均
  125/125），结论口径不变，**一个数都不得据以调参**（BC-BODY1-15 (d)）。
- **E. 其余条款逐字不变**：§2.0 四步、门 1/2/3/4、完成握手、BC-BODY1-21/-22、
  BC-BODY1-29/-30、§5 四种 void 终态与「每种终态各消耗一次 one-Play GO」。

## 历史抬头：P1-M3-BODY-001 1c 操作单（revision 21，臂 B trial 2）

**revision 21（2026-08-14，接受轮 61；用户「照跑 B2–B5，饱和作具名限制」）**：
本修订把操作单轮换到 **`p1-m3-body-001-arm-b-trial-2`**。**零 Play、零指标、
零代码、零阈值、零冻结值改动。**

- **A. 只换一行（对上一修订）**：`--body-policy threshold` **保持不变**（同臂内
  轮换），故 §4 CLI 块对 **revision 19/20（B1）恰 1 行不同**（`--run-id`），回到
  revision 13–17 的常规形态；本文件唯一改过两行的是 revision 19 那次跨臂轮换。
  **注意两个基准不同**：§2.0 (b) 的归因比的是**已复核候选**，起草本修订时该候选是
  `408acd7`（臂 A trial 5 的版本），对它本块是 **2 行不同**（`--run-id` 与
  `--body-policy`）——报告 (b) 时按对已复核候选的**实测**写，不得把「1 行」填进归因。
  **时间边界（接受轮 66）**：`408acd7` 这个具体值自复核轮 11 通过起已过期；
  `<BASE>` 一律运行时现取、差异一律实测，本句的候选值只作历史记录。§1 采集 ID 行、§3 步骤 4/5、门 4 的
  token 序列、§3 步骤 4 的 `--validate-completion` 全部同步。
- **B. 机械确认（接受轮 61 实跑）**：`canonical_trial_id()` 返回同名（**从未被
  消耗，canonical slot 即其自身，无需替代 ID，两个 predecessor 门都不触发**）、
  `_expected_policy()` 返回 **`threshold`**、`expected_acquisition_ids('b')[1]`
  逐字相等、`…-arm-b-trial-2-attempt-N` 被 `run_id_not_frozen_trial` 拒绝、
  run 目录不存在。配对搭档是 **A2**（采集 ID `…-arm-a-trial-2-attempt-2`）。
- **C. 新增 §2.18**（B2 的 Play 前只读核对，九项——沿用 §2.16 的九项结构，其中
  第 4/5 项扩到**六个** run 目录与**六处** post-run 归档，两项臂 B 专属保留）；
  §2.16 已转历史，**§2.17（B1 归档）仍是本轮第一步待执行**。
- **D. 批量授权的边界（账本 2026-08-14）**：用户一次性授权 B2–B5 四次 Play，
  **但每次仍各走完整 §2.0 (a)–(d) 与各自的核对节**；**任何 void 终态立即中止该
  授权**，停下回用户重新决定（臂 B 无替代 ID，post-tracker 作废即烧 slot）。
  `--compare` 仍需十次齐备并单独授权。
- **E. 两条预登记限制随本轮继续生效**：H2-CEILING（`H2_SUPPORTED` 算术不可达，
  上限 `THRESHOLD_ALLOCATION_PARTIAL`）与**处理臂饱和**（`C_geom` 效应量只能报
  下界）。**一个数都不得据以调参**（BC-BODY1-15 (d)）。
- **F. 其余条款逐字不变**：§2.0 四步、门 1/2/3/4、完成握手、BC-BODY1-21/-22、
  BC-BODY1-29/-30、§5 四种 void 终态与「每种终态各消耗一次 one-Play GO」。

## 历史抬头：P1-M3-BODY-001 1c 操作单（revision 20，B1 归档合同）

**revision 20（2026-08-14，接受轮 60）**：B1 已由接受轮 60 判为**有效 trial**
（臂 B **1/5**）。本修订**只**新增 §2.17——B1 的 post-run 归档合同——**不做槽位
轮换**：臂 B trial 2–5 **均未获 GO**，且轮 60 已把「主指标在处理臂上饱和
（`SCENE_DEGENERATE`，`C_geom = 1.0`）」上交用户决定，**在答复前不发任何臂 B
trial 2 前置**。§2.16 转历史。**零 Play、零指标、零代码、零阈值。**

## 历史抬头：P1-M3-BODY-001 1c 操作单（revision 19，**臂 B trial 1** —— 首次跨臂轮换）

**revision 19（2026-08-14，接受轮 58；用户 GO「1 + 3 合并执行，明确拒绝 2」）**：
本修订把操作单从臂 A 轮换到 **`p1-m3-body-001-arm-b-trial-1`**，**这是本文件历史上
第一次跨臂轮换**。**零 Play（本修订自身）、零指标、零代码、零阈值、零冻结值改动。**

- **A. 双重轮换（本文件历史上第一次改动 §4 CLI 的第二行）**：此前每一次修订都只改
  `--run-id` 一行；本轮必须**同时**改 `--run-id` 与 **`--body-policy hold` →
  `threshold`**。故 §4 CLI 块 19 行**恰 2 行不同**，其余 **17 行 / 16 个参数**逐字
  不变（19 行 = 1 行入口 + 18 个参数；历次抬头的「其余 18 个」把参数总数当成了
  「其余」，读数一直偏大 1）。§1 臂位行、§3 步骤
  4/5 同步。**revision 18 抬头预写的那条提示（须同时改臂位行、`--body-policy` 与
  `--run-id`，并核对 `_expected_policy()` 返回 `threshold`）本轮已兑现。**
- **B. 机械确认（接受轮 58 实跑，只读）**：`expected_acquisition_ids('b')` =
  `['…-arm-b-trial-1', …, '-arm-b-trial-5']`，索引 **`[0]`**（不是 `[4]`）；
  `canonical_trial_id()` 返回同名；**`_expected_policy()` 返回 `threshold`**，
  `POLICY_PLANNER['threshold']` = **`threshold-corridor-v1`**；B1 既非 A1 也非 A2
  的替代采集 ID，故**两个 predecessor 门都不触发**；`runtime/runs/…-arm-b-trial-1/`
  不存在。配对搭档是 **A1**（采集 ID `p1-m3-body-001-arm-a-trial-1-attempt-4`）。
- **C. 新增 §2.16**（B1 的 Play 前只读核对，**九项** = §2.14 的七项 + **两项臂 B
  专属**：corridor 工件哈希、`_expected_policy()` 复核）；§2.15 转已执行历史。
- **D. 新增 §1 的 corridor 工件钉住行**：`config/p1-m3-body-001-corridor-prisms.json`
  SHA-256 `9e2956ad…c800`、**779** 条棱柱。这是 **臂 B 专属的启动门**
  （`track_loop.py` 的 `elif policy_name == "threshold":` 分支内，哈希不符即
  `ValueError` 启动期失败），臂 A 五次 Play 从未触碰，此前 §1 也从未钉住它。
- **E. 失效标注就地更正（AGENTS.md「交接文字必须与现实一致」，零语义改动）**：
  §1 激活方式行的「trial 后恢复」（十次 Play 期间 SCENE-004 override 一直移开，
  从未恢复过，恢复它会换掉载体并破坏配对）、§3 步骤 0′ 与门 1 记录条款里 revision
  12 遗留的「记入 trial 2 证据文件」（这是**启动 tracker 的硬前置**，指错文件等于
  条款落空）、§3 步骤 3 的「臂 A 每帧由 `HoldBodyPlanner` 发布 hold」、§5 那条
  `TRIAL_VOID_LOOP_DOMAIN_UPPER_BOUND_VIOLATION_POST_TRACKER_DWELL` 仍把触发写成
  「停留到 `final_mileage >= 2P`」（该上界已由接受轮 42 §A 撤下——**照字面读会促使
  操作员提前退出 Play，正好撞上仍然生效的 `…POST_TRACKER_EARLY_EXIT`**）。
- **F. 新增一条停条件 + 两条披露，均不放宽任何门**：
  - **门 4（§3 步骤 2 末段，启动前命令行核对）**：按下回车之前必须把**实际命令行
    原文**落盘并逐字核对含 `--body-policy threshold` 与
    `--run-id p1-m3-body-001-arm-b-trial-1`。理由是跨臂轮换第一次让 `--body-policy`
    成为可写错的量，而启动前**原本没有任何机制核对它**——写错要到分析期才由臂身份
    三层核对暴露，那时 run 目录已 create-once 建成、采集 ID 已消耗，而**臂 B 没有
    替代 ID**。本门零阈值零指标，只把一次不可恢复的手误挡在 run 目录创建之前。
  - **披露 1**：§5 的**臂 B 零作废容错**，并逐字区分——pre-tracker 的三个硬门与
    启动失败**不消耗采集 ID**（只消耗一次 one-Play GO），真正烧 slot 的是
    post-tracker 终态。
  - **披露 2**：§3 步骤 6 的**退化臂 B 记录与回接受角色条件**（`[0, P)` 内
    `body_motion_effort_m == 0` 时停下回接受角色归因，**本身不使 trial 作废**——
    事后新设作废门属改协议）。
- **G. BC-BODY1-15 (c) 不重新武装**：三分支绑定「批次 1c 的**第一次** Play（必须是
  臂 A trial 1）」，A1 的 `0.5784550773737355` 落在 `[0.5645, 0.95)` 已放电其余九个
  （含臂 B 五次，接受轮 38）。本轮**只改主语措辞，不为 B1 新立任何数值门**。
- **H. 其余条款逐字不变**：§2.0 四步顺序、**门 1/2/3 的判据与阈值**、完成握手、
  BC-BODY1-21/-22、BC-BODY1-29/-30、§5 四种 void 终态的**触发与处置**（除 E 点
  声明的 loop-domain 上界行加注外）与「每种终态各消耗一次 one-Play GO」。
  **（F 点的门 4 是新增的启动前停条件，不改门 1/2/3 的任何判据。）**

**复核轮 8 返工（2026-08-14，接受轮 56；Review round 8 `REWORK_REQUIRED` on
`13bf9dd`，修复归本角色）**：revision 号**不变**（沿轮 46 勘误/轮 47 更正先例）
——本批只改文字，**零 Play、零 ID、零代码、零阈值、零冻结值改动**，八处如下；
三条 CLASS_2 均 `NOT_MECHANIZABLE`，闭合 = 下一复核轮**定点复看**本段点名段落，
本角色不给自己的修正签发通过：

- **F4（CLASS_2）**：§2.0 (b) 基线例示由 `grep -m1`（取文件序第一行 = 最旧）改为
  `… | tail -1`（复核轮次只追加，最新一行 = 文件末行）；规范句「最新一行」逐字不动。
- **F5（CLASS_2）**：§1「acquisition IDs」行按 BC-BODY1-26 改写——A1、A2 双替代，
  其余**八**个等于 canonical slot；原「其余九个」对 A2 为假。
- **F5b（轮 56 自查，同类）**：§1「A1 采集 ID」行去「唯一替代」与「其余九个 ID
  逐字不变」，改指「acquisition IDs」总表行（AGENTS.md 失效文字同批修正义务）。
- **F6（CLASS_2）**：§1 真值载体行的 `--verify` 只读范围按 BC-BODY1-27 改写——
  A1/A2 两个 attempt 采集各另读其 predecessor hold，其余**八**个只读 run 目录。
- **F6b（轮 56 自查，同类）**：§3 步骤 5 的同一声明同步改写（A1/A2 双 hold、
  「其余九个」→「其余八个」）。
- **P1/P2/P3（CLASS_3，复核轮 8 逐字补丁，本角色复判同意后同轮应用）**：§1 A5 行
  与 §4 抬头/尾注的已执行时态更正、§2.6 注残留行号钉去钉。
- 历史修订块（revision 11/12 等抬头）中的当时表述**不回改**——它们是各自批次的
  记录；本批只改 live 段落（§1、§2.0、§2.6 注、§3 步骤 5、§4）。

处置 `RUNBOOK_ROUND8_REWORK_TEXT_ALIGNMENT_TO_BC26_BC27_R7_NO_GATE_RELAXATION_
CLOSURE_BY_TARGETED_REINSPECTION`（裁定与逐条复判见提案 Acceptance round 56）。
**§2.15 仍是唯一待执行节，本批未触碰其任何条款。**（**时间边界（revision 19）**：
该句写于接受轮 56 时属实；§2.15 已于 2026-08-14 由 `e68827d` 执行完毕，自那时起
本轮唯一待执行节是 **§2.16**。）

**revision 18（2026-08-13，接受轮 55；用户「trail5已经运行完成」）**：A5 已由
接受轮 55 判为**有效 trial**，**臂 A 因此 5/5 收官**。本修订**只**新增 §2.15
——A5 的 post-run 归档合同——**不做槽位轮换**：臂 B 五次**均未获 GO**，在拿到
逐字授权之前 §1 采集 ID 行、§3 步骤 4/5 与 §4 CLI **一律不动**（否则操作单会指向
一个未获授权的采集）。§2.14 转历史。**零 Play、零指标、零代码、零阈值。**

**臂 B 首次采集需要的不只是槽位轮换**（本条只作提示，不预判）：臂 B 的
`--body-policy` 是 `threshold`，与臂 A 的 `hold` 是 §1 冻结项里唯一按臂取值的
参数，届时的修订必须同时改 §1 臂位行、§4 CLI 的 `--body-policy` 与 `--run-id`，
并在发令前置里重新核对 `_expected_policy()` 返回 `threshold`。

**revision 17（2026-08-13，接受轮 53；用户 GO「授权第五次trail」）**：本修订把
操作单轮换到 **`p1-m3-body-001-arm-a-trial-5`**（臂 A 第 5 次，收尾臂 A）。
**零 Play、零指标、零代码、零阈值**：暂停窗、初始框、测量窗、整圈周长、watchdog、
五次/臂、CLI 其余 18 个参数逐字不变。

- **A. 槽位轮换**：§1 采集 ID 行、§3 步骤 4/5 与 §4 CLI 的 `--run-id` 换为 A5。
  A5 **从未被消耗**，canonical slot 即其自身，**无需替代 ID，两个 predecessor 门
  都不触发**（机械确认见 §1 行）。
- **B. 无归档待办**：A4 的 post-run 归档（§2.13）已在上一批次执行完毕，§2.13
  转为已执行历史。**本轮 §2 只有一节待执行：§2.14。**
- **C. 新增 §2.14**：A5 的 Play 前只读核对（七项，现在要 `--verify` **四个**
  有效 run、核对**四处** post-run 归档）。§2.12 转历史。
- **D. 失效标注就地更正（AGENTS.md「交接文字必须与现实一致」，零语义改动）**：
  §2.8/§2.9/§2.11 三节的标题此前仍写"待执行 / 本轮第一步"，而三者均已执行完毕；
  §4 标题与括注仍写"本轮 = 臂 A trial 2 / revision 12 已换为 A2"。本轮把四处
  改为与现实一致的措辞，**不改任何参数值、阈值、哈希或动作内容**——留着会让
  实现角色误以为本轮还有归档待办。
- **E. 其余条款逐字不变**：§2.0 四步顺序、三个硬门、完成握手、BC-BODY1-21/-22、
  BC-BODY1-29/-30、§5 四种 void 终态与"每种终态各消耗一次 one-Play GO"。

**revision 16（2026-08-13，接受轮 52；用户「trail4已经结束，归档」）**：A4 已由
接受轮 52 判为**有效 trial**（arm A **4/5**）。本修订**只**新增 §2.13——A4 的
post-run 归档合同——**不做槽位轮换**：arm A trial 5 与臂 B 五次**均未获 GO**，
在拿到逐字授权之前 §1 采集 ID 行、§3 步骤 4/5 与 §4 CLI **一律不动**。
**零 Play、零指标、零代码、零阈值。**

**revision 15（2026-08-13，接受轮 50；用户 GO「接受一下trail3并授权trail4」）**：
A3 已由接受轮 50 判为**有效 trial**（arm A **3/5**），本修订轮换到 **`p1-m3-body-001-arm-a-trial-4`**。
**零 Play、零指标、零代码、零阈值**；结构与 revision 14 同构：§1 采集 ID 行、
§3 步骤 4/5、§4 CLI 换 ID，§2.10 转历史，新增 §2.11（A3 的 post-run 归档合同）
与 §2.12（A4 的 Play 前只读核对）。A4 同样**从未被消耗**，canonical slot 即其
自身，**无需替代 ID、不触发任何 predecessor 门**。

**revision 14（2026-08-13，接受轮 48；用户 GO「授权进行trail3」）**：A2
（attempt-2）已由接受轮 47 判为**有效 trial**（arm A 2/5），本修订把操作单轮换到
**`p1-m3-body-001-arm-a-trial-3`**。**零 Play、零指标、零代码、零阈值**：暂停窗、初始框、
测量窗、整圈周长、watchdog、五次/臂、CLI 其余 18 个参数逐字不变。

- **A. 槽位轮换**：§1 采集 ID 行、§3 步骤 4/5 与 §4 CLI 换为 A3。A3 **从未被
  消耗**，canonical slot 即其自身，**无需替代 ID，两个 predecessor 门都不触发**
  （机械确认见 §1 行）。§2.7 转为已执行历史。
- **B. 新增 §2.9**：A2 的 **post-run 归档**合同（valid-trial 命名空间，A1 先例），
  在本轮 Play 前执行——A2 的 run 目录 **不移动**，只归档 shared 侧六项。
- **C. 新增 §2.10**：A3 的 Play 前只读核对（八项）。
- **D. 其余条款逐字不变**：§2.0 四步顺序、三个硬门、完成握手、BC-BODY1-21/-22、
  BC-BODY1-29/-30、§5 四种 void 终态。

**revision 13（2026-08-13，接受轮 45 §B；BC-BODY1-28 第 4 步）**：Review round 7
`PASS_WITH_NOTES`（候选 `07bb8a4`，`passed_candidate` 机读行已落盘）之后，把
操作单从**已作废并被永久拒绝**的旧 ID 轮换到 BC-BODY1-26 冻结的替代采集
`p1-m3-body-001-arm-a-trial-2-attempt-2`，并落地 F4 条款与 F2 之后的判据文字。
**零 Play、零指标、零代码、零阈值**：暂停窗、初始框、测量窗、整圈周长、
watchdog、五次/臂、CLI 其余 18 个参数逐字不变。

- **A. 槽位轮换**：§1 采集 ID 行、§2.7（新，attempt-2 的只读 Play 前核对）、
  §3 步骤 4/5 与 §4 CLI 的 `--run-id` 全部换为新 ID；§2.6 转为已执行历史。
- **B. F2 之后的判据文字**（N25）：§1 整圈定义域行改写为**只有下界 + 两条
  域完整性门**；watchdog 行的 `81.6 s` 论证降为历史背景。
- **C. F4 条款落地**（BC-BODY1-29/-30）：§3 步骤 4 确认词之后**立即**请用户
  退出，证据事后写；§3 步骤 6 记录 post-tracker 停留与实测圈数。
- **D. 基线指针改为运行时派生**（N26 + COORD-007 R7）：§2.0 (b) 不再手写
  SHA，改取 `docs/reviews/P1-M3-BODY-001.md` 中最新一行 `passed_candidate`。
- **E. 现场保全与隐藏文件**（BC-BODY1-33 + N27）：新增 §2.8 保全记录节，
  预先写死 hold 的十文件精确集合与隐藏文件处置。
- **F. 过期行号**：`:799`、`1034-1038`、`1368-1373` 三处改为按**函数/模式名**
  引用，不再钉行号（行号随每次改动腐化，Review round 7 §4 已两次登记）。

**round 40 更正（2026-08-13，仅三处、零阈值/零指标/零 CLI 改动）**：§2.0 (b)
注的 PLAY_GOVERNING 计数由「恰六个」更正为「七个」并补第七条（本文件自身）
的归因与单独处置；§2.0 新增 BC-BODY1-21/-22 两条执行条款。裁定与依据见
`docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md`
Acceptance round 40。**revision 号不变**：本次只更正计数与新增停条件，
未改任何冻结值、指令或采集 ID。

**revision 12（2026-08-13，按用户 GO 与 Acceptance round 39 §B）**：A1
（`…-attempt-4`）已由接受轮 38 认定为有效 canonical A1 并归档，本修订把
操作单从 A1 轮换到当时唯一授权的采集 `p1-m3-body-001-arm-a-trial-2`
（**时间边界（revision 13）**：该次采集已作废，其 ID 已消耗并被代码永久拒绝；
本操作单当前的采集 ID 见 §1「本轮采集 ID（A2，revision 13）」行）。
**零 Play（本修订自身）、零指标、零代码、零测试、零 config/scenario/model
改动；所有冻结阈值、测量窗、指标口径、初始框、CLI 参数逐字不变。**

- **A. 有效槽位轮换**：新增 §1「本轮采集 ID」钉住行与 **§2.6**（trial 2 的
  只读 Play 前状态核对）；§2.5 转为已执行历史。§3 步骤 4/5 与 §4 CLI 的
  `--run-id` 由 attempt-4 换为 `…-arm-a-trial-2`，**其余参数一个不改、
  一个不加**。A1 的 run 目录、post-run 归档与三处 void hold 在本轮是
  **只读保全对象**，不得移动、覆盖或分析。
- **B. 暂停窗与解释器：记录型条款（§3 步骤 0′/2′）**。二者把既有散文期望
  变成**必须落盘**的步骤，使用的字段**已经存在且已经产出**：暂停窗判据
  沿用 §3 步骤 2 既有括注（「实测取保留帧中最大 `simulation_time_s`」，
  attempt 4 即据此得 `6.381126`），解释器路径取预检 JSON 既有的
  `interpreter.executable`（`preflight_reanchor_env.py:378-379`）。
  **阈值 `[2.000000, 10.000000)` 与唯一合法入口逐字不变。**
- **C. 本修订不是 COORD-007 §4.1/§4.2 的机器断言**。那两条是 **R10**
  （`tools/trial.py` 第 (3)(4) 项），属代码且**未获授权**（账本
  2026-08-12 COORD-007 条目逐字列为明确未授权），亦超出接受角色边界。
  **残留缺口逐字披露，不得被本修订的记录型条款掩盖**：由保留帧导出的
  `reported_sim_t` 是暂停真实时刻的**下界**——最后一帧之后、暂停生效
  之前的不足一帧时间不可见（attempt 4 实测 frame 31 @ `6.381126 s`，
  均值约 `0.206 s/帧`）。因此「末帧 `9.97` PASS 而真实暂停在 `10.03`」
  这一 §4.1 情形**今天仍可逐字重演**，本修订未消除它。消除它需 §4.1 的
  遥测写入（Unity 暂停时落 `sim_t`）+ 启动前断言，即 R10。
- **D. 首跑退化门已由 A1 放电**：BC-BODY1-15 (c) 的三分支是**首次 Play**
  的门，A1 落在 `[0.5645, 0.95)` 已释放其余九个 trial 的协议合格状态，
  trial 2 **不重复触发**该三分支（见 §5）。BC-BODY1-15 (d) 的反调参纪律
  与全部 void 终态**继续逐字适用**。

**revision 11 round 4（2026-08-10，按 Acceptance round 33 §B 闭合 Review
round 5 的 F3）**：§2.1/§2.2 改标为**已执行的历史保全记录**并删去「新 GO 后
再执行」的现在时指令；§2.2 为旧 canonical A1 ID 加时间边界，与 §1/§2.4/§5
及 `run_id_void_consumed` 对齐；新增 **§2.5**——attempt 4 唯一待执行的
**只读** Play 前状态核对（六个 shared 文件不存在、`runtime/frames/` 为空、
四组 hold 完好、无活动标记、`…-attempt-4/` 不存在）；§3 step 5 的 `--verify`
说明与实现对齐（A1 另读 run 外的 predecessor hold）；§6 revision-10 历史句
加时间边界。**零移动、零删除、零重算现场；零代码、零测试改动。**

**revision 11（2026-08-10，round 2 按 Acceptance round 30 §C 返工）**：按 round 29 §C 修 attempt 3 作废
（`TRIAL_VOID_PROTOCOL_DEVIATION_POST_TRACKER_EARLY_EXIT`）暴露的两件事：
正式 ID 已被 void 现场占用、以及「完成」缺少可机械确认的握手。
**本修订零 Play、零新 ID、零指标**；三次 void 现场均已保全。

- **C1 attempt-3 隔离**：见 §2.4（已执行，七组移动的计数/行数/字节/SHA 见
  实现证据）。
- **C2 唯一替代采集 ID**：A1 的下一次且**仅**下一次采集使用
  **`p1-m3-body-001-arm-a-trial-1-attempt-4`**，映射回 canonical slot
  `p1-m3-body-001-arm-a-trial-1` 并与原 B1 配对。旧 ID
  `p1-m3-body-001-arm-a-trial-1` **永久拒绝**（`run_id_void_consumed`）；
  其余九个正式 ID 逐字不变。见 §1 新增钉住项与 §4 的 `--run-id`。
- **C3 完成握手**：见 §3 步骤 4，`TRACKER_AUTO_COMPLETE_CONFIRMED`。
- **C4 异常终态**：见 §5 新增的 post-tracker void 条目。
- **round 30 §C 追加**：§3 step 5 与 analyzer Usage 改用采集 ID（旧 ID 必被拒）；
  §1 拆成 canonical slots / acquisition IDs 两行；§4 写明只换 `--run-id`；
  §5 分开 pre-tracker 与 post-tracker void 的 ID 消耗结论；§3 step 4 的确认词
  改由 `--validate-completion` 机械产生；analyzer 新增 A1 predecessor hold
  真实字节门。
- **C5 冻结不变项**：frame 0/box、planner/arm、模型、重锚、场景、130 s、
  62.5 m 窗、212.9706 m 整圈、主指标、阈值、五次/臂、BC-BODY1-15 **逐字
  不变**；不以 attempt-3 内容调参。

# 以下为 revision 10 及更早修订记录

**revision 10（2026-08-10）**：按 Acceptance round 25 §B 修 attempt 2 作废
（`TRIAL_VOID_PROTOCOL_DEVIATION_PRE_TRACKER`）暴露的两个操作/记录缺陷。
**本修订零 Play、零 run ID、零指标**；两次 void 现场均已保全。

- **B.2 暂停窗口是独立硬门**：§3 步骤 2 改为逐字定义
  `2.000000 <= reported_sim_t < 10.000000`，见 §3 步骤 2 与 §1 新增钉住项。
  不满足时**唯一动作**是保持暂停、不启动 tracker、不恢复 Play、退出并保全
  现场、回 Acceptance。frame 0 匹配、冻结框覆盖正常或「测量窗按里程不受
  影响」**都不得覆盖该终态**，运行中也不得申请例外。
- **B.3 Play 前记录的时序自引用消除**：§2 前段改为四步顺序（GO 入账并提交
  → Implementation 在最终干净 HEAD 上实测并报告 → **Acceptance** 在用户进
  Play 前写入 `docs/unity-test-log.md` → 发令时工作树只允许这一份未提交的
  Unity 日志差异）。**不得**再以「要保持完全干净所以 Play 后补写」为由延迟
  记录；attempt 2 正是因此缺失事前记录而作废。
- **B.1 attempt 2 现场保全**：见 §2.3（已执行，计数/SHA 见实现证据）。
- **B.4 冻结语义全部保留**：revision 9 的唯一解释器/CLI、run ID、frame 0、
  像素框与 normalized box、planner/arm、130 s watchdog、分析器、阈值、
  测量窗、§5 退化三分支与反调参纪律**逐字不变**；零 controller/Assets/
  config/models/tools/tests/指标算法/Review/正式设计改动。

# 以下为 revision 9 及更早修订记录

**revision 9（2026-08-09）**：按 Acceptance round 21 §B.2 迁移预检工具路径。
`tools/check_*.py` 属工作流基础设施（`AGENTS.md`），实现角色不得修改；
revision 8 曾把预检加进 `tools/check_track_env.py`，该文件已逐字节恢复。
§1「Play 前环境预检」钉住项与 §3 步骤 0 的唯一命令改为普通实现工具：

```bash
.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json
```

该工具对 cv2/torch/torchvision/ultralytics 比较**原始 `__version__` 与配置
pin 逐字相等**（不规范化、不剥 `+local`），并在预检前后机械比对
`runtime/runs/` 直接子目录名集合与四个文件（三个发布 + `runtime/metrics.json`）
各自的存在状态、字节大小与 SHA-256。revision 8 的其余落点全部保留。

**revision 8（2026-08-09）**：按 Acceptance round 20 §B 修 arm A trial 1
尝试 1 作废暴露的三个协议缺口。**本修订零 Play、零 run ID、零指标**，
现场保持冻结。

- **B.1 解释器与入口唯一化**：§4 的唯一合法 tracker 入口是
  **`.venv-yoloe/bin/python -m controller.track_loop`**。**禁止**裸
  `python3`、`.venv-track/bin/python` 和直接文件入口
  `python3 controller/track_loop.py`（后者自 `5340cf6`/`a234270` 落地相对
  导入后必然 `ImportError`，revision 7 的字面命令因此不可执行）。
  `.venv-track` 缺 `torch`/`ultralytics`，构造 re-anchor carrier 必然失败。
  **全部 CLI 参数逐字保留**，不改 tracker、re-anchor、planner、指标、
  窗口或阈值。
- **B.2 冻结初始框精度**：init frame、像素框与四个精确分数写进 §1/§3/§4
  （见「冻结初始框」钉住项）。归一化必须用项目 `pixels_to_norm` 口径，
  并要求 `norm_to_csrt_pixels` 往返回 `(177,195,77,73)` **逐值相等**；
  **禁止**用展示用六位小数替代（实测 `0.276562 0.406250 0.120313
  0.152083` 往返为 `(176,195,78,73)`，差 1 px）。未来 Play 只允许对冻结
  叠框做**匹配/不匹配目检**，不重新估框；不匹配的唯一合法动作是 fail
  closed 回 Acceptance。
- **B.3 void 现场的下一轮隔离合同**：见 §2.2（revision 10 起编号）。**该修订期不执行**这些移动。
- **B.5 Play 前环境预检**：见 §3 步骤 0，在任何 Play 步骤之前必须通过。

revision 7 的其余落点（F1 测量窗硬门、F2 update 行分类、N11 勘误）全部保留。

**revision 7（2026-08-08）**：按 Acceptance round 17 §B 修 Review round 3
的两个阻断项。

- **F1 测量窗来源硬门**：分析在使用测量窗之前，必须验证
  `sha256(run/margin.json) ==
  body_config.measurement_window.artifact_sha256` 且
  `margin.visible_arc.sha256 ==
  body_config.measurement_window.visible_arc_sha256`；两侧都必须是 64 位
  小写十六进制，缺失/类型错/不等一律具名 fail closed。receipt 继续记录
  实际两个哈希，且两键进入 compare `identity_keys`——十次 trial 必须
  共用同一个测量窗来源。`_collect_inputs` 的 create-once 保留，但预置
  不同字节会被 pin 拒绝。
- **F2 update 行分类（撤回 revision 6 的无条件读法）**：revision 6 写的
  「每条 update 帧的 `body_planner.name` 逐项相等」按字面执行会杀死本
  操作单自己规定的暂停初始化/追平流程——生产
  `track_loop.process_available` 每批只在最新帧运行 `_body_step`
  （`backlog_count = len(processed)-1` 写满全批，`skipped_count = 0 if
  is_latest else 1`），补追行合法地不带 `body_planner`。round 17 §B.3
  改为按这两个生产计数机械分类：`backlog_count`/`skipped_count` 必须是
  非 bool 非负整数；唯一 init 行两者为 0；每条 update 只能是
  **decision row**（`skipped_count=0`，必须有 `body_planner` mapping 且
  `name` 等于期望 planner，`backlog_count` 可 0 可正）或 **catch-up
  row**（`skipped_count=1` 且 `backlog_count>=1`，必须无 `body_planner`）；
  其他 skipped 值、`skipped=1/backlog=0`、catch-up 带 planner、decision
  缺 planner 均 fail closed，整条 run 至少一条 decision update。**不改
  `track_loop`、不改控制 cadence、不改 planner 决策**——只让分析器承认
  生产已经记录的「该行未执行 planner」。
- **N11 文字勘误**：`OFF_ROUTE_DERIVATION` 垂直情形公式改为
  `d·L/sqrt(d²+L²)`；`OFF_ROUTE_TOL_M = 0.501` 与生产重放结论不变。

revision 6 的其余落点（init/stage 唯一绑定与 planner 后置核对）全部保留。

**revision 6（2026-08-08）**：按 Acceptance round 15 §B 把 init 身份与
stage 唯一绑定——manifest `init.frame_id` 必须存在且为非 bool、`>=0` 的
整数；`frame_records` 中恰有一条 `compute_stage == "init"` 且其
`frame_id` 等于该 manifest 值，其余每条恰为 `"update"`（stage 缺失、
其他字符串、零条/多条 init、init ID 不符均 fail closed），至少保留一条
update；planner 身份只在该可信 stage 划分之后核对：唯一 init 行可缺
planner（存在则必须是 mapping 且 `name` 等于期望 planner），每条 update
必须是 mapping 且名称相等。revision 5 曾把「非 init 一律视作 update」
当作等价做法，那条路径可以把 update 行改标 init 来绕开 planner 核对，
本条起以本版为准；revision 5 的其余落点全部保留。

**revision 5（2026-08-08）**：按 Acceptance round 14 §B 四条闭合身份/
来源链——tracker 逐帧 `capture_monotonic_s` 强制存在、有限且与 truth
同帧字段差 ≤1e-9 s（缺字段即 fail closed）；arm 身份三层一致：仅从
十个冻结 ID 推导期望臂（A=hold/hold-v1、B=threshold/threshold-corridor-v1），
CLI `body_policy`、manifest `body_planner.policy` 与 `.planner`、每条
`compute_stage=update` 帧的 `body_planner.name` 逐项相等；compare 核对
analysis 内容归属路径（`receipt.run_id == 路径 ID`）、十份哈希两两
不同、`init_frame_id` 进跨 run 身份。revision 4 有一处声明曾过早
（「compare 机械拒绝重复」当时只覆盖 CLI ID 列表），本条起以本版为准。
revision 1–4 被判成立的落点（N7 清理、臂 A wiring、里程权重、遮挡排除、
applied effort、128 帧保留独立、生产转点容差、H2 指示量、自包含复算）
保留。

执行合同：`docs/proposals/P1-M3-BODY-001-first-body-motion-closed-loop.md`
Acceptance round 10 §B、round 11 §B、round 12 §B、round 13 §B 与
round 14 §B。**稳定候选经 Acceptance 确认并经独立 Review PASS 前，
零正式 Play、零 trial/ID/指标。**

## 1. 钉住项

| 项 | 冻结值 | 依据 |
|---|---|---|
| 载体 scenario | `config/scenario.default.json`，SHA-256 `f9c9205249aacf7487579ca42f727c766800cc329d0523ec82a96140564a2ce3`；`scenario_id=deterministic-loop-default` | BC-BODY1-2 |
| 激活方式 | 无 runtime override：`runtime/scenario_config.json`（SCENE-004，`00c8802a…b514`）在 Play 前移开并记录，`ScenarioConfig.Load()` 回退项目默认。**（revision 19 更正）该 override 在整个十次 Play 批次期间一直移开、从未恢复**（磁盘上只有 `runtime/scenario_config.p1-scene-004.hold.json`），原「trial 后恢复」自 A1 起即与事实不符：每一节 Play 前核对都要求该文件**缺席**，且带计时 HUD 的正是它——门 1 不再要求用户报暂停时刻就是这个原因。**批次期间不得恢复**：恢复即换载体，破坏 A/B 配对 | 同 1b 已验证路径；轮 58 据实更正 |
| 随机种子 | `random_seed: 0`（scenario 内冻结） | BC-BODY1-2；§5.1 配对 |
| 起点 | `route[0] = (125.5, 0.2, 117.5)`，`Configure` 每次 Play 同一 | BC-BODY1-2 |
| **本轮臂位 / planner（B，revision 19）** | **`--body-policy threshold`**：`ThresholdBodyPlanner`，planner 名 **`threshold-corridor-v1`**（`POLICY_PLANNER['threshold']`，本轮实跑确认）。**两臂构造同一 `WorldEstimateFilter`、走同一 `_body_step`/run-log 路径，差异仅 planner 实例**（该结构性事实逐字保留）；初始化期一次性 `hold_body()` 保留，位于 `_body_step` 之外。**臂 A 侧已完成**：`--body-policy hold` / `HoldBodyPlanner` / `hold-v1`，5/5 有效。**本行是 §1 唯一按臂取不同值的钉住项**，切换它即切换实验臂（下一行的 corridor 工件是**只在臂 B 生效**的启动门，但其值本身两臂同一） | round 11 §B.1；§5.1「只切换 planner」；轮 58 轮换 |
| **corridor 工件（臂 B 专属启动门，revision 19 新增）** | `config/p1-m3-body-001-corridor-prisms.json`，SHA-256 **`9e2956ad93a4a81cf638a913b9c806e1a316616bf090b125641d3f5c0b7fc800`**，**779** 条棱柱；由 `config/p1-m3-body-001.json` 的 `corridor.artifact_sha256` 钉住（本轮实测两者相等）。`track_loop` 只在 `policy_name == "threshold"` 分支加载并比对该哈希，不符即启动期 `ValueError`（**pre-tracker 失败：不消耗采集 ID，但消耗一次 one-Play GO**）。臂 A 五次 Play 从未触碰本项 | 轮 58 新增；`controller/track_loop.py` threshold 分支 |
| tracker | `nanotrack-v2`（冻结 `46747d8`），`runtime/models/nanotrack-v2` + `config/nanotrack-v2.models.json` | §5.1 配对 |
| 重锚定 | `--reanchor-config config/detector-reanchor.models.json`（两臂同） | §5.1 |
| 地平面 | `--ground-plane-y-m 0.2`（显式有限值，冻结场景常量） | §3.4；M2a 约束 |
| 冻结初始框 | **已取得并冻结（revision 8 / round 20 §A.4）**：init frame **`0`**；无真值像素框 **`(177, 195, 77, 73)`**（`min_side = 73 px`），由用户在 2026-08-09 尝试 1 暂停时确认，来源为图像 HSV 红色最大连通域，未读任何真值；归一化逐字为 **`0.2765625 0.40625 0.1203125 0.15208333333333332`**（项目 `pixels_to_norm` 口径，`norm_to_csrt_pixels` 往返 `(177,195,77,73)` 逐值相等）。全部 10 次 Play 逐字复用，**禁止**重新框选或用六位小数替代 | BC-BODY1-2；round 20 §A.4 |
| tracker 解释器/入口 | **`.venv-yoloe/bin/python -m controller.track_loop`（唯一合法）**；禁裸 `python3`、禁 `.venv-track`、禁直接文件入口 | round 20 §B.1 |
| Play 前环境预检 | `.venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json` 必须 `status=PASS` 且退出码 0（§3 步骤 0） | round 20 §B.5；工具路径 round 21 §B.2 |
| **暂停窗口（独立硬门）** | 用户报告的暂停时刻必须满足 **`2.000000 <= reported_sim_t < 10.000000`**（秒，仿真时间）。越界即 **`TRIAL_VOID_PAUSE_WINDOW_VIOLATION`**：保持暂停、不启动 tracker、不恢复 Play、退出并保全现场、回 Acceptance。**frame 0 匹配、框覆盖正常、里程测量窗不受影响，均不得覆盖该终态**；运行中不得申请例外 | round 25 §B.2 |
| **A1 采集 ID（attempt-4 替代）** | **`p1-m3-body-001-arm-a-trial-1-attempt-4`**，映射 canonical slot `p1-m3-body-001-arm-a-trial-1`，与原 B1 配对；旧 ID 永久拒绝，其他 attempt 后缀一律拒绝。原「唯一替代/其余九个 ID 逐字不变」自轮 42 起对 A2 失效（BC-BODY1-26 亦冻结 A2 替代）；十个采集 ID 的总表见下方「acquisition IDs」行 | round 29 §C.2；轮 56 返工 F5b 更正本行 |
| **本轮采集 ID（B5，revision 28）** | **`p1-m3-body-001-arm-b-trial-5`** —— canonical slot **即其自身**，与 **A5**（采集 ID `p1-m3-body-001-arm-a-trial-5`）配对。**从未被消耗**，无需替代 ID，**两个 predecessor 门都不触发**。机械确认（接受轮 73 实跑）：`canonical_trial_id()` 返回同名、**`_expected_policy()` 返回 `threshold`**、`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`、`expected_acquisition_ids('b')[4]` 逐字相等、`…-arm-b-trial-5-attempt-1` 与 `…-arm-b-trial-6` 均被 `run_id_not_frozen_trial` 拒绝、run 目录不存在。**这是本批次最后一次采集**；跑完臂 B 5/5、十次齐备，但 `--compare` **仍需单独授权**，不在批量 GO 内。**上一轮（已完成）**：B4，接受轮 71 判为有效，臂 B 4/5 | 批量 GO 2026-08-14；放行前置「先复核再放行 B5」（账本 2026-08-20，转述条目）已由复核轮 15 → 16 走完并通过；接受轮 73 |
| **（历史）B4 采集 ID（revision 23）** | **`p1-m3-body-001-arm-b-trial-4`** —— canonical slot **即其自身**，与 **A4** 配对。**从未被消耗**，无需替代 ID，**两个 predecessor 门都不触发**。机械确认（接受轮 67 实跑）：`canonical_trial_id()` 返回同名、**`_expected_policy()` 返回 `threshold`**、`expected_acquisition_ids('b')[3]` 逐字相等、`-attempt-N` 被拒、run 目录不存在。**上一轮（已完成）**：B3，接受轮 67 判为有效，臂 B 3/5 | 批量 GO 2026-08-14；接受轮 67 |
| **（历史）B3 采集 ID（revision 22）** | **`p1-m3-body-001-arm-b-trial-3`** —— canonical slot **即其自身**，与 **A3**（采集 ID `p1-m3-body-001-arm-a-trial-3`）配对。**从未被消耗**，无需替代 ID，**两个 predecessor 门都不触发**。机械确认（本轮实跑）：`canonical_trial_id()` 返回同名、**`_expected_policy()` 返回 `threshold`**、`expected_acquisition_ids('b')[2]` 逐字相等、`-attempt-N` 被 `run_id_not_frozen_trial` 拒绝、run 目录不存在。**上一轮（已完成）**：B2，接受轮 63 判为有效，臂 B 2/5 | 批量 GO 2026-08-14；接受轮 63 |
| **（历史）B2 采集 ID（revision 21）** | **`p1-m3-body-001-arm-b-trial-2`** —— canonical slot **即其自身**，与 **A2**（采集 ID `p1-m3-body-001-arm-a-trial-2-attempt-2`）配对。**从未被消耗**，无需替代 ID，**两个 predecessor 门都不触发**。机械确认（本轮实跑）：`canonical_trial_id()` 返回同名、**`_expected_policy()` 返回 `threshold`**、`expected_acquisition_ids('b')[1]` 逐字相等、`…-arm-b-trial-2-attempt-N` 被 `run_id_not_frozen_trial` 拒绝、run 目录不存在。**臂 B 无替代 ID 机制**（§5 零作废容错披露）。**上一轮（已完成）**：B1，接受轮 60 判为有效，臂 B 1/5 | 用户批量 GO 2026-08-14；接受轮 61 |
| **（历史）B1 采集 ID（revision 19）** | **`p1-m3-body-001-arm-b-trial-1`** —— canonical slot **即其自身**，与 **A1**（采集 ID `p1-m3-body-001-arm-a-trial-1-attempt-4`）配对。该 ID **从未被任何采集消耗**，**不需要**替代 ID，也**不触发**任何 predecessor 门。机械确认（本轮实跑）：`canonical_trial_id()` 返回同名、**`_expected_policy()` 返回 `threshold`**、**`expected_acquisition_ids('b')[0]`**（注意是 `[0]`，臂 B 从头开始）逐字相等、`…-arm-b-trial-1-attempt-N` 与 `…-arm-b-trial-6` 均被 `run_id_not_frozen_trial` 拒绝、run 目录不存在。**不得**加任何 `-attempt-N` 后缀——**臂 B 没有替代 ID 机制**（见 §5 的零作废容错披露）。**上一轮（已完成）**：A5 = `p1-m3-body-001-arm-a-trial-5`，revision 17，接受轮 55 判为有效，臂 A 5/5 收官 | 用户 GO 2026-08-14；接受轮 58 |
| **完成握手** | 只有 tracker **自然退出码 0** + stdout final JSON 指向同一采集 ID 的 `summary.json` + run 内 `metrics.final.json`/`summary.json` 均存在，Implementation 才可报 `TRACKER_AUTO_COMPLETE_CONFIRMED` 并请用户退出 Play。用户**不得**依据「一圈跑完」或 HUD 时间自行退出 | round 29 §C.3 |
| **Play 前记录时序** | 记录必须在**发令前**落盘于 `docs/unity-test-log.md`（由 Acceptance 写入）；发令时工作树只允许该一份未提交差异。**禁止** Play 后补写 | round 25 §B.3 |
| 测量窗 | 目标路线里程 `[0, 62.5 m]`（= `31.25 s` @ `2.0 m/s`），进遮挡弧即结束 `C_track|geom`/`C_quality`/H2 的窗；不按墙钟/步数 | BC-BODY1-2/-13 |
| 整圈定义域 | 同一 Play 继续到目标路线**首次完成一个闭环**（里程首次 ≥ 周长 `212.9706 m`），仅为 H1 整圈 `C_geom`；样本集由 `tools/analyze_m3_body.py` 按路线位置机械划定，域为 `[0, P)`（首圈值过滤）。**准入判据只有下界**：`final_mileage < P` → fail closed `trial_invalid_no_single_loop`。**`>= 2P` 上界已于接受轮 42 §A 明文撤下**（其数字形式从未进入任何已接受文件），代之以两条域完整性硬门：`unwrapped` 序列必须**非递减**（`loop_domain_unwrapped_backward_step`），且**首次闭环后不得再出现 `< P` 的样本**（`loop_domain_sample_below_perimeter_after_closure`，先于非递减判定，顺序按接受轮 43 §B.4 写死）。「恰好一个闭环」此后由样本域承担，**Play 跑多远都不再使 trial 作废**，第二圈及以后既不进 H1 也不影响准入 | round 11 §B.4 经接受轮 42 §A 修订；BC-BODY1-23；Review round 7 `CONFIRMED` |
| 可见弧工件 | `docs/evidence/P1-M3-BODY-001-scene-body-margin.json` SHA-256 `c72c9407…576d`，可见弧 SHA-256 `4fe2eea5…df55`；实跑不符唯一合法动作是回 Acceptance | BC-BODY1-2/-13 |
| watchdog | `--planned-duration-s 130.0`：仅 fail-closed 上限（整圈 106.4853 s + 裕量），**不定义任何指标边界**。**历史背景（revision 13 降级）**：轮 41 曾撤回原括注「远低于两圈 213 s」，因为在 `>= 2P` 上界仍在时，tracker 退出后只剩约 `81.6 s` 仿真时间预算；F2 落地后该上界已不存在，**post-tracker 停留时长不再影响 trial 准入**。§3 步骤 4 的「立即请用户退出」是操作纪律（BC-BODY1-29），不是准入门 | round 11 §B.4；轮 41 更正；轮 42 §A 之后降为背景 |
| trial 数 | 恰好 5 个/臂共 10 次 Play，首次 Play 前冻结 | BC-BODY1-13 |
| canonical slots | **十个 canonical slot 与配对顺序冻结**：`p1-m3-body-001-arm-a-trial-1..5` 与 `-arm-b-trial-1..5`，按序号配对 (Aᵢ, Bᵢ)。canonical ID **只**作为 analysis receipt 的 `canonical_trial_id` 字段出现，**不**用作目录名、CLI `--run-id` 或 compare 输入 | round 10 §B.2；round 30 §C.2 |
| acquisition IDs | **十个采集 ID**：A1 = `p1-m3-body-001-arm-a-trial-1-attempt-4`（原 A1 ID 已被 attempt-3 void 现场消耗，永久拒绝）；A2 = `p1-m3-body-001-arm-a-trial-2-attempt-2`（BC-BODY1-26 冻结替代；原 A2 ID 已被 attempt-1 void 现场消耗，`run_id_void_consumed` 永久拒绝）；其余**八**个采集 ID **等于**其 canonical slot。`runtime/runs/<acquisition-id>/` create-once；compare 机械拒绝重复/缺号/错臂/错序，并另检 canonical slot 去重 | round 29 §C.2；round 30 §C.2；轮 42 BC-BODY1-26（A2 替代；轮 56 返工 F5 更正本行） |
| 真值载体 | `runtime/m3_body_truth.jsonl`（`p1-m3-body-truth/v2`）：逐帧目标世界 `(x,y,z)`、几何可见性、truth box/中心、云台/系留饱和、投影 aspect、**机体实际位置与 plant `AppliedVelocity`**；每次 Play 截断重写；真值只进该文件，tracker/estimator/planner 只读 v3 帧与观测；首次分析把 truth 流与五类配置原始字节 create-once 收进 run 目录。`--verify` 对其余**八**个 run 只读 run 目录；**对 A1（attempt-4）与 A2（attempt-2）两个替代采集各另读 run 目录之外的 predecessor hold**（A1 → attempt-3 hold；A2 → attempt-1 void hold，BC-BODY1-27；只枚举文件名并取原始字节 SHA-256，不解析 void 内容、不算 void 指标） | round 11 §B.2；round 12 §B.2/§B.5；round 13 §B.3；round 33 §B.4 |
| 指标口径 | 全部权重为冻结路线里程（梯形权重含首尾边界补全）；`C_quality` 只取 `geometrically_visible` 窗内样本；effort = ∫‖v_applied‖dt（仿真时间差，暂停安全）；H2 = 同路线位置配对差 + 逐 run-pair 中位数，第三分量为冻结的 `1[min_side ≥ 20 px]` 指示量 | round 12 §B.3/§B.4/§B.5；round 13 §B.2 |
| 输入排除 | 1b 诊断帧、`runtime/frames.qual3-leftover-hold/` 与任何旧 `metrics.json`/旧 truth 均不进入输入 | round 10 §A；round 11 §A |

## 2. Play 前隔离（fail-closed，逐项记录）

### 2.0 Play 前记录的强制顺序（round 25 §B.3，逐字执行）

attempt 2 因「记录在采集开始时不存在于任何权威文件」而作废。自 revision 10
起按下列**四步顺序**执行，任何一步未完成即不得发令：

1. **(a)** 用户的新 GO 已由 Acceptance 逐字记入 `docs/authorizations.md`
   **并已提交**。
2. **(b)** 在该最终干净 HEAD `H` 上，Implementation 运行并**报告**：
   `git rev-parse HEAD`、空的 `git status --porcelain`、`git diff --name-only
   <BASE>..H` 的路径归因，以及 §3 步骤 0 预检的**退出码与完整 JSON**。
   **`<BASE>` 不再手写（revision 13 闭合 N26，遵 COORD-007 R7「可派生标识
   禁手写」）**：它等于 `docs/reviews/P1-M3-BODY-001.md` 中**最新一行**
   `passed_candidate:` 的 40 位 SHA，执行时现取，例如
   `grep '^passed_candidate:' docs/reviews/P1-M3-BODY-001.md | tail -1`
   （复核轮次只追加，最新一行 = 文件末行；原例示 `grep -m1` 取文件序第一行
   = 最旧，与规范句相反，复核轮 8 F4 判 CLASS_2，轮 56 返工更正）。
   （历史：`e438b97` 由 round 35 §C.1 作废，`6019f33` 由 Review round 7 的
   `passed_candidate` 取代；此后每轮通过自动前移，不再需要改本条。）

   > **trial 2 的已判定基线 delta —— 历史例示（revision 12 / round 39 §F，计数经
   > round 40 更正）。`<BASE>` 当时是 `6019f33`；B1 的 `<BASE>` 是 `408acd7`，路径集合
   > 与计数都不同，本段的「七个路径」与 inert 判定**不得套用于 B1**，(b) 的归因每轮
   > 现算，本段只示范格式**：该归因在 PLAY_GOVERNING 上**非空，共七个路径**。
   > 其中六个是 COORD-007 的文档自检工具及其测试（`check_docs.py`、
   > `check_role_writes.py`、已删除的 `rotate_docs.py` 与三个
   > `tests/test_*`）。接受角色已按
   > `P1-DETECT-001` qual-3 的先例判为
   > **`INERT_DELTA_MEASUREMENT_PATHS_BYTE_IDENTICAL`**，依据是测量侧
   > （`controller/`、`Assets/`、`config/`、`ProjectSettings/`、
   > `Packages/packages-lock.json`、`analyze_m3_body.py`、
   > `preflight_reanchor_env.py`）对 `6019f33` **逐字节相同**且六者
   > **无任何导入路径**。Implementation 报告该归因即可，**不必**为此停摆。
   > **但**：若 Play 之前上述测量侧路径出现**任何**字节改动，本归因立即
   > 失效，必须停下回 Acceptance 重判；step (d) 的"唯一未提交差异 =
   > `docs/unity-test-log.md`"**不放宽**。
   >
   > **第七个路径 = 本操作单文件自身（round 40 裁定，2026-08-13）**。
   > workflow §4.4 末句「该 work item 冻结集点名的操作单文件」按 COORD-007
   > R1 立法原文取**读法 1**：操作单文件本身入集。故
   > `docs/evidence/P1-M3-BODY-001-1c-preflight.md` 是 PLAY_GOVERNING 成员，
   > round 39 §F 的「恰六个路径」计数句**作废**。该第七条即 **revision 12
   > 本身**（接受角色按账本 2026-08-12 COORD-007 决策点 3 与 2026-08-13 GO
   > 撰写，就是本次 Play 正在执行的指令）。它**不并入**上面的 inert 类——
   > inert 的两条依据是代码论证，对本操作单不适用——而单独判为
   > **`RUNBOOK_DELTA_AUTHORED_UNDER_GO_NO_SEMANTIC_CHANGE_REVIEW_DEBT_
   > REGISTERED`**：CLI 代码块 19 行恰 1 行不同（`--run-id`）、冻结值 token
   > 零丢失、新增条款只增停条件不放宽门；**不阻断**本次 Play，但 revision 12
   > 的逐文件独立复核**仍欠**，挂在下一轮复核（提案 Acceptance round 40 §C）。
   >
   > **revision 19 起本条不得照抄（接受轮 58）**：跨臂轮换的 CLI 块**恰 2 行
   > 不同**（`--run-id` 与 `--body-policy`），而第二行**选择的是另一个 planner
   > 类**——`NO_SEMANTIC_CHANGE` 对它是假的，套用即是虚假归因。revision 19 的
   > 归因另立名字：
   > **`RUNBOOK_DELTA_ARM_ROTATION_A_TO_B_SEMANTIC_BY_DESIGN_UNDER_GO_
   > NO_GATE_RELAXATION_REVIEW_DEBT_REGISTERED`** —— 语义改变是**本次授权的
   > 目的本身**（用户 GO 点名臂 B），不是夹带：冻结值 token 零丢失、其余 17 个
   > CLI 参数逐字不变、新增 §2.16 与两条披露只增停条件、不放宽任何门、不新设
   > 任何数值门。round 40 关于「操作单文件本身是 PLAY_GOVERNING 成员」的裁定
   > 继续适用，故本修订使 PLAY_GOVERNING delta 非空，(b) 须如实报告。
3. **(c)** **Acceptance**（非 Implementation——后者对 Unity 日志只读）在
   **用户进 Play 之前**把上述值写入 `docs/unity-test-log.md`。
4. **(d)** 发令时刻，工作树**只允许**这一份尚未提交的 Unity 日志差异：
   `git diff --name-only` 必须**逐字只有** `docs/unity-test-log.md`。
   workflow §4.5 允许这种白名单文档差异。

**禁止**以「要保持工作树完全干净，所以 Play 后再补写记录」为由延迟落盘——
该时序证据不可事后重建。操作证据 §F.6 只**链接**这份事前日志，不另造第二
个相互矛盾的身份来源。

**BC-BODY1-21（round 40）**：(c) 记录写入后至本次 Play 结束期间，**任何角色
不得再修改本文件**。本文件已被裁定为 PLAY_GOVERNING 成员，任何改动都使 (c)
记录的 HEAD 失效，必须停下、回 Acceptance 重取 (c) 后才能发令。

**BC-BODY1-22（round 40）**：Play 期间发现本操作单文字有歧义或缺陷时，唯一
合法动作是 **fail closed 回 Acceptance**，不得就地修改操作单后继续——
revision 12 尚未经独立复核，就地修补等于把未复核文本变成当场协议。

### 2.1 1b 诊断现场隔离（**已执行**，2026-08-09）

**历史保全记录，非待执行动作。** 下列六项在 attempt 1 之前一次性完成
（移动，不删除），此后未再重复；本节不对未来任何 Play 发出指令。

1. `runtime/frames/` 内 1b 诊断帧（257 项）→ `runtime/frames.1b-diagnostic-hold/`；
2. `runtime/metrics.json`（1b 诊断遗留，schema 无 `run_id`）→
   `runtime/metrics.1b-diagnostic-hold.json`；
3. `runtime/m3_body_truth.jsonl` —— 当时**不存在**，「若存在」分支未触发；
4. `runtime/scenario_config.json`（SCENE-004 override）→
   `runtime/scenario_config.p1-scene-004.hold.json`；
5. `runtime/body_command.json`、`runtime/gimbal_command.json`、
   `runtime/tracking_observation.json` → `<stem>.1b-diagnostic-hold.<ext>`；
6. 当时核对通过：无 release pointer、无活动 qualification/scouting 标记。

移动前后 SHA-256 逐项相等，零删除、零覆盖、零分析；计数与哈希见
`docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md` §B。

> 当时第 6 项还核对了「无 `runtime/runs/p1-m3-body-001-arm-a-trial-1/`」，
> 该判定在 attempt 1 时点成立，但**已被 attempt 3 取代**（见 §2.4）。
> attempt 4 的 create-once 前置是 `…-attempt-4/` 不存在，见 §2.5。

### 2.2 attempt 1 现场保全（round 20 §B.3，**已执行**，2026-08-10）

**历史保全记录，非待执行动作。** attempt 1 作废后，下列三组在 attempt 2
之前完成（移动，不删除；移动前后计数/SHA-256 逐项相等）：

| # | 源（当时） | 目标 |
|---|---|---|
| 1 | `runtime/frames/`（attempt 1 的 46 帧 `frame_0000000000`–`frame_0000000045` + `latest.json`，共 93 项） | `runtime/frames.arm-a-trial-1-void-attempt-1-hold/` |
| 2 | `runtime/m3_body_truth.jsonl`（46 行，SHA-256 `64be7f8542461cc9709d5b80cab0c2d7b5ad661e51763c7185dd8b6fb6fa39f2`） | `runtime/m3_body_truth.arm-a-trial-1-void-attempt-1-hold.jsonl` |
| 3 | `runtime/metrics.json`（Unity `CoverageEvaluator` 产物，SHA-256 `d31af400306e40bf68ef242b6d819979ede9d49bedfc606904eac63c76e92e7e`） | `runtime/metrics.arm-a-trial-1-void-attempt-1-hold.json` |

当时成立并保留至今的结论：1b diagnostic hold 一字节未动，与本节 hold
不混淆不合并；void 工件**禁止删除、覆盖，禁止喂给
`tools/analyze_m3_body.py`**，也不得作为任何指标、窗口或标定的输入。

**旧 canonical ID `p1-m3-body-001-arm-a-trial-1` 的时间边界（round 33
§B.2）**：attempt 1 保全当时它**尚未被创建或消耗**，本节原文因此写过
「只能在新 GO 后由该次正式运行创建」——该表述**只适用于当时**。
attempt 3 已经创建并消耗了该 ID，其 run 目录已移入
`runtime/runs/p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold/`（§2.4）。
**当前与未来，该字符串一律不得再作为 acquisition ID 或 run 目录被创建**：
`analyze_m3_body.canonical_trial_id()` 对它抛 `run_id_void_consumed`，§1 的
acquisition-IDs 行与 §5 post-tracker 段同此结论。A1 唯一的 acquisition ID
是 **`p1-m3-body-001-arm-a-trial-1-attempt-4`**。

### 2.3 attempt 2 现场保全（round 25 §B.1，**已执行**）

attempt 2 作废（`TRIAL_VOID_PROTOCOL_DEVIATION_PRE_TRACKER`）后，其工件已
在 revision 10 批次中移入具名 hold（移动，不删除；目标移动前均不存在；
移动前后计数/SHA-256 与 attempt-2 证据 §G 相等）：

| 源 | 目标 | 计数 / SHA-256（前 = 后） |
|---|---|---|
| `runtime/frames/` | `runtime/frames.arm-a-trial-1-void-attempt-2-hold/` | **109 项**（54 json + 54 jpg + `latest.json`），帧号 0–53 |
| `runtime/m3_body_truth.jsonl` | `runtime/m3_body_truth.arm-a-trial-1-void-attempt-2-hold.jsonl` | **54 行**，`7acd7a76f7791aa2b4f685cd0e8c8e4c23b66b14d274a7db9380ed51e31ea64a` |
| `runtime/metrics.json` | `runtime/metrics.arm-a-trial-1-void-attempt-2-hold.json` | `f12ec0930382372dfc5e3b82251695fdca02ce0e7e307ed7343e49cd39922bbe` |

attempt-1 与 1b 的 hold 逐项复核不变；正式 run 目录仍不存在。两次 void 的
工件**禁止删除、覆盖、分析**，也不得作为任何指标/窗口/标定的输入。

未来 attempt 3 若产生新的 void 现场，按同一命名规律移入
`*.arm-a-trial-1-void-attempt-3-hold`，并在证据中记录计数/SHA。

### 2.4 attempt 3 现场保全（round 29 §C.1，**已执行**）

attempt 3 归因为 `TRIAL_VOID_PROTOCOL_DEVIATION_POST_TRACKER_EARLY_EXIT` 后，
七组工件已移入具名 hold（移动不删除；目标移动前均不存在；前后文件数/行数/
字节/SHA-256 逐项相等）：

| 源 | 目标 |
|---|---|
| `runtime/runs/p1-m3-body-001-arm-a-trial-1/` | `runtime/runs/p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold/` |
| `runtime/frames/` | `runtime/frames.arm-a-trial-1-void-attempt-3-hold/` |
| `runtime/m3_body_truth.jsonl` | `runtime/m3_body_truth.arm-a-trial-1-void-attempt-3-hold.jsonl` |
| `runtime/metrics.json` | `runtime/metrics.arm-a-trial-1-void-attempt-3-hold.json` |
| `runtime/body_command.json` | `runtime/body_command.arm-a-trial-1-void-attempt-3-hold.json` |
| `runtime/gimbal_command.json` | `runtime/gimbal_command.arm-a-trial-1-void-attempt-3-hold.json` |
| `runtime/tracking_observation.json` | `runtime/tracking_observation.arm-a-trial-1-void-attempt-3-hold.json` |

移动后只新建空 `runtime/frames/`；**不得预建** attempt-4 run 目录或其他
shared 文件。attempt-1/2/1b 的 hold 逐项复核不变。三次 void 的工件一律
**禁止删除、覆盖、分析**。将来若再出现 void 现场，按同一命名规律递增
`*-void-attempt-N-hold`。

### 2.5 attempt 4 的 Play 前状态核对（round 33 §B.3，**已执行**，2026-08-10）

**历史记录，非本轮待执行动作**（revision 12）。本节九项已在 attempt 4
之前逐项执行通过，attempt 4 随后完成并被接受轮 38 认定为有效 A1。
本轮（trial 2）的待执行核对是 **§2.6**；本节第 4–7 项的 hold 期望值仍是
**权威原表**，§2.6 按引用核对，不重抄哈希以免转写漂移。

§2.1–§2.4 全部是已执行的历史记录。**attempt 4 之前不需要、也不得再执行
任何移动或清理**——三次 void 与 1b 的保全都已完成，shared 槽位早已空出。

本节是**只读核对**，逐项要求下列状态；**任一项不符即停止并回 Acceptance，
禁止就地修正后继续**：

| # | 核对项 | 期望 |
|---|---|---|
| 1 | `runtime/body_command.json`、`runtime/gimbal_command.json`、`runtime/tracking_observation.json` | **均不存在** |
| 2 | `runtime/metrics.json`、`runtime/m3_body_truth.jsonl`、`runtime/scenario_config.json` | **均不存在**（后者不存在即确保 `ScenarioConfig.Load()` 回退项目默认） |
| 3 | `runtime/frames/` | **存在且为空**（0 项） |
| 4 | 1b diagnostic hold | `runtime/frames.1b-diagnostic-hold/` **257** 项；`metrics.1b-diagnostic-hold.json`、`scenario_config.p1-scene-004.hold.json`、`body_command.1b-diagnostic-hold.json`、`gimbal_command.1b-diagnostic-hold.json`、`tracking_observation.1b-diagnostic-hold.json` 五个 SHA-256 与 §B 证据相等 |
| 5 | attempt-1 hold | `frames.arm-a-trial-1-void-attempt-1-hold/` **93** 项；truth `64be7f85…39f2`（46 行）与 metrics `d31af400…` 与 §F.1 证据相等 |
| 6 | attempt-2 hold | `frames.arm-a-trial-1-void-attempt-2-hold/` **109** 项；truth `7acd7a76…`（54 行）与 metrics `f12ec093…` 与 §H.1 证据相等 |
| 7 | attempt-3 hold | `runs/p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold/` 恰两文件 `frames.jsonl`（755 行，`8f9f3551…16b5`）与 `manifest.json`（207 行，`e5caa982…8a65`）；`frames.arm-a-trial-1-void-attempt-3-hold/` **257** 项；truth `6e273895…`（627 行）、metrics `59085980…`、三个发布 hold 与 §I.1 证据相等 |
| 8 | 活动标记 | 无 release pointer（`release_command.accepted.json`、`release_ack.json`、`p1_detect_qualification_release.json`、`qualification-release-ready.json`）、无 scouting session/qualification 标记 |
| 9 | **attempt-4 create-once 前置** | **`runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4/` 不存在** |

第 9 项是 attempt 4 真正的 create-once 前置：`RunLogger` 以
`mkdir(parents=True, exist_ok=False)`（`controller/run_log.py:508`）创建该
目录，预先存在会在 tracker 启动期炸掉。**不得**改用旧 canonical
`runtime/runs/p1-m3-body-001-arm-a-trial-1/` 作为核对对象——那已是 attempt 3
的 void hold 源，且该 ID 已被消耗（§2.2、§5 post-tracker 段）。

### 2.6 arm A trial 2 首次采集的 Play 前状态核对（revision 12，**已执行**，2026-08-13）

**历史记录，非本轮待执行动作**（revision 13）。本节七项已在那次 Play 之前
逐项执行通过（67 条机械核对 67 PASS），该次 Play 随后被接受轮 41 判为
`TRIAL_VOID_LOOP_DOMAIN_UPPER_BOUND_VIOLATION_POST_TRACKER_DWELL`，其采集 ID
已消耗并永久拒绝。**本轮（attempt-2）的待执行核对是 §2.7**；本节第 3–6 项的
期望值仍是权威原表，§2.7 按引用核对，不重抄哈希以免转写漂移。

**本节是只读核对。本轮不需要、也不得执行任何移动、清理、重建或就地
修正**——A1 的 shared 槽位已由接受轮 37 §C.2 归档完毕，槽位现已空出。
**任一项不符即停止并回 Acceptance，禁止就地修正后继续。**

A1 的正式 run 目录、post-run 归档与三处 void hold 在本轮全部是**只读保全
对象**：不得移动、覆盖、删除，也不得作为 trial 2 的任何输入。

| # | 核对项 | 期望 |
|---|---|---|
| 1 | `runtime/body_command.json`、`gimbal_command.json`、`tracking_observation.json`、`metrics.json`、`m3_body_truth.jsonl`、`scenario_config.json` | **六项均不存在**（后者不存在即确保 `ScenarioConfig.Load()` 回退项目默认） |
| 2 | `runtime/frames/` | **存在且为空**（0 项） |
| 3 | 1b / attempt-1 / attempt-2 / attempt-3 四处 hold | **逐项等于 §2.5 第 4–7 项原表**（帧计数 **257 / 93 / 109 / 257**，各 truth 行数、metrics 与三个发布 hold 的 SHA-256 按该表核对） |
| 4 | **A1 正式 run 目录** | `runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4/` 存在且**恰 11 份文件**；只读复算 `--verify`（见下）退出码 0 且逐字返回 A1 冻结 JSON |
| 5 | **A1 post-run 归档** | `runtime/test-results/p1-m3-body-001-arm-a-trial-1-attempt-4-post-run/` 存在且**恰 6 项**（`frames/`、`m3_body_truth.jsonl`、`metrics.json`、`body_command.json`、`gimbal_command.json`、`tracking_observation.json`），逐项计数/SHA-256 按 `docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md` §N.1 原表核对 |
| 6 | 活动标记 | 同 §2.5 第 8 项：无 release pointer（`release_command.accepted.json`、`release_ack.json`、`p1_detect_qualification_release.json`、`qualification-release-ready.json`）、无 scouting session / qualification 标记 |
| 7 | **create-once 前置（当时的 ID）** | **`runtime/runs/p1-m3-body-001-arm-a-trial-2/` 不存在**（历史；该 ID 此后被该次 Play 消耗，本轮对应项见 §2.7 第 8 项） |

第 4 项的只读复算命令（`--verify` 在写盘前返回，确为只读；按模式名引用，
不钉行号）：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify \
  --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
```

stdout 必须逐字为：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
```

第 7 项是 trial 2 真正的 create-once 前置：`RunLogger` 以
`mkdir(parents=True, exist_ok=False)`（`controller/run_log.py:508`）创建该
目录，预先存在会在 tracker 启动期炸掉。

> **接受轮 39 实测（2026-08-13，零写入）**：上述 1/2/3/4/5/7 项在本轮全部
> 实测通过——六个 shared 文件均 absent、`runtime/frames/` 0 项、四处 hold
> 帧计数 257/93/109/257 相符、A1 run 目录 11 份文件且 `--verify` 逐字
> 复现上面的 JSON（退出码 0）、post-run 归档 6 项、
> `runs/p1-m3-body-001-arm-a-trial-2/` 不存在；`git status --porcelain`
> 复核为空。该实测**不替代**发令前由 Implementation 执行并落盘的本节核对。
>
> **披露（位置风险，非缺陷）**：A1 的 post-run 归档位于
> `runtime/test-results/` 下，该目录同时是 Unity Edit Mode 日志/XML 的
> 累积输出地（本轮 164 项）。同目录已有 `*-exchange` 保全先例，且写入为
> 新增具名条目而非清空，故本轮**不移动**该归档（移动保全证据属
> Implementation 动作，且会改变 §N.1 已记录的路径）。风险登记在案：
> 若将来有工具清空 `runtime/test-results/`，A1 的 shared 侧归档会丢失，
> 但正式 run 目录（第 4 项，独立于该路径）不受影响。

### 2.7 A2 attempt-2 的 Play 前状态核对（revision 13，**已执行**，2026-08-13）

**历史记录，非本轮待执行动作**（revision 14）。本节八项已在 A2 那次 Play 之前
逐项执行通过（54 条机械核对 54 PASS），该次采集随后被接受轮 47 判为**有效 A2**。
**本轮（A3）的待执行核对是 §2.10**，其前置是 §2.9 的归档。

**本节是只读核对。任一项不符即停止并回 Acceptance，禁止就地修正后继续。**
执行时机：§2.8 的保全移动**完成之后**、发令之前。A1 现场（正式 run 目录、
post-run 归档、三处 void hold）与新建的 attempt-1 void hold 在本轮全部是
**只读保全对象**：不得移动、覆盖、删除，也不得作为本次采集的任何输入。

| # | 核对项 | 期望 |
|---|---|---|
| 1 | `runtime/body_command.json`、`gimbal_command.json`、`tracking_observation.json`、`metrics.json`、`m3_body_truth.jsonl`、`scenario_config.json` | **六项均不存在**（§2.8 移动之后应当如此；`scenario_config.json` 不存在即确保 `ScenarioConfig.Load()` 回退项目默认） |
| 2 | `runtime/frames/` | **存在且为空**（0 项，由 §2.8 移动后新建） |
| 3 | 1b / attempt-1 / attempt-2 / attempt-3 四处旧 hold | **逐项等于 §2.5 第 4–7 项原表**（帧计数 **257 / 93 / 109 / 257**，各 SHA-256 按该表核对） |
| 4 | **A1 正式 run 目录** | `runtime/runs/p1-m3-body-001-arm-a-trial-1-attempt-4/` 存在且**恰 11 份文件**；只读复算 `--verify`（见下）退出码 0 且逐字返回 A1 冻结 JSON |
| 5 | **A1 post-run 归档** | `runtime/test-results/p1-m3-body-001-arm-a-trial-1-attempt-4-post-run/` 存在且**恰 6 项**，逐项计数/SHA-256 按 `docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md` §N.1 原表核对 |
| 6 | 活动标记 | 同 §2.5 第 8 项：无 release pointer（`release_command.accepted.json`、`release_ack.json`、`p1_detect_qualification_release.json`、`qualification-release-ready.json`）、无 scouting session / qualification 标记 |
| 7 | **attempt-1 void hold（新，N27 前移）** | `runtime/runs/p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold/` 存在，其**直接文件名集合恰为 §2.8 表列的十个**——**多一个隐藏文件（`.DS_Store` 等）即在此停止**，不得进 Play；三个钉住 SHA-256 与 §2.8 相等 |
| 8 | **attempt-2 create-once 前置** | **`runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2/` 不存在** |

第 4 项的只读复算命令（`--verify` 在写盘前返回，确为只读；按模式名引用，
不钉行号）：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify \
  --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
```

stdout 必须逐字为：

```json
{"disposition": "WITHIN_RANGE", "full_loop_c_geom": 0.5784550773737355, "run_id": "p1-m3-body-001-arm-a-trial-1-attempt-4", "verified": true, "window_c_track_given_geom": 1.0}
```

第 7 项把 N27 的脆性**前移到 GO 消耗之前**：`_check_a2_predecessor_hold` 对
hold 做**精确**十文件集合判等，若等到分析阶段才发现多出隐藏文件，GO 与采集 ID
都已消耗。故本项在 Play 之前先查一次；发现隐藏文件的唯一合法动作是删除该
**非本项目产物**的隐藏文件后重查（十个受保全文件一字节不得动），仍不符即回
Acceptance。

第 8 项是本次采集真正的 create-once 前置：`RunLogger` 以
`mkdir(parents=True, exist_ok=False)` 创建该目录，预先存在会在 tracker 启动期
炸掉。

### 2.8 attempt-1 void 现场保全（BC-BODY1-28 第 5 步，**已执行**，2026-08-13）

**历史记录**（revision 17 就地更正失效标注）。七组移动已在 A2 attempt-2 之前
执行完毕并逐项验证（前后计数/行数/字节/SHA-256 相等、两个目录聚合相等、十文件
hold 零隐藏项、BC-BODY1-33 门排练通过，证据 `…-arm-a-trial-2.md` §K）。
**本节不对未来任何 Play 发出指令。**

接受轮 42 §C 冻结的七组 source→destination，**每个 destination 移动前必须不
存在**；本节在 §2.7 之前执行，由 Implementation 操作：

| Source | Destination |
|---|---|
| `runtime/runs/p1-m3-body-001-arm-a-trial-2/` | `runtime/runs/p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold/` |
| `runtime/frames/` | `runtime/frames.arm-a-trial-2-void-attempt-1-hold/` |
| `runtime/m3_body_truth.jsonl` | `runtime/m3_body_truth.arm-a-trial-2-void-attempt-1-hold.jsonl` |
| `runtime/metrics.json` | `runtime/metrics.arm-a-trial-2-void-attempt-1-hold.json` |
| `runtime/body_command.json` | `runtime/body_command.arm-a-trial-2-void-attempt-1-hold.json` |
| `runtime/gimbal_command.json` | `runtime/gimbal_command.arm-a-trial-2-void-attempt-1-hold.json` |
| `runtime/tracking_observation.json` | `runtime/tracking_observation.arm-a-trial-2-void-attempt-1-hold.json` |

- 逐项记录移动前后文件数/行数/字节数/SHA-256 **相等**，零删除、零覆盖、
  零分析；移动后只新建**空** `runtime/frames/`，不得预建任何 run 目录。
- 并证明 A1 现场（11 份 / 6 项）与四处旧 hold 不变。
- **hold 的十文件精确集合（`_check_a2_predecessor_hold` 判等对象）**：
  `frames.jsonl`、`manifest.json`、`m3_body_truth.jsonl`、`metrics.final.json`、
  `summary.json`、`scenario.json`、`margin.json`、`body_config.json`、
  `reanchor_config.json`、`tracker_model_spec.json`。三个钉住 SHA-256
  （`frames.jsonl` = `a7939b7c…fc54`、`manifest.json` = `d9774905…a50c`、
  `m3_body_truth.jsonl` = `6f3e5238…f095`）在移动后必须仍然相等——字节不随
  路径变，不等即说明移动过程写坏了字节，停止并回 Acceptance。
- **隐藏文件（N27，预先写死）**：hold 目录内**不得**出现十个之外的任何常规
  文件，包括 `.DS_Store`。移动完成后立即核对一次，并在 §2.7 第 7 项再核对
  一次（GO 消耗之前）。删除误落的隐藏文件是允许的；十个受保全文件一字节
  不得动。
- **BC-BODY1-33 门排练**：移动完成后在**真实** hold 上只读复跑一次 A2 前驱门，
  方法是**直接调用 `_check_a2_predecessor_hold(Path('runtime'))`** 并观察其不抛
  异常；命令与逐字输出记入证据。**零 ID、零写盘、零 Play。**
  **勘误（接受轮 46）**：BC-BODY1-33（提案轮 42 §C）原括注说也可以跑
  `--run-id …-attempt-2` 「观察它越过前驱门后停在 `missing_run_directory`」——
  **该说法错误**：`analyze_trial` 的 `missing_run_directory` 检查排在两个前驱门
  **之前**（`analyze_m3_body.py` 内 `missing_run_directory` → `_check_a1/_a2_
  predecessor_hold` 的顺序），所以在 run 目录尚不存在时跑 CLI **证明不了**前驱门
  被走过。CLI 变体因此**不得**用作本排练的证据；直接调用是唯一合格方法。

### 2.9 A2（有效 trial）的 post-run 归档（revision 14，**已执行**，2026-08-13）

**历史记录**（revision 17 就地更正失效标注）。本节已在 A3 那次 Play 之前执行
完毕，移动前后逐项相等且 A2 `--verify` 归档后仍逐字复现（证据 §O.1）。
**本节不对未来任何 Play 发出指令**；**本文件当前待执行的 §2.x 节一律以最新修订抬头为准**（本注写于 revision 19 时指向 §2.16，当时属实；revision 22 起为 §2.19 → §2.20）。此处**不再写死具体节号**——同类指针已在两次轮换中失效两次（复核轮 10 P5/N37）。本节自身无归档待办。

A2 是**有效** trial，故走 **valid-trial 命名空间**（A1 先例，与 void hold 不同）：
**A2 的 run 目录 `runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2/`（11 份文件，
含 `m3_body_analysis.json`）绝对不动**——不移动、不改名、不覆盖。只把 A2 那次
Play 留在 shared 槽位的六项归档，给 A3 腾出空槽：

| Source | Destination（目录 `runtime/test-results/p1-m3-body-001-arm-a-trial-2-attempt-2-post-run/`） |
|---|---|
| `runtime/frames/` | `…-post-run/frames/` |
| `runtime/m3_body_truth.jsonl` | `…-post-run/m3_body_truth.jsonl` |
| `runtime/metrics.json` | `…-post-run/metrics.json` |
| `runtime/body_command.json` | `…-post-run/body_command.json` |
| `runtime/gimbal_command.json` | `…-post-run/gimbal_command.json` |
| `runtime/tracking_observation.json` | `…-post-run/tracking_observation.json` |

**移动前的钉住值（接受轮 48 实测，移动后必须逐项相等——字节不随路径变）**：

| 项 | 计数 | SHA-256 |
|---|---|---|
| `frames/` | **257** 项 | 聚合 `5af3b4d392cf08dd50fe188587f5b0b42015f63244cf47c3a0332bf2c4c76882`（口径同 §2.6 注：目录内每文件 `sha256  相对路径` 行排序后整体取 SHA-256） |
| `m3_body_truth.jsonl` | 773 行 / 796951 字节 | `79378d22cc8d05d3ccd9d6d6493551d3c27e7833e776b30c21ccfec31db0c2f6` |
| `metrics.json` | 61 行 / 2105 字节 | `194eebd71e029660fbbed8acdf50c0c57b2d1d650523be6611f53f0db6a55a8e` |
| `body_command.json` | 10 行 / 207 字节 | `223e7daf8ce2d7d19d01905f56757def8cbee248b9005d28f2a0919cfd1b5618` |
| `gimbal_command.json` | 15 行 / 340 字节 | `35c2f343763954ebd8b1d06f8c5c8345f6e7f84ff25682545cff7f2f07adccfd` |
| `tracking_observation.json` | 18 行 / 456 字节 | `44f789e57d9e282127e64eeb169e2e66d07980787297491d3f13ca07a6d4863d` |

- destination 目录移动前必须**不存在**；逐项记录移动前后计数/行数/字节/SHA-256
  **相等**，零删除、零覆盖、零分析。
- 移动后只新建**空** `runtime/frames/`，不得预建任何 run 目录。
- 移动后**复跑 A2 `--verify`**，必须仍退出 0 并逐字返回 A2 的冻结 JSON
  （`WITHIN_RANGE / 0.5783188398250908 / 1.0`）——run 目录自包含，归档 shared 侧
  不应影响它；不相等即停止并回 Acceptance。
- **位置风险（沿 §2.6 注登记，不新增动作）**：`runtime/test-results/` 同时是
  Unity Edit Mode 日志/XML 的累积输出地；写入为新增具名条目而非清空，故沿用
  A1 的先例不另择路径。若将来有工具清空该目录，A1/A2 的 shared 侧归档会丢失，
  但两者的正式 run 目录不受影响。

### 2.10 A3 的 Play 前状态核对（revision 14，**已执行**，2026-08-13）

**历史记录**（revision 15）。本节八项已在 A3 那次 Play 之前逐项执行通过
（57 条机械核对 57 PASS），该次采集随后被接受轮 50 判为**有效 A3**。
**本轮（A4）的待执行核对是 §2.12**，其前置是 §2.11 的归档。

**只读核对，在 §2.9 归档之后、发令之前执行。任一项不符即停止并回 Acceptance，
禁止就地修正后继续。** A1/A2 的正式 run 目录、两处 post-run 归档、四处旧 hold
与 attempt-1 void hold 在本轮全部是**只读保全对象**。

| # | 核对项 | 期望 |
|---|---|---|
| 1 | `runtime/body_command.json`、`gimbal_command.json`、`tracking_observation.json`、`metrics.json`、`m3_body_truth.jsonl`、`scenario_config.json` | **六项均不存在**（§2.9 之后应当如此；末项不存在即确保 `ScenarioConfig.Load()` 回退项目默认） |
| 2 | `runtime/frames/` | **存在且为空**（0 项，由 §2.9 重建） |
| 3 | 1b / attempt-1 / attempt-2 / attempt-3 四处旧 hold | **逐项等于 §2.5 第 4–7 项原表**（帧计数 **257 / 93 / 109 / 257**，各 SHA-256 按该表核对） |
| 4 | **A1 正式 run 目录** | 存在且**恰 11 份文件**；只读 `--verify` 退出 0 且逐字返回 A1 冻结 JSON（`0.5784550773737355`） |
| 5 | **A2 正式 run 目录** | `runtime/runs/p1-m3-body-001-arm-a-trial-2-attempt-2/` 存在且**恰 11 份文件**；只读 `--verify` 退出 0 且逐字返回 A2 冻结 JSON（`0.5783188398250908`） |
| 6 | **两处 post-run 归档** | A1 的**恰 6 项**（`frames/` 257）；A2 的**恰 6 项**且逐项等于 §2.9 钉住值 |
| 7 | 活动标记 + attempt-1 void hold | 八个具名标记均不存在；void hold 仍**恰 10 份文件、零隐藏项**，三个钉住 SHA 相等 |
| 8 | **A3 create-once 前置** | **`runtime/runs/p1-m3-body-001-arm-a-trial-3/` 不存在** |

第 4/5 项的只读复算命令（`--verify` 在写盘前返回，确为只读）：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-2-attempt-2
```

第 8 项是本次采集真正的 create-once 前置：`RunLogger` 以
`mkdir(parents=True, exist_ok=False)` 创建该目录，预先存在会在 tracker 启动期炸掉。

### 2.11 A3（有效 trial）的 post-run 归档（revision 15，**已执行**，2026-08-13）

**历史记录**（revision 17 就地更正失效标注）。本节已在 A4 那次 Play 之前执行
完毕，移动前后逐项相等且 A3 `--verify` 归档后仍逐字复现（证据 §R.1）。
**本节不对未来任何 Play 发出指令**；**本文件当前待执行的 §2.x 节一律以最新修订抬头为准**（本注写于 revision 19 时指向 §2.16，当时属实；revision 22 起为 §2.19 → §2.20）。此处**不再写死具体节号**——同类指针已在两次轮换中失效两次（复核轮 10 P5/N37）。本节自身无归档待办。

与 §2.9 同构（valid-trial 命名空间，A1/A2 先例）：**A3 的 run 目录
`runtime/runs/p1-m3-body-001-arm-a-trial-3/`（11 份，含 `m3_body_analysis.json`）
绝对不动**；只把 shared 侧六项归入
`runtime/test-results/p1-m3-body-001-arm-a-trial-3-post-run/`（destination 移动前必须不存在）。

**移动前的钉住值（接受轮 50 实测，移动后必须逐项相等）**：

| 项 | 计数 | SHA-256 |
|---|---|---|
| `frames/` | **257** 项 | 聚合 `505b94df06bc001fcd491b197199a9ecc79ab7313e2d93b4078311431bf35956` |
| `m3_body_truth.jsonl` | 751 行 / 774681 字节 | `3b38520f7a5c86e2a46c9f691c76d86b1220872206932eea0ef4c5bd966cee4e` |
| `metrics.json` | 61 行 / 2106 字节 | `b5cfca6d6f251de87829cff383a9deb1cb7c2ec4e11307912dff43e90a26c335` |
| `body_command.json` | 10 行 / 207 字节 | `48692462e9cc758b9c90ef3084c441a1c2b7d971c2a684ecb17406ac33d51eae` |
| `gimbal_command.json` | 15 行 / 341 字节 | `fe132ccdaeb09f4a8a7516802e9a20339f3cb59fd216cfe5e46d3917588705d0` |
| `tracking_observation.json` | 18 行 / 455 字节 | `02dc84ddf5055961031a0f886eb6f4c4aa0d0317d3dc9235ebc406ce694c5d0b` |

- 逐项记录移动前后计数/行数/字节/SHA-256 相等，零删除、零覆盖、零分析；
  移动后只新建**空** `runtime/frames/`，不得预建任何 run 目录。
- 移动后**复跑 A3 `--verify`**，必须仍退出 0 并逐字返回
  `WITHIN_RANGE / 0.597146417669116 / 1.0`。
- 位置风险沿 §2.9 登记，不新增动作。

### 2.12 A4 的 Play 前状态核对（revision 15，**已执行**，2026-08-13）

**历史记录**（revision 17）。本节七项已在 A4 那次 Play 之前逐项执行通过
（67 条机械核对 67 PASS），该次采集随后被接受轮 52 判为**有效 A4**。
**本轮（A5）的待执行核对是 §2.14**；A4 的归档（§2.13）已执行完毕，本轮无归档待办。

**只读核对，在 §2.11 之后、发令之前执行。任一项不符即停止并回 Acceptance。**

| # | 核对项 | 期望 |
|---|---|---|
| 1 | 六个 shared 文件（三个发布 + `metrics.json`/`m3_body_truth.jsonl`/`scenario_config.json`） | **均不存在** |
| 2 | `runtime/frames/` | **存在且为空**（0 项） |
| 3 | 1b / attempt-1 / attempt-2 / attempt-3 四处旧 hold | 帧计数 **257 / 93 / 109 / 257**，各 SHA 按 §2.5 原表 |
| 4 | **三个正式 run 目录** | A1、A2、A3 各**恰 11 份文件**；三条只读 `--verify` 各自退出 0 并逐字返回 `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` |
| 5 | **三处 post-run 归档** | A1/A2/A3 各**恰 6 项**，A3 的逐项等于 §2.11 钉住值 |
| 6 | 活动标记 + attempt-1 void hold | 八个具名标记均不存在；void hold 仍**恰 10 份、零隐藏项**，三个钉住 SHA 相等 |
| 7 | **A4 create-once 前置** | **`runtime/runs/p1-m3-body-001-arm-a-trial-4/` 不存在** |

第 4 项命令：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-2-attempt-2
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-3
```

### 2.13 A4（有效 trial）的 post-run 归档（revision 16，**已执行**，2026-08-13）

**历史记录**（revision 17）。本节已由实现角色执行完毕：移动前后计数/行数/字节/
SHA-256 逐项相等（`frames/` 257 项聚合 `281bb6d8…3b2c`、truth **1718** 行
`f9c1a488…e360`），移动后只重建空 `runtime/frames/`、未预建任何 run 目录，
四个有效 run 的 `--verify` 全部逐字复现（证据
`docs/evidence/P1-M3-BODY-001-arm-a-trial-2.md` §U）。**本轮无归档待办**；下一处
归档合同是 A5 结束后由接受角色另发修订冻结。

与 §2.9/§2.11 同构（valid-trial 命名空间）：**A4 的 run 目录
`runtime/runs/p1-m3-body-001-arm-a-trial-4/`（11 份，含 `m3_body_analysis.json`）
绝对不动**；只把 shared 侧六项归入
`runtime/test-results/p1-m3-body-001-arm-a-trial-4-post-run/`（destination 移动前必须不存在）。

**移动前的钉住值（接受轮 52 实测，移动后必须逐项相等）**：

| 项 | 计数 | SHA-256 |
|---|---|---|
| `frames/` | **257** 项 | 聚合 `281bb6d8f5b3657c203079654559d26cbb810c7eb231f8559b9120073d8a3b2c` |
| `m3_body_truth.jsonl` | **1718** 行 / 1755300 字节 | `f9c1a4889c0ba41f3058a8e8421b9961fda7084499e418eb5b7ba5a9a2c0e360` |
| `metrics.json` | 61 行 / 2085 字节 | `e5f547b71121b2a4e75a251003dfdc5880fc360648d8d4dd3bb4f82b5b116adf` |
| `body_command.json` | 10 行 / 207 字节 | `c1e5bf897cbd8a888773abb5ffc3c8463be0fee47d5b3fdff879192e8e0e3082` |
| `gimbal_command.json` | 15 行 / 341 字节 | `fc23a656f13c99da6bd96ab34ea9f38c5cb1a81b4190166a39350068b3cce62b` |
| `tracking_observation.json` | 18 行 / 454 字节 | `17d41cef97be83fbf0f319f390d92f2e8afa4cbe023357621d13faa5f1deecd6` |

- 逐项记录移动前后计数/行数/字节/SHA-256 相等，零删除、零覆盖、零分析；
  移动后只新建**空** `runtime/frames/`，**不得预建任何 run 目录**。
- 移动后**复跑 A4 `--verify`**，必须仍退出 0 并逐字返回
  `WITHIN_RANGE / 0.5783206310103214 / 1.0`；同时复跑 A1/A2/A3 三个 `--verify`
  确认四个有效 run 全部不受影响。
- **本节执行不释放任何 Play**：arm A trial 5 与臂 B 五次仍需用户逐字 GO，
  届时另发修订做槽位轮换并走 §2.0 四步。（**已兑现**：trial 5 的逐字 GO 于
  2026-08-13 入账，本 revision 17 即该次轮换。）
- 位置风险沿 §2.9 登记，不新增动作。

### 2.14 A5 的 Play 前状态核对（revision 17，**已执行**，2026-08-13）

**历史记录**（revision 18）。本节七项已在 A5 那次 Play 之前逐项执行通过（77 条
机械核对 77 PASS，发令时刻按 §V.4 第 3 条重取后结论不变），该次采集随后被接受轮
55 判为**有效 A5**，臂 A 5/5 收官。**（revision 19 更新）§2.15 已于 2026-08-14
执行完毕；**当前待执行的 §2.x 节以最新修订抬头为准**（revision 22 起为 §2.19 → §2.20）。**

**只读核对，在发令之前执行（本轮没有前置归档——§2.13 已执行完毕）。任一项不符
即停止并回 Acceptance，禁止就地修正后继续。** 四个正式 run 目录、四处 post-run
归档、四处旧 hold 与 attempt-1 void hold 在本轮全部是**只读保全对象**：不得移动、
覆盖、删除，也不得作为本次采集的任何输入。

| # | 核对项 | 期望 |
|---|---|---|
| 1 | 六个 shared 文件（三个发布 + `metrics.json`/`m3_body_truth.jsonl`/`scenario_config.json`） | **均不存在**（末项不存在即确保 `ScenarioConfig.Load()` 回退项目默认） |
| 2 | `runtime/frames/` | **存在且为空**（0 项，由 §2.13 重建） |
| 3 | 1b / attempt-1 / attempt-2 / attempt-3 四处旧 hold | 帧计数 **257 / 93 / 109 / 257**，各 SHA 按 §2.5 第 4–7 项原表；attempt-3 的 run hold 仍**恰两文件** |
| 4 | **四个正式 run 目录** | A1、A2、A3、A4 各**恰 11 份文件**；四条只读 `--verify` 各自退出 0 并逐字返回 `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` / `0.5783206310103214` |
| 5 | **四处 post-run 归档** | A1/A2/A3/A4 各**恰 6 项**；`frames/` 各 **257** 项，四个目录聚合 SHA-256（口径见 `…-arm-a-trial-2.md` §B.3）依次为 `ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` |
| 6 | 活动标记 + attempt-1 void hold | 八个具名标记均不存在；void hold 仍**恰 10 份、零隐藏项**，三个钉住 SHA 相等 |
| 7 | **A5 create-once 前置** | **`runtime/runs/p1-m3-body-001-arm-a-trial-5/` 不存在** |

第 4 项命令：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-2-attempt-2
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-3
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-4
```

第 7 项是本次采集真正的 create-once 前置：`RunLogger` 以
`mkdir(parents=True, exist_ok=False)` 创建该目录，预先存在会在 tracker 启动期炸掉。

> **接受轮 53 实测（2026-08-13，零写入、零 Play、零 ID）**：本节 1–7 项外加
> 采集 ID 的十项槽位机械核对在本轮由接受角色**独立实跑通过**（合计 58 条全 PASS，
> 详见提案接受轮 53 §B）。该实测**不替代**发令前由 Implementation 执行并落盘的
> 本节核对——两者互为独立复算。（**已兑现**：实现角色 §V.1 报 77/77，接受轮 54
> 在最终 HEAD 复跑 58/58，两侧无一项出入。）

### 2.15 A5（有效 trial）的 post-run 归档（revision 18，**已执行**，2026-08-14）

**历史记录**（revision 19）。本节已由实现角色执行完毕（commit `e68827d`）：移动前后
计数/行数/字节/SHA-256 逐项相等，接受轮 58 复测归档 `frames/` 聚合
`9dc67a76…a62b` = 轮 55 钉住值、`runtime/frames/` 0 项、六个 shared 文件全部缺席；
五个有效 run 的 `--verify` 归档后仍逐字复现。**本轮无归档待办**；下一处归档合同是
B1 结束后由接受角色另发修订冻结。

与 §2.9/§2.11/§2.13 同构（valid-trial 命名空间）：**A5 的 run 目录
`runtime/runs/p1-m3-body-001-arm-a-trial-5/`（11 份，含 `m3_body_analysis.json`）
绝对不动**；只把 shared 侧六项归入
`runtime/test-results/p1-m3-body-001-arm-a-trial-5-post-run/`（destination 移动前
必须不存在——接受轮 55 实测**当前不存在**）。

**移动前的钉住值（接受轮 55 实测，移动后必须逐项相等）**：

| 项 | 计数 | SHA-256 |
|---|---|---|
| `frames/` | **257** 项 | 聚合 `9dc67a7613201329b038ba6e425bc2e7aaa4ec7c9d196b09391c71624481a62b` |
| `m3_body_truth.jsonl` | **731** 行 / 751891 字节 | `a93ca5e0b2f67d164d8bfd079826ebef4d5328bb8e165e5362fe73f6c7bc80eb` |
| `metrics.json` | 61 行 / 2101 字节 | `1804dd6fb281e0a81bb2ace43886884b83861e2f324f3c20d4b2600ac50d4aa5` |
| `body_command.json` | 10 行 / 208 字节 | `c98b0b758935e7d0189614e5206713691d34123ab68a1f4af86388f100744256` |
| `gimbal_command.json` | 15 行 / 339 字节 | `02a3299abd8a862cbbc6d56a3e1f67b4529c8cf794a1e94fc988bb137146c5e6` |
| `tracking_observation.json` | 18 行 / 447 字节 | `215549ce0f94a859c548778fa3068a2e607aaac7176944d32d88a351b22f0649` |

（`m3_body_truth.jsonl` 的 SHA-256 与 A5 receipt 的
`input_sha256.m3_body_truth_jsonl` 逐字相等——归档的就是本次分析绑定的那份字节。
`runtime/scenario_config.json` 本轮全程不存在，无需处理。）

- 逐项记录移动前后计数/行数/字节/SHA-256 相等，零删除、零覆盖、零分析；
  移动后只新建**空** `runtime/frames/`，**不得预建任何 run 目录**。
- 移动后**复跑五个 `--verify`**（A1…A5），必须全部退出 0 并逐字返回各自冻结值
  `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` /
  `0.5783206310103214` / `0.5783243208518966`。
- **本节执行不释放任何 Play**：臂 B 五次仍需用户逐字 GO，届时另发修订做槽位与
  `--body-policy` 轮换并走 §2.0 四步；`--compare` 需十次齐备并单独授权。
  （**已兑现**：B1 的逐字 GO 于 2026-08-14 入账，revision 19 即该次跨臂轮换；
  臂 B 余下四次与 `--compare` 仍无 GO。）
- 位置风险沿 §2.9 登记，不新增动作。

### 2.16 B1 的 Play 前状态核对（revision 19，**已执行**，2026-08-14）

**历史记录**（revision 20）。本节九项已在 B1 那次 Play 之前逐项执行通过（115 条
机械核对 115 PASS，接受轮 59 独立复算 60/60 无出入），该次采集随后被接受轮 60 判为
**有效 B1**。**本注写于 revision 20 时属实；§2.17 已于 2026-08-14 执行完毕。**
**本文件当前的待执行节以最新修订抬头为准**（revision 22 起为 §2.19 → §2.20）。

**只读核对，在发令之前执行（本轮没有前置归档——§2.15 已执行完毕）。任一项不符
即停止并回 Acceptance，禁止就地修正后继续。** 本节九项的执行结果由 Implementation
落盘于 **`docs/evidence/P1-M3-BODY-001-arm-b-trial-1.md`**（与 §3 步骤 0′/门 1 同一
文件；revision 19 按 E 点的同类更正一并写明目的地）。 五个正式 run 目录、五处 post-run
归档、四处旧 hold 与 attempt-1 void hold 在本轮全部是**只读保全对象：不得移动、覆盖、删除，也不得作为本次采集的任何输入**（该禁令自 §2.6 起逐轮携带，revision 19 恢复完整表述）。

| # | 核对项 | 期望 |
|---|---|---|
| 1 | 六个 shared 文件（三个发布 + `metrics.json`/`m3_body_truth.jsonl`/`scenario_config.json`） | **均不存在**（末项不存在即确保 `ScenarioConfig.Load()` 回退项目默认；**批次期间不得恢复该 override**） |
| 2 | `runtime/frames/` | **存在且为空**（0 项，由 §2.15 重建） |
| 3 | 1b / attempt-1 / attempt-2 / attempt-3 四处旧 hold | 帧计数 **257 / 93 / 109 / 257**，各 SHA 按 §2.5 第 4–7 项原表；attempt-3 的 run hold 仍**恰两文件** |
| 4 | **五个正式 run 目录** | A1…A5 各**恰 11 份文件**；五条只读 `--verify` 各自退出 0 并逐字返回 `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` / `0.5783206310103214` / `0.5783243208518966` |
| 5 | **五处 post-run 归档** | 各**恰 6 项**；`frames/` 各 **257** 项，五个目录聚合 SHA-256（口径见 `…-arm-a-trial-2.md` §B.3）依次为 `ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` / `9dc67a76…a62b` |
| 6 | 活动标记 + attempt-1 void hold | 八个具名标记（四个 release pointer 见 §2.5 第 8 项；四个 scouting/qualification 标记见 `docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md` §B）均不存在；void hold 仍**恰 10 份、零隐藏项**，三个钉住 SHA 相等 |
| 7 | **B1 create-once 前置** | **`runtime/runs/p1-m3-body-001-arm-b-trial-1/` 不存在** |
| 8 | **臂 B 专属：corridor 工件** | `config/p1-m3-body-001-corridor-prisms.json` 实测 SHA-256 = `config/p1-m3-body-001.json` 的 `corridor.artifact_sha256` = **`9e2956ad…c800`**，**779** 条棱柱。**臂 A 五次从未验过本项**；不符即 tracker 启动期 `ValueError` |
| 9 | **臂 B 专属：臂位机械复核** | `_expected_policy('p1-m3-body-001-arm-b-trial-1')` 返回 **`threshold`**；`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`；`expected_acquisition_ids('b')[0]` 逐字相等；`…-attempt-N` 后缀被 `run_id_not_frozen_trial` 拒绝 |

第 4 项命令：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-2-attempt-2
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-3
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-4
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-5
```

第 7 项是本次采集真正的 create-once 前置：`RunLogger` 以
`mkdir(parents=True, exist_ok=False)` 创建该目录，预先存在会在 tracker 启动期炸掉。

第 8/9 项命令（**臂 B 专属，臂 A 五次从未跑过**；只读，不写任何文件）：

```bash
.venv-yoloe/bin/python -c "
import hashlib, json, pathlib, sys
cfg = json.load(open('config/p1-m3-body-001.json'))['corridor']
art = pathlib.Path(cfg['artifact_path'])
print('corridor sha256 =', hashlib.sha256(art.read_bytes()).hexdigest())
print('pin             =', cfg['artifact_sha256'])
print('instance_count  =', cfg['instance_count'])
sys.path.insert(0, 'tools'); import analyze_m3_body as A
print('_expected_policy =', A._expected_policy('p1-m3-body-001-arm-b-trial-1'))
print('planner name     =', A.POLICY_PLANNER['threshold'])
print('ids(b)[0]        =', A.expected_acquisition_ids('b')[0])
"
```

前两行必须逐字相等且等于 §1 的 `9e2956ad…c800`，`instance_count` 为 **779**；
后三行必须依次为 `threshold`、`threshold-corridor-v1`、
`p1-m3-body-001-arm-b-trial-1`。任一不符即停止并回 Acceptance。

> **接受轮 58 实测（2026-08-14，零写入、零 Play、零 ID）**：第 1–9 项外加采集 ID
> 的槽位机械核对已由接受角色**独立实跑通过**（详见提案接受轮 58）。该实测
> **不替代**发令前由 Implementation 执行并落盘的本节核对——两者互为独立复算。

### 2.17 B1（有效 trial）的 post-run 归档（revision 20，**已执行**，2026-08-14）

**历史记录**（接受轮 64 按复核轮 10 P4 补记）。本节已由实现角色执行完毕
（`b6dcf86`）：移动前后计数/行数/字节/SHA-256 逐项相等，六条 `--verify` 逐字复现，
复核轮 10 已在磁盘复验其钉住表（证据 `…-arm-b-trial-2.md` §A）。**本节自身无归档待办**；本文件当前的待执行节以最新修订抬头为准
（§2.19 亦已于 2026-08-14 执行完毕）。

与 §2.9/§2.11/§2.13/§2.15 同构（valid-trial 命名空间）：**B1 的 run 目录
`runtime/runs/p1-m3-body-001-arm-b-trial-1/`（11 份，含 `m3_body_analysis.json`）
绝对不动**；只把 shared 侧六项归入
`runtime/test-results/p1-m3-body-001-arm-b-trial-1-post-run/`（destination 移动前
必须不存在——接受轮 60 实测**当前不存在**）。

**移动前的钉住值（接受轮 60 实测，移动后必须逐项相等）**：

| 项 | 计数 | SHA-256 |
|---|---|---|
| `frames/` | **257** 项 | 聚合 `09f1ac615777a313109c1ed7feac2ec792de7d01951e56a4f90ec780428b524c` |
| `m3_body_truth.jsonl` | **858** 行 / 919046 字节 | `6addcf08d9fec807c21e7daff5300d885aa63deda5d3d26061eecfe10057935e` |
| `metrics.json` | 61 行 / 2057 字节 | `528ab2b925abd547108e88e04fbd04eb77f6bf6b117330218b98a53a6759b6ba` |
| `body_command.json` | 15 行 / 329 字节 | `b0e36adb0f4782a24e988658a752cb8f8262f5e9afc07f6c64a411912335456c` |
| `gimbal_command.json` | 15 行 / 341 字节 | `90fc33fef3919c5ccdd0445f09d1a99909b11d915a857fa9272b8c35e21bf55d` |
| `tracking_observation.json` | 18 行 / 438 字节 | `924728703d9664c8293d3baf89fc38eb7f84e63c1d1cdced91667455a5026e8c` |

（`body_command.json` 本轮是 **15 行 / 329 字节**，与臂 A 五次的 10 行 / 207–208
字节不同——臂 B 的指令包多出 `velocity_world_mps` 子对象，属设计使然。）

- 逐项记录移动前后计数/行数/字节/SHA-256 相等，零删除、零覆盖、零分析；
  移动后只新建**空** `runtime/frames/`，**不得预建任何 run 目录**。
- 移动后**复跑六个 `--verify`**（A1…A5 + B1），必须全部退出 0 并逐字返回各自冻结值
  （臂 A 五个见 §2.16 第 4 项；B1 = `SCENE_DEGENERATE / 1.0 / 1.0`）。
- **本节执行不释放任何 Play**：臂 B trial 2–5 仍需用户逐字 GO，且轮 60 的
  `SCENE_DEGENERATE` 决定尚未答复，**在答复前不得起草任何臂 B trial 2 前置**。
  （**已兑现 / 时间边界（接受轮 64）**：轮 60 的 `SCENE_DEGENERATE` 已由用户答复，
  2026-08-14 批量 GO 覆盖 B2–B5，本条两项自那时起终止效力；`--compare` 与任何
  重试/重进/调参仍无 GO。）
- 位置风险沿 §2.9 登记，不新增动作。

### 2.18 B2 的 Play 前状态核对（revision 21，**已执行**，2026-08-14）

**历史记录**（revision 22）。本节九项已在 B2 那次 Play 之前逐项执行通过（126 条机械
核对 126 PASS，接受轮 62 独立复算 62/62 无出入），该次采集随后被接受轮 63 判为
**有效 B2**。**本文件当前的待执行节以最新修订抬头为准**（本注写于 revision 22 时
指向 §2.19 → §2.20；两节均已于 2026-08-14 执行完毕）。

**只读核对，在 §2.17 之后、发令之前执行。任一项不符即停止并回 Acceptance，禁止
就地修正后继续。** 六个正式 run 目录、六处 post-run 归档、四处旧 hold 与 attempt-1
void hold 在本轮全部是**只读保全对象：不得移动、覆盖、删除，也不得作为本次采集的
任何输入**。本节结果由 Implementation 落盘于
**`docs/evidence/P1-M3-BODY-001-arm-b-trial-2.md`**（与 §3 步骤 0′/门 1/门 4 同一文件）。

| # | 核对项 | 期望 |
|---|---|---|
| 1 | 六个 shared 文件 | **均不存在**（§2.17 之后应当如此；`scenario_config.json` 批次期间不得恢复） |
| 2 | `runtime/frames/` | **存在且为空**（0 项，由 §2.17 重建） |
| 3 | 四处旧 hold | 帧计数 **257 / 93 / 109 / 257**，各 SHA 按 §2.5 第 4–7 项原表；attempt-3 的 run hold 仍**恰两文件** |
| 4 | **六个正式 run 目录** | A1…A5 + **B1** 各**恰 11 份**；六条只读 `--verify` 各退出 0 并逐字返回 `0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` / `0.5783206310103214` / `0.5783243208518966`，B1 = `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0` |
| 5 | **六处 post-run 归档** | 各**恰 6 项**；`frames/` 各 **257** 项，聚合依次 `ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` / `9dc67a76…a62b` / **`09f1ac61…524c`**（B1，§2.17 钉住值） |
| 6 | 活动标记 + attempt-1 void hold | 八个具名标记（出处见 §2.16 第 6 项）均不存在；void hold 仍**恰 10 份、零隐藏项**，三钉住 SHA 相等 |
| 7 | **B2 create-once 前置** | **`runtime/runs/p1-m3-body-001-arm-b-trial-2/` 不存在** |
| 8 | **臂 B 专属：corridor 工件** | 实测 SHA-256 = config `artifact_sha256` = §1 钉住值 `9e2956ad…c800`，**779** 条棱柱；`policy.tether_corridor_check` 仍为 `true` |
| 9 | **臂 B 专属：臂位机械复核** | `_expected_policy('…-arm-b-trial-2')` = `threshold`；`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`；`expected_acquisition_ids('b')[1]` 逐字相等；`…-attempt-N` 被 `run_id_not_frozen_trial` 拒绝 |

第 4 项 = §2.16 的五条臂 A 命令，**再加第六条（B1，本轮新增）**：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-1-attempt-4
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-2-attempt-2
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-3
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-4
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-a-trial-5
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-b-trial-1
```

**本轮采集 `…-arm-b-trial-2` 尚不存在，第 4 项不对它跑 `--verify`**；它在第 7 项
里被核对为「run 目录不存在」（create-once 前置）。

第 8/9 项：命令块同 §2.16，唯一改动是把 `_expected_policy(...)` 与
`expected_acquisition_ids('b')[...]` 的实参换成本轮的 `…-arm-b-trial-2` 与索引
**`[1]`**；corridor 部分逐字不变（两臂同一工件）。

### 2.19 B2（有效 trial）的 post-run 归档（revision 22，**已执行**，2026-08-14）

**历史记录**（revision 23）。

**历史记录**（接受轮 64 补记）。本节已由实现角色执行完毕（`29e903a`）：移动前后
计数/行数/字节/SHA-256 逐项相等（24/24），七条 `--verify` 逐字复现，`runtime/frames/`
已重建为空（证据 `…-arm-b-trial-2.md` §D；§2.20 时点的复验见 `…-arm-b-trial-3.md`
§A）。

与 §2.9/§2.11/§2.13/§2.15/§2.17 同构：**B2 的 run 目录
`runtime/runs/p1-m3-body-001-arm-b-trial-2/`（11 份）绝对不动**；只把 shared 侧六项
归入 `runtime/test-results/p1-m3-body-001-arm-b-trial-2-post-run/`（destination 移动前
必须不存在——接受轮 63 起草时实测不存在；已于 2026-08-14 移动完毕，移动前后逐项相等）。

**移动前的钉住值（接受轮 63 实测，移动后必须逐项相等）**：

| 项 | 计数 | SHA-256 |
|---|---|---|
| `frames/` | **257** 项 | 聚合 `71f65dca666cc37d91569a9b2b3893c0721e436a1b09756f5e644c0052a20f85` |
| `m3_body_truth.jsonl` | **800** 行 / 862952 字节 | `c2c985feed5d09bb7991fba6d3d28aadf2e0dfb90d3c63fba06b6fd551454df3` |
| `metrics.json` | 61 行 / 2057 字节 | `c60939ac59086b065fff39362a46b05bf745acf3b872b8946112b67e677e640e` |
| `body_command.json` | 15 行 / **328** 字节 | `d066e0b1a8d7103a62dc152440a6630d83b4445713b45183f5d074da45448fa5` |
| `gimbal_command.json` | 15 行 / 341 字节 | `516c2820e4b7623e8a2a8a8938a8b78495975e89b0beb8907b24288b2356d990` |
| `tracking_observation.json` | 18 行 / **458** 字节 | `82ffa1b52f714e325941290c5bca772b985b27cfa0e73210a94d8f0bcdf99463` |

（`body_command.json` 328 字节 vs B1 的 329、`tracking_observation.json` 458 vs 438：
臂 B 包内数值位数不同所致，**不是漂移**——判据是移动前后逐项相等，不是跨 trial 相等。）

- 逐项记录移动前后计数/行数/字节/SHA-256 相等，零删除、零覆盖、零分析；移动后只新建
  **空** `runtime/frames/`，**不得预建任何 run 目录**。
- 移动后**复跑七个 `--verify`**（A1…A5 + B1 + B2），全部退出 0 并逐字返回各自冻结值。
- 位置风险沿 §2.9 登记，不新增动作。

### 2.20 B3 的 Play 前状态核对（revision 22，**已执行**，两次复查各 136/136）

**历史记录**（revision 23）。B3 那次 Play 已执行并由接受轮 67 判为**有效**。
**本轮（B4）的待执行节依次是 §2.21（保全）与 §2.22（核对）。**

**只读核对，任一项不符即停止并回 Acceptance。** 七个正式 run 目录、七处 post-run
归档、四处旧 hold 与 attempt-1 void hold 全部是**只读保全对象：不得移动、覆盖、删除，
也不得作为本次采集的任何输入**。结果落盘于
**`docs/evidence/P1-M3-BODY-001-arm-b-trial-3.md`**。

| # | 核对项 | 期望 |
|---|---|---|
| 1 | 六个 shared 文件 | **均不存在**（§2.19 之后；`scenario_config.json` 批次期间不恢复） |
| 2 | `runtime/frames/` | **存在且为空**（0 项，由 §2.19 重建） |
| 3 | 四处旧 hold | **257 / 93 / 109 / 257**，各 SHA 按 §2.5 第 4–7 项原表；attempt-3 run hold 恰两文件 |
| 4 | **七个正式 run 目录** | A1…A5 + B1 + B2 各**恰 11 份**；七条 `--verify` 各退出 0 并逐字返回冻结值（臂 A 五个 `WITHIN_RANGE`；B1、B2 均 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`） |
| 5 | **七处 post-run 归档** | 各**恰 6 项**、`frames/` 各 **257** 项；聚合依次 `ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` / `9dc67a76…a62b` / `09f1ac61…524c` / **`71f65dca666cc37d91569a9b2b3893c0721e436a1b09756f5e644c0052a20f85`**（B2，§2.19 钉住值——**本项按 64 位全值核对，不用缩写**：revision 22 起草时把末四位误写成 `3a85`，复核轮 10 F7 判为 CLASS_2） |
| 6 | 活动标记 + attempt-1 void hold | 八个具名标记（出处见 §2.16 第 6 项）均不存在；void hold 仍**恰 10 份、零隐藏项**，三钉住 SHA 相等 |
| 7 | **B3 create-once 前置** | **`runtime/runs/p1-m3-body-001-arm-b-trial-3/` 不存在** |
| 8 | **臂 B 专属：corridor 工件** | 实测 SHA-256 = config `artifact_sha256` = §1 钉住值 `9e2956ad…c800`，**779** 条棱柱；`policy.tether_corridor_check` 仍 `true` |
| 9 | **臂 B 专属：臂位机械复核** | `_expected_policy('…-arm-b-trial-3')` = `threshold`；`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`；`expected_acquisition_ids('b')[2]` 逐字相等；`-attempt-N` 被 `run_id_not_frozen_trial` 拒绝 |

第 4 项 = §2.18 的六条，**再加第七条（B2）**：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-b-trial-2
```

**本轮采集 `…-arm-b-trial-3` 尚不存在，第 4 项不对它跑 `--verify`**；它在第 7 项被
核对为「run 目录不存在」。第 8/9 项命令块同 §2.16，实参换成本轮 ID 与索引 **`[2]`**。

### 2.21 现场按来源分离保全（revision 25，**已执行**，2026-08-20）

**结果落盘于 `docs/evidence/P1-M3-BODY-001-arm-b-trial-4.md`**（F13 补；先例见 §2.19，
与 §2.22 同一文件）。

**背景（轮 67 §C 起，经轮 68 与复核轮 13 两次更正）**：2026-08-20 有一次 Play 在
**没有任何放行**的情况下被进入（操作单未轮换、无该轮 (c)、(d) 不成立），用户误以为在
跑 B3。**tracker 未启动、无 run 目录、无采集 ID 被消耗、未到达任何 void 终态**，故批量
授权未被中止。**它造成的实际损失是**：`m3_body_truth.jsonl` 与 `metrics.json` **两项
全损**、`frames/latest.json` **一项**被覆盖；**B3 的 256 份保留帧（id 907…1034）与三个
发布文件字节完好**（依据与机制见 revision 25 抬头 A/C 条）。**B3 的完整 post-run 归档
（六项）仍永久不可能**，归档 7 处 < 有效 run 8 次不变。

**紧迫性**：B3 那 256 份帧只在「后续任何 Play 发布到 **frame id ≥ 1035**」之前存活
（写盘器按 id 淘汰，删除目标 = `publishedFrameId − 128`）；B3 自己那次就跑到 1034，
故**一次时长相当的 B4 在其尾段就会开始逐帧删除它们**。本节因此**先行执行**，不等
§2.22 及其复核放行——**但只能按下表的来源划分执行**。

**执行顺序：先 B 组（不可再生），后 A 组。** 移动不删除；**每个 destination 移动前
必须不存在**；由 Implementation 执行。

**B 组 —— B3 的 shared 侧残留（4 个 destination；命名与四处既有 hold 同构）**

| Source | Destination | 接受轮 69 移动前实测钉住值（全 64 位） |
|---|---|---|
| `runtime/frames/` 内 id **907…1034** 的 **256** 份（`frame_0000000907.*`…`frame_0000001034.*`） | `runtime/frames.arm-b-trial-3-shared-residue-hold/` | **256** 项 = **128** 个 id ×2；`bytes_total` **5513679**；聚合 `568b6b984376211b430ce1c016607e3cda3c3ba26c1ac43ef3ec4a1060d9a815`（口径见 `…-arm-a-trial-2.md` §B.3） |
| `runtime/body_command.json` | `runtime/body_command.arm-b-trial-3-shared-residue-hold.json` | **15** 行 / **331** 字节 / `f79bc73dc313debc2933cc457b1528c7e98e96e7f97d44adcb38ec9d79b05b84` |
| `runtime/gimbal_command.json` | `runtime/gimbal_command.arm-b-trial-3-shared-residue-hold.json` | **15** 行 / **341** 字节 / `6f9358d255f96b51ef91d9662f746616e4e1f8c457a8115ba7b9442cb2294bae` |
| `runtime/tracking_observation.json` | `runtime/tracking_observation.arm-b-trial-3-shared-residue-hold.json` | **18** 行 / **454** 字节 / `3c677ab693076af5c4c97eeff3786e743f583f0bd44141a7bc3a5bf056266bf4` |

**A 组 —— 2026-08-20 那次未放行 Play 的产物（3 个 destination）**

| Source | Destination | 接受轮 69 移动前实测钉住值（全 64 位） |
|---|---|---|
| `runtime/frames/` 内 id **0…28** 的 **58** 份 **加 `latest.json`** = **59** 项 | `runtime/frames.unreleased-play-20260820-hold/` | **59** 项 = **29** 个 id ×2 + `latest.json`；`bytes_total` **939238**；聚合 `39698be45e69d7d0c8cb1632f58f39cdf8972f5b1085a0031b1a65f5244d9a7f` |
| `runtime/m3_body_truth.jsonl` | `runtime/m3_body_truth.unreleased-play-20260820-hold.jsonl` | **29** 行 / **30300** 字节 / `7c6eb5f744f3c45e088e0e3322e2363193a557cae7bc1518537495bd90c3c75c` |
| `runtime/metrics.json` | `runtime/metrics.unreleased-play-20260820-hold.json` | **61** 行 / **2020** 字节 / `c3bb6f6da39953d1f3dbdfd0d4de8a926c11281bdfc970427f44a27c0b0d4a6d` |

**移动前必须做的两件事（fail-closed，任一不符即停止并回 Acceptance）**：

1. **重测七项钉住值**（两个聚合 + 五个文件的行数/字节/SHA-256）。不等即意味着现场在
   接受轮 69 之后又被写过（例如又一次未放行的 Play），属新事件，**不得就地继续**。
2. **归属复核（复核 N43，本轮新增；聚合相等证明不了归属）**：按 **frame id 段**与
   **包内 `capture_unix_s`** 复核两组划分——`runtime/frames/` 内 id 恰好只落在
   `[0, 28]` 与 `[907, 1034]` 两段、**两段之间无任何文件**、合计恰 **315** 项；
   `frame_0000001034.json` 的 `capture_unix_s` = **`1786939588.328`**（2026-08-17）、
   `frame_0000000028.json` 的 = **`1787250613.018`**（2026-08-20）、`latest.json` 的
   `frame_id` = **28**。**出现任何第三段 id、或时戳与所属组不符，即停止并回
   Acceptance。**

**移动后**：

- `runtime/frames/` **恰 0 项**（315 = 256 + 59 全部移出）；**目录本身保留，不删除、
  不新建**——`scenario_config.json` 批次期间同样不恢复。
- 七个 destination 逐项等于上表（计数/行数/字节/SHA-256），两个目录的 id 段与移动前
  一致。
- **复跑八个 `--verify`**（A1…A5 + B1 + B2 + B3），全部退出 0 且逐字返回各自冻结值
  ——**这是本节的承重核对**：它证明保全动作没有碰到任何已判定 run 的字节。
- **执行完即停**：§2.22、§2.0 (b)/(c) 依用户 2026-08-20 的放行条件等复核结论。

**其他约束**：

- **不分析、不 `--finalize`、不计入任何 trial**：A 组不是采集，其产物**永不**作为任何
  run 的输入；B 组是 B3 的残留，B3 已由轮 67 判定，**保全不改变任何已判结果**，也
  **永远不会**补齐为一份完整归档。
- **非门事实登记**：`runtime/road_scene_audit.json` 与 `runtime/route_corridor_audit.json`
  的 mtime 同为 2026-08-20 14:30（该次 Play 重写），但两者**从不属于**六项 shared
  成员、**从未进过任何归档**、每次 Play 都会被重写，故**本节不动它们**；其 mtime
  **不得**被读作批次期间存在额外 Play 的证据。

### 2.22 B4 的 Play 前状态核对（revision 25，**已执行**，2026-08-20，156/156）

> **历史记录（revision 28 补标，接受轮 73 自查发现本节轮换时漏标）。** 本节十项已在 B4
> 那次 Play 之前执行通过（**156/156**，前后跑两遍），该次采集随后由接受轮 71 判为
> **有效 B4**（臂 B 4/5），复核轮 15 已覆盖。**本轮（B5）的待执行节是 §2.24。**
> 下面这条执行前置属**已消费的历史条款**，**不得再照字面执行**：它写的是 B4 那次的
> 放行条件（用户裁定 2026-08-20，复核轮 13 → 14 走完）。B5 有它自己的、同样已满足的
> 前置——见 revision 28 抬头 A 条。

> **（历史）执行前置（用户裁定 2026-08-20，账本同日条目）**：本节不得在独立复核轮 13
> 给出结论之前执行。用户把一轮独立复核前置为 B4 的放行条件；§2.22、§2.0 (b) 与 (c)
> 一并等该结论。**§2.21 不在推迟之列**（风险不对称，理由见接受轮 68 §F）。

**只读核对，任一项不符即停止并回 Acceptance。** 八个正式 run 目录、七处 post-run
归档、四处旧 hold、attempt-1 void hold、§2.21 A 组新建的三处 unreleased hold 与 B 组新建的
**四处 B3 shared 残留 hold** 全部是**只读保全对象**。结果落盘于
**`docs/evidence/P1-M3-BODY-001-arm-b-trial-4.md`**。

| # | 核对项 | 期望 |
|---|---|---|
| 1 | 六个 shared **文件**（三个发布 + `metrics.json` / `m3_body_truth.jsonl` / `scenario_config.json`；口径同 §2.16 第 1 项，**与 §2.21 及本表第 5 项的「六项 shared 成员」不是同一集合**——后者含 `frames/` 而不含 `scenario_config.json`，`frames/` 在本表由第 2 项单列） | **均不存在**（§2.21 之后；`scenario_config.json` 批次期间不恢复） |
| 2 | `runtime/frames/` | **存在且恰 0 项**（315 项已由 §2.21 全部移出；目录本身未删除、未新建） |
| 3 | 四处旧 hold | **257 / 93 / 109 / 257**，各 SHA 按 §2.5 第 4–7 项原表；attempt-3 run hold 恰两文件 |
| 4 | **八个正式 run 目录** | A1…A5 + B1 + B2 + **B3** 各**恰 11 份**；八条 `--verify` 各退出 0 并逐字返回冻结值（臂 A 五个 `WITHIN_RANGE`；B1/B2/**B3** 均 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`） |
| 5 | **七处 post-run 归档** | 各**恰 6 项**、`frames/` 各 **257** 项，聚合依次 `ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` / `9dc67a76…a62b` / `09f1ac61…524c` / `71f65dca…0f85`。**注意：完整归档数（7）少于有效 run 数（8）——差额恒为 B3**：其六项归档源中的 `m3_body_truth.jsonl` 与 `metrics.json` **两项全损**、`frames/` 损 `latest.json` **一项**，被 2026-08-20 那次未放行 Play 覆盖而永久不存在，故**完整归档永久不可能**（轮 67 §C 记 6/6、轮 68 记 3/6 均为高估，复核轮 13 F12 改正）。B3 仅存的 **256 份帧 + 三个发布文件**由 §2.21 B 组保全为四处 `…arm-b-trial-3-shared-residue-hold` 平铺 hold，**均不在 `test-results/` 下、不是归档、不计入本项的 7**（见第 10 项）。**这不是缺项，不得据此判不符。** |
| 6 | 活动标记 + attempt-1 void hold | 八个具名标记（出处见 §2.16 第 6 项）均不存在；void hold 仍**恰 10 份、零隐藏项**，三钉住 SHA 相等 |
| 7 | **unreleased hold（§2.21 A 组）** | 三个 destination 均存在并逐项等于 §2.21 A 表的全 64 位钉住值：`frames.unreleased-play-20260820-hold/` **恰 59** 项（id **0…28** 共 29 个 ×2 + `latest.json`，聚合 `39698be4…9a7f`）、`m3_body_truth.…-hold.jsonl` **29** 行 / **30300** 字节、`metrics.…-hold.json` **61** 行 / **2020** 字节。**并集出处（N45）**：本项与第 10 项两个目录的 `shasum -a 256 *` 行合并排序后再取 SHA = `274e9804098c337d02245c64780c349c5c886c6633e4d8e7e1364d8da3e52d4c` = §2.21 执行前整目录的聚合（复核轮 13 亲测、轮 14 与其续会话各复算一次）——这是把移动前后用哈希连起来的唯一等式，证明 315 项零丢失、零改名、零字节改动；**分组正确性另由两个分组聚合与 id 段/mtime/包内 `capture_unix_s` 支撑，不由本等式承担**（复核轮 14 收工补记 3） |
| 8 | **B4 create-once 前置** | **`runtime/runs/p1-m3-body-001-arm-b-trial-4/` 不存在** |
| 9 | **臂 B 专属** | corridor 实测 SHA = config `artifact_sha256` = §1 钉住值 `9e2956ad…c800`，**779** 条棱柱，`tether_corridor_check` 仍 `true`；`_expected_policy('…-arm-b-trial-4')` = `threshold`、`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`、`expected_acquisition_ids('b')[3]` 相等、`-attempt-N` 被拒 |
| 10 | **B3 shared 残留 hold（§2.21 B 组，四处平铺）** | 四个 destination 均存在并逐项等于 §2.21 B 表的全 64 位钉住值：`frames.arm-b-trial-3-shared-residue-hold/` **恰 256** 项（id **907…1034** 共 128 个 ×2，**无 `latest.json`**，聚合 `568b6b98…a815`）、`body_command.…-hold.json` 15 行 / **331** 字节、`gimbal_command.…-hold.json` 15 行 / 341 字节、`tracking_observation.…-hold.json` 18 行 / **454** 字节。**四者都不是 post-run 归档**，不计入第 5 项的 7 处；命名与四处既有 void hold 同构（复核 N42） |

第 4 项 = §2.20 的七条，**再加第八条（B3）**：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-b-trial-3
```

**本轮采集 `…-arm-b-trial-4` 尚不存在，第 4 项不对它跑 `--verify`**；它在第 8 项被
核对为「run 目录不存在」。

### 2.23 B4（有效 trial）的 post-run 归档（revision 27，**已执行**，2026-08-21）

**结果落盘于 `docs/evidence/P1-M3-BODY-001-arm-b-trial-5.md`**（先例 §2.19：在下一
trial 的预备批次执行、落盘于下一 trial 的证据文件）。

与 §2.9/§2.11/§2.13/§2.15/§2.17/§2.19 同构：**B4 的 run 目录
`runtime/runs/p1-m3-body-001-arm-b-trial-4/`（11 份）绝对不动**；只把 shared 侧六项归入
`runtime/test-results/p1-m3-body-001-arm-b-trial-4-post-run/`（destination 移动前必须
不存在——接受轮 71 起草时实测**不存在**）。

**为什么现在就起草**：shared 槽位此刻装着 B4 的产物。B3 的教训是——一次误入的 Play
会当场覆盖 truth 与 metrics，且**不可恢复**（B3 的帧只是侥幸躲过按 id 淘汰）。
**在归档执行之前不得进入任何 Play。**

**移动前的钉住值（接受轮 71 实测，移动后必须逐项相等）**：

| 项 | 计数 | SHA-256（全 64 位） |
|---|---|---|
| `frames/` | **257** 项（128 帧 ×2 + `latest.json`，id 段 `[724, 851]`） | 聚合 `5ed64cf58350926ee1d2e6edf0b0a04300d7d6595865d38b40fec1be86597ebf`（口径见 `…-arm-a-trial-2.md` §B.3） |
| `m3_body_truth.jsonl` | **852** 行 / **914667** 字节 | `c6218bdefe3b0fc362af8543cecbfcc3bc838f7c4f615b384150f8af8f3d09d3` |
| `metrics.json` | **61** 行 / **2054** 字节 | `43a5db7db4c758ed775ebdd9a45236fe4d75781cb498a6337dfb97ee34704b74` |
| `body_command.json` | **15** 行 / **328** 字节 | `5a13b98671b2b34f858572ad455bd6a16ffdc60492ad0f74ff55efc894f80044` |
| `gimbal_command.json` | **15** 行 / **342** 字节 | `90ae396176c385e352881e028ce5a5ed6a8d2e14562a4fa13a5ef7726836cd19` |
| `tracking_observation.json` | **18** 行 / **459** 字节 | `e583a0d0cfa8842a071605fa8d039f5aa28c668b7403363f6a4fb94985b277d9` |

- 逐项记录移动前后计数/行数/字节/SHA-256 相等，**零删除、零覆盖、零分析**；移动后只
  新建**空** `runtime/frames/`，**不得预建任何 run 目录**。
- 移动后**复跑九个 `--verify`**（A1…A5 + B1 + B2 + B3 + B4），全部退出 0 并逐字返回
  各自冻结值。
- **§2.21 的两处保全 hold 不得触碰**（`frames.arm-b-trial-3-shared-residue-hold/` 256 项
  与 `frames.unreleased-play-20260820-hold/` 59 项），它们**不是** post-run 归档，
  不计入归档处数。归档执行后归档处数 **8**、有效 run **9**——差额仍恒为 B3。
- **本节之后不自动接 B5**：槽位轮换与 B5 的 Play 前核对**尚未起草**，待用户就
  「B5 之前是否再走一轮独立复核」给出指示后另发修订（接受轮 71 §G）。

### 2.24 B5 的 Play 前状态核对（revision 28，**已执行**，2026-08-21，155/155）

> **历史记录（revision 29）。** 本节十一项已在 B5 那次 Play 之前执行通过
> （**155/155**，预检前后各一遍），该次采集随后由接受轮 74 判为**有效 B5**，
> **臂 B 收于 5/5**。**本轮的待执行节是 §2.25**；§3 的采集步骤已无下一次执行对象。

**只读核对，任一项不符即停止并回 Acceptance，禁止就地修正后继续。** 结果落盘于
**`docs/evidence/P1-M3-BODY-001-arm-b-trial-5.md`**（与 §2.23 同一文件）。
九个正式 run 目录、八处 post-run 归档、四处旧 hold、attempt-1 void hold 与 §2.21 的
**七处保全 hold**全部是**只读保全对象：不得移动、覆盖、删除，也不得作为本次采集的
任何输入**。

| # | 核对项 | 期望 |
|---|---|---|
| 1 | 六个 shared **文件**（三个发布 + `metrics.json` / `m3_body_truth.jsonl` / `scenario_config.json`；口径同 §2.16 第 1 项，**与「六项 shared 成员」不是同一集合**——后者含 `frames/` 而不含 `scenario_config.json`） | **均不存在**（§2.23 之后；`scenario_config.json` 批次期间不恢复） |
| 2 | `runtime/frames/` | **存在且恰 0 项**（由 §2.23 重建为空） |
| 3 | 四处旧 hold | **257 / 93 / 109 / 257**，各 SHA 按 §2.5 第 4–7 项原表；attempt-3 run hold **恰两文件** |
| 4 | **九个正式 run 目录** | A1…A5 + B1 + B2 + B3 + **B4** 各**恰 11 份**；**九条 `--verify`** 各退出 0 并逐字返回冻结值（臂 A 五个 `WITHIN_RANGE`；**B1/B2/B3/B4 均 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`**） |
| 5 | **八处 post-run 归档** | 各**恰 6 项**、`frames/` 各 **257** 项，聚合依次 `ea9ba050…2fb3` / `5af3b4d3…6882` / `505b94df…5956` / `281bb6d8…3b2c` / `9dc67a76…a62b` / `09f1ac61…524c` / `71f65dca…0f85` / **`5ed64cf5…7ebf`**（B4，§2.23 钉住值）。**注意：归档 8 处 < 有效 run 9 次，差额恒为 B3**（其六项归档源中 `m3_body_truth.jsonl` 与 `metrics.json` 两项全损、`frames/` 损 `latest.json` 一项）——**这不是缺项，不得据此判不符** |
| 6 | 活动标记 + attempt-1 void hold | 八个具名标记（出处见 §2.16 第 6 项）均不存在；void hold 仍**恰 10 份、零隐藏项**，三钉住 SHA 相等 |
| 7 | **§2.21 A 组（unreleased hold）** | `frames.unreleased-play-20260820-hold/` **恰 59** 项、id 段 `[0,28]` + `latest.json`、`bytes_total` **939238**、聚合 `39698be4…9a7f`；`m3_body_truth.…-hold.jsonl` **29** 行 / **30300** B；`metrics.…-hold.json` **61** 行 / **2020** B |
| 8 | **§2.21 B 组（B3 shared 残留）** | `frames.arm-b-trial-3-shared-residue-hold/` **恰 256** 项、id 段 `[907,1034]`、**无 `latest.json`**、`bytes_total` **5513679**、聚合 `568b6b98…a815`；三个平铺发布件 hold **15 / 331**、**15 / 341**、**18 / 454** B。**七处保全 hold 都不是归档**，不计入第 5 项的 8 处 |
| 9 | **并集等式（N45）** | 第 7、8 项两个目录的 `shasum -a 256 *` 行合并排序后再取 SHA = **`274e9804098c337d02245c64780c349c5c886c6633e4d8e7e1364d8da3e52d4c`**（§2.21 执行前整目录聚合）。**该等式只证 (SHA, 文件名) 多重集不变，不证分组**——分组由第 7/8 项的 id 段与各自聚合承担 |
| 10 | **B5 create-once 前置** | **`runtime/runs/p1-m3-body-001-arm-b-trial-5/` 不存在**（`RunLogger` 以 `mkdir(exist_ok=False)` 创建，预先存在会在 tracker 启动期炸掉） |
| 11 | **臂 B 专属** | corridor 实测 SHA = config `artifact_sha256` = §1 钉住值 `9e2956ad…c800`、**779** 条棱柱、`tether_corridor_check` 仍 `true`；`canonical_trial_id('…-arm-b-trial-5')` 返回自身、`_expected_policy` = `threshold`、`POLICY_PLANNER['threshold']` = `threshold-corridor-v1`、`expected_acquisition_ids('b')[4]` 逐字相等、`…-trial-5-attempt-1` 与 `…-trial-6` 均被 `run_id_not_frozen_trial` 拒绝 |

第 4 项 = §2.22 的八条，**再加第九条（B4）**：

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --verify --run-id p1-m3-body-001-arm-b-trial-4
```

**本轮采集 `…-arm-b-trial-5` 尚不存在，第 4 项不对它跑 `--verify`**；它在第 10 项被核对为
「run 目录不存在」。

> **接受轮 73 实测（2026-08-21，零写入、零 Play、零 ID）**：上表十一项已由接受角色
> **独立实跑通过**（详见提案接受轮 73 §B）。该实测**不替代**发令前由 Implementation
> 执行并落盘的本节核对——两者互为独立复算（§2.16 / 轮 58 先例）。

### 2.25 B5（有效 trial）的 post-run 归档（revision 29，**本轮唯一待执行节**）

**结果落盘于 `docs/evidence/P1-M3-BODY-001-arm-b-trial-5.md`**（§D 新节）。**注意与前几轮
不同**：本轮**没有下一 trial**（臂 B 已 5/5），故落盘地是 B5 自己的证据文件，不是「下一
trial 的文件」——§2.19 的先例在此自然终止。

与 §2.9/§2.11/§2.13/§2.15/§2.17/§2.19/§2.23 同构：**B5 的 run 目录
`runtime/runs/p1-m3-body-001-arm-b-trial-5/`（11 份）绝对不动**；只把 shared 侧六项归入
`runtime/test-results/p1-m3-body-001-arm-b-trial-5-post-run/`（destination 移动前必须
不存在——接受轮 74 起草时实测**不存在**）。

**为什么仍要先做**：shared 槽位此刻装着 B5 的产物。B3 的教训不因「这是最后一次采集」
而失效——一次误入的 Play 会当场覆盖 truth 与 metrics 且不可恢复。**归档执行之前不得
进入任何 Play。**

**移动前的钉住值（接受轮 74 实测，移动后必须逐项相等）**：

| 项 | 计数 | SHA-256（全 64 位） |
|---|---|---|
| `frames/` | **257** 项（128 帧 ×2 + `latest.json`，id 段 `[614, 741]`） | 聚合 `dcabe43b43b2366d898be70c94a64eef01788c55a73fc9e4b4b6e1c7d680b814`（口径见 `…-arm-a-trial-2.md` §B.3） |
| `m3_body_truth.jsonl` | **742** 行 / **806547** 字节 | `6ea05d88c83cfaac13fe9af7b92a0fb5eb5c868a592104057c8151f037da11bd` |
| `metrics.json` | **61** 行 / **2057** 字节 | `024acc1349245a2ad0e32653401123197ba140702206f3852fb117b1a622b3ec` |
| `body_command.json` | **15** 行 / **329** 字节 | `8d95690b572895a49460ed9527992dbbacb192895b12181b04d8eace7fd87006` |
| `gimbal_command.json` | **15** 行 / **342** 字节 | `b19644e915e8b8f842aa0097d4bab0689ed63c0f45fbae4d3520d848bd440637` |
| `tracking_observation.json` | **18** 行 / **458** 字节 | `70f7c699e9e9f100b3263fc078253dd41418bc8b8fac1651703041de579933f2` |

- 逐项记录移动前后计数/行数/字节/SHA-256 相等，**零删除、零覆盖、零分析**；移动后只
  新建**空** `runtime/frames/`，**不得预建任何 run 目录**。
- 移动后**复跑十个 `--verify`**（A1…A5 + B1…B5），全部退出 0 并逐字返回各自冻结值。
- **§2.21 的七处保全 hold 不得触碰**；它们**不是** post-run 归档。归档执行后归档处数
  **9**、有效 run **10**——差额仍恒为 B3。
- **`--compare` 不在本节范围内**，且**不因十次齐备而自动获得授权**：它需要用户**单独
  逐字授权**（批量 GO 明确不覆盖）。**Implementation 不得在归档批次里顺手跑它。**

## 3. 操作步骤（用户执行 Play；Implementation 操作 tracker）

0. **环境预检（round 20 §B.5，先于任何 Play 步骤，fail-closed）**。在将要
   驱动 tracker 的**同一解释器**下运行：

   ```bash
   .venv-yoloe/bin/python tools/preflight_reanchor_env.py --reanchor-config config/detector-reanchor.models.json
   ```

   必须退出码 0 且 stdout JSON `status == "PASS"`（成功时 stdout 只有这一个
   JSON 对象，可直接 `json.loads`）。该工具严格解析 config schema 与
   NanoTrack spec；对 **cv2/torch/torchvision/ultralytics 四个包**比较原始
   `__version__` 与配置 pin **逐字相等**（不规范化、不剥 `+local`，故
   `2.13.0+cpu` 在 pin 为 `2.13.0` 时 fail closed）；构造冻结 NanoTrack-v2
   （含 OpenCV 版本门与 backbone/neckhead 两个 SHA-256）；并**实际构造
   `YoloeProposer` 与 `DinoV2Embedder`**（覆盖 YOLOE 权重、DINOv2 归档/
   逐文件源码/LICENSE/权重的全部哈希）。任一失败非零退出，**不得进
   Play**，回 Acceptance。仅「import 成功」不算 PASS。

   预检前后机械比对并要求完全相等：`runtime/runs/` **直接子目录名集合**，
   以及 `runtime/body_command.json`、`runtime/gimbal_command.json`、
   `runtime/tracking_observation.json`、`runtime/metrics.json` **各自的
   存在状态、字节大小与 SHA-256**；任何创建、删除或字节变化即非零退出。
   cv2 的 pin 取 NanoTrack spec 的 `opencv.tested_version`（唯一可能与
   `cv2.__version__` 相等的字段；`opencv.package_pin` 是 requirement
   specifier，永不相等）——此读法已披露待 Acceptance 确认。

0′. **解释器绑定的记录型条款（revision 12，零代码、零阈值改动）**。
   §1 已把唯一合法入口冻结为 `.venv-yoloe/bin/python -m controller.track_loop`，
   但该约束此前只是散文——预检把 `sys.executable` 写进输出 JSON
   （`preflight_reanchor_env.py:378-379`）却**没有任何机制**把该值绑定到
   之后真正启动 tracker 的解释器（COORD-007 §4.2）。本轮起 Implementation
   必须执行并**落盘记录**下列两步，缺任一步即不得进 Play：

   1. 从步骤 0 的预检 stdout JSON 取 `interpreter.executable` 的**逐字值**，
      记入**本轮采集的证据文件**——其路径**以当轮 §2.x Play 前核对节开头具名的
      落盘地为准**（该节由当轮修订抬头指定；例如 revision 22 的 §2.20 具名
      `docs/evidence/P1-M3-BODY-001-arm-b-trial-3.md`）。**本节不写死具体文件名**：
      revision 12 曾写死「trial 2 证据文件」、revision 19 改写死为 B1，两次都在轮换后
      失效（复核轮 10 F9）；接受轮 64 一度改用「采集 ID 去前缀」的机械导出规则，
      **该规则对臂 A 为假**（A1 的采集 ID 带 `-attempt-4` 后缀，A3/A4/A5 与 A2 共用
      一个证据文件），故改用单一事实源指向。这是**启动 tracker 的硬前置**，指错文件
      等于条款落空；
   2. 启动 tracker 时，命令行首的解释器路径必须与该值**字符串逐字相等**，
      并把实际执行的完整命令行原文一并记入证据。两者不等即
      **fail closed 回 Acceptance**，不得就地改命令后继续。

   **这不是 COORD-007 §4.2 要求的机器断言**（那是 R10，未授权且属代码）：
   本条只保证不相等时**有据可查且必须停**，不能阻止操作员写错后继续。

1. 用户在 Unity Editor 6000.4.1f1 打开
   `Assets/SimplePoly City - Low Poly Assets/Demo/SimplePoly City - Low Poly Assets_Demo Scene.unity`，
   Game 视图激活，**进入 Play 恰好一次**；本 run ID 下退出后不得重进。
2. 用户尽早**暂停**并报告「已暂停」。Implementation 依次机械核对**三个
   独立硬门**，任一不满足即按其终态停止，**互不覆盖**：

   > **接受轮 47 更正（零门改动）**：本步此前要求用户「报告暂停时刻」。
   > 冻结载体 `config/scenario.default.json` **没有计时 HUD**（带 HUD 的是
   > SCENE-004 的 runtime override，§1 明令 Play 前移开），用户因此**无法**
   > 读到该时刻——A1 口报「5S 左右」、attempt-2 口报「看不见 HUD」都是这个
   > 原因。而门 1 的判据**本来就**只认保留帧机械导出值（revision 12 记录型
   > 条款），口报从不是判据。故本步只要求用户报告**已暂停**；若用户能看到
   > 时刻可一并报告，仅作时序记录。**门 1 的阈值与导出口径逐字不变。**

   **门 1 — 暂停窗口（round 25 §B.2，逐字）**：报告的暂停时刻必须满足

   ```text
   2.000000 <= reported_sim_t < 10.000000
   ```

   （秒，仿真时间；实测取保留帧中最大 `simulation_time_s`）。越界即
   **`TRIAL_VOID_PAUSE_WINDOW_VIOLATION`**，唯一动作是：**保持暂停、不启动
   tracker、不恢复 Play**，请用户退出 Play，按 §2.3/§2.4 的命名**规律**保全现场——**臂位与序号一律取 §1「本轮采集 ID」行**，形如 `*.<本轮采集 ID 的臂位与序号>-void-attempt-1-hold`；**不得**沿用 §2.3 表列的 `arm-a-*` 名字（那是臂 A 的历史现场），**也不得**沿用任何前一轮的 ID（复核轮 10 F9：写死 B1 会以一个**有效** trial 之名保全现场，伪造其作废外观）——回
   Acceptance。**门 2/门 3 通过、或「测量窗按里程不受暂停时刻影响」，都不得
   覆盖本终态**；**运行中不得申请例外**（attempt 2 即因 `10.854090` 越界
   而作废）。

   **门 1 的记录型条款（revision 12，零代码、零阈值改动）**：`reported_sim_t`
   **不得**取用户口报的 HUD 时刻（attempt 4 的口报是「5S 左右」，与磁盘
   实测 `6.381126` 并不相同——见 `…-arm-a-trial-1.md` §N.3）。它必须由
   Implementation 从**保留帧**机械导出（本括注为既有口径：取保留帧中最大
   `simulation_time_s`，字段由 `SensorFrameWriter.cs:261` 写入），且
   **导出命令原文、保留帧编号范围、导出的数值本身**三项必须在**启动
   tracker 之前记入**本轮采集的证据文件**（落盘地同步骤 0′ 第 1 步：以当轮 §2.x
   核对节具名者为准，**不写死具体文件名**——复核轮 10 F9）。**未落盘即不得启动
   tracker。**

   **披露：本条款不消除 COORD-007 §4.1 的缺口。** 保留帧导出的
   `reported_sim_t` 是暂停真实时刻的**下界**——末帧写盘之后、暂停生效
   之前的不足一帧时间不可见（attempt 4：frame 31 @ `6.381126 s`，均值约
   `0.206 s/帧`）。故「末帧 `9.97` 通过门 1，而真实暂停在 `10.03`」仍可
   逐字发生。消除它需 §4.1 的遥测写入 + 启动前断言，即 **R10（未授权、
   属代码）**。本轮**不**因此调整 `[2.000000, 10.000000)`——BC-BODY1-15 (d)
   与反调参纪律禁止在此时改阈值。

   **门 2 — 最低保留帧**：必须恰为 `0`，否则 fail closed 回 Acceptance。

   **门 3 — 冻结框匹配**：Implementation 用 `--dump-frame 0` 导出 frame 0
   并叠加**已冻结**的像素框 `(177,195,77,73)`，用户只做**匹配/不匹配目检**。
   **不重新框选、不重新估框、不做六位小数化。** 不匹配即 fail closed 回
   Acceptance，不得现场调整。

   三门全部通过后，Implementation 在**保持暂停**下以逐字冻结值启动 tracker：
   `--init-frame 0 --init-box 0.2765625 0.40625 0.1203125 0.15208333333333332`
   （CLI 见 §4）。

   **门 4 —— 启动前命令行核对（revision 19 新增，只增停条件）**。跨臂轮换使
   `--body-policy` 成为本批次史上第一个被改动的第二参数，而**启动前没有任何机制
   核对它**：步骤 0′ 只比对解释器路径，§2.16 第 9 项只验"分析器期望什么"，都不看
   实际敲下去的命令行。写错的后果**不对称且不可逆**——run 目录一旦 create-once
   建成，采集 ID 即消耗，而臂 B **没有替代 ID**：
   - `--body-policy` 误写 `hold` → 臂身份三层核对在**分析期** fail-closed
     （`arm_policy_not_frozen_expectation`），此时 Play 已跑完、slot 已烧掉；
   - `--run-id` 误写 → 同样是 run 目录已建之后才暴露。

   故按下回车**之前**，Implementation 必须把**实际将要执行的完整命令行原文**记入
   本轮证据文件，并逐字核对它同时包含下列两个 token 序列：

   ```text
   --body-policy threshold
   --run-id p1-m3-body-001-arm-b-trial-5
   ```

   **否定项（revision 27 收编，接受轮 71）**。自 B2 起 Implementation 每轮都自愿
   多跑一组否定核对，四轮全过；本修订把它们写进本门，**只增停条件，不放宽任何既有
   判据**。命令行**不得**含下列任何一项：`arm-a-`、本批次前几轮的 run-id、
   `-attempt-`、`--compare`、**指向 hold 的 token**。

   > **`hold` 一项必须按命名规约判，不得按裸子串判（接受轮 71 裁定）**：
   > `threshold` 字面就含 `hold`，而 `--body-policy threshold` 恰是本门**要求存在**
   > 的肯定项，故裸子串判法对臂 B **恒为假阳性**，会把本门变成不可能通过。
   > **判据**：token 含 `-hold`，或以 `hold` 结尾且**不等于** `threshold`。
   > 真出现 `*-hold` 的 run-id 或路径仍会被抓到。B2/B3/B4 三轮报的 `hold` False
   > 与本判据一致，**属追认既有做法，不是本轮放宽**。

   任一不符即**不得启动**，回 Acceptance。本门**零阈值、零指标**，只把一次不可
   恢复的手误挡在 run 目录创建之前；它**不改变**门 1/2/3 的任何判据。
3. 恢复 Play，不再暂停。tracker 追平保留帧后逐帧发布观测；**本轮（臂 B）每个 decision 帧
   （`skipped_count=0`，见步骤 5 的分类；追平期的 catch-up 行合法地不带
   `body_planner`）经同一 `_body_step` 由 `ThresholdBodyPlanner`（`threshold-corridor-v1`）按其滞回与
   corridor 规则发布 hold 或 `velocity_world`**——臂 B 的 Play 会让机体真的动
   （首次出现在 B1）。
   （臂 A 侧已完成：同一 `_body_step` 由 `HoldBodyPlanner` 每帧发布 hold。）
4. **完成握手（round 29 §C.3，逐字执行）**。目标完成闭环后
   **用户继续保持 Play，不得自行退出**——不得依据「一圈已跑完」或 HUD
   时间判断完成。tracker 继续到 watchdog `--planned-duration-s 130.0`
   （仿真时间语义不变）自动完成。Implementation 必须同时观察到下列**三项**
   才可逐字报告 **`TRACKER_AUTO_COMPLETE_CONFIRMED`** 并请用户退出 Play：

   1. tracker 进程**自然退出码 `0`**（非信号终止、非人工终止）；
   2. stdout 的 final JSON 指向**同一采集 ID** 的 `summary.json`；
   3. run 目录内 `metrics.final.json` 与 `summary.json` **均已存在**。

   **确认词的唯一机械来源（round 30 §C.4）**——不得人工复述，必须由下列
   只读命令 PASS 产生：

   ```bash
   .venv-yoloe/bin/python tools/analyze_m3_body.py --validate-completion \
     --runtime runtime \
     --run-id p1-m3-body-001-arm-b-trial-5 \
     --tracker-exit-code 0 \
     --tracker-final-json '<track_loop 最后一行 JSON 原文>'
   ```

   该模式**只读、不写任何文件、不调用 `finalize_run`**，AND 门包括：exit code
   恰为 `0`；final JSON 为对象且 `run_id` 等于采集 ID；其 `summary` 解析到该
   run 目录的 `summary.json`；manifest 同 ID；`summary.json` 与
   `metrics.final.json` 均存在；summary 的 `metrics_snapshot_present` 为
   `true` 且 `actual_duration_s >= 130.0`。任一不满足即非零具名 fail closed，
   按 §5 的 post-tracker void 处置。只有该命令退出 0 并输出
   `TRACKER_AUTO_COMPLETE_CONFIRMED`，Implementation 才可转述该词并请用户
   退出 Play。

   **BC-BODY1-29（revision 13，F4，零数值门）**：确认词产生后，
   Implementation 的**下一个动作必须是请用户退出 Play**——读 run 记录、
   写证据、写状态一律在用户退出**之后**；用户收到请求后**尽快**退出。
   本条不设任何时间上限（F2 落地后停留时长已不影响 trial 准入，见 §1
   watchdog 行），它只消除不必要的停留并留下可核对的顺序。

   用户退出 Play 后报告 Console 有无报错。（watchdog 只是上限，不定义任何
   指标边界；是否恰好一圈仍由离线机械判定。）
5. Implementation 运行
   `.venv-yoloe/bin/python tools/analyze_m3_body.py --run-id p1-m3-body-001-arm-b-trial-5`：
   工具先把共享 truth 流与 scenario/margin/body config/re-anchor/
   tracker spec 五类原始字节 create-once 收进 run 目录（此后共享文件
   被覆盖/删除不影响本 run），再机械核对 run 绑定（run_id、manifest
   schema、scenario/hash、arm policy↔planner、tracker 身份与双模型
   SHA、re-anchor 身份、condition/track、地平面、初始框、truth 逐条
   scenario_id 与逐帧 capture 绑定、首末帧、样本数、run-bound 输入
   SHA-256）、闭环恰好一次、窗口/整圈定义域，把 receipt 与全部复算量
   写入 run 目录 `m3_body_analysis.json`（create-once）。arm 身份三层
   核对：仅从冻结 ID 推导期望臂，CLI policy、manifest policy/planner、
   逐帧 `body_planner.name` 逐项相等；tracker 逐帧 capture 字段强制
   存在且与 truth 同帧 ≤1e-9 s；`compute_stage` 先机械划分为**恰好
   一条** init（`frame_id` 必须等于 manifest `init.frame_id`）与其余
   全部 update（其他取值/缺失即 fail closed），planner 只在该划分之后
   核对；update 行再按生产计数分为 decision（`skipped_count=0`，必须带
   正确 planner）与 catch-up（`skipped_count=1` 且 `backlog_count>=1`，
   必须不带 planner），至少一条 decision。run-bound `margin.json` 字节
   与其 `visible_arc.sha256` 必须等于 body config 的两个 pin。任何缺件/重复
   ID/跨 run 或哈希不一致 → 工具 fail-closed 退出，trial 不计入，现场
   保留回 Acceptance。复跑核验用 `--verify`（round 33 §B.4，与已发布实现
   对齐；A2 侧按轮 42 BC-BODY1-27，本段由轮 56 返工 F6b 更正）：对
   **A1（attempt-4）与 A2（attempt-2）两个替代采集**，`--verify` 各读取
   **两处**——run 目录内的存档输入，**以及 run 目录之外各自的
   predecessor hold**（A1 →
   `runtime/runs/p1-m3-body-001-arm-a-trial-1-void-attempt-3-hold/`；A2 →
   `runtime/runs/p1-m3-body-001-arm-a-trial-2-void-attempt-1-hold/`），
   两者都与存档逐字节核对。predecessor 门在 `--verify` 路径同样先于任何
   读取执行（`_check_a1_predecessor_hold` / `_check_a2_predecessor_hold`），
   它**只枚举该 hold 的直接文件名并对原始字节取 SHA-256**，不解析 void
   内容、不计算任何 void 指标。其余八个 run 的 `--verify` 仍只读各自的
   run 目录。
6. 读取 `m3_body_analysis.json` 的 `h1.full_loop_c_geom` 与
   `h1.disposition`，记入本次采集的证据；**任何后续 Play 之前回
   Acceptance**。**BC-BODY1-30（revision 13，F4 披露，只记录不判定）**：
   同时记入 (i) tracker 最后一帧的 `simulation_time_s`、Play 最后一条
   truth 的 `simulation_time_s` 及二者之差（post-tracker 停留），
   (ii) 由 `domains.final_unwrapped_mileage_m / route_perimeter_m` 算出的
   实测圈数。**这两项不构成任何门。**

   **臂 B 专属记录与回接受角色条件（revision 19 新增，接受轮 58；只增停条件，
   不新设作废门）**：本轮另须记入 (iii) `cost.body_motion_effort_m`、
   `cost.body_path_length_m`、`cost.planner_switch_count`，以及 (iv) 逐帧
   `body_planner.reason` 的直方图（特别是 `no_observation` / `no_platform_state` /
   `no_estimate` / `planner_exception` / 带 `corridor_blocked` 后缀的项），以及
   `published_reason == publish_failure_fallback` 的帧数。**依据**：没有任何门读
   规划器的 `mode`/`velocity_world_mps`/`planner_error`，而 `0/0/0` 是**合法**输出
   ——正是五次臂 A 的实测值。**若 `body_motion_effort_m == 0`**（**整圈定义域 `[0, P)` 内**机体零位移——
   effort 与路径长度都只在首圈样本上积分（`analyze_m3_body.py` 的 `loop_records`），
   首圈之后的运动不进入本量；即臂 B 在被测窗口内退化成第 6 次臂 A），**停下回接受角色归因，不得自行开始下一次 Play**。
   **本条本身不使 trial 作废**——事后新设作废门属改协议；它只保证退化不被静默
   当成有效对照。同理，第一次出现的**非零** effort/路径/切换数**只记录、不据以
   调参**（BC-BODY1-15 (d)）。

   正式 H1/H2 compare 在十次 trial 齐备后以
   `--compare --arm-a … --arm-b … --output <不存在的新路径>` 产出
   （create-once，哈希十份 analysis）。

## 4. tracker CLI（**本轮 = §1「本轮采集 ID」行所指的那一次**，缺省值显式写出）

**唯一合法入口是 `.venv-yoloe/bin/python -m controller.track_loop`**
（round 20 §B.1）。禁裸 `python3`、禁 `.venv-track/bin/python`、禁直接文件
入口 `python3 controller/track_loop.py`。**每轮替换的位点固定为两个**：`--run-id` 按 round 29 §C.2 取 **§1「本轮采集 ID」行**的值；`--body-policy` 按 round 11 §B.1 取 **§1 臂位行**的值（臂 A `hold` / 臂 B `threshold`）。**同臂轮换只动前者（恰 1 行）；跨臂轮换两者都动（恰 2 行）**——本文件唯一一次跨臂轮换是 revision 19。**其余 16 个参数一个不改、一个不加**（CLI 块 19 行 = 1 行解释器/模块入口 + 18 个 `--` 参数；对上一修订（同臂轮换）换掉 1 个。**对已复核候选换掉几个、未变几行，一律由 §2.0 (b) 执行时对运行时现取的 `<BASE>` 实测得出，本文件不写死**（接受轮 66；复核通过会前移 `passed_candidate`，写死即在下次通过时变成虚假归因）。历史参考：起草 revision 21/22 时的候选是 `408acd7`，对它换掉 2 个、未变参数 16 个、未变行 17 行。历次抬头写的「其余 18 个参数」把参数总数当成了「其余」，读数一直偏大 1）。启动前先按 §3 步骤 0′ 记录解释器逐字相等：

```bash
.venv-yoloe/bin/python -m controller.track_loop \
  --tracker nanotrack-v2 \
  --tracker-model-dir runtime/models/nanotrack-v2 \
  --tracker-model-spec config/nanotrack-v2.models.json \
  --reanchor-config config/detector-reanchor.models.json \
  --condition follow \
  --track-id target-0 \
  --scenario-id deterministic-loop-default \
  --ground-plane-y-m 0.2 \
  --run-id p1-m3-body-001-arm-b-trial-5 \
  --init-frame 0 \
  --init-box 0.2765625 0.40625 0.1203125 0.15208333333333332 \
  --planned-duration-s 130.0 \
  --maximum-ground-range-m 1000.0 \
  --expires-after-s 1.0 \
  --poll-interval-s 0.02 \
  --body-policy threshold \
  --body-planner-config config/p1-m3-body-001.json \
  --body-scenario-config config/scenario.default.json
```

`--init-frame` / `--init-box` 是 round 20 §A.4 冻结值，全部 10 次逐字复用（**本轮不重新框选、不做六位小数化**）；`--run-id` 用采集 ID，其**唯一事实源是 §1「本轮采集 ID」行**（本节不复述具体 ID，以免轮换时两处失配——复核轮 10 F8）；十个 ID 中只有 A1 = attempt-4、A2 = attempt-2 是替代 ID，其余八个等于各自 canonical slot，canonical slot 不进 CLI。
**两臂差异只有 `--body-policy` 一项**（round 11 §B.1）：臂 A = `hold`（五次已完成），
臂 B = `threshold`。臂 B 其余各次的 `--run-id` 同样只取 §1「本轮采集 ID」行的值；
**授权模型以 §5「现行执行前提」为准**——2026-08-14 批量 GO 覆盖 B2–B5，不逐次索要
GO；任何 void 终态立即中止该授权。`--compare` 不在任何 GO 覆盖内。

**跨臂漂移的代价（接受轮 58 披露，不新设门）**：`--compare` 要求十份 receipt 在
**15 个身份键**上一致（含 `init_box_norm`、`init_frame_id`、`body_config_sha256`、
`scenario_sha256`、`margin_artifact_sha256`、`visible_arc_sha256`、
`reanchor_config_sha256`、`tracker_model_spec_sha256`）。臂 B 这一侧若有任何一项漂移，
**该次分析在孤立状态下仍会 PASS**，只有到十次齐备跑 `--compare` 时才暴露——那时
十次 Play 已经花光。故上面**整块 19 行**必须逐字节照抄——**包括随轮换改动的 `--run-id` 与（跨臂时）`--body-policy` 这两行**（其余各行与**现行**已复核候选逐字节相同——`<BASE>` 按 §2.0 (b) 运行时现取，**不写死**）。**不得凭记忆重敲**：`--run-id` 写错则 run 目录已建、采集 ID 已消耗；`--body-policy` 写错（写成 `hold`）则臂身份三层核对在分析期 fail-closed——两者都直接烧掉这个 canonical slot。

## 5. 首跑 fail-closed 分支（写死）

> **现行执行前提（最高优先级；接受轮 64 按复核轮 10 F10 改写为不随轮换失效的
> 形式——此前这里停在 revision 19 的一次性 GO 前提上，与已入账的批量授权相悖）**：
>
> **授权模型（账本 2026-08-14「照跑 B2–B5，饱和作具名限制」）**：臂 B trial 2–5
> 由**一次性批量 GO** 覆盖，**不需要**每次再要一句用户 GO；但**每次 Play 仍各走
> 完整 §2.0 (a)–(d) 与本修订指定的各节核对**，且 **任何 void 终态立即中止该批量
> 授权**，停下回用户重新决定（臂 B 无替代 ID）。臂 A 五次与 B1 已完成，各自的
> 一次性 GO 均已消耗。**批量 GO 明确未覆盖的（账本 2026-08-14「照跑 B2–B5」条
> 逐字）**：`--compare`（需十次齐备并**单独授权**）、任何重试/重进/调参、任何协议/
> 指标/阈值/测量窗/载体/统计量变更。
>
> **另按在案现状继续排除（非批量 GO 条文——不得记到该条名下）**：R10/R11、R12
> ——依据是 COORD-007 账本 2026-08-12 未授权，且 B1 单次 GO 条（2026-08-14，已放电）
> 曾逐字点名。**该条同时点名的「臂 B trial 2–5」已被批量 GO 取代，不在此转录。**
>
> （**接受轮 65 更正**：此处原把两条账本条目的排除项合并后自证「逐字…不作增减」
> ——对批量 GO 条是**增**（R10/R11、R12），对 B1 条是**减**（臂 B trial 2–5），
> 措辞亦非逐字。复核轮 12 F11 判为 CLASS_2：在「账本没有的授权视为未发生」的项目里，
> 给账本安上没说过的话，与漏记授权是同一完整性的镜像破坏。**操作面无净授予**——
> 上列各项今日均真不可为。）
>
> **发令必须同时满足**：**(1)** 本修订抬头指定的 §2.x 核对节全过（含两项**臂 B
> 专属**：corridor 工件哈希、`_expected_policy()` 返回 `threshold`）；**(2)** §2.0
> 的 (b)/(c)/(d) 三步齐备；**(3)** **两条预登记限制已落盘并提交**，且提交发生在
> 本次 Play **之前**——H2-CEILING 与处理臂饱和，预登记若晚于数据即失去意义。
> 可核对：`git log --oneline -S'H2-CEILING' -- docs/implementation-status.md`
> 与 `git log --oneline -S'TREATMENT-ARM SATURATION' -- docs/implementation-status.md`
> 各须返回至少一个提交且早于本次 Play。
>
> **本前提不写具体采集 ID**：当轮对象一律以 **§1「本轮采集 ID」行**为准
> （复核轮 10 F8/F9/F10 + N37 的根因修复）。
>
> **revision 19 执行前提（历史，已放电）**：该前提写于 B1 那次一次性 GO 下，
> 其「本次授权只覆盖一次 Play、只覆盖 `p1-m3-body-001-arm-b-trial-1`；臂 B 余下
> 四次与 `--compare` 仍需逐次逐字 GO」一句自 2026-08-14 批量 GO 入账起终止效力
> （`--compare` 部分**继续有效**）。B1 的那次 Play 已执行并被接受轮 60 判为有效。
>
> **臂 B 零作废容错（接受轮 58 披露，发令前必读；不新设门，只陈述现状）**：
> `canonical_trial_id()` 只认十个字符串，**只有 A1 与 A2 有替代 ID**；
> `…-arm-b-trial-1-attempt-N` 与 `…-arm-b-trial-6` 一律 `run_id_not_frozen_trial`
> （`…-attempt-4` 形式由 `test_other_attempt_suffixes_are_rejected` 逐字钉住；
> `…-arm-b-trial-6` 由 `canonical_trial_id()` 的冻结枚举拒绝，无专门用例）。臂 A 能从
> 两次作废里恢复，**是因为轮 29 §C.2 与轮 42 §B 事后加了代码**（替代 ID +
> predecessor 字节门 + compare 侧对称块）。
>
> **臂 B 若在 tracker 启动之后作废**（run 目录已 create-once 建成、采集 ID 已消耗），
> **该 canonical slot 即烧掉**，恢复须再一次用户授权 + 代码 + 独立复核 + 停点。
> **区分清楚，不得混淆**（依据是本节 pre-tracker 段的逐字规定）：门 1/门 2/门 3 与
> `TRIAL_VOID_TRACKER_STARTUP_FAILURE` 都发生在**创建 run 目录与任何发布之前**，
> 该采集 ID **未被消耗**，可在未来新 GO 下首次合法使用——只消耗一次 one-Play GO。
> 故三个硬门触发时**不得**报告「slot 已烧掉」。真正烧掉 slot 的是 post-tracker 终态。
> 三个硬门、握手与退出纪律仍必须逐字执行，不得「运行中申请例外」。
>
> **revision 18 执行前提（历史，已放电）**：A5 判为有效后待执行的只有 §2.15，
> 该节已于 2026-08-14 由实现角色执行完毕（`e68827d`）；当时"没有任何已授权的
> Play"一句，随 2026-08-14 臂 B trial 1 的 GO 入账而终止效力。
>
> **revision 17 执行前提（历史，已放电）**：A4 判为有效后用户授权 A5 的一次
> Play，前提两项（§2.14 七项 / §2.0 (b)(c)(d)）当时全部满足，该次 Play 已执行
> 并被接受轮 55 判为有效 A5。
>
> **revision 17 执行前提（原文，2026-08-13）**：A4 已由接受轮 52 判为
> **有效 trial**，arm A 现 **4/5**，且 §2.13 的 A4 post-run 归档已执行完毕。
> 用户已授权 **arm A trial 5 的一次 Play**（账本 2026-08-13「授权第五次trail」
> 条）。发令必须同时满足：**(1)** §2.14 七项只读核对全过；**(2)** §2.0 的
> (b)/(c)/(d) 三步齐备。**本轮无归档待办。本次授权只覆盖一次 Play、只覆盖
> `p1-m3-body-001-arm-a-trial-5`**；臂 B 五次仍需逐次逐字 GO，`--compare`
> 另需十次齐备与单独授权。
>
> **revision 15 执行前提（历史，已放电）**：A3 判为有效后用户授权 A4 的一次
> Play，前提三项（§2.11 归档 / §2.12 七项 / §2.0 (b)(c)(d)）当时全部满足，
> 该次 Play 已执行并被接受轮 52 判为有效 A4。

> **下表三分支已由 A1 放电，B1 不重复触发，也不重新武装（revision 19 逐字确认）。**
> BC-BODY1-15 (c) 把三分支绑定在**批次 1c 的第一次 Play**（必须是臂 A
> trial 1）。A1 实测整圈 `C_geom = 0.5784550773737355` 落在
> `[0.5645, 0.95)`，已走「唯一释放分支」，其余九个 trial 因此取得**协议
> 合格**状态（接受轮 38）。**B1 是臂 B 的第一次，但不是批次 1c 的首跑**，故
> 三分支既不重跑也不"因为换了臂所以重新武装"；本操作单**不为 B1 新立任何
> 数值门**——冻结合同里不存在这样的门，编造一个即属改协议。机械事实与之一致：
> 分析器仍会为臂 B 的 run 写出 `h1.disposition` 字符串，但**从不据此抛错**，
> 且 H1 只遍历臂 A。
>
> **对每一轮继续逐字适用**：BC-BODY1-15 (d) 的反调参纪律（对任何算出的数值不得做
> 参数/阈值/窗口/载体调整——**包括臂 B 首次出现的非零 effort / 路径长度 / 切换
> 次数，以及两次 `C_geom = 1.0`**）、下方全部 pre-tracker 与 post-tracker void
> 终态、以及「每种终态各消耗一次 one-Play GO」。
> **协议合格 ≠ 已获授权**：批量 GO 覆盖 B2–B5，但每次 Play 结束后仍按 §3 步骤 6
> 回 Acceptance 归因，**归因通过才轮到下一次的前置**；任何 void 终态中止批量授权。

arm A trial 1 完成并经 `analyze_m3_body.py` 绑定后、任何后续 Play 之前
（**历史条款，A1 已放电**）：

| 整圈 `C_geom`（离线机械口径） | 终态/动作 |
|---|---|
| `< 0.5645` | **`GEOMETRY_MODEL_REJECTED`**：停批次，回 Acceptance/几何 |
| `>= 0.95` | **`SCENE_DEGENERATE`**：停批次，回 Acceptance/场景设计 |
| `[0.5645, 0.95)` | 唯一释放分支：向 Acceptance 申请释放其余 9 次 Play |

- 对该数值**不得**做任何参数/阈值/窗口/载体调整，合法动作只有
  「释放」或「具名终态」二选一（BC-BODY1-15 (d)）。
- Play 中途任何 Console 报错、tracker 异常退出、发布失败终态
  （`BODY_COMMAND_FAIL_CLOSED`）、帧缺口或绑定工具 fail-closed：
  trial 不以任何形式计入，现场保留，回 Acceptance 归因，不得用旧文件
  或就地重跑顶替。
- **pre-tracker 具名终态**（tracker 尚未启动，revision 10）。不计数、现场
  保全、回 Acceptance，且**不得就地重试或申请运行中例外**：

  | 终态 | 触发 | 先例 |
  |---|---|---|
  | `TRIAL_VOID_PAUSE_WINDOW_VIOLATION` | §3 步骤 2 门 1：`reported_sim_t` 越出 `[2.000000, 10.000000)` | attempt 2（`10.854090`） |
  | `TRIAL_VOID_TRACKER_STARTUP_FAILURE` | tracker 在 `TrackLoop.initialize` 之前异常退出 | attempt 1（缺 `ultralytics`） |

  这两种都发生在**创建 run 目录与任何发布之前**：run 目录**未创建**，该
  **采集 ID 未被消耗**，可在未来新 GO 下首次合法使用。

  > **round 41 据实更正（历史记录，不改任何门）**：上表「先例」列的
  > attempt 2 是本门的**设立触发因由**，不是本门的实例——attempt 2 的终态是
  > `TRIAL_VOID_PROTOCOL_DEVIATION_PRE_TRACKER`（接受轮 25 §A.3），
  > `TRIAL_VOID_PAUSE_WINDOW_VIOLATION` 由接受轮 25 §B.2 新设，**迄今从未被
  > 触发**。

- **post-tracker 具名终态**（tracker 已启动，round 29 §C.4）。同样不计数、
  现场保全、回 Acceptance，且不得就地重试或申请运行中例外：

  | 终态 | 触发 | 先例 |
  |---|---|---|
  | **`TRIAL_VOID_PROTOCOL_DEVIATION_POST_TRACKER_EARLY_EXIT`** | tracker 已正常启动并持续发布，但在 §3 步骤 4 的 `TRACKER_AUTO_COMPLETE_CONFIRMED` 之前退出 Play、tracker 非零退出、进程仍存活，或 `metrics.final.json`/`summary.json` 任一缺失 | attempt 3（`125.3803` 退出，缺 130 s 自动完成） |
  | **`TRIAL_VOID_LOOP_DOMAIN_UPPER_BOUND_VIOLATION_POST_TRACKER_DWELL`**（round 41 新设）—— **历史终态，其触发条件已由接受轮 42 §A 撤下（revision 19 加注）**：`>= 2P` 上界不再存在。**准入判据只有下界** `final_mileage < P` → `trial_invalid_no_single_loop`；上界撤下后代之以**两条域完整性硬门**（`loop_domain_sample_below_perimeter_after_closure` 与 `loop_domain_unwrapped_backward_step`，见 §1 整圈定义域行），故「跑得远」本身不再使 trial 作废（A4 跑 `3.2432` 圈仍有效），**但域完整性被破坏仍会 fail-closed**。**照字面读本行会促使操作员提前退出 Play，而提前退出正好撞上仍然生效的 `…POST_TRACKER_EARLY_EXIT`，那才会烧掉采集 ID。** | 当时的触发：tracker 自然完成且确认词已产生，但 Play 继续停留到 `final_mileage >= 2P` | arm A trial 2（`769.393 m` = `3.6127` 圈；post-tracker 停留 `252.399 s`）——保留为历史先例 |

  处置：**不 `--finalize`、不分析、不重进**，保全现场并回 Acceptance。
  **墙钟不得替代仿真时间**完成正常 trial；「一圈已跑完」「测量窗已覆盖」
  都不构成完成。此种情况 run 目录**已创建**，该**采集 ID 已被消耗**，
  下一次采集须由 Acceptance 另行冻结新的采集 ID（attempt 3 即因此换用
  attempt-4 采集 ID）。

- 上述终态**每种都各消耗一次 one-Play GO**（每次进入 Play 即消耗）。其中
  loop-domain 上界一项的**触发条件已由接受轮 42 §A 撤下**，保留为历史记录，
  当前实际可触发的是其余**三种**（revision 19 据实更正原「四种」计数）。

## 6. 提交边界声明

**（接受轮 64 裁定 N36）自 revision 20 起，各修订的提交边界事实并入其修订抬头，
本节不再逐修订补记**——补记会制造第二份索引，正是 N36 自己点名的漂移源。本节保留
revision 19 及更早的历史条目，各带时间边界。


- **revision 19 本身零 Play、零采集 ID 消耗、零运行指标、零代码/测试/config/
  scenario/model 改动**；做的是**跨臂双重轮换**（§1 臂位行 + 采集 ID 行、§3 步骤
  0′/2/3/4/5、§4 CLI 的 `--run-id` 与 `--body-policy`）、**新增 §2.16** 与 §1 的
  corridor 钉住行、§2.15 转历史，外加五处失效标注就地更正与两条披露。
  **冻结值全部逐字保留**：暂停窗 `[2.000000, 10.000000)`、初始框四分数与
  `(177,195,77,73)`、`212.9706`、`130.0`、`62.5`/`31.25`、五次/臂、全部 SHA-256；
  §4 CLI 块与**当时**的已复核候选 `408acd7` 逐行比对**恰 2 行不同**，其余 17 行逐字节
  相同。**时间边界（接受轮 66）**：该候选自复核轮 11 起前移，差异行数一律以 (b) 执行
  时对现行 `<BASE>` 的实测为准。
  **该修订当时已获授权的是且仅是 `p1-m3-body-001-arm-b-trial-1` 的一次 Play**
  （账本 2026-08-14 条）。**时间边界（接受轮 64）**：自 2026-08-14 批量 GO 入账起，
  B2–B5 已获覆盖，本句的「臂 B 余下四次未授权」部分终止效力；**任何重试、任何
  重进、任何调参、`--compare` 仍均未授权**，且任何 void 终态中止批量授权。五个有效 run 目录、五处 post-run 归档与全部 hold 是只读保全对象。
- **revision 18 本身零 Play、零采集 ID、零运行指标、零代码/测试/config 改动**；
  只新增 §2.15 归档合同并把 §2.14 转历史，**未做槽位轮换**（臂 B 当时无 GO）。冻结值
  全部逐字保留。A5 的 Play 已在 revision 17 下完成并判为有效。**时间边界
  （revision 19）**：该条写「本修订之后没有任何已授权的 Play」时属实；此后
  2026-08-14 用户授权了臂 B trial 1 的一次 Play，该句自那时起终止效力，其余部分
  （每次 Play 各需新的逐字 GO）自 2026-08-14 批量 GO 入账起对 B2–B5 终止效力；
  对 `--compare`、任何重试/重进/调参**继续有效**。
- **revision 17 本身零 Play、零新采集 ID 消耗、零运行指标、零代码/测试/config/
  scenario/model 改动**；只做槽位轮换（§1 采集 ID 行、§3 步骤 4/5、§4 CLI 的
  `--run-id`）与一节新增（§2.14 核对），§2.12/§2.13 转历史。**冻结值全部逐字
  保留**：暂停窗 `[2.000000, 10.000000)`、初始框四分数与 `(177,195,77,73)`、
  `212.9706`、`130.0`、`62.5`/`31.25`、五次/臂、全部 SHA-256；A5 无需替代 ID、
  不触发任何 predecessor 门。**本修订不释放 Play**：§5 顶部两项前提缺一不可。
  本轮已获授权的是且仅是 **arm A trial 5 的一次 Play**（账本 2026-08-13
  「授权第五次trail」条）；臂 B 五次、任何重试、任何重进、任何调参、`--compare`
  **均未授权**。四个有效 run 的 run 目录、四处 post-run 归档与五处 void/诊断 hold
  在本轮是只读保全对象。
- **revision 16 本身零 Play、零采集 ID、零运行指标、零代码/测试/config 改动**；
  只新增 §2.13 归档合同，**未做槽位轮换**（A5 无 GO）。冻结值全部逐字保留。
- **revision 15 本身零 Play、零新采集 ID 消耗、零运行指标、零代码/测试/config/
  scenario/model 改动**；只做槽位轮换与两节新增（§2.11 归档合同、§2.12 核对）。
  冻结值全部逐字保留；A4 无需替代 ID、不触发任何 predecessor 门。
  **本修订不释放 Play**：§5 顶部三项前提缺一不可。
- **revision 14 本身零 Play、零新采集 ID 消耗、零运行指标、零代码/测试/config/
  scenario/model 改动**；只做槽位轮换与两节新增（§2.9 归档合同、§2.10 核对）。
  **冻结值全部逐字保留**；A3 无需替代 ID、不触发任何 predecessor 门。
  **本修订不释放 Play**：§5 顶部四项前提缺一不可。
- **revision 13 本身零 Play、零新采集 ID、零运行指标、零代码/测试/config/
  scenario/model 改动**；只做槽位轮换、F2 之后的判据文字、F4 两条操作条款、
  基线指针运行时派生、§2.7/§2.8 两节与三处行号去钉。**冻结值全部逐字保留**：
  暂停窗 `[2.000000, 10.000000)`、初始框四分数与 `(177,195,77,73)`、
  `212.9706`、`130.0`、`62.5`/`31.25`、五次/臂、全部 SHA-256。
  **本修订不释放任何 Play**：§5 顶部三项前提缺一不可，其中用户 GO 未答复。
- **revision 12 本身零 Play、零新采集 ID、零运行指标、零代码/测试/config/
  scenario/model 改动**；本修订只轮换采集槽位并新增两条记录型条款。
  **本轮已获授权的是且仅是 trial 2 的一次 Play**（账本 2026-08-13
  `P1-M3-BODY-001` 条目）；其余 8 次 Play、任何重试、任何重进、任何调参
  **均未授权**。A1 的 run 目录、post-run 归档与三处 void hold 在本轮是
  只读保全对象。
- **revision 12 未交付、也无权交付的两项**：COORD-007 §4.1（暂停窗遥测
  写入 + 启动前断言）与 §4.2（解释器绑定校验）的**机器断言**属 **R10**，
  账本 2026-08-12 COORD-007 条目逐字列为未授权，且为代码——接受角色不写
  实现代码。§3 步骤 0′/2′ 是**记录型**替代，能保证"不符时有据可查且必须
  停"，**不能**保证"机器拒绝启动"。§4.1 的一帧下界缺口（末帧 `9.97`
  通过而真实暂停 `10.03`）**仍然敞开**，已在 §3 步骤 2 逐字披露。
- **revision 11（历史记录）**零 Play、零新采集 ID、零运行指标；1b 与三次
  void 现场均已按 §2.1–§2.4 保全。**时间边界（revision 12）**：该修订写
  「arm A trial 1 的下一次 Play 与其余 9 次全部未授权」时确实无任何 GO；
  此后 attempt 4 已在 2026-08-10 的条件式 GO 下执行并被接受轮 38 认定为
  有效 A1，trial 2 已在 2026-08-13 获用户单次 GO。该句其余部分
  （每次 Play 均须用户新的逐字 GO）自 2026-08-14 批量 GO 入账起对 B2–B5 终止效力；
  对 `--compare`、任何重试/重进/调参**继续有效**。
- **revision 10（历史记录）**零 Play、零正式 ID、零运行指标；attempt 1 与
  attempt 2 的 void 现场按 §2.2/§2.3 保全。**时间边界（round 33 §B.5）**：
  该修订完成时 `p1-m3-body-001-arm-a-trial-1` 尚未创建；此后 attempt 3 已
  创建并消耗该 ID，其 run 目录已移入
  `…-void-attempt-3-hold/`（§2.4），该字符串当前与未来均不得再作为
  acquisition ID 或 run 目录被创建。
- **revision 8（历史记录）**零 Play、零正式 ID、零运行指标；当时 void 现场
  保持冻结，§2.2 的移动此后已在 attempt 2 之前执行完毕（见 §2.2 标注）。
- 本预检/操作单修订零 Play、零正式 ID、零运行指标。
- 真值载体与分析工具的实现、测试与证据见
  `docs/evidence/P1-M3-BODY-001-1c-rework.md`；稳定候选经 Acceptance
  §4.3.1 确认（含写入归因）并独立 Review PASS 前，trial 1 不释放。**时间边界
  （revision 19）**：该前提已于 2026-08-10 满足，trial 1 已由接受轮 38 判为有效 A1，
  臂 A 现 5/5 收官；本句自那时起终止效力。**此后各轮的当轮对象一律以 §1「本轮采集 ID」行为准**，本节不再点名。
