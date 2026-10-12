"""P1-ENG-FAST-002 在域检测器 + 关联插件（阶段 1，线 A：Mac `.venv-yoloe`，零 Play）。

模块划分按已接受合同 §2.1：`dataset`（S3 → 两类标签/ignore/三域）、`spotcheck`（§3.1.2
分层语义抽查，AR2-1 释义）、`train`（ultralytics 训练，§3.2）、`select`（V 上的 conf/run/
关联选择与冻结）、`qualify`（H 一次评估、表 V/B、序列回放口径 A）、`plugin_replay`
（口径 B）、`latency`（AC-7）、`report`；`common` 与 `ledger` 是本包公共件。

Unity 真值只用于离线标签、抽查与评分：本包不写桥文件、不接入控制器；数据根
（缺省 `~/TetheredDroneTracking-full`）与两处 `runtime/` 只读。
"""

import os

WORK_ID = "P1-ENG-FAST-002"

# 不让 ultralytics 联网自检/遥测或自动安装任何依赖（§5 线 A：下载 ≤ 1 = 官方 yolo11n.pt）。
os.environ.setdefault("YOLO_OFFLINE", "True")
os.environ.setdefault("YOLO_AUTOINSTALL", "False")
