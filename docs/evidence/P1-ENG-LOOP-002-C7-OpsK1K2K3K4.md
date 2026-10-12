# P1-ENG-LOOP-002 — C7@OpsK1K2K3K4 核对与独立复核交接

## 0. 角色、输入与边界

日期：2026-10-08；owner=Acceptance（Codex，异源只读核对Claude Opus实现）；requested.round=`C7@OpsK1K2K3K4`；Dispatch-Id=`P1-ENG-LOOP-002-C7@OpsK1K2K3K4-20261008T050706Z-1e0f`。本停点第二次核对，C6首退已用1/1；**只核对、不再退回，附表与未决关注照交新鲜独立R1@OpsK1K2K3K4**。不新增AC/修订、finding/分级/blocks/releases，不签独立verdict或运行放行。

标识由本轮脚本读取交付§7.0、复核机读行、用户日志登记并调用git解析写入：
- 当前代码候选：`d3c3ff03d8c73a9f0adb40cb5c6546f9ad1a89db`（交付§7.0首项）。
- 最近有效通过基线：`9d95aeb817795db992d55f29991ccacdec8b5b88`（同名复核最新有效`passed_candidate`，R1@K1K3已消费；不代Ops通过）。
- 本系列第2次停点全套对应候选：`b6bd195bf1bca56f0107f82d2b802d923b614bfd`（交付§7.0/§11.3）。
- 完整候选diff：上述通过基线至当前代码候选，30 files changed, 10684 insertions(+), 57 deletions(-)；本轮同时读候选之后的交付§7.0/§11、两份ops-c6rework日志及状态/派发增量。候选至开工HEAD的PG差异为空；完整候选diff未排除历史文档/账本/复核。当前交付与代码候选分开核，不把后续文档提交称新代码候选。

必读已覆盖状态板结构/全部交接及本项依赖、workflow/engineering/acceptance角色、工程继承清单与缺陷账本、正式设计相应节、生效AC与三节OPS追加合同、C6§2–5、交付§7.0及§11.1–11.5、完整diff和直接关联代码。代码结论为静态核对；**本轮未运行功能测试/探针、未SSH/板/Play/Unity/真实模型/回放/正式ID/API，consumed=none**。

## 1. 完整候选范围与PLAY_GOVERNING

新Ops首轮独立复核全量范围=最近有效通过基线到当前候选；不是旧K1K3增量返工或旧K1K2K3K4终局续轮。PG唯一定义沿workflow §4.4：controller/、Assets/、tools/、tests/、config/、ProjectSettings/、Packages/packages-lock.json及本项冻结三份操作单。本候选PG非空，恰为以下10路径：

- `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md`
- `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md`
- `docs/evidence/P1-ENG-LOOP-002-play-ops.md`
- `tests/test_eng_loop2_operator_web.py`
- `tests/test_eng_loop2_play_ops.py`
- `tests/test_eng_loop2_summarize_ops.py`
- `tests/test_loop2_isolation.py`
- `tools/eng_loop2/operator_web.py`
- `tools/eng_loop2/play_ops.py`
- `tools/eng_loop2/summarize_ops.py`

上述三份操作单均须逐行核，不以docs目录豁免；controller/、Assets/、config/、ProjectSettings/、packages-lock及原语言服务/适配器/部署摘要/评分算法等无新增代码diff。`.gitignore`两行亦须旁读。全量30路径逐文件归属如下；历史文档不取得新复核通过效力：

| 路径 | 归属与只读范围说明 |
|---|---|
| `.gitignore` | IR-OPS-8唯一具名追加：用途注释及/outputs/eng-loop2/；AC-10修订5，非PLAY_GOVERNING。 |
| `docs/P1-ENG-LOOP-002-diagnostic-smoke-ops.md` | 新工具/对应测试或冻结操作单；AC-5/8/9/10/11/13/14/15/16/18，逐文件细映射沿交付§3、§7.0、§11。 |
| `docs/authorizations.md` | 既有用户授权来源；本轮只读、不代录。 |
| `docs/current-status.md` | 既有合同/当前门与证据指针的文档同步；不以文档推进替实现或独立复核。 |
| `docs/evidence/P1-ENG-LOOP-002-C5-K1K3.md` | 历史核对/身份修复/OPS实现与测试/逐文件映射证据；AC-11/13与核对范围来源，逐文件已读。 |
| `docs/evidence/P1-ENG-LOOP-002-C6-OpsK1K2K3K4.md` | 历史核对/身份修复/OPS实现与测试/逐文件映射证据；AC-11/13与核对范围来源，逐文件已读。 |
| `docs/evidence/P1-ENG-LOOP-002-OpsK1K2K3K4-handoff.md` | 历史核对/身份修复/OPS实现与测试/逐文件映射证据；AC-11/13与核对范围来源，逐文件已读。 |
| `docs/evidence/P1-ENG-LOOP-002-diag-page-fix.md` | 历史核对/身份修复/OPS实现与测试/逐文件映射证据；AC-11/13与核对范围来源，逐文件已读。 |
| `docs/evidence/P1-ENG-LOOP-002-idfix-k1k3.md` | 历史核对/身份修复/OPS实现与测试/逐文件映射证据；AC-11/13与核对范围来源，逐文件已读。 |
| `docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md` | 新工具/对应测试或冻结操作单；AC-5/8/9/10/11/13/14/15/16/18，逐文件细映射沿交付§3、§7.0、§11。 |
| `docs/evidence/P1-ENG-LOOP-002-ops-focused-tests.log` | 历史核对/身份修复/OPS实现与测试/逐文件映射证据；AC-11/13与核对范围来源，逐文件已读。 |
| `docs/evidence/P1-ENG-LOOP-002-ops-ir78-tests.log` | 历史核对/身份修复/OPS实现与测试/逐文件映射证据；AC-11/13与核对范围来源，逐文件已读。 |
| `docs/evidence/P1-ENG-LOOP-002-ops-progress.md` | 历史核对/身份修复/OPS实现与测试/逐文件映射证据；AC-11/13与核对范围来源，逐文件已读。 |
| `docs/evidence/P1-ENG-LOOP-002-ops-tests.log` | 历史核对/身份修复/OPS实现与测试/逐文件映射证据；AC-11/13与核对范围来源，逐文件已读。 |
| `docs/evidence/P1-ENG-LOOP-002-ops-validation-plan.md` | 历史核对/身份修复/OPS实现与测试/逐文件映射证据；AC-11/13与核对范围来源，逐文件已读。 |
| `docs/evidence/P1-ENG-LOOP-002-play-ops.md` | 新工具/对应测试或冻结操作单；AC-5/8/9/10/11/13/14/15/16/18，逐文件细映射沿交付§3、§7.0、§11。 |
| `docs/evidence/supervisor-dispatch.jsonl` | 此前派发/核销历史，非运行证据；本轮不写。 |
| `docs/implementation-status.md` | 既有合同/当前门与证据指针的文档同步；不以文档推进替实现或独立复核。 |
| `docs/phase1-single-drone-design.md` | 既有合同/当前门与证据指针的文档同步；不以文档推进替实现或独立复核。 |
| `docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md` | 既有合同/当前门与证据指针的文档同步；不以文档推进替实现或独立复核。 |
| `docs/reviews/P1-ENG-LOOP-002.md` | 旧K1K3通过轮/基线与CLASS_3来源；本轮只读，不签或改verdict。 |
| `docs/unity-test-log.md` | 本人SUB:2保真原话/呈现登记；本轮只读。 |
| `runtime/README.md` | 操作入口/分工说明，AC-10/13；无实际runtime产物修改。 |
| `tests/test_eng_loop2_operator_web.py` | 新工具/对应测试或冻结操作单；AC-5/8/9/10/11/13/14/15/16/18，逐文件细映射沿交付§3、§7.0、§11。 |
| `tests/test_eng_loop2_play_ops.py` | 新工具/对应测试或冻结操作单；AC-5/8/9/10/11/13/14/15/16/18，逐文件细映射沿交付§3、§7.0、§11。 |
| `tests/test_eng_loop2_summarize_ops.py` | 新工具/对应测试或冻结操作单；AC-5/8/9/10/11/13/14/15/16/18，逐文件细映射沿交付§3、§7.0、§11。 |
| `tests/test_loop2_isolation.py` | 新工具/对应测试或冻结操作单；AC-5/8/9/10/11/13/14/15/16/18，逐文件细映射沿交付§3、§7.0、§11。 |
| `tools/eng_loop2/operator_web.py` | 新工具/对应测试或冻结操作单；AC-5/8/9/10/11/13/14/15/16/18，逐文件细映射沿交付§3、§7.0、§11。 |
| `tools/eng_loop2/play_ops.py` | 新工具/对应测试或冻结操作单；AC-5/8/9/10/11/13/14/15/16/18，逐文件细映射沿交付§3、§7.0、§11。 |
| `tools/eng_loop2/summarize_ops.py` | 新工具/对应测试或冻结操作单；AC-5/8/9/10/11/13/14/15/16/18，逐文件细映射沿交付§3、§7.0、§11。 |

补丁相对已跑全套候选只有`operator_web.py`、`play_ops.py`与`tests/test_eng_loop2_play_ops.py`，git统计为3 files changed, 72 insertions(+), 23 deletions(-)。直接关联读取原CLI/桥/确认与会话状态事件、冻结检查点/身份/部署与原评分/归档契约；旧通过范围携带，不把新增工具自动置为通过。

## 2. C6-1/2/3完成条件核对

| 原核对项 / 既有依据 | C7结论 | 已完成部分与证据 | 未闭完成条件及交复核的具体源路径 |
|---|---|---|---|
| C6-1；AC-10修订3/W4/O3、AC-14修订2 | 满足 | Submitter.seal/claim/submit同锁不可逆封住，App业务入口同核；PlanScheduler.halt/_block及诊断halt阻止发送/跳过/确认/拒绝/release和下一计划推进；迟到回执只记HALTED/UNKNOWN；原stop共享通道每会话至多一次。交付§11.1/11.2，HaltTests、正式Ctrl-C及诊断STOP1/UNKNOWN-stop生产入口替身证据对应。 | 本结论限业务封锁及单stop；收尾失败未传播仍列C6-2，不把按会话seal冒充全局后续流程已停。既已在途受理的命令只记事实，不称撤回已执行请求。 |
| C6-2；AC-10修订3/O3、AC-14修订1/2 | 不满足 | run_attempt捕获BaseException后统一安全收尾，stage_play服务/日志/关单元/记录/摘要分步try；正式挂起不杀进程、不归档，Unity未静止记S-WALL；截止改为等待Play起点+420s。交付§11.1/11.2的挂起/仍出帧/Ctrl-C/部分日志失败用例支持这些分支。 | attempt_closeout.failed（play_ops.py:1937）只将Stop加入found，非Stop异常/Ctrl-C只写closeout文本。若原会话正常且archive_attempt.rename抛OSError，loads=1及operator_stop分类无Stop，run_attempt仍可正常返回，stage_play可继续下一剧本；未兑现失败UNKNOWN/非零/停依赖。stage_play反馈窗口后的log.write在web_shutdown保护外，写入异常可越过网页收尾；web_shutdown异常只记文本不置failure。原stage_receipt finally顺序收尾（:1638附近）也可能一项失败跳过后项，交R1核既有合同边界。 |
| C6-3；AC-8修订3、AC-10修订3、AC-18修订1 | 不满足 | attempts在调用前登记、record原地填写；S-LOAD/backend_fatal/部分失败记录与摘要字段已补，HALTED仍是样本，MISSING_RECORD与确实未执行分列。on_reply在释放在途锁前记计划，确定性竞态红3/3绿3/3与133例focused见交付§11.2及原输出。 | Submitter.submit（operator_web.py:650附近）on_reply异常只记录record_reply_failed并返回正常reply，回执/决策细节完整性未进入失败判断；收尾未从Submitter.records逐请求核补。正式attempt_closeout（:1963）和诊断_record_play（:2927）在途锁acquire超时仍继续snapshot，未把未静止记录明确作UNKNOWN并停止/补账；record块非Stop异常亦被局部failed只记文本，初始NOT_EXECUTED占位可保留。已知竞态正常路径修复成立，不能据此签任何失败出口都不将已受理请求当未执行。 |

这是对C6原完成条件的核对，**不是新增AC、正式复核finding或分级**；以上异常分支是只读代码发现的未闭主张，acceptance未注入故障或跑测试，由R1新鲜核实可达性、原证据充分性与独立处置。实现所报“C6-1/2/3全部修复”不直接作为核对结论。

最新18条Contract conformance只写于同名提案该具名节：AC-8/10/14不满足，AC-15/16/18证据缺失；其余静态/提交义务按表满足。后置真实证据缺失不是新C阻断；C7不再退回、不扩合同。

## 3. SUB:2呈现版本判读（无需本人重看）

**裁定：复用已有本人两张一致的记录；needs_user=none，R1无需等用户重看。** 合同「OPS基线与IR78裁定」§4和已签SUB:2触发的是“呈现代码变化”，不是整个Python文件blob变化。用户日志UT-P1-ENG-LOOP-002-OPS-SUB2登记呈现HEAD=`0c1eb6833fcabd092ff2f6a7317b63328b575399`，旧blob=`3ecd79602634e988c4223af18fa41731fbec7fdf`；当前代码blob=`13db5f119e0976b05db08cf5ff358ac70a2814a7`，的确不同。交付§5.1的旧“文件blob不变”理由不适用于当前候选，本轮改按实际呈现定义判读，不改写原历史证据。

完整web diff仅模块W4说明、Submitter封锁/回调、App动作拒绝及发送/选择/停止记账；从登记版本至当前候选，以AST定位后比较原源码片段，`PAGE`, `FIDELITY_PAGE`, `FidelityHandler`, `load_fidelity_samples`, `Monitor._presentation`, `Monitor.preview_identity`, `App.preview_bytes`, `App.frame_bytes`, `Handler`均逐字相等。原源图字节、预览身份/序号/顺序/坐标、HTML/CSS/JS的图像显示与保真页服务路径未变；本轮未渲染、未看样图、不代判人眼。本人既有外观一致记录和确认人可携带到该呈现路径，提示行绿色sha/已解码实见值与用时仍UNKNOWN，不称模型选对、真实Unity/正式指标通过。R1仍须独立核呈现不变判断，若发现真实呈现变化才按现行SUB:2剩余额度路由本人重核；本轮不预留用户等待门。

## 4. 最后竞态窄修的engineering §6替代

**判读：可提出具名替代申请，适用性与充分性交独立Review判断；本轮不要求重跑全套、不预签当前候选稳定条件②。** 最新窄修三文件限共享在途锁、计划记录回调、相应确定性回归；原真实模型加载器、数据划分、analyze_play指标算法零diff。另一方面，记录回调/收尾快照关联AC-8/18的计划—实际与完整失败分母；不能仅凭analyze_play文件未改就免去Review对“对外指标路径”前提及测试覆盖的判断。若复核认定触及该路径或证据不足，原engineering §6保留要求实现全套的权力。

交付§11.3及`docs/evidence/P1-ENG-LOOP-002-ops-c6rework-tests.log`：已测候选2450例、4 failure/13 error/54 skipped、rc1；16项已接受基线仍失败、JET两项本次不在失败列表而根因UNKNOWN、不称已修；唯一新增失败是backend_fatal受理记录竞态。408.22s real、44,950B在已签上限内，真实模型加载数UNKNOWN。新增竞态的最后窄修在当前候选有133例focused OK及确定性修前红3/3、修后绿3/3，原输出`docs/evidence/P1-ENG-LOOP-002-ops-c6rework-focused.log`；**补丁未跑全套、不记全套通过**。本轮只读原日志/源码，不复算这些测试。

SUB:1按已签最多3个真正候选、每候选1次，当前已用2次，剩第3候选1次。该余额不授权acceptance/Review再跑全套或同候选第二次；若R1判需全套，交实现按合同/新派发使用真正新候选的一次余额，另具名日志，不能仅改文档凑候选。额度超限、同候选第二次、安装或新增类别再回用户；目前无须新签、不重置N-1 3/3或旧账。

## 5. 新鲜独立R1入口、未决关注与停止边界

接手角色=Review；目标=`R1@OpsK1K2K3K4`；**唯一复核文件入口`docs/reviews/P1-ENG-LOOP-002.md`，由Review追加实际Ops首轮或具名派发REVIEW_BLOCKED记录**。以§0当前候选/最近有效通过基线作全量diff，以§1十PG路径为必读范围，旁读完整30路径中的非PG增量/直接关联代码、最新AC核对表、C6§2–5和实现交付§7.0/11。不用C7意见替代读码、不借旧PASS通过新Ops。Review只在一次性worktree接触实现代码；发现缺陷只写复核文件，修复交实现。实际开轮、verdict、finding依据/分级、全局blocks/releases由独立角色按规则签发。

| 关注项 | 原依据/源路径与所需独立判断 |
|---|---|
| C6-2/3未闭 | §2的非Stop失败传播/安全收尾和受理记录异常/锁超时；核既有合同是否兑现，不按实现自报闭合。 |
| PR-O1（携带） | play_ops.DIAG_RELEASE_LINE（:2199）与prepare（:2578附近）对提案全文任意位置匹配sub3_release，不限制具名消费节；值绑定与缺行/错值/不可读拒启已有替身。接受仅能在具名通过消费节程序写实际行；本轮没有有效行，不把格式示例或旧passed值当消费。R1判断全文匹配的门风险，C7不新增节定位解析AC。 |
| PR-O2（携带） | 前台ssh -tt/交互bash/Ctrl-C/同会话端口释放、真实会话stop延迟、真实Unity Play/停帧均未验证，只有本地替身；本人SUB:2只证明呈现外观。挂起会话不杀进程，ResourceWarning与仍运行记录保持，不能把后来自行退出倒填为工具已证停止。诊断stop_unity_and_move_frames只核Unityquiet、未另核会话已退出，请核尚在运行时移动的安全边界。 |
| PR-O3（携带） | stage_play摘要非零rc只写closeout、summarize_ops内原score非零也只存状态；同时formal摘要逐归档各一次，可遇3归档而原实现评分额度≤2。核失败非零/停依赖、原评分预算与不可静默漏分母，不重写算法/资源额度。 |
| 新截止偏保守 | 正式等待Play起点+420s，晚按Play会压缩正常会话/停Play余量并触S-WALL；原T_sess≤290s与余帧公式未变。额外安全收尾等待不是Play额度，不把出帧/TERMINAL时刻当本人按钮时刻；确认操作单/实现/合同一致，保留实际UNKNOWN。 |
| 替代与保真 | §3无需本人重看，§4仅提交替代待R判断；C7不签新Ops稳定/独立通过。 |

四条件预核：①范围/接口已按生效合同冻结（C6-2/3是实现忠实性未闭，不新造合同歧义）；②原新增竞态已有实现红绿/focused、已接受环境基线仍携带，但最后窄修替代与未闭代码分支充分性待Review独立核；③无已知Unity失败待修，此候选真实Unity/板端NOT_RUN，SUB:2呈现记录按§3携带；④实现现行自证、代码候选、未核风险、核对表和状态/交接指针齐，复核文件只由Review写。**这不是acceptance的REVIEW_BLOCKED或通过裁决**；独立Review先核四条件，不成立则REVIEW_BLOCKED不开轮，成立再按新范围R1开轮。C7不再退回，与首退上限不冲突。

新Ops仍IMPLEMENTED/未复核；Overall REVIEW_PASSED/ACTIVE仅旧范围。SUB:3仍等新Ops独立通过及接受消费并程序写sub3_release；本轮不放行诊断/正式G1–G5/B-main/Play。AC-14/15/18及AC-16板端NOT_RUN，无UNITY_NA/DONE。旧K1K3 C5/R1、旧K1K2K3K4 R4终局/返工2/2/冻结集闭合、25条AC修订/新AC0、旧债/偏差/UNKNOWN及ACQ暂停保持。当前轨道0消耗性+2零消耗（本项Review与JET用户方向），不新增第三行。

## 6. 本批自检

- `python3 tools/check_role_writes.py --role acceptance`：通过，未提交改动5路径均在acceptance范围。
- `python3 tools/check_docs.py`：通过，分节/字节/轨道/Gate-echo/全局消耗性门等检查通过。
- `git diff --check`：通过；本批仅5份acceptance文档，不改代码/测试/复核/授权账本。功能测试未运行。

open_items: none
