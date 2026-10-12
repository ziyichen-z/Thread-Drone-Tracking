"""P1-VLM-DATA-001 G0 目录门 + D0 数据引擎（纯离线工具包）。

设计合同 = `docs/proposals/P1-VLM-DATA-001-grounding-data-foundation.md`
revision 2 + §14 BC-DATA-1…5（round 3 `ACCEPTED_WITH_BINDING_CLARIFICATIONS`）。

本包只做离线数据工程：不被 Unity 运行时或 `controller/` import，不触碰
帧桥、不发起任何模型/API/GPU 调用、不创建 scenario/session/run ID。
阶段划分见 `artifacts.py` 的 `STAGES`（S0–S9 单向 DAG 与禁行边）。
"""

from __future__ import annotations

__all__ = [
    "artifacts",
    "audit_tool",
    "bind_layout",
    "build_catalog",
    "build_inventory",
    "contract",
    "g0_report",
    "gen_mother_templates",
    "make_splits",
    "project_boxes",
    "roots",
    "tier1_lang",
    "verifier_contract",
]
