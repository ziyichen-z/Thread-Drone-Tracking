# P1-ENG-LOOP-002 — C3@K1K2K3K4 操作单异源核对

日期：2026-10-07；Acceptance / Codex（Mac mini）；实现者为 Claude Opus。Dispatch-Id：`P1-ENG-LOOP-002-C3@K1K2K3K4-20261007T061349Z-ec9c`。

## 1. 结论、轮次与范围

**附不满足项及未决关注照交新鲜上下文 Review；本轮不再退回实现，不签复核 verdict，不放行准备 SSH 或 B-main。** 实际核对记录为 C1/C2，复核记录为 R1/R2，故本轮确为 `C3@K1K2K3K4`；下一有开轮资格的复核为 `R3@K1K2K3K4`。C1 已用同停点唯一退回，R1 为一次 REWORK_REQUIRED、R2 PASS；返工计数仍 1/2，尚无第二次返工或冻结集，不把新操作单重新计为 R1。PLAY_GOVERNING 非空只满足 diff 资格，不能代替稳定四条件；Review 先独立核四条件，不成立则按 workflow §4.3.1 写 REVIEW_BLOCKED、不开 R3。本接受角色不替它签该结论。

IR-M1…M8 的现行答复及非生效修订申请见提案「mini操作单待裁定答复与 CHANGE 申请」；最新 AC 表只在提案「Contract conformance（核对表）」。AC-10 不满足；AC-14/15/18 与 AC-16 板端证据缺失，其余仅携带未改代码的既有结论。阶段 A REVIEW_PASSED/ACTIVE 保持，新操作单未通过。三证据未齐，无 UNITY_NA，不签 DONE。

候选与最近通过基线逐字依 `-mini-ops-prep.md` §5 运行时解析；不手抄派生 SHA：

```bash
REVIEW=docs/reviews/P1-ENG-LOOP-002.md
PASS=$(rg '^passed_candidate: [0-9a-f]{40}$' "$REVIEW" | tail -1 | awk '{print $2}')
CAND=$(git log origin/main --format=%H -n1 --grep='^P1-ENG-LOOP-002 mini操作单准备' -- docs/evidence/P1-ENG-LOOP-002-play-ops.md)
git merge-base --is-ancestor "$CAND" origin/main
git diff --stat "$PASS" "$CAND"
git diff "$PASS" "$CAND"
git diff "$PASS" "$CAND" -- controller tools tests config Assets
```

运行时核对：解析候选与本派发所指实现收工相等、可由 origin/main 到达；完整范围 11 路径，其中 PLAY_GOVERNING 仅操作单，代码/配置/测试/Assets diff 空。不得把四题答复后的全部文档差异漏掉，也不把本轮后续接受文档当实现候选。读完整候选文档 diff、合同与复核两轮，再读直接关联入口/计量/轮询/部署摘要代码；没有执行这些代码。

| 完整差异文件 | 核对与归属 |
|---|---|
| docs/authorizations.md | 原签/换机/四题原话及完整表引用；四题原条与其入账提交一致。未修改账本、不代签新口径。 |
| docs/current-status.md | R2消费至mini候选的门/交接与历史；结构节有过期“mini未核、B-main/N-3未签”文字，本批改为当前指针。 |
| docs/evidence/P1-ENG-LOOP-002-mini-ops-prep.md | 全文静态缺口、脚本、映射、自证、IR及附录；§7“全套已用尽”不符现账 2/3，见 §4。 |
| docs/evidence/P1-ENG-LOOP-002-play-ops.md | 全文及替换 diff；签发/暂锁、三单元、STOP与严格门；未修改它，偏差见 §3。 |
| docs/evidence/P1-ENG-LOOP-002-precheck.md | B0a/Air停止/mini完整原流与接受核清；R11后R12续读、deps前两版缺原流保留，静态事实不升级运行证据。 |
| docs/evidence/supervisor-dispatch.jsonl | R1返工至mini准备登记/核销；其他角色的历史记录不归本轮写入，不从报告摘要生成授权。 |
| docs/implementation-status.md | R1-1归因、ACQ具名cause CLOSED与其余 OPEN、各阶段未验证边界；本轮不销债或新增 release。 |
| docs/parked-status.md | ACQ R1-4闭合指针同步；不是恢复暂停或追认旧候选。此路径属其他角色状态维护，不是新增实现功能。 |
| docs/phase1-single-drone-design.md | 已接受设计与历史版本同步；当前运行描述的过期签发状态本批只同步现行指针。 |
| docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md | R2消费至四题落实、原 AC-1…18/三条解释修订；逐维度签发与现场前提分开。 |
| docs/reviews/P1-ENG-LOOP-002.md | R2 PASS/红绿/窄修替代充分及未验证范围；结论只覆盖通过候选，不覆盖新操作单。 |

§4.1 文档闭集外的 dispatch/parked 是其他角色的派发与暂停台账同步，非 PLAY_GOVERNING/代码或基础设施变更；逐文件说明，不借“全是 docs”作一般豁免。

## 2. 合同映射与四条件自证

| mini证据 §4 / 合同 | 候选落点与核对 |
|---|---|
| 四题 §1–2：三文件/库披露、单主臂、本人 Air 前台、签发/暂锁 | 操作单 §0/§3/§4 已列；不扩大库摘要或给 mini 运行权。环境未知、SLOT、Air原件及新候选复核仍缺。 |
| 四题 §3：SSH准备1+服务2、独立根、传输/驻留 | §0.4/§2–4/§14 总数映射齐；实际计次语义未签、准备发起块与复用方案不一致（IR-M3/M8）。 |
| AC-10 / §3.6：三剧本、B/C派生、<2辆停、实时预览、令牌 | §6–10保留已核规则/逐字命令；不加剧本、不从意图取真值选择。 |
| AC-10 / §6.2 / 授权边界修订2 | §13十一处置与首次服务/HTTP失败一致；§14“任何提前STOP其余不开”又覆盖非主臂 S-REBUILD 的继续分支，须同步。 |
| AC-6 / 四题 §3(4)：版本/dirty/采集记录 | §1保持等值与全树干净方向正确，发布引用及实际HEAD记录仍有 PR-8 缺口。 |
| AC-7 / §5.2：HTTP/有效载荷/前台生命周期 | §4/§11有模板；未确定 /result 分类、就绪计量/超限前停止与失败计账，见 IR-M2/M7，不能认定 ≤200 已保障。 |
| AC-14/16：资产、场景副本、峰值/归档、runtime仅移动 | §3/§11–12列明；正式板端assets/新归档未产出，采样最大明确非连续峰值证明。 |
| AC-18 / §7：正式证据停点 | §12零模型回放上限不改，未来仍另过实际 C/独立证据核实；本轮不核正式数字。 |

| workflow §4.3.1 条件 | 自证 §6 与本轮核对 |
|---|---|
| ①范围冻结、完整候选与合同逐项自证 | 文件范围有解析式且已冻结提交，但执行口径 IR-M1/M2/M3/M4/M7 尚未冻结，§4 启动含 `<IR-M7 裁定值>`；G1–G5/准备门有循环。不能把“待裁后终版”当当前候选已满足。Review须独立审此条件。 |
| ②相称自动验证/停点全套，已知失败先处理 | 纯操作单无对应 focused，代码零diff，既有 R2窄修与C1返工全套来源可携带；没有新全套/红绿通过。允许说明不适用，但“零消耗”本身不豁免检查可执行命令与失败路径。代码路线必须另定适用验证。 |
| ③已知Unity失败处理、人眼条件 | 本候选未运行Unity，没有新Unity失败；未来正式用户验证尚未产出，不据“不适用”签 UNITY_NA/AC-14。 |
| ④准确范围、状态、自证与提交/推送 | 候选解析/证据/交接可达；本轮附偏差与 IR 答复照交，不提前启动依赖步骤。 |

## 3. 预复核关注项（非 finding，不分级）

编号承接 C1/C2 的 PR-1…7，不改历史结论，不把下列关注项当新增 AC 或独立 verdict。

| ID / 依据 | 直接读取的路径 / 关注 |
|---|---|
| PR-8 / AC-6/10、四题§3(4) | 操作单§1：从发布引用读 review/账本再 detach 到通过候选解决自引用方向正确；但 `grep -v '^docs/'` 放过 PLAY_GOVERNING 操作单，可能取旧R2 PASS搭配新操作单。必须核已审操作单与候选一致、发布来源限定且固定；不能用所有docs差异证明兼容。§1.5记“计划的分离HEAD”不能替代真实执行检出的HEAD/status；采集前先实测，再在独立文档检出保存/推送原流，回执行检出重核同值/干净。未签任意HEAD或tracked文档脏树豁免。 |
| PR-9 / AC-7/10、已签HTTP | `HttpAdapter.predict_one/_call/bind_identity/status`、`LlamaServerAdapter.predict_one`、`_wait_llama_ready/health_status`：POST、GET result、GET status、loopback health/chat分开可见；/result不执行模型，不可自行并入推理预算免计非推理。335是失败/超时/内置尝试共账，不只accepted成功行。健康GET未入language_serve访问日志，成功listening时间公式在启动失败时没有终点；必须覆盖失败原流并在下一请求前守总账，不把事后发现超限当已合规。 |
| PR-10 / AC-10、已签SSH | §0.5一主连接多channel是待签新单位，不可默认复用免费；prep§2.3却直接Popen ssh，不用同一CM。`ssh -S`还须在套接字失效时禁止回退新认证连接、记失败/起止/收尾，不能暗耗第四次。 |
| PR-11 / AC-7/10、engineering§9 | `llama_server_command`仅四类旗标；JET原显式旗标/内存事实不是当前命令可运行证据。源码归档默认值/完整上下文KV投影也不能证明当前二进制真的采用该值或必然OOM。不能通过首次加载试未知条件；代码路线、旗标冻结和资源兼容先解决。 |
| PR-12 / AC-10、停止纪律 | G4要求准备读数，而§1适用“每次SSH前”/顶层全部G门先过造成准备门循环；§0.4准备仅G1–3又漏G5来源。prep§2.2读脚本有readelf/ldd失败仅打印、不核扩展Machine、pgrep rc=2当无匹配的路径；不能称全部fail-fast。操作单须指定逐字命令的bash环境（PATHS未引号的tar/shasum在zsh不按bash分词），`cd ... && umask ...; date ...`后失败也可能继续启动；停止边界不能只依赖最终服务拒启。`ls Assets/_Recovery`无输出不证明目录不存在。 |
| PR-13 / AC-13、验证适用性 | mini§7称N-1全套已用尽，复核R2/提案原账为2/3；纠正为累计2/3、此文档轮未跑，余1不是本派发测试许可，不重置/转用。bash-n/AST/来源解析非真实Air或板端执行验证；未跑命令/健康上限/新flags仍未验证。 |
| PR-14 / A2(e)、engineering§9 | CPython3.12.14源树代理板3.12.3、只跟模块级import的分析不覆盖函数内标准库动态依赖或板构建ABI；Python下层必需闭包仍待目标条件事实，不把少量PyInit/文件存在当可import证明。-I/-S隔离不等于完整环境核验；ENV:2仅条件申请，没另签就不运行。 |

`-mini-ops-prep.md` 的 IR-M2 数千轮询估计和 IR-M7 1201 上界是规划风险，不是实测消费或必然超限证据；其20s示例不能自动成为新就绪失败阈值。HTTP字节仍按Air↔板language_serve实际访问日志全行求和，含result/status与异常/不完整；不把loopback复制一遍纳入同一60MB，也不从原投影推出余量保证。

## 4. 验证适用性、消耗及交接

本轮零功能测试/模型/SSH/复制/评分/Jetson/Unity/runtime操作；仅文档、git diff及源码文本读取，提交前运行角色写入与文档自检。纯文档适用性与旧代码证据可携带，但操作单的门循环/待定参数、STOP矛盾、失败路径仍未满足，不能用无测试覆盖掩盖。没有新增运行证据、finding、债务release或预算消费。全套仍2/3，回放及N-2/mini原账保持；条件性代码或ENV:2的验证须独立核范围/原账，不在本轮授权执行。

全局0条消耗性、2条零消耗活跃交接；全部机读blocks/releases沿顺序核对，实质ACQ R2-1已有release，无未release实质block；SLOT/环境/操作单门仍独立有效。交接Review先读本文件、提案最新核对表/IR答复、mini证据与完整候选；稳定门不过按规则记录，不预开R3、不重开C1首退。用户决策由supervisor转呈并由发生会话入账，接受再落实；本会话不提问或代录用户原话。

收工自检：`python3 tools/check_role_writes.py --role acceptance` 通过（本批5路径）；`python3 tools/check_docs.py` 通过（轨道/Gate-echo/消耗性门/体量等）；`git diff --check` 无错误。这两项Python为规定的文档自检，不是功能测试。
