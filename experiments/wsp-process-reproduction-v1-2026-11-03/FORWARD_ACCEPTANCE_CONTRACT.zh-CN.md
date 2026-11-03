# FA-01：前向服务数值验收合同

2026-11-03 冻结。性质：**工程验收**，不是科学实验；夹具输出只在观察端，不进入任何搜索端。实现见 `forward_service.py`（重建的作者前向服务），执行见 `forward_acceptance.py`，CPU 单测 `test_forward_service.py`。

## 服务实现要点（作者服务未公开，以下为本项目的重建选择）

- 生成：vLLM，逐（题，样本）一个请求，种子 = sha256(题号)前 32 位 + 样本序号；`both` 两臂同题同种子，分别在两张卡上的独立引擎中运行。原版与编辑版各一个检查点目录，编辑版由已校验快照按 BF16 就近舍入写入。
- 评分：作者 `mathqa.extract/is_correct`（只去掉未公开的 mcqa 导入）。`no_answer_finished` 按 notice 004 的更正口径。配对差 = 编辑减原版，按题聚类的标准误。
- 内部读数：Hugging Face 前向 + 显式钩子。残差索引 r：0=embed_tokens 输出，r=第 r−1 个解码层（0 起）输出；mlp/attention 层号 = 0 起模块号；mlp_act = `layers.i.mlp.down_proj` 输入。生成时的激活由同一读取器重读 prompt + 答案前 8192 token 得到（vLLM 不暴露内部量）。
- teacher-forced：右填充，token_logprobs 第 0 位为 NaN；返回体积先估算，超过 6 GB 拒绝（拒绝不计 pass）。attention 概率用 eager 实现。

## 判据（任一不过 → 全线停止，不进入搜索；修复后最多重跑一次并记入偏离日志）

| 编号 | 检查 | 通过条件 |
|---|---|---|
| F1 | 检查点身份 | 空快照构建与原文本导出 sha256 相同；夹具编辑只改夹具张量，改动值个数等于快照清单 |
| F2 | 跨引擎一致（原版） | vLLM prompt_logprobs 与 HF token_logprobs：平均 \|Δ\| ≤ 0.05 nat 且 \|Δ\|>0.5 的比例 ≤ 1%；**同时**负对照（vLLM 原版 vs HF 夹具编辑版）必须不通过 |
| F3 | 跨引擎一致（编辑版） | 同 F2 阈值，vLLM 夹具版 vs HF 夹具版 |
| F4 | 索引恒等 | 从 hidden_states[L] 经 final norm + lm_head 重算的 logprob 与 token_logprobs 最大差 ≤ 1e-3；down_proj(mlp_act) 与 MLP 实际输出相对差 ≤ 1e-2；hidden_states[0] 与 embedding 逐位相同 |
| F5 | 钩子中性 | 带/不带读数钩子的 token_logprobs 逐位相同 |
| F6 | 填充 | 8 条文本一批右填充 vs 逐条：最大 \|Δ\| ≤ 0.1、平均 ≤ 0.005 nat（此差同时作为跨引擎差的批次零分布参考） |
| F7 | A/A 配对 | 空快照 `both`（32 道 GSM8K 练习题×2，1024 token）两臂逐字相同的比例 ≥ 0.9 |
| F8 | 生成激活一致 | 生成激活（中层残差，两行：prompt 末位、答案均值）与独立重算的相对差 ≤ 2e-2 |

夹具：8 道 MATH 练习题（固定步长抽取）的评测 prompt + 参考解；夹具编辑 = 第 L/2−2 层 down_proj 加 50% 范数的高斯噪声（种子 7）。这些题目与编辑只用于工程，不给任何搜索者。

## 只测量、不设门槛（用于冻结正式预算）

- F9a：单条 ~32k token teacher-forced（2 层残差 + 1 层 mlp + logprob）的秒数与峰值显存。
- F9b：原版 256 题×1 样本、max_tokens 4096 的生成吞吐（token/s）与截断比例。不是数学成绩。

## 离线预演（6.2）

`forward_acceptance.py demo`：F2/F4/F6/F7/F8 的判据函数在合成数据上各演示一次通过、一次不通过；2026-11-03 服务器 CPU 运行全部符合。F1/F3/F5 是逐位或同阈值判据，F2 的真实数据负对照兼作"可不通过"的演示。

## 资源

每模型准备预算沿用 v2 的 0.5 GPUh（1800 GPU 秒）；此前已记 0.8B 201.93 s、4B 68.70 s。本合同预计每模型约 6–10 次引擎启动 + 短读数，F7 同时占两卡按两倍计。顺序：0.8B 全部判据 → 通过后 4B。
