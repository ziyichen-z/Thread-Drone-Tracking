"""P1-ENG-SFT-002 受限语言选框三态协议：数据合同（K4）实现。

候选 1（K4）只做离线数据加工：对账、三态派生、训练/选层/评估集、prompt v2
与解析/评分/判定、标签语义抽查面板、tokenizer 本地预检、冻结与本地数据包。
零模型、零 GPU、零 Play、零 scenario/session/run/attempt 身份。

红线（合同 §3）：本包不 import `controller.*`，不改运行时任何文件；Unity 真值
只在离线数据加工中使用，不进入控制器或对外传感器元数据。
"""
