"""P1-ENG-JET-001 板端可行性探测（阶段 A：S0 环境核验、S1/S2 快层线束、SR 中继）。

模块划分按已接受合同 §3：`common`（路径、受保护写入、nearest-rank 分位数、信封常量；纯标准库，
板上与桌面机共用）、`env_probe`（S0 只读读数与预注册判定）、`fastlayer_bench`（S1/S2 板上快层线束，
经 `DetAssocTracker` 构造函数注入引擎加载器）、`replay_publish`（桌面机 5 Hz v3 回放器）、`relay`
（桌面机 ↔ 板 TCP 中继 + UDP 四时戳对时 + 回声应答器）、`assets`（AC-11/12 资产核实与板上清单）、
`ledger`（AC-10/15 消耗账本与待用户项）。

真值隔离（合同 §2.2、AC-12）：本包不读 gold、`truth/`、索引或数据根其他内容；主树 `runtime/` 与数据根
结构性只读（`common.refuse_protected`）；板上运行目录只在 `~/eng-jet/`。
"""

import os

WORK_ID = "P1-ENG-JET-001"

# 不让 ultralytics 联网自检/遥测或自动安装任何依赖（§5 阶段 A：模型下载 = 0，pip 逐包记账）。
os.environ.setdefault("YOLO_OFFLINE", "True")
os.environ.setdefault("YOLO_AUTOINSTALL", "False")
