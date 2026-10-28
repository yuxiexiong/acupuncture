# 早层问题依赖度：既有单针回答的零 GPU 再分析

日期：2026-10-28。状态：**ANALYZED，只读既有归档，无新推理。** 本目录支撑 [下一阶段建议](../../docs/next-stage-dose-calibration-proposal-2026-10-28.zh-CN.md) §1 与 [查重报告](../../docs/literature/dose-calibration-related-work-audit-2026-10-28.zh-CN.md) §4 中引用的全部数字。

## 测量定义

- **问题依赖度**：同一（模型，层，通道，剂量）下八道题回答的不同首 token 数，以及不同前 3 token 前缀数。原版为 8/8。1/1 表示输出已不依赖题目。
- **首步 EOS**：生成长度 1 且结束原因为 EOS。
- **机械重复**：重复出现的 token 四元组占比 ≥50%，沿用既有脚本定义。
- 全部读数来自 `delivery-r01/all.records.jsonl`，按（模型，层，通道，题，剂量）去重。

## 脚本与输出

| 脚本 | 输出 | 内容 |
|---|---|---|
| `early.py` | `outputs/early.txt` | 十点 +1 下 L0–L7 每层每通道首步 EOS 数；首 token 分布；各模型校准尺度 m 随层变化；实际渲染的提示 |
| `dose.py` | `outputs/dose.txt` | 单点正负十档 L0–L7：首步 EOS / 机械重复 / 中位长度 |
| `summ.py` | `outputs/summ.txt` | 从既有 `summary.json` 读按注入层的输出统计与下游传播剖面；各模型逐层 clean 残差/attention/MLP 范数 |
| `tok.py` | `outputs/tok.txt` | 早层首 token 解码为文本（L0–2 与 L3–7 两段） |
| `qdep.py` | `outputs/qdep.txt` | 问题依赖度：四模型全层每层十通道的中位数与"八题同首 token"通道数 |
| `qdep_dose.py` | `outputs/qdep_dose.txt` | 问题依赖度随剂量档的变化 |
| `ident.py` | `outputs/ident.txt` | 八题完整输出逐字相同的通道数及非空例子 |

运行方式：在仓库任意位置执行 `python3 -I experiments/early-layer-question-dependence-v1-2026-10-28/<脚本>`，脚本按自身位置解析数据路径。

## 解释边界

- 八题不是独立样本，不做显著性检验。
- 首 token 多样性是粗指标；正式版应换新题池并加跨题 KL。
- 这些数字描述"输出是否依赖输入"，不描述能力是否保留；深层 ±1 保持 8/8 不等于回答正确。
- Qwen3.5 层型来自 HF main 配置，不是冻结 revision。
