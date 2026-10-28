# 剂量语义与崩溃判据：七步查重报告

日期：2026-10-28（北京时间）。状态：**查重完成，未开新实验。** 查重对象是 10 月 28 日讨论中提出的下一阶段方向；检索与阅读由模型辅助完成，全部外部数字保留来源身份，不并入本项目实测。

本报告只写文献覆盖，不给等级、不给分数。novelty 判断等实验站稳后另写。

## 0. 结论先行

1. **"治疗窗 / 剂量律"作为主线已被做掉。** Liu（Palo Alto Networks，2026-06，[arXiv 2606.19831](https://arxiv.org/abs/2606.19831)）把单神经元剂量定义为预算 B = ‖r_L‖/‖v‖，与本项目 dose=1 的标定是同一单位；在 Qwen3.5-2B、Qwen3.5-4B、Llama-3.1-8B 等八种架构上各取 24 个随机神经元，报告崩溃落在 1.37–1.65 B（Gemma-3 为 0.31），提出"行为触发剂量低于崩溃上限才可控"的控制窗定律，并在 §7.3 做了撤针实验，把持续性归为上下文动量。
2. **"大剂量下输出与输入无关"的理论已发表。** Taimeskhanov 等（ICML 2026，[arXiv 2602.02712](https://arxiv.org/abs/2602.02712)）命题 4.1：α→±∞ 时 logits 收敛到 LN(±v)Wᵀ，与提示无关，交叉熵平台化；11 个模型验证，含 Qwen3-4B/8B、Gemma 3、GPT-2。
3. **对象层面仍空着三件事**（经 §8 复核后收窄）：早层是否存在额外脆弱性，以及它的机制归属；把"信息受损"与"输出被压制"分开的实测读数与逐层阈值；注入时段轴（提示对解码）对崩溃上限的影响。注意"用输入无关性当判据"本身已被 2602.02712 提出，不是空白。
4. 本项目 10 月 26 日的文献清单（`mechanistic-interventions-2026-10-26.json`）未收录本报告列出的任何一篇剂量相关工作。

## 1. 被查的主张

| 编号 | 主张（查重前的版本） |
|---|---|
| M1 | 每个（层，通道）有行为出现剂量 d_on 与上下文抹平剂量 d_erase，二者之间是治疗窗；早层窗口为零 |
| M2 | 可以用"输出对输入的依赖度"作为抹平指数，比相干性判据更早、更准地判崩溃 |
| M3 | 存在一种按层标定的剂量单位，使四模型的 d_erase(L) 曲线重合 |
| M4 | 干预诱发的循环分两类（针持续推动 / 错误历史支撑），可用同前缀无针参照区分，并据此中途撤针 |

## 2. 七步执行记录

共 22 条查询（20 条本轮，2 条前一会话），13 篇取到全文并做定向追问，4 篇只读摘要，其余只看标题与片段。

| 步 | 做法与查询数 | 主要命中 |
|---|---|---|
| 1 抽象阶梯 | 把主张写成"干预强度 × 深度 × 崩溃"模板，搜整类 steering（向量、SAE 特征、单神经元）；5 条 | 强度与相干性权衡是共识：倒 U 曲线（Bas & Novak，[2511.18284](https://arxiv.org/abs/2511.18284)）；Anthropic 2024 feature steering 的"sweet spot"；AxBench 报告早层概念分随强度先升后降、后层单调（[2501.17148](https://arxiv.org/abs/2501.17148)） |
| 2 方法论单独搜 | 残差范数标定、输入无关性指标、KL 相变；4 条 | 按残差范数比例标定已是通行做法：Wu 等 17 模型审计用 α = c‖h‖_ℓ（[2608.08159](https://arxiv.org/abs/2608.08159)）；Liu 用 B；CAA 原文明确不跨层归一化。"输出不再依赖输入"作为显式指标未找到，最接近的是 [2608.22985](https://arxiv.org/abs/2608.22985)（未读全文） |
| 3 蕴含检索 | 找能把我们结果变成推论的工作；4 条 | 2602.02712 命题 4.1 蕴含抹平；Liu 原文"超过上限后归一化残差被钉在 v̂ 上，与输入无关"；Yap 在 Qwen3.5-35B-A3B（GatedDeltaNet 混合架构）报告只在解码期注入未检出显著效应（d = −0.16/−0.20，p = 0.674/0.359，n = 50 场景），并据此主张行为承诺在 prefill 形成（[2603.16335](https://arxiv.org/abs/2603.16335)，表 5）；**这是单模型单行为族的零结果，不能读成"解码期注入普遍无效"**；层剪枝文献（Gromov 等 [2403.17887](https://arxiv.org/abs/2403.17887)）只蕴含"深层冗余"，不蕴含早层机制 |
| 4 同义术语 | coefficient / multiplier / magnitude / scaling factor / budget / dose / window / oversteering；3 条 | "dose–response""therapeutic window"措辞已被 Liu 与 Bhandari & Wade（[2609.06473](https://arxiv.org/abs/2609.06473)）使用；Yap 报告三种剂量响应形状 |
| 5 引用链 | 核心邻居的参考文献与被引；2 轮 | 前向：OpenAlex 对 2606.19831 与 2602.02712 被引均为 0（论文太新）；Semantic Scholar 限流未取到。后向：Liu 的上游是其扰动探针论文（[2604.27401](https://arxiv.org/abs/2604.27401)，FFN-to-skip ratio）、super weight（[2411.07191](https://arxiv.org/abs/2411.07191)）、CNA（[2605.12290](https://arxiv.org/abs/2605.12290)）、Kazemi 2026、Feucht 2026 |
| 6 对抗检索 | 显式问"什么能杀死它"；4 条 | 修复侧已有一族：HPR（[2409.10053](https://arxiv.org/abs/2409.10053)）、Angular Steering（[2510.26243](https://arxiv.org/abs/2510.26243)）、Selective Steering（[2601.19375](https://arxiv.org/abs/2601.19375)）、Minimizing Collateral Damage（[2605.01167](https://arxiv.org/abs/2605.01167)）。M4 的"历史支撑循环"是 Xu 等 2022 已证的自我强化效应（[2206.02369](https://arxiv.org/abs/2206.02369)）；Prefix Steering 证明短暂干预可长期延续（[2610.04967](https://arxiv.org/abs/2610.04967)）；Liu §7.3 已做撤针与强制开头对照 |
| 7 边界申报 | 见 §6 | |

## 3. 逐篇覆盖表

"读取程度"：全文定向 = 取到全文并针对本项目问题追问；摘要 = 只读摘要页；片段 = 只见标题与检索摘录。

| 论文 | 与本项目主张的关系 | 读取程度 |
|---|---|---|
| Liu, *Leverage Is Not Reach: A Control-Window Law for Single-Neuron Steering*, 2606.19831 | 覆盖 M1 主体；同一剂量单位；含 Qwen3.5-2B/4B；崩溃用 distinct-bigram 比值判定；验证集按相对深度 < 0.8 截断，正文无 L0–L2 条目；‖r_L‖ 在生成位置、通用文本上测一次；§7.3 撤针实验覆盖 M4 的概念；讨论中自列"剂量 × 注入时长 × 读出视界"为未测面 | 全文定向（§2、3.2、4.1、7.3、10 精读） |
| Taimeskhanov 等, *Towards Understanding Steering Strength*, 2602.02712, ICML 2026 | **覆盖范围比初版所述更广（2026-10-28 复核更正）**：正文图用中间层与最后一个 token，但附录 A.2 扫描多个 steering 层（含 Gemma-3-1B 的 layer 0 与 Mistral 的 layer 5/11），两处明确讨论"早层 steering 已知效果更差"，并引 Chen 等 2025；更关键的是它把"概率质量集中到少数 token，或输出变得实质上与提示无关"列为退化判据，定义 α* 为出现明显退化前的最大强度，并提出在 [0, α*] 内按交叉熵预算挑 α。因此"输入无关性作为判据"不是空白 | 全文定向 |
| Wu 等, *When Is a Steerable Concept Representation Real?*, 2608.08159 | 17 模型五家族审计"AI 神经科学"类比；强度按残差范数比例；指出"涌现"与"崩溃"都可能是工作点选择的产物；固定层 | 全文定向 |
| Yap, *Behavioral Steering in a 35B MoE… GatedDeltaNet*, 2603.16335 | 覆盖 M3/位置轴的先验：Qwen3.5 混合架构下 decode-only 零效应、prefill-only 有效；对象是行为不是崩溃 | 全文定向（摘要与表 5） |
| Khan 等, *Look Before You Steer*, 2609.22782 | SAE 特征可控性的几何预测；相干性崩溃作为过滤条件；Gemma-2/Llama-3.1/Qwen3 | 全文定向 |
| Aparin & Gaintseva, *Geometric Account… Angle–Norm Decomposition*, 2606.06735 | 七模型；概念在方向、范数控稳定性；严格保范在高强度下可能不稳 | 全文定向 |
| Nguyen 等, *Minimizing Collateral Damage*, 2605.01167 | 附带损伤的形式化与约束优化修复 | 全文定向（摘要） |
| Bas & Novak, 2511.18284 | 50 行为倒 U 曲线，更大数据允许更强系数 | 全文定向（摘要） |
| Lazaridis 等, *When Can One Neuron Fix Repetition Loops*, 2606.13705 | 自然循环的权重编辑修复，Gemma 4 主体、Qwen3.5 探索；不区分干预诱发与历史支撑 | 全文定向（摘要） |
| Dang & Ngo, *Selective Steering*, 2601.19375 | 保范旋转，困惑度阈值 2.0 作崩溃信号，8 模型三家族 | 全文定向（摘要） |
| Zhu & Zhu, *Prefix Steering*, 2610.04967 | 短暂干预可改变后续轨迹；剂量 × 时长的权衡 | 全文定向（摘要） |
| Shih 等, *When Does Activation Steering Change What a Model Computes From?*, 2606.29522 | 区分"改状态"与"偏置读出"；steering 向量范数为自然变化的 26–77 倍 | 全文定向（摘要） |
| Bhandari & Wade, 2609.06473 | 量化下的剂量响应与崩溃地板 | 全文定向（摘要） |
| McKenzie 等, *Endogenous Resistance*, 2602.06941 | 模型中途自行回到主题 | 摘要 |
| Cao 等, *Activation Steering Induces Emergent Misalignment*, 2606.08682 | 强度扫描下相干性骤降 | 摘要 |
| Billa, *Predicting Where Steering Vectors Succeed*, 2604.15557 | 逐层 logit-lens 可及性预测层选择 | 摘要 |
| Herbster 等, 2604.08169 | 只对低于阈值的 token 干预以保能力 | 摘要 |
| Wu 等, *AxBench*, 2501.17148 | 概念/指令/流畅三分评分与 14 档强度扫描 | 片段 |
| Da Silva 等, *Steering off Course*, 2504.04635；Tan 等, 2407.12404 | 跨模型可靠性 | 片段 |
| Pham & Nguyen, HPR, 2409.10053；Vu & Nguyen, Angular, 2510.26243 | 保范修复 | 片段 |
| Xu 等, *Learning to Break the Loop*, 2206.02369；Hiraoka & Inui, 2410.13497；2505.13514 | 重复的自我强化、重复神经元、induction head | 片段 |
| Yu 等, *Super Weight*, 2411.07191 | 早层 down_proj 单权重，移除后停止词概率飙升 | 片段 |
| Liu 等, *Perturbation Probing*, 2604.27401 | Liu 定律的上游；FFN-to-skip ratio | 片段 |

## 4. 覆盖图

**已被覆盖，不能作为主张：**

- 剂量按残差范数标定、可控窗口存在、崩溃约在 1.5 B（Liu；Wu 等；多篇实践）。
- 大剂量下输出与输入无关的机制（2602.02712 理论；Liu 文字陈述）。
- 撤针后行为回落、持续性来自已生成上下文（Liu §7.3；Prefix Steering；Xu 2022）。
- 保范数的修复方案（HPR、Angular、Selective、Collateral Damage）。
- 混合架构里行为承诺在 prefill 形成（Yap）。
- "脑区类比需要可比测量和对照"的方法论批评（Wu 等整篇）。

**部分覆盖：**

- 早层 steering 效果差、输出偏离概念：2602.02712 附录、AxBench、Chen 等 2025 均有观察，但都没有把它解释为抹平或给出逐层阈值。

**对象层面空着：**

1. **崩溃系数的深度依赖。** Liu 称 m* 对深度"依赖较弱"，验证集截断相对深度 < 0.8，正文具名神经元最浅为 L8，24 个随机神经元的层分布未在正文给出。本项目数据（见 `experiments/early-layer-question-dependence-v1-2026-10-28/`）：Qwen3.5-4B 的 L0 十个随机通道九个在 dose=1 全题首步 EOS，9B L0 的一个通道在 +0.25 已 7/8 首步 EOS，L3 以后 dose=1 多数仍保留题目依赖。**但这不构成与 Liu 的数值差异**：1.37–1.65 是模型内平均崩溃系数（模型内 R² 0.40–0.97，通道间离散），不是逐通道界线；两边的 ‖r_L‖ 口径与注入位置也不同。空着的是"早层是否存在额外脆弱性"这个问题本身，而不是一个已测出的冲突数字。
2. **崩溃的判据。** Liu 用 distinct-bigram 比值，并把"流畅但离题"算作未崩溃，对单 EOS token 输出无法评分。本项目有两类它看不见的崩溃：Llama 早层流畅的模板回声；Qwen 早层首步空答。2602.02712 已把输出的提示无关性列为退化判据并给出 α* 配方，**所以空着的不是这个概念**，而是：实测的逐层阈值；跨题一致性读数（其交叉熵按固定上下文逐条估计，没有跨题目指标）；以及把"信息受损"与"输出被压制"分开的读数。首 token 种数不足以承担这个角色，本项目同点 +0.5 下八题同首 token 却分成两题循环、六题立即结束，说明残余的题目依赖仍在。
3. **注入位置轴。** Liu 自列为未测；Yap 证明 prefill 承诺但未碰崩溃。本项目注入覆盖全部提示位置，Liu 的预算以生成位置范数定义，这是 1.0 对 1.65 差异最可能的来源。

## 5. 青蒿素判读

转化本身算贡献；问题只有"做出来谁会改做法"。

- 用 Liu 配方做可控性审计的人：早层需要换上限，否则把抹平误判为有窗口。
- 用 lyra、mfstuff 等工具在 Qwen3.5 上找神经元的人：剂量要按注入位置和层深分开定；解码期注入在这类架构上可能是空操作。
- 做强度理论的人：第一份跨题目、逐层的输入依赖实测。

因此下一阶段不能再以"发现治疗窗"立项；可以立项的是**造出覆盖全深度的剂量单位、看得见输入失明的崩溃判据、以及可直接使用的安全剂量上限表**，Liu 的中后层数据作为新单位必须同时拟合的验收条件。具体见 [下一阶段建议](../next-stage-dose-calibration-proposal-2026-10-28.zh-CN.md)。

M4（两类循环）不再单独立项：概念被 Liu §7.3 与 Xu 2022 覆盖，剩余价值只在"干预诱发循环的在线分类与剂量调度"这一工程转化，并入上限表的崩溃类型列。

## 6. 边界申报

- 未覆盖在审稿件、非 arXiv、非英文与并行未公开工作。
- Semantic Scholar 限流，前向引用链只靠 OpenAlex；两篇核心论文被引为 0，不能据此说无人跟进。
- [2608.22985](https://arxiv.org/abs/2608.22985) 可能含与输入依赖相关的指标，未读全文。
- Liu 的随机神经元层分布未在正文找到，"早层未覆盖"是从正文零命中推断的；开工前必须读其附录或代码。
- 口径差异未摊平：Liu 的 ‖r_L‖ 取生成位置、通用文本；本项目取各题提示位置中位数、排除首 token，并在全部提示位置注入。在摊平前，"1.0 对 1.65"只能登记为待核对的差异，不能登记为矛盾。
- 模型知识截止早于这些论文，全部依据来自本次检索（2026-10-28）。

## 7. 查询日志

本轮 20 条（WebSearch，extended 为主）：
1. activation steering coefficient selection normalized by residual stream norm layer-wise strength scaling
2. steering vector strength sweep coherence fluency degradation trade-off large magnitude incoherent output
3. AxBench steering benchmark concept score instruct fluency factor sweep SAE features neurons prompting
4. angular steering rotation activation space norm-preserving steering avoids degeneration
5. Householder pseudo-rotation activation steering norm preserving coherence
6. "Steering Off Course" reliability steering vectors across models layers
7. Anthropic evaluating feature steering capability degradation steering strength sweet spot
8. single neuron steering LLM amplify suppress MLP neuron dose degeneration empty output repetition
9. steering intervention output becomes independent of prompt "mode collapse" / "prompt-independent" KL phase transition
10. massive activations early layers residual stream dominated by token embedding perturbation all positions attention sink collapse EOS
11. "over-steering" threshold coherence collapse coefficient calibration across layers and models
12. repetition loop mechanism self-reinforcement in-context repetition clean model prefers continuing repeated prefix "repetition neurons"
13. steering applied only during generation vs prompt tokens vs all positions removing steering mid-generation recovery
14. steering "intervention magnitude" / "edit strength" / "scaling factor" relative hidden state norm calibration across layers
15. layer pruning early layers critical later layers redundant "unreasonable ineffectiveness of the deeper layers"
16. neuron steering "therapeutic window" / "usable range" dose-response behavior onset vs breakdown per neuron
17. "Learning to Break the Loop" repetition self-reinforcement
18. activation steering metric "input sensitivity" / "prompt sensitivity" / "prompt-blind" steered outputs identical across prompts
19. "Perturbation probing" two-pass-per-prompt FFN behavioral circuits FFN-to-skip ratio
20. steering Qwen3.5 / Qwen3-Next GatedDeltaNet hybrid activation steering early layers prefill decode

前一会话 2 条：super weight 单权重与停止词概率；activation steering early layers degenerate output EOS。

## 8. 更正记录（2026-10-28 第二版）

一轮外部审阅后对三篇核心论文复核，更正本报告自身的四处过强表述。覆盖判断随之收紧，结论方向不变。

| 初版说法 | 更正 |
|---|---|
| 2602.02712 只在中间层、只对最后一个 token 注入 | 错。附录 A.2 扫描多层含 layer 0，两处讨论早层；并已把"输出实质与提示无关"列为退化判据、给出 α* 与交叉熵预算配方。"输入依赖判据概念空白"不成立 |
| 本项目 ≤1 B 与 Liu 1.65 B 构成同模型同单位的差异 | 不成立。1.65 为模型内平均（R² 0.40–0.97），非逐通道界线；两边范数口径与注入位置不同。降级为待摊平的口径问题 |
| Yap 证明解码期注入效应为零 | 错。单模型单行为族的零结果（p = 0.674/0.359），属"没拿到结果"，只支持增加时段对照 |
| 空白为"输入依赖判据" | 收窄为：实测的逐层阈值、跨题一致性读数、信息受损与输出压制的分离读数 |

仍然成立的部分：Liu 覆盖了剂量单位、窗口概念与撤针对照；2602.02712 覆盖了大剂量极限理论；修复侧已有保范一族；M4 概念被覆盖。因此"治疗窗/剂量律"仍不能作为主线立项。
