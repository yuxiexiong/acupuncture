# 032．CFM-S1：原生形成轨迹

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-10-31T03:54:03.115697+08:00；不能当作全部子运行起止。

**当时的目的与设计**

记录36条原生轨迹，把状态差的延续、旧状态处理差和新写入差分别记账，并看其实际读取和停止结果。

**实际过程、结果与后来更正**

L0的相对状态差约0.81–0.98、L12约0.72–0.83；写入与旧状态处理部分抵消，晚段写入对末端净差约82%–93%。L0 EOS12/12、L12 0/12。这里的分账是当时的内部读数，完整定义与各情景表保留。

**来源身份**：`cache-formation-mechanism-s1-native-trace-v1-2026-10-31`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：缓存形成机制｜CFM-S1｜原始轨迹与状态形成分析计划 v1

原路径：`docs/cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md) · [单独阅读副本](../library/474ffe04506b2300.md)；SHA-256：`474ffe04506b2300348e82a5fb07ed05f52e3d7dad3146a5a59b2e5b5a9b256d`。

---

#### 缓存形成机制｜CFM-S1｜原始轨迹与状态形成分析计划 v1

> 唯一计划编号：`CFM-S1-v1-20261031`。原名“第一阶段：原始干预怎样形成递推状态差异”已更名，实验内容不变；不是2026-10-29已完成的“早层失效定位第一阶段”。当前状态：有效设计，未执行。

##### Material Passport

- 日期：2026-10-31；版本：stage1-plan-r01；academic-research-suite / experiment-agent / plan。
- 身份：基于已有证据的分析与补充观测设计，尚未运行。当前仅核对本地文件、导出字段、历史协议/收据和公开源码/论文；没有模型前向、候选重评分或GPU任务。
- 主线：解释短暂稀疏激活干预怎样改变历史状态，并在撤针后影响回答。中心问题仍是“每步写入怎样变、旧状态的保留/衰减/修正怎样变，以及二者怎样影响后续回答”。
- 本阶段交付：原始C/T轨迹上的过程差异、局部读取联系，以及据此选择第二阶段的判别表。不是新的攻击方案、EOS修复方案或完整因果结论。
- 旧r04保留为辅助探针及设计反例，不作为本阶段运行方案。本文不授权后续运行；工程实现、数值容限和实测资源预算仍待执行前冻结。

##### 1. 明确要回答什么

**已经观察到递推状态替换会改变输出。第一阶段要查清：在没有额外补偿和缓存拼接的原始C/T计算中，这些状态差异具体从哪些时刻、哪些运算产生，怎样积累，以及是否进入了模型实际使用的局部读出。**

三个必须同时完成的分析问题：

1. 当前步新增加的差异，来自加性写入变化，还是旧状态处理算子变化？还是只把前面已有的差异继续带下来？
2. 这些差异主要在事实陈述时产生，还是在后续问题/作答指令阶段继续形成、修正或抵消？撤针后的相同输入下还发生什么？
3. 累积状态差异是否进入实际查询的读取方向？如果状态差异与读取差异脱节，就不能直接拿状态范数解释最终回答。

“原始轨迹”指无额外过程干预的C与原针T；T本身已经受激活干预，不称训练分布内。所有共享变量都由各自完整前向自然产生。本阶段不修改value、不强制βv、不冻结后续门、不交换S/O。

##### 2. 现有资产实际提供了多少证据

固定来源提交为`73185a40de0c779d55beac204c7d46683736b5ef`。读取了[历史合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30/CONTRACT.zh-CN.md)、[冻结实现说明](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-complement-analysis-v1-2026-10-31/source/IMPLEMENTATION.zh-CN.md)、[worker-0完成收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-complement-analysis-v1-2026-10-31/source/runs/b_validate-r01/worker-0/receipt.json)及[冻结文件清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-complement-analysis-v1-2026-10-31/source/freeze-r01.json)。合同正文的旧草案状态不覆盖后续completed收据。

| 已有资产/结果 | 本阶段如何使用 | 不能从中反推什么 |
| --- | --- | --- |
| [L0四格，24输入](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-complement-analysis-v1-2026-10-31/RESULTS.zh-CN.md)：TT首步EOS 24/24；只清理组4后三类状态均清理时首步EOS 0/24，旧核心匹配7/24；仅组4污染时旧核心匹配24/24 | 保留停止、事实敏感度、作答三个终点；不把组4设成唯一根因 | 不能推出“组4储存了事实”或四格交互一定是自然协作 |
| [组件复算](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-mechanism-path-audit-2026-10-31.zh-CN.md)：L0只清理组4递推即解除首步EOS 24/24，但旧核心匹配仍0/24 | 要求最终解释容纳“开口”和“正确交付”分离 | 不把局部读出或EOS恢复当能力恢复 |
| [L12/C3621/−1历史结果](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-mechanism-proposal-2026-10-30.zh-CN.md)：L16–18递推清理使事实敏感度约+5.27，反向污染约−5.75 | 把L12作为第二种既有现象，与L0分别分析；沿用L16–18作为有证据的观测位置 | L12不是已证明的特殊层；两锚点不代表全层、全模型 |
| 本地2040条II-B导出；本方案六旧情景的C、L0-T、L12-T原参考均齐全，共36条，附72条候选序列分数 | 已有行为基线、每步D、候选逐token logprob、文本、来源哈希可直接复用。所选面板C与L12-T各0/12首步EOS，L0-T为12/12 | 没有完整logits，也没有逐步q/k/v、门、状态矩阵；不能反演写入/旧处理过程 |
| 冻结`stage2.py`第442–458行的缓存清单写出逻辑 | 确认写出的是manifest、结构差分、来源及`gate_decay`记录 | 不是完整状态张量。`gate_decay`的原始细粒度记录本地未取得；即使补回衰减记录，也不能代替β/k/v/S |

本次实际核对了导出字段、36条参考覆盖及上述三个本地相关实验目录。没有在这些目录中发现`.pt/.npy/.npz/.safetensors`内部轨迹；**不据此宣称服务器任何地方都没有另存轨迹**。在申请新增推理前，先按旧清单检查是否有同身份归档；若存在且字段足够则复用。哈希不是张量，旧评分不是免费可重放状态。

**因此：当前旧数据足以建立端点约束、选定既有案例和形成缺失清单；不足以完成本阶段核心过程分析。下面给出需要怎样记录和分析，不能把它写成已经得到的发现。**

##### 3. 理论和related work直接拿来用什么

- [Gated DeltaNet](https://arxiv.org/html/2412.06464)与[冻结版本Qwen源码](https://github.com/huggingface/transformers/blob/v5.20.2/src/transformers/models/qwen3_5/modeling_qwen3_5.py)提供更新规则。短卷积、门和读出在架构中的关系是定义，不是本轮待发现机制。
- [WriteSAE v4附录A](https://arxiv.org/html/2605.12770v4#A1)已经分析写入—传播—读取及到logit的近似关系。我们借用该分析顺序，不训练SAE、不声称新发明状态分解。其固定驱动/局部扰动条件不能直接套到C/T的门、key、value均变化的情形；本文保留这些实际差异，不使用“只看衰减门乘积”的简化。
- 已知固定驱动下旧状态差异不被该局部更新算子放大；待测的是当前真实轨迹的差异源、方向、抵消和读取，不再花模型实验验证这个不等式。
- 本阶段可能增加的认识是：**我们的原针实际改变了哪段过程，形成了什么可被读取的差异，并对下一种原生干预时序提出什么可反驳的预测。** 公式重建成功只算工程/分析验收，不算机制成果或新颖性。

##### 4. 固定对象与最小补充观测范围

模型沿用Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`、原权重/模板、原校准规则、BF16/eager配置与冻结依赖身份。运行前核对实际递推/分块内核，eager标签不能替代内核确认。

- 条件：C、L0/C4146/−1、L12/C3621/−1。两个T各自与同输入C比较，不互当供体。
- 输入：VAR01、VAR02、VRD01、VRD02、VRL01、VRL02，各两个原事实版本，共12输入；沿用r04的小面板，不再择优挑题。这些是已经打开的旧题，不称独立确认。其余六旧情景保留作后续扩展可能性，**不称未见留出集**。
- 观测位置：L16–18全部递推头；不按新结果挑头。它是已有双向效应的观测窗口，不是“只有这三层重要”。
- 时序：与旧实验一致，T在`prompt[:-1]`有针；最后一个提示token及后续候选评分无针。C从始至终无针。
- 读取：先记录相同末提示token的原始logits；再从各自原始完整缓存分别读取原有两条固定候选，收集逐token分数及目标层轨迹。候选分支只复制本条完整状态，不跨C/T拼接。
- 两事实版本各自与其C/T逐token对齐；两事实之间可能token数不同，只按预标注语义区段/读取位置比较，不能把相同token编号当语义对齐。
- 第一阶段不新增自由生成。旧回答用于约束解释；候选teacher forcing保证C/T文字相同，但结论只涉及固定候选响应，不冒充自由回答的完整机制。

为什么不能仅观测最后一个token：它只给出末态和读取，无法知道差异在事实输入时已经形成，还是之后才形成。必须覆盖原前缀全过程；后续只沿原来的短候选评分，不增长新长回答。

###### 需要记录的最少字段

| 位置 | 记录 | 用途 |
| --- | --- | --- |
| 身份与时序 | 输入/token/position/mask、校准值及哈希、针实际开启位置、层/头索引、dtype/内核与源码身份 | 保证C/T差异来自原针，保证可与旧读数连接 |
| L16–18每token | 卷积前qkv投影、卷积后实际q/k/v、实际α和β、z；归一化/头扩展/查询缩放约定 | 计算A/B并保留共享变量关系；区分卷积输入变化与卷积后变化，不能只记录门均值 |
| 同层每token读出 | 原始head读出、gated norm后结果与out_proj输出 | 检查状态差异是否进入实际读取，是否在后续门/归一化处改变 |
| 同层状态 | 初态、事实区段末、问题区段末、撤针边界和评分分支末的真实递推矩阵；对应卷积缓冲 | 核对离线重建；不需逐token保存巨大矩阵 |
| 组边界与终点 | L16入口、L19入口/出口在末提示及候选评分位置的向量；原始首步logits、候选逐token分数 | 看组内差异是否传出，并与原端点连接；不据边界向量完成KV路径归因 |

如原内核不暴露区段中间状态，不为记录而改变原前向分块：保存实际暴露的边界，其他中间状态标为离线重建。优先保存紧凑驱动量，在CPU重建逐步矩阵并检验原生head读出和末状态。改变内核才能拿到的量另列工程问题，不偷偷替换原数值路径。

###### 若以后获准采集，成本到底包括什么

科学数据上限为12输入×3条件＝36条前缀形成轨迹、36次共同末提示读取、72条固定候选后缀评分；两候选共享各自末提示状态，避免重复前缀。原校准若有可认证数值则复用；否则最多6个reference前向，两个T共用原规则下对应reference。新增自由生成为0。

另列最多3条身份/只读记录验收重放（同一预定输入×C/L0/L12，各两候选），其中第一次合格记录可进入上述36条，额外重复最多3前缀+3末提示+6候选。失败保留并停止，不自动重试、扩题或换内核。工程误差容限须在查看科学分解前冻结。

成本按实际token数及记录体积估计，不能用36“条”冒充36个token前向；如历史路径逐token前向，应逐token计数。尚未测此记录方式吞吐，不报虚假卡时。本文只列待审范围，没有启动或运行授权。

##### 5. 分析一：把状态差异记成可核对的账，不构造新模型状态

采用源码key×value方向，逐层逐头计算：

\[
S_t=A_tS_{t-1}+B_t,\qquad
A_t=\alpha_t(I-\beta_tk_tk_t^\top),\quad B_t=\beta_tk_tv_t^\top.
\]

这里B是**不依赖旧S的加性写入项**，不是代码中整个delta修正。代码的实际修正为\(\beta k(v-\alpha S_{t-1}^\top k)^\top\)，含有旧状态的读取和减除；不能把其全部变化命名为“新内容写入变化”。两种量均记录，但主要账目按A/B定义。

令Δ为T−C，上横线为两条原轨迹的算术平均。主账采用对称恒等式：

\[
\boxed{\Delta S_t=\underbrace{\bar A_t\Delta S_{t-1}}_{已有差异的延续}
+\underbrace{\Delta A_t\bar S_{t-1}}_{处理算子变化作用于旧状态}
+\underbrace{\Delta B_t}_{当步加性写入变化}}.
\]

第二项再记为\((\Delta\alpha)\bar S-\Delta(\alpha\beta kk^\top)\bar S\)，分别记录整体衰减与定向修正的差异；保留方向、抵消和共享key变化。β/k同时进入两项是实际事实，**不把它们强分成两个独立生物式通道**。

关键解释：看到\(A^TS^T-A^CS^C\)不同，不足以说“保留规则变了”，因为旧S本来已经不同。上式单列了这两种来源。看到β变化也不等于旧状态处理贡献大，必须看它作用于当时的旧状态后产生什么向量/矩阵变化。

所有平均、乘积、分项只在离线分析执行；\(\bar A\)、\(\bar S\)及分项不送回模型，不要求它们可由一个原生前文产生。它是两条实际轨迹之间的精确记账约定，**不是三种独立干预的因果效应**。

###### 要输出什么数，而非只画热点

1. 每token/层/头的ΔS和上述三项；同时记录Frobenius范数、与实际ΔS的内积和各项相互内积，避免大幅抵消被总范数掩盖。
2. 离线递推两个累计账目：\(Z^W_t=\bar A_tZ^W_{t-1}+\Delta B_t\)，\(Z^R_t=\bar A_tZ^R_{t-1}+\Delta A_t\bar S_{t-1}\)。相同零初态下，其和重建ΔS；非零共同起点另记录初态项。它们不是可直接替换的两套缓存。
3. 按“事实陈述、问题/作答指令、撤针后候选”预标注区段汇总差异来源，保留精确token位置。区段根据题面/模板标注，在查看内部量前冻结；窗口按文本定义，不按最大效应截取。
4. 用两种等价端点记账再做敏感性分析：\(A^T\Delta S+\Delta A S^C+\Delta B\)和\(A^C\Delta S+\Delta A S^T+\Delta B\)。若换记账背景就改变“哪一项更重要”的排序，则输出“背景依赖/耦合”，不选最有利版本。
5. 原生重建误差单列。浮点下逐步舍入与chunk重排误差不是写入/旧处理机制；若误差与待解释项同量级，该项不可解释，停止分解结论，不把残差强塞进某个过程。

不按范数最大宣布“主要原因”，不算自然因果贡献百分比。分项在ΔS方向上的投影可正可负、可大于总量；ΔS近零时不除以它，只报告绝对量和抵消。

##### 6. 分析二：什么时候形成，是否进入真正读取

**时间分析。** 对每个原生C/T，另在离线将加性项B按输入区段标记来源，沿该轨迹自己的完整A继续传播。检查事实区段产生的代数分量到撤针时还留下多少、朝哪个方向，后续输入又新增/抵消什么。跨C/T的分量差异同时包含原写入差异和后续处理差异，不能直接解释为纯遗忘；与第5节共同判读。

“来自事实token的分量”只表示计算来源，不等于独占事实语义。事实信息可能在后续token重复写入；一个事实token也含有格式和语法信号。两事实版本保留，用来检查规律是否与事实变化对应，不训练高维语义probe、不把距离缩小叫知识删除。

**局部读取分析。** 对更新后实际状态及规范化、缩放后的实际q，raw head读出为\(o_t=S_t^\top q_t\)。对称记账为：

\[
\Delta o_t=(\Delta S_t)^\top\bar q_t+\bar S_t^\top\Delta q_t.
\]

前项再由\(Z^W,Z^R\)分账，后项保留为查询变化。这里测的是实际局部读出差，不是首步logit的自然路径效应。随后对照真实gated norm、out_proj、L19边界输出和最终分数；不假定小的raw差异在后面不会被放大，不用未验证的线性logit近似硬连行为。

**端点对应。** 每个输入把这些过程量与旧D、新采集原始首步logits、原候选逐token分数并排展示。事实敏感度仍按原target_index定向；状态矩阵记S，事实敏感度报告中记S_fact以免混淆。自由回答旧标签保留，不能因为某个候选分数改善就重判能力。

首次分叉的候选token及共同前缀标明；两候选在不同历史下的多token总分不等同于同一时刻的二选一logit。C/T在同一候选内部使用完全相同的token，避免把生成文字分叉误记为缓存差异。

##### 7. 第一阶段怎样决定第二阶段

下面是待数据检验的分支，当前没有任何一行被判定成立。“较弱”只作连续比较，不等于零；只有误差界以内才记作当前精度未分辨。必须同时报告两个T锚点、六情景、所有目标头及反例；不在6个情景上做高维拟合后报训练R²。

| 第一阶段实际结果 | 得到的认识/被削弱的解释 | 第二阶段最值得检验的对照与不同预测 |
| --- | --- | --- |
| 新差异集中在事实输入期间的ΔB，累计写入账目进入实际读出；旧处理项在不同记账下均较小 | 优先考虑“早期形成的写入差异延续”；仅靠后期处理改变的解释缺少对应证据 | 原针仅开在事实结束前 vs 仅开在事实结束后，均保持各自完整轨迹。预言：前者更能重现所观测的状态/读出方向，后者较弱；若相反，否定该时间机制。不能只凭前者有效就认证纯写入 |
| 事实段后的ΔA作用项持续产生差异，旧来源分量在后段分离并进入读出 | 优先考虑“后续处理参与重塑已有信号”；只在最初写坏一次不够 | 先用共同干净前缀形成历史，再仅在预定后段开启原针，与无针和前段有针/后段撤针对照。预言：无需先污染事实输入也能在后段重现特定旧来源分量的变化。必须同时记录ΔB，后段写入共变则不能称纯保留效应 |
| 两项均大且抵消、共享key/β变化强，或排序随记账背景反转 | 目前不存在稳健的“单一过程主导”；耦合本身是观察，不是已证明协同因果 | 第二阶段使用原针前段开关×后段开关的完整时序四格（每臂自身前向，不拼缓存），检验时序条件依赖及阶段一预测。它先识别时段效应；若内部两项仍共变，不宣布独立W/R贡献 |
| ΔS存在，但局部读出主要对应Δq或后续门/归一化变化，或状态账目与读出对不上 | 形成了状态差异，不足以把它认定为当前行为载体；“只看状态”解释不足 | 第二阶段优先针对原生读取条件提出对照，而不是再做写入/保留补偿。须先写出候选读取解释的不同预测；不能从本阶段自动跳到某个查询替换方案 |
| 原始C/T在本窗口的过程模式不稳定，或只在历史人工交叉格异常 | 此窗口尚不足以支撑形成机制解释；旧拼接效应不能替代原始轨迹证据 | 暂不做本窗口的W/R因果网格。先报告不支持/不足；是否转查其他已记录位置须有新的具体依据，不自动扫层 |
| 工程回放、归一化或重建误差未通过 | 尚不能判断机制 | 停在工程验收，保留失败；不推进第二阶段 |

前两行可以共存，不强制二选一。若采用时序四格，前段E定义为模板开始到事实陈述末，后段L为其后到撤针边界；四臂是00、10、01、11，00/11沿用原C/T身份。保持相同token、原单步剂量/校准；10/01的针次数可能不同，不宣称等总能量比较。若解释依赖纯时长而非内容位置，需要在第二阶段另明确匹配对照，不能把四格自动当作内容特异性证明。

**重要边界：时间开关干预不自动等于写入/旧处理的独立干预。** 它的价值是检验阶段一提出的形成顺序和必要条件，而且避免跨来源拼接。如果两条路径在所有可用操作中仍共同变化，第二阶段只能报告可识别的时序作用，不能承诺必然得到唯一的两份因果比例。

##### 8. 验收与交付，不用“又需要下一轮”掩盖无效

第一阶段达到以下三项才算科学分析完成：

1. 逐题给出差异形成账本、数值残差、时间区段和真实局部读取联系；明确哪些量来自实测、哪些来自离线重建，分项边界随记账方式是否改变。
2. 对每个锚点给出至少一条可被后续结果否定的陈述，或明确结论为“当前观测不能选择机制分支”；不能只交付层/头热点图。
3. 选定下一对照时，同时列出至少两个解释的不同预测以及什么结果使当前解释失败。若候选解释在拟议对照下预测完全相同，该对照不进入第二阶段。

预期交付是一个字段/来源清单、一份逐token过程表、一份按六情景汇总的方向/反例表，以及一页第二阶段决策。统计单位是基础情景，不是token或头；两事实、候选和层头不充当独立样本。六情景只作探索描述，报告范围与逐情景结果，不承诺总体检验功效、不通过删题制造一致性。

**当前状态：完成设计和资料可用性核查。核心轨迹缺失，因此尚未完成上述过程分析。先复用可找到的原始轨迹，确无足够记录时，新增成本仅为原C/T观测重放与短候选读取；不执行r04的补偿或S/O交换网格。**

---

### 原件 2：缓存形成机制｜CFM-S1｜实验合同 r01

原路径：`experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/CONTRACT.zh-CN.md) · [单独阅读副本](../library/128ff4163f8e5fa5.md)；SHA-256：`128ff4163f8e5fa5e516e8691bfb016e8a5d800abf22a144faad24e7b4cf2fa2`。

---

#### 缓存形成机制｜CFM-S1｜实验合同 r01

- 计划编号：`CFM-S1-v1-20261031`；计划正文：[`docs/cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md`](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md)（main f17da0a，内容与 2b1c306 相同，只改了名）。
- 本合同把计划第 4–8 节写成可执行的定义、判据、阈值和停止条件。冻结（`freeze-r01.json`）后不改；任何偏离记入 `IMPLEMENTATION.zh-CN.md` 的决策日志。
- 运行授权：用户 2026-10-30 指示"根据实验计划把代码和通路全部写完，然后跑测试，跑完测试以后直接上服务器实验……实验跑完以后结果推上 Git"，并于同日指定按 CFM-S1 命名实现。

##### 1. 对象（计划 §4，不改）

| 项 | 取值 |
|---|---|
| 模型 | Qwen3.5-4B，revision `851bf6e8…`，BF16，eager，原模板，冻结依赖（`early-input-control-v1` contract.json 的权重哈希、torch 2.6.0+cu124、transformers 5.20.2） |
| 条件 | C（`clean`）、L0/C4146/−1（`N_L00_C4146_D-1`）、L12/C3621/−1（`N_L12_C3621_D-1`）；两个 T 各自只与同输入 C 比较 |
| 输入 | VAR01、VAR02、VRD01、VRD02、VRL01、VRL02 × 两个事实版本 = 12（`early-state-localization-stage2-v2` 的 `data/validation-r01.json`；旧题，不是独立确认） |
| 校准 | 原规则：每情景 f0 无针提示的逐层残差中位范数（`calibrate`），两事实共用；必须与 II-B 归档逐值相同 |
| 时序 | T 只在 `prompt[:-1]` 全部位置加针（`_control_hooks` prefill 模式）；末提示 token 与候选评分无针；C 全程无针 |
| 观测 | L16–18 全部 32 个递推头；L16 入口、L19 入口、L19 出口残差 |
| 读取 | 末提示 token 的原始全词表 logits；两条固定候选从**本条轨迹自己的**末提示后缓存分别 teacher forcing（与 II-B `score` 相同：喂候选前 m−1 个 token），逐 token 对数概率 |
| 新增自由生成 | 0 |

##### 2. 记录（只读，不改前向）

`Qwen3_5GatedDeltaNet.forward` 按模块全局名调用 `torch_chunk_gated_delta_rule`（prefix，分块 64）与 `torch_recurrent_gated_delta_rule`（单 token）。记录器在调用期间把这两个全局名换成透传包装：原样传参调用原函数、原样返回，调用前克隆初态，另记 q/k/v（卷积、头扩展后，进入内核前）、g（=log α）、β、内核输出、内核末态。其余量用 forward hook 读：`in_proj_qkv` 输出（卷积前）、`in_proj_z`、`in_proj_b`、`in_proj_a`、gated norm 输出、`out_proj` 输出，L16 入口 / L19 入口 / L19 出口残差。暴露的真实状态：prefix 末（撤针边界）、末提示 token 后、每条候选分支末的递推矩阵与 conv 缓冲。事实段末、问题段末等中间状态内核不暴露，**标为离线重建**，不为取它而改分块。

##### 3. 阶段、规模与闸门

| 阶段 | 内容 | 规模上限 | worker |
|---|---|---|---|
| preflight | 预定输入 `VAR01-f0-required` × C/L0/L12 | 3 前缀 + 3 末提示 + 6 候选 | 1（门槛需同一输入的三条件，单卡） |
| formal | 12 输入 × 3 条件 | 36 + 36 + 72 | 2（每卡 1 个；单位为情景，轮转分配） |

每条记录的硬闸门（任一不符即停该 worker 并整轮停止，不自动重试、不扩题、不换内核）：

- **R1 复现**：校准、提示 token 哈希、prefix 后全部 64 个缓存张量的哈希清单、首步 logits 哈希 / top5 / 停止优势、两条候选逐 token 对数概率，与 II-B 归档（`data/reference-r01.json`，来源 `b_validate-r01.tar.zst` sha `f56663e1…`）**逐值相同**。
- **R2 调用计数**：每个观测层 prefix 恰 1 次分块调用，末提示与每个喂入的候选 token 各 1 次递推调用。
- **R3 内核身份**：四个函数均解析到 `modeling_qwen3_5` 的 torch 实现；`fla`、`kernels`、`causal_conv1d` 均未安装。
- **R4 未改动**：钩子全部移除，模型权重哈希前后不变；prefix 缓存在评分后不变。

preflight 另加：

- **P1 惰性**：同一轨迹不装记录器重跑，缓存清单、首步 logits 哈希、候选逐 token 对数概率与 logits 哈希逐字节相同。
- **P2 捕获一致**：由捕获的卷积前 qkv、a、b 在同一设备上重算的 q/k/v、g、β 与内核实际输入逐位相同；缓存递推状态等于内核末态。
- **P3 重建**（§4 容限）：三条轨迹都通过。

formal 需要 preflight 核验 `status: passed` 的文件写入授权。

##### 4. 工程容限（离线预演前写死；account.py `TOL`）

- 状态：离线 float64 逐步递推与内核在每个暴露状态上的相对 Frobenius 误差 ≤ **1e-3**。
- 读出：每 token 的 raw head 读出（全部头合并）相对误差 ≤ **1e-2**（内核输出为 BF16，舍入约 2⁻⁹）。
- 恒等式：ΔS 三项和、Z^W+Z^R、Δo 两项和与直接差的相对残差 ≤ **1e-9**；收缩界 ‖ĀX‖ ≤ (1+1e-9)‖X‖（推导档：α≤1、β∈(0,1)、‖k‖<1 时 A 的谱范数 ≤1，凸组合仍 ≤1）。
- 分辨率：数值底 F = 末提示后暴露状态的绝对重建误差（T + C）。‖ΔS_{t_L}‖ ≤ **10F** 的格记为"当前精度未分辨"，不参与分支判读。

任一项不过：停在工程验收，产出 `stopped_engineering`，不做分解结论（计划 §5.5、§7 末行）。

##### 5. 分析定义（计划 §5–§6）

记号：S_t = A_t S_{t−1} + B_t，A_t = α_t(I − β_t k_t k_tᵀ)，B_t = β_t k_t v_tᵀ，o_t = S_tᵀ q_t；k、q 为内核约定的 l2 归一化（eps 1e-6），q 乘 d_k^{−1/2}。Δ = T − C，上横线为两条实际轨迹的算术平均。

1. **逐 token 三项**：ΔS_t = ĀΔS_{t−1}（延续）+ ΔA S̄_{t−1}（处理算子变化）+ ΔB（加性写入变化）；ΔA S̄ 再分为 (Δα)S̄（整体衰减）与其余（定向修正）。记各项 Frobenius 范数、与 ΔS 的内积、两两内积，按头合并并保留逐头数组。
2. **累计账**：Z^W_t = Ā Z^W_{t−1} + ΔB_t，Z^R_t = Ā Z^R_{t−1} + ΔA S̄_{t−1}，零初态，Z^W+Z^R = ΔS。两种端点记账同算：T 背景 A^T·, ΔA S^C；C 背景 A^C·, ΔA S^T。三套账都按产生项所在区段拆分（7 段，可加）。
3. **区段**（`data/segments-r01.json`，只按文本规则生成，在看任何内部量之前冻结）：head（模板头）、fact（用户文本中 `\n问题：` 之前）、question（到 `\n请根据` 之前）、instruction（用户文本其余）、tail（模板尾）、last（末提示 token，无针）、cand（候选）。token 归属其首字符所在段，跨段 token 列出。E = head+fact，L = question+instruction+tail。
4. **自身来源分量**：每条轨迹用自己的完整 A 传播各段的 B（P^{X,s}，Σ_s = S^X），报告份额、范数、P^{T,s}−P^{C,s} 与 ΔS 的内积。只表示计算来源，不等于事实语义。
5. **局部读取**：Δo_t = ΔS_tᵀ q̄_t（状态部分，再按 Z^W/Z^R 及区段分账）+ S̄_tᵀ Δq_t（查询部分）。另对照实测的内核输出差、gated norm 输出差、out_proj 输出差、L19 出口差；不用线性 logit 近似连到行为。
6. **端点**：每情景 D（首步停止优势，两事实等权）、S_fact = [ll(A)−ll(B)]|A 正确 − [ll(A)−ll(B)]|B 正确、首步 EOS；候选共同前缀长度另标。

统计单位是基础情景（6 个）；事实版本、层、头、token 不当独立样本。不报 p 值、不报"因果贡献百分比"。

##### 6. 第二阶段判读规则（计划 §7，预注册）

判读时点 t_L = 末提示 token 更新之后（首个回答读数所用状态）。每个（锚点, 情景）把两事实 × 三层合并：份额 = Σ⟨分项, ΔS⟩ / Σ‖ΔS‖²（读出份额对 Δo 同理），抵消比 = Σ(‖Z^W‖+‖Z^R‖) / Σ‖ΔS‖（对称账）。

主设定（account.py `RULES['main']`）：

| 分支 | 条件 |
|---|---|
| readout_disconnect（计划第 4 行） | 读出状态份额 ρ_state < 0.5 |
| coupled（第 3 行） | 抵消比 ≥ 2，或三套账中 W>R 的次序不一致 |
| early_write（第 1 行） | 非上两类，且三套账的 W_E 最小值 ≥ 0.5、R 最大值 ≤ 0.3 |
| late_processing（第 2 行） | 非上两类，且三套账的 R_{L+last} 最小值 ≥ 0.3 |
| unclassified / unresolved | 都不满足 / 未过 10F 分辨率 |

第 1、2 行可同时成立。锚点层面：某分支在 ≥ **4/6** 个情景成立才算"该锚点支持"；没有分支达到 → **unstable_or_insufficient**（第 5 行，暂不做本窗口的因果网格）；工程未过 → 第 6 行。另报两套敏感性设定（strict：0.6/0.2/0.4/ρ0.6/抵消 1.5；loose：0.4/0.4/0.2/ρ0.4/抵消 2.5），三套设定的锚点判读不一致时标 `threshold_sensitive`，报告以主设定为准并写明。

各分支对应的第二阶段对照与不同预测照抄计划 §7 表，不在本阶段增删。判读输出是"下一对照选哪一个"，不是机制结论。

##### 7. 预注册预测（6.4）

- **推导档**：§4 的恒等式与收缩界必然成立，违反即代码错误（工程失败，不是科学结果）。
- **科学定量预测：无。** 计划明确不预设任何一行成立，也没有可推导的定量预测；本合同不补编。
- **推测档先验**（只用于事后对照自己的偏差，不进判据）：L12 锚点的注入层就在观测窗口上游，猜 early_write 或 coupled；L0 锚点经过 16 层传播，猜 coupled 或 unstable。

##### 8. 零假设与失败类型（6.3、6.7）

- 本阶段是确定性前向上的精确记账，没有抽样噪声，份额不是统计估计；"差异存在"的零值不取 0，而取数值底 10F（§4）。分支阈值是描述性切点，报告同时给出连续值和敏感性。
- 失败类型：R/P 闸门或 §4 容限不过 = **合同执行失败**（信息量为零，不当负面证据）；判出 unstable_or_insufficient = **没拿到结果**（窗口不足以选分支）；锚点判读与推测档先验相反不算失败。

##### 9. 停止条件

1. preflight 任一闸门不过 → 停，不进 formal，不修代码重跑同一授权（另立 r02 须新授权）。
2. formal 任一记录闸门不过 → 整轮停止，保留部分记录。
3. 离线重建或恒等式不过 → 停在工程验收，不输出分支判读。
4. 规模超 §3 上限 → 停。

---

### 原件 3：CFM-S1 结果报告：原始 C/T 轨迹上 L16–18 递推状态差异的形成、记账与读取

原路径：`experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/REPORT.zh-CN.md) · [单独阅读副本](../library/576c1141f353eff3.md)；SHA-256：`576c1141f353eff3a00546961f34dc2a200a1f049498bcce87194211f2a28a48`。

---

#### CFM-S1 结果报告：原始 C/T 轨迹上 L16–18 递推状态差异的形成、记账与读取

日期：2026-10-30（UTC）。计划 `CFM-S1-v1-20261031`；合同 r01（冻结提交 f73147b，freeze sha `3ece676b…`）；运行 preflight-r01、formal-r01；离线记账 `analysis/accounts-r01.json`。

##### 0. 先说不利的部分

1. **合同判读是"两锚点都是 coupled"（6/6 情景，三套阈值设定一致），但这个判读信息量低。** 触发的是抵消比 ≥ 2 这一条（三套账 W>R 次序一致，没有翻转）。合同外、零 GPU 的探索性对照显示，同一套记账用在**无针的自然事实差异**上（同一情景两个事实版本的 C 轨迹配对），抵消比也有 1.95–2.19，主设定下 5/6 同样判 coupled。也就是说，"≥ 2" 这道阈值落在本模型 delta rule 记账的常态水平上。
2. **这是我写合同时的错误**：抵消比和各项份额只用数值底标定了"非零"，没有用对照条件标定零分布（研究准则 6.3）。判读按合同照实记录，不改；下文凡是和自然差异做比较的内容，都是**探索档**（决策日志第 10、11 条）。
3. 这些都不是合同执行失败：工程闸门、重建、恒等式全部通过，数据有效。问题出在分支切点的设计上，影响的是"coupled"这个标签能说明什么，不影响下面的数值。

##### 1. 工程验收（全部通过）

| 项 | 结果 |
|---|---|
| preflight（VAR01-f0 × C/L0/L12） | 复现、惰性（有无记录器逐字节一致）、捕获一致、重建全部通过；29 s |
| formal（36 条，双卡各 1 worker） | 36/36 对 II-B 归档逐值复现（校准、64 个缓存张量清单、首步 logits 哈希 / top5 / 停止优势、候选逐 token 对数概率）；52 s；核验 passed |
| 内核 | 四个函数均为 transformers 5.20.2 的 torch 实现；fla / kernels / causal_conv1d 均未安装 |
| 离线重建（float64） | 状态相对误差最大 8.8×10⁻⁷（容限 10⁻³）；读出最大 2.5×10⁻³（容限 10⁻²，BF16 舍入量级）；数值底 ≤ 1.2×10⁻⁶，所有格子 ‖ΔS‖ 约 2–3，全部可分辨 |
| 恒等式与收缩界 | 三项和、Z^W+Z^R 的相对残差 ≤ 1.7×10⁻¹⁵，Δo 两项和 ≤ 6.0×10⁻¹⁵（勘误 2026-10-31：原文把三者统一写成 ≤ 1.7×10⁻¹⁵，由 S1 结果复核指出）；‖ĀX‖/‖X‖ 最大 0.9998 |

规模：36 前缀 + 36 末提示读取 + 72 候选；没有新增自由生成。

##### 2. 端点（与 II-B 原值相同）

| 情景 | C：D / S_fact | L0 原针：D / S_fact / 首步 EOS | L12 原针：D / S_fact / 首步 EOS |
|---|---|---|---|
| VAR01 | −19.5 / 15.07 | 1.7 / −0.05 / 2/2 | −10.1 / 1.00 / 0/2 |
| VAR02 | −16.5 / 21.35 | 1.7 / 0.07 / 2/2 | −9.5 / 16.15 / 0/2 |
| VRD01 | −20.8 / 22.64 | 1.1 / 0.57 / 2/2 | −12.9 / 13.66 / 0/2 |
| VRD02 | −14.9 / 24.87 | 1.1 / 0.42 / 2/2 | −9.0 / 9.38 / 0/2 |
| VRL01 | −21.7 / 5.35 | 0.9 / 0.12 / 2/2 | −11.3 / 0.63 / 0/2 |
| VRL02 | −19.2 / 16.61 | 1.6 / −0.25 / 2/2 | −10.3 / 1.63 / 0/2 |

D = 首步停止优势（两事实等权），S_fact = 事实敏感度（阶段二定义）。

##### 3. 问题一：新增差异来自哪类运算

t_L（末提示 token 更新后）三层合并、两事实合并的份额（对 ΔS 的投影，可为负、可 >1）：

| 量 | L0 原针（6 情景范围） | L12 原针 | 自然事实差异（探索档） |
|---|---|---|---|
| ‖ΔS‖ / ‖S_C‖ | 0.81–0.98（逐层） | 0.72–0.83 | 0.03–0.13 |
| W（累计加性写入账） | 1.50–1.55 | 1.35–1.40 | 1.13–1.19 |
| R（累计旧状态处理账） | −0.48 ~ −0.55 | −0.35 ~ −0.40 | −0.13 ~ −0.19 |
| T 背景 / C 背景下的 W | 2.00–2.22 / 1.48–1.55 | 1.26–1.32 / 1.74–1.94 | 1.13–1.18 / 1.12–1.19 |
| 抵消比 (‖Z^W‖+‖Z^R‖)/‖ΔS‖ | 2.92–3.10 | 2.81–2.98 | 1.95–2.19 |

读法：

- 两个锚点下，原针都让 L16–18 的递推状态改动到干净状态本身的量级（推导：直接测量）。
- 在 A/B 定义下，加性写入账总是**超出**实际差异，旧状态处理账与之反向。这一点自然差异也有：delta rule 写入 v 时，会经由 −αβkkᵀS 扣掉状态已能预测的部分，ΔB 与 ΔA·S̄ 天然部分抵消（推导：更新规则的代数结构；合成预演里的 coupled 世界就是这个机制）。原针的特征是抵消**更强**：R 约为自然差异的 2–4 倍，抵消比约 3 对约 2.1（探索档，只有一个对照族）。
- 背景依赖：W 份额随记账背景变化 0.4–0.75，但 W>R 的次序在三套账中都不变。L0 在 T 背景下 W 更大，L12 在 C 背景下 W 更大，两个锚点方向相反（描述，未解释）。
- 不能把 W 读成"新内容写入的因果贡献"。β、k 同时进入两项，这是共变下的记账，不是两种独立干预的效应（计划 §5）。

##### 4. 问题二：何时形成、撤针后发生什么

逐区段每 token 平均的新增项（三层分别报告，下表取范围）：

| 区段 | L0：‖ΔB‖ / ‖ΔA·S̄‖ | L0：段末 ‖ΔS‖ | L12：‖ΔB‖ / ‖ΔA·S̄‖ | L12：段末 ‖ΔS‖ |
|---|---|---|---|---|
| head（3 token） | 0.43–0.55 / 0.12–0.16 | 0.74–1.01 | 0.66–0.75 / 0.12–0.18 | 1.09–1.22 |
| fact | 1.00–1.54 / 0.54–0.73 | 2.37–2.93 | 0.74–0.99 / 0.43–0.45 | 2.01–2.25 |
| question | 1.04–1.62 / 0.56–0.83 | 2.69–3.18 | 0.79–1.08 / 0.48–0.51 | 2.25–2.33 |
| instruction | 0.89–1.62 / 0.50–0.81 | 2.90–3.32 | 0.68–1.09 / 0.44–0.49 | 2.48–2.52 |
| tail（模板尾） | 0.93–1.55 / 0.50–0.77 | 3.03–3.40 | 0.77–1.07 / 0.46–0.53 | 2.49–2.74 |
| last（无针） | 1.33–2.05 / 0.56–0.79 | 3.04–3.42 | 1.23–1.65 / 0.46–0.76 | 2.60–2.83 |
| 候选（无针，均值） | 1.63 / 0.87 | 3.14 | 0.75 / 0.33 | 2.51 |

- **差异不集中在事实陈述期**：针在的每一段，每个 token 都产生大小相近的新写入差异，处理项约为写入项的一半。‖ΔS‖ 在事实段末就到了终值的 73–95%，之后饱和：新写入与旧差异被衰减、修正抵掉大致平衡。
- t_L 处 ΔS 按产生区段分账（对称账，W+R 净值）：head+fact 只占 0.07–0.18，question 到 last 占 0.82–0.93，其中 tail + last 为 0.47–0.74。**这大半是近因结构，不是原针特有**：干净轨迹自身的 t_L 状态就有 37% 来自 tail、22% 来自末提示 token、9% 来自 fact（自身来源分量 P^C）。自然事实差异的 W 中 fact 段份额是 0.14–0.68，tail 仍有 0.23–0.54，说明单个事实 token 的变化也经由后续 token 的驱动量重新写入。
- **撤针后差异继续产生**：末提示 token 没有针，单 token 写入差异却是全程最大（L0 1.33–2.05，L12 1.23–1.65）。针撤了，上游其余缓存的差异仍让 L16–18 的 q/k/v/α/β 偏离 C。
- **两个锚点在撤针后分开**：候选阶段 L0 的写入差异维持在加针时的水平（1.63，对比 tail 1.31），L12 降到约一半（0.75，对比 tail 0.97）。L0 原针在 L16–18 产生的是撤针后自我维持的驱动量偏离，L12 的则开始消退（描述，6 情景；与 early-input-control 的"异常维持"线索一致，属类比档）。
- L0-T 自身的 t_L 状态里 head+fact 的份额是 0.33，C 只有 0.13：L0 原针下早段内容留存得更多（描述）。

##### 5. 问题三：状态差异是否进入实际读取

- 局部读出差 Δo = ΔSᵀq̄ + S̄ᵀΔq，t_L 处状态部分份额 ρ_state：L0 0.66–0.83（逐层）、0.73–0.78（逐情景合并）；L12 0.79–0.99、0.83–0.91。查询变化不是主体，状态差异确实进入了读出方向。
- ‖Δo‖/‖o_C‖：L0 0.66–0.78，L12 0.49–0.53；实测 out_proj 输出差 / 干净输出：L0 1.17–1.35，L12 1.06–1.10。
- **但 L16–18 的状态差异解释不了停止**：两个锚点的 ΔS 与读出差量级相近，只有 L0 首步 EOS（L12 的 D 仍为 −9 ~ −13）。这与阶段二"L0 停止不由单组承载"一致：停止不由这一窗口的状态差异大小决定（描述，不是因果检验）。

##### 6. 可被后续结果否定的陈述（计划 §8.2）

1. **两锚点**（推导 + 描述）：t_L 处 L16–18 的 ΔS 中，head+fact 段产生的净分量只占 0.07–0.18。若第二阶段只在 E 段（模板开始到事实末）开针（四格的 10 臂），t_L 状态差异应明显小于 11 臂、10 臂 ‖ΔS‖/‖ΔS_11‖ < 0.5；只在 L 段开针（01 臂）应重现大部分 t_L 差异。若 10 臂 ≥ 0.5，"差异主要由针在场时的近期写入维持"这一读法即被否定。注意：E 段的针也会通过其他层改变后续 token 的驱动量，所以 10 臂不是"纯早期写入"（推测档）。
2. **L0 与 L12 不同**（描述 → 推测）：L0 撤针后写入差异不衰减，L12 衰减。预测：四格的 10 臂中，L0 在 L16–18 留下的 t_L 差异占 11 臂的比例高于 L12。若两者相同或 L12 更高，"L0 驱动量偏离自我维持"的读法即被否定。
3. **抵消强度**（探索档）：原针的抵消比约 3、自然事实差异约 2.1。在第二阶段先补一族零对照（随机方向或其他通道的同剂量针），再判断约 3 是否超出该零分布；在此之前，"原针的写入与处理耦合得比自然差异强"只算线索。

##### 7. 第二阶段选择（按合同 §6 与计划 §7）

- 合同判读：两锚点都落在计划 §7 第 3 行（两项均大且抵消），对应的第二阶段对照是**原针前段开关 × 后段开关的完整时序四格**（00/10/01/11，每臂自身前向，不拼缓存）。
- 但第 0 节已经说明，这一行的触发并不特异。第二阶段在进入四格之前要补的一件事：**给抵消比和 W/R 份额建一个零分布**（随机方向针、其他通道的同剂量针，以及本报告用过的自然事实差异），把合同的描述切点换成"落在零分布之外"的判据。这件事需要新合同和新授权，本阶段没有做。
- 四格对两锚点给出不同的预测（第 6 节第 1、2 条），满足计划 §8.3"至少两个解释的不同预测"；它识别的是时段效应，不是独立的 W/R 因果比例（计划 §7 末段）。

##### 8. 范围与限制

- 6 个旧情景、12 输入，都是已经打开过的题，不是独立确认；统计单位是情景，层、头、token、事实版本都不当独立样本。
- 只看 L16–18；L19 及以后、KV 路径没有分账（边界残差差值已记录在 `boundary`）。
- 中间状态（事实段末、问题段末）是离线重建，不是内核实测；重建误差在 10⁻⁷ 量级。
- 候选只用 teacher forcing，结论只涉及固定候选，不涉及自由回答的完整机制。
- 自然事实差异对照是合同外的单一对照族，只用于说明切点不特异，不当零分布。

##### 9. 文件

- 记录与收据：`runs/preflight-r01/`、`runs/formal-r01/`（JSON；张量 `.pt` 不进 git，服务器 `runs/*/worker-*/tensors/`，归档 `/workspace/cfm-s1-ops/archive/runs-r01.tar.zst`（6.5 GB，sha256 `c57519c3…0714fbcd`），每个张量的 sha256 见记录与收据）。
- 记账：`analysis/accounts-r01.json`（重建、恒等式、判读、端点、边界、区段汇总）、`analysis/tokens-r01.jsonl.zst`（逐 token × 层 × 配对的全部标量，4,416 行）、`analysis/heads-r01.pt`（逐头数组）。
- 探索档：`analysis/explore_natural_pair.py`、`analysis/exploratory-natural-pair-r01.json`。

---

### 原件 4：CFM-S1 实现说明与决策日志

原路径：`experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/IMPLEMENTATION.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/IMPLEMENTATION.zh-CN.md) · [单独阅读副本](../library/a7a7b1c10bd85e44.md)；SHA-256：`a7a7b1c10bd85e44cda06127d14ad3f9c8c1bfabdd13c012102e4c5f48b03e3e`。

---

#### CFM-S1 实现说明与决策日志

日期：2026-10-30（UTC）。计划 `CFM-S1-v1-20261031`；合同 [CONTRACT.zh-CN.md](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/CONTRACT.zh-CN.md) r01。

##### 文件

| 文件 | 作用 |
|---|---|
| `cfm_trace.py` | 透传记录器、单条轨迹（C/T 原路径）、复现与惰性闸门、冻结 / 授权 / worker / 控制器 / 核验 |
| `account.py` | float64 离线重建与工程门、三项对称记账与两种端点记账、区段拆分、自身来源分量、局部读出、§6 判读规则；`selftest` 为合成预演 |
| `build_reference.py` | 从 II-B 归档 `b_validate-r01.tar.zst` 取 36 条参考记录、6 份校准、缓存清单，生成 `data/reference-r01.json` |
| `test_cfm_trace.py` | 在 8 层随机初始化 Qwen3.5（层 4–6 线性 + 7 全注意力，代替 L16–18 + L19）上的 CPU 测试，不加载权重 |
| `data/reference-r01.json` | 每条轨迹必须逐值复现的 II-B 值 |
| `data/segments-r01.json` | 按文本规则生成的区段标签（只用分词器，在看任何内部量前生成并冻结） |

代码来源：直接 import 阶段二 `stage2.py`（缓存清单、管理状态、条件表）及其引入的阶段一 `localize.py`（`forward`、`_build_T`、`_clean_cache`、`score`、`decode`）和 `control_engine.py`（注入、校准）。递推公式与 transformers 5.20.2 `torch_recurrent_gated_delta_rule` 逐行对照；记账结构借 WriteSAE v4 附录 A 的写入—传播—读取顺序，不训练 SAE。

##### 决策日志（偏离计划或计划未覆盖的判断）

1. **计划 §2 引用的 `cache-complement-analysis-v1-2026-10-31/` 与 `docs/cache-mechanism-path-audit-2026-10-31.zh-CN.md` 不在 main（f17da0a）上，服务器上也没有。** 本实现不依赖它们；36 条原参考直接从 II-B 归档（`/workspace/stage2-ops/archive/b_validate-r01.tar.zst`，sha `f56663e1…`，与 `b_validate-r01.verify.json` 一致）重建，每条记录逐值复现（合同 R1）。影响：计划 §2 表里来自那两份文件的数字（如 L0 四格 24 输入）本实验没有复核。
2. **旧轨迹复用检查**（计划 §2"先按旧清单检查是否有同身份归档"）：II-B 归档只有缓存哈希清单与 `gate_decay` 摘要，没有 `.pt/.npy` 张量；服务器 `/workspace/stage2-ops/` 也没有。确无可复用轨迹，按计划新采集。
3. **中间状态**：prefix 是一次分块调用，内核只暴露 prefix 末状态；事实段末、问题段末状态标为离线重建（计划 §4 允许），不拆分 prefix。
4. **候选分支末状态**：与 II-B `score` 完全相同，只喂候选前 m−1 个 token（最后一个 token 只作为被评分目标）。"评分分支末"指喂完第 m−1 个 token 之后的状态。
5. **末提示 token 单列为 `last` 段**，不并入 L（计划 §7 的 L 定义为"事实后到撤针边界"）；判读规则里的 R_late 用 L+last，在合同 §6 写明。
6. **worker 数**：preflight 是一个不可拆的门槛任务（同一输入的三条件），只占一张卡；formal 双卡各 1 个 worker（36 条前缀很短，每卡多 worker 没有收益）。
7. **"旧 D"** 取阶段二定义：D = 首步停止优势，S_fact = 两事实候选对数似然差之差（`analyze_stage2.py` 的 `D_by_base` / `S_by_base`）。
8. **判读阈值**：计划 §7 只给出分支的定性描述；合同 §6 的数值切点（0.5/0.3/0.3/ρ0.5/抵消 2、4/6 情景）是我定的描述性切点，同时预注册两套敏感性设定。计划对这些数字没有规定，它们不来自任何已看过的数据。
9. **合成预演**的 "coupled" 世界第一版（大幅改 key，后改为强后段衰减）都没造出抵消，判据阈值未改；改成 delta rule 的冗余重写（同一 (k,v) 反复写入，β 不同，ΔB 与 ΔA S̄ 逐步抵消）后 5/5 判到 coupled。这是合成世界构造的修正，不是判据修改。

10. **合同外探索分析（运行后，看过主判读之后）**：主判读两锚点都是 coupled，触发条件是抵消比 ≥ 2。为判断这个标签是否特异，在 `analysis/explore_natural_pair.py` 中对同一情景两个事实版本的 C 轨迹（token 位置一致，无针）跑同一套记账。结果：抵消比 1.95–2.19，主设定下 5/6 判 coupled。只读已核验的张量，零 GPU；不改合同判读。影响：报告第 0、3、6、7 节中凡涉及"原针与自然差异比较"的内容都标为探索档。
11. **合同设计错误（我的错误）**：§6 的分支切点只用数值底标定"非零"，没有用对照条件标定零分布（研究准则 6.3）。抵消比切点 2.0 恰好落在本模型 delta rule 记账的常态上，coupled 判读信息量低。修正建议写在报告第 7 节（第二阶段先建零分布），需新合同。
12. **记录格式**：`gate_decay` 继续记录（与 II-B 相同的汇总），没有用于分析。

##### 运行记录

| 运行 | 时间（UTC） | 结果 |
|---|---|---|
| preflight-r01 | 2026-10-30 19:54 | passed；1 worker（GPU 0）；29 s |
| formal-r01 | 2026-10-30 19:57 | passed；2 worker（每卡 1 个）；36 条；52 s |
| account r01 | 2026-10-30 ~20:00 | analyzed；CPU float64；重建与恒等式全过；主判读两锚点 coupled，三套设定一致 |

##### 测试与预演

- `test_cfm_trace.py` 22 项全部通过（`readiness/cpu-tests-r01.log`、`readiness/cpu-receipt-r01.json`；gqa-h20 `.venv-bench`，torch 2.6.0+cu124 / transformers 5.20.2，CPU，仓库外副本 `/workspace/cfm-s1-ops/cputest`）。覆盖：记录器在 fp32 小模型上逐字节惰性（缓存清单、首步 logits、候选分数）；分支评分与阶段一 `score` 相同；调用计数；全局名与钩子恢复；捕获的 q/k/v/g/β 与 forward 内推导逐位相同；注入层及以前缓存 T=C；针只在 prefix；复现检查对任一处 1e-12 的差都报错；fp32 与 bf16 小模型上重建闸门通过；三项恒等式、Z^W+Z^R=ΔS、区段份额和为 1、自身来源份额和为 1、读出恒等式、收缩界；C 对 C 全零且判 unresolved；计划面板（12 输入、3 条件、36 键、EOS 12/0/0）；区段规则。
- `account.py selftest`：五个合成世界（early_write / late_processing / coupled / readout_disconnect / null）各 5 种子全部判到预期分支，且 early_write 世界从不判入 coupled/readout_disconnect；重建闸门对精确状态通过、对 1e-2 状态扰动和 5% 输出扰动失败；锚点规则 4/6 支持、3/6+2/6 判 unstable；α>1 被收缩检查发现。判据可满足与不可满足两面都演示到。

---

### 原件 5：缓存形成机制｜CFM-S1｜原始轨迹与状态形成分析

原路径：`experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/README.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/README.md) · [单独阅读副本](../library/31e0d29ff329d582.md)；SHA-256：`31e0d29ff329d58250e1f5943a3662c61b5aadd199042b7f464e38dd574998b8`。

---

#### 缓存形成机制｜CFM-S1｜原始轨迹与状态形成分析

计划：[`docs/cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md`](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md)（编号 `CFM-S1-v1-20261031`）。

- 合同：[CONTRACT.zh-CN.md](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/CONTRACT.zh-CN.md)
- 实现与决策日志：[IMPLEMENTATION.zh-CN.md](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/IMPLEMENTATION.zh-CN.md)
- 冻结：`freeze-r01.json`；授权与测试：`readiness/`；运行：`runs/`；离线记账：`analysis/`
- 结果报告：[REPORT.zh-CN.md](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/REPORT.zh-CN.md)

张量文件（`runs/*/worker-*/tensors/*.pt`）体积大，不进 git；它们留在服务器 `/workspace/acupuncture/experiments/<本目录>/runs/`，并打包到 `/workspace/cfm-s1-ops/archive/`。每个张量文件的 sha256 记在对应记录和 worker 收据里。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [readiness/cpu-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/readiness/cpu-receipt-r01.json) | {"status": "passed"} | {"created_at": "2026-10-30T19:51:06.684250+00:00"} |
| [runs/formal-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/runs/formal-r01/controller.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-10-30T19:55:11.300314+00:00", "finished_at": "2026-10-30T19:56:03.043327+00:00"} |
| [runs/formal-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/runs/formal-r01/verification.json) | {"status": "passed", "stage": "formal"} | {"verified_at": "2026-10-30T19:56:03.043152+00:00"} |
| [runs/formal-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/runs/formal-r01/worker-0/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-10-30T19:55:11.376839+00:00", "last_record_at": "2026-10-30T19:55:54.130520+00:00", "finished_at": "2026-10-30T19:55:56.070521+00:00"} |
| [runs/formal-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/runs/formal-r01/worker-1/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-10-30T19:55:11.376742+00:00", "last_record_at": "2026-10-30T19:55:52.907472+00:00", "finished_at": "2026-10-30T19:55:55.007293+00:00"} |
| [runs/preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/runs/preflight-r01/controller.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-10-30T19:54:03.115697+00:00", "finished_at": "2026-10-30T19:54:33.636705+00:00"} |
| [runs/preflight-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/runs/preflight-r01/verification.json) | {"status": "passed", "stage": "preflight"} | {"verified_at": "2026-10-30T19:54:33.636552+00:00"} |
| [runs/preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/runs/preflight-r01/worker-0/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-10-30T19:54:03.187245+00:00", "last_record_at": "2026-10-30T19:54:29.497248+00:00", "finished_at": "2026-10-30T19:54:31.812159+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有100个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/032-cache-formation-mechanism-s1-native-trace-v1-2026-10-31.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31)。未复制模型权重、环境或凭据。
