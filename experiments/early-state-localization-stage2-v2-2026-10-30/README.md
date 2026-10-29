# 全层缓存差分与阶段二深度比较

- **范围**：Qwen3.5-4B；先在 L0–L31 每层一个既有固定通道 ×(±1) 共 64 条件上做 KV／递推／conv 八组合缓存差分（G），再按预定窗口选例，对 8 个缓存深度组做七子集扫描（II-A），最后在新题上做候选组双向验证（II-B）。
- **状态（2026-10-30）**：合同 draft-r02 未冻结、未授权运行；实现代码与 CPU 合成测试完成，未做任何模型推理或 GPU 预检；II-B 新题为模型起草、待审。
- **入口**：[方案](PLAN.zh-CN.md) · [合同草案](CONTRACT.zh-CN.md) · [实现说明与决策日志](IMPLEMENTATION.zh-CN.md) · [CPU 收据](readiness/cpu-receipt-r01.json)
