# 阶段 1 接口 B 零训练探针：测试设计（2026-10-11，supervisor 写；diagnostic_only、gate_evidence=false）

依据：账本 2026-10-11「用户按草案签发 VLM-DIAG:B:1」条（信封逐字在该条，本文不放宽任一维度）及同日「用户按推荐追加 VLM-DIAG:B:1」条（修订 1，见文末）；gold 口径按同日「第 1 题」条（可见框，按可见比例四档报告）；远处小目标按同日「第 2 题」条（单列小样本子集并报置信区间）。先例：2026-10-09 `JET:CORES-DIAG:1` 独立目录执行。
接口 B 定义见 `docs/project-background.md` §3：检测器给编号候选框，VLM 回答第几号符合描述，并报歧义或不存在。本轮候选由场景真值给出（候选充分条件那一级），端到端（检测器候选）不在本轮。

## 1. 输入（全部只读，mini 数据根 `~/TetheredDroneTracking-full/`）

- 评估集 `outputs/eng-sft/P1-ENG-SFT-002/data/eval.jsonl`（609 行，sha256 `5d86013f06b4d64a9e3fd92a1d8f99eb06b4910187a0851cf595d75ebe93d0bb`）。
- 帧图 `outputs/eng-sft/P1-ENG-SFT-002/upload/frames/<frame_sha256>.jpg`（逐张核 sha256 = 行内 `frame_sha256`）。
- 对象真值：S3 目录 `runtime/dist-data/frames_catalog/attempt-2/`，取法与核验逐字沿用阶段 0 审计脚本 `~/vlm-diag/COORD-VLM-DIAG-2026-10-10/stage0-20261011/audit_stage0.py`（sha256 前缀 `3688beff34f7659a`）的真值读取与分片 sha 核验部分（可复制进本轮脚本，不改原文件）。
- 参照（只作对照列，不是同一任务）：C2 接口 A 预测 `outputs/eng-sft/P1-ENG-SFT-002/returned/sft-20260918T223245Z-bd1f5ebb/predictions/eval-adapter.jsonl`（`0ccb4f1e…`）。
- 模型：基座 HF 权重 `outputs/eng-loop/P1-ENG-LOOP-001/model/base/`（转换来源）；板上已有 `~/eng-jet/stageb-transfer-20261004T225001Z/Qwen3VL-2B-Instruct-Q4_K_M.gguf` 与同目录 `mmproj-Qwen3VL-2B-Instruct-F16.gguf`、`~/eng-jet/stageb-build-20261005T033318Z/build/bin/llama-server`、同树 `src/ggml-org-llama.cpp-836d571/convert_hf_to_gguf.py` 与 `gguf-py/`。

## 2. 计分行

- 进入推理：`gold_state` ∈ {unique, ambiguous, none} 的 551 行（G1 210、G2 49、G1t 23、G2t 23、G4 86、G3 48、G3t 12、G5 100）。`G3p`（50）与 `LEGACY_ONLY`（8）`gold_state` 为空，不推理、不计分。
- 正式查询数 = 推理行数 × 2 精度 × 2 呈现（551 行时为 2,204；修订 1 后扣除 `ZERO_CANDIDATES`/`CANDIDATE_MAP_FAIL` 行，如实报告）；计时冒烟每精度 ≤ 20 行 × 2 呈现，冒烟行另计，不并入正式结果。总上限 2,600 次（信封第 4 项）。连接失败同行重试至多 1 次并计入次数；解析失败不重试，计失败。

## 3. 候选集与编号

- 候选 = 该帧真值中画面内车辆（与阶段 0 `t2` 的「画面内车辆」同一定义）**去掉完全被遮挡者（`EXCLUDED_OCCLUDED`）**（修订 1），每个候选取裁剪到画面的可见框，坐标换成 0–1000 归一化整数 `[x1, y1, x2, y2]`。
- `has_dynamic_target` 行的目标车若不在真值车辆列表，用行内 gold 框补入为候选。
- gold 映射：每个 gold 框必须与唯一一个候选 IoU ≥ 0.9；不满足的行记 `CANDIDATE_MAP_FAIL`、不推理、单列计数报告。
- 候选为 0 的行（含原 4 行 G5 零候选行）记 `ZERO_CANDIDATES`、不推理、按组单列计数报告（修订 1）；若某 gold 目标本身被判完全遮挡而映射失败，记 `CANDIDATE_MAP_FAIL` 并在报告中列出 row_id。
- 编号：1…N，顺序按以 `sha256(row_id)` 为种子的确定性乱序（避免左到右位置先验）；两种呈现、两种精度用同一编号。

## 4. 两种呈现（测前固定，正式运行中不得改）

- **P-draw**：在原图上画全部候选框（线宽 2 px，单一高对比色），框左上角内侧贴编号标签（黑底白字，标签越界时移入画面内）；提示里不给坐标。
- **P-text**：原图不改；提示里逐行列出 `<编号>: [x1, y1, x2, y2]`（0–1000 坐标）。

提示模板（英文，两种呈现只差括号内一句），`temperature=0`、`max_tokens=64`：

```
The image contains N candidate vehicles, numbered 1 to N {P-draw: "with numbered boxes drawn on the image" | P-text: "with boxes listed below as [x1, y1, x2, y2] in 0-1000 image coordinates"}.
{P-text only: candidate list lines}
Description: "<surface>"
Which candidate(s) match the description? Reply with JSON only:
{"status": "unique" | "ambiguous" | "none", "ids": [...]}
Use "unique" with exactly one id if one candidate matches, "ambiguous" with all matching ids if more than one matches, and "none" with [] if no candidate matches.
```

## 5. 两种精度

- **Q4**：板上现成 `Qwen3VL-2B-Instruct-Q4_K_M.gguf`。
- **BF16**：mini 上用板上同树 `convert_hf_to_gguf.py` + `gguf-py`（回传至 mini）与 `.venv-language` 把基座 HF 权重的语言模型部分转成 `--outtype bf16` GGUF；板上 `llama-server` 加载失败时只许改转 `f16` 一次，再失败即停（信封第 9 项）。转换脚本导入 sentencepiece：按修订 1 从 PyPI 下载安装 `sentencepiece` 1 次（Python 3.12、macOS arm64 wheel，≤ 10 MB），`--target` 装进本次工作目录、经 `PYTHONPATH` 只供转换脚本使用，不动 `.venv-language`；依赖链出现其他包、或转换还要求其他缺失依赖即停回报。
- 两种精度共用板上现成 `mmproj-…-F16.gguf`（视觉编码器相同），差别只在语言模型权重；BF16 臂因此只上传语言模型 GGUF（约 3.4 GB）。

## 6. 读数（每个 精度 × 呈现 各一份）

- 按组成功率：unique 行 = `status` 为 unique 且 `ids` = [gold 编号]；ambiguous 行严格 = `status` 为 ambiguous 且 `ids` 集合 = gold 集合，宽松 = `status` 为 ambiguous；none 行 = `status` 为 none。解析失败单列。
- 单目标行（G1、G2、G1t、G2t、G4）按：现行 S/M/L × 贴边（gold 任一坐标 ≤ 3 或 ≥ 997）；可见比例四档（1 / 0.75–1 / 0.5–0.75 / 0.25–0.5）；远处小目标子集（不贴边且可见短边 < 32 px）带 Wilson 95% 区间；候选数分档（1–2 / 3–5 / 6–10 / > 10）。
- 失败构成：答 none、选到同类别其他车、选到不同类别车、答 ambiguous、解析失败。
- 时延：每次请求墙钟 p50 / p90 / 最大；板上峰值内存与 swap。
- 对照列：同一行 C2 接口 A 成功（IoU ≥ 0.5）——不同任务，只作参照，不做差值检验。

## 7. 执行顺序、目录与停止条件

- **派发 1（准备，零模型运行）**：写脚本；生成 P-draw 图与 P-text 提示；BF16 转换；SSH 上传 BF16 GGUF 与 P-draw 图到板上新目录 `~/eng-jet/vlm-diag-b1-<UTC 时间戳>/` 并逐文件核 sha；空跑核对（构造全部 2,204 条请求但不发送，核计数、候选映射、提示长度）。不启动 `llama-server`、不加载模型。
- **派发 2（正式板上运行）**：开跑前核板上无其他 `llama-server`/GPU 作业（有即停）；每种精度先冒烟 ≤ 20 行 × 2 呈现，按实测时延推算全量墙钟，推算使板上推理阶段超 3.5 h 即停回报；通过后跑全量，结果回传 mini。
- mini 输出：仓库外 `~/vlm-diag/COORD-VLM-DIAG-2026-10-10/stage1-<UTC 时间戳>/`；板上不动 `~/eng-jet/` 既有文件。
- 墙钟 3.5 h 的计量范围：~~板上推理阶段，从首次启动 `llama-server` 到最后一次查询返回~~（原 supervisor 读法）→ 修订 2 起为**实际推理时间**（各精度从启动 `llama-server` 到该精度最后一次查询返回的时段累加，空闲不计）；准备派发另设软限 60 min。
- 任何一维即将越界、OOM、板上可用内存 < 0.5 GB、或任一步与本文不符 → 立即停下回报，不自行变通。
- 结果只作诊断；摘要由 supervisor 照录回本目录。

## 修订 1（2026-10-11，依账本同日「用户按推荐追加 VLM-DIAG:B:1」条）

- §3 候选去掉完全被遮挡的车；候选为 0 的行不推理、单列（`ZERO_CANDIDATES`）。
- §5 sentencepiece 允许下载安装 1 次，只装进工作目录。
- 派发 1 的已有产出（`~/vlm-diag/COORD-VLM-DIAG-2026-10-10/stage1-20261011T004632Z/`）中候选、P-draw 图、请求清单按修订 1 重新生成；脚本可复用，转换源码已回传、不再回传。§4 两种呈现与提示模板、§6 读数不变（§6「候选数分档」按修订后候选数）。

## 修订 2（2026-10-11，依账本同日「用户准清 BF16 假阳性停止标记重跑，并定墙钟按实际推理时间计」条）

- BF16 首次启动被 runner `OTHER_JOBS_PRESENT` 假阳性拦停（启动命令行含 `llama-server` 字样）；准许一次性清板上 `state.json` 的 `stop_reason` 与 `other_jobs`（先备份为 `state.pre-rerun.json`），runner 与参数不改。
- §7 墙钟改按实际推理时间；执行上 BF16 重启前把 `first_server_start_unix` 置为「重启时刻 − 1,224.1 s」（Q4 已用）。启动与轮询命令行不得含 `llama`、`runner` 字样（runner 的其他作业检测按命令行匹配）。
