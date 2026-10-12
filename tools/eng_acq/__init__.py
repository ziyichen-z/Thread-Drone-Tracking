"""P1-ENG-ACQ-001 离线 E1/E2 线束（阶段 1，§3.9；零 Play、零检测新推理、零训练）。

模块：`common`（路径、受保护写入、规范 JSON、消耗账本与信封守卫）、`data`（三序列帧、sidecar、
冻结检测缓存、真值索引与完整性核对）、`e2`（常驻关联回放、保持率/ID 切换/寿命与位姿自检）、
`e1`（样本、扰动臂、第二级缓存回放、十五桶与守恒）、`run`（命令行）。

Unity 真值只用于离线样本构造（k 帧指定框、vis_r、IoU_r）与评分；控制器侧 `controller/` 不导入本包。
数据根（缺省 `~/TetheredDroneTracking-full`）与两处 `runtime/` 只读，写入只落 `outputs/eng-acq/`
与 `docs/evidence/`（AC-9）。解释器 = 数据根 `.venv-yoloe`（有 `lap`；pip 0）。
"""

import os

WORK_ID = "P1-ENG-ACQ-001"

os.environ.setdefault("YOLO_OFFLINE", "True")
os.environ.setdefault("YOLO_AUTOINSTALL", "False")
