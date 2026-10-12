# P1-ENG-CAPTURE-001 — 第四Play/正式重做实现证据

Owner: Air Implementation。只采集、归档与既有零模型点击配对；不改运行时代码，不签复核/验收/DONE。授权、UT-FORMAL2预登记与终场用户代录由Acceptance负责。新信封按同名提案「正式测评提前终止与新一次重做落实」；旧失败、超时和UNKNOWN保持。

## 0. 原件与运行

输出根 `outputs/eng-capture/formal-redo/`，本轮session ID由 `control/launch.json` 运行时解析，下文 `${SID}` 均指该值，不硬写可派生目录名。准备与最终发令HEAD/porcelain现场机器记录见play-ops§12与launch.json；发令porcelain空，最新passed_candidate祖先及PLAY_GOVERNING零diff已核。控制参数/实际命令/模型清单见companion-source.py、control/processes.json、sessions/${SID}/language-session.jsonl。

f0=0，计划T=290s；授权记录1431条，帧21…1520。加载1、session1、resident run3（仅复用已加载模型）；中间两次关闭原因publish_expired、catchup_stale，第三run后最终operator_stop。串行stop回执APPLIED，控制/页面exit0，原件process-end.json；不重开控制会话。ILLEGAL_WRITER_SUSPECTED原日志保留，运行沿已接受显式allow-shared-runtime参数，不删该记录或代称无疑点。

**执行偏差**：首次operator_stop退休事件距launch 304.060s，较290s目标迟14.060s；监控将磁盘全量采样和停止检查置同一循环，采样执行期间无法及时检查，不能把“每10s计划采样”冒称实时护栏。stop.json被循环后续检查重写，最终timestamp不是首次停令；首次有效stop以language-session operator_stop事件/stop-request回执为准。未追认采集上限符合。

## 1. 源完整性与独立点击读数

用户终场针对退出、四身份、更远、一圈和目检捆绑问题答：**“是的，但是在第一个拐角跟丢了”**。针对停止后新0/1/2是否重启Play或采集，答：**“误触的不用理会”**。原话须转Acceptance入Unity日志，不把捆绑确认扩为逐项PASS或把“不用理会”解释为额度返还/源完整。

非真值sensor旁车核查见control/archive-frame-identity.json：当前源新0/1/2 capture时间在operator_stop之后，旧142…1641仍留，共1503帧；正式早期0…141原件不再作为原时间帧保留。真值文件仅stat为3147B，未语义读取、未断言其内容。用户误触及混合时序使源归属不可直接核为单次正式采集；不筛帧、不拼接旧真值、不推最佳片段。

停止后escalated只读检查8774、控制/点击/track进程与truth/latest打开writer均无；源大小/mtime间隔2s一致，用户退出确认及误触说明保留。全部当前源三个对象同卷无覆盖rename；归档3009文件/71,686,913逻辑B，移前后SHA/大小/数量全等（archive.json）。**该核验只证明移动未改当前混合源，不能证明正式源完整。** 哈希、元数据、重启0…2全部保留。

Acceptance本会话只读入口裁定：两次标准main评分NOT_RUN(SOURCE_PROVENANCE_UNRESOLVED)，只允许既有click_latency一次完整原点击流+同会话journal，无真值/main/score_*/replay。完整输出 `${SID}/terminated-click-readings.json`。原日志4个click_received，无click_refused/malformed；工具分母4/总PASS、受理子段全部≤1；合同分母4，无剔除，绑定4/4、e2e逐行≤1，**AC-22独立读数PASS**（未签独立复核）。

| 原序号 | click_id | bound | e2e帧 | 受理子段帧 | wall_s（描述） | 工具读数 |
|---|---|---|---|---|---|---|
| 1 | `4bb53ae5831b452d8ddf540efa907c2b` | True | 0 | 0 | 0.021725 | PASS |
| 2 | `2cb39896cb244125bebc8c39b4032d4e` | True | 0 | 0 | 0.082669 | PASS |
| 3 | `0f8bd42f99ae47c6b934f2b2a8aee3bb` | True | -1 | 0 | 0.080241 | PASS |
| 4 | `3a30f118f132453ba68cbe365788b02f` | True | 0 | 0 | 0.064759 | PASS |

第3行e2e=-1为原工具帧差，原样保留、不钳0、不以子段或墙钟替代；这不是负的物理时延主张。只有点击配对读数获取，无完整跟随评分。

## 2. AC-23…26与稳定停点自证

| 条目 | 当前结果/证据 |
|---|---|
| AC-23 | 标准首红车段/换回段均NOT_RUN(SOURCE_PROVENANCE_UNRESOLVED)；用户报告第一个拐角跟丢，≥1圈跟随与两段修复/准时报告未证，不能PASS。 |
| AC-24 | NOT_RUN(SOURCE_PROVENANCE_UNRESOLVED)，未读真值/窗口IoU，不能用未评分替代NOT_EVALUABLE。 |
| AC-25 | NOT_RUN(SOURCE_PROVENANCE_UNRESOLVED)，d0/N/保持/原越界值未读，不称10–14m保持通过。监控unsafe样本空不替代全合同评分。 |
| AC-26 | 终场捆绑“是的”及拐角跟丢反馈待接受角色代录核定，不签点击/转向/报告逐项PASS。 |

四项稳定候选自证：①范围与证据齐备 **NOT_MET**（AC23…26缺完整正式证据）；②要求验证已过 **NOT_MET**（本轮非完整评分/用户拐角丢失）；③已知失败已处置 **NOT_MET**（publish_expired/catchup_stale、上限晚停及源混存未解决，本信封无代码修复额度）；④风险/状态/准确交接已写 **MET，仅本证据与状态指针**。不提交成功PlayK2K4候选、不启动依赖实现；交Acceptance核清资源/用户反馈/停止归因。阶段A代码通过和既有OPEN债保持，旧正式失败不被本局部PASS覆盖。

## 3. 新窗口资源与限制

新基线control/prelaunch.json连续计时；control/evidence-meter-checkpoint.json（首计量工具返回摘录）阶段检查点：586.677s/305,942,528B。归档/配对/准备均计本窗口；后续证据提交与Acceptance核清仍继续计时，最终执行封口指向control/execution-close.json，不拿阶段检查点冒充最终耗用。原签900s/1GB，预留250/50/500MB；已观察1模型/1session/3run，正式Play1。停止后误触造成额外采集启动，实际追加Play或组件启动类别/次数未逐字核定，**UNKNOWN/偏差保留，完整Play额度符合不成立**。无额外模型/session/run；其他设备、API、下载、安装0。

两次main=0、click_latency=1、replay=0。磁盘为采样的逐路径allocated增量保守峰值，移动路径可重复计，采样之间短暂辅助写入峰值无法证明；旧UNKNOWN不抹，当前完整辅助峰值限制保留。晚停与误触不是获准工程重试，不返还已耗额度，不自动再次Play。
