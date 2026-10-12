# P1-ENG-CAPTURE-001 — 第三次 Play 正式测评提前终止原件

Owner: Implementation；2026-10-10；范围PlayK2K4。新授权900 s/新增1 GB，旧结果与超时/UNKNOWN保持。仅操作/原件及零模型点击读数，不修改运行时代码，不签独立通过或DONE。

## 0. 启动、停止与原件

授权、采集前UT-FORMAL1见账本/Unity日志；现场最终HEAD/空porcelain、动态session身份与f0=0/T_sess=270 s见 `outputs/eng-capture/formal/control/launch.json`。通过候选沿同名复核最新passed_candidate动态解析，PLAY_GOVERNING无diff，仅白名单文档。新基线prelaunch.json；新scene ID0。

会话因publish_expired、catchup_stale两次内部重建后，再次catchup_stale触发rebuild_limit，S-B-TERM停止余剧本。模型缓存累计加载1/请求1→2→3，session1/run3，已用尽本轮名额；会话/page exit0，无人工重启。自动TERMINAL发生在controller已处理717帧（2–723）之后；用户随后明确“已退出 Unity Play”。Unity共1332帧（0–1331），后续未控制的采集帧不能延长有效跟随段。

原件 `outputs/eng-capture/formal/`；动态session子目录从launch读取。unity-runtime归档2667文件/71,011,567 B，同卷无覆盖rename，移前后逐件哈希全等；archive.json及session目录SHA256SUMS.json。旧play数据未混入。

## 1. AC-22 全点击读数

S-B-TERM零模型分析使用既有click_latency一次；未调用analyze_play.main，不读取评分真值、不构造S2假参数。接受侧窄读法为允许原点击流分析、不放宽正式AC；提案后续落实该说明。原输出terminated-click-readings.json。

工具分母5/verdict FAIL/acceptance_subsegment_all_le_1=false。原流5条click_received，未发送malformed_click拒收0，合同分母仍5；4绑定PASS/1未绑定FAIL，因此AC-22 FAIL。第4条工具e2e=-1及受理子段3原样保留、不夹成0、不以子段代e2e；墙钟仅描述。

| 原序号 | click_id | bound | e2e帧 | 受理子段帧 | 墙钟秒 | 工具判定 |
|---|---|---|---|---|---|---|
| 1 | bac20ca4fd414ac497bf66efd34f4267 | True | 0 | 0 | 0.13280391693115234 | PASS |
| 2 | f1d6be75ac994395a068f062c6fb03b9 | True | 0 | 0 | 0.06470513343811035 | PASS |
| 3 | bc1523be7e264834b5eb44051e59c979 | False | None | None | None | FAIL |
| 4 | 5cc49ce80634484aafc4b06e01d88e42 | True | -1 | 3 | 0.6656661033630371 | PASS |
| 5 | 79dc6b18b1944993a56ca19a3447a009 | True | 0 | 0 | 0.22511601448059082 | PASS |

## 2. AC-23、24、25 与剧本缺项

S1原click1用户“静止车已点”且绑定。S2用户“红车已点，且判断比静止车更远”，随后“红车多点了两次，下次就直接我跑完全程，点静止车，点红车追一圈，点静止车，切回红车到结束。你就不用提醒了”。S1后原流实际4点击（2–5）与报告额外2次红车点击不一致，逐条身份/真实S2首次序号仍UNKNOWN；不猜身份、不选最佳段，不再追问该已答内容。

operator-phases原先误填S2 index2，已追加correction保留原记录，不能以该误填作评分凭据。S3红车完整一圈、S4静止→换回红车未完成；第二换回段NOT_RUN(NO_RETURN_SEGMENT)。完整main两段评分与replay均0调用。AC-23/25正式证据缺失、不通过；AC-24评分NOT_RUN，原预测/收据完整保留。

## 3. 用户反馈与资源

上述原话及明确退出事实转接受角色代录Unity日志；本角色不写该日志。下次由用户自行完整四点击/一圈、不逐步提醒是操作偏好；后来另说“授权重新进行一次正式测试”及新资源答复须另条入账，不从偏好推Play。

本轮归档结束unix 1791666450.49894；close-meter墙钟468.608 s、已知保守新增200,679,424 B。采样报告的分配块增长包含移动路径重复计量；历史UNKNOWN保持，不宣称完整旧B合规。本提交/最终计量仍计900 s/1 GB，本次后续最终读数见control/execution-close.json；不能将中间close-meter当全部最终值。

## 4. 四项稳定停点自证与处置范围

1. 接口/范围冻结：原合同AC-21…26与STOP不变；本批只操作/证据。
2. 原候选测试沿已通过K1K2K3K4证据，不重跑用尽全套/模型；本次AC-22 FAIL、正式剧本不齐，不能自证实现者验收通过。
3. 真实TERMINAL/重建上限失败保留，未修运行时代码、未聚焦复测，不把用户重做授权追认为旧结果通过。
4. 未验证风险/状态/原件齐备，条件2/3未齐，不申请独立通过、不启动依赖本结果的实现。交Acceptance记录本次负结果与用户新一轮授权，任何下一次执行先按新信封/现场门核清。候选diff由最新passed_candidate至本批HEAD动态解析，仅本证据/操作单/状态文档；旧债与负结果保持。
