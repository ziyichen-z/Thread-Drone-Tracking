# 回放测试设计 R-1…R-5、导出规格与额度申请草案（2026-10-09，supervisor 会话）

性质：按 `handoff-next-supervisor-2026-10-09.md` 写的测试设计。**不是提案、不是证据、不是授权。** 文中数值一律是「占位」或「暂定（n=…）」。本会话零消耗：没有加载模型、没有 Play、没有连板，只读了 10-08 诊断原件的 JSON/JSONL 与代码；第 1 节的几处算术（位姿单应作用在真值框上）只用了记录文件与 `controller/pose_gmc.py` 的纯函数，没有用任何模型输出，结论只作「待回放确认的假设」。

基线：骨架 v3（`architecture-skeleton-v3-2026-10-09.md`）+ v3.1 修订清单（`v3.1-revision-items-2026-10-09.md`）。本文对它们的追加写在第 7 节，不改 v3/v3.1 正文。

---

## 1. 输入核清：10-08 诊断原件里真正有什么

诊断根 `outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/20261008T213653Z/`（本机 Air，play 72 MB、segments 1 MB）。跑这次 Play 的代码 HEAD = `c4973d0`（运行目录 manifest 的 `git_head`）；`controller/` 从那时到现在没有改动。

| 项 | 事实 |
|---|---|
| 帧 | `play/diag-loop2-214005/frames/frame_<10位>.jpg|.json`，**0–828 连续共 829 帧**，无缺号；640×480，fx=fy=415.692，cx 320，cy 240；帧间隔 0.2 s |
| 真值 | `m3_body_truth.jsonl` 829 行，逐帧有目标世界坐标、真值框（左上原点归一化 xywh，与常驻框同一约定）、可见性。**目标在画面内只有两段：0–68 与 515–602**（共约 155 帧），其余 672 帧目标不在画面 |
| 目标运动 | 2.0 m/s 沿回环，每约 120 帧有 9 帧停顿 |
| 机身 | 几乎不动（只有 383–385 帧位置变化 ≤0.29 m） |
| 常驻快层 | `segments/.../frames.jsonl` 793 行（帧 2–794），只有指针框与状态；17 帧跳过发布、无积压；计算时延 p50 29 ms / p95 88 ms |
| 指定与绑定 | 会话流 4 次绑定：k=186→头帧 243（库 ID 1）、340→379（ID 2）、534→557（ID 11）、691→717（ID 15）。**只有第 3 次绑定的是真值目标（红车）**；第 1、2、4 次绑定的车在真值文件里没有记录（真值只跟一辆车） |
| 红车丢失 | 557 绑定 → 558、559 指针框与真值 IoU 0.99/0.97 → 560 降到 0.72 → **561 起 LOST**（`bound_track_unmatched`）→ 592 起 `bound_track_removed`（正好 30 帧 = `track_buffer`）。目标在 563–600 帧仍完整在画面内、相机已静止，指针始终没回来 |

### 1.1 转向事件（本节是新发现，影响 R-2 与 ω_step 口径）

用相邻帧四元数算整段相对旋转，并分解出绕光轴的分量（图像滚转）：

| 绑定后转向 | 帧 | 每帧总旋转 | 其中绕光轴（图像滚转） | 结局 |
|---|---|---|---|---|
| 第 1 次 | 244–248 | 13.8°、6.1°、2.7°、1.5° | 绝大部分 | 未丢 |
| 第 2 次 | 381–390 | 38.0°、30.1°、1.2°、1.0°、20.6°、13.3°、8.8°、6.1°、4.1° | 绝大部分，符号交替（疑似偏航往复） | 未丢 |
| 第 3 次（红车） | 559–562 | 22.4°、24.2°、18.0° | 21.9°、23.9°、17.8° | **561 丢失** |
| 第 4 次 | 719–728 | 每帧 17–25°，连续 6 帧以上 | 绝大部分 | 未丢 |

原因：相机几乎垂直向下（`camera_forward_world` 的 y 分量 −0.977…−0.994），云台偏航在图像里几乎全部表现为**绕画面中心的旋转**。交接与 v3 里说的「转向 5.17°」是前向量夹角，严重低估了图像实际变化；v3 §9 的 ω_step 占位「3°/帧」与实测 18–38°/帧 不在一个量级。

### 1.2 10-08 现场已经开着位姿补偿（修正交接前提）

常驻插件 `DetAssocTracker` 缺省 `gmc_source="pose"`（`controller/det_assoc_tracker.py:280`，`c4973d0` 同行），`language_loop.py:2290` 建常驻实例时不改它。所以 10-08 的丢失**发生在位姿补偿已生效的情况下**，v3.1 C4「位姿补偿生效后转向型断裂应消失」的前提不成立。

把记录位姿算出的单应（`pose_homography`，`controller/pose_gmc.py`）作用到上一帧真值框，再与下一帧真值框比（只用记录文件，不涉及模型）：

| 帧对 | 不补偿 IoU | 现行补偿（四角外接框）IoU | 只移中心、保留宽高 IoU | 补偿后中心残差（px） |
|---|---|---|---|---|
| 557→558 | 0.78 | 0.79 | 0.79 | (4.7, −4.6) |
| 559→560 | 0.14 | 0.51 | 0.70 | (3.2, −5.9) |
| 560→561 | 0.09 | **0.30** | 0.50 | (−0.3, −6.4) |
| 561→562 | 0.13 | 0.79 | 0.57 | (−2.1, −6.6) |

读法（假设，待回放确认）：位姿与图像在时间上对得上，中心补偿准确（残差 ≈ 目标自身每帧 5–7 px 的运动）；问题在**框形**。红车在 559 帧斜着（外接框 77×75），图像一转，真车外接框变成 61×79 → 36×72，而现行补偿把四个角旋转后取外接框，得到 97×97、88×97 这样膨胀的预测框。560→561 即使检测完美 IoU 也只有 0.30，正好在 BoT-SORT 首轮关联门（`match_thresh` 0.7 即 IoU ≥ 0.3，且 `fuse_score` 再乘置信度）的边上。随后 561 的检测大概率被开成新轨迹、562 起以新 ID 激活，库 ID 11 留在 lost 池里，30 帧后被删。第 1、2、4 次转向没丢，可能与被跟车在画面中的朝向（接近轴对齐时外接框不膨胀）有关。两种补偿各有赢的帧，不能先验选一个——这正是 R-2 要测的。

---

## 2. 一次加载的执行形状

**一次 YOLO 加载、两遍推理、多臂零额外推理：**

1. **遍 A（原始帧）**：冻结检测器对 0–828 共 829 帧逐帧检测一次，缓存原始检测。
2. **遍 B（合成转向帧，§4.2）**：对选定基段做纯旋转变换后再检测，缓存原始检测。
3. **关联臂**：在缓存检测上重放关联器，不再推理。四个臂（只有 `optflow` 需要读图像）：

| 臂 | 含义 | 实现入口 |
|---|---|---|
| `none` | 不补偿 | `make_resident_associator(..., "none")` |
| `optflow` | 库原生稀疏光流 GMC | 同上 `"optflow"` |
| `pose-aabb` | 现行：四角外接框 + 中心雅可比（**须复现 10-08 在 561 丢失**） | 同上 `"pose"` |
| `pose-center` | 只移中心与速度、宽高不变（诊断臂，不是已接受方案） | 回放脚本内一个替换 `apply_pose_warp` 的局部函数，不改 `controller/` |

**复现门（先于一切读数）**：`pose-aabb` 臂在 534–600 段的指针轨迹（以 557 帧与常驻记录 IoU 最大的库轨迹为起点）须在 561 失配；558–560 的框与常驻记录逐帧 IoU ≥ 0.95（占位）。不满足即停，所有 R 读数作废并报差异（可能原因：17 帧跳过发布导致关联器看到的帧序不同、MPS 与现场设备的数值差）。

检测阈值：遍 A/B 以 `conf=0.01` 跑一次（同一次推理，不加帧），原始检测全部入缓存并带 `above_frozen_conf` 标志；关联臂只喂 `conf ≥ 0.25` 的那部分，与冻结规格一致（低分组在现行规格下恒为空，见 §5 Q4）。低分检测只供 R-2 区分「漏检」与「检到但关联不上」。

复用：检测缓存格式沿用 `tools/eng_det/evaluate.py` 的 `detect_frames`（gzip JSONL、头部带权重 sha/imgsz/device/conf，不一致即重算）；关联重放沿用 `tools/eng_acq/e2.py::replay_segment` 的写法（逐帧一次 `update`、`rows_from_library`、`ResidentCore.record`），再加 §3 的导出钩子。

---

## 3. 导出规格（落实 v3.1 §D）

全部写到 `outputs/replay/<run-id>/`（不入仓）。在线可用的量与只供离线评分的真值连接**分文件**：文件名以 `score-` 开头的才允许读真值（v3 不变量 6）。

| 文件 | 每行 | 字段 |
|---|---|---|
| `manifest.json` | 一份 | run_id、git HEAD 与 `git status --porcelain` 行数、输入清单 sha256（帧目录逐文件 sha 的汇总 sha、真值、权重 `d6a0d6a9…`、`config/det-assoc-v1.models.json`、冻结文件）、ultralytics/torch/opencv/numpy 版本、device、遍 A/B 帧数、合成参数与随机种子、各臂配置、起止时间、YOLO 加载次数 |
| `detections.jsonl.gz` | 一帧（含合成帧） | seq_id、frame_key、source_frame_id、synth_index（原始帧为 null）、dets：[det_index, box_norm xywh, conf, cls, above_frozen_conf]（**A8 原始检测**） |
| `tracks-<arm>.jsonl.gz` | 一臂一帧 | seq_id、frame_key、library_frame_id、gmc_source、gmc_matrix（2×3 或 3×3，未施加为 null）、rows：[track_id, state ∈ tracked/lost/unconfirmed, is_activated, box_norm（lost 为当帧预测框）, mean[8], covariance[8×8], matched_det_index（输出行末列 `idx`；无则 −1）, score_last, tracklet_len, start_frame]、removed_ids、silently_dropped_ids（`remove_duplicate_stracks` 吞掉的 ID，§5 Q3）、vlm_busy=false（**A7 占位列**） |
| `ground.jsonl.gz` | 一臂一帧一行轨迹 | frame_key、track_id、两种量测点（**A4**）：P_bottom = 框底中点射线 ∩ y=`ground_plane_y_m`；P_center = 框中心射线 ∩ y=h_c（h_c 占位 0.75 m）；各带 ray、distance、拒绝原因、`measurement_covariance_xz` 解析 R |
| `synthetic.jsonl` | 一合成帧 | 见 §4.2：seq_id、source_frame_id、累计旋转 (axis, angle_deg)、Q（3×3）、H_src→syn（3×3）、改写后位姿四字段、valid_fraction、填充与插值方式 |
| `score-truth-join.jsonl.gz` | 一臂一帧 | 目标轨迹判定（与真值框 IoU ≥ 0.5 的轨迹/检测）、真值框（合成帧为变换后外接框）、真值地面点 |
| `score-r1-survival.csv` | 一个起点 | arm、seq_id、t0、segment_end、first_failure_frame 或空、censored（**A13 首次失效与删失**）、stratum（静止/转向中） |
| `score-r2-turns.csv` | 一个转向事件 | 见 §4.3 |
| `score-r4-residuals.csv`、`score-r4-nis.csv` | 一帧 / 一窗 | 见 §4.4（**C1 时间平均 NIS**） |
| `score-r5-depth.csv` | 一次指定 | 见 §4.5 |
| `summary.json` | 一份 | 各参数暂定值、样本量、置信区间、复现门结果 |

体量估计：检测与轨迹全量约 50–150 MB；合成帧图像**不落盘**（由 `synthetic.jsonl` 参数确定性重建），只抽 40 张存 JPG 供人眼核对。

---

## 4. 逐项设计

### 4.1 R-1 预测可用时长 → T_pred（按 A13 生存界）

- 输入：真值段 0–68、515–602 的原始帧；遍 B 中基段为真值段的合成序列。
- 历史重建：对每臂、每个目标被观测（matched_det_index ≥ 0 且与真值 IoU ≥ 0.5）的帧 t0，从 `tracks-<arm>` 取该轨迹的 mean/covariance，用库 `KalmanFilterXYWH` 只预测不更新，逐帧施加同臂的补偿矩阵，得到 t0+d 的预测框。
- 失效定义：首次 d 使预测框与真值框 IoU < iou_pred（占位 0.3）。另报一个地面版本：冻结世界滤波（`config/p1-m3-body-001.json` 的 q_accel 8.378、σ_px 2.866、σ_att 1.0°、σ_y 0.05、初速 σ 2.0）只预测，预测点投回图像后落在真值框外即失效。
- 删失：真值段结束、目标出画、序列结束而未失效 → 右删失。
- 估计：Kaplan–Meier 得 S(d)；T_pred = 满足 S(d) 的 95% 下界 ≥ 1 − ε_pred 的最大 d（ε_pred 占位 0.1）。
- 输出表：arm × stratum × d 的 S(d)、下界、风险集大小。
- 样本量标注：起点高度自相关，**有效样本按独立段计**（真值段 2 段；合成序列按基起点计），写「暂定（n_起点=…，n_段=…）」。

### 4.2 合成转向帧（C2）

- 位姿约定与 `controller/pose_gmc.py` 相同：旋转矩阵列 = (right, up, forward)，K' = [[fx,0,cx],[0,−fy,cy],[0,0,1]]。
- 相机系内的旋转 Q（绕 forward 即图像滚转；绕 up 即横摆；绕 right 即俯仰）。合成帧基 M' = M·Q。源像素到合成像素：H_src→syn = K'·Qᵀ·K'⁻¹；`cv2.warpPerspective(src, H_src→syn, (640,480), INTER_LINEAR, BORDER_CONSTANT=0)`。
- 位姿改写：right/up/forward 写 M' 的三列；`camera_rotation_xyzw` 由 M' 按与 `rotation_matrix` 同一约定反解，**写出前用 `rotation_matrix` 重建并要求与 M' 逐元素差 < 1e-6**；位置、内参、时间不变；frame_key = `syn-<seq>-<j>`，带 source_frame_id。由此 `pose_homography(相邻合成帧)` 自动给出补偿所需的单应。
- 边界：无源像素处填 0，记 valid_fraction；真值框按四角变换取外接框，变换后在画面内面积 < 50% 记出画（删失）；与无效区重叠 > 30% 的检测标 `edge_artifact`，评分时单列。
- 旋转日程：每条序列 = 基段上连续帧；前 W 帧（占位 8）不变换供关联器热身（这几帧用遍 A 的检测，不另推理）；之后累计角 θ_j = min(ω·j, Θ)，转完保持 Θ。转向方向取「让被跟框趋向画面中心」与其反向各一，方向由 j0 帧的**检测框**决定，不读真值。
- 因子（全部占位）：
  - 滚转：ω ∈ {5, 10, 15, 20, 25}°/帧 × Θ ∈ {30°, 60°, 120°} × 正负 = 30 组；
  - 横摆/俯仰：ω ∈ {2, 5, 10}°/帧 × Θ ∈ {10°, 20°} × 四向 = 24 组；
  - 基起点：真值段 6 个 + 静止车段 6 个（第 1、2、4 次绑定的车；身份用「静止假设下地面点稳定」作**伪真值**，单列不与真值混算）；
  - 合计 54 × 12 = 648 条序列 × 每条变换 16 帧 ≈ 10,400 合成推理帧。
- 限制：纯绕光心旋转的单应与景深无关，**不存在视差**；视差只在光心有平移时出现（实测 560–562 平移 0，383–385 ≤ 0.29 m），所以 v3.1 C2「高物体有视差」应改为「云台转心与光心不重合时才有视差」。真实限制是：边缘无新内容、插值变软、没有运动模糊、只检验关联逻辑，不能替代闭环（同 C3）。

### 4.3 R-2 转向后恢复间隔与转向速率敏感度 → T_repair、ω_step

- 输入：遍 A 的 4 次真实转向（只有 559–562 有真值；另 3 次用伪真值）；遍 B 全部合成序列。
- 每个转向事件、每臂输出一行：arm、event、ω、Θ、方向、t0（转向前最后可靠观测帧）、id_survived（转向后被跟物理目标仍由原库 ID 持有）、break_frame、break_mechanism ∈ {检测漏检、检到但未关联、关联给他人、出画}、new_id_frame（物理目标被新 ID 激活的帧）、gap_detect（t0 到目标再被检出且连续 2 帧的帧数）、gap_assoc（t0 到目标再被某轨迹稳定持有的帧数）、censored。
- 机制判别靠 §3 的原始检测列与 `matched_det_index`：有与真值 IoU ≥ 0.5 的检测而原 ID 未匹配 = 「检到但未关联」；检测在低于 0.25 的区段 = 「低分漏检」。
- 估计：按臂 × ω 报断轨率（带 Wilson 区间）；T_repair 候选 = 「补偿后剩余断轨机制（C4）」的 gap_assoc 分布覆盖 p90 的值，但 n 小时只列原始值、不取分位；ω_step = 断轨率低于占位 5% 的最大 ω，**以图像滚转率而不是前向量夹角计**。
- 只回答「同样相机运动下哪种补偿与关联更好」（C3）；换转向策略后的效果必须回 Unity。
- 样本量：真实真值事件 n=1、伪真值 n=3；合成按基起点计 n=12。全部「暂定」。

### 4.4 R-4 NIS 一致性、尺寸残差、量测点残差 → g_motion、g_size、R_floor、瞄准点

- 输入：真值段原始帧上目标被检出的帧；合成真值序列另列。
- 量测点残差（A4、B8）：每帧两种量测点对真值地面点的残差，拆成沿视线（距离向）与横向分量；分别报**偏差（均值）与抖动（标准差）**；按俯角、目标朝向与视线夹角、是否在转向中分组，检查是否有随视角的系统偏差。真值地面点取真值文件的 `target_world_x/z_m`；**该点是车体中心还是车尾挂点未核**，结论前须核 `LoopTargetVehicle` 的枢轴（只读核 Unity 资源，不 Play）。
- h_c 拟合：另报使 P_center 平均残差为零的 h_c，作为诊断值，不直接采用。
- R_floor：经验残差协方差减去解析 R（像素、姿态、平面三项）的传播部分，取半正定投影；报 B8 要求的「三项是否独立」检验（残差与姿态变化率的相关）。
- NIS（C1）：冻结世界滤波在两种量测点上各跑一遍，逐步 NIS；窗口 N（占位 10 帧）内时间平均 ε̄，N·ε̄ 应落在 χ²(2N) 的 95% 区间；报窗口内比例与窗口数，注明自相关会使比例偏乐观。另报加 R_floor 后的同一检验。
- 尺寸残差：检测框 w、h 对上一帧 KF 预测的 log 比；静止与转向中分列；g_size 候选 = 静止段 |log 比| 的 p99（n < 100 时只报最大值）。转向中的分布单列，用于说明 §1.2 的框形问题。
- 瞄准点（A4）：两种量测点各算「若云台对准它，框中心偏离画面中心多少像素」，供 t_center 容差与 look_at 瞄准点选择。
- 样本量：真值帧约 150，独立段 2；全部「暂定」。

### 4.5 R-5 历史深度与字段是否够重建证据链

- 深度：用会话流算每次指定的 head − k：57、39、23、26 帧（186→243、340→379、534→557、691→717，主要是操作者确认用时）。所需深度 = (head − k) + N_adopt + 余量；再叠加时延剖面（板上单次 prompt 0.78 s + decode 0.9 s ≈ 9 帧，排队与人确认另加），报 128 帧深度在各剖面下的富余。
- 字段：按 v3 §7 证据链三步（k 帧解析、k→N 连续性、KF 从快照回放）逐步列所需字段，对照 §5 Q2/Q3 的现有历史字段，输出缺项表。已知缺：原始检测、KF 速度与协方差、补偿矩阵、未确认轨迹、出画被丢的 lost 框、去重吞掉的 ID。
- 回放验证：用 `tracks-pose-aabb` 重建每次指定在 k 帧的解析结果（复用纯函数 `select_track`），与会话流里的 `track_id` 逐次对比；不一致即报。

### 4.6 R-3（本次不做）

需要相似干扰车素材（场景改动项，用户待定）。现有画面里有其他车，可顺带算「对不相似干扰车的误收养」作为下界检查，标「代理，不是 R-3」。

---

## 5. 代码事实（只读核清）

子代理只读核对、supervisor 逐条抽核行号（标 ✓ 的已抽核）。ultralytics 路径 `.venv-yoloe/lib/python3.12/site-packages/ultralytics/`（下称 U）。

**Q1 BoT-SORT GMC 契约**
- 施加时机：库 `update` 先 KF 预测 `strack_pool`（tracked + lost），再 `_pre_first_associate`，再首轮关联（U/trackers/byte_tracker.py:281–285 ✓）。钩子对 `strack_pool` 与 `unconfirmed` 都施加；removed 不参与（byte_tracker.py:351–362）。
- 变换：2×3 矩阵的 R 扩成 `kron(eye(4), R)` 作用于 (x,y)、(w,h)、(vx,vy)、(vw,vh) 四对，平移只加到 (x,y)；协方差 R8·P·R8ᵀ（U/trackers/utils/stracks.py:166–173 ✓）。宽高被当二维向量旋转，物理上无意义。
- 状态：BoT-SORT 用 `KalmanFilterXYWH`（bot_sort.py:50、175–177）；lost 轨迹预测时 vw、vh 置 0（bot_sort.py:113–116）。
- sparseOptFlow：全帧取特征、不挖检测框，降采样 2，`estimateAffinePartial2D`（4 自由度相似变换）；首帧、匹配点不足或 RANSAC 失败都退化为单位阵（gmc.py:43、294、297–301、319–327）。纯旋转产生的透视项与随位置变化的缩放、剪切全部丢失。
- 替换入口：仓库已覆写 `_pre_first_associate`（`controller/det_assoc_tracker.py:200–231` ✓），`pose` 用 3×3 单应经 `apply_pose_warp`（161–197 ✓）：四角外接框定中心与宽高，中心雅可比转速度与位置/速度协方差块，宽高的协方差块不变。H 为 None（首帧或位姿异常）时不补偿、不回退光流（226–227 ✓）。**10-08 现场即此路径**（缺省 `gmc_source="pose"`，280 ✓；§1.2）。

**Q2 `designate` 拆分**（`controller/resident_core.py`）
- `designate` 482–510 ✓、`_level2` 512–558、`_finish` 560–568、`follow` 430–434 ✓。
- 纯解析：486–502（k、h 帧取历史与一级匹配 `select_track`）、505、509–510；`_level2` 除 549 外；`select_track` 195–227、`level2_mapping` 230–256 为纯函数。注意二级要跑 SOT 回放、受墙钟 `t_replay_s` 约束，不是确定性的，拆分时 runner 须作注入依赖。
- 须迁入写入步骤的副作用：485（分配 designation_id）、503（BOUND 时 `follow`）✓、506–507（`follow` 后写 coasting）✓、549（二级收养 `follow`）✓、566–567（写 `self.designation` 与事件）。顺序约束：先 `follow` 再写 coasting，否则 433 行 ✓ 会把刚写的 coasting 清掉。
- 历史：`self._history` 360 ✓，`record` 380–417 ✓，深度缺省 128（57 ✓）、下限 100；`HistoryEntry` 116–127 ✓ 含帧号、两种时间、相机位置、旋转、内参、库帧号、轨迹行、removed_ids、宽高；`TrackRow` 只有 track_id、box_norm、score、cls、state；`as_record` 导出时不含位姿、内参、宽高。

**Q3 lost 池预测框**
- 逐帧可读：`DetAssocTracker.step` 把 `lost_stracks` 每条的当帧预测框（已预测与补偿、未更新）写进历史，状态 LOST；removed_ids 取 update 前后集合差（`controller/det_assoc_tracker.py:434–439` ✓）。
- 失真与遗漏：lost 行的 score/cls 是最后一次匹配的旧值；框被裁剪到画内，退化或出画的 lost 框直接丢弃（resident_core.py:598–609），于是指针被判 REMOVED 而非 UNMATCHED；未确认轨迹不记录；`remove_duplicate_stracks` 静默删掉的 ID 不进 removed_ids；KF 速度与协方差、补偿矩阵、原始检测都不记录；tracked 框是 KF 后验不是检测框。

**Q4 `_step` 与原始检测**
- `_step` 用 `model.predict` 而非 `model.track`，`boxes = self._detect(image)` 之后原样 `tracker.update(boxes, image)`（`controller/det_assoc_tracker.py:344–355` ✓）。最小暴露点就是 353 行的 `boxes`。检测端 conf 已是 0.25，库内按 0.25/0.1 分高低分组时低分组恒为空。
- 库只输出已激活轨迹（byte_tracker.py:491 ✓）：非首帧新建的轨迹先进 unconfirmed，下一帧匹配上才激活，所以新出现的竞争者最早在第二个匹配帧才可见；库收到的第一帧例外，当帧激活。输出行末列 `idx` 指回原始检测下标，可据此把轨迹与原始检测连起来。

**现成脚本**：没有「冻结检测器对任意帧目录跑一遍再常驻回放」的通用脚本；最近的组合是 `tools/eng_det/evaluate.py::detect_frames`（检测缓存）+ `tools/eng_acq/e2.py::replay_segment`（常驻回放，pose/none 臂给空图，只有 optflow 读 JPG）。

---

## 6. 额度申请草案（只起草，未签；按账本信封格式）

```text
## 2026-10-?? COORD-RECHARTER-2026-10-09 — 用户签发离线回放额度 RECHARTER:REPLAY:1（代录会话：…）
- 用户原话（逐字）："…"
- 授权范围：按 docs/evidence/COORD-RECHARTER-2026-10-09/replay-test-design-2026-10-09.md §2–§4 做一次离线回放；
  诊断性质，不进任何证据链、不作任何门判定、不构成 P1-* 工作项的验收。
- 信封：
  - YOLO 权重加载 ≤ 1 次（outputs/eng-det/runs/run-1/weights/last.pt，sha256 d6a0d6a9…）；进程崩溃后的重载另需 1 次，计入同一上限 2 次
  - 推理帧 ≤ 12,000（原始 829 + 合成 ≤ 11,000；`conf=0.01` 单次推理）
  - Unity/Play = 0；板上动作（SSH、服务启动、查询）= 0；VLM/API 查询 = 0；云 GPU = 0
  - 下载 = 0（不装包、不拉权重；只用现有 venv）
  - 墙钟 ≤ 60 min（从加载到导出写完）
  - 执行机新增磁盘 ≤ 1 GB（outputs/replay/<run-id>/，不入仓）
  - 执行机：见下方待定 1
  - 越界任一维即停，报回用户；不得用剩余额度做本文以外的回放
```

签发前用户还需定的两件事（不是六项待决之一，是执行这份额度本身需要的）：

1. **执行机**。推荐 Mac mini：遵守 10-02 起「Air 只做需要 Unity 验证的任务」；需把诊断根的 play/segments（约 73 MB）与权重（5.5 MB）经局域网拷过去并核 sha，且 mini 上须有 ultralytics 8.4.104 + lap + opencv 的 venv（mini 现状本会话未核，UNKNOWN）。备选 Air：数据与 venv 都已就位（`.venv-yoloe` 已核有 ultralytics 8.4.104、lap 0.5.13、opencv 5.0、torch 2.13），但要用户对机器分工开一次例外。为何只能用户定：机器分工是用户 10-02 的规则。
2. **谁写回放脚本、放哪里**。supervisor 不写代码、不跑模型。推荐：由实现角色在一次被派发的会话里写脚本并执行，脚本放 `outputs/replay/<run-id>/scripts/`（不入仓，sha256 记进 manifest），摘要表由 supervisor 入仓到本目录；派发日志 work_id 用 `COORD-RECHARTER-2026-10-09`。备选：先立正式工作项走接受与复核，脚本进 `tools/`，可复用但多数轮流程开销。为何只能用户定：这是没有 Gate 行的诊断，是否给实现角色一次不挂工作项的派发，现行规则没有覆盖。

---

## 7. 对 v3.1 的追加（不改正文）

1. **ω_step 改口径**：以图像滚转率与横摆/俯仰率分别计，不用前向量夹角；近垂直向下的相机里，云台偏航几乎全是图像滚转（§1.1 实测 18–38°/帧）。v3 §9「占位 3°/帧」作废，改为 R-2 测出。
2. **C4 前提修正**：10-08 现场已开位姿补偿（§1.2）；断裂的候选机制是补偿后的框形（四角外接框在大滚转下膨胀）与 IoU 关联门的组合。快层一轮修正的重心因此从「加补偿」变为「补偿后的框形表示与关联门」。
3. **C2 措辞修正**：纯旋转单应与景深无关，没有视差；视差只来自光心平移。
4. **控制层新问题（C3 补充）**：近垂直向下时，把目标拉回画面中心需要大偏航，且第 2 次转向出现符号交替（疑似偏航往复）。新瞄准目标变成连续受限转向命令时，须限制的是图像滚转率；近天底的偏航奇异要在控制层单独处理。这是第一轮 Play 要观察的项，回放测不到。
5. **R-4 真值点待核**：真值目标坐标是车体中心还是挂点未核，A4 的残差结论依赖它。
