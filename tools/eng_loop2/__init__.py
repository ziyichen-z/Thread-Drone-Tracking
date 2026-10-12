"""P1-ENG-LOOP-002：闭环接入与四类数字首测（阶段 A 代码候选 `K1K2K3K4`）。

板上部署闭集成员（`config/p1-eng-loop-002-board-deploy.json`）：本包只放纯标准库模块；
`analyze_play` 是离线评分器（真值只在其中使用），**不在**部署闭集、不被 `controller/`、
`llama_adapter`、`tools/language_serve.py` 导入（AC-9）。
"""
