# 13 七步查重：A3 多物体属性绑定

日期：2026-11-06。检索截至 2026-11。按 `00_AUDIT_BRIEF.zh-CN.md` 的顺序（6 → 5 → 1 → 2 → 3 → 4 → 7）与八节结构写。阅读层级：F＝取到正文并核对了对应章节或表（F* 表示只定向核对了所引的那几段，没有通读）；A＝只读了摘要；S＝只有检索片段。逐字引文与关键数字均在下载的正文上做过字符串核对（两批共 92 条，91 条整句命中；来自双栏 PDF 的 2610.05463 有两句只能分段命中，文中已标）。正文文本留在 `/tmp/a3_audit/papers/`，核对脚本在 `/tmp/a3_audit/scripts/verify.py` 与 `verify2.py`。

本候选在本轮接受的检验：39 条网页查询、6 条 OpenAlex 被引查询、Semantic Scholar 被引/参考文献接口（约 14 次请求，成功 3 次）、5 份参考文献表的人工扫描、4 次 OpenReview 取审稿尝试（全部被浏览器验证拦下）。存活不等于强：下面写的"未找到"只在这些查询的范围内成立。

**先说最不利的三条：**
1. "位置 ID 由语言模型中层头计算"这一定位有已发表的直接竞争解释：顺序信息主要来自视觉编码器，语言模型一侧只是备份（2603.22278，3 个模型族、带随机方向对照、在 COCO 上改正 40%/54% 的失败）。
2. "换提示让模型逐个指点"在闭源强模型的合成刺激上已能大幅修掉计数错误（Gemini 2.5 Pro、Claude 4.5 Sonnet；2512.15254）；在开源 3–8B 模型上则修不掉（2603.21746、2605.25427）。便宜办法这一关的结论随模型而变。
3. 三篇"内部说法"论文的主体刺激都是合成的；自然图像上的属性绑定错误已有专门基准（InstaBind-Lite，7 个模型），但那篇没有内部证据。

---

## 1. 候选定义

- **现象**：多物体、特征相近的场景里，VLM 把属性安到错误的对象上（misbinding / illusory conjunction），并连带合取视觉搜索、场景描述、计数失败。
- **根因主张（三种并存）**：(甲) 位置 ID 绑定头在特征共享时塌缩——语言模型中层的 ID retrieval / ID selection / feature retrieval 三组头；(乙) 概念向量在共享表征空间里几何重叠；(丙) 缺少串行处理，学会指点后出现 search heads。
- **预期结论（供第 3 步找"已被蕴含"用）**
  - E1：在同一批刺激、同一批模型（≥3 族）上，位置 ID 表征质量、概念向量重叠、是否串行输出三者各自解释了多少绑定错误；控制其中一个后，另一个是否还有独立预测力。
  - E2：三者是同一条因果链上的不同环节（重叠 → 以特征为查询取 ID 时受干扰 → 选错 ID → 串行输出绕开），还是相互独立的失败来源。
  - E3：该根因在自然图像的绑定错误上也成立，按根因设计的干预能补回若干点，而换提示补不回。

---

## 2. 竞争者全景表

核心竞争者（对象层重合：VLM 多物体绑定的定位、修复或基准）10 个，编号 K1–K10；相邻工作 14 组，编号 N1–N14。

### 2.1 核心竞争者

| # | 工作 | 类型 | 模型族 | 干预类型 | 对照 | 评测稳健性 | 效果数字 | 自认局限（逐字） | 代码 | 层级 |
|---|---|---|---|---|---|---|---|---|---|---|
| K1 | Campbell et al.，[2411.00238](https://arxiv.org/abs/2411.00238)，NeurIPS 2024 | 基准/行为 | GPT-4v、GPT-4o、Gemini Ultra 1.5、Claude Sonnet 3.5；另 4 个文生图模型 | 无（行为） | 析取对合取、特征熵操纵、feature triplet 计数 | 只有合成 2D sprite 与 3D Blender 场景；无自然图像 | 合取搜索随干扰物数下降而析取不降；计数受熵调制（数字见第一轮笔记 06） | "our experiments with the open-source Llava-1.5 yielded very poor performance on all tasks"；"none of these methods have yet been deployed at the scale of VLMs" | 未核 | F |
| K2 | Assouel et al.，[2506.15871](https://arxiv.org/abs/2506.15871)，ICLR 2026 Oral | 定位＋小幅修复 | 因果中介：Qwen2-VL、Qwen2.5-VL 3B/7B/32B、LLaVA-1.5 7B/13B、LLaVA-OneVision 7B（2 族 7 个）；Idefics2-8b 只有 RSA | 推理时：头输出的激活修补与加性编辑；键向量编辑 | 计数任务上 top-K 对 bottom-K 头消融（只在 Qwen2.5-32B）；绑定错误修补（附录 D 表 1）没有随机头对照；α 与 K 取扫出来的最优值 | 合成 2×2 / 3×3 网格；PUG 拟真图 200 张、每张 2 只动物；COCO 上按模型自己的描述顺序做干预（结果只在图 45）；没有换问法 | ID 编辑 ">79% efficacy"；低熵修补 +4.6（LLaVA-1.5-7B，27.5→32.1）到 +11.1（Qwen2.5-VL-3B，69.0→80.1），修补后仍比各自高熵基线低 11–38 点；计数：消掉得分最高的 250/2560 个头后 "performance falling to 0%" | "it is an open question whether the emergence of these mechanisms may be driven by architectural inductive biases … We leave the investigation of these questions to future work." | "Datasets, analysis and intervention code will be released."（正文无 URL） | F |
| K3 | Savietto, Campbell et al.，[2602.07025](https://arxiv.org/abs/2602.07025)，arXiv（v2 2026-06） | 定位（表征几何） | Qwen2.5-VL 7B、InternVL2.5 8B、Gemma 3 12B（3 族） | 推理时 steering 只用来验证向量；"重叠 → 搜索错误"这一步是相关 | 探针法对质心法；HSV 色距作替代预测量 | 向量从合成单物体图抽取；steering 在自然图像上验证（85–96%）；搜索任务为合成 2–40 物体 | 目标与最相似干扰物的余弦相似度对搜索正确率：target-present r = −0.90 / −0.90 / −0.97，target-absent −0.83 / −0.88 / −0.69（Qwen / InternVL / Gemma） | "We analyzed only the vision output; language representations may account for unexplained failure modes. We characterized what representations look like but not how they are computed. A complete account requires tracing the underlying circuits." | 正文写 "available at this link"，链接文本在转文本时丢失，未核 | F |
| K4 | Haputhanthri et al.，[2605.25427](https://arxiv.org/abs/2605.25427)，arXiv 2026-05 | 定位＋修复（微调） | search heads：Molmo-7B-D，另在 Qwen2.5-VL-7B 上复现；组合式表征 RSA：Qwen2.5-VL、LLaVA-1.5、Gemma3；微调：Qwen2.5-VL-7B、Gemma-3-12B、LLaVA-1.5-7B | 训练（全权重监督微调，point-to-answer 对 direct answer）；推理时注意力图替换 | Qwen 上消融 top-k 对 bottom-k 与随机 k 个头（100 例）；direct answer 的短/长提示；打乱指点顺序；多种替代的串行微调格式 | 分布外：更多目标数、11–15 个物体、多样性迁移、Pixmo-count 实拍 11–15 个；主体为合成 | 数字只在图里：direct answer 在更大计数上掉到 0%，point-to-answer 泛化；实拍上"both models struggled even with in-distribution counts"；Qwen 的 search heads 识别只用了"37 attention map replacements (across 13 images" | "This approach works well for specific tasks, but is unlikely to be feasible for a broader distribution of tasks."；"An important question for future work is how serial visual attention might be incorporated into more general-purpose training procedures for visual reasoning." | 未找到 URL | F |
| K5 | VISER，[2506.22146](https://arxiv.org/abs/2506.22146)，NeurIPS 2025 | 修复（改输入图＋提示，免训练） | GPT-4o、Claude 3.5 Sonnet、Llama4-scout、Qwen2.5-VL-7B | 输入级 | 行/列/网格/去行号消融与 CoT 基线都只在 GPT-4o 上；与两个 Qwen 微调变体对比 | 合成 2D/3D＋自然图像计数（FSC-147 来源）与空间关系 | 2D 计数 GPT-4o 12.00→38.83、Qwen2.5-VL 5.83→40.83；自然图像计数 GPT-4o 29.82→35.65，Qwen2.5-VL 18.91→17.29（下降） | "On natural images, improvements are more modest"；"a fixed scaffolding structure might show reduced gains when the interference between lines and objects is too high" | 网页 https://sharif-ml-lab.github.io/VISER/ | F |
| K6 | Grounding IDs，[2509.24072](https://arxiv.org/abs/2509.24072)，arXiv | 定位＋输入级修复（图与提示里放成对符号） | 机制：Qwen2.5-VL 7B，另 Qwen2.5-VL 3B、InternVL3.5 8B；行为：加 LLaVA-1.5、GPT-4o、Gemini-2.5-Pro | 推理时激活交换；输入符号 | 交换正确率对随机水平（0.25 / 0.125）；自然图像上用 PatchScopes 解码 0.76 对随机 0.25 | 合成为主；COCO 上有解码与 CHAIR | 表 3：计数 Qwen2.5-VL-7B 29.67 →（VISER 43.33）→ 53.00，GPT-4o 10.50 → 26.50 → 32.33；视觉搜索 GPT-4o 49.41 → 73.40 → 80.62 | 对前人的评语 "Notably, this study is limited to very simple images where grounding is trivial"；未来工作 "One direction involves discovering circuits that support system-2 reasoning tasks, such as counting and spatial reasoning." | https://github.com/sharif-ml-lab/GroundingID | F |
| K7 | Dual Mechanisms of Spatial Variable Binding，[2603.22278](https://arxiv.org/abs/2603.22278)，arXiv 2026-03 | 定位＋推理时修复 | Qwen2-VL 7B/2B、Qwen3-VL-8B、Gemma-3-4b、Pixtral-12B（3 族 5 个） | 推理时：interchange intervention；把位置探针方向加到全部视觉 token 上 | 随机方向对照；α 在验证集上选、在留出的失败样本上评；每组 100 对、95% bootstrap 区间；与 CoT 对比；7 个非空间 VQA 基准上的代价 | 3 个合成集＋What'sUp＋COCO-spatial；探针跨数据集、跨轴迁移 | "Ordering directions correct 40% and 54% of failures versus 10% and 13% for random directions"（Gemma-3-4b、Qwen2-VL-2B，逐题选 α，是上限口径）；非空间基准最多掉 5 点 | 没有单列局限段；自述 "This experiment aims to test generalization to natural settings … not to reach state-of-the-art accuracy" | https://spatial.baulab.info | F |
| K8 | Getting to the Point，[2603.21746](https://arxiv.org/abs/2603.21746)，arXiv 2026-03 | 修复（微调）＋机制 | Qwen2.5-VL 3B/7B、LLaVA-OneVision、InternVL3.5；另测 Gemma 4 | 训练（Point-then-Count 对 Direct Counting）；免训练提示 | 坐标换成 "X" 的微调；黑图＋真值坐标；逐个去掉坐标 | 合成 9×9 网格＋OCID 实拍；分布外更大计数 | 实拍上 PtC 比 DC 最多高 11.9%；用坐标个数当答案在 Qwen2.5-VL 3B 上再 +29.03 点 | "although we validate our findings on real-world images, OCID serves as a relatively controlled scenario" | https://github.com/sislab-unitn/Getting-to-the-Point | F |
| K9 | Visual Enumeration Abilities，[2512.15254](https://arxiv.org/abs/2512.15254)，arXiv 2025-12 | 基准＋提示 | Claude 4.5 Sonnet、Gemini 2.5 Pro、GPT-5、Qwen3-VL-235B | 提示（直接数／先标后数／先指点再标再数） | 三档提示的效应量 | FSC-147、FSCD-LVIS、自建 SolidCount（合成，因子设计） | SolidCount 上 point-label-count：Claude ε² = 0.291、Gemini 0.109，GPT 无差异；FSC-147 只有 Gemini 显著（ε² = 0.014） | "On FSCD-LVIS, none of the models exhibited significant differences across prompting strategies"；"the Qwen model was not able to follow the structured prompt instructions" | 未核 | F |
| K10 | InstaBind-Lite，[2608.16805](https://arxiv.org/abs/2608.16805)，arXiv 2026-08 | 基准＋输入级干预 | Qwen2.5-VL-7B、InternVL3-8B、LLaVA-1.5-7B、LLaVA-OneVision-7B、MiniCPM-V-2.6、Gemini-3.5-Flash、Qwen3-VL-Plus | 裁剪（oracle / 带上下文）；instance-first 提示 | 四档问法；按图像聚类的 1000 次 bootstrap | 自然图像 524 张（COCO/GQA/VAW/网络/自拍），529 组同类实例，9580 题 | 误绑率：开源均值 19.84%、API 7.55%，LLaVA-1.5 为 34.01%；"Among identifiable transfers, 80.70% and 81.51%, respectively, originate from adjacent instances."；裁剪让 LLaVA-1.5 正确率 +20.14、误绑率 −19.12；instance-first 让 InternVL3 误绑率 −4.36，但 "LLaVA-1.5 loses 22.58 accuracy points and increases MBR under the longer prompt" | "Localization and instance-first interventions help selected models but are not universal remedies."；干预"does not establish an internal causal mechanism" | 未找到 | F |

### 2.2 相邻工作

| # | 工作 | 与 A3 的关系 | 关键事实 | 层级 |
|---|---|---|---|---|
| N1 | Budny et al.，[2509.25142](https://arxiv.org/abs/2509.25142) | 同作者群的"串行处理缺陷"行为版 | CoT 与推理训练只在物体能被文字唯一指代时有效；工具（裁剪）只在物体可分开时有效，"tool use does not improve on baseline performance for either of the overlapping conditions" | F* |
| N2 | I Spy，[2510.19678](https://arxiv.org/abs/2510.19678) | 合取搜索行为复现＋GPT-4o 直接微调 | GPT-4o、Claude 3.5 Sonnet、Llama 3.2 90B；"Even minimal fine-tuning (10 examples) yields modest gains, while 100 and 1000 examples produce substantial improvements, though not to the level of pop-out. Notably, these gains extend to out-of-distribution set sizes (50–99 distractors)" | F* |
| N3 | Zhang et al.，[2610.05463](https://arxiv.org/abs/2610.05463)，Computational Brain & Behavior 2026 | 人（n = 1,250）对 MLLM，同刺激 | 错误率相关 ρ = 0.82；Gemini 2.0/2.5 Flash-Lite 等 3 个模型；目标缺席时的极端偏向"arise at the response or decision level rather than from position-specific perceptual limits"（双栏 PDF，分段核对） | F* |
| N4 | Wick，[2606.25066](https://arxiv.org/abs/2606.25066) | 推理 token 当反应时 | "a resolution control shows the conjunction cost is genuine search rather than difficulty resolving small shapes"；摘要称前沿模型在中档模型掉到随机线的地方保持正确率 | F* |
| N5 | Formalizing the Binding Problem，[2606.03976](https://arxiv.org/abs/2606.03976) | 绑定信息量的测量 | DINOv2-Large 上，[CLS] 编码不到一半的绑定信息；"the attention probe on the full set of spatial tokens decodes 92.2% of binding information" | F |
| N6 | Saravanan et al.，[2505.22200](https://arxiv.org/abs/2505.22200)，CVPRW 2025 | 文本 binding ID 搬到 VLM | 只有 LLaVA-OneVision-7B；合成 3D 形状；有同范数随机向量对照 | F* |
| N7 | Kang et al.，[2601.12626](https://arxiv.org/abs/2601.12626) | spatial ID（线性） | steering 中位信念翻转 64.4%，噪声 29.5%；LLaVA-1.5 7B 与 Llama-3.2-VL 11B 上 "wrong spatial IDs in object word activations led to wrong model answers, so linguistic reasoning was not the reason these failures occurred" | F* |
| N8 | Gaze Heads，[2606.14703](https://arxiv.org/abs/2606.14703) | 描述时"看哪里"的头，与 search heads 相邻 | 10 个模型；随机头与全部头对照；Qwen3-VL-8B 83.1%，Ovis1.5、Qwen2-VL、InternVL3.5 在 60–70% 档；"The LLaVA model family and Bunny-3B show no comparable gaze mechanism." | F* |
| N9 | Counting Circuits，[2603.18523](https://arxiv.org/abs/2603.18523) | 计数回路＋合成计数微调 | Qwen2.5-VL-7B、Qwen3-VL-8B、LLaVA-1.5-7B；LoRA 加注意力正则 | F*（第一轮 F） |
| N10 | 计数归因一簇：[2510.19555](https://arxiv.org/abs/2510.19555)、[2605.30170](https://arxiv.org/abs/2605.30170)、[2607.09544](https://arxiv.org/abs/2607.09544)、[2604.10039](https://arxiv.org/abs/2604.10039)、[2505.23941](https://arxiv.org/abs/2505.23941)、[2511.17722](https://arxiv.org/abs/2511.17722)、[2511.17699](https://arxiv.org/abs/2511.17699) | 计数失败的非绑定解释 | 见第 4 节 C3 | 前三篇第一轮 F / 本轮未重读；2607.09544、2604.10039 为 A；2511.17722 为 F*；2511.17699 为 S |
| N11 | 文本 LLM 实体绑定：Feng & Steinhardt [2310.17191](https://arxiv.org/abs/2310.17191)、Dai et al. [2409.05448](https://arxiv.org/abs/2409.05448)、Gur-Arieh et al. [2510.06182](https://arxiv.org/abs/2510.06182)（ICLR 2026）、Slot Machines [2604.21139](https://arxiv.org/abs/2604.21139) | 方法与结论模板的来源 | 见第 4 节"文本侧" | 2510.06182 为 F*；其余 S |
| N12 | Nurisso et al.，[2506.14797](https://arxiv.org/abs/2506.14797)，ICLR 2026 | 理论：泛化与辨识的取舍 | 预言多输入处理容量按 1/n 塌缩；VLM 实测只有 gemma-3-12b-it 与 Qwen2.5-VL-7B 的空间相似度任务 | F* |
| N13 | 行为基准：Auto-Comp [2602.02043](https://arxiv.org/abs/2602.02043)、SABER [2610.22602](https://arxiv.org/abs/2610.22602)、ROPE [2407.06192](https://arxiv.org/abs/2407.06192)、MATE [2503.03854](https://arxiv.org/abs/2503.03854) | 绑定的跨模型行为证据 | Auto-Comp：25+ 个 VLM，低熵干扰项暴露的 Swap 对 Confusion 差距在每个模型上都有；ROPE：自然图像上"more heterogeneous queries lead to substantially more hallucinations" | ROPE 为 F*；其余 A |
| N14 | Who Says What，[2609.31193](https://arxiv.org/abs/2609.31193)，NeurIPS 2026 | 音视频 LLM 上的同模板工作 | 三模态绑定用模态专属的符号变量；失败主要来自音视频连接错位；免训练修法是给说话人加框 | A |

---

## 3. 各轴最高水位

| 轴 | 目前最好的是谁、做到什么 |
|---|---|
| 模型族数量与多样性（行为） | 合成刺激：Auto-Comp 25+ 个 VLM（A）。自然图像：InstaBind-Lite 7 个模型、5 个开源族加 2 个 API（F）。闭源：Campbell 4 个（F）。 |
| 模型族数量与多样性（内部因果） | 位置 ID：Assouel，2 族 7 个模型，Idefics 只有相关（F）。空间变量绑定：Dual Mechanisms，3 族 5 个模型（F）。相邻的 gaze heads：10 个模型，并报告了阴性的族（F*）。概念向量：3 族，但到错误这一步只是相关（F）。search heads：Molmo 与 Qwen 两族（F）。 |
| 因果对照的严格程度 | Dual Mechanisms：随机方向对照、留出集选超参、bootstrap 区间、"先消掉编码器来源再测语言模型来源"的拆分设计（F）。Gaze Heads：随机头加全部头（F*）。Haputhanthri：bottom-k 加随机 k，但只在 Qwen、100 例（F）。Assouel 的绑定错误修补没有随机头对照。 |
| 评测稳健性 | InstaBind-Lite：自然图像、四档问法、按图像聚类的 bootstrap（F）。Dual Mechanisms：两个自然图像集、探针跨集迁移、验证/测试拆分（F）。在通读的 11 篇里，没有一篇对绑定错误的内部干预做过换问法或换选项顺序。 |
| 效果量 | 内部干预修绑定错误：Assouel +4.6 到 +11.1 点（合成，低熵）。内部干预修空间绑定：Dual Mechanisms 改正 40%/54% 的失败（COCO，逐题 α 上限口径）。输入级：Grounding IDs 计数 29.67→53.00（Qwen2.5-VL-7B）、视觉搜索 49.41→80.62（GPT-4o），均为合成。微调：Haputhanthri 在合成分布外条件下保持、direct answer 掉到 0%（图）；Getting to the Point 实拍 +11.9% 与 +29.03。裁剪：InstaBind-Lite 上 LLaVA-1.5 误绑率 −19.12。 |
| 任务与数据广度 | Campbell：搜索、计数、场景描述、类比四任务（合成）。VISER：四任务加 MMBench 等。Assouel：场景描述、取色、空间推理、计数消融，加 PUG 与 COCO。 |
| 是否免训练 | 免训练：Assouel 修补、Dual Mechanisms 放大、VISER、Grounding IDs、裁剪、提示。要训练：point-to-answer（K4、K8）、Counting Circuits。 |
| 是否给出统一解释 | 没有找到把甲、乙、丙放在同一批刺激上比较解释份额的论文（对象层；专门为此的查询 5 条，另核对了三篇之间的互引）。最接近的两种做法：Dual Mechanisms 在同刺激、同模型上用消融给"编码器来源对语言模型来源"排了主次；文本侧 Mixing Mechanisms（2510.06182）在同一批反事实输入上把位置、词汇、反身三种机制合成一个因果模型，正文报告平均 JSS 0.95，而只用位置机制的旧看法是 0.44。 |

---

## 4. 竞争解释与事实约束

### 4.1 事实约束

- **F1 训练外的指点提示在开源小模型上修不掉。**"Regarding training-free approaches, prompting models to point (PtC and # Coord) or enumerate (LtC) objects generally underperform DC."（Qwen2.5-VL 3B/7B、LLaVA-OneVision、InternVL3.5；[2603.21746](https://arxiv.org/abs/2603.21746)，F）。未微调的 Qwen2.5-VL 用指点提示时 "its performance on counting-via-pointing is extremely low"（[2605.25427](https://arxiv.org/abs/2605.25427) 附录 A.4.6，F）。
- **F2 同一类提示在闭源强模型的合成刺激上已大幅见效，实拍上不稳。**SolidCount 上 Claude 4.5 Sonnet 与 Gemini 2.5 Pro 有中到大的效应量，GPT-5 没有；FSC-147 只有 Gemini 显著且效应量小；FSCD-LVIS 都不显著（[2512.15254](https://arxiv.org/abs/2512.15254)，F）。
- **F3 纯文本 CoT 的效果随模型变号。**VISER 只在 GPT-4o 上测了 CoT；Dual Mechanisms 报告 CoT 提高 Qwen2-VL-2B、降低 Gemma-3-4b，且弄坏的原本答对的题约为放大干预的三倍（[2603.22278](https://arxiv.org/abs/2603.22278)，F）；Budny 等指出 CoT 只在物体可被文字唯一指代时有效（[2509.25142](https://arxiv.org/abs/2509.25142)，F*）。开源带思考的变体（Qwen3b-Thinking、Kimi-VL-A3B-Thinking）在计数上 "reasoning does not consistently improve counting performance"（[2511.17722](https://arxiv.org/abs/2511.17722)，F*）。
- **F4 自然图像上绑定错误存在，且输入级修法不通用。**见 K10。裁剪在 Gemini-3.5-Flash 与 Qwen3-VL-Plus 上反而升高误绑率；instance-first 提示在 LLaVA-1.5 上掉 22.58 点（[2608.16805](https://arxiv.org/abs/2608.16805)，F）。
- **F5 LLaVA 系在多条线上表现不同，且混着地板问题。**位置 ID 的相对编码在 LLaVA 上不明显（K2）；gaze heads 在 LLaVA 与 Bunny 上没有（N8，作者的假说是冻结编码器，未证实）；坐标对 LLaVA-OneVision 只有边际提升（K8）；LLaVA-1.5 在 Campbell 的全部任务上很差（K1），在 Assouel 的高熵条件下也只有 70.3%。推导：LLaVA-1.5 上的失败不能直接当作"干净的绑定失败"。
- **F6 现有内部修补幅度小，且口径是上限。**Assouel 的修补用的是"a robust prototype of the spatial symbol for each grid position"，即按目标所在格子取高熵成功试次的平均激活。推导：这个干预带入了目标位置这一信息，+4.6 到 +11.1 应读作知道目标位置时的上限。
- **F7 指点微调后的模型主要靠文本坐标作答。**"removing the image has little effect (<2% drop) on performance, indicating that models generate the final count mostly based on the coordinates, disregarding the visual modality"（[2603.21746](https://arxiv.org/abs/2603.21746)，F）。
- **F8 编码器空间 token 里绑定信息可解码。**DINOv2-Large 上 92.2%（[2606.03976](https://arxiv.org/abs/2606.03976)，F）。作者同时声明 "our probes measure decodable binding information rather than whether the model causally uses such information during downstream inference"。我只核对了 DINOv2-Large 的数字，没有核对 VLM 实际使用的 SigLIP / CLIP 编码器的结果。
- **F9 自然图像上"熵"的操作化不能照搬。**ROPE 里异质查询更易出错，方向与合成集里"低熵更糟"相反；但 ROPE 的任务是给框认 5 个物体的类别，口径不同，不构成矛盾（[2407.06192](https://arxiv.org/abs/2407.06192)，F*）。

### 4.2 竞争解释

- **C1 顺序信息的主来源是视觉编码器，不是语言模型中层头。**"this mechanism plays only a secondary role in shaping model predictions. Instead, the dominant source of spatial information originates in the vision encoder"；信息分布在背景 token 上，只换物体 token 不翻转答案，连同背景条带一起换才翻转；把编码器来源消掉后语言模型在第 11–20 层自己重建一份（[2603.22278](https://arxiv.org/abs/2603.22278)，F）。该文对 Assouel 的评语是 "they do not reveal their origin"。Kang 等也把 LLaVA / Llama 的失败归到错误的 spatial ID（N7）。注意：C1 的任务是空间关系查询，不是特征共享条件下的属性绑定；它直接竞争的是甲的定位，没有测低熵条件。
- **C2 决策层偏置。**目标缺席时的错误来自响应或决策层面的极端偏向（N3）。
- **C3 计数失败的非绑定解释。**输出层（2510.19555）；符号映射（2605.30170）；计数信息在、读出方向错位，steering 最多 +15.6 点（2607.09544，A）；视觉证据在投影处最强、进语言层后衰减并让位给文本先验（2604.10039，A；2505.23941）。绑定一方的证据：熵调制计数（K1）；形状异质时 Gemini 正确率 52.7% → 70.4%，GPT 与 Qwen 在颜色异质时也更好（K9，F）；Assouel 的头消融把计数打到 0%（只在 Qwen2.5-32B）。
- **C4 指点为什么有效，有三种读法。**内部串行搜索例程（K4）；文本坐标充当结构化中间表示（K8 与 F7）；外加线索诱导出跨模态的 grounding ID（K6）。
- **C5 直接微调是否也能泛化。**Campbell 预言直接微调若能缓解，是靠去掉组合式表征；K4 报告 direct answer 不泛化到更多目标数与更大计数；N2 报告 GPT-4o 直接微调后泛化到分布外的干扰物数量但到不了 pop-out。三者的"分布外"轴不同（目标数、计数范围、干扰物数），不构成矛盾，但"只有串行才泛化"要带条件。
- **C6 理论上不可避免的读法。**Nurisso 等把容量上限写成有限语义分辨率下的 1/n 塌缩（N12）；局限段写 "Extending our framework to compositional coding schemes remains an important future direction."
- **C7 认知科学内部对绑定问题是否存在有争论。**Scholte & de Haan 2025（TiCS，"Beyond binding"）及回应（S，只见检索片段与 OpenAlex 标题）。只影响叙事，不影响 VLM 上的实测。

### 4.3 三种内部说法之间的关系

- **有没有人在同一批刺激、同一批模型上比过各自解释多少错误**：没有找到（对象层；专门查询 5 条：第 6 步第 13 条、第 3 步 3 条、第 5 步第 6 条，另加互引核对）。
- **互引核对（本地全文字符串检索）**：乙（2602.07025）引甲一次，只作为"binding failures are the cost of compressing rich visual information into reusable representations"的例证；丙（2605.25427）引甲两处（背景与方法）；乙与丙互不引用；甲早于两者；Dual Mechanisms 引甲，不引乙与丙。
- **模型重合**：Qwen2.5-VL-7B 是三篇共有的唯一模型。LLaVA-1.5-7B 在甲与丙；Gemma-3-12B 在乙与丙；InternVL2.5 只在乙；Molmo 只在丙。
- **刺激不重合**：甲用 2×2 / 3×3 网格的场景描述补全；乙用 2–40 物体的视觉搜索与颜色相似度任务；丙用字母搜索与计数。
- **测量位置不同**：甲在语言模型中层头的输出（提示 token 与末 token）；乙在视觉输出处，向量从单物体图像抽取；丙在注意力图与逐层 patch 表征。
- **推导（未被任何一篇检验）**：三者可以排成一条链——乙的重叠发生在语言模型入口；甲的 ID retrieval 以物体特征为查询去取位置，特征相近时取错；丙的串行输出绕开并行检索。甲自己的表述"interference during the ID retrieval process"与此相容。C1 再往前加了一环：位置信号本身来自编码器。
- **可用于区分的现成线索（推测）**：InstaBind-Lite 报告约 81% 的误绑来自相邻实例。按乙，错误应随特征相似度变；按甲与 C1，错误应随空间索引的可分性变。该文自己说明顺序距离分析没有建立欧氏距离的因果效应。

### 4.4 "less pronounced" 具体指什么

- 正文："We found that models from the Qwen family had a clear preference for a relative coding scheme … The effects were less pronounced for models from the LLava family … This may be a result of differences in position embeddings for the Llava models, or may be due to Llava's significantly smaller training set."
- 附录 A.5.3：RSA 结果 "confirmed that the Qwen family of models employ a relative position coding scheme, while the difference was less pronounced for the Llava family. Interestingly, those results are also reflected in the effectiveness of the interventions reported in Figure 29."；"We also tested a model from the Idefics family, finding similar results as those seen for the Qwen models"。
- 即：指的是相对与绝对两种编码的 RSA 差别在 LLaVA 上较小，且对应的相对/绝对干预效果也较弱。跨族差多少只在图 26–29 里，正文没有数字，我没有取到。两个解释（位置嵌入不同、训练集小）作者都没有检验。
- Dual Mechanisms 的补充："the LM-backbone ordering information is predominantly encoded by relative position, whereas the vision encoder encodes both absolute and relative position"（附录 C.6.2，我只读到正文里的这句转述）。

### 4.5 文本 LLM 的实体绑定做到哪，VLM 结论是否是直接推论

- 文本侧：binding ID（2310.17191）、顺序子空间（2409.05448）、实体追踪与 lookback（Prakash 等）、三机制混合（2510.06182：实体变多时 "the positional mechanism becomes noisy and unreliable in middle positions"，由词汇与反身机制补充；9 个模型、3 个族、10 个任务）。2510.06182 全文里 "vision / image" 字样出现 0 次。
- VLM 侧不是直接推论，依据有三：甲自述"entails a different circuit altogether"且表征跨多个 patch；C1 显示位置信号主要来自编码器并分布在背景 token 上，与文本侧"局限在单个或少数相邻 token"不同；N6 把 binding ID 直接搬到 LLaVA-OneVision 上只做了每图两个物体的简单场景。
- 方法层被占：interchange intervention、三机制因果模型都是文本侧现成的。结论层：没有找到把"位置机制随实体数变噪、由别的机制补位"这句话写到 VLM 上的论文（结论层，第 1 步 5 条加第 3 步 3 条查询）。

---

## 5. 作者留下的开口（逐字）

- Assouel（2506.15871，结论）："it is an open question whether the emergence of these mechanisms may be driven by architectural inductive biases, such as the use of distinct query/key and value embeddings … or distributional aspects of the training data. We leave the investigation of these questions to future work."
- Assouel（§4.1）："This may be a result of differences in position embeddings for the Llava models, or may be due to Llava's significantly smaller training set."
- Savietto（2602.07025，Limitations）："We analyzed only the vision output; language representations may account for unexplained failure modes. We characterized what representations look like but not how they are computed. A complete account requires tracing the underlying circuits."
- Savietto（结论）："whether this structure is induced by the LLM's discrete token space or arises intrinsically remains open for future work"。
- Haputhanthri（2605.25427，引言）："it remains unclear whether learning to point actually induces an internal visual search routine similar to that in humans, or whether its performance benefits arise from resolving the binding problem in VLMs"。
- Haputhanthri（结论）："An important question for future work is how serial visual attention might be incorporated into more general-purpose training procedures for visual reasoning."
- Dual Mechanisms（2603.22278，引言，评前人）："they do not reveal their origin"。
- Grounding IDs（2509.24072，结论）："One direction involves discovering circuits that support system-2 reasoning tasks, such as counting and spatial reasoning."
- Getting to the Point（2603.21746）：留给未来的是其他任务、更复杂的实拍场景与更多样的指代表达。
- Budny（2509.25142）："This points to the need for developing intrinsically visual forms of serial processing"。
- Zhang 等（2610.05463，分段核对）："Is this a failure of binding, a premature quitting strategy, or an artifact of the models' training?"
- InstaBind-Lite（2608.16805）：干预"does not establish an internal causal mechanism"。
- Formalizing Binding（2606.03976）："our probes measure decodable binding information rather than whether the model causally uses such information during downstream inference"。
- Gaze Heads（2606.14703）：哪些架构会长出这类头、同一批头是否也中介空间推理与幻觉，被列为开放问题。
- Nurisso（2506.14797）："Extending our framework to compositional coding schemes remains an important future direction."

---

## 6. 三列表

| 先例支持 | 事实约束与竞争解释 | 谁会因此改做法 |
|---|---|---|
| 现象跨模型：闭源 4 个（K1）、开源多族（K2–K4、K10、N13）；自然图像上有可分离的误绑率（K10）。 | F1–F3：便宜办法的结论随模型变；F4：输入级修法不通用。 | 做免训练输入级修法的人（VISER、Grounding IDs 一线）：K5 附录 E 已给出加线有害的条件，知道根因在哪一环能决定何时该加、何时该裁。依据是这两篇自己的未来工作段。推测档。 |
| 根因有因果干预：甲在 2 族（K2），空间绑定在 3 族（K7），相邻头在 4 个族成立（N8）。 | C1：定位之争（编码器对语言模型中层）；F6：甲的修补是上限口径。 | 训练带指点或 grounding 监督的模型开发者：甲的结论段点名 spatial pointing tasks 与 object-centric 架构；C1 与 N8 则指向编码器是否与语言模型一起训练。没有找到已发表的证据表明有人因此改了训练做法。 |
| 方法先例齐全且有代码：interchange intervention（K7、N11）、探针方向放大（K7）、头消融对照（K4、N8）、绑定信息量探针（N5）。 | C3：计数失败有四种非绑定解释，没有分账；C4：指点为何有效有三种读法。 | 基准作者：K10 把自己定位为 "testbed for future grounding-aware decoding, contrastive neighbor suppression"。 |
| 文本侧已有"三机制同刺激比较"的模板（2510.06182）。 | F5：LLaVA 系混着地板问题；F9：自然图像上熵的操作化不同；C6：理论上不可避免的读法。 | 未找到其他。 |

---

## 7. 要构成足够贡献至少需要做到什么

只写门槛，按"超过第 3 节水位"列。

1. **模型族**：内部因果证据做到 ≥3 个族，并包含 Qwen2.5-VL-7B（三篇共有，便于对上已有数字）。要超过 K2 的 2 族，至少持平 K7 的 3 族；LLaVA 系若纳入，要同时报告高熵基线，把地板与绑定分开（F5）。
2. **对照**：每个头级或方向级干预在全部模型上带随机头或随机方向以及 bottom-k 对照（现有水位：K7、N8 做全了，K2 的绑定错误修补没有）；超参在留出集上选（K7）；不带入目标位置的干预与带入的分开报告（F6）。
3. **三种说法同台**：同一批试次、同一批模型上同时测位置 ID 质量、概念向量重叠、并行对串行输出，给出各自与联合的解释份额；并包含"编码器来源对语言模型来源"的拆分（C1 的设计是现成水位）。目前这一格在对象层空着（见 4.3 的查询范围）。
4. **绑定专属的因变量**：用来源可识别的误绑率，而不只是总正确率（水位：K10）；覆盖场景描述、合取搜索、计数三类任务（水位：K1 四任务，K2 四任务）。
5. **计数分账**：说明计数错误里有多少可归到绑定，并与输出层、符号映射、读出错位、文本先验四种解释在同一批数据上对照（C3）。目前没有找到做过这件事的论文（对象层，第 6 步第 7、10、12 条与第 4 步第 3 条查询）。
6. **自然图像**：内部证据落到自然图像的属性绑定错误上。现有水位是 K2 的 COCO 顺序干预（只有图）、K6 的 COCO 解码 0.76、K7 的 COCO-spatial（空间关系，不是属性绑定）；属性绑定的自然图像基准（K10）上还没有内部证据。
7. **修复效果量与基线**：免训练的内部干预要超过 K2 的 +4.6 到 +11.1 点，并与输入级基线（K5、K6：29.67 → 43.33 → 53.00）、裁剪（K10）、指点微调（K4、K8）在同一批数据上同台。
8. **便宜办法一关**：在目标模型上报告 point-label-count、instance-first、CoT、带思考变体四种提示基线。开源 3–8B 上已有"修不掉"的证据（F1）；闭源强模型的合成集上提示已见效（F2），所以立论条件要选在提示修不掉的地方（重叠、同色、实拍密集——N1、K9、K10 指向这些条件）。
9. **稳健性**：换问法、换选项顺序、留出数据。通读的 11 篇里没有一篇在内部干预上做全。
10. **发现类贡献的下限**：现有定位论文都带了干预修复实验（K2 表 1、K7 表 1、K6 表 3）；只给相关性读数会低于水位（K3 是目前唯一停在相关的一篇，且自己写明是局限）。

---

## 8. 七步检索日志

### 第 6 步 对抗式检索（16 条网页查询＋4 次 OpenReview 尝试）

1. VLM binding problem failure not binding alternative explanation counting visual search
2. set-of-mark OR pointing prompt fixes multi-object attribute binding counting vision language models 2026
3. arXiv 2026 vision language model binding errors mechanism position IDs replicate OR "do not replicate" OR alternative ordering
4. "binding" vision language models attention heads "illusory conjunction" OR "feature binding" mechanistic 2026 arXiv LLaVA InternVL
5. reasoning models thinking solve visual search conjunction counting binding problem VLM GPT-5 Gemini 2.5 serial
6. zero-shot "point" then count prompt VLM counting accuracy improvement Molmo Qwen2.5-VL grounding prompt without fine-tuning binding
7. VLM counting failure cause not perception symbolic mapping OR "language prior" OR "output layer" probe encoder sufficient 2026
8. attribute binding natural images benchmark multimodal LLM attribute swapped objects LLaVA GPT-4o fail real images compositional
9. object-centric tokens OR slot attention vision language model fixes binding problem multi-object counting visual search fine-tuning 2026
10. "The Count Is There, but Misaligned" counting failures VLMs arXiv
11. set-of-mark prompting visual grounding marks improve attribute binding multi-object LLaVA open-source fails "set-of-mark" limitation 2025 2026
12. visual crowding vision language models counting failure competing explanation resolution patch overlapping objects not binding
13. VLM binding failures "position ID" "concept vector" OR "representational interference" OR "search heads" compare explanations same stimuli unified account 2026
14. multi-object hallucination ROPE attribute binding VLM mechanism heads intervention feature entropy homogeneous objects 2026
15. VLM visual search conjunction natural images real-world scenes binding failure humans comparison 2026 arXiv MLLM "visual search" natural
16. "Feature binding in biological and artificial vision" Trends in Cognitive Sciences 2025 "no binding problem" deep networks argument; "No free lunch with the binding problem"

- 命中：F1–F4、C2–C5、K8、K9、N5、2607.09544、2604.10039、2607.06420。C1（2603.22278）不是这一步找到的，是第 5 步从 K2 的被引表里出来的；K10 是第 4 步换词后才出来的。
- 未命中：否定位置 ID 存在的复现失败报告；证明定位结果与随机对照分不开的工作；专门在属性绑定上评测 set-of-mark 的工作。
- OpenReview：论坛 3RQ863cRbx（K2，ICLR 2026 Oral）、Q5RYn6jagC（K1）、T52hZeT7rn（K5）的回复接口与网页都被浏览器验证拦下，一条审稿意见都没读到。

### 第 5 步 引用链挖掘

- Semantic Scholar 接口：K2 的被引 16 条、参考文献 47 条取到；其余论文被限流（同一出口 IP 上有另一路查重也在用该接口），K1 的被引表没有取到。
- OpenAlex 被引查询 6 条（K1–K6）：K1 得 16 条非 arXiv 的被引，K3、K5、K6 各 1 条，K2、K4 为 0（OpenAlex 对 arXiv 互引覆盖差）。
- 本地参考文献表扫描 5 份：2506.15871、2605.25427、2602.07025、2603.22278、2509.24072；并做了甲、乙、丙与 C1 之间的互引字符串核对。
- 网页查询 7 条：
  1. Saravanan "Investigating Mechanisms for In-Context Vision Language Binding"
  2. "Do VLMs Have Bad Eyes? Diagnosing Compositional Failures via Mechanistic Interpretability"
  3. "Training-Free Visual Search" "Context-Aware Scanpath Simulation" vision language models
  4. Budny "serial processing" deficits explain divergences human VLM reasoning geometric enumeration mental rotation arXiv 2025
  5. Tangtartharakul Storrs 2026 visual search binding vision language models; Alonso "Vision-language models struggle to align entities across modalities"
  6. "position IDs" OR "position ID" vision language model binding Assouel follow-up 2026 fix binding errors training OR fine-tuning OR intervention
  7. "feature entropy" OR "feature triplets" OR "low entropy" VLM binding errors scene description 2026 open-source models benchmark InternVL Gemma Qwen
- 命中：2603.22278、2606.14703、2609.31193、2606.03976、2605.31503、2610.07646、2601.12626、2509.25142、2503.03854、2508.16652。
- 未命中：K2 之后专门修位置 ID 的训练或微调工作；第 3 条的那篇 ACM 论文只有 OpenAlex 标题，没找到正文；Tangtartharakul & Storrs 2026 没查到。

### 第 1 步 抽象阶梯（5 条）

模板："用共享（组合式）表征并行处理多个条目的系统，会按特征重叠程度发生错配；内容无关的索引在干扰下退化；串行化可以绕开。"

1. Gur-Arieh Geva Geiger "Mixing Mechanisms" how language models retrieve bound entities in-context positional lexical reflexive
2. language model entity binding fails many entities similar attributes interference binding ID capacity limit mechanistic 2025 2026
3. Nurisso "generalization-identification tradeoff" OR "curse of generalization" Frankland capacity limit multi-object neural networks theory binding
4. video LLM OR audio LLM multi-entity attribute binding errors mechanism symbolic indices interference similar entities interpretability
5. text-to-image diffusion attribute binding leakage cause text encoder embedding entanglement mechanism fix attention "attribute binding" analysis

- 命中：2510.06182、2604.21139、2506.14797、2609.31193、Magnet 2409.19967（文生图里把属性错配归到文本编码器，S）；ViT 物体绑定 2510.24709（由第 6 步第 9 条带出）。
- 未命中：在文本 LLM 上按"属性相似度"操纵干扰并测绑定机制退化的工作。

### 第 2 步 方法论单独搜（3 条）

1. activation patching attention head localization unreliable VLM OR LLM "mean ablation" "resample" hyperparameters sensitivity circuits not robust across prompts
2. steering vectors concept directions limitations unreliable side effects "activation steering" generalization failure evaluation 2025
3. probing representational similarity analysis does not imply causal use "control tasks" OR "amnesic probing" limitation decodable not used

- 命中（均 S）：Zhang & Nanda 2309.16042（度量与腐化方式不同会得出不同的定位结果）；AtP* 2403.00745（注意力饱和与正负抵消造成假阴性）；消融基线比较 2408.17322；Tan 等 NeurIPS 2024（steering 的可操纵性逐输入差异大）；Elazar 等 2006.00995 及后续（可解码不等于被使用；去掉后不掉分也不等于没用上）。
- 对本候选的含义（推导）：K2 用单一度量与平均激活修补、K3 停在相关、N5 自己声明可解码不等于被使用，都落在这些已知局限里。
- 未命中：专门报告 VLM 上头级定位不稳定的工作。

### 第 3 步 蕴含检索（3 条）

1. VLM binding errors "ID retrieval" interference caused by feature similarity query key matching mediates representational similarity position index collapse explains errors
2. unified mechanistic account multi-object failures vision language models counting visual search binding same circuit shared heads across tasks causal 2026
3. fine-tuning multi-object binding VLM generalization trade-off compositional representations "conjunctive" direct answer shortcut synthetic counting transfer real images

- 命中：没有找到写出 E1 或 E2 的论文。E3 被部分触及：K7 在自然图像上做到了"按机制设计的干预有效、CoT 不能替代"，但对象是空间关系。
- 未命中：E1、E2 的任何一句。

### 第 4 步 同义术语枚举（5 条）

词表：binding problem、attribute / feature / variable / entity binding、attribute–object association、misbinding、swap errors、illusory conjunction、attribute leakage、attribute hallucination、instance confusion、object individuation、multi-object hallucination、compositional hallucination、feature interference、crowding、superposition、who-is-who。

1. "swap errors" OR "misbinding" OR "attribute leakage" vision language model multi-object mechanism LLaVA Qwen attribute hallucination interpretability
2. attribute hallucination multi-object VLM "attribute" confusion between objects attention heads causal intervention mitigation LLaVA InternVL training-free 2026
3. "object individuation" OR "instance individuation" vision language models counting mechanism interpretability tokens per object
4. "variable binding" OR "entity-attribute" image tokens VLM causal tracing which object "color of the" multi-object information flow last token retrieval heads 2025 2026
5. "compositional hallucination" OR "attribute-object mismatch" OR "instance confusion" OR "who is who" large vision language model crowded scenes same-class objects benchmark mechanism

- 命中：K10（由 misbinding 一词带出，前面五步都没碰到）、2511.17699、2509.14837、2605.30911。
- 未命中：幻觉社区里针对"物体间属性错配"的头级干预。

### 阅读量

- F（通读了方法、结果、局限）：11 篇——2411.00238、2506.15871、2602.07025、2605.25427、2506.22146、2509.24072、2603.22278、2603.21746、2512.15254、2608.16805、2606.03976。
- F*（取到正文，只定向核对了所引段落）：12 篇——2509.25142、2510.19678、2610.05463、2606.25066、2505.22200、2601.12626、2606.14703、2603.18523、2510.06182、2506.14797、2407.06192、2511.17722。
- A（只读摘要）：9 篇——2604.10039、2607.09544、2602.02043、2510.24709、2610.22602、2609.31193、2605.31503、2610.07646、2503.03854。
- S（只有检索片段或标题）：约 19 篇——2604.21139、2508.16652、2511.17699、2509.14837、2607.06420、2605.30911、2310.17191、2409.05448、2409.19967、2310.11441、2606.06890、2605.15672、2604.09942、2505.17726、2502.14113、2411.17794、2309.16042、2403.00745、TiCS 绑定争论的几篇。
- 沿用第一轮 F、本轮没有重读：2510.19555、2605.30170、2505.23941。

### 对第一轮笔记的更正

- 05-M3 写"随机对照：grep 无命中"。更准确的说法：附录 C 有 top-K 对 bottom-K 的头消融对照，但只在计数任务、只在 Qwen2.5-32B；绑定错误修补确实没有随机头对照。
- 06-概念 1 的 Gap"2605.25427 附录 A.4 未读"已补：Qwen2.5-VL 上的 search heads 用 37 次替换、13 张图识别；消融带 bottom-k 与随机 k 对照，100 例。
- 06-概念 1 的"换提示不能、换输入能"过粗：见 F1–F4，结论随模型与刺激变。

### 偏离记账

- 顺序：主体按 6 → 5 → 1 → 2 → 3 → 4 执行；第 4 步第 1 条与第 2 步第 1 条是和第 5 步的两条查询同批发出的，早于第 1 步的收尾。不影响结论。
- 第 5 步里 2506.22146 的 Semantic Scholar 被引结果文件在清理磁盘时被我连同已转文本的 HTML 一起删掉，没有读；该文的被引只看了 OpenAlex 的 1 条。
- 中途本机 /tmp 配额写满，我删除了自己在 /tmp/a3_audit 下载的 HTML 与 PDF 原件（文本已提取），没有动其他目录。

### 第 7 步 边界申报

- **OpenReview 审稿讨论**：0 条读到（被浏览器验证拦截）。K2 是 ICLR 2026 Oral，审稿人对随机对照、LLaVA 差异、位置嵌入解释的质疑与作者答复都没看到。
- **被引覆盖不全**：K1 的 arXiv 被引表没有取到；K2 在 Semantic Scholar 上只有 16 条被引，对一篇 Oral 来说可能偏少；Google Scholar 没有查。
- **图里的数字**：HTML 转文本取不到图。K2 的相对/绝对 RSA 与图 29、图 45，K4 的图 6 与图 8，K7 的固定 α 结果（附录 C.7）都没有数值。
- **附录**：K3、K7、K8 的附录只读了被正文转述的部分。
- **闭源模型**：内部无法验证；F2 只有行为证据。
- **在审稿件、非 arXiv、非英文、并行未公开工作**：没有覆盖。OpenAlex 标题里的 "On Locality and Length Generalization in Visual Reasoning"、"No free lunch with the binding problem" 等只见标题。
- **知识截止**：2026-06 之后的工作完全依赖检索；本轮找到的 2026-07 以后的论文有 2607.09544、2608.16805、2609.31193、2610.05463、2610.07646、2610.22602，不能保证没有漏掉同期的直接竞争者。
- **代码**：只从正文摘出 URL，没有点开核实仓库内容。
