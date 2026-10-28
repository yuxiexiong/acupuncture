# 内部轨迹本地归档核验

北京时间 2026-10-28 14:23，A/B/C 全部下载并核验通过。**7,632 条唯一正式记录，缺失、额外、重复均为 0。** 56 条预检单列，不进入正式三维展示。

| 模型 | 注入覆盖 | 正式记录 |
|---|---|---:|
| Qwen3.5-2B | L0–L5 | 920 |
| Qwen3.5-4B | L0–L31 | 4,872 |
| Qwen3.5-9B | L0–L5 | 920 |
| Llama-3.1-8B-Instruct | L0–L5 | 920 |

共取回 15,496 个原始运行文件，2,724,784,628 字节（2.538 GiB），保存在各实验 `archive-r01/execution-r01`。原远端结果及原本地历史快照保持原样；未下载模型权重、未运行推理或新实验，也没有另存一份大型 tar。

核验直接复用各实验冻结 `verify_worker` 的纯 CPU 逻辑：逐份 record、压缩 trace、metadata/calibration SHA-256；来源身份、token 与 provenance；所有层 × attention/MLP/residual 及全部应有输入位置；有限数值与零范数未定义规则；同前缀独立 cache 参照；零剂量/撤针预检；针前 prompt 不变；hook 清理和存档目标权重前后哈希。另核对 worker exit 0、queue 收据哈希、来源精确集合和实际文件集合。全部合同、冻结源和授权哈希亦已对齐；没有重新散列大型模型。

图中的数值比较是同一输入前缀下的干预分支与无针参照。原版自由生成回答另由既有来源联结，不能把两条已分叉的自由回答直接按序号相减。每条轨迹观察模型全部层；这里的归档通过不等于因果机制已确证。

- [总核验摘要](combined-verification.json)
- [A 逐文件哈希及 worker 核验](../../early-layer-mechanism-v1-2026-10-28/archive-r01/verification.json)
- [B 逐文件哈希及 worker 核验](verification.json)
- [C 逐文件哈希及 worker 核验](../../llama31-early-layer-trace-v1-2026-10-28/archive-r01/verification.json)
- [可复跑的纯 CPU 核验脚本](verify_archive.py)
