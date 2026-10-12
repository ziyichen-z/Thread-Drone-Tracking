# P1-SCENE-006 batch 1c — 正式 P3 采集证据（`C_1c`）

Work ID: `P1-SCENE-006`（amendment 1 revision 5，batch 1c）
日期: 2026-08-03
角色: 实现（implementation）
依据: amendment §25 BC-B1C-1–5 + §5.6 ④；复核 round 4
`PASS_WITH_NOTES` on `C_tool′ = e7213e5`
（`docs/reviews/P1-SCENE-006.md`）；工具阶段证据见
`docs/evidence/P1-SCENE-006-batch1c-tool.md`

## 1. 采集身份（§5.6 ④）

- 采集命令（单次 headless Edit Mode，detached HEAD 恰为 `e7213e5`）：

```bash
git checkout e7213e5   # git status --porcelain 为空
…/Unity -batchmode -nographics -projectPath ~/TetheredDroneTracking \
  -executeMethod TetheredTracking.Scene006.Scene006FinalistGenerator.RunBatch1c \
  -quit -logFile runtime/test-results/p1-scene-006-batch1c.log
```

- 工件 `docs/evidence/P1-SCENE-006-p3-finalist.json` 记录：
  `capture_commit = tool_commit = e7213e5858e76c2556ed55b4836500ba18cf5a56`，
  采集前 porcelain 为空；场景 `.unity` 文件采集前后 SHA-256 相同
  （`dec58698…0c9bf`），`scene_saved = false`；
  `scene_state_sha256 = 75b84083…` 与 batch-1b P1 采集的场景状态哈希
  一致（场景重建链复现已复核状态）。
- 输入绑定：P1/P2 族 B 工件按内容 SHA-256 记录在 `selection` 节；
  决赛 trace 绑定 `trace-B-197.0-30.0.json`（`46036a6c…`，重生成逐位
  一致）。
- 历史拓扑（复核 F15(b) 流程注记）：本提交从 detached `e7213e5` 产生，
  与之后的三笔 docs 提交（`9245601`、`1f5b9f2`、`ae8091d`）分岔；
  汇合方案交接受角色裁定，`capture HEAD = tool commit` 保持不变。

## 2. 结果：`P3_OK`

- **选择（§5.4 冻结评分，三格全排序）**：
  `(197,30) h16 vfov40` score `0.0846560` > `(195,30) h20 vfov40`
  `0.0423282` > `(197,30) h16 vfov35` `0.0`（L_point 贴 0.50 带边）。
  **决赛点 = `(197,30), h=16, vfov=40`**。
- **BC-B1C-2 支撑核对**：3/3 入带格 `legal=true` 且支撑恰好唯一命中
  `Natures_Grass Tile Small`（草地 allowlist）；无 F6 形态。
- **T5 复核性重跑**：与 P1 高度-16 报告逐候选逐项相同
  （`t5_recheck.equal = true`，合同哈希 `8f72d80f…` 一致）。
- **T4（字面 §5.4.4 证书，绑定该草地实例）**：`PASS`——
  `G = 0.5055555701255798 ≥ 0.05`；1039 站点中 183 持证
  （机体拒 478 / 系留拒 842 / 路径拒 0）；最佳站点 `C_station = 1.0`，
  `C_hold` 取 P2 格 `c_geom = 0.4944444…`。
- **T6**：`PASS`——`k* = 2 ≤ 10`；提示帧 min(w,h)
  `143.229 px ≥` P2 域中位 `63.257 px`。
- checker（规范模块入口）
  `python3 -m tools.scene006_candidate_check check <p3> --p1-path … --p2-path …`
  **OK**。

与复核 round 4 探针观测（同 finalist、同 G、同 k*）一致，无待归因分歧；
探针数字不作证据，本工件独立成立。

## 3. 边界符合性

零 `config/`/场景字节、零 Play、零 scenario/session/run ID；未新增网格
格、未改分数/阈值/tie-break、未顺延次名；batch 2 保持
`BLOCKED_USER_GO`，**`P3_OK` 不是 batch-2 GO**。
族 A 的 `BLOCKED_GEOMETRY_INFEASIBLE` 处分维持 batch-1b 记录。

## 4. 停点与复核范围

`C_1c` = 本文件 + `P1-SCENE-006-p3-finalist.json` 所在提交（hash 见
状态板/git log）。写入审计端点：`--base 77595c8`；独立复核 diff 端点
`77595c8..C_1c`。重点复核项：工件内 §5.4 排序表逐格重算、T4 证书逐
站点抽验（字面头段修剪、绑定实例、机体/系留分类）、T6 窗口逐样本、
身份字段与场景零写入证明。

## 5. Unity 用例

batch 1c 全部为 Edit Mode 离线执行，零 Play、零采集会话：无用户 Unity
运行用例。复现：按 §1 的命令在干净 `e7213e5` 上重跑并以 checker 校验。
