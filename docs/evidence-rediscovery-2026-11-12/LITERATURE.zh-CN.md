# 近邻核查与青蒿素原则

检索日：2026-11-12。目标是对初轮七条线索找到最直接的重合、反证和可借方法，不做“必须无人做过”的筛选。只把下列实际打开的一手来源用于结论；预印本和作者博客的结果均为作者报告，未独立复现。表中的阅读深度不是论文质量评分。当前检索不保证穷尽，更不构成绝对首次性证明。

## 1. 检索记录

使用公开网页搜索和一手论文页面，未上传本项目原始数据。初轮线索已在本目录 `INITIAL_LEADS` 登记；执行者此前知道部分近邻，不能声称完全盲于文献。

本轮实际查询：

1. `activation steering same intervention different context background causal effect write read hybrid linear attention`
2. `"What Attention Recalls and Recurrence Controls"`
3. `"When Does Activation Steering Change What a Model Computes From?"`
4. `"Weight Space Programming" language model agent repair`
5. `site.arxiv.org activation patching metrics methods 2309.16042`
6. `site.arxiv.org activation steering evaluation side effects context "SteerScope"`
7. `site.arxiv.org adaptive data analysis reusable holdout group distributionally robust spurious correlations`
8. `"Sparks of Weight-Space Programming" Takehi`

随后沿旧近邻清单及引用打开 WriteSAE、How Linear Attention Remembers、Models Take Notes at Prefill、Who Asks, Who Answers 等原文。纳入标准：与候选问题的操作、任务、解释或验证目标直接有关；避免为凑文献数加入仅名称相似的论文。搜索还出现若干近期权重编程应用，但未完成正文核查，未据其标题作结论。

## 2. 一手来源账

| 编号与来源 | 本轮实际阅读 | 对本轮判断的作用及可借部分 |
|---|---|---|
| L01 [When Does Activation Steering Change What a Model Computes From?](https://arxiv.org/html/2606.29522)，Shih 等，2026 | 摘要、§8.2–9及限制；不是全文逐项复核 | 已有工作区分行为相似和计算依据，并检查向量尺度及方向特异性。承接其因果承诺，不把“大效应”本身当新机制；其选定任务／位置不直接回答本项目的四格实际差值结果。 |
| L02 [What Attention Recalls and Recurrence Controls in Hybrid Language Models](https://aclanthology.org/2026.findings-emnlp.2061/)，Afendulev 等，Findings EMNLP 2026 | 出版元数据、摘要 | 在所测任务中报告 KV 与递推的分工及状态交换。可作为条件比较的基线；摘要不足以证明永久分工，也不足以逐协议对照 WIN。深入方法仍是限制。 |
| L03 [The Key Handoff: Retrieval in Hybrid Language Models](https://arxiv.org/html/2609.32942)，Kale 等，2026 | 摘要、§2 操作与量尺、范围限制 | 通过交叉安排将携带答案、计算出的 key 和位置指针分开。可直接借用这种区分逻辑；本项目仅有首行偏好不能称新选择机制。 |
| L04 [Where Steering Signals Come From: Activation Source Selection in Activation Steering](https://arxiv.org/html/2607.25270)，Ye 等，2026 | 摘要、§3.3–4.1 | 来源选择影响 steering 已有研究基础。该工作的 generation-only 等设置与本项目不同；可以借来源身份检查，不能仅把 C/H 两来源重新命名便称创新。 |
| L05 [Reading Is Not Using: Retrieval, Judgment, and the Design of AI Financial Research Workflows](https://arxiv.org/html/2608.24842)，Liu 与 Liu，2026 | 摘要、§5.4；原文标为初步稿 | 区分信息取出和决策使用，并报告记忆移植与非平凡 sham。可借目标和对照意识；作者报告的部分阴性控制限制不能略去。不是本项目机制的独立证明。 |
| L06 [Towards Best Practices of Activation Patching in Language Models: Metrics and Methods](https://arxiv.org/abs/2309.16042)，Zhang 与 Nanda，ICLR 2024 | 摘要与元数据 | 度量和损坏方式影响定位结果已有直接方法论基础。Q3 不能以“指标有局限”作为新的总发现；应提供具体可操作的失效判断。 |
| L07 [Does Steering Break Your Model? A Multi-Dimensional Evaluation Suite for LLM Steering Methods](https://arxiv.org/abs/2610.07722)，Yang 等，2026 | 摘要与元数据 | 多维评估 steering 效果和副作用已有工具路线。可借评价维度，不重复造综合分数；本文方法细节未精读，不用于宣称某个指标充分或不足。 |
| L08 [Sparks of Weight-Space Programming](https://rikiyat.github.io/blog/weight-space-programming/)，Takehi 等，2026-11-02 | 作者原始博客引言；未复现其搜索过程 | LLM 直接读写权重的总路线已有。承接实现思想，剩余问题放在稳定失败、反馈和验收对象的关系。博客主张不作为已独立验证的性能基准。 |
| L09 [Weight-Space Programming of Policies and Their Verification via Model Checking](https://arxiv.org/abs/2611.11604)，Gross，2026-11-08 | 摘要、HTML 目录；未精读实现 | 权重编程中平均性能与形式要求不一致及验证反馈已有近邻。可借“验收要求进入反馈”；有限 MDP 的 model checking 不能直接迁移为 VLM 自由回答的形式保证。 |
| L10 [Generalization in Adaptive Data Analysis and Holdout Reuse](https://arxiv.org/abs/1506.02629)，Dwork 等，2015 | 摘要与元数据 | 自适应反复看验证数据的有效性问题已有理论基础。标记 WSP 的选择历史；不据此断言开发提升全属过拟合，也不默认必须采用某种隐私算法。 |
| L11 [Distributionally Robust Neural Networks for Group Shifts](https://arxiv.org/abs/1911.08731)，Sagawa 等，2020 | 摘要与元数据 | 平均指标掩盖群组表现与最差组泛化已有研究。可借目标区分；稳定失败源项与预定义群组不是同一统计对象，不能直接套用结论。 |
| L12 [WriteSAE: Sparse Autoencoders for Recurrent State](https://arxiv.org/html/2605.12770)，2026 | 方法相关段、4B 生成探针、§6.2失败与范围 | 缓存写入干预、读出近似和失败边界均已有方法。4B 某个 cell 的替换／公式失败与另一 cell 的换行生成成功要同时保留，不能称整个 4B 无效。 |
| L13 [How Linear Attention Remembers](https://arxiv.org/html/2609.33093)，2026 | 写—留—读相关段、§4.1–4.2、附录 E/F 范围 | 已有因果写读链与混合架构的记忆来源比较。借其分层终点及适用边界；本项目不能靠“也测了写读”立项，剩余价值在干预条件如何改变同一关系。 |
| L14 [Models Take Notes at Prefill: KV Cache Can Be Editable and Composable](https://arxiv.org/html/2606.17107)，2026 | 引言的机制与操作说明、§3开头、限制 | 下游缓存保留计算后内容、只改源位置未必足够已有相关解释。承接缓存形成历史的重要性；其 KV 编辑范围不等于本项目递推混合背景。 |
| L15 [Who Asks, Who Answers: Linear Attention Builds the Query in Hybrid Language Models](https://arxiv.org/abs/2611.01909)，Zeng 等，2026-11-01 | 摘要与元数据 | 线性注意力参与构造检索 query 已有直接近邻。Q1 不得把“递推影响 query”当新发现；若后来引用其块级实现或跨架构结果细节，需先继续核原文方法。 |

表中链接所指为 2026-11-12 阅读时的公开版本；arXiv HTML 的“当前版本”会更新，具体论断如后续用于稿件，应固定相应版本及原文位置。本文没有将未读正文伪装为精读，没有使用搜索结果摘要替代实现核验。

## 3. 查重后的决定，不做创新性洁癖

| 初轮问题 | 已有基础／实质重合 | 本项目可以争取的有用增量 | 当前处理 |
|---|---|---|---|
| Q1 固定实际写入差值为何只在某背景有选择作用 | 写入干预、query 构造、来源影响与条件性都已有 | 在同一实际差值和完整回答约束下，识别决定可转移性的关系，能解释现有交叉格并预测例外 | 保留主候选。不能只宣布“有交互”；也不因交互概念已有就放弃 |
| Q2 形成历史为何改变 KV／递推恢复关系 | 混合模型分工、缓存形成和下游计算已有 | 解释已有不同结论何时兼容，形成能区分修复需求的条件判断 | 保留另一主候选；不是推翻前人，而是承接并明确适用条件 |
| Q3 局部代理何时不能承诺完整恢复 | 度量敏感性、计算与行为区别、多维副作用已有 | 在实际使用场景中降低错误的定位／修复决策；要比几个反例更具体 | 纳入 Q1/Q2 的测量主线，独立立项暂缓 |
| Q4 首行退化还是供体相关选择 | key／位置／答案区分已有现成方法 | 给 Q1 的替代解释加实质约束 | 并入 Q1，借方法，不为追求不同再发明标签 |
| Q5 平均提分与稳定修复覆盖 | 最差组目标、验证反馈、WSP 已有 | 核清构造依据—反馈—验收的实际断点，区分目标错位与修补空间不足 | 保留独立实践候选；不把“平均不等于稳定”本身当贡献 |
| Q6 深度／符号／剂量图谱 | 干预扫描是成熟路线 | 有用的资料、边界和选材依据；目前缺少超出定性图谱的预测 | 保留背景，不继续自动扩网格 |
| Q7 数值执行路径影响解释 | 工程一致性本就是前提 | 当前用于保证研究可信度；只有出现跨情境的可复用诊断才考虑独立问题 | 作为质量约束，不包装成已发现通用机制 |

“已有方法可以使用”不降低严谨性要求；“直接近邻很多”也不等于问题没价值。这里没有给论文录用概率或强行挑一个胜者。保留问题的依据，是它是否能改变解释或实践决策；当前证据尚不能保证一定做成论文。
