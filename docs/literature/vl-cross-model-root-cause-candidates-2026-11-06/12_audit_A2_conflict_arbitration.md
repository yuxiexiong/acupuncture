# 12 七步查重：候选 A2「冲突仲裁」（图像与另一信息源冲突时谁赢）

检索日期 2026-11-06，检索截至 2026-11。七步顺序 6 → 5 → 1 → 2 → 3 → 4 → 7。阅读层级：**F** = 取到正文并核对了对应章节或表；**A** = 只读了摘要（含取到全文只读摘要）；**S** = 只有检索片段或取到未读。逐字引文在 `pdftotext` 输出上做了二次核对（两批共 70 条，69 条整句命中；1 条因页码夹在句中，拆成前后两半后各自命中，见 §8）。ICML 2026 He et al. 一行只有会议页面的转述，不算逐字引文。推断标档：推导 / 类比 / 推测。本文不给等级、分数或"值得做"的判断。

**先说最不利的六点（细节见各节）：**

1. **"三类冲突是否共用同一仲裁节点"在部件层既没有被证明，也没有被否证**（对象层与结论层；本轮专门查询 4 条 WebSearch + 3 条 arXiv API + 7 篇邻居的被引清单）。但间接证据不站在"单一节点"一边：同框做了三类冲突的唯一一篇（2602.14518，探针）结论是类型**线性可分**；文本 LLM 上有两篇直接报告"同一批头换一种冲突就角色反转"与"找不到通用冲突回路"；(b) 类两篇论文给出的层位互不相同（最早层 vs 中深层）。
2. **第一轮说的"机制只在图压过先验的设定上做过"已不完全成立**：WhatIfVis（2607.26326）把层级激活修补与一维可控向量做到了含 count、weight 的"先验压过图"设定上，3 族 6 模型，带随机 rank-1 对照。它是层级不是头级，这是剩下的差距。
3. **冲突类头级定位普遍缺"多次层匹配随机抽取"的对照**，而一篇方法学论文（2610.13111）已经实测：在 Qwen3-VL-8B 上，发现的视觉头集的转向效果**不优于**层匹配随机头集，单次随机抽取的基线无法定位。另一篇（2607.26913）实测：打乱配对后拟合出的方向，修复成功数与正确配对几乎一样（59/66 对 60/66）。
4. **"先验压过图"一侧出现了不靠内部干预的较强修法**：视觉 in-context 示例（+9.7 到 +30.3 点，五个模型族，含动物腿计数）、候选级先验校准 SPC（+7.8/+7.0 点且测了候选顺序置换）、纯文本后训练 TACT（66.8→80.4）。任何内部修复都要和它们同表比。
5. **行为层的统一已被占**：2610.19407 用一条线性合并律（先验以单位权重进入，文本与视觉各一个权重）在未见降质组合上预测 VLM 偏好（R² 0.69–0.86）。内部没有人读出或改写这个权重（对象层；本轮 1 条 + 第一轮 6 条查询）。
6. **OpenReview 审稿讨论本轮仍没读到**：检索接口可用（定位了 8 个论坛号），但帖子接口与网页都被人机验证拦下，没有绕过。

---

## 1. 候选定义

- **现象（一句）**：图像与另一信息源（世界知识／提示里的错误预设／随附上下文文本）给出不同答案时，VLM 的输出系统性地倒向其中一方，且倒向哪一方随模型族、任务、问法而变。
- **根因主张（一句）**：取舍由语言解码器里一小撮部件（注意力头、或隐藏状态里的低秩方向）决定；A2 的归并假设是三类冲突共用（至少部分共用）同一个仲裁节点。
- **预期结论（供第 3 步蕴含检索用）**：
  - E1：「在 ≥2 个模型族上，从一类冲突定位出的头集／方向，对另外两类冲突的取舍有超出多次随机对照的因果效应。」
  - E2（反面）：「三类冲突各有独立部件；跨类迁移与随机对照分不开。」
  - E3：「基于该节点的修复在等义改写、选项顺序置换、留出数据下保持，且不伤另一侧（被要求答常识／跟文本时不变差）。」

---

## 2. 竞争者全景表

"对照"栏只写我在正文里核到的；"未见"指对 `random` 等关键词全文检索无相关命中，不等于作者一定没做（附录可能有）。

### 2.1 子类 (a)：图像 对 世界知识

| 工作 | 类型 | 模型族 | 干预类型 | 对照 | 评测稳健性 | 效果数字 | 自认局限（逐字） | 代码 | 层级 |
|---|---|---|---|---|---|---|---|---|---|
| Pixels vs Priors，[2505.17127](https://arxiv.org/abs/2505.17127)，EMNLP 2025 | 基准＋定位＋推理时转向 | LLaVA-NeXT、Qwen2-VL、Janus-Pro（3 族） | 推理时（激活转向） | 随机方向对照：未见（`random` 只命中数据构造） | 固定两种模板（this / most）；合成图；改写未测。自己在相关工作里批评编辑类方法 "often fail to generalize across paraphrased prompts or unseen contexts" | WK→CF 颜色 98.6–99.7%、大小 71.3–89.9%；CF→WK 颜色 78.2–86.4%、大小 33.5–70.37%（数字沿用第一轮 F） | "steering models from visual perception back to world knowledge is more difficult than the reverse" | github.com/rsinghlab/pixels_vs_priors（S） | F |
| When Seeing Overrides Knowing，[2507.13868](https://arxiv.org/abs/2507.13868)，ACL 2026 | 数据集＋定位＋推理时干预 | LLaVA-NeXT-7B、Gemma3-12B（2 族） | 推理时（按 logit lens 选 20 个 factual 头＋20 个 counterfactual 头，对其注意力做乘性调整，最后 token） | 有，但只一次抽取："we randomly select 100 attention heads and apply the same intervention for varying λ values"，结果"no substantial deviation from baseline"；另有 POPE 特异性检查与随机 patch 对照 | 单一数据集 WHOOPS-AHA!；改写未测 | factual accuracy 27%→74%（LLaVA-NeXT）；18%→83%（Gemma3） | "it does not capture the possible contributions of other components, such as MLP layers or visual encoders"；只做 late-fusion | francescortu/Seeing-Knowing（第一轮 F） | F |
| Vision-Default, Prior-Override，[2606.28273](https://arxiv.org/abs/2606.28273) v2（2026-11-05） | 定位（诊断） | Qwen2.5-VL 3B/7B、LLaVA-NeXT 7B（Mistral）、PaliGemma 3B/10B（Gemma 2）（3 族 5 模型） | 推理时（残差／逐头／MLP 激活修补＋零消融，均在最后 token） | **无随机头对照**。特异性靠：P/V 双向不对称；5 折重采样（19/25 次精确复现头集）；WHOOPS! 上重新发现（8/9、19/21、20/24、7/8、12/12）；换成"变图像、定提示"的对比后 "61% of visual-circuit-classified heads also classified under the primary contrast" | 两个数据集；两种对比；改写未测；WHOOPS! 每模型只剩 17–33 条 | 消融全部 promoting 头：先验作答翻转 68–96%，视觉作答 0.8–7.5%；WHOOPS! 上 38.1–59.3% 对 3.7–14.3%（LLaVA-NeXT p = .227 不显著）；图像对比下视觉作答翻转 1.8–40.6% | "the measured asymmetry may partly reflect how the two prompts are routed rather than arbitration between perception and memory alone"；"our claims concern this late-stage arbitration only"；"Larger models may develop different strategies" | github.com/nlietzow/vision-default-prior-override | F（主文通读） |
| Arbitration Failure, Not Perceptual Blindness，[2604.09364](https://arxiv.org/abs/2604.09364)（arXiv 版自标 under review；OpenReview 检索列表显示 COLM 2026，论坛页未能打开核实） | 定位＋推理时转向 | LLaVA-1.5/NeXT/OneVision、Qwen2-VL、InternVL2、BLIP-2、Janus-Pro 共 10 个，到 72B | 推理时（全序列残差修补；早层线性与 SAE 转向） | 随机方向对照：未见；报了改善／变差样本数（如 6:2、16:6） | 分析部分 8 种问法（第一轮 F）；转向收益未在换问法下复测；合成图 | 全序列修补翻转 60–84%，只换最后 token 0–1%；转向最多 +3.8% | "can improve visual grounding by up to +3.8% with degrading performance in some setups"；"This suggests that there are attribute-specific arbitration pathways rather than a single universal mechanism." | 未找到 | F |
| WhatIfVis / Seeing or Knowing?，[2607.26326](https://arxiv.org/abs/2607.26326) v2 | 基准＋定位＋修复（SFT；学到的一维向量） | Qwen2.5-VL 3B/7B、Qwen3.5 4B/9B、Gemma-4 E2B/E4B（3 族 6 模型） | 推理时（按层的注意力输出修补，最后 token；DAS 式一维向量）＋训练（SFT） | **有**：同层同倍率的随机初始化 rank-1 投影，3 个种子，得 5.9%（低于基线 14.7%），学到的向量比随机平均高 31.8 点 | 五个维度（spatial-temporal、color、count、size、weight）；双向 PairAcc；SFT 只在一个子集训、在留出子集上仍涨；改写与选项顺序：未核 | SFT 把宏平均 PairAcc "from 14.7 to 52.7"；基线在 weight、count 上 PairAcc 近零 | "Baseline models favor internal prior knowledge over image content for spatial-temporal, count, and weight, despite perceiving the counterfactual information."；局限段自述架构覆盖不全（原句未全摘） | 未核 | F |
| Selective Prior Calibration，[2607.29240](https://arxiv.org/abs/2607.29240) | 修复（解码层：从带图得分里减去无图的候选级先验偏好） | Qwen3-VL-32B、LLaVA 系（具体型号未核） | 推理时（输出分数层，不动内部） | 有：把候选先验换成开发集均值、别题先验、或候选间随机置换后，修复基本消失 | **候选顺序置换**、留出类别、外部冲突基准、无冲突基准都测了；CDH-Bench 共 300 例 | CF 准确率 +7.8 / +7.0 点；Qwen3-VL-32B：CF-Acc 0.665→0.743，CS-Acc 0.965→0.970 | "SPC requires a fixed candidate set, access to candidate-level probabilities, and model-specific paired CF–CS development data." | github.com/MiLab-HITSZ/2026ChenSPC | F |
| TACT，[2608.06938](https://arxiv.org/abs/2608.06938) | 修复（纯文本后训练，只动语言解码器） | Qwen3-VL-8B 为主（其余未核） | 训练 | 未核 | 四个基准上都涨（+12.6、+14.3、+17.0、+10.4）；改写与常识侧代价未核 | "TACT improves Accuracy from 66.8% to 80.4% and reduces prior-bias from 31.5% to 18.2%" | 未摘 | 未核 | F（只核了结果句） |
| In-Context Learning Can Help…，[2610.12942](https://arxiv.org/abs/2610.12942) | 便宜办法（视觉 in-context 示例） | 五个 VLM 族（含 Qwen3-VL 235B/32B） | 输入侧 | 设有 simple／no-prior 对照题 | 五项任务：counting（动物腿数）、color、shape、direction、spatial relation；先验一致样本基本不变 | 反事实样本 +27.2%（Qwen3-VL 235B）、+15.1%（32B）；五族 +9.7% 到 +30.3% | "in-context learning is limited when the underlying visual capability is weak or absent" | 未核 | A（摘要＋任务段） |
| ViSiP-Bench / MAPS，[2610.21902](https://arxiv.org/abs/2610.21902) | 基准＋修复（微调） | 24 个模型 | 训练 | — | 指出 "cross-model prior agreement falls below 80%, and over 15% of items can be answered correctly without any image"；rare-but-real 真实场景 | 数字未摘 | 未摘 | 未核 | A |
| Grounding on Request，[2610.33841](https://arxiv.org/abs/2610.33841) | 修复（只训两个新词的嵌入）＋测量（FLIP / STAY） | 3 个 VLM | 训练（仅嵌入） | — | 3 个既有基准＋自建 Ground-CF | 数字未摘 | 未摘 | 未核 | A |
| CounterCount，[2605.17826](https://arxiv.org/abs/2605.17826) v2（OpenReview 列为 ICLR 2027 投稿） | 基准＋弱修复（计数区域注意力放大） | 16 个模型；内部只到 Qwen、Gemma 两族 | 推理时 | — | MCQ 与开放式；选项顺序随机；用了标注框 | 平均 +3.3 点（每模型取 12 配置最优） | 见第一轮 04-C3 | 未核 | F（第一轮）；本轮只核了它与头级机制的关系：仅在相关工作里引 PvP、Ortu，未做头或方向分析 |
| VLMBias，[2505.23941](https://arxiv.org/abs/2505.23941)，ICLR 2026 | 基准 | 闭源五个＋开源若干 | 输入侧（去背景 +21.09）与提示 | — | 多种问法 | 见第一轮 04-C3 | 见第一轮 | 数据公开 | F（第一轮，未重读） |
| Diagnosing Knowledge Conflict in Multimodal Long-CoT，[2602.14518](https://arxiv.org/abs/2602.14518) | 定位（探针）＋推理时控制；**三类冲突同框** | R1-Onevision-7B、Ocean-R1-7B-Instruct、Llama-3.2V-11B-cot（推理型 VLM） | 推理时（探针引导的表征转向；VCD） | 未核 | 7,500+ 条长 CoT；三类冲突各自的客观冲突集（PhD-icc、PhD-ccs、TruthfulQA 改造） | 线性探针 AUC 93.2–98.8%；类型混淆：R1-Onevision 上 25.1% 的 VT 被判成 VP，Llama-3.2V 上 14.7% 的 VP 被判成 VT；PT 100% 分开 | "reinforcing the model’s implicit source preference under conflict is far easier than enforcing the opposite source" | "anonymous link" | F |

### 2.2 子类 (b)：图像 对 提示里的错误预设

| 工作 | 类型 | 模型族 | 干预类型 | 对照 | 评测稳健性 | 效果数字 | 自认局限（逐字） | 代码 | 层级 |
|---|---|---|---|---|---|---|---|---|---|
| Mechanisms of Prompt-Induced Hallucination，[2601.05201](https://arxiv.org/abs/2601.05201)，ACL 2026 | 定位＋推理时消融 | LLaVA-OneVision-7B、Qwen2-VL-7B、Janus-Pro-7B（3 族；前两者共用 Qwen2 语言模型） | 推理时（逐头 knockout 后取 top-m 联合消融）；头集中在语言模型最早层 | 有："we compare PIH heads to an equal number of randomly selected heads from the same layers in which the PIH heads reside"（抽取次数未核） | 计数→颜色跨任务成立；改写未测 | prompt match 42.58 / 56.51 / 64.10 → 1.42 / 3.22 / 10.19；随机对照 37.80 / 54.60 / 58.30（第一轮 05-M1 F） | "the specific PIH heads identified here and the effects of their ablation may not generalize directly to substantially larger models" | 脚注有（仓库名截断） | F |
| Causal Evidence for Attention Head Imbalance…（MACI），[2605.19250](https://arxiv.org/abs/2605.19250) | 定位＋推理时条件干预 | Qwen2.5-VL-7B、Qwen3-VL-8B、InternVL3-8B、LLaVA-NeXT-7B、LLaVA-7B（3 族 5 模型） | 推理时（path patching 定出 driving／resisting 两组头；探针判冲突后才零消融 driving 头） | **有**：等量随机头消融，5 个种子取平均，结果贴近 Base | 500 条留出；object→attribute／relation 跨类型；MMMC→SCI-SemanticConflict 零样本；同时报无冲突准确率；改写未测 | Qwen2.5-VL-7B：幻觉率 28.83→24.10，无冲突准确率 78.18→77.73；SCI 平均 −7.9 点；三个模型无冲突准确率掉 ≤2 点 | "on InternVL3 and LLaVA, larger accuracy drops accompany larger hallucination reductions. These drops may reflect residual detector errors or driving heads being less conflict-specific in these models."；自称 proof-of-concept | "upon acceptance" | F |
| Robust MLLMs Against Modality Conflict（MMMC），[2507.07151](https://arxiv.org/abs/2507.07151) | 基准＋修复（提示／SFT／强化学习，LoRA） | InstructBLIP、LLaVA-1.5、LLaVA-NeXT、Qwen2-VL（7B；另 2B） | 训练 | — | 自述强化学习最好、SFT 稳定；训练超过 1000 条会 collapse | 数字未摘 | 未摘 | 数据在 HF | F（只核了方法与模型段） |
| CAER，[2607.28991](https://arxiv.org/abs/2607.28991) | 修复（冲突检测＋双前缀专家） | 多个开源 MLLM | 训练（外挂模块） | — | MMMC＋自建 AgriConflict | 未摘 | 未摘 | 未核 | A |
| HalluScope / HalluVL-DPO，[2604.21911](https://arxiv.org/abs/2604.21911) | 基准＋微调 | 见第一轮 04-C4 | 训练 | — | — | 未摘 | — | — | F（第一轮，未重读） |

### 2.3 子类 (c)：图像 对 上下文文本

| 工作 | 类型 | 模型族 | 干预类型 | 对照 | 评测稳健性 | 效果数字 | 自认局限（逐字） | 代码 | 层级 |
|---|---|---|---|---|---|---|---|---|---|
| How Do VLMs Process Conflicting Information…，[2507.01790](https://arxiv.org/abs/2507.01790) | 定位＋推理时头缩放 | 行为与聚类 4 个模型；**头干预只在 Qwen2.5-VL** | 推理时（单头输出乘 α = 10，最后 token） | 随机头对照：未见 | 在 Pascal VOC 上找头，在 CIFAR-10/100、ImageNet100、CUB-Color 上测 | router 头 L11H14：目标为图像时 +1.4 到 +9.9；目标为图注时 +6.3、−0.2、−0.8、+1.6、−4.9。**图像提升头 L19H26：图像侧 +3.7 到 +12.9，图注侧 −31.0、−7.7、−9.4、−18.6、−34.6**（Table 1） | "it is not guaranteed that those heads can further generalize to other datasets"；"An interesting future work could explore the interactions among attention heads" | github.com/ethahtz/vlm_conflicting_info_processing | F |
| Evaluating and Steering Modality Preferences，[2505.20977](https://arxiv.org/abs/2505.20977)，ICML 2026 | 基准（MC²）＋推理时转向 | Qwen2-VL-7B、Qwen2.5-VL-7B、LLaVA-OneVision-7B、InternVL3-8B（3 族） | 推理时（两种指令下最后 token 隐状态之差作方向） | 随机方向对照：未见 | MC² 八类任务；下游 PhD-icc、MathVista、TallyQA、VSR、AmbigCaps；改写与选项顺序未测 | 见第一轮 04-C5 | 局限段只谈数据筛选（第一轮） | EchoDreamer/Modality-Preference（S） | F |
| Instruction Anchor，[2602.03677](https://arxiv.org/abs/2602.03677) v2 | 定位＋推理时头阻断／放大 | Qwen2.5-VL-7B、InternVL3-8B（2 族）；附录称推广到更大的稠密模型与 MoE 模型 | 推理时（注意力敲除定通路；逐头阻断与放大） | **有**：等量随机头；另设"只动 modality-shared heads"对照（阻断无效） | 基于 MC² 加模态指令；附录称测了不同指令风格与开放式生成；通用能力表（TextVQA、Flickr30k、MMLU、IFEval，仅 Qwen2.5-VL-7B） | 阻断 Top-40 头（约 5%）使文本跟随 MFR 掉约 60%；放大 Top-30 头使失败样本 MFR 绝对涨约 60% | 过度放大（α = 18）会损害（原句未全摘） | "upon acceptance" | F |
| MLLMs Get It Right, Then Get It Wrong（CALRD），[2606.17953](https://arxiv.org/abs/2606.17953) | 定位（逐层 logit 轨迹）＋推理时解码修复 | InstructBLIP-7B、LLaVA-1.5-7B、LLaVA-1.6-7B、Qwen2.5-VL-7B、Qwen3-VL-8B | 推理时（检测到中间层的视觉预测被晚层压掉就恢复） | 与 VCD、DeCo、DoLa、OPERA 比 | PhD-icc 与自建 Conflict-VQA；另报 POPE、CHAIR | 冲突基准最多 +9.4 点；"85% of failures shift toward text, while 89% of successes shift toward vision" | 未来工作：规模与预训练数据（原句未全摘） | 未核 | F |
| Mechanistic Analysis and Inference-Time Control of Modality Conflict，ICML 2026 页面（[OpenReview 1XzMBbB1Rn](https://openreview.net/forum?id=1XzMBbB1Rn)） | 定位＋推理时偏置向量 | LLaVA-v1.6、Qwen2.5-VL | 推理时（commitment zone 的 MLP 替换；无状态 offset 向量） | 未核 | CLEVR-CONFLICT，称推广到 COCO | 未核 | 页面摘要称 MLP 是"context-dependent amplifier rather than a standalone switch"（转述，非逐字核对） | 未核 | A（只有会议页面的摘要转述） |
| Prior Directions，[2607.26913](https://arxiv.org/abs/2607.26913) v2 | 定位（低秩方向）＋推理时编辑 | InternVL3.5-8B、MiniCPM-V-4.5、Qwen3-VL-8B、Holo2-8B（4 族） | 推理时（rank-32 子空间编辑） | **最严**：rank-matched 随机子空间；打乱配对重拟合（20 个置换种子）；对齐分量与正交残差分别测 | GUI 定位任务（ScreenSpot-Pro 改造），过期文字线索 对 当前截图；无关文字作对照 | 几何上正确配对在全部 15 个设定都更好；但修复数 "matched and Pairing-Permuted edits restore 60/66 and 59/66"；正交残差 20/66；随机 6–7/66 | "the construction that best identifies recurrent representation change need not be uniquely more behaviorally effective" | github.com/phare111/prior-directions | F |
| MoGround，[2609.33431](https://arxiv.org/abs/2609.33431) | 基准＋修复（**权重空间向量**，由 LoRA 微调得到） | 7 个开源 VLM | 静态权重（训练得到） | — | 人写的留出子集 MoGround-Human；Retrieved 子集；"transfers to pools it never saw"；改写：未核 | "a weight-space robustness vector reduces distraction on all seven models by 29% to 51%, at a cost of only 0.1 average points of accuracy on standard multimodal tasks" | 未摘 | 未核 | F（摘要、贡献、数据校验段） |
| Words or Vision，[2503.02199](https://arxiv.org/abs/2503.02199)，CVPR 2025 | 基准＋修复（指令；SFT＋文本增广） | 10 个 VLM | 训练／提示 | — | — | 指令 16.8%→14.2%（第一轮） | — | — | F（第一轮，未重读） |
| 其他修复：Modality Interference [2505.19616](https://arxiv.org/abs/2505.19616)（扰动式微调）；AMPS [2602.12533](https://arxiv.org/abs/2602.12533)（逐样本调转向强度，摘要自述"strong steering can impair standard inference and increase error rates"）；MaLoRA [2510.26721](https://arxiv.org/abs/2510.26721)（注意力 key 空间错位，门控 LoRA）；Option-Redirecting Bias [2609.32489](https://arxiv.org/abs/2609.32489)（ACM MM '26，推理时转向） | 修复 | — | 训练／推理时 | — | — | 未摘 | — | — | A |

### 2.4 行为层"线索权重"

| 工作 | 做了什么 | 内部？ | 层级 |
|---|---|---|---|
| Biased Bayesian Observers，[2610.19407](https://arxiv.org/abs/2610.19407) | ŝ_J = π0 + β_T·e_T + β_V·e_V，"the prior enters with unit weight and no intercept"；Qwen2.5-VL、Qwen3.5、Gemma3、GLM-4.6V；OOD R² 0.69–0.86；线性合并优于"取更自信的那一路" | 否，明说 probe 是行为测量 | F |
| Where Should Language Sit…，[2609.07474](https://arxiv.org/abs/2609.07474) | cue-conflict 法量理想观察者斜率；39–78% 的回答直接抄文本中点 | 否 | F（第一轮 06，未重读） |
| When Modalities Conflict，[2511.02243](https://arxiv.org/abs/2511.02243) | 相对不确定度与 balance point；logit lens 逐层振荡（2 族，相关） | 仅 logit lens | F（第一轮 06，未重读） |
| Same Semantics, Different Outcome，[2609.00550](https://arxiv.org/abs/2609.00550) | 同一段与参数知识相矛盾的证据，分别以文本、渲染成图像、两者并给三种形式提供；13 个 MLLM、两个数据集。摘要：图像形式比文本形式更容易让模型放弃参数知识；两者并给时偏哪边 "essentially arbitrary, varying with input order, model, and dataset" | 否（行为） | A |
| When Irrelevant Text Matters，[2608.19208](https://arxiv.org/abs/2608.19208) | 无关文本下的决策 margin 近似是无文本 margin 的仿射变换 | 否（行为） | A |
| Which Source Wins?，[2608.17205](https://arxiv.org/abs/2608.17205)；Mixed Signals，[2504.08974](https://arxiv.org/abs/2504.08974)；Sensory PID，[2606.00959](https://arxiv.org/abs/2606.00959)；Omni 模型模态偏好，[2604.16902](https://arxiv.org/abs/2604.16902)（逐层探针） | 行为或探针 | 否／探针 | A–S |

### 2.5 擦线成员

| 工作 | 要点 | 层级 |
|---|---|---|
| 用户施压：MM-SY [2410.11302](https://arxiv.org/abs/2410.11302)、GasEraser [2504.09456](https://arxiv.org/abs/2504.09456)、LQCD [2408.11261](https://arxiv.org/abs/2408.11261)、Pi et al.（EMNLP 2025，"Pointing to a Llama and Call it a Camel"） | 本轮没有检到新的 ≥2 族内部定位（对象层；专门查询 1 条 S6-11，另第一轮 3 条）。状态同第一轮 04-C6 | F（第一轮）／S |
| 图中文字，语言端：Where Vision Becomes Text，[2602.22918](https://arxiv.org/abs/2602.22918) | Qwen3-VL、Phi-4、InternVL3.5 共 5 个模型，因果干预定出 OCR 信号进入语言流的层带（DeepStack 约 50% 深度，单阶段投影 6–25%）；"OCR removal can improve counting performance (up to +6.9pp)"。定位的是"读字"通路，不是"字 对 图"冲突的取舍 | A |
| 图中品牌标识 对 文章内容：Brand-as-Memory，[2607.03365](https://arxiv.org/abs/2607.03365) | 7 个 VLM 行为；19–21 层因果形成，第二个族复现；"it overrides content (∼1.8×) as a signal-magnitude effect within a shared pathway, not a privileged route"；转向后 −41% | F（摘要、Table 2、局限） |
| Embedded Stroop，[2511.13400](https://arxiv.org/abs/2511.13400)；编码器侧排版回路（第一轮 04-C8） | 行为；编码器内 | A／F（第一轮） |

### 2.6 文本 LLM 的"上下文 对 参数知识"

| 工作 | 结论 | 层级 |
|---|---|---|
| PH3，[2402.18154](https://arxiv.org/abs/2402.18154)，Findings ACL 2024 | 中后层有作用相反的 memory heads 与 context heads；剪头后 "can flexibly control eight LMs to use internal memory (↑ 44.0%) or external context (↑ 38.5%)" | A（摘要句已核） |
| Controllable Context Sensitivity and the Knob Behind It，[2411.07404](https://arxiv.org/abs/2411.07404)，ICLR 2025 | 单层里的一维子空间编码"跟上下文还是跟先验"，同族内（微调版→instruct→base）通用；Llama-3.1、Mistral-v0.3、Gemma-2 | S（检索摘要；WhatIfVis 明说沿用其一维假设） |
| JUICE / Taming Knowledge Conflicts，[2503.10996](https://arxiv.org/abs/2503.10996) | "Surprisingly, half of the top-performing “memory heads” in substitution conflicts become “context heads” in coherent conflicts." | F |
| ParaConflict（Li et al. 2025），经 [2609.24238](https://arxiv.org/abs/2609.24238) 转述 | "“context heads” and “memory heads” can switch roles when the degree of conflict changes slightly"；后者在 31 个模型上复核 Yu et al. (2023) 的行为结论，称若干结论不能干净推广 | F（转述句）／原文 S |
| Where Knowledge Collides，[2601.09445](https://arxiv.org/abs/2601.09445) | "we find no evidence of a single universal circuit for handling knowledge conflict"；作者自注"although not conclusive" | F |
| ReDeEP [2410.11414](https://arxiv.org/abs/2410.11414)、Tighidet et al. [2410.05817](https://arxiv.org/abs/2410.05817) | RAG：注意力头抄外部上下文、后层 FFN 注入参数知识；知识来源可探 | S |

### 2.7 关键问题逐条对照

- （引用链口径：下文"被引清单"指 Semantic Scholar 返回的 7 篇邻居的 225 条被引。）
- **谁定位了什么、随机对照、换数据集是否稳定**：见 2.1–2.3 的"对照"与"评测稳健性"两栏。带随机对照的：PIH（同层随机头）、2605.19250（5 种子）、Instruction Anchor（随机头＋shared 头）、WhatIfVis（随机 rank-1，3 种子）、Prior Directions（随机子空间＋打乱配对 20 种子）、Ortu（单次 100 头）。未见随机对照的：PvP、2606.28273、2604.09364、Hua、ModPref。换数据集后：2606.28273 的头集在 WHOOPS! 上重新发现 8/9–12/12 但翻转率掉到 38.1–59.3%；Hua 的 router 头在 CUB-Color 上失效；PIH 计数→颜色成立；2605.19250 跨类型与跨基准成立。**换提示模板后定位是否稳定：只有 2604.09364（8 问法，分析层）与 Instruction Anchor（指令风格，附录，我未核数字）碰过。**
- **修了一侧是否伤另一侧**：有四处实测。Hua 的图像提升头让图注侧掉 7.7–34.6 点（F）；MACI 在 InternVL3 与 LLaVA 上无冲突准确率掉得更多（F，数字未摘）；2604.09364 的转向有样本变差（F）；SPC 摘要自述"Suppressing this prior indiscriminately can repair CF errors, but may also disrupt correct answers on matched commonsense (CS) images, where the same prior is helpful"（A，摘要原句）。MM-SY 的 DPO 把纠错接受率压到 2%（第一轮 F）。PvP、Ortu、2606.28273 的干预本身就是双向的，不以"答对"为目标。
- **机制有没有搬到"先验压图"的计数设定**：部分搬了。WhatIfVis 含 count 与 weight 两个基线偏先验的维度，做了层级修补与一维向量（F）；其重建探针用了 VLMs-are-Biased 的动物子集，三个模型在该子集上近零（F）。头级的（PvP 方向、2606.28273 的 promoting 头、Ortu 的 factual 头）拿到 VLMBias／CounterCount 上：未检到（对象层；本轮 3 条查询 S6-2、S6-6、补充 1 条，另第一轮约 5 条）。
- **行为层权重有没有人在内部读出或改写**：未检到（对象层；本轮 1 条专门查询，第一轮 06 路 6 条）。2610.19407 的作者与 PvP、PIH、2606.28273 的作者重合（Rudman），该文把 Hua、MaLoRA、PIH 归为"attention mechanism"、把 PvP、ModPref、2604.09364 归为"steering directions"，自己不做内部。
- **VLM 结论是否只是文本 LLM 结论的推论**：见 §4 的 C7。
- **作者留下的开口**：见 §5。

---

## 3. 各轴最高水位

| 轴 | 目前最好的是谁、做到什么 |
|---|---|
| 模型族数量与多样性（因果干预） | (a)：2606.28273，3 族 5 模型（Qwen2.5-VL／Mistral 骨干的 LLaVA-NeXT／Gemma 2 骨干的 PaliGemma），3B–10B；WhatIfVis，3 族 6 模型（Qwen2.5-VL、Qwen3.5、Gemma-4）；2604.09364 的全序列修补覆盖 9 个模型（是否含 26B／72B 本轮未核）。(b)：2605.19250，3 族 5 模型。(c)：ModPref 3 族 4 模型（转向）；Instruction Anchor 2 族（头级）；CALRD 5 模型（解码层）。头级因果证据全部 ≤约 13B。闭源模型只有行为。 |
| 因果对照的严格程度 | 单篇最严：Prior Directions（随机子空间＋打乱配对 20 种子＋对齐／正交分解）。头级里最严：2605.19250（path patching 双向分组＋5 种子随机头＋跨类型＋跨基准）与 Instruction Anchor（随机头＋shared 头＋通用能力表）。方法学标尺：2610.13111 用 250 组层匹配随机头集的分布。**冲突类论文里没有一篇同时做到：多次层匹配随机抽取的分布、提示类型 × 图像类型的 2×2、最后 token 与全序列两种干预位置并报。** |
| 评测稳健性 | 输出层修法里：SPC（候选顺序置换＋留出类别＋外部基准＋无冲突基准）。内部干预里：2605.19250（留出 500＋跨类型＋零样本跨基准＋无冲突准确率）；2606.28273（第二数据集重发现＋第二种对比＋5 折）；2604.09364（8 问法，仅分析）。**内部干预或静态权重修复在等义改写＋选项顺序置换下的收益：没有一篇报告**（对象层与结论层；本轮专门查询 2 条 S6-3、S4-3，第一轮 4 条）。 |
| 效果量 | 翻转型（构造对比上）：PvP 98.6–99.7%；2606.28273 68–96%；PIH 把 prompt match 压到 1.42–10.19；Instruction Anchor 恢复约 60%。答对型：WhatIfVis SFT 的 PairAcc 14.7→52.7；TACT 66.8→80.4；SPC +7.8／+7.0；CALRD 最多 +9.4；MACI 约 −4.7 点幻觉率（Qwen2.5-VL）；MoGround −29% 到 −51% 干扰率；2604.09364 +3.8；CounterCount +3.3。便宜办法：视觉 ICL +9.7 到 +30.3；VLMBias 去背景 +21.09。 |
| 任务与数据广度 | 三类冲突同框：2602.14518（探针级，推理型 VLM）。(a) 内多维度：WhatIfVis 五维（含 count、weight）；ViSiP-Bench 六类先验、24 个模型、真实罕见场景。(c)：MC² 八类任务。(b)：MMMC（object／attribute／relation）。自然图像：ViSiP、SCAM、COCO 派生集；机制论文多数仍是合成反事实图。 |
| 是否免训练 | 免训练推理时：头消融／缩放、转向、CALRD、SPC、MACI。静态权重：MoGround 的权重空间向量（需 LoRA 训练得到）。**免训练的静态权重编辑（Nullu 式零空间投影）用在冲突仲裁上：未检到**（对象层；2 条查询 S6-3、S2-3）。 |
| 是否给出统一解释 | 行为层：2610.19407 一条线性合并律同时容纳先验、文本、视觉。表征层：2602.14518"三类冲突类型线性可分"；WhatIfVis"vision-versus-prior 是一维旋钮"（只 a 类）；ModPref"模态偏好方向"（只 c 类）。部件层：2606.28273"视觉默认、先验靠稀疏头覆盖"（只 a 类）。**跨三类的部件级统一或否定：未检到。** |

---

## 4. 竞争解释与事实约束

### 4.1 事实约束（实测否定或收窄某条路）

- **F1 发现的头集，其转向效果可能与随机头集分不开。** 2610.13111（自标 ICLR 2027，未核实）在 Qwen3-VL-8B 上做 12 套发现方式 × 层匹配随机对照："no discovered head-set steers better than its layer-matched random sets (rank p ≥ 0.14)"；单次随机抽取的效果从 −0.34 到 +0.84，"so the single-draw baselines used in prior work cannot place a head-set within this distribution"；必要性检验则能分开。对象是视觉路由头，不是冲突头。（F）含义（推导）：Ortu 的单次 100 头对照、2605.19250 的 5 种子对照，按这个标尺都偏少；2606.28273 没有随机头对照。
- **F2 "最能刻画表征变化的方向"不等于"唯一有效的干预方向"。** Prior Directions：正确配对 60/66，打乱配对 59/66，四个模型。（F）
- **F3 推向图像的干预会伤文本／常识一侧。** Hua Table 1（图注侧 −7.7 到 −34.6）；MACI 在两个模型上；SPC 摘要；AMPS 摘要；2604.09364。（F／A，见 2.7）
- **F4 最后 token 与全序列两种干预位置结论相反且未对齐。** 2604.09364：只换最后 token 翻转 0–1%，全序列 60–84%（第一轮 F）；其余头级论文都在最后 token 上做并有效。2606.28273 自己限定"our claims concern this late-stage arbitration only"。（F）
- **F5 (b) 类的层位两篇不一致。** PIH："localized primarily to early layers of the language model"（第一轮 F）；2605.19250："Both groups are concentrated in middle-to-deep layers"（F）。任务不同（"Describe the N+k objects" 对 MMMC 错误前提问答）、方法不同（逐头 knockout 对 path patching）、模型只部分重合。未在同协议下对过。
- **F6 "先验压图"一侧，视觉示例就能修掉一大块。** 2610.12942：五族 +9.7 到 +30.3，含动物腿计数（A）。与 VLMBias"few-shot 无效"（第一轮 F）方向相反；两者的示例构造、模型、题集是否可比，我没有摊开核对，**不登记为矛盾**。
- **F7 文本 LLM 上，头的角色随冲突类型翻转；找不到通用冲突回路。** JUICE、ParaConflict、2601.09445（F，见 2.6）。对 VLM 是类比档。
- **F8 换提示指令控制取舍，不稳定。** WhatIfVis："vanilla models … show unstable visual context sensitivity"（F，摘要句）；Words or Vision 16.8%→14.2%（第一轮 F）；2609.07474"the prompt is part of the stimulus"（第一轮 F）。

### 4.2 竞争解释（同一现象的其他已发表解释）

- **C1 稀疏头仲裁**：2606.28273、Ortu、Hua、PIH、2605.19250、Instruction Anchor。
- **C2 没有专门的仲裁器，是证据强度的线性合并**：2610.19407（线性合并优于"取更自信的一路"）。同向：Brand-as-Memory"a signal-magnitude effect within a shared pathway, not a privileged route"。
- **C3 取决于单模态能力／不确定度**：MoGround"distraction scales inversely with grounding strength (r = −0.90)"（A，摘要）；2511.02243 的相对不确定度与 balance point（第一轮 F）。
- **C4 分布式而非稀疏**：2604.09364，因果效应几乎全在图像 token 上、最后 token 无效；并称"attribute-specific arbitration pathways rather than a single universal mechanism"。
- **C5 检测与解决是两个机制**：2509.02805（LLaVA-OV-7B 单模型，探针＋注意力图样）："These findings support the hypothesis that detection and resolution are functionally distinct mechanisms."（A）
- **C6 晚层覆盖**：CALRD，中间层先形成视觉预测、晚层被文本压掉（5 模型，logit 轨迹，相关＋解码层修复）；MLP 作放大器（2606.28273；ICML 2026 He et al.，A）。
- **C7 是文本 LLM"上下文 对 记忆"机制的延伸**：Ortu："The competition between parametric knowledge and conflicting external evidence, identified in text-only LLMs … extends to the multimodal setting"；2606.28273："Our setting is the multimodal analogue of context-memory conflict in language models"，同时声明差异："Unlike the relatively balanced trade-offs observed for parametric-versus-retrieval conflict in unimodal language models (Jin et al., 2024), we find a strongly asymmetric structure in VLMs"；WhatIfVis 直接沿用 Minder 的一维假设；PIH 以两模型共用 Qwen2 骨干且头编号重合为据，认为头来自语言模型。**但没有一篇在同骨干的纯文本 LLM 上跑同一干预**（对象层；本轮 2 条查询 S1-4、S3-2；第一轮 05 路已注明 PIH 未做）。所以"VLM 结论是文本结论的推论"目前是类比档，既未证实也未排除；已知的一处不一致是对称性（文本上较平衡，VLM 上强不对称）。
- **C8 训练数据／先验强度**：Words or Vision 的数据失衡论证（第一轮）；TACT 的"low-frequency factual scenarios"（F，摘要句）；ViSiP 指出各模型的先验本身一致率不到 80%（A）。

### 4.3 专答：三类冲突是否共用同一个仲裁节点

**直接检验（同一模型上，把一类冲突定位出的头或方向拿到另一类冲突上测因果效应，并与随机对照比）：未检到**（对象层与结论层；专门查询 S6-1、S6-4、S3-1、S3-4 共 4 条 WebSearch，arXiv API 3 条，7 篇邻居的被引清单共 225 条逐条看过标题；其中最近的 2606.28273 只有 4 条被引，都不是跨类检验）。把三类并成一簇仍然只是我们的归并。

现有的间接证据，按"偏向共用／偏向不共用／不能判"分：

| 证据 | 指向 | 级别 | 说明 |
|---|---|---|---|
| 2602.14518：同一模型上 VP、VT、PT 三类冲突的类型信号线性可分；PT 100% 分开；VT 与 VP 互相混淆 25.1%／14.7%，作者称"leading to partially shared representations" | 不共用（PT 对其余）；部分重叠（VT 对 VP） | 相关（探针），3 个推理型 VLM | 探针读的是"冲突类型"，不是"取舍部件"；类型可分不蕴含仲裁部件不同。且 VP 用反常识图、VT 用误导文本，输入分布本身不同 |
| 层位：(a) 在后半层（2606.28273：52–100% 深度；WhatIfVis：mid-to-upper）；(c) 在中深层（Hua 的 L11–L19；Instruction Anchor 的深层注意力）；(b) PIH 在最早层、2605.19250 在中深层 | 若 PIH 成立，(b) 与 (a)(c) 不共用；若 2605.19250 成立，三者层位重叠 | 推导 | 层位重叠不等于部件共用；各文的读数、位置、对比构造都不同 |
| 2605.19250 明说其设定不同于 "visual-illusion or language-prior conflict [7] or context-parametric conflict [25]"，没有测那两类 | 不能判 | — | 作者把三者当不同对象 |
| 2606.28273 把 Hua（image-versus-caption）与 Ortu（factual-versus-counterfactual）的头并称"candidate routing heads"，但没有比较头集 | 不能判 | — | 同一作者组还做了 PIH（b 类）与 2610.19407（行为层），三套头集都在他们手里，未见交叉 |
| 2606.28273：同为 (a) 类的两种对比（变提示／变图像）头集重合 61% | 类内部分重合 | 因果，3 族 | 是类内，不是跨类；也说明换对比方式就有约四成不重合 |
| 类内迁移成立：PIH 计数→颜色；2605.19250 object→attribute／relation、MMMC→SCI；Hua 跨 4 个数据集（CUB-Color 例外） | 类内共用 | 因果 | 不涉及跨类 |
| Instruction Anchor：只阻断 modality-shared heads 无效，要 modality-specific heads | (c) 类内两个方向不共用关键头 | 因果，带随机对照 | — |
| 2610.19407：一条线性合并律同时拟合先验、文本、视觉 | 行为上可用同一公式 | 行为 | 作者自认"we extensively manipulate the supplied evidence but do not systematically manipulate prior beliefs independently of that evidence" |
| 2609.00550：同一语义的反参数证据，放在图像里比放在文本里更容易被采信；图文并给时偏向随输入顺序、模型、数据集而变 | 行为上"图像 对 先验"与"文本 对 先验"的取舍不等价 | 行为，13 个模型 | 只读了摘要；无内部测量 |
| 文本 LLM：JUICE（半数 top memory heads 换冲突类型后变 context heads）、ParaConflict、2601.09445（无通用回路） | 不共用 | 类比 | 文本模型、小模型为主 |
| 音频 LLM：2606.18924，"while text and audio rely on functionally distinct pathways, they ultimately converge into a shared semantic space in late layers"；Qwen 上两路数据子回路 IoU ≈ 0.01 | 早段不共用、晚段共享空间 | 类比 | 两个音频模型 |
| Brand-as-Memory：来源先验与内容证据走"shared pathway" | 共用通路、靠幅度取胜 | 因果（单域，两族） | 新闻可信度单一任务 |
| 2604.09364：颜色与大小的交叉层排序不同，"attribute-specific arbitration pathways rather than a single universal mechanism" | 连 (a) 类内部都未必单一 | 相关（逐层 logit） | 作者自注大小题有关键词匹配嫌疑 |

小结（推导）：没有人证明共用，也没有人证明不共用。已有间接证据更像"类内可迁移、跨类至多部分重叠"，其中最硬的反向材料来自文本 LLM（类比档）与探针（相关档），都不是 VLM 上的部件级因果检验。

---

## 5. 作者留下的开口（逐字）

- 2606.28273（F）："A full 2 × 2 design crossing prompt type with image type, testing whether the classified heads show a super-additive effect in conflict cases beyond additive prompt-only and image-only effects, would isolate the arbitration component more directly. We see this as the natural next step for this line of work."
- 2606.28273（F）："the measured asymmetry may partly reflect how the two prompts are routed rather than arbitration between perception and memory alone"；"suggesting that future control methods may need to be architecture-specific"；"Larger models may develop different strategies as their capacity and memorized knowledge increase."
- 2505.17127（F）："steering models from visual perception back to world knowledge is more difficult than the reverse, suggesting an asymmetry ... Understanding this distinction further remains an open direction for future work."（后半句沿用第一轮核对）
- 2507.13868（F）："it does not capture the possible contributions of other components, such as MLP layers or visual encoders. Extending this framework to broader architectural elements is a promising direction."
- 2507.01790（F）："it is not guaranteed that those heads can further generalize to other datasets"；"An interesting future work could explore the interactions among attention heads (i.e. circuit analysis)"
- 2601.05201（F）："the specific PIH heads identified here and the effects of their ablation may not generalize directly to substantially larger models"
- 2605.19250（F）："These drops may reflect residual detector errors or driving heads being less conflict-specific in these models."
- 2604.09364（F）："This suggests that there are attribute-specific arbitration pathways rather than a single universal mechanism."
- 2610.19407（F）："the modality weights βT and βV are fitted empirically rather than derived from a normative account"；"we extensively manipulate the supplied evidence but do not systematically manipulate prior beliefs independently of that evidence"
- 2601.09445（F，文本 LLM）："An in-depth analysis of the distinct circuits within language models and their roles in shaping the final prediction … is left to future work."（省略号处为原文从句）
- 2607.29240（F）："SPC requires a fixed candidate set, access to candidate-level probabilities, and model-specific paired CF–CS development data."
- 2610.12942（A）："in-context learning is limited when the underlying visual capability is weak or absent"
- 2602.14518（F）："reinforcing the model’s implicit source preference under conflict is far easier than enforcing the opposite source"（作者把它当发现，对修复方是开口：反向控制仍难）

---

## 6. 三列表

| 先例支持 | 事实约束与竞争解释 | 谁会因此改做法 |
|---|---|---|
| 三个子类各自都有 ≥3 族的头级或方向级因果证据：(a) 2606.28273、WhatIfVis、PvP、Ortu；(b) PIH、2605.19250；(c) ModPref、Instruction Anchor（2 族）、Prior Directions（4 族） | F1 随机头集对照不足；F2 方向识别不等于干预有效 | 做头级定位的作者：对照步骤从"单次随机抽取"改为"多组层匹配随机分布"。依据是 2610.13111 已把它写成报告规范；冲突线尚无人照做 |
| 类内迁移已多处成立（PIH、2605.19250、Hua、2606.28273 的 WHOOPS!） | 跨类未测；文本 LLM 上头的角色随冲突类型翻转（F7）；2602.14518 类型可分 | 做冲突机制的三个组（Rudman／Golovanevsky 线、Ortu 线、Zhang Yu 线）：若跨类共用成立，"每类冲突各发现一遍"的流程可合并；若不成立，现有"一组头管冲突"的表述要按类限定。这是推导，没有找到任何一方表态 |
| "先验压图"设定已有层级机制与多种修法（WhatIfVis、SPC、TACT、ICL） | F6 视觉示例即可修掉一大块；C3 取决于单模态能力 | 做修复的人：基线表里要加视觉 ICL 示例与 SPC。依据是两文都报告了在同类题上的两位数或接近两位数收益 |
| 双侧代价已有人量（Hua Table 1、MACI、SPC 的 CS-Acc、MoGround 的 −0.1） | F3 推向图像会伤另一侧 | 基准作者：FLIP／STAY（2610.33841）、PairAcc（WhatIfVis）、CF-Acc／CS-Acc（CDH-Bench）这类双侧指标已在出现 |
| 行为层线性合并律 | C2 无专门仲裁器的读法 | 未找到（没有检到有人据此改内部分析或训练流程） |
| 推理时修法多、训练式修法多 | 等义改写＋选项顺序下的内部修复收益无人报告 | 部署方或模型提供方是否因此改流程：未找到 |

---

## 7. 要构成足够贡献至少需要做到什么（只列门槛）

以"超过 §3 各轴水位"的形式写。每条后面括号里是现水位的出处。

1. **模型族**：≥3 个语言骨干无亲缘的族、≥5–6 个模型上做因果干预（2606.28273、WhatIfVis、2605.19250），并至少把因果干预推到一个 >13B 的模型（现有头级因果证据止于约 10–13B）。
2. **冲突类别**：在同一批模型、同一协议下覆盖 (a)(b)(c) 三类，并给出跨类迁移（一类定位的部件对另两类的因果效应）。现水位：三类同框只到探针（2602.14518），部件级全部单类。其中至少含一个"先验压过图"的设定（count／weight 类），且做到头级或方向级（现水位：WhatIfVis 的层级修补＋一维向量）。
3. **因果对照**：多组（2610.13111 用 250 组）层匹配随机头集或随机方向的分布对照；打乱配对的对照（Prior Directions）；必要性与充分性都报；提示类型 × 图像类型的 2×2（2606.28273 自列下一步）；最后 token 与全序列两种干预位置并报（2604.09364 对其余）。
4. **评测稳健性**：等义改写、选项顺序全排列（第一轮 04-C7 与 SPC 的水位）、留出类别与留出数据集（SPC、2605.19250、WhatIfVis）、自然图像（ViSiP 的 rare-but-real、SCAM）。修复收益在每个条件下分别报告。现水位：内部修复在改写＋顺序下无人报告。
5. **双侧代价**：同时报跟图一侧、取先验或跟文本一侧、无冲突任务（SPC 的 CS-Acc 0.965→0.970；MACI 的无冲突准确率；Instruction Anchor 的 TextVQA／MMLU／IFEval；MoGround 的 −0.1）。
6. **效果量**：在"先验压图"设定上，与下列已发表数字同表比较并超过内部干预类的现水位：CounterCount +3.3、2604.09364 +3.8（内部）；SPC +7.8／+7.0、TACT 66.8→80.4、WhatIfVis SFT 14.7→52.7、视觉 ICL +9.7 到 +30.3、去背景 +21.09（非内部或训练式）。
7. **统一解释**：若主张共用，需给部件重合度相对随机期望的统计＋跨类干预迁移；若主张不共用，需排除"读数位置、提示模板、对比构造不同造成的不重合"（2606.28273 类内两种对比就只重合 61%）。并与行为层线性合并律（2610.19407）对上：内部读出或改写对应于 β 或先验项的量。现水位：行为层公式与表征层"类型可分"之间没有东西。
8. **与文本 LLM 的关系**：在同骨干的纯文本 LLM 上跑同一干预（现无人做），否则结论可被读成"上下文 对 记忆"文献的推论（C7）。
9. **若贡献形态是静态权重修复**：现水位是 MoGround（训练得到的权重向量，7 个模型，−29% 到 −51%，代价 0.1 点）；免训练静态权重编辑在冲突仲裁上未检到先例。需补上 MoGround 未报或我未核到的改写与选项顺序稳健性。
10. **若贡献形态是测量或基准**：现水位是 ViSiP-Bench（24 模型，按模型动态诱导先验，三个连续指标）、WhatIfVis（双向 PairAcc）、CounterCount（区域标注，16 模型）、MC²（8 类任务）、MMMC、FLIP／STAY。新基准至少要同时覆盖三类冲突并保留这些基准各自已有的控制（无图可答比例、各模型先验不一致、双向成对指标）。

---

## 8. 七步检索日志

本候选共接受 **1 轮七步查重**（第一轮盘点不算查重）：WebSearch 31 条、Semantic Scholar 引用接口 8 条（7 条成功）、arXiv API 3 条、OpenReview 标题检索 12 条、参考文献清单扫描 3 篇。

### 第 6 步 对抗式检索（13 条 WebSearch）
1. VLM knowledge conflict types "shared" OR "distinct" mechanisms … unified analysis — 命中 2509.02805；无统一分析
2. VLM counterfactual counting bias fine-tuning fix VLMBias … steering attention heads — 无新修法
3. steering vectors head ablation VLM conflict "paraphrase" OR "rephrased" robustness — 无直接命中；Revis 2602.11824
4. multimodal knowledge conflict mechanistic interpretability 2026 … unified — Zhu et al. 2410.03659
5. "prior override" OR "vision-default" follow-up 2×2 design — 未见后续
6. VLM counting familiar objects counterfactual "prior" mechanistic … Visual CounterFact transfer — 2603.18523、2511.17699（计数回路，不涉先验冲突）
7. attention head localization VLM unstable … "random heads" comparable effect — **2610.13111**、2607.29412、2608.27417
8. mitigating visual knowledge conflict … hurts commonsense "trade-off" — CDH-Bench 2603.27982
9. Minder "controllable context sensitivity" knob — 2411.07404
10. same attention heads mediate different knowledge conflict types … JUICE — PH3
11. VLM sycophancy mechanism 2026 … "visual sycophancy" — 无新的内部工作
12. typographic attack VLM language decoder layers causal tracing — 仅编码器侧
13. VLMBias OR CounterCount … "fine-tuning" OR "LoRA" OR "steering" — 无
未命中：以"内部修复换问法后收益消失"为主结论的论文；把头级机制搬到 VLMBias／CounterCount 的论文。

### 第 5 步 引用链挖掘
- Semantic Scholar 被引：2507.13868（13 条）、2505.20977（29）、2604.09364（12）、2505.17127（39）、2601.05201（8）、2503.02199（120）、2606.28273（4），共 225 条逐条看标题。**2507.01790（Hua et al.）接口持续 429，被引未扫到。**
- 由此新增并取正文：2607.26913、2607.03365、2609.33431、2609.35272、2608.17205、2602.03677、2606.17953、2602.14518、2604.14888、2602.12533、2606.00959、2511.13400、2610.33841、2610.21902、2610.12942、2608.06938、2607.28991、2607.29240、2607.26326、2608.00035、2609.32763、2610.03445、2604.14363、2608.19208、2604.22038、2609.00550。2503.02199 的被引里另有若干只看了标题的近邻（记 S）：2509.23050、2511.22826、2607.27304、2609.26986、2601.22150、2604.17217、2608.03160。
- 参考文献清单：2606.28273（全）、2610.19407（全）、2604.09364（部分）。新增 2504.08974、ConflictVis、2604.16902、2510.26721、MINT。
- arXiv API 3 条：`ti:"knowledge conflict"`＋vision＋mechanis*；`abs:"modality conflict"`＋(heads｜steering｜patching)（新增 2609.32489）；VL＋conflict＋"attention heads"＋prior（新增 2606.27596，未取）。
- 1 条 WebSearch 核对三个标题。
- **OpenReview**：标题检索 12 条，定位到 Arbitration Failure（o3pc99Q3Mi，COLM 2026）、MM-SY（E2PFv7ad3p，ICLR 2025）、VLMBias（DG4S2OlGQA，ICLR 2026）、ModPref（sWW6lvti8X，ICML 2026）、MINT（zyu1tXMcbh，ICLR 2026 撤稿）、CounterCount（23ALDy4LjU，ICLR 2027 投稿）、PvP（04jgYbcdyE）、PIH（LMgqya1sxx）。读帖接口返回 403 ChallengeRequired，网页是人机验证页；5 次读取尝试全部失败，**审稿讨论一条都没读到**。

### 第 1 步 抽象阶梯（5 条 WebSearch）
模板："两个信息源冲突时由少数部件仲裁，且不同冲突类型共用部件"。搜了整类：文本 LLM 的 context-memory／inter-context／intra-memory、音频与视频 LLM、RAG、来源选择。
1. LM knowledge conflict "context-memory" "inter-context" "intra-memory" … unified circuit — 2601.09445、ParaConflict、JUICE、2609.24238
2. audio-language OR video-language modality conflict mechanism — 2604.02605、2606.18924、2605.19250
3. LLM "source selection" … single "arbitration" direction — 2410.05817
4. "context heads" "memory heads" VLM … inherit text LLM — 无直接检验
5. RAG faithfulness … "copying heads" "knowledge FFNs" — ReDeEP 等
未命中：指令 对 上下文 对 参数知识的三层内部机制。

### 第 2 步 方法论单独搜（3 条 WebSearch）
1. steering vectors unreliable "random direction" baseline — 2407.12404、2505.22637、2602.17881
2. head ablation "hydra effect" OR "self-repair" …; "does localization inform editing" — 2307.15771、2402.15390（后半未命中）
3. Nullu HalluSpace weight editing limitations; VIGIL; DARE — 只命中 Nullu 2412.13817；**VIGIL、DARE 在 VLM 冲突语境下未检到**
另：第 6 步的第 7 条实际命中方法论文 2610.13111。SAE、transcoder 的已知局限本轮未单独搜。

### 第 3 步 蕴含检索（5 条 WebSearch）
拿 §1 的 E1–E3 去找原句。
1. "heads identified" one conflict type "transfer" another conflict … — 无跨类迁移检验
2. VLM image treated as context "same mechanism" … inherited from language model — 无直接检验；ICML 2026 He et al.
3. "MACI" modality conflict conditional intervention — 2605.19250
4. sycophancy typographic prompt-injection "same direction" OR "shared subspace" — 无统一解释
5. VLM cue combination weights "internal" representation probe — 无（命中 2605.08200、2603.29676，均不是）
结论层被占的情况：E1、E2 未见原句；E3 未见。最接近的原句是 2602.14518 的"different conflict types are explicitly encoded as linearly separable features rather than entangled"（探针层，非部件层）。

### 第 4 步 同义术语枚举（4 条 WebSearch）
词表：knowledge conflict／cross-modality (parametric) conflict／modality conflict／visual-textual conflict／perception-knowledge conflict／vision-knowledge conflict／counterfactual image／commonsense-driven hallucination／language prior／unimodal bias／text dominance／text-centric bias／modality preference／modality bias／modality following／modality interference／modality distraction／blind faith in text／visual lock-in／visual revision／false premise／false presupposition／leading question／anchoring／prompt-induced hallucination／sycophancy／gaslighting／typographic attack／image-embedded prompt／visual prompt injection／Stroop／cue conflict／cue combination／context sensitivity／context-memory conflict／RAG faithfulness。
1. "false premise" OR "false presupposition" OR "leading question" — 2605.19250、2605.24024
2. "language prior" OR "unimodal bias" OR "text dominance" — 2410.04780、2605.24024
3. "modality interference" OR "modality distraction" OR "misleading context" … weight-space vector — 2505.19616、2507.07151
4. "visual prompt injection" OR "image-embedded text" OR "typographic" … "OCR heads" — 2602.22918
词表里没单独搜的：visual lock-in、anchoring、commonsense-driven hallucination（后者经引用链覆盖）。

### 阅读量（本轮，分开数）
- **F：26 篇** — 2606.28273、2507.13868、2505.17127、2601.05201、2507.01790、2505.20977、2604.09364、2602.03677、2602.14518、2605.19250、2607.26326、2606.17953、2607.26913、2610.19407、2607.29240、2503.10996、2601.09445、2605.17826、2607.03365、2609.33431、2606.18924、2609.24238、2608.06938、2507.07151、2605.24024、2610.13111。其中通读主文的只有 2606.28273；其余是定向读（方法、对照、结果表、局限）。只核了个别段落的：2608.06938、2507.07151、2609.24238、2609.33431、2605.24024、2610.13111。
- **A：25 篇** — 2604.14363、2608.19208、2604.22038、2609.00550、2402.18154、2602.22918、2509.02805、2610.12942、2610.33841、2610.21902、2607.28991、2608.00035、2609.32763、2609.35272、2609.32489、2510.26721、2604.16902、2410.03659、2505.19616、2606.00959、2511.13400、2610.03445、2604.14888、2602.12533、ICML 2026 He et al.（会议页面转述）。
- **S：约 47 条** — 2509.23050、2511.22826、2607.27304、2609.26986、2601.22150、2604.17217、2608.03160（只看标题）；取到未读：2504.08974、2411.07404、2408.11261、2410.04780、2608.17205、2510.21518、2606.14703、2608.27417、2607.29412、2602.11824、2412.13949、2511.17254、2601.05547、2509.21400。只有片段：2606.27596、2611.01467、2606.06890、2605.13737、2608.22916、2610.00111、2609.09124、2604.06422、2603.29676、2605.08200、2407.12404、2505.22637、2602.17881、2307.15771、2402.15390、ParaConflict 原文、2410.05817、2410.11414、2512.07515、2412.13817、2604.12371、2604.25102、2410.08145、MINT、Pi et al. EMNLP 2025、Yu et al. 2023、2605.22902（arXiv 404）。
- **沿用第一轮 F、本轮未重读**：2505.23941、2503.02199、2410.11302、2504.09456、2511.02243、2609.07474、2604.21911。

### 第 7 步 边界申报
- OpenReview 审稿讨论：未读到（见第 5 步）。
- Hua et al.（2507.01790）的被引清单未扫到。2606.28273 是最近的一篇，目前只有 4 条被引；它自列的下一步（2×2 设计）与跨类检验最可能出自同一作者组的后续稿，属并行未公开工作，无法覆盖。
- "未见随机对照"的判断来自对 `random` 等词的全文检索，附录里换了说法的对照可能漏掉（PvP、2604.09364、ModPref、Hua）。
- 逐字引文核对：两批共 70 条，69 条整句命中；2606.28273 的"the measured asymmetry may partly reflect…"一句因 PDF 页码"9"夹在句中，拆成前后两半后各自命中。沿用第一轮的引文（标了"第一轮"的）本轮没有重核。
- 知识截止在 2026-06 前后；之后的论文与模型名（Qwen3.5、Gemma-4、GLM-4.6V、Holo2、Qwen3-VL 235B 等）照原文转录，未独立核实。2610.13111 自标"Published as a conference paper at ICLR 2027"，与日期不合常理，未核实。
- 非 arXiv、非英文、在审未公开、并行未公开的工作未覆盖。闭源模型内部无法验证。各论文的 GitHub 仓库未打开。
- 过程记录：下载目录 `/tmp/a2_audit/papers` 里有 10 份 PDF（2509.02805、2610.13111、2606.14703、2605.24024、2608.27417、2509.21400、2511.17254、2603.27982、2412.13949、2601.05547）不在我可见的命令记录里。我重新从 arXiv 各下一份逐字节比对，10 份全部一致，之后才使用。
- 过程记录：`/tmp` 一度触发配额错误，一批下载作废后重下。`/tmp/a2_audit` 现约 78 MB，其中 21 个 PDF（含 10 个作废的残件）我没能删掉（带变量的 `rm` 被安全检查拦下，未绕过），可整目录删除。
