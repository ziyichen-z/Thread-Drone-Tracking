# P1-ENG-ASSET-001 — 分层标签抽查（AC-4）

本文件是 AC-4 的抽样契约与面板清单：**种子与配额必须先提交**，面板生成器
在运行时解析本文件的 `git status --porcelain`（须为空）与
`git log -1 --format=%H` 并写入 `panel-receipt.json`。本文件只存面板、分层
统计与 Unity 日志条目指针，**不复制用户判定原文**（原文由接受/辅助角色代录进
`docs/unity-test-log.md` 的 `UT-P1-ENG-ASSET-001-label-audit` 条目，标 `OFFLINE_VISUAL_CHECK`，零 Play）。

## 1. 抽样参数

- 抽样种子（seed）：`P1-ENG-ASSET-001-label-audit-2026-09-08`
- 配额（S1/S2/S3/S4）：`20/15/15/10`
- 抽样单位：指令逐行文件的一行 (帧, 对象)；域 = 对账域全部 57430 行
- 指令逐行文件 SHA-256：`06565a95d0d1dc7c7fa84406411be52d1e3a97b5b0135045e9c0467e8ccc7eaa`
- 层内取样序：`SHA-256(seed‖frame_id‖object_id)` 升序；每对象每层 ≤ 2 行；层不足额时留空不回填
- 唯一图片总数上限：60

## 2. 分层定义、分母与实取数

| 层 | 定义（按优先序归层，每行只属第一个命中层） | 分母（行） | 分母（去重对象） | 配额 | 实取 |
|---|---|---|---|---|---|
| S1 | `color_status != VERIFIED`（目标对象在 S5 的颜色未验证） | 26027 | 56 | 20 | 20 |
| S2 | `uniqueness_status ∈ {AMBIGUOUS_SAME_CLASS, WILDCARD_UNKNOWN_CLASS, UNIQUE_CLASS_COLOR, UNIQUE_RELATION}` | 8482 | 36 | 15 | 15 |
| S3 | `short_side_px < 32` | 467 | 23 | 15 | 15 |
| S4 | `uniqueness_status = UNIQUE_CLASS ∧ short_side_px ≥ 64` | 15983 | 27 | 10 | 10 |

合计实取 60 行（上限 60）。

## 3. 面板清单

| panel_index | stratum | split | frame_id | object_id | uniqueness_status | short_side_px | surface | overlay_sha256 |
|---|---|---|---|---|---|---|---|---|
| 1 | S1 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000002826.jpg` | `Vehicle_Pick up Truck_color01 (1)` | UNIQUE_CLASS | 110.4 | the pickup truck | `928791740a6d1e1367fa9a6afb44e387464e913f28335cb9550e1d96a069a59e` |
| 2 | S1 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000003091.jpg` | `Vehicle_Ambulance (2)` | UNIQUE_CLASS | 60.4 | the ambulance | `4d44fea6cf1a01c60e2c051c71caab2c1a0aeb091c24c8b38b4e1e6d2ad0ea1f` |
| 3 | S1 | test | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000000985.jpg` | `Vehicle_Bus_color03 (1)` | UNIQUE_CLASS | 45.5 | the bus | `b2da4a115c8fc653342f61b78c0175c47e2da02e2265032269d952885698b7d6` |
| 4 | S1 | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a2-p1-c1-s1/frames/frame_0000000492.jpg` | `Vehicle_Taxi (10)` | COLOR_UNVERIFIED | 60.1 | （无唯一程序） | `843c5160c8cc96fb7ffc6fd5bd1ee9966214ca5be0358a7588a46ac70925bb03` |
| 5 | S1 | dev | `runtime/test-results/p1-detect-001-scout-1-closed-exchange/frames/frame_0000000064.jpg` | `Vehicle_Taxi (2)` | UNIQUE_CLASS | 76.4 | the taxi | `579a7f11f122cfc136b6d545d30448f0010c091016e82e6b7d2fba8df4ff66d2` |
| 6 | S1 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000002228.jpg` | `Vehicle_Truck_color02 (3)` | COLOR_UNVERIFIED | 35.3 | （无唯一程序） | `ca5cb8ec8a288066137d1743d17cb8dc817d2eeea5810915b66c8f9d38a2c976` |
| 7 | S1 | dev | `runtime/test-results/ut-p1-track-002-001-b2-pilot/pass/frames/frame_0000001477.jpg` | `Vehicle_Bus_color03 (1)` | UNIQUE_CLASS | 38.3 | the bus | `01b67f2e13bc67eeece9efc90566ee443c7cfe121e680bf7f388fb75a38a3626` |
| 8 | S1 | dev | `runtime/test-results/ut-p1-m2-rate-002-002-rerun-stopped-scene-defect/frames/frame_0000000067.jpg` | `Vehicle_Taxi (2)` | UNIQUE_CLASS | 54.0 | the taxi | `b967db170f8ed7ae2a077b3703b398467e6654224daaf2d9a3a5ec0c2b3659f2` |
| 9 | S1 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000002632.jpg` | `Vehicle_Container_color02 (5)` | UNIQUE_CLASS | 93.5 | the container truck | `18c81ab6ee9e51a5f32fb28b94427077690562a911bc68bca6f6044fbf1c138a` |
| 10 | S1 | dev | `runtime/test-results/p1-m3-body-001-arm-a-trial-4-post-run/frames/frame_0000001600.jpg` | `Vehicle_Police Car (1)` | COLOR_UNVERIFIED | 34.5 | （无唯一程序） | `d267d6dd850bc89a79f5af87db842d4f522dacb37829b673e8f869e18067988b` |
| 11 | S1 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000002750.jpg` | `Vehicle_Container_color02 (5)` | UNIQUE_CLASS | 93.5 | the container truck | `6e2fc25757e1cd2b467246f8759cfc36dfdeb32b8c6bd4f05e86709b1e1b3edc` |
| 12 | S1 | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a2-p1-c1-s1/frames/frame_0000001256.jpg` | `Vehicle_Pick up Truck_color01` | WILDCARD_UNKNOWN_CLASS | 33.6 | （无唯一程序） | `6dde541cb30a8cac20fd99fc6651145e87021b641836c944ebaf1341fd9d7709` |
| 13 | S1 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001233.jpg` | `Vehicle_Bus_color02` | UNIQUE_CLASS | 61.5 | the bus | `564641e78146b6fc6c99135111fc61c7bbbd35d72bc8d127462a3e61014b01c3` |
| 14 | S1 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000001152.jpg` | `Vehicle_Pick up Truck_color01 (2)` | UNIQUE_CLASS | 154.0 | the pickup truck | `0fc75275b59bef2575c2d4900b29604f59e2ec7c65d3e82de2c3f0f46668e3af` |
| 15 | S1 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000000386.jpg` | `Vehicle_Taxi` | UNIQUE_RELATION | 97.3 | the taxi to the viewer's left of the container truck | `2a55e267ba8b0c29394d59f8a05b88b8275f9feef29e47a18b552f9023334c8c` |
| 16 | S1 | dev | `runtime/test-results/p1-m3-body-001-arm-a-trial-1-attempt-4-post-run/frames/frame_0000000919.jpg` | `Vehicle_Police Car (1)` | COLOR_UNVERIFIED | 34.5 | （无唯一程序） | `ef04605582dd9f15db784033f0ebd58a9fae6b2a330278dca1d58a6f35f6aad2` |
| 17 | S1 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000001793.jpg` | `Vehicle_Taxi` | UNIQUE_RELATION | 105.4 | the taxi to the viewer's left of the bus | `3fb82f8c3c0095c20c792a8bedcefb4688055f8bac6fc9f13ddd4d5d23e5896d` |
| 18 | S1 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000000099.jpg` | `Vehicle_Pick up Truck_color01 (1)` | UNIQUE_CLASS | 61.3 | the pickup truck | `559c40a3db1fe7f6182f8e929e47876cff6293b0b1069ed80d28a059d824d648` |
| 19 | S1 | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a2-p1-c1-s1/frames/frame_0000001789.jpg` | `Vehicle_SUV_color01 (6)` | UNIQUE_RELATION | 52.0 | the suv to the viewer's left of the ambulance | `0d80d8ac15337ad330fcd83fe2b1a8cf19f78e522cf632a8a0bcfef02b189b13` |
| 20 | S1 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000000253.jpg` | `Vehicle_Pick up Truck_color01 (9)` | COLOR_UNVERIFIED | 63.5 | （无唯一程序） | `20104668f90e1cac28763d210544ddf1365025818d27dc881823950d77669f70` |
| 21 | S2 | test | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000000792.jpg` | `Vehicle_Pick up Truck_color02 (1)` | UNIQUE_RELATION | 68.8 | the pickup truck to the viewer's left of the suv | `1a997c06d8030576a3f39e077aa36768eeeb18a60a835ecd5427b86241f7e215` |
| 22 | S2 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000000240.jpg` | `Vehicle_Car_color03 (1)` | UNIQUE_CLASS_COLOR | 27.0 | the gray car | `a07a4b2b239904f94601459151cc4ec96323178a50f2db9b36b8f715fc72690a` |
| 23 | S2 | test | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a3-p1-c1-s1/frames/frame_0000000853.jpg` | `Vehicle_Pick up Truck_color02 (1)` | AMBIGUOUS_SAME_CLASS | 93.4 | （无唯一程序） | `97442b82a37213e6251a8b40f3e4f9f06e6e2e19a7eacce2457f2beb4e72486d` |
| 24 | S2 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002322.jpg` | `Vehicle_Bus_color01 (1)` | WILDCARD_UNKNOWN_CLASS | 41.1 | （无唯一程序） | `8ff99c675aaec1aa998d732023f4e0e3cb57f48e78186931aeee6c36e1c38682` |
| 25 | S2 | test | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002318.jpg` | `Vehicle_Bus_color03` | WILDCARD_UNKNOWN_CLASS | 25.8 | （无唯一程序） | `5b493ad8e651048bac64a89f2e7424ee5b9c90d484fe959cff71330c82d81195` |
| 26 | S2 | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a2-p1-c1-s1/frames/frame_0000001582.jpg` | `Vehicle_Truck_color01 (1)` | AMBIGUOUS_SAME_CLASS | 123.1 | （无唯一程序） | `be3fc423e1672a2a4e2f08bf0c6d17c38066026b046903f7c2a093022d30922f` |
| 27 | S2 | test | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001880.jpg` | `Vehicle_Bus_color03` | AMBIGUOUS_SAME_CLASS | 94.3 | （无唯一程序） | `278dfd74ce8a56e80c2a4c7481e7d7f9ad5aa2f2601da0518ad1be2571f4cac2` |
| 28 | S2 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000001877.jpg` | `Vehicle_Pick up Truck_color02 (4)` | UNIQUE_RELATION | 52.5 | the pickup truck to the viewer's right of the car | `cd8f869b1bae2b4d0be8211d5a34668f094ab68b2be9a33c25e5b458bdefa168` |
| 29 | S2 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000001651.jpg` | `Vehicle_Container_color03` | WILDCARD_UNKNOWN_CLASS | 65.1 | （无唯一程序） | `be7c4f034c206ce8a3b09d1c127a5f4bac5c9862717588c43958cd3a770e8faa` |
| 30 | S2 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002016.jpg` | `Vehicle_Container_color03` | UNIQUE_CLASS_COLOR | 165.7 | the red container truck | `941966633cae1410c00b22831e07cc29399c1d38cf96dfbbb8e91d1183ade082` |
| 31 | S2 | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a2-p1-c1-s1/frames/frame_0000001872.jpg` | `Vehicle_Truck_color02 (1)` | WILDCARD_UNKNOWN_CLASS | 94.8 | （无唯一程序） | `ca2fce437aa23fd7caaae6eb0fa3c95bd40f8ca9ecc0d8daddd2674b645a1f07` |
| 32 | S2 | test | `runtime/test-results/p1-scene-004-scout-4-closed-exchange/frames/frame_0000001142.jpg` | `Vehicle_SUV_color01 (1)` | UNIQUE_CLASS_COLOR | 74.7 | the purple suv | `f43747153a3f34c961e5a2b113a9e641fc1c485060e516c533188055c62e2444` |
| 33 | S2 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000002831.jpg` | `Vehicle_Container_color03 (1)` | UNIQUE_CLASS_COLOR | 104.0 | the red container truck | `8ffae342c2e7f3360773913e380944afce84e90227558efafb8a52ecdc7b23b8` |
| 34 | S2 | test | `runtime/test-results/p1-scene-004-scout-4-closed-exchange/frames/frame_0000000404.jpg` | `Vehicle_Container_color02 (2)` | UNIQUE_CLASS_COLOR | 87.0 | the blue container truck | `d88c0a00deba9ee8843b96417c4f9d7f2284219c58e829314fd3aa21ff45f0e6` |
| 35 | S2 | test | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000002321.jpg` | `Vehicle_Car_color03 (1)` | WILDCARD_UNKNOWN_CLASS | 46.2 | （无唯一程序） | `ea97dd3d8c66f12fa0d0248435a272d090d2b96202ac829382b9e96a6382c840` |
| 36 | S3 | unassigned | `runtime/frames.qual3-leftover-hold/frame_0000005304.jpg` | `Vehicle_Container_color02 (2)` | UNIQUE_CLASS | 30.7 | the container truck | `7725141ec2ef9371b86eb2b1d52e009106d504e40e87fef9e1b22e7eb4ba6bd2` |
| 37 | S3 | unassigned | `runtime/test-results/p1-detect-001-qual-2-protocol-invalid-exchange/frames/frame_0000001665.jpg` | `Vehicle_Container_color02 (2)` | UNIQUE_CLASS | 31.1 | the container truck | `15b814609500397602146e74e278d5d822c39547f6c4c5f7080b7773e5c52e82` |
| 38 | S3 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000001758.jpg` | `Vehicle_Car_color03 (1)` | UNIQUE_CLASS | 24.0 | the car | `86c187aedaed04b3a4c05e7d425e3a294bfdce5fee12f0cf68331650f857cba8` |
| 39 | S3 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001821.jpg` | `Vehicle_Truck_color01 (1)` | UNIQUE_CLASS | 30.8 | the truck | `e92c13acb9ea56d0dce1a1f56754ca3428364e9c4b4e24e1035e346fbabde5a5` |
| 40 | S3 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001593.jpg` | `Vehicle_Truck_color01 (1)` | UNIQUE_CLASS | 28.9 | the truck | `e642a95ef66a53b3d6b2a323b013acc8521ecdd769e5e44e227fb4f08836980e` |
| 41 | S3 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000001017.jpg` | `Vehicle_Police Car (5)` | UNIQUE_CLASS | 21.5 | the police car | `a2e0a8cd86e9335229eb6fd3e4a4070fbdd42af9a9e879f3d726b680866ef7fb` |
| 42 | S3 | train | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a2-p1-c1-s1/frames/frame_0000001604.jpg` | `Vehicle_Car_color03 (1)` | UNIQUE_CLASS | 13.4 | the car | `f127f1edde6ce5ceeb74d78e6e52ef4448ed21bce32b6322b033fd31c5eb0a79` |
| 43 | S3 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000000934.jpg` | `Vehicle_Container_color02 (1)` | UNIQUE_CLASS | 31.9 | the container truck | `b35780ed6d9e4c7062ef4803324e9402ff0d35f1e9992152787d22385e7f21be` |
| 44 | S3 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000001525.jpg` | `Vehicle_SUV_color03 (4)` | UNIQUE_CLASS | 23.3 | the suv | `8fb159c5f015d6850b6d79e5d8a25c2faac0404da32bfd6cc3ff71a6a22a74bb` |
| 45 | S3 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000000802.jpg` | `Vehicle_Police Car (5)` | UNIQUE_CLASS | 28.7 | the police car | `e9e6a87c318574aaaa11c4e79fc70c3d8d873023525ebed6427ba009d7afc954` |
| 46 | S3 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000001417.jpg` | `Vehicle_Pick up Truck_color02 (7)` | UNIQUE_CLASS | 27.7 | the pickup truck | `9221df68e5e0d14998b06b20b52aba9eed6fcd7f988538f776e0a7e66549c490` |
| 47 | S3 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000000346.jpg` | `Vehicle_Container_color03` | UNIQUE_CLASS | 22.6 | the container truck | `0a842d9f050b88ce986349cdc8c7a1cecb095a48e8c89b8731a1f23993f86d78` |
| 48 | S3 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000000793.jpg` | `Vehicle_Police Car (4)` | UNIQUE_CLASS | 30.0 | the police car | `238752969ee4ac80047324251c8f37dd70a1a2c03448be5aabf78c59d1cd2ed0` |
| 49 | S3 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000001457.jpg` | `Vehicle_Container_color02` | UNIQUE_CLASS | 23.5 | the container truck | `75b457f7ff0498718e31208a036f0fbaa5b4409661345d37aacebdd3ee38f695` |
| 50 | S3 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a1-p1-c1-s2/frames/frame_0000001524.jpg` | `Vehicle_SUV_color03 (4)` | UNIQUE_CLASS | 23.3 | the suv | `c7e4108856101158e563af18541ef0314a525ceb656b4c680ae84413ce13a499` |
| 51 | S4 | dev | `runtime/test-results/ut-p1-m2-rate-002-001-case3-attempt1/frames/frame_0000000084.jpg` | `Vehicle_SUV_color01 (1)` | UNIQUE_CLASS | 64.3 | the suv | `dd664ea14d9484e832bc177c9210815904054a5d3980e9718a2dcfa62567ca36` |
| 52 | S4 | dev | `runtime/test-results/ut-p1-m2-rate-002-001-case3-attempt1/frames/frame_0000006066.jpg` | `Vehicle_SUV_color01 (1)` | UNIQUE_CLASS | 64.3 | the suv | `51de1b83f14125227ba58d909af1775605b5fde0766f0080cb0989c32a741ff1` |
| 53 | S4 | unassigned | `runtime/test-results/p1-detect-001-qual-2-protocol-invalid-exchange/frames/frame_0000002948.jpg` | `Vehicle_Container_color02 (2)` | UNIQUE_CLASS | 80.5 | the container truck | `a708454cd537ad15a263e433f4490636827f18ca8267319c1c55f729484fdcf8` |
| 54 | S4 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a6-p1-c1-s1/frames/frame_0000000266.jpg` | `Vehicle_Container_color03` | UNIQUE_CLASS | 79.7 | the container truck | `6ae94dae206fcb070e145a63d005399bdf1a737560f2a18255581e17b24d61e3` |
| 55 | S4 | unassigned | `runtime/rate-study/P1-M2-RATE-003-CLOCKSMOKE/smoke-20260731T024450-995000/frames/frame_0000002182.jpg` | `Vehicle_Container_color01` | UNIQUE_CLASS | 73.0 | the container truck | `f81a6da0f5788d5170cbcd826ce612875ffc763ba59f7f7c60da5cbb49fbad52` |
| 56 | S4 | dev | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a7-p1-c1-s1/frames/frame_0000002141.jpg` | `Vehicle_SUV_color03 (4)` | UNIQUE_CLASS | 115.3 | the suv | `eee2b08376d89ebc9fc7f1998b16cb33b035236286177b1952a7a2fb7cfafabe` |
| 57 | S4 | unassigned | `runtime/rate-study/P1-M2-RATE-003-CLOCKSMOKE/smoke-20260731T024450-995000/frames/frame_0000001091.jpg` | `Vehicle_Container_color01` | UNIQUE_CLASS | 73.0 | the container truck | `cb72a6c566fbbcc495095ba143bec30a241def87e6dd6e747c3ba784963763f2` |
| 58 | S4 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a9-p1-c1-s1/frames/frame_0000000030.jpg` | `Vehicle_Truck_color01 (1)` | UNIQUE_CLASS | 75.8 | the truck | `07a67a013678126739f47a4c38ceb7b3d80b400dad08f92f0fa3ac3a945126b4` |
| 59 | S4 | unassigned | `runtime/frames.qual3-leftover-hold/frame_0000007807.jpg` | `Vehicle_Container_color02 (2)` | UNIQUE_CLASS | 97.9 | the container truck | `24482d13716974d3702a533154344c739cd4120609a0d423f9454e7539107990` |
| 60 | S4 | unassigned | `runtime/test-results/p1-vlm-survey/p1-vlm-survey-a4-p1-c1-s1/frames/frame_0000001640.jpg` | `Vehicle_Bus_color01 (1)` | UNIQUE_CLASS | 109.5 | the bus | `289d9407dbc77d1bca9c2c9e9d945afe733dc47d56d909106b2444c3b184daae` |

## 4. 面板收据

- `panel-receipt.json` SHA-256：`edaae14892e6f75914c760b1256bba5463394c8748403199e18b89ff4eccebf9`（首次生成收据，原字节保留）
- 当前叠加图由 `runtime/eng-asset/P1-ENG-ASSET-001/receipts/run-render-fix-20260909T034849Z.json` 记录的 AC-4 修订 2 重绘产出（移除插图、原帧完整、标题置于帧外；样本身份与原图副本不变）。
- 面板与原图副本落本地 `outputs/eng-asset/P1-ENG-ASSET-001/panel/`（git 忽略）。

## 5. 用户判定统计

判定原文落点：`docs/unity-test-log.md` 的 `UT-P1-ENG-ASSET-001-label-audit` 条目（`OFFLINE_VISUAL_CHECK`，零 Play，由接受/辅助角色代录）。代录表列：`| panel_index | 类别 | 颜色 | 框 | 错误类型 |`，判定取 `对` / `错` / `不确定`，错误类型多选自闭集 `类别错` / `颜色错` / `框不紧或截断` / `遮挡误判` / `车辆缺失或幻影`。

判定来源条目：`UT-P1-ENG-ASSET-001-label-audit`（`docs/unity-test-log.md`，只读）。

| 层 | 面板 | 已判定 | 未判定 | 类别 对/错/不确定 | 颜色 对/错/不确定 | 框 对/错/不确定 |
|---|---|---|---|---|---|---|
| S1 | 20 | 20 | 0 | 20/0/0 | 20/0/0 | 20/0/0 |
| S2 | 15 | 15 | 0 | 15/0/0 | 14/1/0 | 13/0/2 |
| S3 | 15 | 15 | 0 | 15/0/0 | 15/0/0 | 9/0/6 |
| S4 | 10 | 10 | 0 | 10/0/0 | 10/0/0 | 10/0/0 |

错误类型合计（多选）：类别错 0；颜色错 1；框不紧或截断 0；遮挡误判 0；车辆缺失或幻影 0

n ≤ 60 的描述性抽查，不构成审计通过或 F1–F4 结论；「不确定」单独计数、不计为对；空层不计为通过；未判定面板计入 unjudged。

