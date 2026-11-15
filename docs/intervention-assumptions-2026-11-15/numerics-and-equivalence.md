# 参数等价、数值实现与结构补查

2026-11-15；主作者路线，综合 Advisor 初审后修订并完成同人复核，记录见reviews/synthesis-recheck.md。来源身份：公开论文作者报告、项目已归档观察、下列条件推导。无模型运行、量化实验或权重编辑。

## 候选演变

最初考虑三类：P1等价重参数化下少通道干预的意义；P2量化/有限精度是否改变针响应；P3训练与结构是否改变可控性。首轮检索后补开P4：MoE路由是否是dense针迁移的隐藏条件。P4是后检索候选，不冒称独立初轮。初始思路在聊天推理中形成，本文件在检索后记录，不能当成检索前冻结。

| 候选 | 新证据后的决定 | 仍可能有价值的部分 |
|---|---|---|
| P1 改坐标/等价权重缩放使同编号针突然强弱不同 | 淘汰其新机制主张：大部分是未变换干预或未校准有效剂量 | 当前hook的等价性边界与数值验收；不是论文主线 |
| P2 改量化等级使针效果不同 | 泛化问题已有直接研究，不能简单重做量化×steering | 条件保留：递推状态压缩是否保留完整行为的干预响应，而非只保留无针准确率；尚无直接本项目证据 |
| P3 训练/微调改变steerability | 已有训练轨迹研究及权重steering；问题太宽，暂缓 | 如果找到具体训练后系数与响应规律，归几何/动力学问题，不另起泛化训练项目 |
| P4 MoE路由改变针作用/副作用 | RARE已直接研究与干预路由漂移；不推荐用MoE标签重做 | 可借其“计算路径兼容性”对照思想；不据此扩本项目模型 |

## P1：一个可以直接排除伪发现的推导

当前 `control_engine.py` 在MLP的down_proj输入（非线性之后）加第j坐标，幅度为 `a = dose × reference_residual_scale / ||w_j||`。理论上局部写入是 `a w_j`。列范数已校准，但逐token浮点加法的实际偏移仍需读取audit，不能把请求量当已实现量。

对于门控MLP `m = W_down [σ(W_gate h) ⊙ (W_up h)]`，把第j条up投影（如有bias也同步）乘 `c>0`、down第j列除c，实数运算下无针函数不变。若还使用固定的未校准坐标偏移，其写入缩小c倍；这是单位改变，不是改变了该模型的物理可控性。使用现有列范数校准，`a'=c a`，故 `(w_j/c)a'=w_j a`，局部输出相同，后续同状态下也相同。这不要求SiLU齐次，因为没有缩放gate支路。

边界：以上校准使用**变换后的列范数**与相同参考残差尺度；复用旧cached column_norms不属于该等价设定。c<0需同步坐标方向/剂量符号；任意中间层旋转通常不保持原逐元素门控架构，不能任意插矩阵后仍称天然单神经元。有限精度、缓存/校准实现不同会破坏实数恒等；此时先检查数值路径和实际注入差异，不能直接声称神经元功能发现。若形成稳定且有用的数值响应边界，仍可作为P2类实践问题。以上是作者从实际hook与代数作出的条件推导，未运行CPU或模型实验。

近邻 [On the Non-Identifiability of Steering Vectors, arXiv:2602.06801v4](https://arxiv.org/html/2602.06801v4) Appendix D已写权重与干预同步变换的等价性。本轮仅读相关附录及C/B，不接受其所有更强论断：激活协方差低秩不等于输出Jacobian有相同零空间；局部一阶等价不等于任意幅度和prompt的完整生成等价。表B中的“比随机扰动小”也不能单独证明等价。P1的上述排除依赖显式代数，而非这篇论文的广泛不可识别结论。

## P2：压缩是否保持扎针响应，尤其是持续更新的记忆状态？

**问题卡。** 在无针功能仍可用的压缩模型中，部署精度/分组/舍入是否会系统性改变同一稀疏干预的目标作用、历史内容使用和完整回答代价；这种改变是否超出输入处剂量误差或重新标定？这属于独立部署可靠性备选，不预设量化一定损害或改善steering，也不直接解决原针机制的卡点。改后系统的差异即使非剂量等价，也须另建对原模型计算依赖的解释联系，不能靠无针准确率相似代替。

**为什么可能重要。** 无针benchmark通过不自动证明内部干预的功能保持；若压缩后需要不同针或不同校准，控制接口应有自己的验证标准。一个可复用的失效预测或明确等价边界有实践价值；只展示低bit后输出变坏，没有超出量化常识。

**最危险近邻。** [Steering Under Compression, 2609.06473v1](https://arxiv.org/html/2609.06473v1) 已在7–9B模型上比较FP16/INT8/NF4权重量化，使用等行为效果下的能力代价，区分各条件无针基线、校准和失败区域。它本身已覆盖本问题的大部分泛化价值。当前公开结果不是完整预注册池的确认结论；不能把作者描述性结果扩为所有量化都等效。P2只有明确落到**重复状态写回对有针/无针对比的影响**并产生有用的解释或预测增量，才有剩余空间。可以承接已知理论解释未被解释的重要行为，不要求新数学。

第二层近邻更紧：[LoReS, 2611.01864v1](https://arxiv.org/html/2611.01864v1) 已区分状态内外量化，研究遗忘率、舍入累积、旋转造成scale反馈及query对齐；[Low-Bit GDN, 2610.39931v1](https://arxiv.org/html/2610.39931v1) 已用未来loss敏感性分配bit并维护近期pure writes。二者覆盖当前混合/递推模型。不能把误差累积、保护慢遗忘头或暂存新写入再发明一遍。它们已读部分尚未给出有针/无针对比的完整行为响应验证；这是检索边界，不是证明无人做过。

综合Advisor另补查后，作者回核了[STEPQuant](https://arxiv.org/html/2609.38169)摘要/引言，它已按误差寿命和key-row读出影响处理状态量化；[When Quantization Breaks Memory](https://arxiv.org/html/2609.04490)摘要/引言则已研究GRU/LSTM中状态写回吞掉连续小更新与补偿。后者并非LLM扎针证据，但足够否定把“小更新被阈值吞掉”当新原理。Advisor还核了LoReS附录D.2/Table11：已有不同mixer架构下dominant-channel删除/均值替换的PPL对照，宽泛的“结构条件改变稀疏内部干预后果”已有先例；这不等于加法针完整回答机制。

**理论依据及其限度。** 对同一量化算子Q，一般 `Q(s+δ)−Q(s) ≠ δ`。简单固定步长q、四舍五入时，`s=.49q, δ=.02q`跨网格给q的差，`s=.10q`的同δ却给0。它只说明局部干预受网格位置影响，是普通量化算术，不证明实际模型有显著效应。

固定后续局部驱动、同A/B且用同一时序读写时，可写 `ΔŜ_t = A_t ΔŜ_(t−1) + (e_t^needle−e_t^clean)`，其中e是各自状态的量化误差。有针/无针误差并不自动独立或相同；若采用自适应分组尺度，针还可能改变整个组的量化网格。开放模型轨迹还会改变A/B/query，不能用这一条件恒等式断言模型行为由舍入主导。论文价值必须来自真实的条件规律及完整行为，不来自再写一次误差递推。

**项目支持与反证。** 目前只有hook对BF16实际注入量的审计字段，不能据此宣布发现低bit状态效应。NGC在固定操作下显示内部增益规律可预测却未救回错误完整答案，提醒不要把局部增益/读出等同控制收益；它不是量化对照，不能算P2阳性或阴性。既有报告没有提供同一针跨precision的配对完整行为证据。

**竞争解释。** 输入处有效剂量不同；压缩模型本来就退化；干预方向重新估计改变；量化引入选择性的写入/读取变化；解码分叉把小差异放大。单个最终答案或余弦相似不足以区分。不能用一个匹配范数声称这些已被控制。

**缺少什么及可行性。** 理论和部署方法可复用；需要同一操作语义下、能区分注入与后续状态写回的证据，以及仍有功能的各条件无针参照。当前资产没有完成这个比较，外部仓库未复现。CPU可分析量化算术与已有序列，但不能凭未保存的真实状态声称完成行为检验。没有据此安排新模型测量。

**保留/停止条件。** 若只是复现权重量化的等效代价、已知状态误差累积或改变剂量，停止作为独立机制方向；若所有差异伴随无针崩溃，不能主张选择性控制；若方向与行为响应稳定，报告有限部署可靠性，不能事后改成寻找更极端低bit。只有可解释、可复用的响应差异/等价边界，才可能值得进一步立题；不是要求先有阳性才能研究，而是要提出具体且有内容的未知关系。当前建议是备选资料问题，未达到实验优先级。

## P3/P4补查为何没有另立主线

[How Does Controllability Emerge During Pretraining, 2508.01892v1](https://arxiv.org/html/2508.01892v1) 已研究表达能力与线性可控性在训练中的不同出现时点。相关性不足以识别某个系数的因果作用，但足以否定“训练会改变可控性”的新发现说法。[Steering Language Models with Weight Arithmetic, 2511.05408v2](https://arxiv.org/abs/2511.05408v2) 已利用对比微调的权重差控制行为；不等于研究固定针的易感性，也不意味着本项目需要另起微调。

[INNSteer, 2606.08454](https://arxiv.org/html/2606.08454) 学习可逆表示变换后施针；[DIAL, 2610.31438](https://arxiv.org/abs/2610.31438) 训练几何感知适配器。它们是更换/学习干预算子的重要近邻，并非天然模型结构系数的干预证据。DIAL的norm weight不是主干RMSNorm γ，见几何路线进一步核查。

[RARE, 2608.21236v1](https://arxiv.org/html/2608.21236v1) 已直接把MoE内部干预的表示变化与路由漂移拆开，并报告保留干净路由改善控制。它不证明所有路由应保持不变，但“路由是隐藏条件”不能当本轮独创。[MASCing, 2604.27818](https://arxiv.org/abs/2604.27818) 另已把路由mask作为行为控制接口。当前dense模型资产不能直接检验MoE特定问题；不为避开近邻而扩模型家族。

最后，[Prompt-Activation Duality, 2605.10664v3](https://arxiv.org/html/2605.10664v3) §5.4/Appendix N已做clean-cache与dirty-cache反事实并讨论长期连贯性。其标准注意力与本项目递推状态不同，但“针会通过缓存累积副作用”已不是空白，不得用迁移到另一缓存类型就声称新机制。

## 已核资料层级

项目：实际hook源码已读；NGC在固定分支`86bfe25ac83bd043cc7dccaa0d63b8483b926bd9`的REPORT/CONTRACT及正式receipt状态已核，未重算原始回答；主工作树HEAD与路径见SCOPE。

公开来源：Compression摘要/方法/等效代价/限制相关段；Non-Identifiability附录B/C/D；LoReS§4.2–4.4及F/G相关；Low-Bit GDN§2.2–2.3、§4.3与局限入口；Prompt-Activation摘要、§5.3–5.4；RARE摘要、§1–4入口；其余上列论文摘要/方法入口，不声称逐页全文审计。作者网站Inverse Scaling读了摘要与范围，其单行为/有限样本观察仅作警示，未将其架构归因或“INT8 safe”转为本报告结论。

## 检索日志

日期2026-11-15，网页搜索→arXiv/会议/作者一手来源。以下是实际查询的主题与关键字，无私有材料：

1. `activation steering quantization robustness precision language models`; `activation steering function preserving reparameterization neuron scaling`; `training language models steerability activation steering architecture coefficients`。
2. 精确标题 `On the Non-Identifiability of Steering Vectors`; `Steering Under Compression`; `activation steering bfloat16`; `steerability training activation model`。
3. `activation steering architecture training controllability`; `steerable normalization language models activation`; `activation steering Jacobian training`; `How Does Controllability Emerge`。
4. `activation steering KV cache quantization`; `steering quantization recurrent language`; `activation steering precision numerical`; `activation steering function-preserving`。
5. 精确标题 `Low-Bit GDN Recurrent-State Quantization`; `Quantizing Recurrent Language Models Is Easier`; `KV-cache contamination steering`; `Memory Steering compressed representation safety`。
6. `mixture experts activation steering routing sensitivity router temperature`; `steering expert routing activation`; `activation steering top-k experts`; `activation steering normalization gain`。

OpenAlex备用脚本查询`activation steering architecture controllability`因DNS失败，无结果；其余引用由网页工具取得。聚合网站仅定位原文，未把命中数当文献数量或查重完成度。P2的精确交集尚无直接命中，不等于新颖性已经成立。
