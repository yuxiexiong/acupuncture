# 022．旧回答再分析：输出还随题目变化吗

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-10-28；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

不重新推理，读取四模型已保存回答，统计同一点八题的不同首token数、前三token前缀数、首步EOS、机械重复和完全相同输出。

**实际过程、结果与后来更正**

这是CPU旧数据分析。完整逐层、逐剂量数字在outputs记录中；前缀多样性描述输出变化，不能替代回答正确率。原文中的指标定义和解释原样保留。

**来源身份**：`early-layer-question-dependence-v1-2026-10-28`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：剂量语义与崩溃判据：七步查重报告

原路径：`docs/literature/dose-calibration-related-work-audit-2026-10-28.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/literature/dose-calibration-related-work-audit-2026-10-28.zh-CN.md) · [单独阅读副本](../library/8300ffea5e36b93d.md)；SHA-256：`8300ffea5e36b93d7666f1ec0955f93cd90922b1bfefc32d636ff20b6a1519d5`。

---

#### 剂量语义与崩溃判据：七步查重报告

日期：2026-10-28（北京时间）。状态：**查重完成，未开新实验。** 查重对象是 10 月 28 日讨论中提出的下一阶段方向；检索与阅读由模型辅助完成，全部外部数字保留来源身份，不并入本项目实测。

本报告只写文献覆盖，不给等级、不给分数。novelty 判断等实验站稳后另写。

##### 0. 结论先行

1. **"治疗窗 / 剂量律"作为主线已被做掉。** Liu（Palo Alto Networks，2026-06，[arXiv 2606.19831](https://arxiv.org/abs/2606.19831)）把单神经元剂量定义为预算 B = ‖r_L‖/‖v‖，与本项目 dose=1 的标定是同一单位；在 Qwen3.5-2B、Qwen3.5-4B、Llama-3.1-8B 等八种架构上各取 24 个随机神经元，报告崩溃落在 1.37–1.65 B（Gemma-3 为 0.31），提出"行为触发剂量低于崩溃上限才可控"的控制窗定律，并在 §7.3 做了撤针实验，把持续性归为上下文动量。
2. **"大剂量下输出与输入无关"的理论已发表。** Taimeskhanov 等（ICML 2026，[arXiv 2602.02712](https://arxiv.org/abs/2602.02712)）命题 4.1：α→±∞ 时 logits 收敛到 LN(±v)Wᵀ，与提示无关，交叉熵平台化；11 个模型验证，含 Qwen3-4B/8B、Gemma 3、GPT-2。
3. **对象层面仍空着三件事**（经 §8 复核后收窄）：早层是否存在额外脆弱性，以及它的机制归属；把"信息受损"与"输出被压制"分开的实测读数与逐层阈值；注入时段轴（提示对解码）对崩溃上限的影响。注意"用输入无关性当判据"本身已被 2602.02712 提出，不是空白。
4. 本项目 10 月 26 日的文献清单（`mechanistic-interventions-2026-10-26.json`）未收录本报告列出的任何一篇剂量相关工作。

##### 1. 被查的主张

| 编号 | 主张（查重前的版本） |
|---|---|
| M1 | 每个（层，通道）有行为出现剂量 d_on 与上下文抹平剂量 d_erase，二者之间是治疗窗；早层窗口为零 |
| M2 | 可以用"输出对输入的依赖度"作为抹平指数，比相干性判据更早、更准地判崩溃 |
| M3 | 存在一种按层标定的剂量单位，使四模型的 d_erase(L) 曲线重合 |
| M4 | 干预诱发的循环分两类（针持续推动 / 错误历史支撑），可用同前缀无针参照区分，并据此中途撤针 |

##### 2. 七步执行记录

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

##### 3. 逐篇覆盖表

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

##### 4. 覆盖图

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

##### 5. 青蒿素判读

转化本身算贡献；问题只有"做出来谁会改做法"。

- 用 Liu 配方做可控性审计的人：早层需要换上限，否则把抹平误判为有窗口。
- 用 lyra、mfstuff 等工具在 Qwen3.5 上找神经元的人：剂量要按注入位置和层深分开定；解码期注入在这类架构上可能是空操作。
- 做强度理论的人：第一份跨题目、逐层的输入依赖实测。

因此下一阶段不能再以"发现治疗窗"立项；可以立项的是**造出覆盖全深度的剂量单位、看得见输入失明的崩溃判据、以及可直接使用的安全剂量上限表**，Liu 的中后层数据作为新单位必须同时拟合的验收条件。具体见 [下一阶段建议](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/next-stage-dose-calibration-proposal-2026-10-28.zh-CN.md)。

M4（两类循环）不再单独立项：概念被 Liu §7.3 与 Xu 2022 覆盖，剩余价值只在"干预诱发循环的在线分类与剂量调度"这一工程转化，并入上限表的崩溃类型列。

##### 6. 边界申报

- 未覆盖在审稿件、非 arXiv、非英文与并行未公开工作。
- Semantic Scholar 限流，前向引用链只靠 OpenAlex；两篇核心论文被引为 0，不能据此说无人跟进。
- [2608.22985](https://arxiv.org/abs/2608.22985) 可能含与输入依赖相关的指标，未读全文。
- Liu 的随机神经元层分布未在正文找到，"早层未覆盖"是从正文零命中推断的；开工前必须读其附录或代码。
- 口径差异未摊平：Liu 的 ‖r_L‖ 取生成位置、通用文本；本项目取各题提示位置中位数、排除首 token，并在全部提示位置注入。在摊平前，"1.0 对 1.65"只能登记为待核对的差异，不能登记为矛盾。
- 模型知识截止早于这些论文，全部依据来自本次检索（2026-10-28）。

##### 7. 查询日志

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

##### 8. 更正记录（2026-10-28 第二版）

一轮外部审阅后对三篇核心论文复核，更正本报告自身的四处过强表述。覆盖判断随之收紧，结论方向不变。

| 初版说法 | 更正 |
|---|---|
| 2602.02712 只在中间层、只对最后一个 token 注入 | 错。附录 A.2 扫描多层含 layer 0，两处讨论早层；并已把"输出实质与提示无关"列为退化判据、给出 α* 与交叉熵预算配方。"输入依赖判据概念空白"不成立 |
| 本项目 ≤1 B 与 Liu 1.65 B 构成同模型同单位的差异 | 不成立。1.65 为模型内平均（R² 0.40–0.97），非逐通道界线；两边范数口径与注入位置不同。降级为待摊平的口径问题 |
| Yap 证明解码期注入效应为零 | 错。单模型单行为族的零结果（p = 0.674/0.359），属"没拿到结果"，只支持增加时段对照 |
| 空白为"输入依赖判据" | 收窄为：实测的逐层阈值、跨题一致性读数、信息受损与输出压制的分离读数 |

仍然成立的部分：Liu 覆盖了剂量单位、窗口概念与撤针对照；2602.02712 覆盖了大剂量极限理论；修复侧已有保范一族；M4 概念被覆盖。因此"治疗窗/剂量律"仍不能作为主线立项。

---

### 原件 2：下一阶段建议：全深度剂量单位、输入依赖崩溃判据与安全剂量上限表

原路径：`docs/next-stage-dose-calibration-proposal-2026-10-28.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/next-stage-dose-calibration-proposal-2026-10-28.zh-CN.md) · [单独阅读副本](../library/ecc1988d9dd4a580.md)；SHA-256：`ecc1988d9dd4a5806c90e1a4f70cedefb931149da42f5d645ab8ba30795b5315`。

---

#### 下一阶段建议：全深度剂量单位、输入依赖崩溃判据与安全剂量上限表

日期：2026-10-28（北京时间）。状态：**建议稿，未冻结合同，未授权运行。** 依据为本仓库既有 18,272 份单针回答、7,632 条内部轨迹的零 GPU 再分析（脚本与输出见 [experiments/early-layer-question-dependence-v1-2026-10-28/](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-layer-question-dependence-v1-2026-10-28)）与 [七步查重报告](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/literature/dose-calibration-related-work-audit-2026-10-28.zh-CN.md)。

全文按三档标注：**推导**（有论证链）、**类比**（有邻域证据，跨域未验证）、**推测**（需独立验证）。

##### 0. 一句话

早层扎针后的空答与循环不是"语言组织区"受损。**重点假设**是：早层干预使模型难以有效利用题目信息。现有证据支持这个假设，**不足以认定上下文已被抹平**，也不足以直接开全模型统一剂量定律的大扫描。

下一阶段先造一件东西并回答一个问题：

- **仪器**：把"信息受损"与"输出被压制"分开的事实响应读数（§3.1）。
- **问题**：在控制实际干预强度与注入时段后，早层是否仍更容易失去对题目关键事实的响应；若是，原因是信息受损还是输出被压制。

统一剂量单位与安全剂量上限表是这些测量**可能**得到的结果，不是必须得到的答案；即便某种归一化能把已有曲线拉平，也要在未参与拟合的层、通道与题目上预测成功才算规律。本线是对 Liu（[2606.19831](https://arxiv.org/abs/2606.19831)）控制窗定律在深度与时段两轴上的延伸，不是证伪。

##### 1. 为什么换方向：早层现象的再解读

###### 1.1 现有数据说了什么

对每个（模型，层，通道，+1）条件，数八道题干预后回答的**不同首 token 数**。原版八题首 token 各不相同（8 种）。若只剩 1 种，说明输出已不依赖题目。

| 层 | 2B：八题同首 token 的通道数 /10 | 4B | 9B | Llama-3.1-8B |
|---|---:|---:|---:|---:|
| L0 | 5 | 9 | 9 | 2 |
| L1 | 1 | 7 | 5 | 0 |
| L2 | 3 | 3 | 6 | 0 |
| L3 | 1 | 0 | 6 | 0 |
| L4–L7 | 0–1 | 0–1 | 3–4 | 0 |
| L11 以后 | 0 | 0 | 0 | 0 |

9B 的 L0 有 4 个通道八题完整输出逐字相同且不是空答（整篇"托托托"、"StackStack"、"映映映"、纯换行）；换通道换一个固定词，换题目不变。4B L0 十个随机通道九个 8/8 首步 EOS。剂量阶梯上两个点的形态并不相同，**不存在统一的 0.5→1 阈值**。4B L0 N4146：−0.5 到 +0.5 保持 5–8 种首 token，±1 降到 1 种。9B L0 N978：+0.25 已有 7/8 题首步 EOS、首 token 只剩 2 种，−0.5 已是 8/8 首步 EOS，而 +0.5 反而没有首步 EOS。同一点正负两侧的失稳形态也不同：−1 是首步结束，+1 是 128 token 的"托"循环。因此既不能按 |d| 排单调阈值，也不能称正负对称。深层对照：L20 以后 ±1 多数仍保持 8 种首 token，坏在内容而不是坏在"不看题"。

另一处必须保留的反例：9B L0 N978 的 +0.5 八题首 token 全是"托"，但其中两题重复到 128 token、其余六题"托"后立即结束。**相同首 token 下题目仍在影响后续行为**，所以首 token 种数只是粗筛，不能当输入依赖程度的度量。

Llama 早层没有首步 EOS，但 L0–L1 八题首 token 中位数只剩 3 种（基线 7 种），内容是模板回声、系统日期、"答案："、编号列表：句子组织完好，丢的是输入。

###### 1.2 读法

- **推导（已收窄）：早层的写入相对残差更大，因而更容易让下游难以利用题目信息。** 剂量按该层残差范数中位数标定。4B 在 L0–L2 的 attention 与 MLP 输出范数只有 0.5–1.2，残差 2.1–2.3，残差几乎就是 token embedding。下游每个模块都在 RMSNorm 之后读残差，归一化丢弃幅度只留方向；同一个常向量 c 加到所有位置后，各位置的方向都向 ĉ 收拢，位置间角度差被压缩。这与 Liu 的 cos θ_v 坐标、2602.02712 的 LN(±v)Wᵀ 极限是同一套几何，不是新机制。
- **方向收拢不等于信息已被抹掉。** 同一个输出也可能是题目信息仍在残差里，只是 EOS 或某个循环 token 被推得过强、压住了正常答案。通道无关（4B L0 十点九个 8/8）、符号无关（±1 都失稳）、输出变成通道决定的常数，这三条与两种机制都相容，不能单独判定哪一种。有限剂量下压缩到何种程度、哪一环不再可用，必须另测，判别设计见 §3.1。
- **类比：空答是 Qwen 模板下"没有内容时的默认输出"。** Qwen 提示以空 think 块结尾，抹平后首选变成 `<|im_end|>` 或重开 `<think>`；Llama 没有这个结构，吐出的是模板回声。两个模型差的是默认输出，不是脆弱性。
- **推测：抹平持续到哪一层由残差里 embedding 以外成分的占比决定。** 2B/4B 在 L3（第一层全注意力）骤停，9B 延续到 L7–L10，"第一层全注意力之前"的规律在 9B 不成立，不采用。

###### 1.3 与已发表结果的关系

Liu 用 B = ‖r_L‖/‖v‖ 报告崩溃在 1.37–1.65 B，其中 Qwen3.5-4B 为 1.65。**这是模型内的平均崩溃系数，不是逐通道的统一界线**：其模型内 R² 为 0.40–0.97，通道间离散度相当大。其 ‖r_L‖ 取通用文本的生成位置，本项目取各题提示位置中位数并在全部提示位置注入。因此"本项目 ≤1、Liu 1.65"**目前不构成差异证据**，只构成一个必须先摊平的口径问题。

Yap（[2603.16335](https://arxiv.org/abs/2603.16335)）在 Qwen3.5-35B 混合架构上报告只在解码期注入未检出显著效应（d = −0.16/−0.20，p = 0.674/0.359，n = 50 场景）。这是**单一模型、单一行为族、两个剂量下的零结果**，按本项目的失败分型属于"没拿到结果"，不是"解码期注入普遍无效"的证明。它支持把注入时段作为对照轴，不能替实验预定结果。

##### 2. 主体贡献：造出来的三样东西

1. **一个仪器：输入依赖崩溃判据。** 对任意干预（原生神经元、SAE 特征、均值差向量），在固定题池上测干预后输出对输入的依赖度，给出崩溃剂量。替代 distinct-bigram 比值与 LLM 评委，能抓住空答和"流畅但对输入失明"两类现有判据看不见的崩溃。

   **与已发表工作的边界（2026-10-28 复核后收窄）**：2602.02712 已把"输出变得实质上与提示无关"明确列为退化判据之一，并提出在 [0, α*] 内按交叉熵预算挑 α 的配方。因此"用输入无关性当崩溃判据"**不是概念空白**。仍然空着的是两件具体的事：实测的逐层阈值；跨题一致性读数（他们按固定上下文逐条画交叉熵，没有跨题目的一致性或事实响应指标）。本仪器的落点因此从"提出判据"改为"把判据做成可测量、能分辨信息受损与输出压制的读数"。
2. **一个单位：让崩溃阈值在全部层与注入位置上成为常数的剂量标定 B'(L, 注入位置)。** 三个预注册候选：去掉 embedding 分量后的残差范数；下一层 attention 输入的范数；按注入位置数加权的残差范数。由数据选，选出后一个剂量数字在 L0 与 L20、在 Qwen 与 Llama 之间才真正可比。
3. **一张表：四模型全层安全剂量上限，以及按它重评的 22 个公开配方**（lyra 与 Abhinav 的坐标）。这是给工具使用者直接拿去用的。

Liu 的 1.65 对本项目的 ≤1.0 只作为第 2 项的动机与验收：新单位必须让他的中后层数据和本项目的早层数据落在同一常数上。揭示的缺口只出现在动机段，主体是仪器、单位与表。

##### 3. 三条主张与现状

| 主张 | 档位 | 现有证据 | 杀死它的观测 |
|---|---|---|---|
| A. 控制实际强度与注入时段后，早层仍更容易失去对题目关键事实的响应 | 推导 | §1.1 表；深层 ±1 保持题目依赖；但"早层 steering 效果更差"本身已是公开结果（AxBench、2602.02712 附录两处），所以只有带机制归属才算贡献 | 同范数随机方向在早层给出相同阈值与相同四格归属 |
| A′. 存在一种剂量单位使阈值跨深度恒定 | 推测 | 尚无证据；是可能的结果，不是必须得到的答案 | 三个候选单位都不能在未参与拟合的层、通道、题目上预测成功 |
| B. 输入依赖判据比相干性判据更早触发，并覆盖空答与模板回声 | 推导 | 问题依赖度全层剖面；Llama 早层流畅回声 | 两判据在全部层给出相同上限 |
| C. 早层崩溃是 prefill 位置现象 | 类比 | Yap 表 5；本项目全提示位置注入 | 只解码注入在早层仍 ≤1.0 B 崩溃 |

###### 3.1 判别仪器：事实响应二维分解

首 token 种数只作粗筛。主读数改为配对事实题上的两项量，二者组合成四格判读：

- **事实边际**：对配对题 A 与 A′（只差一个关键事实，正确答案必须不同），在答案提交位置上取两个事实依赖答案 token 的 logit 差。边际保住，说明残差里还分得清这个事实。
- **压制量**：最佳停止 token 与最佳循环 token 对这两个答案 token 的 logit 优势。优势为正，说明正常答案被压住。

| | 事实边际保住 | 事实边际≈0 |
|---|---|---|
| **停止/循环未胜出** | 完好 | 信息受损 |
| **停止/循环胜出** | 输出被压制 | 两者同时发生 |

四格都要能在预演里被满足和不被满足（合同冻结前的离线演示）。这组读数只用 logits，不依赖语义评委，也不用首词或流畅度代判；它可以复用既有的同前缀无针参照机械，并且是本线真正要交付的仪器。

##### 4. 三个合同（建议顺序）

###### 合同 1：先分辨机制，不先追曲线；约 8–13 worker 小时

规模与成本按本仓库自身收据实测：十点扫描 7,064 份生成耗 7.636 worker 小时（约 925 份/worker 小时，9B 最慢），正负剂量阶段为 1,189–1,414 份/worker 小时。**原稿"约 2 GPU 小时"按此口径核算差约 40 倍，已作废。** 原设计（2 模型 × 6 层 × 10 通道 × 7 档 × 3 时段 × 30 题）是 75,600 份生成，约 84 worker 小时，加随机臂翻倍，双卡约 3.5 天。现按"先分辨机制"重新定规模：

| 轴 | 取值 | 数 |
|---|---|---:|
| 模型 | 4B、9B | 2 |
| 层 | L0、L1、L3（首个全注意力层）、L20（深层对照） | 4 |
| 通道 | 既有十点中取 3–4 个，身份不变 | 3–4 |
| 注入时段 | 提示除末位 / 末位＋解码 / 全部位置（原版基线已有，不重跑） | 3 |
| 题目 | 6 对"改一个关键事实、答案必须随之改变"的配对题 | 12 |
| 剂量 | 二分搜索定阈值，每格 4–5 探 | 4–5 |
| 对照 | 等范数随机高斯方向，同网格 | ×2 |

合计 6,912–11,520 份生成，约 8–13 worker 小时，双卡约 4–7 小时墙钟。剂量用二分搜索而非固定阶梯，所以该计数是上界。**对照臂排队首。**

时段切分必须写死：第一个回答 token 由最后一个提示位置预测，所以"只读题时扎"必须排除最后一个提示位置，否则与"只生成时扎"边界含混。三臂的位置集合分别为 {提示除末位}、{末位}∪{解码}、全部。

预注册的不是"Liu 对不对"，而是 §3.1 四格判读里每个格子的归属，以及三个候选单位中哪一个让早层与深层对照的阈值重合。停止条件：若随机方向臂在早层给出与原通道相同的阈值与相同的四格归属，则"通道特异性"不成立，本线只保留判据与剂量上限两项交付。

###### 合同 2：深度分辨的崩溃律，约 6 GPU 小时

- 四模型全部 32（24）层、每层十通道，剂量阶梯在 0.5–2.0 B 之间加密，得到 m*(L)。
- 同时计算每层残差的参与比 PR(r_L)，检验 Liu 的解释能否预测早层的低 m*。
- 预测：早层 m* 随深度单调上升至 L3 附近饱和；新单位下 m*(L) 平坦。平坦则定律成立；不平坦则交付单模型标定表，论文卖点改为判据。

###### 合同 3：判据对比与处方，0–1 GPU 小时

- 用合同 2 数据比较两种判据的上限差；产出每模型每层的安全剂量上限表；按它重评 22 个公开坐标；给出崩溃类型列（首步 EOS / 常数 token 循环 / 特殊标记循环 / 模板回声 / 流畅离题）。

所有合同按 6.1–6.7 执行：冻结前离线预演两种判据能通过也能不通过（4B L0 N4146 的 +0.5 与 +1 是现成的一正一反）；零假设用随机方向臂标定；预测先写后看；偏离记账；失败分型。

##### 5. 零 GPU 先做

- 读 Liu 的代码与附录，确认其随机神经元的层分布与注入位置；能复用其代码就不自写。
- 把问题依赖指标正式化：题池换成未读过的新题，报告跨题 KL 与首 token 多样性两种读数。
- 从归档轨迹算**注入层**逐位置的"与写入方向的夹角"。归档只存了每站点每位置的 clean/steer 范数、差分范数与 cos(clean_i, steer_i)，**不能恢复不同位置之间的向量关系**；但在注入层，扰动是同一个已知常向量 c，三角形被完全钉住：由 a=‖clean_i‖、b=‖steer_i‖、d=‖c‖ 与 cos(clean_i, steer_i) 可解出 cos(clean_i, c) = (b·cos − a)/d。于是能算出每个提示位置到 ĉ 的角度，并用 max 两两夹角 ≤ θ_i + θ_j 给出位置间角度差的**上界**。这只是单边约束（能证明"都快平行了"，不能证明"还很分散"），且只在注入层成立，下游层的差分不再是已知常向量。
- 用 Liu 的范数口径重算现有剂量阶梯的 B 值，看 1.0 对 1.65 的差异有多少可由口径解释。

##### 6. 停掉、降级、搁置

- 脑区作为论文主张：停。可留在动机段。
- 三维图作为证据：停。保留为浏览工具。
- 两类循环（针推动 / 历史支撑）：不单独立项，并入上限表的崩溃类型列；撤针与历史动量已被 Liu §7.3 与 Xu 等 2022 覆盖。
- 跨家族迁移第二阶段、十个修复候选：搁置，待上限表出来后决定是否在正确剂量下重做。

##### 7. 风险与退路

- 最大风险：Liu 附录或代码已覆盖早层且口径一致。此时主张 A 降为复现，退路不是缩题，而是主张 B 与 C 单独成立：输入依赖判据和位置轴在其论文中确实没有。
- 次要风险：四模型 m*(L) 互不相似。此时交付单模型标定表与判据。
- 口径风险：在摊平前，"1.0 对 1.65"只登记为待核对差异，不写成矛盾。

##### 8. 改做法的人

- 用 Liu 配方做可控性审计的人：早层要换上限。
- 在 Qwen3.5 上用 lyra、mfstuff 工具找针的人：剂量按注入位置与层深分开定；解码期注入可能是空操作。
- 做强度理论的人：第一份跨题目、逐层的输入依赖实测。

##### 9. 依据

- 原始回答：`experiments/layer-survey-toy-v1-2026-10-27/delivery-r01/all.records.jsonl`、`experiments/layer-negative-dose-survey-toy-v1-2026-10-27/delivery-r01/all.records.jsonl`、`experiments/llama31-layer-survey-v1-2026-10-28/delivery-r01/all.records.jsonl`、`experiments/llama31-single-point-dose-survey-v1-2026-10-28/delivery-r01/all.records.jsonl`。
- 轨迹统计：`experiments/layer-trace-extension-v1-2026-10-28/analysis-early-r01/summary.json`。
- 再分析脚本与输出：`experiments/early-layer-question-dependence-v1-2026-10-28/`。
- Qwen3.5 层型（HF main 配置，非冻结 revision）：2B/4B/9B 均为 full_attention_interval=4，L3、L7、L11… 为全注意力，其余为 GatedDeltaNet。

##### 10. 更正记录（2026-10-28 第二版）

本版按一轮外部审阅与原始数据复核改写。更正的是本文档自身的错误，不是实验结果。

| 原稿说法 | 更正 |
|---|---|
| ±0.5 以内保留题目差异、±1 才崩，正负对称 | 不成立。9B L0 N978 在 +0.25 已 7/8 首步 EOS、−0.5 已 8/8，而 +0.5 无首步 EOS；−1 与 +1 的失稳形态不同。无统一阈值，不对称 |
| 八题首 token 相同即"输出不再依赖题目" | 过强。同点 +0.5 下八题同首 token，但两题循环、六题立即结束；题目仍影响后续行为。首 token 种数降为粗筛 |
| 早层 dose=1 等价于抹平上下文 | 收窄为"更容易让下游难以利用题目信息"。相同输出可由信息受损或输出被压制产生，现有证据不能分辨 |
| 2602.02712 只在中间层、只对最后一个 token 注入 | 错。其附录 A.2 扫描多个层含 layer 0，并两处明确讨论早层偏离；更关键的是它已把"输出实质与提示无关"列为退化判据并给出 α* 配方。本文档原称"输入依赖判据空白"过强 |
| 本项目 ≤1 B 与 Liu 1.65 B 构成差异证据 | 不成立。1.65 是模型内平均（R² 0.40–0.97），非逐通道界线；两边范数口径不同。降级为待摊平的口径问题 |
| Yap 证明解码期注入零效应 | 错。是单模型单行为族的零结果（p = 0.674/0.359），属"没拿到结果" |
| 合同 1 约 2 GPU 小时 | 错约 40 倍。原网格为 75,600 份生成、约 84 worker 小时。已按实测吞吐重新定规模为 6,912–11,520 份、8–13 worker 小时 |
| 零 GPU 可从归档轨迹算逐位置塌陷 | 部分错。归档不含位置间向量关系；仅在注入层可由已知常向量反解每位置与写入方向的夹角，给出位置间角度差的单边上界 |
| 主线必须产出全层安全剂量上限表 | 降级。上限表只覆盖实测到的层与通道，统一剂量单位列为可能结果而非必须结果 |

---

### 原件 3：早层问题依赖度：既有单针回答的零 GPU 再分析

原路径：`experiments/early-layer-question-dependence-v1-2026-10-28/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-layer-question-dependence-v1-2026-10-28/README.zh-CN.md) · [单独阅读副本](../library/3b95bf14367f4ca9.md)；SHA-256：`3b95bf14367f4ca95c39a55aa62b4048d34e6af592bdd09544314684c4fb794f`。

---

#### 早层问题依赖度：既有单针回答的零 GPU 再分析

日期：2026-10-28。状态：**ANALYZED，只读既有归档，无新推理。** 本目录支撑 [下一阶段建议](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/next-stage-dose-calibration-proposal-2026-10-28.zh-CN.md) §1 与 [查重报告](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/literature/dose-calibration-related-work-audit-2026-10-28.zh-CN.md) §4 中引用的全部数字。

##### 测量定义

- **问题依赖度**：同一（模型，层，通道，剂量）下八道题回答的不同首 token 数，以及不同前 3 token 前缀数。原版为 8/8。1/1 表示输出已不依赖题目。
- **首步 EOS**：生成长度 1 且结束原因为 EOS。
- **机械重复**：重复出现的 token 四元组占比 ≥50%，沿用既有脚本定义。
- 全部读数来自 `delivery-r01/all.records.jsonl`，按（模型，层，通道，题，剂量）去重。

##### 脚本与输出

| 脚本 | 输出 | 内容 |
|---|---|---|
| `early.py` | `outputs/early.txt` | 十点 +1 下 L0–L7 每层每通道首步 EOS 数；首 token 分布；各模型校准尺度 m 随层变化；实际渲染的提示 |
| `dose.py` | `outputs/dose.txt` | 单点正负十档 L0–L7：首步 EOS / 机械重复 / 中位长度 |
| `summ.py` | `outputs/summ.txt` | 从既有 `summary.json` 读按注入层的输出统计与下游传播剖面；各模型逐层 clean 残差/attention/MLP 范数 |
| `tok.py` | `outputs/tok.txt` | 早层首 token 解码为文本（L0–2 与 L3–7 两段） |
| `qdep.py` | `outputs/qdep.txt` | 问题依赖度：四模型全层每层十通道的中位数与"八题同首 token"通道数 |
| `qdep_dose.py` | `outputs/qdep_dose.txt` | 问题依赖度随剂量档的变化 |
| `ident.py` | `outputs/ident.txt` | 八题完整输出逐字相同的通道数及非空例子 |

运行方式：在仓库任意位置执行 `python3 -I experiments/early-layer-question-dependence-v1-2026-10-28/<脚本>`，脚本按自身位置解析数据路径。

##### 解释边界

- 八题不是独立样本，不做显著性检验。
- 首 token 多样性是粗指标；正式版应换新题池并加跨题 KL。
- 这些数字描述"输出是否依赖输入"，不描述能力是否保留；深层 ±1 保持 8/8 不等于回答正确。
- Qwen3.5 层型来自 HF main 配置，不是冻结 revision。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| 本目录未提取到上述类型JSON | 不据此推断运行成功或失败 | — |

## 全部原始资产入口

本目录在固定提交下共有15个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/022-early-layer-question-dependence-v1-2026-10-28.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-layer-question-dependence-v1-2026-10-28)。未复制模型权重、环境或凭据。
