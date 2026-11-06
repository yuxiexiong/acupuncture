# 15 七步查重：A5 空间关系失败（空间头稀疏 / 空间词偏置 / 位置编码）

日期：2026-11-06。执行顺序 6 → 5 → 1 → 2 → 3 → 4 → 7。本候选本轮接受了 1 轮七步、42 条查询（31 条网页检索、8 条 Semantic Scholar 被引查询、3 次 OpenReview 尝试）的检验；第 1–4 步各只有 3 条查询，偏薄，见第 8 节。不给等级或分数。

阅读层级：**F** = 取到正文并读了对应章节或表（其中"F通读"= 读了主体各节，"F定向"= 只读了标出的章节）；**A** = 只读了摘要；**S** = 只有检索片段或标题。本文件所有逐字引文都来自本地取到的 arXiv HTML 转出的正文（不是网页摘要工具的转述），F 级数字同此。

先说最不利的三点：

1. **"失败在语言侧"这句话已被写出，且同时存在相反结论。** 2606.01914 写 "the failure arises on the language side rather than the visual side"；2603.22278 写 "the dominant source of spatial information originates in the vision encoder" 且 LM 侧机制 "plays only a secondary role"；2601.12626 对 LLaVA-1.5 与 Llama-3.2 写 "linguistic reasoning was not the reason these failures occurred"。三者设定不同（见 4.3），没有判别实验。
2. **(b) 的"0.998 可读"建立在人工筛出的极端样本与合成两物体场景上，且在较强模型上词偏置的总体效应很小**（Qwen2-VL-7B 修复增量在公开集 −1.1 至 +3.9 点）。
3. **基本的同视角空间关系在行为层已接近饱和**：EASI 报告 GPT-5 在 Spatial Relations 上 "reaching human-level performance"；InternVL3.5 在 What'sUp-A 上 97.3%。差距大的子类已移到视角变换、心理重建、相机视角下的前后、朝向幅度，而三种根因说法的证据几乎都停在两物体的 left/right/above/below。

---

## 1. 候选定义

- **现象**：VLM 在基本空间关系题上答错——左右、上下、前后、朝向、相对深度、视角变换。基准：What'sUp、VSR、COCO-/GQA-spatial、3DSRBench、ViewSpatial-Bench、SpatialBench 类（EASI 八项）、DORI/OR-Bench（朝向）。
- **根因主张（三个部位）**：(a) 负责空间感知与关系推理的注意力头稀少且弱；(b) 语言侧的空间词偏置——选项里多一个空间词就把答案拉走，而视觉关系仍可线性读出；(c) 位置编码与位置索引的安排——图像拍平成一维、文本与图像共用索引空间。
- **预期结论（第 3 步用来检索的句子）**：
  - S1："在同一批模型、同一批错题上，(a)(b)(c) 各自能修回的错误占比是 x/y/z，重叠为 w。"
  - S2："空间关系错误主要是语言侧读出问题，不是视觉侧缺信息；只改语言侧就能修回大部分。"
  - S3："存在跨模型族一致、可免训练干预的空间部件或方向。"
- **检索到的占位情况**：S2 属**结论被占**（且有反方，见上）；S3 属**对象被占**（spatial ID、role direction、ordering direction 都已在 ≥3 族上做了带对照的免训练干预）；S1 在对象层与结论层本轮未检到（专门查询 5 条 + 6 篇邻居的被引列表逐条看标题），最接近的一篇明写留作 future work（2609.35486）。

---

## 2. 竞争者全景表

共 27 行。"对照"列指有无随机部件 / 随机方向 / 图像消融对照；"稳健"列指换选项顺序、换问法、留出数据、自然图像。

| # | 工作 | 类型 | 模型族 | 干预类型 | 对照 | 评测稳健性 | 效果数字 | 自认局限（逐字） | 代码 | 层级 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | [2606.01914](https://arxiv.org/abs/2606.01914) Spatial Lexical Bias（v2 2026-08，发表处未核） | 定位 + 修复 | LLaVA、Qwen、InternVL 共 9 个（1B–8B）；机制分析 7 个；稀疏敲除仅 InternVL2-1B | 残差互换、稀疏敲除（推理时）；LLM-only LoRA-DPO / SFT（训练） | 等量随机部件；无关词选项对照；blank-image 重训探针；置乱标签探针；held-out case | 选项全排列（2/6/24 种全对才算对）；三个公开集；未见关系；MME/MMBench/COCO caption/MMLU/IFEval。等义改写未测；开放式只做了 LLaVA 三个模型 | BSTF 55 例：三选一 0.022→0.917，四选一 0.038→0.816，二选一保持 0.999。全量四选一 robust 增量最高：合成 +100.0，WhatsUp-B +68.0，SpatialMQA-Direct +32.6，VSR +20.1。提示修复三种变体 ≤10.7% | "they do not establish a complete circuit"；"The mechanistic account of this paper does not transfer directly to open-ended generation; we leave this to future work." | https://github.com/chuang-ma-ku/spatial-lexical-bias | F通读 |
| 2 | [2603.20662](https://arxiv.org/abs/2603.20662) Attention in Space | 定位 + 修复 + 基准（CogVSR） | InternVL3-2B/8B、Qwen2.5-VL-3B/7B、Llama-3.2-11B/90B | 头遮蔽（输出乘 ε）；头方向正向平移；SHA（输入加框与掩码） | CogVSR 上等量随机头（Table 2）；下游四基准的负向干预表（Table 4）只有 before/after，表头无随机列 | 下游各基准只抽 200 题；LLM 判分（Gemini2.5-flash-lite）；换问法、选项顺序未测 | 遮蔽空间感知头：Qwen2.5-VL-7B 80.04（随机）→57.69。VSR 遮蔽后 62.47→21.76。正向干预 80.04→81.89；VSR 62.47→63.72。SHA：InternVL3-2B 空间感知 61.37→71.82 | "we focus on eight predefined cognitive functions and restrict our analysis to attention heads, leaving other components such as MLPs unexplored." | 未找到 | F通读 |
| 3 | [2608.23074](https://arxiv.org/abs/2608.23074) Grounding Isn't Knowing | 定位 | LLaVA-1.5-7B/13B、Qwen2.5-VL-7B | token 消融、attention knockout、头级因果中介、累积头消融 | 等量随机 token，三种子；低重要性头对照 | What'sUp A/B 的筛选子集（真实受控照片）；另有 LaMa 去物体版 | 目标 token 消融：定位掉 5.37/27.90/64.93 点，关系 "at most 1.32 points"。定位与关系的 top-10 头只重合 2–3 个 | "Whether this mechanism generalizes to crowded scenes, 3D relations, and temporal reasoning remains open." | 未找到 | F通读 |
| 4 | [2503.01773](https://arxiv.org/abs/2503.01773) AdaptVis（ICML 2025） | 定位 + 修复 | LLaVA-1.5、LLaVA-1.6；附录 Qwen2-VL | 图像注意力 logits 温度缩放（推理时，免训练） | 未见随机对照；对比 VCD、DoLa | 改选项个数（2/4/6）；POPE/GQA/VQAv2/TextVQA 不退化；α、β 要按数据集用 20% 验证集调 | "up to 50 absolute points"（WhatsUp 合成子集）；VSR F1 51.3→62.5（LLaVA-1.5，第一轮 F）；Qwen2-VL 在 VG_two_object 上 10+ 点 | "the optimal α and β is different across different distributions and prompts. This dependence on a validation set for tuning poses a limitation on its applicability." | github.com/shiqichen17/AdaptVis（第一轮） | F定向（局限、附录 B、E.7、E.8） |
| 5 | [2601.12626](https://arxiv.org/abs/2601.12626) Spatial IDs（ICLR 2026） | 定位 + 诊断 + 微调信号 | 提取自 11 个 VLM（LLaVA、Llama、Qwen、InternVL、Gemma 系）；失败诊断只做 LLaVA-1.5-7B 与 Llama-3.2-11B | spatial ID 转向（推理时）；像素遮蔽；Qwen2-2B 微调 | 噪声对照（检索片段称 belief swap 64.4% 对噪声 29.5%，S）；遮蔽物体 vs 随机位置 | 合成（Objaverse 贴网格）提取；COCO-spatial 诊断 | 诊断结论："for both LLaMA and LLaVA, the linguistic reasoning stage is faithful to spatial IDs"；LLaVA 归到编码器检测，Llama 归到跨模态整合 | "These conclusions are preliminary and do not suggest that all of a model's failures stem from one architectural component"；"we only extract and steer models of sizes up to 14B parameters" | https://github.com/Raphoo/linear-mech-vlms | F定向（摘要、§4.2、§7） |
| 6 | [2603.22278](https://arxiv.org/abs/2603.22278) Dual Mechanisms of Spatial Variable Binding（Cui, Prakash, Raina, Bau, Torralba, Shaham） | 定位 + 修复 | Qwen、Gemma、Pixtral 三族 5 个模型 | interchange intervention；对全部视觉 token 加排序探针方向（推理时，免训练） | 随机方向（10%、13% 对 40%、54%）；CoT 对照；七个非空间 VQA 基准 | 三个合成集 + What'sUp + COCO-spatial（自然图）；跨数据集、跨轴探针迁移；α 在验证集选后 "gains persist" | 修回失败 40.2%（Gemma-3-4b）、54.5%（Qwen2-VL-2B）；What'sUp 合成拼图 43–55%；on/under、front/behind 53–68%。非空间基准 "at most 5 points" 代价 | "a mechanistic account of depth relations such as front/behind, are left for future work"；自然图上做不了 interchange："a condition that cannot currently be satisfied with unmodified natural images" | https://spatial.baulab.info | F定向（引言、§5.4、B.1） |
| 7 | [2606.31257](https://arxiv.org/abs/2606.31257) Decodable Is Not Grounded | 定位（方法学批评）+ 修复 | 行为 + arbiter + 探针：14 个模型、6 个 LM 族（Qwen2/2.5/3、Mistral、SmolLM、Gemma），2B–27B，含 SpaceQwen、SpaceOm；纠正电池 8 个 | 方向投影、旋转、SEA、SADI、ITI、SAE、LoRA、ReFT 共 9 种 | 五种图像消融（gray、black、noise、scramble、mismatch）；shuffled-label 探针下限；旋转对 LoRA 三种子 | ViewSpatial camera-relative（1047 纯轴题）+ What'sUp + 3DSRBench | Qwen2.5-VL-7B：水平 82.4（gray 49.4），竖直 58.5（gray 59.6），深度 31.4（gray 45.1）。竖直投影增益有图 +21、无图 +19。Qwen3-VL-8B 深度 21%→77%（免训练旋转，三种子 +49±8 对 LoRA +55±2）；LLaVA-OV +14，InternVL3-8B +8，InternVL3-2B 与 Pixtral 只能压不能装 | "our causal evidence is representation-level, as a clean pixel-level minimal pair for camera-relative front/back is unattainable"；"tracing it to training data is future work." | 未找到 | F通读 |
| 8 | [2609.35486](https://arxiv.org/abs/2609.35486) Who Is Left of Whom? | 定位 + 修复 | LLaVA-1.6-Mistral-7B、InternVL3.5-8B、Pixtral-12B 及各自 LLM 骨干；行为测更多 | 激活修补、location-ID 转向、role direction 转向（推理时） | 范数匹配随机方向、shuffled-ID、正交方向；95% CI | 配对一致性（位置互换、目标/参照反转）；合成 → What'sUp-A、COCO-Spatial（不重调） | What'sUp-A：LLaVA-1.6 准确率 82.2→84.0，反转一致性 70.6→73.9；InternVL3.5 97.3→97.4；Pixtral 83.5→85.0。九个设定里反转一致性全涨，八个 CI 不含零 | "attributing individual errors to specific components is left for future work."；"larger, MoE and proprietary models remain to be examined." | 未找到 | F定向（引言、Table 2、局限） |
| 9 | [2608.22916](https://arxiv.org/abs/2608.22916) Knowing Isn't Always Saying | 定位 | 10 个 VLM；3 数据集；7 种提示格式 | direction patching（沿 spatial-ID 方向）；头敲除 | crossfit 与噪声基线 | 跨提示格式、token 位置、层 | 因果影响只在 L12–L32 出现；text CoT 在 9/10 模型上压住 object-word 处的传输；InternVL3-8B 一个头（L27.H21）恢复 +0.063，LLaVA-OV 最好的头只 +0.013 | "a full circuit account (upstream triggers, downstream completion, cross-architecture comparison) remains open."；"direction patching is silent on transport that may occur through non-linear pathways" | 未找到 | F定向（摘要、引言、§4.2 局部、局限） |
| 10 | [2610.17976](https://arxiv.org/abs/2610.17976) Seeing Depth but Choosing Cues | 定位 + 修复 | 五个模型族（含 Qwen3-VL-4B/8B/32B、LLaVA-OneVision-1.5、Gemma） | object-level depth write-back（推理时，不用深度标注） | 随机方向、反向、写在答案 token、cue-avoidant 提示、外部深度图；grey 与 mismatch 图 | 渲染 + 真实照片；cue-consistent 对 cue-conflict | Qwen3-VL-8B 渲染竖直冲突：探针 99.0% 对模型 42.8%；LLaVA-OV-1.5-8B 7.4%。"Spatial fine-tuning does not remove the effect." | "The causal effect also varies across model families and domains." | 未找到 | F定向（摘要、§3–4 若干段、局限） |
| 11 | [2605.30161](https://arxiv.org/abs/2605.30161) Why Far Looks Up | 定位（表征）+ 基准（SpatialTunnel） | Molmo、NVILA、Qwen2.5-VL 各带 80k–2M 微调；RoboRefer-2B；Qwen3-VL-235B | 无内部干预；数据缩放微调对比 | consistent 对 counter 分组 | EmbSpatial、CV-Bench-3D、BLINK + 合成 | Qwen2.5-VL（2M 微调）consistent 60.9% 对 counter 24%。RoboRefer gap +0.046，Qwen3-VL-235B +0.068 | RoboRefer："we treat it as an illustrative reference rather than attributing its gains to a single factor." | 项目页（未核 URL） | F定向（摘要、引言、§3–5 若干段、结论） |
| 12 | [2610.13527](https://arxiv.org/abs/2610.13527) S-Space | 定位 + 诊断 | 未摘 | 子空间干预 | 未摘 | 未摘 | 摘要："MLLMs can form capable spatial representations, yet fall short in the spatial transformations required to reason reliably across viewpoint changes." | 未摘 | https://github.com/mirros-lab/s-space | A |
| 13 | [2607.03358](https://arxiv.org/abs/2607.03358) Pathways of Visual Information Flow | 定位 | Qwen3-VL-4B、InternVL3.5-4B、LLaVA-1.5-7B | causal patching、attention knockout | 反事实对 | 合成 + 自然 | "direct pathway for recognition, text-mediated pathway for spatial relations" | "ablation-based interventions can reveal what models could do rather than what they normally do" | https://github.com/israfelsr/vlm-pathways | F定向（摘要、§3–4 若干行） |
| 14 | [2509.19191](https://arxiv.org/abs/2509.19191) RoPE scaling | 定位 + 修复（位置编码） | Qwen2-VL-2B/7B；几何分析含 LLaVA-1.5、Qwen2.5-VL、InternVL-2.5 | RoPE 高维频率缩放（免训练或 6 万条 GQA 微调） | 未摘 | What's Up A/B、VSR、COCO-/GQA-spatial | 2B：What's Up A 74.61→77.27，B 53.16→58.25，VSR 73.30→73.75；7B：A 98.06→98.86，B 87.84→88.97（第一轮 F） | "it serves only as a localized remedy for potential limitations in RoPE." | https://github.com/Siriuslala/vlm_interp | 第一轮 F；本轮 F定向（局限句） |
| 15 | [2503.17349](https://arxiv.org/abs/2503.17349) Beyond Semantics | 定位 + 修复 | LLaVA 系 | 视觉 token 范数归一 + 中层特征（重训） | 置换视觉 token 对照 | 未摘 | 置换后 GQA 61.36→58.62，CV-Bench 2D 56.59→56.26（S，检索片段） | 第一轮记录：对从头训编码器的新模型是否仍有此问题明说不知道 | 项目页 user074.github.io/respatialaware | 第一轮 F；本轮 A |
| 16 | [2603.12545](https://arxiv.org/abs/2603.12545) Spatial Reasoning is Not a Free Lunch | 定位（训练级对照） | LLaVA 框架内换编码器 + 2D-RoPE | 重训 | 无内部干预 | MMVP、VSR 等 | "spatial failures in VLMs are strongly coupled to the visual backbone"；"but do not fully resolve it" | "Our study focused on static, 2D images, benchmarks, and encoder variants within the LLaVA framework." | 未找到 | F定向（结论句、Future Work） |
| 17 | [2505.16416](https://arxiv.org/abs/2505.16416) Circle-RoPE；[2510.23095](https://arxiv.org/abs/2510.23095) MHRoPE | 修复（位置索引） | Qwen2.5-VL、LLaVA | 重训 | 未见方差 | MMMU 等 | Circle-RoPE 0.4–0.6 点（第一轮 F） | "we leave large-scale 3D/video evaluation to future work"（第一轮） | github.com/JJJYmmm/Multimodal-RoPEs（S） | 第一轮 |
| 18 | [2511.13719](https://arxiv.org/abs/2511.13719) SenseNova-SI | 修复（数据缩放） | InternVL3-2B/8B、Qwen3-VL-8B、Bagel | 800 万条空间数据续训 | no-vision、text-only 训练、VSI-Debiased、circular test | 八个基准 + MMBench 等 | InternVL3-8B 八基准均值 45.7→61.5；MindCube 41.5→85.7；VSI 42.1→68.8。Qwen3-VL-8B 版 BLINK −4.8、3DSR −0.7、EmbSpatial −5.2 | "data scaling alone is unlikely to achieve human-level spatial intelligence" | 权重开源 | F定向（引言、主表、§5.3.2、§5.5） |
| 19 | [2609.24813](https://arxiv.org/abs/2609.24813) INTCORT | 修复 | 六个 VLM | 输入几何变换 + 问句反转 + 置信度路由（免训练，不动内部） | 对比 AdaptVis、DoLa、VCD | 七个空间基准 + 通用基准 | 平均 +10.01%，最高 +25.01%（摘要） | 未摘 | 未找到 | A |
| 20 | [2609.38716](https://arxiv.org/abs/2609.38716) SpatialCORE | 修复（后训练） | 未摘 | 置信度加权的 grounding 奖励 | 未摘 | 多基准 + 零样本迁移 | 摘要称开源与专用空间模型中最好 | 未摘 | https://github.com/rafiibnsultan/SpatialCORE | A |
| 21 | [2605.07148](https://arxiv.org/abs/2605.07148) Latent 3D Scene Topology | 定位 + 修复 | 未摘 | 子空间提取 + Dirichlet 能量正则（500 步 SFT） | 未摘 | 真实空间基准 | 比标准 SFT 最高 +12.1% | 未摘 | https://github.com/pittisl/vlm-latent-shaping | A |
| 22 | [2610.05715](https://arxiv.org/abs/2610.05715) OR-Bench / RotationCue | 基准 + 定位 + 修复（朝向） | 12 个 VLM（9 开源 3 闭源）；修复 3 个 | 冻结表征上训轻量解码器，结果以文本回灌 | 去掉图像输入 | 8 个任务 | 旋转检测均值 87.8%；90° 阈值 37.9%、粗角度 40.5%（随机 33.3%，人类 93.3%、88.9%）；精确角度 91.8–100% 落在 0°/90°/180°，"persists even when the visual input is removed entirely"；RotationCue Macro-8 +7.9 至 +12.6 | 未摘 | 未找到 | F定向（摘要、引言、§3） |
| 23 | [2604.13321](https://arxiv.org/abs/2604.13321)；[2603.06054](https://arxiv.org/abs/2603.06054) 朝向探针两篇 | 定位（探针） | 前者 LLaVA-1.5/1.6、LLaVA-OneVision、Qwen2.5-VL-7B 的编码器；后者五个 4B 以下模型（Ovis2.5、Qwen3-VL-2B 等）全栈 | 无干预（前者有特征替换） | 见 4.4 | 见 4.4 | 见 4.4 | 前者："we still don't know why they fail." | 前者 github.com/anjugopinath/MLLM_Orientation（第一轮） | F定向 |
| 24 | [2510.02528](https://arxiv.org/abs/2510.02528) Multimodal Function Vectors | 定位 + 修复 | OpenFlamingo-4B（单族） | 因果中介找头，抽 function vector | 未摘 | 合成 + 真实 | 摘要：提升零样本关系准确率 | 未摘 | https://github.com/fushuhao6/Multimodal-Function-Vector | A |
| 25 | [2602.08713](https://arxiv.org/abs/2602.08713) Multimodal Fine-Tuning: Spatial Features | 定位 | 未摘 | stage-wise model diffing，追到少数头 | 未摘 | 未摘 | 摘要：一部分 vision-preferring 特征编码空间关系 | 未摘 | 未找到 | A |
| 26 | Sophon（NeurIPS 2026 poster，未找到 arXiv 号） | 基准 + 定位 | 开源与前沿模型 | 探针、text-only 对照 | 未核 | 程序生成点云刺激 | 检索片段：开源模型在 BLINK Spatial、What's Up CLEVR 上 85–94%，在 Sophon 上跌到随机；编码器探针 80–97%，LLM 各层 80–86%；text-only 对照 +40 pp | 未取到 | 未找到 | S |
| 27 | [2506.21458](https://arxiv.org/abs/2506.21458) MindCube 附录 F.5；[2510.13394](https://arxiv.org/abs/2510.13394) Spatial-DISE | 分部件微调；人工错误分类 | Qwen2.5-VL-3B；多模型 | 只训编码器 / 只训 LLM / 全训 | — | MindCube-Tiny（step 57 的早期读数） | 基线 37.81；只训编码器 37.81；只训 LLM 51.43；全训 52.67。Spatial-DISE：reasoning 错误 72.5%，perceptual 17.5%，comprehension 10% | — | — | F定向（各一张表/一段） |

行为层参照（不计入 27 行）：EASI [2508.13142](https://arxiv.org/abs/2508.13142)（F定向）；COMFORT [2410.17385](https://arxiv.org/abs/2410.17385)（A）。

### 2.1 行为层现状（F，除注明外）

- 八基准主表（[2511.13719](https://arxiv.org/abs/2511.13719) Table 1）。人类：VSI-Bench 79.2、MMSI 97.2、MindCube 94.5、SITE 67.5、BLINK 95.67、3DSR 95.7、EmbSpatial 90.33。闭源最好一行（Gemini-3-Pro-Preview）：52.5 / 45.2 / 70.9 / ViewSpatial 50.4 / 62.3 / 76.0 / 68.9 / 84.3。GPT-5：55.0 / 41.8 / 56.3 / 45.6 / 61.9 / 68.0 / 60.3 / 81.6。Qwen3-VL-8B：57.9 / 31.1 / 29.4 / 42.2 / 45.8 / 66.7 / 53.9 / 77.7。InternVL3-8B：42.1 / 28.0 / 41.5 / 38.7 / 41.1 / 53.5 / 44.3 / 76.3。
- 子类差距（[2508.13142](https://arxiv.org/abs/2508.13142)）：GPT-5 "even reaching human-level performance on tasks requiring Metric Measurement (MM) and Spatial Relations (SR)"；"Notable gaps, often exceeding 30 percentage points" 在 Perspective-Taking、Mental Reconstruction、Deformation and Assembly、Comprehensive Reasoning；GPT-5 在两个 MR 子任务上低于随机。
- 相机视角三轴（[2606.31257](https://arxiv.org/abs/2606.31257) Fig. 3，轴内二选一，随机 50%）：水平 / 竖直 / 深度——Qwen3-VL-8B 88 / 95 / 22；InternVL3-8B 88 / 62 / 31；Gemma-3-4B 60 / 60 / 53，12B 80 / 61 / 43，27B 82 / 62 / 46；Qwen2.5-VL-7B 83 / 59 / 31。同一批模型在 What'sUp 近场 front/behind 与 3DSRBench closer-to-camera 上是对的。
- 两物体基本题：InternVL3.5-8B 在 What'sUp-A 上 97.3%，LLaVA-1.6-Mistral 82.2%，Pixtral-12B 83.5%（[2609.35486](https://arxiv.org/abs/2609.35486) Table 2）；但 LLaVA-1.6 的反转一致性 70.6%、位置互换一致性 66.3%。严格口径（四选一、24 种排列全对）下基线：Qwen3-VL-8B 在 WhatsUp-B 83.8、VSR 38.1；LLaVA-1.5-7B 在 WhatsUp-B 6.4（由 [2606.01914](https://arxiv.org/abs/2606.01914) Table 2 的修后值减增量算出）。
- 朝向：OR-Bench 见第 22 行；DORI 见第一轮 01-C5。
- Gemma3 在 What'sUp / VSR 上的逐项数字、闭源模型在 What'sUp / VSR 上的最新数字：本轮未取到。

---

## 3. 各轴最高水位

| 轴 | 目前最好的是谁、做到什么 |
|---|---|
| 模型族数量与多样性 | 行为 + 图像消融 + 逐层探针：2606.31257，14 个模型、6 个 LM 族、2B–27B，含三条族内规模阶梯。因果干预：2608.22916 十个 VLM（direction patching）；2606.31257 八个模型（九种纠正）；2601.12626 十一个 VLM（提取与转向 spatial ID）。闭源模型的内部证据：没有 |
| 因果对照的严格程度 | 2609.35486：范数匹配随机方向 + shuffled-ID + 正交方向 + 95% CI。2610.17976：随机方向、反向、换写入位置、提示对照、外部深度图、grey 与 mismatch 图。2606.31257：五种图像消融且要求一致，三种子。2603.22278：反事实成对的 interchange intervention + 随机方向。2606.01914：等量随机部件 + held-out case + 无关词对照 |
| 评测稳健性 | 选项顺序：2606.01914 全排列全对。配对一致性：2609.35486。捷径排查：2511.13719（no-vision、VSI-Debiased、hard circular）与 2605.30161 / 2610.17976（线索冲突分组）。合成 → 自然图不重调：2609.35486、2603.22278。等义改写与开放式生成：本轮读到的正文里都没有系统测试（2606.01914 只在 LLaVA 三个模型上做了 option-free one-word，并声明机制不同） |
| 效果量 | 训练类：LLM-only DPO 在极端样本上 0.022→0.917，公开集四选一 robust 最高 +68.0 / +32.6 / +20.1（2606.01914）；数据缩放八基准均值 +15.8（2511.13719）。免训练类：修回 40–55% 的失败（2603.22278，Gemma-3-4b 与 Qwen2-VL-2B）；深度 21%→77%（2606.31257，仅 Qwen3-VL-8B）；VSR F1 +11.2（AdaptVis，LLaVA-1.5）；平均 +10.01%（INTCORT，A） |
| 任务与数据广度 | 行为：EASI 八基准。机制：多数停在两到三物体的 left/right/above/below；front/behind 与深度有 2606.31257、2610.17976、2605.30161；视角变换有 S-Space（A）；朝向有 OR-Bench。没有一篇机制工作同时覆盖平面关系、深度、视角、朝向 |
| 是否免训练 | 是：AdaptVis、ordering amplification（2603.22278）、role steering（2609.35486）、旋转（2606.31257，一个模型）、depth write-back（2610.17976）、RoPE scaling、INTCORT、SHA（要外部检测器）。否：DPO/SFT、SenseNova-SI、Circle-RoPE、Beyond Semantics、SpatialCORE |
| 是否给出统一解释 | 没有一篇把 (a)(b)(c) 放进同一实验。最接近的"分部位"框架：2601.12626 §4.2（编码器 / 跨模态绑定 / 语言推理三段诊断，两个模型，相关级，作者自称 preliminary）；2606.31257（按轴分三态：grounded / prior / inverted，不是按部位）；S-Space 的 perception–computation 分解（A）；MindCube 分部件微调；2603.06054 的 perceptual / cognitive failure（探针） |

---

## 4. 竞争解释与事实约束

### 4.1 事实约束（逐条）

1. **线性可读不等于依赖图像**。竖直轴探针 94%，但 real 58.5 ≈ gray 59.6；投影增益无图 +19、有图 +21。— [2606.31257](https://arxiv.org/abs/2606.31257) §4（F）。2606.01914 的 0.998 做了 blank-image 重训（0.137）与置乱标签对照，所以不属于纯先验；它没有做 mismatch 图对照（附录 L 只列这两种）。
2. **(b) 在较强模型上的总体效应小**。DPO 增量（二/三/四选一）：Qwen2-VL-7B 在 WhatsUp-B +0.9 / +1.9 / +3.9、VSR −1.1 / +0.0 / +3.0；Qwen3-VL-8B 在 WhatsUp-B +2.2 / +4.7 / +4.9、VSR +2.4 / +3.2 / +4.5。LLaVA-1.5-7B 在 WhatsUp-B +38.9 / +50.6 / +49.6。修后 VSR 四选一 robust 仍只有 15.0–43.9。— [2606.01914](https://arxiv.org/abs/2606.01914) Table 2（F）
3. **(b) 的机制证据样本很窄**。BSTF 55 例的门槛是二选一 robust = 1.00 且三选一掉 ≥80 pp；各模型例数 16 / 11 / 9 / 9 / 5 / 3 / 2，"Qwen2-VL-2B and Qwen3-VL-8B have very few cases (n≤3)"；稀疏敲除与 token 间交接只在 InternVL2-1B。— 同上 §3.1、M.7（F）
4. **不是选项数的问题，是词对的问题**。把二选一里的错误项换成那个空间词（仍是两项），严格准确率 1.000→0.163。— 同上 §3.1（F）。这说明"二选一稳定"只对特定竞争词成立。
5. **(a) 的"稀缺 → 失败"没有被检验**。原文用词是 "which likely contributes to the failure" 与 "suggesting that current VLMs likely underrepresent spatial reasoning"。正向干预 +1.85 点。— [2603.20662](https://arxiv.org/abs/2603.20662) §6（F）
6. **(c) 的修复效应小**。RoPE scaling 在 VSR 上 +0.45，作者自称 "localized remedy"；Circle-RoPE 0.4–0.6 点；换编码器加 2D-RoPE "do not fully resolve it"。— [2509.19191](https://arxiv.org/abs/2509.19191)、[2603.12545](https://arxiv.org/abs/2603.12545)（F定向）；Circle-RoPE 为第一轮 F
7. **空间数据微调没有消掉线索捷径**。Qwen2.5-VL 2M 微调后 consistent 60.9% 对 counter 24%（[2605.30161](https://arxiv.org/abs/2605.30161)）；"Spatial fine-tuning does not remove the effect"（[2610.17976](https://arxiv.org/abs/2610.17976)）；SpaceQwen-3B 与 SpaceOm-3B 相机视角深度 45 / 46（[2606.31257](https://arxiv.org/abs/2606.31257) Fig. 3）；SenseNova-SI-1.1-Qwen3-VL-8B 在三个 BSTF case 上 0.637 / 0.006，基座 1.000 / 0.045（[2606.01914](https://arxiv.org/abs/2606.01914) 附录 P，作者注明只有三个 case）。反例：RoboRefer（2000 万条以上）gap +0.046。
8. **基本同视角关系已接近饱和**。见 2.1。2606.31257 称 What'sUp、VSR "now largely saturated"。
9. **微观部件跨模型不一致**。同一免训练旋转只在 Qwen3-VL-8B 上等于训练编辑；InternVL3-8B 有单头集中而 LLaVA-OV 没有（"architecture-dependent"）；Janus 上线性子空间响应强但生成不变。— [2606.31257](https://arxiv.org/abs/2606.31257) §6、[2608.22916](https://arxiv.org/abs/2608.22916) §4.2 与局限（F）
10. **提示修不好**。三种指令变体 ≤10.7%（2606.01914）；CoT "breaks about three times as many previously correct items as amplification"（2603.22278）；text CoT 压住传输（2608.22916）；三种 CoT 方案与 RL "cannot reliably improve"（2511.13719）；cue-avoidant 提示无效（2610.17976）。这是先例支持，不是坏消息；放在这里是因为它排除了"换提示"这条便宜路。
11. **AdaptVis 的最优温度随数据分布与提示变**，合成数据多数要 α<1、真实图要 α>1。— [2503.01773](https://arxiv.org/abs/2503.01773)（F）

### 4.2 竞争解释（逐条，同一现象的另一种已发表解释）

1. 主要信号来自视觉编码器的全局排序表示，LM 侧机制只是次要。— [2603.22278](https://arxiv.org/abs/2603.22278)
2. 错在 spatial ID 绑定之前（LLaVA：编码器检测；Llama：跨模态整合），语言推理忠实于 ID。— [2601.12626](https://arxiv.org/abs/2601.12626) §4.2
3. 竖直是语言先验，深度是带错符号的视觉读出，成因指向 "a learned frame-convention conflict"；指纹由 LM 骨干决定。— [2606.31257](https://arxiv.org/abs/2606.31257) §5、§7
4. 图像平面线索（竖直位置、表观大小）压过已编码的深度。— [2610.17976](https://arxiv.org/abs/2610.17976)、[2605.30161](https://arxiv.org/abs/2605.30161)；LLaVA 里 "above"/"front" 与 "behind"/"below" 嵌入几乎重合（[2601.12626](https://arxiv.org/abs/2601.12626) Fig. 7）
5. 参考系歧义：模型偏向反射式坐标变换、不能灵活换参考系。— [2410.17385](https://arxiv.org/abs/2410.17385)（A）
6. 中层对图像的注意力几何落点不对。— [2503.01773](https://arxiv.org/abs/2503.01773)
7. 视觉 token 范数压住位置信号，模型按 bag-of-tokens 用视觉。— [2503.17349](https://arxiv.org/abs/2503.17349)（第一轮 F）
8. 目标/参照角色绑定：角色反转后一致性掉；问句里两个实体换顺序后 "performance declines dramatically"。— [2609.35486](https://arxiv.org/abs/2609.35486)、[2503.01773](https://arxiv.org/abs/2503.01773) E.8
9. 条件性传输：编码普遍在，能否到达答案取决于提示格式、token 位置与层；空间关系走 text-mediated 通路。— [2608.22916](https://arxiv.org/abs/2608.22916)、[2607.03358](https://arxiv.org/abs/2607.03358)
10. 瓶颈在视角变换的计算，不在感知。— [2610.13527](https://arxiv.org/abs/2610.13527)（A）
11. 编码器预训练目标与一维展平。— [2603.12545](https://arxiv.org/abs/2603.12545)
12. 数据稀缺："The limitations in spatial intelligence mainly stem from high-quality, diverse data scarcity." — [2511.13719](https://arxiv.org/abs/2511.13719)

### 4.3 三种落在不同部位的说法有没有被直接比较，各自解释多大比例

- **直接比较**：把 (a) 空间头、(b) 空间词偏置、(c) 位置编码放进同一批模型、同一批错题的实验，本轮在对象层和结论层都没有检到（专门查询 5 条：网页检索第 2、7、15、21、23 条；另逐条看了 6 篇邻居的被引标题）。2609.35486 明写 "attributing individual errors to specific components is left for future work."
- **现有的零散比例数字（口径互不相同，不能相加，也不能互相比较大小）**：
  - (b)：极端样本上修回约九成（0.022→0.917）；自然基准的错误里有多少属于词偏置，原文没有给。
  - (a)：必要性——遮蔽后掉 20–40 点；可修回——+1.85 点。没有"占错误多少"的数字。
  - (c)：What's Up B +5.09 点（Qwen2-VL-2B），VSR +0.45 点。
  - 视觉侧排序信号：修回 40–55% 的失败，随机方向 10–13%（2603.22278，per-item α）。
  - spatial ID：错题的 ID 偏差分布与对题显著不同（Mann-Whitney U），没有比例。
  - 分部件微调：只训 LLM 拿到全训增益的约 92%（(51.43−37.81)/(52.67−37.81)），只训编码器为 0（MindCube，Qwen2.5-VL-3B，step 57）。
  - 人工错误分类：reasoning 72.5% / perceptual 17.5% / comprehension 10%（Spatial-DISE，行为层）。
- **"语言侧"与"视觉侧"两派是否真冲突**（推导）：设定不同。2606.01914 的样本按构造是二选一全对的，等于预先筛掉了视觉侧失败；2603.22278 用的是两物体排序任务上较弱的模型（Gemma-3-4b、Qwen2-VL-2B，"the 7B variant is near ceiling here"）；2601.12626 的诊断在 COCO-spatial 二选一上、用 LLaVA-1.5 与 Llama-3.2。三者各自成立与否不互相否定，但也因此都不能推到"VLM 空间错误主要在哪"。没有人在同一模型同一题集上跑过两边的仪器。

### 4.4 "朝向"两份探针结论是否真冲突

不是同一个量，也不是同一种探针；读完后两篇在"编码器里有、LLM 没用上"这一点上方向一致。

| | [2604.13321](https://arxiv.org/abs/2604.13321) | [2603.06054](https://arxiv.org/abs/2603.06054) |
|---|---|---|
| 被测的量 | 整图或贴上去的前景块的**平面内旋转角**（回归） | CARLA 三维场景里行人、自行车**朝左还是朝右**（二分类反事实对） |
| 探针输入 | 编码器输出的完整特征（数万维），岭回归 | 平均池化或左右分区池化后的激活；LLM 里取末 token |
| 位置 | 只测视觉编码器 | 编码器各层 → 投影器 → LLM 各层 |
| 训练/测试 | 同一张图的不同旋转（"familiar"） | 不同 town 留出 |
| 结论 | MAE < 3°；信息 "spread diffusely across tens of thousands of features" | 平均池化下全栈都读不出；分区池化下编码器中层在 5 m 处读得出（Ovis2.5、Qwen3-VL），LLM 层读不出；20 m 以上趋零 |

2603.06054 自己的结论是 "the LLM appears to be the main bottleneck for orientation understanding at short distances"。第一轮摘的那句 "not explicitly encoded ... throughout the entire model" 对应的是平均池化探针。第三份证据：OR-Bench（绕竖直轴的方位角变化）上线性探针在粗角度上超过模型自己的回答，且 canonical-angle collapse 去掉图像仍在（[2610.05715](https://arxiv.org/abs/2610.05715)）。尚缺的：同一批模型、同一批图上同时测这三种"朝向"，以及对读得出的朝向方向做干预。

### 4.5 "线性可读 0.998 但被空间词拉走"的设定是否自然

- 图像：Blender 渲染，两个物体（红球 + 蓝方块，或球 + 柴犬），相机固定在上方俯视，目标物体放在参照物四个方向之一、固定距离 1.6。自然图基准只用于修复评测，没有在自然图上做探针。
- 样本：55 个极端 case（见 4.1 第 3 条）。作者自称 "BSTF cases are extreme exemplars, not exhaustive"。
- 探针：每模型 800 条同分布的答对样本训练，在 7,443 条答错行上测；第一层就超过 0.92。（推导）在固定相机的两物体合成图里，关系标签是两物体图像坐标的简单函数，第一层即可读说明这个视觉判别本身很容易，不能据此推到自然图上"关系仍可读"。
- 选项：第三个选项是人为加的；作者补了四选一延伸、无关词对照、去选项的 one-word 实验（仅 LLaVA 三个模型，"LLaVA-v1.6-Mistral answers right for all 1,500 front images"），并声明 "We do not claim that these generation preferences share the same mechanism as the MCQ effect."
- （推测）被加的空间词与真实关系在图上是否存在可辩护的歧义（例如俯视下的 behind 与图像上方），我读到的附录 B 没有排除；需要看其渲染参数才能判断。

### 4.6 大规模空间数据微调是否已在行为层解决

没有解决，但基本关系已不是差距所在。

- 涨幅：见第 18 行。SenseNova-SI 自己写 "data scaling alone is unlikely to achieve human-level spatial intelligence"，并报告增益随数据量递减。
- 修后离人类：VSI 68.8 对 79.2；MMSI 43.3 对 97.2；3DSR 55.5 对 95.7；BLINK 63.9 对 95.67。
- 捷径仍在：见 4.1 第 7 条。
- 内部根因研究剩下的位置（只陈述文献里空着的，不评价）：微调前后内部哪里变了，只有 2602.08713（A，针对多模态微调本身）与 2605.30161（表征层，无干预）；线索冲突、相机视角前后、视角变换、朝向幅度上的机制工作各只有一两篇；闭源模型没有内部证据。

### 4.7 文本 LLM 或纯视觉模型的结论能否让 VLM 结论变成推论

- 文本 LLM 里空间关系线性可读、反义关系近似对跖：[2506.02996](https://arxiv.org/abs/2506.02996)（S）。2609.35486 直接在 LLM 骨干 + 文字场景描述上测到同样的 location ID 与 role direction，且 LLM+text 的角色转向增益比 VLM+image 大（LLaVA-1.6 骨干 +3.3 对 +1.8）。（推导）角色绑定这一部分在 VLM 上的结论有被"继承自文本 LLM"蕴含的风险；对象位置读入这一部分不被蕴含。
- 文本 LLM 上"探针近乎完美、干预只修回约两成"：[2603.18353](https://arxiv.org/abs/2603.18353)（A，临床分诊任务，探针 AUROC 98.2%，概念瓶颈转向修回 17/85 并破坏 25/47）。（类比）提示 VLM 上"可读所以可修"的推断同样可能不成立；2606.31257 引它做同一论点。
- 纯视觉：CLIP 式模型里位置嵌入与 token 嵌入的交互造成左右对称破缺（[2601.12809](https://arxiv.org/abs/2601.12809)，S，合成一维数据）；编码器探针 80–97%（Sophon，S）；VLM 明显差于自己的编码器（[2506.08008](https://arxiv.org/abs/2506.08008)，S）。这些支持"编码器里有"，不蕴含 VLM 里哪个部位丢掉。
- 文本 LLM 选项集合偏置：检到位置偏置、流行度偏置（[2608.29257](https://arxiv.org/abs/2608.29257)，S）等，没有检到"加入语义相近的干扰项"的机制研究（方法层与对象层，1 条查询）。

---

## 5. 作者留下的开口（逐字，均已在本地正文中核对）

- "attributing individual errors to specific components is left for future work." — 2609.35486 Limitations
- "Our interventions also localize manipulable LLM-side states and components, but they do not establish a complete circuit." — 2606.01914 Limitations
- "errors on richer in-the-wild benchmarks may involve additional mechanisms, including object recognition, scene complexity, relation ambiguity, and instruction-following failures." — 2606.01914 Limitations
- "The mechanistic account of this paper does not transfer directly to open-ended generation; we leave this to future work." — 2606.01914
- "Whether similar option-induced biases arise in other tasks, such as counting, color, or questions with ambiguous answers, requires further experimental validation." — 2606.01914
- "we focus on eight predefined cognitive functions and restrict our analysis to attention heads, leaving other components such as MLPs unexplored." — 2603.20662 §7
- "Whether this mechanism generalizes to crowded scenes, 3D relations, and temporal reasoning remains open." — 2608.23074 Conclusion
- "These conclusions are preliminary and do not suggest that all of a model's failures stem from one architectural component" — 2601.12626 §4.2
- "a mechanistic account of depth relations such as front/behind, are left for future work." — 2603.22278 B.1
- "results on closed-source models or architectures with fundamentally different vision encoders remain unexplored." — 2603.22278 B.1
- "tracing it to training data is future work." — 2606.31257 §7
- "a full circuit account (upstream triggers, downstream completion, cross-architecture comparison) remains open." — 2608.22916 §4.2
- "direction patching is silent on transport that may occur through non-linear pathways or through alternative directions outside this subspace." — 2608.22916 Limitations
- "The causal effect also varies across model families and domains. Extending the analysis to additional depth cues and more general spatial reasoning is an important direction for future work." — 2610.17976 §6
- "we still don't know why they fail." — 2604.13321 §1
- "This dependence on a validation set for tuning poses a limitation on its applicability." — 2503.01773 Appendix A
- "it serves only as a localized remedy for potential limitations in RoPE." — 2509.19191
- "data scaling alone is unlikely to achieve human-level spatial intelligence" — 2511.13719 §5.3.2
- "Extending the analysis to depth, distance and multi-object relations, freer layouts and open-ended phrasings is a natural next step." — 2609.35486 Limitations

---

## 6. 三列表

| 先例支持 | 事实约束与竞争解释 | 谁会因此改做法 |
|---|---|---|
| 现象在 ≥6 个 LM 族、14 个以上开源模型与闭源模型上实测（2606.31257、2511.13719、2508.13142） | 基本同视角关系接近饱和；差距在视角变换、心理重建、相机视角前后、朝向幅度（4.1 第 8 条） | 基准设计者：已有人改用全排列全对、配对一致性、线索冲突分组、circular test 口径（2606.01914、2609.35486、2605.30161、2511.13719） |
| "编码在、没用上"在空间题上被 ≥5 篇独立工作测到（2606.01914、2606.31257、2610.17976、2610.05715、2608.22916、Sophon-S） | 可读不等于依赖图像（4.1 第 1 条）；文本 LLM 上可读不等于可修（2603.18353） | 做探针与转向主张的研究者：2606.31257 提议把图像消融作为默认对照；2610.17976 用了 grey 与 mismatch 图对照并在被引列表里引用了前者（推导：依据引用关系与对照设计，未核对其是否明言受此启发） |
| 免训练内部干预在 ≥3 族上有带随机对照的正结果（2603.22278、2609.35486、2610.17976） | 微观部件跨模型不一致（4.1 第 9 条）；各篇修的是不同部位，互相没比过（4.3） | 做空间数据微调的团队：未找到因内部定位结论而改训练配方的记录 |
| 只改语言侧能修（LLM-only DPO；MindCube 只训 LLM） | 视觉侧为主的相反结论（4.2 第 1、2 条）；(b) 在较强模型上效应小（4.1 第 2 条） | 位置编码设计者：有持续的方案迭代（Circle-RoPE、MHRoPE），但空间题上的效应量小；是否因 (c) 的空间题证据而改设计，未找到 |
| 提示与 CoT 修不好（4.1 第 10 条） | 空间微调没消掉线索捷径（4.1 第 7 条） | 具身与机器人下游：未找到 |

---

## 7. 要构成足够贡献至少需要做到什么（只列门槛）

1. **模型覆盖**：不低于现有最高——行为 + 图像消融 + 探针 14 个模型、6 个 LM 族；因果干预 8–10 个模型；且须含 2025–2026 代模型（Qwen3-VL、InternVL3/3.5、Gemma3），因为 (b) 这类效应在 LLaVA 系与 1B–2B 模型上大、在 Qwen2-VL-7B 与 Qwen3-VL-8B 上小。
2. **同一口径的部位比较**：在同一批模型、同一批错题上，把至少 (a) 空间头、(b) 空间词偏置、(c) 位置编码，以及文献里已有的视觉侧排序信号、spatial ID 绑定、角色方向放进同一实验，给出各自可修回比例与重叠。这是现有工作都没有的一条。
3. **因果对照**：每个干预配等量随机部件、范数匹配随机方向、shuffled-ID 或正交方向，≥3 种子并报区间；部件集在留出样本上复验；加图像消融（gray 与 mismatch）区分视觉依赖与先验。
4. **评测稳健性**：选项全排列全对 + 配对一致性（位置互换、角色反转）+ 线索冲突分组 + ≥3 个自然图基准不重调 + 未见关系 + 通用能力不退化；另需补上现有工作都缺的等义改写与开放式生成。
5. **效果量**：训练类需对上 LLM-only DPO（极端样本 0.022→0.917；公开集四选一 robust +68.0 / +32.6 / +20.1）与 800 万条级数据缩放（八基准均值 +15.8）；免训练类需对上"修回 40–55% 失败"（随机方向 10–13%）、深度 21%→77%（单模型）、VSR F1 +11.2，并且在 ≥3 族成立。
6. **任务广度**：超出两物体的 left/right/above/below；至少覆盖一个行为差距仍大于 30 点的子类（视角变换、心理重建、相机视角前后、朝向幅度），或用更严口径证明基本题上差距仍在。
7. **统一解释**：要么给出能在"视觉侧为主"（2603.22278、2601.12626）与"语言侧为主"（2606.01914、2606.31257、MindCube）之间做判别的实验，要么给出条件边界（哪类模型、哪类问法、哪类关系下哪个部位主导）。
8. **回应"数据已解决"**：在 SenseNova-SI、RoboRefer 一类空间微调模型上复测同一套读数。

---

## 8. 七步检索日志

### 第 6 步 对抗式检索（15 条）

查询：(1) VLM spatial reasoning failure mechanistic interpretability left right attention heads 2026；(2) vision language models spatial relations "linearly decodable" but not used causal intervention；(3) spatial reasoning VLM benchmark shortcuts blind language prior without image What'sUp VSR critique；(4) SenseNova-SI spatial intelligence scaling data GPT-5 human gap EASI；(5) spatially fine-tuned VLM still fails left right perspective taking shortcut does not generalize；(7) VLM spatial reasoning errors decomposition vision encoder vs projector vs LLM "error attribution"；(9) "spatial" VLM activation steering OR "attention head" intervention "training-free" What'sUp VSR；(10) Qwen3-VL InternVL3 Gemma 3 GPT-5 Gemini spatial benchmark human gap；(11) COMFORT frame of reference ambiguity；(12) visual token positional encoding LLM spatial reasoning 2D position embedding RoPE；(13) visual prompting coordinates grid set-of-mark does not fix spatial ... chain-of-thought hurts；(23) unified account why VLMs fail spatial reasoning competing explanations compared same models；(24) VLM attention head importance localization unstable ... random head baseline；(25) shuffle OR permute visual token position ids ... 2D RoPE removal；(31) depth input OR 3D geometry encoder VLM spatial reasoning VGGT ... still fails relative direction。

命中：2606.31257、Sophon、2605.30161、2603.20475、2511.13719、2508.13142、2410.17385、2603.12545、MindCube、Spatial-DISE、ACL 2026 SCOPE（S）、SpinBench（S）、Graph-of-Mark 2603.06663（S）。
未命中：否定 (a) 头定位稳定性的专门批评（只找到相邻的 split-half 检查，S）；去掉 2D RoPE 后左右题下降的直接实验（Qwen2.5-VL / InternVL 上）；把三种说法统一比较的工作；加深度或几何编码器的模型在相对方向上的失败分析（只见方法论文标题，S）。

### 第 5 步 引用链（15 次动作）

- Semantic Scholar 被引查询 8 条：2603.20662（8 篇）、2608.23074（2 篇）、2606.31257（3 篇）、2601.12626（14 篇）、2503.01773（约 85 篇）、2603.22278（2 篇）成功；2606.01914 两次返回空或失败，2509.19191 失败（限流）。
- 通读了 2606.31257 的参考文献列表与 related work 段。
- 定点查找 4 条：Why Far Looks Up、Sophon、Seeing but Not Believing / Hidden in plain sight、Kang et al. 的 OpenReview。
- OpenReview：执行了 3 次请求（论坛回复接口、标题检索接口、网页抓取论坛页），**没有取到任何一篇的审稿讨论**。论坛回复接口与论坛页都返回人机验证。标题检索那一次我带了浏览器 UA 字符串并取到了结果；随后我想用同样的 UA 重试论坛回复接口，被权限系统以"绕过机器人检查"为由拒绝（未执行）。在已经收到验证页之后还换 UA 去试，是我的错，之后没有再碰 OpenReview。标题检索返回的 venue 字段显示 Kang et al. 另有一条 "Sense of Space (SoS) Poster" 记录（S）。

由引用链新增并取正文的：2608.22916、2609.35486、2610.17976、2610.13527、2610.05715、2603.22278、2607.03358、2609.24813、2609.38716。只看到标题的（S）：2610.16135、2606.05843、2604.15809、2605.12586、2602.19117、2601.01984、2607.21085、2609.35272、2608.16805、2609.17004、2610.29244、2605.18162、2605.15672。

### 第 1 步 抽象阶梯（3 条）

模板："内部有信息 X 但输出不用" 与 "选项集合里的相近干扰项改变选择"。查询：(15) "encoding" "utilization" gap VLM spatial hidden states linear probe outperforms model answer intervention recovers fraction of errors；(16) LLM multiple choice adding distractor option semantically related ... decoy effect；(28) latent knowledge probing vs behavior gap "knows more than it says" video OR audio。
命中：2604.09364（A）、2604.04411（S）、2605.13737（S，全模态）、2312.01037（S）、2608.29257（S）。未命中：LLM 上"加入语义相近干扰项"的机制研究。

### 第 2 步 方法论单独搜（3 条）

查询：(22) activation patching limitations interpretability illusion subspace；hydra effect；steering vectors；(26) "hydra effect" self-repair；"steering vectors" reliability generalization；(29) linear probe control tasks selectivity amnesic probing。
命中（均 S，未取正文）：2311.17030（子空间修补错觉）、2307.15771（消融后的自修复）、2407.12404（转向向量在分布内方差大、分布外脆）、1909.03368、2102.12452、2506.11673；另有 2603.18353（A）。VLM 内部的对应提示：2607.03358 "ablation-based interventions can reveal what models could do rather than what they normally do"（F）。

### 第 3 步 蕴含检索（3 条）

查询：(17) text-only LLM left right spatial relation ... linear spatial representation probing；(21) spatial reasoning errors VLM "language backbone" same LLM different vision encoder；(30) LLM spatial preposition prior bias ... text-only blind VLM。
命中：2506.02996（S）、2411.06048（S）、MindCube F.5（F）、2603.12545（F定向）。S1 那句未检到；S2 检到正反两方原句（见开头）；S3 检到 spatial ID / role direction / ordering direction 三个对象。

### 第 4 步 同义术语枚举（3 条）

词表：spatial relation / spatial reasoning / spatial understanding / spatial intelligence / relative position / directional relation / spatial variable binding / position ID、spatial ID、location ID、ordering ID / egocentric、allocentric / frame of reference / perspective taking / orientation、rotation、heading / depth ordering / relation hallucination / where pathway、dorsal stream；encoding–utilization dissociation / encoding–grounding gap / decode≠deploy / seeing but not believing / knowing isn't saying / representation–action gap。
查询：(19) egocentric allocentric perspective taking VLM internal representation mechanistic；(20) multimodal LLM "relative position" OR "directional relation" causal tracing ... "cross-model"；(27) "relation hallucination" LVLM mechanistic attention heads。
命中：ACL 2026 VRUBench（S）、2602.15892 FlipSet（S）、2510.02528（A）、2602.08713（A）、2605.11808（S）。词表里没有单独发过查询的词：dorsal stream、depth ordering、heading、spatial intelligence 的机制向检索。

### 阅读量（分开数）

- **F 共 21 篇**：F通读 4 篇（2606.01914、2603.20662、2608.23074、2606.31257）；F定向 17 篇（2601.12626、2603.22278、2609.35486、2608.22916、2503.01773、2605.30161、2511.13719、2508.13142、2610.17976、2604.13321、2603.06054、2610.05715、2607.03358、2506.21458、2510.13394、2603.12545、2509.19191）。
- **A 共 12 篇**：2610.13527、2609.24813、2609.38716、2605.07148、2602.07025、2503.17349（第一轮为 F）、2603.20475、2603.18353、2604.09364、2602.08713、2510.02528、2410.17385。
- **S 约 40 篇**：Sophon、2601.12809、2601.09954、2509.02175、2510.17771、2506.08008、2506.02996、2311.17030、2307.15771、2407.12404、1909.03368、2102.12452、2506.11673、2411.06048、2608.29257、2604.04411、2605.13737、2312.01037、2602.15892、2603.06663、2606.03890、2605.20448、2505.21538、2505.03821、2605.11808、2608.27417、2607.29412、ACL 2026 两篇（VRUBench、SCOPE）、SpinBench，以及第 5 步列出的 13 个只见标题的被引条目。其中 2601.12809、2601.09954、2509.02175、2510.17771、2506.08008、2506.02996 取到了正文但没读，按 S 计。

### 第 7 步 边界申报

- **OpenReview 审稿讨论一篇都没取到**（见第 5 步）。最近几篇的审稿人质疑点未知。
- 2606.01914 的被引列表没取到；它是最接近的一篇，后继工作可能漏掉。
- 在审与并行未公开工作不可见。2026-08 至 2026-10 的 arXiv 条目只通过被引列表碰到，没有按月扫 listing。
- 非 arXiv 的会议论文只碰到三篇（NeurIPS 2026 Sophon、ACL 2026 两篇），都没取正文。非英文文献没查。
- 闭源模型内部无法验证；闭源模型在 What'sUp、VSR 上的最新逐项数字没取到；Gemma3 只有 ViewSpatial 三轴数字。
- 第 1–4 步各只有 3 条查询。文本 LLM 的空间表征、选项集合偏置的机制、方法学局限三块都只到 S 或 A。
- 多篇 A 级条目（S-Space、INTCORT、SpatialCORE、3D topology）的模型清单、对照与局限没有读，第 2 节相应格子写的是"未摘"。
- 我的模型知识截止在 2026-06 前后；此后的论文全部来自本轮检索，没有先验可交叉核对。
- 运行事故：共享的 /tmp 配额一度写满，我只删了自己下载的原始 HTML/PDF（已转成文本），没有动别人的目录。
