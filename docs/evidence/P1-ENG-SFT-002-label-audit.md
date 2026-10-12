# P1-ENG-SFT-002 — 派生标签语义抽查（表 J / AC-14）

本文件是表 J 的抽样契约与面板清单：**种子、层定义与配额先提交**，面板生成器在运行时解析本文件的 `git status --porcelain`（须为空）与 `git log -1 --format=%H`并写入 `panel-receipt.json`。本文件只存抽样参数、分层实取、面板清单、统计与实现者预筛表，**不复制用户判定原文**（原文由接受/辅助角色代录进 `docs/unity-test-log.md` 的 `UT-P1-ENG-SFT-002-label-audit` 条目，标 `OFFLINE_VISUAL_CHECK`，零 Play）。

## 1. 抽样参数

- 抽样种子（seed）：`tdt-eng-sft-002-2026-09-13`（与表 D′ 同一 `h(s)`）
- 用户判定上限：24 张唯一图片；实现者预筛上限：36 张
- 层内取样序：`h(s)` 升序，平局补 `frame_id`/`surface`；J2 先 `color_required`、J3 先含目标车再候选数 3–4、J1 用户份额按弱类顺序各取一行、J4 每类 ≤ 1
- 唯一性：同一 `object_id` 每层 ≤ 1 行、同一帧全局 ≤ 1 行；不足额留空披露、不回填
- 实取：用户 21 行 + 预筛 29 行 = 50 张唯一图片

## 2. 层定义、分母与实取

| 层 | 定义 | 抽样域（行） | 用户配额 | 用户实取 | 预筛配额 | 预筛实取 |
|---|---|---|---|---|---|---|
| J1 | class unique（目录车） | 3003 | 4 | 4 | 8 | 8 |
| J2 | color unique（`color_required` 优先） | 1024 | 3 | 3 | 4 | 4 |
| J3 | class ambiguous（候选集完整） | 420 | 4 | 4 | 8 | 8 |
| J4 | none | 690 | 4 | 4 | 8 | 5 |
| J5 | 目标车 unique | 584 | 3 | 1 | 4 | 0 |
| J6 | G4 关系行 | 86 | 3 | 3 | 4 | 4 |
| J7 | #27 排除帧（`Vehicle_Bus_color03`） | 341 | 2 | 2 | 0 | 0 |

## 3. 面板清单

| panel_index | 层 | 份额 | 来源 | frame_id | object_ids | surface | 状态 | 层(px) | overlay_sha256 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | J1 | user | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000002820.jpg` | `Vehicle_Car_color02` | the car | unique | L | `5df23b89303da6dc45f7c1124594f8f33d840684598689fb1b7ed5258016850b` |
| 2 | J1 | user | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000001801.jpg` | `Vehicle_Pick up Truck_color01 (2)` | the pickup truck | unique | M | `92a09be4b0764c4852832c014a0c92e5b4714a10c0bfead61805f668b34296fe` |
| 3 | J1 | user | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a2-p1-c1-s1/frames/frame_0000002253.jpg` | `Vehicle_Truck_color01 (1)` | the truck | unique | L | `f218542e7d6e32930ae255a4366818b0991622d861357f6371379828259c2291` |
| 4 | J1 | user | select | `runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames/frame_0000000005.jpg` | `Vehicle_SUV_color01 (1)` | the suv | unique | L | `d0fef8ed0fa279fa2d5ea9f84e36ff9fc48690af1dfcc19b0b906bdd97081b26` |
| 5 | J2 | user | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000002023.jpg` | `Vehicle_Container_color02 (1)` | the blue container truck | unique | L | `675a36d8f83187bd4c904efd596f679c1caee684eefbdbc115a34ef67bb48d9b` |
| 6 | J2 | user | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000002749.jpg` | `Vehicle_Container_color03 (1)` | the red container truck | unique | L | `ba7e35779b04920fe28a75bed395dec7838dd8134861399676d09c5aa83ba4f7` |
| 7 | J2 | user | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000001566.jpg` | `Vehicle_Container_color01` | the green container truck | unique | M | `aaaa6f75277c7aeea420d9ce5cd7694b68f5e471f877e5ca9289673086895787` |
| 8 | J3 | user | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000001376.jpg` | `Vehicle_Car_color01 (1)`, `Vehicle_Car_color03 (3)`, `dynamic-target` | the car | ambiguous | S | `9a2a01d5d984856f850b5bc4d987837acca2762fefc616d3f81e202c9157fa9c` |
| 9 | J3 | user | G3 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001788.jpg` | `Vehicle_Taxi (10)`, `Vehicle_Taxi (4)`, `Vehicle_Taxi (9)` | the taxi | ambiguous | S | `7cc7a89c0c176fdfed955175715d97e969a87ecd1c5e6ddec30091537479d4cc` |
| 10 | J3 | user | G3 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001968.jpg` | `Vehicle_Bus_color01 (1)`, `Vehicle_Bus_color02`, `Vehicle_Bus_color03` | the bus | ambiguous | M | `6eb60b8d259d54fbfcdab1d23ecfea2e3f97b27b151583676a1b1010279157ce` |
| 11 | J3 | user | G3 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000000374.jpg` | `Vehicle_Container_color02 (2)`, `Vehicle_Container_color02 (5)`, `Vehicle_Container_color03` | the container truck | ambiguous | S | `7f29fb1a598b419f8ac0ba7416bf022069a02ed5ba68ba711ced9e552aabc4cb` |
| 12 | J4 | user | G5 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000001501.jpg` | （无框） | the police car | none | NA | `a83edc78f7fbfdc0526f45c8a2a30a7b6bef9090e2fee73ab0cb5d0f2c3980d9` |
| 13 | J4 | user | G5 | `runtime/test-results/p1-m3-body-001-arm-b-trial-2-post-run/frames/frame_0000000709.jpg` | （无框） | the pickup truck | none | NA | `fd87ad8aafddc08842f9f470e142ee37ab7a5222bc64fa0d91c28b86ff4a1951` |
| 14 | J4 | user | G5 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000001302.jpg` | （无框） | the bus | none | NA | `0c00a2afa452d22a98f5f6d76d7c509fe69f849f39d9f0d167e7b9a3a48535f7` |
| 15 | J4 | user | G5 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000000898.jpg` | （无框） | the ambulance | none | NA | `d2483e95d248115fe0ffdced59235cf45fad17f6719b0f28465294233160aa1d` |
| 16 | J5 | user | G1t | `runtime/test-results/p1-m3-body-001-arm-b-trial-5-post-run/frames/frame_0000000657.jpg` | `dynamic-target` | the car | unique | M | `759eed50c4d6ac36710111a3a688c2f7d32a991c115ccb87dbb11627edd647d3` |
| 17 | J6 | user | G4 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000001590.jpg` | `Vehicle_SUV_color01` | the suv to the viewer's left of the blue container truck | unique | M | `7521885cb8eb3df018fedb090ceceb7cbac95ef54e4d871d5f6bf53fa9fb96e7` |
| 18 | J6 | user | G4 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000001570.jpg` | `Vehicle_Police Car (1)` | the police car to the viewer's left of the bus | unique | S | `8c6b915257e46c8c3a429664c33df709108cb75676056e06294ea590b404e58d` |
| 19 | J6 | user | G4 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000001960.jpg` | `Vehicle_Pick up Truck_color02 (1)` | the pickup truck to the viewer's right of the bus | unique | M | `a3f879fc2c9f2b28f4f6755e67228afb6f63199a6a83f429bc5297552280209f` |
| 20 | J7 | user | j7 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000000859.jpg` | `Vehicle_Bus_color03` | the gray bus | excluded | NA | `717ba810a99771040a1f4a4d8bf083f52d7ed7677d79adb6f34ee81a1077e3f7` |
| 21 | J7 | user | j7 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000000942.jpg` | `Vehicle_Bus_color01 (1)` | the gray bus | excluded | NA | `138ff7c3040d6432fe6f0b58f2eb81435435d87472e568e1c667e5fe7f609f8d` |
| 22 | J1 | prescreen | train | `runtime/test-results/ut-p1-m2-rate-002-001-case3-attempt1/frames/frame_0000005815.jpg` | `Vehicle_Taxi (2)` | the taxi | unique | M | `04d61122abc09b884f21f289fb0103d3f18cc0f00fec7093bf79b7b896978f19` |
| 23 | J1 | prescreen | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000000371.jpg` | `Vehicle_Container_color02 (1)` | the container truck | unique | L | `606ec73f5a7f1b4897cfe93bd9601ff1a162cebddc71a97d798b946c7d331b2d` |
| 24 | J1 | prescreen | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000000282.jpg` | `Vehicle_Pick up Truck_color02 (4)` | the pickup truck | unique | L | `7141b7a1f0f9d75dbb4289f1cd9853abf7cb3a0e6bfa5b0316913acb062e49e0` |
| 25 | J1 | prescreen | train | `runtime/frames.arm-a-trial-1-void-attempt-3-hold/frame_0000000501.jpg` | `Vehicle_Bus_color03 (1)` | the bus | unique | S | `326a064e718914d12fc0217e147409a1cc98227a0829c534c2918b5296af91eb` |
| 26 | J1 | prescreen | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000000057.jpg` | `Vehicle_SUV_color03 (4)` | the suv | unique | L | `f7e42278238abd999edaacdcd01751338596abb57532a77553728c85e6d00ff2` |
| 27 | J1 | prescreen | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000000969.jpg` | `Vehicle_Pick up Truck_color02` | the pickup truck | unique | L | `4d22e140698c3c31170af22258ec8c1f6eb75bcda9b5d68a7ec4b4d1eac27907` |
| 28 | J1 | prescreen | G1 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000000300.jpg` | `Vehicle_Container_color02 (5)` | the container truck | unique | M | `b86b5b159b4168c5e9cc36c2a86cd02761363529c37640bd9eb8de09c4bf95be` |
| 29 | J1 | prescreen | train | `runtime/test-results/ut-p1-m2-rate-002-b2-formal/r20-follow-3/attempt-2-complete-admissible/frames/frame_0000010805.jpg` | `Vehicle_Container_color01` | the container truck | unique | M | `d8c410508a0776ff102631c164d429acd37d38cbe49d74ddfb9a2654fee58f41` |
| 30 | J2 | prescreen | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000001409.jpg` | `Vehicle_Container_color01 (1)` | the green container truck | unique | L | `6bec49980ba9d5529e33b9480eec83ff511db42571b92744d17148e7c02e4e30` |
| 31 | J2 | prescreen | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000000269.jpg` | `Vehicle_Container_color02` | the blue container truck | unique | M | `d5bafc703dc874406b06d2499068fd5bce37816ecf9a548341ce1b441971f9bf` |
| 32 | J2 | prescreen | G2 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000001551.jpg` | `Vehicle_Container_color03` | the red container truck | unique | S | `e7ebc4a29c19da67a87fa94523e85355db995f5aba7592a0f1e82a501acf6663` |
| 33 | J2 | prescreen | G2 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000000604.jpg` | `Vehicle_Container_color02 (2)` | the blue container truck | unique | M | `b9ff883be39dbf4d4ad20fdf3d54caf09fe046e9024509483223ca823875c421` |
| 34 | J3 | prescreen | G3 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000001141.jpg` | `Vehicle_Pick up Truck_color01 (8)`, `Vehicle_Pick up Truck_color02 (1)`, `Vehicle_Pick up Truck_color03 (2)` | the pickup truck | ambiguous | M | `50f180611cca3ec6d652ddbbe59468a1070fbf1980cd7780f31bf1e5ef6a5803` |
| 35 | J3 | prescreen | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000002166.jpg` | `Vehicle_Pick up Truck_color01 (1)`, `Vehicle_Pick up Truck_color02` | the pickup truck | ambiguous | M | `cbbb62b1acc05a0d56bf9a8425ca4279e03a93d2c2130b304ddfb6933237dab6` |
| 36 | J3 | prescreen | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a2-p1-c1-s1/frames/frame_0000002269.jpg` | `Vehicle_Truck_color01 (1)`, `Vehicle_Truck_color02 (1)` | the truck | ambiguous | M | `a12fd5da8c8096711eb77e94f0fea0b9fb3a38df60abe686695575e8ee22a58d` |
| 37 | J3 | prescreen | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000002595.jpg` | `Vehicle_Pick up Truck_color01 (3)`, `Vehicle_Pick up Truck_color02 (4)` | the pickup truck | ambiguous | S | `0fef38f77549f4bbe8aa82c2f7cb1e44dc67c5d63b96aaec423384889917dfde` |
| 38 | J3 | prescreen | G3 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002234.jpg` | `Vehicle_Pick up Truck_color01 (9)`, `Vehicle_Pick up Truck_color03 (3)` | the pickup truck | ambiguous | L | `14cfeb770e76dc1b3762947e772d2365cdadb899c49dcb52c5c4f00743affab5` |
| 39 | J3 | prescreen | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000001829.jpg` | `Vehicle_Container_color01 (1)`, `Vehicle_Container_color03 (1)` | the container truck | ambiguous | L | `8c1a80d437a868b300afbd946038af0a03cca813b8aee223a3647f114e7957dd` |
| 40 | J3 | prescreen | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000002324.jpg` | `Vehicle_Police Car (1)`, `Vehicle_Police Car (5)` | the police car | ambiguous | S | `2fc9bdf76ea3602be63eb1a9dff89090e0e76b037088156d497a69bcc3ed7464` |
| 41 | J3 | prescreen | select | `runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames/frame_0000000138.jpg` | `Vehicle_Taxi (2)`, `Vehicle_Taxi (8)` | the taxi | ambiguous | S | `23585f44df02f86b5c3f45fe8eae76202452870a713d241f4091489a3ab50182` |
| 42 | J4 | prescreen | G5 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002275.jpg` | （无框） | the suv | none | NA | `639a8654afddf8fac90e785456887d4030e16839d953641913526b3f386db974` |
| 43 | J4 | prescreen | G5 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000000827.jpg` | （无框） | the taxi | none | NA | `8c2af1be8e5396d8df06f74cde59da540fda693121b21d3a6dadbb235ff3d6db` |
| 44 | J4 | prescreen | select | `runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames/frame_0000000261.jpg` | （无框） | the truck | none | NA | `b3c4dabb0eabff19eda947b009b051f352f009c863c26d555af5526539ca152c` |
| 45 | J4 | prescreen | G5 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000002208.jpg` | （无框） | the container truck | none | NA | `06073bc0cc775eb0dfae224f5eafdf3e2d00aeac537a022ad263ed8c69b6b2b3` |
| 46 | J4 | prescreen | G5 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000000883.jpg` | （无框） | the car | none | NA | `d61526dd7436f98ae38a0e1377594c400429376acf12c40c7529f64f68c7ab31` |
| 47 | J6 | prescreen | G4 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000002147.jpg` | `Vehicle_SUV_color01 (6)` | the suv to the viewer's right of the ambulance | unique | S | `c936c2409edef2656b65fe1b006b52bed06a96f2f00ebb7aed4bc37d63505ca3` |
| 48 | J6 | prescreen | G4 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002325.jpg` | `Vehicle_Car_color01` | the car to the viewer's left of the bus | unique | M | `e90faa16fd3eb96ecc2f5edfcb9de07cfc37c66d3d4ea21360238727cd06bf9b` |
| 49 | J6 | prescreen | G4 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000002151.jpg` | `Vehicle_Taxi (6)` | the taxi to the viewer's left of the ambulance | unique | M | `106186d7b157e31502ccd0b4113f169db5c3e72a6af845b65973ee783b5e0395` |
| 50 | J6 | prescreen | G4 | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000001544.jpg` | `Vehicle_Taxi (5)` | the taxi to the viewer's right of the pickup truck | unique | M | `3b74e778a90b9a0e0fe82ea8ff13a0d18bceb2f0ea17bba0de8b88294901a5c9` |

**J7 身份披露（AC-14 修订 2）**：叠框对象、框与 S5 颜色词指向同一个对象；触发整帧排除的 `#27` counterexample 另列，不与叠框对象混用。

| panel_index | 叠框对象（判定对象） | S5 颜色词 | 被排除的 noun | 触发排除的 counterexample |
|---|---|---|---|---|
| 20 | `Vehicle_Bus_color03` | gray | the gray bus | `Vehicle_Bus_color03` |
| 21 | `Vehicle_Bus_color01 (1)` | gray | the gray bus | `Vehicle_Bus_color03` |

## 4. 与 P1-ENG-ASSET-001 面板的交集

本次面板与 ASSET-001 的 60 张面板无 `(frame_id, object_id)` 交集。

## 5. 用户判定统计

| 层 | 用户面板 | 已判定 | 状态对 | 状态错 | 状态不确定 | 其他字段错 | 未判定 |
|---|---|---|---|---|---|---|---|
| J1 | 4 | 4 | 4 | 0 | 0 | 0 | 0 |
| J2 | 3 | 3 | 3 | 0 | 0 | 0 | 0 |
| J3 | 4 | 4 | 4 | 0 | 0 | 0 | 0 |
| J4 | 4 | 4 | 4 | 0 | 0 | 0 | 0 |
| J5 | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| J6 | 3 | 3 | 3 | 0 | 0 | 0 | 0 |
| J7 | 2 | 2 | 2 | 0 | 0 | 2 | 0 |

错误类型计数：颜色错 2

「不确定」单列、不计为对；未判定行计 unjudged。判定原文见 Unity 日志条目 `UT-P1-ENG-SFT-002-label-audit`。

## 6. 实现者预筛（披露，不计为语义核验）

| panel_index | 层 | 状态 | 候选完整 | 颜色 | 关系方向 | 错误类型 | 备注 |
|---|---|---|---|---|---|---|---|
| 22 | J1 | 对 | NA | NA | NA | — | 画面内唯一出租车，框紧；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 23 | J1 | 对 | NA | NA | NA | — | 左缘截断，可见框覆盖可见部分；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 24 | J1 | 对 | NA | NA | NA | — | 皮卡车斗可辨；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 25 | J1 | 不确定 | NA | NA | NA | — | S 层且左缘截断，面板上无法确认类别；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 26 | J1 | 对 | NA | NA | NA | — | 正俯视，SUV/轿车之分靠车体长宽比；救护车未被框，正确；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 27 | J1 | 对 | NA | NA | NA | — | 沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 28 | J1 | 对 | NA | NA | NA | — | 左缘截断；同帧红色车是 truck 类，未框，正确；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 29 | J1 | 不确定 | NA | NA | NA | — | 约 36 px 宽的截断条；已另行核对该帧执行域确只有一辆 container truck；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 30 | J2 | 对 | NA | 对 | NA | — | 绿色可辨；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 31 | J2 | 对 | NA | 对 | NA | — | 蓝色可辨；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 32 | J2 | 对 | NA | 对 | NA | — | S 层；顶部中央红色集装箱车正面，红色可辨；左上蓝色集装箱车（S3 EXCLUDED_OCCLUDED）与下方灰色皮卡不属该颜色 noun；本次新看 |
| 33 | J2 | 对 | NA | 对 | NA | — | 上缘截断（可见约 57%）的深蓝色集装箱车；右侧红色集装箱车为异色，未框正确；本次新看 |
| 34 | J3 | 对 | 对 | NA | NA | — | 红、灰、蓝三辆皮卡均框；左缘紫色截断物经 S3 核为 SUV（TRUNCATED），非候选；本次新看 |
| 35 | J3 | 对 | 对 | NA | NA | — | 灰色皮卡与下方红色皮卡均框；即旧用户 #9 样本，序号与叠加图变化故重看；本次新看 |
| 36 | J3 | 对 | 对 | NA | NA | — | 米色自卸车与右上深红色卡车均框；中间红色为轿车；即旧用户 #10 样本；本次新看 |
| 37 | J3 | 对 | 对 | NA | NA | — | 红色皮卡与左上截断灰色皮卡（可见约 52%）均框；右缘蓝车经 S3 核为 car；即旧用户 #11 样本；本次新看 |
| 38 | J3 | 对 | 对 | NA | NA | — | 蓝、红两辆皮卡均框；左缘灰车为 car、左上黄色截断物为 taxi（S3 TRUNCATED）；下缘红色截断物不在 S3 目录车清单，与 pickup 候选无关；本次新看 |
| 39 | J3 | 对 | 对 | NA | NA | — | 绿色集装箱车与下缘截断红色集装箱车（约 84%）均框；楼后蓝车为 car，黄色/橄榄色平板车为 truck 类，未框正确；本次新看 |
| 40 | J3 | 对 | 对 | NA | NA | — | 两辆警车均框（上方一辆约 50×25 px）；画面其余为公交/卡车/皮卡；本次新看 |
| 41 | J3 | 对 | 对 | NA | NA | — | 下缘截断出租车（可见约 52%）与上方小出租车均框；本次新看 |
| 42 | J4 | 对 | NA | NA | NA | — | 可见车辆为卡车与目标车，无 SUV；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 43 | J4 | 对 | NA | NA | NA | — | 仅一辆蓝色皮卡，无出租车；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 44 | J4 | 不确定 | NA | NA | NA | — | 左缘绿色截断车辆无法判类（同族帧中该位置是 container truck）；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 45 | J4 | 对 | NA | NA | NA | — | 可见为皮卡/轿车/SUV，无集装箱车；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 46 | J4 | 对 | NA | NA | NA | — | 可见紫色车与蓝色皮卡，均非普通轿车；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 47 | J6 | 对 | NA | NA | 对 | — | 救护车在左，被框 SUV 在其右；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 48 | J6 | 对 | NA | NA | 不确定 | — | 面板上未能明确辨出参照的 bus，方向无法独立复核；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 49 | J6 | 对 | NA | NA | 对 | — | 出租车在救护车左侧；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |
| 50 | J6 | 对 | NA | NA | 对 | — | 出租车在红色皮卡右侧；沿用 2026-09-14 预筛（样本身份与原图/叠加图 SHA 未变） |

预筛 29 张（上限 36）：状态对 26、错 0、不确定 3。**预筛只作披露，不计为语义核验，不改变任何冻结决定。**
