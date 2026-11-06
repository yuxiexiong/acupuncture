# 06 外领域形式化对象：可用来命名和测量 VLM 跨模型根因的概念

日期：2026-11-06。检索截至 2026-11。本文件按 00_BRIEF 的字段记录，另加 (a) 原学科的形式化对象与可测量、(d) 搬运时最可能断的假设。
阅读层级：F = 取到正文并核对了对应章节/表；A = 只读了摘要（含从正文 PDF 里只读摘要与模型清单的）；S = 只有检索片段。
推断档位：推导 / 类比 / 推测。不含等级或"值得做"的判断。

先说不利的部分：
- 七个概念里，**"形式化对象被搬过来 + 内部因果证据 + ≥2 个模型族"三项同时成立的只有绑定问题一个**（且三篇内部工作对内部成因的说法并不相同）。
- 线索整合的形式化对象（理想观察者权重、对数几率线性合并）2026 年下半年已被至少三篇搬到 VLM 上并做了定量拟合，但都停在行为层；"权重在内部哪里、能否改写"在这几篇里没有测量。
- 信号检测论的 d′/c 拆分在 VLM 上只找到两篇窄口径工作（一篇闭源单模型、一篇单一开源模型的工程任务）；POPE 类 yes-bias 文献里没检到用 d′/c 的（6 条查询，见日志）。
- 拥挤效应、变化盲视、注意瞬脱：在 VLM 上 0 命中（4 条查询），只能列入"未找到"。

---

## 概念 1：绑定问题（特征整合理论、错觉结合、容量限制）

### Takeaway
这是搬运最完整的一个：形式化对象（合取/析取搜索、feature triplets、feature entropy）被直接用来构造刺激并预测错误率；内部成因在 Qwen 系、LLaVA 系、InternVL、Gemma、Molmo 上都有测量，其中 position-ID 机制在 Qwen2.5-VL 与 LLaVA-1.5 上有激活修补的因果证据。但内部成因目前有三种并存的说法，修补后的改善幅度只有 4.6–11.1 个点。

### Cited Findings

**(a) 原学科的形式化对象与可测量**
- Treisman & Gelade (1980) 特征整合理论：单特征（disjunctive）搜索不随干扰物数量变差，合取（conjunctive）搜索随集合大小变差；注意被压缩时出现 illusory conjunctions（把 A 的颜色配到 B 的形状上）。可测量：搜索斜率（RT 或正确率对 set size）、错觉结合率、subitizing 上限（4–6 个）。Campbell 等把 "binding problem" 定义为 "a fundamental problem that arises when a shared set of representational resources must be used to represent distinct entities ... necessitating the use of serial processing to avoid interference"（F）— [Campbell et al. 2024, arXiv 2411.00238, 摘要](https://arxiv.org/abs/2411.00238)

**(b) 对应的 VLM 现象**
- 多物体场景下计数、视觉搜索、场景描述、视觉类比失败；错误随"共享特征的物体数"上升而不是单纯随物体数上升。

**(c) 已有搬运**

现象的跨模型证据
- Campbell et al.（NeurIPS 2024）：GPT-4v、GPT-4o、Gemini Ultra 1.5、Claude Sonnet 3.5 四个闭源模型上做合取/析取搜索、数量估计、场景描述；另加 4 个文生图模型做数量估计。合取搜索随物体数下降而析取不降；数量估计的容量上限"both fall within the subitizing limit of human vision"，且受 feature entropy 调制（低熵＝高干扰最差）。场景描述任务用 "feature triplet"（三物体中一对共享一个特征、另一对共享另一个特征）的个数量化干扰可能性，错误随 triplet 数上升（F，§2–§4，Fig.1–3）— [arXiv 2411.00238](https://arxiv.org/abs/2411.00238)
- 同文局限（逐字）："we primarily investigated propietary VLMs, for which we do not have detailed knowledge of the training data or architecture, or the ability to directly investigate internal representations"；LLaVA-1.5 "yielded very poor performance on all tasks"（F，§6.1）— [arXiv 2411.00238](https://arxiv.org/abs/2411.00238)
- 视觉搜索范式的另外三篇行为复现：GPT-4o / GPT-4-Turbo / Claude / Llama-3.2-Vision 上的 pop-out 与合取容量限制（A）— [arXiv 2510.19678](https://arxiv.org/abs/2510.19678)；用 reasoning tokens 当反应时类比，GPT-5.5 / o4-mini / Claude Opus 等，"feature search costs flat effort while conjunction effort climbs with set size"，但 target-present 斜率大于 target-absent，与人相反（A）— [arXiv 2606.25066](https://arxiv.org/abs/2606.25066)；人（n=1,250）对 MLLM，同一批刺激，错误率相关 ρ = 0.82，但 MLLM 在复杂搜索中出现极端的 present/absent 回答偏向（A）— [arXiv 2610.05463](https://arxiv.org/abs/2610.05463)

根因主张与内部证据（三条并存的说法）
1. **Position ID（空间索引）塌缩**：VLM 用内容无关的空间索引做绑定，由三类注意头实现（ID retrieval / ID selection / feature retrieval）；共享特征多（低熵）时 position ID 表征变差。CMA 在 Qwen2.5-VL-3B/7B/32B、Qwen2-VL、LLaVA-1.5-7B/13B、LLaVA-OneVision 七个模型上做；RSA 另含 Idefics2-8b。干预（把高熵条件下成功试次的 ID selection 头平均激活替换进低熵试次）后低熵场景描述正确率：LLaVA-1.5-7B 27.50%→32.10%（+4.60），LLaVA-1.5-13B 41.20%→51.60%（+10.40），Qwen2.5-VL-3B 69.00%→80.10%（+11.10），Qwen2.5-VL-7B 51.20%→62.30%（+11.10）；同模型高熵基线分别为 70.30 / 75.00 / 91.20 / 89.90%。证据级别：因果，2 个模型族（Qwen 系、LLaVA 系）（F，§4.5、Appendix D Table 1）— [Assouel et al., arXiv 2506.15871v2](https://arxiv.org/abs/2506.15871)
   - 同文：Qwen 系明显用相对位置编码，"The effects were less pronounced for models from the LLava family"（F，§3）；作者留的开口（逐字）："it is an open question whether the emergence of these mechanisms may be driven by architectural inductive biases ... or distributional aspects of the training data. We leave the investigation of these questions to future work."（F，Discussion）
2. **概念向量几何重叠（表征干扰）**：在 Qwen2.5-VL 7B、InternVL2.5 8B、Gemma 3 12B 上抽取颜色、形状、颜色-形状合取的 concept vectors；目标与最相似干扰物的余弦相似度与视觉搜索正确率的 Pearson 相关：target-present −0.90 / −0.90 / −0.97，target-absent −0.83 / −0.88 / −0.69（Qwen / InternVL / Gemma）。三模型的表征相似结构两两相关 r > 0.93。steering 验证向量因果有效（自然图像上 85–96%），但"几何重叠→搜索错误"这一步是相关。证据级别：相关，3 个模型族（F，§6 Table 4、§5 Table 3）— [Savietto, Campbell et al., arXiv 2602.07025v2](https://arxiv.org/abs/2602.07025)
   - 作者自认局限（逐字）："We analyzed only the vision output; language representations may account for unexplained failure modes. We characterized what representations look like but not how they are computed. A complete account requires tracing the underlying circuits."（F，Limitations）
3. **缺少串行处理；学会"指点"后出现内部搜索例程**：Qwen2.5-VL-7B 的物体表征更接近 compositional 而非 conjunctive 编码（RSA r = 0.9269 对 0.6278）；在 Molmo-7B 上用 causal mediation 找到第 19 层的 "search heads"，并称 "similar search heads emerge in other model families, such as Qwen2.5-VL"，消融后任务表现明显下降；微调学会 point-via-text 后 "eliminates binding errors"（F，§3–§4 摘读；附录 A.4 未读）— [Haputhanthri et al., arXiv 2605.25427](https://arxiv.org/abs/2605.25427)

不同论文对根因的说法是否一致
- 不完全一致。(1) 说失败点在空间索引的检索与选择；(2) 说失败点在视觉输出端特征方向的重叠，且明说只看了视觉输出；(3) 说根本原因是并行处理、修法是引入串行。三者同出一个作者群（Campbell / Webb 等），互相引用为相容，但没有一篇在同一批刺激上比较"position-ID 质量"与"概念向量重叠"各自解释多少错误。（推导：来自三篇各自的局限段落。）

竞争者（已有修法）
- Position-ID 修补（上文）：+4.6 到 +11.1 点，低熵条件修补后仍比高熵基线低 11–38 点（F）— [arXiv 2506.15871](https://arxiv.org/abs/2506.15871)
- VISER：在输入图上加低层空间结构（如水平线）并配顺序解析提示；GPT-4o 视觉搜索 +25.0%、计数 +26.8%、空间关系 +9.5%；"purely textual strategies, including Chain-of-Thought prompting, are insufficient and can even degrade performance"；模型含 GPT-4o、Claude Sonnet、Llama4、Qwen2.5-VL（A）；网页 https://sharif-ml-lab.github.io/VISER/ — [arXiv 2506.22146](https://arxiv.org/abs/2506.22146)
- Grounding IDs：解释外加视觉标记为何有效（标记在模型内诱导出跨模态的潜在标识符）（A）— [arXiv 2509.24072](https://arxiv.org/abs/2509.24072)
- 微调学会指点（上文 3）；Campbell 等提的方向是串行处理或 slot-based object-centric 表征，原文："none of these methods have yet been deployed at the scale of VLMs"（F，§6）— [arXiv 2411.00238](https://arxiv.org/abs/2411.00238)

便宜办法
- 纯文本提示（含 CoT）不足，可使表现变差（A，VISER 摘要）；改图（加结构）有效——即"换输入"能部分修，"换提示"不能。

数据与基准
- Campbell 等的 2D sprite / 3D 物体搜索、数量估计、场景描述集（合成，文中未核对公开地址）；Assouel 等的高/低熵网格集（2×2：1600 试次；3×3 另述，Appendix A.1.4，F）。

**(d) 最可能断的假设**
- 人类理论里"串行注意＝解法"依赖时间维度；VLM 的解码步、推理 token、指点坐标是否等价于串行注意，只有 2605.25427 一篇的 proof-of-principle（推导）。
- 人类 illusory conjunction 是在注意被压缩（短呈现、双任务）时测的；VLM 没有"呈现时间"这个旋钮，容量上限与人的 subitizing 范围重合可能来自别的原因（例如训练数据里小数目占多数）（推测）。
- FIT 假设特征图按维度分离（颜色图、形状图）；ViT patch token 是否有对应的分离结构未在上述文中检验（推测）。

### Inferences
- 绑定是七个概念里唯一满足"现象跨模型（闭源 4 + 开源 ≥5 个族）＋内部证据跨模型（因果：Qwen、LLaVA；相关：Qwen、InternVL、Gemma）"的（推导，依据上面各条 F）。
- 三种内部说法之间的相对解释份额没有被测过，这是对象层面的开口（推导：三篇的局限段落均未做此比较；我没有读 2605.25427 的附录，不排除其中有部分比较）。

### Gaps
- 2605.25427 附录 A.4（其他模型族的 search heads 与消融数字）未读；"similar search heads emerge in other model families" 的数字未核。
- 闭源模型的内部无法验证。
- 自然图像上的绑定错误与合成刺激上的机制是否同一，2506.15871 称 position ID 可推广到照片级图像，但对应的错误分析我没有核对。

---

## 概念 2：按可靠度加权的线索整合（Ernst & Banks、贝叶斯线索合并、因果推断）

### Takeaway
形式化对象已被搬过来并做了定量拟合：一篇把 VLM 的图文偏好写成对数几率的两参数线性合并并在未见降质组合上预测（R² 0.69–0.86），一篇用 cue-conflict 法量出各模型权重相对理想观察者的斜率（0.11–0.82）。它们都是行为层；"权重"没有被在内部读出或改写。内部因果工作（先验覆盖头、仲裁层、深度线索写回）存在且跨模型，但没有用线索权重的语言。

### Cited Findings

**(a) 原学科的形式化对象与可测量**
- 最大似然线索合并：合并估计 = Σ w_i·x_i，w_i ∝ 1/σ_i²；可测量：单线索噪声 σ_i（由单线索判别阈值得到）、冲突试次上读出的权重、合并后方差是否低于任一单线索。Ernst & Banks (2002) 是 2608.17205、2610.19407、2609.07474、2512.02719 共同引用的源（F，各文参考文献）。因果推断模型（先判断两线索是否同源再决定合并或分离）在 2609.07474 里作为人类规则被引用（"discard it only on inferring a separate source [124]"），没有在模型上拟合（F）— [arXiv 2609.07474](https://arxiv.org/abs/2609.07474)

**(b) 对应的 VLM 现象**
- 图文冲突时偏向文本（"blind faith in text"）或偏向视觉，各论文报告不一；图像与世界知识先验冲突时答先验；深度判断被图像平面线索带偏。

**(c) 已有搬运**

搬了形式化对象并做了测量（行为层）
- **两参数贝叶斯线索合并**：把联合偏好 s_J 写成 ŝ_J = π0 + β_T·e_T + β_V·e_V（e 为单模态 Bayes factor 的对数，π0 为先验对数几率），在 DocVQA / VQAv2 / RealworldQA 的冲突样本上，对 Qwen2.5-VL、Qwen3.5、Gemma3、GLM-4.6V 拟合；OOD 协议下 "R2 of 0.80–0.86 for both Qwen models and GLM-4.6V, and 0.69 for Gemma3"。干净输入下文本证据均值是视觉的 1.4–3.8 倍；integration bias β_T/β_V：Qwen3.5 与 GLM-4.6V 为 0.56–0.68（更重视觉证据），Gemma3 为 0.96–1.27，Qwen2.5-VL 为 1.06–1.45。作者据此解释"跟文本"可以与"更重视觉证据"并存（F，§4.2、§5 Table 3）— [Barua, Mahowald, Rudman, arXiv 2610.19407](https://arxiv.org/abs/2610.19407)
  - 局限（逐字）："the modality weights βT and βV are fitted empirically rather than derived from a normative account, because models differ in how they weight text and vision evidence in ways our framework does not yet predict"；"we extensively manipulate the supplied evidence but do not systematically manipulate prior beliefs independently of that evidence"（F，Limitations）
- **Cue-conflict 法 + 理想观察者斜率**：六个 VLM（Qwen2.5-VL-7B、Qwen3-VL-8B、Qwen3-VL-32B、InternVL3.5-8B、Idefics3-8B、Phi-4-multimodal），标尺上标记位置估计，图像可靠度与语句可靠度各 6 档。相对高斯理想的斜率：0.99、0.64、0.99、0.61、0.30、0.23（Qwen2.5-VL-7B 与 Qwen3-VL-32B 均为 0.99）；相对均匀似然理想的斜率降为 0.69、0.82、0.43、0.35、0.25、0.11（原文给出的顺序）。"Between 39 and 78% of the answers copy the stated interval’s midpoint exactly"——即单元格权重 0.3 常常是"多数试次抄文本、其余读图"的混合，而不是逐试次加权（F，§6.2）— [Xie & Alanwar, arXiv 2609.07474v3](https://arxiv.org/abs/2609.07474)
  - 作者自认（逐字）："The ideal-observer weights depend on the noise model assumed for the text cue, since a Gaussian and a bounded-uniform version differ in the fitted slopes by a factor of about 1.4. A Bayesian benchmark built from the models’ own priors and likelihoods failed a calibration check on nouns with no color prior ... four of the six vision-language models share a Qwen language backbone, while the two with other backbones read the ruler worst and fall furthest below the ideal."（F，局限段）
- **BayesBench**：九个模型（GPT-5 Mini、Claude 3.7 Sonnet、GPT-4o、Llama-4 Maverick、Mistral 24B、Qwen2.5-VL-32B、Gemini 2.5 Flash Lite、Gemma 3 4B、Phi-4 Multimodal），长度/位置/距离/时长估计，文本与图像两线索；用等权、拟合 α、逆方差加权三种基线比较，并定义 Bayesian Consistency Score。"GPT-5 Mini achieves perfect text accuracy but fails to integrate visual cues efficiently"（F，摘要、§3 Table 1、§4）— [Ma, Wang, Fountas, arXiv 2512.02719](https://arxiv.org/abs/2512.02719)
- **相对不确定度 + balance point**（未用线索整合的名字，但对象等同于心理测量函数的主观相等点）：LLaVA-1.5 系、LLaVA-1.6 系、Qwen-VL 系；text-following 概率随相对熵 ΔH_rel 单调变化，balance point = 50% 跟随点。"Qwen models possess a clear inherent vision preference (negative balance point), whereas LLaVA models have a neutral or text-leaning preference"。内部：logit-lens 逐层 top-1 在 balance point 附近"振荡"，LLaVA-1.6-7B 模糊区 1.43 次、"nearly double that of the clear region"。证据级别：相关，2 个模型族（F，§4–§5）— [Zhang et al., arXiv 2511.02243](https://arxiv.org/abs/2511.02243)
- **可读性降质下的再分配**：六个开源 VLM（Qwen2-VL-2B、Qwen2.5-VL-7B、LLaVA-1.6-Mistral-7B、LLaVA-OneVision-7B、Idefics3-8B、Phi-3.5-Vision），GSM8K/SVAMP 上五个模型更强烈地远离被降质的文本，ChartQA-Conflict（229 条）上六个模型方向反转。局限（逐字）："the remaining differences between arithmetic and ChartQA-Conflict prevent us from identifying a single causal mechanism"（F，摘要、Limitations）— [arXiv 2608.17205](https://arxiv.org/abs/2608.17205)

内部因果证据（未用线索权重的语言，但对象相同）
- **先验覆盖头**：Qwen-VL2.5 (3B, 7B)、LLaVA-NeXT 7B、PaliGemma (3B, 10B) 三个族；"visual grounding emerges by default, whereas prior grounding depends on a small set of causally necessary attention heads (2.5–4.8%) concentrated in the second half of the network"；消融后 68–96% 的先验答案翻为视觉答案，视觉答案只变 0.8–7.5%。路由实现在族间不同："Qwen-VL and LLaVA-NeXT redistribute attention between image and text tokens, whereas PaliGemma routes through ..."。证据级别：因果，3 个模型族。局限（逐字）："the measured asymmetry may partly reflect how the two prompts are routed rather than arbitration between perception and memory alone"（F，摘要、§3、Limitations）— [Lietzow et al., arXiv 2606.28273v2](https://arxiv.org/abs/2606.28273)
- **Encoding–Grounding Dissociation**：十个 VLM（LLaVA-v1.5、LLaVA-Next、LLaVA-OneVision、Qwen2-VL、InternVL2 等，7B–72B）；答错的样本里视觉属性同样可线性解码（AUC > 0.86），最终层 logit 差与落地结果相关 ρ = 0.847；全序列激活修补改变 60–84% 的输出，"image tokens carry almost all of the causal impact"；早层 steering 最多 +3.8%。证据级别：因果，≥3 个模型族（F，摘要、§2、Limitations）— [Nooralahzadeh et al., arXiv 2604.09364](https://arxiv.org/abs/2604.09364)
- **PvP steering**：LLaVA-Next、Qwen2-VL、Janus-Pro；平均把 99.3% 的颜色预测、80.8% 的大小预测从先验翻到反事实图像（F，摘要、Limitations）— [Golovanevsky et al., arXiv 2505.17127](https://arxiv.org/abs/2505.17127)
- **图像内部的线索冲突（深度 vs 图像平面线索）**："eleven VLMs from five families"（正文出现的模型名含 Qwen3-VL-4B/8B/32B、InternVL3-8B/38B、Gemma-4-12B/31B、LLaVA-OneVision-1.5-8B / 2-8B、SpaceThinker-Qwen2.5VL-3B；五个族的完整划分我没有逐一核表）；渲染场景垂直位置冲突下 Qwen3-VL-8B 降到 42.8%、LLaVA-OneVision-1.5-8B 降到 7.4%；同一前向里物体级深度读出在 Qwen 上 99.0% 正确而回答只有 42.8%；把模型自己的深度读出写回物体 token 可纠正部分冲突判断，但"The effect is mixed or negative for InternVL3 and Gemma-4, and cue-consistent accuracy often decreases"。证据级别：相关（解码）跨 5 族；因果（写回）在 Qwen3-VL 与 LLaVA-OneVision 上成立、其余混合（F，§3、§4、§5.2、Limitations）— [Zou & Marttinen, arXiv 2610.17976](https://arxiv.org/abs/2610.17976)
- **视听 LLM 的视觉支配**：Qwen2.5-Omni 3B 为主，附录称在 Qwen3-Omni、Video-LLaMA、MiniCPM-o 上验证；音视频冲突时音频理解下降最多 56%；中间层音频信息可探针读出；attention knockout 屏蔽深层的视觉通路后音频推理恢复。证据级别：因果，主实验单模型（附录未读）（F，摘要、§3、§6、§9）— [arXiv 2604.02605](https://arxiv.org/abs/2604.02605)

不同论文对根因的说法是否一致
- "偏文本"是不是模型的固有偏置，说法不一：2511.02243 把数据集层的差异归为单模态不确定度分布 + balance point；2610.19407 说强文本跟随可以与接近 1 的 integration bias 并存，差异主要来自证据强度；2609.07474 指出相当比例是"抄文本"与"读图"的混合而非逐试次加权。三者对"权重"这个量的操作定义不同（平衡点位置 / β_T:β_V / 冲突试次读出的权重）。（推导）
- 先验 vs 图像：2606.28273 说视觉落地是默认、先验需要专门的头；2604.09364 说问题在仲裁而非编码；2505.17127 说早层反映先验、中后层转向视觉。方向相容但强调点不同，未见在同一数据上的对比。（推导）

竞争者（已有修法）
- 头消融、PvP steering、深度写回、attention knockout（均见上）；改善幅度与副作用各文自述：2604.09364 早层 steering 最多 +3.8% "with degrading performance in some setups"；2610.17976 写回在一致条件上常降分。

便宜办法
- 2609.07474："The measured weights shift with the prompt’s wording, so the prompt is part of the stimulus"；去掉"合并两个来源"的指令后斜率仍为 0.71、0.58、0.52、0.21、0.29（五个模型）（F）。2610.17976：空间微调的 SpaceThinker 在两种冲突下只有 51.8% 与 32.4%（F）。

数据与基准
- BayesBench（公开，摘要称 release）；ChartQA-Conflict（229 条）；Visual CounterFact；WHOOPS!。

**(d) 最可能断的假设**
- 理想观察者要求各线索噪声条件独立且（通常）高斯；文本线索在 VLM 里不是带噪测量而是符号陈述，2609.07474 实测换噪声模型斜率差约 1.4 倍，2610.19407 自述对数似然差与后验对数几率"is approximate"（推导，来自两文局限）。
- 人类线索合并是逐试次的连续加权；VLM 的"权重"可能是两种离散策略（抄文本 / 读图）在试次间的混合比例（推导，依据 2609.07474 的 39–78% 抄中点）。
- 人类的可靠度由感觉噪声决定；VLM 的"可靠度"与单模态任务难度、表面形式（渲染文字 vs 图表）纠缠，2608.17205 的方向反转即是例子（推导）。

### Inferences
- 这一概念的形式化对象在行为层已被占：两参数合并律、理想观察者斜率、一致性分数都已发表（推导）。
- 行为层的"权重"与内部因果工作里的"先验头 / 仲裁层 / 写回方向"之间没有检到把两者接起来的论文（对象层；本概念下查询 5 条 + arXiv API 1 条，见日志）。这是检索范围内的观察，不是"没人做过"的断言。
- 2610.19407 的作者 Rudman 同时是 2606.28273 与 2505.17127 的作者，这个接法离该团队很近（推测：只依据作者重合）。

### Gaps
- 2503.02199（Words or Vision，CVPR 2025）已下载未读，文中只通过他文引用。
- 因果推断（common-cause）模型是否被拟合到 VLM：未检到（1 条 arXiv API 查询 + 1 条 WebSearch）。McGurk 只检到 AV-HuBERT 对 44 名被试的比较（arXiv 2601.15869，S），不是 LLM 类模型。
- 2604.02605 附录里其他 AVLLM 的数字未核。

---

## 概念 3：信号检测论（敏感度 d′ 与判据 c 的拆分）

### Takeaway
把"说 yes"拆成 d′ 与 c 的做法在 VLM 上检到两篇正文：一篇在 Gemini-3.1-Pro 上表明直接追问下的"检出"主要是判据向 yes 移动；一篇在 Qwen2.5-VL-7B 上用激活 steering 把 c 移动 −1.515 而 d′ 未改善。两篇各只有一个模型做了 SDT 拆分。POPE 类 yes-bias 文献用 yes-ratio / precision / recall，没有检到 d′/c；yes-bias 的内部解释至少有三种。

### Cited Findings

**(a) 原学科的形式化对象与可测量**
- 等方差高斯 SDT：d′ = z(H) − z(FA)，c = −[z(H) + z(FA)]/2；两者数学上独立——改变收益结构移动 c 不改 d′，降低刺激质量降低 d′ 不移 c。扩展：不等方差模型、z-ROC 斜率、meta-d′（F，引言）— [Cacioli, arXiv 2603.14893](https://arxiv.org/abs/2603.14893)

**(b) 对应的 VLM 现象**
- 是/否题上偏向回答 yes（POPE 等）；追问"有没有看到 X"时的虚报；过度保守（不肯判"危险"）。

**(c) 已有搬运**

搬了形式化对象并做了测量
- **非注意盲视 + SDT**（medRxiv 预印本）：实验 1 在 20 个模型配置上（OpenAI：GPT-4o、GPT-4o-mini、GPT-5.4、GPT-5.4-mini；Anthropic：Claude Sonnet 4/4.6、Opus 4/4.7；Google：Gemini 2.5 Flash、3 Flash、2.5 Pro、3.1 Pro）做胸部 CT 大猩猩静态图；实验 2 在 Gemini 3.1 Pro 上带无大猩猩对照臂。SDT 表（合并 n = 24/臂）：任务内自发报告 1/24 对 0/24，d′ = 0.50，c = +1.80；q1 含蓄追问 15/24 (62%) 对 4/24 (17%)，d′ = 1.22，c = +0.31，Holm 校正 p = 0.011；q2 "unusual" 20/24 对 16/24，d′ = 0.50，c = −0.66。原文："what looks like “detection” at q3 / primed is largely yes-bias"。d′ 与 c 用 loglinear 边界校正（Hautus 1995）。证据级别：行为，SDT 拆分只在一个闭源模型上（F，§2.6、Table 1、§4.5）— [Raymond et al., medRxiv, PMC13308084, doi:10.64898/2026.06.16.26355792](https://europepmc.org/articles/PMC13308084)
  - 局限（逐字）："With n = 12 per cell in Exp 2 (n = 24 pooled across framings), confidence intervals on each probe-level contrast are wide; only the q1 effect survives Holm correction at α = 0.05."
- **判据可被内部方向移动**：Qwen2.5-VL-7B-Instruct 的两阶段震害评估流水线，基线 "flags only 27.0% of genuinely unsafe buildings ... an SDT criterion of c = +1.354, despite adequate evidence quality (d′ = 1.521)"；注入在情绪场景上定位的 fear 方向后 Red 召回升到 75.7%（p < 0.001），"The mechanism is a shift in criterion (Δc = −1.515) while discrimination is not improved (Δd′ = −0.493)"；范数匹配的随机方向（p = 0.46）与 happiness 方向（p = 0.84）无显著效应。证据级别：因果，单模型。局限（逐字）："The clearest limitation is scope. The experiments use one backbone, one affect corpus and one building benchmark"；测试集 65 例，"only one of 24 macro-F1 comparisons survives multiplicity correction"（F，摘要、§5.3）— [Zhou, arXiv 2610.11986](https://arxiv.org/abs/2610.11986)
- **文本 LLM 上的完整参数化 SDT**（不是 VLM，作为方法先例）：三个 LLM、168,000 试次的事实判别；检验"温度＝判据移动"的类比，结果是类比部分失效——"temperature simultaneously increasing sensitivity (AUC) and shifting criterion"；各模型都表现出不等方差证据分布。原文称完整参数框架（"unequal-variance model fitting, criterion estimation, z-ROC analysis"）此前未被用于 LLM（F，摘要与引言；这是该文作者的单方陈述）— [arXiv 2603.14893](https://arxiv.org/abs/2603.14893)

没用 SDT 语言、但对象相近的 yes-bias 内部解释（相互竞争）
1. **System 注意力冗余**：LLaVA-1.5 7B（附 LLaVA-NeXT-Vicuna 7B、LLaVA-1.5 13B；Qwen2-VL 在附录 A.6 "critically evaluated"），把后层 system token 的注意力因果地重分配给图像与文本后 yes-bias 大幅下降。证据级别：因果，主体为一个模型族。局限（逐字）："Our work focusses on LLaVA-based architectures ... The generality of our system-mediated account should therefore be tested on a broader variety of VLM families"；"our claims regarding representation-level mechanisms should be further validated through directly probing a model’s internal states"（F，§3、Limitations；附录 A.6 未读）— [Chan et al., arXiv 2601.12430, ACL 2026 Findings](https://arxiv.org/abs/2601.12430)
2. **语言先验**：无图输入时答案分布已偏；用仿射校准使无图时各答案得分均匀（Post-Hoc Debias）（A）— [arXiv 2403.05262](https://arxiv.org/abs/2403.05262)；LLaVA-1.5、InstructBLIP、mPLUG-Owl2 上 yes-ratio 在数据集间严重不平衡，能量解码平均把 yes-ratio gap 降 8.81%、准确率 +4.82%（A）— [arXiv 2507.07731](https://arxiv.org/abs/2507.07731)
3. **读数协议产物**：POPE 上用哪组 yes/no token 读 logit 单独就能把 LLaVA-1.5-7B 的 adversarial F1 移动 6.13 点，"exceeds the adversarial gain reported by five of the six papers we surveyed"；并报告答错的样本比答对的样本得到更多图像注意力（Cohen’s d = −0.46，p = 1.4 × 10⁻²⁴），"the opposite of what grounding-based corrections assume"；另在 3 个 tokenizer 族的 4 个 VLM 上确认协议层混杂（A，摘要；正文表格未核）— [arXiv 2610.25964](https://arxiv.org/abs/2610.25964)

- 视觉搜索里的回答偏向：人与 MLLM 比较中 "MLLMs exhibited extreme present/absent response biases in complex searches"（A）— [arXiv 2610.05463](https://arxiv.org/abs/2610.05463)
- 把幻觉分成"敏感度失败 / 判据失败"的框架性论述（文本层面的提法，S，未读正文）— [Machine Psychometrics, arXiv 2605.23952](https://arxiv.org/abs/2605.23952)

不同论文对根因的说法是否一致
- 不一致，且层级不同：system 注意力（部件层）、语言先验（训练偏置层）、读数 token（测量层）。2610.25964 的"错答样本图像注意力更高"与"图像注意力不足导致幻觉"一类主张直接相左（竞争解释，A 级）。

竞争者（已有修法）
- 注意力重分配（2601.12430）、仿射校准 / VDD（2403.05262）、能量解码（2507.07731）、fear 方向 steering（2610.11986）。前三者以 accuracy / F1 / yes-ratio 报告，没有报告修后 d′ 是否变化——即没有回答"修的是判据还是敏感度"（推导：依据摘要与所读章节；三文正文表格未逐表核对）。

便宜办法
- 2610.25964 称在固定基线上试了 9 种推理时修正，"none beat it"（A）。

数据与基准
- POPE（MSCOCO，random / popular / adversarial 三切分，公开）；HallusionBench；SeisMLLM-1K 测试切分 65 例。

**(d) 最可能断的假设**
- SDT 假设每个试次有一个标量证据变量，判据是加在其上的阈值。VLM 的 yes/no 是 logit 差，但读数依赖 token 集合（2610.25964），"证据轴"本身不唯一（推导）。
- 等方差高斯假设：文本 LLM 上已实测为不等方差（2603.14893），d′ 与 c 在不等方差下不再独立，需要多判据点的 ROC（推导）。
- "判据问题可由一个偏置项修"要求偏向在刺激间是常数位移；POPE 三切分的 yes-rate 随切分变化（S：LLaVA v1 的 0.759 / 0.804 / 0.860，来自 arXiv 2609.27890 的检索片段），提示偏向与负样本类型相关，可能不是纯判据（推测）。
- 人类实验用收益矩阵移动 c；LLM 上对应的旋钮（温度）已被实测同时改变敏感度（推导，2603.14893）。

### Inferences
- "POPE 类幻觉主要是判据问题而不是敏感度问题"这句话，在检索范围内没有找到跨模型的 d′/c 证据支持或否定（结论层；SDT 相关查询 4 条 WebSearch + 2 条 arXiv API）。已有的两篇正文证据各是一个模型、非 POPE 任务。
- 现成材料：多篇缓解论文公布了混淆矩阵（S：arXiv 2605.04641 的 LLaVA-1.5-7B POPE-Popular 假阳性 274→120），可直接换算 d′/c，无需新实验（推导）。

### Gaps
- 2610.25964、2507.07731、2403.05262 只读了摘要；它们的修后混淆矩阵未核。
- 2607.02575（Criterion-Conditional In-Context Learning）与 2609.05761（GeoContext）只见标题，未读。
- 闭源模型无法做内部验证；PMC 一文是 medRxiv 预印本，未经同行评审。

---

## 概念 4：Stroop 干扰与认知控制（自动化不对称、冲突适应）

### Takeaway
行为层的搬运面很广（一篇测了 47 个 VLM，一篇 13 个），内部证据只到单模型：InternVL 3.5 4B 上用 SAE 找到一个冲突调制的 supernode、消融后 Stroop 错误上升；另一篇只在 CLIP 嵌入空间做了几何与 steering。

### Cited Findings

**(a) 原学科的形式化对象与可测量**
- Stroop 范式：不一致试次相对一致试次的代价（congruency effect）；读词比命名颜色更自动化，故干扰不对称；冲突适应（Gratton 效应）＝前一试次不一致时本试次的冲突代价变小。可测量：一致性效应大小、序列效应（iI − cI）。2510.24804 摘要："A signature of human cognitive control is conflict adaptation: improved performance on a high-conflict trial following another high-conflict trial."（A）— [arXiv 2510.24804](https://arxiv.org/abs/2510.24804)

**(b) 对应的 VLM 现象**
- 图中文字压过视觉属性（typographic 干扰）；被明确指示报告颜色时仍读词。

**(c) 已有搬运**
- 47 个 VLM、4,410 个任务、七种冲突范式（Stroop、Flanker 与五个现实变体）："VLMs exhibit robust congruency effects across all tasks, with larger models systematically resolving conflicts more effectively than smaller models"；模型含 InternVL2/3、Qwen2/2.5-VL、Llama-3.2-Vision 等。证据级别：行为（A）— [Wang, Li et al., arXiv 2505.18969](https://arxiv.org/abs/2505.18969)
- 序列 Stroop：13 个 VLM 中 12 个表现出与冲突适应一致的行为（例外归因于天花板）；在 InternVL 3.5 4B 上用 SAE 找到文字与颜色的部分重叠 supernodes，"their relative sizes mirror the automaticity asymmetry between reading and color naming in humans"；第 24–25 层一个冲突调制 supernode 消融后 "significantly increases Stroop errors while minimally affecting congruent trials"。证据级别：因果，单模型（A）— [Hu, arXiv 2510.24804](https://arxiv.org/abs/2510.24804)
- CLIP、SigLIP-2 与六个生成式 VLM（Qwen2-VL-7B、LLaVA-1.5/1.6、BLIP-2、InstructBLIP、InternVL-2.5 等）的 Stroop 基准；CLIP 嵌入空间里 "word identity is encoded along stronger and more separable directions than ink color"，沿词方向 steering 有效、沿颜色方向远不如。局限（逐字）："Due to limited computational resources, embedding-level interventions were conducted only ..."（句子后半未摘全；摘要表明干预只在 CLIP 图像嵌入上做）。代码 https://github.com/NurbukeTeker/vlm-stroop-conflict（A + 局限段首句 F）— [arXiv 2610.12650](https://arxiv.org/abs/2610.12650)
- 字体识别的 Stroop 式变体：few-shot 与 CoT 几乎无帮助（S）— [arXiv 2503.23768](https://arxiv.org/abs/2503.23768)

不同论文对根因的说法是否一致
- 2610.12650 把偏向归于编码器嵌入几何（词方向更强）；2510.24804 把控制定位在 LLM 后层的一个 supernode。一个在编码器、一个在语言骨干，未见对比（推导）。

竞争者 / 便宜办法
- 2610.12650 摘要：明确指示报告颜色仍偏向词，"until the “word” is no longer legible"（A）。2503.23768：提示工程几乎无效（S）。

**(d) 最可能断的假设**
- 人类 Stroop 的核心量是反应时与练习造成的自动化；VLM 没有反应时，"自动化"只能用表征强度或模型规模替代（类比）。
- 冲突适应在人类里要求跨试次的控制状态；VLM 的"跨试次"是同一上下文里的前文，效应可能来自 in-context 模式匹配（推测）。

### Inferences
- 现象跨模型成立（47 与 13 个模型，A 级）；根因的跨模型证据未达到 BRIEF 的"≥2 个模型族"线（因果证据单模型，另一篇在 CLIP 上）（推导）。

### Gaps
- 三篇都只读了摘要与模型清单；2505.18969 的"demand-resource relationship"具体量化未核。

---

## 概念 5：工作记忆干扰/衰减，与信息论口径的"视觉信息随生成被稀释"

### Takeaway
"长生成中图像被遗忘"已有信息论口径的形式化（M3ID 的 prompt dependency measure、MemVR 的互信息随深度递减定理、C-PMI），但这些形式化主要用来给解码方法立据，内部测量基本是注意力占比曲线；认知心理学的工作记忆范式（n-back、前摄/倒摄干扰）被搬到 VLM 上的两篇都是行为层，且结论是"模型的干扰图样与人不同"。

### Cited Findings

**(a) 原学科的形式化对象与可测量**
- 信息论：互信息 I(Y; C | X)、数据处理不等式（Markov 链上互信息不增）。认知心理学：n-back 的 d′ 随 n 下降（容量）；前摄干扰（旧学习干扰新记忆）对倒摄干扰（新学习干扰旧记忆）；遗忘来自相似痕迹竞争而非单纯衰减。M3Eval 原文："Forgetting arises from competition among similar memory traces rather than simple decay."（F，相关工作 "Memory Investigation in Cognitive Psychology" 段）— [arXiv 2606.05008](https://arxiv.org/abs/2606.05008)

**(b) 对应的 VLM 现象**
- 描述越长，后段幻觉越多；对图像 token 的注意随生成步下降（"visual forgetting" / "fading memory" / "visual consistency decay"）。

**(c) 已有搬运**

信息论口径
- **M3ID**：定义 visual prompt dependency measure，PDM(y<t; c|x) ≜ dist(p(·|y<t, x, c), p(·|y<t, x))；"PDM-H decreases as more tokens are generated, indicating that the visual information gets diluted"，称为 "conditioning dilution or fading memory effect"；图示在 LLaVA 上、MS COCO 验证集。证据级别：相关（输出分布层面的量），所核对的图为单模型（F，§1、§3、Fig.3）— [Favero et al., arXiv 2403.14003](https://arxiv.org/abs/2403.14003)
- **MemVR**：Theorem A.1（逐字）"Assume that each Transformer layer acts as a deterministic or stochastic mapping with the Markov property. Then, the mutual information between the hidden states and the visual features decreases with depth"；修法是在中后层 FFN 重新注入视觉 token；实验模型含 LLaVA-1.5、Qwen-VL、GLM-4V、LLaVA-Next。证据级别：论证（定理）+ 行为（F，Appendix A；实验表未逐项核）— [arXiv 2410.03577](https://arxiv.org/abs/2410.03577)
- **C-PMI 校准解码**：把幻觉缓解写成条件互信息最大化；该文对前人的评语（逐字）："only M3ID [21] considers theoretical aspects, yet it introduces mutual information solely to justify its ..."（句尾未摘全）；模型 LLaVA-1.5、InstructBLIP、Shikra、LLaVA-NeXT（F，引言与相关工作）— [arXiv 2505.19678](https://arxiv.org/abs/2505.19678)
- **VIF**：测量图文相关随生成长度的变化，称 "visual consistency decay"；加一个模块维持视觉依赖；LLaVA-1.5、Qwen2.5-VL、mPLUG-Owl3（F，引言）— [arXiv 2605.18160](https://arxiv.org/abs/2605.18160)
- **PID Flow**：用 partial information decomposition 把每层的预测信息拆成冗余、视觉独有、语言独有、协同四部分；LLaVA-1.5-7B 与 LLaVA-1.6-7B（一个模型族）（A）— [arXiv 2602.15580](https://arxiv.org/abs/2602.15580)

注意力口径（内部读数）
- **CAAC**：用 relevancy 分析，图像 token 对输出 token 的相关度随生成长度下降；模型 InstructBLIP、LLaVA-NeXT、LLaVA-1.5 等。证据级别：相关，≥2 个模型族（F，§3 "Analysis: Decaying attention to image tokens"）— [arXiv 2505.21472](https://arxiv.org/abs/2505.21472)
- **LASER**：称 visual forgetting 主要来自两个被忽视的因素——"early-stage attention decay disrupts evidence acquisition, and attention concentration on a subset of task-irrelevant visual sink tokens"；用两种训练奖励修；主要在 Qwen2.5-VL-7B（A）— [arXiv 2607.01707](https://arxiv.org/abs/2607.01707)

工作记忆范式（行为）
- 空间 n-back：Qwen2.5 与 Qwen2.5-VL，文本渲染与图像渲染配对；"models show reliably higher accuracy and d’ with text than with vision"；名义 2/3-back 的表现 "often fails to reflect the instructed lag and instead aligns with a recency-locked comparison"；网格大小改变近期重复结构从而改变干扰与错误图样。单模型族（A）— [arXiv 2602.04355](https://arxiv.org/abs/2602.04355)
- M3Eval（视频）：GPT-5.4、Gemini-3.1-Pro、Qwen3.5、Qwen3-VL、InternVL3.5 等；"humans exhibit notably stronger retroactive interference than proactive interference, whereas multi-modal models demonstrate comparable interference levels. This contrast indicates a fundamental difference in memory mechanisms between humans and models."（F，§1；n-back 部分的"不随 N 衰减、随符号总数 K 下降"来自检索片段，S）；代码与数据 https://pku-value-lab.github.io/m3eval-homepage — [arXiv 2606.05008](https://arxiv.org/abs/2606.05008)

不同论文对根因的说法是否一致
- 不一致：(i) 后段注意力衰减（CAAC 等）；(ii) 早段注意力衰减 + sink token（LASER，明确说前人把它当 "late-stage attention decay problem"）；(iii) 层深方向的互信息递减（MemVR，轴是"层"不是"生成步"）；(iv) RoPE 位置衰减（FarSight，arXiv 2505.16652，S）。注意 (iii) 与 (i)(ii) 是不同的轴——"在哪一层"与"在哪一步"不能互推。

竞争者（已有修法）
- M3ID（对比无图分布的解码）、MemVR（重注入）、C-PMI（token 净化）、VIF（加模块需训练）、CAAC（注意力校准）、LASER（后训练奖励）。作者自认局限：MemVR "A primary challenge resides in the complex task of identifying the optimal hyperparameters"（F，附录 Limitations）。

便宜办法
- 未找到直接检验"换提示能否修长生成遗忘"的正文证据。

**(d) 最可能断的假设**
- MemVR 的定理要求层间是 Markov 链；带残差连接且每层都能重新注意图像 token 的解码器不满足"下一层只依赖上一层隐藏状态"这一条件，图像 token 在每一层都可被重新读取（推导：由 Transformer 注意力结构得出，非该文自述）。
- 认知心理学的"衰减"假设痕迹随时间被动变弱；VLM 的图像 token 一直在上下文里、原样可取，M3Eval 的行为结果（不随时间间隔衰减、随条目数下降，S）与"检索竞争"相容而与"存储衰减"不相容（类比）。
- PDM 测的是输出分布对图像的依赖度，下降既可能是"忘了图"，也可能是后段 token 本来就更由语言决定（功能词、延续句式）；需要按 token 类型标定零分布（推测）。

### Inferences
- 这个概念下，信息论对象已被搬运但多为方法立据（C-PMI 对 M3ID 的评语即此意）；跨模型的内部因果证据（修补/消融后遗忘曲线按预期改变，≥2 族）在所读章节里没有看到（推导；相关查询 2 条 WebSearch）。
- 各文的"遗忘"定义落在三条不同的轴上（生成步、层深、位置距离），目前没有检到把三者放在同一量纲下比较的工作（对象层，2 条查询）。

### Gaps
- 2607.01707、2602.04355、2602.15580 只读摘要；LASER 的"causal analysis"具体做法未核。
- FarSight（2505.16652）、Vision Inference Former 的定量表未核。
- 这一概念与其他检索者的"幻觉/注意力"线路可能重叠，这里只记录形式化对象的搬运状况。

---

## 概念 6：传感器融合中的尺度失配与校准（模态接口处的范数差）

### Takeaway
"模态间尺度失配"在 VLM 上有直接测量：视觉 token 的 L2 范数比文本嵌入高一到两个数量级，在 LLaVA-1.5、Qwen2.5-VL、KimiVL、GLM-4.1V 上都存在；但该文用的形式化是 Pre-Norm 残差动力学，不是控制/机器人里的传感器标定或协方差加权，修法只在 LLaVA-1.5 上重训验证。传感器融合的形式化对象本身未检到被搬运。

### Cited Findings

**(a) 原学科的形式化对象与可测量**
- 传感器融合（卡尔曼滤波 / 加权最小二乘）：各传感器读数按噪声协方差的逆加权，前提是各通道已标定到同一量纲（增益、偏置、时间对齐）。可测量：通道增益比、残差的白化程度、协方差一致性检验。（此条为学科常识陈述，本次未取外领域综述正文核对。）

**(b) 对应的 VLM 现象**
- 细粒度视觉感知弱、跨模态融合效率低；该文未把它绑定到某一个具体失败基准上，而是报告整体基准提升。

**(c) 已有搬运**
- **范数差的测量**：视觉编码器输出平均 L2 范数——CLIP-ViT-L/14 29.30 ± 17.12、SigLIP-SO-400m 71.78 ± 13.95、SigLIP2 59.37 ± 106.08、MoonViT 72.17 ± 7.13；文本嵌入——Qwen2.5-7B 0.80、Qwen3-8B 1.38、Llama3.2-3B 1.09（Table 1）。投影器前后（Table 2，按 PDF 文本顺序读出，列序 LLaVA-v1.5 / Qwen-2.5-VL / KimiVL / GLM-4.1V）：投影前 28.71 / 3484.24 / 137.93 / 47.44，投影后 39.96 / 56.88 / 4.78 / 4.58，文本 1.08 / 0.86 / 0.85 / 0.80。原文："a substantial disparity between visual and text token norms persists in all analyzed models"。证据级别：相关（测量），4 个模型（F，§3 RQ1–RQ2；Table 2 的列对应关系是我从抽取文本顺序推定的，LLaVA 一列与检索片段一致）— [Li et al., arXiv 2512.08374, ICLR 2026 poster](https://arxiv.org/abs/2512.08374)
- **根因主张**：Pre-Norm 架构下高范数视觉 token 有 "representational inertia"，逐层语义变化比文本 token 慢（用相邻层余弦相似度作代理，RQ3）。修法：投影器后插入一个按文本嵌入平均范数初始化增益的 LayerNorm，"Experiments conducted on the LLaVA-1.5 architecture"，多模态基准与 MMLU 均提升。证据级别：理论论证 + 相关测量跨模型；因果（改结构重训）只在 LLaVA-1.5（F，摘要、§3）— 同上
- 相邻：输入空间的 modality gap（SEA，arXiv 2408.11813；LLaViT，arXiv 2511.10301）均为 S。

不同论文对根因的说法是否一致
- 未检到对"范数差导致视觉信息损失"的直接反驳或替代解释；同文自己指出带内部 norm 层的投影器（KimiVL、GLM-4.1V）压缩了范数但差距仍在，"simply inserting a normalization layer within the projector is not a guaranteed solution"（F）。

**(d) 最可能断的假设**
- 传感器融合假设通道间的尺度差是需要消除的标定误差；在 Pre-Norm Transformer 里每个子层输入先过归一化，范数差对注意力打分的影响被部分抵消，剩下的影响走残差更新的相对步长——所以"尺度失配"在这里是动力学量而不是静态标定量（推导，依据该文自己的理论设定）。
- 该文观察到 Qwen-2.5-VL 的文本嵌入范数被"系统性抬高"以被动补偿——说明训练本身会做一部分"标定"，失配量与训练程度有关而非纯结构量（推导，来自原文 §3）。

### Inferences
- 这是一个"可测量存在、外领域形式化未搬运"的概念：范数比是现成的跨模型量，但它与具体失败现象（哪个基准、哪类题）之间的因果联系只有一个模型上的重训结果（推导）。
- 推理时直接重缩放视觉 token 范数（不重训）能否改变行为，在所读章节里没有看到（方法层，1 条查询）。

### Gaps
- 附录 C（Qwen 系文本嵌入范数抬高的细节）未读；Table 2 的列对应需对照 PDF 版式复核。
- 没有取控制/机器人领域的综述正文来核对 (a)。

---

## 概念 7：非注意盲视（attentional set / 任务设定抑制报告）

### Takeaway
"窄任务指令下不报告明明能报告的显著物"在闭源模型上被两篇独立工作测到，其中一篇强调必须配无目标对照臂和 SDT 才能解释；没有任何内部证据，也没有开源模型上的机制工作。

### Cited Findings

**(a) 原学科的形式化对象与可测量**
- Simons & Chabris 的"看不见的大猩猩"与 Drew 等的放射科版本：在高负荷主任务下对意外刺激的报告率，对比开放指令下的报告率；Drew 范式里 83% 的放射科医师未报告。可测量：focused 条件与 open 条件的报告率差（within-item gap）。— [arXiv 2606.26529 引言](https://arxiv.org/abs/2606.26529)；[PMC13308084 摘要](https://europepmc.org/articles/PMC13308084)

**(b) 对应的 VLM 现象**
- 被要求"数结节 / 评估结节"时不报告同图中的安全关键异常；同一对象在开放描述下能报告。

**(c) 已有搬运**
- 放射文本情景与胸部影像任务，七个模型；"ordinary focused instructions suppressed reporting by up to 0.92; the gap ranged from minimal to complete across seven models, did not vary monotonically with scale"；视觉研究用 claude-haiku-4-5、gpt-4o-mini、gpt-4o、claude-sonnet-4-6：star 条件下 closed 报告率 0.00（gpt-4o）、0.00（gpt-4o-mini）、0.50（haiku）、0.54（sonnet）；一个独立的开放式 critic 在 24 情景探针里恢复了全部遗漏。证据级别：行为，闭源（F，摘要、结果段）— [Shin, arXiv 2606.26529](https://arxiv.org/abs/2606.26529)
- 20 个配置、三家厂商；"Gemini configurations cluster at 85–92% detection; the OpenAI family sits between 60–77%; the Anthropic Claude-4 generation sits at 8–17%"（primed-L2 水平）；任务指令对 primed 指令的差在 2024 模型为 +64 个百分点、2026 模型 +26 个百分点（F，§3）— [Raymond et al., PMC13308084](https://europepmc.org/articles/PMC13308084)

根因的跨模型证据：未找到（无内部测量）。

便宜办法
- 换成开放指令或加一个开放式 critic 即可恢复（2606.26529）——这是"换提示能修"的一类，按 BRIEF 应归入不那么"干净"的失败。

**(d) 最可能断的假设**
- 人类非注意盲视是知觉层面未进入意识；模型这里更像指令服从（只报告被问到的），2606.26529 自己称之为 "a failure of report under an attentional set"。是否"没看见"需要内部读数区分，行为上不可辨（推导）。

### Inferences
- 现象跨闭源模型成立但模型间差异极大（0.00 到 0.54），且换提示可修；根因证据为"未找到"（推导）。

### Gaps
- 开源模型上是否复现、内部是否仍编码了被抑制对象：未检到（1 条 WebSearch + arXiv API 无直接命中）。

---

## 只有类比或行为描述、没有检到形式化测量与内部证据的概念

### Takeaway
拥挤效应、变化盲视、注意瞬脱在 VLM 上未检到任何论文；Weber 定律、来源监控有行为测量但无内部证据；因果推断式（common-cause）整合模型与传感器标定只作为类比出现。

### Cited Findings
- **拥挤效应（crowding，Bouma 定律）**：arXiv API 查询 `abs:"visual crowding" AND (vision-language OR multimodal)` 返回 3 条，均不相关（PRISM、DiMo-GUI、V*）；WebSearch 2 条只返回人类视觉与 2017 年 CNN 工作（Volokitin et al., NeurIPS 2017，S）。在 VLM 上：未找到（对象层，4 条查询，清单见文末日志 WebSearch 4、8、13、19 与 arXiv API Q1）。
- **变化盲视（change blindness）**：arXiv API 0 条；WebSearch 2 条只返回人类研究与一个 change captioning 基准（C3-Bench，arXiv 2606.25445，S，测的是描述变化而非漏检变化）。未找到（对象层，3 条查询）。
- **注意瞬脱（attentional blink）**：arXiv API 0 条；WebSearch 1 条无命中。未找到（对象层，2 条查询）。
- **Weber 定律 / 数量知觉**：检索片段称在 ViLT、BLIP-2、GPT-4V、Gemini 等上，多数模型的误差图样不符合 Weber 定律（S，非逐字，未取正文核对）— [arXiv 2402.03328](https://arxiv.org/abs/2402.03328)；NumerosityVLM 做了逐层探针，称数量信息在早期 patch 表征可检出、部分模型在输出阶段快速退化（S）— [arXiv 2608.15425](https://arxiv.org/abs/2608.15425)。两篇都只有检索片段。
- **来源监控（source monitoring，认知心理学）**：11 个 VLM 上测"模型能否追踪信息来自哪个模态"，作者把它当作绑定问题的一个实例；结论是句法与语义信号都起作用、模态分布差异大时语义信号占上风。行为层（A）— [Hua et al., arXiv 2604.22038, COLM 2026](https://arxiv.org/abs/2604.22038)
- **因果推断式多感官整合（先判同源再合并）**：2609.07474 把它当人类规则引用，未在模型上拟合（F）；McGurk 效应只检到 AV-HuBERT 与 44 名被试的比较（S）— [arXiv 2601.15869](https://arxiv.org/abs/2601.15869)
- **"VLMs are blind"**（重叠圆、相交线等低层几何失败）：常被与拥挤/敏锐度类比，但原文未用心理物理形式化（S，已下载未读）— [arXiv 2407.06581](https://arxiv.org/abs/2407.06581)

### Inferences
- 拥挤效应在原学科有干净的定量律（临界间距 ≈ 0.5 × 离心率），而 ViT 的 patch 网格没有离心率概念——搬运时"离心率"这个自变量没有对应物，可能是它没有被搬的原因之一（推测）。
- 变化盲视与注意瞬脱都依赖时间呈现（闪烁、RSVP）；静态图 VLM 没有对应旋钮，视频 VLM 才有（推测）。

### Gaps
- 以上"未找到"均限于 arXiv 摘要字段与通用网页检索；CogSci / CCN 会议论文集、VSS 摘要没有单独检索。

---

## 检索日志

**查询条数**：WebSearch 19 条（其中 2 条 extended 模式）+ arXiv API 摘要字段查询 13 条 = 32 条。

WebSearch 查询清单
1. binding problem vision language models feature integration illusory conjunctions arXiv
2. vision language model modality conflict cue combination reliability weighting Bayesian arXiv 2025
3. signal detection theory hallucination vision language model sensitivity criterion response bias d-prime
4. visual crowding vision language models psychophysics change blindness attentional blink VLM
5. McGurk effect multimodal LLM audio-visual conflict causal inference model
6. visual token norm mismatch text tokens LLaVA connector scale misalignment modality gap MLLM
7. POPE yes bias LVLM hallucination "signal detection" criterion sensitivity decomposition arXiv
8. "crowding" OR "change blindness" multimodal large language models benchmark arXiv GPT-4o LLaVA
9. emergent symbolic mechanisms vision language models position IDs binding causal mediation arXiv 2025
10. visual forgetting long generation LVLM attention decay image tokens hallucination increases with length information bottleneck
11. Stroop effect typographic vision language models interference cognitive control mechanistic arXiv
12. VLM working memory capacity limit visual n-back multi-object interference cognitive science vision language models
13. vision-language models "crowding" flankers eccentricity human-like psychophysics VLM letters arXiv 2025 2026
14. "change blindness" vision-language models GPT-4o Gemini detect changes flicker paradigm arXiv
15. VLM yes/no hallucination "d'" OR "d-prime" OR "response criterion" OR "decision threshold" bias calibration object existence LLaVA "acquiescence"
16. information-theoretic visual information flow MLLM mutual information image tokens decays generation "information bottleneck" hallucination arXiv
17. psychophysics vision language models Weber's law numerosity "serial position" OR "primacy" multi-image position bias mechanistic
18. （extended）"signal detection theory" "vision-language" OR "multimodal" model object hallucination yes-bias sensitivity versus bias separate threshold POPE 2025 2026
19. （extended）"inattentional blindness" OR "attentional blink" OR "visual crowding" large vision-language models experiment GPT-4V LLaVA Qwen

arXiv API（export.arxiv.org，abs 字段，按提交日期倒序，每条取前 12–14 条）
- Q1 "visual crowding" × VLM/multimodal（3 条，均不相关）
- Q2 "change blindness" × VLM（0）
- Q3 "attentional blink" × LM/VLM（0）
- Q4 "signal detection theory" × VLM/MLLM（2）
- Q5 "illusory conjunction" × VLM/multimodal（0；说明相关论文摘要不用这个词）
- Q6 "cue combination" / "cue integration" / "cue-conflict" × VLM/MLLM（9）
- Q7 Stroop × VLM/MLLM/multimodal（7）
- Q8 "binding problem" × VLM/MLLM（7）
- Q9 "psychometric function" / psychophysics × VLM（10）
- Q10 "response bias" / "decision criterion" / "d-prime" × VLM/MLLM（4）
- Q11 "working memory" × VLM × interference/capacity（2）
- Q12 "feature integration" / "conjunction search" / "pop-out" × VLM/MLLM（14）
- Q13 McGurk / multisensory × language model × conflict/integration（7，均不相关）

**取到正文并核对了章节或表的论文（F，26 篇）**
其中标 * 的 13 篇只核对了摘要、模型清单与局限/结论段（或单个定理/单段），未逐表核数字。
1. arXiv 2411.00238 Campbell et al., Binding Problem（NeurIPS 2024）
2. arXiv 2602.07025 Savietto et al., Geometry of Representational Failures
3. arXiv 2506.15871 Assouel et al., Visual symbolic mechanisms
4. arXiv 2605.25427 Haputhanthri et al., Binding Visual Features Point by Point *
5. arXiv 2609.07474 Xie & Alanwar, Where Should Language Sit
6. arXiv 2610.19407 Barua et al., Biased Bayesian Observers
7. arXiv 2512.02719 Ma et al., BayesBench *
8. arXiv 2511.02243 Zhang et al., When Modalities Conflict
9. arXiv 2608.17205 Ghosh et al., Which Source Wins *
10. arXiv 2610.17976 Zou & Marttinen, Seeing Depth but Choosing Cues
11. arXiv 2606.28273 Lietzow et al., Vision-Default, Prior-Override *
12. arXiv 2604.09364 Nooralahzadeh et al., Arbitration Failure *
13. arXiv 2505.17127 Golovanevsky et al., Pixels Versus Priors *
14. arXiv 2604.02605 Selvakumar et al., Do AVLLMs Really See and Hear *
15. PMC13308084 / doi:10.64898/2026.06.16.26355792 Raymond et al., Looked but didn't see（medRxiv）
16. arXiv 2610.11986 Zhou, FearCaut-Qwen *
17. arXiv 2603.14893 Cacioli, LLMs as Signal Detectors（文本 LLM）*
18. arXiv 2601.12430 Chan et al., System-Mediated Attention Imbalances
19. arXiv 2606.26529 Shin, The inattentional gap
20. arXiv 2606.05008 Huang et al., M3Eval *
21. arXiv 2403.14003 Favero et al., M3ID
22. arXiv 2410.03577 MemVR *
23. arXiv 2505.21472 CAAC
24. arXiv 2605.18160 Vision Inference Former *
25. arXiv 2505.19678 C-PMI *
26. arXiv 2512.08374 Li et al., The Unseen Bias

**只读摘要（A，16 篇）**（多数是下载了 PDF 但只读了摘要与模型清单）
arXiv 2509.24072、2506.22146、2604.22038、2510.19678、2606.25066、2610.05463、2507.07731、2403.05262、2610.25964、2603.18373、2610.12650、2510.24804、2505.18969、2602.04355、2607.01707、2602.15580

**只有检索片段或只见标题（S）**
arXiv 2402.03328、2608.15425、2407.06581、2406.16851、2503.23768、2503.02199（已下载未读）、2605.23952（已下载未读）、2607.02575、2609.05761、2601.15869、2505.16652、2408.11813、2511.10301、2609.27890、2605.04641、2606.25445

**没覆盖到的范围**
- CogSci / CCN 论文集、VSS 摘要、Journal of Vision 等非 arXiv 来源没有单独检索；PubMed 只碰巧命中一篇。
- OpenReview 审稿讨论没有取（任务建议源之一，未做）。
- 非英文文献未检索。
- 在审与并行未公开工作不可见；2026-10 的几篇 arXiv（2610.*）均为 v1 预印本，未经评审。
- 闭源模型的内部成因无法验证；概念 1、3、7 的部分跨模型现象证据只在闭源模型上。
- 文中出现的若干模型名（GPT-5.6-Luna、Gemini-3.5-Flash、Qwen3.5、Gemma-4、Claude Opus 4.7/4.8 等）晚于我的知识截止，按论文原文照录，未独立核实其存在与规格。
- 外领域经典综述（Treisman & Gelade 1980、Ernst & Banks 2002、Macmillan & Creelman 2005、Bouma 1970）没有取正文，(a) 项里的形式化对象来自上述 VLM 论文的转述与学科常识。
- 下载的 PDF 与抽取文本留在 /home/ubuntu/tmp_of/dl，可用于复核逐字引文。
