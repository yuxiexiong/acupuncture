# 路径设计的CPU合成检查

状态：2026-10-31完成。仅Python标准库、合成二维状态；没有模型、权重、torch或GPU。本检查不是Qwen机制实验，不与旧实验样本数相加。

为[受控路径设计r04](../../docs/cache-mechanism-controlled-path-design-r04-2026-10-31.zh-CN.md)检查：

- 固定key时，以p=βv控制写入、以(α,β)控制旧状态处理，补偿v后与原delta更新一致。
- 改写入保留旧状态算子、改旧处理保留加性写入。
- β=0且目标写入非零时拒绝，β=0且p=0可以取v=0。
- 同样的总效果下，S/O交叉读取能区分仅S、仅O、共同作用；另检查两通道抵消。

代码：[check.py](check.py)。结果：[check-result.json](check-result.json)。复算命令：`python experiments/cache-path-design-check-v1-2026-10-31/check.py`。

32组×8配置×5步，种子20261031；最大双精度误差见结果文件。真实模型的BF16、内核、补偿幅度、分布合理性与机制结论都未验证。失败条件与工程停止规则以设计文档为准。

第二次针对性复审新增[limits_check.py](limits_check.py)与[limits-check-result.json](limits-check-result.json)，不覆盖原检查。反例验证：补偿虽保持βv，仍可超出原轨迹族的状态范围；联合限制与匹配门可给出完全相同的四格及原配对端点。原检查不能用作排除失配的证据。两次均为CPU合成检查，不是Qwen实测。
