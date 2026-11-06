# 第 5 步 引用链挖掘 + OpenReview 审稿（分工 C）

完成时间：2026-11-06 约 17:20 UTC。候选对象："VLM 的物体幻觉通路"——偏文本的中深层注意力头 / 双通路 / 线性方向与子空间（VTI、Nullu、SSL）/ 视觉 token 局部化（ProjectAway）。

本笔记只做记录，不给等级、分数或"值得做"。文中逐字引文共 39 条，全部用脚本在下载的正文里做过第二次匹配（`/tmp/a4_audit/sub_c_scripts/verify.py`，39/39 命中；匹配时归一了空白、行尾连字符与弯引号）。

## 0. 坏消息先说

1. **任务 B 没有交付：OpenReview 审稿正文一条都没取到。** `api2.openreview.net/notes/search` 能用（拿到了 forum id）；`api2.openreview.net/notes?forum=<id>` 对五个 forum 全部返回 `403 ChallengeRequiredError "Challenge verification required"`。这是站方的人机验证，我没有去过它，也没有换别的端点套同样的内容，也没有拿二手摘要顶替。第 4 节只有 forum id。
2. **被引扫描是标题层的。** S2 被引 346 条（8 篇种子合计，有重叠）逐条看过标题，归类凭标题；真正取正文读过对应章节的只有 7 篇，另 10 篇只读摘要，3 篇综述只读了 grep 定位到的段落。
3. **S2 的被引数明显偏少且有噪声**：Dual-Pathway 5 条里 4 条与本题无关，Role-Break 0 条，AllPath 11 条；Nullu 的 70 条里混着 2 篇早于 Nullu 的论文。最新三篇种子的被引侧基本是空的——"最新种子之后有没有人做直接比较"这一问，这一步答不了。
4. **综述对这些机制主张的"评价"没找到**：三篇综述（2404.18930、2501.01346、2507.19024）里 grep 到的只是罗列与转述，没有比较或质疑；三篇都没有检出 Yang 的 hallucination heads。
5. Google Scholar 没试；WebSearch 只跑了 2 条。

## 1. 各种子论文：被引与参考文献扫描条数

| 种子 | S2 被引（条数 = 逐条看过标题的条数） | OpenAlex 被引 | 参考文献（从缓存正文读） |
|---|---|---|---|
| Yang et al. ICLR 2025（S2 id `4dc1fbde…2589`，无 arXiv 号） | 62 | 未取到（OpenAlex 标题检索不到该条目） | 约 45 条，全部看过 |
| Dual-Pathway 2605.13156 | 5 | 4 | 40 条，全部看过 |
| AllPath 2511.17254 | 11 | 0（两条记录） | 87 条，全部看过 |
| Nullu 2412.13817 | 70 | 15 | 57 条，关键词过滤后看（23 条命中） |
| ProjectAway 2410.02762 | 129 | 10 | 42 个条目块，关键词过滤后看 |
| Role-Break 2607.29412 | 0 | 0 | 约 35 条，全部看过 |
| VTI 2410.15778（加项） | 63 | 11 | 未系统读 |
| SSL 2505.16146（加项） | 6 | 3 | 只查互引 |
| 合计 | **346**（有重叠） | **43** | — |

原始 JSON：`/tmp/a4_audit/sub_c_data/s2_<id>_citations.json`、`oa_cites_<id>.json`。

### 1.1 种子之间的互引（正文 grep；行引用列；0 = 未检出）

| 行＼列 | Yang | DualPath | AllPath | Nullu | ProjectAway | VTI | Devils 2411.16724 | VHD 2412.13949 | SPIN 2505.16411 | Rudman 2601.05201 | Neo 2410.07149 | FCCT 2511.05923 | CausalMM |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Yang | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Dual-Pathway | 0 | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 引 | 引 | 引 | 0 |
| AllPath | 引 | 0 | – | 0 | 0 | 0 | 引 | 0 | 0 | 0 | 0 | 0 | 引 |
| Nullu | 0 | 0 | 0 | – | 0 | 引 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ProjectAway | 0 | 0 | 0 | 0 | – | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Role-Break | 0 | 0 | 0 | 0 | 0 | 0 | 引 | 引 | 引 | 引 | 0 | 0 | 0 |
| SSL | 0 | 0 | 0 | 0 | 引 | 引 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

读法（推导档，依据就是上表）：四条根因说法的代表作彼此基本不互引。Dual-Pathway 不引 Yang、AllPath、Nullu、VTI、ProjectAway；Role-Break 同样一篇都不引；AllPath 不引任何线性方向类。**在这 6 篇种子的参考文献这一层，没有检出把"头 / 双通路 / 线性子空间 / 视觉 token 局部化"放在一起的工作**（一层、6 份参考文献表；被引侧见第 2 节）。grep 用标题片段与作者名，断词可能漏计。

### 1.2 种子自己的对照与局限（顺手核到的）

- Dual-Pathway（F，摘要/§3/§4/附录 A）：有随机部件对照——"we include a random control that applies the uniformscaling factor to the same number of randomly selected components"（原文断词如此）；模型为 Qwen3-VL-8B、LLaVA-v1.6-7B、Llama-3.2-Vision-11B、InternVL3-8B/14B；评测 POPE-adversarial 与 AMBER；摘要："validate that the same circuit selectively transfers to relational but not attribute hallucination"。正文未检出 "Limitations" 小节。
- AllPath（F，附录 E）：局限逐字 "However, we do not investigate what causal pathways are most effective for different types of questions, nor do we explore training strategies that could systematically improve the use of such pathways." 全文 "random" 的前 12 处都是 POPE random 子集或随机抽图，**未检出随机头对照**。
- Yang（F，附录 A.1）：有零消融 vs 均值消融、概率 vs 对数概率的敏感性分析和样本数敏感性；MiniGPT-4 上复做了头定位；参考文献里未见与其他根因说法的比较。

## 2. 筛出的五类清单

层级：**F** = 取到正文并读了所列章节；**A** = 只读摘要（含取到正文但只读摘要）；**S** = 只有标题。S 级的归类只凭标题，可能归错。

### (i) 直接比较或统一多种根因说法

没有检出在同一模型同一协议下把四种说法并排比较的工作（层次：对象层；依据：346 条 S2 被引标题 + 43 条 OpenAlex + 6 份参考文献表 + 2 条 WebSearch）。最接近的是下面这些"各自提出一个统一口径"或"拆分错误来源"的：

| 工作 | arXiv | 年 | 来源 | 为什么相关 | 层级 |
|---|---|---|---|---|---|
| Causal Evidence for Attention Head Imbalance in Modality Conflict Hallucination（MACI） | 2605.19250 | 2026-05 | Yang、AllPath 被引 | 五个 MLLM 上 path patching，分出 hallucination-driving 与 hallucination-resisting 两组头；把 Yang、VHD、AllPath 并列为"head-level methods"并说明区别。任务是 modality conflict（MMMC），不是 POPE/CHAIR | F（摘要、§1、§2、结论与局限） |
| The Evidence Anchoring Boundary | 2610.12981 | 2026-10 | Yang 被引 | 同一个 visual-residual 编辑按深度逐层施加，量"在哪还有杠杆"；presence/attribute/relation 三类题；六个检查点三族 | F（摘要、§1、§3.2） |
| Encoded but Unused: Bounding the Sources of VLM Errors | 2610.29241 | 2026-10 | ProjectAway 被引 | 把错误拆成表示失败与利用失败并给上下界；LLaVA-1.6-7B、Qwen2.5-VL-7B；属性题 | A |
| When Prompts Override Vision（基准名 HalluScope） | 2604.21911 | 2026-04 | Yang、VTI 被引 | 用基准分摊"视觉骨干不足 vs 语言主导"的相对重要性 | A |
| DO-Bench | 2604.22822 | 2026-04 | SSL 被引 | 把物体存在题的错误归到 prior override 或 perception limited | A |
| What Makes LVLMs Hallucinate Less? | 2605.30911 | 2026-05 | Nullu 被引 | 架构三维度 × 三类幻觉；把注意力/解码/改权重归为 component level | A |
| Mitigating Hallucinations in LVLMs via Causal Route Gating | 2605.24024 | 2026-05 | Yang、AllPath 被引 | 标题与检索片段：按步门控 text-route 头 | S（papers 有缓存） |
| The Truth Stays in the Family: … Inherited Truthful Heads in Model Lineages | 2606.15821 | 2026-06 | Yang 被引 | 头在模型谱系间继承 | S（有缓存） |
| D-LEAF: Layer-to-head Attention Diagnostics | 无号 | 2025 | Yang 被引 | 层到头的定位 | S |
| Tracing and Mitigating Hallucinations in Multimodal LLMs via Dynamic Attention Localization | 2509.07864 | 2025-09 | Yang、Nullu 被引 | 动态定位 | S |
| Causally-Grounded Dual-Path Attention Intervention（AAAI 2026） | 2511.09018 | 2025-11 | WebSearch | 另一个"dual-path" | S |
| DARE: Dual-path Auto-Regressive-aware Editing | 2609.36440 | 2026-09 | Nullu、ProjectAway 共同被引 | "dual-path" 编辑 | S |
| Overthinking Causes Hallucination: Tracing Confounder Propagation（CVPR 2026） | 2603.07619 | 2026-03 | ProjectAway 被引 | 另一种根因说法 | S（已下载未读） |
| Revealing Perception and Generation Dynamics in LVLMs | 2512.18813 | 2025-12 | ProjectAway 被引 | 感知/生成两阶段 | S |
| A Comprehensive Information-Decomposition Analysis of LVLMs（ICLR） | 2603.29676 | 2026-03 | ProjectAway 被引 | 信息分解 | S |
| Arbitration Failure, Not Perceptual Blindness | 2604.09364 | 2026-04 | ProjectAway 被引 | 仲裁失败说 | S（vl03 有缓存） |
| Vision-Default, Prior-Override（EMNLP 2026） | 2606.28273 | 2026-06 | ProjectAway 被引 | 感知–知识冲突的因果机制 | S |
| Same Task, Different Circuits（NeurIPS 2025） | 2506.09047 | 2025-06 | ProjectAway 被引 | 同任务不同模态回路 | S |
| CausalLens: Sensitivity-Guided Multi-Head Causal Intervention（CVPR 2026） | 未查到 | 2026 | Role-Break 参考文献 | 多头因果干预 | S |
| GeoPID: Decomposing and Steering Visual Information in VLMs | 2610.08401 | 2026-10 | VTI 被引 | 分解 + 转向 | S |
| Causal Probing for Internal Visual Representations in MLLMs | 2605.05593 | 2026-05 | VTI 被引 | 因果探针 | S |

### (ii) 否定或限定这些说法

| 工作 | arXiv | 年 | 来源 | 限定了什么 | 层级 |
|---|---|---|---|---|---|
| **HaloProbe** | 2604.06165 | 2026-04 | Yang、AllPath、ProjectAway 三家被引 | "幻觉词图像注意力更低"在按 token 位置、首次/非首次提及分层后反转或消失（Simpson's paradox）；点名 Devils in Middle Layers | F |
| **Targeting the Attention Heads Behind Object Hallucination in LLaVA**（COLM 2026 Actionable Interpretability Workshop） | 2608.24966 | 2026-08 | Yang 被引 | 在 LLaVA-1.5-7B 上重走 Yang 式"诊断→定点"并补随机头对照与定长预算分析；自述 CHAIR 增益里混着"说得更少" | F |
| **Prior Directions** | 2607.26913 | 2026-07 | Yang、Nullu、ProjectAway 被引 | 配对打乱对照的子空间修复 59/66，匹配构造 60/66；识别最好的子空间不等于行为上唯一有效。任务是 GUI grounding，不是物体幻觉 | F |
| **Where Hallucinations Live: A Cross-Architecture Circuit in VQ-Tokenized VLMs** | 2609.29048 | 2026-09 | VTI 被引 | 25 个模型 8 个 LLM 族；称既有机制研究"typically as single-model case studies"、既有修法"evaluated almost exclusively on binary benchmarks"；其回路只在 VQ 族成立 | F（摘要、§1、局限开头） |
| **Mechanisms of Prompt-Induced Hallucination in VLMs**（Rudman et al.） | 2601.05201 | 2026-01 | Dual-Pathway、Role-Break 参考文献 | 三个 VLM 上头级消融；"model-specific ways"——头的作用方式跨模型不同。任务是计数的 prompt-induced hallucination | F（摘要、§1、对照段） |
| Beyond Logit Lens（NAACL 2025） | 2411.19187 | 2024-11 | ProjectAway 被引 | logit lens 对动作、OCR、空间关系、属性比较类幻觉不够 | A |
| MESA: Mitigating Entangled Steering | 2604.07914 | 2026-04 | Nullu 被引 | latent steering 让输出变短、token 分布偏移 | A |
| Beyond Global Editing | 2608.09344 | 2026-08 | Nullu、VTI 被引 | 单一全局子空间对所有样本一视同仁 | A |
| MPD（ACL 2026） | 2604.20366 | 2026-04 | Nullu、VTI 被引 | representation-based 方法损伤通用生成能力 | A |
| Beyond Attention Imbalance（FLASH） | 2609.37263 | 2026-09 | AllPath 被引 | 认为"注意力失衡"之外另有两种模式（Perceptual-Semantic Dissociation、Localized Fixation） | A |
| System-Mediated Attention Imbalances Make VLMs Say Yes（ACL 2026） | 2601.12430 | 2026-01 | Yang 被引 | POPE yes 偏置的另一个解释（system prompt 介导） | S（papers 有缓存） |
| Beyond Language Priors: Diagnosing and Fixing Visual-Origin Hallucinations | 2609.00231 | 2026-08 | VTI 被引 | 视觉来源的幻觉，对"语言先验主导"的限定 | S |
| Analyzing and Mitigating Object Hallucination: A Training Bias Perspective（AAAI） | 2508.04567 | 2025-08 | VTI 被引 | 训练偏置说 | S |
| Cohesion: Consensus-Based Hallucination Subspace Estimation（ICIP 2026） | DOI 10.1109/icip61757.2026.11630364 | 2026 | Nullu、VTI 被引 | 标题指向子空间估计需要共识 | S |
| Looks the Same, Answers Differently: Flip-Direction Steering | 2609.28851 | 2026-09 | VTI 被引 | 标题 | S |
| LatentLens | 2602.00462 | 2026-01 | ProjectAway 被引 | 限定 logit lens 对视觉 token 的可读性 | S（有缓存） |
| The Explainability Illusion: Must ViTs Exhibit Patch-Decoding Interpretability? | 2610.25289 | 2026-10 | ProjectAway 被引 | 标题 | S |
| Not Every Mention Is a Claim | 2610.23610 | 2026-10 | ProjectAway 被引 | 检测口径 | S（已下载未读） |
| Same Attention, Different Truths（CVPR 2026） | 2608.07302 | 2026-08 | ProjectAway 被引 | 标题 | S（有缓存） |
| Where Do Long Captions Fail? Position-Aware Diagnosis | 2610.31111 | 2026-10 | Yang 被引 | 位置因素（与 HaloProbe 的混杂变量同向） | S |
| When Do Frozen VLMs Respond to Image-Free Object-Token Edits? | 2609.03429 | 2026-09 | ProjectAway 被引 | **读摘要与引言后判为不相关**（遥感、自训 projector 的 object-token 测试台） | A |

没有检出"复现失败"类的论文（层次：对象层；依据同上 346+43 条标题）。

### (iii) 在新模型族上复做定位

| 工作 | arXiv | 模型（逐字或正文所见） | 层级 |
|---|---|---|---|
| Dual-Pathway（种子） | 2605.13156 | Qwen3-VL-8B、LLaVA-v1.6-7B(Mistral)、Llama-3.2-Vision-11B、InternVL3-8B/14B | F |
| AllPath（种子） | 2511.17254 | LLaVA-v1.5-7B、Qwen-VL-Chat；附录 C.3 "Additional Results of Qwen2.5-VL on POPE" | F（附录目录） |
| Evidence Anchoring Boundary | 2610.12981 | "Our base checkpoints are LLaVA-1.5-7B/13B, Qwen2.5-VL-7B, and InternVL3.5-8B"；另 LLaVA-NeXT-34B、Qwen2.5-VL-32B | F |
| Where Hallucinations Live | 2609.29048 | 25 个模型 8 个 LLM 族；VQ 族（VILA-U、Liquid、Chameleon、Lumina-mGPT 等），对照含 LLaVA-1.6、Qwen2.5-VL | F（摘要/引言） |
| Rudman et al. | 2601.05201 | LLaVA-OneVision、Qwen-VL、Janus-Pro（对照段所见） | F |
| MACI | 2605.19250 | "five open-source MLLMs"，具体名单未核（参考文献含 Qwen3-VL technical report） | F（名单未核） |
| Encoded but Unused | 2610.29241 | LLaVA-1.6-7B、Qwen2.5-VL-7B | A |
| Before the Token Commits: Trajectory-Level Benchmarking of Visual Hallucinations in Diffusion VLMs | 2609.34772 | 扩散式 VLM | S |
| Role-Break（种子） | 2607.29412 | 参考文献含 Qwen3-VL；定位在哪些模型上做未核 | S |

Gemma3、Pixtral：346 条标题里没有出现这两个名字（标题通常不写模型名，不能当作"没有"）。

### (iv) 用于属性 / 关系 / 多图 / 视频幻觉

| 工作 | arXiv | 来源 | 类型 | 层级 |
|---|---|---|---|---|
| Dual-Pathway | 2605.13156 | 种子 | 关系迁移、属性不迁移（摘要逐字见 1.2） | F |
| MACI | 2605.19250 | Yang、AllPath 被引 | 贡献段："ablating object-identified driving heads also reduces hallucination on attribute/relation conflicts" | F |
| Evidence Anchoring Boundary | 2610.12981 | Yang 被引 | presence/attribute/relation；"universal subtraction is neutral or harmful" | F |
| Encoded but Unused | 2610.29241 | ProjectAway 被引 | 属性 | A |
| Beyond Logit Lens | 2411.19187 | ProjectAway 被引 | 动作、OCR、空间关系、属性比较 | A |
| Mitigating Hallucination in VideoLLMs via Temporal-Aware Activation Engineering（NeurIPS） | 2505.12826 | Yang 被引 | 视频 | S |
| Relaxing Anchor-Frame Dominance … Video LLMs | 2604.12582 | ProjectAway 被引 | 视频 | S |
| CircuitProbe（Video LMs） | 2507.19420 | ProjectAway 被引 | 视频 | S |
| VideoHallu（NeurIPS） | 2505.01481 | ProjectAway 被引 | 视频 | S |
| When Thinking Drifts: Evidential Grounding for Robust Video Reasoning（NeurIPS） | 2510.06077 | VTI 被引 | 视频 | S |
| Subspace Entropic Contrastive Decoding for Faithful Video Temporal Grounding | DOI 10.1145/3767308.3836515 | Nullu 被引 | 视频 | S |
| Discovering Compositional Hallucinations in LVLMs（NeurIPS 2025） | 无号 | AllPath 被引 | 组合 | S |
| ChainMPQ（ICLR） | 2510.06292 | ProjectAway 被引 | 关系 | S |
| From What to Which: Decoding Modifier Grounding | 2610.12305 | ProjectAway 被引 | 属性/修饰语 | S |
| Who Is Left of Whom? | 2609.35486 | ProjectAway 被引 | 空间关系 | S |
| The Dual Mechanisms of Spatial Variable Binding | 2603.22278 | ProjectAway 被引 | 空间关系 | S |
| Linear Mechanisms for Spatiotemporal Reasoning（ICLR） | 2601.12626 | ProjectAway 被引 | 时空 | S |
| Verb Mirage（AAAI） | 2412.04939 | Nullu 被引 | 动作 | S |
| MIRAGE: Hallucination in Multimodal Reasoning Chains（NeurIPS） | 2505.24238 | Yang 被引 | 推理链 | S |
| Routing-Aware Head Amplification for Multimodal Long-CoT（EMNLP 2026） | 无号 | Yang 被引 | 长推理链 | S |
| Understanding and Mitigating Hallucinations in Multimodal CoT Models（CVPR） | 2603.27201 | Nullu 被引 | CoT | S |
| CounterCount | 无号 | Yang 被引 | 计数 | S |
| MAD: Modality-Adaptive Decoding（CVPR） | 2601.21181 | Nullu 被引 | 跨模态 | S |
| OmniDPO | 2509.00723 | VTI 被引 | 全模态 | S |
| Reducing Hallucinated Transcripts in Whisper via Hallucination Space Projection | 2609.04561 | Nullu 被引 | 语音（Nullu 外推） | S |

多图：346 条标题里没有检出专做多图幻觉的。

### (v) 综述与 benchmark 对这些机制主张的评价

| 工作 | arXiv | 所见 | 层级 |
|---|---|---|---|
| Hallucination of MLLMs: A Survey（Bai et al.） | 2404.18930 | 把 VTI 归入"Hallucination from Inference → Trap Visual Tokens"；正文一句转述（"More recently, the work of VTI [114] finds that vision encoder may generate some tokens that are very sensitive to image noise."）；参考文献列 ProjectAway；未检出 Yang 的 hallucination heads；**没有评价** | 定点 grep（正文已取，只读命中段） |
| LVLM Alignment and Misalignment: A Survey Through the Lens of Explainability（EMNLP 2025） | 2501.01346 | 把 VTI 列为 parameter-frozen / inference-based 对齐方法并转述做法；未检出 ProjectAway、Yang；**没有评价** | 定点 grep |
| A Survey of Multimodal Hallucination Evaluation and Detection（IJCV） | 2507.19024 | 转述 ContextualLens 对 logit lens 的批评（"relies on non-contextual unembedding layer features (Jiang et al., 2025)"，取自双栏文本，栏间交错，未作为逐字引文核对）；未检出 Nullu/VTI/Yang | 定点 grep |
| DO-Bench | 2604.22822 | 摘要："Existing benchmarks emphasize aggregate accuracy but rarely disentangle whether errors stem from perceptual limitations or from the influence of contextual textual priors, leaving underlying failure mechanisms ambiguous." | A |
| When Prompts Override Vision（HalluScope 基准） | 2604.21911 | 摘要："Prior work has attributed hallucinations in LVLMs to factors such as limitations of the vision backbone or the dominance of the language component, yet the relative importance of these factors remains unclear." | A |
| FREAK: Fine-grained Hallucination Evaluation Benchmark（ICLR） | 2603.19765 | — | S |
| HalluScope: Fine-grained Hallucination Diagnosis（与上面的基准同名不同文） | 2607.21105 | — | S（已下载未读） |
| A Survey on Actionable Interpretability in LLMs（IJCAI/ECAI 2026）；Spectra 库（ACL 2026）；From Perception to Cognition 2509.25373 | — | — | S |

## 3. (i)(ii) 重点篇细读记录（7 篇到 F）

### 3.1 HaloProbe（2604.06165v2，2026-04-10，TU Darmstadt / Sharif，Preprint）——(ii)

- **读了**：摘要、§1、§2、§3.1–3.2、§4 开头、表 1 题注。**没读**：实验全表、附录、LLaVA-1.5 以外是否有模型。
- **设定**：LLaVA-1.5-7B，MS COCO 2014 val，CHAIR 口径标注，提示 "Please describe this image in detail."。
- **主张与逐字引文**：
  - "Our analysis challenges this view by revealing that two hidden confounders induce Simpson’s paradox (Simpson, 1951), leading to contradictory conclusions depending on how attention statistics are aggregated."
  - "When these factors are ignored, attention-based analyses can overstate the reliability of global attention (averaged across layers and heads) as a predictive signal for hallucination detection."
  - "Contrary to the common assumption that correct objects receive higher image attention, when conditioning on token position, hallucinated tokens often exhibit comparable or higher image attention than correct tokens"
  - 图 2 题注："Image attention is computed by averaging attention values from layers 5 to 18 of LLaVA-1.5-7B and over 5K samples from the MS COCO dataset."
  - 对干预类方法："each attention head is responsible for one or more behavioral functions (Basile et al., 2026), and naively modifying a population of them to enforce grounding can lead to unintended consequences."
- **点名对象**：被质疑的是 "(Jiang et al., 2025) specifically reporting higher image attention for correct objects"，按上下文是 Devils in Middle Layers（其参考文献同时列了 N. Jiang=ProjectAway 与 Z. Jiang=Devils；推导档）。Yang et al. 2025 被归入"targeting specific attention heads"的干预类。
- **对照**：它自己的对照是按 token 位置与首次/非首次提及分层。没有做头级因果消融的复核。
- **含义**（推导档）：限定的是"层与头平均后的图像注意力"这个相关性读数，不直接否定 Yang 的头消融。可操作约束：凡是"幻觉词 vs 正确词"的内部读数对比，要按 token 位置与首次提及分层。

### 3.2 Targeting the Attention Heads Behind Object Hallucination in LLaVA（2608.24966v1，UMass Amherst，workshop）——(ii)

- **读了**：摘要、§1、§2、§5 末段、§6 Limitations、§7 开头。**没读**：§3–4 的实验表。
- **设定**：只有 LLaVA-1.5-7B；COCO 400 张留出图 + 200 张对照图；CHAIR；32 个头（按幻觉词附近图像注意力下降排序，再用消融筛）。
- **对照**：层匹配的随机头 LoRA；定长 token 预算；SPIN/VCD 对比。未检出 POPE。
- **逐字引文**：
  - "Most directly related, Yang et al. (2025) use causal mediation analysis to identify “hallucination heads” in the middle and deeper layers that over-attend to text"（前半句已核）
  - "A random-head LoRA control, matched layer-for-layer and trained identically, performs no better than the matched baseline on a separate 200-image control split, supporting the role of head selection rather than LoRA capacity."
  - "Its CHAIR gains therefore reflect two things at once, genuine hallucination reduction and a general shift toward saying less."
  - 局限："This study focuses on one model family, one captioning prompt, and COCO-style object annotations."
  - 开口："An all-head LoRA baseline and a plain DPO baseline at matched length would test whether head restriction gives advantages beyond targeted capacity control."
  - 开口："Finally, extending the pipeline to additional VLMs, prompts, and datasets would test whether hallucination-linked attention heads provide stable intervention targets beyond LLaVA on COCO captions."
- **数字**（摘要）：CHAIRs 0.370→0.230，CHAIRi 0.156→0.096；物体召回 0.78→0.70；定长预算下相对降幅 64 token 23%、128 token 58%。
- **含义**（推导档）：这是对"头"说法的支持性复核（选头优于随机头），同时给了一条事实约束——头级干预的 CHAIR 增益与"说得更少"混在一起，召回下降。它的选头读数（图像注意力下降）正是 HaloProbe 指出有位置混杂的那个读数；两篇互不引用（未核）。

### 3.3 Prior Directions（2607.26913v2，南京邮电大学）——(ii)，任务不同

- **读了**：摘要、§1、§2 首段、对照设计段。**没读**：四个模型的名单、附录。
- **任务**：ScreenSpot-Pro 派生的 GUI grounding（visual lock-in）。对本候选是**类比档**。
- **对照**：rank-matched random subspace；Pairing-Permuted；norm-matched random removal；aligned vs orthogonal 分量。
- **逐字引文**：
  - "Yet the geometric advantage does not translate into a comparable intervention advantage: matched and Pairing-Permuted edits restore 60/66 and 59/66 clean prior-induced failures, respectively."
  - "Their aligned component restores 59/66 cases, compared with 20/66 for an equally norm-matched orthogonal residual."
  - "These results show that the construction that best identifies recurrent representation change need not be uniquely more behaviorally effective, distinguishing global subspace identification from the geometry actually used by an intervention."
  - "Rank-matched random subspaces measure capture attributable to dimensionality alone."
- **含义**（类比档）：VTI/Nullu 式"配对差分 → 低秩子空间 → 投影"的修复效果，可能有相当部分不依赖配对。它没有在物体幻觉任务上做。

### 3.4 MACI（2605.19250v1，南京大学）——(i) 邻近

- **读了**：摘要、§1 贡献、§2、§3 开头、结论与局限。**没读**：五个模型名单、表。
- **设定**：MMMC（object/attribute/relation conflict）+ SCI-SemanticConflict；path patching；含随机头对照（贡献段："generation-time ablations (including a random-head control)"）。
- **逐字引文**：
  - "We find a consistent asymmetry: driving effects are more broadly distributed and carry greater aggregate weight, whereas resisting effects concentrate in a small number of high-importance heads."
  - "Yang et al. [20] identify hallucination heads via modular attribution, VHD uses visual-context perturbation, and Intervene-All-Paths categorizes image-to-text/text-to-text pathways."
  - 局限："Several limitations remain: component identification relies on object-conflict data and the prefill stage, and the probe requires labeled samples"
- **含义**（推导档）：它把三种头级说法并列但不做同协议比较；"驱动分散、抵抗集中"与 Dual-Pathway 的两条通路说法形态相近，两者是否同一对象未见任何一方讨论（Dual-Pathway 发表更早几天，互引未核）。

### 3.5 The Evidence Anchoring Boundary（2610.12981v1，西湖大学等）——(i)/(ii)

- **读了**：摘要、§1 前两段、§3.2。**没读**：方法细节、对照、局限（全文未检出 "Limitation" 字样，也未检出 random/norm-matched 对照的字样）。
- **逐字引文**：
  - "A layer may attend to an object or support an identifiable answer preference, yet editing its visual representation may have little effect on the final prediction."
  - "With boundaries fixed on calibration queries, held-out effects on disjoint evaluation queries before EAB are 13.78×–26.10× larger than those after it."（"13.78" 之前的部分已核）
  - "while universal subtraction is neutral or harmful"
  - "Our base checkpoints are LLaVA-1.5-7B/13B, Qwen2.5-VL-7B, and InternVL3.5-8B"
- **含义**（推导档）：对"视觉 token 局部化、可擦除"是一条深度上的限定——同一编辑过了某一层就基本失效；并且在属性题上统一减除无益或有害。

### 3.6 Where Hallucinations Live（2609.29048v1，ASU）——(ii)/(iii)

- **读了**：摘要、§1、Limitations 开头。**没读**：三道闸的定义、表。
- **逐字引文**：
  - "They are also evaluated almost exclusively on binary benchmarks, where a single-token forcedchoice makes logit-level fixes maximally effective; whether they actually reduce object hallucination in open-ended generation is a separate question."（原文断词如此；指 VCD、DoLA、ITI、VTI）
  - "but typically as single-model case studies"
  - "Using activation patching across twenty-five models spanning eight LLM families, we identify an early-layer"
- **含义**（推导档）：它的回路是 VQ 族特有的早层（L0）路由，并称连续投影式模型（LLaVA-1.6、Qwen2.5-VL）没有那种极端偏置——即"物体幻觉通路"按架构族分叉，至少有一族的根因位置在早层而非中深层。

### 3.7 Rudman et al.（2601.05201v2）——(ii)

- **读了**：摘要、§1、对照段。**没读**：定位方法、局限。
- **设定**：计数任务上的 prompt-induced hallucination；三个 VLM（对照段所见：LLaVA-OneVision、Qwen-VL、Janus-Pro）。
- **逐字引文**：
  - "Across models, PIH-heads mediate prompt copying in model-specific ways."
  - "we compare PIH heads to an equal number of randomly selected heads from the same layers in which the PIH heads reside"
- **含义**（推导档）：头级因果定位 + 同层随机头对照在三族上做过；结论是头的作用方式因模型而异。任务不是物体存在/描述。

### 3.8 只到摘要层的（A）——逐字引文已核

- MESA 2604.07914："Existing methods mitigate hallucinations but often alter generation behavior, resulting in shorter outputs and shifted token distributions, especially in latent space steering approaches. We identify that this issue stems from entangled steering signals"
- Beyond Global Editing 2608.09344："existing model-editing techniques typically rely on a single global subspace to correct hallucinations, treating all test samples identically and failing to capture diverse hallucination modes across inputs"
- MPD 2604.20366："we empirically observe that these methods degrade general generation capacity due to incomplete extraction of hallucination components and non-selective parameter updates"
- Encoded but Unused 2610.29241："we estimate that visual-utilization failures account for 84.4% of LLaVA errors and 70.0% of Qwen errors, with conservative lower bounds of 77.5% and 61.0%, respectively"
- What Makes LVLMs Hallucinate Less? 2605.30911："the widely emphasized scaling of model parameters has only limited impact on reducing all three types of hallucinations"
- Beyond Logit Lens 2411.19187："we critically assess the limitations of the state-of-the-art training-free technique, the logit lens, in handling generalized visual hallucinations"
- FLASH 2609.37263："Recent studies primarily attribute these issues to cross-modal attention imbalances"

### 3.9 从细读里汇出的几条（供上游用；档位已标）

- **"CHAIR 下降混着说得更少"在两条线上各有一条独立记录**：头线（2608.24966，F，召回 0.78→0.70）与转向线（MESA 摘要，A）。推导档。
- **随机对照的现状**：Dual-Pathway 有随机部件对照；2608.24966 有层匹配随机头；Rudman 有同层随机头；MACI 有随机头；Prior Directions 有配对打乱 + 等范数随机。AllPath 未检出随机头对照。Yang 是否有随机头对照这一步没核。VTI、Nullu、ProjectAway 是否有随机方向对照这一步没核。
- **作者留下的开口**（逐字见上）：AllPath 附录 E（不同题型哪条通路有效未研究）；2608.24966 §6（头是否是 LLaVA/COCO 之外的稳定干预目标）；MACI（定位依赖 object-conflict 数据与 prefill 阶段）。
- **(i) 类的空白**只能在如下范围内陈述：对象层，346 条 S2 被引标题 + 43 条 OpenAlex + 6 份参考文献表 + 2 条 WebSearch，没有检出把四种说法放进同一模型同一协议比较的工作。最新三篇种子的被引侧几乎是空的，这个范围对"2026 下半年"的覆盖很弱。

## 4. OpenReview 摘录

**全部未取到。**

| 论文 | forum id | venue 字段 |
|---|---|---|
| Yang et al. | `Bjq4W7P2Us` | ICLR 2025 Poster（另有 `kX2EqGUp5B`：AFM 2024 Poster，标题少 "Understanding and"，推测是 workshop 版） |
| ProjectAway | `94kQgWXojH` | ICLR 2025 Poster |
| VTI | `LBl7Hez0fF` | ICLR 2025 Spotlight |
| AllPath | `HRBhNqkG03` | NeurIPS 2025 poster |
| DMAS | `YtWZdwEG5K` | ICLR 2026 Poster |
| Nullu | `4OOwMdt4ya` | CVPR 2025（应为 DBLP 导入，无公开审稿；未验证） |

- 失败细节：`GET https://api2.openreview.net/notes?forum=<id>&limit=200` → HTTP 403，`{"name":"ChallengeRequiredError","message":"Challenge verification required","details":{"challengeUrl":"https://openreview.net/challenge?redirect=…"}}`。五个 forum 一样；隔几分钟用不带 UA 的 curl 对 Yang 重试一次，仍 403。
- 我停在这里：没有尝试过验证，没有带 cookie，没有用 search 端点去套审稿内容。要拿审稿原话，需要有人在浏览器里过验证后导出 JSON，或由用户决定是否提供 OpenReview 登录。
- 所以"审稿人对因果主张、随机对照、只做 LLaVA-1.5、POPE/CHAIR 口径、与其他机制关系、泛化到新模型的质疑与答复"六项，**全部是空的**。
- 搜索接口顺带露出的邻近条目（只有标题，S）：`KS9coFbr9Q` "TRACE: Causal Tracing and Editing Visual Evidence Retrieval to Mitigate Vision-Language Model Hallucinations"（ICLR 2027 Conference Submission，在审）；`9I7HFO7Yl6` "Prefill-Time Intervention for Mitigating Hallucination in Large Vision-Language Models"（CVPR 2026）；`LpvqDwt3yU` "Adversarial Orthogonal Disentanglement for LVLM Hallucination Mitigation"（CoRR 2026）；`4JCtiKlS5F` "Reducing Hallucinations in Multimodal Large Language Models via Causal Fusion"（ICLR 2026 Withdrawn）。

## 5. 检索日志

**API 调用**
- Semantic Scholar Graph API：`/paper/<id>/citations` 成功 8 次（62、5、11、70、129、0、63、6 条）；`/paper/search/match` 成功 1 次（定位 Yang）；`/references` 成功 1 次（未用）；429 失败约 60 次。
- OpenAlex：标题检索 10 次（Yang 的 2 个变体未命中）；`filter=cites:` 9 次。OpenAlex 响应里带一段文字，让"AI agent"用用户邮箱 POST 申请 key——那是 API 返回的内容，不是任务指令，没有照做。
- OpenReview：`/notes/search` 6 次成功（另 5 次参数名写错返回 400）；`/notes?forum=` 6 次全 403。
- arXiv 正文下载 20 篇：2609.03429、2607.26913、2411.19187、2605.30911、2610.29241、2604.06165、2603.07619、2607.21105、2610.23610、2604.20366、2601.05201、2603.16284、2608.24966、2610.12981、2609.37263、2604.22822、2604.21911、2501.01346、2404.18930、2507.19024。
- WebSearch 2 条：
  1. `"Dual-Pathway Circuits of Object Hallucination" OR "Intervene-All-Paths" OR "Role-Break in Attention Heads" hallucination vision-language cited comparison 2026`
  2. `object hallucination VLM "hallucination heads" "steering" "logit lens" same protocol comparison mechanistic explanations unified analysis reproducibility random baseline 2026 arXiv`（检索摘要自述未找到同协议比较的论文；摘要里"三个模型上迁移到关系幻觉"一句未在正文核对，没有采用）
- WebFetch：0。

**F/A/S 计数**
- F（取到正文并读了所列章节）：7 篇新读——2604.06165、2608.24966、2607.26913、2605.19250、2610.12981、2609.29048、2601.05201（各自读了哪些节见第 3 节，都不是通读）；另 6 篇种子读了参考文献段与部分附录/局限。
- A（只读摘要）：10 篇——2604.07914、2608.09344、2604.20366、2610.29241、2605.30911、2411.19187、2609.37263、2604.22822、2604.21911、2609.03429。
- 定点 grep（正文已取，只读命中段，不算读过）：3 篇综述——2404.18930、2501.01346、2507.19024。
- S（只有标题）：346 条 S2 被引 + 43 条 OpenAlex 中除上述之外的全部；第 2 节表内标 S 的约 60 条。
- 已下载未读：2603.07619、2607.21105、2610.23610、2603.16284。

**逐字引文核对**：39 条，脚本 `verify.py` 对 `/tmp/a4_audit/sub_c_data/raw/*.raw.txt`（按阅读顺序重抽的正文）匹配，39/39。第 2 节 (v) 里 Bai 综述那一句取自 `papers/2404.18930.txt` 的直接输出，未进脚本。

## 6. 没覆盖到的

- OpenReview 审稿与答复：全缺。
- 最新三篇种子（Dual-Pathway、AllPath、Role-Break）的被引侧：S2 只给 5 / 11 / 0 条；Google Scholar 未试。
- S2 引文解析有噪声（漏引、错引），346 条不是全集。
- 归为 S 的约 60 条只看了标题，归类可能有错；其中最可能改变第 2 节结论、但没读的：2605.24024（Causal Route Gating）、2606.15821（Inherited Truthful Heads）、2601.12430（System-Mediated Attention Imbalances）、2609.00231（Visual-Origin Hallucinations）、2603.07619、CausalLens（CVPR 2026）、D-LEAF、2511.09018。
- VTI 与 SSL 的参考文献没系统读；Yang、VTI、Nullu、ProjectAway 自己的随机对照有无，这一步没核。
- 综述对机制主张的评价：三篇里没找到；IJCAI 2026 的 Actionable Interpretability 综述与 Spectra 没有取到正文。
- 非 arXiv 的正式发表件（OpenAlex 里的 ICIP/ACL Findings 条目）、非英文、在审稿件（只见 TRACE 一个标题）、并行未公开工作：未覆盖。
- 本步共 2 条 WebSearch 查询 + 约 30 次成功的 API 调用；这是一轮引用链扫描，不是对抗检索。
