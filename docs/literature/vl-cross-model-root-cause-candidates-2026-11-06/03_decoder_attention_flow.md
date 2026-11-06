# 03 解码器内部的注意力分配与信息流：跨模型失败现象候选盘点

检索日期 2026-11-06。结构说明：`researcher.md` 要求只按 Key Question 分节；`00_BRIEF` 要求逐候选填字段并附检索日志，且冲突时以它为准。所以本文件先给「候选清单」（主交付），再按五个 Key Question 给 Takeaway / Cited Findings / Inferences / Gaps，最后是未达门槛项与检索日志。

阅读层级：**F** = 取到正文并在本地文本里核对了对应章节或表；**A** = 取到正文但只读了摘要与局限段；**S** = 只有检索片段。所有逐字引文都是从本地下载的 arXiv HTML / PDF 文本里 grep 出来的，不是摘要工具的转述。

最不利的三点先说：
1. 这一块的"跨模型"很大一部分是 LLaVA-1.5 / MiniGPT-4 / Shikra / InstructBLIP 四件套，四者的语言骨干全是 Vicuna/LLaMA 系。按 BRIEF 的定义（编码器或骨干不同即算不同族）它们算多族，但 PAI 作者自己把这点列为局限。只有 C1、C3、C5、C6、C8 有 Qwen / InternVL / Gemma 上的独立证据。
2. "注意力少 → 失败"这条读法已经被多篇论文直接反驳（见 KQ5）：真实物体与幻觉物体拿到的图像注意力一样多；单纯放大图像注意力无效或有害；被抑制的"汇聚 token"有的携带全局信息。任何以"注意力量"为根因的候选都背着这组竞争解释。
3. 长链推理视觉遗忘（原拟 C4）行为层证据全部落在 Qwen 系骨干上，没有进主表（见「未达主表门槛」）。

---

## 候选清单（主表，8 个）

### C1 视觉汇聚 token：解码器把大量图像注意力给了少数与文本无关的图像 token

- **现象**：生成任意文本 token 时，固定位置的少数图像 token（背景/无语义）拿到高注意力；与物体幻觉和细粒度定位差相关。基准：CHAIR、POPE、MME、MMHal、CV-Bench。
- **现象的跨模型证据**
  - Kang et al.（ICLR 2025）在 LLaVA-1.5-7B/13B、LLaVA-1.5-HD、VILA-13B、Qwen2-VL-7B、InternVL2-8B 上做方法评测；现象分析图以 LLaVA-1.5-7B 为主（"The experiment is conducted on LLaVA-1.5-7B and MME Dataset"）。F — [2503.03321](https://arxiv.org/abs/2503.03321) §4、Table 1–2
  - AvisC 称之为 blind tokens，LLaVA-1.5 与 InstructBLIP；附录另有 LLaVA-OneVision、Qwen2.5-VL 的评测（数字未核）。F — [2405.17820](https://arxiv.org/abs/2405.17820) §2、Limitations
  - HAVAE 称之为 Inert Tokens / Vocabulary Hijacking（这些 token 的隐藏状态经 logit lens 跨层解码到同一组无关词），LLaVA-1.5 7B/13B、Shikra、MiniGPT-4、Qwen2-VL-7B。F — [2605.10622](https://arxiv.org/abs/2605.10622) §6.1
  - DAMRO：LLaVA-1.5、LLaVA-NeXT、InstructBLIP。F（摘要与局限）— [2410.04514](https://arxiv.org/abs/2410.04514)
  - LASER 在长推理里也报告了视觉汇聚 token，但分析只在 Qwen2.5-VL-7B。F — [2607.01707](https://arxiv.org/abs/2607.01707) Limitations
- **根因主张**：解码器内某些隐藏维度的 massive activation 使这些图像 token 成为汇聚点，吸走本该给相关图像 token 的注意力预算（Kang）。位置：语言解码器的自注意力，从浅层出现并持续到末层。
- **根因的跨模型证据**：**因果（弱）**。干预一：遮掉汇聚 token 到文本的注意力，性能几乎不变，遮同样数量的随机图像 token 则显著下降（"masking the visual sink tokens has little impact on the model's performance"），这支持"汇聚 token 本身不携带被用到的信息"，图上是 LLaVA-1.5。干预二：把汇聚 token 上的注意力重分给非汇聚图像 token（VAR），在 4 个族上都涨分。干预二是"改了以后变好"，没有演示"让汇聚加重 → 指定失败出现"的翻转。F — [2503.03321](https://arxiv.org/abs/2503.03321) §4.2、Table 1–2
- **不同论文对根因的说法是否一致：不一致，至少五种**
  1. Kang：解码器内 massive activation，类比 LLM 的 BOS 汇聚；训练中如何形成留作未来工作（"We leave the investigation of how visual tokens are recognized as sink tokens during training as future work"）。F
  2. DAMRO：根在视觉编码器（"We attribute to the unexpected attention distribution to an inherent flaw in the visual encoder itself"）。F — [2410.04514](https://arxiv.org/abs/2410.04514)
  3. Luo et al.（ICLR 2026）：区分 ViT 汇聚与 LLM 内生汇聚；ViT 汇聚 token 携带粗粒度全局语义，对需要全局理解的任务有益，应当被利用而不是被抑制（"The propagated ViT sinks capture coarse, high-level contextual information"）。F — [2510.08510](https://arxiv.org/abs/2510.08510) §1、§3
  4. EVAS（EMNLP 2025）：浅层汇聚密、深层稀；**图像汇聚密度高的头对减轻幻觉起正面作用**，修法是把浅层最密汇聚头的注意力矩阵广播给同层其他头。F（摘要与图注）— [EVAS](https://aclanthology.org/2025.emnlp-main.174.pdf)
  5. TokenPenalty（Findings of ACL 2026）：query/key 投影里极端激活的 token"play indispensable roles in contextual understanding"，"perturbing these tokens leads to significant performance drops"。F（摘要）— [TokenPenalty](https://aclanthology.org/2026.findings-acl.628.pdf)
  - 另：HAVAE 声明 Vocabulary Hijacking 与 Visual Attention Sink"empirical results demonstrate significant divergences (detailed in Appendix C)"，并报告直接惩罚对 Inert Token 的注意力"offers no benefit and is in fact detrimental"。F — [2605.10622](https://arxiv.org/abs/2605.10622)
- **竞争者（已有修法）**
  - **VAR**（Kang）：选"图像中心头"，把汇聚 token 的注意力按比例转给其他图像 token；无训练。LLaVA-1.5-7B：CHAIR_S 45.0→43.2、POPE acc 84.76→85.87、MME 1495.5→1513.8；Qwen2-VL-7B：MME 1672.3→1688.5；InternVL2-8B：MME 1648.1→1655.4。失败条件：不做头选择直接全头重分，POPE/MME/MM-Vet 全部变成 0.0（Table 4）。作者局限："the raw attention map may not be perfect for grounding the object because the model may have seen the object incorrectly"。代码：正文未给 URL。F — [2503.03321](https://arxiv.org/abs/2503.03321)
  - **AvisC**：按层找 blind token 后做对比解码。作者局限："its effectiveness declines in tasks requiring precise object counting … This suggests that blind tokens may sometimes carry essential information for quantification"；有额外推理开销。F — [2405.17820](https://arxiv.org/abs/2405.17820)
  - **HAVAE**：只强化不被劫持的头。LLaVA-1.5-7B CHAIR_S 48.2→18.2、CHAIR_I 14.2→3.8（同表 PAI 23.8/6.2，VISTA 15.6/5.2 但 F1 掉到 67.3）。作者局限："its mechanistic origin remains to be fully elucidated … the precise training dynamics that precipitate this behavior remain unclear"；只到 13B。代码 github.com/lab-klc/HAVAE。F — [2605.10622](https://arxiv.org/abs/2605.10622)
  - **RAVE**（需训练）：对视觉 key 的 pre-softmax 分数加可学习的 query–key 偏置。平均 +3 分；推理端到端约 +17%、训练约 +10%。作者局限："evaluation across broader model scales and multimodal architectures remains future work"。F — [2605.18359](https://arxiv.org/abs/2605.18359)
  - **LASER**（RL 后训练）：奖励里加"汇聚抑制"。作者局限："visual sink token identification relies on architecture-specific attention patterns, potentially requiring recalibration when applied to other model families"。代码 github.com/KeViNYuAn0314/LASER。F — [2607.01707](https://arxiv.org/abs/2607.01707)
  - **DIYSink**（需从头训练）：汇聚/非汇聚 token 用两个投影器。F — [2510.08510](https://arxiv.org/abs/2510.08510)
- **剩余空间**：VAR 的涨幅是个位数；计数类任务上抑制汇聚反而掉分（AvisC）；汇聚的识别标准依赖架构（LASER）；训练中如何形成无人给出答案（Kang、HAVAE 都留为开口）。
- **便宜办法**：未找到"换提示能/不能消除汇聚"的直接测试。
- **数据与基准**：CHAIR（COCO 500 图）、POPE、MME、MMHal-Bench、AMBER、CV-Bench、MMVP，均公开。

### C2 文本侧汇聚 token：新 token 主要靠少数 summary / anchor / 已生成 token 生成

- **现象**：自注意力图上出现"柱状"聚合模式，后续 token 过度依赖少数 summary token（句号、换行、BOS、系统提示、或前文已生成的物体词），随后出现幻觉物体。CHAIR、POPE。
- **现象的跨模型证据**
  - OPERA：InstructBLIP、MiniGPT-4、LLaVA-1.5、Shikra。F — [2311.17911](https://arxiv.org/abs/2311.17911) Table 1
  - TAME（ICLR 2025）：称 anchor token，LLaVA-1.5、MiniGPT-4、InstructBLIP、Shikra。F（摘要与局限）— [TAME](https://proceedings.iclr.cc/paper_files/paper/2025/file/4537e2172096d966228d68c428392894-Paper-Conference.pdf)
  - PAS：幻觉预测时模型"effectively ignores the image and instead relies on previously generated output ('prelim') tokens"；LLaVA-1.5、MiniGPT-4、Shikra；仅用对 prelim token 的注意力做幻觉检测 AUROC 约 84–86。F — [2511.11502](https://arxiv.org/abs/2511.11502) Table 1
  - VisFlow：三种模式——注意力偏向尾部图像 token、过度依赖上一个生成 token、过度盯系统提示。A — [2506.12609](https://arxiv.org/abs/2506.12609)
- **根因主张**：解码器继承了 LLM 的"信息聚合到锚点 token"的习惯；聚合之后前面的图像 token 被忽略（OPERA）。TAME 进一步归到 query–key 矩阵特征谱（均值非零、方差极化）。
- **根因的跨模型证据**：**相关**（注意力图样 ↔ 幻觉，4 个 Vicuna 系模型）；OPERA/TAME 的解码干预在这 4 个模型上降低幻觉，属于弱因果。OPERA Table 1（max 512 token）CHAIR_S：InstructBLIP 30.0→16.6、MiniGPT-4 24.2→22.6、LLaVA-1.5 20.6→14.2、Shikra 22.0→14.2。F — [2311.17911](https://arxiv.org/abs/2311.17911)
- **说法是否一致**
  - TAME 直接否定 OPERA 的处方："we find that penalizing summary tokens is not necessary: merely intervening in the query-key parameters variance, without costing extra inference time, still alleviates hallucinations"，并承认"Why anchor tokens affect model performance remains elusive"。F
  - Yang et al.（C7）把同一现象归到少数"幻觉头"偏向文本 token，而非某类 token。F
  - OPERA 自己把一部分失败归到训练得来的共现偏置而非聚合机制："Such hallucinations should blame MLLM's strong bias between 'road' and 'cars', which is learned during the training phase"。F
- **竞争者**
  - **OPERA**：beam search 里加 over-trust 惩罚 + 回滚。作者局限："OPERA demonstrates marginal gains when addressing hallucinations in short answers (< 10 tokens), primarily due to the hysteresis of knowledge aggregation patterns"；"can not address all kinds of the hallucinations"。开销：TARAC 实测 OPERA 时间开销 7.79×，FCCT 实测 TPOT 1.9×；SPARC 在长描述上测到 OPERA 使 CLAIR 分数下降（IIW-400 56.36→51.02）。F — [2311.17911](https://arxiv.org/abs/2311.17911)；[2504.04099](https://arxiv.org/abs/2504.04099)；[2511.05923](https://arxiv.org/abs/2511.05923) Table 7；[2502.01419](https://arxiv.org/abs/2502.01419) Table 1
  - **TAME**：解码时调 query-key 特征谱方差，声称无额外推理时间。代码 github.com/Everlyn-Labs/ANTRP。F
  - **FarSight**：改因果掩码上三角做"attention register"吸收离群 token 的注意力。A — [2505.16652](https://arxiv.org/abs/2505.16652)
  - **PAS**：只做检测。作者局限：只测开放式描述与物体存在幻觉；对非全自注意力变体"our hypothesis/observations might not hold"。F — [2511.11502](https://arxiv.org/abs/2511.11502)
- **剩余空间**：短答案（<10 token）无效；强共现偏置下无效；机制层解释作者自认不清楚。
- **便宜办法**：未找到。
- **数据与基准**：CHAIR、POPE、MME、GPT-4V 辅助评测，公开。
- **注意**：本候选的全部证据都在 Vicuna/LLaMA 骨干上，未见 Qwen/InternVL/Gemma 上对"summary token 柱状模式 ↔ 幻觉"的独立复测。

### C3 图像注意力 / 视觉依赖随已生成长度衰减，长描述后段幻觉增多

- **现象**：生成越长，输出对图像的依赖越低，幻觉物体集中在后段。CHAIR（512 token）、AMBER、长描述 IIW-400 / DOCCI。
- **现象的跨模型证据**
  - LURE（ICLR 2024）：幻觉物体在句子后段的比例，MiniGPT-4 0.227、LLaVA 0.331、LLaMA-Adapter 0.442（Table 16，6 个开源模型）。F — [2310.00754](https://arxiv.org/abs/2310.00754)
  - M3ID（CVPR 2024）：把 VLM 建模为 fading-memory 自回归系统，visual prompt dependency 随生成下降并与幻觉相关；LLaVA、InstructBLIP、mPLUG-Owl2。F（§1、§4）— [2403.14003](https://arxiv.org/abs/2403.14003)
  - IKOD：5,000 张 COCO 图，LLaVA-1.5 与 InstructBLIP 上"As the sequence progresses, image attention clearly declines. Moreover, hallucinated tokens tend to cluster in low-attention regions"。F — [2508.03469](https://arxiv.org/abs/2508.03469) §3
  - SPARC：LLaVA-1.5、LLaVA-NeXT、Qwen2-VL；"As the generation context length increases, image attention diminishes"且变得更噪。F — [2502.01419](https://arxiv.org/abs/2502.01419) Fig. 2、§3.2
  - VISTA：用 logit 排名而非注意力量，"gradual visual information loss – visually grounded tokens gradually become less favored throughout generation"；LLaVA-1.5、MiniGPT-4、Shikra、InstructBLIP。F — [2502.03628](https://arxiv.org/abs/2502.03628)
  - TARAC（LLaVA-1.5、Qwen2-VL、InternVL）、ILVAD（LLaVA-1.5/NeXT、Qwen2-VL、Qwen3-VL-8B、InternVL3-8B）、CAAC（"the hallucinatory tokens appear later in the generated sequence"）。F — [2504.04099](https://arxiv.org/abs/2504.04099)；[2605.20965](https://arxiv.org/abs/2605.20965)；[2505.21472](https://arxiv.org/abs/2505.21472)
- **根因主张**：自回归生成中文本上下文越来越长，图像条件被稀释；位于解码器对图像 token 的注意力（随生成步）与由此决定的条件依赖。
- **根因的跨模型证据**：**相关**（≥3 个族：LLaVA、InstructBLIP、Qwen2-VL、InternVL）；**因果（弱）**：推理时把图像注意力/图像条件补回去能降幻觉，在 LLaVA、Qwen、InternVL 上都有（ILVAD：Qwen3-VL-8B CHAIR_S 51.6→45.2，InternVL3-8B 21.2→16.8）。F — [2605.20965](https://arxiv.org/abs/2605.20965) Table 1
- **说法是否一致：不一致**
  1. 稀释 / fading memory（M3ID、IKOD、SPARC、TARAC）。
  2. RoPE 长程衰减：远离指令的图像 token 交互弱（CCA，只在 LLaVA 上重训验证；TokenPenalty 归为"positional information decay"；VisFlow 提到 RoPE 造成的视觉注意力偏置）。F/A — [2410.15926](https://arxiv.org/abs/2410.15926)；[TokenPenalty](https://aclanthology.org/2026.findings-acl.628.pdf)；[2506.12609](https://arxiv.org/abs/2506.12609)
  3. 依赖前文已生成 token（PAS）与滚雪球（FarSight 把幻觉分成 initial 与 snowball）。F/A
  4. 混淆因素：TARAC 附录指出，把重复出现的正确 token 算进去以后，正确 token 也在低图像注意力区出现峰（"repeated tokens, despite having low attention on image tokens, can be inferred from the preceding correct token"），即"低图像注意力"并不专属于幻觉。F — [2504.04099](https://arxiv.org/abs/2504.04099) 附录
  5. 见 KQ5：Same Attention, Different Truths 报告真实物体与幻觉物体在中后层拿到同样强的图像注意力。F — [2608.07302](https://arxiv.org/abs/2608.07302)
- **竞争者**
  - **M3ID**：放大图像条件相对无条件分布的互信息；可配 DPO 训练。F — [2403.14003](https://arxiv.org/abs/2403.14003)
  - **PAI**：放大图像 token 注意力 + 减去纯文本 logits。CHAIR_S（greedy）：LLaVA 46.6→24.8、MiniGPT-4 32.8→26.3、Shikra 51.2→37.6。作者局限："The language decoders of existing open-source LVLMs are primarily models from the LLaMA-family. It is worth exploring whether the issues of image neglect and text inertia are introduced by LLaMA"；"Its upper limit depends on the capabilities of the well-trained model"。FCCT 实测 PAI 的 TPOT 2.6×。F — [2407.21771](https://arxiv.org/abs/2407.21771)；[2511.05923](https://arxiv.org/abs/2511.05923)
  - **SPARC**：只选择性地、逐步地放大。LLaVA-1.5 上 CLAIR：IIW-400 56.36→61.49、DOCCI 59.26→62.70；同表 OPERA −5.34、VCD −4.20、PAI +0.50。关键观察："increasing the influence of all visual tokens reduces recall"。代码 github.com/mingi000508/SPARC。F — [2502.01419](https://arxiv.org/abs/2502.01419)
  - **IKOD**：KV 合并得到更聚焦图像的视图再协同解码；0.205 s/item 对 greedy 0.115。作者局限："When the input image has some misleading information, excessive focus on the image could make models prone to generating responses that go against common sense"；只测两个模型。F — [2508.03469](https://arxiv.org/abs/2508.03469)
  - **TARAC**：累积历史图像注意力再注入；约 +4% TPOT；"reduces hallucinated sentences by 25.2% on CHAIR"。作者局限："A current limitation is the reliance on fixed hyperparameters"。F — [2504.04099](https://arxiv.org/abs/2504.04099)
  - **ILVAD**：用前几个生成 token 的跨层注意力做显著图，生成中持续增强。代码 github.com/ytx-ML/ILVAD。F — [2605.20965](https://arxiv.org/abs/2605.20965)
  - **CAAC**（github.com/mehrdadfazli/CAAC）、**VISTA**（激活空间转向，github.com/LzVv123456/VISTA；HAVAE 表里 VISTA 在 LLaVA-1.5-7B 上 F1 从 76.4 掉到 67.3）、**MemVR**（中层 FFN 重注入图像 token，A）、**RIVS**（IJCAI 2026，表示干预，A）、**CCA**（改位置对齐并重训 LLaVA，POPE-COCO 平均 acc 81.38→86.86）。
- **剩余空间**：多数方法以 CHAIR 降幅报告，SPARC 指出现有方法"improve the precision of MLLMs at the cost of recall"；IKOD 承认图像本身有误导信息时过度看图有害；没有论文给出"长度本身"与"累积文本内容"的分离实验（未找到）。
- **便宜办法**：未找到针对长描述的换提示对照。
- **数据与基准**：CHAIR（COCO）、AMBER、IIW-400、DOCCI、POPE，公开。

### C5 图像信息只在浅—中层进入文本位置，深层几乎不再读图像 token

- **现象**（内部现象）：深层对图像 token 的注意力极低；敲掉深层的"图像→文本"注意力或直接删掉深层图像 token，多数基准分数不变。被归因的行为失败：物体幻觉（PAINT、MINT、Devils）、需要细粒度/后期才知道找什么的任务（定位、OCR）在早剪枝下崩。
- **现象的跨模型证据**
  - FastV：LLaVA-1.5、QwenVL-Chat、Video-LLaVA；LLaVA-1.5 第 2 层之后图像 token 平均注意力只有系统提示的 0.21%，前两层为 50%。F — [2403.06764](https://arxiv.org/abs/2403.06764) §1
  - Zhang et al.（CVPR 2025）：LLaVA-1.5-7b/13b、LLaVA-v1.6-Vicuna-7b、Llama3-LLaVA-NEXT-8b；注意力敲除显示两阶段（低层整体图像→问题 token，中层物体信息→问题 token，再到末位置），第一段敲除平均降约 60%、第二段约 21%；LLaVA-v1.6-13B 删掉最后 20 层的图像 token 准确率不变、推理时间约 −40%。F — [2411.18620](https://arxiv.org/abs/2411.18620) §5、附录
  - Kaduri et al.：InternVL2 与 LLaVA-1.5，跨模态流集中在中层（InternVL2 约 25% 的层、LLaVA-1.5 层 4–20 约 50%）。F — [2411.17491](https://arxiv.org/abs/2411.17491) 附录
  - FCCT：LLaVA-1.5-7b、Qwen-VL-Chat、LLaVA-NeXT（另提 InternVL）；末 token 的中层 MHSA 是跨模态聚合关键。F（摘要与表）— [2511.05923](https://arxiv.org/abs/2511.05923)
  - Information Horizon：LLaVA-1.5-7B 与 Qwen2.5-VL-7B，深层（约第 20 层后）现有剪枝方法不优于随机；视界位置随任务变——Qwen2.5-VL-7B 上 ScienceQA/MME/POPE 约第 20 层、OCRBench/TextVQA 约第 27 层；LLaVA-1.5-7B 上 15 对 24 层。F — [2512.07580](https://arxiv.org/abs/2512.07580) §4.2
  - PID Flow：LLaVA-1.5-7B/1.6-7B，language-unique 信息在末层约占 82%，协同 <2%。F（摘要）— [2602.15580](https://arxiv.org/abs/2602.15580)
  - Basu et al.（LLaVA、多模态 Phi-2，A）；Neo et al.（LLaVA，附 LLaVA-Phi，F）；HiMAP、ShortV（A）。
- **根因主张**：两种相反的用法——(a) 这是正常且高效的信息流（图像信息早已搬进文本位置），所以可以剪；(b) 这是缺陷，深层"不再读图"导致后续决策脱离图像。位于解码器跨模态注意力的层分布。
- **根因的跨模型证据**：对"信息流发生在浅—中层"是**因果**（注意力敲除/剪除后输出概率按预期变化；LLaVA 系、InternVL2、Qwen-VL、Qwen2.5-VL）。对"深层不读图**造成**幻觉"只有**相关 + 弱因果**（PAI/PAINT/Devils 放大后幻觉降，主要在 Vicuna 系）。
- **说法是否一致：不一致，且直接相反**
  - Seeing but Not Believing（ICLR 2026）："shallow layers focus primarily on text, while deeper layers sparsely but reliably attend to localized evidence regions"（LLaVA、Qwen、Gemma、InternVL）——深层的少量图像注意力是有用的定位信号，不是"不读图"。F — [2510.17771](https://arxiv.org/abs/2510.17771)
  - Devils in Middle Layers：中层才是关键，再分"visual information enrichment"与"semantic refinement"两段；并指出 Shikra"consistently exhibits extremely high visual attention ratios at nearly all layers"，第 0 层高注意力在 Shikra、MiniGPT-4 上不出现。F — [2411.16724](https://arxiv.org/abs/2411.16724) Limitations、Fig. 注
  - Feather the Throttle：FastV 式早剪枝在定位任务上崩，原因是 RoPE 长程衰减使靠图像上方的 token 被剪掉；多数基准不掉分说明"many benchmarks require minimal visual grounding"。只在一个自训 VLM（SigLIP + Llama 2 7B）上做。F — [2412.13180](https://arxiv.org/abs/2412.13180)
  - Cohen et al.：实体识别占用了中层，"allowing few layers for consecutive reasoning"——问题是图像处理发生得太晚而不是太早结束。探针实验只在 LLaVA 式模型。F（摘要与局限）— [2412.14133](https://arxiv.org/abs/2412.14133)
  - Seeing without Looking：去掉大量图像 token 在幻觉基准上只略降，归因于基准不测视觉。A/F — [2605.22903](https://arxiv.org/abs/2605.22903)
- **竞争者**
  - **PAI**（见 C3）；**PAINT**（只放大 local 与 summary 两类图像 token，A，[2501.12206](https://arxiv.org/abs/2501.12206)）；**MINT**（遮掉无关图像 token + 对比解码，A，[2502.00717](https://arxiv.org/abs/2502.00717)）。
  - **Devils 的头间注意力整合**：LLaVA-1.5-7B/13B、Shikra-7B、MiniGPT-4-7B；SVAR 检测 AUROC 最高 74%。作者局限："identifying the specific range of these stages remains somewhat subjective"。代码 github.com/ZhangqiJiang07/middle_layers_indicating_hallucinations。F — [2411.16724](https://arxiv.org/abs/2411.16724)
  - **IRI**（FCCT）：把中层表示注入后层；LLaVA-1.5-7b POPE-adversarial 78.96→85.17，TPOT 1.0×（同表 VCD 2.7×、OPERA 1.9×、PAI 2.6×）。F — [2511.05923](https://arxiv.org/abs/2511.05923) Table 7
  - **VEA**（Seeing but Not Believing，见 C6）。
- **剩余空间**：信息视界随任务和模型能力移动（OCR 更深、强模型更深），固定层段的方法在跨任务时无依据；没有论文在同一组模型上同时测"深层图像注意力量"与"深层图像注意力是否指向证据"并与失败做因果对照（未找到）。
- **便宜办法**：未找到。
- **数据与基准**：GQA 子集（Zhang）、COCO/CHAIR、POPE、TextVQA、OCRBench、RefCOCO 类定位，公开。

### C6 看见了但没用上：证据已在注意力/隐藏状态里，最终答案仍错

- **现象**：模型答错时，(a) 深层注意力仍落在正确证据区域；(b) 视觉属性可从隐藏状态线性解码，成功与失败样本的解码精度几乎相同；(c) 同一视觉编码器的直接读出远高于 VLM 自己的回答。任务：TextVQA 等证据标注 VQA、反事实颜色/大小图、视觉中心基准（深度、对应）。
- **现象的跨模型证据**
  - Liu et al.（ICLR 2026）：LLaVA-NeXT 7B/13B、Qwen2.5-VL 7B/32B、Gemma3 4B/27B、InternVL3.5 8B/14B。F — [2510.17771](https://arxiv.org/abs/2510.17771) Table 1–2
  - Zhang et al.（ICLR 2025）：LLaVA-1.5、InstructBLIP 等，TextVQA 上对 GT 框的注意力比"is greater than 1 in most layers, showing that the MLLMs know where to look in the image even when they fail to answer correctly"。F — [2502.17422](https://arxiv.org/abs/2502.17422) Fig. 3
  - Arbitration Failure（2604.09364）：10 个 VLM（DeepSeek-Janus、LLaVA-NeXT、InternVL2、Qwen2-VL、BLIP-2 等，含 LLaVA-v1.5-13B、InternVL2-26B、Qwen2-VL-72B）；视觉属性早层线性可解码 AUC>0.86，成功/失败样本几乎相同；末层 logit 差与接地结果相关 ρ=0.847；样本层面用编码强度预测结果 AUC=0.528。F — [2604.09364](https://arxiv.org/abs/2604.09364) 摘要、§1、§5
  - Fu et al.：VLM 在视觉中心任务上远低于自身视觉编码器的直接读出，常到随机水平；"vision representations throughout projector and LLM layers do not degrade and can still solve the task with a visual probing strategy"。F — [2506.08008](https://arxiv.org/abs/2506.08008) §1
  - VISTA："hidden genuine information – visually grounded tokens though not being eventually decoded still retain relatively high rankings at inference"（4 个 Vicuna 系模型）。F — [2502.03628](https://arxiv.org/abs/2502.03628)
  - Jiang et al.（ICLR 2025）：对图像表示做 logit lens，真实物体概率高于幻觉物体；LLaVA 与 InstructBLIP。F（摘要）— [2410.02762](https://arxiv.org/abs/2410.02762)
- **根因主张**：瓶颈在解码器如何在视觉证据与语言先验之间裁决（arbitration），而不在感知；位于解码器后段把图像位置上的信息转成输出 logit 的通路。
- **根因的跨模型证据**：**因果**。全序列激活修补（把反事实运行的整段 token 表示换入）翻转 60–84% 的输出，末 token 修补只有 0–1%；部分 token 分解显示"image tokens carry almost all of the causal effect, while patching text tokens yields only a marginal effect"；10 个模型、多个族。F — [2604.09364](https://arxiv.org/abs/2604.09364) §1、§6。另：Fu et al. 微调 LLM 部分最能改善并减轻语言先验（因果，训练层面）。F — [2506.08008](https://arxiv.org/abs/2506.08008) §4.3
- **说法是否一致**
  - Liu et al. 给了两个并列解释而未区分："Textual Information Dominance"与"Visual Context Under-utilization"（类比 RAG 中上下文未被利用）。F
  - Fu et al.：LLM 没学会用视觉表示并继承语言先验；提示调优只边际改善。F
  - 2405.18415：信息在潜空间但"can only be effectively decoded with enough training data"——数据频率解释。A — [2405.18415](https://arxiv.org/abs/2405.18415)
  - Same Attention, Different Truths：幻觉分两类——视觉不确定（遮掉高注意区域即消失）与上下文先验（遮掉后仍在、注意力漂到别处）。即"看对地方但没用上"只覆盖一部分失败。F — [2608.07302](https://arxiv.org/abs/2608.07302) 摘要
  - Visuals Lie（2606.17389）：注意力结构指标预测对错接近随机（52–55%），隐藏状态探针 AUROC>0.95；但遮掉最受关注的 30% patch，LLaVA 掉 8.2pp、PaliGemma 掉 11.3pp——"attention patterns enable feature extraction but do not encode uncertainty about those features"。F — [2606.17389](https://arxiv.org/abs/2606.17389) §5
- **竞争者**
  - **VEA**（Liu et al.）：用深层注意力选证据区，遮掉其余再答。Exact Match：LLaVA-NeXT-7B 38.5→49.6、Qwen2.5-VL-7B 73.4→78.4、Gemma3-4B 56.6→61.2、InternVL3.5-8B 79.3→83.2。作者局限："attention may not always fully capture all the internal mechanisms of evidence localization"；需要中间激活，API 模型用不了；要逐模型做层剖面。代码：正文未见 URL。F — [2510.17771](https://arxiv.org/abs/2510.17771)
  - **ViCrop**（Zhang et al.）：用注意力/梯度图裁剪放大再答。TextVQA LLaVA-1.5 47.80→55.17（rel-att）/56.06（grad-att）。作者局限："questions concerning relations and counting are particularly difficult for ViCrop methods to help answer"；时间开销数秒。代码 github.com/saccharomycetes/mllms_know。F — [2502.17422](https://arxiv.org/abs/2502.17422)
  - **激活转向**（2604.09364）：线性与 SAE 引导，早层，"improve visual grounding by up to +3.8% with degrading performance in some setups"。作者局限："Our analysis relies on synthetic counterfactual images"；大小类别的改写一致率只有 48–54%。F
  - **知识擦除**（Jiang et al.）：把图像特征对幻觉物体方向正交化，COCO2014 幻觉最多降 25.7%；代码 github.com/nickjiang2378/vl-interp。F（摘要）
  - **LoRA 微调 LLM**（Fu et al.）：每个视觉中心任务 5,000 例，等参数量下微调 LLM 比微调投影器或 ViT 准确率更高，也最能压掉语言先验偏置；需要任务数据。F — [2506.08008](https://arxiv.org/abs/2506.08008) §4.3
- **剩余空间**：VEA 与 ViCrop 都是"改输入让证据更显眼"，没有修裁决通路本身；转向只 +3.8% 且有的配置变差；关系与计数类问题 ViCrop 无效。修补实验用的是合成反事实图，自然图像上未验证（作者自列）。
- **便宜办法**：换提示基本无效有两条直接证据——VEA 表中"Inst"（指令提示）基线相对 Base 只有 −0.6 至 +0.8 EM；Fu et al."Prompt-tuning the VLM improves performance marginally, but with diminishing improvements and does not close the gap"。F
- **数据与基准**：TextVQA、带证据框的 VQA 集（Liu et al. 4 个任务）、CV-Bench/BLINK 类视觉中心任务、合成反事实颜色/大小图（2604.09364），多数公开。

### C7 少数偏文本的注意力头驱动物体幻觉

- **现象**：描述任务中的幻觉物体词，其概率主要由少数中深层注意力头贡献；这些头对文本 token 的注意力远高于对图像 token。CHAIR、POPE。
- **现象的跨模型证据**
  - Yang et al.（ICLR 2025）：LLaVA-7B 与 MiniGPT-4 上做归因；附录在 Llama-3.2-11B-Vision、LLaVA-v1.5-13B、Chameleon-30B、LLaVA-v1.6-34B 上评测修法（CHAIR_S：28.4→22.6、48.6→38.8、38.0→34.8、23.2→20.4）。F — [Yang et al.](https://proceedings.iclr.cc/paper_files/paper/2025/file/8001c3568152d134d821cd46d4d84768-Paper-Conference.pdf) Table 9
  - VHR：InstructBLIP-7b、LLaVA-1.5-7b、LLaVA-NeXT-7b，用 Vision-aware Head Divergence 找对视觉敏感的头。F（摘要、§4.1）— [2412.13949](https://arxiv.org/abs/2412.13949)
  - SPIN：LLaVA-1.5、MiniGPT-4、Shikra、Qwen-VL、Qwen2.5-VL；"hallucinations can be attributed to a dynamic subset of attention heads in each layer"。F（摘要、局限）— [2505.16411](https://arxiv.org/abs/2505.16411)
  - AllPath（NeurIPS 2025）：幻觉不来自单一路径，而是 image→input-text、image→output-text、text→text 三条路径的交互，且随问答格式（判别式/生成式）变化。F（摘要、局限）— [2511.17254](https://arxiv.org/abs/2511.17254)
- **根因主张**：这些头在视觉指令微调后几乎没变（"lazy"），注意力模式更像底座 LLM；位于解码器中深层 MHA。
- **根因的跨模型证据**：**因果**（头级干预）。Yang：因果中介分析显示 MHA 对幻觉词概率的贡献大于 MLP；下调这些头对文本 token 的注意力显著降幻觉，"while increasing attention on image tokens has no effect"，且"this intervention is effective specifically for hallucination heads"；幻觉头偏文本"up to five times"。归因在 LLaVA-7B 与 MiniGPT-4 两个模型上做（MiniGPT-4 上显著的头更少）。F。SPIN、VHR、HAVAE、QK Steering 在更多族上做了头级/模式级干预并降幻觉。
- **说法是否一致**
  - 头是否固定：Yang 是静态的一组头；SPIN 是"dynamic subset"，每个 query token 重选。
  - 该动哪一侧：Yang——压文本有效、抬图像无效；VHR / HAVAE / VAR——强化视觉头有效；SPIN——压低图像注意力低的头。三种处方都报告有效，没有同条件对比（未找到）。
  - QK Steering：幻觉信号集中在中层 QK 乘积的主奇异模、且在对称（内容相似）通道里；反对称通道无信号。F — [2606.20419](https://arxiv.org/abs/2606.20419)
  - Nullu 把同一失败放在 MLP 权重的"HalluSpace"里（含 LLM 先验），与"MHA 贡献大于 MLP"不同位置。F（摘要、§3）— [2412.13817](https://arxiv.org/abs/2412.13817)
  - VHR 自列："there may be other architectural factors—such as those in the vision encoder and the FFN module in the LLMs—that contribute to hallucinations but were not directly addressed"。F
- **竞争者**
  - **AD-HH / TF-HH**（Yang）：解码时对选中头关掉文本注意力 / 微调这些头。LLaVA-v1.5-7B COCO 描述幻觉率最多降 1.7×。代码 github.com/TianyunYoung/Hallucination-Attribution。F
  - **SPIN**："reducing hallucination scores up to 2.7× while maintaining F1"。作者局限："Our method's effectiveness is somewhat reduced when paired with sampling-based decoding strategies (e.g., nucleus sampling)"；需要权重访问。F — [2505.16411](https://arxiv.org/abs/2505.16411)
  - **VHR**：强化后 14 层效果最好，"further reinforcement degrades the model's generation quality"。代码 github.com/jinghan1he/VHR。F
  - **AllPath**：代码 github.com/SooLab/AllPath。作者局限："we do not investigate what causal pathways are most effective for different types of questions, nor do we explore training strategies"；失败例：两条路径都不可靠时干预无效。F
  - **QK Product Steering**（Findings of EMNLP 2026，静态权重编辑、零推理开销、免数据）：Qwen2.5-VL-7B、InternVL3-8B、Pixtral-12B，CHAIR_S 平均相对降 4.0%，随机模对照无变化。作者局限："it does not explicitly capture position-dependent effects such as rotary positional embeddings"；"the best configuration may vary by architecture"。F — [2606.20419](https://arxiv.org/abs/2606.20419)
  - **Nullu**（静态权重编辑，MLP 零空间投影，无推理开销）：LLaVA-1.5、MiniGPT-4、mPLUG-Owl2。代码 github.com/Ziwei-Zheng/Nullu。F（摘要、算法）
- **剩余空间**：静态编辑里幅度最小（QK Steering 相对 4.0%）；头的身份在模型间不共享，每个模型要重新找；采样解码下效果减弱；"压文本"与"抬图像"哪种对哪类失败有效未被区分。
- **便宜办法**：未找到。
- **数据与基准**：CHAIR、POPE、MCQ-POPE、MME、AMBER，公开。

### C8 空间关系题：图像注意力量少且落点的几何分布不对

- **现象**：两物体的简单空间关系（under / behind / left of）答错。WhatsUp（Controlled A/B、COCO、VG）、VSR。
- **现象的跨模型证据**：LLaVA-1.5、LLaVA-1.6，附录 Qwen2-VL。F — [2503.01773](https://arxiv.org/abs/2503.01773) Table 1–2、Appendix B
- **根因主张**：图像 token 占输入约 90% 却只拿到约 10% 的注意力；更关键的是中间层注意力在图像上的空间分布是否对准物体实际位置。位于解码器中间层对图像 token 的注意力分布。
- **根因的跨模型证据**：**因果（弱）+ 相关**。相关：答对与注意力对准物体位置强相关。干预：对图像注意力 logits 做温度缩放（置信高时锐化、低时展平），VSR F1：LLaVA-1.5 51.3→62.5、LLaVA-1.6 29.4→39.3；Qwen2-VL 上"on VG_two_object … our method yields a significant improvement of 10+ absolute points"。F
- **说法是否一致**：作者自己否定了"量"的解释——"simply increasing attention to image tokens fails to improve spatial reasoning"，问题在几何分布。作者同时声明方法"are not designed to handle errors outside the language model's capabilities, such as the CLIP failures discussed by Tong et al."，即编码器侧失败是并列解释。F
- **竞争者**：**ScalingVis / AdaptVis**（同文）；同表 VCD、DoLa 在 VSR 上基本无效（LLaVA-1.5 F1 50.6、53.2）。作者局限："the optimal α and β is different across different distributions and prompts. This dependence on a validation set for tuning poses a limitation"。代码 github.com/shiqichen17/AdaptVis。F
- **剩余空间**：LLaVA-1.6 修后 VSR F1 仍只有 39.3；最优温度随数据分布和提示变。
- **便宜办法**：未找到直接测试。
- **数据与基准**：WhatsUp、VSR，公开。
- **注意**：本候选只有一篇论文支撑，跨族靠同文附录。

### C9 多图输入：位置偏置与跨图信息串扰

- **现象**：(a) 交换图片顺序预测就变，开源模型偏向靠后的图、闭源模型中间位置弱；(b) 描述某张图时混入另一张图的内容。PQA、BLINK、MIRB、Mantis-Eval、MuirBench、Winoground、VisMin。
- **现象的跨模型证据**
  - SoFA（CVPR 2025）：OpenFlamingo、Idefics2、InternVL2、Mantis、LLaVA-NeXT(-Interleave)、VILA，及 GPT-4o 等闭源模型。F — [2503.13792](https://arxiv.org/abs/2503.13792) §1、Table 2
  - FOCUS：InternVL3、Qwen2.5-VL、Qwen3-VL、LLaVA-OneVision、Mantis。F — [2508.13744](https://arxiv.org/abs/2508.13744) Table 1
- **根因主张**：图像被当作特殊文本 token，图像间的因果（单向）注意力使靠前的图看不到全局、靠后的图能与前面的交互，等于给图片强加了语义顺序（SoFA）。位于解码器的图间注意力掩码。FOCUS 把串扰归到语言模型没有显式机制隔离不同图的视觉内容。
- **根因的跨模型证据**：位置偏置——**因果（弱）**：把图间因果注意力与双向注意力线性插值后，位置偏置下降、准确率平均 +2~3%（Idefics2 MIRB 46.58→48.83；InternVL2 BLINK 38.95→43.26；Mantis、LLaVA-NeXT 也涨）。F。串扰——**相关**且不一致：Qwen3-VL-8B 多图输入使隐藏状态相似度 0.340→0.366，但 Qwen2.5-VL-7B 上单图与多图差别极小（0.336 对 0.335）。F — [2508.13744](https://arxiv.org/abs/2508.13744) 附录
- **说法是否一致**：SoFA 说根在图间因果注意力；SoFA 同时写"LVLMs may inherit the notorious position bias from their language component"（继承 LLM 的位置偏置）；FOCUS 说 SoFA"targets position bias rather than cross-image information leakage"，两者是不同失败。闭源模型的"中间弱"无法做内部验证。
- **竞争者**
  - **SoFA**：无训练，改图间注意力。代码 github.com/xytian1008/sofa。F
  - **FOCUS**：每次只留一张干净图、其余换噪声，聚合 logits 再用全噪声参考去偏。Winoground Image/Group 最多 +18.8/+16.8，VisMin +44.37/+41.9，Mantis-Eval +5.5，MuirBench +3.2，MIRB +1.7。作者局限："FOCUS requires N+1 forward passes for N input images"；超参逐模型逐基准用验证集选，"their generalization to unseen settings without validation data has not been verified"。代码 github.com/yejipark-m/FOCUS。F
  - PulseFocus（arXiv 2603.04676，逐图注意力门控）：只有检索片段，正文 404。S
- **剩余空间**：MuirBench 上 FOCUS 平均只 +0.4（InternVL3 族）到 +2.14（LLaVA-OV 族）；串扰的内部表征证据在两个 Qwen 版本间不一致。
- **便宜办法**：FOCUS 报告把图片顺序显式写进文本也不行——"Even when the image order is explicitly provided, the model still fails to generate accurate answers"；把单图对比解码直接搬到多图"not only fails to mitigate information leakage but also further distracts the model's output"。F
- **数据与基准**：PQA（SoFA 构造）、BLINK、MIRB、Mantis-Eval、MuirBench、Winoground、VisMin，公开。

---

## 未达主表门槛（单一模型族或行为层证据不足）

### S1 长链推理中的视觉遗忘（reasoning / CoT 模型）
- **现象**：推理链越长，感知类题目越容易错；注意力与 visual dependency 随生成下降。
- **为什么没进主表**：行为层证据全部在 Qwen 系骨干上。More Thinking, Less Seeing 自列："our evaluation is limited to models built on the Qwen2.5-VL backbone, which may constrain the generalizability of our findings"；TVC 的分析用 QVQ-72B-Preview；VAPO 分析的 R1-OneVision / VLAA-Thinker / Vision-R1 与 Reflection-V 的 OpenVLThinker 都是 Qwen2.5-VL 衍生；LASER 只在 Qwen2.5-VL-7B。F — [2505.21523](https://arxiv.org/abs/2505.21523)；[2503.13360](https://arxiv.org/abs/2503.13360)；[2509.25848](https://arxiv.org/abs/2509.25848)；[2509.12132](https://arxiv.org/abs/2509.12132)；[2607.01707](https://arxiv.org/abs/2607.01707)
- **唯一的跨族内部证据**：SPD-Faith Bench 附录在 Qwen2.5-VL 与 LLaVA-1.5-7B 上画了逐层注意力，称"Suppression-then-Decay"模式都在，并推到"a structural bottleneck inherent to current Transformer-based MLLMs"；这是两模型的注意力图（相关），不是行为层复测。F — [2602.07833](https://arxiv.org/abs/2602.07833) 附录 D
- **因果证据（均为 Qwen 系）**：TVC 在推理中途移除图像只掉约 2%，早期移除掉约 20%；Reflection-V 测到约 300 token 后视觉注意力降到初始的 20–30%，且"RL … fails to equip them with visual reflection capability"；VAPO 的 visual replay 与 focus prompt 都能部分缓解；LASER 在早期阶段做一次性全遮蔽使准确率 62.8%→48.9%，同样干预放在后期只降 2.0%。F
- **已有修法**：TVC（训练，五个数学基准平均较前 SOTA +3.4%；局限："simply increasing visual revisits proves insufficient"，不适合实时场景）；Reflection-V（SFT+GRPO，注意力奖励，github.com/jian0805/ReflectionV）；Qwen-LA（RL + 视觉 token 复制/路由，增加推理开销，github.com/Liar406/Look_Again；并声称"text-only reflection … is insufficient"）；VAPO；LASER（MathVision 上 44.6 对 VAPO-Thinker-7B 31.9、Reflection-V-7B 33.9）；SAGE（无训练，SPD-Faith）。
- **竞争解释**：LASER 认为主因不是后期衰减而是早期衰减破坏取证 + 汇聚 token；Qwen-LA 的形式化证明假设"one important cause of VLM hallucination is the neglect of visual information"，作者自认"it may limit the scope of the proof"；More Thinking 指出推理长度与幻觉的关系非单调，且训练数据类型比量更重要。

### S2 RoPE 长程衰减造成的图像 token 位置偏置
- CCA：只在 LLaVA（CLIP + Vicuna）上重训验证（"our approach is validated on LLaVA"）。F — [2410.15926](https://arxiv.org/abs/2410.15926)
- Feather the Throttle：只在一个自训 VLM（SigLIP + Llama 2 7B）。F — [2412.13180](https://arxiv.org/abs/2412.13180)
- TokenPenalty（LLaVA-1.5、Qwen2-VL、Qwen2.5-VL 有评测）与 VisFlow 提到 RoPE，但我没核到它们对 RoPE 根因的跨模型内部测量。A
- 结论：多篇论文引用同一解释，独立的跨族内部证据未核实到。

### S3 实体知识题：图像实体比文本实体差，因为图像信息流发生得太晚
- 行为差距在多个模型上测到（最多 18%），但探针/信息流实验只在 LLaVA 式模型（"we focused on the performance of LLaVA style models"；"leaves the solutions as future works"）。F — [2412.14133](https://arxiv.org/abs/2412.14133)

---

## KQ1 哪些论文在多个模型族上测到"深层几乎不看图像 token"或"图像注意力随生成变长而下降"？归因了哪些失败？因果证据做了几个族？

### Takeaway
"深层少看图"在 LLaVA 系、Qwen-VL、InternVL2、Qwen2.5-VL 上都有注意力敲除级别的证据，但它被同时用来论证"可以剪"和"造成幻觉"；"随长度衰减"在 LLaVA、InstructBLIP、Qwen2-VL、InternVL 上有相关证据，因果只到"补回去后幻觉降"这一级。长推理丢视觉依据的行为证据全在 Qwen 系。

### Cited Findings
- 见 C5（层向）、C3（长度向）、S1（长推理）、C9（多图）各条，出处同上。
- 层向的敲除/剪除干预：LLaVA 系 4 个模型（[2411.18620](https://arxiv.org/abs/2411.18620)）、InternVL2 + LLaVA-1.5（[2411.17491](https://arxiv.org/abs/2411.17491)）、LLaVA-1.5 + Qwen2.5-VL（[2512.07580](https://arxiv.org/abs/2512.07580)）、LLaVA-1.5 + Qwen-VL-Chat + LLaVA-NeXT（[2511.05923](https://arxiv.org/abs/2511.05923)）。F
- 长度向的重加权干预：LLaVA-1.5 / NeXT / Qwen2-VL（[2502.01419](https://arxiv.org/abs/2502.01419)）、LLaVA-1.5 / Qwen2-VL / InternVL（[2504.04099](https://arxiv.org/abs/2504.04099)）、LLaVA / Qwen2-VL / Qwen3-VL / InternVL3（[2605.20965](https://arxiv.org/abs/2605.20965)）。F

### Inferences
- 层向与长度向是两条独立的轴（"在哪层"与"第几个 token"），多数论文各测一条；把两者合成"注意力衰减"一个说法是不成立的互推。【推导】
- "补回图像注意力后幻觉降"不能区分"衰减是根因"与"更强的图像条件普遍压低语言先验"。【推导：M3ID、PAI 的修法本身就是放大图像条件对无条件分布的差】

### Gaps
- 未找到把"生成长度"与"累积文本内容"分开的受控实验（例如固定前文内容只改位置）。
- 未找到在 Gemma / PaliGemma / Idefics / Phi-vision 上对长度衰减的测量。

## KQ2 视觉汇聚 token 与文本侧汇聚 token 各被证明造成什么失败？跨哪些模型？

### Takeaway
视觉汇聚：存在性与"无信息"在 LLaVA、InstructBLIP、Qwen2-VL、InternVL2、VILA 上有证据，但"是否该抑制"有五种互相冲突的说法。文本侧汇聚：OPERA 的柱状模式只在 4 个 Vicuna 系模型上，且 TAME 称惩罚 summary token 并非必要。

### Cited Findings
- 见 C1、C2。
- 汇聚不该一律抑制的四条证据：AvisC 计数掉分（[2405.17820](https://arxiv.org/abs/2405.17820)）；HAVAE 惩罚 Inert Token 有害（[2605.10622](https://arxiv.org/abs/2605.10622)）；ViT 汇聚携带全局信息（[2510.08510](https://arxiv.org/abs/2510.08510)）；EVAS 高密度图像汇聚头有益（[EVAS](https://aclanthology.org/2025.emnlp-main.174.pdf)）。F

### Inferences
- 几篇论文里的"sink"不是同一批 token：Kang 用隐藏维度 massive activation 定义，Luo 用 ViT 特征范数，HAVAE 用 logit-lens 解码词，AvisC 用注意力均值 + 标准差。结论互相冲突可能只是定义不同。【推测：未见任何一篇在同一模型上对这四种定义求交集】

### Gaps
- 未找到在同一模型上对比多种汇聚定义重合度的工作（查了 3 条与 sink 相关的查询）。
- 文本侧 summary-token 模式在 Qwen / InternVL / Gemma 上是否存在：未找到。

## KQ3 "信息在隐藏状态里但没用上"的证据：logit lens、探针、激活修补各显示了什么？位置是否跨模型相似？

### Takeaway
三种读数都有跨族结果，其中激活修补（10 个 VLM）给出了因果级证据：换掉图像位置的整段表示才翻转输出，末 token 修补无效。位置的"相对深度相似"只有粗粒度说法（中层），没有逐头对齐。

### Cited Findings
- 见 C6。
- 位置：FCCT 称末 token 的中层 MHSA 聚合跨模态信息（[2511.05923](https://arxiv.org/abs/2511.05923)）；Kaduri 称中层约 25%–50% 的层承担跨模态流（[2411.17491](https://arxiv.org/abs/2411.17491)）；Yang 称幻觉头在中深层（[Yang et al.](https://proceedings.iclr.cc/paper_files/paper/2025/file/8001c3568152d134d821cd46d4d84768-Paper-Conference.pdf)）；QK Steering 在三个模型上都选中层（[2606.20419](https://arxiv.org/abs/2606.20419)）；Liu et al. 每个模型取 AUROC 最高的 10% 层做 visual-grounding layers，需要逐模型剖面（[2510.17771](https://arxiv.org/abs/2510.17771)）；2604.09364 给出每个模型的 MAC 交叉层（如 DeepSeek-Janus 30 层中 L10.8、LLaVA-NeXT 32 层中 L12.7）（[2604.09364](https://arxiv.org/abs/2604.09364)）。F
- Visuals Lie：PaliGemma"integrates visual signals earlier and has a shallower decoder, leaving less late-layer separation"——相对深度并不一致的一个例子（[2606.17389](https://arxiv.org/abs/2606.17389)）。F

### Inferences
- "中层"在各论文里是各自定义的层段，没有统一的相对深度刻度；说"不同模型处于相似相对深度"目前只能到"都不在最浅和最深"这个粗度。【推导】
- 修补结果说明裁决所依赖的信息分布在大量图像位置上，而不是集中到末 token——这与 LLM 事实回忆的标准图景不同，Neo et al. 的"mirroring the process in text-only language models"说法与之有张力。【推导；两篇任务不同（物体识别对反事实属性），不能直接算矛盾】

### Gaps
- 未找到在自然图像（非合成反事实）上的全序列修补复测。
- 未找到逐头级别的跨模型对齐（哪些头在不同模型里功能对应）。

## KQ4 已有修法各自在哪些模型上、涨多少、开销、副作用、自认局限

### Takeaway
推理时重加权与对比解码最多、也最常被后来者测到副作用（开销 2–8×、长描述 recall 下降）；头级干预开销近零但要逐模型找头；静态权重编辑有两条（MLP 零空间投影、QK 奇异模），幅度小；微调/RL 主要出现在长推理一线。

### Cited Findings
- 逐法细节见各候选「竞争者」。
- 开销对照（LLaVA-1.5-7b，TTFT / TPOT 倍数）：VCD 1.6× / 2.7×，OPERA 1.1× / 1.9×，PAI 1.6× / 2.6×，IRI 1.0× / 1.0×（[2511.05923](https://arxiv.org/abs/2511.05923) Table 7）；TARAC 报 OPERA 7.79×、VCD 2.21×、AGLA 2.27×（[2504.04099](https://arxiv.org/abs/2504.04099)）；IKOD 报 s/item：greedy 0.115、OPERA 3.015、VCD 0.211、HALC 3.205、AGLA 1.589、IKOD 0.205（[2508.03469](https://arxiv.org/abs/2508.03469) Table）。F
- 别的任务上的损伤：OPERA 与 VCD 在长描述 CLAIR 上下降（[2502.01419](https://arxiv.org/abs/2502.01419)）；AvisC 计数下降（[2405.17820](https://arxiv.org/abs/2405.17820)）；VAR 全头应用归零（[2503.03321](https://arxiv.org/abs/2503.03321) Table 4）；VHR 强化过多层降质（[2412.13949](https://arxiv.org/abs/2412.13949)）；VISTA 在 HAVAE 表中 F1 76.4→67.3（[2605.10622](https://arxiv.org/abs/2605.10622) Table 1）；2604.09364 的 SAE 转向在部分配置变差（[2604.09364](https://arxiv.org/abs/2604.09364)）。F

### Inferences
- 不同论文对同一基线（如 LLaVA-1.5-7B greedy 的 CHAIR_S）报的数从 20.6 到 53.0 不等（OPERA 20.6、Kang 45.0、PAI 46.6、ILVAD 48.6、HAVAE 48.2、Devils 53.0），取决于 max token、采样图与提示；跨论文直接比涨幅不可靠。【推导：数字均来自上面各 F 级表】

### Gaps
- "DARE editing"作为 VLM 幻觉修法：1 条查询未找到对应论文，未核实其存在。
- HIME（arXiv 2602.18711，MLP 层自适应权重编辑）、VTI、VCD、HALC、AGLA、AttnReal、D-Attn、LLaViT、Look-Back、CausalMM 只在别人的表或检索片段里见到，未取正文。S

## KQ5 有没有论文反驳"注意力下降就是失败"？竞争解释清单

### Takeaway
有，而且不止一条。按反驳的对象分为六类。

### Cited Findings
1. **量不区分真假**：真实物体与幻觉物体在中后层拿到同样强的图像注意力，"the key issue may not be how much the model attends, but what it attends to and why"（LLaVA-1.5-7B 上的分析）。F — [2608.07302](https://arxiv.org/abs/2608.07302)
2. **抬图像注意力无效或有害**："increasing attention on image tokens has no effect"（Yang）；"simply increasing attention to image tokens fails to improve spatial reasoning"（AdaptVis）；"increasing the influence of all visual tokens reduces recall"（SPARC）；惩罚 Inert Token 有害（HAVAE）。F — [Yang et al.](https://proceedings.iclr.cc/paper_files/paper/2025/file/8001c3568152d134d821cd46d4d84768-Paper-Conference.pdf)；[2503.01773](https://arxiv.org/abs/2503.01773)；[2502.01419](https://arxiv.org/abs/2502.01419)；[2605.10622](https://arxiv.org/abs/2605.10622)
3. **深层少看图是正常信息流**：图像信息在浅—中层已搬进文本位置，深层删图像 token 不掉分（Zhang et al.、FastV、Kaduri、Information Horizon、ShortV、HiMAP）。F/A — [2411.18620](https://arxiv.org/abs/2411.18620)；[2403.06764](https://arxiv.org/abs/2403.06764)；[2411.17491](https://arxiv.org/abs/2411.17491)；[2512.07580](https://arxiv.org/abs/2512.07580)；[2504.00502](https://arxiv.org/abs/2504.00502)；[2503.13108](https://arxiv.org/abs/2503.13108)
4. **深层稀疏注意力恰恰是有用的**：深层"sparsely but reliably attend to localized evidence regions"，答错时也如此。F — [2510.17771](https://arxiv.org/abs/2510.17771)
5. **注意力结构不预测对错**：注意力指标近随机（52–55%），隐藏状态探针强得多；但遮掉高注意 patch 会掉分（因果上必要、诊断上无用）。F — [2606.17389](https://arxiv.org/abs/2606.17389)
6. **汇聚 token 有功能**：见 KQ2。
7. **低图像注意力不专属于幻觉**：重复出现的正确 token 也在低注意区（TARAC 附录）。F — [2504.04099](https://arxiv.org/abs/2504.04099)
8. **基准本身不要求看图**：早剪枝不掉分是因为基准"require minimal visual grounding"（Feather）；去掉大量图像 token 在幻觉基准上只略降（Seeing without Looking）。F/A — [2412.13180](https://arxiv.org/abs/2412.13180)；[2605.22903](https://arxiv.org/abs/2605.22903)
9. **编码器侧解释**：DAMRO 把异常注意力归到视觉编码器；AdaptVis 与 OPERA 都把一部分失败让给编码器感知不足。F — [2410.04514](https://arxiv.org/abs/2410.04514)；[2503.01773](https://arxiv.org/abs/2503.01773)；[2311.17911](https://arxiv.org/abs/2311.17911)

### Inferences
- 第 1、2、5 条合起来，对"注意力量"作为根因是事实约束级的坏消息；对"注意力落点 / 后续裁决"作为根因不构成反驳。【推导】
- 第 3 条与第 4 条并不矛盾：前者说的是总量与可剪性，后者说的是残余注意力的指向。【推导】

### Gaps
- OpenReview 审稿讨论没有查（0 条查询），审稿人对这些因果主张的质疑未收集。
- Same Attention, Different Truths 的"同样强"结论我只核到 LLaVA-1.5-7B 上的分析；它在 Shikra、Qwen2-VL 上是否也测了注意力对比，未核实。

---

## 检索日志

**查询条数：17 条 WebSearch。** 清单：
1. visual attention sink large multimodal models arXiv
2. visual forgetting long generation attention to image tokens decays hallucination LVLM 2025
3. "More Thinking, Less Seeing" multimodal reasoning models hallucination attention arXiv
4. cross-modal information flow multimodal LLM image tokens early layers causal tracing attention knockout models
5. VLM hidden states encode visual information but answer wrong probing "seeing but not believing" attention
6. hallucination heads LVLM attention heads intervention text reliance modular attribution
7. decline of image attention in deep layers is not failure VLM visual tokens redundancy rethinking attention-based hallucination explanation
8. "To Sink or Not to Sink" visual information pathways vision-language models
9. "Understanding and Mitigating Hallucination in Large Vision-Language Models via Modular Attribution and Intervention" arXiv
10. Nullu HalluSpace LVLM weight editing hallucination; DARE editing vision-language hallucination
11. multi-image VLM position bias attention cross-image information leakage mechanism decoder attention
12. EVAS attention sink shallow layers dense deep layers sparse hallucination LVLM
13. reasoning VLM visual attention decays during long chain-of-thought re-attention "look again" OR "look-back" OR "visual re-focusing" 2025 2026
14. attention to image tokens does not predict hallucination critique causal analysis LVLM attention intervention fails negative result（对抗式）
15. VLM probing hidden states linearly decodable visual information not used in answer "knows but" counting OR spatial 2025 2026 arXiv mechanistic
16. "Intervening Anchor Token" TAME decoding hallucination MLLM eigenspectrum
17. static weight editing attention heads LVLM hallucination without inference overhead cross-model 2026 "visual attention" fine-tuning attention loss

**取到正文的论文：71 篇**（arXiv HTML 或会议 PDF 转文本，存于 /tmp/vl03/papers）。

其中 **F（核对了具体章节/表）55 篇**：2503.03321、2311.17911、2510.08510、2605.18359、2607.01707、2405.17820、2403.06764、2411.18620、2410.07149、2411.17491、2411.16724、2407.21771、2412.13180、2602.15580、2511.05923、2512.07580、2505.21472、2504.04099、2508.03469、2605.20965、2403.14003、2502.01419、2410.15926、2503.13360、2505.21523、2502.03628、2310.00754、2510.17771、2502.17422、2410.02762、2506.08008、2505.16411、2511.17254、2605.10622、2412.13949、2412.13817、2503.01773、2508.13744、2503.13792、2605.22903、2410.04514、2608.07302、2509.12132、2505.23558、2509.25848、2602.07833、2511.11502、2604.09364、2606.20419、2412.14133、2606.17389、Yang et al. ICLR 2025（proceedings PDF）、TAME ICLR 2025（proceedings PDF）、EVAS EMNLP 2025（2025.emnlp-main.174）、TokenPenalty Findings of ACL 2026（2026.findings-acl.628）。说明：其中 2410.02762、2412.13949、2412.13817、2505.16411、2605.22903、EVAS、TokenPenalty、TAME 只核了摘要 + 局限 + 一张表或一处正文，深度低于其余。

**A（正文取到但只读了摘要与局限段）16 篇**：2406.04236、2502.11501、2503.13108、2504.00502、2410.03577、2405.18415、2506.12609、2412.18108、2503.06287、2502.16842、2502.00717、2501.12206、2506.17664、2505.16652、RIVS（IJCAI 2026 proceedings 0094）、Testa et al.（2026.findings-emnlp.1887）。

**只有检索片段（S），未取正文**：PulseFocus（arXiv 2603.04676，HTML 与 PDF 均 404）、FG-TRACER（WACV 2026，机构库 403）、2508.18297、2606.13870、HIME 2602.18711、Attention Hijackers 2503.08216、Look-Back 2507.03019、AttnReal、D-Attn、LLaViT、CausalMM、VTI、VCD、HALC、AGLA、DOPRA。

**命名不一致**：2026.findings-acl.628 的 PDF 标题是 TokenPenalty，摘要正文里称方法为 TokenTruth；本文按标题记。

**没覆盖到的范围**
- OpenReview 审稿讨论：未查。
- GitHub 仓库：只记录了正文里出现的 URL，没有逐个打开核对代码是否可用。
- 在审稿件与未公开并行工作：不可见。
- 非 arXiv / 非 ACL Anthology / 非 ICLR-IJCAI proceedings 的来源（如 CVPR 2026 open access 补充材料）：未取。
- 非英文文献：未查。
- 闭源模型（GPT / Gemini / Claude）：只有行为层结果（SoFA、SPD-Faith），内部机制无法验证。
- 七步查重没有跑：本文件是候选盘点，不是新颖性查重；引用链挖掘（系统扫邻居的参考文献与被引）没有做，对抗式检索只有第 14 条一条查询。
- 知识截止：检索到 2026-08 的 arXiv 号（2608.07302）；2026-09 至 11 月的新稿覆盖取决于搜索引擎索引，未单独核。
