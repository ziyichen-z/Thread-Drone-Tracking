# P1-M3-BODY-001 `--compare` 执行证据（接受轮 76 §C 合同，恰一次）

**范围**：M3′ batch 1 十次采集齐备后的配对比较，**按接受轮 76 §C 的十条合同执行恰一次**。
授权 = 用户 2026-08-21 逐字「**认可，继续**」（`docs/authorizations.md` 同日条目），
其读法明写「**「认可」指认可该合同条款，故合同即授权范围**」。

**落盘地说明（本角色选定，交接受角色追认）**：交接与合同都只写「记录输出 SHA-256 并落盘
证据」，**未具名文件**。本角色选**专用文件**而非追加进某个 trial 的证据文件，理由是
`--compare` 是**批次级工件**（跨十次采集），不属于任何单个 trial；`…-arm-b-trial-5.md`
已承载 B5 的 §B/§C/§D 三节，再塞入批次级内容会使「按 trial 归档」的检索规律失效。
**若接受角色另有落点偏好，以其裁定为准**（同类缺具名落盘地的情形曾由复核轮 13 F13 判为
CLASS_2，本节因此把选择与理由写在明面上，不留给下一个角色猜）。

**状态**：**已执行**（2026-08-21，实现角色）。零 Play、零采集 ID 创建/消耗、零调参、
零代码/测试/config/scenario/model 改动、零操作单改动。**归因（verdict 的含义与措辞）归
接受角色**（合同第 10 条）；**独立复核仍欠**。

---

## A. 执行前置（合同第 3 条 + 第 2 条 create-once）：**全部满足**

| 前置 | 实测 | 结果 |
|---|---|---|
| 工作树干净 | `git status --porcelain` 空输出；HEAD `af7ba52` | ✓ |
| 十个 run 目录 | 各**恰 11 份**且各含 `m3_body_analysis.json`（10/10） | ✓ |
| 十条 `--verify` | 全部退出 0 且逐字复现冻结值（臂 A 五个 `WITHIN_RANGE`；B1…B5 五个 `SCENE_DEGENERATE` / `1.0` / 窗口 `1.0`） | ✓ |
| `runtime/frames/` | **恰 0 项** | ✓ |
| 六个 shared 文件 | 均**不存在**（§2.25 之后） | ✓ |
| 输出路径 create-once | `runtime/test-results/p1-m3-body-001-compare.json` 执行前**不存在** | ✓ |

> **自查更正（据实登记）**：本角色第一次跑前置时用 zsh 的 `for r in $RUNS` 遍历十个 ID，
> **zsh 默认不对未加引号的参数展开做分词**，`$r` 一次吃下整串，第 2 项误报「0/10」。
> 该误报**由本角色当场识破并改用 Python 重做**（结果 10/10），**未据此停止、也未据此
> 放行**——错的是核对脚本，不是现场。登记以便复核角色核对本节两次执行的差异。

## B. 执行（合同第 1 条，命令原文逐字）

```bash
.venv-yoloe/bin/python tools/analyze_m3_body.py --compare \
  --arm-a p1-m3-body-001-arm-a-trial-1-attempt-4,p1-m3-body-001-arm-a-trial-2-attempt-2,p1-m3-body-001-arm-a-trial-3,p1-m3-body-001-arm-a-trial-4,p1-m3-body-001-arm-a-trial-5 \
  --arm-b p1-m3-body-001-arm-b-trial-1,p1-m3-body-001-arm-b-trial-2,p1-m3-body-001-arm-b-trial-3,p1-m3-body-001-arm-b-trial-4,p1-m3-body-001-arm-b-trial-5 \
  --output runtime/test-results/p1-m3-body-001-compare.json
```

**退出码 0**，stdout 与 stderr 均无输出（除第三方库告警外无任何内容）。
**ID 序列未改动**，A1 用 attempt-4、A2 用 attempt-2，与冻结表一致；
`compare_arms` 的 `expected_acquisition_ids()` 逐字比对未触发任何 `raise`。
**恰执行一次，零重试。**

**输出**：`runtime/test-results/p1-m3-body-001-compare.json`，**3413 字节**，
`schema_version` `p1-m3-body-compare/v3`，

```text
SHA-256  4bd4a14f2176af3ad51ddecc49922e3dabacd9b467267111c1a6303c6c2a0607
```

（合同第 10 条：该 SHA 由**接受角色**钉住入册，本节只据实报告实测值。）

## C. 输出内容（**本节只报事实，归因归接受角色**）

**H2 段 —— verdict `THRESHOLD_ALLOCATION_PARTIAL`**，`passed_components` =
`["area_median_px", "center_error_px"]`：

| 分量 | 五个配对格点中位数 | `summary_median_improvement` | `all_pairs_same_sign` | `pass` |
|---|---|---|---|---|
| `area_median_px` | `632.4378616307513` / `513.9202581212885` / `663.310713669307` / `558.6660874410882` / `585.4605541298952` | `585.4605541298952` | `true` | **`true`** |
| `center_error_px` | `0.5305252075195312` / `0.7804527282714844` / `1.1124763488769531` / `1.5641822814941406` / `1.1714401245117188` | `1.1124763488769531` | `true` | **`true`** |
| `min_side_ge20_share` | **`0.0` × 5** | **`0.0`** | `false` | **`false`** |

**H1 段**：`h1_arm_a_trials` 五条，逐字等于臂 A 的五个冻结值
（`0.5784550773737355` / `0.5783188398250908` / `0.597146417669116` /
`0.5783206310103214` / `0.5783243208518966`，全 `WITHIN_RANGE`）。
另含 `arm_a` / `arm_b` 两个 ID 序列与十份 `analysis_sha256`。

## D. 两条必须随输出一起陈述的事实（合同第 5/6/7 条）

1. **`H2_SUPPORTED` 算术上不可达，本次输出实测坐实**：`min_side_ge20_share` 的五个配对
   格点中位数**全部恰为 `0.0`**，而 `pass` 要求**严格 `> 0`** → 该分量**永远不通过** →
   可达 verdict 只有 `THRESHOLD_ALLOCATION_PARTIAL` 或 `THRESHOLD_ALLOCATION_INEFFECTIVE`。
   接受轮 76 §C.5 **在执行之前**就用真实数据算出了这五个 `0.0`，本次执行**逐项复现**。
   **这正是 H2-CEILING 预登记的内容**——`PARTIAL` 是**事前已知限制下的结果，不是事后
   解释**。
2. **该 JSON 的 H1 段只含臂 A**：`h1_arm_a_trials` 由 `arm_a` 构造，**臂 B 的五次
   `SCENE_DEGENERATE` 不在文件里**。故**任何引用该 JSON 的文字都必须同时陈述处理臂
   饱和**，否则读者只看到臂 A 的 `0.578` 系列而看不到臂 B 撞天花板——**单看 JSON 会
   系统性低估这条限制**。
3. **强制措辞（合同第 7 条）**：效应量**只能**表述为「臂 B 达到 100% 几何可见性，
   **效应量为下界**」，**不得**写成 `1.00 − 0.578`。

## E. 执行后现场（实测，非假定）

- **十条 `--verify` 复跑全部退出 0 且逐字复现**——`--compare` 只读十份 analysis，
  未触碰任何 run 目录字节。
- 十个 run 目录仍**各 11 份**；`runtime/frames/` 仍**恰 0 项**；post-run 归档仍 **9** 处；
  §2.21 七处保全 hold 未触碰。
- `runtime/` 在 `.gitignore` 内，故本批仓库侧 diff 只有本证据文件与状态板。

## F. 边界与未执行项（据实）

- **恰一次执行，零重试**；**未**改 ID / 顺序 / 输出路径（合同第 8 条的重试禁令未被触发，
  因为没有失败）。
- **未执行**：任何新指标/新阈值/新样本域/新统计量/新配对方式（合同第 9 条）；**未据比较
  结果调任何参数**（BC-BODY1-15 (d)）。
- **M3′ batch 1 的关闭未被触发也未被主张**（合同第 10 条），需接受角色另行判断加用户授权。
- **本批未经独立复核。**

## G. 复核范围（给复核角色）

- 本文件全文；对照接受轮 76 §C 的十条合同与 `docs/authorizations.md` 2026-08-21 条目。
- 实测复算建议：输出 SHA-256 `4bd4a14f…0607` 与 3413 字节；十份 `analysis_sha256` 对各
  run 目录内 `m3_body_analysis.json` 的实测值；三分量的十五个配对中位数与三个 summary；
  `min_side_ge20_share` 五个 `0.0` 与 `pass` 的严格 `> 0` 判据（`tools/analyze_m3_body.py`）；
  H1 段只含臂 A 这一事实；十条 `--verify` 执行后仍逐字复现。
- **另请复核 §A 的落盘地选择与自查更正**（zsh 分词导致的前置误报，已当场识破并重做）。
