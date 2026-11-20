# 文献覆盖、原文入口与逐篇影响

截至 2026 年 11 月 20 日，共 **40 篇论文正文与 1 篇作者研究博客**。表中每项均给出所读原文和对应细读分册，分册记录实验对象、干预或对照、量纲、结果、限制及与项目的重合。论文使用可公开核对的 arXiv 固定版本；arXiv 收录本身不代表同行评议。下列作者数据沿用其原始评测，本次没有重跑外部模型。

## 如何获得和筛选文献

先从两个研究问题抽取能判别重合的操作：一是同文本改变内部历史、换入写入、改变接收背景与读取用途，再测分数或完整作答；二是在保留其他任务行为的约束下控制／修补模型。并列检查前序单针、跨模型、剂量与损伤证据。检索从项目旧文献表及 11 月 12 日两轮近邻出发，用公开网页、学术检索索引、论文互引及截至当日的新预印本补足。匹配到同类干预与任务、同一架构和部件、同类因果对照或能构成直接反例的研究优先。标题相似、仅用同一模型、一般算法／基础理论、无关应用或同文的其他版本均不单独计入。

所有纳入项按作者公开正文从引言、方法和实验读至结论；遇到数值、反例、判分或设定依赖附录时回查对应附录。没有逐一验算每一公式或复判外部每条生成。陈旧 KV 修复论文所称独立补充附录未出现在可取源包，分册已指明受限之处。11 月 1 日旧表含 124 个 arXiv 编号，本次没有把曾经搜集的书目继承为精读量。未订阅数据库、未公开材料、索引延迟及未展开的参考链仍可能有直接近邻。本次结论限于列出的原文。

[11 月 1 日候选来源账](../literature/merged-prior-art-sources-2026-11-01.json) · [11 月 12 日一轮](../evidence-rediscovery-2026-11-12/LITERATURE.zh-CN.md) · [11 月 12 日二轮](../evidence-rediscovery-2026-11-12/round-02/LITERATURE.zh-CN.md) · [本轮检索式及历史书目去重](search-log.zh-CN.md)

## 逐篇对照

| 编号 | 论文全文（固定版本） | 对 Acupuncture 的直接影响 | 设计、数值与边界 |
|---|---|---|---|
| 01 | [How Linear Attention Remembers](https://arxiv.org/html/2609.33093v1) · 2609.33093v1 | 供体事实写入、保存、读出和反向恢复都有直接先例；纯递推与混合模型的结果必须分别比较。 | [逐篇分析](04a-memory.zh-CN.md#paper-2609-33093) |
| 02 | [The Key Handoff: Retrieval in Hybrid Language Models](https://arxiv.org/html/2609.32942v1) · 2609.32942v1 | 不同入口状态下，位置、实体绑定与最终选择可以拆开；背景依赖及来源竞争已有实测。 | [逐篇分析](04a-memory.zh-CN.md#paper-2609-32942) |
| 03 | [Who Asks, Who Answers: Linear Attention Builds the Query in Hybrid Language Models](https://arxiv.org/html/2611.01909v1) · 2611.01909v1 | Qwen3.5 递推构造查询、全注意力选择来源，限制“递推能定向检索”首创说法。 | [逐篇分析](04a-memory.zh-CN.md#paper-2611-01909) |
| 04 | [What Attention Recalls and Recurrence Controls in Hybrid Language Models](https://arxiv.org/html/2609.04434v1) · 2609.04434v1 | 双向交换递推与 KV 后追踪完整答案已有先例，限制赋予单类缓存固定语义职责。 | [逐篇分析](04a-memory.zh-CN.md#paper-2609-04434) |
| 05 | [WriteSAE: Sparse Autoencoders for Recurrent State](https://arxiv.org/html/2605.12770v4) · 2605.12770v4 | 写入替换、读者依赖和按门与查询预测分数已有先例；读写门的位置和任务需具体比较。 | [逐篇分析](04a-memory.zh-CN.md#paper-2605-12770) |
| 06 | [Reading Is Not Using: Retrieval, Judgment, and the Design of AI Financial Research Workflows](https://arxiv.org/html/2608.24842v1) · 2608.24842v1 | 检索到信息和依据信息作出判断已有任务级区分，非专一性假操作仍可影响结果。 | [逐篇分析](04a-memory.zh-CN.md#paper-2608-24842) |
| 07 | [LatentPort: Beyond KV Cache – Cross-Model Transfer of Recurrent Memory in Hybrid Language Models](https://arxiv.org/html/2609.25053v1) · 2609.25053v1 | 一对模型之间移植循环状态后检验续写损失已有先例；与我们的干预功能迁移终点不同。 | [逐篇分析](04a-memory.zh-CN.md#paper-2609-25053) |
| 08 | [Contiguity, Not Importance: Budgeted Repair of Stale KV Caches After Document Edits](https://arxiv.org/html/2609.17983v1) · 2609.17983v1 | 相同位置上的干净状态移植有效，原位重算可很弱，制约由移植直接倒推原故障原因。 | [逐篇分析](04a-memory.zh-CN.md#paper-2609-17983) |
| 09 | [Tail-Replay: Escaping the Curse of Linear Attention in Prefix Caching for Hybrid LLMs](https://arxiv.org/html/2608.30310v2) · 2608.30310v2 | 混合模型保留部分状态后重建递推历史已有系统参照；必须明确重建时可用哪些信息。 | [逐篇分析](04a-memory.zh-CN.md#paper-2608-30310) |
| 10 | [Aborted but Not Forgotten: KV-Cache Retention Breaks Rollback Consistency in Language Agents](https://arxiv.org/html/2608.15939v1) · 2608.15939v1 | 相同可见历史与内部状态等价性已有直接检验，单凭文字相同不能认定完整回滚。 | [逐篇分析](04a-memory.zh-CN.md#paper-2608-15939) |
| 11 | [Leverage Is Not Reach: A Control-Window Law for Single-Neuron Steering in Language Models](https://arxiv.org/html/2606.19831v1) · 2606.19831v1 | 单点剂量、退化、撤针后的文本延续已有近邻；本项目进一步固定同一文本、改变内部历史。 | [逐篇分析](04b-steering.zh-CN.md#paper-2606-19831) |
| 12 | [Sparse Neuron Ablation Triggers Catastrophic Collapse of the Language Core in Large Vision-Language Models](https://arxiv.org/html/2512.00918v2) · 2512.00918v2 | 少数单元足以造成大范围生成损坏已有实证；所用模型、扰动与任务有差异。 | [逐篇分析](04b-steering.zh-CN.md#paper-2512-00918) |
| 13 | [Targeted Neuron Modulation via Contrastive Pair Search](https://arxiv.org/html/2605.12290v1) · 2605.12290v1 | 依据对比行为搜寻神经元并评价控制代价已有先例。 | [逐篇分析](04b-steering.zh-CN.md#paper-2605-12290) |
| 14 | [Forecasting Side Effects of Activation Steering](https://arxiv.org/html/2608.11227v1) · 2608.11227v1 | 控制行为与副作用可同时量化并作预测，须区分已见标定与条件外预测。 | [逐篇分析](04b-steering.zh-CN.md#paper-2608-11227) |
| 15 | [Does Steering Break Your Model? A Multi-Dimensional Evaluation Suite for LLM Steering Methods](https://arxiv.org/html/2610.07722v1) · 2610.07722v1 | 使用多个任务测 steering 代价已有独立基准，不能把综合评测本身作为贡献。 | [逐篇分析](04b-steering.zh-CN.md#paper-2610-07722) |
| 16 | [Sparse Internal Control of Language Models](https://arxiv.org/html/2611.04349v1) · 2611.04349v1 | 控制、保护、可复用性在已有工作中分别接受检验，稀疏度不保证三者。 | [逐篇分析](04b-steering.zh-CN.md#paper-2611-04349) |
| 17 | [Massive Activations in Hybrid Linear Attention Large Language Models: Pre-Attention Spikes and Inter-Spike Plateaus](https://arxiv.org/html/2608.12149v3) · 2608.12149v3 | 混合架构中的高幅激活已有测量；幅值或形状相近不能认定同一项计算失效。 | [逐篇分析](04b-steering.zh-CN.md#paper-2608-12149) |
| 18 | [Cross-Architecture Steering Transfer in Language Models: A Systematic Empirical Study](https://arxiv.org/html/2608.05164v1) · 2608.05164v1 | 学习表示映射并在目标模型查行为已有实证；项目中更可靠的结论是已测配方迁移后的损伤。 | [逐篇分析](04b-steering.zh-CN.md#paper-2608-05164) |
| 19 | [A Single Neuron Is Sufficient to Bypass Safety Alignment in Large Language Models](https://arxiv.org/html/2605.08513v1) · 2605.08513v1 | 特定单神经元可改变被评分的安全行为已有先例；我方旧输出还需区分行为变化与一般退化。 | [逐篇分析](04b-steering.zh-CN.md#paper-2605-08513) |
| 20 | [Language model capabilities fail in a shared, predictable order under compression and perturbation](https://arxiv.org/html/2611.11695v1) · 2611.11695v1 | 受扰后能力损失的顺序已有多模型量化；小面板反例不足以定义新的普遍退化规律。 | [逐篇分析](04b-steering.zh-CN.md#paper-2611-11695) |
| 21 | [Steering Safely or Off a Cliff? Rethinking Specificity and Robustness in Inference-Time Interventions](https://arxiv.org/html/2602.06256v1) · 2602.06256v1 | 同一干预在更新事实时有益、在无关材料中有害；与我方固定可见文字后交换内部来源有别。 | [逐篇分析](04b-steering.zh-CN.md#paper-2602-06256) |
| 22 | [Weight-Space Programming for Vision–Language Model Repair](https://arxiv.org/html/2611.23615v2) · 2611.23615v2 | 已直接用 WSP 修补视觉模型；人工故障低位痕迹与本项目原生失败来源不同。 | [逐篇分析](04c-wsp-vision.zh-CN.md#paper-2611-23615) |
| 23 | [Seeing or Knowing? Visual Context Sensitivity in Multimodal Large Language Models](https://arxiv.org/html/2607.26326v2) · 2607.26326v2 | 同图按问题选择视觉或常识，配对测完整回答及干预已有直接先例。 | [逐篇分析](04c-wsp-vision.zh-CN.md#paper-2607-26326) |
| 24 | [Controllable Context Sensitivity and the Knob Behind It](https://arxiv.org/html/2411.07404v4) · 2411.07404v4 | 文本中的上下文／先验选择及控制已有实证，视觉任务的选择问题应承接这类比较。 | [逐篇分析](04c-wsp-vision.zh-CN.md#paper-2411-07404) |
| 25 | [What Does Weight-Space Programming Add to Diffusion Editing? Program Construction versus Score-Guided Refinement](https://arxiv.org/html/2611.22228v1) · 2611.22228v1 | 编辑程序与外部评分优化的贡献已有拆分，开发分上升不能单独归功于程序理解。 | [逐篇分析](04c-wsp-vision.zh-CN.md#paper-2611-22228) |
| 26 | [Exploring Weight-Space Programming: Capabilities, Generalization, and Limitations](https://arxiv.org/html/2611.09382v1) · 2611.09382v1 | WSP 的能力、对象与可推广性已有多任务评估；零散成功不足以推出通用修补。 | [逐篇分析](04c-wsp-vision.zh-CN.md#paper-2611-09382) |
| 27 | [Weight-Space Programming of Policies and Their Verification via Model Checking](https://arxiv.org/html/2611.11604v1) · 2611.11604v1 | 权重编程中的总任务分和逐条件验证已有明确区分；有限策略验证不能直接移植至开放回答。 | [逐篇分析](04c-wsp-vision.zh-CN.md#paper-2611-11604) |
| 28 | [Minimizing Collateral Damage in Activation Steering](https://arxiv.org/html/2605.01167v1) · 2605.01167v1 | 以行为效果和连带损失共同评价干预已有先例，不能把保护指标本身视为新方法。 | [逐篇分析](04c-wsp-vision.zh-CN.md#paper-2605-01167) |
| 29 | [When Does Activation Steering Change What a Model Computes From?](https://arxiv.org/html/2606.29522v2) · 2606.29522v2 | “输出改变”和“后续计算改用另一状态”已有直接判别；我们的材料没有预定义语义更新规则。 | [逐篇分析](04d-causal.zh-CN.md#paper-2606-29522) |
| 30 | [The Curse of Multiple Mediators: Hidden Interaction Effects in Activation Patching](https://arxiv.org/html/2606.27510v1) · 2606.27510v1 | 多部件恢复出现交互已有理论与实证；四格分数不能直接换算为自然介导份额。 | [逐篇分析](04d-causal.zh-CN.md#paper-2606-27510) |
| 31 | [Towards Best Practices of Activation Patching in Language Models: Metrics and Methods](https://arxiv.org/html/2309.16042v2) · 2309.16042v2 | 度量与损坏方式可以改变激活替换得到的定位；首词、分差、完整答案须分别报告。 | [逐篇分析](04d-causal.zh-CN.md#paper-2309-16042) |
| 32 | [Written as a Record, Read as an Address: What a Forward Pass Leaves in an Operation’s KV Cache](https://arxiv.org/html/2609.24635v1) · 2609.24635v1 | 缓存中可读的内容和下游实际使用的地址已有分离，单靠解码难以定位信息用途。 | [逐篇分析](04d-causal.zh-CN.md#paper-2609-24635) |
| 33 | [Models Take Notes at Prefill: KV Cache Can Be Editable and Composable](https://arxiv.org/html/2606.17107v1) · 2606.17107v1 | 缓存可保留已计算的信息，局部替换和下游补丁的作用不同；文中研究 KV 缓存。 | [逐篇分析](04d-causal.zh-CN.md#paper-2606-17107) |
| 34 | [A Unified View of Attention and Residual Sinks: Outlier-Driven Rescaling is Essential for Transformer Training](https://arxiv.org/html/2601.22966v1) · 2601.22966v1 | 尺度及归一化改变模型行为有机制先例；最终整体缩放不能单独解释特定赢家改变。 | [逐篇分析](04d-causal.zh-CN.md#paper-2601-22966) |
| 35 | [Muir: Linear Attention with Sensitivity-Allocated Gating and Matched-Filter Readout](https://arxiv.org/html/2611.08376v1) · 2611.08376v1 | 读取与门控的作用已有架构实证；读取前的门和本项目归一化后的输出门操作不同。 | [逐篇分析](04d-causal.zh-CN.md#paper-2611-08376) |
| 36 | [Where Steering Signals Come From: Activation Source Selection in Activation Steering](https://arxiv.org/html/2607.25270v2) · 2607.25270v2 | 提取干预信号时的来源选择会影响效果；尚不能据此预测我们的两种实际写入差。 | [逐篇分析](04d-causal.zh-CN.md#paper-2607-25270) |
| 37 | [How LLMs Are Persuaded: A Few Attention Heads, Rerouted](https://arxiv.org/html/2605.09314v2) · 2605.09314v2 | 少数注意力头介导输入影响已有先例，头部定位与解释整条历史形成链有距离。 | [逐篇分析](04d-causal.zh-CN.md#paper-2605-09314) |
| 38 | [What Drives Representation Steering? A Mechanistic Case Study on Steering Refusal](https://arxiv.org/html/2604.08524v2) · 2604.08524v2 | 表征干预改变下游计算已有机制研究；其拒答任务并未测本项目的供体编号选择。 | [逐篇分析](04d-causal.zh-CN.md#paper-2604-08524) |
| 39 | [The Token Before the Value Is the Key](https://arxiv.org/html/2609.15545v3) · 2609.15545v3 | 同一 Qwen3.5-4B 受损背景恢复来源键，可恢复 98.3% 候选分差；指标与四格完整编号不同。 | [逐篇分析](04d-causal.zh-CN.md#paper-2609-15545) |
| 40 | [When Are Sparse Feature Interventions Actually Localized? Matched Evaluation for SAE-Based Safety Control](https://arxiv.org/html/2607.10226v1) · 2607.10226v1 | 在相同层、相同干预量比较后稀疏方法的优势会逆转；只看干预维度或单一判分器不够。 | [逐篇分析](04d-causal.zh-CN.md#paper-2607-10226) |

**另列作者报告**　[Sparks of Weight-Space Programming: LLMs can natively read & write neural network weights](https://rikiyat.github.io/blog/weight-space-programming/) 首发既有 WSP 操作与数学案例，作者公开报告和后续澄清应与本项目重放、回滚及独立验证分别判断。[设计和影响](04c-wsp-vision.zh-CN.md)
