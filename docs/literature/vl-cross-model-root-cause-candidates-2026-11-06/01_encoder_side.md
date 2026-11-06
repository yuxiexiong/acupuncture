# 01 视觉编码器一侧的跨模型根因候选

检索日期 2026-11-06。口径见 `00_BRIEF.zh-CN.md`。阅读层级：**F** = 用 `curl` 取到 arXiv 正文（HTML 或 PDF→`pdftotext`）并在本地 `grep` 核对了对应段落/表格；**F-部分** = 取到正文但只核对了一两段；**A** = 只读了摘要/引言；**S** = 只有检索片段。所有逐字引文都是从本地正文文本里摘的，没有经过网页摘要工具转述。F 不等于通读全文：我是按关键词定位段落读的，没看到的章节里可能有与此处相左的内容。

**先说最不利的三件事**

1. 「编码器没看见」这一类根因主张（MMVP 的 CLIP-blind、朝向、计数、低层几何）在编码器一侧**没有内部因果证据**。原始论文给的是相关（MMVP：按视觉模式的 Pearson > 0.7）或论证（DORI：归因于 CLIP 式预训练）。反方向却已有 ≥2 个模型族的相关级证据：线性探针能从同一批编码器输出里读出朝向（MAE < 3°）、计数、圆是否相交等信息，而整机答错。
2. 编码器内部做过干预、且跨 ≥2 个模型族的只有两条：排版攻击回路（消融编码器注意力头）和 ViT 高范数 token（V-sink）。前者在 LVLM 上的收益只有 0–1.7 个点；后者的效应随任务变号（局部任务变好、全局任务变差）。
3. 「registers 一类伪影 token 传进 VLM 并造成某个具体失败」**没有被直接证明**。唯一把 register 修法装进 VLM 的实验（test-time register，LLaVA-Llama-3-8B）结果是八个基准平均分 46.2 对 46.2，只改善了注意力图的可读性。

---

## 候选主表（现象与根因均有 ≥2 个模型族证据）

### C1｜ViT 高范数 token（V-sink / 伪影 token）传入 LLM 并占用注意力，压低局部细节任务

- **现象**：视觉编码器输出里少数高范数 token（多在背景）进入 LLM 后持续吸走注意力；把注意力从它们身上挪开，细粒度/局部任务变好，全局任务变差。测法：按 token 组做注意力 Key 缩放的网格搜索（MME/CV-Bench/MMStar 子任务）；只用 sink / 去掉 sink 的对比。
- **现象的跨模型证据**
  - LLaVA-1.5-7B（CLIP ViT-L + Vicuna）上定义 V-sink（来自 ViT）与 L-sink（LLM 深层生成）；范数与注意力剖面在 LLaVA-OneVision-7B（SigLIP + Qwen2）上复现（"confirming that the sink taxonomy generalizes across architectures"）。细粒度感知任务调比例最多 +6.49%，粗粒度任务最多 −4.27%。— [2604.03316](https://arxiv.org/abs/2604.03316) §3、Fig.5（F）
  - 四个 ViT–LLM 组合（视觉骨干 CLIP、SigLIP；语言骨干 Qwen2、Qwen2.5、Phi-2、Vicuna）：「for local tasks, removing sinks improves performance, indicating potential interference」；只用 sink 在全局任务上强。— [2510.08510](https://arxiv.org/abs/2510.08510) §3.2–3.3、Fig.5(B)（F；Fig.5 具体用了四个组合中的哪几个我没核到）
  - LLaVA-Llama-3-8B：视觉编码器输出的离群 token「leak into the language model's attention to visual tokens」（定性图）。— [2506.08010](https://arxiv.org/abs/2506.08010) §5.4、Fig.6（F）
  - LLaVA-1.5-7B/13B、VILA-13B、Qwen2-VL-7B、InternVL2-8B 上都有「visual attention sink」，但该文把它归到 LLM 一侧（见下）。— [2503.03321](https://arxiv.org/abs/2503.03321)（F）
- **根因主张**：ViT 在双向注意力下把少数背景 patch 变成高范数「寄存」token；这些 token 经 projector 后以整体偏高的范数进入 LLM，成为注意力汇。位置：视觉编码器（MLP 神经元）→ projector → LLM 注意力。
- **根因的跨模型证据**
  - **因果（LLaVA-1.5 一族确证）**：对 V-sink / 普通 token 的 Key 做缩放，任务表现按预期变向。— 2604.03316（F）
  - **因果（训练级，四个 ViT–LLM 组合）**：为 sink 与非 sink 分设 projector（DIYSink）后各基准一致上涨。— 2510.08510（F）
  - **因果（编码器内部；对下游失败无效应）**：一小组「register neurons」决定离群 token 的位置，把它们的激活移到一个额外 token 上即可去掉伪影（OpenCLIP、DINOv2）；在 LLaVA-Llama-3-8B 的 CLIP ViT-L/14 里是约 10 万个神经元中的 100 个。干预改变了伪影位置与注意力图，但 VLM 分数不变。— 2506.08010 §3–5.4（F）
  - **相关（LLaVA-1.5 一族）**：POPE-COCO 上，视觉 token 的峰值/平均 L2 范数比越高，幻觉样本比例越高。— [2510.16596](https://arxiv.org/abs/2510.16596) Fig.2(a)（F）；LLaVA-1.5 中 LLM 解码注意力的离群 token 与 ViT 注意力图的离群 token 位置相同。— [2410.04514](https://arxiv.org/abs/2410.04514)（F）
  - 综合档位：**因果 1 族（LLaVA-1.5）+ 相关/训练级证据 ≥2 族**。第二个模型族上没有看到推理期的内部干预数据。
- **不同论文对根因的说法是否一致：不一致，至少四种**
  1. sink 来自 **LLM 自身**：视觉 sink token 的大激活维度就是底座 LLM 的维度（LLaVA-1.5-7B 仍是 LLaMA2 的 {1415, 2533}）；「the formation of visual sink tokens and text sink tokens shares the same underlying mechanism inherited from the base language models」；「We leave the investigation of how visual tokens are recognized as sink tokens during training as future work.」— 2503.03321（F）
  2. sink 来自 **ViT**，且**有害**（引发幻觉）：「We attribute to the unexpected attention distribution to an inherent flaw in the visual encoder itself」— 2410.04514（F）；SHIELD 称之为 statistical bias — 2510.16596（F）
  3. sink 来自 ViT，但**对全局任务有益**，应当利用而不是去掉 — 2510.08510（F）；PAINT 也主张对 summary token 加注意力（LLaVA-1.5）— [2501.12206](https://arxiv.org/abs/2501.12206)（F）
  4. 两种来源并存（V-sink 与 L-sink），作用随任务变号 — 2604.03316（F）
- **竞争者（已有修法）**
  - Test-time registers（Jiang 等，NeurIPS 2025）：训练后把 register 神经元的激活移到新增 token。VLM 上只测了 LLaVA-Llama-3-8B：八基准平均 46.2 → 46.2（HallusionBench 28.6→29.4，OCRBench 41.6→41.3）。自述：「We do not pass the register to the LLM; we leave exploring its use as global memory for the LLM or leveraging multiple registers for adaptive computation to future work.」；「we only addressed one component type that is responsible for their creation – neurons, while neglecting other possible elements ... such as attention layers or positional encodings」；「we mostly focus on individual models (CLIP, DINOv2). We do not present results on other, less commonly used, pretrained ViTs」。代码：https://github.com/nickjiang2378/test-time-registers（F）
  - Layer-wise Sink Gating（2604.03316）：冻结主干，训练一个小门控预测逐层 Key 缩放。LLaVA-1.5：单层最好 L10，MMStar +0.72、CV-Bench +2.14。局限：分析「only」在 LLaVA-1.5 上做全，LLaVA-OV 只复现了范数/注意力剖面。是否开源未核到。（F）
  - DIYSink / sink-to-the-front（2510.08510，ICLR 2026）：双 projector + 动态选择；训练免费版是把 ViT sink 挪到序列最前。四个 ViT–LLM 组合。数字未摘录。是否开源未核到。（F）
  - VAR（2503.03321，ICLR 2025）：把 sink 的注意力重分配给图像。LLaVA-1.5、VILA、Qwen2-VL、InternVL2。自述：「the mechanisms behind how LMMs select visual sink tokens and how visual attention sinks emerge during the training process remain open questions.」（F）
  - DAMRO（2410.04514，EMNLP 2024）：用 ViT 的 CLS 注意力挑出离群 token 当负样本做对比解码。分析只在 LLaVA-1.5。（F）
  - SHIELD（2510.16596）：token 重加权 + 噪声 token 相减 + 对抗对比解码。LLaVA-1.5 / InstructBLIP / Qwen-VL；CHAIR 上比 OPERA 最多好 18%。根因分析只在 LLaVA-1.5。自述：「Future work could explore the design of more robust visual encoders to further reduce bias and vulnerability」。（F）
  - 原始修法：训练时加 register（Darcet 等，ICLR 2024）。自述：「we have not been able to fully determine which aspects of the training led to the appearance of artifacts in different models」；OpenCLIP 的离群 token 似乎落在 value 投影的零空间，「the investigation for this phenomenon is left for future work」。— [2309.16588](https://arxiv.org/abs/2309.16588)（F-部分）
- **剩余空间**：没有一篇给出「去掉 V-sink 后某个具名失败基准涨多少、离上限多远」的数。已有收益在 0–2 点（LSG）到 6.49 点（oracle 网格、单任务）之间。V-sink 与 LLM 自生 sink 的各自贡献没有被分开量过；「V-sink 是否就是 2503.03321 报告的那批 sink token」没有同一模型上的逐 token 对照。
- **便宜办法**：未找到「换提示能否消除」的测试。把 sink 挪到序列最前（免训练）对全局任务有帮助、对局部任务持平（2510.08510）。
- **数据与基准**：无专用基准；用 MME、CV-Bench、MMStar、POPE、CHAIR。2510.08510 自建 600 条 image–query 的全局/局部标注集（公开与否未核到）。

### C2｜图中文字劫持答案（typographic attack）——视觉编码器里的「排版回路」注意力头

- **现象**：图里叠一段与内容无关的文字，模型按文字而不是按视觉内容回答。测法：TypoD、SCAM（1162 张真实图）、RIO-Bench obj-attack。
- **现象的跨模型证据**
  - LLaVA 与 InstructBLIP 在 TypoD 上明显掉点。— [2402.19150](https://arxiv.org/abs/2402.19150)（F）
  - 11 个 LVLM（LLaVA 系、Gemma3、Llama3.2-vision、Llama4、GPT-4o、Claude Sonnet 4）：较小的 LLaVA 与 Gemma3 掉「more than 40-60 percentage points」。— [2504.04893](https://arxiv.org/abs/2504.04893)（F）
  - Qwen3-VL-4B/8B/30B、InternVL3.5-8B/14B、Gemma3-4B/12B 在 RIO-Bench obj-attack 上基线 44–70。— [2607.02494](https://arxiv.org/abs/2607.02494) Table 4（F）
- **根因主张**：CLIP 式 ViT 后半层有一小组注意力头专门把图中文字的信息搬到 CLS（或充当 CLS 的首个视觉 token）。位置：视觉编码器注意力头。
- **根因的跨模型证据：因果，≥2 族，但效应小**
  - 纯 CLIP：消融这组头，typographic ImageNet-100 最多 +22.06%，干净 ImageNet-100 掉不到 1%。— [2508.20570](https://arxiv.org/abs/2508.20570)（F）
  - LVLM 的视觉编码器内做零消融（RIO-Bench obj-attack，Overall Δ）：Qwen3-VL-4B +0.97、8B +1.58、30B-A3B +1.13；Gemma3-4B +1.73；InternVL3.5-8B +0.23、14B +0.01。干净集影响 −0.3% 到 +0.6%。— 2607.02494 Table 4（F）
- **不同论文对根因的说法是否一致：部分冲突**
  - 编码器说：SCAM「We hypothesize that this vulnerability stems from their reliance on weaker vision encoders, particularly the ViT-L-14-336 backbone trained by OpenAI」。
  - LLM/提示说：TypoD 发现 LVLM「could somewhat discriminate visual contents and typography in the images」，把提示写详细后掉点从 42.07% 降到 13.90%；SCAM 同时写「a more powerful LLM backbone can compensate for the limitations of the vision encoder」。
  - 2607.02494 自己的数据支持「编码器回路只占一小部分」：消融后 InternVL3.5 几乎不动。
- **竞争者**
  - Dyslexify（2508.20570）：免训练消融注意力头；只在 CLIP 分类上验证，消融只改 CLS 的残差流。没有 LVLM 结果。
  - Stochastic-lottery 回路挖掘 + 消融（2607.02494）：见上。「Attention Reweighting does not apply to LVLMs, which often do not implement and train a dedicated class token」，所以在 LVLM 上退回到零消融。
  - 提示工程（2402.19150）：LLaVA、InstructBLIP；代码 https://github.com/ChaduCheng/TypoDeceptions。
  - Test-time register 的副产物：把高范数伪影挪到文字所在 patch 上可在激活空间遮掉文字（只测 CLIP 分类）。— 2506.08010 附录 A.8（F）
  - Defense-Prefix、OCR+模糊预处理：在 2508.20570 / 2607.02494 里作基线（A）。
- **剩余空间**：编码器内消融后，Qwen3-VL-8B 在 obj-attack 上 71.69，Gemma3-12B 约 50；干净集与攻击集的差距没有被这类干预补上多少。SCAM 自述「a central limitation of our evaluation remains the reliance on "naive prompting"」。
- **便宜办法**：换提示能修掉一大块（42.07% → 13.90%，TypoD），所以这不是「换提示修不好」的干净失败。
- **数据与基准**：TypoD（公开）、SCAM（1162 图，公开）、RIO-Bench、RTA-100、Disentangling、PAINT、IN-100-Text（2607.02494 新建）。

### C3｜末层视觉特征丢失/扭曲细粒度信息，中间层里有（"deep-layer bias" / "Visual Encoding Distortion"）

- **现象**：把喂给 LLM 的视觉特征从标准输出层换成更浅的层，一部分原本答错的题变对；计数、定位类任务尤甚。
- **现象的跨模型证据**
  - InstructBLIP（EVA-ViT，39 层）、LLaVA-1.5（CLIP，25 层）、Qwen-VL（ViT-bigG，49 层）：「a significant proportion of samples can be decoded correctly at the early visual hidden layers but unexpectedly decode wrongly at the standard output layer」，InstructBLIP 第 5 桶（31–34 层）EDR 达 69.35%。— [2411.15839](https://arxiv.org/abs/2411.15839) Table 1（F）
  - CLIP ViT-L/14 + MobileLLaMA 1.4B/2.7B、Vicuna-7B：浅/中层在 MME 约三分之一子任务上胜过深层；第 18 层在 position 任务上比倒数第二层高 20%，CV-Bench 高 3%。— [2504.21447](https://arxiv.org/abs/2504.21447)（F）
  - LLaVA-1.5：加入中间层特征改善空间理解。— [2503.17349](https://arxiv.org/abs/2503.17349)（F）
  - 纯编码器：对比式预训练的 PEcore 最好的特征「are hidden within the intermediate layers of the network」；COCO 检测上最好层与 DINOv2 持平、最后层明显更差。— [2504.13181](https://arxiv.org/abs/2504.13181)（F-部分）
- **根因主张**：对比式（图像级）目标让最后几层向全局/文本对齐收拢，局部细节在到达输出层之前被压掉。位置：视觉编码器深层。
- **根因的跨模型证据**：**因果（输入级干预：换层）3 族**（VaLiD），但换层时 projector 没有为那一层重训，翻转里混着「projector 对该层特征不适配」的成分；**训练级干预 1 种编码器**（2504.21447 每层重训，只有 CLIP ViT-L）。为什么末层会丢——只有论证，没有内部测量。
- **不同论文对根因的说法是否一致：有竞争解释**
  - 「末层够用，是 LLM 没用」：Prismatic 四种编码器上，末层特征用视觉读出法远高于整机，且信息在 projector 与 LLM 各层都还读得出（见 KQ3）。— [2506.08008](https://arxiv.org/abs/2506.08008)（F）
  - 「损失在 connector」：connector 明显扭曲视觉表示的局部几何。— [2509.11986](https://arxiv.org/abs/2509.11986)（A）
  - 2504.21447 称「Scaling up the LLM size does not compensate for the loss of visual detail in the deep layers」（检索片段转述，S；正文里我只核到实验设置与局限段）。
- **竞争者**
  - VaLiD：视觉层融合 + 对比解码，三个模型；MME posters 任务 LLaVA-1.5 +29.59%。自述：「we believe that future work should focus on investigating the root causes of these distortions so that higher quality visual features can be extracted.」（F）
  - 2504.21447 的线性多层融合：胜过 DenseConnector、MMFuser。自述：「our study does not extend to larger-scale LLMs. In terms of visual encoders, we focus exclusively on CLIP-ViT-L/14 ... and leave the exploration of alternative backbones to future work」。（F）
  - Perception Encoder 的 language/spatial alignment tuning：把中间层能力对齐到输出端（F-部分，数字未摘录）。
  - MMFuser（2410.11829）、DenseConnector、TGIF：只见于检索片段（S）。
- **剩余空间**：没有人在 SigLIP / DINOv2 / Qwen 原生 ViT 上重做逐层重训的对照；VaLiD 的 EDR 没有区分「信息丢了」与「projector 不适配」。
- **便宜办法**：未找到换提示的测试。提高分辨率不改变取哪一层。
- **数据与基准**：MME、POPE、AMBER、CV-Bench、RefCOCO；无专用基准。

### C4｜CLIP-blind pairs：九类视觉模式上的系统性错误（MMVP）

- **现象**：CLIP 嵌入相似（cos > 0.95）而 DINOv2 嵌入不相似（< 0.6）的图对，问一个直白的差异题，模型成对答对率很低。基准：MMVP（150 对、300 题）、MMVP-VLM。
- **现象的跨模型证据**：LLaVA-1.5、InstructBLIP、Mini-GPT4、GPT-4V、Gemini、Bard。「Models except GPT-4V and Gemini, scored below random guess level (25%)」；GPT-4V 38.7%；LLaVA-1.5 24.7；人 95.7%。— [2401.06209](https://arxiv.org/abs/2401.06209) §2.3、Fig.4、Table 3、附录（F）
- **根因主张**：对比式预训练的视觉编码器把这些图对编码得几乎一样（「their pre-trained CLIP vision encoders overlook crucial visual details in images」）。位置：视觉编码器的预训练目标。
- **根因的跨模型证据**
  - **相关（2 族）**：按九类视觉模式，CLIP 的成绩与 MLLM 的成绩 Pearson > 0.7（LLaVA-1.5 用 OpenAI CLIP ViT-L，InstructBLIP 用 EVA ViT-g）。— 2401.06209 §3.3（F）
  - **相关（多种对比式编码器）**：MMVP-VLM 上 OpenAI CLIP、SigLIP ViT-SO、EVA01/02、DFN、MetaCLIP「increasing network size and training data only aids in identifying two visual patterns」。— 2401.06209 Table 1（F）
  - **训练级干预（LLaVA 一族）**：换/混编码器后 MMVP 上升（见竞争者）。
  - 原文还用选项对调作旁证：GPT-4V 40.3% 对 38.7%，「This further suggests that the visual incapabilities are in the vision encoder rather than in alignment or the LLMs」——这是论证，不是内部测量。
- **不同论文对根因的说法是否一致：冲突**
  - 「We suggest that the perceived limitations of VLMs' vision encoders may simply come from their misuse rather than an inherent inability」；并点名「Previous works have ... attributed VLM limitations to vision encoder weakness and proposed ensembling encoders ... this strategy is unlikely to address the underlying failures」。— 2506.08008 讨论部分（F）。注意它测的是 CV-Bench/BLINK/MOCHI 六个任务，不是 MMVP 本身。
  - 朝向、计数两类模式各自有「编码器里读得出」的证据（见 C5、C6）。
- **竞争者**
  - Interleaved-MoF（CLIP + DINOv2 token 交错）：LLaVA 5.5 → 16.7（+10.7），LLaVA-1.5 24.7 → 28.0（+3.3）；加性混合时 DINOv2 比例过高会损害指令跟随。「Merely increasing the image resolution ... does not boost visual grounding capabilities.」— 2401.06209 Table 2–3（F）
  - 生成式反馈微调 CLIP：DIVA（MMVP-VLM「3-7% ↑」；LLaVA-1.5-7B/13B 有提升表）— [2407.20171](https://arxiv.org/abs/2407.20171)（F-部分）；un²CLIP：OpenAI ViT-L-14@224 的 MMVP-VLM 平均 19.3 → DIVA 25.9 → GenHancer 31.9 → un²CLIP 32.6；@336 为 20.0 → 30.4；OpenCLIP ViT-H 28.9 → 36.3。自述局限：「finetuning CLIP requires a pretrained unCLIP model at first」。— [2505.24517](https://arxiv.org/abs/2505.24517) Table 1（F）
  - 多编码器融合：Cambrian-1 的 SVA（[2406.16860](https://arxiv.org/abs/2406.16860)，F-部分）、Prismatic 的 DINOv2+SigLIP（「significantly boosts performance on localization and challenge evaluations」，[2402.07865](https://arxiv.org/abs/2402.07865)，F-部分）。数字未摘录。
  - 换成带生成/稠密目标的编码器：LLaVA-AIMv2 在 CV-Bench 2D、TallyQA、CountBenchQA 上是 LLaVA 变体里最好的；结论是「encoder objectives and positional structure shape spatial behavior, but do not fully resolve it」。— [2603.12545](https://arxiv.org/abs/2603.12545)（F）
- **剩余空间**：编码器侧最好的修法之后 MMVP-VLM 平均仍只有 30–36（人 95.7）；un²CLIP 表里第一列（朝向与方向）在 ViT-L@224 上从 13.3 变成 0.0。MMVP 只有 150 对。2025–2026 的新模型在 MMVP 上的分数我没查到（一条查询，无结果）。
- **便宜办法**：提高分辨率无效（上引）；换提示未见系统测试。
- **数据与基准**：MMVP、MMVP-VLM（公开）；CV-Bench 2638 题（公开）。

### C5｜物体朝向/旋转判断失败

- **现象**：让模型判断物体朝向或旋转角度，粗粒度尚可，细粒度接近随机。基准：DORI（33,656 题、13,652 图、14 个来源）、MMVP 的 orientation 模式、RotBench、EgoOrientBench。
- **现象的跨模型证据**
  - DORI：「many open-source MLLMs perform at or near random chance」；闭源也「perform poorly overall」（GPT-4o、Gemini 1.5 Pro/2.0 Flash 等）。— [2505.21649](https://arxiv.org/abs/2505.21649) Tab.3–4（F）
  - 2604.13321 转述：「Nichols et al. tested 15 MLLMs ... the best systems could only answer 34% of the questions correctly」。— [2604.13321](https://arxiv.org/abs/2604.13321) §1（F；34% 这个数我只在转述里见到，没在 DORI 正文里定位到）
  - CARLA 合成交通场景，Ovis2.5、InternVL3.5、Qwen3-VL 等六个小模型。— [2603.06054](https://arxiv.org/abs/2603.06054)（F）
- **根因主张（编码器侧）**：CLIP 式对比目标只优化语义对齐，朝向这类连续几何量没有被编码。位置：视觉编码器预训练目标。
- **根因的跨模型证据：论证，且被相关级证据反驳**
  - 支持方只有论证：「We attribute this to pretraining methodology. Most MLLMs employ CLIP-style contrastive objectives that optimize for semantic alignment rather than geometric structure」— 2505.21649（F）。
  - 反方（相关，2 族）：对 LLaVA-1.5/1.6 的 CLIP、LLaVA-OneVision 的 SigLIP、Qwen2.5-VL-7B 的 ViT 输出训练线性回归，前景物体的平面内旋转角 MAE < 3°。「This contradicts the assumption that MLLM orientation failures originate in the visual encoder.」— 2604.13321（F）
  - 另一方（相关，≥2 族，结论相反）：朝向（左朝/右朝）「are not explicitly encoded, that meaning there is not a direction for this concept in the model's activation space, throughout the entire model across all six models」。— 2603.06054（F）
- **不同论文对根因的说法是否一致：不一致，而且两份探针研究测的不是同一个量**。2604.13321 测的是同一张图/同一前景贴片的**平面内旋转角**（回归，训练与测试用同类「familiar」图像）；2603.06054 测的是 3D 场景里物体**朝左还是朝右**（二分类反事实对）。前者读得出、后者读不出，目前不能判定是相互矛盾还是各自成立。DORI 自己的数据还指向第三种解释：融合方式——同一个 Qwen2.5-3B 上 token-based fusion 74.3% 对线性投影 41.2%（平均粗粒度准确率，Tab.6）。
- **竞争者**
  - DORI 上 LoRA 微调 Qwen2.5-VL-3B（27K 样本）：留出集绝对 +34–40 点，迁移到 3DSRBench/BLINK/SAT 最多 +27 点。（F）
  - 2604.13321 没有提修法，自述：「we still don't know why they fail. Although a full explanation is beyond the scope of this paper, we show that although present, orientation information is spread diffusely across tens of thousands of features. This may or may not be while MLLMs fail to exploit the available orientation information.」；「foreground orientations are sensitive to canonical background orientations, which may make them unreliable in some circumstances」。代码：https://github.com/anjugopinath/MLLM_Orientation（F）
  - 2603.06054 自述局限：只有四个概念、每个概念两类、全是合成数据。（F）
- **剩余空间**：没有人在同一批模型、同一批图上同时测「平面内旋转」与「3D 朝向」两种探针，也没有人对读得出的朝向方向做干预看答案是否翻转。
- **便宜办法**：未找到系统的提示/分辨率消融。un²CLIP 表里朝向一列在编码器微调后没有改善（C4）。
- **数据与基准**：DORI、RotBench（2508.13968）、EgoOrientBench（均只在引用里见到公开性，未核）；2604.13321 的图像与代码公开。

### C6｜计数失败

- **现象**：数图里有几个物体，数量稍大或有干扰物就错。基准：CIVET 合成集、Pixmo-Count、CountBench、BlindTest 的数圆/数交点、围棋盘合成集、VLMBias。
- **现象的跨模型证据**
  - 7 个模型（CLIP、CoCa、LLaVA-Interleave、LLaVA-OneVision、Qwen2-VL、PaliGemma 2、InternVL3）：最好 PaliGemma 2 74.86%，CLIP 20.52%。— [2510.19555](https://arxiv.org/abs/2510.19555)（F）
  - GPT-4o、Gemini-1.5 Pro、Claude-3 Sonnet、Claude-3.5 Sonnet 在 BlindTest 七个任务上平均 58.07%（数两条线的交点 56.84%）。— [2407.06581](https://arxiv.org/abs/2407.06581)（F）
  - MMVP 的 quantity/count 模式（C4）。
- **根因主张（编码器侧）**：(a) 对比式编码器不编码数量（MMVP 的归因；「CLIP 数不到十」一线）；(b) 切片把物体切开或重复（见 C9）。
- **根因的跨模型证据：(a) 只有论证/相关，并被 ≥2 族的探针结果反驳**
  - 「the encoder representation Enc contains sufficient information to directly solve our task, suggesting that the primary problem lies in the decoder」；逐层分析「identifies the output layer as the main source of errors」。正文图是 LLaVA-OneVision，其余模型在补充材料（我没看到补充材料）。只微调输出层：合成 +17.13%、真实 +4.46%，InternVL3 +21.19%、LLaVA-Interleave +20.98%。— 2510.19555（F）
  - Qwen3-VL-32B + 从零训练的玩具 VLM：视觉骨干对数量的表示线性可分并外推，「ruling out perceptual failure」，塌在符号映射阶段；玩具模型上遮掉探针认出的 k 个 token，输出恰好减 k。自述：「our conclusions strictly apply to this architecture」，因为其他开源模型「lacked sufficient baseline counting capabilities」。— [2605.30170](https://arxiv.org/abs/2605.30170)（ICML 2026，F）
  - LLaVA-OneVision-S：SigLIP 输出线性探针区分 4 条腿/5 条腿 95.26%，整机 49.71%，「defaulting to biased answers 99.43% of the time」。— [2505.23941](https://arxiv.org/abs/2505.23941) 附录 A.8、Table 8（F）
- **不同论文对根因的说法是否一致**：编码器说（MMVP）对 解码器/输出层说（2510.19555）对 符号映射说（2605.30170）对 语言先验覆盖说（2505.23941）。后三者都把位置放在编码器之后，但彼此也不相同。2510.19555 还留了一句：「Some pre-training biases persist even after fine-tuning the output layer ... these biases are not localized in the output layer, but are instead more deeply rooted within the model.」
- **竞争者**：只微调输出层（2510.19555）；CogAlign（见 C7）；Molmo 的 point-then-count（在 2502.15969 中作为对比对象出现，A）；locality alignment 在 TallyQA 上有提升（C10，数字未摘录）；避免切片（C9）。
- **剩余空间**：微调输出层后 PaliGemma 2 接近 90%（合成），真实图只 +4.46%。2605.30170 自述假设了「Perceptual Success」：真实场景里的遮挡、伪装造成的检测失败被排除在外。
- **便宜办法**：2510.19555 比较了开放式与封闭式问法（Fig.3，数字未摘录）；Forgotten Polygons 里给边标号 + CoT 能把数边数提上来（C7）。
- **数据与基准**：CIVET、Pixmo-Count（38k 图）、CountBench/CountBenchQA、TallyQA、VLMBias、围棋盘合成集（代码 https://github.com/Russellpang/semproj ，从 PDF 文本摘出，URL 中有换行，未点开核实）。

### C7｜低层几何与形状感知失败（BlindTest、正多边形、Geoperception）

- **现象**：两圆是否相交、线是否相交、哪个字母被圈、正七边形是什么形状、点是否在线上——人接近满分，模型大幅失分。
- **现象的跨模型证据**
  - BlindTest：四个闭源模型平均 58.07%，最好 Sonnet-3.5 77.84%。— 2407.06581（F）
  - 13 个 MLLM（LLaVA-1.5/NeXT/OneVision、Qwen2-VL、InternVL、Molmo、Janus-Pro、Math-LLaVA、G-LLaVA、Math-PUMA、GPT-4-Turbo、GPT-4o 等）：七边形只有 GPT-4o 与 Molmo 超过 1%；GPT-4o 认七边形 92% 但数边只对 58%。— [2502.15969](https://arxiv.org/abs/2502.15969) Table 1（F）
  - Geoperception：最好 Gemini-1.5-Pro 平均 56.98%，开源最好 Pixtral-12B 41.95%；PointLiesOnLine 所有模型不到 30%。— [2412.08737](https://arxiv.org/abs/2412.08737) Table 2（F）
- **根因主张（编码器侧）**：(a) 视觉编码器「shape-blind」，不常见的多边形在嵌入空间里挤成一团；(b) ViT 切块破坏低层几何（Euclid 的假说）。
- **根因的跨模型证据**
  - (a) **相关（弱）**：t-SNE 图，LLaVA-OneVision 为例，「exhibits the same embedding pattern as all other models (Appendix D)」。没有探针，没有干预。— 2502.15969（F）
  - (b) **训练级对比 + 假说**：同一训练框架下 ConvNeXt-Large 学几何概念最快，胜过大 3–5 倍的 ViT；「We hypothesize that CNN architecture extract visual features globally ... ViT architectures split images into discrete patches, making it more challenging to retain the original low-level visual information」；DINOv2 学不动，SigLIP 系「performance in learning basic visual geometry attributes is limited」。— 2412.08737（F）
  - **反方（相关，2 族）**：LLaVA-OneVision-S（SigLIP）与 Phi-3.5（CLIP）的编码器输出，两圆任务与折线图任务线性探针 ≥ 99.47%。「vision encoders contain sufficient visual information to solve BlindTest and that language models fail to decode this information」。— 2407.06581 Fig.14（F）
  - **反方（1 族，结论在解码器）**：CLIP/SigLIP + 线性分类器在长度比较等探针任务上「perform poorly」，但冻结编码器、只微调 LLaVA-1.5 的 LLM 后明显变好，「the bottleneck lies in the decoder's ability to effectively process and utilize the visual information, rather than in the visual representation itself」。— [2502.11492](https://arxiv.org/abs/2502.11492)（F）
- **不同论文对根因的说法是否一致：冲突**。2502.15969 说编码器看不见；2407.06581 说编码器里线性可读；2502.11492 说线性读不出但信息在、解码器是瓶颈。三者任务不同（多边形分类 / 圆相交与折线 / 长度与角度比较），探针方法也不同（t-SNE / 线性 / 线性 + 微调解码器），不能直接互相否定。2407.06581 另给一个结构性解释：late fusion——「VLMs extract visual features from the image before even looking at the question」。
- **竞争者**
  - Euclid：只用合成几何数据训练，Geoperception 上比 Gemini-1.5-Pro 平均高 10.65%，个别任务高 58.56%。（F）
  - VC-CoT（给图加编号标注 + CoT）：13 个模型平均 34.51% → 37.86%，9/13 受益；「annotations alone or CoT without annotations fail to override visual biases」。（F）
  - CogAlign：三个 VLM，Chocolate +4.6%、Math-Vision +2.9%。（F）
  - SVE-Math（GeoGLIP 编码器）：2502.15969 说它的代码仓库缺文件，没能评测。（F，转述）
- **剩余空间**：Euclid 之外，开源模型在 Geoperception 上离 100% 还差 40 点以上；VC-CoT 后平均仍不到 40%。
- **便宜办法**：BlindTest 用两种提示取平均，线宽与图尺寸变化也试过，没有修好；VC-CoT 是提示 + 改图，有效但有限。
- **数据与基准**：BlindTest、Geoperception、2502.15969 的 2000 张多边形图、MathVerse（均公开或可复现，未逐个点开核实）。

### C8｜小目标/局部细节看不清（答案区域越小越错）

- **现象**：答案所在框占图比例越小，准确率越低；把图裁到答案框再放大就能答对。
- **现象的跨模型证据**（TextVQA 验证集，按框面积分 small/medium/large；括号内为 human-CROP 后）：BLIP-2 12.13/19.57/36.32（55.76/52.02/45.73）；InstructBLIP 21.79/30.58/45.30（69.60/…）；LLaVA-1.5 39.38/47.74/50.65（69.95/65.36/56.96）；Qwen-VL 56.42/65.09/68.60（70.35/…）；GPT-4o 65.76/72.81/69.17（75.63/81.32/71.72）。— [2502.17422](https://arxiv.org/abs/2502.17422) Table 1（F）
- **根因主张**：是「看不清」而不是「找不到」——模型的注意力已经落在正确区域，但在给定的输入分辨率/切块粒度下细节没有被编码进去。位置：视觉编码器输入分辨率与 patch 粒度（论文没有把编码器、connector、LLM 三者拆开）。
- **根因的跨模型证据**：**输入级因果干预，≥4 族**（裁剪使小目标准确率大幅上升）；**相关，4 族**（BLIP-2、InstructBLIP、Qwen-VL、LLaVA-1.5 各层对答案框的 attention ratio > 1，且答对答错时都如此）。「具体是编码器的哪一步丢了细节」只有论证。
- **不同论文对根因的说法是否一致**：MMVP 称「Merely increasing the image resolution ... does not boost visual grounding capabilities」（那是 MMVP 上的 CLIP-blind 图对，不是小目标）；S² 表明多尺度的小模型能线性重构大模型的大部分表示（[2403.13043](https://arxiv.org/abs/2403.13043)，F-部分）。未见直接否定「感知限制」读法的论文。
- **竞争者**：ViCrop（用模型自身注意力/梯度自动裁剪，免训练；两个 MLLM、七个 VQA 基准，数字未摘录）。自述：「questions concerning relations and counting are particularly difficult for ViCrop methods to help answer. This is expected as the proposed ViCrop can only focus on one region in the image. We leave extending ViCrop to focus on multiple regions simultaneously for future work.」高分辨率微调、S²、AnyRes 类切片（后者引出 C9）。
- **剩余空间**：human-CROP 后小目标仍只有 55–76%；涉及关系与计数的问题裁剪帮不上。
- **便宜办法**：裁剪（即改输入）有效；换问法未见测试。
- **数据与基准**：TextVQA（公开）。

### C9｜切片 / 填充式视觉编码策略造成的计数与边缘物体错误

- **现象**：高分辨率图被切成固定大小的块分别送进编码器，跨块或落在重叠区的物体被重复计数或被切碎；填充成正方形时模型把与填充同色的真实区域当成不存在。
- **现象的跨模型证据**
  - GPT-4V：切片重叠区内的物体数被翻倍/翻四倍（合成探针图）。LLaVA-1.5：把灰色区域当填充忽略。— [2403.11703](https://arxiv.org/abs/2403.11703) §2、Fig.1/3（F）
  - 数麻将牌（只留待数区域），缩到一个 tile 内不切片：Gemini 2.0 Flash 准确率 0.50 → 0.60，Gemini 2.0 Pro 0.52 → 0.70，GPT-4o 0.45 → 0.48，GPT-4o-mini 0.39 → 0.47。— [2503.09348](https://arxiv.org/abs/2503.09348) Tab.5（F）
  - EntityGrid-QA：切片式方法（IXC-4KHD、LLaVA-NeXT）在被切碎与未被切碎的输入间差 13.0%，不切片的（LLaVA-1.5）只差 3.0%。— [2407.08706](https://arxiv.org/abs/2407.08706) Fig.1(b)（F）
- **根因主张**：编码器输入端的切片/填充策略破坏了物体的完整性与位置连续性。位置：视觉编码器之前的切块与分辨率处理。
- **根因的跨模型证据**：**行为级输入干预，≥3 族**（闭源模型只能做这一层）。没有任何内部读数；按共用口径的三级划分，内部证据是**论证**。
- **不同论文对根因的说法是否一致**：MOAT 只说切片「plays a part」，且 GPT-4o 的改善很小（0.45 → 0.48）；同一张表里把任务从原图简化到「只数」带来的提升（0.18 → 0.45）远大于去掉切片。计数另有编码器之后的解释（C6）。
- **竞争者**：LLaVA-UHD（可变尺寸切片；TextVQA +6.4、POPE +3.2）；HiRes-LLaVA 的 SliceRestore Adapter（「∼12%」）；原生动态分辨率编码器（NaViT、Qwen2-VL 的 2D-RoPE、SigLIP2 NaFlex——2603.12545 把 NaFlex 列为未做的扩展）。
- **剩余空间**：去掉切片后 Gemini 2.0 Pro 数麻将牌仍只有 0.70。
- **便宜办法**：把图缩到一个 tile 内即可部分修复（属于改输入）。
- **数据与基准**：EntityGrid-QA、MOAT（1005 题）、LLaVA-UHD 的合成探针。

### C10｜基本空间关系（左右上下、定位）失败——编码器缺局部语义 / 位置信息

- **现象**：「杯子在桌子上还是桌子下」这类题接近随机。基准：What'sUp、VSR、CV-Bench 2D、RefCOCO、OCID-Ref。
- **现象的跨模型证据**：What'sUp 上各类 VL 模型「all perform poorly」，如在 VQAv2 上微调过的 BLIP 56% 对人 99%。— [2310.19785](https://arxiv.org/abs/2310.19785)（F-部分）；LLaVA-NeXT、LLaVA-OneVision、Qwen2.5-VL、SmolVLM2、Gemma3、PaliGemma2 等「consistent spatial performance gaps across models」。— 2603.12545（F）
- **根因主张（编码器侧，两种）**：(a) 图像级监督的 ViT 没有在每个位置上编码「那里是什么」；(b) CLIP 式全局对齐目标 + 把图拍平成 1D 序列。
- **根因的跨模型证据**
  - (a) **相关 + 训练级干预，2 种编码器（CLIP、SigLIP），1 套 VLM 配方**：MaskEmbed 后 patch 级探针变好，用它训出的 VLM 在 RefCOCO、OCID-Ref、TallyQA、VSR、AI2D 上普遍更好（雷达图，数字未摘录）。— [2410.11087](https://arxiv.org/abs/2410.11087)（F）
  - (b) **训练级对比，1 族（LLaVA-1.5 框架内换编码器）**：AIMv2 > CLIP；SigLIP/SigLIP2「more fragmented gains」；加 2D-RoPE 在 MMVP、VSR 上再涨。— 2603.12545（F）
  - 综合档位：**相关 / 训练级干预；编码器种类 ≥2，但 VLM 配方只有 LLaVA 式一种**。
- **不同论文对根因的说法是否一致：多种竞争解释**
  - 预训练语料：LAION-2B 里常见空间介词出现在不到 0.2% 的数据里。— 2310.19785（F-部分）
  - LLM 侧位置编码被压制：LLaVA-1.5 中视觉 token 范数比文本大 1–2 个数量级；打乱视觉 token 顺序结果变化很小。— 2503.17349（F，单模型，见下节）
  - LLM 注意力的几何分布不对。— AdaptVis [2503.01773](https://arxiv.org/abs/2503.01773)（A）
  - 编码器里读得出、LLM 不用。— 2506.08008（F）；「high linear decodability of spatial features does not ensure their causal deployment」— [2606.31257](https://arxiv.org/abs/2606.31257)（S，只有检索片段与一张表的残片）
  - 2D-RoPE 的 ViT 里左右/前后方向向量共线且正交，去掉 2D RoPE 几何结构被破坏；对物体视觉嵌入做插值干预可改变关系判断。— [2509.19191](https://arxiv.org/abs/2509.19191) §4（F-部分）
- **竞争者**：Locality alignment（代码 https://github.com/iancovert/locality-alignment ）。自述：「One limitation of our work is that we focus on a single VLM training approach – the Llava-style patches-as-tokens architecture ... An important direction for future work is to test locality alignment in other VLM training approaches, with larger LMs, and to evaluate how it composes with other techniques that enhance visual features.」；并且它需要把 MaskEmbed 的 decoder 当 adapter 才有提升。2D-RoPE / 换编码器（2603.12545，自述「incorporating DINOv2 in LLaVA is left out」）。RoPE scaling（2509.19191）。
- **剩余空间**：2603.12545 的结论句是「do not fully resolve it」。
- **便宜办法**：What'sUp 试过把 "behind" 换成更常见的 "in the background"、上调含介词样本权重、微调，结论是这些基本干预不足以解决（F-部分，原句只读到一半）。
- **数据与基准**：What'sUp、VSR、CV-Bench、RefCOCO、OCID-Ref、TallyQA（公开）。

---

## 单模型，待扩（现象或根因只有一个模型族的证据）

| 条目 | 说法 | 证据所在模型 | 出处与层级 |
|---|---|---|---|
| S1 视觉 token 范数压制 LLM 位置编码 | 视觉嵌入范数比文本大 1–2 个数量级，RoPE 被压掉，模型成了 "bag-of-tokens"；归一化 + 中间层特征可改善。作者自称「norm-induced problem is the causal mechanism」 | LLaVA-1.5-7B | [2503.17349](https://arxiv.org/abs/2503.17349)（F） |
| S2 峰值/平均范数比与幻觉率 | 比值越高幻觉样本占比越高 | 分析只在 LLaVA-1.5；修法在 3 个模型上 | [2510.16596](https://arxiv.org/abs/2510.16596) Fig.2（F） |
| S3 ViT 离群 token 与 LLM 离群注意力同位置 | 「highly consistent with each other」 | LLaVA-1.5 | [2410.04514](https://arxiv.org/abs/2410.04514)（F） |
| S4 Test-time register 进 VLM | 去掉离群 token 后注意力图更干净，分数不变 | LLaVA-Llama-3-8B | [2506.08010](https://arxiv.org/abs/2506.08010) Table 6（F） |
| S5 "Fractured magnitude" | 视觉数量表示线性且外推，符号映射塌掉 | Qwen3-VL-32B + 玩具 VLM | [2605.30170](https://arxiv.org/abs/2605.30170)（F） |
| S6 CLIP 的物体幻觉传给 LVLM | OHD-Caps 上 CLIP ViT-B/32 只有 14.3；细粒度对比损失微调到 82.5；换进 LLaVA-1.5 后 Nocaps 80.2 → 83.2 | LLaVA-1.5 | [2410.03176](https://arxiv.org/abs/2410.03176)（F） |
| S7 浅层优于倒数第二层的逐层重训对照 | 见 C3 | 仅 CLIP ViT-L/14 | [2504.21447](https://arxiv.org/abs/2504.21447)（F） |
| S8 ViT 切块不利于低层几何 | ConvNeXt 学得最快；作者标为假说 | Euclid 一套训练框架 | [2412.08737](https://arxiv.org/abs/2412.08737)（F） |
| S9 语言先验盖过编码器证据 | 探针 95.26% → 91.24% → 89.08%（编码器 / projector 后 / LLM 末层），整机 49.71% | LLaVA-OneVision-S | [2505.23941](https://arxiv.org/abs/2505.23941) A.8（F） |
| S10 local token 与 summary token 需要不同的注意力增强 | CHAIR 降幅最多 62.3%（相对 PAI） | LLaVA-1.5（作者称可扩展，未做） | [2501.12206](https://arxiv.org/abs/2501.12206)（F） |
| S11 朝向信息弥散在几万个特征里 | 特征替换实验 | LLaVA 系 + Qwen2.5-VL（两族，但只是描述性性质，未与失败建立联系） | [2604.13321](https://arxiv.org/abs/2604.13321)（F） |

## 查过、但根因不在视觉编码器一侧的

- **否定（negation）**：NegBench 的对象是联合嵌入模型的**文本侧**——「joint embedding-based VLMs frequently collapse affirmative and negated statements into similar embeddings」；CLIP 系在 MCQ-Neg 上接近 25% 随机线，放大到 ViT-H 或换 SigLIP、AIMv2 都不改善。— [2501.09425](https://arxiv.org/abs/2501.09425) Fig.4–5（F）。生成式 VLM 里否定由 LLM 处理；NegBench 补充材料称 LLaVA 的否定表现好于其 CLIP 编码器、归因于 Vicuna（S，只见检索片段）。
- **属性绑定（bag-of-words）**：「CLIP does not lack binding information ... attribute–object bindings are already encoded within CLIP's text and image embeddings」，问题在跨模态对齐，一个线性变换即可修。— [2502.03566](https://arxiv.org/abs/2502.03566)（F）。这是 CLIP 检索场景的结论，不是生成式 VLM。
- **联合嵌入空间的几何不可能性**：证明余弦相似度的联合空间不能同时表示基本内容、属性绑定、空间关系、否定中的任意两项。— [2503.08723](https://arxiv.org/abs/2503.08723)（F-部分）。对象是池化后的全局嵌入，生成式 VLM 用的是 patch token，适用性没有被论证。

---

## KQ1 哪些失败被归因于对比式编码器看不见？换编码器后归因还成立吗？

### Takeaway
被归到「对比式编码器看不见」的有：MMVP 的九类模式（含朝向、计数、视角、位置关系）、朝向（DORI）、多边形形状、低层几何、空间局部语义、小细节。换成 SigLIP、DINOv2 混合或带生成目标的编码器后分数有提升但不大（MMVP 上 +3 到 +13 点），而且提升能否归因于「原编码器看不见」没有被检验——反方向的探针证据反而在增多。

### Cited Findings
- MMVP 把失败直接归给 CLIP：「MLLMs fail in simple questions because their pre-trained CLIP vision encoders overlook crucial visual details in images」。— [2401.06209](https://arxiv.org/abs/2401.06209)
- 所有测过的对比式编码器（含 SigLIP ViT-SO、EVA、DFN、MetaCLIP）在九类模式里只有两类随规模改善。— 2401.06209 Table 1
- 混入 DINOv2（I-MoF）：LLaVA +10.7、LLaVA-1.5 +3.3。— 2401.06209 Table 3
- 编码器微调后 MMVP-VLM 平均最高到 32.6–36.3。— [2505.24517](https://arxiv.org/abs/2505.24517) Table 1
- LLaVA 框架内换 AIMv2 最稳，SigLIP/SigLIP2 增益零散，结论「do not fully resolve it」。— [2603.12545](https://arxiv.org/abs/2603.12545)
- Prismatic 四种编码器上，视觉读出最好的常是 DINOv2，但 DINOv2 版 VLM 在六个任务里没有一个最好；「VLM-based rankings have already led to conclusions that CLIP-style pretraining strategies are the most promising for VLMs ... Our results suggest this might be a premature conclusion.」— [2506.08008](https://arxiv.org/abs/2506.08008) Table 1、§3.3
- Cambrian-1：语言监督的编码器在各类基准上都优于自监督编码器，OCR 与图表差距最大。— [2406.16860](https://arxiv.org/abs/2406.16860) Table 2
- 否定不属于视觉编码器侧（见上节）。

### Inferences
- 「换编码器涨分」与「原编码器看不见」是两件事：前者是训练级干预，同时改了 projector 的输入分布和 LLM 看到的 token 统计。（推导：2506.08008 显示编码器排名在视觉读出与 VLM 读出之间不保序。）
- MMVP 的构造用 DINOv2 当「看得见」的参照，所以它测的是「CLIP 与 DINOv2 的分歧」，不是「CLIP 输出里是否含该信息」。（推导：构造规则 cos_CLIP > 0.95 且 cos_DINO < 0.6 是在池化嵌入上算的，patch token 层面未检验。）

### Gaps
- 没有找到在 MMVP 图对上直接对 patch token 做探针的工作（1 条针对性查询，无结果）。
- 没有找到 2025–2026 新模型（原生分辨率 ViT、SigLIP2）在 MMVP 上的系统成绩表（1 条查询，无结果）。
- Cambrian-1、Prismatic 的多编码器具体增益我没摘数字。

## KQ2 高范数伪影 token 是否被证明会传进 VLM 并造成具体失败？

### Takeaway
「传进去」有 ≥2 个模型族的证据（LLaVA-1.5、LLaVA-OneVision、LLaVA-Llama-3、CLIP/SigLIP × 四种 LLM）。「造成具体失败」没有干净的证明：去掉它们，局部任务涨、全局任务掉；最直接的 register 修法装进 VLM 后总分不变。详见 C1。

### Cited Findings
- V-sink 与 L-sink 的区分及任务依赖的变号效应。— [2604.03316](https://arxiv.org/abs/2604.03316)
- 「ViT sinks are partially propagated into the LLM」；去掉 sink 改善局部任务。— [2510.08510](https://arxiv.org/abs/2510.08510)
- Test-time register 在 LLaVA-Llama-3-8B 上 46.2 对 46.2。— [2506.08010](https://arxiv.org/abs/2506.08010) Table 6
- 把 sink 归给 LLM 自身、并称其形成机制「remain open questions」。— [2503.03321](https://arxiv.org/abs/2503.03321)
- 与幻觉的联系只有 LLaVA-1.5 上的相关。— [2510.16596](https://arxiv.org/abs/2510.16596)、[2410.04514](https://arxiv.org/abs/2410.04514)
- 伪影在 DINOv2、OpenCLIP、DeiT-III 上都有，成因未定。— [2309.16588](https://arxiv.org/abs/2309.16588)

### Inferences
- 2503.03321（sink 的激活维度继承自 LLM）与 2604.03316（V-sink 经 projector 后范数整体偏高、不是少数维度尖峰）可以同时成立：两者描述的可能是不同的 token 群。（推测：没有同一模型上的逐 token 对照。）
- 幻觉文献里「高范数 token → 幻觉」目前是相关加修法有效，修法（重加权 + 对比解码）同时动了很多东西，不能单独归因。（推导：SHIELD 的消融只在 LLaVA-1.5 的 CHAIR 上做。）

### Gaps
- 没找到在 Qwen-VL 原生 ViT、InternViT、SigLIP2 上量化 V-sink 的工作（2 条查询）。
- 没找到「用带 register 的编码器（如 DINOv2-reg）从头训 VLM 并与不带 register 的对照」的实验。
- 2510.08510 的具体数字与 Fig.5 所用模型我没核到。

## KQ3 「信息在编码器里、下游没用上」的证据，各在几个模型族上成立？

### Takeaway
这是本轮证据最厚的一类，至少七篇、覆盖 LLaVA/Prismatic（CLIP、SigLIP、DINOv2、IN-1k ViT）、Qwen-VL、Phi-3-V、InternVL、PaliGemma 2、LLaVA-OneVision、Phi-3.5、Qwen2.5-VL、Qwen3-VL。但几乎全是相关级（探针），而且它们指向的是**编码器之后**的根因，对「编码器侧候选」是竞争解释而不是支持。

### Cited Findings
- 六个 vision-centric 任务，视觉读出 对 VLM 对 盲答（DINOv2）：语义对应 0.536/0.225/0.298，低层匹配 0.819/0.170/0.251，深度 0.887/0.653/0.597，affordance 0.411/0.155/0.154，艺术风格 0.675/0.530/0.446，3D 0.598/0.315/0.311；CLIP、SigLIP、IN-1k 同样掉。Qwen-VL、Phi-3-V、InternVL 同趋势，InternVL 有一处例外。— [2506.08008](https://arxiv.org/abs/2506.08008) Table 1、Fig.3
- 同文：视觉表示在 projector 与 LLM 各层「do not degrade」；prompt-tuning 只小幅改善；同参数量 LoRA 下微调 LLM 比微调 ViT 或 projector 涨得多；VLM 的答案分布与空白图时的答案分布「uncannily similar」。作者保留：「that does not necessarily imply that current visual encoders are sufficient for all visual tasks」。
- 六个 VLM、三个基准：模糊掉问题相关区域后 40%–97% 的样本下一 token 分布几乎不变；这些样本上各模型自己的视觉塔线性探针能以 0.72–0.79 分辨有无扰动，argmax 只在 2%–11% 上变化，「encoder–decoder gap of 0.66–0.71 replicates on all six models」。— [2609.00868](https://arxiv.org/abs/2609.00868)（F，摘要与 §4 两段）
- BlindTest：LLaVA-OneVision-S 与 Phi-3.5 的编码器输出线性探针 ≥ 99.47%。— [2407.06581](https://arxiv.org/abs/2407.06581)
- 朝向：四个编码器 MAE < 3°。— [2604.13321](https://arxiv.org/abs/2604.13321)
- 计数：编码器平均表示足以解题，错在输出层。— [2510.19555](https://arxiv.org/abs/2510.19555)；Qwen3-VL — [2605.30170](https://arxiv.org/abs/2605.30170)；LLaVA-OV-S — [2505.23941](https://arxiv.org/abs/2505.23941)
- 驾驶场景六个小模型：区分「perceptual failure」（信息没线性编码到最后）与「cognitive failure」（编码了仍答错）；物体存在性从编码器中层到 LLM 末层都读得出，朝向全程读不出。— [2603.06054](https://arxiv.org/abs/2603.06054)
- 专用视觉模型在 BLINK 上比最好的多模态 LLM 高 18%–57%（对应估计比 GPT-4V 高 62.8%）。— [2404.12390](https://arxiv.org/abs/2404.12390)（F-部分）

### Inferences
- 探针读得出只说明信息线性可得，不说明 LLM 能以它的方式取到；2506.08008 自己写了「this is a sufficient but not necessary condition」，2606.31257 的标题就是这个反驳。（推导）
- 「信息在、没用上」目前缺的是干预：除 2605.30170 在玩具模型上遮 token 之外，没有看到「沿探针方向改编码器输出 → 整机答案按预期翻转」在 ≥2 个模型族上的实验。（这是我看过的 47 篇范围内的陈述，层面是方法层；针对性查询 3 条。）

### Gaps
- 2510.19555 除 LLaVA-OneVision 外其余模型的逐层图在补充材料里，我没取到。
- 2606.31257（Decodable Is Not Grounded）正文取到了但摘要段没解析出来，只有检索片段，结论细节未核。
- [2606.13870](https://arxiv.org/abs/2606.13870)（Mirage Probes，两个开源 VLM）只读了摘要：区分「靠文本先验作答」与「在潜空间里构造虚假视觉内容」两种情形。

## KQ4 各候选已有修法做到哪一步？

### Takeaway
修法分五类：换/加编码器、编码器后训练（locality alignment、生成式反馈）、编码器内编辑（register 神经元、排版回路头）、取层/融合、推理期处理视觉 token（重加权、sink 门控、裁剪）。逐候选的数字与作者自述局限写在主表各条的「竞争者」里。共同点：编码器侧修法的增益多在个位数，且大多只在 LLaVA 式配方上验证。

### Cited Findings
- 换/加编码器：I-MoF +3.3 到 +10.7（MMVP）— [2401.06209](https://arxiv.org/abs/2401.06209)；AIMv2 替换 — [2603.12545](https://arxiv.org/abs/2603.12545)。
- 编码器后训练：un²CLIP MMVP-VLM 19.3 → 32.6 — [2505.24517](https://arxiv.org/abs/2505.24517)；locality alignment 只在 Prismatic 配方上验证 — [2410.11087](https://arxiv.org/abs/2410.11087)；OHD-Caps 微调使 LLaVA-1.5 Nocaps 80.2 → 83.2 — [2410.03176](https://arxiv.org/abs/2410.03176)。
- 编码器内编辑：test-time register 46.2 → 46.2 — [2506.08010](https://arxiv.org/abs/2506.08010)；排版回路消融 +0.01 到 +1.73 — [2607.02494](https://arxiv.org/abs/2607.02494)。
- 取层/融合：VaLiD — [2411.15839](https://arxiv.org/abs/2411.15839)；浅中深线性融合 — [2504.21447](https://arxiv.org/abs/2504.21447)。
- 推理期：LSG +0.72 / +2.14 — [2604.03316](https://arxiv.org/abs/2604.03316)；SHIELD 比 OPERA 最多好 18%（CHAIR）— [2510.16596](https://arxiv.org/abs/2510.16596)；ViCrop — [2502.17422](https://arxiv.org/abs/2502.17422)。
- 对照（非编码器侧）：只微调输出层，计数合成 +17.13% — [2510.19555](https://arxiv.org/abs/2510.19555)；同参数量下微调 LLM 优于微调 ViT — [2506.08008](https://arxiv.org/abs/2506.08008)。

### Inferences
- 把同一个现象上「编码器侧修法的增益」与「编码器之后修法的增益」放在一起，后者更大的例子有计数（输出层 +17 对 切片 +0.03 到 +0.18）与 vision-centric 任务（LoRA-LLM 对 LoRA-ViT）。这两组数字来自不同数据集与设置，不能直接比大小，只能说方向一致。（类比）

### Gaps
- 多数修法论文我没有核对开源仓库是否真的可用；主表里只列了正文中出现的 URL。
- OpenReview 审稿讨论一条都没查。

## KQ5 有没有两篇论文对同一现象给出相互冲突的根因解释？

### Takeaway
有，至少五组。其中朝向那一组在核对口径后发现两份探针测的不是同一个量，不能直接记为矛盾。

### Cited Findings
1. **MMVP 类视觉缺陷**：编码器看不见（[2401.06209](https://arxiv.org/abs/2401.06209)）对 编码器读得出、LLM 没用（[2506.08008](https://arxiv.org/abs/2506.08008)，点名反驳）。口径差异：前者用 MMVP 图对 + VQA；后者用 CV-Bench/BLINK/MOCHI + 视觉读出。
2. **朝向**：CLIP 式目标不编码几何（[2505.21649](https://arxiv.org/abs/2505.21649)，论证）对 线性可读 MAE < 3°（[2604.13321](https://arxiv.org/abs/2604.13321)）对 全程线性读不出（[2603.06054](https://arxiv.org/abs/2603.06054)）。口径差异：平面内旋转角回归 对 3D 朝左/朝右二分类；真实图贴片 对 CARLA 合成；模型不重叠。
3. **低层几何**：编码器 shape-blind（[2502.15969](https://arxiv.org/abs/2502.15969)，t-SNE）对 线性探针 ≥ 99.47%（[2407.06581](https://arxiv.org/abs/2407.06581)）对 线性探针差但微调解码器可解（[2502.11492](https://arxiv.org/abs/2502.11492)）。任务不同。
4. **视觉注意力汇**：来自 LLM（[2503.03321](https://arxiv.org/abs/2503.03321)）对 来自 ViT 且有害（[2410.04514](https://arxiv.org/abs/2410.04514)、[2510.16596](https://arxiv.org/abs/2510.16596)）对 来自 ViT 且有益（[2510.08510](https://arxiv.org/abs/2510.08510)）对 两者并存（[2604.03316](https://arxiv.org/abs/2604.03316)）。
5. **排版攻击**：弱编码器（[2504.04893](https://arxiv.org/abs/2504.04893)、[2607.02494](https://arxiv.org/abs/2607.02494)）对 提示/LLM 可补偿（[2402.19150](https://arxiv.org/abs/2402.19150)；SCAM 自己也写了 LLM 规模的作用）。
6. **末层特征**：末层丢了细节（[2411.15839](https://arxiv.org/abs/2411.15839)、[2504.21447](https://arxiv.org/abs/2504.21447)）对 末层够用（[2506.08008](https://arxiv.org/abs/2506.08008)）。

### Inferences
- 第 1、3、6 组的共同分歧点是「用什么读出方法判定编码器里有没有」：VQA 读出、t-SNE、线性探针、任务专用头（DPT、patch 余弦）给出的答案不同。（推导）
- 第 2 组在摊开口径后更像「两个不同的量」，是否矛盾需要同图同模型的对照才能定。（推测）

### Gaps
- 没有找到任何一篇在同一批模型和同一批样本上同时跑「编码器探针」与「编码器内干预」来裁决上述任一组分歧的论文（层面：方法层；针对性查询 3 条）。

---

## 检索日志

**查询：19 条 WebSearch**（均为 standard 模式）
1. vision transformer registers artifact tokens LLaVA VLM high-norm tokens effect
2. "Hidden in plain sight" VLMs overlook their visual representations
3. vision encoder orientation rotation blind CLIP SigLIP DINOv2 probing MLLM arXiv 2025
4. VLM counting failure vision encoder linear probe information present but LLM fails arXiv
5. typographic attack CLIP attention heads circuit mechanistic defense LLaVA transfer
6. high-norm visual tokens vision encoder cause hallucination LVLM register tokens mitigate
7. vision encoder negation CLIP image encoder LLaVA negation failure root cause text encoder vs vision
8. multimodal LLM shape-blind polygons vision encoder geometric low-level perception Euclid
9. register tokens CLIP SigLIP vision encoder LLaVA Qwen InternVL outlier visual tokens attention sink from ViT arXiv 2025 2026
10. "VLMs are blind" linear probe vision encoder features contain information follow-up "late fusion" OR "early fusion"
11. vision encoder is not the bottleneck spatial reasoning VLM probing encoder patch features left right relation arXiv 2025（对抗式）
12. MMVP SigLIP DINOv2 multi-encoder still fails CLIP-blind pairs 2025 analysis "MMVP" encoder vs LLM bottleneck（对抗式）
13. ViT position embedding 2D spatial structure lost VLM vision tokens permutation insensitive spatial reasoning root cause
14. CLIP last layer features discard local detail intermediate layers VLM multi-layer visual features fine-grained "Perception Encoder" OR "dense" analysis
15. visual attention sink tokens LVLM originate from vision encoder high-norm ViT outlier tokens analysis hallucination 2025 2026 arXiv
16. MLLM vision encoder intermediate layers contain fine-grained information lost in final layer; multi-layer visual feature fusion analysis counting spatial LLaVA Qwen 2025
17. CLIP vision encoder fine-tuned inside VLM changes; SigLIP DINOv2 "CLIP-blind" OR "SigLIP-blind" pairs still fail MLLM benchmark 2025 2026（无新结果）
18. MMVP benchmark accuracy recent models 2025 2026 InternVL3 Qwen2.5-VL GPT-4o Gemini 2.5 "MMVP" results table saturation（无结果）
19. dynamic resolution image slicing tiling artifacts VLM objects split across tiles counting errors AnyRes analysis patch boundary failure

没有做的：系统的引用链挖掘（只顺着正文里的引用追了几篇）；没有按同义词表逐一枚举。

**取到正文并核对了相关段落/表格（F）：38 篇**
2401.06209、2506.08008、2506.08010、2407.06581、2501.09425、2410.11087、2503.17349、2502.03566、2604.13321、2505.23941、2605.30170、2510.19555、2603.06054、2508.20570、2607.02494、2502.15969、2412.08737、2510.16596、2411.15839、2501.12206、2505.21649、2402.19150、2504.04893、2502.17422、2410.03176、2503.03321、2604.03316、2510.08510、2504.21447、2410.04514、2505.24517、2603.12545、2609.00868、2502.11492、2403.11703、2503.09348、2407.08706、2407.20171（最后一篇偏部分）

**取到正文但只核对了一两段（F-部分）：9 篇**
2309.16588、2503.08723、2504.13181、2404.12390、2310.19785、2402.07865、2406.16860、2509.19191、2403.13043

**只读摘要/引言（A）：6 篇**
2606.13870、2606.06714、2602.08713、2509.11986、2408.16357、2503.01773；另 2503.08216 读到足以判定不属于编码器侧（它讲的是指令 token 劫持注意力）。

**下载了但没读，或只有检索片段（S）：** 2606.31257（摘要没解析出来）、2404.08636、2302.12066、2510.04547、2506.02557、2402.00626、2601.22231；检索片段里出现但没下载的：MMFuser 2410.11829、TGIF、DenseConnector、GenHancer、RotBench 2508.13968、EgoOrientBench、NegBench 的 CVPR 补充材料、乌得勒支大学关于 CLIP 否定的硕士论文、PeakPatch、YARD 2605.31429、RegCache。

**没覆盖到的范围**
- OpenReview 审稿讨论：零条。
- 会议正式版与 arXiv 版的差异：没有逐篇比对；多数只读了 arXiv 最新 HTML 版。
- 补充材料：一份都没取（影响 2510.19555 的跨模型逐层图、NegBench 关于 LLaVA 的说法）。
- 非 arXiv、非英文文献；在审/未公开工作。
- 闭源模型（GPT、Gemini、Claude）内部无法验证，相关证据全部是行为级。
- 2026 年 7–11 月的论文只碰到两篇（2607.02494、2609.00868），这一时段没有做专门的时间限定检索；我的知识截止在 2026-06 之前，之后的工作只能靠检索命中。
- GitHub 仓库：只记录了正文里出现的 URL，没有点开确认是否可运行。
