"""P1-ENG-FAST-001 快层替换探针（全离线，零 Play）。

模块划分按已接受合同 §2.1：`inputs`（联表/参考库/身份清单）、`detect`（T0-bank /
T0-oracle）、`recall`（P1 分桶召回）、`margin`（P2a）、`replay`（P2b）、
`vlm_arms`（P3 臂 A/B/C）、`vlm_remote`（5060 自含查询脚本）、`baseline`（臂 D）、
`latency`、`report`；`common` 与 `ledger` 是本包内部公共件。

Unity 真值只用于事后评分：本包不写任何桥文件、不接入控制器，`runtime/` 只读。
"""

WORK_ID = "P1-ENG-FAST-001"
