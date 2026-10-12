# P1-ENG-CAPTURE-001 — Air 第二次 Play 实际结果

Owner: Implementation；2026-10-10；停点范围 PlayK2K4。仅证据整理，未改运行时代码，未签通过或 DONE。

## 0. 执行与原件

第二次本人授权 Play 已实际执行。新鲜 f0=0，T_sess=230 s；启动 HEAD/空 porcelain 与覆盖 SHA 原始记录在 `outputs/eng-capture/play/attempt-2-control/launch.json`、`prelaunch.json`。当轮通过候选从同名复核机读行动态解析；运行代码无 diff。全部产物留 Air。

用户在第902帧后手动退出，903帧齐备；自由切换12次点击、11次提交绑定。会话随后由既有 stop 安全终止，operator_stop/APPLIED，session/click服务 exit 0；首个 stop 因缺共享 runtime 明示参数被拒（未写请求），补齐后仅一次有效 stop。原始日志含旧请求 ILLEGAL_WRITER_SUSPECTED，保留不洗白。

归档 `outputs/eng-capture/play/capture-play-1/unity-runtime/`：1809文件/50,887,855 B，同卷无覆盖 rename；移前后逐件 SHA 全等。机器清单 `attempt-2-archive.json`、`capture-play-1/SHA256SUMS.json`；第二次编排源 `attempt-2-companion-source.py`。首次失败Play独立保全，不混入评分。

## 1. AC-22

12点击原始全流在 `capture-play-1.click-web.jsonl`，会话 `sessions/capture-play-1/`。尚未正式评分，不把11次绑定或 APPLIED 回执当端到端≤1帧通过。全部发出点击含失败保留。

## 2. AC-23

EVIDENCE_MISSING：用户明确自由切换，未核定S2/S4原序号，也未确认红车完整一圈。保留现场跟随良好的反馈及2–3次不灵敏反馈；不猜目标身份，不运行缺参数的两次评分。

## 3. AC-24

NOT_RUN（零模型评分未运行）。预测窗口原日志已保全，不以存在日志判通过。

## 4. AC-25

EVIDENCE_MISSING：原S2、S4保持窗无法核定；未计算d0/N/进带/保持，未以自由切换代正式剧本。

## 5. AC-26 与预算

用户原话已转交接受角色代录Unity日志；本实现角色只读该日志。模型/session启动各1；正式run数量须接受角色沿真实目录核定（session目录无run-*子目录，不把0目录当0运行）。Play累计2/2，无再重开额度。

第二次准备基线20:36:26.569Z；终端安全结束20:42:13.765Z；归档结束20:42:32.549Z。close-meter实测准备至计量404.587 s，旧墙钟保守360 s，共764.587 s；本文件写入及最终资源封口仍计本次420 s。已知磁盘保守291,059,456 B，含路径移动重复计量；历史附属峰值UNKNOWN保留。采样元数据不能证明所有短命辅助峰值，不主张完整B符合。最终封口见 `attempt-2-control/execution-close.json`：第二次438.978 s，超过单attempt420 s约18.978 s；旧360 s保守共账798.978 s。运行与归档及时结束，但证据整理导致本次超时，记执行偏差，不能称全信封符合；封口后文档/提交核清附属耗用尚待接受角色记账，不把该值当最终完整B总耗时。

## 6. 稳定停点自证与交接

1. 范围/接口冻结：AC-21…26合同不改，本批仅操作/证据。
2. 验证：已通过阶段A代码与测试证据沿同名K1K2K3K4-handoff，不重复已用尽全套/模型；本次正式剧本、评分缺项，不能自证相称验收已通过。
3. Unity：用户反馈基本跟住/切换、2–3次不灵敏且手动停止；原因未定位，没有修复或聚焦复测，不把反馈改成全剧本通过。
4. 状态/风险：本轮是缺项与负结果收尾，四项稳定候选条件未齐，不申请独立复核通过。交Acceptance核清资源/现场反馈/剧本偏差与后续处置；不启动依赖本次结果的实现。完整差异由同名复核最近passed_candidate到当前HEAD动态解析，原件在上述路径；不手抄候选SHA。
