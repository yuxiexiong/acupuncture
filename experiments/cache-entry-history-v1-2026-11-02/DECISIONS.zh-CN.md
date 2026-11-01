# EH 决策日志

- **D1 00 不另评**：00 定义为 C_native（同一缓存、自然入口）；01、FIX0 的自然入口用闸门核对等于 x_C。
- **D2 FIX 正向 e2 取自 B3 记录**：N:CFIX、N:CC 的 logits 已在 B4 与 B3 之间逐位复现，不再重评；XH11 与 B3 N:CC 的逐位重放闸门把本轮与 B3 接上。
- **D3 runner 复用 B4 的样板**（freeze/authorize/run/verify/launch），run_item 新写；不挂 readout hook。
- **D4 评审构想稿不在仓库**：计划 v1 按对话中粘贴的内容写入仓库，并加入反向顺序 FIX 臂与两条预测。
