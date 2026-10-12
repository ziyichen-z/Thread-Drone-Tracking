#!/usr/bin/env python3
"""P1-ENG-ASSET-001 旧资产适配盘点工具包（只读原件、纯离线、零模型）。

合同：`docs/proposals/P1-ENG-ASSET-001-legacy-asset-inventory-and-minimal-instruction-set.md`
（D3 用户收敛版，2026-09-08 `ACCEPTED`，`Workflow: engineering-v1`，唯一必经
停点 `K4`）。本包只回答三个问题：旧数据里的类别/颜色/框哪些可用；沿用既有
Tier-1 模板能形成哪些无歧义指令、分布在哪些既有划分；后续语言选框模块接入
现有跟踪器需要满足哪些输入与接口条件。

边界（AC-6 / §3 红线，机检见 `tests/test_eng_asset_inventory.py`）：

- **不 import** `controller.track_loop` / `controller.run_log` /
  `controller.trackers`；本包不运行任何跟踪器、不调用任何模型。
- 写出只允许落在 §3 表 A 的 A2 闭集；`receipts.assert_output_allowed` 对禁写
  闭集（`runtime/dist-data`、`runtime/test-results`、`config/`、`Assets/`、
  `controller/`、`tools/dist_data/` 等）做包含检查，命中即拒绝并写失败收据。
- 指令语义**逐字复用**既有函数（`tools.dist_data.build_catalog.frame_world` /
  `minimal_program_with_reference` / `prospective_mother_eligible`），本包不自写
  冲突判定，也不改写 S5 字段与冻结常量。
"""

from __future__ import annotations

WORK_ID = "P1-ENG-ASSET-001"
SCHEMA_PREFIX = "p1-eng-asset-001"
ATTEMPT = "attempt-2"
