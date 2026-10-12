# P1-ENG-FRAME-001 Unity Play 证据

Status: **RUN_COMPLETED_AC21_INCOMPLETE**（2026-10-01）。tracker自然结束、Unity已退出；AC-23安全/身份读数核对满足，AC-21的R7工具输出缺失与用户机身跟随/起停目检未闭，不签整体Unity PASS，不记DONE。实际完整原件保留，接受角色未改代码或跑测试。

当前补测（2026-10-04）已完成行为/安全核对，按钮墙钟缺证；现行裁定见 [补测收集与接受裁定](P1-ENG-FRAME-001-supplement-play-20261004.md)。下文保留10-01原结果，不将其旧缺口当作当前未闭义务。

## 预检、授权与候选身份

首轮预检及未暂停处置、第二次重核放行、暂停核帧与启动、当轮原始HEAD/status见 `docs/unity-test-log.md`「UT-P1-ENG-FRAME-001-D1」。机器记录为同名 `-preflight.json`、`-unpaused-play.json`、`-retry-preflight.json`、`-play2-paused.json`；当前结果为 `docs/evidence/P1-ENG-FRAME-001-play-result.json`，包含manifest/summary/原分析/两份metrics、完整run路径/文件sha、128组同帧原值。候选及配置/模型sha运行时取得；代码/冻结参数与R2通过候选一致，C3不变。

用户本轮原话依次为“已暂停”“匹配”“仅本次延长至420秒”“已恢复”“仅本次延长至480秒”；墙钟两次例外已在越界前逐字入账，最终只限当前第二次总墙钟≤480秒，约273秒仿真计划和其他额度不改。Play开始/退出按钮时刻未独立取得，不能由采集跨度补造完整墙钟；待用户补充。先前330秒及420秒为历史约束。

## 实际完整启动命令（已执行一次）

工作目录 `~/TetheredDroneTracking`；command数组由本轮print-only原样追加三个body参数：

```bash
~/TetheredDroneTracking/.venv-yoloe/bin/python -m controller.track_loop --runtime ~/TetheredDroneTracking/runtime --tracker nanotrack-v2 --init-frame 0 --init-box 0.2765625 0.40625 0.1203125 0.15208333333333332 --track-id target-0 --scenario-id deterministic-loop-untethered --condition follow --ground-plane-y-m 0.2 --planned-duration-s 272.97056274847716 --tracker-model-spec ~/TetheredDroneTracking/config/nanotrack-v2.models.json --tracker-model-dir ~/TetheredDroneTracking/runtime/models/nanotrack-v2 --run-id p1-eng-frame-001-play-1 --body-policy standoff --body-planner-config config/p1-eng-frame-001-body.json --body-scenario-config config/scenario.untethered.json
```

## 运行完成与消耗

退出码0，状态TRACKING，1366条frame记录；实际tracker仿真跨度273.009458s（≥冻结计划272.970563s，完成两圈+60s）；summary与metrics.final存在，无lost/gap/reinit_required记录。旁车整个Play共1480帧，末仿真时间295.985931s；全程首末capture单调钟跨度465.024116s，包括暂停，但不等于完整Play墙钟。tracker自然结束至退出仍有约23s仿真尾段，工具all使用整个旁车Play，loop2只取预注册第二圈，原输出不裁尾。

累计Unity Play2（首轮未完成1+本轮1）、Nano权重加载1、正式run新建1；新scenario/session ID、GPU·h、付费API、YOLO/VLM、下载/安装/远端均0。没有第三次Play授权；剩余加载/run数字额度不构成再开许可。K2账本不改作Unity账本。首轮原件在两处hold保留，本轮独立run只创建一次，未复用已产生ID。

## 安全读数

### §T

| 核对量 | 实际读数 | 结论 |
|---|---:|---|
| 围栏外帧数 | 0 | 满足 |
| 高度偏离初始±0.05m帧数 | 0 | 满足 |
| tether_saturated真帧数 | 0 | 满足无缆模式 |
| 距锚点超过35m帧数 | 1090 | 仅描述，不断言可达圆 |

共享覆盖自预检至退出/收集保持缺席（操作期间未生成或恢复，前/暂停/运行中/后均核到缺席）；Unity日志原文：`Loaded tethered scenario 'deterministic-loop-untethered' from ~/TetheredDroneTracking/config/scenario.untethered.json`。首帧及全部保留元数据场景一致。平台量取同一Play评估器旁车的body/applied_velocity/饱和字段，不进入控制器。按scenario_id+frame_id核全部128组末段保留元数据：camera_position_world_m逐分量与body_world_xyz完全相等，两项饱和标记全部相等；具名样本/原值及sha见机器结果。分析场景sha同时绑定manifest的body场景/effective场景两sha，来源路径原样保留；FRAME配置/场景/模型与预检sha相同。

### §P

命令最大水平速度2.786999m/s（≤4），vy绝对最大值0.0；1361条planner决策中follow_move占0.910360、in_band_hold占0.089640，fallback_margin/hold_estimate_*与全部边界/避障/系留修饰计数均0。是命令速度读数，未用实际速度替代。AC-23该次安全与来源读数核对满足。

## R-1…R-7 描述读数与用户目检

以下来自未修改的工具分析输出，不设性能门、不与旧BODY-001作比较；全字段见机器结果及run内原analysis。

| 描述量 | all（整个旁车Play） | loop2（第二圈） |
|---|---:|---:|
| R1 中心误差p50/p90(px) | 37.442858/40.946273 | 37.471199/40.31439 |
| R2 云台饱和比例 | 0.0 | 0.0 |
| R3 跟随距离p50/p90/max(m) | 14.046544/14.521123/45.556431 | 14.062173/14.227842/15.338217 |
| R4 路程(m)/起停次数/静止比例 | 426.521474/14/0.166216 | 170.76211/5/0.065789 |
| R5 斜距p10/p50(m) | 27.489148/28.002787 | 27.568343/28.01063 |
| R6 follow_move比例 | 0.91036 | 0.943609 |

**R7输出缺口：** `--analyze-run`退出码0，但原输出 `R7_c_track: null`。`tools/frame_follow_replay.py:1311–1314`只读metrics顶层/summary.c_track，实际Unity schema把值放在aggregate.c_track。原始评估器读数：tracker自然结束快照0.994950175285，Play退出快照0.918990254402；尾段无tracker的新帧会改变累计量，二者不可混写为同一端点。原analysis不补填/覆盖。AC-21要求工具产出R1…R7，目前R7缺失，交实现角色按既有AC-21修复并用此已保存run零消耗重分析，不新增AC/阈值、参数或Play。

用户目检原话（逐字）：**“consle无错误，但是我看不见无人机啊”**。Console无错误已记录；机身跟随/起停目检未完成，不能由路径长度或接受角色视觉判断代签。只读核到Game是OverviewCamera（约150m高、正交半幅100m）、机身DroneHub约1.2m宽、无缆时无缆绳；运行时机身对象为TetheredDrone_1，Scene中选中后F可聚焦。当前Play已退出，未再开，不用本次结果改渲染/视角/配置。

## 接受裁定与未闭项

| 项目 | 结论 | 具体依据/下一动作 |
|---|---|---|
| AC-21 两圈与计划时长 | 满足 | tracker自然退出0、273.009458s；summary/metrics.final原件 |
| AC-21 同度量工具R1…R7 | 不满足 | R7=null，schema字段路径缺口；实现按既有AC-21修复后仅重分析现有run |
| AC-21 用户跟随/起停目检 | 证据缺失 | 用户看不到机身，原话保留；未放宽人眼条件 |
| AC-23 安全/身份/同帧来源 | 满足 | 上述§T/§P、全128组同帧一致、双sha绑定 |
| 本次完整墙钟核实 | 证据缺失 | 首末capture465.024116s不是按钮墙钟；480s授权有效，按钮开始/结束时刻尚缺 |

整体Unity验收未通过，Overall维持IMPLEMENTED_REVIEWED_AWAITING_UNITY、Lifecycle ACTIVE；R2既有通过轮保留，R1-3范围外债仍OPEN。下一接手实现角色仅修R7既有义务、保留原件、零消耗重分析；目检与完整墙钟仍回接受/用户。已用尽Play，不放行新采集，不写独立复核文件或finding等级，不借此次读数增加性能主张。
