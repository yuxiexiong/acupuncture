# 冻结几何路线：归一化、权重尺度与激活参数

日期：2026-11-15。身份：研究问题探索，不是实验方案、运行队列或新结果。采用 evidence-to-questions 与独立 Advisor。只读项目材料与公开文献；不加载模型、不运行科学实验、不修改模型。初始登记在公开检索前写入。

## 检索前独立候选登记

| 编号 | 初始问题 | 起点与最危险反例 |
|---|---|---|
| G1 | 归一化是否把单通道插针转成对整条残差流的竞争性重缩放，进而决定目标效应与能力代价？ | RMSNorm 的导数已有解析式；若只证明有全局重缩放，问题已被数学回答。需要行为解释增量而非重发现公式。 |
| G2 | 单通道干预的有效性究竟依赖语义方向，还是其相对于残差流的尺度和夹角；能否得到跨条件的有效剂量描述？ | 项目已做 down_proj 列范数校准，少坐标不等于小剂量；标量范数可能完全遗漏方向及下游内容。 |
| G3 | 冻结的归一化增益、残差权重与门控工作点，是否是干预选择性与副作用的可分调节因素？ | 修改权重可能直接换了模型能力或等价改了剂量；必须明确不是把一般损伤减少包装成选择性改善。 |
| G4 | 干预效果是否取决于 MLP 非线性的局部工作区，能否由激活函数/通道参数的调整提高可控性？ | 当前 hook 位于非线性之后，直接注入并不经过该激活函数；换激活可能只是重训模型或破坏基线。 |
| G5 | 同一模型函数的不同内部参数化是否改变“少数通道”的表观特殊性，从而改变何谓可归因的针？ | 合法重参数化受逐元素非线性约束，不可任意旋转 MLP 中间基；若仅换坐标后忘了同步干预，是伪问题。 |

初始自查：不以 WSB 现有解释限制本路线；不恢复 WSP；不把 NGC 的局部增益失败推广成所有几何解释失败。不把改变架构/参数的研究候选视作执行授权。暂无样本、矩阵、预算或工程实施设计，因此 C01–C14 实验设计验收不适用；若后续落成操作方案须另审。

## 证据、理论与第一轮取舍（送审草案）

来源版本：工作树 HEAD `3d00273b9a21b0f1160ead0c91eb3d9e94a1ec35`；当前主线原结果在本工作树缺失时，用只读 `git show codex/evidence-rediscovery-20261112:...`，该分支本轮读时为 `86bfe25ac83bd043cc7dccaa0d63b8483b926bd9`。读了项目入口、Advisor状态/决策、执行协议及最新日志、known-basics；没有重算原始样本。

- **项目实现已知：** `experiments/early-input-control-v1-2026-10-29/control_engine.py:159–190` 在 down_proj 输入处单通道加法，`requested=dose*reference_scale/column_norm`。因此注入是非线性之后的写向量，原生 SiLU 不会直接再门控这次新增值；上游非线性决定原有背景，下游非线性仍可改变传播。列范数已经校准，不可再以列范数解释同 dose 的强弱而不算实际向量。
- **项目观察：** `experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/FIRST_PASS.zh-CN.md` 在88固定点、八已见题中记录剂量过渡、非单调与题间分离；不能称普遍单阈值规律，未重新评分。NGC原报告（上述固定分支，`experiments/cache-native-gain-v1-2026-11-08/REPORT.zh-CN.md`）报告四方向增益配置调整修复0题，内部预测规律不构成完整答案解释；该操作不是RMSNorm gain，不能拿它否定全部归一化候选。
- **数学已知：** 令 `N(h)=Dγ h/r`, `r=sqrt(hᵀh/d+ε)`，则 `J_N=Dγ(I/r−hhᵀ/(d r³))`。径向与切向响应不同、γ产生各向异性，是链式法则而非待发现规律；ε=0时径向导数为0。γ非均匀时输出不是普通欧氏等半径球，不能把单位球直觉无条件套到learned-gain之后。
- **数学已知：** pre-norm块 `h'=h+F(N(h))` 中，在ε可忽略且c>0、其余上下文/状态一致时 `N(ch)=N(h)`，但 `ch+F(N(h))` 一般不与 `h+F(N(h))` 共线。径向缩放能改变保留残差与新模块输出的相对权重；“下一层归一化会完全抹掉幅度”错误。这个局部恒等关系不是新机制结果，也不允许直接外推多token缓存演化。

### 最危险近邻及实质重合

1. [Angle–Norm Decomposition, 2606.06735v2](https://arxiv.org/html/2606.06735v2)：实读摘要、§3、§4、局限。已经直接分离角度/半径并比较目标效应、PPL和能力；严格保范数并非普遍最优。其“容量”解释是作者假说。**G1/G2作为角度—范数控制方法或副作用发现已高度重合，不能换成单神经元就称创新。**
2. [Spherical Steering, ICML2026](https://proceedings.mlr.press/v306/you26a.html)：读正式摘要和元数据，保范数旋转及置信门已是已有方法。Angular Steering亦已定位，但本轮未读全文，不承担更细技术裁决。
3. [Leverage Is Not Reach, 2606.19831](https://arxiv.org/html/2606.19831)：实读摘要、§1–2及§3入口；已将单通道写向量、残差预算、相干窗口及Gemma post-FFN范数上限联系起来，含Qwen3.5。**G2不能以“单针有效剂量预测”重述。** 其通用曲线/阈值为有条件作者结果，不是本项目已证事实，也不覆盖所有非单调任务。
4. [Activation Scaling, EMNLP2024](https://aclanthology.org/2024.findings-emnlp.479/)：读正式摘要/元数据。稀疏activation scaling联合有效性、忠实性和最小性目标已有，改gain做控制不是天然新方法。
5. [Unified View of Attention and Residual Sinks, 2601.22966](https://arxiv.org/html/2601.22966)：实读§1–2、§3入口。区分token-specific massive activation、跨token residual sink、attention sink；小归一化权重可使outlier主要承担分母重缩放，显式门控与参数吸收已有，包含线性/混合架构。**“冻结norm参数影响一般功能”“outlier是隐式gain”不是新问题。**
6. [Anatomy of Massive Activations and Attention Sinks, 2603.05498](https://arxiv.org/html/2603.05498)：实读§3.1生命周期和SwiGLU二次放大分析；前人已有step-up/down、残差持久、近恒等SiLU与方向性高增益结构。**G4以门控工作点解释大激活不是空白。**
7. [A Single Layer to Explain Them All, 2605.08504v2](https://arxiv.org/html/2605.08504)：实读§3.1与§4入口。RMSNorm高gain维度与FFN联合产生massive activation及方向刚性已有，不得把大γ通道当新发现。
8. [Outlier-Safe Pre-Training, ACL2025](https://aclanthology.org/2025.acl-long.618/)：读正式摘要与作者代码仓入口。Single-Scale RMSNorm及训练干预抑制outlier已有；不能据训练变体推断现有冻结模型直接替换后仍等能力。
9. [Steering Interference Reflects the Model’s Defaults, 2609.06951v4](https://arxiv.org/pdf/2609.06951)：读摘要/引言与图1；作者报告多个模型中同量随机方向具有相似平均副作用，方向几何不能准确解释单对行为干扰。**这反对仅以方向夹角解释所有副作用，但没有排除norm/更新动力学。**
10. [Mechanistic Indicators, 2602.01716v3](https://arxiv.org/pdf/2602.01716)：读摘要/引言；已有内部信号预测steering可靠性。仅建预测器不等于机制解释，亦非全新任务。
11. [DSO, CVPR2026](https://machinelearning.apple.com/research/direct-steering-optimization)：读作者页面检索摘要，已定位官方论文。训练线性变换控制行为—性能的泛化建议需要比较此近邻；本轮未审全文，不声称其已经解决单针参数敏感性。

### 草案结论

**当前没有足够证据将原五项升级为强主线。** G1/G2淘汰泛化新颖性主张，G4暂缓，G5交父路线统一审查。G3只保留下列一个可被否决的研究问题，不作为立即可执行计划：

> **G3-R：在相同注入处有效扰动条件下，模型学到的归一化/残差重缩放机制，是否决定了稀疏干预使模型保持或丢失输入约束的边界，而不只是改变目标方向的即时强度？**

这里“相同有效扰动”不是任意一个范数或角度标量，必须明确对应的即时计算对象；若实际上改变了输入表征或基线功能，就不能声称隔离了一个纯gain因素。候选解释包括输入相关信息被新写入压过、后续模块更新相对残差变弱、以及模型默认行为在一般扰动下占优。它们尚非互斥、未被本项目实测区分。

**价值：** 若能识别一种在保持局部steer作用时改变输入约束保持的、训练形成的重缩放机制，可解释为何同类针跨架构出现不同控制上限，且把“几何相关性”推进为关于完整回答的条件机制；不要求发明新norm或全新模型。**最强支持：** 现成理论说明即使角度相同，后续残差更新比例不同；近邻实测半径可影响能力但未在已读段落识别唯一因果通道。**最危险反证：** 角度—半径近邻可能已足够解释全部差异；修改γ可能只是普通activation scaling，或所有收益都是减弱目标效应/换了基线。项目尚无直接γ干预证据。

**缺失依赖：** 需要知道实际hook之后的归一化/残差路径、实际背景向量与norm增益、input-dependent读写及完整回答的对应证据；现有报告与hash不等于已保存这些张量。**可行性分拆：** 局部公式/源码可行；有无可改变的经验边界未知；能否在改参数后保持可比功能未知；形成超越近邻的论文贡献未知。**改变判断/退出：** 若变化由已知角度—半径配方或实际注入量即可解释，归为校准并停止；若只改变基线或减弱针而无保留目标作用的条件关系，停止控制机制主张；若没有独立于最终答案后验拟合的输入约束解释，也不升级。现阶段只值得继续资料辨别，尚不推荐模型试跑。

作者反方自查：问题未必值得单独立项，最危险的是把“后续更新比例”这个架构事实改名为新机制；即使γ能调效果也未必有实质新认识。不能把旧NGC写入增益阴性洗成这个假说阳性，也不能把massive activations与本项目针误认同一通道。允许Advisor将G3-R一并否决。

### 送审前范围纠正

父路线提醒：用户研究对象是通常冻结的结构/系数怎样改变**针的响应**，不是仅换一种steering算子。因此G3-R必须区分参数p改变无针行为的主效应与p改变有针/无针对比的效应修饰。p造成基线变化不自动否定科学价值；它只阻止把绝对答案改善直接归为针响应改变。前段“只改变基线则停止”指没有针响应增量时停止本主张，不要求所有无针输出逐token不变。

新增近邻：[DIAL, 2610.31438v1](https://arxiv.org/html/2610.31438)已读摘要/方法入口：它训练适配器、在冻结主干上做几何感知编辑，不能仅凭标题认为研究了改norm训练权重后的针响应；需核对应具体norm段落。[INNSteer, 2606.08454v2](https://arxiv.org/abs/2606.08454)读摘要，学习可逆变换再在latent施针是已有算子路线，不等价于证明天然归一化参数调节针效应。本次不推荐从零造一个新steering算子来逃避结构问题。

### 后续核查：冻结结构与算子的边界

DIAL Eq.(4)、Appendix B.1、D.3已核：`norm weight`是适配器学到的投影/保范数旋转插值，base LLM始终冻结。故不把它写成修改天然RMSNorm γ的研究；它仍直接覆盖“学一个更好径向steering规则”。

Unified View §3.3–3.5已补读：PreAffine在归一化前改变分母，标准RMSNorm γ在归一化后逐维缩放，两者不是同一操作；GatedNorm还有显式输入依赖。此区别给G3-R一个更具体的被审对象：**天然系统对输入依赖重缩放的依赖，是否会让相同的needle方向在某些条件下变成内容选择、在另一些条件下变成无差别压低非目标信号？** 但“分母耦合存在”仍是数学；已有outlier训练实验也已覆盖整体功能，不是针效应的直接证据。主报告不承诺这里仍有新颖性，需针响应和旧内容实际使用之间的额外解释。

## 检索日志与核验深度

检索日期2026-11-15；本轮统一记录时刻2026-11-15 13:39:24 UTC（北京时间21:39:24），该时刻是日志汇总、不是每次搜索精确执行时刻。全部查询仅公开通用概念，无私有实验数据/题目上传。搜索用来找候选，再用上列原始URL核对；未声称穷尽查重或复现。

依次检索：

- `activation steering RMSNorm LayerNorm norm preserving steering geometry`
- `language model steering residual stream norm scaling orthogonal steering side effects`
- `transformer activation steering gauge invariance reparameterization neurons`
- `"activation steering" "layer norm" gain tuning`
- `"steering" "residual" "norm" "depth" language model`
- `"Mechanistic Indicators of Steering Effectiveness" arxiv`
- `"Steering Interference Reflects" arxiv`
- `"LayerNorm" "steering" "tuning"`
- `"residual norm" "steering" "updates"`
- `"residual" "norm" "steering" "capacity"`
- `"LayerNorm" "activation" "suppression" "steering"`
- `"residual scaling" "activation steering"`
- `"RMSNorm" "steering" "Jacobian"`
- `"pre-norm" "residual" "norm" "identity" transformer curse depth`
- `"normalization" "outlier" "activation steering" neuron`
- `"DSO: Direct Steering Optimization"`
- `massive activations language models RMSNorm steering sink attention`
- `"RMSNorm" "gain" "outlier" "steering"`
- `"Leverage Is Not Reach"`
- `"Decoy Direction Optimization" "Gain"`
- `"Outlier-Safe Pre-Training"`
- `"Decoy Direction Optimization" arxiv`
- `"residual sink" "steering"`
- `"normalization" "steerability" "parameters" language model`

父路线补充DIAL与INNSteer准确标识后直接打开原文，无额外私有检索。Mechanistic Indicators与Steering Interference的无版本HTML返回404，随后读arXiv PDF；不把失败页面算实读。RMSNorm [1910.07467](https://arxiv.org/abs/1910.07467)仅核摘要/元数据，导数由定义推导，不冒充原文新定理。搜索结果中的博客、转载与社区网页只用于发现线索，没有承载最终技术结论。

### 更直接的参数改动近邻（送交同一Advisor）

[Decoy Direction Optimization, 2609.16204v1](https://arxiv.org/html/2609.16204) 已核摘要、Appendix D.2的RMSNorm Gain Control及F.2参数表：作者实际讨论提高拒答对齐归一化γ以改变消融响应，并报告这类编辑经常使生成失稳。它的主问题是抵抗估计式拒答方向投影，不能等同本项目单通道加法；但足以否定“改变冻结γ会改变干预反应”这一空白主张。本文不复述攻击配置，也不将防御目标改为项目新目标。

因此下一版问题必须更严格：**结构或参数变化能否改变多终点针响应的形状、方向或效能—代价边界，且不是仅将旧针的有效剂量重新标定？** 这仍是需要论证的问题，不是已找到机制或提升；作者正在接受同一Advisor复核。若只存在剂量重标定，科学上可形成等价性边界，但不能包装为新可控模型或更优干预。

补读 [How Far Can You Steer?, 2611.06001v1](https://arxiv.org/html/2611.06001)：读摘要/引言，已有行为—能力frontier定义和留出/开放生成限制。因此采用frontier本身没有新颖性；它只提供评价语言。公开搜索另含 `"steerability" "RMSNorm" "gain"` 与 `"activation steering" "parameter" "response curve"`。

## 作者修订候选 G3-R2（同一Advisor已复核）

**问题：通常固定的归一化/残差重缩放参数，能否改变单通道针的响应方向、非单调结构或目标效果—输入约束保持关系，使其不能由原模型的剂量重新标定解释？如果可以，这种变化是否由某个具体重缩放关系解释，而非一般基线改变或损伤？**

这里的参数对象首先是RMSNorm逐通道γ及与之耦合的残差/模块相对权重，不包含把新适配器当原模型参数。先筛除γ与相邻权重的代数等价重参数化：在RMSNorm后线性读取的路径，γ可吸收入消费者矩阵；相关路径精确补偿且针表征不变时，不能凭参数名产生新功能。实际问题是未被补偿的组合映射及其针响应。显式PreAffine/GatedNorm是可借用的架构对照概念，尚无理由默认选择它们或训练新模型。

**R2覆盖前文G3-R的退出措辞：** 未保持目标效果只排除稳定控制改善主张，不自动否定针方向翻转、选择性消失等机制价值。参数主效应不自动否定问题；离散准确率的地板/天花板也可能制造表观交互，不能单凭交互项命名机制。研究训练后参数不等于识别它在训练中形成的因果过程。

- **为何比G3-R更准确：** 将“参数是否影响输出”换为“参数是否改变针的作用规律”。已知数学只证明局部传递会变，不能预言实际训练模型的完整回答会产生何种不可用剂量重标定解释的变化。
- **不先假定答案：** 参数改变可能只换剂量刻度，可能改变针方向的作用，也可能仅改变无针基线；三者科学身份不同。也可能产生不可用的一般损伤，不能把它当新可控性。
- **不是强立项推荐：** 当前只有理论可能性及相邻作者结果，无本项目直接γ×needle证据；大多数初始提法已被近邻覆盖。R2保留为需要具体证据支持的问题，不排入实验队列。
- **重标定的边界：** 不能用看完同一答案后任意拟合的逐样本函数，让任何标量曲线都“可解释”；也不能仅凭一个指标不重合宣布机制变化。需要预先有意义的有效剂量对应关系，并关心共同可观察的目标/完整任务/副作用结构。此处只澄清研究命题，未制定拟合程序或测量方案。
- **避免过度控制：** 不要求把参数改变之后所有下游激活强行匹配，因为那会把待研究的效应本身抹掉。“同针”需要在改动前界定注入算子及实际落地变化，不能偷换成必须同整个轨迹。若参数改变了写向量，需明确是在研究同名坐标还是同残差扰动；二者不能混报。
- **增量成立的条件：** 不只是给现有曲线加一条模型变体，必须给出一个具体重缩放关系怎样解释针响应改变的可反驳认识；阴性若支持剂量等价，只能在实际检验范围内成立。
- **退出条件：** 若证据只够支持局部尺度恒等式、既有角度—半径方法、γ调参提升或基线迁移，不单独立项；若没有能区分“参数响应变化”与“普通改变针剂量”的证据对象，暂缓而不扩大模型/层/参数扫描。

## 最终判断与Advisor处理

**本路线目前没有值得独立立项推荐的强候选。** G3-R2只作为低信心问题交总路线比较；不声称已有γ×needle观察、可用控制改进或论文贡献。G1/G2宽泛提法停止，G4暂缓，G5交父路线处理。未来若没有具体、非代数等价的参数关系与超越剂量校准的认识增量，本路线停止。

独立上下文Advisor先审G3-R，再审同一作者的R2，直接指出原题过宽、近邻更直接、等向量匹配可能过度控制、γ不是独立功能单元。作者采纳；实质修订经同一人复核，明确要求的最后三处更正已落实。[完整初审/复核](reviews/geometry-review.md)与[逐项处理](reviews/geometry-disposition.md)保留，不冒充独立复现。未解决的是经验现象是否存在、能否识别非剂量等价关系以及认识增量是否足够，不以“审查通过”覆盖这些缺口。
