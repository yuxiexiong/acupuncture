# NBR-01 偏离与修复记录

## D1（2026-11-03，预检 r01 合同执行失败 → 修复重试 r02）

- **现象**：`runs/preflight-r01` 的第一次梯度前向反向时报错：`one of the variables needed for gradient computation has been modified by an inplace operation: [1, 32, 128, 128] ... version 1; expected version 0`。约 28 设备秒，无记录，无判读证据。**分类：合同执行失败（信息量为零）。**
- **根因**：t2 核读取缓存中的递推状态，autograd 为反向（对 q 等的梯度）保存了这块张量；随后模型按正常流程把新状态原地写回同一张量。CPU 测试只用了独立张量，没有走“缓存原地更新”这条真实调用路径。
- **修复**：梯度模式下，每个线性注意力层把 `initial_state.detach().clone()` 交给原核，卷积更新也使用 `conv_state` 的克隆。只改变 autograd 看到的张量身份，前向数值不变（梯度前向的缓存随后丢弃）；推理前向与逐位闸门不受影响。CPU 测试新增一例：用真实原核与原地写回复现报错，并验证修复后可反向、输出逐位不变。
- **共卡**：本次预检开始时，另一条工作流（cache-chain-generalization）在两张卡上各有一个约 10 GB 的进程。显存合计远低于 96 GB；batch1 推理逐进程独立，数值由逐位重放闸门检验；只影响耗时。不动对方进程。
- **重试**：唯一一次有记录的修复重试：CPU 收据 r02、冻结 r02、授权 preflight-r02、输出 `runs/preflight-r02`；r01 目录原样保留。
