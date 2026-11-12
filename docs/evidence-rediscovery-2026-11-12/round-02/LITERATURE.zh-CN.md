# 第二轮一手文献核查与取舍

检索日期：2026-11-12。工具：公开网页搜索与arXiv原文页面。目标是挑战候选问题的重要性与剩余增量，而非找到没有任何相似论文的缝隙。只用公开概念查询，未发送私有原始实验数据。初始候选登记见[INITIAL_REGISTER](INITIAL_REGISTER.zh-CN.md)，登记在本轮新增定向检索之前；既有阅读带来的锚定已披露。

以下16项是实际打开的一手页面，阅读深度逐项列明；没有宣称全文精读、独立复现或穷尽查重。搜索结果中的二手解读只用于发现入口，不作为结论依据。预印本的自述不自动成为本项目已核验的事实。

## 1. 查询日志（原查询文本）

| 批次 | 查询 |
|---|---|
| S01 | `vision language models knowledge conflict question intent real world image larger VLind WhatIfVis ROME benchmark` |
| S01 | `language models activation perturbations persistent failure recovery recurrent state sparse neurons collapse` |
| S01 | `function vectors task vectors steering transfer across models causal abstraction interventions` |
| S02 | `LLM recurrent hidden state perturbation recovery persistent errors same transcript cache corruption hybrid linear attention` |
| S02 | `language models inference state fault propagation transient perturbation cache recovery error amplification` |
| S02 | `controllable context sensitivity knowledge conflicts instruction intent Minder 2025` |
| S03 | `language models capability collapse knowledge intact recover access activation perturbation latent competence` |
| S03 | `language model activation steering global collapse recovery sparse neurons operational state competence control` |
| S03 | `language models task conditional steering preserve capabilities universal intervention selective control failure` |
| S04 | `LLM memory state transplantation compatibility functional modularity cache editing reuse causal dependence` |
| S04 | `"activation patching" "repair" "natural" causal interpretability compensation` |
| S04 | `"state" "handoff" "hybrid" "LatentPort"` |

此外直接回读上一轮近邻及从主论文发现的直接近邻。检索返回的多主题混合排序不视为系统综述；S03结果显示曾截断，因此只使用随后实际打开的原文。未把查询命中篇数当文献覆盖率。

## 2. 直接改变判断的近邻

### P01 Seeing or Knowing? Visual Context Sensitivity in Multimodal Large Language Models

[原文v2](https://arxiv.org/html/2607.26326v2)，2026-08-25版本。实际读：摘要、引言、§2–3重建方法、§4–6相关结果、附录A与B。没有核代码或原始训练数据。

作者区分感知与利用，使用WhatIfVis双意图与配对评分；在模型微调后定位控制子空间，再将控制用于原模型。SFT也改善按意图作答，故“前人只有固定偏置、没有遵循问题”不成立。外部指定标量控制与输入条件下自动纠错仍须分开，但不能仅凭这一区别宣布新题。我们可直接借用其问题设置与方法；本项目必须增加可靠性、适应成本或具体解释价值。

### P02 Controllable Context Sensitivity and the Knob Behind It

[原文v4](https://arxiv.org/html/2411.07404v4)，2025-05-30版本；[ICLR官方入口](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c9d780d1e2d57d4b70e807608a72501b-Abstract-Conference.html)。实际读：摘要、引言，未精读完整方法附录。

文本中的上下文／常识双向选择和低维控制已有明确研究。其微调与子空间结果使B的“问题重要”成立，却削弱“问题新”的主张。适用的思想应承接，不把视觉版或不同模型名本身算增量。

### P03 What Attention Recalls and Recurrence Controls in Hybrid Language Models

[原文](https://arxiv.org/html/2609.04434)，2026-09-03版本。实际读：摘要、引言、§3–4方法和主表、结论及限制。

作者通过保留／交换KV与递推通道研究检索和响应模式，明确所称分工是功能作用，不是静态内容互斥；也承认混合状态的相容性限制。不能用我们的混合恢复结果反驳一个作者未主张的“绝对独立仓库”。可借其状态操作与任务分离；A需要解释受扰动后的实际可恢复性，而非重做一次分工表。

### P04 Who Asks, Who Answers: Linear Attention Builds the Query in Hybrid Language Models

[原文](https://arxiv.org/html/2611.01909)，2026-11-01版本。实际读：摘要、引言相关部分、§3–4.1任务、截断与块级干预；§5以后仅见目录与摘要，不称已精读完整跨架构证据。

作者已提出递推构造查询、softmax执行查找的Encode–Address机制。其主任务含单token值及预填回答，不能直接替代我们自然完整回答的判据。它提供很近的计算解释候选；若我们将来只找到相同查询作用，应承认继承，不能因使用不同针号就宣称新机制。

### P05 When Does Activation Steering Change What a Model Computes From?

[原文v2](https://arxiv.org/html/2606.29522)，2026-09-06版本。实际本轮读：摘要、引言与贡献定义；上一轮另读过§8.2–9及限制，阅读身份分别保留。

论文区分答案变化与后续计算真正使用被编辑状态，并以已知状态更新任务检验；也对平均激活steering的自然状态解释提出反证。A不能把“行为不同不等于计算机制不同”重新包装成发现。可以借用其用途检验思想，追问实际失效与恢复的计算关系。

### P06 Contiguity, Not Importance: Budgeted Repair of Stale KV Caches After Document Edits

[原文](https://arxiv.org/html/2609.17983)，2026-09-16版本。实际读：摘要、引言、结果概述与方法问题定义入口；未核代码和全部附录。

作者直接区分干净状态移植与在旧背景中重算，指出移植可恢复的位置未必是可实施修复的位置。其对象是文档编辑后的陈旧KV，不是本项目强激活扰动。这个近邻说明恢复条件很重要，也使“移植不等于修复”本身不能单独成为我们的创新。

## 3. 承接基础与防止过度包装

| 编号及原文 | 实际阅读深度 | 对候选的影响 |
|---|---|---|
| P07 [Leverage Is Not Reach](https://arxiv.org/html/2606.19831)，2026-06-18 | 摘要、引言、§4–5部分、§7.1–7.4 | 剂量校准、控制与塌陷的区别已有直接工作；其持久性例子归因于生成上下文，不能借此裁决我们所有混合缓存条件。R3/R5必须超过强度与输出类型描述 |
| P08 [Sparse Neuron Ablation Triggers Catastrophic Collapse…](https://arxiv.org/html/2512.00918)，v2 2026-06-20 | 摘要、引言、相关工作、问题定义入口 | 极少单元可引起严重输出失效已有先例。不能把坐标少与效果大本身当主要贡献；不同消融和加法操作仍不可混同 |
| P09 [How Linear Attention Remembers](https://arxiv.org/html/2609.33093)，2026-09-27 | 本轮摘要与结构；上一轮读过写读与混合架构部分 | 保存、读取与多事实耦合已有分析基础。A需要把实际受扰动计算与任务恢复联系起来，不能重新发现两者概念不同 |
| P10 [Tail-Replay](https://arxiv.org/html/2608.30310)，v2 2026-10-15 | 摘要、§1–3方法与§4实验设置 | 作者保留FA状态及其输出隐藏量，从后缀重建递推状态；这不是任意受损历史都可短回放。可提供恢复方法参照，不把其基准质量变成我们已有恢复保证 |
| P11 [Aborted but Not Forgotten](https://arxiv.org/html/2608.15939)，2026-08-16 | 摘要、引言及同token不同cache识别说明 | 转录清除不等于状态回滚已有系统级研究。R1若只说文字之外有历史，价值不足；其部署安全结论不由我们人工扰动数据复现 |
| P12 [LatentPort](https://arxiv.org/html/2609.25053)，2026-09-07 | 摘要、引言与范围说明 | 形状兼容、状态逼近与行为用途的区别已有实践背景；作者限定单向模型对与teacher-forced延续。可借状态接口思想，不能把局部距离直接当任务恢复 |
| P13 [Language model capabilities fail in a shared, predictable order…](https://arxiv.org/html/2611.11695)，2026-11-08 | 摘要、引言、Results首节 | 损伤下能力顺序的可预测性已有跨方法研究，且声明长回答等边界。我们少量非单调样例不直接推翻总体统计，也不足以建新通用故障定律 |
| P14 [Sparse Internal Control of Language Models](https://arxiv.org/html/2611.04349)，2026-11-03 | 摘要及结构，未精读算法证明 | 稀疏控制、保护、方向信息和复用已经被列为独立评价轴。仅提出这些标准不能算我们的新框架；算法细节未核，不判断其实际优势 |
| P15 [Steering Safely or Off a Cliff?](https://arxiv.org/html/2602.06256)，2026-02-05 | 摘要、引言和问题范围 | 一般能力、相关控制属性和分布变化下的鲁棒性已被区分。B不能只以某些保护题通过就宣称可靠修复 |
| P16 [The Curse of Multiple Mediators](https://arxiv.org/html/2606.27510)，2026-06-25 | 摘要、引言和贡献；未逐步验算证明 | 作者讨论组件效果对其他状态的依赖及归因偏差。WSB行为交互不能单凭“大”命名新原理；其NIE/PIE理论也不能不匹配图和操作就直接套作本项目份额 |

## 4. 文献后重新开放候选的记录

1. 初始R2似乎能把WSP从搜索细节提升到信息使用问题；P01/P02显示这个问题已有直接框架和方法。保留重要性，降低本项目立即立题的优先级，删掉首次／唯一控制器措辞。
2. 初始R1的“短暂扰动为何持续”被P07/P10/P11进一步约束；只有持续性或重建有效不够。重写为历史信息使用的实际失效与可恢复性，保留原主线，而非转到缓存系统。
3. R3/R5与P07/P08/P13高度相邻。旧数据可作证据背景，当前没有足以独立支撑共同失效机制或通用风险判据的测量。
4. R6与P05/P16高度相邻。把识别限制变成研究质量要求，不自造一个“新因果框架”。
5. R4/R7重要但项目证据不对齐。P12支持状态／功能迁移有研究价值，不支持把我们现有损伤迁移当作功能迁移成功。

## 5. 查重结论的精确边界

本轮**没有**得到“两个问题无人做过”的结论。得到的是：A有最强的项目证据衔接，但仍需一项实际计算关系解释完整任务恢复；B有清楚的任务价值，但同题已有很强先例，我们自己的剩余贡献还不充分。青蒿素原则允许承接同题成熟方法；不能以“已有论文”否定一切，也不能以“还没在本模型跑过”赋予新意。

未执行的范围：没有系统检索全部数据库、引文追踪全集、代码复现或对论文全部数值进行审计。没有验证新论文的所有作者强主张；报告只使用上述读过部分。后续若围绕具体方法或强新颖性主张推进，须针对该主张再核方法与实现，而不是无限增加泛泛文献数量。
