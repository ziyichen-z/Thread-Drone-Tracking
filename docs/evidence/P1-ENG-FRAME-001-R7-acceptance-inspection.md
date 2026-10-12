# P1-ENG-FRAME-001 R7实现结果接受核验（2026-10-01）

Status: **AWAITING_TEST_AND_REVIEW_AUTHORIZATION**。本轮为既有AC-21返工结果核验与补测前置处置；不是正式C轮、独立复核或Unity PASS。实现候选从 `git log -1 --format=%H -- tools/frame_follow_replay.py` 解析；本轮HEAD/status与完整文件清单见同名 `-inspection.json`。接受未跑测试、回放、模型或Play。

先看本批文件清单，逐文件读取全部9路径：工具3行增量、测试50行增量、真实fixture全文、状态板10行差异、实现证据71行、复算记录221行、三份原始日志。源码与证据对应关系沿原AC-21/AC-24/AC-25读取；真实评估器直接关联代码为 `CoverageEvaluator.cs` 的MetricsDocument.aggregate / AggregateMetrics.c_track / BuildMetricsDocument，现行 c_track=trackingDuration/safeTotal，given_geom分母不同，不混用。相关旧R2凭据与workflow §4.3.1/§4.3.3/§4.4/§4.5、engineering §4/§6均按原文处理。

| 原义务/核验对象 | 本轮结论 | 直接依据 |
|---|---|---|
| AC-21 R7字段输出 | 窄修证据满足；整体未闭 | analyze_run只在顶层/summary均无键时读aggregate.c_track；原优先级、null/0、显式metrics与舍入保留。真实schema红1败→绿5/5日志；复算输入metrics.json，R7=0.918990 |
| AC-21来源/端点 | 满足于本次离线核验 | 原metrics字节与fixture相同；接受直接核138原文件sha无差异，新输出sha匹配；新旧analysis仅R7键不同；metrics.final单独具名0.994950，不替换退出端点 |
| AC-24新候选全套 | 证据缺失 | 未执行；旧2061项结果不能替代新代码。具名Nano/CSRT资源需求见R7实现证据「AC-24全套待执行的资源边界」 |
| AC-25范围/接口 | 满足于本次窄修 | 本批仅tools/frame_follow_replay.py、其测试/fixture与evidence/status；controller/Assets/config等未改，无参数/指标定义/合同扩张 |
| 用户机身跟随/起停与按钮墙钟 | 证据缺失 | 补测未启动；旧用户只确认Console无错误且看不到无人机，完整旧按钮墙钟未知 |
| 新候选独立凭据 | 证据缺失 | tools/tests/fixture是PLAY_GOVERNING，新旧代码不同；旧R2不覆盖本次；禁止Play放行 |

预复核关注项：①核真实fixture来源与aggregate而非given_geom，②核显式null与零值优先级未改变、未擅选metrics.final，③核新全套与旧13项失败逐名归因，④相对通过候选逐文件核所有文档/协调差异，不以本批9路径排除累计候选差异。均是待复核关注，不签finding/分级或扩大合同。

资源/角色前置已向用户给出具体选项：一次Python全套，额外Nano实例加载最多2（权重文件4次）、CSRT实例最多2，CPU/临时测试数据，补测余额不动，Unity/正式ID/API/GPU/下载新增0；一个新鲜上下文最强独立复核子代理；仅本次R7同源接受核对例外。本机command -v claude没有入口，当前实现子代理与接受均Codex，不能声称满足原§4.3.3异源。用户答复前不开展依赖授权工作；本轮只做已有授权核验、保留成果与准备具体交接。未改现行工作流基础设施。

下一接手由状态板唯一交接行规定。获准后先记录原话与限额、实现补全停点自证，再正式接受核对/独立复核及消费，通过后才重新预检/放行480秒补测。R1-3范围外债、旧负结果/证据及人眼要求均保留。
