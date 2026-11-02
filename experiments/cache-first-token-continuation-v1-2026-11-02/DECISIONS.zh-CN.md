# FC-01 决策日志

- **D1 计划由评审撰写**（6486eff），本合同只做执行冻结；我提议的“首步强制 q0”臂已在计划中，未加 H 恢复臂（计划 §3 的理由）。
- **D2 停止集合**：模型目录无 generation_config.json，config 的 eos_token_id = 248044，已含在 {248044, 248046} 中；不使用 HF generate，自写贪心循环，只在停止集合或 32 token 处终止。
- **D3 解码循环**：L.forward 单 token 前向，第一步 logits 的哈希按 B.score 的口径（logits.float() 的 F.th）计算，以便与 NR 记录逐位比对。
- **D4 C 臂按输入共享**：C_nat、C_noEOS1 每输入一次；不按方向复制。
- **D5 runner 复用 NR-01 样板**（freeze/authorize/run/verify/launch），不存张量，轨迹全部写入记录 JSON。
