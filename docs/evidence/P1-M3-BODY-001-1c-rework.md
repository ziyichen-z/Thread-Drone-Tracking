# P1-M3-BODY-001 1c 返工批次（Acceptance round 11 §B 六条）

批次性质：round 11 `REVISION_REQUESTED_1C_PREFLIGHT` 的返工——落地
run-bound M3 离线真值载体与最小分析链、修订 arm A trial 1 操作单。
**零正式 Play、零 trial/run ID、零运行指标、零配额。**

## 1. 六条 binding 要求落点

| round 11 §B | 落点 |
|---|---|
| 1 臂 A wiring | 操作单 §1/§4：臂 A 正式 CLI 改 `--body-policy hold` + 冻结 body planner config + 主环线 scenario config；两臂同一 estimator、同一 `_body_step`/run-log 路径，差异仅 planner 实例（臂 B 只切 `threshold`）；初始化一次性 `hold_body()` 保留（`initialize()` 未触碰） |
| 2 真值载体 | `CoverageEvaluator` 新增 `M3BodyTruthRecord`（`p1-m3-body-truth/v1`）+ `WriteM3BodyTruth`：逐帧 append `runtime/m3_body_truth.jsonl`，每次 Play `FileMode.Create` 截断（writer 随组件生灭，一 Play 一文件）；逐帧含目标世界 `(x,y,z)`、几何可见性、truth box/中心、云台/系留饱和、投影 aspect；非有限值 throw fail-closed；门控 `M3BodyTruthAllowed` = 仅普通 run 的普通帧（任何 active 实验或非 Ordinary qualification disposition 零输出，RATE/qualification 协议产物不变） |
| 3 可完整复算 | `tools/analyze_m3_body.py`：单 trial 复算 H1 整圈 `C_geom`、窗内 `C_track|geom`/`C_track`、`C_quality` 三分量（里程加权）、中心误差 max/p90、云台/系留饱和占比（窗+整圈）、body-motion effort、planner 切换次数、机体轨迹（v3 元数据相机位置）、NEES/NIS、`σ_px` 残差对照；`--compare` 模式按 BC-BODY1-14 产出 H2 三档 verdict 与臂 A 逐 trial H1 表；两臂同一冻结可见弧、同一里程样本规则 |
| 4 两个边界分开 | 里程投影（闭合折线最近点）+ 解卷绕：窗 `[0, 62.5 m]` 只结束窗内指标；整圈 = 未卷绕里程 `< perimeter` 的帧集，首次闭环机械划定；`final_mileage ∉ [P, 2P)` 即 `trial_invalid_no_single_loop` fail-closed；`--planned-duration-s 130.0` 仅 watchdog |
| 5 旧现场 fail closed | 操作单 §2 逐项隔离清单（frames/metrics/truth/override/command 五组，移动不删除，逐项记录）；`analyze_m3_body.py` 机械 receipt：run_id、scenario/hash、body config hash、首末 frame、样本数、frames.jsonl/manifest/truth/metrics.final 四文件 SHA-256 + 帧元数据清单哈希；缺件/重复/不一致全部命名 fail-closed，分析文件 create-once |
| 6 返工停点 | 本批次完成后回 Acceptance §4.3.1 停点确认（含写入归因），再交独立 Review；verdict 消费前零正式 Play |

## 2. 改动清单

| 文件 | 内容 |
|---|---|
| `Assets/TetheredTracking/Scripts/CoverageEvaluator.cs` | `M3BodyTruthRecord` + `M3BodyTruthFileName` + `WriteM3BodyTruth` + `BuildM3BodyTruthRecord`（internal static，可测）+ `M3BodyTruthAllowed` 门控 + writer 生命周期（OnDestroy/OnApplicationQuit）；`VisibilitySnapshot` 由 private 改 internal（嵌套类型可访问性，供 internal 方法与测试使用；零行为变化） |
| `Assets/TetheredTracking/Tests/EditMode/M3BodyTruthEditModeTests.cs`（+`.meta`） | 4 个聚焦测试：记录键/中心像素/时钟恒量与 JSON 无 NaN；null box → -1 约定；非有限 throw；门控谓词普通/非普通帧 |
| `tools/analyze_m3_body.py` | 单 trial 绑定+复算（`--run-id`）与两臂比较（`--compare`）；全部 fail-closed 命名错误；不写 stdout 以外副作用，分析文件 create-once |
| `tests/test_analyze_m3_body.py` | 9 个测试：里程/解卷绕/加权中位数单元；合成整圈 trial 集成（全量数值断言）；8 个 fail-closed 用例；H2 三档 verdict + 冻结 5/臂；真值单向流动机械检查（`controller/` 零引用 `m3_body_truth`） |
| `docs/evidence/P1-M3-BODY-001-1c-preflight.md` | 操作单 revision 2（§B.1/§B.4/§B.5 落实；CLI、隔离清单、分析步骤、三分支） |

真值单向流动：真值只在 `CoverageEvaluator` 内产生、只写
`m3_body_truth.jsonl`；`controller/` 全库零引用该文件（机械测试锁定）；
v3 传感器元数据键零新增（载体不改 `SensorFrameWriter`）。

## 3. 实际运行的命令与结果

```bash
.venv-track/bin/python -m unittest tests.test_analyze_m3_body   # 9/9 OK
.venv-track/bin/python -m unittest discover -s tests            # 433 ran / 1 既有失败
python3 tools/build_m3_corridor.py --check                      # exit 0，779 棱柱哈希不变
python3 tools/check_scene_body_margin.py                        # exit 0，pins 字节不变
# Unity Edit Mode（batchmode，6000.4.1f1，本批次工作树）：
#   runtime/test-results/p1-m3-body-001-1c-rework-editmode.xml
#   testcasecount="267" result="Passed" failed="0"（263 既有 + 4 新增）
```

- 全套 433/1：唯一失败是已登记的既有 infra 债务 `test_check_docs.py`
  （`test_compliant_minimal_status_passes`，与 `61ea20b` 以来各批次同一
  失败，需用户授权的协调批次；本批次未触碰该两文件）。
- Edit Mode 首轮 266/267 的唯一失败是本批次新测试自身的 JSON 空格断言
  （`JsonUtility.ToJson` 输出紧凑格式），已就地修正断言并复跑
  **267/267**；实现代码零改动。

## 4. 未验证项与已知限制

- 真值载体的 Play 行为（截断、逐帧 append、OnDestroy 关闭）由代码审查
  与 Edit Mode 单测覆盖；首次真实 Play 产物由 trial 1 的绑定工具机械
  核验（这正是 §B.5 的 receipt 设计）。
- `WriteM3BodyTruth` 门控在 active RATE/qualification 实验帧零输出；
  RATE-002/003 与 DETECT 协议产物路径零改动（未触碰其槽位机械）。
- `--compare` 的 H1 只逐 trial 报告臂 A 值与在区间判定（设计未冻结跨
  trial 聚合，不发明）；H2 判定式按 BC-BODY1-14 (a)(b)(c) 逐字。

## 5. 给复核角色的复核范围

1. `CoverageEvaluator.cs` 新载体：记录字段与既有 `VisibilitySnapshot`
   语义逐键对映；截断语义（`FileMode.Create` + 组件生命周期）是否恰为
   「一 Play 一文件」；门控是否在 RATE/qualification 帧真零输出；非有限
   guard 完备性；`VisibilitySnapshot` internal 化无封装外溢。
2. 真值单向流动：全库确认 tracker/estimator/planner/元数据路径不读
   `m3_body_truth.jsonl`；v3 元数据键零新增。
3. `tools/analyze_m3_body.py`：里程投影/解卷绕数学；窗与整圈两个定义域
   的机械划定；`[P, 2P)` 恰好一圈判据；receipt 绑定字段是否覆盖 round
   11 §B.5 逐项；fail-closed 路径是否真零写入。
4. H2 三档与 BC-BODY1-14 符号约定逐字对读；`C_quality` 里程加权与
   BC-BODY1-5 对读。
5. 测试是否覆盖声明行为（合成 trial 的数值断言是否独立可复算）。
