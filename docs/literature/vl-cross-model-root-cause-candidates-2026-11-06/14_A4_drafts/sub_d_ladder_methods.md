# A4 物体幻觉通路｜七步查重 第 1 步（抽象阶梯）＋第 2 步（方法论单独搜）

检索者：sub_d。日期 2026-11-06，检索截至 2026-11。本文件是草稿输入，不含等级、分数、"值得做"判断。

**阅读层级口径（取对自己不利的读法）**
- **F**：取到正文，且核对了摘要/引言之外至少一处正文章节、表、图注或附录。
- **A**：取到正文但只核对了摘要或引言级陈述，或只读摘要。
- **S**：只有检索片段 / 二手摘要；或正文已下载但本轮没读。
- 逐字引文全部在下载文本里做过归一化匹配（去空白、去行尾连字符）。双栏 PDF 抽取会把两栏交错，12 篇另取了 arXiv HTML 流式文本（`papers/<id>.h.txt`）核对句子；HTML 版会丢掉公式里的数字，凡这种情况数字在 PDF 文本里单独核对，文中标"（数字核自 PDF 文本）"。
- 来自第一轮盘点笔记（05_mechinterp_crossmodel.md）而本轮没有重取的，标"05 路 F，本轮未重取"。

**先说不利的（事实约束与竞争解释，细节见正文对应节）**
1. 文本 LLM 上"truth direction 单一且通用"的说法已被多篇正文级工作收窄：跨数据集不泛化（Orgad）、随层/任务类型/难度/提示模板变（Poulis）、对 sycophantic 与 expectation-inverted lying 失效（Ying）、至少是二维而非一维（Bürger）。把 VLM 的"幻觉方向"当成一条跨任务、跨模型的固定方向，在模板层没有先例支撑，反例更多。（事实约束，§1.3）
2. 头级"真值/语境忠实"结构在**同一谱系**（基座 LLM → 其 VLM 后代）内保留，在**不同预训练谱系**之间相关接近零（Vicuna-7B 对 Mistral-7B 0.04–0.08，2606.15821，F）。这与 07 筛选文件里"直接迁移未见"的约束同向，并且给了它一个量化数字。（事实约束，§1.2）
3. 医学 VLM 上三骨干各自训练 SAE 的对照里，幻觉相关（suppress）特征跨骨干相似度低至 0.25，作者结论是"each model develops its own hallucination pathways"（2605.24977，F）。这直接压在 SSL"一个骨干的 SAE 方向无对齐地加到另一骨干"的做法上。（事实约束，§2.4）
4. 文本 LLM 语境幻觉检测里，逐头 lookback ratio 的预测力"is not concentrated only on a subset of heads"，只用 top-10 头不如用全部头（Lookback Lens，F）。这是模板层对"少数头"说法的一条竞争读法：检测信号可以是分散的，"少数头"可能是干预口径的产物而不是信号分布的性质。（竞争解释，类比档，§1.1b）
5. MT 幻觉线上，"源贡献低 → 幻觉"的量的读法被后续工作收窄：Xu et al. 称 source contribution 的**图样**比源/目标相对贡献**量**更能指示幻觉；Guerreiro et al. 称在自然幻觉上 sequence log-probability 是最好的检测器。与 07 文件"量的读法已被反驳"同向。（事实约束，类比档，§1.1b）
6. 仪器层：消融定位不能推出编辑位置（Hase）；子空间修补可以经由休眠旁路产生"看起来对"的效果（Makelov）；消融会被下游补偿（Hydra / self-repair）；回路忠实度分数随消融方式变（Miller）；单输入因果中介分数本身方差大（Méloux）；steering 逐样本方差大且常反向（Tan、Braun）；SAE 换种子只有约三成特征重合（Paulo）。每条都对应本候选现有文献里的一类主张，见第 2 步。

---

# 第 1 步 抽象阶梯

**模板**："生成模型输出了输入里没有依据的内容 U；U 的概率由少数依赖先验（而非输入证据）的内部部件 / 一个低维线性方向贡献；抑制该部件或方向可减少 U。"

拆成三条可分别检索的子命题：
- T1 **部件稀疏**：U 由少数头/神经元贡献；
- T2 **先验 vs 证据**：这些部件读的是先验（参数知识、已生成文本），不是输入证据（图像、源句、检索上下文、音频）；
- T3 **线性方向**：存在一个低维方向/子空间，沿它干预可增减 U，且该方向跨任务、跨模型可复用。

## 1.1 命中

### (a) 文本 LLM：幻觉 / 真值的内部定位

| 工作 | 对应子命题 | 关键内容（逐字句来自正文） | 层级 |
|---|---|---|---|
| Marks & Tegmark, *The Geometry of Truth*（2310.06824，COLM 2024） | T3 | mass-mean 方向"are more causally implicated in model outputs"；自认局限："we study only models in the LLaMA-2 family, so it is possible that some of our results do not apply for all LLMs"；"cannot disambiguate truth from closely related features, such as “commonly believed” or “verifiable”" | F（§5、§7.1） |
| Li et al., ITI（2306.03341） | T1+T3 | "only a subset of attention heads appear to be strongly related to truthfulness"，只干预 top-K 头；Table 3 比较了不同方向"including random directions"；摘要自述"a trade-off between truthfulness and helpfulness" | A（只核对到方法段与摘要；Table 3 数字未摘） |
| Burns et al., CCS（2212.03827） | T3 | 自述"it transfers across unrelated tasks, suggesting that models may have a task-agnostic representation of the truth" | A |
| Azaria & Mitchell（2304.13734） | T3 | 分类器 71%–83% 准确率（摘要） | A |
| Levinstein & Herrmann, *Still No Lie Detector*（2307.00175） | T3 反例 | "these methods fail to generalize in very basic ways"；§4.4.1 用否定句检验 | F（§4.4.1） |
| Bürger et al., *Truth is Universal*（2407.12831，NeurIPS 2024） | T3 | 真值是**二维**子空间："Two directions explain the generalisation failure"（一般真值方向 tG + 极性敏感方向 tP）；"this finding is universal and holds for various LLMs, including Gemma-7B, LLaMA2-13B, Mistral-7B and LLaMA3-8B"；局限："we test the generalization of TTPD, which is based on the truth direction tG , on only a limited number of statements types and real-world scenarios" | F（贡献列表、局限段） |
| Liu et al., *Universal Truthfulness Hyperplane*（2407.08582） | T3 | 用 40+ 数据集训练探针，"achieving ∼ 70% cross-task accuracy"；引言称只在 TruthfulQA 上训的探针跨任务平均掉约 25 个点（该句双栏交错，未逐字核） | A |
| Orgad et al., *LLMs Know More Than They Show*（2410.02707，ICLR 2025） | T3 反例 | "truthfulness encoding is not universal but rather multifaceted"；"Generalization occurs only within tasks requiring similar skills"；另："they may encode the correct answer, yet consistently generate an incorrect one" | A（摘要＋引言对 §4 的概述） |
| Poulis et al., *Testing the Limits of Truth Directions*（2604.03754） | T3 反例 | universality claims "more limited than previously known"，随层、任务难度、任务类型、提示模板有显著差异 | A |
| Ying et al., *The Truthfulness Spectrum Hypothesis*（2602.20273） | T3 调和 | 方向从 domain-general 到 domain-specific 成谱；线性探针"fail on sycophantic" 与 expectation-inverted lying；图 3："Mahalanobis cosine similarity linearly predicts OOD" 表现 | F（图 3 图注；其余摘要） |
| Bao et al.（2506.00823，ACL Findings 2025） | T3 | 不是所有 LLM 都有一致的 truth direction，与模型能力相关；质疑 Levinstein & Herrmann 的否定句结论是模型问题而非探针问题 | A |
| Ferrando et al., *Do I Know This Entity?*（2411.14257，ICLR 2025） | T2+T3 | SAE 的 known/unknown entity 方向；"chat finetuning has repurposed this existing mechanism"（SAE 在 base 模型上训，对 chat 模型的拒答有因果作用）；"unknown entity recognition directions disrupt the factual recall mechanism, by suppressing the attention of attribute extraction heads"；"we reproduce these findings for the Llama 3.1 8B model" | A（摘要＋贡献列表） |
| Anthropic, *On the Biology of a Large Language Model*（2025，transformer-circuits.pub） | T2 | 默认拒答回路＋"known answer"抑制回路；"at least some hallucinations can be attributed to a “misfire” of this inhibitory circuit"；"We corroborate these findings and illustrate new circuit mechanisms that underlie them"（指 Ferrando et al.）。对象是 Claude 3.5 Haiku 的替换模型，不是开源 VLM | F（Entity Recognition and Hallucinations 一节） |
| Yu et al., *Characterizing Mechanisms for Factual Recall*（2310.15910） | T1+T2 | 用头输出对"记忆答案/上下文答案"词向量的投影找出 memory head 与 in-context head（"We obtain the memory head and in-context head in the following way"），缩放单个头可改变用哪一来源；模型 Pythia-1.4b | F（方法节） |
| Jin et al., *Cutting Off the Head Ends the Conflict*（2402.18154） | T1+T2 | "memory and context heads in later layers can cause knowledge conflicts"；PH3 通过 path patching 找头并剪除，8 个 LM | F（结论节；数字未摘） |
| Minder et al., *Controllable Context Sensitivity and the Knob Behind It*（2411.07404，ICLR 2025） | T2+T3 | "we identify a 1-dimensional subspace in a single layer that encodes whether the model follows context or prior knowledge"；"the exact same subspace serves as an effective knob in not only that model but also non-fine-tuned instruct and base models of that model family" | A |
| Sun et al., ReDeEP（2410.11414，ICLR 2025） | T2 | "hallucinations occur when the Knowledge FFNs in LLMs overemphasize parametric knowledge in the residual stream, while Copying Heads fail to effectively retain or integrate external knowledge from retrieved content" | A |
| Chuang et al., Lookback Lens（2407.07071） | T1 反例 / T2 | 逐头"lookback ratio"（对上下文 vs 对已生成 token 的注意力比）做检测；"the predictive power is not concentrated only on a subset of heads"；"Using only top-10 heads is worse than using all heads"，"top-100 heads largely recover the model’s performance using all heads"。跨模型（7B→13B）不是直接搬："we use a linear regression model to map the heads from the 13B model to the heads in 7B model"；跨任务＋跨模型同时变时"we do not observe significant improvements" | F（§4 跨模型、§5 消融） |
| McDougall et al., Copy Suppression（2310.04625） | T1 | 单头 L10H7 抑制朴素抄写；"One major effect of copy suppression is its role in self-repair"（GPT-2 Small） | A |
| Zhao et al., SpARE（2410.15999） | T3 | 用 SAE 特征控制"用上下文还是用参数知识"；只看到标题与摘要首段 | S |

### (b) 语音 / 音频 / 视频 / 前 LLM 时代图像描述 / MT / 摘要

| 工作 | 对应子命题 | 关键内容 | 层级 |
|---|---|---|---|
| Rohrbach et al., *Object Hallucination in Image Captioning*（1809.02156，EMNLP 2018） | T2（相关级） | 提出 image consistency 与 language model consistency 两个量来判断幻觉来自图像误分类还是语言先验；图 2 例："The hallucination error (“fork”) is more consistent with the Language Model."。这是"幻觉物体更像语言模型会续的词"的最早定量化，手段是外部对照模型，不是内部部件 | F（§2.2、图 2；§3 汇总数字未摘） |
| Calm-Whisper（2505.12969，Interspeech 2025） | T1（因果，单模型） | Whisper-large-v3 解码器 20 个自注意力头逐个遮蔽；3 个头"account for over 75% of the hallucinations"（UrbanSound8K 非语音）；"masking head #1 leads to a reduction of the hallucination rate by more than 30%"；只微调这 3 个头，非语音幻觉降 80% 以上、WER 退化 <0.1%（后两个数字来自摘要） | F（§3.1–3.2）。未见随机头对照（grep `random` 无相关命中） |
| Glazer et al., *Are Audio-Language Models Listening?*（2603.06854） | T1+T2 | text dominance："over-relying on linguistic priors instead of grounding"；找"audio-specialist heads"，其音频注意力预测答对，且与"matched random-head controls"比较；再做头级 steering | F（§4 基线段；效果数字未摘） |
| Cho et al., *Who Wins the Conflict?*（2606.18924） | T2 | 音频-文本冲突下文本占优；"the text pathway does not erase audio"信息而是抑制完好的音频表示；§5.3 "Limitations of Circuit Deletion"：同时删文本与音频回路并不回到中性基线；修法是 back-patching；两个模型、八种语言、四个冲突任务 | F（§5.3） |
| Dale et al.（2212.08597，ACL 2023） | T2（"源贡献低"） | 用 ALTI+ 的源贡献比例检测 MT 幻觉：幻觉是"“detached” from the source"；"Our work is the first to test this intuition in a real setting"（此前只在人造幻觉上验证）；对最严重幻觉检测提升约 2 倍（摘要） | F |
| Guerreiro et al., *Looking for a Needle in a Haystack*（2208.05309，EACL 2023） | T2 限制 | 自然幻觉上"sequence log-probability is the best hallucination detector"；此前提出的内部特征检测器多数不足 | A |
| Xu et al.（2301.07779，TACL） | T2 限制 | source contribution "patterns are stronger indicators of hallucinations" than the relative contributions of the source and target（后半句双栏交错，未逐字核）；文中列了两种图样，第一种是贡献集中在少数源 token，第二种没摘到 | A |
| Ferrando et al., ALTI（2203.04212） | 仪器 | 逐层聚合的 token 归因；本轮只取到正文未读 | S |
| 摘要（summarization） | — | 检索片段称摘要幻觉多为 extrinsic（注意力落在源上但推断越界），与 NMT"解码器忽略源"不同（2606.13216，S）；Baan et al. 2019 称摘要模型的头可消融剪除而性能几乎不掉（1911.03898，S） | S |
| 视频 LLM | — | 2 条查询（1-7、1-17），返回的全是图像 LVLM 工作；未找到对视频 LLM 幻觉做内部部件定位的正文 | 未命中 |

### (c) VQA 时代的 language prior / unimodal bias

| 工作 | 关键内容 | 层级 |
|---|---|---|
| Goyal et al., VQA v2（1612.00837） | 语言先验让模型忽略图像；用互补图像对平衡数据集 | A |
| Agrawal et al., VQA-CP（1712.00377） | 训练/测试答案先验不同的切分下，已有 VQA 模型大幅掉点（"rely on strong language priors in train sets"意群） | A |
| Kervadec et al., *How Transferable are Reasoning Patterns in VQA?*（2104.03656，CVPR 2021） | 通过 oracle 视觉输入与噪声视觉输入模型的 attention modes 对比分析捷径；LXMERT 类模型 | A |
| VisQA（2104.00926）；Language prior 量化（1905.04877）；2305.10143 | 头级可视化工具 / 先验度量 / 物体-答案共现偏置 | S |

VQA 时代的结论层内容是**行为与数据层**的（先验来自问题类型—答案共现，换先验分布就掉点），内部定位只到注意力可视化与 attention modes，没有检索到做因果干预的头级工作（1 条查询，对象层）。

## 1.2 文本 LLM 与 VLM 结论的关系（单列）

### 1.2.1 已被直接检验的

1. **基座 LLM 的头级"语境忠实"打分与其 VLM 后代一致，跨谱系不一致**——Choi et al., *The Truth Stays in the Family*（2606.15821，ICML 2026，代码 https://github.com/miso-choi/TruthProbe）。F（§2.2、§4.2、表 3、附录 F/K/M）。
   - 量的定义：逐头线性探针，区分 context-faithful 与 hallucinated 回答（HaluEval 等），5 折验证准确率即该头的 Truth Score。作者强调问的是"we ask whether individual attention heads faithfully incorporate the provided context"——这是**语境忠实**（context-truthfulness），不是 Marks & Tegmark 意义上的命题真值方向。
   - 同谱系：单数据集探测下基座与 MLLM 后代的 Truth Score 相关在 0.77–0.98 一带（图 1 左柱状图，数值从抽取文本读出，没能逐一对应到模型，引用前需看原图）；跨数据集、跨模态探测下"Vicuna-7B and its LLaVA descendants maintain correlations of approximately 0.51–0.64"（数字核自 PDF 文本）。
   - 跨谱系：Mistral-7B 对 Vicuna-7B "near-zero correlation (0.04–0.08) with Vicuna-7B"；"truthful heads are not universally shared across independently pretrained models, but are instead organized in a lineage-specific manner"。附录 K 的读法："the weak cross-family inheritance observed in Fig. 1 is largely due to representational misalignment rather than the complete absence of truthfulness-related heads"。
   - 位置："80.0% of Top-20 truthful heads in LLaVA-1.5 are located in layers 10-31"。
   - 干预：用基座 LLM 的 Truth Score 做软门控加到 VLM 上。CHAIR（LLaVA-1.5，64 token）CHAIR_I 6.99 → 5.36、CHAIR_S 23.00 → 17.40；用 MLLM 自己的分数是 6.20 / 21.60。POPE(MSCOCO) 上 LLaVA-1.5 Acc 86.9 → 86.7（略降）、LLaVA-NeXT 87.7 → 88.3。随机门控对照（3 种子）："the random head gating method consistently leads to a notable decrease in performance than that of vanilla model"（LLaVA-1.5 86.1 ± 0.18）。Qwen3-VL-8B：POPE 88.59 → 88.63，CHAIR_S 9.4 → 9.8（变差）。
   - 它**没有**做的：没有把 Truth Score 高/低的头与 VLM 幻觉文献里的"偏文本头 / hallucination heads"（Yang et al.）做重合率比较（正文只在相关工作里引用 Yang et al.；grep `overlap|coincide` 无相关命中）；没有在 Marks & Tegmark 式真/假陈述上取方向。
2. **幻觉头的注意力图样与基座 LLM 相似**——Yang et al.（ICLR 2025）：LLaVA-7B 对 Vicuna-7B、MiniGPT-4 对 Llama-2-7B，且指令微调后变化慢。05 路 F，本轮未重取。这是"图样相似"，不是在纯文本任务上检验同一批头的功能。
3. **文本骨干上取的 steering 向量可以搬到 VLM**——Gan et al.（2505.14071，ACL 2026）。F（引言贡献列表、方法段；全文 grep）。"we investigate whether MLLMs can be steered using vectors derived from their text-only LLM backbone, via sparse autoencoders (SAEs), mean shift, and linear probing"；"representations from the text-only LLM backbone remain effective for steering its multimodal counterpart, even after vision-language post-training"；"mean shift boosts spatial relationship accuracy on CV-Bench by up to +7.3% and counting accuracy by up to +3.3%"。任务是空间关系与计数，**不是幻觉**；概念方向是 spatial/counting 等，不是 truth。全文 grep `random` 只命中参考文献，未见随机方向对照。
4. **共用语言骨干的两个 VLM 之间头编号半数重合**——PIH 头（2601.05201），05 路 F，本轮未重取；该文没有在纯文本 Qwen2 上做同一消融。
5. **同一 LVLM 内 truthfulness 头与视觉感知头是不同子集**——Yin et al., *Dynamic Multimodal Activation Steering*（2602.21704，ICLR 2026）。A。"truthfulness and visual perception capabilities predominantly engage different subsets of attention heads within the model architecture"；"truthfulness steering vectors vary significantly across different semantic contexts"。两类头都在 LVLM 内部用多模态样本定义，没有与基座 LLM 对比（grep `text-only|base LLM` 无命中）。它对本候选的含义是：VLM 里"幻觉相关头"至少有两族，且 truthfulness 向量随语义簇变（与 §1.3 文本侧"非单一"同向）。
6. **LVLM 之间的幻觉子空间可迁移，但要先对齐**——TruthPrInt（2503.10602，ICCV 2025）。F（§3.3 / 迁移实验设置）。"ComnHallu to enhance both cross-LVLM and cross-data hallucination detection transferability by constructing and aligning hallucination latent subspaces"；MiniGPT-4（Vicuna）上训的检测器经子空间投影对齐后用于 Qwen2-VL、InternVL-2.5。这是 LVLM↔LVLM，不是文本 LLM↔VLM，且迁移的是**检测器**并带对齐步骤。
7. **基座 SAE 特征在 chat 微调后仍有因果作用**——Ferrando et al.（见上表，A）。这是文本 base→chat，不涉及 VLM；列在此处是因为它是"unknown-entity 方向跨微调保留"的唯一直接证据。

### 1.2.2 只是类比的（文本侧有结论，VLM 侧没有找到直接检验）

| 文本 / 其他模态侧结论 | VLM 侧对应说法 | 关系 | 档位 |
|---|---|---|---|
| memory head / in-context head（Yu；Jin） | "偏文本的头"抑制后幻觉下降 | 两边都是"少数头决定用先验还是用输入"。没有找到在同一模型上检验二者是否同一批头的工作（对象层，查询 1-2、1-11、1-16 共 3 条）。TruthProbe 的"context-truthful heads"是最接近的桥，但它的探针任务是 HaluEval 语境忠实，不是 Yu/Jin 的反事实知识冲突 | 类比 |
| 一维"用上下文还是用先验"旋钮，同谱系 base/instruct/微调模型共用（Minder） | "幻觉方向"（VTI、Nullu、SSL） | 文本侧该旋钮只在同一模型族内复用；VLM 侧 SSL 声称跨不同骨干复用。没有找到把 Minder 式旋钮搬到 VLM 幻觉上并报告成败的工作（对象层，查询 1-1、1-12、1-16 共 3 条） | 类比 |
| unknown-entity latent / "known answer"抑制回路（Ferrando；Anthropic） | "幻觉物体词的概率来自先验" | 文本侧机制是"熟悉度信号误触发 → 关掉默认拒答"；VLM 物体幻觉里对应物会是"共现物体的熟悉度"。没有找到在 VLM 上检验 entity-recognition latent 与物体幻觉关系的工作（对象层，查询 1-4 共 1 条，只返回 Ferrando 原文） | 推测 |
| Knowledge FFN 过度注入参数知识、Copying Heads 没保住外部内容（ReDeEP） | "偏文本头" | ReDeEP 把先验一侧放在 FFN、证据一侧放在头；VLM"偏文本头"说法把先验一侧也放在头。VLM 侧最接近的是 VDC（2512.18813，A）把注意力输出当视觉感知、FFN 输出当内部知识，但不是 ReDeEP 式回归分解。这是一处**部件归属不一致**：同一模板在文本 RAG 上给出"FFN 是先验来源"，在 VLM 上给出"头是先验来源" | 类比（竞争解释） |
| lookback ratio 的预测力分散在许多头（Lookback Lens） | "少数头" | 见"先说不利的"第 4 条 | 类比（竞争解释） |
| MT："源贡献低 → 幻觉"（Dale）及其收窄（Xu、Guerreiro） | "图像贡献低 / 偏文本" | MT 侧有现成的定量工具 ALTI+（把每个输出 token 的贡献分给源与目标前缀）。检索未见把 ALTI 类分解用到 VLM 物体幻觉上的工作（方法层→对象层，查询 1-8 共 1 条；返回的是基于注意力比的 LVLM 方法，如 2608.11847、2505.16411，均为 S/他路已读）。VLM 文献里的"偏文本"多用注意力权重比定义，ALTI 的出发点正是注意力权重不等于贡献 | 类比 |
| Whisper：3/20 个解码器自注意力头占 75% 以上的非语音幻觉（Calm-Whisper） | "少数中深层头" | 另一模态上 T1 的因果先例（单模型、无随机头对照） | 类比 |
| 音频 LLM：text dominance 可定位到头并带随机头对照（2603.06854）；文本通路抑制音频表示（2606.18924） | "偏文本" | 另一模态上 T2 的先例；2606.18924 的"抑制而非擦除"与 A1（看见了没用上）更近 | 类比 |
| Rohrbach 2018：幻觉词与语言模型预测更一致 | "幻觉来自语言先验" | 行为/外部对照级先例；LVLM 时代的同类量化有 NoLan（2602.22144）、PDM-H / LanP（2502.12359）——均为 S，本轮未读（他路可能已读） | 类比 |

### 1.2.3 没找到的（都注明层次与查询条数）

- **对象层**：把文本 LLM 上按 Marks & Tegmark / Bürger 方式取的 truth direction 直接加到 VLM 上、并报告物体幻觉指标成败的工作——未找到（查询 1-1、1-9、1-12、1-16，共 4 条）。最接近的是 Gan et al.（搬的是 spatial/counting 概念向量）与 TruthProbe（搬的是头级打分，不是方向）。
- **结论层**：报告"VLM 幻觉方向与底座 LLM truth direction 的余弦 / 子空间重合度"的句子——未找到（同上 4 条查询；另在 2606.15821、2505.14071、2602.21704、2503.10602 正文里 grep 相关词无命中）。
- **对象层**：检验 VLM 幻觉头与 Yu/Jin 的 memory/context 头、与 Ferrando 的 unknown-entity latent 是否同一批部件——未找到（查询 1-2、1-4、1-11，共 3 条）。

## 1.3 truth direction 在文本 LLM 上"是否单一、是否跨任务、是否跨模型"——已知结论（正反）

| 轴 | 支持 | 限制 / 反例 |
|---|---|---|
| **是否单一** | Marks & Tegmark：mass-mean 方向有因果作用（F） | Bürger：至少二维（tG + tP），一维探针在肯定句→否定句上失败正是因为没分开两者（F）；Orgad："multiple, distinct notions of truth"意群（A）；Ying：从通用到专用的一族方向（F/A）；2505.21800 "From Directions to Cones"（S，已下载未读） |
| **是否跨任务 / 跨数据集** | CCS 自述跨无关任务迁移（A）；Liu：多样数据训练后跨任务约 70%（A）；Bao：原子陈述上训的探针可泛化到逻辑变换、QA、ICL（A）；Ying：多数域之间泛化好，联合训练能恢复（A） | Levinstein & Herrmann：对否定句不泛化（F）；Orgad：只在需要相似技能的任务内泛化（A）；Poulis：随层、任务类型、难度、提示模板变（A）；Ying：对 sycophantic、expectation-inverted lying 失效（A） |
| **是否跨模型** | Bürger：二维结构在 Gemma-7B、LLaMA2-13B、Mistral-7B、LLaMA3-8B 上都出现（F）——这是"各模型分别找到同构结构"，不是同一向量可搬 | Bao：不是所有模型都有一致方向，与能力相关（A）；TruthProbe：头级结构只在谱系内保留，跨谱系 0.04–0.08（F）；"Shared Truth"（NeurIPS 2026 poster，S）：跨族真值结构"partially compatible, ordinally stable, but non-isomorphic"（来自检索摘要，未核正文）；Lookback Lens：7B→13B 需回归映射头（F） |

三条轴分开读：文本侧"存在线性可读的真值信号"证据很强；"它是一条方向"被二维/多方向结果收窄；"跨任务可用"正反都有，取决于训练数据多样性与任务类型；"跨模型"只有结构同构与谱系内保留的证据，没有无对齐直接搬运跨谱系成功的正文级证据（方法层，查询 1-9 与 2-2 共 2 条）。

## 1.4 第 1 步对本候选意味着什么

- （推导）模板的三条子命题在别处的证据强度不同：T2（先验 vs 证据）在 MT、RAG、知识冲突、音频四处都有独立先例；T1（少数部件）有 Whisper、memory/context head 支持，也有 Lookback Lens 的分散性反例；T3（单一可复用方向）反例最多。因此"头"与"方向"两类说法在模板层的先例地位不对称。
- （推导）TruthProbe 给出了一个可直接复用的检验口径：同一打分在基座与后代之间算相关，并用无亲缘模型做零带（0.04–0.08）。A4 里"偏文本头是否继承自语言骨干"这一问，在**语境忠实打分**这个量上已有答案（同谱系保留）；在"偏文本头"这个量上还没有同口径的数字。
- （类比）ReDeEP 把先验来源放在 FFN，而 VLM 幻觉头文献把它放在头。Dual-Pathway（2605.13156，他路 F）是否已覆盖 MLP 通路由负责该篇的检索者核对；若只有头被测过，"先验在头里"与"先验在 FFN、头只是没把图像证据带过来"在现有 VLM 证据上未必分得开。
- （类比）MT 线的教训是量的读法先被提出、后被收窄为图样的读法；VLM 侧 07 文件第 2 条约束已经记录了同样的转向。
- （推测）如果 VLM 幻觉方向与底座 LLM 的 context-vs-prior 旋钮（Minder）是同一方向，那么它应当在纯文本的上下文冲突任务上同样可读、可控；未见检验。

## 1.5 第 1 步未命中汇总

- 视频 LLM 幻觉的内部部件定位：未找到（对象层，2 条查询）。
- 摘要任务上按头/层把"源贡献"与"参数先验"分开的机制工作：未找到（对象层，1 条查询）。
- VQA-CP 时代对 language prior 做头级因果干预的工作：未找到（对象层，1 条查询）。
- §1.2.3 的三项。
- 检索摘要里提到一篇"用 path patching 在五个开源 MLLM 上找 hallucination-driving / resisting heads"的 2026 预印本，摘要工具给的编号 2605.10622 取回后是 *Vocabulary Hijacking in LVLMs*，正文 grep `path patching|driving|resisting` 无命中——该 path-patching 论文的编号没有确认，只算 S，建议由第 5 步（引用链）核对。

---

# 第 2 步 方法论单独搜

每件仪器：已知局限 → 逐字句与出处 → 对本候选意味着什么（标档）。

## 2.1 Activation patching

- **腐蚀方式改变定位结果**。Zhang & Nanda, *Towards Best Practices of Activation Patching*（2309.16042，ICLR 2024）F（§1、§3.2）："varying these hyperparameters could lead to disparate interpretability results"；高斯噪声"may break model’s internal mechanisms by introducing OOD inputs to the layers"；建议："We advocate for STR, as it supplies in-distribution corrupted prompts that help to preserve consistent model behavior. On evaluation metric, we recommend logit difference"。
- **noising 与 denoising 测的不是同一件事**。Heimersheim & Nanda（2404.15255）F（§2.3、§2.5）：denoising 找的是"patching which activations were sufficient to restore the behaviour"，noising 找的是"patching which activations were necessary to maintain for the behaviour"；高斯噪声修补"has not been used much recently, especially because the corruption can sometimes be ineffective"。
- **子空间修补的错觉**。Makelov et al.（2311.17030）A：即使子空间干预让输出像是特征被改了，"this effect may be achieved by activating a dormant parallel pathway leveraging another subspace that is causally disconnected from model outputs"。
- **单输入因果中介分数本身不稳**。Méloux et al.（2510.00845）F（摘要、结果节、建议节）："exact, single-input CMA scores exhibit high intrinsic variability, implying that the causal effect of a component is a volatile random variable rather than a fixed property"。
- 对本候选：
  - （推导）VLM 幻觉修补里常见的腐蚀是"换成无关图 / 噪声图 / 去掉图"。按 Zhang & Nanda，噪声图与去图属于分布外腐蚀，对应的定位结果要与"换成只差目标物体的对照图"（STR 的视觉对应物）比较后才可比。
  - （推导）"抑制该头后幻觉下降"是 noising 型证据（必要性）；"把该头从无幻觉运行补回即可消除幻觉"是 denoising 型（充分性）。竞争者全景表里应分列，不能合并成"因果"一栏。
  - （类比）"沿幻觉方向投影/擦除后幻觉下降"属于子空间干预，Makelov 的错觉在 VLM 上是否出现未见检验。

## 2.2 头消融 / 缩放

- **补偿**。McGrath et al., *The Hydra Effect*（2307.15771）F（§1、§2.3）："ablations of one attention layer of a language model cause another layer to compensate"；它"complicates our understanding of what it means for a network component to be important because two natural-seeming measures of importance (unembedding and ablation-based measures) become much less correlated than we would naïvely expect"。Rushing & Nanda（2402.15390）A：全分布上"self-repair is imperfect"且逐提示波动大。
- **消融值的选择**。Li & Janson, *Optimal Ablation*（2409.09951）F（§2）：零/均值/重采样消融除了"删除"信息还会"spoofing"，其中一种是"causes the model to treat x in a way that it never treated any training input"；作者主张 OA 给出的部件重要性更可靠（摘要）。Miller et al.（2407.08734）A："existing methods are highly sensitive to seemingly insignificant changes in the ablation methodology"；"the task a circuit is required to perform depends on the ablation used to test it"。
- **定位 ≠ 编辑位置**。Hase et al., *Does Localization Inform Editing?*（2301.04213，NeurIPS 2023）F（摘要、表 1 图注）：Causal Tracing 的定位结论"do not provide any insight into which model MLP layer would be best to edit in order to override an existing stored fact with a new one"；"Tracing effects explain essentially none of the variance in rewrite score, while the choice of edit layer is very important"。
- **重合率不等于忠实度**。Hanna et al.（2403.17806）A："measuring overlap is no substitute for measuring faithfulness"。
- **注意力权重选头 vs 因果选头**。1 条查询（2-11）：返回的都是非 VLM 的个案（注意力最高的位置不是修补效应最大的位置），未找到在 VLM 上直接比较"按图像注意力比选头"与"按修补效应选头"的工作（对象层，1 条查询）。全部 S。
- 对本候选：
  - （推导）零消融/缩放到 0 的头级结果同时含"删除"与"spoofing"两部分；与 mean / resample 消融的结果不可直接比较。已取到的 VLM 幻觉头论文各自用哪种消融，需要在竞争者全景表里逐个标出。
  - （推导）"单头消融无效"不能读成"该头不参与"（Hydra）；"单头消融有效"在有补偿的情况下是下界。
  - （推导，来自 Hase）"头 H 被定位为幻觉来源"推不出"编辑/抑制 H 是最好的修法"。定位类贡献与修复类贡献要各自有独立证据。
  - （类比）Calm-Whisper 的"3 个头占 75%"是单头遮蔽口径，同样受上述限制。

## 2.3 Steering vector / 均值差方向

- **逐样本不可靠**。Tan et al.（2407.12404，NeurIPS 2024）A："steerability is highly variable across different inputs"；"steerability is also mostly a property of the dataset rather than the model"；分布外"for several concepts they are brittle to reasonable changes in the prompt"。Braun et al.（2505.22637）A：效果"exhibit high variance across samples, and often give an effect opposite of the desired one"；"vector steering is unreliable when the target behavior is not represented by a coherent direction"。
- **评测口径**。Pres et al.（2410.17245）A：四条缺失性质之一是"baseline comparisons should be offered"；按其流程重评后"some interventions are less effective than previously reported"。
- **跨模型复现**。Da Silva et al., *Steering off Course*（2504.04635）A："up to 36 models belonging to 14 families"，大量模型无提升甚至退化（摘要意群，后半句双栏交错未逐字核）。Brumley et al.（2411.07213）A："ICVs outperform FVs in behavioral shifting, whereas FVs excel in tasks requiring more precision"。
- **输给简单基线**。AxBench（2501.17148，ICML 2025）F（摘要＋结果/讨论节）：概念 steering 上"prompting outperforms all existing methods, followed by finetuning"；"SAEs are not competitive"；"DiffMean significantly outperforms SAEs, particularly in earlier layers"；表征类 steering"fail to outperform standard prompting and finetuning baselines"。模型为 Gemma-2-2B/9B。
- **方向取法**。Marks & Tegmark（F）：mass-mean 方向比 LR/CCS 探针方向因果作用更强；ITI（A）：Table 3 含随机方向对照，mass mean shift 最好。Im & Li（2502.02716）A：把 CAA（均值差）、RepE（主成分）、ITI（探针参数）放进统一框架比较（结论句未摘）。
- **随机方向对照与副作用**。1 条查询（2-5）：返回 2607.09156（主张匹配范数的随机方向只作诊断、且取多次抽样最大值是有偏估计）、2603.24543、SteerScope 2610.07722（分布外提示下副作用更明显）——全部 S，未取正文。
- 对本候选：
  - （推导）VLM 幻觉 steering 论文（VTI、Nullu、SSL）报告的是数据集平均。按 Tan/Braun，需要逐样本分布（多大比例反向）才能判断"方向"是否成立；05 路已记 Dual-Pathway 的"static direction 只解释 45–69% 方差、mean-difference 投影无效"与此同向。
  - （推导）AxBench 的结果意味着"换提示"是 steering 类修法必须打的基线；这与 00_BRIEF 的"便宜办法"字段同一要求，第 6 步（对抗轮）已有专门查询（6-6）。
  - （推导）ITI 在 2023 年就把随机方向放进了对照表，TruthProbe 有随机门控对照；因此"随机方向/随机部件对照"在该仪器上是既有惯例，缺它的 VLM steering 结果在对照严格度这条轴上低于文本侧水位。
  - （类比）DMAS 报告 truthfulness 向量随语义簇显著变化，与 Braun"行为不是一个相干方向时 steering 不可靠"是同一条件。

## 2.4 SAE 特征：跨模型 / 跨层迁移与 universality

- **同数据换种子，特征不同**。Paulo & Belrose（2501.16615）F（摘要、§7）：Llama 3 8B 上 131K latents 的 SAE，只有 30% "of the features were shared across different seeds"（"30%"与该短语在 PDF 文本中相邻但被双栏打断，数字核自 PDF 文本）；"SAEs do not uncover a “universal” set of features"。
- **跨模型是"经变换后相似"，且有相当比例不对应**。Lan et al.（2410.06981）F（引言、讨论）：假说是 SAE 特征空间在 rotation-invariant 变换下相似，据此 steering 向量"may be transferred across models via certain transformations"；同时"there is a notable fraction of features idiosyncractic to different SAEs"。
- **下游任务不如线性探针**。Kantamneni et al.（2502.16681，ICML 2025）A：图 1 图注"SAE probes underperform the baseline of logistic" regression（四种情形的跨数据集均值）。DeepMind 团队 2025-03 的 *Negative Results for SAEs On Downstream Tasks*（S，只见二手摘要）：分布外有害意图检测上稠密线性探针近乎完美、SAE 探针差。AxBench 见 §2.3。
- **专门查：把模型 A 上训的 SAE 方向直接加到另一骨干的残差流**（3 条查询：2-1、2-2、2-12；另 2-6 查 base→chat）：
  - **需要映射的先例**。Oozeer et al., *Activation Space Interventions Can Be Transferred Between LLMs*（2503.04429，ICML 2025）A：学一个 autoencoder / affine 映射把源模型激活映到目标模型后再迁移 steering 向量；跨架构在词表相近时可行，"the vocabulary spaces are distinct"时困难（该句前半双栏交错）。Chen et al., *Transferring Linear Features Across Language Models With Model Stitching*（2506.06609）A："affine mappings between residual streams of language models is a cheap way to effectively transfer represented features between models"——迁移 SAE 权重同样先学仿射映射。
  - **同谱系内可直接用的先例**。Ferrando et al.（base SAE 方向对 chat 模型有因果作用，A）；Kissane et al. "SAEs (usually) transfer between base and chat models"（S，论坛帖：Mistral-7B、Qwen 1.5 0.5B 可迁移，Gemma v1 2B 因权重差异大而失败）；Gemma Scope（S）。
  - **文本 SAE 用到 VLM 的先例**。Gan et al.（文本骨干的 SAE 特征方向加到其多模态后代，F，见 §1.2.1）；VISTA（2605.24946，ICML 2026，A）：反过来训练投影器——"trainable linear projector maps them into a frozen LLM"残差流，让现成文本 SAE 能读视觉 token。两者都是**同一语言骨干**。
  - **直接的负面证据（对象最近）**。Nooralahzadeh et al., *Universal Boosts, Specific Suppressors*（2605.24977）F（摘要、方法、讨论）：在 RadVLM（Qwen3-VL-8B 骨干）、LLaVA-Rad（Vicuna）、CheXOne（Qwen2.5-VL-3B）上**各自训练** SAE 并做跨模型特征对齐；boost 特征跨架构相似（signature cosine 0.91-0.95），suppress 特征"as low as 0.25 [0.12, 0.40] for LLaVA-Rad vs. CheXOne"（两处数字核自 PDF 文本）；"hallucination-linked (suppress) directions are model-specific"；"Therefore, transferable steering must treat suppression per-backbone, rather than sharing a universal suppress list"；"models share some quality-promoting directions, but each model develops its own hallucination pathways"；"boost priors may transfer, while suppress features should be re-examined for each" backbone。领域是胸片报告，不是自然图像物体幻觉。
  - **SSL 自己怎么写的**（2505.16146，F：§3、§4.4、Limitations）：SAE 来自 LLaVA-NeXT-8b 第 25 层，方向"generalize seamlessly to other architectures"（LLaVA-1.5-7b、InstructBLIP-7b）；强度逐模型另调："We set γ to 0.6, 0.8, and 0.1 for LLaVA-NeXT, LLaVA-1.5, and InstructBLIP, respectively"（数字核自 PDF 文本）；随机对照只出现在 LLaVA-NeXT 上的潜变量分类图（"Random1 denotes a single latent activation randomly selected from the SAE latent space"），在另两个模型上的随机方向对照 grep 未见；局限："our study does not include a comparison of SAEs trained on other model architectures"。正文没有说明两个不同骨干的残差空间如何对应（grep `mapping|align` 无相关命中）。
  - 结论：除 SSL 本身外，**未找到**"不经任何映射、把一个预训练谱系上的 SAE 方向直接加到另一谱系残差流里"且带随机方向对照的先例；也**未找到**点名批评 SSL 这一步的论文（方法层/对象层，3 条查询）。找到的先例要么同谱系，要么先学映射；找到的最近负面证据（2605.24977）指向幻觉相关特征是骨干特有的。
- 对本候选：
  - （推导）SSL 的跨骨干主张与四条正文级结果相抵：TruthProbe 跨谱系 0.04–0.08、Oozeer/Chen 需要映射、Lan 有不对应特征、2605.24977 suppress 特征骨干特有。在 SSL 补出随机方向对照之前，其跨模型效果有一个未排除的读法：InstructBLIP 上 γ=0.1 的小扰动带来的是非特异效应。这是竞争解释，不是已证实的否定。
  - （推导）SAE 换种子只有约三成特征重合，意味着"第 k 号潜变量是幻觉特征"这类陈述需要多种子 SAE 才成立；SSL 只用了一个公开 SAE。
  - （类比）"boost 通用、suppress 专有"若在自然图像物体幻觉上成立，则"幻觉通路"与"忠实通路"的跨模型性不对称——未见检验。

## 2.5 Logit lens / 词表投影

- **文本侧已知局限**。Belrose et al., *Tuned Lens*（2303.08112）A：logit lens"which yielded useful insights but is often brittle"；即使看起来能用，输出也"hard to interpret due to representational drift"（不同层表示基不同）。
- **VLM 视觉 token 上的适用性**。
  - 支持：Neo et al.（2410.07149，ICLR 2025）F（贡献列表、局限）："the information for an object is highly localized to the token positions corresponding to their original location in the image"；视觉 token 表示逐层向可解释词表 token 靠拢；局限："our results may not generalize to significantly different architectures"（只做了 LLaVA 类）。ProjectAway（2410.02762）由他路读过，局限见 05 笔记。
  - 限制：LatentLens（2602.00462）F（§1–2）：LogitLens 等"substantially underestimate the interpretability of visual token" representations——其方法判 68% 视觉 token 可解释，EmbeddingLens 与 LogitLens 只有 32% 与 24%（数字来自正文，跨 15 个 VLM 与各层平均）；两条结构性局限："The description set is limited to a model vocabulary"，以及"Latent representations from different layers are always compared to the same reference vectors"。
  - 检索片段（S，未取正文）：一篇提出 Logit Lens Loss 的工作称视觉内容会扩散到语言 token、局部性被破坏，使 logit lens 可视化不可用；2605.22903 称深层视觉 token 彼此更相似。
- 对本候选：
  - （推导）"物体信息局部化在对应视觉 token 上、可沿词表方向读出和擦除"依赖 logit lens 的读数。按 LatentLens，logit lens 在视觉 token 上漏读约三分之二（24% 对 68%）；因此"读不出 = 没有该物体信息"不成立，"擦掉词表方向 = 擦掉物体信息"也只对被 logit lens 读出的那部分成立。
  - （推导）Neo et al. 的局部化结论自限于 LLaVA 类（线性/MLP 投影器、无 token 压缩）；对 Q-Former（InstructBLIP、MiniGPT-4）或带 token 合并的架构，局部化前提需单独核。
  - （类比）tuned lens 的动机（早层基不同）提示：在 VLM 早层对视觉 token 用 logit lens 的阴性结果信息量低。

## 2.6 静态权重编辑（零空间投影、ROME 类）

- **伤一般能力**。Gu et al.（2401.04700）A：编辑改进事实性的同时带来"unintended side effects on the general abilities"（QA、对话、NER、NLI 等）。检索片段（S）：ROME 顺序编辑先渐退后突然崩溃；MEMIT-Merge 对指令式提问不泛化（2603.15518）。
- **零空间投影的保证有边界**。*Reproducibility Study of AlphaEdit*（2606.26783）F（摘要、§5.2–5.3）：原范围内可复现，但"the null-space projection’s protection against catastrophic forgetting is bounded rather than unconditional"；在 Phi3、Gemma2 上受架构（融合投影矩阵、MLP 后归一化）影响，"AlphaEdit does not seem like a universal drop-in solution"；编辑数从 3,000 扩到 10,000 后一般能力与拒答行为退化。AlphaEdit+（ACL Findings 2026，S）：新编辑与已存知识冲突时投影不稳。
- **定位与编辑脱钩**：见 §2.2 Hase；Makelov 把 rank-1 编辑与子空间错觉联系起来（A）。
- 对本候选：
  - （类比）Nullu / HalluSpace 是对权重做"幻觉子空间"的零空间投影，与 AlphaEdit 的投影在数学形式上相邻但目的不同（前者去掉一个子空间，后者保护一个子空间）。AlphaEdit 复现研究里"归一化层破坏线性假设""保证随规模失效"两点是否适用于 Nullu，未见检验。
  - （推导）静态编辑类修法的评测至少要报一般能力（非幻觉基准）与描述长度/召回；这一点在第 6 步对抗轮已有专门查询（6-6）。

## 2.7 Causal mediation / 头归因的统计稳定性

- Méloux et al.（2510.00845）F："circuit discovery is not a standalone task but a statistical estimation problem"；"The discovered circuits are highly sensitive to the experimental design choices"（原句在 PDF 中写作"experimental de-/sign choices"，跨栏）；建议做 bootstrap 重采样并报告稳定性指标；改变元分布（换数据集/改写）比 bootstrap 更稳。
- Miller et al.（A）、Hanna et al.（A）见 §2.2。
- Certified Circuits（2602.22968，ICML 2026）A：对概念数据集做有界编辑距离扰动，弃用不稳定部件，得到更小更准的回路。
- 检索片段（S）：ViT 上换种子重挖回路，稳定性随数据集大小单调上升（2604.14477）。
- Lookback Lens（F）：跨任务＋跨模型同时变时检测器无显著提升——头级读数的迁移是有条件的。
- 对本候选：
  - （推导）05 路已记："换种子重跑定位流程后部件重合率"在 36 篇 VLM 正文里未见；格式一变头排名相关从 0.82 掉到 0.12（2511.17254）。本步补上的是：文本侧已有把这件事当统计估计问题来处理的成套口径（bootstrap、Jaccard、弃权），VLM 幻觉头文献在"统计稳定性"这条轴上的水位低于文本侧。
  - （推导）TruthProbe 用 5 折交叉验证平均作头打分、并以无亲缘模型作零带，是目前取到的 VLM 相关工作里对头级读数稳定性交代最完整的一个。

## 2.8 线性探针本身（补充，头级"Truth Score"类读数的地基）

- Hewitt & Liang, *Designing and Interpreting Probes with Control Tasks*（1909.03368）A：探针准确率要与 control task 对照，用 selectivity 衡量探针是在读表示还是在记映射。
- 对本候选：（类比）逐头探针准确率（ITI、TruthProbe、DMAS 的选头依据）若没有 control task 或随机标签对照，头间排名里混有维度与范数的差异；TruthProbe 用跨谱系相关作了间接对照，没有 control task（grep 未见）。

---

# 检索日志

## 第 1 步查询清单（18 条）

1-1 truthfulness direction base LLM transfers to vision-language model hallucination "truth direction" VLM object hallucination linear probe same direction as text
1-2 VLM hallucination attention heads inherited from base LLM "context heads" OR "memory heads" knowledge conflict same heads text-only LLM comparison
1-3 "Textual Steering Vectors Can Improve Visual Understanding in Multimodal Large Language Models"
1-4 vision-language model hallucination "unknown entity" OR "entity recognition" SAE latents "Do I Know This Entity" visual object hallucination sparse autoencoder base LLM features
1-5 truth direction LLM does not generalize across tasks datasets "truthfulness" probe generalization failure negation multiple directions 2025 2026
1-6 audio large language model hallucination mechanistic interpretability attention heads text prior "audio" LLM object hallucination internal analysis language prior heads
1-7 video LLM hallucination mechanistic analysis attention heads language prior "video" large language model hallucination internal causal intervention heads
1-8 "Lookback Lens" OR "ALTI" OR "source contribution" applied to vision-language model hallucination image token contribution per-head attention ratio transfer across models
1-9 truth direction transfer across different LLMs cross-model universality truthfulness representation "across models" linear map probe transfer hallucination detection
1-10 "Dynamic Multimodal Activation Steering" hallucination truthfulness visual perception different attention heads arXiv
1-11 LVLM hallucination "parametric knowledge" FFN "copying heads" ReDeEP-style decomposition visual context vs parametric knowledge feed-forward attention heads vision-language
1-12 hallucination direction LVLM compared with text truthfulness direction cosine similarity "ITI" text-only statements probe transfers to image inputs multimodal truthfulness probe modality transfer
1-13 abstractive summarization hallucination mechanistic attribution "source contribution" OR "context attribution" attention heads parametric prior unfaithful generation internal localization LLM
1-14 VQA language prior bias attention heads analysis transformer "reasoning patterns" Kervadec VQA-CP question-only shortcut internal analysis visual question answering
1-15 Whisper hallucination attention heads "Calm-Whisper" decoder self-attention heads cause hallucination non-speech arXiv
1-16 same LVLM hallucination direction shared between text-only inputs and image inputs "modality-agnostic" truthfulness subspace base language model probe transfer multimodal hallucination detection cross-modal
1-17 Video-LLM hallucination "language prior" internal representation steering OR attention heads temporal hallucination mechanism video large multimodal model 2026
1-18 hallucinated objects in LVLM captions predictable by text-only language model without image "blind" LLM continuation co-occurrence prior analysis object hallucination language prior quantify

## 第 2 步查询清单（12 条）

2-1 sparse autoencoder trained on text LLM backbone applied to multimodal VLM residual stream transfer features "SAE" base LLM to VLM steering hallucination
2-2 applying sparse autoencoder features or steering vectors from one model to a different model architecture cross-model transfer steering vectors "different models" representation alignment critique
2-3 logit lens visual tokens VLM unreliable critique image token representations not aligned with vocabulary embedding space "logit lens" vision tokens limitation
2-4 circuit discovery stability across random seeds prompts "circuit" overlap variance mechanistic interpretability reliability statistical "stability" attention head attribution
2-5 steering vectors random direction baseline norm-matched control side effects general capabilities degrade "random vector" activation steering evaluation critique
2-6 "SAEs (usually) transfer between base and chat models" OR "sparse autoencoder" transfer fine-tuned model reconstruction degrade base model SAE on finetuned different backbone fails
2-7 model editing ROME MEMIT null-space projection side effects negative results "general abilities" collapse generalization failure evaluation pitfalls 2025
2-8 "negative results" sparse autoencoders downstream tasks linear probes outperform SAE out-of-distribution harmful intent detection DeepMind mechanistic interpretability team
2-9 activation patching Gaussian noise corruption out-of-distribution critique "counterfactual" patching unreliable localization causal tracing limitations mechanistic interpretability
2-10 AlphaEdit null-space projection model editing fails critique reproducibility "null space" editing side effects sequential editing limitations 2025 2026
2-11 attention weights head selection versus causal importance mismatch "attention" heads identified by attention ratio not causally important activation patching comparison vision-language OR LLM
2-12 SAE steering direction trained on LLaVA-NeXT applied to LLaVA-1.5 InstructBLIP different backbone residual stream transfer without alignment critique random direction control hallucination steering cross-model

另：约 45 篇是按已知 arXiv 号直接下载（不占检索条数），下载后以首页标题核对编号无误。

## 阅读层级清单

**F（30 篇；正文章节已核）**
- 第 1 步（18）：2606.15821、2503.10602、2505.14071、2310.06824、2407.12831、2307.00175、2602.20273、2310.15910、2402.18154、2407.07071、2212.08597、1809.02156、2603.06854、2606.18924、2505.12969、Anthropic *On the Biology of a Large Language Model*（transformer-circuits.pub/2025/attribution-graphs/biology.html）、2605.24977、2505.16146。
- 第 2 步（12）：2309.16042、2404.15255、2307.15771、2409.09951、2301.04213、2501.17148、2410.06981、2501.16615、2410.07149、2602.00462、2510.00845、2606.26783。
- 说明：这些是关键词定位式阅读（定点摘录 300–1100 字符窗口），不是通读。F 只表示所引的句子与数字所在章节核对过。

**A（37 篇；取到正文但只核对摘要/引言级陈述）**
- 第 1 步（19）：2306.03341、2212.03827、2304.13734、2407.08582、2410.02707、2604.03754、2506.00823、2411.14257、2410.11414、2411.07404、2310.04625、2208.05309、2301.07779、1712.00377、1612.00837、2104.03656、2602.21704、2512.18813、2603.10470（后两篇只读到引言片段）。
- 第 2 步（18）：2402.15390、2311.17030、2407.08734、2403.17806、2407.12404、2411.07213、2410.17245、2502.02716、2505.22637、2504.04635、2502.16681、2503.04429、2506.06609、2605.24946、2303.08112、2401.04700、2602.22968、1909.03368。

**S（只有检索片段，或已下载未读）**
- 已下载未读：2203.04212（ALTI）、2410.15999（SpARE）、2505.21800（From Directions to Cones）、2606.13216、2605.10622（Vocabulary Hijacking，取回后发现不是要找的 path-patching 论文）。
- 只有片段：Kissane et al. 论坛帖；DeepMind *Negative Results for SAEs*；"Shared Truth"（NeurIPS 2026 poster）；1911.03898；2104.00926；1905.04877；2305.10143；2608.11847；2604.04863；2602.22144（NoLan）；2502.12359（LanP / PDM-H）；2607.09156；2603.24543；2610.07722；2603.15518；AlphaEdit+（ACL Findings 2026）；2604.14477；2502.11367；EACL Findings 2026 的 SAE feature drift 论文；Logit Lens Loss 论文；2604.02486；2605.22903；AHEAD（ACL Findings 2026）；"path patching 五个 MLLM"预印本（编号未确认）。

**引自第一轮笔记、本轮未重取**：Yang et al.（ICLR 2025，hallucination heads）、2601.05201（PIH）、2605.13156（Dual-Pathway）、2511.17254（AllPath）、2410.02762（ProjectAway）。

## 检索过程中的事故与更正

- 16:3x 下载第二批时 /tmp 用户配额写满，13 篇下载失败。处理：改用自写的 `sub_d_scripts/fetchd.sh`（PDF 转文本后即删），并删除了我自己下载清单内 45 个编号的 `.pdf`（`.txt` 全部保留）。如果别的检索者恰好也下载过这 45 个编号中的 PDF，它们的 PDF 也被我删了，文本仍在。失败的 13 篇已全部重取成功。
- 我往 `papers/` 里写了 12 个 `<id>.h.txt`（arXiv HTML 流式文本，用于核对双栏断句）和 `anthropic_biology_2025.txt`，都是数据文件，不是脚本。
- 检索摘要工具把一篇 path-patching 论文错配到 2605.10622；已在 §1.5 说明，未采用其内容。
- 全部逐字引文（约 130 条）用 `sub_d_scripts/verify_quotes.py` 对下载文本做过归一化匹配，清单在 `sub_d_scripts/quotes*.tsv`；未通过的已改为转述或缩短为可匹配的片段。

## 没覆盖到的

- OpenReview 审稿讨论（SSL、VTI、Nullu、TruthProbe 的审稿意见里是否有人提过随机方向对照或跨骨干对齐问题）——没查。
- 在审稿件、未公开并行工作、非 arXiv（除一个 transformer-circuits 页面）、非英文文献——没查。
- 论坛/博客类一手来源（Kissane 帖、DeepMind 负结果帖）只到 S。
- 文本 LLM 真值方向文献只取了被点名的与检索返回的；RepE/LAT（Zou et al.）、SAPLMA 后续、Goldowsky-Dill 的 deception probe、"refusal direction"一线没取。
- ITI Table 3（随机方向对照的具体数字）、Jin et al. 的头数与效果数字、Calm-Whisper 之外的语音幻觉工作、Rohrbach §3 的汇总数字——没摘。
- 视频 LLM、摘要任务两处是"2 条 / 1 条查询未命中"，覆盖很薄。
- 第 2 步里 causal scrubbing、attribution patching（AtP*）、path patching 的专门局限文献没单独搜；"注意力权重选头 vs 因果选头"只有 1 条查询且全是 S。
- VTI、Nullu 原文本轮没有重读（由负责竞争者全景表的检索者读）；本文件里关于它们的话只到"方向/子空间类方法"这一层。
- 闭源模型内部无法验证；Anthropic 页面的对象是 Claude 3.5 Haiku 的替换模型。
- 知识截止影响：2026-06 之后的工作全靠本轮检索发现，漏检概率高于此前年份。

## 本步检验强度申报

第 1 步 18 条查询、第 2 步 12 条查询，合计 30 条；F 30 篇、A 37 篇（F 均为定点摘录式阅读，不是通读）。这是模板层与仪器层的检验，不是对 A4 对象层竞争者的检验；存活与否不由本文件判断。
