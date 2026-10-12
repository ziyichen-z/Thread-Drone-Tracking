# OFFLINE-PROBE-2026-09-12 — 5060 笔记本 agent 对零样本探针结果的只读复核（非权威预筛）

> 代录说明：以下为用户在 5060 笔记本上运行的复核 agent 所写 `review.md` 的逐字副本
> （原件 sha256 `13ce5e9fc850dfec…`，位于 T7 `TDT-PROBE-DATA-2026-09-11-finish/probe/outputs/qwen3vl-2b-review-package-20260912/`）。
> 它不是复核角色的 verdict，没有 work ID，不改变任何门；对应的结果代录见
> `docs/unity-test-log.md` → **UT-OFFLINE-PROBE-2026-09-12**。文内相对链接指向 T7 上的原目录，仓库内不存在。

---

# Qwen3-VL-2B 结果复核（2026-09-12）

复核对象：`probe/outputs/qwen3vl-2b-default-20260912/`，405 行、279 帧。坐标换算与本批输入尺寸通过；现有 404 个可解析框未发生静默坏框。发现解析器缺少语义校验，以及 G3 指标没有实现说明中的“任一同类车命中”。本次只做 CPU 离线复核和处理器复现，没有加载模型权重、重新生成预测或修改原脚本/原结果。

## 发现及影响

### [P2] 坏框可能静默通过有效性标记

位置：[run_qwen3vl_2b.py:112](source-snapshots/run_qwen3vl_2b.py)，调用位置 256–266 行。

`invalid_output` 只检查 JSON 语法及顶层是否为字典。后续归一化失败不会反写这个标记。离线调用原函数已复现：

| 输入 | 当前行为 |
|---|---|
| `{}`、长度非 4、非数字、NaN | 返回无框，但 `invalid_output=false` |
| 反向角点 | 接受，后续 IoU 变为 0 |
| 越界坐标 `[-20,0,1200,1000]` | 静默裁剪成 `[0,0,1,1]` |
| 布尔坐标 `true` | 当作数字 1 接受 |
| `ambiguous=true, candidates=[]` | 会计为报告歧义，不校验候选 |

**实际影响：本批没有触发上述静默坏框。**404 条均为有限数值、范围内且角点有序的合法框；其余 1 条 JSON 失败已正确标记无效（1/405=0.247%）。显式 `bbox_2d:null` 应保留为合法“未找到”，并与缺失字段、坏框区分。

建议解析后统一做 schema/数值/范围/角点顺序校验，返回状态与错误原因；越界先报告，再决定是否另存裁剪版本。歧义候选也应校验。候选格式不合规时不要靠修补 JSON 把当前坏输出升级为成功。

### [P2] G3 单框只比指定 gold，漏记命中其他同类车辆

位置：[run_qwen3vl_2b.py:261](source-snapshots/run_qwen3vl_2b.py)。`frame_by_path` 在 189 行建立后未使用，因此未读取候选框进行匹配。这与 [探针说明](source-snapshots/probe-README.md) 的判定要求不符。

保持 IoU≥0.5，离线对同帧同类、非 phantom 且有框的 referent/distractor 取最大 IoU，结果如下。无效输出留在分母，计未命中。

| G3 范围 | 行数 | 指定 gold 命中（原指标） | 任一同类命中（含 distractor） | 仅任一 OK 同类命中 |
|---|---:|---:|---:|---:|
| 全部 | 60 | 24（40.0%） | 40（66.7%） | 37（61.7%） |
| 严格歧义，same_class_visible≥2 | 23 | 6 | 19 | 19 |
| 非严格，same_class_visible<2 | 37 | 18 | 21 | 18 |

有 16 行原先未命中指定 gold，但命中了另一辆同类车。应把这列作为独立诊断指标保存；它不代表正确报告了歧义，也不能与 G1/G2/G4 的唯一目标 Success 混为一谈。

现有合法输出的 `ambiguous:true` 确实为 0（严格组也是 0/23）。但“模型完全没有尝试输出多目标”不成立：唯一失败行 `G3_AMBIG-0299` 输出了多个对象。该行不能算成功报告或完整候选列表。

## 坐标约定

- gold：左上角原点，x 向右、y 向下，归一化 `[x,y,w,h]`。参考 `project_boxes.py:87`、`:194`；405 行 gold 均与清单中目标候选框一致。
- 预测：`[x1,y1,x2,y2] / 1000`。Qwen 官方技术报告 §3.2.4 明确使用 [0,1000] 归一化坐标：[技术报告](https://arxiv.org/html/2511.21631v2#S3.SS2.SSS4)。无需再除以 640/480，也无需翻转 y 轴。
- 当前 `_xywh_to_xyxy` 与 IoU 实现正确。独立公式重算的每条 IoU、Success、12 个组层汇总与原文件一致，浮点比较容差 1e-12。
- gold 是世界 AABB 投影并裁到画幅的框，不能把它解释成人工可见部分紧框。
- prompt 没有明确写原点、轴方向和 0–1000 范围；建议未来版本显式写明并记录 prompt 哈希。此项是可复现性加固，本次没有发现尺度错误证据。

## 处理器是否缩放

使用现有环境 transformers 5.17.0，离线加载原 run 记录的本地 revision `89644892e4d85e24eaac8bacfd4f463576704203` 的 AutoProcessor，按原 `apply_chat_template` 路径复现一个代表帧及原 prompt。

| 项目 | 实测/配置 |
|---|---|
| 全部 279 张输入尺寸 | 640×480 |
| image processor 类 | Qwen2VLImageProcessor（Qwen3 配置复用此实现） |
| do_resize | true |
| patch_size / merge_size | 16 / 2，尺寸对齐因子 32 |
| 像素面积下限/上限 | 65,536 / 16,777,216 |
| image_grid_thw | `[1,30,40]` |
| 实际空间尺寸 | width=40×16=640，height=30×16=480 |
| patch 数 / 合并后视觉 token | 1200 / 300 |
| 像素值处理 | rescale=1/255，mean/std=0.5/0.5，映射到约 [-1,1] |

**自动 resize 开关开启，但本批尺寸没有变化。**两个边长本来就是 32 的倍数，面积也在阈值内。所查 `_preprocess` 图像路径没有空间 crop 或 letterbox padding；patchify 只是分块并组织张量。像素强度缩放与几何坐标缩放是两回事。

边界：历史输出没有记录 image_grid_thw / 处理器配置哈希，本结论来自当前同版本、同缓存 revision 的离线复现，不能替代不存在的历史逐行 trace。建议之后保存原尺寸、实际尺寸、grid、视觉 token 数、处理器配置与代码版本。

## 输出解析与截断

全部 405 条原始输出都带 Markdown fence。当前解析器有意去掉 fence；404 条成功读取，1 条失败。因此原无效率是“容忍 fence 后的解析无效率”，不能称为严格 JSON-only 遵循率。

唯一失败行是 predictions.jsonl 第 299 行，`G3_AMBIG-0299`：多个 JSON 对象直接以逗号相连、没有合法外层数组/候选对象，最后还停在未闭合的 label 字符串。已保存 `invalid_output=true`、`parsed=null`、`iou=null`、`success=false`，没有被静默计成功。

用同 revision tokenizer 对保存的 raw_output 重新分词长度为 128，与脚本默认 `max_new_tokens=128` 相同，强烈提示触及长度上限；但原 env 未存生成参数，预测未存原 token IDs、生成长度和 finish_reason，不能完全证明当时的停止原因。即使放宽 token 上限，多个对象直接拼接的问题仍需 schema 约束处理。

建议未来记录 JSON 错误类型/位置、schema_error、生成 token 数、末尾 token/EOS、可能截断标记及 max_new_tokens；汇总增加 invalid/error/truncated 数，明确 mean IoU 仅对有 IoU 的行求均值。当前 G3/M 的 mean IoU 分母为 23，而 Success 分母为 24。

## 校验范围与复现

已核对清单 sha256 与 env/summary 一致；405 个 row_id 顺序完全匹配、无漏行重复；279 个图像的 sha256、文件长度、尺寸及 JPEG 结构通过；没有行级 runtime exception。本次未校验整包其余未用文件。最初 smoke 目录只有空 predictions 且无 summary，是不完整运行；smoke-r2 有一条输出，正式结论以上述 405 行 default run 为准。

证据：[evidence.json](evidence.json)。含输入文件指纹、解析器反例、处理器配置及源码指纹、失败原文、G3 每行补算结果。

复现脚本：[audit.py](audit.py)。在工作区根运行 `py -3.13 probe/outputs/qwen3vl-2b-review-package-20260912/audit.py`。脚本读取原结果，以断言核验本次发现，覆盖本目录 evidence.json，不执行模型推理。
