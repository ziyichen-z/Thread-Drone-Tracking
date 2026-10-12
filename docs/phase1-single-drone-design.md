# 单机阶段设计文档（Phase 1）

> 版本：v0.3.73（2026-10-12）——`P1-ENG-FASTFIX-001` D2 `ACCEPTED`、`engineering-v1`保持；候选4独立R2@K1K2K3K4 REVIEW_PASSED已消费、R1-1闭合，代码停点收口；Overall REVIEW_PASSED/Lifecycle ACTIVE。现行AC表、核对表、归因与用户入口见同名提案「R2通过消费」§1–5；AC/接口/停点未改。三窗口均released，不证明完整峰值；旧UNKNOWN/偏差与OPEN债保持，TX/B/C未签0、AC-8及现场项NOT_RUN，无Unity/UNITY_NA/DONE。

> 当前LOOP-002授权/候选状态（2026-10-08）：合批进度与全套清单核清完成，现行入口为同名提案同名节§1–4，修复合同仍见「SUB3核清与评分上限落实」§2–5。DIAG-CONTROL-1/评分全批≤3窄修已实现、未全套/非稳定；全套清单SUITE-LIST-1待补正归档读取/临时复制披露，未呈可首签清单；合批新OpsScoreDiagK1K4停点未复核；Overall REWORK_REQUIRED，旧Ops R2 PASS/归因/计数携带，R1-5 OPEN。SUB:3用尽、新诊断未签0；SUB:1/N-1耗尽、全套不绿；SUB:2本人附议/UNKNOWN保持。正式G1–G5/现场登记/AC-18未闭，AC-14/15/18及AC-16正式板端NOT_RUN，无UNITY_NA/DONE；旧债/偏差/UNKNOWN/ACQ暂停保持。以下版本说明为历史快照。

> 版本：v0.3.67（2026-10-07）——`P1-ENG-LOOP-002` SUB1换机答复落实：只读补核交Mac mini，Air未用余额作废；mini原件/别名先核，缺失即停。原闭集及完整B-main/N-3未签保持；(k)会话/快层与Unity仍在Air，mini无需安装Unity。现行边界见同名提案「SUB1换机答复落实」，无新板端/Unity证据。

> 版本：v0.3.66（2026-10-07）——`P1-ENG-LOOP-002` 补核答复落实：四答与账本/B0a推荐一致，仅一次≤600s只读补核可执行；共享库先取事实、46273保持不碰，完整B-main/N-3待补核后转用户。执行边界见同名提案「补核答复落实」；原AC/门/证据与实际采集前置保持，无新增板端或Unity证据。

> 版本：v0.3.65（2026-10-07）——`P1-ENG-LOOP-002` B0a核清完成；N-2账在限，完整B-main确定计划与本轮只读补核申请分列，N-3逐码转呈用户。共享库/精确部署根/监听UNKNOWN使完整运行申请暂阻；AC/REVIEW_PASSED不变，操作单/实际采集及证据停点未放行。见同名提案「B0a核清」与§5.2回填。

> 版本：v0.3.64（2026-10-07）——`P1-ENG-LOOP-002` B-pre答复落实：N-2已签、(h)(j)(k)已答；只用Jetson，5060不启用，服务由本人启动。授权边界修订1见同名提案「B-pre答复落实」；仅有限只读B0a可执行，(i) B-main/N-3待读数核清、未签0。原AC与REVIEW_PASSED不变，无新增硬件/Unity证据，不签DONE。

> 版本：v0.3.63（2026-10-07）——`P1-ENG-LOOP-002` R2消费完成，阶段A代码REVIEW_PASSED；R1-1已闭、AC-7满足，完整归因/六题前置见同名提案「R2消费」。AC-14/15/18与AC-16板端NOT_RUN，无UNITY_NA，不签DONE；B未签0，实际Play放行与证据停点仍待。ACQ R1-4具名cause债经本项独立复核核实后CLOSED，不追认旧候选/Unity或恢复暂停；其余债保持。

> 版本：v0.3.62（2026-10-06）——`P1-ENG-LOOP-002` C2@K1K2K3K4 已核，附AC-7异常IO计量偏差及未决关注项照交新鲜上下文R1；IR-13…17读法裁定见同名提案「C1返工读法答复」，不增改AC义务。B证据后续C轮按实际连续计数，不再预记C2；独立复核/Unity未完成，六题与未签0、旧债保持。

> 版本：v0.3.61（2026-10-06）——`P1-ENG-LOOP-002` 实现待裁定释义已追加：designation_id 限常驻代、decode 常量共享位置及终止不可用的据实原因，原算法/样本/硬件/信封不变；见同名提案「待裁定答复」AC-7 修订 1、AC-8 修订 1/2。代码候选 C1 首退，独立复核/Unity 未完成；首次全套有效，六道用户题与未签0保持。

> 版本：v0.3.60（2026-10-06）——`P1-ENG-LOOP-002` D4 ACCEPTED，engineering-v1、AC-1…18 与输入 schema 冻结；合同见同名提案「D4 接受裁定」，N-1首签已按§5.1落实，现行授权边界见「N-1答复落实」。代码/独立复核/Unity 尚未执行；六道用户题与未签维度0保持，ACQ暂停和旧债不变。

> 版本：v0.3.59（2026-10-04）——`P1-ENG-FRAME-001` 墙钟收尾落实：接受按实现者证据、最终R3@K2 PASS_WITH_NOTES与同一补测AC-21/23及用户目检裁定UNITY_PASSED、DONE/ACTIVE。完整按钮墙钟为已追认的可能超额：未知、≤532.672385 s 保守上界、可能超过480 s；余额0、不补测。三证据与保留R1-3 OPEN/旧失败/环境及HTTP局限见 `docs/evidence/P1-ENG-FRAME-001-supplement-play-20261004.md`「墙钟收尾落实」；不改合同或研究主张，以下旧版本注记按当时状态解读。

> 版本：v0.3.58（2026-10-01）——`P1-ENG-FRAME-001` 的 R2@K2 `PASS_WITH_NOTES` 已由接受角色消费；机身 c-组合与无缆缺省的 K2 代码停点通过，第二次Play已完成约273秒tracker运行并退出，AC-23安全/来源核对满足；AC-21的R7分析输出与机身跟随/起停目检未闭，完整按钮墙钟未独立取得。用户仅将本次总墙钟延至480秒，无第三次Play授权；原件与裁定见 Unity 日志 UT-P1-ENG-FRAME-001-D1 及同名play证据。证据与未闭债见 `docs/implementation-status.md`「P1-ENG-FRAME-001 — R2@K2 通过轮消费」；合同主体与其余预算不变，本次墙钟例外见账本，不产生研究主张。

> 版本：v0.3.57（2026-09-30）——接受 `P1-ENG-FRAME-001` D2，`engineering-v1` 生效：主线拟用 `config/scenario.untethered.json` 无缆缺省与距离保持带机身跟随；旧 `config/scenario.default.json` 字节不动，绷紧系留假设只适用有缆模式。实现、K2 独立复核及 Unity 仍未完成；历史系留研究设计与证据不回溯。合同与已签额度见同名提案「D2 接受裁定」「已签执行合同」。

> 版本：v0.3.56（2026-09-29）——`P1-ENG-ACQ-001` 的 `candidates` CLI、结果 schema 与单 Unity 主机 K 收据窄修合同见同名提案「candidates 后端接线窄范围修复 CLARIFY」（AC-21、AC-18 修订 3）；新 K1K3 候选经 C/R 通过、用户在另一台 Mac 上本地生成与生效 hz/R 绑定的收据后才可核对 Play D1。B4 人工计时、B5 人工/离线读数沿用操作单；旧通过候选不为新代码放行。

> 版本：v0.3.55（2026-09-28）——`P1-ENG-ACQ-001` D2 按 workflow §4.2(a) 接受，engineering-v1、AC-1…20 与合并 `K1K2K3` 生效；指针式常驻关联、按传感器帧历史、三级解析（含 k 帧起跟回放）、转向通道及最小伺服的字面合同见同名提案「§4.2(a) 接受处置」。AR2-2 的 E1 600 次限额与全样本守恒冲突保留为具名限制；§5 执行信封与 Play D1 未签，§7 (g)–(i) 待用户，未实现或验证。
> 版本：v0.3.54（2026-09-27）——接受 P1-ENG-FAST-002 当前范围，engineering-v1、单候选 K3K4。`det-assoc-v1` 仅为 v0.3 §3 的可显式选用局部备选，缺省与换目标不重训练属性不变。AR2-1/2 执行释义见提案「用户选 (a) 后的接受处置」；阶段 1 门值、AC-12 Unity 通过条件、§7(h) 来源与 §5 线 A 信封见提案「待裁定：用户授权后的 AC-n 合同补齐」，口径 B 门值与设备判门范围仍待用户，尚未实现或完成。
> 版本：v0.3.52（2026-09-26）——接受 COORD-016 D3 流程设计（研究轨道，BC-1…6）：D1 非递增有上限、D7 预注册数值有限例外、D2b 有界定向返工；规则落地与任何新信封仍待用户逐字授权，运行时基线不变。
> 版本：v0.3.51（2026-09-24）——接受 P1-ENG-FAST-001 D3 离线快层替换探针，engineering-v1、AC-1…11 与 K4 生效；执行信封待用户授权，LOOP-001 返工仍暂停。
> 版本：v0.3.50（2026-09-23）——LOOP-001 R-B12…13：诊断 6 段 2–4 首批 `catchup_stale` 硬停止，追平改为初始化后静音多批收敛（T_catchup 6 s，K_pub/T_pub/五项门不变）并固定入画即指定的择时；新候选回 K1K2K3。
> 版本：v0.3.49（2026-09-23）——LOOP-001 R-B8…11：用户要求机身跟随，接入冻结阈值规划器并增加 K2；正式 P1 改为一圈抽样演示门，额度不增。
> 版本：v0.3.48（2026-09-22）——LOOP-001 R-B5…7：本地按钮页具名GUI例外、AC-18及AC-12修订4/5；
> 新增诊断3次独立记账，零消耗候选经C3→R5后再诊断，原计数与终局限制保持。

> 版本：v0.3.47（2026-09-22）——LOOP-001 R-B1…4：用户授权 runInBackground 单字段例外与追加两次诊断；
> AC-4 修订3、AC-12 修订3；新候选经 C2→R3 后再诊断，正式 Play 前提保持。

> 版本：v0.3.46（2026-09-20）——LOOP-001 P-B-2 采用独立配对不可用诊断，追加 AC-16 修订 3；
> 核验配对前跳过不占查询号，已发起查询的身份失败仍产结果；无新增验收项或额度。

> 版本：v0.3.45（2026-09-20）——LOOP-001 P-B-1 采用 (a)，追加 AC-16 修订 2：
> same_frame/no_tracker_box/tracking_lag 发起前跳过只记会话日志，移出结果原因闭集；不新增验收项或额度。

> 版本：v0.3.44（2026-09-20）——LOOP-001 实现期八问追加八行同编号 AC 修订；无预览不得确认播种，
> 收据、尝试、异常和核验映射明确。阶段 A 信封已签发、实测另批安排；阶段 B 未授权，K1K3 尚未到达。

> 版本：v0.3.43（2026-09-19）——接受 P1-ENG-LOOP-001 D4 与八行首次接受释义，engineering-v1 生效；
> 语言指定、人工确认与语义提醒的 K1K3 合同，阶段 A/B 执行额度均未授权。详见 §1。

> 版本：v0.3.42（2026-09-18）——SFT-002 K3待裁定五行追加释义：冒烟、训练细节、选优、预算执行与代码束；
> 5060诊断授权已补账；正式云端操作单须先落实预算停止路径，旧里程碑与运行时基线不变。

> 版本：v0.3.41（2026-09-14）——SFT-002 实现期待裁定六行释义与表 J 两条颜色归因；
> 候选1信封及tokenizers补录见账本，K3未授权；不改变运行时基线或旧里程碑。

> 版本：v0.3.40（2026-09-13）——接受 P1-ENG-SFT-002 D3 用户保留范围后的合同，
> engineering-v1 生效；Unity 三态数据 K4 → LoRA/云端 K3，执行额度仍待授权。详见 §1。

> 版本：v0.3.39（2026-09-08）——P1-ENG-ASSET-001 显示与机读代录补充裁定，首次释义挂接 AC；
> 同批修复不增加样本/看图轮次，K4 与旧研究证据门保持。

> 版本：v0.3.38（2026-09-08）——P1-ENG-ASSET-001 实现期合同裁定：同批面板迁出 runtime、
> 问题转录路由及未验证类别分支释义；零新增资源，运行时与旧归档合同不变。

> 版本：v0.3.37（2026-09-08）——接受 P1-ENG-ASSET-001 D3 用户收敛合同，
> 裁定 engineering-v1；仅资产/指令盘点、分层抽查、只读接口缺口。用户同日已单独授权执行。

> 版本：v0.3.36（2026-09-07）——按 COORD-010 用户批准 A+B+C 完成状态迁移：
> DATA-002 不足且保留来源缺口终止，DATA-001 部分交付收束，DIST-001 四臂/T-G1 延期。
> 工程首版范围见 §1；只改变范围安排，不回写历史证据或运行时合同，不授予执行额度。

> 版本：v0.3.35（2026-09-07）——DATA-002 BC-SURVEY-19 解释本次失焦中断为
> `PILOT_FAIL_TOOL` 与原信封内工程重试；不新增终态、义务或资源。B–D 产出不足已消费，
> 用户 §2.4 选择及 Unity 证据缺口见状态板；F1–F4、四臂、T-G1、运行时基线不变。

> 版本：v0.3.34（2026-09-03）——`P1-VLM-DATA-002` Accepted 后解释行
> BC-SURVEY-17/18 将 BC14 的 `survey_acquisition` 闭集固定为顶层 3 键和 89 个具名
> `SURVEY_*` 常量，并将 BC16 的“全部候选”固定为十锚点逐项枚举计数
> `53/209/60/74/135/248/62/128/217/0`；两行均为 `CLARIFY`，不新增义务、不改资源信封，
> round 5 的 BC14/16 窄返工、COORD-005 暂停与后续 C1@stageA→R1@stageA 顺序不变。
> 版本：v0.3.33（2026-09-03）——`P1-VLM-DATA-002` Acceptance round 5 新增
> BC-SURVEY-16：十个锚点坐标/顺序不动，逐锚点穷举冻结候选并只为首个合法 plan 建身份；
> 当前只保留 1/2/3/4/6/7/9，5/8/10 无身份、无 Play。规划 `99/101` 不变成新承诺，
> F1–F4/pilot/§5 门不降，失败仍落 `SURVEY_FLOORS_UNREACHABLE`。候选还须补 BC14 的
> close 重入及零帧 verify 双钉核对和 BC16 穷举回归，COORD-005 继续暂停。
> 版本：v0.3.32（2026-09-03）——`P1-VLM-DATA-002` Acceptance round 4 新增
> BC-SURVEY-14/15：S0 `survey_acquisition` 完整冻结采集协议，attempt-1→2/3 的差异集合
> 改为恰五键；plan/manifest/S0/当前运行投影跨入口互钉，漂移即失败；证人分量框的中心命中
> 严格沿用右/下开边界。阶段 A 继续窄返工，COORD-005 诊断 Play 仍暂停，授权信封不变。
> 版本：v0.3.31（2026-09-03）——`P1-VLM-DATA-002` 实现期合同裁定新增
> BC-SURVEY-7…13：attempt-2/3 S0 必须哈希冻结实际根清单并由 S1 对账；停放障碍取
> 三轴 4 m 闭集扩张；§8 只冻结锚点坐标/顺序，扫描数字仅作诊断；冻结 `sweep_proxy`、
> `VALID_SURVEY` 的 primary 顺序、全画幅 4-邻接证人算法和严格绑定已复核 plan 的
> `view_id`。阶段 A 代码已交付但须先返工 BC-SURVEY-7/13 及相应回归，COORD-005 诊断
> Play 在返工完成前暂停。用户授权 #1 的额度与阶段边界不变且仍零消耗；正式采集、
> session/run ID、S0–S5 attempt、阶段 B–D、S6、API/GPU/模型/训练仍未授权。
> 版本：v0.3.30（2026-09-03）——Acceptance round 3 接受
> `P1-VLM-DATA-002` revision 2（BC-SURVEY-1…6）：在不改 language→box、四臂、T-G1
> 与 F1–F4 的前提下，允许一条待用户分阶段授权的场景内巡览补采合同。冻结逐帧
> `VALID_SURVEY`、停放目标真值、连续净空、零帧归档、COORD-005 零-ID 诊断、经复核
> plan/config 和混合 attempt-2/3 的实际输入 lineage；正式 Play 上限 10，诊断 Play 上限
> 3，API/GPU 均为 0。接受本身不授权实现、plan/scenario/session ID、Play、S0–S5
> supersession 或 S6；本段是接受时点边界，阶段 A 的后续授权见上方执行范围维护。
> 版本：v0.3.29（2026-09-01）——Acceptance round 29 接受正式 S3→S5
> continuation 的执行合规性，但真实归档反证 S4 的 515 MB manifest 不符合
> BC-DATA-25「小型摘要」：全量 `near_duplicate_pairs` 造成 2.5–3.6 GiB
> 解析驻留，归为 `CLASS_2`。BC-DATA-26 保留 pHash/并簇/split/count 语义，
> 删除非合同性的全量 pair 调试载荷，改存受 family 数约束且可重放最终分量的
> deterministic union witnesses。本轮只开代码/测试返工；现有正式工件不覆盖，
> S6–S9/G0/D0、audit、supersession、补采集与全部资源仍未授权。
> 版本：v0.3.28（2026-09-01）——Acceptance round 24 消费
> `P1-VLM-DATA-001` Review round 6 `REWORK_REQUIRED`：F20 恢复 S7 每次迭代的
> split 语义与冻结 F2/分层分母；F21 要求正式路径 S5 按既有
> `(camera_depth_m, frame_id)`/K 语义逐对象有界累积，S6–S8 同型债务在各阶段
> 授权前另行裁定；F22 让整表/流式 split 真正共用 `assign_atoms()` 并纠正文证。
> 逻辑 schema、门值、投影/遮挡/split 输出语义与资源授权不变；正式 S3–S5、
> S6–S9/G0/D0 仍未授权，返工后须回停点并进入 Review round 7。
> 版本：v0.3.27（2026-08-29）——Acceptance round 21 以 BC-DATA-25 归因
> `P1-VLM-DATA-001` 正式 S3 的真实归档 OOM：保留完整逐帧×逐对象
> 逻辑 schema，把 S3 `frames_catalog` 与 S4 `sample_roles` 冻结为单一逻辑
> artifact/ref 下的确定性、哈希绑定分片行流，manifest 最后原子发布，
> 全部消费者有界迭代。F1–F4、门值、frame/object 域、投影/遮挡/
> split 语义与附录 A 不变。本轮只开代码/测试返工；新候选须经停点和
> Review round 6，正式 S3–S5 续跑仍需用户新授权，S6–S9/G0/D0 继续未授权。
> v0.3.26 执行范围维护（2026-08-28）——用户逐字授权
> `P1-VLM-DATA-001` 正式 S0–S5 与一份明确标注为「审计前上界、非门
> verdict」的诊断报告；Acceptance round 20 将其限为 create-once S0–S5、
> 零审计降级条件下的只读内存上界和 `NOT_EVALUATED_PRE_AUDIT` 状态。S6–S9、
> G0/D0、人工审计、supersession/重试及全部模型/API/GPU/Play/ID/后续训练
> 仍未授权；设计版本、F1–F4、下限和运行时合同不变。
> 版本：v0.3.26（2026-08-28）——Acceptance round 17 以 BC-DATA-24
> 消歧 `P1-VLM-DATA-001` 的历史布局核验：scouting 的预测 AABB 与归档
> 裁剪真值框须在 viewport-clipped 域计算中心命中和 IoU；逐帧 truth 正常
> 缺席是无观测，不等于存在字节损坏，但不得补足冻结样本门。阈值、抽样、
> partition、m3 分支与全部资源授权边界不变；返 Implementation 后仍须停点
> 与 Review round 5。
> 版本：v0.3.25（2026-08-28）——Acceptance round 16 消费
> `P1-VLM-DATA-001` Review round 4：F16–F19 均按 CLASS_2 归 Implementation；
> BC-DATA-23 将历史布局交叉验证固定在 S2 写 `layout` 之前，以精确
> `(family, scenario_sha256)` partition 决定绑定，S3 只消费 BOUND，G0 不得
> 用空表 fallback。F17–F19 已先行落地、F16 返工中；F15 与全部正式工件、
> audit、模型/API/GPU、Unity/Play/ID 授权边界不变。
> 版本：v0.3.24（2026-08-27）——Acceptance round 10 消费
> `P1-VLM-DATA-001` Review round 2：F11–F14 均按 CLASS_2 返工，
> BC-DATA-20 将 F12 的一致性域限定为附录 A.2 当前 source unit 自身归档
> 子树内全部 manifest 与合格 snapshot；任一显式证人与点名 provider
> 不一致即只退出该 unit，不得被 sidecar/provider fallback 掩盖。F1–F10
> 的闭合、F1–F4、9-partition 既有结果和全部资源边界不变；Review round 2
> 的纯离线 `UNITY_NA` 附议维持。
> 版本：v0.3.23（2026-08-26）——Acceptance round 8 消费
> `P1-VLM-DATA-001` Review round 1 的 `REWORK_REQUIRED`：BC-DATA-13
> 以归档 source unit / scenario partition 取代 BC-DATA-8.8 的宽泛 family
> 单 SHA 与纯祖先搜索；BC-DATA-14 固定审计 key 的 `/` 域分隔；
> BC-DATA-15 将三处图像空间距离冻结为相机前向深度 z；
> BC-DATA-16…19 分离遮挡/语言域、封闭 ref/held-out 泄漏、收紧 removal
> 与布局前提并修正 dropped/splits/S8 单位。F1–F4 与全部资源边界不变；
> Review 已附议纯离线 `UNITY_NA`，但 F1–F10 仍须返工闭合。
> 版本：v0.3.22（2026-08-26）——Acceptance round 6 对
> `P1-VLM-DATA-001` 第二候选复验：326/326 双解释器与 29,923 条只读
> inventory dry-run 均通过，但 R4-1…3 仍是 §2.3 的潜伏 fail-open，故
> §4.3.1 停点未成立。BC-DATA-10/-11 要求未知 phantom 类别或已知类别
> 无同类实例时在代理构造前硬失败；BC-DATA-12 只允许归档 provider 闭集
> 内的祖先快照，永久排除可变 `runtime/scenario_config.json`。F1–F4、
> 动态目标 `car/red`、运行时合同与全部执行授权边界不变。
> 版本：v0.3.21（2026-08-26）——Acceptance round 5 根据冻结构造源、
> M0 至当前的历史等价性、独立 F23 oracle 与用户逐字事实认定
> 「这是一辆纯色的红车」，将现有归档动态目标的字段冻结为
> `class=car` / `color=red`（BC-DATA-9）。BC-DATA-8.3 收窄为只对
> 未验证字段通配；目标仍只作阻断体、永不可指称。任何按旧全
> 通配语义计算的 S7/G0 判定须按 §2.2 supersession 作废重出；
> 当前尚无正式 S1–S8 工件。F1–F4 定义、分母和下限不变，
> round 4 返工停点仍未成立。
> 版本：v0.3.20（2026-08-26）——Acceptance round 4 对
> `P1-VLM-DATA-001` 实现回传 R1–R3 作出 BC-DATA-6…8：补正冻结根闭集
> （SCENE-006 灰色替身探针只盘点、rs3 框预览作派生图）、把 arm-A void
> truth 从 `VALID_FORMAL` 拆回 `VOID_TRIAL_HOLD`，并冻结十项 fail-closed
> 确定义。因 R1/R2 会改变 S1 的确定输出，§4.3.1 停点未成立，先回
> Implementation 小范围返工；不改主研究问题、F1–F4、运行时合同或既有
> 授权边界，正式工件/人工审计/模型/API/GPU/Unity/Play 仍未授权。
> v0.3.19 实现状态维护（2026-08-26）——用户逐字「授权进行实现」，
> 打开 `P1-VLM-DATA-001` 已接受合同的代码、自动测试、临时 fixture 与
> 实现者证据；正式 S1–S8/G0/D0 工件生成、人工审计、模型/API/GPU、
> Unity/Play 与后续实验仍未授权。设计版本与运行时合同不变。
> 版本：v0.3.19（2026-08-26）——Acceptance round 3 接受
> `P1-VLM-DATA-001` revision 2（BC-DATA-1…5）：冻结 G0/D0 的归档
> inventory、schema-honest layout/projection、atom 级 split、Tier-1
> verifier、有限人工审计与 F1–F4 下限。该子合同仍是零 Play/API/GPU
> 停点；接受不授权实现、离线工件生成、人工审计、模型调用或 `UNITY_NA`，
> v0.3.18 的主研究问题与全部既有运行时合同不变。
> 版本：v0.3.18（2026-08-25）——Acceptance round 3 接受
> `P1-VLM-DIST-001` revision 2（BC-DIST-1…4）：项目当前首要研究问题改为
> verified teacher-language SFT 相对 matched template-SFT 对 ≤3B VLM
> language→box grounding 的增量；教师必要性不预设。C1 只作封顶无教师
> 热身，报告问答不进首批。同步只改变研究主张与 M6 归属；不授权 D0–D3、
> 下载、API、GPU、Unity/Play、场景/车辆改动，`PROJECT_BRIEF.md` 的运行时
> 合同和 v0.3.17 既有实现/证据原样保留。
> 版本：v0.3.17（2026-08-07）——Acceptance round 2 接受 `P1-M3-BODY-001`
> （M3′ 批次 1：世界系估计器 + 阈值式机身分配 + 首个机体运动闭环）附
> BC-BODY1-1…10。指标层全取本设计 §6 既有定义（`C_track|geom` 主、
> `C_quality` 机制），`C_point` 撤回；BC-M34-4 适配性报告由批次 1a-α
> 工具在逐字节同一的 SCENE-002 困难路线/锚点上机械产出（满足门而非
> 改序，BC-M34-1…10 语义零修改）。当时采纳系留绷紧假设（张力控制绞盘；
> §4 已知落差与 R2 行同批收窄），代码零改动。
> v0.3.16 最终状态（2026-08-05）——`UT-P1-SCENE-006-001` 非 Play 五辆
> 落点/场景合理性目检 PASS，关闭授权与 BC-B2-8 均满足；整个
> `P1-SCENE-006` 关闭为 `CLOSED_PROTOCOL_PRECONDITION_UNSATISFIED`。
> 这不是场景资格结论、`DONE` 或 `UNITY_NA`，不关闭任何下游研究义务。
> v0.3.16 终态维护（2026-08-05）——用户授权保留并关闭 T1′ 重定向为
> `CLOSED_PROTOCOL_PRECONDITION_UNSATISFIED`；BC-P2-5 禁止把空 E 分支交
> Review。整个 SCENE-006 仍停在 BC-B2-8：用户须完成五辆落点/场景合理性
> 非 Play Unity 目检，PASS 后才由 Acceptance 最终关闭 work item。
> v0.3.16 实施状态维护（2026-08-05）——BC-P2-9–11 返工经 Acceptance
> `ACCEPTED`；零额度空 E 终态最终确认为
> `T1P2_PROMPT_LAW_UNSATISFIABLE / PROTOCOL_PRECONDITION_UNSATISFIED`。
> 不形成稳定候选或 Review；继续扩 prompt 帧域须用户新的逐字授权。
> 版本：v0.3.16（2026-08-05）——Acceptance 对 `P1-SCENE-006` 阶段 T
> 返回 `REVISION_REQUESTED`：零额度 `T1P2_PROMPT_LAW_UNSATISFIABLE`
> 归因成立，主张上限仅为 `PROTOCOL_PRECONDITION_UNSATISFIED`。BC-P2-9–11
> 冻结 RGBA `1e-6` 绝对表示容差、标准 JSON `null` 边界及逐条预期 Unity
> error；返工前后均禁止诊断帧、稳定候选、Review 和正式 T1′，额度未耗。
> 版本：v0.3.15（2026-08-04）——Acceptance round 3 接受
> `P1-SCENE-006` T1′ parity-redirection revision 2（BC-P2-1–8）：probe 与
> runtime 目标共用单一生产构造源，四份独立 oracle fail-closed；prompt
> 只在 T6 warmup `[0,10]` 中选取，须不截断且落在真实 `V=1` 测量域 `D`
> 的 type-7 `[q05,q95]` 尺度/离轴双边带。`D_V` 不得以 box 状态缩域；E 空
> 只到协议前置不满足。COORD-005 两帧确认先于稳定候选；随后强制停点、独立
> Review，方可动用一次正式离线 T1′。当前只开放 Implementation 阶段 T，
> 资格仍为 `QUALIFICATION_UNDETERMINED_SPEC_GAP_F23`。
> F23 历史更正（v0.3.14，Acceptance §35）——independent Review round 8
> 对 `C_b2=d2db9f3` 的代码符合性为 `PASS`；addendum F23 证明正式 T1′
> 渲染的是无材质灰色替身而非红色运行时目标，且 prompt 截边/尺度/离轴
> parity 未冻结。因此 `4/52` 只保留为 v0.3.14 灰色探针的协议局部负结果，
> 不得用于关闭 SCENE-006 或下游研究主张。
> 版本：v0.3.14（2026-08-04）——用户逐字授权 `P1-SCENE-006` batch 2；
> 按 amendment §30 先做候选 T1′ 工具零 diff 判定，若工具变化先形成并
> 复核 `C_b2tool`，通过后才新增 `scenario.p1-scene-006.json` 并运行正式
> T1′。配置冻结为 P3 finalist `(197,30), h=16, vfov=40`、族 B 路线和五行
> relocation；不覆盖旧字节、不改运行时协议、零 Play/session/run ID。
> 版本：v0.3.13（2026-08-02）——接受 `P1-SCENE-006` amendment 1
> revision 5：授权 A `(150,108)` 与 B `(195,30)` 双筛，B 只用冻结路线的
> `(+60,-60)` 平移和 §3.3.2 五行临时车辆侧移；P1→P2→P3 保持零配置写入，
> 两族完整运行后由同一冻结评分裁决。batch 1b/1c 各自形成稳定候选并独立
> 复核；新 scenario 字节、Play/capture 与 batch-2 GO 仍未授权。
> v0.3.12（2026-08-01）——接受 `P1-SCENE-006` revision 4：困难
> 场景以 T1–T6 离线资格合同恢复指向/遮挡/机身换位的区分度；541-state
> trace、连续机身/系留净空、完整锚点安全体积与新光学 fail-closed 探针
> 冻结。当前只开放 Editor 工具 batch 1；新 scenario 字节仍需用户 GO，
> 运行时 acquisition 另案拥有。
> v0.3.11 里程碑状态（2026-08-01）——用户以“好的，关闭M2”逐字授权按
> 已核对的 D2 叙述关闭 M2；这是“已有基线 + 诚实负结果 + 明确限制”的
> `CLOSED_D2_NEGATIVE_RESULT`，不扩大任何研究主张或下游范围。
> v0.3.11 维护（2026-08-01）——落实 `DR-P1-M2-001` round 4 的
> B4/B5/B6 有界文档修订：如实登记 M2 未缓解的天花板/跨率风险、绑定逐曲线
> 证据身份，并纠正 SCENE-002 天底指向证据的解释；不改变降级范围或指标定义。
> 版本：v0.3.11（2026-07-31）——接受 `P1-M2-SCOPE-001` 与
> `P1-M3M4-SCOPE-001`：M2 以已有云台-only 曲线和 RATE-001/002 的
> 诚实负结果形成关闭候选，受控同追踪器跨帧率比较降为 M5 可选敏感性轴；
> M3′ 改为“保持可见”（估计器 + L1 + 机身分配），M4′ 改为“丢失恢复”
> （L2a/L2b/L4 + 全量仲裁），困难场景与规划器接口各有前置门。
> 版本：v0.3.10（2026-07-31）——接受 `P1-M2-RATE-003` Amendment
> DR-B：decision 工件恒记无条件 `c_geom`/`c_track`，以
> `theta_geom=0.05` 诊断条件化分母背离并绑定引用限定；难度配置审计分为
> must-pass 速度无关门与 record-only 速度导出量；采用 3 相位 × 2 难度
> 六个独立 HOLD 标定槽位和同相位两率的 SHA-256 配对锚。名义研究数据
> 会话预算为 20 次；用户已于 2026-07-31 以“同意授权”完成 0c 逐字确认。
> 版本：v0.3.9（2026-07-30）——接受 `P1-M2-RATE-003` revision 3：
> RATE 活跃路径升为共享主机 Stopwatch 身份的 v3 协议，在独立时钟停点后
> 以 D1/D2 × 5/20 Hz × 三个确定性相位完成等时配对率研究；正式/探针时域
> 冻结为 150.0 s，累计无效研究尝试达到 4 次即暂停归因并重新授权。
> 版本：v0.3.8（2026-07-29）——接受 `P1-DETECT-001` Release A5：
> non-RATE 资格会话以共享主机单调时钟的 create-once release command
> 和第一新鲜 v3 帧统一 tracker/re-anchor/control/evaluator 起点，并以
> simulation + monotonic wall 双时长和 hash-bound metrics 身份失败关闭。
> 版本：v0.3.7（2026-07-29）——接受 `P1-SCENE-004` revision 2：载体
> 开发与难度证明分场景承担，benign 短环线负责资格化与率研究测量流，
> 困难场景原样保留承担 §6 反天花板义务；冻结输入 + 姿态无关包络门、
> 采集健康门与独立记账类、只读近场 Gate 0 前置，资格会话时长按实证
> 的背景锁定时间尺度上调。
> 版本：v0.3.6（2026-07-28）——接受 `P1-SCENE-003` revision 3：以
> hash-bound 环心锚点/确定性安全回退、session-bound 双 scouting
> profile 和重新冻结的远端上尾恢复探测可行性；理论弧长预期仅作描述，
> embedding 仍由用户显式裁决，RATE-003 不自动继承该几何。
> 状态：v0.3.17 为当前运行时实施基线，v0.3.36 为当前已接受研究设计；
> M0、M2 已关闭。新构思先进入
> `docs/proposals/`，经 Codex 接受后再修改本设计；实现证据与验证门分别见
> `docs/implementation-status.md` 和 `docs/current-status.md`。
> 已知与当前 Unity 脚手架的落差见第 10 节风险清单，不在正文中假装已解决。

## 1. 研究问题与定位

**第一轮移动目标捕获合同（P1-ENG-CAPTURE-001，2026-10-09）：** 依用户(a)终局接受D2、engineering-v1生效；唯一执行合同见 `docs/proposals/P1-ENG-CAPTURE-001-moving-target-capture-round1.md` §1–8、AC-1…27及「终局裁定（第三次，依用户 (a)）」对AR1-2/3/6的解释。捕获模式VLM旁路，补偿只移中心、宽高不变，目标管理器统一提交/释放，预测只动云台、机身HOLD；兼容模式保持旧语言行为与尝试计数。K1K2K3K4代码/操作单先C/R通过消费，唯一一次Play产物另过PlayK2K4；未签维度0，未实现/复核/Unity验收，无新研究或板端主张。LOOP-002暂停与旧债不变；以下旧合同按原候选解读，现行门只见状态板。

**协作设施边界（COORD-015，2026-09-25）：** supervisor 提案按研究轨道接受；接受后修订 1 与 BC-12 保留，修订 2/3 已按用户修订 4 撤销，恢复 D6 的 Opus／Claude Code `/supervisor` 方案；合同及 BC-1…15（含 BC-13 撤销注记，BC-14/15 为 2026-09-26 `CLARIFY`）见 `docs/proposals/COORD-015-supervisor-role-record.md`。§9.2 文档与工具、Codex CLI 下载/A6、A4 与 A5/A7 合成演练证据已入库，落地停点经核对与独立复核 `R2@落地` 通过，2026-09-26 接受侧置 `DONE`；两类信封首签与首次启用仍待用户授权，未签即不启用。此协作设施不改变本节工程首版范围、运行时协议或里程碑门。

**代拍放宽设计（COORD-016，2026-09-26）：** D3 按研究轨道接受；提案 §2–4 与 BC-1…6 仅定义 D1 非递增且每提案最多 3 次、D7 预注册合同数值的用户允许有限例外、D2b 的一次冻结集定向返工及复核分路。规则/工具落地须用户直接授权，落地后的独立复核尚未进行；新决策信封须用户另签。当前已签 FAST-002 信封不含 D7/D2b，本段不改变任何现行代拍判据或运行时合同。

**当前工程首版范围（COORD-010，用户 2026-09-07 批准）：**

现有 Unity 车辆场景中，受限自然语言选目标 → 框有效性及帧对应检查 → SOT 接管
与既有跟随控制；保留人工框选/确认，迟到结果不得直接当当前帧观测。丢失或歧义
显式报告并允许重新指定；自动恢复能力由后续独立接口提案确定。先形成电脑端
可复现示例、安装与模型版本说明、指令说明、人工回退、关键测试、固定评估及失败
案例、演示和许可说明。此为后续章程范围，不声称这些能力已经实现。

旧采集/数据包按 COORD-010 §3 终止；四臂/T-G1 不再是工程首版前置。M1/M3′/M4′/M5
及 M6 不因换轨关闭；复用控制/评估缺陷仍须评估。完整限制与资产使用约束唯一落点
为 `docs/implementation-status.md`「COORD-010 — 工程继承清单」。不承诺真实飞行、
开放域语义、教师增量、Jetson 性能或论文结论；公开发布、下载/推理/训练与数据加工
均由后续独立授权处理。闭环运行时接口与截止规则见下述已接受合同；宿主实测与 K 收据已完成，执行信封见授权账本。离线数据/训练子合同见下。

**已接受的闭环接入与四类数字首测（P1-ENG-LOOP-002，2026-10-06）：** D4按engineering-v1接受；合同唯一落点为 `docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md` §1–7、AC-1…18及其追加修订。Air会话/常驻快层接既有standoff-band-v1，Jetson同一C2 Q4 JSON三态服务为单主臂、5060不启用；prompt/parse/schema/decode、六键比较链、K检查点/时间/帧身份、安全/真值隔离保持。十二类指定漏斗、意图仅评分与归属/冲突闭集支撑四类描述性数字，N-5采样与实时预览跳过不作性能比较。当前增量合同/未闭门见「OPS九题答复落实」「OPS验证额度落实与IR裁定」及「OPS基线与IR78裁定」§1–5；Ops R2 PASS已消费、R1-1…4闭合、R1-5 SCOPE_GAP/OPEN；现行追加AC-10修订7/8及新合批停点见「SUB3核清与评分上限落实」§1–5；旧AC-10修订6/Ops通过消费与旧机读绑定保留为当时记录，旧C7不满足为历史候选结论。SUB:1三候选各1次耗尽/全套新增失败0但不绿；SUB:2呈现未变本人两张附议携带/提示与用时UNKNOWN；SUB:3已用尽、本机控制套接字路径故障范围内必修，新诊断未签0，不转正式证据；正式评分全批总额3已由用户首签，常量/测试已窄修、未全套/非稳定，进度及清单补正见「合批进度与全套清单核清」，新独立复核未开，其他信封维度保持；网页替代按键窗，发令前人工发送/跳过及N-5保持；原「R4消费与诊断故障裁定」合同解释保持：原R4终局PASS已消费、原冻结集闭合；新增版本解析/来源加载修复C5已核、新K1K3独立R1 PASS已消费、当轮Overall REVIEW_PASSED，不改旧停点2/2终局；第三次诊断已核有限启动/收尾事实，非阻断笔误逐字补丁已核闭合；诊断不证明正式板端通过，缺口/操作偏差/UNKNOWN照记。runtime_build继续是二进制自报标签（b数字），明确build 0读取b0；源码发布标签b11381由原归档/构建来源链披露，不能替代实时sha或伪造自报值。N-1全套3/3用尽；B-main/N-3已签但正式G1–G5、Air正式原件/环境、现场HEAD/status/Unity日志与AC-18证据核实仍在，AC-14/15/18与AC-16板端NOT_RUN，无UNITY_NA/DONE，不关闭旧研究里程碑。诊断原件不作证据或门依据，DIAG:RESUME:1/2一次许可均耗尽；第四次独立一次诊断已核收尾、许可耗尽、窗口结束；SUB:3独立一次亦已用尽，全部旧许可/余额不恢复；诊断分工覆盖、粗账/偏差/UNKNOWN见上轮路线§1–2，现行操作分工/网页/验证边界见「OPS九题答复落实」；ACQ暂停/非verdict/清理与其他旧债/偏差/UNKNOWN保持。

**已接受的离线快层替换探针（P1-ENG-FAST-001，2026-09-24）：** D3 按 engineering-v1 接受，合同唯一落点为 `docs/proposals/P1-ENG-FAST-001-fast-layer-replacement-probe.md` §1…8、AC-1…11。复用归档帧与既有预测，按近重复原子隔离视觉提示参考池；分桶报告预训练检测召回、静态同类 margin、ByteTrack/BoT-SORT 离线窗口 ID 保持率与 VLM 四臂的 oracle 候选对照。保持率按七类互斥结局与唯一分母计算；读数只供用户决定 LOOP-001 续跑或收口，不形成换栈、闭环跟踪或 Jetson 结论。单候选 `K4` 须经 C1/R1，纯离线 `UNITY_NA` 关闭前须复核附议；§5 下载 `lap` wheel、Mac/5060 模型启动、查询和传输额度仍是申请值，须用户另行逐字授权。LOOP-001 的暂停、合同与阶段 B 余额不变。

**已接受的闭环接入合同（P1-ENG-LOOP-001，2026-09-19）：** D4 按 engineering-v1 接受，
合同唯一落点为 `docs/proposals/P1-ENG-LOOP-001-language-select-closed-loop-integration.md` §1…8、AC-1…19、八行首次接受释义及 Pending rulings 的实现期修订（最新 R-B8…11）；旧修订保留，冲突处按追加顺序。
VLM 负责受限语言候选与低频语义核验提醒；首次播种、判丢及重新指定由操作者决定。NanoTrack-v2 原段 raw_lost/raw_ok 输出沿用基线，
核验不触发自动控制或重播种；协议失败仍终止段。加载时快照绑定实际图像与元数据，初始化静音，写桥前验证身份、帧差、
加载耗时与采集年龄；HTTP 单工且客户端断联亦有总截止。旧帧的重新加载不刷新观测年龄。
阶段 A 实现/离线验证经 C→R 的 K1K3 合并停点；阶段 B 原 E1 目标由 2026-09-23 用户范围变更改为正式 P1 的一圈抽样演示门：同一人工确认段跨 106.5 s，九个预定源帧点人工核对红车及框，机身实际位移并有同帧门控命令收据；E1 事件仍如实分类，但不代替一圈通过。同次失败不由后来成功覆盖，既有 C_geom 不代替源帧目检；单次演示不构成跨场景或逐帧跟踪性能主张。接入冻结 BODY-001 阈值规划器只限本项 Python 会话，不改原规划器与控制包，新增 K2 与 K1K3 合并为 K1K2K3；新候选通过前暂停 Play/模型服务。2026-09-23 诊断 6 于 R7 候选测到机身同帧门控速度与 20.6 m 位移及两张具名样帧人眼确认，但段 2–4 首批因单批 0.4 s/2 帧追平要求 `catchup_stale` 硬停止；接受侧按 R-B12…13 追加 AC-3 修订 3（初始化后静音直至积压 ≤ K_pub 才 unmute 过五项门，T_catchup 6 s fail-closed；K_pub/T_pub/T_stall 与门内容不变）与 AC-12 修订 7（入画即指定、优先第 2 窗起点；诊断 7 仅新候选 R8 通过后用；正式 P1 连续 2 次同类失败即回用户），新候选走 C7/R8@K1K2K3，通过前零 Play。2026-09-20 的合同解释保留显式共享槽开关与静音诊断收据，
只有 WRITTEN 算实际发布；逐帧 raw_lost 不被批末 raw_ok 抹去；无预览不得确认播种，尝试编号不冒充模型调用，异常与 inconclusive 分层记录。
阶段 A 信封已于 2026-09-19 签发；实测与 K 收据已完成，2026-09-22 接受侧已消费 R2@K1K3 PASS_WITH_NOTES（F1/F2 闭合）。
现状与归因见 implementation-status 同名节，F3 非阻断记债 OPEN；阶段 B 已于 2026-09-22 获用户单独签发（见授权账本同名条目），无 Unity 通过证据，尚未 DONE。
首批追平的 0.4 s 发布门风险见提案 Acceptance rulings；失焦阻塞与新候选顺序见 Pending rulings R-B1…4。
Unity 零改动仅放行 ProjectSettings/ProjectSettings.asset 的 runInBackground: 0→1（用户同日授权）；
Assets/config/冻结 SFT 工具及其余工程设置保持，具体边界以 AC-4 修订3 为准；R4 已给 PASS_WITH_NOTES，F4/F5 闭合、F6 已应用；用户已接受仅本次同会话复核例外并由接受侧消费（提案 Acceptance rulings）。诊断5已测到旧候选首批追平；两张样帧逐张确认仍缺，诊断不替代正式证据。
用户现已授权仅本地按钮页的GUI例外与另追加3次诊断；AC-18固定CLI外壳、所见身份绑定、真实预览与两个确认截止，
AC-12修订4/5固定预算迁移、操作单择时与无自动过期语义；该按钮版已经 C3/C4 和 R5/R6 收敛，R6 仅覆盖机身跟随前候选。用户机身跟随原话已于 2026-09-23 入账，新合同与停止条件见提案 R-B8…11；阶段 B 剩余额度不增，原 F3 债仍 OPEN。
真值隔离与继承债保持；K5 另立，不作自动恢复、
跟踪性能、ReID、跨场景或 Jetson 主张，旧研究里程碑不因此关闭。

**已接受的前置盘点任务（P1-ENG-ASSET-001，2026-09-08）：** 用户主动缩小范围后，
D3 合同按 engineering-v1 接受，AC-1…6 及首次接受释义见同名提案。交付资产与 Tier-1 指令
盘点报告、一次 ≤60 张分层标签抽查、报告内只读接口缺口；只描述现有划分/对象重叠。
不运行模型，不交付固定评估集；接管实验归后续语言选框接入任务。K4 核对、独立复核与
UNITY_NA 附议保留；执行信封见账本 2026-09-08「授权收敛合同实现与本地盘点」，
2026-09-11 接受角色消费 R2@K4 PASS_WITH_NOTES 与同轮 UNITY_NA 附议，工作项 DONE。
F5 已修闭合，F8 非阻断记债 OPEN、F9 文档补丁交实现；见提案复判及缺陷账本。提案待裁定补充裁定：
AC-4 修订 2 移除会覆盖原帧的插图，以完整原帧加本行框、帧外标题做同批显示修复；
AC-4 修订 3 冻结机读代录与失败语义。首次释义逐项挂到同编号 AC 修订，AC-3 修订 3
澄清未知类别阻断体来源并要求相应回归。两派生目录合计 ≤32 MB，不增加样本/看图轮次、
模型/实验/资源额度，不修改运行时基线或旧里程碑。显示确认及用户判定已完成；本项 DONE 不关闭旧研究里程碑或授权后续接入。


**已接受的离线数据与训练任务（P1-ENG-SFT-002，2026-09-13）：** 用户按 workflow §4.2 (a)
保留范围后，接受角色正式接受 D3 并裁定 engineering-v1。唯一合同见
`docs/proposals/P1-ENG-SFT-002-lora-training-and-cloud-execution.md` §1…7、AC-1…14 与首次接受释义。
K4 交付 Unity 三态派生数据、固定 prompt v2、解析/评分、语义抽查、tokenizer 预检和冻结数据包；
K3 交付 Qwen3-VL-2B LoRA 三配置、云端代码束、零样本配对对照、盲选层选优及正式评估。
训练只用 Unity 的既有 train∪dev 减 detect-scout1，选层为该族；test 评估609行，legacy405条守恒。
已绑定且框有效的动态目标车在本项可作 car/red car 候选；不回改旧研究指称合同。
首次接受释义固定闭集、共享 gold 函数、预检绑定、数据包/代码束以及 J1…J7 抽查域；
表 G/H 为工程验收协议，§8 数据实测/训练投影分列；K3模型效果已由实现报告交付，尚未经独立复核。S6未审计、框UNVERIFIED、
颜色#27、对象重叠及描述性区间限制随使用保留。003继续暂停；AC-12在2026-09-18候选2签发日已判
NOT_RUN(SFT_003_NOT_DONE)，本候选不等待003、SynDrone额度为0。K4/K3各经接受侧只读C轮、独立复核及UNITY_NA附议；
候选1的R2@K4 PASS_WITH_NOTES与UNITY_NA正式附议已于2026-09-18由接受角色消费，AC-1…6/14验收通过；
候选2已于2026-09-18授权：云端单张RTX 5090、累计≤8 GPU·h、GPU租金≤6美元；云端A/B已执行并销毁实例，整个工作项未DONE。收尾、归因、F2/F3 OPEN与后续设计输入见implementation-status同名节。
2026-09-14追加的六行AC释义保持；#20/#21原颜色错与具名排除处置不变。抽样域缺口F1已由R2核实闭合，
用户重判新#9–#11及其截断备注保留。
2026-09-18再追加AC-10修订1…3、AC-13修订1、AC-7修订2，详见提案待裁定：训练/冒烟/选优取法接受，
预算守卫不等于实例停费；K3实跑与三份摘要已交，当前C1@K3退回实现，K3 C/R=1/0、唯一C退回已用。
待修续跑/回传身份绑定、自检参数边界和执行披露，详见提案最新核对表；K4冻结集不改。
功能门GATE_NOT_MET、词表NON_INFERIOR、跨环境NOT_RUN为待复核实现结果，不作部署或泛化结论。
5060自检只验证接口/显存/速度，不作为K3证据；云端D-1…3原话已补账并作接受侧解释，未增加预算。
非纯色“最接近”匹配未纳入当前协议，预筛#33仍只是未核验限制；运行时基线与旧里程碑不变。

**延期保留的研究问题（v0.3.19 确认性主张；恢复研究时适用）：**

> 经验证的大模型语言监督，是否能在独立语言测试集上，使 ≤3B VLM 的
> referring-expression grounding 显著优于同数据量、同训练预算的
> 程序化模板 SFT？

唯一确认性 estimand 是 verified teacher-language SFT 相对 matched
template-SFT 的 `Success@IoU≥0.5` 增量，完整合同与 BC-DIST-1…4 见
`P1-VLM-DIST-001` §15。教师是否必要是实验结论，不是设计前提；负结果
「模板监督足矣」同样是预注册结果。

**保留的系统研究问题（只适用系留开启的既有单机/系留副线，不再是当前首要主张）：**

> 在固定锚点、有限缆长与受限云台视场下，如何依据不确定的目标运动 belief，在云台角运动与机身平移之间分配控制，使**正确身份目标的可观测概率**最大化，同时最小化机身运动与系留操作风险？

延期研究的定位约束（不作为当前工程执行指令）：

- `P1-VLM-DIST-001` 的贡献候选是**经验证的教师语言监督相对程序模板
  监督的增量**，不是教师标注框、教师视觉能力或“教师天然必要”。
- 既有 SOT / YOLOE / ReID / tether-aware 规划仍是系统底盘；其已冻结
  协议、证据和负结果不因研究优先级改变而重写。原 L3 系统 VLM 仍是
  暂停的可选增强，不与本次语言数据蒸馏混称。
- C1 只作无教师工程热身；报告问答、接力采集与新场景不在首批范围。
- **Phase 2 自然延伸**：两台无人机对同一目标 belief 做可见性区间调度 + 带确认的所有权交接，交接决策蒸馏为小模型部署 8GB Jetson Orin Nano。
- 仿真运行时契约仍以 `PROJECT_BRIEF.md` 为准；系留开启时的物理简化为球面
  工作空间约束（第 10 节 R2），无缆主线按 `P1-ENG-FRAME-001` 的围栏与
  机身安全合同实现。论文中如实区分两模式，不称高保真系留动力学。
  v0.3.19 当时不授权执行或运行时修改；本项后续授权与完成门另见同名提案。

## 2. 系统架构与接口

三层结构不变：反射层（每帧：双通道感知 + 云台伺服）、规划层（1–5 Hz：机身分配、搜索、状态机）、语义层（事件触发：VLM）。

接口拆分为五个（取代 v0.2 的"只消费 TargetEstimate"——那与 L3 需要图像相矛盾）：

```
TargetEstimate    # 目标运动 belief：位置/速度/协方差
TargetIdentity    # 外观身份包：IdentityProfile 摘要（3.1 节）
PlatformState     # 机身/云台/可选缆线状态：位置、速度、云台角与限位裕度；系留裕度只在开启模式有意义
WorldModelHandle  # 路网图、遮挡结构、可见性查询（评测真值不经此进入控制器）
RecoveryContext   # 受控打包给 VLM 的关键帧 + 状态摘要，仅 L3 生成
```

`TargetEstimate` 字段（含评审补充）：

```
TargetEstimate {
  track_id, source_drone_id
  observation_timestamp, publish_timestamp, valid_until
  frame_id / coordinate_frame / units
  position_xz[2], velocity_xz[2], covariance[4x4]     # 状态见 3.5
  measurement_source        # SOT | YOLOE | fused | predicted-only
  association_confidence, tracking_state (L0–L4)
  schema_version
}
```

**诚实声明**：单机的进程内通道换成双机网络通道并非"接口不变"——时钟同步、乱序、丢包、旧消息、ACK、所有权冲突、协方差相关性是 Phase 2 的已知开放问题（第 9 节），Phase 1 只保证消息 schema 与语义可复用。

## 3. 识别与追踪框架：SOT + YOLOE 双通道

设计目标：目标无关（换目标不重训练；工程属性，不作论文卖点）、跟丢可找回、防 ID switch；当前先在电脑端仿真跑通，接口保留未来 Orin Nano 部署能力，但硬件可载性不是 M0-M6 的验收条件。

### 3.1 目标指定与 IdentityProfile

第一帧人工框选（或 YOLOE 文本提示提出候选、人工确认）。单帧单实例的身份表示偏弱（航空车辆 ReID 受视角/高度/分辨率影响显著，参见 [VRAI](https://arxiv.org/abs/1904.01400)），故身份包设计为**可信外观库**而非单 EMA：

```
IdentityProfile {
  immutable_first_view      # 首帧模板——身份锚，永不更新
  trusted_view_bank[]       # 不同方向/尺度/光照的确认视图，入库需过确认门控
  reid_centroid             # 由 view bank 聚合，而非单帧 EMA
  distractor_bank[]         # 已确认的相似干扰负样本
  model_id, embedding_version
}
```

`IdentityProfile` 即 Phase 2 跨机移交的目标身份包。

### 3.2 双通道结构与职责边界

```
                ┌─ SOT 主通道（每帧）：模板匹配局部搜索 ────┐
帧 ──► 调度器 ──┤                                          ├─► 仲裁 ─► 世界系滤波 ─► 云台伺服
                └─ YOLOE 通道（低频+事件）：类级候选提议 ───┘
```

- **SOT 主通道（每帧）**：轻量模板追踪器在预测位置附近局部搜索，负责"跟得住"。
- **YOLOE 通道（低频 + 事件）**：视觉提示检测。**职责边界修正（v0.3）**：YOLOE 视觉提示的语义是"找像这类的对象"（官方评测甚至默认按类聚合多张参考图，见 [YOLOE](https://openaccess.thecvf.com/content/ICCV2025/papers/Wang_YOLOE_Real-Time_Seeing_Anything_ICCV_2025_paper.pdf)），**只承担候选提议，不承担实例身份确认**。
- **实例身份**由独立的 ReID 打分负责（对 `reid_centroid` 与 view bank 的相似度 + distractor margin）。
- 重捕获接受分数：`YOLOE 提议分 × ReID 身份分 × 运动似然（马氏距离）`，三者缺一不可。

### 3.3 仲裁与模板管理（防漂移、防 ID switch）

1. **一致**（IoU 高 + ReID 高）：采纳 SOT 框；仅此时允许更新滚动模板 / view bank 入库；
2. **冲突**（YOLOE+ReID 候选与 SOT 框不重叠）：**不单帧重播种**——进入 tentative 状态，需连续 N-of-M 帧、运动一致性、身份 margin 三重确认后才重播种 SOT，否则维持原轨迹并升高不确定性。单帧重播种会把漂移变成 ID switch；
3. **SOT 置信骤降**：立即触发一次 YOLOE 校验；
4. **双通道均无果**：报丢失，入 L1。

漂移重播种次数、tentative 拒绝次数均记入诊断指标。

### 3.4 算法选型、桌面仿真路径与后续部署风险

| 位置 | 首选 | 备选 / 对照 | 备注 |
|---|---|---|---|
| SOT 主通道 | NanoTrack / HiT-Small 级 | OpenCV CSRT（占位+经典对照）；TCTrack、Aba-ViTrack（可选对照） | 同一接口可插拔 |
| 候选提议 | YOLOE-S 视觉提示 | YOLO11n（COCO car 类基线）；颜色阈值（调试占位） | 同一"目标提议器"接口 |
| 实例身份 | 轻量 ReID 头（view bank 打分） | — | 与提议器解耦 |
| 离线参照 | SAM 2 / SAMURAI | — | 仅仿真离线：轨迹参照与上界；不上板 |

**本场景局部备选（`P1-ENG-FAST-002`，2026-09-28 阶段 1 描述性收口）**：`det-assoc-v1` 把在域训练的 YOLO11 检测器与 ByteTrack/BoT-SORT 关联封装为可显式选用的 `TrackLoop` 插件，限本城市和目标外观；换目标需要重训练。阶段 1 为 `QUALIFICATION_GATE_NOT_MET`/`ENDED`，代码未获独立复核，原读数和 AC-4 口径偏差见同名提案「阶段 1 收口裁定」。它不改缺省插件，不取代本节目标无关（换目标不重训练）的工程属性，也不自动成为 `P1-ENG-LOOP-001` 的已接受替换；插件复核由已接受的 `P1-ENG-ACQ-001` K3 承接。本段不签发训练、Unity 或 Play 额度。

**已接受的 M2a 基线（`P1-TRACK-001`）**：先在桌面端以 5 Hz 接入 OpenCV
CSRT，作为长期保留的经典对照与接口占位，不据此关闭正式 M2。CSRT 的公开更新
接口只返回成功标志与框，不提供校准置信度；有效观测为兼容现有协议写入诊断
占位值 `1.0`，并在运行日志标记 `confidence_source="placeholder"`，不得把它
解释为模型置信度或设置 CSRT 置信阈值。原设计把正式 M2 的 5/20 Hz 对比
交给独立率研究；v0.3.11 保留三代协议与负结果，但不再把完成受控跨帧率
对比设为 M2 关闭前提。

**已接受的深度 SOT 候选（`P1-TRACK-002`，2026-07-24）**：桌面仿真采用
现有 OpenCV DNN `TrackerNano` API 与冻结的 NanoTrack-v2 backbone/neck-head
ONNX 模型。模型来源、不可变 commit、许可证、双 SHA-256、OpenCV/DNN backend
和预处理身份必须入 manifest；缺失或不匹配时 fail-closed，不得静默回退
CSRT。`getTrackingScore()` 只作为未校准诊断分数；上游无可辩护的默认丢失
阈值，因此本项不声称解决“漂移不自知”，也不使用项目数据选择阈值。YOLOE
检测/仲裁仍是独立后续通道。插件核心可先实现，但关闭仍依赖 Sonnet 复核和
继任率研究基础设施上的预注册 30 s Unity 资格试跑。

**已接受的最小安全三门再锚定载体（`P1-DETECT-001`，2026-07-28，
Codex base Round 2 + Amendment A1 Round 2）**：用户授权把一个有界
M4 子集提前为 M2 载体前置。
PyTorch YOLOE 只作类级候选提议；控制生效的重播种还必须通过冻结
pinned DINOv2 ViT-S/14 通用外观嵌入门、世界系 LOS 运动门、候选 margin
与连续轮次一致性。DINOv2 标准代码/权重由 Meta 明确以 Apache-2.0 发布；
源码固定 commit `7764ea0f912e53c92e82eb78a2a1631e92725fc8`，预处理固定
为 PIL/RGB bicubic 256→center-crop 224→ToTensor→ImageNet normalization，
嵌入为最终 LayerNorm 后 384 维 CLS token。它不宣称通用嵌入等价于完整
车辆 ReID/view bank，不主张跨模型阈值等价，也不把相对 SOT-only 的收益
单独归因给 YOLOE。异步候选只能在 detector 源帧初始化新 NanoTrack，再
严格顺序重放保留帧，并在同一主循环临界区确认 replay 头帧与当前已消费帧
完全相等后原子替换；禁止跨帧直接 `init()`。模型、阈值、worker/失败预算、
真值隔离和验收以接受提案及 bindings 为准。下载 pinned 源码/标准权重仍需
用户另行明确同意；首次导入/反序列化前须补齐源码与权重 identity/hash/
肯定许可证据并排除特殊非商业权重。实现达到稳定候选后必须停在 Sonnet
独立复核门。

**已接受的同主机时钟修复（`P1-DETECT-001` Clock A4，2026-07-29，
Codex `ACCEPTED`）**：普通帧使用 `tethered-sensor-frame/v3`，并把
`System.Diagnostics.Stopwatch` 的有限非负秒值与
`capture_monotonic_clock_id=system-stopwatch/v1` 一起发布；当前
macOS/Unity Mono 资格环境已验证该值与 Python `time.monotonic()` 同源于
主机 `mach_absolute_time()` epoch。重锚路径只接受精确 v3/clock identity，
并在任何模型加载或 run 目录创建前校验初始化帧；运行时入口二次校验。
RATE-002 的 v2 仍保留其 Editor 进程相对时钟语义，且不得与重锚配置组合。
历史 v1 仅可由离线 scouting 兼容读取，不得进入新追踪/重锚测量。模型、
阈值、stale 上限、指标、真值隔离、场景与资格门均不变；候选必须重新过
Sonnet，复核前不得启动新资格会话。

**已接受的 non-RATE 资格 release 边界（`P1-DETECT-001` Release A5，
2026-07-29，Codex `ACCEPTED`）**：仅对 SCENE-004 follow、
NanoTrack-v2 + re-anchor 资格会话，tracker 初始化后发布 create-once
ready；用户在 Unity 暂停期间发出 hash-bound create-once release command。
command 之前的 retained/backlog 帧可供 SOT 顺序追赶，但保持 HOLD：不发布
observation/control、不释放 re-anchor，也不进入 duration、cadence 或主
指标。第一个满足 command 共享 host-monotonic 边界的普通 v3 live frame
同时成为 tracker ack、simulation/monotonic-wall、re-anchor、control 和
`CoverageEvaluator` 起点；evaluator 在自身内部清空此前真值累计并把该
frame/run/command/active-marker identity 写入 metrics。Python 仅接受与
ack 一致且达到计划 simulation duration 的 metrics snapshot，session
完成还要求 simulation 与 monotonic wall span 均 ≥150 s。RATE-002/v2
互斥，Unix span 只作审计，所有 run-local provenance 永久保留；模型、
阈值、指标公式和几何不变。跨 Unity 会话保留的 active marker 只有在其
command 的 Unix 与共享 host-monotonic 时间都严格晚于当前 evaluator
session 启动、且场景身份匹配时才可 arm；旧/外场景 marker 对普通会话
保持 inert，不重置聚合、不阻断 observation、不写入 foreign metrics
identity。通过该 ownership/freshness 门后仍执行完整哈希失败关闭。A5
候选必须过 Sonnet，复核前不得准备 qual-3。

**已接受的 scouting 相机上界绑定（`P1-DETECT-001` Capture A2）**：
仅在 hash-bound `p1-detect-scouting` 非测量会话中，Unity 侧允许真值目标
通过既有 `TetheredGimbal.LookAtWorld` plant 驱动相机；45° off-nadir
限位、slew 与 saturation 原样保留，外部云台 receiver 禁用。manifest 与
truth sidecar 固定记录 `gimbal_driver=truth_directed_scouting`，controller
仍零引用 Unity 真值。离线 recall 只标为
`ORACLE_POINTED_DETECTABILITY_UPPER_BOUND`，不能写成闭环 recall；闭环
可行性仍由三门载体的独立资格会话裁定。

**已接受的 scouting 恢复绑定（`P1-DETECT-001` Recovery A3）**：
Unity truth box 只允许精确键集合 `{x,y,width,height}` 的有限数值对象，
离线/测试兼容路径另允许有限四元素序列；IoU 与 embedding 共用同一严格
入口，其他形态 fail-closed。首次无效结果必须字节保留；重分析使用独立
create-once plan/result/supersession/completion identity，绑定新旧结果、
原因和 plan hash，旧 close 不得签发完成。真实 capture sidecar 至少一份
按字节入回归 fixture。Unity writer 只可规范化合法框右/下端点不超过
`1e-5` 的浮点舍入越界；既有缺失 sidecar 不回填、不重采，仍按 recall miss
处理。A3 不授权调阈值、改几何或自动 go/no-go，独立复核通过前不得对真实
capture 执行重分析。

**已接受的 Option B 场景恢复绑定（`P1-SCENE-003` revision 3，
2026-07-28，Codex Round 3）**：唯一物理变化是把锚点候选从
`(132.0, 0.2, 117.0)` 移至路线包围盒中心 `(150.0, 0.2, 90.0)`；
若环心不满足合法支撑面与 Minkowski 膨胀后的锚点柱、垂直系留走廊、
悬停球闭集净空审计，则在中心半径 10 m、0.5 m 网格上按
`距离 → x → z` 确定性选择首个合法点，全部失败即阻断。最终位置的
route/config、几何工件、斜距/像素带及上尾分位全部进入 hash 链。

scout-1 以只读 adapter 封存为 `scout-1-legacy/v1`，不得重跑模型、重写
旧工件或伪造 lifecycle；scout-2 使用全新 create-once identity 和
`p1-scene-003-scout-2/v1`，显式绑定 profile/geometry hash。新 gating
远端为 `slant_range >= 40.0 m` 的 44.44% 较宽上尾；描述性子带保持
15.98% 上尾比例。实际 recall 分母只取
`remote_visible + missing_pair_misses`，理论 range-eligible tick
预期不作为分母或完备性下限，missing pair 计 miss 而非双重判为 capture
不完整。recall 达标后还需至少 10 个 distractor cosine 样本，并向用户
提供目标/干扰完整分布、目标 `0.5` 门通过数和逐帧 `0.1` margin 通过数；
用户显式 GO 前不得资格化。新 `C_geom` 必须记录，RATE-003 从不自动继承
该几何；`C_geom >= 0.95` 时还须用户与 `DR-P1-M2-001` 升级裁定。全部
真值仍只进入 `CoverageEvaluator`/离线评估链，不进入 controller 或感知端。

**实现门结果（2026-07-28）**：上述 Option B 尚未成为运行时场景。真实
场景审计在第一道支撑门即返回 `BLOCKED_ANCHOR_PLACEMENT`：10 m 回退圆内
1,257/1,257 候选的实际 grass-tile 支撑高程约为 `0.0000013 m`，不满足
冻结的锚点 `y=0.2 ±0.05 m`；体育场 footprint 还覆盖整个候选圆。旧
scout-1 场景/工件保持不变，scout-2 未创建。任何改变候选区域、回退半径、
支撑高程解释或体育场的方案必须先形成新的设计修订并由 Codex 接受。

**已接受的分场景绑定（`P1-SCENE-004` revision 2，2026-07-29，Codex
Round 2，`ACCEPTED_WITH_BINDING_CLARIFICATIONS`）**：用户 2026-07-29
决定把载体开发与难度证明拆到两个场景。**困难场景（含 B2、scout-1 全部
证据与场景本体）原样保留**，继续承担 §6 反天花板义务与 M4/M5 实验；
新增 **benign 开发场景**只负责把云台-only 反射层跑到可资格化，并在所有
工件与报告中显式标注 `benign-coverage carrier development scenario`，
不得冒充正式实验难度。环心锚点构想**仅对 body-static 阶段关闭**：M3
机身移动接手远距问题，SCENE-003 的体育场视线几何与净空审计机制转为
M3 规划输入。

冻结输入：路旁草地锚点候选中心 `(140.0, 112.0)`（锚点 y **由实测支撑
面高程导出**，草地 ≈`1.3e-6 m`；`0.2` 是路面高程而非全局锚点契约——
这是 SCENE-003 阻断的直接教训），悬停 `initial_altitude_m = 25.0`
（相机 y = 支撑面高程 + 25.0），z=120 大路上 ~30×6 m 双车道环线，目标
速度 2.0 m/s。**`ground_plane_y_m` 继续绑定车辆行驶面 `0.2000004`，
不得随锚点支撑高程改为 0**。

包络门（几何工件从冻结字节导出，逐项同时输出裕度）：最大斜距 ≤32 m、
全环最大 off-nadir ≤45° **且余量 ≥5.0°**、环周期 ∈[30,45] s、全环
`min(w,h)` 的 **p05 ≥25 px**。像素判据取姿态无关分位量而非框高最小
值：scout-1 在同一 25.0–31.0 m 斜距带的 204 个实测样本中，框高分布
43.6–86.5 px（10.3% <60 px），而 `min(w,h)` 的 p05 为 30.5 px——框的
长短轴取决于航向与云台偏航，不只取决于距离。锚点回退 lattice 的每个
候选必须**同时**通过支撑/净空门与本包络门。

scouting 记账（`p1-scene-004-scout-3/v1`，create-once 全新链，A2/A3
语义继承，legacy 只读审计不变）：真值 writer 在"目标可见但框不可投影"
时**不得抛出致缺文件**，每个已发布帧必须落结构化文档；
`TARGET_VISIBLE_UNPROJECTABLE` 为**独立记账类，排除在 gating 分母之外**
并单独设比率门（≤2%），超门指向指向包络/采集问题；采集健康门
（缺失率 >5% → `CAPTURE_INCOMPLETE`）**严格先于** recall 判定，
gating recall 取**严格分母**（仅成对可见）≥0.7，保守分母口径并报。
干扰车"完整在图内且最小边 ≥16 px"的有效样本机会下界 ≥10 必须在采集前
由几何工件导出；该 16 px 只存在于几何工件，
`config/detector-reanchor.models.json` 的 `minimum_crop_side_px = 2`
与其配置哈希保持字节不变。

真值 sidecar 的写路径自 SCENE-004 起**只发 `p1-detect-scouting-truth/v2`**；
v1 仅作为已冻结 scout-1 档案的**只读**格式保留。scout-2 若在 M3 后恢复，
必须使用 profile 化的离线工具，不得直接复用 `run_detector_scouting.py`
读取新采集。真值目录由 session 的 `SessionRoot` 导出，不得在 writer 内写死
profile 名——否则新 profile 会静默继承别人的路径，把每个 tick 记成缺失对。

前置门：接受后第一步是**只读近场 Gate 0 探针**——在 scout-1 冻结字节
的沙箱副本上跑 pin 住的模型，不动场景、不建 profile、不占用 Unity 会话、
不写任何冻结产物；cosine 统计须排除参考帧本身；recall **<0.7 一律返回
用户裁决**（<0.5 为 `PROBE_MODEL_SELECTION_BLOCK` 选型级发现），
≥0.7 方可开始实现批次。

**资格会话时长（修正 `P1-DETECT-001` 验收 6）**：benign 几何下"≥1 环
周期"退化为 ~36 s，低于 B2 实证的 ~40 s 背景锁定点，且 DETECT-001 已
记录 30 s 级窗口无预测力。本场景的资格会话改为**墙钟 ≥150 s 且 ≥4 个
完整环**（已实现几何工件的权威环周期为 `31.0711 s`，提案期的 `~36 s`
仅为旧估计）；`C_track|geom ≥0.4`、incorrect/matched <0.5 等其余判据不变；
困难场景下的"≥1 环周期"原文保留。按 v0.3.11，benign 几何下 5/20 Hz
可能同近天花板的区分度风险在 M2 **未被处置**：`P1-M2-RATE-003` 已降为
deferred optional M5 asset，受控跨率诊断仅由 M5 可选敏感性轴在取得新范围
授权后承担。反天花板/困难场景义务指定给 `P1-SCENE-005`、M3′/M4′；其中
`P1-SCENE-005` 当前仍为 `PAUSED_AWAITING_USER_SELECTION` 的未裁定提案，因此这些是
后续责任归属，不是 M2 当前已有的缓解措施。

**已接受的困难场景重建绑定（`P1-SCENE-006` revision 4，2026-08-01，
Acceptance round 5，`ACCEPTED_WITH_BINDING_CLARIFICATIONS`）**：该 ID 只
建立满足 §6 反天花板义务的候选场景资格合同，不修改 M3′ 控制器、
WorldModel、BC-M34-4(b) 或 DETECT criterion 4。旧困难场景的三个负结果
保持：路线距锚点最小 0.5 m、远端约 8.77 px 且 recall 0/45、云台饱和
0.7353 而 frustum loss 为 0。新候选优先搜索环心锚点、30° VFOV、20 m
悬停，但三者均为 `UNEVALUATED_CANDIDATE`，Acceptance 不预签通过。

共同离线评估域使用精确复现 `LoopTargetVehicle.Step(0.2)` 的 541-state
trace：`s_0` 为放置语义后的唯一 pre-Step `t=0` 状态，`s_1…s_540` 为
540 个等权覆盖率样本；每个 HOLD/station 从 `Euler(90,0,0)` 云台初态
独立重放真实 45° clamp、120°/s `RotateTowards` 语义。T1/T1′/T2/T3
固定在 `p_hover=(anchor_x,support_y+altitude,anchor_z)`；T4 枚举以锚点
为原点、4 m 网格、AGL `{8,12,16,20,24,28,32}` m、系留球内的站点。
truth-directed 结果只进入评估工件，不得进入 controller 或 WorldModel。

资格门冻结为：T1 在 rays-off、15 点、可见比例 `≥0.2` 的逐样本
`C_frustum` boolean 域上，以真实 renderer truth box 的 `min(w,h)` type-7
p05 `≥25 px`；T2 `L_point=1-C_frustum ∈[0.10,0.50]`；T3
`L_occ=C_frustum-C_geom ∈[0.05,0.40]` 且总损失
`1-C_geom ∈[0.15,0.60]`；T4 仅要求合法 station gain `≥0.05`，明确不是
BC-M34-4(b) 充分见证。T6 只是在固定 `p_hover` 上按离轴 argmin 相位和
预注册 `K_acq=10` 工程窗口验证存在首个 `V=1` 且其 `min(w,h)` 不低于
T1 域中位数的 **Editor 离线候选门**；`s_init` 不进入 scenario schema，
也不证明正式会话已有运行时 acquisition。

T4 的每个入选站点必须持有 `p_hover→p` 直线路径证书：rest-to-rest、
速度 ≤4 m/s、加速度 ≤4 m/s²，endpoint-inclusive `δ=0.25 m` 采样；机体
有效球半径 1.625 m，系留有效胶囊半径 0.375 m。锚点端
`d_trim=1.70 m` 仅忽略唯一实测支撑实例，头段其他 collider 与余段全部
collider 仍失败关闭。T5 使用 support-derived anchor y，并与车辆/LOS
`ground_plane_y_m=0.2000004` 分列；锚柱 1.5 m、走廊 1.0 m、悬停球
1.5 m、垂直参与带 `[support_y,hover_y+1.5 m]`，严格内点、闭集相切、
真实 TRS 和全静态障碍集均 fail closed。环心 10 m/0.5 m lattice 必须在
任何配置写入前做零写入 preflight；全拒绝即
`BLOCKED_ANCHOR_PLACEMENT_V2`，禁止扩大区域或移除体育场。

T1′ 在候选光学上使用 `k=15,20,…,540` 的 106 帧与不相交的 T6 prompt，
目标/干扰样本各至少 40，严格 recall 工程门为 0.90。任一 `V=1` tick
缺图像/truth pair 为 `PROBE_INCOMPLETE`；域成员 truth box 不可投影为
`PROBE_FIDELITY_CONTRADICTION`；二者均不产门值。recall ≥0.90 只到
`AWAITING_EMBEDDING_FEASIBILITY_REVIEW`：实现者必须交付逐帧 target、
max-distractor、margin 与冻结 0.5/0.1 双门分布，工具永不自动 PASS，最终
门态由 Acceptance 单列裁定。

**已接受的 post-V2 锚点/路线 amendment（revision 5，2026-08-02，
Acceptance round 6，`ACCEPTED`，BC-AM1-1–6）**：在 revision 4 的全部门、
阈值、安全参数、候选格 `10 m / 0.5 m / 1257`、排序与 horizon 不变的前提
下，候选格中心从环心改为 A `(150,108)` 和 B `(195,30)` 双筛；A 复用冻结
路线，B 只用该路线的 `(+60,-60)` 平移，并只在临时 Edit Mode 场景逐行应用
提案 §3.3.2 的五行车辆侧移。两族均须完整执行 P1/P2，不设优先级或提前停止，
统一进入冻结决赛集 `F`、score 与 tie-break；P3 失败不得顺延次名。

P1 在五个冻结高度逐 `(anchor,altitude)` 跑完整 T5；P2 只在 P1 合格对的
预注册网格上权威计算 T1/T2/T3；P3 只对唯一决赛点运行 T4/T6 与 T5 复核。
任一具名失败均返回设计，不得就地扩大网格、改阈值、删车或换点。batch 1b
完成 F1/F2/F4、工具、B 路线 SCENE-002 审计、P1/P2 后停止并独立复核；只有
复核通过才可开始 batch 1c 的 P3，后者再次形成稳定候选停点。版本身份按提案
§5.6 的冻结路径集、`tool_commit`/`capture_commit`、四层 commit 拓扑和零 diff
证明执行。两批均禁止配置/场景字节、Play/capture、scenario/session/run ID；
batch 2 的用户 GO 已于 2026-08-04 逐字取得，实施受提案 §30 约束。

实施分两停点。当前只开放 batch 1：`Assets/TetheredTracking/Editor/`、
`Assets/TetheredTracking/Tests/EditMode/`、SCENE-006 专用 `tools/` 与对应
Python 测试、证据和 `runtime/` 新目录；`config/`、运行时 `Scripts/`、
既有通用分析器、Play、scenario/session/run ID 均禁止。batch 1 交付工具、
现场景 T1–T5 对照与候选格 preflight 后停止，等待 Acceptance 写入审计与独立复核。
preflight 非全拒绝且复核通过后才可请求的 batch-2 用户 GO 已取得。batch 2
仍是独立停点，不得覆盖任何旧配置/哈希，也不包含运行时 acquisition/
初始化协议；工具若变化，须在正式配置与 T1′ 工件前另过 `C_b2tool` 停点。
`C_b2tool′ = b85f461` 已于 independent Review round 7 获得 `PASS`，Acceptance
已按提案 §33 明确开放 BC-B2-3/5 配置阶段：先完成默认配置直接读者对账，
再形成 self-diff 只含唯一新配置的 `C_b2config`，随后才可按 BC-B2-6 运行
离线 T1′；配置、工件与证据形成后仍须停止于 `C_b2`，等待 Acceptance
写入审计、T1′ 单列处分和独立复核。BC-B2-8 与最终非 Play Unity 视觉检查
继续生效；这不关闭 M1、M3′ 或 DETECT criterion 4。
配置阶段现已按序完成并停止于 `C_b2 = d2db9f3`：唯一新配置
`C_b2config = 0e6407b`，正式 T1′ 完整捕获且样本下限满足，但冻结检测器
recall 仅 `4/52 = 0.076923`，故 Acceptance §34 单列裁定为
**`T1PRIME_FAIL_RECALL_BELOW_FAIL_MAX`**。该负结果禁止在当前批次通过改门、
改场景或改模型补救，正等待完整 `d21aafc..d2db9f3` 独立复核；即使复核
确认结果有效，BC-B2-8 的非 Play Unity 视觉检查仍是 work item 收束前置。
Review round 8 已对该端点给出代码符合性 `PASS`，但其 F23 addendum 发现
probe/runtime 外观与 prompt-domain parity 未进入 v0.3.14 合同。Acceptance
§35 因而保留 §34 的协议局部 `FAIL` 历史，撤回其作为候选场景最终资格
结论的效力；门回到 `QUALIFICATION_UNDETERMINED_SPEC_GAP_F23`。用户随后
授权有界重定，parity-redirection revision 2 已在 Acceptance round 3 以
BC-P2-1–8 接受：单一生产构造源 + 独立 oracle；`D_V={V=1}` 全员 box `OK`
后才计算 type-7 `[q05,q95]`；prompt 池保持 T6 `[0,10]`，E 空只到协议前置
不满足；COORD-005 两帧人眼确认发生在稳定候选之前。当前仅开放 T 阶段实现，
其后仍须 H→Acceptance 停点审计（base `d2db9f3`）→ independent Review，
`PASS` 后方可运行一次正式离线 T1′。M3′/DETECT criterion 4 不改变。

阶段 T 的首次零额度选择已命中 BC-P2-5：`D_V=D=52` 全员 box `OK`，但
warmup `[0,10]` 的 E 为空，故终态为 `T1P2_PROMPT_LAW_UNSATISFIABLE`，
资格只到 `QUALIFICATION_UNDETERMINED / PROTOCOL_PRECONDITION_UNSATISFIED`。
Acceptance v0.3.16 要求同范围返工 BC-P2-9–11：四份 oracle 仍硬钉作者
RGBA，仅逐分量允许 `1e-6` Unity 表示误差；提交证据必须是严格 JSON，
不可用数值序列化为 `null`；Unity 测试只逐条期待已知材质消息，不得吞掉
其他 error。返工不会开放 H/S/Review/X，也不授权扩 prompt 帧域。

**R0 拆分为两个时间尺度**：[Ultralytics 文档明确](https://docs.ultralytics.com/models/yoloe) YOLOE 标准导出时提示被烘进产物，导出产物不支持动态 `set_classes()` / 新视觉提示——与“换目标只换第一帧”冲突。

- **当前电脑仿真（M0-M6）**：M0 只验证 PyTorch 动态视觉提示与标准 ONNX
  的能力边界。实测后选择 **PyTorch YOLOE 作为仿真运行时**；标准 ONNX 仅作
  静态导出证据，不承担动态换目标。
- **未来部署（M7）**：只有用户显式启动 Orin/Jetson 部署后才评估 TensorRT，
  CUDA、engine 构建、延迟、内存与热约束。当前电脑不下载 TensorRT，也不因
  缺少 NVIDIA 环境阻塞 M0-M6。

M7 若仍要求动态提示部署，再比较三条候选出路：

1. 拆分推理图，使 VPE（视觉提示嵌入）成为引擎的运行时输入；
2. 每次任务初始化时重建/导出引擎（评估耗时是否可接受）；
3. prompt encoder 留 PyTorch，检测主干走 TensorRT。

这不是同一里程碑的“两级验证”：本机 PyTorch/ONNX 属于 M0，NVIDIA/TensorRT
属于未来 M7，两者的状态和证据完全分开。

**M0 本地证据（2026-07-22，Sonnet 独立复核 PASS）**：在 Unity 连续帧上先
以红色目标车提示运行 PyTorch 并导出 ONNX，再以同一参考帧中的黄色车辆作为
不同提示重试。
PyTorch 提示推理、ONNX 导出和 ONNX 静态推理均成功，但导出模型通过 `YOLOE`
和通用 `YOLO` 两条加载路径都拒绝运行时 `refer_image/visual_prompts`。因此
排除“单个标准固定导出 + 每任务运行时换视觉提示”，并确定当前仿真使用
PyTorch 动态提示路径。每目标导出与自定义 VPE/主干拆分仅在未来 M7 部署
阶段按需比较。可复现实验记录见
`docs/evidence/P1-YOLOE-001-local-onnx.md`。

### 3.5 世界系状态估计

- 状态取地面运动的 `[x, z, vx, vz]`（4×4 协方差）；若后续 IMM 引入 CT 转弯模型（含航向/转率），需定义到该状态的一致投影后再发布。
- 观测由框底中心与地面求交获得；**测量协方差由像素不确定性 + 相机姿态不确定性 + 地面高度不确定性传播**，不用固定噪声。已知限制（如实写入论文）：斜视、坡路、遮挡截断时该几何模型误差急剧增大。
- 消息带双时间戳（观测/发布）与 `valid_until`。
- M2a 的无滤波 LOS 占位必须通过显式、有限且无默认值的
  `--ground-plane-y-m` 标定水平面；追踪器与实验 helper 都不得从目标路线
  真值推导该值。普通 SOT 失败进入可继续消费后续连续帧的 `LOST`，不可恢复的
  帧缺口或 frame-ID 重置进入终止本次进程的 `ERROR_REINIT_REQUIRED`。

**M3′ 归属（`P1-M3M4-SCOPE-001`）**：估计器在无新量测时的
predicted-only 传播、协方差膨胀与 T1 共同构成 L1，因此 L1 随本节进入
M3′；L2a/L2b/L4 状态机仍归 M4′。控制器侧遮挡先验的物料来源、离线构建、
schema/hash 和查询语义必须在 M3′ 实现提案中先行接受，运行时不得读取
evaluator、truth sidecar 或逐帧目标真值。

### 3.6 云台控制：LOS pointing + 像素残差修正

命名修正（v0.3）：主通道是**基于世界系目标估计的视线指向（LOS pointing）**，不是完整 PBVS（无目标位姿）。结构不变：指向 Kalman 预测位置（前馈），有检测时以像素残差小增益修正系统性偏差；45° 限位与限速饱和处理，限位裕度上报 `PlatformState`。

**多率架构**（显式声明，取代 v0.2"提帧不影响方法"的说法——帧率改变闭环性能，只能说方法支持多率实现，结果分帧率报告）：

| 回路 | 频率 |
|---|---|
| 图像/SOT/仲裁 | 5 Hz 起步，M2 评估 20 Hz，两档分别报告 |
| 估计传播 + 云台角速率控制 | 50 Hz（预测外推，不依赖新帧） |
| 规划层 | 1–5 Hz |
| 语义层 | 事件触发 |

v0.3.11 限定：上表只登记支持的运行点与历史协议条件，不授权把现有 5/20 Hz
曲线并列成效果比较。受控同追踪器跨帧率对比未完成；现有曲线不可用于估计
帧率效应，也不支持任何跨帧率定量或因果结论。该未缓解风险转入 M5 可选
敏感性轴，启动时须重新取得用户范围授权。

执行拆分：`P1-TRACK-001` 交付并记录 5 Hz M2a 的 follow/nadir 基线；
RATE-001/002/003 保留完整协议、复核与终止证据。按 v0.3.11，M2 关闭不再
等待 RATE-003 研究会话；同追踪器受控 5/20 Hz 对比降为 M5 的可选敏感性
轴，须由用户届时显式启动。

**已接受的 M2 帧率协议（`P1-M2-RATE-001`）**：采用固定 N=3 的
`{5,20} Hz × {follow,nadir}` 设计，逐 run 报告并以 cell 中位数/极差汇总。
两档分别使用预先标注并记录图像 SHA-256 的冻结初始化帧/框；follow 与 nadir
在同一帧率档共享初始 nadir 参考。确定性初始化取两档共同的
`simulation_time_s ∈ [7.0,8.0)` 半开窗口内首个完整帧；原 `[3.0,4.0)`
窗口因首次 Unity 标定发现目标与干扰车持续重叠，在任何数据产生前由用户批准
作废。冻结参考框前必须展示实际矩形叠加图供操作者确认。除 `capture_hz`、
证据用 `scenario_id`、
派生 init frame 外，只允许把 `retained_frame_count` 和
`maximum_pending_frame_count` 按帧率缩放以保持时间窗口相等。20 Hz 是正式
条件，不得以 10 Hz 替代；墙钟采集节奏、仿真时间采样节奏、tracker 延迟与
backlog 分开报告。对比只作闭环诊断，不声称单独识别采样与自运动因果。
墙钟证据同时保留全体帧的 raw cadence；S1 只使用
`capture_unix_s >= manifest.created_unix_s` 的 post-launch cohort，以排除
协议强制的暂停框确认时间。cutoff 之后发生的运行中停顿不得剔除；cutoff
无效或 eligible 样本不足时 S1 fail-closed。该修订由真实 20 Hz r1/r2 中
被误计的 `99.031/74.757 s` 操作者停顿触发，并经用户批准。

任何 rate-study run 被采信前，必须用直接 Edit Mode 测试覆盖 evaluator 的
时长积分、`1/capture_hz` 回退、matched/incorrect/duplicate/unmatched 和
pending 修剪。20 Hz follow 的 cell 中位数若
`C_track_given_geom < 25%`，或首次 `LOST` 前的连续跟踪时长中位数短于一个
路线环路，则触发冻结权重、零微调的 `P1-TRACK-002` 提案；CSRT 始终保留为
经典对照。该触发不自动授权实现。正式 M2 关闭仍需独立
`DR-P1-M2-001` 新鲜上下文设计审查。

**RATE-001 关闭处置（2026-07-24）**：首批 CSRT 2×2×3 产物永久保留，但
初始化帧在 tracker 启动时已陈旧并形成突发积压；11 个 run 各有一次发布而
evaluator 匹配为零，另一个 run 出现 spurious-`ok` 漂移。该批次的科学状态为
`BATCH1_PROTOCOL_INVALID`，R1/R2 为 `UNDETERMINED_INVALID_INPUT`，不得用于
正式帧率或 SOT 升级结论。`P1-M2-RATE-001` 因此以
`CLOSED_PROTOCOL_INVALID` 关闭且不再测量；正式 5/20 Hz 义务转交独立的
`P1-M2-RATE-002`。

**已接受的继任实验协议（`P1-M2-RATE-002`，2026-07-24）**：Unity 是实验
状态属主，运行态仅含 `HOLD → RELEASED` 与终态 `ABORTED`，不存在独立
`ARMED`。追踪进程在 HOLD 期逐帧原子发布带序号、同主机单调时间和完整
tracker/model/init 身份的 v2 ready 心跳；操作者确认后，协调器把确切 ready
字节及哈希绑定进 release 命令，Unity 在处理命令的同一 Update 周期内复核
全部身份及 `0 ≤ current_frame_id − last_processed_frame_id ≤ 1`，通过才同时
启用目标运动、控制施加、evaluator 和测量时间基。release command/ack 的确切
字节与不可变初始 manifest 由 `release_provenance.json` 哈希链接；每次
prepare 必须清除或拒绝旧 ready/control/ack 槽。`SensorFrameWriter` 增加
会话内单调采集时间并升为传感器元数据 v2，所有结局、时延和汇总仅使用
acknowledged release 后样本。

RATE-002 资格试跑冻结为 **20 Hz follow、HOLD 内已处理至少 20 帧且
`seq ≥ 20`、release 后固定 30.0 s**；通过五项预注册判据后才允许 2 次标定和
12 次测量。侦察网格、全体干扰最小分离、R1′/R2′ 边界和 R3′ 固定三值右删失
均以该提案的精确定义为准。协议改变时间/控制语义，因此 C# 基础设施形成稳定
候选后必须先停在 Sonnet 独立复核和聚焦 Unity 验证门，未过门不得启动资格
试跑或正式重测。

**RATE-002 修订 A1（2026-07-25）**：会话顺序改为侦察 → 20 Hz 标定 →
20 Hz follow 资格试跑 → 三次正式 20 Hz follow → Decision A。Decision A
只使用这三个 admissible 正式 run，按冻结规则
`triggered := R1′ OR R2′ OR R3′`；资格试跑数据不进入该判定。用户已在任何
资格试跑/正式测量数据产生前预注册 `trigger_branch="stop"`：触发即自动跳过
剩余九次测量和尚未执行的 5 Hz 标定，批次标记
`TERMINATED_AT_DECISION_A` 与 `M2_NOT_CLOSABLE`，转入
`P1-DETECT-001`/新载体批次；未触发才继续三次 20 Hz nadir、5 Hz 标定及六次
5 Hz 测量。三次有效 run 在补跑上限内无法凑齐时进入
`BLOCKED_INVALID_CELL`，不产生性能布尔结论。规范工件
`runtime/rate-study/P1-M2-RATE-002-B1/decision_a.json` 绑定三个 run 的
manifest/release-provenance 哈希、逐规则结果、敏感性、真实会话顺序与时间；
采用 create-once 语义，并由同一 fail-closed 校验门同时约束第 4 次测量和
5 Hz 标定。固定先后顺序的系统负载/时间混杂必须披露，不得归因成纯帧率效应。

**已接受的继任率研究（`P1-M2-RATE-003` revision 3，2026-07-30，
acceptance round 3）**：RATE-001/002 的归档 v2 路径和历史语义保持只读；
RATE-003 活跃路径使用 `tethered-sensor-frame/v3` 及版本化的 rate3
session/ready/release/provenance/decision schema。RATE 会话的帧 capture、
tracker-ready、release ack 和 Python re-anchor 内部单调源统一绑定
`system-stopwatch/v1`；所有跨进程比较先校验 clock identity。启动期检查
分别早于模型/run 目录/ready/release 副作用，运行期坏帧早于该帧的
observation、control、re-anchor 与 evaluator 副作用并使 run 以
`INVALID_CLOCK` 终止。该时间语义变更是独立强制停点；归档 v2/v3 双向串喂
必须失败关闭，聚焦 Unity 只用不产研究数字的 `rs3-clock-smoke` 身份。

冻结测量范围为 follow 条件下 `D1 = 2.0 m/s` 与
`D2 candidate = 8.0 m/s`、5/20 Hz、三个预注册确定性弧长相位；同相位两率
相邻、12 槽顺序与补跑位置均在数据前固定。D2 的 5 Hz 一次探针先判协议/
数据 admissibility，再判帧间位移模型与 `C_track|geom >= 0.15`；若合格但
触底，只能一次下调至 6.0 m/s，完成新配置哈希、路线/包络审计和用户 0b
确认后直接进入正式矩阵，不新增第二探针。D2 只能称 synthetic kinematic
speed-stress condition；O1、nadir 全矩阵、路线圆角/动力学均不在本工作内。

探针和全部正式 run 的 `planned_duration_s` 精确冻结为 `150.0`，跨 rate、
difficulty 与 8→6 m/s 分支不得伸缩；采信同时要求 release-origin
simulation duration、共享主机 monotonic wall duration、evaluator cutoff
和 LOST 右删失满足提案 §10，evaluator/simulation 差值容差为 0.5 s。
实测环周期来自已释放运动段的有向起始截面，只作报告，不参与完成门或反改
时域。主分析为三个逐相位配对差及其中位数，`θ = 0.05` 只是预注册实际意义
阈值；三相位不是随机样本，不报 95% CI 或总体等效。D1 前提、相位异质性、
H2 背离与六值 `final_action` 按接受提案的总定义分别落独立字段。

每个探针/正式槽总 attempt ≤3；此外，全批次
`batch_invalid_attempt_count` 对 scouting/calibration/probe/formal 的每份
不可变 invalid/non-admissible receipt 累加且不清零，clock-smoke 与创建
研究 attempt identity/receipt 前的 preflight 拒绝不计。计数达到 4 后，
下一研究数据会话必须失败关闭，先由接受角色归因并取得用户重新授权。
`P1-DETECT-001` qual-3 Unity PASS 与接受归因、时钟停点的独立复核及
clock-smoke PASS 都是研究数据会话的前置门。RATE-003 不关闭 M2；
`DR-P1-M2-001` 仍按 §4.7 独立到期。

**RATE-003 Amendment DR-B（2026-07-31，acceptance round 4）**：
`p1-rate3-decision/v1` 对 12 个正式 run 恒记并哈希绑定权威
`metrics.final.json` 的无条件 `c_geom`/`c_track`，并按相位产出
`delta_geom_i`、无条件 `Delta_i^track`/`Delta^track`。冻结
`theta_geom = 0.05`；任一相位两率的 `|delta_geom_i| > 0.05` 即置该难度
`CGEOM_DIVERGENCE_FLAG`。旗标只触发 DR referral、限定语、条件化与
无条件差并报及伪天花板警示，永不改变六值 `final_action`。

D2/获 0b 后 6.0 配置的包络审计把 slant、off-nadir、min-side p05 与路线
合法性列为 must-pass：须通过并与已归档 D1 值相等；相同表示可用时要求
bit-equal，浮点重算唯一退化容差为 `1e-9`。速度导出的 loop period 与
distractor tick 仅记录 `{difficulty value, D1 baseline, delta}`，不进入
overall status。路线报告除 `scenario_id` 外的 schema/status、样本与障碍
计数、分类计数和 violation 数组均按接受提案 BC-DRB-3 比较。

采用六个 `rs3-d{1|2}-p{1|2|3}-calib` 独立 HOLD 标定槽位，全部产物先于
探针冻结；scouting 与每个 calibration 槽总 attempt ≤3。同一
`(difficulty, phase)` 的 5/20 Hz run 必须绑定同一冻结帧/框 SHA-256，
错配时该对两 run 均 non-admissible。成功路径预算为侦察 1 + 标定 6 +
探针 1 + 正式 12 = 20 次；用户 0c 逐字确认入授权账本前，任何研究数据
会话均失败关闭。探针 A0/B1–B3 不改，但归因须并读其 `c_geom`、
`c_track` 与 `C_track|geom`。

验收 0c 已于 2026-07-31 入账：用户原话“同意授权”，范围为上述 20 次
名义成功路径。该授权不豁免 BC-R3-2（累计第 4 次无效尝试即暂停）、
`DR-P1-M2-001` round 3、qual-3 PASS + 接受归因、条件性 0b 或其他运行门。

**Batch-2 实现澄清（2026-07-31，不改变 v0.3.10 测量语义）**：每个
(difficulty, rate) 使用独立冻结配置文件；同 difficulty 的两率共用
`scenario_id`，只允许 capture rate、retained count 与 evaluator pending
count 三字段随 rate 缩放，同 rate 的 D1/D2 只允许 `scenario_id` 与
`target.speed_mps` 不同。SCENE-004 的 D1/D2 路线合法性报告由同一
`RoadSceneAuditor` 生成；D1 在稳定候选中首次提交后冻结为只读基线，D2
逐字段与其比较。两报告 `CLEAR` 且最终 difficulty audit
`ENVELOPE_OK` 是 batch-2 停点前置证据，不是留给复核阶段补做的运行门。

**M2 收口降级（`P1-M2-SCOPE-001`，2026-07-31）**：M2 采用 D2 零新
会话路径。关闭证据由 TRACK-001/002、DETECT qual-3 的既有曲线，以及
RATE-001 `CLOSED_PROTOCOL_INVALID`、RATE-002
`TERMINATED_AT_DECISION_A` 的诚实负结果组成。5 Hz CSRT、20 Hz
NanoTrack 和 20 Hz NanoTrack + 三门载体因 tracker、场景、协议、控制条件
和感知栈不同而不可比较；qual-3 的探测器在环完成 75/75 轮，但零 REANCHOR，
不得简称为“纯云台-only”。关闭叙述必须逐字声明：“受控同追踪器跨帧率
对比未完成；现有曲线不可用于估计帧率效应，也不支持任何跨帧率定量或因果
结论。”RATE-003 机械与冻结参数完整保留为 M5 可选资产，0c 为 0/20 消耗
且不自动授权改变后的 M5 范围。`DR-P1-M2-001` round 4 的 B4/B5/B6
有界文档修订已于 2026-08-01 落地，round 5 随后以 `PASS_WITH_NOTES`
清除设计审查门；关闭叙述的 N1/N2/N3/N5/N6′/N6/N7/N8 与 N9 最终检查
也已通过。用户于 2026-08-01 以“好的，关闭M2”逐字授权，M2 据此按上述
限定关闭；授权账本边界不关闭任何下游义务或重新授权 RATE-003。

## 4. 机身规划层：词典序控制分配

### 4.1 问题形式（取代 v0.2 的未闭合加权式）

以下词典序 + 机会约束是保留的研究副线形式；`P1-ENG-FRAME-001` 接受后的
工程主线缺省改为距离保持带 + 比例速度 + 预测提前量，阈值策略留作有缆
对照和新策略内的兜底。画面居中仍由云台负责；该工程策略已实现并经最终 R3@K2 独立复核通过，AC-21/23 Unity 验证通过、本项 DONE；墙钟追认与保留局限见 `docs/implementation-status.md`「P1-ENG-FRAME-001 — 墙钟收尾落实与 DONE」。

"云台优先"不靠权重悬殊（可能退化为机身永不动），改为**词典序 + 机会约束**：

- **P1（保留研究形式，非工程缺省）**：若预测时域内可见概率满足 `Pr[目标可见 | belief B_k] ≥ p_min, ∀k ∈ horizon`（基于 belief 的期望可见性，不是点估计），则机身最小化运动（含悬停）；
- **P2（可见性即将违约时）**：求解滚动优化

```
min_{u_0..u_{H-1}}  Σ_k  λ_v·R_vis(p_k, B_k) + λ_q·R_quality(p_k, B_k) + λ_m·‖u_k‖ + λ_s·‖u_k − u_{k−1}‖
s.t.  p_{k+1} = f(p_k, u_k)                    # 机身动力学（先一阶速度模型）
      ‖v_k‖ ≤ 4 m/s, ‖a_k‖ ≤ a_max, 8 ≤ h_k ≤ 32
      ‖p_k − anchor‖ ≤ 35                      # 仅系留开启：球面工作空间
      简化缆线-障碍约束（缆线段与建筑不相交） # 仅系留开启
      p_k.xz ∈ geofence_xz_m                  # 配置出现时；无缆模式必填
      机身移动线段避开膨胀障碍棱柱             # 两模式
```

其中 `R_vis` 是目标 belief 与遮挡结构下的期望不可见代价，`R_quality` 惩罚距离过远/离轴过大（成像退化）。

### 4.2 命名与动机的修正

- 机身代价统一称 **body-motion / operational effort**，不称 energy——除非后续实际建模张力、功耗或卷扬机构；
- 系留开启模式下，系留的真实含义是**有限工作空间 + 缆线张力/拖曳/缠绕风险 + 机身移动扰动成像**，不必然更耗能；系留轨迹规划已有考虑缆线-障碍的工作（评审所引 [arXiv:2011.03491](https://arxiv.org/abs/2011.03491)），**加权优化本身不是创新点**——此段是保留研究副线的论述，不为当前工程规划器建立研究主张。

### 4.3 实现路径与保留模式

保留研究副线曾计划先实现词典序判据 + 简化求解（采样式/势场近似），完整 MPC 为目标形态；不作为当前工程执行合同。系留开启时保留两个研究模式：**预置机动**（P2 的自然输出）与**哨兵模式**（目标出可达视野域时，移动到最大化未来再入可见概率的等待位——Phase 2 交接的单机雏形）。

**M3′ 规划器接口停点（`P1-M3M4-SCOPE-001`）**：M3′ 先冻结可供 M4′
消费的版本化命令契约，再实现依赖策略。契约至少绑定 command/sequence ID、
坐标系与单位、HOLD/velocity/waypoint 模式、issue/valid-until、约束拒绝、
ACK、stale/重复/乱序与 fail-safe 语义；作为控制协议变更单独形成稳定候选
并经独立复核。M3′ 只提供等待位/航点能力；L4 状态与转移仍由 M4′ 实现。

已知落差：M0 已实现三轴 body 速度通道、限高与有缆模式球面系留裁剪。系留开启时缆绳自
v0.3.17 起显式假设为**张力控制绞盘维持绷紧**：放线长度等于锚点–机体
距离（上限 35 m），因此球形可达域与「缆绳占据锚点→机体直线段」都是该
假设下的精确结果而非近似（商用系留机普遍用张力绞盘防松弛缠绕；
`TetheredDronePlant` 现有实现即该模型，代码零改动）。plant 仍是运动学
模型，未建模项收窄为：张力对机体的反作用力、绞盘收放速率上限、缆绳
气动耦合（垂度在绷紧假设下不存在）；规划层也尚未实现本节的词典序
判据——见 R2。`P1-ENG-FRAME-001` 接受的无缆模式取消球面钳位，增加
围栏硬钳；`tether_saturated` 恒 false，机身线段避障及速度/加速度/高度
限制仍适用。该模式已实现、K2 独立复核与 AC-21/AC-23 Unity 验证通过，本项 DONE；范围外债及墙钟已追认的可能超额仍如实保留，见同名收尾证据。

## 5. 丢失升级阶梯

`P1-ENG-FASTFIX-001` D2 已接受捕获模式的窄自动重捕：仅连续时序降级升级后的载体重建、旧可靠绑定提示与双截止窗口，几何/运动/尺寸及竞争门仍 fail-closed；失败/歧义显式报告，人工请求优先。完整性失败与 BROKEN/DISPUTED 不自动恢复。A候选4已过独立R2并经接受消费、R1-1已闭，有限离线回放沿候选1；现行证据、主张限制与未闭义务见同名提案「R2通过消费」§2–3。旧/续做磁盘UNKNOWN保持；尚未通过Unity验证，不称误重捕率或板端能力。A首签不覆盖B/C；具体接口、计数与回滚仍以「D2 接受裁定」为准，不扩成研究 L2 搜索或 ReID。

工程首版最低恢复范围见 §1：报告丢失并允许重新指定。下表保留研究设计；
不据此宣称 ReID、复杂搜索或自动恢复已经实现，也不授权继续整包实现。

| 级别 | 状态 | 行为 | 转移 |
|---|---|---|---|
| L0 | 正常追踪 | 双通道感知 + LOS 伺服 | 仲裁规则 4 持续 ~1 s → L1 |
| L1 | 惯性滑行 | 云台跟随纯预测；协方差膨胀 | 协方差超阈或 T1(~3 s) → L2 |
| L2a | 几何搜索 | 预测轨迹扫描 → 扇形/螺旋扩展；每视角 YOLOE 提议 + 3.2 节三重打分 | 重捕获 → L0；超时 → L2b |
| L2b | 路网 belief 搜索 | 目标 belief 在路网图上 HMM/粒子传播，按后验概率排序搜索视角 | 重捕获 → L0；超时 T2 → L3 |
| L3 | 语义决策（VLM） | 见下 | 假设 → 交 L2b 执行验证；超重试上限/冷却中/不可用 → L4 |
| L4 | 哨兵回退 | 4.3 节等待位 | 目标重现 → L0 |

**里程碑归属（v0.3.18）**：L1 属 M3′“保持可见”；L2a/L2b/L4 属
M4′“丢失恢复”。原 L3 系统 VLM 消融不再占用 M6，维持暂停的可选系统
副线；恢复须用户另行裁定。M4′ 消费 M3′ 已复核的规划器接口，不能反向
绕过该停点。

**v0.3 的关键调整**：

1. **L2b 是 VLM 的公平对照**——VLM 与 L2b 拿到同一份 `WorldModelHandle`（路网 + 遮挡结构）。若 VLM 收益只来自"它看了地图而基线没看"，归因即不成立；
2. **重捕获歧义优先走 MHT + ReID**（多假设并行维护 + view bank 打分），VLM 只裁决 ReID margin 无法区分的语义歧义；
3. L3 增加**最大重试次数、冷却时间、失败终止条件**，防循环调用；
4. VLM 输入为 `RecoveryContext`（受控关键帧 + 状态摘要 + 路网局部图），输出仍只是假设 JSON（区域/概率/建议观测位），不含控制指令。

## 6. 指标体系（v0.3 重写）

**已核实的天花板问题**：当前路线最远点距锚点水平 72.1 m、与 25 m 高度的无人机高差 24.6 m → 离轴角 71.2°；云台 45° + 垂直半视场 30°（水平半视场 37.6°）合计可达 75°+，故 **B0（机身不动）即可让目标中心几乎全程在画面内**；而现有 [CoverageEvaluator.cs](../Assets/TetheredTracking/Scripts/CoverageEvaluator.cs) 只判断真值中心点是否落在视口矩形内，无遮挡、无面积、无身份概念——旧主指标已被几何做满，必须重构。

**四指标拆分**：

| 指标 | 定义 | 用途 |
|---|---|---|
| `C_geom` | 目标真值在视锥内**且未被遮挡**（射线检测）的时间比例 | 几何上界诊断；B0 在无遮挡场景应≈100%，作为 sanity check 而非成绩 |
| `C_track` | 预测框与真值框 IoU ≥ 阈值 **且身份正确** 的时间比例 | **主指标：正确身份跟踪覆盖率** |
| `C_track\|geom` | 物理可见条件下的跟踪成功率 | 分离"看不见"与"没跟上" |
| `C_quality` | 目标像素面积、完整可见比例、中心误差 | 成像质量；解释远距/大离轴的退化 |

**边界纪律**：Unity 真值只进 evaluator，永不进入控制器/感知器。

**框协议**：预测框使用图像内可见部分的归一化 top-left `xywh`；发布前必须
裁剪到 `[0,1] × [0,1]`，即 `x ≥ 0`、`y ≥ 0`、`x + width ≤ 1`、
`y + height ≤ 1`。接收器拒绝越界框，不在 evaluator 内静默改写预测。这样
预测框与 `ProjectBounds` 生成的裁剪真值框采用同一边界定义。

**诊断指标**：丢失次数、**删失处理的 MTTR**（未重捕获样本按删失统计，避免幸存者偏差）、ID switch 次数、错误重捕获率、漂移重播种/tentative 拒绝次数、机身运动量、VLM 调用次数与延迟。

**场景反天花板（保留研究轨道要求）**：系留开启的正式实验须变化锚点位置、系留长度、相机 FOV、目标速度，并加入遮挡与干扰车辆——保证 `C_geom` 显著低于 100%，指标才有区分度。当前工程任务不据此增设资格门或场景改动。

**已接受的场景合法性门（`P1-SCENE-001`，2026-07-27）**：第三方 city
场景文件保持原样；可选 `scene_adjustments` 以“规范化预制件根名 + 原始
XZ”唯一定位并确定性迁移与目标路线相交的停放车辆，配置字节继续由现有
SHA-256 冻结链约束。修正后、评估遮挡代理构建前必须对所有场景车辆执行
route-corridor 净空审计，零/多匹配或任一剩余违规均终止场景构建。被选为
RATE-002 干扰的车辆显式挂 `RateStudyDistractor`；scouting 必须使实测活动
干扰数量精确等于场景级期望值，禁止空真通过。动态 renderer 相交计数仅由
显式验证配置启用，只写场景审计工件，不进入传感器、tracker、控制或
`CoverageEvaluator`。含缺陷场景的 B1 战役原样归档为
`SUPERSEDED_SCENE_DEFECT` 且 run ID 永不复用；修正后战役使用
`P1-M2-RATE-002-B2` 重新冻结 scouting 与标定。

**已接受的道路合法路线门（`P1-SCENE-002`，2026-07-27，Round 2）**：
目标路线冻结为顺时针、靠右行驶的道路内环，精确车道偏移、路面高度与
转角只由 Unity 内沥青边界实测生成。三份 scenario 以精确文件字节
SHA-256 绑定同一版本化道路数据；缺失、哈希/schema/分类/足迹异常均
fail-closed。合法性门同时要求路线采样落在沥青带内，并用锚定路面的
三维车辆扫掠包络审计车辆、杆柱、树木、建筑和街道家具；有足够净高的
架空结构不因 XZ 投影重合而误判，实例 TRS 不支持时不得静默近似。
评估域 actor 的一次性放置必须在首帧前完成，正式保证来自放置 API 阶段
守卫；逐帧跳变/相交监视仅为显式验证诊断，只写独立工件，不进入
`CoverageEvaluator`。SCENE-001 的 Unity FAIL 永久保留，剩余项合并进
`UT-P1-SCENE-002-001`；新稳定候选须先经 Sonnet，通过合并 Unity 门前
不得创建 B2。未来 M5 只可生成种子冻结、同审计通过且不暴露给感知端的
路线；本项不实现随机路线生成器。

## 7. 评测协议（v0.3 重构）

**三条正交消融轴**（取代 B0→B3 阶梯——旧阶梯一次改多个变量，无法归因）。所有控制器比较固定同一感知器；所有感知器比较固定同一控制器：

| 研究问题 | 对照序列 |
|---|---|
| 感知是否有效 | SOT-only → minimal triple-gated re-anchor（`P1-DETECT-001`）→ 完整 ReID/view-bank/模板门控（3.3 全量）；不得把三门载体收益单独归因给 YOLOE |
| 机身分配是否有效 | 云台-only → 限位阈值触发式机动 → 词典序预测规划（4.1） |
| 重捕获是否有效（暂停的系统副线） | 无搜索 → L2a 几何搜索 → L2b 路网 belief → L2b+L3 VLM |

**上界与关键对照**：

- Oracle target state / oracle visibility（真值直通控制器的上界，量化感知损失）；
- **忽略系留约束的规划器**（撞约束时截断）——保留系留研究副线的对照；当前无缆工程任务不据此主张 tether-aware 价值或增加消融；
- SAM 2 / SAMURAI 离线轨迹作感知上界参照。

**统计纪律**：成对随机种子（同一种子跑所有方法）、报告均值与 95% CI、按场景难度分层；敏感性分析覆盖缆长、锚点、FOV、车速。

**验收表述**：不使用"B1 覆盖率必须大于 B0"这类单调判据——若方法以少量覆盖损失换取大幅机身运动减少同样是有效结果。主报告形式为**覆盖率–机身运动 Pareto 曲线**上的支配关系。

## 8. Orin Nano 8GB：从"预算表"降级为"待验证假设 + 实测协议"

**执行边界（v0.3.1）**：本节是 M7/Phase 2 的未来部署协议，不是当前电脑仿真
的安装清单或验收条件。M0-M6 不安装 TensorRT/CUDA/Jetson 依赖；只有用户明确
启动 M7 后才执行本节。COORD-010 已批准小规模 Jetson 可行性探测前移，
但须新工作项独立说明设备与额度并获授权；不激活 P1-M7-DEPLOY-001，
本批硬件/下载额度为零，桌面量化不能替代板端实测。

**独立前移项（2026-09-28）**：`P1-ENG-JET-001` D2 已接受为
`engineering-v1` 工程探测，范围限于 A3 §6 第 0–5 步与桌面机 ↔ Jetson
中继测试，合并停点 `K1K3K4`；Unity 留桌面机，板子 headless，只产出板端
描述性读数与建议，不产生部署研究主张或 M7 关闭结论。任务合同见同名提案
§1–§7。其 §5 执行信封仍须用户逐字另签；未签前下载、量化、传输与板上
运行额度均为 0，§7 (h)–(n) 的未答复选项按「不做」缺省处理。

2026-10-04阶段B答复已由接受落实（同名提案「阶段B答复落实」）：允许保留
S1/S2 STOP及恢复标记申请阶段B，S5判定档采用运行时5 Hz、首次init冷启动
丢帧单列；量化路线I-A、跳过3a、另起稳定停点，执行等待消耗轨道释放。
通过线出处/STOP处置与依赖准备/逐维度申请以该合同为准；阶段B额度仍全0，
本次无新硬件证据、无M7关闭或部署研究主张。

同日「阶段B准备审核」与「阶段B补写核清」追加固定tag、W轮子/本地检查点直建、
合并与资产、云控制路径解释；BP-1…5静态材料已核清，预检更正版见后节§3，
该轮交用户的选择随后已落实，现行合同及事实/额度唯一入口见下段。
原通过线分类与STOP保留，不以桌面或公开源码文本代替板端实测。

同日「阶段B预检答复落实」落实账本用户§5答复：选择类按推荐（含视觉编码
缓存例外、128张本域校准规则、S4-a复用、B1/B2具名失败例外及14码处置）；
一次Mac mini→Jetson有线board只读预检≤300s、无重试已授权，判为零消耗，
可与FRAME交接并存但遵守单写者/槽位互斥。本次终点为云前独立子范围，
B-CLOUD/CLOUDDEP未答，云及C2量化产物路径不执行；其他执行维度仍0，
预检现已执行1/1，原文件哈希与读数核清见同名提案§8.2；cmake缺项现按用户反馈3.28.3/ii核清，
一次板相关来源元数据查询合同见「阶段B元数据授权落实」§2–4；META-BATCH-1累计61/86、31/40项目已由接受核清，
当轮31拟pin为条件计划、文件闭集未核；剩余25次/9项目作废，原账/原件不回改，详见「阶段B元数据核清」§1–3/AC-10修订20；后续文件声明核验见下。
同日用户已签META-VERIFY及SRC-ARCHIVE，合同/AC-10修订21–22见「阶段B核验授权落实」§1–4：
仅Mac mini取31个METADATA侧文件与1次固定commit源码归档用于核验，两项现已执行并由接受核清；
「阶段B核验核清」/AC-10修订23裁定31件固定wheel的METADATA静态声明闭集已核（含5件Dynamic），
不认证安装/运行兼容；归档字节/sha及固定commit响应链已核、源码不再计新增下载。
同日「阶段BGGUF事实落实」接受用户GGUF精确字节作为条件预算出处，文件输入推荐已重算；
完整双向传输/峰值/墙钟等仍UNKNOWN，后续执行维度0、不含云；
用户事实与逐维度待签唯一入口为「阶段B预检答复落实」§5，未核0。原S1/S2 STOP、补丁未上板、
两条OPEN债保持，不签DONE；完整边界与通过线/STOP依该合同§1–5。

同日「阶段B下载授权落实」将用户B-SIGN-DOWNLOAD写为AC-10修订24/AC-11修订3：
仅Mac mini下载31固定轮子+2固定GGUF，各1次、重试0、累计≤2,443,785,130 B，
整批≤1 h、本次新增占用含暂存/.part/失败保留件≤10 GB，执行前后核查；
源码新增0、其他未签维度0、不含云。合同仅允许GGUF一次跳转至用户本机已放行
候选主机；当轮的CDN放行/离线前提后已落实，唯一用户入口仍为上述§5。
下载不授解压/安装/传板/模型执行、不替代板端实测，不签B1完成或DONE。
同日「阶段B下载核清」核实轮子31件完整实体字节/sha符合、请求与计时/占用在限内；
GGUF两件302至us.aws.cdn.hf.co，按合同停对象未取回、各1/1尝试已用尽；
接受侧候选主机遗漏归因只在该节。新主机放行/新尝试仍由用户在上述§5决定，
接受当前不追加主机或签额；其余未签维度0、不含云，原STOP/未上板/OPEN债保持。

同日「阶段B用户GGUF核清」核实用户自下2件字节/sha与账本期望及用户读数双符合，
不计代理下载额度，新尝试0；原下载停止归因/计次保持。无需再问新主机/代理另取，
31轮子及2 GGUF已核清，保留源码只复用；上述§5更新为用户逐维度签传板/安装/构建等，
未核前提/未签维度0、不含云，不产生板端兼容/性能结论，STOP/未上板/OPEN债及门值保持。

同日「阶段B传板授权落实」追加AC-10修订25/AC-11修订4，将用户TX-ASSETS签发写成
34件各1次、重试0、≤1 h/板新增≤5 GB的迁移合同，尚未传板；本机窄目标放行及
一次两端余量前置见该节§2–5，逐维度入口仍为「阶段B预检答复落实」§5。
仅资源落盘、不解压/安装/构建/加载/测试，其他未签维度0、不含云；原负结果、
补丁未上板、OPEN债和主张上限不变，不消费verdict或签DONE。

同日「阶段B传板授权落实」§5追加AC-10修订26与B-LOCAL-EXCLUDE-TRANSFER具名申请：
原加板IP推荐已依账本撤回；会话沙箱启用，仅用户另签条目对应的目录脚本调用在沙箱外运行，
用户本人改设置/反馈及Implementation离线核前提齐全前不试连。申请尚未签，TX-ASSETS数值不变。

2026-10-06用户另签C2本地诊断追加：Mac mini下载训练同revision官方base、合并C2→GGUF→Q4_K_M，
板复用现有mmproj/server与固定prompt v2、609行确认集，只对C2 bf16配对；合同、六维额度及工具缺项
以JET-001提案「阶段BC2本机量化诊断授权落实」为准。未核新工具/安装不执行，3c与云仍停；
base提示调试资源核清见同名提案，不转为证据/正式AC或门满足。前文C2不执行是当轮快照，
只对本次具名Mac诊断被替代，不授权正式S3/S4/S5、共驻或M7关闭。

v0.2 预算表只算了权重，未计激活/TensorRT workspace、CUDA context、图像缓存、VLM 视觉编码器、KV cache、系统与仿真桥内存、多模型共驻峰值、热降频（[官方规格](https://www.nvidia.com/en-gb/autonomous-machines/embedded-systems/jetson-orin/)只承诺 8GB LPDDR5 与 67 TOPS，不构成共存证明；[Qwen2.5-VL-3B BF16 checkpoint 本身 7.5GB](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct/tree/main)，4-bit 权重 ~2GB ≠ 运行内存）。

**修正后的立场**：

1. 权重级估算仅说明"不明显不可行"，可行性由 **R4 实测协议**裁定：单模型与共驻峰值内存、p50/p95 延迟、15W/25W 功耗模式、连续运行热稳态、不同图像 token 数、VLM 推理期间 SOT/控制回路是否被阻塞；
2. **交接策略的蒸馏目标优先是小型策略网络**（结构化状态 → 动作），3B VLM 不是预设——只有当输入必须含图像语义时才保留小 VLM；
3. 硬件实测从 M7 开始；是否提前冒烟由用户另行显式启动，不默认插入当前
   M0-M6 仿真路线。

## 9. Phase 2 预留

- 五接口消息（第 2 节）为跨机移交的 schema；`IdentityProfile` 为身份包；
- 覆盖率评测器按 n 机实现（"任意一机 C_track 成立"）；
- 锚点/路线/FOV 场景参数化（R2 待改）；预留第二锚点位，可达域重叠区为交接区；
- **已知开放问题清单（不声称已解决）**：时钟同步、消息乱序/丢包/过期、交接 ACK 与所有权冲突、跨机协方差相关性（重复计数）、跨机外观域差。

## 10. 风险清单

| # | 风险 | 等级 | 处置 |
|---|---|---|---|
| R0 | YOLOE 标准导出烘死提示，动态换目标与固定产物冲突 | 当前仿真已处置；未来部署待定 | M0 已选 PyTorch YOLOE 做电脑仿真；TensorRT 三条出路延后到 M7 |
| R1 | 主指标几何天花板（已核实） | P0 | M0 已实现 evaluator 四件套；M2 强曲线位于 `C_geom=1` 的 benign 载体，反天花板义务在 M2 未完成。责任转给仍暂停且未裁定的 `P1-SCENE-005` 及后续 M3′/M4′，当前不算已有缓解 |
| R2 | 系留开启模式的 Unity 脚手架落差：绷紧假设（张力控制绞盘，v0.3.17）下的运动学模型；不含张力反作用力、绞盘收放速率上限与缆绳气动耦合（垂度在绷紧假设下不存在）。无缆模式另受 `P1-ENG-FRAME-001` 围栏与通用安全边界约束，K2 与 AC-21/23 Unity 验证已过、本项 DONE；范围外债与墙钟缺证追认保留 | P1 | body y 通道、锚点/路线参数化、frame_id 原子帧包已于 M0 实现；球形工作空间只在绷紧系留假设下成立，论文按模式如实表述，进度证据见 `docs/implementation-status.md` |
| R3 | 帧率/多率变更改变闭环性能 | P1 | 受控同追踪器跨帧率对比未执行，风险未缓解；转 M5 可选敏感性轴，须重新取得用户范围授权 |
| R4 | Orin 内存/延迟/热不确定 | P1（部署期） | 第 8 节实测协议；M7 启动前不阻塞电脑仿真 |
| R5 | 教师语言监督对 matched template-SFT 无增量 | P1 | 按 T-G1 报预注册负结果「模板监督足矣」；不得改称教师必要或挑选风格/seed |

## 11. 里程碑（v0.3.36 当前）

| # | 内容 | 验收 |
|---|---|---|
| **M0（已关闭）** | 本地 PyTorch/ONNX 动态提示边界；evaluator 四指标（含遮挡射线）；帧导出原子性 | PyTorch 仿真路径确定；标准 ONNX 动态重提示结论完成独立复核；新 evaluator 与 Unity 用例通过 |
| M1 | 场景视觉验证 + 场景参数化（锚点/路线/FOV/车速可配，含遮挡布置） | 参数化配置跑通；`C_geom` 在设计场景中显著 < 100% |
| **M2（已关闭：D2 负结果）** | 反射层闭环：保留 5 Hz CSRT+LOS、NanoTrack 资格曲线与三门载体 qual-3；RATE-001/002 负结果如实报告；同追踪器受控 5/20 Hz 对比降为 M5 可选敏感性轴 | 云台-only 在新指标下的既有基线曲线；不可比性与 N1/N2/N3/N5 逐条披露；`DR-P1-M2-001` round 5 `PASS_WITH_NOTES`；用户 2026-08-01 逐字授权关闭 |
| M3′（保持可见） | 世界系估计（协方差传播）+ L1 predicted-only 滑行 + 云台-only/限位裕度阈值式/词典序机身分配；先过困难场景适配性门和规划器接口停点 | 预登记场景适配性核查通过后，报告三策略覆盖率–机身运动 Pareto 与估计器一致性证据 |
| M4′（丢失恢复） | 消费 M3′ 规划器接口的 L2a/L2b/L4 + 3.3 全量仲裁/ReID/view-bank + 遮挡实验；原 L3 系统 VLM 副线暂停 | 删失 MTTR、ID switch、错误重捕获率报告 |
| M5 | 场景随机化 + 三轴消融 + oracle/tether-unaware 对照 + 敏感性分析 | **最小可运行系统** + 完整实验报告 |
| M6 | 原 DIST-001 四臂/T-G1 确认性研究延期；DATA-001 G0/D0 包部分交付收束，DATA-002 旧采集不足且保留来源缺口终止（COORD-010 §3 用户批准） | 未完成、未关闭，不签 G0/Unity/M6 通过；历史设计、复核与不足证据保留，当前处置及使用限制见 implementation-status 工程继承清单。未来恢复研究须重审数据、协议、预算；工程发布使用独立工作项。 |
| M7 | 用户显式启动后：Orin Nano 移植、TensorRT 动态提示路径选择、R4 实测协议全量 | 实测版资源/延迟报告；不反向阻塞 M0-M6 |

**投稿边界**：若恢复后训练研究，主张的闭环仍以 `P1-VLM-DIST-001` 的 T-G1、完整
负结果披露和后续新鲜上下文设计审查为准。若另写原系留系统论文，仍须
补齐正式优化问题、非天花板指标、L2b/oracle/tether-unaware 强对照、
系留约束消融及相称的 Orin/HIL 或实机证据；v0.3.19 不视这些旧义务已完成。
