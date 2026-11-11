# 11 七步查重：A1「看见了没用上」

历史原件；不是本次提出的假设、论证或运行要求。

原路径：`docs/literature/vl-cross-model-root-cause-candidates-2026-11-06/11_audit_A1_seen_not_used.md`。来源：[固定提交原件](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/literature/vl-cross-model-root-cause-candidates-2026-11-06/11_audit_A1_seen_not_used.md)；SHA-256：`e6d0bab4ef8f79b9a1c4cd2c3f39c6edb2f75d77dfcc1bb815af1c974decc33f`。精确字节见原文归档。

---

# 11 七步查重：A1「看见了没用上」

日期：2026-11-06。检索截至 2026-11。口径：`00_BRIEF`、`00_AUDIT_BRIEF`、`07_SCREENING`。七步顺序 6 → 5 → 1 → 2 → 3 → 4 → 7。本文件不给等级、分数或「值不值得做」。

阅读层级：F = 取到正文并核对了对应章节或表；A = 只核了摘要（含取到正文但只看了摘要与个别句子的）；S = 只有检索片段或标题。本轮关键数字与逐字引文全部来自 F，并用脚本在下载的正文里做了空白归一后的子串核对（51 条全部命中）。

**最不利的先说（细节见第 4 节）：**

1. 「探针读得出 = 模型有这个信息可用」已被一篇 14 模型的工作直接反驳：最可读的那条轴（94%）换成灰图后行为不变，是语言先验；沿探针方向的免训练「恢复」在灰图下收益几乎一样（+19 对 +21）。A1 的现象定义若只靠探针，站不住。
2. 这个题目上的工作在 2026 年 4–11 月密集出现：本轮表里 32 个竞争者，其中 2026-06 及之后出现的 15 个；另有至少 3 篇 ICLR 2027 在审稿件标题就是这件事。
3. 「结论那句话」已有人逐字写出（结论层被占，见第 4 节 E1）：*"visual utilization as the dominant bottleneck"*、*"The models already see; the challenge is making them act on what they see."*
4. 已有的内部修复，沿探针方向或在「裁决层」做的，多数补回量小或不稳（#1：+0.3 至 +3.8 pp；#2：一个模型上 logit 变 +0.403 而准确率变 0；#4：单一探针方向修正 +0）。例外是 #11，沿真值探针方向转向约 +19 pp，但只有一个模型、合成计数图、无随机方向对照。
5. 第一轮当作 A1 主要因果证据的「全序列修补翻转 60–84%」，读透后只是破坏方向（把答对的改成答先验），不是定位，也没有救回任何一个答错样本；录用决定原文写的是 *"only modest causal support"*。

---

## 1. 候选定义

- **现象**：VLM 答错时，所需视觉证据已在内部（注意力落在正确区域，或隐藏状态里可读出），但最终答案没用上。
- **根因主张**：问题出在语言解码器内，从视觉证据到答案的利用/读出通路。
- **预期结论（用于第 3 步蕴含检索，推测档）**：
  - S1：「跨 ≥N 个模型族，答错样本里正确的视觉证据可从语言解码器隐藏状态读出；失败由解码器内一条共有的读出通路造成，而不是感知。」
  - S2：「对该通路做（免训练的）干预，可把相当比例的答错样本翻回正确，且优于随机部件/随机方向对照，换问法、换选项顺序、留出数据后仍成立。」
  - S3：「该通路解释了多类任务（属性、计数、空间）上的同一种失败。」

---

## 2. 竞争者全景表

共 32 行。前 15 行为 F（本轮读正文），其余为 A 或 S。「对照」一栏只写随机部件/随机方向/打乱标签一类；「未命中」指在正文 References 之前用关键词 `random direction|random vector|random head|shuffled label|norm-matched|same-norm|random control` grep 无结果，不等于作者没做任何对照。

### 2.1 F 级（15 个）

| # | 工作 | 类型 | 模型族 | 干预类型 | 对照 | 评测稳健性 | 效果数字 | 自认局限（逐字） | 代码 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Arbitration Failure, Not Perceptual Blindness，[2604.09364](https://arxiv.org/abs/2604.09364)，2026，COLM 2026（[OpenReview](https://openreview.net/forum?id=o3pc99Q3Mi)） | 定位 + 修复 | 10 个：LLaVA-v1.5/NeXT/OneVision、Qwen2-VL、InternVL2、BLIP-2、Janus-Pro，加 13B/26B/72B | 推理时：单层全序列残差替换（破坏方向）；早层线性/SAE 转向 | 未命中。修补无「换成无关图」对照；转向无随机方向对照 | 8 种问法只用于分析（3 个主模型各 100 例，胜出一致 93.9%）；转向收益未在换问法下复测；合成反事实图；修补每模型 100 例 | 探针 AUC > 0.86（10% 深度），成败两组置信度差 < 0.03；全序列修补 60–84% 由视觉答案翻到先验，末 token 0–1%，**反向翻转 0/900**；转向 +1.4 至 +3.8 pp（293 例），在裁决层 ≤ +0.3 | *"Our analysis relies on synthetic counterfactual images"*；*"probes trained on specific attribute labels would provide an even more targeted test of whether the visual attribute itself, rather than correlated features, is encoded"*；*"The steering experiments (Section 7) are limited to the 7–8B primary models"* | 正文无 URL |
| 2 | Knowing Isn't Always Saying，[2608.22916](https://arxiv.org/abs/2608.22916)，2026，EMNLP 2026（OpenReview 记录） | 定位 | 10 个 / 5 族：Qwen2.5-VL 7B/32B、LLaVA-OV、InternVL2.5/3、Gemma-3 4B/12B/27B、Janus-Pro | 推理时：沿类条件方向在指定层 × token 位置加向量（direction patching）；一例头敲除 | **有**：同范数随机方向基线（指标即「干预 − 随机」）；错轴与非物体位置对照（[−0.018,+0.031]）；五折交叉拟合 | 7 种提示格式、3 个数据集（含 RefCOCO）、两种属性（空间、颜色）；四选一 | 只在 12–32 层起效（如 Janus L12 +0.325）；文本 CoT 在多数模型上关掉 object-word 位置的通路，visual CoT 10/10 模型打开；生成模式下朝**错误**象限转向，9/10 模型掉 8–21 pp；Janus logit +0.403 而准确率 0 pp | *"direction patching is silent on transport that may occur through non-linear pathways or through alternative directions outside this subspace"*；*"Free-form spatial descriptions, fine-grained localization, and other attribute types (size, shape, material) remain untested."*；*"Our head-level localization is proof-of-concept, not a complete circuit."* | 正文无 URL |
| 3 | Encoded but Unused，[2610.29241](https://arxiv.org/abs/2610.29241)，2026-10，预印本 | 测量 | 2 个：LLaVA-1.6-7B、Qwen2.5-VL-7B | 无内部干预；对输入加噪/背景模糊来构造上下界 | 未命中；用输入变换给探针不完美定界 | 自然图像（VAW，6000+ 图），颜色/材质/形状；留一属性值泛化 | 探针 ROC-AUC 0.95 / 0.91；**答错样本中「利用失败」占 84.4% / 70.0%，保守下界 77.5% / 61.0%** | 自述先做三类可从物体本身判定的属性（§E 讨论范围，未细读）；*"all code … will be made publicly available"* | 未放出 |
| 4 | Decodable Is Not Grounded，[2606.31257](https://arxiv.org/abs/2606.31257)，2026-06，预印本（ICLR 2027 投稿版为 Desk Rejected，OpenReview 记录） | 反驳 + 定位 + 修复 | 行为与探针 14 个 / 6 个 LM 族（Qwen2/2.5/3、Mistral、SmolLM、Gemma，2B–27B）；修正 8 个 | 推理时：decision token 转向、top-k 神经元投影、旋转；训练：低秩编辑（LoRA/ReFT）；共 9 种修正 | **有**：打乱标签的探针下限；带外（L2–6）投影对照；**五种去图对照**（灰、黑、噪声、打乱 patch、同轴但不匹配的真实图）；旋转对 LoRA 三个种子 | 换措辞（front/back → closer/farther 仍低于随机）；二选一正极字母逐题随机；两个外部基准（What'sUp、3DSRBench） | 探针：竖直 94%（行为 59%）、深度 77%（行为 31%）；投影把竖直 59→79，但灰图下同样 +19；Qwen3-VL-8B 上免训练旋转把深度 21→77（+49±8，对 LoRA +55±2）；别的模型只 +14、+8，或只能训练 | *"We note that γ is currently swept on the evaluation set; a held-out γ selection is the correct protocol"*；*"our causal evidence is representation-level, as a clean pixel-level minimal pair for camera-relative front/back is unattainable"*；*"tracing it to training data is future work"* | 正文无 URL |
| 5 | Diagnosing Visual Ignorance，[2606.06890](https://arxiv.org/abs/2606.06890)，2026，预印本 | 定位 + 测量 | 3 个：Qwen2.5-VL-3B/7B、LLaVA-v1.6-Mistral-7B | 推理时：逐层替换末提示 token 残差（图不同、题相同）；另有逐层换入微调后权重 | 未命中 | 两种问法（Q1/Q2）；机制部分只在 VLMBias 计数（197 对）；模糊评测 12 个基准 | 末 token 残差替换在中层几乎无效，21–23 层起效，27 层注意力一步 +0.160；最强模糊下答案连续不变 32.2% / 28.7% / 48.1% | *"causal residual interchange and module-level localization were evaluated in Qwen-3B"* | 正文无 URL |
| 6 | The Visual Insensitivity Gap，[2609.00868](https://arxiv.org/abs/2609.00868)，2026-09，预印本（单作者；OpenReview 未检到） | 测量 | 6 个 / 3 族：LLaVA-1.5、LLaVA-NeXT、Idefics3、Qwen3-VL、Qwen2.5-VL 7B/32B | 输入级：对问题相关区域做高斯模糊 | 高 VSI 样本作配对对照；置换检验 | POPE、MMVP、HallusionBench、MMStar；σ ∈ {10,20,40} | 40%–97% 样本对区域模糊不敏感；本塔探针分辨「有无扰动」0.72–0.79，而 argmax 只变 2%–11%，差 0.66–0.71（n=83） | *"we intervene at the input, so the disconnect is causal at the input–output level but does not pinpoint a structural locus within the language head"*；*"Probe accuracies are linear-decodability lower bounds on the encoders' information content."* | 称随代码发布，URL 未见 |
| 7 | Seeing but Not Believing（VEA），[2510.17771](https://arxiv.org/abs/2510.17771)，ICLR 2026 Poster（[OpenReview](https://openreview.net/forum?id=JAI7afWA9e)，取到 3 份评审，评分 6/6/6） | 定位（相关）+ 修复 | 8 个 / 4 族：LLaVA-NeXT、Qwen2.5-VL、Gemma3、InternVL3.5 | 输入侧：用深层注意力生成遮罩叠到图上再答；不改模型内部 | 无内部干预故不适用；基线含指令提示、两步法 CGR、VAR、AGLA | 4 个偏文字的 VQA 集（InfoVQA、DocVQA、SROIE、TextVQA）；噪声/低分辨率/随机遮挡鲁棒性 | EM +3.6 至 +11.1（平均 +5.67）；指令提示 −0.6 至 +0.8；CGR +2.4 至 +7.0 | *"attention may not always fully capture all the internal mechanisms of evidence localization"*；层位差异 *"remains open for future investigation"*。**LLaVA-NeXT 与 InternVL3.5 的遮罩来自替身模型**：*"we employ Qwen2.5VL-7B as a delegate model for Vea"* | 正文无 URL |
| 8 | Hidden in Plain Sight，[2506.08008](https://arxiv.org/abs/2506.08008)，COLM 2025（OpenReview 记录） | 测量 + 修复（训练） | Prismatic 4 种编码器（DINOv2、IN1k-ViT、CLIP、SigLIP）+ InternVL、Phi-3-V、Qwen-VL | 训练：等参数量 LoRA 分别调 ViT/投影器/LLM（每任务 5000 例）；前缀提示调优 | 分部件等参数量对照；盲答基线 | 6 个 vision-centric 任务（BLINK/CV-Bench/MOCHI 类） | 视觉读出对 VLM：如低层匹配 0.819 对 0.170（第一轮核过 Table 1）；调 LLM 涨得最多 | *"Note that this is a sufficient but not necessary condition; even if vision representations are not amenable to our probing methods, they may still be useful to the LLM through a different algorithm."*；提示调优 *"does not close the gap with standard vision evaluation strategies"* | 正文无仓库 URL |
| 9 | Vision-Default, Prior-Override，[2606.28273](https://arxiv.org/abs/2606.28273)（v2，2026-11-05），EMNLP 2026（Semantic Scholar 记录） | 定位 | 5 个 / 3 族：Qwen-VL 3B/7B、LLaVA-NeXT 7B、PaliGemma 3B/10B | 推理时：**末 token** 上残差/单头/MLP 修补与零消融；对比变量是**提示**（this 对 usually），图固定 | 无随机头对照；用双向不对称 + 五折重分类稳定性（25 次里 19 次完全复现） | Visual CounterFact 颜色 + WHOOPS!；附录 F 改成变图固定提示 | 2.5–4.8% 的头；整组消融翻转 68–96% 的先验作答，视觉作答只变 0.8–7.5%；V2P 达 50% 翻转的层：Qwen-7B L18、LLaVA-NeXT L12、PaliGemma-3B L13 | *"A full 2×2 design crossing prompt type with image type …"* *"We see this as the natural next step for this line of work."*；*"Components contributing earlier in the sequence, for example during the processing of image tokens, are outside the scope of the analysis and their role may be underestimated."* | [github](https://github.com/nlietzow/vision-default-prior-override) |
| 10 | Pixels Versus Priors，[2505.17127](https://arxiv.org/abs/2505.17127)，EMNLP 2025 | 定位 + 修复（转向） | 3 个：LLaVA-NeXT、Qwen2-VL、Janus-Pro | 推理时：在**末 token**、连续若干中后层加转向向量；对比变量是**提示** | 未见随机方向对照（本轮未专门 grep） | 固定两种提示模板 | WK→CF 颜色 ≥ 98%；反向更难 | *"steering models from visual perception back to world knowledge is more difficult than the reverse"* | [github](https://github.com/rsinghlab/pixels_vs_priors) |
| 11 | The Count Is There, but Misaligned，[2607.09544](https://arxiv.org/abs/2607.09544)，2026-07，预印本 | 定位 + 修复 | 4 个 / 2 族：InternVL2-1B/4B、Qwen3-VL-2B/8B | 推理时：沿真值探针方向转向；探针判错后再问一次 | 未命中 | 合成计数图（1–9）；四个自建集 + 一个别的集 | 「真值探针」与「输出探针」共享子空间但读出方向不对齐（SVCCA）；转向约 27%→46%（一个数据集、一个模型）；检测后重问最多 +15.6 pp | *"use synthetic data whose transfer to real-world settings is still unverified, cover only two VLM families, conduct a causal intervention experiment with only one model"* | 正文无 URL |
| 12 | VLMs Need Words，[2604.02486](https://arxiv.org/abs/2604.02486)（v3），COLM 2026（据仓库名）；读得较浅 | 竞争解释 + 修复（训练） | 微调实验 Qwen3VL-2B、Gemma3-4B；评测模型数未核 | 训练：教任意名字；任务微调 | 未核 | 语义对应、合成形状、人脸匹配；留出更难的形状与迷宫 | 可命名实体远好于不可命名；任务微调后近满分并泛化 | *"Prior work has attributed this ''hidden-in-plain-sight'' gap to the language model, but the cause remains unexplained."* | [github](https://github.com/Patchwork53/VLMs-Need-Words-COLM2026) |
| 13 | See, Think, Use，[2611.01467](https://arxiv.org/abs/2611.01467)，2026-11-01，预印本；读得较浅 | 测量（行为协议）+ 修复（提示） | 2 族：Qwen3-VL-8B、InternVL3.5-8B | 无内部干预；让模型先框出实例 | 随机分配算力对照 | 6 个数据集，含 VLMBias、Visual CounterFact、BEAF、DynaMath | 结论句：*"Answers follow the model's perception except on images that contradict a common prior, and asking the model to localize first repairs this failure when its boxes are right."* | 未摘 | 称将放出 |
| 14 | Senses Wide Shut，[2605.13737](https://arxiv.org/abs/2605.13737)（v2），预印本；读得较浅 | 测量 + 修复 | 8 个开源全模态模型 + Gemini 3.1 Pro | 推理时：探针引导的输出 logit 调整（PGLA，需带标签训练探针） | 未命中（附录有 probe specificity 一节，未读） | 500 段电影片段，2×2；6 选 1，固定顺序 + K=3 次打乱；7 种提示变体 | 平衡准确率平均 +15.0 pp（不限标准题损失），限 3 pp 时 +9.9 | *"Hidden states carry a decodable mismatch signal, reliably for vision and more weakly for audio, but this signal does not reach the output."* | [github](https://github.com/ngquangtrung57/imavb) |
| 15 | Same Task, Different Circuits，[2506.09047](https://arxiv.org/abs/2506.09047)，NeurIPS 2025 poster（OpenReview 记录）；数字沿用第一轮 F，本轮只核了一句引文与仓库 | 定位 + 修复 | 3 族：Qwen2-VL、Pixtral、Gemma-3 | 推理时：back-patching | 有：随机回路、文本对照 | 自建 5 任务 + VQAv2、RealWorldQA | 平均 +4.6%，约补回模态差距的 32% | *"Yet, the causes for the remaining gap remain unclear"* | [github](https://github.com/technion-cs-nlp/vlm-circuits-analysis) |

### 2.2 A 与 S 级（17 个，字段从简）

| # | 工作 | 类型 | 模型 | 做法与数字（来自摘要） | 层级 |
|---|---|---|---|---|---|
| 16 | CALRD，[2606.17953](https://arxiv.org/abs/2606.17953)，据检索片段为 IJCAI-ECAI 2026 | 修复（解码） | 5 个，InstructBLIP 到 Qwen3-VL | 中间层先答对、末段被文本压回；检测到被压就取回中间层分布；冲突基准上最多 +9.4%；*"It recovers what the model already knew but failed to preserve."* | A |
| 17 | DualPD，[2601.07359](https://arxiv.org/abs/2601.07359) | 修复（解码） | LLaVA、Qwen-VL | 「seeing it right but saying it wrong」；层间对比 logit + 压低低贡献头；数字未摘 | A |
| 18 | DeCo，[2410.11779](https://arxiv.org/abs/2410.11779) | 修复（解码） | 未核 | 用前面层修正末层 logit；描述幻觉平均压 10.8% | A |
| 19 | To See or To Please，[2603.18373](https://arxiv.org/abs/2603.18373)（v5） | 测量 | 9 个开源 | 空白图下三层诊断；9000 对里 28.1% 为「察觉到没图仍编答案」 | A |
| 20 | Responses Fall Short of Understanding，[2604.04411](https://arxiv.org/abs/2604.04411) | 测量 + 修复（训练） | 未核 | 文档理解上探针高于回答；只调中间层同时抬高两者并缩小差距 | A |
| 21 | Linear Separability Ceiling，[2507.07574](https://arxiv.org/abs/2507.07574)（v4） | 测量 + 修复（训练） | 未核 | 多数模型生成式成绩不及自己视觉嵌入的线性可分上限；加对比目标后超过；[代码](https://github.com/envomp/Beyond-the-Linear-Separability-Ceiling) | A |
| 22 | RL Teaches VLMs Where to Attend，[2610.23983](https://arxiv.org/abs/2610.23983) | 定位 + 修复 | 未核 | RL 后编码器探针不变、LLM 层探针升；给未训练模型加固定注意力偏置可部分复现增益 | A |
| 23 | Centroid Erasure / TCCD，[2604.14363](https://arxiv.org/abs/2604.14363) | 测量 + 修复（解码） | 7 个 / 4 族 | 图后文本位置被替换的代价是视觉位置的 4 倍；对比解码单任务最多 +16.9%（按任务挑最优 α）；[代码](https://github.com/yahskapar/centroid-erasure) | A |
| 24 | Biased Bayesian Observers，[2610.19407](https://arxiv.org/abs/2610.19407) | 统一解释（行为模型） | 未核 | 两参数线索整合模型预测图文冲突下的偏好；*"reconciling reports of text and vision dominance under a single combination rule"* | A |
| 25 | CARD，[2608.20763](https://arxiv.org/abs/2608.20763) | 定位 | 4 个 | 沿一条轴转向、看另一条轴的预测；信念表征不进入动作预测 | A |
| 26 | MLLMs Know Where to Look（ViCrop），[2502.17422](https://arxiv.org/abs/2502.17422)，ICLR 2025 | 定位（相关）+ 修复（输入） | 第一轮 F | TextVQA LLaVA-1.5 47.80→55.17/56.06 | 第一轮 F |
| 27 | When Seeing Overrides Knowing，[2507.13868](https://arxiv.org/abs/2507.13868) | 定位 + 修复（头） | 第一轮 F，2 族 | 末 token 注意力头乘性干预 | 第一轮 F |
| 28 | Seeing Is Not Enough（ICLR 2027 在审，[OpenReview](https://openreview.net/forum?id=1d4sP1tTgd)） | 基准 + 修复（提示） | 未核 | 区分感知失败与「过程失败」；能列全候选的模型仍有 > 95% 过度下结论，结构化提示降到 < 13% | A |
| 29 | The Umbra Effect（ICLR 2027 在审，[OpenReview](https://openreview.net/forum?id=2m5YSJ6z77)） | 定位 | 5 个 / 2 族 | 反方向的解离：视觉信息因果上影响答案，却难以被注入方向「说出来」；Qwen2.5-VL-3B 在 L23 有视觉位到答案位的交接 | A |
| 30 | Exact Visual Grounding（ICLR 2027 在审，[OpenReview](https://openreview.net/forum?id=9dJ4gjepyC)） | 修复（训练） | Qwen3.5-9B 等 | 合成监督；9 个基准宏平均 60.06→63.90；探针显示中后层更可读 | A |
| 31 | Bigger Is Not Better / VisArb（ICML 2026 Mech Interp Workshop，[页面](https://icml.cc/virtual/2026/79404)） | 定位 + 修复（训练部件） | 6 族 | 越大越依赖先验；先验在早层出现；在视觉骨干与连接器之间插 SAE | S |
| 32 | Seeing Clearly, Answering Incorrectly（MMVU），[2406.10638](https://arxiv.org/abs/2406.10638)，CVPR 2025 | 基准 + 修复 | 15 个 | ICLR 评审指出它早于 #7 提出同一现象；CGR/VAR 即出自此文 | S |

第一轮已记录、本轮未重读的同类工作（不计入 32）：计数错在输出层（2510.19555）、数量线性可分而符号映射塌（2605.30170）、BlindTest 编码器探针 ≥ 99.47%（2407.06581）、朝向编码器 MAE < 3°（2604.13321）、朝向全程读不出（2603.06054）、分类信息在但解不出（2405.18415）、VISTA（2502.03628）、Visuals Lie（2606.17389）、Same Attention Different Truths（2608.07302）。

---

## 3. 各轴最高水位

| 轴 | 目前最好的是谁 | 做到什么 |
|---|---|---|
| 模型族数量与多样性（行为 + 探针） | #4（2606.31257） | 14 个模型、6 个 LM 族、2B–27B，含 3 条族内规模阶梯 |
| 模型族数量（带内部因果干预） | #2（2608.22916）与 #1（2604.09364） | 各 10 个模型；#2 是 5 族且每个都有随机方向基线；#1 到 72B 但无随机对照 |
| 因果对照的严格程度 | #2 与 #4 | #2：同范数随机方向、错轴、错位置、交叉拟合。#4：五种去图对照（含同分布的不匹配真实图）、带外层对照、打乱标签下限、三种子 |
| 「信息在」的测量严格度 | #3（2610.29241）与 #4 | #3 给出考虑探针不完美的上下界（下界 77.5% / 61.0%）；#4 用去图对照区分「视觉来的」与「先验来的」 |
| 评测稳健性 | #4、#14、#2 | #4：换措辞、选项字母逐题随机、两个外部基准。#14：7 种提示变体 + K=3 次选项打乱。#2：7 种提示格式、3 个数据集。**修复收益本身在换问法下复测**：在 15 篇 F 里未见（方法层；正文 grep `paraphras`） |
| 效果量（内部、免训练、由错翻对） | #4 单模型；#14 多模型 | #4：Qwen3-VL-8B 深度题 21%→77%，与 LoRA 打平，但只在这一个模型上成立，其余 +14、+8 或无效。#14：8 个模型平均 +15.0 pp（输出端 logit 调整，要标签）。#11：约 +19 pp（一个模型、合成图） |
| 效果量（解码/输入侧、免训练） | #7、#16、#23 | VEA EM 最多 +11.1（8 模型）；CALRD 最多 +9.4%（5 模型）；TCCD 单任务最多 +16.9%（挑最优超参） |
| 效果量（训练） | #8、#12、#30 | LoRA 调 LLM 涨幅最大（每任务 5000 例）；任务微调近满分；合成监督宏平均 +3.84 |
| 任务与数据广度（测量） | #5、#6、#3 | #5 的模糊评测 12 个基准；#6 四个基准 × 6 模型；#3 自然图像 6000+ |
| 任务与数据广度（内部因果） | 都窄 | 颜色/大小反事实（#1、#9、#10）、空间（#2、#4）、计数（#5、#11）。#2 自述 *"other attribute types (size, shape, material) remain untested"* |
| 是否免训练 | 多数是 | #1、#2、#4（部分）、#7、#11、#14、#16–18、#23 |
| 是否给出统一解释 | 各说各的，至少 8 种 | 见第 4 节 E2。未找到把其中两种以上放在同一批模型、同一批题上判别的工作（结论层；第 6、3 步合计约 14 条查询 + 15 篇 F 的 Related Work） |

---

## 4. 竞争解释与事实约束

### 4.1 事实约束（实测否定或收窄了某条路）

- **F1 可读出 ≠ 用的是图**。Qwen2.5-VL-7B 上竖直轴探针 94%、行为 59%；换灰图后行为 59.6%，免训练投影在灰图下 +19（看图时 +21）。14 个模型里竖直轴探针 87–97%、深度 73–86%，行为却是先验或反号。原文：*"Probing and steering overstate grounded knowledge because they are blind to image-dependence; the arbiter is not."* — [2606.31257](https://arxiv.org/abs/2606.31257) §4.2、§5（F）
- **F2 转向成功 ≠ 恢复了视觉利用**。同文：*"an intervention that moves accuracy can still act on a non-visual prior, so a behavioral success is not grounded recovery without a causal control"*。（F）
- **F3 探针方向不是干预最优方向**。*"the decoding-optimal probe direction is not the intervention-optimal one"*（2606.31257 §4.1，F）；Qwen3-VL-8B 上单一探针方向与 GEVD 子空间修正 +0，而 rank-1 ReFT +58、4 成分 ICA 反射 +60（同文 §6，F）。
- **F4 在「裁决层」干预几乎无效**。InternVL2 在 MAC 层（L26）转向 ≤ +0.3%，在 L3 为 +3.4/+3.8；*"The MAC crossover indicates where the decision is observed, not where it should be changed."* — [2604.09364](https://arxiv.org/abs/2604.09364) §7（F）
- **F5 logit 动了、答案不动**。Janus 在 visual CoT 下 Δargmax +0.403，生成模式准确率变化 0 pp。— [2608.22916](https://arxiv.org/abs/2608.22916) §4.1（F）
- **F6 提示能修掉一部分**。「先框再答」在框对的时候修好先验冲突下的不跟随（[2611.01467](https://arxiv.org/abs/2611.01467)，F 浅）；两步法 CGR 在 8 个模型上 +2.4 至 +7.0 EM（八个模型平均约 +3.6，VEA 为 +5.67）（[2510.17771](https://arxiv.org/abs/2510.17771) Table 1，F）；visual CoT 在 10/10 模型上保持通路打开（2608.22916，F）。反面证据：单句指令 −0.6 至 +0.8（同表）；前缀调优补不上（2506.08008，F）；7 种提示变体都修不动（2605.13737，F 浅）。即「换提示修不了」只对最简单的提示成立。
- **F7 现象范围可能比 A1 的定义窄**。*"Answers follow the model's perception except on images that contradict a common prior"*（2611.01467，2 族 6 数据集，F 浅）。若成立，「看见了没用上」主要落在先验冲突题上，与 A2 重合。
- **F8 机制不是一条**。*"attribute-specific arbitration pathways rather than a single universal mechanism"*（2604.09364 §4，F）；同一模型在相机视角前后题上反号、在近场前后与度量深度上正确（2606.31257 §5.1，F）；最小修正逐模型不同（同文 §6）；Qwen 族内 7B 与 32B 的通路分组不同（2608.22916 §4.1，F）。
- **F9 第一轮的主要因果证据偏弱（推导）**。#1 的全序列修补是在某一层把所有位置的残差换成标准图那次运行的，等于从该层起改跑标准图；方向是把答对的改成答先验，*"Notably, there are zero reverse flips across all 900 patched samples."*；没有用它去救答错的样本；无随机源对照。COLM 录用决定原文：*"The main limitations of this work are the reliance on synthetic data, only modest causal support, and insufficient contextualization with prior work"*（OpenReview，F）。
- **F10 #1 与 #6 的探针标签不是答案属性（推导）**。#6 的探针分的是「图有没有被模糊」；#1 的局限段自己说应改用属性标签（见第 5 节）。探针认得出模糊，不等于模糊去掉了作答所需信息。
- **F11 VEA 的增益不能当作「该模型自己看见了」的证据（推导）**。涨得最多的 LLaVA-NeXT-7B（+11.1）用的是 Qwen2.5-VL-7B 的注意力（见 #7 引文）。ICLR 评审也问了注意力没落对时的情况与文字类之外的场景（OpenReview，F）。

### 4.2 结论层被占的句子（逐字）

- **E1**：*"Overall, our study identifies visual utilization as the dominant bottleneck in VLMs"*（2610.29241 摘要）；*"The models already see; the challenge is making them act on what they see."*（2604.09364 §8）；*"VLMs are not effectively using visual information easily accessible throughout the entire model, and they inherit the language priors present in the LLM"*（2506.08008 摘要）。对应 S1 的前半句。S1 后半（「共有的读出通路」）、S2、S3 本轮未找到逐字对应的句子（结论层；第 3 步 3 条 + 第 6 步 11 条查询 + OpenReview 8 条）。

### 4.3 竞争解释（同一现象的另一个已发表说法）

- **E2-a 裁决失败**：编码一样强，末层 logit 差决定成败（2604.09364，F）。
- **E2-b 条件性传输**：*"reframe the encoding-grounding gap as a problem of conditional transport"*，是否到达答案取决于层、token 位置、提示格式（2608.22916，F）。
- **E2-c 视觉是默认、先验靠少数头覆盖**（2606.28273，F）。与 A1 方向相反：它说默认就是用图。
- **E2-d 末段文本压回**：中间层先答对，后段被压（2606.17953，A；DeCo，A；2606.06890 的「晚段才耦合」，F）。
- **E2-e 先验在早层就形成**，必须在最前面纠正（Bigger Is Not Better，S；2604.09364 的「转向要在裁决形成之前」，F）。E2-d 与 E2-e 对「在哪」的说法相反，未见同协议比较。
- **E2-f 缺语义标签**：能叫出名字的视觉实体才被用上；自称解释了 Hidden in Plain Sight 的差距（2604.02486，F 浅）。
- **E2-g 读出方向错位**：真值探针与输出探针共享子空间、方向不对齐（VLM 计数：2607.09544，F；文本 LLM：KAPPA [2509.23782](https://arxiv.org/abs/2509.23782)，A）。若成立，A1 是文本 LLM 上「knowledge–prediction gap」的多模态特例。
- **E2-h 贝叶斯线索整合**：行为可由各模态证据强度加模态偏置预测，不需要假设某条通路坏了（2610.19407，A）。
- **E2-i 解码≠部署的三种状态**：grounded / prior / inverted，「没用上」只是其中之一，还有「用反了」（2606.31257，F）。
- **E2-j 感知才是瓶颈（别的任务类）**：约 87% 的错误是读错图（[2605.20177](https://arxiv.org/abs/2605.20177)，ICML 2026，S）；ARC 类约 80% 来自感知（ACL 2026，S）；视觉心智理论受限于感知（NeurIPS 2026，S）；朝向全程读不出（2603.06054，第一轮 F）。这些与 A1 不在同一批任务上，是范围边界，不是直接否定。
- **E2-k 训练数据/学到的捷径**：*"Many training distributions may allow a model to predict the answer from the question, coarse scene information, and familiar associations."*（2606.06890 讨论，F）；2405.18415（第一轮 F）。

---

## 5. 作者留下的开口（逐字，均 F）

- 2604.09364：*"Extending to naturally occurring conflicts—unusual real-world colors, ambiguous scenes, fine-grained attributes—is an important direction for future work."*
- 2604.09364：*"probes trained on specific attribute labels would provide an even more targeted test of whether the visual attribute itself, rather than correlated features, is encoded"*
- 2609.00868：*"we intervene at the input, so the disconnect is causal at the input–output level but does not pinpoint a structural locus within the language head"*；*"Two extensions follow naturally: activation patching across the cross-modal projection to localise the failure"*，以及对不敏感子群加权重训。
- 2608.22916：*"direction patching is silent on transport that may occur through non-linear pathways or through alternative directions outside this subspace"*；*"Free-form spatial descriptions, fine-grained localization, and other attribute types (size, shape, material) remain untested."*；*"Our head-level localization is proof-of-concept, not a complete circuit."*
- 2606.28273：*"A full 2×2 design crossing prompt type with image type"* … *"We see this as the natural next step for this line of work."*；*"Components contributing earlier in the sequence, for example during the processing of image tokens, are outside the scope of the analysis and their role may be underestimated."*
- 2606.31257：*"tracing it to training data is future work"*；*"our causal evidence is representation-level, as a clean pixel-level minimal pair for camera-relative front/back is unattainable"*
- 2606.06890：*"causal residual interchange and module-level localization were evaluated in Qwen-3B"*（另两个模型只有相关性）。
- 2607.09544：*"use synthetic data whose transfer to real-world settings is still unverified, cover only two VLM families, conduct a causal intervention experiment with only one model"*
- 2510.17771：*"attention may not always fully capture all the internal mechanisms of evidence localization"*；ICLR 评审提问（OpenReview）：*"Why not apply this method to intermediate features or attention?"*
- 2506.08008：*"Note that this is a sufficient but not necessary condition; even if vision representations are not amenable to our probing methods, they may still be useful to the LLM through a different algorithm."*
- 2506.09047：*"Yet, the causes for the remaining gap remain unclear"*（补回约 32%）。
- 2604.02486：*"Prior work has attributed this ''hidden-in-plain-sight'' gap to the language model, but the cause remains unexplained."*（它随后给了自己的解释，见 E2-f）
- 2505.17127：*"steering models from visual perception back to world knowledge is more difficult than the reverse"* … *"remains an open direction for future work"*（后半句为第一轮所核）。
- 语音同类（[2608.19211](https://arxiv.org/abs/2608.19211)，A）：单层编辑能把答案推向被压住的类，但 *"this recovery is directional rather than a selective restoration of the correct class"*。

---

## 6. 三列表

| 先例支持 | 事实约束与竞争解释 | 谁会因此改做法 |
|---|---|---|
| 现象在 ≥ 6 个模型族、多种读数（注意力、线性探针、MLP 探针、输入扰动）上各自成立：#1、#3、#5、#6、#7、#8、#19 | F1、F2：探针与转向都可能读到/放大先验而不是视觉 | 做「潜在知识」类解释性研究的人：2606.31257 明确主张把「真实图对去图」作为默认对照，改的是报告探针与转向结果这一步 |
| 根因在语言端：分部件微调（#8）、末段注意力一步（#5）、稀疏头（#9）、层 × 位置图（#2） | F8：机制随属性、任务类型、模型而变；E2 的 11 种说法未被判别 | 做评测的人：#6、#5、#19 都主张在准确率之外报告视觉敏感度，改的是基准计分这一步 |
| 内部干预能动答案：#2（10 模型，带随机对照）、#4（8 模型修正）、#11、#14 | F3–F5：探针方向与裁决层的干预多数补回量小或不稳（例外 #11，单模型合成图） | 做模型训练的人：#8 说加编码器不解决问题、该调 LLM；#12、#30 说要任务/合成监督。改的是「换编码器还是调语言端」这一步 |
| 输入侧/解码侧已有可用修法：VEA、ViCrop、CALRD、DeCo、TCCD | F6：提示（先框再答、两步法、visual CoT）已能修掉一部分；F7：范围可能只限先验冲突 | 用内部通路修复来替代上述做法后，哪类部署方会改哪一步：**未找到**明确陈述（本轮 15 篇 F 的讨论段里没有） |
| 相邻模态有同形结果：全模态（#14）、语音（2608.19211、2609.00727、SonicBench）、视频（2602.11244、2605.21954） | E2-g：文本 LLM 已有 knowledge–prediction gap 的几何解释与修法（KAPPA），VLM 结论可能是其推论 | — |

---

## 7. 要构成足够贡献，至少需要做到什么

以「超过第 3 节各轴水位」的形式列，只写门槛。

1. **「信息在」的证明**：要同时过去图对照（至少灰图 + 同分布不匹配真实图，#4）与探针不完美定界（#3）；探针标签须是作答所需的属性本身，并给打乱标签下限。只报探针准确率低于现有水位。
2. **模型覆盖**：内部因果证据要超过 10 个模型 / 5 族且每个都带随机方向或随机部件对照（#2）；行为与探针层面要对得上 14 个模型 / 6 个 LM 族（#4）。
3. **因果方向**：要有「由错翻对」的结果，对象是真实答错的样本；现有同类结果是 #4（一种任务类型、一个模型上干净成立）、#11（一个模型、合成图）、#14（输出端、要标签）。只做破坏方向（#1、#2）不超过水位。
4. **定位粒度**：要比「某层全序列替换」细（#1 的做法被评为 modest），至少到 #2 的层 × token 位置 × 提示格式，或 #9 的头级并补上随机头对照。
5. **数据**：要有自然图像上的内部因果结果；现有内部因果几乎都在合成反事实或四选一空间题上（#1、#11 自列为局限）。测量侧的水位是 6000+ 张自然图（#3）与 12 个基准（#5）。
6. **评测稳健性**：分析与修复都要在换问法（≥ 8 种，#1）、选项打乱（#4、#14）、外部基准（#4）下成立；超参要在留出集上选（#4 自认没做到）。修复收益在换问法下复测这一项，现有 F 级工作里未见。
7. **效果量**：免训练内部修复要在 ≥ 2 个族上超过现有输入/解码侧基线（VEA 最多 +11.1 EM、CALRD 最多 +9.4%、PGLA 平均 +15.0 pp），并与提示基线（先框再答、两步法、visual CoT）和 LoRA 调 LLM 同表比较。
8. **统一解释**：要在同一批模型、同一批题上判别 E2 里至少两到三种说法（尤其 E2-d 对 E2-e 的「晚段压回」对「早层形成」，E2-b 对 E2-g），并说明为何 #1、#4 报告的「逐属性、逐任务类型、逐模型不同」不构成反例；否则与现有 8 种以上并列。
9. **与 A2 的边界**：要回答 F7——离开先验冲突题之后现象是否还在、占多大比例。

---

## 关键问题逐条作答（供合稿者直接取用）

**谁直接测了差距、多大。** 见第 2 节 #1、#3–#8、#11、#14、#19。量级：答错样本里 84.4% / 70.0%（下界 77.5% / 61.0%）属利用失败（#3，自然图，2 模型）；探针对行为差 +36、+47 个点（#4，单模型，另 13 个模型同向）；探针 0.72–0.79 对 argmax 变化 2–11%（#6，6 模型，n=83）；编码器读出对整机如 0.819 对 0.170（#8）。四个数字的量纲不同，不能互相换算。

**谁补过、补回多少、有无随机对照、稳健否。** 见第 3 节「效果量」三行与第 2 节「对照」「评测稳健性」两栏。F 级里带随机方向/部件对照的只有 #2（但它不做由错翻对）、#4（带外层与去图对照）、#15。

**末 token 口径矛盾：是不同设定，不是真冲突（推导，依据三篇 F）。**

| | 2604.09364 | 2606.06890 | 2606.28273 / 2505.17127 |
|---|---|---|---|
| 对比变量 | 图不同（反事实对标准），题相同 | 图不同，题相同 | **图相同**，提示不同（this 对 usually/most） |
| 干预对象 | 某一层的残差整体替换 | 某一层末 token 残差替换 | 末 token 上的头/MLP 输出（消融、修补），或连续多层加向量 |
| 层位 | 只在 MAC 层（36–71% 深度）一处 | 逐层扫 | 后半段（关键窗口起于 52–76% 深度） |
| 末 token 结果 | 0–1% 翻转 | 中层近零，21–23 层起效，27 层跳升（共 36 层） | 残差修补在后段窗口内恢复；整组头消融 68–96% |

读法：图不同而只换中层末 token 残差时，后面的层还会再去读没被换掉的图像位置，所以不翻（#1、#5 一致）；到后段再换就有效（#5）。#9、#10 的图本来就相同，差别只在提示，信息本就在末 token 一侧；它们动的是做读取的头或连续多层，不是某层的一次性状态。#1 没有报告后段的末 token 修补，所以「末 token 干预对 VLM 无效」这句话超出了它自己的数据。两组工作未在同一协议下比较过；#9 自列的 2×2 设计尚未做。另有一条相邻线索（S）：一篇 NeurIPS 2026 页面上的小规模研究报告图像 token 修补 0/12 恢复、图后文本位置修补可恢复，与 #1 的「图像 token 承担几乎全部因果效应」方向不同，但任务是图文说明冲突，未取到正文。

**有没有反驳「可读出 = 可用」。** 有：F1–F3（#4）；#6、#8 自己写了探针只是下界或充分非必要条件；文本侧的经典批评为 Hewitt & Liang 的 control tasks、Ravichander et al.（[2005.00719](https://arxiv.org/abs/2005.00719)）与 amnesic probing（S）；ICLR 2027 在审稿件里有「Decodable Is Not Necessarily Used」（Desk Rejected）、「Lagged Coupling」「Decodable but Confounded」等同主题文本侧工作（S）。

**文本 LLM、语音、视频的同类现象。**
- 文本：*LLMs Know More Than They Show*（[2410.02707](https://arxiv.org/abs/2410.02707)，S）；KAPPA 把差距解释为知识子空间与预测子空间错位并做推理时对齐，自由作答 41.7%→44.2%（[2509.23782](https://arxiv.org/abs/2509.23782)，A）；临床场景探针 AUROC 98.2% 而转向只纠正 24% 的漏判（[2603.18353](https://arxiv.org/abs/2603.18353)，S）；RAG 语境利用的机制研究两条线结论不一（S）。
- 语音：*Represented but Ignored*（[2608.19211](https://arxiv.org/abs/2608.19211)，A，4 个模型，隐藏状态干预能推向被压住的韵律判断，但非选择性恢复）；*Heard but Not Heeded*（2609.00727，S）；SonicBench（2601.11039，S）；VoxParadox（[2605.27772](https://arxiv.org/abs/2605.27772)，A）。
- 视频与全模态：#14；时间方向在编码器 73.1%、到 LLM 末层约 53%（2602.11244，S）；*MLLMs Know When Before Speaking*（2605.21954，S）。
- 现成的统一解释：E2-g（子空间错位）与 E2-h（线索整合）是两种可以让 VLM 结论变成推论的框架。未找到有人把 KAPPA 式对齐直接搬到 VLM 上并跨族验证（对象层；第 1、3 步共 7 条查询）；最接近的是 #11（计数，2 族，因果只 1 个模型）。

---

## 8. 七步检索日志

**本候选接受的检验**：一轮七步。网页检索 30 条；OpenReview 检索接口 28 次调用；Semantic Scholar 12 个端点（7 个成功）；OpenAlex 4 次（1 次有效）。存活不等于强：只查了这一轮。

### 第 6 步 对抗式检索（先做）— 网页 11 条 + OpenReview 在审稿件 8 条

网页查询：(1) VLM linear probe decodable not used … "decodable" not grounded；(2) perception is the bottleneck not reasoning … probe fails 2026；(3) hidden states encode correct answer but output wrong "seeing but not believing" follow-up intervention；(4) describe-then-answer prompting closes gap …；(5) VLM "knows" but fails to answer … extraction gap probe；(6) "Arbitration Failure, Not Perceptual Blindness" cited；(7) "Hidden in plain sight" … follow-up fix …；(8) "actionability gap" OR "probe-behavior gap" steering corrects only fraction …；(9) activation patching VLM natural images "seen but not used" … rescue wrong answers causal；(10) "Bigger Is Not Better" …；(11) "When Does a VLM Believe the Caption Over Its Eyes" …

OpenReview（限定 ICLR 2027 投稿）：vision-language models encode but fail to use visual evidence；seeing but not believing VLM；VLM linear probe decodable yet wrong answer；latent visual knowledge elicitation vision-language；activation patching vision-language visual evidence utilization；knowing but not saying multimodal；perception versus reasoning bottleneck vision-language probing；visual information utilization language decoder readout。

- 命中：2606.31257、2603.18373、2607.09544、2604.02486、2604.04411、2603.06054、2606.19297、2605.20177、ACL 2026 ARC 一篇、NeurIPS 2026 两篇、2608.20763、2603.18353、2608.22916、Bigger Is Not Better、2406.10638；ICLR 2027 在审 28 条里相关 11 条。
- 未命中：证明「换提示即可完全修好」的工作；证明定位结果换随机种子不可复现的工作（各 1–2 条查询，对象层）。

### 第 5 步 引用链挖掘

- Semantic Scholar：2604.09364 被引 12、参考 27（全部过目，取了 8 篇正文）；2506.08008 被引 69、参考 36（全部过目标题，取了 12 篇正文）；2606.31257 被引 3（只看标题：2610.17976 *Seeing Depth but Choosing Cues in Vision-Language Models*、2610.16135 *Omni-Modal LLMs Know More Than They Say*，均 S，未取正文）、参考 43；2609.00868 参考 31、被引未取到；2510.17771 与 2606.28273 被限流（429），未取到。
- OpenAlex：2510.17771 被引 6 条（只看标题）；另三次标题匹配错误，作废。
- 正文参考文献：通读了 2604.09364 的全部参考文献；从 2606.31257、2608.22916、2609.00868 的 Related Work 里追出 2603.18353、2601.12626、2603.21687、2604.23351、2604.16060、2603.22278、2602.08713 等。
- OpenReview：11 个标题查会议归属；取到评审正文的是 2510.17771（3 份）与 2604.09364（1 份 + 录用决定）。2506.08008 的 COLM 2025 评审未取到（检索接口只返回投稿本身；`/notes?forum=` 接口要求人机验证）。
- 网页 2 条：papers citing "Seeing but Not Believing" …；"Unveiling the Ignorance of MLLMs: Seeing Clearly, Answering Incorrectly"。
- 命中的新近邻：2611.01467、2610.29241、2610.19407、2606.06890、2605.13737、2610.03445、2609.35272、2608.17205、2610.19892、2610.23983、2607.26326、2607.12815、2604.14363、2604.12119、2603.19203、2602.19615、2510.04819、2509.23050。

### 第 1 步 抽象阶梯 — 4 条

模板：「模型内部有信息 X，输出不用」。(1) LLM hidden states encode correct answer but generate wrong answer "know more than they show" OR "hidden knowledge" …；(2) RAG context utilization failure mechanistic … arbitration；(3) video LLM temporal information linearly decodable … probing gap 2026；(4) audio LLM OR speech LLM encoder representation contains information linear probe but LLM ignores …。命中见「关键问题」一节。未命中：一篇同时覆盖文本、语音、视觉并给出同一机制的工作（结论层，4 条）。

### 第 2 步 方法论单独搜 — 4 条

(1) activation patching limitations interpretability illusion "hydra effect" best practices；(2) steering vectors unreliable generalization … AxBench …；(3) probing classifier accuracy does not imply model uses information control tasks amnesic probing …；(4) model editing static weight edit vision-language model … rank-one edit attention heads …。

命中（均 S）：Heimersheim & Nanda（[2404.15255](https://arxiv.org/abs/2404.15255)，修补结论只对所用提示分布成立、有后备部件补偿）；Zhang & Nanda（2309.16042，超参与指标会改变定位结果）；子空间修补错觉（2311.17030）；转向向量分布外不稳（[2407.12404](https://arxiv.org/abs/2407.12404)）；AxBench（2501.17148，提示强于 SAE 转向）及其 2026 年反驳（2605.31183）；Head Pursuit（2510.21518）。ICLR 2027 在审另有「What Can Activation-Patching Evidence Establish?」「When Activation Patching Admits Many Faithful Circuits」（S）。未命中：针对 VLM「视觉利用」的静态权重编辑（方法 × 对象层，1 条查询；最接近的是 #4 的 LoRA/ReFT 低秩编辑，属训练）。

### 第 3 步 蕴含检索 — 3 条

把 S1–S3 拿去搜：(1) VLM "visual utilization" bottleneck not perception universal mechanism across architectures intervention rescues errors language decoder readout circuit；(2) closing the gap between linear probe accuracy and VLM answer accuracy training-free intervention …；(3) VLM intermediate layer contains correct answer final layer wrong: layer-contrast decoding OR early-exit decoding …。命中：E1 的三句；CALRD、DeCo、DualPD、KAPPA、2507.07574。S1 后半、S2、S3 未找到逐字对应。

### 第 4 步 同义术语枚举 — 6 条

词表（先列后搜）：seeing but not believing；seeing right but saying wrong；seeing clearly, answering incorrectly；encoding–grounding dissociation；arbitration failure；hidden in plain sight；encoded but unused；visual-utilization failure；visual ignorance；visual insensitivity；visual sycophancy / split beliefs；decode ≠ deploy；conditional transport；routing failure；representation–action gap；knowledge–prediction gap；knowing vs. saying；use–elicitation dissociation；process failure；cognitive vs. perceptual failure；late-layer textual override；language prior / blind faith in text；modality neglect / modality collapse；visual laziness；alignment gap / linear separability ceiling；represented but ignored / heard but not heeded（语音）；中文：视而不见、看见了没用上。

查询：(1) "visual neglect" OR "visual laziness" OR "modality collapse" OR "visual forgetting" …；(2) "perception-reasoning gap" OR "extraction gap" OR "recognition-action gap" OR "knowing-doing gap" …；(3) "encoded but not used" OR "represented but ignored" OR "present but unused" OR "seen but ignored" …；(4) "latent visual knowledge" OR "implicit visual knowledge" OR "hidden visual knowledge" …；(5) "perception-cognition" OR "see but not understand" OR "look but not see" OR "knows but cannot tell" …；(6) 一条中文查询。新命中：2507.07574、2605.08200、2606.05753、2602.22766、2605.05593、2511.12928（均 S）。中文查询只返回英文论文的中文摘要页。

### 阅读量（分开数）

- **F：15 篇**。通读主体 4 篇：2604.09364、2609.00868、2606.31257、2510.17771。定向核对方法/对照/局限 7 篇：2606.28273、2608.22916、2606.06890、2506.08008、2505.17127、2607.09544、2610.29241。较浅（摘要 + 关键句 + 局限）3 篇：2611.01467、2605.13737、2604.02486。沿用第一轮 F、本轮只核一句引文 1 篇：2506.09047。
- **A：31 篇**。2606.17953、2601.07359、2410.11779、2603.18373、2604.04411、2507.07574、2610.23983、2604.14363、2610.19407、2608.20763、2608.19211、2509.23782、2606.13870、2603.21687、2604.23351、2601.12626、2610.03445、2609.35272、2608.17205、2610.19892、2607.26326、2607.12815、2605.27772、2604.12119、2603.19203、2602.19615、2510.04819、2509.23050；ICLR 2027 在审 3 篇摘要（Seeing Is Not Enough、Umbra Effect、Exact Visual Grounding）。
- **S：约 40 条**（只有检索片段或标题，含第 2 步的方法论文献、语音/视频同类、另 5 篇 ICLR 2027 在审标题）。
- 评审：2 篇论文的 OpenReview 评审正文（共 4 份评审 + 1 份决定）。
- 取到正文但本轮未读、沿用第一轮结论的：2507.13868、2606.17389、2608.07302、2502.17422、2405.18415、2605.17826、2512.03276、2507.01790 等。

### 第 7 步 边界申报

- **在审稿件**：只查了 ICLR 2027（OpenReview 公开，8 个检索词）。NeurIPS 2026 录用稿只见到会议页面片段；CVPR 2027、ACL ARR 在审稿件不可见。
- **引用链不全**：6 篇近邻里 3 篇（2510.17771、2609.00868、2606.28273）的 Semantic Scholar 被引列表因限流没取到；Google Scholar 未查。2510.17771 的被引只有 OpenAlex 的 6 条标题。
- **OpenReview 评审**：只取到 2 篇的评审正文；2506.08008、2606.28273、2608.22916 的评审没取到。
- **非 arXiv、非英文**：未覆盖；中文查询 1 条，无独立中文文献命中。
- **闭源模型**：内部证据为零，无法验证；#13、#14 只有行为数据。
- **知识截止**：我的知识截止在 2026-06，之后的工作全靠本轮检索；2026-06 及之后出现的 15 个竞争者里只有 8 个读到 F。
- **读得浅的近邻**：2611.01467、2605.13737、2604.02486 只做了较浅阅读；2610.19407、2606.17953 只到摘要，它们各自支撑第 4 节的一条（F6/F7、E2-h、E2-d），细节未核。
- **代码**：15 篇 F 里有公开仓库的 5 篇（#9、#10、#12、#14、#15；A 级里 #21、#23 也有）；#1–#7 正文均无仓库 URL，未去 GitHub 逐个搜索。
